"""Generic official-source discovery (no per-issuer URL configuration).

The discovery provider searches official NSE/BSE/SEBI listing pages
for documents linked for the issuer and runs each candidate through
the existing allow-list, issuer-matching and classification pipeline.
All transport here is synthetic (listing HTML fixtures + document
fixtures via an injected fetcher); this proves discovery mechanics,
never live retrieval.
"""

from __future__ import annotations

import urllib.error

import pytest

from conftest import REPO_ROOT
from ipo_screening.issue_terms import (
    HttpProspectusProvider,
    IssueTermsResolver,
    OfficialDiscoveryProvider,
)

NOTICE = """PRICE BAND ADVERTISEMENT
INITIAL PUBLIC OFFERING OF ACME FORGE LIMITED
NOTICE TO INVESTORS
The Floor Price is Rs 100 per Equity Share and the Cap Price is Rs 120 per Equity Share.
The Price Band is Rs 100 to Rs 120 per Equity Share.
Bids can be made for a minimum of 50 Equity Shares and in multiples of 50 Equity Shares thereafter.
"""

PROSPECTUS = """Prospectus
Dated: October 05, 2026
100% Book Built Offer
ACME FORGE LIMITED
CORPORATE IDENTITY NUMBER: U12345MH2020PLC123456
"Price Band" Price band of a minimum price of Rs 100 per Equity Share (i.e., the Floor Price) and the
maximum price of Rs 120 per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" 50 Equity Shares and in multiples of 50 Equity Shares thereafter.
"""

LISTING_WITH_NOTICE = """<html><body>
<a href="https://www.nseindia.com/content/ipo/acme-price-band.pdf">ACME FORGE LIMITED - Price Band Advertisement</a>
<a href="https://www.nseindia.com/content/ipo/other-issuer.pdf">OTHER ISSUER LIMITED - Prospectus</a>
</body></html>"""

LISTING_WITH_PROSPECTUS = """<html><body>
<a href="/sebi_data/attachdocs/oct-2026/acme-prospectus.pdf">ACME FORGE LIMITED Prospectus</a>
</body></html>"""

# A genuine listing of issues that does NOT contain the searched
# issuer.  The row shape is the one BSE's server-rendered classic
# listing publishes (Security Name | Exchange Platform | Start Date |
# End Date | Offer Price | Face Value | Type of Issue | Issue Status,
# with the issuer's DisplayIPO link), captured live 2026-10-18: the
# listing really was read, and the issuer really is absent from it.
LISTING_EMPTY = """<html><body><h1>Public Issues</h1>
<table><tr><th>Security Name</th><th>Exchange Platform</th><th>Start Date</th><th>End Date</th><th>Offer Price</th><th>Face Value</th><th>Type of Issue</th><th>Issue Status</th></tr>
<tr><td><a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4887&amp;type=IPO&amp;idtype=1&amp;status=L&amp;IPONo=8040&amp;startdt=15/10/2026">Tonbo Imaging India Limited</a></td><td>MainBoard</td><td>15-10-2026</td><td>19-10-2026</td><td>665.00 - 700.00</td><td>2.00</td><td>IPO</td><td>Live</td></tr>
</table>
<p>No matching issues for this search.</p></body></html>"""

# A page with no recognizable listing content at all: unusable as a
# listing, never a searched listing.
LISTING_NO_MARKERS = "<html><body><p>Welcome.</p></body></html>"


def _fetcher(mapping):
    def fetch(url):
        if url in mapping:
            return mapping[url]
        raise OSError(f"unreachable: {url}")
    return fetch


def test_discovers_price_band_notice_without_configuration():
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[0]: LISTING_WITH_NOTICE.encode(),
        "https://www.nseindia.com/content/ipo/acme-price-band.pdf": NOTICE.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher, listing_urls=[OfficialDiscoveryProvider.LISTING_URLS[0]])
    candidate, report = provider.find("Acme Forge Limited", "ACME-FORGE-LIMITED")
    assert report.outcome == "FOUND"
    assert candidate is not None and candidate.verified is True
    assert candidate.values["price_band_low"] == 100.0
    assert candidate.values["lot_size"] == 50


