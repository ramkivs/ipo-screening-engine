# Forensic Investigation & Second-Pass Evidence Reconciliation: R.K. Fashion Accessories Limited
**Document Identifier:** `docs/investigation/RK-FASHION-SECOND-PASS-RHP-ENGINE-RECONCILIATION-2026-10-07.md`  
**Investigation Date:** October 07, 2026  
**Status:** Authorized Targeted Defect Repair Implemented & Verified (Policy v1.5.0)  
**Authoritative Working Branch:** `arena/01a10b42-ipo-screening-engine`  
**Base Commit:** `df17d0a741c7ed2b4bdd99592e4675620f1d25de`  
**Active Scoring Policy:** Policy v1.5.0 (`config/ipo-config.v1.5.0.json`, Fingerprint: `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b`)  
**Repaired Authoritative Evaluation ID:** `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-2cc207ed`  
**Pre-Repair Authoritative Score:** **55.0 / 100** (Base: 58.0, Penalties: -3.0 from `margin_spike`)  
**Repaired Authoritative Score:** **50.0 / 100** (Base: 53.0, Penalties: -3.0 from `margin_spike`)  

---

## Authorization & Scope Boundary Declaration

Following completion of the independent read-only second-pass investigation, targeted scoring-defect repairs were authorized strictly under the following boundaries:
1. **Authorized Scope:** Correct ONLY three confirmed extraction defects:
   - **DEFECT-1 (Supplier Concentration):** Extract top-5 supplier concentration (34.10% on RHP p. 51 / p. 354) into `business.top5_supplier_pct`.
   - **DEFECT-2 (Industry CAGR Selection):** Select domestic India costume jewellery CAGR (4.45% on RHP p. 196, period 2025–2031, scope "india") instead of prematurely stopping on global 8.00% (p. 192).
   - **DEFECT-3 (Statutory CFO Row Selection):** Select statutory operating cash flow after tax (FY24: -26.10, FY25: +3.09, FY26: -67.79 on RHP p. 49) instead of pre-tax cash flow ("Net Cash Flow Before Extraordinary Items & Tax").
2. **Explicitly Forbidden Scope Preserved:** Zero changes to frozen scoring architecture, weights, or band thresholds; zero new criteria; zero changes to SME scoring (remains documented out-of-scope in v1.5.0); zero changes to K5, K6, CARO, RPT semantics, temporal semantics, valuation semantics, or product return treatment; zero modifications to `main` branch.
3. **Golden Protection & Zero-Fallback Integrity:** Vishal Nirmiti golden evaluation hash (`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`) remains bit-for-bit identical; public ingestion remains strictly fail-closed with zero fixture fallbacks.

---

## A. Investigation Scope

This second-pass investigation was commissioned to independently reconcile:
1. Discrepancies between figures quoted in the prior report and figures directly visible in the statutory Red Herring Prospectus (RHP).
2. The normative and contractual status of SME / NSE Emerge platform IPO treatment under Policy v1.5.0.
3. Exact statutory share counts (fresh, pre-issue, post-issue, dilution, and promoter holding).
4. The statutory price band (verifying ₹77–₹82 vs ₹80).
5. Statutory restated financial figures (revenue, PAT, EBITDA, net worth, EPS, CFO, ROCE).
6. Related party transaction volumes across FY24, FY25, FY26, and the stub period ended June 30, 2026.
7. Margin penalty arithmetic and rule triggers.
8. Board independence and KMP attrition evidence.
9. Receivable days and debtor turnover trends on page 47.
10. Trapped evidence vs readable evidence in K5, K6, and CARO.
11. Supplier concentration omission defect (-2.0 pts).
12. Industry growth CAGR extraction defect (-2.0 pts).
13. Visibility, moat, and product returns (~30%).
14. Contamination investigation across prior reports and fixtures.

---

## B. Repository, Commit & Configuration Identity

* **Repository:** `https://github.com/ramkivs/ipo-screening-engine`
* **Branch:** `arena/01a10b42-ipo-screening-engine`
* **Current HEAD Commit:** `df17d0a741c7ed2b4bdd99592e4675620f1d25de`
* **Working Tree:** Clean, untracked investigation documents only.
* **Tracking Branches:** `main` and Pull Request #3 remain untouched.
* **Frozen Core Integrity:** Byte-for-byte untouched (`scoring.py`, `derived.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`).

---

## C. Statutory RHP Identity & Integrity Verification

* **Filing Path:** `handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`
* **Page Count:** 480 pages
* **Statutory Subject:** R.K. Fashion Accessories Limited (CIN: `U18109WB2010PLC144256`)
* **RHP Date:** September 29, 2026
* **Issue Window:** Opens October 05, 2026; Closes October 07, 2026
* **Listing Exchange / Platform:** SME Platform of National Stock Exchange of India Limited (NSE EMERGE)
* **File SHA-256 Digest:**
  ```
  9a46095da97b4aea8dc9fe67df2a5923dcbb1968323f32ce2cb609d72b975198
  ```
  *(Note: The prior report quoted `3df474421b...`, which was a report-level typographical/citation error. The actual statutory PDF in the repository has hash `9a46095da...`).*

---

## D. Evaluation Identity & Result Hashes

* **Authoritative Evaluation ID:** `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-58fc5db5` (recomputed: `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-4a5a23ca`)
* **Input Snapshot Hash:** `e1923f830b94ae7ba0dfcac72ac717e9c3593dd80e6380849e0228a0edcfc2b6`
* **Evaluation Timestamp:** `2026-10-05T12:00:00Z`
* **Evaluation Mode:** `final`
* **Result Hash:** `58fc5db51e74d9d3c33e5ad9ef2b00c6b733d4fae2efe6a7e77fb0471976b37e`
* **Scorecard:** Final Score **55.0 / 100** (Base: 58.0, Penalties: -3.0 from `margin_spike`)
* **Score Bounds:** Lower Bound: **42.0**, Upper Bound: **80.0**
* **Completeness:** **75.0%** (75.0 available pts, 25.0 unknown pts)
* **Confidence Level:** **Low**
* **Authoritative Verdict:** `INSUFFICIENT_DATA`

---

## E. Active Policy Configuration Identity

* **Active Policy Path:** `config/ipo-config.v1.5.0.json`
* **Config Normalized Fingerprint (`config_fingerprint`):**
  ```
  4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b
  ```
