# Test-suite performance investigation — 2026-10-25 (Arena)

## Environment and starting point

- Repository: `ramkivs/ipo-screening-engine`.
- Active branch: `arena/cf756dd1-ipo-screening-engine`.
- `git fetch origin main` confirmed clean starting HEAD and remote main both at
  `dedb4b876cdc68bdf3023d9740dc13f6888b45b3`. No branch switch was made.
- Python 3.11, local `.venv`, dependencies installed from `requirements.txt`.
  Initial environment lacked pytest; dependency installation is not included in
  test timings. All validation ran in Arena, not a Windows-local checkout.
- Inspected README, RUNBOOK, A9 workflow, conftest, progress plugin, and the
  PDF/ingestion test inventory (55 existing modules, including synthetic ones).
  Audited reader mutation/patching in the eight opt-in modules specifically.

## Measured baseline and optimized full regression

Commands are in [TEST_PERFORMANCE.md](TEST_PERFORMANCE.md). Full runs used the
unfiltered `PYTHONPATH=engine python -m pytest tests/ -q --durations=30`.
The baseline collected the original tests before test-code edits. The two full
runs executed sequentially; no other full/integration workload ran concurrently.
Lightweight inspection, documentation and brief targeted checks took place
while full runs were active. These are practical Arena wall measurements, not
controlled dedicated-host benchmarks.

| Measurement | Baseline | Optimized |
|---|---:|---:|
| Backend collected | 1,908 | 1,914 |
| Backend passed | 1,908 | 1,914 |
| Backend failed / skipped / deselected | 0 / 0 / 0 | 0 / 0 / 0 |
| Backend warnings | 25 | 25 |
| Backend pytest elapsed | 1,970.48 s | 988.74 s |
| Backend shell wall (`time`) | 1,972.110 s (32m52.110s) | 990.112 s (16m30.112s) |
| Pass-9 collected / passed | 88 / 88 | 88 / 88 |
| Pass-9 failed / skipped / deselected | 0 / 0 / 0 | 0 / 0 / 0 |
| Pass-9 warnings | 1 | 1 |
| Pass-9 pytest elapsed | 1.66 s | 1.10 s |

Full-suite wall reduction: **981.998 seconds (16m21.998s), 49.79%, 1.99× faster**.
These are single-run observations, not a statistical benchmark; CPU/filesystem
variation contributes to differences. The original full-suite count did not
fall: six new tests account for the increase. The full optimized cache reported
**13,585 hits / 1,596 decoded pages / 1,596 retained immutable strings**.

The warnings were not suppressed: one Starlette/httpx test-client deprecation
and 24 existing deprecated HTTP-422 constant warnings. Pass-9 has the former.

## Root causes and retained slow boundaries

The extractor already shares a text dictionary between section and financial
extractors **within one call**, but fresh readers in separate tests/uploads
repeat pypdf text decoding. Multiple full ingestions repeat that work even when
the changing behavior is manual terms, conflict governance or evidence
registration. TOC reads also bypass the extraction-local text dictionary.

Baseline slow calls included:

| Test boundary | Baseline call | Optimized call |
|---|---:|---:|
| Evidence-fix re-upload regression | 128.27 s | 80.08 s |
| Vishal three terms still awaiting OFS | 92.42 s | Below optimized slowest-30 cutoff (4.00 s) |
| Manual entry cannot displace official verification | 92.13 s | Below optimized slowest-30 cutoff (4.00 s) |
| Verified notice reaches Evidence API | 88.28 s | 39.39 s |
| UI7 official notice auto-resolution | 88.26 s | Below optimized slowest-30 cutoff (4.00 s) |
| CLI real extraction subprocess | 34.96 s | 35.27 s |

The re-upload regression intentionally restores monkeypatches before subsequent
uploads; those later uploads remain uncached. The CLI runs in a new process and
is not accelerated by a process-local pytest cache. Paras's module upload
fixture remains uncached (55.02 s baseline setup / 51.87 s optimized setup).

