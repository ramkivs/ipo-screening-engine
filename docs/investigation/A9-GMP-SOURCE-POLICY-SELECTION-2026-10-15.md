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

- **Focused tests:** `tests/test_d1_d3_gmp_source_policy.py` (84 tests). Coverage:
  - the publisher-reported label;
  - hash verification of the declared retained file, including altered, missing and misdeclared copies;
  - capture at, inside and after the cutoff, and IST offsets;
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

## 7. Proposal — minimum GMP evidence linkage (2026-10-16)

- **Status:** PROPOSAL — NOT APPROVED. This is Arena analysis for Ramki's decisions L1–L4 (§7.10). Nothing in this section is implemented, and A9 stays fail-closed.
- **Baseline:** D1–D3 implementation `805affe` on `arena/5ccbfd5d-ipo-screening-engine`; the authoritative `arena/573e69a4-ipo-screening-engine` is at `9dba813`.

### 7.1 The gap, and a correction to §6.3

`gmp_evidence.py` can verify a retained capture: D1 integrity, D2 capture time and D3 displayed state. No approved contract says how an evaluation's `market.gmp` value identifies the capture, its digest, its capture time or the displayed text it was transcribed from.

The v1.5 input already has generic fields that can carry such a reference:
- `market.gmp.source_id` → a `_sources[]` entry with `uri`, `content_hash` and `retrieval_timestamp`;
- `_evidence[<field path>]` entries with `locator` and `quote` (alias `quoted_text`).

A probe on 2026-10-16 added the §7.2 reference for ML-T to the golden input, validated it against the unchanged v1.5 schema, and ran it in Final mode:
- The input validated with no findings.
- A15 kept the `uri`, the capture time as `LOCAL_RETRIEVED_AT` (KNOWN) and the line locators. The quotes stayed in `evidence.json`.
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
| `_sources[S].content_hash` | `sha256:` followed by the artifact file's 64-hex digest. This pins the exact file. |
| `_sources[S].retrieval_timestamp` | the manifest's `retrievalWindowUtc.notAfter` |
| `_evidence["market.gmp.pct"]` | `source_id` `S`; `locator` `line <n>` of the artifact; `quote` = the exact displayed percentage on that line; `extraction_method` `MANUAL_ENTRY` |
| `_evidence["market.gmp.as_of"]` | `source_id` `S`; `locator` `line <n>`; `quote` = the publisher stamp that `as_of` was transcribed from |

Worked example (ML-T):

```json
"market": {"gmp": {"as_of": "2026-10-15T16:02:00+05:30", "pct": 71.4, "trend": null, "source_id": "SRC-MLGMP-TONBO-T"}},
"_sources": [{"source_id": "SRC-MLGMP-TONBO-T", "source_type": "MARKET_DATA",
  "uri": "evidence/gmp-observations/marketliveipogmp-tonbo-20261015/capture-manifest.json#ml-tonbo-chunk-0",
  "content_hash": "sha256:33516f86ebb2cc7e53ad0491ffad05bae1ca7115c6008ecfb7f41a9c6c79705d",
  "retrieval_timestamp": "2026-10-15T13:17:58.770Z"}],
"_evidence": {
  "market.gmp.pct": {"source_id": "SRC-MLGMP-TONBO-T", "locator": "line 7", "quote": "+71.4%", "extraction_method": "MANUAL_ENTRY"},
  "market.gmp.as_of": {"source_id": "SRC-MLGMP-TONBO-T", "locator": "line 84", "quote": "4:02 pm IST on Thu, 15 Oct, 2026", "extraction_method": "MANUAL_ENTRY"}}
```

Notes on the example:
- ML-T line 7 is `₹500+71.4%`. Line 84 gives the stamp with its year and zone; lines 11 and 13 split `15 Oct, 4:02 pm` from `IST`.
- A ₹0 reading quotes `0.0%` with `pct: 0`. "Not quoted yet" is quoted with `pct: null`.
- A publisher trend label would need a third entry, `_evidence["market.gmp.trend"]`. MarketLiveIPOGMP publishes none.

### 7.3 Minimum evaluation-record linkage (A15 1.1.0)

The existing mapping already gives:
- the source `S` with `uri` and `LOCAL_RETRIEVED_AT`;
- the evidence objects with `locator`, and `artifact_ref` pointing to the preserved `evidence.json` entry that holds the quote.

The proposal adds only two things, and only when a link is attempted:
1. **For a verified link, a digest on `S`** (`digest_refs`): `algorithm` `SHA-256`; `digest_value` recomputed from the file, in lowercase hex; `subject_kind` `RAW_ARTIFACT_BYTES` (L2-a); `subject_ref` = the repository-relative artifact path; `origin` `LOCAL_COMPUTED`; `evidence_refs` = the two evidence objects. It replaces the `LEGACY_UNRESOLVED` mapping of that `content_hash`. That amends the A15 package rule §1.3 for this case only.
2. **One diagnostic.** The code is free text (for example `A9_GMP_EVIDENCE_LINK`). It records the result (`VERIFIED`, `NOT_AVAILABLE_BY_CUTOFF` or `FAILED: <reason>`), the D1 label verbatim and the D3 state.

