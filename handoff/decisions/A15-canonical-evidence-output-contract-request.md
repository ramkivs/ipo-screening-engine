# A15 — Canonical Evidence and Output Contract Decision Request

- **Record ID:** A15
- **Title:** Decision request for the canonical evidence/result representation
- **Status:** OPEN DECISION REQUEST — NO NEW POLICY OR IMPLEMENTATION APPROVED
- **Decision authority requested:** RAMKI
- **Request date:** 2026-10-13 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** Assembled review candidate `9bad659927616ad7fd3aad2864b6637f095872c5` (tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5`); A11–A13 and current A8-M/A9/A10 records are in that candidate.
- **Scope:** Resolve the remaining shared semantic and serialization contract needed before any canonical schema/result implementation. This request is not itself an approval.
- **Implementation authority:** NOT GRANTED. Phase 0 remains OPEN; Phase 1 and `P1-CANON-01` remain NOT AUTHORIZED.

## Decisions already approved and preserved

- **A1:** Ramki is the field-conflict authority. Preserve original observations and provenance; each adjudication needs its own durable field-level record. A disputed field remains non-screenable pending that record and validation.
- **A7-D1:** Keep `final_outcome`, per-rule knockout state/evidence, critical-safety completeness, score interval/score-derived verdict, and diagnostics distinct. The approved logical rules are not a serialized schema.
- **A7-D2:** `UNVERIFIED` is neither `TRIGGERED` nor `CLEAR` and cannot by itself produce `AVOID`. Missing critical safety evidence with no verified knockout yields `INSUFFICIENT_DATA`. The exact terminal case below remains open.
- **A8-M:** NIFTY classification and required-NIFTY `UNKNOWN` → no Final are approved policy only; source-native qualification and the session/publication-availability prerequisite remain open.
- **A9:** An absent or invalid required qualifying GMP snapshot/hash withholds Final. A9 does not choose a provider, hash algorithm, hashed object, field shape, or serialization.
- **A10:** Interim subscription handling is evidence/display only. It does not authorize scoring or decide missing/unavailable subscription Final behavior.

These records remain controlling at their cited baselines. A15 does not reopen or extend those decisions.

## Specific decision requested

Please approve or amend one coherent canonical evidence/result contract that answers the following, without overriding explicit v1.5 requirements or inferring source-specific policy:

1. **Semantic field map:** Define how the canonical evaluation record distinguishes source identity; source-native event/session and value-as-of; provider publication/availability; retrieval time; evaluation time/cutoff; original and normalized values; value state versus evidence/verification status; unknown/missing/conflict reasons; field-level A1 adjudication and authority provenance; and immutable snapshot/result linkage. Preserve the differing A8 time meanings rather than collapsing them. For hashes, specify algorithm, exact hashed object/bytes, and relationship to source-native versus local-capture evidence.
2. **A7 unresolved terminal case:** When there is no verified knockout and no critical-safety gap, but an unresolved `UNVERIFIED` knockout prevents the applicable uncertainty rules from establishing a safe result, choose the terminal `final_outcome`/status **or explicitly approve a no-terminal serialization**. Specify how that state remains distinguishable from `AVOID`, `CLEAR`, `INSUFFICIENT_DATA`, score diagnostics and missing critical-safety evidence. Do not infer any label before this decision.
3. **Schema and compatibility:** Select or amend the schema location/version, property-level serialization, validation behavior, and compatibility/migration treatment for existing immutable snapshots and result hashes. State whether changes require a new schema/version; do not silently reinterpret historic bytes or hashes.

A decision may leave individual provider/source contracts open. In particular, it must not imply that NSE, GMP, subscription, peers, VIX or another provider is qualified. A10's subscription Final consequence and A8 source-specific cutoffs remain separate open decisions; A9's narrow consequence must not be generalized.

## Requested acceptance evidence and constraints

A durable Ramki-attributed decision should identify each approved semantic/property definition, the selected schema/version and compatibility rule, the A7 terminal representation (or explicit no-terminal state), rationale, date, supporting evidence and any explicit deferrals with safe consequences. If a question is intentionally deferred, state the safe behavior while it remains open. Do not convert a proposal or this request into a decision.

Until that decision is recorded and the separate Phase 1 grant is issued, do not change schemas, serializers, scoring, configuration, fixtures, application behavior or tests. Phase 0 closure remains a separate decision and is not accomplished by this request.

## Rationale

A1, A7, A8-M, A9 and A10 establish important semantic constraints but do not supply a complete canonical property-level contract. A7 explicitly leaves the exact serialized result and one unverified-only terminal case unresolved; A9 leaves hash scope/algorithm open; and the published Program Authority package identifies schema/version/compatibility as prerequisites to `P1-CANON-01`. Recording the narrow unresolved decisions prevents downstream code from inventing fields or terminal states while retaining all approved semantics.

## Supporting evidence and v1.5 references

- `handoff/decisions/A1-evidence-adjudication-authority.md`, `A7-knockout-verdict-precedence.md`, the current A8/A8-M records, `A9-missing-gmp-final-fail-closed.md`, and `A10-interim-subscription-handling.md` in candidate `9bad659`.
- `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §§3.2–3.5, 5, 16, 18–20, 23; `ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md` §§3–5, 9, 12–15, 23; and `ARENA_IPO_Screening_Artifact_Manifest_v1.5.md`. v1.5 remains authoritative. If a direct conflict is found, stop and request an explicit Ramki decision; A15 does not silently override it.
- Published Program Authority package, which records the shared field-map/schema/version prerequisites and the separate `P1-CANON-01` dependencies.

## Unresolved dependencies and authority boundary

A15 remains open until Ramki records the requested contract decision. Even after that decision, implementation requires a separate exact-scope Phase 1 grant, and independent review/release remain separate. No reviewer, policy outcome, provider, schema version, terminal label, or implementation authority is appointed or approved here.

---
