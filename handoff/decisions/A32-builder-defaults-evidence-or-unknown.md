# A32 — Capital and Governance Defaults in the Builder: Evidence or UNKNOWN

- **Decision ID:** A32
- **Title:** the builder must not supply a favourable constant for a capital-structure or governance field it did not read
- **Record type:** **IMPLEMENTATION RECORD under an already-approved principle.** Per `handoff/decisions/CONVENTION.md` rule 4, the principle is A22/A23/Step-4-Area-B(i)'s ("missing evidence is UNKNOWN, never a favourable default" and "a quotation the engine wrote is not evidence"); this record states how that principle was applied to five builder fields, and what it cost two real filings. It creates no new policy, criterion, weight or threshold.
- **Decision status:** **APPROVED / RATIFIED BY RAMKI 2026-10-28; IMPLEMENTED 2026-10-26; FULL BACKEND SUITE EXECUTED.**
- **Decision authority:** RAMKI. The principle was approved in A22 (2026-10-20) and A23 (2026-10-21); RAMKI explicitly ratified this application on 2026-10-28.
- **Date:** 2026-10-26 (Asia/Calcutta); no decision time is asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/79aac867-ipo-screening-engine`, from `main` `96379ab597524878582a7c6abfa131eec67a04b4`.
- **Scope:** `engine/ipo_screening/extraction/builder.py::_build_capital_structure`, `_build_governance`; the readers in `extraction/sections.py` that supply those fields; and the four test expectations that encoded the defaults.
- **Out of scope and unchanged:** every weight, threshold, penalty, band, criterion definition and knockout; `config/ipo-config.v1.5.0.json` and `v1.6.0`; `schema/`; `derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`, `price_band_notice.py` (frozen core); the golden record; every historical evaluation.

## 1. What the builder was doing

When the extraction produced no value, `CanonicalInputBuilder` supplied a constant:

| Field | Constant | What it cleared | Evidence in the filing |
|---|---|---|---|
| `capital_structure.promoter_pledge_pct` | `0.0` | K2's pledge limb (`pledge > 25%`) | p. 114: *"none of the Equity Shares held by our Promoter are pledged"* |
| `capital_structure.promoter_lockin_in_place` | `True` | C `lockin` (1 pt) | p. 116: *"locked in for a period of three years"* |
| `capital_structure.large_holders_unlocked_early` | `False` | C `lockin` (1 pt) — it is the second leg of `lockin_bucket` | not disclosed in these filings |
| `capital_structure.discounted_allotments_18m_before_drhp` | `False` | the `heavy_discounted_allotments_18m` penalty | not disclosed |
| `governance.board_independent_majority` | `False` | D `board_kmp` (2 pts) — unfavourable, but equally unevidenced | p. 337: *"seven Directors … three are Independent Directors"* |

Each constant was a default in the ordinary sense: when the reader failed, the builder
supplied the answer that scores best (or, for the board, the answer that scores worst). The
score did not depend on the document at all.

## 2. The rule applied

> A capital-structure or governance field is present in the canonical input only when a
> reader established it from the filing. Otherwise the field is absent, the dependent metric
> is UNKNOWN, and the criterion is unscored — its points move from *available* to *unknown*
> rather than being awarded or denied.

This is A22's rule (`auditor_changed_3y` / `repeated_eom`: evidence-or-UNKNOWN) applied to
the rest of the block. Nothing about the criteria, their bands or their maps changes: the
schema already admits `null` for all five fields and every consumer already treats `None` as
UNKNOWN (`canonical_input.flag` returns `None`, `_lockin_bucket` returns UNKNOWN, K2 leaves
the leaf unverified).

The constants remain available on the **synthetic template path**
(`allow_fixture_fallbacks=True`), where a reference base is supplied on purpose and a
template's values are the intended input. Only the strict real-filing path fails closed.

## 3. What made the constants removable in the same pass

Removing a default without adding the reader would have converted five answers into five
unknowns. The readers were repaired first (each in `sections.py`, each with a verbatim
quotation and the page actually matched):

- **Pledge** — the pattern required the plural (`our promoters are pledged`); Paras, with a
  single promoter, says *"none of the Equity Shares held by our Promoter are pledged"*. Both
  numbers and both copulas are now accepted.
- **Lock-in** — only `locked in for a period of <term>` was accepted, so *"locked in for a
  period of three years"* read but a plain *"locked in for three years"* or *"locked-in for
  3 years"* did not. All three forms are read.
- **Auditor continuity** — the sentence *"There has been no change in our statutory auditors
  in the last three years"* (p. 99) names no firm, and it was only read inside the branch
  that had already captured the firm's name. It is now an independent observation, emitted
  outside that branch.
- **Board composition** — the counts are spelled in words (*"we have seven Directors … of
  whom … three are Independent Directors"*). Word numbers are mapped; both counts are
  required; the field is emitted only when the composition sentence is read.

`large_holders_unlocked_early` and `discounted_allotments_18m_before_drhp` have **no reader
yet** and these filings do not state either fact, so they are now UNKNOWN on the strict path.
That is the honest state, not a gap in the readers: an early release of a pre-IPO holder's
shares is not something a filing's silence can establish.

## 4. Consequences — including the ones that cost points

- **Two real filings' pinned scores moved down by one point each**, because neither states an
  early unlock and both previously earned C `lockin` from the `large_holders_unlocked_early =
  False` default:
  - R.K. Fashion Accessories: final 44.0 → **43.0**, base 47.0 → **46.0**, completeness
    67% → **66%**, lower bound 31.0 → **28.0**, Module C 10 → **9**.
  - Aurora ingestion case (`complete_sample_rhp.pdf`): final 18.0 → **17.0**,
    completeness 67% → **66%**.
  Four expectations were corrected, each with the reason written at the assertion
  (`tests/test_rk_fashion_reconciliation.py`, `tests/test_ui7_ingestion.py`). No assertion was
  weakened, none converted to a skip, none removed.
- **Paras (retained, non-authoritative):** the pledge, the lock-in and the board composition
  are now evidenced (so the board's *unfavourable* default became an evidenced finding), and
  the auditor continuity point is earned from p. 99. The lock-in point is lost to the
  unavailable second leg. Net effect on the run is recorded in the report §22.6 — the number
  was not the target.
- **K2 does not become CLEAR.** Removing the pledge default removes a *cleared limb*, not the
  knockout's requirement: `sebi_ed_action_active` is still UNKNOWN on Paras, so K2 stays
  UNVERIFIED. A filing that states neither the pledge nor a regulator denial leaves K2
  unverified, which is what A23 asked for.
- **The board field is a two-way case.** Its default was `False` — the unfavourable answer —
  and the old code emitted it with a quotation of its own making. Both halves were wrong for
  the same reason: an unread section is not a finding in either direction.

## 5. Verification

- `tests/test_reading_defects_20261026.py` — **28 passed** (synthetic, instant), including
  `test_capital_and_governance_absent_evidence_stays_absent` and
  `test_fixture_fallbacks_are_still_available_to_the_template_path`.
- Affected suites (Paras evidence / gaps / issue terms, acceptance matrix, v16 implementation,
  frozen-core line endings, R.K. reconciliation, UI7 ingestion) — all green on the final code.
- Full backend suite: **1,970 collected → 1,969 passed / 1 failed** on first run (the tier
  inventory rejecting the new synthetic module; listed, then green), and green on re-run.
- Frozen core untouched; `test_frozen_core_line_endings` and `test_v16_implementation` pass;
  the Vishal golden result hash still reproduces.

## 6. Unresolved dependencies

1. **RESOLVED 2026-10-28:** RAMKI ratified this application of A22/A23.
2. **`large_holders_unlocked_early` and `discounted_allotments_18m_before_drhp` have no
   reader.** Whether an engine may ever establish them from a filing at all — for example
   from a lock-in table that lists which holders are released early — is a policy question
   (A21/A25 family), not an extractor improvement.
3. **`governance.auditor_reputed` still emits a synthesised quotation**
   (`"Auditor: <name>, reputed network: True"`). The value is a judgement about the firm's
   reputation, not a filing statement, so the fix is a *stated basis* rather than a quote;
   left unchanged in this pass and recorded.
4. `rpt_pct_revenue` now quotes the filing's own row instead of a synthesised sentence, but
   the metric it feeds is still deliberately unfed (the approved definition does not exist).

## 7. Implementation authority

**Granted for this branch only, as the implementation of the approved A22/A23 principle**;
**no authority is asserted over any scoring artefact.** RAMKI ratified the recorded application
on 2026-10-28; that ratification does not enlarge this implementation scope.
