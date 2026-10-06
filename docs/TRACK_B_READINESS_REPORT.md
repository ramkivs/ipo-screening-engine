# IPO Screening Engine — Track B Readiness & Architecture Reconciliation Report

**Document ID:** `DOC-TRACK-B-READINESS-20261006`  
**Target Repository:** `ramkivs/ipo-screening-engine`  
**Authoritative Baseline:** `main @ 01ba66c12ca1195fd7acbd287c3e39a019808094`  
**Program Authority:** Ramki  
**Scope:** Track B Only — Non-Production Investigation & Readiness Reconciliation  
**Status:** `READY_WITH_DECLARED_GAPS`  
**Implementation Authority:** Strictly Blocked Pending Ramki Review & Authorization (No Implementation Pass)  

---

## 1. Executive Summary & Fresh Baseline Verification

Per Program Authority instructions, this pass executes a clean-slate investigation and architecture reconciliation for **Track B** on a verified fresh baseline:

* **Authoritative Implementation Baseline:** `main` at commit `01ba66c12ca1195fd7acbd287c3e39a019808094` (clean tree, untouched).
* **Starting Commit Verification:** Verified SHA `01ba66c12ca1195fd7acbd287c3e39a019808094`.
* **Zero Carry-Over:** Confirmed working directory is reset to authoritative `main`; no untracked files or Phase-7 delivery branch artifacts exist in the baseline working tree.
* **Fail-Closed Rule:** All investigations strictly separate normative requirements from reference-only prototype materials.
* **No Implementation Mandate:** Zero product source code, configurations, or production test suites are mutated. This report establishes formal readiness, ambiguity resolution, dependency classifications, and architectural boundaries before any code changes are authorized.

---

## 2. Track B Discovery & Recovery

### 2.1 Track B Semantic Definitions & Discovery Across Handoff Artifacts

A comprehensive audit of the authoritative handoff artifacts (`IPO_Screening_Engine_Specification_v1.5.md`, `IPO_Screening_Engine_Technical_Design_v1.5.md`, `ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md`, and `ARENA_IPO_Screening_Artifact_Manifest_v1.5.md`) along with reference prototype artifacts (`Claude_IPO Screening Engine v 1.3 — Specification.md`, `ipo-scorer_4.html`, and prior Arena workspace states) establishes that **Track B** embodies **Post-Listing Outcome Tracking, Back-Testing, Statistical Analytics, and Governed Model Calibration**.

Across the project architecture, two parallel workstreams exist:
1. **Track A (Pre-Listing Deterministic Screening & Qualification Core)**:
   * **Scope**: Phases 1–4 (and Phase 5 ingestion hardening). Evaluates RHP/DRHP filings at `PRELIMINARY` (anchor/price-band) and `FINAL` (issue close) stages.
   * **Core Deliverable**: Deterministic 0–100 scores, tri-state knockouts (K1–K6), sector/structure overlays, red-flag penalties, confidence/score ranges, immutable evaluation records, and Excel historical workbook sheets 1–10, 13, and 14.
2. **Track B (Post-Listing Lifecycle, Back-Testing & Governed Calibration)**:
   * **Scope**: Phase 6 of Build Sequence (Spec s28, Tech Design s18), Minimum Historical Lifecycle (Spec s21), Excel Sheets 11 (`Post_Listing`) & 12 (`Backtest`) (Spec s22, Tech Design s12), and Success Metrics (Reference Spec s13).
   * **Core Deliverable**: Post-listing observation capture (`POST_LISTING_1W`, `POST_LISTING_1M`, `POST_LISTING_6M`), deterministic realized return and benchmark alpha calculation, backtest dataset aggregation, predictive statistical diagnostics (Hit Rate, Avoided-Loss Rate, Spearman Rank Correlation / Information Coefficient), and governed configuration calibration proposals.

