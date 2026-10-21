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
import copy
import math
import http.cookiejar
import json
from html import unescape as html_unescape
import os
import re
import tempfile
import time
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
DISCOVERABLE_TERMS = REQUIRED_ISSUE_TERMS + ("fresh_issue", "open_date", "close_date")

# Source hierarchy: official exchange/SEBI/issuer documents retrieved
# directly outrank retained copies of the same official documents; both
# outrank other evidence. Optional platform candidates are retained but
# never acquire official verification authority.
OFFICIAL_HOSTS = {
    "nseindia.com",
    "www.nseindia.com",
    "bseindia.com",
    "www.bseindia.com",
    "sebi.gov.in",
    "www.sebi.gov.in",
}


# Archive hosts are eligible only in the issuer-matched discovery pathway.
# Preserve the existing direct notice/final-Prospectus URL allowlists.
DISCOVERY_HOSTS = OFFICIAL_HOSTS | {'nsearchives.nseindia.com', 'listing.bseindia.com', 'api.bseindia.com'}

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,application/xhtml+xml;q=0.9,text/plain;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-IN,en;q=0.9",
}

# Session state for official-site retrieval.  BSE (verified 2026-10-18
# from the user's Windows runtime) serves its HOMEPAGE with HTTP 200 to
# cookie-less one-shot requests for listing/issue URLs, while a session
# that first establishes cookies from the site itself receives the real
# pages.  A shared cookie jar plus a one-time homepage warm-up per
# official host reproduces the browser session behaviour; content
# validation in the discovery provider still decides what counts as a
# listing, so a wrong-page response is never silently accepted.
_SESSION_JAR = http.cookiejar.CookieJar()
_SESSION_OPENER_READY = False
_WARMED_HOSTS: set = set()


def _ensure_session_opener() -> None:
    global _SESSION_OPENER_READY
    if _SESSION_OPENER_READY:
        return
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(_SESSION_JAR)
    )
    urllib.request.install_opener(opener)
    _SESSION_OPENER_READY = True


