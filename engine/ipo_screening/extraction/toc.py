"""Table of Contents (TOC) parsing and section-based page routing.

Indian RHP prospectuses follow the SEBI ICDR prescribed section layout.
Using the Table of Contents lets extraction target the specific 5-15 pages
containing a schedule rather than scanning all 500+ pages of the PDF.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pypdf


@dataclass(frozen=True)
class TOCEntry:
    title: str
    canonical_key: str
    printed_page: int
    pdf_page: int


# Mapping of canonical keys to regexes matching TOC entries
_SECTION_PATTERNS = (
    ("the_offer", re.compile(r"\bTHE\s+OFFER\b", re.IGNORECASE)),
    ("capital_structure", re.compile(r"\bCAPITAL\s+STRUCTURE\b", re.IGNORECASE)),
    ("objects_of_the_offer", re.compile(r"\bOBJECTS\s+OF\s+(?:THE\s+)?OFFER\b", re.IGNORECASE)),
    ("basis_for_offer_price", re.compile(r"\bBASIS\s+(?:FOR|OF)\s+(?:THE\s+)?OFFER\s+PRICE\b", re.IGNORECASE)),
    ("industry_overview", re.compile(r"\bINDUSTRY\s+OVERVIEW\b", re.IGNORECASE)),
    ("our_business", re.compile(r"\bOUR\s+BUSINESS\b", re.IGNORECASE)),
    ("our_management", re.compile(r"\bOUR\s+MANAGEMENT\b", re.IGNORECASE)),
    ("promoters", re.compile(r"\bOUR\s+PROMOTER(?:S|\s+AND\s+PROMOTER\s+GROUP)?\b", re.IGNORECASE)),
    ("restated_financials", re.compile(r"\b(?:RESTATED\s+)?FINANCIAL\s+STATEMENTS\b", re.IGNORECASE)),
    ("financial_indebtedness", re.compile(r"\b(?:FINANCIAL\s+INDEBTEDNESS|CAPITALISATION\s+STATEMENT)\b", re.IGNORECASE)),
    ("litigation", re.compile(r"\bOUTSTANDING\s+LITIGATION\b", re.IGNORECASE)),
    ("contingent_liabilities", re.compile(r"\bSUMMARY\s+OF\s+CONTINGENT\s+LIABILITIES\b", re.IGNORECASE)),
    ("related_party", re.compile(r"\bSUMMARY\s+OF\s+RELATED\s+PARTY\b", re.IGNORECASE)),
    ("offer_structure", re.compile(r"\bOFFER\s+STRUCTURE\b", re.IGNORECASE)),
)


class TOCRouter:
    """Detects and parses the Table of Contents, mapping sections to PDF pages."""

    def __init__(self, entries: Dict[str, TOCEntry], pdf_offset: int, page_count: int) -> None:
        self.entries = entries
        self.pdf_offset = pdf_offset
        self.page_count = page_count

    @classmethod
    def from_pdf(cls, reader: pypdf.PdfReader, max_scan_pages: int = 25) -> "TOCRouter":
        """Scan early pages for Table of Contents and build section router."""
        page_count = len(reader.pages)
        scan_limit = min(max_scan_pages, page_count)

        toc_text = ""
        toc_pdf_page = -1

        for i in range(scan_limit):
            try:
                text = reader.pages[i].extract_text() or ""
            except Exception:
                continue

            if (
                re.search(r"\bTABLE\s+OF\s+CONTENTS\b", text, re.IGNORECASE)
                or re.search(r"\bINDEX\b", text, re.IGNORECASE)
                or re.search(r"^\s*CONTENTS\s*$", text, re.IGNORECASE | re.MULTILINE)
            ):
                toc_text += "\n" + text
                if toc_pdf_page < 0:
                    toc_pdf_page = i + 1

        entries: Dict[str, TOCEntry] = {}
        pdf_offset = 0

        if toc_text:
            # Parse lines like: "CAPITAL STRUCTURE .......... 86"
            lines = toc_text.splitlines()
            line_pattern = re.compile(r"^\s*([A-Za-z\s–—\-:,]+?)\s*[\.\s…_-]{3,}\s*(\d+)\s*$")

            parsed_items: List[Tuple[str, int]] = []
            for line in lines:
                match = line_pattern.match(line)
                if match:
                    title, page_str = match.groups()
                    try:
                        p_num = int(page_str)
                        parsed_items.append((title.strip(), p_num))
                    except ValueError:
                        continue

            # Determine pdf_offset: In Indian prospectuses, page 1 begins shortly after TOC
            # Find the entry for page 1 (e.g. "SECTION I: GENERAL ... 1")
            first_page_entries = [p for _, p in parsed_items if p == 1]
            if first_page_entries and toc_pdf_page > 0:
                # Typically page 1 is the page immediately following TOC
                pdf_offset = toc_pdf_page

            # Match canonical keys
            for title, p_num in parsed_items:
                for key, pattern in _SECTION_PATTERNS:
                    if key not in entries and pattern.search(title):
                        if key == "the_offer" and re.search(r"\bSUMMARY\s+OF\b", title, re.IGNORECASE):
                            continue
                        # Approximate PDF page = printed page + offset
                        actual_pdf_page = min(p_num + pdf_offset, page_count)
                        entries[key] = TOCEntry(
                            title=title,
                            canonical_key=key,
                            printed_page=p_num,
                            pdf_page=actual_pdf_page,
                        )

        return cls(entries, pdf_offset, page_count)

    def get_page_range(self, section_key: str, default_span: int = 15) -> Tuple[int, int]:
        """Return 1-based (start_page, end_page) for a given section."""
        entry = self.entries.get(section_key)
        if not entry:
            # Fallback: full document or safe default
            return 1, min(self.page_count, 50)

        start = max(1, entry.pdf_page)
        # Find next section to bound end page
        all_pages = sorted(e.pdf_page for e in self.entries.values() if e.pdf_page > start)
        if all_pages:
            end = min(self.page_count, all_pages[0])
        else:
            end = min(self.page_count, start + default_span)

        return start, max(start, end)
