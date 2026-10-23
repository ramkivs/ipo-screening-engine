"""Contingent-liability note extraction (knockout K5 input), 2026-10-20.

Observed before the change (Jio RHP, SHA-256 ``72480c2e…1b6d``):

* the note lookup started at page 250 and accepted the first page matching
  "Contingent Liabilities", which is neither the note nor the right period;
* `_parse_contingent_liabilities` returned the first line containing "Total"
  and a decimal.  Pointed at Jio's Note 37 that line is "Total 534 469 806
  208 154" — the key-management compensation total — so a knockout input
  could be populated with an unrelated figure;
* `financials.contingent_liabilities_unquantified` had no extraction path at
  all, so the second K5 leaf could never be established.

The reader anchors on the note's own heading, reads the period headers
immediately above the first row, selects the **latest fiscal-year column
(31 March)** so the amount is period-consistent with the full-year net worth
it is divided by, and fails closed on any width or header ambiguity.

Numerator definition (decision D-2, 2026-10-20): the disclosed total of the
**contingent-liability section**.  A unique ``Total`` row wins and its
constituent rows are ignored (no double counting); otherwise the section's
rows are summed.  Capital commitments -- a ``(II) Commitments`` subsection or
a commitment-labelled row -- are excluded, because a contractual commitment
is not a contingent liability.  A quantified subset is not evidence that the
whole section is quantified: an unparseable row, more than one total, or an
unquantified exposure without a disclosed total leaves the amount unknown.

The unquantified flag is set only from a positive unquantified disclosure; a
negated statement leaves it unknown (never False), and an absent disclosure
leaves it unknown too.

K5 still cannot be cleared on Jio: it requires both the quantified ratio and
the unquantified flag, and the source contains no unquantified statement.
"""

from __future__ import annotations

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.extraction.financial_tables import FinancialTableExtractor

JIO_PDF = (
    REPO_ROOT / "evidence" / "non-authoritative" / "jio"
    / "U72900GJ2019PLC110816_JIO.pdf"
)

JIO_NOTE_37 = """JIO PLATFORMS LIMITED
Notes to the Restated Consolidated Financial Information
(All amounts are Rs. in millions unless otherwise stated)
37 Contingent Liabilities and Commitments
As at
30th June, 2026
As at
30th June, 2025
As at
31st March, 2026
As at
31st March, 2025
As at
31st March, 2024
(I) Contingent Liabilities
Claims / disputed liabilities against the Group not
acknowledged as debts*
14,688 14,151 15,021 30,183 27,924
The claims/disputed liabilities are not likely to have any
material effect on financial position of the Group.
(II) Commitments
Estimated amount of contracts remaining to be executed on
Capital account not provided for
90,389 65,624 26,198 51,272 58,284
36.2 Compensation of Key Management Personnel
Total 534 469 806 208 154
"""


def _extractor(pages):
    extractor = FinancialTableExtractor.__new__(FinancialTableExtractor)
    extractor.page_count = max(pages) if pages else 1
    extractor.extract_page_text = lambda p: pages.get(p, "")
    return extractor


def _read(pages, ranges=None):
    return _extractor(pages)._extract_contingent_liabilities(ranges or {})


def test_five_column_note_selects_the_latest_fiscal_year():
    """FY2026 (31 March 2026) is 15,021, not the June-2026 interim 14,688 and
    not the commitments total."""
    page, amount, unquantified, quote = _read({405: JIO_NOTE_37})
    assert page == 405
    assert amount == 15021.0
    assert unquantified is None
    assert "not acknowledged as debts" in quote


def test_adjacent_note_with_the_same_header_does_not_shift_the_columns():
    """Note 38 repeats the five period headings on the following page; the
    header window must stay inside Note 37."""
    _, amount, _, _ = _read({405: JIO_NOTE_37, 406: JIO_NOTE_37.replace("37 ", "38 ")})
    assert amount == 15021.0


def test_three_column_fiscal_note_selects_the_latest_year():
    note = """Notes to the Restated Consolidated Financial Information
38 Contingent liabilities and commitments
As at 31st March, 2026 As at 31st March, 2025 As at 31st March, 2024
Claims/disputed liabilities not acknowledged as debts 1,200.50 900.25 750.00
Commitments 400.00 300.00 200.00
"""
    _, amount, _, _ = _read({330: note})
    assert amount == 1200.5


def test_row_width_mismatch_fails_closed():
    note = JIO_NOTE_37.replace(
        "14,688 14,151 15,021 30,183 27,924", "14,688 14,151 15,021 30,183"
    )
    assert _read({405: note})[1] is None


def test_missing_period_headers_fail_closed():
    note = "\n".join(
        line
        for line in JIO_NOTE_37.splitlines()
        if "March" not in line and "June" not in line
    )
    assert _read({405: note})[1] is None


def test_unquantified_disclosure_is_flagged_but_absence_is_not_false():
    flagged = JIO_NOTE_37.replace(
        "The claims/disputed liabilities are not likely to have any",
        "Certain claims are unquantified. The claims/disputed liabilities are not likely to have any",
    )
    _, amount, unquantified, _ = _read({405: flagged})
    # An unquantified exposure and no disclosed section total: the total is
    # not established, so the amount is unknown (D-2).  The flag still
    # suppresses any CLEAR of K5.
    assert amount is None
    assert unquantified is True
    assert _read({405: JIO_NOTE_37})[2] is None


