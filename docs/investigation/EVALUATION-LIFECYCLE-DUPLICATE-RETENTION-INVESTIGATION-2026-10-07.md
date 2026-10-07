# IPO Screening Engine — Evaluation Lifecycle & Duplicate Retention Architectural Investigation

**Document ID:** `EVALUATION-LIFECYCLE-DUPLICATE-RETENTION-INVESTIGATION-2026-10-07`  
**Date:** 2026-10-07  
**Branch:** `arena/01a10b42-ipo-screening-engine`  
**Authoritative Baseline Commit:** `b6020fc94b72957a5bb861e376230af8daa33293`  
**Investigation Mode:** Read-Only Product + Architecture Investigation (Zero Implementation, Zero Mutation, Zero Deletion)

---

## Executive Summary

During browser-based user verification following the defect repair of R.K. Fashion Accessories Limited, four distinct evaluation executions of the same issuer and evaluation mode (`FINAL`) were observed in the presentation store:

1. `R-K-FASHION-ACCESSORIES-LIMITED-20261007-133111Z-final-c4e88b17` — Final Score: **50.0 / 100** (Authoritative Post-Repair)
2. `R-K-FASHION-ACCESSORIES-LIMITED-20261007-092818Z-final-6ee95f0a` — Final Score: **55.0 / 100** (Pre-Repair Baseline, Commit `df17d0a7`)
3. `R-K-FASHION-ACCESSORIES-LIMITED-20261007-062328Z-final-808a237d` — Final Score: **60.0 / 100** (Intermediate Extraction Phase)
4. `R-K-FASHION-ACCESSORIES-LIMITED-20261007-035435Z-final-1d64ea28` — Final Score: **61.0 / 100** (Initial Ingestion Baseline)

This investigation resolves the fundamental product and architectural question: **How should the IPO Screening Engine model, store, expose, retain, archive, and display multiple evaluation executions for the same company?**

### Key Findings & Answers:
1. **Multiple Evaluations Are Intentional and Mandatory:** Under Spec v1.5 Section 21 (`Historical Persistence`) and Tech Design Section 13 (`Historical Preservation Rules`), multiple executions for the same IPO are an explicit core architectural requirement. The design rule states: *"Never delete an old evaluation; never overwrite an old score... A corrected extraction creates `evaluation_v2`. A new config creates a new evaluation. A new market snapshot creates a new evaluation. Historical records remain immutable."*
2. **Current Model Is Append-Only Immutable Executions:** The engine models an evaluation strictly as an immutable execution record. The store (`EvaluationStore`) has no concept of "current" vs "superseded"; it stores every unique execution. The presentation layer (`list_ipos`) computes "latest" on-the-fly via a chronological timestamp sort (`max(evaluation_timestamp)`).
3. **Physical Deletion Is Strictly Prohibited:** Physically deleting evaluation directories from disk violates core regulatory compliance (SEBI ICDR algorithmic auditability), breaks cryptographic hash verification (`manifest.json`), invalidates downstream backtest dataset integrity (`validate_parent_evaluation` in `dataset.py`), and corrupts calibration proposal provenance (`source_dataset_hash`).
4. **Current Ingestion Idempotency Is Strict on Content, Not Time:** In `PresentationService.ingest_document()`, an incoming filing upload is deduplicated only if its deterministic `result_hash` matches an existing record, or if both `input_snapshot_hash` and `config_hash` match. When extraction bugs are repaired or inputs change, `result_hash` changes; hence, creating a new evaluation record is the intended and correct behavior.
5. **The Missing Product Layer Is Lifecycle Status:** The engine lacks a formal, queryable lifecycle status (`ACTIVE` vs `SUPERSEDED` vs `ARCHIVED`). As a result, the UI history view (`#ipos/{id}`) displays all historical executions side-by-side with equal visual prominence, leading to user confusion.
6. **Recommended Resolution: Non-Destructive Archival & Status Badging:** We recommend implementing a non-destructive lifecycle management layer (Option B: `ARCHIVE / SUPERSEDE`) with UI filtering (Option C: `HIDE FROM DEFAULT UI`). Physical deletion must remain disabled.

---

## A. Current Architecture

