# IPO Screening Engine — Evaluation Lifecycle Governance Decision
## ACTIVE → SUPERSEDED → ARCHIVED: Architecture & Product Contract

**Document Identifier:** `EVALUATION-LIFECYCLE-GOVERNANCE-DECISION-2026-10-07`  
**Date:** 2026-10-07  
**Branch:** `arena/01a10b42-ipo-screening-engine`  
**Authoritative Baseline Commit:** `b6020fc94b72957a5bb861e376230af8daa33293`  
**Governance Authority:** Read-Only Product + Architecture Investigation (Zero Implementation, Zero Code Mutation, Zero Data Deletion)

---

## A. Executive Decision

The IPO Screening Engine requires a durable, formal, and deterministic lifecycle governance contract to manage multiple immutable evaluation executions for the same issuer. 

Based strictly on authoritative repository specifications, technical design documents, and the immutability requirements of SEBI ICDR algorithmic screening, the architecture adopts the **Orthogonal Two-Dimensional Lifecycle Model** (Alternative B):

1. **Dimensional Separation:**
   - **Lifecycle State:** `ACTIVE` vs `SUPERSEDED` (Governs operational authority and supersession lineage).
   - **Visibility State:** `VISIBLE` vs `ARCHIVED` (Governs presentation prominence and historical clutter suppression).
   - **Operational Projection:**
     $$\text{Operational Status} = \begin{cases} 
     \mathbf{ACTIVE} & \text{if } \text{lifecycle} = \text{ACTIVE} \land \text{visibility} = \text{VISIBLE} \\
     \mathbf{SUPERSEDED} & \text{if } \text{lifecycle} = \text{SUPERSEDED} \land \text{visibility} = \text{VISIBLE} \\
     \mathbf{ARCHIVED} & \text{if } \text{visibility} = \text{ARCHIVED}
     \end{cases}$$
2. **Permanent Prohibition of Physical Deletion:**
   - Physical deletion of evaluation directories or JSON artifacts from disk is **strictly and permanently prohibited**.
   - Evaluations are immutable legal and compliance records under Spec v1.5 Section 21 & 23 and Technical Design Section 13.
3. **Decoupled Durability Boundary:**
   - Lifecycle metadata shall reside **outside** the immutable 7-file evaluation bundle (`evaluation.json`, `input.json`, `evidence.json`, `market.json`, `peers.json`, `result.json`, `manifest.json`).
   - Lifecycle state will be managed via a dual-layer store: a store-level index (`lifecycle_index.json`) for $O(1)$ query performance and an evaluation-sibling record (`lifecycle.json`) for decentralized auditability.
   - All cryptographic hashes (`result_hash`, `manifest_hash`, `input_snapshot_hash`) remain 100% bit-for-bit stable across all lifecycle transitions.
4. **Deterministic ACTIVE Selection:**
   - The engine rejects the unsafe heuristic `latest timestamp = current`.
   - `ACTIVE` evaluation selection is strictly mode-scoped (`FINAL` vs `PRELIMINARY`), policy-scoped (active policy v1.5.0), and resolved via an explicit issuer pointer.

---

## B. Existing Contract Evidence

The authoritative contracts within the repository govern evaluation persistence and immutability:

### 1. Specification v1.5 (`handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md`)
- **Section 21 (`Historical Persistence`):**
  > *"This is mandatory. Every evaluation receives: evaluation_id, ipo_id, evaluation_mode, evaluation_timestamp, engine_version, spec_version, config_version, input_snapshot_hash, source_manifest_hash, result_hash. Never overwrite a prior evaluation. A rerun creates a new immutable evaluation. Minimum historical lifecycle: PRELIMINARY → FINAL → POST_LISTING_1W → POST_LISTING_1M → POST_LISTING_6M."*
- **Section 22 (`Excel Historical Workbook`):**
  > *"Historical rule: Never replace historical rows. Each evaluation is an append-only row keyed by evaluation_id."*
- **Section 23 (`Immutable Evaluation Record`):**
  > *"Before Excel generation, persist a complete machine-readable record... evaluation.json, input.json, evidence.json, market.json, peers.json, result.json, manifest.json. The manifest records hashes of all source and result artifacts."*
