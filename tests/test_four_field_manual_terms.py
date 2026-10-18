"""Four-field manual issue-term entry workflow (2026-10-18).

Initial screening must not wait for official-source retrieval. The
operator supplies all four required issue terms from the broker
platform through ``POST /api/v1/ingest/manual-terms``:

- ``issue.price_band_low``   -- price-band floor, INR per equity share
- ``issue.price_band_high``  -- price-band cap, INR per equity share
- ``issue.lot_size``         -- application lot, whole equity shares
- ``issue.ofs``              -- Offer-for-Sale MONETARY amount in the
  filing's ``financials.reporting_unit`` (v1.5 input contract: number,
  minimum 0, "in reporting_unit"; the approved enrichment formula
  derives it as seller shares x cap price). Never a share count, never
  assumed zero when unknown.

This module proves, at the service/API boundary:

A. a complete valid four-field submission reaches the EXISTING scoring
   engine with the exact submitted values and MANUAL_ENTRY provenance,
   and the evaluation is persisted;
B. omitting any one required field (especially issue.ofs) keeps the
   fail-closed AWAITING_ISSUE_TERMS posture with the precise field
   named; nothing is fabricated, defaulted or persisted;
C. invalid values (type, NaN/Inf, negative OFS, inverted band,
   fractional lot) are rejected without silent zero/null substitution;
D. manual values keep MANUAL_ENTRY / UNVERIFIED provenance, conflict
   handling and verified-value protection remain intact, and values
   entered for one IPO never leak into another;
E. a manual completion preserves the official-discovery outcome as
   UNAVAILABLE where appropriate -- manual input is a separate source
   of input and never evidence of official publication.
"""

from __future__ import annotations

import copy
import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from conftest import REPO_ROOT, run
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import (
    IngestionValidationError,
    PresentationConfig,
    PresentationService,
)

PDF_BYTES = b"%PDF-1.4 four-field-manual-terms"
EXPLANATION = "Terms read from the broker platform IPO page on 2026-10-18."
FOUR = ("price_band_low", "price_band_high", "lot_size", "ofs")
VALUES = {"price_band_low": 208.0, "price_band_high": 220.0, "lot_size": 68.0, "ofs": 3300.0}


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


def _missing_doc(golden_input, *, drop=FOUR, strip_sellers=False):
    """Golden input with the named issue terms removed (never defaulted)."""
    doc = copy.deepcopy(golden_input)
    for field in drop:
        doc["issue"][field] = None
    if strip_sellers:
        doc["issue"]["ofs_sellers"] = []
    return doc


