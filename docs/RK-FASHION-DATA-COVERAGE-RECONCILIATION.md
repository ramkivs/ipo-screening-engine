# R.K. Fashion Accessories Data-Coverage Defect: Forensic Investigation & Pipeline Repair Report

**Target Filing:** R.K. Fashion Accessories Limited RHP (`handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`, 496 pages)  
**CIN:** U18109WB2010PLC144256  
**Reference Commit:** `e959e12` on branch `arena/01a10b42-ipo-screening-engine`  
**Engine Specification:** v1.5.0 (`schema/ipo-input.v1.5.schema.json`, `config/ipo-config.v1.5.0.json`)

---

## 1. Executive Summary & Authoritative Reconciliation Impact

**Authoritative Deterministic Result Hash:** `58fc5db51e74d9d3c33e5ad9ef2b00c6b733d4fae2efe6a7e77fb0471976b37e`  
**Deterministic Evaluation ID:** `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-58fc5db5`  
**Input Snapshot Hash:** `e1923f830b94ae7ba0dfcac72ac717e9c3593dd80e6380849e0228a0edcfc2b6`  
**Source Manifest Hash:** `dbb8f47274b0bcf7eb6363e707c860436a95237d660cf0a565ffc5770f859ef5`  
**Engine Version:** `1.5.0` | **Configuration Version:** `1.5.0`

| Metric / Attribute | Baseline Evaluation (`e959e12`) | Obsolete Contaminated (`2e27164`) | Authoritative Clean Repaired Evaluation | Net Reconciled Delta (vs Baseline) |
| :--- | :--- | :--- | :--- | :--- |
| **Final Score** | **20.0 / 100** | *61.0 / 100 (OBSOLETE)* | **55.0 / 100** | **+35.0 pts** |
| **Base Score** | 20.0 / 100 | *64.0 / 100 (OBSOLETE)* | **58.0 / 100** | **+38.0 pts** |
| **Penalties Applied** | 0.0 pts | -3.0 pts (`margin_spike`) | **-3.0 pts** (`margin_spike` triggered) | **-3.0 pts** |
| **Available Points** | 30.0 points | 82.0 points | **75.0 points** | **+45.0 points** |
| **Unknown Points** | **70.0 points** | 18.0 points | **25.0 points** | **-45.0 points** |
| **Completeness %** | 30.0% completeness | 82.0% (OBSOLETE) | **75.0% completeness** | **+45.0%** |
| **Confidence Level** | Low | Medium (OBSOLETE) | **Low** ($75.0\% < 80.0\%$) | **Preserved Fail-Closed** |
| **Verdict** | INSUFFICIENT_DATA | INSUFFICIENT_DATA | **INSUFFICIENT_DATA** | Preserved Fail-Closed |
| **Floor (Lower Bound)** | 17.0 | 48.0 (OBSOLETE) | **42.0** | **+25.0 pts** |
| **Ceiling (Upper Bound)** | 90.0 | 79.0 (OBSOLETE) | **80.0** | **-10.0 pts** |
| **Module A (Financial Quality)** | 0.0 / 0.0 (25 unknown pts) | 21.0 / 25.0 | **21.0 / 25.0 (0 unknown pts)** | **+21.0 pts (100% scored)** |
| **Module B (Valuation)** | 0.0 / 0.0 (16 unknown pts) | 10.0 / 16.0 | **10.0 / 16.0 (4 unknown pts)** | **+10.0 pts (real peer scored)** |
| **Module C (Offer Structure)** | 11.0 / 11.0 (4 unknown pts) | 11.0 / 11.0 (OBSOLETE) | **10.0 / 11.0 (4 unknown pts)** | **+10.0 pts (dilution 0/1)** |
| **Module D (Governance)** | 5.0 / 9.0 (6 unknown pts) | 11.0 / 15.0 | **11.0 / 15.0 (0 unknown pts)** | **+6.0 pts (100% scored)** |
| **Module E (Business/Moat)** | 4.0 / 10.0 (5 unknown pts) | 11.0 / 15.0 (OBSOLETE) | **6.0 / 8.0 (7 unknown pts)** | **+2.0 pts (moat/vis UNKNOWN)** |
| **Module F (Market/Demand)** | 0.0 / 0.0 (10 unknown pts) | 0.0 / 0.0 | **0.0 / 0.0 (10 unknown pts)** | Genuine external unknowns |

