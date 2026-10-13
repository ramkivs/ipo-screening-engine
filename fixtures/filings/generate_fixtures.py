"""Generates representative SEBI ICDR compliant PDF filings for Phase 5B validation.

Classes generated:
  - Class A: Financial Institution (Apex Housing Finance Limited)
  - Class B: Cyclical / Manufacturing (Zenith Heavy Forgings Limited - 5 Full FYs)
  - Class C: EPC / Infrastructure (Garuda Infra Projects Limited)
  - Class D: Loss-Making Growth Tech (QuickDeliver Network Limited)
  - Class E: Modern / Complex RHP (Nexus Retail Brands Limited)
"""

from __future__ import annotations

from pathlib import Path
from typing import List


def create_pdf(pages_text: List[str]) -> bytes:
    """Build a deterministic PDF 1.4 document containing the given pages."""
    catalog_id = 1
    pages_id = 2
    font_id = 3
    font_obj = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    page_ids = []
    page_objs = []
    stream_objs = []

    for i, ptext in enumerate(pages_text):
        p_id = 4 + i * 2
        s_id = 5 + i * 2
        page_ids.append(p_id)

        stream_content = "BT /F1 9 Tf 40 760 Td 12 TL\n"
        for line in ptext.split("\n"):
            line_esc = (
                line.replace("\\", "\\\\")
                .replace("(", "\\(")
                .replace(")", "\\)")
            )
            stream_content += f"({line_esc}) ' \n"
        stream_content += "ET"

        stream_bytes = stream_content.encode("utf-8")
        s_obj = f"<< /Length {len(stream_bytes)} >>\nstream\n{stream_content}\nendstream"
        p_obj = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
            f"/Contents {s_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
        )
        page_objs.append((p_id, p_obj))
        stream_objs.append((s_id, s_obj))

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    pages_obj = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    catalog_obj = f"<< /Type /Catalog /Pages {pages_id} 0 R >>"

    all_objs = {
        catalog_id: catalog_obj,
        pages_id: pages_obj,
        font_id: font_obj,
    }
    for pid, pobj in page_objs:
        all_objs[pid] = pobj
    for sid, sobj in stream_objs:
        all_objs[sid] = sobj

    pdf_out = "%PDF-1.4\n"
    offsets = {}
    for oid in sorted(all_objs.keys()):
        offsets[oid] = len(pdf_out.encode("utf-8"))
        pdf_out += f"{oid} 0 obj\n{all_objs[oid]}\nendobj\n"

    xref_offset = len(pdf_out.encode("utf-8"))
    pdf_out += f"xref\n0 {len(all_objs) + 1}\n0000000000 65535 f \n"
    for oid in sorted(all_objs.keys()):
        pdf_out += f"{offsets[oid]:010d} 00000 n \n"
    pdf_out += (
        f"trailer\n<< /Size {len(all_objs) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    return pdf_out.encode("utf-8")


def generate_class_a_financial() -> bytes:
    """Class A: Financial Institution / Lender filing."""
    pages = [
        # Page 1: Cover
        """RED HERRING PROSPECTUS
APEX HOUSING FINANCE LIMITED
(Our Company was incorporated as Apex Housing Finance Private Limited under Companies Act, 1956)
CIN: U65922MH2010PLC204561
INITIAL PUBLIC OFFER OF UP TO [●] EQUITY SHARES OF FACE VALUE OF ₹ 10 EACH
FRESH ISSUE OF UP TO [●] EQUITY SHARES AGGREGATING UP TO ₹ 60,000.00 LAKHS BY OUR COMPANY (THE "FRESH ISSUE")
OFFER FOR SALE OF UP TO [●] EQUITY SHARES AGGREGATING UP TO ₹ 25,000.00 LAKHS BY THE SELLING SHAREHOLDER
BOOK RUNNING LEAD MANAGERS: ICICI Securities Limited, Axis Capital Limited
REGISTRAR TO THE OFFER: KFin Technologies Limited""",

        # Page 2: TOC
        """TABLE OF CONTENTS
SECTION I - GENERAL
THE OFFER .... 3
SECTION II - CAPITAL STRUCTURE
CAPITAL STRUCTURE .... 4
SECTION III - PARTICULARS OF THE OFFER
OBJECTS OF THE OFFER .... 5
SECTION IV - ABOUT OUR COMPANY
OUR MANAGEMENT .... 6
SECTION V - FINANCIAL INFORMATION
RESTATED FINANCIAL STATEMENTS .... 7
SECTION VI - LEGAL INFORMATION
OUTSTANDING LITIGATION .... 11""",

        # Page 3: The Offer & Offer Structure
        """THE OFFER
The Offer comprises a Fresh Issue of Equity Shares aggregating up to ₹ 60,000.00 lakhs and an Offer for Sale of Equity Shares aggregating up to ₹ 25,000.00 lakhs.
OFFER STRUCTURE
In accordance with Regulation 6(1) of the SEBI ICDR Regulations:
QIB Allocation: Not less than 50% of the Offer shall be available for allocation to QIBs.
Retail Allocation: Not less than 35% of the Offer shall be available for allocation to Retail Individual Bidders.
Non-Institutional Bidders (NII): Not more than 15% of the Offer shall be available for allocation to NIIs.""",

        # Page 4: Capital Structure
        """CAPITAL STRUCTURE
Shareholding of our Promoters and Promoter Group
Set forth below is the shareholding of our Promoters and members of the Promoter Group as on the date of this Red Herring Prospectus:
Shareholder Pre-Offer Shares Pre-Offer (%) Post-Offer Shares Post-Offer (%)
A. Promoters
Apex Holdings Private Limited 4,20,00,000 56.00 [●] [●]
B. Promoter Group
Apex Trusteeship Limited 93,75,000 12.50 [●] [●]
Total 5,13,75,000 68.50 [●] [●]
Promoter Lock-in: An aggregate of 20% of the post-Offer Equity Share capital held by our Promoters shall be locked in for a period of 18 months from the date of Allotment.
None of the Equity Shares held by our Promoters are pledged as of the date of this Red Herring Prospectus.""",

        # Page 5: Objects of the Offer
        """OBJECTS OF THE OFFER
The Net Proceeds from the Fresh Issue will be utilised towards the following objects:
Schedule of Implementation and Deployment
(Amount In ₹ lakhs)
Particulars Total estimated cost Amount to be funded from Net Proceeds
(A) Augmentation of Tier-I Capital base to meet future capital requirements 52,000.00 52,000.00
Sub-total (A) 52,000.00 52,000.00
General Corporate Purposes* [●] [●]
Total [●] [●]
* The amount utilised for general corporate purposes shall not exceed 25% of the Fresh Offer.""",

        # Page 6: Our Management
        """OUR MANAGEMENT
Board of Directors
As of the date of this Red Herring Prospectus, our Board comprises 8 Directors, of which 1 is Managing Director, 1 is Whole-Time Director, 2 are Non-Executive Directors, and 4 are Independent Directors.
Our Company is in compliance with the corporate governance norms prescribed under SEBI Listing Regulations.""",

        # Page 7: Restated Statement of Profit and Loss
        """Apex Housing Finance Limited
Restated Statement of Profit and Loss
Annexure II
(Amount in Lakhs, unless otherwise stated)
Particulars Notes For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024
Revenue from operations 22 42,500.00 36,200.00 29,800.00
Other income 23 450.00 380.00 310.00
Total Income (I) 42,950.00 36,580.00 30,110.00
Expenses
Finance costs (interest expended) 24 23,800.00 20,900.00 17,500.00
Employee benefits expenses 25 3,200.00 2,750.00 2,200.00
Depreciation and amortization 26 480.00 420.00 360.00
Provisions and contingencies 27 5,100.00 4,800.00 4,400.00
Other expenses 28 1,120.00 950.00 810.00
Total Expenses (II) 33,700.00 29,820.00 25,270.00
Profit before tax (I - II) 9,250.00 6,760.00 4,840.00
Tax expense 2,450.00 1,760.00 1,240.00
Profit after tax 6,800.00 5,000.00 3,600.00""",

        # Page 8: Restated Statement of Assets and Liabilities
        """Apex Housing Finance Limited
Restated Statement of Assets and Liabilities
Annexure I
(Amount in Lakhs, unless otherwise stated)
Particulars Notes As at 31 March 2026 As at 31 March 2025 As at 31 March 2024
ASSETS
Financial Assets
Cash and cash equivalents 11 1,250.00 980.00 850.00
Loans and advances 12 3,25,000.00 2,65,000.00 2,05,000.00
Investments 13 15,200.00 11,400.00 9,100.00
Other financial assets 14 3,550.00 2,620.00 5,050.00
Total Assets 3,45,000.00 2,80,000.00 2,20,000.00
EQUITY AND LIABILITIES
Equity share capital 18 7,500.00 7,500.00 7,500.00
Other equity 19 44,500.00 33,500.00 24,500.00
Total Equity (D) 52,000.00 41,000.00 32,000.00
Liabilities
Borrowings (Debt Securities) 20 1,20,000.00 95,000.00 75,000.00
Borrowings (other than Debt) 21 1,60,000.00 1,30,000.00 1,00,000.00
Total Borrowings 2,80,000.00 2,25,000.00 1,75,000.00
Total Liabilities 2,93,000.00 2,39,000.00 1,88,000.00""",

        # Page 9: Restated Statement of Cash Flows
        """Apex Housing Finance Limited
Restated Statement of Cash flows
Annexure III
(Amount in Lakhs, unless otherwise stated)
Particulars For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024
Net cash provided by/(used in) operating activities 4,500.00 3,800.00 2,900.00
Purchase of Property, Plant and Equipment (150.00) (120.00) (95.00)
Net cash from/(used in) financing activities 5,000.00 4,200.00 3,100.00""",

        # Page 10: KPIs (CRAR, NIM, GNPA)
        """Key Performance Indicators
Return on Capital Employed (%)(9) 16.80 15.20 13.90
CRAR (%) 20.10 19.20 18.40
Gross NPA (%) 2.40 3.10 4.20
Net NPA (%) 1.10 1.50 2.10
Net Interest Margin (%) 3.70 3.45 3.10
Cost to Income Ratio (%) 46.50 49.00 52.00""",

        # Page 11: Outstanding Litigation
        """OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS
Except as stated below, there are no outstanding criminal proceedings or material civil litigation involving our Company, Directors or Promoters.
Actions by statutory or regulatory authorities:
As on the date of this Red Herring Prospectus, there are no outstanding disciplinary actions or penalties imposed by SEBI or the RBI or Stock Exchanges against our Company, Directors or Promoters.""",
    ]
    return create_pdf(pages)


def generate_class_b_cyclical() -> bytes:
    """Class B: Cyclical / Manufacturing filing with 5 Full FYs."""
    pages = [
        # Page 1: Cover
        """RED HERRING PROSPECTUS
ZENITH HEAVY FORGINGS LIMITED
CIN: U28910GJ2005PLC045981
INITIAL PUBLIC OFFER OF UP TO [●] EQUITY SHARES OF FACE VALUE OF ₹ 10 EACH
FRESH ISSUE OF UP TO [●] EQUITY SHARES AGGREGATING UP TO ₹ 35,000.00 LAKHS BY OUR COMPANY
OFFER FOR SALE OF UP TO 40,00,000 EQUITY SHARES AGGREGATING UP TO ₹ [●] LAKHS
BOOK RUNNING LEAD MANAGERS: SBI Capital Markets Limited""",

        # Page 2: TOC
        """TABLE OF CONTENTS
THE OFFER .... 3
CAPITAL STRUCTURE .... 4
OBJECTS OF THE OFFER .... 5
OUR MANAGEMENT .... 6
RESTATED FINANCIAL STATEMENTS .... 7
OUTSTANDING LITIGATION .... 10""",

        # Page 3: The Offer
        """THE OFFER
Fresh Offer: Aggregating up to ₹ 35,000.00 lakhs
Offer for Sale: Up to 40,00,000 Equity Shares
Offer Structure: QIB 50%, Retail 35%, NII 15%""",

        # Page 4: Capital Structure
        """CAPITAL STRUCTURE
Shareholding of our Promoters and Promoter Group
Total Promoter and Promoter Group shareholding:
Total 3,25,00,000 65.00 [●] [●]
None of the Equity Shares held by our Promoters are pledged.
Promoter contribution locked in for 18 months.""",

        # Page 5: Objects of the Offer
        """OBJECTS OF THE OFFER
Schedule of Implementation and Deployment
(Amount In ₹ lakhs)
(A) Funding Capital Expenditure for expansion of forging facility 24,000.00 24,000.00
(B) Prepayment or repayment of all or a portion of certain outstanding borrowings 6,000.00 6,000.00
Sub-total (A+B) 30,000.00 30,000.00
General Corporate Purposes* [●] [●]
Total [●] [●]
* The amount utilised for general corporate purposes shall not exceed 25% of the Fresh Offer.""",

        # Page 6: Our Management
        """OUR MANAGEMENT
Board of Directors: 8 Directors total, 4 Independent Directors.""",

        # Page 7: 5-Year P&L
        """Zenith Heavy Forgings Limited
Restated Statement of Profit and Loss
Annexure II
(Amount in Lakhs, unless otherwise stated)
Particulars Notes For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024 For the year ended 31 March 2023 For the year ended 31 March 2022
Revenue from operations 21 48,000.00 42,000.00 35,000.00 28,000.00 22,000.00
Total Income 48,600.00 42,500.00 35,400.00 28,300.00 22,250.00
Cost of Material Consumed 22 22,500.00 20,100.00 17,200.00 14,000.00 11,200.00
Finance costs 23 2,100.00 2,050.00 1,950.00 1,800.00 1,650.00
Depreciation and amortization 24 1,850.00 1,650.00 1,450.00 1,250.00 1,050.00
Total Expenses 42,200.00 37,200.00 31,500.00 25,600.00 20,400.00
Profit before tax 6,400.00 5,300.00 3,900.00 2,700.00 1,850.00
Profit after tax 4,800.00 3,950.00 2,900.00 2,000.00 1,350.00""",

        # Page 8: 5-Year Balance Sheet
        """Zenith Heavy Forgings Limited
Restated Statement of Assets and Liabilities
Annexure I
(Amount in Lakhs, unless otherwise stated)
Particulars Notes As at 31 March 2026 As at 31 March 2025 As at 31 March 2024 As at 31 March 2023 As at 31 March 2022
Trade receivables 12 7,800.00 6,900.00 5,800.00 4,700.00 3,800.00
Cash and cash equivalents 13 450.00 380.00 310.00 250.00 190.00
Total Equity (D) 24,500.00 19,700.00 15,750.00 12,850.00 10,850.00
- Borrowings 18 6,200.00 6,800.00 7,400.00 8,100.00 8,900.00
- Borrowings 19 5,400.00 5,100.00 4,800.00 4,200.00 3,700.00""",

        # Page 9: 5-Year Cash Flow
        """Zenith Heavy Forgings Limited
Restated Statement of Cash flows
Annexure III
(Amount in Lakhs, unless otherwise stated)
Particulars For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024 For the year ended 31 March 2023 For the year ended 31 March 2022
Net cash provided by/(used in) operating activities 5,600.00 4,800.00 3,700.00 2,600.00 1,800.00
Purchase of Property, Plant and Equipment (3,200.00) (2,800.00) (2,400.00) (1,900.00) (1,500.00)""",

        # Page 10: Outstanding Litigation
        """OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS
None of our Promoters, Directors, or Group Companies are involved in any material litigation or criminal cases.""",
    ]
    return create_pdf(pages)


def generate_class_c_epc() -> bytes:
    """Class C: EPC / Infrastructure filing with Order Book."""
    pages = [
        # Page 1: Cover
        """RED HERRING PROSPECTUS
GARUDA INFRA PROJECTS LIMITED
CIN: U45200DL2008PLC174829
INITIAL PUBLIC OFFER OF UP TO [●] EQUITY SHARES OF FACE VALUE OF ₹ 10 EACH
FRESH ISSUE OF UP TO [●] EQUITY SHARES AGGREGATING UP TO ₹ 28,000.00 LAKHS BY OUR COMPANY
OFFER FOR SALE OF UP TO 25,00,000 EQUITY SHARES AGGREGATING UP TO ₹ [●] LAKHS
BOOK RUNNING LEAD MANAGERS: Kotak Mahindra Capital Company Limited""",

        # Page 2: TOC
        """TABLE OF CONTENTS
THE OFFER .... 3
CAPITAL STRUCTURE .... 4
OBJECTS OF THE OFFER .... 5
OUR BUSINESS .... 6
RESTATED FINANCIAL STATEMENTS .... 7
OUTSTANDING LITIGATION .... 10""",

        # Page 3: The Offer
        """THE OFFER
Fresh Offer: Aggregating up to ₹ 28,00,0.00 lakhs
Offer Structure: QIB 50%, Retail 35%, NII 15%""",

        # Page 4: Capital Structure
        """CAPITAL STRUCTURE
Shareholding of our Promoters and Promoter Group
Total 2,80,00,000 70.00 [●] [●]
Promoter shares pledge: None of the Equity Shares held by our Promoters are pledged.
Promoter lock-in for 18 months in place.""",

        # Page 5: Objects of the Offer
        """OBJECTS OF THE OFFER
Schedule of Implementation and Deployment
(Amount In ₹ lakhs)
(A) Funding working capital requirements 18,000.00 18,000.00
(B) Repayment of certain borrowings 5,000.00 5,000.00
General Corporate Purposes* [●] [●]
Total [●] [●]
* Shall not exceed 25% of the Fresh Offer.""",

        # Page 6: Our Business / Order Book
        """OUR BUSINESS
Order Book and Project Execution Capabilities
As of March 31, 2026, our confirmed order book stood at ₹ 1,45,000.00 lakhs, providing strong revenue visibility over the next 30 months.
Top 5 customers accounted for 64.20% of our revenue from operations in Fiscal 2026.""",

        # Page 7: P&L
        """Garuda Infra Projects Limited
Restated Statement of Profit and Loss
Annexure II
(Amount in Lakhs, unless otherwise stated)
Particulars Notes For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024
Revenue from operations 25 54,200.00 46,500.00 38,100.00
Total Income 54,800.00 47,100.00 38,600.00
Subcontracting and civil construction charges 26 28,400.00 24,800.00 20,500.00
Finance costs 27 2,450.00 2,150.00 1,920.00
Depreciation and amortization 28 1,120.00 980.00 840.00
Total Expenses 49,800.00 43,100.00 35,600.00
Profit before tax 5,000.00 4,000.00 3,000.00
Profit after tax 3,750.00 2,980.00 2,240.00""",

        # Page 8: Balance Sheet
        """Garuda Infra Projects Limited
Restated Statement of Assets and Liabilities
Annexure I
(Amount in Lakhs, unless otherwise stated)
Particulars Notes As at 31 March 2026 As at 31 March 2025 As at 31 March 2024
Trade receivables 14 12,400.00 10,800.00 9,100.00
Cash and cash equivalents 15 620.00 480.00 390.00
Total Equity (D) 21,500.00 17,750.00 14,770.00
- Borrowings 20 8,500.00 7,900.00 7,200.00
- Borrowings 21 6,800.00 6,100.00 5,400.00""",

        # Page 9: Cash Flow
        """Garuda Infra Projects Limited
Restated Statement of Cash flows
Annexure III
(Amount in Lakhs, unless otherwise stated)
Particulars For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024
Net cash provided by/(used in) operating activities 4,100.00 3,300.00 2,600.00
Purchase of Property, Plant and Equipment (1,850.00) (1,600.00) (1,250.00)""",

        # Page 10: Outstanding Litigation
        """OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS
Our Company and Promoters have no pending criminal actions or disciplinary proceedings by SEBI or Stock Exchanges.""",
    ]
    return create_pdf(pages)


def generate_class_d_loss_making() -> bytes:
    """Class D: Loss-Making Growth Tech filing."""
    pages = [
        # Page 1: Cover
        """RED HERRING PROSPECTUS
QUICKDELIVER NETWORK LIMITED
CIN: U72900KA2016PLC092147
INITIAL PUBLIC OFFER OF UP TO [●] EQUITY SHARES OF FACE VALUE OF ₹ 1 EACH
FRESH ISSUE OF UP TO [●] EQUITY SHARES AGGREGATING UP TO ₹ 45,000.00 LAKHS BY OUR COMPANY
OFFER FOR SALE OF UP TO 50,00,000 EQUITY SHARES AGGREGATING UP TO ₹ [●] LAKHS
BOOK RUNNING LEAD MANAGERS: Morgan Stanley India Company Private Limited""",

        # Page 2: TOC
        """TABLE OF CONTENTS
THE OFFER .... 3
CAPITAL STRUCTURE .... 4
OBJECTS OF THE OFFER .... 5
OUR MANAGEMENT .... 6
RESTATED FINANCIAL STATEMENTS .... 7
OUTSTANDING LITIGATION .... 10""",

        # Page 3: The Offer
        """THE OFFER
Fresh Offer: Aggregating up to ₹ 45,000.00 lakhs
Offer Structure: Under Regulation 6(2) QIB 75%, Retail 10%, NII 15%""",

        # Page 4: Capital Structure
        """CAPITAL STRUCTURE
Shareholding of our Promoters and Promoter Group
Total 1,80,00,000 48.50 [●] [●]
None of the Equity Shares held by our Promoters are pledged.
Promoter lock-in for 18 months in place.""",

        # Page 5: Objects of the Offer
        """OBJECTS OF THE OFFER
Schedule of Implementation and Deployment
(Amount In ₹ lakhs)
(A) Funding technology infrastructure and dark store expansion 30,000.00 30,000.00
(B) Funding customer acquisition and brand marketing 6,000.00 6,000.00
General Corporate Purposes* [●] [●]
Total [●] [●]
* Shall not exceed 25% of the Fresh Offer.""",

        # Page 6: Our Management
        """OUR MANAGEMENT
Board comprises 8 Directors with 4 Independent Directors.""",

        # Page 7: P&L (Loss-making: negative PAT)
        """QuickDeliver Network Limited
Restated Statement of Profit and Loss
Annexure II
(Amount in Lakhs, unless otherwise stated)
Particulars Notes For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024
Revenue from operations 22 18,500.00 12,400.00 6,800.00
Total Income 18,900.00 12,650.00 6,950.00
Delivery logistics costs 23 9,400.00 6,800.00 4,100.00
Employee benefits expenses 24 6,200.00 4,900.00 3,400.00
Finance costs 25 350.00 280.00 190.00
Depreciation and amortization 26 840.00 620.00 410.00
Advertising and marketing 27 3,400.00 3,100.00 2,600.00
Total Expenses 21,200.00 16,500.00 11,200.00
Profit/(Loss) before tax (2,300.00) (3,850.00) (4,250.00)
Profit after tax (2,300.00) (3,850.00) (4,250.00)""",

        # Page 8: Balance Sheet
        """QuickDeliver Network Limited
Restated Statement of Assets and Liabilities
Annexure I
(Amount in Lakhs, unless otherwise stated)
Particulars Notes As at 31 March 2026 As at 31 March 2025 As at 31 March 2024
Trade receivables 12 1,450.00 980.00 520.00
Cash and cash equivalents 13 8,400.00 4,200.00 2,100.00
Total Equity (D) 14,200.00 6,500.00 3,100.00
- Borrowings 18 1,200.00 1,500.00 1,800.00
- Borrowings 19 800.00 700.00 600.00""",

        # Page 9: Cash Flow
        """QuickDeliver Network Limited
Restated Statement of Cash flows
Annexure III
(Amount in Lakhs, unless otherwise stated)
Particulars For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024
Net cash provided by/(used in) operating activities (1,650.00) (2,900.00) (3,400.00)
Purchase of Property, Plant and Equipment (1,200.00) (950.00) (650.00)""",

        # Page 10: Outstanding Litigation
        """OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS
No criminal or active regulatory proceedings against our Company or Promoters.""",
    ]
    return create_pdf(pages)


def generate_class_e_modern() -> bytes:
    """Class E: Modern Complex Filing with multi-page table and irregular formatting."""
    pages = [
        # Page 1: Cover
        """RED HERRING PROSPECTUS
NEXUS RETAIL BRANDS LIMITED
CIN: U52100MH2018PLC312894
INITIAL PUBLIC OFFER OF UP TO [●] EQUITY SHARES OF FACE VALUE OF ₹ 2 EACH
FRESH ISSUE OF UP TO [●] EQUITY SHARES AGGREGATING UP TO ₹ 22,500.00 LAKHS BY OUR COMPANY
OFFER FOR SALE OF UP TO 30,00,000 EQUITY SHARES AGGREGATING UP TO ₹ [●] LAKHS
BOOK RUNNING LEAD MANAGERS: JM Financial Limited""",

        # Page 2: TOC
        """TABLE OF CONTENTS
THE OFFER .... 3
CAPITAL STRUCTURE .... 4
OBJECTS OF THE OFFER .... 5
RESTATED FINANCIAL STATEMENTS .... 6
OUTSTANDING LITIGATION .... 9""",

        # Page 3: The Offer
        """THE OFFER
Fresh Offer: Aggregating up to ₹ 22,500.00 lakhs
Offer Structure: QIB 50%, Retail 35%, NII 15%""",

        # Page 4: Capital Structure
        """CAPITAL STRUCTURE
Shareholding of our Promoters and Promoter Group
Total 2,40,00,000 60.00 [●] [●]
None of the Equity Shares held by our Promoters are pledged.
Promoter lock-in for 18 months in place.""",

        # Page 5: Objects of the Offer
        """OBJECTS OF THE OFFER
Schedule of Implementation and Deployment
(Amount In ₹ lakhs)
(A) Setting up new retail stores across India 14,000.00 14,000.00
(B) Repayment of certain term borrowings 3,500.00 3,500.00
General Corporate Purposes* [●] [●]
Total [●] [●]
* In compliance with SEBI ICDR Regulations, GCP shall not exceed 25% of the Fresh Offer.""",

        # Page 6: P&L
        """Nexus Retail Brands Limited
Restated Statement of Profit and Loss
Annexure II
(Amount in Lakhs, unless otherwise stated)
Particulars Notes For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024
Revenue from operations 24 38,400.00 29,800.00 21,500.00
Total Income 38,750.00 30,100.00 21,700.00
Cost of Material Consumed 25 16,500.00 13,200.00 9,800.00
Finance costs 26 1,250.00 1,100.00 950.00
Depreciation and amortization 27 1,650.00 1,350.00 1,050.00
Total Expenses 34,200.00 26,800.00 19,500.00
Profit before tax 4,550.00 3,300.00 2,200.00
Profit after tax 3,400.00 2,450.00 1,620.00""",

        # Page 7: Balance Sheet
        """Nexus Retail Brands Limited
Restated Statement of Assets and Liabilities
Annexure I
(Amount in Lakhs, unless otherwise stated)
Particulars Notes As at 31 March 2026 As at 31 March 2025 As at 31 March 2024
Trade receivables 15 3,200.00 2,500.00 1,800.00
Cash and cash equivalents 16 1,150.00 820.00 540.00
Total Equity (D) 15,800.00 12,400.00 9,950.00
- Borrowings 20 4,200.00 4,600.00 4,900.00
- Borrowings 21 2,800.00 2,500.00 2,200.00""",

        # Page 8: Cash Flow
        """Nexus Retail Brands Limited
Restated Statement of Cash flows
Annexure III
(Amount in Lakhs, unless otherwise stated)
Particulars For the year ended 31 March 2026 For the year ended 31 March 2025 For the year ended 31 March 2024
Net cash provided by/(used in) operating activities 3,900.00 2,950.00 2,100.00
Purchase of Property, Plant and Equipment (2,100.00) (1,750.00) (1,400.00)""",

        # Page 9: Outstanding Litigation
        """OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS
Our Company and Promoters have no pending criminal proceedings or SEBI/Stock Exchange regulatory actions.""",
    ]
    return create_pdf(pages)


def main() -> None:
    fixtures_dir = Path("fixtures/filings")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    fixtures = [
        ("class_a_financial_lender.pdf", generate_class_a_financial()),
        ("class_b_cyclical_manufacturing.pdf", generate_class_b_cyclical()),
        ("class_c_epc_infrastructure.pdf", generate_class_c_epc()),
        ("class_d_loss_making_tech.pdf", generate_class_d_loss_making()),
        ("class_e_modern_complex_rhp.pdf", generate_class_e_modern()),
    ]

    for fname, data in fixtures:
        fpath = fixtures_dir / fname
        fpath.write_bytes(data)
        print(f"Generated {fpath} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
