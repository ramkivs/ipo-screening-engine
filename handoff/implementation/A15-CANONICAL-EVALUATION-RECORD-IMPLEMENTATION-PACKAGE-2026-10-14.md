# A15 Canonical Evaluation Record — Decision-Ready Implementation Profile

- **Original disposition recommendation:** **ACCEPT WITH SPECIFIED AMENDMENTS** to the 2026-10-13 A15 property/schema proposal.
- **Current status:** Ramki approved the exact profile with specified amendments on 2026-10-14 and granted its bounded implementation; implementation is complete at `fecdd8220500d7932c93b55b311a5f9830f92572` (tree `657e6b049156ce14a1b77b495700f34a3a20c068`). Independent review and product acceptance remain pending.
- **Profile prepared:** 2026-10-14 (Asia/Calcutta); based on remotely verified package commit `dbc7544ae800408e162a1787031c15659924ea65` and its matching file blob.
- **Candidate M:** `9bad659927616ad7fd3aad2864b6637f095872c5`, tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5` — unchanged and out of implementation scope.

The exact profile in §§1–3 was first published as a recommendation, then approved by Ramki with specified amendments under the 2026-10-14 A15 disposition recorded in `handoff/decisions/A15_CANONICAL_EVIDENCE_OUTPUT_CONTRACT_DECISION_2026-10-13.md`. The five-path scope in §4 was separately authorized as an explicit overlap while Phase 0 remains OPEN. This package's original §5 approval request is retained as historical evidence and is superseded by that disposition. The work reuses A15's semantic direction, A7-D1/D2, A1, A8-M/A9/A10, v1.5 and the inspected `EvaluationRecord`/`EvaluationStore`/`hashing.py` behavior. No broad audit or product-code/test run was performed for the original documentation revision.

## 1. Decision matrix — exact recommended contract

All nested objects are closed (`additionalProperties: false`); there is no `extensions` object in v1. Empty arrays are explicit, not omitted. The schema's `$schema`/`$id` are schema metadata, not record payload properties; every data property listed below is required.

| JSON path | Type / allowed value | Requiredness and rule |
|---|---|---|
| `$schema` / schema file | Draft 2020-12; `schema/ipo-evaluation-record.v1.schema.json` | New output schema only; do not change either existing v1.5 input schema. Use `$id: "urn:ipo-screening-engine:ipo-evaluation-record:1.0.0"`. |
| `record_schema_version` | string, const `"1.0.0"` | Required. Independent of input schema and serialization/hash profile versions. |
| `serialization_profile` | closed object: `profile_id`, `encoding`, `indent`, `sort_keys`, `ensure_ascii`, `line_ending`, `final_newline`, `string_normalization`, `non_finite_numbers` | Required, exact value below. This describes the on-disk JSON bytes, not the hash grammar. |
| `record` | closed object: `evaluation_id`, `ipo_id`, `company_name`, `engine_version`, `spec_version`, `config_version`, `config_hash` (all non-empty strings) | Required. Values copy the existing immutable `EvaluationRecord`; do not mint a second evaluation ID. |
| `evaluation` | closed object: `mode`, `evaluated_at`, `evaluation_cutoff`, `processing_status`, `validation` | Required. `mode` is one of the current `LIFECYCLE` values `PRELIMINARY`, `FINAL`, `POST_LISTING_1W`, `POST_LISTING_1M`, or `POST_LISTING_6M`; `evaluated_at` is an RFC 3339 date-time with explicit offset; `evaluation_cutoff` is the timestamp-state object below; `processing_status` is `COMPLETED` or `FAILED`; validation below. |
| `sources[]` | objects: required `source_id`, `source_type`; optional `uri`, `source_record_id`, `source_revision_id`, `digest_refs`; `timestamps[]` required | Required array; empty only when no source is represented. Do not infer source/provider identity, revision or qualification. `source_id` is unique in-record. |
| `evidence[]` | objects: required `evidence_id`, `source_id`, `locator`, `extraction_method`; optional `confidence` (number 0–1), `artifact_ref`; `timestamps[]` required | Required array; references must resolve to `sources`. `locator` is a document/page/section locator or structured field/path, never a fabricated page. |
| `observations[]` | objects: required `observation_id`, `field_path`, `source_id`, `evidence_refs[]`, `value_state`, `timestamps[]`; optional `source_revision_id`, `raw_value`, `raw_lexeme`, `reason` | Required array; preserve each source observation and competing revision. `raw_value` is a JSON scalar and required for `VALUE`; preserve `raw_lexeme` when it exists in the source artifact. `UNKNOWN` requires the same `{code, message?, evidence_refs[]}` reason object as a field value and forbids `raw_value`. Unknown facts carry state/reason, not invented values. |
| `field_values[]` | objects described in §2 | Required; one canonical entry per material field in the frozen input, including `UNKNOWN` and `NOT_APPLICABLE`. Conflicting raw observations remain in `observations[]`; no auto-winner. |
| `adjudications[]` | objects described in §2 | Required; empty unless an actual durable A1/Ramki adjudication exists. Never synthesize one. |
| `snapshots` | closed object with `input_snapshot_hash`, `source_manifest_hash`, `market_snapshot_hash`, `peer_snapshot_hash`, `artifact_refs` | Required. Hashes preserve the existing record values; artifact refs are the exact sibling names `input.json`, `evidence.json`, `market.json`, `peers.json`, `result.json`, and `manifest.json`. |
| `result` | closed object: `outcome_resolution`, conditional `final_outcome`, `knockouts[]`, `critical_safety`, `score`, `score_interval`, `score_verdict`, `diagnostics[]` | Required. Exact outcome mapping is in §3. Keep all A7 concerns separate. |
| `integrity` | closed object containing `digests[]` | Required. Do **not** put a self-referential `manifest_hash` in this object; the existing sibling `manifest.json` covers the record artifact. Digest fields and origins are below. |

ID uniqueness is enforced within each namespace (`source_id`, `evidence_id`, `observation_id`, `adjudication_id`, `digest_id`); every reference must resolve. Array order follows `serialization_profile.array_order`.

| Nested property | Type / allowed value | Requiredness / condition |
|---|---|---|
| `evaluation.validation.schema_status`, `semantic_status` | each `NOT_RUN`, `PASSED`, or `FAILED` | Both required. `schema_status` describes the input record's schema check, not self-validation of this output file. |
| `evaluation.validation.findings[]` | `{code:string, severity:INFO, WARNING, or ERROR, message:string, field_path?:string, evidence_refs:string[]}` | Required array; empty when there are no findings. |
| `evaluation.evaluation_cutoff` | timestamp-state object `{state, source_text?, normalized_utc?, evidence_refs[], reason?}` | Required; `KNOWN` requires the evidenced cutoff text and offset/UTC normalization where available; `UNKNOWN` requires a reason; `NOT_APPLICABLE` only where the approved metric contract has no cutoff. Never substitute retrieval or evaluation time. |
| `snapshots.artifact_refs` | closed object with keys `input`, `evidence`, `market`, `peers`, `result`, `manifest`; values are their exact sibling filenames | Required; no absolute paths or remote URI substitution. |
| `snapshots.*_hash` | non-empty strings for `input_snapshot_hash`, `source_manifest_hash`, `market_snapshot_hash`, `peer_snapshot_hash` | All required and copied without reinterpretation; describe their digest origin in `integrity.digests[]`. |
| `result.outcome_resolution.state` | `TERMINAL` or `NONTERMINAL_UNRESOLVED` | Required. `NONTERMINAL_UNRESOLVED` requires `reason={code:"UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT", evidence_refs:[…]}`; `TERMINAL` has no `outcome_resolution.reason`. |
| `result.final_outcome` | non-empty string | Required iff `outcome_resolution.state=TERMINAL`; forbidden otherwise. Semantic validator enforces the precedence/mapping in §3. |
| `result.knockouts[]` | `{rule_id:string, state:TRIGGERED, CLEAR, or UNVERIFIED, evidence_refs:string[], missing_input_refs:string[]}` | Required array; every rule represented by the current evaluator remains separate. |
| `result.critical_safety` | `{status:COMPLETE, INCOMPLETE, or UNKNOWN, missing_evidence_refs:string[], reason?:string}` | Required. `reason` is required when status is `INCOMPLETE` or `UNKNOWN`; refs may be empty only when the missing evidence cannot yet be identified, and the reason must say so. |
| `result.score` | closed object with required finite numbers `base_score`, `final_score`, `completeness_pct`, `available_points`, `unknown_points`, `total_evaluable_points`, `unresolved_penalty_points` | Required; copied from the existing score/confidence payload. `completeness_pct` is 0–100. Do not recompute these values in the serializer. |
| `result.score_interval` | `{state:AVAILABLE or UNKNOWN, lower_bound?:number, upper_bound?:number}` | Required; `AVAILABLE` requires finite lower and upper bounds; `UNKNOWN` forbids them. |
| `result.score_verdict` | `{value:string, uncertain:boolean, insufficient_data:boolean}` | Required; copied from existing score output, not recomputed by the serializer. |
| `result.diagnostics[]` | `{code:string, message:string, evidence_refs:string[]}` | Required array; includes `VERDICT_UNCERTAIN` when emitted; diagnostics never overwrite `final_outcome`. |

### 1.1 Exact serialization and hashing profile

| Item | Proposed value |
|---|---|
| On-disk profile | Closed object values: `profile_id="ipo-evaluation-record-json/1.0.0"`, `encoding="UTF-8"`, `indent=2`, `sort_keys=true`, `ensure_ascii=false`, `line_ending="LF"`, `final_newline=true`, `string_normalization="PRESERVE_SOURCE_TEXT"`, `non_finite_numbers="REJECT"`, `array_order="stable-id/path; timestamp-kind/source-text"`. Run schema validation before writing. |
| Writer | The current `EvaluationStore` JSON style, with the new artifact prevalidated using `allow_nan=false`; do not serialize the record through `canonical_json` as file bytes. |
| Existing object-hash profile | `canonicalization_id="ipo-engine-canonical-json/1.5.0"`; SHA-256 over the canonicalized JSON **object**, as `sha256_of()` currently does. Keep this for `result_hash` and the store manifest; do not alter `hashing.py` or historical hashes. |
| New record manifest entry | Same existing manifest convention: hash the parsed `evaluation-record.v1.json` object using `sha256_of()`, not the pretty-printed raw file bytes. Add `artifact_hash_algorithm="SHA-256"`, `artifact_hash_profile="ipo-engine-canonical-json/1.5.0"`, and `artifact_hash_subject="parsed JSON object"` to new manifests so the algorithm and subject are explicit. `verify_hashes()` continues to recompute the same object hash. |
| `serialization_profile` vs hash profile | Independent. File JSON contains ordinary schema-valid JSON numbers. `canonical_json()` tags floats as `{"__float__":"…"}`; using that text as the `.json` file would turn numeric score fields into objects and fail the proposed schema. That is a real technical incompatibility, not a policy conflict. |
| Cross-runtime check | A Node.js reference test must reproduce the v1.5 canonical-object bytes/digest for pinned fixtures (including Unicode, key order, finite floats and non-finite rejection). Python golden-byte tests separately pin the record file serialization. A failure blocks the profile; do not silently bump/change the v1.5 hash grammar. |

### 1.2 Canonical field-value and time contract

| Property | Type / values | Requiredness / conditional rule |
|---|---|---|
| `field_values[].field_path` | non-empty string | Required; unique within the record. |
| `value_state` | `VALUE`, `UNKNOWN`, `NOT_APPLICABLE` | Required; existing v1.5 meanings. `UNKNOWN` is never zero. |
| `value_origin` | `SOURCE`, `DERIVED` | Required only for `VALUE`. |
| `raw_value`, `normalized_value` | JSON scalar (`string`, finite `number`, or `boolean`) | Both required for `VALUE`; for identity normalization they must agree. Omit for `UNKNOWN`/`NOT_APPLICABLE`. |
| `raw_unit`, `normalized_unit` | non-empty string | Optional only where the field has a unit; never invent one. |
| `normalization` | closed object `{kind, formula_id?, formula_version?, input_field_refs[]?}`; `kind` is `IDENTITY`, `NORMALIZED`, or `DERIVED` | Required for `VALUE`. `NORMALIZED` and `DERIVED` require formula ID/version; `DERIVED` also requires at least one input field ref. |
| `verification_status` | `VERIFIED` or `UNVERIFIED` | Required for `VALUE` and `UNKNOWN`; absent for `NOT_APPLICABLE`. Independent of value state and source qualification. |
| `qualification_status` | `QUALIFIED`, `UNQUALIFIED`, `PENDING`, `NOT_APPLICABLE` | Required for every field value. `NOT_APPLICABLE` state requires `NOT_APPLICABLE` qualification. Schema validity, a URI or a local hash does not make a source qualified. |
| `source_observation_ids[]`, `evidence_refs[]` | strings resolving to `observations[]` / `evidence[]` | Required arrays. A source `VALUE` needs source/evidence support; a derived value needs formula inputs. Arrays may be empty only for `UNKNOWN`/`NOT_APPLICABLE` or an evidenced derivation with input-field refs. |
| `reason` | closed object `{code, message?, evidence_refs[]}` | Required for `UNKNOWN`; `UNVERIFIED`; `UNQUALIFIED`/`PENDING`; unresolved conflict; or invalid/unavailable required evidence. Candidate codes: `MISSING`, `UNAVAILABLE`, `INVALID`, `CONFLICT_UNRESOLVED`, `SOURCE_UNQUALIFIED`, `TIMEZONE_UNRESOLVED`, `NOT_AVAILABLE_BY_CUTOFF`, `UNVERIFIED`, `NOT_APPLICABLE`. Codes are proposals, not existing policy enums. |
| `timestamps[]` | objects `{kind, state, source_text?, normalized_utc?, evidence_refs[], reason?}`; `state` is `KNOWN`, `UNKNOWN`, or `NOT_APPLICABLE` | Required array on each observation; empty only if no timestamp fact is applicable/available. `kind` is one of `SOURCE_EVENT_OR_SESSION`, `SOURCE_VALUE_AS_OF`, `SOURCE_PUBLISHED_AT`, `SOURCE_AVAILABLE_AT`, `LOCAL_RETRIEVED_AT`. `KNOWN` requires original `source_text`; `SOURCE_AVAILABLE_AT` requires evidence refs; include `normalized_utc` only when timezone/offset is evidenced. `UNKNOWN` requires `reason={code, message?}` and forbids `normalized_utc`; retain naive source text and use `TIMEZONE_UNRESOLVED` where appropriate. Do not rely on current `parse_datetime()`'s naive-to-UTC default to qualify A8-M. |
| `adjudications[]` item | `{adjudication_id, field_path, competing_observation_ids[≥2], decision, selected_observation_id?, rationale, authority, authorization_evidence_refs[≥1], decided_at}` | `decision` is `SELECT_OBSERVATION` or `NO_SELECTION`; selection requires a selected observation ID; `authority` is `RAMKI`; `decided_at` is RFC 3339. Only serialize an actual A1 decision. |

### 1.3 Exact digest record

Each `integrity.digests[]` item is a closed object with required `digest_id`, `algorithm`, `digest_value`, `subject_kind`, `subject_ref`, `origin`, and `evidence_refs[]`; `canonicalization_id` and `reason` are conditional.

| Property | Proposed values / rule |
|---|---|
| `algorithm` | `SHA-256` for locally computed digests. Preserve a source-declared algorithm verbatim; if that source omits it, use `UNKNOWN` plus a reason while retaining `SOURCE_DECLARED` origin. Use `UNKNOWN` for legacy opaque digests with no algorithm. |
| `digest_value` | Non-empty string; locally computed SHA-256 must be 64 lowercase hexadecimal characters. Source-declared text is preserved verbatim. |
| `subject_kind` | `RAW_ARTIFACT_BYTES`, `CANONICAL_JSON_OBJECT`, `V1_5_RESULT_PAYLOAD`, `SOURCE_DECLARED_SUBJECT`, `LEGACY_UNSPECIFIED`. |
| `origin` | `LOCAL_COMPUTED`, `SOURCE_DECLARED`, `INDEPENDENTLY_ATTESTED`, `LEGACY_UNRESOLVED`. The last value is the specified amendment needed to preserve current opaque `content_hash`/manifest values without mislabeling them. |
| `subject_ref` | Exact artifact path, object role, source ID or source-claimed subject. Use literal `UNKNOWN` plus a reason only for `LEGACY_UNRESOLVED`. |
| `canonicalization_id` | Required for `CANONICAL_JSON_OBJECT` and `V1_5_RESULT_PAYLOAD`; use `ipo-engine-canonical-json/1.5.0` for existing engine hashes. Absent for raw-byte digests unless the source explicitly states otherwise. |
| `evidence_refs` | Empty is allowed for a locally computed digest. At least one source/evidence reference is required for `SOURCE_DECLARED` and `INDEPENDENTLY_ATTESTED`; attestation must actually be verifiable. |
| `reason` | Required for `LEGACY_UNRESOLVED`; preserve the old digest text and state that its algorithm/subject/origin is not established. |

`result_hash` is recorded as local SHA-256 over the existing v1.5 result-payload subject (engine/spec/config hashes, snapshot hashes, mode, plan, derived metrics, knockouts, score, penalties and missing/unverified inputs), canonicalized with v1.5 grammar. Do not change its inputs. Map `input_snapshot_hash` to the local canonical input object; map `source_manifest_hash` as local only when the existing fallback `sha256_of(evidence)` was used, otherwise `LEGACY_UNRESOLVED` unless origin metadata proves more; map market/peer hashes as local only when the local fallback was used, otherwise `LEGACY_UNRESOLVED`; treat existing opaque `SourceRef.content_hash` values as `LEGACY_UNRESOLVED`. None is a provider hash by inference. A9 still has no approved GMP source/hash subject; no digest in this profile qualifies A9 by itself.

## 2. Missing, invalid, conflicting, unverified and outcome rules

| Case | Serialized behavior / consequence | Governing authority check |
|---|---|---|
| Verified applicable knockout | `knockouts[].state=TRIGGERED`; `outcome_resolution.state=TERMINAL`; `final_outcome="AVOID"`; retain critical-safety gaps and score uncertainty separately. | A7 approved. |
| No verified knockout, critical-safety evidence missing | `final_outcome="INSUFFICIENT_DATA"`; preserve missing/unverified evidence and diagnostics. | v1.5 §18 / A7 approved. |
| Ordinary result, no A7 override | `final_outcome` equals the existing configured v1.5 `verdict.verdict`, including its existing `VERDICT_UNCERTAIN` value where that is what the evaluator emits. Retain the same score-derived verdict separately in `score_verdict`; do not add labels/thresholds or let diagnostics erase an independently established outcome. | Consistent recommendation; exact property mapping still needs Ramki's design approval. |
| A7 unverified-only case: no verified knockout or critical-safety gap, but an `UNVERIFIED` knockout prevents establishing a safe result | `outcome_resolution.state="NONTERMINAL_UNRESOLVED"`; `reason.code="UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT"`; `reason.evidence_refs` contains the relevant evidence IDs; **omit `final_outcome` entirely** (not `null`). Keep knockout `UNVERIFIED`, processing, validation and score diagnostics separate. | A7 semantics are approved; exact serialization is unresolved. This representation is the recommendation, not approval. |
| Missing value | `value_state=UNKNOWN`; no raw/normalized numeric substitute; reason/evidence refs retained; never convert to zero. | v1.5/A15 approved semantics. |
| Invalid input schema/type/required field | Fail before scoring; mark validation/processing failure in the existing error path. The current store creates no `EvaluationRecord` for pre-record rejection, so this increment writes **no** `evaluation-record.v1.json` for that failure and does not add a failure-record subsystem. | v1.5 approved; persistence of failed attempts is outside this increment. |
| Invalid/unavailable source fact in a persisted record | Keep the field `UNKNOWN`, `UNVERIFIED` or `UNQUALIFIED` as evidenced, with `INVALID`/`UNAVAILABLE` reason; apply only the already approved metric-specific gate. | A15/A8-M/A9 limits retained; no new global missing-input rule. |
| Conflict without a durable A1 decision | Preserve every observation/revision/evidence ref; canonical field is `UNKNOWN`, `UNVERIFIED`, qualification `PENDING`, reason `CONFLICT_UNRESOLVED`; `adjudications=[]`; field is non-screenable. | A1 approved. |
| A8-M/A9/A10 | Required NIFTY `UNKNOWN` blocks Final only under A8-M; absent/invalid required qualifying GMP snapshot/hash withholds Final only under A9; subscription observations remain distinct and evidence/display-only, with no inferred A10 Final rule. | Approved scope boundaries retained; no source acquisition, provider qualification or source gate added. |

## 3. Compatibility, actual gaps and disposition

| Choice checked | Authority / evidence | Finding |
|---|---|---|
| Separate output schema at the proposed path/version; closed shape and required groups | A15 explicitly leaves path/version, property spellings, enum values and conditional requiredness undecided; v1.5 input schema remains governing | No semantic conflict. Exact path/version and closed/required rules are new owner decisions; do not edit v1.5 input schemas. |
| State, verification, qualification, validation and processing axes | A15 + v1.5 §§3.2–3.4, 16, 18–20 | The axes are settled; the spellings/conditionals in §1 are proposals only. Unknown is not zero; schema errors stop scoring. |
| Source observations, conflicts and adjudications | A1 and A15 | Preserve all observations; no automatic winner. A1 adjudication appears only when actual Ramki authorization/evidence exists. Existing record model lacks some raw-lexeme/revision/time/adjudication fields; serialize only evidence present, preserve links to the original artifacts, and mark missing facts UNKNOWN/LEGACY_UNRESOLVED rather than synthesizing them. |
| Verified knockout, missing safety, uncertain score and unverified-only result | A7-D1/D2 + v1.5 §18 | Precedence is settled; A7's exact unverified-only serialization is expressly unresolved. Recommend the no-final nonterminal profile below. Ordinary score-verdict copying is a property-level proposal, not an A7 approval. |
| File serialization and digest canonicalization | `hashing.py` grammar 1.5.0 uses float-tag objects; `EvaluationStore` manifests currently hash parsed objects through `sha256_of()` | Actual technical incompatibility only if the hash text is used as the output file. Separate schema-valid JSON file serialization from the existing hash grammar; keep v1.5 hash inputs/bytes unchanged. |
| Digest origins/subjects | A15; existing `SourceRef.content_hash` and `source_manifest_hash` can be opaque | Origin distinctions align with A15. `LEGACY_UNRESOLVED` is an amendment needed for old opaque values. A9 has no approved provider/event/hash subject; this record cannot qualify a GMP hash. |
| A8-M/A9/A10 requiredness | A8-M, A9, A10 decisions | Retain NIFTY UNKNOWN and GMP qualifying-hash consequences only in their existing scopes; A10 Final behavior remains open. No source gate/provider is added. |
| History and result hashes | v1.5 §§19–21, 23 and A15 immutability requirement | Add one artifact and descriptive hash metadata to new manifests only. Preserve existing artifact payloads, `result_hash` inputs and all historical directories. |
| Failed-attempt artifact persistence | Current pipeline rejects invalid schema before constructing/storing `EvaluationRecord`; v1.5 says invalid input stops scoring | Not a semantic conflict. This increment does not add a failure-record subsystem; no output record is written for pre-record rejection. |

**Recommendation:** **ACCEPT WITH SPECIFIED AMENDMENTS.** A15's semantic baseline is sound and the proposal is implementable after the concrete choices above are accepted. The material amendments are: closed schema with the requiredness table above; ordinary `final_outcome` copying the current configured verdict after A7 precedence; explicit A7 nonterminal/no-final representation; a separate schema-valid JSON writer profile because v1.5 hash canonicalization tags floats; `LEGACY_UNRESOLVED` for opaque existing digests; and no in-record `manifest_hash` (the existing artifact manifest is the external digest record). No reason to re-audit or re-decide settled A15/A1/A7/A8-M/A9/A10 semantics.

## 4. Smallest exact implementation scope after authorization

**User-visible result:** every newly persisted `EvaluationRecord` directory (all five current `LIFECYCLE` stages) contains `evaluation-record.v1.json` alongside the current artifacts. It is directly inspectable and schema-validatable from the existing single-user local store. No API or frontend work is included.

| Exact path | Authorized change proposed |
|---|---|
| `schema/ipo-evaluation-record.v1.schema.json` | New Draft 2020-12 schema implementing §1–§2, closed objects, references and terminal/nonterminal conditionals. |
| `engine/ipo_screening/evaluation_record.py` | New pure `EvaluationRecord` projection, reason/digest-origin mapping, RFC 3339/time-fact normalization only when evidenced, strict schema/semantic validation, and deterministic new-record serialization profile. |
| `engine/ipo_screening/evaluation.py` | Add artifact name to `ARTIFACT_FILES` and `EvaluationRecord.artifacts()`; append the new artifact to new manifests; add the declared manifest hash algorithm/profile/subject; preserve all old payload/hash inputs; keep write-once semantics. |
| `tests/test_evaluation_record_v1.py` | New bounded tests: schema/conditionals, field state matrix, A7 precedence, references, timestamp unknowns, digest origins/subjects, golden serialization, Node reference hash vector and historical invariance. |
| `tests/test_reproducibility_store.py` | Update required-artifact assertion and expected artifact hashes from 6 to 7; keep existing `result_hash`, immutability and append-only assertions unchanged. |

**Explicit exclusions:** no changes to `canonical.py`, `hashing.py`, input schemas, scoring/config, extraction, source acquisition, NIFTY/GMP qualification, A10 policy, failed-attempt persistence, history migration, API/UI, auth, database, multi-user or enterprise architecture. If any listed behavior cannot be implemented within these five paths, stop for amended scope authority—do not broaden implicitly. Candidate M is not edited, rebuilt, rebased or reclassified.

### Focused tests and acceptance

Run only, after implementation authorization:

```bash
python -m pytest tests/test_evaluation_record_v1.py tests/test_reproducibility_store.py
```

Pass criteria: (1) all required/conditional schema cases pass and invalid combinations fail closed; (2) all state, reason and evidence references resolve; no unknown-to-zero, unverified-to-clear/triggered or automatic A1 winner; (3) A7 mapping table is exact, including no `final_outcome` in the unverified-only case; (4) Python file bytes match pinned golden output and Node independently matches the v1.5 canonical object-hash vector; non-finite values reject; (5) manifest verifies the new artifact and hash profile; (6) existing v1.5 result hash and old artifact payloads remain unchanged; (7) no old directory is rewritten; (8) no source/runtime gate or excluded path changes. This is implementation validation only, not independent acceptance, Phase 0 closure, canonical selection, merge or release. No A13 85-test or UI-7 rerun is included.

## 5. Original Ramki disposition and authority request (historical; superseded)

This section records the pre-approval request and is retained for provenance. Ramki's 2026-10-14 ACCEPT WITH SPECIFIED AMENDMENTS disposition and separate exact implementation grant satisfied the requested A/B/C items for this profile; this section is no longer an outstanding request. The distinctions remain controlling: design approval is not a code grant, and a code grant is not Phase 0 closure.

### A. Design approval — required first

Ramki must record one exact disposition against this file/revision, preferably:

> **A15 PROPERTY/SCHEMA DECISION — ACCEPT WITH SPECIFIED AMENDMENTS.** I approve the profile in §1–§2: schema path/version and closed required fields; the stated value, verification, qualification, timestamp and reason enums/conditionals; the ordinary v1.5 verdict-to-`final_outcome` mapping; A7 `NONTERMINAL_UNRESOLVED` with `UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT`, evidence refs and omitted `final_outcome`; the separate deterministic writer/hash profiles; digest origins including `LEGACY_UNRESOLVED`; and the listed compatibility rules. This is design approval only and grants no implementation authority.

If Ramki changes a value, the changed row must be recorded explicitly; settled A15 semantics need not be restated.

### B. Exact implementation authorization — separate written grant

After A, Ramki must record a separate grant with this exact scope (the code base/Phase 0 option must be completed explicitly):

> **A15 IMPLEMENTATION AUTHORIZATION.** I authorize only the five paths listed in §4 and the focused command in §4, based on product-review code base `4b19faf848a721265597a678926988d484d30e59`, with all changes committed/published only to `arena/573e69a4-ipo-screening-engine`. Candidate M and its canonical status/tree remain untouched. No other files, source/provider acquisition, source-specific gates, API/UI, config/fixture changes, PR, merge, release or production activation are authorized. This authorization is limited to implementing the design profile I approved in §5A.

If Ramki selects a different base, the exact commit must replace `4b19…` in the grant. Do not switch branches or publish to another branch. This grant does not itself close Phase 0.

### C. Phase 0 boundary — explicit choice

A11 still records Phase 0 OPEN; no existing A15 grant authorizes Phase 1. To remove avoidable delay, this package **recommends OVERLAP** for only the five-path increment in §4, with Phase 0 remaining OPEN and Candidate M untouched. That is a recommendation, not an existing exception. Ramki must state either:

- **WAIT:** this implementation grant takes effect only after a separately recorded Phase 0 closure; or
- **OVERLAP:** record: “I authorize this bounded A15 increment while Phase 0 remains OPEN as an explicit overlap; this does not close Phase 0.”

Historical pre-approval hold: do not implement until A, B and the Phase 0 choice are recorded. That hold was satisfied and superseded by the explicit 2026-10-14 disposition above. GCP/D1/D3 were not blockers for this isolated work.

---

## 6. Execution and acceptance status as of 2026-10-14

- **Implementation:** completed on the fixed session branch at `fecdd8220500d7932c93b55b311a5f9830f92572`, tree `657e6b049156ce14a1b77b495700f34a3a20c068`; its exact changed paths are the five listed in §4. The commit and tree were remotely verified unchanged during the post-A15 convergence check.
- **Focused verification:** the prior implementation turn reported `python -m pytest tests/test_evaluation_record_v1.py tests/test_reproducibility_store.py` — **43 passed in 16.54s**. No rerun was needed because the committed code/tree remained unchanged. This result is implementation-test evidence, not an independent review or product acceptance. The repository has no GitHub Actions workflows/runs or PR check results to provide remote CI confirmation.
- **Candidate M:** remains `9bad659927616ad7fd3aad2864b6637f095872c5` / tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5`; the A15 implementation is post-M and is not included in that candidate. No rebuild, rebase or reclassification occurred.
- **Independent review:** pending. A14 records Sai's appointment only for exact Candidate M; the A15 commit/tree is outside that appointment. No A15 review extension, Sai-authored disposition or substantiated independence report is recorded.
- **Product acceptance:** not recorded. It remains a separate Ramki decision after the relevant exact-target review; no implementation test or review recommendation substitutes for it.
- **Promotion:** no canonical delivery branch selected; no PR created for the session branch; no merge, release or production activation authorized. Phase 0 remains OPEN and general Phase 1 remains unauthorized.
