"""Workstream 2 — evidence presentation integrity regression suite.

Covers, under the existing contracts (no new evidence-schema
properties or enums):
- Non-scalar canonical values (financial periods) presented through a
  read-only summary derived from the persisted canonical input.
- Extractor-generated processing claims distinguished from recorded
  quotations (via the existing evidence `note` property).
- Document identity resolved from the source manifest only when it
  plausibly names a document; otherwise honestly unresolved.
- Scalar projection, verification classifications, historical records
  and D-PEER-1 behaviour unchanged.
"""

from __future__ import annotations

import copy
import json

import pytest

from conftest import EVAL_AT, REPO_ROOT
from ipo_screening.enrichment_engine import EnrichmentEngine
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.extraction.interfaces import RawExtraction
from ipo_screening.extraction.price_band_notice import PriceBandNoticeParser
from ipo_screening.pipeline import evaluate
from ipo_screening.presentation.service import PresentationConfig, PresentationService
from ipo_screening.schema_validation import validate_schema

GOLDEN_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
PROCESSING_NOTE = "PROCESSING_SUMMARY: Parsed 3 financial periods from restated statements"


def _service(store_dir):
    return PresentationService(PresentationConfig(store_root=store_dir, config_dir=REPO_ROOT / "config"))


def _evidence_map(service, evaluation_id):
    resp = service.get_evaluation_evidence(evaluation_id)
    assert resp is not None
    return {item.evidence_id: item for item in resp.items}


def _golden_with_periods_evidence(golden_input, periods_note=PROCESSING_NOTE, quote=None):
    doc = copy.deepcopy(golden_input)
    spec = {
        "evidence_id": "EV-financials-periods",
        "source_id": "RHP-VISHAL-NIRMITI",
        "locator": "P&L, Balance Sheet, Cash Flow Annexures",
        "page": 73,
        "extraction_method": "DETERMINISTIC_PDF",
        "note": periods_note,
    }
    if quote is not None:
        spec["quote"] = quote
    doc["_evidence"]["financials.periods"] = spec
    return doc


# --- Non-scalar (periods) presentation ------------------------------------

