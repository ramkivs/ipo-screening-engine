"""Domain section extractors for RHP prospectuses.

Extracts non-table and hybrid sections according to ICDR layout:
  - Cover page & The Offer (company name, fresh issue, OFS, price band, lot size, quotas)
  - Capital Structure (promoter holding, pledge, lock-in)
  - Objects of the Offer (schedule of proceeds, Capex, Debt, Working Capital, GCP [●])
  - Governance & Management (auditor opinion, litigation, board independence, RPT)
  - Business & Industry (customer concentration, industry CAGR, moat, visibility)
"""

from __future__ import annotations

import datetime
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
    r'(?P<label>offer\s+for\s+sale(?:\s+size)?)[^\n]*?(?:[^\n]*?\n){0,32}?\s*(?:NIL|Not\s+Applicable)\b',
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

# ---------------------------------------------------------------------------
# Issue window on the cover
# ---------------------------------------------------------------------------
# A filed cover prints the window as a labelled row, and a filed cover also
# carries footnote markers inside that row:
#     BID/OFFER OPENS ON WEDNESDAY OCTOBER 21, 2026 BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026
# The ``#`` (or ``*``, ``(1)``) refers to the UPI-mandate footnote below the
# table.  Requiring whitespace directly after the label made the *closing* date
# unreadable on such a cover while the opening date -- which carried no marker
# -- was read normally, so the issue window arrived half-populated.  The
# marker is now tolerated between the label and the date.
#
# This does not widen what counts as an issue date: the date must still follow
# the ``opens on`` / ``closes on`` label of the issue (or bid/offer) window,
# so a certificate date, an allotment date or an Articles defined term can
# never be picked up.
_FOOTNOTE_CHARS = r"[\s\u2020\u2021\u00a7\u00b6#*-]*"
_FOOTNOTE_MARKER = (
    _FOOTNOTE_CHARS
    + r"(?:\([0-9#*\u2020]+\)|[0-9]{1,2})?"
    + _FOOTNOTE_CHARS
)
_ISSUE_DATE_TAIL = (
    _FOOTNOTE_MARKER
    + r":?\s*(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*)?"
    + r"([A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4})"
)
_ISSUE_WINDOW_LABEL = r"(?:issue|bid(?:\s*/\s*offer)?)\s*"
_ISSUE_OPENS = re.compile(_ISSUE_WINDOW_LABEL + r"opens?\s*(?:on)?" + _ISSUE_DATE_TAIL, re.IGNORECASE)
_ISSUE_CLOSES = re.compile(_ISSUE_WINDOW_LABEL + r"closes?\s*(?:on)?" + _ISSUE_DATE_TAIL, re.IGNORECASE)

#: ``aggregating (up) to ₹ N <unit>`` -- the explicit monetary statement of an
#: offer component.  The currency token is required so an unrelated
#: "aggregating to 5,000,000 shares" is not read as money.
_COMPONENT_AMOUNT = re.compile(
    r"aggregating(?:\s+up)?\s+to\s+(?:\u20b9|Rs\.?|INR)\s*"
    r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(lakhs?|crores?|millions?)",
    re.IGNORECASE,
)
#: Labels that end a component's own assertion, so a following component's
#: amount can never be bound backwards into it.
_COMPONENT_BOUNDARY = re.compile(
    r"fresh\s+(?:issue|offer)|offer\s+for\s+sale|total\s+(?:issue|offer)"
    r"|reservation|employee|shareholder|anchor",
    re.IGNORECASE,
)
#: A component label immediately *before* this one, optionally joined by
#: "and"/"&"/",": a merged header cell ("Fresh Issue and Offer for Sale") or an
#: adjacent column label.  Such a label does not say which column the following
#: money belongs to, so the amount is not bound to this component -- reading it
#: in text order gave the Offer for Sale the fresh-issue figure on a two-column
#: cover table.
_COMPONENT_ADJACENT_LABEL = re.compile(
    r"(?:" + _COMPONENT_BOUNDARY.pattern + r")\s*(?:and|&|/|\+|,)?\s*$",
    re.IGNORECASE,
)