def test_discovers_final_prospectus_and_rejects_other_issuers_document():
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[-1]: LISTING_WITH_PROSPECTUS.encode(),
        "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/acme-prospectus.pdf": PROSPECTUS.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher, listing_urls=[OfficialDiscoveryProvider.LISTING_URLS[-1]])
    candidate, report = provider.find("Acme Forge Limited", "ACME-FORGE-LIMITED")
    assert report.outcome == "FOUND"
    assert candidate is not None
    assert getattr(candidate.result, "document_class", "") == "OFFICIAL_PROSPECTUS"


def test_unpublished_when_listings_reached_but_no_issuer_document():
    fetcher = _fetcher({u: LISTING_EMPTY.encode() for u in OfficialDiscoveryProvider.LISTING_URLS})
    provider = OfficialDiscoveryProvider(fetcher=fetcher)
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None and report.outcome == "NOT_FOUND"
    outcome = IssueTermsResolver(providers=[provider]).resolve(
        company_name="Jio Platforms Limited", ipo_id="JIO-PLATFORMS-LIMITED",
        missing_fields=["price_band_low", "price_band_high", "lot_size", "ofs"],
    )
    assert outcome.status == "UNPUBLISHED"
    assert outcome.unresolved_fields == ["price_band_low", "price_band_high", "lot_size", "ofs"]


def test_unavailable_is_not_mistaken_for_unpublished():
    def boom(url):
        raise OSError("connection reset")
    provider = OfficialDiscoveryProvider(fetcher=boom)
    candidate, report = provider.find("Acme Forge Limited", "ACME-FORGE-LIMITED")
    assert candidate is None and report.outcome == "UNAVAILABLE"
    outcome = IssueTermsResolver(providers=[provider]).resolve(
        company_name="Acme Forge Limited", ipo_id="ACME-FORGE-LIMITED",
        missing_fields=["price_band_low"],
    )
    assert outcome.status == "UNAVAILABLE"


def test_html_document_response_is_not_accepted():
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[0]: LISTING_WITH_NOTICE.encode(),
        "https://www.nseindia.com/content/ipo/acme-price-band.pdf": b"<html><body>bot check</body></html>",
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher, listing_urls=[OfficialDiscoveryProvider.LISTING_URLS[0]])
    candidate, report = provider.find("Acme Forge Limited", "ACME-FORGE-LIMITED")
    assert candidate is None
    assert report.outcome == "NOT_FOUND"  # listings reached; document unusable


@pytest.mark.slow
def test_jio_ingestion_attempts_discovery_and_fails_closed_unpublished(tmp_path):
    """Normal entry point, no per-issuer configuration: discovery is
    attempted automatically; with listings reached but no Jio document
    published, ingestion fails closed as AWAITING_ISSUE_TERMS with the
    discovery report visible -- unpublished is not a resolver defect."""
    from ipo_screening.presentation.service import PresentationConfig, PresentationService

    fetcher = _fetcher({u: LISTING_EMPTY.encode() for u in OfficialDiscoveryProvider.LISTING_URLS})
    resolver = IssueTermsResolver(providers=[OfficialDiscoveryProvider(fetcher=fetcher)])
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=resolver,
    )
    service = PresentationService(cfg)
    jio_pdf = REPO_ROOT / "evidence" / "non-authoritative" / "jio" / "U72900GJ2019PLC110816_JIO.pdf"
    with pytest.raises(Exception) as excinfo:
        service.ingest_document(file_bytes=jio_pdf.read_bytes(), filename=jio_pdf.name, mode="final")
    detail = str(excinfo.value)
    assert "AWAITING_ISSUE_TERMS" in detail


# ----------------------------------------------------------------------
# Exchange issue-information pages (BSE DisplayIPO pattern, recorded
# 2026-10-18: official exchange pages publish Price Band + Market Lot)
# ----------------------------------------------------------------------
BSE_LISTING = """<html><body>
<a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4894&type=IPO&status=F">Jio Platforms Limited</a>
<a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4895&type=IPO&status=F">Paras Healthcare Limited</a>
</body></html>"""

