# UI-4: Post-Listing Observation & Performance Explorer

**Authoritative Specification & Implementation Report**  
**Engine Baseline:** `v1.5.0` (Active Policy) | `v1.6.0-draft` (Inactive Calibration Proposal)  
**API Protocol:** UI-1 Presentation API (`docs/openapi/presentation-api-v1.yaml`)  
**Presentation Surfaces:** UI-2 Core Dashboard & Scorecard + UI-3 Evidence & Provenance Explorer + UI-4 Post-Listing Observation & Performance Explorer  
**Status:** DELIVERED & AUDITED  
**Date:** 2026-10-06  

---

## 1. Executive Summary

UI-4 delivers the **Post-Listing Observation & Performance Explorer**, completing the presentation layer's coverage of post-listing tracking, actual price trajectories, benchmark comparisons, corporate action adjustments, and research feedback loops. Consuming the Phase-6 read-model endpoints defined in the UI-1 Presentation API (`/evaluations/{id}/post-listing`, `/evaluations/{id}/performance`, `/backtest/analytics`, `/calibration/proposals`), UI-4 provides investment committees, risk analysts, and researchers with an institutional surface to track how pre-listing IPO evaluations perform in live public secondary markets.

$$\text{Final Pre-Listing Evaluation} \longrightarrow \text{Listing Day Open/Close} \longrightarrow \text{1-Week (1W)} \longrightarrow \text{1-Month (1M)} \longrightarrow \text{6-Month (6M)} \longrightarrow \text{Aggregate Research Feedback}$$

### Key Capabilities Delivered:
1. **Performance Explorer View (`#performance/{evaluation_id}`):** Dedicated route exposing structured performance metrics, milestone progress, price histories, and cryptographic linkage for any completed pre-listing evaluation.
2. **Performance Summary KPI Strip:** Instant executive metrics across Issue Price, Listing Date, 1W Return, 1M Return, 6M Return, and Excess Alpha vs Benchmark (`NIFTY 50` / `NIFTY 50 TRI`).
3. **Deterministic Lifecycle Timeline:** 5-step visual milestone tracker mapping evaluation maturation:
   - Step 1: `FINAL Screening` (Scorecard & Verdict)
   - Step 2: `Listing Day` (Open & Close pricing)
   - Step 3: `1-Week (1W)` (Initial trading stabilization)
   - Step 4: `1-Month (1M)` (Post-listing seasoning)
   - Step 5: `6-Month (6M)` (Long-term maturity)
   Incomplete or unreached horizons explicitly display `INCOMPLETE` or `PENDING` states without false positive completion.
4. **Multi-Horizon Price & Return Detail Cards:** Comprehensive inspection of each recorded horizon, separating:
   - Primary Pricing: Issue Price, Listing Open, Listing Close
   - Secondary Pricing: Raw Observed Close, Corporate Action Factor, Adjusted Observed Close
   - Benchmark Tracking: Symbol, Listing Value, Observed Value, Benchmark Return %
   - Deterministic Return Decomposition: Absolute Return %, Listing Gain %, Secondary Return %, Excess Return (Alpha) %
