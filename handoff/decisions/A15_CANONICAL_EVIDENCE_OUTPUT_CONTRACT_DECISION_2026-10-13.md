# A15 — Canonical Evidence and Output Contract Design Decision

- **Decision ID:** A15
- **Title:** Semantic approval of the canonical evidence/output contract design direction
- **Status:** SEMANTIC/CONTRACT-DESIGN DIRECTION APPROVED 2026-10-13; PROPERTY/SCHEMA PROFILE ACCEPTED WITH SPECIFIED AMENDMENTS AND BOUNDED FIVE-PATH IMPLEMENTATION AUTHORIZED 2026-10-14; IMPLEMENTATION COMPLETED AT `fecdd8220500d7932c93b55b311a5f9830f92572`. Independent review, product acceptance, canonical selection and promotion remain pending.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-13 (Asia/Calcutta)
- **Approval provenance:** The instruction initiating this publication explicitly states that Ramki approved A15 at the semantic/contract-design level on 2026-10-13. No decision time is supplied or asserted. The specifically named prepared file was absent from both the verified pre-publication workspace and remote session-branch tree at `50160ab9832597e359d2f29512bacdf542b08645`; this record captures only the approval scope expressly stated in the instruction and does not claim to reproduce unavailable additional wording.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** Session branch `arena/573e69a4-ipo-screening-engine` at pre-publication tip `50160ab9832597e359d2f29512bacdf542b08645`.
- **Review candidate:** Commit `9bad659927616ad7fd3aad2864b6637f095872c5`, tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5`; this decision does not change that candidate.
- **Scope:** Semantic/contract-design direction for the canonical evidence and evaluation-result representation, and authority to prepare a separate property/schema proposal for later Ramki review.
- **Implementation authority:** Ramki separately authorized only the five-path A15 increment on 2026-10-14 as an explicit overlap while Phase 0 remains OPEN. This does not authorize broader Phase 1 work; `P1-CANON-01` and all other implementation remain NOT AUTHORIZED.

## 2026-10-14 superseding property/schema disposition and execution record

**Disposition:** Ramki accepted the decision-ready A15 evaluation-record profile with specified amendments and separately authorized its exact bounded implementation. The disposition was provided in Ramki's explicit Arena task instruction on 2026-10-14; the initial 2026-10-13 semantic decision remains intact. This addendum records that later approval rather than attributing it to the earlier decision date.

**Accepted profile:** the exact decision-ready profile in `handoff/implementation/A15-CANONICAL-EVALUATION-RECORD-IMPLEMENTATION-PACKAGE-2026-10-14.md` §§1–3, based on the package revision at `dbc7544ae800408e162a1787031c15659924ea65`, with its stated amendments: (1) closed Draft 2020-12 schema at `schema/ipo-evaluation-record.v1.schema.json`, version `1.0.0`, with the specified conditional requiredness; (2) existing configured verdict copied to terminal `final_outcome` after A7 precedence, and the A7 unverified-only case represented as `NONTERMINAL_UNRESOLVED` with `UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT` and no `final_outcome`; (3) schema-valid deterministic record-file serialization kept separate from the unchanged v1.5 canonical-object hash grammar; (4) opaque legacy digests preserved as `LEGACY_UNRESOLVED`, without an in-record self-referential manifest hash; and (5) additive compatibility only, preserving old hashes/artifacts and all A1/A7/A8-M/A9/A10 and v1.5 scope boundaries. No source/provider qualification or new metric-specific gate was approved.

**Exact implementation authority:** only these five paths, on the fixed branch `arena/573e69a4-ipo-screening-engine`, based on product-review code base `4b19faf848a721265597a678926988d484d30e59`: `schema/ipo-evaluation-record.v1.schema.json`, `engine/ipo_screening/evaluation_record.py`, `engine/ipo_screening/evaluation.py`, `tests/test_evaluation_record_v1.py`, and `tests/test_reproducibility_store.py`. The authorization was an explicit overlap while Phase 0 remains OPEN. Candidate M `9bad659927616ad7fd3aad2864b6637f095872c5` and its tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5` were not changed. No additional product paths, sources, configuration, fixtures, API/UI, PR, merge, release or production activation were authorized.

**Implementation and verification:** implementation commit `fecdd8220500d7932c93b55b311a5f9830f92572`, tree `657e6b049156ce14a1b77b495700f34a3a20c068`, changes exactly the five paths above. The reported focused command `python -m pytest tests/test_evaluation_record_v1.py tests/test_reproducibility_store.py` passed **43 tests** in the prior implementation turn. The commit/tree is unchanged; no rerun was warranted. This is implementation-test evidence, not independent review or acceptance. GitHub currently has no Actions workflows/runs or check results for this branch.