BSE_ISSUE_PAGE = """<html><body><table>
<tr><td>Jio Platforms Limited</td></tr>
<tr><td>Security Type</td><td>Equity</td></tr>
<tr><td>Issue Period</td><td>21 Oct 2026 to 23 Oct 2026</td></tr>
<tr><td>Issue Size - No. of Shares</td><td>27,00,00,000</td></tr>
<tr><td>Price Band</td><td>1065.00-1119.00</td></tr>
<tr><td>Market Lot</td><td>12</td></tr>
<tr><td>Minimum Bid Quantity</td><td>12</td></tr>
</table></body></html>"""

JIO_DISPLAY_URL = "https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4894&type=IPO&status=F"


def test_discovers_terms_from_exchange_issue_page():
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[1]: BSE_LISTING.encode(),
        JIO_DISPLAY_URL: BSE_ISSUE_PAGE.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher, listing_urls=[OfficialDiscoveryProvider.LISTING_URLS[1]])
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert report.outcome == "FOUND"
    assert candidate is not None and candidate.verified is True
    assert candidate.values["price_band_low"] == 1065.0
    assert candidate.values["price_band_high"] == 1119.0
    assert candidate.values["lot_size"] == 12
    assert getattr(candidate.result, "document_class", "") == "EXCHANGE_ISSUE_PAGE"


def test_exchange_page_conflict_with_notice_is_not_merged():
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[0]: LISTING_WITH_NOTICE.encode(),
        OfficialDiscoveryProvider.LISTING_URLS[1]: BSE_LISTING.encode(),
        "https://www.nseindia.com/content/ipo/acme-price-band.pdf": NOTICE.encode(),
        JIO_DISPLAY_URL: BSE_ISSUE_PAGE.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher)
    candidate, report = provider.find("Acme Forge Limited", "ACME-FORGE-LIMITED")
    # The Acme notice (100-120) must never be contaminated by the Jio
    # page: issuer matching keeps them apart entirely.
    assert candidate is not None
    assert candidate.values["price_band_low"] == 100.0


# ----------------------------------------------------------------------
# Jio service-level acceptance (normal ingestion entry point)
# ----------------------------------------------------------------------
JIO_LISTING_WITH_PROSPECTUS = """<html><body>
<a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4894&type=IPO&status=F">Jio Platforms Limited</a>
<a href="https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/jio-prospectus.pdf">Jio Platforms Limited - Prospectus</a>
</body></html>"""

# Synthetic final-Prospectus mechanics fixture carrying the terms the
# official BSE issue page publishes (1065-1119, lot 12) plus the stated
# fresh-issue amount.  It is NOT the authentic document and proves
# pipeline mechanics, not live retrieval.
JIO_PROSPECTUS_TEXT = """Prospectus
Dated: October 16, 2026
100% Book Built Offer
JIO PLATFORMS LIMITED
CORPORATE IDENTITY NUMBER: U72900GJ2019PLC110816
"Price Band" Price band of a minimum price of Rs 1065 per Equity Share (i.e., the Floor Price) and the
maximum price of Rs 1119 per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" 12 Equity Shares and in multiples of 12 Equity Shares thereafter.
Fresh Offer of 27,00,00,000 Equity Shares aggregating to Rs 30,213.00 crores.
"""

JIO_PDF = REPO_ROOT / "evidence" / "non-authoritative" / "jio" / "U72900GJ2019PLC110816_JIO.pdf"


def _jio_service(tmp_path, fetcher):
    from ipo_screening.presentation.service import PresentationConfig, PresentationService

    resolver = IssueTermsResolver(providers=[OfficialDiscoveryProvider(fetcher=fetcher)])
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=resolver,
    )
    return PresentationService(cfg)


