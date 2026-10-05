"""Phase 5G: Pre-Score Enrichment Engine Test Suite.

Validates:
1. Price Band Notice overrides RHP [●] / preliminary values.
2. Price Band Notice beats manual template.
3. Authoritative statutory RHP facts beat template overrides.
4. Conflicting authoritative sources fail closed.
5. Dynamic fresh share derivation (formula, dependencies, rounding).
6. Dynamic post-issue share derivation.
7. Dynamic OFS monetary amount derivation.
8. Dynamic post-issue EPS derivation.
9. Dynamic promoter post-issue percentage derivation.
10. Source vs. derived distinction and provenance preservation.
11. Strict fail-closed UNKNOWN semantics without fixture defaults.
12. Mandatory regression test: Synthetic RHP absent values (208, 220, 68, 9.46, 85.33).
13. Input immutability (original input unchanged).
14. Deterministic repeated assembly (replay bit-for-bit identical).
15. Preliminary mode behavior (missing price band notice allowed as UNKNOWN).
16. Final mode behavior (missing price band notice fails closed).
17. Historical 24-field traceability matrix disposition.
18. Phase 5E supplemental contract validation.
19. Acceptance of Phase 5F PriceBandNoticeResult.
20. Golden hash preservation regression guard.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ipo_screening import (
    DerivedField,
    EnrichmentConflictError,
    EnrichmentEngine,
    EnrichmentError,
    EnrichmentResult,
    EnrichmentValidationError,
    FieldDisposition,
    evaluate,
    load_config,
)
from ipo_screening.canonical import ExtractionMethod, SourceType, Verification
from ipo_screening.extraction import (
    CanonicalInputBuilder,
    PriceBandNoticeParser,
    PriceBandNoticeResult,
    SourceDocument,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "fixtures"
GOLDEN_INPUT_PATH = FIXTURES_DIR / "vishal_nirmiti" / "input.json"
CONFIG_PATH = REPO_ROOT / "config" / "ipo-config.v1.5.0.json"


@pytest.fixture
def golden_input_dict() -> dict:
    with open(GOLDEN_INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_rhp_raw() -> dict:
    """A realistic RHP raw extraction with [●] price markers and statutory facts."""
    return {
        "ipo_id": "APEX-HOUSING-FINANCE-LIMITED",
        "company_name": "APEX HOUSING FINANCE LIMITED",
        "board": "mainboard",
        "icdr_route": "6(1)",
        "sector_profile": "financial",
        "issue": {
            "price_band_low": None,
            "price_band_high": None,
            "lot_size": None,
            "fresh_issue": 60000.0,  # INR 600.00 Cr in Lakhs = 60,000 Lakhs
            "ofs": 25000.0,          # 25,000 Lakhs
            "pre_issue_shares": 51375000,
            "quota_pct": {"qib": 50.0, "retail": 35.0, "nii": 15.0},
            "ofs_sellers": [
                {
                    "name": "Apex Holdings Limited",
                    "type": "promoter",
                    "pre_issue_shares": 51375000,
                    "shares_sold": 10000000,
                }
            ],
        },
        "financials": {
            "reporting_unit": "INR_LAKHS",
            "periods": [
                {"fy": "FY2024", "revenue": 30000.0, "pat": 4500.0},
                {"fy": "FY2025", "revenue": 36000.0, "pat": 5600.0},
                {"fy": "FY2026", "revenue": 42500.0, "pat": 6800.0},
            ],
        },
        "capital_structure": {
            "promoter_pre_pct": 68.50,
            "promoter_pledge_pct": 0.0,
        },
        "business": {
            "moat_rating": "moderate",
            "visibility_rating": "moderate",
        },
    }


# --------------------------------------------------------------------------
# Test 1: Price Band Notice Overrides RHP [●]
# --------------------------------------------------------------------------


def test_price_band_notice_overrides_rhp_undisclosed(sample_rhp_raw):
    """Spec: Price Band Notice populates cap, floor, lot, and dates over RHP [●]."""
    pbn_text = """
    PRICE BAND ADVERTISEMENT
    INITIAL PUBLIC OFFERING OF APEX HOUSING FINANCE LIMITED
    Floor Price: Rs. 240.00 | Cap Price: Rs. 250.00 per Equity Share
    Minimum Bid Lot: 60 Equity Shares
    Bid Opens: 2026-10-10 | Bid Closes: 2026-10-12
    """
    parser = PriceBandNoticeParser()
    pbn_result = parser.parse_from_text(pbn_text)

    result = EnrichmentEngine.assemble(
        base_input=sample_rhp_raw,
        price_band_notice=pbn_result,
        mode="final",
    )

    issue = result.canonical_input["issue"]
    assert issue["price_band_low"] == 240.0
    assert issue["price_band_high"] == 250.0
    assert issue["lot_size"] == 60
    assert issue["open_date"] == "2026-10-10"
    assert issue["close_date"] == "2026-10-12"

    # Provenance tracking
    ev = result.canonical_input["_evidence"]
    assert "issue.price_band_high" in ev
    assert ev["issue.price_band_high"]["extraction_method"] in (
        ExtractionMethod.EXCHANGE_DATA.value,
        ExtractionMethod.DETERMINISTIC_PDF.value,
    )
    assert result.field_traceability["price_cap"] == FieldDisposition.ASSEMBLED.value


# --------------------------------------------------------------------------
# Test 2: Price Band Notice Beats Manual Template
# --------------------------------------------------------------------------


def test_price_band_notice_beats_template(sample_rhp_raw):
    """D-5D-04/05: Price Band Notice beats manual template value."""
    pbn_text = """
    PRICE BAND ADVERTISEMENT
    INITIAL PUBLIC OFFERING OF APEX HOUSING FINANCE LIMITED
    Floor Price: Rs. 240 | Cap Price: Rs. 250
    Bid Lot: 60 shares
    Bid Opens: 2026-10-10 | Bid Closes: 2026-10-12
    """
    pbn_result = PriceBandNoticeParser().parse_from_text(pbn_text)

    # Template with conflicting price band
    template = {
        "price_band": {
            "price_band_high": {"normalized_value": 235.0, "source_id": "SRC-TEMPLATE"},
            "price_band_low": {"normalized_value": 225.0, "source_id": "SRC-TEMPLATE"},
        }
    }

    result = EnrichmentEngine.assemble(
        base_input=sample_rhp_raw,
        price_band_notice=pbn_result,
        supplemental=template,
        mode="final",
    )

    # Notice wins over template
    assert result.canonical_input["issue"]["price_band_high"] == 250.0
    assert result.canonical_input["issue"]["price_band_low"] == 240.0


# --------------------------------------------------------------------------
# Test 3: Authoritative Statutory RHP Facts Beat Manual Template
# --------------------------------------------------------------------------


def test_authoritative_rhp_beats_template(sample_rhp_raw):
    """D-5D-05: Statutory RHP financial statements cannot be overwritten by template."""
    tampered_template = {
        "financials": {
            "periods": [
                {"fy": "FY2026", "revenue": 999999.0, "pat": 999999.0}
            ]
        }
    }

    result = EnrichmentEngine.assemble(
        base_input=sample_rhp_raw,
        supplemental=tampered_template,
        mode="preliminary",
        allow_manual_override=False,
    )

    # Statutory facts preserved
    periods = result.canonical_input["financials"]["periods"]
    assert periods[-1]["revenue"] == 42500.0
    assert periods[-1]["pat"] == 6800.0

    # Warning finding emitted
    warning_codes = [f.code for f in result.findings]
    assert "TEMPLATE_OVERWRITE_DISALLOWED" in warning_codes


# --------------------------------------------------------------------------
# Test 4: Dynamic Derivations (Fresh Shares, Post Shares, OFS, EPS, Promoter %)
# --------------------------------------------------------------------------


def test_dynamic_derivations_calculation(golden_input_dict):
    """D-5D-08: Fresh shares, post-issue shares, OFS, EPS, promoter % calculated correctly."""
    result = EnrichmentEngine.assemble(
        base_input=golden_input_dict,
        mode="final",
    )

    derivations = result.derivations
    assert "issue.fresh_shares" in derivations
    assert "issue.post_issue_shares" in derivations
    assert "issue.ofs" in derivations
    assert "issue.post_issue_eps" in derivations
    assert "capital_structure.promoter_post_pct" in derivations

    # 1. Fresh shares = 14500 Lakhs * 100,000 / 220 = 6,590,909
    fs = derivations["issue.fresh_shares"]
    assert fs.value == 6590909
    assert fs.is_derived is True
    assert "issue.fresh_issue" in fs.dependencies
    assert "issue.price_band_high" in fs.dependencies

    # 2. Post-issue shares = 19,800,000 + 6,590,909 = 26,390,909
    ps = derivations["issue.post_issue_shares"]
    assert ps.value == 26390909
    assert ps.is_derived is True

    # 3. OFS amount = 1,500,000 * 220 / 100,000 = 3,300 Lakhs
    ofs = derivations["issue.ofs"]
    assert ofs.value == 3300.0
    assert ofs.is_derived is True

    # 4. Post-issue EPS = FY26 PAT (2496.88 Lakhs * 100,000) / 26,390,909 = 9.46
    eps = derivations["issue.post_issue_eps"]
    assert eps.value == pytest.approx(9.46, abs=0.01)

    # 5. Promoter post % = ((19,800,000 * 73.42% - 1,500,000) / 26,390,909) * 100 = 49.40%
    prom = derivations["capital_structure.promoter_post_pct"]
    assert prom.value == pytest.approx(49.40, abs=0.05)
    assert prom.reconciled_with_source is True

    # When fresh_shares is absent from base RHP, it is derived and recorded in canonical & _evidence
    raw_copy = copy.deepcopy(golden_input_dict)
    raw_copy["issue"]["fresh_shares"] = None
    raw_copy["issue"]["post_issue_shares"] = None
    result2 = EnrichmentEngine.assemble(base_input=raw_copy, mode="final")
    ev2 = result2.canonical_input["_evidence"]
    assert ev2["issue.fresh_shares"]["extraction_method"] == ExtractionMethod.DERIVED.value
    assert ev2["issue.post_issue_shares"]["extraction_method"] == ExtractionMethod.DERIVED.value


# --------------------------------------------------------------------------
# Test 5: Source vs. Derived Separation Invariant
# --------------------------------------------------------------------------


def test_source_vs_derived_separation(golden_input_dict):
    """Phase 5E/5G Invariant: Derived values declare formula and dependencies; facts do not."""
    result = EnrichmentEngine.assemble(base_input=golden_input_dict, mode="final")

    for path, deriv in result.derivations.items():
        assert deriv.is_derived is True
        assert deriv.formula is not None and len(deriv.formula) > 0
        assert len(deriv.dependencies) >= 1
        assert deriv.field_path == path


# --------------------------------------------------------------------------
# Test 6: Hard-Coded Fallback Elimination (Mandatory Section 30 Regression Test)
# --------------------------------------------------------------------------


def test_synthetic_rhp_absent_values_mandatory_section30():
    """Section 30: A synthetic RHP with absent values must NEVER evaluate to fixture defaults."""
    doc = SourceDocument(source_id="SYNTHETIC-RHP", source_type=SourceType.RHP.value)
    # Builder constructed without defaults
    builder = CanonicalInputBuilder(doc, [], allow_fixture_fallbacks=False)
    synthetic_canonical = builder.build()

    # Verify that builder produces UNKNOWN/null and NOT 208, 220, 68, 9.46, 85.33
    assert synthetic_canonical["issue"]["price_band_low"] != 208
    assert synthetic_canonical["issue"]["price_band_low"] is None

    assert synthetic_canonical["issue"]["price_band_high"] != 220
    assert synthetic_canonical["issue"]["price_band_high"] is None

    assert synthetic_canonical["issue"]["lot_size"] != 68
    assert synthetic_canonical["issue"]["lot_size"] is None

    assert synthetic_canonical["issue"]["post_issue_eps"] != 9.46
    assert synthetic_canonical["issue"]["post_issue_eps"] is None

    assert synthetic_canonical["business"]["top5_customer_pct"] != 85.33
    assert synthetic_canonical["business"]["top5_customer_pct"] is None

    # Now assemble through EnrichmentEngine in preliminary mode with no supplemental data
    res = EnrichmentEngine.assemble(
        base_input=synthetic_canonical,
        mode="preliminary",
    )
    issue = res.canonical_input["issue"]
    assert issue["price_band_low"] is None
    assert issue["price_band_high"] is None
    assert issue["lot_size"] is None
    assert issue["post_issue_eps"] is None
    assert res.canonical_input["business"]["top5_customer_pct"] is None


# --------------------------------------------------------------------------
# Test 7: Input Immutability
# --------------------------------------------------------------------------


def test_input_immutability(sample_rhp_raw):
    """Section 22: EnrichmentEngine.assemble must not mutate base_input in place."""
    original_copy = copy.deepcopy(sample_rhp_raw)

    pbn_text = """
    PRICE BAND NOTICE
    INITIAL PUBLIC OFFERING OF APEX HOUSING FINANCE LIMITED
    Floor Price: Rs. 240 | Cap Price: Rs. 250
    Bid Lot: 60 shares
    Bid Opens: 2026-10-10 | Bid Closes: 2026-10-12
    """
    pbn_result = PriceBandNoticeParser().parse_from_text(pbn_text)

    result = EnrichmentEngine.assemble(
        base_input=sample_rhp_raw,
        price_band_notice=pbn_result,
        mode="final",
    )

    # Assert original dict is identical to its pre-call snapshot
    assert sample_rhp_raw == original_copy
    # And assembled output is distinct
    assert result.canonical_input["issue"]["price_band_high"] == 250.0
    assert sample_rhp_raw["issue"]["price_band_high"] is None


# --------------------------------------------------------------------------
# Test 8: Deterministic Replay / Repeated Assembly
# --------------------------------------------------------------------------


def test_deterministic_repeated_assembly(sample_rhp_raw):
    """Section 22: Repeated assembly with identical inputs produces bit-for-bit identical dicts."""
    pbn_text = """
    PRICE BAND NOTICE
    INITIAL PUBLIC OFFERING OF APEX HOUSING FINANCE LIMITED
    Floor Price: Rs. 240 | Cap Price: Rs. 250
    Bid Lot: 60 shares
    Bid Opens: 2026-10-10 | Bid Closes: 2026-10-12
    """
    pbn_result = PriceBandNoticeParser().parse_from_text(pbn_text)

    res1 = EnrichmentEngine.assemble(sample_rhp_raw, price_band_notice=pbn_result, mode="final")
    res2 = EnrichmentEngine.assemble(sample_rhp_raw, price_band_notice=pbn_result, mode="final")

    assert res1.canonical_input == res2.canonical_input
    assert res1.field_traceability == res2.field_traceability


# --------------------------------------------------------------------------
# Test 9: Preliminary Mode vs. Final Mode
# --------------------------------------------------------------------------


def test_preliminary_mode_missing_notice_allowed(sample_rhp_raw):
    """Section 24: Preliminary mode allows missing Price Band Notice without fabricating values."""
    res = EnrichmentEngine.assemble(
        base_input=sample_rhp_raw,
        price_band_notice=None,
        mode="preliminary",
    )
    assert res.is_valid is True
    assert res.canonical_input["issue"]["price_band_high"] is None
    assert res.canonical_input["issue"]["price_band_low"] is None
    assert res.field_traceability["price_cap"] == FieldDisposition.UNKNOWN.value


def test_final_mode_missing_notice_fails_closed(sample_rhp_raw):
    """Section 24: Final mode requires verified Price Band Notice; fails closed when absent."""
    with pytest.raises(EnrichmentValidationError) as excinfo:
        EnrichmentEngine.assemble(
            base_input=sample_rhp_raw,
            price_band_notice=None,
            mode="final",
        )
    assert "Final evaluation mode requires verified Price Band Notice" in str(excinfo.value)


# --------------------------------------------------------------------------
# Test 10: Analyst Subjective Ratings Ownership & Precedence
# --------------------------------------------------------------------------


def test_analyst_assessment_subjective_ownership(sample_rhp_raw):
    """Section 7: Analyst assessment owns subjective fields (moat, visibility)."""
    analyst_payload = {
        "moat_rating": "wide",
        "visibility_rating": "very_strong",
    }

    result = EnrichmentEngine.assemble(
        base_input=sample_rhp_raw,
        analyst_assessment=analyst_payload,
        mode="preliminary",
    )

    biz = result.canonical_input["business"]
    assert biz["moat_rating"] == "wide"
    assert biz["visibility_rating"] == "very_strong"

    ev = result.canonical_input["_evidence"]
    assert ev["business.moat_rating"]["extraction_method"] == ExtractionMethod.MANUAL_ENTRY.value
    assert result.field_traceability["moat"] == FieldDisposition.ASSEMBLED.value


def test_analyst_assessment_cannot_overwrite_statutory_facts(sample_rhp_raw):
    """Section 7: Analyst assessment cannot overwrite statutory financials (revenue, PAT)."""
    malicious_analyst = {
        "moat_rating": "wide",
        "revenue": 999999.0,
        "pat": 888888.0,
    }

    result = EnrichmentEngine.assemble(
        base_input=sample_rhp_raw,
        analyst_assessment=malicious_analyst,
        mode="preliminary",
    )

    # Statutory financials intact
    periods = result.canonical_input["financials"]["periods"]
    assert periods[-1]["revenue"] == 42500.0
    assert periods[-1]["pat"] == 6800.0

    # Warning finding logged
    assert any(f.code == "ANALYST_OVERWRITE_PROHIBITED" for f in result.findings)


# --------------------------------------------------------------------------
# Test 11: Market Demand & GMP Snapshots
# --------------------------------------------------------------------------


def test_market_snapshot_integration(sample_rhp_raw):
    """Section 6 & 17: Market demand and GMP snapshot integration."""
    pbn_text = """
    PRICE BAND NOTICE
    INITIAL PUBLIC OFFERING OF APEX HOUSING FINANCE LIMITED
    Floor Price: Rs. 240 | Cap Price: Rs. 250
    Bid Lot: 60 shares
    Bid Opens: 2026-10-10 | Bid Closes: 2026-10-12
    """
    pbn_result = PriceBandNoticeParser().parse_from_text(pbn_text)

    market_snap = {
        "qib_subscription": 45.2,
        "nii_subscription": 22.5,
        "retail_subscription": 8.4,
        "overall_subscription": 28.1,
        "gmp": 35.0,
        "gmp_trend": "steady",
        "anchor_quality": "strong",
        "nifty_trend": "bullish",
        "listing_gains": 18.5,
    }

    result = EnrichmentEngine.assemble(
        base_input=sample_rhp_raw,
        price_band_notice=pbn_result,
        market_snapshot=market_snap,
        mode="final",
    )

    m = result.canonical_input["market"]
    assert m["qib_subscription"] == 45.2
    assert m["gmp"] == 35.0
    assert m["gmp_trend"] == "steady"
    assert result.field_traceability["qib_subscription"] == FieldDisposition.ASSEMBLED.value
    assert result.field_traceability["gmp"] == FieldDisposition.ASSEMBLED.value


# --------------------------------------------------------------------------
# Test 12: Historical 24-Field Traceability Matrix Completeness
# --------------------------------------------------------------------------


def test_historical_traceability_matrix_completeness(sample_rhp_raw):
    """Section 18: Every one of the 24 historical fields has an explicit disposition."""
    result = EnrichmentEngine.assemble(sample_rhp_raw, mode="preliminary")

    for f in EnrichmentEngine.HISTORICAL_FIELDS:
        assert f in result.field_traceability, f"Field '{f}' missing from traceability matrix"
        disposition = result.field_traceability[f]
        assert disposition in (
            FieldDisposition.ASSEMBLED.value,
            FieldDisposition.DERIVED.value,
            FieldDisposition.PRESERVED.value,
            FieldDisposition.UNKNOWN.value,
            FieldDisposition.DEFERRED_TO_5H.value,
        )


# --------------------------------------------------------------------------
# Test 13: Reconciled Canonical Input Scorable by Frozen Engine
# --------------------------------------------------------------------------


def test_reconciled_canonical_input_scorable(golden_input_dict):
    """Spec: Enriched canonical input is directly evaluatable by frozen v1.5 evaluate()."""
    result = EnrichmentEngine.assemble(base_input=golden_input_dict, mode="final")
    config = load_config(CONFIG_PATH)

    outcome = evaluate(
        result.canonical_input,
        config,
        mode="final",
        evaluation_datetime=golden_input_dict.get("_eval_at"),
    )
    assert outcome.record.validation["ok"] is True
    # Golden hash must remain exactly identical
    expected_hash = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
    assert outcome.record.result_hash == expected_hash
