"""Extraction gaps found by scoring the Paras RHP end to end (2026-10-24).

The operator's evaluation of Paras Healthcare (RHP sha256 ``E0A3187F…570E74``)
returned ``Final Score 8.0 / Available 29 / Unknown 71``.  Reproducing it on
the retained filing showed that four of the unknowns were **reading defects in
the shared extractor**, not absent data in the document:

1. **The reporting unit was not recognised.**  Every restated statement is
   captioned ``(All amounts are in INR million, unless otherwise stated)`` and
   the KPI tables say ``Amount (₹ million)``.  ``detect_currency_unit`` only
   accepted ``in millions`` / ``₹ in millions`` (the latter requiring a word
   boundary before ``₹``, which cannot exist after ``(``), so the filing was
   booked as ``INR_LAKHS`` and every monetary value taken from the statements
   was **ten times too small** relative to the issue amounts, which are
   normalised from ``INR_MILLIONS`` on a different path.

2. **PAT was never read.**  The statement labels it
   ``Profit/(loss) for the period/year (A)``; the accepted forms were
   ``profit/(loss) for the year`` and ``profit after tax``.  With PAT unknown,
   margin trend, cash-flow quality, P/E, PEG and the ``profit_declining``
   knockout leaf are all unknown.

3. **CFO was never read.**  The cash-flow statement says
   ``Net cash generated from operating activities (A)``; only ``provided by``
   and ``from``/``flow from`` were accepted.

4. **Contingent liabilities were never read.**  The note is captioned
   ``32. Commitments and contingencies`` (the note rule expects "contingent
   liabilities and commitments") and states the exposure as prose.  The
   document nevertheless prints a ``SUMMARY OF CONTINGENT LIABILITIES`` table
   whose Total row is ``3,905.01`` as at 31 March 2026 — 98.88% of the FY2026
   net worth of ``3,949.41``, *exactly* the ratio the RHP states in its own
   risk factor ("89.55% of our net worth" as at 30 June 2026; 98.88% for
   FY2026).  Leaving it unread left knockout **K5 blind to a disclosed
   knockout**.

This module pins the reading rules with synthetic pages (fast, issuer-neutral)
and the real filing's numbers in ``test_paras_evidence_regression.py``, where
the document is already extracted once for the module.

What is deliberately *not* claimed here: none of these corrections resolves the
locked issue terms, changes a threshold, changes a weight, or changes what a
criterion means.  A value that is not printed still stays ``None``.
"""

from __future__ import annotations

import pytest

from ipo_screening.extraction.financial_tables import FinancialTableExtractor
from ipo_screening.extraction.numbers import detect_currency_unit


# ---------------------------------------------------------------------------
# 1. Reporting-unit headers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "header",
    [
        "(All amounts are in INR million, unless otherwise stated)",
        "Amount (₹ million)",
        "(₹ million)",
        "(INR million)",
        "All amounts are stated in INR millions",
        "Figures in ₹ million",
    ],
)
def test_million_headers_are_recognised(header):
    assert detect_currency_unit(header) == "INR_MILLIONS"


@pytest.mark.parametrize(
    "header,expected",
    [
        ("(₹ in lakhs)", "INR_LAKHS"),
        ("(All amounts are Rs. in lakhs unless otherwise stated)", "INR_LAKHS"),
        ("Rs. in Crores", "INR_CRORES"),
        ("(All amounts are in INR crore, unless otherwise stated)", "INR_CRORES"),
        ("Amount (₹ thousands)", "INR_THOUSANDS"),
        ("Amount (₹ billion)", "INR_BILLIONS"),
    ],
)
def test_every_scale_keeps_its_own_unit(header, expected):
    assert detect_currency_unit(header) == expected


def test_a_body_sentence_is_not_a_unit_header():
    """A figure mentioned in prose must not declare the page's unit."""
    assert detect_currency_unit("Our revenue was ₹ 500 million in Fiscal 2026.") is None
    assert detect_currency_unit("") is None
    assert detect_currency_unit(None) is None


