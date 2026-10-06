# UI-2: Core Executive Dashboard & IPO Evaluation Detail Scorecard

**Authoritative Specification & Implementation Report**  
**Engine Baseline:** `v1.5.0` (Active Policy) | `v1.6.0-draft` (Inactive Calibration Proposal)  
**API Protocol:** UI-1 Presentation API (`docs/openapi/presentation-api-v1.yaml`)  
**Status:** DELIVERED & AUDITED  
**Date:** 2026-10-06  

---

## 1. Executive Summary

UI-2 delivers the first complete web presentation layer for the Indian Mainboard IPO Screening Engine. Built directly upon the frozen UI-1 Presentation Read-Model API, UI-2 provides institutional analysts, investment committees, and risk officers with high-fidelity, accessible, and strictly read-only visibility into screening evaluations, knockout determinations, module scores, and governance parameters.

### Delivered Components:
1. **Executive Dashboard (`#dashboard`):** High-level KPI cards, verdict distribution, score band histogram, recent evaluations feed, and active policy lifecycle indicator.
2. **IPO Discovery / Directory (`#directory`):** Real-time filtered search, deterministic pagination, issuer profiles, evaluation counts, latest scores, and semantic verdict badges.
3. **IPO Evaluation Detail Scorecard (`#evaluations/{id}`):** Comprehensive multi-section scorecard detailing evaluation identity, cryptographic hashes, confidence breakdown, score bounds, tri-state knockout rules (K1–K6), Modules A–F criteria breakdown, active penalties, and missing/unverified values catalog.
4. **Read-Only API Client Abstraction (`frontend/api.js`):** Modular ES client encapsulating all presentation endpoints with deterministic error handling and zero mutation capabilities.
5. **Institutional Design System (`frontend/styles.css`):** High-contrast, WCAG AA compliant responsive stylesheet with dedicated semantic palettes for verdicts (`APPLY`, `CONSIDER`, `AVOID`, `INSUFFICIENT_DATA`), knockout states (`CLEAR`, `TRIGGERED`, `UNVERIFIED`), and fail-closed markers (`UNKNOWN`, `NOT_APPLICABLE`).
6. **Automated Verification Suites:** 12 Node.js tests (`frontend/test/`) and 7 Python integration tests (`tests/test_ui2_frontend.py`), confirming asset serving, accessibility landmarks, fail-closed handling, zero score computation, and absence of configuration mutation controls.

---

## 2. Strict Architectural & Governance Invariants

UI-2 adheres strictly to all governance boundaries and security constraints mandated by the system architecture:

| Invariant | UI-2 Implementation & Verification | Status |
| :--- | :--- | :---: |
| **Zero Client-Side Calculation** | Frontend code contains zero arithmetic formulas for score aggregation, module weighting (`* 0.25`, etc.), penalty subtraction, or verdict thresholds. All scores, bounds, and verdicts are computed exclusively by engine core and projected by UI-1. | **VERIFIED** |
| **Strict Read-Only Enforcement** | `ApiClient` and HTTP handlers implement only `GET`, `HEAD`, and `OPTIONS`. Zero `POST`, `PUT`, `PATCH`, or `DELETE` methods exist in the client. | **VERIFIED** |
| **Fail-Closed Unknown Semantics** | Missing, unextracted, or unverified values are explicitly rendered as `UNKNOWN` or `UNVERIFIED`. Under no circumstances are null or undefined values converted to `0` or `0.00`. | **VERIFIED** |
| **Frozen Core Preservation** | Zero modifications to core files (`derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`, `extraction/price_band_notice.py`). | **VERIFIED** |
| **Golden Evaluation Determinism** | Golden Vishal Nirmiti result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` remains bit-for-bit identical. | **VERIFIED** |
| **Configuration Governance** | Active policy `v1.5.0` is displayed; draft proposal `v1.6.0` is displayed as inactive. Zero UI controls, buttons, or endpoints exist to activate or modify policy configurations. | **VERIFIED** |
| **Zero Credential Exposure** | Zero API keys, bearer tokens, or model provider credentials exist in client assets or HTML markup. | **VERIFIED** |

---

## 3. Detailed Component Architecture

### 3.1 Architecture Overview
```
+---------------------------------------------------------------------------------+
|                                 Browser Client                                  |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  |                            Header & Governance                            |  |
|  |  [IPO Screening Engine v1.5.0] [Dashboard] [Directory] [Policy: v1.5.0]  |  |
|  +---------------------------------------------------------------------------+  |
|                                       |                                         |
|  +------------------------------------+--------------------------------------+  |
|  |                                    |                                      |  |
|  v                                    v                                      v  |
|  #dashboard View                     #directory View                        #evaluations/{id} View
|  - KPI Summary Cards                 - Search Input                         - Scorecard Header & Mode
|  - Verdict Breakdown                 - Deterministic Table                  - Core Cryptographic Hashes
|  - Score Distribution                - Pagination Controls                  - Confidence & Score Range
|  - Recent Evaluations                - Latest Verdict Badges                - Knockout Rules (K1-K6)
|                                                                             - Modules A-F Score Breakdown
|                                                                             - Penalties & Missing Catalog
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  |                     ApiClient (frontend/api.js)                           |  |
|  |      - Strictly read-only HTTP GET requests                               |  |
|  |      - Deterministic ApiError wrapping                                    |  |
|  +---------------------------------------------------------------------------+  |
+---------------------------------------|-----------------------------------------+
                                        | HTTP GET
                                        v