#### Surfacing Related Secondary Workstreams
In addition to the primary definition of Track B as Post-Listing Backtesting/Calibration, two secondary capabilities exist in the handoff artifacts that must be explicitly demarcated:
* **Automated Extraction & Ingestion Pipeline (Phase 5)**: Automated TOC extraction, financial table parsing, OCR adapters, and market bidding/GMP connectors. (Demarcated as an upstream feeder to Track A/B canonical inputs).
* **Interactive UI / Web Dashboard**: Client-side interactive scorer (`ipo-scorer_4.html`) and backtest visualization dashboard. (Demarcated as a presentation layer projection).

---

### 2.2 Formal Track B Specification

| Dimension | Track B Specification & Governing Requirement | Normative Source |
| :--- | :--- | :--- |
| **Objective** | Systematically capture realized market outcomes of screened IPOs post-listing, compute absolute and benchmark-relative returns, evaluate predictive validity of screening scores, and formulate governed calibration proposals without mutating immutable pre-listing evaluations. | Spec s2, s21, s28 Phase 6; Tech Design s11, s12 |
| **Required Capabilities** | 1. Ingestion of post-listing market observations ($T+0$ listing, $T+7$ 1-week, $T+30$ 1-month, $T+180$ 6-month).<br>2. Deterministic price return, benchmark return (Nifty 50), and alpha calculations.<br>3. Statistical backtesting diagnostics: Hit Rate, Avoided-Loss Rate, IC/rank correlation, decile return spreads.<br>4. Governed calibration proposal formulation with maturity gates and downside safeguards.<br>5. Append-only Excel workbook projection for Sheets 11 (`Post_Listing`) and 12 (`Backtest`). | Spec s21, s22; Tech Design s12; Ref Spec s12, s13 |
| **In-Scope Components** | • `PostListingObservation` data model and schema.<br>• Deterministic Return Engine (raw return, benchmark return, corporate action adjustments).<br>• Outcome Store & Backtest Dataset Assembly Engine.<br>• Statistical Analytics Engine (Hit Rate, Avoided Loss, Information Coefficient).<br>• Calibration Proposal Engine (diff calculation, shadow evaluation, candidate config generation).<br>• Excel Projection Engine for `Post_Listing` and `Backtest` sheets. | Spec s21, s22; Tech Design s11, s12 |
| **Out-of-Scope Components** | • Autonomous live order routing, trading, or execution systems.<br>• Automatic unapproved production configuration mutation.<br>• Re-scoring or mutating immutable historical `FINAL` evaluation records.<br>• SME IPOs, REITs, InvITs, Rights Issues (normatively excluded under Spec s2). | Spec s2, s3, s21, s23 |
| **Inputs** | 1. Authoritative immutable pre-listing `final` evaluation records (`evaluation_id`, `ipo_id`, `issue_price`, `score`, `verdict`, `timestamp`).<br>2. Realized market price quotes (listing day open/close, 1W close, 1M close, 6M close).<br>3. Benchmark price series (Nifty 50 closes on corresponding trading dates).<br>4. Corporate actions (splits, bonuses, dividends) during observation window. | Spec s4, s21; Tech Design s3.1, s11 |
| **Outputs** | 1. Cryptographically signed, immutable `PostListingObservation` records.<br>2. Governed `BacktestDataset` manifests and serialized datasets.<br>3. Statistical `BacktestReport` (Hit rate, avoided-loss rate, IC, decile analysis).<br>4. Governed `CalibrationProposal` artifacts (`status: DRAFT` / `IMPLEMENTED_INACTIVE`).<br>5. Updated historical Excel workbook (`Post_Listing` and `Backtest` sheets). | Spec s21, s22, s23; Tech Design s11, s12 |
| **Persistence Requirements** | • Isolated observation persistence: `<store>/<final-evaluation-id>/observations/observation_<horizon>.json`.<br>• Zero in-place mutation of existing parent evaluation artifacts (`evaluation.json`, `result.json`).<br>• Deterministic observation hashing: SHA-256 over normalized observation payload. | Spec s3.1, s21, s23; Tech Design s11, s13 |
| **Configuration Requirements** | • Specification of observation horizons (`1w`: 7d, `1m`: 30d, `6m`: 180d).<br>• Benchmark specification (`NIFTY_50`).<br>• Minimum statistical maturity gates ($\ge 15$ mature IPOs with 6M observations for calibration).<br>• Versioning metadata for proposed configurations (`config_version: 1.6.0`, `is_active: false`). | Spec s3.5, s20; Tech Design s8 |
| **UI / API Requirements** | • CLI Command Suite: `post-listing observe`, `post-listing dataset`, `post-listing analyze`, `post-listing calibrate-propose`, `post-listing shadow-evaluate`, `config verify`, `config diff`.<br>• Read-only analytical API/dashboard projection showing score-vs-return scatter, hit rate metrics, and candidate diffs. | Tech Design s12, s16 |
| **Deterministic Requirements** | • Same inputs + same post-listing quotes + same benchmark = identical returns, alpha, and hash.<br>• Pure functions with zero floating-point non-associativity drift (exact Decimal arithmetic for currency and percentage ratios). | Spec s3.1; Tech Design s2, s5 |
| **Excel Requirements** | • Sheet 11 (`Post_Listing`): Append-only rows recording IPO ID, Evaluation ID, Issue Price, Listing Date, Listing Price, Listing Gain %, 1W/1M/6M Prices and Returns %.<br>• Sheet 12 (`Backtest`): Append-only rows recording Evaluation ID, Company, Final Score, Verdict, Confidence, Listing Gain %, 6M Return %, 6M Benchmark Alpha %, Hit/Miss Status. | Spec s22; Tech Design s12 |
| **Historical Data Requirements** | • Minimum sample size governance before calibration proposals can be generated.<br>• Partitioning into development vintages and holdout test sets to prevent overfitting. | Ref Spec s13; Spec s28 |
| **Testing Requirements** | • Observation capture & validation tests.<br>• Corporate action & dividend adjustment return tests.<br>• Dataset assembly, linkage, and deduplication tests.<br>• Statistical diagnostic tests (Hit Rate, Avoided Loss, Spearman Rank IC).<br>• Calibration candidate proposal generation & diff verification tests.<br>• Invariant regression tests: Track A golden hash `e84f8bc0...` permanently untouched. | Spec s26; Tech Design s17 |
| **Evidence Requirements** | • Verifiable exchange bulletin/terminal trade record for listing price and horizon closes.<br>• Provenance record for corporate action adjustments. | Spec s3.4, s24; Tech Design s3.3 |
| **Dependencies** | • Track A `FINAL` evaluations (prerequisite baseline).<br>• Clean historical market data source for stock and benchmark index closes.<br>• Ramki program authorization for calibration thresholds and target metrics. | Spec s21, s28 |
| **Blocking Gaps** | • Absence of authoritative corporate action adjustment feed specification.<br>• Formal policy decision on statistical significance threshold for weight calibration.<br>• Excel Sheet 11/12 integration into core workbook generator. | Identified in Section 6 |
| **Acceptance Criteria** | 1. 100% test coverage across observation, return calculation, dataset assembly, statistical diagnostics, and calibration proposal generation.<br>2. Zero mutation of Track A core scoring files (`derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`).<br>3. Track A golden evaluation hash remains bit-for-bit identical (`e84f8bc0...`).<br>4. Proposed configuration remains inactive until explicit production activation authorization. | Spec s27; Execution Prompt s23 |

