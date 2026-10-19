"""Financial-statement ingestion: fiscal column selection and row mapping
(2026-10-19 diagnostic, Jio Platforms evaluation).

Verified defect (root cause of the reported Revenue CAGR of -48.36%):
SEBI RHP summary/Ind AS statement tables carry a three-month (interim)
column block BEFORE the fiscal-year block, newest-first, often with a
leading note number::

    Revenue from Operations 26  391,729  350,323  1,468,853  1,282,184  1,095,581
    (three months Jun-26) (three months Jun-25) (Fiscal 2026) (Fiscal 2025) (Fiscal 2024)

The extractor selected the LEFTMOST n columns, silently mixing interim
and fiscal columns into the fiscal periods (FY2024 <- Fiscal 2026;
FY2025 <- Q1 Jun-2025; FY2026 <- Q1 Jun-2026). The 2Y revenue CAGR then
collapsed to -48.36% against the true fiscal +15.79% (the figure the RHP
itself states on page 128).

These tests pin the corrected mapping and the related verified row-label
and unit fixes, on the exact observed document (the real Jio RHP) and on
synthetic statement text. The Vishal reference extraction
(test_extraction.py) must remain byte-identical -- its 3/4-numeric rows
select identically under the corrected rule.
"""

from __future__ import annotations

import re

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction.financial_tables import FinancialTableExtractor
from ipo_screening.extraction.numbers import detect_currency_unit

JIO_PDF = REPO_ROOT / "evidence" / "non-authoritative" / "jio" / "U72900GJ2019PLC110816_JIO.pdf"


class _StubReader:
    pages = []


def _extractor():
    # The table-parsing helpers do not touch doc/reader content.
    return FinancialTableExtractor(None, _StubReader(), text_cache={})


PL_SPECS = [
    ("revenue", [r"revenue from operations"]),
    ("pat", [r"profit after tax"]),
    ("depreciation", [r"depreciation and amorti[sz]ation"]),
    ("finance_costs", [r"finance costs"]),
    ("total_expenses", [r"total expenses\b"]),
]
BS_SPECS = [
    ("net_worth", [r"total equity(?! and liabilit)", r"total equity \(d\)"]),
    ("cash_and_equivalents", [r"cash and cash equivalents"]),
]
CF_SPECS = [
    ("cfo", [
        r"net cash provided by/\(used in\) operating activities",
        r"net cash from operating activities",
        r"net cash flow from operating activities",
    ]),
]


# ---------------------------------------------------------------------------
# Synthetic statement text -- the exact observed column/label shapes
# ---------------------------------------------------------------------------

SUMMARY_PL = """
Summary of restated consolidated statement of profit and loss
(in ₹ million, unless otherwise specified)
Particulars Three months periods ended Fiscal
June 30, 2026 June 30, 2025 2026 2025 2024
Income
Revenue from Operations 26  391,729  350,323  1,468,853  1,282,184  1,095,581
Expenses
Finance Costs 30  29,799  21,048  86,534  49,051  40,476
Depreciation and Amortisation Expense  74,575  64,789  272,489  241,376  221,031
Total Expenses  297,708  261,350  1,094,060  942,057  813,674
Profit After Tax  77,641  71,104  300,527  261,203  214,340
"""

SUMMARY_BS = """
Summary of restated consolidated statement of assets and liabilities
(in ₹ million)
Particulars As at June 30, 2026 June 30, 2025 March 31, 2026 March 31, 2025 March 31, 2024
Cash and Cash Equivalents 190,268  97,089  165,570  80,115  24,889
Equity Share capital 89,390  89,390  89,390  89,390  89,390
Other Equity 3,348,560  3,031,281  3,270,379  2,961,084  2,693,474
Non-Controlling Interest 10,969  11,068  10,993  11,338  11,353
Borrowings 491,201  489,960  514,548  452,289  431,825
Total Non-Current Liabilities  2,112,570  2,072,318  2,113,371  1,969,515  1,889,405
Borrowings 122,521  238,232  193,262  278,314  111,664
Total Equity and Liabilities 6,229,053  5,961,770  6,155,940  5,812,338  5,395,804
"""

SUMMARY_CF = """
Net Cash Flow from Operating Activities (A)  234,459  209,065  775,563  681,557  576,616
"""


def test_summary_table_columns_map_to_fiscal_periods_not_interim():
    """The exact observed defect: interim columns must never land in the
    fiscal periods. Values are the real Jio RHP summary figures."""
    fe = _extractor()
    pl = fe._parse_table_lines(SUMMARY_PL, PL_SPECS, 3)
    assert pl["revenue"] == [1468853.0, 1282184.0, 1095581.0]
    assert pl["pat"] == [300527.0, 261203.0, 214340.0]
    assert pl["finance_costs"] == [86534.0, 49051.0, 40476.0]
    assert pl["total_expenses"] == [1094060.0, 942057.0, 813674.0]
    bs = fe._parse_table_lines(SUMMARY_BS, BS_SPECS, 3)
    assert bs["cash_and_equivalents"] == [165570.0, 80115.0, 24889.0]
    cf = fe._parse_table_lines(SUMMARY_CF, CF_SPECS, 3)
    assert cf["cfo"] == [775563.0, 681557.0, 576616.0]


