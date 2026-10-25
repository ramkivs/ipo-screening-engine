"""Offer-for-Sale NIL binding: a NIL in another row is not the OFS value.

Verified defect (2026-10-19 HD Fire/Jio reconciliation): the cover-page
matcher searched up to 32 newlines after any "offer for sale" occurrence
for ``NIL`` / ``Not applicable``.  A pure-OFS cover whose *fresh issue*
row states NIL (a standard two-column layout) therefore matched and set
``issue.ofs = 0.0``, discarding the stated OFS quantity.  The operator's
HD Fire record exhibits exactly that conflict (filing-extracted 0 versus
the entered 71,231 for a pure-OFS offer).

The correction keeps the genuine positives (the Jio cover, where the
"Not applicable" is the OFS cell) and rejects a NIL that is the value of
another structural label.  No schema, scoring, golden or historical
record changes.
"""

from __future__ import annotations

from types import SimpleNamespace

from ipo_screening.extraction.sections import SectionExtractor, _find_ofs_nil


def _stub_extractor(cover: str) -> SectionExtractor:
    extractor = SectionExtractor.__new__(SectionExtractor)
    extractor.page_count = 4
    extractor.doc = SimpleNamespace(source_id="RHP-TEST-OFS")
    extractor.extract_page_text = lambda p: cover if p == 1 else ""
    return extractor


# ---------------------------------------------------------------------------
# Helper-level cases
# ---------------------------------------------------------------------------

def test_real_jio_cover_shape_still_establishes_the_ofs_is_nil():
    """The genuine two-column Jio cover: the OFS cell is Not applicable."""
    cover = (
        "TYPE FRESH ISSUE SIZE OFFER FOR SALE SIZE TOTAL ISSUE SIZE\n"
        "Fresh Issue Up to \n270,000,000 \nEquity Shares of \n"
        "aggregating up to \n₹[●] million \nNot applicable Up to \n"
        "270,000,000 \n"
    )
    assert _find_ofs_nil(cover) is not None


def test_same_line_not_applicable_is_accepted():
    assert _find_ofs_nil("Offer for Sale Size: Not applicable\n") is not None


def test_fresh_issue_nil_is_not_the_ofs_value():
    """The exact pre-fix false positive: a pure-OFS cover with a fresh NIL."""
    cover = (
        "Offer for Sale Size\n"
        "26,280,000 Equity Shares\n"
        "Fresh Issue\n"
        "NIL\n"
    )
    assert _find_ofs_nil(cover) is None


def test_pre_ipo_nil_is_not_the_ofs_value():
    cover = "Offer for Sale\nDetails are set out below.\nPre-IPO Placement\nNIL\n"
    assert _find_ofs_nil(cover) is None


def test_promoter_group_nil_is_not_the_ofs_value():
    cover = "Offer for Sale Size\nRs. 712.13 crore\nPromoter Group\nNIL\n"
    assert _find_ofs_nil(cover) is None


def test_an_amount_on_the_ofs_line_is_never_turned_into_nil():
    cover = "Offer for Sale Size 26,280,000 Equity Shares\nFresh Issue\nNIL\n"
    assert _find_ofs_nil(cover) is None


def test_a_label_and_nil_on_the_same_line_is_not_the_ofs_value():
    assert _find_ofs_nil("Offer for Sale Size\nFresh Issue: NIL\n") is None


# ---------------------------------------------------------------------------
# Extractor-level cases: the canonical field must stay unknown, never 0
# ---------------------------------------------------------------------------

def test_pure_ofs_cover_with_fresh_nil_does_not_fabricate_an_explicit_zero():
    cover = (
        "ACME FIRE PROTECT LIMITED\n"
        "DETAILS OF THE ISSUE\n"
        "TYPE FRESH ISSUE SIZE OFFER FOR SALE SIZE TOTAL ISSUE SIZE\n"
        "Fresh Issue\nNIL\n"
        "Offer for Sale of up to 26,280,000 Equity Shares by the Selling Shareholders\n"
    )
    fields = {ex.field_path: ex for ex in _stub_extractor(cover).extract_cover_and_offer()}
    # No fabricated explicit zero: the OFS amount is unknown, not "none".
    assert "issue.ofs" not in fields


def test_fresh_only_cover_still_establishes_ofs_zero():
    """The approved fresh-only shape (Jio) is unchanged."""
    cover = (
        "ACME LIMITED\n"
        "TYPE FRESH ISSUE SIZE OFFER FOR SALE SIZE\n"
        "Fresh Issue Up to 1,000 Equity Shares aggregating up to Rs.[x] million\n"
        "Not applicable\n"
    )
    fields = {ex.field_path: ex for ex in _stub_extractor(cover).extract_cover_and_offer()}
    assert fields["issue.ofs"].candidate_value == 0.0
    assert fields["issue.ofs_sellers"].candidate_value == []
