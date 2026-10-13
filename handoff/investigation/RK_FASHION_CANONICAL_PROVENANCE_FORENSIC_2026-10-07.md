# Forensic Investigation Report: R.K. Fashion Accessories Canonical Input Provenance & Cross-IPO Contamination Audit

**Target Filing:** R.K. Fashion Accessories Limited RHP (`handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`, 496 pages)  
**CIN:** U18109WB2010PLC144256  
**Authoritative Commit Baseline:** `2e1c58584ff2926400845ae25c1be7a2032776ed` on branch `arena/01a10b42-ipo-screening-engine`  
**Investigation Date:** 2026-10-07  
**Investigation Mode:** Strict Read-Only Investigation (Zero Implementation Changes, Zero Schema Mutations, Zero Main Merges, Zero Commits)

---

## 1. Executive Finding

This forensic investigation confirms that while the mathematical score aggregation of the screening engine is internally consistent, **eight critical canonical input fields entering the R.K. Fashion Accessories evaluation are contaminated by test fixture constants from Vishal Nirmiti Limited (`fixtures/vishal_nirmiti/input.json`)**:

1. **`issue.post_issue_eps = 9.46`** (Vishal Nirmiti fixture value; R.K. actual post-issue EPS is **₹4.05**, or pre-issue FY26 EPS of **₹5.59**).
2. **`issue.post_issue_shares = 26,390,909`** (Vishal Nirmiti fixture value; R.K. actual post-issue share capital is **15,516,763** shares).
3. **`issue.pre_issue_shares = 19,800,000`** (Vishal Nirmiti fixture value; R.K. actual pre-issue share capital is **11,249,563** shares).
4. **`issue.lot_size = 68`** (Vishal Nirmiti fixture value; R.K. actual SME lot size is **1,600** shares).
5. **`capital_structure.promoter_pre_pct = 73.42%`** (Vishal Nirmiti fixture value; R.K. actual promoter & promoter group pre-issue holding is **99.67%**).
6. **`governance.rpt_pct_revenue = 6.67%`** (Vishal Nirmiti fixture value; R.K. actual FY2026 RPT share is **10.79%**).
7. **`business.moat_rating = "strong_niche"`** (Vishal Nirmiti fixture value; unextracted from PDF text, injected via `builder.py:282`).
8. **`business.visibility_rating = "strong"`** (Vishal Nirmiti fixture value; unextracted from PDF text, injected via `builder.py:283`).

### Point of Injection
The contamination entered through `DocumentExtractor.extract_from_pdf` in `engine/ipo_screening/extraction/extractor.py:34`, which defaults parameter `allow_fixture_fallbacks: bool = True`. In `engine/ipo_screening/extraction/builder.py`, whenever an optional or missing field has no raw PDF extraction candidate, `CanonicalInputBuilder` falls back to historical test fixture constants from Vishal Nirmiti. When `allow_fixture_fallbacks=False` is tested, the canonical JSON fails schema validation because `issue.lot_size` evaluates to `None` while `schema/ipo-input.v1.5.schema.json` requires an integer.

### Material Score Impact
- The contamination of `post_issue_shares` artificially suppressed dilution to $24.97\% < 25.0\%$, granting +1.0 point on `dilution` that R.K. does not qualify for (actual dilution is $27.50\% \ge 25\%$, which scores 0.0).
- Defaulting `moat_rating = "strong_niche"` and `visibility_rating = "strong"` injected **+5.0 scored points** (+3.0 on `moat`, +2.0 on `visibility`) from unextracted qualitative ratings.
- If proven factual fields are corrected and unextracted qualitative ratings fail-closed to `UNKNOWN`, the provisional deterministic score shifts from **61.0/100 (82% completeness, Medium confidence)** to **55.0/100 (75% completeness, Low confidence)**.

---

## 2. Current 61-Point Evaluation Status

The evaluation produced at baseline `2e1c585` reports:

| Metric | Authoritative Reported Value |
| :--- | :--- |
| **Final Score** | **61.0 / 100** |
| **Base Score** | **64.0 / 82.0 available points** |
| **Floor (Lower Bound)** | **48.0** |
| **Ceiling (Upper Bound)** | **79.0** |
| **Available Points** | **82.0 points** |
| **Unknown Points** | **18.0 points** |
| **Completeness %** | **82.0%** |
| **Confidence Level** | **Medium** |
| **Verdict** | **INSUFFICIENT_DATA** |
| **Result Hash** | `033fd07d4f0c9ab91863d4a8d85305d439966a9e1833b0fcd57b96028570eab7` |
| **Evaluation ID** | `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-033fd07d` |

### Current Module Breakdown:
- **Module A (Financial Quality):** 21.0 / 25.0 (0 unknown pts)
- **Module B (Valuation):** 10.0 / 16.0 available (4.0 unknown pts)
- **Module C (Offer Structure):** 11.0 / 11.0 available (4.0 unknown pts)
- **Module D (Governance):** 11.0 / 15.0 (0 unknown pts)
- **Module E (Business/Moat):** 11.0 / 15.0 (0 unknown pts)
- **Module F (Market Signals):** 0.0 / 0.0 available (10.0 unknown pts)
- **Penalties Applied:** -3.0 points (`margin_spike` triggered due to EBITDA margin expanding > 500 bps YoY)

---

## 3. Cross-IPO Contamination Findings

A global repository scan against `fixtures/vishal_nirmiti/input.json` and historical constants (`208`, `220`, `68`, `9.46`, `85.33`, `73.42`, `6.67`) identified the following contamination vectors:

| Contaminated Field | Current Value Entering Evaluator | Source File & Line | Originating Fixture | R.K. Fashion Accessories Expected Ground Truth | Severity |
| :--- | :---: | :--- | :--- | :--- | :---: |
| `issue.post_issue_eps` | `9.46` | `builder.py:165` | `vishal_nirmiti/input.json:194` | **₹4.05** (FY26 PAT ₹628.69L / 15,516,763 post shares) | **CRITICAL** |
| `issue.post_issue_shares` | `26390909` | `builder.py:163` | `vishal_nirmiti/input.json:192` | **15,516,763** (RHP p. 107 Section D) | **CRITICAL** |
| `issue.pre_issue_shares` | `19800000` | `builder.py:164` | `vishal_nirmiti/input.json:193` | **11,249,563** (RHP p. 106 Section B) | **CRITICAL** |
| `issue.lot_size` | `68` | `builder.py:159` | `vishal_nirmiti/input.json:188` | **1,600** (RHP p. 14, p. 102; NSE EMERGE lot size) | **HIGH** |
| `capital_structure.promoter_pre_pct` | `73.42` | `builder.py:213` | `vishal_nirmiti/input.json:207` | **99.67%** (RHP p. 126: 99.61% Promoters + 0.06% Group) | **MEDIUM** |
| `governance.rpt_pct_revenue` | `6.67` | `builder.py:260` | `vishal_nirmiti/input.json:225` | **10.79%** (RHP p. 38, p. 62 for FY2026) | **HIGH** |
| `business.moat_rating` | `"strong_niche"` | `builder.py:282` | `vishal_nirmiti/input.json:237` | Unextracted from PDF; should fail-close to `None` | **HIGH** |
| `business.visibility_rating` | `"strong"` | `builder.py:283` | `vishal_nirmiti/input.json:238` | Unextracted from PDF; should fail-close to `None` | **HIGH** |
| `board` | `"mainboard"` | `builder.py:61` | Fallback default | **"sme"** (NSE EMERGE platform, RHP p. 107) | **MEDIUM** |

---

## 4. Valuation Forensic