- **Section 24 (`Auditability`):**
  > *"The engine must be able to answer: Why did this criterion receive this score? Which source supplied the value? Which page/table supplied it? Can the exact historical score be reproduced?"*

### 2. Technical Design v1.5 (`handoff/authoritative/IPO_Screening_Engine_Technical_Design_v1.5.md`)
- **Section 11 (`Historical Persistence`):**
  > *"Every run creates an immutable: EvaluationRecord. Recommended ID: `IPOID-YYYYMMDD-HHMMSS-MODE-<short-hash>`. Never update an old record."*
- **Section 13 (`Historical Preservation Rules`):**
  > *"Never: delete an old evaluation; overwrite an old score; regenerate an old evaluation under a new config without creating a new evaluation ID. A corrected extraction creates: evaluation_v2. A new config creates a new evaluation. A new market snapshot creates a new evaluation. Historical records remain immutable."*

### 3. Engine Implementation (`engine/ipo_screening/evaluation.py`)
- `EvaluationStore.write()` enforces exclusive directory creation (`mkdir(parents=True, exist_ok=False)`). Attempting to overwrite an existing evaluation ID raises `ImmutabilityError`.
- `EvaluationStore.verify_hashes()` independently verifies the SHA-256 of all 6 payload files against `manifest.json` and recomputes `result_hash`. Any alteration of stored files is immediately detected as tampering.

---

## C. The Three Proposed States: Definition & Model Architecture

### 1. State Definitions

#### `ACTIVE`
- **Definition:** The single evaluation designated as the authoritative operational benchmark for a specific issuer and evaluation mode (`FINAL` or `PRELIMINARY`).
- **Operational Meaning:** This evaluation supplies the score, verdict, knockout status, and confidence displayed in the primary IPO Directory (`#directory`), executive dashboard summaries, and default portfolio feeds.
- **Cardinality:** Exactly **one** evaluation per `(ipo_id, evaluation_mode)` may be `ACTIVE` at any given time.

#### `SUPERSEDED`
- **Definition:** An immutable historical evaluation that was previously authoritative but has been superseded by a newer, verified evaluation execution (due to extraction defect repair, amended statutory filing, price band finalization, or policy re-calibration).
- **Operational Meaning:** Fully preserved, fully auditable, and linked to its successor via a lineage pointer (`superseded_by`). It remains visible in the Issuer History view (`#ipos/{id}`) to demonstrate the analytical evolution of the offering.

#### `ARCHIVED`
- **Definition:** An immutable historical evaluation intentionally suppressed from standard operational and history views to eliminate visual clutter, while remaining 100% durable, tamper-evident, and recoverable.
- **Operational Meaning:** Hidden behind an explicit user toggle (`Show Archived Runs`) in the UI. Retains full cryptographic integrity. It is never physically purged from disk.

---

### 2. Analysis of Alternative Models

The prompt mandates evaluating three architectural structures:
- **Alternative A: Single Flat Enum (`status = ACTIVE | SUPERSEDED | ARCHIVED`)**
- **Alternative B: Orthogonal Two-Dimensional Model (`lifecycle = ACTIVE | SUPERSEDED`, `visibility = VISIBLE | ARCHIVED`)**
- **Alternative C: Dynamic Graph / Lineage-Only Model**

```
Alternative A (Flat Enum):               Alternative B (Orthogonal 2D Model):
┌─────────────────────────┐              ┌───────────────────┬──────────────────┐
│         ACTIVE          │              │  Lifecycle State  │ Visibility State │
├─────────────────────────┤              ├───────────────────┼──────────────────┤
│       SUPERSEDED        │              │      ACTIVE       │     VISIBLE      │
├─────────────────────────┤              │        vs         │        vs        │
│        ARCHIVED         │              │    SUPERSEDED     │     ARCHIVED     │
└─────────────────────────┘              └───────────────────┴──────────────────┘
(Collapses lineage and visibility)       (Preserves lineage even when hidden)
```

#### Detailed Comparison:

| Evaluation Criteria | Alternative A: Single Flat Enum | Alternative B: Orthogonal Two Dimensions | Alternative C: Graph Lineage Only |
|---|---|---|---|
| **State Loss Risk** | **HIGH.** Archiving an evaluation erases whether it was `ACTIVE` or `SUPERSEDED`, and severs supersession tracking. | **ZERO.** An evaluation can be `(SUPERSEDED, ARCHIVED)`. Its replacement lineage is completely preserved while hidden. | **MEDIUM.** Requires reconstructing full tree on every query. |
| **Withdrawn Offerings** | Ambiguous: Is a withdrawn IPO's evaluation `ARCHIVED` or `ACTIVE`? | Clean: `(ACTIVE, ARCHIVED)` — it is the latest evaluation, but suppressed because the IPO was withdrawn. | Complex edge cases. |
| **Exploratory Runs** | Cannot distinguish between superseded baseline runs (visible) and superseded test runs (archived). | Clean: Baseline run is `(SUPERSEDED, VISIBLE)`; exploratory run is `(SUPERSEDED, ARCHIVED)`. | Undifferentiated historical nodes. |
| **API Projection** | Single string `status`. | Simple projection: primary `lifecycle_state`, boolean `is_archived`, and combined `status`. | Complex graph traversal payloads. |

### Architectural Recommendation:
**Adopt Alternative B (Orthogonal Two-Dimensional Model).**  
It provides the exact mathematical separation required between *analytical lineage* (what replaced what) and *user visibility* (what is currently displayed).

---

## D. State Transition Matrix

The table below governs all transitions between the operational states:

| FROM \ TO | **ACTIVE** | **SUPERSEDED** | **ARCHIVED** |
|---|---|---|---|
| **ACTIVE** | **DISALLOWED** | **ALLOWED** | **CONDITIONAL** |
| **SUPERSEDED** | **CONDITIONAL** | **DISALLOWED** | **ALLOWED** |
| **ARCHIVED** | **CONDITIONAL** | **ALLOWED** | **DISALLOWED** |

### Transition Rules & Explanations:

1. **`ACTIVE → ACTIVE` (DISALLOWED):**
   - *Reason:* No-op. An evaluation cannot transition to a state it already occupies.
2. **`ACTIVE → SUPERSEDED` (ALLOWED):**
   - *Trigger:* Automatic upon successful ingestion and scoring of a newer evaluation with a distinct `result_hash` for the same `(ipo_id, mode)`, OR manual designation of an alternate active evaluation.
   - *Action:* The incumbent active evaluation records `superseded_by: <new_eval_id>` and transitions to `SUPERSEDED`.
3. **`ACTIVE → ARCHIVED` (CONDITIONAL):**
   - *Condition:* Permitted **only** when an offering is formally cancelled, rejected by SEBI, or withdrawn by the issuer.
   - *Guard:* Normal active evaluations for ongoing IPOs cannot be archived without first designating a successor active evaluation or declaring offering termination.
4. **`SUPERSEDED → ACTIVE` (CONDITIONAL):**
   - *Condition:* Administrative Rollback. Requires Governance Lead authority.
   - *Action:* Re-activating an older evaluation automatically demotes the currently active evaluation to `SUPERSEDED` (with reason `ADMINISTRATIVE_ROLLBACK`).
5. **`SUPERSEDED → SUPERSEDED` (DISALLOWED):**
   - *Reason:* No-op.
6. **`SUPERSEDED → ARCHIVED` (ALLOWED):**
   - *Trigger:* Routine operational decluttering. Analysts archive superseded intermediate, exploratory, or draft evaluations to clean the history table.
   - *Lineage:* The `superseded_by` relationship remains completely intact.
7. **`ARCHIVED → ACTIVE` (CONDITIONAL):**
   - *Condition:* Multi-step administrative restore. Requires unarchiving and explicit reactivation by an authorized administrator.
8. **`ARCHIVED → SUPERSEDED` (ALLOWED):**
   - *Trigger:* Standard "Unarchive" action. Restores the evaluation to visible historical status within `#ipos/{id}`.
9. **`ARCHIVED → ARCHIVED` (DISALLOWED):**
   - *Reason:* No-op.

---

## E. ACTIVE Selection Semantics

### 1. Why `latest timestamp = current` Is Fatal
Relying on `max(evaluation_timestamp)` to select the active evaluation introduces critical failure modes:

