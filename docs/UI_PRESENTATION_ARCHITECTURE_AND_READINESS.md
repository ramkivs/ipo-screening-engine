# IPO Screening Engine — UI & Product Presentation Architecture & Readiness Report

**Document ID:** `DOC-UI-ARCH-READINESS-20261006`  
**Authoritative Completed Delivery Lineage:** Commit `690d4722294f18b4897676ede8392314f63f3128`  
**Current Baseline:** Commit `b61c4840a5ea4e616123091574f2706e7baa759c`  
**Current Main Baseline:** Commit `01ba66c12ca1195fd7acbd287c3e39a019808094` (`main`)  
**Working Session Branch:** `arena/01a10b42-ipo-screening-engine`  
**Program Authority:** Ramki  
**Governance Mode:** READ-ONLY INVESTIGATION (Zero Implementation / Zero Configuration Mutation / Zero Activations / Zero Merges)  

---

## 1. Executive Summary

This architecture and readiness report investigates the future presentation and user interface (UI) layer for the Indian Mainboard IPO Screening Engine. 

### Key Findings:
1. **Engine Core is Complete and Verified**: Across the completed delivery lineage through commit `690d4722294f18b4897676ede8392314f63f3128`, the backend calculation engine, extraction pipeline, post-listing observation models, deterministic return calculation, historical backtest analytics, and governed calibration proposal framework are **100% complete, fully implemented, and validated across 575 automated tests**. Phase 6A–6D capabilities are completed engineering assets and must **not** be redesigned or rebuilt.
2. **Current UI State is Prototype / Reference Only**: The existing presentation asset in the repository consists solely of a legacy single-file proof-of-concept (`handoff/reference/ipo-scorer_4.html`, 41.5 KB). While it demonstrated early client-side PDF text extraction and score badge rendering for Spec v1.4, it is architecturally obsolete: it attempts to duplicate scoring logic in client-side JavaScript, exposes LLM credentials in the browser, lacks all post-listing observation and backtesting surfaces, and does not consume the authoritative Python engine's immutable records.
3. **UI is a First-Class Mandatory Product Requirement**: Command-line tooling (`ipo_screen.py`) and 14-sheet Excel workbooks (`IPO_Screening_History.xlsx`) provide complete headless execution, but institutional investment committees, analysts, and governance reviewers require a modern visual dashboard to inspect scorecards, examine evidence quotes, navigate historical evaluations, and interact with backtest scatter plots.
4. **Architecture: Decoupled Read-Only Presentation Layer**: The UI must be constructed under a strict unidirectional architecture:
   $$\text{Authoritative Engine / Stored Records} \longrightarrow \text{Read-Only Presentation API (FastAPI)} \longrightarrow \text{Modern Web UI}$$
   The UI will be a **pure presentation surface**. Browser-side scoring, metric derivation, return calculations, and credential handling are **strictly prohibited**.
5. **Implementation Readiness Decision**: **`READY WITH CONTRACT GAPS`**. The backend engine and immutable storage formats are complete and robust. However, before coding frontend components, a formal OpenAPI/REST presentation read-model specification must be defined to bridge raw filesystem stores with browser clients without exposing filesystem mechanics or security vulnerabilities.

---

## 2. Existing UI / Presentation Inventory

A complete repository audit was conducted across all files, git history, and delivery tags to identify presentation-related assets:

| Asset Name | Location | Type / Tech | Operational Role | Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Interactive Scorer Prototype** | `handoff/reference/ipo-scorer_4.html` | Standalone HTML / JS / CSS (41.5 KB), PDF.js | Client-side extraction & scoring prototype for Spec v1.4 | **PROTOTYPE / REFERENCE ONLY**. Duplicates scoring logic in JS; exposes Anthropic API keys in browser; lacks Phase 5/6/7 features. |
| **14-Sheet Historical Excel Projection** | `engine/ipo_screening/excel.py` | Python / `openpyxl` | Headless projection of immutable records to `IPO_Screening_History.xlsx` | **PRODUCT_COMPLETE**. Generates all 14 specified sheets (`IPO_Master`, `Evaluations`, `Post_Listing`, `Backtest`, etc.). Pure projection; not an interactive UI. |
| **Command-Line Interface (CLI)** | `engine/tools/ipo_screen.py` | Python / `argparse` | Headless execution CLI with 14 subcommands | **PRODUCT_COMPLETE**. Rich terminal reporting with ANSI color coding, JSON outputs, diff summaries, and shadow evaluations. |
| **Markdown Reports & Runbooks** | `docs/` (`FINAL_REPORT.md`, `RUNBOOK.md`) | Markdown | Comprehensive operational and architectural documentation | **PRODUCT_COMPLETE**. Authoritative reference documentation. |