### 4.1 Post-Issue EPS Provenance
- In Vishal Nirmiti, FY26 PAT was ₹2,496.88L and post-issue shares were 26,390,909. Dividing $249,688,000 / 26,390,909 = \mathbf{9.4611} \approx \mathbf{9.46}$.
- In R.K. Fashion Accessories:
  - FY26 Restated PAT = **₹628.69 Lakhs** (RHP p. 166, p. 170).
  - Pre-issue shares = **11,249,563** (RHP p. 106).
  - Fresh shares = **4,267,200** (RHP p. 106).
  - Total Post-Issue Shares = **15,516,763** (RHP p. 107).
  - True Post-Issue EPS:
    $$\text{Post-Issue EPS} = \frac{62,869,000}{15,516,763} = \mathbf{4.05168 \approx 4.05}$$
  - True Pre-Issue Weighted Average EPS: **₹5.59** (RHP p. 166).
- **Conclusion:** `9.46` has zero factual connection to R.K. Fashion Accessories and is a 100% cross-IPO contamination artifact.

### 4.2 Issuer P/E and `pe_vs_peers`
- Under `derived.py:568`, `issuer_pe = price_band_high / post_issue_eps`.
- With contaminated EPS (9.46): $\text{Issuer P/E} = 82 / 9.46 = \mathbf{8.67\times}$.
- With true R.K. post-issue EPS (4.05): $\text{Issuer P/E} = 82 / 4.05168 = \mathbf{20.24\times}$.
- With R.K. pre-issue FY26 EPS (5.59): $\text{Issuer P/E} = 82 / 5.59 = \mathbf{14.67\times}$ (matches RHP p. 167 exactly).
- Banaras Beads Limited Peer P/E: **44.31** (as of September 28, 2026, RHP p. 168).
- **Premium vs Peer:**
  - With contaminated EPS (8.67x): $(8.67 / 44.31 - 1) = \mathbf{-80.44\%} \le -20\%$ (scored 8.0 / 8.0).
  - With true post-issue EPS (20.24x): $(20.24 / 44.31 - 1) = \mathbf{-54.33\%} \le -20\%$ (still scores 8.0 / 8.0).
  - With RHP pre-issue EPS (14.67x): $(14.67 / 44.31 - 1) = \mathbf{-66.90\%} \le -20\%$ (still scores 8.0 / 8.0).
- **Score Consequence:** `pe_vs_peers` robustly scores 8.0 points across all interpretations because Banaras Beads trades at 44.31x, well above R.K.'s multiple. However, the reported issuer P/E in telemetry was falsified by the 9.46 EPS.

### 4.3 P/B and `second_multiple = 211.07` Provenance
- In `derived.py:587`, `_issuer_pb = mcap / (equity + fresh)`.
- `mcap` was computed using contaminated shares: $82 \times 26,390,909 / 10^7 = \mathbf{₹216.405\text{ Crore}}$.
- `equity + fresh` = $(1616.22 + 3499.10) / 100 = \mathbf{₹51.1532\text{ Crore}}$.
- $\text{Issuer P/B} = 216.405 / 51.1532 = \mathbf{4.2305}$.
- Peer Banaras Beads P/B: **1.36** (RHP p. 168: CMP ₹119.20 / NAV ₹87.38).
- $\text{second\_multiple\_premium\_pct} = (4.2305 / 1.36 - 1) \times 100 = \mathbf{211.07\%}$.
- **Reconstruction with True R.K. Shares (15,516,763):**
  - True Mcap: $82 \times 15,516,763 / 10^7 = \mathbf{₹127.237\text{ Crore}}$.
  - True Issuer P/B: $127.237 / 51.1532 = \mathbf{2.487 \approx 2.49}$.
  - (Compare RHP p. 168: NAV at Cap Price = ₹34.14; $82 / 34.14 = \mathbf{2.40}$).
  - True Premium: $(2.487 / 1.36 - 1) \times 100 = \mathbf{+82.90\%}$.
- **Score Consequence:** Both $+211.07\%$ and $+82.90\%$ fall into the `else` band of `second_multiple` (score: 0.0 / 4.0 points).

