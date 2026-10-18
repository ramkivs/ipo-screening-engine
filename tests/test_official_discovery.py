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