+---------------------------------------------------------------------------------+
|                       FastAPI Presentation Service (/api/v1)                    |
|  - /health                   - /ipos                                            |
|  - /meta                     - /evaluations                                     |
|  - /configuration/current    - /evaluations/{id}                                |
|  - /static (mounted at /ui)  - /evaluations/{id}/evidence                       |
+---------------------------------------------------------------------------------+
```

### 3.2 Component Specifications

#### A. Executive Dashboard (`#dashboard`)
- **KPI Metrics Strip:** Total issuers tracked, total evaluations processed, latest screening verdict, and active policy version (`v1.5.0`).
- **Verdict Distribution Grid:** High-contrast cards displaying count and percentage breakdown across `APPLY`, `CONSIDER`, `AVOID`, and `INSUFFICIENT_DATA`.
- **Score Distribution Histogram:** Aggregated score bands (`0–19`, `20–39`, `40–59`, `60–79`, `80–100`) visualizing population screening distribution.
- **Recent Evaluations Ledger:** Paginated ledger with direct drill-down links to evaluation scorecards, displaying evaluation timestamp, mode (`DRAFT`, `PRICED`, `FINAL`), score, and verdict.

#### B. IPO Discovery & Directory (`#directory`)
- **Real-Time Search & Debounce:** Debounced full-text search across issuer names and identifiers without page reload.
- **Deterministic Pagination:** URL-state synchronized page indexing (`page`, `pageSize`) ensuring reproducible views.
- **Issuer Listing Table:** Issuer Name, Unique IPO ID, Sector Profile tag, Evaluation Count, Latest Score, Latest Verdict badge, and Detail Action button.

#### C. IPO Evaluation Detail Scorecard (`#evaluations/{id}`)
- **Header & Action Bar:** Back to directory navigation, issuer legal name, exchange symbol (`BSE:544321` etc.), evaluation mode badge (`FINAL`, `PRICED`, `PRE_PRICE`), and prominent verdict badge.
- **Section 1: Core Evaluation Identity:**
  - Evaluation ID, Evaluation Mode, Evaluated At timestamp (UTC).
  - Policy Specification Version (`v1.5`), Engine Version (`1.5.0`), Config Version (`1.5.0`).
  - Cryptographic Fingerprints: Result Hash, Source Manifest Hash, and Input Snapshot Hash.
- **Section 2: Executive Summary & Confidence Analysis:**
  - Final Score (`XX.X / 100.0`) and Base Score.
  - Deterministic Score Range: Lower Bound (`XX.X`) and Upper Bound (`XX.X`) indicating score boundary under missing information.
  - Confidence Rating badge (`HIGH`, `MEDIUM`, `LOW`) and Completeness percentage (`XX.X%`).
  - Critical Data Missing catalog and Unverified Knockouts summary.
- **Section 3: Knockout Rules Matrix (K1–K6):**
  - Tri-state rule indicators: `CLEAR` (green pill), `TRIGGERED` (red bold pill), and `UNVERIFIED` (amber pill).
  - Explicit rule titles (K1: Regulatory Debarment, K2: Track Record, K3: Negative Net Worth, K4: Promoters Litigation, K5: Auditor Resignation, K6: Over-leveraged Balance Sheet).
  - Missing required inputs displayed directly under unverified rules.
- **Section 4: Scoring Modules Breakdown (Modules A–F):**
  - Module A: Corporate Governance & Integrity (Max 25.0 pts)
  - Module B: Business Model & Industry Dynamics (Max 20.0 pts)
  - Module C: Financial Quality & Stability (Max 15.0 pts)
  - Module D: Issue Structure & Proceeds Allocation (Max 10.0 pts)
  - Module E: Valuation & Peer Multiple Comparison (Max 30.0 pts)
  - Module F: Overlays & Contextual Adjustments
  - Per-criterion tables displaying Criterion ID, Name, Formatted Value, Semantic State (`SCORED`, `UNKNOWN`, `NOT_APPLICABLE`), Earned Score, Max Score, Scorer Reason, and Capping Indicators.
- **Section 5: Penalties & Missing Data Catalog:**
  - Active Penalties list with deductions and regulatory citations.
  - Missing / Unverified Values catalog highlighting data points requiring further analyst investigation.

---

## 4. Visual Design System & WCAG AA Compliance

