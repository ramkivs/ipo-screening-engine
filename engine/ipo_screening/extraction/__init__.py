"""Phase 5A Automated Extraction Package for IPO Screening Engine."""

from .builder import CanonicalInputBuilder
from .extractor import DocumentExtractor
from .financial_tables import FinancialTableExtractor
from .interfaces import (
    ExtractionReport,
    RawExtraction,
    SourceDocument,
)
from .numbers import (
    detect_currency_unit,
    is_undisclosed_marker,
    parse_indian_number,
)
from .ocr_adapter import (
    NoOpOcrAdapter,
    OcrAdapter,
    TesseractOcrAdapter,
    detect_scanned_page,
)
from .pdf_source import PDFSourceError, compute_file_sha256, load_pdf_source
from .sections import SectionExtractor
from .toc import TOCEntry, TOCRouter

__all__ = [
    "CanonicalInputBuilder",
    "DocumentExtractor",
    "ExtractionReport",
    "FinancialTableExtractor",
    "NoOpOcrAdapter",
    "OcrAdapter",
    "PDFSourceError",
    "RawExtraction",
    "SectionExtractor",
    "SourceDocument",
    "TOCEntry",
    "TOCRouter",
    "TesseractOcrAdapter",
    "compute_file_sha256",
    "detect_currency_unit",
    "detect_scanned_page",
    "is_undisclosed_marker",
    "load_pdf_source",
    "parse_indian_number",
]
