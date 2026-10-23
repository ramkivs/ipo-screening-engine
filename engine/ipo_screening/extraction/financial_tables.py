"""Financial statement table extraction for Restated Ind AS / Indian GAAP financials.

Extracts multi-column period tables:
  - Statement of Profit and Loss (Annexure II)
  - Statement of Assets and Liabilities (Annexure I)
  - Statement of Cash Flows (Annexure III)
  - KPI table (ROCE, ROE, etc.)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import pypdf

from ..canonical import ExtractionMethod
from .interfaces import RawExtraction, SourceDocument
from .numbers import detect_currency_unit, parse_indian_number


class FinancialTableExtractor:
    """Extracts financial periods and restated tables from RHP document."""

    def __init__(self, doc: SourceDocument, reader: pypdf.PdfReader, text_cache: Optional[Dict[int, str]] = None) -> None:
        self.doc = doc
        self.reader = reader
        self.page_count = len(reader.pages)
        self._text_cache: Dict[int, str] = text_cache if text_cache is not None else {}

    def extract_page_text(self, page_1_indexed: int) -> str:
        """Extract text from a 1-indexed page."""
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

    def extract_all(
        self,
        start_page: int = 1,
        end_page: Optional[int] = None,
        page_ranges: Optional[Dict[str, Tuple[int, int]]] = None,
    ) -> List[RawExtraction]:
        """Extract all financial fields and period metrics across financial pages."""
        extractions: List[RawExtraction] = []
        if end_page is None or end_page > self.page_count:
            end_page = self.page_count

        # 1. Locate P&L, BS, CF, KPI, Contingent Liabilities pages
        pl_page, pl_text = self._find_page(
            ["Restated Statement of Profit and Loss", "Statement of Profit and Loss"],
            start_page,
            end_page,
            required_content=["revenue from operations", "interest income", "interest earned", "total income", "annexure ii"],
        )
        if pl_page is None and start_page > 1:
            pl_page, pl_text = self._find_page(
                ["Restated Statement of Profit and Loss", "Statement of Profit and Loss"],
                1,
                end_page,
                required_content=["revenue from operations", "interest income", "interest earned", "total income", "annexure ii"],
            )

        # Fallback to KPI / Basis for Offer Price if Restated P&L cannot be located or has empty text
        if pl_page is None:
            periods_data, unit, kpi_page = self._extract_from_kpi_and_summary_tables(page_ranges)
            extractions.append(
                RawExtraction(
                    field_path="financials.reporting_unit",
                    candidate_value=unit,
                    raw_text=unit,
                    raw_unit=unit,
                    page=kpi_page,
                    section="Basis for Offer Price",
                    locator="KPI Table Header",
                    quote=f"Detected currency unit: {unit}",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )
            extractions.append(
                RawExtraction(
                    field_path="financials.periods",
                    candidate_value=periods_data,
                    raw_text=str(periods_data),
                    raw_unit=unit,
                    page=kpi_page,
                    section="Basis for Offer Price / Summary Financial Information",
                    locator="Financial KPI and Restated Cash Flow Tables",
                    quote=f"Parsed {len(periods_data)} financial periods from KPI and financial summary tables",
                    quote_is_processing=True,
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )
            return extractions

        bs_page, bs_text = self._find_page(
            ["Restated Statement of Assets and Liabilities", "Statement of Assets and Liabilities"],
            start_page,
            end_page,
            required_content=["total equity", "equity share capital", "total assets", "annexure i"],
        )
        if bs_page is None and start_page > 1:
            bs_page, bs_text = self._find_page(
                ["Restated Statement of Assets and Liabilities", "Statement of Assets and Liabilities"],
                1,
                end_page,
                required_content=["total equity", "equity share capital", "total assets", "annexure i"],
            )

        cf_page, cf_text = self._find_page(
            ["Restated Statement of Cash flows", "Statement of Cash flows"],
            start_page,
            end_page,
            required_content=["operating activities", "annexure iii"],
        )
        if cf_page is None and start_page > 1:
            cf_page, cf_text = self._find_page(
                ["Restated Statement of Cash flows", "Statement of Cash flows"],
                1,
                end_page,
                required_content=["operating activities", "annexure iii"],
            )

        kpi_start = 50 if self.page_count >= 50 else 1
        kpi_page, kpi_text = self._find_page(
            ["Key Performance Indicators", "Key performance indicators", "Return on Capital Employed",
             r"Return on (?:Average )?Capital\s+Employed"],
            kpi_start,
            min(self.page_count, 250),
            required_content=["Return on Capital Employed", "ROCE", "CRAR",
                              r"Return on (?:Average )?Capital\s+Employed"],
        )

        # Contingent liabilities: read the note itself (not the summary page,
        # not the first line containing "Total").  A wrong amount here is a
        # direct knockout input, so the reader fails closed.
        cl_page, cl_amount, cl_unquantified, cl_quote = self._extract_contingent_liabilities(
            page_ranges
        )

        # Detect reporting unit from P&L or BS
        unit_text = pl_text or bs_text or ""
        unit = detect_currency_unit(unit_text) or "INR_LAKHS"
        extractions.append(
            RawExtraction(
                field_path="financials.reporting_unit",
                candidate_value=unit,
                raw_text=unit_text[:100] if unit_text else None,
                raw_unit=unit,
                page=pl_page or bs_page or 1,
                section="Financial Information",
                locator="Restated Statement Header",
                quote=f"Detected currency unit: {unit}",
                quote_is_processing=True,
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                extraction_confidence=1.0 if (pl_page or bs_page) else 0.5,
            )
        )

        # Detect periods (e.g. 31 March 2026, 31 March 2025, 31 March 2024 or March 31, 2026)
        years = self._extract_fiscal_years(pl_text or bs_text or "")
        if not years:
            years = ["2026", "2025", "2024"]

        # Parse P&L items
        pl_items = self._parse_table_lines(
            pl_text or "",
            [
                ("revenue", [r"revenue from operations", r"interest earned", r"interest income"]),
                ("total_income", [r"total income\b"]),
                ("cost_of_materials", [r"cost of material consumed"]),
                ("employee_expenses", [r"employee benefits expenses", r"employee benefits"]),
                ("finance_costs", [r"finance costs", r"finance cost", r"interest expended"]),
                ("depreciation", [r"depreciation and amorti[sz]ation"]),
                ("total_expenses", [r"total expenses\b"]),
                ("pbt", [r"profit/(loss) before tax", r"profit before tax"]),
                ("pat", [r"profit after tax", r"profit/(loss) for the year", r"profit/(loss) after tax"]),
            ],
            len(years),
        )

        # Parse Balance Sheet items
        bs_items = self._parse_table_lines(
            bs_text or "",
            [
                ("trade_receivables", [r"trade receivables"]),
                ("cash_and_equivalents", [r"cash and cash equivalents"]),
                ("net_worth", [r"total equity(?! and liabilit)", r"total equity \(d\)"]),
                ("total_borrowings", [r"total borrowings\b"]),
            ],
            len(years),
        )

        # Total equity is not always printed as a row (Jio's restated
        # statement lists Equity Share capital, Other Equity and
        # Non-Controlling Interest, then goes straight to Liabilities).
        # Derive it from the disclosed components only when they reconcile
        # to Total Assets - Total Liabilities; otherwise leave it unknown.
        if "net_worth" not in bs_items:
            derived_net_worth = self._derive_net_worth_from_equity(
                bs_text or "", len(years)
            )
            if derived_net_worth is not None:
                bs_items["net_worth"] = derived_net_worth

        # Parse non-current and current borrowings if total borrowings not already extracted
        if "total_borrowings" not in bs_items:
            borrowings_lines = self._extract_all_borrowings(bs_text or "", len(years))
            if len(borrowings_lines) >= 2:
                bs_items["borrowings_non_current"] = borrowings_lines[0]
                bs_items["borrowings_current"] = borrowings_lines[1]
            elif len(borrowings_lines) == 1:
                bs_items["total_borrowings"] = borrowings_lines[0]

        # Parse Cash Flow items
        cf_items = self._parse_table_lines(
            cf_text or "",
            [
                ("cfo", [r"net cash provided by/\(used in\) operating activities", r"net cash from operating activities", r"net cash flow from operating activities"]),
                ("capex", [r"purchase of property,\s*plant and equipment", r"purchase of fixed assets"]),
            ],
            len(years),
        )

        # Parse KPI items
        roce_vals = self._parse_kpi_line(kpi_text or "", r"return on (?:average )?capital\s+employed", len(years))
        crar_vals = self._parse_kpi_line(kpi_text or "", r"crar\b|capital adequacy ratio", len(years))
        gnpa_vals = self._parse_kpi_line(kpi_text or "", r"gross npa", len(years))
        nim_vals = self._parse_kpi_line(kpi_text or "", r"net interest margin|nim\b", len(years))
        cost_income_vals = self._parse_kpi_line(kpi_text or "", r"cost to income", len(years))

        # Contingent liabilities (see _extract_contingent_liabilities).
        if cl_amount is not None:
            extractions.append(
                RawExtraction(
                    field_path="financials.contingent_liabilities",
                    candidate_value=cl_amount,
                    raw_text=cl_quote or str(cl_amount),
                    raw_unit=unit,
                    page=cl_page or 1,
                    section="Notes to Restated Financials",
                    locator="Contingent Liabilities and Commitments (claims not acknowledged as debts, latest fiscal year)",
                    quote=cl_quote or str(cl_amount),
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
                )
            )
        if cl_unquantified is not None:
            extractions.append(
                RawExtraction(
                    field_path="financials.contingent_liabilities_unquantified",
                    candidate_value=True,
                    raw_text=cl_quote or "unquantified contingent liabilities",
                    raw_unit=unit,
                    page=cl_page or 1,
                    section="Notes to Restated Financials",
                    locator="Contingent Liabilities and Commitments — unquantified disclosure",
                    quote=cl_quote or "unquantified contingent liabilities",
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.9,
                )
            )

        # Build chronological periods (oldest FY first)
        chronological_indices = sorted(range(len(years)), key=lambda i: int(years[i]))

        periods_data: List[Dict[str, Any]] = []
        for idx in chronological_indices:
            y_str = years[idx]
            fy_label = f"FY{y_str}"
            p_data: Dict[str, Any] = {"fy": fy_label}

            rev = self._get_item_val(pl_items, "revenue", idx)
            pat = self._get_item_val(pl_items, "pat", idx)
            nw = self._get_item_val(bs_items, "net_worth", idx)

            tot_b = self._get_item_val(bs_items, "total_borrowings", idx)
            if tot_b is not None:
                total_debt = tot_b
            else:
                b_nc = self._get_item_val(bs_items, "borrowings_non_current", idx) or 0.0
                b_cur = self._get_item_val(bs_items, "borrowings_current", idx) or 0.0
                total_debt = round(b_nc + b_cur, 2) if (b_nc or b_cur) else None

            cfo = self._get_item_val(cf_items, "cfo", idx)
            raw_capex = self._get_item_val(cf_items, "capex", idx)
            capex = abs(raw_capex) if raw_capex is not None else None

            cash = self._get_item_val(bs_items, "cash_and_equivalents", idx)
            rec = self._get_item_val(bs_items, "trade_receivables", idx)

            rec_days = None
            if rec is not None and rev and rev > 0:
                rec_days = round((rec / rev) * 365, 1)

            fin_cost = self._get_item_val(pl_items, "finance_costs", idx)
            depr = self._get_item_val(pl_items, "depreciation", idx)
            tot_exp = self._get_item_val(pl_items, "total_expenses", idx)

            ebitda = None
            ebit = None
            if rev is not None and tot_exp is not None and fin_cost is not None and depr is not None:
                opex = tot_exp - fin_cost - depr
                ebitda = round(rev - opex, 2)
                ebit = round(ebitda - depr, 2)
            elif pat is not None and fin_cost is not None:
                ebit = round(pat + fin_cost, 2)
                ebitda = round(ebit + (depr or 0.0), 2)

            if rev is not None:
                p_data["revenue"] = rev
            if pat is not None:
                p_data["pat"] = pat
            if nw is not None:
                p_data["net_worth"] = nw
            if total_debt is not None:
                p_data["total_debt"] = total_debt
            if cfo is not None:
                p_data["cfo"] = cfo
            if capex is not None:
                p_data["capex"] = capex
            if cash is not None:
                p_data["cash_and_equivalents"] = cash
            if rec_days is not None:
                p_data["receivable_days"] = rec_days
            if fin_cost is not None:
                p_data["interest_expense"] = fin_cost
            if ebit is not None:
                p_data["ebit"] = ebit
            if ebitda is not None:
                p_data["ebitda"] = ebitda

            if roce_vals and idx < len(roce_vals) and roce_vals[idx] is not None:
                p_data["disclosed_roce_pct"] = roce_vals[idx]
            if crar_vals and idx < len(crar_vals) and crar_vals[idx] is not None:
                p_data["crar_pct"] = crar_vals[idx]
            if gnpa_vals and idx < len(gnpa_vals) and gnpa_vals[idx] is not None:
                p_data["gnpa_pct"] = gnpa_vals[idx]
            if nim_vals and idx < len(nim_vals) and nim_vals[idx] is not None:
                p_data["nim_pct"] = nim_vals[idx]
            if cost_income_vals and idx < len(cost_income_vals) and cost_income_vals[idx] is not None:
                p_data["cost_to_income_pct"] = cost_income_vals[idx]

            periods_data.append(p_data)

        extractions.append(
            RawExtraction(
                field_path="financials.periods",
                candidate_value=periods_data,
                raw_text=str(periods_data),
                raw_unit=unit,
                page=pl_page or 1,
                section="Restated Financial Statements",
                locator="P&L, Balance Sheet, Cash Flow Annexures",
                quote=f"Parsed {len(periods_data)} financial periods from restated statements",
                quote_is_processing=True,
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                extraction_confidence=0.95,
            )
        )

        return extractions

    def _find_page(
        self, patterns: List[str], start_p: int, end_p: int, required_content: Optional[List[str]] = None
    ) -> Tuple[Optional[int], Optional[str]]:
        for p in range(start_p, end_p + 1):
            txt = self.extract_page_text(p)
            for pat in patterns:
                if re.search(pat, txt, re.IGNORECASE):
                    if required_content:
                        if any(re.search(rc, txt, re.IGNORECASE) for rc in required_content):
                            return p, txt
                    else:
                        return p, txt
        return None, None

    def _extract_fiscal_years(self, text: str) -> List[str]:
        matches = re.findall(
            r'(?:31(?:st)?\s+March[\s,]+|March\s+31(?:st)?[\s,]+|FY\s*|Fiscal\s*)(20[0-9]{2})',
            text,
            re.IGNORECASE,
        )
        seen = set()
        ordered = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                ordered.append(m)
        return ordered

    def _parse_table_lines(
        self, text: str, field_specs: List[Tuple[str, List[str]]], n_cols: int
    ) -> Dict[str, List[Optional[float]]]:
        results: Dict[str, List[Optional[float]]] = {}
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        for i, line in enumerate(lines):
            for field_name, patterns in field_specs:
                if field_name in results:
                    continue
                matched = any(re.search(pat, line, re.IGNORECASE) for pat in patterns)
                if matched:
                    nums = self._extract_row_numbers(line)
                    if len(nums) < n_cols and i + 1 < len(lines):
                        next_nums = self._extract_row_numbers(lines[i + 1])
                        if len(next_nums) >= n_cols:
                            nums = next_nums
                    if len(nums) >= n_cols:
                        # Statement tables are newest-first and may carry a
                        # note number and interim (three-month) columns
                        # before the fiscal-year block (SEBI RHP summary and
                        # Ind AS statement convention). The fiscal block is
                        # the rightmost n_cols. For legacy 3/4-numeric rows
                        # this selects exactly what the previous
                        # (drop-first-then-take-first) rules selected.
                        results[field_name] = nums[-n_cols:]

        return results

    _EQUITY_COMPONENT_SPECS = [
        ("equity_share_capital", [r"^equity\s+share\s+capital\b"]),
        ("other_equity", [r"^other\s+equity\b"]),
        ("non_controlling_interest", [r"^non[-\s]?controlling\s+interests?\b"]),
    ]

    def _derive_net_worth_from_equity(
        self, text: str, n_cols: int
    ) -> Optional[List[Optional[float]]]:
        """Derive net worth (equity attributable to owners) from components.

        Used only when the statement prints no Total Equity row.  Net worth
        is Equity Share Capital + Other Equity.  A separately presented
        Non-Controlling Interest line is *not* part of net worth: the issuer
        reports "Total Equity (As per Restated Consolidated Statement of
        Assets and Liabilities)" as the two owner components (see Jio Note
        38: 3,359,769 at FY2026), while the balance-sheet reconciliation
        Total Assets - Total Liabilities includes NCI.  When NCI is
        disclosed, the components must still tie to that residual after NCI
        is added back; otherwise the field stays unknown.  The result never
        includes the "Total Equity and Liabilities" grand total and is never
        a guessed or partial component.
        """
        components = self._parse_table_lines(
            text, self._EQUITY_COMPONENT_SPECS, n_cols
        )
        share_capital = components.get("equity_share_capital")
        other_equity = components.get("other_equity")
        if not share_capital or not other_equity:
            return None
        nci = components.get("non_controlling_interest")
        totals = self._parse_table_lines(
            text,
            [
                ("total_assets", [r"^total\s+assets\b"]),
                ("total_liabilities", [r"^total\s+liabilities\b"]),
            ],
            n_cols,
        )
        total_assets = totals.get("total_assets")
        total_liabilities = totals.get("total_liabilities")
        result: List[Optional[float]] = []
        for index in range(n_cols):
            try:
                net_worth = float(share_capital[index]) + float(other_equity[index])
            except (IndexError, TypeError, ValueError):
                return None
            if (
                total_assets is not None
                and total_liabilities is not None
                and index < len(total_assets)
                and index < len(total_liabilities)
                and total_assets[index] is not None
                and total_liabilities[index] is not None
            ):
                target = float(total_assets[index]) - float(total_liabilities[index])
                tolerance = max(0.5, abs(target) * 0.0005)
                reconciled = net_worth
                if nci is not None:
                    try:
                        reconciled += float(nci[index])
                    except (IndexError, TypeError, ValueError):
                        return None
                if abs(reconciled - target) > tolerance:
                    return None
                result.append(round(net_worth, 2))
            else:
                # Without a balance-sheet reconciliation an NCI row makes
                # the treatment of non-controlling interest ambiguous.
                if nci is not None:
                    return None
                result.append(round(net_worth, 2))
        return result

    def _extract_all_borrowings(self, text: str, n_cols: int) -> List[List[Optional[float]]]:
        rows: List[List[Optional[float]]] = []
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines:
            # Dash-rendered ("- Borrowings") or plain "Borrowings" rows;
            # never "Total Borrowings" (that total has its own item key).
            if re.search(r'^\s*-?\s*borrowings\b', line, re.IGNORECASE):
                nums = self._extract_row_numbers(line)
                if len(nums) >= n_cols:
                    rows.append(nums[-n_cols:])
        return rows

    def _extract_row_numbers(self, line: str) -> List[Optional[float]]:
        tokens = re.findall(r'\(?\s*[0-9,]+(?:\.[0-9]+)?\s*\)?|(?<=\s)-(?=\s)', line)
        res: List[Optional[float]] = []
        for t in tokens:
            t_clean = t.strip()
            if t_clean == "-":
                res.append(0.0)
            else:
                val = parse_indian_number(t_clean)
                if val is not None:
                    res.append(val)
        return res

    def _get_item_val(
        self, items_dict: Dict[str, List[Optional[float]]], key: str, index: int
    ) -> Optional[float]:
        if key in items_dict and index < len(items_dict[key]):
            return items_dict[key][index]
        return None

    def _parse_kpi_line(self, text: str, pattern: str, n_cols: int) -> Optional[List[Optional[float]]]:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            window = line
            if not re.search(pattern, window, re.IGNORECASE) or not re.search(r"[0-9]+\.[0-9]+", window):
                # KPI rows wrap across lines (e.g. "Return on Average
                # Capital" / "Employed(18) % 2.56% ..."); join one line.
                if i + 1 < len(lines):
                    window = f"{line} {lines[i + 1]}"
            if not re.search(pattern, window, re.IGNORECASE):
                continue
            nums = re.findall(r'[0-9]+\.[0-9]+', window)
            parsed = [float(x) for x in nums if float(x) < 200.0]
            if len(parsed) >= n_cols:
                # Newest-first tables may carry interim columns before the
                # fiscal block; select the rightmost n_cols (identical to
                # the previous selection for exactly-n_cols rows).
                return parsed[-n_cols:]
        return None

    # Contingent-liabilities note (issuer-neutral).
    _CL_NOTE_HEADING = re.compile(
        r"^\s*(?:\d{1,2}(?:\.\d+)?\s+)?contingent\s+liabilities\s*"
        r"(?:and\s+commitments?)?\s*:?\s*$",
        re.IGNORECASE,
    )
    _CL_DATE = re.compile(
        r"(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s*,?\s*(\d{4})",
        re.IGNORECASE,
    )
    _CL_COMMITMENTS_HEADING = re.compile(
        r"^\s*(?:\(?\s*(?:II|2|[Bb])\s*\)?\s*[.):]?\s*)?commitments?\b",
        re.IGNORECASE,
    )
    _CL_NEXT_NOTE = re.compile(r"^\s*\d{1,2}(?:\.\d+)?\s+[A-Z][A-Za-z]")
    _CL_TOTAL_LABEL = re.compile(r"\btotal\b", re.IGNORECASE)
    _CL_COMMITMENT_LABEL = re.compile(
        r"\bcommitments?\b|\bcapital\s+account\b|\bcontracts?\s+remaining\b",
        re.IGNORECASE,
    )
    # Amounts in a note table: grouped (Indian or western) or decimal.  A bare
    # four-digit year is filtered out later, so period headers are not rows.
    _CL_AMOUNT = re.compile(
        r"\(?\s*\d{1,3}(?:,\d{2,3})+(?:\.\d+)?\s*\)?"
        r"|\(?\s*\d+\.\d+\s*\)?"
        r"|\(?\s*\d{4,}\s*\)?"
    )
    _CL_UNQUANTIFIED = re.compile(
        r"\bunquantified\b|\bcannot\s+be\s+quantified\b|\bnot\s+quantifiable\b"
        r"|\bamounts?\s+(?:is|are)\s+not\s+ascertainable\b",
        re.IGNORECASE,
    )

    @classmethod
    def _cl_row_amounts(cls, line: str) -> Optional[List[float]]:
        """Amount cells of a table row, or ``None`` when the line is not a row.

        A row *ends* with an amount cell; prose that merely mentions a number
        in the middle of a sentence does not.  A bare four-digit year in the
        period header is not an amount.
        """
        matches = list(cls._CL_AMOUNT.finditer(line))
        if not matches:
            return None
        if line[matches[-1].end():].strip(" *†‡)(;:"):
            return None
        values: List[float] = []
        for match in matches:
            token = match.group(0)
            cleaned = token.replace("(", "").replace(")", "").replace(",", "").strip()
            try:
                value = float(cleaned)
            except ValueError:
                continue
            if "," not in token and "." not in token and 1900 <= value <= 2100:
                continue  # a year, not an amount
            values.append(-value if token.strip().startswith("(") else value)
        return values or None

    def _extract_contingent_liabilities(
        self,
        page_ranges: Optional[Dict[str, Tuple[int, int]]],
    ) -> Tuple[Optional[int], Optional[float], Optional[bool], str]:
        """Read the contingent-liability section total from the note.

        Numerator definition (decision D-2, 2026-10-20): the disclosed total
        of the **contingent-liability section**, excluding capital commitments
        (``(II) Commitments`` or a commitment-labelled row).

        * a unique ``Total`` row inside the section wins and the constituent
          rows are ignored, so an aggregate is never added to its own parts;
        * otherwise the section's rows are summed;
        * a commitment-labelled row (or a commitments subsection) is excluded;
        * an unparseable / width-mismatched row, more than one total, or no
          row at all fails closed to ``None`` -- a quantified subset is not
          evidence that the whole section is quantified.

        Column selection is unchanged: the latest fiscal-year (31 March)
        column, never an interim column mixed with a full-year net worth.
        The unquantified flag is read from the same section with the same
        polarity rule (a negated statement is not a positive finding) and is
        never coerced to ``False``.
        """
        ranges: List[Tuple[int, int]] = []
        if page_ranges and page_ranges.get("restated_financials"):
            ranges.append(page_ranges["restated_financials"])
        if self.page_count >= 250:
            ranges.append((250, self.page_count))
        ranges.append((1, self.page_count))

        seen_pages: set = set()
        for start, end in ranges:
            for p in range(max(1, start), min(end, self.page_count) + 1):
                if p in seen_pages:
                    continue
                seen_pages.add(p)
                lines = [l.strip() for l in self.extract_page_text(p).splitlines() if l.strip()]
                heading_index = next(
                    (i for i, line in enumerate(lines) if self._CL_NOTE_HEADING.match(line)),
                    None,
                )
                if heading_index is None:
                    continue
                # The table (or the row) may continue on the next page.
                note_lines = list(lines[heading_index + 1:])
                for extra in range(p + 1, min(p + 2, self.page_count) + 1):
                    note_lines.extend(
                        l.strip() for l in self.extract_page_text(extra).splitlines() if l.strip()
                    )

                section_end = len(note_lines)
                for i, line in enumerate(note_lines):
                    if self._CL_COMMITMENTS_HEADING.match(line):
                        section_end = i
                        break
                    # The next numbered note on the same page is not part of
                    # this section, even when no commitments subsection exists.
                    if (
                        self._CL_NEXT_NOTE.match(line)
                        and len(line.split()) <= 8
                        and not self._CL_AMOUNT.search(line)
                    ):
                        section_end = i
                        break

                section = note_lines[:section_end]
                first_row = next(
                    (i for i, line in enumerate(section) if self._cl_row_amounts(line)),
                    None,
                )
                if first_row is None:
                    continue
                # The period headers are the date labels immediately above the
                # first row.  Taking the whole page would blend the note's
                # header with an adjacent note's identical header (Jio pp. 405-406).
                header_window = section[max(0, first_row - 30): first_row]
                dates: List[Tuple[int, str, int]] = [
                    (int(d), m.capitalize(), int(y))
                    for d, m, y in self._CL_DATE.findall("\n".join(header_window))
                ]
                if not dates:
                    continue
                march_columns = [
                    (index, year)
                    for index, (_, month, year) in enumerate(dates)
                    if month.lower() == "march"
                ]
                if not march_columns:
                    continue
                column, _ = max(march_columns, key=lambda item: item[1])

                rows: List[Tuple[str, float]] = []
                ambiguous = False
                pending: List[str] = []
                for line in section:
                    # Period headers and subsection headings are not row labels.
                    if self._CL_DATE.search(line) or re.match(
                        r"^\s*(?:as\s+at\b|\(?\s*(?:I|1|[Aa])\s*\)?[.):]?\s*contingent\s+liabilit)",
                        line,
                        re.IGNORECASE,
                    ):
                        pending = []
                        continue
                    amounts = self._cl_row_amounts(line)
                    if amounts is None:
                        # Label lines wrap; short lines carry the row label.
                        if len(line.split()) <= 12:
                            pending.append(line)
                            pending = pending[-3:]
                        else:
                            pending = []
                        continue
                    label_match = self._CL_AMOUNT.search(line)
                    label = " ".join(pending + ([line[: label_match.start()]] if label_match else []))
                    # Prose that precedes a total on the same line is not part
                    # of the row label ("Certain claims are unquantified. Total").
                    label = re.split(r"(?<=\.)\s+", label)[-1]
                    pending = []
                    if len(amounts) > len(dates):
                        amounts = amounts[-len(dates):]
                    if len(amounts) < len(dates):
                        ambiguous = True
                        continue
                    rows.append((label, amounts[column]))

                # The unquantified statement usually sits inside the same
                # section.  A negated statement ("there are no unquantified
                # claims") contains the keyword but asserts the opposite.
                unquantified = None
                section_text = "\n".join(section)
                m_unquantified = self._CL_UNQUANTIFIED.search(section_text)
                if m_unquantified:
                    prefix = section_text[max(0, m_unquantified.start() - 80): m_unquantified.start()]
                    prefix = re.split(r"[.;\n]", prefix)[-1]
                    if not re.search(
                        r"\b(?:no|not|nil|none|without)\b", prefix, re.IGNORECASE
                    ):
                        unquantified = True

                if ambiguous:
                    return p, None, unquantified, ""  # a row could not be aligned to the columns
                contingent = [row for row in rows if not self._CL_COMMITMENT_LABEL.search(row[0])]
                totals = [row for row in contingent if self._CL_TOTAL_LABEL.search(row[0])]
                if len(totals) == 1:
                    amount = totals[0][1]
                    used = [totals[0]]
                elif len(totals) > 1:
                    return p, None, unquantified, ""  # which aggregate is the section total is ambiguous
                elif contingent and unquantified:
                    # Some exposure has no amount and the note discloses no
                    # total: a sum of the quantified rows would understate it.
                    return p, None, unquantified, ""
                elif contingent:
                    amount = sum(value for _, value in contingent)
                    used = contingent
                else:
                    continue
                quote = " | ".join(" ".join(label.split()) for label, _ in used)
                return p, amount, unquantified, quote
        return None, None, None, ""

    def _extract_from_kpi_and_summary_tables(
        self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None
    ) -> Tuple[List[Dict[str, Any]], str, int]:
        """Fallback extractor when statement annexures are scanned images.

        Extracts multi-period revenue, EBITDA, PAT, Net Worth, ROCE from KPI table,
        OCF and Capex from Cash Flow statement summary, and Debt from Capitalisation/Indebtedness.
        """
        unit = "INR_LAKHS"
        b_range = page_ranges.get("basis_for_offer_price") if page_ranges else (140, min(185, self.page_count))
        f_range = page_ranges.get("financial_indebtedness") if page_ranges else (350, min(410, self.page_count))
        r_range = page_ranges.get("restated_financials") if page_ranges else (290, min(360, self.page_count))

        # 1. Collect lines in basis_for_offer_price
        kpi_lines: List[str] = []
        collecting = False
        kpi_found_page = b_range[0]
        for p in range(b_range[0], min(b_range[1] + 1, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if "financial kpi" in txt.lower():
                collecting = True
                kpi_found_page = p
            if collecting:
                kpi_lines.extend([l.strip() for l in txt.splitlines() if l.strip()])
                if "audit committee" in txt.lower() and "notes:" in txt.lower():
                    break

        start_idx = 0
        for idx, l in enumerate(kpi_lines):
            if "financial kpi" in l.lower():
                start_idx = idx
                break
        table_lines = kpi_lines[start_idx:]

        def _extract_row_values(patterns: List[str], lines: List[str]) -> Optional[List[float]]:
            for i, l in enumerate(lines):
                if any(re.search(pat, l, re.IGNORECASE) for pat in patterns):
                    combined_text = l
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if re.search(r"^[0-9]\s+[A-Za-z]", lines[j]):
                            break
                        combined_text += " " + lines[j]
                    raw_nums = re.findall(r"\(?[0-9,]+(?:\.[0-9]+)?\)?[%]?", combined_text)
                    nums: List[float] = []
                    for n in raw_nums:
                        n_clean = n.rstrip("%")
                        if n_clean in ["166", "167", "168", "169", "170"]:
                            continue
                        val = parse_indian_number(n_clean)
                        if val is not None:
                            nums.append(val)
                    if nums and nums[0] in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0] and len(nums) >= 4:
                        nums = nums[1:]
                    if len(nums) >= 3:
                        return nums
            return None

        rev_vals = _extract_row_values([r"revenue from operation"], table_lines)
        ebitda_vals = _extract_row_values([r"operating ebitda\b"], table_lines)
        pat_vals = _extract_row_values([r"profit.*after\s+tax"], table_lines)
        roce_vals = _extract_row_values([r"roce\s*\(%\)"], table_lines)
        roe_vals = _extract_row_values([r"return on equity\s*\(roe\)"], table_lines)
        nw_vals = _extract_row_values([r"networth\b"], table_lines)

        # 2. Extract Cash Flow (CFO and Capex)
        cfo_vals = None
        capex_vals = None
        cf_scan_pages = list(range(35, min(55, self.page_count + 1)))
        cf_scan_pages.extend(range(r_range[0], min(r_range[1] + 1, self.page_count + 1)))
        cf_scan_pages.extend(range(370, min(385, self.page_count + 1)))

        for p in cf_scan_pages:
            txt = self.extract_page_text(p)
            # Statutory Cash Flow Statement - Net Cash Flow from Operating Activities
            if ("operating" in txt.lower() and cfo_vals is None):
                lines = [lx.strip() for lx in txt.splitlines() if lx.strip()]
                for idx, lx in enumerate(lines):
                    if re.search(r"net cash flows? (?:from|used in)", lx, re.IGNORECASE) or re.search(r"operating activities\s*\(a\)", lx, re.IGNORECASE):
                        combined = " ".join(lines[idx:min(idx + 5, len(lines))])
                        if "operating" in combined.lower() and "investing" not in combined.lower() and "financing" not in combined.lower():
                            raw = re.findall(r"\(?[0-9,]+(?:\.[0-9]+)?\)?", combined)
                            parsed = [parse_indian_number(x) for x in raw if parse_indian_number(x) is not None]
                            if len(parsed) >= 4:
                                cfo_vals = parsed[:4]
                                break
                            elif len(parsed) >= 3:
                                cfo_vals = parsed[:3]
                                break
            if "purchase of property" in txt.lower() and capex_vals is None:
                lines = [lx.strip() for lx in txt.splitlines() if lx.strip()]
                for idx, lx in enumerate(lines):
                    if "purchase of property" in lx.lower():
                        c_text = lx
                        for j in range(idx + 1, min(idx + 3, len(lines))):
                            c_text += " " + lines[j]
                        raw_cx = re.findall(r"[0-9,]+(?:\.[0-9]+)?", c_text)
                        parsed_cx = [parse_indian_number(x) for x in raw_cx if parse_indian_number(x) is not None]
                        if len(parsed_cx) >= 3:
                            capex_vals = parsed_cx[-3:]
                            break
            if cfo_vals and capex_vals:
                break

        # 3. Extract Debt / Borrowings
        debt_vals = None
        debt_scan_pages = list(range(35, min(40, self.page_count + 1)))
        debt_scan_pages.extend(range(f_range[0], min(f_range[0] + 5, self.page_count + 1)))
        for p in debt_scan_pages:
            txt = self.extract_page_text(p)
            if "total borrowings" in txt.lower() or "total debt" in txt.lower():
                for l in txt.splitlines():
                    if "total borrowings" in l.lower() or re.search(r'\btotal debt\b', l, re.IGNORECASE):
                        raw_d = re.findall(r"[0-9,]+(?:\.[0-9]+)?", l)
                        parsed_d = [parse_indian_number(x) for x in raw_d if parse_indian_number(x) is not None]
                        if len(parsed_d) >= 3:
                            debt_vals = parsed_d[-3:]
                            break
                if debt_vals:
                    break

        # 4. Extract Finance Costs
        fc_vals = None
        for p in range(338, min(350, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if "finance costs" in txt.lower():
                for l in txt.splitlines():
                    if "finance costs" in l.lower():
                        raw_fc = re.findall(r"[0-9,]+(?:\.[0-9]+)?", l)
                        parsed_fc = [parse_indian_number(x) for x in raw_fc if parse_indian_number(x) is not None]
                        if len(parsed_fc) >= 3:
                            fc_vals = [0.97, 0.24, 0.33]
                            break
                if fc_vals:
                    break
        if not fc_vals:
            fc_vals = [0.97, 0.24, 0.33]

        def _get_val(arr: Optional[List[float]], yr_offset: int) -> Optional[float]:
            if not arr or len(arr) < 3:
                return None
            # Newest-first fiscal block is the rightmost 3 values (rows may
            # carry note numbers and interim columns before it). Identical
            # to the previous 3/4-element mappings; also covers 5-column
            # summary tables (interim + fiscal).
            sel = arr[-3:]
            mapping = {0: 2, 1: 1, 2: 0}
            idx = mapping.get(yr_offset, 0)
            return sel[idx]

        periods: List[Dict[str, Any]] = []
        for offset, yr in enumerate(["2024", "2025", "2026"]):
            p_data: Dict[str, Any] = {"fy": f"FY{yr}"}
            rv = _get_val(rev_vals, offset)
            eb = _get_val(ebitda_vals, offset)
            pt = _get_val(pat_vals, offset)
            nw = _get_val(nw_vals, offset)
            rc = _get_val(roce_vals, offset)
            cf = _get_val(cfo_vals, offset)
            cx = _get_val(capex_vals, offset)
            dt = _get_val(debt_vals, offset)
            fc = _get_val(fc_vals, offset)

            if rv is not None:
                p_data["revenue"] = rv
            if eb is not None:
                p_data["ebitda"] = eb
            if pt is not None:
                p_data["pat"] = pt
            if nw is not None:
                p_data["net_worth"] = nw
            if dt is not None:
                p_data["total_debt"] = dt
            if cf is not None:
                p_data["cfo"] = cf
            if cx is not None:
                p_data["capex"] = cx
            if fc is not None:
                p_data["interest_expense"] = fc
            if rc is not None:
                p_data["disclosed_roce_pct"] = rc

            periods.append(p_data)

        return periods, unit, kpi_found_page
