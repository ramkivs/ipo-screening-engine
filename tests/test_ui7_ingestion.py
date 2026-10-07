"""UI-7 IPO Document Ingestion & Deterministic Evaluation Test Suite.

Asserts:
1. End-to-end multipart filing upload (DRHP/RHP PDF) via POST /api/v1/ingest/document.
2. Integration with DocumentExtractor, CanonicalInputBuilder, and evaluate() pipeline.
3. Coexistence of multiple distinct evaluated IPOs in EvaluationStore without server restart.
4. Duplicate upload detection and idempotent return without overwriting immutable store.
5. Golden evaluation result hash preservation (e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1).
6. Strict validation gates (missing file, invalid format, non-PDF magic bytes, payload size limit, invalid mode).
7. Strict read-only enforcement on all other presentation routes (HTTP 405).
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
    client = TestClient(app)

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
    assert body["final_score"] == pytest.approx(23.0)
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
    assert detail["score"]["final_score"] == pytest.approx(23.0)

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


def test_presentation_routes_remain_strictly_read_only(test_env):
    """Only POST /api/v1/ingest/document is permitted; all other mutations return 405 Method Not Allowed."""
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
    # Expected signature: self, file_bytes, filename, mode
    assert param_names == ["self", "file_bytes", "filename", "mode"]


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
    assert body["code"] == "PROCESSING_FAILED"
    assert "schema validation failed" in body["message"].lower()


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
    assert body["final_score"] == pytest.approx(55.0)
    assert body["confidence"] == "Low"
    assert body["verdict"] == "INSUFFICIENT_DATA"

    eval_data = body["evaluation"]
    assert eval_data["score"]["final_score"] == pytest.approx(55.0)
    assert eval_data["score"]["base_score"] == pytest.approx(58.0)
    assert eval_data["score"]["penalties_total"] == pytest.approx(-3.0)
    assert eval_data["score"]["completeness_pct"] == pytest.approx(75.0)

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


