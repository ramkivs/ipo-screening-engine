# A15 Canonical Evaluation Record — Implementation Package

- **Status:** READY-TO-EXECUTE SPECIFICATION — PROPOSAL ONLY; NO PRODUCT CODE OR SCHEMA AUTHORIZED
- **Prepared:** 2026-10-14 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Authoritative session ref checked:** `arena/573e69a4-ipo-screening-engine` at `674aa9b0aca57544f412891cc26c4fa30459e017`
- **Product-code review base:** `arena/01a10b42-ipo-screening-engine` at `4b19faf848a721265597a678926988d484d30e59`
- **Candidate M:** `9bad659927616ad7fd3aad2864b6637f095872c5`, tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5` (unchanged; not the implementation base selected by this document)
- **Controlling records:** A1 (`11eebb4…`), A7 (`3e70b56…`), A11 (`688cc05…`), A15 decision (`3247904…`), and A15 property/schema proposal (`62cf3c3…`).

> This is an implementation specification for owner review, not an approval, implementation grant, canonical selection, Phase 0 closure, acceptance, merge, release, or production authorization. Do not execute the code changes below until the design decision and exact-scope implementation grant in §8 are recorded.

## 1. Decision and authority boundary

**Already approved:** Ramki's 2026-10-13 A15 decision approves the semantic/contract-design direction: preserve value state, verification, source/metric qualification, validation, processing and outcome as distinct concerns; preserve evidence and temporal meaning; keep source revisions and A1 adjudications attributable; distinguish digest origin and subject; retain A7/A8-M/A9/A10 limits; and preserve immutable history. These semantic decisions are not reopened here.

**Not approved:** The published A15 proposal explicitly labels all concrete field names, enums, schema path/version, conditional requiredness, serialization/hash profile and migration choices as recommendations. Its presence does not approve those choices. A7's unverified-only terminal/no-terminal case also remains unresolved.

**Implementation authority:** A11 keeps Phase 0 OPEN. A11 and A15 explicitly withhold implementation authority; A15 says `P1-CANON-01` is not authorized and requires a separate written grant. A12/A13 do not provide an exact-scope A15 implementation grant. The tracker is a status summary, not a grant. No applicable implicit authority is used to override those express restrictions. GCP/D1/D3 are unrelated to this isolated output-record increment and are not prerequisites.

## 2. A15 decision matrix

Classification key: **1** already approved by an authoritative decision; **2** directly proposed and consistent with approved decisions, but not itself approved; **3** a genuine owner decision remains; **4** blocked by an external/source-specific dependency. A recommendation in category 2 is not approval.

| Area | Classification | Existing evidence and resolution for this package |
|---|---|---|
| **Semantic axes** | **1 — approved** | A15 and v1.5 require value state (`VALUE`, `UNKNOWN`, `NOT_APPLICABLE`), verification, qualification, validation, processing, result and diagnostics to remain distinct. A1 requires preservation of competing observations and Ramki-attributed field adjudication. A7-D1 requires outcome, per-rule knockout state/evidence, critical-safety completeness, score interval/verdict and diagnostics to remain distinct. Do not collapse these into a single status. |
| **A15 record envelope and property names** | **2 — proposed, consistent** | The proposal names `record_schema_version`, `serialization_profile`, `record`, `evaluation`, `sources`, `evidence`, `observations`, `field_values`, `adjudications`, `snapshots`, `result` and `integrity`. It also proposes `value_state`, `verification_status`, `qualification_status`, `schema_status`, `semantic_status`, `processing_status`, reason/evidence references and digest metadata. Use these as the implementation target only after the complete profile is approved; do not claim these spellings are already policy. |
| **Schema and versioning** | **2 — proposed, consistent** | The proposal recommends a separate `schema/ipo-evaluation-record.v1.schema.json`, JSON Schema Draft 2020-12, and record version `1.0.0`, independent of input-schema and canonicalization versions. Keep `ipo-input.v1.5.schema.json` and `supplemental-enrichment.v1.schema.json` unchanged. |
| **Closed shape and exact requiredness** | **3 — unresolved** | The proposal allows either `additionalProperties: false` or a namespaced extension object; it does not select one. Its per-field, Preliminary/Final and metric-specific requiredness matrix is also explicitly pending. Package recommendation: closed objects (`additionalProperties: false`) for v1.0; explicit `UNKNOWN`/reason/evidence fields instead of silently omitting unknown facts; no generic missing-input-to-Final rule. Ramki must approve this profile. |
| **Serialization and deterministic representation** | **2 — proposed, conditional** | UTF-8 JSON with a versioned `canonicalization_id` is consistent with v1.5 reproducibility. Reuse `hashing.canonical_json` / grammar `1.5.0` only if the focused cross-process and cross-runtime golden-byte tests below pass. If they do not, stop and propose a new canonicalization ID/version; do not change the existing grammar or old hashes in this increment. |
| **Digest subjects and origin** | **3 for exact profile; 4 for qualifying provider hashes** | The proposal's `SHA-256` recommendation and `LOCAL_COMPUTED`, `SOURCE_DECLARED` and `INDEPENDENTLY_ATTESTED` origin distinctions are consistent with A15, but their exact enums/subjects are not approved. A9 still does not identify which source-native GMP snapshot/hash qualifies; source/provider evidence is an external dependency. A local or generic payload hash must never be described as a provider digest or as satisfying A9. |
| **Missing, invalid and unverified values** | **1 for semantics; 2 for proposed encoding** | Approved: unknown is not zero; `UNVERIFIED` is neither `TRIGGERED` nor `CLEAR`; schema/required-field failures stop scoring; missing critical-safety evidence is not a verified knockout; A8-M required UNKNOWN blocks Final only in its NIFTY scope; A9's qualifying missing/invalid snapshot/hash blocks Final only in its GMP scope; A10 interim observations remain distinct and evidence/display-only. The proposal's explicit reason and evidence-reference fields are consistent; their exact names/enums remain proposed. |
| **A7 unverified-only result** | **3 — unresolved** | A7-D2 settles the semantics but explicitly leaves the exact terminal result/status unresolved when no verified knockout or critical-safety gap exists and an `UNVERIFIED` knockout prevents an established safe result. See §3 for the smallest safe representation recommendation. |
| **Compatibility and reproducibility** | **1 for immutability; 2/3 for output-version details** | v1.5 and A15 require immutable evaluations, deterministic result hashes and preservation of historical bytes. The proposal's additive output version, no in-place rewrite and no automatic migration are consistent recommendations. Exact unsupported-version behavior, output golden bytes and the mapping between the new record digest and existing `result_hash` remain for approval. No historical record is migrated or rehashed. |
| **Tests and acceptance** | **2 — proposed, consistent** | The A15 proposal's focused tests (strict schema/reference validation; distinct state axes; Preliminary/Final requiredness; timestamps; conflicts/A1; digest subjects/origins; A7 cases; deterministic golden bytes; history invariance; A10 separation) follow the approved semantics. The exact accepted profile and tests must be named by the implementation grant. |
| **External data-source contracts** | **4 — blocked where used** | Actual NIFTY source/session/availability, A9 GMP provider/event/hash subject, and A10 subscription Final behavior remain separate dependencies. They do not block a generic output record that faithfully represents missing/unqualified evidence; this increment must not implement those gates or fabricate source metadata. |

## 3. A7 unverified-only representation

**Verified from A7:** A verified applicable knockout produces `AVOID`; without a verified knockout, missing critical-safety evidence produces `INSUFFICIENT_DATA`; `UNVERIFIED` is neither `TRIGGERED` nor `CLEAR`; score-range uncertainty remains a diagnostic and does not erase other evidence. A7-D2 does **not** choose a terminal label for the unverified-only case.

**Recommendation — not an existing approval:** Represent that case as:

```json
{
  "outcome_resolution": {
    "state": "NONTERMINAL_UNRESOLVED",
    "reason": {
      "code": "UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT",
      "evidence_refs": ["<existing evidence IDs>"]
    }
  },
  "knockouts": [{"state": "UNVERIFIED", "evidence_refs": ["<existing evidence IDs>"]}],
  "diagnostics": ["<existing score diagnostics>"]
}
```

For this state, **omit `final_outcome` entirely**; do not emit `null`, `AVOID`, `CLEAR`, `INSUFFICIENT_DATA`, or a newly invented terminal value. The schema should make `final_outcome` required only for an approved terminal state and forbidden for `NONTERMINAL_UNRESOLVED`. Keep processing and validation statuses separate from outcome resolution. This is the smallest deterministic fail-closed serialization: it records what happened, provides the reason/evidence, and cannot be mistaken for a favorable or terminal decision.

Ramki must approve or amend this exact A7 serialization before implementation. A15 semantic approval did not make that A7 property-level decision. For an ordinary determinate case with no A7 override, this package recommends copying the existing configured v1.5 score verdict into `final_outcome` while retaining it separately as `score_verdict`; verified-knockout and critical-safety precedence still apply. This adds no verdict values or thresholds, but the exact mapping is a proposed property-level choice, not an existing approval.

## 4. Recommended output contract

This is the exact proposed profile to approve or amend; it does not purport to be the approved schema.

### 4.1 Versioned record

Create a new additive artifact named `evaluation-record.v1.json` beside the existing immutable artifacts. Its top-level object contains the A15 groups in the matrix, with:

- `record`: existing evaluation/IPO identity and engine, specification, configuration and config-hash identifiers;
- `evaluation`: mode, evaluation time, processing status and separate structural/semantic validation results;
- `sources`, `evidence`, `observations`: only source identities, locators, raw observations, revisions and timestamp facts actually present in the evaluation; references must resolve;
- `field_values`: field path, explicit value state, raw/source and normalized value/unit where available, formula/version where applicable, verification and qualification statuses, source-observation/evidence references, and reason;
- `adjudications`: empty unless an actual durable A1 decision exists; any item must carry the field, conflict set, competing observations, rationale, Ramki authority, authorization evidence and date;
- `snapshots`: IDs/references for the exact immutable input, source, market, peer and other applicable snapshots used;
- `result`: outcome resolution, terminal `final_outcome` only where approved, per-rule knockouts/evidence, critical-safety completeness, score interval, score-derived verdict and diagnostics as separate members;
- `integrity`: digest entries with exact subject, algorithm, canonicalization ID where applicable, origin and evidence for source claims/attestations.

A timestamp is never relabeled: source event/session, source-value as-of, source-published, demonstrated source-available, local retrieval, evaluation cutoff and `evaluated_at` remain separate. If source facts are absent or ambiguous, record the available source text and an explicit unknown/unqualified reason; never synthesize UTC, publication time, provider identity, revision precedence or availability.

### 4.2 Hash and artifact behavior

- Preserve the current `EvaluationRecord.result_hash` calculation and existing `evaluation.json`, `input.json`, `evidence.json`, `market.json`, `peers.json` and `result.json` payload meanings/bytes. For new evaluations, `manifest.json` retains its current format and adds one entry for `evaluation-record.v1.json`; historical artifacts and manifests are not rewritten. Do not recompute historical hashes or claim a new source certification.
- For the new record only, use the existing SHA-256/canonical-JSON implementation if and only if the pinned cross-process and cross-runtime golden-byte tests prove the declared profile. A local digest must identify the exact local object/bytes hashed; a source-declared digest remains a source claim; an independently attested digest requires verifiable attestation evidence.
- Avoid a self-hash cycle: `integrity.digests` describes named subjects; its proposed `manifest_hash` is over the deterministically ordered digest-entry list, not over a record that includes that same hash. The current manifest logic hashes each parsed artifact object with `sha256_of`; writing the new artifact as the exact canonical JSON bytes (without a trailing newline) makes its file bytes match that declared canonical subject. No old evaluation directory is rewritten.
- Store the new artifact as deterministic UTF-8 JSON. If canonical bytes use the existing compact `canonical_json` profile, write those exact bytes; do not pretty-print and then describe a different canonical byte sequence. Keep schema version and canonicalization version independent.

### 4.3 Data and policy boundaries

- No conversion of absent/invalid values to zero; no `UNVERIFIED` to `CLEAR`/`TRIGGERED`; no automatic A1 adjudication; no qualification based only on schema validity, URI, or local hash.
- Represent source-specific requiredness only when the already approved metric contract supplies it. Do not add a global missing-input Final block, A10 subscription Final rule, provider selection, GMP hash qualification, or NIFTY freshness rule.
- A8-M may remain `UNKNOWN` when source-native session/timezone/availability facts are unavailable. The known `parse_datetime` behavior that attaches UTC to naive timestamps must not be used to qualify an A8-M record; fixing/using that path for NIFTY requires its own authorized source-contract implementation.

## 5. Exact implementation package (after the gates in §8)

**Target:** product review base `4b19faf…` on an explicitly authorized candidate/ref. This is not a change to Candidate M and does not select a canonical delivery branch.

| Path | Change after authorization |
|---|---|
| `schema/ipo-evaluation-record.v1.schema.json` | **New.** Draft 2020-12 schema for the approved version-1.0.0 output record; closed objects; conditionals for terminal/nonterminal resolution; strict types/enums/references. |
| `engine/ipo_screening/evaluation_record.py` | **New.** Pure projection/serializer from the existing `EvaluationRecord` to the versioned A15 record, plus strict schema and semantic validation. It may only pass through evidenced source facts and must preserve unknown/unqualified states. |
| `engine/ipo_screening/evaluation.py` | **Narrow modification.** Add the new artifact to `ARTIFACT_FILES`, `EvaluationRecord.artifacts()` and the generated manifest for new evaluations; write this artifact using its exact canonical UTF-8 bytes, preserve existing fields/result-hash inputs and historical directories, and have `EvaluationStore.verify_hashes()` verify the new manifest entry without relaxing existing checks. |
| `tests/test_evaluation_record_v1.py` | **New.** Focused schema, projection, fail-closed A7, deterministic serialization, cross-runtime golden bytes, hash-subject, and compatibility tests listed in §6. |
| `tests/test_reproducibility_store.py` | **Narrow test update.** Add the new artifact to the required-on-disk assertion and update the manifest artifact-count expectation from six to seven; retain the existing result-hash and append-only assertions unchanged. |

**No other path is in scope.** If implementation requires changes to `canonical.py`, `canonical_input.py`, enrichment/snapshot models, config, input schemas, API/UI, or any other test file, stop and request amended authority with the concrete dependency. Do not broaden the patch implicitly.

**Visible product result:** each newly written evaluation directory contains `evaluation-record.v1.json`, independently schema-validatable and covered by the record's artifact manifest. It is additive to the current local single-user evaluation store. This first increment does not add authentication, database, service, API or frontend architecture.

## 6. Focused validation and acceptance criteria

Run only the focused command below after implementation authority is granted; no full-suite or Windows claim follows from this specification.

```bash
python -m pytest tests/test_evaluation_record_v1.py tests/test_reproducibility_store.py
```

The new-record test module must include an independent Node.js reference check for the cross-runtime golden-byte vector, using the repository's existing JavaScript test runtime; it is part of this bounded command, not a new runtime application feature.

1. **Schema:** valid terminal and nonterminal examples pass; invalid types, unknown properties/enums, duplicate IDs, dangling references and invalid state combinations fail closed.
2. **Value/evidence states:** `VALUE`, `UNKNOWN`, `NOT_APPLICABLE`, `VERIFIED`, `UNVERIFIED`, qualification, validation and processing remain distinct; unknown is never zero; reason/evidence references are retained.
3. **A7 matrix:** verified knockout → `AVOID`; no verified knockout plus critical-safety gap → `INSUFFICIENT_DATA`; combined verified knockout/missing safety/score uncertainty preserves all facts; unverified-only case has `NONTERMINAL_UNRESOLVED`, evidence/reason, and no `final_outcome` (only after Ramki approves this representation).
4. **A1:** competing observations remain; no automatic winner; an adjudication is accepted only when every approved A1 element is present and attributable; otherwise field remains non-screenable.
5. **Times/revisions/digests:** pure serialization fixtures preserve distinct time meanings and original offsets; retrieval is not availability; unresolved timezone/revision stays unresolved; local/source-declared/attested digest origins and exact subjects cannot be conflated; no generic hash satisfies A9. No source is fetched or newly qualified.
6. **Metric boundaries:** pure record fixtures keep required-NIFTY UNKNOWN handling scoped to A8-M and required qualifying-hash status scoped to A9; A10 observations stay distinct/display-only and tests do not assert its open Final rule. This increment does not implement or retune any source-specific Final gate.
7. **Determinism:** serialize twice and in a fresh process to identical declared canonical bytes; compare the pinned fixture byte-for-byte with an independent second-runtime reference (Node.js, using the repository's existing JS test runtime); known-byte digest fixtures match. If the second runtime is unavailable or the existing profile cannot be proven, stop and obtain a test-profile decision—do not silently skip cross-runtime conformance or change the grammar/version.
8. **Store/compatibility:** the new artifact appears in the manifest and `EvaluationStore.verify_hashes()` reports no mismatch; new writes remain append-only; the existing v1.5 golden result hash and old artifact payloads remain unchanged; no historical directory is migrated or rewritten.
9. **Scope:** exact changed-path allowlist above; no source acquisition, scoring/config/fixture changes, A9/NIFTY runtime gate, UI, release or production work.

A passing result is implementation validation only. It is not independent acceptance, Phase 0 closure, canonical selection, merge, release or activation.

## 7. External dependencies deliberately excluded

These do not block the generic output-record implementation if missing facts remain explicit; they do block claims about the corresponding source-specific Final gate:

- **A8-M:** authoritative NSE price-index records, complete expected sessions and availability-by-cutoff/session-calendar evidence;
- **A9:** approved GMP source/event/as-of/cutoff and qualifying snapshot/hash subject;
- **A10:** subscription source contract and missing/unavailable Final consequence;
- **A1:** any actual field-level Ramki adjudication, which must be separately recorded when a conflict exists.

No NDAL contact, data purchase, provider assumption, A5/GCP fixture change, D1/D3 policy choice, or unrelated roadmap item is part of this package.

## 8. Exact outstanding decision and authorization

The smallest genuine owner gate is:

1. **Design disposition:** Ramki accepts or amends this exact recommended profile—especially closed-schema/conditional requiredness, the ordinary determinate `final_outcome` mapping, and A7 `NONTERMINAL_UNRESOLVED` with omitted `final_outcome`. This does **not** repeat or reopen A15 semantic approval; it resolves only concrete property/schema/serialization choices that A15 expressly left open.
2. **Implementation grant:** a separate written, exact-scope grant must authorize the five paths in §5, the focused tests in §6, target candidate/ref, and permitted publication. A11/A15 currently say this authority is not granted. If authorization is issued while Phase 0 remains OPEN, it should explicitly say whether this bounded work is permitted as an overlap/exception or must wait for Phase 0 closure; this package does not close Phase 0 or imply that exception.

Until those two items are recorded, make no product code, schema, test, configuration or fixture change. Once recorded, execute this package without re-investigating A15 semantics or asking for routine implementation choices. Candidate M remains unchanged throughout.

---
