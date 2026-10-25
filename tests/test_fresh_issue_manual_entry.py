"""issue.fresh_issue manual entry -- closing the Jio manual-entry dead end
(2026-10-19).

Observed Windows failure (ingestion ``ing-8db36776dd794ec3``,
``U72900GJ2019PLC110816_JIO.pdf``): filing extraction, issuer
identification and official discovery (UNAVAILABLE) all succeeded; the
four-field manual entry was accepted; eligibility then blocked evaluation
SOLELY because ``issue.fresh_issue`` was missing -- a field the manual
form did not accept. Evaluation did not run and nothing was persisted.

Contract reconciliation (see
``docs/investigation/JIO-FRESH-ISSUE-MANUAL-ENTRY-2026-10-19.md``):

- The canonical input contract v1.5 (``schema/ipo-input.v1.5.schema.json``,
  spec s20 hard gate) lists ``issue.fresh_issue`` in ``issue.required``:
  it is a genuine prerequisite for every evaluation. ``evaluate()`` hard
  fails without it; every historical evaluation carries it.
- The scoring contract (spec s18) consumes it in module C
  (``fresh_share`` 3 pts, ``use_of_proceeds`` 4 pts) and it is never
  silently zeroed by the scored metrics (absent -> UNKNOWN, never 0).
- The completing source classes are the filing, the final Prospectus, or
  -- since this correction, as directed -- the bounded manual entry
  (MANUAL_ENTRY / UNVERIFIED, never official verification), on the same
  authority as the other four terms (the broker's IPO page states the
  fresh-issue amount).

So: CASE B -- the field stays required (the fail-closed gate remains when
it is genuinely absent) and is now explicitly enterable end to end. No
scoring formula, weight, threshold, knockout, ranking or golden fixture
changes; no fabricated or defaulted amount; provenance is never upgraded.
"""

from __future__ import annotations

import copy
import io

import pytest
from fastapi.testclient import TestClient

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import (
    PresentationConfig,
    PresentationService,
)

PDF_BYTES = b"%PDF-1.4 fresh-issue-manual-entry"
EXPLANATION = "Fresh-issue amount read from the broker platform IPO page on 2026-10-19."
FOUR = ("price_band_low", "price_band_high", "lot_size", "ofs")
FIVE = FOUR + ("fresh_issue",)

JIO_PDF = REPO_ROOT / "evidence" / "non-authoritative" / "jio" / "U72900GJ2019PLC110816_JIO.pdf"
# Test-scoped magnitudes only (consistent with the established Jio
# prospectus-pathway tests); no Jio value is asserted as a real-world fact.
JIO_TERMS = {
    "price_band_low": "1065",
    "price_band_high": "1119",
    "lot_size": "12",
    "ofs": "0",
    "fresh_issue": "1485000",
}


def _client(tmp_path, monkeypatch, doc_factory):
    monkeypatch.setattr(
        DocumentExtractor,
        "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (doc_factory(), {}),
    )
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
    return client, service


def _jio_client(tmp_path):
    """Real Jio extraction, no official providers (discovery UNAVAILABLE)."""
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
    return client, service


def _missing_doc(golden_input, *, drop=FIVE):
    doc = copy.deepcopy(golden_input)
    for field in drop:
        doc["issue"][field] = None
    return doc


def _upload(client, payload=None, path="/api/v1/ingest/manual-terms", file_bytes=PDF_BYTES, **fields):
    data = {"mode": "final"}
    if payload:
        data.update(payload)
    data.update(fields)
    return client.post(
        path,
        files={"file": ("filing.pdf", io.BytesIO(file_bytes), "application/pdf")},
        data=data,
    )


def _manual(body):
    return (body.get("issue_terms") or {}).get("manual_entry") or {}


def _evidence_map(record):
    items = (record.get("evidence") or {}).get("evidence") or []
    if isinstance(items, dict):
        return items
    return {item.get("evidence_id"): item for item in items}


def _spec_for(record, field):
    """Evidence spec for an issue field, tolerating the established
    evidence-id shapes (created ``EV-issue.<field>``; preserved
    ``EV-issue-<field>`` / ``EV-<field>`` hyphen forms from a prior spec)."""
    evidence = _evidence_map(record)
    hyphen = field.replace("_", "-")
    for candidate in (f"EV-issue.{field}", f"EV-issue-{hyphen}", f"EV-{hyphen}"):
        if candidate in evidence:
            return evidence[candidate]
    raise KeyError(field)


# ---------------------------------------------------------------------------
# A. The exact observed dead end: reproduced and then closed
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_jio_four_field_submission_still_fails_closed_naming_fresh_issue(tmp_path):
    """Reproduction of the observed failure, preserved fail-closed: the
    four-field submission alone must still block naming issue.fresh_issue
    (a genuinely required input is never fabricated or defaulted)."""
    client, service = _jio_client(tmp_path)
    res = _upload(
        client,
        {k: JIO_TERMS[k] for k in FOUR} | {"explanation": EXPLANATION},
        file_bytes=JIO_PDF.read_bytes(),
    )
    assert res.status_code == 422, res.text
    body = res.json()
    assert body["code"] == "AWAITING_ISSUE_TERMS"
    assert body["missing_fields"] == ["fresh_issue"]
    assert service.eval_store.list_evaluations() == []