def _find_ofs_nil(cover_text: str) -> Optional[str]:
    """Return the matched OFS-NIL quotation, or None when it is ambiguous.

    Accepted:
      * "Offer for Sale Size: Not applicable" (same line);
      * "OFFER FOR SALE SIZE" followed by a value line "Not applicable";
      * "OFFER FOR SALE SIZE" followed by a fresh row and then the OFS cell
        "Not applicable" (the real Jio cover shape), including a reader-wrapped
        label such as "OFFER FOR\nSALE SIZE".

    Rejected:
      * an OFS label line that itself states an amount or quantity;
      * a NIL that is the value of a bare Fresh Issue / Pre-IPO / Promoter /
        reservation / total-issue label, on its own line, as the previous line,
        or as a wrapped preceding label.
    """
    for match in _OFS_NIL_PATTERN.finditer(cover_text):
        quote = match.group(0)
        # Start AFTER the complete (possibly wrapped) label, so an amount
        # on "SALE SIZE Rs. ..." is still checked, not hidden by the wrap.
        after_label = cover_text[match.end("label"):match.end()].split("\n", 1)[0]
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
        # Competing bare labels can wrap too (e.g. "TOTAL ISSUE\nSIZE").
        # Retain both original guards and reject their wrapped equivalents.
        label_lines = before.split("\n")[-4:] + [line_prefix]
        if any(_OFS_NIL_BARE_LABEL.match("\n".join(label_lines[-n:]).strip())
               for n in range(2, min(5, len(label_lines)) + 1)):
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
        # A25-D2 (approved 2026-10-20): per-page extraction status, so a page whose
        # text extraction *failed* is never indistinguishable from a page that was
        # read and came back blank.  Values: READ, BLANK, FAILED, OUT_OF_RANGE.
        # Nothing else changes -- the returned text and the shared cache behave
        # exactly as before, so no existing extraction result can move.
        self._page_status: Dict[int, str] = {}

    def extract_page_text(self, page_1_indexed: int) -> str:
        """Extract text from a 1-indexed page with caching."""
        if page_1_indexed in self._text_cache:
            return self._text_cache[page_1_indexed]
        if 1 <= page_1_indexed <= self.page_count:
            try:
                txt = self.reader.pages[page_1_indexed - 1].extract_text() or ""
                self._page_status[page_1_indexed] = "READ" if txt else "BLANK"
            except Exception:
                txt = ""
                self._page_status[page_1_indexed] = "FAILED"
            self._text_cache[page_1_indexed] = txt
            return txt
        self._page_status[page_1_indexed] = "OUT_OF_RANGE"
        return ""

    @property
    def page_status(self) -> Dict[int, str]:
        """How each touched page was read (A25-D2 observability)."""
        return dict(self._page_status)

    def pages_read(self, start: int, end: int) -> bool:
        """True when every page of ``[start, end]`` was read or was blank.

        A page that failed to extract, or that this document does not contain,
        leaves the range incompletely read.  That is insufficient evidence for a
        conclusion of *absence* and is never treated as one; it says nothing
        about a page that was read and did contain a finding.  A range covering
        no page of this document was not searched at all, so it is not read
        either -- the empty case is deliberately not vacuously true.
        """
        if start > self.page_count or end < 1:
            return False
        for page in range(max(1, start), min(end, self.page_count) + 1):
            status = self._page_status.get(page)
            if status is None:
                # No status recorded for a page this instance did not extract.
                # Text supplied through the shared cache counts as read; a page
                # nobody touched is not evidence of anything, least of all of an
                # absence.
                if page not in self._text_cache:
                    return False
                continue
            if status not in ("READ", "BLANK"):
                return False
        return True

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
    def _explicit_component_amount(
        cls,
        text: str,
        label_pattern: str,
        excluded: Sequence[str],
    ) -> Optional[Tuple[float, str, str, str]]:
        """The explicit ``aggregating up to ₹ N <unit>`` for one offer component.

        Returns ``(value, unit, quote, raw_text)`` or ``None``.  Two rules keep
        the money apart from the shares and from the other component:

        * the search for an amount stops at the next component label, so a
          following component's amount can never be bound backwards; and
        * a match whose own text runs through an excluded label (the Offer for
          Sale for a fresh-issue search, and the reverse) is not a statement
          about this component.

        Distinct surviving amounts are contradictory evidence and the field is
        withheld -- the same fail-closed rule the share quantity already
        follows.  An amount is never inferred from a share count or a price.
        """
        found: List[Tuple[float, str, str, str]] = []
        for label_match in re.finditer(label_pattern + r"\b", text, re.IGNORECASE):
            if _COMPONENT_ADJACENT_LABEL.search(text[max(0, label_match.start() - 60): label_match.start()]):
                continue  # merged header cell / adjacent column: column unknown
            segment = text[label_match.end(): label_match.end() + 300]
            boundary = _COMPONENT_BOUNDARY.split(segment, maxsplit=1)[0]
            amount = _COMPONENT_AMOUNT.search(boundary)
            if not amount:
                continue
            between = boundary[: amount.start()].lower()
            if any(marker in between for marker in excluded):
                continue
            value = parse_indian_number(amount.group(1))
            if value is None:
                continue
            quote = text[label_match.start(): label_match.end() + amount.end()]
            found.append((value, amount.group(2).upper(), quote, amount.group(1)))
        distinct = {(value, unit) for value, unit, _quote, _raw in found}
        if len(distinct) > 1:
            return None
        return found[0] if found else None

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
        m_open = _ISSUE_OPENS.search(cover_text)
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

        m_close = _ISSUE_CLOSES.search(cover_text)
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

        m_fresh = self._explicit_component_amount(
            cover_text,
            r'fresh\s+(?:offer|issue)',
            excluded=("offer for sale", "selling shareholder", "ofs"),
        )
        if m_fresh:
            num_val, unit_val, quote, raw_val = m_fresh
            extractions.append(
                RawExtraction(
                    field_path="issue.fresh_issue",
                    candidate_value=num_val,
                    raw_text=raw_val,
                    raw_unit=unit_val,
                    page=1,
                    section="Cover",
                    locator="Cover page, Fresh Offer",
                    quote=quote,
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
            # 3a. The explicit monetary Offer for Sale.
            # The share count on a filed cover is routinely a ``[●]``
            # placeholder until the price band is fixed, while the money is
            # already stated: "OFFER FOR SALE OF UP TO [●] EQUITY SHARES ...
            # AGGREGATING UP TO ₹ 9,500.00 MILLION".  The upload path used to
            # read only NIL and (for a sole seller) a share quantity, so a
            # disclosed monetary OFS never reached the canonical input at all
            # and ``issue.ofs`` stayed unknown on a filing that discloses it.
            # The amount is read independently of the share count, never
            # inferred from it, and withheld when the cover states two
            # different amounts.
            m_ofs_amount = self._explicit_component_amount(
                cover_text,
                r'offer\s+for\s+sale',
                excluded=("fresh offer", "fresh issue"),
            )
            if m_ofs_amount:
                ofs_val, ofs_unit, ofs_amount_quote, ofs_raw = m_ofs_amount
                extractions.append(
                    RawExtraction(
                        field_path="issue.ofs",
                        candidate_value=ofs_val,
                        raw_text=ofs_raw,
                        raw_unit=ofs_unit,
                        page=1,
                        section="Cover",
                        locator="Cover page, Offer for Sale Amount",
                        quote=ofs_amount_quote,
                        extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                        extraction_confidence=0.98,
                    )
                )

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

    # Category headings inside a shareholding table.  In the ICDR summary
    # layout (A) is "Promoter & Promoter Group" and (B) is "Public"; in the
    # detailed layout (A) is "Promoters" and (B) is "Promoter Group".  The
    # label above the (B) total decides whether it belongs in the promoter
    # figure, so the public category is never added to the promoter holding.
    _PROMOTER_CATEGORY_LABEL = re.compile(
        r"^\s*(?:\(?\s*[A-Za-z0-9]{1,3}\s*\)?\s*[.):]?\s*)?"
        r"(promoter\s*(?:&|and)\s*promoter\s*group|promoters?|promoter\s*group"
        r"|public(?:\s+shareholders?)?|non[-\s]?promoter[^\n]*)\s*:?\s*$",
        re.IGNORECASE,
    )
    # A post-issue column is used only when the table says so explicitly.
    _POST_ISSUE_CONTEXT = re.compile(
        r"post\s*[-\s]?\s*(?:offer|issue)|after\s+the\s+(?:offer|issue)|on\s+allotment",
        re.IGNORECASE,
    )

    @classmethod
    def _promoter_category_before(cls, lines: List[str], idx: int, window: int = 60) -> Optional[str]:
        """The nearest category heading above a total row, if any."""
        for k in range(idx - 1, max(-1, idx - window - 1), -1):
            match = cls._PROMOTER_CATEGORY_LABEL.match(lines[k])
            if match:
                return match.group(1).strip().lower()
        return None

    @staticmethod
    def _category_kind(label: Optional[str]) -> Optional[str]:
        """``promoter`` / ``other`` / ``None`` (unknown) for a category label."""
        if not label:
            return None
        if "non-promoter" in label or "non promoter" in label:
            return "other"
        if "public" in label:
            return "other"
        if "promoter" in label:
            return "promoter"
        return None

    @staticmethod
    def _row_percentages(lines: List[str], idx: int) -> List[float]:
        """Read intact decimal cells from a labelled, possibly wrapped total.

        PDF layout engines can split a share count and put the remaining cells
        on several lines. Continue only through numeric/placeholder-only text;
        category labels, named/numbered shareholders, totals and prose end the
        row. Never search ahead across such a boundary for missing cells.
        The bound also makes an unterminated/malformed row fail closed.
        """
        parts = [lines[idx]]
        for nxt in lines[idx + 1:idx + 17]:
            if (not nxt.strip()
                    or re.match(r"^\s*\d+[.)]\s", nxt)
                    or not re.fullmatch(r"[\d\s,.%\[\]●•*–—−-]+", nxt)):
                break
            parts.append(nxt)
        else:
            # More than sixteen continuation lines cannot be safely assigned
            # to this row. Do not expose a partially collected post column.
            if idx + 17 < len(lines) and re.fullmatch(
                    r"[\d\s,.%\[\]●•*–—−-]+", lines[idx + 17]):
                return []
        window = " ".join(parts)
        values = [float(x) for x in re.findall(r"[0-9]+\.[0-9]+", window)]
        percentages = [v for v in values if 0.0 <= v <= 100.0]
        # Wrapped pre + lower/upper post tables have at most three percentage
        # cells. Overflow cannot be assigned to that layout safely: it may be
        # an unlabelled neighbouring numeric row, not another post scenario.
        if len(parts) > 1 and len(percentages) > 3:
            return []
        # An undisclosed cell is not an absent column. Do not collapse a
        # partial post-offer row and mistake a lower-band value for the upper
        # band (or a pre-offer value for a post-offer one).
        marker = re.search(r"\[[●•*]\]|(?<!\S)[–—−-](?!\S)", window)
        if marker:
            first = re.search(r"[0-9]+\.[0-9]+", window)
            return percentages[:1] if first and first.start() < marker.start() else []
        return percentages

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
        pledge_page: Optional[int] = found_page
        pledge_quote: Optional[str] = None
        lockin_page: Optional[int] = found_page
        lockin_quote: Optional[str] = None
        sentence_pre_pct: Optional[float] = None
        sentence_pre_page: Optional[int] = None
        sentence_pre_quote: Optional[str] = None

        # An explicit no-pledge statement is evidence, and it is quoted as
        # printed.  The previous pattern required the plural ("our promoters
        # are pledged"), so a filing stating the singular -- "none of the
        # Equity Shares held by our Promoter are pledged", the ordinary wording
        # where there is a single promoter -- matched nothing and the value
        # fell through to a 0.0 default.  The number was the same, but it was
        # unevidenced, and the emitted quotation was a synthesised sentence
        # that appears nowhere in the filing (the A22/A23 quotation rule).
        pledge_re = re.compile(
            r"none\s+of\s+the\s+equity\s+shares\s+held\s+by\s+our\s+promoters?\s+"
            r"(?:are|is)\s+pledged",
            re.IGNORECASE,
        )
        lockin_re = re.compile(
            r"locked[\s-]*in\s+(?:for\s+)?(?:a\s+period\s+of\s+)?"
            r"(?:18\s+months|one\s+year|three\s+years|1\s+year|3\s+years)",
            re.IGNORECASE,
        )
        pre_sentence_re = re.compile(
            r"(?:equivalent\s+to|representing|comprising)\s+(?P<pct>\d{1,3}\.\d{1,2})\s*%\s+of\s+the\s+"
            r"issued,\s*subscribed\s+and\s+paid-?up",
            re.IGNORECASE,
        )

        # Concatenate text across the section pages to cover tables spanning page breaks
        cap_lines: List[str] = []
        for p in range(p_start, min(p_end + 1, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if pledge_pct is None:
                m_pledge = pledge_re.search(" ".join(txt.split()))
                if m_pledge:
                    pledge_pct = 0.0
                    pledge_page = p
                    pledge_quote = m_pledge.group(0)
            if lockin is None:
                m_lockin = lockin_re.search(" ".join(txt.split()))
                if m_lockin:
                    lockin = True
                    lockin_page = p
                    lockin_quote = m_lockin.group(0)
            if sentence_pre_pct is None:
                m_pre = pre_sentence_re.search(" ".join(txt.split()))
                if m_pre:
                    value = parse_indian_number(m_pre.group("pct"))
                    if value is not None and 0 < value <= 100:
                        sentence_pre_pct = value
                        sentence_pre_page = p
                        sentence_pre_quote = m_pre.group(0)
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
            a_values: List[float] = []
            b_values: List[float] = []
            b_found = False
            b_category: Optional[str] = None
            for idx, l in enumerate(cap_lines):
                if not a_values and self._TOTAL_A_LABEL.search(l):
                    a_values = self._row_percentages(cap_lines, idx)
                    for j in range(idx + 1, min(idx + 200, len(cap_lines))):
                        if re.search(r'Total\s*\(\s*B\s*\)', cap_lines[j], re.IGNORECASE):
                            b_found = True
                            b_values = self._row_percentages(cap_lines, j)
                            b_category = self._promoter_category_before(cap_lines, j)
                            break
            if a_values:
                if not b_found:
                    pre_pct = round(a_values[0], 2)
                else:
                    kind = self._category_kind(b_category)
                    if kind == "promoter" and b_values:
                        pre_pct = round(a_values[0] + b_values[0], 2)
                    elif kind == "other":
                        pre_pct = round(a_values[0], 2)
                    else:
                        # (B) is not labelled, or is a promoter group without a
                        # value: whether it belongs in the promoter total cannot
                        # be established, so the field stays unknown.
                        pre_pct = None

        pre_quote = None
        if pre_pct is None:
            for candidate_page in range(p_start, min(p_end + 1, self.page_count + 1)):
                text = self.extract_page_text(candidate_page)
                flat = " ".join(text.split())
                if not ("Pre-Issue" in text and "Post-Issue" in text
                        and re.search(r"members of the Promoter Group.*?do not hold any shares", flat, re.I)):
                    continue
                match = re.search(r"(?m)^([^\n]*?)\s+([0-9,]{6,})\s+([0-9]+\.[0-9]+)\s+([0-9,]{6,})\s+\[[●•*]\]\s*$", text)
                if match and match.group(2) == match.group(4) and 0 <= float(match.group(3)) <= 100:
                    pre_pct = float(match.group(3))
                    pre_quote = match.group(0).strip()
                    found_page = candidate_page
                    break
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
                    quote=pre_quote or f"Total Promoter & Promoter Group pre-issue shareholding: {pre_pct}%",
                    quote_is_processing=pre_quote is None,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        # Post-issue promoter holding fallback scan.  The category arithmetic
        # is unchanged; the label guard only stops the combined summary row
        # from being read as the promoter total.
        if post_pct is None:
            # A post-issue value is read only from a row that carries a
            # post-issue column: the table must say "Post-Offer"/"Post-Issue"
            # (or "after the Offer"/"on Allotment") and the row must hold a
            # numeric percentage in more than one column.  A row whose other
            # columns are "[●]" discloses a pre-issue figure only, and a
            # pre-issue-only table must not be read as post-issue.
            a_values: List[float] = []
            b_values: List[float] = []
            b_found = False
            b_category: Optional[str] = None
            saw_unusable_row = False
            for idx, l in enumerate(cap_lines):
                if not a_values and self._TOTAL_A_LABEL.search(l):
                    values = self._row_percentages(cap_lines, idx)
                    if len(values) < 2:
                        saw_unusable_row = True
                        continue
                    has_post_context = any(
                        self._POST_ISSUE_CONTEXT.search(x)
                        for x in cap_lines[max(0, idx - 120): idx]
                    )
                    if not has_post_context:
                        saw_unusable_row = True
                        continue
                    a_values = values
                    for j in range(idx + 1, min(idx + 200, len(cap_lines))):
                        if re.search(r'Total\s*\(\s*B\s*\)', cap_lines[j], re.IGNORECASE):
                            b_found = True
                            b_values = self._row_percentages(cap_lines, j)
                            b_category = self._promoter_category_before(cap_lines, j)
                            break
            if a_values:
                if not b_found:
                    post_pct = round(a_values[-1], 2)
                else:
                    kind = self._category_kind(b_category)
                    if kind == "promoter" and len(b_values) >= 2:
                        post_pct = round(a_values[-1] + b_values[-1], 2)
                    elif kind == "other":
                        post_pct = round(a_values[-1], 2)
                    else:
                        # (B) unlabelled or its post value is not disclosed:
                        # the promoter total cannot be established.
                        post_pct = None
            elif saw_unusable_row:
                post_pct = None

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

        # Pre-IPO placements: the share-capital history table states each
        # allotment with its date, its share count and its price per share.
        # An empty list used to be the builder's default, which the frozen
        # bucket rule reads as "no placements are disclosed" and scores 2/2 --
        # points earned by *not reading* the table.  The rows are read here so
        # the bucket is computed from the filing's own history.
        month_numbers = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
            "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
            "november": 11, "december": 12,
        }
        placement_re = re.compile(
            r"(?P<month>january|february|march|april|may|june|july|august|september|"
            r"october|november|december)\s+(?P<day>\d{1,2}),\s+(?P<year>19\d\d|20\d\d)\s*\$?\s*"
            r"(?P<shares>\d[\d,]*)\s+"
            r"(?P<nature>further\s+issue\s+of\s+equity\s+shares|allotment\s+of\s+equity\s+shares)"
            r"[\s\S]{0,80}?\bCash\b\s+(?P<fv>\d[\d,]*(?:\.\d+)?)\s+"
            r"(?P<price>\d[\d,]*(?:\.\d+)?)",
            re.IGNORECASE,
        )
        placements: List[Dict[str, Any]] = []
        placement_page: Optional[int] = None
        placement_quote: Optional[str] = None
        for p in range(p_start, min(p_end + 1, self.page_count + 1)):
            if placements:
                break
            flat = " ".join(self.extract_page_text(p).split())
            if "further issue of equity shares" not in flat.lower():
                continue
            for m in placement_re.finditer(flat):
                month = month_numbers[m.group("month").lower()]
                day = int(m.group("day"))
                year = int(m.group("year"))
                try:
                    date_value = datetime.date(year, month, day).isoformat()
                except ValueError:
                    continue
                shares = parse_indian_number(m.group("shares"))
                price = parse_indian_number(m.group("price"))
                if price is None or price <= 0:
                    continue
                entry: Dict[str, Any] = {"date": date_value, "price": float(price)}
                if shares is not None and shares > 0:
                    entry["shares"] = float(shares)
                placements.append(entry)
                if placement_quote is None:
                    placement_page = p
                    placement_quote = m.group(0)
        if placements:
            extractions.append(
                RawExtraction(
                    field_path="capital_structure.pre_ipo_placements",
                    candidate_value=placements,
                    raw_text=placement_quote or str(placements),
                    page=placement_page or found_page,
                    section="Capital Structure",
                    locator="History of equity share capital (issue rows)",
                    quote=placement_quote or "",
                    quote_is_processing=placement_quote is None,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )

        if pre_pct is None and sentence_pre_pct is not None:
            # "our Promoter holds 73,519,238 Equity Shares, equivalent to
            # 72.80% of the issued, subscribed and paid-up Equity Share
            # capital" -- the pre-Offer holding stated in prose, with the
            # share count that produces it on the same line.
            pre_pct = sentence_pre_pct
            extractions.append(
                RawExtraction(
                    field_path="capital_structure.promoter_pre_pct",
                    candidate_value=pre_pct,
                    raw_text=sentence_pre_quote or str(pre_pct),
                    raw_unit="PERCENT",
                    page=sentence_pre_page or found_page,
                    section="Capital Structure",
                    locator="Promoter shareholding, pre-Offer (prose)",
                    quote=sentence_pre_quote or "",
                    quote_is_processing=sentence_pre_quote is None,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )

        if pledge_pct is not None:
            extractions.append(
                RawExtraction(
                    field_path="capital_structure.promoter_pledge_pct",
                    candidate_value=pledge_pct,
                    raw_text=pledge_quote or str(pledge_pct),
                    raw_unit="PERCENT",
                    page=pledge_page or found_page,
                    section="Capital Structure",
                    locator="Promoter share pledge confirmation",
                    quote=pledge_quote or "",
                    quote_is_processing=pledge_quote is None,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=1.0,
                )
            )

        if lockin is not None:
            extractions.append(
                RawExtraction(
                    field_path="capital_structure.promoter_lockin_in_place",
                    candidate_value=lockin,
                    raw_text=lockin_quote or str(lockin),
                    page=lockin_page or found_page,
                    section="Capital Structure",
                    locator="Promoter lock-in disclosure",
                    quote=lockin_quote or "",
                    quote_is_processing=lockin_quote is None,
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
        line_pages: List[int] = []
        category_traces: Dict[str, Tuple[int, str]] = {}
        for p in range(p_start, scan_end):
            txt = self.extract_page_text(p)
            for line in txt.split("\n"):
                if line.strip():
                    section_lines.append(line.strip())
                    line_pages.append(p)

        def _scan_category_amount(keyword_list: List[str]) -> Tuple[Optional[float], Optional[str]]:
            for i, l in enumerate(section_lines):
                if any(k.lower() in l.lower() for k in keyword_list):
                    for j in range(i, min(i + 4, len(section_lines))):
                        tokens = re.findall(r'\[[^a-zA-Z0-9\s]+\]|\[[●•\*]\]|[0-9,]+(?:\.[0-9]+)?', section_lines[j])
                        for tok in tokens:
                            if is_undisclosed_marker(tok):
                                category_traces[keyword_list[0]] = (line_pages[j], section_lines[j])
                                return None, "[●]"
                            num = parse_indian_number(tok)
                            if num is not None and num > 50.0:
                                category_traces[keyword_list[0]] = (line_pages[j], section_lines[j])
                                return num, None
            return None, None

        # 0. Row-oriented schedule reading (added 2026-10-26).
        #
        # The keyword scan above is phrase-bound: it looks for the *caption*
        # words it was written against ("repayment and/ or pre", "prepayment,
        # in full or in part").  A schedule that says "Prepayment or scheduled
        # re-payment, in full or part, of certain outstanding borrowings" -- an
        # ordinary ICDR wording -- matched none of them, so the debt line was
        # dropped while the GCP line (whose caption *is* in the list) was still
        # read.  The schedule is a numbered table, so each object row can be
        # classified from its own verb and party instead: a repayment of the
        # issuer's own borrowings is `debt_repayment`; the same verb applied to
        # a subsidiary's borrowings is `other` (the issuer receives no asset and
        # retires no own liability); `general corporate purposes` keeps its
        # governed category, and its `[●]` is undisclosed rather than zero.
        # A money cell is either a decimal amount ("3,209.00") or a grouped
        # integer ("275,000").  The integer form matters: a schedule printed
        # one row per line puts the caption and its amount on the same line,
        # and a reader that only recognises decimals carries that row into the
        # next one -- merging a debt row into the GCP row below it.
        _MONEY = re.compile(r"\b\d{1,3}(?:,\d{2,3})+(?:\.\d+)?\b|\b\d+\.\d{2}\b")
        _REPAY = re.compile(r"\b(?:pre-?payment|re-?payment)\b", re.IGNORECASE)
        _BORROW = re.compile(r"\b(?:borrowings?|term\s+loans?)\b", re.IGNORECASE)
        # An *equity investment in* a group company is `other`: the issuer
        # parts with cash and retires none of its own debt (Paras: "Investment
        # in our wholly owned Subsidiary ... for repayment/prepayment of
        # borrowings").  A direct prepayment of group debt from the proceeds is
        # still `debt_repayment` (Jio: "Prepayment ... of certain outstanding
        # borrowings availed by the Material Subsidiary, RJIL") -- the object
        # is the retirement of borrowings, whichever entity they sit in.
        _INVEST_IN_GROUP = re.compile(
            r"\binvest(?:ment)?\s+in\b[^.]{0,90}?"
            r"(?:subsidiar(?:y|ies)|joint\s+venture|associate|group\s+compan)",
            re.IGNORECASE,
        )
        row_categories: List[Tuple[str, Optional[float], int, str, Optional[str]]] = []
        # Table cells are separate text lines in a PDF ("... outstanding
        # borrowings" / "availed by our Company" / "3,209.00"), so a row is
        # assembled before it is classified: a numbered object line and the
        # lines that follow it (until the next numbered line, the "Net
        # Proceeds" total, or a note) form one row.
        blocks: List[Tuple[List[str], int]] = []
        current: List[str] = []
        current_page = p_start
        carry = False
        for i, l in enumerate(section_lines):
            starts_row = bool(re.match(r"^\s*\d+[.)]\s", l))
            stops_block = bool(re.match(r"^\s*(?:Net\s+Proceeds|Note|\*|\(collectively)", l, re.IGNORECASE))
            if starts_row:
                if current:
                    blocks.append((current, current_page))
                current = [l]
                current_page = line_pages[i]
                # A row whose caption and amount share one line is complete
                # as soon as it starts; only a row that runs on is carried.
                if _MONEY.search(l) or re.search(r"\[[^a-zA-Z0-9\s]+\]", l):
                    blocks.append((current, current_page))
                    current = []
                    carry = False
                else:
                    carry = True
                continue
            if stops_block:
                if current:
                    blocks.append((current, current_page))
                current = []
                carry = False
                continue
            if carry:
                current.append(l)
                # A row ends at its amount or its undisclosed marker; text
                # after that belongs to the next prose block, not to the row.
                if _MONEY.search(l) or re.search(r"\[[^a-zA-Z0-9\s]+\]", l):
                    blocks.append((current, current_page))
                    current = []
                    carry = False
        if current:
            blocks.append((current, current_page))

        for block, block_page in blocks:
            text = " ".join(" ".join(block).split())
            if not re.match(r"^\s*\d+[.)]\s", block[0]):
                continue
            body = re.sub(r"^\s*\d+[.)]\s*", "", text).strip()
            if len(body) < 12:
                continue
            lowered = body.lower()
            if "general corporate purposes" in lowered:
                category = "gcp"
            elif _REPAY.search(body) and _BORROW.search(body):
                category = "other" if _INVEST_IN_GROUP.search(body) else "debt_repayment"
            else:
                continue
            amounts = _MONEY.findall(body)
            amount = parse_indian_number(amounts[-1]) if amounts else None
            marker: Optional[str] = None
            if amount is None:
                markers = re.findall(r"\[[^a-zA-Z0-9\s]+\]", body)
                if not markers:
                    continue
                marker = markers[-1]
            row_categories.append((category, amount, block_page, body, marker))
        if row_categories:
            # A row-oriented read supersedes the keyword scan: it sees every
            # object row, including the ones whose caption wording differs.
            use_of_proceeds.clear()
            for category, amount, page, raw, marker in row_categories:
                if any(u["category"] == category for u in use_of_proceeds):
                    # The first stated row for a category wins.  The same
                    # objects schedule is often printed twice (requirement of
                    # funds, then the deployment schedule), and summing the two
                    # presentations double-counts the allocation.
                    continue
                item: Dict[str, Any] = {"category": category, "amount": amount}
                if marker:
                    item["undisclosed_marker"] = marker
                use_of_proceeds.append(item)
                category_traces[category] = (page, raw)

        # 1. Working capital
        if not row_categories:
            wc_amt, wc_marker = _scan_category_amount(["working capital requirements", "funding working capital"])
            if wc_amt is not None or wc_marker is not None:
                item: Dict[str, Any] = {"category": "working_capital", "amount": wc_amt}
                if wc_marker:
                    item["undisclosed_marker"] = wc_marker
                use_of_proceeds.append(item)

        # 2. Debt repayment
        if not row_categories:
            debt_amt, debt_marker = _scan_category_amount(["repayment and/ or pre", "repayment of term loans", "debt repayment", "prepayment, in full or in part"])
            if debt_amt is not None or debt_marker is not None:
                item = {"category": "debt_repayment", "amount": debt_amt}
                if debt_marker:
                    item["undisclosed_marker"] = debt_marker
                use_of_proceeds.append(item)

        # 3. Growth Capex / Capital Augmentation
        if not row_categories:
            capex_amt, capex_marker = _scan_category_amount(["capital expenditure", "purchase of plant", "growth capex", "augmentation of"])
            if capex_amt is not None or capex_marker is not None:
                item = {"category": "growth_capex", "amount": capex_amt}
                if capex_marker:
                    item["undisclosed_marker"] = capex_marker
                use_of_proceeds.append(item)

        # 4. General corporate purposes (GCP)
        if not row_categories:
            gcp_amt, gcp_marker = _scan_category_amount(["general corporate purposes"])
            if gcp_amt is not None or gcp_marker is not None:
                item = {"category": "gcp", "amount": gcp_amt}
                if gcp_marker:
                    item["undisclosed_marker"] = gcp_marker
                use_of_proceeds.append(item)

        if use_of_proceeds:
            found_page = min((x[0] for x in category_traces.values()), default=p_start)
            # The quotation is the schedule's own row text, not a sentence of
            # the engine's making: a field whose evidence is a processing note
            # ("Use of proceeds categories: [...]") is not drawn from the
            # filing at all, and the reader of the evidence cannot check it.
            schedule_quote = ""
            for category in (u["category"] for u in use_of_proceeds):
                trace = category_traces.get(category)
                if trace and trace[1]:
                    schedule_quote = trace[1]
                    found_page = trace[0]
                    break
            extractions.append(
                RawExtraction(
                    field_path="use_of_proceeds",
                    candidate_value=use_of_proceeds,
                    raw_text=str(use_of_proceeds),
                    page=found_page,
                    section="Objects of the Offer",
                    locator="Schedule of Implementation and Deployment",
                    quote=schedule_quote,
                    quote_is_processing=not schedule_quote,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        keys = {"working_capital": "working capital requirements", "debt_repayment": "repayment and/ or pre", "growth_capex": "capital expenditure", "gcp": "general corporate purposes"}
        for index, item in enumerate(use_of_proceeds):
            # Row-oriented readings are keyed by the governed category itself;
            # the keyword scan keys by the caption phrase it matched.
            trace = category_traces.get(item["category"]) or category_traces.get(keys.get(item["category"], ""))
            if trace:
                page, quote = trace
                extractions.append(RawExtraction(
                    field_path=f"use_of_proceeds[{index}].amount",
                    candidate_value=item["amount"], raw_text=quote, page=page,
                    section="Objects of the Offer", locator=f"{item['category']} allocation row",
                    quote=quote, extraction_confidence=0.98,
                ))
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

    # ------------------------------------------------------------------
    # Outstanding litigation and SEBI/ED regulatory action -- defect class D-5
    # ------------------------------------------------------------------
    #
    # ``extract_governance`` used to initialise ``lit_bucket = "clean"`` and
    # ``sebi_active = False`` *before* the litigation scan and then append both
    # fields unconditionally afterwards, whatever the scan found -- including
    # when every page in the range was empty.  Three separate integrity
    # problems followed from that:
    #
    #   1. the absence of an extracted proceeding was treated as proof that no
    #      proceeding exists, and ``clean`` is the favourable end of a scored
    #      criterion (Module D ``litigation``, 4/4 points);
    #   2. ``sebi_ed_action_active = False`` was emitted with the quotation
    #      "No active SEBI or ED regulatory proceedings" -- text that appears
    #      nowhere in any filing and was *not* marked ``quote_is_processing``,
    #      so the evidence record presented a synthesised sentence as a source
    #      quotation (the same defect D-4 removed from the auditor fields);
    #   3. the classification regexes saw three phrases only, so the statutory
    #      *summary-table* form of this disclosure -- one row per party group
    #      and direction, one column per proceeding type, counts in the cells -
    #      could not be read at all, and neither could the labelled
    #      "Criminal proceedings against the Company / Nil" list form.
    #
    # The contract already provides the state this needs; nothing governed is
    # changed.  ``schema/ipo-input.v1.5.schema.json`` allows
    # ``governance.litigation_bucket: null`` and
    # ``governance.sebi_ed_action_active: null``; ``derived._litigation_bucket``
    # returns UNKNOWN for null; the ``litigation`` criterion scores UNKNOWN
    # rather than zero; K2 lists ``sebi_ed_action_active`` among its required
    # inputs; and ``config.critical_data`` makes its absence yield
    # INSUFFICIENT_DATA.  The extractor simply stops asserting what the filing
    # does not state.  The three buckets, their points and the adverse-marker
    # vocabulary are exactly as governed -- only the *default* is removed.
    #
    # Polarity matters in both directions, as in D-1 and D-2: "there are no
    # outstanding criminal proceedings or material civil litigation" is a
    # statement of *absence*, not a finding of material civil litigation, and
    # the previous code classified precisely that sentence as ``minor_civil``.
    #
    # Deliberately NOT decided here (each needs a governed standard, see
    # docs/investigation/D-5-LITIGATION-REGULATORY-EVIDENCE-DEFAULTS-2026-10-20.md):
    #   * a party-coverage standard for ``clean`` -- whether an absence
    #     statement naming "the Company and its Promoters" also clears the
    #     Directors.  The statement is accepted and the parties it names are
    #     recorded in the evidence note, so the gap is visible in the record
    #     rather than silently closed;
    #   * a source-coverage standard under which a SEBI-only negative could
    #     clear a flag whose governed name covers SEBI **and** the Enforcement
    #     Directorate.  Until one is defined, only a negative naming both
    #     regulators yields False; anything else stays UNKNOWN.
    # An *affirmative* regulatory finding is always allowed through (a non-nil
    # SEBI/ED cell in an adverse row, or a sentence with the agency, a finite
    # act and a party): asserting an action the filing discloses is recoverable,
    # clearing K2 without evidence is not.  A `Nil` cell never yields True, and
    # a `Nil` cell scoped to the Promoters never clears the flag either.

    #: Parties whose litigation the bucket covers.  The criterion formula says
    #: "across promoters, directors and the company", so a proceeding against
    #: *any* of them is in scope; the issuer's own name is not required.
    _LIT_PARTY = re.compile(
        r"\b(?:our\s+|the\s+)?(?:company|body\s+corporate|subsidiar(?:y|ies)|directors?"
        r"(?:\s*\(excluding\s+promoters\))?|promoters?|key\s+managerial\s+personnel|kmp"
        r"|senior\s+management|group\s+companies?)\b",
        re.IGNORECASE,
    )

    #: Negation immediately before the phrase, within the same sentence
    #: (the D-1 ``_GOING_CONCERN_NEGATION`` technique).
    _LIT_NEGATION = re.compile(r"\b(?:no|not|none|nil|without|nothing)\b", re.IGNORECASE)

    #: Abbreviations after which a period does **not** end a sentence.  Used
    #: only when narrowing a line span to one sentence (A29 P1); treating
    #: ``Limited.`` as a sentence end is correct, treating ``Rs.`` or ``Mr.`` as
    #: one is not.
    _LIT_SENTENCE_ABBREV = frozenset(
        {
            "mr", "mrs", "ms", "dr", "shri", "smt", "rs", "no", "nos", "co",
            "pvt", "inc", "corp", "ltd", "viz", "approx", "cf", "vs", "st",
            "jr", "sr", "u/s", "w.e.f", "i.e", "e.g",
        }
    )

    #: The party groups A24 admits -- the same population ``_LIT_PARTY``
    #: recognises, read as *named groups* so that a filing heading can be
    #: classified only when it identifies exactly one of them.
    _LIT_PARTY_GROUPS: Tuple[Tuple[str, str], ...] = (
        ("Company", r"\bour\s+company\b|\bthe\s+company\b|\bcompany\b"),
        ("Promoters", r"\bpromoters?\b"),
        ("Directors", r"\bdirectors?\b"),
        ("Subsidiaries", r"\bsubsidiar(?:y|ies)\b"),
        ("KMP", r"\bkey\s+managerial\s+personnel\b|\bKMP\b"),
        ("Senior management", r"\bsenior\s+management\b"),
    )

    #: A29 P3 kill switch.  Heading attribution is the one correction in this
    #: pass that can *add* a party to a finding, so it is isolated behind a
    #: single flag: setting this to ``False`` restores the pre-A29 party test
    #: exactly (a sentence that names no party emits nothing, and K2 returns to
    #: UNKNOWN), with no other behaviour affected.  The P3 tests in
    #: ``tests/test_litigation_regulatory_defaults.py`` are the cases to
    #: re-baseline if it is ever turned off.
    _LIT_HEADING_PARTY_ATTRIBUTION = True

    #: A *section-level* heading inside the litigation section, of the form the
    #: ICDR Schedule-VI layout prints: ``IV. Outstanding litigation involving
    #: RIL, the Promoter``.  Only these carry party scope across a page break;
    #: a lettered sub-heading (``c) Actions by statutory/ regulatory
    #: authorities against ...``) scopes one item and is not used (A29 P3).
    _LIT_SECTION_HEADING = re.compile(
        r"^[ \t]*(?:SECTION[ \t]+)?(?P<num>[IVX]{1,6})[.)][ \t]+(?P<title>[A-Z][^.\n]{2,160})$",
        re.MULTILINE,
    )

    #: Adverse-proceeding vocabulary for the prose route, deliberately
    #: *unchanged* from the baseline so that no filing is newly condemned by
    #: this pass; only the favourable default is removed.  The table and
    #: labelled-list routes below read only the filing's own disclosure forms.
    _LIT_CRIMINAL_PHRASE = re.compile(
        r"criminal\s+proceedings\s+against\s+our\s+promoters|\br\.c\.c\.|criminal\s+complaint",
        re.IGNORECASE,
    )
    _LIT_CIVIL_PHRASE = re.compile(
        r"material\s+civil\s+litigation|\bcivil\s+suits?\b",
        re.IGNORECASE,
    )

    #: Explicit statement that proceedings of the stated kind do not exist.
    #: ``no | none | nil`` may be separated from the noun only by adjectives --
    #: a finite verb in between means the sentence is not an absence statement
    #: ("No doubt, there are criminal proceedings ..." must stay adverse).
    _LIT_ABSENCE = re.compile(
        r"\b(?:no|none|nil)\b(?P<gap>[^.\n]{0,120}?)"
        r"\b(?:(?:outstanding|pending|active|ongoing|material|such)\s+)*"
        r"(?:criminal\s+(?:proceedings?|case[s]?|complaint[s]?|action[s]?)"
        r"|civil\s+litigation|litigation|legal\s+proceedings?|regulatory\s+proceedings?"
        r"|disciplinary\s+(?:actions?|proceedings?)|proceedings?)\b",
        re.IGNORECASE,
    )
    _LIT_ABSENCE_GAP_VERB = re.compile(
        r"\b(?:is|are|was|were|has|have|had|does|do|did|shall|will|may|can|could)\b",
        re.IGNORECASE,
    )
    #: Proceeding types that *qualify* a denial, narrowing what it denies.
    #: ``material | outstanding | pending | ongoing | such | any | other |
    #: relevant | legal`` are neutral and leave a denial comprehensive.
    _LIT_QUALIFIED_TYPES = (
        r"criminal|civil|regulatory|statutory|tax|disciplinary|money[- ]laundering"
    )
    #: Which dimension a denial actually reaches.  ``clean`` is the favourable
    #: end of a criterion whose other two values are criminal/regulatory matters
    #: and material civil litigation, so a nil that denies only one of them is
    #: not evidence for the other -- exactly the situation D-5 says must stay
    #: UNKNOWN instead of being resolved favourably.
    _LIT_DENIES_CRIMINAL = re.compile(
        r"\b(?:criminal|regulatory|statutory|disciplinary|money[- ]laundering)\b",
        re.IGNORECASE,
    )
    _LIT_DENIES_CIVIL = re.compile(r"\bcivil\b|\bdisputes?\b", re.IGNORECASE)
    _LIT_LITIGATION_NOUN = re.compile(r"\blitigation\b", re.IGNORECASE)

    #: A24-D1 (approved 2026-10-20): the party population the bucket is defined
    #: over -- the Company, its Promoters and its Directors, exactly as the
    #: governed metric formula states it ("across promoters, directors and the
    #: company", ``derived.py:1384``; likewise the upstream reference config's
    #: bucket note at ``handoff/reference/ipo-config.json:294``).  KMP and
    #: Senior Management are deliberately *not* required: widening the
    #: population is a separate governed decision, not an extraction choice.
    _LIT_POP_ISSUER = re.compile(
        r"\b(?:our|the)\s+company\b|\bthe\s+issuer\b|\bour\s+body\s+corporate\b",
        re.IGNORECASE,
    )
    _LIT_POP_PROMOTERS = re.compile(r"\bpromoters?\b|\bpromoter\s+group\b", re.IGNORECASE)
    _LIT_POP_DIRECTORS = re.compile(r"\bdirectors?\b", re.IGNORECASE)
    #: A mention of *other* corporate bodies is not coverage of the issuer:
    #: "our Promoters, Directors, or Group Companies" names the group, so
    #: stripping these first is what keeps A24 R3 honest.
    _LIT_POP_OTHER_BODIES = re.compile(
        r"\bgroup\s+compan(?:y|ies)\b|\bother\s+compan(?:y|ies)\b|\bsubsi(?:diar(?:y|ies)|diar)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _lit_absence_covers_population(cls, sentence: str) -> bool:
        """Does this denial assert absence for all three parties of the bucket?

        ``clean`` is a statement about the Company, its Promoters and its
        Directors, so a denial reaching fewer of them leaves part of the
        population undisclosed -- UNKNOWN, not the favourable end.  Adverse
        findings keep their wider scope: any party in ``_LIT_PARTY`` still
        condemns, because a finding needs no population coverage to be true.
        """
        without_others = cls._LIT_POP_OTHER_BODIES.sub(" ", sentence)
        return bool(
            cls._LIT_POP_ISSUER.search(without_others)
            and cls._LIT_POP_PROMOTERS.search(sentence)
            and cls._LIT_POP_DIRECTORS.search(sentence)
        )

    @classmethod
    def _lit_absence_is_comprehensive(cls, sentence: str) -> bool:
        """May this absence statement support ``clean``?

        Yes when the statement is unqualified ("no litigation is pending",
        "not involved in any material litigation or criminal cases"), or when it
        reaches both dimensions of the bucket.  No when it denies only criminal
        / regulatory matters, only civil litigation, or only a type the bucket
        does not score at all (tax) -- then the other dimension is simply
        undisclosed, which is UNKNOWN, not ``clean``.
        """
        for noun in cls._LIT_LITIGATION_NOUN.finditer(sentence):
            before = sentence[max(0, noun.start() - 30): noun.start()]
            if re.search(
                rf"\b(?:{cls._LIT_QUALIFIED_TYPES})\b(?:\s+\w+){{0,3}}\s*$", before
            ):
                continue  # "criminal litigation", "tax litigation": a qualified mention
            return True  # an unqualified "litigation" covers every dimension
        criminal = bool(cls._LIT_DENIES_CRIMINAL.search(sentence))
        civil = bool(cls._LIT_DENIES_CIVIL.search(sentence))
        # A denial of a type the bucket does not score at all (tax exposure, an
        # assessment) leaves *both* scored dimensions undisclosed, so it cannot
        # resolve the bucket either way.
        other = bool(re.search(r"\btax\b|\bassessment\b|\bduty\b|\bduties\b", sentence, re.IGNORECASE))
        if criminal or civil or other:
            return criminal and civil
        # No type word at all: "no proceedings / no cases are pending" is a
        # blanket statement about the party, so it carries the whole bucket.
        return True

    #: "None of our Promoters, Directors or Group Companies are involved in any
    #: material litigation" -- subject-first absence, common SME wording.
    _LIT_ABSENCE_NONE_OF = re.compile(
        r"\bnone\s+of\b[^.\n]{0,200}?\b(?:is|are|was|were)\s+(?:now\s+|ever\s+)?"
        r"(?:involved|a\s+party|parties|subject|named)\b[^.\n]{0,80}?\bin\s+any\b",
        re.IGNORECASE,
    )

    #: Regulator identity.  ``ED`` is matched case-sensitively: a
    #: case-insensitive two-letter token would fire on ordinary prose.
    _REG_AGENCY = re.compile(
        r"\bSEBI\b|\bSecurities\s+and\s+Exchange\s+Board\s+of\s+India\b"
        r"|\bEnforcement\s+Directorate\b|\bPMLA\b|\bPrevention\s+of\s+Money\s+Laundering\s+Act\b",
        re.IGNORECASE,
    )
    #: The two regulators the governed flag is named after, tested separately:
    #: ``sebi_ed_action_active`` may only be *cleared* by a statement that
    #: covers both of them, and only by one that covers each of them at all.
    #: ``_REG_AGENCY`` stays the "is a regulator named here" test.
    _REG_AGENCY_SEBI = re.compile(
        r"\bSEBI\b|\bSecurities\s+and\s+Exchange\s+Board(?:\s+of\s+India)?\b",
        re.IGNORECASE,
    )
    _REG_AGENCY_ED = re.compile(
        r"\bED\b|\bEnforcement\s+Directorate\b|\bPMLA\b"
        r"|\bPrevention\s+of\s+Money\s+Laundering\s+Act\b",
        re.IGNORECASE,
    )
    #: The finite act inside a sentence.  A negation *before* the act negates
    #: the act ("SEBI has **not** imposed ...", "**no** penalty has been
    #: imposed by SEBI"); a negation after it does not ("SEBI has imposed a
    #: penalty, not a fine").
    _REG_ACT_VERB = re.compile(
        r"\b(?:initiated|issued|passed|imposed|conducted|attached|registered|taken|served|filed|raised"
        r"|recorded|framed|pending|preferred|moved|referred)\b",
        re.IGNORECASE,
    )
    #: An action of a regulator, in either word order, within one sentence.
    _REG_ACTION = re.compile(
        # The regulator must be shown *acting*: "proceedings ... initiated by
        # SEBI".  A bare preposition ("actions by SEBI involving our Company")
        # is a section heading, not a finding; headings are masked before this
        # scan runs and the finite act is the second guard.
        r"\b(?:proceedings?|action|actions|order|orders|notice|notices|summons|search\s+and\s+seizure"
        r"|show\s+cause|attachment|penalt(?:y|ies)|disciplinary\s+action)\b[^.\n]{0,90}?"
        r"\b(?:initiated|issued|passed|imposed|conducted|attached|registered|taken|served|filed|raised"
        r"|recorded|framed)\b"
        r"|\b(?:initiated|issued|passed|imposed|conducted|attached|registered|taken)\b[^.\n]{0,70}?"
        r"\b(?:against|upon|on)\b[^.\n]{0,60}?(?:SEBI|Enforcement Directorate|\bED\b|PMLA)"
        # ... or in the natural order, regulator first.  The action noun is
        # required so that a bare "SEBI has approved the offer document" is not
        # an action against anybody.  A29 (K2-A) adds the procedural verbs a
        # regulator uses when it *appeals* an order -- ``filed``, ``preferred``,
        # ``moved``, ``referred`` -- and the appeal/petition nouns that name the
        # thing filed.  The action noun is still required, so a filing
        # reference whose object is not an action of the regulator cannot be
        # turned into a finding by the verb alone.
        r"|\b(?:SEBI|Securities and Exchange Board of India|Enforcement Directorate|\bED\b|PMLA)\b"
        r"[^.\n]{0,60}?\b(?:has|have|had|is|was|were)?\s*(?:initiated|issued|passed|imposed|conducted"
        r"|attached|registered|served|filed|preferred|moved|referred)\b[^.\n]{0,60}?"
        r"\b(?:proceedings?|notice|order|orders|summons|show\s+cause|penalt|attachment|charge\s?sheet"
        r"|revision\s+application|appeal|petition|complaint)"
        # ... or a matter stated as pending before the regulator.
        r"|\b(?:proceedings?|case[s]?|appeal|matter|enquiry|investigation)\b[^.\n]{0,50}?"
        r"\bpending\s+before\b[^.\n]{0,50}?(?:SEBI|Enforcement Directorate|\bED\b|PMLA)",
        re.IGNORECASE,
    )
    #: A denial whose scope is a *closed* period says nothing about whether an
    #: action is active now, which is what ``sebi_ed_action_active`` asks.  A
    #: rolling window ("in the last five years") and an as-of-the-prospectus
    #: statement both reach the present and are accepted; "during the financial
    #: year 2023-24" or "as on 31 March 2022" does not.
    _REG_ABSENT_CLOSED = re.compile(
        r"\b(?:during|in|for|within|as\s+(?:on|at)|upto|up\s+to|till|through)\s+"
        r"(?:the\s+)?(?:financial\s+year|f\.?y\.?\s*\d|year\s+ended|year\s*\d{4}"
        r"|quarter|half[-\s]year|period\s+(?:ended|from|to)|six\s+months\s+ended)\b"
        r"|\bas\s+(?:on|at)\s+\d{1,2}[/ -][A-Za-z0-9]{3,9}[/ -]\d{2,4}"
        r"|\bas\s+(?:on|at)\s+\d{4}\b",
        re.IGNORECASE,
    )

    #: Boilerplate that names SEBI without describing any action (the cover
    #: page, "not been recommended or approved by SEBI").  A29 (P4) separates
    #: the *citation* forms out of this veto: a bare regulation cite is never an
    #: action by itself, but a sentence that reports a specific adjudicative
    #: event and happens to cite the regulation it was decided under is a
    #: genuine action statement and must not be discarded for the citation.
    _REG_BOILERPLATE = re.compile(
        r"\bICDR\b|\bnot\s+been\s+recommended\b|\bguarantee\s+the\s+accuracy\b"
        r"|\bregistration\s+no\b|\bSEBI\s+(?:ICDR|LODR|PFRR|DAP|Listing)\b"
        r"|\blimitation\s+act\b",
        re.IGNORECASE,
    )
    #: A bare regulation citation ("... Regulations, 2003", "Regulation 3(a)").
    #: Vetoed only when the sentence reports no adjudicative event, so that the
    #: citation cannot be the whole case for a finding and cannot veto one
    #: either.
    _REG_BOILERPLATE_CITE = re.compile(
        r"\bregulations,?\s*20\d\d\b|\bregulation\s+\d", re.IGNORECASE
    )
    #: A dated or forked adjudicative event: the marker that a sentence is
    #: reporting what a forum actually did, rather than restating the law.
    _REG_ADJUDICATIVE_EVENT = re.compile(
        r"\b(?:order|notice|complaint|summons|direction|circular)\s+dated\b"
        r"|\bdated\s+\d{1,2}\s+(?:January|February|March|April|May|June|July|August"
        r"|September|October|November|December)\b"
        r"|\b(?:High\s+Court|Supreme\s+Court|Special\s+Court|Securities\s+Appellate"
        r"|Tribunal|SAT|Adjudicating\s+Officer|Whole\s*time\s+Member|Division\s+Bench"
        r"|Single\s+Judge)\b",
        re.IGNORECASE,
    )
    #: Meta-discourse about the disclosure itself ("this section also provides
    #: the details of all disciplinary actions ... including outstanding
    #: actions").  Narrowing a span to a sentence (A29 P1) makes statements
    #: *about* the section quotable for the first time, and such a sentence
    #: describes the document, not an event: the action nouns it contains are
    #: the object of "provides the details of".
    _REG_META_DISCOURSE = re.compile(
        r"\bthis\s+section\b|\bdetails\s+of\s+(?:all\s+|the\s+)?(?:disciplinary|actions?"
        r"|proceedings?|penalt|litigation)"
        r"|\b(?:are|is)\s+(?:set\s+out|disclosed|described|provided)\s+(?:below|above)\b"
        r"|\bdisclosed\s+(?:below|above)\b|\bset\s+out\s+below\b",
        re.IGNORECASE,
    )
    #: Where the action stands, as the quotation itself states it.  A29 (K2-A)
    #: makes the distinction explicit in the evidence note rather than letting a
    #: reader infer "active" from a past-tense verb: a proceeding pending at the
    #: cutoff qualifies, and a concluded one is reported as concluded.
    _REG_STATUS_PENDING = re.compile(
        r"\b(?:is|are|was|were|has\s+been|have\s+been|remains?)\s+(?:currently\s+|still\s+)?pending\b"
        r"|\bcurrently\s+pending\b|\bpending\s+before\b|\bsub\s*judice\b|\bawaiting\s+(?:the\s+)?(?:final\s+)?"
        r"(?:order|judgment|decision|adjudication)\b",
        re.IGNORECASE,
    )
    _REG_STATUS_CONCLUDED = re.compile(
        r"\b(?:disposed|dismissed|set\s+aside|quashed|upheld|allowed|rejected|withdrawn"
        r"|concurred|no\s+penalty|without\s+(?:the\s+)?levy|absolved|acquitted)\b",
        re.IGNORECASE,
    )

    #: Labelled list form used inside the litigation section: a category label
    #: on one line, its value alone on the next --
    #: "a) Criminal proceedings against the Company" / "Nil".
    #: This is the ICDR Schedule-VI layout real RHPs print (Jio p. 464, Vishal
    #: Nirmiti pp. 439-441), and the label often names the regulator itself
    #: ("Disciplinary actions by SEBI and / or the Stock Exchanges involving
    #: our Company"), which is why the label is read as a *label* here and
    #: never as an adverse finding by the prose scan.
    _LIT_LABELLED = re.compile(
        r"^(?P<label>(?:\(?[a-z0-9]{1,4}[).]\s*)?[^\n]{0,150}?"
        r"(?:criminal\s+proceedings?|material\s+civil\s+litigation|civil\s+litigation"
        r"|disciplinary\s+actions?|actions?\s+by\s+statutory[^.\n]{0,60}?regulatory\s+authorities"
        r"|regulatory\s+proceedings?|tax\s+proceedings?)"
        r"[^\n]{0,90})[ \t]*\n+[ \t]*(?P<value>Nil|N/A|NA|Not\s+applicable|[-\u2013\u2014]"
        r"|\[\u25cf\]|(?P<count>\d[\d,]*(?:\.\d+)?))[ \t]*$",
        re.IGNORECASE | re.MULTILINE,
    )
    #: Adverse versus self-initiated, read out of the label itself.
    _LIT_LABEL_ADVERSE = re.compile(
        r"\b(?:against|involving|pending)\b", re.IGNORECASE
    )
    _LIT_LABEL_SELF = re.compile(
        r"\b(?:by|from)\s+(?:our|the)\s+(?:company|promoters?|directors?|subsidiaries|kmp"
        r"|senior\s+management)\b",
        re.IGNORECASE,
    )
    #: A bare category heading: a short line naming proceeding types with no
    #: value of its own.  Masked from the prose and SEBI scans, because the
    #: words "criminal proceedings" or "disciplinary actions by SEBI" inside a
    #: heading disclose nothing -- the finding lives in the text under it.
    _LIT_HEADING = re.compile(
        r"^[ \t]*(?:\(?[a-z0-9]{1,4}[).][ \t]*)?(?:the[ \t]+)?(?:criminal[ \t]+proceedings?"
        r"|material[ \t]+civil[ \t]+litigation|civil[ \t]+litigation|disciplinary[ \t]+actions?"
        r"|actions?[ \t]+by[ \t]+statutory[^.\n]{0,60}?regulatory[ \t]+authorities"
        r"|outstanding[ \t]+litigation[^.\n]{0,60}|regulatory[ \t]+proceedings?"
        r"|tax[ \t]+proceedings?)[^.\n]{0,90}$",
        re.IGNORECASE | re.MULTILINE,
    )

    #: Summary-table form (SEBI ICDR Schedule VI / Materiality Policy): one
    #: header row naming the proceeding types, one row per party group and
    #: direction.  Columns are mapped by label, never by assumed position.
    _LIT_TABLE_HEAD = re.compile(r"category\s+of\s+individuals\s*/\s*entities", re.IGNORECASE)
    _LIT_TABLE_COLUMNS = (
        ("criminal", re.compile(r"criminal\s+proceedings?", re.IGNORECASE)),
        ("tax", re.compile(r"tax\s+proceedings?", re.IGNORECASE)),
        ("regulatory", re.compile(r"statutory\s+or\s+regulatory\s+proceedings?", re.IGNORECASE)),
        ("sebi", re.compile(r"disciplinary\s+actions?\s+by\s+sebi", re.IGNORECASE)),
        ("civil", re.compile(r"material\s+civil\s+litigation", re.IGNORECASE)),
        ("amount", re.compile(r"aggregate\s+amount\s+involved", re.IGNORECASE)),
    )
    _LIT_TABLE_ROW = re.compile(
        r"^\s*\|?\s*(?P<side>against|by)\s+our\s+(?P<party>company|subsidiary|directors?[^|\n]{0,40}?"
        r"|promoters?|kmp|key\s+managerial\s+personnel|senior\s+management)\b(?P<rest>.*)$",
        re.IGNORECASE | re.MULTILINE,
    )
    _LIT_TABLE_ROW_LINE = re.compile(r"^\s*\|?\s*(?:against|by)\s+our\s+", re.IGNORECASE)
    _LIT_CELL_NIL = re.compile(r"^(?:nil|na|n/a|not\s+applicable|[-\u2013\u2014]|\[\u25cf\])$", re.IGNORECASE)
    _LIT_CELL_COUNT = re.compile(r"^\d[\d,]*(?:\.\d+)?%?$")

    @staticmethod
    def _lit_is_separator(line: str) -> bool:
        """A table rule line such as ``| --- | --- |``: structure, not text."""
        stripped = line.strip()
        return bool(stripped) and set(stripped) <= set("|-+\u2013\u2014 :.")

    @classmethod
    def _lit_prose_pages(
        cls, lit_pages: Sequence[Tuple[int, str]]
    ) -> List[Tuple[int, str]]:
        """Litigation pages with any summary-table block blanked out.

        Blanking preserves character offsets, so a quote taken from the masked
        text is still a verbatim slice of the page.  The table is read by the
        structured route instead; the prose routes keep the surrounding
        narrative, which is where "except as stated below" style disclosures
        live.
        """
        out: List[Tuple[int, str]] = []
        for page, text in lit_pages:
            if not text:
                out.append((page, text))
                continue
            lines = text.split("\n")
            masked: List[str] = []
            in_table = False
            for line in lines:
                if cls._LIT_TABLE_HEAD.search(line) or (in_table and cls._lit_is_separator(line)):
                    in_table = True
                    masked.append(" " * len(line))
                    continue
                if in_table:
                    # Blank rules, pipe rows and party rows all belong to the
                    # table block; the first other line ends it.
                    if (
                        not line.strip()
                        or "|" in line
                        or cls._lit_is_separator(line)
                        or bool(cls._LIT_TABLE_ROW_LINE.match(line))
                    ):
                        masked.append(" " * len(line))
                        continue
                    in_table = False
                elif cls._lit_is_separator(line):
                    masked.append(" " * len(line))
                    continue
                masked.append(line)
            joined = "\n".join(masked)
            # A labelled list item ("a) Criminal proceedings against the
            # Company" + "Nil" on the next line) is structured evidence read by
            # the structured route.  Its label line names a proceeding type
            # without disclosing any proceeding, so mask exactly the lines the
            # item occupies -- otherwise the label of a *nil* row is scanned as
            # an adverse finding.  Only those lines are masked, so narrative
            # prose on the same page stays visible.
            for match in cls._LIT_LABELLED.finditer(joined):
                if match.group("count") is not None:
                    continue  # a disclosed count is narrative evidence, not a label
                lo = joined.rfind("\n", 0, match.start()) + 1
                hi = joined.find("\n", match.end())
                hi = len(joined) if hi == -1 else hi
                joined = joined[:lo] + " " * (hi - lo) + joined[hi:]
            for match in cls._LIT_HEADING.finditer(joined):
                joined = joined[: match.start()] + " " * (match.end() - match.start()) + joined[match.end():]
            # A numbered section heading ("IV. Outstanding litigation involving
            # RIL, the Promoter") is scope, not disclosure: masking it keeps the
            # heading out of every quotation and stops a line span from joining
            # it to the sentence below it.  Its party scope is read from the
            # original text by ``_lit_section_party_map`` (A29 P3).
            for match in cls._LIT_SECTION_HEADING.finditer(joined):
                joined = joined[: match.start()] + " " * (match.end() - match.start()) + joined[match.end():]
            out.append((page, joined))
        return out


    @staticmethod
    def _lit_cells(line: str) -> List[str]:
        """Split a table line into cells: pipe-delimited, else whitespace."""
        if "|" in line:
            return [cell.strip() for cell in line.split("|") if cell.strip()]
        return line.split()

    #: A party label may carry a qualifier of its own -- real ICDR summary
    #: tables write ``Against our Directors (excluding Promoters)``.  The row
    #: pattern ends the party name at the first pipe, so the qualifier is left
    #: at the start of the row body and would otherwise become a spurious first
    #: cell: every value shifts one column, and a row that a person reads
    #: instantly is counted as unreadable (A24-D3, approved 2026-10-20).  Only a
    #: bracketed run immediately followed by a cell boundary is removed, and
    #: only in the row body -- never in the quotation, which is taken from the
    #: unmodified line, so provenance and the Directors/Promoters distinction
    #: survive.  A row that is still ambiguous after this stays unparseable,
    #: which blocks a favourable conclusion instead of inventing one.
    _LIT_PARTY_QUALIFIER = re.compile(r"^\s*\([^|()]*\)\s*(?=\||$)")

    @classmethod
    def _lit_row_cells(cls, rest: str) -> List[str]:
        """Cells of a table row body, with a party-label qualifier removed."""
        return cls._lit_cells(cls._LIT_PARTY_QUALIFIER.sub("", rest, count=1))

    @staticmethod
    def _lit_party_class(label: str) -> Optional[str]:
        """Which party of the criterion's population an ICDR table row speaks for.

        Ordered deliberately: ``Directors (excluding Promoters)`` is a Directors
        row, not a Promoters row, and the qualifier is never read as coverage of
        the excluded group.
        """
        low = (label or "").lower()
        if "director" in low:
            return "directors"
        if "promoter" in low:
            return "promoters"
        if "company" in low or "body corporate" in low:
            return "company"
        return None

    @classmethod
    def _lit_prefix(cls, text: str, start: int) -> str:
        """Same-sentence prefix before a phrase (D-1's polarity technique)."""
        prefix = text[max(0, start - 160): start]
        cut = max(prefix.rfind("."), prefix.rfind("\n"), prefix.rfind(";"), prefix.rfind(":"))
        return prefix[cut + 1:]

    @staticmethod
    def _lit_span(masked: str, start: int, end: int) -> Tuple[int, int]:
        """Whole-line sentence span around a match.

        PDF text is line-structured, so a sentence is assembled from lines:
        backwards while the previous line is not a sentence end, forwards while
        the current line is not terminated, and never across a blank line.  The
        span is computed on the masked text and applied to the original, which
        keeps every emitted quotation a verbatim contiguous slice of the page.
        """
        lines = masked.split("\n")
        offsets: List[int] = []
        pos = 0
        for line in lines:
            offsets.append(pos)
            pos += len(line) + 1
        idx = len(lines) - 1
        for i, offset in enumerate(offsets):
            if offset > start:
                idx = max(0, i - 1)
                break
        lo = idx
        while lo > 0:
            previous = lines[lo - 1].strip()
            if not previous or previous.endswith((".", ":", ";", "*")):
                break
            if not re.search(r"[a-z]", previous):
                break  # a section heading, not part of the sentence
            lo -= 1
        hi = idx
        while hi + 1 < len(lines):
            current = lines[hi].strip()
            following = lines[hi + 1].strip()
            if not following or current.endswith("."):
                break
            hi += 1
        return offsets[lo], offsets[hi] + len(lines[hi])

    @classmethod
    def _lit_sentence(cls, text: str, start: int, end: int) -> str:
        """The line-spanning sentence around a match, whitespace-normalised."""
        left, right = cls._lit_span(text, start, end)
        return " ".join(text[left:right].split())[:400]

    #: A single newline inside a paragraph is a PDF *rendering* artefact, not a
    #: syntactic break.  Two consecutive newlines are a paragraph break and are
    #: left alone, so a match can never join unrelated paragraphs.
    _LIT_WRAP = re.compile(r"(?<!\n)\n(?!\n)")

    #: A run of blanked characters: summary-table rows, section headings and
    #: nil labels are replaced by spaces at their original width, so a match
    #: that touches one has walked out of the prose it belongs to.
    _LIT_MASKED_REGION = re.compile(r"\s{3,}")

    @classmethod
    def _lit_match_text(cls, masked: str) -> str:
        """``masked`` with hard line wraps turned into spaces *at the same
        offsets*.

        The extractor's regulatory patterns exclude ``\\n`` so that a match
        cannot run across a sentence; on a hard-wrapped PDF line that exclusion
        also breaks a single sentence in half (A29 P2: ``SEBI \\nfiled`` matched
        nothing).  Replacing a lone newline with one space keeps every offset
        identical, so a span computed on this text is still a span on the page
        and the emitted quotation is still a verbatim slice.
        """
        return cls._LIT_WRAP.sub(" ", masked)

    @classmethod
    def _lit_sentence_bounds(
        cls, masked: str, lo: int, hi: int, start: int
    ) -> Tuple[int, int]:
        """Narrow ``[lo, hi)`` to the sentence containing ``start``.

        A line span is bounded by the lines a match happens to touch, and a
        filing paragraph of 800-1,800 characters is one line span.  This finds
        the sentence inside it so that the 600-character quotability rule (A29
        P1) measures a sentence rather than an accident of typesetting.  A
        period only ends a sentence when the next character starts a new one and
        the period is not part of a known abbreviation, and a sentence never
        crosses a blank line.
        """
        if hi <= lo or not (lo <= start < hi):
            return lo, hi
        breaks: List[int] = []
        window = masked[lo:hi]
        for match in re.finditer(r"[.!?](?=\s)", window):
            pos = lo + match.start()
            following = pos + 1
            while following < hi and masked[following].isspace():
                following += 1
            if following >= hi:
                continue
            if not (masked[following].isupper() or masked[following] in "(\"'\u201c\u2018"):
                continue
            word = re.search(r"([A-Za-z]{1,6})$", masked[lo:pos])
            if word is not None and word.group(1).lower() in cls._LIT_SENTENCE_ABBREV:
                continue
            breaks.append(pos)
        left = lo
        right = hi
        for pos in breaks:
            if pos < start:
                left = pos + 1
            else:
                right = pos + 1
                break
        return left, right

    @classmethod
    def _lit_party_groups(cls, text: str) -> List[str]:
        """Which A24 party groups ``text`` names (headings are classified)."""
        return [
            label
            for label, pattern in cls._LIT_PARTY_GROUPS
            if re.search(pattern, text, re.IGNORECASE)
        ]

    @classmethod
    def _lit_section_party_map(
        cls, lit_pages: Sequence[Tuple[int, str]]
    ) -> List[Tuple[int, int, str, str]]:
        """Section headings in the litigation section that name exactly one party.

        A29 P3.  Only a heading that identifies precisely one A24 group is
        usable: "Outstanding litigation involving the Directors" is a party
        statement for everything under it, while "Outstanding tax claims
        involving the Company, Promoter, Subsidiaries and Directors" is
        ambiguous and contributes nothing.  Heading lines are read from the
        *original* page text because the prose routes mask them.
        """
        out: List[Tuple[int, int, str, str]] = []
        for page, text in lit_pages:
            if not text:
                continue
            for match in cls._LIT_SECTION_HEADING.finditer(text):
                groups = cls._lit_party_groups(match.group("title"))
                # An empty group means "this heading does not identify one
                # party" -- it is recorded so that it *clears* whatever an
                # earlier heading established, which is the fail-closed reading
                # of an ambiguous scope.
                out.append(
                    (page, match.start(), match.group(0).strip(), groups[0] if len(groups) == 1 else "")
                )
        return out

    @staticmethod
    def _lit_party_from_heading(
        headings: Sequence[Tuple[int, int, str, str]], page: int, start: int
    ) -> Optional[Tuple[str, str]]:
        """The last section heading at or before ``(page, start)``, if any."""
        found: Optional[Tuple[int, int, str, str]] = None
        for heading in headings:
            if (heading[0], heading[1]) <= (page, start):
                found = heading
            else:
                break
        if found is None or not found[3]:
            return None
        return found[2], found[3]

    @classmethod
    def _reg_action_status(cls, sentence: str) -> str:
        """``pending`` / ``concluded`` / ``unspecified``, as the quotation states."""
        if cls._REG_STATUS_PENDING.search(sentence):
            return "pending"
        if cls._REG_STATUS_CONCLUDED.search(sentence):
            return "concluded"
        return "unspecified"

    @classmethod
    def _lit_agencies(cls, sentence: str) -> Tuple[bool, bool]:
        """(SEBI named?, Enforcement Directorate named?) for one sentence.

        Kept as a pair because the two states differ: a sentence naming only
        SEBI can *accuse* (the flag covers "SEBI or ED") but cannot *exonerate*,
        because exoneration has to speak for the regulator it does not name.
        """
        return (
            bool(cls._REG_AGENCY_SEBI.search(sentence)),
            bool(cls._REG_AGENCY_ED.search(sentence)),
        )

    @staticmethod
    def _lit_parties_named(quote: str) -> str:
        """Which party groups an emitted statement actually names (audit note)."""
        found: List[str] = []
        for label, pattern in (
            ("Company", r"\bcompany\b"),
            ("Subsidiaries", r"\bsubsi"),
            ("Directors", r"\bdirectors?\b"),
            ("Promoters", r"\bpromoters?\b"),
            ("KMP", r"\bkey\s+managerial\s+personnel\b|\bKMP\b"),
            ("Senior management", r"\bsenior\s+management\b"),
        ):
            if re.search(pattern, quote, re.IGNORECASE):
                found.append(label)
        return ", ".join(found) if found else "not stated"

    def _litigation_bucket_finding(
        self, lit_pages: Sequence[Tuple[int, str]]
    ) -> Optional[Tuple[str, int, str, str]]:
        """Classify the litigation bucket, or return None when unevidenced.

        Returns ``(bucket, page, verbatim quote, basis)``.  Every branch is
        driven by text present on the page it cites; no finding -- rather than
        the favourable ``"clean"`` bucket -- is the answer when the section is
        missing, empty, unreadable or ambiguous.

        Order is deliberate.  An adverse statement wins over any structured nil
        and over any absence statement, because "no litigation is pending
        except as described below" is a real disclosure; a structured table can
        then only *add* an adverse finding, never cancel one.
        """
        # 1. Adverse prose, on the governed vocabulary, with a polarity guard.
        #    The strongest finding in the range wins, as before: a civil
        #    mention on an earlier page does not hide a criminal one later.
        prose = self._lit_prose_pages(lit_pages)
        adverse: Optional[Tuple[int, str]] = None
        civil_hit: Optional[Tuple[int, str]] = None
        by_page = dict(lit_pages)
        for page, masked in prose:
            if not masked:
                continue
            original = by_page.get(page, masked)
            for regex, is_criminal in (
                (self._LIT_CRIMINAL_PHRASE, True),
                (self._LIT_CIVIL_PHRASE, False),
            ):
                for match in regex.finditer(masked):
                    if self._LIT_NEGATION.search(self._lit_prefix(masked, match.start())):
                        continue  # "no outstanding ... material civil litigation" is not civil litigation
                    lo, hi = self._lit_span(masked, match.start(), match.end())
                    quote = " ".join(original[lo:hi].split())[:400]
                    if is_criminal:
                        adverse = (page, quote)
                        break
                    if civil_hit is None:
                        civil_hit = (page, quote)
            if adverse is not None:
                break
        if adverse is not None:
            return ("criminal_or_regulatory", adverse[0], adverse[1], "prose")
        if civil_hit is not None:
            return ("minor_civil", civil_hit[0], civil_hit[1], "prose")

        # 2. Statutory summary table: cell counts per party group and type.
        table = self._litigation_table_finding(lit_pages)
        if table is not None:
            return table

        # 3. Labelled list form ("Criminal proceedings against the Company: Nil").
        labelled = self._litigation_labelled_finding(lit_pages)
        if labelled is not None:
            return labelled

        # 4. Explicit statement that no proceedings exist -> the clean bucket,
        #    now supported by a quotation instead of by the absence of one.
        for page, masked in prose:
            if not masked:
                continue
            original = by_page.get(page, masked)
            for match in list(self._LIT_ABSENCE.finditer(masked)) + list(
                self._LIT_ABSENCE_NONE_OF.finditer(masked)
            ):
                gap = match.groupdict().get("gap")
                if gap and self._LIT_ABSENCE_GAP_VERB.search(gap):
                    continue
                lo, hi = self._lit_span(masked, match.start(), match.end())
                sentence = " ".join(original[lo:hi].split())[:400]
                if not self._LIT_PARTY.search(sentence):
                    continue  # nothing is asserted absent for any party
                if not self._lit_absence_is_comprehensive(sentence):
                    # A denial of one proceeding type leaves the rest of the
                    # population undisclosed: no bucket, so the criterion is
                    # UNKNOWN rather than awarded the favourable end.
                    continue
                if not self._lit_absence_covers_population(sentence):
                    # A24-D1: a nil naming fewer parties than the bucket is
                    # defined over does not establish absence for the rest.
                    continue
                return ("clean", page, sentence, "prose-absence")
        return None

    def _lit_table_header(
        self, text: str
    ) -> Optional[Tuple[int, List[Optional[str]], str]]:
        """Locate an ICDR summary-table header: ``(header_end, keys, quote)``.

        Shared by the bucket and the regulatory-action routes so that both read
        the same column mapping and neither re-derives it differently.
        """
        head = self._LIT_TABLE_HEAD.search(text)
        if head is None:
            return None
        line_start = text.rfind("\n", 0, head.start()) + 1
        line_end = text.find("\n", head.start())
        header_line = text[line_start: line_end if line_end != -1 else len(text)]
        columns = self._lit_cells(header_line)
        if len(columns) < 3:
            return None
        keys: List[Optional[str]] = []
        for cell in columns[1:]:
            key: Optional[str] = None
            for name, pattern in self._LIT_TABLE_COLUMNS:
                if pattern.search(cell):
                    key = name
                    break
            keys.append(key)
        if not any(key in ("criminal", "civil", "regulatory", "sebi") for key in keys):
            return None  # an unmappable header is not evidence either way
        return head.end(), keys, " ".join(header_line.split())[:400]

    def _sebi_ed_table_finding(
        self, lit_pages: Sequence[Tuple[int, str]]
    ) -> Optional[Tuple[bool, int, str, Dict[str, str]]]:
        """A non-nil SEBI / stock-exchange cell on an adverse table row.

        The ICDR summary table is where an outstanding disciplinary action by
        SEBI is disclosed, so a count in that column is a positive finding.  Its
        ``Nil`` is deliberately not read as a verified absence: the column is
        scoped by its own heading (frequently "against our Promoters in the last
        five years") and never mentions the Enforcement Directorate, so it can
        clear nothing.
        """
        for page, text in lit_pages:
            if not text:
                continue
            header = self._lit_table_header(text)
            if header is None:
                continue
            _, keys, _ = header
            if "sebi" not in keys:
                continue
            sebi_at = keys.index("sebi")
            for row in self._LIT_TABLE_ROW.finditer(text):
                if row.group("side").lower() != "against":
                    continue  # "by our Company" is the issuer's own claim
                parts = self._lit_row_cells(row.group("rest"))
                if len(parts) != len(keys):
                    continue
                cell = parts[sebi_at]
                if not self._LIT_CELL_COUNT.match(cell):
                    continue  # Nil / NA / unreadable: no action stated
                if float(cell.replace(",", "").rstrip("%")) > 0:
                    return (
                        True,
                        page,
                        " ".join(row.group(0).split())[:400],
                        {"status": "unspecified", "party_basis": "table"},
                    )
        return None

    def _litigation_table_finding(
        self, lit_pages: Sequence[Tuple[int, str]]
    ) -> Optional[Tuple[str, int, str, str]]:
        """Read the ICDR "summary table of outstanding litigation".

        Fail-closed by construction: a header that cannot be mapped to columns,
        or a row whose cell count does not match the column count, yields no
        finding at all.  A partially-read table is ambiguous evidence, and
        ambiguity is UNKNOWN -- never the favourable bucket.  A count in a
        column that maps to no governed bucket (tax exposures, for instance)
        blocks ``clean`` without inventing a bucket of its own, so a filing
        that discloses *something* can never be reported as litigation-free.
        """
        for page, text in lit_pages:
            if not text:
                continue
            header = self._lit_table_header(text)
            if header is None:
                continue
            _, keys, header_quote = header

            adverse = civil = sebi = False
            unmapped = False
            adverse_rows = 0
            unreadable_adverse_rows = 0
            evidence_row: Optional[Tuple[int, str]] = None
            # A24-D1: which parties the *readable* "against" rows cover.
            covered_parties: set = set()
            for row in self._LIT_TABLE_ROW.finditer(text):
                side = row.group("side").lower()
                parts = self._lit_row_cells(row.group("rest"))
                if len(parts) != len(keys):
                    # An adverse row that cannot be read leaves the population
                    # incomplete, so "clean" is off the table even if every
                    # other row says nil.
                    if side == "against":
                        unreadable_adverse_rows += 1
                    continue
                if side == "against":
                    # Only the "against" rows describe exposure; a table whose
                    # rows are all "by our Company" states no adverse litigation
                    # but also proves nothing about what is not shown.
                    adverse_rows += 1
                counts: Dict[str, bool] = {}
                readable = True
                for key, cell in zip(keys, parts):
                    if key is None:
                        continue
                    if self._LIT_CELL_NIL.match(cell):
                        counts[key] = False
                    elif self._LIT_CELL_COUNT.match(cell):
                        counts[key] = float(cell.replace(",", "").rstrip("%")) > 0
                    else:
                        readable = False
                        break
                if not readable or not counts:
                    continue
                if side == "against":
                    # A24-D1: coverage is claimed only by a row whose cells were
                    # actually read.  A party whose row exists but cannot be
                    # parsed is a party whose position is unknown, so counting it
                    # as covered would let an unreadable Directors row help clear
                    # the table.
                    party_class = self._lit_party_class(row.group("party"))
                    if party_class is not None:
                        covered_parties.add(party_class)
                quote = " ".join(row.group(0).split())[:400]
                if counts.get("sebi") and side == "against":
                    sebi = True
                    evidence_row = (page, quote)
                if side == "against":
                    if counts.get("criminal") or counts.get("regulatory"):
                        adverse = True
                        evidence_row = (page, quote)
                    elif counts.get("civil"):
                        civil = True
                        if evidence_row is None:
                            evidence_row = (page, quote)
                    elif any(counts.values()):
                        # disclosed, but its type maps to no governed bucket
                        unmapped = True
                        if evidence_row is None:
                            evidence_row = (page, quote)
            if adverse_rows == 0:
                continue
            if adverse or sebi:
                # An affirmative disclosure stands on its own evidence: a row
                # elsewhere in the table that could not be parsed can add a
                # proceeding, never cancel one.
                return ("criminal_or_regulatory", evidence_row[0], evidence_row[1], "summary-table")
            if unreadable_adverse_rows:
                # Only a *favourable* conclusion needs the whole adverse
                # population read; an unreadable row makes the table's silence
                # ambiguous, which is UNKNOWN -- never the favourable bucket.
                return None
            if civil:
                # Material civil litigation is more favourable than a criminal
                # or regulatory matter, so it is likewise withheld while part of
                # the table is unreadable.
                return ("minor_civil", evidence_row[0], evidence_row[1], "summary-table")
            if unmapped:
                return None
            # A table that omits a whole proceeding type cannot prove its
            # absence, so "clean" additionally requires the columns that the
            # bucket is defined over to be present.
            if not {"criminal", "civil", "regulatory"} <= {key for key in keys if key}:
                return None
            if not {"company", "promoters", "directors"} <= covered_parties:
                # A24-D1, the same rule the prose route applies: a table whose
                # "against" rows reach fewer than the three parties of the
                # criterion's population covers only the parties it shows, and a
                # row that is missing is not a row that says Nil.
                return None
            return ("clean", page, header_quote, "summary-table")
        return None

    def _litigation_labelled_finding(
        self, lit_pages: Sequence[Tuple[int, str]]
    ) -> Optional[Tuple[str, int, str, str]]:
        """Read the labelled list form used inside the litigation section.

        Only "against" rows are adverse: proceedings *initiated by* the issuer
        are its own claims, not a risk to the screening result, and are
        therefore recorded without a bucket change.
        """
        adverse: Optional[Tuple[int, str, str]] = None
        civil: Optional[Tuple[int, str, str]] = None
        seen_nil = False
        for page, text in lit_pages:
            if not text:
                continue
            for match in self._LIT_LABELLED.finditer(text):
                value = (match.group("value") or "").strip()
                quote = " ".join(match.group(0).split())[:400]
                if self._LIT_CELL_NIL.match(value):
                    seen_nil = True
                    continue
                label = match.group("label")
                if not self._LIT_LABEL_ADVERSE.search(label):
                    continue  # no party is named as respondent: not a finding
                if self._LIT_LABEL_SELF.search(label) and not re.search(
                    r"\bagainst\b", label, re.IGNORECASE
                ):
                    continue  # the issuer as claimant, not as defendant
                low = label.lower()
                entry = (page, quote, low)
                if (
                    "criminal" in low
                    or "regulatory" in low
                    or "disciplinary" in low
                    or "statutory" in low
                ):
                    adverse = adverse or entry
                elif "civil" in low or "litigation" in low:
                    civil = civil or entry
                else:
                    continue  # e.g. tax: disclosed, but it maps to no bucket
        if adverse is not None:
            return ("criminal_or_regulatory", adverse[0], adverse[1], "labelled-list")
        if civil is not None:
            return ("minor_civil", civil[0], civil[1], "labelled-list")
        if seen_nil:
            return None  # nils in some categories do not establish nil litigation
        return None

    def _sebi_ed_labelled_finding(
        self, lit_pages: Sequence[Tuple[int, str]]
    ) -> Optional[Tuple[bool, int, str, Dict[str, str]]]:
        """A labelled category line naming SEBI or the ED, with a count.

        "Disciplinary actions by SEBI ... involving our Company" followed by
        "2" is a disclosed action; followed by "Nil" it is not, and a nil in a
        promoter-scoped category is no evidence about the issuer, so this route
        can only ever answer True.
        """
        for page, text in lit_pages:
            if not text:
                continue
            for match in self._LIT_LABELLED.finditer(text):
                if match.group("count") is None:
                    continue  # a nil value is not an action
                label = match.group("label")
                if self._LIT_LABEL_SELF.search(label) and not re.search(
                    r"\bagainst\b", label, re.IGNORECASE
                ):
                    continue
                if not self._LIT_LABEL_ADVERSE.search(label):
                    continue
                if not self._LIT_PARTY.search(label):
                    continue
                sebi_named, ed_named = self._lit_agencies(label)
                if not (sebi_named or ed_named):
                    continue
                return (
                    True,
                    page,
                    " ".join(match.group(0).split())[:400],
                    {"status": "unspecified", "party_basis": "labelled"},
                )
        return None

    def _sebi_ed_action_finding(
        self, lit_pages: Sequence[Tuple[int, str]], allow_absence: bool = True
    ) -> Optional[Tuple[bool, int, str, Dict[str, str]]]:
        """Establish an active SEBI/ED action -- or its explicit absence.

        ``True`` requires a regulator to be named as the actor of an action
        involving a party of the issuer; ``False`` requires an explicit
        negative covering both SEBI and the Enforcement Directorate, because
        the governed flag is ``sebi_ed_action_active``.  Boilerplate that merely
        cites SEBI regulations, and negatives scoped to one regulator only,
        emit nothing -- which is exactly how a promoter-scoped "Nil" cell or an
        inaccessible regulatory page must be represented.

        ``allow_absence`` is the A25 condition that the searched range was
        genuinely usable: when the litigation section was located only by the
        hardcoded fallback window, or a page in the range failed to extract, the
        denial is still an *observed* statement but the coverage behind it is not
        established, so ``False`` is withheld and the field stays absent
        (K2 UNVERIFIED).  ``True`` never depends on this: a disclosed action is
        evidence whoever found it.

        A29 (K2-A) changes four things in the *positive* route, none of them a
        relaxation of what counts as evidence:

        * the 600-character quotability cap measures the **sentence** around the
          match, not the line span a paragraph happened to produce (P1);
        * a hard line wrap is treated as a space for matching only, at identical
          offsets, so a sentence the PDF broke in half still matches (P2);
        * a sentence that names no party may take its party from the last
          section-level heading that names exactly one A24 group, and the
          attribution is carried in the evidence note (P3);
        * a bare regulation citation no longer vetoes a sentence that reports a
          dated or forked adjudicative event (P4), and a regulator's own
          ``filed`` / ``preferred`` appeal of an order is recognised (P5).

        The fourth element of the returned tuple is the A29 metadata: the status
        the quotation states (``pending`` / ``concluded`` / ``unspecified``) and
        how the party was established.  It is evidence presentation only -- the
        boolean is decided exactly as before.
        """
        negative: Optional[Tuple[int, str]] = None
        headings = self._lit_section_party_map(lit_pages)
        for page, text in self._lit_prose_pages(lit_pages):
            if not text:
                continue
            original = dict(lit_pages).get(page, text)
            match_text = self._lit_match_text(text)
            # An explicit *absence* statement naming both regulators needs no
            # act verb: "there are no active SEBI or ED regulatory proceedings
            # against our Company" is the whole finding.  Collected rather than
            # returned, because a positive statement anywhere in the range
            # outranks a general denial elsewhere.
            for match in list(self._LIT_ABSENCE.finditer(match_text)) + list(
                self._LIT_ABSENCE_NONE_OF.finditer(match_text)
            ):
                gap = match.groupdict().get("gap")
                if gap and self._LIT_ABSENCE_GAP_VERB.search(gap):
                    continue
                lo, hi = self._lit_span(text, match.start(), match.end())
                lo, hi = self._lit_sentence_bounds(text, lo, hi, match.start())
                statement = " ".join(original[lo:hi].split())
                if len(statement) > 600:
                    continue
                sebi_named, ed_named = self._lit_agencies(statement)
                if not (sebi_named and ed_named):
                    continue
                if self._REG_BOILERPLATE.search(statement):
                    continue
                if self._REG_ABSENT_CLOSED.search(statement):
                    continue  # a closed-period nil cannot speak for the present
                if not self._LIT_PARTY.search(statement):
                    continue
                negative = (page, statement)
                break
        for page, text in self._lit_prose_pages(lit_pages):
            if not text:
                continue
            original = dict(lit_pages).get(page, text)
            match_text = self._lit_match_text(text)
            for match in self._REG_ACTION.finditer(match_text):
                # P2 lets a match cross a hard wrap; it must never cross a
                # masked region (summary table, section heading, nil label),
                # which survives as a run of blanked characters.
                if self._LIT_MASKED_REGION.search(match.group(0)):
                    continue
                lo, hi = self._lit_span(text, match.start(), match.end())
                segment = self._lit_sentence_bounds(text, lo, hi, match.start())
                if segment[0] <= match.start() and segment[1] >= match.end():
                    lo, hi = segment
                sentence = " ".join(original[lo:hi].split())
                if len(sentence) > 600:
                    continue  # still not one quotable sentence: fail closed
                sebi_named, ed_named = self._lit_agencies(sentence)
                if not (sebi_named or ed_named):
                    continue
                if self._REG_BOILERPLATE.search(sentence):
                    continue
                if self._REG_META_DISCOURSE.search(sentence):
                    continue  # a statement about the section, not an event
                if self._REG_BOILERPLATE_CITE.search(
                    sentence
                ) and not self._REG_ADJUDICATIVE_EVENT.search(sentence):
                    continue
                meta: Dict[str, str] = {
                    "status": self._reg_action_status(sentence),
                    "party_basis": "quoted",
                }
                if not self._LIT_PARTY.search(sentence):
                    # A29 P3: the filing states party scope in its section
                    # heading ("Outstanding litigation involving the
                    # Directors") and then names the party by its own short name
                    # in the sentence.  Attribute only when the heading names
                    # exactly one A24 group, and record the heading so the
                    # attribution is auditable and separable.  With the P3 flag
                    # off, a sentence that names no party emits nothing -- the
                    # pre-A29 behaviour, bit for bit.
                    attributed = (
                        self._lit_party_from_heading(headings, page, match.start())
                        if self._LIT_HEADING_PARTY_ATTRIBUTION
                        else None
                    )
                    if attributed is None:
                        continue
                    meta["party_basis"] = "heading"
                    meta["heading"] = attributed[0]
                    meta["party"] = attributed[1]
                # Negation is tested over the sentence *up to the regulator
                # mention*, not only over the raw prefix before the matched
                # noun: the noun can sit on a heading line while the negation
                # sits on the next line of the same statement ("Actions by
                # statutory or regulatory authorities: ... there are no
                # outstanding disciplinary actions or penalties imposed by
                # SEBI ...").  Erring towards "negated" costs a missed trigger;
                # asserting an action the filing expressly denies triggers K2
                # and an AVOID verdict.
                agency_at = len(sentence)
                for regex in (self._REG_AGENCY_SEBI, self._REG_AGENCY_ED):
                    found = regex.search(sentence)
                    if found is not None:
                        agency_at = min(agency_at, found.start())
                verb = self._REG_ACT_VERB.search(sentence)
                # Cut at the act when the sentence states one, so that a
                # negation between the regulator and the act is seen
                # ("SEBI has *not* imposed"); cut at the regulator otherwise
                # ("*no* outstanding disciplinary actions ... imposed by SEBI"
                # already had its negation before the matched noun).
                cut_at = verb.start() if verb is not None else agency_at
                window = sentence[:cut_at]
                negated = bool(self._LIT_NEGATION.search(window)) or bool(
                    self._LIT_NEGATION.search(self._lit_prefix(text, match.start()))
                )
                if negated:
                    # A SEBI-only (or ED-only) negative cannot clear a flag
                    # whose governed name covers both regulators; the field
                    # stays absent and K2 stays UNVERIFIED.
                    if (
                        sebi_named
                        and ed_named
                        and allow_absence
                        and not self._REG_ABSENT_CLOSED.search(sentence)
                    ):
                        return (
                            False,
                            page,
                            sentence,
                            {"status": "absent", "party_basis": meta["party_basis"]},
                        )
                    continue
                return (True, page, sentence, meta)
        if negative is not None and allow_absence:
            return (False, negative[0], negative[1], {"status": "absent", "party_basis": "quoted"})
        return None

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

        if auditor_name is None:
            for report_page in report_pages:
                text = self.extract_page_text(report_page)
                if "Chartered Accountants" not in text:
                    continue
                signers = re.findall(r"\bFor\s+([^\n]+?\bLLP)\b", text)
                if signers:
                    auditor_name = "; ".join(signers)
                    break

        # Auditor continuity stated directly by the statutory auditors' own
        # letter in the General Information section:
        #   "There has been no change in our statutory auditors in the last
        #    three years preceding the date of this Red Herring Prospectus."
        # That is the positive continuity statement A22 requires (the same
        # auditor for the last three years), stated in the negative about
        # *change*; it is read here rather than inferred from the absence of a
        # change statement.  It used to be read only inside the branch that had
        # already captured the firm's name, so the letter alone -- which states
        # no name -- established nothing.  A filing without the sentence stays
        # UNKNOWN.
        tenure_direct = re.compile(
            r"there\s+has\s+been\s+no\s+change\s+in\s+(?:our|the)\s+statutory\s+auditors?"
            r"\s+in\s+the\s+last\s+(?:three|3)\s+years",
            re.IGNORECASE,
        )
        direct_changed: Optional[bool] = None
        direct_page = found_opinion_page
        direct_quote = ""
        for p in range(1, min(160, self.page_count) + 1):
            txt = self.extract_page_text(p)
            if "statutory auditor" not in txt.lower():
                continue
            m_direct = tenure_direct.search(" ".join(txt.split()))
            if m_direct:
                direct_changed = False
                direct_page = p
                direct_quote = (
                    self._opinion_sentence(txt, re.escape(m_direct.group(0)))
                    or m_direct.group(0)
                )
                break

        aud_changed_3y: Optional[bool] = None
        tenure_quote = ""
        tenure_page = found_opinion_page

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
                if not m_tenure:
                    m_tenure = re.search(
                        r"Auditors[’']\s*report\s+jointly\s+issued\s+by\s+us[\s\S]{0,450}?years\s+ended[\s\S]{0,80}?2026,?\s*2025\s+and\s+2024",
                        txt, re.I,
                    )
                if m_tenure:
                    aud_changed_3y = False
                    tenure_page = p
                    tenure_quote = self._opinion_sentence(
                        txt, re.escape(m_tenure.group(0))
                    ) or " ".join(m_tenure.group(0).split())
                    break


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
            eom_page = found_opinion_page
            eom_text = section_text
            if not negative_eom:
                for candidate_page in scan_pages:
                    text = self.extract_page_text(candidate_page)
                    explicit = re.search(
                        r"\b(?:no|nil|without)\s+(?:any\s+)?emphasis\s+of\s+matters?[^.]{0,400}?auditor[’']s?\s+report[^.]{0,300}",
                        text, re.I,
                    )
                    if explicit and not self._has_positive_emphasis_of_matter(explicit.group(0)):
                        negative_eom = explicit
                        eom_text = explicit.group(0)
                        eom_page = candidate_page
                        break
            if negative_eom and not self._has_positive_emphasis_of_matter(eom_text):
                eom_quote = self._opinion_sentence(
                    eom_text, r"\b(?:no|nil|without)\s+(?:any\s+)?emphasis\s+of\s+matters?\b"
                ) or " ".join(negative_eom.group(0).split())
                extractions.append(
                    RawExtraction(
                        field_path="governance.repeated_eom",
                        candidate_value=False,
                        raw_text=eom_quote,
                        page=eom_page,
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

        # Continuity is emitted whether or not the firm's name was captured on
        # the scanned pages: the statement that the same auditors served for
        # three years names no firm, and it is evidence about the tenure on its
        # own.  (Emission used to sit inside the ``auditor_name`` branch, so a
        # filing whose letter named nobody recorded no continuity at all.)
        if aud_changed_3y is None and direct_changed is not None:
            aud_changed_3y = direct_changed
            tenure_page = direct_page
            tenure_quote = direct_quote
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

        # 2. Litigation bucket & SEBI/ED action (D-5).
        #
        # Emitted only from evidence.  The scan below used to end in
        # ``lit_bucket = "clean"`` / ``sebi_active = False`` regardless of what
        # it found, and both fields were appended unconditionally with a
        # quotation of its own making.  Now: a finding is emitted when the
        # litigation section states it, and is *absent* -- so the derived metric
        # is UNKNOWN and K2 is UNVERIFIED rather than CLEAR -- when the section
        # is missing, unreadable, empty, or ambiguous about who the proceeding
        # involves or which regulator acted.
        # A25-D2 (approved 2026-10-20): the two observability states, recorded
        # where they are knowable.  ``lit_located`` distinguishes a window that
        # came from the filing's own table of contents from the hardcoded
        # fallback; ``lit_all_read`` says whether every page of the window was
        # actually read (A25-D2 per-page status) rather than failing to extract.
        lit_range = page_ranges.get("litigation") if page_ranges else None
        lit_located = lit_range is not None
        p_lstart, p_lend = lit_range or (430, min(500, self.page_count))
        lit_pages = [
            (p, self.extract_page_text(p))
            for p in range(max(1, p_lstart), min(p_lend, self.page_count) + 1)
        ]
        # A range that covers no page at all (a short document, a fallback
        # window past its end) is not a searched section.
        lit_scanned_pages = list(range(max(1, p_lstart), min(p_lend, self.page_count) + 1))
        lit_all_read = self.pages_read(p_lstart, p_lend)
        # A25-D1: an absence may be *emitted* only on a located, completely read
        # window.  Adverse findings do not depend on this -- seeing an action is
        # evidence regardless of how the page was found.
        lit_allow_absence = lit_located and lit_all_read
        lit_coverage = (
            "litigation section located via the filing's table of contents; "
            if lit_located
            else "litigation window from the hardcoded fallback range, not located in the table of contents; "
        ) + (
            "all pages in the window read"
            if lit_all_read and lit_scanned_pages
            else "window did not cover any readable page"
            if not lit_scanned_pages
            else "one or more pages in the window failed to extract"
        )

        lit_finding = self._litigation_bucket_finding(lit_pages)
        if lit_finding is not None:
            lit_bucket, lit_page, lit_quote, lit_basis = lit_finding
            extractions.append(
                RawExtraction(
                    field_path="governance.litigation_bucket",
                    candidate_value=lit_bucket,
                    raw_text=lit_quote,
                    page=lit_page,
                    section="Outstanding Litigation",
                    locator="Outstanding Litigation and Material Developments",
                    quote=lit_quote,
                    notes=(
                        f"bucket from the {lit_basis} disclosure; coverage basis: {lit_coverage}; "
                        f"parties named in the quoted text: {self._lit_parties_named(lit_quote)}"
                    ),
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95 if lit_basis != "prose" else 0.90,
                )
            )

        sebi_finding = self._sebi_ed_action_finding(
            lit_pages, allow_absence=lit_allow_absence
        )
        if sebi_finding is None or sebi_finding[0] is not True:
            # A disclosed action outranks a general denial, and the structured
            # routes state one positively; neither can state the absence, which
            # is why they are never consulted for False.
            for extra in (
                self._sebi_ed_table_finding(lit_pages),
                self._sebi_ed_labelled_finding(lit_pages),
            ):
                if extra is not None:
                    sebi_finding = extra
                    break
        if sebi_finding is not None:
            sebi_active, sebi_page, sebi_quote, sebi_meta = sebi_finding
            sebi_notes = (
                # A25-D1: a `false` means "no SEBI/ED action is disclosed
                # on the searched pages", never that the engine verified
                # none exists.  The wording the record carries is the
                # difference, so the stronger claim cannot be rebuilt
                # downstream from a bare boolean.
                "SEBI/ED action disclosed by the filing"
                if sebi_active
                else "issuer-authored denial that any SEBI or ED action exists; "
                "no external or regulator-source check was performed, so this is "
                "absence of disclosure, not verified absence"
            )
            if sebi_active:
                # A29 (K2-A) makes the *status* of the disclosed action part of
                # the evidence rather than something a reader has to infer from
                # a past-tense verb: a proceeding the filing states is pending
                # at the cut-off is an active action, and a concluded one is
                # reported as concluded so the two are never conflated.
                sebi_notes += (
                    f"; action status stated in the quotation: {sebi_meta.get('status', 'unspecified')}"
                )
                if sebi_meta.get("status") == "pending":
                    sebi_notes += (
                        "; A29 (K2-A): a proceeding pending at the evaluation cut-off is an "
                        "active action, subject to the existing party-scope rules"
                    )
                if sebi_meta.get("party_basis") == "heading":
                    sebi_notes += (
                        f"; party attributed under A29 (P3) from the section heading "
                        f"\"{sebi_meta.get('heading', '')}\" -> {sebi_meta.get('party', '')}; "
                        "the quoted sentence does not itself name an A24 party group"
                    )
            sebi_notes += (
                f"; search basis: {lit_coverage}; parties named in the quoted text: "
                + self._lit_parties_named(sebi_quote)
            )
            extractions.append(
                RawExtraction(
                    field_path="governance.sebi_ed_action_active",
                    candidate_value=sebi_active,
                    raw_text=sebi_quote,
                    page=sebi_page,
                    section="Outstanding Litigation",
                    locator="Disciplinary actions by SEBI or Stock Exchanges",
                    quote=sebi_quote,
                    notes=sebi_notes,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.92,
                )
            )

        # 3. Board independence
        mgmt_range = page_ranges.get("our_management") if page_ranges else None
        p_mstart, p_mend = mgmt_range or (290, min(320, self.page_count))

        # Board independence is emitted only when the composition sentence is
        # actually read.  It used to be initialised False and emitted
        # unconditionally, with a synthesised quotation ("Board independent
        # majority: False"): an unread board section therefore earned the
        # unfavourable end of a scored criterion without evidence -- the mirror
        # image of the A23 defect, and equally a missing value reported as a
        # finding.  The composition sentence spells the counts in words
        # ("we have seven Directors on our Board, of whom ... three are
        # Independent Directors"), so word numbers are read too.
        _WORD_NUMBERS = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
            "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        }

        def _small_count(token: str) -> Optional[int]:
            token = token.strip().lower()
            if token.isdigit():
                return int(token)
            return _WORD_NUMBERS.get(token)

        independent_majority: Optional[bool] = None
        found_mgmt_page = p_mstart
        board_quote: Optional[str] = None

        for p in range(p_mstart, p_mend + 1):
            txt = self.extract_page_text(p)
            if "independent director" in txt.lower():
                flat = " ".join(txt.split())
                m_total = re.search(
                    r'(?:have|comprises?|consists?\s+of)\s+(\d{1,2}|[a-z]{3,9})\s*\(?\d*\)?\s*Directors\s+on\s+our\s+Board',
                    flat, re.IGNORECASE,
                ) or re.search(r'comprises?\s+(\d{1,2}|[a-z]{3,9})\s*Directors', flat, re.IGNORECASE)
                m_indep = re.search(
                    r'(\d{1,2}|[a-z]{3,9})\s+are\s+Independent\s+Directors', flat, re.IGNORECASE
                )
                if m_total and m_indep:
                    total_cnt = _small_count(m_total.group(1))
                    indep_cnt = _small_count(m_indep.group(1))
                    if total_cnt and indep_cnt and indep_cnt <= total_cnt:
                        found_mgmt_page = p
                        independent_majority = (indep_cnt / total_cnt) > 0.50
                        start = max(0, m_total.start() - 40)
                        end = min(len(flat), m_indep.end() + 20)
                        board_quote = flat[start:end].strip()
                        break
                    # A page that mentions independent directors without the
                    # composition sentence is not the answer: keep looking
                    # rather than stopping at the first candidate page.

        if independent_majority is not None:
            extractions.append(
                RawExtraction(
                    field_path="governance.board_independent_majority",
                    candidate_value=independent_majority,
                    raw_text=board_quote or str(independent_majority),
                    page=found_mgmt_page,
                    section="Our Management",
                    locator="Board of Directors Composition",
                    quote=board_quote or "",
                    quote_is_processing=board_quote is None,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.90,
                )
            )

        # 4. Related Party Transactions (% of revenue)
        rpt_pct = None
        rpt_page = p_start
        rpt_quote = ""
        for p in range(min(p_start, 35), min(p_end, 70) + 1):
            txt = self.extract_page_text(p)
            if "sum of all related party" in txt.lower() and "% of revenue" in txt.lower():
                m_rpt = re.search(r'as a % of revenue from operations[^\n]*?\n\s*([0-9\.\s]+)', txt, re.IGNORECASE)
                if m_rpt:
                    # The evidence is the filing's own row, never a sentence
                    # the engine wrote about the value it found.
                    rpt_quote = " ".join(m_rpt.group(0).split())
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
                    quote=rpt_quote,
                    quote_is_processing=not rpt_quote,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )

        return extractions

    # ------------------------------------------------------------------
    # Customer / supplier concentration (table form)
    # ------------------------------------------------------------------
    # "Top five suppliers 1,140.95 21.94 % 1,232.05 26.95% 670.30 15.17%"
    #
    # The earlier readers required the literal token "top 5": a filing that
    # spells the row "Top five suppliers" (an ordinary ICDR table) matched
    # nothing, so a disclosed 21.94% became "neither top-5 customer nor top-5
    # supplier concentration is disclosed".  The row is read here by position
    # in its own table: each row carries amount/percentage *pairs*, and the
    # first pair is the latest period.  The fiscal table is preferred over the
    # interim table on the same page (A20's fiscal-column rule), and the read
    # fails closed when no fiscal header precedes the row.
    _CONCENTRATION_ROW = re.compile(
        r"^(top\s*(?:five|5)|top\s*(?:ten|10)|largest)\s+(suppliers?|customers?)\b(.*)$",
        re.IGNORECASE,
    )
    _CONCENTRATION_FISCAL_HEADER = re.compile(
        r"fiscal\s*20\d\d(?:[\s\S]{0,60}fiscal\s*20\d\d)", re.IGNORECASE
    )

    def _top_five_concentration(
        self, pages: Sequence[int]
    ) -> Dict[str, Tuple[float, int, str]]:
        """Latest-fiscal-year top-five supplier/customer percentages."""
        found: Dict[str, Tuple[float, int, str]] = {}
        for p in pages:
            txt = self.extract_page_text(p)
            if "top" not in txt.lower():
                continue
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            fiscal_index: Optional[int] = None
            for i, line in enumerate(lines):
                if self._CONCENTRATION_FISCAL_HEADER.search(line):
                    fiscal_index = i
            if fiscal_index is None:
                continue
            pending: List[str] = []
            for line in lines[fiscal_index + 1:]:
                match = self._CONCENTRATION_ROW.match(line)
                if not match:
                    if re.match(r"^notes?\b", line, re.IGNORECASE) or line.startswith("*"):
                        break
                    pending = []
                    continue
                shape, party, rest = match.groups()
                if shape.lower().replace(" ", "") not in ("topfive", "top5"):
                    pending = []
                    continue
                text = " ".join((rest or "").split())
                if not re.search(r"\d", text) and len(text) < 40:
                    # the row wraps: its cells continue on the next line(s)
                    pending = [line]
                    continue
                row = " ".join([line] + pending) if pending else line
                pending = []
                pairs = re.findall(r"(\d[\d,]*(?:\.\d+)?)\s*(?:\.\d+)?\s*%", " ".join([text] + []))
                if not pairs:
                    continue
                try:
                    pct = float(pairs[0].replace(",", ""))
                except ValueError:
                    continue
                key = "supplier" if party.lower().startswith("supplier") else "customer"
                if 0 < pct <= 100 and key not in found:
                    found[key] = (pct, p, " ".join(row.split()))
        return found

    # ------------------------------------------------------------------
    # Industry report identity (source of the industry forecast)
    # ------------------------------------------------------------------
    # spec s12 requires a CAGR to be scored with its scope, forecast period
    # AND source together.  The source is the filing's own defined term:
    #   "CRISIL Report" Industry Report titled "Assessment of ..." dated
    #   September, 2026, issued by CRISIL Intelligence
    _INDUSTRY_REPORT_DEF = re.compile(
        r"[\u201c\"](?P<label>[^\u201d\"]{2,40}?[Rr]eport)[\u201d\"]\s*,?\s*"
        r"(?:an?\s+)?Industry\s+Report\s+titled\s*[\u201c\"](?P<title>[^\u201d\"]{10,200})[\u201d\"]\s*,?\s*"
        r"dated\s+(?P<date>[A-Z][a-z]+\s*\d{1,2},\s*20\d\d|[A-Z][a-z]+\s*,?\s*20\d\d)",
    )

    def _industry_report_source(self, scan_end: int = 40) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """The filing's defined industry report, verbatim, with its page."""
        for p in range(1, min(scan_end, self.page_count) + 1):
            txt = self.extract_page_text(p)
            if "industry report titled" not in txt.lower():
                continue
            match = self._INDUSTRY_REPORT_DEF.search(" ".join(txt.split()))
            if not match:
                continue
            label = match.group("label").strip()
            title = match.group("title").strip()
            date = match.group("date").strip()
            source = f'{label} ("{title}", dated {date})'
            return source, p, match.group(0)
        return None, None, None

    _CAGR_RANGE = re.compile(
        r"(?:the\s+)?(?P<scope>[A-Za-z][A-Za-z\s\-]{2,60}?)\s+market\s+is\s+expected\s+to\s+grow\s+"
        r"at\s+a\s+CAGR\s+of\s+(?P<lo>\d+(?:\.\d+)?)\s*(?:to|-|\u2013)\s*(?P<hi>\d+(?:\.\d+)?)\s*%"
        r"\s*(?:between|from)\s+fiscals?\s*(?P<y1>20\d\d)\s*(?:and|to|-|\u2013)\s*(?P<y2>20\d\d)",
        re.IGNORECASE,
    )

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

        # 1c. Table form ("Top five suppliers ... 21.94 %"), used when the
        #     legacy "top 5" row reader found nothing.
        concentration_quotes: Dict[str, str] = {}
        concentration_pages: Dict[str, int] = {}
        if top5_supp is None or top5_cust is None:
            concentration_pages_to_scan: List[int] = []
            # The concentration tables sit in the risk factors / business
            # sections.  The risk-factors section has no TOC entry, so the
            # bounded window the legacy readers use is scanned too when no
            # range is routed (otherwise a filing whose TOC omits it can never
            # be read here, which is the defect being repaired).
            base_start, base_end = (21, min(120, self.page_count))
            concentration_pages_to_scan.extend(range(base_start, base_end + 1))
            for key in ("risk_factors", "our_business", "mda"):
                rng = page_ranges.get(key) if page_ranges else None
                if rng:
                    concentration_pages_to_scan.extend(
                        range(max(1, rng[0]), min(rng[1], self.page_count) + 1)
                    )
            table_read = self._top_five_concentration(sorted(set(concentration_pages_to_scan)))
            if top5_supp is None and "supplier" in table_read:
                top5_supp, found_supp_page, concentration_quotes["supplier"] = table_read["supplier"]
                concentration_pages["supplier"] = found_supp_page
            if top5_cust is None and "customer" in table_read:
                top5_cust, found_cust_page, concentration_quotes["customer"] = table_read["customer"]
                concentration_pages["customer"] = found_cust_page

        if top5_supp is not None:
            quote = concentration_quotes.get("supplier")
            extractions.append(
                RawExtraction(
                    field_path="business.top5_supplier_pct",
                    candidate_value=top5_supp,
                    raw_text=quote or str(top5_supp),
                    raw_unit="PERCENT",
                    page=found_supp_page or 51,
                    section="Risk Factors",
                    locator=(
                        "Top-five suppliers table, latest fiscal-year column"
                        if quote
                        else "Supplier concentration table"
                    ),
                    quote=quote or f"Top 5 suppliers accounted for {top5_supp}% of purchases",
                    quote_is_processing=quote is None,
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
        cagr_scope_label = None
        cagr_source_quote = None
        found_ind_page = p_istart
        cagr_candidates = []

        industry_source_label, industry_source_page, industry_source_quote = self._industry_report_source()

        for p in range(p_istart, min(p_iend + 1, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if "cagr" not in txt.lower():
                continue

            # 0. A disclosed forecast RANGE with its own period, e.g.
            #    "the healthcare delivery market is expected to grow at a CAGR
            #     of 10 to 12% between fiscals 2025 and 2030".
            #    The value recorded is the *lower* bound: the filing does not
            #    commit to a point estimate, and the lower bound is the
            #    conservative reading (the disclosed range is recorded in the
            #    quote).  This path is only used when the filing also defines
            #    the report that published the forecast, because the metric
            #    requires value, scope, period and source together.
            m_range = self._CAGR_RANGE.search(" ".join(txt.split()))
            if m_range and industry_source_label:
                lo = float(m_range.group("lo"))
                hi = float(m_range.group("hi"))
                if 0 < lo <= hi < 100:
                    scope_phrase = m_range.group("scope").strip()
                    scope_phrase = re.sub(r"^(?:the|a|an)\s+", "", scope_phrase, flags=re.IGNORECASE)
                    is_india = "india" in txt.lower() or "domestic" in txt.lower()
                    cagr_candidates.append({
                        "val": lo,
                        # ``industry_scope`` is a schema enum (india/global/
                        # regional); the market the forecast describes is kept
                        # in ``scope_label`` for the locator, never smuggled
                        # into the enum field.
                        "scope": "india" if is_india else "global",
                        "scope_label": (
                            f"India {scope_phrase} market" if is_india else f"{scope_phrase} market"
                        ),
                        "period": f"FY{m_range.group('y1')}-FY{m_range.group('y2')}",
                        "source": str(industry_source_label),
                        "quote": m_range.group(0),
                        "range": (lo, hi),
                        "source_page": industry_source_page,
                        "source_quote": industry_source_quote,
                        "page": p,
                        "priority": 100,
                    })

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
            cagr_scope_label = best.get("scope_label")
            cagr_source_quote = best.get("source_quote")
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
                    locator=(
                        f"Industry Scope ({cagr_scope_label})" if cagr_scope_label else "Industry Scope"
                    ),
                    quote=cagr_quote or "",
                    quote_is_processing=cagr_quote is None,
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
                    quote=cagr_quote or "",
                    quote_is_processing=cagr_quote is None,
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
                    quote=cagr_source_quote or cagr_quote or "",
                    quote_is_processing=(cagr_source_quote or cagr_quote) is None,
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
        {
            # Paras Healthcare RHP (2026), "F. Comparison of accounting
            # ratios with Listed Industry Peers": Face value, Enterprise
            # Value, Closing Price, Revenue, EBITDA, EPS (Basic), EPS
            # (Diluted), P/E, EV/EBITDA, Net Worth, Return on Net Worth,
            # NAV per Equity Share.  The numeric block wraps across physical
            # lines (a value splits mid-number), so the rows are read by the
            # streaming reader below rather than one line at a time.
            "id": "listed_peers_ev_ebitda",
            "width": 12,
            "layout": "stream",
            "header": re.compile(
                r"face\s*value.{0,300}?enterprise\s*value.{0,240}?closing\s*price"
                r".{0,240}?revenue.{0,160}?ebitda.{0,160}?eps.{0,80}?basic.{0,80}?eps"
                r".{0,80}?diluted.{0,160}?p\s*/\s*e.{0,80}?ev\s*/\s*ebitda"
                r".{0,120}?net\s*worth.{0,120}?net\s*asset\s*value\s*per\s*equity\s*share",
                re.IGNORECASE | re.DOTALL,
            ),
            "cmp": 2, "pe": 7, "roe": 10, "nav": 11,
        },
    )

    # Label that separates the issuer's own row from the peer rows in a
    # "listed peers" comparison table.  The issuer's row is *not* a peer: it
    # carries its own (often undisclosed) multiples and must not enter the
    # peer set.
    _PEER_ROW_LABEL = re.compile(
        r"^(?:industry\s+)?(?:listed\s+peers?|peer\s+group|peer\s+companies)\s*[*:]?$",
        re.IGNORECASE,
    )

    @classmethod
    def _peer_stream_rows(
        cls, txt: str, width: int
    ) -> List[Tuple[str, List[Optional[float]]]]:
        """Read a peer table whose numeric block wraps across physical lines.

        Used for layouts where a single row is not confined to one line: a
        value may split mid-number (``1,228,529.3`` / ``9``), and a company
        name may wrap over several lines.  Only rows that appear *after* the
        "Listed Peers" label are returned, so the issuer's own row is never
        counted as a peer; a table without that label yields no rows at all
        (fail-closed).
        """
        raw_lines = [" ".join(l.split()) for l in txt.splitlines() if l.split()]
        # Glue a number that the page layout split across two lines: the last
        # value on a line is printed with a single decimal ("1,228,529.3")
        # and its final digit stands alone on the next line ("9").  Only that
        # shape is rejoined -- a line holding a complete value (two decimals,
        # as every other cell in these tables) is never merged with the next.
        joined: List[str] = []
        for line in raw_lines:
            prev_tokens = joined[-1].split() if joined else []
            if (
                prev_tokens
                and re.fullmatch(r"\d{1,2}", line)
                and re.fullmatch(r"[\d,]+\.\d", prev_tokens[-1])
            ):
                joined[-1] = joined[-1] + line
                continue
            joined.append(line)

        rows: List[Tuple[str, List[Optional[float]]]] = []
        name: List[str] = []
        cells: List[Optional[float]] = []
        in_peers = False
        for line in joined:
            if re.match(r"^(?:notes?\b|source\b|#)", line, re.IGNORECASE):
                break
            if cls._PEER_ROW_LABEL.match(line):
                in_peers = True
                name, cells = [], []
                continue
            line_cells: List[Optional[float]] = []
            text_tokens: List[str] = []
            for token in line.split():
                is_cell, value = cls._peer_cell(token)
                if is_cell:
                    line_cells.append(value)
                else:
                    text_tokens.append(token)
            if not line_cells:
                name.append(line)
                continue
            if cells and len(cells) + len(line_cells) > width:
                # An abandoned partial row is dropped and its name released:
                # the next company's name must not inherit it.
                cells, name = [], []
            cells.extend(line_cells)
            if len(cells) == width:
                pname = " ".join(name) or " ".join(text_tokens)
                pname = re.sub(r"\s*\^\s*$", "", pname).strip()
                if in_peers:
                    rows.append((pname, cells))
                name, cells = [], []
            elif len(cells) > width:
                cells = []
        return rows

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
        core = without_footnote.rstrip("*†%^#").replace(",", "").strip()
        if core.startswith("(") and core.endswith(")"):
            try:
                return (True, -float(core[1:-1].strip()))
            except ValueError:
                return (False, None)
        try:
            return (True, float(core))
        except ValueError:
            pass
        placeholder = without_footnote.rstrip("*†$^#").strip().lower()
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
            # The table is identified by its recognised column header, not by
            # a fixed title phrase: filings head it "Comparison of accounting
            # ratios with Listed Industry Peers", "Listed Peers" or "Industry
            # Peer Group", and the older gate skipped any table whose wording
            # differed.  A page carrying "peer" is still required, so an
            # unrelated table cannot be mistaken for a peer comparison.
            if "peer" in txt.lower():
                shape: Optional[Dict[str, Any]] = None
                header_match = None
                for cand in self._PEER_SHAPES:
                    header_match = cand["header"].search(txt)
                    if header_match:
                        shape = cand
                        break
                if shape is None:
                    # Table present but the column layout is not one this
                    # parser can map without guessing: emit no peers
                    # (fail-closed) rather than wrong-field values.
                    continue

                # The valuation date belongs to *this* table: the section also
                # carries ratios struck at the balance-sheet date, so a range
                # scan would stamp the peer multiples with the wrong day.
                table_as_of = self._peer_as_of_date(p, p) or as_of_date

                if shape.get("layout") == "stream":
                    # Rows wrap across physical lines: read them from the
                    # remainder of the page that follows the column header.
                    for pname, cells in self._peer_stream_rows(
                        txt[header_match.end():], shape["width"]
                    ):
                        if len(cells) == shape["width"] + 1 and cells[0] is not None and \
                                float(cells[0]).is_integer() and 1 <= cells[0] <= 50:
                            cells = cells[1:]
                        if len(cells) != shape["width"]:
                            continue
                        if not self._peer_name_is_valid(pname):
                            continue
                        cmp_index = shape["cmp"]
                        cmp = cells[cmp_index] if cmp_index is not None else None
                        pe = cells[shape["pe"]]
                        ronw = cells[shape["roe"]]
                        nav = cells[shape["nav"]]
                        if pe is None and (nav is None or nav <= 0):
                            # No multiple and no NAV: the row cannot place the
                            # peer on any valuation axis.
                            continue
                        pb = round(cmp / nav, 2) if (cmp and nav and nav > 0) else None
                        peers.append({
                            "name": pname,
                            "business_match": "partial",
                            "listed_years": None,
                            "as_of": table_as_of,
                            "pe": pe,
                            "pb": pb,
                            "roe_pct": ronw,
                            "source_id": self.doc.source_id,
                        })
                    if peers:
                        break
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
                    page=p,
                    section="Basis for Offer Price",
                    locator="Comparison of Accounting Ratios with Listed Industry Peers",
                    # The quotation is the table's own column header, which
                    # names the columns the peers were read from.
                    quote=" ".join(header_match.group(0).split()),
                    quote_is_processing=False,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )

        return extractions
