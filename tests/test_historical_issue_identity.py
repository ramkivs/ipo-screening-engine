"""Issue identity binding for closed exchange listings.

The engine searches the exchange's **live** public-issues listing.  A
closed issue leaves that listing, which is why a closed record is not a
discovery source by default.  Admitting one requires binding it to the
exact offering, and this module tests that binding:

* a closed record is eligible only when its own issue identity (exact
  issuer, exact bid window, exchange issue number, internally consistent
  identifiers) is bound to the offering under examination;
* a previous offering by the same issuer is never eligible, however exact
  the name match;
* conflicting or missing identifiers withhold the record rather than pick
  a winner;
* the closed-issue listing is off unless configured, and can never
  substantiate a NOT_FOUND / UNPUBLISHED conclusion.

All transport is synthetic.  Nothing here asserts live retrieval.
"""

from __future__ import annotations

import pytest

from ipo_screening.issue_identity import (
    BOUND,
    IDENTITY_CONFLICT,
    IDENTITY_INCOMPLETE,
    IDENTITY_UNBOUND,
    STALE_OR_DIFFERENT_ISSUE,
    IssueIdentity,
    check_issue_identity,
)
from ipo_screening.issue_terms import IssueTermsResolver, OfficialDiscoveryProvider
from ipo_screening.official_issue_sources import (
    BSE_HISTORICAL_LISTING,
    BSE_LISTING,
    bse_historical_issue_records,
)

ISSUER = "Paras Healthcare Limited"
OTHER = "Jio Platforms Limited"

CURRENT = IssueIdentity(open_date="2026-10-21", close_date="2026-10-23")
PREVIOUS = IssueIdentity(open_date="2024-08-01", close_date="2024-08-05")

DETAIL_URL = ("https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4895&type=IPO"
              "&idtype=2&status=H&IPONo=8048&startdt=21/10/2026")


def historical_row(name=ISSUER, scrip="4895", ipono="8048", start="21/10/2026", end="23-10-2026",
                   band="660.00 - 693.00", status="H", link_type="IPO", with_link=True,
                   link_start=None):
    if with_link:
        href = (f"https://www.bseindia.com/markets/publicIssues/DisplayIPO?id={scrip}"
                f"&type={link_type}&idtype=2&status={status}&IPONo={ipono}"
                f"&startdt={link_start or start}")
        name_cell = f'<a href="{href.replace("&", "&amp;")}">{name}</a>'
    else:
        name_cell = name
    return (f"<tr><td>{name_cell}</td><td>MainBoard</td><td>{start.replace('/', '-')}</td>"
            f"<td>{end}</td><td>{band}</td><td>1.00</td><td>Book Building</td></tr>")


def historical_listing(*rows, header=True):
    head = ("<tr><th>Security Name</th><th>Exchange Platform</th><th>Start Date</th>"
            "<th>End Date</th><th>Offer Price</th><th>Face Value</th><th>Type of Issue</th></tr>"
            if header else "")
    return f"<html><body><table>{head}{''.join(rows)}</table></body></html>".encode()


DETAIL_PAGE = """<html><body><table>
<tr><td><b>Paras Healthcare Limited</b></td></tr>
<tr><td>Security Type</td><td>Equity</td></tr>
<tr><td>Symbol</td><td>PARASHLTH</td></tr>
<tr><td>Issue Period</td><td>21 Oct 2026 to 23 Oct 2026</td></tr>
<tr><td>Price Band</td><td>660.00-693.00</td></tr>
<tr><td>Market Lot</td><td>21</td></tr>
<tr><td>Minimum Bid Quantity</td><td>21</td></tr>
<tr><td>Maximum Bid Quantity for Non-Institutional Investors</td><td>54,92,403</td></tr>
</table></body></html>""".encode()

LIVE_WITHOUT_ISSUER = (b"<html><body><table>"
                       b"<tr><th>Security Name</th><th>Start Date</th><th>End Date</th>"
                       b"<th>Issue Status</th></tr>"
                       b"<tr><td>Another Company Limited</td><td>21-10-2026</td>"
                       b"<td>23-10-2026</td><td>Forthcoming</td></tr>"
                       b"</table></body></html>")


def fetcher(pages):
    calls = []

    def _fetch(url, *_args, **_kwargs):
        calls.append(url)
        if url not in pages:
            raise AssertionError(f"unexpected fetch: {url}")
        value = pages[url]
        if isinstance(value, Exception):
            raise value
        return value
    _fetch.calls = calls
    return _fetch


