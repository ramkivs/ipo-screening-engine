# A9 — Missing GMP Final Fail Closed

- **Decision ID:** A9
- **Title:** Missing GMP Final Fail Closed
- **Decision status:** RAMKI-APPROVED DECISION — OPTION A, FAIL CLOSED.
- **Publication status:** PUBLISHED AND INDEPENDENTLY VERIFIED at `refs/heads/arena/4e1080b7-ipo-screening-engine` in commit `0c6defe3aaab4b01a711cd8d50f03c25f2d2a180`.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-10
- **Authorization basis:** Ramki's explicit approval of Option A, explicit assignment of A9, and supplied approval date in TASK 33. No decision time or timezone is supplied or asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** Branch `arena/4e1080b7-ipo-screening-engine`, pre-record commit `2fa855cd251e03c3b87d0e8d1f7c35c6e42a03e4`, tree `2994f984eb7f30287f846193e4392ca43ebeccbc`.
- **Scope:** The consequence for `FINAL` when a required qualifying GMP snapshot or its required hash is absent or invalid.
- **Implementation authority:** NOT GRANTED.

## Approved decision

> If a required qualifying GMP snapshot or its required hash is absent or invalid, withhold `FINAL`. A blocked-input marker is not a qualifying snapshot or hash.

This decision resolves only the missing-GMP `FINAL` handling previously left open in A8 §43.

## Rationale

Specification v1.5 §19 requires the GMP snapshot and source hashes for `FINAL`. A8 §43 recorded the missing-GMP `FINAL` handling as unresolved. Ramki's explicit TASK 33 approval selects Option A for this case. This is a project-level resolution of that open question; it does not amend v1.5 or represent the choice as text already present in the specification.

## Limitations and unchanged decisions

This decision is narrowly limited to the stated missing-or-invalid required qualifying GMP snapshot/hash condition. It does not:

1. Select or approve a GMP provider or source.
2. Define a qualifying observation, event/as-of semantics, cutoff, hash algorithm, schema, serialization, or blocked-input representation.
3. Authorize an exception to the fail-closed rule.
4. Authorize scoring, partial evaluation, or a definitive outcome.
5. Resolve A5 peer-calibration requirements. A5 remains `CALIBRATION_EVIDENCE_INSUFFICIENT`; the peer-calibration/eligibility block remains in force.
6. Claim that P0-B provenance has been verified in the repository. No P0-B decision record was found in the target branch's reachable history; this decision's authorization basis is Ramki's explicit TASK 33 approval.
7. Approve v1.6, establish release/version governance, authorize implementation, or grant a Phase 0 freeze.
8. Change existing decisions, subscription/market/peer source contracts, or other required-input constraints. This decision does not authorize `FINAL` or scoring when another required qualifying input is missing or invalid.

Any future exception or reconsideration requires a separately approved contract that defines the applicable exception, required evidence, snapshot/hash representation, and `FINAL` eligibility conditions.

## Evidence references

- `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §19 and §§21, 23 — Final snapshots/source hashes and immutable-record/hash requirements.
- `handoff/authoritative/ARENA_IPO_Screening_Artifact_Manifest_v1.5.md` — v1.5 authority classification; this decision does not change it.
- `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` §§37–43 and §55 — approved GMP evidence safeguards and the previously unresolved missing-GMP `FINAL` choice.
- `handoff/decisions/CONVENTION.md` §§13–18 — decision-record format, metadata, authority distinction, and implementation-authority boundary.
- Ramki's explicit Option A approval, A9 assignment, and decision date in TASK 33 (current Arena instruction).

## Unresolved dependencies

The GMP provider/source, qualifying observation, event/as-of semantics, cutoff, hash algorithm, snapshot representation, schema, serialization, and blocked-input representation remain undefined by this decision. A5 peer-calibration evidence remains blocked. The Task 18 chronology remains unresolved. Other source contracts remain unchanged.

## Implementation authority

**NOT GRANTED.** This decision does not authorize implementation or alter the Phase 0 freeze or v1.6 approval status.
