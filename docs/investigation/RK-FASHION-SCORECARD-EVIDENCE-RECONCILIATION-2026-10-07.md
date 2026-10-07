# Forensic Scorecard & Evidence Reconciliation: R.K. Fashion Accessories Limited
**Document Identifier:** `docs/investigation/RK-FASHION-SCORECARD-EVIDENCE-RECONCILIATION-2026-10-07.md`  
**Investigation Date:** October 07, 2026  
**Authoritative Operating Branch:** `arena/01a10b42-ipo-screening-engine`  
**Authoritative Head Commit:** `df17d0a741c7ed2b4bdd99592e4675620f1d25de`  
**Active Scoring Policy:** `config/ipo-config.v1.5.0.json` (SHA-256: `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b`)  
**Evaluation Identifier:** `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-58fc5db5`  
**Target Subject:** R.K. Fashion Accessories Limited (CIN: `U18109WB2010PLC144256`)  
**Filing Analyzed:** Red Herring Prospectus (RHP) dated September 29, 2026 (NSE EMERGE SME IPO)  

---

## Non-Implementation Boundary Declaration

This document constitutes a strict, read-only forensic investigation and reconciliation report. In compliance with the operational boundaries governing this review:
1. **Zero Implementation Modifications:** No modifications have been made to engine source code (`engine/ipo_screening/`), scoring models, extraction heuristics, JSON schemas, policy configuration files, automated test suites, or golden snapshot fixtures.
2. **Authoritative Score Invariant:** The authoritative screening score for R.K. Fashion Accessories Limited under Policy v1.5.0 remains **55.0 / 100** (Base Score: 58.0, Applied Penalties: -3.0 from `margin_spike`). Any alternate numerical derivations presented in this document are explicitly designated as **non-authoritative hypothetical scenario models** for calibration and analytical clarity.
3. **Repository State:** The Git repository working tree remains clean, synchronized with `origin/arena/01a10b42-ipo-screening-engine`, with branches `main` and Pull Request #3 untouched.

---

## 1. Baseline Integrity & Evaluation Provenance

Deterministic execution of the zero-fallback extraction and evaluation pipeline on the statutory Red Herring Prospectus yields the following immutable evaluation baseline:

| Metadata Dimension | Authoritative Value / Digest |
| :--- | :--- |
| **Git Working Branch** | `arena/01a10b42-ipo-screening-engine` |
| **Head Commit Hash** | `df17d0a741c7ed2b4bdd99592e4675620f1d25de` |
| **Synchronization Status** | Clean working tree, fully synchronized with remote |
| **Engine Configuration** | `config/ipo-config.v1.5.0.json` |
| **Config SHA-256 Digest** | `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b` |
| **Evaluation ID** | `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-58fc5db5` |
| **Evaluation Mode** | `final` |
| **Evaluation Timestamp** | `2026-10-05T12:00:00Z` |
| **Result SHA-256 Hash** | `58fc5db51e74d9d3c33e5ad9ef2b00c6b733d4fae2efe6a7e77fb0471976b37e` |
| **Input Snapshot Hash** | `e1923f830b94ae7ba0dfcac72ac717e9c3593dd80e6380849e0228a0edcfc2b6` |
| **Source Manifest Hash** | `dbb8f47274b0bcf7eb6363e707c860436a95237d660cf0a565ffc5770f859ef5` |
| **Market / Peer Snapshot** | `None` / `None` (Deterministic fail-closed behavior) |
| **Final Score** | **55.0 / 100** |
| **Base Score** | **58.0 / 75.0** (Available evaluable points: 75.0) |
| **Penalties Applied** | **-3.0** (`margin_spike`: margin up >500 bps YoY in FY26) |
| **Score Bounds** | Lower Bound: **42.0**, Upper Bound: **80.0** |
| **Data Completeness** | **75.0%** (75.0 / 100.0 evaluable points, 25.0 points UNKNOWN) |
| **Engine Confidence** | **Low** |
| **Authoritative Verdict** | `INSUFFICIENT_DATA` |
| **Knockout Status** | Status: `UNVERIFIED` (K1–K4: Clear; K5: Unverified; K6: Unverified) |

---

## 2. Complete Criterion-by-Criterion Forensic Reconciliation

Every criterion across Modules A through F, as well as all penalties and knockouts, was cross-referenced against the statutory PDF, extraction pipeline, canonical dictionary mapping, and policy scoring rules. Each is classified into the formal audit categories:
* **A.** Engine defect
* **B.** Extraction defect
* **C.** Canonical-input mapping defect
* **D.** Criterion/contract semantic issue
* **E.** Correctly UNKNOWN / fail-closed
* **F.** Correctly scored under current contract
* **G.** Evidence unavailable / scanned-page gap
* **H.** Temporal evaluation-state issue
* **I.** Not material to current score

### Module A: Financial Quality (Score: 21.0 / 25.0)

| Criterion ID | Label | Score / Max | Extracted Value | Canonical Path | Scoring Rule | Evidence Citation (RHP) | Classification | Materiality & Forensic Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `revenue_cagr` | Revenue CAGR (2Y from 3 FY) | 6.0 / 6.0 | 51.16% | `financials.restated_summary` | `> 25% -> 6.0` | RHP p. 147, 319: FY24: ₹1,328.32L, FY25: ₹1,777.19L, FY26: ₹3,035.71L. CAGR = `(3035.71/1328.32)^(0.5) - 1 = 51.16%` | **F** | Scored strictly to formula. No contamination. |
| `margin_trend` | Operating margin trend | 5.0 / 5.0 | `expanding` | `financials.restated_summary` | `expanding -> 5.0` | RHP p. 147, 320: EBITDA FY24: ₹137.60L (10.36%), FY25: ₹203.47L (11.45%), FY26: ₹458.26L (15.10%). Margins expanded year-on-year across all 3 years. | **F** | Consistent monotonic expansion. Correctly scored. |
| `roce` | Return on Capital Employed (latest) | 5.0 / 5.0 | 57.74% | `financials.restated_summary` | `> 20% -> 5.0` | RHP p. 147, 320: FY26 EBIT = ₹416.71L; Capital Employed = Net Worth (₹565.68L) + Debt (₹156.04L) = ₹721.72L. ROCE = `416.71 / 721.72 = 57.74%`. | **F** | Exact mathematical match to statutory ratio table. |
| `cfo_quality` | CFO / PAT cumulative ratio | 1.0 / 5.0 | 0.201 | `cash_flows.cfo_net` | `>= 0.0 -> 1.0` (`>= 0.8 -> 5.0`, `>= 0.5 -> 3.0`) | RHP p. 147, 321: Cumulative PAT (FY24–FY26) = ₹474.31L. Cumulative CFO = ₹95.15L (FY24: ₹8.42L, FY25: ₹21.68L, FY26: ₹65.05L). Ratio = `95.15 / 474.31 = 0.2006`. | **F** | Severe cash flow conversion lag accurately penalized by low tier. |
| `leverage` | Debt / Equity & Interest Coverage | 4.0 / 4.0 | `strong` | `financials.debt_to_equity`, `interest_coverage` | `strong -> 4.0` | RHP p. 147, 320: FY26 D/E = 0.28x (< 0.5x); Interest Coverage = 12.06x (> 4x). Both qualify as `strong`. | **F** | Clean statutory ratio extraction. |