def _upload(client, path="/api/v1/ingest/manual-terms", **data):
    payload = {"mode": "final"}
    payload.update(data)
    return client.post(
        path,
        files={"file": ("filing.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
        data=payload,
    )


def _stored(service):
    return set(service.eval_store.list_evaluations())


# ---------------------------------------------------------------------------
# A. Complete manual input reaches the existing scoring engine
# ---------------------------------------------------------------------------

def test_complete_four_field_submission_reaches_scoring_and_persists(
    tmp_path, monkeypatch, golden_input, config
):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))

    # Plain upload stays fail-closed and names all four missing terms.
    awaiting = _upload(client, "/api/v1/ingest/document")
    assert awaiting.status_code == 422
    assert awaiting.json()["code"] == "AWAITING_ISSUE_TERMS"
    assert set(awaiting.json()["missing_fields"]) == set(FOUR)
    assert _stored(service) == set()

    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert res.status_code == 201, res.text
    body = res.json()

    # The response identifies every supplied term as manual and unverified.
    manual = body["issue_terms"]["manual_entry"]
    assert manual["provenance"] == "MANUAL_ENTRY"
    assert manual["verified"] is False
    assert set(manual["fields"]) == set(FOUR)
    assert manual["values"] == {
        "price_band_low": 208.0,
        "price_band_high": 220.0,
        "lot_size": 68.0,
        "ofs": 3300.0,
    }
    assert manual["explanation"] == EXPLANATION
    assert manual["reporting_unit"] == "INR_LAKHS"

    # The persisted evaluation carries the exact submitted values.
    record = service.eval_store.read(body["evaluation_id"])
    issue = record["input_snapshot"]["input"]["issue"]
    assert issue["price_band_low"] == 208.0
    assert issue["price_band_high"] == 220.0
    assert issue["lot_size"] == 68
    assert issue["ofs"] == 3300.0

    # All four carry MANUAL_ENTRY provenance against the manual source,
    # with the operator explanation preserved; none is verified.
    record_items = {item["evidence_id"]: item for item in record["evidence"]["evidence"]}
    for field in FOUR:
        item = record_items[f"EV-issue.{field}"]
        assert item["extraction_method"] == "MANUAL_ENTRY"
        assert item["source_id"] == "SRC-MANUAL-ENTRY"
        assert EXPLANATION in (item.get("note") or "")
    assert any(
        s.get("source_id") == "SRC-MANUAL-ENTRY" for s in record["evidence"]["sources"]
    )

    # The scorecard was produced by the EXISTING scoring engine from
    # those exact values: replaying the persisted input through
    # pipeline.evaluate() reproduces the recorded score and verdict.
    snapshot_input = record["input_snapshot"]["input"]
    moment = datetime.strptime(
        record["evaluation_timestamp"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc)
    replay = run(snapshot_input, config, at=moment)
    assert float(record["score"]["final_score"]) == pytest.approx(
        float(replay.score.final_score)
    )
    assert str(record["verdict"]["verdict"]) == str(replay.score.verdict)

    # The evidence API presents the four values as manual and unverified.
    ev = client.get(f"/api/v1/evaluations/{body['evaluation_id']}/evidence").json()
    items = {item["field"]: item for item in ev["items"]}
    for field in FOUR:
        entry = items[f"EV-issue.{field}"]
        assert entry["extraction_method"] == "MANUAL_ENTRY"
        assert entry["verification"] == "UNVERIFIED"
    assert items["EV-issue.ofs"]["extracted_value"] == 3300.0
    assert items["EV-issue.ofs"]["unit"] == "INR lakh"


# ---------------------------------------------------------------------------
# B. Missing required inputs stay blocked, field by field
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("omit", FOUR)
def test_omitting_any_required_field_blocks_evaluation(
    tmp_path, monkeypatch, golden_input, omit
):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    terms = {k: str(v) for k, v in VALUES.items() if k != omit}
    res = _upload(client, explanation=EXPLANATION, **terms)
    assert res.status_code == 422, res.text
    detail = res.json()
    assert detail["code"] == "AWAITING_ISSUE_TERMS"
    assert detail["missing_fields"] == [omit]
    # No missing value was fabricated or defaulted into the payload.
    assert set(detail["resolution"]["manual_entry"]["fields"]) == set(FOUR) - {omit}
    assert _stored(service) == set()


def test_omitting_ofs_on_a_fully_unresolved_issue_keeps_ofs_awaiting(
    tmp_path, monkeypatch, golden_input
):
    """Root-cause regression: three manual terms used to strand the
    screening on issue.ofs with no permitted way to supply it. Omission
    must still block (no derivation/default substitution), but the field
    is now enterable in the same panel."""
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        explanation=EXPLANATION,
    )
    assert res.status_code == 422
    body = res.json()
    assert body["code"] == "AWAITING_ISSUE_TERMS"
    assert body["missing_fields"] == ["ofs"]
    assert _stored(service) == set()

    # Completing the set with the OFS amount releases the pipeline.
    done = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert done.status_code == 201, done.text
    record = service.eval_store.read(done.json()["evaluation_id"])
    assert record["input_snapshot"]["input"]["issue"]["ofs"] == 3300.0


def test_missing_fresh_issue_still_fails_closed_after_four_terms(
    tmp_path, monkeypatch, golden_input
):
    """issue.fresh_issue is not one of the four manually enterable terms.
    When the filing does not state it, evaluation stays fail-closed with
    that precise field instead of a schema failure or a fabricated
    amount."""

    def factory():
        doc = _missing_doc(golden_input)
        doc["issue"]["fresh_issue"] = None
        return doc

    client, service = _client(tmp_path, monkeypatch, factory)
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
    assert _stored(service) == set()