---

### Reconciliation of Score Discrepancies (Historical Contaminated 61.0 vs Verified Clean Repaired 55.0)

In the initial reconciliation pass at commit `2e27164`, an evaluation score of **61.0 / 100** (Base: 64.0, Penalty: -3.0) was reported. Comprehensive forensic investigation revealed that this 61.0 score was **OBSOLETE AND CONTAMINATED** due to test fixture constants silently leaking into the evaluation from `CanonicalInputBuilder` (`builder.py`), which defaulted to fallback values from Vishal Nirmiti (`fixtures/vishal_nirmiti/input.json`).

When all cross-IPO fixture fallbacks were completely eliminated (`allow_fixture_fallbacks=False`) and the pipeline was audited against clean, proven R.K. Fashion Accessories RHP facts, three distinct criteria diverged from the obsolete 61-point claim:

1. **Module C — `dilution` ($-1.0$ point divergence):**
   - *Contaminated State (`2e27164`)*: Scored $1.0 / 1.0$ point based on Vishal Nirmiti's post-issue shares fallback of $26,390,909$, which falsely computed dilution as $4,267,200 / 26,390,909 = 16.17\% < 25.0\%$.
   - *Repaired Clean State*: R.K.'s actual post-issue share count from RHP page 107 is $15,516,763$. The true dilution is $4,267,200 / 15,516,763 = \mathbf{27.500581...\%} \ge 25.0\%$. Because General Corporate Purposes (GCP) is undisclosed (`[●]`), the growth exemption cannot be conferred under fail-closed rules. Consequently, `dilution_ok` evaluates strictly to `False`, scoring **0.0 / 1.0 points**.
2. **Module E — `moat` ($-3.0$ points divergence, $+5.0$ unknown points):**
   - *Contaminated State (`2e27164`)*: Scored $3.0 / 5.0$ points based on Vishal Nirmiti's `"strong_niche"` fixture fallback.
   - *Repaired Clean State*: Qualitative assessments are not deterministically extractable from the statutory RHP text. Under strict fail-closed extraction, `moat_rating` is `None`, evaluating criterion `moat` to **UNKNOWN** ($0.0$ scored / $5.0$ unavailable points).
3. **Module E — `visibility` ($-2.0$ points divergence, $+2.0$ unknown points):**
   - *Contaminated State (`2e27164`)*: Scored $2.0 / 2.0$ points based on Vishal Nirmiti's `"strong"` fixture fallback.
   - *Repaired Clean State*: Qualitative assessments are not deterministically extractable from the statutory RHP text. Under strict fail-closed extraction, `visibility_rating` is `None`, evaluating criterion `visibility` to **UNKNOWN** ($0.0$ scored / $2.0$ unavailable points).

#### Mathematical Reconciliation from Obsolete 64.0 Base to Verified 58.0 Base:
$$\text{Obsolete Contaminated Base Score} = 64.0$$
$$- 1.0 \text{ (true dilution 27.50\% } \ge 25.0\%) = 63.0$$
$$- 3.0 \text{ (moat unextracted qualitative rating } \to \text{UNKNOWN}) = 60.0$$
$$- 2.0 \text{ (visibility unextracted qualitative rating } \to \text{UNKNOWN}) = \mathbf{58.0}$$

$$\text{Final Verified Clean Score} = \text{Base } (58.0) - \text{Active Penalties } (3.0) = \mathbf{55.0 \text{ / } 100}$$

