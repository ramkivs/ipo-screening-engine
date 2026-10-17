"""Step 5 + Step 4 closure regression suite (2026-10-17).

Area B(i): the auditor opinion is established only by positive
examination-report language. The previous behaviour defaulted to
"unqualified" (sections.py initial value, builder.py ``_pick_gov``
default) without evidence, conflating *unknown* with a *verified clean
opinion* and feeding knockout K1 / the auditor criterion. The opinion
now stays None (schema-supported null) unless the source establishes
it; K1's tri-state contract resolves UNVERIFIED, never CLEAR, on
unknown input (knockout semantics unchanged).

Area C / Step 5: bounded manual entry of price_band_low,
price_band_high and lot_size through POST /api/v1/ingest/manual-terms.
Manual values carry MANUAL_ENTRY provenance against a STRUCTURED_INPUT
operator source, are never presented as verified, require an
explanation, block on conflicts until explicitly confirmed, never
displace a verified official value, and leave OFS derivation unchanged.
Unresolved terms keep the fail-closed AWAITING_ISSUE_TERMS posture.
"""

from __future__ import annotations

import copy
import io

import pytest
from fastapi.testclient import TestClient

from conftest import EVAL_AT, REPO_ROOT
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.pipeline import evaluate
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import (
    IngestionValidationError,
    PresentationConfig,
    PresentationService,
)

PDF_BYTES = b"%PDF-1.4 step5-test"
EXPLANATION = "Terms read from the exchange price-band announcement dated 2026-10-10."


# --------------------------------------------------------------------------
# Area B(i): auditor opinion
# --------------------------------------------------------------------------


def _extractor_with_pages(pages):
    extractor = SectionExtractor.__new__(SectionExtractor)
    extractor.page_count = max(pages) if pages else 1
    extractor.extract_page_text = lambda p: pages.get(p, "")
    return extractor


def _opinion(extractions):
    for ex in extractions:
        if ex.field_path == "governance.auditor_opinion":
            return ex.candidate_value
    return None


_RANGES = {"restated_financials": (1, 2), "litigation": (3, 3), "our_management": (4, 4)}


def test_supported_unqualified_opinion_is_extracted():
    ex = _extractor_with_pages(
        {1: "Independent Auditor's Examination Report. In our view the financial statements give an unqualified opinion."}
    )
    assert _opinion(ex.extract_governance(_RANGES)) == "unqualified"


def test_supported_unmodified_opinion_is_extracted():
    ex = _extractor_with_pages(
        {1: "Examination Report of the Independent Auditors. We express an unmodified opinion on the restated financial information."}
    )
    assert _opinion(ex.extract_governance(_RANGES)) == "unqualified"


def test_supported_qualified_and_adverse_opinions_are_extracted():
    qualified = _extractor_with_pages(
        {1: "Independent Auditor's Examination Report. Basis for qualified opinion: inventory was not verified."}
    )
    assert _opinion(qualified.extract_governance(_RANGES)) == "qualified"
    adverse = _extractor_with_pages(
        {1: "Examination Report. Adverse opinion: the statements do not present fairly."}
    )
    assert _opinion(adverse.extract_governance(_RANGES)) == "adverse"
    emphasis = _extractor_with_pages(
        {1: "Examination Report of Independent Auditor. Emphasis of Matter: we draw attention to note 4."}
    )
    assert _opinion(emphasis.extract_governance(_RANGES)) == "emphasis_of_matter"


def test_opinion_not_found_emits_no_clean_opinion():
    ex = _extractor_with_pages(
        {1: "Independent Auditor's Examination Report on Restated Financial Information.", 2: "Basis of preparation and restatement adjustments."}
    )
    extractions = ex.extract_governance(_RANGES)
    assert _opinion(extractions) is None
    assert all(e.field_path != "governance.auditor_opinion" for e in extractions)


def test_builder_no_longer_defaults_to_unqualified():
    builder = CanonicalInputBuilder.__new__(CanonicalInputBuilder)
    builder.base = {}
    builder.extractions = []
    builder.allow_fixture_fallbacks = False
    assert builder._build_governance()["auditor_opinion"] is None


def _knockout_state(record, rule_id="K1"):
    knockouts = record.knockouts
    rules = knockouts["results"] if isinstance(knockouts, dict) else knockouts
    for rule in rules:
        if rule.get("rule_id") == rule_id:
            return rule.get("state")
    raise AssertionError(f"{rule_id} not found in {knockouts}")


def test_unknown_opinion_resolves_unverified_never_clear(golden_input, config):
    doc = copy.deepcopy(golden_input)
    doc["governance"]["auditor_opinion"] = None
    outcome = evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT)
    metrics = outcome.record.derived_metrics["metrics"]
    if isinstance(metrics, dict):
        opinion_metric = metrics["auditor_opinion"]
    else:
        opinion_metric = next(m for m in metrics if m["metric_id"] == "auditor_opinion")
    assert opinion_metric["state"] == "UNKNOWN"
    assert opinion_metric.get("value") is None
    assert _knockout_state(outcome.record) == "UNVERIFIED"


