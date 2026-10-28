"""The snapshot cache must re-read HTML term pages under their own class.

``test_notice_cache_document_class.py`` pinned the A30 rule 1 defect for a
Prospectus: ``NoticeSnapshotCache.get`` re-parsed every snapshot with the
*notice* parser, so a verified document came back as "no evidence".

The same rule was still broken for the two HTML classes.  Exchange issue
pages (``EXCHANGE_ISSUE_PAGE``) and opt-in platform pages
(``INVESTMENT_PLATFORM_PAGE``) are produced by ``ExchangeIssuePageParser``,
but ``get`` had no branch for them: they fell through to the notice path,
which refuses HTML by class, and the snapshot read back as ``None``.  A
verified official exchange page -- the document the discovery path exists to
find -- silently disappeared on the second resolution whenever
``IPO_ISSUE_TERMS_CACHE_DIR`` was configured.

These cases pin the round-trip, the class recorded beside the snapshot, and
the authority boundary: a platform page is re-read as a platform page and is
never upgraded to the official exchange class, because a platform candidate
never confers authority (``issue_platforms``).  All fixtures here are
synthetic and shaped like the exchange markup; none is presented as an
actual issuer document.
"""

from __future__ import annotations

import json

from ipo_screening.extraction.exchange_issue_page import ExchangeIssuePageParser
from ipo_screening.issue_terms import NoticeCandidate, NoticeSnapshotCache

COMPANY = "Synthetic Fixture Industries Limited"
IPO_ID = "SYNTHETIC-FIXTURE-INDUSTRIES"
EXCHANGE_URL = "https://www.bseindia.com/markets/PublicIssues/IPOIssues/DisplayIPO/synthetic"
PLATFORM_URL = "https://example-platform.invalid/ipo/synthetic-fixture-industries"

#: Synthetic exchange-shaped markup.  Labelled values only, as the exchange
#: renders them; the issuer name is the short "LIMITED" line before the band.
EXCHANGE_HTML = b"""<html><body>
<table>
<tr><td>Issue Information</td></tr>
<tr><td>Synthetic Fixture Industries Limited</td></tr>
<tr><td>Price Band</td><td>Rs 100 to Rs 120 per Equity Share</td></tr>
<tr><td>Market Lot</td><td>125 Equity Shares</td></tr>
<tr><td>Issue Period</td><td>04 November 2026 to 06 November 2026</td></tr>
</table>
</body></html>"""

#: The same terms as published on a third-party investment platform.  The
#: values are identical on purpose: identical terms never make the platform
#: an official source.
PLATFORM_HTML = b"""<html><body>
<table>
<tr><td>Synthetic Fixture Industries Limited</td></tr>
<tr><td>Price Band</td><td>Rs 100 to Rs 120 per Equity Share</td></tr>
<tr><td>Market Lot</td><td>125 Equity Shares</td></tr>
<tr><td>Issue Period</td><td>04 November 2026 to 06 November 2026</td></tr>
</table>
</body></html>"""


def _candidate(raw: bytes, document_class: str, uri: str, provider: str) -> NoticeCandidate:
    """A candidate exactly as the discovery/provider path builds one."""
    result = ExchangeIssuePageParser().parse(raw, url=uri)
    assert result.company_name == COMPANY, result.company_name
    assert result.price_band_low is not None, "fixture must carry a price band"
    result.document_class = document_class
    result.metadata["document_class"] = document_class
    return NoticeCandidate(
        result=result,
        provider=provider,
        uri=uri,
        retrieved_at="2026-10-28T00:00:00+00:00",
        raw_bytes=raw,
        verified=document_class == "EXCHANGE_ISSUE_PAGE",
    )


def _exchange_candidate() -> NoticeCandidate:
    return _candidate(EXCHANGE_HTML, "EXCHANGE_ISSUE_PAGE", EXCHANGE_URL, "official-discovery")


def _platform_candidate() -> NoticeCandidate:
    return _candidate(PLATFORM_HTML, "INVESTMENT_PLATFORM_PAGE", PLATFORM_URL, "public-platform")