### In-Depth Forensic Inspection of `handoff/reference/ipo-scorer_4.html`
Detailed inspection of `ipo-scorer_4.html` revealed:
* **Extraction Capabilities**: Implements client-side PDF text extraction using PDF.js v3.11.174. Discovers prospectus sections via regex patterns (`SEC={offer, cap, obj, basis, fin, rpt, lit, mgmt, ind, bus}`).
* **Security Defect (Direct Client Credentials)**: Lines 231–238 implement direct browser-to-Anthropic HTTP calls:
  ```javascript
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': k,
      'anthropic-dangerous-direct-browser-access': 'true'
    },
    ...
  });
  ```
  This exposes long-lived API keys directly in browser memory and network traffic, violating Spec Section 25 and Technical Design Section 16.
* **Scoring Logic Duplication**: Lines 45–157 implement `derive(i, c)` and `score(inp, cfg, mode)` in client-side JavaScript. This violates the Single Source of Truth principle. The JS implementation uses naive binary floating-point math, lacks exact Decimal arithmetic, fails to enforce Kleene tri-state logic for knockouts, and ignores Phase 5 pre-score enrichment precedence.
* **Missing Presentation Surfaces**: Contains zero presentation components for:
  - Post-listing observations (Listing day, 1W, 1M, 6M actual prices and returns)
  - Benchmark tracking (Nifty 50 alpha)
  - Backtest analytics (Hit rates, avoided-loss rates, Rank IC, decile spreads)
  - Governed calibration proposals and configuration diffs
  - Multi-IPO historical outcome store navigation

---

## 3. Current UI Classification

The current user interface capability of the repository is formally classified as:

### **`PROTOTYPE / REFERENCE ONLY`**

* **Reasoning**: While `ipo-scorer_4.html` demonstrates that an interactive visual interface was envisioned, it is an early, uncoupled prototype that cannot be used in production. It predates the implementation of the authoritative Python engine (Phases 1–7), contains dangerous security anti-patterns (client-side API keys), and duplicates scoring logic. The repository contains **no productized web frontend**.

---

## 4. Authoritative Backend & Data Inventory

The backend calculation engine provides rich, deterministic, immutable data structures across all phases. A detailed audit of structures A through AI is documented in `docs/UI_PRESENTATION_CAPABILITY_MATRIX.md`. The core categories are:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Authoritative Data Categories                         │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ 1. Pre-Listing Screening      │ • CanonicalInput (43886069...)              │
│    (Phases 1–4, 5A–5J)        │ • EvaluationRecord (result hash e84f8bc0...)│
│                               │ • 35+ Pure Derived Metrics                  │
│                               │ • Tri-State Knockouts (K1–K6)               │
│                               │ • Module Scores A–F (Max 100)               │
│                               │ • Confidence & Score Range (Lower / Upper)  │
│                               │ • Evidence Registry (Quotes, Pages, Sources)│
├───────────────────────────────┼─────────────────────────────────────────────┤
│ 2. Post-Listing Observations  │ • PostListingObservation (Per-Horizon JSON) │
│    (Phase 6A)                 │ • Trading Calendar Resolver (NSE / BSE)     │
│                               │ • Exact Decimal Returns & Alpha vs Nifty 50 │
│                               │ • Corporate Action Adjustment Factors       │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ 3. Backtest & Analytics       │ • BacktestDataset (Multi-IPO Canonical Hash)│
│    (Phases 6B, 6C)            │ • Spearman Rank IC (Score vs 6M Alpha)      │
│                               │ • Hit Rate (% APPLY with Positive Alpha)    │
│                               │ • Avoided-Loss Rate (% AVOID Negative Alpha)│
│                               │ • Decile / Quintile Performance Spreads     │
│                               │ • 8-Point Data Leakage Audit Engine         │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ 4. Governed Calibration       │ • CalibrationProposal (Cryptographic Hash)  │
│    (Phases 6D, 7)             │ • Inactive Candidate Config v1.6.0          │
│                               │ • In-Memory Shadow Evaluation Engine        │
│                               │ • Config Diff Engine (Approved Scope Only)  │
└───────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 5. UI Source-of-Truth Architecture

To ensure mathematical reproducibility and prevent calculation divergence, the product presentation architecture must enforce a strict, unidirectional data flow:

```
┌─────────────────────────────────────────────────────────────┐
│                 AUTHORITATIVE ENGINE CORE                   │
│   - engine/ipo_screening/ (Pipeline, Derived, Scoring)      │
│   - 100% Frozen Core Integrity (SHA-256 Checksums)          │
│   - Immutable Filesystem Store (<store>/<eval_id>/)         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ Read-Only Access (Filesystem / API)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            READ-ONLY PRESENTATION API (FASTAPI)             │
│   - Queries Immutable Records & Manifests                   │
│   - Generates Normalized JSON Read Models                   │
│   - Enforces Secure Server-Side Credential Management       │
│   - Pure Projection / Zero State Mutation                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ HTTPS / JSON Payloads
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    MODERN WEB UI CLIENT                     │
│   - React / TypeScript Frontend Application                 │
│   - Interactive Scorecards, Confidence Gauges, Badges       │
│   - Evidence Drawer with Prospectus Quote Viewer            │
│   - Backtest Visualizations (Scatter, Deciles, Gauges)      │
│   - Configuration Diff & Governance Status Badges           │
└─────────────────────────────────────────────────────────────┘
```

### The Inviolable UI Boundary Rules:
1. **Zero Client-Side Calculation**: The browser UI must **never** derive financial metrics, evaluate knockout conditions, compute scores, or calculate realized returns. It is strictly a visual renderer of server-provided numbers.
2. **Deterministic Source of Truth**: The `EvaluationRecord` and `PostListingObservation` stored on disk are the sole authoritative truth. If the UI displays a number, that number must trace directly to an immutable record hash.
3. **No Overwrites / Immutability**: The UI cannot edit or mutate a finalized evaluation. Re-evaluations create distinct historical records with new evaluation timestamps and IDs.

---

## 6. Presentation / Backend Boundary

The responsibilities between the backend engine, presentation API, and frontend client are strictly partitioned:

| Functional Responsibility | Headless Engine (Python) | Presentation API (FastAPI) | Frontend UI (Browser) |
| :--- | :---: | :---: | :---: |
| **PDF Extraction & OCR** | **AUTHORITATIVE** | Mediates Upload | File Selector & Progress Bar |
| **Model API Key Management** | Prohibited | **AUTHORITATIVE (Vault/Env)** | **STRICTLY PROHIBITED** |
| **Input Validation (Schema & Semantic)**| **AUTHORITATIVE** | Validates Payloads | Form Validation Feedback |
| **Derived Financial Metrics** | **AUTHORITATIVE** | Passes Through | Display Value & Formula Tooltip |
| **Knockout Evaluation (Kleene Logic)** | **AUTHORITATIVE** | Passes Through | Tri-State Badges (Clear/Triggered/Unverified) |
| **Scoring & Weighting (Modules A–F)** | **AUTHORITATIVE** | Passes Through | Score Breakdown Bars & Gauges |
| **Verdict Determination** | **AUTHORITATIVE** | Passes Through | Visual Verdict Badge (`APPLY`/`CONSIDER`/`AVOID`) |
| **Post-Listing Return & Alpha Math** | **AUTHORITATIVE** | Aggregates Timeline | Line Charts & Horizon Cards |
| **Backtest Statistical Diagnostics** | **AUTHORITATIVE** | Formats Chart Data | Scatter Plots & Decile Bar Charts |
| **Interactive Sorting, Filtering, Search**| Not Applicable | Query Parameters | **AUTHORITATIVE (Client Grid)** |
| **Responsive Layout & Theme (Dark/Light)**| Not Applicable | Not Applicable | **AUTHORITATIVE (CSS / Client)** |

---

## 7. Required UI Product Surfaces

The future web UI must provide eight dedicated product surfaces:

### 7.1 Dashboard (`/dashboard`)
* **Purpose**: Portfolio-level executive summary of evaluated IPOs and engine health.
* **Visual Components**:
  * **Metric KPI Cards**: Total IPOs Evaluated, Average Score, Distribution by Verdict (`% APPLY`, `% CONSIDER`, `% AVOID`, `% INSUFFICIENT_DATA`), Active Configuration Badge (`v1.5.0 ACTIVE`).
  * **Recent Evaluations Table**: Chronological list of recent evaluations with issuer name, issue date, mode (`PRELIMINARY` vs `FINAL`), final score, verdict badge, confidence indicator, and quick links to detail views.
  * **Score Distribution Chart**: Histogram of final scores across the universe with verdict color bands.

### 7.2 IPO Evaluation Detail (`/evaluations/{id}`)
* **Purpose**: Comprehensive, institutional-grade scorecard for an individual IPO.
* **Visual Components**:
  * **Header Banner**: Company name, IPO ID, ICDR Route (`6(1)`/`6(2)`), Sector Profile, Issue Date, Evaluation Mode, Timestamp, Engine/Config Versions, and Golden Result Hash.
  * **Verdict & Score Summary Card**: Large verdict badge, final score (e.g., `35.0 / 100`), base score (`38.0`), total penalties (`-3.0`), score range bar (`25.0 – 62.0`), and points-weighted confidence gauge (`Low - 73%`).
  * **Module Breakdown (A through F)**: Expandable accordion cards displaying module score vs max (e.g., `Module A: Financial Quality - 14.0 / 25.0`), criteria table with metric values, benchmark thresholds, points awarded, and reason codes.
  * **Knockout Inspection Gate (K1–K6)**: Tri-state status cards (`CLEAR` [green], `TRIGGERED` [red], `UNVERIFIED` [amber]) explicitly naming any missing input requirements.
  * **Penalties Card**: Itemized list of active penalties with point deductions and triggers.
  * **Missing / Unverified Data Drawer**: Collapsible list of missing data items explaining the score range spread.

