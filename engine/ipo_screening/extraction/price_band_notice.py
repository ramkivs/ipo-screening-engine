"""Price Band Notice Ingestion & Validation.

Phase 5F: Price Band Notice Ingestion.

Implements the upstream Price Band Notice parser defined by Phase 5D and
producing the Phase 5E supplemental enrichment contract.

Key architectural invariants:
1. Source Classification:
   - Evaluates documents independently from RHP filings.
   - Generates SourceRef with source_type="EXCHANGE" and note="PRICE_BAND_NOTICE".
2. Deterministic SHA-256:
   - Computed from the actual source bytes.
3. Source Facts vs. Derived Quantities:
   - Extracts source facts only: Cap Price, Floor Price, Lot Size, Open Date, Close Date.
   - Zero dynamic share, EPS, or OFS derivations.
4. SEBI ICDR Price Collar Validation:
   - Validates that cap_price > floor_price and (cap_price - floor_price) / floor_price <= 0.20 (20%).
   - Exact Decimal arithmetic.
   - Invalid collar fails closed; never repairs or clamps numbers.
5. Strict Fail-Closed UNKNOWN Semantics:
   - Missing fields evaluate strictly to None (UNKNOWN).
   - Never defaulted to 0, false, or fixture values (208, 220, 68, 9.46, 85.33).
6. Contract Compatibility:
   - Output directly produces the Phase 5E supplemental enrichment contract representation
     (schema/supplemental-enrichment.v1.schema.json).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..canonical import ExtractionMethod, SourceRef, SourceType, Verification
from ..errors import EngineError, Finding, SEVERITY_ERROR, SEVERITY_WARNING
from .interfaces import SourceDocument
from .numbers import parse_indian_number
from .ocr_adapter import NoOpOcrAdapter, OcrAdapter, detect_scanned_page
from .pdf_source import compute_file_sha256, load_pdf_source

# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------


class PriceBandNoticeError(EngineError):
    """Base exception for Price Band Notice extraction and validation failures."""


class PriceBandNoticeClassificationError(PriceBandNoticeError):
    """Raised when an input document cannot be verified as a Price Band Notice."""


class PriceCollarValidationError(PriceBandNoticeError):
    """Raised when the price band violates SEBI ICDR collar regulations (cap <= floor or spread > 20%)."""


class PriceBandNoticeParseError(PriceBandNoticeError):
    """Raised when a notice document is unreadable, corrupted, or irreconcilably contradictory."""


# --------------------------------------------------------------------------
# Month Name Mapping for Indian IPO Notices
# --------------------------------------------------------------------------

_MONTH_NAMES: Mapping[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Regex to strip leading weekday names
_WEEKDAY_PREFIX_RE = re.compile(
    r"^(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)[,\s]+",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# Dataclasses
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PriceBandField:
    """An individual extracted price-band fact with evidence provenance."""

    name: str
    value: Any  # float, int, str, or None
    raw_text: Optional[str] = None
    page: Optional[int] = None
    locator: Optional[str] = None
    quote: Optional[str] = None
    extraction_method: str = ExtractionMethod.DETERMINISTIC_PDF.value
    verification: str = Verification.VERIFIED.value
    confidence: Optional[float] = 1.0

    def to_provenance_dict(self, source_id: str) -> Dict[str, Any]:
        """Convert to the Phase 5E supplemental-enrichment provenanceValue shape."""
        out: Dict[str, Any] = {
            "raw_value": self.value,
            "normalized_value": self.value,
            "source_id": source_id,
            "extraction_method": self.extraction_method,
            "verification": self.verification,
        }
        if self.name in ("price_band_high", "price_band_low"):
            out["unit"] = "INR"
        elif self.name == "lot_size":
            out["unit"] = "SHARES"

        if self.locator is not None:
            out["locator"] = self.locator
        if self.page is not None:
            out["page"] = self.page
        if self.quote is not None:
            out["quote"] = self.quote
        if self.confidence is not None:
            out["confidence"] = self.confidence
        return out


@dataclass
class PriceBandNoticeResult:
    """The complete result of ingesting and validating a Price Band Notice."""

    source: SourceDocument
    source_ref: SourceRef
    is_classified_notice: bool
    company_name: Optional[str] = None
    price_band_high: Optional[PriceBandField] = None
    price_band_low: Optional[PriceBandField] = None
    lot_size: Optional[PriceBandField] = None
    open_date: Optional[PriceBandField] = None
    close_date: Optional[PriceBandField] = None
    collar_spread_pct: Optional[float] = None
    collar_valid: Optional[bool] = None
    findings: List[Finding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_full_price_band(self) -> bool:
        return bool(
            self.price_band_high
            and self.price_band_high.value is not None
            and self.price_band_low
            and self.price_band_low.value is not None
        )

    @property
    def has_lot_size(self) -> bool:
        return bool(self.lot_size and self.lot_size.value is not None)

    @property
    def has_dates(self) -> bool:
        return bool(
            self.open_date
            and self.open_date.value is not None
            and self.close_date
            and self.close_date.value is not None
        )

    def to_enrichment_dict(self, ipo_id: Optional[str] = None) -> Dict[str, Any]:
        """Produce a complete Phase 5E supplemental enrichment document payload."""
        source_id = self.source_ref.source_id
        doc_id = ipo_id or (
            (self.company_name.upper().replace(" ", "-") if self.company_name else "IPO")
        )

        sources_payload = [
            {
                "source_id": self.source_ref.source_id,
                "source_type": self.source_ref.source_type,
                "uri": self.source_ref.uri or "",
                "content_hash": self.source_ref.content_hash or "",
                "source_timestamp": self.source_ref.source_timestamp or "",
                "note": "PRICE_BAND_NOTICE",
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
            "is_classified_notice": self.is_classified_notice,
            "company_name": self.company_name,
            "price_band_low": self.price_band_low.value if self.price_band_low else None,
            "price_band_high": self.price_band_high.value if self.price_band_high else None,
            "lot_size": self.lot_size.value if self.lot_size else None,
            "open_date": self.open_date.value if self.open_date else None,
            "close_date": self.close_date.value if self.close_date else None,
            "collar_spread_pct": self.collar_spread_pct,
            "collar_valid": self.collar_valid,
            "findings": [f.to_dict() for f in self.findings],
        }


# --------------------------------------------------------------------------
# Notice Classification Markers
# --------------------------------------------------------------------------

_NOTICE_TITLE_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(r"price\s+band\s+(?:notice|advertisement|announcement)", re.IGNORECASE),
    re.compile(r"pre-bid\s+advertisement", re.IGNORECASE),
    re.compile(r"notice\s+to\s+investors", re.IGNORECASE),
    re.compile(r"the\s+floor\s+price\s+and\s+(?:the\s+)?cap\s+price", re.IGNORECASE),
    re.compile(r"(?:corrigendum|addendum).*price\s+band", re.IGNORECASE),
    re.compile(r"bid/offer\s+period.*price\s+band", re.IGNORECASE),
    re.compile(r"initial\s+public\s+offering.*price\s+band", re.IGNORECASE),
    re.compile(r"price\s+band\s+determination", re.IGNORECASE),
)

_NOTICE_SEMANTIC_TOKENS: Sequence[str] = (
    "cap price",
    "floor price",
    "bid lot",
    "price band",
    "equity shares",
)


# --------------------------------------------------------------------------
# Price Band Notice Parser
# --------------------------------------------------------------------------


class PriceBandNoticeParser:
    """Deterministic, fail-closed parser for SEBI / Exchange Price Band Notices."""

    def __init__(self, ocr_adapter: Optional[OcrAdapter] = None) -> None:
        self.ocr_adapter = ocr_adapter or NoOpOcrAdapter()

    def parse_from_file(
        self,
        file_path: str | Path,
        source_id: Optional[str] = None,
    ) -> PriceBandNoticeResult:
        """Parse a Price Band Notice from a PDF or text file."""
        resolved = Path(file_path)
        if not resolved.exists():
            raise PriceBandNoticeParseError(f"Notice file not found: {resolved}")

        raw_bytes = resolved.read_bytes()
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        pages: List[Tuple[int, str]] = []

        if resolved.suffix.lower() == ".pdf":
            source_doc, reader = load_pdf_source(
                resolved,
                source_id=source_id or f"SRC-PBN-{content_hash[:8].upper()}",
                source_type=SourceType.EXCHANGE.value,
            )
            for idx, p in enumerate(reader.pages, start=1):
                p_text = p.extract_text() or ""
                pages.append((idx, p_text))

            # Check for scanned pages requiring OCR
            if all(len(p_text.strip()) < 50 for _, p_text in pages):
                if not isinstance(self.ocr_adapter, NoOpOcrAdapter):
                    ocr_pages = []
                    for idx, _ in pages:
                        ocr_text = self.ocr_adapter.extract_text(resolved, idx)
                        ocr_pages.append((idx, ocr_text))
                    pages = ocr_pages
        else:
            # Plain text circular
            text = raw_bytes.decode("utf-8", errors="replace")
            source_doc = SourceDocument(
                source_id=source_id or f"SRC-PBN-{content_hash[:8].upper()}",
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
        filename: str = "price_band_notice.txt",
        source_id: Optional[str] = None,
    ) -> PriceBandNoticeResult:
        """Parse a notice directly from a raw string."""
        raw_bytes = text.encode("utf-8")
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        source_doc = SourceDocument(
            source_id=source_id or f"SRC-PBN-{content_hash[:8].upper()}",
            source_type=SourceType.EXCHANGE.value,
            uri=filename,
            content_hash=content_hash,
            file_size_bytes=len(raw_bytes),
            page_count=1,
        )
        return self.parse_document(source_doc, [(1, text)])

    def parse_document(
        self, source_doc: SourceDocument, pages: Sequence[Tuple[int, str]]
    ) -> PriceBandNoticeResult:
        """Parse an established SourceDocument and pages into a structured notice result."""
        # Aggregate text across pages
        full_text = "\n".join(text for _, text in pages)
        findings: List[Finding] = []

        # 1. Document Classification
        is_notice, class_reason = self._classify_document(full_text)
        if not is_notice:
            raise PriceBandNoticeClassificationError(
                f"Document does not match Price Band Notice criteria: {class_reason}"
            )

        source_ref = SourceRef(
            source_id=source_doc.source_id,
            source_type=SourceType.EXCHANGE.value,
            uri=source_doc.uri,
            content_hash=source_doc.content_hash,
            source_timestamp=source_doc.source_timestamp,
            retrieval_timestamp=source_doc.retrieval_timestamp,
        )

        company_name = self._extract_company_name(full_text)

        # 2. Extract Price Band (Floor & Cap)
        floor_field, cap_field, price_findings = self._extract_price_band(pages)
        findings.extend(price_findings)

        # 3. Extract Lot Size
        lot_field, lot_findings = self._extract_lot_size(pages)
        findings.extend(lot_findings)

        # 4. Extract Issue Dates (Open & Close)
        open_field, close_field, date_findings = self._extract_dates(pages)
        findings.extend(date_findings)

        # 5. SEBI ICDR Price Collar Validation
        collar_valid: Optional[bool] = None
        spread_pct: Optional[float] = None

        if (
            floor_field
            and floor_field.value is not None
            and cap_field
            and cap_field.value is not None
        ):
            floor_val = float(floor_field.value)
            cap_val = float(cap_field.value)
            collar_valid, spread_pct, collar_err = self._validate_collar(
                floor_val, cap_val
            )
            if not collar_valid:
                findings.append(
                    Finding(
                        code="INVALID_PRICE_COLLAR",
                        message=collar_err or "Price collar violates SEBI ICDR regulations",
                        severity=SEVERITY_ERROR,
                        scope="price_band_notice",
                        location="price_band",
                    )
                )
                raise PriceCollarValidationError(collar_err)

        return PriceBandNoticeResult(
            source=source_doc,
            source_ref=source_ref,
            is_classified_notice=True,
            company_name=company_name,
            price_band_high=cap_field,
            price_band_low=floor_field,
            lot_size=lot_field,
            open_date=open_field,
            close_date=close_field,
            collar_spread_pct=spread_pct,
            collar_valid=collar_valid,
            findings=findings,
            metadata={"full_text_length": len(full_text)},
        )

    # ----------------------------------------------------------------------
    # Classification Logic
    # ----------------------------------------------------------------------

    def _classify_document(self, text: str) -> Tuple[bool, str]:
        """Verify whether document contains authoritative Price Band Notice indicators."""
        clean_text = text.lower()

        # Check for title / header markers
        has_title = any(pattern.search(text) for pattern in _NOTICE_TITLE_PATTERNS)

        # Count semantic token presence
        token_count = sum(1 for token in _NOTICE_SEMANTIC_TOKENS if token in clean_text)

        if has_title and token_count >= 2:
            return True, "Authoritative title and semantic price tokens matched"
        if token_count >= 4:
            return True, "Strong semantic price band token match"

        return False, f"Missing notice header or insufficient tokens (tokens found: {token_count})"

    # ----------------------------------------------------------------------
    # Company Name Extraction
    # ----------------------------------------------------------------------

    def _extract_company_name(self, text: str) -> Optional[str]:
        m = re.search(
            r"(?:INITIAL\s+PUBLIC\s+OFFERING\s+OF|OFFER\s+BY|NOTICE\s+OF)\s+([A-Z0-9\s,\.\-&]+?)\s+(?:LIMITED|LTD)",
            text,
            re.IGNORECASE,
        )
        if m:
            name = m.group(1).strip() + " LIMITED"
            return re.sub(r"\s+", " ", name)
        # Alternate match
        m2 = re.search(r"\b([A-Z][A-Za-z0-9\s,\.\-&]+?\s+(?:LIMITED|LTD\.?))\b", text)
        if m2:
            return re.sub(r"\s+", " ", m2.group(1).strip())
        return None

    # ----------------------------------------------------------------------
    # Price Band Extraction (Cap & Floor)
    # ----------------------------------------------------------------------

    def _extract_price_band(
        self, pages: Sequence[Tuple[int, str]]
    ) -> Tuple[Optional[PriceBandField], Optional[PriceBandField], List[Finding]]:
        findings: List[Finding] = []
        candidates: List[Tuple[float, float, int, str, str]] = []

        # Regex patterns enforcing negative lookahead against corrupted OCR glyphs / characters
        pat_fc = re.compile(
            r"floor\s+price\s+(?:is\s+)?(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]+)?)(?![A-Za-z0-9?@#*]).*?cap\s+price\s+(?:is\s+)?(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]+)?)(?![A-Za-z0-9?@#*])",
            re.IGNORECASE | re.DOTALL,
        )
        pat_range = re.compile(
            r"price\s+band\s+(?:is\s+)?(?:of\s+)?(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]+)?)(?![A-Za-z0-9?@#*])\s*to\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]+)?)(?![A-Za-z0-9?@#*])",
            re.IGNORECASE,
        )
        pat_lu = re.compile(
            r"lower\s+end[^\n]*?(?:is\s+)?(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]+)?)(?![A-Za-z0-9?@#*]).*?upper\s+end[^\n]*?(?:is\s+)?(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]+)?)(?![A-Za-z0-9?@#*])",
            re.IGNORECASE | re.DOTALL,
        )
        pat_sep_floor = re.compile(
            r"floor\s+price\s*(?:is\s+|[:\-])?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]+)?)(?![A-Za-z0-9?@#*])",
            re.IGNORECASE,
        )
        pat_sep_cap = re.compile(
            r"cap\s+price\s*(?:is\s+|[:\-])?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]+)?)(?![A-Za-z0-9?@#*])",
            re.IGNORECASE,
        )

        # Scan each page
        for page_num, text in pages:
            # Pattern A: Explicit Floor and Cap sentences
            m_fc = pat_fc.search(text)
            if m_fc:
                f_val = parse_indian_number(m_fc.group(1))
                c_val = parse_indian_number(m_fc.group(2))
                if f_val and c_val:
                    quote = m_fc.group(0)[:120]
                    candidates.append((f_val, c_val, page_num, quote, "Explicit Floor and Cap phrase"))

            # Pattern B: Range phrase: "Price Band of Rs. X to Rs. Y"
            m_range = pat_range.search(text)
            if m_range:
                f_val = parse_indian_number(m_range.group(1))
                c_val = parse_indian_number(m_range.group(2))
                if f_val and c_val:
                    quote = m_range.group(0)
                    candidates.append((f_val, c_val, page_num, quote, "Price Band range phrase"))

            # Pattern C: Lower end and Upper end
            m_lu = pat_lu.search(text)
            if m_lu:
                f_val = parse_indian_number(m_lu.group(1))
                c_val = parse_indian_number(m_lu.group(2))
                if f_val and c_val:
                    quote = m_lu.group(0)[:120]
                    candidates.append((f_val, c_val, page_num, quote, "Lower and Upper end phrase"))

            # Pattern D: Separate Floor Price line and Cap Price line
            floor_match = pat_sep_floor.search(text)
            cap_match = pat_sep_cap.search(text)
            if floor_match and cap_match:
                f_val = parse_indian_number(floor_match.group(1))
                c_val = parse_indian_number(cap_match.group(1))
                if f_val and c_val:
                    quote = f"Floor: {floor_match.group(0)}, Cap: {cap_match.group(0)}"
                    candidates.append((f_val, c_val, page_num, quote, "Separate Floor and Cap lines"))

        if not candidates:
            # Check if isolated Cap or Floor exists
            isolated_floor = None
            isolated_cap = None
            for page_num, text in pages:
                if not isolated_cap:
                    c_m = pat_sep_cap.search(text)
                    if c_m:
                        val = parse_indian_number(c_m.group(1))
                        if val:
                            isolated_cap = PriceBandField(
                                name="price_band_high",
                                value=val,
                                raw_text=c_m.group(1),
                                page=page_num,
                                locator=f"Page {page_num}, 'Cap Price'",
                                quote=c_m.group(0),
                            )
                if not isolated_floor:
                    f_m = pat_sep_floor.search(text)
                    if f_m:
                        val = parse_indian_number(f_m.group(1))
                        if val:
                            isolated_floor = PriceBandField(
                                name="price_band_low",
                                value=val,
                                raw_text=f_m.group(1),
                                page=page_num,
                                locator=f"Page {page_num}, 'Floor Price'",
                                quote=f_m.group(0),
                            )

            return isolated_floor, isolated_cap, findings

        # Check for multiple conflicting candidates (Case H)
        unique_pairs = set((c[0], c[1]) for c in candidates)
        if len(unique_pairs) > 1:
            findings.append(
                Finding(
                    code="CONFLICTING_PRICE_BANDS",
                    message=f"Multiple conflicting price band candidates found: {list(unique_pairs)}",
                    severity=SEVERITY_ERROR,
                    scope="price_band_notice",
                    location="price_band",
                )
            )
            raise PriceBandNoticeParseError(
                f"Multiple conflicting price band pairs found in notice: {list(unique_pairs)}"
            )

        # Single authoritative pair
        floor_val, cap_val, page_num, quote, pattern_desc = candidates[0]

        floor_field = PriceBandField(
            name="price_band_low",
            value=floor_val,
            raw_text=str(floor_val),
            page=page_num,
            locator=f"Page {page_num}, 'Price Band Floor'",
            quote=quote,
            extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
            verification=Verification.VERIFIED.value,
        )

        cap_field = PriceBandField(
            name="price_band_high",
            value=cap_val,
            raw_text=str(cap_val),
            page=page_num,
            locator=f"Page {page_num}, 'Price Band Cap'",
            quote=quote,
            extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
            verification=Verification.VERIFIED.value,
        )

        return floor_field, cap_field, findings

    # ----------------------------------------------------------------------
    # Lot Size Extraction
    # ----------------------------------------------------------------------

    def _extract_lot_size(
        self, pages: Sequence[Tuple[int, str]]
    ) -> Tuple[Optional[PriceBandField], List[Finding]]:
        findings: List[Finding] = []
        candidates: List[Tuple[int, int, str]] = []

        patterns: Sequence[re.Pattern[str]] = (
            re.compile(
                r"(?:minimum\s+)?bid\s+lot\s*(?:is|of|[:\-])?\s*([0-9,]+)(?![A-Za-z0-9?@#*])\s*(?:equity\s+)?shares",
                re.IGNORECASE,
            ),
            re.compile(
                r"market\s+lot\s*(?:is|of|[:\-])?\s*([0-9,]+)(?![A-Za-z0-9?@#*])\s*(?:equity\s+)?shares",
                re.IGNORECASE,
            ),
            re.compile(
                r"lot\s+size\s*(?:is|of|[:\-])?\s*([0-9,]+)(?![A-Za-z0-9?@#*])\s*(?:equity\s+)?shares",
                re.IGNORECASE,
            ),
            re.compile(
                r"minimum\s+of\s+([0-9,]+)(?![A-Za-z0-9?@#*])\s+equity\s+shares\s+and\s+in\s+multiples",
                re.IGNORECASE,
            ),
            re.compile(
                r"one\s+lot\s+consists\s+of\s+([0-9,]+)(?![A-Za-z0-9?@#*])\s+(?:equity\s+)?shares",
                re.IGNORECASE,
            ),
            re.compile(
                r"bids\s+can\s+be\s+made\s+for\s+a\s+minimum\s+of\s+([0-9,]+)(?![A-Za-z0-9?@#*])\s+equity\s+shares",
                re.IGNORECASE,
            ),
        )

        for page_num, text in pages:
            for pat in patterns:
                for match in pat.finditer(text):
                    num = parse_indian_number(match.group(1))
                    if num is not None and num > 0 and float(num).is_integer():
                        candidates.append((int(num), page_num, match.group(0)))

        if not candidates:
            return None, findings

        unique_lots = set(c[0] for c in candidates)
        if len(unique_lots) > 1:
            findings.append(
                Finding(
                    code="CONFLICTING_LOT_SIZES",
                    message=f"Multiple conflicting lot sizes found: {list(unique_lots)}",
                    severity=SEVERITY_ERROR,
                    scope="price_band_notice",
                    location="price_band.lot_size",
                )
            )
            raise PriceBandNoticeParseError(
                f"Multiple conflicting lot sizes found in notice: {list(unique_lots)}"
            )

        lot_val, page_num, quote = candidates[0]
        lot_field = PriceBandField(
            name="lot_size",
            value=lot_val,
            raw_text=str(lot_val),
            page=page_num,
            locator=f"Page {page_num}, 'Minimum Bid Lot'",
            quote=quote,
            extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
            verification=Verification.VERIFIED.value,
        )
        return lot_field, findings

    # ----------------------------------------------------------------------
    # Date Extraction (Open & Close)
    # ----------------------------------------------------------------------

    def _extract_dates(
        self, pages: Sequence[Tuple[int, str]]
    ) -> Tuple[Optional[PriceBandField], Optional[PriceBandField], List[Finding]]:
        findings: List[Finding] = []
        open_candidates: List[Tuple[str, int, str]] = []
        close_candidates: List[Tuple[str, int, str]] = []

        open_patterns: Sequence[re.Pattern[str]] = (
            re.compile(
                r"(?:bid/offer|issue|bid/issue|offer|bid)\s+opens\s*(?:on\s*)?[:\-]?\s*([^\n\r]+)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:bid/offer|issue|bid/issue|offer|bid)\s+opening\s+date\s*[:\-]?\s*([^\n\r]+)",
                re.IGNORECASE,
            ),
            re.compile(
                r"opening\s+date\s*[:\-]?\s*([^\n\r]+)",
                re.IGNORECASE,
            ),
        )

        close_patterns: Sequence[re.Pattern[str]] = (
            re.compile(
                r"(?:bid/offer|issue|bid/issue|offer|bid)\s+closes\s*(?:on\s*)?[:\-]?\s*([^\n\r]+)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:bid/offer|issue|bid/issue|offer|bid)\s+closing\s+date\s*[:\-]?\s*([^\n\r]+)",
                re.IGNORECASE,
            ),
            re.compile(
                r"closing\s+date\s*[:\-]?\s*([^\n\r]+)",
                re.IGNORECASE,
            ),
        )

        for page_num, text in pages:
            # Scan open dates
            for pat in open_patterns:
                for match in pat.finditer(text):
                    date_str = self._normalize_date_string(match.group(1))
                    if date_str:
                        open_candidates.append((date_str, page_num, match.group(0)))

            # Scan close dates
            for pat in close_patterns:
                for match in pat.finditer(text):
                    date_str = self._normalize_date_string(match.group(1))
                    if date_str:
                        close_candidates.append((date_str, page_num, match.group(0)))

        open_field: Optional[PriceBandField] = None
        close_field: Optional[PriceBandField] = None

        if open_candidates:
            unique_opens = set(c[0] for c in open_candidates)
            if len(unique_opens) > 1:
                findings.append(
                    Finding(
                        code="CONFLICTING_OPEN_DATES",
                        message=f"Multiple conflicting issue open dates: {list(unique_opens)}",
                        severity=SEVERITY_ERROR,
                        scope="price_band_notice",
                        location="price_band.open_date",
                    )
                )
                raise PriceBandNoticeParseError(f"Conflicting open dates: {list(unique_opens)}")
            val, pg, q = open_candidates[0]
            open_field = PriceBandField(
                name="open_date",
                value=val,
                raw_text=val,
                page=pg,
                locator=f"Page {pg}, 'Bid Opening Date'",
                quote=q,
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                verification=Verification.VERIFIED.value,
            )

        if close_candidates:
            unique_closes = set(c[0] for c in close_candidates)
            if len(unique_closes) > 1:
                findings.append(
                    Finding(
                        code="CONFLICTING_CLOSE_DATES",
                        message=f"Multiple conflicting issue close dates: {list(unique_closes)}",
                        severity=SEVERITY_ERROR,
                        scope="price_band_notice",
                        location="price_band.close_date",
                    )
                )
                raise PriceBandNoticeParseError(f"Conflicting close dates: {list(unique_closes)}")
            val, pg, q = close_candidates[0]
            close_field = PriceBandField(
                name="close_date",
                value=val,
                raw_text=val,
                page=pg,
                locator=f"Page {pg}, 'Bid Closing Date'",
                quote=q,
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                verification=Verification.VERIFIED.value,
            )

        # Validate open_date <= close_date
        if open_field and close_field:
            if open_field.value > close_field.value:
                findings.append(
                    Finding(
                        code="INVALID_ISSUE_DATE_ORDER",
                        message=f"Issue open date ({open_field.value}) is after close date ({close_field.value})",
                        severity=SEVERITY_ERROR,
                        scope="price_band_notice",
                        location="price_band",
                    )
                )
                raise PriceBandNoticeParseError(
                    f"Open date {open_field.value} is after close date {close_field.value}"
                )

        return open_field, close_field, findings

    def _normalize_date_string(self, raw_str: str) -> Optional[str]:
        """Convert varied Indian notice date formulations into standard YYYY-MM-DD."""
        text = _WEEKDAY_PREFIX_RE.sub("", raw_str.strip()).strip()

        # 1. Match YYYY-MM-DD
        m = re.search(r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b", text)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

        # 2. Match DD-MM-YYYY or DD/MM/YYYY
        m = re.search(r"\b(0[1-9]|[12]\d|3[01])[-/](0[1-9]|1[0-2])[-/](20\d{2})\b", text)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

        # 3. Match DD-[A-Za-z]{3,9}-YYYY (e.g. 12-Nov-2026 or 12/Nov/2026)
        m = re.search(r"\b(0?[1-9]|[12]\d|3[01])[-/]([A-Za-z]{3,9})[-/](20\d{2})\b", text)
        if m:
            day = int(m.group(1))
            mon_key = m.group(2).lower()
            year = int(m.group(3))
            if mon_key in _MONTH_NAMES:
                return f"{year:04d}-{_MONTH_NAMES[mon_key]:02d}-{day:02d}"

        # 4. Match DD(th) Month YYYY (e.g. 10th October 2026 or 6 October, 2026)
        m = re.search(
            r"\b(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?\s+([A-Za-z]+)[,\s]+(20\d{2})\b",
            text,
        )
        if m:
            day = int(m.group(1))
            mon_key = m.group(2).lower()
            year = int(m.group(3))
            if mon_key in _MONTH_NAMES:
                return f"{year:04d}-{_MONTH_NAMES[mon_key]:02d}-{day:02d}"

        # 5. Match Month DD(th)?, YYYY (e.g. October 06, 2026)
        m = re.search(
            r"\b([A-Za-z]+)\s+(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?[,\s]+(20\d{2})\b",
            text,
        )
        if m:
            mon_key = m.group(1).lower()
            day = int(m.group(2))
            year = int(m.group(3))
            if mon_key in _MONTH_NAMES:
                return f"{year:04d}-{_MONTH_NAMES[mon_key]:02d}-{day:02d}"

        return None

    # ----------------------------------------------------------------------
    # SEBI ICDR Price Collar Validation
    # ----------------------------------------------------------------------

    def _validate_collar(
        self, floor: float, cap: float
    ) -> Tuple[bool, Optional[float], Optional[str]]:
        """Validate SEBI Regulation 127 price band collar constraints using exact Decimal."""
        try:
            f = Decimal(str(floor))
            c = Decimal(str(cap))
        except (InvalidOperation, ValueError, TypeError) as exc:
            return False, None, f"Malformed numeric values in price band: floor={floor}, cap={cap}"

        if f <= Decimal("0") or c <= Decimal("0"):
            return False, None, f"Floor ({floor}) and cap ({cap}) must be strictly positive"

        if c <= f:
            return (
                False,
                None,
                f"Cap price (₹{cap}) must be strictly greater than floor price (₹{floor})",
            )

        spread = (c - f) / f
        spread_pct = float(spread * 100)

        # SEBI Regulation 127: cap shall not be more than 120% of floor (spread <= 20%)
        # Exact decimal arithmetic: 0.20
        if spread > Decimal("0.20"):
            return (
                False,
                spread_pct,
                f"Cap price (₹{cap}) exceeds floor price (₹{floor}) by {spread_pct:.2f}%, violating the SEBI ICDR 20% collar limit",
            )

        return True, spread_pct, None


__all__ = [
    "PriceBandNoticeError",
    "PriceBandNoticeClassificationError",
    "PriceCollarValidationError",
    "PriceBandNoticeParseError",
    "PriceBandField",
    "PriceBandNoticeResult",
    "PriceBandNoticeParser",
]
