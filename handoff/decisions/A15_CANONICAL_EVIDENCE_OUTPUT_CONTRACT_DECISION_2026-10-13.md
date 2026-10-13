# A15 — Canonical Evidence and Output Contract Design Decision

- **Decision ID:** A15
- **Title:** Semantic approval of the canonical evidence/output contract design direction
- **Status:** RAMKI-APPROVED — SEMANTIC/CONTRACT-DESIGN LEVEL ONLY; PROPERTY/SCHEMA PROPOSAL PENDING; IMPLEMENTATION NOT AUTHORIZED
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-13 (Asia/Calcutta)
- **Approval provenance:** The instruction initiating this publication explicitly states that Ramki approved A15 at the semantic/contract-design level on 2026-10-13. No decision time is supplied or asserted. The specifically named prepared file was absent from both the verified pre-publication workspace and remote session-branch tree at `50160ab9832597e359d2f29512bacdf542b08645`; this record captures only the approval scope expressly stated in the instruction and does not claim to reproduce unavailable additional wording.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** Session branch `arena/573e69a4-ipo-screening-engine` at pre-publication tip `50160ab9832597e359d2f29512bacdf542b08645`.
- **Review candidate:** Commit `9bad659927616ad7fd3aad2864b6637f095872c5`, tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5`; this decision does not change that candidate.
- **Scope:** Semantic/contract-design direction for the canonical evidence and evaluation-result representation, and authority to prepare a separate property/schema proposal for later Ramki review.
- **Implementation authority:** **NOT GRANTED.** Phase 0 remains OPEN; Phase 1 and `P1-CANON-01` remain NOT AUTHORIZED.

## Approved semantic/contract-design direction

Ramki approves advancing A15 from an open semantic/contract-design request to a documented design baseline. The approved scope is the set of logical distinctions and constraints below; concrete JSON property names, enum spellings, schema paths/versions, serialization grammar, exact per-property requiredness and migration rules remain for the separately reviewed proposal and a later explicit Ramki decision.

1. **Preserve the governing v1.5 and A1/A7/A8-M/A9/A10 rules.** These approvals are layered project decisions; A15 does not rewrite v1.5, reopen settled policy, or extend a metric-specific rule to another metric.
2. **Keep value state, evidence verification, source/metric qualification, validation, processing and outcome resolution distinguishable.** `VALUE`, `UNKNOWN` and `NOT_APPLICABLE` retain v1.5 meanings; `UNVERIFIED` is not `CLEAR`, `TRIGGERED`, zero or a favorable substitute. Reasons and supporting evidence for unknown, unverified, invalid, conflicted or unqualified states must remain inspectable. This decision does not approve additional enum members or property names.
3. **Keep material values attributable to source and evidence observations.** Preserve raw and normalized values/units and the normalization basis required by v1.5 §5, along with source/evidence references, confidence/verification information and immutable snapshot/result linkage. A schema validator must not adjudicate a source conflict.
4. **Do not collapse time meanings.** Preserve source-native event/observation/session time, its original timestamp/zone or offset, normalized UTC, publication/availability, retrieval, evaluation cutoff and evaluation time as distinct concepts when applicable. Source-specific contracts establish which are available and required; generated timestamps are not source-event evidence.
5. **Preserve observations and revisions.** Keep competing source observations and their provenance; use source-defined revision precedence only when evidence establishes it. A1 adjudication remains field-specific, attributable to Ramki, and must retain the competing observations, rationale, decision, authorization evidence and date. No majority vote or automatic last-write-wins resolution is approved.
6. **Distinguish digest origin and exact subject.** A locally calculated digest identifies only the exact local bytes/object hashed. It is not a provider-byte digest or provider certification. Any source-reported or independently attested digest must be represented as such with its supporting evidence; no source/provider or qualifying hash is invented here.
7. **Keep A7 result concerns separate.** Preserve final outcome, per-rule knockout states/evidence, critical-safety completeness, score interval/score-derived verdict and diagnostics as distinct logical concerns. For the A7-D2 case with no verified knockout or critical-safety gap but an unresolved `UNVERIFIED` knockout that prevents an established safe result, retain an **unresolved/nonterminal** condition rather than inventing a terminal label. Its future serialization must remain separate from terminal `final_outcome` and from processing/validation status. A7's exact serialized representation remains to be proposed; no new terminal outcome is approved.
8. **Apply requiredness only within its approved scope.** v1.5 Preliminary/Final rules and the A8/A9/A10 contracts remain controlling. A8-M's required-NIFTY `UNKNOWN` blocks Final only for that required NIFTY input; A9's absent/invalid required qualifying GMP snapshot/hash withholds Final only in its approved GMP scope; A10 does not decide subscription Final behavior. No global missing-input Final rule or provider qualification is established.
9. **Preserve immutability.** Historical evaluations and source/result artifacts are not overwritten or silently reinterpreted. Any later version or migration must identify its source, preserve original bytes and hashes, and be separately specified and approved.

## Decisions explicitly not made by A15

This semantic approval does **not** select or approve:

- exact property names, data types, enum values or conditional schema definitions;
- source/provider qualification, a source URL, a source event, a freshness allowance, or any source-specific cutoff not already decided;
- the terminal `final_outcome` for A7's unverified-only case;
- hash algorithm, canonicalization version, exact serialized hash subject, or a rule by which a digest qualifies under A9;
- an output-schema location/version, serializer version, migration or backward-compatibility behavior;
- A10 missing/unavailable subscription Final behavior;
- a schema/code/configuration/fixture/test change, Phase 0 closure, Phase 1 authority, release or production activation.

The earlier A15 request's Arena **recommendation** column is not a source-selection decision and does not silently approve any property spelling or unresolved metric policy. The property/schema proposal is documentation-only and must label its choices as recommendations for Ramki to accept, amend or reject.

## Reconciliation with controlling decisions and v1.5

- **A1:** Ramki remains the field-conflict authority; originals are preserved; each actual adjudication needs its own durable field-level decision and validation; unresolved disputes remain non-screenable.
- **A7:** Preserve A7-D1/D2, including the still-unresolved terminal label/serialization for the specified unverified-only case. No `AVOID`, `CLEAR`, `INSUFFICIENT_DATA` or other terminal label is inferred for that case.
- **A8-M:** The approved NIFTY 50 PRICE INDEX classification and its required-input UNKNOWN-to-no-Final consequence remain NIFTY-specific. Source-native evidence qualification and the deterministic session/publication-availability prerequisite remain open. A local capture hash does not identify provider bytes.
- **A9:** Withhold Final when a required qualifying GMP snapshot or required hash is absent or invalid. A9 still selects no provider, algorithm, hash subject or serialization.
- **A10:** Subscription observations remain distinct and evidence/display-only under interim handling; no scoring or missing-subscription Final rule is added.
- **v1.5:** §§3.2–3.4, 5, 16, 18–20, 21 and 23 remain authoritative. A15's logical contract does not amend them. The output representation may be designed as a separate versioned record; no in-place v1.5 schema change is authorized by this decision.

No direct conflict between those governing decision semantics and the cited v1.5 requirements was identified in this review. The separate property/schema proposal records candidate implementation gaps and asks Ramki to decide any unresolved design choice before implementation.

## Required next step

Prepare and submit `handoff/investigation/A15-CANONICAL-EVIDENCE-OUTPUT-SCHEMA-DESIGN-PROPOSAL-2026-10-13.md` for Ramki's later review. It may recommend concrete properties and enum values, but must identify them as proposals, preserve all approved semantics above, and enumerate conditional requiredness, exact digest subjects, schema/serialization compatibility and focused acceptance tests. Do not implement that proposal without a separate exact-scope written grant.

## Consequences and authority boundary

- A15 semantic/contract-design approval is **not** Phase 0 closure. Phase 0 remains OPEN.
- `P1-CANON-01` remains NOT AUTHORIZED. A separate written Phase 1 implementation grant naming exact candidate prerequisites and files is required.
- Sai's appointment and any subsequent review are separate from A15 approval; see [`A14-independent-reviewer-appointment-request.md`](A14-independent-reviewer-appointment-request.md). No independent acceptance is recorded by this decision.
- No source is newly qualified; the NDAL request remains UNSENT.
- No merge to `main`, PR, release, production activation or change to the assembled candidate is authorized.

---