```
Timeline:
Day 1: Ingest complete statutory RHP (FINAL mode) ──────────> Score: 50.0 (Authoritative)
                                                                 ▲
Day 2: Analyst runs historical DRHP check (PRELIMINARY mode) ───┤ Timestamps: Day 2 > Day 1!
                                                                 ▼
Result under naive timestamp: DRHP falsely overwrites RHP! ───> CORRUPTED DASHBOARD
```

- **Preliminary After Final:** Running a `PRELIMINARY` DRHP evaluation after a `FINAL` RHP evaluation causes the preliminary score to falsely displace the definitive RHP evaluation.
- **Rerun of Legacy Code / Fixture:** Running an offline verification script or historical regression test with current wall-clock stamps would cause obsolete code outputs to supersede production results.
- **Failed Ingestions:** A partially parsed or errored extraction must never displace an active, verified evaluation.
- **Policy Mismatches:** Evaluations generated under experimental or shadow configurations (e.g. candidate policy v1.6.0) must never overwrite evaluations under the active ratified baseline (v1.5.0).

### 2. Authoritative Selection Algorithm

The engine shall identify the `ACTIVE` evaluation through the following deterministic precedence:

```python
def get_active_evaluation(ipo_id: str, mode: str, store_root: Path) -> Optional[EvaluationSummary]:
    # Step 1: Query the Explicit Issuer Lifecycle Pointer
    index = load_lifecycle_index(store_root)
    issuer_entry = index.get_issuer(ipo_id)
    if issuer_entry:
        active_id = issuer_entry.get_active_id(mode=mode)
        if active_id and store.exists(active_id):
            record = store.read(active_id)
            if record.get("config_hash") == ACTIVE_RATIFIED_CONFIG_HASH:
                return to_summary(record, lifecycle="ACTIVE", visibility="VISIBLE")

    # Step 2: Fallback Inference (Cold-start / Legacy Store Migration)
    candidates = []
    for eval_id in store.list_evaluations():
        rec = store.read(eval_id)
        if (rec.get("ipo_id") == ipo_id 
            and rec.get("evaluation_mode") == mode.upper()
            and rec.get("config_hash") == ACTIVE_RATIFIED_CONFIG_HASH
            and not is_explicitly_archived(eval_id, index)):
            candidates.append(rec)

    if not candidates:
        return None

    # Sort strictly by statutory progression, then timestamp, then result_hash
    candidates.sort(key=lambda r: (
        r.get("evaluation_timestamp", ""),
        r.get("result_hash", "")
    ))
    return to_summary(candidates[-1], lifecycle="ACTIVE", visibility="VISIBLE")
```

#### Selection Invariants:
1. **Mode Isolation:** `FINAL` and `PRELIMINARY` evaluations have separate, independent active pointers. A `PRELIMINARY` evaluation can never displace a `FINAL` evaluation.
2. **Policy Verification:** An evaluation is only eligible for `ACTIVE` status if its `config_hash` matches the ratified active screening policy (currently `ipo-config.v1.5.0.json`).
3. **Explicit Pointer Authority:** The explicit pointer in `lifecycle_index.json` strictly supersedes all timestamp sorting.

---

## F. Supersession Semantics

### 1. Scope & Constraints
Supersession can only occur when all four boundary conditions are met:
1. **Issuer Invariance:** $\text{ipo\_id}(\text{new}) == \text{ipo\_id}(\text{incumbent})$.
2. **Mode Invariance:** $\text{evaluation\_mode}(\text{new}) == \text{evaluation\_mode}(\text{incumbent})$.
3. **Validity Gate:** The new evaluation must successfully pass all schema, financial, and semantic validation gates without raising an uncaught exception.
4. **Distinct Outcome:** $\text{result\_hash}(\text{new}) \neq \text{result\_hash}(\text{incumbent})$. (Identical outcomes trigger the existing idempotency gate and return the existing record).

### 2. Lineage Representation
To protect frozen core immutability, lineage pointers must never be injected into historical `evaluation.json` files. Lineage is tracked as follows:

```json
{
  "evaluation_id": "R-K-FASHION-ACCESSORIES-LIMITED-20261007-092818Z-final-6ee95f0a",
  "lifecycle_state": "SUPERSEDED",
  "visibility_state": "VISIBLE",
  "superseded_by": "R-K-FASHION-ACCESSORIES-LIMITED-20261007-133111Z-final-c4e88b17",
  "superseded_at": "2026-10-07T13:31:11Z",
  "supersession_reason": "DEFECT_REPAIR_STATUTORY_CFO_CAGR_SUPPLIER",
  "replaces": "R-K-FASHION-ACCESSORIES-LIMITED-20261007-062328Z-final-808a237d"
}
```

- **Unidirectional vs Bidirectional:**
  - The Lifecycle Store records both `superseded_by` (forward pointer) and `replaces` (backward pointer).
  - This allows traversing the full lineage graph forward (discovering the modern repair) or backward (auditing historical baselines).

---

## G. Archival Semantics

### 1. What Archival Does and Does Not Mean
- **Archival Is:** An operational visibility filter that removes non-authoritative historical clutter from default dashboard views.
- **Archival Is NOT:** Physical deletion, data purging, disk cleanup, or invalidation of evidence.

### 2. The Seven Absolute Negative Rules of Archival
Archival MUST NEVER modify or purge:
1. `evaluation.json`
2. `input.json`
3. `evidence.json`
4. `result.json`
5. `manifest.json`
6. `market.json` or `peers.json`
7. `observations/` (child post-listing observation files)

Any implementation that writes to, mutates, or truncates any of these 7 files or their parent directory timestamp violates the core repository contract.

### 3. Archival Invariants & Answers to Explicit Questions:
- **Can an ACTIVE evaluation be archived?** Only if the entire offering is formally marked `CANCELLED` or `WITHDRAWN`. Under normal operating conditions, an ongoing IPO must have its active evaluation visible.
- **Can a SUPERSEDED evaluation be archived?** YES. This is the primary intended usage for exploratory and intermediate development executions.
- **Can an ARCHIVED evaluation become visible again?** YES. Archival is **100% reversible** at any time.
- **Can an ARCHIVED evaluation become ACTIVE?** CONDITIONAL. It must be unarchived and explicitly designated as `ACTIVE` via an administrative rollback action.
- **Can an ARCHIVED evaluation ever be physically deleted?** **STRICTLY NO.** The engine contains zero physical deletion logic.
- **Where does archival state live?** In the external `lifecycle_index.json` and sibling `lifecycle.json` files.

---

## H. Persistence Architecture

### Comparison of Storage Strategies:

```
Option A: Mutate evaluation.json            Option D: Dual Hybrid Architecture (RECOMMENDED)
<store>/<eval_id>/                         <store_root>/
├── evaluation.json  <-- VIOLATES HASH!    ├── lifecycle_index.json  <-- Fast O(1) Index
├── manifest.json                          └── <eval_id>/
└── ...                                        ├── evaluation.json   <-- 100% IMMUTABLE
                                               ├── manifest.json     <-- 100% IMMUTABLE
                                               ├── ...
                                               └── lifecycle.json    <-- Local Lifecycle Metadata
```

### The Dual Hybrid Architecture (Option D):

1. **Store-Level Fast Index (`<store_root>/lifecycle_index.json`):**
   - High-speed lookup for `list_ipos()` and `list_evaluations()`.
   - Maintains issuer-level active pointers:
     ```json
     {
       "issuers": {
         "R-K-FASHION-ACCESSORIES-LIMITED": {
           "active_final_id": "R-K-FASHION-ACCESSORIES-LIMITED-20261007-133111Z-final-c4e88b17",
           "active_preliminary_id": null,
           "status": "ACTIVE_OFFERING",
           "last_updated": "2026-10-07T13:31:11Z"
         }
       },
       "archived_evaluations": [
         "R-K-FASHION-ACCESSORIES-LIMITED-20261007-035435Z-final-1d64ea28",
         "R-K-FASHION-ACCESSORIES-LIMITED-20261007-062328Z-final-808a237d"
       ]
     }
     ```
   - Updated atomically using atomic write-rename (`tempfile.NamedTemporaryFile` + `os.replace`).
2. **Sibling Audit Record (`<store_root>/<evaluation_id>/lifecycle.json`):**
   - Sits inside the evaluation directory as an unhashed sibling file (excluded from `manifest.json`).
   - Ensures that if an evaluation directory is archived to tape, exported, or transferred to cold storage, its lifecycle lineage travels with it.
   - Contains transition history, timestamps, operator signatures, and supersession pointers.

