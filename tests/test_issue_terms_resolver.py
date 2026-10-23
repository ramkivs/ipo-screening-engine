"""Runtime issue-terms resolver: official-source resolution of missing
IPO issue terms (price band, bid lot, OFS) before final evaluation.

Coverage distinguishes:
- RETAINED copies: the Vishal notice text retained in fixtures/notices
  is an authored parser-test fixture (commit 3cddb64), NOT a retrieved
  official disclosure. Retained copies are therefore reported as
  UNVERIFIED and never resolve canonical terms.
- MOCKED retrieval: HttpNoticeProvider with an injected fetcher — these
  tests prove verified-channel mechanics only, not live retrieval. The
  notice text served is the retained fixture text; authenticity of
  content is established only by genuine retrieval from an official
  host in production, which the sandbox cannot perform.
- SYNTHETIC conflicts/partials crafted by mutating the retained text.

Jio Platforms is exercised explicitly: no Jio filing or notice exists in
the configured sources at execution time, so the resolver must report
the terms unavailable/awaiting rather than inventing them.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from ipo_screening.issue_terms import (
    HttpNoticeProvider,
    IssueTermsResolver,
    NoticeSnapshotCache,
    RetainedNoticeProvider,
)

NOTICE_TEXT = (REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt").read_text(encoding="utf-8")
MISSING = ["price_band_low", "price_band_high", "lot_size", "ofs"]


def _notice_dir(tmp_path: Path, name: str = "notices", text: str = NOTICE_TEXT) -> Path:
    directory = tmp_path / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "price_band_notice.txt").write_text(text, encoding="utf-8")
    return directory


def _resolve(resolver: IssueTermsResolver, company="VISHAL NIRMITI LIMITED", ipo="VISHAL-NIRMITI-LIMITED"):
    return resolver.resolve(company_name=company, ipo_id=ipo, missing_fields=MISSING)


def test_retained_notice_is_reported_but_never_verified(tmp_path):
    """A retained copy may match the issuer and parse cleanly, yet its
    official provenance cannot be established from the file alone, so
    it must not resolve canonical terms."""
    resolver = IssueTermsResolver(providers=[RetainedNoticeProvider([_notice_dir(tmp_path)])])
    outcome = _resolve(resolver)
    assert outcome.status == "UNVERIFIED"
    assert outcome.notice is None
    assert outcome.verified is False
    assert outcome.resolved_fields == []
    assert any(r.outcome == "UNVERIFIED" for r in outcome.provider_reports)


def test_other_issuers_notice_is_never_borrowed(tmp_path):
    resolver = IssueTermsResolver(providers=[RetainedNoticeProvider([_notice_dir(tmp_path)])])
    outcome = _resolve(resolver, company="JIO PLATFORMS LIMITED", ipo="JIO-PLATFORMS-LIMITED")
    assert outcome.status in ("UNPUBLISHED", "UNAVAILABLE")
    assert outcome.notice is None
    assert sorted(outcome.unresolved_fields) == sorted(MISSING)


def test_conflicting_official_disclosures_are_not_arbitrarily_selected():
    """MOCKED verified channel: two official-host retrievals disagree."""
    conflicting = NOTICE_TEXT.replace("₹208", "₹300").replace("₹220", "₹330")
    providers = [
        HttpNoticeProvider(
            {"VISHAL-NIRMITI-LIMITED": "https://www.nseindia.com/notice/vishal-a"},
            fetcher=lambda url: NOTICE_TEXT.encode("utf-8"),
        ),
        HttpNoticeProvider(
            {"VISHAL-NIRMITI-LIMITED": "https://www.bseindia.com/notice/vishal-b"},
            fetcher=lambda url: conflicting.encode("utf-8"),
        ),
    ]
    outcome = _resolve(IssueTermsResolver(providers=providers))
    assert outcome.status == "CONFLICT"
    # Conflicts block only the disputed fields, not independent valid lot/dates.
    assert outcome.notice is not None
    assert "price_band_low" not in outcome.resolved_fields
    assert "price_band_high" not in outcome.resolved_fields
    assert "lot_size" in outcome.resolved_fields
    assert "price_band_low" not in outcome.enrichment_payload["price_band"]
    assert "price_band_high" not in outcome.enrichment_payload["price_band"]
    assert any("price_band_low" in c for c in outcome.conflicts)


def test_partial_notice_reports_unresolved_fields():
    """MOCKED verified channel serving a notice without the bid lot."""
    partial = "\n".join(
        line for line in NOTICE_TEXT.splitlines() if "minimum of 68" not in line
    )
    provider = HttpNoticeProvider(
        {"VISHAL-NIRMITI-LIMITED": "https://www.nseindia.com/notice/vishal-partial"},
        fetcher=lambda url: partial.encode("utf-8"),
    )
    outcome = _resolve(IssueTermsResolver(providers=[provider]))
    assert outcome.status in ("PARTIAL", "UNPUBLISHED", "UNAVAILABLE")
    if outcome.status == "PARTIAL":
        assert "lot_size" in outcome.unresolved_fields


def test_cache_reuse_and_stale_refresh_semantics(tmp_path):
    cache = NoticeSnapshotCache(tmp_path / "cache", ttl_hours=24)
    verified_provider = HttpNoticeProvider(
        {"VISHAL-NIRMITI-LIMITED": "https://www.nseindia.com/notice/vishal-cache"},
        fetcher=lambda url: NOTICE_TEXT.encode("utf-8"),
    )
    resolver = IssueTermsResolver(providers=[verified_provider], cache=cache)
    first = _resolve(resolver)
    assert first.status == "RESOLVED" and not first.from_cache

    # Fresh cache serves without providers, keeping its original identity.
    cached_only = IssueTermsResolver(providers=[], cache=cache)
    second = _resolve(cached_only)
    assert second.status == "RESOLVED" and second.from_cache

    # Age the snapshot beyond the TTL: it must not be treated as fresh.
    meta_files = list((tmp_path / "cache").glob("*.json"))
    assert meta_files
    meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
    meta["retrieved_at"] = "2020-01-01T00:00:00Z"
    meta_files[0].write_text(json.dumps(meta), encoding="utf-8")
    stale_only = IssueTermsResolver(providers=[], cache=cache)
    third = _resolve(stale_only)
    assert third.status in ("UNPUBLISHED", "UNAVAILABLE")
    assert any("stale" in r.detail for r in third.provider_reports)


def test_http_provider_with_mocked_fetcher_official_host(tmp_path):
    """MOCKED retrieval: proves provider mechanics, not live retrieval."""
    provider = HttpNoticeProvider(
        {"VISHAL-NIRMITI-LIMITED": "https://www.nseindia.com/notice/vishal-price-band"},
        fetcher=lambda url: NOTICE_TEXT.encode("utf-8"),
    )
    resolver = IssueTermsResolver(providers=[provider])
    outcome = _resolve(resolver)
    assert outcome.status == "RESOLVED"
    assert outcome.source_uri and outcome.source_uri.startswith("https://www.nseindia.com/")


def test_http_provider_rejects_non_official_host_and_handles_outage():
    unofficial = HttpNoticeProvider(
        {"VISHAL-NIRMITI-LIMITED": "https://example.com/notice"},
        fetcher=lambda url: NOTICE_TEXT.encode("utf-8"),
    )
    outcome = _resolve(IssueTermsResolver(providers=[unofficial]))
    assert outcome.status == "UNAVAILABLE"
    assert outcome.notice is None

    def _boom(url):
        raise OSError("network down")

    unavailable = HttpNoticeProvider(
        {"VISHAL-NIRMITI-LIMITED": "https://www.bseindia.com/notice/vishal"},
        fetcher=_boom,
    )
    outcome = _resolve(IssueTermsResolver(providers=[unavailable]))
    assert outcome.status == "UNAVAILABLE"
    assert outcome.notice is None


def test_jio_platforms_terms_are_not_invented(tmp_path):
    """At execution time no Jio Platforms filing or Price Band Notice is
    present in any configured source; the resolver must say so."""
    resolver = IssueTermsResolver(
        providers=[RetainedNoticeProvider([_notice_dir(tmp_path)])],
        cache=NoticeSnapshotCache(tmp_path / "jio-cache"),
    )
    outcome = _resolve(resolver, company="JIO PLATFORMS LIMITED", ipo="JIO-PLATFORMS-LIMITED")
    assert outcome.status in ("UNPUBLISHED", "UNAVAILABLE")
    assert outcome.notice is None
    assert outcome.resolved_fields == []
