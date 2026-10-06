# UI-5: Backtest Analytics Dashboard

**Authoritative Specification & Implementation Report**  
**Engine Baseline:** `v1.5.0` (Active Policy) | `v1.6.0-draft` (Inactive Calibration Proposal)  
**API Protocol:** UI-1 Presentation API (`docs/openapi/presentation-api-v1.yaml`)  
**Presentation Surfaces:** UI-2 Core Dashboard & Scorecard + UI-3 Evidence Explorer + UI-4 Performance Explorer + UI-5 Backtest Analytics Dashboard  
**Status:** DELIVERED & AUDITED  
**Date:** 2026-10-06  

---

## 1. Executive Summary

UI-5 delivers the **Backtest Analytics Dashboard**, providing an institutional read-only presentation surface for historical population diagnostics, Rank Information Coefficients (Spearman correlation), hit rates, score-to-outcome relationships, and point-in-time leakage audit findings. Consuming the Phase-6C analytical read model via the UI-1 Presentation API (`GET /api/v1/backtest/analytics` and `GET /api/v1/backtest/datasets`), UI-5 projects population-level predictive diagnostics without replicating mathematical formulas or statistical heuristics in the browser.

$$\text{Screening Universe} \longrightarrow \text{Evaluations Store} \longrightarrow \text{Assembled Dataset} \longrightarrow \text{Phase-6C Deterministic Analytics} \longrightarrow \text{UI-5 Population Presentation}$$

### Key Capabilities Delivered:
1. **Dedicated Backtest Analytics Route (`#backtest`, aliased `#analytics/backtest`):** Direct navigation from the top navbar, executive dashboard header, and individual offering performance explorers.
2. **Architectural Distinction Banner:** Explicit 3-domain visual separation:
   - **Historical Population Analysis** (Current View: cross-sectional Rank IC, hit rates, decile distributions across all evaluated historical IPOs).
   - **Individual IPO Performance** (Single-offering post-listing trajectory, secondary price adjustments, alpha vs benchmark).
   - **Calibration Proposals** (Governed candidate policies awaiting formal human review; strictly separated from active execution).
3. **Executive Analytics Summary (KPI Strip):** Instant executive metrics displaying:
   - Analysis Sample Size ($N$): Total eligible offerings analyzed.
   - Sample Maturity Tier: Multi-horizon maturity classifications (`1W`, `1M`, `6M`).
   - Rank IC (Spearman correlation): Monotonic ranking predictive power ($\rho$) and p-value.
   - Hit Rate % (1W): Proportion of non-AVOID offerings generating positive excess returns.
   - Avoided Loss Rate % (1W): Proportion of AVOID offerings that underperformed benchmark.
   - Point-in-Time Leakage Audit: Binary audit verification (`PASSED` / `FAILED`).
4. **Rank IC & Spearman Correlation Detail:** Structured presentation of predictive rank ordering between fundamental screening scores (`FINAL_SCORE`) and realized excess returns (`EXCESS_RETURN`) by horizon (`SIX_MONTH`), sample size, p-value, and statistical maturity classification.
5. **Hit-Rate & Avoidance Diagnostics:** Horizon breakdown of hit rates and loss avoidance rates conforming strictly to backend verdict semantics without client-side thresholding.
6. **Score Decile & Quantile Distribution:** Table presentation of decile buckets (score lower/upper bounds, $N$, mean return, benchmark return, excess spread) when populated by the authoritative backend, and an explicit small-sample governance notice (`N < 100`) when deciles are not mathematically formed.
7. **Cohort Stability & Holdout Transparency:** Clear sections for Historical Vintage and Temporal Holdout Partition explicitly stating `Status: NOT EXPOSED IN CURRENT API SCHEMA`, adhering to fail-closed principles without synthesizing artificial data.
8. **Point-in-Time Leakage Audit Panel:** Research governance audit verifying prospectus feature freezing, trading calendar alignment, and corporate action synchronization.
9. **Cryptographic Provenance Panel:** Audit fingerprints for `analysis_hash` and `dataset_hash` with one-click copy-to-clipboard controls.
10. **Calibration Governance Boundary:** Explicit lifecycle firewall:
    $$\text{Evidence} \longrightarrow \text{Analysis} \longrightarrow \text{Proposal} \neq \text{Approval} \neq \text{Implementation} \neq \text{Activation}$$
    Displays Active Policy (`● v1.5.0 Executable`) vs Candidate Proposal (`○ v1.6.0 READY_FOR_HUMAN_REVIEW`). Strictly zero in-browser mutation or activation controls.

---

## 2. Architectural Boundaries & System Invariants