### 4.4 Peer Semantics (Single Peer vs "Peer Median")
- RHP p. 168 contains exactly one listed peer: **Banaras Beads Limited**.
- In `derived.py`, `ctx.peers.median("pe")` computes the median of a single-element list `[44.31]`, returning `44.31`.
- While mathematically sound, reporting this in scorecard telemetry as "median VALID peer P/E" creates the semantic illusion of an industry-wide median. Under ICDR disclosure standards, this is a 1-to-1 single peer proxy.

---

## 5. Related-Party Transaction (RPT) Forensic

### 5.1 PDF Source Evidence
RHP pages 38 and 62 provide the statutory summary table:
- **Stub June 30, 2026:** RPT ₹160.56L / Revenue ₹749.28L = **21.43%**
- **FY 2025–26:** RPT ₹327.63L / Revenue ₹3,035.71L = **10.79%**
- **FY 2024–25:** RPT ₹108.49L / Revenue ₹1,777.19L = **6.10%**
- **FY 2023–24:** RPT ₹882.10L / Revenue ₹1,328.49L = **66.40%**

### 5.2 Contamination Source of 6.67%
- The value `6.67` currently entering the evaluation is nowhere in the R.K. RHP.
- It is identical to `fixtures/vishal_nirmiti/input.json:225` (`"rpt_pct_revenue": 6.67`), injected via `builder.py:260`.
- **Score Impact:**
  - `rpt` band rule: `< 5%` -> 3 pts; `<= 15%` -> 1 pt; `else` -> 0 pts.
  - At 6.67%, it scored 1.0 point.
  - At the true FY26 value of 10.79%, it still satisfies `<= 15%`, scoring **1.0 point**.
  - (Note: If evaluated against Stub June 2026 at 21.43%, it would score 0.0 points).

### 5.3 K6 Knockout Investigation (`rpt_pct_of_revenue_growth`)
- K6 triggers if `rpt_pct_of_revenue_growth > 40%`.
- Between FY25 and FY26: Total Revenue increased by ₹1,258.52L; Total RPT increased by ₹219.14L ($219.14 / 1258.52 = \mathbf{17.41\%}$).
- However, statutory RPT includes sales, raw material purchases, director remuneration, rent, and unsecured loans. The RHP does not disclose the exact share of revenue growth generated specifically by related parties.
- Therefore, `rpt_pct_of_revenue_growth` is genuinely UNKNOWN, and K6 evaluating to **UNVERIFIED** is mathematically and contractually correct under Kleene three-valued logic.

---

## 6. Auditor / EOM / CARO Forensic

### 6.1 Auditor Tenure and Opinion
- **Statutory Auditor:** M/s Murarka & Associates, Chartered Accountants (Partner: CA Sanjay Kumar Murarka, ICAI Peer Reviewed).
- **Tenure:** Audited all 3 restated financial years (FY24, FY25, FY26) and Stub June 2026.
- **Auditor Changes:** RHP p. 92 explicitly certifies: `"There has been no change in the Statutory Auditors of our Company during the last 3 years preceding the date of this Red Herring Prospectus."`
- **Audit Opinion:** RHP p. 36 and p. 292 certify that all audit reports were **unqualified with zero qualifications**.
- **CFO Resignations:** RHP p. 264 notes cessation of Mohammed Usman as Director on October 03, 2025 (transitioning to CEO), with MD Khurshid Alam serving as CFO. No CFO resignation within 2 years.

### 6.2 Provenance of `auditor = eom_only`
- A full-text search across all 496 pages of the RHP reveals **zero occurrences of "Emphasis of Matter"**.
- Why did the evaluator output `auditor_bucket = "eom_only"`?
- In `derived.py:1481-1493`:
  ```python
  if opinion == "unqualified" and reputed is True:
      return _v("auditor_bucket", "clean_reputed", ...)
  if opinion in ("emphasis_of_matter", "unqualified"):
      return _v("auditor_bucket", "eom_only", ...)
  ```
