# Broad remediation — consolidated disposition (2026-10-27)

One execution pass over the whole broad-remediation scope, with the two open semantic
questions measured rather than argued. **No engine file was changed.** The pass adds two
decision records, one regression-test module, and corrections to four documents.

Governing instruction: the Jio disposition report, the 2169 passing tests and the published
commit are **not** proof every requirement is closed. PR #13 must not be merged. The existing
lock-in generalization and all prior work are preserved.

---

## STATUS UPDATE — A33/A34 approved, implemented and focused-verified
(2026-10-27, resumed execution; supersedes the "unresolved" dispositions below)

**This document's §2–§10 describe the earlier pass, in which both decisions were
PROPOSED and no engine file was changed. They are retained as the evidence base.
The current state is:**

| Item | Current state |
| --- | --- |
| **A33** | **Alternative A APPROVED, provisionally.** Preserve the current `kmp_exits_2y` counting rule; **no counting or scoring change**. Jio 6, Paras 4; both `board_kmp` SCORED 0 `high_churn`. |
| **A34** | **Alternative B APPROVED and implemented.** A category-specific institutional carve-out alone does not establish an early unlock. The PR #13 reader in `sections.py` now sets `large_holders_unlocked_early` only from an evidenced actual early release; otherwise the field stays `null` and C `lockin` is UNKNOWN. |
| **A32** | **Still `NOT RATIFIED`.** A34's approval is not A32's ratification. Keeping that status visible, and keeping A34 recorded as approved rather than unapproved, are genuine remaining governance-recording requirements (A34 §0.3). |
| **Issuer reproduction** | Both issuers reproduced fresh. Jio 37.0 / `AVOID` / K2 / 63.0% → **62.0%**, bounds 25–74 → **25–75**, `lockin` SCORED 0 `weak` → **UNKNOWN**. Paras 13.0 / `AVOID` / K5 / 44.21% → **43.16%**, bounds 1–66 → **1–67**, `lockin` SCORED 0 `weak` → **UNKNOWN**. No final score, verdict or knockout changed. |
| **Semantic boundary** | Verified: carve-out alone does not set the flag; evidenced early release is handled by the governing criterion; ambiguous/insufficient evidence and unrelated pledge/transferability language stay UNKNOWN; genuine positives remain detectable via labelled synthetic tests. Zero real-filing positives across five filings (2,826 pages) is a corpus limitation, **not** proof that early releases never occur. |
| **Verification** | 28 A34 tests + 65-test focused batch + 132-test affected-regression batch + tier gate + frozen-core/golden-result/v1.6/schema/compileall checks — all PASS. **Full suite not run by instruction.** |
| **PR #13** | Still **OPEN, not merged**. |

Authoritative detail: `A33-A34-ISSUER-REPRODUCTION-2026-10-27.md` (with
`a33-a34-issuer-reproduction-20261027/summary.json`),
`handoff/decisions/A33-kmp-exit-counting-scope.md` §0,
`handoff/decisions/A34-early-unlock-carve-out-semantics.md` §0,
`LOCKIN-INSTITUTIONAL-CARVEOUT-GENERALITY-2026-10-27.md` revision 2,
`PARAS-UNKNOWN-TRIAGE-2026-10-27.md` §0/§3,
`JIO-34-GLOBAL-ARCHITECTURE-DISPOSITION-2026-10-27.md` §11, and tracker
Revision 31.

**Evidence caveat.** The paused session reported 28 A34 tests and 90 tests
across four additional modules as passing, but that session's uncommitted work
and test output did not survive the workspace reset. Only PR #13's head tree
(committed) survived. The A34 suites were reconstructed from the surviving
decision records and re-run; no unverifiable result was carried forward.

---

## 1. Authoritative repository / branch / commit / PR / CI state