# ---------------------------------------------------------------------------
# C. Invalid inputs are rejected without silent defaults
# ---------------------------------------------------------------------------

def test_invalid_ofs_values_are_rejected(tmp_path, monkeypatch, golden_input):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    for bad, needle in (
        (-1.0, "zero or a positive"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (True, "number"),
        ("3300", "number"),
    ):
        with pytest.raises(IngestionValidationError) as excinfo:
            service.ingest_document(
                file_bytes=PDF_BYTES,
                filename="filing.pdf",
                manual_terms=dict(VALUES, ofs=bad),
                manual_explanation=EXPLANATION,
            )
        assert "issue.ofs" in str(excinfo.value)
        assert needle in str(excinfo.value)
    assert _stored(service) == set()


def test_invalid_numeric_and_band_values_are_rejected_via_api(
    tmp_path, monkeypatch, golden_input
):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    cases = [
        dict(price_band_low="208", price_band_high="220", lot_size="68", ofs="-5"),
        dict(price_band_low="208", price_band_high="220", lot_size="68.5", ofs="3300"),
        dict(price_band_low="230", price_band_high="220", lot_size="68", ofs="3300"),
        dict(price_band_low="0", price_band_high="220", lot_size="68", ofs="3300"),
    ]
    for terms in cases:
        res = _upload(client, explanation=EXPLANATION, **terms)
        assert res.status_code == 400, res.text
        assert res.json()["code"] == "VALIDATION_ERROR"
    # A rejected submission must not coerce anything to zero or persist.
    assert _stored(service) == set()

    # NaN over the API is rejected as well (the service rejects
    # non-finite values; the transport layer may reject earlier with 422
    # -- either way nothing reaches evaluation and no value is defaulted).
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="nan",
        explanation=EXPLANATION,
    )
    assert res.status_code in (400, 422), res.text
    assert _stored(service) == set()


def test_unsupported_manual_fields_are_rejected_at_service_level(
    tmp_path, monkeypatch, golden_input
):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    with pytest.raises(IngestionValidationError) as excinfo:
        service.ingest_document(
            file_bytes=PDF_BYTES,
            filename="filing.pdf",
            manual_terms={"gmp_pct": 42.0},
            manual_explanation=EXPLANATION,
        )
    assert "gmp_pct" in str(excinfo.value)
    assert _stored(service) == set()


def test_manual_ofs_zero_is_an_explicit_value_not_a_default(
    tmp_path, monkeypatch, golden_input
):
    """0 is a valid canonical OFS amount (number, minimum 0): an explicit
    operator statement of "no offer for sale". It is recorded exactly as
    submitted; nothing else is changed."""
    client, service = _client(
        tmp_path, monkeypatch, lambda: _missing_doc(golden_input, strip_sellers=True)
    )
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="0",
        explanation="Broker platform page shows a fresh issue only; no offer for sale.",
    )
    assert res.status_code == 201, res.text
    body = res.json()
    manual = body["issue_terms"]["manual_entry"]
    assert manual["values"]["ofs"] == 0.0
    record = service.eval_store.read(body["evaluation_id"])
    assert record["input_snapshot"]["input"]["issue"]["ofs"] == 0.0
    ofs_items = [
        item
        for item in record["evidence"]["evidence"]
        if item.get("evidence_id") == "EV-issue.ofs"
    ]
    assert ofs_items and ofs_items[0]["extraction_method"] == "MANUAL_ENTRY"


# ---------------------------------------------------------------------------
# D. Provenance, conflicts and isolation
# ---------------------------------------------------------------------------