---

### Complete Authoritative Score Arithmetic (Verified Clean Result)

- **Module A (Financial Quality): 21.0 / 25.0 (Available: 25.0, Unknown: 0)**
  - `revenue_cagr`: 6.0 / 6.0 (band `> 25`, derived 2-yr CAGR = 51.16%)
  - `margin_trend`: 5.0 / 5.0 (band `expanding`, EBITDA margin 0.86% -> 16.74% -> 24.16%)
  - `roce`: 5.0 / 5.0 (band `> 20`, disclosed FY26 ROCE = 57.74%)
  - `cfo_quality`: 1.0 / 5.0 (band `>= 0`, cumulative CFO/PAT ratio = 0.2006)
  - `leverage`: 4.0 / 4.0 (band `strong`, D/E 0.11, ICR > 100)
- **Module B (Valuation): 10.0 / 16.0 (Available: 16.0, Unknown: 4.0)**
  - `pe_vs_peers`: 8.0 / 8.0 (band `<= -20%`, Banaras Beads P/E 44.31 vs Issuer P/E 20.25, premium = -54.31%)
  - `second_multiple`: 0.0 / 4.0 (band `else`, Banaras Beads P/B 1.36 vs Issuer P/B ~2.49)
  - `peg`: 2.0 / 4.0 (band `< 1`, PEG = 0.1285, capped at 2.0 due to `low_base_year`)
  - `sector_ipo_relative`: UNKNOWN (4.0 unknown points; secondary market sector IPO database unsupplied)
- **Module C (Offer Structure, Proceeds & Pre-IPO): 10.0 / 11.0 (Available: 11.0, Unknown: 4.0)**
  - `fresh_share`: 3.0 / 3.0 (band `> 70`, 100% fresh issue of ₹3,499.10L)
  - `ofs_seller_type`: 2.0 / 2.0 (band `none_or_small`, OFS is NIL)
  - `promoter_ofs_pct`: 2.0 / 2.0 (band `== 0`, OFS is NIL)
  - `dilution`: 0.0 / 1.0 (band `false`, dilution = 27.50% $\ge$ 25.0%, GCP undisclosed so growth exemption not conferred)
  - `use_of_proceeds`: UNKNOWN (4.0 unknown points; fail-closed due to explicitly undisclosed GCP `[●]`)
  - `pre_ipo_placement`: 2.0 / 2.0 (band `none_or_near_ipo`, no discounted placement within 12m)
  - `lockin`: 1.0 / 1.0 (band `intact`, 18-month promoter lock-in confirmed)
- **Module D (Promoter & Governance): 11.0 / 15.0 (Available: 15.0, Unknown: 0)**
  - `promoter_post_holding`: 4.0 / 4.0 (band `> 60`, post-issue holding 72.25%)
  - `litigation`: 4.0 / 4.0 (band `clean`, no criminal litigation against promoters/directors)
  - `rpt`: 1.0 / 3.0 (band `<= 15`, FY26 RPT % of revenue = 10.79%)
  - `auditor`: 1.0 / 2.0 (band `eom_only`, Murarka & Associates unchanged 3 FYs, peer-reviewed, not Big-4)
  - `board_kmp`: 1.0 / 2.0 (band `other`, 3 of 7 independent directors = 42.8% <= 50%)
- **Module E (Business & Moat): 6.0 / 8.0 (Available: 8.0, Unknown: 7.0)**
  - `industry_growth`: 3.0 / 5.0 (band `>= 8`, Global Artificial Jewellery Market CAGR = 8.0%)
  - `moat`: UNKNOWN (5.0 unknown points; qualitative rating not in RHP, fail-closed `None`)
  - `concentration`: 3.0 / 3.0 (band `< 30`, top-5 customer concentration = 11.11%)
  - `visibility`: UNKNOWN (2.0 unknown points; qualitative rating not in RHP, fail-closed `None`)