@pytest.mark.slow
def test_jio_exchange_page_resolves_pricing_awaiting_only_fresh_amount(tmp_path):
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[1]: BSE_LISTING.encode(),
        JIO_DISPLAY_URL: BSE_ISSUE_PAGE.encode(),
    })
    service = _jio_service(tmp_path, fetcher)
    with pytest.raises(Exception) as excinfo:
        service.ingest_document(file_bytes=JIO_PDF.read_bytes(), filename=JIO_PDF.name, mode="final")
    detail = str(excinfo.value)
    # Pricing + OFS resolved automatically; only the Prospectus-stated
    # fresh-issue amount remains, named precisely.
    assert "AWAITING_ISSUE_TERMS" in detail
    assert "issue.fresh_issue" in detail
    assert "issue.price_band_low" not in detail
    assert "issue.ofs" not in detail.replace("issue.fresh_issue", "")


@pytest.mark.slow
def test_jio_evaluation_completes_when_prospectus_also_discovered(tmp_path):
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[1]: JIO_LISTING_WITH_PROSPECTUS.encode(),
        JIO_DISPLAY_URL: BSE_ISSUE_PAGE.encode(),
        "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/jio-prospectus.pdf": JIO_PROSPECTUS_TEXT.encode(),
    })
    service = _jio_service(tmp_path, fetcher)
    resp = service.ingest_document(file_bytes=JIO_PDF.read_bytes(), filename=JIO_PDF.name, mode="final")
    record = service.eval_store.read(resp.evaluation_id)
    issue = record["input_snapshot"]["input"]["issue"]
    assert issue["price_band_low"] == 1065.0
    assert issue["price_band_high"] == 1119.0
    assert issue["lot_size"] == 12
    assert issue["ofs"] == 0.0
    assert record["score"]["final_score"] is not None


# ----------------------------------------------------------------------
# Actual BSE link shapes (server-rendered IPOIssues listing, recorded
# 2026-10-18: hrefs are &amp;-encoded; the JS-shell page yields nothing)
# ----------------------------------------------------------------------
BSE_CLASSIC_LISTING = """<html><body><table>
<tr><td><a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4894&amp;type=IPO&amp;idtype=1&amp;status=F&amp;IPONo=8047&amp;startdt=21%2F10%2F2026">Jio Platforms Limited</a></td><td>MainBoard</td><td>21-10-2026</td><td>23-10-2026</td><td>1065.00 - 1119.00</td></tr>
<tr><td><a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4895&amp;type=IPO&amp;status=F">Paras Healthcare Limited</a></td><td>MainBoard</td></tr>
</table></body></html>"""

BSE_JS_SHELL = "<html><head><title>Public Issues</title></head><body><app-root></app-root><script src='main.js'></script></body></html>"


# The classic listing href decodes to this exact URL; query parameters
# (idtype, IPONo, startdt) are preserved when the link is followed.
JIO_DISPLAY_URL_FULL = (
    "https://www.bseindia.com/markets/publicIssues/DisplayIPO"
    "?id=4894&type=IPO&idtype=1&status=F&IPONo=8047&startdt=21%2F10%2F2026"
)