Repeated canonical building and complete API workflows were reviewed but not
memoized: retaining fresh provenance/timestamps, domain extraction, schema
validation, evaluation and persistence is safer than sharing mutable prepared
canonical results or service state. No duplicate assertion was removed.

## Exact changes and coverage accounting

- Added process-local immutable page-text cache plus an explicit function-scoped
  fixture; enabled it in eight named modules only (listed in the design doc).
- Keyed reuse by full PDF content hash and page object identity; fresh readers
  remain fresh. All non-default extraction arguments/visitors bypass reuse and
  exceptions are not cached. No production cache or production code changes.
- Added a terminal cache hit/miss summary and an uncached-control environment
  switch, `PYTEST_PDF_TEXT_CACHE=0`.
- Added conservative integration inventory, mutually exclusive `fast` and
  `integration` classifications, and expanded `slow` to alias integration.
  No default test deselection. Mixed modules remain entirely integration.
- Added five cache isolation checks (including real tiny-PDF reader seam) and one
  inventory completeness check. **Removed: 0. Consolidated: 0.**
- AST comparison against starting HEAD confirmed every existing top-level
  function/class body in the eight modified test modules is unchanged
  (102 top-level test functions; parametrization also unchanged).
- Updated README/RUNBOOK and added tier design and this results report. Existing
  A9 full regression job, dispatch choice, and failure propagation unchanged;
  finalization adds the PR trigger described below.

Uncached real-file coverage remains for Vishal, R.K., Jio, and Paras. Existing
manual-term, discovered-prospectus and R.K. ingestion canaries retain the
PDF → extraction → canonical → issue terms → evaluation → persistence path.
Paras's existing hash-checked evidence regression intentionally stops at its
parser/upload boundary; this change does not invent an official evaluation.
Provenance, fail-closed, security, idempotency, re-upload, parser-mutation,
fallback-isolation and Windows-path assertions remain intact.

## Tier measurements and final checks

| Tier/check | Before/control | After | After result |
|---|---:|---:|---|
| Full backend | 32m52.110s shell wall | 16m30.112s shell wall | 1,914 passed; no failures/skips/deselections; 25 warnings |
| Fast backend | 1m17.629s shell wall, cache-disabled control on new tier | 1m20.592s shell wall | 1,037 passed; 877 deliberately deselected; 0 failed/skipped; 1 warning |
| Integration backend | Not independently timed before tiering; included in original full baseline | 15m40.213s shell wall | 877 passed; 1,037 deliberately deselected; 0 failed/skipped; 25 warnings |
| Pass-9 | 1.66s pytest elapsed | 1.10s pytest elapsed | 88 passed; 0 failed/skipped/deselected; 1 warning |
| Frontend | 93 passed; 1.135412s Node elapsed, 3.253s npm shell wall | 93 passed; 0.930932s Node elapsed, 1.224s npm shell wall | 0 failed/skipped; no test warnings |

Fast and integration were also executed **as standalone commands**, not inferred
from the full run. Their pytest elapsed times were 79.53s and 938.78s respectively
(fast cache-disabled control: 76.61s). The cache is not intended to accelerate the
fast tier; its slightly slower second run is ordinary timing variation. The
control has the same 1,037 tests, including the six new checks, and is **not**
misrepresented as the original pre-edit baseline. Tier selections intentionally
exclude the complementary tier; the unfiltered full run excluded nothing.
Standalone integration reproduced the full run's 13,585 hits and 1,596 misses.
The import deprecation warning appears in each independent pytest process, so
separate-tier warning totals are not additive to the single-process full total.

The new tier design gives roughly 80-second backend PR feedback plus frontend
and integrity checks, while retaining an explicit ~16.5-minute full regression
path. Fast alone is not full-suite acceptance.

## Integrity and limitations