def test_a_cached_exchange_issue_page_round_trips(tmp_path):
    """Before the fix this returned ``(None, False)`` -- the exchange page vanished."""
    candidate = _exchange_candidate()
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)

    restored, stale = cache.get(IPO_ID)

    assert restored is not None, (
        "a cached official exchange issue page must not read back as absent"
    )
    assert stale is False
    assert restored.result.document_class == "EXCHANGE_ISSUE_PAGE"
    assert restored.verified is True
    assert restored.from_cache is True
    assert restored.uri == EXCHANGE_URL
    assert restored.provider == "official-discovery"


def test_the_exchange_page_round_trip_preserves_every_extracted_field(tmp_path):
    candidate = _exchange_candidate()
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)

    restored, _stale = cache.get(IPO_ID)
    original = candidate.result

    assert restored.result.price_band_low.value == original.price_band_low.value == 100.0
    assert restored.result.price_band_high.value == original.price_band_high.value == 120.0
    assert restored.result.lot_size.value == original.lot_size.value == 125.0
    assert restored.result.open_date.value == original.open_date.value == "2026-11-04"
    assert restored.result.close_date.value == original.close_date.value == "2026-11-06"
    # Provenance travels with the restored fields, not only with the snapshot.
    assert restored.result.price_band_low.verification == original.price_band_low.verification


def test_the_cached_exchange_class_is_recorded_beside_the_snapshot(tmp_path):
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, _exchange_candidate())

    _bin, meta_path = cache._paths(IPO_ID)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    assert meta["document_class"] == "EXCHANGE_ISSUE_PAGE"
    assert meta["verified"] is True
    assert meta["content_hash"] and len(meta["content_hash"]) == 64


def test_a_cached_platform_page_round_trips_as_a_platform_page(tmp_path):
    """A platform page must survive the cache AND keep its non-official class."""
    candidate = _platform_candidate()
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)

    restored, stale = cache.get(IPO_ID)

    assert restored is not None, "a cached platform page must not read back as absent"
    assert stale is False
    assert restored.result.document_class == "INVESTMENT_PLATFORM_PAGE"
    assert restored.result.metadata["document_class"] == "INVESTMENT_PLATFORM_PAGE"


def test_a_platform_page_is_never_upgraded_to_the_official_exchange_class(tmp_path):
    """Identical terms on a platform page do not make it an official document.

    The cache dispatches through the exchange parser, which names its own
    class; the stored class must be re-asserted or a platform snapshot would
    come back labelled as an official exchange publication.
    """
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, _platform_candidate())

    restored, _stale = cache.get(IPO_ID)

    assert restored.result.document_class != "EXCHANGE_ISSUE_PAGE"
    assert restored.verified is False, "the cache must not confer authority on read"


def test_a_snapshot_with_no_extractable_terms_reads_back_without_inventing_them(tmp_path):
    """An HTML page carrying no labelled terms yields no fields, cached or not.

    The cache restores the document, not a conclusion: a page that stated
    nothing must not gain values on the way back out.
    """
    bare = b"""<html><body><table>
    <tr><td>Synthetic Fixture Industries Limited</td></tr>
    </table></body></html>"""
    result = ExchangeIssuePageParser().parse(bare, url=EXCHANGE_URL)
    assert result.company_name == COMPANY
    result.document_class = "EXCHANGE_ISSUE_PAGE"
    result.metadata["document_class"] = "EXCHANGE_ISSUE_PAGE"
    candidate = NoticeCandidate(
        result=result,
        provider="official-discovery",
        uri=EXCHANGE_URL,
        retrieved_at="2026-10-28T00:00:00+00:00",
        raw_bytes=bare,
        verified=True,
    )

    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)
    restored, _stale = cache.get(IPO_ID)

    assert restored is not None
    assert restored.result.price_band_low is None
    assert restored.result.lot_size is None
    assert restored.result.open_date is None