- **Module F (Market & Demand Signals): 0.0 / 0.0 (Available: 0, Unknown: 10.0)**
  - `gmp_trend`: UNKNOWN (3.0 pts, unsupplied external secondary feed)
  - `market_regime`: UNKNOWN (2.0 pts, unsupplied external index feed)
  - `overall_subscription`: UNKNOWN (2.0 pts, unsupplied live exchange feed)
  - `nii_subscription`: UNKNOWN (2.0 pts, unsupplied live exchange feed)
  - `retail_nii_penalty`: UNKNOWN (1.0 pt, unsupplied live exchange feed)
- **Base Score Total:** $21.0 + 10.0 + 10.0 + 11.0 + 6.0 + 0.0 = \mathbf{58.0 \text{ / } 75.0 \text{ available points}}$
- **Penalties Total:** $\mathbf{-3.0 \text{ points}}$ (`margin_spike` triggered due to EBITDA margin jumping from 0.86% in FY24 to 24.16% in FY26, > 500 bps YoY)
- **Final Deterministic Score:** $58.0 - 3.0 = \mathbf{55.0 \text{ / } 100}$
- **Completeness %:** $\frac{75.0 \text{ available}}{100.0 \text{ max}} \times 100\% = \mathbf{75.0\%}$
- **Confidence Level:** **Low** ($75.0\% < 80.0\%$ threshold)
- **Verdict:** `INSUFFICIENT_DATA` (fail-closed due to completeness $< 80.0\%$)
- **Floor (Lower Bound):** $58.0 - 3.0 \text{ (active)} - 13.0 \text{ (unresolved penalties)} = \mathbf{42.0}$
- **Ceiling (Upper Bound):** $58.0 + 25.0 \text{ (unknown)} - 3.0 \text{ (active)} = \mathbf{80.0}$

---

## 2. Industry CAGR Semantics & Contractual Grounding

### Schema & Evaluator Contract (v1.5.0)
Under `schema/ipo-input.v1.5.schema.json` (lines 746–775):
- `industry_cagr_pct`: Number (percentage).
- `industry_scope`: Enum `["india", "global", "regional", null]`. Global scope is an explicitly valid statutory input.
- `industry_forecast_period`: String (e.g. "2026-2035").
- `industry_source`: String citing the independent report.
- `industry_is_primary`: Boolean indicating primary product segment.

Under `config/ipo-config.v1.5.0.json` (lines 585–605), `industry_growth` requires all three companion fields (`industry_scope`, `industry_forecast_period`, `industry_source`). If any are omitted, the criterion fails closed to `UNKNOWN`.

### Why Global Artificial Jewellery Market CAGR (8.0%) is Authoritative
Section V (Industry Overview) of the RHP presents two distinct market discussions:
1. **Subsection A (PDF p. 192): `GLOBAL IMITATION JEWELLERY MARKET`**
   - *"The global Artificial Jewellery Market is estimated to be valued at approximately USD 29.16 Billion in 2026. The market is projected to reach USD 58.32 Billion by 2035, expanding at a CAGR of 8% from 2026 to 2035."*
   - Independent Source: Maximize Market Research Report (`https://www.maximizemarketresearch.com/market-report/jewelry-market/147820/`).
   - Forecast Period: `2026-2035`.
   - Point Estimate: Exactly `8.0%`.
2. **Subsection B (PDF p. 194): `INDIAN JEWELLERY MARKET`**
   - Discusses the broad Indian domestic jewellery market (valued at USD 90–91B, projected to USD 150B at a CAGR range of 5.2–6.3%).
   - Critical Disclosure on p. 194: *"The Gold jewellery market in India dominates the landscape with a commanding 80–85% share, while studded jewellery accounts for 15–20%. Fine jewellery represents nearly 90% of the overall market."*

