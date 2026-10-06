# R.K. Fashion Accessories Data-Coverage Defect: Forensic Investigation & Pipeline Repair Report

**Target Filing:** R.K. Fashion Accessories Limited RHP (`handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`, 496 pages)  
**CIN:** U18109WB2010PLC144256  
**Reference Commit:** `e959e12` on branch `arena/01a10b42-ipo-screening-engine`  
**Engine Specification:** v1.5.0 (`schema/ipo-input.v1.5.schema.json`, `config/ipo-config.v1.5.0.json`)

---

## 1. Executive Summary & Reconciliation Impact

| Metric / Attribute | Baseline Evaluation (Before Repair) | Repaired Evaluation (After Pipeline Repair) | Net Reconciled Delta |
| :--- | :--- | :--- | :--- |
| **Final Score** | **20.0 / 100** | **59.0 / 100** (61.0 with segment CAGR) | **+39.0 to +41.0 pts** |
| **Available Points** | 30.0 points | 82.0 points | **+52.0 points** |
| **Unknown Points** | **70.0 points** | **18.0 points** (all genuinely external) | **-52.0 points** |
| **Completeness %** | 30.0% completeness | 82.0% completeness | **+52.0%** |
| **Confidence Level** | Low | **Medium** | Upgraded |
| **Verdict** | INSUFFICIENT_DATA | INSUFFICIENT_DATA (gated by unavail Module F) | Preserved |
| **Module A (Financial Quality)** | 0.0 / 0.0 (25 unknown pts) | **21.0 / 25.0 (0 unknown pts)** | **+21.0 pts (100% scored)** |
| **Module B (Valuation)** | 0.0 / 0.0 (16 unknown pts) | **10.0 / 16.0 (4 unknown pts)** | **+10.0 pts (real peer scored)** |
| **Module C (Offer Structure)** | 11.0 / 11.0 (4 unknown pts) | **11.0 / 11.0 (4 unknown pts)** | **100% available scored** |
| **Module D (Governance)** | 5.0 / 9.0 (6 unknown pts) | **11.0 / 15.0 (0 unknown pts)** | **+6.0 pts (100% scored)** |
| **Module E (Business/Moat)** | 4.0 / 10.0 (5 unknown pts) | **11.0 / 15.0 (0 unknown pts)** | **+7.0 pts (100% scored)** |
| **Module F (Market/Demand)** | 0.0 / 0.0 (10 unknown pts) | 0.0 / 0.0 (10 unknown pts) | Genuine external unknowns |

---

## 2. Root Cause Analysis of Information Loss

Through systematic execution profiling of `DocumentExtractor.extract_from_pdf` on the 496-page R.K. Fashion Accessories RHP, four distinct failure points were isolated across the pipeline:

### Failure Point 1: `TOCRouter` Failure on Alternative Heading (`CONTENTS`)
- **First Point of Loss:** `TOCRouter.from_pdf` in `engine/ipo_screening/extraction/toc.py`.
- **Mechanism:** The TOC discovery regex looked strictly for `\bTABLE\s+OF\s+CONTENTS\b` or `\bINDEX\b`. In the R.K. Fashion RHP, PDF page 4 is titled solely `"CONTENTS"`. Consequently, TOC routing failed silently, producing 0 page routing ranges.
- **Consequence:** Downstream section extractors fell back to generic unrouted page scanning windows, missing targeted sections across the 496-page filing.
- **Repair:** Enhanced TOC discovery in `TOCRouter.from_pdf` to match `^\s*CONTENTS\s*$` alongside existing TOC headers, and expanded canonical section regexes for `the_offer`, `basis_for_offer_price`, `promoters`, `restated_financials`, and `financial_indebtedness`.

### Failure Point 2: Scanned Annexures & Missing Fallback in `FinancialTableExtractor`
- **First Point of Loss:** `FinancialTableExtractor._find_page` in `engine/ipo_screening/extraction/financial_tables.py`.
- **Mechanism:** In the R.K. Fashion RHP, the Restated Financial Statement annexures (Annexure I Assets & Liabilities, Annexure II Profit & Loss, Annexure III Cash Flows) on PDF pages 294–318 were scanned raster images without an embedded text layer (`len(extract_text()) < 30`).
- **Consequence:** The extractor could not extract rows from scanned annexures, resulting in 0 financial periods and causing all 5 Module A criteria (Revenue CAGR, Margin Trend, ROCE, CFO Quality, Leverage) to report UNKNOWN (25 unknown points).
- **Repair:** Implemented `_extract_from_kpi_and_summary_tables` fallback in `FinancialTableExtractor`. When restated statement annexures lack text, the engine automatically extracts multi-period Revenue, EBITDA, PAT, Net Worth, ROCE, and ROE from the ICDR-mandated text-based Basis for Offer Price KPI table (PDF pp. 169–170), OCF and Capex from the Cash Flow summary table (PDF p. 379), Debt from Capitalisation/Indebtedness (PDF p. 36/356), and Finance Costs from MD&A disclosures.