```
+-----------------------------------------------------------------------------------------------------------------+
|                                              BROWSER PRESENTATION LAYER                                          |
|                                                                                                                 |
|  +--------------------------------+   +------------------------------------+   +-----------------------------+  |
|  |     UI-2 Executive Scorecard   |   |   UI-4 Performance Explorer        |   |   UI-5 Backtest Analytics   |  |
|  |   - Overall Score: 35.0/100    |---|   - Single Offering Post-Listing   |---|   - Population Rank IC: +0.165  |  |
|  |   - Verdict: INSUFFICIENT_DATA |   |   - Alpha vs NIFTY 50 (1W, 1M, 6M) |   |   - 1W Hit Rate: 100.0%         |  |
|  +--------------------------------+   +------------------------------------+   +-----------------------------+  |
|                                                           |                                                     |
|                                                           v HTTP GET (Strictly Read-Only)                       |
+-----------------------------------------------------------------------------------------------------------------+
|                                              UI-1 PRESENTATION API                                              |
|                                                                                                                 |
|  GET /backtest/analytics               --> BacktestAnalyticsResponse (Rank IC, Hit Rates, Deciles, Hashes)       |
|  GET /backtest/datasets                --> BacktestDatasetListResponse (Assembled Dataset Manifests)             |
|  GET /calibration/proposals            --> CalibrationProposalListResponse (Read-Only Candidate Policies)       |
|  GET /configuration/current            --> ConfigurationStatusResponse (Active v1.5 vs Candidate v1.6)          |
+-----------------------------------------------------------------------------------------------------------------+
|                                        AUTHORITATIVE ENGINE & DATA STORES                                        |
|                                                                                                                 |
|  [Backtest Analytics Store]            [Backtest Dataset Store]              [Calibration Governance]            |
|  build/analytics/analysis.json         build/dataset/dataset.json            config/calibration-proposal.json    |
|  - Spearman Rank IC & p-values         - Canonical multi-horizon rows        - Candidate v1.6.0 (INACTIVE)       |
|  - Hit & Avoided Loss Rates            - Dataset SHA-256 Hash                - Frozen v1.5.0 Core (ACTIVE)       |
|  (DETERMINISTIC ENGINE CALCULATION)    (IMMUTABLE HISTORICAL SNAPSHOTS)      (OFFLINE COMMITTEE RATIFICATION)    |
+-----------------------------------------------------------------------------------------------------------------+
```

### Invariant I: Zero Analytical Calculation Authority
The browser operates exclusively as a presentation terminal. The frontend contains strictly zero code or formulas for:
- Spearman rank correlation ($\rho = 1 - \frac{6 \sum d_i^2}{n(n^2-1)}$)
- Student's t or permutation p-values
- Hit rates or loss avoidance percentages
- Decile bucketing, bucket boundaries, or quantile averages
- Decile spreads (top decile minus bottom decile)
- Vintage cohort aggregations
- Out-of-sample holdout partitions

All analytical metrics are computed deterministically by `engine/ipo_screening/post_listing/analytics.py` on the server and verified prior to storage.

### Invariant II: Strict Fail-Closed / Unknown Semantics
In alignment with engine-wide fail-closed principles, missing or incomplete values are never coerced or defaulted to zero (`0`, `0.0`, or `0.00%`):
- A missing Rank IC or p-value is displayed as `UNAVAILABLE`.
- Missing hit rates or avoided loss rates are displayed as `UNAVAILABLE`.
- When sample size $N < 100$, decile buckets are not fabricated; an institutional small-sample notice is displayed.
- Zero values ($0.000000$ or $0.0\%$) are displayed only when the engine authoritatively returns 0.

### Invariant III: Absolute Core Engine Immutability
UI-5 introduces strictly zero changes to the engine core:
- `scoring.py`, `derived.py`, `knockouts.py`, `snapshots.py`, `evaluation.py` remain untouched.
- `return_engine.py`, `dataset.py`, `analytics.py`, `calibration.py` remain untouched.
- Golden evaluation result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` is bit-for-bit identical.

### Invariant IV: Zero In-Browser Policy Activation Controls
Calibration proposals (`v1.6.0-draft`) remain strictly separated from active production scoring (`v1.5.0`). The frontend provides zero activation controls, proposal approval buttons, or mutation endpoints.

### Invariant V: Zero Credential & Filesystem Leakage
The presentation layer does not leak server host paths (`/home/user/`, `/etc/`), local filesystem references, or API keys (`AI71_API_KEY`, `OPENAI_API_KEY`). Only logical resource URIs and cryptographic SHA-256 digests are exposed.

---

## 3. UI-5 Component Specification

### 3.1 Route & Header
- **Routes:** `#backtest` (primary) and `#analytics/backtest` (alias).
- **Navigation Breadcrumb:** `IPO Screening Engine • Historical Population Analysis`.
- **Top Actions:** Return to Dashboard (`&larr; Return to Dashboard`) and Explore IPO Directory (`Explore IPO Directory &rarr;`).

