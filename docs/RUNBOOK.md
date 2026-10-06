# Runbook — IPO Screening Engine v1.5

Audience: the analyst running and maintaining the engine. Everything here has
been executed in this repository; commands are copy-pasteable from the
repository root.

---

## 1. What this engine does, in one paragraph

It turns a structured description of an IPO — offer terms, restated financials,
governance, business quality, peer multiples and market snapshots — into a
deterministic score out of 100, a score *range*, a confidence level, a verdict
and a tri-state knockout line. Every input value must be traceable to a source
document, absence is recorded as `UNKNOWN` rather than zero, and every run is
frozen into an immutable record that can be replayed to the same hash months
later. Excel is a projection of those records, never a source of truth.

---

## 2. Setup

```bash
cd /home/user/ipo-screening-engine

# Python 3.11+. Install the three runtime/test dependencies.
python3 -m pip install --break-system-packages jsonschema openpyxl pytest

# pypdf is only needed to re-extract text from an RHP PDF.
python3 -m pip install --break-system-packages pypdf

# The engine is a plain package: put it on PYTHONPATH, no install step.
export PYTHONPATH=$PWD/engine
```

Sanity check:

```bash
python3 -c "import ipo_screening as e; print(e.__version__, e.SPEC_VERSION)"
# 1.5.0 1.5

python3 -m pytest tests/ -q
# 238 passed
```

---

## 3. Daily workflow

The operator surface is a single CLI:

```bash
python3 engine/tools/ipo_screen.py --help
```

### 3.1 Validate the policy configuration

Always do this first after touching `config/ipo-config.v1.5.0.json`. A broken
configuration is a hard gate: the engine refuses to score rather than guessing.

```bash
python3 engine/tools/ipo_screen.py check-config
```

Expected output ends with `valid  True` and lists 10 resolved
profile × structure plans, each totalling 100 points. A non-zero exit means the
config is invalid and must be fixed before any evaluation.

### 3.2 Build the input document

Write a JSON file that validates against `schema/ipo-input.v1.5.schema.json`.
Two conventions matter more than any other:

* **Omit or set `null` for anything you could not establish.** Never write `0`
  to mean "unknown". Zero is a fact; absence is a gap. The engine cannot tell
  them apart after the fact, and a zero will be scored.
* **Record evidence for every material value.** `_sources` lists the documents,
  `_evidence` maps an input path to the page and quote it came from. The engine
  warns about material fields with no evidence and refuses to certify a run
  whose provenance is missing.

The golden fixture is the worked example:

```bash
python3 -m json.tool fixtures/vishal_nirmiti/input.json | head -60
```

### 3.2.1 Automated RHP Extraction & Pre-Score Enrichment (`extract --enrich`)

To automatically extract statutory facts directly from an RHP/DRHP PDF and enrich
them with a Price Band Notice:

```bash
python3 engine/tools/ipo_screen.py extract filings/prospectus.pdf \
    --enrich \
    --notice notices/price_band.txt \
    --output build/canonical.json \
    --mode final
```

To run evaluation immediately on the resulting document, pass `--run`:

```bash
python3 engine/tools/ipo_screen.py extract filings/prospectus.pdf \
    --enrich \
    --notice notices/price_band.txt \
    --run \
    --mode final \
    --at 2026-10-05T12:00:00Z \
    --store build/evaluations
```

### 3.2.2 Deterministic Canonical Assembly (`assemble`)

To assemble a canonical input JSON from an unpriced or preliminary input along
with external market, peer, and analyst snapshots:

```bash
python3 engine/tools/ipo_screen.py assemble raw_rhp.json \
    --notice notices/price_band.txt \
    --market market_snapshot.json \
    --peers peer_snapshot.json \
    --output build/assembled_canonical.json \
    --mode final
```

### 3.3 Run an evaluation

**Pin the evaluation instant with `--at` whenever the result will be compared,
published or stored.** The instant determines which market blocks are fresh and
which peers are current; without `--at` the run uses the wall clock and the
result hash will move as data crosses a staleness boundary.

```bash
python3 engine/tools/ipo_screen.py run fixtures/vishal_nirmiti/input.json \
    --at 2026-10-05T12:00:00Z \
    --store build/evaluations \
    --workbook build/IPO_Screening_History.xlsx
```

Read the output top to bottom:

```
  Final score           35.0  (base   38.0, penalties -3.0)
  Score range           25.0 to   62.0
  Verdict             INSUFFICIENT_DATA  [final]
  Confidence          Low (73.0% of evaluable points available)
  Knockouts           UNVERIFIED
```

Then the module table, the completeness block, and the warnings. The flags to
act on:

| Signal | Meaning |
| --- | --- |
| `Knockouts UNVERIFIED` | At least one knockout could not be decided. Read the `Missing_Unverified` sheet and supply the missing fact, or accept that the gate is unresolved. |
| `Verdict INSUFFICIENT_DATA` | A declared critical input is unknown and no knockout triggered. The score is *not* a decision. |
| `Confidence Low` | Under 80% of the evaluable points were available. |
| `range` wider than ~20 points | The result is dominated by what is missing rather than by what is known. |
| `PROVENANCE_MISSING_FOR_FIELDS` | Scored values are not traceable to a source. Fix before relying on the result. |

Use `--verbose` to see every warning, the per-knockout missing facts, and the
top strengths and risks.

### 3.4 Modes

| Mode | When | What differs |
| --- | --- | --- |
| `preliminary` | Before the issue closes | The post-close market criteria (`gmp_trend`, `retail_nii_penalty`, subscription) are excluded and remain visible as `EXCLUDED_BY_MODE` |
| `final` | After the issue closes | All criteria, including the retail/NII under-subscription penalty |
| `post_listing_1w` / `_1m` / `_6m` | After listing | Scoring is unchanged; the realised outcome from the input's `post_listing` block is recorded for back-testing |

A Final evaluation automatically picks up the latest stored Preliminary for the
same issuer and stores a delta record. The Preliminary itself is never modified.

```bash
# Preliminary, then Final two hours later.
python3 engine/tools/ipo_screen.py run input.json --mode preliminary \
    --at 2026-10-05T12:00:00Z --store build/evaluations
python3 engine/tools/ipo_screen.py run input.json --mode final \
    --at 2026-10-05T14:00:00Z --store build/evaluations
```

### 3.5 Post-listing tracking

Add the realised outcome to the input and re-run in a post-listing mode. The
`Post_Listing` and `Backtest` sheets pick it up on the next projection.

```jsonc
"post_listing": {
  "listing_date": "2026-10-12",
  "listing_gain_pct": 22.4,
  "return_1w_pct": 31.2,
  "return_1m_pct": 18.9
}
```

```bash
python3 engine/tools/ipo_screen.py run input.json --mode post_listing_1m \
    --at 2026-11-16T12:00:00Z --store build/evaluations \
    --workbook build/IPO_Screening_History.xlsx
```

---

## 4. Audit and reproducibility

### 4.1 Verify every stored record

Re-derives each artifact hash from disk and recomputes the result hash. Any
edit to any file is detected. Exit code `3` means a mismatch.

```bash
python3 engine/tools/ipo_screen.py verify --store build/evaluations
# OK   VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0  artifacts=6
# 1 evaluation(s) checked, 0 mismatch(es)
```

### 4.2 Replay a historical run

Re-evaluates from the *frozen artifacts* at the *original instant*. Success
means the same inputs, snapshot, configuration and engine version still produce
the same result hash — the spec s19 guarantee.

```bash
python3 engine/tools/ipo_screen.py replay \
    VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0 \
    --store build/evaluations
# stored result     e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1
# recomputed        e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1
# match             True
```

If `match` is `False`, check in this order:

1. **Config changed.** `config_hash` is part of the result hash. Any edit to
   `ipo-config.v1.5.0.json` moves every subsequent result hash. Compare the
   `config_hash` in the stored `evaluation.json` with the current one.
2. **Engine version changed.** `ENGINE_VERSION` is part of the payload.
3. **Snapshot artifacts edited.** Run `verify` first; a tampered
   `input.json`/`evidence.json`/`market.json`/`peers.json` breaks replay.
4. **Genuine bug.** If all three check out, the replay has found a
   reproducibility defect; treat it as a P1 and add a regression test.

### 4.3 Rebuild the workbook

Excel is a projection. Rebuild it any time from the store; never hand-edit it.
The rebuild is deterministic, so byte-identical inputs give byte-identical
output.

```bash
python3 engine/tools/ipo_screen.py project \
    --store build/evaluations --workbook build/IPO_Screening_History.xlsx
```

---

## 5. Reading the workbook

Fourteen sheets, in fixed order (`SHEET_ORDER`):

| Sheet | What it answers |
| --- | --- |
| `IPO_Master` | One row per issuer: first/latest evaluation, count, latest score and verdict |
| `Evaluations` | One row per evaluation, append-only, keyed by `evaluation_id`. Every hash is here |
| `Module_Scores` | Module A–F score, max, known and unknown points |
| `Criteria_Detail` | Every criterion: state, value, band, score, max, reason, formula, evidence |
| `Knockouts` | Tri-state per rule with the missing inputs named on the row |
| `Penalties` | Each penalty and whether it triggered |
| `Missing_Unverified` | The action list: every unknown criterion, unverified knockout, non-VALID peer, unusable market block and unresolved penalty, with the points affected |
| `Evidence` | Source, page, section, quote, extraction method for every evidence item |
| `Market_Snapshots` | Per block: status, as-of, age, values |
| `Peer_Snapshots` | Per peer: status, as-of, age, listed years, multiples, reason |
| `Post_Listing` | Realised listing gain and 1w/1m/6m returns |
| `Backtest` | Score at evaluation vs realised outcome |
| `Config_Versions` | Which config version and hash produced which evaluations |
| `Run_Log` | Status, validation result, error and warning counts per run |