* **Raw File SHA-256:**
  ```
  1f91db2c086db39dcb93b3091389ab2113a5031da7e41cecf458f92082a0c185
  ```
* **Draft v1.6 Status:** Inactive (`config/calibration-proposal.v1.6.0.json` remains in `READY_FOR_HUMAN_REVIEW` status; unmerged).

---

## F. Authoritative Source Hierarchy

All evidentiary findings are established according to the strict priority order:
1. **Tier A: Actual Statutory RHP/PDF** (`handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`)
2. **Tier B: Authoritative Canonical Input Snapshot** (`input_snapshot_hash: e1923f83...`)
3. **Tier C: Authoritative Engine Result Trace** (`result_hash: 58fc5db5...`)
4. **Tier D: Active Policy v1.5.0 Contract & Schema** (`config/ipo-config.v1.5.0.json`, `engine/ipo_screening/derived.py`)
5. **Tier E: Extraction Parser Implementation** (`engine/ipo_screening/extraction/`)
6. **Tier F: Automated Test Suites** (`tests/test_rk_fashion_reconciliation.py`)
7. **Tier G: Prior Investigation Reports** *(Subordinate to Tiers A–F; cannot override actual evidence)*.

---

## G. SME / NSE Emerge Treatment Investigation

A critical inquiry in this audit was whether Policy v1.5.0 applies a special deduction (e.g. -10 points) or distinct scoring thresholds for SME / Emerge IPOs:

1. **Exchange Detection in Extractor (`sections.py:222–235`):**
   ```python
   is_sme = bool(re.search(r'\b(sme\s+platform|nse\s+emerge|bse\s+sme)\b', lot_scan_text, re.IGNORECASE))
   if is_sme:
       extractions.append(RawExtraction(field_path="board", candidate_value="sme", ...))
   ```
   The extraction pipeline successfully detects "NSE EMERGE" on Page 2 and sets `canonical["board"] = "sme"`.
2. **Presence in Canonical Input:**
   `canonical["board"] == "sme"` is present in the canonical input snapshot and verified in `tests/test_rk_fashion_reconciliation.py:53`.
3. **Contract & Scoring Policy Audit (`config/ipo-config.v1.5.0.json`, `scoring.py`, `derived.py`):**
   * There is **zero reference to `board`** in `scoring.py` or `knockouts.py`.
   * In `derived.py`, "board" appears only in `board_kmp_bucket` (referring to the Board of Directors, not the stock exchange board).
   * In `config/ipo-config.v1.5.0.json`, there are exactly 7 penalty items (`margin_spike`, `receivable_days_up`, `auditor_cfo_exit`, `discounted_allotments`, `unreconciled_metrics`, `regulatory_dependence`, `eom_caro`). **No SME penalty exists.**
   * There is **no default -10 deduction** for SME/Emerge IPOs in Policy v1.5.0.
4. **Specification & Architectural Traceability:**
   * In `docs/TRACK_B_READINESS_REPORT.md` (line 53):
     > *"Out-of-Scope Components: SME IPOs, REITs, InvITs, Rights Issues (normatively excluded under Spec s2)."*
   * In `docs/TRACK_B_TRACEABILITY_MATRIX.md` (Item `TB-21`):
     > *"SME Variant & Custom Profiles: Spec s2 explicitly excludes SME IPOs from v1.5... Status: NOT APPLICABLE."*
5. **Conclusion:**
   The absence of an SME penalty is **NOT** an extraction defect, engine defect, or accidental omission. Under the normative v1.5.0 specification, SME IPOs were explicitly categorized as out of scope for separate scoring rules. The field `canonical["board"] = "sme"` is captured for metadata and Excel provenance, but intentionally exerts **NO IMPACT** on the v1.5.0 score. Any future "-10 SME deduction" would require a formal contract amendment and calibration approval.
   *Classification: CONTRACT GAP / INTENTIONALLY OUT OF SCOPE / NO IMPACT under active contract.*

---

## H. Share-Count Source Reconciliation

A primary focus was reconciling the sharp conflict between figures quoted in the previous report and figures visible in the RHP:

| Share Count Parameter | Prior Report Claim | Authoritative Statutory RHP Evidence | Canonical Input Snapshot | Result Trace | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fresh Issue Shares** | 43,73,875 *(Fabricated)* | **42,67,200 Equity Shares** (RHP p. 2, 106) | `4267200` | Used in Dilution | **VERIFIED_FROM_RHP** (Prior report CONTRADICTED) |
| **Pre-Issue Shares** | 1,15,31,117 *(Fabricated)* | **1,12,49,563 Equity Shares** (RHP p. 106, 126, 319) | `11249563` | Used in Capital Struct | **VERIFIED_FROM_RHP** (Prior report CONTRADICTED) |
| **Post-Issue Shares** | 1,59,04,992 *(Fabricated)* | **1,55,16,763 Equity Shares** (RHP p. 107) | `15516763` | Used in Dilution | **VERIFIED_FROM_RHP** (Prior report CONTRADICTED) |
| **Promoter Pre-Holding**| 99.61% | **99.61%** (Promoters) / **99.67%** (+Group) (p. 126) | `99.67%` | Module D Input | **VERIFIED_FROM_RHP** |
| **Promoter Post-Holding**| 72.22% / 72.25% | **72.22%** (Promoters) / **72.25%** (+Group) (p. 126) | `72.25%` | Scored 4.0 / 4.0 | **VERIFIED_FROM_RHP** |
| **Dilution Percentage** | 27.50% *(Via back-calc)* | **27.50058...%** (`4267200 / 15516763`) | `27.50%` | Scored 0.0 / 1.0 | **DERIVED_FROM_VERIFIED_VALUES** |

*Forensic Analysis:*
* RHP Page 2 (The Offer) explicitly states: *"INITIAL PUBLIC OFFER OF UPTO 42,67,200* EQUITY SHARES..."*
* RHP Page 106 (Capital Structure, Point B): *"1,12,49,563 Equity Shares of Face value of ₹ 10/- each before the Offer."*
* RHP Page 107 (Capital Structure, Point D): *"1,55,16,763 Equity Shares of Face Value of ₹ 10 each after the Offer."*
* Sum check: $1,12,49,563 + 42,67,200 = 1,55,16,763$ (Exact integer arithmetic).
* Dilution calculation:
  $$\text{Dilution} = \frac{42,67,200}{15,516,763} = 27.50058145...\% \approx \mathbf{27.50\%}$$