def test_periods_presented_from_canonical_value_not_quote(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evals")
    out = evaluate(_golden_with_periods_evidence(golden_input), config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    item = _evidence_map(_service(tmp_path / "evals"), out.record.evaluation_id)["EV-financials-periods"]

    assert item.extracted_value is None  # a count is never substituted for the periods
    assert item.value_summary == "3 reporting periods: FY2024, FY2025, FY2026"
    assert item.quote_kind == "PROCESSING"
    assert item.quote is None
    assert item.note == PROCESSING_NOTE
    assert item.locator == "P&L, Balance Sheet, Cash Flow Annexures"
    assert item.page == 73


def test_periods_summary_tracks_canonical_periods(golden_input, config, tmp_path):
    """The note claims 3 periods; the canonical input holds 2. The
    presentation must follow the canonical value, proving it is not
    parsed from the processing message."""
    doc = _golden_with_periods_evidence(golden_input)
    extra = copy.deepcopy(doc["financials"]["periods"][0])
    extra["fy"] = "FY2023"
    doc["financials"]["periods"] = [extra] + doc["financials"]["periods"]
    store = EvaluationStore(tmp_path / "evals")
    out = evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    item = _evidence_map(_service(tmp_path / "evals"), out.record.evaluation_id)["EV-financials-periods"]
    assert item.value_summary == "4 reporting periods: FY2023, FY2024, FY2025, FY2026"


def test_missing_canonical_value_is_not_fabricated(golden_input, config, tmp_path):
    doc = copy.deepcopy(golden_input)
    doc["_evidence"]["issue.listing_date"] = {
        "source_id": "RHP-VISHAL-NIRMITI",
        "locator": "Cover page",
        "extraction_method": "DETERMINISTIC_PDF",
        "quote": "Listing date to be announced",
    }
    doc["issue"]["listing_date"] = None
    store = EvaluationStore(tmp_path / "evals")
    out = evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    item = _evidence_map(_service(tmp_path / "evals"), out.record.evaluation_id)["EV-issue.listing_date"]
    assert item.extracted_value is None
    assert item.value_summary is None


# --- Processing claims vs recorded quotations ------------------------------

def test_extraction_marks_processing_quotes_via_existing_note_property():
    processing = RawExtraction(
        field_path="financials.periods",
        candidate_value=[{"fy": "FY2026"}],
        quote="Parsed 1 financial periods from restated statements",
        quote_is_processing=True,
    )
    ev = processing.to_evidence_dict("RHP-TEST")
    assert "quote" not in ev
    assert ev["note"].startswith("PROCESSING_SUMMARY: Parsed 1 financial periods")

    genuine = RawExtraction(
        field_path="issue.price_band_low",
        candidate_value=208,
        quote="Floor Price is ₹208 per Equity Share",
    )
    ev = genuine.to_evidence_dict("RHP-TEST")
    assert ev["quote"] == "Floor Price is ₹208 per Equity Share"
    assert "note" not in ev


def test_scalar_projection_and_recorded_quotation_unchanged(golden_input, config, tmp_path):
    """Notice-assembled Vishal (retained fixture source): scalar values,
    verbatim quotation and RETAINED_UNVERIFIED classification unchanged."""
    base = copy.deepcopy(golden_input)
    for field in ("price_band_low", "price_band_high", "lot_size", "ofs"):
        base["issue"][field] = None
    for key in ("issue.price_band_low", "issue.price_band_high", "issue.lot_size", "issue.ofs"):
        base["_evidence"].pop(key, None)
    notice = PriceBandNoticeParser().parse_from_file(REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt")
    canonical = EnrichmentEngine.assemble(base_input=base, price_band_notice=notice, mode="final").canonical_input

    store = EvaluationStore(tmp_path / "evals")
    out = evaluate(canonical, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    items = _evidence_map(_service(tmp_path / "evals"), out.record.evaluation_id)

    low = items["EV-issue.price_band_low"]
    assert low.extracted_value == 208
    assert low.unit == "INR per equity share"
    assert low.quote_kind == "RECORDED"
    assert "₹208" in low.quote
    assert low.verification == "RETAINED_UNVERIFIED"
    assert low.document == "clean_notice.txt"
    assert items["EV-issue.lot_size"].extracted_value == 68


# --- Document identity ------------------------------------------------------

def test_document_identity_from_manifest_and_honest_unresolved(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evals")
    out = evaluate(_golden_with_periods_evidence(golden_input), config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    items = _evidence_map(_service(tmp_path / "evals"), out.record.evaluation_id)

    # The RHP source URI is a repository path whose filename contains
    # spaces; only the basename may be displayed.
    company_item = items["EV-company-name"]
    assert company_item.document == "U01122MH1994PLC185445-vishal nirmiti.pdf"
    assert "/" not in company_item.document

    # Descriptive manifest text is not a document identity.
    market_items = [i for i in items.values() if i.source == "MARKET-TRACKER"]
    for item in market_items:
        assert item.document is None


# --- Historical integrity + D-PEER-1 ----------------------------------------

def test_projection_does_not_rewrite_historical_records(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evals")
    out = evaluate(golden_input, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    assert out.record.result_hash == GOLDEN_HASH
    before = json.dumps(store.read(out.record.evaluation_id), sort_keys=True)
    _evidence_map(_service(tmp_path / "evals"), out.record.evaluation_id)
    after = json.dumps(store.read(out.record.evaluation_id), sort_keys=True)
    assert before == after


def test_d_peer_1_still_intact(golden_input):
    doc = copy.deepcopy(golden_input)
    doc["peers"] = []
    assert not [f for f in validate_schema(doc) if "peer" in str(f.location)]
    assert "Generic Listed Peer Ltd" not in json.dumps(doc)