Work top-left to bottom-right and open `Missing_Unverified` first: it is the
list of things to go and find.

### Historical preservation

Rows are never replaced. Re-running the same input at a later instant produces a
new `evaluation_id` and a new row; the earlier row stays. If you need to correct
an input, correct it and re-run — that creates a new evaluation, and the
original remains auditable.

---

## 6. Troubleshooting

| Symptom | Cause | Action |
| --- | --- | --- |
| `SchemaValidationError` | The input does not match the v1.5 schema | The message names the JSON path. Check for a quoted number (`"1500000"`), a date in the wrong format, or an unknown key. `additionalProperties: false` means typos are errors |
| `SemanticValidationError: PROCEEDS_GCP_LIMIT` | GCP exceeds 25% of the fresh issue | Check the reporting unit. Amounts are in `financials.reporting_unit`; the fresh issue is normalised internally |
| `GCP_CEILING_RECORDED_AS_AMOUNT` | A GCP amount equal to exactly 25% of the fresh issue | Almost certainly the legal ceiling recorded as the amount. Set `amount: null` and `undisclosed_marker: "[●]"` |
| `GCP_UNDISCLOSED` (warning) | The RHP prints `[●]` for GCP | Expected. The proceeds criterion is `UNKNOWN`; the ceiling is recorded separately as `gcp_legal_max` |
| `PEER_MULTIPLES_STALE` | A peer multiple is older than `peer_staleness_days` (30) | Refresh the peer data or accept the wider range. A stale peer is treated exactly like a missing one |
| `OFS_6_2_BREACH` | On the 6(2) route, a seller exceeded its permitted cap | Correct the seller row, or use route 6(1) if that is what the RHP says |
| `PERIODS_CYCLICAL_INSUFFICIENT` | The `cyclical` profile needs five FY observations | Supply five, or use the `standard` profile |
| `ImmutabilityError` | Writing an `evaluation_id` that already exists | Expected. Change the inputs, the config or the instant; never delete a stored evaluation |
| `unknown evaluation mode` | A mode not declared in `config.modes` | Use one of the five declared modes |
| `unknown metric` in `check-config` | An overlay references a metric with no implementation | Implement the metric in `derived.py` and register it. Do **not** loosen the validator |
| Empty `Evidence` / `Peer_Snapshots` sheet | The projection was built from a record missing its artifacts | Use `project` against the store, or `build_workbook(record.to_dict())`. Fixed in `EvaluationRecord.to_dict()`; if it recurs, the record is not self-sufficient |

---

## 7. Maintenance

### 7.1 Changing policy

Policy lives in `config/ipo-config.v1.5.0.json`, not in code. Bands, weights,
thresholds, knockouts, penalties, verdict cut-offs, profile rules and
validation limits are all data. After any edit:

```bash
python3 engine/tools/ipo_screen.py check-config   # must print valid True
python3 -m pytest tests/ -q                       # must stay green (238)
```

Changing the config **invalidates every stored result hash** by design: the
`config_hash` is part of the result payload. Existing records remain valid as
history; new runs will not replay to the old hashes. If you need both, cut a new
config version rather than editing in place.

### 7.2 Adding a derived metric

1. Implement it in `engine/ipo_screening/derived.py` with `@metric("id")`.
2. Always return a `formula` string, even from UNKNOWN paths.
3. Return `_u(...)` for absence, never a default of zero.
4. Declare it in `config.derived_metrics` if a criterion references it.
5. Add a test asserting the UNKNOWN path as well as the value path.

`check_config` fails if a criterion or overlay references an unimplemented
metric (`CONFIG_METRIC_UNIMPLEMENTED`), so a missing implementation cannot ship
silently.

### 7.3 Adding a sector overlay

Add the profile to `sector_overlays`, list removed criteria and added criteria,
and run `check-config`. Each profile × structure combination must reconcile to
exactly 100 points or the config is rejected
(`CONFIG_OVERLAY_RECONCILE`).

Cover both halves of the overlay in tests: the plan swap (which criteria appear)
and the derivation of every metric those criteria read
(`tests/test_sector_overlays.py`). The reconciliation test alone will not catch a
metric that is present in the plan but never derives a value.

### 7.3.1 Where a given behaviour is tested

