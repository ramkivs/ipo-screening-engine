"""Official RHP document class, current-issue dates and OFS resolution.

2026-10-23 investigation (Paras Healthcare ingestion, trace ``ing-42ded42dde7a41b2``)
found three separable defects behind "extraction succeeded, but ``issue.ofs``
never resolved and the official RHP was rejected":

1. **Document-class conflation.**  ``PriceBandNoticeParser._classify_document``
   accepted any document carrying four of its five semantic tokens.  Every RHP
   and final Prospectus carries all five, so a 496-page RHP was treated as a
   *Price Band Notice* -- a class whose contract is "the document announces one
   price band and one issue window".  The notice's conflict rules then rejected
   the filing for content the notice rules were never meant to govern.

2. **Historical dates as current terms.**  ``_extract_dates`` read
   ``closing date`` lines from every page of the document, so a sentence in the
   history section ("the Issue Closing Date was July 14, 2017") became a
   candidate for the *current* issue's close date, and any disagreement with the
   cover aborted extraction of the whole document.

3. **Field conflict treated as document failure.**  One contradictory field
   discarded price band, lot size and issue window together, including fields
   nothing disputed.

The corrections are general: term-page scoping, a document-date plausibility
window, an explicit historical-frame test, a prospectus title guard, a
withhold-don't-abort rule for genuine current-issue conflicts, and an RHP
document class with its own (partial) field authority.  Nothing here is
issuer-specific: no company name, CIN, date, URL or expected value from the
Paras filing appears in production code, and the tests below use synthetic
documents that exercise the *behaviour*.

Execution status: NOT RUN -- deferred to the separate regression pass.
"""

from __future__ import annotations

import pytest

from ipo_screening.extraction.official_offer_amounts import parse_official_rhp
from ipo_screening.extraction.price_band_notice import (
    PriceBandNoticeClassificationError,
    PriceBandNoticeParser,
)

FIXTURES = __import__("pathlib").Path(__file__).resolve().parents[1] / "fixtures" / "notices"


def _notice(text: str) -> object:
    return PriceBandNoticeParser().parse_from_text(text)


# ---------------------------------------------------------------------------
# 1. Current-issue dates vs historical dates
# ---------------------------------------------------------------------------

RHP_COVER = """RED HERRING PROSPECTUS
Dated: October 20, 2026
ACME HEALTHCARE LIMITED
ISSUE OPENS ON: OCTOBER 21, 2026
ISSUE CLOSES ON: OCTOBER 23, 2026
Price band of Rs 100 to Rs 110 per Equity Share
BID LOT: 135 Equity Shares
"""

RHP_HISTORY = """Our Company completed its initial public offering in 2017. The Issue
Closing Date was July 14, 2017 and the Equity Shares of our Company were listed on
the Stock Exchanges.
"""


def test_historical_issue_date_is_not_the_current_close_date():
    """A historical "closing date" sentence cannot become the current close date."""
    parser = PriceBandNoticeParser()
    pages = [(1, RHP_COVER), (420, RHP_HISTORY)]
    open_field, close_field, findings = parser._extract_dates(pages)
    assert open_field is not None and open_field.value == "2026-10-21"
    assert close_field is not None and close_field.value == "2026-10-23"
    assert "HISTORICAL_DATES_EXCLUDED" in {finding.code for finding in findings}
    excluded = parser._last_excluded_dates
    assert any(item["value"] == "2017-07-14" for item in excluded)
    assert all(item["page"] == 420 for item in excluded)


NOTICE_2017 = """PRICE BAND NOTICE
Dated: July 10, 2017
ACME HEALTHCARE LIMITED
ISSUE OPENS ON: JULY 12, 2017
ISSUE CLOSES ON: JULY 14, 2017
Price band of Rs 100 to Rs 110 per Equity Share
BID LOT: 135 Equity Shares
"""


