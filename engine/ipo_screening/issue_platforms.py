"""Opt-in public investment-platform discovery. Candidates NEVER confer authority.

No private APIs, login flows, CAPTCHA bypass or guessed issuer URLs. Follow only
same-host links exposed by the configured public listing, bounded per provider.
"""
from __future__ import annotations

import re
import copy
from dataclasses import replace
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from .extraction.exchange_issue_page import ExchangeIssuePageParser, _strip_html

PLATFORM_LISTINGS = {
    "dhan": "https://dhan.co/ipo/",
    "groww": "https://groww.in/ipo",
    "angelone": "https://www.angelone.in/upcoming-ipo",
    "indmoney": "https://www.indmoney.com/ipo",
}


def _identity(text):
    text = re.sub(r"\b(?:ipo|limited|ltd)\b", "", text, flags=re.I)
    return "".join(c for c in text.lower() if c.isalnum())


def failure_kind(exc):
    code = getattr(exc, "code", None)
    if code in (401, 403):
        return "ACCESS_DENIED"
    if code == 429:
        return "RATE_LIMITED"
    if isinstance(exc, TimeoutError) or (isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError)):
        return "TIMEOUT"
    return "HTTP_ERROR" if code else "RETRIEVAL_FAILURE"


class PublicPlatformProvider:
    def __init__(self, name, fetcher=None, max_candidates=4):
        if name not in PLATFORM_LISTINGS:
            raise ValueError("unknown platform")
        self.name = name
        self.listing_url = PLATFORM_LISTINGS[name]
        self.fetcher = fetcher
        self.max_candidates = max_candidates

    def find(self, company_name, ipo_id):
        from .issue_terms import NoticeCandidate, ProviderReport, ListingAttempt, _default_http_fetch, _utcnow
        fetch = self.fetcher or (lambda url: _default_http_fetch(url, 15))
        attempts = []
        candidates = []
        try:
            listing = fetch(self.listing_url)
        except Exception as exc:
            kind = failure_kind(exc)
            return None, ProviderReport(self.name, "UNAVAILABLE", kind,
                sources=[ListingAttempt(self.listing_url, kind, detail=str(exc))])
        text = listing.decode("utf-8", errors="replace")
        if re.search(r"captcha|access denied|verify you are human|cloudflare challenge", _strip_html(listing), re.I):
            return None, ProviderReport(self.name, "UNAVAILABLE", "ACCESS_DENIED: no bypass attempted",
                sources=[ListingAttempt(self.listing_url, "ACCESS_DENIED")])
        links = []
        for m in re.finditer(r'''href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>''', text, re.I | re.S):
            anchor = re.sub(r"<[^>]*>", " ", m.group(2))
            # Exact legal-name match after only IPO/legal suffix normalization.
            if _identity(anchor.strip()) != _identity(company_name):
                continue
            link = urljoin(self.listing_url, m.group(1))
            if (urlparse(link).scheme == "https" and urlparse(link).hostname == urlparse(self.listing_url).hostname
                    and link not in links and link.rstrip('/') != self.listing_url.rstrip('/')):
                links.append(link)
        attempts.append(ListingAttempt(self.listing_url, "ok" if links else "UNUSABLE_OR_NO_MATCH",
                                       bool(links), len(links), "Only issuer-matched public links followed"))
        for url in links[:self.max_candidates]:
            try:
                raw = fetch(url)
                content = _strip_html(raw)
                if re.search(r"captcha|access denied|verify you are human", content, re.I):
                    attempts.append(ListingAttempt(url, "ACCESS_DENIED")); continue
                headings = re.findall(r"<h1[^>]*>(.*?)</h1>", raw.decode('utf-8', errors='replace'), re.I | re.S)
                if not any(_identity(re.sub(r"<[^>]+>", " ", h)) == _identity(company_name) for h in headings):
                    attempts.append(ListingAttempt(url, "IDENTITY_MISMATCH")); continue
                result = ExchangeIssuePageParser().parse(raw, url=url)
                result.company_name = company_name  # exact heading match above, not a guessed alias
                result.document_class = "INVESTMENT_PLATFORM_PAGE"
                result.metadata["document_class"] = result.document_class
                source_id = "SRC-PLATFORM-" + result.source_ref.content_hash[:8].upper()
                result.source = replace(result.source, source_id=source_id, source_type="MARKET_DATA")
                result.source_ref = replace(result.source_ref, source_id=source_id, source_type="MARKET_DATA")
                for name in ("price_band_low", "price_band_high", "lot_size", "open_date", "close_date", "fresh_issue_amount", "ofs_amount"):
                    field = getattr(result, name, None)
                    if field is not None:
                        setattr(result, name, replace(field, verification="UNVERIFIED", extraction_method="MARKET_DATA",
                            locator=(field.locator or "IPO detail").replace("Exchange issue information", "Public platform IPO detail")))
                if not any(getattr(result, f, None) is not None for f in ("price_band_low", "price_band_high", "lot_size", "open_date", "close_date", "ofs_amount", "fresh_issue_amount")):
                    kind = ("PARSE_FAILURE_OR_MALFORMED_TERMS" if re.search(
                        r"price\s*(?:band|range)|lot\s*size|fresh\s*issue|offer\s*for\s*sale", content, re.I)
                        else "NOT_DISCLOSED_IN_EXAMINED_CONTENT")
                    attempts.append(ListingAttempt(url, kind)); continue
                candidates.append(NoticeCandidate(result, self.name, url,
                    _utcnow().isoformat(), verified=False))
                attempts.append(ListingAttempt(url, "CANDIDATE", detail="Unverified platform values; official evidence still required"))
            except Exception as exc:
                attempts.append(ListingAttempt(url, failure_kind(exc), detail=str(exc)))
        report = ProviderReport(self.name, "FOUND" if candidates else "UNAVAILABLE",
                                "Public candidate discovery exhausted; not official verification", sources=attempts)
        if not candidates:
            return None, report
        first = copy.deepcopy(candidates[0])
        if len(candidates) > 1:
            first.components = list(candidates)
        return first, report
