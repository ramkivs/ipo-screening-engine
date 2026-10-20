"""HD Fire Protect: published-fix verification on primary-source shapes.

The shareholding table below is **reconstructed** from the SEBI-hosted
Abridged Prospectus for HD Fire Protect Limited (RHP dated October 5, 2026),
section 5, "Pre-Offer and post-Offer shareholding of our Promoters, the
members of our Promoter Group and additional top 10 Shareholders".  The rows,
share counts and percentages are the published values; the line breaks are a
reconstruction, because the PDF itself cannot be downloaded into this sandbox
(egress is blocked) and the page-fetch tool returns only the first 30 pages of
the full RHP.

Why this matters
----------------
HD Fire's promoter category is 95.33 % (Total (A)) and the promoter group is
4.67 % (Total (B)); both post-Offer columns are ``[●]`` because the RHP was
filed before the price band ("To be filled at the Prospectus stage").  The
pre-fix extractor took the last percentage of the ``Total (A)`` window
(95.33), added ``Total (B)`` (4.67) and emitted **100.00 % as the post-issue
holding** — the two *pre-issue* category totals.  That is the exact origin of
the ``promoter_post_pct = 100 %`` carried by the historical HD Fire record.

After decision A21 / D-3 the same table yields:

* ``promoter_pre_pct = 100.00``  (A + B, both promoter categories — correct)
* ``promoter_post_pct = None``   (the post columns are undisclosed — correct)

The historical record is not edited; this test only pins current behaviour.
"""

from __future__ import annotations

import pytest

from ipo_screening.extraction.sections import SectionExtractor

from test_promoter_holding_extraction import _StubDoc, _StubReader, _extract

# RHP section 5 (Abridged Prospectus), reconstructed row-for-row.
HD_FIRE_TABLE = """Shareholding pattern
Pre-Offer shareholding as on the date of the Red Herring Prospectus Post-Offer shareholding as at the date of Allotment
Promoters
Harish Narshi Dharamshi 98,351,000 56.13% [●] [●] [●] [●]
Kusum Harish Dharamshi 31,240,000 17.83% [●] [●] [●] [●]
Miheer Sadanand Ghotikar 18,392,000 10.49% [●] [●] [●] [●]
Parika Miheer Ghotikar 11,594,000 6.62% [●] [●] [●] [●]
Anik Narendra Dharamshi 7,458,000 4.26% [●] [●] [●] [●]
Total (A) 167,035,000 95.33% [●] [●] [●] [●]
Promoter Group (other than the Promoters)
Narendra Visanji Dharamshi 6,006,000 3.43% [●] [●] [●] [●]
Hiren Narshi Dharamshi (HUF) 792,000 0.45% [●] [●] [●] [●]
Frenal Rishi Lodaya 462,000 0.26% [●] [●] [●] [●]
Avika Miheer Ghotikar 440,000 0.25% [●] [●] [●] [●]
Riaan Miheer Ghotikar 440,000 0.25% [●] [●] [●] [●]
Usha Ashwin Shah 55,000 0.03% [●] [●] [●] [●]
Total (B) 8,195,000 4.67% [●] [●] [●] [●]
Additional top 10 Shareholders (other than Promoters and Promoter Group)
Nil Nil Nil [●] [●] [●] [●]
Total (C) Nil Nil [●] [●] [●] [●]
Other public shareholders
Nil Nil Nil [●] [●] [●] [●]
Total (D) Nil Nil [●] [●] [●] [●]
Total (A+B+C+D) 175,230,000 100% [●] [●] [●] [●]"""

# The combined whole-company row on its own: no promoter split is derivable.
HD_FIRE_COMBINED_ONLY = """Shareholding pattern
Pre-Offer shareholding as on the date of the Red Herring Prospectus Post-Offer shareholding as at the date of Allotment
Total (A+B+C+D) 175,230,000 100% [●] [●] [●] [●]"""


def test_hd_fire_pre_offer_categories_are_summed_and_post_stays_unknown():
    out = _extract(HD_FIRE_TABLE, page=95)
    assert out.get("capital_structure.promoter_pre_pct") == 100.0
    # The RHP prints [●] in both post-Offer columns: the post-issue holding is
    # UNKNOWN, and the pre-issue 100.00 must never be reused as the post value.
    assert out.get("capital_structure.promoter_post_pct") is None


def test_hd_fire_combined_row_alone_fabricates_nothing():
    out = _extract(HD_FIRE_COMBINED_ONLY, page=95)
    assert out.get("capital_structure.promoter_pre_pct") is None
    assert out.get("capital_structure.promoter_post_pct") is None


# The governance text below is the "Auditor Qualifications" statement of the
# Abridged Prospectus, verbatim, plus the statutory auditor's name.
HD_FIRE_AUDITOR_TEXT = """Statutory Auditors
Our statutory auditors are KKC & Associates LLP, Chartered Accountants.
Auditor Qualifications
There are no reservations, qualifications and adverse remarks included by the Statutory Auditors in the Restated Financial Information.
"""


def _governance(text: str, pages=(250, 260)):
    ex = SectionExtractor(_StubDoc(), _StubReader(400), text_cache={257: text})
    raw = ex.extract_governance({"governance": pages})
    return {r.field_path: r for r in raw}


def test_hd_fire_auditor_text_emits_no_unsupported_tenure_or_eom_negative():
    out = _governance(HD_FIRE_AUDITOR_TEXT)
    # D-4: no positive tenure sentence and no explicit negative EOM statement
    # in this text, so both fields stay absent (UNKNOWN) rather than False.
    assert "governance.auditor_changed_3y" not in out
    assert "governance.repeated_eom" not in out


def test_hd_fire_auditor_text_emits_no_going_concern_negative():
    out = _governance(HD_FIRE_AUDITOR_TEXT)
    # D-1: absence of a going-concern paragraph is never emitted as False.
    assert "governance.going_concern_uncertainty" not in out


def test_litigation_bucket_is_not_clean_without_evidence():
    # D-5 / A23.  This text carries no litigation statement at all.  The field
    # is emitted as an explicit UNKNOWN (null candidate, no quotation) rather
    # than omitted, so the scan's provenance survives; what must never appear
    # is a "clean" verdict.
    out = _governance(HD_FIRE_AUDITOR_TEXT)
    record = out.get("governance.litigation_bucket")
    if record is not None:
        assert record.candidate_value is None
        assert record.is_unknown is True
        assert record.quote is None


def test_sebi_action_default_quote_is_not_presented_as_source_text():
    # D-5 / A23.  The fabricated "No active SEBI or ED regulatory proceedings"
    # quotation is gone: with no SEBI/ED statement in the source the record is
    # UNKNOWN and carries no quote at all.
    out = _governance(HD_FIRE_AUDITOR_TEXT)
    record = out.get("governance.sebi_ed_action_active")
    if record is not None:
        assert record.candidate_value is None
        assert record.is_unknown is True
        assert record.quote is None
        assert record.quote_is_processing is False