**Authoritative Justification:**
- **Product Segment Alignment:** R.K. Fashion Accessories Limited does not manufacture gold bullion, diamond solitaires, or precious metal jewellery. It manufactures 100% imitation/artificial fashion jewellery and accessories. Applying the precious metals bullion market CAGR (80-85% gold) to an imitation fashion jewellery producer violates financial and semantic grounding.
- **Definitive Metric vs Range:** The global artificial jewellery report provides a definitive point estimate (`8.0%`) and single forecast horizon (`2026-2035`), whereas the general Indian overview cites a loose range (`5.2 - 6.3%`).
- **Contract Compliance:** Global artificial jewellery outlook complies completely with the v1.5.0 specification and schema enums without altering engine scoring rules.

---

## 3. Explicit Tripartite Unknown Points Classification (25.0 Unknown Points)

The 25 unobserved points across the 100 evaluable points are strictly partitioned into three mutually exclusive categories:

### Category 1: External-Data Unavailable (14.0 Points)
These criteria evaluate market-wide conditions or live market transactions occurring outside the statutory RHP document boundary:
1. **`B.sector_ipo_relative` (4.0 pts):** Requires secondary trading performance and listing-day multiples of the last 4 IPOs in the same sector over the preceding 12 months. This historical trading dataset is not part of the issuer's pre-issue RHP.
2. **`F.gmp_trend` (3.0 pts):** Requires live unofficial grey market premium tracking feeds.
3. **`F.market_regime` (2.0 pts):** Requires secondary market index moving averages (Nifty 50 50-DMA and 200-DMA).
4. **`F.overall_subscription` (2.0 pts):** Requires real-time exchange bidding book data across QIB, NII, and Retail books.
5. **`F.nii_subscription` (2.0 pts):** Requires real-time non-institutional investor bidding book data.
6. **`F.retail_nii_penalty` (1.0 pt):** Requires final bidding-close undersubscription tallies.

### Category 2: Source Explicitly Undisclosed / Unavailable in RHP (4.0 Points)
These criteria could not be scored because the statutory prospectus deliberately left the required value blank or unpriced:
1. **`C.use_of_proceeds` (4.0 pts):** In RHP Section III ("Objects of the Issue", p. 133), the General Corporate Purposes (GCP) amount is stated with the legal placeholder `[●]` pending discovery of the final offer price. Under v1.5.0 specification Section 13, the engine is strictly prohibited from substituting the statutory 25% ceiling or treating the undisclosed amount as zero, as doing so would allow blind-heavy issues to bypass governance checks. The criterion fail-closes to `UNKNOWN`.

### Category 3: Unextracted Qualitative Dimensions (7.0 Points)
These criteria evaluate qualitative company characteristics that are not deterministically extractable from statutory disclosures:
1. **`E.moat` (5.0 pts):** Market-position and moat durability rating (`moat_rating`). Absent an analyst override, it strictly evaluates to `None` / `UNKNOWN`.
2. **`E.visibility` (2.0 pts):** Capacity and order-book revenue visibility assessment (`visibility_rating`). Absent an analyst override, it strictly evaluates to `None` / `UNKNOWN`.

---

## 4. Root Cause Analysis of Information Loss

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
  3. Pre-issue and post-issue shares were missing extractors, causing fallbacks to Vishal constants ($19,800,000$ and $26,390,909$), which contaminated dilution calculations.
  4. Lot size lacked an extractor, falling back to 68 instead of the SME trading lot of 1,600.
  5. Post-issue EPS fell back to 9.46 instead of deriving from restated PAT and post-issue shares (4.05).
  6. RPT percentage fell back to 6.67% instead of extracting FY26 disclosed 10.79%.
  7. Statutory auditor tenure and network standing fields (`auditor_changed_3y`, `auditor_reputed`) were unmapped, causing `auditor_bucket` to return UNKNOWN.
  8. Industry CAGR metadata (`industry_scope`, `industry_forecast_period`, `industry_source`) was missing, triggering the strict spec s12 all-or-nothing fail-closed gate.
