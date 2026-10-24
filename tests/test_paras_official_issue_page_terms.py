"""Official exchange issue-page terms for the Paras Healthcare filing.

The retained RHP states `issue.price_band_low`, `issue.price_band_high`
and `issue.lot_size` as `[●]` placeholders.  BSE publishes all three on
its own issue-information page for the issue (issue no. 8048, symbol
PARASHLTH, period 21-23 October 2026); the rendered page text is
retained in
`evidence/non-authoritative/paras-healthcare-issue-terms-20261024/`.

These tests use a TRANSCRIPTION of that page's labelled rows -- the
label/value pairs as displayed, in the table shape BSE serves -- because
the sandbox cannot retrieve bseindia.com directly (egress is blocked at
TLS) and `functions.fetch_page` returns rendered text, not HTML.  The
fixture is therefore official-SHAPED input, not provider bytes:

  * it proves the shared parser and the shared discovery path can read
    the published field set, and
  * it asserts the fixture still agrees with the retained capture, so
    the two cannot drift apart silently.

Nothing here resolves a term for the engine, writes a canonical record,
or creates an evaluation.  No Paras-specific code path exists: every
assertion runs the general parser and the general provider.
"""

from __future__ import annotations

import json

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction.exchange_issue_page import ExchangeIssuePageParser
from ipo_screening.issue_identity import (BOUND, STALE_OR_DIFFERENT_ISSUE,
                                          IDENTITY_UNBOUND, IssueIdentity)
from ipo_screening.issue_terms import (
    REQUIRED_ISSUE_TERMS,
    IssueTermsResolver,
    OfficialDiscoveryProvider,
)

CAPTURE_DIR = REPO_ROOT / "evidence" / "non-authoritative" / "paras-healthcare-issue-terms-20261024"
DETAIL_CAPTURE = CAPTURE_DIR / "source-captures" / "bse-displayipo-4895-chunk-0.md"

ISSUER = "Paras Healthcare Limited"
DETAIL_URL = ("https://www.bseindia.com/markets/publicIssues/DisplayIPO"
              "?id=4895&type=IPO&idtype=2&status=H&IPONo=8048&startdt=21/10/2026")

# The labelled rows of the BSE issue page, as displayed on 2026-10-24.
# (label, shown value) -- order preserved from the served page.
DETAIL_ROWS = [
    ("Book Building - Historical", ""),
    ("Security Type", "Equity"),
    ("Symbol", "PARASHLTH"),
    ("Issue Period", "21 Oct 2026 to 23 Oct 2026"),
    ("Issue Size \u2013 No. of Shares", "1,20,83,331"),
    ("Price Band", "660.00-693.00"),
    ("Price-Band Advertisement", "Click Here"),
    ("IPO Categories", "FI, IC, MF, FII, OTH, CO, IND, NOH"),
    ("UPI Categories", "IND, NOH"),
    ("Cut off Amount (Rs.)", "IND - 200000"),
    ("Face Value", "1.00"),
    ("Tick Size", "1.00"),
    ("Market Lot", "21"),
    ("Minimum Bid Quantity", "21"),
    ("Maximum Bid Quantity for Qualified Institutional Investors", "1,20,83,316"),
    ("Maximum Bid Quantity for Non-Institutional Investors", "54,92,403"),
]


def issue_page(rows=DETAIL_ROWS, heading=ISSUER) -> bytes:
    """A BSE-shaped issue table: one label cell and one value cell per row."""
    cells = "".join(f"<tr><td><b>{label}</b></td><td>{value}</td></tr>" for label, value in rows)
    return (f"<html><body><table><tr><td><b>{heading}</b></td></tr>{cells}</table>"
            f"</body></html>").encode()


