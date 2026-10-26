"""UI-7 IPO Document Ingestion & Deterministic Evaluation Test Suite.

Asserts:
1. End-to-end multipart filing upload (DRHP/RHP PDF) via POST /api/v1/ingest/document.
2. Integration with DocumentExtractor, CanonicalInputBuilder, and evaluate() pipeline.
3. Coexistence of multiple distinct evaluated IPOs in EvaluationStore without server restart.
4. Duplicate upload detection and idempotent return without overwriting immutable store.
5. Golden evaluation result hash preservation (e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1).
6. Strict validation gates (missing file, invalid format, non-PDF magic bytes, payload size limit, invalid mode).
7. Scoped write enforcement on all other presentation routes (HTTP 405).
8. Support for preliminary evaluation mode.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict

import pytest
from conftest import EVAL_AT, REPO_ROOT
from fastapi.testclient import TestClient

from ipo_screening.evaluation import EvaluationStore
from ipo_screening.pipeline import evaluate, load_config
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService


# These tests never mutate PDF readers/pages; only immutable text is reused.
pytestmark = pytest.mark.usefixtures("cached_pdf_text")

FILINGS_DIR = REPO_ROOT / "fixtures" / "filings"
SAMPLE_RHP_PDF = FILINGS_DIR / "complete_sample_rhp.pdf"
SAMPLE_RHP_2_PDF = FILINGS_DIR / "complete_sample_rhp_2.pdf"
CLASS_A_PDF = FILINGS_DIR / "class_a_financial_lender.pdf"
RK_PDF = REPO_ROOT / "handoff" / "reference" / "U18109WB2010PLC144256-R.K Fashion accessories.pdf"
GOLDEN_RESULT_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"


@pytest.fixture
def test_env(tmp_path: Path, golden_input: Dict[str, Any], config: Dict[str, Any]):
    """Set up test environment pre-populated with baseline Vishal Nirmiti evaluation."""
    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)

    # Populate baseline Vishal Nirmiti evaluation
    outcome = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT,
        store=store,
    )
    assert outcome.record.result_hash == GOLDEN_RESULT_HASH

    cfg = PresentationConfig(
        store_root=store_dir,
        config_dir=REPO_ROOT / "config",
    )
    service = PresentationService(cfg)
    app = create_app(service)
    client = TestClient(app, base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"})

    return {
        "store": store,
        "store_dir": store_dir,
        "service": service,
        "client": client,
        "vishal_eval_id": outcome.record.evaluation_id,
        "vishal_result_hash": outcome.record.result_hash,
    }


# -----------------------------------------------------------------------------
# 1. Ingestion Workflow & Multi-IPO Coexistence
# -----------------------------------------------------------------------------


def test_ingest_document_success_and_coexistence(test_env):
    """A second IPO is introduced via the UI/API workflow without server restart and coexists with Vishal Nirmiti."""
    client = test_env["client"]
    store = test_env["store"]

    assert SAMPLE_RHP_PDF.is_file(), f"Missing fixture at {SAMPLE_RHP_PDF}"
    pdf_bytes = SAMPLE_RHP_PDF.read_bytes()

    # Step 1: Verify store initially contains only Vishal Nirmiti
    initial_ipos_res = client.get("/api/v1/ipos")
    assert initial_ipos_res.status_code == 200
    initial_ipos = initial_ipos_res.json()["items"]
    assert len(initial_ipos) == 1
    assert initial_ipos[0]["company_name"].upper() == "VISHAL NIRMITI LIMITED"

    # Step 2: Ingest Complete Sample RHP PDF (Aurora Systems Limited)
    files = {"file": ("complete_sample_rhp.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"mode": "final"}
    response = client.post("/api/v1/ingest/document", files=files, data=data)

    assert response.status_code == 201, f"Ingestion failed: {response.text}"
    body = response.json()

    assert body["company_name"] == "AURORA SYSTEMS LIMITED"
    assert body["ipo_id"] == "AURORA-SYSTEMS-LIMITED"
    assert body["evaluation_mode"] == "FINAL"
    assert body["is_duplicate"] is False
    # D-5: this synthetic filing carries no litigation section, so the
    # litigation criterion is UNKNOWN instead of being awarded 4/4 on the
    # extractor's "clean" default (final 23.0 -> 19.0, available 26 -> 22).
    # 2026-10-23: -1 point. kmp_exits_2y no longer defaults to 0 when the filing
    # discloses no KMP-exit count, so board_kmp resolves UNKNOWN instead of a
    # fabricated "other" bucket. No weight or bucket boundary changed.
    # 2026-10-26: -1 point. large_holders_unlocked_early no longer defaults to
    # False; this filing states neither the lock-in nor an early unlock, so
    # lockin_bucket is UNKNOWN. No weight or bucket boundary changed.
    # 2026-10-26 (report s.25): -4 points. The synthetic filing has no
    # share-capital history and no changes-in-directorate table at all. Those
    # sections are now reported UNREAD, so `pre_ipo_placement_bucket` (-2) and
    # `board_kmp` (-2) are UNKNOWN instead of earning the favourable bucket for
    # a section the engine never read. Weights and boundaries are unchanged;
    # the same filing keeps its points wherever the source does disclose the
    # facts (verified-nil stays a scored nil).
    assert body["final_score"] == pytest.approx(13.0)
    assert body["verdict"] == "INSUFFICIENT_DATA"
    assert body["confidence"] == "Low"
    assert body["result_hash"] is not None
    assert body["evaluation_url"].startswith("/#evaluations/")

    sample_eval_id = body["evaluation_id"]

    # Step 3: Verify coexistence in EvaluationStore without restart
    assert store.exists(sample_eval_id)
    assert store.exists(test_env["vishal_eval_id"])

    # Step 4: Verify directory discovery returns BOTH IPOs
    updated_ipos_res = client.get("/api/v1/ipos")
    assert updated_ipos_res.status_code == 200
    updated_ipos = updated_ipos_res.json()["items"]
    assert len(updated_ipos) == 2

    company_names = {ipo["company_name"].upper() for ipo in updated_ipos}
    assert "VISHAL NIRMITI LIMITED" in company_names
    assert "AURORA SYSTEMS LIMITED" in company_names

    # Step 5: Verify evaluations list returns both records
    evals_res = client.get("/api/v1/evaluations")
    assert evals_res.status_code == 200
    evals = evals_res.json()["items"]
    assert len(evals) == 2

    # Step 6: Verify newly created evaluation detail is accessible via presentation API
    detail_res = client.get(f"/api/v1/evaluations/{sample_eval_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["evaluation_id"] == sample_eval_id
    assert detail["company_name"] == "AURORA SYSTEMS LIMITED"
    # 2026-10-26 (report s.25): 17.0 -> 13.0 -- share-capital history and
    # directorate sections are absent from this synthetic filing and are now
    # UNREAD rather than a favourable default (placements -2, board_kmp -2).
    assert detail["score"]["final_score"] == pytest.approx(13.0)

    # Step 7: Verify golden hash for Vishal Nirmiti is strictly preserved
    vishal_detail = client.get(f"/api/v1/evaluations/{test_env['vishal_eval_id']}").json()
    assert vishal_detail["result_hash"] == GOLDEN_RESULT_HASH


def test_ingest_multiple_distinct_ipos(test_env):
    """Multiple distinct IPOs can be sequentially ingested and stored concurrently."""
    client = test_env["client"]

    # Ingest Aurora Systems Limited
    res_a = client.post(
        "/api/v1/ingest/document",
        files={"file": ("aurora.pdf", io.BytesIO(SAMPLE_RHP_PDF.read_bytes()), "application/pdf")},
        data={"mode": "final"},
    )
    assert res_a.status_code == 201
    body_a = res_a.json()
    assert body_a["company_name"] == "AURORA SYSTEMS LIMITED"

    # Ingest Zenith Logistics Limited
    res_b = client.post(
        "/api/v1/ingest/document",
        files={"file": ("zenith.pdf", io.BytesIO(SAMPLE_RHP_2_PDF.read_bytes()), "application/pdf")},
        data={"mode": "final"},
    )
    assert res_b.status_code == 201
    body_b = res_b.json()
    assert body_b["company_name"] == "ZENITH LOGISTICS LIMITED"

    # Verify all 3 IPOs coexist
    ipos = client.get("/api/v1/ipos").json()["items"]
    assert len(ipos) == 3
    names = {i["company_name"].upper() for i in ipos}
    assert names == {
        "VISHAL NIRMITI LIMITED",
        "AURORA SYSTEMS LIMITED",
        "ZENITH LOGISTICS LIMITED",
    }


# -----------------------------------------------------------------------------
# 2. Duplicate Detection & Idempotency
# -----------------------------------------------------------------------------


def test_ingest_duplicate_document_idempotency(test_env):
    """Re-uploading the identical filing returns HTTP 200 with is_duplicate: True without creating duplicates."""
    client = test_env["client"]
    pdf_bytes = SAMPLE_RHP_PDF.read_bytes()

    # First upload -> 201 Created
    res1 = client.post(
        "/api/v1/ingest/document",
        files={"file": ("filing.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "final"},
    )
    assert res1.status_code == 201
    body1 = res1.json()
    assert body1["is_duplicate"] is False
    eval_id1 = body1["evaluation_id"]

    # Second upload of same document -> 200 OK (idempotent duplicate)
    res2 = client.post(
        "/api/v1/ingest/document",
        files={"file": ("filing_copy.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "final"},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["is_duplicate"] is True
    assert body2["evaluation_id"] == eval_id1
    assert body2["result_hash"] == body1["result_hash"]
    assert "already exists" in body2["message"]

    # Evaluation count in store must not increase
    evals = client.get("/api/v1/evaluations").json()["items"]
    assert len(evals) == 2  # Vishal Nirmiti + 1 Aurora


# -----------------------------------------------------------------------------
# 3. Validation Gates & Error Handling
# -----------------------------------------------------------------------------


def test_ingest_rejects_empty_file(test_env):
    """Empty filing document upload is rejected with HTTP 400."""
    client = test_env["client"]
    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
    )
    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "empty" in body["message"].lower()


def test_ingest_rejects_non_pdf_magic_bytes(test_env):
    """Filing without '%PDF-' magic bytes is rejected with HTTP 400 Bad Request."""
    client = test_env["client"]
    fake_txt = b"This is a text file masquerading as a PDF."
    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("fake.pdf", io.BytesIO(fake_txt), "application/pdf")},
    )
    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "%PDF-" in body["message"]


def test_ingest_rejects_invalid_mode(test_env):
    """Unsupported evaluation mode is rejected with HTTP 400 Bad Request."""
    client = test_env["client"]
    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")},
        data={"mode": "invalid_mode_xyz"},
    )
    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "invalid evaluation mode" in body["message"].lower()


def test_ingest_rejects_oversized_payload(test_env, monkeypatch):
    """Filing exceeding 50 MB limit is rejected with HTTP 413 Payload Too Large."""
    client = test_env["client"]

    # Create dummy buffer pretending to be 51 MB
    service = test_env["service"]
    monkeypatch.setattr(service, "MAX_INGEST_SIZE_BYTES", 100)  # low threshold for testing

    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("large.pdf", io.BytesIO(b"%PDF-" + b"0" * 200), "application/pdf")},
    )
    assert res.status_code == 413
    body = res.json()
    assert body["code"] == "PAYLOAD_TOO_LARGE"


# -----------------------------------------------------------------------------
# 4. Strict Read-Only Guard on All Other Presentation Routes
# -----------------------------------------------------------------------------


def test_presentation_routes_limit_write_scope(test_env):
    """Only filing ingestion and exact evaluation lifecycle routes accept POST."""
    client = test_env["client"]

    # Block POST on read-only collections
    for path in ["/api/v1/evaluations", "/api/v1/ipos", "/api/v1/backtest/analytics"]:
        res = client.post(path, json={"foo": "bar"})
        assert res.status_code == 405
        assert res.json()["code"] == "READ_ONLY_METHOD_NOT_ALLOWED"

    # Block PUT, PATCH, DELETE even on ingest endpoint
    for method in ["PUT", "PATCH", "DELETE"]:
        res = client.request(method, "/api/v1/ingest/document")
        assert res.status_code == 405
        assert res.json()["code"] == "READ_ONLY_METHOD_NOT_ALLOWED"

    # Suffix lookalikes are not accepted as lifecycle write routes.
    res = client.post("/api/v1/not-an-evaluation/archive", json={})
    assert res.status_code == 405
    assert res.json()["code"] == "READ_ONLY_METHOD_NOT_ALLOWED"

    # A cross-site browser request cannot use an unauthenticated workflow route.
    res = client.post(
        "/api/v1/evaluations/nonexistent-evaluation/archive",
        json={},
        headers={"Origin": "https://attacker.example"},
    )
    assert res.status_code == 403
    assert res.json()["code"] == "CROSS_ORIGIN_WRITE_REJECTED"

    # Malformed authority syntax also fails closed rather than raising a 500.
    res = client.post(
        "/api/v1/evaluations/nonexistent-evaluation/archive",
        json={},
        headers={"Origin": "http://[::1"},
    )
    assert res.status_code == 403
    assert res.json()["code"] == "CROSS_ORIGIN_WRITE_REJECTED"

    # Same-origin requests pass the origin check and reach route validation.
    res = client.post(
        "/api/v1/evaluations/nonexistent-evaluation/archive",
        json={},
        headers={"Origin": "http://127.0.0.1:8000"},
    )
    assert res.status_code == 404


def test_local_api_rejects_dns_rebinding_host(test_env):
    """A matching attacker Host/Origin must not turn a rebinding site into same-origin."""
    app = create_app(test_env["service"])
    localhost_client = TestClient(app, base_url="http://localhost:8000")
    assert localhost_client.get("/api/v1/health").status_code == 200

    attacker_origin = "http://rebinding.example:8000"
    client = TestClient(
        create_app(test_env["service"]),
        base_url=attacker_origin,
        headers={"Origin": attacker_origin},
    )

    read_response = client.get("/api/v1/ipos")
    assert read_response.status_code == 400
    assert read_response.json()["code"] == "LOOPBACK_HOST_REQUIRED"

    write_response = client.post(
        "/api/v1/evaluations/nonexistent-evaluation/archive",
        json={},
    )
    assert write_response.status_code == 400
    assert write_response.json()["code"] == "LOOPBACK_HOST_REQUIRED"


def test_workflow_post_requires_origin_header(test_env):
    """A local write without browser same-origin evidence fails closed."""
    client = TestClient(
        create_app(test_env["service"]),
        base_url="http://127.0.0.1:8000",
    )
    response = client.post(
        "/api/v1/evaluations/nonexistent-evaluation/archive",
        json={},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "ORIGIN_REQUIRED"


# -----------------------------------------------------------------------------
# 5. Preliminary Evaluation Mode Support
# -----------------------------------------------------------------------------


def test_ingest_document_preliminary_mode(test_env):
    """Uploading with mode='preliminary' runs preliminary evaluation."""
    client = test_env["client"]
    pdf_bytes = SAMPLE_RHP_PDF.read_bytes()

    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("aurora.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "preliminary"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["evaluation_mode"] == "PRELIMINARY"
    assert body["company_name"] == "AURORA SYSTEMS LIMITED"


# -----------------------------------------------------------------------------
# 6. Security Boundary: Public Server-Path Fallback Removal & Protection
# -----------------------------------------------------------------------------


def test_ingest_rejects_unauthorized_reference_base_path_parameter(test_env, tmp_path):
    """Public ingestion endpoint strictly rejects reference_base_path parameter with HTTP 400."""
    client = test_env["client"]
    pdf_bytes = SAMPLE_RHP_PDF.read_bytes()

    # Create a safe test fixture file to represent a targeted server file
    canary_file = tmp_path / "target_fixture.json"
    canary_file.write_text(json.dumps({"canary": "sensitive_data"}), encoding="utf-8")

    # Client attempts to submit reference_base_path via multipart form
    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("aurora.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={
            "mode": "final",
            "reference_base_path": str(canary_file),
        },
    )

    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "SECURITY_VIOLATION_UNAUTHORIZED_PARAMETER"
    assert "reference_base_path" in body["message"]
    assert "strictly prohibited" in body["message"]


def test_public_ingestion_cannot_trigger_server_file_read(test_env, tmp_path, monkeypatch):
    """Proves that public ingestion cannot turn a supplied reference_base_path into a server-side file read."""
    client = test_env["client"]
    pdf_bytes = SAMPLE_RHP_PDF.read_bytes()

    canary_file = tmp_path / "unauthorized_server_file.json"
    canary_file.write_text(json.dumps({"target": "secret"}), encoding="utf-8")

    opened_files = []
    import builtins
    original_open = builtins.open

    def tracking_open(file, *args, **kwargs):
        opened_files.append(str(file))
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", tracking_open)

    # Attempt malicious submission
    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("aurora.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "final", "reference_base_path": str(canary_file)},
    )

    assert res.status_code == 400
    # Crucial security assertion: the targeted file was never opened
    assert str(canary_file) not in opened_files


def test_service_ingest_document_signature_has_no_path_parameter():
    """PresentationService.ingest_document must not accept caller-controlled filesystem path parameters."""
    import inspect

    sig = inspect.signature(PresentationService.ingest_document)
    param_names = list(sig.parameters.keys())

    assert "reference_base_path" not in param_names
    assert "base_path" not in param_names
    assert "path" not in param_names
    # Step 5 extends the signature with bounded manual-entry parameters;
    # caller-controlled filesystem path parameters remain prohibited.
    # The ingestion-activity `recorder` is an internal instrumentation
    # object supplied only by the service/API layer itself -- it is
    # never accepted from request input and carries no path authority.
    assert param_names == ["self", "file_bytes", "filename", "mode", "manual_terms", "manual_explanation", "confirm_conflicts", "recorder"]


def test_repository_native_internal_extractor_retains_reference_base_path_support():
    """DocumentExtractor retains reference_base_path for genuine internal test/CLI workflows."""
    from ipo_screening.extraction import DocumentExtractor

    extractor = DocumentExtractor()
    assert hasattr(extractor, "extract_from_pdf")
    import inspect

    sig = inspect.signature(extractor.extract_from_pdf)
    assert "reference_base_path" in sig.parameters


# -----------------------------------------------------------------------------
# 7. Fail-Closed Boundary & Fallback Rejection Tests
# -----------------------------------------------------------------------------


def test_public_ingestion_rejects_fallback_parameters(test_env):
    """Public ingestion endpoint strictly rejects allow_fixture_fallbacks parameter with HTTP 400."""
    client = test_env["client"]
    pdf_bytes = SAMPLE_RHP_PDF.read_bytes()

    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("aurora.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={
            "mode": "final",
            "allow_fixture_fallbacks": "true",
        },
    )

    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "SECURITY_VIOLATION_UNAUTHORIZED_PARAMETER"
    assert "allow_fixture_fallbacks" in body["message"]
    assert "strictly prohibited" in body["message"]


def test_ingest_incomplete_stub_fails_closed_without_fallbacks(test_env):
    """Minimal synthetic stub lacking issue fields fails closed with HTTP 422 under fail-closed ingestion."""
    client = test_env["client"]
    pdf_bytes = CLASS_A_PDF.read_bytes()

    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("class_a.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "final"},
    )

    assert res.status_code == 422
    body = res.json()
    assert body["code"] in ("PROCESSING_FAILED", "AWAITING_ISSUE_TERMS")
    # Fail-closed either via the awaiting-terms status or the schema gate;
    # both reject the incomplete stub without fallbacks.
    message = body["message"].lower()
    assert "awaiting_issue_terms" in message or "schema validation failed" in message


VISHAL_RHP_PDF = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"


def test_ingest_vishal_rhp_undisclosed_issue_terms_fail_precisely(test_env):
    """Regression (Windows UI PROCESSING_FAILED): the Vishal Nirmiti RHP
    leaves price band, minimum bid lot and OFS amount as [●] placeholders.
    Re-uploading it must fail closed with a precise, actionable error
    naming the undisclosed fields -- not four opaque schema violations --
    and must leave the pre-existing historical evaluation untouched.

    This test injects a provider-less resolver: it exercises the
    genuinely-unavailable path. Under the DEFAULT runtime configuration
    the retained notice is discovered automatically instead (covered by
    tests/test_vishal_default_notice_wiring.py).
    """
    from ipo_screening.issue_terms import IssueTermsResolver

    store = test_env["store"]
    cfg = PresentationConfig(
        store_root=test_env["store_dir"],
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    client = TestClient(
        create_app(PresentationService(cfg)),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )
    assert VISHAL_RHP_PDF.is_file(), f"Real filing missing at {VISHAL_RHP_PDF}"

    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("vishal_nirmiti_rhp.pdf", io.BytesIO(VISHAL_RHP_PDF.read_bytes()), "application/pdf")},
        data={"mode": "final"},
    )

    assert res.status_code == 422, f"Unexpected ingestion outcome: {res.text}"
    body = res.json()
    # With no official Price Band Notice available to the runtime resolver,
    # the undisclosed terms yield an explicit awaiting status (fail-closed).
    assert body["code"] == "AWAITING_ISSUE_TERMS"
    message = body["message"]
    for field in ("issue.price_band_low", "issue.price_band_high", "issue.lot_size", "issue.ofs"):
        assert field in message
    assert "AWAITING_ISSUE_TERMS" in message
    assert "None is not of type" not in message
    assert body["missing_fields"] == ["price_band_low", "price_band_high", "lot_size", "ofs"]

    # Historical evaluation preserved: exactly the baseline record remains,
    # with its original id and golden result hash, and no new record exists.
    ipos = client.get("/api/v1/ipos").json()["items"]
    assert len(ipos) == 1
    assert store.exists(test_env["vishal_eval_id"])
    detail = client.get(f"/api/v1/evaluations/{test_env['vishal_eval_id']}").json()
    assert detail["result_hash"] == GOLDEN_RESULT_HASH


def test_ingest_vishal_rhp_auto_resolves_terms_from_official_notice(tmp_path, golden_input, config):
    """End-to-end: Vishal RHP + runtime resolver -> assembled, evaluated,
    persisted, idempotent.

    MOCKED verified channel: an HttpNoticeProvider with an injected
    fetcher serves the retained notice text from an official-host URL.
    This proves the verified-retrieval mechanics; it is not live
    retrieval, and the served text remains the repository-retained
    fixture text (see tests/test_cross_ipo_issue_term_provenance.py).
    """
    from ipo_screening.issue_terms import HttpNoticeProvider, IssueTermsResolver, NoticeSnapshotCache

    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)
    baseline = evaluate(golden_input, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    historical_id = baseline.record.evaluation_id

    # Synthetic transport only: match the unchanged RHP cover issue window.
    notice_bytes = (REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt").read_bytes().replace(
        b"Tuesday, October 06, 2026", b"Wednesday, September 30, 2026"
    ).replace(b"Thursday, October 08, 2026", b"Monday, October 05, 2026")
    resolver = IssueTermsResolver(
        providers=[
            HttpNoticeProvider(
                {"VISHAL-NIRMITI-LIMITED": "https://www.nseindia.com/announcements/vishal-price-band"},
                fetcher=lambda url: notice_bytes,
            )
        ],
        cache=NoticeSnapshotCache(tmp_path / "terms-cache"),
    )
    cfg = PresentationConfig(store_root=store_dir, config_dir=REPO_ROOT / "config", issue_terms_resolver=resolver)
    client = TestClient(create_app(PresentationService(cfg)), base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"})

    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("vishal_nirmiti_rhp.pdf", io.BytesIO(VISHAL_RHP_PDF.read_bytes()), "application/pdf")},
        data={"mode": "final"},
    )
    assert res.status_code == 201, f"Auto-resolution ingestion failed: {res.text}"
    body = res.json()
    assert body["issue_terms"]["status"] == "RESOLVED"
    assert sorted(body["issue_terms"]["resolved_fields"]) == ["lot_size", "price_band_high", "price_band_low"]

    record = store.read(body["evaluation_id"])
    persisted_input = record["input_snapshot"]["input"]
    issue = persisted_input["issue"]
    assert issue["price_band_low"] == 208
    assert issue["price_band_high"] == 220
    assert issue["lot_size"] == 68
    assert issue["ofs"] == 3300  # derived: OFS seller shares x cap price
    evidence_items = record["evidence"]["evidence"]
    source_ids = {item.get("source_id", "") for item in evidence_items}
    assert any(str(s).startswith("SRC-PBN-") for s in source_ids), source_ids
    # Derived OFS (never a direct source claim): the persisted record keeps
    # the SRC-DERIVED derivation reference produced by enrichment assembly.
    assert "SRC-DERIVED" in json.dumps(record)

    # Scorecard reopens with the persisted provenance-bearing record.
    detail = client.get(f"/api/v1/evaluations/{body['evaluation_id']}")
    assert detail.status_code == 200
    assert detail.json()["result_hash"] == body["result_hash"]

    # Duplicate upload is idempotent; the historical record is untouched.
    dup = client.post(
        "/api/v1/ingest/document",
        files={"file": ("vishal_nirmiti_rhp.pdf", io.BytesIO(VISHAL_RHP_PDF.read_bytes()), "application/pdf")},
        data={"mode": "final"},
    )
    assert dup.status_code == 200
    assert dup.json()["is_duplicate"] is True
    assert dup.json()["evaluation_id"] == body["evaluation_id"]
    assert store.read(historical_id)["result_hash"] == GOLDEN_RESULT_HASH


def test_ingest_rk_fashion_accessories_real_statutory_filing(test_env):
    """Real statutory RHP (R.K. Fashion Accessories) ingests cleanly without fixture contamination."""
    client = test_env["client"]
    assert RK_PDF.is_file(), f"Real filing missing at {RK_PDF}"
    pdf_bytes = RK_PDF.read_bytes()

    res = client.post(
        "/api/v1/ingest/document",
        files={"file": ("rk_fashion.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "final"},
    )

    assert res.status_code == 201, f"Ingestion failed: {res.text}"
    body = res.json()

    assert body["company_name"] == "R.K. FASHION ACCESSORIES LIMITED"
    assert body["ipo_id"] == "R-K-FASHION-ACCESSORIES-LIMITED"
    assert body["evaluation_mode"] == "FINAL"
    assert body["is_duplicate"] is False
    # Step 4 Area B(i): RK's opinion is not establishable from the filing,
    # so the auditor criterion is UNKNOWN instead of scored on an
    # unsupported "unqualified" default (final 50.0 -> 49.0).
    # D-5: RK's litigation section is never located by the TOC router, so the
    # scan covers no page at all; "clean" on an empty scan was an unsupported
    # finding, and the criterion is now UNKNOWN (49.0 -> 45.0).
    # 2026-10-23: -1 point from removing the unsupported kmp_exits_2y = 0 default.
    # 2026-10-26: -1 point from removing the unsupported
    # large_holders_unlocked_early = False default.  RK states the promoter
    # lock-in but says nothing about an early release for large pre-IPO
    # holders, so `lockin_bucket` is UNKNOWN rather than "intact"; the point
    # and the availability move together (44.0 -> 43.0, base 47.0 -> 46.0).
    # 2026-10-26 (report s.25): -2 points. RK's share-capital history schedule
    # was located (pages 14/97/105/111/113/118-121/124) but no allotment row
    # could be read from it, so coverage is PARTIAL and
    # `pre_ipo_placement_bucket` is UNKNOWN: the engine no longer awards 2/2
    # points for a section it could not extract. RK's directorate table *was*
    # read (1 appointment, 0 exits in the window), so board_kmp keeps its
    # verified evidence (43.0 -> 41.0).
    assert body["final_score"] == pytest.approx(41.0)
    assert body["confidence"] == "Low"
    assert body["verdict"] == "INSUFFICIENT_DATA"

    eval_data = body["evaluation"]
    assert eval_data["score"]["final_score"] == pytest.approx(41.0)  # D-5; kmp/lockin defaults removed
    assert eval_data["score"]["base_score"] == pytest.approx(44.0)  # s.25: placements UNKNOWN (-2)
    assert eval_data["score"]["penalties_total"] == pytest.approx(-3.0)
    assert eval_data["score"]["completeness_pct"] == pytest.approx(64.0)  # s.25: + placements unknown

    # Prove absence of Vishal Nirmiti qualitative defaults
    modules = {m["id"]: m for m in eval_data["score"]["modules"]}
    moat = next(c for c in modules["E"]["criteria"] if c["id"] == "moat")
    vis = next(c for c in modules["E"]["criteria"] if c["id"] == "visibility")

    assert moat["state"] == "UNKNOWN"
    assert moat["score"] == 0.0
    assert moat["value"] is None

    assert vis["state"] == "UNKNOWN"
    assert vis["score"] == 0.0
    assert vis["value"] is None