def test_note_number_columns_are_excluded():
    """A leading note number is never read as a period value."""
    fe = _extractor()
    pl = fe._parse_table_lines(SUMMARY_PL, [("revenue", [r"revenue from operations"])], 3)
    assert 26.0 not in pl["revenue"]
    assert 30.0 not in fe._parse_table_lines(SUMMARY_PL, [("finance_costs", [r"finance costs"])], 3)["finance_costs"]


def test_total_equity_and_liabilities_is_never_read_as_net_worth():
    """Verified mapping defect: `total equity` matched the grand-total row
    (Total Equity and Liabilities == Total Assets), silently feeding total
    assets in as net worth. The grand total must not match; a real Total
    Equity row must."""
    fe = _extractor()
    bs = fe._parse_table_lines(SUMMARY_BS, BS_SPECS, 3)
    assert "net_worth" not in bs  # governed unknown, never a wrong total
    ok = fe._parse_table_lines(
        "Total Equity (D)  3,448,919  3,131,739  3,370,762  3,061,812  2,794,217",
        BS_SPECS, 3)
    assert ok["net_worth"] == [3370762.0, 3061812.0, 2794217.0]


def test_plain_borrowings_rows_sum_to_total_debt_fiscally():
    """Non-current and current 'Borrowings' rows (no dash prefix) are both
    captured; the caller sums them into total_debt."""
    fe = _extractor()
    rows = fe._extract_all_borrowings(SUMMARY_BS, 3)
    assert rows == [[514548.0, 452289.0, 431825.0], [193262.0, 278314.0, 111664.0]]
    assert rows[0][0] + rows[1][0] == 707810.0  # FY2026 total borrowings


def test_depreciation_amortisation_spelling_both_recognised():
    fe = _extractor()
    pl = fe._parse_table_lines(SUMMARY_PL, [("depreciation", [r"depreciation and amorti[sz]ation"])], 3)
    assert pl["depreciation"] == [272489.0, 241376.0, 221031.0]
    # British spelling used in the Vishal statement must keep working too.
    pl2 = fe._parse_table_lines(
        "Depreciation and amortization expenses 36  776.53  746.90  916.79",
        [("depreciation", [r"depreciation and amorti[sz]ation"])], 3)
    assert pl2["depreciation"] == [776.53, 746.9, 916.79]


def test_kpi_roce_wrapped_row_and_average_label_are_parsed():
    """The 'Return on Average Capital Employed' KPI row wraps across two
    lines and carries interim columns first; the fiscal values must be
    selected (they override the computed ROCE downstream)."""
    fe = _extractor()
    kpi_text = (
        "KPIs Unit\n"
        "As at and for the three months ended June 30, 2026 June 30, 2025 2026 2025 2024\n"
        "PAT Margin(16) % 19.82% 20.30% 20.46% 20.36% 19.55%\n"
        "Return on Average Capital \n"
        "Employed(18) % 2.56% 3.01% 10.76% 12.50% 12.83%\n"
    )
    vals = fe._parse_kpi_line(kpi_text, r"return on (?:average )?capital\s+employed", 3)
    assert vals == [10.76, 12.5, 12.83]


def test_kpi_single_line_roce_unchanged():
    """The Vishal shape (single line, exactly n decimals) is untouched."""
    fe = _extractor()
    vals = fe._parse_kpi_line(
        "9.  Return on Capital Employed (%)(9) 28.02 30.32 14.60",
        r"return on (?:average )?capital\s+employed", 3)
    assert vals == [28.02, 30.32, 14.6]


def test_currency_unit_detects_in_rupee_million():
    """Verified unit defect: the common header form '(in ₹ million)' was
    not recognised and fell through to the INR_LAKHS default."""
    rupee = chr(0x20B9)
    assert detect_currency_unit(f"(in {rupee} million, unless otherwise specified)") == "INR_MILLIONS"
    assert detect_currency_unit(f"(All amounts are Rs. in millions)") == "INR_MILLIONS"
    # Existing forms stay detected (Vishal: Amount in Lakhs).
    assert detect_currency_unit("(Amount in Lakhs, unless otherwise stated)") == "INR_LAKHS"
    assert detect_currency_unit(f"{rupee} in Crores") == "INR_CRORES"


# ---------------------------------------------------------------------------
# The exact observed document -- end-to-end extraction pins
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_jio_real_filing_periods_are_fiscal_and_cagr_is_the_fiscal_figure():
    from ipo_screening.extraction import DocumentExtractor

    doc, _ = DocumentExtractor().extract_from_pdf(
        pdf_path=JIO_PDF, allow_fixture_fallbacks=False
    )
    fin = doc["financials"]
    assert fin["reporting_unit"] == "INR_MILLIONS"
    periods = fin["periods"]
    rev = [p["revenue"] for p in periods]
    assert rev == [1095581.0, 1282184.0, 1468853.0]
    cagr = ((rev[-1] / rev[0]) ** 0.5 - 1) * 100
    # The RHP itself states 15.79% (page 128); the pre-fix extraction
    # produced -48.36% from mixed interim/fiscal columns.
    assert cagr == pytest.approx(15.79, abs=0.05)
    assert periods[-1]["cfo"] == 775563.0
    assert periods[-1]["disclosed_roce_pct"] == 10.76
    assert periods[-1]["total_debt"] == 707810.0
    # Net worth is not a stated row in these statements: it must stay
    # absent (governed unknown), never the Total Assets grand total.
    assert all(p.get("net_worth") is None for p in periods)