---

### 2.3 Surfaced Ambiguities Between Normative Specifications & Reference Artifacts

In compliance with prompt instructions, the following structural ambiguities are explicitly surfaced for Program Authority resolution:

1. **Ambiguity A1 — Scope Boundary of "Track B" (Backtest Engine vs UI Scorer vs Ingestion Pipeline)**:
   * *Normative Spec*: Spec s28 lists Phase 5 as "Extraction" and Phase 6 as "Back-testing (post-listing tracking and calibration)".
   * *Reference Artifacts*: Prototype `ipo-scorer_4.html` implements browser-based extraction and interactive scoring; prior workspace state developed Phase 6A–6D as post-listing backtesting.
   * *Ambiguity*: Is Track B exclusively Phase 6 (Post-listing tracking, backtesting, and calibration), or does it encompass the web UI (`ipo-scorer_4.html`) and Phase 5 ingestion connectors?
   * *Recommended Resolution*: Treat Track B normatively as **Post-Listing Tracking, Back-Testing, and Governed Calibration** (Phases 6A–6D / Phase 7), while classifying the Web UI and External Connectors as secondary supporting workstreams.

2. **Ambiguity A2 — Observation Storage Topography**:
   * *Spec s21 / Tech Design s11*: Mandates immutable evaluation records and minimum lifecycle (`PRELIMINARY` $\to$ `FINAL` $\to$ `POST_LISTING_1W` $\to$ `POST_LISTING_1M` $\to$ `POST_LISTING_6M`), but does not specify whether post-listing observations are stored inside `<store>/<eval_id>/observations/` or in a flat global outcome directory.
   * *Prior Workspace State*: Implemented nested pattern `<store>/<final-evaluation-id>/observations/observation_<horizon>.json`, leaving parent evaluation artifacts completely untouched.
   * *Recommended Resolution*: Affirm the nested sub-resource storage pattern to guarantee 100% immutability of parent evaluation manifests.

