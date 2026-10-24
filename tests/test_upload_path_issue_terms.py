"""The *upload* extraction path: cover-page issue terms and canonical units.

There are two extraction paths in this engine and they are not the same code:

* the **parser** path (``PriceBandNoticeParser`` / ``parse_official_rhp``) used
  by official discovery and by the field resolver, corrected in A30; and
* the **upload** path — ``SectionExtractor.extract_cover_and_offer`` feeding
  ``CanonicalInputBuilder`` — which every uploaded filing is ingested through.

The 2026-10-24 controlled ingestion of the Paras Healthcare RHP showed the two
paths disagreeing on real evidence: the parser read the closing date and the
disclosed Offer-for-Sale amount, the upload path read neither, and it stored a
₹5,000 million fresh issue as ``5000.0`` in an ``INR_LAKHS`` input — a tenfold
magnitude error.  These cases pin the upload path, issuer-independently.

All documents here are synthetic.  The real filing is pinned separately in
``tests/test_paras_evidence_regression.py``.
"""

from __future__ import annotations

import pytest

from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import RawExtraction, SourceDocument
from ipo_screening.extraction.sections import SectionExtractor

SOURCE = SourceDocument(
    source_id="SRC-TEST-UPLOAD-PATH",
    source_type="RHP",
    uri="https://nseindia.com/x/rhp.pdf",
)


class _Page:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _Reader:
    """Minimal stand-in for ``pypdf.PdfReader`` (the extractor only reads pages)."""

    def __init__(self, pages) -> None:
        self.pages = [_Page(text) for text in pages]


def _cover_extract(pages):
    extractor = SectionExtractor(SOURCE, _Reader(pages))
    return {e.field_path: e for e in extractor.extract_cover_and_offer()}


# ---------------------------------------------------------------------------
# Defect A — the closing date behind a footnote marker
# ---------------------------------------------------------------------------

COVER_FOOTNOTE = """RED HERRING PROSPECTUS
Dated: October 14, 2026
ACME HEALTHCARE LIMITED
BID/OFFER PERIOD
BID/OFFER OPENS ON WEDNESDAY OCTOBER 21, 2026 BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026
# UPI mandate end time and date shall be at 5:00 p.m. on the Bid/Offer Closing Date.
"""


def test_close_date_survives_a_footnote_marker_after_the_label():
    """``CLOSES ON# FRIDAY OCTOBER 23, 2026`` is a date, not a parse failure."""
    fields = _cover_extract([COVER_FOOTNOTE])
    assert fields["issue.open_date"].candidate_value == "2026-10-21"
    assert fields["issue.close_date"].candidate_value == "2026-10-23"


@pytest.mark.parametrize(
    "marker",
    ["#", "*", "†", "(1)", "(#)", "*1", ":", " - ", "#1"],
    ids=lambda m: f"marker={m!r}",
)
def test_footnote_variants_after_the_closing_label_are_tolerated(marker):
    """Comparable formatting variants resolve to the same ISO date."""
    cover = (
        "RED HERRING PROSPECTUS\nDated: October 14, 2026\nACME HEALTHCARE LIMITED\n"
        f"BID/OFFER OPENS ON WEDNESDAY OCTOBER 21, 2026\n"
        f"BID/OFFER CLOSES ON{marker} FRIDAY OCTOBER 23, 2026\n"
    )
    fields = _cover_extract([cover])
    assert fields["issue.close_date"].candidate_value == "2026-10-23"


def test_footnote_tolerance_does_not_turn_unrelated_dates_into_issue_dates():
    """A dated sentence that is not the issue window is still not the close date."""
    fields = _cover_extract(
        [
            "RED HERRING PROSPECTUS\nDated: October 14, 2026\nACME HEALTHCARE LIMITED\n"
            "Our Company was incorporated pursuant to a certificate of incorporation\n"
            "# dated December 21, 1987, issued by the Registrar of Companies.\n"
            "BID/OFFER OPENS ON WEDNESDAY OCTOBER 21, 2026\n"
            "BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026\n"
            "# Allotment shall be on or about October 27, 2026.\n"
        ]
    )
    assert fields["issue.close_date"].candidate_value == "2026-10-23"
    assert fields["issue.close_date"].candidate_value != "1987-12-21"
    assert fields["issue.close_date"].candidate_value != "2026-10-27"


