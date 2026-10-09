# A7 — Knockout and Verdict Precedence

- **Decision ID:** A7
- **Title:** Verified-knockout outcome and score-range precedence
- **Status:** APPROVED AS A RAMKI PROJECT DECISION; v1.5 does not itself state the `TRIGGERED` → `AVOID` mapping.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-09 (Asia/Calcutta)
- **Decision source / authorization evidence:** Ramki's explicit A7 approval in principle in TASK 15 and approved outcome-precedence direction in TASK 16.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/4e1080b7-ipo-screening-engine`, pre-record commit `01ba66c12ca1195fd7acbd287c3e39a019808094`
- **Scope:** Final-outcome precedence for verified applicable knockouts, score-range uncertainty and missing critical safety evidence.
- **Implementation authority:** NOT GRANTED. This decision does not authorize Phase 1 or application implementation.

## Approved decision text

1. A verified, applicable knockout takes precedence over numerical scoring.
2. A verified, applicable knockout produces the final outcome `AVOID`.
3. Missing critical safety evidence remains explicitly recorded and is never treated as verified or clear.
4. When score-range uncertainty applies, preserve `VERDICT_UNCERTAIN` as a scoring diagnostic; it does not override a verified knockout.
5. When no verified knockout exists but critical safety evidence is missing, use `INSUFFICIENT_DATA` rather than issuing `AVOID` merely because evidence is incomplete.
6. An `UNVERIFIED` knockout is neither `TRIGGERED` nor `CLEAR`.

## Required combined case

When all three conditions coexist—(a) a verified applicable knockout, (b) missing critical safety evidence and (c) a score range crossing a verdict band—the approved policy is:

- **Final outcome:** `AVOID`, because the verified applicable knockout is the independent basis for the outcome and takes precedence over numerical scoring.
- **Scoring diagnostic:** preserve `VERDICT_UNCERTAIN`; do not discard the score-range fact, but do not let it replace the knockout outcome.
- **Evidence state:** retain the critical-safety gap as missing/unverified evidence. Do not mark it verified, clear or resolved merely because another knockout is verified.

If no verified knockout exists and critical safety evidence is missing, the outcome is `INSUFFICIENT_DATA` under v1.5 §18 and decision item 5. An `UNVERIFIED` knockout remains `UNVERIFIED`; this decision does not convert it into a triggered or clear state.

## V1.5 reconciliation

**Authoritative text inspected:** `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §§16 and 18.

- §16 defines K1–K6 and tri-state knockout output, but does not explicitly map a verified `TRIGGERED` knockout to `AVOID`.
- §18 requires `VERDICT_UNCERTAIN` when the score range crosses a verdict band, says critical safety gaps produce `INSUFFICIENT_DATA` rather than `AVOID` merely because the score is incomplete, and says an `UNVERIFIED` knockout prevents a normal `CLEAR` interpretation.
- The only `AVOID` occurrence in the authoritative v1.5 artifacts is the §18 warning against using it merely because the score is incomplete. No explicit verified-knockout outcome mapping was found.

**Arena reconciliation:** The approved `AVOID` mapping is therefore recorded as Ramki's project decision resolving a v1.5 ambiguity—not as a rule already written in v1.5. No direct contradiction was found for the stated combined case: `AVOID` is based on the verified knockout, not solely on incomplete scoring; the safety gap is retained; and `VERDICT_UNCERTAIN` is preserved rather than erased. The v1.5 text does not define whether `VERDICT_UNCERTAIN` must be the sole final outcome or can be retained as a diagnostic alongside a knockout outcome; this decision makes that distinction explicit without changing the v1.5 file.

## Rationale

A verified applicable knockout is an independent safety finding and should not be reversed by numerical scoring or a score-range band. At the same time, missing safety evidence and score uncertainty remain material facts and must remain visible. When no verified knockout supplies an independent basis for `AVOID`, incomplete critical safety evidence must not be converted into that outcome.

## Consequences and constraints

- The final knockout outcome, score-range diagnostic and evidence status are distinct facts and must not be collapsed.
- No `AVOID` outcome may be generated solely because a numerical score is incomplete.
- An unverified knockout is not resolved by this decision; it remains `UNVERIFIED` and cannot be represented as `TRIGGERED` or `CLEAR`.
- This is a separate governance clarification. It does not amend or rewrite the authoritative v1.5 specification and does not change schemas, configuration or scoring code.

## Unresolved dependencies

- The Phase 0 evaluation-record contract must define how a final outcome and the `VERDICT_UNCERTAIN` diagnostic are both represented. No schema change is made here.
- V1.5 §18 says an `UNVERIFIED` knockout prevents normal `CLEAR`, but neither the specification nor this decision assigns a separate terminal outcome to an unverified-only knockout when no critical-safety `INSUFFICIENT_DATA` condition applies. Do not infer one.

## Implementation authority

**Not granted.** Phase 1 remains unauthorized.
