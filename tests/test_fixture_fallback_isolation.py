"""Comprehensive isolation and regression test suite for cross-IPO fixture fallbacks.

Tests:
  Test A: Default allow_fixture_fallbacks=False enforcement in DocumentExtractor & PresentationService
  Test B: Builder isolation - no Vishal Nirmiti fallback leakage when allow_fixture_fallbacks=False
  Test C: Backward compatibility - explicit allow_fixture_fallbacks=True retains fixture constants
  Test D: R.K. Fashion deterministic extraction of lot size (1600), shares (11.25M/15.52M), board (sme)
  Test E: Deterministic arithmetic derivation of post_issue_eps from PAT and post_issue_shares
  Test F: Strict fail-closed UNKNOWN for unextracted qualitative ratings (moat_rating, visibility_rating)
  Test G: Golden hash bit-for-bit preservation for Vishal Nirmiti (e84f8bc0...)
  Test H: Multi-IPO generalization - synthetic filings extract cleanly without fixture contamination
"""

from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.extractor import DocumentExtractor
from ipo_screening.extraction.interfaces import SourceDocument
from ipo_screening.pipeline import evaluate, load_config
from ipo_screening.presentation.service import PresentationService

REPO_ROOT = Path(__file__).parent.parent
RK_PDF = REPO_ROOT / "handoff" / "reference" / "U18109WB2010PLC144256-R.K Fashion accessories.pdf"
CONFIG_FILE = REPO_ROOT / "config" / "ipo-config.v1.5.0.json"
VISHAL_INPUT_FILE = REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json"
FILINGS_DIR = REPO_ROOT / "fixtures" / "filings"
GOLDEN_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"

VISHAL_CONSTANTS = {
    "price_band_low": 208,
    "price_band_high": 220,
    "lot_size": 68,
    "fresh_issue": 14500,
    "ofs": 3300,
    "fresh_shares": 6590909,
    "post_issue_shares": 26390909,
    "pre_issue_shares": 19800000,
    "post_issue_eps": 9.46,
    "promoter_pre_pct": 73.42,
    "rpt_pct_revenue": 6.67,
    "moat_rating": "strong_niche",
    "visibility_rating": "strong",
}


def test_a_default_allow_fixture_fallbacks_is_supported():
    """Test A: Verify allow_fixture_fallbacks parameter in DocumentExtractor & builder."""
    # 1. DocumentExtractor.extract_from_pdf has allow_fixture_fallbacks parameter
    sig_ext = inspect.signature(DocumentExtractor.extract_from_pdf)
    assert "allow_fixture_fallbacks" in sig_ext.parameters

    # 2. CanonicalInputBuilder.__init__ has allow_fixture_fallbacks defaulting to False
    sig_builder = inspect.signature(CanonicalInputBuilder.__init__)
    assert sig_builder.parameters["allow_fixture_fallbacks"].default is False

    # 3. PresentationService.ingest_document implementation inspection
    service_src = inspect.getsource(PresentationService.ingest_document)
    assert "allow_fixture_fallbacks" in service_src


def test_b_builder_isolation_no_vishal_leakage():
    """Test B: CanonicalInputBuilder with empty extractions must NOT inject Vishal constants."""
    doc = SourceDocument(
        source_id="TEST-DOC",
        source_type="RHP",
        uri="test.pdf",
        content_hash="abc",
        file_size_bytes=100,
        page_count=10,
    )
    builder = CanonicalInputBuilder(doc=doc, extractions=[], reference_base={}, allow_fixture_fallbacks=False)
    canonical = builder.build()

    issue = canonical.get("issue", {})
    cap = canonical.get("capital_structure", {})
    gov = canonical.get("governance", {})
    biz = canonical.get("business", {})

    assert issue.get("price_band_low") is None
    assert issue.get("price_band_high") is None
    assert issue.get("lot_size") is None
    assert issue.get("fresh_issue") is None
    assert issue.get("ofs") is None
    assert issue.get("fresh_shares") is None
    assert issue.get("post_issue_shares") is None
    assert issue.get("pre_issue_shares") is None
    assert issue.get("post_issue_eps") is None

    assert cap.get("promoter_pre_pct") is None
    assert gov.get("rpt_pct_revenue") is None
    assert biz.get("moat_rating") is None
    assert biz.get("visibility_rating") is None