### 7.3 Evidence & Provenance Explorer (`/evaluations/{id}/evidence`)
* **Purpose**: Complete audit trail linking every scored number to its prospectus source.
* **Visual Components**:
  * **Dual-Pane Audit View**: Left pane lists all canonical fields and derived metrics; right pane displays the evidence registry record.
  * **Prospectus Citation Box**: Document name, fiscal period, exact page number, table reference, and verbatim extracted quote.
  * **Formula Inspector**: Clear mathematical formula definition showing how raw inputs mapped to the derived metric.

### 7.4 Historical Evaluation Timeline (`/evaluations/{id}/history`)
* **Purpose**: Side-by-side progression tracking across the IPO lifecycle.
* **Visual Components**:
  * **Lifecycle Stepper**: Visual progression (`PRELIMINARY` $\to$ `FINAL` $\to$ `POST_LISTING_1W` $\to$ `POST_LISTING_1M` $\to$ `POST_LISTING_6M`).
  * **Delta Comparison View**: Compares Day-1 Preliminary evaluation against Day-3 Final evaluation, highlighting subscription updates, price band finalization, score adjustments, and verdict narrowing.

### 7.5 Post-Listing Performance (`/evaluations/{id}/performance`)
* **Purpose**: Realized return and alpha tracking against post-listing benchmarks.
* **Visual Components**:
  * **Horizon Cards**: Dedicated cards for Listing Day, 1-Week, 1-Month, and 6-Month horizons.
  * **Performance Metrics**: Issue Price, Listing Open, Listing Close, Horizon Close, Realized Return %, Nifty 50 Benchmark Return %, and Net Alpha %.
  * **Corporate Action Alert**: Badges indicating stock splits, bonus issues, or dividend adjustments applied to prices.

### 7.6 Backtest Analytics Dashboard (`/backtest`)
* **Purpose**: Empirical performance analytics across the entire evaluated IPO universe.
* **Visual Components**:
  * **Sample Maturity Card**: Sample size ($N$), maturity classification (`DESCRIPTIVE_ONLY`, `EXPLORATORY`, `STATISTICALLY_ACTIONABLE`), and leakage audit status (`PASS` [green]).
  * **Score vs Return Scatter Plot**: Interactive scatter chart plotting Final Pre-Listing Score ($X$-axis) against 6-Month Alpha ($Y$-axis), displaying the linear regression line, Spearman Rank IC ($+0.165$), and $p$-value.
  * **Hit Rate & Downside Protection Gauges**: Donut charts displaying Hit Rate (% of APPLY with positive alpha) and Avoided-Loss Rate (% of AVOID with negative alpha).
  * **Decile / Quintile Performance Spreads**: Column chart showing mean excess returns across score buckets, visualizing the monotonic spread from top bucket to bottom bucket.
  * **Temporal Vintage Breakdown**: Bar charts displaying IC and hit rates across calendar cohorts (e.g. 2024 vs 2025).

### 7.7 Calibration & Governance Surface (`/governance/calibration`)
* **Purpose**: Governed configuration comparison and proposal review.
* **Visual Components**:
  * **Governance Status Banner**: Prominent display of the Inactive Status: `ACTIVE BASELINE: v1.5.0` vs `CANDIDATE: v1.6.0 (IMPLEMENTED_INACTIVE)`.
  * **Module Weight Comparison**: Grouped horizontal bar chart showing baseline vs proposed weights (Module A: 25$\to$30, Module B: 20$\to$15, C–F: unchanged).
  * **Maturity Gate Status**: Visual indicator of the 4-tier calibration gate (`CALIBRATION_CANDIDATE`).
  * **Shadow Evaluation Comparison**: In-memory rescoring summary showing score distribution deltas, average shift, and verdict migration matrix.
  * **Knockout Firewall Verification**: Cryptographic badge confirming zero automated knockout changes (`FIREWALL_ENFORCED_EMPTY`).

### 7.8 Audit & Traceability Graph (`/audit/{id}`)
* **Purpose**: End-to-end provenance graph visualization.
* **Visual Components**:
  * **Graph Flow**: `PDF Section` $\longrightarrow$ `Evidence Item` $\longrightarrow$ `Canonical Input` $\longrightarrow$ `Derived Metric` $\longrightarrow$ `Module Score` $\longrightarrow$ `Final Verdict`.
  * **Cryptographic Verification Box**: Instant client-side verification of artifact SHA-256 hashes against `manifest.json`.

