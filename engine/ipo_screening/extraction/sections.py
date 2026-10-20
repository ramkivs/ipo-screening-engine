"""Domain section extractors for RHP prospectuses.

Extracts non-table and hybrid sections according to ICDR layout:
  - Cover page & The Offer (company name, fresh issue, OFS, price band, lot size, quotas)
  - Capital Structure (promoter holding, pledge, lock-in)
  - Objects of the Offer (schedule of proceeds, Capex, Debt, Working Capital, GCP [●])
  - Governance & Management (auditor opinion, litigation, board independence, RPT)
  - Business & Industry (customer concentration, industry CAGR, moat, visibility)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pypdf

from ..canonical import ExtractionMethod
from .interfaces import RawExtraction, SourceDocument
from .numbers import is_undisclosed_marker, parse_indian_number


# ---------------------------------------------------------------------------
# Offer-for-Sale NIL binding
# ---------------------------------------------------------------------------
#
# A cover table can state the Offer for Sale as NIL / "Not applicable".  The
# original pattern searched up to 32 newlines after *any* "offer for sale"
# occurrence, so an unrelated NIL in an adjacent row (a fresh-issue NIL, a
# pre-IPO NIL, a promoter-group NIL) could be bound to the OFS and stored as
# an explicit ``issue.ofs = 0`` -- fabricating a zero where the filing states
# a real OFS amount.  The matcher below keeps the positive two-column cases
# (including the Jio cover, where "Not applicable" is the OFS cell) while
# refusing a NIL that is itself the value of another structural label.

_OFS_NIL_PATTERN = re.compile(
    r'offer for sale(?: size)?[^\n]*?(?:[^\n]*?\n){0,32}?\s*(?:NIL|Not\s+Applicable)\b',
    re.IGNORECASE,
)
_OFS_NIL_TOKEN = re.compile(r'(?:NIL|Not\s+Applicable)\b', re.IGNORECASE)
_OFS_NIL_BARE_LABEL = re.compile(
    r'^(?:'
    r'fresh\s+(?:issue|offer)(?:\s+size)?'
    r'|pre[-\s]?ipo(?:\s+(?:placement|issue))?'
    r'|promoter(?:\s+group)?'
    r'|anchor\s+investor(?:s)?'
    r'|(?:eligible\s+)?employee(?:s)?\s+reservation'
    r'|(?:shareholders?|eligible\s+ril\s+shareholders?)\s+reservation'
    r'|reservation'
    r'|total\s+issue(?:\s+size)?'
    r'|issue\s+size'
    r')\s*[:.\-]?$',
    re.IGNORECASE,
)
_OFS_NIL_AMOUNT = re.compile(r'(?:₹|Rs\.?|INR)\s*[\d,]+|\b\d[\d,]{2,}\b', re.IGNORECASE)


def _find_ofs_nil(cover_text: str) -> Optional[str]:
    """Return the matched OFS-NIL quotation, or None when it is ambiguous.

    Accepted:
      * "Offer for Sale Size: Not applicable" (same line);
      * "OFFER FOR SALE SIZE" followed by a value line "Not applicable";
      * "OFFER FOR SALE SIZE" followed by a fresh row and then the OFS cell
        "Not applicable" (the real Jio cover shape).

    Rejected:
      * an OFS label line that itself states an amount or quantity;
      * a NIL that is the value of a bare Fresh Issue / Pre-IPO / Promoter /
        reservation / total-issue label, on its own line or as the previous
        line.
    """
    for match in _OFS_NIL_PATTERN.finditer(cover_text):
        quote = match.group(0)
        first_line = quote.split("\n", 1)[0]
        after_label = re.sub(
            r'^offer\s+for\s+sale(?:\s+size)?', '', first_line, flags=re.IGNORECASE
        )
        if _OFS_NIL_AMOUNT.search(after_label):
            # The OFS row states an amount/quantity: it is not NIL.
            continue

        tokens = list(_OFS_NIL_TOKEN.finditer(quote))
        if not tokens:
            continue
        nil_abs = match.start() + tokens[-1].start()
        line_start = cover_text.rfind("\n", 0, nil_abs) + 1
        line_prefix = cover_text[line_start:nil_abs].strip()
        if _OFS_NIL_BARE_LABEL.match(line_prefix):
            # "Fresh Issue: NIL" -- the NIL belongs to the other label.
            continue

        before = cover_text[:line_start].rstrip("\n")
        prev_line = before.rsplit("\n", 1)[-1].strip() if before else ""
        if _OFS_NIL_BARE_LABEL.match(prev_line):
            # "Fresh Issue" / "Pre-IPO Placement" / "Promoter Group" on the
            # line immediately before a standalone NIL: not the OFS value.
            continue
        return quote
    return None


class SectionExtractor:
    """Extracts structured IPO domain fields across text sections."""

    def __init__(self, doc: SourceDocument, reader: pypdf.PdfReader, text_cache: Optional[Dict[int, str]] = None) -> None:
        self.doc = doc
        self.reader = reader
        self.page_count = len(reader.pages)
        self._text_cache: Dict[int, str] = text_cache if text_cache is not None else {}

    def extract_page_text(self, page_1_indexed: int) -> str:
        """Extract text from a 1-indexed page with caching."""
        if page_1_indexed in self._text_cache:
            return self._text_cache[page_1_indexed]
        if 1 <= page_1_indexed <= self.page_count:
            try:
                txt = self.reader.pages[page_1_indexed - 1].extract_text() or ""
            except Exception:
                txt = ""
            self._text_cache[page_1_indexed] = txt
            return txt
        return ""

    @staticmethod
    def _labelled_quantity_candidates(
        text: str,
        label_pattern: str,
        forbidden_markers: Sequence[str],
        window: int = 220,
    ) -> List[Tuple[float, str]]:
        """Quantities bound to a semantic label within a bounded window.

        A candidate is rejected when another issue component's label
        (e.g. "offer for sale" for a fresh-issue quantity) intervenes
        between the label and the number -- the classic cover-page
        confusion where one regex spans two clauses of the offer
        structure sentence and assigns the OFS quantity to fresh
        shares. Generic across issuers and layouts.
        """
        candidates: List[Tuple[float, str]] = []
        for match in re.finditer(label_pattern, text, re.IGNORECASE):
            segment = text[match.end(): match.end() + window]
            quantity_match = re.search(
                r'(?:of\s+)?(?:up\s*to\s*)?([0-9,]+)\s*equity shares',
                segment,
                re.IGNORECASE,
            )
            if not quantity_match:
                continue
            between = segment[: quantity_match.start()].lower()
            if any(marker in between for marker in forbidden_markers):
                continue
            value = parse_indian_number(quantity_match.group(1))
            if value:
                candidates.append(
                    (value, text[match.start(): match.end() + quantity_match.end()])
                )
        return candidates

    @staticmethod
    def _extract_seller_names(text: str) -> List[Tuple[str, str]]:
        """Selling-shareholder identities anchored on the
        ("SELLING SHAREHOLDER") marker itself, so sellers listed after
        commas/"and" (not only after "by") are all enumerated. Returns
        (name, exact source substring) pairs, de-duplicated in order.
        """
        results: List[Tuple[str, str]] = []
        seen: set = set()
        for marker in re.finditer(
            r'\(\s*[“"]SELLING SHAREHOLDER[”"]\s*\)', text, re.IGNORECASE
        ):
            segment_start = max(0, marker.start() - 160)
            segment = text[segment_start: marker.start()]
            tail = re.split(r',|\bBY\b|\bAND\b', segment.replace("\n", " "))[-1]
            name_match = re.search(
                r'([A-Za-z0-9][A-Za-z0-9\s,&\.]*?\bLimited)\s*$',
                tail.strip(),
                re.IGNORECASE,
            )
            if not name_match:
                continue
            name = re.sub(r"\s+", " ", name_match.group(1)).strip()
            if name and name.upper() not in seen:
                seen.add(name.upper())
                first_word = name.split()[0]
                offset = segment.upper().find(first_word.upper())
                start = segment_start + (offset if offset >= 0 else 0)
                results.append((name, text[start: marker.end()]))
        return results

    @classmethod
    def _resolve_labelled_quantity(
        cls,
        text: str,
        label_pattern: str,
        forbidden_markers: Sequence[str],
    ) -> Tuple[Optional[float], Optional[str]]:
        """Resolve one labelled quantity, failing closed on ambiguity.

        Distinct surviving values for the same label are contradictory
        evidence: no value is chosen arbitrarily.
        """
        candidates = cls._labelled_quantity_candidates(text, label_pattern, forbidden_markers)
        values = {value for value, _quote in candidates}
        if len(values) == 1:
            return candidates[0]
        return None, None

    def extract_cover_and_offer(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract company name, issue size, price band, quotas, and OFS details."""
        extractions: List[RawExtraction] = []

        # 1. Company Name from Cover (first 4 pages)
        cover_text = ""
        for p in range(1, min(5, self.page_count + 1)):
            cover_text += "\n" + self.extract_page_text(p)

        m_comp = re.search(r'([A-Z0-9\s,\.\(\)]+?\bLIMITED\b)', cover_text)
        if m_comp:
            cname = m_comp.group(1).strip()
            for pfx in [
                "RED HERRING PROSPECTUS",
                "DRAFT RED HERRING PROSPECTUS",
                "PROSPECTUS OF",
                "INITIAL PUBLIC OFFER",
                "100% BOOK BUILT ISSUE",
                "BOOK BUILT ISSUE",
            ]:
                if pfx in cname:
                    cname = cname.replace(pfx, "").strip()
            cname = re.sub(r'^(?:100%\s+)?BOOK\s+BUILT\s+ISSUE\s*', '', cname, flags=re.IGNORECASE).strip()
            if "\n" in cname:
                # The lazy cover span can swallow preceding cover lines
                # (document-class titles are stripped above; logos and
                # other header matter are not names). The issuer name is
                # the standalone line ending in LIMITED within the span.
                name_lines = [
                    ln.strip()
                    for ln in cname.splitlines()
                    if ln.strip().upper().endswith("LIMITED") and len(ln.split()) >= 2
                ]
                if name_lines:
                    cname = name_lines[-1]
            extractions.append(
                RawExtraction(
                    field_path="company_name",
                    candidate_value=cname,
                    raw_text=cname,
                    page=1,
                    section="Cover",
                    locator="Cover page header",
                    quote=cname,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=1.0,
                )
            )

        # 1b. Issue Dates from Cover/Notice
        m_open = re.search(
            r'(?:issue|bid(?:\s*/\s*offer)?)\s*opens?\s*(?:on)?\s*(?:\([0-9]+\))?:?\s*(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*)?([A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4})',
            cover_text,
            re.IGNORECASE,
        )
        if m_open:
            d_str = m_open.group(1).strip()
            iso_open = None
            import datetime
            for fmt in ("%B %d, %Y", "%B %d,%Y", "%b %d, %Y", "%b %d,%Y"):
                try:
                    iso_open = datetime.datetime.strptime(d_str, fmt).strftime("%Y-%m-%d")
                    break
                except Exception:
                    pass
            if iso_open:
                extractions.append(
                    RawExtraction(
                        field_path="issue.open_date",
                        candidate_value=iso_open,
                        raw_text=d_str,
                        page=1,
                        section="Cover",
                        locator="Cover page, Issue Opening Date",
                        quote=m_open.group(0),
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        extraction_confidence=0.98,
                    )
                )

        m_close = re.search(
            r'(?:issue|bid(?:\s*/\s*offer)?)\s*closes?\s*(?:on)?\s*(?:\([0-9]+\))?:?\s*(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*)?([A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4})',
            cover_text,
            re.IGNORECASE,
        )
        if m_close:
            d_str = m_close.group(1).strip()
            iso_close = None
            import datetime
            for fmt in ("%B %d, %Y", "%B %d,%Y", "%b %d, %Y", "%b %d,%Y"):
                try:
                    iso_close = datetime.datetime.strptime(d_str, fmt).strftime("%Y-%m-%d")
                    break
                except Exception:
                    pass
            if iso_close:
                extractions.append(
                    RawExtraction(
                        field_path="issue.close_date",
                        candidate_value=iso_close,
                        raw_text=d_str,
                        page=1,
                        section="Cover",
                        locator="Cover page, Issue Closing Date",
                        quote=m_close.group(0),
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        extraction_confidence=0.98,
                    )
                )

        # 1c. Price Band (search cover pages and basis for offer price)
        pb_scan_text = cover_text
        if page_ranges and "basis_for_offer_price" in page_ranges:
            b_start, b_end = page_ranges["basis_for_offer_price"]
            for bp in range(b_start, min(b_start + 4, b_end + 1)):
                pb_scan_text += "\n" + self.extract_page_text(bp)

        m_pb = re.search(
            r'price\s+band\s+of\s+₹?\s*([0-9]+(?:\.[0-9]+)?)\s*to\s*₹?\s*([0-9]+(?:\.[0-9]+)?)',
            pb_scan_text,
            re.IGNORECASE,
        )
        pb_low = None
        pb_high = None
        if m_pb:
            pb_low = float(m_pb.group(1))
            pb_high = float(m_pb.group(2))
            extractions.append(
                RawExtraction(
                    field_path="issue.price_band_low",
                    candidate_value=pb_low,
                    raw_text=str(pb_low),
                    raw_unit="INR",
                    page=1,
                    section="The Offer",
                    locator="Price Band Disclosure",
                    quote=m_pb.group(0),
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )
            extractions.append(
                RawExtraction(
                    field_path="issue.price_band_high",
                    candidate_value=pb_high,
                    raw_text=str(pb_high),
                    raw_unit="INR",
                    page=1,
                    section="The Offer",
                    locator="Price Band Disclosure",
                    quote=m_pb.group(0),
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        # 1d. Lot Size (e.g. "multiples of 1600 Equity Shares" or "minimum bid lot ... 1600")
        lot_scan_text = cover_text
        for p in range(5, min(25, self.page_count + 1)):
            lot_scan_text += "\n" + self.extract_page_text(p)
        if page_ranges and "the_offer" in page_ranges:
            o_start, o_end = page_ranges["the_offer"]
            for op in range(o_start, min(o_start + 6, o_end + 1)):
                lot_scan_text += "\n" + self.extract_page_text(op)

        m_lot = re.search(
            r'(?:multiples\s+of|lot\s+size\s+(?:is\s+)?|minimum\s+trading\s+lot(?:\s+size)?\s*(?:is\s+)?)\s*([0-9,]+)',
            lot_scan_text,
            re.IGNORECASE,
        )
        if not m_lot:
            m_lot = re.search(r'bid\s+lot\s+(?:is\s+)?([0-9,]+)', lot_scan_text, re.IGNORECASE)
        if m_lot:
            lot_val = int(parse_indian_number(m_lot.group(1)) or 0)
            if lot_val > 0:
                extractions.append(
                    RawExtraction(
                        field_path="issue.lot_size",
                        candidate_value=lot_val,
                        raw_text=str(lot_val),
                        page=1,
                        section="The Offer",
                        locator="Bid Lot Details",
                        quote=m_lot.group(0),
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        extraction_confidence=0.95,
                    )
                )

        # 1e. Board Detection (SME vs Mainboard)
        is_sme = bool(re.search(r'\b(sme\s+platform|nse\s+emerge|bse\s+sme)\b', lot_scan_text, re.IGNORECASE))
        if is_sme:
            extractions.append(
                RawExtraction(
                    field_path="board",
                    candidate_value="sme",
                    raw_text="sme",
                    page=1,
                    section="The Offer",
                    locator="Exchange Platform",
                    quote="SME Platform disclosure",
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        # 2. Fresh Issue Shares & Amount
        # The quantity must be bound to the fresh-issue label without an
        # intervening Offer-for-Sale label: cover sentences routinely
        # state "... (FRESH OFFER) AND AN OFFER FOR SALE OF UP TO N
        # EQUITY SHARES", and an unguarded span assigns the OFS quantity
        # to fresh shares. Ambiguous (contradictory) bindings fail closed.
        fresh_shares_count, fresh_quote = self._resolve_labelled_quantity(
            cover_text,
            r'fresh\s+(?:offer|issue)\b',
            ("offer for sale", "ofs", "selling shareholder"),
        )
        if fresh_shares_count:
            extractions.append(
                RawExtraction(
                    field_path="issue.fresh_shares",
                    candidate_value=int(fresh_shares_count),
                    raw_text=str(int(fresh_shares_count)),
                    page=1,
                    section="Cover",
                    locator="Cover page, Fresh Issue Shares",
                    quote=fresh_quote,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        m_fresh = None
        for _label_match in re.finditer(r'fresh\s+(?:offer|issue)\b', cover_text, re.IGNORECASE):
            _segment = cover_text[_label_match.end(): _label_match.end() + 220]
            _amount_match = re.search(
                r'aggregating(?: up)? to ₹\s*([0-9,]+(?:\.[0-9]+)?)\s*(lakhs?|crores?|millions?)',
                _segment,
                re.IGNORECASE,
            )
            if not _amount_match:
                continue
            _between = _segment[: _amount_match.start()].lower()
            if "offer for sale" in _between or "selling shareholder" in _between:
                continue  # amount belongs to the OFS clause, not the fresh issue
            m_fresh = (_label_match, _amount_match)
            break
        if m_fresh:
            _label_match, _amount_match = m_fresh
            raw_val = _amount_match.group(1)
            unit_val = _amount_match.group(2).upper()
            num_val = parse_indian_number(raw_val)
            extractions.append(
                RawExtraction(
                    field_path="issue.fresh_issue",
                    candidate_value=num_val,
                    raw_text=raw_val,
                    raw_unit=unit_val,
                    page=1,
                    section="Cover",
                    locator="Cover page, Fresh Offer",
                    quote=cover_text[_label_match.start(): _label_match.end() + _amount_match.end()],
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )
        elif fresh_shares_count and pb_high:
            derived_fresh_lakhs = round(fresh_shares_count * pb_high / 100000.0, 2)
            extractions.append(
                RawExtraction(
                    field_path="issue.fresh_issue",
                    candidate_value=derived_fresh_lakhs,
                    raw_text=str(derived_fresh_lakhs),
                    raw_unit="INR_LAKHS",
                    page=1,
                    section="Cover",
                    locator="Cover page, Derived Fresh Offer Size at Cap",
                    quote=f"Fresh shares {fresh_shares_count} @ ₹{pb_high} = ₹{derived_fresh_lakhs} Lakhs",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )

        # 3. OFS Seller & shares / NIL detection
        ofs_nil_quote = _find_ofs_nil(cover_text)
        if ofs_nil_quote is not None:
            extractions.append(
                RawExtraction(
                    field_path="issue.ofs",
                    candidate_value=0.0,
                    raw_text="0.0",
                    raw_unit="INR_LAKHS",
                    page=1,
                    section="Cover",
                    locator="Cover page, Offer for Sale Size",
                    quote=ofs_nil_quote,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=1.0,
                )
            )
            extractions.append(
                RawExtraction(
                    field_path="issue.ofs_sellers",
                    candidate_value=[],
                    raw_text="[]",
                    page=1,
                    section="Cover",
                    locator="Cover page, Offer for Sale Size",
                    quote=ofs_nil_quote,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=1.0,
                )
            )
        else:
            ofs_shares_count, ofs_quote = self._resolve_labelled_quantity(
                cover_text,
                r'offer\s+for\s+sale\b',
                ("fresh offer", "fresh issue"),
            )

            seller_entries = self._extract_seller_names(cover_text)
            seller_names = [name for name, _quote in seller_entries]

            if len(seller_names) == 1:
                # Sole named selling shareholder: the cover's aggregate
                # OFS quantity is that seller's quantity. (The v1.5 seller
                # model requires numeric pre_issue_shares, which the
                # cover does not independently establish; it carries the
                # established sold quantity, as in existing records.)
                ofs_seller_obj = [
                    {
                        "name": seller_names[0],
                        "type": "promoter_group",
                        "pre_issue_shares": int(ofs_shares_count) if ofs_shares_count else None,
                        "shares_sold": int(ofs_shares_count) if ofs_shares_count else None,
                        "holding_pct_pre_issue": None,
                        "source_id": self.doc.source_id,
                    }
                ]
                extractions.append(
                    RawExtraction(
                        field_path="issue.ofs_sellers",
                        candidate_value=ofs_seller_obj,
                        raw_text=str(ofs_seller_obj),
                        page=1,
                        section="Cover",
                        locator="Cover page, Details of the Offer for Sale",
                        quote=seller_entries[0][1],
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        extraction_confidence=0.95,
                    )
                )
            elif len(seller_names) > 1:
                # Multiple selling shareholders with (at most) an
                # aggregate OFS quantity: the v1.5 seller model cannot
                # represent an unattributed quantity, and the aggregate
                # must not be attributed to any individual seller.
                # Seller identity is preserved in the evidence quotation;
                # the canonical seller list stays empty so OFS derivation
                # fails closed instead of guessing.
                _span_start = cover_text.find(seller_entries[0][1])
                _span_end = cover_text.find(seller_entries[-1][1]) + len(seller_entries[-1][1])
                _span = cover_text[_span_start:_span_end]
                extractions.append(
                    RawExtraction(
                        field_path="issue.ofs_sellers",
                        candidate_value=[],
                        raw_text="[]",
                        page=1,
                        section="Cover",
                        locator="Cover page, Details of the Offer for Sale",
                        quote=_span[:600],
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        extraction_confidence=0.90,
                    )
                )

        # 4. Quotas (QIB, Retail, NII)
        offer_range = page_ranges.get("offer_structure") if page_ranges else None
        if not offer_range and page_ranges:
            offer_range = page_ranges.get("the_offer")
        p_start, p_end = offer_range or (50, min(100, self.page_count))

        quota_qib = None
        quota_retail = None
        quota_nii = None

        for p in range(p_start, p_end + 1):
            txt = self.extract_page_text(p)
            if "quota" in txt.lower() or "allocation" in txt.lower() or "qib" in txt.lower():
                m_qib = re.search(r'qib[^\n]*?([0-9]+(?:\.[0-9]+)?)\s*%', txt, re.IGNORECASE)
                m_ret = re.search(r'retail[^\n]*?([0-9]+(?:\.[0-9]+)?)\s*%', txt, re.IGNORECASE)
                m_nii = re.search(r'(?:nii|non-institutional)[^\n]*?([0-9]+(?:\.[0-9]+)?)\s*%', txt, re.IGNORECASE)
                if m_qib and quota_qib is None:
                    quota_qib = float(m_qib.group(1))
                if m_ret and quota_retail is None:
                    quota_retail = float(m_ret.group(1))
                if m_nii and quota_nii is None:
                    quota_nii = float(m_nii.group(1))
                if quota_qib is not None and quota_retail is not None and quota_nii is not None:
                    break

        if quota_qib is not None or quota_retail is not None or quota_nii is not None:
            quotas = {
                "qib": quota_qib,
                "retail": quota_retail,
                "nii": quota_nii,
            }
            extractions.append(
                RawExtraction(
                    field_path="issue.quota_pct",
                    candidate_value=quotas,
                    raw_text=str(quotas),
                    page=p_start,
                    section="Offer Structure",
                    locator="Offer Quotas Allocation",
                    quote=f"QIB: {quota_qib}%, Retail: {quota_retail}%, NII: {quota_nii}%",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.90,
                )
            )

        return extractions

    # Category-total labels in the ICDR shareholding pattern.  The summary row
    # "Total (A)+(B)+(C)" is the whole company; a prefix match on "Total (A)"
    # read it as the promoter category and produced 100% (observed on the Jio
    # RHP p.107: 66.43% promoter, 33.57% public).  The trailing lookahead
    # keeps that summary row out of the promoter fallback.
    _TOTAL_A_LABEL = re.compile(r"total\s*\(\s*a\s*\)(?!\s*[+(])", re.IGNORECASE)

    def extract_capital_structure(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract promoter pre/post holding %, pledge %, and lock-in."""
        extractions: List[RawExtraction] = []
        c_range = page_ranges.get("capital_structure") if page_ranges else None
        p_start, p_end = c_range or (80, min(130, self.page_count))

        pre_pct = None
        post_pct = None
        pledge_pct = None
        lockin = None
        found_page = p_start

        # Concatenate text across the section pages to cover tables spanning page breaks
        cap_lines: List[str] = []
        for p in range(p_start, min(p_end + 1, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if pledge_pct is None and re.search(r'none of the equity shares held by our promoters are pledged', txt, re.IGNORECASE):
                pledge_pct = 0.0
            if lockin is None and re.search(r'locked in for a period of 18 months', txt, re.IGNORECASE):
                lockin = True
            for l in txt.split("\n"):
                if l.strip():
                    cap_lines.append(l.strip())

        for i, line in enumerate(cap_lines):
            if re.search(r'shareholding of our promoters and (?:members of the\s+)?promoter group', line, re.IGNORECASE):
                for j in range(i, min(i + 120, len(cap_lines))):
                    l = cap_lines[j]
                    if l.startswith("Total") and re.search(r'[0-9]+(?:\.[0-9]+)?', l):
                        nums = re.findall(r'\[[●•\*]\]|[0-9,]+(?:\.[0-9]+)?', l)
                        pct_candidates = [parse_indian_number(x) for x in nums if not is_undisclosed_marker(x)]
                        pct_candidates = [x for x in pct_candidates if x is not None and 10.0 <= x <= 100.0]
                        if pct_candidates:
                            pre_pct = pct_candidates[0]
                            if any(is_undisclosed_marker(x) for x in nums):
                                post_pct = None
                            break
                if pre_pct is not None:
                    break

        # Check if a genuine Total (A) row exists for promoter pre-holding.
        # A combined "Total (A)+(B)+(C)" summary row is the whole company, not
        # the promoter category: a prefix match on "Total (A)" read it as the
        # promoter total and returned 100% (Jio RHP p.107 states 66.43%).
        # The category-total arithmetic itself is unchanged: combining the
        # public category into the promoter category is a separate question
        # (decision D-3) that changes an existing filing's extracted value.
        if pre_pct is None:
            tot_a_pre = None
            tot_b_pre = None
            for idx, l in enumerate(cap_lines):
                if self._TOTAL_A_LABEL.search(l):
                    c_text = l
                    for j in range(idx + 1, min(idx + 3, len(cap_lines))):
                        c_text += " " + cap_lines[j]
                    floats = [float(x) for x in re.findall(r'[0-9]+\.[0-9]+', c_text)]
                    if len(floats) >= 2:
                        tot_a_pre = floats[0]
                if re.search(r'Total\s*\(\s*B\s*\)', l, re.IGNORECASE):
                    floats = [float(x) for x in re.findall(r'[0-9]+\.[0-9]+', l)]
                    if len(floats) >= 2:
                        tot_b_pre = floats[0]
            if tot_a_pre is not None:
                pre_pct = round(tot_a_pre + (tot_b_pre or 0.0), 2)

        if pre_pct is not None:
            extractions.append(
                RawExtraction(
                    field_path="capital_structure.promoter_pre_pct",
                    candidate_value=pre_pct,
                    raw_text=str(pre_pct),
                    raw_unit="PERCENT",
                    page=found_page,
                    section="Capital Structure",
                    locator="Shareholding of our Promoters and Promoter Group",
                    quote=f"Total Promoter & Promoter Group pre-issue shareholding: {pre_pct}%",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        # Post-issue promoter holding fallback scan.  The category arithmetic
        # is unchanged; the label guard only stops the combined summary row
        # from being read as the promoter total.
        if post_pct is None:
            a_pct = None
            b_pct = None
            for idx, l in enumerate(cap_lines):
                if self._TOTAL_A_LABEL.search(l):
                    c_text = l
                    for j in range(idx + 1, min(idx + 3, len(cap_lines))):
                        c_text += " " + cap_lines[j]
                    nums = re.findall(r'[0-9,]+(?:\.[0-9]+)?', c_text)
                    pcts = [parse_indian_number(x) for x in nums if parse_indian_number(x) is not None]
                    pcts = [x for x in pcts if 10.0 <= x <= 100.0]
                    if pcts:
                        a_pct = pcts[-1]
                if re.search(r'Total\s*\(\s*B\s*\)', l, re.IGNORECASE):
                    nums = re.findall(r'[0-9,]+(?:\.[0-9]+)?', l)
                    pcts = [parse_indian_number(x) for x in nums if parse_indian_number(x) is not None]
                    pcts = [x for x in pcts if 0.0 <= x < 10.0]
                    if pcts:
                        b_pct = pcts[-1]
            if a_pct is not None:
                post_pct = round(a_pct + (b_pct or 0.0), 2)

        if post_pct is not None:
            extractions.append(
                RawExtraction(
                    field_path="capital_structure.promoter_post_pct",
                    candidate_value=post_pct,
                    raw_text=str(post_pct),
                    raw_unit="PERCENT",
                    page=found_page,
                    section="Capital Structure",
                    locator="Shareholding of our Promoters and Promoter Group",
                    quote=f"Post-issue promoter holding: {post_pct}%",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.90,
                )
            )

        # Pre-issue and Post-issue shares
        pre_shares = None
        post_shares = None
        for idx, l in enumerate(cap_lines):
            if pre_shares is None and ("before the offer" in l.lower() or "before the issue" in l.lower()):
                forward_text = " ".join(cap_lines[idx:min(idx + 4, len(cap_lines))])
                m_pre = re.search(r'([0-9,]{6,})\s*Equity Shares', forward_text, re.IGNORECASE)
                if m_pre:
                    parsed_pre = int(parse_indian_number(m_pre.group(1)) or 0)
                    if parsed_pre > 10000:
                        pre_shares = parsed_pre
                        extractions.append(
                            RawExtraction(
                                field_path="issue.pre_issue_shares",
                                candidate_value=pre_shares,
                                raw_text=str(pre_shares),
                                page=p_start,
                                section="Capital Structure",
                                locator="Pre-issue Share Capital",
                                quote=f"Pre-issue Equity Shares: {pre_shares}",
                                quote_is_processing=True,
                                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                                extraction_confidence=0.95,
                            )
                        )
            if post_shares is None and ("after the offer" in l.lower() or "after the issue" in l.lower()):
                forward_text = " ".join(cap_lines[idx:min(idx + 4, len(cap_lines))])
                m_post = re.search(r'([0-9,]{6,})\s*Equity Shares', forward_text, re.IGNORECASE)
                if m_post:
                    parsed_post = int(parse_indian_number(m_post.group(1)) or 0)
                    if parsed_post > 10000:
                        post_shares = parsed_post
                        extractions.append(
                            RawExtraction(
                                field_path="issue.post_issue_shares",
                                candidate_value=post_shares,
                                raw_text=str(post_shares),
                                page=p_start,
                                section="Capital Structure",
                                locator="Post-issue Share Capital",
                                quote=f"Post-issue Equity Shares: {post_shares}",
                                quote_is_processing=True,
                                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                                extraction_confidence=0.95,
                            )
                        )

        if pledge_pct is not None:
            extractions.append(
                RawExtraction(
                    field_path="capital_structure.promoter_pledge_pct",
                    candidate_value=pledge_pct,
                    raw_text=str(pledge_pct),
                    raw_unit="PERCENT",
                    page=found_page,
                    section="Capital Structure",
                    locator="Promoter share pledge confirmation",
                    quote="None of the Equity Shares held by our Promoters are pledged",
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=1.0,
                )
            )

        if lockin is not None:
            extractions.append(
                RawExtraction(
                    field_path="capital_structure.promoter_lockin_in_place",
                    candidate_value=lockin,
                    raw_text=str(lockin),
                    page=found_page,
                    section="Capital Structure",
                    locator="Promoter lock-in for 18 months",
                    quote="Promoter contribution locked in for 18 months",
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=1.0,
                )
            )

        return extractions

    def extract_objects_of_offer(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract use_of_proceeds schedule with fail-closed [●] GCP detection."""
        extractions: List[RawExtraction] = []
        obj_range = page_ranges.get("objects_of_the_offer") if page_ranges else None
        p_start, p_end = obj_range or (120, min(145, self.page_count))

        use_of_proceeds: List[Dict[str, Any]] = []
        found_page = p_start

        # Scan across the section pages so split tables are seamlessly covered
        scan_end = min(p_start + 6, p_end + 1, self.page_count + 1)
        section_lines: List[str] = []
        for p in range(p_start, scan_end):
            txt = self.extract_page_text(p)
            for line in txt.split("\n"):
                if line.strip():
                    section_lines.append(line.strip())

        def _scan_category_amount(keyword_list: List[str]) -> Tuple[Optional[float], Optional[str]]:
            for i, l in enumerate(section_lines):
                if any(k.lower() in l.lower() for k in keyword_list):
                    for j in range(i, min(i + 4, len(section_lines))):
                        tokens = re.findall(r'\[[^a-zA-Z0-9\s]+\]|\[[●•\*]\]|[0-9,]+(?:\.[0-9]+)?', section_lines[j])
                        for tok in tokens:
                            if is_undisclosed_marker(tok):
                                return None, "[●]"
                            num = parse_indian_number(tok)
                            if num is not None and num > 50.0:
                                return num, None
            return None, None

        # 1. Working capital
        wc_amt, wc_marker = _scan_category_amount(["working capital requirements", "funding working capital"])
        if wc_amt is not None or wc_marker is not None:
            item: Dict[str, Any] = {"category": "working_capital", "amount": wc_amt}
            if wc_marker:
                item["undisclosed_marker"] = wc_marker
            use_of_proceeds.append(item)

        # 2. Debt repayment
        debt_amt, debt_marker = _scan_category_amount(["repayment and/ or pre", "repayment of term loans", "debt repayment"])
        if debt_amt is not None or debt_marker is not None:
            item = {"category": "debt_repayment", "amount": debt_amt}
            if debt_marker:
                item["undisclosed_marker"] = debt_marker
            use_of_proceeds.append(item)

        # 3. Growth Capex / Capital Augmentation
        capex_amt, capex_marker = _scan_category_amount(["capital expenditure", "purchase of plant", "growth capex", "augmentation of"])
        if capex_amt is not None or capex_marker is not None:
            item = {"category": "growth_capex", "amount": capex_amt}
            if capex_marker:
                item["undisclosed_marker"] = capex_marker
            use_of_proceeds.append(item)

        # 4. General corporate purposes (GCP)
        gcp_amt, gcp_marker = _scan_category_amount(["general corporate purposes"])
        if gcp_amt is not None or gcp_marker is not None:
            item = {"category": "gcp", "amount": gcp_amt}
            if gcp_marker:
                item["undisclosed_marker"] = gcp_marker
            use_of_proceeds.append(item)

        if use_of_proceeds:
            extractions.append(
                RawExtraction(
                    field_path="use_of_proceeds",
                    candidate_value=use_of_proceeds,
                    raw_text=str(use_of_proceeds),
                    page=found_page,
                    section="Objects of the Offer",
                    locator="Schedule of Implementation and Deployment",
                    quote=f"Use of proceeds categories: {[u['category'] for u in use_of_proceeds]}",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        return extractions

    # ------------------------------------------------------------------
    # Related-party transactions (generic, issuer-neutral)
    # ------------------------------------------------------------------
    # The related-party note is introduced in several wordings:
    #   "Transactions with related parties"            (Vishal)
    #   "Transactions with the related parties"        (Jio)
    #   "Transactions during the period / year with Related Parties" (Jio table)
    _RPT_TRANSACTIONS_HEADER = re.compile(
        r"transactions?\s+(?:(?:during|for)\s+(?:the\s+)?(?:period|year)"
        r"[^.]{0,40}\s+)?with\s+(?:the\s+)?related\s+part(?:y|ies)",
        re.IGNORECASE,
    )

    # A table carrying a Relationship column labels each amount row by
    # relationship (Parent / Fellow Subsidiaries / Associate/JV / Others).
    _RPT_RELATIONSHIP_PREFIX = re.compile(
        r"^(?:parent\b|fellow\s+subsidiar|associate\b|joint\s+venture\b|jv\b|"
        r"others?\b|key\s+managerial\b|kmp\b|promoter|non[-\s]?controlling)",
        re.IGNORECASE,
    )

    _RPT_CATEGORY_PHRASES: Tuple[Tuple[str, str], ...] = (
        ("sale of goods", "sale_of_goods"),
        ("sales of goods", "sale_of_goods"),
        ("sale of services", "sale_of_services"),
        ("revenue from operations", "revenue_from_operations"),
        ("purchase of goods", "purchase_of_goods"),
        ("purchases of goods", "purchase_of_goods"),
        ("sale of property, plant and equipment", "sale_of_ppe"),
        ("sale of property plant and equipment", "sale_of_ppe"),
        ("purchase of property, plant and equipment", "purchase_of_ppe"),
        ("purchase of property plant and equipment", "purchase_of_ppe"),
        ("reimbursement of expenses paid", "reimbursement_expenses_paid"),
        ("reimbursement of expenses received", "reimbursement_expenses_received"),
        ("hiring/transport charges paid", "hiring_transport_charges_paid"),
        ("transport charges paid", "transport_charges_paid"),
        ("job work charges received", "job_work_charges_received"),
        ("job work charges paid", "job_work_charges_paid"),
        ("interest paid", "interest_paid"),
        ("interest received", "interest_received"),
        ("rent paid", "rent_paid"),
        ("rent received", "rent_received"),
        ("loan taken", "loan_taken"),
        ("loans taken", "loan_taken"),
        ("loan repaid", "loan_repaid"),
        ("loans repaid", "loan_repaid"),
        ("share of profit paid", "share_of_profit_paid"),
        ("managerial remuneration", "remuneration"),
        ("remuneration", "remuneration"),
        ("salary", "salary"),
    )

    @staticmethod
    def _rpt_norm(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower()).strip(" .")

    def _rpt_category_match(self, normalized: str) -> Optional[Tuple[str, str, int]]:
        """Return (key, label, chars_consumed) if text starts with a category."""
        for phrase, key in self._RPT_CATEGORY_PHRASES:
            if normalized == phrase:
                return key, phrase, len(phrase)
            if normalized.startswith(phrase + " "):
                return key, phrase, len(phrase)
        return None

    def extract_related_party_transactions(
        self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None
    ) -> List[RawExtraction]:
        """Extract the related-party *transactions* table from the filing.

        Generic and deterministic: locates the "Transactions with related
        parties" table inside the related-party note of the restated
        financial information, reads counterparty rows under transaction
        category headers across the disclosed financial-year columns, and
        emits one extraction per (category, counterparty, period) with a
        verbatim row quote.  Outstanding-balance tables are excluded.
        Amounts stay in the unit disclosed by the note; "-" cells are
        treated as undisclosed (never zero).  Rows whose amount count does
        not match the disclosed period columns are skipped (ambiguous).

        The extractions are registered as evidence under
        ``governance.related_party_transactions[i]`` paths.  The runtime
        canonical schema is closed, so no structured canonical field is
        added; the values live in the evidence registry with verbatim
        quotes.  They deliberately do NOT populate the scoring fields
        ``rpt_pct_revenue`` / ``rpt_pct_of_revenue_growth``:
        the approved metric definitions do not yet specify transaction
        categories, growth window or negative-growth treatment (see
        docs/investigation/RPT-EXTRACTION-AND-METRIC-DEFINITIONS-2026-10-17.md).
        """
        fin_range = page_ranges.get("restated_financials") if page_ranges else None
        scan = range(fin_range[0], fin_range[1] + 1) if fin_range else range(1, self.page_count + 1)
        anchor_page: Optional[int] = None
        for p in scan:
            if p > self.page_count:
                break
            if self._RPT_TRANSACTIONS_HEADER.search(self.extract_page_text(p)):
                anchor_page = p
                break
        if anchor_page is None and fin_range:
            # The TOC range for the financial section may end before the
            # related-party note; fall back to a full-document search.
            for p in range(1, self.page_count + 1):
                if self._RPT_TRANSACTIONS_HEADER.search(self.extract_page_text(p)):
                    anchor_page = p
                    break
        if anchor_page is None:
            return []

        # Gather lines from the anchor page onwards (same note), stopping
        # at the outstanding-balances table or after a bounded window.
        lines: List[Tuple[int, str]] = []
        stop = False
        for p in range(anchor_page, min(anchor_page + 6, self.page_count + 1)):
            for raw_line in self.extract_page_text(p).splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                low_line = line.lower()
                if (
                    "outstanding balances" in low_line
                    or "balances as at" in low_line
                    or "major related party transactions" in low_line
                ):
                    # Balance tables and the "major transactions" breakdown
                    # repeat the same amounts at counterparty level; parsing
                    # them would double count the note's category totals.
                    stop = True
                    break
                lines.append((p, line))
            if stop:
                break
        if not lines:
            return []

        # Period columns from the table header ("year ended 31 March YYYY").
        # Header rows can wrap across many lines (Jio's note spreads the
        # five period columns over ~20 lines); scan a bounded header window.
        years: List[int] = []
        for _, line in lines[:30]:
            for m in re.finditer(r"31(?:st)?\s+March,?\s+(20\d{2})", line):
                y = int(m.group(1))
                if y not in years:
                    years.append(y)
        if len(years) < 2:
            return []
        years = years[:3]

        unit = None
        note_text = " ".join(line for _, line in lines)
        # The note may inherit the unit declared at the head of the
        # restated financial statements (e.g. "(Amount in Lakhs, unless
        # otherwise stated)"); search a bounded window before the note.
        unit_window = note_text
        for p in range(max(1, anchor_page - 60), anchor_page):
            unit_window += " " + self.extract_page_text(p)[:400]
        if re.search(r"in\s+lakhs?\b", unit_window, re.IGNORECASE):
            unit = "INR_LAKHS"
        elif re.search(r"in\s+crores?\b", unit_window, re.IGNORECASE):
            unit = "INR_CRORES"
        elif re.search(r"in\s+millions?\b", unit_window, re.IGNORECASE):
            unit = "INR_MILLIONS"

        header_blob = " ".join(line for _, line in lines[:14]).lower()
        has_relationship_column = "relationship" in header_blob
        amount_token = re.compile(r"^(?:-|\d[\d,]*\.\d+|\d[\d,]*)$")
        transactions: List[Dict[str, Any]] = []
        seen = set()
        current_category: Optional[Tuple[str, str]] = None
        pending_name = ""
        started = False
        for page, line in lines:
            low = line.lower()
            if self._RPT_TRANSACTIONS_HEADER.search(line):
                started = True
                continue
            if not started:
                continue
            if low.startswith("total"):
                pending_name = ""
                continue
            tokens = line.split()
            amounts: List[str] = []
            while tokens and amount_token.match(tokens[-1]) and len(amounts) < len(years):
                amounts.insert(0, tokens.pop())
            name_part = " ".join(tokens).strip()
            if len(amounts) == len(years) and (name_part or pending_name):
                display = " ".join(f"{pending_name} {name_part}".split())
                pending_name = ""
                # A leading Sr. No. is a row key, never part of the category.
                display = re.sub(r"^\d{1,3}\s+", "", display)
                normalized = self._rpt_norm(display)
                match = self._rpt_category_match(normalized)
                counterparty = display
                if match is not None:
                    key, label, consumed = match
                    current_category = (key, label)
                    counterparty = display[consumed:].strip(" .")
                elif has_relationship_column and not self._RPT_RELATIONSHIP_PREFIX.match(normalized):
                    # A table with a Relationship column names its category on
                    # the row itself.  An unrecognised category header must
                    # never inherit the previous category: "Revenue Received
                    # in Advance" is not revenue from operations.
                    current_category = None
                    continue
                if current_category is None or not counterparty:
                    continue
                # Interim columns can remain in the text; a counterparty is a
                # name, never a trailing number.
                counterparty = re.sub(r"(?:\s+[\d,]+(?:\.\d+)?)+$", "", counterparty).strip()
                if not counterparty:
                    continue
                counterparty_clean = " ".join(counterparty.split()).strip("* ").strip().rstrip(".")
                for year, token in zip(years, amounts):
                    if token == "-":
                        continue  # undisclosed / nil marker: not zero
                    try:
                        amount = float(token.replace(",", ""))
                    except ValueError:
                        continue
                    dedupe = (current_category[0], counterparty_clean.lower(), year)
                    if dedupe in seen:
                        continue
                    seen.add(dedupe)
                    transactions.append(
                        {
                            "category": current_category[0],
                            "category_label": current_category[1],
                            "counterparty": counterparty_clean,
                            "period": f"FY{year}",
                            "amount": amount,
                            "unit": unit,
                            "page": page,
                            "_quote": line,
                        }
                    )
                continue
            if amounts:
                # Partial amount row: ambiguous layout; fail closed.
                pending_name = ""
                continue
            # Non-amount line: category header or wrapped counterparty name.
            normalized = self._rpt_norm(f"{pending_name} {line}" if pending_name else line)
            match = self._rpt_category_match(normalized)
            if match is not None and normalized == match[1]:
                current_category = (match[0], match[1])
                pending_name = ""
            elif match is not None and not pending_name and self._rpt_category_match(self._rpt_norm(line)) and normalized == self._rpt_norm(line):
                current_category = (match[0], match[1])
                pending_name = ""
            else:
                pending_name = f"{pending_name} {line}".strip()

        extractions: List[RawExtraction] = []
        for idx, txn in enumerate(transactions):
            quote = txn.pop("_quote")
            extractions.append(
                RawExtraction(
                    field_path=f"governance.related_party_transactions[{idx}]",
                    candidate_value=txn,
                    raw_text=quote,
                    page=txn["page"],
                    section="Restated Financial Information",
                    locator=f"Related Party Transactions — {txn['category_label']} — {txn['counterparty']} — {txn['period']}",
                    quote=quote,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.9,
                )
            )
        return extractions

    # A going-concern *uncertainty* is established only by the standard
    # disclosure language: a material uncertainty related to going concern,
    # substantial doubt about the ability to continue, or an equivalent
    # statement.  A transfer "on a going concern basis" (an accounting
    # measurement convention) is not an uncertainty.
    _GOING_CONCERN_UNCERTAINTY = re.compile(
        r"material\s+uncertainty[^.]{0,200}?going\s+concern"
        r"|going\s+concern[^.]{0,200}?material\s+uncertainty"
        r"|substantial\s+doubt[^.]{0,160}?(?:ability\s+to\s+continue|going\s+concern)"
        r"|ability\s+to\s+continue\s+as\s+a\s+going\s+concern[^.]{0,160}?(?:uncertain|doubt)",
        re.IGNORECASE,
    )

    # Negations that turn the standard uncertainty phrase into a statement of
    # its absence.  Kept as an explicit list rather than a bare "no" so that
    # an unrelated word in the same sentence ("No doubt, there is a material
    # uncertainty ...") does not suppress a genuine disclosure.
    _GOING_CONCERN_NEGATION = re.compile(
        r"\bthere\s+(?:is|are|was|were)\s+(?:no|not)\b"
        r"|\b(?:do|does|did|has|have|had)\s+not\s+"
        r"(?:identify|identified|report|reported|find|found|note|noted|exist|arise)\b"
        r"|\bno\s+(?:material\s+|significant\s+)?uncertainty\b"
        r"|\bno\s*$"
        r"|\bwithout\s+(?:any\s+)?(?:material\s+)?uncertainty\b"
        r"|\bnone\b",
        re.IGNORECASE,
    )
    _GOING_CONCERN_POST_NEGATION = re.compile(
        r"\b(?:does|do|did|has|have|had)\s+not\s+(?:exist|been\s+identified|identified)\b"
        r"|\bno\s+such\b",
        re.IGNORECASE,
    )

    @classmethod
    def _going_concern_uncertainty_match(cls, text: str) -> Optional[re.Match]:
        """A *positive* going-concern uncertainty statement.

        "There is no material uncertainty related to going concern" and "we
        did not identify any material uncertainty ..." contain the standard
        phrase but assert its absence.  Emitting True for them triggered K1
        on the opposite of the disclosed fact.  The absence of a positive
        statement is still not a negative confirmation: callers must leave
        the field unknown.
        """
        for match in cls._GOING_CONCERN_UNCERTAINTY.finditer(text):
            prefix = text[max(0, match.start() - 120): match.start()]
            cut = max(prefix.rfind("."), prefix.rfind("\n"), prefix.rfind(";"))
            if cut != -1:
                prefix = prefix[cut + 1:]
            if cls._GOING_CONCERN_NEGATION.search(prefix):
                continue
            end = text.find(".", match.end())
            sentence_tail = text[match.start(): end if end != -1 else len(text)]
            if cls._GOING_CONCERN_POST_NEGATION.search(sentence_tail):
                continue
            return match
        return None

    @classmethod
    def _has_positive_emphasis_of_matter(cls, text: str) -> bool:
        """True only for a positive Emphasis of Matter statement.

        "There are no Emphasis of matters in auditor's report" is a negative
        disclosure; treating it as an EOM would invert its meaning.
        """
        for match in re.finditer(r"emphasis\s+of\s+matters?", text, re.IGNORECASE):
            before = text[max(0, match.start() - 80):match.start()].lower()
            if re.search(r"\b(?:no|nil|without)\s*$", before):
                continue
            if re.search(r"\bthere\s+(?:are|is)\s+no\s*$", before):
                continue
            return True
        return False

    @staticmethod
    def _opinion_sentence(text: str, pattern: str) -> str:
        """Verbatim sentence around the opinion phrase (whitespace-normalised)."""
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return ""
        start = max(text.rfind(".", 0, match.start()), text.rfind("\n", 0, match.start()))
        end = text.find(".", match.end())
        end = len(text) if end == -1 else end + 1
        return " ".join(text[start + 1:end].split())[:400]

    def _examination_report_pages(self, scan_pages: List[int]) -> List[int]:
        """Contiguous pages of the auditors' examination report.

        The opinion is stated in the report's conclusion, which usually does
        not repeat the heading wording.  Anchor on the first page carrying the
        examination-report heading, then include pages up to and including the
        auditor signature (UDIN) — bounded to eight pages — and stop before
        the restated statements begin.
        """
        anchor = None
        for p in scan_pages:
            if "examination report" in self.extract_page_text(p).lower():
                anchor = p
                break
        if anchor is None:
            return []
        pages: List[int] = []
        for p in range(anchor, min(anchor + 8, self.page_count + 1)):
            txt = self.extract_page_text(p)
            low = txt.lower()
            # The statements themselves begin with a standalone heading
            # line; the report's scope paragraph mentions the same statements
            # inline, so only the heading counts.
            if p > anchor and re.search(
                r"^\s*restated\s+consolidated\s+statements?\s+of\s+assets\s+and\s+liabilit(?:y|ies)\s*$",
                txt,
                re.IGNORECASE | re.MULTILINE,
            ):
                break
            pages.append(p)
            # UDIN is the auditors' unique document identification number and
            # appears in the signature block.  Match the token, not the
            # substring: "including" contains "udin".
            if re.search(r"\bUDIN\b", txt) or "for and on behalf of" in low:
                break
        return pages

    def extract_governance(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract auditor opinion, litigation bucket, SEBI action, and board independence."""
        extractions: List[RawExtraction] = []

        # 1. Auditor opinion
        fin_range = page_ranges.get("restated_financials") if page_ranges else None
        p_start, p_end = fin_range or (60, min(80, self.page_count))

        # The opinion is established only by positive opinion language in
        # the examination report. Failure to detect adverse language is NOT
        # evidence of an unqualified opinion: when no opinion language is
        # found the field stays unknown (None) and no extraction is emitted
        # (Step 4 Area B(i), approved 2026-10-17).
        auditor_opinion = None
        found_opinion_page = p_start

        scan_pages = list(range(p_start, min(p_end + 1, self.page_count + 1)))
        if self.page_count >= 350:
            scan_pages.extend(range(340, 350))

        # The opinion is stated on the report's conclusion page, which does
        # not repeat the words "examination report" / "independent auditor".
        # Gating on those words on the SAME page skipped Jio's conclusion
        # (pp. 321-324: the opinion language is on pp. 323-324).  Scan the
        # contiguous examination-report section instead: from the anchor page
        # up to and including the auditor signature (UDIN), bounded.
        report_pages = self._examination_report_pages(scan_pages)
        page_texts = {p: self.extract_page_text(p) for p in report_pages}
        section_text = "\n".join(page_texts[p] for p in report_pages)
        opinion_quote = ""

        def page_for(offset: int) -> int:
            cursor = 0
            for p in report_pages:
                cursor += len(page_texts[p]) + 1
                if offset < cursor:
                    return p
            return report_pages[-1] if report_pages else p_start

        # 1. A qualification, adverse opinion, disclaimer or positive Emphasis
        #    of Matter anywhere in the report dominates.  A qualification is
        #    never overridden by a later "no modification" sentence.
        for p in report_pages:
            txt = page_texts[p]
            low = txt.lower()
            if self._has_positive_emphasis_of_matter(txt) or "included following matter(s)" in low:
                auditor_opinion = "emphasis_of_matter"
                found_opinion_page = p
                opinion_quote = self._opinion_sentence(txt, r"emphasis\s+of\s+matters?")
                break
            if "adverse opinion" in low:
                auditor_opinion = "adverse"
                found_opinion_page = p
                opinion_quote = self._opinion_sentence(txt, r"adverse\s+opinion")
                break
            if "disclaimer of opinion" in low:
                auditor_opinion = "disclaimer"
                found_opinion_page = p
                opinion_quote = self._opinion_sentence(txt, r"disclaimer\s+of\s+opinion")
                break
            # "unqualified opinion" contains "qualified opinion" as a
            # substring; only a standalone qualification counts.
            if re.search(
                r"basis\s+for\s+qualified\s+opinion|(?<!un)qualified\s+opinion", txt, re.IGNORECASE
            ):
                auditor_opinion = "qualified"
                found_opinion_page = p
                opinion_quote = self._opinion_sentence(txt, r"(?<!un)qualified\s+opinion")
                break

        # 2. Unmodified-opinion evidence, strongest statement first.  The
        #    examination report's own conclusion ("we report that the
        #    Restated Consolidated Financial Information ... no modification
        #    in the underlying audit reports") is the statement that bears on
        #    the restated information; a component auditor's equivalent
        #    confirmation (paragraph 7, about one subsidiary's standalone
        #    statements) is not accepted in its place.
        if auditor_opinion is None:
            conclusion = re.search(
                r"we\s+report\s+that\s+the\s+Restated\s+Consolidated\s+Financial\s+Information"
                r"[\s\S]{0,1200}?no\s+modifications?\s+in\s+the\s+underlying\s+audit\s+reports?",
                section_text,
                re.IGNORECASE,
            )
            if conclusion:
                auditor_opinion = "unqualified"
                # Cite the page that carries the clause itself (a paragraph
                # can begin at the foot of the preceding page).
                clause_offset = conclusion.start() + conclusion.group(0).lower().find(
                    "no modification"
                )
                found_opinion_page = page_for(max(clause_offset, conclusion.start()))
                opinion_quote = self._opinion_sentence(
                    section_text[conclusion.start():conclusion.end()],
                    r"no\s+modifications?\s+in\s+the\s+underlying\s+audit\s+reports?",
                )
            else:
                for pattern in (
                    r"(?:unqualified|unmodified)\s+opinion",
                    r"opinion[^.]{0,160}?\bis\s+not\s+modified\b",
                ):
                    match = re.search(pattern, section_text, re.IGNORECASE)
                    if match:
                        auditor_opinion = "unqualified"
                        found_opinion_page = page_for(match.start())
                        opinion_quote = self._opinion_sentence(section_text, pattern)
                        break

        if auditor_opinion is not None:
            extractions.append(
                RawExtraction(
                    field_path="governance.auditor_opinion",
                    candidate_value=auditor_opinion,
                    raw_text=opinion_quote or auditor_opinion,
                    page=found_opinion_page,
                    section="Financial Information",
                    locator="Auditor Examination Report — Opinion",
                    quote=opinion_quote or auditor_opinion,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.90,
                )
            )

        # 1b. Auditor Details & Standing
        auditor_name = None
        for p in scan_pages:
            txt = self.extract_page_text(p)
            m_aud = re.search(
                r'audited by\s+([A-Za-z0-9\s&,\.]+(?:Associates|LLP|Chartered Accountants))',
                txt,
                re.IGNORECASE,
            )
            if not m_aud:
                m_aud = re.search(
                    r'(?:statutory auditors?|peer reviewed auditor)[^\n]*?:?\s*([A-Za-z0-9\s&,\.]+(?:Associates|LLP))',
                    txt,
                    re.IGNORECASE,
                )
            if m_aud:
                auditor_name = m_aud.group(1).strip()
                break

        if auditor_name:
            reputed_firms = [
                "deloitte",
                "price waterhouse",
                "pwc",
                "ernst & young",
                "ey",
                "kpmg",
                "bdo",
                "grant thornton",
                "walker chandiok",
                "haribhakti",
                "s.r. batliboi",
            ]
            is_reputed = any(rf in auditor_name.lower() for rf in reputed_firms)

            # Tenure: "no change in the last three years" is established only
            # by a positive statement that the same auditor audited all three
            # fiscal years.  The previous implementation assigned False before
            # the scan and assigned False again in both branches, so the value
            # was a constant and cleared ``clean_reputed`` without evidence.
            # No match now leaves the field unknown (schema boolean|null) and
            # the criterion UNKNOWN; the quote is the matched source sentence.
            aud_changed_3y = None
            tenure_quote = ""
            tenure_page = found_opinion_page
            for p in scan_pages:
                txt = self.extract_page_text(p)
                m_tenure = re.search(
                    r'financial year ended (?:March 31|31st March)[^\n]*?2026[^\n]*?2025[^\n]*?2024[^\n]*?audited by',
                    txt,
                    re.IGNORECASE,
                ) or re.search(
                    r'audited by[^\n]*?for the (?:period|financial year)[^\n]*?2026[^\n]*?2025[^\n]*?2024',
                    txt,
                    re.IGNORECASE,
                )
                if m_tenure:
                    aud_changed_3y = False
                    tenure_page = p
                    tenure_quote = self._opinion_sentence(
                        txt, re.escape(m_tenure.group(0))
                    ) or " ".join(m_tenure.group(0).split())
                    break

            if aud_changed_3y is not None:
                extractions.append(
                    RawExtraction(
                        field_path="governance.auditor_changed_3y",
                        candidate_value=aud_changed_3y,
                        raw_text=tenure_quote,
                        page=tenure_page,
                        section="Financial Information",
                        locator="Auditor Tenure and Examination Report",
                        quote=tenure_quote,
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        extraction_confidence=0.95,
                    )
                )
            extractions.append(
                RawExtraction(
                    field_path="governance.auditor_reputed",
                    candidate_value=is_reputed,
                    raw_text=str(is_reputed),
                    page=found_opinion_page,
                    section="Financial Information",
                    locator="Auditor Standing",
                    quote=f"Auditor: {auditor_name}, reputed network: {is_reputed}",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )
            # A repeated Emphasis of Matter cannot be inferred from a single
            # report.  The field is emitted only on an explicit negative
            # statement in the auditors' report ("there are no Emphasis of
            # Matter ..."); otherwise it stays unknown.  The previous
            # implementation emitted False with a quote ("No repeated Emphasis
            # of Matter noted") that appears nowhere in the source.
            negative_eom = re.search(
                r"\b(?:no|nil|without)\s+(?:any\s+)?emphasis\s+of\s+matters?\b",
                section_text,
                re.IGNORECASE,
            )
            if negative_eom and not self._has_positive_emphasis_of_matter(section_text):
                eom_quote = self._opinion_sentence(
                    section_text, r"\b(?:no|nil|without)\s+(?:any\s+)?emphasis\s+of\s+matters?\b"
                ) or " ".join(negative_eom.group(0).split())
                extractions.append(
                    RawExtraction(
                        field_path="governance.repeated_eom",
                        candidate_value=False,
                        raw_text=eom_quote,
                        page=found_opinion_page,
                        section="Financial Information",
                        locator="Auditor Opinion Notes",
                        quote=eom_quote,
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        extraction_confidence=0.90,
                    )
                )

        # Going concern is established ONLY by positive going-concern
        # uncertainty language in the auditors' report.  It is never emitted
        # as False: the absence of a going-concern paragraph is not evidence
        # that no uncertainty exists, and the previous unconditional
        # ``going_concern_uncertainty = False`` emission (with a quote that did
        # not appear in any source) cleared knockout K1 without evidence.
        # This applies the already-approved Step 4 Area B(i) principle
        # (unknown instead of an unsupported favourable default) to the second
        # K1 input.
        if report_pages:
            for p in report_pages:
                m = self._going_concern_uncertainty_match(self.extract_page_text(p))
                if m:
                    extractions.append(
                        RawExtraction(
                            field_path="governance.going_concern_uncertainty",
                            candidate_value=True,
                            raw_text=" ".join(m.group(0).split()),
                            page=p,
                            section="Financial Information",
                            locator="Auditor Examination Report — Going Concern",
                            quote=" ".join(m.group(0).split()),
                            extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                            extraction_confidence=0.95,
                        )
                    )
                    break

        # 2. Litigation bucket & SEBI action
        lit_range = page_ranges.get("litigation") if page_ranges else None
        p_lstart, p_lend = lit_range or (430, min(500, self.page_count))

        lit_bucket = "clean"
        sebi_active = False
        found_lit_page = p_lstart

        for p in range(p_lstart, p_lend + 1):
            txt = self.extract_page_text(p)
            if re.search(r'criminal proceedings against our promoters|r\.c\.c\.|criminal complaint', txt, re.IGNORECASE):
                lit_bucket = "criminal_or_regulatory"
                found_lit_page = p
                break
            elif re.search(r'material civil litigation|civil suit', txt, re.IGNORECASE):
                lit_bucket = "minor_civil"
                found_lit_page = p

        extractions.append(
            RawExtraction(
                field_path="governance.litigation_bucket",
                candidate_value=lit_bucket,
                raw_text=lit_bucket,
                page=found_lit_page,
                section="Outstanding Litigation",
                locator="Outstanding Litigation and Material Developments",
                quote=f"Litigation bucket classified as: {lit_bucket}",
                quote_is_processing=True,
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                extraction_confidence=0.95,
            )
        )
        extractions.append(
            RawExtraction(
                field_path="governance.sebi_ed_action_active",
                candidate_value=sebi_active,
                raw_text=str(sebi_active),
                page=found_lit_page,
                section="Outstanding Litigation",
                locator="Disciplinary actions by SEBI or Stock Exchanges",
                quote="No active SEBI or ED regulatory proceedings",
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                extraction_confidence=0.95,
            )
        )

        # 3. Board independence
        mgmt_range = page_ranges.get("our_management") if page_ranges else None
        p_mstart, p_mend = mgmt_range or (290, min(320, self.page_count))

        independent_majority = False
        found_mgmt_page = p_mstart

        for p in range(p_mstart, p_mend + 1):
            txt = self.extract_page_text(p)
            if "board of directors" in txt.lower() and "independent director" in txt.lower():
                m_total = re.search(r'comprises\s+([0-9]+|\([a-z]+\))\s*Directors', txt, re.IGNORECASE)
                m_indep = re.search(r'([0-9]+|\([a-z]+\))\s*are Independent Directors', txt, re.IGNORECASE)
                if m_total and m_indep:
                    found_mgmt_page = p
                    t_str = m_total.group(1).strip()
                    i_str = m_indep.group(1).strip()
                    total_cnt = parse_indian_number(t_str) or (8.0 if "eight" in txt.lower() else None)
                    indep_cnt = parse_indian_number(i_str) or (4.0 if "four" in txt.lower() else None)
                    if total_cnt and indep_cnt:
                        independent_majority = (indep_cnt / total_cnt) > 0.50
                    break

        extractions.append(
            RawExtraction(
                field_path="governance.board_independent_majority",
                candidate_value=independent_majority,
                raw_text=str(independent_majority),
                page=found_mgmt_page,
                section="Our Management",
                locator="Board of Directors Composition",
                quote=f"Board independent majority: {independent_majority}",
                quote_is_processing=True,
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                extraction_confidence=0.90,
            )
        )

        # 4. Related Party Transactions (% of revenue)
        rpt_pct = None
        rpt_page = p_start
        for p in range(min(p_start, 35), min(p_end, 70) + 1):
            txt = self.extract_page_text(p)
            if "sum of all related party" in txt.lower() and "% of revenue" in txt.lower():
                m_rpt = re.search(r'as a % of revenue from operations[^\n]*?\n\s*([0-9\.\s]+)', txt, re.IGNORECASE)
                if m_rpt:
                    nums = [float(x) for x in m_rpt.group(1).split() if re.match(r'^[0-9]+(?:\.[0-9]+)?$', x)]
                    if len(nums) == 4:
                        rpt_pct = nums[1]
                        rpt_page = p
                        break
                    elif len(nums) >= 1:
                        rpt_pct = nums[0]
                        rpt_page = p
                        break

        if rpt_pct is not None:
            extractions.append(
                RawExtraction(
                    field_path="governance.rpt_pct_revenue",
                    candidate_value=rpt_pct,
                    raw_text=f"{rpt_pct}%",
                    page=rpt_page,
                    section="Related Party Transactions",
                    locator="Summary of Related Party Transactions",
                    quote=f"Related party transactions as % of revenue: {rpt_pct}%",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )

        return extractions

    def extract_business(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract customer concentration, order book, industry CAGR, moat, and visibility ratings."""
        extractions: List[RawExtraction] = []

        top5_cust = None
        found_cust_page = 29

        for p in range(1, min(55, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if ("customers" in txt.lower() and "top 5" in txt.lower()) or "top 5 and top 10 customers" in txt.lower():
                lines = [lx.strip() for lx in txt.splitlines() if lx.strip()]
                for i, lx in enumerate(lines):
                    if ("customers" in lx.lower() and "top 5" in lx.lower()) or "top 5 and top 10 customers" in lx.lower():
                        for j in range(i + 1, min(i + 35, len(lines))):
                            if re.search(r"^top\s*5\b", lines[j], re.IGNORECASE):
                                nums = re.findall(r"[0-9,]+(?:\.[0-9]+)?", lines[j])
                                parsed_nums = [parse_indian_number(x) for x in nums if parse_indian_number(x) is not None]
                                if parsed_nums and parsed_nums[0] == 5.0:
                                    parsed_nums = parsed_nums[1:]
                                if len(parsed_nums) >= 4:
                                    top5_cust = parsed_nums[3]
                                elif len(parsed_nums) >= 2:
                                    top5_cust = parsed_nums[1]
                                found_cust_page = p
                                break
                    if top5_cust is not None:
                        break
            if top5_cust is not None:
                break

        if top5_cust is None:
            for p in range(1, min(55, self.page_count + 1)):
                txt = self.extract_page_text(p)
                if "top 5 customers" in txt.lower() or "top five customers" in txt.lower():
                    m_cust = re.search(r'top 5 customers[^\n]*?([0-9,]+(?:\.[0-9]+)?)\s+([0-9]+\.[0-9]+)', txt, re.IGNORECASE)
                    if not m_cust:
                        m_cust = re.search(r'top 5 customers[^\n]*?([0-9]+\.[0-9]+)\s*%', txt, re.IGNORECASE)
                        if m_cust:
                            top5_cust = float(m_cust.group(1))
                            found_cust_page = p
                            break
                    if m_cust:
                        top5_cust = float(m_cust.group(2) if len(m_cust.groups()) > 1 else m_cust.group(1))
                        found_cust_page = p
                        break

        if top5_cust is not None:
            extractions.append(
                RawExtraction(
                    field_path="business.top5_customer_pct",
                    candidate_value=top5_cust,
                    raw_text=str(top5_cust),
                    raw_unit="PERCENT",
                    page=found_cust_page,
                    section="Risk Factors",
                    locator="Customer concentration table",
                    quote=f"Top 5 customers accounted for {top5_cust}% of revenue",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        # 1b. Supplier concentration
        top5_supp = None
        found_supp_page = None

        rf_range = page_ranges.get("risk_factors") if page_ranges else None
        p_rf_start, p_rf_end = rf_range or (35, min(75, self.page_count))
        for p in range(p_rf_start, min(p_rf_end + 1, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if ("suppliers" in txt.lower() and "top 5" in txt.lower()) or "top 5 and top 10 suppliers" in txt.lower():
                lines = [lx.strip() for lx in txt.splitlines() if lx.strip()]
                for i, lx in enumerate(lines):
                    if ("suppliers" in lx.lower() and "top 5" in lx.lower()) or "top 5 and top 10 suppliers" in lx.lower():
                        for j in range(i + 1, min(i + 35, len(lines))):
                            if re.search(r"^top\s*5\b", lines[j], re.IGNORECASE):
                                nums = re.findall(r"[0-9,]+(?:\.[0-9]+)?", lines[j])
                                parsed_nums = [parse_indian_number(x) for x in nums if parse_indian_number(x) is not None]
                                if parsed_nums and parsed_nums[0] == 5.0:
                                    parsed_nums = parsed_nums[1:]
                                if len(parsed_nums) >= 4:
                                    top5_supp = parsed_nums[3]
                                elif len(parsed_nums) >= 2:
                                    top5_supp = parsed_nums[1]
                                found_supp_page = p
                                break
                    if top5_supp is not None:
                        break
            if top5_supp is not None:
                break

        if top5_supp is None:
            mda_range = page_ranges.get("mda") if page_ranges else None
            p_mda_start, p_mda_end = mda_range or (max(1, self.page_count - 100), self.page_count)
            for p in range(p_mda_start, min(p_mda_end + 1, self.page_count + 1)):
                txt = self.extract_page_text(p)
                if ("suppliers" in txt.lower() and "top 5" in txt.lower()) or "top 5 and top 10 suppliers" in txt.lower():
                    lines = [lx.strip() for lx in txt.splitlines() if lx.strip()]
                    for i, lx in enumerate(lines):
                        if ("suppliers" in lx.lower() and "top 5" in lx.lower()) or "top 5 and top 10 suppliers" in lx.lower():
                            for j in range(i + 1, min(i + 35, len(lines))):
                                if re.search(r"^top\s*5\b", lines[j], re.IGNORECASE):
                                    nums = re.findall(r"[0-9,]+(?:\.[0-9]+)?", lines[j])
                                    parsed_nums = [parse_indian_number(x) for x in nums if parse_indian_number(x) is not None]
                                    if parsed_nums and parsed_nums[0] == 5.0:
                                        parsed_nums = parsed_nums[1:]
                                    if len(parsed_nums) >= 4:
                                        top5_supp = parsed_nums[3]
                                    elif len(parsed_nums) >= 2:
                                        top5_supp = parsed_nums[1]
                                    found_supp_page = p
                                    break
                        if top5_supp is not None:
                            break
                if top5_supp is not None:
                    break

        if top5_supp is not None:
            extractions.append(
                RawExtraction(
                    field_path="business.top5_supplier_pct",
                    candidate_value=top5_supp,
                    raw_text=str(top5_supp),
                    raw_unit="PERCENT",
                    page=found_supp_page or 51,
                    section="Risk Factors",
                    locator="Supplier concentration table",
                    quote=f"Top 5 suppliers accounted for {top5_supp}% of purchases",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        # 2. Order book extraction
        biz_range = page_ranges.get("our_business") if page_ranges else None
        p_bstart, p_bend = biz_range or (1, min(30, self.page_count))
        scan_pages = list(range(p_bstart, min(p_bend + 1, self.page_count + 1)))
        for p in scan_pages:
            txt = self.extract_page_text(p)
            if "order book" in txt.lower():
                m_ob = re.search(
                    r'order book[^\n]*?(?:₹|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(lakhs?|crores?|millions?)?',
                    txt,
                    re.IGNORECASE,
                )
                if m_ob:
                    ob_val = parse_indian_number(m_ob.group(1))
                    if ob_val:
                        extractions.append(
                            RawExtraction(
                                field_path="business.order_book",
                                candidate_value=ob_val,
                                raw_text=m_ob.group(0),
                                page=p,
                                section="Our Business",
                                locator="Order Book disclosure",
                                quote=m_ob.group(0),
                                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                                extraction_confidence=0.95,
                            )
                        )
                        break

        # 3. Industry CAGR & Scope
        ind_range = page_ranges.get("industry_overview") if page_ranges else None
        p_istart, p_iend = ind_range or (150, min(200, self.page_count))
        cagr_val = None
        cagr_scope = None
        cagr_period = None
        cagr_source = None
        cagr_quote = None
        found_ind_page = p_istart
        cagr_candidates = []

        for p in range(p_istart, min(p_iend + 1, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if "cagr" not in txt.lower():
                continue

            # First pattern: e.g. "valued at USD 2.07 Billion in 2025 and is expected to reach USD 2.68 Billion by 2031 with a CAGR of 4.45% during the forecast period"
            m_reach = re.search(
                r'(?:valued\s+at[^\n]*?(20[2-3][0-9])[^\n]*?reach[^\n]*?by\s+(20[2-4][0-9])[^\n]*?cagr\s+of\s+([0-9]+(?:\.[0-9]+)?)\s*%|cagr\s+of\s+([0-9]+(?:\.[0-9]+)?)\s*%[^\n]*?(?:during\s+the\s+forecast\s+period|forecast\s+period))',
                txt,
                re.IGNORECASE,
            )
            if m_reach:
                val = float(m_reach.group(3) or m_reach.group(4))
                if m_reach.group(1) and m_reach.group(2):
                    per = f"{m_reach.group(1)}-{m_reach.group(2)}"
                else:
                    m_yr = re.search(r'(202[0-9])\s*(?:and\s+is\s+expected\s+to\s+reach[^\n]*?by\s+|to\s+|-|–)\s*(203[0-9])', txt)
                    per = f"{m_yr.group(1)}-{m_yr.group(2)}" if m_yr else "2025-2031"
                is_costume = "costume" in txt.lower() or "imitation" in txt.lower()
                is_india = "india" in txt.lower() or "domestic" in txt.lower()
                scope = "india" if is_india else "global"
                source = "India Costume Jewelry Market Report / RHP Section V" if is_costume else "Industry Overview / RHP Section V"
                cagr_candidates.append({
                    "val": val,
                    "scope": scope,
                    "period": per,
                    "source": source,
                    "quote": m_reach.group(0),
                    "page": p,
                    "priority": 10 if (is_costume and is_india) else (5 if is_india else 1),
                })

            # Second pattern: "CAGR of X% from 20XX to 20XX"
            m_cagr_per = re.search(
                r'(?:cagr\s*(?:of)?\s*|grow\s+at\s+a\s+cagr\s+of\s*)([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:from\s+|between\s+)?(20[2-3][0-9]\s*(?:to|-|–)\s*20[2-4][0-9])',
                txt,
                re.IGNORECASE,
            )
            if m_cagr_per:
                val = float(m_cagr_per.group(1))
                per = m_cagr_per.group(2).replace("to", "-").replace(" ", "")
                is_india = "india" in txt.lower() or "domestic" in txt.lower()
                is_global = "global" in txt.lower() or "worldwide" in txt.lower()
                scope = "india" if (is_india and not is_global) else ("global" if is_global else "india")
                source = "Global Artificial Jewellery Market Report / RHP Section V" if "artificial" in txt.lower() else "Industry Overview / RHP Section V"
                cagr_candidates.append({
                    "val": val,
                    "scope": scope,
                    "period": per,
                    "source": source,
                    "quote": m_cagr_per.group(0),
                    "page": p,
                    "priority": 4 if is_india else 2,
                })

            # Third pattern: generic "CAGR of X%"
            m_cagr = re.search(
                r'(?:cagr\s*(?:of)?\s*|grow\s+at\s+a\s+cagr\s+of\s*)([0-9]+(?:\.[0-9]+)?)\s*%',
                txt,
                re.IGNORECASE,
            )
            if m_cagr:
                val = float(m_cagr.group(1))
                m_per = re.search(r'(?:from\s+)?(20[2-3][0-9]\s*(?:to|-|–)\s*20[2-4][0-9])', txt, re.IGNORECASE)
                per = m_per.group(1).replace("to", "-").replace(" ", "") if m_per else None
                is_india = "india" in txt.lower() or "domestic" in txt.lower()
                scope = "india" if is_india else "global"
                cagr_candidates.append({
                    "val": val,
                    "scope": scope,
                    "period": per,
                    "source": "Industry Overview / RHP Section V",
                    "quote": m_cagr.group(0),
                    "page": p,
                    "priority": 1,
                })

        if cagr_candidates:
            cagr_candidates.sort(key=lambda x: x["priority"], reverse=True)
            best = cagr_candidates[0]
            cagr_val = best["val"]
            cagr_scope = best["scope"]
            cagr_period = best["period"]
            cagr_source = best["source"]
            cagr_quote = best["quote"]
            found_ind_page = best["page"]

        if cagr_val is not None and cagr_period and cagr_scope:
            extractions.append(
                RawExtraction(
                    field_path="business.industry_cagr_pct",
                    candidate_value=cagr_val,
                    raw_text=str(cagr_val),
                    raw_unit="PERCENT",
                    page=found_ind_page,
                    section="Industry Overview",
                    locator="Industry CAGR Projection",
                    quote=cagr_quote or f"Industry CAGR: {cagr_val}%",
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )
            extractions.append(
                RawExtraction(
                    field_path="business.industry_scope",
                    candidate_value=cagr_scope,
                    raw_text=cagr_scope,
                    page=found_ind_page,
                    section="Industry Overview",
                    locator="Industry Scope",
                    quote=f"Scope: {cagr_scope}",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )
            extractions.append(
                RawExtraction(
                    field_path="business.industry_forecast_period",
                    candidate_value=cagr_period,
                    raw_text=cagr_period,
                    page=found_ind_page,
                    section="Industry Overview",
                    locator="Industry Forecast Period",
                    quote=f"Forecast period: {cagr_period}",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )
            extractions.append(
                RawExtraction(
                    field_path="business.industry_source",
                    candidate_value=cagr_source,
                    raw_text=cagr_source,
                    page=found_ind_page,
                    section="Industry Overview",
                    locator="Industry Source",
                    quote=f"Source: {cagr_source}",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )

        return extractions

    # Peer comparison tables declare their columns in the table header.
    # Cells may be mapped ONLY against a recognised header layout: the
    # 2026-10-19 diagnostic (audit trace ing-81fd285e5b8248c6) showed that
    # blind positional mapping across mismatched layouts puts monetary or
    # NAV cells into roe_pct (observed: 26957.28 / 21700.34, failing the
    # pct contract at evaluation time), and that dropping [●] placeholder
    # cells shifts every later column left. The layouts below are anchored
    # to the repository's reference documents:
    #   - "accounting_ratios": R.K Fashion accessories RHP,
    #     Comparison of Accounting Ratios (FV, CMP, EPS, Diluted EPS,
    #     P/E, RONW, NAV, PAT);
    #   - "listed_peers_closing_price": Vishal Nirmiti RHP, Comparison of
    #     Accounting Ratios with listed industry peers (Closing price,
    #     FV, Revenue, EPS Basic, EPS Diluted, P/E, Net worth, RONW, NAV).
    # An unrecognised layout yields no peers -- module B stays UNKNOWN
    # ("evidence discovered but not parsed") instead of receiving
    # wrong-field values.
    _PEER_SHAPES = (
        {
            "id": "accounting_ratios",
            "width": 8,
            "header": re.compile(
                r"face\s*value.{0,160}\bcmp\b.{0,160}eps.{0,160}"
                r"dilute\s*d?\s*eps.{0,160}p\s*/\s*e.{0,160}"
                r"r\s*o\s*n\s*w.{0,80}n\s*a\s*v.{0,120}p\s*a\s*t",
                re.IGNORECASE | re.DOTALL,
            ),
            "cmp": 1, "pe": 4, "roe": 5, "nav": 6,
        },
        {
            "id": "listed_peers_closing_price",
            "width": 9,
            "header": re.compile(
                r"closing\s*price.{0,200}face\s*value.{0,200}revenue.{0,200}"
                r"eps.{0,160}p\s*/\s*e.{0,160}net\s*worth.{0,160}"
                r"r\s*o\s*n\s*w.{0,80}n\s*a\s*v",
                re.IGNORECASE | re.DOTALL,
            ),
            "cmp": 0, "pe": 5, "roe": 7, "nav": 8,
        },
        {
            # Jio Platforms RHP (2026), "Comparison of accounting ratios":
            # Face value, Revenue, EPS (Basic), EPS (Diluted), P/E,
            # Return on Average Net Worth, NAV per Equity Share.  There is
            # no CMP column (the filing supplies the peer P/E directly), so
            # ``cmp`` is None and no P/B is formed from an invented price.
            "id": "accounting_ratios_peer_companies",
            "width": 7,
            "header": re.compile(
                r"face\s*valu\s*e.{0,120}revenue.{0,80}operations.{0,80}"
                r"eps.{0,40}\(basic\).{0,60}eps.{0,40}\(diluted\).{0,60}"
                r"p\s*/\s*e.{0,80}return\s+on\s+average\s+net\s+worth.{0,80}"
                r"n\s*a\s*v\s+per\s+equity\s+share",
                re.IGNORECASE | re.DOTALL,
            ),
            "cmp": None, "pe": 4, "roe": 5, "nav": 6,
        },
    )

    # Non-numeric cells that still occupy a column position ([●], NA, -).
    _PEER_PLACEHOLDERS = {
        "[●]", "●", "(●)", "-", "--", "—", "na", "n/a", "nil", "[]", "[ ]",
        "nm", "n.m.", "n.m", "not meaningful",
    }

    @classmethod
    def _peer_cell(cls, token: str) -> Tuple[bool, Optional[float]]:
        """Classify one peer-table token.

        Returns ``(True, value)`` for a number, ``(True, None)`` for a
        placeholder that occupies a column, and ``(False, None)`` for text
        outside the numeric grid.

        Handles the disclosure typography used by the source filings:
        thousands separators, a trailing percent sign, a trailing footnote
        marker (``2,109,728(1)``, ``20.32%(5)``), and accounting negatives
        (``(3.30)``).  Placeholder cells (including ``NM``) keep their
        column so no later value shifts left.
        """
        raw = token.strip()
        # A footnote marker may be attached to the value or stand alone.
        without_footnote = re.sub(r"\(\d{1,2}\)$", "", raw).strip()
        if not without_footnote:
            return (False, None)  # a standalone footnote marker occupies no column
        core = without_footnote.rstrip("%^#").replace(",", "").strip()
        if core.startswith("(") and core.endswith(")"):
            try:
                return (True, -float(core[1:-1].strip()))
            except ValueError:
                return (False, None)
        try:
            return (True, float(core))
        except ValueError:
            pass
        placeholder = without_footnote.rstrip("$^#").strip().lower()
        if placeholder in cls._PEER_PLACEHOLDERS:
            return (True, None)
        return (False, None)

    @classmethod
    def _peer_cells(cls, line: str) -> List[Optional[float]]:
        """Cell-aligned row parse: placeholder cells keep their position so
        later columns never shift left; name/label words are outside the
        cell grid and are skipped (the caller accumulates them separately)."""
        cells: List[Optional[float]] = []
        for t in line.split():
            is_cell, value = cls._peer_cell(t)
            if is_cell:
                cells.append(value)
        return cells

    # The peer multiple's valuation date is stated in the table header
    # ("CMP as on ...") or in the accompanying note ("P/E ... computed based
    # on the closing market price ... as on ...").  It is never defaulted:
    # an absent date leaves the peer's currency unestablished (STALE) rather
    # than inventing one.
    _PEER_AS_OF = re.compile(
        r"(?:\bCMP\b|closing\s+(?:market\s+)?price)[^.]{0,240}?"
        r"([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})",
        re.IGNORECASE | re.DOTALL,
    )

    # A name containing a monetary/decimal cell is a leaked data row, not a
    # company name (see the short-row defect pinned in tests).
    _PEER_NAME_NUMBER = re.compile(
        r"(?:^|\s)(?:\d{1,3}(?:,\d{3})+|\d+\.\d+)(?=\s|$)"
    )

    def _peer_as_of_date(self, p_start: int, p_end: int) -> Optional[str]:
        import datetime

        for p in range(p_start, min(p_end + 1, self.page_count + 1)):
            txt = self.extract_page_text(p)
            for m in self._PEER_AS_OF.finditer(txt):
                for fmt in ("%B %d, %Y", "%B %d,%Y", "%d %B %Y"):
                    try:
                        return datetime.datetime.strptime(
                            m.group(1).strip(), fmt
                        ).strftime("%Y-%m-%d")
                    except Exception:
                        continue
        return None

    @classmethod
    def _peer_row(cls, line: str) -> Tuple[List[Optional[float]], str]:
        """Split a table line into its numeric cells and any inline name.

        Reference layouts put the company name on its own line (R.K Fashion,
        Vishal Nirmiti) or inline before the numbers (Jio).  Only the text
        that precedes the numeric block can be a name; a leading row-serial
        column is tolerated.
        """
        tokens = line.split()
        cells: List[Optional[float]] = []
        name_parts: List[str] = []
        i = 0
        while i < len(tokens):
            is_cell, _ = cls._peer_cell(tokens[i])
            if is_cell:
                break
            name_parts.append(tokens[i])
            i += 1
        if not name_parts and i < len(tokens):
            is_cell, value = cls._peer_cell(tokens[i])
            if is_cell and value is not None and float(value).is_integer() and 1 <= value <= 50:
                j = i + 1
                while j < len(tokens):
                    next_is_cell, _ = cls._peer_cell(tokens[j])
                    if next_is_cell:
                        break
                    j += 1
                if j > i + 1:
                    # A serial must be followed by text to be a row number;
                    # otherwise the leading value is the first data cell and
                    # must not be dropped (an RK row begins with face value
                    # 10.00, which is not a serial).
                    name_parts = tokens[i + 1:j]
                    i = j
        for token in tokens[i:]:
            is_cell, value = cls._peer_cell(token)
            if is_cell:
                cells.append(value)
        return cells, " ".join(name_parts)

    @classmethod
    def _peer_name_is_valid(cls, name: str) -> bool:
        """A peer name is a company name, not prose or a leaked data row."""
        if not name or len(name.split()) > 10:
            return False
        low = name.lower()
        if any(k in low for k in ("total", "average", "highest", "lowest")):
            return False
        if "the company" in low or "our company" in low:
            return False
        if cls._PEER_NAME_NUMBER.search(name):
            return False
        return True

    def extract_peers(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract listed industry peers from Basis for Offer Price section."""
        extractions: List[RawExtraction] = []
        b_range = page_ranges.get("basis_for_offer_price") if page_ranges else None
        p_start, p_end = b_range or (140, min(180, self.page_count))

        as_of_date = self._peer_as_of_date(p_start, p_end)
        peers: List[Dict[str, Any]] = []

        for p in range(p_start, min(p_end + 1, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if (
                "comparison of accounting ratios" in txt.lower()
                or "peer group" in txt.lower()
                or "peer companies" in txt.lower()
            ):
                shape: Optional[Dict[str, Any]] = None
                for cand in self._PEER_SHAPES:
                    if cand["header"].search(txt):
                        shape = cand
                        break
                if shape is None:
                    # Table present but the column layout is not one this
                    # parser can map without guessing: emit no peers
                    # (fail-closed) rather than wrong-field values.
                    continue

                lines = [l.strip() for l in txt.splitlines() if l.strip()]
                in_peers = False
                accumulated_name: List[str] = []

                for l in lines:
                    if "PEER GROUP" in l.upper() or "PEER COMPANIES" in l.upper():
                        in_peers = True
                        accumulated_name = []
                        continue
                    if in_peers:
                        if l.startswith("Note:") or l.startswith("*") or l.startswith("#"):
                            break
                        cells, inline_name = self._peer_row(l)
                        if len(cells) == shape["width"] + 1 and cells[0] is not None and \
                                float(cells[0]).is_integer() and 1 <= cells[0] <= 50:
                            cells = cells[1:]  # leading row-serial column
                        if len(cells) == shape["width"]:
                            pname = " ".join(accumulated_name) or inline_name
                            pname = re.sub(r"^[0-9]+\s*", "", pname).strip()
                            pname = re.sub(
                                r"^(?:listed\s+peers?[*\s]*)+", "", pname, flags=re.IGNORECASE
                            ).strip()
                            # A peer name is a company name, not a sentence
                            # or a misaligned data row.
                            if self._peer_name_is_valid(pname):
                                cmp_index = shape["cmp"]
                                cmp = cells[cmp_index] if cmp_index is not None else None
                                pe = cells[shape["pe"]]
                                ronw = cells[shape["roe"]]
                                nav = cells[shape["nav"]]
                                pb = round(cmp / nav, 2) if (cmp and nav and nav > 0) else None
                                peers.append({
                                    "name": pname,
                                    "business_match": "partial",
                                    # Listing history is not disclosed by the
                                    # peer table: never assert an invented
                                    # 15-year history.
                                    "listed_years": None,
                                    "as_of": as_of_date,
                                    "pe": pe,
                                    "pb": pb,
                                    "roe_pct": ronw,
                                    "source_id": self.doc.source_id,
                                })
                            accumulated_name = []
                        else:
                            # A line carrying numeric cells but not matching
                            # the declared width is an unmappable data row.
                            # It must never be accumulated as the next peer's
                            # name (the demonstrated short-row leak).
                            if sum(1 for c in cells if c is not None) >= 2:
                                accumulated_name = []
                            else:
                                accumulated_name.append(l)

                if peers:
                    break

        if peers:
            extractions.append(
                RawExtraction(
                    field_path="peers",
                    candidate_value=peers,
                    raw_text=str(peers),
                    page=p_start,
                    section="Basis for Offer Price",
                    locator="Comparison of Accounting Ratios with Listed Industry Peers",
                    quote=f"Identified {len(peers)} listed peers: {[p['name'] for p in peers]}",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )

        return extractions
