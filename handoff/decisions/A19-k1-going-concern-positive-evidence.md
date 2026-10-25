# A19 — K1 Going-Concern Input: Positive Evidence Only; Negative-Confirmation Rule Deferred

- **Decision ID:** A19 (decision **D-1** of the HD Fire / Jio decision set)
- **Title:** `governance.going_concern_uncertainty` is established only by positive evidence
- **Decision status:** RAMKI-APPROVED POLICY. No negative-confirmation rule is approved.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Authorization basis:** Ramki's direct 2026-10-20 instruction approving the D-1 recommendation: *"Retain evidence-backed, positive-only detection and UNKNOWN when the evidence is absent, negated, or insufficient. Defer introducing a general negative-confirmation rule. An unmodified audit opinion alone must not establish that going-concern uncertainty is absent."* The instruction also requires this record to identify the evidence-coverage and false-negative analysis needed before such a rule can be reconsidered.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/ae4d04e8-ipo-screening-engine` at remotely verified commit `7754f9b397696e72ab025eca964325aa074f2796`.
- **Scope:** the `governance.going_concern_uncertainty` input, its extraction, and knockout K1's use of it.
- **Implementation authority:** GRANTED only for retaining and verifying the polarity guard already published in `e2ce2c2`. No new extraction path, no `False` emission, no K1 rule change.
- **Publication status:** recorded in the authoritative tracker; the implementation commit is identified there.

## Decision

1. `going_concern_uncertainty` is **true** only when the auditors' report contains positive
   going-concern uncertainty language (material uncertainty / significant doubt about the
   entity's ability to continue as a going concern).
2. A **negated** statement ("there is no material uncertainty related to going concern"), an
   **absent** going-concern paragraph, or an **unmodified opinion alone** does not establish
   that uncertainty is absent. The field stays `None` (UNKNOWN).
3. UNKNOWN passes through the Kleene knockout evaluation as **K1 UNVERIFIED**. K1 cannot be
   CLEARed by the absence of evidence, and a negation is never converted to `False`.
4. No synthetic citation or processing quotation is attached to a field that was not found.
5. A general **negative-confirmation rule is deferred**. It may be reconsidered only after
   the prerequisites in "Deferred work" are satisfied and separately approved.

## Rationale

- ISA 570 requires a separate statement when a material uncertainty exists; an unmodified
  opinion is therefore **not** evidence of its absence.
- Before `e2ce2c2`, the phrase regex matched the standard *negative* confirmation and emitted
  `True`, triggering K1 on the opposite of the disclosed fact. That was a polarity defect, not
  a missing rule, and it is corrected.
- The engine's own contract for this field is already evidence-positive: the schema allows
  `boolean | null`, the derived metric treats absence as UNKNOWN, and K1's `any` tree cannot
  resolve to CLEAR from an UNKNOWN leaf.
- Converting absence into `False` would be a **new governed rule** with a coverage boundary
  (which pages, which reports, which subsidiaries) and a false-negative risk, not a bug fix.

## Scope

- `engine/ipo_screening/extraction/sections.py`: `_going_concern_uncertainty_match()` is the
  only consumer of `_GOING_CONCERN_UNCERTAINTY` (verified by `grep`).
- `engine/ipo_screening/extraction/builder.py`: `_pick_gov("going_concern_uncertainty", None)`.
- `engine/ipo_screening/derived.py`: passthrough metric; absent ⇒ UNKNOWN.
- `config/ipo-config.v1.5.0.json` K1 (unchanged).

## Explicit exclusions

- No change to K1's `required` list, `when.any` tree, Kleene semantics, or scoring.
- No change to the auditor-opinion resolver.
- No negative-confirmation rule, no `False` emission, no "no going-concern paragraph found"
  shortcut.
- No change to config, schema, fixtures, golden hash or historical evaluations.

## Implementation implications

None beyond the already-published `e2ce2c2` guard. The guard rejects a phrase match whose
120-character sentence prefix or sentence tail is a negation (`there is no`, `we did not
identify`, `no material uncertainty`, `without … uncertainty`, `none`, `no longer`,
`no such`), while an unrelated negative word ("No doubt, there is a material uncertainty …")
does not suppress a genuine disclosure.

## Verification evidence

Executed on the final tree of the 2026-10-20 governance pass:

| Check | Result |
|---|---|
| `tests/test_going_concern_negative_disclosure.py` | **8 passed** — positive phrase detected; five negative phrasings not emitted; measurement-basis phrase not emitted; unrelated "No doubt" still emitted |
| `tests/test_auditor_evidence_section.py` | positive / absence / live-Jio controls pass |
| `grep -rn "_GOING_CONCERN_UNCERTAINTY" engine/` | two hits only, both in `sections.py`: the definition and its single call site inside `_going_concern_uncertainty_match`; no bypassing consumer |
| Jio live filing | unqualified opinion, no going-concern paragraph ⇒ `None`, **K1 UNVERIFIED** |
| HD Fire | no source inspected ⇒ `None`; K1 unverified |
| Full backend suite (`pytest tests -q`, final tree) | **1192 passed, 0 failed, 0 xfailed**, 38 warnings, 1566.58 s (baseline `7754f9b`: 1179 passed, 1 xfailed, 1542.57 s) |

Controlled evaluation: flag `True` ⇒ K1 TRIGGERED / verdict AVOID; flag `None` ⇒ K1 UNVERIFIED
/ INSUFFICIENT_DATA; **score unchanged** in both runs.

## Deferred work — prerequisites before a negative-confirmation rule can be reconsidered

1. **Evidence-coverage definition:** the exact set of documents and pages that must be scanned
   (auditors' report, CARO annexure, notes, subsidiary reports), and how a partial/changed
   filing is detected.
2. **Required language specification:** the exact auditor wording (or combination) that would
   count as an explicit negative confirmation, and the treatment of "no material uncertainty"
   in a management/notes section versus the auditors' report.
3. **False-negative analysis:** measurement, on a sample of filings with a going-concern
   paragraph, of how often the paragraph would be missed by the scanner — a rule may only be
   adopted if that rate is established and acceptable.
4. **Re-score decision:** whether existing UNVERIFIED K1 states would be recomputed, and how
   historical records are left immutable while new runs use the new rule.

## Limitations and unresolved blockers

- HD Fire's auditor report and RHP remain unavailable. No claim is made that HD Fire has no
  going-concern uncertainty; its K1 stays UNVERIFIED.
- The guard is conservative: an unrelated negative word inside the same sentence window
  suppresses a positive disclosure to UNKNOWN. That direction is deliberate (a missed trigger,
  never a false CLEAR).