---

## I. Cryptographic Implications

Lifecycle metadata must be strictly separated from cryptographic hashes to guarantee analytical reproducibility:

| Hash / Identifier | Participates in Lifecycle? | Invariant Rule |
|---|---|---|
| **`result_hash`** | **NO** | Recomputed strictly from deterministic inputs, scores, knockouts, and derived metrics. Never changes when an evaluation is superseded or archived. |
| **`input_snapshot_hash`** | **NO** | Hash of canonical input snapshot. Unaffected by lifecycle transitions. |
| **`source_manifest_hash`** | **NO** | Hash of extracted evidence items and source documents. Completely decoupled. |
| **`manifest.json`** | **NO** | Manifest registers hashes for the 6 core payload files. It **explicitly does not list `lifecycle.json`**. |
| **`evaluation_id`** | **NO** | Created at execution time using timestamp and `result_hash`. Immutable forever. |

### Recording Transitions Without Hash Invalidation:
Because `lifecycle.json` is not listed in `manifest.json`, running `EvaluationStore.verify_hashes(evaluation_id)` continues to report 100% cryptographic integrity (`result_hash_matches == True`, `artifact_mismatches == []`) before and after any supersession or archival event!

---

## J. Dependency & Audit Implications

### 1. Tracing External References
Evaluation IDs are deeply embedded across repository artifacts:

```
Evaluation ID (<evaluation_id>)
     │
     ├── Observations: <store>/<id>/observations/observation_*.json
     │
     ├── Backtest Datasets: tests/fixtures/post_listing/dataset_*.json ("final_evaluation_id")
     │
     ├── Calibration Proposals: config/calibration-proposal.*.json ("source_dataset_hash")
     │
     ├── Excel Workbooks: build/IPO_Screening_History.xlsx ("Evaluations", "Module_Scores")
     │
     └── Investigation Reports: docs/investigation/*.md (Cited audit evidence)
```

### 2. Downstream Reference Invariants:
1. **Resolvability Guarantee:** Any evaluation referenced by a backtest dataset or calibration proposal **must remain permanently resolvable** via `GET /api/v1/evaluations/{id}`. Archiving an evaluation must never return HTTP 404; it returns the evaluation record marked with `"is_archived": true`.
2. **Dataset Integrity Protection:** `verify_dataset()` in `dataset.py` verifies parent evaluations on disk. Because archival preserves all files in `<store>/<id>/`, `validate_parent_evaluation()` continues to pass without error.
3. **Transition Constraints:** Downstream references **never block** an evaluation from becoming `SUPERSEDED` (models calibrate against historical superseded runs). However, if an evaluation is referenced by an active dataset, archiving it requires an explicit audit warning logged in the lifecycle index.

---

## K. UI Contract

