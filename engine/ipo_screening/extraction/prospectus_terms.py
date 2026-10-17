"""Official Prospectus issue-term extraction (narrow, truthful pathway).

Authorized 2026-10-17 as a distinct official document class: a final
Prospectus filed on an official host (SEBI/exchange) may establish the
price-band floor, cap and bid lot for issue-term resolution. It is NOT
a Price Band Notice and is never labelled as one:

- source identity uses the ``SRC-PROSPECTUS-<content-hash>`` prefix
  (Price Band Notices use ``SRC-PBN-…``);
- the enrichment payload note is ``OFFICIAL_PROSPECTUS``;
- evidence locators read "Final Prospectus — … definition".

Fail-closed semantics mirror the notice parser: only terms the document
explicitly establishes are extracted; undisclosed (``[●]``) or ambiguous
terms stay ``None``. Documents that are not final prospectuses (Price
Band Notices, RHP/DRHP filings) are rejected by classification.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..canonical import ExtractionMethod, SourceRef, SourceType, Verification
from ..errors import EngineError, Finding
from .interfaces import SourceDocument
from .numbers import parse_indian_number
from .pdf_source import load_pdf_source
from .price_band_notice import PriceBandField


class ProspectusTermsError(EngineError):
    """Base exception for Prospectus term extraction failures."""


class ProspectusClassificationError(ProspectusTermsError):
    """Raised when a document cannot be established as a final Prospectus."""


@dataclass
class ProspectusTermsResult:
    """Issue terms established by an official final Prospectus."""

    source: SourceDocument
    source_ref: SourceRef
    is_classified_prospectus: bool
    company_name: Optional[str] = None
    cin: Optional[str] = None
    price_band_low: Optional[PriceBandField] = None
    price_band_high: Optional[PriceBandField] = None
    lot_size: Optional[PriceBandField] = None
    open_date: Optional[PriceBandField] = None
    close_date: Optional[PriceBandField] = None
    document_class: str = "OFFICIAL_PROSPECTUS"
    findings: List[Finding] = field(default_factory=list)

    def to_enrichment_dict(self, ipo_id: Optional[str] = None) -> Dict[str, Any]:
        """Phase 5E-shaped enrichment payload with truthful classification."""
        source_id = self.source_ref.source_id
        doc_id = ipo_id or (
            self.company_name.upper().replace(" ", "-") if self.company_name else "IPO"
        )
        sources_payload = [
            {
                "source_id": source_id,
                "source_type": self.source_ref.source_type,
                "uri": self.source_ref.uri or "",
                "content_hash": self.source_ref.content_hash or "",
                "source_timestamp": self.source_ref.source_timestamp or "",
                "note": "OFFICIAL_PROSPECTUS",
            }
        ]
        price_band_payload: Dict[str, Any] = {}
        for field_name in (
            "price_band_low",
            "price_band_high",
            "lot_size",
            "open_date",
            "close_date",
        ):
            field_obj: Optional[PriceBandField] = getattr(self, field_name)
            if field_obj is not None:
                price_band_payload[field_name] = field_obj.to_provenance_dict(source_id)
            else:
                price_band_payload[field_name] = {
                    "raw_value": None,
                    "normalized_value": None,
                    "source_id": source_id,
                    "extraction_method": ExtractionMethod.NOT_APPLICABLE.value,
                    "verification": Verification.UNVERIFIED.value,
                }
        as_of = (
            self.source_ref.source_timestamp
            or self.source_ref.retrieval_timestamp
            or "2026-10-05T12:00:00Z"
        )
        return {
            "contract_version": "1.0",
            "ipo_id": doc_id,
            "as_of": as_of,
            "sources": sources_payload,
            "price_band": price_band_payload,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_ref.source_id,
            "source_type": self.source_ref.source_type,
            "content_hash": self.source_ref.content_hash,
            "document_class": self.document_class,
            "is_classified_prospectus": self.is_classified_prospectus,
            "company_name": self.company_name,
            "cin": self.cin,
            "price_band_low": self.price_band_low.value if self.price_band_low else None,
            "price_band_high": self.price_band_high.value if self.price_band_high else None,
            "lot_size": self.lot_size.value if self.lot_size else None,
        }


_CIN_PATTERN = re.compile(r"\b[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}\b")
_PROSPECTUS_DATED = re.compile(
    r"Prospectus\s*\n?\s*Dated\s*:\s*[A-Z][a-z]+\s*\d{1,2},\s*\d{4}", re.IGNORECASE
)
_COMPANY_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9\s,\.\-&]+?\s+(?:LIMITED|LTD\.?))\b")

_FLOOR_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(
        r"minimum price of (?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]+)?)\s*per equity share.{0,80}?floor price",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"floor price[^0-9]{0,90}?being,?\s*(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]+)?)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"floor price\s*(?:is|:)?\s*(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
)
_CAP_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(
        r"maximum price of (?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]+)?)\s*per equity share.{0,80}?cap price",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"cap price[^0-9]{0,90}?being,?\s*(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]+)?)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"cap price\s*(?:is|:)?\s*(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
)
_LOT_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(r"[\"“”']?bid lot[\"“”']?\s*:?\s*([0-9,]+)\s*equity shares", re.IGNORECASE),
    re.compile(
        r"minimum bid lot[^0-9]{0,80}?([0-9,]+)\s*(?:equity\s+)?shares",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(r"bid lot\s+of\s+([0-9,]+)\s*equity shares", re.IGNORECASE),
)


def _quote_window(text: str, start: int, end: int, radius: int = 110) -> str:
    snippet = text[max(0, start - radius): end + radius].replace("\n", " ")
    return re.sub(r"\s+", " ", snippet).strip()


class ProspectusTermsParser:
    """Deterministic, fail-closed extractor for final-Prospectus terms."""

    def parse_from_file(
        self,
        file_path: str | Path,
        source_id: Optional[str] = None,
    ) -> ProspectusTermsResult:
        resolved = Path(file_path)
        if not resolved.exists():
            raise ProspectusTermsError(f"Prospectus file not found: {resolved}")
        raw_bytes = resolved.read_bytes()
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        resolved_source_id = source_id or f"SRC-PROSPECTUS-{content_hash[:8].upper()}"

        pages: List[Tuple[int, str]] = []
        if resolved.suffix.lower() == ".pdf":
            source_doc, reader = load_pdf_source(
                resolved,
                source_id=resolved_source_id,
                source_type=SourceType.EXCHANGE.value,
            )
            for idx, page in enumerate(reader.pages, start=1):
                pages.append((idx, page.extract_text() or ""))
        else:
            text = raw_bytes.decode("utf-8", errors="replace")
            source_doc = SourceDocument(
                source_id=resolved_source_id,
                source_type=SourceType.EXCHANGE.value,
                uri=str(resolved),
                content_hash=content_hash,
                file_size_bytes=len(raw_bytes),
                page_count=1,
            )
            pages = [(1, text)]
        return self.parse_document(source_doc, pages)

    def parse_from_text(
        self,
        text: str,
        filename: str = "prospectus.txt",
        source_id: Optional[str] = None,
    ) -> ProspectusTermsResult:
        raw_bytes = text.encode("utf-8")
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        source_doc = SourceDocument(
            source_id=source_id or f"SRC-PROSPECTUS-{content_hash[:8].upper()}",
            source_type=SourceType.EXCHANGE.value,
            uri=filename,
            content_hash=content_hash,
            file_size_bytes=len(raw_bytes),
            page_count=1,
        )
        return self.parse_document(source_doc, [(1, text)])

    def parse_document(
        self,
        source_doc: SourceDocument,
        pages: Sequence[Tuple[int, str]],
    ) -> ProspectusTermsResult:
        full_text = "\n".join(text for _, text in pages)
        cover_text = "\n".join(text for _, text in list(pages)[:2])

        # --- Classification: final Prospectus, not a notice, not an RHP ---
        if "red herring" in cover_text.lower():
            raise ProspectusClassificationError(
                "document is a Red Herring Prospectus / DRHP, not a final Prospectus"
            )
        if not _PROSPECTUS_DATED.search(full_text):
            raise ProspectusClassificationError(
                "no 'Prospectus Dated:' title marker found"
            )
        cin_match = _CIN_PATTERN.search(full_text)
        if not cin_match:
            raise ProspectusClassificationError(
                "no Corporate Identity Number found; cannot establish issuer identity"
            )
        company_name = self._extract_company_name(cover_text) or self._extract_company_name(full_text)
        if not company_name:
            raise ProspectusClassificationError("issuer company name not established")

        source_ref = SourceRef(
            source_id=source_doc.source_id,
            source_type=SourceType.EXCHANGE.value,
            uri=source_doc.uri,
            content_hash=source_doc.content_hash,
            source_timestamp=source_doc.source_timestamp,
            retrieval_timestamp=source_doc.retrieval_timestamp,
        )

        result = ProspectusTermsResult(
            source=source_doc,
            source_ref=source_ref,
            is_classified_prospectus=True,
            company_name=company_name,
            cin=cin_match.group(0),
        )
        result.price_band_low = self._extract_term(
            pages, _FLOOR_PATTERNS, "price_band_low", "Final Prospectus — 'Floor Price' definition"
        )
        result.price_band_high = self._extract_term(
            pages, _CAP_PATTERNS, "price_band_high", "Final Prospectus — 'Cap Price' definition"
        )
        result.lot_size = self._extract_term(
            pages, _LOT_PATTERNS, "lot_size", "Final Prospectus — 'Bid Lot' definition", integer=True
        )
        return result

    @staticmethod
    def _extract_company_name(text: str) -> Optional[str]:
        # Prefer a standalone cover line (the issuer name appears alone on
        # its own line); a free regex span can swallow preceding cover text.
        for line in text.splitlines():
            candidate = line.strip()
            if re.fullmatch(r"[A-Z0-9][A-Z0-9\s,\.\-&]*?(LIMITED|LTD\.?)", candidate):
                if not any(word in candidate for word in ("OFFER", "ISSUE", "PROSPECTUS")):
                    return re.sub(r"\s+", " ", candidate)
        match = _COMPANY_PATTERN.search(text)
        if match:
            return re.sub(r"\s+", " ", match.group(1).strip())
        return None

    @staticmethod
    def _extract_term(
        pages: Sequence[Tuple[int, str]],
        patterns: Sequence[re.Pattern[str]],
        name: str,
        locator: str,
        integer: bool = False,
    ) -> Optional[PriceBandField]:
        for page_num, text in pages:
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    value = parse_indian_number(match.group(1))
                    if value is None:
                        continue
                    if integer:
                        value = int(value)
                    return PriceBandField(
                        name=name,
                        value=value,
                        raw_text=match.group(0),
                        page=page_num,
                        locator=locator,
                        quote=_quote_window(text, match.start(), match.end()),
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        verification=Verification.VERIFIED.value,
                        confidence=0.95,
                    )
        return None