def listing(**changes) -> bytes:
    """The BSE listing row that links the issuer's own issue page."""
    status = changes.get("status", "Live")
    name = changes.get("name", ISSUER)
    link = changes.get("link", DETAIL_URL)
    return (f"<html><body><table>"
            f"<tr><th>Security Name</th><th>Start Date</th><th>End Date</th>"
            f"<th>Offer Price</th><th>Issue Status</th></tr>"
            f"<tr><td><a href=\"{link}\">{name}</a></td><td>21-10-2026</td>"
            f"<td>23-10-2026</td><td>660.00 - 693.00</td><td>{status}</td></tr>"
            f"</table></body></html>").encode()


def fetcher(pages: dict):
    def _fetch(url, *_args, **_kwargs):
        if url not in pages:
            raise AssertionError(f"unexpected fetch: {url}")
        return pages[url]
    return _fetch


def discover(page: bytes, company=ISSUER):
    listing_url = OfficialDiscoveryProvider.LISTING_URLS[1]
    provider = OfficialDiscoveryProvider(
        fetcher=fetcher({listing_url: listing(), DETAIL_URL: page}),
        listing_urls=[listing_url],
    )
    return provider.find(company, "PARAS-HEALTHCARE-LIMITED")


# ----------------------------------------------------------------------
# The retained capture and the fixture must not drift apart
# ----------------------------------------------------------------------
@pytest.mark.parametrize("quoted", [
    "**Price Band** | 660.00-693.00",
    "**Market Lot** | 21",
    "**Minimum Bid Quantity** | 21",
    "**Symbol** | PARASHLTH",
    "**Issue Period** | 21 Oct 2026 to 23 Oct 2026",
])
def test_fixture_values_still_appear_in_the_retained_official_capture(quoted):
    assert quoted in DETAIL_CAPTURE.read_text(encoding="utf-8")