**Status boundaries:** A15 implementation is complete and remotely present. The independent reviewer appointed under A14 is scoped to Candidate M, not this post-M A15 code commit; no A15 review extension/report is recorded. Product acceptance and canonical delivery selection remain separate and are not recorded. No PR disposition, merge/release, or production activation has been authorized. Phase 0 remains OPEN and general Phase 1 remains unauthorized.

> The 2026-10-13 sections below preserve their original decision baseline. Any statement there that the exact property/schema profile is pending or that the bounded A15 implementation grant has not been made is superseded only by this addendum. All other scope limits remain in force.

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

## Decisions still not made after A15 (as of 2026-10-14)

The accepted package profile in the addendum is the only approved concrete A15 property/schema/serialization contract. A15 still does **not**:

- qualify a source/provider, select a source URL or source-native event, approve a freshness allowance or settle source-specific cutoff/availability rules beyond existing decisions;
- decide A10's missing/unavailable subscription Final behavior or extend A8-M/A9 rules to other metrics;
- establish a provider/source hash algorithm, exact qualifying GMP hash subject or source certification; the A15 digest fields do not qualify an A9 input;
- authorize any implementation beyond the exact five paths in the 2026-10-14 grant, or any config/fixture/scoring/source/API/UI changes;
- close Phase 0, authorize general Phase 1 or `P1-CANON-01`, select a canonical delivery branch, or approve release/production activation.

The earlier A15 recommendation column remains a proposal except where the accepted 2026-10-14 profile explicitly adopts a choice; no other metric/source policy is inferred from it.

## Reconciliation with controlling decisions and v1.5

- **A1:** Ramki remains the field-conflict authority; originals are preserved; each actual adjudication needs its own durable field-level decision and validation; unresolved disputes remain non-screenable.
- **A7:** Preserve A7-D1/D2. The approved A15 output profile serializes the specified unverified-only case as `NONTERMINAL_UNRESOLVED`, with reason `UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT` and no `final_outcome`; it introduces no new terminal outcome.
- **A8-M:** The approved NIFTY 50 PRICE INDEX classification and its required-input UNKNOWN-to-no-Final consequence remain NIFTY-specific. Source-native evidence qualification and the deterministic session/publication-availability prerequisite remain open. A local capture hash does not identify provider bytes.
- **A9:** Withhold Final when a required qualifying GMP snapshot or required hash is absent or invalid. A9 still selects no provider or qualifying GMP hash subject; the A15 output digest profile does not supply source qualification or make a generic/local digest satisfy A9.
- **A10:** Subscription observations remain distinct and evidence/display-only under interim handling; no scoring or missing-subscription Final rule is added.
- **v1.5:** §§3.2–3.4, 5, 16, 18–20, 21 and 23 remain authoritative. A15's logical contract does not amend them. The output representation may be designed as a separate versioned record; no in-place v1.5 schema change is authorized by this decision.

No direct conflict between those governing decision semantics and the cited v1.5 requirements was identified. The accepted A15 profile is an additive versioned output artifact; it does not edit either v1.5 input schema or alter historical hashes/artifacts. Source-native qualification, event/cutoff/availability contracts and A10 Final behavior remain open where noted above.

## Required next step

The design proposal and exact-scope implementation are complete. The next gate is exact-target independent review of implementation commit `fecdd8220500d7932c93b55b311a5f9830f92572` / tree `657e6b049156ce14a1b77b495700f34a3a20c068`, followed by separate Ramki product acceptance if warranted. A14 appoints Sai only for Candidate M. Ramki must either explicitly extend Sai's review scope (with Sai's independence/conflict declaration) or appoint another reviewer with a documented independence basis before treating A15 as independently reviewed. No review/acceptance is inferred from the implementation test result.

## Consequences and authority boundary

- A15 semantic/contract-design approval is **not** Phase 0 closure. Phase 0 remains OPEN.
- `P1-CANON-01` remains NOT AUTHORIZED. A separate written Phase 1 implementation grant naming exact candidate prerequisites and files is required.
- Sai's appointment and any subsequent review are separate from A15 approval; see [`A14-independent-reviewer-appointment-request.md`](A14-independent-reviewer-appointment-request.md). No independent acceptance is recorded by this decision.
- No source is newly qualified; the NDAL request remains UNSENT.
- No merge to `main`, PR, release, production activation or change to the assembled candidate is authorized.

---