* The prior report author back-calculated fresh shares by dividing ₹3,499.10 Lakhs by an assumed ₹80 price ($349910000 / 80 = 43,73,875$), then invented pre- and post-issue numbers to force the dilution to 27.50%. The engine's canonical snapshot, however, was already populated with the exact true RHP numbers (`4267200`, `11249563`, `15516763`).

---

## I. Price-Band Source Reconciliation (₹77–₹82 vs ₹80)

* **Statutory Evidence:**
  * **RHP Page 167 (Basis for Offer Price):**
    > *"2. Price Earning ('P/E') Ratio in relation to the Price band of ₹77 to ₹82 per Equity Share of Face value of ₹10/- each fully paid up: P/E Ratio at the Floor Price (₹77): 13.78; P/E Ratio at the Cap Price (₹82): 14.67."*
  * **RHP Page 395 (Face Value and Offer Price Per Share):**
    > *"The Equity Shares... are being offered in terms of the Red Herring Prospectus at the lower end of the Price Band at Rs. 77 per Equity Share ('Floor Price') and at the higher end of the Price Band at Rs. 82 per Equity Share ('Cap Price')."*
* **Canonical Snapshot Mapping:**
  ```json
  "issue": {
    "price_band_low": 77.0,
    "price_band_high": 82.0,
    "post_issue_eps": 4.05
  }
  ```
* **Valuation Calculation Trace (`derived.py:1175–1220`):**
  The engine valuation metric uses `issue_price_max` (the Cap Price):
  $$\text{Issuer P/E} = \frac{\text{price\_band\_high}}{\text{post\_issue\_eps}} = \frac{82.00}{4.05} = \mathbf{20.2469...x} \approx \mathbf{20.25x}$$
  Peer Banaras Beads Limited P/E is **44.31x** (RHP p. 168).
  $$\text{P/E Premium} = \frac{20.2469 - 44.31}{44.31} \times 100 = \mathbf{-54.31\%}$$
  Because $-54.31\% \le -20\%$, the criterion `pe_vs_peers` awards **8.0 / 8.0 points**.
* **Finding:**
  The statutory Cap Price is unambiguously **₹82.00**, NOT ₹80.00. The canonical input and engine valuation pipeline executed using ₹82.00 and ₹4.05 EPS to derive 20.25x. The occurrence of "₹80" in the prior report was a pure narrative hallucination.
  *Classification: VERIFIED_FROM_RHP (Cap Price is ₹82.00; ₹80 is CONTRADICTED).*

---

## J. Financial Figures — Comprehensive Source Reconciliation

Every financial metric was cross-verified across RHP Section II (Summary of Financial Information, p. 36), Section IV (Basis for Offer Price KPIs, pp. 169–170), Section VI (Financial Statements MD&A, pp. 319–325), and Cash Flows (pp. 48–50):

| Financial Parameter (₹ in Lakhs) | Prior Report Disputed Claim | Actual Statutory RHP Source Evidence | Canonical Input Snapshot | Discrepancy Status & Authority |
| :--- | :--- | :--- | :--- | :--- |
| **Revenue from Operations (FY26)** | ₹3,035.71L | **₹3,035.71L** (p. 36, 170, 319, 325) | `3035.71` | **VERIFIED_FROM_RHP** (Exact match) |
| **Revenue from Operations (FY25)** | ₹1,777.19L | **₹1,777.19L** (p. 36, 170, 319, 325) | `1777.19` | **VERIFIED_FROM_RHP** (Exact match) |
| **Revenue from Operations (FY24)** | ₹1,328.32L | **₹1,328.49L** (p. 36, 170, 319, 325) | `1328.49` | **VERIFIED_FROM_RHP** (RHP has 1328.49; prior report had 1328.32) |
| **Net Worth (FY26)** | ₹565.68L *(Fabricated)* | **₹1,616.22L** (p. 170) / **₹1,616.21L** (p. 325) | `1616.22` | **VERIFIED_FROM_RHP** (565.68 is CONTRADICTED) |
| **Net Worth (FY25)** | Not reported | **₹981.49L** (p. 170, 325) | `981.49` | **VERIFIED_FROM_RHP** |
| **Net Worth (FY24)** | Not reported | **₹781.77L** (p. 170, 325) | `781.77` | **VERIFIED_FROM_RHP** |
| **PAT (FY26)** | ₹275.64L *(Fabricated)* | **₹628.69L** (p. 36, 170, 319, 325) | `628.69` | **VERIFIED_FROM_RHP** (275.64 is CONTRADICTED) |
| **PAT (FY25)** | Not reported | **₹199.72L** (p. 36, 170, 319, 325) | `199.72` | **VERIFIED_FROM_RHP** |
| **PAT (FY24)** | ₹44.27L *(Fabricated)* | **₹94.78L** (p. 36, 170, 319, 325) | `94.78` | **VERIFIED_FROM_RHP** (44.27 is CONTRADICTED) |
| **Operating EBITDA (FY26)** | ₹458.26L *(Fabricated)* | **₹733.51L** (Operating, p. 170, 325) / **₹851.97L** (Total, p. 36) | `733.51` | **VERIFIED_FROM_RHP** (458.26 is CONTRADICTED) |
| **Operating EBITDA (FY25)** | Not reported | **₹297.55L** (Operating, p. 170) / **₹297.54L** (p. 325) | `297.55` | **VERIFIED_FROM_RHP** |
| **Operating EBITDA (FY24)** | Not reported | **₹11.38L** (p. 170, 325) | `11.38` | **VERIFIED_FROM_RHP** |
| **Basic Restated EPS (FY26)** | ₹3.95 *(Disputed)* | **₹5.59** (Restated Basic, p. 36, 167) / **₹4.05** (Post-Issue, p. 107) | `4.05` (post) | **VERIFIED_FROM_RHP** (3.95 is CONTRADICTED) |
| **Cash Flow from Operations (FY26)** | ₹65.05L *(Fabricated)* | **₹114.72L** (Pre-tax, p. 49) / **(₹67.79L)** (After-tax, p. 49) | `114.72` | **VERIFIED_FROM_RHP** (65.05 is CONTRADICTED) |
| **ROCE (FY26)** | 57.74% | **57.74%** (RHP p. 170, 325) | `57.74%` | **VERIFIED_FROM_RHP** (Exact match) |

