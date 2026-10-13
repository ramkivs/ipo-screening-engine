# UI-6: Calibration & Configuration Presentation

**Authoritative Specification & Implementation Report**  
**Engine Baseline:** `v1.5.0` (Active Policy) | `v1.6.0-draft` (Inactive Calibration Proposal)  
**API Protocol:** UI-1 Presentation API (`docs/openapi/presentation-api-v1.yaml`)  
**Presentation Surfaces:** UI-2 Core Dashboard & Scorecard + UI-3 Evidence Explorer + UI-4 Performance Explorer + UI-5 Backtest Analytics Dashboard + UI-6 Calibration & Configuration Presentation  
**Status:** DELIVERED & AUDITED  
**Date:** 2026-10-06  

---

## 1. Executive Summary

UI-6 delivers the **Calibration & Configuration Presentation**, the final planned presentation capability for the standalone IPO Screening Engine. UI-6 provides an institutional, auditable, strictly read-only presentation of the active production policy (`v1.5.0`), the candidate calibration proposal (`v1.6.0-draft`), empirical evidence supporting the proposal, analysis provenance, deterministic current-vs-proposed weight shifts, non-regression and shadow validation results, and the governance lifecycle firewall that strictly separates proposal from approval, implementation, and activation.

$$\text{Evidence} \longrightarrow \text{Analysis} \longrightarrow \text{Proposal} \neq \text{Approval} \neq \text{Implementation} \neq \text{Activation}$$

### Key Capabilities Delivered:
1. **Dedicated Calibration & Policy Route (`#calibration`, aliased `#configuration`):** Accessible from the top navigation bar, executive dashboard header, performance explorer, and backtest analytics dashboard.
2. **Prominent Governance Status & Activation Firewall Panel:** Visual milestone tracker enforcing the governance hierarchy:
   - Step 1: `Empirical Evidence` (Phase 6B/6C Realized Returns & Bhavcopies)
   - Step 2: `Statistical Analysis` (Rank IC & Spearman Correlation Diagnostics)
   - Step 3: `Calibration Proposal` (`PROP-1.0.0` in `READY_FOR_HUMAN_REVIEW` status)
   - Step 4: `Governance Review` (Program Authority Review)
   - Step 5: `Release Activation` (STRICTLY LOCKED / OFFLINE RATIFICATION ONLY)
   Visibly confirms **ZERO in-browser activation authority**.
3. **Active Baseline Policy (v1.5.0) Detailed Presentation:** Full display of active production configuration (`v1.5.0`, spec `1.5`, config hash `382ff86c...`), total points (`100.0 pts`), frozen core status (`VERIFIED`), and baseline module weights across all 6 fundamental modules.
4. **Candidate Policy Proposal (v1.6.0-draft) Presentation:** Full display of candidate proposal metadata (`PROP-1.0.0`, status `READY_FOR_HUMAN_REVIEW`, maturity gate `CALIBRATION_CANDIDATE`, objective `BALANCED_DIAGNOSTIC`, approval status `APPROVED`, draft config hash `4ce1480c...`, proposal hash `87bc9bcf...`).
5. **Deterministic Current-vs-Proposed Comparison Table:** Direct authoritative rendering of module weight shifts:
   - Module A (Financial Quality): `25.0 pts` $\rightarrow$ `30.0 pts` (`+5.0 pts`) — *Increased reflecting stronger development rank correlation ($\rho = 0.164656$). Expected: Improved 1W rank correlation.*
   - Module B (Valuation): `20.0 pts` $\rightarrow$ `15.0 pts` (`-5.0 pts`) — *Decreased reflecting negative development rank correlation ($\rho = -0.139969$). Expected: Reduced valuation noise.*
   - Module C (Offer Structure, Proceeds & Pre-IPO): `15.0 pts` $\rightarrow$ `15.0 pts` (`0.0 pts`) — *Baseline weight retained.*
   - Module D (Promoter & Governance): `15.0 pts` $\rightarrow$ `15.0 pts` (`0.0 pts`) — *Baseline weight retained.*
   - Module E (Business & Moat): `15.0 pts` $\rightarrow$ `15.0 pts` (`0.0 pts`) — *Baseline weight retained.*
   - Module F (Market & Demand Signals): `10.0 pts` $\rightarrow$ `10.0 pts` (`0.0 pts`) — *Baseline weight retained.*
   - Total Scale: `100.0 pts` $\rightarrow$ `100.0 pts` (`0.0 pts`) — *Normalized 100-point total score invariant strictly preserved.*
   - Thresholds: APPLY threshold retained at `75.0 pts` (`NO_CHANGE`, downside discipline preserved).
   - Knockouts: `FIREWALL_EMPTY` (Zero knockout rules relaxed or modified).
