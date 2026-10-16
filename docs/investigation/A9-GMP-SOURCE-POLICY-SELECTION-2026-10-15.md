# A9 Publisher-Level GMP Source-Policy Selection

**Record ID:** `A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15`
**Date:** 2026-10-15
**Branch:** `arena/573e69a4-ipo-screening-engine`
**Baseline reviewed:** remote branch tip `707405e9e81c80d791cedea9139d2ecfaf3ad02d`
**Status:** Model A selected as the source-policy direction. No individual publisher is selected, approved, or A9-qualified.
**Update (2026-10-15):** §6 records Ramki-approved project rules D1–D3 under this contract: evidence artifact and hash, availability by cutoff, and missing versus zero. They qualify no publisher.

## 1. Selected policy and authority limits

**Selected policy direction: MODEL A — PUBLISHER-LEVEL GMP OBSERVATION.** The declared source will be one specific, named publisher's own reported GMP observation. The engine must describe it as that publisher's reported value, not as a verified or dealer-native quote.

This is a policy selection, not provider approval, source qualification, or implementation authorization. It does not select Niva Market Watch, IPOStation, InvestorGain, IPO Watch, or another publisher. No current candidate is A9-qualified. Model B/dealer-level provenance is not required by this selected policy, but any provenance claim must remain within the evidence actually available.

Multiple publishers that share the same upstream source are not automatically independent corroboration.

This is a follow-on to the [A9 GMP Source-Model Decision Record](A9-GMP-SOURCE-MODEL-DECISION-2026-10-15.md). It supersedes only that record's earlier statement that Model A had not yet been selected; the investigation findings and conclusion that no candidate was qualified remain in force.

## 2. Evidence carried forward

**Observed in the completed review:** Niva Market Watch and IPOStation displayed issue-specific GMP values. InvestorGain displayed dated history but no identifiable dealer-level quote. Values and timestamps differed across pages; some pages showed only a date or page-update time rather than distinct observation, publication, and retrieval times. No original response bytes or headers were retained and no evidence hash was computed. A currently displayed history is not proof that the same observation was available historically.

**Publisher claims:** Niva names InvestorGain as its GMP source. IPOStation names InvestorGain as its primary feed and IPO Watch as its cross-check. Those source and cross-check claims do not independently establish how the values were obtained or that the publishers are independent.

**Unresolved:** Timezone and evaluation-cutoff compatibility, freshness/staleness, historical reproducibility, source-artifact retention, missing-versus-zero semantics, conflict/correction behavior, and the exact integrity-hash subject remain insufficiently established. See the linked decision record for the reviewed page references and detailed findings; no new provider investigation is implied here.

## 3. Minimum source-specific qualification contract

All eight requirements below remain **UNRESOLVED for any named publisher**. The listed evidence describes what would resolve each gap; it does not prescribe unsupported source capabilities or numerical rules.

| # | Requirement | Evidence needed to resolve it |
|---|---|---|
| **1** | **Publisher identity and traceable issue-specific observation.** | Select one named publisher and retain evidence tying that publisher's own page or record to the particular IPO observation being evaluated. The trace must identify the source and the issue-specific record without implying a dealer source that is not exposed. |
| **2** | **IPO/issue identity and exact semantics of the published GMP value.** | Evidence must identify the IPO/issue and define what the publisher's displayed GMP field means, including the value's units and any other source-defined interpretation needed to reproduce it. A visible number alone is insufficient. |
| **3** | **Observation, publication, and retrieval-time semantics wherever available; timezone and evaluation-cutoff compatibility.** | Source-specific evidence must distinguish the meaning of each available timestamp and its timezone. The selected evaluation cutoff must be explicitly defined and shown compatible with the source's time fields; no cutoff is set by this record. |
| **4** | **Evidence-backed freshness and stale-value behavior.** | Establish the source's update/freshness behavior and what happens when an observation is delayed or stale, using source-specific documentation or retained observations. Any allowed-age rule remains for explicit policy selection; no threshold is invented here. |
| **5** | **Retained source artifact and reproducible integrity hash with a defined hash subject.** | Preserve the source artifact used for an evaluation with enough retrieval context to reproduce the capture. The source-specific contract must identify the exact hash subject and reproducible hashing procedure; neither is specified here. |
| **6** | **Missing versus genuine-zero representation.** | Source-specific evidence must distinguish a missing or unavailable observation from an actual zero GMP, including the publisher's displayed and retained representation. No sentinel or missing-value behavior is assumed. |
| **7** | **Conflict, correction, revision, and precedence behavior.** | Establish how the selected publisher handles conflicting inputs, corrections, revisions, and any source fallback or precedence. Evidence must distinguish a revised value from an overwritten value; no conflict rule or precedence is invented here. |
| **8** | **Sufficient retained history to reproduce the observation used by an evaluation.** | Retain enough issue-specific historical evidence to reproduce the exact publisher observation used, including relevant version or correction information and its evaluation-time availability. A mutable current page alone is insufficient. |

A hash can establish the integrity of the captured bytes; it does not independently establish the bytes' source authenticity or the truth of an underlying quote.

## 4. A9 and Final-mode consequences

A9 remains fail-closed until one named publisher satisfies the source-specific qualification contract. The selected policy direction does not change the gate or Final-mode behavior:

- Missing GMP remains nonterminal with reason `MISSING`.
- Present but unqualified GMP remains nonterminal with reason `SOURCE_UNQUALIFIED`.
- Neither withheld case sets `final_outcome`.
- A publisher's displayed value alone does not enable Final.

No scoring formulas, schemas, serialization, existing result hashes, or other verified behavior are changed or authorized to change by this record. No connector or source ingestion is authorized.

## 5. Next action

Assess **one named publisher** against the eight requirements above using concrete source evidence. Do not restart broad candidate discovery. Until that assessment establishes a qualifying source, preserve the existing A9 fail-closed behavior.

## 6. Approved project rules D1–D3 (2026-10-15)