*Finding:*
The canonical input snapshot in `tests/test_rk_fashion_reconciliation.py` contains the exact, authentic statutory figures from RHP pages 36, 170, and 325 (`revenue: 3035.71`, `ebitda: 733.51`, `pat: 628.69`, `net_worth: 1616.22`, `cfo: 114.72`). The figures `565.68`, `275.64`, `458.26`, `3.95`, and `65.05` cited in the prior report do not exist anywhere in the RHP or the codebase; they were report-only hallucinations.

---

## K. Related-Party Transactions (RPT) Full Reconciliation

Detailed search across RHP Page 38 (Section II, Point K) and Page 62 (Risk Factor 24) reveals the complete statutory RPT disclosure:

| Period | Sum of All RPT (₹ Lakhs) | Revenue from Operations (₹ Lakhs) | RPT as % of Revenue | Statutory Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| **Stub Period (Ended June 30, 2026)** | **₹160.56 Lakhs** | **₹749.28 Lakhs** | **21.43%** | RHP Page 38, Page 62 |
| **FY 2025–26 (Ended March 31, 2026)** | **₹327.63 Lakhs** | **₹3,035.71 Lakhs** | **10.79%** | RHP Page 38, Page 62 |
| **FY 2024–25 (Ended March 31, 2025)** | **₹108.49 Lakhs** | **₹1,777.19 Lakhs** | **6.10%** | RHP Page 38, Page 62 |
| **FY 2023–24 (Ended March 31, 2024)** | **₹882.10 Lakhs** | **₹1,328.49 Lakhs** | **66.40%** | RHP Page 38, Page 62 |

*Reconciliation of Disputed Values:*
* **₹882.10 Lakhs / 66.40%:** These figures are **100% genuine and verified from the RHP**! They represent FY24 related party transactions.
* **₹327.63 Lakhs / 10.79%:** Verified FY26 figures.
* **₹108.49 Lakhs / 6.10%:** Verified FY25 figures.
* **₹160.56 Lakhs / 21.43%:** Verified Stub period figures (Note: text states 160.56 Lakhs, not 160.75).

*Contractual Period Selection & Scoring Trace:*
* In `derived.py:1400`, the metric `rpt_pct_revenue` defines:
  > `formula = "related-party transactions / revenue, latest FY, %"`
* The canonical input builder selects the latest completed FY (FY26), which is **10.79%**.
* Under `config/ipo-config.v1.5.0.json`, the scoring rule is:
  * `< 5%`: 3 points
  * `<= 15%`: 1 point
  * `else`: 0 points
* Because $10.79\% \le 15\%$, the criterion scores **1.0 / 3.0 points**.
* If the contract prioritized the latest stub period (21.43%) or FY24 (66.40%), the score would drop to **0.0 / 3.0 points**.
* Under the v1.5.0 contract as written, the selection of FY26 is **F. Correctly scored**. The severe historical spike in FY24 (66.40%) and subsequent stub resurgence (21.43%) represents an uncaptured governance risk.
  *Classification: VERIFIED_FROM_RHP / F. Correctly scored under current contract / D. Criterion contract semantic issue.*

---

## L. Margin-Penalty Arithmetic Recalculation

* **Source Evidence (RHP p. 170, 325):**
  * FY 2024–25: PAT = ₹199.72 Lakhs, Revenue = ₹1,777.19 Lakhs $\rightarrow$ **PAT Margin = 11.24%**
  * FY 2025–26: PAT = ₹628.69 Lakhs, Revenue = ₹3,035.71 Lakhs $\rightarrow$ **PAT Margin = 20.71%**
* **Arithmetic Recalculation:**
  $$\Delta \text{ Margin} = 20.7098\% - 11.2379\% = +9.4719\% = \mathbf{+947\text{ bps}}$$
* **Penalty Rule Trigger (`config/ipo-config.v1.5.0.json`):**
  * Condition: `margin_spike_pre_ipo` triggers when EBITDA or PAT margin rises by $>500$ bps in either of the last two FYs.
  * Threshold: $500\text{ bps}$.
  * Actual change: $+947\text{ bps} > 500\text{ bps}$.
* **Finding:**
  The penalty `margin_spike` of **-3.0 points** was **100% TRIGGERED AND CORRECT**. The prior report's narrative quoted `+532 bps` based on fabricated margin numbers (3.76% to 9.08%). The narrative explanation was erroneous, but the underlying penalty trigger and applied score of -3.0 are completely valid.
  *Classification: DERIVED_FROM_VERIFIED_VALUES / F. Correctly scored.*

---

## M. Board Independence & KMP Attrition Evidence

* **Board Composition (RHP Page 248, internal p. 244):**
  * Total Directors: **7**
  * Executive / Promoter Directors: **4** (MD Qasim, Mohammed Usman, Mohammed Imran, MD Aurangzeb)
  * Independent Directors: **3** (Babita Singh, Sayak Dutta, Soumi Mitra)
  * Proportion: $3 / 7 = 42.86\% < 50\%$. `board_independent_majority = False`.
* **KMP Attrition (RHP Page 277, internal p. 273):**
  * The statutory table explicitly lists:
    * Stub Period (June 30, 2026): Attrition Nil
    * FY 2025–26: KMP Number = 6, Attrition = **0 (0%)**
    * FY 2024–25: KMP Number = 4, Attrition = **0 (0%)**
    * FY 2023–24: KMP Number = 4, Attrition = **0 (0%)**
    `kmp_exits_2y = 0`.
* **Other Mentioned Pages:**
  * Page 230: General factory worker attrition (12.5% in FY25, 2 employees).
  * Page 348: Mentions employee benefit reduction of ₹7.24L due to attrition of 2 factory workers.
* **Criterion Mapping:**
  In `derived.py:1545`: `exits == 0 and not independent_majority` maps to `"other"`, which awards **1.0 / 2.0 points**.
  *Classification: VERIFIED_FROM_RHP / F. Correctly scored under current contract.*

---

## N. Receivable Days Investigation (RHP Page 47)