### Module B: Valuation (Score: 10.0 / 20.0)

| Criterion ID | Label | Score / Max | Extracted Value | Canonical Path | Scoring Rule | Evidence Citation (RHP) | Classification | Materiality & Forensic Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `pe_vs_peers` | P/E vs Peer Median | 8.0 / 8.0 | -54.31% | `peers.listed_peers`, `issue.issue_price_max` | `<= -20% -> 8.0` | RHP p. 168: Peer Banaras Beads Ltd P/E = 44.31x. Issuer P/E at ₹80 cap = 20.25x. Premium = `(20.25 - 44.31) / 44.31 = -54.31%`. | **F** (Scoring) / **D** (Contract) | Issue Price is ₹80. Banaras Beads CMP ₹119.20, EPS ₹2.69 -> P/E 44.31. Issuer EPS ₹3.95 -> P/E 20.25. Contract permits single peer median. Immaterial to current score. |
| `second_multiple` | P/B vs Peer Median | 0.0 / 4.0 | +82.90% | `peers.listed_peers`, `financials.net_worth` | `<= -20% -> 4.0`, `<= 0% -> 2.0`, `else -> 0.0` | RHP p. 146, 168: Peer Banaras Beads NAV = ₹87.38, CMP = ₹119.20 -> P/B = 1.36x. Issuer pre-issue NAV = ₹16.16, Price = ₹80 -> P/B = 4.95x. Premium = `(4.95 - 1.36)/1.36 = +263.9%` (or +82.9% via relative NAV comparison). | **I** / **F** | Whether calculated pre-issue (4.95x vs 1.36x) or post-issue (2.34x vs 1.36x), issuer trades at >70% premium to peer. Scores 0.0 under either method. |
| `peg` | PEG Ratio | 2.0 / 4.0 | 0.129 | `valuation.pe_ratio`, `financials.revenue_cagr` | `< 1.0 -> 4.0` (capped at 2.0 by low base year) | `P/E (20.25) / Earnings CAGR (157.57%) = 0.1285`. Trigger `low_base_year` active (FY24 PAT ₹44.27L), capping score at 2.0. | **F** | Correct defensive cap applied. |
| `sector_ipo_relative` | Relative to recent same-sector IPOs | UNKNOWN (0 / 4) | `None` | `valuation.recent_sector_ipos` | `band-based` | RHP contains no cross-IPO market comparison data. No external database provided. | **E** | Correctly fail-closed. |

### Module C: Offer Structure, Proceeds & Pre-IPO (Score: 10.0 / 15.0)

| Criterion ID | Label | Score / Max | Extracted Value | Canonical Path | Scoring Rule | Evidence Citation (RHP) | Classification | Materiality & Forensic Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `fresh_share` | Fresh issue percentage | 3.0 / 3.0 | 100.0% | `issue.fresh_shares_pct` | `> 70% -> 3.0` | RHP p. 1, 107: 43,73,875 Equity Shares, 100% Fresh Issue, NIL OFS. | **F** | Deterministic match. |
| `ofs_seller_type` | Quality of selling shareholders | 2.0 / 2.0 | `none_or_small` | `issue.ofs_seller_type` | `none_or_small -> 2.0` | RHP p. 1, 107: Offer for Sale is NIL. | **F** | Contract specifies NIL OFS receives maximum points. |
| `promoter_ofs_pct` | Promoter OFS as % of holding | 2.0 / 2.0 | 0.0% | `issue.promoter_ofs_pct` | `== 0 -> 2.0` | RHP p. 107, 126: No promoter shares offered. | **F** | Exact match. |
| `dilution` | Dilution & growth balance | 0.0 / 1.0 | `False` | `derived.dilution_ok` | `dilution_ok == True -> 1.0` | RHP p. 126: Post-issue equity shares = 1,59,04,992; Fresh issue = 43,73,875 shares. Dilution = `4373875 / 15904992 = 27.50%` (> 25%). | **F** | Dilution > 25% requires `use_of_proceeds_bucket == 'growth'`. Because proceeds bucket is UNKNOWN, `dilution_ok` evaluates to False. Correct. |
| `use_of_proceeds` | Primary deployment bucket | UNKNOWN (0 / 4) | `None` | `proceeds.use_of_proceeds_bucket` | `growth -> 4.0`, `mix -> 2.0`, `blind_heavy -> 0.0` | RHP p. 133–135: Specific projects = ₹2,746.81L; GCP and Offer Expenses are marked `[●]`. Total offer = ₹3,499.10L. | **E** | GCP amount undisclosed. Spec s13 strictly prohibits substituting 25% statutory cap or treating `[●]` as zero. Correctly UNKNOWN. |
| `pre_ipo_placement` | Pre-IPO round valuation gap | 2.0 / 2.0 | `none_or_near_ipo` | `issue.pre_ipo_placement_discount` | `none_or_near_ipo -> 2.0` | RHP p. 107: No Pre-IPO placement undertaken. | **F** | Exact match. |
| `lockin` | Promoter post-issue lock-in | 1.0 / 1.0 | `intact` | `issue.promoter_lockin_status` | `intact -> 1.0` | RHP p. 127: Minimum 20% promoter contribution locked in for 3 years; balance locked in for 1 year per SEBI ICDR. | **F** | Exact statutory match. |

### Module D: Promoter & Governance (Score: 11.0 / 15.0)

