"""Official exchange issue-information page parser.

Exchanges publish the live terms of an IPO on their issue-information
pages (e.g. BSE ``DisplayIPO``): price band, market lot and issue
period, on the exchange's own allow-listed host.  These pages are
official exchange publications of the price band, distinct from the
newspaper Price Band Notice and from a final Prospectus; the result
carries ``document_class = "EXCHANGE_ISSUE_PAGE"`` so provenance never
mislabels the source, while the field contract (``PriceBandField``)
matches the notice pathway.

Deterministic and fail-closed: only explicitly labelled values are
extracted; "Market Lot" is the lot size (never minimum bid quantity
or minimum investment); an unparseable page yields no fields.
"""

from __future__ import annotations

import hashlib
import html as html_module
import re
from datetime import datetime
from typing import Optional

from ..canonical import ExtractionMethod, SourceRef, SourceType, Verification
from .interfaces import SourceDocument
from .price_band_notice import PriceBandField, PriceBandNoticeResult

_MONTHS = "%d %B %Y|%d %b %Y".split("|")


def _strip_html(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = html_module.unescape(text)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _number(token: str) -> float:
    return float(token.replace(",", ""))


def _parse_date(token: str) -> Optional[str]:
    token = " ".join(token.replace(",", " ").split())
    for fmt in _MONTHS:
        try:
            return datetime.strptime(token, fmt).date().isoformat()
        except ValueError:
            continue
    return None


class ExchangeIssuePageParser:
    """Parse an official exchange issue-information page (HTML)."""

    def parse(self, raw: bytes, *, url: str) -> PriceBandNoticeResult:
        content_hash = hashlib.sha256(raw).hexdigest()
        source_id = f"SRC-EXCHANGE-{content_hash[:8].upper()}"
        source = SourceDocument(
            source_id=source_id,
            source_type=SourceType.EXCHANGE.value,
            uri=url,
            content_hash=content_hash,
        )
        source_ref = SourceRef(
            source_id=source_id,
            source_type=SourceType.EXCHANGE.value,
            uri=url,
            content_hash=content_hash,
        )
        text = _strip_html(raw)
        result = PriceBandNoticeResult(
            source=source,
            source_ref=source_ref,
            is_classified_notice=False,
            metadata={"document_class": "EXCHANGE_ISSUE_PAGE", "page_kind": "exchange_issue_information"},
        )
        result.document_class = "EXCHANGE_ISSUE_PAGE"  # resolver-level class

        band = re.search(
            r"price\s*band\D{0,30}?([\d,]+\.?\d*)\s*(?:-|–|—|to)\s*([\d,]+\.?\d*)",
            text,
            re.IGNORECASE,
        ) or re.search(
            r"offer\s*price\D{0,20}?([\d,]+\.?\d*)\s*(?:-|–|—)\s*([\d,]+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if band:
            low, high = _number(band.group(1)), _number(band.group(2))
            if 0 < low <= high:
                quote = band.group(0)
                result.price_band_low = PriceBandField(
                    name="price_band_low", value=low, raw_text=band.group(1),
                    locator="Exchange issue information - Price Band", quote=quote,
                    extraction_method=ExtractionMethod.EXCHANGE_DATA.value,
                    verification=Verification.VERIFIED.value, confidence=0.95,
                )
                result.price_band_high = PriceBandField(
                    name="price_band_high", value=high, raw_text=band.group(2),
                    locator="Exchange issue information - Price Band", quote=quote,
                    extraction_method=ExtractionMethod.EXCHANGE_DATA.value,
                    verification=Verification.VERIFIED.value, confidence=0.95,
                )
                result.collar_spread_pct = round((high - low) / low * 100, 4) if low else None
                result.collar_valid = True

        lot = re.search(r"market\s*lot\D{0,20}?(\d[\d,]*)", text, re.IGNORECASE)
        if lot:
            result.lot_size = PriceBandField(
                name="lot_size", value=int(_number(lot.group(1))), raw_text=lot.group(1),
                locator="Exchange issue information - Market Lot", quote=lot.group(0),
                extraction_method=ExtractionMethod.EXCHANGE_DATA.value,
                verification=Verification.VERIFIED.value, confidence=0.95,
            )

        period = re.search(
            r"issue\s*period\D{0,20}?(\d{1,2}\s+[A-Za-z]{3,9},?\s+20\d{2})\s*(?:to|-)\s*(\d{1,2}\s+[A-Za-z]{3,9},?\s+20\d{2})",
            text,
            re.IGNORECASE,
        )
        if period:
            open_iso, close_iso = _parse_date(period.group(1)), _parse_date(period.group(2))
            if open_iso:
                result.open_date = PriceBandField(
                    name="open_date", value=open_iso, raw_text=period.group(1),
                    locator="Exchange issue information - Issue Period", quote=period.group(0),
                    extraction_method=ExtractionMethod.EXCHANGE_DATA.value,
                    verification=Verification.VERIFIED.value, confidence=0.95,
                )
            if close_iso:
                result.close_date = PriceBandField(
                    name="close_date", value=close_iso, raw_text=period.group(2),
                    locator="Exchange issue information - Issue Period", quote=period.group(0),
                    extraction_method=ExtractionMethod.EXCHANGE_DATA.value,
                    verification=Verification.VERIFIED.value, confidence=0.95,
                )

        # Issuer identity: the shortest name-like LIMITED line preceding
        # the terms (exchange pages head the issue table with it).
        head = text[: band.start()] if band else text[:2000]
        names = [
            line.strip(" |")
            for line in head.splitlines()
            if re.search(r"\bLIMITED\b", line, re.IGNORECASE) and 2 <= len(line.split()) <= 7
        ]
        if names:
            result.company_name = min(names, key=len)
        return result
