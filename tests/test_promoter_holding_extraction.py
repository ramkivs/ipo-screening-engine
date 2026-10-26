"""Promoter holding: the combined summary row is not the promoter total.

The shareholding-pattern summary is::

    Total (A) Promoter & Promoter Group   5,937,841,645  66.43 %
    (B) Public                            3,001,189,185  33.57 %
    Total (A)+(B)+(C)                     8,939,030,830 100.00 %

The fallback in ``SectionExtractor.extract_capital_structure`` matched
``Total (A)`` as a **prefix**, so the combined ``Total (A)+(B)+(C)`` row also
satisfied it and the promoter holding was fabricated as 100 % (Jio RHP
p. 107 states 66.43 % pre-issue and prints ``[●]`` post-issue).

Corrected behaviour (narrow guard): the label test requires a standalone
``Total (A)``; a combined summary row no longer matches.  Everything else in
the fallback is unchanged, deliberately:

* the public category is still added to the promoter category when both
  standalone rows exist.  Removing that sum changes R.K. Fashion's extracted
  value from **99.67 % to 99.61 %** — the filing discloses both figures in two
  different tables (Total (A) 99.61 % on the Regulation 31 pattern; "Promoter
  and Promoter Group" 99.67 % on the promoter table).  Choosing between two
  disclosed promoter figures is a semantic decision (D-3), not a guard;
* a filing whose only total is the combined summary now yields **UNKNOWN**
  rather than a fabricated 100 %.  That is the existing missing-value
  contract: no promoter split is derivable from the whole-company row.

Impact: ``promoter_post_pct`` feeds Module D ``promoter_post_holding``
(> 60 % -> 4/4) and K4's ``promoter_full_exit`` / ``< 20`` leaves.  For Jio the
fabricated 100 % becomes UNKNOWN, so the criterion becomes UNKNOWN (a re-run
loses 4 earned and 4 available points).  Historical records are not touched.
"""

from __future__ import annotations

import pytest

from ipo_screening.extraction.sections import SectionExtractor


class _StubDoc:
    source_id = "SRC-TEST"


class _StubReader:
    def __init__(self, n: int) -> None:
        self.pages = [None] * n


def _extract(text: str, page: int = 107):
    ex = SectionExtractor(_StubDoc(), _StubReader(200), text_cache={page: text})
    raw = ex.extract_capital_structure({"capital_structure": (page, page)})
    return {r.field_path: r.candidate_value for r in raw}


# The shareholding-pattern layout of Jio RHP p. 107 (verbatim row shape):
# the promoter category is a named row; the only "Total" line is combined.
JIO_LIKE = """6. Shareholding pattern of the Company
Promoter & Promoter Group 1 5,937,841,645 - - 5,937,841,645 66.43 5,937,841,645 66.35
(B) Public 103 3,001,189,185 - - 3,001,189,185 33.57 3,001,189,185 33.57
Total (A)+(B)+(C) 104 8,939,030,830 - - 8,939,030,830 100.00 8,939,030,830 100.00"""

# A layout that does disclose a standalone promoter total, with an explicit
# post-issue column.
STANDALONE_A = """Shareholding pattern
Pre-Offer shareholding Post-Offer shareholding as at Allotment
Total (A) 5,900,000,000 66.43 5,900,000,000 65.00"""

# The ICDR summary layout: (A) is Promoter & Promoter Group, (B) is Public.
STANDALONE_A_AND_B = """Shareholding pattern
Pre-Offer shareholding Post-Offer shareholding as at Allotment
(A) Promoter & Promoter Group
Total (A) 5,900,000,000 66.43 5,900,000,000 65.00
(B) Public
Total (B) 2,980,000,000 33.57 3,176,000,000 35.00"""

# The detailed layout (R.K. Fashion shape): (A) Promoters, (B) Promoter Group.
PROMOTER_AND_GROUP = """Shareholding pattern
Pre-Offer shareholding Post-Offer shareholding as at Allotment
(A) Promoters
Total (A) 1,12,06,672 99.61 1,12,06,672 72.22
(B) Promoter Group
Total (B) 5,100 0.06 5,100 0.03"""

# A pre-issue-only table: every post-issue column is "[●]" (Vishal shape).
PRE_ONLY_TABLE = """Shareholding pattern
Pre-Offer shareholding as at the date of this Red Herring Prospectus
Total (A) 74,27,420 37.51 [●] [●]"""