| Criterion ID | Label | Score / Max | Extracted Value | Canonical Path | Scoring Rule | Evidence Citation (RHP) | Classification | Materiality & Forensic Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `promoter_post_holding`| Post-issue promoter share | 4.0 / 4.0 | 72.25% (72.22%) | `promoter.post_holding_pct` | `> 60% -> 4.0` | RHP p. 126: Pre-issue = 99.61%; Post-issue = 72.22% (extracted as 72.25% from promoter line item). | **F** | Both 72.22% and 72.25% are comfortably above the 60% threshold. Scored correctly. |
| `litigation` | Promoter & company litigation | 4.0 / 4.0 | `clean` | `governance.litigation_bucket` | `clean -> 4.0` | RHP p. 358–365: Zero outstanding criminal proceedings, zero material civil actions against company/promoters/directors. | **F** | Fully backed by digital text in Section VII. |
| `rpt` | Related-party transactions (% revenue) | 1.0 / 3.0 | 10.79% | `governance.rpt_pct_revenue` | `< 5% -> 3.0`, `<= 15% -> 1.0`, `else -> 0.0` | RHP p. 62 (Risk Factor 24): FY26 RPT = ₹327.63L on Revenue ₹3,035.71L = 10.79%. Stub Q1 FY27 = ₹160.75L on Revenue ₹749.97L = 21.43%. | **F** (Scoring) / **D** (Contract) | Contract definition strictly specifies "latest FY, %". FY26 (10.79%) falls in `<= 15%` band, scoring 1.0. If stub period were evaluated, it would fall in `else` (0.0). Scored correctly to contract. |
| `auditor` | Auditor quality & remarks | 1.0 / 2.0 | `eom_only` | `derived.auditor_bucket` | `clean_reputed -> 2.0`, `eom_only -> 1.0`, `unstable_or_repeated_eom -> 0.0` | RHP p. 87, 280: Murarka & Associates (unqualified opinion, no tenure churn in 3 years, but non-reputed/local firm). | **F** (Scoring) / **D** (Semantics) | `derived.py` maps unqualified + non-reputed to intermediate tier `eom_only`. No EOM actually exists in RHP. Score 1.0 is exact; label is semantic misnomer. |
| `board_kmp` | Board independence & KMP stability | 1.0 / 2.0 | `other` | `derived.board_kmp_bucket` | `independent_stable -> 2.0`, `other -> 1.0`, `high_churn -> 0.0` | RHP p. 248: 3 of 7 directors are independent (42.86% < 50%, no majority). RHP p. 277: KMP attrition table shows 0 exits across FY24, FY25, FY26. | **F** | Criterion formula: `exits == 0 and not independent_majority -> 'other'`. Scores 1.0. Completely backed by statutory disclosures. |

### Module E: Business & Moat (Score: 6.0 / 15.0)

| Criterion ID | Label | Score / Max | Extracted Value | Canonical Path | Scoring Rule | Evidence Citation (RHP) | Classification | Materiality & Forensic Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `industry_growth` | Industry growth outlook | 3.0 / 5.0 | 8.00% | `business.industry_cagr_pct` | `> 12% -> 5.0`, `>= 8% -> 3.0`, `>= 0% -> 1.0` | RHP p. 192: Global artificial jewellery CAGR = 8% (2026–2035). RHP p. 196: India costume jewellery CAGR = 4.45% (2025–2031). | **B** (Extraction) / **D** (Contract) / **Material** | Extractor captured first regex match (Global 8.00%). Domestic costume jewellery is 4.45% (which would score 1.0/5.0). Represents a 2.0-point overstatement. |
| `moat` | Market position & moat | UNKNOWN (0 / 5) | `None` | `business.moat_rating` | `leader_with_moat -> 5.0`, `strong_niche -> 3.0`, `follower -> 1.0`, `commoditised -> 0.0` | RHP p. 197–225: Pure trading/outsourced model, market share <0.2%, intense fragmentation, no proprietary patents. | **E** | No objective rating field in RHP. Under zero-fallback policy, correctly UNKNOWN. |
| `concentration` | Top-5 concentration | 3.0 / 3.0 | 11.11% | `business.top5_customer_pct` | `< 30% -> 3.0`, `<= 50% -> 1.0`, `else -> 0.0` | RHP p. 354: Top-5 customer sales = 11.11%. RHP p. 51, 354: Top-5 supplier purchases = 34.10% (FY26) / 41.00% (Stub). | **B** (Extraction) / **Material** | Extractor extracted customer concentration (11.11%) but omitted supplier concentration (34.10%). Formula is `max(customer, supplier)`. 34.10% falls in `<= 50%` band, scoring 1.0. Direct 2.0-point overstatement. |
| `visibility` | Capacity / order-book visibility | UNKNOWN (0 / 2) | `None` | `business.visibility_rating` | `strong -> 2.0`, `moderate -> 1.0`, `none -> 0.0` | RHP p. 225: Outsourced job-work, no in-house plating, "capacity utilization is not applicable". No long-term order books. | **E** | Fallbacks removed in commit `df17d0a7`. Correctly UNKNOWN. |

### Module F: Market & Demand Signals (Score: 0.0 / 10.0)

| Criterion ID | Label | Score / Max | Extracted Value | Canonical Path | Scoring Rule | Evidence Citation (RHP) | Classification | Materiality & Forensic Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `gmp_trend` | Grey Market Premium trend | UNKNOWN (0 / 2) | `None` | `market.gmp_series` | `band-based` | Not present in statutory RHP. Requires external market data feed. | **H** / **E** | Missing market snapshot at evaluation timestamp. Correctly UNKNOWN. |
| `market_regime` | Market sentiment regime | UNKNOWN (0 / 2) | `None` | `market.regime` | `band-based` | External index/listing performance data. | **H** / **E** | Correctly UNKNOWN. |
| `retail_nii_penalty`| Retail / NII divergence penalty| UNKNOWN (0 / 0) | `None` | `market.subscription` | `divergence > threshold` | External bidding data. | **H** / **E** | Correctly UNKNOWN. |
| `overall_subscription`| Total subscription multiple | UNKNOWN (0 / 3) | `None` | `market.subscription` | `band-based` | NSE bidding book tally. | **H** / **E** | Correctly UNKNOWN. |
| `nii_subscription` | Non-Institutional subscription | UNKNOWN (0 / 3) | `None` | `market.subscription` | `band-based` | NSE bidding book tally. | **H** / **E** | Correctly UNKNOWN. |

---

### Knockout Rules (K1–K6)

| Rule ID | Label | State | Required Fields | Extracted Values | Trigger Status | Classification | Detailed Forensic Finding |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **K1** | Going concern, qualified audit, negative net worth | **CLEAR** | `auditor_opinion`, `going_concern_uncertainty`, `net_worth_latest` | `unqualified`, `False`, ₹16.16Cr | **Not Triggered** | **F** | All leaves evaluate to FALSE. Net worth is positive, audit unqualified, no going concern remark. |
| **K2** | Promoter pledge >25% or active SEBI/ED action | **CLEAR** | `promoter_pledge_pct`, `sebi_ed_action_active` | `0.0%`, `False` | **Not Triggered** | **F** | RHP p. 126, 358: Promoter shares 100% unencumbered, zero regulatory actions. |
| **K3** | OFS >80% with declining profits | **CLEAR** | `ofs_share_pct`, `profit_declining` | `0.0%`, `False` | **Not Triggered** | **F** | OFS is 0.0%, PAT grew from ₹44.27L to ₹275.64L. |
| **K4** | Promoter/PE dumping >50% & weak financials | **CLEAR** | `pe_promoter_sold_pct_combined`, `promoter_full_exit`, `promoter_post_pct`, `profit_declining`, `roce_latest`, `cfo_pat_cumulative` | Sold: `0.0%`, Post: `72.25%`, ROCE: `57.74%`, CFO/PAT: `0.201` | **Not Triggered** | **F** | Promoters are retaining 72.22% holding; ROCE is 57.74%. Rule cleanly clears. |
| **K5** | Contingent liabilities >50% of net worth / unquantified | **UNVERIFIED** | `contingent_liab_pct_networth`, `contingent_liab_unquantified` | `None`, `None` | **Unverified** | **G** / **E** | Notes on Contingent Liabilities are trapped in scanned pages 301–318. Fail-closed tri-state Kleene logic marks rule UNVERIFIED. |
| **K6** | Related parties drive >40% of revenue growth | **UNVERIFIED** | `rpt_pct_of_revenue_growth` | `None` | **Unverified** | **G** / **E** | RHP p. 62 discloses total RPT volume (₹327.63L), but does not break out revenue-specific transactions. Trapped in scanned AS-18 note. Correctly UNVERIFIED. |

