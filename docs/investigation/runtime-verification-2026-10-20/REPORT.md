# Runtime regression evidence convergence — 2026-10-20

## Conclusion

Adequate regression execution evidence exists for the complete current runtime
at `e7b588cffb8a2155c9a0041b2134d34144b371fd`. This does not claim exhaustive
semantic correctness or close the separately documented CARO/external-source
policy gaps. No new full backend run was necessary or performed. No runtime or
test correction was required. Publication changes only evidence and the tracker.

## Tested-tree identity (not inferred from commit messages)

Runtime implementation commit: `41f2f86909fa4495b3c9d735d897c00bb20843b4`.
Its patch changes `engine/ipo_screening/extraction/sections.py`,
`tests/test_litigation_regulatory_defaults.py`, `tests/test_extraction_phase5b.py`:
A24 party coverage and table-row alignment, A25 disclosed-negative semantics,
located/fully-read absence prerequisites and per-page observability are included.

The recovered `/home/user/full_a24.log` is preserved byte-for-byte as
`prior-full-backend.log` (SHA-256 in `tree-identity.json`). Actual output records
1288 collected, 1288 passed, 0 failed/skipped, 25 warnings, 1272.03 seconds,
EXIT=0. No xfail/xpass outcomes are reported. Plugin completion is 1288/1288;
its measured 1269.9 seconds excludes some pytest startup/teardown, so the pytest
1272.03 seconds is the suite duration, not a contradictory measurement.
Warnings: one Starlette/httpx deprecation plus 24 deprecated HTTP-422-constant
warnings. They are preserved, not suppressed or classified as regressions.

Evidence linking the log to the runtime commit is corroborative, not a
cryptographically stamped original-run manifest:

- Git commit/reflog places 41f2f86 at 2026-10-20 16:04:57 UTC; log plugin start
  is 16:05:03. Preserved original file mtime is 16:26:13.997349244 UTC (observed
  completion proxy, not a separately captured original shell end timestamp).
  Original log lacks a timezone/HEAD header; UTC attribution follows the sandbox
  timestamps and contemporaneous record. Do not invent a more precise shell start/end.
- Next commit d1be6d2 is 16:33:55 UTC. Its contemporaneous tracker validation
  entry and RUNBOOK §17.6 explicitly record the A24/A25 tree, command
  `python3 -m pytest tests/ -q`, count and 1272.03-second result.
- Raw log contains the 89-test litigation module and all 1288 completed tests,
  including golden checks. This matches the A24/A25 expanded suite.
- `git diff --name-status 41f2f86 e7b588c` enumerates all intervening paths:
  documentation/decision records, one old test rename/docstring and the new
  audit-test file. No application, dependency, configuration, schema, frontend,
  fixture or source-evidence path changed.
- `tree-identity.json` records equal Git object IDs for engine, frontend, config,
  schema, fixtures, evidence, requirements.txt, test harness and progress plugin.
  Identical tree IDs establish content equivalence, not just similar messages.
- Full-module AST comparison confirms the old litigation test differs only by
  the disclosed-negative function rename and docstring (normalized away).
  No assertion or executable body changed. The other existing tests are unchanged.

Together the actual log, contemporaneous record, chronology and object identity
support reuse of the full result for current runtime. The original log alone
would not prove its checkout SHA; this evidentiary limitation is explicit.

## Current checks and timing

Exact argument arrays, working directories, UTC start/end, wall durations and
exit codes are in `checks.json`; unmodified outputs are adjacent `.log` files.

| Check | Result | UTC start → end | Reported test duration |
| --- | --- | --- | --- |
| Focused backend | 122 passed; 0 failed/skipped/xfail/xpass, no warnings reported | 17:42:14.423558+00:00 → 17:42:15.269449+00:00 | 0.27 s |
| Frontend npm test | 90 passed; 0 fail/cancelled/skipped/todo | 17:42:15.269606+00:00 → 17:42:16.502581+00:00 | 656.435112 ms |
| check-config | valid True; 10 profiles, each 100 points | 17:42:16.502792 → see checks.json | no test duration |

Backend command:

```
python3 -m pytest tests/test_governance_contract_audit.py \
  tests/test_auditor_tenure_defaults.py \
  tests/test_litigation_regulatory_defaults.py \
  tests/test_hd_fire_primary_source_extraction.py -q
```

Frontend: `cd frontend && npm test` (package script `node --test test/*.test.js`).
Config: `python3 engine/tools/ipo_screen.py check-config`.
Collection: `python3 -m pytest tests/ --collect-only -q`: 1305 tests collected
in 0.56 seconds. Collection emits the existing Starlette/httpx warning;
collection is not a full execution result. Total 1305 = prior 1288 + 17 new
checks, all of which were executed in the 122-test focused run.

Progress plugin output at 25/50/75/100/122 is preserved. These checks took seconds;
foreground harness output returns at command completion, so no long silent run
occurred. Initial investigation, tree-equivalence decision and completion were
reported to the user. No substantial suite started in this pass, no stalls,
no redundant full reruns, no failures dismissed and no tests weakened.

## Integrity and residual scope

Golden/config/schema/history protection follows from empty runtime/protected-path
diffs, identical objects and publication restricted to this evidence directory
plus an additive tracker entry. No historic evaluations were regenerated. Raw
logs are small text evidence, not large datasets or newly generated evaluations.

Remaining A26/A27/A8-R policy boundaries are unchanged. Adequate runtime regression
evidence does not mean unimplemented CARO or external corroboration is complete.
No additional regression coverage gap was identified in the intervening changes.
Remote commit/content and PR verification follow push; the completion response
reports actual publication identity. Main and PR #6 are not modified.