- **Decision IDs:** D1, D2, D3 (GMP source-policy rules under the §3 contract)
- **Decision status:** RAMKI-APPROVED PRODUCT POLICY. These are user-approved decisions, not Arena recommendations.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-15 (Asia/Calcutta). No decision time is supplied or asserted.
- **Authorization basis:** Ramki's explicit approval of the three decisions quoted below, given in the 2026-10-15 instruction "Implement approved GMP source-policy decisions D1–D3".
- **Repository and baseline:** `ramkivs/ipo-screening-engine`; fixed session branch `arena/573e69a4-ipo-screening-engine` at remotely verified commit `9dba813b88d9f4ff238a4f94c80dd1e7cbb11dd4`.
- **Scope:** three requirements of the §3 contract, for any named publisher:
  - D1 covers requirement 5 (artifact and hash);
  - D2 covers the evaluation-time availability part of requirement 8;
  - D3 covers requirement 6 (missing versus zero).
  - The rules select, approve and qualify no publisher.
- **Where recorded:** here, as Ramki instructed, so that no competing decision document exists. GOV-001's default is a separate `handoff/decisions/` record; this section carries the elements GOV-001 requires.
- **Implementation authority:** GRANTED, within A16's personal-use scope, for the minimum enforcement listed under "Implementation". Nothing else is authorized.

### 6.1 Approved decisions

**D1 — Evidence artifact and hash.**
> A retained rendered-text capture plus its file hash is acceptable only as a clearly labelled publisher-reported observation. The hash establishes integrity of the retained capture, not publisher authenticity, source-native bytes, or dealer verification. Never describe a rendered capture as raw/source-native evidence.

**D2 — Availability by cutoff.**
> To qualify for an evaluation cutoff, the evidence capture must have been obtained at or before the evaluation timestamp. A later capture of a reading with an earlier displayed timestamp does not prove the reading was available at the earlier cutoff. Enforce this consistently with A17-1. Do not infer historical availability from a publisher's displayed timestamp.

**D3 — Missing versus zero.**
> "Not quoted yet" maps to MISSING. A displayed ₹0 maps to SOURCE_UNQUALIFIED. A numeric zero alone is not valid qualifying GMP evidence.

**Origin.** The [MarketLiveIPOGMP qualification record](A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md) §15.5 framed these as open decisions. They adopt the substance of that record's §8 proposals, to the extent of the approved text above:
- PR-3 (artifact and hash) for D1;
- PR-1's "retrieved at or before the evaluation timestamp" clause for D2;
- PR-4a and PR-4b for D3.

PR-4f and PR-5 remain unadopted.

### 6.2 Relationship to v1.5 and existing decisions

- **v1.5, not changed.** §19 requires the GMP snapshot and source hashes for Final. It defines no GMP hash subject, availability rule or zero semantics. D1–D3 are project-level resolutions of those gaps, not v1.5 text.
- **A9 is unchanged.** Final stays withheld for every present GMP observation (`SOURCE_UNQUALIFIED`) and every missing one (`MISSING`). D1–D3 add no qualified path.
- **A17 is unchanged.**
  - D2 uses A17-1's cutoff instant: the evaluation timestamp, inclusive. As under A17-1, both instants need an explicit UTC offset, with no tolerance, and the check fails closed otherwise.
  - D2 governs qualification evidence. It does not alter A17 scoring eligibility, which still compares the source timestamp only. A17-2 (24 h) and A17-3 (publisher labels only) are untouched.
- **Rendered-capture precedent.** D1 departs, for GMP only, from the tracker precedent that rendered captures leave source-native qualification open (tracker l.30, l.107). It accepts a rendered capture only as a publisher-reported observation. It does not make one source-native.

### 6.3 Implementation (minimum necessary)

The artifact and hash follow the existing evidence convention. `capture-manifest.json` declares, for each retained file:
- the file itself, with its byte count and uppercase SHA-256 of the exact file bytes;
- the UTC window bracketing its retrieval;
- `captureMethod.rawProviderResponseBytesCaptured: false` for a rendered capture.

| # | Change | Why |
|---|---|---|
| 1 | **New `engine/ipo_screening/gmp_evidence.py`:**<br>• **D1** `load_rendered_capture` accepts only a manifest that declares a rendered capture, and only a file inside the package. It recomputes the file's SHA-256 against the declared digest and byte count. It classifies the result `PUBLISHER_REPORTED_RENDERED_CAPTURE`, with a fixed publisher-reported label. Its source-native, publisher-authentication and dealer-verification properties are always false.<br>• **D2** `capture_obtained_by` is true only when the window end is at or before the evaluation timestamp. The window end is the instant by which the capture had certainly been obtained. A publisher's displayed or site-wide update time is never used.<br>• **D3** `classify_displayed_gmp` returns MISSING for the exact "Not quoted yet", ZERO for a displayed zero (`SOURCE_UNQUALIFIED`), AMOUNT for a well-formed non-zero amount (candidate only), and MALFORMED for anything else (rejected).<br>• `assess_capture` combines the three. Its best result is "eligible for cutoff consideration", which is not qualification; the A9 reason it reports is always nonterminal. | Gives D1–D3 one executable definition over the retained evidence packages. No existing code read the capture manifests to verify a capture's file hash or capture time. |
| 2 | **`connectors/adapters.py`, `GmpSignalAdapter`:**<br>• D3 classification of the premium and percentage fields. "Not quoted yet" gives no value. A displayed zero is kept as a present 0.0; a rupee-only zero records `pct` 0.0, because `market.gmp` carries only `pct` and a zero premium is 0% of any issue price.<br>• Malformed displays, or ones that contradict each other, raise `ConnectorPayloadError`. Examples: "Not quoted yet" beside a value or trend label, or a zero beside a non-zero value.<br>• D2: the capture time is taken only from the payload. It is no longer filled with the normalisation clock. | The adapter reads both "₹0" and malformed strings as no value, which A9 then reports as MISSING (contrary to D3).<br>It also substitutes the current time for a missing retrieval time. That substitute reaches `_sources` and the A15 record as `LOCAL_RETRIEVED_AT`, an invented capture time. |
| 3 | **`connectors/interfaces.py`:** `ExternalSnapshot.retrieval_timestamp` may be `None`, and `to_source_ref()` omits an unknown retrieval time. | So no capture time is asserted when none was recorded. Other adapters are unchanged. |