- Because Murarka & Associates is a regional firm rather than a Big-4 network, `auditor_reputed` is `False`.
- The engine's v1.5 categorization assigns non-reputed auditors with unqualified opinions to the `"eom_only"` bucket, which awards **1.0 / 2.0 points** (compared to 2.0 for `clean_reputed`).
- **Conclusion:** The evaluation of 1.0 point is correct according to the engine's categorical definition, but the label `"eom_only"` is a confusing misnomer in the telemetry, as no actual EOM remark exists.

---

## 7. Scanned-Page Forensic Audit

The restated financial annexures on PDF pages 294–318 were inspected:

| Statement / Note | PDF Pages | Text-Layer Status | Content Identified from Scanned Image / Alternative Text | Derivable Status |
| :--- | :---: | :---: | :--- | :---: |
| **Annexure I: Balance Sheet** | 294–296 | Image only (<20 chars) | Share Capital, Reserves, Total Borrowings, Trade Payables | Derivable from KPI table (p. 170) & Indebtedness (p. 356) |
| **Annexure II: Profit & Loss** | 297–299 | Image only (<20 chars) | Revenue, Expenses, EBITDA, PAT, Tax Expense | Fully extracted from KPI table (p. 169–170) |
| **Annexure III: Cash Flows** | 300–304 | Partial text (p. 300) | Operating Cash Flow (FY24 -7.13L, FY25 77.61L, FY26 114.72L) | Extracted from Cash Flow Summary (p. 379) |
| **Note 31: Related Parties** | 305–307 | Image only | Names of related parties, nature of transactions | Extracted from Summary Table (p. 38, p. 62) |
| **Note 33: Contingent Liabilities** | 308 | Image only | TDS default demand details | Fully verified via p. 38 and p. 362 text |
| **Trade Receivables Aging** | 309–312 | Image only | Debtor aging schedule | **UNKNOWN** (scanned, unextracted) |
| **CARO Disclosures** | 313–318 | Image only | Statutory auditor CARO clauses | **UNKNOWN** (scanned, unextracted) |

---

## 8. K5 Contingent-Liability Forensic

### 8.1 Actual Unit and Presentation
- Summary p. 38: `"There is an outstanding demand total of Rs. 800 including default of TDS for the years 2025-26 of Rs 360 and 2018-19 of Rs 440."`
- Detailed Litigation Table p. 362 (Header: `₹ in Lakhs`):
  - Category: `Direct Tax (TDS)`
  - Number of Cases: `02`
  - Total Amount: **`0.01 Lakhs`**
  - Details: `"There is an outstanding demand totalling Rs. 800 including default of TDS for the years 2025-26 (Rs 360) and 2018-19 (Rs 440)"`
- **Unit Finding:** The demand is literally **₹800 (eight hundred rupees)**, presented as **₹0.01 Lakhs**.

### 8.2 Comparison Against Net Worth and K5
- Latest Restated Net Worth (March 31, 2026): **₹1,616.22 Lakhs** (or June 30, 2026: ₹1,799.08 Lakhs).
- Ratio:
  $$\frac{\text{Contingent Liabilities}}{\text{Net Worth}} = \frac{0.01\text{ Lakhs}}{1,616.22\text{ Lakhs}} = 0.00000619 = \mathbf{0.000619\%} \ll 50\%$$
- All tax demands are quantified (GST Nil, Income Tax of Promoters Nil, Income Tax of Directors Nil).
- **Why K5 Evaluated to UNVERIFIED:** Because Note 33 at page 308 was a scanned raster image, `financials.contingent_liabilities` was unpopulated (`None`). Under Kleene logic, missing input forces K5 to **UNVERIFIED**. If 0.01 Lakhs were mapped, K5 would definitively resolve to **CLEAR**.

---

## 9. Use-of-Proceeds Contract Analysis

### 9.1 RHP Disclosures (p. 133–134)
- Working capital: ₹521.44 Lakhs
- Baruipur new plating facility: ₹880.37 Lakhs
- Ezra Street B2B showroom: ₹537.00 Lakhs
- Rash Behari Avenue B2C stores: ₹248.00 Lakhs
- Showroom inventory cost: ₹560.00 Lakhs
- **General Corporate Purposes (GCP):** `[●]`
- **Statutory Cap Clause (p. 134 Footnote):**
  `"* The amount utilized for general corporate purposes shall not exceed 15% of the Gross Proceeds of the Offer or ₹1000 lakhs whichever is less in accordance with SEBI ICDR regulations."`