def provider_for(pages, **kwargs):
    return OfficialDiscoveryProvider(
        fetcher=fetcher(pages),
        listing_urls=kwargs.pop("listing_urls", [BSE_LISTING]),
        **kwargs,
    )


# ----------------------------------------------------------------------
# The identity model itself
# ----------------------------------------------------------------------
def test_bound_only_when_the_window_matches():
    observed = IssueIdentity("2026-10-21", "2026-10-23", "8048", "PARASHLTH")
    verdict = check_issue_identity(observed, CURRENT)
    assert verdict.eligible is True
    assert verdict.state == BOUND
    assert "2026-10-21..2026-10-23" in verdict.reasons[0]


def test_no_expected_identity_can_never_bind():
    observed = IssueIdentity("2026-10-21", "2026-10-23", "8048")
    for expected in (None, IssueIdentity(), IssueIdentity(open_date="2026-10-21")):
        verdict = check_issue_identity(observed, expected)
        assert verdict.eligible is False
        assert verdict.state == IDENTITY_UNBOUND


def test_a_different_window_is_a_different_offering():
    observed = IssueIdentity("2024-08-01", "2024-08-05", "7000")
    verdict = check_issue_identity(observed, CURRENT)
    assert verdict.eligible is False
    assert verdict.state == STALE_OR_DIFFERENT_ISSUE


def test_a_record_without_both_dates_is_incomplete():
    verdict = check_issue_identity(IssueIdentity(open_date="2026-10-21"), CURRENT)
    assert verdict.eligible is False
    assert verdict.state == IDENTITY_INCOMPLETE


def test_declared_identifiers_must_agree_with_the_expectation():
    expected = IssueIdentity("2026-10-21", "2026-10-23", issue_number="9999", symbol="OTHER")
    verdict = check_issue_identity(IssueIdentity("2026-10-21", "2026-10-23", "8048", "X"), expected)
    assert verdict.eligible is False
    assert verdict.state == IDENTITY_CONFLICT
    assert len(verdict.reasons) == 2


def test_an_internally_contradictory_record_is_never_bound():
    verdict = check_issue_identity(CURRENT, CURRENT, conflicts=["row date contradicts its link"])
    assert verdict.eligible is False
    assert verdict.state == IDENTITY_CONFLICT


def test_expected_identity_is_read_from_the_canonical_issue_mapping():
    identity = IssueIdentity.from_issue_context(
        {"open_date": "2026-10-21", "close_date": "2026-10-23", "price_band_low": 660.0})
    assert identity.open_date == "2026-10-21"
    assert identity.binds_window is True
    assert IssueIdentity.from_issue_context({"open_date": None}).binds_window is False
    assert IssueIdentity.from_issue_context(None).binds_window is False


# ----------------------------------------------------------------------
# Reading a closed-issue listing
# ----------------------------------------------------------------------
def test_bound_record_carries_band_dates_and_identity_provenance():
    records, rejections = bse_historical_issue_records(
        historical_listing(historical_row()), ISSUER, CURRENT)
    assert rejections == []
    page_url, result = records[0]
    assert page_url == DETAIL_URL
    assert result.company_name == ISSUER
    assert (result.price_band_low.value, result.price_band_high.value) == (660.0, 693.0)
    assert result.price_band_high.quote == "660.00 - 693.00"
    assert (result.open_date.value, result.close_date.value) == ("2026-10-21", "2026-10-23")
    assert result.metadata["issue_identity"]["state"] == BOUND
    assert result.metadata["issue_identity"]["observed"]["issue_number"] == "8048"
    assert result.metadata["issue_status"] == "H"
    assert result.metadata["page_kind"] == "bse_historical_public_issue_listing"


def test_a_previous_offering_by_the_same_issuer_is_withheld():
    listing = historical_listing(
        historical_row(scrip="4123", ipono="6900", start="01/08/2024", end="05-08-2024",
                       band="300.00 - 320.00"))
    records, rejections = bse_historical_issue_records(listing, ISSUER, CURRENT)
    assert records == []
    assert STALE_OR_DIFFERENT_ISSUE in rejections[0]
    assert "300.00 - 320.00" not in rejections[0]


