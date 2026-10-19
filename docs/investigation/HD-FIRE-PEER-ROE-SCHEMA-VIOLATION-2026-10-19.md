# HD Fire Protect peer-ROE schema violation — bounded root-cause investigation and correction (2026-10-19)

**Audit trace:** `ing-81fd285e5b8248c6` (operator's Windows store). **Observed:** `PROCESSING_FAILED`
with `SCHEMA_VIOLATION at peers/0/roe_pct: 26957.28 is greater than maximum 10000` and
`peers/1/roe_pct: 21700.34 …`. Manual issue-term interface also recorded
`issue.ofs: entered 71231 vs existing 0` (source: filing extraction); the operator confirmed the
conflict resolution. **Branch:** `arena/d15866b5-ipo-screening-engine` (base `176c3b6afea1863a3fc4ea2449dc87bd9ba34239`).

## Phase 1 — trace of the failed run

**Located:** the failed run's store artifacts (canonical input, peer rows, evidence, activity) live
in the operator's Windows store; Arena cannot read that machine. The workspace session restore
also dropped ignored paths (`build/`, `.cache/` — see the `.gitignore` NOTE), so no local copy
survives. Retrieval commands for the operator are in §Retrieval/acceptance below. The failure's
stage, mechanism and error format were reproduced and verified in-repo (Phase 2).

**Value provenance chain (verified in code — no scaling exists in the path):** raw table cell →
tokenizer (`float(t.replace(",", ""))`; non-numeric tokens **dropped**) → `roe_pct = nums[5]`
positional (`sections.py::extract_peers`) → canonical `peers[].roe_pct` → passed through
`connectors/adapters.py::_safe_float` and `snapshots.py::_num` unchanged → first schema bound at
`pipeline.evaluate()` step 1. Comma-grouped cells ("26,957.28") parse to `26957.28` exactly.
**Therefore "percentage/fraction scaling" and "unit conversion" are eliminated as causes** for the
extraction path: the stored value equals the raw cell.

**Cause class (established by reproduction on the repository's own reference filings — NOT from
magnitude alone):**
1. **Wrong financial field mapping — hard-coded layout.** `extract_peers` mapped cells by the
   R.K Fashion "Comparison of Accounting Ratios" layout only
   ([FV, CMP, EPS, Diluted EPS, P/E, RONW, NAV, PAT]; pinned by
   `test_rk_fashion_reconciliation.py`: Banaras Beads pe 44.31 / roe_pct 3.08 / pb 1.36). Replaying
   the Vishal Nirmiti listed-peers table ([Closing price, FV, Revenue, EPS Basic, EPS Diluted,
   P/E, Net worth, RONW, NAV]) through those positions produced `roe_pct = 13.86` — the **P/E
   cell** — and `pb = 0.0` (a garbage "peer" with a 115-word narrative name was emitted in
   real-filing extraction). Demonstrated, not hypothesised.
2. **Placeholder-collapse column shift.** Non-numeric cells (`[●]`, `-`, `NA`) were dropped from
   the row, shifting every later column left: the R.K issuer-shaped row
   `10.00 [●] 6.50 6.50 [●] 40.66 15.99 182.86` mapped `roe_pct = 182.86` (PAT) and
   `nav = None` instead of RoNW 40.66. Demonstrated.
3. With (1)+(2), a monetary or NAV cell lands in `roe_pct` — the exact signature of the reported
   `26957.28` / `21700.34` (2dp, comma-groupable monetary-scale cells, two peers of one table).
   **Which of (1), (2), or "genuinely extreme source RoNW" applies to the HD Fire rows
   specifically is unresolved from Arena** — it requires the raw rows (see §Retrieval). The
   magnitude alone cannot decide (directive honoured).

**Not causes:** the schema bound itself (10000 is the frozen `#/$defs/pct` maximum, shared by
`roe_pct`/`roa_pct`/`growth_pct` and `periods[].roe_pct`); the scoring engine (never reached);
the issue-term/OFs workstream (independent — see Phase 4).

## Phase 2 — contracts, transformations, and why it failed only at evaluation time

- **Contract:** `schema/ipo-input.v1.5.schema.json` `properties/peers/items` →
  `roe_pct: $ref #/$defs/pct` = `{"type": ["number","null"], "minimum": -1000, "maximum": 10000}`.
  Golden peers carry ordinary percents (18.25, 9.51; R.K: 3.08) — the unit is percent.
- **Extraction-time validation is a no-op in this flow:** `CanonicalInputBuilder.validate()`
  (`extraction/builder.py:118`) returns True without checking anything whenever
  `issue.price_band_low is None` (the deliberate pre-enrichment skip) — and the service's
  `ingest_document` never calls it. The **first full schema enforcement** is
  `pipeline.evaluate()` step 1 (`enforce_schema(input_document, schema)`,
  `pipeline.py:276`). That is why 26957.28 passed upstream and detonated at evaluation time as
  the anonymous wall `SCHEMA_VIOLATION at peers/0/roe_pct: …` (format: `errors.py::ValidationError`
  preview, `code at location: message`).
- **Normalization layers do not bound:** `connectors/adapters.py::_safe_float`,
  `snapshots.py::_num` pass values through; `classify_peers` statuses (VALID/REJECTED) operate
  after the schema gate and cannot rescue an out-of-contract value.
- **Source precedence:** `extraction/builder.py:55-57` — `base.get("peers")` (reference/golden
  base) wins over extracted `peers`.
- **Existing tests/fixtures:** `test_rk_fashion_reconciliation.py` (real-table pins),
  `fixtures/vishal_nirmiti/input.json` golden peers (PEER-SCREENER 18.25/9.51),
  `test_connectors.py` (KNR/PNC normalization). No test pinned the positional garbage — the
  Vishal real-filing garbage peer was schema-valid (in-bounds wrong data) and invisible.

## Phase 3 — corrections (narrow; no clamping, no rewriting, no relaxation)

| File | Fix |
|---|---|
| `engine/ipo_screening/extraction/sections.py` | `extract_peers`: cells are mapped ONLY against a recognised header layout (two evidence-anchored signatures: R.K accounting-ratios; Vishal listed-peers) with placeholder-preserving cell alignment and strict row width; leading row-serial tolerance; prose names (>10 words / total/average/highest/lowest) are not peers; **an unrecognised layout emits no peers** (module B stays UNKNOWN — "evidence discovered but not parsed") instead of wrong-field values. |
| `engine/ipo_screening/schema_validation.py` | New `validate_peer_records()`: the SAME schema definition over the `peers` array, findings naming the peer and field (`peers/i/roe_pct`, `peer 'Name' …`). |
| `engine/ipo_screening/presentation/service.py` | `ingest_document`: at ingestion time (right after extraction, before any term work) the peers array is validated; violations raise `IngestionValidationError` (400) with the named diagnostic + `validation/peer_contract` FAILED audit event: "Raw values are never clamped or substituted; correct the peer source data and re-upload the filing." |

Untouched: schema bounds, scoring formulas/weights/thresholds/knockouts, golden fixtures, frozen
core, provenance semantics, fail-closed governance (each corrected path is either source-true
values or an honest governed UNKNOWN).

**Verification of the correction on reference documents (executed):** R.K Fashion extraction is
byte-identical to its pins (Banaras 44.31/3.08/1.36). Vishal real-filing peer extraction now
agrees exactly with the golden peer values (GPT Infraprojects pe 14.83 / pb 2.73 / roe_pct 18.25;
Indian Hume Pipe pe 13.86 / pb 1.32 / roe_pct 9.51 — previously pe 26.79 / roe_pct 13.86 /
pb 0.0 garbage). Jio peers unchanged (none).

## Phase 4 — issue-term governance (the OFS conflict; independent of the peer failure)

Verified and pinned (`test_confirmed_ofs_override_stays_manual_entry_and_unverified`): the filing
extracted `issue.ofs = 0` (NIL-OFS); the operator entered **71231**. The conflict is surfaced
(409 `ISSUE_TERM_CONFLICT`, `existing_value 0.0`, `existing_origin FILING_EXTRACTION`,
`manual_value 71231.0`) and requires explicit confirmation; on confirmation the manual value
applies to the canonical input, every one of the five terms carries `MANUAL_ENTRY` /
`SRC-MANUAL-ENTRY` / `verified:false` with the operator explanation, `overridden_by_verified`
is empty (confirmation never implies official verification), and the audit trace records
`manual_submission → manual_entry → evaluation/completed → persistence/completed` with
`values.ofs == 71231.0`. All five mandatory terms and their reporting-unit labelling are covered
by the established five-field suite (87 frontend / five-field backend batteries re-run green).

## Phase 5 — regression tests and re-execution

New `tests/test_peer_row_mapping_and_bounds.py` (**11 tests**):
- both reported values (26957.28 / 21700.34) rejected with peer-and-field-named diagnostics;
- cause-level retry: those same magnitudes as NET-WORTH cells of the listed-peers layout map to
  their own column; `roe_pct` takes the RONW column (12.40 / 8.90) and the rows are contract-valid;
- valid in-bound (18.25/9.51), extreme in-bound (9999.9, −999.0, 10000.0, −1000.0, null) accepted
  untouched; invalid (10000.01, −1000.01, numeric string) rejected;
- layout pins for both reference shapes (R.K 44.31/3.08/1.36; Vishal 14.83/18.25/2.73 and
  13.86/9.51/1.32 — golden agreement);
- placeholder cells keep their column ([●] P/E stays unknown; RoNW stays RoNW);
- unrecognised layout emits no peers; prose rows are not peers;
- service-level early rejection (400, named, nothing evaluated/persisted) and a valid-peers flow
  completing normally;
- the Phase-4 OFS conflict/confirmation governance chain end to end.

**Executed:** `pytest tests/test_peer_row_mapping_and_bounds.py -q` → **11 passed**.
`pytest tests/test_rk_fashion_reconciliation.py tests/test_extraction.py tests/test_vishal_golden.py -q`
→ 36 passed (R.K/Vishal/GOLDEN pins byte-identical). Four-field/fresh-issue/audit/step5/ui7 batch
→ 78 passed. Jio/discovery/financial-mapping/core-semantics/connectors batch → 89 passed.
Full backend `pytest tests/ -q` → **1111 passed**, exit 0. `cd frontend && npm test` → **87 passed**.

**Re-execution of the affected ingestion:** through the supported workflow, re-uploading the HD
Fire filing now re-extracts with the corrected mapping. Outcome is governed either way:
(cause was column misalignment) → peers carry source-true values and the evaluation completes and
persists; (source cells genuinely out of contract) → the upload is rejected early with the
peer-and-field-named diagnostic and nothing is silently changed. The real-file retry is a Windows
acceptance step (Arena has neither the filing nor the store); commands below.

## Retrieval / acceptance (Windows, PowerShell)

```powershell
cd C:\path\to\ipo-screening-engine
# 1) Locate the failed run and its raw peer rows/evidence (names + source cells):
$id = "ing-81fd285e5b8248c6"
$ing = Get-ChildItem -Recurse -Directory -Filter $id .\build,.\ingestions -ErrorAction SilentlyContinue | Select-Object -First 1
Get-Content (Join-Path $ing.FullName "input.json") | ConvertFrom-Json |
  Select-Object -ExpandProperty peers | Format-List name,pe,pb,roe_pct
(Get-Content (Join-Path $ing.FullName "input.json") | ConvertFrom-Json)._evidence.peers
Get-Content (Join-Path $ing.FullName "activity.jsonl") | Select-String "SCHEMA_VIOLATION|conflict|ofs"
# 2) Update to the fix and retry through the supported workflow:
git fetch origin "refs/heads/arena/d15866b5-ipo-screening-engine:refs/remotes/origin/arena/d15866b5-ipo-screening-engine"
git checkout arena/d15866b5-ipo-screening-engine; git pull origin arena/d15866b5-ipo-screening-engine
git rev-parse HEAD    # expect the publication-amendment SHA in the tracker
$env:PYTHONPATH = "$PWD\engine"
.\.venv\Scripts\python -m uvicorn ipo_screening.presentation.api:app --host 127.0.0.1 --port 8000
```
Then hard-refresh `/ui/` and re-upload the HD Fire filing. Verify one of the two governed
outcomes (evaluation completes + persists with provenance, or the named peer diagnostic), and that
the confirmed OFS (71231) is recorded as MANUAL_ENTRY/UNVERIFIED on the new record.

## Status

- Confirmed defects corrected: layout-blind positional mapping; placeholder-collapse; prose-name
  peers; late anonymous bounds failure. Hypotheses rejected: scaling/unit conversion (no such
  code path); scoring/contract-bound error; OFs coupling. Unresolved: the raw-cell classification
  of the two HD Fire values (needs the store/filing — commands above).
- Published on `arena/d15866b5-ipo-screening-engine` (commit/remote/PR status in the tracker
  publication amendment). PR #6 lifecycle preserved; `main` untouched.