def test_historical_date_is_excluded_inside_the_document_date_window():
    """Wording, not distance from the document date, carries history."""
    parser = PriceBandNoticeParser()
    pages = [(1, NOTICE_2017), (20, "The previous Issue Closing Date was July 12, 2017.")]
    open_field, close_field, findings = parser._extract_dates(pages)
    assert open_field is not None and open_field.value == "2017-07-12"
    assert close_field is not None and close_field.value == "2017-07-14"
    # The historical sentence is excluded but the current window is not, even
    # though the two dates are two days apart.
    excluded = parser._last_excluded_dates
    assert [item["value"] for item in excluded] == ["2017-07-12"]
    assert "HISTORICAL_DATES_EXCLUDED" in {finding.code for finding in findings}


def test_two_current_issue_close_dates_genuinely_conflict_and_are_withheld():
    """Two credible current-issue candidates stay unresolved -- never newest-wins."""
    parser = PriceBandNoticeParser()
    cover = RHP_COVER + "BID/OFFER CLOSES ON: OCTOBER 27, 2026\n"
    open_field, close_field, findings = parser._extract_dates([(1, cover)])
    assert open_field is not None and open_field.value == "2026-10-21"
    assert close_field is None
    assert "CONFLICTING_CLOSE_DATES" in {finding.code for finding in findings}


def test_unlabelled_history_deep_in_a_filing_yields_no_candidates():
    """Narrative history is not read as an issue window; the cover still is."""
    parser = PriceBandNoticeParser()
    deep = (
        "Statement of previous issues. A previous public issue opened in April "
        "2017 and closed on April 05, 2017."
    )
    open_field, close_field, _ = parser._extract_dates([(1, RHP_COVER), (300, deep)])
    assert open_field.value == "2026-10-21"
    assert close_field.value == "2026-10-23"
    assert parser._last_excluded_dates == []


def test_a_historical_date_is_reported_once_per_page():
    parser = PriceBandNoticeParser()
    parser._extract_dates([(1, RHP_COVER), (420, RHP_HISTORY)])
    values = [(item["field"], item["value"], item["page"]) for item in parser._last_excluded_dates]
    assert values == [("close_date", "2017-07-14", 420)]


# ---------------------------------------------------------------------------
# 2. Document classification: RHP is not a Price Band Notice
# ---------------------------------------------------------------------------


def test_rhp_is_not_classified_as_a_price_band_notice():
    parser = PriceBandNoticeParser()
    pages = [(1, RHP_COVER), (2, "Price band, floor price, cap price, bid lot and equity shares.")]
    is_notice, reason = parser._classify_document("\n".join(t for _, t in pages), pages)
    assert is_notice is False
    assert "prospectus" in reason.lower()


def test_rhp_is_rejected_by_the_notice_parser_for_its_document_class():
    """The rejection names the class, not a date conflict or a missing marker."""
    with pytest.raises(PriceBandNoticeClassificationError) as excinfo:
        _notice(RHP_COVER)
    message = str(excinfo.value)
    assert "does not match Price Band Notice criteria" in message
    assert "prospectus" in message.lower()


def test_short_untitled_notice_still_uses_token_evidence():
    """The length rule must not disable the token path for real short notices."""
    parser = PriceBandNoticeParser()
    text = (
        "Price Band: Rs 100 to Rs 110 per Equity Share. Cap Price Rs 110. "
        "Floor Price Rs 100. Bid Lot 135 Equity Shares."
    )
    is_notice, _ = parser._classify_document(text, [(1, text)])
    assert is_notice is True


def test_long_document_without_a_notice_title_is_not_a_notice():
    """A long filing using the vocabulary is still not a notice."""
    parser = PriceBandNoticeParser()
    body = "Price band, floor price, cap price, bid lot and equity shares."
    pages = [(number, body) for number in range(1, 41)]
    is_notice, reason = parser._classify_document("\n".join(t for _, t in pages), pages)
    assert is_notice is False
    assert "not a Price Band Notice" in reason


def test_a_genuine_price_band_notice_is_still_classified():
    parser = PriceBandNoticeParser()
    text = (FIXTURES / "clean_notice.txt").read_text()
    is_notice, reason = parser._classify_document(text)
    assert is_notice is True
    assert "price" in reason.lower()


# ---------------------------------------------------------------------------
# 3. Partial field resolution: one conflict, one field
# ---------------------------------------------------------------------------