### 3.2 Distinction Banner
Visual region (`role="region"`, `aria-label="System Domain Distinctions"`) separating:
1. **Historical Population Analysis (Active View):** Cross-sectional statistical diagnostics, Rank IC, hit rates, and decile distributions across the historical universe.
2. **Individual IPO Performance:** Single-offering post-listing trajectory, secondary price adjustments, and alpha tracking (links to `#directory`).
3. **Calibration Proposals:** Governed candidate policies awaiting formal human review (tagged `GATED`).

### 3.3 Executive Analytics Summary
Visual KPI grid (`role="region"`, `aria-label="Executive Analytics Summary"`):
1. **Analysis Sample Size ($N$):** Number of eligible offerings in universe.
2. **Sample Maturity (1W / 1M / 6M):** Visual pills indicating sample maturity tier (`DESCRIPTIVE_ONLY`, `EXPLORATORY`, `STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS`).
3. **Rank IC (Spearman):** Formatted signed correlation ($\rho = +0.164656$) and p-value ($0.1200$).
4. **1W Hit Rate:** Outperformance rate of qualifying non-AVOID offerings ($100.0\%$).
5. **1W Avoided Loss Rate:** Loss prevention rate of AVOID offerings ($100.0\%$).
6. **Point-in-Time Leakage Audit:** Clear visual badge (`PASSED`).

### 3.4 Diagnostic Sections
1. **Information Coefficient (Rank IC) & Correlation:**
   - Table detailing Predictor $\rightarrow$ Outcome (`FINAL_SCORE -> EXCESS_RETURN`), Horizon (`SIX_MONTH`), Spearman Rank IC ($\rho$), p-value, and Sample Size ($N$).
   - Governance notice explaining small-sample limitations ($N < 30 \implies \mathtt{DESCRIPTIVE\_ONLY}$; $N \ge 100$ required for statistical actionability).
2. **Hit-Rate & Avoidance Diagnostics:**
   - Table detailing Hit Rate % and Avoided Loss Rate % across 1-Week, 1-Month, and 6-Month horizons.
   - Explanatory callout detailing authoritative verdict semantics.
