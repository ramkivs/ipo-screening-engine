# A9 global qualification — execution and dependency disposition

Date: 2026-10-22, Asia/Calcutta. Status: **OPEN — CONTRACT/IMPLEMENTATION GAP**.
This is completed independent preparation/validation, not an accepting implementation.

## Baseline and authority

The fixed session branch `arena/07f3439f-ipo-screening-engine` was fast-forwarded
from handoff-only `01ba66c` to published implementation
`e05c0efbca1ecb3024e52da73a22e180ea171118` without switching branches. PR #6
was inspected, not modified. The prior investigation used `e8f9a282…`; the A9
investigation records, A17/A18, GMP code, evaluation_record.py and linkage tests
have identical content between those two published revisions (verified by git
diff). They need not share the same branch ancestry to establish content equality.

A16 and the current one-pass directive authorize this work. The superseded broad
Phase-1 hold is not a blocker. GOV-001 permits an explicitly open decision record;
[A19](../../handoff/decisions/A19-gmp-qualification-contract-request.md) records
only the actual semantic questions, not an application for routine permission.
No live authority-decision service was found; the request has no approval response.

## Evidence disposition (no new retrieval or broad search)

Evidence directory: `evidence/gmp-observations/marketliveipogmp-tonbo-20261015`.
All eight retained rendered files match manifest byte counts and SHA-256 digests.
They are transcribed rendered content, not provider bytes. Exact receipt, headers,
cache state and machine-checkable transcription fidelity are unavailable. These
limits do not reinstate a provider-native-byte prerequisite under D1.

| Question | Disposition | What remains / recoverability |
|---|---|---|
| Repeated returned Tonbo text stable | SATISFIED narrowly | Four retrievals are recorded as identical; only one file retained. Unknown tool caching prevents a broader storage-behaviour conclusion. |
| Same-stamp mutation never occurs | UNRESOLVED | No changed pair is retained. Existing identical text cannot demonstrate universal immutability. A genuine version sequence is needed. |
| Corrections, withdrawals, preserved old versions | UNRESOLVED | About-page promises are not examples. Need a real before/after correction or withdrawal record with affected observation identity and timing. May be recoverable from a source-maintained archive if it exists; availability is not established. |
| Conflicting observations | UNRESOLVED factual evidence; BLOCKED policy | Cross-check claim has no conflict-resolution example. Do not infer precedence. PR-4f/PR-5 are still proposals. |
| Final prelisting freeze | UNRESOLVED with adverse evidence | Hero Motors says before listing but stamps 15:37 IST on listing day; cause not established. A future freeze check is not evidence already obtained. |
| Exact retained observation reproduction | SATISFIED | Tonbo title/page, +71.4%, publisher time and exact retained bytes. This is not proof of earlier readings. |
| Capture at historical cutoff | SATISFIED only for compatible cutoff | Window end 2026-10-15T13:17:58.770Z; no exact receipt inferred. Cutoff inside window cannot establish capture completed by it. |
| Earlier readings/history | UNRESOLVED | Chart reading list absent. ₹32 delta does not retain an earlier ₹468 reading. Earlier observations cannot be reconstructed from this package. |
| Mutable later page proves historical availability | UNSATISFIED evidence method | A later capture never fills missing historical availability. A previously retained independently dated archive could be assessed, if one exists. |
| Retained Tonbo observation eligible at October19+ Final | UNSATISFIED | Stale. Later capture of the same observation does not refresh its publisher as-of. |

Publisher time is 2026-10-15T10:32:00Z. Combining A17 and D2 gives a timing-only
eligible interval from **2026-10-15T13:17:58.770Z through
2026-10-16T10:32:00Z inclusive**. This is not a qualifying interval for A9.
The original October16–19 successive-reading evidence opportunity is over; no
later capture can recreate it. On October22 the planned post-October23 check is
still future, and would not retroactively prove the earlier history either.

Sources: candidate README 28–37; manifest artifacts and derivedChecks; retained
About 11/27; Hero Motors 124–132; alternative-publisher assessment sections 14–16.
R1–R4's recorded bounded passes and D1–D3's dispositions are preserved. R7/R8 as
overall publisher requirements remain UNRESOLVED, not silently promoted or
labelled demonstrated same-stamp mutation.

