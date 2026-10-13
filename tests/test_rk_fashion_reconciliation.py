"""Validation and regression test suite for R.K. Fashion Accessories defect repair.

Forensic reconciliation asserting:
1. End-to-end extraction from RHP PDF without hard-coding or reference template.
2. Reconciliation of Module A, B, C, D, E data points from RHP source pages.
3. Repair of DEFECT-1: top-5 supplier concentration (34.10% -> criterion score 1/3).
4. Repair of DEFECT-2: domestic Indian costume jewellery CAGR (4.45% -> criterion score 1/5).
5. Repair of DEFECT-3: statutory operating cash flow after tax (-26.10, 3.09, -67.79 -> criterion score 0/5).
6. Total repaired score: 50.0 / 100 (Base 53.0, Penalties -3.0).
7. Bit-for-bit preservation of Vishal Nirmiti golden evaluation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ipo_screening.extraction.extractor import DocumentExtractor
from ipo_screening.pipeline import evaluate, load_config

REPO_ROOT = Path(__file__).parent.parent
RK_PDF = REPO_ROOT / "handoff" / "reference" / "U18109WB2010PLC144256-R.K Fashion accessories.pdf"
CONFIG_FILE = REPO_ROOT / "config" / "ipo-config.v1.5.0.json"
VISHAL_INPUT_FILE = REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json"
GOLDEN_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"


def test_vishal_nirmiti_golden_hash_preserved():
    """Golden evaluation result hash e84f8bc0... must remain bit-for-bit identical."""
    assert VISHAL_INPUT_FILE.exists()
    config = load_config(CONFIG_FILE)
    with open(VISHAL_INPUT_FILE, "r", encoding="utf-8") as f:
        canonical = json.load(f)

    eval_at = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    outcome = evaluate(canonical, config, mode="final", evaluation_datetime=eval_at)

    assert outcome.record.result_hash == GOLDEN_HASH
    assert outcome.record.score["final_score"] == 35.0
    assert outcome.record.score["penalties_total"] == -3.0
    assert outcome.record.verdict["verdict"] == "INSUFFICIENT_DATA"


def test_rk_fashion_accessories_extraction_and_reconciliation():
    """R.K. Fashion Accessories extracts ground-truth RHP data and scores accurately."""
    assert RK_PDF.exists(), f"Reference PDF missing at {RK_PDF}"

    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(RK_PDF, allow_fixture_fallbacks=False)

    # 1. Cover & Issue Identity
    assert canonical["company_name"] == "R.K. FASHION ACCESSORIES LIMITED"
    assert canonical["ipo_id"] == "R-K-FASHION-ACCESSORIES-LIMITED"
    assert canonical["board"] == "sme"
    assert canonical["issue"]["price_band_low"] == 77.0
    assert canonical["issue"]["price_band_high"] == 82.0
    assert canonical["issue"]["lot_size"] == 1600
    assert canonical["issue"]["fresh_shares"] == 4267200
    assert canonical["issue"]["pre_issue_shares"] == 11249563
    assert canonical["issue"]["post_issue_shares"] == 15516763
    assert canonical["issue"]["post_issue_eps"] == 4.05
    assert canonical["issue"]["fresh_issue"] == 3499.1
    assert canonical["issue"]["ofs"] == 0.0
    assert canonical["issue"]["ofs_sellers"] == []
    assert canonical["issue"]["open_date"] == "2026-10-05"
    assert canonical["issue"]["close_date"] == "2026-10-07"

    # 2. Module A: Multi-period Financials from Basis for Offer Price & Cash Flow
    periods = canonical["financials"]["periods"]
    assert len(periods) == 3
    assert [p["fy"] for p in periods] == ["FY2024", "FY2025", "FY2026"]

    fy24 = periods[0]
    assert fy24["revenue"] == 1328.49
    assert fy24["ebitda"] == 11.38
    assert fy24["pat"] == 94.78
    assert fy24["net_worth"] == 781.77
    assert fy24["total_debt"] == 60.90
    assert fy24["cfo"] == -26.10  # Repaired statutory operating cash flow (was -7.13 pre-tax)
    assert fy24["capex"] == 118.79
    assert fy24["interest_expense"] == 0.33
    assert fy24["disclosed_roce_pct"] == 13.32

    fy25 = periods[1]
    assert fy25["revenue"] == 1777.19
    assert fy25["ebitda"] == 297.55
    assert fy25["pat"] == 199.72
    assert fy25["net_worth"] == 981.49
    assert fy25["total_debt"] == 60.88
    assert fy25["cfo"] == 3.09  # Repaired statutory operating cash flow (was 77.61 pre-tax)
    assert fy25["capex"] == 0.32
    assert fy25["interest_expense"] == 0.24
    assert fy25["disclosed_roce_pct"] == 29.13

    fy26 = periods[2]
    assert fy26["revenue"] == 3035.71
    assert fy26["ebitda"] == 733.51
    assert fy26["pat"] == 628.69
    assert fy26["net_worth"] == 1616.22
    assert fy26["total_debt"] == 170.32
    assert fy26["cfo"] == -67.79  # Repaired statutory operating cash flow (was 114.72 pre-tax)
    assert fy26["capex"] == 36.35
    assert fy26["interest_expense"] == 0.97
    assert fy26["disclosed_roce_pct"] == 57.74

    # 3. Module B: Peer Comparison Table
    peers = canonical["peers"]
    assert len(peers) >= 1
    banaras = next(p for p in peers if "Banaras" in p["name"])
    assert banaras["name"] == "Banaras Beads Limited"
    assert banaras["pe"] == 44.31
    assert banaras["pb"] == 1.36
    assert banaras["roe_pct"] == 3.08
    assert banaras["as_of"] == "2026-09-28"

    # 4. Module D: Capital Structure & Governance
    assert canonical["capital_structure"]["promoter_pre_pct"] == 99.67
    assert canonical["capital_structure"]["promoter_post_pct"] == 72.25
    assert canonical["capital_structure"]["promoter_pledge_pct"] == 0.0
    assert canonical["capital_structure"]["promoter_lockin_in_place"] is True

    assert canonical["governance"]["auditor_opinion"] == "unqualified"
    assert canonical["governance"]["auditor_changed_3y"] is False
    assert canonical["governance"]["auditor_reputed"] is False
    assert canonical["governance"]["litigation_bucket"] == "clean"
    assert canonical["governance"]["sebi_ed_action_active"] is False
    assert canonical["governance"]["rpt_pct_revenue"] == 10.79

    # 5. Module E: Business & Industry
    assert canonical["business"]["top5_customer_pct"] == 11.11
    assert canonical["business"]["top5_supplier_pct"] == 34.10  # Repaired DEFECT-1
    assert canonical["business"]["industry_cagr_pct"] == 4.45  # Repaired DEFECT-2 (was 8.0)
    assert canonical["business"]["industry_scope"] == "india"
    assert canonical["business"]["industry_forecast_period"] == "2025-2031"
    assert canonical["business"]["industry_source"] == "India Costume Jewelry Market Report / RHP Section V"
    assert canonical["business"]["moat_rating"] is None
    assert canonical["business"]["visibility_rating"] is None

    # 6. Pipeline Evaluation
    config = load_config(CONFIG_FILE)
    eval_at = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    outcome = evaluate(canonical, config, mode="final", evaluation_datetime=eval_at)

    assert outcome.record.validation["ok"] is True
    assert outcome.record.score["final_score"] == 50.0  # 55.0 - 2 (supplier) - 2 (cagr) - 1 (cfo)
    assert outcome.record.score["base_score"] == 53.0
    assert outcome.record.score["penalties_total"] == -3.0
    assert outcome.record.confidence["level"] == "Low"
    assert outcome.record.confidence["completeness_pct"] == 75.0
    assert outcome.record.score["lower_bound"] == 37.0
    assert outcome.record.score["upper_bound"] == 75.0
    assert outcome.record.verdict["verdict"] == "INSUFFICIENT_DATA"

    # Module assertions
    modules = {m["module_id"]: m for m in outcome.record.score["modules"]}

    # Module A: 20 / 25 (cfo_quality drops from 1 to 0 due to negative cumulative CFO)
    assert modules["A"]["score"] == 20.0
    assert modules["A"]["unknown_points"] == 0
    cfo_crit = next(c for c in modules["A"]["criteria"] if c["criterion_id"] == "cfo_quality")
    assert cfo_crit["state"] == "SCORED"
    assert cfo_crit["score"] == 0.0

    # Module B: 10 / 16, pe_vs_peers scored 8.0 vs Banaras Beads
    assert modules["B"]["score"] == 10.0
    pe_crit = next(c for c in modules["B"]["criteria"] if c["criterion_id"] == "pe_vs_peers")
    assert pe_crit["state"] == "SCORED"
    assert pe_crit["score"] == 8.0

    # Module C: 10 / 11 of available points scored (OFS=0, 100% fresh, dilution 27.5% > 25% -> 0 pts)
    assert modules["C"]["score"] == 10.0
    fresh_crit = next(c for c in modules["C"]["criteria"] if c["criterion_id"] == "fresh_share")
    assert fresh_crit["state"] == "SCORED"
    assert fresh_crit["score"] == 3.0
    ofs_seller_crit = next(c for c in modules["C"]["criteria"] if c["criterion_id"] == "ofs_seller_type")
    assert ofs_seller_crit["score"] == 2.0
    prom_ofs_crit = next(c for c in modules["C"]["criteria"] if c["criterion_id"] == "promoter_ofs_pct")
    assert prom_ofs_crit["state"] == "SCORED"
    assert prom_ofs_crit["score"] == 2.0

    # Module D: 11 / 15, 0 unknown
    assert modules["D"]["score"] == 11.0
    assert modules["D"]["unknown_points"] == 0
    prom_post_crit = next(c for c in modules["D"]["criteria"] if c["criterion_id"] == "promoter_post_holding")
    assert prom_post_crit["state"] == "SCORED"
    assert prom_post_crit["score"] == 4.0
    aud_crit = next(c for c in modules["D"]["criteria"] if c["criterion_id"] == "auditor")
    assert aud_crit["state"] == "SCORED"
    assert aud_crit["score"] == 1.0

    # Module E: 2 / 8, 7 unknown points (moat 5 pts, visibility 2 pts unextracted)
    assert modules["E"]["score"] == 2.0
    assert modules["E"]["unknown_points"] == 7.0
    ind_crit = next(c for c in modules["E"]["criteria"] if c["criterion_id"] == "industry_growth")
    assert ind_crit["state"] == "SCORED"
    assert ind_crit["score"] == 1.0  # Repaired: 4.45% in band >= 0% scores 1/5 (was 8.0% -> 3/5)
    conc_crit = next(c for c in modules["E"]["criteria"] if c["criterion_id"] == "concentration")
    assert conc_crit["state"] == "SCORED"
    assert conc_crit["score"] == 1.0  # Repaired: effective conc 34.10% in <=50% scores 1/3 (was 11.11% -> 3/3)


def test_defect1_supplier_concentration_reconciliation():
    """DEFECT-1: Top-5 supplier concentration extracted from RHP p.51/p.354 and correctly scores 1/3."""
    extractor = DocumentExtractor()
    canonical, _ = extractor.extract_from_pdf(RK_PDF, allow_fixture_fallbacks=False)

    top5_cust = canonical["business"].get("top5_customer_pct")
    top5_supp = canonical["business"].get("top5_supplier_pct")

    assert top5_cust == pytest.approx(11.11)
    assert top5_supp == pytest.approx(34.10)

    # Effective concentration must be max(customer, supplier) = 34.10%
    effective_concentration = max(top5_cust, top5_supp)
    assert effective_concentration == pytest.approx(34.10)

    # Under v1.5.0 config, 34.10% falls in <= 50% band -> 1.0 / 3.0 pts
    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final", evaluation_datetime=datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc))
    mod_e = next(m for m in outcome.record.score["modules"] if m["module_id"] == "E")
    conc_crit = next(c for c in mod_e["criteria"] if c["criterion_id"] == "concentration")
    assert conc_crit["state"] == "SCORED"
    assert conc_crit["score"] == 1.0


def test_defect2_industry_cagr_selection_reconciliation():
    """DEFECT-2: Selected CAGR is domestic Indian costume jewellery (4.45%), not global 8.00%."""
    extractor = DocumentExtractor()
    canonical, _ = extractor.extract_from_pdf(RK_PDF, allow_fixture_fallbacks=False)

    biz = canonical["business"]
    assert biz["industry_cagr_pct"] == pytest.approx(4.45)
    assert biz["industry_scope"] == "india"
    assert biz["industry_forecast_period"] == "2025-2031"
    assert biz["industry_source"] == "India Costume Jewelry Market Report / RHP Section V"

    # Prove global CAGR occurrences (8.00% on p.192, 5.28% on p.190) did NOT become the selected value
    assert biz["industry_cagr_pct"] != pytest.approx(8.00)
    assert biz["industry_cagr_pct"] != pytest.approx(5.28)

    # Under v1.5.0 config, 4.45% falls into band >= 0% -> 1.0 / 5.0 pts
    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final", evaluation_datetime=datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc))
    mod_e = next(m for m in outcome.record.score["modules"] if m["module_id"] == "E")
    ind_crit = next(c for c in mod_e["criteria"] if c["criterion_id"] == "industry_growth")
    assert ind_crit["state"] == "SCORED"
    assert ind_crit["score"] == 1.0


def test_defect3_operating_cash_flow_field_selection():
    """DEFECT-3: Extractor selects statutory operating cash flow after tax, yielding 0/5 for negative CFO/PAT."""
    extractor = DocumentExtractor()
    canonical, _ = extractor.extract_from_pdf(RK_PDF, allow_fixture_fallbacks=False)

    periods = canonical["financials"]["periods"]
    fy24_cfo = next(p["cfo"] for p in periods if p["fy"] == "FY2024")
    fy25_cfo = next(p["cfo"] for p in periods if p["fy"] == "FY2025")
    fy26_cfo = next(p["cfo"] for p in periods if p["fy"] == "FY2026")

    # Statutory post-tax operating cash flow values
    assert fy24_cfo == pytest.approx(-26.10)
    assert fy25_cfo == pytest.approx(3.09)
    assert fy26_cfo == pytest.approx(-67.79)

    # Pre-tax values must NOT silently re-enter canonical CFO fields
    for p in periods:
        assert p["cfo"] not in [-7.13, 77.60, 77.61, 114.72]

    # Cumulative calculations
    cum_cfo = sum(p["cfo"] for p in periods)
    cum_pat = sum(p["pat"] for p in periods)
    cfo_pat_ratio = cum_cfo / cum_pat

    assert cum_cfo == pytest.approx(-90.80)
    assert cum_pat == pytest.approx(923.19)
    assert cfo_pat_ratio == pytest.approx(-0.09835, rel=1e-3)

    # Negative ratio scores 0.0 under v1.5.0 config
    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final", evaluation_datetime=datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc))
    mod_a = next(m for m in outcome.record.score["modules"] if m["module_id"] == "A")
    cfo_crit = next(c for c in mod_a["criteria"] if c["criterion_id"] == "cfo_quality")
    assert cfo_crit["state"] == "SCORED"
    assert cfo_crit["score"] == 0.0