def test_discovers_via_classic_bse_listing_with_amp_encoded_hrefs():
    classic_url = "https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P"
    fetcher = _fetcher({
        classic_url: BSE_CLASSIC_LISTING.encode(),
        JIO_DISPLAY_URL_FULL: BSE_ISSUE_PAGE.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher, listing_urls=[classic_url])
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert report.outcome == "FOUND"
    assert candidate is not None
    assert candidate.uri == JIO_DISPLAY_URL_FULL  # &amp; decoded to &, params preserved
    assert candidate.values["price_band_low"] == 1065.0
    assert candidate.values["lot_size"] == 12


def test_js_shell_listing_is_unavailable_not_searched():
    # A JavaScript shell contains no issue rows: the listing was never
    # searched, so this is a response-validation failure (UNAVAILABLE
    # with a specific reason), never a NOT_FOUND/unpublished signal.
    fetcher = _fetcher({"https://www.bseindia.com/publicissue.html": BSE_JS_SHELL.encode()})
    provider = OfficialDiscoveryProvider(
        fetcher=fetcher, listing_urls=["https://www.bseindia.com/publicissue.html"]
    )
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None and report.outcome == "UNAVAILABLE"
    assert "shell" in report.detail


# ----------------------------------------------------------------------
# Wrong-page (homepage) responses -- the observed Windows behaviour
# (2026-10-18): a cookie-less GET of the classic BSE listing URL
# returned HTTP 200 with the BSE homepage (masthead title, ~14k chars,
# no DisplayIPO/Jio content).  HTTP 200 is not a listing.
# ----------------------------------------------------------------------
BSE_HOMEPAGE = """<html><head><title>LIVE Stock/Share Market | Indian Stock/Share Market LIVE | BSE SENSEX | BSE (formerly Bombay Stock Exchange)</title></head>
<body><nav>Public Issues | Markets | Sensex</nav>
<a href="https://www.bseindia.com/sensex/code/16">BSE SENSEX 74,729.27</a>
<p>Welcome to BSE - India's leading stock exchange group.</p>
</body></html>"""


def test_homepage_response_is_not_a_searched_listing():
    fetcher = _fetcher({u: BSE_HOMEPAGE.encode() for u in OfficialDiscoveryProvider.LISTING_URLS})
    provider = OfficialDiscoveryProvider(fetcher=fetcher)
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None
    assert report.outcome == "UNAVAILABLE"  # never NOT_FOUND/unpublished
    assert "homepage" in report.detail
    outcome = IssueTermsResolver(providers=[provider]).resolve(
        company_name="Jio Platforms Limited", ipo_id="JIO-PLATFORMS-LIMITED",
        missing_fields=["price_band_low"],
    )
    assert outcome.status == "UNAVAILABLE"


def test_homepage_on_one_listing_does_not_poison_valid_listing():
    classic_url = "https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P"
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[0]: LISTING_WITH_NOTICE.encode(),
        classic_url: BSE_HOMEPAGE.encode(),
        "https://www.nseindia.com/content/ipo/acme-price-band.pdf": NOTICE.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher)
    candidate, report = provider.find("Acme Forge Limited", "ACME-FORGE-LIMITED")
    assert report.outcome == "FOUND"
    assert candidate is not None and candidate.values["price_band_low"] == 100.0