def test_supported_adverse_opinion_still_triggers_k1(golden_input, config):
    doc = copy.deepcopy(golden_input)
    doc["governance"]["auditor_opinion"] = "qualified"
    outcome = evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT)
    assert _knockout_state(outcome.record) == "TRIGGERED"


def test_explicit_unqualified_opinion_remains_scored(golden_input, config):
    doc = copy.deepcopy(golden_input)
    doc["governance"]["auditor_opinion"] = "unqualified"
    outcome = evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT)
    metrics = outcome.record.derived_metrics["metrics"]
    if isinstance(metrics, dict):
        opinion_metric = metrics["auditor_opinion"]
    else:
        opinion_metric = next(m for m in metrics if m["metric_id"] == "auditor_opinion")
    assert opinion_metric["state"] == "VALUE"
    assert opinion_metric.get("value") == "unqualified"
    assert _knockout_state(outcome.record) != "TRIGGERED"


def test_golden_result_hash_preserved(golden_input, config):
    outcome = evaluate(copy.deepcopy(golden_input), config, mode="final", evaluation_datetime=EVAL_AT)
    assert outcome.record.result_hash == (
        "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
    )


# --------------------------------------------------------------------------
# Area C / Step 5: manual issue-term entry
# --------------------------------------------------------------------------


def _client(tmp_path, monkeypatch, doc_factory):
    monkeypatch.setattr(
        DocumentExtractor,
        "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (doc_factory(), {}),
    )
    store_dir = tmp_path / "evaluations"
    cfg = PresentationConfig(
        store_root=store_dir,
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    return TestClient(create_app(service), base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"}), service


def _missing_terms_doc(golden_input):
    doc = copy.deepcopy(golden_input)
    doc["issue"]["price_band_low"] = None
    doc["issue"]["price_band_high"] = None
    doc["issue"]["lot_size"] = None
    assert doc["issue"]["ofs"] is not None  # OFS stays filing/derived, never manual
    return doc


def _upload(client, path="/api/v1/ingest/document", **data):
    payload = {"mode": "final"}
    payload.update(data)
    return client.post(
        path,
        files={"file": ("filing.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
        data=payload,
    )


def _stored_evaluation_ids(service):
    return set(service.eval_store.list_evaluations())


def test_manual_entry_requires_explanation(tmp_path, monkeypatch, golden_input):
    client, _ = _client(tmp_path, monkeypatch, lambda: _missing_terms_doc(golden_input))
    res = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
    )
    assert res.status_code == 400
    assert res.json()["code"] == "VALIDATION_ERROR"
    assert "explanation" in res.json()["message"].lower()


def test_manual_entry_validates_values(tmp_path, monkeypatch, golden_input):
    client, _ = _client(tmp_path, monkeypatch, lambda: _missing_terms_doc(golden_input))
    inverted = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="230",
        price_band_high="220",
        lot_size="68",
        explanation=EXPLANATION,
    )
    assert inverted.status_code == 400
    bad_lot = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="208",
        price_band_high="220",
        lot_size="0",
        explanation=EXPLANATION,
    )
    assert bad_lot.status_code == 400
    fractional_lot = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="208",
        price_band_high="220",
        lot_size="68.5",
        explanation=EXPLANATION,
    )
    assert fractional_lot.status_code == 400


def test_manual_entry_rejects_unsupported_fields_at_service_level(tmp_path, golden_input):
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    with pytest.raises(IngestionValidationError):
        service.ingest_document(
            file_bytes=PDF_BYTES,
            filename="filing.pdf",
            manual_terms={"gmp_pct": 42.0},
            manual_explanation=EXPLANATION,
        )


def test_manual_entry_completes_evaluation_with_manual_provenance(
    tmp_path, monkeypatch, golden_input
):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_terms_doc(golden_input))
    awaiting = _upload(client)
    assert awaiting.status_code == 422
    assert awaiting.json()["code"] == "AWAITING_ISSUE_TERMS"
    assert set(awaiting.json()["missing_fields"]) == {
        "price_band_low",
        "price_band_high",
        "lot_size",
    }
    before = _stored_evaluation_ids(service)
    assert before == set()

    res = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        explanation=EXPLANATION,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    manual = body["issue_terms"]["manual_entry"]
    assert manual["provenance"] == "MANUAL_ENTRY"
    assert manual["verified"] is False
    assert set(manual["fields"]) == {"price_band_low", "price_band_high", "lot_size"}
    assert manual["explanation"] == EXPLANATION

    # Persisted record carries MANUAL_ENTRY provenance, never verified.
    record = service.eval_store.read(body["evaluation_id"])
    assert record["input_snapshot"]["input"]["issue"]["price_band_low"] == 208.0
    manual_items = [
        item
        for item in record["evidence"]["evidence"]
        if item.get("extraction_method") == "MANUAL_ENTRY"
    ]
    assert manual_items, "no MANUAL_ENTRY evidence persisted"
    assert all(item["source_id"] == "SRC-MANUAL-ENTRY" for item in manual_items)
    assert any(EXPLANATION in (item.get("note") or "") for item in manual_items)
    assert any(
        s.get("source_id") == "SRC-MANUAL-ENTRY" for s in record["evidence"]["sources"]
    )

    # Re-read through the evidence API: values present, method shown,
    # verification is UNVERIFIED -- not OFFICIAL_VERIFIED.
    evidence = client.get(f"/api/v1/evaluations/{body['evaluation_id']}/evidence").json()
    items = {item["field"]: item for item in evidence["items"]}
    low = items["EV-issue.price_band_low"]
    assert low["extracted_value"] == 208.0
    assert low["extraction_method"] == "MANUAL_ENTRY"
    assert low["verification"] == "UNVERIFIED"

    # OFS behaviour unchanged: filing/derived value, never manual.
    assert record["input_snapshot"]["input"]["issue"]["ofs"] == golden_input["issue"]["ofs"]
    manual_fields = {
        item["field"] for item in evidence["items"] if item["extraction_method"] == "MANUAL_ENTRY"
    }
    assert manual_fields == {
        "EV-issue.price_band_low",
        "EV-issue.price_band_high",
        "EV-issue.lot_size",
    }