def test_the_same_window_but_a_different_issue_number_is_a_conflict():
    expected = IssueIdentity("2026-10-21", "2026-10-23", issue_number="8048")
    records, rejections = bse_historical_issue_records(
        historical_listing(historical_row(ipono="9999")), ISSUER, expected)
    assert records == []
    assert IDENTITY_CONFLICT in rejections[0]


def test_a_record_without_an_issue_number_identifies_no_offering():
    records, rejections = bse_historical_issue_records(
        historical_listing(historical_row(ipono="")), ISSUER, CURRENT)
    assert records == []
    assert IDENTITY_INCOMPLETE in rejections[0]


def test_a_link_whose_start_date_contradicts_the_row_is_withheld():
    listing = historical_listing(historical_row(start="21/10/2026", end="23-10-2026",
                                                link_start="22/10/2026"))
    records, rejections = bse_historical_issue_records(listing, ISSUER, CURRENT)
    assert records == []
    assert IDENTITY_CONFLICT in rejections[0]
    assert "contradicts the listing row start date" in rejections[0]


def test_a_non_ipo_record_in_the_archive_is_withheld():
    records, rejections = bse_historical_issue_records(
        historical_listing(historical_row(link_type="RI")), ISSUER, CURRENT)
    assert records == []
    assert records == [] and rejections  # never a silent drop


def test_another_issuers_row_is_ignored_entirely():
    records, rejections = bse_historical_issue_records(
        historical_listing(historical_row(name=OTHER, scrip="4894", ipono="8047")),
        ISSUER, CURRENT)
    assert records == [] and rejections == []


def test_a_similarly_named_issuer_is_not_admitted():
    records, rejections = bse_historical_issue_records(
        historical_listing(historical_row(name="Paras Hospitals Limited")), ISSUER, CURRENT)
    assert records == [] and rejections == []


def test_an_unreadable_band_is_never_guessed():
    """A record whose price cell is not a two-sided band supplies no band.

    It is still admissible as an identity-bound record of the offering
    (the issue page remains the authority for the terms), but no value is
    invented from it.
    """
    records, rejections = bse_historical_issue_records(
        historical_listing(historical_row(band="Price on application")), ISSUER, CURRENT)
    assert len(records) == 1
    _, result = records[0]
    assert result.price_band_low is None and result.price_band_high is None
    assert result.metadata["issue_identity"]["state"] == BOUND


# ----------------------------------------------------------------------
# The provider: off by default, opt-in, identity-bound
# ----------------------------------------------------------------------
def test_the_closed_issue_listing_is_not_searched_unless_configured():
    fetch = fetcher({BSE_LISTING: LIVE_WITHOUT_ISSUER})
    provider = OfficialDiscoveryProvider(fetcher=fetch, listing_urls=[BSE_LISTING])
    provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED")
    assert BSE_HISTORICAL_LISTING not in fetch.calls
    assert provider.historical_listing_urls == []


def test_absent_from_the_live_listing_but_bound_in_the_closed_archive():
    provider = provider_for(
        {BSE_LISTING: LIVE_WITHOUT_ISSUER, BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
         DETAIL_URL: DETAIL_PAGE},
        historical_listing_urls=[BSE_HISTORICAL_LISTING])
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED",
                                      issue_context={"open_date": "2026-10-21",
                                                     "close_date": "2026-10-23"})
    assert report.outcome == "FOUND"
    assert candidate.values["price_band_low"] == 660.0
    assert candidate.values["price_band_high"] == 693.0
    assert candidate.values["lot_size"] == 21
    assert candidate.uri in (DETAIL_URL,)


def test_without_an_expected_window_the_archive_supplies_nothing():
    provider = provider_for(
        {BSE_LISTING: LIVE_WITHOUT_ISSUER, BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
         DETAIL_URL: DETAIL_PAGE},
        historical_listing_urls=[BSE_HISTORICAL_LISTING])
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED")
    assert candidate is None
    assert any(IDENTITY_UNBOUND in note for note in report.notes)


def test_a_closed_issue_archive_never_substantiates_non_publication():
    """Every live listing unreadable + a readable, empty archive is UNAVAILABLE.

    An issue that is still forthcoming cannot appear in a closed-issue
    archive, so its silence is not evidence of anything.
    """
    pages = {BSE_LISTING: OSError("connection reset by peer"),
             BSE_HISTORICAL_LISTING: historical_listing()}
    provider = provider_for(pages, listing_urls=[BSE_LISTING],
                            historical_listing_urls=[BSE_HISTORICAL_LISTING])
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED",
                                      issue_context={"open_date": "2026-10-21",
                                                     "close_date": "2026-10-23"})
    assert candidate is None
    assert report.outcome == "UNAVAILABLE"
    assert report.listing_searched is False
    historical = [a for a in report.sources if a.url == BSE_HISTORICAL_LISTING][0]
    assert historical.classification == "historical"
    assert historical.searched is False


