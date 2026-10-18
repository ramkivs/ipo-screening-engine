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
    _WARMED_HOSTS.add(host)
    try:
        warm = urllib.request.Request(
            f"{parsed.scheme}://{host}/", headers=dict(_BROWSER_HEADERS)
        )
        with urllib.request.urlopen(warm, timeout=min(timeout_seconds, 15.0)) as response:
            response.read(4096)
    except Exception:
        pass  # best-effort; the real fetch and its validation decide


def _default_http_fetch(url: str, timeout_seconds: float) -> bytes:
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
    _warm_up_session(url, timeout_seconds)
    parsed = urlparse(url)
    headers = dict(_BROWSER_HEADERS)
    if parsed.scheme and parsed.hostname:
        headers["Referer"] = f"{parsed.scheme}://{parsed.hostname}/"
    request = urllib.request.Request(url, headers=headers)
    # Bounded retries for transient retrieval failures (connection
    # resets, timeouts, HTTP 429/5xx): official document servers are
    # intermittently unavailable, and a single attempt turned a
    # transient failure into a permanent AWAITING_ISSUE_TERMS.
    last_exc: Optional[Exception] = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 (allow-listed hosts only)
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
        timeout_seconds: float = 60.0,
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
        url = _lookup_configured_url(self.urls_by_ipo, company_name, ipo_id)
        if not url:
            return None, ProviderReport(self.name, "UNAVAILABLE", "no official notice URL configured for this issuer")
        host = (urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts:
            return None, ProviderReport(self.name, "REJECTED", f"host {host or '?'} is not an official source host")
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
                result = PriceBandNoticeParser().parse_from_file(temp_path)
            finally:
                _best_effort_unlink(temp_path)
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
        timeout_seconds: float = 60.0,
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
        url = _lookup_configured_url(self.urls_by_ipo, company_name, ipo_id)
        if not url:
            return None, ProviderReport(self.name, "UNAVAILABLE", "no official prospectus URL configured for this issuer")
        host = (urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts:
            return None, ProviderReport(self.name, "REJECTED", f"host {host or '?'} is not an official source host")
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

    Outcomes: FOUND (verified candidate), NOT_FOUND (listings reached,
    no issuer-matched document published yet), UNAVAILABLE (listings
    unreachable -- transient; never evidence of non-publication).
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
        "https://www.sebi.gov.in/sebiweb/home/handleAction?doListing=yes&sid=1&ssid=7&smid=0",
    )
    _GENERIC_TOKENS = {"LIMITED", "INDIA", "PRIVATE", "COMPANY", "INDUSTRIES", "INDUSTRY", "GLOBAL", "INTERNATIONAL"}

    # Response-identity fingerprints.  An HTTP 200 is not a listing:
    # BSE serves its homepage (title carries the LIVE/SENSEX masthead)
    # to session-less requests, and its newer public-issues page is a
    # JavaScript shell.  Neither may count as a searched listing, and
    # neither is evidence that an issuer's terms are unpublished.
    _LISTING_MARKERS = (
        "displayipo", "issue-information", "issue_information",
        "public issues", "public issue", "security name", "attachdocs",
        "all-upcoming-issues", "price band",
    )
    _HOMEPAGE_MARKERS = ("bse sensex", "live stock/share market", "formerly bombay stock exchange")
    _SHELL_MARKERS = ("<app-root", "app-root>", "enable javascript to run this app", "you need to enable javascript")

    @classmethod
    def _classify_listing(cls, raw: bytes) -> str:
        """Classify a fetched listing response: ok | empty | homepage | shell.

        BSE pages share the homepage masthead in their chrome, so the
        homepage verdict requires the masthead AND the absence of any
        genuine issue content (issue-detail links, Price Band, Market
        Lot, Issue Period): a real DisplayIPO page carries the masthead
        title but is not the homepage.
        """
        text = raw.decode("utf-8", errors="ignore").lower()
        if any(marker in text for marker in cls._SHELL_MARKERS):
            return "shell"
        has_issue_links = any(
            marker in text
            for marker in ("displayipo", "issue-information", "issue_information")
        )
        has_issue_content = has_issue_links or any(
            marker in text for marker in ("price band", "market lot", "issue period")
        )
        if not has_issue_content and sum(marker in text for marker in cls._HOMEPAGE_MARKERS) >= 2:
            return "homepage"
        if has_issue_content or any(marker in text for marker in cls._LISTING_MARKERS):
            return "ok"
        return "empty"

    def __init__(
        self,
        fetcher: Optional[Callable[[str], bytes]] = None,
        allowed_hosts: Optional[set[str]] = None,
        listing_urls: Optional[Sequence[str]] = None,
        max_candidates: int = 6,
        timeout_seconds: float = 60.0,
    ):
        self.allowed_hosts = allowed_hosts if allowed_hosts is not None else set(OFFICIAL_HOSTS)
        self.listing_urls = list(listing_urls) if listing_urls is not None else list(self.LISTING_URLS)
        self.max_candidates = max_candidates
        self.timeout_seconds = timeout_seconds
        self._fetcher = fetcher

    def _fetch(self, url: str) -> bytes:
        if self._fetcher is not None:
            return self._fetcher(url)
        return _default_http_fetch(url, self.timeout_seconds)

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
        pairs: List[Tuple[str, str]] = []
        for match in re.finditer(r'href\s*=\s*"([^"]+)"[^>]*>(.*?)</a>', text, re.IGNORECASE | re.DOTALL):
            pairs.append((match.group(1), re.sub(r"<[^>]+>", " ", match.group(2))))
        for match in re.finditer(r"https?://[^\s\"<>]+?\.pdf\b", text, re.IGNORECASE):
            pairs.append((match.group(0), ""))
        seen = set()
        for href, anchor in pairs:
            url = urllib.parse.urljoin(base_url, href.strip())
            host = (urllib.parse.urlparse(url).hostname or "").lower()
            if host not in self.allowed_hosts:
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


    def _from_issue_page(self, url: str, company_name: str) -> tuple[Optional[NoticeCandidate], str]:
        """Fetch and parse an official exchange issue-information page.

        Returns (candidate, reason); reason names the exact failing
        stage when no candidate results, so a wrong-page (homepage)
        response is never conflated with an unpublished issue.
        """
        from .extraction.exchange_issue_page import ExchangeIssuePageParser

        host = (urllib.parse.urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts:
            return None, f"{url}: host is not an official source host"
        try:
            raw = self._fetch(url)
        except Exception as exc:
            return None, f"{url}: issue-page retrieval failed ({type(exc).__name__})"
        if not raw.lstrip()[:15].lower().startswith((b"<!doctype", b"<html", b"<")):
            return None, f"{url}: issue page returned a non-HTML response"
        if self._classify_listing(raw) == "homepage":
            return None, (
                f"{url}: issue page returned the exchange homepage instead of "
                "issue information (HTTP 200 wrong-page/session response)"
            )
        try:
            result = ExchangeIssuePageParser().parse(raw, url=url)
        except Exception as exc:
            return None, f"{url}: issue page could not be parsed ({type(exc).__name__})"
        if _norm_name(result.company_name) != _norm_name(company_name):
            return None, f"{url}: issue page names a different issuer"
        if result.price_band_low is None and result.lot_size is None:
            return None, f"{url}: issue page has no labelled Price Band or Market Lot"
        return NoticeCandidate(
            result=result,
            provider=self.name,
            uri=url,
            retrieved_at=_utcnow().isoformat().replace("+00:00", "Z"),
            raw_bytes=None,
            verified=True,
        ), ""

    @staticmethod
    def _merge_candidates(candidates: List[NoticeCandidate]) -> NoticeCandidate:
        """Fill missing pricing fields of the primary candidate from
        other verified, issuer-matched candidates (the resolver's
        conflict check still rejects disagreements).  Field objects
        keep their own quotes/locators; sources are recorded."""
        if len(candidates) == 1:
            return candidates[0]
        # A final Prospectus is the richest primary (it can also carry
        # the stated fresh-issue amount); otherwise first discovered.
        primary = next(
            (c for c in candidates if getattr(c.result, "document_class", "") == "OFFICIAL_PROSPECTUS"),
            candidates[0],
        )
        # Never merge disagreeing disclosures: surface the conflict
        # instead of arbitrarily preferring one source.
        for other in candidates[1:]:
            for field_name in ("price_band_low", "price_band_high", "lot_size"):
                left = getattr(primary.result, field_name, None)
                right = getattr(other.result, field_name, None)
                if left is not None and right is not None and float(left.value) != float(right.value):
                    raise ValueError(
                        f"conflicting official values for {field_name}: {left.value} ({primary.uri}) vs {right.value} ({other.uri})"
                    )
        merged_from = [primary.uri]
        for other in (c for c in candidates if c is not primary):
            filled = False
            for field_name in ("price_band_low", "price_band_high", "lot_size", "open_date", "close_date"):
                if getattr(primary.result, field_name, None) is None and getattr(other.result, field_name, None) is not None:
                    setattr(primary.result, field_name, getattr(other.result, field_name))
                    filled = True
            # A final Prospectus additionally carries the stated
            # fresh-issue amount; keep it reachable for enrichment.
            if getattr(other.result, "fresh_issue_amount", None) is not None and getattr(primary.result, "fresh_issue_amount", None) is None:
                primary.result.fresh_issue_amount = other.result.fresh_issue_amount  # type: ignore[attr-defined]
            if filled:
                merged_from.append(other.uri)
        if len(merged_from) > 1 and hasattr(primary.result, "metadata"):
            primary.result.metadata["merged_from"] = merged_from
        return primary

    def find(self, company_name: str, ipo_id: str) -> tuple[Optional[NoticeCandidate], ProviderReport]:
        reached = False
        notes: List[str] = []

        def note(text: str) -> None:
            if text and text not in notes and len(notes) < 6:
                notes.append(text)

        for listing_url in self.listing_urls:
            try:
                raw = self._fetch(listing_url)
            except Exception as exc:
                note(f"{listing_url}: listing retrieval failed ({type(exc).__name__})")
                continue
            kind = self._classify_listing(raw)
            if kind == "homepage":
                note(
                    f"{listing_url}: returned the exchange homepage, not an issue "
                    "listing (HTTP 200 wrong-page response; a listing was not searched)"
                )
                continue
            if kind == "shell":
                note(
                    f"{listing_url}: returned a JavaScript application shell with no "
                    "issue rows in the served HTML (a listing was not searched)"
                )
                continue
            reached = True
            collected: List[NoticeCandidate] = []
            for link in self._candidate_links(raw, listing_url, company_name):
                low = link.lower()
                if "displayipo" in low or "issue-information" in low or "issue_information" in low:
                    page_candidate, reason = self._from_issue_page(link, company_name)
                    if page_candidate is not None:
                        collected.append(page_candidate)
                    else:
                        note(reason)
                    continue
                for provider_cls in (HttpNoticeProvider, HttpProspectusProvider):
                    provider = provider_cls({ipo_id: link}, fetcher=self._fetcher, allowed_hosts=self.allowed_hosts, timeout_seconds=self.timeout_seconds)
                    candidate, _report = provider.find(company_name, ipo_id)
                    if candidate is not None:
                        collected.append(candidate)
                        break
            if collected:
                try:
                    merged = self._merge_candidates(collected)
                except ValueError as exc:
                    return None, ProviderReport(self.name, "REJECTED", str(exc))
                return merged, ProviderReport(
                    self.name, "FOUND", f"discovered official document via {listing_url}: {merged.uri}"
                )
        if reached:
            detail = (
                "official listings searched; no issuer-matched official document "
                "was found (this does not by itself establish non-publication)"
            )
            if notes:
                detail += "; " + "; ".join(notes)
            return None, ProviderReport(self.name, "NOT_FOUND", detail)
        return None, ProviderReport(
            self.name, "UNAVAILABLE",
            "no valid official listing could be retrieved: "
            + ("; ".join(notes) if notes else "no listing sources configured"),
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
    dirs = [d for d in os.getenv("IPO_PRICE_BAND_NOTICE_DIR", "").split(os.pathsep) if d]
    if dirs:
        providers.append(RetainedNoticeProvider(dirs))
    cache_dir = os.getenv("IPO_ISSUE_TERMS_CACHE_DIR")
    cache = NoticeSnapshotCache(cache_dir, ttl_hours=float(os.getenv("IPO_ISSUE_TERMS_CACHE_TTL_HOURS", "168"))) if cache_dir else None
    return IssueTermsResolver(providers=providers, cache=cache)