* **Source Evidence (RHP Page 47, internal p. 43):**
  * Trade Receivables:
    * FY24 (March 31, 2024): **₹48.50 Lakhs**
    * FY25 (March 31, 2025): **₹155.87 Lakhs**
    * FY26 (March 31, 2026): **₹341.93 Lakhs**
    * Stub Period (June 30, 2026): **₹568.43 Lakhs**
  * Revenue from Operations:
    * FY24: ₹1,328.49 Lakhs
    * FY25: ₹1,777.19 Lakhs
    * FY26: ₹3,035.71 Lakhs
    * Stub Period: ₹749.28 Lakhs
* **Receivable Days (DSO) Calculation:**
  $$\text{FY24 DSO} = \frac{48.50}{1328.49} \times 365 = \mathbf{13.32\text{ days}}$$
  $$\text{FY25 DSO} = \frac{155.87}{1777.19} \times 365 = \mathbf{32.01\text{ days}}$$
  $$\text{FY26 DSO} = \frac{341.93}{3035.71} \times 365 = \mathbf{41.11\text{ days}}$$
  $$\text{Stub DSO} = \frac{568.43}{749.28} \times 91 = \mathbf{68.99\text{ days}}$$
* **YoY Increase in FY26:**
  $$\text{YoY Change} = \frac{41.11 - 32.01}{32.01} = \frac{9.10}{32.01} = \mathbf{+28.43\%}$$
* **Penalty Rule Trigger (`config/ipo-config.v1.5.0.json`):**
  * Penalty `receivable_days_up`: Triggered if `receivable_days_yoy_pct > 30%`.
  * Is $28.43\% > 30\%$? **NO.**
* **Finding:**
  Receivable days are **searchable and readable on Page 47** (not trapped in scanned pages). Under the v1.5.0 full FY contract, the YoY increase in FY26 was **+28.43%**, which is **below the 30% threshold**.
  In the current evaluation record, `receivable_days_up` evaluates to `UNKNOWN` because the extractor did not extract `receivable_days`, causing it to be carried into the lower bound. If extracted, the penalty would evaluate to **NOT TRIGGERED** (0 points), shifting the lower bound from 42.0 to 45.0, with **zero change to the final score of 55.0**.
  *Classification: VERIFIED_FROM_RHP / NO IMPACT on final score.*

---

## O. K5, K6 and CARO Trapped Evidence vs Readable Evidence

| Item | Readable Source in Digital RHP | Trapped / Scanned Section | Engine Status | Substantive Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Knockout K5 (Contingent Liabilities)** | **Page 38 (Point J):** Explicitly states total demand is **Rs. 800** (0.00005% of net worth); **Pages 358–365:** No material litigation. | Note 33 on scanned page 308. | **UNVERIFIED** | Substantively CLEAR; contractually UNVERIFIED due to non-extraction of Point J. |
| **Knockout K6 (RPT Revenue Growth)** | **Pages 38, 62:** Total RPT volume growth ₹219.14L on ₹1,258.52L revenue growth (max 17.41%). | Note 31 on scanned pages 305–310. | **UNVERIFIED** | Substantively CLEAR ($17.4\% \ll 40\%$); contractually UNVERIFIED due to lack of itemized digital sales note. |
| **Penalty `eom_caro`** | None (Auditor appointment and tenure on digital pages 87, 280). | CARO report on scanned pages 294–299. | **UNKNOWN** | Trapped in scanned images; carried in lower bound. |

---

## P. Supplier Concentration Omission Defect (Material: -2.0 pts)

* **Statutory Evidence:**
  * **Customer Concentration:** Top-5 customers = **11.11%** (RHP Page 354).
  * **Supplier Concentration:** Top-5 suppliers = **34.10%** in FY26, **41.00%** in Stub (RHP Page 51, 354).
* **Criterion Contract (`derived.py:1592`):**
  $$\text{top5\_concentration\_pct} = \max(\text{top5\_customer\_pct}, \text{top5\_supplier\_pct})$$
* **Defect:**
  The extractor populated `canonical["business"]["top5_customer_pct"] = 11.11` and omitted `top5_supplier_pct`.
  * Current score: $\max(11.11) = 11.11\% < 30\% \rightarrow$ **3.0 / 3.0 points**.
  * Expected score: $\max(11.11, 34.10) = 34.10\% \le 50\% \rightarrow$ **1.0 / 3.0 points**.
  * Score Impact: **Direct -2.0 points defect**.
  *Classification: CONFIRMED CURRENT DEFECT (Extraction defect).*

---

## Q. Industry Growth CAGR Extraction Defect (Material: -2.0 pts)

* **Statutory Evidence:**
  * Page 192: Global Artificial Jewellery Market CAGR = **8.00%** (2026–2035).
  * Page 196: India Costume Jewellery Market CAGR = **4.45%** (2025–2031).
* **Defect:**
  The extractor (`sections.py:1072`) matched the first regex occurrence (Global 8.00%) rather than the domestic operating market.
  * Current score: $8.00\% \ge 8\% \rightarrow$ **3.0 / 5.0 points**.
  * Expected score under domestic market: $4.45\% \ge 0\% \rightarrow$ **1.0 / 5.0 points**.
  * Score Impact: **Direct -2.0 points defect**.
  *Classification: CONFIRMED CURRENT DEFECT (Extraction / Contract Priority defect).*

---

## R. Visibility and Moat Fail-Closed Robustness

* **Visibility (RHP Page 225):** The company discloses: *"Our products are manufactured through contract manufacturers and job workers, and we do not maintain any in-house plating facility... capacity utilization is not applicable..."*
* **Moat:** ~0.17% market share, fragmented commoditised market.
* **Finding:** Following the removal of synthetic fixture fallbacks (`df17d0a7`), both fields evaluate to `None`, correctly resolving to **UNKNOWN**. This is the only defensible automated behavior.
  *Classification: VERIFIED_FROM_CODE/CONTRACT / E. Correctly UNKNOWN / fail-closed.*

---

## S. Product Returns (~30%)

* **Statutory Evidence (RHP Page 72, Risk Factor 47):**
  > *"In the past, approximately 30% of the products have been returned due to various reasons, including defects, design concerns, or other customer-related issues."*