def test_one_conflicting_field_does_not_discard_the_others():
    result = PriceBandNoticeParser().parse_from_file(FIXTURES / "conflicting_notice.txt")
    assert result.price_band_low is None and result.price_band_high is None
    assert result.lot_size is not None
    assert result.open_date is not None and result.close_date is not None
    assert "price_band" in result.metadata["issue_term_errors"]


# ---------------------------------------------------------------------------
# 4. OFS: the six states stay distinct
# ---------------------------------------------------------------------------


def test_rhp_undisclosed_ofs_stays_unresolved_and_is_diagnosed():
    """``[●]`` is a placeholder, not a zero."""
    text = (
        "Red Herring Prospectus\nDated: October 20, 2026\nACME HEALTHCARE LIMITED\n"
        "CIN: U85110HR1987PLC035823\n"
        "FRESH ISSUE SIZE OFFER FOR SALE SIZE TOTAL ISSUE SIZE\n"
        "The Offer comprises a Fresh Issue aggregating up to ₹ [●] lakhs and an "
        "Offer for Sale aggregating up to ₹ [●] lakhs by the Selling Shareholder.\n"
    )
    result = parse_official_rhp(text.encode(), "https://nseindia.com/x/RHP.pdf")
    assert result.ofs_amount is None
    assert result.fresh_issue_amount is None
    diagnostics = result.metadata.get("issue_term_diagnostics", [])
    assert any(item["code"] == "SOURCE_PLACEHOLDER" and item["field"] == "ofs" for item in diagnostics)
    assert any(item["code"] == "SOURCE_PLACEHOLDER" and item["field"] == "fresh_issue" for item in diagnostics)


def test_explicit_ofs_nil_still_binds_to_zero():
    """The governed two-column cover shape still establishes an explicit NIL."""
    text = (
        "Red Herring Prospectus\nDated: October 20, 2026\nACME HEALTHCARE LIMITED\n"
        "CIN: U85110HR1987PLC035823\n"
        "FRESH ISSUE SIZE OFFER FOR SALE SIZE TOTAL ISSUE SIZE\n"
        "Fresh Issue Up to\n270,000,000\nEquity Shares of face value of ₹10\n"
        "aggregating up to\n₹[●] million\nNot applicable\n"
    )
    result = parse_official_rhp(text.encode(), "https://nseindia.com/x/RHP.pdf")
    assert result.ofs_amount is not None and result.ofs_amount.value == 0.0
    assert result.ofs_amount_unit == "INR_LAKHS"


def test_positive_ofs_amount_is_read_from_issuer_specific_evidence():
    text = (
        "Red Herring Prospectus\nDated: October 20, 2026\nACME HEALTHCARE LIMITED\n"
        "CIN: U85110HR1987PLC035823\n"
        "FRESH ISSUE SIZE OFFER FOR SALE SIZE TOTAL ISSUE SIZE\n"
        "The Offer comprises an Offer for Sale aggregating up to ₹ 5,000 lakhs by "
        "the Selling Shareholders and a Fresh Issue aggregating up to ₹ 10,000 lakhs.\n"
    )
    result = parse_official_rhp(text.encode(), "https://nseindia.com/x/RHP.pdf")
    assert result.ofs_amount is not None and result.ofs_amount.value == 5000.0
    assert result.ofs_amount_unit == "INR_LAKHS"
    assert result.ofs_amount.page == 1
    assert result.ofs_amount.quote


# ---------------------------------------------------------------------------
# 5. RHP class boundaries and identity
# ---------------------------------------------------------------------------


def test_general_information_document_is_not_an_rhp():
    """A GID is a format guide, never issuer terms."""
    text = (
        "GENERAL INFORMATION DOCUMENT\nRed Herring Prospectus\nDated: October 20, 2026\n"
        "ACME HEALTHCARE LIMITED\nCIN: U85110HR1987PLC035823\n"
    )
    with pytest.raises(ValueError):
        parse_official_rhp(text.encode(), "https://nseindia.com/x/GID.pdf")


def test_draft_red_herring_prospectus_is_not_promoted():
    text = (
        "Draft Red Herring Prospectus\nDated: October 20, 2026\nACME HEALTHCARE LIMITED\n"
        "CIN: U85110HR1987PLC035823\n"
    )
    with pytest.raises(ValueError):
        parse_official_rhp(text.encode(), "https://nseindia.com/x/DRHP.pdf")


