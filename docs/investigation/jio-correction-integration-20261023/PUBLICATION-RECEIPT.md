# Publication receipt — Jio correction integration

| Item | Value |
|---|---|
| Branch | `arena/07f3439f-ipo-screening-engine` |
| Integration commit | `e612702ea22acf221758c44a2f3f98eca85f4d51` |
| Tree | `6f8324c98c854f84a8c797986c1fcac049fca7bb` |
| Parent | `8a1a37022f00496dd22e67b51319a407f6daf6fb` |
| Commit change set | 85 files (50 added, 35 modified) |
| Report | `docs/investigation/JIO-CORRECTION-INTEGRATION-2026-10-23.md` |

## Verified after push

* `git ls-remote` returned `e612702…` for the branch; the GitHub commit API reports the same SHA, parent `8a1a3702…`, 85 changed files.
* **Tree equality:** all 181 published `engine/`, `tests/`, `schema/` and `frontend/` files were re-hashed locally with `git hash-object` and compared to `git rev-parse <commit>:<path>` — 0 mismatches. Independent `raw.githubusercontent.com` fetches of `extraction/builder.py` and `pipeline.py` contain the `kmp_exits_2y` and `field_map` corrections.
* **Correction presence** in the published engine (fixed-string search over the commit): ISSUE routing, debt wording, page-anchored leaves, sole-promoter row, joint-report tenure, `setdefault` evidence agreement, `kmp_exits_2y = None`, `field_map` emission, explicit-map preference, `_find_ofs_nil`.
* **A9 unchanged:** `gmp_binding.py`, `gmp_evidence.py`, `gmp_policy.py`, `connectors/coordinator.py` and `schema/gmp-qualification-binding.v1.schema.json` have identical blob SHAs to the parent commit.
* **Historical records untouched:** `git diff` from the parent to this commit is empty for `docs/investigation/jio-fresh-20261023/` and for the two `JIO-33-*` reports.

## Test evidence (executed, not inherited)

| Suite | Result |
|---|---|
| Backend, integrated tree | **1670 passed, 0 failed**, 25 warnings, 20m17s (`tests-integrated-final.log`) |
| Frontend, integrated tree | **93 passed, 0 failed** (`frontend-tests.log`) |
| First attempt (recorded for audit) | 1668 passed, 2 failed — one missing fixture (fixed), one pre-existing workbook-timestamp flake (reproduced 0/5 on rerun) (`tests-integrated-attempt1.log`) |

## Not performed

* No CI workflow run was triggered for this commit; the results above are local executions on the integrated tree.
* No browser/UI acceptance session; the frontend suite is headless `node --test`.
* No new evaluation was created (see report §7); no market data was fetched.