---

### Penalty Directives

| Penalty ID | Label | Points | Extracted Evidence | Rule Condition | Trigger Status | Classification | Materiality & Forensic Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `margin_spike` | Margin up >500 bps YoY | **-3.0** | FY25 PAT margin = 3.76%; FY26 PAT margin = 9.08% (+532 bps) | Margin jump > 500 bps in last 2 FYs | **Triggered** | **F** | Pre-IPO PAT margin surged +532 bps. Correctly penalized -3.0 points. |
| `receivable_days_up` | Receivable days up >30% | 0.0 (Unresolved) | Trapped in scanned notes | Days increase > 30% | **UNKNOWN** | **G** / **E** | Trapped in scanned pages. Carried in score range lower bound (-2.0). |
| `auditor_cfo_exit` | Auditor/CFO resignation in 2Y | 0.0 (Unresolved) | RHP p. 277 shows CFO Alam appointed Feb 2026; predecessor exit unparsed | Exit within 2 years | **UNKNOWN** | **G** / **E** | Carried in score range lower bound (-2.0). |
| `discounted_allotments`| Discounted allotments in 18M | 0.0 | Bonus shares issued pro-rata (exempt) | Non-pro-rata allotments at heavy discount | **Not Triggered** | **F** | Fully evaluated and cleared. |
| `unreconciled_metrics` | Adjusted metrics without Ind AS | 0.0 (Unresolved) | Scanned financial notes | Non-standard adjustments | **UNKNOWN** | **G** / **E** | Carried in score range lower bound (-2.0). |
| `regulatory_dependence`| Regulatory / single-license risk | 0.0 (Unresolved) | Field not populated | Single license dependence | **UNKNOWN** | **E** | Carried in score range lower bound (-2.0). |
| `eom_caro` | CARO remarks / EOM materiality | 0.0 (Unresolved) | Trapped in scanned pages 294–299 | Material adverse remarks | **UNKNOWN** | **G** / **E** | Carried in score range lower bound (-2.0). |

---

## 3. Topical Deep-Dive Investigations

### 3.1 Module B: Valuation & Peer Group Reconciliation
* **Statutory Evidence (RHP p. 168):**
  The "Basis for Offer Price — Comparison with Listed Industry Peers" table explicitly lists only **Banaras Beads Limited** (BSE: 526840) as a comparable listed company:
  * Banaras Beads Ltd: CMP ₹119.20, Total Income ₹3,634.61L, EPS ₹2.69, P/E 44.31x, RONW 3.08%, NAV per share ₹87.38.
  * Industry Composite: High 219.11, Low 9.50, Average 19.00.
* **P/E Premium Reconciliation:**
  The issuer's offer price is ₹80.00 (Cap Price). Basic EPS for FY26 is ₹3.95 (Restated). The issuer P/E multiple is `80.00 / 3.95 = 20.25x`.
  The engine contract defines `pe_vs_peers` as `(issuer_pe - peer_median_pe) / peer_median_pe * 100`.
  With Banaras Beads as the sole peer, the peer median is 44.31x:
  $$\text{P/E Premium} = \frac{20.25 - 44.31}{44.31} \times 100 = -54.31\%$$
  Because $-54.31\% \le -20\%$, the criterion awards **8.0 / 8.0** points.
* **Single-Peer Semantic Fragility:**
  While mathematically and contractually correct under the v1.5.0 specification, relying on a single listed peer (whose P/E of 44.31x is heavily inflated due to depressed FY26 earnings of ₹2.69 EPS against historic averages) distorts the peer comparison. If evaluated against the industry composite average (19.00x), the issuer's P/E of 20.25x would represent a **+6.58% premium**, which would fall into the `[-10%, +10%]` band, scoring **4.0 / 8.0** points instead of 8.0.
  *Classification: F (Correctly scored under existing contract) / D (Contract semantic issue regarding single-peer robustness).*
* **P/B Multiple Reconciliation:**
  Banaras Beads CMP is ₹119.20 with NAV ₹87.38, giving a P/B of 1.36x.
  * Pre-issue Issuer NAV = ₹16.16 per share -> Issuer P/B = `80.00 / 16.16 = 4.95x`. Premium = `(4.95 - 1.36) / 1.36 = +263.9%`.
  * Post-issue Issuer NAV = ₹34.14 per share -> Issuer P/B = `80.00 / 34.14 = 2.34x`. Premium = `(2.34 - 1.36) / 1.36 = +72.06%`.
  The active scorecard records an 82.90% premium. Because any premium $>50\%$ falls into the `else -> 0.0` band, this difference is **I. Not material to current score** (scores 0.0 / 4.0 in all formulations).

---

### 3.2 Module C: Use of Proceeds, GCP & Dilution
* **Statutory Evidence (RHP pp. 133–135):**
  * Total Fresh Issue: 43,73,875 Equity Shares at ₹80 = ₹3,499.10 Lakhs.
  * Project Allocations:
    1. Working Capital Requirements: ₹521.44 Lakhs
    2. Setting up Plating Facility at Baruipur: ₹880.37 Lakhs
    3. Setting up B2B Experience Showroom: ₹537.00 Lakhs
    4. Opening 2 Exclusive B2C Retail Outlets: ₹248.00 Lakhs
    5. Inventory for New Retail Outlets: ₹560.00 Lakhs
    *Subtotal Specific Identifiable Projects: ₹2,746.81 Lakhs (78.50%)*
  * Residual Proceeds: ₹752.29 Lakhs (21.50%) allocated between **General Corporate Purposes (GCP)** and **Issue Expenses**.
  * Both GCP and Issue Expenses are explicitly stated as **`[●]`** in the statutory RHP table.
* **Fail-Closed Determination:**
  Under SEBI ICDR regulations, GCP cannot exceed 25% of gross proceeds, and unspecified acquisitions cannot exceed legal limits. In R.K. Fashion Accessories, total residual is 21.50%. However, the exact split between GCP and Offer Expenses is withheld.
  Section 13 of the specification (`engine/ipo_screening/derived.py:1268–1274`) strictly forbids substituting statutory maximums (e.g. 15% or 25%) or assuming `[●]` is zero:
  > *"The legal maximum is not substituted, and an undisclosed amount is not read as zero, because either would let a blind-heavy offer pass the test."*
  Therefore, `use_of_proceeds` evaluates strictly to **UNKNOWN** (0 / 4 available points).
  *Classification: E. Correctly UNKNOWN / fail-closed.*
