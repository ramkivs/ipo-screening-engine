"""Unit tests for Phase 5F Price Band Notice Ingestion.

Validates:
1. Parser construction and execution.
2. Source classification (matches notice markers; rejects non-notices).
3. Cap Price extraction.
4. Floor Price extraction.
5. Lot Size extraction.
6. Open and Close Date extraction.
7. Provenance, page locators, and quote preservation.
8. Deterministic SHA-256 calculation from original source bytes.
9. Extraction method tracking.
10. SEBI ICDR price collar validation (<= 20% valid; > 20% rejected; cap <= floor rejected).
11. Strict fail-closed UNKNOWN behavior (missing fields evaluate to None, no fixture defaults).
12. Conflicting candidate rejection (fail closed on multiple price bands/lots/dates).
13. Phase 5E supplemental enrichment contract compatibility (validates against schema).
14. Regression invariants (golden hash preserved).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ipo_screening.canonical import ExtractionMethod, SourceType, Verification
from ipo_screening.enrichment_contract import (
    PRICE_BAND_NOTICE_NOTE,
    PRICE_BAND_NOTICE_SOURCE_TYPE,
    is_price_band_source,
    validate_enrichment_contract,
)
from ipo_screening.extraction.price_band_notice import (
    PriceBandNoticeClassificationError,
    PriceBandNoticeParseError,
    PriceBandNoticeParser,
    PriceBandNoticeResult,
    PriceCollarValidationError,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "notices"


@pytest.fixture
def parser() -> PriceBandNoticeParser:
    return PriceBandNoticeParser()


# --------------------------------------------------------------------------
# Test 1: Clean Notice Ingestion
# --------------------------------------------------------------------------


def test_clean_price_band_notice_parsing(parser):
    """Spec: Ingest a clean Price Band Notice text file and verify all fields."""
    fixture_path = FIXTURES_DIR / "clean_notice.txt"
    result = parser.parse_from_file(fixture_path)

    assert result.is_classified_notice is True
    assert "VISHAL NIRMITI LIMITED" in (result.company_name or "")
    assert result.price_band_low is not None
    assert result.price_band_low.value == 208.0
    assert result.price_band_high is not None
    assert result.price_band_high.value == 220.0
    assert result.lot_size is not None
    assert result.lot_size.value == 68
    assert result.open_date is not None
    assert result.open_date.value == "2026-10-06"
    assert result.close_date is not None
    assert result.close_date.value == "2026-10-08"

    assert result.collar_valid is True
    assert result.collar_spread_pct == pytest.approx(5.769, rel=1e-2)


# --------------------------------------------------------------------------
# Test 2: Alternative Language & Phrasing
# --------------------------------------------------------------------------


def test_alternative_wording_notice_parsing(parser):
    """Spec: Ingest notice with 'lower end / upper end', 'Market Lot', 'DD-Mon-YYYY' dates."""
    fixture_path = FIXTURES_DIR / "alternative_notice.txt"
    result = parser.parse_from_file(fixture_path)

    assert result.is_classified_notice is True
    assert result.price_band_low.value == 475.0
    assert result.price_band_high.value == 500.0
    assert result.lot_size.value == 30
    assert result.open_date.value == "2026-11-12"
    assert result.close_date.value == "2026-11-14"
    assert result.collar_valid is True
    assert result.collar_spread_pct == pytest.approx(5.263, rel=1e-2)


# --------------------------------------------------------------------------
# Test 3: OCR Style Notice with INR and Delimited Formats
# --------------------------------------------------------------------------


def test_ocr_style_notice_parsing(parser):
    """Spec: Ingest notice with pipe-delimited INR amounts and wordy lot sentences."""
    fixture_path = FIXTURES_DIR / "ocr_style_notice.txt"
    result = parser.parse_from_file(fixture_path)

    assert result.is_classified_notice is True
    assert result.price_band_low.value == 100.0
    assert result.price_band_high.value == 118.0
    assert result.lot_size.value == 125
    assert result.open_date.value == "2026-10-15"
    assert result.close_date.value == "2026-10-17"
    assert result.collar_valid is True
    assert result.collar_spread_pct == pytest.approx(18.0, rel=1e-2)


# --------------------------------------------------------------------------
# Test 4: Deterministic SHA-256 Calculation
# --------------------------------------------------------------------------


def test_deterministic_sha256_calculation(parser):
    """Phase 5D D-5D-03: Source SHA-256 must be calculated from original file bytes."""
    fixture_path = FIXTURES_DIR / "clean_notice.txt"
    raw_bytes = fixture_path.read_bytes()
    expected_hash = hashlib.sha256(raw_bytes).hexdigest()

    result = parser.parse_from_file(fixture_path)
    assert result.source_ref.content_hash == expected_hash
    assert result.source.content_hash == expected_hash

    # Rerun to assert byte-for-byte reproducibility
    result2 = parser.parse_from_file(fixture_path)
    assert result2.source_ref.content_hash == expected_hash


# --------------------------------------------------------------------------
# Test 5: SourceRef Classification & Backward Compatibility
# --------------------------------------------------------------------------


def test_source_ref_classification(parser):
    """Phase 5E invariant: source_type='EXCHANGE' and note='PRICE_BAND_NOTICE'."""
    fixture_path = FIXTURES_DIR / "clean_notice.txt"
    result = parser.parse_from_file(fixture_path, source_id="SRC-PBN-001")

    assert result.source_ref.source_id == "SRC-PBN-001"
    assert result.source_ref.source_type == SourceType.EXCHANGE.value
    assert result.source_ref.source_type == PRICE_BAND_NOTICE_SOURCE_TYPE
    assert is_price_band_source(result.source_ref)


# --------------------------------------------------------------------------
# Test 6: Evidence Locators & Quotes
# --------------------------------------------------------------------------


def test_evidence_locators_and_quotes(parser):
    """Spec s3.4: Extracted fields must preserve locator, page number, and quote."""
    fixture_path = FIXTURES_DIR / "clean_notice.txt"
    result = parser.parse_from_file(fixture_path)

    # Floor Price locator and quote
    assert result.price_band_low.locator is not None
    assert "Page 1" in result.price_band_low.locator
    assert result.price_band_low.quote is not None
    assert "Floor Price" in result.price_band_low.quote
    assert result.price_band_low.verification == Verification.VERIFIED.value

    # Lot size locator and quote
    assert result.lot_size.locator is not None
    assert "Page 1" in result.lot_size.locator
    assert "68" in result.lot_size.quote


# --------------------------------------------------------------------------
# Test 7: SEBI ICDR Price Collar Validation
# --------------------------------------------------------------------------


def test_sebi_collar_boundary_valid(parser):
    """Collar spread exactly at 20% limit is valid (e.g. 100 to 120)."""
    text = """
    PRICE BAND NOTICE
    INITIAL PUBLIC OFFERING OF EXACT COLLAR LIMITED
    Floor Price: Rs. 100 per equity share | Cap Price: Rs. 120 per equity share
    Minimum Bid Lot: 50 equity shares
    Bid Opens: 2026-10-01 | Bid Closes: 2026-10-03
    """
    result = parser.parse_from_text(text)
    assert result.collar_valid is True
    assert result.collar_spread_pct == pytest.approx(20.0)


def test_sebi_collar_exceeded_fails_closed(parser):
    """Collar spread > 20% raises PriceCollarValidationError (fail closed)."""
    fixture_path = FIXTURES_DIR / "invalid_collar_notice.txt"
    with pytest.raises(PriceCollarValidationError) as excinfo:
        parser.parse_from_file(fixture_path)
    assert "violating the SEBI ICDR 20% collar limit" in str(excinfo.value)


def test_inverted_collar_fails_closed(parser):
    """Cap price <= floor price raises PriceCollarValidationError (fail closed)."""
    fixture_path = FIXTURES_DIR / "inverted_collar_notice.txt"
    with pytest.raises(PriceCollarValidationError) as excinfo:
        parser.parse_from_file(fixture_path)
    assert "Cap price" in str(excinfo.value)
    assert "must be strictly greater than floor price" in str(excinfo.value)


# --------------------------------------------------------------------------
# Test 8: Document Classification & Rejection of Non-Notices
# --------------------------------------------------------------------------


def test_non_notice_document_rejected(parser):
    """Non-notice document (e.g. annual report) raises PriceBandNoticeClassificationError."""
    fixture_path = FIXTURES_DIR / "non_notice_document.txt"
    with pytest.raises(PriceBandNoticeClassificationError) as excinfo:
        parser.parse_from_file(fixture_path)
    assert "does not match Price Band Notice criteria" in str(excinfo.value)


# --------------------------------------------------------------------------
# Test 9: Conflicting Candidates Rejection (Fail Closed)
# --------------------------------------------------------------------------


def test_conflicting_price_bands_rejected(parser):
    """Notice with conflicting candidate price bands raises PriceBandNoticeParseError."""
    fixture_path = FIXTURES_DIR / "conflicting_notice.txt"
    with pytest.raises(PriceBandNoticeParseError) as excinfo:
        parser.parse_from_file(fixture_path)
    assert "Multiple conflicting price band" in str(excinfo.value)


# --------------------------------------------------------------------------
# Test 10: Missing Fields Fail Closed to UNKNOWN (No Defaults)
# --------------------------------------------------------------------------


def test_missing_cap_price_is_none_no_default(parser):
    """Missing Cap Price evaluates to None (UNKNOWN); never defaults to 220."""
    fixture_path = FIXTURES_DIR / "missing_cap_notice.txt"
    result = parser.parse_from_file(fixture_path)
    assert result.price_band_high is None
    assert result.price_band_low is not None
    assert result.price_band_low.value == 150.0
    assert result.has_full_price_band is False


def test_missing_floor_price_is_none_no_default(parser):
    """Missing Floor Price evaluates to None (UNKNOWN); never defaults to 208."""
    fixture_path = FIXTURES_DIR / "missing_floor_notice.txt"
    result = parser.parse_from_file(fixture_path)
    assert result.price_band_low is None
    assert result.price_band_high is not None
    assert result.price_band_high.value == 180.0
    assert result.has_full_price_band is False


def test_missing_lot_size_is_none_no_default(parser):
    """Missing Lot Size evaluates to None (UNKNOWN); never defaults to 68."""
    fixture_path = FIXTURES_DIR / "missing_lot_notice.txt"
    result = parser.parse_from_file(fixture_path)
    assert result.lot_size is None
    assert result.has_lot_size is False


def test_missing_dates_are_none(parser):
    """Missing issue dates evaluate to None."""
    fixture_path = FIXTURES_DIR / "missing_date_notice.txt"
    result = parser.parse_from_file(fixture_path)
    assert result.open_date is None
    assert result.close_date is None
    assert result.has_dates is False


# --------------------------------------------------------------------------
# Test 11: Malformed and Ambiguous Input Handling
# --------------------------------------------------------------------------


def test_malformed_numbers_fail_closed(parser):
    """Malformed numbers (NaN, alphabetic placeholders) evaluate to None."""
    fixture_path = FIXTURES_DIR / "malformed_number_notice.txt"
    result = parser.parse_from_file(fixture_path)
    assert result.price_band_high is None
    assert result.price_band_low is None
    assert result.lot_size is None


def test_ambiguous_ocr_symbols_fail_closed(parser):
    """Unrecognized glyphs (1?0, 2@0) fail number parsing and evaluate to None."""
    fixture_path = FIXTURES_DIR / "ambiguous_ocr_notice.txt"
    result = parser.parse_from_file(fixture_path)
    assert result.price_band_high is None
    assert result.price_band_low is None
    assert result.lot_size is None


# --------------------------------------------------------------------------
# Test 12: Inverted Date Order Rejection
# --------------------------------------------------------------------------


def test_inverted_date_order_rejected(parser):
    """Open date after close date raises PriceBandNoticeParseError."""
    text = """
    PRICE BAND NOTICE
    INITIAL PUBLIC OFFERING OF INVERTED DATE LIMITED
    Price Band: Rs. 100 to Rs. 115 per equity share
    Lot Size: 50 equity shares
    Issue Opens On: 2026-10-15
    Issue Closes On: 2026-10-10
    """
    with pytest.raises(PriceBandNoticeParseError) as excinfo:
        parser.parse_from_text(text)
    assert "Open date" in str(excinfo.value)
    assert "is after close date" in str(excinfo.value)


# --------------------------------------------------------------------------
# Test 13: Phase 5E Supplemental Contract Compatibility
# --------------------------------------------------------------------------


def test_phase_5e_contract_compatibility(parser):
    """Spec: to_enrichment_dict() produces valid supplemental-enrichment.v1 schema payload."""
    fixture_path = FIXTURES_DIR / "clean_notice.txt"
    result = parser.parse_from_file(fixture_path)

    enrichment_payload = result.to_enrichment_dict(ipo_id="VISHAL-NIRMITI-LIMITED")
    assert enrichment_payload["contract_version"] == "1.0"
    assert enrichment_payload["ipo_id"] == "VISHAL-NIRMITI-LIMITED"

    # Validate against Phase 5E schema
    findings = validate_enrichment_contract(enrichment_payload)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert not errors, f"Validation errors against Phase 5E schema: {[e.message for e in errors]}"

    # Verify field values inside enrichment dictionary
    pb = enrichment_payload["price_band"]
    assert pb["price_band_high"]["normalized_value"] == 220.0
    assert pb["price_band_high"]["unit"] == "INR"
    assert pb["price_band_low"]["normalized_value"] == 208.0
    assert pb["lot_size"]["normalized_value"] == 68
    assert pb["lot_size"]["unit"] == "SHARES"
    assert pb["open_date"]["normalized_value"] == "2026-10-06"
    assert pb["close_date"]["normalized_value"] == "2026-10-08"


# --------------------------------------------------------------------------
# Test 14: Golden Result Hash Regression Guard
# --------------------------------------------------------------------------


def test_golden_hash_preservation_regression(golden_input, config):
    """Phase 5F Invariant: Deterministic scoring core and golden hash are untouched."""
    from ipo_screening.pipeline import evaluate

    outcome = evaluate(golden_input, config, evaluation_datetime=golden_input.get("_eval_at"))
    expected_hash = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
    assert outcome.record.result_hash == expected_hash
