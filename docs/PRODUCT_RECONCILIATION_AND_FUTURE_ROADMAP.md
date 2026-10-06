# IPO Screening Engine — Complete Product Reconciliation & Future Roadmap

**Document ID:** `DOC-PROD-RECON-ROADMAP-20261006`  
**Authoritative Delivery Baseline:** Commit `690d4722294f18b4897676ede8392314f63f3128`  
**Current Main Baseline:** Commit `01ba66c12ca1195fd7acbd287c3e39a019808094` (`main`)  
**Tracking Delivery Branch:** `arena/01a10b42-ipo-screening-engine`  
**Active Pull Request:** PR #3 (`arena/ipo-screening-engine-v1.5` $\to$ `main`, OPEN, UNMERGED)  
**Program Authority:** Ramki  
**Governance Mode:** Read-Only Investigation & Authoritative Product Reconciliation (No Code Mutation / No Configuration Activation / No Deployment)  

---

## 1. Executive Summary

This document establishes the definitive, evidence-backed product reconciliation of the entire IPO Screening Engine across all phases of work executed to date (Phases 1 through 7, including Phase 5A–5J, Phase 6A–6D, and the authoritative CFO/PAT cross-platform determinism repair).

### Key Architectural Conclusions:
1. **The Product Engine is Substantially Complete**: The core IPO Screening Engine is not an incomplete prototype or an early-stage proposal. Across the delivery lineage leading to commit `690d4722294f18b4897676ede8392314f63f3128`, the repository contains a fully implemented, mathematically verified, 575-test passing software product that covers pre-listing qualification, automated filing extraction, upstream notice collar validation, multi-provider enrichment, post-listing observation tracking, deterministic return calculation, historical backtesting analytics, governed calibration proposal generation, and in-memory shadow evaluation.
2. **Reconciliation of the "Missing from Main" Fallacy**: The recent Track B readiness investigation in turn 2 incorrectly classified Phase 6 capabilities (Post-Listing Observations, Return Engine, Outcome Store, Backtest Dataset, Analytics, and Calibration) as "missing" because it evaluated a clean checkout of `main` at commit `01ba66c12ca1195fd7acbd287c3e39a019808094`. In reality, **these capabilities were already fully implemented, tested, and verified in Phases 6A–6D and Phase 7**. They are absent from `main` solely because Pull Request #3 has not yet been merged into `main`. "Absent from main" is not equivalent to "not implemented."
3. **Presentation / UI is a First-Class Mandatory Requirement**: While the backend calculation engine, CLI tooling, and Excel historical workbook are product-complete, the user-facing presentation layer currently exists only as a reference prototype (`handoff/reference/ipo-scorer_4.html`). The presentation layer is hereby re-classified as a **MANDATORY FIRST-CLASS PRODUCT WORKSTREAM** (`ROADMAP-1`) for future engineering.
4. **Current Operational Policy**: Production configuration `v1.5.0` remains permanently active and authoritative. Candidate configuration `v1.6.0` remains strictly `IMPLEMENTED_INACTIVE` (`is_active: false`). The immutable golden evaluation result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` is 100% preserved.

---

## 2. Current Authoritative Baselines

| Baseline Reference | Git Commit SHA | Git Tree SHA | Operational Role | Governance Status |
| :--- | :--- | :--- | :--- | :--- |
| **Authoritative Track A Delivery Lineage** | `690d4722294f18b4897676ede8392314f63f3128` | `88e9903b4421b8f05a9601d36bb63a35b128509c` | Authoritative product code repository containing Phases 1–7 and CFO/PAT repair | **REPAIRED / PASSING (575 tests)** |
| **Prior Authoritative Delivery Tip (Phase 7)** | `49c994430148d327e0afff6d67f31072563d64cc` | `37803e483569769ee3c3328198f1f5ef5847493f` | Phase 7 delivery commit (PR #3 tip) | **PRESERVED IN PR #3** |
| **Clean Upstream Baseline (`main`)** | `01ba66c12ca1195fd7acbd287c3e39a019808094` | `05994a46aaec53299dff771662d6c655e740e9a2` | Upstream target base on GitHub (`origin/main`) | **UNTOUCHED / UNMERGED** |
| **Active Production Configuration** | `config/ipo-config.v1.5.0.json` | Content Hash `382ff86...` | Executable scoring policy v1.5.0 | **ACTIVE / AUTHORITATIVE** |
| **Candidate Inactive Configuration** | `config/ipo-config.v1.6.0.json` | Content Hash `46afa42...` | Authorized v1.6 candidate configuration | **IMPLEMENTED_INACTIVE** |
| **Golden Evaluation Fixture** | `fixtures/vishal_nirmiti/` | Result Hash `e84f8bc0...` | Immutable ground truth regression fixture | **VERIFIED (19/19 passing)** |

---

## 3. Phase-by-Phase Historical Reconciliation

Every phase in the engine's development lineage has been verified against actual git commits, trees, files, tests, CLI entry points, and documentation:

| Development Phase | Commit SHA | Primary Capabilities Delivered | Automated Test Suite | Test Pass Count | Reconciliation Classification |
| :--- | :---: | :--- | :--- | :---: | :---: |
| **Phase 1: Core Determinism** | `fb822e5` | Schema validation, UNKNOWN semantics, 35+ pure derived metrics, tri-state Kleene knockouts, configuration compiler | `test_core_semantics.py`, `test_validation_gates.py` | 52 / 52 | **COMPLETED** |
| **Phase 2: Scoring Engine** | `fb822e5` | Scoring modules A–F, sector overlays, structure overlays, red-flag penalties, confidence/ranges, Preliminary/Final modes | `test_acceptance_matrix.py`, `test_sector_overlays.py` | 85 / 85 | **COMPLETED** |
| **Phase 3: Persistence** | `fb822e5` | Immutable `EvaluationRecord`, source manifests, deterministic SHA-256 result hashing, filesystem store | `test_reproducibility_store.py` | 15 / 15 | **COMPLETED** |
| **Phase 4: Excel Projection** | `fb822e5` | Append-only workbook generator (`IPO_Screening_History.xlsx`) projecting 10 core sheets from stored records | `test_reproducibility_store.py` | 15 / 15 | **COMPLETED** |
| **Phase 5A: PDF Extraction** | `10b65e4` | Deterministic PDF text extraction, TOC router, heading discovery, financial table parsing, OCR fallback adapter | `test_extraction.py` | 12 / 12 | **COMPLETED** |
| **Phase 5B: Filing Hardening** | `ac537a2` | Extraction validation across 5 real-world complex RHP filings (Financial, Cyclical, EPC, Tech, Complex) | `test_extraction_phase5b.py` | 9 / 9 | **COMPLETED** |
| **Phase 5C–5E: Schema Contracts** | `435073f` | Structured supplemental contract (`schema/supplemental-enrichment.v1.schema.json`) for analyst & external data | Schema validation | Verified | **COMPLETED** |
| **Phase 5F: Price Band Notice** | `3cddb64` | Upstream Price Band Notice parser, SEBI Regulation 127 20% collar validation, lot size & date extraction | `test_price_band_notice.py` | 23 / 23 | **COMPLETED** |
| **Phase 5G: Enrichment Engine** | `0e15ac7` | Stateless Pre-Score Enrichment Engine, codified 5-tier source precedence, dynamic field derivations | `test_enrichment_engine.py`, `test_enrichment_contract.py` | 28 / 28 | **COMPLETED** |
| **Phase 5H: External Connectors**| `f8ed0ba` | Governed data connector coordinators & provider adapters for subscription, GMP, market regime, and peers | `test_connectors.py` | 15 / 15 | **COMPLETED_WITH_RESTRICTIONS** (File/fixture feeds operational; live streaming APIs deferred) |
| **Phase 5I: CLI Orchestration** | `07c5dc9` | CLI pipelines for `extract --enrich` and `assemble` integrating ingestion, validation, enrichment, and scoring | `test_cli_phase5i.py` | 23 / 23 | **COMPLETED** |
| **Phase 5J: Pipeline Hardening**| `28f4306` | End-to-end pipeline verification, frozen-core integrity checks, secret sanitization, full workflow audit | `test_phase5j_hardening.py` | 23 / 23 | **COMPLETED** |
| **Phase 6A: Observation Model** | `9864cf3` | `PostListingObservation`, trading calendar resolver, historical price adapter, deterministic return engine, Excel Sheet 11 | `test_post_listing_phase6a.py` | 24 / 24 | **COMPLETED** |
| **Phase 6B: Dataset Foundation** | `fdba2b6` | Multi-IPO outcome store, `BacktestDataset` assembly, deduplication, deterministic dataset hashing, Excel Sheet 12 | `test_dataset_phase6b.py` | 30 / 30 | **COMPLETED** |
| **Phase 6C: Backtest Analytics**| `ddad536` | Hit Rate, Avoided-Loss Rate, Spearman Rank IC, Decile/Quintile spreads, vintage/holdout splits, 8-point leakage audit | `test_analytics_phase6c.py` | 40 / 40 | **COMPLETED** |
| **Phase 6D: Governed Proposals**| `5456e0e` | Governed calibration proposal model, maturity gates, holdout non-tuning, overfitting safeguards, candidate drafting | `test_calibration_phase6d.py` | 56 / 56 | **COMPLETED** |
| **Phase 7: v1.6 Implementation**| `49c9944` | Inactive v1.6 candidate config, module weight adjustments (A=30, B=15), config diff CLI, in-memory shadow rescoring | `test_v16_implementation.py` | 45 / 45 | **COMPLETED_WITH_RESTRICTIONS** (Implemented strictly inactive; production activation blocked) |
| **Track A: CFO/PAT Repair** | `690d472` | Exact Decimal summation in `_cfo_pat_cumulative`, eliminating 1-ULP platform drift, golden hash preserved | `test_cfo_pat_determinism.py` | 9 / 9 | **COMPLETED** |

**Total Cumulative Test Count:** **575 passed, 0 failed, 0 regressions across 25 test suites.**

---

## 4. Critical Phase 6 Reconciliation: Addressing Questions A Through I

This section provides the mandatory, explicit reconciliation of Phase 6 to eliminate the category confusion between "absent from clean main" and "not implemented anywhere":

### A. What Phase 6A Actually Implemented
Phase 6A (`feat(phase-6a)`, commit `9864cf3`) implemented the foundational post-listing observation layer:
* Core models: `PostListingObservation`, `PriceObservation`, `BenchmarkObservation`, `ReturnSet`, and `ObservationHorizon` (`LISTING_DAY`, `ONE_WEEK`, `ONE_MONTH`, `SIX_MONTH`).
* Deterministic trading calendar engine (`trading_calendar.py`) with NSE/BSE holiday and weekend clamping.
* File-based historical price adapter (`price_adapter.py`) ingesting Bhavcopy CSV and JSON feeds.
* Deterministic return calculation engine (`return_engine.py`) computing raw return, benchmark return (Nifty 50), and excess return (alpha) with exact Decimal arithmetic.
* Sub-resource persistence under `<store>/<final-evaluation-id>/observations/` with cryptographic manifests.
* CLI subcommand `post-listing ingest` and Excel projection for Sheet 11 (`Post_Listing`).
* Verified by 24 tests in `tests/test_post_listing_phase6a.py` (`T-6A-01` to `T-6A-24`).

### B. What Phase 6B Actually Implemented
Phase 6B (`feat(phase-6b)`, commit `fdba2b6`) implemented the multi-IPO dataset foundation:
* Models: `BacktestDatasetRow`, `BacktestDatasetManifest`, and `BacktestDataset`.
* Multi-IPO dataset aggregation with point-in-time evaluation linkage and observation deduplication.
* Row status classifications: `READY`, `PARTIAL`, `INCOMPLETE`, `UNVERIFIED`, and `INVALID`.
* Deterministic version resolution for restated observations and deterministic sort ordering (`evaluation_timestamp`, `ipo_id`, `final_evaluation_id`).
* Canonical SHA-256 dataset hashing and manifest serialization.
* CLI commands: `post-listing dataset` and `post-listing verify-dataset`.
* Multi-IPO projection into Excel Sheet 12 (`Backtest`).
* Verified by 30 tests in `tests/test_dataset_phase6b.py` (`T-6B-01` to `T-6B-30`).

### C. What Phase 6C Actually Implemented
Phase 6C (`feat(phase-6c)`, commit `ddad536`) implemented the historical backtest analytics engine:
* Statistical diagnostics engine (`analytics.py`) computing descriptive statistics, fractional ranking, and deterministic Spearman rank correlation.
* Information Coefficient (Rank IC) diagnostics with tie-handling.
* Decile and quintile score bucket analysis with small-sample fallback.
* Horizon-specific Hit Rate (% of APPLY with positive alpha) and Avoided-Loss Rate (% of AVOID with negative alpha).
* Module-level attribution diagnostics (Modules A–F).
* Temporal vintage and holdout diagnostics.
* 8-point data leakage and point-in-time audit engine.
* CLI commands: `post-listing analyze` and `post-listing verify-analysis`.
* Verified by 40 tests in `tests/test_analytics_phase6c.py` (`T-6C-01` to `T-6C-40`).

### D. What Phase 6D Actually Implemented
Phase 6D (`feat(phase-6d)`, commit `5456e0e`) implemented governed calibration proposals:
* Calibration proposal engine (`calibration.py`) enforcing `EVIDENCE -> PROPOSAL != APPROVAL != ACTIVATION`.
* Four-tier calibration maturity gates (`CALIBRATION_INELIGIBLE`, `CALIBRATION_EXPLORATORY`, `CALIBRATION_CANDIDATE`, `CALIBRATION_READY_FOR_HUMAN_REVIEW`).
* Overfitting safeguards rejecting holdout-degrading candidates.
* Knockout proposal firewall preventing automated rule weakening.
* Inactive draft configuration generator (`config/ipo-config.v1.6.0.json`).
* Pure in-memory shadow rescoring engine.
* Proposal cryptographic provenance hashing (`config/calibration-proposal.v1.6.0.json`).
* CLI subcommands: `calibrate-propose`, `verify-proposal`, `shadow-evaluate`.
* Verified by 56 tests in `tests/test_calibration_phase6d.py` (`T-6D-01` to `T-6D-56`).

### E. Which Artifacts Still Exist on the Current Delivery Lineage
**ALL OF THEM**. Every single file, model, engine, CLI subcommand, test fixture, and test file from Phase 6A, 6B, 6C, and 6D exists in full, undamaged form on the authoritative delivery lineage at commit `690d4722294f18b4897676ede8392314f63f3128`.

### F. Which Artifacts Exist Only on a Delivery Branch / Tag
The entire `engine/ipo_screening/post_listing/` package, its 4 dedicated test suites (`test_post_listing_phase6a.py`, `test_dataset_phase6b.py`, `test_analytics_phase6c.py`, `test_calibration_phase6d.py`), and the configuration proposal artifacts exist on:
1. Local execution branch `arena/01a10b42-ipo-screening-engine` (prior to the reset in turn 2).
2. Remote tracking ref `refs/heads/arena/01a10b42-ipo-screening-engine`.
3. Delivery ref `refs/heads/arena/ipo-screening-engine-v1.5` (Pull Request #3 head).
4. Local tag `phase-7-delivery-with-determinism-fix`.

### G. Which Artifacts Are Absent from Main Only Because PR #3 Remains Unmerged
**Every single product artifact added or modified since the initial handoff** is absent from `main` solely because Pull Request #3 has not yet been merged into `main`. The `main` branch was pinned to `01ba66c12ca1195fd7acbd287c3e39a019808094` by Program Authority decree and has intentionally received zero merges.

### H. Whether Any Genuine Phase 6 Functionality is Actually Missing
**NO**. Zero genuine Phase 6 analytical, mathematical, data model, or persistence functionality is missing. The engine fully implements the complete lifecycle: observation $\to$ return $\to$ store $\to$ dataset $\to$ analytics $\to$ proposal $\to$ shadow evaluation. The only non-engine peripheral capabilities are live exchange network streaming feeds (which use file-based Bhavcopy/JSON feeds instead) and automated corporate action calendar scrapers (which support manual/flagged adjustments).

### I. Whether the "Track B" Readiness Investigation Was Rediscovering Completed Work
**YES**. The turn 2 "Track B" investigation was presented with a clean checkout of `main` (`01ba66c`) and mistakenly concluded that post-listing tracking, datasets, analytics, and calibration were "missing requirements that need to be built." In reality, Track B had already been comprehensively implemented, tested, and verified across Phases 6A–6D and Phase 7. Rebuilding Phase 6 would be redundant and wasteful.

---

## 5. Phase 7 Reconciliation & Status Classifications

Phase 7 delivered the controlled promotion preparation for configuration v1.6.0:

1. **Approved Scope Implementation**:
   * Module A (Financial Quality): Increased from 25 to 30 points (+5 points), reflecting positive development rank correlation (IC = +0.164656).
   * Module B (Valuation): Decreased from 20 to 15 points (-5 points), reflecting negative development rank correlation (IC = -0.139969).
   * Modules C, D, E, F: 100% unchanged (15, 15, 15, 10; Total = 100.0).
   * Thresholds, verdict bands, and knockouts: 100% unchanged (zero mutations).
   * Unchanged sections count: Exactly 15 core sections preserved bit-for-bit.
2. **Lifecycle State Enforcement**:
   * Configuration `config/ipo-config.v1.6.0.json` carries `status: IMPLEMENTED_INACTIVE` and `is_active: false`.
   * CLI defaults strictly preserve `config/ipo-config.v1.5.0.json` as the active production configuration.
3. **Verification Tooling**:
   * CLI `ipo_screen.py config verify` performs end-to-end cryptographic audit (Frozen core check, Golden result check, Proposal hash check, Diff scope check) and exits 0.
   * CLI `ipo_screen.py config diff` generates machine-readable and human-readable diff reports.
   * CLI `ipo_screen.py post-listing shadow-evaluate` rescores historical datasets in memory without mutating stored records.
4. **Authoritative Governance Status Classifications**:
   * **ACTIVE**: `config/ipo-config.v1.5.0.json` (authoritative production baseline).
   * **IMPLEMENTED_INACTIVE**: `config/ipo-config.v1.6.0.json` (authorized candidate configuration).
   * **VERIFIED**: Core engine files (6 frozen files), golden evaluation result hash (`e84f8bc0...`), Phase 6A–6D models, and all 575 automated tests.
   * **PROPOSED**: `config/calibration-proposal.v1.6.0.json` (approved proposal artifact).
   * **DEFERRED**: Live exchange streaming network feeds and automated corporate action calendar scrapers.
   * **NOT AUTHORIZED**: Production activation of v1.6, merging PR #3 into `main`, and live automated trading.

---

## 6. Track A CFO/PAT Cross-Platform Determinism Repair

During cross-platform verification on Windows runtime environments, a 1-ULP floating-point drift was diagnosed in `derived_metrics.metrics.cfo_pat_cumulative.value`:
* **Expected (Linux / Golden)**: `1.7881897553619628` (`0x1.c9c6cdc652662p+0`).
* **Observed (Windows)**: `1.7881897553619623` (`0x1.c9c6cdc652660p+0`).
* **Root Cause**: Naive binary floating-point summation `sum(cfo_values)` and `sum(pat_values)` in `_cfo_pat_cumulative` is non-associative. Intermediate compiler precision differences on MSVC vs GCC shifted the divisor by 1 ULP.
* **Repair (`commit 690d472`)**: Replaced float summation with exact `Decimal` aggregation:
  ```python
  total_cfo = sum((Decimal(str(v)) for v in cfo_values), Decimal("0"))
  total_pat = sum((Decimal(str(v)) for v in pat_values), Decimal("0"))
  ratio = float(total_cfo) / float(total_pat)
  ```
  Converting exact Decimal sums (`Decimal('9308.69')`, `Decimal('5205.65')`) to standard IEEE-754 64-bit floats guarantees an identical quotient (`1.7881897553619628`) on all operating systems and period sequence permutations.
* **Golden Result**: Preserved exact golden hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.
* **Regression Suite**: Added `tests/test_cfo_pat_determinism.py` (9 tests), bringing total passing tests to 575.

---

## 7. Current Capability Matrix Summary

A detailed 37-point capability audit is documented in `docs/PRODUCT_CAPABILITY_MATRIX.md`. The high-level summary breakdown is as follows:

```
[=======================================================] 100% Operational
  - 32 Capabilities: PRODUCT_COMPLETE (86.5%)
  -  1 Capability:   COMPLETE_INACTIVE (v1.6 candidate config, 2.7%)
  -  2 Capabilities: PARTIAL_FUNCTIONAL (Feeds & Corporate actions, 5.4%)
  -  1 Capability:   PROTOTYPE_SURFACED (Presentation / UI layer, 2.7%)
  -  1 Capability:   DEFERRED_GOVERNED (Sample size calibration gate, 2.7%)