# ---------------------------------------------------------------------------
# 2 and 3. PAT and CFO row labels
# ---------------------------------------------------------------------------


def _extractor(pages):
    extractor = FinancialTableExtractor.__new__(FinancialTableExtractor)
    extractor.page_count = max(pages) if pages else 1
    extractor.extract_page_text = lambda p: pages.get(p, "")
    return extractor


PINCOMING = """Restated Consolidated Statement of Profit and Loss
(All amounts are in INR million, unless otherwise stated)
Income
Revenue from operations 22      4,702.78   3,683.87   16,059.52   12,940.63   11,290.39
Total expenses                  4,306.26   3,683.89   15,527.51   13,642.43   12,334.51
Profit/(loss) before tax          481.20      58.43      760.33     (500.36)      66.30
Profit/(loss) for the period/year (A)  496.82  (10.24)   438.34     (579.83)    (153.31)
"""

CASHFLOW = """Restated Consolidated Statement of Cash Flows
(All amounts are in INR million, unless otherwise stated)
Cash generated from operations  430.28   509.54   2,173.35   960.04   1,029.90
Net cash generated from operating activities (A)  643.38  379.15  1,635.12  861.91  924.77
"""


def test_pat_is_read_from_the_period_slash_year_label():
    items = _extractor({1: PINCOMING})._parse_table_lines(
        PINCOMING,
        [
            ("revenue", [r"revenue from operations"]),
            (
                "pat",
                [
                    r"profit after tax",
                    r"profit\s*/\s*\(loss\)\s*for\s*the\s*period\s*/\s*year",
                    r"profit\s*/\s*\(loss\)\s*for\s*the\s*(?:year|period)\b",
                ],
            ),
        ],
        3,
    )
    # The three-month columns precede the fiscal block; the fiscal block is
    # the rightmost three cells, newest first (the caller re-orders).
    assert items["revenue"] == [16059.52, 12940.63, 11290.39]
    assert items["pat"] == [438.34, -579.83, -153.31]


def test_cfo_is_read_from_net_cash_generated_from_operating_activities():
    items = _extractor({1: CASHFLOW})._parse_table_lines(
        CASHFLOW,
        [
            (
                "cfo",
                [
                    r"net cash provided by/\(used in\) operating activities",
                    r"net cash (?:generated|provided|arising) (?:from|by|out of) operating activities",
                ],
            )
        ],
        3,
    )
    assert items["cfo"] == [1635.12, 861.91, 924.77]


# ---------------------------------------------------------------------------
# 4. The "Summary of Contingent Liabilities" table
# ---------------------------------------------------------------------------

PARAS_SUMMARY_DAY_FIRST = """SUMMARY OF CONTINGENT LIABILITIES
Except as disclosed below, there are no contingent liabilities of our Company as at June 30, 2026, June 30, 2025, March 31, 2026, March 31, 2025 and March 31, 2024 derived from the Restated Consolidated Financial Information:
(₹ in million)
S.
No. Particulars
As at 30
June, 2026
As at 30
June, 2025
As at
31 March,
2026
As at
31 March,
2025
As at
31 March,
2024
1
Corporate guarantees given on behalf of Subsidiaries
3,448.01 2,877.68 3,368.21 3,297.93 2,746.02
2
Claims against the Group not acknowledged as debts
536.41 525.47 536.80 497.97 140.21
Total 3,984.42 3,403.15 3,905.01 3,795.90 2,886.23
"""

PARAS_SUMMARY_MONTH_FIRST = PARAS_SUMMARY_DAY_FIRST.replace(
    "As at\n31 March,\n2026\nAs at\n31 March,\n2025\nAs at\n31 March,\n2024",
    "As at\nMarch 31,\n2026\nAs at\nMarch 31,\n2025\nAs at\nMarch 31,\n2024",
)