def test_the_articles_definition_of_a_2017_closing_date_is_not_the_issue_close():
    """``"Closing Date" shall mean 14 July 2017`` is a definition, not the window."""
    fields = _cover_extract(
        [
            "RED HERRING PROSPECTUS\nDated: October 14, 2026\nACME HEALTHCARE LIMITED\n"
            "BID/OFFER OPENS ON WEDNESDAY OCTOBER 21, 2026\n"
            "BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026\n",
            "\u201cClosing Date\u201d shall mean 14 July 2017;",
        ]
    )
    assert fields["issue.close_date"].candidate_value == "2026-10-23"


# ---------------------------------------------------------------------------
# Defect B — the disclosed monetary Offer for Sale
# ---------------------------------------------------------------------------

OFS_COVER = """RED HERRING PROSPECTUS
Dated: October 14, 2026
ACME HEALTHCARE LIMITED
THE OFFER
FRESH ISSUE OF UP TO [\u25cf] EQUITY SHARES OF FACE VALUE OF \u20b9 1 EACH AGGREGATING UP TO \u20b9 5,000.00 MILLION
AND AN OFFER FOR SALE OF UP TO [\u25cf] EQUITY SHARES OF FACE VALUE OF \u20b9 1 EACH AGGREGATING UP TO \u20b9 9,500.00 MILLION
"""


def test_explicit_ofs_monetary_amount_is_read_independently_of_the_share_count():
    """A placeholder share count does not hide a stated Offer-for-Sale amount."""
    fields = _cover_extract([OFS_COVER])
    assert fields["issue.fresh_issue"].candidate_value == 5000.0
    assert fields["issue.fresh_issue"].raw_unit.upper().startswith("MILLION")
    assert fields["issue.ofs"].candidate_value == 9500.0
    assert fields["issue.ofs"].raw_unit.upper().startswith("MILLION")


def test_the_fresh_issue_amount_is_never_bound_to_the_offer_for_sale():
    """Reading text order would give OFS the fresh-issue figure; it must not."""
    fields = _cover_extract([OFS_COVER])
    assert fields["issue.ofs"].candidate_value != fields["issue.fresh_issue"].candidate_value


def test_seller_rows_summing_to_the_aggregate_do_not_become_the_ofs_amount():
    """Per-seller rows corroborate the total; they are not substituted for it."""
    cover = (
        "RED HERRING PROSPECTUS\nDated: October 14, 2026\nACME HEALTHCARE LIMITED\n"
        "THE OFFER\n"
        "OFFER FOR SALE OF UP TO [\u25cf] EQUITY SHARES AGGREGATING UP TO \u20b9 9,500.00 MILLION\n"
        "THE SELLING SHAREHOLDERS\n"
        "Seller One: up to \u20b9 3,000.00 MILLION\n"
        "Seller Two: up to \u20b9 6,500.00 MILLION\n"
    )
    fields = _cover_extract([cover])
    assert fields["issue.ofs"].candidate_value == 9500.0


def test_absent_ofs_monetary_disclosure_is_not_zero():
    """No OFS amount and no NIL wording leaves the field unknown."""
    fields = _cover_extract(
        [
            "RED HERRING PROSPECTUS\nDated: October 14, 2026\nACME HEALTHCARE LIMITED\n"
            "FRESH ISSUE OF UP TO [\u25cf] EQUITY SHARES AGGREGATING UP TO \u20b9 5,000.00 MILLION\n"
        ]
    )
    assert "issue.ofs" not in fields


def test_explicit_nil_under_the_existing_contract_still_binds_zero():
    """The existing NIL contract is unchanged by the monetary reader."""
    fields = _cover_extract(
        [
            "RED HERRING PROSPECTUS\nDated: October 14, 2026\nACME HEALTHCARE LIMITED\n"
            "FRESH ISSUE OF UP TO 12,000,000 EQUITY SHARES AGGREGATING UP TO \u20b9 5,000.00 MILLION\n"
            "OFFER FOR SALE: Not Applicable\n",
        ]
    )
    assert fields["issue.ofs"].candidate_value == 0.0


def test_two_different_ofs_amounts_are_withheld_not_first_won():
    """Conflicting monetary disclosures withhold the field."""
    cover = (
        "RED HERRING PROSPECTUS\nDated: October 14, 2026\nACME HEALTHCARE LIMITED\n"
        "OFFER FOR SALE OF UP TO 1,000,000 EQUITY SHARES AGGREGATING UP TO \u20b9 9,500.00 MILLION\n"
        "In another section: OFFER FOR SALE AGGREGATING UP TO \u20b9 7,500.00 MILLION\n"
    )
    fields = _cover_extract([cover])
    assert "issue.ofs" not in fields


