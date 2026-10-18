"""Generic official-source discovery (no per-issuer URL configuration).

The discovery provider searches official NSE/BSE/SEBI listing pages
for documents linked for the issuer and runs each candidate through
the existing allow-list, issuer-matching and classification pipeline.
All transport here is synthetic (listing HTML fixtures + document
fixtures via an injected fetcher); this proves discovery mechanics,
never live retrieval.
"""

from __future__ import annotations

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

LISTING_EMPTY = "<html><body><p>No matching issues.</p></body></html>"


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
        OfficialDiscoveryProvider.LISTING_URLS[2]: LISTING_WITH_PROSPECTUS.encode(),
        "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/acme-prospectus.pdf": PROSPECTUS.encode(),
    })
    provider = OfficialDiscoveryProvider(fetcher=fetcher, listing_urls=[OfficialDiscoveryProvider.LISTING_URLS[2]])
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