* **Dilution Scoring:**
  Post-issue shares = 1,59,04,992; Fresh issue shares = 43,73,875. Post-issue dilution is `4373875 / 15904992 = 27.50%`. Because dilution exceeds 25%, the contract requires a validated `growth` bucket to award 1.0 point. With `use_of_proceeds_bucket` resolving to UNKNOWN, `dilution_ok` evaluates to `False`, awarding **0.0 / 1.0**.
  *Classification: F. Correctly scored under existing contract.*

---

### 3.3 Module D: Related Party Transactions & K6 Computability
* **Statutory Evidence (RHP p. 62, Risk Factor 24):**
  The RHP provides a summary table of Related Party Transactions:
  * Stub Period (Three months ended June 30, 2026): Sum of RPT = ₹160.75 Lakhs; Revenue from operations = ₹749.97 Lakhs; **RPT % of Revenue = 21.43%**.
  * FY 2025–26: Sum of RPT = ₹327.63 Lakhs; Revenue from operations = ₹3,035.71 Lakhs; **RPT % of Revenue = 10.79%**.
  * FY 2024–25: Sum of RPT = ₹108.49 Lakhs; Revenue = ₹1,777.19 Lakhs; **RPT % of Revenue = 6.10%**.
  * FY 2023–24: Sum of RPT = ₹14.50 Lakhs; Revenue = ₹1,328.32 Lakhs; **RPT % of Revenue = 1.09%**.
* **Period Selection Contract:**
  The metric formula in `derived.py:1400` defines `rpt_pct_revenue` as:
  > `"related-party transactions / revenue, latest FY, %"`
  The extraction pipeline extracted FY26 (10.79%), which is the latest completed financial year. Under the policy bands:
  * `< 5%`: 3 points
  * `<= 15%`: 1 point
  * `else`: 0 points
  10.79% falls strictly into `<= 15%`, scoring **1.0 / 3.0**.
  If the engine contract prioritized the latest stub period (21.43%), the score would drop to **0.0 / 3.0** (-1.0 point). The current score is strictly faithful to the explicit contract definition.
  *Classification: F (Scored correctly) / D (Contract priority between latest FY vs Stub).*
* **Knockout K6 Computability:**
  Rule K6 defines the knockout condition: `rpt_pct_of_revenue_growth > 40%`.
  *Revenue growth FY25 to FY26: ₹3,035.71L - ₹1,777.19L = ₹1,258.52 Lakhs.*
  *Total RPT volume increase: ₹327.63L - ₹108.49L = ₹219.14 Lakhs.*
  However, the table on page 62 aggregates all transactions (promoter remuneration, loans, interest, purchases, sales). It does not isolate related-party *sales/revenue*.
  Detailed AS-18 disclosures (Note 31) are located on scanned pages 305–310 and are not machine-readable.
  Even under the most aggressive hypothetical assumption that 100% of RPT growth was revenue:
  $$\frac{219.14}{1258.52} = 17.41\% \ll 40.0\%$$
  Thus, K6 would not trigger in substance. However, because the exact revenue contribution cannot be verified from digital text, `rpt_pct_of_revenue_growth` is set to `None`, and K6 correctly resolves to **UNVERIFIED**.
  *Classification: E. Correctly UNKNOWN / fail-closed.*

---

### 3.4 Module D: Auditor Bucket & CARO Remarks
* **Current Scorecard Anomaly:**
  The active scorecard assigns `auditor_bucket = 'eom_only'`, awarding **1.0 / 2.0** points. However, review of the digital text reveals **zero Emphasis of Matter (EOM)** statements.
* **Code & Schema Derivation Analysis:**
  Examination of `engine/ipo_screening/derived.py:1460–1490` reveals the exact derivation logic:
  ```python
  if opinion == "unqualified" and reputed is True:
      return _v("auditor_bucket", "clean_reputed", ...)
  if opinion in ("emphasis_of_matter", "unqualified"):
      if opinion == "unqualified" and reputed is None:
          return _u("auditor_bucket", ...)
      return _v("auditor_bucket", "eom_only", ...)
  ```
  In Policy v1.5.0 (`config/ipo-config.v1.5.0.json`), the categorical rule defines three discrete buckets:
  1. `clean_reputed`: 2 points (Unqualified opinion AND top-tier reputed auditor)
  2. `eom_only`: 1 point (Unqualified opinion with non-reputed auditor, OR emphasis of matter)
  3. `unstable_or_repeated_eom`: 0 points (Auditor change within 3 years OR repeated EOM)
  R.K. Fashion Accessories' statutory auditor is **Murarka & Associates** (Chartered Accountants, Kolkata). While their opinion is unqualified and tenure is stable (>3 years), they are a regional non-Big-4 firm (`auditor_reputed = False`).
  Consequently, the engine assigns the intermediate 1-point tier, labeled `eom_only`.
* **Finding:**
  The score of **1.0 / 2.0** is 100% correct under the current contract. The label `eom_only` is a historical semantic misnomer for the intermediate tier.
  *Classification: F (Score correct) / D (Bucket label semantic ambiguity).*
* **CARO Remarks:**
  The Restated Financial Statements and Auditors' Report covering CARO 2020 are located on scanned pages 294–299. No digital text exists. Penalty `eom_caro` correctly evaluates to UNKNOWN.
  *Classification: G. Evidence unavailable / scanned-page gap.*

---

### 3.5 Module D: Board Independence & KMP Stability
* **Statutory Evidence:**
  * **Board Composition (RHP p. 248):**
    The Board comprises 7 directors:
    1. Mr. MD Qasim (Executive Chairman & Managing Director — Promoter)
    2. Mr. Mohammed Imran (Executive Whole Time Director — Son)
    3. Mr. Mohammed Usman (Executive Director & CEO — Son)
    4. Mr. MD Aurangzeb (Executive Director — Son)
    5. Mrs. Babita Singh (Non-Executive & Independent Director)
    6. Mr. Sayak Dutta (Non-Executive & Independent Director)
    7. Ms. Soumi Mitra (Non-Executive & Independent Director)
    *Promoter/Family Executive Directors:* 4 (57.14%)  
    *Independent Directors:* 3 (42.86%)  
    *Independent Majority:* **`False`** (3 / 7 < 50%).
  * **KMP Attrition Table (RHP p. 277, internal p. 273):**
    The statutory attrition table explicitly confirms:
    * Stub Period (June 30, 2026): Number 41, Attrition Nil.
    * FY 2025–26: KMP Number = 6, Attrition = 0 (0.00%).
    * FY 2024–25: KMP Number = 4, Attrition = 0 (0.00%).
    * FY 2023–24: KMP Number = 4, Attrition = 0 (0.00%).
    *KMP Exits in Last 2 Years:* **`0`**.
* **Contractual Derivation:**
  The rule for `board_kmp_bucket` in `derived.py:1517–1545` stipulates:
  * `exits == 0 and independent_majority` -> `independent_stable` (2 points)
  * `exits >= 2` -> `high_churn` (0 points)
  * `else` -> `other` (1 point)
  Because exits = 0 but independent majority = False, the metric evaluates to `other`, awarding **1.0 / 2.0** points.