def test_partial_manual_entry_stays_awaiting_and_persists_nothing(
    tmp_path, monkeypatch, golden_input
):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_terms_doc(golden_input))
    res = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="208",
        explanation=EXPLANATION,
    )
    assert res.status_code == 422
    detail = res.json()
    assert detail["code"] == "AWAITING_ISSUE_TERMS"
    assert set(detail["missing_fields"]) == {"price_band_high", "lot_size"}
    assert detail["resolution"]["manual_entry"]["fields"] == ["price_band_low"]
    assert _stored_evaluation_ids(service) == set()


def test_conflict_blocks_until_explicitly_confirmed(tmp_path, monkeypatch, golden_input):
    client, service = _client(tmp_path, monkeypatch, lambda: copy.deepcopy(golden_input))
    conflict = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="200",
        explanation=EXPLANATION,
    )
    assert conflict.status_code == 409
    detail = conflict.json()
    assert detail["code"] == "ISSUE_TERM_CONFLICT"
    entry = detail["conflicts"][0]
    assert entry["field"] == "issue.price_band_low"
    assert entry["manual_value"] == 200.0
    assert entry["existing_value"] == 208.0
    assert entry["existing_origin"] == "FILING_EXTRACTION"
    assert _stored_evaluation_ids(service) == set()

    resolved = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="200",
        explanation=EXPLANATION,
        confirm_conflicts="true",
    )
    assert resolved.status_code == 201, resolved.text
    record = service.eval_store.read(resolved.json()["evaluation_id"])
    # Confirmation resolved the conflict but did NOT upgrade provenance.
    assert record["input_snapshot"]["input"]["issue"]["price_band_low"] == 200.0
    assert any(
        item.get("extraction_method") == "MANUAL_ENTRY"
        and item.get("source_id") == "SRC-MANUAL-ENTRY"
        for item in record["evidence"]["evidence"]
    )


def test_manual_terms_endpoint_rejects_forbidden_parameters(
    tmp_path, monkeypatch, golden_input
):
    client, _ = _client(tmp_path, monkeypatch, lambda: _missing_terms_doc(golden_input))
    res = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        explanation=EXPLANATION,
        reference_base_path="/etc",
    )
    assert res.status_code == 400
    assert res.json()["code"] == "SECURITY_VIOLATION_UNAUTHORIZED_PARAMETER"


VISHAL_RHP_PDF = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"


def test_vishal_real_filing_manual_entry_fills_only_authorized_terms(tmp_path):
    """Real RHP with [●] terms: manual entry fills floor/cap/lot but OFS
    remains outstanding (not manually enterable, derivation unchanged),
    so the posture stays AWAITING_ISSUE_TERMS and nothing persists."""
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    client = TestClient(
        create_app(service),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )
    pdf_bytes = VISHAL_RHP_PDF.read_bytes()

    awaiting = client.post(
        "/api/v1/ingest/document",
        files={"file": ("vishal.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "final"},
    )
    assert awaiting.status_code == 422
    assert {"price_band_low", "price_band_high", "lot_size", "ofs"} <= set(
        awaiting.json()["missing_fields"]
    )

    res = client.post(
        "/api/v1/ingest/manual-terms",
        files={"file": ("vishal.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={
            "mode": "final",
            "price_band_low": "208",
            "price_band_high": "220",
            "lot_size": "68",
            "explanation": EXPLANATION,
        },
    )
    assert res.status_code == 422, res.text
    body = res.json()
    assert body["code"] == "AWAITING_ISSUE_TERMS"
    assert body["missing_fields"] == ["ofs"]
    assert set(body["resolution"]["manual_entry"]["fields"]) == {
        "price_band_low",
        "price_band_high",
        "lot_size",
    }
    assert service.eval_store.list_evaluations() == []