def test_capture_manifest_digests_match_the_retained_files():
    import hashlib
    manifest = json.loads((CAPTURE_DIR / "capture-manifest.json").read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        path = CAPTURE_DIR / artifact["file"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        assert digest == artifact["sha256"], artifact["file"]
        assert path.stat().st_size == artifact["bytes"], artifact["file"]


# ----------------------------------------------------------------------
# The shared parser reads the published field set
# ----------------------------------------------------------------------
def test_issue_page_supplies_both_band_values_and_the_market_lot():
    result = ExchangeIssuePageParser().parse(issue_page(), url=DETAIL_URL)
    assert result.company_name == ISSUER
    assert result.price_band_low.value == 660.0
    assert result.price_band_high.value == 693.0
    assert result.price_band_high.quote.strip().endswith("660.00-693.00")
    assert result.lot_size.value == 21
    assert result.lot_size.locator == "Exchange issue information - Market Lot"
    assert result.open_date.value == "2026-10-21"
    assert result.close_date.value == "2026-10-23"
    assert result.document_class == "EXCHANGE_ISSUE_PAGE"
    assert not result.metadata.get("issue_term_errors")


def test_market_lot_is_never_taken_from_a_maximum_bid_quantity():
    result = ExchangeIssuePageParser().parse(issue_page(), url=DETAIL_URL)
    assert result.lot_size.value == 21
    assert result.lot_size.value not in (12083316, 5492403)


def test_conflicting_market_lots_on_one_page_withhold_the_lot():
    rows = DETAIL_ROWS + [("Market Lot", "25")]
    result = ExchangeIssuePageParser().parse(issue_page(rows=rows), url=DETAIL_URL)
    assert result.price_band_low.value == 660.0  # the band is unaffected
    assert result.lot_size is None
    assert result.metadata["issue_term_errors"]["lot_size"] == (
        "Conflicting labelled values in one issue page")


# ----------------------------------------------------------------------
# The shared discovery path resolves all three from the official page
# ----------------------------------------------------------------------
def test_discovery_resolves_band_and_lot_from_the_official_issue_page():
    candidate, report = discover(issue_page())
    assert report.outcome == "FOUND"
    assert candidate is not None and candidate.verified is True
    assert candidate.uri == DETAIL_URL
    assert candidate.values["price_band_low"] == 660.0
    assert candidate.values["price_band_high"] == 693.0
    assert candidate.values["lot_size"] == 21


def test_resolver_reports_the_three_terms_resolved_and_dates_intact():
    listing_url = OfficialDiscoveryProvider.LISTING_URLS[1]
    resolver = IssueTermsResolver([OfficialDiscoveryProvider(
        fetcher=fetcher({listing_url: listing(), DETAIL_URL: issue_page()}),
        listing_urls=[listing_url],
    )])
    outcome = resolver.resolve(
        company_name=ISSUER,
        ipo_id="PARAS-HEALTHCARE-LIMITED",
        missing_fields=["price_band_low", "price_band_high", "lot_size"],
    )
    assert outcome.status == "RESOLVED"
    assert set(outcome.resolved_fields) == {"price_band_low", "price_band_high", "lot_size"}
    assert outcome.unresolved_fields == []
    assert outcome.notice.open_date.value == "2026-10-21"
    assert outcome.notice.close_date.value == "2026-10-23"


# ----------------------------------------------------------------------
# What must still fail
# ----------------------------------------------------------------------
def test_a_page_without_a_market_lot_leaves_the_lot_unresolved():
    rows = [row for row in DETAIL_ROWS if row[0] != "Market Lot"]
    listing_url = OfficialDiscoveryProvider.LISTING_URLS[1]
    resolver = IssueTermsResolver([OfficialDiscoveryProvider(
        fetcher=fetcher({listing_url: listing(), DETAIL_URL: issue_page(rows=rows)}),
        listing_urls=[listing_url],
    )])
    outcome = resolver.resolve(
        company_name=ISSUER,
        ipo_id="PARAS-HEALTHCARE-LIMITED",
        missing_fields=["price_band_low", "price_band_high", "lot_size"],
    )
    assert outcome.status == "PARTIAL"
    assert outcome.unresolved_fields == ["lot_size"]


def test_another_issuers_issue_page_cannot_supply_these_terms():
    candidate, report = discover(issue_page(heading="Acme Forge Limited"))
    assert candidate is None
    assert report.outcome != "FOUND"


def test_a_listing_row_for_a_similarly_named_issuer_is_not_followed():
    listing_url = OfficialDiscoveryProvider.LISTING_URLS[1]
    provider = OfficialDiscoveryProvider(
        fetcher=fetcher({listing_url: listing(name="Paras Hospitals Limited")}),
        listing_urls=[listing_url],
    )
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED")
    assert report.outcome != "FOUND"


def test_the_closed_issue_page_is_not_reachable_through_the_searched_listing():
    """The page that carries the terms is a *historical* BSE page.

    The engine searches BSE's live public-issues listing; once the issue
    closes, that listing no longer carries the row, and the historical
    listing is not among the searched listings.  Recording the official
    evidence does not change that: nothing here may slip the closed page
    into discovery, and no test asks it to.
    """
    assert not any("id=2&Type=P" in url for url in OfficialDiscoveryProvider.LISTING_URLS)


def test_no_provider_leaves_the_required_term_gate_closed():
    """With no provider at all the resolver reports UNAVAILABLE -- never a
    resolved term -- and every required term stays unresolved."""
    outcome = IssueTermsResolver([]).resolve(
        company_name=ISSUER,
        ipo_id="PARAS-HEALTHCARE-LIMITED",
        missing_fields=list(REQUIRED_ISSUE_TERMS),
    )
    assert outcome.status == "UNAVAILABLE"
    assert outcome.resolved_fields == []
    assert list(outcome.unresolved_fields) == list(REQUIRED_ISSUE_TERMS)


def test_a_searched_listing_without_this_issuer_leaves_the_gate_closed():
    """A searched listing that does not link the issuer yields
    UNPUBLISHED (not a resolved term): all four required terms stay
    unresolved, so final-mode evaluation remains blocked.  No ingestion
    runs and no evaluation object is created."""
    listing_url = OfficialDiscoveryProvider.LISTING_URLS[1]
    other = listing(name="Acme Forge Limited",
                    link="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=17&type=IPO")
    outcome = IssueTermsResolver([OfficialDiscoveryProvider(
        fetcher=fetcher({listing_url: other}), listing_urls=[listing_url],
    )]).resolve(
        company_name=ISSUER,
        ipo_id="PARAS-HEALTHCARE-LIMITED",
        missing_fields=list(REQUIRED_ISSUE_TERMS),
    )
    assert outcome.status == "UNPUBLISHED"
    assert outcome.resolved_fields == []
    assert list(outcome.unresolved_fields) == list(REQUIRED_ISSUE_TERMS)
    assert "price_band_low" in outcome.unresolved_fields
    assert "price_band_high" in outcome.unresolved_fields
    assert "lot_size" in outcome.unresolved_fields


# ----------------------------------------------------------------------
# Closed-issue archive: the same offering, bound by identity
# ----------------------------------------------------------------------
#: The retained historical-listing row, as served (markdown table row).
CAPTURE_LINK = ("https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4895&type=IPO"
                "&idtype=2&status=H&IPONo=8048&startdt=21/10/2026")
LISTING_CAPTURE = CAPTURE_DIR / "source-captures" / "bse-historical-listing-chunk-0-prefix.md"

CONTEXT = {"open_date": "2026-10-21", "close_date": "2026-10-23"}
TERMS = ["price_band_low", "price_band_high", "lot_size"]


def test_the_retained_listing_row_still_carries_this_issue_identity():
    text = LISTING_CAPTURE.read_text(encoding="utf-8")
    assert f"]({CAPTURE_LINK})" in text
    assert ("| [Paras Healthcare Limited](" + CAPTURE_LINK + ") | MainBoard | 21-10-2026 | "
            "23-10-2026 | 660.00 - 693.00 | 1.00 | Book Building |") in text


def closed_archive(row_link=CAPTURE_LINK, name="Paras Healthcare Limited",
                   cells=("21-10-2026", "23-10-2026", "660.00 - 693.00", "1.00", "Book Building")):
    """The retained historical-listing row, in the HTML shape BSE serves."""
    row = (f'<tr><td><a href="{row_link.replace("&", "&amp;")}">{name}</a></td>'
           + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    return ("<html><body><table><tr><th>Security Name</th><th>Exchange Platform</th>"
            "<th>Start Date</th><th>End Date</th><th>Offer Price</th><th>Face Value</th>"
            f"<th>Type of Issue</th></tr>{row}</table></body></html>").encode()


def test_the_closed_archive_row_binds_to_this_offering_and_no_other():
    from ipo_screening.official_issue_sources import bse_historical_issue_records
    bound, rejections = bse_historical_issue_records(
        closed_archive(), ISSUER, IssueIdentity("2026-10-21", "2026-10-23"))
    assert rejections == []
    page_url, result = bound[0]
    assert page_url == CAPTURE_LINK
    assert result.metadata["issue_identity"]["state"] == BOUND
    assert (result.price_band_low.value, result.price_band_high.value) == (660.0, 693.0)

    # The same row is never admitted for a different offering window.
    _, other = bse_historical_issue_records(
        closed_archive(), ISSUER, IssueIdentity("2025-02-03", "2025-02-05"))
    assert other and STALE_OR_DIFFERENT_ISSUE in other[0]


def test_the_three_terms_resolve_through_the_general_path_when_bound():
    """Live listing silent, closed archive bound, issue page authoritative."""
    from ipo_screening.issue_terms import IssueTermsResolver
    from ipo_screening.official_issue_sources import BSE_HISTORICAL_LISTING, BSE_LISTING

    live = (b"<html><body><table><tr><th>Security Name</th><th>Start Date</th>"
            b"<th>End Date</th><th>Issue Status</th></tr><tr><td>Another Company Limited</td>"
            b"<td>21-10-2026</td><td>23-10-2026</td><td>Forthcoming</td></tr></table></body></html>")
    pages = {BSE_LISTING: live, BSE_HISTORICAL_LISTING: closed_archive(),
             CAPTURE_LINK: issue_page()}

    def _fetch(url, *_a, **_k):
        return pages[url]

    provider = OfficialDiscoveryProvider(fetcher=_fetch, listing_urls=[BSE_LISTING],
                                         historical_listing_urls=[BSE_HISTORICAL_LISTING])
    outcome = IssueTermsResolver([provider]).resolve(
        company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
        missing_fields=TERMS, issue_context=CONTEXT)

    assert outcome.status == "RESOLVED"
    assert set(outcome.resolved_fields) == set(TERMS)
    values = {name: outcome.field_diagnostics[name]["candidates"][0]["value"] for name in TERMS}
    assert values == {"price_band_low": 660.0, "price_band_high": 693.0, "lot_size": 21.0}
    low = outcome.field_diagnostics["price_band_low"]["candidates"][0]
    assert low["issuer"] == ISSUER
    assert low["verification"] == "VERIFIED"
    assert low["content_hash"] and low["uri"] == CAPTURE_LINK
    # Retained provenance: the whole document class and source travel with it.
    assert low["document_class"] == "EXCHANGE_ISSUE_PAGE"
    band = outcome.enrichment_payload["price_band"]["price_band_low"]
    assert band["normalized_value"] == 660.0
    assert band["quote"] == "660.00 - 693.00"
    assert band["locator"] == "BSE historical public-issue listing - Offer Price"
    assert band["verification"] == "VERIFIED"


def test_the_bound_record_is_never_admitted_without_the_filings_window():
    from ipo_screening.issue_terms import IssueTermsResolver
    from ipo_screening.official_issue_sources import BSE_HISTORICAL_LISTING, BSE_LISTING

    pages = {BSE_HISTORICAL_LISTING: closed_archive(), CAPTURE_LINK: issue_page()}

    def _fetch(url, *_a, **_k):
        if url == BSE_LISTING:
            raise OSError("TLS/SSL connection has been closed")
        return pages[url]

    provider = OfficialDiscoveryProvider(fetcher=_fetch, listing_urls=[BSE_LISTING],
                                         historical_listing_urls=[BSE_HISTORICAL_LISTING])
    outcome = IssueTermsResolver([provider]).resolve(
        company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED", missing_fields=TERMS)
    assert outcome.status == "UNAVAILABLE"
    assert outcome.resolved_fields == []
    assert all("[TRANSPORT]" in note for note in outcome.provider_reports[0].notes
               if "retrieval failed" in note)
    assert any(IDENTITY_UNBOUND in note for note in outcome.provider_reports[0].notes)


# ----------------------------------------------------------------------
# The configured-URL path for the price-band advertisement itself
# ----------------------------------------------------------------------
#: The advertisement BSE links from this issue's page.  It is the document
#: class HttpNoticeProvider parses, and it is NOT retrievable from this
#: sandbox; the tests below use synthetic notice text for a configured URL,
#: which is what the provider will read once the bytes are reachable.
BSE_PRICE_BAND_URL = ("https://listing.bseindia.com/Download/8888888/PreAnchor/"
                      "PBA_20261015184043.pdf")

PARAS_NOTICE = b"""PRICE BAND ADVERTISEMENT
INITIAL PUBLIC OFFERING OF PARAS HEALTHCARE LIMITED
NOTICE TO INVESTORS
The Floor Price is Rs 660 per Equity Share and the Cap Price is Rs 693 per Equity Share.
The Price Band is Rs 660 to Rs 693 per Equity Share.
Bids can be made for a minimum of 21 Equity Shares and in multiples of 21 Equity Shares thereafter.
"""


def test_the_advertisement_host_stays_scoped_to_discovery():
    """The archive host is reachable through discovery, not as a raw URL.

    `listing.bseindia.com` is allow-listed for the issuer-matched discovery
    pathway and deliberately not for operator-configured notice/Prospectus
    URLs.  That scoping is an existing safeguard with its own test
    (`test_archive_hosts_are_scoped_to_issuer_matched_discovery_not_direct_
    prospectus_urls`); admitting a configured URL there would be a source
    policy change, so the advertisement is reached the supported way: the
    exchange's own issue page links it, and discovery follows that link.
    """
    from ipo_screening.issue_terms import (HttpNoticeProvider, OFFICIAL_HOSTS,
                                           OfficialDiscoveryProvider)
    assert "listing.bseindia.com" in OfficialDiscoveryProvider().allowed_hosts
    assert "listing.bseindia.com" not in OFFICIAL_HOSTS
    provider = HttpNoticeProvider({"PARAS-HEALTHCARE-LIMITED": BSE_PRICE_BAND_URL},
                                  fetcher=lambda _url: PARAS_NOTICE)
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED")
    assert candidate is None
    assert report.outcome == "REJECTED"
    assert "not an HTTPS official source host" in report.detail


def test_discovery_follows_the_linked_advertisement_and_reads_band_and_lot():
    """The supported route: the issue page links it, discovery follows it."""
    listing_url = OfficialDiscoveryProvider.LISTING_URLS[1]
    page = issue_page().replace(
        b"</table>",
        f'<tr><td><a href="{BSE_PRICE_BAND_URL}">Price-Band Advertisement</a></td>'
        f"<td>Click Here</td></tr></table>".encode())
    provider = OfficialDiscoveryProvider(
        fetcher=fetcher({listing_url: listing(), DETAIL_URL: page,
                         BSE_PRICE_BAND_URL: PARAS_NOTICE}),
        listing_urls=[listing_url])
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED")
    assert report.outcome == "FOUND"
    assert BSE_PRICE_BAND_URL in {c.uri for c in (candidate.components or [candidate])}
    by_uri = {c.uri: c for c in (candidate.components or [candidate])}
    advertisement = by_uri[BSE_PRICE_BAND_URL]
    assert advertisement.values["price_band_low"] == 660.0
    assert advertisement.values["price_band_high"] == 693.0
    assert advertisement.values["lot_size"] == 21


def test_a_configured_url_on_a_non_official_host_is_still_rejected():
    from ipo_screening.issue_terms import HttpNoticeProvider
    provider = HttpNoticeProvider({"PARAS-HEALTHCARE-LIMITED": "https://example.com/pba.pdf"},
                                  fetcher=lambda _url: PARAS_NOTICE)
    candidate, report = provider.find(ISSUER, "PARAS-HEALTHCARE-LIMITED")
    assert candidate is None
    assert report.outcome == "REJECTED"
    assert "not an HTTPS official source host" in report.detail


def test_the_advertisement_and_the_exchange_page_agree():
    """Two official document classes, one set of values, no conflict."""
    from ipo_screening.issue_terms import HttpNoticeProvider, IssueTermsResolver

    notice = HttpNoticeProvider({"PARAS-HEALTHCARE-LIMITED": BSE_PRICE_BAND_URL},
                                fetcher=lambda _url: PARAS_NOTICE,
                                allowed_hosts={"listing.bseindia.com"})
    listing_url = OfficialDiscoveryProvider.LISTING_URLS[1]
    page = OfficialDiscoveryProvider(
        fetcher=fetcher({listing_url: listing(), DETAIL_URL: issue_page()}),
        listing_urls=[listing_url])
    outcome = IssueTermsResolver([notice, page]).resolve(
        company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
        missing_fields=TERMS, issue_context=CONTEXT)
    assert outcome.status == "RESOLVED"
    assert outcome.conflicts == []
    assert [r.outcome for r in outcome.provider_reports] == ["FOUND", "FOUND"]
    for name, expected in (("price_band_low", 660.0), ("price_band_high", 693.0),
                           ("lot_size", 21.0)):
        uris = {c["uri"] for c in outcome.field_diagnostics[name]["candidates"]}
        assert uris == {BSE_PRICE_BAND_URL, DETAIL_URL}
        assert outcome.field_diagnostics[name]["candidates"][0]["value"] == expected