**Already compliant, so not changed:**
- **Evaluation-input path.**
  - `pct: null` with no trend gives `MISSING`.
  - `pct: 0` gives `SOURCE_UNQUALIFIED`: the snapshot keeps a present zero, and the gate counts any non-null value.
  - A display string in `pct` (for example "₹0" or "Not quoted yet") fails schema validation before any scoring or store write.
- **A9 gate.** It has no qualified path. It does not accept a generic market-snapshot digest or a connector `content_hash`; A15 already records the latter as `LEGACY_UNRESOLVED` / `LEGACY_UNSPECIFIED`.
- **A15.** It records a retrieval time as known only when it carries an explicit offset; otherwise the time is `TIMEZONE_UNRESOLVED`.

**Deliberately not changed:**
- the A9 gate and its messages;
- the input and A15 schemas;
- configuration, scoring formulas and weights;
- the frozen core, the A17 cutoff module and the pipeline;
- the golden result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.

No retrieval-time or hash field was added.

**Precise limitation: D1 and D2 cannot be established while an evaluation runs, so A9 keeps failing closed.** Nothing in the v1.5 contracts links an evaluation's `market.gmp` to a retained capture:
- `market.gmp` is closed, with only `as_of`, `pct`, `trend` and `source_id`.
- The closed `_sources[]` entry carries one optional `retrieval_timestamp`. It is a single instant, not a window, and is not tied to a declared artifact.
- That entry's `content_hash` has no declared subject or representation.
- `source_type` has no class for a publisher-reported rendered capture.
- The A15 digest vocabulary has no rendered-capture subject. Its `RAW_ARTIFACT_BYTES` would describe the capture as raw, which D1 forbids.

An A9 qualified path would need two things, each requiring its own decision and a schema change:
1. a persisted, per-evaluation GMP evidence reference — the capture manifest and artifact, or equivalent — carrying the file hash, its publisher-reported rendered class and the capture window;
2. a matching A15 digest subject and label.

*Correction (2026-10-16): this paragraph overstates the limitation. An evidence reference fits existing v1.5 fields, and A15 1.1.0 can represent the file digest. See §7.1.*

### 6.4 Evidence and tests

- **Focused tests:** `tests/test_d1_d3_gmp_source_policy.py`. It had 84 tests at `805affe`, and 85 after the 2026-10-16 duplicate-id test (§7.11.4). Coverage:
  - the publisher-reported label;
  - hash verification of the declared retained file, including altered, missing and misdeclared copies;
  - an artifact id declared more than once (added 2026-10-16);
  - a window ending at the cutoff, a cutoff inside the window, a window ending after the cutoff, and IST offsets;
  - a later byte-identical recapture;
  - offset-less and missing windows;
  - "Not quoted yet", zero, malformed and well-formed displays;
  - the connector through to the A9 gate;
  - the evaluation-input path;
  - A17-2/A17-3 unchanged.
- **Mutation check:** each of eight reversions fails the focused tests.
- **Full suite and integrity checks:** the full Python suite, `verify_frozen_core()`, `verify_golden_result()` and `verify_v1_6_implementation()` results are recorded in the tracker's D1–D3 section.

### 6.5 Consequences and unresolved dependencies

- **No publisher qualifies.** For MarketLiveIPOGMP, R7 still needs source evidence. See the qualification record §16.
- **Still open:**
  - the A9 qualified path and its representation (§6.3);
  - R7, and R8's history before capture;
  - §8 PR-4f and PR-5.
- **D3 covers only the exact "Not quoted yet" and a displayed zero.** Other markers fail closed as malformed, for example InvestorGain's "₹ --" or PapsDigital's "N/A". Well-formed negative amounts keep their existing treatment as values (the input schema allows `pct` down to −1000). D3 does not address them, and no qualification follows.

## 7. GMP evidence linkage — proposal history and current implementation (2026-10-16)

- **Status (historical at proposal creation; superseded by A18):** This section began as an Arena proposal for L1–L4. Ramki subsequently approved L1 as revised, L2-a, L3-a, and L4-a with no schema/version change, as recorded in [`handoff/decisions/A18-gmp-evidence-linkage-contract.md`](../../handoff/decisions/A18-gmp-evidence-linkage-contract.md). Current implementation and verification status are in §7.12. No individual publisher is approved or A9-qualified.
- **Baseline:** D1–D3 implementation `805affe`, which is also the authoritative `arena/573e69a4-ipo-screening-engine` tip (verified 2026-10-15T19:00:14Z). First published in `2de60b6`.
- **Revision (2026-10-16, second pass):** revised in place after the decision-boundary review in §7.11. The superseded wording remains in `2de60b6`. Three changes:
  1. The capture window is never entered as an exact retrieval time.
  2. The pin covers the manifest.
  3. An issue-identity binding is added.

### 7.1 The gap, and a correction to §6.3

At proposal time, `gmp_evidence.py` could verify a retained capture's D1 integrity, D2 availability by cutoff and D3 displayed state, but no approved contract linked an evaluation's `market.gmp` value to that capture, digest, window or displayed text. A18 subsequently approved that link contract; §7.12 records its implementation.

The v1.5 input already has generic fields that can carry such a reference:
- `market.gmp.source_id` → a `_sources[]` entry with `uri`, `content_hash` and `retrieval_timestamp`;
- `_evidence[<field path>]` entries with `locator` and `quote` (alias `quoted_text`).

