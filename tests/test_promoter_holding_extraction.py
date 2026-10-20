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

# A layout that does disclose a standalone promoter total.
STANDALONE_A = """Shareholding pattern
Total (A) 5,900,000,000 66.43 5,900,000,000 65.00"""

STANDALONE_A_AND_B = """Shareholding pattern
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


@pytest.mark.xfail(
    strict=True,
    reason=(
        "the public category total is added to the promoter total (A+B = 100%); "
        "removing the sum changes R.K. Fashion 99.67 -> 99.61, which is decision D-3"
    ),
)
def test_public_total_is_not_added_to_the_promoter_total():
    out = _extract(STANDALONE_A_AND_B)
    assert out.get("capital_structure.promoter_pre_pct") == 66.43
    assert out.get("capital_structure.promoter_post_pct") == 65.0


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
    assert out.get("capital_structure.promoter_pre_pct") is None
    assert out.get("capital_structure.promoter_post_pct") is None