### 1. The Immutability and Historical Persistence Contract
The persistence architecture is codified across three authoritative documents:
- **Spec v1.5 Section 21 (`Historical Persistence`):** Mandatory historical persistence. Every evaluation receives `evaluation_id`, `ipo_id`, `evaluation_mode`, `evaluation_timestamp`, `engine_version`, `spec_version`, `config_version`, `input_snapshot_hash`, `source_manifest_hash`, and `result_hash`. Overwrites are strictly forbidden.
- **Spec v1.5 Section 23 (`Immutable Evaluation Record`):** Persists a complete machine-readable directory containing 7 artifacts prior to any reporting or Excel projection.
- **Tech Design Section 13 (`Historical Preservation Rules`):**
  > *"Never: delete an old evaluation; overwrite an old score; regenerate an old evaluation under a new config without creating a new evaluation ID. A corrected extraction creates `evaluation_v2`. A new config creates a new evaluation. A new market snapshot creates a new evaluation. Historical records remain immutable."*

### 2. `EvaluationStore` Implementation
Located at `engine/ipo_screening/evaluation.py` (lines 403–533):
```python
class EvaluationStore:
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)

    def write(self, record: EvaluationRecord) -> Path:
        directory = self.path_for(record.evaluation_id)
        if directory.exists():
            raise ImmutabilityError(
                f"evaluation {record.evaluation_id!r} already exists at {directory}; "
                "historical evaluations are immutable and must never be overwritten (spec s21)."
            )
        directory.mkdir(parents=True, exist_ok=False)
        for name, payload in sorted(record.artifacts().items()):
            target = directory / name
            with target.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.write("\n")
        return directory
```

#### Key Store Characteristics:
- **Append-Only File Store:** Writes to `<store_root>/<evaluation_id>/` using `exist_ok=False`. Writing an existing ID raises `ImmutabilityError`.
- **Zero Mutation APIs:** The store contains `write()`, `read()`, `read_artifact()`, `read_full()`, `read_all()`, `latest_for()`, and `verify_hashes()`. There is **no `delete()`**, **no `update()`**, and **no `archive()`** method.
- **Tamper-Evident Verification (`verify_hashes`):** Recomputes SHA-256 for all 6 payload files against `manifest.json` and independently re-derives `result_hash` from the deterministic payload. Any byte modification to stored artifacts is detected immediately.

---

## B. Current UI & API Behavior

### 1. Presentation API (`engine/ipo_screening/presentation/api.py`)
The Presentation API is structured around read-only resource discovery with a single ingestion entry point:
- `GET /api/v1/ipos`: Lists tracked issuers with summary counts and `latest_*` fields.
- `GET /api/v1/ipos/{ipo_id}`: Retrieves issuer details and its list of evaluations.
- `GET /api/v1/ipos/{ipo_id}/history`: Returns chronological evaluation timeline and preliminary-to-final delta.
- `GET /api/v1/evaluations`: Deterministically lists all evaluation records across all issuers.
- `GET /api/v1/evaluations/{id}`: Detailed scorecard for a specific evaluation execution.
- `GET /api/v1/evaluations/{id}/evidence`: Field-level citations and source manifests.
- `GET /api/v1/evaluations/{id}/post-listing`: Realized return observations.
- `GET /api/v1/evaluations/{id}/performance`: Excess returns and benchmark comparisons.
- `POST /api/v1/ingest/document`: Ingests a statutory PDF, runs extraction and scoring, and records the evaluation.

#### The Strict Read-Only Middleware Guard:
Lines 348–368 of `api.py` enforce a strict HTTP middleware:
```python
@app.middleware("http")
async def read_only_guard(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.method == "POST" and request.url.path in (
            "/api/v1/ingest/document",
            "/api/v1/ingest/document/",
        ):
            return await call_next(request)

        return JSONResponse(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            content={
                "error": "Method Not Allowed",
                "message": f"Method {request.method} is prohibited. The Presentation API is strictly read-only.",
                "code": "READ_ONLY_METHOD_NOT_ALLOWED",
            },
            headers={"Allow": "GET, HEAD, OPTIONS"},
        )
```
- **Mutation Endpoints:** **NONE EXIST.** Any attempt to issue `DELETE`, `PUT`, or `PATCH` is rejected with `HTTP 405 Method Not Allowed`.
- **Deletion/Archive Endpoints:** There is no endpoint to delete an evaluation, delete an IPO, archive an evaluation, or mark an evaluation as current.