---

## 8. Navigation Model

The UI navigation must be intuitive, professional, and optimized for equity research workflows:

```
┌──────────────────────────────────────────────────────────────┐
│  IPO SCREENING ENGINE              [Active Config: v1.5.0]   │
├──────────────────────────────────────────────────────────────┤
│  [PRIMARY NAVIGATION]                                        │
│    📊 Dashboard         (/dashboard)                         │
│    🏢 IPO Universe      (/universe)                          │
│    📈 Backtest Analytics(/backtest)                          │
│    ⚖️ Governance & Diff (/governance)                        │
│                                                              │
│  [CONTEXT NAVIGATION - When viewing a specific IPO]          │
│    • Scorecard Summary  (/evaluations/{id})                  │
│    • Module Breakdown   (/evaluations/{id}/modules)          │
│    • Evidence Explorer  (/evaluations/{id}/evidence)         │
│    • Lifecycle History  (/evaluations/{id}/history)          │
│    • Post-Listing Alpha (/evaluations/{id}/performance)      │
│    • Audit Provenance   (/evaluations/{id}/audit)            │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. Evidence & Provenance Model

Auditability is a core regulatory invariant of the engine:
1. **Interactive Evidence Popovers**: Every cell in the scorecard carrying a financial figure or ratio must support hover/click popovers displaying:
   * Source filing name (e.g., `Vishal Nirmiti Limited - RHP.pdf`)
   * Table / Section name (e.g., `Restated Statement of Profit and Loss`)
   * Page number citation (e.g., `Page 142`)
   * Exact verbatim extracted quote
2. **Side-by-Side PDF Viewer**: In the Evidence Explorer view, clicking an evidence citation should open an embedded PDF viewer scrolled directly to the cited page with bounding-box highlights where available.
3. **No Uncited Claims**: If an input lacks evidence, the UI must flag it with an amber badge (`EVIDENCE_MISSING`), showing that the value relies on unverified manual input.

---

## 10. Post-Listing Presentation

The post-listing view must accurately project the Phase 6A observation models:
1. **Multi-Horizon Tabs**: Clear tabular breakdown across `LISTING_DAY`, `ONE_WEEK`, `ONE_MONTH`, and `SIX_MONTH`.
2. **Price & Benchmark Table**:
   * Issue Price (INR)
   * Official Exchange Closing Price (NSE/BSE)
   * Raw Realized Return %
   * Nifty 50 Base Index & Observation Index
   * Nifty 50 Return %
   * Net Excess Return (Alpha %)
3. **Status Badges**: Every horizon must display its observation status:
   * `VERIFIED` (Green): Full trading day close and benchmark verified.
   * `UNVERIFIED` (Amber): Price pending secondary source reconciliation.
   * `INCOMPLETE` (Grey): Horizon date not yet reached (future maturity).
   * `INVALID` (Red): Data contradiction or missing exchange feed.

---

## 11. Backtest Presentation

The backtest surface must project the Phase 6C analytics engine:
1. **Sample Maturity Warning**: If $N < 15$, the UI must prominently display an informational banner: `SAMPLE SIZE MATURITY: DESCRIPTIVE ONLY (N = {count}). Statistical diagnostics are exploratory and not actionable for automated policy change.`
2. **Score-vs-Return Scatter**: Interactive plot with tooltips identifying each IPO dot, hover display of final score, realized 6M return, and excess return.
3. **Information Coefficient (Rank IC)**: High-level KPI card displaying Spearman Rank IC (e.g., `+0.165`), accompanied by the $t$-statistic, $p$-value, and directional interpretation.
4. **Hit & Avoidance Rates**: Clear visual presentation of institutional efficacy:
   * Hit Rate: `X% of APPLY recommendations generated positive alpha over Nifty 50.`
   * Avoided-Loss Rate: `Y% of AVOID recommendations protected capital (negative alpha).`
5. **Decile Spread Bar Chart**: Grouped bar chart showing average alpha across score buckets.

---

## 12. Calibration Presentation

The calibration surface must enforce the Fundamental Governance Invariant:
$$\text{EVIDENCE} \longrightarrow \text{PROPOSAL} \ne \text{APPROVAL} \ne \text{IMPLEMENTATION} \ne \text{ACTIVATION}$$

1. **Clear Lifecycle Distinctions**:
   * **PROPOSAL**: Visualized as a drafted calibration with cryptographic provenance.
   * **APPROVAL**: Marked with Program Authority authorization metadata (e.g., Ramki approval).
   * **IMPLEMENTATION**: Marked as `IMPLEMENTED_INACTIVE` in configuration files.
   * **ACTIVATION**: Gated and blocked in production.
2. **Side-by-Side Configuration Diff**: Visual diff table showing baseline weights vs proposed weights:
   * Module A (Financial Quality): `25.0` $\to$ `30.0` (+5.0 pts) [Green]
   * Module B (Valuation): `20.0` $\to$ `15.0` (-5.0 pts) [Red]
   * Modules C, D, E, F: `Unchanged` [Grey]
3. **Shadow Evaluation Impact Matrix**: Visual matrix showing how historical verdicts would shift if the candidate configuration were active:
   * Total Scored: $N$
   * Verdict Changes: e.g., 1 issuer shifted from `CONSIDER` to `APPLY`.
   * Mean Score Delta: e.g., $+1.2$ points.

---

## 13. Security & Credential Boundary

### Critical Architectural Vulnerability in Prototype:
The prototype in `handoff/reference/ipo-scorer_4.html` accepted Anthropic API keys directly in a browser form input and issued client-side HTTP requests with `anthropic-dangerous-direct-browser-access: true`.

### Mandatory Production Architecture:
```
┌────────────────────────┐                   ┌────────────────────────┐
│      WEB BROWSER       │                   │    FASTAPI BACKEND     │
│                        │                   │                        │
│  User selects PDF file ├──────POST /pdf────► Ingests PDF file       │
│  (Zero API keys held)  │                   │ Calls LLM via server   │
│                        │                   │ API Key held in VAULT  │
│  Receives Canonical    │◄──────JSON────────┤ Returns structured     │
│  Input JSON            │                   │ CanonicalInput payload │
└────────────────────────┘                   └────────────────────────┘
```
1. **Zero Browser Secrets**: No API keys, database credentials, or private exchange tokens may ever be transmitted to or stored in client-side storage (`localStorage`, `sessionStorage`, or cookies).
2. **Server-Side Secret Management**: Model provider keys (`ANTHROPIC_API_KEY`, etc.) reside strictly in server environment variables or enterprise secret vaults (AWS Secrets Manager, HashiCorp Vault).
3. **Cross-Origin Security**: API servers must enforce strict Content Security Policy (CSP), CORS allowlists, and disable iframe framing outside authorized domains.

---

## 14. Visualization Requirements

| Visualization Component | Authoritative Engine Source | Target Surface | Chart Type | Aggregation / Computation Rules |
| :--- | :--- | :--- | :--- | :--- |
| **Score Distribution** | `EvaluationRecord.score.final_score` | Dashboard | Histogram | Backend provides bucketed histogram counts. |
| **Verdict Breakdown** | `EvaluationRecord.verdict.verdict` | Dashboard | Donut Chart | Backend provides categorical counts. |
| **Module Contributions** | `EvaluationRecord.score.modules[]` | Evaluation Detail | Stacked Bar / Radar | Direct rendering of Module A–F scores. |
| **Score Range & Uncertainty**| `EvaluationRecord.score_range` | Evaluation Detail | Bullet / Range Bar | Lower bound, final score, upper bound. |
| **Return by Horizon** | `PostListingObservation.return_set` | Performance | Grouped Column | Raw return vs Nifty 50 return per horizon. |
| **Score vs Return Scatter** | `BacktestDatasetRow.final_score` + `horizons.6M.alpha` | Backtest | Scatter Plot | Backend provides point pairs; UI renders SVG dots and trendline. |
| **Rank IC Correlation** | `AnalyticsSummary.rank_ic` | Backtest | KPI Gauge / Card | Pre-computed Spearman correlation and p-value. |
| **Decile Performance** | `AnalyticsSummary.decile_buckets` | Backtest | Column Chart | Pre-computed mean return per score bucket. |
| **Config Diff Comparison**| `ConfigDiffReport.changed_scoring_fields` | Governance | Grouped Horizontal Bar | Side-by-side Module A–F weights (1.5 vs 1.6). |

---

## 15. UX Priority Matrix (MUST / SHOULD / LATER)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UX CAPABILITY PRIORITY BREAKDOWN                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  MUST HAVE (First UI Release - Core MVP)                                    │
│    1. Executive Dashboard (IPO list, verdict badges, scores, config status) │
│    2. IPO Evaluation Detail (Full scorecard, modules A-F, knockouts, ranges)│
│    3. Evidence & Provenance Explorer (Prospectus citations, page & quote)   │
│    4. Historical Evaluation Timeline (Preliminary vs Final comparison)      │
│    5. Post-Listing Performance Cards (1W, 1M, 6M returns & Nifty 50 alpha) │
│    6. Backtest Analytics Dashboard (Score vs return scatter, Rank IC)       │
├─────────────────────────────────────────────────────────────────────────────┤
│  SHOULD HAVE (Second UI Release)                                            │
│    7. Side-by-Side Multi-IPO Comparator (Compare 2-3 issuers)               │
│    8. Decile / Quintile Performance Deep-Dive                               │
│    9. Vintage & Holdout Temporal Breakdown                                  │
│   10. Interactive PDF Embedded Viewer with Page Auto-Navigation             │
│   11. Excel / CSV Report Download Action Buttons                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  LATER (Subsequent Enterprise Releases)                                     │
│   12. Calibration Proposal Diff & In-Memory Shadow Rescoring Simulator      │
│   13. Multi-User Authentication & Role-Based Access Control (RBAC)          │
│   14. Analyst Watchlists, Notes & Tagging                                   │
│   15. Automated Real-Time Price Ingestion Webhooks                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Technical & Environmental Dependencies

| Dependency | Category | Current Status | Impact on UI Implementation | Priority |
| :--- | :--- | :--- | :--- | :---: |
| **Authoritative Delivery Lineage (`690d472`)** | Architecture | Verified (575 passing tests) | **NON-BLOCKING**. Full calculation and analytical engine available. | P0 |
| **PR #3 / Main Consolidation** | Release Governance | OPEN / UNMERGED | **NON-BLOCKING for development**; BLOCKING for production release to `main`. | P0 |
| **Filesystem `EvaluationStore`** | Data Source | Implemented (`evaluation.py`) | **NON-BLOCKING**. FastAPI read-model can directly traverse `<store>/`. | P1 |
| **REST Presentation Read-Model API (`UI-1`)** | Backend Boundary | Unbuilt Specification | **BLOCKING FOR FRONTEND IMPLEMENTATION**. Must define API endpoints first. | P1 |
| **Relational Persistence (PostgreSQL)** | Storage | Deferred (P3 gap) | **NON-BLOCKING**. API layer abstracts storage; swap to SQL is seamless. | P3 |
| **Live Streaming Market Feeds** | Data Feeds | Deferred (P2 gap) | **NON-BLOCKING**. File-based Bhavcopy/JSON feeds supply all post-listing data. | P2 |
| **Authentication & RBAC** | Security | Unbuilt | **NON-BLOCKING for local/demo**; BLOCKING for multi-tenant deployment. | P3 |

---

## 17. Proposed UI Implementation Roadmap (UI-0 through UI-8)

```
UI-0: Product Presentation Architecture & Contract Specification (COMPLETE)
  │