5. **Corporate Action Adjustment Transparency:** Clear visual status of whether observed prices reflect unadjusted trading (`Factor: 1.0000 Clean`) or adjusted corporate actions (stock splits, bonus issues, capital reorganizations), displaying corporate action status codes (`CLEAN_UNADJUSTED`, `ADJUSTED_BONUS_OR_SPLIT`, `UNVERIFIED_ACTIONS`).
6. **Observation Provenance Audit Panel:** Cryptographic fingerprints ensuring complete auditability from secondary data sources (Bhavcopy / Exchange feeds) to the original evaluation artifact (`final_evaluation_id`, `final_result_hash`, `source_manifest_hash`, `calculation_inputs_hash`, `observation_hash`).
7. **Aggregate Backtest Boundary Affordance:** Explicit research bridge to aggregate backtesting metrics (`/api/v1/backtest/analytics`), enforcing the institutional distinction: **Individual Observation $\neq$ Aggregate Backtest Analysis**. Exposes population rank IC, hit rates, decile spreads, and dataset provenance.
8. **Calibration Governance Boundary:** Dedicated governance callout for policy calibration proposals (`/api/v1/calibration/proposals`), enforcing the core governance principle: **Evidence $\rightarrow$ Analysis $\rightarrow$ Proposal $\neq$ Approval $\neq$ Implementation $\neq$ Activation**. Prohibits automated in-browser mutation or policy activation controls.
9. **Bidirectional Navigation Integration:** Header affordances in UI-2 Scorecard (`Post-Listing Performance ->`), Scorecard return links (`<- Return to Scorecard`), and direct cross-links to UI-3 Evidence Explorer (`Inspect Evidence ->`).
10. **Zero Calculation Authority Invariant:** Strictly zero client-side return or alpha computation in browser code; all calculations are executed deterministically on the engine backend.

---

## 2. Architectural Boundaries & System Invariants

```
+-----------------------------------------------------------------------------------------------------------------+
|                                              BROWSER PRESENTATION LAYER                                          |
|                                                                                                                 |
|  +--------------------------------+   +------------------------------------+   +-----------------------------+  |
|  |     UI-2 Executive Scorecard   |   |   UI-3 Evidence & Provenance       |   |    UI-4 Performance Explorer|  |
|  |   - Overall Score: 35.0/100    |---|   - Prospectus Citations (DRHP/RHP)|---|   - Timeline: 1W, 1M, 6M    |  |
|  |   - Verdict: INSUFFICIENT_DATA |   |   - Cryptographic Fingerprints     |   |   - Alpha vs Benchmark      |  |
|  +--------------------------------+   +------------------------------------+   +-----------------------------+  |
|                                                           |                                                     |
|                                                           v HTTP GET (Read-Only)                                |
+-----------------------------------------------------------------------------------------------------------------+
|                                              UI-1 PRESENTATION API                                              |
|                                                                                                                 |
|  GET /evaluations/{id}                 --> EvaluationReadModel (Immutable Pre-Listing Evaluation)                |
|  GET /evaluations/{id}/evidence        --> EvidenceReadModel (Verbatim Prospectus Citations)                    |
|  GET /evaluations/{id}/post-listing    --> PostListingObservationsResponse (Child Horizon Observations)          |
|  GET /evaluations/{id}/performance     --> PerformanceSummaryResponse (Multi-Horizon Return Summary)             |
|  GET /backtest/analytics               --> BacktestAnalyticsResponse (Aggregate IC, Hit Rates, Decile Spreads)  |
|  GET /calibration/proposals            --> CalibrationProposalsResponse (Read-Only Candidate Policies)          |
+-----------------------------------------------------------------------------------------------------------------+
|                                        AUTHORITATIVE ENGINE & DATA STORES                                        |
|                                                                                                                 |
|  [Evaluations Store]                   [Observations Store]                 [Analytics / Calibration]           |
|  <store>/<eval_id>/evaluation.json     <store>/<eval_id>/observations/      build/analytics/analysis.json       |
|  <store>/<eval_id>/result.json         observation_1w.json                  build/calibration/proposal_v16.json |
|  <store>/<eval_id>/manifest.json       observation_1m.json                  Active: v1.5.0 | Inactive: v1.6.0   |
|  (FROZEN & IMMUTABLE)                  (CHILD ARTIFACTS)                    (GOVERNANCE GATED)                  |
+-----------------------------------------------------------------------------------------------------------------+
```