def test_summary_total_is_read_for_the_latest_march_column():
    page, amount, unquantified, quote = _extractor({91: PARAS_SUMMARY_DAY_FIRST})._read_contingent_liability_summary(
        [(1, 91)]
    )
    assert page == 91
    # FY2026 (31 March 2026) — not the June-2026 interim 3,984.42, which would
    # be divided by a full-year net worth.
    assert amount == 3905.01
    assert unquantified is None
    assert "3,905.01" in quote and "31 March 2026" in quote


def test_summary_header_may_be_written_month_first():
    """``March 31, 2026`` is the same column as ``31 March 2026``."""
    assert _extractor({1: PARAS_SUMMARY_MONTH_FIRST})._read_contingent_liability_summary(
        [(1, 1)]
    )[1] == 3905.01


def test_summary_dates_in_the_lead_in_sentence_are_not_columns():
    """The prose repeats every date; only the header fragments count."""
    _, amount, _, _ = _extractor({1: PARAS_SUMMARY_DAY_FIRST})._read_contingent_liability_summary(
        [(1, 1)]
    )
    assert amount == 3905.01


def test_summary_without_a_march_column_fails_closed():
    text = PARAS_SUMMARY_DAY_FIRST.replace("31 March,\n2026", "30 June,\n2026").replace(
        "31 March,\n2025", "30 June,\n2025"
    ).replace("31 March,\n2024", "30 June,\n2024")
    assert _extractor({1: text})._read_contingent_liability_summary([(1, 1)])[1] is None


def test_summary_with_two_totals_fails_closed():
    text = PARAS_SUMMARY_DAY_FIRST + "Total 1.00 1.00 1.00 1.00 1.00\n"
    assert _extractor({1: text})._read_contingent_liability_summary([(1, 1)])[1] is None


def test_summary_total_that_does_not_align_fails_closed():
    text = PARAS_SUMMARY_DAY_FIRST.replace(
        "Total 3,984.42 3,403.15 3,905.01 3,795.90 2,886.23",
        "Total 3,984.42 3,403.15 3,905.01",
    )
    result = _extractor({1: text})._read_contingent_liability_summary([(1, 1)])
    # A three-cell total against five dated columns is ambiguous: the reader
    # must not guess which three.
    assert result[1] is None


def test_summary_is_not_used_when_the_note_already_answers():
    """The note remains the primary source; the summary is a fallback only."""
    note = """Notes to the Restated Consolidated Financial Information
37 Contingent Liabilities and Commitments
As at
31st March, 2026
As at
31st March, 2025
As at
31st March, 2024
Claims / disputed liabilities against the Group not
acknowledged as debts
1,200.50 900.25 750.00
"""
    pages = {1: PARAS_SUMMARY_DAY_FIRST, 405: note}
    _, amount, _, _ = _extractor(pages)._extract_contingent_liabilities({})
    assert amount == 1200.5


def test_a_column_header_split_across_lines_is_still_a_column():
    """Vishal Nirmiti prints ``As at March 31,`` / ``2026`` on two lines.

    Read line-by-line the header yields no date at all and the whole table
    becomes unreadable — for a layout reason, not an evidence reason.  A
    different issuer is exactly how that kind of over-fitting shows up.
    """
    text = """SUMMARY OF CONTINGENT LIABILITIES
Details of the contingent liabilities (as per Ind AS 37) of our Company as at March 31, 2026, March 31, 2025 and March 31, 2024 derived from the Restated Financial Statements are set forth below:
(Amount in ₹ lakhs)
Particulars  As at March 31,
2026
As at March 31,
2025
As at March 31,
2024
(i) Claim against the Company not acknowledged as debt
184.31 157.32 342.30
(ii) Bank Guarantees issued 2,002.33 2,265.53 2,275.16
Total 2,186.64 2,422.85 2,617.46
"""
    page, amount, unquantified, quote = _extractor({75: text})._read_contingent_liability_summary(
        [(1, 75)]
    )
    assert page == 75
    assert amount == 2186.64
    assert unquantified is None
    assert "31 March 2026" in quote
