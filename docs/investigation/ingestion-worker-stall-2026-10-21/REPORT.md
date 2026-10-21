# Stalled Jio ingestion: confirmed lifecycle defects and local-diagnosis boundary

Date: 2026-10-21. Baseline remote: `cb5c5e595557ed79f5f78bbc3150ac42b5cd7f88`.
Branch: `arena/95234306-ipo-screening-engine`. No alternate delivery branch.

## Executive finding — do not confuse reproduction with the Windows cause

**A repository defect that produces the exact two-upload-event / permanently RUNNING shape is demonstrated and corrected. Its triggering condition is an exception while publishing activity, followed by another exception in terminal-error reporting, escaping to a daemon wrapper that silently discards it. This does not establish that those exceptions occurred inside the user's Windows PID 11272.** No Python stack dump, actual activity JSON, deployed-module identity or ingestion-specific exception log for `ing-bbd84e84a1f24abd` is accessible here. The exact local root cause and live local acceptance remain unresolved; this report is not certification that PID 11272 was repaired.

The repository Jio PDF is available, so it was tested rather than requested again. SHA-256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`; byte identity with the Windows upload is unknown. Using the baseline dispatcher and current processing path, it reaches **BLOCKED / AWAITING_ISSUE_TERMS** in **32.05 s**, 21 events, no evaluation ID or persistence. The corrected dispatcher reaches the same honest blocked result in **31.73 s**, 22 events (additional worker-start event). Official providers are deliberately empty, networking is not used, and evaluation is explicitly prohibited in this diagnostic. These isolated temporary-store tests do not claim live source acceptance. See `reproduce_available_jio.py`, `available-jio-results.json` and `.log`. This normal-path run preceded the final terminal-durability guard refinement; that refinement is covered by focused/full tests.

## Verified state and history

Initial sandbox Git index was at main `01ba66c`, while all 428 delivery files exactly matched the remote `cb5c5e5` bytes. Files were compared before staging and safely fast-forwarding the existing branch. No reset/clean, branch switch, unrelated file overwrite or user-data deletion was used.

- Latest issue-term fix: **cb5c5e5**. Its service changes are at required-term discovery, after document validation/extraction. It expands required terms, traverses providers and merges field-provenant payloads; it did not change thread dispatch or activity persistence. Its previous full-suite result does not establish Windows execution behavior.
- Ingestion observability/daemon wrapper originated at **22f82b8f8f347d29a65ac831c10ce966a79d0d35**. Its claim that thread failures could never leave RUNNING was false: `except Exception: pass` assumes the nested handler successfully persisted a terminal outcome. That assumption was untested in the prior normal async test.
- Thus the confirmed lifecycle defect predates cb5c5e5. No demonstrated causal link from the latest issue-term change to the two-event local stall is established. More discovery work can take longer, but it occurs later than the observed persisted frontier and must not be blamed without evidence.
- PR #6 was remotely verified OPEN/unmerged with head `arena/5dd3fe52-ipo-screening-engine` / `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine`. It is not a PR from this session branch and is not retargeted. Main remains `01ba66c12ca1195fd7acbd287c3e39a019808094` at starting verification.

## Execution trace and earliest justified conclusion

1. API `POST /api/v1/ingestions/start` reads upload bytes, enforces 50 MB, calls `start_ingestion_async`, returns activity/correlation URLs. GET status/events read the same durable activity store; frontend polls these endpoints and consumes the actual terminal result.
2. `new_recorder` atomically persists upload RUNNING. The old dispatcher starts a daemon thread; the worker calls `ingest_document(recorder=...)`.
3. `ingest_document` enters `_ingest_document_impl`, which emits upload SUCCEEDED, checks byte size/PDF magic/mode, and emits **document_validation passed**. This event precedes config loading, temporary PDF staging, text extraction, issuer identification and all official discovery.
4. Extraction emits its start/completion and issuer/term events. Discovery reports providers and unresolved terms; missing/unverified required terms remain fail-closed. Evaluation/persistence execute only if the existing readiness gates pass.
5. Processing exceptions normally call recorder emit/finish. Crucially, those calls can themselves throw. `finish` changes in-memory status before saving the final event, so a terminal memory snapshot is not evidence that the disk record is terminal.
6. The old daemon wrapper swallowed ordinary escaped exceptions, missed `BaseException` exits, had no fallback when a worker returned without a terminal result, and did not handle Thread constructor/start failure. API acknowledgement always claimed RUNNING, even when execution had already ended.

**Earliest confirmed local frontier: the second durable upload event. Earliest actual stopped Python operation: unknown.** The third activity publication/validation window, failed activity I/O, exited worker, stale/deployed-code mismatch and a genuinely blocked operation are distinguishable possibilities, not established Windows findings. A successful health endpoint and nine waiting OS threads cannot identify which occurred. No source evidence justifies asserting that the Windows worker is inside PDF parsing, provider retrieval, config loading or a particular lock.

## Small reproducible defect

`reproduce_boundary.py` loads only the baseline dispatch method from the immutable baseline commit (no branch switch), runs the real ingestion method and injects two activity-write interruptions at document validation/error publication. No extraction, network or evaluation is reached.

- Baseline: worker exits; disk has `RUNNING`, `finished_at=null`, `error_code=null`, `evaluation_id=null`, exactly `['upload','upload']` event stages.
- Corrected: same injected faults produce durable `FAILED`, `INGESTION_WORKER_FAILED`, finished timestamp and no evaluation ID. The worker-entry event is visible. Failed stage events and terminal termination remain separate events; failed persistence is not reported as success.

The fault injection proves the repository mechanism and matching symptom, not a Windows filesystem/sharing/antivirus diagnosis. `boundary-results.json` and `boundary.log` retain the actual results.

## Correction (small worker-boundary change)

- **service.py:** record worker entry; handle thread dispatch failure; catch escaped worker exceptions including SystemExit; log original traceback with ingestion ID; persist a terminal fallback only when inner processing did not already terminate. A return without a terminal result is FAILED, not assumed success.
- Preserve specific inner BLOCKED/FAILED/SUCCEEDED outcomes. Before trusting a terminal in-memory record, compare it with disk and attempt to persist the exact snapshot if different. Terminal-write retry uses the same snapshot, not a second completion event or a second evaluation.
- **api.py:** 202 acknowledgement uses the actual recorder state rather than unconditional RUNNING. A dispatch failure remains an accepted diagnostic attempt with a durable FAILED activity, not a successful ingestion.
- **tests/test_ingestion_worker_lifecycle.py:** deterministic worker-boundary, durability and API regressions; existing activity suite remains unchanged. Actual engine success in a temporary store is verified, not just a mocked success badge.

No scoring formula, weights, thresholds, knockouts, golden fixtures, evidence verification authority, issue terms, schema/config, evaluation history or frontend behavior is changed. No automatic processing retry is introduced; existing result-hash duplicate detection remains in place. Activity write retry cannot create an evaluation.

## Validation ledger

- Before correction: **4 failed, 2 passed, 1 warning, 6.53 s**; dispatch, escaped ordinary exception/SystemExit, incomplete return. See `before.log`.
- Additional memory/disk durability regression before final refinement: **1 failed, 2 passed, 9 deselected, 2.47 s** (`-k inner_terminal` also selects two existing parametrized cases). See `durability-before.log`.
- An intermediate expanded-test run had two test-harness failures (default TestClient host rejected by existing loopback guard, and a log assertion racing its worker). Fixtures were corrected to loopback and joined worker completion; no backend security guard or assertion of actual failure was weakened.
- Final focused command: `.venv/bin/python -m pytest tests/test_ingestion_worker_lifecycle.py tests/test_ingestion_activity.py -q`: **23 passed, 3 deprecation warnings, 1.84 s**. Covers 13 new cases plus 10 existing activity tests.
- Full backend command `.venv/bin/python -u -m pytest tests -q`: **1,368 passed, 0 failed/skipped, 25 deprecation warnings, 1653.21 s (27:33.21), EXIT 0** (`backend.log`); frozen 210-file runtime/test/config/schema/fixture/frontend manifest is `tested-tree.json`. Initial early run was interrupted for the demonstrated terminal memory/disk gap; its log is retained, never counted as a pass.
- `(cd frontend && npm test)`: **90 passed, 0 failed** (`frontend.log`).
- `.venv/bin/python -m compileall -q engine tests/test_ingestion_worker_lifecycle.py`: EXIT 0 (syntax, not static typing). `node --check` for every `frontend/*.js`: EXIT 0. `check-config`: EXIT 0, valid ten profiles (`config.log`).
- Static typing was actually attempted with ephemeral **mypy 2.4.0**, without modifying requirements/config. Standard command on service.py/api.py: **EXIT 2**, duplicate module discovery (`ipo_screening.post_listing.calibration` and `engine.ipo_screening.post_listing.calibration`) prevents further checking. The identical command on a temporary source-only archive of cb5c5e5 gives the same blocker. A limited `--follow-imports=skip --ignore-missing-imports` check: **EXIT 1**, two existing `None.get` union-attribute errors in read-model service code. Baseline has the identical two diagnostics after line-number normalization. Neither type check is represented as passing; see `types-*.log`. No unrelated type fixes or suppressions were introduced to obtain a green result.
- `(cd frontend && npm run build)`: **EXIT 1, Missing script: build** (`build.log`). This repository serves plain static frontend assets with FastAPI StaticFiles and defines only npm test; there is no configured production bundling/typecheck script. No production bundle is claimed, and no artificial build step was added to mask the lifecycle issue.

## Remaining genuine boundaries and local evidence needed

- **Actual PID/local root cause remains unconfirmed.** Preserve the original activity JSON and server logs before restarting. Capture a Python all-thread stack dump of the currently verified Uvicorn PID (do not assume old PID 11272 is still the same process), its command line/module path, deployed commit and SHA-256 of service.py and the uploaded PDF. Compare the PDF hash above rather than resending an already available document. A read-only `py-spy dump --pid <current-pid>` is one possible local stack capture; it was not executed here. Do not include credentials or document contents in diagnostics.
- Do not manually mark `ing-bbd84e84a1f24abd` failed or rewrite its JSON from this diagnosis. A live worker may still be able to persist. No local record or Windows process was accessed or mutated from Arena.
- A live thread blocked in filesystem I/O or another call is not safely cancellable with Python Thread. No arbitrary timeout, heartbeat expiry or superficial UI polling change is added that could declare FAILED while evaluation later persists. A demonstrated blocking stack is needed to justify operation-specific timeouts or a killable worker architecture. Existing HTTP timeout/retry bounds are unchanged.
- Abrupt process death cannot run a daemon's finally block. Permanent inability to write the activity filesystem also cannot guarantee a durable terminal record; retries are bounded and failures logged, not silently swallowed or falsely marked persisted. Restart/orphan ownership and active-hang cancellation are not claimed solved.
- Existing static-type blockers and the absent build script are explicitly reported, not hidden. These checks are not green merely because backend/frontend tests pass.

## Final disposition

**Bounded repository lifecycle correction: verified. Exact Windows ingestion root cause/local acceptance: OPEN, not certified complete.** All 210 manifest files were rehashed after the full run with zero mismatches; manifest SHA-256 `0e3fa79105b2bdfea1442d591f1150edcc7b6d0fbe4a94affb2423e3a944db9a`. No source/test edits followed the final frozen run. Static typing and the requested build command are not passing, with unchanged baseline / absent-script evidence above. These outcomes are not relabelled green.

## Publication

Correction, tests, evidence logs and append-only authoritative tracker update are published on the existing branch after validation. The exact commit SHA, independent remote byte checks, final manifest verification, PR/main state and clean worktree are recorded in the completion response. **Repository lifecycle correction is not completion of the unobservable Windows root-cause investigation.**