@pytest.mark.slow
def test_jio_five_field_submission_completes_evaluation_end_to_end(tmp_path):
    """The dead end is closed: the same filing with the fresh-issue amount
    supplied through the bounded manual entry reaches the EXISTING
    evaluation pipeline, persists, and is retrievable from the audit log."""
    client, service = _jio_client(tmp_path)
    res = _upload(client, dict(JIO_TERMS, explanation=EXPLANATION), file_bytes=JIO_PDF.read_bytes())
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["ipo_id"] == "JIO-PLATFORMS-LIMITED"
    assert body["final_score"] is not None

    record = service.eval_store.read(body["evaluation_id"])
    issue = record["input_snapshot"]["input"]["issue"]
    # The four existing manual terms AND the fresh amount reach the
    # canonical evaluation input exactly as submitted.
    assert issue["price_band_low"] == 1065.0
    assert issue["price_band_high"] == 1119.0
    assert issue["lot_size"] == 12
    assert issue["ofs"] == 0.0
    assert issue["fresh_issue"] == 1485000.0

    # Manual evidence stays MANUAL_ENTRY / UNVERIFIED on every field.
    manual = body["issue_terms"]["manual_entry"]
    assert set(manual["fields"]) == set(FIVE)
    assert manual["provenance"] == "MANUAL_ENTRY"
    assert manual["verified"] is False
    evidence = _evidence_map(record)
    for field in FIVE:
        spec = _spec_for(record, field)
        assert spec["extraction_method"] == "MANUAL_ENTRY"
        assert spec["source_id"] == "SRC-MANUAL-ENTRY"
        assert EXPLANATION in (spec.get("note") or "")

    # Discovery UNAVAILABLE remains UNAVAILABLE: manual entry is a
    # separate input source, never evidence of official publication.
    terms_report = body.get("issue_terms") or {}
    assert terms_report.get("status") == "UNAVAILABLE"
    assert terms_report.get("verified") is False

    # The audit record exists, is correlated and retrievable end to end.
    ingestion_id = body["ingestion_id"]
    hist = client.get(f"/api/v1/ingestions/{ingestion_id}")
    assert hist.status_code == 200
    record_json = hist.json()
    assert record_json["status"] == "SUCCEEDED"
    assert record_json["evaluation_run"] is True and record_json["persisted"] is True
    events = [(e["stage"], e["event_type"], e["status"]) for e in record_json["events"]]
    assert ("term_resolution", "manual_submission", "SUCCEEDED") in events
    assert ("term_resolution", "manual_entry", "SUCCEEDED") in events
    assert ("evaluation", "completed", "SUCCEEDED") in events
    assert ("persistence", "completed", "SUCCEEDED") in events
    accepted = [e for e in record_json["events"] if e["event_type"] == "manual_entry"][0]
    assert accepted["details"]["values"]["fresh_issue"] == 1485000.0


def test_five_field_submission_on_synthetic_filing_completes_evaluation(
    tmp_path, monkeypatch, golden_input
):
    """Fast synthetic variant of the dead-end closure (golden-based filing
    with all five terms nulled, discovery UNAVAILABLE)."""
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        fresh_issue="14500",
        explanation=EXPLANATION,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    record = service.eval_store.read(body["evaluation_id"])
    issue = record["input_snapshot"]["input"]["issue"]
    assert issue["fresh_issue"] == 14500.0
    assert set(_manual(body)["fields"]) == set(FIVE)


# ---------------------------------------------------------------------------
# B. No fabrication / no defaults; genuinely missing inputs stay fail-closed
# ---------------------------------------------------------------------------

def test_unsupplied_fresh_issue_stays_fail_closed_after_four_terms(
    tmp_path, monkeypatch, golden_input
):
    """The gate follows the authoritative contract: fresh_issue is required
    (schema issue.required). A submission that omits it stays blocked with
    that precise field named; nothing is invented, zeroed or defaulted."""
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert res.status_code == 422
    body = res.json()
    assert body["code"] == "AWAITING_ISSUE_TERMS"
    assert body["missing_fields"] == ["fresh_issue"]
    assert service.eval_store.list_evaluations() == []


def test_partial_submission_of_only_fresh_issue_keeps_other_terms_blocked(
    tmp_path, monkeypatch, golden_input
):
    """Every required term is still individually required: supplying only
    fresh_issue does not complete the input."""
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(client, fresh_issue="14500", explanation=EXPLANATION)
    assert res.status_code == 422
    body = res.json()
    assert body["code"] == "AWAITING_ISSUE_TERMS"
    assert set(body["missing_fields"]) == set(FOUR)
    assert service.eval_store.list_evaluations() == []