6. **Empirical Rationale & Dataset Partitioning:** Full display of calibration dataset sample ($N=120$ offerings across 3 vintages: 2024, 2025, 2026), in-sample development cohort ($N=80$, baseline $\rho = -0.005256$), and out-of-sample holdout cohort ($N=40$, baseline $\rho = 0.115372$).
7. **Non-Regression & Shadow Validation Audit:** Verification of safety checks:
   - `downside_protection`: PASSED (`CLEAR` $\rightarrow$ `CLEAR`, knockout rules, penalty ceilings, and AVOID boundary remain intact).
   - `holdout_stability`: PASSED ($0.115372 \rightarrow 0.115372$, holdout out-of-sample performance non-degraded).
   - `deterministic_reproducibility`: PASSED (`DETERMINISTIC` $\rightarrow$ `DETERMINISTIC`, pure arithmetic deterministic replay).
   - Shadow evaluation transparency: Explicit notice clarifying that per-offering shadow evaluations are maintained in offline verification logs (`build/shadow/`) and not projected as individual evaluation records in the presentation store.
8. **Cryptographic Provenance Panel:** Full SHA-256 fingerprint audit trail (`proposal_hash`, `baseline_config_hash`, `candidate_config_hash`, `source_dataset_hash`, `source_analysis_hash`) with copy-to-clipboard presentation controls.
9. **Zero Activation & Zero Mutation Invariant:** Strictly zero activation buttons, mutation handlers, or promotion controls in the client; active policy `v1.5.0` remains active, candidate `v1.6.0` remains strictly inactive.
10. **Standalone Application Boundary:** Strictly standalone architecture with no external identity, RBAC, multi-user, or enterprise dependencies.

---

## 2. Architectural Boundaries & System Invariants

```
+-----------------------------------------------------------------------------------------------------------------+
|                                              BROWSER PRESENTATION LAYER                                          |
|                                                                                                                 |
|  +--------------------------------+   +------------------------------------+   +-----------------------------+  |
|  |     UI-2 Executive Scorecard   |   |   UI-5 Backtest Analytics          |   |   UI-6 Calibration & Policy |  |
|  |   - Overall Score: 35.0/100    |---|   - Population Rank IC: +0.165     |---|   - Active: v1.5.0 (EXEC)   |  |
|  |   - Verdict: INSUFFICIENT_DATA |   |   - 1W Hit Rate: 100.0%            |   |   - Candidate: v1.6.0 (OFF) |  |
|  +--------------------------------+   +------------------------------------+   +-----------------------------+  |
|                                                           |                                                     |
|                                                           v HTTP GET (Strictly Read-Only)                       |
+-----------------------------------------------------------------------------------------------------------------+
|                                              UI-1 PRESENTATION API                                              |
|                                                                                                                 |
|  GET /configuration/current            --> ConfigurationStatusResponse (Active v1.5 vs Candidate v1.6)          |
|  GET /calibration/proposals            --> CalibrationProposalListResponse (Governed Proposals List)            |
|  GET /calibration/proposals/{id}       --> CalibrationProposal (Module Proposals, Rationale, Non-Regression)    |
|  GET /backtest/analytics               --> BacktestAnalyticsResponse (Supporting Empirical Evidence)            |
+-----------------------------------------------------------------------------------------------------------------+
|                                        AUTHORITATIVE ENGINE & DATA STORES                                        |
|                                                                                                                 |
|  [Active Policy Store]                 [Candidate Proposal Store]            [Analytics / Dataset Stores]        |
|  config/ipo-config.v1.5.0.json         config/calibration-proposal.v1.6.0    build/analytics/analysis.json       |
|  - Production Executable v1.5.0        - Candidate v1.6.0 Proposal           build/dataset/dataset.json          |
|  (ACTIVE & EXECUTABLE)                 (READY_FOR_HUMAN_REVIEW, INACTIVE)   (AUTHORITATIVE EVIDENCE BASE)       |
+-----------------------------------------------------------------------------------------------------------------+
```