### Failure Point 3: Omission of Peer Comparison Extractor
- **First Point of Loss:** `DocumentExtractor.extract_from_pdf` in `engine/ipo_screening/extraction/extractor.py`.
- **Mechanism:** `SectionExtractor` had no method to extract listed peers from the Basis for Offer Price section. `CanonicalInputBuilder` defaulted to `{"name": "Generic Listed Peer Ltd: MISSING"}`.
- **Consequence:** The valuation module rejected the peer as missing, resulting in `pe_vs_peers` and `second_multiple` reporting UNKNOWN (12 unknown points).
- **Repair:** Implemented `SectionExtractor.extract_peers` to parse the standard ICDR "Comparison of Accounting Ratios with Listed Industry Peers" table (PDF p. 168). Extracted listed peer **Banaras Beads Limited** (P/E 44.31, P/B 1.36, RoNW 3.08%, CMP ₹119.20, as-of `2026-09-28`).

### Failure Point 4: Multi-Line Table Wrapping & Builder Mapping Defaults
- **First Point of Loss:** `SectionExtractor.extract_cover_and_offer` and `CanonicalInputBuilder._build_issue`.
- **Mechanism:**
  1. On the cover page, a two-column layout caused `OFFER FOR SALE SIZE` and `NIL` to be separated by table line breaks. Single-line regexes failed to match `NIL`, and `builder.py` defaulted `ofs` to 3,300 lakhs when `allow_fixture_fallbacks` was active.
  2. `promoter_post_pct` was not extracted due to line breaks across table cells (`Total (A)` on PDF p. 126).
  3. Statutory auditor tenure and network standing fields (`auditor_changed_3y`, `auditor_reputed`) were unmapped, causing `auditor_bucket` to return UNKNOWN.
  4. Industry CAGR metadata (`industry_scope`, `industry_forecast_period`, `industry_source`) was missing, triggering the strict spec s12 all-or-nothing fail-closed gate.
- **Repair:**
  1. Multi-line NIL OFS detector in `SectionExtractor.extract_cover_and_offer` emits `issue.ofs: 0.0` and `issue.ofs_sellers: []`.
  2. Multi-line post-issue shareholding parser captures promoter holding of `72.25%`.
  3. Governance extractor parses statutory auditor **Murarka & Associates** (audited all 3 FYs, not Big 4 -> `auditor_changed_3y = False`, `auditor_reputed = False` -> `eom_only` score 1.0).
  4. Business extractor parses top-5 customer concentration (`11.11%`) and forward industry CAGR (`8.0%`, scope `global`, period `2026-2035`, source `Global Artificial Jewellery Market Report`).

---

## 3. Criterion-by-Criterion Forensic Trace & Classification Matrix

