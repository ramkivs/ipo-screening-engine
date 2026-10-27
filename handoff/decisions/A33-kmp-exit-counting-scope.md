# A33 — The scope of `kmp_exits_2y`: KMP exits only, or every exit in the changes-in-directorate table

- **Decision ID:** A33
- **Title:** what counts as an "exit" for `governance.kmp_exits_2y` — and why the answer must not be changed by an extractor
- **Record type:** **OPEN DECISION INVESTIGATION.** No decision is recorded and no
  code change is made or authorized by this record. Per `handoff/decisions/CONVENTION.md`
  rules 4 and 6, this is an investigation of an ambiguity, with a recommendation; it is
  not an approval of that recommendation and it grants no implementation authority.
- **Decision status:** **PROPOSED / UNRESOLVED (not implemented).**
- **Decision authority:** RAMKI.
- **Date:** 2026-10-27 (Asia/Calcutta); no decision time is asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/342ccacc-ipo-screening-engine`, from `main`
  `69a9ff9d77c9886a1b30c31ed327d5a9d747a1a7` (the merge of PR #12).
- **Scope:** the meaning of `governance.kmp_exits_2y`, its producers
  (`engine/ipo_screening/extraction/directorate.py`, `engine/ipo_screening/extraction/builder.py`),
  its consumers (`engine/ipo_screening/derived.py::_board_kmp_bucket`, `config/ipo-config.v1.5.0.json`,
  the D `board_kmp` criterion), and the documentation that describes it.
- **Out of scope and unchanged:** every weight, threshold, penalty, band and knockout;
  `config/ipo-config.v1.5.0.json` and `v1.6.0`; `schema/`; the frozen-core pin on
  `engine/ipo_screening/derived.py` (`7783dfeb…`); every historical evaluation record.

---

## 1. The question

The criterion is named for Key Managerial Personnel and its metric formula says "KMP
exit". The input that feeds it is read from a table that carries **both** board rows and
KMP rows under one caption. So:

> Does `governance.kmp_exits_2y` count *only* exits by Key Managerial Personnel
> (CEO/MD/WTD/CFO/Company Secretary/Manager), or every dated exit the reader
> established from the changes-in-directorate table?

This is the question `docs/investigation/JIO-33-FINAL-EVIDENCE-RECOVERY-2026-10-23.md`
recorded as **GOVERNANCE_DECISION_REQUIRED for counting**, and the one
`docs/investigation/JIO-34-GLOBAL-ARCHITECTURE-DISPOSITION-2026-10-27.md` §6.3(i) and
§8(1) present without a decision.

## 2. What the code does today (verified, not inferred)

* `engine/ipo_screening/extraction/directorate.py::count_exits` (line 528) counts every
  event whose `event` is in `_EXIT_EVENTS = {resignation, cessation, retirement,
  term_expiry}` (line 217) whose date falls in the 24 calendar months ending at the
  anchor, inclusive at both ends (line 548). **It does not consult `role` at all.**
* The builder (`engine/ipo_screening/extraction/builder.py::_derive_board_changes`)
  persists the dated events on `governance.board_changes` and derives the count against
  the offer open date (close date, then listing date, as fallbacks); an unread table
  leaves the count `null` (UNKNOWN), never `0`.
* `schema/ipo-input.v1.5.schema.json` describes the source as *"Dated **director /
  key-managerial-personnel events** read from the changes-in-directorate table."*

So today the count is **every exit in the table**, board or KMP.

## 3. What the governing contracts say

| Source | Wording |
|---|---|
| `config/ipo-config.v1.5.0.json` → `derived_metrics.board_kmp_bucket` | "independent_stable: independent-majority board, **no KMP exit in 2Y**; high_churn: **>=2 KMP exits in 2Y**; else other" |
| `handoff/reference/Claude_IPO Screening Engine v 1.3 — Specification.md` line 106 | "Board independence & KMP stability \| 2 \| Independent-majority, stable = 2; **high KMP churn** = 0" |
| `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §4.3 | lists "KMP changes", "board composition", "independent-director count", "CFO changes/resignations" as separate required inputs, and defines no criterion row |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` Revision 25 (2026-10-26, PR #12, merged to `main` as `69a9ff9`) | the reader was implemented and cross-issuer validated: Vishal 18 rows (9 board + 9 KMP) → **0**; R.K. Fashion 1 row → **0**; Paras 14 rows (7 board + 7 KMP) → **4**; **Jio 17 rows → 6**. "Both adverse moves are evidence-driven …; no threshold was touched." |

The formula's words say "KMP exit"; the merged implementation and its cross-issuer
validation count the whole table. The two are not reconciled anywhere in the repository,
which is why this is a decision and not a bug fix.

## 4. Measured impact — three variants, computed on the real tables

`role` is the only per-row category the reader records, so any KMP-only rule must key on
it. Three variants were computed against the four filings the tracker validated:

| Issuer / table | rows | current | **B1** strict KMP role | **B2** KMP role **or** unrecognised role |
|---|---|---|---|---|
| Jio Platforms (anchor 2026-10-21) | 17 | **6** | **1** | **2** |
| Paras Healthcare — board p. 346 | 7 | 0 | 0 | 0 |
| Paras Healthcare — KMP p. 357 | 7 | **4** | **0** | **4** |
| Vishal Nirmiti — board p. 306 | 4 | 0 | 0 | 0 |
| Vishal Nirmiti — KMP p. 319 | 4 | 0 | 0 | 0 |

* **B1 (strict role filter)** drops five of Jio's six in-window exits (four board-role
  resignations and one whose designation the reader did not recover) and **all four** of
  Paras's. Both filings fall below the ≥2 boundary: `board_kmp` moves `high_churn` →
  `other`, i.e. **0 → 1 point each**. It converts disclosed churn into an unverified
  count.
* **B2 (the rule the disposition report describes — skip a *known* non-KMP designation,
  count an unrecognised one fail-closed)** gives Jio 2 and Paras 4. **No filing's bucket
  changes**, because both remain ≥2. The disposition report's estimate ("effect on Jio:
  none") is correct **under B2**.

B2 is therefore low-impact but still not free: it makes the count depend on whether the
reader happened to recover a designation, and it leaves the field's name meaning something
other than what the metric formula says.

## 5. Recommendation

**Retain the current rule.** `kmp_exits_2y` counts every dated exit the reader
established from the changes-in-directorate table, without a role filter.

Rationale:

1. It is the rule that was implemented, merged to `main` in PR #12, documented in
   tracker Revision 25 and validated on four real filings.
2. **`role` is an extraction field, and its absence is not evidence about the person.**
   The Paras KMP table prints no designation column, so the reader leaves `role` null on
   every row; B1 therefore returns zero for a table that discloses four resignations.
   Keying a *count* on a field whose absence is an extraction artifact turns an extraction
   limitation into a scoring outcome.
3. The criterion is `board_kmp` — "Board independence & **KMP stability**" — and the
   schema names its source "director / key-managerial-personnel events". Counting the
   table the schema names is consistent with both.
4. B2 would leave the current numbers unchanged, so it buys nothing but a rename of the
   rule; B1 destroys evidence. Neither is worth a change to a merged behaviour.

**Follow-up (recommended, separate decision):** the real defect is not the scope but the
**role recovery**. The reader returns `role: null` for every row of a table with no
designation column (Paras p. 357) and for several Jio rows. Improving role recovery —
taking the designation from the reason text, as it already does for Vishal p. 306 — would
make the count *more* auditable without changing what it counts. That is an extractor
improvement and does not require this decision.

## 6. Alternatives considered

* **A. Status quo (recommended).** Count the table; no role filter. No score change.
* **B1. KMP-only by recognised `role`.** Measured: Jio 6 → 1, Paras 4 → 0, both moving
  `board_kmp` from `high_churn` to `other` (+1 each). Rejected: it discards disclosed
  evidence, and it makes the count depend on a field whose absence is an artifact.
* **B2. KMP-only, fail-closed on an unrecognised role** (the disposition report's rule).
  Measured: Jio 6 → 2, Paras 4 → 4, no bucket change. Rejected: no measured benefit, and
  the count still keys on `role`.
* **C. Rename or split the field** (e.g. `directorate_exits_2y`) so the name matches the
  count. Recorded, not recommended now: it is a schema/canonical-input change that would
  invalidate every retained record's `field_map` and is a separate decision.

## 7. Consequences and constraints

* No code, schema, config, test expectation or historical record is changed by this
  record.
* `tests/test_kmp_exit_counting_scope_20261027.py` (new, 14 tests, synthetic tier) pins
  the current rule issuer-neutrally — including the non-KMP board exit, the mixed table,
  duplicate rows, an unrecognised designation, the window boundaries and the
  UNKNOWN-not-zero anchor — so the pending decision has a regression baseline and any
  future change is measured against it. The module states explicitly that it records
  what the engine does, not that the KMP-only reading is wrong.
* `docs/investigation/JIO-34-GLOBAL-ARCHITECTURE-DISPOSITION-2026-10-27.md` §6.3(i) is
  corrected where it names the two Jio exits a KMP-only rule would retain: they are the
  CEO resignation and the one exit whose designation the reader did not recover — not a
  Company Secretary resignation, which does not occur in Jio's window. §6.3(i) and §8(1)
  now cite this record and state the B1/B2 distinction.

## 8. Unresolved dependencies

1. **RAMKI's decision** on the scope question. Recommended answer: retain the current
   rule (alternative A).
2. Whether the metric formula's words ("KMP exit") should be amended to match the count,
   or the count changed to match the words. That amends a criterion definition and is not
   this record's authority.
3. The role-recovery improvement (§5) is an extractor change and needs its own
   verification pass; it is not authorized here.

## 9. Implementation authority

**Not granted.** This record is an investigation with a recommendation. No change to
`kmp_exits_2y`, its producers, its consumers or its documentation is authorized by it.