### Invariant I: Zero Activation Authority in Browser
The browser operates strictly as an auditable read-only terminal. The presentation layer contains:
- ZERO activation controls (no `<button>Activate</button>`, `activatePolicy`, `applyProposal`, etc.)
- ZERO mutation endpoints (no `POST`, `PUT`, `PATCH`, or `DELETE`)
- ZERO configuration editing or save controls
- ZERO automatic promotion triggers

Any future policy activation requires formal offline investment committee ratification and controlled engineering deployment.

### Invariant II: Strict Fail-Closed / Unknown Semantics
In alignment with engine-wide fail-closed principles, missing or incomplete values are never coerced or defaulted to zero (`0`, `0.0`, or `0.00%`):
- Missing hashes or attributes display `UNAVAILABLE` or `NOT EXPOSED`.
- Absence of a proposed change explicitly renders `NO_CHANGE`, preserving baseline weights.
- Unreached or incomplete horizons display `INCOMPLETE` / `PENDING`.

### Invariant III: Absolute Core Engine Immutability
UI-6 introduces strictly zero changes to the engine core:
- `scoring.py`, `derived.py`, `knockouts.py`, `snapshots.py`, `evaluation.py` remain untouched.
- `return_engine.py`, `dataset.py`, `analytics.py`, `calibration.py` remain untouched.
- `config/ipo-config.v1.5.0.json` (active configuration) remains untouched.
- `config/calibration-proposal.v1.6.0.json` (candidate proposal) remains untouched.
- Golden evaluation result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` is bit-for-bit identical.

### Invariant IV: Zero Credential & Filesystem Leakage
The presentation layer does not leak server host paths (`/home/user/`, `/etc/`), local filesystem references, or API keys (`AI71_API_KEY`, `OPENAI_API_KEY`). Only logical resource URIs and cryptographic SHA-256 digests are exposed.

---

## 3. UI-6 Component Specification

### 3.1 Route & Header
- **Routes:** `#calibration` (primary) and `#configuration` (alias).
- **Navigation Breadcrumb:** `IPO Screening Engine • Policy Evolution & Governance`.
- **Top Actions:** Return to Dashboard (`&larr; Return to Dashboard`) and Backtest Analytics Dashboard (`Backtest Analytics Dashboard &rarr;`).

### 3.2 Prominent Governance Lifecycle Strip
Visual region (`role="region"`, `aria-label="Governance Lifecycle Status"`) displaying:
- Active Status: `● ACTIVE: v1.5.0`
- Candidate Status: `○ CANDIDATE: v1.6.0 (READY_FOR_HUMAN_REVIEW)`
- 5-step milestone chain:
  1. `Empirical Evidence` (Realized Returns & Bhavcopies)
  2. `Statistical Analysis` (Rank IC & Correlation Diagnostics)
  3. `Calibration Proposal` (`PROP-1.0.0`, `READY_FOR_HUMAN_REVIEW`)
  4. `Governance Approval` (Investment Committee Review)
  5. `Release Activation` (STRICTLY LOCKED)
- Explicit Governance Notice confirming zero activation authority in browser.

### 3.3 Side-by-Side Policy Cards
1. **Active Policy Card (v1.5.0):**
   - Header: `Active Policy (v1.5.0)` with badge `● ACTIVE • EXECUTABLE`.
   - Properties: Configuration Version (`1.5.0`), Spec Version (`1.5`), Execution Status (`EXECUTABLE`), Total Points (`100.0 pts`), Frozen Core (`VERIFIED`), Config Hash (`382ff86c...`).
2. **Candidate Proposal Card (v1.6.0-draft):**
   - Header: `Candidate Proposal (v1.6.0-draft)` with badge `○ CANDIDATE • INACTIVE`.
   - Properties: Proposal ID (`PROP-1.0.0`), Target Policy Version (`v1.6.0`), Proposal Status (`READY_FOR_HUMAN_REVIEW`), Maturity Gate (`CALIBRATION_CANDIDATE`), Approval Status (`APPROVED`), Proposal Hash (`87bc9bcf...`).