def test_rhp_without_identity_is_not_accepted():
    with pytest.raises(ValueError):
        parse_official_rhp(
            b"Red Herring Prospectus Dated: October 20, 2026\nAn unnamed issuer.\n",
            "https://nseindia.com/x/RHP.pdf",
        )


def test_rhp_result_keeps_its_own_document_class_and_provenance():
    text = (
        "Red Herring Prospectus\nDated: October 20, 2026\nACME HEALTHCARE LIMITED\n"
        "CIN: U85110HR1987PLC035823\n"
        "The Offer comprises a Fresh Issue aggregating up to ₹ 10,000 lakhs.\n"
    )
    result = parse_official_rhp(text.encode(), "https://nseindia.com/x/RHP.pdf")
    assert result.document_class == "OFFICIAL_RHP_TERMS"
    assert result.source_ref.source_id.startswith("SRC-OFFICIAL-RHP-")
    assert result.company_name == "ACME HEALTHCARE LIMITED"
    assert result.cin == "U85110HR1987PLC035823"
    assert result.metadata["document_role_basis"]
    # Identity comes from the document, so an issuer mismatch is detectable
    # upstream; the parser never adopts the requested issuer's name.
    assert "PARAS" not in result.company_name.upper()


def test_rhp_missing_a_field_leaves_it_unknown_not_defaulted():
    """An RHP that states no price band yields None for it and still parses."""
    text = (
        "Red Herring Prospectus\nDated: October 20, 2026\nACME HEALTHCARE LIMITED\n"
        "CIN: U85110HR1987PLC035823\n"
        "ISSUE CLOSES ON: OCTOBER 23, 2026\n"
    )
    result = parse_official_rhp(text.encode(), "https://nseindia.com/x/RHP.pdf")
    assert result.price_band_low is None and result.price_band_high is None
    assert result.lot_size is None
    assert result.close_date is not None and result.close_date.value == "2026-10-23"


def test_rhp_cover_terms_are_extracted_field_by_field():
    """The RHP path publishes the band, lot and window the cover states."""
    text = (
        "Red Herring Prospectus\nDated: October 20, 2026\nACME HEALTHCARE LIMITED\n"
        "CIN: U85110HR1987PLC035823\n"
        "ISSUE OPENS ON: OCTOBER 21, 2026\nISSUE CLOSES ON: OCTOBER 23, 2026\n"
        "Price band of Rs 100 to Rs 110 per Equity Share\n"
        "BID LOT: 135 Equity Shares\n"
        "The Offer comprises a Fresh Issue aggregating up to ₹ 10,000 lakhs.\n"
    )
    result = parse_official_rhp(text.encode(), "https://nseindia.com/x/RHP.pdf")
    assert (result.price_band_low.value, result.price_band_high.value) == (100.0, 110.0)
    assert result.lot_size.value == 135
    assert (result.open_date.value, result.close_date.value) == ("2026-10-21", "2026-10-23")
    assert result.fresh_issue_amount.value == 10000.0
    # Provenance travels with each field, not with the document as a whole.
    assert result.price_band_low.page == 1 and result.price_band_low.quote
    assert result.lot_size.page == 1 and result.close_date.quote
    assert result.price_band_low.extraction_method == "DETERMINISTIC_PDF"
    assert result.price_band_low.verification == "VERIFIED"
    assert result.metadata["issue_term_errors"] == {}


def test_historical_date_inside_the_rhp_path_is_excluded():
    text = (
        "Red Herring Prospectus\nDated: October 20, 2026\nACME HEALTHCARE LIMITED\n"
        "CIN: U85110HR1987PLC035823\n"
        "ISSUE CLOSES ON: OCTOBER 23, 2026\n"
        + RHP_HISTORY
    )
    result = parse_official_rhp(text.encode(), "https://nseindia.com/x/RHP.pdf")
    assert result.close_date is not None and result.close_date.value == "2026-10-23"
    assert any(
        item["value"] == "2017-07-14"
        for item in (result.metadata.get("historical_dates_excluded") or [])
    )