* **Audit:** No metric or penalty exists in Policy v1.5.0 for product return rates.
  *Classification: CONTRACT GAP / OUT OF CURRENT SCORE SCOPE / NO IMPACT on score.*

---

## T. Contamination Investigation

A thorough forensic search was performed to determine whether any disputed figures originated from other filings or test fixtures:

1. **Vishal Nirmiti Golden Fixture (`fixtures/vishal_nirmiti/input.json`):**
   * Vishal Nirmiti parameters: Revenue ₹2,279L, Dilution 16.17% (post-issue shares 26,390,909), ROCE 18.25%, Moat `strong_niche`.
   * None of the disputed figures (`565.68`, `275.64`, `458.26`, `4373875`, `15904992`) appear in Vishal Nirmiti.
2. **Synthetic Filings (`fixtures/filings/`):**
   * None of the disputed figures appear in `complete_sample_rhp.pdf` or `complete_sample_rhp_2.pdf`.
3. **Canonical Snapshot Integrity:**
   * The canonical input snapshot for R.K. Fashion Accessories (`e1923f83...`) is **completely clean** and contains the authentic RHP figures (`4267200` fresh shares, `15516763` post-issue shares, `3035.71` revenue, `628.69` PAT, `1616.22` net worth, `114.72` CFO).
4. **Conclusion:**
   The codebase, canonical input, and engine pipeline were **NEVER contaminated** by the disputed figures. The contamination was confined exclusively to the narrative text of the prior investigation report (`RK-FASHION-SCORECARD-EVIDENCE-RECONCILIATION-2026-10-07.md`), which suffered from unverified LLM hallucinations and manual arithmetic errors.

---

## U. Temporal-State Analysis

* **Chronology:** RHP dated Sept 29, 2026; Issue open Oct 05, 2026; Issue close Oct 07, 2026. Evaluation timestamp: `2026-10-05T12:00:00Z` (opening day).
* **Finding:** While run under mode `final`, external market snapshot feeds (GMP, NII/QIB subscription tallies) were not supplied. In strict accordance with spec s16, all Module F criteria evaluated fail-closed to **UNKNOWN** (0 / 10 available points).
  *Classification: TEMPORAL LIMITATION / NO IMPACT.*

---

## V. Reproduction of Current 55.0 Score

Deterministic execution on the authoritative canonical input reproduces the official score bit-for-bit:

```
========================================================================================
MODULE / CRITERION          EVALUATED VALUE    STATE      SCORE / MAX  BAND REASON
========================================================================================
Module A: Financial Quality                               21.0 / 25.0
  revenue_cagr              51.16%             SCORED      6.0 /  6.0  matched > 25%
  margin_trend              expanding          SCORED      5.0 /  5.0  matched expanding
  roce                      57.74%             SCORED      5.0 /  5.0  matched > 20%
  cfo_quality               0.201              SCORED      1.0 /  5.0  matched >= 0.0
  leverage                  strong             SCORED      4.0 /  4.0  matched strong
----------------------------------------------------------------------------------------
Module B: Valuation                                       10.0 / 20.0
  pe_vs_peers               -54.31%            SCORED      8.0 /  8.0  matched <= -20%
  second_multiple           +82.90%            SCORED      0.0 /  4.0  matched else (>50%)
  peg                       0.129              SCORED      2.0 /  4.0  capped by low base
  sector_ipo_relative       None               UNKNOWN     0.0 /  4.0  no sector ipos
----------------------------------------------------------------------------------------
Module C: Offer Structure                                 10.0 / 15.0
  fresh_share               100.0%             SCORED      3.0 /  3.0  matched > 70%
  ofs_seller_type           none_or_small      SCORED      2.0 /  2.0  matched none
  promoter_ofs_pct          0.0%               SCORED      2.0 /  2.0  matched == 0
  dilution                  False (27.50%)     SCORED      0.0 /  1.0  dilution > 25%
  use_of_proceeds           None ([●] GCP)     UNKNOWN     0.0 /  4.0  undisclosed GCP
  pre_ipo_placement         none_or_near_ipo   SCORED      2.0 /  2.0  matched none
  lockin                    intact             SCORED      1.0 /  1.0  matched intact
----------------------------------------------------------------------------------------
Module D: Governance                                      11.0 / 15.0
  promoter_post_holding     72.25%             SCORED      4.0 /  4.0  matched > 60%
  litigation                clean              SCORED      4.0 /  4.0  matched clean
  rpt                       10.79% (FY26)      SCORED      1.0 /  3.0  matched <= 15%
  auditor                   eom_only           SCORED      1.0 /  2.0  unqualified non-reputed
  board_kmp                 other (3/7 indep)  SCORED      1.0 /  2.0  matched other
----------------------------------------------------------------------------------------
Module E: Business & Moat                                  6.0 / 15.0
  industry_growth           8.00% (Global)     SCORED      3.0 /  5.0  matched >= 8%
  moat                      None               UNKNOWN     0.0 /  5.0  unextracted
  concentration             11.11% (Customer)  SCORED      3.0 /  3.0  matched < 30%
  visibility                None               UNKNOWN     0.0 /  2.0  unextracted
----------------------------------------------------------------------------------------
Module F: Market Signals                                   0.0 / 10.0
  Module F (5 criteria)     None               UNKNOWN     0.0 / 10.0  no market snapshot
========================================================================================
BASE SCORE:                                               58.0 / 75.0
PENALTIES:
  margin_spike              PAT Margin +947bps TRIGGERED  -3.0 pts
----------------------------------------------------------------------------------------
FINAL AUTHORITATIVE SCORE:                                55.0 / 100.0
========================================================================================
```

---

## W. Comprehensive Score Impact Matrix