def test_negated_unquantified_statement_does_not_trigger_k5():
    """'There are no unquantified claims' contains the keyword but asserts the
    opposite.  It must leave the flag unknown, not raise a K5 trigger."""
    note = JIO_NOTE_37.replace(
        "The claims/disputed liabilities are not likely to have any",
        "There are no unquantified claims. The claims/disputed liabilities are not likely to have any",
    )
    _, amount, unquantified, _ = _read({405: note})
    assert amount == 15021.0
    assert unquantified is None


CL_HEADER = """Notes to the Restated Consolidated Financial Information
(All amounts are Rs. in crore unless otherwise stated)
37 Contingent Liabilities and Commitments
As at 31st March, 2026 As at 31st March, 2025 As at 31st March, 2024
"""


def _section(body: str) -> str:
    return CL_HEADER + body


def test_guarantees_are_counted_without_a_claims_row():
    """A note that itemises guarantees/EPCG but has no claims label is still
    the contingent-liability section; the claims row is not the numerator."""
    note = _section(
        """(I) Contingent Liabilities
Bank guarantees secured on fixed deposits 5,850.00 4,100.00 3,000.00
Unfulfilled EPCG export obligations 3,143.00 2,900.00 2,500.00
(II) Commitments
Estimated amount of contracts remaining to be executed on capital account not provided for 1,200.00 900.00 800.00
"""
    )
    _, amount, unquantified, _ = _read({405: note})
    assert amount == 8993.0
    assert unquantified is None


def test_multiple_categories_within_the_section_are_summed():
    note = _section(
        """(I) Contingent Liabilities
Claims / disputed liabilities against the Company not acknowledged as debts 1,000.00 900.00 800.00
Bank guarantees secured on fixed deposits 5,850.00 4,100.00 3,000.00
"""
    )
    _, amount, _, _ = _read({405: note})
    assert amount == 6850.0


def test_disclosed_total_is_not_added_to_its_constituent_rows():
    """Aggregate plus components must not double count."""
    note = _section(
        """(I) Contingent Liabilities
Bank guarantees 5,850.00 4,100.00 3,000.00
Unfulfilled EPCG export obligations 3,143.00 2,900.00 2,500.00
Total contingent liabilities 8,993.00 7,000.00 5,500.00
"""
    )
    _, amount, _, quote = _read({405: note})
    assert amount == 8993.0
    # A29: the citation now carries the selected cell and its column after the
    # verbatim label.  The label is still the first element, so the evidence can
    # be read back against the note; the earlier exact-equality assertion
    # pinned the label-only form this pass deliberately replaced.
    assert quote.startswith("Total contingent liabilities")
    assert "8,993 as at 31 March 2026" in quote


def test_commitments_are_excluded_from_the_numerator():
    """Capital commitments are a contractual obligation, not a contingent
    liability, even when the reader sees them (D-2)."""
    note = _section(
        """(I) Contingent Liabilities
Bank guarantees 5,850.00 4,100.00 3,000.00
(II) Commitments
Capital commitments 1,200.00 900.00 800.00
"""
    )
    _, amount, _, _ = _read({405: note})
    assert amount == 5850.0


def test_two_disclosed_totals_leave_the_amount_unknown():
    note = _section(
        """(I) Contingent Liabilities
Bank guarantees 5,850.00 4,100.00 3,000.00
Total 5,850.00 4,100.00 3,000.00
Total 6,450.00 4,500.00 3,300.00
"""
    )
    _, amount, _, _ = _read({405: note})
    assert amount is None


def test_unquantified_exposure_without_a_total_leaves_the_amount_unknown():
    note = _section(
        """(I) Contingent Liabilities
Bank guarantees 5,850.00 4,100.00 3,000.00
Certain claims are unquantified.
"""
    )
    _, amount, unquantified, _ = _read({405: note})
    assert amount is None
    assert unquantified is True


def test_unquantified_exposure_with_a_disclosed_total_keeps_the_total():
    note = _section(
        """(I) Contingent Liabilities
Bank guarantees 5,850.00 4,100.00 3,000.00
Certain claims are unquantified.
Total 6,450.00 4,500.00 3,300.00
"""
    )
    _, amount, unquantified, _ = _read({405: note})
    assert amount == 6450.0
    assert unquantified is True


def test_next_numbered_note_on_the_same_page_is_not_part_of_the_section():
    note = _section(
        """(I) Contingent Liabilities
Bank guarantees 5,850.00 4,100.00 3,000.00
38 Capital Management
Borrowings 707.00 650.00 600.00
"""
    )
    _, amount, _, _ = _read({405: note})
    assert amount == 5850.0


def test_no_note_fails_closed():
    assert _read({405: "Profit and loss statement without the note."})[1] is None


@pytest.mark.slow
def test_jio_real_filing_contingent_liabilities():
    doc, _ = DocumentExtractor().extract_from_pdf(
        pdf_path=JIO_PDF, allow_fixture_fallbacks=False
    )
    financials = doc["financials"]
    assert financials["contingent_liabilities"] == 15021.0
    assert financials["contingent_liabilities_unquantified"] is None