3. **Ambiguity A3 — Benchmark Index & Total Return Index (TRI) Specification**:
   * *Spec s2 / Ref Spec s13*: Cites "Nifty trend" and "return vs Nifty".
   * *Ambiguity*: Should the benchmark return use Nifty 50 Price Return (PR) or Total Return Index (TRI, which includes dividends)?
   * *Recommended Resolution*: Default to standard Nifty 50 Price Return for core comparisons, with an optional flag for Nifty 50 TRI where total return dividend feeds are available.

4. **Ambiguity A4 — Governed Calibration Authority Threshold**:
   * *Spec s28 Phase 6*: Mandates "Implement post-listing tracking and calibration."
   * *Ambiguity*: What sample size and statistical threshold must be achieved before a calibration proposal can be formally recommended for promotion?
   * *Recommended Resolution*: Require minimum $N \ge 15$ fully mature IPOs across $\ge 2$ market cycles, with mandatory holdout set validation and downside regression checks before promotion.

---

## 3. Track B Spec-to-Code Traceability Matrix

Every Track B requirement is mapped from normative source to implementation, tests, and acceptance criteria:

| Requirement ID | Requirement Description | Normative Source | Reference Implementation (Prior Workspace State) | Existing / Proposed Test | Classification | Proposed Action | Dependency | Acceptance Criterion |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **TB-REQ-01** | Post-Listing Observation Model | Spec s21; Tech Design s11 | `post_listing/observation.py` (`PostListingObservation`) | `test_post_listing_phase6a.py` (T-6A-01 to T-6A-15) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Port additive `post_listing/` module to target baseline | Track A Final Eval | Immutable observation record with cryptographic SHA-256 hash |
| **TB-REQ-02** | Deterministic Return Engine | Spec s2; Ref Spec s13 | `post_listing/return_engine.py` (`compute_realized_returns`) | `test_post_listing_phase6a.py` (T-6A-16 to T-6A-30) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Port return engine with corporate action adjustments | TB-REQ-01 | Exact Decimal return calculation matching golden benchmarks |
| **TB-REQ-03** | Multi-Horizon Lifecycle ($T+0$, 1W, 1M, 6M) | Spec s21; Tech Design s12 | `post_listing/observation.py` (`ObservationHorizon`) | `test_post_listing_phase6a.py` (T-6A-31 to T-6A-45) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Enforce standardized horizon boundaries | TB-REQ-01 | Observations support 1W, 1M, 6M without data leakage |
| **TB-REQ-04** | Historical Outcome Store | Spec s21, s23; Tech Design s11 | `post_listing/dataset.py` (`OutcomeStore`) | `test_dataset_phase6b.py` (T-6B-01 to T-6B-20) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Implement isolated sub-store under evaluation directory | TB-REQ-01 | Parent `evaluation.json` and `result.json` remain bit-for-bit untouched |
| **TB-REQ-05** | Backtest Dataset Assembly Engine | Spec s28 Phase 6 | `post_listing/dataset.py` (`build_backtest_dataset`) | `test_dataset_phase6b.py` (T-6B-21 to T-6B-40) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Port deterministic dataset builder and manifest hashing | TB-REQ-04 | Deterministic dataset hash across permutations |
| **TB-REQ-06** | Predictive Analytics: Hit Rate | Ref Spec s13 | `post_listing/analytics.py` (`compute_hit_rate`) | `test_analytics_phase6c.py` (T-6C-01 to T-6C-10) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Calculate % of APPLY IPOs with positive 6M alpha | TB-REQ-05 | Exact mathematical formula matching reference definition |
| **TB-REQ-07** | Predictive Analytics: Avoided-Loss Rate | Ref Spec s13 | `post_listing/analytics.py` (`compute_avoided_loss_rate`) | `test_analytics_phase6c.py` (T-6C-11 to T-6C-20) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Calculate % of AVOID IPOs with negative 6M alpha | TB-REQ-05 | Exact mathematical formula matching reference definition |
| **TB-REQ-08** | Predictive Analytics: Rank Correlation / IC | Ref Spec s13 | `post_listing/analytics.py` (`compute_rank_ic`) | `test_analytics_phase6c.py` (T-6C-21 to T-6C-30) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Implement Spearman rank correlation between score and return | TB-REQ-05 | Deterministic rank handling with average tied ranks |
| **TB-REQ-09** | Decile & Bucket Performance Spread | Ref Spec s13 | `post_listing/analytics.py` (`compute_decile_spreads`) | `test_analytics_phase6c.py` (T-6C-31 to T-6C-40) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Evaluate mean return spread across score buckets | TB-REQ-05 | Monotonic spread analysis reported in structured diagnostics |
| **TB-REQ-10** | Governed Calibration Proposal Engine | Spec s28 Phase 6 | `post_listing/calibration.py` (`generate_proposal`) | `test_calibration_phase6d.py` (T-6D-01 to T-6D-30) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Implement proposal formulation with maturity gates | TB-REQ-08, TB-REQ-09 | Cryptographically bound proposal artifact linking dataset & analysis |
| **TB-REQ-11** | Candidate Configuration Generation (v1.6) | Spec s3.5, s20 | `post_listing/calibration.py` (`generate_v16_config`) | `test_calibration_phase6d.py` (T-6D-31 to T-6D-56) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Generate inactive candidate config (`is_active: false`) | TB-REQ-10 | v1.5 baseline unmodified; candidate passes schema check |
| **TB-REQ-12** | Shadow Evaluation Engine | Spec s3.1, s28 | `post_listing/v16_implementation.py` (`shadow_evaluate`) | `test_v16_implementation.py` (T-7-14 to T-7-28) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Pure in-memory rescoring without stored record mutation | TB-REQ-11 | Produces exact score and verdict deltas; zero historical mutation |
| **TB-REQ-13** | Configuration Diff & Verification Tool | Spec s3.5, s24 | `post_listing/v16_implementation.py` (`compute_diff`) | `test_v16_implementation.py` (T-7-07 to T-7-13, T-7-29 to T-7-36) | **COMPLETE** (in ref branch) / **MISSING** (on main) | Implement machine-readable and human-readable diff CLI | TB-REQ-11 | Validates approved scope changes only (modules A/B weights) |
| **TB-REQ-14** | Excel Sheet 11: `Post_Listing` Projection | Spec s22; Tech Design s12 | `excel.py` (`_write_post_listing`) | Proposed | **PARTIAL** | Wire post-listing observation records to Excel workbook generator | TB-REQ-01 | Append-only projection of post-listing rows in workbook |
| **TB-REQ-15** | Excel Sheet 12: `Backtest` Projection | Spec s22; Tech Design s12 | `excel.py` (`_write_backtest`) | Proposed | **PARTIAL** | Wire backtest analytics results to Excel workbook generator | TB-REQ-05 | Append-only projection of score vs realized return rows |
| **TB-REQ-16** | Secondary Ingestion Feeder (Phase 5) | Spec s6, s25 | `connectors/` & `extraction/` | `test_extraction.py`, `test_connectors.py` | **COMPLETE** (in ref branch) / **MISSING** (on main) | Keep isolated as upstream extraction layer | None | Ingestion validation produces canonical input; scoring untouched |
| **TB-REQ-17** | Browser Scorer / UI Dashboard | Ref Prototype `ipo-scorer_4.html` | `ipo-scorer_4.html` | Proposed manual UI test | **PARTIAL** | Modernize reference HTML into read-only analytical dashboard | TB-REQ-05 | Client-side visual representation; server remains source of truth |