# No category heading: whether (B) belongs in the promoter total is unknown.
UNLABELLED_B = """Shareholding pattern
Pre-Offer shareholding Post-Offer shareholding as at Allotment
Total (A) 5,900,000,000 66.43 5,900,000,000 65.00
Total (B) 2,980,000,000 33.57 3,176,000,000 35.00"""


def test_standalone_promoter_total_is_extracted():
    """Positive control: with a genuine ``Total (A)`` row the fallback
    returns the disclosed promoter holding."""
    out = _extract(STANDALONE_A)
    assert out["capital_structure.promoter_pre_pct"] == 66.43
    assert out["capital_structure.promoter_post_pct"] == 65.0


def test_combined_total_row_is_not_the_promoter_holding():
    """``Total (A)+(B)+(C)`` is the whole company.

    The promoter split cannot be recovered from the summary alone, so the
    field is UNKNOWN; recovering the disclosed 66.43 % needs the promoter-row
    parser (option (b) of decision D-3).
    """
    out = _extract(JIO_LIKE)
    assert out.get("capital_structure.promoter_pre_pct") is None
    assert out.get("capital_structure.promoter_post_pct") is None


def test_public_total_is_not_added_to_the_promoter_total():
    """The public category is not part of the promoter holding (decision D-3)."""
    out = _extract(STANDALONE_A_AND_B)
    assert out.get("capital_structure.promoter_pre_pct") == 66.43
    assert out.get("capital_structure.promoter_post_pct") == 65.0


def test_promoter_group_total_is_added_to_the_promoter_total():
    """In the detailed layout (B) is the promoter group, which belongs in the
    promoter-and-promoter-group figure (R.K. Fashion shape)."""
    out = _extract(PROMOTER_AND_GROUP)
    assert out.get("capital_structure.promoter_pre_pct") == 99.67
    assert out.get("capital_structure.promoter_post_pct") == 72.25


def test_pre_issue_table_does_not_supply_a_post_issue_value():
    """The row's only numeric percentage is the pre-issue one; the post-issue
    columns are "[●]", so the post-issue holding is unknown (D-3b)."""
    out = _extract(PRE_ONLY_TABLE)
    assert out.get("capital_structure.promoter_pre_pct") == 37.51
    assert out.get("capital_structure.promoter_post_pct") is None


def test_unlabelled_b_total_leaves_the_promoter_holding_unknown():
    """Without a category heading, whether (B) is the promoter group or the
    public cannot be established, so neither value is guessed."""
    out = _extract(UNLABELLED_B)
    assert out.get("capital_structure.promoter_pre_pct") is None
    assert out.get("capital_structure.promoter_post_pct") is None


def test_live_vishal_pre_issue_table_is_not_read_as_post_issue():
    """Vishal's section 11 table is a pre-issue table whose post-issue cells
    are "[●]"; the extracted post-issue holding must be UNKNOWN, not the
    pre-issue Total (A) of 37.51 %."""
    from pathlib import Path

    from ipo_screening.extraction.pdf_source import load_pdf_source

    pdf = (
        Path(__file__).resolve().parents[1]
        / "handoff/reference/U01122MH1994PLC185445-vishal nirmiti.pdf"
    )
    if not pdf.exists():  # pragma: no cover - reference filing absent
        pytest.skip("reference Vishal RHP is not present")
    doc, reader = load_pdf_source(pdf)
    ex = SectionExtractor(doc, reader, text_cache={})
    out = {r.field_path: r.candidate_value for r in ex.extract_capital_structure({})}
    assert out.get("capital_structure.promoter_pre_pct") == 73.42
    assert out.get("capital_structure.promoter_post_pct") is None


def test_live_jio_shareholding_pattern_is_not_fabricated():
    """Live pin on the committed RHP: no 100 % where the filing states
    66.43 % pre-issue and prints ``[●]`` post-issue."""
    from pathlib import Path

    from ipo_screening.extraction.pdf_source import load_pdf_source
    from ipo_screening.extraction.toc import TOCRouter

    pdf = (
        Path(__file__).resolve().parents[1]
        / "evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf"
    )
    if not pdf.exists():  # pragma: no cover - evidence absent in a trimmed checkout
        pytest.skip("committed Jio RHP is not present")
    doc, reader = load_pdf_source(pdf)
    toc = TOCRouter.from_pdf(reader)
    ranges = {k: toc.get_page_range(k) for k in toc.entries if toc.get_page_range(k)}
    ex = SectionExtractor(doc, reader, text_cache={})
    out = {r.field_path: r.candidate_value for r in ex.extract_capital_structure(ranges)}
    # 2026-10-23: the filing's sole-promoter row prints the pre-issue percentage
    # (5,937,841,645 shares, 66.43 %, identical post count, post "[●]"). Reading
    # that printed value is not fabrication; the post-issue percentage remains
    # unknown and no 100 % is ever emitted.
    assert out.get("capital_structure.promoter_pre_pct") == 66.43
    assert out.get("capital_structure.promoter_post_pct") is None