| Question | Module |
| --- | --- |
| Does the golden case still produce the frozen result? | `tests/test_vishal_golden.py` |
| Is a missing input treated as UNKNOWN rather than zero? | `tests/test_core_semantics.py` |
| Is a bad input blocked, and by which gate? | `tests/test_validation_gates.py` |
| Which criteria does each profile resolve to? | `tests/test_overlays_knockouts.py` |
| What does each overlay's metric compute? | `tests/test_sector_overlays.py` |
| Are hashes, immutability and Excel projection intact? | `tests/test_reproducibility_store.py` |
| Does the acceptance matrix (P1–P30, S1–S17) hold? | `tests/test_acceptance_matrix.py` |
| Does the CLI behave and exit with the right code? | `tests/test_cli.py` |

### 7.4 Re-extracting RHP text

The page cache is not committed.

```bash
python3 - <<'PY'
from pypdf import PdfReader
import json
reader = PdfReader("handoff/reference/U01122MH1994PLC185445-vishal nirmiti.pdf")
pages = {str(i + 1): (p.extract_text() or "") for i, p in enumerate(reader.pages)}
json.dump(pages, open(".cache/rhp_pages.json", "w"))
print(len(pages), "pages cached")
PY
```

Takes about 30 seconds for 551 pages. Note that PDF page *n* is
`.cache/rhp_pages.json` key `n`.

---

## 8. Golden regression

The Vishal Nirmiti case is the reference behaviour for the whole engine. Its
expected outputs are committed under `fixtures/vishal_nirmiti/`.

```bash
python3 -m pytest tests/test_vishal_golden.py -q
```

The frozen result (config 1.5.0 / engine 1.5.0, evaluated at
`2026-10-05T12:00:00Z`):

| Field | Value |
| --- | --- |
| Final score | **35.0** (base 38.0, penalties −3.0) |
| Score range | **25.0 – 62.0** |
| Verdict | `INSUFFICIENT_DATA` |
| Confidence | `Low` (73.0 of 100 points available) |
| Knockouts | K1/K5/K6 `UNVERIFIED`, K2/K3/K4 `CLEAR` |
| Result hash | `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` |
| Evaluation id | `VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0` |

### Regenerating the expected files

Only do this when a *deliberate* change has moved the result, and say so in the
commit message. Regenerating to make a failure disappear defeats the purpose.

```bash
rm -rf build/vishal
python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
from ipo_screening.pipeline import evaluate, load_config
from ipo_screening.evaluation import EvaluationStore

cfg = load_config()
doc = json.load(open("fixtures/vishal_nirmiti/input.json"))
when = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
store = EvaluationStore("build/vishal/evaluations")
out = evaluate(doc, cfg, mode="final", evaluation_datetime=when, store=store,
               workbook_path="build/vishal/IPO_Screening_History.xlsx")
ev = out.record.to_dict()
fx = Path("fixtures/vishal_nirmiti")

json.dump({"expected": out.validation.to_dict()}, open(fx / "expected_validation.json", "w"), indent=2, sort_keys=True)
d = out.derived.to_dict()
json.dump({"metrics": d["metrics"], "overrides_applied": d["overrides_applied"]}, open(fx / "expected_derived.json", "w"), indent=2, sort_keys=True)
json.dump(ev["knockouts"], open(fx / "expected_knockouts.json", "w"), indent=2, sort_keys=True)
json.dump(ev["score"], open(fx / "expected_score.json", "w"), indent=2, sort_keys=True)
json.dump({
    "confidence": ev["confidence"], "score_range": ev["score_range"], "verdict": ev["verdict"],
    "hashes": {k: ev[k] for k in ("input_snapshot_hash", "source_manifest_hash",
                                  "market_snapshot_hash", "peer_snapshot_hash", "result_hash")},
    "engine_version": ev["engine_version"], "spec_version": ev["spec_version"],
    "config_version": ev["config_version"],
}, open(fx / "expected_verdict.json", "w"), indent=2, sort_keys=True)
print(ev["result_hash"])
PY
python3 -m pytest tests/ -q
```

---

## 9. What the engine will not do

Worth knowing, so nobody waits for behaviour that is deliberately absent:

* **It will not fill a gap with a plausible number.** No ceiling, no peer median,
  no "last year's value", no zero.
* **It will not score with an invalid configuration.** There is no override flag.
* **It will not overwrite a stored evaluation.** Corrections create new records.
* **It will not treat a stale observation as current.** It becomes `UNKNOWN`.
* **It will not certify a run whose provenance is missing** — the run is scored,
  but `PROVENANCE_MISSING_FOR_FIELDS` is recorded and the record says so.
* **It will not fetch data.** Extraction is upstream and out of the scoring path;
  the engine never makes a network call.

---

## 10. Reference

| Document | Purpose |
| --- | --- |
| `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` | Governing specification (highest precedence) |
| `handoff/authoritative/IPO_Screening_Engine_Technical_Design_v1.5.md` | Component design |
| `docs/TRACEABILITY_MATRIX.md` | Requirement → code → test, plus divergences and open ambiguities |
| `docs/FINAL_REPORT.md` | Implementation summary, results, residual issues (sections A–I) |
| `config/ipo-config.v1.5.0.json` | The executable policy |
| `schema/ipo-input.v1.5.schema.json` | The input contract |
| `fixtures/vishal_nirmiti/` | Golden case: input, expected outputs, RHP provenance |
| `engine/tools/ipo_screen.py` | The CLI implemented above |