| Module & Criterion ID | PDF Source Evidence (Page & Quote) | Extractor Output | Canonical Field | Evaluator Input | Repaired Result | Defect Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. revenue_cagr** | PDF pp. 169–170: Rev FY24 ₹1,328.49L, FY25 ₹1,777.19L, FY26 ₹3,035.71L | `financials.periods[].revenue` | `financials.periods` | `revenue_cagr_2y_from_3fy = 51.17%` | **SCORED 6.0/6.0** (band `> 25`) | `PRESENT_AND_REPAIRED` |
| **A. margin_trend** | PDF pp. 169–170: EBITDA FY24 0.86%, FY25 16.74%, FY26 24.16%; PAT FY24 7.13%, FY25 11.24%, FY26 20.71% | `financials.periods[].ebitda, pat` | `financials.periods` | `margin_trend = "expanding"` | **SCORED 5.0/5.0** (band `expanding`) | `PRESENT_AND_REPAIRED` |
| **A. roce** | PDF pp. 169–170: Disclosed ROCE FY26: 57.74% | `financials.periods[].disclosed_roce_pct` | `financials.periods` | `roce_latest = 57.74%` | **SCORED 5.0/5.0** (band `> 20`) | `PRESENT_AND_REPAIRED` |
| **A. cfo_quality** | PDF p. 379: OCF FY24 -₹7.13L, FY25 ₹77.61L, FY26 ₹114.72L; PAT sum ₹923.19L | `financials.periods[].cfo, pat` | `financials.periods` | `cfo_pat_cumulative = 0.2006` | **SCORED 1.0/5.0** (band `>= 0`) | `PRESENT_AND_REPAIRED` |
| **A. leverage** | PDF p. 36/356: FY26 Debt ₹170.32L, Net Worth ₹1,616.22L, Interest ₹0.97L | `financials.periods[].total_debt, net_worth` | `financials.periods` | `leverage_bucket = "strong"` (D/E 0.11, ICR > 100) | **SCORED 4.0/4.0** (band `strong`) | `PRESENT_AND_REPAIRED` |
| **B. pe_vs_peers** | PDF p. 168: Banaras Beads Limited CMP ₹119.20, EPS ₹2.69, P/E 44.31 (2026-09-28) | `peers` (1 peer object) | `peers` | Issuer P/E 14.67–20.25 vs Peer 44.31 (`pe_premium_pct <= -20%`) | **SCORED 8.0/8.0** (band `<= -20`) | `PRESENT_AND_REPAIRED` |
| **B. second_multiple** | PDF p. 168: Banaras Beads NAV ₹87.38 -> P/B 1.36 vs Issuer P/B ~2.4 | `peers` (P/B 1.36) | `peers` | `second_multiple_premium_pct` | **SCORED 0.0/4.0** (band `else`) | `PRESENT_AND_REPAIRED` |
| **B. peg** | P/E ~14.67 / PAT CAGR 157.4% = 0.093 | Derived from Issue & Periods | `derived.peg` | `peg = 0.093` | **SCORED 2.0/4.0** (band `< 1`, cap low_base) | `PRESENT_AND_REPAIRED` |
| **B. sector_ipo_relative** | Not present in pre-issue RHP (requires external database of recent 4 sector IPOs) | None | `recent_sector_ipos` | `None` | **UNKNOWN** (4.0 unavail pts) | `GENUINELY_UNAVAILABLE` |
| **C. fresh_share** | PDF p. 1, p. 82: Fresh 42,67,200 shares (₹3,499.10L), OFS NIL | `issue.fresh_issue, issue.ofs` | `issue.fresh_issue, issue.ofs` | `fresh_share_pct = 100.0%` | **SCORED 3.0/3.0** (band `> 70`) | `PRESENT_AND_REPAIRED` |
| **C. ofs_seller_type** | PDF p. 1: "OFFER FOR SALE SIZE: NIL" | `issue.ofs = 0.0, ofs_sellers = []` | `issue.ofs_sellers` | `ofs_seller_bucket = "none_or_small"` | **SCORED 2.0/2.0** (band `none_or_small`) | `PRESENT_AND_REPAIRED` |
| **C. promoter_ofs_pct** | PDF p. 1: "OFFER FOR SALE SIZE: NIL" | `issue.ofs = 0.0, ofs_sellers = []` | `issue.ofs_sellers` | `promoter_ofs_pct_of_holding = 0.0%` | **SCORED 2.0/2.0** (band `== 0`) | `PRESENT_AND_REPAIRED` |
| **C. dilution** | Pre-issue 11,249,563, Fresh 4,267,200 -> Dilution 27.5% | `issue.pre_issue_shares, fresh_shares` | `issue` | `dilution_ok = True` | **SCORED 1.0/1.0** (band `true`) | `PRESENT_AND_REPAIRED` |
| **C. use_of_proceeds** | PDF p. 133: Working capital ₹1,500L, Capex ₹1,000L, GCP `[●]` | `use_of_proceeds` (`[●]` GCP) | `use_of_proceeds` | Undisclosed marker triggers fail-closed UNKNOWN | **UNKNOWN** (4.0 unavail pts) | `GENUINELY_UNAVAILABLE` (fail-closed spec requirement) |
| **C. pre_ipo_placement** | PDF p. 106–133: No discounted placement in 12m | `capital_structure.pre_ipo_placements` | `capital_structure` | `pre_ipo_placement_bucket = "none_or_near_ipo"` | **SCORED 2.0/2.0** (band `none_or_near_ipo`) | `PRESENT_AND_REPAIRED` |
| **C. lockin** | PDF p. 106: Locked in for 18 months | `capital_structure.promoter_lockin_in_place` | `capital_structure` | `lockin_bucket = "intact"` | **SCORED 1.0/1.0** (band `intact`) | `PRESENT_AND_REPAIRED` |
| **D. promoter_post_holding** | PDF p. 126: Promoters 72.22% + Group 0.03% = 72.25% | `capital_structure.promoter_post_pct` | `capital_structure.promoter_post_pct` | `promoter_post_pct = 72.25%` | **SCORED 4.0/4.0** (band `> 60`) | `PRESENT_AND_REPAIRED` |
| **D. litigation** | PDF Section IX: No promoter/director criminal litigation | `governance.litigation_bucket` | `governance.litigation_bucket` | `litigation_bucket = "clean"` | **SCORED 4.0/4.0** (band `clean`) | `PRESENT_AND_REPAIRED` |
| **D. rpt** | PDF Section V/Financial Notes: RPT within limit | `governance.rpt_pct_revenue` | `governance.rpt_pct_revenue` | `rpt_pct_revenue = 6.67%` | **SCORED 1.0/3.0** (band `<= 15`) | `PRESENT_AND_REPAIRED` |
| **D. auditor** | PDF p. 170/292: Murarka & Associates, unchanged 3 FYs, not Big 4 | `governance.auditor_changed_3y: false, auditor_reputed: false` | `governance` | `auditor_bucket = "eom_only"` | **SCORED 1.0/2.0** (band `eom_only`) | `PRESENT_AND_REPAIRED` |
| **D. board_kmp** | PDF p. 248: 7 directors, 3 independent (42.8% <= 50%) | `governance.board_independent_majority` | `governance` | `board_kmp_bucket = "other"` | **SCORED 1.0/2.0** (band `other`) | `PRESENT_AND_REPAIRED` |
| **E. industry_growth** | PDF p. 192: Global Artificial Jewellery Market CAGR 8.0%, 2026–2035 | `business.industry_cagr_pct: 8.0`, scope: global, period: 2026-2035 | `business` | `industry_cagr_pct = 8.0%` | **SCORED 3.0/5.0** (band `>= 7`) | `PRESENT_AND_REPAIRED` |
| **E. moat** | PDF Section V: Strong niche artificial jewellery positioning | `business.moat_rating` | `business.moat_rating` | `moat_rating = "strong_niche"` | **SCORED 3.0/5.0** (band `strong_niche`) | `PRESENT_AND_REPAIRED` |
| **E. concentration** | PDF p. 45: Top 5 customers accounted for 11.11% in FY26 | `business.top5_customer_pct` | `business.top5_customer_pct` | `top5_concentration_pct = 11.11%` | **SCORED 3.0/3.0** (band `< 30`) | `PRESENT_AND_REPAIRED` |
| **E. visibility** | Operational capacity and order visibility | `business.visibility_rating` | `business.visibility_rating` | `visibility_rating = "strong"` | **SCORED 2.0/2.0** (band `strong`) | `PRESENT_AND_REPAIRED` |
| **F. anchor_quality** | External bidding signal (not in pre-issue RHP) | None | `market.anchor` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |
| **F. qib_subscription** | Live market subscription (not in pre-issue RHP) | None | `market.subscription.qib_x` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |
| **F. gmp_trend** | Grey market premium feed (not in pre-issue RHP) | None | `market.gmp.trend` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |
| **F. market_regime** | Nifty 50 secondary market index trend | None | `market.regime` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |
| **F. retail_nii_penalty** | Bidding close under-subscription signal | None | `market.subscription` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |

---

## 4. Verification and Invariant Compliance

1. **Zero Frozen Core Modifications:**
   `git diff --stat` confirms zero modifications to `engine/ipo_screening/derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`, and `extraction/price_band_notice.py`.
2. **Vishal Nirmiti Bit-for-Bit Golden Result Preservation:**
   `test_vishal_nirmiti_golden_hash_preserved` confirms that the golden result hash remains bit-for-bit identical:
   `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` (Score 35.0, Verdict INSUFFICIENT_DATA, Penalties -3.0).
3. **General ICDR Extractor Rule (No Hard-coding):**
   All extractors use standard ICDR patterns (TOC headers, KPI summary layouts, ICDR peer comparison rows, SEBI disclosure tables). No R.K.-specific company name branches or PDF-specific overrides were added.
4. **UI-7 Ingestion Security Boundary:**
   Zero server file paths in public ingestion API. Multipart document ingestion tested and verified with 13 passing unit and integration tests.
5. **Full Test Suite Status:**
   - 650 pytest test cases pass across all test modules (100% pass rate).
   - 8 native Node.js frontend tests pass (100% pass rate).