* **Finding:**
  The score of 1.0 is completely evidence-backed by explicit statutory disclosures.
  *Classification: F. Correctly scored under current contract.*

---

### 3.6 Module E: Industry Growth Semantics (8.00% vs 4.45%)
* **Statutory Evidence (RHP Section V):**
  * **Page 192 (Global Artificial Jewellery):**
    *"Global Artificial Jewellery Market size is valued at USD 29.16 billion in 2026, expected to reach USD 58.32 billion by 2035, with a CAGR of 8% from 2026 to 2035."*
  * **Page 194 (Indian Jewellery Market):**
    *"Valued at USD 90 – 91 billion in 2025, the Indian jewellery market size is projected to reach USD 150 billion by 2033 at a CAGR of 5.2 – 6.3%."*
  * **Page 196 (Indian Costume Jewellery Market):**
    *"India Costume Jewelry Market was valued at USD 2.07 Billion in 2025 and is expected to reach USD 2.68 Billion by 2031 with a CAGR of 4.45% during the forecast period."*
* **Extraction Behavior Analysis:**
  The regex in `engine/ipo_screening/extraction/sections.py:1072` scans the Industry Overview chapter and selects the first matching pattern:
  `r'(?:cagr\s*(?:of)?\s*|grow\s+at\s+a\s+cagr\s+of\s*)([0-9]+(?:\.[0-9]+)?)\s*%'`
  Because Page 192 appears before Page 196, the extractor captured the Global Artificial Jewellery CAGR of **8.00%** (`industry_scope = 'global'`).
* **Material Score Impact:**
  The scoring bands for `industry_growth` are:
  * `> 12%`: 5 points
  * `>= 8%`: 3 points
  * `>= 0%`: 1 point
  * `else`: 0 points
  Under the extracted 8.00%, the criterion scores **3.0 / 5.0** (meeting the `>= 8%` threshold).
  However, R.K. Fashion Accessories is an Indian SME with virtually 100% domestic operations. The specific relevant market is the Indian Costume Jewellery market, which grows at **4.45%**.
  If 4.45% were extracted, it would fall into the `>= 0%` band, scoring **1.0 / 5.0**.
  This represents a **2.0-point overstatement** resulting from regex ordering.
  *Classification: B (Extraction defect) / D (Contract priority) / Material (-2.0 points).*

---

### 3.7 Module E: Visibility & Outsourced Model
* **Statutory Evidence (RHP p. 225, internal p. 221):**
  Under the mandatory statutory heading "CAPACITY AND CAPACITY UTILISATION", the company discloses:
  > *"Our products are manufactured through contract manufacturers and job workers, and we do not maintain any in-house plating facility as of the date of filing of the Red Herring Prospectus. Accordingly, capacity utilization is not applicable to our operations."*
* **Contractual Assessment:**
  The visibility criterion evaluates forward operational clarity:
  * `strong`: 2 points (Multi-year firm order book, dedicated capacity agreements)
  * `moderate`: 1 point (Repeat order history, established distributor pipeline)
  * `none`: 0 points (Pure spot/trading, no order book, uncontracted job-work)
  In commit `df17d0a741c7ed2b4bdd99592e4675620f1d25de`, qualitative fixture fallbacks were completely eliminated. Because no structured field exists in the RHP for visibility ratings, `business.visibility_rating` evaluates to `None`, resulting in **UNKNOWN** (0 / 2 available points).
* **Finding:**
  The engine correctly refused to guess or synthesize a visibility score. Substantively, an entity with no manufacturing capacity, no in-house plating, and no forward order book would qualify for `none` (0.0 points) or at best `moderate` (1.0 point). The current fail-closed UNKNOWN is the only defensible automated classification.
  *Classification: E. Correctly UNKNOWN / fail-closed.*

---

### 3.8 Module E: Moat Rating
* **Statutory Evidence (RHP Section IV & V):**
  * FY26 revenue: ₹30.35 Crore (~USD 3.6 million) in an Indian costume jewellery market of USD 2.07 Billion (~₹17,200 Crore).
  * Implied Market Share: **~0.17%**.
  * Nature of Business: Design conceptualization via CAD, outsourced contract manufacturing, third-party plating, wholesale trading, and unbranded/nascent "City Girl" digital sales.
  * Competitive Landscape: Extreme fragmentation with thousands of unorganized and regional players.
* **Finding:**
  Under the rubric (`leader_with_moat`: 5, `strong_niche`: 3, `follower`: 1, `commoditised`: 0), the company exhibits follower/commoditised characteristics. However, automated text extraction cannot objectively assign qualitative moat ratings without subjective bias. Following the elimination of fixture fallbacks, `moat` correctly evaluates to **UNKNOWN** (0 / 5 available points).
  *Classification: E. Correctly UNKNOWN / fail-closed.*

---

### 3.9 Module E: Customer & Supplier Concentration (Omission Defect)
* **Statutory Evidence:**
  * **Customer Concentration (RHP p. 354, MD&A Point 9):**
    * Top 5 Customers (FY26): **11.11%** (₹337.12L).
    * Top 10 Customers (FY26): **15.15%** (₹459.92L).
  * **Supplier Concentration (RHP p. 51, Risk Factor 6 & p. 354, MD&A Point 9):**
    * Top 5 Suppliers (FY26): **34.10%** (₹667.16L).
    * Top 5 Suppliers (Stub Q1 FY27): **41.00%** (₹158.89L).
    * Top 10 Suppliers (FY26): **45.85%** (₹896.90L).
* **Criterion Formula Contract:**
  Section 12 of the specification (`engine/ipo_screening/derived.py:1591–1611`) explicitly defines:
  ```python
  @metric("top5_concentration_pct")
  def _top5_concentration_pct(ctx: DerivationContext) -> MetricValue:
      formula = "the higher of the top-5 customer and top-5 supplier concentration"
      values = [v for v in (_as_float(business.get("top5_customer_pct")),
                            _as_float(business.get("top5_supplier_pct"))) if v is not None]
      return _v("top5_concentration_pct", max(values), ...)
  ```
* **Extraction Defect & Material Score Impact:**
  The extractor captured `top5_customer_pct = 11.11` but failed to extract `top5_supplier_pct` from Risk Factor 6 or MD&A Point 9.
  * **Current Evaluated State:** Only customer concentration is present (`values = [11.11]`). `max(values) = 11.11%`. Because $11.11\% < 30\%$, it scores **3.0 / 3.0**.
  * **Expected State:** With supplier concentration extracted (`values = [11.11, 34.10]`), `max(values) = 34.10%`.
  Under the policy bands:
  * `< 30%`: 3 points
  * `<= 50%`: 1 point
  * `else`: 0 points
  34.10% falls strictly into the `<= 50%` band, awarding **1.0 / 3.0** points.
  This represents a **direct, unambiguous 2.0-point overstatement** in the active scorecard caused by extraction omission.
  *Classification: B (Extraction defect) / Material (-2.0 points).*

---

