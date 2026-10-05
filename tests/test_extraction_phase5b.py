"""Phase 5B Real-World Filing Extraction Validation and Hardening Tests.

Validates extraction across representative real-world filing classes:
  - Class A: Financial Institution / Lender (Apex Housing Finance Limited)
  - Class B: Cyclical / Manufacturing (Zenith Heavy Forgings Limited - 5 Full FYs)
  - Class C: EPC / Infrastructure / Real Estate (Garuda Infra Projects Limited)
  - Class D: Loss-Making Growth Tech (QuickDeliver Network Limited)
  - Class E: Modern Complex Filing (Nexus Retail Brands Limited)
  - Anchor Real-World: Vishal Nirmiti Limited (551-page RHP)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from ipo_screening import evaluate, load_config
from ipo_screening.extraction import (
    CanonicalInputBuilder,
    DocumentExtractor,
    FinancialTableExtractor,
    RawExtraction,
    SectionExtractor,
    is_undisclosed_marker,
    load_pdf_source,
    parse_indian_number,
)

FILINGS_DIR = REPO_ROOT / "fixtures" / "filings"
CONFIG_FILE = REPO_ROOT / "config" / "ipo-config.v1.5.0.json"
VISHAL_PDF = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"
VISHAL_FIXTURE = REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json"


# --------------------------------------------------------------------------
# Class A: Financial Institution / Lender
# --------------------------------------------------------------------------


def test_fixture_class_a_financial_lender():
    pdf_path = FILINGS_DIR / "class_a_financial_lender.pdf"
    assert pdf_path.exists()

    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(pdf_path)

    # 1. Identity & Routing
    assert canonical["company_name"] == "APEX HOUSING FINANCE LIMITED"
    assert canonical["sector_profile"] == "financial"
    assert canonical["icdr_route"] == "6(1)"

    # 2. Financial Metrics
    fin = canonical["financials"]
    assert fin["reporting_unit"] == "INR_LAKHS"
    assert len(fin["periods"]) == 3

    fy26 = next(p for p in fin["periods"] if p["fy"] == "FY2026")
    assert fy26["revenue"] == 42500.0
    assert fy26["pat"] == 6800.0
    assert fy26["net_worth"] == 52000.0
    assert fy26["total_debt"] == 280000.0
    assert fy26["crar_pct"] == 20.10
    assert fy26["gnpa_pct"] == 2.40
    assert fy26["nim_pct"] == 3.70
    assert fy26["cost_to_income_pct"] == 46.50

    # 3. Capital Structure & Objects
    assert canonical["capital_structure"]["promoter_pre_pct"] == 68.50
    assert canonical["capital_structure"]["promoter_pledge_pct"] == 0.0

    uop = canonical["use_of_proceeds"]
    gcp = next(u for u in uop if u["category"] == "gcp")
    assert gcp["amount"] is None
    assert gcp.get("undisclosed_marker") in ("[●]", "[•]", "[*]")

    # 4. Engine evaluation with financial overlay
    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final")
    assert outcome.record.validation["ok"] is True
    assert outcome.record.plan["sector_overlay"] == "financial"
    assert outcome.record.result_hash is not None


# --------------------------------------------------------------------------
# Class B: Cyclical / Manufacturing (5 Full FYs)
# --------------------------------------------------------------------------


def test_fixture_class_b_cyclical_manufacturing_5fy():
    pdf_path = FILINGS_DIR / "class_b_cyclical_manufacturing.pdf"
    assert pdf_path.exists()

    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(pdf_path)

    assert canonical["company_name"] == "ZENITH HEAVY FORGINGS LIMITED"
    assert canonical["sector_profile"] == "cyclical"

    periods = canonical["financials"]["periods"]
    assert len(periods) == 5
    assert [p["fy"] for p in periods] == ["FY2022", "FY2023", "FY2024", "FY2025", "FY2026"]

    fy22 = next(p for p in periods if p["fy"] == "FY2022")
    fy26 = next(p for p in periods if p["fy"] == "FY2026")
    assert fy22["revenue"] == 22000.0
    assert fy22["pat"] == 1350.0
    assert fy26["revenue"] == 48000.0
    assert fy26["pat"] == 4800.0
    assert fy26["total_debt"] == 11600.0  # 6200 + 5400

    # Engine evaluation with cyclical overlay
    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final")
    assert outcome.record.validation["ok"] is True
    assert outcome.record.plan["sector_overlay"] == "cyclical"
    assert outcome.record.score["final_score"] == 41.0


# --------------------------------------------------------------------------
# Class C: EPC / Infrastructure / Real Estate
# --------------------------------------------------------------------------


def test_fixture_class_c_epc_infrastructure():
    pdf_path = FILINGS_DIR / "class_c_epc_infrastructure.pdf"
    assert pdf_path.exists()

    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(pdf_path)

    assert canonical["company_name"] == "GARUDA INFRA PROJECTS LIMITED"
    assert canonical["sector_profile"] == "epc_real_estate"
    assert canonical["business"].get("order_book") == 145000.0

    # Engine evaluation with EPC overlay
    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final")
    assert outcome.record.validation["ok"] is True
    assert outcome.record.plan["sector_overlay"] == "epc_real_estate"
    assert outcome.record.score["final_score"] == 41.0


# --------------------------------------------------------------------------
# Class D: Loss-Making Growth Tech
# --------------------------------------------------------------------------


def test_fixture_class_d_loss_making_tech():
    pdf_path = FILINGS_DIR / "class_d_loss_making_tech.pdf"
    assert pdf_path.exists()

    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(pdf_path)

    assert canonical["company_name"] == "QUICKDELIVER NETWORK LIMITED"
    periods = canonical["financials"]["periods"]
    assert len(periods) == 3

    # Negative PAT correctly preserved
    fy26 = next(p for p in periods if p["fy"] == "FY2026")
    assert fy26["pat"] == -2300.0
    assert fy26["cfo"] == -1650.0

    # Auto profile detects loss_making or standard
    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final")
    assert outcome.record.validation["ok"] is True
    assert outcome.record.plan["auto_profile_applied"] == "loss_making"


# --------------------------------------------------------------------------
# Class E: Modern Complex Filing
# --------------------------------------------------------------------------


def test_fixture_class_e_modern_complex_rhp():
    pdf_path = FILINGS_DIR / "class_e_modern_complex_rhp.pdf"
    assert pdf_path.exists()

    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(pdf_path)

    assert canonical["company_name"] == "NEXUS RETAIL BRANDS LIMITED"
    assert canonical["sector_profile"] == "standard"
    assert canonical["financials"]["periods"][2]["revenue"] == 38400.0
    assert canonical["financials"]["periods"][2]["pat"] == 3400.0

    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final")
    assert outcome.record.validation["ok"] is True
    assert outcome.record.score["final_score"] == 43.0


# --------------------------------------------------------------------------
# Anchor Real-World RHP (Vishal Nirmiti - 551 Pages)
# --------------------------------------------------------------------------


def test_anchor_real_world_rhp_vishal_nirmiti():
    assert VISHAL_PDF.exists()
    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(
        VISHAL_PDF, reference_base_path=VISHAL_FIXTURE
    )

    assert canonical["company_name"] == "VISHAL NIRMITI LIMITED"
    assert canonical["financials"]["reporting_unit"] == "INR_LAKHS"
    assert len(canonical["financials"]["periods"]) == 3

    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final")

    assert outcome.record.validation["ok"] is True
    assert outcome.record.verdict["verdict"] == "INSUFFICIENT_DATA"
    assert outcome.record.score["final_score"] == 35.0
    assert outcome.record.score["penalties_total"] == -3.0


# --------------------------------------------------------------------------
# Evidence Provenance and Fail-Closed Validation
# --------------------------------------------------------------------------


def test_evidence_provenance_and_auditability():
    pdf_path = FILINGS_DIR / "class_b_cyclical_manufacturing.pdf"
    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(pdf_path)

    assert "_evidence" in canonical
    evidence = canonical["_evidence"]
    assert len(evidence) >= 10

    # Ensure crucial financial and governance fields carry traceable provenance
    for field in [
        "company_name",
        "capital_structure.promoter_pre_pct",
        "financials.periods",
        "governance.litigation_bucket",
    ]:
        assert field in evidence, f"Field {field} missing in extraction evidence log"
        rec = evidence[field]
        assert rec["locator"] is not None
        assert rec["extraction_method"] == "DETERMINISTIC_PDF"
        assert rec["extraction_confidence"] > 0.85


def test_fail_closed_undisclosed_markers():
    assert is_undisclosed_marker("[●]") is True
    assert is_undisclosed_marker("[•]") is True
    assert is_undisclosed_marker("[*]") is True
    assert is_undisclosed_marker("[   ]") is True
    assert is_undisclosed_marker("NIL") is True
    assert is_undisclosed_marker("N.A.") is True
    assert is_undisclosed_marker("-") is True
    assert is_undisclosed_marker("12,345.67") is False


def test_parse_indian_number_edge_cases():
    assert parse_indian_number("1,23,456.78") == 123456.78
    assert parse_indian_number("(1,500.00)") == -1500.00
    assert parse_indian_number("—") is None
    assert parse_indian_number("[●]") is None