- **Repair:**
  1. Multi-line NIL OFS detector in `SectionExtractor.extract_cover_and_offer` emits `issue.ofs: 0.0` and `issue.ofs_sellers: []`.
  2. Multi-line post-issue shareholding parser captures promoter holding of `72.25%` and pre-issue holding of `99.67%`.
  3. Forward table row parser extracts pre-issue shares of `11,249,563` and post-issue shares of `15,516,763`.
  4. Lot size extractor discovers SME market trading lot of `1,600` shares on definitions and trading disclosures pages.
  5. Derived post-issue EPS computes deterministically as $₹62,869,000 / 15,516,763 = \mathbf{4.05}$.
  6. RPT extractor captures FY26 RPT percentage of revenue as `10.79%` (repairing the old contaminated `6.67%` fallback).
  7. Governance extractor parses statutory auditor **Murarka & Associates** (audited all 3 FYs, not Big 4 -> `auditor_changed_3y = False`, `auditor_reputed = False` -> `eom_only` score 1.0).
  8. Business extractor parses top-5 customer concentration (`11.11%`) and forward industry CAGR (`8.0%`, scope `global`, period `2026-2035`, source `Global Artificial Jewellery Market Report`).

---

## 5. Criterion-by-Criterion Forensic Trace & Classification Matrix