def test_a_transport_failure_of_one_source_leaves_the_other_readable():
    pages = {BSE_LISTING: OSError("[Errno 104] Connection reset by peer"),
             BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
             DETAIL_URL: DETAIL_PAGE}
    provider = provider_for(pages, historical_listing_urls=[BSE_HISTORICAL_LISTING])
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED",
                                      issue_context={"open_date": "2026-10-21",
                                                     "close_date": "2026-10-23"})
    assert report.outcome == "FOUND"
    assert candidate.values["lot_size"] == 21
    failed = [a for a in report.sources if a.url == BSE_LISTING][0]
    assert failed.classification == "failed"
    assert any("[TRANSPORT]" in note for note in report.notes)


def test_a_transport_failure_is_reported_as_transport_not_absence():
    pages = {BSE_LISTING: OSError("TLS handshake failed"),
             BSE_HISTORICAL_LISTING: OSError("TLS handshake failed")}
    provider = provider_for(pages, historical_listing_urls=[BSE_HISTORICAL_LISTING])
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED")
    assert candidate is None
    assert report.outcome == "UNAVAILABLE"
    assert report.notes and all("[TRANSPORT]" in note for note in report.notes)


def test_closed_archive_evidence_cannot_supply_another_issuers_terms():
    provider = provider_for(
        {BSE_LISTING: LIVE_WITHOUT_ISSUER, BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
         DETAIL_URL: DETAIL_PAGE},
        historical_listing_urls=[BSE_HISTORICAL_LISTING])
    candidate, report = provider.find("Unrelated Healthcare Limited", "UNRELATED",
                                      issue_context={"open_date": "2026-10-21",
                                                     "close_date": "2026-10-23"})
    assert candidate is None
    assert report.outcome != "FOUND"


# ----------------------------------------------------------------------
# Through the resolver: identity, conflict and the required-term gate
# ----------------------------------------------------------------------
def resolver_for(pages, **kwargs):
    return IssueTermsResolver([provider_for(pages, historical_listing_urls=[BSE_HISTORICAL_LISTING],
                                           **kwargs)])


CONTEXT = {"open_date": "2026-10-21", "close_date": "2026-10-23"}
TERMS = ["price_band_low", "price_band_high", "lot_size"]


def test_resolver_resolves_all_three_terms_from_bound_closed_evidence():
    resolver = resolver_for({BSE_LISTING: LIVE_WITHOUT_ISSUER,
                             BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
                             DETAIL_URL: DETAIL_PAGE})
    outcome = resolver.resolve(company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
                               missing_fields=TERMS, issue_context=CONTEXT)
    assert outcome.status == "RESOLVED"
    assert set(outcome.resolved_fields) == set(TERMS)
    for field, expected in (("price_band_low", 660.0), ("price_band_high", 693.0),
                            ("lot_size", 21.0)):
        candidate = outcome.field_diagnostics[field]["candidates"][0]
        assert candidate["value"] == expected
        assert candidate["issuer"] == ISSUER
        assert candidate["uri"] and candidate["content_hash"]
        assert candidate["verification"] == "VERIFIED"


def test_conflicting_band_between_listing_and_issue_page_withholds_the_field():
    detail = DETAIL_PAGE.replace(b"660.00-693.00", b"700.00-735.00")
    resolver = resolver_for({BSE_LISTING: LIVE_WITHOUT_ISSUER,
                             BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
                             DETAIL_URL: detail})
    outcome = resolver.resolve(company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
                               missing_fields=TERMS, issue_context=CONTEXT)
    # The resolver reports the disagreement rather than choosing a source.
    assert outcome.status == "CONFLICT"
    assert outcome.resolved_fields == ["lot_size"]
    assert "price_band_low" in outcome.unresolved_fields
    assert "price_band_high" in outcome.unresolved_fields
    assert any("price_band_low" in conflict for conflict in outcome.conflicts)