### Invariant I: Zero Calculation Authority in Browser
The browser operates strictly as a read-only presentation terminal. The frontend contains zero mathematical logic or heuristics for computing:
- Absolute return: $R_{abs} = \frac{P_{adjusted} - P_{issue}}{P_{issue}}$
- Listing gain: $R_{listing} = \frac{P_{open} - P_{issue}}{P_{issue}}$
- Secondary return: $R_{sec} = \frac{P_{adjusted} - P_{close}}{P_{close}}$
- Benchmark return: $R_{bm} = \frac{B_{observed} - B_{listing}}{B_{listing}}$
- Excess return (Alpha): $\alpha = R_{abs} - R_{bm}$

All calculations are executed server-side by the deterministic Phase-6 return engine and validated prior to serialization into JSON artifacts. The client merely renders the formatted values received from UI-1.

### Invariant II: Strict Fail-Closed / Unknown Semantics
In alignment with engine-wide fail-closed principles, missing or incomplete values are never coerced or defaulted to zero (`0` or `0.00%`):
- An unobserved return is displayed as `UNAVAILABLE` or `INCOMPLETE`.
- Missing prices are displayed as `—`.
- Missing or unrecorded horizons display explicit milestone states (`INCOMPLETE` / `PENDING`).
- Zero returns ($0.00\%$) are displayed only when the engine authoritatively reports zero.

### Invariant III: Permanent Evaluation Immutability
The original `FINAL` pre-listing evaluation artifact (`evaluation.json`, `result.json`, `manifest.json`) is cryptographically frozen. Post-listing observations are stored as child artifacts under `<store>/<eval_id>/observations/observation_<horizon>.json`. Adding post-listing observations never modifies, overwrites, or invalidates the original evaluation record or its cryptographic result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.

### Invariant IV: Zero In-Browser Policy Activation Controls
In accordance with institutional governance standards, calibration proposals (`v1.6.0-draft`) are strictly separated from production execution (`v1.5.0`). The web presentation layer provides zero mutation affordances, activation buttons, or API modification endpoints. Calibration proposals require offline human committee ratification and explicit deployment lifecycles.

### Invariant V: Zero Credential & Filesystem Leakage
The presentation layer does not leak server host paths (`/home/user/`, `/etc/`), local filesystem references, internal environment variables, or external API keys (`AI71_API_KEY`, `OPENAI_API_KEY`). All audit traces use logical URIs and cryptographic SHA-256 digests.

---

## 3. UI-4 Component Specification

### 3.1 Header & Evaluation Linkage
- **Navigation Controls:** Direct links back to Scorecard (`&larr; Return to Scorecard`) and Evidence Explorer (`Inspect Evidence &rarr;`).
- **Context Metadata:** Displays Company Name, IPO Identifier, Evaluation ID, Mode (`FINAL`), Engine Version (`v1.5.0`), and Active Spec Version (`v1.5`).
- **Hash Traceability:** Provides instant copy-to-clipboard functionality for Evaluation ID and parent result hash.

### 3.2 Performance Summary KPI Strip
Accessible region (`role="region"`, `aria-label="Performance Summary KPIs"`) displaying key performance indicators:
1. **Issue Price & Listing Date:** Formatted in INR (`₹215.00`) alongside official BSE/NSE listing date.
2. **1-Week (1W) Return & Alpha:** Absolute return percentage badge and excess return relative to benchmark.
3. **1-Month (1M) Return & Alpha:** Absolute return percentage badge and excess return relative to benchmark.
4. **6-Month (6M) Return & Alpha:** Absolute return percentage badge or explicit `INCOMPLETE` badge when unreached.
5. **Lifecycle Maturity:** Overall completion status across horizons (`PARTIAL (2/3 Recorded)` or `MATURED`).

