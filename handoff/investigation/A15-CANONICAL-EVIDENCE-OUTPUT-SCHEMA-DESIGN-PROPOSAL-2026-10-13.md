# A15 — Canonical Evidence/Output Property and Schema Design Proposal

- **Status at preparation (2026-10-13):** DOCUMENTATION-ONLY DESIGN PROPOSAL — NOT APPROVED; NO SCHEMA OR IMPLEMENTATION AUTHORIZED. **Current disposition (2026-10-14):** superseded by Ramki's acceptance-with-specified-amendments of the decision-ready profile and bounded implementation grant recorded in `handoff/decisions/A15_CANONICAL_EVIDENCE_OUTPUT_CONTRACT_DECISION_2026-10-13.md` and `handoff/implementation/A15-CANONICAL-EVALUATION-RECORD-IMPLEMENTATION-PACKAGE-2026-10-14.md`.
- **For:** RAMKI / Program Authority
- **Prepared:** 2026-10-13 (Asia/Calcutta)
- **Decision baseline:** `handoff/decisions/A15_CANONICAL_EVIDENCE_OUTPUT_CONTRACT_DECISION_2026-10-13.md` (semantic/contract-design approval only as of 2026-10-13; later disposition is recorded there)
- **Review candidate:** `9bad659927616ad7fd3aad2864b6637f095872c5`, tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5`
- **Pre-proposal session tip:** `50160ab9832597e359d2f29512bacdf542b08645`
- **Implementation authority:** This proposal itself granted none. The later exact five-path A15 implementation grant is recorded in the linked 2026-10-14 disposition; Phase 0 remains OPEN and `P1-CANON-01` / general Phase 1 remain NOT AUTHORIZED.

> Historical note: the property names, enums, schema path/version, serialization profile and hash scope below were recommendations when prepared on 2026-10-13. Ramki's later approval applies to the decision-ready profile in the 2026-10-14 implementation package, not automatically to every alternative or statement in this earlier proposal. This file itself does not implement or modify a JSON Schema, serializer, application, configuration, fixture or test.

## 1. Purpose and decision boundary

A15's 2026-10-13 approval establishes the semantic design direction and authorizes this property/schema proposal. It does not accept the earlier A15 recommendation column item-by-item and does not select source providers, an A7 terminal label, hash scope, schema version or migration behavior. This proposal is the next review artifact; its concrete choices remain recommendations.

The design goal is one immutable evaluation record that can answer: what value/state was used; which source observation and evidence support it; when the event occurred, was published/available, was retrieved and was evaluated; whether the source/metric contract qualified the observation; how conflicts/revisions were handled; what result was established; and which exact bytes/objects the recorded hashes identify.

## 2. Governing requirements inspected

| Authority | Approved requirement retained by this proposal | Boundary that must not be crossed |
|---|---|---|
| **v1.5 §§3.2–3.4, 5** | Value state is `VALUE`, `UNKNOWN` or `NOT_APPLICABLE`; zero is numeric. Every material input carries value/status, source, source date/as-of, document/page or structured reference, extraction method and verification status. Preserve raw value/unit, normalized value, formula, source reference and confidence/verification. | Do not force missing data to zero or treat verification, confidence or source qualification as synonyms. Do not omit required evidence by relying on an optional schema slot. |
| **v1.5 §§16, 18** | Knockouts are `TRIGGERED`, `CLEAR` or `UNVERIFIED`; missing knockout input is not `CLEAR` and `UNVERIFIED` identifies missing evidence. Scoring criteria separately use `AVAILABLE`, `UNKNOWN` or `NOT_APPLICABLE`; score range, completeness, `VERDICT_UNCERTAIN` and `INSUFFICIENT_DATA` have their stated roles. | Do not collapse value-state enums, criterion availability, knockout state, score verdict, or A7 final outcome into one status. Preserve A7's project-level additions without misrepresenting them as v1.5 fields. |
| **v1.5 §§19–20** | Preliminary shows available/pending information, score range and provisional verdict. Final freezes the applicable subscription, market, GMP and peer snapshots, config version and source hashes; it is never overwritten. Schema/type/required-field failures stop scoring; cross-source differences are reported, not silently resolved. | Do not make a global missing-input Final rule. A schema check cannot resolve source conflicts or qualify a provider. |
| **v1.5 §§21, 23–24** | Every evaluation is immutable, receives an ID/version/hash set, can be reproduced, and has a machine-readable record/manifest before reporting. Historical bytes/rows are not replaced. | Do not rewrite a past record or hash in place, or claim that a locally computed hash attests provider bytes. |
| **A1** | Ramki alone adjudicates an actual field conflict. Preserve original observations; each adjudication identifies field, competing observations/provenance, rationale, decision, authorization evidence and date. Until authorized and validated, the disputed field remains non-screenable. Majority vote is prohibited; `CORROBORATED` is informational. | No automatic winner, agent adjudication, deletion of conflicting evidence, or promotion to `VERIFIED`. |
| **A7-D1/D2** | Keep final outcome, per-rule knockout state/evidence, critical-safety completeness/missing evidence, score interval/derived verdict and diagnostics separate. Verified applicable knockout and missing-critical-safety cases retain their approved handling. An `UNVERIFIED` knockout is neither triggered nor clear and cannot alone produce `AVOID`. | In the unverified-only case with no critical-safety gap but no established safe result, the terminal outcome remains unspecified. This proposal uses a distinct *proposed nonterminal resolution state* and assigns no terminal label. |
| **A8-M** | For required NIFTY, use only qualifying completed NSE NIFTY 50 PRICE INDEX sessions and approved SMA semantics; preserve source-native event/session, original timezone/offset, UTC, publication/availability, retrieval, cutoff and evaluation meanings. Unknown/unqualified/conflicting evidence yields `UNKNOWN`; required NIFTY `UNKNOWN` blocks Final. A local-capture hash identifies only local bytes. | This is NIFTY-specific. It does not qualify an NSE URL or data capture, allow a numeric publication delay, or set other metrics' Final behavior. |
| **A9** | Missing/invalid required qualifying GMP snapshot/hash withholds Final; a blocked marker is not a qualifying snapshot/hash. | No provider, hash algorithm/subject, schema, serialization or extension to subscription is approved by A9. |
| **A10** | NSE, BSE and All Exchange observations remain distinct; interim use is evidence/display-only, not scoring. | Missing/unavailable subscription Final behavior remains undecided; do not infer one from A9 or NIFTY. |

### Conflict check and implementation gap

No direct conflict between the inspected v1.5 requirements and A1/A7/A8-M/A9/A10 policy records was identified. A7's project-level outcome clarification supplements an output shape that v1.5 does not prescribe; A7 itself says not to claim its new logical fields are v1.5 schema fields. A8-M is a metric-specific freshness/source rule, not a global replacement for v1.5.

A separate candidate implementation gap was found: `engine/ipo_screening/canonical.py::parse_datetime` attaches UTC to a timezone-naive timestamp. A8-M requires unresolved timezone/source-time facts to remain `UNKNOWN`. The A8-M rule controls; the existing helper must not be treated as qualifying NIFTY evidence as-is. This proposal documents the gap for any future authorized implementation; it does not change the approved policy or code.

## 3. Existing shape and gaps at candidate M

| Existing surface | Verified candidate shape | Design gap to address in a future authorized implementation |
|---|---|---|
| `schema/ipo-input.v1.5.schema.json` | Draft 2020-12 input schema. Root `_sources` and `_evidence` are optional. A source reference requires `source_id` only when supplied; source type, URI, content hash and source/retrieval timestamps are optional. Evidence has a required `source_id` when an evidence entry is present, but evidence ID, locator, as-of, extraction method and confidence are optional. | No per-material-field/Preliminary/Final requiredness matrix; no complete linked output/evaluation record schema. Optional container/property shape is not proof that a material value satisfies v1.5 evidence requirements. |
| `schema/supplemental-enrichment.v1.schema.json` | Requires `contract_version`, `ipo_id`, `as_of` and a source list; source references still use a generic optional content hash and source/retrieval timestamps. | Does not model the complete immutable result, A1 decision record, all A8 timestamp meanings or digest origin/subject. |
| `canonical.Value` | Candidate model separates `state` (`VALUE`, `UNKNOWN`, `NOT_APPLICABLE`) and `verification` (`VERIFIED`, `UNVERIFIED`); value, units, period, raw numeric value/unit, normalization, source/evidence reference and note exist. Several are optional; `raw_value` is numeric, not an exact source-text field. | Add no schema property by inference. Proposal should preserve raw lexical evidence where parsing loses it, require approved fields conditionally, and keep verification/qualification/validation separate. |
| `SourceRef` / `Evidence` | Source reference has source ID/type, URI, optional opaque `content_hash`, retrieval/source timestamp. Evidence has evidence ID, source ID, locator, method/confidence and one optional `as_of`. | No digest algorithm/origin/subject; no complete event/session vs publication/availability/cutoff/evaluation grouping; no source revision or A1 adjudication record. |
| `EvaluationRecord` | Includes v1.5 identity/version/hash fields, input/evidence/market/peer snapshots, validation, knockouts, score, score range, verdict mapping, diagnostics/missing-unverified data. | Candidate code/schema has no `final_outcome` property or dedicated evaluation-result JSON Schema. A7 requires distinct logical result concerns, while A7's exact terminal/nonterminal serialization remains unresolved. |
| `hashing.py` | Uses SHA-256 for raw bytes and canonical JSON. `CANONICAL_GRAMMAR_VERSION` is `1.5.0`; canonical JSON sorts keys, removes insignificant whitespace, NFC-normalizes strings, rejects non-finite floats and encodes floats through a tagged `__float__` representation. Code comments say changing the grammar invalidates existing hashes. | An opaque source `content_hash` does not identify algorithm, exact subject, canonicalization or origin. A future schema must name each without reinterpreting old digest fields. |

No application/schema files are changed by this review.

## 4. Proposed record envelope and property groups

**Proposal only:** add a distinct, versioned evaluation-result contract rather than silently changing the v1.5 input contract. The sketch uses snake_case names for review; these names are not approved.

```jsonc
{
  "record_schema_version": "1.0.0",           // proposed new output-schema version
  "serialization_profile": {                   // proposed; separate from schema version
    "canonicalization_id": "ipo-engine-canonical-json/1.5.0",
    "encoding": "UTF-8"
  },
  "record": { "evaluation_id": "...", "ipo_id": "..." },
  "evaluation": {
    "mode": "PRELIMINARY | FINAL",
    "evaluated_at": { "original": "...", "utc": "..." },
    "processing_status": "...",
    "validation": { "schema_status": "...", "semantic_status": "..." }
  },
  "sources": [],
  "evidence": [],
  "observations": [],
  "field_values": {},
  "adjudications": [],
  "snapshots": {},
  "result": {
    "outcome_resolution": { "state": "...", "reason": {} },
    "final_outcome": null,
    "knockouts": [],
    "critical_safety": {},
    "score": {},
    "score_verdict": {},
    "diagnostics": []
  },
  "integrity": { "digests": [], "manifest_hash": "..." }
}
```

| Proposed group | Definition and links | Conditional requirement proposal |
|---|---|---|
| `record` | Stable evaluation ID, IPO ID, record creation identity, engine/spec/config versions, and `record_schema_version`. Keep mode (Preliminary/Final) explicit. | Required for every serialized evaluation. A rerun gets a new immutable ID; never update a prior record. |
| `evaluation` | Evaluation mode, evaluation timestamp/cutoff, processing status, and a `validation` object with structural and semantic findings. | Evaluation time always required; applicable cutoff required when the metric contract uses one. Processing/validation fields describe execution and data validation, not a screening outcome. |
| `sources` | Per-record source registry: stable `source_id`, source type/name, URI or structured-source identity, provider/source-native record ID where evidenced, and any approved source-contract ID/version. | A material field must resolve to an identified source when its state/contract requires source evidence. A registry entry never itself means the source is qualified. |
| `evidence` | Evidence ID, source ID, locator (document page/section/table or structured field/path), artifact reference, extraction method, confidence when available, and observations it supports. | Material inputs follow v1.5 §3.4/Prompt §12. A structured source need not fabricate a page number; the locator must be appropriate to that source. |
| `observations` | Immutable source observations with observation ID, metric/field path, source/evidence IDs, raw payload/locator, source-native record/revision identity and timestamp group. | Preserve each competing observation/revision. Do not discard or overwrite observations after reconciliation. |
| `field_values` | Canonical field map; each item links the raw/source observation(s), value state, raw/normalized representation, units/period/formula, verification and qualification references, and reasons. | Use conditional requirements in §8 below. No field becomes screenable merely because it parses or validates structurally. |
| `adjudications` | Separate A1 decision objects, linked by field path and IDs of all competing observations. | Present only for an actual Ramki adjudication; all A1 evidence/rationale/date fields are required then. Never synthesize one for an unresolved conflict. |
| `snapshots` | Frozen input, source manifest, market, subscription, GMP, peer and result artifact references, each with immutable ID, cutoff/session and digest references where applicable. | Final freezes the snapshots/config/source hashes required by v1.5 and the applicable approved metric contracts; Preliminary remains separately immutable. |
| `result` | A7 logical concerns: outcome resolution, final outcome when terminal, per-rule states/evidence, critical-safety completeness, score interval/derived verdict and diagnostics. | Apply A7 exactly. Do not fill a terminal outcome for the unresolved unverified-only case. |
| `integrity` | Digest records plus an artifact manifest whose entries name exact subjects, algorithms, origins and canonicalization IDs. | Hash requirements follow v1.5/A9 only within scope; never infer that a local digest qualifies a provider source. |

## 5. Proposed state, verification, qualification and reason model

All names/enums in this table are **proposed**, except the v1.5/A1/A7 terms explicitly identified as approved.

| Dimension | Proposed field / candidate values | Semantics and validation rule |
|---|---|---|
| Canonical value existence | `value_state`: `VALUE`, `UNKNOWN`, `NOT_APPLICABLE` (approved v1.5 values) | `VALUE` requires the relevant value and units; `UNKNOWN` carries a reason; `NOT_APPLICABLE` is not missing data. Never coerce any state to numeric zero. |
| Scoring criterion availability | `criterion_state`: `AVAILABLE`, `UNKNOWN`, `NOT_APPLICABLE` (v1.5 §18) | Keep separate from `value_state` and knockout state. Preserve score-range/completeness treatment under v1.5. |
| Evidence verification | `verification_status`: `VERIFIED`, `UNVERIFIED` (existing candidate terminology aligned to v1.5/A1) | `UNVERIFIED` records missing/insufficient evidence and is neither a knockout `CLEAR` nor `TRIGGERED`. `CORROBORATED` stays informational under A1, not an alternate screenable verification state. |
| Source/metric qualification | `qualification_status`: candidate `QUALIFIED`, `UNQUALIFIED`, `PENDING`, `NOT_APPLICABLE`; link a decision/contract reference | Qualification asks whether the source/observation meets an approved metric contract. It is not established by the presence of a URI, a local hash, or schema validity. The enum and exact authority required are unapproved. |
| Structural/semantic validation | `validation.schema_status` / `validation.semantic_status`: candidate `NOT_RUN`, `PASSED`, `FAILED`; include findings and references | Invalid schema/types/missing required fields fail the v1.5 scoring gate. Cross-source discrepancies are reported; validation never performs A1 adjudication. Enum values remain proposed. |
| Processing | `processing_status`: candidate `NOT_STARTED`, `COMPLETED`, `FAILED` | Describes whether serialization/evaluation processing ran. It does not say whether a terminal screening outcome exists or whether a data value is verified. |
| Outcome resolution | `outcome_resolution.state`: candidate `TERMINAL`, `NONTERMINAL_UNRESOLVED`; add a reason for the latter | Distinguishes whether an approved terminal outcome could be established. The A7 unverified-only case may be represented as `NONTERMINAL_UNRESOLVED`; no terminal label is thereby selected. Property and enum are proposals. |
| Reason | `reason.code`, `reason.message`, `reason.evidence_refs`, optional `rule_id` | Require a reason whenever a required value is UNKNOWN, unverified, unqualified, invalid, conflicted or outcome-nonterminal. Candidate code values could include `MISSING`, `UNAVAILABLE`, `INVALID`, `CONFLICT_UNRESOLVED`, `SOURCE_UNQUALIFIED`, `TIMEZONE_UNRESOLVED`, `NOT_AVAILABLE_BY_CUTOFF`; these are examples for owner review, not approved enumerations. |
| Confidence/corroboration | Keep extraction confidence, criterion completeness and corroborating observations separate | Do not turn confidence into verification or source qualification. A1's `CORROBORATED` remains informational and cannot resolve a conflict by vote. |

### Screenability proposal

A field is eligible for screening only after the approved field contract's required evidence exists, its source/metric qualification is satisfied, the value is appropriately `VERIFIED`, and structural/semantic validation passes. An unresolved A1 conflict stays non-screenable. This is an expression of A1/v1.5 constraints; the exact machine predicate and requiredness matrix need Ramki's property-level approval. A schema validator alone cannot grant screenability.

## 6. Source, evidence, snapshot and result linkage

**Proposed identifiers:** `source_id` identifies a source entry within a record; `evidence_id` identifies a supporting artifact/locator; `observation_id` identifies one source-native observation/revision; `snapshot_id` identifies a frozen grouped input; `evaluation_id` identifies one immutable run; `adjudication_id` identifies one Ramki decision. Each ID must be stable within its record and all references must resolve.

Recommended linkage:

1. `field_values.<field>.source_observation_ids[]` points to the exact observations used or considered.
2. Each observation references one `source_id`, zero or more `evidence_id`s, an exact locator/artifact, and its revision/timestamp metadata.
3. `snapshots` refer to the exact observation IDs and source manifest used at the evaluation cutoff; do not rely on “latest” mutable registries.
4. The `result` references the input/snapshot IDs and config version that generated it; derived metrics record formula/version and input-field references as required by v1.5 §5.
5. A Preliminary-to-Final delta links both immutable evaluation IDs; it does not mutate the Preliminary.
6. A source entry or successful schema validation does not establish provider qualification. No actual provider or source evidence is added by this proposal.

## 7. Proposed timestamp contract and conditional requiredness

| Proposed timestamp property group | Meaning; must not be substituted by | Conditional requirement proposal |
|---|---|---|
| `source_event` | Source-native event/observation identity, session/date, original source timestamp text, original zone/offset, normalized UTC and occurrence-evidence IDs. Not retrieval or publication time. | Required when a metric contract is event/session based. For NIFTY, require completed session/event evidence and timezone/offset semantics; unresolved source time means UNKNOWN. |
| `source_value_as_of` | Time the source says the value/observation is as of. Keep distinct from event occurrence where they differ. | Required when the approved source contract defines a source-native as-of. Do not copy an evaluation-time stamp into it. |
| `source_published_at` | Source publication timestamp. It does not, by itself, prove event time or actual availability. | Required only where the relevant approved contract requires/uses publication time and evidence supplies it. |
| `source_available_at` | Evidence that the source record was actually available by a cutoff. Not merely a scheduled publication or later retrieval. | Required for A8-M qualifying selection: demonstrate availability by cutoff. If it cannot be established, required NIFTY is UNKNOWN and Final is withheld. Other metrics need their own rule. |
| `retrieved_at` | Time the local system retrieved/captured the material. Not event/as-of or proof it was published by an earlier cutoff. | Record for each capture when available; preserve as a local observation. |
| `evaluation_cutoff` | Explicit decision boundary for selecting eligible snapshot observations. | Required by the applicable source/metric contract; never invent a generic cross-metric cutoff or delay. |
| `evaluated_at` | Time the immutable evaluation was performed. | Required for each evaluation record; this does not replace any source/event/cutoff time. |

**Representation recommendation:** use an object for each timestamp with `source_text`, `utc`, `offset`, and `evidence_ids` where the source semantics warrant it. Keep `session_date`/`session_id` as separate identifiers. If the original zone/offset is absent or ambiguous, retain the source text, leave normalized UTC unavailable, record a reason, and apply the metric's approved UNKNOWN/Final rule; never silently treat a naive timestamp as UTC for A8-M.

### Requiredness by evaluation mode and metric

| Context | Requiredness proposal | Existing rule preserved |
|---|---|---|
| Every material field | Always serialize a state. For `VALUE`, preserve raw/source value and unit, normalized value/unit, formula, source reference and confidence/verification under v1.5 §5. Source/evidence fields are required when the governing material-input contract requires them. | v1.5 §§3.2, 3.4, 5; Prompt §12. The exact JSON required list remains for Ramki to approve. |
| `UNKNOWN` / `UNVERIFIED` / conflict | Include explicit state, reason and evidence/input references; do not omit the property or use zero. `NOT_APPLICABLE` remains distinct. | v1.5 §§3.2–3.3; A1; A7. |
| Preliminary | Permit pending/unavailable fields only with explicit states/reasons; preserve points available/pending, provisional verdict and score range. | v1.5 §19. No Final-only gate is generalized to Preliminary. |
| Final | Freeze the required source snapshots, config version and source hashes; each source-specific contract determines required evidence and cutoff. Invalid/missing required schema fields block scoring. | v1.5 §§19–20. No global missing-input Final consequence is added. |
| Required NIFTY | If required NIFTY evidence is UNKNOWN/unqualified, do not issue Final; retain the exact reason. | A8-M only. No source URL/capture becomes qualified by this schema. |
| Required GMP | If the required qualifying snapshot or its required hash is absent/invalid, withhold Final. The hash kind/algorithm/subject must be settled by its source contract. | A9 only. Do not generalize to subscription or peers. |
| Subscription | Preserve NSE/BSE/All Exchange observations distinctly; display/evidence only under A10 interim handling. | A10 leaves missing/unavailable subscription Final behavior open. No default requiredness or Final block is proposed as policy. |
| Locator by source type | Require a document page/section for a filing when that is the material locator; for structured data require a stable field/path/record identifier instead of a fictitious page. | v1.5 permits document/page **or** structured-source reference. |

The labels `MUST`, `MAY` and `MUST_WITH_EXPLICIT_STATE` would be useful in the final requirements matrix, but they are proposal vocabulary only. Ramki must decide the exact field-by-field matrix before schema implementation.

## 8. Revision, conflict and A1 adjudication proposal

**Observation/revision fields proposed:** `observation_id`, `source_record_id`, `source_revision_id`, `revision_published_at`, `supersedes_observation_id`, `conflict_set_id`, and `precedence_evidence_ids`. These are optional where a source has no revision concept; absence must be explicit when revision precedence is material.

- Preserve all raw observations, locators, source/evidence references, timestamps and digest references. Never replace the prior observation with a later capture.
- Apply source-defined revision precedence only when the source evidence establishes the relationship. A8-M's same-index/session conflict without that evidence yields UNKNOWN. No generic newest-retrieval-time or last-write-wins rule.
- On an actual field conflict, propose an `adjudications[]` record containing: `adjudication_id`; `field_path`; `conflict_set_id`; all `competing_observation_ids`; `rationale`; `decision` and selected observation/value reference if Ramki chooses one; `authority` identifying Ramki; `authorization_evidence_id`; `decision_date`; and validation/findings. This maps A1's requirements; the field names/shape are not approved.
- Before a valid Ramki-attributed adjudication and validation exist, keep the field non-screenable. The conflict record must not delete original states or mark them retrospectively verified.
- A reviewer, extraction model, schema validator or majority of sources cannot perform the A1 decision.

## 9. Digest algorithm, exact subject, canonicalization and origin proposal

The current candidate uses SHA-256, but A9 does not define which digest qualifies. The following is a **recommendation**, not an A9/provider decision.

| Proposed digest case | Algorithm/bytes to hash | Proposed origin metadata and limits |
|---|---|---|
| Locally captured source artifact | SHA-256 over the exact captured byte sequence, before parse/render/re-encoding. Record byte length and immutable artifact ID. | `digest_origin=LOCAL_COMPUTED`; it identifies those local bytes only. It does not prove provider-response bytes, source publication or source qualification. |
| Source-declared digest | Preserve the exact reported algorithm, digest text, claimed subject and source evidence without relabeling it as locally recomputed. | `digest_origin=SOURCE_DECLARED`; a source claim is not independently verified merely because the value parses. |
| Independently verifiable attestation | Verify a signature/receipt or independently documented source attestation over a defined subject and retain its verification evidence. | Candidate `INDEPENDENTLY_ATTESTED` origin only when actual verifiable evidence exists. Never write `PROVIDER_CERTIFIED` based on a local hash or an unsupported claim. |
| Canonical input snapshot | SHA-256 over UTF-8 bytes returned by the declared canonicalization profile for the exact normalized input-snapshot object. | Record algorithm, `canonicalization_id`, exact object/role, schema version and artifact ID. |
| Source manifest | SHA-256 over the canonicalized, deterministically ordered source/evidence/revision manifest used by that evaluation. | The manifest lists individual artifact digests and origins; no self-hash cycle. |
| Result payload | SHA-256 over the exact canonicalized `result` object (terminal/nonterminal resolution, knockouts, safety completeness, score interval/verdict and diagnostics), excluding only the integrity field containing this hash. | Keep run envelope and result subject explicit. The proposal must be compared with the candidate `compute_result_hash` behavior before any grant; no historical hash is recomputed. |

**Proposed digest record fields:** `digest_id`, `algorithm` (recommend `SHA-256` for newly computed digests), `digest_hex`, `subject_kind`, `subject_id`, `byte_length` when meaningful, `canonicalization_id` for logical objects, `digest_origin`, `source_claim` if applicable, `attestation_evidence_ids`, and capture time. The values and enums remain unapproved.

**Canonicalization recommendation:** keep schema version and serialization/hash grammar version independent. Reuse the candidate's declared `CANONICAL_GRAMMAR_VERSION="1.5.0"` only if the exact UTF-8, NFC, key ordering, whitespace, float tagging and non-finite-number rejection behavior is frozen and cross-runtime tests prove it; otherwise propose a new grammar ID/version before implementation. Any grammar change creates new digests for new records only and must never invalidate history by rewriting stored bytes. Preserve raw-byte hashes without canonicalization. `SourceRef.content_hash` must not be upgraded to a provider hash by inference.

**A9 boundary:** A9 still requires a future GMP source contract to identify which snapshot/hash subject is the qualifying one. This recommendation does not satisfy that dependency or admit fabricated provider evidence.

## 10. A7 result and unresolved/nonterminal representation proposal

A7's approved outcomes and diagnostics remain controlling. Suggested structure (all names are proposals):

```text
result.outcome_resolution.state = TERMINAL | NONTERMINAL_UNRESOLVED
result.outcome_resolution.reason = { code, evidence_refs }
result.final_outcome = <approved terminal value>   # only when state is TERMINAL
result.knockouts[] = { rule_id, state, evidence_refs, missing_inputs }
result.critical_safety = { completeness, missing_evidence_refs }
result.score = { value, interval, completeness }
result.score_verdict = <configured score-derived result>
result.diagnostics[] = [...]
evaluation.processing_status = COMPLETED | FAILED
evaluation.validation.schema_status = PASSED | FAILED | NOT_RUN
```

For the A7-D2 unverified-only case, propose `outcome_resolution.state=NONTERMINAL_UNRESOLVED`, a reason/evidence reference, and **no terminal `final_outcome`**. Processing may have completed and schema/semantic validation may have passed; those facts do not convert the unresolved decision into a terminal result. Conversely, validation failure is not an A7 outcome. Do not emit `AVOID`, `CLEAR`, `INSUFFICIENT_DATA` or another terminal value for this case absent a later A7 decision.

| A7 case | Approved logical handling retained | Proposal representation |
|---|---|---|
| Verified applicable knockout, including score-range uncertainty | A7 verified knockout produces `AVOID`; preserve `VERDICT_UNCERTAIN` diagnostic and all other evidence gaps. | Terminal `final_outcome=AVOID`; separate knockout, safety-gap, score-range and diagnostic data. |
| No verified knockout; critical-safety evidence missing | `INSUFFICIENT_DATA`; missing evidence remains explicit. | Terminal `final_outcome=INSUFFICIENT_DATA`; preserve `UNVERIFIED` evidence and reason. |
| No verified knockout or critical-safety gap, but `UNVERIFIED` prevents an established safe result | Terminal label/serialization remains unresolved by A7. | Proposed `NONTERMINAL_UNRESOLVED`; omit/null `final_outcome` by a schema rule to be approved. This is not a new A7 decision. |
| Verified knockout + missing critical safety + score-range uncertainty | `AVOID` on the independent verified knockout; preserve missing safety evidence and `VERDICT_UNCERTAIN`. | Separate fields remain present; no diagnostic overwrites outcome or vice versa. |

Ramki must approve the exact terminal/no-terminal serialization before implementation. A15's semantic direction does not alter A7's still-open terminal decision.

## 11. Output schema, serializer, validation and compatibility proposal

| Design choice | Recommendation for Ramki's review | Status |
|---|---|---|
| Output-schema location | Add a distinct `schema/ipo-evaluation-record.v1.schema.json`; do not change `schema/ipo-input.v1.5.schema.json` or `schema/supplemental-enrichment.v1.schema.json` in place. | Proposed path only. |
| Schema version | JSON Schema Draft 2020-12; record property `record_schema_version="1.0.0"`. Version input, result-record schema and canonicalization independently. | Proposed version only. |
| Strict validation | Closed object shapes (`additionalProperties: false`, or a single explicit namespaced `extensions` object); reject unknown enum/type combinations, duplicate IDs, dangling references and invalid conditional state combinations. Run JSON Schema plus semantic validators; no implicit coercion or default-to-zero. | Proposed; exact rule list and extension policy need approval. |
| Serialization | UTF-8 JSON; deterministic canonical form identified by a versioned `canonicalization_id`. Freeze number/date/string/key-order rules and publish golden bytes. A schema version change does not by itself define hash grammar, and vice versa. | Proposed; candidate grammar 1.5.0 needs explicit conformance review. |
| Historical compatibility | Read historical v1.5 input/evaluation artifacts as their recorded versions; retain exact original byte streams and hash values. An unsupported schema/grammar version fails closed for operations requiring interpretation; do not relabel old records as the new schema. | Proposed fail-closed rule; owner review required. |
| Migration | No automatic migration in this proposal. If later approved, migration creates a new immutable record with a new ID, links to the exact old record/hash, records migration tool/version and keeps original bytes/hash unchanged. Missing facts stay unknown/unqualified; migration may not synthesize provider evidence or A1 decisions. | Not authorized or implemented. |
| Historical result semantics | Keep v1.5 `evaluation_id`, IPO/mode/time, engine/spec/config versions, input/source/result hashes and append-only Preliminary/Final lifecycle. New record version is additive and explicitly linked; no old record is overwritten. | Required compatibility objective; details need approval. |

If a direct v1.5 requirement cannot be represented under this proposal, stop and obtain an explicit Ramki decision rather than changing v1.5 or silently relaxing validation.

## 12. Required focused acceptance tests

The eventual authorized contract implementation should include, at minimum:

1. Strict schema positive/negative tests, unknown-field rejection, type failures, duplicate IDs and dangling source/evidence/observation references.
2. Round-trip tests for `VALUE`, `UNKNOWN`, `NOT_APPLICABLE`; raw source text/value, source and normalized units, formula/version, periods, and no unknown-to-zero coercion.
3. Cross-product tests separating value state, criterion availability, `VERIFIED`/`UNVERIFIED`, qualification, schema/semantic validation and processing status.
4. Conditional requiredness for Preliminary and Final, with distinct required-NIFTY, A9 missing/invalid qualifying GMP snapshot/hash, and A10 display-only/subscription-Final-open cases.
5. Timestamp fixtures with original offsets, normalized UTC, unknown/naive timezone, source event vs value-as-of vs publication vs availability vs retrieval vs evaluation cutoff/time; future/partial/expected missing NIFTY sessions and availability-by-cutoff failures must remain UNKNOWN and block required NIFTY Final.
6. Revision/conflict tests: competing observations preserved; source-defined precedence accepted only with evidence; retrieval order alone never selects a winner; A1 adjudication requires all A1 fields and an attributable authorization record.
7. Digest known-byte and canonical-object tests, byte length/subject checks, tampering, local-capture versus source-declared versus attested origin, no unsupported provider-certification, and A9 fail-closed behavior.
8. A7 branch tests for verified knockout, critical-safety gap, score-range diagnostic, combined case, and unverified-only nonterminal representation with no terminal label.
9. Deterministic serialize/parse/serialize and cross-runtime golden-byte tests tied to schema and canonicalization versions.
10. Historical-byte/hash invariance tests proving no v1.5 record, Preliminary, Final or source artifact is overwritten or silently rehashed; migration tests only after an approved migration rule.
11. A10 tests ensure separate NSE/BSE/All Exchange evidence and no scoring qualification from interim evidence/display handling; do not assert a subscription Final consequence A10 leaves undecided.

The existing 85 scoped tests recorded by A13 remain candidate-baseline evidence only. They are not repeated for this documentation change and are not independent acceptance.

## 13. Open decisions for Ramki and review route

Ramki's later property/schema review should explicitly accept, amend or reject:

- the proposed record/group/property names and exact enums;
- the per-field Preliminary/Final/metric requiredness matrix;
- qualification and reason vocabularies and their authority/evidence links;
- timestamp property names and source-specific conditional rules;
- revision/conflict identifiers and A1 adjudication schema;
- SHA-256 recommendation, exact digest subjects/origin values and canonicalization grammar/version;
- whether A7's no-terminal case uses the proposed nonterminal object and how `final_outcome` is absent/null;
- output schema path/version, strict-validation/extension policy and migration/compatibility rules;
- acceptance-test scope and historic-byte/hash fixtures.

Source qualification, NIFTY availability rules, GMP source/hash qualification and subscription Final handling retain their separate A8-M/A9/A10 authority boundaries. No provider or evidence source is named here.

Sai's A14 assignment concerns independent review of candidate `9bad659927616ad7fd3aad2864b6637f095872c5` / tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5`; appointment is not acceptance. The A14 review and any later implementation review must use their exact scopes and record an explicit outcome. This design proposal is for Ramki's decision and does not expand Sai's candidate review target.

## 14. Authority boundary

Documentation only. No executable schema, serializer, application code, configuration, fixture or test was created or changed by this proposal. Phase 0 remains OPEN; `P1-CANON-01` remains NOT AUTHORIZED. A separate written implementation grant is required after Ramki's property/schema decision. No PR, merge to `main`, release, production activation or NDAL send is authorized.

---