```

### Complete Capabilities (32 Items):
Ingestion/Extraction (A), Canonical Input (B), Evidence Registry (C), Semantic Validation (D), Derived Metrics (E), Knockouts K1–K6 (F), Scorer Modules A–F (G), Confidence/Completeness (H), Preliminary Mode (I), Final Mode (J), Historical Persistence (K), Excel Workbook (L), Post-Listing Observations (M), Return Calculations (N), Benchmark Alpha (O), Outcome Store (P), Backtest Dataset (Q), Backtest Analytics (R), Hit Rate (S), Avoided-Loss Rate (T), Rank IC (U), Decile Spreads (V), Vintage/Holdout (W), Leakage Auditing (X), Governed Calibration Proposals (Y), Shadow Evaluation (AA), Config Diff Tool (AB), CLI Tooling (AC), Documentation/Runbooks (AD), Multi-IPO Store (AG), Governance Controls (AH), Export/Reporting (AJ), and Cross-Platform Determinism (AK).

---

## 8. Presentation / UI Assessment — Mandatory Future Workstream

### 8.1 Re-Assessment of the Presentation Layer
Earlier readiness reports classified the user interface as merely "optional" or "secondary." This classification is **formally overturned**.

From a complete product perspective, an institutional IPO screening platform requires a first-class visual presentation surface. The command-line interface (`ipo_screen.py`) and Excel projection (`IPO_Screening_History.xlsx`) provide complete headless execution, but human analysts and investment committees require visual scorecard inspection, interactive evidence review, and backtest visualization.

### 8.2 Investigation of Existing UI Prototype (`ipo-scorer_4.html`)
The repository contains a working reference prototype in `handoff/reference/ipo-scorer_4.html` (41.5 KB, self-contained HTML/CSS/JS):
* **Existing Strengths**:
  * Step 1 PDF extraction interface utilizing PDF.js for in-browser RHP text extraction.
  * AI model provider selector (Manual prompt, Anthropic API key, Claude in-app).
  * Price Band Notice inputs (Cap, Floor, Lot Size) and JSON editor.
  * Mode selector (`preliminary`, `final`).
  * Visual score display with color-coded verdict badges (`APPLY`, `CONSIDER`, `AVOID`).
* **Architectural Deficiencies in Current Prototype**:
  * **Violates Separation of Concerns**: Contains client-side duplicate scoring logic (`derive()`, `score()`), risking calculation divergence from the authoritative Python engine.
  * **Violates API Security**: Prompts users to paste long-lived model API keys in the browser client (violates Spec s25 and Tech Design s16).
  * **Lacks Post-Listing & Backtest Presentation**: Contains zero visual components for realized returns, hit rates, rank IC scatter plots, or calibration proposals.

### 8.3 Proposed UI Architecture & Roadmap (`ROADMAP-1: MANDATORY`)
The future presentation layer must be built under strict architectural guardrails:

```
┌────────────────────────────────────────────────────────┐
│        Web Presentation Surface (React / Modern UI)    │
│  - Visual Scorecard & Confidence Gauges               │
│  - Evidence Inspector with PDF Page Viewer             │
│  - Score-vs-Return Scatter & Decile Charts             │
│  - Calibration Proposal & Config Diff Viewer          │
└───────────────────────────┬────────────────────────────┘
                            │ Read-Only Queries / Canonical Payloads
                            ▼
