# A12 — 01a Ratified as Product-Code Review Base Only

- **Record ID:** A12
- **Title:** Product-code review-base ratification, without canonical selection
- **Status:** RAMKI-APPROVED — REVIEW BASE ONLY
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-13 (Asia/Calcutta)
- **Approval provenance:** Ramki's explicit instruction in the Arena conversation received 2026-10-13 (Asia/Calcutta). No decision time is supplied or asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** Session branch `arena/573e69a4-ipo-screening-engine` at `de8d5f82442eff3ef77437c1fe96fa73c7a62c2c`; product source `arena/01a10b42-ipo-screening-engine` at `4b19faf848a721265597a678926988d484d30e59`; governance source `arena/4e1080b7-ipo-screening-engine` at `adbd93c5b4450fb113561368d7d101eb4686c842`.
- **Scope:** Which ref is to serve as the product-code review base for a bounded non-canonical candidate.
- **Implementation authority:** NOT GRANTED.

## Approved decision

1. Ratify `arena/01a10b42-ipo-screening-engine` at `4b19faf848a721265597a678926988d484d30e59` as the **product-code review base only**.
2. Use 4e at `adbd93c5b4450fb113561368d7d101eb4686c842` as the pinned governance/evidence source for the current A8-M, A9 and A10 decisions; it is not selected as the product-code base.
3. This ratification does **not** select a canonical delivery candidate, establish acceptance, grant general branch-integration authority, authorize Phase 1 implementation, or authorize merge to `main`, release or production activation. Candidate assembly is separately and narrowly governed by A13.

## Supporting evidence and v1.5 references

- `handoff/investigation/IPO-SCREENING-ENGINE-RECONCILIATION-AUDIT-DRAFT-2026-10-13.md` and the published Program Authority decision package at the session baseline above.
- Source-tree comparison at 01a `4b19faf848a721265597a678926988d484d30e59` and 4e `adbd93c5b4450fb113561368d7d101eb4686c842`; see also the 01a/4e governance records named in A13.
- `handoff/authoritative/ARENA_IPO_Screening_Artifact_Manifest_v1.5.md`, `IPO_Screening_Engine_Specification_v1.5.md` §§1–6, and `ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md` §§1–2, 21–23. These define reference precedence and product requirements; this ratification is not acceptance of implementation.

## Rationale and limitations

The reconciliation audit reports that 01a is a descendant of PR #3 and contains the later product/UI/lifecycle/repair work. It lacks the current A8-M/A9/A10 records and A9 gate found on 4e. The branches diverge from `main`; 4e and 01a are not one accepted tree. This decision separates the product-code review base from the governance source and does not approve every existing policy, configuration, fixture or implementation on 01a.

## Consequences and constraints

- The candidate remains non-canonical and pending independent review.
- 4e's source tracker remains untouched; the session tracker remains candidate-only.
- A12 alone does not authorize assembly. See the separate bounded authorization in A13.
- Phase 0 remains OPEN and Phase 1 remains UNAUTHORIZED under A11 and the governing records.

## Unresolved dependencies

Candidate assembly and its independent review; canonical contract approval; separate Phase 1 implementation authority; and all release gates remain outstanding.

---