def test_a_different_issuer_with_the_same_disclosure_structure_is_read_the_same_way():
    """The rule is structural: no issuer-specific vocabulary or figures."""
    other = (
        "RED HERRING PROSPECTUS\nDated: March 4, 2027\nNORTHWIND LOGISTICS LIMITED\n"
        "THE OFFER\n"
        "FRESH ISSUE OF UP TO [\u25cf] EQUITY SHARES OF FACE VALUE OF \u20b9 2 EACH "
        "AGGREGATING UP TO \u20b9 2,400.00 CRORE\n"
        "AND AN OFFER FOR SALE OF UP TO 1,500,000 EQUITY SHARES AGGREGATING UP TO \u20b9 1,100.00 CRORE\n"
    )
    fields = _cover_extract([other])
    assert fields["issue.fresh_issue"].candidate_value == 2400.0
    assert fields["issue.fresh_issue"].raw_unit.upper().startswith("CRORE")
    assert fields["issue.ofs"].candidate_value == 1100.0


# ---------------------------------------------------------------------------
# Defect C — canonical monetary units
# ---------------------------------------------------------------------------

def _extractions(**amounts):
    out = []
    for field, (value, unit) in amounts.items():
        out.append(
            RawExtraction(
                field_path=f"issue.{field}",
                candidate_value=value,
                raw_text=str(value),
                raw_unit=unit,
                page=1,
                locator="cover",
            )
        )
    return out


def _canonical_issue(extractions, reporting_unit):
    builder = CanonicalInputBuilder(
        SOURCE,
        extractions
        + [
            RawExtraction(
                field_path="financials.reporting_unit",
                candidate_value=reporting_unit,
                raw_text=reporting_unit,
                raw_unit=reporting_unit,
                page=1,
            )
        ],
        reference_base=None,
        allow_fixture_fallbacks=False,
    )
    issue = builder._build_issue()
    return issue


def test_million_amounts_are_converted_into_the_filings_reporting_unit():
    """₹5,000 million is 50,000 lakh: 1 million = 10 lakh."""
    issue = _canonical_issue(
        _extractions(fresh_issue=(5000.0, "MILLION"), ofs=(9500.0, "MILLION")),
        "INR_LAKHS",
    )
    assert issue["fresh_issue"] == 50000.0
    assert issue["ofs"] == 95000.0


def test_an_amount_already_in_the_reporting_unit_is_not_converted():
    """Identity conversion: lakhs stay lakhs, and no double conversion happens."""
    issue = _canonical_issue(_extractions(fresh_issue=(14500.0, "LAKHS")), "INR_LAKHS")
    assert issue["fresh_issue"] == 14500.0


def test_a_millions_reporting_unit_keeps_millions():
    """Reporting in millions: an input stated in millions is not scaled."""
    issue = _canonical_issue(
        _extractions(fresh_issue=(5000.0, "MILLIONS"), ofs=(9500.0, "MILLIONS")),
        "INR_MILLIONS",
    )
    assert issue["fresh_issue"] == 5000.0
    assert issue["ofs"] == 9500.0


def test_crore_amounts_are_converted_into_lakhs():
    """1 crore = 100 lakh."""
    issue = _canonical_issue(_extractions(ofs=(1100.0, "CRORE")), "INR_LAKHS")
    assert issue["ofs"] == 110000.0


def test_a_second_issuer_converts_the_same_way():
    """Issuer-independent: crore-stated amounts scale identically."""
    issue = _canonical_issue(
        _extractions(fresh_issue=(2400.0, "CRORES"), ofs=(1100.0, "CRORES")),
        "INR_LAKHS",
    )
    assert issue["fresh_issue"] == 240000.0
    assert issue["ofs"] == 110000.0


def test_an_unsupported_unit_fails_closed_instead_of_guessing():
    """An unconvertible unit leaves the amount unknown, never mis-scaled."""
    issue = _canonical_issue(_extractions(fresh_issue=(5000.0, "USD_MILLIONS")), "INR_LAKHS")
    assert issue["fresh_issue"] is None


def test_a_field_without_a_unit_is_left_as_extracted():
    """Historical behaviour: no unit means the value is already canonical."""
    issue = _canonical_issue(_extractions(fresh_issue=(14500.0, None)), "INR_LAKHS")
    assert issue["fresh_issue"] == 14500.0


def test_normalization_does_not_touch_unrelated_monetary_fields():
    """Only the two issue monetary terms are normalized."""
    issue = _canonical_issue(_extractions(fresh_issue=(5000.0, "MILLION")), "INR_LAKHS")
    assert set(issue) >= {"fresh_issue", "ofs", "price_band_low", "price_band_high"}
    assert issue["price_band_low"] is None
    assert issue["ofs"] is None