---

## 4. Architecture Reconciliation & Invariant Protection

A critical requirement of this investigation is proving that Track B can be implemented purely additively without compromising any of the 10 non-negotiable architectural principles established in v1.5:

1. **Deterministic Scoring Invariant (Spec s3.1)**:
   * Track B return calculations, statistical aggregations, and shadow evaluations use pure mathematical functions and exact Decimal arithmetic (`ROUND_HALF_UP`).
   * No random seeds, platform-dependent floating-point summation, or wall-clock dependencies.
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
2. **UNKNOWN != Zero Invariant (Spec s3.2)**:
   * Missing market observations at 1W, 1M, or 6M horizons evaluate to `UNKNOWN` or `UNOBSERVED`, never coerced to 0% return.
   * Incomplete horizons are excluded from statistical denominators rather than defaulting to zero gain.
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
3. **Fail-Closed Validation Invariant (Spec s3.3, s20)**:
   * Invalid market data (e.g., negative prices, unverified corporate actions, missing issue price) immediately halts observation recording with `REFUSED` or `INVALID`.
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
4. **Evidence-Before-Score Invariant (Spec s3.4, s24)**:
   * Realized market quotes must attach source provenance (exchange trade bulletin reference, terminal snapshot timestamp, extraction locator).
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
5. **Immutable Evaluation History Invariant (Spec s3.6, s21, s23)**:
   * Post-listing observations are stored in dedicated observation subdirectories (`<store>/<eval_id>/observations/observation_<horizon>.json`).
   * Parent `evaluation.json`, `result.json`, and `manifest.json` files are never opened for writing or modified.
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
6. **Reproducibility Invariant (Spec s3.1, s20)**:
   * Observation records carry deterministic SHA-256 payload hashes.
   * Re-running the dataset assembly over identical observation files generates bit-for-bit identical dataset hashes.
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
7. **Configuration Versioning Invariant (Spec s3.5, s20)**:
   * Baseline configuration `config/ipo-config.v1.5.0.json` remains permanently immutable and active.
   * Calibration proposals formulate candidate configurations (e.g. `config/ipo-config.v1.6.0.json`) strictly tagged with `status: IMPLEMENTED_INACTIVE` and `is_active: false`.
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
8. **Source / Input Hashes Invariant (Spec s21)**:
   * Pre-listing input snapshot hashes and source manifest hashes remain completely untouched.
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
9. **Excel Append-Only Semantics (Spec s3.6, s22; Tech Design s12, s14)**:
   * Sheets 11 (`Post_Listing`) and 12 (`Backtest`) are purely additive projections.
   * Existing rows for Sheets 1–10, 13, and 14 are never updated or overwritten.
   * **Reconciliation Result**: *Fully Additive / Zero Violation*.