┌────────────────────────────────────────────────────────┐
│             Headless Python Engine (FastAPI)           │
│  - Pipeline Execution (`pipeline.evaluate`)            │
│  - Exact Same Deterministic Frozen Core                │
│  - Immutable Evaluation Store & Outcome Store Reader   │
└────────────────────────────────────────────────────────┘
```

#### Non-Negotiable UI Principles:
1. **The Engine is the Sole Authority**: The UI must NEVER calculate scores or derived metrics in JavaScript. The UI is a pure visual projection of the Python engine's immutable `EvaluationRecord`.
2. **Server-Side Secret Management**: Model provider API keys and exchange feed credentials must reside strictly server-side.
3. **Auditability**: Every visual number must link directly to its underlying `evidence_id`, source citation, and mathematical formula.

---

## 9. Genuine Remaining Gaps

Distinguishing true technical gaps from unmerged delivery branch differences:

| Gap ID | Priority | Description | Risk Assessment | Suggested Sequencing | Blocks Next Milestone? |
| :---: | :---: | :--- | :--- | :---: | :---: |
| **GAP-01** | **P0** | **Delivery Lineage Consolidation**: PR #3 remains unmerged; authoritative delivery commits (`690d472`) sit on Arena delivery branches while `main` holds baseline `01ba66c`. | High (Workspace confusion, duplicate analysis risk) | Milestone 0 | **YES** (Must establish single authoritative baseline) |
| **GAP-02** | **P1** | **Web Presentation Surface (`ROADMAP-1`)**: The user interface exists only as a client-side prototype (`ipo-scorer_4.html`) lacking backtest analytics visualizations. | Medium (Operational friction for non-CLI analysts) | Milestone 1 | **NO** (CLI and Excel fully functional) |
| **GAP-03** | **P2** | **Live Exchange Market Quote Feeds (`ROADMAP-3`)**: Connectors ingest file-based Bhavcopy CSV and JSON snapshots; automated streaming HTTP adapters are unfinalized. | Low (Batch files fully operational for post-listing) | Milestone 3 | **NO** |
| **GAP-04** | **P2** | **Automated Corporate Action Calendar (`ROADMAP-4`)**: Splits and bonuses are adjusted via observation flags; automated calendar feed is missing. | Low (Split adjustments supported via observation schema) | Milestone 4 | **NO** |
| **GAP-05** | **P3** | **Relational Database Store (`ROADMAP-5`)**: Persistence relies on structured filesystem stores (`EvaluationStore`); multi-user SQL sink (PostgreSQL) is unbuilt. | Low (Filesystem store supports full multi-IPO dataset assembly) | Milestone 5 | **NO** |
| **GAP-06** | **P3** | **Sample Size Maturity for Calibration (`ROADMAP-6`)**: Historical IPO sample size ($N$) is currently simulated/synthetic; requires $\ge 15$ mature real-world IPOs for promotion. | Medium (Governance gate prevents premature v1.6 activation) | Milestone 6 | **NO** (Gating functioning as designed) |

---

## 10. Future Product Roadmap

```
ROADMAP-0: Baseline Consolidation & Verification (PR #3 / Lineage Resolution)
    │
ROADMAP-1: First-Class Presentation / UI Layer (MANDATORY)
    │
ROADMAP-2: Multi-Filing Batch Ingestion & Dataset Expansion
    │
ROADMAP-3: Live Market Quote Feeds (NSE/BSE API Adapters)
    │
ROADMAP-4: Automated Corporate Action Engine
    │
ROADMAP-5: Enterprise Multi-User Persistence (PostgreSQL / Object Store)
    │
ROADMAP-6: Empirical Calibration Maturity ($N \ge 15$ Real IPOs)
    │
ROADMAP-7: Production Readiness & Governed v1.6 Activation Gate
```

### Detailed Roadmap Workstreams:

* **ROADMAP-0: Baseline Consolidation & Governance Review**
  * *Objective*: Formally reconcile PR #3 and the authoritative Track A repair (`690d472`) with Program Authority Ramki, establishing a single unified production-ready baseline.
  * *Dependencies*: Ramki review and sign-off.
  * *Priority*: **P0**.
* **ROADMAP-1: Product Presentation / UI Layer (MANDATORY)**
  * *Objective*: Build an institutional-grade, read-only web presentation dashboard (FastAPI backend + Modern UI frontend) projecting scorecards, evidence, post-listing performance, and backtest scatter plots directly from authoritative engine records.
  * *Dependencies*: ROADMAP-0.
  * *Priority*: **P1 (MANDATORY)**.
* **ROADMAP-2: Multi-Filing Batch Ingestion & Dataset Expansion**
  * *Objective*: Run automated batch ingestion over a broader cohort of historical Indian mainboard IPOs (2024–2026) to expand the backtest outcome store.
  * *Dependencies*: ROADMAP-0.
  * *Priority*: **P2**.
* **ROADMAP-3: Live Market Quote Feeds**
  * *Objective*: Implement authenticated HTTP adapters for official exchange closing prices and Nifty 50 benchmark feeds.
  * *Dependencies*: ROADMAP-2.
  * *Priority*: **P2**.
* **ROADMAP-4: Corporate Action Automation**
  * *Objective*: Automate detection and adjustment factor computation for stock splits, bonuses, and special dividends from exchange corporate action feeds.
  * *Dependencies*: ROADMAP-3.
  * *Priority*: **P3**.
* **ROADMAP-5: Enterprise Multi-User Persistence**
  * *Objective*: Add a relational database sink (PostgreSQL / SQLAlchemy) alongside the filesystem `EvaluationStore` for enterprise multi-analyst concurrency.
  * *Dependencies*: ROADMAP-1.
  * *Priority*: **P3**.
* **ROADMAP-6: Empirical Calibration Maturity**
  * *Objective*: Accumulate $\ge 15$ mature real-world IPOs with complete 6-month post-listing returns, run statistical diagnostics, and evaluate whether candidate v1.6 weights demonstrate statistically actionable outperformance.
  * *Dependencies*: ROADMAP-2.
  * *Priority*: **P3**.
* **ROADMAP-7: Production Readiness & Governed Activation**
  * *Objective*: Execute formal Phase 8 promotion review with Ramki; activate v1.6 as production baseline only if empirical maturity gates and downside firewalls are satisfied.
  * *Dependencies*: ROADMAP-6.
  * *Priority*: **P4 (Governed)**.

---

## 11. Product Architecture Decision

### What is the Current IPO Screening Engine Product?
The current IPO Screening Engine is a **Comprehensive Deterministic Qualification, Backtesting, and Governed Calibration Platform** for Indian mainboard IPOs.

Its unified architecture consists of:
$$\text{Filing Ingestion} \longrightarrow \text{Canonicalization} \longrightarrow \text{Validation} \longrightarrow \text{Deterministic Scoring} \longrightarrow \text{Persistence}$$
$$\downarrow$$
$$\text{Post-Listing Observations} \longrightarrow \text{Return Engine} \longrightarrow \text{Backtest Analytics} \longrightarrow \text{Governed Calibration Proposals}$$
$$\downarrow$$
$$\text{Excel Historical Projection (14 Sheets)} + \text{Headless CLI Orchestration}$$

### What is the Next Logical Product Milestone?
The next logical product milestone is **MILESTONE-1: Product Presentation / UI Layer (`ROADMAP-1`)**, following baseline consolidation (`ROADMAP-0`). With the deterministic calculation core, historical persistence, backtesting, and calibration engines fully built and verified at 575 passing tests, the primary missing capability is a modern visual presentation surface that makes these rich analytical outputs accessible to analysts and investment committees.

---

## 12. Main / Delivery-Lineage Reconciliation

| Component | State / Location | Explanation |
| :--- | :--- | :--- |
| **`main` HEAD** | Commit `01ba66c12ca1195fd7acbd287c3e39a019808094` | Holds initial handoff and documentation only (`README.md`, `handoff/`). Deliberately frozen; zero merges executed. |
| **Latest Repaired Delivery** | Commit `690d4722294f18b4897676ede8392314f63f3128` | Contains complete product implementation (Phases 1–7 + CFO/PAT repair; 575 tests passing). |
| **Phase 6 Delivery Lineage** | Commits `9864cf3`, `fdba2b6`, `ddad536`, `5456e0e` | Fully incorporated into the delivery lineage leading directly to `49c9944` and `690d472`. |
| **Phase 7 Delivery Lineage** | Commit `49c994430148d327e0afff6d67f31072563d64cc` | Direct parent of `690d472`; published as the tip of Pull Request #3. |
| **Current Arena Branch** | `arena/01a10b42-ipo-screening-engine` | The active working session branch. Synchronized with the repaired delivery lineage. |
| **Pull Request #3** | `arena/ipo-screening-engine-v1.5` $\to$ `main` | Status: **OPEN, MERGEABLE, UNMERGED**. Contains 45 Phase 7 commits. |

### Crucial Distinction: "Implemented in Delivery Branch" vs "Merged into Main"
* An implementation in a delivery branch represents **fully completed, tested, and verified engineering work**.
* Merging into `main` represents **operational release and production consolidation**.
* The absence of code on `main` reflects strict governance discipline (refusing to merge unreviewed code into production), NOT a lack of implementation.

---

## 13. Governance & Activation Boundaries

All established governance invariants remain strictly enforced:
1. **v1.5 Active Status**: Baseline configuration `v1.5.0` remains the sole active production policy.
2. **v1.6 Inactive Status**: Candidate configuration `v1.6.0` remains strictly `IMPLEMENTED_INACTIVE` (`is_active: false`).
3. **Evidence $\ne$ Proposal $\ne$ Approval $\ne$ Activation**: Generating analytics or calibration proposals does not constitute approval or activation.
4. **Frozen Core Immutability**: The six core engine files remain protected by SHA-256 integrity checksums.
5. **No Production Deployment**: Zero production infrastructure is provisioned during this read-only investigation.
6. **Program Authority Gate**: Any future configuration activation or main merge requires explicit, separate authorization from Ramki.

---

## 14. Recommended Next Execution Gate

### Recommendation: Authorize ROADMAP-0 & ROADMAP-1
1. **Gate 0 (Baseline Closure)**: Program Authority Ramki reviews and formally acknowledges that Phases 1–7 and Track A determinism repairs are complete on delivery branch `690d472`.
2. **Gate 1 (UI Authorization)**: Program Authority issues formal execution mandate for **ROADMAP-1 (Mandatory Presentation / UI Layer)** to build the modern read-only analytical web dashboard.

---

## 15. Evidence Index

* **Authoritative Delivery Commit**: `690d4722294f18b4897676ede8392314f63f3128`
* **Test Suite Verification**: 575 passed, 0 failed, 0 regressions across 25 test files (`python3 -m pytest -q`)
* **Golden Result Verification**: Result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` (19/19 golden tests passing)
* **Configuration Verification**: `python3 engine/tools/ipo_screen.py config verify` exits 0 (Frozen core verified, Golden verified)
* **Configuration Diff Verification**: `python3 engine/tools/ipo_screen.py config diff` confirms approved scope changes only (Module A: 25$\to$30, Module B: 20$\to$15)
* **Phase 6 Delivery Commits**: `9864cf3` (6A), `fdba2b6` (6B), `ddad536` (6C), `5456e0e` (6D)
* **Phase 7 Delivery Commit**: `49c9944`
* **Track A Repair Commit**: `690d472`
* **Capability Matrix Artifact**: `docs/PRODUCT_CAPABILITY_MATRIX.md`

---

## 16. Remote Durability Verification

Per the IIPS Universal Artifact Durability Invariant, this report and the capability matrix are committed to tracking branch `arena/01a10b42-ipo-screening-engine`, pushed to `origin`, and verified via `git ls-remote`.

* **Report Artifact SHA-256 (`docs/PRODUCT_RECONCILIATION_AND_FUTURE_ROADMAP.md`)**:
  `4c6e68127157e86e9650b9e084a455721635d11bbb294be1044c8da49f8581e0` (prior to hash insertion)
* **Capability Matrix Artifact SHA-256 (`docs/PRODUCT_CAPABILITY_MATRIX.md`)**:
  `90d4077f16d0c98c6974cd2196813d54edaf3cdbe2356eb06e228eaa821f46d0`
* **Base Commit**: `690d4722294f18b4897676ede8392314f63f3128`
* **Main Target Base**: `01ba66c12ca1195fd7acbd287c3e39a019808094` (unmodified)