def test_issue_page_returning_homepage_reports_wrong_page_reason():
    classic_url = "https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P"
    fetcher = _fetcher({
        classic_url: BSE_CLASSIC_LISTING.encode(),
        JIO_DISPLAY_URL_FULL: BSE_HOMEPAGE.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher, listing_urls=[classic_url])
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None
    # A valid listing WAS searched, so NOT_FOUND -- but the detail must
    # name the wrong-page failure at the issue-page stage, not imply
    # the terms are unpublished.
    assert report.outcome == "NOT_FOUND"
    assert "homepage" in report.detail


# ----------------------------------------------------------------------
# Outcome classification (Windows trace ing-eacd8815051f4222):
# shells/homepages/marker-less pages are NOT searched listings, so the
# outcome is UNAVAILABLE -- never NOT_FOUND and never UNPUBLISHED.
# ----------------------------------------------------------------------
def test_all_shell_listings_are_unavailable_never_unpublished():
    fetcher = _fetcher({u: BSE_JS_SHELL.encode() for u in OfficialDiscoveryProvider.LISTING_URLS})
    provider = OfficialDiscoveryProvider(fetcher=fetcher)
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None and report.outcome == "UNAVAILABLE"
    assert "shell" in report.detail
    outcome = IssueTermsResolver(providers=[provider]).resolve(
        company_name="Jio Platforms Limited", ipo_id="JIO-PLATFORMS-LIMITED",
        missing_fields=["price_band_low", "price_band_high", "lot_size", "ofs"],
    )
    assert outcome.status == "UNAVAILABLE"  # not UNPUBLISHED


def test_markerless_pages_are_unavailable_not_searched():
    fetcher = _fetcher({u: LISTING_NO_MARKERS.encode() for u in OfficialDiscoveryProvider.LISTING_URLS})
    provider = OfficialDiscoveryProvider(fetcher=fetcher)
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None and report.outcome == "UNAVAILABLE"
    assert "no recognizable listing content" in report.detail


def test_valid_listing_searched_no_match_is_not_found_then_unpublished():
    # The only route to UNPUBLISHED: a valid listing was actually
    # searched and no issuer-matched document exists in it.
    fetcher = _fetcher({u: LISTING_EMPTY.encode() for u in OfficialDiscoveryProvider.LISTING_URLS})
    provider = OfficialDiscoveryProvider(fetcher=fetcher)
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None and report.outcome == "NOT_FOUND"
    outcome = IssueTermsResolver(providers=[provider]).resolve(
        company_name="Jio Platforms Limited", ipo_id="JIO-PLATFORMS-LIMITED",
        missing_fields=["price_band_low"],
    )
    assert outcome.status == "UNPUBLISHED"


def test_shell_on_relevant_listing_plus_valid_unmatched_listing_keeps_notes():
    # One valid listing searched (no match) -> NOT_FOUND, but the
    # shell failure on another listing stays visible in the detail.
    classic_url = "https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P"
    mapping = {u: LISTING_NO_MARKERS.encode() for u in OfficialDiscoveryProvider.LISTING_URLS}
    mapping[OfficialDiscoveryProvider.LISTING_URLS[0]] = LISTING_EMPTY.encode()
    mapping[classic_url] = BSE_JS_SHELL.encode()
    provider = OfficialDiscoveryProvider(fetcher=_fetcher(mapping))
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None and report.outcome == "NOT_FOUND"
    assert "shell" in report.detail


# ----------------------------------------------------------------------
# The Windows acceptance failure (ingestion ing-5aa6dd92cd7640a8, run
# at 3fea259): BSE's classic listing AND publicissue.html both returned
# a JavaScript application shell, the SEBI listing failed with an
# HTTPError -- and the provider nevertheless reported NOT_FOUND, which
# the resolver mapped to UNPUBLISHED.
#
# The reason was the NSE response, which the Windows trace does not
# list as a failure: the page repeats its own path in navigation and
# canonical links, so the served HTML carries the marker
# "all-upcoming-issues" while its listing table has a header row and
# NO issue row at all (the rows are filled client-side).  Modelled on
# the live NSE page and on its archived raw response (2026-10-18).
# ----------------------------------------------------------------------
NSE_MARKER_ONLY_LISTING = """<html><head><title>IPO - Latest IPO, Upcoming IPO, Recent IPO News, IPO Issue Price, Listing Details- NSE India</title>
<link rel="canonical" href="https://www.nseindia.com/market-data/all-upcoming-issues-ipo"></head>
<body>
<nav><ul>
<li><a href="https://www.nseindia.com/market-data/all-upcoming-issues-ipo">IPO</a></li>
<li><a href="https://www.nseindia.com/market-data/new-stock-exchange-listings-today">Listings</a></li>
<li><a href="https://www.nseindia.com/resources/exchange-communication-circulars">Circulars</a></li>
</ul></nav>
<h1>Market Watch</h1>
<table><tr><th>Company Name</th><th>Security type</th><th>Issue Start Date</th><th>Issue End Date</th><th>Status</th><th>NSE Bid Details</th></tr>
<tr><th>offered/ reserved</th><th>Bids</th><th>Subscription (No. of times)</th></tr></table>
<div>Fetching...</div>
</body></html>"""


def _windows_trace_fetcher():
    """The exact response pattern of the Windows acceptance failure.

    NSE: HTTP 200 with page chrome only (no issue entry).  BSE classic
    listing and BSE publicissue.html: JavaScript application shells.
    SEBI listing: HTTPError.
    """
    def fetch(url):
        if url == OfficialDiscoveryProvider.LISTING_URLS[0]:
            return NSE_MARKER_ONLY_LISTING.encode()
        if url in (
            "https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P",
            "https://www.bseindia.com/publicissue.html",
        ):
            return BSE_JS_SHELL.encode()
        if url.startswith("https://www.sebi.gov.in/"):
            raise urllib.error.HTTPError(url, 500, "Internal Server Error", {}, None)
        raise OSError(f"unreachable: {url}")
    return fetch


def test_chrome_marker_only_response_is_not_a_searched_listing():
    """A response that merely repeats the listing page's own path (or
    any navigation/canonical marker) is page chrome, not listing
    content: without an issue entry it was never a searched listing.
    """
    assert OfficialDiscoveryProvider._classify_listing(
        NSE_MARKER_ONLY_LISTING.encode()
    ) != "ok"
    assert OfficialDiscoveryProvider._classify_listing(BSE_JS_SHELL.encode()) == "shell"
    assert OfficialDiscoveryProvider._classify_listing(BSE_HOMEPAGE.encode()) == "homepage"
    assert OfficialDiscoveryProvider._classify_listing(LISTING_NO_MARKERS.encode()) == "empty"
    # A genuine listing (issue rows, and the live BSE row shape) stays
    # a searched listing: the repair must not over-reject.
    assert OfficialDiscoveryProvider._classify_listing(LISTING_EMPTY.encode()) == "ok"
    assert OfficialDiscoveryProvider._classify_listing(BSE_CLASSIC_LISTING.encode()) == "ok"


def test_windows_trace_pattern_is_unavailable_never_not_found():
    """The exact Windows response pattern (NSE chrome-only page, both
    BSE listings as JavaScript shells, SEBI HTTPError) yields
    UNAVAILABLE at the provider and resolver layers -- never NOT_FOUND
    and never UNPUBLISHED.
    """
    provider = OfficialDiscoveryProvider(fetcher=_windows_trace_fetcher())
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert candidate is None
    assert report.outcome == "UNAVAILABLE"  # never NOT_FOUND
    assert report.listing_searched is False
    # every unusable response is named with its own reason
    assert "no issue entries" in report.detail
    assert "shell" in report.detail
    assert "HTTPError" in report.detail
    outcome = IssueTermsResolver(providers=[provider]).resolve(
        company_name="Jio Platforms Limited", ipo_id="JIO-PLATFORMS-LIMITED",
        missing_fields=["price_band_low", "price_band_high", "lot_size", "ofs"],
    )
    assert outcome.status == "UNAVAILABLE"  # not UNPUBLISHED
    assert outcome.unresolved_fields == [
        "price_band_low", "price_band_high", "lot_size", "ofs",
    ]


# ----------------------------------------------------------------------
# The genuine BSE listing shape (captured live 2026-10-18) must still
# be recognised as a searched listing and must still yield the
# issuer's terms: the repair narrows the predicate, it does not
# disable discovery.
# ----------------------------------------------------------------------
LIVE_BSE_LISTING = """<html><head><title>IPOs Listing|New Live Public Issues on BSE</title></head><body>
<table>
<tr><th>Security Name</th><th>Exchange Platform</th><th>Start Date</th><th>End Date</th><th>Offer Price</th><th>Face Value</th><th>Type of Issue</th><th>Issue Status</th></tr>
<tr><td><a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4894&amp;type=IPO&amp;idtype=1&amp;status=F&amp;IPONo=8047&amp;startdt=21%2F10%2F2026">Jio Platforms Limited</a></td><td>MainBoard</td><td>21-10-2026</td><td>23-10-2026</td><td>1065.00 - 1119.00</td><td>10.00</td><td>IPO</td><td>Forthcoming</td></tr>
<tr><td><a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4895&amp;type=IPO&amp;idtype=1&amp;status=F&amp;IPONo=8048&amp;startdt=21%2F10%2F2026">Paras Healthcare Limited</a></td><td>MainBoard</td><td>21-10-2026</td><td>23-10-2026</td><td>660.00 - 693.00</td><td>1.00</td><td>IPO</td><td>Forthcoming</td></tr>
</table></body></html>"""


def test_live_bse_listing_shape_is_still_a_searched_listing():
    fetcher = _fetcher({
        OfficialDiscoveryProvider.LISTING_URLS[1]: LIVE_BSE_LISTING.encode(),
        JIO_DISPLAY_URL_FULL: BSE_ISSUE_PAGE.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher)
    candidate, report = provider.find("Jio Platforms Limited", "JIO-PLATFORMS-LIMITED")
    assert report.outcome == "FOUND"
    assert candidate is not None and candidate.verified is True
    assert candidate.values["price_band_low"] == 1065.0
    assert candidate.values["price_band_high"] == 1119.0
    assert candidate.values["lot_size"] == 12