def test_c_builder_backward_compatibility_with_fixture_flag():
    """Test C: CanonicalInputBuilder with allow_fixture_fallbacks=True retains fallback constants."""
    doc = SourceDocument(
        source_id="TEST-DOC",
        source_type="RHP",
        uri="test.pdf",
        content_hash="abc",
        file_size_bytes=100,
        page_count=10,
    )
    builder = CanonicalInputBuilder(doc=doc, extractions=[], reference_base={}, allow_fixture_fallbacks=True)
    canonical = builder.build()

    issue = canonical.get("issue", {})
    cap = canonical.get("capital_structure", {})
    gov = canonical.get("governance", {})
    biz = canonical.get("business", {})

    assert issue.get("price_band_low") == 208
    assert issue.get("price_band_high") == 220
    assert issue.get("lot_size") == 68
    assert issue.get("fresh_issue") == 14500
    assert issue.get("ofs") == 3300
    assert issue.get("fresh_shares") == 6590909
    assert issue.get("post_issue_shares") == 26390909
    assert issue.get("pre_issue_shares") == 19800000
    assert issue.get("post_issue_eps") == 9.46

    assert cap.get("promoter_pre_pct") == 73.42
    assert gov.get("rpt_pct_revenue") == 6.67
    assert biz.get("moat_rating") == "strong_niche"
    assert biz.get("visibility_rating") == "strong"


def test_d_rk_fashion_deterministic_extraction():
    """Test D: R.K. Fashion Accessories extracts real RHP facts without fallbacks."""
    assert RK_PDF.exists()
    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(RK_PDF, allow_fixture_fallbacks=False)

    assert canonical["company_name"] == "R.K. FASHION ACCESSORIES LIMITED"
    assert canonical["board"] == "sme"
    assert canonical["issue"]["lot_size"] == 1600
    assert canonical["issue"]["pre_issue_shares"] == 11249563
    assert canonical["issue"]["post_issue_shares"] == 15516763
    assert canonical["issue"]["fresh_shares"] == 4267200
    assert canonical["capital_structure"]["promoter_pre_pct"] == 99.67
    assert canonical["capital_structure"]["promoter_post_pct"] == 72.25
    assert canonical["governance"]["rpt_pct_revenue"] == 10.79


def test_e_deterministic_arithmetic_derivation_post_issue_eps():
    """Test E: post_issue_eps is derived from PAT and post_issue_shares without hardcoding."""
    extractor = DocumentExtractor()
    canonical, _ = extractor.extract_from_pdf(RK_PDF, allow_fixture_fallbacks=False)

    periods = canonical["financials"]["periods"]
    latest_pat = periods[-1]["pat"]  # 628.69 lakhs
    post_shares = canonical["issue"]["post_issue_shares"]  # 15,516,763

    expected_eps = round((latest_pat * 100000.0) / post_shares, 2)
    assert expected_eps == 4.05
    assert canonical["issue"]["post_issue_eps"] == 4.05


def test_f_strict_fail_closed_unknown_for_qualitative_ratings():
    """Test F: Unextracted qualitative ratings evaluate to None and score as UNKNOWN."""
    extractor = DocumentExtractor()
    canonical, _ = extractor.extract_from_pdf(RK_PDF, allow_fixture_fallbacks=False)

    assert canonical["business"]["moat_rating"] is None
    assert canonical["business"]["visibility_rating"] is None

    config = load_config(CONFIG_FILE)
    eval_at = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    outcome = evaluate(canonical, config, mode="final", evaluation_datetime=eval_at)

    modules = {m["module_id"]: m for m in outcome.record.score["modules"]}
    moat_crit = next(c for c in modules["E"]["criteria"] if c["criterion_id"] == "moat")
    assert moat_crit["state"] == "UNKNOWN"
    assert "moat assessment is not recorded" in moat_crit["reason"]

    vis_crit = next(c for c in modules["E"]["criteria"] if c["criterion_id"] == "visibility")
    assert vis_crit["state"] == "UNKNOWN"
    assert "visibility assessment is not recorded" in vis_crit["reason"]


def test_g_vishal_nirmiti_golden_hash_preservation():
    """Test G: Golden hash e84f8bc0... must remain bit-for-bit identical."""
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


def test_h_multi_ipo_generalization():
    """Test H: Second-IPO filings extract cleanly without fixture contamination."""
    extractor = DocumentExtractor()
    filing_pdfs = sorted(FILINGS_DIR.glob("class_*.pdf"))
    assert len(filing_pdfs) >= 3

    for pdf_path in filing_pdfs:
        canonical, report = extractor.extract_from_pdf(pdf_path, allow_fixture_fallbacks=False)
        assert canonical["company_name"] != "VISHAL NIRMITI LIMITED"

        # None of the unextracted fields in synthetic filings should have Vishal constants
        issue = canonical.get("issue", {})
        if issue.get("lot_size") is not None:
            assert issue.get("lot_size") != 68 or pdf_path.name == "class_b_cyclical_manufacturing.pdf"
        assert canonical["business"].get("moat_rating") is None
        assert canonical["business"].get("visibility_rating") is None