def test_a_cap_without_a_floor_does_not_become_a_band():
    detail = DETAIL_PAGE.replace(b"<tr><td>Price Band</td><td>660.00-693.00</td></tr>",
                                 b"<tr><td>Price Band</td><td>693.00</td></tr>")
    resolver = resolver_for({BSE_LISTING: LIVE_WITHOUT_ISSUER,
                             BSE_HISTORICAL_LISTING: historical_listing(
                                 historical_row(band="NIL")),
                             DETAIL_URL: detail})
    outcome = resolver.resolve(company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
                               missing_fields=TERMS, issue_context=CONTEXT)
    assert outcome.status == "PARTIAL"
    assert outcome.resolved_fields == ["lot_size"]
    assert "price_band_low" in outcome.unresolved_fields


def test_the_market_lot_never_comes_from_a_maximum_bid_quantity():
    detail = DETAIL_PAGE.replace(b"<tr><td>Market Lot</td><td>21</td></tr>", b"")
    resolver = resolver_for({BSE_LISTING: LIVE_WITHOUT_ISSUER,
                             BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
                             DETAIL_URL: detail})
    outcome = resolver.resolve(company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
                               missing_fields=TERMS, issue_context=CONTEXT)
    assert "lot_size" in outcome.unresolved_fields
    assert outcome.resolved_fields == ["price_band_low", "price_band_high"]


def test_a_stale_record_never_reaches_field_selection():
    """The second line of defence: the resolver's own issue-window check."""
    resolver = resolver_for({BSE_LISTING: LIVE_WITHOUT_ISSUER,
                             BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
                             DETAIL_URL: DETAIL_PAGE})
    outcome = resolver.resolve(
        company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED", missing_fields=TERMS,
        issue_context={"open_date": "2026-11-01", "close_date": "2026-11-03"})
    assert outcome.resolved_fields == []
    assert outcome.status in ("UNPUBLISHED", "UNAVAILABLE")


def test_without_any_qualifying_evidence_the_gate_stays_closed():
    resolver = resolver_for({BSE_LISTING: LIVE_WITHOUT_ISSUER,
                             BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
                             DETAIL_URL: DETAIL_PAGE})
    outcome = resolver.resolve(company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
                               missing_fields=TERMS)
    assert outcome.status == "UNPUBLISHED"
    assert outcome.resolved_fields == []
    assert list(outcome.unresolved_fields) == TERMS


@pytest.mark.parametrize("missing", [["lot_size"], ["price_band_high"], ["price_band_low"]])
def test_only_the_requested_term_is_answered(missing):
    resolver = resolver_for({BSE_LISTING: LIVE_WITHOUT_ISSUER,
                             BSE_HISTORICAL_LISTING: historical_listing(historical_row()),
                             DETAIL_URL: DETAIL_PAGE})
    outcome = resolver.resolve(company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
                               missing_fields=missing, issue_context=CONTEXT)
    assert outcome.resolved_fields == missing


def test_two_issue_numbers_claiming_one_window_withhold_both():
    """An ambiguous archive supplies nothing, and says why."""
    listing = historical_listing(
        historical_row(ipono="8048", band="660.00 - 693.00"),
        historical_row(scrip="4899", ipono="8099", band="700.00 - 735.00"))
    records, rejections = bse_historical_issue_records(listing, ISSUER, CURRENT)
    assert records == []
    assert len(rejections) == 2
    assert all(IDENTITY_CONFLICT in reason for reason in rejections)
    assert all("claim the same bid window" in reason for reason in rejections)
    assert any("700.00 - 735.00" not in reason for reason in rejections)


def test_the_same_issue_listed_twice_is_one_issue_not_a_conflict():
    listing = historical_listing(historical_row(), historical_row())
    records, rejections = bse_historical_issue_records(listing, ISSUER, CURRENT)
    assert rejections == []
    assert len(records) == 1


def test_an_ambiguous_archive_cannot_resolve_any_term():
    resolver = resolver_for({BSE_LISTING: LIVE_WITHOUT_ISSUER,
                             BSE_HISTORICAL_LISTING: historical_listing(
                                 historical_row(ipono="8048"),
                                 historical_row(scrip="4899", ipono="8099")),
                             DETAIL_URL: DETAIL_PAGE})
    outcome = resolver.resolve(company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
                               missing_fields=TERMS, issue_context=CONTEXT)
    assert outcome.resolved_fields == []
    assert outcome.unresolved_fields == TERMS
