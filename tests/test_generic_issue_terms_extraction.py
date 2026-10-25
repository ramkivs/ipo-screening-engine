"""Generic fresh-issue vs OFS quantity separation (Windows-evidence-led).

Primary regression: on a real RHP cover, the sentence
"... (FRESH OFFER) AND AN OFFER FOR SALE OF UP TO 15,00,000 EQUITY
SHARES" caused the OFS quantity to be recorded as `issue.fresh_shares`
(the unguarded `fresh (offer|issue) ... equity shares` span crossed the
OFS clause). Quantities are now bound to their semantic label within a
bounded window; an intervening other-component label rejects the
candidate, and contradictory bindings fail closed.

Genericity: fixtures below use two invented issuers, different IPO
quantities and layouts. No production logic references any issuer.
"""

from __future__ import annotations

from types import SimpleNamespace

from ipo_screening.extraction.prospectus_terms import _quote_window
from ipo_screening.extraction.sections import SectionExtractor


def _extractor(cover: str, source_id: str = "RHP-TEST-0001"):
    extractor = SectionExtractor.__new__(SectionExtractor)
    extractor.page_count = 4
    extractor.doc = SimpleNamespace(source_id=source_id)
    extractor.extract_page_text = lambda p: cover if p == 1 else ""
    return extractor


def _fields(extractions):
    return {ex.field_path: ex for ex in extractions}


WINDOWS_COVER = """RED HERRING PROSPECTUS Dated: September 24, 2026
100% Book Built Offer
ACME PRECISION LIMITED
INITIAL PUBLIC OFFERING OF 80,90,909 EQUITY SHARES OF FACE VALUE OF ₹ 10 EACH ("EQUITY SHARES") OF
ACME PRECISION LIMITED ("OUR COMPANY") FOR CASH AT A PRICE OF ₹ [●] PER EQUITY SHARE AGGREGATING
UP TO ₹ [●] LAKHS COMPRISING A FRESH ISSUE OF 65,90,909 EQUITY SHARES AGGREGATING UP TO ₹ 14,500.00
LAKHS BY OUR COMPANY ("FRESH OFFER") AND AN OFFER FOR SALE OF UP TO 15,00,000 EQUITY SHARES
AGGREGATING UP TO ₹ 3,300.00 LAKHS BY VAMAN PRESTRESSING COMPANY PRIVATE LIMITED ("SELLING SHAREHOLDER")
"""

AMOUNT_FIRST_COVER = """RED HERRING PROSPECTUS
ZENITH POLYMERS LIMITED
THE OFFER COMPRISES A FRESH ISSUE AGGREGATING UP TO ₹ 9,000.00 LAKHS BY OUR COMPANY ("FRESH OFFER")
AND AN OFFER FOR SALE OF UP TO 25,00,000 EQUITY SHARES BY ORBIT HOLDINGS PRIVATE LIMITED ("SELLING SHAREHOLDER")
"""


def test_windows_regression_ofs_quantity_is_not_fresh_shares():
    fields = _fields(_extractor(WINDOWS_COVER).extract_cover_and_offer())
    fresh = fields.get("issue.fresh_shares")
    assert fresh is not None
    assert fresh.candidate_value == 6590909  # the FRESH quantity, from its own clause
    sellers = fields["issue.ofs_sellers"].candidate_value
    assert len(sellers) == 1
    assert sellers[0]["name"] == "VAMAN PRESTRESSING COMPANY PRIVATE LIMITED"
    assert sellers[0]["shares_sold"] == 1500000  # the OFS quantity, separately mapped


def test_amount_first_cover_does_not_invent_fresh_shares():
    """Fresh quantity stated only as an amount: the OFS share count must
    not become fresh_shares (the exact Windows failure shape)."""
    fields = _fields(_extractor(AMOUNT_FIRST_COVER).extract_cover_and_offer())
    assert "issue.fresh_shares" not in fields
    sellers = fields["issue.ofs_sellers"].candidate_value
    assert sellers[0]["shares_sold"] == 2500000


def test_fresh_only_cover_invents_no_ofs():
    cover = """RED HERRING PROSPECTUS
MERIDIAN TEXTILES LIMITED
FRESH ISSUE OF 40,00,000 EQUITY SHARES AGGREGATING UP TO ₹ 8,000.00 LAKHS BY OUR COMPANY ("FRESH OFFER")
"""
    fields = _fields(_extractor(cover).extract_cover_and_offer())
    assert fields["issue.fresh_shares"].candidate_value == 4000000
    assert "issue.ofs_sellers" not in fields


def test_ofs_only_cover_invents_no_fresh_shares():
    cover = """RED HERRING PROSPECTUS
MERIDIAN TEXTILES LIMITED
OFFER FOR SALE OF UP TO 12,00,000 EQUITY SHARES BY ORBIT HOLDINGS PRIVATE LIMITED ("SELLING SHAREHOLDER")
"""
    fields = _fields(_extractor(cover).extract_cover_and_offer())
    assert "issue.fresh_shares" not in fields
    assert fields["issue.ofs_sellers"].candidate_value[0]["shares_sold"] == 1200000


def test_multiple_sellers_aggregate_is_not_attributed():
    cover = """RED HERRING PROSPECTUS
ACME PRECISION LIMITED
FRESH ISSUE OF 10,00,000 EQUITY SHARES ("FRESH OFFER") AND AN OFFER FOR SALE OF UP TO 30,00,000
EQUITY SHARES BY ALPHA HOLDINGS PRIVATE LIMITED ("SELLING SHAREHOLDER"), BETA CAPITAL PRIVATE
LIMITED ("SELLING SHAREHOLDER") AND GAMMA TRUST LIMITED ("SELLING SHAREHOLDER")
"""
    fields = _fields(_extractor(cover).extract_cover_and_offer())
    assert fields["issue.fresh_shares"].candidate_value == 1000000
    sellers_extraction = fields["issue.ofs_sellers"]
    # Identity preserved in the recorded quotation; canonical attribution
    # fails closed (empty list) rather than assigning 30,00,000 to anyone.
    assert sellers_extraction.candidate_value == []
    assert "ALPHA HOLDINGS PRIVATE LIMITED" in sellers_extraction.quote
    assert "BETA CAPITAL PRIVATE" in sellers_extraction.quote


def test_contradictory_fresh_quantities_fail_closed():
    cover = """RED HERRING PROSPECTUS
ACME PRECISION LIMITED
FRESH ISSUE OF 10,00,000 EQUITY SHARES AGGREGATING UP TO ₹ 2,000.00 LAKHS
THE FRESH OFFER COMPRISES A FRESH ISSUE OF 20,00,000 EQUITY SHARES AS RESTATED IN THE SUMMARY
"""
    fields = _fields(_extractor(cover).extract_cover_and_offer())
    assert "issue.fresh_shares" not in fields


def test_quote_window_snaps_to_definition_boundaries():
    text = (
        'Previous definition ends here. “Cap Price” The higher end of the Price Band, '
        'in this case being, ₹ 220 per Equity Share above which no Bids were accepted. '
        '“Cash Escrow Agreement” Agreement dated January 1.'
    )
    start = text.index("₹ 220")
    quote = _quote_window(text, start, start + 5)
    assert quote.startswith("“Cap Price”")
    assert quote.endswith("accepted.")
    assert "Cash Escrow" not in quote
    assert quote in text  # exact source substring, never rewritten