---

## 11. Phase 6A Post-Listing Outcome Ingestion

Phase 6A provides an immutable post-listing observation model and deterministic return engine. It links realized post-listing price outcomes to existing immutable `FINAL` evaluations without modifying pre-listing records.

### 11.1 Post-Listing Ingestion Workflow

To ingest historical Bhavcopy prices and record 1W, 1M, and 6M observations:

```bash
python3 engine/tools/ipo_screen.py post-listing ingest \
    --evaluation-id <FINAL_EVALUATION_ID> \
    --prices <BHAVCOPY_OR_PRICE_FILE> \
    --store build/evaluations \
    [-v]
```

Optional arguments:
* `--corporate-actions <FILE>`: JSON contract supplying adjustment factors for splits, bonuses, or rights issues.
* `--reason <STRING>`: Restatement reason when superseding a prior observation.

### 11.2 Storage Structure & Invariants

Observations are saved as linked child artifacts under:
```
<store>/<final-evaluation-id>/observations/
    ├── observation_1w.json
    ├── observation_1m.json
    ├── observation_6m.json
    └── manifest.json
```

* **Parent Immutability**: `evaluation.json`, `result.json`, `input.json`, and parent `manifest.json` are never modified or overwritten.
* **Evaluation Status Gate**: Storage refuses attachment if the parent evaluation is not `FINAL` or if `result_hash` mismatches.
* **Trading Calendar Clamping**: Horizons 1W (7d), 1M (30d), and 6M (180d) automatically clamp non-trading days (weekends, exchange holidays) to the latest preceding valid trading day.
* **Fail-Closed Arithmetic**: Missing benchmark data yields `None` (UNKNOWN) for benchmark and excess returns, never defaulting to zero.
* **Deterministic Hashing**: Every observation artifact computes and records a SHA-256 hash over its canonical inputs and results.

---

## 12. Phase 6B Multi-IPO Historical Outcome Dataset & Assembly

Phase 6B provides the deterministic dataset assembly and audit verification foundation required for downstream backtesting (Phase 6C). It joins immutable pre-listing screening evaluations with post-listing realized outcome observations without recalculating historical scores or mutating evaluation artifacts.

### 12.1 Dataset Assembly Workflow

To assemble a multi-IPO historical outcome dataset from a store of evaluations:

```bash
python3 engine/tools/ipo_screen.py post-listing dataset \
    --store build/evaluations \
    --output build/backtest_dataset.json \
    [--csv build/backtest_dataset.csv] \
    [--strict] \
    [-v]
```

### 12.2 Dataset Verification Workflow

To audit and verify the cryptographic integrity, schema, and store linkage of a generated dataset:

```bash
python3 engine/tools/ipo_screen.py post-listing verify-dataset \
    --dataset build/backtest_dataset.json \
    [--store build/evaluations] \
    [-v]
```

### 12.3 Status & Inclusion Semantics

Each row in the dataset is classified deterministically:
* `READY`: All three observation horizons (1W, 1M, 6M) are present and verified.
* `PARTIAL`: At least one horizon is present and verified (e.g. 1W/1M available while 6M is pending).
* `INCOMPLETE`: Evaluation exists, but no post-listing observations are available yet.
* `UNVERIFIED`: An observation has unverified corporate actions or unconfirmed adjustments.
* `INVALID`: Broken linkage, parent result hash mismatch, or corrupted observation hash.

Newer IPOs are never discarded merely because 6M is pending; they enter as `PARTIAL` with unavailable horizons set to `None` (`UNKNOWN`).

### 12.4 Restatement & Versioning Rule

When multiple versions of an observation exist for the same evaluation and horizon:
* The latest valid superseding version (`supersedes_observation_id`) is selected as the effective observation.
* Historical superseded versions remain preserved on disk.
* Unlinked conflicting versions trigger an `INVALID` classification or fail closed under `--strict`.

### 12.5 Deterministic Ordering & Dataset Hash

* **Ordering**: Rows are sorted strictly by `(evaluation_timestamp, ipo_id, final_evaluation_id)`.
* **Dataset Hash**: SHA-256 computed over the canonical JSON representation of sorted rows, ensuring byte-identical reproducibility independent of filesystem traversal order or generation wall clock.
* **Scope Firewall**: Statistical calibration, Spearman IC, decile ranking, regression, and scoring changes are strictly out of scope for Phase 6B and deferred to Phase 6C/6D.

---

## 13. Phase 6C Historical Backtest Analytics & Statistical Diagnostics