Baseline and optimized checks passed for all **4 JSON schemas**,
`verify_frozen_core()`, `verify_golden_result()`,
`verify_v1_6_implementation()`, `python -m compileall -q engine`, and
`git diff --check`. Production engine/config/schema/fixture files are unchanged.

Golden result remains
`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.
v1.6 remains `IMPLEMENTED_INACTIVE`, `is_active: false`; active baseline remains
v1.5.0.

Limitations:

- Cache is explicitly for immutable readers/pages/streams in audited modules;
  do not add PDF mutations to those modules without disabling it or moving the
  test. Its reader digest is calculated once per reader, not after mutations.
- First parses, uncached canaries, subprocesses, and deliberate mutation/cache
  isolation suites remain expensive. There is no persistent/disk cache.
- The test fixture uses pypdf's page/reference seam under the repository's pinned
  pypdf version; review it on dependency upgrades (the tiny real-reader test
  exercises this seam). Cache memory is session-scoped, not shared across workers.
- Tiering is intentionally conservative: some inexpensive synthetic cases stay
  in integration alongside workflows. Full validation still requires both
  tiers (or, preferably for release, the unfiltered full command).
- No xdist, parallel test execution, Windows-local measurement or Windows speedup
  claim. No coverage percentage claim: preservation is demonstrated by retained
  test bodies/assertions, collection accounting and unfiltered passing runs.
- New tiers did not exist at baseline. An independently timed pre-change
  integration-only command was not run; its baseline coverage is included in
  the unfiltered 1,908-test run. No inferred integration wall time is presented
  as an independently measured result.

## Independent finalization verification — 2026-10-25

A fresh verification pass against fetched `origin/main` at
`dedb4b876cdc68bdf3023d9740dc13f6888b45b3` independently audited every original
changed/new file (including the six initially untracked files), rather than
relying only on the earlier report. No unrelated, production, scoring, schema,
golden, fixture or CI change was present in that 17-file audit. Original test
function/class ASTs again matched the baseline: eight modules / 102 top-level
test functions. A separate real tiny-PDF repeated-extraction probe confirmed two
fresh readers, two canonical builds, distinct canonical/report/extraction
objects, and 12 text-cache hits / 4 misses. All seven named uncached boundary
modules were verified not to activate the cache.

| Independently reproduced check | Result |
|---|---|
| Unfiltered backend, `--durations=30` | **1,914 passed**, 0 failed/skipped/deselected, **25 warnings**; pytest **1,002.76 s**, shell wall **1,004.233 s (16m44.233s)** |
| Fast tier, independently rerun | **1,037 passed**, 877 explicitly deselected, 0 failed/skipped, **1 warning**; pytest **75.85 s**, shell wall **76.908 s** |
| Cache accounting | **13,585 hits / 1,596 decoded pages / 1,596 strings**, identical to first optimized run |
| Pass-9 | **88 passed**, 0 failed/skipped/deselected, **1 warning**; pytest **1.29 s**, shell wall **2.284 s** |
| Frontend | **93 passed**, 0 failed/skipped; Node **1.137349414 s**, npm shell wall **1.292 s**; no test warnings |
| Schemas / frozen core / golden / inactive v1.6 | **PASS**, all four schemas and all six pinned core files; same golden hash; `IMPLEMENTED_INACTIVE`, `is_active: false` |
| Compileall / whitespace / protected paths | **PASS**; engine/config/schema/fixtures/CI unchanged in initial audit |

Relative to the original 1,972.110-second baseline, the independently reproduced
full run saves **967.877 seconds (49.08%)**. The original 49.79% observation above
is retained, not replaced or misrepresented as a statistical guarantee. Brief
inspection/targeted probes occurred during this full run; no second long
regression workload ran alongside it. Standalone integration timing above is
the original directly executed run, not a new independently repeated command;
all 877 integration cases ran again in the independent unfiltered regression.

Documentation now explicitly distinguishes normal workflow gates from forced
execution: rejected/awaiting requests still do not evaluate or persist. The
repository's authoritative tracker exists, so reconciliation adds an 18th,
documentation-only path (`handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`)
beyond the audited 17. Historical tracker entries are retained.

## Publication, CI trigger correction and artifacts

- Authoritative remote: `https://github.com/ramkivs/ipo-screening-engine.git`.
  Baseline fetched/verified as `dedb4b876cdc68bdf3023d9740dc13f6888b45b3`.
