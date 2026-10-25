"""The snapshot cache must re-read a document under the class it was stored as.

A30 (2026-10-23) made the price-band notice parser refuse a prospectus **by
class** -- correct in itself, but ``NoticeSnapshotCache.get`` re-parsed every
cached snapshot with the *notice* parser.  A final Prospectus that had been
retrieved, verified and cached therefore came back from the cache as "no
evidence": verified official evidence silently disappeared on the second
resolution.  The full regression suite caught it
(``test_cache_read_survives_windows_unlink_failure``).

The cache now records ``document_class`` when it stores a candidate and
dispatches to the parser for that class on read.  These cases pin the
round-trip, the recorded class, and the backward-compatible read of entries
written before the class was stored.
"""

from __future__ import annotations

import json

from ipo_screening.issue_terms import (
    HttpNoticeProvider,
    HttpProspectusProvider,
    NoticeSnapshotCache,
)

COMPANY = "Vishal Nirmiti Limited"
IPO_ID = "VISHAL-NIRMITI-LIMITED"
SEBI_URL = "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"

PROSPECTUS_TEXT = """Prospectus
Dated: October 05, 2026
100% Book Built Offer
VISHAL NIRMITI LIMITED
CORPORATE IDENTITY NUMBER: U01122MH1994PLC185445
"Price Band" Price band of a minimum price of Rs 208 per Equity Share (i.e., the Floor Price) and the
maximum price of Rs 220 per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.
"""

NOTICE_TEXT = """PRICE BAND ADVERTISEMENT
INITIAL PUBLIC OFFERING OF VISHAL NIRMITI LIMITED
NOTICE TO INVESTORS

The Floor Price is Rs 208 per Equity Share of face value of Rs 10 each and the Cap Price is Rs 220 per Equity Share of face value of Rs 10 each.
The Price Band is Rs 208 to Rs 220 per Equity Share.
Bids can be made for a minimum of 68 Equity Shares and in multiples of 68 Equity Shares thereafter.

BID/OFFER PERIOD:
BID/OFFER OPENS ON: Tuesday, October 06, 2026
BID/OFFER CLOSES ON: Thursday, October 08, 2026
"""


def _prospectus_candidate():
    provider = HttpProspectusProvider({IPO_ID: SEBI_URL}, fetcher=lambda _u: PROSPECTUS_TEXT.encode())
    candidate, report = provider.find(COMPANY, IPO_ID)
    assert report.outcome == "FOUND", report
    return candidate


def test_a_cached_prospectus_round_trips_as_a_prospectus(tmp_path):
    """Before the fix this returned ``(None, False)`` -- verified evidence lost."""
    candidate = _prospectus_candidate()
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)

    restored, stale = cache.get(IPO_ID)

    assert restored is not None, "a cached final Prospectus must not read back as absent"
    assert stale is False
    assert restored.result.is_classified_prospectus is True
    assert restored.result.document_class == "OFFICIAL_PROSPECTUS"
    assert restored.result.company_name == candidate.result.company_name
    assert restored.verified is True
    assert restored.uri == candidate.uri
    assert restored.from_cache is True


def test_the_cached_class_is_recorded_beside_the_snapshot(tmp_path):
    candidate = _prospectus_candidate()
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)

    _bin, meta_path = cache._paths(IPO_ID)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    assert meta["document_class"] == "OFFICIAL_PROSPECTUS"
    # The existing provenance fields are unchanged.
    assert meta["provider"] == "official-prospectus"
    assert meta["verified"] is True
    assert meta["content_hash"] and len(meta["content_hash"]) == 64


def test_a_cached_notice_still_round_trips_as_a_notice(tmp_path):
    """The notice path is unchanged, including its classification."""
    provider = HttpNoticeProvider({IPO_ID: SEBI_URL}, fetcher=lambda _u: NOTICE_TEXT.encode())
    candidate, report = provider.find(COMPANY, IPO_ID)
    assert report.outcome == "FOUND", report

    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)
    restored, stale = cache.get(IPO_ID)

    assert restored is not None and stale is False
    assert type(restored.result) is type(candidate.result)  # notice parser, not prospectus
    assert restored.provider == candidate.provider
    assert restored.result.price_band_low.value == 208.0
    assert restored.result.price_band_high.value == 220.0


def test_an_entry_written_before_the_class_was_recorded_is_still_read(tmp_path):
    """Backward compatibility: derive the class from the stored provider."""
    candidate = _prospectus_candidate()
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)

    _bin, meta_path = cache._paths(IPO_ID)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.pop("document_class")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    restored, _stale = cache.get(IPO_ID)
    assert restored is not None
    assert restored.result.is_classified_prospectus is True