Phase 6C provides the deterministic analytical diagnostics engine that consumes the Phase 6B historical outcome dataset and produces point-in-time safe, reproducible backtest analytics. It adheres strictly to the Phase 6D scope firewall: generates statistical evidence only without rescoring historical IPOs, tuning weights, or modifying screening configurations.

### 13.1 Analysis Execution Workflow

To run comprehensive historical backtest diagnostics over a Phase 6B canonical dataset:

```bash
python3 engine/tools/ipo_screen.py post-listing analyze \
    --dataset build/backtest_dataset.json \
    --output build/backtest_analysis.json \
    [--csv build/backtest_analysis_summary.csv] \
    [-v]
```

### 13.2 Analysis Verification Workflow

To audit and cryptographically verify the canonical integrity and dataset linkage of an analytical artifact:

```bash
python3 engine/tools/ipo_screen.py post-listing verify-analysis \
    --analysis build/backtest_analysis.json \
    [--dataset build/backtest_dataset.json] \
    [-v]
```

### 13.3 Diagnostic Capabilities & Statistical Methodology

1. **Sample-Size Maturity Classification**:
   * `N < 30`: `DESCRIPTIVE_ONLY` (insufficient statistical power for definitive inference).
   * `30 <= N < 100`: `EXPLORATORY` (preliminary directional signals, requires cautious interpretation).
   * `N >= 100`: `STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS` (sufficient sample maturity for diagnostic evaluation).

2. **Descriptive Statistics**:
   * Computes sample size ($N$), arithmetic mean, median, min, max, sample standard deviation ($N-1$ Bessel-corrected), and quartiles (Q1, Q3).
   * Records directional count breakdowns (positive, negative, zero) and positive rate percentages.
   * Reports benchmark and excess return statistics preserving `UNKNOWN` semantics (never defaulting missing values to zero).

3. **Spearman Rank Correlation & Rank Information Coefficient (IC)**:
   * Predictors: `final_score`, `module_a_score` through `module_f_score`.
   * Realized Outcomes: 1W return, 1M return, 6M return, excess returns vs NIFTY 50 TRI, and listing day gain.
   * Method: Exact Pearson correlation on fractional (average) ranks to handle ties without bias.
   * Degeneracy Handling: Constant/zero-variance inputs return correlation `0.0` with status `UNDEFINED_ZERO_VARIANCE`. Sample size $N < 3$ returns status `INSUFFICIENT_DATA`.
   * Rank-IC: Documented method `SPEARMAN_RANK_CORRELATION`, tie policy `AVERAGE_RANK`, missing value policy `PAIRWISE_EXCLUDE`.

4. **Decile & Quintile Bucket Analysis**:
   * Evaluates realized outcomes across 10 deciles and 5 quintiles of pre-listing screening scores.
   * Deterministic Tie Policy: Sorts by `(final_score, evaluation_timestamp, ipo_id)`.
   * Small Sample Fallback: If eligible observations $N < K$ (where $K=10$ for deciles or $K=5$ for quintiles), status is marked `INSUFFICIENT_DATA` and empty buckets are emitted (never artificially synthesizing buckets from fewer observations).

5. **Hit-Rate Diagnostics**:
   * Measures win-rate (positive absolute return and positive excess return) across 1W, 1M, and 6M horizons.
   * Breaks down hit-rates by authoritative verdict classes (`APPLY`, `WATCH`, `AVOID`, `INSUFFICIENT_DATA`).

6. **Module-Level & Temporal Diagnostics**:
   * Module Diagnostics: Independently evaluates the predictive relationship of each Module A-F against 1W, 1M, and 6M outcomes.
   * Temporal Vintage Analysis: Groups outcome and screening statistics by evaluation calendar year (vintage).
   * Temporal Holdout Diagnostic: Partitions earlier vintages as development and the latest vintage as holdout when $N \ge 30$ and $\ge 2$ vintages exist; emits `INSUFFICIENT_DATA` if coverage is inadequate.

7. **Point-in-Time Safety & Leakage Audit**:
   * 8-check deterministic audit verifying that evaluation timestamps strictly precede or coincide with listing dates, no future fields are leaked into screening predictors, evaluation linkages are intact, and observation hashes are valid.
   * If any check fails, the audit status is marked `FAIL` and analytical acceptance is blocked.

8. **Deterministic Content Hashing**:
   * Analytical manifest computes SHA-256 over the canonical JSON of the analytical results, excluding ephemeral execution wall-clock timestamps.

---

## 14. Phase 6D Governed Calibration Proposal & Shadow Evaluation Operations

Phase 6D provides the governed calibration proposal engine that consumes Phase 6B historical datasets and Phase 6C backtest analytics to formulate auditable, point-in-time safe calibration proposals and optional inactive v1.6 configuration drafts.

### 14.1 Fundamental Governance Invariant

```
EVIDENCE -> PROPOSAL != APPROVAL != IMPLEMENTATION != ACTIVATION
```

