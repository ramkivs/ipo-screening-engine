# Program Authority Decision Package — Phase 0, Candidate, and First Implementation Scope

> **Status: DOCUMENTATION-ONLY REQUEST DRAFT — NOT A PROGRAM AUTHORITY DECISION.** Prior PUB-1/TRK-1 did not cover this file. Ramki's 2026-10-13 instruction now authorizes publication of this exact path on the fixed session branch only. That publication authority creates no policy, implementation, acceptance, candidate-assembly, merge, release, or production-activation authority.

- **For:** Ramki / Program Authority
- **Prepared:** 2026-10-13 (Asia/Calcutta)
- **Starting commit:** `e044091a462129fbb67724ad93f76aedb9993322`
- **Fixed working branch:** `arena/573e69a4-ipo-screening-engine`
- **Related published evidence:** `handoff/investigation/IPO-SCREENING-ENGINE-RECONCILIATION-AUDIT-DRAFT-2026-10-13.md`; review-candidate tracker at `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`.

## 1. Decision requested — summary

The repository does not establish formal Phase 0 closure criteria, a canonical product candidate, or a named independent reviewer. A8-M remains open; Phase 1 remains unauthorized. The smallest shared contract prerequisite before A9/NIFTY code work is an owner-approved canonical evidence/output field map and serialization/versioning decision. There is also a verified placement blocker: the proposed P1 code/schema/test paths are absent from fixed session HEAD `e044091` and present on 01a, so a separately authorized candidate assembly is required before `P1-CANON-01` can run on this branch. A9 and NIFTY remain separate downstream workstreams, each requiring its own source/evidence contract and implementation grant.

**Recommendation for Ramki to accept, modify, or reject:**

1. Keep Phase 0 **OPEN** until its exit criteria below are approved and evidenced; do not close it based on this package, implementation tests, or work on a different branch.
2. Consider `arena/01a10b42-ipo-screening-engine` at `4b19faf848a721265597a678926988d484d30e59` as the **product-code review base**, not as an accepted/canonical release. Keep 4e as the current governance/evidence reference. Do not reconcile or merge the refs until specifically authorized.
3. Before implementation on the fixed session branch, separately authorize (or defer) an exact candidate-assembly plan that makes the selected product-code base available on that branch and records which 4e decisions control. Candidate assembly is not canonical selection, acceptance, merge to `main`, or release. It is currently not authorized.
4. Approve a semantic field map and serialization/versioning contract before downstream A9/NIFTY implementation.
5. Name an independent reviewer; none was located in the reviewed records.
6. After formal Phase 0 disposition, candidate assembly, and contract approval, separately authorize the bounded `P1-CANON-01` implementation. If Program Authority wants implementation to overlap with an OPEN Phase 0, it must explicitly authorize that exception and define its phase status. Neither candidate assembly nor implementation is authorized by this draft.

## 2. Verified facts from existing records

### Governance and policy

- **Phase 0 is OPEN; Phase 1 is UNAUTHORIZED.** The A8-M handoff and repository tracker state this explicitly; no contrary closure or implementation authorization was found in the reviewed A8/A9 records. The scoped search located no formal Phase 0 closure/freeze or independent acceptance record.
- **A1:** Ramki is the conflict-adjudication authority. The A1 record expressly says it is not a field-level adjudication and leaves unresolved the canonical contract for source observations and field-level resolution. Each actual disputed field requires its own attributable decision; no general precedence or majority-vote rule is authorized.
- **A7:** approved outcome rules remain unchanged: a verified applicable knockout takes precedence and yields `AVOID`; missing critical-safety evidence with no verified knockout yields `INSUFFICIENT_DATA`; `UNVERIFIED` is neither `TRIGGERED` nor `CLEAR`; result concerns (final outcome, per-rule state/evidence, critical-safety completeness/missing evidence, score interval/derived verdict, diagnostics) remain distinct. The concrete serialized result contract and the no-terminal label/serialization for one unverified-only case remain unresolved; do not reopen the settled rules.
- **A8-M:** NIFTY price-index/SMA semantics and required-NIFTY UNKNOWN-to-Final behavior are approved. Source-native qualification and the deterministic session/publication-availability prerequisite remain open; no provider bytes or current category are established, and the inspected application refs do not contain the SMA calculation or required-NIFTY Final gate. The existing NDAL request remains **UNSENT**.
- **A8-S/A10:** S2 is the preferred actual final published subscription record, conditionally. A10 authorizes interim evidence/display treatment only; it does not qualify a source, authorize scoring, or determine missing-subscription Final behavior.
- **A8-G/A9:** A9's policy is settled: an absent/invalid required qualifying GMP snapshot or required hash withholds `FINAL`. A9 does not choose a provider or define the source event, cutoff, hash scope/serialization, schema, or implementation. Implementation authority remains not granted.
- **A8-P/A5:** peer observation direction exists, but source/universe/cutoff/eligibility and calibration evidence/parameters remain blocked; A5 remains `CALIBRATION_EVIDENCE_INSUFFICIENT`.
- These are distinct states: a completed investigation is not a policy approval; an approved policy is not a source qualification; existing code/tests are not an implementation grant or independent acceptance.