10. **Frozen Core Rule (Spec s29; Execution Prompt s23)**:
    * The six core evaluation engine files (`derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`, `extraction/price_band_notice.py`) remain completely untouched during Track B implementation.
    * Track B logic resides exclusively in dedicated packages (`engine/ipo_screening/post_listing/`).
    * **Reconciliation Result**: *Fully Additive / Zero Mutation to Frozen Core*.

### Exact Files Required for Implementation (When Authorized)
When implementation authority is granted, Track B can be implemented by adding new files and narrowly extending CLI/Excel projections:
* **New Additive Modules (No Core Mutation)**:
  * `engine/ipo_screening/post_listing/__init__.py`
  * `engine/ipo_screening/post_listing/observation.py`
  * `engine/ipo_screening/post_listing/return_engine.py`
  * `engine/ipo_screening/post_listing/dataset.py`
  * `engine/ipo_screening/post_listing/analytics.py`
  * `engine/ipo_screening/post_listing/calibration.py`
  * `engine/ipo_screening/post_listing/v16_implementation.py`
* **Additive Extensions to Existing Periphery Files**:
  * `engine/tools/ipo_screen.py`: Add CLI subcommand dispatcher for `post-listing` and `config` verification.
  * `engine/ipo_screening/excel.py`: Add projection methods `_write_post_listing` and `_write_backtest`.