| Module & Criterion ID | PDF Source Evidence (Page & Quote) | Extractor Output | Canonical Field | Evaluator Input | Repaired Result | Defect Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. revenue_cagr** | PDF pp. 169–170: Rev FY24 ₹1,328.49L, FY25 ₹1,777.19L, FY26 ₹3,035.71L | `financials.periods[].revenue` | `financials.periods` | `revenue_cagr_2y_from_3fy = 51.16%` | **SCORED 6.0/6.0** (band `> 25`) | `PRESENT_AND_REPAIRED` |
| **A. margin_trend** | PDF pp. 169–170: EBITDA FY24 0.86%, FY25 16.74%, FY26 24.16%; PAT FY24 7.13%, FY25 11.24%, FY26 20.71% | `financials.periods[].ebitda, pat` | `financials.periods` | `margin_trend = "expanding"` | **SCORED 5.0/5.0** (band `expanding`) | `PRESENT_AND_REPAIRED` |
| **A. roce** | PDF pp. 169–170: Disclosed ROCE FY26: 57.74% | `financials.periods[].disclosed_roce_pct` | `financials.periods` | `roce_latest = 57.74%` | **SCORED 5.0/5.0** (band `> 20`) | `PRESENT_AND_REPAIRED` |
| **A. cfo_quality** | PDF p. 379: OCF FY24 -₹7.13L, FY25 ₹77.61L, FY26 ₹114.72L; PAT sum ₹923.19L | `financials.periods[].cfo, pat` | `financials.periods` | `cfo_pat_cumulative = 0.2006` | **SCORED 1.0/5.0** (band `>= 0`) | `PRESENT_AND_REPAIRED` |
| **A. leverage** | PDF p. 36/356: FY26 Debt ₹170.32L, Net Worth ₹1,616.22L, Interest ₹0.97L | `financials.periods[].total_debt, net_worth` | `financials.periods` | `leverage_bucket = "strong"` (D/E 0.11, ICR > 100) | **SCORED 4.0/4.0** (band `strong`) | `PRESENT_AND_REPAIRED` |
| **B. pe_vs_peers** | PDF p. 168: Banaras Beads Limited CMP ₹119.20, EPS ₹2.69, P/E 44.31 (2026-09-28) | `peers` (1 peer object) | `peers` | Issuer P/E 20.25 vs Peer 44.31 (`pe_premium_pct = -54.31%`) | **SCORED 8.0/8.0** (band `<= -20`) | `PRESENT_AND_REPAIRED` |
| **B. second_multiple** | PDF p. 168: Banaras Beads NAV ₹87.38 -> P/B 1.36 vs Issuer P/B ~2.49 | `peers` (P/B 1.36) | `peers` | `second_multiple_premium_pct = +82.90%` | **SCORED 0.0/4.0** (band `else`) | `PRESENT_AND_REPAIRED` |
| **B. peg** | P/E 20.25 / PAT CAGR 157.44% = 0.1285 | Derived from Issue & Periods | `derived.peg` | `peg = 0.1285` | **SCORED 2.0/4.0** (band `< 1`, cap low_base) | `PRESENT_AND_REPAIRED` |
| **B. sector_ipo_relative** | Not present in pre-issue RHP (requires external database of recent 4 sector IPOs) | None | `recent_sector_ipos` | `None` | **UNKNOWN** (4.0 unavail pts) | `GENUINELY_UNAVAILABLE` |
| **C. fresh_share** | PDF p. 1, p. 82: Fresh 42,67,200 shares (₹3,499.10L), OFS NIL | `issue.fresh_issue, issue.ofs` | `issue.fresh_issue, issue.ofs` | `fresh_share_pct = 100.0%` | **SCORED 3.0/3.0** (band `> 70`) | `PRESENT_AND_REPAIRED` |
| **C. ofs_seller_type** | PDF p. 1: "OFFER FOR SALE SIZE: NIL" | `issue.ofs = 0.0, ofs_sellers = []` | `issue.ofs_sellers` | `ofs_seller_bucket = "none_or_small"` | **SCORED 2.0/2.0** (band `none_or_small`) | `PRESENT_AND_REPAIRED` |
| **C. promoter_ofs_pct** | PDF p. 1: "OFFER FOR SALE SIZE: NIL" | `issue.ofs = 0.0, ofs_sellers = []` | `issue.ofs_sellers` | `promoter_ofs_pct_of_holding = 0.0%` | **SCORED 2.0/2.0** (band `== 0`) | `PRESENT_AND_REPAIRED` |
| **C. dilution** | Pre 11,249,563, Fresh 4,267,200, Post 15,516,763 -> Dilution 27.50% | `issue.pre_issue_shares, fresh_shares, post_issue_shares` | `issue` | `dilution_ok = False` (dilution 27.50% $\ge$ 25.0% threshold) | **SCORED 0.0/1.0** (band `false`) | `PRESENT_AND_REPAIRED` |
| **C. use_of_proceeds** | PDF p. 133: Working capital ₹1,500L, Capex ₹1,000L, GCP `[●]` | `use_of_proceeds` (`[●]` GCP) | `use_of_proceeds` | Undisclosed marker triggers fail-closed UNKNOWN | **UNKNOWN** (4.0 unavail pts) | `GENUINELY_UNAVAILABLE` (fail-closed spec requirement) |
| **C. pre_ipo_placement** | PDF p. 106–133: No discounted placement in 12m | `capital_structure.pre_ipo_placements` | `capital_structure` | `pre_ipo_placement_bucket = "none_or_near_ipo"` | **SCORED 2.0/2.0** (band `none_or_near_ipo`) | `PRESENT_AND_REPAIRED` |
| **C. lockin** | PDF p. 106: Locked in for 18 months | `capital_structure.promoter_lockin_in_place` | `capital_structure` | `lockin_bucket = "intact"` | **SCORED 1.0/1.0** (band `intact`) | `PRESENT_AND_REPAIRED` |
| **D. promoter_pre_holding** | PDF p. 126: Promoters 99.61% + Group 0.06% = 99.67% | `capital_structure.promoter_pre_pct` | `capital_structure.promoter_pre_pct` | `promoter_pre_pct = 99.67%` | Telemetry captured | `PRESENT_AND_REPAIRED` |
| **D. promoter_post_holding** | PDF p. 126: Promoters 72.22% + Group 0.03% = 72.25% | `capital_structure.promoter_post_pct` | `capital_structure.promoter_post_pct` | `promoter_post_pct = 72.25%` | **SCORED 4.0/4.0** (band `> 60`) | `PRESENT_AND_REPAIRED` |
| **D. litigation** | PDF Section IX: No promoter/director criminal litigation | `governance.litigation_bucket` | `governance.litigation_bucket` | `litigation_bucket = "clean"` | **SCORED 4.0/4.0** (band `clean`) | `PRESENT_AND_REPAIRED` |
| **D. rpt** | PDF Section I / p. 62: FY26 RPT % of revenue is 10.79% | `governance.rpt_pct_revenue` | `governance.rpt_pct_revenue` | `rpt_pct_revenue = 10.79%` (replaces obsolete 6.67% fallback) | **SCORED 1.0/3.0** (band `<= 15`) | `PRESENT_AND_REPAIRED` |
| **D. auditor** | PDF p. 170/292: Murarka & Associates, unchanged 3 FYs, not Big 4 | `governance.auditor_changed_3y: false, auditor_reputed: false` | `governance` | `auditor_bucket = "eom_only"` | **SCORED 1.0/2.0** (band `eom_only`) | `PRESENT_AND_REPAIRED` |
| **D. board_kmp** | PDF p. 248: 7 directors, 3 independent (42.8% <= 50%) | `governance.board_independent_majority` | `governance` | `board_kmp_bucket = "other"` | **SCORED 1.0/2.0** (band `other`) | `PRESENT_AND_REPAIRED` |
| **E. industry_growth** | PDF p. 192: Global Artificial Jewellery Market CAGR 8.0%, 2026–2035 | `business.industry_cagr_pct: 8.0`, scope: global, period: 2026-2035 | `business` | `industry_cagr_pct = 8.0%` | **SCORED 3.0/5.0** (band `>= 8`) | `PRESENT_AND_REPAIRED` |
| **E. moat** | Qualitative rating not deterministically extracted from RHP | `business.moat_rating = None` | `business.moat_rating` | `moat_rating = None` | **UNKNOWN** (5.0 unavail pts) | `GENUINELY_UNAVAILABLE` (qualitative) |
| **E. concentration** | PDF p. 45: Top 5 customers accounted for 11.11% in FY26 | `business.top5_customer_pct` | `business.top5_customer_pct` | `top5_concentration_pct = 11.11%` | **SCORED 3.0/3.0** (band `< 30`) | `PRESENT_AND_REPAIRED` |
| **E. visibility** | Qualitative rating not deterministically extracted from RHP | `business.visibility_rating = None` | `business.visibility_rating` | `visibility_rating = None` | **UNKNOWN** (2.0 unavail pts) | `GENUINELY_UNAVAILABLE` (qualitative) |
| **F. anchor_quality** | External bidding signal (not in pre-issue RHP) | None | `market.anchor` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |
| **F. qib_subscription** | Live market subscription (not in pre-issue RHP) | None | `market.subscription.qib_x` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |
| **F. gmp_trend** | Grey market premium feed (not in pre-issue RHP) | None | `market.gmp.trend` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |
| **F. market_regime** | Nifty 50 secondary market index trend | None | `market.regime` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |
| **F. retail_nii_penalty** | Bidding close under-subscription signal | None | `market.subscription` | `None` | **UNKNOWN** | `GENUINELY_UNAVAILABLE` |

---

## 6. Verification and Invariant Compliance

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
   - 658 pytest test cases pass across all test modules (100% pass rate).
   - Includes dedicated isolation suite `tests/test_fixture_fallback_isolation.py` (Tests A through H) asserting zero cross-IPO contamination.
   - Includes reconciliation test suite `tests/test_rk_fashion_reconciliation.py`.
