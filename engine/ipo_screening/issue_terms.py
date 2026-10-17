"""Runtime resolution of missing IPO issue terms.

Provider-neutral resolver used by the upload path when an RHP/DRHP does
not disclose required issue terms (``[●]`` placeholders). It looks for an
official Price Band Notice (issuer/exchange/SEBI disclosure document)
through pluggable providers, verifies issuer identity and value sanity,
detects conflicts instead of arbitrarily choosing, and hands the parsed
notice to :class:`EnrichmentEngine` — the established assembly path that
reconciles pricing terms, derives the OFS amount from verified
dependencies (seller shares x cap price), and registers field-level
evidence provenance in the canonical input.

Semantics preserved:
- no hardcoded fixture defaults, no borrowed values from other issuers,
  no silent zero substitution;
- a field is either disclosed by a parsed source document, derived by
  the approved enrichment formula, or remains unknown;
- unpublished terms are reported as such (``AWAITING_ISSUE_TERMS`` at
  the API boundary), distinctly from provider unavailability;
- cached snapshots keep their original retrieval timestamp and are
  never presented as newly published announcements.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence
from urllib.parse import urlparse

from .extraction.price_band_notice import (
    PriceBandNoticeParser,
    PriceBandNoticeResult,
)
from .extraction.prospectus_terms import ProspectusTermsParser

PRICING_TERMS = ("price_band_low", "price_band_high", "lot_size")
REQUIRED_ISSUE_TERMS = PRICING_TERMS + ("ofs",)

# Source hierarchy: official exchange/SEBI/issuer documents retrieved
# directly outrank retained copies of the same official documents; both
# outrank anything else, which this resolver does not consult at all.
OFFICIAL_HOSTS = {
    "nseindia.com",
    "www.nseindia.com",
    "bseindia.com",
    "www.bseindia.com",
    "sebi.gov.in",
    "www.sebi.gov.in",
}


def _default_http_fetch(url: str, timeout_seconds: float) -> bytes:
    """Default retrieval for official documents.

    Exchange/SEBI document servers commonly reject bare library user
    agents; a browser-compatible header set keeps retrieval behaviour
    consistent with how the documents are published for public access.
    The host allowlist -- not the headers -- is the security boundary.
    """
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            ),
            "Accept": "application/pdf,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 (allow-listed hosts only)
        return response.read()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _norm_name(name: Optional[str]) -> str:
    return "".join(ch for ch in (name or "").upper() if ch.isalnum())


def _notice_values(result: PriceBandNoticeResult) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for field_name in PRICING_TERMS:
        field_obj = getattr(result, field_name, None)
        if field_obj is None:
            values[field_name] = None
        elif hasattr(field_obj, "normalized_value"):
            values[field_name] = field_obj.normalized_value
        else:
            values[field_name] = getattr(field_obj, "value", None)
    return values


def _values_valid(values: Mapping[str, Any]) -> Optional[str]:
    low, high, lot = (values.get(k) for k in PRICING_TERMS)
    if low is not None and (not isinstance(low, (int, float)) or low <= 0):
        return "price_band_low is not a positive number"
    if high is not None and (not isinstance(high, (int, float)) or high <= 0):
        return "price_band_high is not a positive number"
    if low is not None and high is not None and high < low:
        return "price_band_high is below price_band_low"
    if lot is not None and (not isinstance(lot, (int, float)) or int(lot) <= 0):
        return "lot_size is not a positive integer"
    return None


@dataclass
class NoticeCandidate:
    """A parsed Price Band Notice matched to an issuer.

    ``verified`` is True only when the document was retrieved from an
    allow-listed official source host (NSE/BSE/SEBI) and issuer-matched.
    Retained local copies are reported but never treated as verified
    official disclosures: their provenance cannot be established from
    the file alone.
    """

    result: PriceBandNoticeResult
    provider: str
    uri: str
    retrieved_at: str
    from_cache: bool = False
    raw_bytes: Optional[bytes] = None
    verified: bool = False

    @property
    def values(self) -> Dict[str, Any]:
        return _notice_values(self.result)


@dataclass
class ProviderReport:
    provider: str
    outcome: str  # FOUND | NOT_FOUND | UNAVAILABLE | REJECTED
    detail: str = ""


@dataclass
class ResolutionOutcome:
    status: str  # RESOLVED | PARTIAL | UNPUBLISHED | UNAVAILABLE | CONFLICT | UNVERIFIED
    notice: Optional[PriceBandNoticeResult] = None
    resolved_fields: List[str] = field(default_factory=list)
    unresolved_fields: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    provider_reports: List[ProviderReport] = field(default_factory=list)
    from_cache: bool = False
    source_uri: Optional[str] = None
    verified: bool = False
    provider: Optional[str] = None
    retrieved_at: Optional[str] = None
    # PRICE_BAND_NOTICE | OFFICIAL_PROSPECTUS -- the document class is
    # carried truthfully into reports; a Prospectus is never labelled a
    # Price Band Notice.
    document_class: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "verified": self.verified,
            "resolved_fields": list(self.resolved_fields),
            "unresolved_fields": list(self.unresolved_fields),
            "conflicts": list(self.conflicts),
            "from_cache": self.from_cache,
            "source_uri": self.source_uri,
            "provider": self.provider,
            "retrieved_at": self.retrieved_at,
            "document_class": self.document_class,
            "providers": [
                {"provider": r.provider, "outcome": r.outcome, "detail": r.detail}
                for r in self.provider_reports
            ],
        }


class RetainedNoticeProvider:
    """Parses Price Band Notice documents retained in local directories.

    These directories are the operator's snapshot store of official
    disclosures (for example exchange announcement PDFs/text retained
    with the application data). Only issuer-matching documents qualify.
    """

    name = "retained-official-notices"

    def __init__(self, directories: Sequence[str | Path]):
        self.directories = [Path(d) for d in directories]

    def find(self, company_name: str, ipo_id: str) -> tuple[Optional[NoticeCandidate], ProviderReport]:
        target = _norm_name(company_name)
        searched = 0
        for directory in self.directories:
            if not directory.is_dir():
                continue
            for path in sorted(directory.iterdir()):
                if path.suffix.lower() not in (".txt", ".md", ".pdf") or not path.is_file():
                    continue
                searched += 1
                try:
                    result = PriceBandNoticeParser().parse_from_file(path)
                except Exception:
                    continue  # not a price band notice; not evidence either way
                if _norm_name(result.company_name) != target:
                    continue  # another issuer's notice is never borrowed
                return (
                    NoticeCandidate(
                        result=result,
                        provider=self.name,
                        uri=str(path),
                        retrieved_at=_utcnow().isoformat().replace("+00:00", "Z"),
                        raw_bytes=path.read_bytes(),
                    ),
                    ProviderReport(self.name, "FOUND", f"issuer-matched notice at {path}"),
                )
        if searched:
            return None, ProviderReport(self.name, "NOT_FOUND", f"no issuer-matched notice in retained documents ({searched} parsed/searched)")
        return None, ProviderReport(self.name, "UNAVAILABLE", "no retained notice documents available to search")


class HttpNoticeProvider:
    """Retrieves a Price Band Notice from an official URL.

    Only allow-listed official hosts (NSE/BSE/SEBI by default) qualify;
    search results, snippets and non-official mirrors never do. The
    fetcher is injectable so tests can distinguish mocked retrieval from
    live retrieval; the default fetcher performs a real HTTPS GET.
    """

    name = "official-url"

    def __init__(
        self,
        urls_by_ipo: Mapping[str, str],
        fetcher: Optional[Callable[[str], bytes]] = None,
        allowed_hosts: Optional[set[str]] = None,
        timeout_seconds: float = 20.0,
    ):
        self.urls_by_ipo = dict(urls_by_ipo)
        self.allowed_hosts = allowed_hosts if allowed_hosts is not None else set(OFFICIAL_HOSTS)
        self.timeout_seconds = timeout_seconds
        self._fetcher = fetcher

    def _fetch(self, url: str) -> bytes:
        if self._fetcher is not None:
            return self._fetcher(url)
        return _default_http_fetch(url, self.timeout_seconds)

    def find(self, company_name: str, ipo_id: str) -> tuple[Optional[NoticeCandidate], ProviderReport]:
        url = self.urls_by_ipo.get(ipo_id) or self.urls_by_ipo.get(company_name)
        if not url:
            return None, ProviderReport(self.name, "UNAVAILABLE", "no official notice URL configured for this issuer")
        host = (urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts:
            return None, ProviderReport(self.name, "REJECTED", f"host {host or '?'} is not an official source host")
        try:
            raw = self._fetch(url)
        except Exception as exc:
            return None, ProviderReport(self.name, "UNAVAILABLE", f"official source retrieval failed: {exc}")
        suffix = ".pdf" if raw.startswith(b"%PDF-") else ".txt"
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                handle.write(raw)
                temp_path = Path(handle.name)
            try:
                result = PriceBandNoticeParser().parse_from_file(temp_path)
            finally:
                temp_path.unlink(missing_ok=True)
        except Exception as exc:
            return None, ProviderReport(self.name, "REJECTED", f"retrieved document is not a parseable Price Band Notice: {exc}")
        if _norm_name(result.company_name) != _norm_name(company_name):
            return None, ProviderReport(self.name, "REJECTED", "retrieved notice names a different issuer")
        return (
            NoticeCandidate(
                result=result,
                provider=self.name,
                uri=url,
                retrieved_at=_utcnow().isoformat().replace("+00:00", "Z"),
                raw_bytes=raw,
                verified=True,
            ),
            ProviderReport(self.name, "FOUND", f"notice retrieved from {url}"),
        )


class HttpProspectusProvider:
    """Retrieves a final Prospectus from an official URL (narrow pathway,
    authorized 2026-10-17).

    A Prospectus is a distinct official document class from a Price Band
    Notice: candidates carry ``SRC-PROSPECTUS-…`` identity and
    ``OFFICIAL_PROSPECTUS`` classification, and only terms the document
    explicitly establishes are extracted. The same allow-listed official
    hosts (NSE/BSE/SEBI) qualify; the host allowlist is not broadened.
    """

    name = "official-prospectus"

    def __init__(
        self,
        urls_by_ipo: Mapping[str, str],
        fetcher: Optional[Callable[[str], bytes]] = None,
        allowed_hosts: Optional[set[str]] = None,
        timeout_seconds: float = 20.0,
    ):
        self.urls_by_ipo = dict(urls_by_ipo)
        self.allowed_hosts = allowed_hosts if allowed_hosts is not None else set(OFFICIAL_HOSTS)
        self.timeout_seconds = timeout_seconds
        self._fetcher = fetcher

    def _fetch(self, url: str) -> bytes:
        if self._fetcher is not None:
            return self._fetcher(url)
        return _default_http_fetch(url, self.timeout_seconds)

    def find(self, company_name: str, ipo_id: str) -> tuple[Optional[NoticeCandidate], ProviderReport]:
        url = self.urls_by_ipo.get(ipo_id) or self.urls_by_ipo.get(company_name)
        if not url:
            return None, ProviderReport(self.name, "UNAVAILABLE", "no official prospectus URL configured for this issuer")
        host = (urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts:
            return None, ProviderReport(self.name, "REJECTED", f"host {host or '?'} is not an official source host")
        try:
            raw = self._fetch(url)
        except Exception as exc:
            return None, ProviderReport(self.name, "UNAVAILABLE", f"official source retrieval failed: {exc}")
        suffix = ".pdf" if raw.startswith(b"%PDF-") else ".txt"
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                handle.write(raw)
                temp_path = Path(handle.name)
            try:
                result = ProspectusTermsParser().parse_from_file(temp_path)
            finally:
                temp_path.unlink(missing_ok=True)
        except Exception as exc:
            return None, ProviderReport(self.name, "REJECTED", f"retrieved document is not an established final Prospectus: {exc}")
        if not result.is_classified_prospectus:
            return None, ProviderReport(self.name, "REJECTED", "document is not classified as a final Prospectus")
        if _norm_name(result.company_name) != _norm_name(company_name):
            return None, ProviderReport(self.name, "REJECTED", "retrieved prospectus names a different issuer")
        return (
            NoticeCandidate(
                result=result,
                provider=self.name,
                uri=url,
                retrieved_at=_utcnow().isoformat().replace("+00:00", "Z"),
                raw_bytes=raw,
                verified=True,
            ),
            ProviderReport(self.name, "FOUND", f"final Prospectus retrieved from {url}"),
        )


class NoticeSnapshotCache:
    """Content-addressed snapshot cache for retrieved notices.

    A fresh hit is returned with its ORIGINAL retrieval timestamp; a
    stale entry is reported as stale and never silently refreshed or
    presented as a new announcement.
    """

    def __init__(self, cache_dir: str | Path, ttl_hours: float = 168.0):
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(hours=ttl_hours)

    def _paths(self, ipo_id: str) -> tuple[Path, Path]:
        key = hashlib.sha256(ipo_id.encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"{key}.bin", self.cache_dir / f"{key}.json"

    def get(self, ipo_id: str) -> tuple[Optional[NoticeCandidate], bool]:
        """Return (candidate, is_stale). Candidate is None if absent."""
        bin_path, meta_path = self._paths(ipo_id)
        if not bin_path.is_file() or not meta_path.is_file():
            return None, False
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(meta["retrieved_at"].replace("Z", "+00:00"))
        except Exception:
            return None, False
        stale = (_utcnow() - fetched_at) > self.ttl
        suffix = ".pdf" if bin_path.read_bytes()[:5] == b"%PDF-" else ".txt"
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                handle.write(bin_path.read_bytes())
                temp_path = Path(handle.name)
            try:
                result = PriceBandNoticeParser().parse_from_file(temp_path)
            finally:
                temp_path.unlink(missing_ok=True)
        except Exception:
            return None, False
        return (
            NoticeCandidate(
                result=result,
                provider=meta.get("provider", "cache"),
                uri=meta.get("uri", ""),
                retrieved_at=meta["retrieved_at"],
                from_cache=True,
                raw_bytes=bin_path.read_bytes(),
                verified=bool(meta.get("verified", False)),
            ),
            stale,
        )

    def put(self, ipo_id: str, candidate: NoticeCandidate) -> None:
        if candidate.raw_bytes is None:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        bin_path, meta_path = self._paths(ipo_id)
        bin_path.write_bytes(candidate.raw_bytes)
        meta_path.write_text(
            json.dumps(
                {
                    "ipo_id": ipo_id,
                    "provider": candidate.provider,
                    "uri": candidate.uri,
                    "retrieved_at": candidate.retrieved_at,
                    "verified": bool(candidate.verified),
                    "content_hash": hashlib.sha256(candidate.raw_bytes).hexdigest(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )


class IssueTermsResolver:
    """Coordinates providers, caching, identity and conflict checks."""

    def __init__(
        self,
        providers: Sequence[Any] = (),
        cache: Optional[NoticeSnapshotCache] = None,
    ):
        self.providers = list(providers)
        self.cache = cache

    def resolve(self, *, company_name: str, ipo_id: str, missing_fields: Sequence[str]) -> ResolutionOutcome:
        missing = [f for f in missing_fields if f in PRICING_TERMS]
        outcome = ResolutionOutcome(status="UNPUBLISHED", unresolved_fields=list(missing_fields))

        candidates: List[NoticeCandidate] = []
        from_cache = False

        if self.cache is not None:
            cached, stale = self.cache.get(ipo_id)
            if cached is not None and not stale:
                candidates.append(cached)
                from_cache = True
                outcome.provider_reports.append(
                    ProviderReport("snapshot-cache", "FOUND", f"fresh cached snapshot originally retrieved at {cached.retrieved_at}")
                )
            elif cached is not None and stale:
                outcome.provider_reports.append(
                    ProviderReport("snapshot-cache", "UNAVAILABLE", f"cached snapshot from {cached.retrieved_at} is stale; refresh required")
                )

        if not candidates:
            for provider in self.providers:
                candidate, report = provider.find(company_name, ipo_id)
                outcome.provider_reports.append(report)
                if candidate is not None:
                    candidates.append(candidate)

        if not candidates:
            searched = any(r.outcome == "NOT_FOUND" for r in outcome.provider_reports)
            outcome.status = "UNPUBLISHED" if searched else "UNAVAILABLE"
            return outcome

        # Provenance gate: only documents retrieved from allow-listed
        # official hosts count as verified disclosures. Retained copies
        # (including any file shipped or staged locally) are reported so
        # the operator can act, but they never resolve canonical terms.
        verified_candidates = [c for c in candidates if c.verified]
        if not verified_candidates:
            outcome.status = "UNVERIFIED"
            for candidate in candidates:
                outcome.provider_reports.append(
                    ProviderReport(
                        candidate.provider,
                        "UNVERIFIED",
                        f"issuer-matched notice at {candidate.uri} is a retained copy whose "
                        "official provenance is not established; not used for evaluation",
                    )
                )
            return outcome
        candidates = verified_candidates

        # Conflict detection: never arbitrarily select between disclosures.
        conflicts: List[str] = []
        baseline = candidates[0].values
        for other in candidates[1:]:
            for field_name in PRICING_TERMS:
                left, right = baseline.get(field_name), other.values.get(field_name)
                if left is not None and right is not None and float(left) != float(right):
                    conflicts.append(f"issue.{field_name}: {left} ({candidates[0].provider}) vs {right} ({other.provider})")
        if conflicts:
            outcome.status = "CONFLICT"
            outcome.conflicts = conflicts
            return outcome

        chosen = candidates[0]
        invalid = _values_valid(chosen.values)
        if invalid:
            outcome.status = "UNAVAILABLE"
            outcome.provider_reports.append(ProviderReport(chosen.provider, "REJECTED", f"unsupported value: {invalid}"))
            return outcome

        resolved = [f for f in missing if chosen.values.get(f) is not None]
        outcome.resolved_fields = resolved
        outcome.unresolved_fields = [f for f in missing_fields if f not in resolved and f != "ofs"]
        outcome.notice = chosen.result
        outcome.document_class = getattr(chosen.result, "document_class", "PRICE_BAND_NOTICE")
        outcome.from_cache = from_cache
        outcome.source_uri = chosen.uri
        outcome.verified = True
        outcome.provider = chosen.provider
        outcome.retrieved_at = chosen.retrieved_at
        outcome.status = "RESOLVED" if len(resolved) == len(missing) else "PARTIAL"

        if (
            self.cache is not None
            and not from_cache
            and chosen.verified
            and chosen.raw_bytes is not None
            and outcome.document_class == "PRICE_BAND_NOTICE"
        ):
            # The snapshot cache re-parses with the notice parser; only
            # notice-class documents are cached.
            self.cache.put(ipo_id, chosen)
        return outcome


def build_resolver_from_env() -> IssueTermsResolver:
    """Default runtime resolver wired from environment configuration.

    - ``IPO_PRICE_BAND_NOTICE_URLS``: JSON map of ipo_id -> official URL
      (allow-listed NSE/BSE/SEBI hosts). Documents retrieved this way are
      the only verified notice source.
    - ``IPO_PROSPECTUS_URLS``: JSON map of ipo_id -> official final-
      Prospectus URL (same allow-listed hosts). A Prospectus is a
      distinct document class from a Price Band Notice and is labelled
      ``OFFICIAL_PROSPECTUS`` / ``SRC-PROSPECTUS-…``, never as a notice.
    - ``IPO_PRICE_BAND_NOTICE_DIR``: operator-retained notice directories
      (os.pathsep-separated). Retained copies are searched and reported,
      but classified UNVERIFIED and never used to resolve terms.
    - ``IPO_ISSUE_TERMS_CACHE_DIR`` / ``IPO_ISSUE_TERMS_CACHE_TTL_HOURS``.

    No notice document is shipped with the application as production
    evidence: the files under ``fixtures/notices`` are authored parser
    test fixtures, not retrieved official disclosures.
    """
    providers: List[Any] = []
    urls_raw = os.getenv("IPO_PRICE_BAND_NOTICE_URLS", "").strip()
    if urls_raw:
        try:
            providers.append(HttpNoticeProvider(json.loads(urls_raw)))
        except Exception:
            pass
    prospectus_urls_raw = os.getenv("IPO_PROSPECTUS_URLS", "").strip()
    if prospectus_urls_raw:
        try:
            providers.append(HttpProspectusProvider(json.loads(prospectus_urls_raw)))
        except Exception:
            pass
    dirs = [d for d in os.getenv("IPO_PRICE_BAND_NOTICE_DIR", "").split(os.pathsep) if d]
    if dirs:
        providers.append(RetainedNoticeProvider(dirs))
    cache_dir = os.getenv("IPO_ISSUE_TERMS_CACHE_DIR")
    cache = NoticeSnapshotCache(cache_dir, ttl_hours=float(os.getenv("IPO_ISSUE_TERMS_CACHE_TTL_HOURS", "168"))) if cache_dir else None
    return IssueTermsResolver(providers=providers, cache=cache)