def test_manual_ofs_conflict_with_filing_value_requires_confirmation(
    tmp_path, monkeypatch, golden_input
):
    client, service = _client(tmp_path, monkeypatch, lambda: copy.deepcopy(golden_input))
    conflict = _upload(client, ofs="2500", explanation=EXPLANATION)
    assert conflict.status_code == 409
    detail = conflict.json()
    assert detail["code"] == "ISSUE_TERM_CONFLICT"
    entry = detail["conflicts"][0]
    assert entry["field"] == "issue.ofs"
    assert entry["manual_value"] == 2500.0
    assert entry["existing_value"] == 3300.0
    assert entry["existing_origin"] == "FILING_EXTRACTION"
    assert _stored(service) == set()

    resolved = _upload(
        client, ofs="2500", explanation=EXPLANATION, confirm_conflicts="true"
    )
    assert resolved.status_code == 201, resolved.text
    record = service.eval_store.read(resolved.json()["evaluation_id"])
    # The exact confirmed value is recorded, with manual provenance.
    assert record["input_snapshot"]["input"]["issue"]["ofs"] == 2500.0
    ofs_item = [
        item
        for item in record["evidence"]["evidence"]
        if item.get("evidence_id") == "EV-issue.ofs"
    ][0]
    assert ofs_item["extraction_method"] == "MANUAL_ENTRY"
    assert ofs_item["source_id"] == "SRC-MANUAL-ENTRY"


def test_manual_ofs_never_displaces_officially_verified_value(
    tmp_path, monkeypatch, golden_input
):
    def factory():
        doc = copy.deepcopy(golden_input)
        # Simulate a verified official-source resolution of issue.ofs
        # (e.g. a future prospectus/notice channel): SRC-PROSPECTUS-*
        # provenance is classified OFFICIAL_VERIFIED by the service.
        doc["_evidence"]["issue.ofs"] = {
            "evidence_id": "EV-issue.ofs",
            "source_id": "SRC-PROSPECTUS-TEST",
            "locator": "Prospectus, Offer for Sale",
            "extraction_method": "TABLE_EXTRACTION",
        }
        return doc

    client, service = _client(tmp_path, monkeypatch, factory)
    res = _upload(
        client, ofs="2500", explanation=EXPLANATION, confirm_conflicts="true"
    )
    assert res.status_code == 201, res.text
    body = res.json()
    manual = body["issue_terms"]["manual_entry"]
    assert manual["overridden_by_verified"] == ["ofs"]
    assert manual["fields"] == []
    record = service.eval_store.read(body["evaluation_id"])
    # The verified value stands; the manual value was not applied.
    assert record["input_snapshot"]["input"]["issue"]["ofs"] == 3300.0


def test_manual_terms_are_isolated_per_ipo(tmp_path, monkeypatch, golden_input):
    other = copy.deepcopy(golden_input)
    other["ipo_id"] = "OTHER-ISSUER-LIMITED"
    other["company_name"] = "Other Issuer Limited"
    queue = [_missing_doc(golden_input), _missing_doc(other)]

    client, service = _client(tmp_path, monkeypatch, lambda: queue.pop(0))

    done = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert done.status_code == 201, done.text
    assert done.json()["ipo_id"] == "VISHAL-NIRMITI-LIMITED"

    # A different IPO, uploaded without manual terms, does not inherit
    # the values entered for the first one.
    leaked = _upload(client, "/api/v1/ingest/document")
    assert leaked.status_code == 422
    assert leaked.json()["code"] == "AWAITING_ISSUE_TERMS"
    assert set(leaked.json()["missing_fields"]) == set(FOUR)
    assert _stored(service) == {
        eid for eid in service.eval_store.list_evaluations()
    }
    assert len(_stored(service)) == 1


# ---------------------------------------------------------------------------
# E. Manual completion preserves the official-discovery outcome
# ---------------------------------------------------------------------------

def test_manual_completion_preserves_unavailable_discovery_outcome(
    tmp_path, monkeypatch, golden_input
):
    client, service = _client(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert res.status_code == 201, res.text
    issue_terms = res.json()["issue_terms"]
    # The official-discovery outcome is preserved: no configured source
    # resolved anything (UNAVAILABLE), and the manual completion is a
    # separate input source -- never a claim of official publication.
    assert issue_terms["status"] == "UNAVAILABLE"
    assert issue_terms["verified"] is False
    assert issue_terms["manual_entry"]["provenance"] == "MANUAL_ENTRY"
    assert issue_terms["manual_entry"]["verified"] is False
