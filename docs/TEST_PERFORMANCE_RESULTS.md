> **Integration closure, revision21 (2026-10-26):** PR #10 merged as`70c5b0facc20f718500bcddc1efaae778ebd78c5`,
> accepted source head9333b1c. Windows gate accepted by user decision: focused
> exit0; initial full1941passed/1CLI subprocess timeout; same test isolated pass
>98.51s. NOT a clean Windows full pass, and no rerun required. Historical OPEN
> statements below are superseded by tracker revision21 and the
> [verified remote closure receipt](https://github.com/ramkivs/ipo-screening-engine/pull/10#issuecomment-6409140261). Closure updates are docs-only;
> existing timing/validation receipts are preserved, not rewritten.

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

### Remotely verified full CI receipt (code/CI head)

- [Run **40194048213**](https://github.com/ramkivs/ipo-screening-engine/actions/runs/40194048213),
  event `pull_request`, head **`3ba28f6f67998cb6c9b6b1abf5f4fcf5b75ee502`**:
  **completed / success**. Job `regression` / check-run **121170970031** ran
  2026-10-25 **12:39:09–12:57:09 UTC** (**18m00s** including setup/teardown).
- Direct API readback of its JUnit notice: **tests 1,914; failures 0; errors 0;
  skipped 0; suite time 1,048.850 s**. This is remote evidence, not the Arena
  benchmark. The unchanged job's full target is `tests/`, with no marker filter.
- Backend, frontend, schema/integrity, compileall and both clean-tree/diff checks
  all returned **success**. The remote frontend step's count was not recovered
  separately; **93 passed** above is the independently reproduced local count.
- Remote check annotations separately report a Node.js 20 action-runtime
  deprecation warning (actions forced to Node.js 24) and an `ubuntu-latest` →
  Ubuntu 26 migration notice. These are runner/action notices, not pytest
  warning counts. The remote pytest warning total was **not independently
  retrieved**; the verified local total remains exactly **25**, unsuppressed.
- Bulk `gh run view --log` retrieval failed with EOF at the redirect to the
  external Actions results host, outside the sandbox's permitted hosts. No log
  contents were fabricated. Completion, every step conclusion, exact JUnit
  counts/time, and annotations were recovered directly through `api.github.com`.
- PR API reported synthetic merge **`3d91b72241c058eb39d185f6cb368bd7391e7eed`**;
  its tree **`33aff794bc804a2fcdefe1a81ce5c7c3889d4ab4`** exactly matches the
  published code/CI head tree. All 19 published file blobs were independently
  matched to the local committed tree through the contents API.
- Direct post-run readback: PR #10 **OPEN, MERGEABLE, CLEAN**, `mergedAt: null`;
  `origin/main` unchanged at the authoritative baseline. Only the fixed Arena
  branch was pushed; no force push, merge, release or deployment.
- This receipt's follow-up changes **only these documentation/tracker paths**:
  `docs/TEST_PERFORMANCE.md`, `docs/TEST_PERFORMANCE_RESULTS.md`, and
  `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`. Test code and the
  workflow are unchanged from the successfully tested code/CI head. The final
  documentation-head SHA and its own completed full-CI run are recorded in the
  PR's final verification comment (not conflated with the code-head run here).

### Optimization-publication changed-path manifest (19 paths at dfa34b2)

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

## Windows failure continuation — 2026-10-25

### Evidence boundary and checkout reconciliation

- Published optimization lineage is preserved: original baseline
  `dedb4b876cdc68bdf3023d9740dc13f6888b45b3`, optimization publication
  `dfa34b26a45b672dc92bcaed337e48f7a2b4ca13`, existing PR #10 **open**.
- At continuation start Arena's actual branch was
  `arena/cf756dd1-ipo-screening-engine`, actual HEAD **dedb4b8**. The remote
  branch was **dfa34b2**. All **19** restored files matched the remote bytes
  exactly: **13 unstaged tracked edits, 6 untracked files, nothing staged**.
  No unrelated edit or harness change existed in Arena. This is a sandbox
  restoration state, not a claim about the user's Windows working tree.
- No reset, clean, force push or file overwrite is used to conceal that state.
  The scoped correction is committed with the published **dfa34b2 as its
  parent**, using the verified final index tree (`write-tree` / `commit-tree`)
  and a compare-and-swap update of the existing branch ref. The final index/tree
  already describes the files on disk; no checkout/reset is needed. Thus all
  published optimization commits remain ancestors and the new commit's diff is
  only the corrections below, not a duplicate optimization patch.
- The user's modified `tests/gmp_mechanics_harness.py` is unavailable in Arena;
  Arena's copy remains byte-identical to the published version. It is neither
  overwritten nor included in the correction. Its Windows edit must be retained.

### User-supplied Windows results (not independently rerun by Arena)

| Windows run | Reported result | What it establishes |
|---|---|---|
| Optimized `dfa34b2`, full | **1,907 passed, 7 failed, 57 warnings, 26m42s** | Seven Windows failures; not a green Windows optimization acceptance |
| Original `dedb4b8`, selected seven | **7 failed**, 1 warning, **103.81s** | Same seven fail on baseline; this was **targeted**, not a full-suite timing baseline |

The user also reported a modified Windows `tests/gmp_mechanics_harness.py`; its
contents and timing relative to the full run are unavailable, so these are not
asserted to be clean-tree Windows observations. The new diagnostic records its
status without reading or overwriting the edit.

Do not compare those durations as an optimization speed ratio. Earlier Arena
performance measurements above are retained as their own Linux observations.
New portability validation timings below are correctness evidence only.

### Exact retained-byte investigation

The actual original Git blobs match every declared manifest digest. Using Git's
real checkout machinery with `core.autocrlf=true` and **old** attributes converts
the following bytes; **corrected** attributes preserve the original exactly.
All probes use private indexes/work trees, never the user's checkout/index.

| Retained path/package | Original / declared SHA-256 | Old CRLF checkout SHA-256 | Bytes original → CRLF → corrected |
|---|---|---|---|
| `evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md` | `bd6bea50eed267ef338b9e0fcacbd905ffce4d3044dc89b3f3d367c9f551d772` | `bbffd7744ecb94939c95fd4a65f2a63e6c464ad299df0edb6785f57940620d60` | 6534 → 6623 → 6534 |
| Paras `source-captures/bse-displayipo-4895-chunk-0.md` | `908ed21835c0952f763e6bb052247f8879328f863bc8e12c5878660f14cc0b70` | `cac731bff7e46772a690711a9d7d19f382fba26861d4b26fc3b8eb9c57ea803f` | 3220 → 3268 → 3220 |
| Paras `source-captures/bse-historical-listing-chunk-0-prefix.md` | `d8a54f26a17a1b31d13040b4ecfbcd5e08b601772f0d7f469b3cce38ea27c590` | `d227f83a93f66088383aabcd26032b0abf5bbe8ddb9cfc9e584574ccd48b846d` | 5443 → 5499 → 5443 |
| Paras `source-captures/bse-notice-20261019-49-chunk-0.md` | `cf158f9dda463d021a0417d5a2ddfcb5c721dc6f51d9ca478ab28badbb5a11f4` | `03800e5bcca61ff94b059312b1727c7f3c9ad3a725e5f841a21ebb27bec77aff` | 744 → 774 → 744 |
| Paras `source-captures/sebi-abridged-prospectus-chunk-0-prefix.md` | `01c3d61fd6a541e9c3e3ad5a6e1933a9519f8bc0029b2c284755220dffd72168` | `9780624c34ff4da00d6f3912b14dd1e20dde0cc58211ce2951fbef217f2ee3c2` | 8256 → 8315 → 8256 |

The Paras package root is
`evidence/non-authoritative/paras-healthcare-issue-terms-20261024/`.
InvestorGain's converted hash **exactly equals the user's failure**, confirming
that case's CRLF cause. Paras's exact failing path is established and the same
mechanism reproduced, but the actual Windows Paras bytes/digest were **not
supplied**; its Windows cause is not falsely marked confirmed. The diagnostic
collects that missing digest and the normalized-LF fingerprint. No retained
bytes, manifest, checksum or expected digest is changed. New tests exercise fresh
checkouts with `autocrlf=true` and `input`; an unprotected README control checks
that conversion was not accidentally disabled globally.

### Pillow and reproducibility

The only dependency declaration is `requirements.txt`; no optional OCR groups
exist. RapidOCR 3.10.0 already declares Pillow transitively, and the production
OCR path calls `bitmap.to_pil().convert('RGB')`. The regression imports PIL
explicitly. A full requirements install here installed Pillow **13.0.0** and
passes the OCR test. Missing PIL in the user's interpreter therefore indicates
an incomplete/mismatched environment, not an optional test. Pinning Pillow
13.0.0 directly makes this runtime/test dependency explicit and reproducible.
The required Windows action is installation of the full requirements with the
same interpreter as pytest, not an Arena-only transient install or a skip.

The exact published reproducibility child script was recovered from the test
AST and run under emulated implicit CP1252 opens in Arena. It fails at
`json.load(open(sys.argv[1]))` with `UnicodeDecodeError`, byte `0x8f`, position
1843. Explicit UTF-8 fixes that failure. The existing test now has native and
CP1252-default parameters, each retaining seeds **0, 1, 12345** and the original
hash equality/return-code assertions. The actual original Windows traceback
remains absent: the reproduction demonstrates a justified encoding correction,
not proof that the user's truncated traceback had exactly that exception.
The read-only diagnostic runs the exact original published child script under
the user's native interpreter and captures its real stdout/stderr/return code.

### R.K. failures: causal path established; Windows extraction cause still open

- Same source PDF hash in Arena:
  `9a46095da97b4aea8dc9fe67df2a5923dcbb1968323f32ce2cb609d72b975198`,
  **17,310,664 bytes, 496 pages**. The PDF has binary NUL bytes within Git's first
  8,000-byte detection window; ordinary text checkout conversion is not inferred
  as its cause. The actual Windows PDF hash still needs comparison.
- At pinned **pypdf 6.20.1**, TOC capital routing is **106–133**. PDF page **125**
  explicitly labels pre-/post-offer columns; page **126** labels `Promoters`,
  `Total (A)` with post percentages **72.22**, and `Promoter Group`, `Total (B)`
  with **0.03**. The existing guarded category arithmetic yields **72.25**.
  (The existing raw extraction's page locator is section start 106; physical
  table pages were verified separately. No provenance locator is silently edited.)
- Canonical construction retains that value. A controlled copy with only this
  value/evidence absent yields derived `promoter_post_pct=UNKNOWN`,
  `promoter_full_exit=UNKNOWN`, and score **40.0**, versus **44.0** for the actual
  extracted input. This establishes the reported score's four-point causal
  relationship without adding a default, hard-coded issuer value or score change.
- Each of the three reported R.K. tests passed **individually with cache disabled**
  (12.05s; 11.76s; 12.39s respectively, the UI case with one import warning), and
  **together with cache disabled: 3 passed, 1 warning, 36.56s**. They also pass in
  the cache-enabled reported-seven run and corrected focused suite below.
- Capital extraction probes under hash seeds **0, 1, 12345** agree on 72.25,
  routing and page-126 UTF-8 text hash
  `42bf341056e6f33c7ed70c8ef663b8a3281727f083a2c7b7afd276e61f2dff17`.
- The production extraction/config/scoring code and PDF blobs are identical
  between original baseline and optimization. The fixture-fallback suite is not
  cache-opted-in. There is **no direct evidence for a cache regression**, and no
  production parser correction is justified yet. Missing facts are the failing
  Windows interpreter/package versions, PDF hash, page text/status, routing and
  canonical extraction. The diagnostic emits precisely these, without touching
  the user's harness, parser state or a service/store.

### Scoped corrections and validation

Correction paths relative to published **dfa34b2** (eight paths only):
`.gitattributes`, `requirements.txt`, `tests/test_reproducibility_store.py`,
`tests/test_retained_bytes_portability.py`, `tests/diagnose_windows_portability.py`,
`docs/TEST_PERFORMANCE.md`, `docs/TEST_PERFORMANCE_RESULTS.md`, and
`handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`.
The earlier 19-path manifest is the optimization-publication snapshot; the combined
PR now has **24** changed paths relative to **dedb4b8**. No production, schema,
frozen-core, scoring, fixture, retained-evidence, CI or harness change is included
in the portability correction. No original assertion is weakened or removed.
The full count rises by **3** (two checkout cases + one CP1252 parameter).

- Before corrections, fresh complete Arena environment / published code:
  **7 passed, 1 warning, 28.64s pytest / 29.349s wall** for the seven reported cases.
- After correction, byte/hash/repro subset: **33 passed, 1.83s**.
- Broad focused suite (including real OCR, all R.K. cases and promoter guards):
  **45 passed, 1 warning, 35.27s pytest / 35.957s wall**.
- Cache/tier guards: **6 passed, 0.04s**. `pip check`: no broken requirements.
- Pass-9: **88 passed, 1 warning, 0.78s pytest / 1.415s wall**.
- Frontend: **93 passed**, 0 failed/skipped, **0.803230798s Node / 1.574s npm wall**.
- Four schemas, six frozen-core pins, golden result, inactive v1.6, compileall and
  whitespace checks: **PASS**. Golden result unchanged; v1.6 not activated.
- Read-only diagnostic executed in Arena, including full canonical extraction;
  capture hashes match, canonical post holding is 72.25, and the original native
  Linux child succeeds. UTF-8 receipt output and refusal to write to the
  repository/harness were checked. This is tool validation, not Windows evidence.

- **Full corrected Arena suite:** **1,917 passed**, 0 failed/skipped/deselected,
  **25 warnings**, **710.07s pytest / 711.133s wall (11m51.133s)**. Cache summary
  remains **13,585 hits / 1,596 decoded pages**. This sandbox/installation's
  correctness timing is not a new comparable performance baseline.
- Tier collection is complementary: **1,040 fast + 877 integration = 1,917**;
  filtering occurs only in explicit tier commands, never the full command.
- Local logs and byte/provenance probes are under
  `/home/user/windows-investigation/`, outside Git; no generated evidence, logs
  or environment artifacts are added to the repository.
- The focused correction is published only on the existing Arena branch to
  **PR #10**, with **dfa34b2 as parent**. Its exact SHA and independently observed
  remote full-CI conclusion/counts, final remote branch/PR state and the continued
  Windows evidence blocker are recorded in the PR's portability closeout comment.
  Earlier optimization green-CI receipts are not substituted for that new check.
  PR #10 is deliberately kept open; no merge/release/deployment.

Current Windows acceptance is **OPEN**: three
R.K. failures remain unexplained on the failing interpreter; the actual original
reproducibility exception and Paras checkout digest remain to be supplied;
Pillow installation and fresh byte-preserving Windows checkout need execution
there. One diagnostic JSON from that interpreter (command in TEST_PERFORMANCE.md)
is the precise outstanding evidence request. No Windows pass or seven-failure
closure is claimed from Linux results.