UI-1: Read-Only Backend Presentation API Boundary (FastAPI Read Model)
  │
UI-2: Core Executive Dashboard & IPO Evaluation Detail Scorecard
  │
UI-3: Interactive Evidence & Provenance Explorer
  │
UI-4: Historical Lifecycle & Post-Listing Performance Surfaces
  │
UI-5: Backtest Analytics & Visualization Dashboard (Scatter, Rank IC)
  │
UI-6: Governed Calibration & Configuration Diff Surface
  │
UI-7: Enterprise Authentication, Authorization & User State (RBAC)
  │
UI-8: Production Hardening, Subresource Integrity & Security Audit
```

### Detailed Roadmap Workstream Stages:
* **UI-0: Product Presentation Architecture & Contract Specification (This Milestone)**
  * *Deliverable*: Authoritative UI architecture report and data contract matrix.
  * *Status*: **COMPLETE**.
* **UI-1: Read-Only Backend Presentation API Boundary (FastAPI)**
  * *Objective*: Build a lightweight, read-only Python FastAPI service exposing normalized REST endpoints (`/api/v1/evaluations`, `/api/v1/evaluations/{id}`, `/api/v1/backtest/latest`, etc.) reading directly from the immutable `EvaluationStore`.
  * *Dependencies*: Lineage `690d472`.
* **UI-2: Core Executive Dashboard & IPO Evaluation Detail Scorecard**
  * *Objective*: Implement the primary React / TypeScript frontend application featuring the Portfolio Dashboard and the complete IPO Evaluation Detail Scorecard.
  * *Dependencies*: UI-1.
* **UI-3: Interactive Evidence & Provenance Explorer**
  * *Objective*: Build the dual-pane evidence drawer with prospectus quote citations, page navigation, and mathematical derivation tooltips.
  * *Dependencies*: UI-2.
* **UI-4: Historical Lifecycle & Post-Listing Performance Surfaces**
  * *Objective*: Implement side-by-side preliminary vs final evaluation comparison and multi-horizon post-listing return/alpha tracking cards.
  * *Dependencies*: UI-2.
* **UI-5: Backtest Analytics & Visualization Dashboard**
  * *Objective*: Implement interactive charting for Score-vs-Return scatter plots, Rank IC gauges, hit rates, avoided-loss rates, and decile spreads.
  * *Dependencies*: UI-1.
* **UI-6: Governed Calibration & Configuration Diff Surface**
  * *Objective*: Implement the configuration diff viewer, proposal provenance inspector, and in-memory shadow evaluation comparison view.
  * *Dependencies*: UI-1.
* **UI-7: Enterprise Authentication, Authorization & User State (RBAC)**
  * *Objective*: Introduce secure session management, role-based permissions (Viewer, Analyst, Reviewer, Admin), and analyst audit logging.
  * *Dependencies*: UI-2.
* **UI-8: Production Hardening, Subresource Integrity & Security Audit**
  * *Objective*: Production bundle optimization, CSP headers, automated frontend unit tests, and cross-browser accessibility compliance.
  * *Dependencies*: UI-2 through UI-7.

---

## 18. Implementation Readiness Decision

The current state of the IPO Screening Engine regarding frontend UI implementation is formally decided as:

### **`READY WITH CONTRACT GAPS`**

### Technical Justification:
1. **Engine Core is 100% Ready**: The underlying computational models, scoring engine, persistence records, post-listing observation models, return calculations, and statistical backtest analytics are fully functional, thoroughly tested (575 passing tests), and architecturally stable.
2. **Contract Gaps Must Be Resolved First**: While the data exists in immutable filesystem JSON files, there is currently **no formal REST / HTTP API specification** defining how the frontend will query these records. Building a React frontend directly against filesystem paths or ad-hoc scripts would violate separation of concerns and introduce brittle coupling.
3. **Prerequisite Contract Requirements Before Implementation**:
   * **Contract Gap 1 (Presentation REST API Specification)**: Define an OpenAPI 3.1 specification for the read-only presentation endpoints (`GET /api/v1/evaluations`, `GET /api/v1/evaluations/{id}/detail`, `GET /api/v1/evaluations/{id}/evidence`, `GET /api/v1/post-listing/{id}`, `GET /api/v1/backtest/summary`).
   * **Contract Gap 2 (Server-Side Extraction Gateway)**: Specify the server-side API contract to mediate RHP PDF uploads and execute LLM extraction without client-side API key exposure.
   * **Contract Gap 3 (Pagination & Query Contracts)**: Standardize query parameters for filtering, sorting, and paginating large evaluation universes.

---

## 19. Exact Next Execution Gate

### **RECOMMENDED GATE: `GATE UI-1 (PRESENTATION API CONTRACT & READ-MODEL IMPLEMENTATION)`**

* **Action**: Authorize Phase `UI-1` to:
  1. Define the formal OpenAPI / REST contract for the read-only presentation API.
  2. Implement the read-only FastAPI presentation service reading from `EvaluationStore` without modifying the Frozen Core or scoring logic.
  3. Validate the API endpoints against the existing Vishal Nirmiti golden evaluation and post-listing fixtures.
* **Governance Boundary**: Zero mutations to `engine/ipo_screening/` core logic. Zero configuration activations. Active baseline remains `v1.5.0`.

---

## 20. Evidence Index

* **Authoritative Delivery Lineage**: Commit `690d4722294f18b4897676ede8392314f63f3128` (Phases 1–7 + CFO/PAT determinism repair).
* **Automated Acceptance Test Suite**: 575 passed, 0 failed across 25 test files (`python3 -m pytest tests/test_vishal_golden.py tests/test_post_listing_phase6a.py tests/test_cfo_pat_determinism.py`).
* **Golden Evaluation Fixture**: Result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` (100% bit-for-bit match).
* **Candidate Configuration**: `config/ipo-config.v1.6.0.json` (Status: `IMPLEMENTED_INACTIVE`, `is_active: false`).
* **Calibration Proposal**: `config/calibration-proposal.v1.6.0.json` (Proposal Hash: `87bc9bcfa0bd9561adf3eb0be53a4291c465b5b02cd8561209f323e94a2249af`).
* **Legacy UI Reference Prototype**: `handoff/reference/ipo-scorer_4.html` (Inspected and classified as PROTOTYPE / REFERENCE ONLY).
* **Data Contract Matrix**: `docs/UI_PRESENTATION_CAPABILITY_MATRIX.md` (Detailed audit of structures A through AI, SHA-256: `5b0717d5601cf6ac7bd8b8b5feb2142a6e744dabb30bc66b84ff1de78265c484`).
* **Consolidated Product Reconciliation**: `docs/PRODUCT_RECONCILIATION_AND_FUTURE_ROADMAP.md`.
* **Primary Deliverable SHA-256**: `96c18c4105ebb96a985ad8f7fdca79f8d6bf8e0819d96544f6eb9ec41b0a214b` (prior to hash insertion).