A probe on 2026-10-16 added the §7.2 reference for ML-T to the golden input, validated it against the unchanged v1.5 schema, and ran it in Final mode:
- The input validated with no findings.
- A15 kept the `uri` and the line locators. The quotes stayed in `evidence.json`.
- The probe supplied the window end as `retrieval_timestamp`, and A15 recorded it as a KNOWN `LOCAL_RETRIEVED_AT`. That overstates it, because the window end is not the capture time (§7.11.1).
- The pinned SHA-256 was recorded as `LEGACY_UNRESOLVED` / `LEGACY_UNSPECIFIED`, with algorithm and subject `UNKNOWN`.
- No quote was checked against the artifact, and the A9 gate read none of these fields. The outcome stayed `SOURCE_UNQUALIFIED`.
- A capture dated after the evaluation drew no D2 signal.

**The gap is therefore an approved contract plus a runtime check, not a field.** Two §6.3 statements overstated it:
1. No input-schema change is needed to carry the reference.
2. In the A15 implementation package (§1.3), `RAW_ARTIFACT_BYTES` is the subject for raw-byte digests, which take no canonicalization. The A15 decision (item 6, l.38) says a locally computed digest identifies only the exact local bytes, never provider bytes. The retained file's digest is therefore representable in A15 1.1.0. Whether that token is acceptable under D1's wording is decision L2.

### 7.2 Minimum input reference (existing v1.5 fields only)

| Field | Content |
|---|---|
| `market.gmp.source_id` | `S`, the linked source |
| `_sources[S].source_type` | `MARKET_DATA` |
| `_sources[S].uri` | repository-relative path to a capture manifest under `evidence/gmp-observations/`, then `#`, then the artifact id |
| `_sources[S].content_hash` | `sha256:` followed by the 64-hex digest of the capture manifest's bytes. The manifest declares the artifact's SHA-256, its byte count and its retrieval window, so this one pin makes all three tamper-evident. *(Revised: the first version pinned only the artifact, which left the window unprotected.)* |
| `_sources[S].retrieval_timestamp` | **absent.** The manifest records no exact receipt time (`exactReceiptTimeCaptured: false`), and its window end is not one (§7.11.1). This field may be set only if a future manifest records an exact receipt time, and it must then equal that time. *(Revised: the first version entered the window end here.)* |
| `_evidence["market.gmp.pct"]` | `source_id` `S`; `locator` `line <n>` of the artifact; `quote` = the exact displayed percentage on that line; `extraction_method` `MANUAL_ENTRY` |
| `_evidence["market.gmp.as_of"]` | `source_id` `S`; `locator` `line <n>`; `quote` = the publisher stamp that `as_of` was transcribed from |
| `_evidence["company_name"]` | `source_id` `S`; `locator` `line 1`; `quote` = the capture's title line, which names the issue. This binds the capture to the evaluated IPO (L3). *(Added in the revision.)* |

Worked example (ML-T):

```json
"market": {"gmp": {"as_of": "2026-10-15T16:02:00+05:30", "pct": 71.4, "trend": null, "source_id": "SRC-MLGMP-TONBO-T"}},
"_sources": [{"source_id": "SRC-MLGMP-TONBO-T", "source_type": "MARKET_DATA",
  "uri": "evidence/gmp-observations/marketliveipogmp-tonbo-20261015/capture-manifest.json#ml-tonbo-chunk-0",
  "content_hash": "sha256:a4f83492455f4691159ba1f049547803cfa0db2aee248b7dbdfb4c990cfbb87d"}],
"_evidence": {
  "company_name": {"source_id": "SRC-MLGMP-TONBO-T", "locator": "line 1", "quote": "# Tonbo Imaging IndiaIPO GMP Today", "extraction_method": "MANUAL_ENTRY"},
  "market.gmp.pct": {"source_id": "SRC-MLGMP-TONBO-T", "locator": "line 7", "quote": "+71.4%", "extraction_method": "MANUAL_ENTRY"},
  "market.gmp.as_of": {"source_id": "SRC-MLGMP-TONBO-T", "locator": "line 84", "quote": "4:02 pm IST on Thu, 15 Oct, 2026", "extraction_method": "MANUAL_ENTRY"}}
```

Notes on the example:
- ML-T line 7 is `₹500+71.4%`. Line 84 gives the stamp with its year and zone; lines 11 and 13 split `15 Oct, 4:02 pm` from `IST`.
- A ₹0 reading quotes `0.0%` with `pct: 0`. "Not quoted yet" is quoted with `pct: null`.
- A publisher trend label would need one more entry, `_evidence["market.gmp.trend"]`. MarketLiveIPOGMP publishes none.
- The pin is the SHA-256 of `capture-manifest.json` as it stands at `9e0e4ed`. The artifact's own digest, `33516f86…705d`, is declared inside that manifest.
- **The pinned manifest must not change.** This manifest was amended twice after it was created (`6ecd26c`, `9e0e4ed`). Once an evaluation references a manifest, any later follow-up goes into a new file or package. A changed manifest makes the link fail closed (§7.5), and the pinned bytes stay in the repository history.
- `S` must be the `source_id` of exactly one `_sources` entry. The v1.5 schema does not enforce unique source ids, so the verifier must.

### 7.3 Minimum evaluation-record linkage (A15 1.1.0)

The existing mapping already gives:
- the source `S` with `uri`. With `retrieval_timestamp` absent, it records no `LOCAL_RETRIEVED_AT` fact;
- the evidence objects with `locator`, and `artifact_ref` pointing to the preserved `evidence.json` entry that holds the quote.

The proposal adds only three things, and only when a link is attempted:
1. **For a verified link, two digests on `S`** (`digest_refs`): one for the manifest and one for the artifact. Each has:
   - `algorithm` `SHA-256`;
   - `digest_value` recomputed from the bytes read, in lowercase hex;
   - `subject_kind` `RAW_ARTIFACT_BYTES` (L2-a);
   - `subject_ref` = the repository-relative path;
   - `origin` `LOCAL_COMPUTED`;
   - `evidence_refs` = the link's evidence objects.

   They replace the `LEGACY_UNRESOLVED` mapping of that `content_hash`. That amends the A15 package rule §1.3 for this case only.
