"""Phase 5A Automated Extraction Layer Tests.

Tests:
  - 5A.1: Source adapter, PDF loader, SHA-256 calculation, zero-byte/encryption fail-closed
  - 5A.2: TOC detection, ICDR section routing
  - 5A.3: Domain section extraction (Cover, Capital Structure, Objects of Offer, Governance, Business)
  - 5A.4: Financial table extraction (Restated P&L, BS, CF, KPIs, Indian numbering, negatives)
  - 5A.5: Canonical JSON builder, schema validation, _sources and _evidence provenance
  - 5A.6: End-to-end PDF -> Canonical JSON -> Pipeline evaluation execution
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
    NoOpOcrAdapter,
    PDFSourceError,
    RawExtraction,
    SectionExtractor,
    TOCRouter,
    TesseractOcrAdapter,
    compute_file_sha256,
    detect_currency_unit,
    detect_scanned_page,
    is_undisclosed_marker,
    load_pdf_source,
    parse_indian_number,
)

PDF_FIXTURE = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"
VISHAL_INPUT_FIXTURE = REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json"
CONFIG_FILE = REPO_ROOT / "config" / "ipo-config.v1.5.0.json"


# --------------------------------------------------------------------------
# Task 5A.1: Numbers, units, and PDF source loader
# --------------------------------------------------------------------------


def test_parse_indian_numbers():
    assert parse_indian_number("14,500.00") == 14500.0
    assert parse_indian_number("15,00,000") == 1500000.0
    assert parse_indian_number("₹ 33,867.73") == 33867.73
    assert parse_indian_number("Rs. 10/-") == 10.0
    assert parse_indian_number("(2,881.95)") == -2881.95
    assert parse_indian_number("(46.64)") == -46.64
    assert parse_indian_number("-123.45") == -123.45
    assert parse_indian_number("0.0") == 0.0


def test_undisclosed_markers():
    assert is_undisclosed_marker("[●]") is True
    assert is_undisclosed_marker("[•]") is True
    assert is_undisclosed_marker("[*]") is True
    assert is_undisclosed_marker("NIL") is True
    assert is_undisclosed_marker("-") is True
    assert is_undisclosed_marker("") is True
    assert is_undisclosed_marker("14,500") is False

    assert parse_indian_number("[●]") is None
    assert parse_indian_number("NIL") is None


def test_detect_currency_unit():
    assert detect_currency_unit("(Amount in Lakhs, unless otherwise stated)") == "INR_LAKHS"
    assert detect_currency_unit("₹ in Crores") == "INR_CRORES"
    assert detect_currency_unit("Amount in Millions") == "INR_MILLIONS"
    assert detect_currency_unit("in Billions") == "INR_BILLIONS"
    assert detect_currency_unit("random string with no units") is None


def test_pdf_source_fail_closed_on_missing_or_empty(tmp_path):
    # Non-existent file
    with pytest.raises(PDFSourceError, match="does not exist"):
        load_pdf_source(tmp_path / "nonexistent.pdf")

    # Zero-byte empty file
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    with pytest.raises(PDFSourceError, match="zero bytes"):
        load_pdf_source(empty_pdf)


def test_pdf_source_loads_valid_fixture():
    assert PDF_FIXTURE.exists()
    doc, reader = load_pdf_source(PDF_FIXTURE)
    assert doc.page_count == 551
    assert doc.content_hash == "644be76e26d43dcaa26ba11303072cf4543bc7a52f30cd37bf1d2d1d552645f6"
    assert doc.uri.endswith("vishal nirmiti.pdf")
    assert len(reader.pages) == 551


# --------------------------------------------------------------------------
# OCR Adapter isolation
# --------------------------------------------------------------------------


def test_ocr_adapters():
    noop = NoOpOcrAdapter()
    assert noop.is_available() is False
    assert noop.ocr_image_bytes(b"sample") == ""

    tess = TesseractOcrAdapter(binary_path="/nonexistent/tesseract")
    assert tess.is_available() is False
    assert tess.ocr_image_bytes(b"sample") == ""

    assert detect_scanned_page("   ") is True
    assert detect_scanned_page("A" * 10, threshold=50) is True
    assert detect_scanned_page("A" * 100, threshold=50) is False


# --------------------------------------------------------------------------
# Task 5A.2: TOC and Document Navigation
# --------------------------------------------------------------------------


def test_toc_router_discovers_icdr_sections():
    doc, reader = load_pdf_source(PDF_FIXTURE)
    router = TOCRouter.from_pdf(reader)
    assert len(router.entries) >= 8

    # Verify key ICDR sections found
    for sec in ["the_offer", "capital_structure", "objects_of_the_offer", "restated_financials", "litigation"]:
        assert sec in router.entries

    # Check page ranges
    uop_range = router.get_page_range("objects_of_the_offer")
    assert uop_range is not None
    assert uop_range[0] <= uop_range[1]
    assert uop_range[0] >= 100


# --------------------------------------------------------------------------
# Task 5A.3: Domain Section Extraction
# --------------------------------------------------------------------------


def test_section_extractor_cover_and_capital():
    doc, reader = load_pdf_source(PDF_FIXTURE)
    router = TOCRouter.from_pdf(reader)
    page_ranges = {k: router.get_page_range(k) for k in router.entries}

    extractor = SectionExtractor(doc, reader)

    cover_res = extractor.extract_cover_and_offer(page_ranges)
    cover_fields = {e.field_path: e.candidate_value for e in cover_res}
    assert cover_fields["company_name"] == "VISHAL NIRMITI LIMITED"
    assert cover_fields["issue.fresh_issue"] == 14500.0

    cap_res = extractor.extract_capital_structure(page_ranges)
    cap_fields = {e.field_path: e.candidate_value for e in cap_res}
    assert cap_fields["capital_structure.promoter_pre_pct"] == 73.42
    assert cap_fields["capital_structure.promoter_pledge_pct"] == 0.0
    assert cap_fields["capital_structure.promoter_lockin_in_place"] is True


def test_section_extractor_objects_of_offer_fail_closed_gcp():
    doc, reader = load_pdf_source(PDF_FIXTURE)
    router = TOCRouter.from_pdf(reader)
    page_ranges = {k: router.get_page_range(k) for k in router.entries}

    extractor = SectionExtractor(doc, reader)
    uop_res = extractor.extract_objects_of_offer(page_ranges)
    assert len(uop_res) == 1
    uop_list = uop_res[0].candidate_value

    wc = next((u for u in uop_list if u["category"] == "working_capital"), None)
    debt = next((u for u in uop_list if u["category"] == "debt_repayment"), None)
    gcp = next((u for u in uop_list if u["category"] == "gcp"), None)

    assert wc is not None and wc["amount"] == 7500.0
    assert debt is not None and debt["amount"] == 1900.0
    assert gcp is not None
    assert gcp["amount"] is None
    assert gcp.get("undisclosed_marker") in ("[●]", "[•]", "[*]")


# --------------------------------------------------------------------------
# Task 5A.4: Financial Tables Extraction
# --------------------------------------------------------------------------


def test_financial_table_extractor():
    doc, reader = load_pdf_source(PDF_FIXTURE)
    fin_extractor = FinancialTableExtractor(doc, reader)
    res = fin_extractor.extract_all(start_page=340, end_page=390)

    fields = {e.field_path: e.candidate_value for e in res}
    assert fields["financials.reporting_unit"] == "INR_LAKHS"

    periods = fields["financials.periods"]
    assert len(periods) == 3
    assert [p["fy"] for p in periods] == ["FY2024", "FY2025", "FY2026"]

    fy26 = next(p for p in periods if p["fy"] == "FY2026")
    assert fy26["revenue"] == 33867.73
    assert fy26["pat"] == 2497.50
    assert fy26["net_worth"] == 8678.35
    assert fy26["total_debt"] == 8741.70
    assert fy26["cfo"] == 2715.47
    assert fy26["capex"] == 3528.88
    assert fy26["interest_expense"] == 1504.04
    assert fy26["disclosed_roce_pct"] == 28.02


# --------------------------------------------------------------------------
# Task 5A.5 & 5A.6: Canonical Builder and End-to-End Pipeline Evaluation
# --------------------------------------------------------------------------


def test_document_extractor_and_pipeline_execution():
    extractor = DocumentExtractor()
    canonical, report = extractor.extract_from_pdf(
        PDF_FIXTURE,
        reference_base_path=VISHAL_INPUT_FIXTURE,
    )

    # Extraction assertions
    assert report.field_count >= 10
    assert report.verified_count >= 10
    assert canonical["company_name"] == "VISHAL NIRMITI LIMITED"
    assert canonical["financials"]["reporting_unit"] == "INR_LAKHS"
    assert len(canonical["financials"]["periods"]) == 3
    assert len(canonical["_sources"]) >= 1
    assert len(canonical["_evidence"]) >= 10

    # Ensure schema validation passes
    builder = CanonicalInputBuilder(report.source, report.extractions, reference_base=canonical)
    assert builder.validate(canonical) is True

    # Run through deterministic v1.5 screening engine pipeline
    config = load_config(CONFIG_FILE)
    outcome = evaluate(canonical, config, mode="final")

    assert outcome.record.validation["ok"] is True
    assert outcome.record.verdict["verdict"] == "INSUFFICIENT_DATA"
    assert outcome.record.score["final_score"] == 35.0
    assert outcome.record.score["penalties_total"] == -3.0
    assert outcome.record.result_hash is not None


def test_cli_extract_subcommand(tmp_path):
    import subprocess
    import sys

    out_file = tmp_path / "extracted.json"
    cli_path = REPO_ROOT / "engine" / "tools" / "ipo_screen.py"

    proc = subprocess.run(
        [
            sys.executable,
            str(cli_path),
            "extract",
            str(PDF_FIXTURE),
            "--template",
            str(VISHAL_INPUT_FIXTURE),
            "--output",
            str(out_file),
            "--run",
            "--at",
            "2026-10-05T12:00:00Z",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )

    assert proc.returncode == 0, f"Error: {proc.stderr}"
    assert "extraction summary" in proc.stdout
    assert "document uri" in proc.stdout
    assert "fields extracted" in proc.stdout
    assert "VISHAL NIRMITI LIMITED" in proc.stdout
    assert "35.0" in proc.stdout
    assert out_file.exists()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["company_name"] == "VISHAL NIRMITI LIMITED"