### 3.4 Current vs Proposed Module Weights Comparison
Deterministic comparison table displaying:
- Module A (Financial Quality): `25.0 pts` $\rightarrow$ `30.0 pts` (`+5.0 pts`, `PROPOSED`)
- Module B (Valuation): `20.0 pts` $\rightarrow$ `15.0 pts` (`-5.0 pts`, `PROPOSED`)
- Module C (Offer Structure): `15.0 pts` $\rightarrow$ `15.0 pts` (`0.0 pts`, `NO_CHANGE`)
- Module D (Promoter & Governance): `15.0 pts` $\rightarrow$ `15.0 pts` (`0.0 pts`, `NO_CHANGE`)
- Module E (Business & Moat): `15.0 pts` $\rightarrow$ `15.0 pts` (`0.0 pts`, `NO_CHANGE`)
- Module F (Market & Demand): `10.0 pts` $\rightarrow$ `10.0 pts` (`0.0 pts`, `NO_CHANGE`)
- Total Scale: `100.0 pts` $\rightarrow$ `100.0 pts` (`0.0 pts`, `NORMALIZED`)
- Downside Discipline Callouts: APPLY threshold unchanged at `75.0 pts`; Knockout Firewall `FIREWALL_EMPTY` (all knockouts intact).

### 3.5 Supporting Empirical Evidence & Dataset Partition
- Total Sample: $N=120$ offerings across 3 vintages (2024, 2025, 2026).
- In-Sample Development: $N=80$ offerings ($2024, 2025$), baseline $\rho = -0.005256$.
- Out-of-Sample Holdout: $N=40$ offerings ($2026$), baseline $\rho = 0.115372$.
- Calibration Objective: `BALANCED_DIAGNOSTIC`.

### 3.6 Non-Regression & Shadow Validation Audit
- Audit Checks Table:
  - `downside_protection`: PASSED (`CLEAR` $\rightarrow$ `CLEAR`).
  - `holdout_stability`: PASSED ($0.115372 \rightarrow 0.115372$).
  - `deterministic_reproducibility`: PASSED (`DETERMINISTIC` $\rightarrow$ `DETERMINISTIC`).
- Shadow Evaluation Callout: Per-offering shadow score comparisons maintained offline (`build/shadow/`) and not projected as individual evaluation records in the presentation store.

### 3.7 Cryptographic Provenance Panel
SHA-256 fingerprint audit trail with copy buttons:
- Proposal Artifact Hash: `87bc9bcfa0bd9561adf3eb0be53a4291c465b5b02cd8561209f323e94a2249af`
- Active Baseline Config Hash: `382ff86cc9d753514509f89c096f3b262bd4e12e644e0d7d03fe811b44e0f1e8`
- Candidate Draft Config Hash: `4ce1480c84e6ebfe22b96511f0f9b1b6577031bf272fe703c48f220a70def1f1`
- Source Dataset Hash: `7cac90dbf32bd385e3627074407191f7f1778093ba14879a2247075e1309057e`
- Source Analysis Hash: `2932cdf824b6f1a1939bad1b82f6da5e730ba5555b2c0da2573a6177c64f37b2`
- Presentation API Specification: `UI-1 Presentation API (docs/openapi/presentation-api-v1.yaml)`

---

## 4. API Contract & Extensions

The implementation updates `docs/openapi/presentation-api-v1.yaml`, `engine/ipo_screening/presentation/models.py`, and `engine/ipo_screening/presentation/service.py` with 100% backward-compatible additive optional fields on `CalibrationProposal`:
- `objective`: string (nullable)
- `sample_summary`: object (nullable)
- `evidence_summary`: object (nullable)
- `module_proposals`: array of objects (nullable)
- `threshold_proposals`: array of objects (nullable)
- `non_regression_results`: array of objects (nullable)
- `recommendation`: string (nullable)

All existing endpoints and schemas maintain identical semantics.

---

## 5. Verification & Acceptance Results