### 2. Frontend User Interface (`frontend/app.js`)
Inspection of the client SPA reveals the current presentation behavior:
1. **IPO Directory (`#directory` / `renderIposTable`):**
   - Displays one row per tracked issuer.
   - Summarizes evaluation activity: `evaluation_count: ipo.evaluation_count`.
   - Shows `latest_score` and `latest_verdict`.
   - Provides a direct link: `<a href="#evaluations/${ipo.latest_evaluation_id}">View Scorecard</a>`.
   - In this view, multiple executions are hidden behind the aggregate summary; the user sees only the most recent execution's score.
2. **Lifecycle History View (`#ipos/{id}` / `renderIpoDetail`):**
   - Shows the company name and `history.history.length` Lifecycle Evaluations.
   - Displays a `Preliminary -> Final Progression Delta` card if a `preliminary_delta` object exists.
   - Renders a plain table with columns: `Evaluation ID`, `Mode / Stage`, `Timestamp`, `Final Score`, `Verdict`, `Confidence`, `Action (Scorecard, Evidence)`.
   - **Crucial Deficiency:** All executions appear with equal visual weight. If four `FINAL` evaluations exist for R.K. Fashion, all four appear as standard rows. There is no indicator stating which execution is "Active", which is "Superseded", or why scores changed from 61 to 60 to 55 to 50.
3. **Evaluation Scorecard Detail (`#evaluations/{id}`):**
   - Renders the full deterministic scorecard.
   - Displays `RESULT HASH`, `DATE`, `ENGINE`, and `CONFIG` tags.
   - Does not state whether the evaluation being viewed is current or superseded.
4. **User Controls:**
   - **No selection checkboxes** exist in any table.
   - **No bulk action controls** exist.
   - **No archive, hide, or delete buttons** exist.

---

## C. Evaluation Identity Semantics

### 1. Anatomy of an `evaluation_id`
Generated by `evaluate_id()` in `engine/ipo_screening/hashing.py`:
$$\text{evaluation\_id} = \texttt{\{safe\_ipo\}-\{YYYYMMDD\}-\{HHMMSSZ\}-\{mode\}-\{short\_hash(result\_hash)\}}$$
Example: `R-K-FASHION-ACCESSORIES-LIMITED-20261007-133111Z-final-c4e88b17`

| Component | Example Value | Semantic Meaning |
|---|---|---|
| `safe_ipo` | `R-K-FASHION-ACCESSORIES-LIMITED` | Slugified entity identifier for the issuer. |
| `date` | `20261007` | UTC date of execution. |
| `time` | `133111Z` | UTC wall-clock time of execution (ISO-8601). |
| `mode` | `final` | Lifecycle stage (`preliminary`, `final`, `post_listing_1w`, etc.). |
| `short_hash` | `c4e88b17` | First 8 characters of the deterministic SHA-256 `result_hash`. |

### 2. Result Hash vs Evaluation ID
An evaluation's identity is split across two conceptual layers:
1. **The Deterministic Result Hash (`result_hash`):**
   - Calculated via `compute_result_hash()` over:
     $$\text{result\_payload} = \{\text{engine\_version}, \text{spec\_version}, \text{config\_hash}, \text{input\_snapshot\_hash}, \text{source\_manifest\_hash}, \text{market\_snapshot\_hash}, \text{peer\_snapshot\_hash}, \text{mode}, \text{plan}, \text{derived\_metrics}, \text{knockouts}, \text{score}, \text{penalties}, \text{missing\_unverified}\}$$
   - **Crucial Rule:** `result_hash` deliberately **excludes** wall-clock timestamps and `evaluation_id`.
   - Two runs with identical inputs, configuration, and code will produce the exact same `result_hash`, even years apart.
2. **The Execution Identity (`evaluation_id`):**
   - Binds the deterministic `result_hash` to a physical point in time (`evaluation_timestamp`).
   - Represents the historical occurrence of an evaluation execution.

---

## D. Persistence & Artifact Map

Tracing a single evaluation execution reveals a tightly coupled hierarchy of persisted files:

```
<store_root>/
└── <evaluation_id>/
    ├── evaluation.json       # Canonical master record: metadata, scores, derived metrics, validation
    ├── input.json            # Canonical input snapshot conforming to ipo-input.v1.5.schema.json
    ├── evidence.json         # Source documents, page citations, line snippets, extraction method
    ├── market.json           # Frozen market snapshot (GMP, subscription, market regime)
    ├── peers.json            # Frozen peer multiples and peer financial metrics
    ├── result.json           # Isolated scoring outcome (score, knockouts, confidence, bounds, verdict)
    ├── manifest.json         # Cryptographic manifest listing SHA-256 hashes of all 6 sibling files
    └── observations/         # Child directory created post-listing (storage.py)
        ├── observation_listing_day.json
        ├── observation_1w.json
        ├── observation_1m.json
        └── observation_6m.json
```

### Downstream Repository Artifacts Referencing `evaluation_id`:

| Artifact | Repository Path | Nature of Dependency | Impact of Deleting Evaluation |
|---|---|---|---|
| **Child Observations** | `<store>/<id>/observations/*.json` | Direct filesystem parent directory | Child observations orphaned or destroyed. |
| **Post-Listing Dataset** | `tests/fixtures/post_listing/dataset_*.json` | Stores `final_evaluation_id` & `final_result_hash` per row | `verify_dataset()` fails with `ParentEvaluationNotFoundError`. |
| **Calibration Proposals** | `config/calibration-proposal.*.json` | Stores `source_dataset_hash` | Cryptographic provenance of policy calibration proposal is broken. |
| **Excel Historical Workbook** | `build/IPO_Screening_History.xlsx` | `Evaluations`, `Module_Scores`, `Evidence` rows keyed by ID | Excel sheets desynchronize from store; auditability destroyed. |
| **Investigation Reports** | `docs/investigation/*.md` | Explicitly cite execution IDs and result hashes | Forensic and audit documentation becomes non-verifiable. |

---

## E. Duplicate & Idempotency Semantics

### 1. Ingestion Idempotency Logic
In `PresentationService.ingest_document()`, duplicate detection operates under a three-tier gate:

```python
existing_eval_id: Optional[str] = None

# Tier 1: Exact Evaluation ID match
if self.eval_store.exists(outcome.record.evaluation_id):
    existing_eval_id = outcome.record.evaluation_id
else:
    # Tier 2 & 3: Iterate through stored evaluations in the same mode
    for eid in self.eval_store.list_evaluations():
        rec = self.eval_store.read(eid)
        if rec.get("evaluation_mode", "").upper() == outcome.record.evaluation_mode.upper():
            # Tier 2: Exact deterministic result hash match
            if rec.get("result_hash") == outcome.record.result_hash:
                existing_eval_id = eid
                break
            # Tier 3: Exact input snapshot and config hash match
            if (rec.get("input_snapshot_hash") == outcome.record.input_snapshot_hash
                and rec.get("config_hash") == outcome.record.config_hash):
                existing_eval_id = eid
                break
```

### 2. What Constitutes a Duplicate vs a New Execution?
- **Exact Duplicate:** A submission where the resulting canonical input and active config produce either an identical `result_hash` or identical `(input_snapshot_hash, config_hash)`.
  - *Engine Behavior:* Bypasses `EvaluationStore.write()`, sets `is_duplicate=True`, and returns the existing evaluation record.
- **New Execution:** Any submission where:
  - The filing PDF contains different data.
  - The extraction logic was updated/repaired, producing different fields in `canonical_dict`.
  - The active configuration version or hash changed.
  - Different market or peer snapshots were enriched.
  - *Engine Behavior:* Generates a new `result_hash`, builds a new `evaluation_id`, and writes a new 7-file directory to `EvaluationStore`.

---

## F. R.K. Fashion Case Study

The four observed R.K. Fashion Accessories executions represent the exact forensic evolution of the screening engine across recent development sessions:

```
[2026-10-07T03:54:35Z] Score: 61.0 (Initial Ingestion Baseline)
        │
        ▼ (Fix post-issue shareholding / OFS NIL extraction)
[2026-10-07T06:23:28Z] Score: 60.0 (Intermediate Extraction)
        │
        ▼ (Enforce fail-closed fallback elimination; commit df17d0a7)
[2026-10-07T09:28:18Z] Score: 55.0 (Pre-Repair Baseline: 3 defects present)
        │
        ▼ (Repair supplier concentration, Indian CAGR, statutory CFO; commit aa4d76af)
[2026-10-07T13:31:11Z] Score: 50.0 (Authoritative Post-Repair Outcome)
```

### Forensic Analysis of the Four Executions:

| Execution ID | Timestamp (UTC) | Final Score | Base Score | Result Hash | Status & Audit Classification |
|---|---|---|---|---|---|
| `...-20261007-035435Z-final-1d64ea28` | 03:54:35 | 61.0 | 64.0 | `1d64ea28...` | **Superseded (Exploratory):** Initial ingestion prior to strict schema and table tuning. |
| `...-20261007-062328Z-final-808a237d` | 06:23:28 | 60.0 | 63.0 | `808a237d...` | **Superseded (Intermediate):** Captures intermediate shareholding adjustments. |
| `...-20261007-092818Z-final-6ee95f0a` | 09:28:18 | 55.0 | 58.0 | `6ee95f0a...` | **Superseded (Authoritative Baseline):** Committed in `df17d0a7`. Must remain auditable as the baseline for the forensic defect investigation. |
| `...-20261007-133111Z-final-c4e88b17` | 13:31:11 | 50.0 | 53.0 | `c4e88b17...` | **ACTIVE / CURRENT:** Authoritative post-repair outcome committed in `aa4d76af` and `b6020fc9`. |

### Audit & Retention Findings:
1. **None are "accidental" or corrupted data:** Each execution was a deterministic evaluation of R.K. Fashion under the exact code state present in the workspace at that moment.
2. **Commit `df17d0a7` specifically required score 55.0:** The pre-repair baseline score of 55.0 is formally documented in `RK-FASHION-DATA-COVERAGE-RECONCILIATION.md` and test suite `test_rk_fashion_reconciliation.py`. Deleting `...-6ee95f0a` would destroy the audit baseline proving why the repair was necessary.
3. **Commit `aa4d76af` produced score 50.0:** Score 50.0 is the verified, permanent outcome.
4. **Conclusion:** All four executions must be retained on disk for audit integrity. In the UI, `...-c4e88b17` (score 50.0) must be tagged `CURRENT / ACTIVE`, while the previous three must be tagged `SUPERSEDED`.

---

## G. Comparison: Delete vs Archive vs Hide

| Evaluation Dimension | Option A: DELETE (Physical Deletion) | Option B: ARCHIVE / SUPERSEDE (Explicit Lifecycle State) | Option C: HIDE FROM DEFAULT UI (Presentation Filter Only) |
|---|---|---|---|
| **Action** | `shutil.rmtree()` removes `<store>/<id>/` from disk. | Add `status: "SUPERSEDED"` and link `superseded_by: <id>`. | UI/API defaults to displaying only the latest execution. |
| **Store Immutability** | **VIOLATED.** Destroys append-only contract. | **PRESERVED.** Artifacts remain intact; state added via metadata/overlay. | **PRESERVED.** Store untouched. |
| **Spec v1.5 Compliance** | **FAIL.** Violates Section 21 and Tech Design s13. | **PASS.** Fulfills Tech Design s13 (`evaluation_v2`). | **PASS.** Fully compliant. |
| **Auditability (s24)** | **DESTROYED.** Historical advice cannot be reproduced. | **PERFECT.** Complete audit trail with supersession lineage. | **PERFECT.** Complete audit trail preserved. |
| **Backtest Dataset Impact** | **BREAKING.** `verify_dataset()` crashes on missing parent. | **ZERO.** Parent evaluation remains resolvable. | **ZERO.** Datasets unaffected. |
| **Cryptographic Hashes** | Hashes lost. | All manifest and result hashes remain verifiable. | All hashes remain verifiable. |
| **Reversibility** | **IRREVERSIBLE.** Permanent data loss. | **100% REVERSIBLE.** Can be unarchived or inspected. | **100% REVERSIBLE.** Filter toggleable. |
| **API Changes** | Requires `DELETE` endpoint (breaks read-only guard). | Add query param `include_superseded=false` or state field. | Add query param `latest_only=true`. |
| **UI Experience** | Clean directory, but dead links / 404s for old bookmarks. | Clean directory showing Active; History view shows lineage badges. | Clean directory; History view shows all runs with "Latest" tag. |
| **Security Risk** | **CRITICAL.** Path traversal risk; arbitrary file deletion. | **VERY LOW.** Non-destructive state transition. | **ZERO.** Read-only view adjustment. |