@pytest.mark.parametrize("tail", [
    "72 99.61 1,12,06,672 72.22 1,12,06,672 72.22",
    "72 99.61\n1,12,06,672 72.22\n1,12,06,672 72.22",
    "72\n99.61\n1,12,06,672\n72.22\n1,12,06,672\n72.22",
])
def test_wrapped_total_keeps_pre_and_both_post_columns(tail):
    text = ("Pre-Offer shareholding Post-Offer shareholding as at Allotment\n"
            "Promoters\nTotal (A) 1,12,06,6\n" + tail +
            "\nPromoter Group\nTotal (B) 5,100 0.06 5,100 0.03 5,100 0.03")
    out = _extract(text)
    assert out["capital_structure.promoter_pre_pct"] == 99.67
    assert out["capital_structure.promoter_post_pct"] == 72.25


@pytest.mark.parametrize("boundary", ["Public", "Promoter Group", "Total (B)",
                                      "1. Other shareholder", "1. 1000 20.00", "Footnote"])
def test_wrapped_row_never_borrows_percentages_across_a_row_boundary(boundary):
    lines = ["Total (A) 1,234 61.00", boundary, "1,234 45.00 1,234 45.00"]
    assert SectionExtractor._row_percentages(lines, 0) == [61.0]


def test_wrapped_pre_only_row_stays_unknown_after_offer():
    out = _extract("Pre-Offer shareholding Post-Offer shareholding\n"
                   "Total (A) 1,234\n61.00\n[●] [●]\n[●] [●]\nPublic\n"
                   "Total (B) 2,345 39.00 3,456 55.00")
    assert out["capital_structure.promoter_pre_pct"] == 61.0
    assert out.get("capital_structure.promoter_post_pct") is None


def test_wrapped_pre_only_table_cannot_supply_post_offer_cells():
    out = _extract("Pre-Offer shareholding\nTotal (A) 1,234\n61.00\n1,234 60.00")
    assert out.get("capital_structure.promoter_post_pct") is None


@pytest.mark.parametrize("row", ["Total (A) 1,234 61.00\n1,234 45.00\n[●] [●]",
                                  "Total (A) 1,234 [●]\n1,234 45.00\n1,234 45.00"])
def test_undisclosed_wrapped_columns_are_not_collapsed(row):
    out = _extract("Pre-Offer shareholding Post-Offer shareholding\n" + row)
    assert out.get("capital_structure.promoter_post_pct") is None


def test_wrapped_numeric_overflow_is_not_an_extra_post_scenario():
    assert SectionExtractor._row_percentages([
        "Total (A) 1,234 61.00", "1,234 45.00 1,234 45.00", "2,345 55.00"], 0) == []


def test_unterminated_numeric_row_fails_closed():
    assert SectionExtractor._row_percentages(["Total (A) 1,234 61.00"] + ["1234"] * 17, 0) == []


def test_wrapping_retains_upper_band_column_order_not_maximum():
    out = _extract("Pre-Offer shareholding Post-Offer shareholding\n"
                   "Total (A) 1,234 61.00\n1,234 55.00\n1,234 45.00")
    assert out["capital_structure.promoter_post_pct"] == 45.0


def test_wrapped_group_with_undisclosed_post_value_stays_unknown():
    out = _extract("Pre-Offer shareholding Post-Offer shareholding\n"
                   "Promoters\nTotal (A) 1,234 61.00\n1,234 45.00\n1,234 45.00\n"
                   "Promoter Group\nTotal (B) 123 1.00\n123 0.80\n[●] [●]")
    assert out.get("capital_structure.promoter_post_pct") is None


@pytest.mark.parametrize("marker", ["-", "—", "–", "[●]", "[•]", "[*]"])
def test_wrapped_missing_upper_band_cell_is_unknown(marker):
    out = _extract("Pre-Offer shareholding Post-Offer shareholding\n"
                   "Total (A) 1,234 61.00\n1,234 45.00\n" + marker)
    assert out.get("capital_structure.promoter_post_pct") is None
