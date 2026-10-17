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

### 6.3 D1–D3 implementation (2026-10-15 snapshot)

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

**Deliberately not changed in the D1–D3 implementation (2026-10-15):**
- the A9 gate and its messages;
- the input and A15 schemas;
- configuration, scoring formulas and weights;
- the frozen core, the A17 cutoff module and the pipeline;
- the golden result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.

No retrieval-time or hash field was added.

**Historical limitation (as of 2026-10-15; superseded by A18 in §7).** When D1–D3 were implemented, the v1.5 input and A15 implementation did not link an evaluation's `market.gmp` to a retained capture. A18 later approved a bounded link through existing v1.5 `_sources`/`_evidence` fields and the existing A15 raw-byte digest representation. The approved link requires no schema or version change. It does not create an A9 qualified path; A9 remains fail-closed.
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
  - A9 publisher qualification remains unresolved; the evidence link in §7 is not a qualification path;
  - R7, and R8's history before capture;
  - §8 PR-4f and PR-5.
- **D3 covers only the exact "Not quoted yet" and a displayed zero.** Other markers fail closed as malformed, for example InvestorGain's "₹ --" or PapsDigital's "N/A". Well-formed negative amounts keep their existing treatment as values (the input schema allows `pct` down to −1000). D3 does not address them, and no qualification follows.

## 7. GMP evidence linkage — A18-approved contract and status snapshot (2026-10-16)

This is the intended §7 reference used by `engine/ipo_screening/gmp_evidence.py`; §6 records D1–D3 and this section records the later linkage decision. The durable decision record is [`handoff/decisions/A18-gmp-evidence-linkage-contract.md`](../../handoff/decisions/A18-gmp-evidence-linkage-contract.md).

### 7.1 Approval and contract summary

**Status:** Ramki approved L1 as revised, L2-a, L3-a, and L4-a on 2026-10-16. The approval is recorded in A18. It permits the narrow linkage correction and regressions; it does not select or qualify a publisher.

The link uses existing v1.5 `_sources` and `_evidence` fields. It pins a single capture manifest, binds the evaluated issuer/title and GMP value/timestamp quotes, recomputes local SHA-256 digests for the manifest and artifact, and preserves a bracketing capture window honestly as an `UNKNOWN` retrieval fact. The complete signed percentage token must exactly match the quoted value; ambiguous or partial token matches fail closed. A link failure is a diagnostic, not a structural rejection or scoring change. No schema, version, or frozen-core change is authorized.

### 7.2 Duplicate-key handling and boundaries

Duplicate JSON keys are rejected at the scoped evaluation-input and pinned capture-manifest boundaries. Configuration and stored-evaluation readers retain their existing JSON behavior; this is not a global parser change.

`VERIFIED` establishes only a link between one evaluation and specified retained local rendered bytes/text. It does not establish publisher authenticity, source-native evidence, or a qualified GMP source. A9 remains fail-closed for Final.

### 7.3 Implementation and publication snapshot

The code/test source is `ca6c9862c5809d72a73d1493ef5f6fe31ec7f34f`, present unchanged in the eight scoped paths at session ref `bbe445a34196b93c98e9fa018888eb1536151f02`. The authoritative ref was `805affe10ef387b649717facb31b0378f7b233d7`. The session branch contains proposal history; no clean baseline-derived implementation/documentation ref or PR existed at this verification snapshot. The session branch must not be fast-forwarded to authoritative.

### 7.4 Qualification status

- MarketLiveIPOGMP: **NOT QUALIFIED**.
- InvestorGain: **NOT QUALIFIED**.
- PapsDigital: **non-independent alternative**.
- R7: **UNRESOLVED**; R8 history remains open.
- No R7 capture was taken because the documented new-observation condition was not met.
- No publisher is qualified by linkage. A9 remains fail-closed; missing GMP is `MISSING`, present GMP is `SOURCE_UNQUALIFIED`, and Final has no terminal `final_outcome`.

### 7.5 Verification evidence and post-publication update

Previously reported verification on a temporary baseline-plus-patch tree: focused tests **128 passed**; full suite **885 passed** with two Starlette deprecation warnings; compileall, frozen-core (6/6), golden-result, and v1.6 integrity checks passed. These results are not a substitute for rerunning checks on the Windows-created final implementation commit.

After Windows creates and remotely verifies the two clean refs, update the tracker in a documentation-only follow-up with the exact implementation/doc ref SHAs, ancestry, changed paths, and final test evidence. Do not record a publication claim before fetching and verifying the corresponding remote ref.