### 9.2 Contract Semantics vs Interval Arithmetic
- Under pure interval arithmetic, since GCP is capped at $\le 15\%$ and there are no acquisitions ($0\%$), $(GCP + Unidentified) \le 15\% < 20\%$. Thus `blind_heavy` is mathematically impossible.
- Furthermore, Growth Capex = ₹1,665.37L / ₹3,499.10L = $47.59\% < 75\%$ (so it does not qualify for `growth`), which would make it `mixed_ok` (score: 2.0 / 4.0 points).
- **Engine Behavior & Contract Law:** Under v1.5 specification s3.2 and s13, the engine strictly forbids substituting legal caps when the RHP contains `[●]`. A missing amount makes the category share `None`, and `blind` evaluates to `None`, fail-closing `use_of_proceeds` to `UNKNOWN` (4.0 unknown points).
- **Conclusion:** The engine's current UNKNOWN status is contractually mandatory under the frozen core v1.5 specification.

---

## 10. Qualitative Field Contamination Audit

| Field | Current Canonical Value | PDF Text Extracted? | Provenance Classification |
| :--- | :---: | :---: | :--- |
| **`moat_rating`** | `"strong_niche"` | **NO** | **SUSPECT_CONTAMINATED** (injected by `builder.py:282` fallback from Vishal Nirmiti) |
| **`visibility_rating`** | `"strong"` | **NO** | **SUSPECT_CONTAMINATED** (injected by `builder.py:283` fallback from Vishal Nirmiti) |
| **`board_independent_majority`** | `False` | **YES** | **VERIFIED** (RHP p. 248: 7 total directors, 3 independent = 42.86% $\le$ 50%) |
| **`litigation_bucket`** | `"clean"` | **YES** | **VERIFIED** (RHP pp. 358–365: zero criminal/regulatory litigation) |
| **`top5_customer_pct`** | `11.11` | **YES** | **VERIFIED** (RHP p. 45: 11.11% in FY26) |
| **`industry_cagr_pct`** | `8.0` | **YES** | **VERIFIED** (RHP p. 192: Global Artificial Jewellery Market Report) |

---

## 11. Product Return Risk Coverage

- **Exact RHP Disclosure:** RHP page 72, Risk Factor 47:
  `"In the past, approximately 30% of the products have been returned due to various reasons, including defects, design concerns, or other customer-related issues. The Company offers a six-month exchange guarantee, under which customers are entitled to seek replacement of products found to be defective within the specified period from the date of purchase."`
- **Detailed Historical Returns (RHP p. 56, Risk Factor 16):**
  - FY24: ₹80.54L (6.14% of sales)
  - FY25: ₹86.48L (4.77% of sales)
  - FY26: ₹253.32L (7.84% of sales)
  - Stub June 2026: ₹64.85L (8.66% of sales)
- **Engine Classification:** **ONTOLOGY / MODEL COVERAGE GAP**. The v1.5 screening engine schema contains no property for product return rates, and the scoring model contains no penalty or criterion evaluating return/warranty risk. It has zero effect on the current score.

---

## 12. Complete Canonical Provenance Matrix