### 5.1 Node.js Frontend Unit Tests (`frontend/test/`)
Native Node.js test runner suite (`test/*.test.js`) executes 47 tests across 6 test suites:
- `api.test.js`: 8 tests (Initialisation, system endpoints, query params, URL encoding, 404/network errors, ID validation)
- `app.test.js`: 4 tests (Formatting helpers, zero scoring calculation invariant, governance invariant, fail-closed invariant)
- `evidence.test.js`: 8 tests (UI-3 evidence protocols, provenance panel, contract guidance, quote preservation, locators, modal inspection)
- `performance.test.js`: 8 tests (UI-4 post-listing & performance API protocols, `formatReturnPct` fail-closed semantics, KPI strip, deterministic timeline, multi-horizon cards, corporate action factors, backtest/calibration governance boundaries, zero client return calculation invariant)
- `backtest.test.js`: 10 tests (UI-5 backtest endpoints, distinction banner, executive KPI section, fail-closed `UNAVAILABLE` handling, decile handling for small sample, populated decile rendering, unexposed vintage/holdout handling, leakage audit panel, calibration boundary, zero client statistical calculation invariant)
- `calibration.test.js`: 9 tests (UI-6 calibration proposal retrieval, governance chain firewall, active v1.5 presentation, candidate v1.6 presentation, current-vs-proposed module weight shift comparison, non-regression audit checks, provenance panel, zero activation controls, zero calculation authority)

**Result:** 47 passing tests, 0 failures, execution time ~370ms.

### 5.2 Python Integration & Acceptance Tests (`tests/`)
Comprehensive pytest suite executes 635 tests:
- `tests/test_ui6_calibration.py`: 8 tests
  - `test_ui6_static_assets_contain_calibration_presentation`: Verifies `#calibration-view` landmarks and navbar tab.
  - `test_ui6_css_contains_calibration_styles`: Verifies governance chain, policy card, and delta pill styles.
  - `test_ui6_app_contains_calibration_routing_and_views`: Verifies routing, rendering methods, and governance chain.
  - `test_ui6_calibration_endpoints_served_by_api`: End-to-end FastAPI TestClient integration with live proposal detail and configuration status.
  - `test_ui6_cross_view_navigation_integration`: Verifies navigation from Dashboard, Backtest, and Performance views.
  - `test_ui6_zero_activation_controls_and_handlers`: Verifies absence of activation controls.
  - `test_ui6_no_server_filesystem_paths_exposed`: Verifies absence of server paths (`/home/user`, `/etc`).
  - `test_ui6_no_credential_exposure`: Verifies zero API key or secret leakage.
- Full Engine Test Suite (`tests/`): All 635 tests pass cleanly, including golden evaluation verification and reproduction benchmarks.

**Result:** 635 passed, 1 warning (deprecation warning in testclient), 0 errors, execution time ~2m14s.

### 5.3 Golden Hash Invariant Verification
The golden evaluation result hash remains bit-for-bit identical:
$$\text{Golden Result Hash} = \mathtt{e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1}$$
Frozen core modules (`derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`) remain untouched.

---

## 6. Cryptographic SHA-256 Checksums

| File Path | SHA-256 Digest | Status |
| :--- | :--- | :--- |
| `docs/openapi/presentation-api-v1.yaml` | `36e10bef60a39d2df527bb124545f716c5ba1fd09eaac6d69b26124bb450876f` | Modified (Additive) |
| `engine/ipo_screening/presentation/models.py` | `29f6cd592a0bd237f42a23e7ee98692bd4308feb2ae803cdd387a25de9e5dd80` | Modified (Additive) |
| `engine/ipo_screening/presentation/service.py` | `5b30c3a609701c03a083dc0f7cfafa374bf333bdb4b73e3109f04645aa1a7f2b` | Modified (Additive) |
| `frontend/index.html` | `d47517f8b5261b7c02f2723fa41efa20b07c521d754876cbd1f83b3afff79348` | Modified |
| `frontend/styles.css` | `e06fe47387d91ed64b112808205e55e0eaea0c83e7245fc7237d3ac3d81cc958` | Modified |
| `frontend/api.js` | `cf485cbe2c43f925896d9cd74f06cfc0863046f69b286ba98051df803707fe23` | Modified |
| `frontend/app.js` | `644d5a1db8796505b015241b67cd6f6c38737ea8ccea57c46ffec7d8fd6ec40a` | Modified |
| `frontend/test/calibration.test.js` | `2024c1bb9b06cfd9866f37ab134321f3af8280ad86a60f887a0d564b46523c50` | Added |
| `tests/test_ui6_calibration.py` | `e5e867386a56aa327cdc0156abe60d2d6561fd342abf9b8f019cf65ba14d5bf3` | Added |
| `docs/UI-6-CALIBRATION-CONFIGURATION-PRESENTATION.md` | `[Self-Referencing Document]` | Added |