The presentation layer (`frontend/app.js`, `frontend/styles.css`) shall implement the following user contracts:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ IPO Directory (#directory)                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Issuer: R.K. Fashion Accessories Limited                                    │
│ Active Score: 50.0 / 100  |  Verdict: INSUFFICIENT_DATA  |  Confidence: Low │
│ Mode: FINAL (v1.5.0)      |  Historical Executions: 3 (1 visible, 2 archived)│
│ [View Active Scorecard]   |  [View Issuer Lifecycle History]                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Issuer Lifecycle History (#ipos/{ipo_id})                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ ACTIVE EVALUATION                                                           │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ [ACTIVE] c4e88b17 | Score: 50.0 | Date: 2026-10-07 13:31 UTC (Authoritative)│ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ HISTORICAL EXECUTIONS (SUPERSEDED)                                          │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ [SUPERSEDED] 6ee95f0a | Score: 55.0 | Date: 2026-10-07 09:28 UTC        │ │
│ │ Lineage: Superseded by c4e88b17 (Defect Repair: Statutory CFO/CAGR)     │ │
│ │ [Archive] [View Scorecard] [Inspect Evidence]                           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [x] Show Archived Executions (2)                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ [ARCHIVED] 808a237d | Score: 60.0 | Date: 2026-10-07 06:23 UTC [Unarchive]│
│ │ [ARCHIVED] 1d64ea28 | Score: 61.0 | Date: 2026-10-07 03:54 UTC [Unarchive]│
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Scorecard Detail (#evaluations/{id}) — Viewing Superseded Evaluation 6ee95f0a │
├─────────────────────────────────────────────────────────────────────────────┤
│ ⚠️  NOTICE: This evaluation is SUPERSEDED.                                  │
│     An authoritative replacement was generated on 2026-10-07 (Score: 50.0).  │
│     [Switch to Active Evaluation c4e88b17 &rarr;]                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## L. Authorization Model

Lifecycle mutations require strict role-based separation:

| Action | Required Role | API Endpoint | Preconditions & Guards |
|---|---|---|---|
| **Ingest & Auto-Supersede** | Analyst / Operator | `POST /api/v1/ingest/document` | Valid PDF, schema pass, deterministic score. |
| **Archive Superseded Run** | Analyst / Operator | `POST /api/v1/evaluations/{id}/archive` | Target must be `SUPERSEDED`. Cannot archive `ACTIVE`. |
| **Unarchive Run** | Analyst / Operator | `POST /api/v1/evaluations/{id}/unarchive` | Target must be `ARCHIVED`. Restores to `SUPERSEDED`. |
| **Administrative Rollback**| Governance Lead | `POST /api/v1/evaluations/{id}/make-active`| Explicit justification code; demotes current active. |
| **Archive Withdrawn Offering**| Compliance Admin | `POST /api/v1/ipos/{id}/archive-offering` | Requires formal proof of issue withdrawal/cancellation. |
| **Physical Deletion** | **PROHIBITED** | **NO ENDPOINT** | Architecture permanently prohibits physical deletion. |

---

## M. R.K. Fashion Case Mapping

The four executions of R.K. Fashion Accessories Limited are mapped into the recommended governance framework:

```
[2026-10-07T03:54:35Z] Score 61.0 (1d64ea28) ──> Status: ARCHIVED (Exploratory Ingestion)
          │
[2026-10-07T06:23:28Z] Score 60.0 (808a237d) ──> Status: ARCHIVED (Intermediate Shareholding Tuning)
          │
[2026-10-07T09:28:18Z] Score 55.0 (6ee95f0a) ──> Status: SUPERSEDED / VISIBLE (Retained Defect Baseline)
          │
[2026-10-07T13:31:11Z] Score 50.0 (c4e88b17) ──> Status: ACTIVE (Authoritative Post-Repair Benchmark)
```

### Forensic Disposition:
1. **`c4e88b17` (Score 50.0):** Marked `ACTIVE / VISIBLE`. Displayed in `#directory` and as the authoritative headline scorecard.
2. **`6ee95f0a` (Score 55.0):** Marked `SUPERSEDED / VISIBLE`. It is the formal pre-repair baseline committed in `df17d0a7` and cited in `RK-FASHION-DATA-COVERAGE-RECONCILIATION.md`. It must remain visible by default in the history timeline so auditors can verify the defect repair.
3. **`808a237d` (Score 60.0) & `1d64ea28` (Score 61.0):** Marked `SUPERSEDED / ARCHIVED`. Hidden by default behind the "Show Archived Executions" toggle, preventing visual clutter while remaining fully recoverable.

---

## N. Protected-Record Rules

To safeguard system integrity, certain evaluations are classified under protection tiers:

### 1. Protection Tiers

| Tier | Evaluation Classes | Archival Permitted? | Deactivation Permitted? |
|---|---|---|---|
| **Tier 1: Core Golden Baselines** | `VISHAL-NIRMITI-LIMITED-...` (`e84f8bc...`), golden test fixtures. | **STRICTLY FORBIDDEN** | **STRICTLY FORBIDDEN** |
| **Tier 2: Governance & Backtest** | Evaluations cited in `tests/fixtures/post_listing/dataset_*.json` or signed calibration proposals. | **CONDITIONAL** (Requires governance confirmation; generates audit log). | Permitted via standard supersession. |
| **Tier 3: Standard Filings** | General corporate statutory evaluations. | Permitted when superseded. | Permitted via standard supersession. |

---

## O. Failure & Concurrency Rules (Fail-Closed)

The lifecycle engine enforces fail-closed behavior across all edge cases:

1. **Concurrent Supersession Race:**
   - Writing to `lifecycle_index.json` requires acquiring an exclusive file lock (`lifecycle_index.lock`).
   - If two evaluations complete simultaneously, the second writer detects that the active pointer has advanced and evaluates its supersession against the newly committed active ID.
2. **Cyclic Lineage Prevention:**
   - Before setting `A superseded_by B`, the engine traverses the lineage graph of `B`. If `B` has an ancestor path to `A`, the mutation aborts with `CyclicLineageError`.
3. **Corrupted or Missing Lifecycle Index (Self-Healing Cold Start):**
   - If `lifecycle_index.json` is missing or fails JSON parsing, the engine **fails closed** to read-only dynamic inference (Section E.2) and logs an administrative alert without halting screening operations.
4. **Dangling Pointers:**
   - If `lifecycle_index.json` contains an ID not present in `EvaluationStore`, the missing ID is flagged as `ORPHAN_LIFECYCLE_RECORD` and ignored; the system falls back to the most recent verified physical record.

---

## P. Recommended Implementation Phases (When Authorized)

When implementation is formally authorized in a future prompt, it should be delivered in 5 distinct phases:

### Phase A: Contract & Schema Definition
- Author Pydantic models and JSON schemas for `LifecycleRecord`, `IssuerLifecycleEntry`, and `LifecycleIndex`.
- Codify error classes: `CyclicLineageError`, `ProtectedRecordError`, `InvalidStateTransitionError`.
- *Authorization Required:* Schema definitions and model additions.

### Phase B: Persistence Engine & Store Integration
- Implement `LifecycleStore` managing `lifecycle_index.json` with POSIX file locking and atomic rename.
- Extend `EvaluationStore` with non-invasive helper methods (`get_lifecycle(eval_id)`, `set_lifecycle(eval_id, state)`).
- Ensure `verify_hashes()` continues to pass with zero modifications to the 7 core artifacts.
- *Authorization Required:* Persistence code additions.

### Phase C: Presentation API Extensions
- Add query parameters to Presentation API: `GET /ipos/{id}/history?include_archived=false`.
- Introduce governed mutation endpoints:
  * `POST /api/v1/evaluations/{id}/archive`
  * `POST /api/v1/evaluations/{id}/unarchive`
  * `POST /api/v1/evaluations/{id}/make-active`
- Update Read-Only Middleware whitelist for these specific lifecycle management paths.
- *Authorization Required:* API route additions and middleware updates.

### Phase D: Frontend UI Implementation
- Update `frontend/app.js`:
  * Render `ACTIVE` banner and `SUPERSEDED` warnings.
  * Add expandable "Archived Executions" section in `#ipos/{id}`.
  * Implement single and bulk archive/unarchive UI buttons.
- Update `frontend/styles.css` with badges for `ACTIVE`, `SUPERSEDED`, and `ARCHIVED`.
- *Authorization Required:* Frontend script and stylesheet changes.

### Phase E: Verification & Test Suite
- Add comprehensive pytest integration tests covering state transitions, concurrency locks, cyclic lineage prevention, and bulk archival.
- Verify bit-for-bit preservation of Vishal Nirmiti golden hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.
- *Authorization Required:* Test file additions.

---

## Q. Explicit Non-Authorizations

In strict accordance with the prompt's authority boundaries, the following actions were **NOT authorized and were NOT performed**:
- ❌ No implementation of lifecycle schemas, classes, or persistence code.
- ❌ No modification of existing source code (`engine/`, `frontend/`, `config/`).
- ❌ No modification of `EvaluationStore` or any evaluation artifact on disk.
- ❌ No creation of `lifecycle.json` or `lifecycle_index.json` files.
- ❌ No state changes made to any existing evaluation (no records marked ACTIVE, SUPERSEDED, or ARCHIVED).
- ❌ No deletion or physical alteration of any evaluation data.
- ❌ No tests added or modified.
- ❌ No Git commits or branch updates.
- ❌ No push to remote repository.
- ❌ No merge to `main`.

---

# FINAL STATUS

INVESTIGATION COMPLETE — IMPLEMENTATION NOT AUTHORIZED