### Canonical model evidence

On the 01a product ref, `engine/ipo_screening/canonical.py` currently gives `SourceRef` generic `source_id`, `source_type`, `uri`, `content_hash`, `retrieval_timestamp`, and `source_timestamp`; `Evidence` has an evidence id, source id, locator and one `as_of` value, among other fields. The supplemental `sourceRef` schema likewise has a closed set of generic fields. Those artifacts do not explicitly distinguish all A8-required values as separate contract elements: source-native event/session identity and occurrence, original timestamp and zone/offset, normalized UTC, publication/availability, retrieval, snapshot cutoff/evaluation timestamp, provider record/revision evidence, and the hash's byte/payload scope. Nor is a field-level A1 resolution record defined by the current model.

The immutable evaluation record stores frozen input/market/peer snapshots and hashes, but that does not by itself define the missing source-specific provenance or A7 serialized output contract. The v1.5 schema/version and historical record/hash invariants must not be changed by inference.

**Placement blocker for the proposed implementation:** at the reported fixed session HEAD `e044091`, none of the specific code, schema, or test paths enumerated for `P1-CANON-01` is present. Those paths do exist on 01a. Ratifying 01a as a review base does not make its files part of the fixed session branch. Therefore `P1-CANON-01` cannot be executed on this branch until Program Authority separately authorizes and a specific candidate assembly is completed on the fixed session branch. No such assembly or integration is authorized or performed here.

### Candidate refs and delivery evidence

