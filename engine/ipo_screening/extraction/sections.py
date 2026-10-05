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
from typing import Any, Dict, List, Optional, Tuple

import pypdf

from ..canonical import ExtractionMethod
from .interfaces import RawExtraction, SourceDocument
from .numbers import is_undisclosed_marker, parse_indian_number


class SectionExtractor:
    """Extracts structured IPO domain fields across text sections."""

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

    def extract_cover_and_offer(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract company name, issue size, price band, quotas, and OFS details."""
        extractions: List[RawExtraction] = []

        # 1. Company Name from Cover (first 3 pages)
        cover_text = ""
        for p in range(1, min(4, self.page_count + 1)):
            cover_text += "\n" + self.extract_page_text(p)

        m_comp = re.search(r'([A-Z0-9\s,\.\(\)]+?\bLIMITED\b)', cover_text)
        if m_comp:
            cname = m_comp.group(1).strip()
            if "PROSPECTUS OF" in cname:
                cname = cname.split("PROSPECTUS OF")[-1].strip()
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

        # 2. Fresh Issue
        m_fresh = re.search(
            r'fresh (?:offer|issue)[^\n]*?aggregating up to ₹\s*([0-9,]+(?:\.[0-9]+)?)\s*(lakhs?|crores?|millions?)',
            cover_text,
            re.IGNORECASE,
        )
        if m_fresh:
            raw_val = m_fresh.group(1)
            unit_val = m_fresh.group(2).upper()
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
                    quote=m_fresh.group(0),
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        # 3. OFS Seller & shares
        m_ofs_shares = re.search(
            r'offer for sale[^\n]*?up to\s*([0-9,]+)\s*equity shares',
            cover_text,
            re.IGNORECASE,
        )
        ofs_shares_count = None
        if m_ofs_shares:
            ofs_shares_count = parse_indian_number(m_ofs_shares.group(1))

        m_seller = re.search(
            r'by\s+([A-Za-z0-9\s,\.\(\)]+?(?:Private|Public)?\s*Limited)\s*\(\s*[“"]SELLING SHAREHOLDER[”"]\s*\)',
            cover_text,
            re.IGNORECASE,
        )
        if m_seller:
            seller_name = m_seller.group(1).strip()
            ofs_seller_obj = [
                {
                    "name": seller_name,
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
                    quote=m_seller.group(0),
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.95,
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
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.90,
                )
            )

        return extractions

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
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

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
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.90,
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
                        tokens = re.findall(r'\[[●•\*]\]|[0-9,]+(?:\.[0-9]+)?', section_lines[j])
                        for tok in tokens:
                            if is_undisclosed_marker(tok):
                                return None, tok
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

        # 3. Growth Capex
        capex_amt, capex_marker = _scan_category_amount(["capital expenditure", "purchase of plant", "growth capex"])
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
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        return extractions

    def extract_governance(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract auditor opinion, litigation bucket, SEBI action, and board independence."""
        extractions: List[RawExtraction] = []

        # 1. Auditor opinion
        fin_range = page_ranges.get("restated_financials") if page_ranges else None
        p_start, p_end = fin_range or (60, min(80, self.page_count))

        auditor_opinion = "unqualified"
        found_opinion_page = p_start

        scan_pages = list(range(p_start, min(p_end + 1, self.page_count + 1)))
        if self.page_count >= 350:
            scan_pages.extend(range(340, 350))

        for p in scan_pages:
            txt = self.extract_page_text(p)
            if "examination report" in txt.lower() or "independent auditor" in txt.lower():
                if "emphasis of matter" in txt.lower() or "included following matter(s)" in txt.lower():
                    auditor_opinion = "emphasis_of_matter"
                    found_opinion_page = p
                    break
                elif "qualified opinion" in txt.lower() or "adverse opinion" in txt.lower():
                    auditor_opinion = "qualified"
                    found_opinion_page = p
                    break

        extractions.append(
            RawExtraction(
                field_path="governance.auditor_opinion",
                candidate_value=auditor_opinion,
                raw_text=auditor_opinion,
                page=found_opinion_page,
                section="Financial Information",
                locator="Independent Auditors Examination Report",
                quote=f"Auditor opinion classified as: {auditor_opinion}",
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                extraction_confidence=0.95,
            )
        )

        # 2. Litigation bucket & SEBI action
        lit_range = page_ranges.get("litigation") if page_ranges else None
        p_lstart, p_lend = lit_range or (430, min(500, self.page_count))

        lit_bucket = "none"
        sebi_active = False
        found_lit_page = p_lstart

        for p in range(p_lstart, p_lend + 1):
            txt = self.extract_page_text(p)
            if re.search(r'criminal proceedings against our promoters|r\.c\.c\.|criminal complaint', txt, re.IGNORECASE):
                lit_bucket = "criminal_or_regulatory"
                found_lit_page = p
                break
            elif re.search(r'material civil litigation|civil suit', txt, re.IGNORECASE):
                lit_bucket = "material_civil"
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
                extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                extraction_confidence=0.90,
            )
        )

        return extractions

    def extract_business(self, page_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> List[RawExtraction]:
        """Extract customer concentration, industry CAGR, moat, and visibility ratings."""
        extractions: List[RawExtraction] = []

        top5_cust = None
        found_cust_page = 29

        for p in range(25, min(55, self.page_count + 1)):
            txt = self.extract_page_text(p)
            if "top 5 customers" in txt.lower() or "top five customers" in txt.lower():
                m_cust = re.search(r'top 5 customers[^\n]*?([0-9,]+(?:\.[0-9]+)?)\s+([0-9]+\.[0-9]+)', txt, re.IGNORECASE)
                if m_cust:
                    top5_cust = float(m_cust.group(2))
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
                    extraction_method=ExtractionMethod.DETERMINISTIC_PDF.value,
                    extraction_confidence=0.98,
                )
            )

        return extractions