### 3.3 Deterministic Performance Timeline
Structured timeline (`aria-label="Lifecycle Performance Timeline"`) illustrating chronological milestone completion:
- **Milestone 1:** `FINAL Screening` — Pre-listing fundamental evaluation with immutable score and verdict.
- **Milestone 2:** `Listing Day` — Primary trading execution with open/close price recording.
- **Milestone 3:** `1-Week (1W)` — 7 calendar days / 5 trading days post-listing observation.
- **Milestone 4:** `1-Month (1M)` — 30 calendar days post-listing seasoning.
- **Milestone 5:** `6-Month (6M)` — 180 calendar days maturity observation.

Each step displays its deterministic status badge (`COMPLETED`, `RECORDED`, `VERIFIED`, `INCOMPLETE`, `PENDING`), target date, and actual secondary trading date.

### 3.4 Multi-Horizon Observation Cards
Each recorded horizon renders a dedicated card containing:
- **Price Metrics Table:**
  - Issue Price (Offer band cutoff)
  - Listing Day Open Price
  - Listing Day Close Price
  - Raw Observed Close (Unadjusted closing price on observation date)
  - Corporate Action Adjustment Factor
  - Adjusted Observed Close (Effective price used for return calculations)
- **Corporate Action Badge:**
  - `Factor: 1.0000 (Clean / Unadjusted)` — No stock splits, bonus shares, or capital reorganizations.
  - `Factor: <f> (Adjusted for Actions)` — Adjusted price reflecting verified corporate adjustments.
  - `Status: UNVERIFIED` — Highlights unverified corporate action status.
- **Return Breakdown Table:**
  - Absolute Return %: Total return from Issue Price to Adjusted Close
  - Listing Gain %: Primary market pop from Issue Price to Listing Open
  - Secondary Return %: Subsequent price movement from Listing Close to Adjusted Close
  - Benchmark Symbol & Return %: Reference index return over matching period (`NIFTY50`)
  - Excess Return (Alpha) %: Net outperformance over benchmark

### 3.5 Provenance & Cryptographic Audit Panel
Accessible region (`role="region"`, `aria-label="Observation Provenance and Fingerprints"`) detailing:
- Final Evaluation Linkage (`evaluation_id`)
- Final Result Hash (`result_hash`)
- Source Manifest Hash (`source_manifest_hash`)
- Benchmark Symbol & Index Code
- Observation Version & Child Store Status (`FROZEN OBSERVER STORE`)

### 3.6 Aggregate Backtest Analytics Affordance
Dedicated institutional boundary callout framing individual offerings within the broader research corpus:
- **Governance Notice:** *Individual Observation $\neq$ Aggregate Backtest Analysis*. Individual observations measure single-offering post-listing trajectory; aggregate backtesting evaluates population rank information coefficient (IC), hit rates, and decile spreads across historical cohorts.
- **Artifact Metrics:** Displays Analysis Hash, Dataset Hash, Sample Maturity count, and Leakage Audit status (`PASSED`).

### 3.7 Calibration Governance Boundary Callout
Policy evolution callout preserving governance hierarchy:
- **Governance Notice:** *Policy Evolution Principle: Evidence $\rightarrow$ Analysis $\rightarrow$ Proposal $\neq$ Approval $\neq$ Implementation $\neq$ Activation*.
- **Status Display:** Shows Active Policy (`● v1.5.0 Executable`) vs Candidate Proposal (`○ v1.6.0 READY_FOR_HUMAN_REVIEW`).
- **Ratification Boundary:** Clarifies that activation requires formal offline committee ratification with strictly zero in-browser mutation or activation controls.

---

## 4. Navigation & Cross-View Integration

UI-4 connects seamlessly with existing presentation views:
1. **Directory (`#directory`) & Dashboard (`#dashboard`):** Recent evaluation tables include a direct `Performance` button alongside `Scorecard` and `Evidence`.
2. **Scorecard (`#evaluations/{id}`):** Header actions bar includes `Post-Listing Performance &rarr;` button leading to `#performance/{id}`.
3. **Performance Explorer (`#performance/{id}`):**
   - Header provides `&larr; Return to Scorecard` to navigate back to fundamental scoring.
   - Header provides `Inspect Evidence &rarr;` to navigate to prospectus source evidence.
   - Provenance panel allows copying hashes for forensic verification.