| Field Path | Current Value | Evaluator Use | Provenance Status | Contamination Risk | Correct Value / Status | Action Required |
| :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| `company_name` | `R.K. FASHION ACCESSORIES LIMITED` | Identity | **VERIFIED** | None | Same | None |
| `board` | `mainboard` | Rules | **INCORRECT_MAPPING** | Medium | `sme` | Fix parser |
| `issue.price_band_low` | `77.0` | Valuation | **VERIFIED** | None | 77.0 | None |
| `issue.price_band_high` | `82.0` | Valuation | **VERIFIED** | None | 82.0 | None |
| `issue.fresh_issue` | `3499.1` | Proceeds/Dilution | **VERIFIED** | None | 3499.10 | None |
| `issue.ofs` | `0.0` | Offer Structure | **VERIFIED** | None | 0.0 | None |
| `issue.fresh_shares` | `4267200` | Dilution | **VERIFIED** | None | 4267200 | None |
| `issue.post_issue_shares` | `26390909` | Dilution/P/B | **SUSPECT_CONTAMINATED** | **CRITICAL** | `15516763` | Remove fallback |
| `issue.pre_issue_shares` | `19800000` | Dilution | **SUSPECT_CONTAMINATED** | **CRITICAL** | `11249563` | Remove fallback |
| `issue.post_issue_eps` | `9.46` | P/E, PEG | **SUSPECT_CONTAMINATED** | **CRITICAL** | `4.05` | Remove fallback |
| `issue.lot_size` | `68` | Telemetry | **SUSPECT_CONTAMINATED** | **HIGH** | `1600` | Extract lot size |
| `financials.periods` | 3 FY periods | Financials (Mod A) | **VERIFIED** | None | FY24-26 verified | None |
| `peers` | Banaras Beads | Valuation (Mod B) | **VERIFIED** | None | Banaras Beads | None |
| `capital_structure.promoter_pre_pct` | `73.42` | Telemetry | **SUSPECT_CONTAMINATED** | **MEDIUM** | `99.67` | Remove fallback |
| `capital_structure.promoter_post_pct`| `72.25` | Governance (Mod D)| **VERIFIED** | None | 72.25 | None |
| `governance.rpt_pct_revenue` | `6.67` | Governance (Mod D)| **SUSPECT_CONTAMINATED** | **HIGH** | `10.79` | Extract from p. 38 |
| `governance.litigation_bucket` | `clean` | Governance (Mod D)| **VERIFIED** | None | clean | None |
| `governance.auditor_opinion` | `unqualified`| Governance (Mod D)| **VERIFIED** | None | unqualified | None |
| `business.top5_customer_pct` | `11.11` | Business (Mod E) | **VERIFIED** | None | 11.11 | None |
| `business.industry_cagr_pct` | `8.0` | Business (Mod E) | **VERIFIED** | None | 8.0 | None |
| `business.moat_rating` | `strong_niche` | Business (Mod E) | **SUSPECT_CONTAMINATED** | **HIGH** | `None` (UNKNOWN) | Remove fallback |
| `business.visibility_rating` | `strong` | Business (Mod E) | **SUSPECT_CONTAMINATED** | **HIGH** | `None` (UNKNOWN) | Remove fallback |

---

## 13. Floor / Ceiling Reconciliation

The dashboard values are 100% reproducible:
- **Base Score:** 64.0
- **Penalties Total:** -3.0 (`margin_spike` applied)
- **Unresolved Penalty Points:** 13.0 (from 5 unverified penalties: `receivable_days_up` 3.0, `auditor_cfo_exit` 3.0, `unreconciled_metrics` 2.0, `regulatory_dependence` 2.0, `eom_caro` 3.0)
- **Unknown Points:** 18.0
- **Floor (Lower Bound):**
  $$\text{Floor} = \text{Base} + \text{Penalties} - \text{Unresolved Penalties} = 64.0 + (-3.0) - 13.0 = \mathbf{48.0}$$
- **Ceiling (Upper Bound):**
  $$\text{Ceiling} = \text{Base} + \text{Unknown Points} + \text{Penalties} = 64.0 + 18.0 + (-3.0) = \mathbf{79.0}$$

---

## 14. Proven Corrected Fields

The following fields have indisputable mathematical and text grounding in the RHP:
1. `issue.post_issue_shares = 15516763` (RHP p. 107)
2. `issue.pre_issue_shares = 11249563` (RHP p. 106)
3. `issue.post_issue_eps = 4.05` (FY26 PAT ₹628.69L / 15,516,763 shares)
4. `issue.lot_size = 1600` (RHP p. 14, p. 102)
5. `capital_structure.promoter_pre_pct = 99.67` (RHP p. 126)
6. `governance.rpt_pct_revenue = 10.79` (RHP p. 38, p. 62)
7. `financials.contingent_liabilities = 0.01` (RHP p. 362)
8. `board = "sme"` (RHP p. 107)