* **No Automatic Policy Mutation**: Phase 6D never modifies active screening configs, weights, formulas, or verdict thresholds.
* **Ramki Approval Boundary**: The Program Authority is Ramki. Any activation or promotion to production requires separate, explicit authorization from Ramki.
* **Active Config Invariant**: `config/ipo-config.v1.5.0.json` remains authoritative and unchanged.

### 14.2 Calibration Proposal Generation Workflow

To generate a governed calibration proposal from historical datasets and analytical diagnostics:

```bash
python3 engine/tools/ipo_screen.py post-listing calibrate-propose \
    --dataset build/backtest_dataset.json \
    --analysis build/backtest_analysis.json \
    --config config/ipo-config.v1.5.0.json \
    --output build/calibration_proposal.json \
    [--draft-config build/ipo-config.v1.6.0-draft.json] \
    [--objective BALANCED_DIAGNOSTIC] \
    [-v]
```

### 14.3 Proposal Verification Workflow

To audit and cryptographically verify the canonical integrity and linkage of a calibration proposal:

```bash
python3 engine/tools/ipo_screen.py post-listing verify-proposal \
    --proposal build/calibration_proposal.json \
    [--analysis build/backtest_analysis.json] \
    [--dataset build/backtest_dataset.json] \
    [--config config/ipo-config.v1.5.0.json] \
    [-v]
```

### 14.4 In-Memory Shadow Evaluation Workflow

To execute an in-memory shadow rescoring comparison between active v1.5 and a candidate proposal without mutating stored evaluations:

```bash
python3 engine/tools/ipo_screen.py post-listing shadow-evaluate \
    --proposal build/calibration_proposal.json \
    --dataset build/backtest_dataset.json \
    [--config config/ipo-config.v1.5.0.json] \
    [--output build/shadow_evaluation.json] \
    [-v]
```

### 14.5 Calibration Maturity Gates

Proposals are classified strictly according to sample size, temporal vintage coverage, and integrity:

1. `CALIBRATION_INELIGIBLE`:
   * $N < 30$ valid samples, leakage audit failure, or broken cryptographic linkages.
   * Prohibits calibration proposal generation; baseline v1.5 configuration remains unchanged.

2. `CALIBRATION_EXPLORATORY`:
   * $30 \le N < 100$, or $< 3$ historical vintages.
   * Research-only exploration; strictly prohibited from generating a v1.6 draft config or being submitted for production governance review.

3. `CALIBRATION_CANDIDATE`:
   * $N \ge 100$, $\ge 3$ distinct historical vintages, verified chronological development/holdout partition, and passed leakage audit.
   * Eligible to generate an inactive v1.6 configuration draft (`1.6.0-draft`, `DRAFT_INACTIVE`).

4. `CALIBRATION_READY_FOR_HUMAN_REVIEW`:
   * High-confidence candidate proposals where all non-regression checks pass and holdout evidence confirms stability. Submitted to Ramki for human governance review with status `PENDING_HUMAN_REVIEW`.

### 14.6 Overfitting Safeguards

* **Overfitting Safeguards**:
* **Development vs. Holdout Separation**: Candidates are formed exclusively on historical development partitions. Holdout partitions are evaluated strictly out-of-sample; tuning on holdout data is prohibited.
* **Holdout Degradation Rejection**: If a candidate improves development metrics but materially degrades holdout performance, it is automatically rejected and logged in `rejected_candidates`.
* **Knockout Firewall**: `knockout_proposals` strictly defaults to empty. Any alteration to knockout logic requires separate, explicit evidence and is flagged `REQUIRES_EXPLICIT_GOVERNANCE_REVIEW`.

---

## 15. Phase 7: Authorized v1.6 Implementation & Promotion Preparation

Phase 7 establishes the controlled, authorized implementation of the Phase 6D calibration proposal approved by Program Authority Ramki into a production-candidate configuration (`config/ipo-config.v1.6.0.json`).

```
+---------------------------------------------------------------------------------------------------+
|                                  PHASE 7 GOVERNANCE LIFECYCLE                                    |
|                                                                                                   |
|  Phase 6D Proposal  -->  Explicit Ramki Approval  -->  v1.6 Implementation  --> Deterministic    |
|  (Empirically gated)     (Durable artifact)            (status: INACTIVE)       Verification      |
|                                                                                        |          |
|                                                                                        v          |
|  Controlled Promotion Readiness  <--  In-Memory Shadow Evaluation  <--  Frozen Core Verification  |
|  (Awaiting explicit activation)       (Zero historical mutation)        (6 files sha256 match)    |
+---------------------------------------------------------------------------------------------------+
```

### 15.1 Configuration Lifecycle State

The repository strictly preserves dual configuration states:
* **Active Baseline**: `config/ipo-config.v1.5.0.json` remains the authoritative production configuration (`is_active: true`, CLI default).
* **Authorized Candidate**: `config/ipo-config.v1.6.0.json` is implemented but marked inactive (`status: IMPLEMENTED_INACTIVE`, `is_active: false`).