def _warm_up_session(url: str, timeout_seconds: float) -> None:
    """Establish session cookies from an official host's homepage.

    One attempt per host per process, best-effort: failure simply means
    the subsequent fetch proceeds cookie-less (and wrong-page responses
    are classified as such by the caller).  Warm-up is skipped for
    document (PDF) URLs so single-document retrieval behaviour -- and
    its retry accounting -- is unchanged.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in OFFICIAL_HOSTS or host in _WARMED_HOSTS:
        return
    if parsed.path.lower().endswith(".pdf"):
        return
    try:
        warm = urllib.request.Request(
            f"{parsed.scheme}://{host}/", headers=dict(_BROWSER_HEADERS)
        )
        with urllib.request.urlopen(warm, timeout=min(timeout_seconds, 15.0)) as response:
            response.read(4096)
        _WARMED_HOSTS.add(host)  # failed warm-ups must not poison subsequent attempts
    except Exception:
        pass  # best-effort; the real fetch and its validation decide


def _default_http_fetch(url: str, timeout_seconds: float, *, referer: Optional[str] = None,
                        eligible_redirect_hosts: Optional[set[str]] = None) -> bytes:
    """Default retrieval for official documents.

    Exchange/SEBI document servers commonly reject bare library user
    agents; a browser-compatible header set keeps retrieval behaviour
    consistent with how the documents are published for public access.
    The host allowlist -- not the headers -- is the security boundary.
    Listing/issue pages are fetched inside a cookie session (see
    ``_warm_up_session``): an HTTP 200 homepage response to a
    cookie-less request is a known BSE behaviour and must never be
    mistaken for the requested page.
    """
    _ensure_session_opener()
    parsed = urlparse(url)
    is_bse_api = parsed.hostname == 'api.bseindia.com' and parsed.path.startswith('/BseIndiaAPI/api/')
    _warm_up_session('https://www.bseindia.com/' if is_bse_api else url, timeout_seconds)
    headers = dict(_BROWSER_HEADERS)
    if parsed.scheme and parsed.hostname:
        headers["Referer"] = referer or f"{parsed.scheme}://{parsed.hostname}/"
    if parsed.path.startswith("/api/") or is_bse_api:
        headers["Accept"] = "application/json,text/plain,*/*"
    if is_bse_api:
        headers["Origin"] = "https://www.bseindia.com"
        headers["Referer"] = referer or "https://www.bseindia.com/"
    request = urllib.request.Request(url, headers=headers)
    # Bounded retries for transient retrieval failures (connection
    # resets, timeouts, HTTP 429/5xx): official document servers are
    # intermittently unavailable, and a single attempt turned a
    # transient failure into a permanent AWAITING_ISSUE_TERMS.
    last_exc: Optional[Exception] = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 (allow-listed hosts only)
                final_url = response.geturl() if hasattr(response, "geturl") else url
                final_host = (urlparse(final_url).hostname or "").lower()
                original_host = (urlparse(url).hostname or "").lower()
                eligible = eligible_redirect_hosts if eligible_redirect_hosts is not None else OFFICIAL_HOSTS
                allowed_redirects = eligible if original_host in eligible else {original_host}
                if final_host not in allowed_redirects or urlparse(final_url).scheme != parsed.scheme:
                    raise ValueError("retrieval redirected outside eligible source hosts")
                return response.read()
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code not in (429, 500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_exc = exc
        if attempt < 2:
            time.sleep(0.5 * (attempt + 1))
    assert last_exc is not None
    raise last_exc


def _best_effort_unlink(path: Path) -> None:
    """Remove a temp file without ever failing the caller.

    On Windows a file still held open by the PDF reader cannot be
    unlinked (WinError 32); letting that exception escape from a
    ``finally`` block destroyed otherwise-successful parses and was
    misreported as a document rejection.  Cleanup is best-effort: the
    OS temp directory reclaims leftovers.
    """
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _norm_name(name: Optional[str]) -> str:
    return "".join(ch for ch in (name or "").upper() if ch.isalnum())


def _norm_key(key: Optional[str]) -> str:
    """Slug-normal form of a configured mapping key / identifier."""
    slug = "".join(ch if ch.isalnum() else "-" for ch in (key or "").upper())
    return "-".join(part for part in slug.split("-") if part)


def _lookup_configured_url(
    urls_by_ipo: Mapping[str, str], company_name: str, ipo_id: str
) -> Optional[str]:
    """Find the configured official URL for this issuer.

    Exact ``ipo_id`` and exact ``company_name`` matches win; otherwise a
    slug-normalised comparison applies, so an operator may key the
    mapping by the runtime IPO ID slug (``ACME-LIMITED``), the spaced
    company name (``Acme Limited``) or any case/separator variant --
    all denote the same issuer key, never a different issuer's URL.
    """
    for candidate in (ipo_id, company_name):
        if candidate and urls_by_ipo.get(candidate):
            return urls_by_ipo[candidate]
    wanted = {_norm_key(ipo_id), _norm_key(company_name)} - {""}
    for key, url in urls_by_ipo.items():
        if _norm_key(key) in wanted:
            return url
    return None


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
    if low is not None and (isinstance(low, bool) or not isinstance(low, (int, float)) or not math.isfinite(low) or low <= 0):
        return "price_band_low is not a positive number"
    if high is not None and (isinstance(high, bool) or not isinstance(high, (int, float)) or not math.isfinite(high) or high <= 0):
        return "price_band_high is not a positive number"
    if low is not None and high is not None and high < low:
        return "price_band_high is below price_band_low"
    if lot is not None and (isinstance(lot, bool) or not isinstance(lot, (int, float)) or not math.isfinite(lot) or lot <= 0 or int(lot) != lot):
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
    components: List[Any] = field(default_factory=list)

    @property
    def values(self) -> Dict[str, Any]:
        return _notice_values(self.result)


@dataclass
class ListingAttempt:
    """What one configured listing source actually yielded.

    Every configured listing URL produces exactly one attempt, so a
    source can never contribute to the aggregate outcome without a
    visible record of what it returned.  ``searched`` is true only
    when the served response really carried issue records, i.e. when
    the listing was genuinely read.
    """
    url: str
    classification: str  # ok | empty | homepage | shell | failed
    searched: bool = False
    issue_entries: int = 0
    detail: str = ""


@dataclass
class ProviderReport:
    provider: str
    outcome: str  # FOUND | NOT_FOUND | UNAVAILABLE | REJECTED
    detail: str = ""
    # True only when the provider actually searched a genuine, usable
    # official listing for this issuer.  A NOT_FOUND report that is
    # not backed by such a listing search (a search of a retained
    # local corpus, which is unverified and is not a listing) is not
    # evidence of non-publication and never maps to UNPUBLISHED.
    listing_searched: bool = False
    # Per-source reasons (one per listing URL that could not be
    # searched), kept structured so no reason is lost when the
    # single-line detail is bounded for display.
    notes: List[str] = field(default_factory=list)
    # One attempt per configured listing source, searched or not.
    sources: List[ListingAttempt] = field(default_factory=list)

    @property
    def searched_listings(self) -> List[str]:
        """The listings that were genuinely searched, by URL.

        This is the evidence a NOT_FOUND report must carry before the
        resolver may conclude UNPUBLISHED: a bare flag is not enough,
        the report has to name a listing that really was read.
        """
        return [attempt.url for attempt in self.sources if attempt.searched]


def _json_safe_diagnostics(value: Any) -> Any:
    """Keep rejected nonfinite evidence legible without emitting illegal JSON.

    This is reporting only: candidate validation/selection uses the original
    numbers, and no rejected value is coerced to zero or canonical input.
    """
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {key: _json_safe_diagnostics(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_diagnostics(item) for item in value]
    return copy.deepcopy(value)


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
    field_diagnostics: Dict[str, Any] = field(default_factory=dict)
    enrichment_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "fields": _json_safe_diagnostics(self.field_diagnostics),
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
                {
                    "provider": r.provider,
                    "outcome": r.outcome,
                    "detail": r.detail,
                    "listing_searched": r.listing_searched,
                    "searched_listings": list(r.searched_listings),
                    "notes": list(r.notes),
                    "sources": [
                        {
                            "url": s.url,
                            "classification": s.classification,
                            "searched": bool(s.searched),
                            "issue_entries": s.issue_entries,
                            "detail": s.detail,
                        }
                        for s in r.sources
                    ],
                }
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
            return None, ProviderReport(
                self.name,
                "NOT_FOUND",
                f"no issuer-matched notice in retained documents ({searched} parsed/searched); "
                "the retained corpus is unverified and is not an official listing, so this "
                "is not evidence of non-publication",
            )
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
        timeout_seconds: float = 60.0,
    ):
        self.urls_by_ipo = dict(urls_by_ipo)
        self.allowed_hosts = allowed_hosts if allowed_hosts is not None else set(OFFICIAL_HOSTS)
        self._requires_https = allowed_hosts is None
        self.timeout_seconds = timeout_seconds
        self._fetcher = fetcher

    def _fetch(self, url: str) -> bytes:
        if self._fetcher is not None:
            return self._fetcher(url)
        return _default_http_fetch(url, self.timeout_seconds)

    def find(self, company_name: str, ipo_id: str) -> tuple[Optional[NoticeCandidate], ProviderReport]:
        url = _lookup_configured_url(self.urls_by_ipo, company_name, ipo_id)
        if not url:
            return None, ProviderReport(self.name, "UNAVAILABLE", "no official notice URL configured for this issuer")
        host = (urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts or (self._requires_https and urlparse(url).scheme != "https"):
            return None, ProviderReport(self.name, "REJECTED", f"host {host or '?'} is not an HTTPS official source host")
        try:
            raw = self._fetch(url)
        except Exception as exc:
            return None, ProviderReport(self.name, "UNAVAILABLE", f"official source retrieval failed: {exc}")
        if raw.lstrip()[:15].lower().startswith((b"<!doctype", b"<html")):
            return None, ProviderReport(self.name, "REJECTED", "official host returned an HTML page instead of a document (possible interstitial or anti-bot response)")
        suffix = ".pdf" if raw.startswith(b"%PDF-") else ".txt"
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                handle.write(raw)
                temp_path = Path(handle.name)
            try:
                from .extraction.official_notice_ocr import parse_if_scanned
                result = parse_if_scanned(raw, url)
                if result is None:
                    result = PriceBandNoticeParser().parse_from_file(temp_path)
            finally:
                _best_effort_unlink(temp_path)
        except Exception as exc:
            return None, ProviderReport(self.name, "REJECTED", f"retrieved document is not a parseable Price Band Notice: {exc}")
        if _norm_name(result.company_name) != _norm_name(company_name):
            return None, ProviderReport(self.name, "REJECTED", "retrieved notice names a different issuer: " + repr(result.company_name) + ("; OCR header: " + result.metadata["ocr_header_excerpt"] if result.metadata.get("ocr_header_excerpt") else ""))
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
        timeout_seconds: float = 60.0,
    ):
        self.urls_by_ipo = dict(urls_by_ipo)
        self.allowed_hosts = allowed_hosts if allowed_hosts is not None else set(OFFICIAL_HOSTS)
        self._requires_https = allowed_hosts is None
        self.timeout_seconds = timeout_seconds
        self._fetcher = fetcher

    def _fetch(self, url: str) -> bytes:
        if self._fetcher is not None:
            return self._fetcher(url)
        return _default_http_fetch(url, self.timeout_seconds)

    def find(self, company_name: str, ipo_id: str) -> tuple[Optional[NoticeCandidate], ProviderReport]:
        url = _lookup_configured_url(self.urls_by_ipo, company_name, ipo_id)
        if not url:
            return None, ProviderReport(self.name, "UNAVAILABLE", "no official prospectus URL configured for this issuer")
        host = (urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts or (self._requires_https and urlparse(url).scheme != "https"):
            return None, ProviderReport(self.name, "REJECTED", f"host {host or '?'} is not an HTTPS official source host")
        try:
            raw = self._fetch(url)
        except Exception as exc:
            return None, ProviderReport(self.name, "UNAVAILABLE", f"official source retrieval failed: {exc}")
        if raw.lstrip()[:15].lower().startswith((b"<!doctype", b"<html")):
            return None, ProviderReport(self.name, "REJECTED", "official host returned an HTML page instead of a document (possible interstitial or anti-bot response)")
        suffix = ".pdf" if raw.startswith(b"%PDF-") else ".txt"
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                handle.write(raw)
                temp_path = Path(handle.name)
            try:
                result = ProspectusTermsParser().parse_from_file(temp_path)
            finally:
                _best_effort_unlink(temp_path)
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


class OfficialDiscoveryProvider:
    """Discovers official issue-term documents without per-issuer config.

    Searches the official listing pages of the exchanges/SEBI for
    documents linked for this issuer, then runs each candidate through
    the same allow-list, issuer-matching and classification pipeline as
    the configured-URL providers.  Nothing is scraped from search
    engines or snippets: only documents hosted on allow-listed official
    hosts and linked from official listing pages are considered, and a
    candidate counts only after it parses and issuer-matches.

    Outcomes: FOUND (verified candidate); NOT_FOUND (at least one
    valid listing was actually searched and no issuer-matched document
    was found -- the only outcome the resolver may map to UNPUBLISHED);
    UNAVAILABLE (no valid listing could be retrieved or searched --
    transport failures and homepage/JavaScript-shell/no-content
    responses included; never evidence of non-publication).
    """

    name = "official-discovery"

    LISTING_URLS = (
        "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
        # BSE's server-rendered public-issues listing (the newer
        # publicissue.html is a JavaScript application shell whose raw
        # HTML contains no issue rows, so a plain HTTP client finds
        # nothing there; this classic page carries the DisplayIPO
        # links in the served HTML).
        "https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P",
        "https://www.bseindia.com/publicissue.html",
        # Actual current public SPA feed, not the deprecated GetPublicIssue/w.
        "https://api.bseindia.com/BseIndiaAPI/api/GetPublicIssue_par_updated/w?flag=1",
        # Public record feed behind NSE's JavaScript listing; no guessed issuer IDs.
        "https://www.nseindia.com/api/all-upcoming-issues?category=ipo",
        "https://www.sebi.gov.in/sebiweb/home/handleAction?doListing=yes&sid=1&ssid=7&smid=0",
    )
    _GENERIC_TOKENS = {"LIMITED", "INDIA", "PRIVATE", "COMPANY", "INDUSTRIES", "INDUSTRY", "GLOBAL", "INTERNATIONAL"}

    # Response-identity fingerprints.  An HTTP 200 is not a listing:
    # BSE serves its homepage (title carries the LIVE/SENSEX masthead)
    # to session-less requests, and its newer public-issues page is a
    # JavaScript shell.  Neither may count as a searched listing, and
    # neither is evidence that an issuer's terms are unpublished.
    #
    # A listing is recognised by its ISSUE ENTRIES -- never by a
    # marker substring.  Marker-only recognition was the defect
    # repaired on 2026-10-18: an exchange page echoes its own path in
    # navigation and canonical links ("public issues",
    # "all-upcoming-issues"), so the NSE response received on the
    # Windows runtime was classified as a genuine listing although its
    # served HTML carries no issue row at all (the listing table is
    # filled client-side).  That single response produced a false
    # NOT_FOUND and therefore a false UNPUBLISHED conclusion, which
    # contradicted its own diagnostics (Windows trace
    # ing-5aa6dd92cd7640a8, at 3fea259).
    _HOMEPAGE_MARKERS = ("bse sensex", "live stock/share market", "formerly bombay stock exchange")
    _SHELL_MARKERS = ("<app-root", "app-root>", "enable javascript to run this app", "you need to enable javascript")

    # Column headers that identify a table of issue records.  Two or
    # more of them in a table's header row make the table a listing of
    # issues; a single generic column does not.
    _ISSUE_TABLE_COLUMNS = (
        "security name", "company name", "issue start date", "issue open date",
        "open date", "close date", "start date", "end date", "issue end date",
        "issue status", "offer price", "price band", "market lot", "issue size",
        "no. of shares", "bid lot", "issue period", "issue name", "issue type",
    )
    # References to ONE issue: the exchange issue-information pages and
    # the issuer's own official documents (price band notice, SEBI
    # attachment documents).  These are exactly the links discovery
    # follows, so their presence in the served HTML is evidence that
    # the listing itself was readable.
    _PER_ISSUE_LINK_MARKERS = (
        "displayipo", "acqdisp", "attachdocs", "issue-information",
        "issue_information", "price-band", "price_band",
    )
    # An issue date as published by the exchanges ("21-10-2026",
    # "21/10/2026", "21 Oct 2026", "October 2026").
    _ISSUE_DATE_PATTERN = re.compile(
        r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b"
        r"|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b"
        r"|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}\b"
    )

    @classmethod
    def _per_issue_links(cls, text: str) -> List[str]:
        """The served page's links to ONE issue (exchange issue page or
        the issuer's own official document).

        Only real anchor targets count: a page that merely mentions
        an issue in prose is not a listing, and a ``<link>`` element
        (canonical/alternate metadata) is page chrome, not a link to
        an issue.
        """
        return [
            href
            for href in re.findall(r"<a\b[^>]*href\s*=\s*[\"']([^\"']*)[\"']", text, re.IGNORECASE)
            if any(marker in href for marker in cls._PER_ISSUE_LINK_MARKERS)
        ]

    @classmethod
    def _issue_records(cls, text: str) -> List[str]:
        """The issue records the served HTML actually carries.

        A record is a TABLE DATA ROW that identifies one issue: a row
        that links to an issue page or to an official document, or a
        row of an issue-listing table that carries an issue date.

        Page chrome can never be a record.  An exchange repeats its
        own navigation and metadata links on every page -- NSE serves
        "Price Bands & Surveillance Actions" in the site-wide menu
        and canonical/alternate links to "/market-data/issue-
        information?series=EQ&symbol=..." on every page it renders --
        so a scan of the whole document (the rule used before
        2026-10-18) classified the client-side NSE listing shell as a
        genuine listing and produced a false NOT_FOUND, hence a false
        UNPUBLISHED conclusion (Windows acceptance trace
        ing-32ddf313bbe247b0 at 0dda109, 2026-10-18).
        """
        records: List[str] = []
        for table in re.findall(r"<table\b.*?</table>", text, re.DOTALL):
            rows = re.findall(r"<tr\b.*?</tr>", table, re.DOTALL)
            if not rows:
                continue
            header = rows[0]
            # A header row names the listing's columns; a table whose
            # first row is already a data row (the shape BSE's
            # classic listing serves) has no header at all.
            is_issue_table = (
                "<td" not in header
                and sum(1 for marker in cls._ISSUE_TABLE_COLUMNS if marker in header) >= 2
            )
            for row in rows:
                if "<td" not in row:
                    continue  # a header row, not a record
                if cls._per_issue_links(row) or (
                    is_issue_table and cls._ISSUE_DATE_PATTERN.search(row)
                ):
                    records.append(row)
        return records

    @classmethod
    def _has_issue_entries(cls, text: str) -> bool:
        """True only when the served HTML actually carries issue entries.

        A page whose listing table is filled client-side carries no
        issue record at all: it was never a searched listing, however
        many navigation, canonical or menu links it repeats.
        """
        return bool(cls._issue_records(text))

    @staticmethod
    def _page_text(raw: bytes) -> str:
        """The served page as lower-case text (classification input)."""
        return raw.decode("utf-8", errors="ignore").lower()

    @classmethod
    def _classify_listing(cls, raw: bytes) -> str:
        """Classify a fetched listing response: ok | empty | homepage | shell.

        ``ok`` means the response carried the listing's issue entries --
        the only response that may count as a searched listing.  A
        homepage, a JavaScript application shell and a page without
        issue entries are unusable: none of them is evidence that an
        issuer's terms are unpublished.

        BSE pages share the homepage masthead in their chrome, so the
        homepage verdict requires the masthead AND the absence of issue
        entries: a real DisplayIPO page carries the masthead title but
        is not the homepage.
        """
        text = cls._page_text(raw)
        if any(marker in text for marker in cls._SHELL_MARKERS):
            return "shell"
        if cls._has_issue_entries(text):
            return "ok"
        if sum(marker in text for marker in cls._HOMEPAGE_MARKERS) >= 2:
            return "homepage"
        return "empty"

    def __init__(
        self,
        fetcher: Optional[Callable[[str], bytes]] = None,
        allowed_hosts: Optional[set[str]] = None,
        listing_urls: Optional[Sequence[str]] = None,
        max_candidates: int = 6,
        timeout_seconds: float = 60.0,
    ):
        self.allowed_hosts = allowed_hosts if allowed_hosts is not None else set(DISCOVERY_HOSTS)
        self._requires_https = allowed_hosts is None
        self.listing_urls = list(listing_urls) if listing_urls is not None else list(self.LISTING_URLS)
        self.max_candidates = max_candidates
        self.timeout_seconds = timeout_seconds
        self._fetcher = fetcher

    def _fetch(self, url: str, referer: Optional[str] = None) -> bytes:
        if self._fetcher is not None:
            return self._fetcher(url)
        return _default_http_fetch(url, self.timeout_seconds, referer=referer,
                                   eligible_redirect_hosts=self.allowed_hosts)

    def _candidate_links(self, listing_bytes: bytes, base_url: str, company_name: str) -> List[str]:
        # Served HTML encodes query separators as &amp; in hrefs;
        # unescape first so followed URLs carry real parameters.
        text = html_unescape(listing_bytes.decode("utf-8", errors="ignore"))
        tokens = [
            tok
            for tok in re.split(r"[^A-Za-z0-9]+", (company_name or "").upper())
            if len(tok) >= 3 and tok not in self._GENERIC_TOKENS
        ]
        slug = "".join(re.split(r"[^A-Za-z0-9]+", (company_name or "").upper()))
        found: List[Tuple[int, str]] = []
        from .official_issue_sources import links
        pairs = links(listing_bytes, base_url)
        for match in re.finditer(r"https?://[^\s\"<>]+?\.pdf\b", text, re.IGNORECASE):
            pairs.append((match.group(0), ""))
        seen = set()
        for href, anchor in pairs:
            url = urllib.parse.urljoin(base_url, href.strip())
            host = (urllib.parse.urlparse(url).hostname or "").lower()
            if host not in self.allowed_hosts or (self._requires_https and urlparse(url).scheme != "https"):
                continue
            haystack = f"{url} {anchor}".upper()
            if slug and slug in haystack.replace("-", "").replace("_", "").replace(" ", ""):
                relevant = True
            else:
                relevant = any(tok in haystack for tok in tokens)
            if not relevant:
                continue
            low = url.lower()
            is_document = low.endswith(".pdf") or ".pdf" in low or "attachdocs" in low or "prospectus" in low or "price-band" in low or "price_band" in low
            is_issue_page = "displayipo" in low or "issue-information" in low or "issue_information" in low
            if not (is_document or is_issue_page):
                continue
            if url in seen:
                continue
            seen.add(url)
            if is_issue_page:
                priority = 0
            elif "price-band" in low or "price_band" in low or "price band" in anchor.lower():
                priority = 1
            elif "prospectus" in low:
                priority = 2
            else:
                priority = 3
            found.append((priority, url))
        found.sort(key=lambda item: item[0])
        return [url for _prio, url in found[: self.max_candidates]]


    def _from_issue_page(self, url: str, company_name: str, referer: Optional[str] = None) -> tuple[Optional[NoticeCandidate], str]:
        """Fetch and parse an official exchange issue-information page.

        Returns (candidate, reason); reason names the exact failing
        stage when no candidate results, so a wrong-page (homepage)
        response is never conflated with an unpublished issue.
        """
        from .extraction.exchange_issue_page import ExchangeIssuePageParser

        host = (urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts or (self._requires_https and urlparse(url).scheme != "https"):
            return None, f"{url}: host is not an HTTPS official source host"
        try:
            raw = self._fetch(url, referer=referer)
        except Exception as exc:
            return None, f"{url}: issue-page retrieval failed ({type(exc).__name__}: {exc})"
        try:
            if urlparse(url).path == '/api/ipo-detail':
                from .official_issue_sources import parse_nse_detail
                result = parse_nse_detail(raw, url)
            else:
                if not raw.lstrip().startswith(b'<'):
                    return None, f"{url}: issue page returned a non-HTML response"
                # Detail pages are not listings. BSE uses its homepage title on
                # real detail pages too; verify issuer + labelled terms FIRST.
                result = ExchangeIssuePageParser().parse(raw, url=url)
        except Exception as exc:
            return None, f"{url}: issue page could not be parsed ({type(exc).__name__}: {exc})"
        if _norm_name(result.company_name) != _norm_name(company_name):
            kind = self._classify_listing(raw)
            reason = ("exchange homepage instead of issue information" if kind == "homepage" else
                      "JavaScript shell with no issuer issue data" if kind == "shell" else
                      "issue page names a different issuer or lacks issuer identity")
            return None, f"{url}: {reason}"
        if not any(getattr(result, f + "_amount" if f in ("fresh_issue", "ofs") else f, None) is not None for f in DISCOVERABLE_TERMS):
            return None, f"{url}: issue page has no labelled Price Band or Market Lot"
        return NoticeCandidate(
            result=result,
            provider=self.name,
            uri=url,
            retrieved_at=_utcnow().isoformat().replace("+00:00", "Z"),
            raw_bytes=raw,
            verified=True,
        ), ""

    def _issue_attachments(self, page, company_name, ipo_id):
        """Follow bounded document links only after the issue page issuer matches."""
        from .official_issue_sources import links, official_document_members
        from .extraction.official_offer_amounts import document_pages, explicit_amounts, parse_official_rhp
        found, reasons = [], []
        eligible = []
        for url, label in links(page.raw_bytes or b"", page.uri):
            parsed = urlparse(url)
            if (parsed.hostname not in self.allowed_hosts or
                    (self._requires_https and parsed.scheme != "https")):
                continue
            if (parsed.path.lower().endswith((".pdf", ".zip")) and
                    re.search(r"price.?band|prospectus|rhp|drhp|gid|offer.document|ratios|basis.of.issue.price", label + " " + url, re.I)):
                if url not in eligible:
                    eligible.append(url)
        for url in eligible[:self.max_candidates]:
            try:
                raw = self._fetch(url, referer=page.uri)
                members = list(official_document_members(raw, url))
                if not members:
                    reasons.append(f"{url}: official archive contains no supported PDF/text members")
                for member, uri in members:
                    try:
                        result = parse_official_rhp(member, uri)
                    except Exception:
                        result = None
                    if result is not None:
                        if _norm_name(result.company_name) != _norm_name(company_name):
                            reasons.append(f"{uri}: official RHP names a different issuer")
                            continue
                        found.append(NoticeCandidate(result, self.name, uri,
                            _utcnow().isoformat().replace("+00:00", "Z"), verified=True))
                        continue
                    rejected = []
                    for provider_cls in (HttpNoticeProvider, HttpProspectusProvider):
                        provider = provider_cls({ipo_id: uri}, fetcher=lambda _url, data=member: data,
                            allowed_hosts=self.allowed_hosts, timeout_seconds=self.timeout_seconds)
                        candidate, report = provider.find(company_name, ipo_id)
                        if candidate is not None:
                            if provider_cls is HttpNoticeProvider:
                                candidate.result = explicit_amounts(candidate.result, document_pages(member))
                            found.append(candidate)
                            break
                        rejected.append(f"{report.provider}: {report.detail}")
                    else:
                        reasons.append(f"{uri}: attachment rejected; " + "; ".join(rejected))
            except Exception as exc:
                reasons.append(f"{url}: official attachment retrieval/decoding failed ({type(exc).__name__}: {exc})")
        return found, reasons

    @staticmethod
    def _merge_candidates(candidates: List[NoticeCandidate]) -> NoticeCandidate:
        """Fill missing pricing fields of the primary candidate from
        other verified, issuer-matched candidates (the resolver's
        conflict check still rejects disagreements).  Field objects
        keep their own quotes/locators; sources are recorded."""
        if len(candidates) == 1:
            return candidates[0]
        primary = copy.deepcopy(candidates[0])
        primary.components = list(candidates)
        for other in candidates[1:]:
            for name in PRICING_TERMS + ("open_date", "close_date"):
                if getattr(primary.result, name, None) is None:
                    setattr(primary.result, name, getattr(other.result, name, None))
        return primary

    def find(self, company_name: str, ipo_id: str) -> tuple[Optional[NoticeCandidate], ProviderReport]:
        reached = False
        notes: List[str] = []
        attempts: List[ListingAttempt] = []
        all_candidates: List[NoticeCandidate] = []

        def note(text: str) -> None:
            if text and text not in notes:
                notes.append(text)

        for listing_url in self.listing_urls:
            try:
                from .official_issue_sources import BSE_LISTING, BSE_PUBLIC_LISTING
                raw = self._fetch(listing_url, referer=BSE_PUBLIC_LISTING if listing_url == BSE_LISTING else None)
            except Exception as exc:
                detail = f"listing retrieval failed ({type(exc).__name__}: {exc})"
                note(f"{listing_url}: {detail}")
                attempts.append(ListingAttempt(listing_url, "failed", False, 0, detail))
                continue
            if listing_url == BSE_LISTING and not raw.lstrip().startswith(b"<"):
                from .official_issue_sources import bse_issue_records
                try:
                    records = bse_issue_records(raw, company_name)
                except (ValueError, TypeError, AttributeError) as exc:
                    detail = f"BSE public issue records malformed/unusable ({type(exc).__name__}: {exc})"
                    attempts.append(ListingAttempt(listing_url, "malformed", False, 0, detail))
                    note(f"{listing_url}: {detail}")
                    continue
                attempts.append(ListingAttempt(listing_url, "issue_records" if records else "no_match",
                    bool(records), len(records), "Exact issuer-matched current BSE IPO records; absence is not publication evidence"))
                for page_url, result in records[:self.max_candidates]:
                    candidate = NoticeCandidate(result, self.name, listing_url,
                        _utcnow().isoformat().replace("+00:00", "Z"), raw_bytes=raw, verified=True)
                    all_candidates.append(candidate)
                    page_candidate, reason = self._from_issue_page(page_url, company_name, referer=BSE_PUBLIC_LISTING)
                    if page_candidate:
                        all_candidates.append(page_candidate)
                        attachments, reasons = self._issue_attachments(page_candidate, company_name, ipo_id)
                        all_candidates.extend(attachments)
                        for reason in reasons:
                            note(reason)
                    else:
                        note(reason)
                continue
            from .official_issue_sources import NSE_LISTING, nse_issue_links
            if listing_url == NSE_LISTING and not raw.lstrip().startswith(b"<"):
                try:
                    discovered = nse_issue_links(raw, company_name)
                except (ValueError, TypeError, AttributeError) as exc:
                    detail = f"NSE public issue records malformed/unusable ({type(exc).__name__}: {exc})"
                    attempts.append(ListingAttempt(listing_url, "malformed", False, 0, detail))
                    note(f"{listing_url}: {detail}")
                    continue
                attempts.append(ListingAttempt(listing_url, "issue_records" if discovered else "no_match",
                    bool(discovered), len(discovered), "Exact issuer-matched NSE records; absence is not publication evidence"))
                for page_url, api_url in discovered[:self.max_candidates]:
                    for detail_url in (page_url, api_url):
                        candidate, reason = self._from_issue_page(detail_url, company_name, referer=listing_url)
                        if candidate:
                            all_candidates.append(candidate)
                            attachments, reasons = self._issue_attachments(candidate, company_name, ipo_id)
                            all_candidates.extend(attachments)
                            for reason in reasons:
                                note(reason)
                        else:
                            note(reason)
                continue
            kind = self._classify_listing(raw)
            if kind == "homepage":
                detail = (
                    "returned the exchange homepage, not an issue listing "
                    "(HTTP 200 wrong-page response; a listing was not searched)"
                )
                note(f"{listing_url}: {detail}")
                attempts.append(ListingAttempt(listing_url, "homepage", False, 0, detail))
                continue
            if kind == "shell":
                detail = (
                    "returned a JavaScript application shell with no issue rows "
                    "in the served HTML (a listing was not searched)"
                )
                note(f"{listing_url}: {detail}")
                attempts.append(ListingAttempt(listing_url, "shell", False, 0, detail))
                continue
            if kind != "ok":
                # A page with no recognizable listing content and no
                # issue entries cannot be counted as a searched
                # listing: treating it as one turned unusable
                # responses into a false NOT_FOUND / UNPUBLISHED
                # conclusion (Windows traces ing-eacd8815051f4222 at
                # ea437f3, ing-5aa6dd92cd7640a8 at 3fea259 and
                # ing-32ddf313bbe247b0 at 0dda109, 2026-10-18).
                detail = (
                    "returned a page with no recognizable listing content and no "
                    "issue entries in the served HTML (the listing table may be "
                    "populated by JavaScript; a listing was not searched)"
                )
                note(f"{listing_url}: {detail}")
                attempts.append(ListingAttempt(listing_url, "empty", False, 0, detail))
                continue
            reached = True
            records = self._issue_records(self._page_text(raw))
            attempt = ListingAttempt(
                listing_url, "ok", True, len(records),
                f"listing searched: {len(records)} issue "
                f"{'entry' if len(records) == 1 else 'entries'} read from the served HTML",
            )
            attempts.append(attempt)
            collected: List[NoticeCandidate] = []
            for link in self._candidate_links(raw, listing_url, company_name):
                low = link.lower()
                if "displayipo" in low or "issue-information" in low or "issue_information" in low:
                    page_candidate, reason = self._from_issue_page(link, company_name, referer=listing_url)
                    if page_candidate is not None:
                        collected.append(page_candidate)
                        attachments, reasons = self._issue_attachments(page_candidate, company_name, ipo_id)
                        collected.extend(attachments)
                        for reason in reasons:
                            note(reason)
                    else:
                        note(reason)
                    continue
                for provider_cls in (HttpNoticeProvider, HttpProspectusProvider):
                    provider = provider_cls({ipo_id: link}, fetcher=self._fetcher, allowed_hosts=self.allowed_hosts, timeout_seconds=self.timeout_seconds)
                    candidate, sub_report = provider.find(company_name, ipo_id)
                    if candidate is not None:
                        collected.append(candidate)
                        break
                else:
                    # A candidate document that could not be used must
                    # not vanish silently: record why.
                    note(f"{link}: {sub_report.detail}")
            if collected:
                attempt.detail += "; issuer-matched official document found"
                all_candidates.extend(collected)
            else:
                attempt.detail += "; no issuer-matched official document found in it"
        if all_candidates:
            merged = self._merge_candidates(all_candidates)
            return merged, ProviderReport(self.name, "FOUND", "examined all configured listings; issuer-matched documents found",
                                          notes=list(notes), sources=list(attempts))
        if reached:
            searched = [a.url for a in attempts if a.searched]
            detail = (
                "valid official listings searched ("
                + ", ".join(searched)
                + "); no issuer-matched official document was found (this does "
                "not by itself establish non-publication)"
            )
            if notes:
                detail += "; " + "; ".join(notes)
            # ``listing_searched=True`` is the substantiation the
            # resolver requires before a NOT_FOUND may become
            # UNPUBLISHED: at least one genuine, usable listing really
            # was searched for this issuer.  The searched listings are
            # named in ``sources`` so the claim is checkable.
            return None, ProviderReport(
                self.name, "NOT_FOUND", detail, listing_searched=True,
                notes=list(notes), sources=list(attempts),
            )
        return None, ProviderReport(
            self.name, "UNAVAILABLE",
            "no valid official listing could be retrieved: "
            + ("; ".join(notes) if notes else "no listing sources configured"),
            notes=list(notes), sources=list(attempts),
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
                from .extraction.official_notice_ocr import parse_if_scanned
                result = parse_if_scanned(bin_path.read_bytes(), meta.get("uri", ""))
                if result is None:
                    result = PriceBandNoticeParser().parse_from_file(temp_path)
            finally:
                _best_effort_unlink(temp_path)
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

    def resolve(self, *, company_name: str, ipo_id: str, missing_fields: Sequence[str], issue_context: Optional[Mapping[str, Any]] = None) -> ResolutionOutcome:
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

        # A cache is evidence, not permission to skip remaining configured sources.
        for provider in self.providers:
            try:
                candidate, report = provider.find(company_name, ipo_id)
            except Exception as exc:
                candidate = None
                report = ProviderReport(getattr(provider, "name", type(provider).__name__),
                                        "UNAVAILABLE", f"provider failed: {type(exc).__name__}: {exc}")
            outcome.provider_reports.append(report)
            if candidate is not None:
                candidates.extend(candidate.components or [candidate])

        if not candidates:
            # A NOT_FOUND provider report becomes UNPUBLISHED only when
            # it is substantiated by a search of a genuine, usable
            # official listing (``listing_searched``) AND it names the
            # listings that were really read (``searched_listings``).
            # A provider that could not search anything -- transport
            # failure, exchange homepage, JavaScript application shell,
            # a page whose served HTML carries no issue entries --
            # reports UNAVAILABLE and can never contribute an
            # UNPUBLISHED conclusion; nor can a search of the retained
            # local corpus, which is unverified and is not a listing.
            # The flag alone is not evidence: a report that claims a
            # search but names no listing is treated as unsubstantiated
            # (Windows acceptance trace ing-32ddf313bbe247b0 at
            # 0dda109, 2026-10-18).
            searched = any(
                r.outcome == "NOT_FOUND" and r.listing_searched and r.searched_listings
                for r in outcome.provider_reports
            )
            outcome.status = "UNPUBLISHED" if searched else "UNAVAILABLE"
            outcome.field_diagnostics = {f: {"state": "NOT_DISCLOSED_IN_EXAMINED_SOURCES" if searched else "SOURCE_UNAVAILABLE",
                                           "candidates": [], "detail": "Eligible providers exhausted; listing silence is not proof of non-publication."}
                                         for f in missing_fields}
            return outcome

        from .issue_term_fields import resolve_fields
        return resolve_fields(self, outcome, candidates, company_name, ipo_id, missing_fields, from_cache, issue_context or {})


class ConfigurationDiagnosticProvider:
    """Reports an unusable URL-mapping configuration as a provider
    outcome, instead of the provider silently never being registered.

    The detail names the environment variable and the parse problem;
    it never echoes the configured value (which may contain operator
    infrastructure details beyond the public official URLs).
    """

    def __init__(self, name: str, detail: str):
        self.name = name
        self.detail = detail

    def find(self, company_name: str, ipo_id: str) -> tuple[Optional[NoticeCandidate], ProviderReport]:
        return None, ProviderReport(self.name, "UNAVAILABLE", self.detail)


def _url_map_from_env(var_name: str) -> tuple[Dict[str, str], Optional[str]]:
    """Parse an IPO-ID -> URL JSON env mapping.

    Returns (mapping, problem). ``problem`` is None when the variable is
    unset/empty or parses to a usable mapping; otherwise it describes
    why the configuration cannot be used.
    """
    raw = os.getenv(var_name, "").strip()
    if not raw:
        return {}, None
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        return {}, f"{var_name} is not valid JSON ({type(exc).__name__}: {exc}); expected a JSON object mapping IPO IDs to official URLs"
    if not isinstance(parsed, dict):
        return {}, f"{var_name} must be a JSON object mapping IPO IDs to official URLs, not {type(parsed).__name__}"
    mapping = {str(k): v for k, v in parsed.items() if isinstance(v, str) and v.strip()}
    if parsed and not mapping:
        return {}, f"{var_name} contains no usable IPO-ID -> URL entries"
    return mapping, None


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
    notice_urls, notice_problem = _url_map_from_env("IPO_PRICE_BAND_NOTICE_URLS")
    if notice_problem:
        providers.append(ConfigurationDiagnosticProvider(HttpNoticeProvider.name, notice_problem))
    elif notice_urls:
        providers.append(HttpNoticeProvider(notice_urls))
    prospectus_urls, prospectus_problem = _url_map_from_env("IPO_PROSPECTUS_URLS")
    if prospectus_problem:
        providers.append(ConfigurationDiagnosticProvider(HttpProspectusProvider.name, prospectus_problem))
    elif prospectus_urls:
        providers.append(HttpProspectusProvider(prospectus_urls))
    if os.getenv("IPO_OFFICIAL_DISCOVERY", "1").strip().lower() not in ("0", "false", "no"):
        providers.append(OfficialDiscoveryProvider())
    from .issue_platforms import PublicPlatformProvider, PLATFORM_LISTINGS
    enabled = {x.strip().lower() for x in os.getenv("IPO_TERM_PLATFORM_PROVIDERS", "").split(",") if x.strip()}
    for name in sorted(enabled):
        if name in PLATFORM_LISTINGS:
            providers.append(PublicPlatformProvider(name))
        else:
            providers.append(ConfigurationDiagnosticProvider(name, "unknown platform provider"))
    dirs = [d for d in os.getenv("IPO_PRICE_BAND_NOTICE_DIR", "").split(os.pathsep) if d]
    if dirs:
        providers.append(RetainedNoticeProvider(dirs))
    cache_dir = os.getenv("IPO_ISSUE_TERMS_CACHE_DIR")
    cache = NoticeSnapshotCache(cache_dir, ttl_hours=float(os.getenv("IPO_ISSUE_TERMS_CACHE_TTL_HOURS", "168"))) if cache_dir else None
    return IssueTermsResolver(providers=providers, cache=cache)
