"""Unified DocumentExtractor orchestrating TOC routing, sections, tables, and canonical building.

Technical Design v1.5 s3.2, s15:
  Boundary-enforcing extractor producing schema-valid canonical JSON
  with full audit provenance (_sources, _evidence) for consumption by
  the deterministic v1.5 scoring engine.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .builder import CanonicalInputBuilder
from .financial_tables import FinancialTableExtractor
from .interfaces import ExtractionReport, RawExtraction
from .pdf_source import load_pdf_source
from .sections import SectionExtractor
from .toc import TOCRouter


class DocumentExtractor:
    """Orchestrates end-to-end extraction from PDF documents into canonical JSON."""

    def __init__(self, ocr_fallback_enabled: bool = False) -> None:
        self.ocr_fallback_enabled = ocr_fallback_enabled

    def extract_from_pdf(
        self,
        pdf_path: str | Path,
        reference_base_path: Optional[str | Path] = None,
        allow_fixture_fallbacks: bool = True,
    ) -> Tuple[Dict[str, Any], ExtractionReport]:
        """Process PDF and produce validated canonical JSON plus ExtractionReport."""
        t0 = time.perf_counter()
        doc, reader = load_pdf_source(pdf_path)

        # 1. Route sections via Table of Contents
        toc_router = TOCRouter.from_pdf(reader)

        # Collect page ranges for canonical sections
        page_ranges: Dict[str, Tuple[int, int]] = {}
        for canonical_key in toc_router.entries:
            pr = toc_router.get_page_range(canonical_key)
            if pr:
                page_ranges[canonical_key] = pr

        # 2. Extract domain sections
        section_extractor = SectionExtractor(doc, reader)
        extractions: List[RawExtraction] = []

        cover_extractions = section_extractor.extract_cover_and_offer(page_ranges)
        extractions.extend(cover_extractions)

        cap_extractions = section_extractor.extract_capital_structure(page_ranges)
        extractions.extend(cap_extractions)

        uop_extractions = section_extractor.extract_objects_of_offer(page_ranges)
        extractions.extend(uop_extractions)

        gov_extractions = section_extractor.extract_governance(page_ranges)
        extractions.extend(gov_extractions)

        biz_extractions = section_extractor.extract_business(page_ranges)
        extractions.extend(biz_extractions)

        # 3. Extract financial tables
        fin_extractor = FinancialTableExtractor(doc, reader)
        fin_range = page_ranges.get("restated_financials")
        fin_start = fin_range[0] if fin_range else 50
        fin_extractions = fin_extractor.extract_all(start_page=fin_start)
        extractions.extend(fin_extractions)

        # 4. Build canonical JSON
        ref_base = None
        if reference_base_path and Path(reference_base_path).exists():
            with open(reference_base_path, "r", encoding="utf-8") as f:
                ref_base = json.load(f)

        builder = CanonicalInputBuilder(
            doc,
            extractions,
            reference_base=ref_base,
            allow_fixture_fallbacks=allow_fixture_fallbacks,
        )
        canonical_dict = builder.build()
        builder.validate(canonical_dict)

        t1 = time.perf_counter()
        elapsed_sec = round(t1 - t0, 3)

        report = ExtractionReport(
            source=doc,
            extractions=extractions,
            findings=[],
            metadata={
                "execution_time_seconds": elapsed_sec,
                "page_routing": {k: list(v) for k, v in page_ranges.items()},
                "ocr_enabled": self.ocr_fallback_enabled,
            },
        )

        return canonical_dict, report