The UI-2 design system adheres to institutional financial terminal conventions:
- **Typography:** Modern high-legibility monospace stack (`ui-monospace`, `SFMono-Regular`, `Menlo`, `Consolas`) for numerical metrics, hashes, and identifiers; crisp system sans-serif for executive headings.
- **Color System & Semantic Tokens:**
  - `APPLY`: `#065f46` text, `#d1fae5` background, `#34d399` border (Contrast ratio > 5.2:1).
  - `CONSIDER`: `#1e40af` text, `#dbeafe` background, `#60a5fa` border (Contrast ratio > 5.5:1).
  - `AVOID`: `#991b1b` text, `#fee2e2` background, `#f87171` border (Contrast ratio > 6.1:1).
  - `INSUFFICIENT_DATA` / `UNKNOWN`: `#854d0e` text, `#fef9c3` background, `#facc15` border (Contrast ratio > 4.8:1).
  - `NOT_APPLICABLE`: `#475569` text, `#f1f5f9` background, `#cbd5e1` border.
- **Accessibility & ARIA Landmarks:**
  - Header tagged with `role="banner"`.
  - Main navigation tagged with `role="navigation"`.
  - Content container tagged with `role="main"`.
  - Screen views tagged with `role="region"` and explicit `aria-label` attributes.
  - Data tables equipped with semantic `<thead>`, `<tbody>`, and column header scopes.

---

## 5. Verification & Acceptance Results

### 5.1 Node.js Frontend Test Suite (`frontend/test/`)
```
> ipo-screening-engine-ui@1.0.0 test
> node --test test/*.test.js

TAP version 13
ok 1 - ApiClient - Initialisation and read-only protocol
ok 2 - ApiClient - System endpoints (getHealth, getMeta, getConfigurationStatus)
ok 3 - ApiClient - listIpos builds query parameters accurately
ok 4 - ApiClient - listEvaluations builds query parameters accurately
ok 5 - ApiClient - Detail endpoints encode URL parameters correctly
ok 6 - ApiClient - handles 404 and API error schemas
ok 7 - ApiClient - handles network disconnection error cleanly
ok 8 - ApiClient - rejects empty or missing IDs in getIpo and getEvaluation
ok 9 - App - Formatting helpers produce valid accessible HTML markup
ok 10 - App - Zero Score Calculation Invariant: source files contain no arithmetic weighting or scoring formulas
ok 11 - App - Governance Invariant: no policy activation or modification controls in frontend
ok 12 - App - Fail-Closed Invariant: missing/null values never default to zero
1..12
# tests 12
# pass 12
# fail 0
```

### 5.2 Python Static Serving & Integrity Suite (`tests/test_ui2_frontend.py`)
```
============================= test session starts ==============================
collected 7 items

tests/test_ui2_frontend.py::test_ui2_static_assets_served PASSED
tests/test_ui2_frontend.py::test_ui2_html_structure_and_aria_landmarks PASSED
tests/test_ui2_frontend.py::test_ui2_zero_calculation_invariant PASSED
tests/test_ui2_frontend.py::test_ui2_zero_mutation_and_read_only_protocol PASSED
tests/test_ui2_frontend.py::test_ui2_fail_closed_unknown_representation PASSED
tests/test_ui2_frontend.py::test_ui2_no_configuration_activation_controls PASSED
tests/test_ui2_frontend.py::test_ui2_no_credential_exposure PASSED

============================== 7 passed in 0.59s ===============================
```

### 5.3 Full Presentation Acceptance Suite
```
============================= test session starts ==============================
collected 28 items

tests/test_presentation_api.py .....................                     [ 75%]
tests/test_ui2_frontend.py .......                                       [100%]

======================== 28 passed, 1 warning in 2.42s =========================
```

### 5.4 Golden Regression & Frozen Core Audit
```
============================= test session starts ==============================
collected 19 items

tests/test_vishal_golden.py ...................                          [100%]

============================== 19 passed in 0.06s ==============================

Golden Result Hash: e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1 (BIT-FOR-BIT IDENTICAL)
Frozen Core Status: 100% UNTOUCHED
```

---

## 6. Artifact SHA-256 Checksums

| File Path | SHA-256 Digest |
| :--- | :--- |
| `frontend/index.html` | `a9ff47f9afc60746d8a71b28490a3d0ab2a9711107f3b14539f8b4aaa8cb54c7` |
| `frontend/styles.css` | `8eb70b5f51a355332d29c8afce83c343b54a5e32c864d8d889f7c26c638b030e` |
| `frontend/api.js` | `9feff7d6eeeb1ae482212a0638af97eff2bba778c9a16836a752ba818031180b` |
| `frontend/app.js` | `4f251f69a9bf8b02d2f87a765ee9b219c86503b40ec6ae2977ed1705431bc5d4` |
| `frontend/package.json` | `cb7c5c4363b00b807f929ef7b7dfe38753805875f5a33de45eff2a05887acbac` |
| `frontend/test/api.test.js` | `7cda445f46a17067e0460a623917c83582cd3a8d3f784c1b835e2c4d8ef5e088` |
| `frontend/test/app.test.js` | `e35ab512678d8fe5e5a60832b1e71d9be0d21f24bdb9d538604fb49c604e30de` |
| `tests/test_ui2_frontend.py` | `75c7e12e93da9758f3f82a14aa22717ab4be0a97470e4a419f3e50c467907f86` |
| `engine/ipo_screening/presentation/api.py` | `805867ee05e78190826ed6a502286ccd0de8ed73315389a07a5693d65aaa8eb9` |