- Initial implementation/docs/tracker commit:
  `96cd9bd548b24b86caa1f89e2c0ab0a6cf509cd8`, pushed only to the fixed branch
  `arena/cf756dd1-ipo-screening-engine`.
- Published [PR #10](https://github.com/ramkivs/ipo-screening-engine/pull/10)
  against `main`. Direct remote readback at that commit: **OPEN, MERGEABLE,
  mergeStateStatus CLEAN**, 18 changed paths, no checks attached. This is a
  timestamped initial-publication observation, not an assertion that no checks
  can subsequently appear.
- Explicit full dispatch of the existing A9 workflow failed with **HTTP 403,
  Resource not accessible by integration**. The old automatic push trigger only
  covers `arena/07f3439f-ipo-screening-engine`, not this branch. No successful
  remote CI run was inferred from local tests or the absence of checks.
- To obtain applicable full CI without extra approval or permissions, the
  follow-up adds only `pull_request: branches: [main]` to that workflow's event
  configuration. Its complete job, default full selection, manual choices,
  frontend/integrity checks, permissions and failure propagation are unchanged.
  PR events have no push `head_commit.message` linkage marker, so they select
  **full**, not focused linkage. This intentional CI correction is a **19th**
  changed path, beyond the original 17 and tracker reconciliation; no silent
  expansion or accidental CI modification is claimed.
- The PR's **Checks** tab and final verification comment hold remote run URLs,
  exact tested SHA, status/conclusion and final branch/mergeability receipts.
  Those are remote evidence, distinct from the locally reproduced measurements
  above. The final published HEAD is available from PR `headRefOid` / the remote
  branch; a commit cannot embed its own SHA in its tracked contents.
- No merge, release or deployment is implied or performed by publication.
  Production/scoring/schema/golden/fixture paths remain unchanged. Raw local logs
  remain under `/home/user/test-performance/` in Arena, finalization reruns in
  `finalization/`, outside Git; caches and `.venv` remain ignored. Prior local
  baseline/optimized timing records are preserved without rewriting results.

### Complete final changed-path manifest

1. `.github/workflows/a9-contract-regression.yml` — PR trigger only (two lines).
2. `README.md` — tier entry points.
3. `docs/RUNBOOK.md` — operational tier commands.
4. `docs/TEST_PERFORMANCE.md` — design, boundaries, controls, publication links.
5. `docs/TEST_PERFORMANCE_RESULTS.md` — exact benchmark/verification evidence.
6. `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` — bounded reconciliation.
7. `tests/conftest.py` — opt-in fixture, markers, classification, cache summary.
8. `tests/pdf_text_cache.py` — immutable-text-only helper.
9. `tests/test_pdf_text_cache.py` — five isolation checks.
10. `tests/test_suite_tiers.py` — one completeness guard.
11. `tests/tier_inventory.py` — explicit integration inventory.
12. `tests/test_cross_ipo_issue_term_provenance.py` — fixture activation only.
13. `tests/test_derived_evidence_registration.py` — fixture activation/import only.
14. `tests/test_extraction.py` — fixture activation only.
15. `tests/test_official_discovery.py` — fixture activation only.
16. `tests/test_rk_fashion_reconciliation.py` — fixture activation only.
17. `tests/test_rpt_extraction.py` — fixture activation only.
18. `tests/test_step5_auditor_and_manual_terms.py` — fixture activation only.
19. `tests/test_ui7_ingestion.py` — fixture activation only.