## Candidate readiness

| Requirement | MarketLiveIPOGMP disposition |
|---|---|
| Publisher qualification | NOT QUALIFIED; Model A identity is not approval |
| Issuer / issue | Captured Tonbo context established; general distinct-offering binding still needs contract |
| Percentage / trend | +71.4% explicitly displayed; no accepted trend label, do not derive from ▲₹32 |
| Timezone / cutoff | Explicit IST normalization established; evaluate each actual cutoff |
| Capture by cutoff / 24h | Timing interval above only; expired for October19+ Final |
| R7 / R8 | UNRESOLVED; engine policy questions separated from factual evidence |
| A18 | Mechanism available, local byte integrity checked; no evaluation or qualification created from it in this pass |
| Qualification signal / required hash | Undefined; A19 OPEN, artifact hashes not substituted |
| Qualified replay | BLOCKED on authorized contract plus legitimate evidence baseline |

InvestorGain remains NOT QUALIFIED. PapsDigital remains closed as a non-independent
alternative. No publisher or qualifying positive fixture was created.

## Question classification

1. **Settled decisions:** Model A; A17 inclusive cutoff, explicit offsets, 24h,
   accepted publisher labels only; D1 rendered bytes; D2 availability; D3 missing
   versus zero; A18 linkage != qualification. Apply without reapproval.
2. **Resolved from existing evidence:** retained integrity, captured values/time,
   limited stability, timing interval, lack of retained earlier history.
3. **Resolvable under standing authority, completed here:** implementation design,
   regression-gap mapping, compatible boundary tests, reproducible CI, docs,
   tracker and publication/verification of this bounded work.
4. **Needs new evidence:** R7 correction/withdrawal/version/conflict examples,
   historical readings and freeze behaviour; genuine qualified multi-issue
   regression baseline. A policy decision cannot create that evidence.
5. **Needs new semantic authority:** qualification authority/scope; selection and
   correction rules; required trend/absence treatment; signal/hash subject and
   exact representation/compatibility. A19 requests only these decisions.

## Implementation design completed without speculative runtime changes

Existing components to reuse: gmp_policy.py for A17 time/labels;
gmp_evidence.py for manifest/artifact integrity and A18 linkage; pipeline.py for
retained context/replay; evaluation_record.py for shared A9 outcome resolution.
A18 currently rejects non-null trend at gmp_evidence.py:1043–1044. Any future
trend-evidence extension must be separately authorized; do not silently remove
that check. Null trend qualification eligibility itself needs disposition.

After ratification AND sufficient evidence, implement in this order:

1. Represent the immutable authorized disposition and exact qualification subject
   under the approved compatibility contract. Do not overload VERIFIED/content_hash.
2. Verify authorization/scope, distinct offering, selected observation, exact value
   and permitted trend evidence. Reuse A18 byte and capture-window checks.
3. Enforce A17 cutoff/freshness and adopted correction/selection rules; construct
   deterministic failure diagnostics and retained qualification evidence.
4. Add successful admission only to the shared Final gate. Remove only A9's veto
   when valid; leave KO/critical/unknown/other outcome resolution untouched.
5. Persist/replay the subject, authorization/policy and evidence dependencies,
   excluding final result hash/derived evaluation ID from upstream hash inputs.
6. Execute defect-specific rejection tests from a genuinely passing baseline,
   then global integrations/integrity and publication verification.

No new runtime API, approval flag, hash function, schema or accepting branch was
implemented. The proposed exact semantic contents and unresolved serialization
choices are recorded in A19, visibly unapproved.

## Regression preparation and limits