* **Zero Mutation Files (Strictly Frozen)**:
  * `engine/ipo_screening/derived.py` (FROZEN)
  * `engine/ipo_screening/scoring.py` (FROZEN)
  * `engine/ipo_screening/knockouts.py` (FROZEN)
  * `engine/ipo_screening/snapshots.py` (FROZEN)
  * `engine/ipo_screening/evaluation.py` (FROZEN)
  * `engine/ipo_screening/extraction/price_band_notice.py` (FROZEN)

---

## 5. Dependency Gate Classification

Each dependency for Track B is formally evaluated and classified:

| Dependency Item | Classification | Description & Blocking Assessment | Status / Action Required |
| :--- | :---: | :--- | :--- |
| **Track A Pre-Listing Scoring Baseline** | **READY** | Track A v1.5 implementation provides immutable evaluation records and golden fixtures required as input for post-listing observations. | Ready in reference delivery branch; baseline clean on `main`. |
| **Post-Listing Observation Schema** | **READY** | Data model and JSON schema for `PostListingObservation` and horizons (`1W`, `1M`, `6M`) are fully designed. | Ready for implementation. |
| **Return Calculation Mathematics** | **READY** | Exact mathematical formulation for raw return, annualized return, benchmark return, and alpha is validated. | Ready for implementation. |
| **Historical Outcome Storage Architecture** | **READY** | Isolated sub-resource storage topography (`<eval_id>/observations/`) is validated and preserves parent record immutability. | Ready for implementation. |
| **Statistical Diagnostic Metrics** | **READY** | Mathematical algorithms for Hit Rate, Avoided Loss, Spearman Rank Correlation, and Decile Spreads are formalized. | Ready for implementation. |
| **Corporate Action Adjustment Feed** | **DATA / EXTERNAL** | Standardized corporate action feed (stock splits, bonus shares, rights) required to adjust historical prices. | **DECLARED GAP**: In initial phases, manual corporate action adjustments or split factors are supplied in observation inputs. |
| **Market Quote Data Source** | **DATA / EXTERNAL** | Realized closing prices for stock and Nifty 50 on specific post-listing calendar trading dates. | **DECLARED GAP**: Can be provided via canonical observation files or manual exchange bulletins without blocking core engine logic. |
| **Calibration Sample Size Governance** | **GOVERNANCE** | Policy decision on minimum mature sample size ($N$) before calibration proposals can be generated. | **DECLARED GAP**: Requires Program Authority (Ramki) policy sign-off; default heuristic set to $N \ge 15$ mature 6M observations. |
| **Excel Sheets 11 & 12 Wiring** | **IMPLEMENTATION** | Integration of `Post_Listing` and `Backtest` sheet writers into `excel.py`. | **READY**: Purely additive projection once observation store is ported. |
| **Interactive UI / Web Dashboard** | **UI / OPTIONAL** | Modernization of `ipo-scorer_4.html` into a visual backtesting dashboard. | **NON-BLOCKING**: CLI and Excel provide authoritative headless operation; UI is an optional presentation enhancement. |

---

## 6. Implementation Readiness Determination

### Formal Readiness Verdict: `READY_WITH_DECLARED_GAPS`