`outcome_resolution` is unchanged: `SOURCE_UNQUALIFIED`, or `MISSING`, and no `final_outcome`.

### 7.4 Verification

All of the following must pass; otherwise the result is `FAILED`.

1. **Location:** `uri` names a manifest inside `evidence/gmp-observations/` (no absolute path, `..` or URL) and an artifact that manifest declares.
2. **D1:** `load_rendered_capture` accepts the manifest and recomputes the file's SHA-256 and byte count. This establishes integrity only.
3. **Pin:** `content_hash` equals the recomputed digest, so a substituted file, or a manifest edited to declare one, fails.
4. **Capture time:** taken from the manifest's window end, never from the publisher stamp. `retrieval_timestamp` must be the same instant. Then D2 applies: `capture_obtained_by(capture, evaluation timestamp)`.
5. **Value:** the `pct` quote occurs on its `locator` line of the verified text. `classify_displayed_gmp(quote, unit="%")` must give ZERO or AMOUNT equal to `pct`, or MISSING with `pct: null`. MALFORMED fails.
6. **Stamp:** the `as_of` quote occurs on its line and equals `as_of` rendered in the publisher's stamp format (L3). `as_of` must not be later than the capture time.
7. **A17:** the existing rules then apply to `as_of` unchanged: cutoff, 24 h maximum age, and publisher labels only.

**Trust limit:**
- The window is the sandbox clock read before and after the tool call, checked against GitHub's `Date` header. The manifest itself says the window "does not establish when the publisher generated the content or whether the tool served cached content".
- The pin covers the artifact, not the manifest. The window's integrity rests on the repository history of the manifest.

### 7.5 Behaviour

| Case | Link result | A9 | Scoring |
|---|---|---|---|
| **Absent:** `S` has no evidence-manifest `uri`; this covers every current input | none, and no diagnostic | unchanged | unchanged (A17) |
| **Malformed:** bad `uri`; pin not `sha256:` plus 64 hex; missing or offset-less `retrieval_timestamp`; missing `_evidence` entry | `FAILED: <reason>` | `SOURCE_UNQUALIFIED` / `MISSING` | unchanged |
| **Mismatched:**<br>• pin, manifest and file digests differ, or the file is missing;<br>• `retrieval_timestamp` ≠ window end;<br>• a quote is not on its line;<br>• the value ≠ `pct`, or the stamp ≠ `as_of`;<br>• `as_of` is after the capture;<br>• the manifest is not a rendered capture. | `FAILED: <reason>` | same | unchanged |
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
- **Code (only after approval):**
  - a linkage verifier in `gmp_evidence.py` that reuses the D1–D3 functions;
  - the §7.3 digest and diagnostic in the A15 builder;
  - no change to the A9 gate's outcome logic.

### 7.8 Tests required

- **Substitution:**
  - swapped artifact bytes;
  - a manifest digest edited to match them;
  - another artifact id in the same manifest;
  - another IPO's capture;
  - a later recapture used for an earlier evaluation.
- **Stale evidence:**
  - `as_of` older than 24 h at evaluation;
  - window end after the evaluation;
  - evaluation inside the window;
  - an offset-less window or retrieval time;
  - retrieval time ≠ window end.
- **Missing evidence:**
  - no `S`;
  - an `S` without an evidence-manifest `uri` (record unchanged);
  - a missing manifest or artifact;
  - a missing `pct` or `as_of` evidence entry.
- **Mismatched value or artifact:**
  - a quote on another line;
  - a quoted value ≠ `pct`;
  - a rupee quote for `pct`;
  - "Not quoted yet" with a non-null `pct`;
  - `0.0%` must give ZERO and `SOURCE_UNQUALIFIED`;
  - a stamp ≠ the rendered `as_of`;
  - `as_of` after the capture.
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

### 7.10 Decisions requested (none approved)

| Decision | (a) | (b) |
|---|---|---|
| **L1:** input convention | Adopt §7.2 over existing v1.5 fields | Not adopted |
| **L2:** A15 digest subject | `RAW_ARTIFACT_BYTES` in A15's raw-byte sense, with the D1 label in the diagnostic; no schema change | A dedicated subject kind; A15 1.2.0 |
| **L3:** stamp binding | Check `as_of` against the quoted stamp in the publisher's format: MarketLiveIPOGMP `h:mm am/pm IST on Ddd, D Mon, YYYY`, ML-T line 84 | Require only `as_of` ≤ capture time. A mistranscribed later stamp could then make stale evidence look fresh. |
| **L4:** failure handling | Record failures as nonterminal diagnostics | Reject structurally malformed references before scoring |

**Recommendation:** L1, L2-a, L3-a and L4-a, which need no schema or version change. Then implement the verifier and the A15 mapping with the §7.8 tests. A9 stays fail-closed throughout.