2. **For a verified manifest, the window as an unknown retrieval time.** This is one `LOCAL_RETRIEVED_AT` fact:
   - `state` `UNKNOWN`;
   - `source_text` = the ISO 8601 interval `<notBefore>/<notAfter>`, copied from the manifest;
   - `reason` `UNAVAILABLE`, with the message "exact receipt time not captured; the manifest records only this bracketing window".

   The A15 1.1.0 schema requires a reason for `UNKNOWN` and forbids `normalized_utc`, so no instant is asserted. No schema change is needed. *(Added in the revision.)*
3. **One diagnostic.** The code is free text (for example `A9_GMP_EVIDENCE_LINK`). It records:
   - the result: `VERIFIED`, `NOT_AVAILABLE_BY_CUTOFF` or `FAILED: <reason>`;
   - the D1 label verbatim;
   - the D3 state;
   - both digests;
   - the window.

   The record therefore keeps what was verified even if the files later change.

`outcome_resolution` is unchanged: `SOURCE_UNQUALIFIED`, or `MISSING`, and no `final_outcome`.

### 7.4 Verification

All of the following must pass; otherwise the result is `FAILED`.

1. **Location:**
   - `S` is the `source_id` of exactly one `_sources` entry.
   - Its `uri` names a manifest inside `evidence/gmp-observations/`, with no absolute path, `..` or URL.
   - It names an artifact that the manifest declares exactly once. D1 rejects a duplicated id (§7.11.4).
2. **Manifest pin:** read the manifest bytes once. `content_hash` must equal their SHA-256, and the same bytes are parsed. A manifest edited after pinning fails, including one with a shifted window.
3. **D1:** `load_rendered_capture` recomputes the artifact's SHA-256 and byte count against the pinned manifest's declaration. This establishes integrity only. All later checks use the bytes that were hashed.
4. **Capture time** *(revised)*:
   - The exact capture instant is unknown. The pinned window brackets it: it lies between `notBefore` and `notAfter`.
   - D2 is proven only if `notAfter`, the latest possible capture time, is at or before the evaluation timestamp: `capture_obtained_by(capture, evaluation timestamp)`.
   - An evaluation inside the window fails closed, and so does a window without explicit offsets.
   - `retrieval_timestamp` must be absent unless the manifest records an exact receipt time. No current manifest does.
   - The publisher stamp is never the capture time.
5. **Identity** *(added)*: the `company_name` quote is line 1 of the verified text.
   - Take the text between `# ` and the first `IPO GMP`. The two evidenced titles are ML-T:1 `# Tonbo Imaging IndiaIPO GMP Today` and ML-HM:1 `# Hero MotorsIPO GMP & Listing Price`. The rendering joins the name to "IPO".
   - Case-fold it and collapse each run of non-alphanumeric characters to one space.
   - The result must equal `company_name` normalized the same way, after dropping one trailing `Limited`, `Ltd` or `Ltd.`.
6. **Value:** the `pct` quote occurs on its `locator` line of the verified text. `classify_displayed_gmp(quote, unit="%")` must give ZERO or AMOUNT equal to `pct`, or MISSING with `pct: null`. MALFORMED fails.
7. **Stamp:** the `as_of` quote occurs on its line and equals `as_of` rendered in the publisher's stamp format (L3).
   - `as_of` must not be later than `notAfter`.
   - A stamp inside the window is possible and is not a contradiction. *(Revised: "the capture time" was not a known instant.)*
8. **A17:** the existing rules then apply to `as_of` unchanged: cutoff, 24 h maximum age, and publisher labels only.

**Trust limit:**
- The window is the sandbox clock read before and after the tool call, checked against GitHub's `Date` header. The manifest itself says the window "does not establish when the publisher generated the content or whether the tool served cached content".
- The pin makes the recorded window tamper-evident from the moment the evaluation input is written. It does not prove the window was true when it was recorded.
- **Historical proposal note, superseded by A18 and §7.12:** duplicate JSON keys are now rejected by the strict parser at the scoped evaluation-input boundaries and when parsing the pinned manifest bytes. The parser change does not alter permissive configuration or stored-record readers; it is not a global loader change.

### 7.5 Behaviour

| Case | Link result | A9 | Scoring |
|---|---|---|---|
| **Absent:** `S` has no evidence-manifest `uri`; this covers every current input | none, and no diagnostic | unchanged | unchanged (A17) |
| **Malformed:**<br>• bad `uri`;<br>• pin not `sha256:` plus 64 hex;<br>• a `retrieval_timestamp` present although the manifest records no exact receipt time;<br>• a window that is missing, inverted or without offsets;<br>• a missing `_evidence` entry (`pct`, `as_of` or `company_name`);<br>• `S` not exactly one `_sources` entry. | `FAILED: <reason>` | `SOURCE_UNQUALIFIED` / `MISSING` | unchanged |
| **Mismatched:**<br>• pin ≠ the manifest's digest, for example an edited manifest or a shifted window;<br>• the artifact ≠ its declared digest or byte count, or a file is missing;<br>• an artifact id declared more than once;<br>• the title quote ≠ `company_name` (another issue's capture);<br>• a quote is not on its line;<br>• the value ≠ `pct`, or the stamp ≠ `as_of`;<br>• `as_of` after the window end;<br>• the manifest is not a rendered capture. | `FAILED: <reason>` | same | unchanged |
| **Captured after the cutoff:** window end after the evaluation timestamp, evaluation inside the window, or an evaluation time with no timezone | `NOT_AVAILABLE_BY_CUTOFF`, never retroactive | same | unchanged |
| **All checks pass** | `VERIFIED`: eligible for cutoff consideration only | same | unchanged |

