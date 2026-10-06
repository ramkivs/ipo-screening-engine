"""Validation and regression test suite for R.K. Fashion Accessories defect repair.

Forensic reconciliation asserting:
1. End-to-end extraction from RHP PDF without hard-coding or reference template.
2. Reconciliation of Module A, B, C, D, E data points from RHP source pages.
3. Module score verification and unknown points reduction.
4. Bit-for-bit preservation of Vishal Nirmiti golden evaluation.
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
    canonical, report = extractor.extract_from_pdf(RK_PDF)

    # 1. Cover & Issue Identity
    assert canonical["company_name"] == "R.K. FASHION ACCESSORIES LIMITED"
    assert canonical["ipo_id"] == "R-K-FASHION-ACCESSORIES-LIMITED"
    assert canonical["board"] == "mainboard"
    assert canonical["issue"]["price_band_low"] == 77.0
    assert canonical["issue"]["price_band_high"] == 82.0
    assert canonical["issue"]["fresh_shares"] == 4267200
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
    assert fy24["cfo"] == -7.13
    assert fy24["capex"] == 118.79
    assert fy24["interest_expense"] == 0.33
    assert fy24["disclosed_roce_pct"] == 13.32

    fy25 = periods[1]
    assert fy25["revenue"] == 1777.19
    assert fy25["ebitda"] == 297.55
    assert fy25["pat"] == 199.72
    assert fy25["net_worth"] == 981.49
    assert fy25["total_debt"] == 60.88
    assert fy25["cfo"] == 77.61
    assert fy25["capex"] == 0.32
    assert fy25["interest_expense"] == 0.24
    assert fy25["disclosed_roce_pct"] == 29.13

    fy26 = periods[2]
    assert fy26["revenue"] == 3035.71
    assert fy26["ebitda"] == 733.51
    assert fy26["pat"] == 628.69
    assert fy26["net_worth"] == 1616.22
    assert fy26["total_debt"] == 170.32
    assert fy26["cfo"] == 114.72
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
    assert canonical["capital_structure"]["promoter_post_pct"] == 72.25
    assert canonical["capital_structure"]["promoter_pledge_pct"] == 0.0
    assert canonical["capital_structure"]["promoter_lockin_in_place"] is True

    assert canonical["governance"]["auditor_opinion"] == "unqualified"
    assert canonical["governance"]["auditor_changed_3y"] is False
    assert canonical["governance"]["auditor_reputed"] is False
    assert canonical["governance"]["litigation_bucket"] == "clean"
    assert canonical["governance"]["sebi_ed_action_active"] is False

    # 5. Module E: Business & Industry
    assert canonical["business"]["top5_customer_pct"] == 11.11
    assert canonical["business"]["industry_cagr_pct"] == 8.0
    assert canonical["business"]["industry_scope"] == "global"
    assert canonical["business"]["industry_forecast_period"] == "2026-2035"

    # 6. Pipeline Evaluation
    config = load_config(CONFIG_FILE)
    eval_at = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    outcome = evaluate(canonical, config, mode="final", evaluation_datetime=eval_at)

    assert outcome.record.validation["ok"] is True
    assert outcome.record.score["final_score"] == 61.0
    assert outcome.record.score["penalties_total"] == -3.0
    assert outcome.record.confidence["level"] == "Medium"
    assert outcome.record.confidence["completeness_pct"] >= 80.0

    # Module assertions
    modules = {m["module_id"]: m for m in outcome.record.score["modules"]}

    # Module A: 21 / 25, 0 unknown
    assert modules["A"]["score"] == 21.0
    assert modules["A"]["unknown_points"] == 0

    # Module B: 10 / 16, pe_vs_peers scored 8.0 vs Banaras Beads
    assert modules["B"]["score"] == 10.0
    pe_crit = next(c for c in modules["B"]["criteria"] if c["criterion_id"] == "pe_vs_peers")
    assert pe_crit["state"] == "SCORED"
    assert pe_crit["score"] == 8.0

    # Module C: 11 / 11 of available points scored (OFS=0, 100% fresh)
    assert modules["C"]["score"] == 11.0
    fresh_crit = next(c for c in modules["C"]["criteria"] if c["criterion_id"] == "fresh_share")
    assert fresh_crit["state"] == "SCORED"
    assert fresh_crit["score"] == 3.0
    ofs_seller_crit = next(c for c in modules["C"]["criteria"] if c["criterion_id"] == "ofs_seller_type")
    assert ofs_seller_crit["state"] == "SCORED"
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

    # Module E: 11 / 15, 0 unknown
    assert modules["E"]["score"] == 11.0
    assert modules["E"]["unknown_points"] == 0
    ind_crit = next(c for c in modules["E"]["criteria"] if c["criterion_id"] == "industry_growth")
    assert ind_crit["state"] == "SCORED"
    assert ind_crit["score"] == 3.0
    conc_crit = next(c for c in modules["E"]["criteria"] if c["criterion_id"] == "concentration")
    assert conc_crit["state"] == "SCORED"
    assert conc_crit["score"] == 3.0