---

## 5. Verification & Acceptance Results

### 5.1 Node.js Frontend Unit Tests (`frontend/test/`)
Native Node.js test runner suite (`test/*.test.js`) executes 28 tests across 4 test suites:
- `api.test.js`: 8 tests (Initialisation, system endpoints, query params, URL encoding, 404/network errors, ID validation)
- `app.test.js`: 4 tests (Formatting helpers, zero scoring calculation invariant, governance invariant, fail-closed invariant)
- `evidence.test.js`: 8 tests (UI-3 evidence protocols, provenance panel, contract guidance, quote preservation, locators, modal inspection)
- `performance.test.js`: 8 tests (UI-4 post-listing & performance API protocols, `formatReturnPct` fail-closed semantics, KPI strip, deterministic timeline, multi-horizon cards, corporate action factors, backtest/calibration governance boundaries, zero client return calculation invariant)

**Result:** 28 passing tests, 0 failures, execution time ~270ms.

### 5.2 Python Integration & Acceptance Tests (`tests/`)
Comprehensive pytest suite executes 619 tests:
- `test_ui4_performance.py`: 8 tests
  - `test_ui4_static_assets_contain_performance_explorer`: Verifies `#performance-view` landmarks.
  - `test_ui4_css_contains_performance_styles`: Verifies timeline, KPI, and corporate action styles.
  - `test_ui4_app_contains_scorecard_navigation_and_performance_view`: Verifies routing, methods, and navigation links.
  - `test_ui4_zero_return_computation_invariant`: Verifies absence of client-side return calculation functions.
  - `test_ui4_no_server_filesystem_paths_exposed`: Verifies absence of server paths (`/home/user`, `/etc`).
  - `test_ui4_no_credential_exposure`: Verifies zero API key or secret leakage.
  - `test_ui4_post_listing_and_performance_endpoints_served_by_api`: End-to-end FastAPI TestClient integration with live child observations.
  - `test_ui4_no_policy_activation_controls`: Verifies absence of policy activation controls.
- Full Engine Test Suite (`tests/`): All 619 tests pass cleanly, including golden evaluation verification and reproduction benchmarks.

**Result:** 619 passed, 1 warning (deprecation warning in testclient), 0 errors, execution time ~2m39s.

### 5.3 Golden Hash Invariant Verification
The golden evaluation result hash remains bit-for-bit identical:
$$\text{Golden Hash} = \mathtt{e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1}$$
Frozen core modules (`derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`) remain untouched.

---

## 6. Cryptographic SHA-256 Checksums

| File Path | SHA-256 Digest | Status |
| :--- | :--- | :--- |
| `frontend/index.html` | `097a28c1bbd82c3e5358b6caa3ca0a7077ee2d8a55d38f2867076a7229f8ae81` | Modified |
| `frontend/styles.css` | `942a5e6fa596f8f14cc7fb533b67c6995bc0c0dae0031edf83450fec4b0552ab` | Modified |
| `frontend/app.js` | `0a2019e727b2edb1d61f88264c117f3aeed1fb295a8c5952c432cb426dad4a9d` | Modified |
| `frontend/api.js` | `214f4547c93efacf83308680ffd52d3ca2f4f92e32777b78c4a3ec119cb18b3f` | Unmodified |
| `frontend/test/performance.test.js` | `2cb53d2db71f825eb8e792b4526c364d23cce042e0c2048a545c37c91b4c1fcd` | Added |
| `tests/test_ui4_performance.py` | `cc84cb77dfc776d21a48a6f2a8471c71b9104ecd44b3e3329d6649357d09d1ae` | Added |
| `docs/UI-4-POST-LISTING-PERFORMANCE.md` | `[Self-Referencing Document]` | Added |
