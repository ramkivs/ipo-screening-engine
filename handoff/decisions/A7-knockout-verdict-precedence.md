# A7 — Knockout and Verdict Precedence

- **Decision ID:** A7
- **Title:** Verified-knockout outcome, evaluation-result representation and unverified-knockout handling
- **Status:** RAMKI-APPROVED PROJECT DECISIONS (original Tasks 15/16; A7-D1 and A7-D2 approved in Task 18); OUTPUT CONTRACT PARTIAL. v1.5 does not prescribe the exact result representation or map a verified `TRIGGERED` knockout to `AVOID`.
- **Decision authority:** RAMKI
- **Decision dates:** Original core decision: 2026-10-09; A7-D1 and A7-D2 approvals: 2026-10-10 (Asia/Calcutta).
- **Decision source / authorization evidence:** Ramki's explicit A7 approval in principle in TASK 15 and approved outcome-precedence direction in TASK 16; Ramki's explicit approval of A7-D1 and A7-D2 in the TASK 18 instruction received 2026-10-10 (Asia/Calcutta).
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** Original decision baseline: branch `arena/4e1080b7-ipo-screening-engine`, pre-record commit `01ba66c12ca1195fd7acbd287c3e39a019808094`. Task 18 amendment baseline: the same session branch at published Task 16 commit `abaac15ed3ffbb4b951c1b3f00b9d725b3ebbc07`.
- **Scope:** Final-outcome precedence, distinct representation of evaluation results and diagnostics, unverified-knockout handling, score-range uncertainty and missing critical safety evidence.
- **Implementation authority:** NOT GRANTED. This decision does not authorize Phase 1 or application implementation.

## Original approved decision text (Tasks 15/16; retained)

1. A verified, applicable knockout takes precedence over numerical scoring.
2. A verified, applicable knockout produces the final outcome `AVOID`.
3. Missing critical safety evidence remains explicitly recorded and is never treated as verified or clear.
4. When score-range uncertainty applies, preserve `VERDICT_UNCERTAIN` as a scoring diagnostic; it does not override a verified knockout.
5. When no verified knockout exists but critical safety evidence is missing, use `INSUFFICIENT_DATA` rather than issuing `AVOID` merely because evidence is incomplete.
6. An `UNVERIFIED` knockout is neither `TRIGGERED` nor `CLEAR`.

## Additional approved decisions — Task 18

### A7-D1 — Separate final outcome and diagnostics

**RAMKI-APPROVED DECISION (2026-10-10, Asia/Calcutta):** The evaluation result must represent these concerns separately:

- `final_outcome`;
- each rule's knockout state and its supporting evidence;
- critical-safety evidence completeness and references to missing evidence;
- the score interval and score-derived verdict; and
- diagnostics, including `VERDICT_UNCERTAIN`.

A diagnostic must not silently overwrite the approved final outcome. A final outcome must not erase the score interval, knockout state or critical-safety evidence gap. This is a project-level contract clarification about distinct logical result concerns; it does not claim v1.5 defines these exact fields or their serialized shape, and it does not amend the specification or authorize a schema change.

### A7-D2 — Unverified-only knockout handling

**RAMKI-APPROVED DECISION (2026-10-10, Asia/Calcutta):**

- An `UNVERIFIED` knockout is neither `TRIGGERED` nor `CLEAR`, and an unverified knockout must not independently produce `AVOID`.
- If no verified knockout exists and an unresolved knockout constitutes a critical-safety gap, use `INSUFFICIENT_DATA`.
- Otherwise, do not issue a definitive favorable outcome until the applicable approved uncertainty rules establish a safe result.
- Preserve every unverified state and its supporting evidence.

**UNRESOLVED:** If no verified knockout and no critical-safety gap exist, but an unresolved `UNVERIFIED` knockout means the applicable uncertainty rules do not establish a safe result, the exact terminal `final_outcome`/status remains unspecified. Do not infer `AVOID`, `CLEAR`, `INSUFFICIENT_DATA` or another terminal label for that case.

## Required combined case

When all three conditions coexist—(a) a verified applicable knockout, (b) missing critical safety evidence and (c) a score range crossing a verdict band—the approved policy is:

- **Final outcome:** `AVOID`, because the verified applicable knockout is the independent basis for the outcome and takes precedence over numerical scoring.
- **Scoring diagnostic:** preserve `VERDICT_UNCERTAIN`; do not discard the score-range fact, but do not let it replace the knockout outcome.
- **Evidence state:** retain the critical-safety gap as missing/unverified evidence. Do not mark it verified, clear or resolved merely because another knockout is verified.

If no verified knockout exists and critical safety evidence is missing, the outcome is `INSUFFICIENT_DATA` under v1.5 §18 and decision item 5. An `UNVERIFIED` knockout remains `UNVERIFIED`; this decision does not convert it into a triggered or clear state.

## V1.5 reconciliation

**Authoritative text inspected:** `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §§3.3, 16 and 18; the authoritative v1.5 technical design and execution prompt were also searched for outcome-field definitions.

**SPECIFICATION REQUIREMENT (v1.5):**

- §16 retains K1–K6 with tri-state evaluation and says to show missing evidence for `UNVERIFIED`; §3.3 likewise says missing knockout input must not be treated as `CLEAR`. Neither section maps a verified `TRIGGERED` knockout to `AVOID`.
- §18 requires `VERDICT_UNCERTAIN` when the score range crosses a verdict band, says missing critical safety information produces `INSUFFICIENT_DATA` rather than `AVOID` merely because the score is incomplete, and says an `UNVERIFIED` knockout prevents a normal `CLEAR` interpretation.

**UNAVAILABLE in authoritative v1.5:** The artifacts do not define a `final_outcome` field or prescribe the exact result structure that separates final outcome, knockout/evidence state, score interval/verdict and diagnostics. They also do not assign a terminal outcome to an unverified-only knockout with no critical-safety gap. The only `AVOID` occurrence found in those artifacts is §18's warning against using it merely because the score is incomplete.

**RAMKI-APPROVED DECISION — project-level reconciliation:** The `final_outcome`/diagnostic separation in A7-D1 clarifies how to retain v1.5's score-derived `VERDICT_UNCERTAIN` without replacing or erasing a separately approved final outcome. It does not claim those exact fields already exist in v1.5. A7-D2 adds the approved rule that an unverified knockout alone cannot produce `AVOID` and cannot support a definitive favorable result until approved uncertainty rules establish safety. These directions preserve v1.5's tri-state and missing-evidence requirements; they do not rewrite the specification.

**ARENA RECOMMENDATION / conflict assessment:** The earlier verified-knockout-to-`AVOID` mapping remains a Ramki project decision resolving an ambiguity, not a v1.5 requirement. No direct conflict was found for the combined case: `AVOID` rests on the independently verified applicable knockout, not solely on incomplete scoring; critical-safety gaps remain visible; and `VERDICT_UNCERTAIN` is retained as a diagnostic. No direct conflict was found in A7-D2, but v1.5 does not prescribe the remaining unverified-only terminal outcome described above.

## Rationale

A verified applicable knockout is an independent safety finding and should not be reversed by numerical scoring or a score-range band. At the same time, missing safety evidence and score uncertainty remain material facts and must remain visible. When no verified knockout supplies an independent basis for `AVOID`, incomplete critical safety evidence must not be converted into that outcome.

## Consequences and constraints

- The distinct logical result concerns in A7-D1 must not be collapsed: final outcome, per-rule knockout state/evidence, critical-safety evidence completeness, score interval/score-derived verdict, and diagnostics.
- `VERDICT_UNCERTAIN` is retained as a diagnostic and must not silently replace the final outcome; the final outcome must not erase the score interval, knockout state or safety-evidence gap.
- No `AVOID` outcome may be generated solely because numerical scoring is incomplete or because a knockout is only `UNVERIFIED`.
- An unverified knockout remains `UNVERIFIED`, with its supporting evidence preserved; it is neither `TRIGGERED` nor `CLEAR`.
- These are governance clarifications. They do not amend or rewrite authoritative v1.5 and do not change schema, configuration or scoring code.

## Unresolved dependencies

- The Phase 0 contract must still define the concrete serialized evaluation-record fields and terminal-state mapping, without collapsing the distinct concerns approved in A7-D1. No schema change is made here.
- The exact terminal `final_outcome`/status remains unresolved when there is no verified knockout or critical-safety gap, but an unresolved `UNVERIFIED` knockout prevents the applicable approved uncertainty rules from establishing a safe result. Do not infer a terminal label for this case.

## Implementation authority

**Not granted.** Phase 1 remains unauthorized.