| Item | Value |
|---|---|
| Repository | `ramkivs/ipo-screening-engine` (clone of `https://github.com/ramkivs/ipo-screening-engine.git`) |
| Working branch | `arena/342ccacc-ipo-screening-engine` |
| Base | `main` @ `69a9ff9d77c9886a1b30c31ed327d5a9d747a1a7` (merge of PR #12) |
| Local HEAD at start of pass | `46363465293a8adb29a45e7cff18396fef997ddc` |
| Remote branch HEAD | identical to local |
| `git status` at start | clean |
| PR #13 | **OPEN** — "Generalise the Regulation 17 institutional lock-in carve-out reader"; base `main`; head `arena/342ccacc-ipo-screening-engine`; commits `cac095d` (reader) + `4636346` (disposition docs/tests); `mergeStateStatus UNSTABLE` |
| PR #13 CI | `regression` (workflow "A9 contract boundary regression") **IN_PROGRESS** at `2026-10-27T15:47:22Z` |
| PR #13 merged? | **NO — and it must not be merged** |
| Worktree | `.venv` rebuilt from `docs/investigation/jio-fresh-20261023/dependencies.txt`; Python 3.11.2 |

Branch reconciliation: the checkout was reset to the fresh clone this session (local `arena/…`
pointed at `69a9ff9`, `.venv` absent). After `git fetch origin`, the staged tree was verified
**IDENTICAL** to `origin/arena/342ccacc-ipo-screening-engine` before
`git reset --soft <remote-tip>`; HEAD `4636346`, clean.

---

## 2. Requirement-by-requirement disposition

| # | Requirement | Disposition | Evidence |
|---|---|---|---|
| 1 | Re-establish authoritative state (repo, branch, worktree, HEADs, PR, CI, diffs, docs, tests, contracts) | **Done.** State in §1; PR #13's diff read (12 files, `engine/ipo_screening/extraction/sections.py` +66 is the only engine change); contracts located: `config/ipo-config.v1.5.0.json` `derived_metrics.board_kmp_bucket`, `schema/ipo-input.v1.5.schema.json`, `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md`, `handoff/reference/Claude_IPO Screening Engine v 1.3 — Specification.md`, `handoff/decisions/A32-…`, tracker Revision 25 | §1; §4; §5 |
| 2 | Resolve `kmp_exits_2y` — no silent redefinition | **Resolved as a governance decision (A33), code unchanged.** Current rule verified and pinned by 14 new tests; both KMP-only variants measured; recommendation: retain the current rule | §4 |
| 3 | Resolve the Reg 17(1)(c) carve-out — implement only when authorized | **Resolved as a governance decision (A34), code unchanged.** Both quotes independently re-extracted and verified verbatim with correct pages; recommendation: a category carve-out alone must not set the flag | §5 |
| 4 | Reconcile the broader remediation (eight workstreams, UNKNOWN scoring, K1–K6, GCP separation, market-data restriction, peer absence, reverted Module E, regression matrix, documentation reconciliation) | **Re-assessed.** No manufactured fixes, no fabricated values, no weakened fail-closed behaviour. Three documentation reconciliations made (see §3) | §3 |
| 5 | Execute and verify — general solutions, regression tests, tier gate, full suite, Jio/Paras reproduction | **Done.** New issuer-neutral module (14 tests, synthetic tier); focused suites green; tier gate green; full suite run; Jio reproduced by its pinned test, Paras reproduced end-to-end this pass | §7; §8; §9 |
| 6 | Final deliverable — one consolidated report with ten items | **This document** | all sections |
| — | Preserve the existing lock-in generalization and all prior work | **Preserved.** The PR #13 reader (`cac095d`) and its 17-test matrix are unchanged; A34 records the open question and recommends a narrower rule pending RAMKI | §5; §6 |
| — | No competing branch, no duplicate PR | **Holds.** One branch, one PR (#13, OPEN) | §1 |

---

## 3. Workstream table

| Workstream | Status | Note |
|---|---|---|
| WS1 UNKNOWN scoring / completeness / bounds | **Completed & verified** | Fail-closed tri-state holds; no favourable defaults reintroduced. The 2166/0 figure in the lock-in generality report was a documentation mismatch and is corrected to the 2169/0 result |
| WS2 `kmp_exits_2y` counting scope | **Remediated awaiting verification** — decision recorded, **not implemented** | A33 PROPOSED/UNRESOLVED; 14-test baseline added; recommendation: retain the current rule |
| WS3 Reg 17(1)(c) carve-out semantics | **Remediated awaiting verification** — decision recorded, **not implemented** | A34 PROPOSED/UNRESOLVED; quotes verified; recommendation: carve-out alone must not set the flag |
| WS4 K1–K6 truth-state, absence of favourable defaults | **Completed & verified** | `promoter_pledge_pct` is `null` on the current Jio engine result (K2 driven by the pledge limb being UNKNOWN, not by a default); K1/K2/K5 tri-state reproduced |
| WS5 Final-filing discovery; GCP vs legal-max separation | **Completed & verified** | GCP `[●]` stays UNKNOWN and the 25% statutory ceiling is not substituted; `ofs_seller_type` / `promoter_ofs_pct` stay UNKNOWN rather than scoring a deceptive `none_or_small` |
| WS6 Environmental market-data restriction vs adapter defect | **Completed & verified (restriction, not defect)** | No market block exists for Jio or Paras in the corpus; the current-engine probe used `IssueTermsResolver(providers=[])` plus five manual terms, which accounts for part of the 34.0 → 37.0 delta. No adapter defect claimed |
| WS7 Peer absence and non-substitution | **Completed & verified** | Jio's two peers are `VALID`; `second_multiple` and `sector_ipo_relative` stay UNKNOWN; no peer metric substituted |
| WS8 Preserve the reverted Module E change | **Preserved** | No Module E change present in the tree; the revert stands |
| WS9 Regression matrix and tier declarations | **Completed & verified** | New module is synthetic-tier (not in `INTEGRATION_MODULES`); tier gate green |
| WS10 Reconcile documentation / published evidence with code and test results | **Completed this pass** | Three corrections: (a) disposition report §6.3(i)/§8(1) — the B1/B2 distinction and the corrected Jio attribution; (b) lock-in generality report §2/§6 — the "free at Allotment" inference withdrawn and the full-suite figure corrected; (c) Paras triage §3 — "discloses the early unlock" corrected to "discloses the carve-out" |

No workstream was closed by assertion. Every "completed & verified" entry rests on a test
run or a measured reproduction recorded in §8 and §9.

---

## 4. Evidence-backed `kmp_exits_2y` disposition

**What the engine does (verified, not inferred).** `engine/ipo_screening/extraction/directorate.py::count_exits`
(line 528) counts every event whose `event` ∈ `_EXIT_EVENTS = {resignation, cessation,
retirement, term_expiry}` (line 217) inside the 24 calendar months ending at the anchor,
inclusive (line 548). **It does not consult `role`.** The builder derives the count against
the offer open date (`builder.py::_derive_board_changes`); an unread table leaves the count
`null`, never `0`. The schema names the source *"Dated director / key-managerial-personnel
events"*.

**The governing contracts disagree in wording.** The metric formula says "KMP exit"; the
merged implementation (PR #12, tracker Revision 25, cross-issuer validated on four filings)
counts the whole table. That disagreement is the decision, not a bug.

**Both KMP-only readings were measured on the real tables:**

| Reading | Jio (17 rows, anchor 2026-10-21) | Paras KMP p. 357 (7 rows) | Consequence |
|---|---|---|---|
| **B1** recognised KMP `role` only | **1** | **0** | both < ≥2 → `board_kmp` `high_churn` → `other` (+1 each) |
| **B2** skip a known non-KMP designation, count an unrecognised one fail-closed | **2** | **4** | no bucket changes |

**Disposition: retain the current rule; do not silently redefine.** B1 discards disclosed
evidence — Paras's KMP table prints no designation column, so `role` is null on every row
and all four disclosed resignations would become unclassifiable. B2 changes no bucket and
buys nothing. The real defect is **role recovery**, which is an extractor improvement and a
separate decision.

**Jio's published 34.0 record is not in dispute.** It carries `kmp_exits_2y: null` →
`board_kmp` **UNKNOWN** (Module D score 5.0, `unknown_points` 6.0). The disposition report's
§6.3(i) parenthetical is corrected: the two Jio exits B2 retains are the CEO resignation
(2026-03-23) and the one exit whose designation the reader did not recover (2026-06-19);
there is **no Company Secretary resignation in Jio's window**.

**Recorded in** `handoff/decisions/A33-kmp-exit-counting-scope.md` — PROPOSED, UNRESOLVED,
no implementation authority. `tests/test_kmp_exit_counting_scope_20261027.py` (14 tests)
pins the current rule issuer-neutrally: verified KMP exit, non-KMP board exit, mixed table,
duplicate rows, unrecognised designation, window boundaries, UNKNOWN-not-zero anchor,
builder derivation, criterion bucket.

---

## 5. Evidence-backed Regulation 17(1)(c) disposition

**The quotes were independently re-extracted this pass with `pypdf` and are verbatim with
correct page attribution.** The reader's provenance is sound.

* **Jio Platforms**, printed **p. 105** (PDF index 104),
  `evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`:
  > In terms of Regulation 17 (1)(c) of the SEBI ICDR Regulations, equity shares held by a
  > VCF or Category I AIF or Category II AIF or FVCI shall not be locked-in for a period of
  > six months from the date of Allotment, provided that such equity shares shall be locked
  > in for a period of at least six months from the date of purchase by such shareholders.
* **Paras Healthcare**, printed **p. 117** (PDF index 116),
  `evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf`:
  > …will be locked-in for a period of six months from the date of Allotment, except for …
  > (iii) the Equity Shares held by a VCF or a Category I AIF or a Category II AIF or a
  > FVCI, provided that such Equity Shares will be locked-in for a period of at least six
  > months from the date of purchase by the VCF or Category I AIF or Category II AIF or
  > FVCI shareholders.

**What the text establishes:** the general six-months-from-Allotment lock-in is removed for
the named categories and a *minimum* six months from **purchase** is imposed — a different
commencement date. **What it does not establish:** when those holders purchased. That date
decides whether the carve-out produces a release earlier than the general rule, at the same
time, or later. The flag as currently set therefore asserts a release the filing does not
evidence.

**Disposition: the carve-out alone must not set the flag; insufficient evidence must remain
UNKNOWN.** Without evidence of an actual early release (a dated lock-in table listing which
holders are released and when, or an explicit statement of early release),
`capital_structure.large_holders_unlocked_early` stays `null` and C `lockin` stays UNKNOWN.

**Authority boundary.** A32 (2026-10-26) states the field "have no reader" and that whether
an engine may ever establish it from a filing "is a policy question (A21/A25 family), not an
extractor improvement"; A32 is `READY FOR RAMKI RATIFICATION (NOT RATIFIED)` and asserts
"no authority is asserted over any scoring artefact". PR #13 implemented the reader anyway.
The reader and its 17-test matrix are **preserved unchanged** per the governing instruction;
the open question is recorded rather than resolved in code.

**Measured effect if the recommendation is adopted:** Jio and Paras each move C `lockin`
from SCORED 0 (`weak`) to UNKNOWN (one point moves from scored to available); no weight,
boundary, threshold, penalty or knockout moves.

**Recorded in** `handoff/decisions/A34-early-unlock-carve-out-semantics.md` — PROPOSED,
UNRESOLVED, no implementation authority.

---

## 6. Governance decisions

### A33 — `kmp_exits_2y` counting scope (`handoff/decisions/A33-kmp-exit-counting-scope.md`)

* **Recommendation:** retain the current rule — count every dated exit the reader
  established from the changes-in-directorate table, no role filter.
* **Rationale:** it is the merged, documented, four-issuer-validated rule; `role` is an
  extraction field whose absence is not evidence about the person; B1 destroys disclosed
  evidence; B2 buys nothing.
* **Alternatives:** A status quo (recommended); B1 strict KMP role (measured: Jio 6→1,
  Paras 4→0, both +1); B2 fail-closed on an unrecognised role (measured: Jio 6→2, Paras 4→4,
  no change); C rename/split the field (separate schema decision).
* **Affected contracts/fields:** `governance.kmp_exits_2y`, `governance.board_changes`,
  `derived.board_kmp_bucket`, `derived_metrics.board_kmp_bucket` formula wording, the D
  `board_kmp` criterion.
* **Status:** PROPOSED / UNRESOLVED. **No implementation authority.**

### A34 — Regulation 17(1)(c) and `large_holders_unlocked_early`
(`handoff/decisions/A34-early-unlock-carve-out-semantics.md`)

* **Recommendation:** a category carve-out alone must not set the flag. Set it only on
  evidence of an actual early release; otherwise the field stays `null` and C `lockin`
  stays UNKNOWN.
* **Rationale:** the carve-out states a purchase-anchored *minimum*, not a release; the
  purchase dates are not printed; an UNKNOWN is honest and recoverable, a wrongly-set flag
  is not; the reader's own fail-closed boundaries already refuse the same inference
  elsewhere.
* **Alternatives:** A carve-out alone sets the flag (status quo, preserved pending the
  decision); B carve-out never sets it (recommended); C add a separate structured field for
  the carve-out; D require the purchase date (rejected — the filing does not print it, so
  the flag would be unreachable).
* **Affected contracts/fields:** `capital_structure.large_holders_unlocked_early`,
  `derived._lockin_bucket`, the C `lockin` criterion, `schema/ipo-input.v1.5.schema.json`.
* **Status:** PROPOSED / UNRESOLVED. **No implementation authority.** Depends on
  ratification of A32, which remains `NOT RATIFIED`.

---

## 7. Changed files and commit SHAs

| File | Change |
|---|---|
| `handoff/decisions/A33-kmp-exit-counting-scope.md` | **new** |
| `handoff/decisions/A34-early-unlock-carve-out-semantics.md` | **new** |
| `tests/test_kmp_exit_counting_scope_20261027.py` | **new** (14 tests, synthetic tier) |
| `docs/investigation/JIO-34-GLOBAL-ARCHITECTURE-DISPOSITION-2026-10-27.md` | §6.3(i), §6.3(ii), §8 corrected |
| `docs/investigation/LOCKIN-INSTITUTIONAL-CARVEOUT-GENERALITY-2026-10-27.md` | §2 inference withdrawn, §5/§6 full-suite figure corrected, §6 semantic-scope limitation added |
| `docs/investigation/PARAS-UNKNOWN-TRIAGE-2026-10-27.md` | §3 corrected to "discloses the carve-out", A34 pointer |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` | Revision 30 added |
| `docs/investigation/BROAD-REMEDIATION-CONSOLIDATED-DISPOSITION-2026-10-27.md` | **new** (this report) |

**No `engine/`, `config/`, `schema/`, `frontend/` or frozen-core file was changed.**
The single engine change in PR #13 (`engine/ipo_screening/extraction/sections.py`, +66) is
untouched.

Commit: **one commit** with subject `docs(governance): record the kmp_exits_2y and Reg
17(1)(c) decisions`, on `arena/342ccacc-ipo-screening-engine` directly on top of the PR #13
tip `4636346` (a plain push — no force was needed, because the remote had not moved). The
SHA is deliberately **not** written into this report: self-referential SHA pinning caused
three earlier mismatches when the commit was amended. The SHA is stated in the session
record and verifiable with `git rev-parse HEAD`. Remote HEAD is verified equal to local HEAD
after the push, and PR #13's `headRefOid` is verified to track the tip.

---

## 8. Focused, tier-gate and full-suite results

**Focused (this pass):**

```
tests/test_kmp_exit_counting_scope_20261027.py                  14 passed   (0.05s)
tests/test_jio_current_engine_result_20261027.py                 3 passed   (29.3s)
tests/test_suite_tiers.py                                         1 passed   (0.0s)
                                                           ----
                                                                      18 passed  (29.8s)
```

**Tier gate:** `tests/test_suite_tiers.py::test_real_file_and_ingestion_modules_have_an_explicit_tier`
green. The new module is not in `INTEGRATION_MODULES` and does not mention `ingest_document`,
so it correctly runs in the fast synthetic tier.

**Full backend suite:** `pytest tests/ -q` → **2183 passed, 0 failed, 25 warnings in
1462.48s (0:24:22)**. The 14-test increase over the previously recorded 2169 is exactly
`tests/test_kmp_exit_counting_scope_20261027.py`; no other module changed. No engine file
was touched, so the frozen-core pins (`verify_frozen_core()`, `verify_golden_result()`) are
unaffected.

---

## 9. Jio and Paras reproducibility

### Jio Platforms

| | Published 34.0 record (`jio-fresh-20261023/final-retained`) | Current engine (`jio-current-engine-probe-20261027`, pinned by test) |
|---|---|---|
| final / base / penalty | 34.0 / 34.0 / 0.0 | **37.0 / 37.0 / 0.0** |
| completeness | 57.0% | **63.0%** |
| verdict | `INSUFFICIENT_DATA` (band `AVOID`) | **`AVOID`** |
| `kmp_exits_2y` | **`null`** → `board_kmp` UNKNOWN | **6** → `board_kmp` SCORED 0 `high_churn` |
| `large_holders_unlocked_early` | `false` (builder default, pre-A32) | **`true`** → C `lockin` SCORED 0 `weak` |
| `promoter_pledge_pct` | `0.0` (builder default, pre-A32) | **`null`** |
| knockouts | K1/K2/K5 UNVERIFIED | **K2 TRIGGERED** |
| modules | A 17 / B 1 / C 11 / D 5 / E 0 / F 0 | A 17 / B 1 / C 10 / D 9 / E 0 / F 0 |

Reproduced by `tests/test_jio_current_engine_result_20261027.py` (3 passed), which pins the
20 divergent files, the published 34.0 record and the current 37.0/AVOID/K2 result. The
34.0 → 37.0 delta is **not** a scoring change: the probe resolved issue terms with
`IssueTermsResolver(providers=[])` plus five manual terms and supplied no market block, so
Modules C/D move while B/E/F stay blocked. This is the documented environmental restriction,
not a defect.

### Paras Healthcare (reproduced end-to-end this pass)

Rebuilt from `evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf`
(651 pages, sha256 `e0a3187f…`, asserted by the existing regression module) through
`DocumentExtractor` → `CanonicalInputBuilder` → `pipeline.evaluate(mode="final")`, with the
identity-bound issue terms (band 660/693, lot 21) supplied separately.

| Field | Reproduced |
|---|---|
| final / base / penalty | **13.0 / 16.0 / −3.0** |
| completeness | **44.21%** |
| verdict | **`AVOID`** |
| knockouts | **K5 TRIGGERED**; K1/K2 UNVERIFIED |
| C `lockin` | **SCORED 0.0 `weak`** |
| D `board_kmp` | **SCORED 0.0 `high_churn`** |
| `kmp_exits_2y` | **4** (`DISCLOSED`) |
| `large_holders_unlocked_early` | **`true`** |
| `promoter_lockin_in_place` | **`true`** |

This matches `PARAS-UNKNOWN-TRIAGE-2026-10-27.md` §1 and §3 byte for byte on every value it
pins (13.0 / 16.0 / −3.0 / 44.21% / AVOID / K5 / lockin SCORED 0 weak), so the post-change
record is a faithful reproduction. The one honest difference from the pre-change pinned
record is completeness 43.16% → 44.21%, caused by `lockin` moving UNKNOWN → scored-0 — the
change the lock-in reader introduced, and the one A34 now questions.

---

## 10. Remaining limitations and precise next action

**Limitations (all recorded, none hidden):**

1. **A33 is unresolved.** The `kmp_exits_2y` scope is a definitional question with a
   measured recommendation; no code change is authorized by this pass.
2. **A34 is unresolved, and A32 is unratified.** The Regulation 17(1)(c) question belongs
   to A32's policy family; the reader stands but its justification is open.
3. **Role recovery is incomplete.** The reader returns `role: null` for every row of a table
   with no designation column (Paras p. 357) and for several Jio rows. This is the follow-up
   that would make the count auditable — an extractor improvement, not this decision.
4. **Module B is blocked on peer data** for both issuers: Jio has two `VALID` peers but no
   second multiple and no recent same-sector IPO series; Paras has no peer block at all.
   `second_multiple` and `sector_ipo_relative` stay UNKNOWN; no substitution is authorized.
5. **Module E is blocked on assessment inputs** (`moat_rating`, `visibility_rating`);
   **Module F is blocked on a market-observation block** for both issuers. Neither is an
   adapter defect and neither was simulated.
6. **Paras's required blocks** (post-issue share count; the actual GCP amount; per-seller
   OFS share counts; the MRPT basis D-35) remain genuinely absent from the filing.
7. **The 34.0 → 37.0 Jio delta is partially environmental**, as stated in §9; the probe is
   not a like-for-like rerun of the published record.
8. **Page scope.** The lock-in reader scans the TOC-routed capital-structure range; a
   carve-out printed elsewhere (Moneyview p. 485) is recognised at rule level only.

**Precise next action:**

RAMKI to decide **A33** and **A34**. Recommended answers: **retain the current `kmp_exits_2y`
rule** (no role filter), and **do not set `large_holders_unlocked_early` from a category
carve-out alone** (leave it `null` → C `lockin` UNKNOWN absent evidence of an actual early
release). On either decision, the corresponding test module is the regression baseline and
the measured impact is already recorded in §4 and §5. If A34 is answered in favour of the
recommendation, the reader change is one guard in
`engine/ipo_screening/extraction/sections.py::extract_capital_structure` and its
17-test matrix — **and it must be ratified first, because A32 explicitly withholds authority
over this artefact and is itself unratified.**

**Verdict: GOVERNANCE DECISION REQUIRED — IMPLEMENTATION BLOCKED ONLY AT THE IDENTIFIED BOUNDARY.**