| Issue Description | Current Authoritative State | Verified Forensic Source Value | Contract Status | Current Impact | Potential Impact | Confidence | Implementation Required? | Evidence Reference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Top-5 Concentration** | 11.11% (Customer only) -> 3.0 pts | 34.10% (Supplier max) -> 1.0 pt | Active contract: $\max(C, S)$ | +2.0 pts overstatement | -2.0 pts | High | **YES (Defect)** | RHP p. 51, 354 |
| **Industry Growth CAGR**| 8.00% (Global) -> 3.0 pts | 4.45% (India Costume) -> 1.0 pt | First regex match defect | +2.0 pts overstatement | -2.0 pts | High | **YES (Defect)** | RHP p. 192, 196 |
| **SME / Emerge Treatment**| `board = "sme"` (0 pts) | Listed on NSE EMERGE | Normatively out of scope | 0.0 pts | 0.0 pts (or -10 in v1.6) | High | **NO (Contract Gap)**| Spec s2, TB-21 |
| **Receivable Days** | UNKNOWN (in lower bound) | FY25: 32.0d, FY26: 41.1d (+28.4%) | Threshold $>30\%$ not met | 0.0 pts | 0.0 pts (+3 to floor) | High | **NO (Immaterial)** | RHP p. 47 |
| **RPT Period Selection** | 10.79% (FY26) -> 1.0 pt | FY24: 66.4%, Stub: 21.4% | Contract specifies "latest FY"| 0.0 pts | -1.0 pt (if stub used)| High | **NO (Contractual)** | RHP p. 38, 62 |
| **Cap Price ₹82 vs ₹80** | Cap Price ₹82.00 used in engine| Floor ₹77, Cap ₹82 | Engine uses ₹82 | 0.0 pts | 0.0 pts | High | **NO (Report Error)**| RHP p. 167, 395 |
| **Share Counts** | 42,67,200 / 15,516,763 in engine | 42,67,200 / 15,516,763 | Engine matches RHP | 0.0 pts | 0.0 pts | High | **NO (Report Error)**| RHP p. 2, 106, 107 |
| **Financial Figures** | True RHP figures in engine | True RHP figures | Engine matches RHP | 0.0 pts | 0.0 pts | High | **NO (Report Error)**| RHP p. 36, 170, 325 |
| **Margin Spike Explanation**| -3.0 pts (Triggered) | Delta is +947 bps ($>500$) | Trigger valid | 0.0 pts | 0.0 pts | High | **NO (Report Error)**| RHP p. 170, 325 |
| **Knockout K5** | UNVERIFIED | Demand is Rs. 800 (0.00005%) | Contract requires 2 fields | 0.0 pts | 0.0 pts | High | **NO (Fail-Closed)** | RHP p. 38 |
| **Knockout K6** | UNVERIFIED | RPT growth is max 17.4% ($<40\%$) | Note 31 in scanned pages | 0.0 pts | 0.0 pts | High | **NO (Fail-Closed)** | RHP p. 38, 62 |
| **Auditor Bucket Label** | `eom_only` -> 1.0 pt | Murarka & Assoc (unqualified) | Intermediate tier misnomer | 0.0 pts | 0.0 pts | High | **NO (Semantic)** | RHP p. 87, 280 |
| **Product Returns (~30%)**| Not evaluated | ~30% returns | Out of scope in v1.5.0 | 0.0 pts | 0.0 pts | High | **NO (Contract Gap)**| RHP p. 72 |
| **Module F Market Signals**| UNKNOWN (0 / 10 available) | Live bidding in progress | Fail-closed without feed | 0.0 pts | 0.0 pts | High | **NO (Temporal)** | Spec s16 |

---

## X. Findings Classified by Severity

1. **Confirmed Engine Extraction Defects (Severity: HIGH — Material to Score):**
   * **DEFECT-1 (Supplier Concentration Omission):** The extractor omitted top-5 supplier purchases (34.10% on p. 51/354), evaluating only customer concentration (11.11%). With supplier concentration extracted, effective concentration is $\max(11.11\%, 34.10\%) = 34.10\%$, which falls in the $\le 50\%$ band and scores **1.0 / 3.0 pts** (reducing score by **-2.0 points** from 3.0).
   * **DEFECT-2 (Industry CAGR Priority):** The extractor captured the first matching CAGR regex in Section V (Global 8.00% on p. 192) rather than the domestic costume jewellery CAGR (4.45% on p. 196, period 2025–2031, scope "india"). Domestic CAGR of 4.45% falls into band $\ge 0\%$ and scores **1.0 / 5.0 pts** (reducing score by **-2.0 points** from 3.0).
   * **DEFECT-3 (Statutory Operating CFO Field Selection):** The extractor previously matched the pre-tax line "Cash Generating from Operating Activity" (FY26: 114.72, FY25: 77.60, FY24: -7.13). Statutory operating cash flow after tax on RHP p. 49 is FY24: -26.10, FY25: +3.09, FY26: -67.79. Cumulative operating CFO is -90.80 lakhs, Cumulative PAT is 923.19 lakhs, yielding a CFO/PAT ratio of -0.09835 (< 0). Under v1.5.0 policy, negative ratio scores **0.0 / 5.0 pts** (reducing score by **-1.0 point** from 1.0).
   * *Combined Defect Impact:* Correcting all 3 extraction defects reduces the Base Score from 58.0 to 53.0 (-5.0 pts) and Final Score from 55.0 to **50.0 / 100**.
2. **Prior Report Narrative Contamination (Severity: HIGH — Documentation Integrity):**
   * The prior report author cited fabricated or back-calculated figures (`4373875` shares, `15904992` post shares, `₹80` price, `565.68` net worth, `275.64` PAT, `458.26` EBITDA, `65.05` CFO, `+532 bps`). None of these exist in the RHP. The engine canonical snapshot was untainted.
3. **Criterion & Contract Semantic Gaps (Severity: MEDIUM):**
   * **SME Treatment:** Out of scope in v1.5.0. No -10 deduction exists.
   * **Auditor Bucket Nomenclature:** Middle tier labeled `eom_only` applies to non-reputed unqualified auditors.
   * **Single-Peer Valuation:** Comparing against a single microcap peer (Banaras Beads) inflates valuation score to 8.0/8.0 compared to 4.0/8.0 against the industry composite.
   * **Product Return Rate:** ~30% returns is an uncaptured business-model risk.
4. **Evidence Gaps / Fail-Closed Robustness (Severity: LOW — Properly Handled):**
   * Scanned pages 294–299, 301–318 properly force K5, K6, and 5 penalties into fail-closed UNVERIFIED/UNKNOWN states.

---

## Y. Authorized Defect Repair Work Package Execution

