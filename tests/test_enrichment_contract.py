"""Unit tests for Phase 5E Contract & Schema Preparation.

Validates:
1. Valid Price Band Notice supplemental object.
2. Valid Analyst Assessment supplemental object.
3. EXCHANGE + PRICE_BAND_NOTICE classification.
4. STRUCTURED_INPUT + MANUAL_ENTRY classification.
5. Required provenance structure.
6. Analyst attribution requirements.
7. Source-vs-derived distinction (formulas, dependencies, is_derived flag).
8. UNKNOWN / null representation (fail-closed, no fixture defaults).
9. Rejection of invalid enum / classification combinations.
10. Rejection of malformed provenance / missing source_id.
11. Backward compatibility with existing v1.5 canonical input.
12. 259-test baseline regression invariants.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict

import pytest

from ipo_screening.canonical import ExtractionMethod, SourceRef, SourceType, Verification
from ipo_screening.enrichment_contract import (
    ANALYST_EXTRACTION_METHOD,
    ANALYST_SOURCE_TYPE,
    PRICE_BAND_NOTICE_NOTE,
    PRICE_BAND_NOTICE_SOURCE_TYPE,
    create_analyst_source_ref,
    create_price_band_source_ref,
    enforce_enrichment_contract,
    is_analyst_source,
    is_price_band_source,
    load_enrichment_schema,
    validate_enrichment_contract,
    validate_source_derived_separation,
)
from ipo_screening.errors import SchemaValidationError


@pytest.fixture
def valid_enrichment_payload() -> Dict[str, Any]:
    """A valid, complete supplemental enrichment document (v1.0)."""
    return {
        "contract_version": "1.0",
        "ipo_id": "VISHAL-NIRMITI-LIMITED",
        "as_of": "2026-10-05T12:00:00Z",
        "sources": [
            {
                "source_id": "SRC-PBN-001",
                "source_type": "EXCHANGE",
                "uri": "filings/vishal_nirmiti/price_band_ad.pdf",
                "content_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
                "source_timestamp": "2026-10-01T06:00:00Z",
                "note": "PRICE_BAND_NOTICE",
            },
            {
                "source_id": "SRC-NSE-BID-001",
                "source_type": "MARKET_DATA",
                "uri": "https://api.nseindia.com/ipo/bids/VISHAL",
                "content_hash": "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5",
                "retrieval_timestamp": "2026-10-05T11:30:00Z",
            },
            {
                "source_id": "SRC-ANALYST-001",
                "source_type": "STRUCTURED_INPUT",
                "uri": "dossiers/analyst_eval_vishal.json",
                "source_timestamp": "2026-10-04T18:00:00Z",
                "note": "Analyst qualitative evaluation dossier",
            },
        ],
        "price_band": {
            "price_band_low": {
                "raw_value": 208.0,
                "normalized_value": 208.0,
                "unit": "INR",
                "source_id": "SRC-PBN-001",
                "locator": "Page 1, 'Offer Details' Table, Row 1",
                "extraction_method": "DETERMINISTIC_PDF",
                "verification": "VERIFIED",
                "confidence": 1.0,
            },
            "price_band_high": {
                "raw_value": 220.0,
                "normalized_value": 220.0,
                "unit": "INR",
                "source_id": "SRC-PBN-001",
                "locator": "Page 1, 'Offer Details' Table, Row 2",
                "extraction_method": "DETERMINISTIC_PDF",
                "verification": "VERIFIED",
                "confidence": 1.0,
            },
            "lot_size": {
                "raw_value": 68,
                "normalized_value": 68,
                "unit": "SHARES",
                "source_id": "SRC-PBN-001",
                "locator": "Page 1, 'Bid Details' Box",
                "extraction_method": "DETERMINISTIC_PDF",
                "verification": "VERIFIED",
            },
            "open_date": {
                "raw_value": "2026-10-06",
                "normalized_value": "2026-10-06",
                "source_id": "SRC-PBN-001",
                "locator": "Page 1, 'Issue Schedule'",
                "extraction_method": "DETERMINISTIC_PDF",
                "verification": "VERIFIED",
            },
            "close_date": {
                "raw_value": "2026-10-08",
                "normalized_value": "2026-10-08",
                "source_id": "SRC-PBN-001",
                "locator": "Page 1, 'Issue Schedule'",
                "extraction_method": "DETERMINISTIC_PDF",
                "verification": "VERIFIED",
            },
        },
        "market_data": {
            "subscription": {
                "as_of": "2026-10-05T11:30:00Z",
                "qib_x": 31.4,
                "nii_x": 18.2,
                "retail_x": 4.5,
                "overall_x": 15.6,
                "source_id": "SRC-NSE-BID-001",
                "extraction_method": "EXCHANGE_DATA",
                "verification": "VERIFIED",
            },
            "gmp": {
                "as_of": "2026-10-05T10:00:00Z",
                "pct": 24.5,
                "trend": "strong",
                "source_id": "SRC-TRACKER-001",
                "extraction_method": "MARKET_DATA",
                "verification": "UNVERIFIED",
            },
            "regime": {
                "as_of": "2026-10-05T09:30:00Z",
                "nifty_trend": "supportive",
                "last_ipo_listing_gains_pct": [15.2, 28.4, -4.1, 12.0, 35.8],
                "source_id": "SRC-EXCHANGE-001",
                "extraction_method": "EXCHANGE_DATA",
                "verification": "VERIFIED",
            },
            "anchor": {
                "as_of": "2026-10-05T11:00:00Z",
                "quality": "reputed",
                "source_id": "SRC-CIRCULAR-001",
                "extraction_method": "EXCHANGE_DATA",
                "verification": "VERIFIED",
            },
        },
        "analyst_assessment": {
            "moat_rating": {
                "value": "strong_niche",
                "assessed_by": "analyst-rk-44",
                "assessment_timestamp": "2026-10-04T18:00:00Z",
                "assessment_note": "High switching costs in RDSO-approved concrete railway sleepers.",
                "verification": "UNVERIFIED",
                "source_id": "SRC-ANALYST-001",
            },
            "visibility_rating": {
                "value": "strong",
                "assessed_by": "analyst-rk-44",
                "assessment_timestamp": "2026-10-04T18:00:00Z",
                "assessment_note": "Order book of Rs 1,250 Cr represents 2.8x FY24 revenue.",
                "verification": "UNVERIFIED",
                "source_id": "SRC-ANALYST-001",
            },
        },
        "derived": {
            "fresh_shares": {
                "is_derived": True,
                "calculated_value": 6590909,
                "formula": "round(fresh_issue * 1e7 / price_band_high)",
                "dependencies": ["issue.fresh_issue", "price_band.price_band_high"],
                "unit": "SHARES",
            },
            "post_issue_shares": {
                "is_derived": True,
                "calculated_value": 26390909,
                "formula": "pre_issue_shares + fresh_shares",
                "dependencies": ["issue.pre_issue_shares", "derived.fresh_shares"],
                "unit": "SHARES",
            },
            "ofs_amount": {
                "is_derived": True,
                "calculated_value": 33.0,
                "formula": "sum(seller_shares) * price_band_high / 1e7",
                "dependencies": ["issue.ofs_sellers", "price_band.price_band_high"],
                "unit": "INR_CRORES",
            },
            "post_issue_eps": {
                "is_derived": True,
                "calculated_value": 9.46,
                "formula": "pat_latest * 1e7 / post_issue_shares",
                "dependencies": ["financials.periods[-1].pat", "derived.post_issue_shares"],
                "unit": "INR",
            },
            "promoter_post_pct": {
                "is_derived": True,
                "calculated_value": 55.08,
                "formula": "(promoter_pre_shares - promoter_ofs_sold) / post_issue_shares * 100",
                "dependencies": ["capital_structure.promoter_pre_shares", "issue.ofs_sellers", "derived.post_issue_shares"],
                "unit": "PERCENT",
            },
        },
    }


# --------------------------------------------------------------------------
# Test 1: Valid Price Band Notice supplemental object
# --------------------------------------------------------------------------


def test_valid_price_band_notice_object(valid_enrichment_payload):
    """Spec: Valid Price Band Notice payload satisfies the enrichment schema."""
    findings = validate_enrichment_contract(valid_enrichment_payload)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert not errors, f"Unexpected errors: {[e.message for e in errors]}"
    # Verify price band values are intact
    pb = valid_enrichment_payload["price_band"]
    assert pb["price_band_high"]["normalized_value"] == 220.0
    assert pb["price_band_low"]["normalized_value"] == 208.0
    assert pb["lot_size"]["normalized_value"] == 68


# --------------------------------------------------------------------------
# Test 2: Valid Analyst Assessment supplemental object
# --------------------------------------------------------------------------


def test_valid_analyst_assessment_object(valid_enrichment_payload):
    """Spec: Valid Analyst Assessment payload satisfies attribution and schema."""
    findings = validate_enrichment_contract(valid_enrichment_payload)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert not errors
    analyst = valid_enrichment_payload["analyst_assessment"]
    assert analyst["moat_rating"]["value"] == "strong_niche"
    assert analyst["moat_rating"]["assessed_by"] == "analyst-rk-44"
    assert analyst["visibility_rating"]["value"] == "strong"


# --------------------------------------------------------------------------
# Test 3: EXCHANGE + PRICE_BAND_NOTICE classification
# --------------------------------------------------------------------------


def test_price_band_source_classification():
    """Phase 5D D-5D-02: Price Band Notice maps to SourceType.EXCHANGE + note=PRICE_BAND_NOTICE."""
    source_ref = create_price_band_source_ref(
        source_id="SRC-PBN-001",
        uri="filings/ad.pdf",
        content_hash="abc123hash",
        source_timestamp="2026-10-01T06:00:00Z",
    )
    assert source_ref.source_type == SourceType.EXCHANGE.value
    assert source_ref.source_type == PRICE_BAND_NOTICE_SOURCE_TYPE
    assert is_price_band_source(source_ref)

    # Dict representation
    source_dict = {
        "source_id": "SRC-PBN-002",
        "source_type": "EXCHANGE",
        "note": "PRICE_BAND_NOTICE - SEBI advertisement",
    }
    assert is_price_band_source(source_dict)


# --------------------------------------------------------------------------
# Test 4: STRUCTURED_INPUT + MANUAL_ENTRY classification
# --------------------------------------------------------------------------


def test_analyst_assessment_classification():
    """Phase 5D D-5D-13: Analyst Assessment maps to STRUCTURED_INPUT + MANUAL_ENTRY."""
    source_ref = create_analyst_source_ref(
        source_id="SRC-ANALYST-001",
        analyst_id="analyst-rk-44",
        source_timestamp="2026-10-04T18:00:00Z",
    )
    assert source_ref.source_type == SourceType.STRUCTURED_INPUT.value
    assert source_ref.source_type == ANALYST_SOURCE_TYPE
    assert is_analyst_source(source_ref, ExtractionMethod.MANUAL_ENTRY.value)

    # Dict representation
    source_dict = {
        "source_id": "SRC-ANALYST-002",
        "source_type": "STRUCTURED_INPUT",
    }
    assert is_analyst_source(source_dict, "MANUAL_ENTRY")


# --------------------------------------------------------------------------
# Test 5: Required provenance structure
# --------------------------------------------------------------------------


def test_required_provenance_structure(valid_enrichment_payload):
    """Spec s3.4: Provenance must supply source_id, locator, and extraction_method."""
    enforce_enrichment_contract(valid_enrichment_payload)

    # Missing source_id on a provenance value is rejected
    invalid = copy.deepcopy(valid_enrichment_payload)
    del invalid["price_band"]["price_band_high"]["source_id"]
    with pytest.raises(SchemaValidationError) as exc:
        enforce_enrichment_contract(invalid)
    assert any("source_id" in f.message for f in exc.value.findings)


# --------------------------------------------------------------------------
# Test 6: Analyst attribution requirement
# --------------------------------------------------------------------------


def test_analyst_attribution_mandatory(valid_enrichment_payload):
    """Phase 5D D-5D-13: Analyst qualitative ratings require assessed_by attribution."""
    invalid = copy.deepcopy(valid_enrichment_payload)
    del invalid["analyst_assessment"]["moat_rating"]["assessed_by"]
    with pytest.raises(SchemaValidationError) as exc:
        enforce_enrichment_contract(invalid)
    assert any("assessed_by" in f.message for f in exc.value.findings)


def test_analyst_assessment_unverified_tier4_warning(valid_enrichment_payload):
    """Tier 4 qualitative judgments must remain UNVERIFIED; VERIFIED emits warning."""
    suspicious = copy.deepcopy(valid_enrichment_payload)
    suspicious["analyst_assessment"]["moat_rating"]["verification"] = "VERIFIED"
    findings = validate_enrichment_contract(suspicious)
    warnings = [f for f in findings if f.code == "ANALYST_ASSESSMENT_CANNOT_BE_VERIFIED"]
    assert len(warnings) == 1
    assert "Tier-4 qualitative judgment and must remain UNVERIFIED" in warnings[0].message


# --------------------------------------------------------------------------
# Test 7: Source vs. Derived distinction
# --------------------------------------------------------------------------


def test_source_vs_derived_separation_enforced(valid_enrichment_payload):
    """Phase 5D D-5D-07/D-5D-08: Source facts and derived quantities must stay apart."""
    # Derived quantities must declare is_derived=True, formula, dependencies
    invalid = copy.deepcopy(valid_enrichment_payload)
    del invalid["derived"]["fresh_shares"]["formula"]
    with pytest.raises(SchemaValidationError) as exc:
        enforce_enrichment_contract(invalid)
    assert any("formula" in f.message for f in exc.value.findings)

    # Source facts cannot claim extraction_method=DERIVED
    invalid2 = copy.deepcopy(valid_enrichment_payload)
    invalid2["price_band"]["price_band_high"]["extraction_method"] = "DERIVED"
    findings = validate_source_derived_separation(invalid2)
    assert any(f.code == "SOURCE_FACT_MARKED_AS_DERIVED" for f in findings)


# --------------------------------------------------------------------------
# Test 8: UNKNOWN / null representation (fail-closed, no fixture defaults)
# --------------------------------------------------------------------------


def test_unknown_null_fail_closed_representation(valid_enrichment_payload):
    """Spec s3.2, Phase 5D D-5D-09: Missing values remain null; no coercion to zero."""
    payload = copy.deepcopy(valid_enrichment_payload)
    # Undisclosed price band in preliminary mode is null
    payload["price_band"]["price_band_high"]["raw_value"] = None
    payload["price_band"]["price_band_high"]["normalized_value"] = None
    payload["price_band"]["price_band_low"]["raw_value"] = None
    payload["price_band"]["price_band_low"]["normalized_value"] = None

    findings = validate_enrichment_contract(payload)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert not errors, f"Null price band should be permitted in enrichment contract: {errors}"


# --------------------------------------------------------------------------
# Test 9: Rejection of invalid enum / classification combinations
# --------------------------------------------------------------------------


def test_rejection_of_invalid_enums(valid_enrichment_payload):
    """Invalid source_type or extraction_method is rejected by schema."""
    invalid = copy.deepcopy(valid_enrichment_payload)
    invalid["sources"][0]["source_type"] = "INVALID_SOURCE_TYPE"
    with pytest.raises(SchemaValidationError):
        enforce_enrichment_contract(invalid)

    invalid2 = copy.deepcopy(valid_enrichment_payload)
    invalid2["price_band"]["price_band_high"]["extraction_method"] = "INVALID_METHOD"
    with pytest.raises(SchemaValidationError):
        enforce_enrichment_contract(invalid2)

    invalid3 = copy.deepcopy(valid_enrichment_payload)
    invalid3["analyst_assessment"]["moat_rating"]["value"] = "super_monopoly"  # not in enum
    with pytest.raises(SchemaValidationError):
        enforce_enrichment_contract(invalid3)


# --------------------------------------------------------------------------
# Test 10: Rejection of malformed provenance
# --------------------------------------------------------------------------


def test_rejection_of_malformed_provenance(valid_enrichment_payload):
    """Malformed provenance (e.g. invalid confidence range) is rejected."""
    invalid = copy.deepcopy(valid_enrichment_payload)
    invalid["price_band"]["price_band_high"]["confidence"] = 1.5  # maximum is 1.0
    with pytest.raises(SchemaValidationError) as exc:
        enforce_enrichment_contract(invalid)
    assert any("confidence" in f.location for f in exc.value.findings)


# --------------------------------------------------------------------------
# Test 11: Backward compatibility with existing v1.5 canonical input
# --------------------------------------------------------------------------


def test_v1_5_canonical_input_schema_remains_backward_compatible():
    """Phase 5E: The v1.5 canonical input schema is NOT mutated and accepts existing fixtures."""
    from ipo_screening.schema_validation import enforce_schema, load_schema

    canonical_schema = load_schema()
    # Ensure canonical schema id is v1.5
    assert canonical_schema["$id"] == "ipo-input.v1.5.schema.json"

    # Verify Vishal Nirmiti golden fixture validates against canonical schema
    golden_path = Path(__file__).resolve().parents[1] / "fixtures" / "vishal_nirmiti" / "input.json"
    with open(golden_path, "r", encoding="utf-8") as handle:
        golden_doc = json.load(handle)

    findings = enforce_schema(golden_doc, canonical_schema)
    assert findings == []


# --------------------------------------------------------------------------
# Test 12: Frozen core golden result hash verification
# --------------------------------------------------------------------------


def test_frozen_golden_hash_remains_intact(golden_input, config):
    """Phase 5E invariant: Deterministic evaluation core is untouched; golden hash matches."""
    from ipo_screening.pipeline import evaluate

    outcome = evaluate(golden_input, config, evaluation_datetime=golden_input.get("_eval_at"))
    expected_hash = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
    assert outcome.record.result_hash == expected_hash, (
        f"Result hash mismatch: got {outcome.record.result_hash}, expected {expected_hash}"
    )