Each case is schema-valid v1.5 input, so failures are recorded rather than rejected (L4).

### 7.6 Backward compatibility

- **Existing inputs.** No current input has an evidence-manifest `uri`; connector sources use `connector://`. Existing results, result hashes (golden `e84f8bc0…`) and A15 records are therefore unchanged.
- **Diagnostics.** None is added unless a link is attempted.
- **Stored evaluations** are not re-interpreted (A15 decision item 9, l.41).
- **Connector.** A connector `content_hash` is a JSON-payload digest and stays `LEGACY_UNRESOLVED`.
- **Frozen core.** `market.gmp` keeps its shape, so nothing reaches the frozen core.

### 7.7 Schema and version

- **Input v1.5 schema:** no change is needed. No in-place change is authorized in any case (A15 decision, l.62).
- **A15 schema:** no change under L2-a.
  - L2-b would add one `subject_kind` value, for example `RENDERED_CAPTURE_BYTES`.
  - It would bump `$id` and `RECORD_SCHEMA_VERSION` from 1.1.0 to 1.2.0 and update the schema tests.
  - Existing 1.1.0 records would stay valid, with no migration.
- **Code scope proposed before A18:**
  - a linkage verifier in `gmp_evidence.py` that reuses the D1–D3 functions;
  - the §7.3 digest and diagnostic in the A15 builder;
  - no change to the A9 gate's outcome logic. A18 later authorized this bounded scope; §7.12 records the implementation.

### 7.8 Tests required

- **Substitution:**
  - swapped artifact bytes;
  - a manifest digest edited to match them (caught by the manifest pin);
  - another artifact id in the same manifest;
  - a duplicated artifact id;
  - another IPO's capture with an equal value and stamp (caught by the identity line);
  - a later recapture used for an earlier evaluation.
- **Stale evidence:**
  - `as_of` older than 24 h at evaluation;
  - window end after the evaluation;
  - evaluation inside the window;
  - a manifest window shifted earlier (caught by the pin);
  - an offset-less window;
  - a `retrieval_timestamp` present without an exact receipt time.
- **Missing evidence:**
  - no `S`, or two `_sources` entries with id `S`;
  - an `S` without an evidence-manifest `uri` (record unchanged);
  - a missing manifest or artifact;
  - a missing `pct`, `as_of` or `company_name` evidence entry.
- **Mismatched value or artifact:**
  - a quote on another line;
  - a quoted value ≠ `pct`;
  - a rupee quote for `pct`;
  - "Not quoted yet" with a non-null `pct`;
  - `0.0%` must give ZERO and `SOURCE_UNQUALIFIED`;
  - a stamp ≠ the rendered `as_of`;
  - `as_of` after the window end;
  - a title line naming another issue.
- **A15 record:**
  - the window is `UNKNOWN` with an interval `source_text` and no `normalized_utc`;
  - two `LOCAL_COMPUTED` digests in lowercase hex.
- **Non-regression:**
  - golden hash and existing A15 records byte-identical;
  - connector sources stay `LEGACY_UNRESOLVED`;
  - A9 never terminal for any link result;
  - A17 suite unchanged;
  - frozen-core, golden and v1.6 verifiers PASS.

### 7.9 Eligibility is not qualification

A `VERIFIED` link shows only that one evaluated observation meets D1–D3 for that evaluation. It does not qualify MarketLiveIPOGMP or any other publisher:
- R7 and R8's history stay open.
- A15 digests do not qualify an A9 input (A15 decision, l.49 and l.60).
- A9 stays fail-closed until a separately approved qualified path exists.

### 7.10 Decisions requested (historical; superseded by A18)

| Decision | (a) | (b) |
|---|---|---|
| **L1:** input convention | Adopt §7.2 as revised over existing v1.5 fields:<br>• manifest pin;<br>• no `retrieval_timestamp`;<br>• quotes for `pct`, `as_of` and `company_name`. | Not adopted |
| **L2:** A15 digest subject | `RAW_ARTIFACT_BYTES` in A15's raw-byte sense for the manifest and the artifact, with the D1 label in the diagnostic. The window is recorded as an `UNKNOWN` `LOCAL_RETRIEVED_AT` (§7.3). No schema change. | A dedicated subject kind; A15 1.2.0 |
| **L3:** stamp and identity binding | Check `as_of` against the quoted stamp in the publisher's format: MarketLiveIPOGMP `h:mm am/pm IST on Ddd, D Mon, YYYY` (ML-T line 84). Check the title line against `company_name` (§7.4 step 5). | Require only `as_of` ≤ window end. A mistranscribed later stamp could then make stale evidence look fresh, and another issue's capture with equal values would pass. |
| **L4:** failure handling | Record failures as nonterminal diagnostics | Reject structurally malformed references before scoring |

**Recommendation at proposal time:** L1 as revised, L2-a, L3-a and L4-a, which need no schema or version change. A18 records Ramki's subsequent approval of these choices. The authorization review and question below are retained as historical proposal context; §7.12 records implementation status. A9 stays fail-closed throughout.

### 7.11 Decision-boundary review (2026-10-16)

Checked at 2026-10-15T19:00:14Z (00:30 IST, 16 Oct) against `805affe`, the authoritative tip. This section records the decision-boundary analysis and the status at that time. A18 later records Ramki's approval and supersedes the authorization-status statements below.

#### 7.11.1 Capture-time semantics

What the retained evidence says (ML-T `capture-manifest.json`, `captureMethod`):
- `exactReceiptTimeCaptured: false`. No retained field records when the capture was received.
- `retrievalWindowBasis`: the window is the sandbox UTC clock read before and after the sequential tool call, and one read can close one window and open the next. The window "does not establish when the publisher generated the content or whether the tool served cached content".
- The displayed stamp (`4:02 pm IST`) is the publisher's recording time (qualification record R3, I2). It is not a capture time.