3. **Score Decile & Quantile Analysis:**
   - Populated decile table when buckets exist (Bucket #, Score Range, $N$, Mean Return %, Benchmark Return %, Excess Spread %).
   - Small-sample notice when $N < 100$: *Decile Partitioning: Insufficient Sample Size ($N < 100$)*, confirming zero client-side interpolation.
4. **Historical Vintage & Cohort Stability:**
   - Callout stating: `Status: NOT EXPOSED IN CURRENT API SCHEMA`.
   - Explains that calendar-year vintage breakdowns are maintained in offline research datasets (`build/analytics/analysis.json`) and not projected by the UI-1 Presentation API.
5. **Out-of-Sample Temporal Holdout Partition:**
   - Callout stating: `Status: NOT EXPOSED IN CURRENT API SCHEMA`.
   - Explains that temporal holdout partitioning is maintained in offline research manifests and not projected by the UI-1 Presentation API.
6. **Point-in-Time Safety & Leakage Audit Panel:**
   - Overall audit status badge (`AUDIT PASSED`).
   - Audit checks: Prospectus Feature Freeze, Trading Day Calendar Alignment, Corporate Action Synchronization.
7. **Dataset & Analysis Provenance Fingerprints:**
   - SHA-256 fingerprints for `analysis_hash` and `dataset_hash` with copy buttons.
   - Engine status: `v1.5.0 (Active Frozen Core)`.
   - API schema: `UI-1 Presentation API (docs/openapi/presentation-api-v1.yaml)`.
8. **Calibration Governance Boundary:**
   - Explicit firewall: Evidence $\rightarrow$ Analysis $\rightarrow$ Proposal $\neq$ Approval $\neq$ Implementation $\neq$ Activation.
   - Status display: Active `v1.5.0` vs Candidate `v1.6.0` (`READY_FOR_HUMAN_REVIEW`).
   - Notice: Activation requires formal offline committee ratification; zero in-browser activation controls.

---

## 4. API Contract & Fields Consumed

The implementation preserves the UI-1 Presentation API contract **completely unchanged** (`docs/openapi/presentation-api-v1.yaml`):

### Fields Consumed from `GET /api/v1/backtest/analytics`:
- `analysis_hash`: string (SHA-256 hash of analysis manifest)
- `dataset_hash`: string (SHA-256 hash of underlying dataset)
- `sample_maturity`: object mapping `one_week`, `one_month`, `six_month` to maturity tiers
- `leakage_audit_passed`: boolean (overall point-in-time audit status)
- `rank_ic`: object (`horizon`, `spearman_ic`, `p_value`, `sample_size`)
- `hit_rates`: object (`one_week`, `one_month`, `six_month`)
- `avoided_loss_rates`: object (`one_week`, `one_month`, `six_month`)
- `decile_buckets`: array of bucket objects (`bucket_number`, `score_lower_bound`, `score_upper_bound`, `n`, `mean_return`, `mean_benchmark_return`, `mean_excess_return`)

### Supplementary Endpoints Consumed:
- `GET /api/v1/backtest/datasets`: provides `row_count` and observation counts
- `GET /api/v1/configuration/current`: provides active vs candidate policy status
- `GET /api/v1/calibration/proposals`: provides proposal status for governance callout

---

## 5. Verification & Acceptance Results

### 5.1 Node.js Frontend Unit Tests (`frontend/test/`)
Native Node.js test runner suite (`test/*.test.js`) executes 38 tests across 5 test suites:
- `api.test.js`: 8 tests (Initialisation, system endpoints, query params, URL encoding, 404/network errors, ID validation)
- `app.test.js`: 4 tests (Formatting helpers, zero scoring calculation invariant, governance invariant, fail-closed invariant)
- `evidence.test.js`: 8 tests (UI-3 evidence protocols, provenance panel, contract guidance, quote preservation, locators, modal inspection)
- `performance.test.js`: 8 tests (UI-4 post-listing & performance API protocols, `formatReturnPct` fail-closed semantics, KPI strip, deterministic timeline, multi-horizon cards, corporate action factors, backtest/calibration governance boundaries, zero client return calculation invariant)
- `backtest.test.js`: 10 tests (UI-5 backtest endpoints, distinction banner, executive KPI section, fail-closed `UNAVAILABLE` handling, decile handling for small sample, populated decile rendering, unexposed vintage/holdout handling, leakage audit panel, calibration boundary, zero client statistical calculation invariant)

**Result:** 38 passing tests, 0 failures, execution time ~360ms.

### 5.2 Python Integration & Acceptance Tests (`tests/`)
Comprehensive pytest suite executes 627 tests:
- `tests/test_ui5_backtest.py`: 8 tests
  - `test_ui5_static_assets_contain_backtest_dashboard`: Verifies `#backtest-view` landmarks and navbar tab.
  - `test_ui5_css_contains_backtest_styles`: Verifies distinction banner, KPI grid, and maturity pill styles.
  - `test_ui5_app_contains_backtest_routing_and_views`: Verifies routing, rendering methods, and distinction callouts.
  - `test_ui5_zero_statistical_computation_invariant`: Verifies absence of client-side Spearman, IC, hit rate, or decile formulas.
  - `test_ui5_no_server_filesystem_paths_exposed`: Verifies absence of server paths (`/home/user`, `/etc`).
  - `test_ui5_no_credential_exposure`: Verifies zero API key or secret leakage.
  - `test_ui5_backtest_endpoints_served_by_api`: End-to-end FastAPI TestClient integration with live backtest analytics and dataset responses.
  - `test_ui5_no_policy_activation_controls`: Verifies absence of policy activation controls.
- Full Engine Test Suite (`tests/`): All 627 tests pass cleanly, including golden evaluation verification and reproduction benchmarks.

**Result:** 627 passed, 1 warning (deprecation warning in testclient), 0 errors, execution time ~2m14s.

### 5.3 Golden Hash Invariant Verification
The golden evaluation result hash remains bit-for-bit identical:
$$\text{Golden Result Hash} = \mathtt{e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1}$$
Frozen core modules (`derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`) remain untouched.

---

## 6. Cryptographic SHA-256 Checksums

| File Path | SHA-256 Digest | Status |
| :--- | :--- | :--- |
| `frontend/index.html` | `e4edc8c3c0522bd04385f9344147ff466a3807ccb0024c7055e7e0f336c5adf9` | Modified |
| `frontend/styles.css` | `8d154b1a48bfd9e11298615129979dab360938ef2716e9c58d66005e1436f3f6` | Modified |
| `frontend/api.js` | `b35b823b6b75af7112a2224c56544dc378d5c4548437fe75771654a185812541` | Modified |
| `frontend/app.js` | `79624951ead35bf0af40b9f05399d1cb687777690cfe1e9178952daf9636aba9` | Modified |
| `frontend/test/backtest.test.js` | `fcd67ff39d5106ee2cd1047af32a441960759e2776e8ac32fe7c73911a33c65f` | Added |
| `tests/test_ui5_backtest.py` | `779953689a58760400f6392245df227a248705e2bf44714c63c3456779570c96` | Added |
| `docs/UI-5-BACKTEST-ANALYTICS-DASHBOARD.md` | `[Self-Referencing Document]` | Added |