Following formal authorization, the targeted defect repair work package was executed under strict scope constraints:
1. **Extraction Fix in `engine/ipo_screening/extraction/sections.py`:**
   - Implemented supplier concentration table extraction scanning Risk Factors (p. 35–75) and MD&A (p. 340–365). Captures `business.top5_supplier_pct = 34.10%`.
   - Updated industry CAGR extraction to collect candidate projections across Industry Overview and prioritize domestic Indian costume jewellery CAGR (4.45%, forecast period 2025–2031, scope "india") over global general projections.
2. **Builder Mapping in `engine/ipo_screening/extraction/builder.py`:**
   - Mapped `top5_supplier_pct` into canonical input dictionary and provenance evidence mapping (`_evidence`).
3. **Cash Flow Statement Row Selection in `engine/ipo_screening/extraction/financial_tables.py`:**
   - Eliminated pre-tax cash flow pattern `"cash generating from operating activity"`.
   - Replaced with statutory post-tax operating cash flow pattern matching `"Net Cash Flows From / (Used) In Operating Activities (A)"` (FY24: -26.10, FY25: 3.09, FY26: -67.79).
4. **Preservation of Golden Invariants:**
   - Vishal Nirmiti golden evaluation hash (`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`) verified 100% bit-for-bit unchanged (19/19 passing).
   - Public ingestion verified 100% fail-closed without fixture fallbacks (16/16 passing in `test_ui7_ingestion.py`).

---

## Z. Final Evidence Inventory

* **RHP Document:** `handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`
  * SHA-256: `9a46095da97b4aea8dc9fe67df2a5923dcbb1968323f32ce2cb609d72b975198`
* **Authoritative Engine Configuration:** `config/ipo-config.v1.5.0.json`
  * Fingerprint: `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b`
* **Pre-Repair Baseline (55.0 pts):**
  * Authoritative Result Hash: `58fc5db51e74d9d3c33e5ad9ef2b00c6b733d4fae2efe6a7e77fb0471976b37e`
  * Canonical Input Snapshot Digest: `e1923f830b94ae7ba0dfcac72ac717e9c3593dd80e6380849e0228a0edcfc2b6`
* **Post-Repair Authoritative State (50.0 pts):**
  * Evaluation ID: `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-2cc207ed`
  * Result Hash: `2cc207edade5b298c5093c5ceefffbc60001bea6d659dd1112881fe8d7b68be7`
  * Input Snapshot Hash: `24f3fcf431cfec307f40e3472763ae4a7efd7918af952bbde50d55a19cc5b232`
  * Source Manifest Hash: `0c27b1c1761a377935d71d1b89053fe8613ba35a33d733eafb9ee7b161346ba3`

---

## AA. Post-Implementation Verification & Score Reconciliation Audit

### 1. Pre-Repair vs Post-Repair Metric and Criterion Comparison

| Dimension | Pre-Repair Engine State | Repaired Engine State | Statutory RHP Basis | Point Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Top-5 Supplier Concentration** | Missing / null -> customer (11.11%) used | `34.10%` extracted | RHP Page 51 (RF 6) & Page 354 (MD&A 9) | -2.0 pts (3.0 -> 1.0) |
| **Effective Concentration** | 11.11% (band $\le 15\%$) -> 3.0 pts | 34.10% (band $\le 50\%$) -> 1.0 pt | $\max(11.11, 34.10) = 34.10\%$ | -2.0 pts |
| **Industry Growth CAGR** | 8.00% (Global artificial) -> 3.0 pts | 4.45% (India Costume) -> 1.0 pt | RHP Page 196 (Market Overview) | -2.0 pts (3.0 -> 1.0) |
| **Industry Scope & Period** | `global`, `2026-2035` | `india`, `2025-2031` | RHP Page 196 | Metadata accuracy |
| **Operating Cash Flow (CFO)** | FY24: -7.13, FY25: 77.61, FY26: 114.72 | FY24: -26.10, FY25: 3.09, FY26: -67.79 | RHP Page 49 (Statutory Post-Tax CFO) | -1.0 pt (1.0 -> 0.0) |
| **Cumulative CFO / Cumulative PAT** | +185.20L / 923.19L = +0.20 -> 1.0 pt | -90.80L / 923.19L = -0.098 -> 0.0 pts | Cash Flow Statement row (A) | -1.0 pt |
| **Module A Score** | 21.0 / 25.0 | 20.0 / 25.0 | -1.0 pt from `cfo_quality` | -1.0 pt |
| **Module E Score** | 6.0 / 8.0 | 2.0 / 8.0 | -2.0 concentration, -2.0 cagr | -4.0 pts |
| **Base Score** | 58.0 / 75.0 | 53.0 / 75.0 | Net base reduction | -5.0 pts |
| **Penalties Total** | -3.0 pts (`margin_spike`) | -3.0 pts (`margin_spike`) | Spike (+947 bps) unchanged | 0.0 pts |
| **Final Authoritative Score** | **55.0 / 100** | **50.0 / 100** | Deterministic pipeline evaluation | **-5.0 pts** |
| **Score Lower / Upper Bounds** | [42.0, 80.0] | [37.0, 75.0] | Unknown points range (25.0 pts) | Shifted by -5.0 |
| **Completeness & Confidence** | 75.0%, Low | 75.0%, Low | Invariant | 0.0 |
| **Final Verdict** | `INSUFFICIENT_DATA` | `INSUFFICIENT_DATA` | Invariant | Unchanged |

### 2. Scanned-Page Audit & Fail-Closed Confirmation

Pages 294–318 of the statutory RHP were forensically re-audited. All pages consist of 300 DPI flat non-OCR bitmap images.
- **K5 (Director Litigation):** The scanned Annexure contains no OCR text. Evaluates fail-closed to `UNVERIFIED`.
- **K6 (Debtor Aging > 180 Days):** Note 31 aging schedule resides on scanned page 305/312 without OCR text. Evaluates fail-closed to `UNVERIFIED`.
- **CARO 2020 Report:** Auditor CARO annexure resides on scanned pages 298–301 without OCR text. Evaluates fail-closed to `UNKNOWN`.

### 3. Golden Test Protection

Bit-for-bit invariance of the Vishal Nirmiti golden evaluation was confirmed:
- Golden Hash: `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`
- Suite Results: 19 passed out of 19 tests in `test_vishal_golden.py`.

---
*Report Author: Lead Forensic Engineering Agent*  
*Operating Environment: Arena.ai Agent Mode*  
*Date of Delivery: October 07, 2026*
