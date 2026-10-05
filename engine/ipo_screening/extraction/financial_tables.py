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

    def __init__(self, doc: SourceDocument, reader: pypdf.PdfReader) -> None:
        self.doc = doc
        self.reader = reader
        self.page_count = len(reader.pages)

    def extract_page_text(self, page_1_indexed: int) -> str:
        """Extract text from a 1-indexed page."""
        if 1 <= page_1_indexed <= self.page_count:
            try:
                return self.reader.pages[page_1_indexed - 1].extract_text() or ""
            except Exception:
                return ""
        return ""

    def extract_all(self, start_page: int = 1, end_page: Optional[int] = None) -> List[RawExtraction]:
        """Extract all financial fields and period metrics across financial pages."""
        extractions: List[RawExtraction] = []
        if end_page is None or end_page > self.page_count:
            end_page = self.page_count

        # 1. Locate P&L, BS, CF, KPI, Contingent Liabilities pages
        pl_page, pl_text = self._find_page(
            ["Restated Statement of Profit and Loss", "Statement of Profit and Loss"],
            start_page,
            end_page,
            required_content=["revenue from operations", "annexure ii"],
        )
        bs_page, bs_text = self._find_page(
            ["Restated Statement of Assets and Liabilities", "Statement of Assets and Liabilities"],
            start_page,
            end_page,
            required_content=["total equity", "annexure i"],
        )
        cf_page, cf_text = self._find_page(
            ["Restated Statement of Cash flows", "Statement of Cash flows"],
            start_page,
            end_page,
            required_content=["cash flow from operating activities", "annexure iii"],
        )
        kpi_page, kpi_text = self._find_page(["Return on Capital Employed", "Key Performance Indicators"], 50, min(end_page, 200))
        cl_page, cl_text = self._find_page(["Contingent Liabilities and Commitments", "Contingent Liabilities"], 300, end_page)

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
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                extraction_confidence=1.0 if (pl_page or bs_page) else 0.5,
            )
        )

        # Detect periods (e.g. 31 March 2026, 31 March 2025, 31 March 2024)
        years = self._extract_fiscal_years(pl_text or bs_text or "")
        if not years:
            years = ["2026", "2025", "2024"]

        # Parse P&L items
        pl_items = self._parse_table_lines(
            pl_text or "",
            [
                ("revenue", [r"revenue from operations"]),
                ("total_income", [r"total income\b"]),
                ("cost_of_materials", [r"cost of material consumed"]),
                ("employee_expenses", [r"employee benefits expenses", r"employee benefits"]),
                ("finance_costs", [r"finance costs", r"finance cost"]),
                ("depreciation", [r"depreciation and amortization"]),
                ("total_expenses", [r"total expenses\b"]),
                ("pbt", [r"profit/(loss) before tax", r"profit before tax"]),
                ("pat", [r"profit after tax", r"profit/(loss) for the year"]),
            ],
            len(years),
        )

        # Parse Balance Sheet items
        bs_items = self._parse_table_lines(
            bs_text or "",
            [
                ("trade_receivables", [r"trade receivables"]),
                ("cash_and_equivalents", [r"cash and cash equivalents"]),
                ("net_worth", [r"total equity\b", r"total equity \(d\)"]),
            ],
            len(years),
        )

        # Parse non-current and current borrowings
        borrowings_lines = self._extract_all_borrowings(bs_text or "", len(years))
        if len(borrowings_lines) >= 2:
            bs_items["borrowings_non_current"] = borrowings_lines[0]
            bs_items["borrowings_current"] = borrowings_lines[1]

        # Parse Cash Flow items
        cf_items = self._parse_table_lines(
            cf_text or "",
            [
                ("cfo", [r"net cash provided by/\(used in\) operating activities", r"net cash from operating activities"]),
                ("capex", [r"purchase of property,\s*plant and equipment", r"purchase of fixed assets"]),
            ],
            len(years),
        )

        # Parse KPI items (ROCE)
        roce_vals = self._parse_kpi_line(kpi_text or "", r"return on capital employed", len(years))

        # Parse Contingent liabilities
        cl_amount = self._parse_contingent_liabilities(cl_text or "")
        if cl_amount is not None:
            extractions.append(
                RawExtraction(
                    field_path="financials.contingent_liabilities",
                    candidate_value=cl_amount,
                    raw_text=str(cl_amount),
                    raw_unit=unit,
                    page=cl_page or 1,
                    section="Notes to Restated Financials",
                    locator="Contingent Liabilities and Commitments",
                    quote=f"Total Contingent Liabilities: {cl_amount}",
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
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
        matches = re.findall(r'31\s+March\s+(20[0-9]{2})', text, re.IGNORECASE)
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
                    if len(nums) == n_cols + 1:
                        nums = nums[1:]
                    if len(nums) >= n_cols:
                        results[field_name] = nums[:n_cols]

        return results

    def _extract_all_borrowings(self, text: str, n_cols: int) -> List[List[Optional[float]]]:
        rows: List[List[Optional[float]]] = []
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines:
            if re.search(r'-\s*borrowings\b', line, re.IGNORECASE):
                nums = self._extract_row_numbers(line)
                if len(nums) == n_cols + 1:
                    nums = nums[1:]
                if len(nums) >= n_cols:
                    rows.append(nums[:n_cols])
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
        for line in text.split("\n"):
            if re.search(pattern, line, re.IGNORECASE):
                nums = re.findall(r'[0-9]+\.[0-9]+', line)
                parsed = [float(x) for x in nums if float(x) < 200.0]
                if len(parsed) >= n_cols:
                    return parsed[:n_cols]
        return None

    def _parse_contingent_liabilities(self, text: str) -> Optional[float]:
        lines = text.split("\n")
        for line in lines:
            if re.search(r'Total', line, re.IGNORECASE) and re.search(r'[0-9,]+\.[0-9]+', line):
                nums = re.findall(r'[0-9,]+(?:\.[0-9]+)?', line)
                if nums:
                    return parse_indian_number(nums[0])
        return None
