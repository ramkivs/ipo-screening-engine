"""Promoter pre/post-issue holding: the fallback that fabricates 100%.

Observed on the committed Jio RHP (p. 107, "Shareholding pattern of the
Company"):

    Total (A) Promoter & Promoter Group   5,937,841,645  66.43 %
    (B) Public                            3,001,189,185  33.57 %
    Total (A)+(B)+(C)                     8,939,030,830 100.00 %

``SectionExtractor.extract_capital_structure`` returns
``promoter_pre_pct = 100.0`` and ``promoter_post_pct = 100.0`` for that
page.  The filing states 66.43 %.  Three independent defects in the
"Total (A)"/"Total (B)" fallback produce that:

1. ``re.search(r"Total\\s*\\(\\s*A\\s*\\)", line)`` is a PREFIX match, so the
   ``Total (A)+(B)+(C)`` summary row is read as the promoter total, and the
   loop's last-match-wins assignment overwrites a genuine ``Total (A)`` row
   that appears earlier in the same block;
2. ``pre_pct = tot_a_pre + tot_b_pre`` adds the public category to the
   promoter category, which reconstructs 100 % by construction (ICDR
   shareholding format: (A) promoter & promoter group, (B) public);
3. the post-issue scan appends the following two lines to the matched row,
   so percentages from the next category leak into the promoter calculation.

Impact: ``promoter_post_pct`` feeds Module D ``promoter_post_holding``
(> 60 % -> 4/4) and K4's ``promoter_full_exit`` / ``< 20`` leaves.  A
fabricated 100 % therefore awards points and clears K4.

These tests are marked ``xfail(strict=True)``: they assert the CORRECT
behaviour, so they currently fail.  Correcting the extractor changes the
scored canonical input for filings of this shape (a new evaluation would
score differently), which is a missing-value/semantic decision that has not
been authorized; the marker must be removed only together with that
decision.  See ``docs/investigation/HD-FIRE-RHP-EVIDENCE-RECONCILIATION-2026-10-20.md``.
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


# The shareholding-pattern layout of Jio RHP p. 107 (verbatim row shape).
JIO_LIKE = """6. Shareholding pattern of the Company
Promoter & Promoter Group 1 5,937,841,645 - - 5,937,841,645 66.43 5,937,841,645 66.35
(B) Public 103 3,001,189,185 - - 3,001,189,185 33.57 3,001,189,185 33.57
Total (A)+(B)+(C) 104 8,939,030,830 - - 8,939,030,830 100.00 8,939,030,830 100.00"""

# A layout that does disclose a standalone promoter total.
STANDALONE_A = """Shareholding pattern
Total (A) 5,900,000,000 66.43 5,900,000,000 65.00"""

STANDALONE_A_AND_B = """Shareholding pattern
Total (A) 5,900,000,000 66.43 5,900,000,000 65.00
Total (B) 2,980,000,000 33.57 3,176,000,000 35.00"""


def test_standalone_promoter_total_is_extracted():
    """Positive control: with only a genuine ``Total (A)`` row the fallback
    returns the disclosed promoter holding.  The defect is triggered by
    neighbouring rows, not by the path itself."""
    out = _extract(STANDALONE_A)
    assert out["capital_structure.promoter_pre_pct"] == 66.43
    assert out["capital_structure.promoter_post_pct"] == 65.0


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Total (A) prefix-matches the Total (A)+(B)+(C) summary row; promoter "
        "holding is fabricated as 100% (Jio p.107 states 66.43%)"
    ),
)
def test_combined_total_row_is_not_the_promoter_holding():
    out = _extract(JIO_LIKE)
    # The promoter category is 66.43% pre-issue; the post-issue percentage is
    # printed as [●] on p.109, so it cannot be established from this table.
    assert out.get("capital_structure.promoter_pre_pct") == 66.43
    assert out.get("capital_structure.promoter_post_pct") is None


@pytest.mark.xfail(
    strict=True,
    reason="the public category total is added to the promoter total (A+B = 100%)",
)
def test_public_total_is_not_added_to_the_promoter_total():
    out = _extract(STANDALONE_A_AND_B)
    assert out.get("capital_structure.promoter_pre_pct") == 66.43
    assert out.get("capital_structure.promoter_post_pct") == 65.0


@pytest.mark.xfail(
    strict=True,
    reason="live Jio RHP p.107: extractor returns 100.0 where the filing states 66.43%",
)
def test_live_jio_shareholding_pattern():
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
    assert out.get("capital_structure.promoter_pre_pct") == 66.43