---

## 15. Unresolved Fields

1. `business.moat_rating`: Requires qualitative heuristic extraction or external evaluation.
2. `business.visibility_rating`: Requires qualitative heuristic extraction or external evaluation.
3. `governance.rpt_pct_of_revenue_growth`: Unseparated in statutory disclosures (remains UNKNOWN, K6 UNVERIFIED).
4. `use_of_proceeds`: GCP amount undisclosed `[●]` (fail-closed UNKNOWN per spec s13).
5. `sector_ipo_relative`: Requires secondary market database of previous 4 sector IPOs.
6. `Module F (Market Signals)`: All 5 criteria remain genuine external unknowns.

---

## 16. Provisional Score Impact

### Scenario A: Proven Factual Fields Corrected (Qualitative Retained)
- `dilution` changes from True (1.0 pt) to False (0.0 pt) because true dilution is $27.50\% \ge 25.0\%$.
- All other criteria remain identical (`pe_vs_peers` stays 8.0, `second_multiple` stays 0.0, `rpt` stays 1.0).
- **Base Score:** 63.0 / 82.0
- **Final Score:** **60.0 / 100** (Floor: 47.0, Ceiling: 78.0, Completeness: 82.0%, Confidence: Medium).

### Scenario B: Proven Factual Fields Corrected + Unextracted Fallbacks Removed (Fail-Closed)
- `dilution` drops from 1.0 to 0.0 (-1.0 pt).
- `moat` drops from 3.0 to UNKNOWN (-3.0 pts scored, +5.0 unknown pts).
- `visibility` drops from 2.0 to UNKNOWN (-2.0 pts scored, +2.0 unknown pts).
- **Base Score:** 58.0 / 75.0 available
- **Final Score:** **55.0 / 100**
- **Unknown Points:** 25.0 points
- **Completeness %:** **75.0%**
- **Confidence Level:** **Low** (due to completeness < 80%)
- **Floor:** 42.0 | **Ceiling:** 80.0

---

## 17. Recommended Remediation Sequence

*Pending explicit authorization from engineering leadership:*
1. **Pass 1 — Fix Ingestion Schema & Default Gate:**
   Update `schema/ipo-input.v1.5.schema.json` to allow `issue.lot_size` to be `null` or extract SME lot size (1,600) so that `allow_fixture_fallbacks: bool = False` can be enforced across all production extractions without validation aborts.
2. **Pass 2 — Excise Fixture Fallbacks in `builder.py`:**
   Permanently remove the fallback constants `9.46`, `26390909`, `19800000`, `68`, `73.42`, `6.67`, `"strong_niche"`, and `"strong"` from `CanonicalInputBuilder`.
3. **Pass 3 — Implement Direct RHP Parsers:**
   Add dedicated regex extractors in `SectionExtractor` for:
   - Capital Structure share counts (pre-issue 11,249,563, fresh 4,267,200, post-issue 15,516,763).
   - Post-issue EPS computation from restated PAT and post-issue shares.
   - RPT summary percentage from RHP Section I (p. 38).
   - SME lot size from Section I / Issue Summary (p. 14).
4. **Pass 4 — Re-evaluate and Regenerate Artifacts:**
   Execute deterministic evaluation on clean inputs and update the golden regression suite.

---

## 18. Frozen-Core / Golden / Security Verification

- **Frozen Core:** Untouched. Zero edits to `derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`, and `extraction/price_band_notice.py`.
- **Vishal Nirmiti Golden Hash:** Verified bit-for-bit identical (`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`).
- **UI-7 Ingestion Security:** Verified intact. Zero public `reference_base_path` exposures.
- **Main Branch:** Completely untouched.
- **Working Tree:** No code modifications made during this investigation.