Resolution, with no invented semantics:
- **Where the capture instant lies.** It lies between `notBefore` and `notAfter`, and nothing narrows it further.
- **Upper bound only.** `notAfter` is the latest possible capture time and is used only as an upper bound.
  - If `notAfter` ≤ E, the capture happened at or before E. D2 as implemented (`capture_obtained_by`) is therefore sound.
  - It is also conservative: an E inside the window is not proven and fails closed, even though the capture may have come first.
- **Never recorded as the capture time.** No contract shows that the window end equals the capture time.
  - The first §7.2 put it in `retrieval_timestamp`, which A15 persists as an exact KNOWN `LOCAL_RETRIEVED_AT` (probe, §7.1). That row is withdrawn.
- **Honest A15 representation.** A15 1.1.0 can carry the window as `LOCAL_RETRIEVED_AT` with `state` `UNKNOWN`, the interval as `source_text` and `reason` `UNAVAILABLE` (§7.3).
  - Checked by validating instances against `timestampFact` on 2026-10-16. That form is valid.
  - Adding `normalized_utc`, omitting the reason, or using a code outside the enum is rejected.
- **Not an interval in `retrieval_timestamp`.** The builder records any non-instant `retrieval_timestamp` as UNKNOWN `INVALID` (`evaluation_record.py` l.202–204). An interval must not go in that field.
- **Code wording.** Wording that called the window end "the capture time" was corrected (§7.11.4). The behaviour was already the upper-bound rule.

#### 7.11.2 Historical authorization review of L1–L4 (superseded by A18)

Prior explicit decisions checked:
- **D1–D3** (§6.1): implementation authority covered only the listed minimum.
- **A15 decision:** l.41 requires later versions and migrations to be separately specified and approved. l.62 authorizes no in-place v1.5 schema change.
- **A15 package §1.3:** an opaque `content_hash` maps to `LEGACY_UNRESOLVED`.
- **A16:**
  - l.20: no authority for "unqualified source behavior";
  - l.28: "A15's approved output profile remains bounded to its exact implementation";
  - l.32: a policy or data decision remains necessary for metric behaviour that depends on it;
  - l.34: no "live-source integrations without evidence/contracts".

| | Exact rule | Existing behaviour | Validity evidence | Compatibility | Already authorized? | New decision |
|---|---|---|---|---|---|---|
| **L1** | §7.2 as revised | Fields accepted and carried; `content_hash` → `LEGACY_UNRESOLVED`; quotes unchecked; no link | Probe: schema-valid v1.5 input; A9 `SOURCE_UNQUALIFIED` | No current input has an evidence-manifest `uri`, so none changes | No. It gives generic fields a GMP-evidence meaning (A16 l.32, l.34). | Yes |
| **L2** | Two `LOCAL_COMPUTED` digests and the `UNKNOWN` window fact, for a verified link (§7.3) | `LEGACY_UNRESOLVED` digest; no retrieval fact when `retrieval_timestamp` is absent | Schema enum values exist; window fact validated (§7.11.1) | Only linked evaluations change; stored records are not re-interpreted | No. It amends the A15 mapping (A15 l.41; A16 l.28). | Yes |
| **L3** | Stamp in the publisher's format; title-line identity; `as_of` ≤ window end (§7.4 steps 5 and 7) | None | Evidenced only for MarketLiveIPOGMP: ML-T:84, ML-T:1, ML-HM:1 | Publisher-specific; another publisher needs its own evidence | No. It sets publisher-specific verification semantics (A16 l.32). | Yes |
| **L4** | Failures are nonterminal diagnostics (§7.5) | No link, so no failure | Matches the existing A9 nonterminal pattern | No input is newly rejected | No. It is part of the same contract. | Yes, with L1 |

At the time of this decision-boundary review, none was authorized. That review-time status is superseded by A18 (2026-10-16), which records approval of L1 as revised, L2-a, L3-a, and L4-a with no schema/version change. The (a)/(b) alternatives in §7.10 are technical sub-choices; the later approval resolves them as recorded in A18.

#### 7.11.3 Questions A–G

| | Under the revised proposal | Status at the review time (no linkage) |
|---|---|---|
| **A. Identity** | Manifest, artifact and issue are identified separately:<br>• the manifest pin fixes the manifest;<br>• the manifest's single declaration of the `#` artifact id fixes the artifact's digest and bytes, and D1 rejects an undeclared or duplicated id;<br>• the title quote fixes the issue. | Not established |
| **B. Hash** | Both digests are recomputed from the bytes read. A mismatch is `FAILED`. This proves integrity only (D1). | Not checked |
| **C. Value** | `pct` and `as_of` must equal quotes on their lines of the verified text. A substituted capture fails on the pin, the identity line or the values. | Quotes unchecked |
| **D. Time** | §7.11.1. Neither the window end nor the stamp is ever treated as the capture time. A window ending after E, or an E inside the window, fails D2. | No signal |
| **E. Failures** | • Missing reference: no link, and the record is unchanged.<br>• `FAILED`: missing manifest or artifact; malformed reference; hash mismatch; missing or malformed window; `pct` or `as_of` mismatch; duplicated or contradictory entries; untied value.<br>• Late capture: `NOT_AVAILABLE_BY_CUTOFF`.<br>• "Not quoted yet": MISSING, with `pct: null`. ₹0: ZERO and `SOURCE_UNQUALIFIED`.<br>• Duplicate JSON keys are rejected at the scoped evaluation-input and manifest boundaries; configuration and stored-record readers remain permissive (§7.12).<br>• A9 stays nonterminal in every case. | Every case is silently unlinked |
| **F. Reproducibility** | The input plus the pinned manifest and artifact re-derive the result. The A15 record keeps both digests, the window text and the D1 label. If the manifest is later amended, re-verification fails closed, and the pinned bytes stay in history. | Only an opaque pin is recorded |
| **G. Compatibility** | No schema or version change. Existing inputs and records are unchanged, with no reinterpretation. | — |

#### 7.11.4 Done in this pass under existing D1–D2 authority