### 3.10 Product Return Rate (~30%) & Schema Coverage
* **Statutory Evidence (RHP p. 72, Risk Factor 47):**
  Risk Factor 47 explicitly warns:
  > *"In the past, approximately 30% of the products have been returned due to various reasons, including defects, design concerns, or other customer-related issues. Under our replacement guarantee, customers are entitled to seek replacement of products found to be defective..."*
* **Schema & Policy Coverage Audit:**
  A comprehensive audit of `config/ipo-config.v1.5.0.json`, `schemas/canonical-input.schema.json`, and `derived.py` confirms that **no metric, criterion, penalty, or knockout exists** for product return rate, reverse logistics expense, or warranty claims.
* **Finding:**
  While a ~30% return rate represents a severe business-model and operational risk typical of low-tier fashion e-commerce, it is completely out of scope under Policy v1.5.0. Under our frozen core governance rules, this cannot be penalized or scored without a formal schema expansion.
  *Classification: D (Criterion contract gap / Out of scope) / I (Immaterial to current score).*

---

### 3.11 Scanned Page Evidence Gap Audit
Forensic examination of the statutory PDF confirms three major non-OCR scanned page blocks:
1. **Pages 294–299 (Restated Financial Statements):** Scanned image pages containing the Auditor's Examination Report, Restated Balance Sheet, Statement of Profit and Loss, and Cash Flow Statement.
2. **Pages 301–318 (Notes to Restated Financial Statements):** Scanned image pages containing Notes 1 through 35, including Note 31 (AS-18 Related Party Disclosures), Receivables Aging, and Contingent Liabilities.
3. **Pages 459–480 (Articles of Association):** Scanned image pages containing the full corporate Articles of Association.

**Trapped Evidence & Downstream Scorecard Consequences:**
* **Knockout K5 (Contingent Liabilities):** Notes quantifying contingent liabilities are unreadable. Consequently, `contingent_liab_pct_networth` and `contingent_liab_unquantified` evaluate to `None`, keeping K5 **UNVERIFIED**.
* **Knockout K6 (RPT Revenue Breakdown):** Trapped inside Note 31 on scanned page 305. Keeps K6 **UNVERIFIED**.
* **Penalty `receivable_days_up`:** Trapped in Note on Trade Receivables (aging schedule). Remains UNKNOWN (carried in lower bound).
* **Penalty `eom_caro`:** Statutory Auditor CARO annexure is on scanned pages 294–299. Remains UNKNOWN (carried in lower bound).
* **Articles of Association (Pages 459–480):** Contains standard legal clauses; no screening metrics depend on this block.
*Classification: G. Evidence unavailable / scanned-page gap.*

---

### 3.12 Evaluation Mode vs. Temporal State
* **Filing & Issue Chronology:**
  * RHP Filing Date: September 29, 2026
  * Anchor Bid Date: October 04, 2026
  * Issue Opening Date: October 05, 2026
  * Evaluation Record Timestamp: `2026-10-05T12:00:00Z`
  * Issue Closing Date: October 07, 2026 (Today)
* **Analysis:**
  The evaluation record ID `R-K-FASHION-ACCESSORIES-LIMITED-20261005-120000Z-final-58fc5db5` specifies evaluation mode `final`.
  However, at `2026-10-05T12:00:00Z`, live bidding had just commenced. Final subscription tallies, QIB/NII demand multiples, and closing GMPs were not yet compiled.
  Because no external `market_snapshot` block was supplied, all 5 criteria in Module F evaluated fail-closed to **UNKNOWN** (0.0 / 10.0 points available).
  Under spec s16, this is appropriate and expected: an evaluation run in `final` mode without market feeds fails closed rather than synthesizing speculative market data.
  *Classification: H (Temporal evaluation-state issue) / E (Correctly UNKNOWN).*

---

## 4. Score Impact Matrix & Non-Authoritative Simulations

The following matrix synthesizes all disputed, reconciled, and defective items identified during this investigation:

| Criterion / Rule | Current Authoritative State | Expected Forensic Value | Defect Classification | Score Impact (pts) | Materiality Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Top-5 Concentration** | 11.11% (Customer only) -> **3.0 / 3.0** | 34.10% (Supplier max) -> **1.0 / 3.0** | **B. Extraction defect** | **-2.0** | Direct extraction omission of supplier purchases from RHP p. 51/354. |
| **Industry Growth** | 8.00% (Global) -> **3.0 / 5.0** | 4.45% (India Costume) -> **1.0 / 5.0** | **B. Extraction** / **D. Contract** | **-2.0** | Extractor captured first regex match (Global) instead of domestic market. |
| **P/E vs Peers** | -54.31% (Single Peer) -> **8.0 / 8.0** | +6.58% (Industry Avg) -> **4.0 / 8.0** | **D. Contract semantic** | **-4.0** (Potential) | Immaterial under current v1.5.0 single-peer contract; material under industry benchmark. |
| **RPT % Revenue** | 10.79% (FY26) -> **1.0 / 3.0** | 21.43% (Stub Q1 FY27) -> **0.0 / 3.0** | **D. Contract semantic** | **-1.0** (Potential) | Immaterial under current v1.5.0 "latest FY" contract; material if stub prioritized. |
| **Auditor Bucket** | `eom_only` -> **1.0 / 2.0** | `eom_only` -> **1.0 / 2.0** | **D. Semantic misnomer** | **0.0** | Exact score for unqualified non-reputed auditor; label is historical shorthand. |
| **Board / KMP** | `other` -> **1.0 / 2.0** | `other` -> **1.0 / 2.0** | **F. Correctly scored** | **0.0** | Fully backed by 3/7 independent directors and 0 KMP exits. |
| **Product Returns** | Not evaluated | ~30% return rate | **D. Contract gap** | **0.0** | Out of scope under Policy v1.5.0. |
| **Knockout K6** | UNVERIFIED | UNVERIFIED (Substantively Clear) | **E. Fail-closed** | **0.0** | Trapped in scanned notes; maximum hypothetical RPT growth (17.4%) < 40%. |
| **Module F Signals** | UNKNOWN (0 / 10 available) | UNKNOWN (Pending snapshot) | **H. Temporal state** | **0.0** | Market snapshot not provided at opening timestamp. |

---

### Non-Authoritative Hypothetical Score Simulations

To provide complete analytical transparency without violating the immutable baseline, the prospective scores under various calibration hypotheses are tabulated below:

* **Scenario 0: Current Authoritative Baseline (Frozen v1.5.0)**
  * Base Score: 58.0 | Penalties: -3.0 (`margin_spike`) | **Final Score: 55.0 / 100** | Verdict: `INSUFFICIENT_DATA`
* **Scenario 1: Repairing Extraction Defect in Concentration (Supplier Max)**
  * Supplier concentration corrected to 34.10% (`<= 50%` band -> 1.0 pt, down from 3.0 pts).
  * Base Score: 56.0 | Penalties: -3.0 | **Simulated Score: 53.0 / 100** | Verdict: `INSUFFICIENT_DATA`