---

## H. Audit, Evidence & Governance Implications

### 1. Distinction: Product Retention vs Audit Retention vs User Visibility
- **Audit Retention (Mandatory & Permanent):** Regulated financial screening algorithms must be capable of answering: *"What did the model recommend on 2026-10-05, on what exact data, and with what code version?"* Under SEBI (Investment Advisers) Regulations and ICDR disclosure standards, an evaluation once generated cannot be expunged. It is an immutable audit record.
- **Product Retention (Governed Lifecycle):** The operational lifecycle that connects evaluations to post-listing observations (1W, 1M, 6M), backtest analytics, and model calibration proposals. Deleting an evaluation breaks this chain.
- **User Visibility (Presentation Layer):** What the human analyst needs to see in the morning. An analyst examining R.K. Fashion wants to see the **active, authoritative score (50.0)**. They do not want visual clutter from older intermediate runs, but they must be able to expand "Historical Executions" to inspect the model's evolution.

### 2. The Invariants That Forbid Physical Deletion
An evaluation record **MUST NEVER BE PHYSICALLY DELETED** if:
1. It is the golden evaluation baseline (e.g., Vishal Nirmiti `e84f8bc...`).
2. It is referenced by a `PostListingObservation` in `observations/`.
3. It is included as a row in a backtest dataset (`tests/fixtures/post_listing/dataset_*.json`).
4. It forms part of the dataset hash (`source_dataset_hash`) of an active calibration proposal (`config/calibration-proposal.v1.6.0.json`).
5. It is referenced in a `preliminary_delta` record of a subsequent `FINAL` evaluation.
6. It has been cited in any signed investigation report or published recommendation.

---

## I. Recommended Product Contract

Based strictly on the codebase architecture and repository specifications, we recommend the following formal product contract for future implementation:

### 1. Architectural Concept: Two-Tier Evaluation Lifecycle
Every evaluation in `EvaluationStore` shall possess a lifecycle status:
- `ACTIVE` (or `CURRENT`): The single authoritative evaluation for a given `(ipo_id, mode)`.
- `SUPERSEDED`: A valid historical evaluation that has been replaced by a more recent execution (due to extraction repair, newer filing, or updated policy).
- `ARCHIVED`: An evaluation manually hidden from operational views by an authorized analyst, retaining full auditability.

### 2. Product Behavior Rules:
1. **Physical Deletion Forbidden:** The engine shall provide **no physical deletion API**. Any request to delete an evaluation is rejected.
2. **Automatic Supersession:** When a new evaluation is successfully executed for an `(ipo_id, mode)` with a different `result_hash`:
   - The new evaluation becomes `ACTIVE`.
   - The prior evaluation automatically transitions to `SUPERSEDED`, recording:
     * `superseded_by: <new_evaluation_id>`
     * `superseded_at: <timestamp>`
     * `supersession_reason: "NEW_EXECUTION"`
3. **Directory View (`#directory`):**
   - Displays strictly one row per IPO representing the `ACTIVE` evaluation.
   - Shows the active score, verdict, and confidence.
4. **History View (`#ipos/{id}`):**
   - Chronologically lists all executions for the IPO.
   - The current execution is highlighted with an `ACTIVE` badge.
   - Superseded executions display a `SUPERSEDED` badge with a link to the superseding evaluation.
   - A toggle control: `[x] Show Superseded Executions (3)` allows collapsing older runs to eliminate visual clutter while preserving instantaneous access.
5. **Scorecard View (`#evaluations/{id}`):**
   - If an analyst navigates to a superseded evaluation (e.g. score 55), the page renders a prominent banner:
     > ⚠️ *Notice: This evaluation was superseded on 2026-10-07 by evaluation `...-c4e88b17` (Score: 50.0). [View Active Scorecard &rarr;]*

---

## J. Answers to Prompt Specific Questions