| Ref | Current tip / ancestry | Evidence relevant to consideration | Material limitation |
|---|---|---|---|
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` | Common baseline. | Sparse; not the full application candidate. |
| PR #3, `arena/ipo-screening-engine-v1.5` | `49c994430148d327e0afff6d67f31072563d64cc`, 16 commits beyond main | Core v1.5, Phase 5, Track B 6A–6D, Phase 7 candidate/tests. PR is currently OPEN and CLEAN/mergeable. | No presentation API, lifecycle module, or frontend app; no reviews or status checks. CLEAN is not acceptance. |
| Product continuation, `arena/01a10b42-ipo-screening-engine` | `4b19faf848a721265597a678926988d484d30e59`, PR #3 plus 33 commits | Adds presentation/UI-1–UI-7, lifecycle/lineage, CFO/PAT and R.K. Fashion repairs, upload/security fixes, and later product work. This is the most complete inspected application tree. | Lacks the current 4e A8-M/A9/A10 records and A9 gate. Historical test reports are not independent acceptance. |
| Governance/evidence, `arena/4e1080b7-ipo-screening-engine` | `adbd93c5b4450fb113561368d7d101eb4686c842`, 12 commits beyond main | Current A8-M/A9/A10 decisions and source investigations; A9 gate exists in its `pipeline.py`. | Lacks the 01a presentation/UI and post-listing calibration implementation. It is not the full product candidate. |

01a and 4e diverge from the same main baseline; neither contains the other's post-main commits. The 4e tracker source remains unchanged at its recorded blob. The session-branch tracker is explicitly a review candidate, not the canonical delivery tracker.

## 3. Decision 1 — Phase 0 disposition and exit criteria

**Recommendation:** retain **Phase 0 OPEN** now. The project records identify unresolved dependencies but do not establish an approved, exhaustive closure checklist. Ramki must approve or amend the following proposed checklist and decide which open source contracts are Phase 0 exit blockers versus explicitly deferred, fail-closed items:

1. Record the Phase 0 scope, governing v1.5 baseline, and which policy/evidence refs control; do not merge refs by inference.
2. Approve the semantic canonical evidence and evaluation-result field map and serialization/schema-version approach (Decision 4 below). If Ramki elects to defer this shared contract, record that Phase 0 is not closed for the A9/NIFTY downstream stage and no such implementation may proceed.
3. Resolve A1/A7 contract requirements, or explicitly record what remains open and how it remains non-screenable/non-final; do not invent a terminal label or field-level adjudication.
4. For each A8 area in scope, either approve its source/event/cutoff/missing-input contract or explicitly defer it with its non-screenable/fail-closed consequence. A9's settled GMP rule remains narrow; NIFTY's source evidence remains unqualified; A10 does not decide subscription Final consequences; A5 remains blocked.
5. Identify required source/data evidence and record its provenance/availability limits. Do not treat rendered NIFTY captures or synthetic Track B datasets as source-native/real-world acceptance. Explicitly disposition whether D1/D2/D3 and GCP sign-off are Phase 0 blockers or separately deferred decisions.
6. Have Program Authority record completion of these decision/evidence criteria. Name an independent reviewer for later implementation acceptance as a separate decision; the same person may review Phase 0 evidence only if explicitly tasked.
7. Close Phase 0 only when the approved Phase 0 checklist is evidenced and Ramki records closure. Phase 0 closure does not itself grant Phase 1 implementation authority, establish independent acceptance, or authorize branch integration, merge, release, or production activation. Recommended sequence: close the Phase 0 decision/contract checklist, then separately authorize Phase 1. If work is to overlap, Program Authority must explicitly grant and classify that exception.

**Decision needed:** approve/modify this exit checklist and explicitly state whether unresolved A8 source contracts can be carried as blocked/deferred while keeping required inputs non-screenable and Final fail-closed. Until then, Phase 0 stays OPEN.

## 4. Decision 2 — product candidate to consider

**Recommendation, not a branch selection:** use 01a `4b19faf` as the application-code base to **consider for a future authorized review candidate**, because it is a descendant of PR #3 and contains the later UI, lifecycle, and repair work. Do not call it canonical or accepted. Use 4e `adbd93c` as the current governance/evidence reference for the A8/A9/A10 decisions, not as the application base. PR #3 is an incomplete fallback for the broader current product because it lacks later UI/lifecycle work. No ref alone is presently an acceptable integrated candidate.

**Decision needed:** Ramki must ratify 01a as the review base or name another base; identify which 4e policy/evidence records control; and separately authorize or defer a specific candidate-assembly plan on the fixed session branch. If authorized, the record must name source ref(s), exact target candidate/tree, and whether controlling 4e decisions are copied into the candidate or pinned by immutable refs. If not authorized, `P1-CANON-01` remains blocked on this branch. None of these choices makes the candidate canonical, accepted, merged to `main`, or releasable. This package performs no branch integration, cherry-pick, merge, or release.

## 5. Decision 3 — independent reviewer and acceptance

No independent reviewer is named in the inspected records. Ramki must name a reviewer who did not implement the changes under review and specify the review scope. The reviewer must independently inspect the exact candidate commit/tree and:

- verify the approved scope against the diff and decision records;
- review the field map/schema/serialization against A1, A7, and A8 without inferring provider qualification or unresolved policy;
- for later A9/NIFTY work, execute the authorized focused and regression tests on that exact tree and inspect fail-closed/provenance behavior, rather than rely on branch-reported counts;
- confirm no unauthorized scoring/config/fixture changes, no generic hash acceptance, no NIFTY/VIX coupling, and no weakening of unknown/conflict behavior;
- explicitly state which platforms and evidence they actually verified. No Windows verification may be claimed unless they run and record it.

Independent acceptance is not Phase 0 closure by itself, and neither is an implementation test pass. Release/activation still requires separate authority.

## 6. Decision 4 — canonical field map and first bounded implementation request

**Answer to the contract question:** **Yes.** An explicit semantic field map and serialization/versioning decision are prerequisites before A9/NIFTY downstream integration. This follows from A1's unresolved schema/evidence dependency, A7's unresolved concrete output representation, A8's separate timestamp/provenance safeguards, and A9's explicitly undefined hash/snapshot representation. This does **not** authorize changing the current schema, and this package does not invent property names or a schema version.

### Proposed semantic field map for approval

The owner should approve or amend the required meanings before anyone chooses property names:

- source/provider identity and stable source-native record reference;
- actual event/observation/session identity and evidence that it occurred;
- original source timestamp with original timezone/UTC offset, kept separate from normalized UTC;
- publication/availability, retrieval, evaluation cutoff, and evaluation timestamp as separate concepts;
- hash algorithm and byte scope (provider-original bytes versus local/rendered capture versus normalized/canonical payload); no equivalence by label;
- revision/correction identity and source-defined precedence evidence;
- source observation/evidence links to canonical fields and, only for an actual conflict, a separate attributable A1 record containing the affected field, competing observations and provenance, rationale, Ramki's decision, authorization evidence, and decision date; preserve original observations and keep the disputed field non-screenable until adjudicated and validated;
- distinct value state and evidence/verification state;
- A7 evaluation output keeping final outcome, each rule's knockout state and supporting evidence, critical-safety evidence completeness and references to missing evidence, score interval and score-derived verdict, and diagnostics separate; Ramki must decide the unverified-only terminal outcome or explicitly approve how a no-terminal result is serialized. Until then, do not invent a label or implement that case.

### `P1-CANON-01` — proposed first implementation authorization

**Request:** after Ramki records the Phase 0 disposition (recommended: close the decision/contract checklist), approves the field map and schema/versioning choice, authorizes and completes candidate assembly on the fixed session branch, names the independent reviewer, and separately grants Phase 1 authority, authorize only implementation of the shared canonical provenance/result representation needed by downstream gates. If Program Authority elects to run this before Phase 0 closure, that overlap must be a separately recorded phase exception; do not infer one.

- **Candidate touchpoints, not authorized by this draft:** `engine/ipo_screening/canonical.py`; `engine/ipo_screening/canonical_input.py`; `engine/ipo_screening/enrichment_contract.py`; `engine/ipo_screening/snapshots.py`; and `engine/ipo_screening/evaluation.py` only for approved immutable snapshot/result serialization. The schema path/version must be explicitly named in the authority decision; possible current surfaces are `schema/supplemental-enrichment.v1.schema.json` and `schema/ipo-input.v1.5.schema.json`. Do not edit either existing version in place by inference; Ramki must explicitly choose an in-place change or name the successor schema path(s). Permit only `tests/test_enrichment_contract.py`, `tests/test_evaluation_lifecycle.py`, and one new `tests/test_canonical_provenance_contract.py`, limited to this contract. If implementation requires any other module/schema/test file, stop and request amended authority.
- **Deliverables:** (1) approved provenance/value-state and attributable A1 field-resolution representations carried through canonical parsing/validation; (2) the explicitly selected schema version and serializers for the approved source/evidence and immutable snapshot/result fields; (3) focused tests in the permitted test paths demonstrating round-trip, strict validation, conflict/missing-state preservation, and historical compatibility; (4) test-run evidence and an exact changed-file/schema-version summary for the independent reviewer. No provider acquisition or downstream gate behavior is a deliverable.
- **Dependencies:** approved semantic field map; a decision for A7's unverified-only terminal case (either its terminal outcome or an explicitly approved no-terminal serialization); explicit schema path/version and backward-compatibility decision; formal Phase 0 disposition (recommended closure of the decision/contract checklist first); authorized candidate assembly completed on the fixed session branch with an exact target tree; separate Phase 1 implementation authority for the exact files; named independent reviewer. Any overlap with an OPEN Phase 0 requires an explicit exception.
- **Acceptance criteria:** strict round-trip/schema validation; all approved times and hash scope remain distinct; missing/unqualified/conflicting observations stay UNKNOWN/UNVERIFIED and do not become screenable; original observations are retained; field adjudication is attributable and separate; immutable historical records are not rewritten; existing v1.5 scoring/config/golden behavior remains unchanged; A7 fields are serialized only as approved and no terminal state is invented; the exact changed-file list stays within the authorized paths.
- **Explicit exclusions:** candidate assembly/branch integration (a prior, separate gate); provider adapters or source acquisition; computing or certifying provider/source hashes (this package only serializes/validates the approved hash-scope metadata); A9 gate; NIFTY calculator/gate; scoring/knockout/config/weight changes; fixture or historical-data migration; UI, database, infrastructure, merge to `main`, release, or production activation.

**Decision needed:** approve/modify the field map and versioning approach; grant or deny `P1-CANON-01` as a separate bounded implementation authorization. Until the map/version decision and implementation grant are explicit, make no code/schema/test changes.

## 7. Subsequent A9 and NIFTY workstreams — independent after shared prerequisites

| Workstream | Already settled | Still required before its own implementation | Separate acceptance boundary |
|---|---|---|---|
| **A9 GMP gate** | A9 fail-closed policy: a missing/invalid required qualifying GMP snapshot or required hash withholds Final. The policy is not reopened here. Partial gate exists only on 4e. | Approved provider/source and actual observation/event/as-of semantics; cutoff/publication/retrieval evidence; explicit hash scope and snapshot serialization; candidate chosen; separate implementation authority. | Gate on the selected tree blocks Final for the A9 condition; blocked marker or generic payload hash does not qualify; GMP-only scope; Preliminary and subscription behavior unchanged; focused missing/invalid-hash and valid-source-contract tests. |
| **NIFTY trend** | NIFTY 50 price-index SMA-50/200 classification, session-based window semantics, and required-NIFTY UNKNOWN-to-Final rule are approved. | Source-native authoritative closes for a complete expected 200-session series; source identity/revision evidence; publication availability by explicit cutoff; supported session/special-session calendar rule with no invented delay; candidate chosen; separate implementation authority. The NDAL request remains UNSENT. | Strict above/below/mixed/equal behavior; incomplete, invalid, stale, unqualified or unresolved-conflict inputs yield UNKNOWN with reason; required UNKNOWN blocks Final; source/cutoff provenance preserved; no VIX/listing-gain blend or score-map change. |

**Sequencing decision:** after `P1-CANON-01` is independently accepted on the authorized session candidate, A9 and NIFTY may proceed **in parallel**, each only after its own source/evidence contract and explicit scoped authorization. Neither approval is implied by the shared contract or its acceptance. A8-S, GMP source qualification beyond A9's narrow gate, A8-P/A5, VIX, listing-gain, anchor, and any other market-metric work remain separate evidence/policy/implementation decisions; they are not silently included in either workstream. Keep VIX distinct from NIFTY.

## 8. Exact Program Authority response requested

Please record each item separately; no response is presumed:

1. **Phase 0:** `KEEP OPEN` / `APPROVE OR AMEND the proposed exit checklist` / `OTHER DISPOSITION: ____`.
2. **Product review base:** `RATIFY 01a @ 4b19faf AS THE REVIEW BASE ONLY` / `NAME ANOTHER REF: ____`. This is not canonical selection, acceptance, or release authority.
3. **Candidate assembly on the fixed session branch:** `AUTHORIZE A SEPARATE, BOUNDED ASSEMBLY PLAN` / `DEFER`. If authorized, identify the source ref(s), exact target tree, how 4e decisions are controlling (copied or pinned), and independent review required: `____`. This is not a merge to `main` or release; without it, `P1-CANON-01` cannot run on the current branch.
4. **Independent reviewer:** `NAME: ____; role/independence basis: ____; acceptance scope: ____`.
5. **Canonical contract:** `APPROVE / AMEND / REJECT` the semantic field map above; decide schema path/versioning and the unresolved A7 terminal case without inventing provider contracts.
6. **First implementation grant:** only after the Phase 0 disposition, approved contract, completed candidate assembly, and reviewer assignment, `AUTHORIZE / DO NOT AUTHORIZE P1-CANON-01`; any Phase 0/Phase 1 overlap must be explicitly classified as an exception. If authorized, identify any allowed scope change: `____`.
7. **Later work:** confirm that A9, NIFTY, and other A8 metrics require their own source/evidence contracts and scoped implementation approvals after shared prerequisites: `YES / AMEND: ____`.
8. **Release boundary:** confirm Phase 0 disposition, Phase 1 implementation grant, independent acceptance, merge/release, and production activation are separate gates and none implies another: `YES / AMEND: ____`.

## 9. Publication and execution boundary

The prior PUB-1/TRK-1 approval was limited to the audit, tracker-delta proposal, and tracker copy-forward candidate on the session branch; GOV-001 establishes decision-record location/format, not general publication authority. Ramki's 2026-10-13 instruction separately authorizes documentation-only publication of this exact file on the fixed session branch. This does not authorize publication of other untracked files or any substantive decision. No application/schema/configuration/fixture/test changes, candidate assembly/branch integration, NDAL contact, merge, release, or activation are authorized by this package.
