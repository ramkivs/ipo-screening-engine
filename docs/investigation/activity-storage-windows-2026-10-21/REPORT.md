# Published worker regression: Windows activity visibility

Date: 2026-10-21. Branch: `arena/95234306-ipo-screening-engine`.
Implementation: `b6230bb421153c75b9e1010d16bb89860d5dcc1c`.

## Scope and result

This investigation concerns the reported `test_genuine_evaluation_success_and_api_history` regression in published `c32e3a7b3376f9f40f7713dd8770940427b410a5`: polling an already-created ingestion returns `None`, then `saved['status']` raises `TypeError`. It is **separate from the earlier live Windows ingestion/PID 11272 stall**, whose original operation/root cause remains unknown.

The failure was reproduced on an actual GitHub-hosted Windows/Python 3.11 runner, not the user's `G:` checkout. The corrected source passed 20 native Windows repetitions and 5 hosted Linux repetitions of the 27 focused cases. The full Linux backend suite also passed, as recorded below. No claim is made that Arena accessed the user's Windows process, browser, drive or cherry-pick.

## Evidence and diagnosis

1. Local Linux published lifecycle baseline: 13 passed. The hosted Linux baseline also completed five repetitions. Linux alone did not reproduce the reported failure.
2. Native Windows baseline run [39599814603](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39599814603) checked out **c32e3a7**, explicitly pinned in `baseline-workflow.yml`; its workflow commit was `4bd72e1`, not the checked-out application revision. The original 13 lifecycle cases/helper/assertions were unchanged. A diagnostic wrapper only logged actual activity `Path.read_text` exceptions and re-raised them; it did not inject faults, retry, suppress exceptions or change results.
3. That run reproduced the exact genuine-success/API-history test failure at `terminal` line 21, `saved['status']`, **1 failed, 12 passed, 1 warning, 1.29 s**. The diagnostic captured **`PermissionError(13, 'Permission denied')`, `winerror=None`**. Full traceback and diagnostic are in `baseline-windows-annotations.json`. The earlier native run 39599549915 also failed Windows while Linux passed.
4. `IngestionActivityStore.get` caught every exception and returned `None`, conflating an existing record that could not be opened with a genuinely absent ID. The store performed destination replacement and concurrent destination/history reads without a shared I/O lock. Atomic complete-JSON publication does not guarantee that a concurrent Windows open succeeds during replacement. The worker and API/polling threads share this store instance.
5. Four deterministic portability cases all failed against the published baseline (`before.log`): unreadable/corrupt records incorrectly became missing; get/history readers did not wait for in-progress publication. The modeled Windows sharing denial matches the observed errno 13 even without a `winerror` value. These modeled tests are not represented as native reproduction; the native evidence is the separate hosted runner failure above.

**Directly observed root of the false-missing result:** a real Windows activity read error was swallowed and converted to `None`. **Corrected concurrency defect:** same-store publication and reads were not serialized. The passing native repetitions support the correction; no Windows kernel/filesystem trace was collected to identify exact internal handle/share flags or exclude every possible external reader. There is no evidence of a wrong fixture path, missing evaluation input or a polling deadline being the source of the observed `None`.

## Minimal correction

- A per-store reentrant I/O lock serializes `save`, `get`, `list_recent` and retention pruning. Readers cannot open the destination halfway through this instance's publication, and pruning cannot remove a file during the instance's own read.
- `get` returns `None` **only for `FileNotFoundError`**. Permission/other I/O errors and invalid JSON propagate, rather than producing a false 404/missing record. No preflight `is_file` check masks the real open result.
- Worker terminal reconciliation explicitly logs `OSError`/`ValueError` read failures and proceeds through its existing trusted-snapshot persistence recovery. It does not rerun ingestion/evaluation or fabricate success. The logger is defined locally before dispatch; the two isolated checks below exercise this error branch.
- Existing history skip-corrupt and best-effort retention semantics were preserved, not redesigned. The lock is process/store-instance local, **not** cross-process coordination, an antivirus workaround, a retry-until-success scheme, or a cure for permanently unavailable storage.

The original lifecycle file, 2-second polling deadline, genuine evaluation persistence assertion and API/event consistency assertions are byte-for-byte unchanged from c32e3a7. No frontend polling workaround or None-skipping helper was introduced. No scoring, policy/authority, golden, schema/config, issuer-specific behavior or issue-term fail-closed change. No production ingestion/evaluation/history or `runtime-logs/` mutation.

## Validation

- Before correction, new portability regressions: **4 failed** (`before.log`).
- Local Linux focused command: `PYTHONPATH=engine .venv/bin/python -m pytest -q tests/test_activity_storage_portability.py tests/test_ingestion_worker_lifecycle.py tests/test_ingestion_activity.py`: **27 passed, 3 deprecation warnings, 1.86 s**, exit 0 (`focused.log`).
- Corrected native CI [39600318064](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39600318064), source **b6230bb421153c75b9e1010d16bb89860d5dcc1c**: Windows **20 × 27 = 540 successful case executions**; hosted Linux **5 × 27 = 135**. Both job conclusions are success. Check annotations explicitly confirm the repeat counts and `win32`/`linux`. Metadata and annotations are retained as `corrected-ci.json`, `corrected-windows-annotations.json`, `corrected-linux-annotations.json`. CI has an actions Node-version deprecation warning, not a test failure. The branch/path-scoped workflow is an investigation diagnostic, not a claim of a full Windows backend run.
- `PYTHONPATH=engine .venv/bin/python docs/investigation/activity-storage-windows-2026-10-21/check_terminal_read_recovery.py`: **2 isolated checks passed** (`terminal-read-recovery.log`). Injected PermissionError and JSONDecodeError are logged; the exact BLOCKED snapshot is durably republished without duplicate finalization, evaluation or false success. Uses temporary stores and synchronous dispatch; it is supplemental to, not a replacement for, original asynchronous lifecycle tests.
- Full Linux backend `PYTHONPATH=engine .venv/bin/python -u -m pytest tests -q`: **1,372 passed, 0 failed/skipped, 25 deprecation warnings, 1162.60 s (19:22), exit 0** (`full-backend.log`). One complete run for this correction; no source changes during the run. All 212 frozen paths reverified unchanged afterward.
- Python compileall for engine and both relevant test modules: exit 0. Correct CLI `PYTHONPATH=engine .venv/bin/python engine/tools/ipo_screen.py check-config`: exit 0, valid ten profiles (`config.log`). An initial incorrect `-m ipo_screening.cli` invocation failed because that module does not exist (`config-command-attempt.log`); it is not counted as a successful config check.
- No frontend changes; no new frontend/build/typecheck success is asserted. Prior c32 report's 90 frontend passes, baseline mypy blockers and absent npm build script remain historical results, not rerun/green claims for this correction.

## Frozen source and publication

`tested-tree.json` freezes 212 runtime/test/config/schema/fixture/frontend/workflow paths; SHA256 **526b2a7d083de82f0af41ae1a7c333e89ac693b84320cfd834520c5f03e44cd9**. Original lifecycle bytes are unchanged. The only application source differences from c32 are activity storage and terminal read reconciliation; new portability tests and the diagnostic workflow are separate additions.

The appended tracker entry records actual full-suite completion and preservation of prior tracker bytes. Independent post-push verification checks remote source/artifact byte identity, main remaining `01ba66c12ca1195fd7acbd287c3e39a019808094`, and PR #6 remaining OPEN/unmerged with its existing unrelated head/base. Final documentation-only commit SHA is reported in the completion response after push/independent verification. No merge, retarget, reset, clean, amend or force-push is authorized or used.