| Area | Existing coverage / independent work | Qualification-dependent gap |
|---|---|---|
| Missing, unqualified, generic digest, Preliminary | test_evaluation_record_v1.py; rerun | Admission using authorized disposition, not blanket veto |
| Stale/future/offsetless/24h, trend mapping | test_a17_gmp_policy.py; rerun | Same negatives from qualified baseline |
| Zero/missing, late capture, tamper/malformed | test_d1_d3_gmp_source_policy.py; rerun | Successful-path integration and qualification-subject tamper |
| Identity/link integrity, conflicting declarations | test_gmp_evidence_linkage.py; rerun | Distinct issue under same issuer; qualification binding and selection rules |
| Trend linkage restriction | Three new cases compare VERIFIED null-trend component baseline with each rejected non-null label and assert actual reason | Approved label-evidence contract / absence semantics |
| Cross-issuer/evaluation replay | Four new cases: two synthetic issuers × two instants, verified linkage but unqualified Final, persisted replay, Preliminary preservation | Genuine multi-issuer / multi-issue qualified cases; cross-substitution from passing cases |
| Retained rendered bytes | One new test verifies eight manifest lengths/digests | Source qualification still not established |
| KO/critical/other gates | Existing gate and frozen-core suite rerun | A9-pass cases must then reach those gates |
| Schema/golden/persistence/integrity | Full suite + direct schema/frozen/golden/v1.6 checks | Approved new representation compatibility and qualified replay |

Missing/invalid qualification hash, generic-hash substitution, wrong issue,
conflicts/corrections/revisions/precedence, malformed evidence and unsupported
trend must be isolated mutations of genuine contract-compliant positives after
ratification. Synthetic approval flags, invented captures and relabelled current
unqualified evidence are prohibited. Today's negative coverage proves only the
current boundary, not a future successful validator.

## Current validation results

Environment: Python 3.11 venv, exact requirements.txt installed; Node 22.22.3.

- Focused A17/D1–D3/A18/A9 suites: **188 passed** before the final retained-byte
  integrity test was added. The full run below includes that eighth new test.
- Final focused rerun including all eight added cases: **189 passed** (22.70s).
- Full backend: `.venv/bin/python -m pytest tests/ -q` — **1059 passed**, 19 warnings,
  1178.54s. Warnings: existing unregistered `slow` marks and FastAPI/Starlette 422
  constant deprecation. No test failures or skips.
- Frontend: `npm test --prefix frontend` — **77 passed**, zero failed/skipped.
- Python compileall: PASS.
- All three schema documents: validator_for(...).check_schema — PASS.
- Frozen core: PASS, 6/6.
- Golden result: PASS, `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.
- v1.6 verification: PASS, no failures/warnings; remains inactive.
- git diff --check: PASS.

No frontend build/type script exists; this is JavaScript, not a TypeScript build.
The new GitHub workflow reruns backend/frontend/compile checks at the published
revision. Its actual result and remote identity are recorded by a subsequent
tracker verification entry, not assumed here. No local/browser or Windows
runtime acceptance is claimed. No application server was started or stopped.

## Completion boundary

Independent work is complete subject to publication/CI verification. A19 is a
request, not approval. Remaining order: semantic disposition + actual R7/R8
source evidence -> authorized source qualification -> compatible signal/hash
implementation -> global accepting-path tests -> integrity/replay/remote closure.
Until all closure criteria pass: **OPEN — CONTRACT/IMPLEMENTATION GAP**.

## Publication receipt

PR #7 publishes bounded changes on the fixed session branch, based on PR #6's
implementation head without modifying PR #6/main. Preparation commit:
`ba9cc5ae726b25ec182db1149185c8fba62cb832`; API-visible CI diagnostics commit:
`b9df27b45852c4afbb4cc4f430e79c7eea74b424`. Exact five changed-file bytes, remote
commit and full tree identity matched local Git at each published revision.

First workflow run 39787253029 failed backend; redirected logs are inaccessible
and the check exposes only exit 1. Cause remains unknown. The diagnostic rerun
39790967681 at b9df27b has a COMPLETED/SUCCESS regression job/check 119866566070
(all backend/frontend/schema/integrity/compile/clean-tree steps successful).
Workflow aggregate still reports IN_PROGRESS/null conclusion at 14:25:14Z; this
report does not invent aggregate completion. Local 1059/189/77 results stand as
actual executions; a successful remote job does not explain the prior failure.

This receipt is docs-only, CI intentionally skipped. Runtime, tests and workflow
remain byte-identical to the job-tested b9df27b revision; remote verification of
the receipt follows publication. Remaining work is unchanged: A19 ratification
and sufficient source evidence before any accepting implementation. Status OPEN.