1. **Should users be allowed to physically delete evaluations?**  
   **NO.** Physical deletion violates Spec v1.5 s21 and Tech Design s13 ("Never delete an old evaluation"), breaks cryptographic integrity, breaks backtest dataset validation, and destroys SEBI ICDR auditability.
2. **Should users be allowed to archive/supersede them?**  
   **YES.** Analysts should have the ability to archive or supersede historical runs, removing them from active operational dashboards while preserving all underlying artifacts.
3. **Should the UI distinguish Current vs Historical?**  
   **YES.** The UI must prominently distinguish `ACTIVE / CURRENT` evaluations from `SUPERSEDED / HISTORICAL` evaluations in both the Directory and History views.
4. **Should bulk selection be supported?**  
   **YES, for bulk archival / hiding only.** Bulk physical deletion must never be supported. Bulk marking of older exploratory executions as `SUPERSEDED` or `ARCHIVED` is a legitimate product workflow.
5. **What artifacts must never be deleted?**  
   - Master records (`evaluation.json`) and canonical snapshots (`input.json`).
   - Sibling evidence records (`evidence.json`) and cryptographic manifests (`manifest.json`).
   - Post-listing observations and backtest dataset rows.
   - Golden evaluations and calibration baseline proposals.
6. **Should deletion be reversible?**  
   Physical deletion is irreversible and therefore prohibited. Lifecycle management (Archiving / Superseding / Hiding) **must be 100% reversible**.
7. **What should happen to evidence when an evaluation is archived?**  
   Evidence must remain **completely intact and persisted on disk**. Archival alters query-layer visibility and presentation status; it never alters or purges evidence files.
8. **What should happen when a new evaluation supersedes an old one?**  
   The new evaluation is written as a new immutable directory. The previous evaluation transitions to `SUPERSEDED` with a cryptographic lineage pointer to the new ID, and the UI automatically switches the default display to the new evaluation.

---

## K. Proposed Future Implementation Scope (When Authorized)

When implementation is formally authorized in a subsequent turn, the recommended work should be scoped as follows:

1. **Phase 1: Presentation Projection & UI Badging (Zero Store Changes)**
   - Update `PresentationService.get_ipo_detail()` and `get_ipo_history()` to compute `is_latest: bool` on each `EvaluationSummary`.
   - Update `frontend/app.js` (`renderIpoDetail`):
     * Badge the latest evaluation as `CURRENT / ACTIVE`.
     * Badge earlier evaluations of the same mode as `SUPERSEDED`.
     * Add a UI collapse/expand toggle for superseded evaluations.
     * Add a warning banner on `#evaluations/{id}` when viewing a non-latest evaluation.
2. **Phase 2: First-Class Lifecycle Metadata (Non-Destructive Store Extension)**
   - Add a lightweight `lifecycle.json` file inside `<store>/<evaluation_id>/` (or a store-level index `lifecycle_index.json`) tracking `{status: "ACTIVE"|"SUPERSEDED"|"ARCHIVED", superseded_by, reason}`.
   - Maintain the frozen core and `manifest.json` completely untouched.
3. **Phase 3: Governed Archival Endpoint**
   - Introduce an explicit `POST /api/v1/evaluations/{id}/archive` endpoint protected by strict authorization guards and path-traversal validation.
   - Enforce fail-closed dependency checks (prevent archiving if referenced in an active backtest dataset).

---

## L. Explicit List of Things NOT Authorized in This Prompt

This investigation was conducted strictly under read-only parameters. The following actions were **NOT authorized and were NOT performed**:
- ❌ No implementation of deletion, archiving, or hiding logic.
- ❌ No modifications to source code (`engine/`, `frontend/`, `config/`).
- ❌ No modifications to existing evaluation directories or JSON files.
- ❌ No deletion of any evaluation record on disk (all R.K. Fashion records preserved).
- ❌ No API changes or additions.
- ❌ No UI template or stylesheet changes.
- ❌ No Git commits or branch updates.
- ❌ No push to remote repository.
- ❌ No changes to `origin/main` or `arena/01a10b42-ipo-screening-engine`.

---

# FINAL STATUS

INVESTIGATION COMPLETE — IMPLEMENTATION NOT AUTHORIZED