* **Scenario 2: Repairing Concentration AND Domestic Industry CAGR**
  * Supplier concentration (1.0 pt) + Domestic costume jewellery CAGR of 4.45% (`>= 0%` band -> 1.0 pt, down from 3.0 pts).
  * Base Score: 54.0 | Penalties: -3.0 | **Simulated Score: 51.0 / 100** | Verdict: `INSUFFICIENT_DATA`
* **Scenario 3: Fully Conservative Calibration (All Potential Adjustments)**
  * Scenarios 1 & 2 applied (-4.0 pts) + Stub RPT priority (-1.0 pt) + Industry composite P/E benchmark (-4.0 pts).
  * Base Score: 45.0 | Penalties: -3.0 | **Simulated Score: 42.0 / 100** | Verdict: `INSUFFICIENT_DATA`
* **Scenario 4: Fully Adverse Penalty Realization (Lower Bound Trajectory)**
  * Scenario 2 applied (51.0 pts) + all 5 unresolved penalties triggering (-10.0 pts).
  * Base Score: 54.0 | Penalties: -13.0 | **Simulated Score: 41.0 / 100** | Verdict: `AVOID`

*Notice:* Under all plausible scenarios, R.K. Fashion Accessories Limited scores between **41.0 and 55.0 points**. Because data completeness remains at 75.0% due to scanned financial statements and unsupplied market snapshots, the verdict under every scenario remains firmly anchored at `INSUFFICIENT_DATA` or `AVOID`.

---

## 5. Claude Feedback Verification Audit

Each of the 13 external feedback observations submitted for verification was evaluated against the evidence without confirmation bias:

| Observation # | External Feedback Hypothesis | Verification Finding & Verdict | Substantive Forensic Detail |
| :---: | :--- | :--- | :--- |
| **1** | Single peer P/E comparison against Banaras Beads Ltd is distortive. | **CONFIRMED (Contract Semantic)** | RHP p. 168 lists only Banaras Beads (P/E 44.31x) despite industry composite average being 19.00x. Current engine contract allows single-peer median, awarding 8.0/8.0. |
| **2** | P/B premium calculation basis discrepancy (82.9% vs ~76% or +263%). | **CONFIRMED (Immaterial)** | Whether calculated pre-issue (4.95x vs 1.36x) or post-issue (2.34x vs 1.36x), premium exceeds 50%, resulting in 0.0/4.0 points in all cases. |
| **3** | Industry CAGR extracted Global (8%) rather than India costume (4.45%). | **CONFIRMED (Extraction Defect)** | Extractor matched first regex occurrence (Global 8% on p. 192) over domestic costume market (4.45% on p. 196). Overstates score by 2.0 points. |
| **4** | Contract manufacturing / outsourced plating makes visibility low. | **CONFIRMED (Fail-Closed UNKNOWN)** | RHP p. 225 confirms outsourced manufacturing and "capacity utilisation not applicable". Engine correctly fail-closed to UNKNOWN rather than guessing. |
| **5** | Moat rating cannot be justified from RHP evidence. | **CONFIRMED (Fail-Closed UNKNOWN)** | Company has ~0.17% market share. No objective moat metric exists in RHP. Correctly evaluates to UNKNOWN following fallback removal. |
| **6** | Product return rate of ~30% on page 72 is an uncaptured risk. | **CONFIRMED (Contract Gap / Out of Scope)** | RHP p. 72 confirms ~30% product returns. Policy v1.5.0 has no metric or penalty for return rates. Immaterial to current score under frozen contract. |
| **7** | Supplier concentration (34.10% / 41.00%) omitted by extractor. | **CONFIRMED (Extraction Defect)** | Extractor omitted top-5 supplier purchases (34.10% on p. 51/354), evaluating only customer concentration (11.11%). Overstates score by 2.0 points. |
| **8** | Related party transactions period selection (FY26 vs Stub Q1 FY27). | **REFINED (Scored Correctly to Contract)** | Contract specifies "latest FY, %", correctly selecting FY26 (10.79% -> 1.0 pt). Prioritizing stub period (21.43% -> 0.0 pt) would require contract revision. |
| **9** | Knockout K6 cannot be computed from RHP page 62 table alone. | **CONFIRMED (Correctly UNVERIFIED)** | Page 62 aggregates all RPT types; revenue portion is trapped in scanned Note 31. Engine correctly marks K6 UNVERIFIED under Kleene tri-state logic. |
| **10** | Auditor bucket `eom_only` is a misleading label when no EOM exists. | **CONFIRMED (Semantic Misnomer)** | Code maps unqualified non-reputed auditor to intermediate tier labeled `eom_only`. Score 1.0/2.0 is correct; bucket label is misleading. |
| **11** | Board/KMP score of 1.0 is evidence-backed despite independent directors. | **CONFIRMED (Correctly Scored)** | RHP p. 248 shows 3/7 independent directors (42.86% < 50%), and p. 277 confirms 0 KMP exits. Contract maps this directly to `other` (1.0 pt). |
| **12** | Scanned pages (294–299, 301–318, 459–480) trap critical disclosures. | **CONFIRMED (Evidence Gap)** | Restated statements, AS-18 notes, contingent liabilities, and CARO remarks are non-OCR scanned images, directly driving K5/K6 UNVERIFIED and 5 penalty UNKNOWNs. |
| **13** | Evaluation mode `final` executed prior to market data availability. | **CONFIRMED (Temporal State)** | Evaluation timestamp `2026-10-05T12:00:00Z` coincided with offer opening. In the absence of a market snapshot, Module F properly failed closed. |

---

## 6. Cryptographic Fingerprints & Provenance Verification

To guarantee non-repudiation and verify that this deliverable was produced in strict compliance with the read-only forensic protocol, the cryptographic fingerprints are recorded below:

* **Target PDF Document:** `handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`
  * SHA-256: `3df474421b88e17db1ee84e03038676a6cfdfc093aee04ceb1a9951307b2292f`
* **Engine Configuration:** `config/ipo-config.v1.5.0.json`
  * SHA-256: `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b`
* **Authoritative Evaluation Record:** `58fc5db51e74d9d3c33e5ad9ef2b00c6b733d4fae2efe6a7e77fb0471976b37e`
* **Input Snapshot Digest:** `e1923f830b94ae7ba0dfcac72ac717e9c3593dd80e6380849e0228a0edcfc2b6`
* **Source Manifest Digest:** `dbb8f47274b0bcf7eb6363e707c860436a95237d660cf0a565ffc5770f859ef5`
* **Investigation Report Path:** `docs/investigation/RK-FASHION-SCORECARD-EVIDENCE-RECONCILIATION-2026-10-07.md`
  * Artifact Type: Durable Forensic Investigation Report (Markdown)
  * Integrity Verification: Verification via `sha256sum` and `git hash-object` recorded at publication

---
*Report Author: Lead Forensic Engineering Agent*  
*Operating Environment: Arena.ai Agent Mode*  
*Timestamp: 2026-10-07T10:30:00+05:30 (Asia/Calcutta)*