Track B is determined to be **READY FOR IMPLEMENTATION WITH DECLARED GAPS**.

#### Explanation of Declared Gaps and Non-Blocking Justification:
1. **Declared Gap G1 — External Live Price Feed Connector**:
   * *Assessment*: Automated real-time streaming connectors to exchange APIs are not yet implemented on `main`.
   * *Why Non-Blocking*: The Track B observation engine is designed to ingest standard validated JSON observation payloads (`observation_<horizon>.json`) created manually, from exchange bulletins, or via scheduled batches. Live API streaming is an operational convenience, not an architectural prerequisite.
2. **Declared Gap G2 — Corporate Action Adjustment Automation**:
   * *Assessment*: Automated adjustment for corporate actions (stock splits, bonus issues) requires an external corporate action calendar.
   * *Why Non-Blocking*: The `PostListingObservation` model includes explicit fields for `adjustment_factor` and `unadjusted_price`. This allows exact manual entry or corporate action adjustment flags without blocking return calculations.
3. **Declared Gap G3 — Formal Program Authority Sample Size Gate**:
   * *Assessment*: The exact minimum number of mature IPOs required before a calibration proposal can be formally recommended for production activation is pending formal Ramki sign-off.
   * *Why Non-Blocking*: The calibration proposal engine enforces a default fail-closed maturity gate ($N \ge 15$ mature 6M observations) and outputs proposals strictly with `status: IMPLEMENTED_INACTIVE`. This prevents any automated activation while allowing full testing of the proposal generation pipeline.

---

## 7. No Implementation Attestation

In strict compliance with Section 7 of the execution mandate:
* **Product Source Mutation**: `engine/` was NOT mutated.
* **Configuration Mutation**: `config/` was NOT mutated.
* **Test Mutation**: `tests/` was NOT mutated.
* **Activation**: Zero configurations were activated.
* **Branch Integrity**: `main` remains untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`.
* **Deployment / Infrastructure**: Zero production infrastructure was provisioned.

---

## 8. Durability Principle & Verification

Per the IIPS-style Universal Artifact Durability Invariant:
* The local Arena sandbox state is non-authoritative.
* This authoritative Track B Readiness & Reconciliation Report is committed directly to the designated repository branch `arena/01a10b42-ipo-screening-engine`.
* The commit is pushed to remote origin and verified via `git ls-remote`.

---

## 9. Required Program Authority (Ramki) Decisions

Before implementation of Track B is authorized in a subsequent execution pass, the following decisions are requested from Program Authority Ramki:

1. **Decision D1 — Primary Scope Authorization**: Confirm that Track B is formally authorized to implement Phases 6A–6D (Post-Listing Observation Model, Deterministic Return Engine, Historical Outcome Store, Statistical Analytics, and Governed Calibration Proposals) as an additive extension.
2. **Decision D2 — Secondary Workstream Priorities**: Confirm whether the Ingestion/Extraction Pipeline (Phase 5) and Web UI Dashboard (`ipo-scorer_4.html`) should be maintained as separate parallel workstreams or scheduled sequentially following Track B completion.
3. **Decision D3 — Calibration Promotion Policy**: Approve the proposed statistical governance criteria for future v1.6+ configuration activations:
   * Minimum mature sample size: $N \ge 15$ IPOs with complete 6-month post-listing observations.
   * Information Coefficient (IC) threshold: Positive Spearman rank correlation between model score and 6-month alpha.
   * Downside firewall: Zero baseline `AVOID` IPOs may receive an `APPLY` verdict under candidate configurations.
   * Mandatory human approval: Production configuration activation remains strictly gated on explicit Ramki sign-off.

---

## 10. Delivery & Repository Verification

* **Designated Branch**: `arena/01a10b42-ipo-screening-engine`
* **Base Commit**: `01ba66c12ca1195fd7acbd287c3e39a019808094`
* **Artifact Path**: `docs/TRACK_B_READINESS_REPORT.md`
* **Verification Status**: Ready for commit, push, and remote validation.