### 15.2 Configuration Verification Workflow

To verify that the authorized v1.6 configuration strictly derives from the approved proposal and v1.5 baseline, satisfies all schema constraints, preserves the frozen core, and maintains provenance linkage:

```bash
python3 engine/tools/ipo_screen.py config verify \
    --config config/ipo-config.v1.6.0.json \
    --proposal config/calibration-proposal.v1.6.0.json \
    --baseline config/ipo-config.v1.5.0.json \
    [-o build/v16_verification_report.json] \
    [-v]
```

### 15.3 Configuration Diff Workflow

To inspect the exact machine-readable and human-readable difference between v1.5 baseline and v1.6 candidate:

```bash
python3 engine/tools/ipo_screen.py config diff \
    --baseline config/ipo-config.v1.5.0.json \
    --candidate config/ipo-config.v1.6.0.json \
    [--proposal config/calibration-proposal.v1.6.0.json] \
    [-o build/config_diff.json] \
    [-v]
```

**Approved Diff Summary**:
* `modules.A.max`: 25 -> 30 (+5 points reflecting stronger development rank correlation).
* `modules.B.max`: 20 -> 15 (-5 points reflecting weaker development rank correlation).
* Modules C, D, E, F: Unchanged (15, 15, 15, 10). Total = 100.0.
* Thresholds & Verdict Bands: Unchanged.
* Knockouts: Unchanged (zero mutations).
* 15 Core Sections Unchanged: `currency`, `units`, `modes`, `profile_resolution`, `sector_overlays`, `structure_overlays`, `knockouts`, `penalties`, `caps`, `confidence`, `critical_data`, `validation`, `gcp`, `derived_metrics`, `peer_status`.

### 15.4 v1.5 vs v1.6 Shadow Evaluation Workflow

To run a comparative shadow rescoring of historical IPO evaluations under v1.6 against the active v1.5 baseline without mutating any stored records:

```bash
python3 engine/tools/ipo_screen.py post-listing shadow-evaluate \
    --config-v1-5 config/ipo-config.v1.5.0.json \
    --config-v1-6 config/ipo-config.v1.6.0.json \
    --dataset build/backtest_dataset.json \
    [-o build/v16_shadow_report.json] \
    [-v]
```

### 15.5 Promotion Readiness Checklist

Before activating v1.6 as the production baseline in a subsequent phase:
1. [x] Phase 6D Proposal explicitly approved by Program Authority Ramki.
2. [x] Durable approved proposal saved at `config/calibration-proposal.v1.6.0.json`.
3. [x] v1.6 configuration implemented at `config/ipo-config.v1.6.0.json` with status `IMPLEMENTED_INACTIVE`.
4. [x] Frozen Core files verified bit-for-bit identical (6 files SHA-256 matched).
5. [x] Golden Result hash verified identical (`e84f8bc0...`).
6. [x] CLI `config verify` passes with exit code 0.
7. [x] Comparative shadow evaluation confirms downside protection and holdout stability.
8. [x] Comprehensive test suite passes (575 passed, 0 failures, 0 regressions).
9. [ ] Explicit activation authorization from Ramki (Phase 8 promotion gate).

---

## 16. CFO/PAT Cross-Platform Determinism Verification

### 16.1 Overview

A cross-platform floating-point summation defect was detected during Windows verification of Phase 7, where binary float non-associativity in Python's native summation caused `derived_metrics.metrics.cfo_pat_cumulative.value` to evaluate to `1.7881897553619623` on Windows vs the expected `1.7881897553619628` (a 1-ULP drift).

The engine was repaired in `engine/ipo_screening/derived.py:_cfo_pat_cumulative` by utilizing exact Decimal summation across observations prior to float conversion:
```python
total_cfo = sum((Decimal(str(v)) for v in cfo_values), Decimal("0"))
total_pat = sum((Decimal(str(v)) for v in pat_values), Decimal("0"))
ratio = float(total_cfo) / float(total_pat)
```
This guarantees identical 64-bit IEEE-754 quotients (`0x1.c9c6cdc652662p+0`) across all operating systems (Linux, Windows, macOS) and period sequence permutations, while strictly preserving the normative mathematical formula: $\text{cumulative ratio} = \sum \text{CFO} / \sum \text{PAT}$.

### 16.2 Verification Commands

To verify determinism and golden result preservation on any platform:

```bash
# 1. Verify golden regression and result hash
python3 -m pytest -v tests/test_vishal_golden.py

# 2. Verify CFO/PAT determinism suite (formula, order invariance, fail-closed)
python3 -m pytest -v tests/test_cfo_pat_determinism.py

# 3. Verify Frozen Core and v1.6 configuration integrity
python3 -m pytest -v tests/test_v16_implementation.py
```