- **D2 wording.** The `gmp_evidence.py` module and `capture_obtained_by` docstrings no longer call the window end "the capture time". They now state that it is the latest possible capture time, used only as an upper bound. Three focused tests were renamed to match. Behaviour is unchanged.
- **D1 identity.** `load_rendered_capture` now rejects an artifact id declared more than once, instead of taking the first. A new focused test covers it, and a mutation run without the guard fails that test.
- **Module docstring.** It no longer says that no field could link an evaluation; it now matches §7.1.
- **Review-time status, superseded by A18:** the linkage verifier and A15 mapping were not yet done when this review was written. The verifier and mapping are now implemented without a schema/version change; see §7.12.

#### 7.11.5 Historical question for Ramki (resolved by A18)

**Historical question:** Approve §7, as revised on 2026-10-16, as the GMP evidence-linkage contract (L1 as revised, L2-a, L3-a, L4-a), with no schema or version change?
- **Recommendation at that time:** yes.
- **Decision:** Ramki's direct 2026-10-16 task instruction identifies the contract as approved and directs its correction and verification. A18 records the approval as L1 as revised, L2-a, L3-a, and L4-a with no schema/version change. The implementation and current boundaries are recorded in §7.12.

### 7.12 Approval, implementation, and verification reconciliation (2026-10-16)

**Authority.** A18 is the durable decision record for the direct user approval of L1–L4. The historical recommendation in §7.10 and the review status in §7.11 are not the approval basis.

**Implementation.** Commit `e473f0090916cf6a125447be077316ea694b2675` on `arena/ea6e5bc2-ipo-screening-engine` corrects percentage-token binding and adds focused linkage regressions. The verifier now requires the quote to equal the one complete signed percentage token on its locator line; an omitted sign, substring of a larger number, or multiple percentage tokens fails closed. It parses the token sign before numeric comparison. A repeated `IPO GMP` title marker is rejected as ambiguous. Wrong/empty issuer identity and altered assembled A15 field values are also covered by focused tests. Existing failure diagnostics, replay context, and A9 behavior remain unchanged.

**Verification.** The pre-correction regression reproduced `-71.4%` / quote `71.4%` / input `71.4` as `VERIFIED`. After correction, the focused group and full suite passed on implementation commit `e473f0090916cf6a125447be077316ea694b2675` (128 and 885 passed respectively). They were rerun after documentation commit `99759bcad75db3b16451c90e3b74960e04219e11`:
- `.venv/bin/python -m pytest tests/test_gmp_evidence_linkage.py tests/test_strict_evaluation_json.py tests/test_d1_d3_gmp_source_policy.py -q` — **128 passed** in 9.86 seconds;
- `.venv/bin/python -m pytest tests/ -q` — **885 passed**, two Starlette deprecation warnings, 316.98 seconds;
- `PYTHONPATH=engine .venv/bin/python` calling `verify_frozen_core()` — **PASS** (six pinned files);
- `.venv/bin/python -m compileall -q engine tests` — **PASS**;
- `git show --check --oneline HEAD` and `git diff --check HEAD^ HEAD` — **PASS**.

**Latest verification (2026-10-16).** On implementation commit `ca6c9862c5809d72a73d1493ef5f6fe31ec7f34f`, `.venv/bin/python -m pytest tests/test_gmp_evidence_linkage.py tests/test_strict_evaluation_json.py tests/test_d1_d3_gmp_source_policy.py -q` exited **0** (**128 passed**, 9.64 seconds); `.venv/bin/python -m pytest tests/ -q` exited **0** (**885 passed**, 316.21 seconds, two Starlette deprecation warnings); compileall and `verify_frozen_core()` (6/6) passed; `git show --check` and `git diff --check` passed.

**Clean-baseline implementation-patch verification (after session docs commit `775f82bc7e0e6f58ae4c1cd7501f8b692950fec0`).** A temporary archive of authoritative baseline `805affe10ef387b649717facb31b0378f7b233d7` plus the exact eight-path implementation patch passed `git apply --check`, application, and byte comparison against `ca6c986`. With `PYTHONPATH=<temporary-tree>/engine`, the focused command exited **0** (**128 passed**, 10.12 seconds); the full command exited **0** (**885 passed**, two Starlette deprecation warnings, 321.24 seconds); compileall exited **0**; `verify_frozen_core()` passed all six pinned files; `verify_golden_result()` passed with hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`; `verify_v1_6_implementation()` passed with zero failures/warnings. This validates a temporary clean implementation patch, not a Git commit/branch. These are self-run checks, not independent verification. Current tracker/A18 edits are docs-only and no code changed after the run.

**Boundaries.** No frozen-core, scoring, A9, schema, or version change. The retrieval window remains an honest `UNKNOWN` fact, not an exact receipt time. Linkage and manifest write-once checks do not qualify a publisher. MarketLiveIPOGMP and InvestorGain remain **NOT QUALIFIED**; PapsDigital remains a **non-independent alternative**; R7 remains **UNRESOLVED**, R8 history remains open, and the documented new-observation condition for an R7 capture was not met. A9 remains fail-closed. The repository tracker has been reconciled on the session branch only and explicitly distinguishes that push from authoritative publication; the authoritative baseline tracker is unchanged.

**Publication.** Implementation code commit `ca6c9862c5809d72a73d1493ef5f6fe31ec7f34f` and the first docs-only tracker-reconciliation commit `4c6c01416d99b38191dd47aea5226f95feb3ee3e` were pushed and remotely verified on `arena/ea6e5bc2-ipo-screening-engine`; after the latter push, `git ls-remote` reported the session ref at `4c6c014`. The remote authoritative branch remains at `805affe10ef387b649717facb31b0378f7b233d7`. The session history includes proposal commits. No clean baseline-derived implementation/documentation refs, authoritative merge, or PR exist. This is not an assertion of authoritative publication; clean refs must be created through a workflow permitted to do so.