def test_explicit_zero_fresh_issue_is_an_operator_statement_not_a_default(
    tmp_path, monkeypatch, golden_input
):
    """Explicit 0 states a pure-OFS offer (schema minimum 0) and is
    preserved exactly; it is never a silent substitute for an unknown."""
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        fresh_issue="0",
        explanation="Operator statement: pure-OFS offer, no fresh issue.",
    )
    assert res.status_code == 201, res.text
    body = res.json()
    record = service.eval_store.read(body["evaluation_id"])
    assert record["input_snapshot"]["input"]["issue"]["fresh_issue"] == 0.0
    manual = body["issue_terms"]["manual_entry"]
    assert manual["values"]["fresh_issue"] == 0.0
    assert manual["provenance"] == "MANUAL_ENTRY" and manual["verified"] is False


@pytest.mark.parametrize("bad", ["-1", "nan", "inf"])
def test_invalid_fresh_issue_values_are_rejected_without_substitution(
    tmp_path, monkeypatch, golden_input, bad
):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        fresh_issue=bad,
        explanation=EXPLANATION,
    )
    assert res.status_code == 400, res.text
    assert res.json()["code"] == "VALIDATION_ERROR"
    assert service.eval_store.list_evaluations() == []


# ---------------------------------------------------------------------------
# C. Provenance, protection and scoring semantics unchanged
# ---------------------------------------------------------------------------

def test_manual_fresh_issue_never_displaces_officially_verified_value(
    tmp_path, monkeypatch, golden_input
):
    def factory():
        doc = copy.deepcopy(golden_input)
        # Simulate verified official resolution of the fresh amount
        # (the Prospectus pathway): SRC-PROSPECTUS-* provenance is
        # classified OFFICIAL_VERIFIED by the service.
        doc["_evidence"]["issue.fresh_issue"] = {
            "evidence_id": "EV-issue.fresh_issue",
            "source_id": "SRC-PROSPECTUS-TEST",
            "locator": "Prospectus, fresh issue",
            "extraction_method": "TABLE_EXTRACTION",
        }
        return doc

    client, service = _client(tmp_path, monkeypatch, factory)
    res = _upload(client, fresh_issue="9999", explanation=EXPLANATION, confirm_conflicts="true")
    assert res.status_code == 201, res.text
    body = res.json()
    manual = body["issue_terms"]["manual_entry"]
    assert manual["overridden_by_verified"] == ["fresh_issue"]
    assert manual["fields"] == []
    # The verified value stands; the manual value was not applied.
    record = service.eval_store.read(body["evaluation_id"])
    assert record["input_snapshot"]["input"]["issue"]["fresh_issue"] == 14500.0


def test_scoring_semantics_identical_for_extracted_and_manual_fresh_issue(
    tmp_path, monkeypatch, golden_input
):
    """The same values produce the same score regardless of supply path:
    no scoring formula, band, weight or threshold changed."""

    def extracted_factory():
        return copy.deepcopy(golden_input)

    def manual_factory():
        return _missing_doc(golden_input)

    client1, _ = _client(tmp_path / "a", monkeypatch, extracted_factory)
    res1 = client1.post(
        "/api/v1/ingest/document",
        files={"file": ("filing.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
        data={"mode": "final"},
    )
    assert res1.status_code == 201, res1.text
    body1 = res1.json()

    client2, _ = _client(tmp_path / "b", monkeypatch, manual_factory)
    res2 = _upload(
        client2,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        fresh_issue="14500",
        explanation=EXPLANATION,
    )
    assert res2.status_code == 201, res2.text
    body2 = res2.json()

    assert body2["final_score"] == pytest.approx(body1["final_score"])
    assert body2["verdict"] == body1["verdict"]


def test_manual_fresh_issue_conflict_requires_explicit_confirmation(
    tmp_path, monkeypatch, golden_input
):
    def factory():
        doc = copy.deepcopy(golden_input)
        for field in FOUR:
            doc["issue"][field] = None
        return doc  # fresh_issue=14500 extracted

    client, service = _client(tmp_path, monkeypatch, factory)
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        fresh_issue="20000",
        explanation=EXPLANATION,
    )
    assert res.status_code == 409
    detail = res.json()
    assert detail["code"] == "ISSUE_TERM_CONFLICT"
    assert any(c["field"] == "issue.fresh_issue" for c in detail["conflicts"])

    resolved = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        fresh_issue="20000",
        explanation=EXPLANATION,
        confirm_conflicts="true",
    )
    assert resolved.status_code == 201, resolved.text
    body = resolved.json()
    record = service.eval_store.read(body["evaluation_id"])
    # Confirmed manual override applies (extraction, not official verified),
    # and stays MANUAL_ENTRY provenance.
    assert record["input_snapshot"]["input"]["issue"]["fresh_issue"] == 20000.0
    spec = _spec_for(record, "fresh_issue")
    assert spec["extraction_method"] == "MANUAL_ENTRY"
