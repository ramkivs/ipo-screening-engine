# IPO Screening Engine — Reconciliation Audit & Decision Packages

> **Status: WORKING DRAFT — NON-AUTHORITATIVE; DOCUMENTATION-ONLY PUBLICATION AUTHORIZED.** This is an audit and a set of proposed decision inputs, not a policy approval, implementation specification, independent acceptance, canonical tracker, or release record. Ramki explicitly authorized this audit and the tracker-delta proposal for additive publication on the fixed session branch, and separately authorized a tracker copy-forward candidate pending review. No engine code, schema, configuration, fixtures, or tests are changed. The source tracker on 4e remains untouched.

- **Audit date:** 2026-10-13 (UTC)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Session branch / baseline:** `arena/573e69a4-ipo-screening-engine` at `01ba66c12ca1195fd7acbd287c3e39a019808094`
- **Scope:** Reconcile the requested A8/A5, Phase 0/1, Track B, UI/Phase 5, product-repair, integration, acceptance, release, and deferred-roadmap items against currently fetched repository refs and GitHub PR state.

## 1. Direct answers

### Is local NIFTY trend work the only outstanding implementation?

**No.** NIFTY calculation and the required-NIFTY Final gate are absent from the inspected application lines, but they are not the only code/integration gaps:

1. The approved **A9 GMP fail-closed rule** has partial runtime implementation on `arena/4e1080b7-ipo-screening-engine`; it is absent from both PR #3's head and the later full-product branch `arena/01a10b42-ipo-screening-engine`. The source-specific GMP/hash contract and A9 implementation authority remain open. The inspected A9 tests do not specifically cover missing/invalid source-hash qualification.
2. The reviewed canonical source/evidence model is generic and does not explicitly model all approved A8 distinctions (source-native event/session time and original zone/offset, publication/availability, retrieval, cutoff/evaluation time, revision evidence, and field-level adjudication). A contract/schema change may be needed, but Phase 0 is open and Phase 1 is unauthorized; do not change it now.
3. There is no single delivery ref containing both the later application work and the current A8/A9/A10 governance records. The application, policy/evidence, and PR refs are materially divergent. Branch reconciliation is a delivery prerequisite, not authorization to merge or cherry-pick.
4. Source-specific subscription, GMP, market, and peer adapters cannot be finalized responsibly until actual sources, event semantics, cutoffs, and evidence contracts are established. These are currently evidence/policy blockers, not permission to invent a provider or build a speculative connector.

So the answer is **more than NIFTY**, but this audit does **not** authorize any of those implementation changes. It distinguishes absent code from evidence, policy, acceptance, and release gates below.

### What is complete, and what remains open?

- **A8-M policy semantics are approved**, including price-index SMA classification and the required-NIFTY `UNKNOWN` → non-final/withhold-Final consequence. **A8-M itself remains OPEN** because source-native qualification and the deterministic session/publication-availability prerequisite are unmet. No category was assigned in this audit.
- **A9 policy is settled** for its narrow case: a required qualifying GMP snapshot or required hash that is absent or invalid blocks `FINAL`. Do not reopen or extend that rule to subscription.
- **A10 interim subscription handling is approved** for evidence/display only. It grants neither source qualification nor scoring eligibility and does not decide subscription-related `FINAL` consequences.
- **Phase 0 remains OPEN; Phase 1 remains UNAUTHORIZED.** No located record formally closes/freezes Phase 0 or provides independent acceptance of a unified delivery candidate.
- **PR #3 remains OPEN.** Its GitHub state is CLEAN/mergeable, but it has no review decision, reviews, or status checks. CLEAN is not acceptance.
- **No merge, release, or production activation is authorized.** No Windows filesystem evidence was inspected or verified.

## 2. Method and limits

Read-only inspection was performed on fetched Git refs, selected tracked reports/models/tests, and GitHub PR/status APIs. The repository was unshallowed before ancestry comparisons. This audit did **not** repeat SMA calculations, redo the A8-M source-locator investigation, contact a provider, send the NDAL request, subscribe, buy data, or incur a charge. The existing A8-M report's historical evidence and cross-check conclusions are reused, not re-created.

The reported historical test totals below are transcribed from branch documentation and commit records; they are **not tests run for this audit** and are not independent acceptance. No Windows/PowerShell environment was accessed. No external web research was performed.

## 3. Verified branch, PR, and worktree state

### Repository refs

| Ref | Tip | Commits ahead of `main` | What the inspected ref represents |
|---|---|---:|---|
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` | 0 | Sparse baseline; not the later delivery candidate. |
| `arena/ipo-screening-engine-v1.5` (PR #3 head) | `49c994430148d327e0afff6d67f31072563d64cc` | 16 | v1.5, Phase 5E–5J, Track B 6A–6D, and Phase 7 candidate line. No presentation API, lifecycle module, or frontend app. |
| `arena/01a10b42-ipo-screening-engine` | `4b19faf848a721265597a678926988d484d30e59` | 49 | Later product/evidence line: includes PR #3 history plus 33 further commits, including presentation/UI, lifecycle, and later repairs. It lacks the A9 decision/implementation and current A8-M approval records found on 4e. |
| `arena/4e1080b7-ipo-screening-engine` | `adbd93c5b4450fb113561368d7d101eb4686c842` | 12 | Current governance/evidence line: A8-M/A9/A10 records, source investigation, and an A9 pipeline gate; it lacks the later presentation app and post-listing calibration module. |

`01a` and `4e` share `main` as their merge base and diverged; neither contains the other's post-main history. `01a` is 33 commits ahead of PR #3, while 4e has 12 commits on a separate line. The three refs must not be described as one accepted release. In particular, the tracker on 4e labels that branch “Delivery branch,” although its tree lacks substantial later application functionality; the tracker should distinguish the governance/evidence ref from the product-code ref and the PR candidate after publication is authorized.

### Pull request and checks

- [PR #3](https://github.com/ramkivs/ipo-screening-engine/pull/3), **“IPO Screening Engine v1.5,”** is OPEN from `arena/ipo-screening-engine-v1.5` (`49c9944`) to `main` (`01ba66c`).
- GitHub reports `mergeStateStatus: CLEAN`; `reviewDecision` is empty; review list and status-check rollup are empty.
- The head commit's status is `pending` with **0 statuses and 0 check runs**. No PR comments/reviews or completed checks were found in the queried state.
- `CLEAN` only describes current mergeability; it is not a review, test pass, independent acceptance, merge authorization, or release approval.
- PR #3 is not the 01a application line and does not include the current 4e A8/A9/A10 decisions. No merge or PR mutation was made.

### Session checkout

The working branch remains `arena/573e69a4-ipo-screening-engine` at the baseline above; before the authorized publication it had no remote branch/upstream. Publication is confined to this fixed session branch. No branch switch or PR change was made; the product delivery branch has not been selected.

## 4. Reconciled workstream status

Statuses below separate policy approval from implementation, evidence, acceptance, and release. “Implemented” refers only to code/docs found on the named branch; it is not a project-wide acceptance claim.

| Workstream | Status | Verified position and remaining gate |
|---|---|---|
| **A8-M — NIFTY meaning/classification** | **CLOSED — policy decision verified; A8-M remains OPEN** | The 2026-10-13 decision defines `market.regime.nifty_trend` as a completed-session-close-derived NIFTY 50 **price-index** trend. Strictly above both SMA-50/200 is `supportive`; strictly below both is `weak`; other valid mixed/equal cases are `neutral`; incomplete/invalid/unqualified/conflicting required inputs are `UNKNOWN`. This is classification policy, not score-map or implementation approval. Do not reopen it. |
| **A8-M — existing local history and source qualification** | **BLOCKED — evidence required** | Existing package documents 245 closes through 2026-10-08 and descriptive SMA calculations. The latest targeted 2026-10-09/12 source cross-check was not appended to that series and was not used for a recalculation. Original provider response bytes, record-level publication/availability and receipt evidence, stable provider record IDs, and revision precedence are not established. Existing local/rendered artifacts remain descriptive, not qualified for `FINAL`; no category was assigned. |
| **A8-M — calendar, availability, and runtime gate** | **BLOCKED — evidence required; implementation authority not granted** | Session-date support does not establish when a close became available. No numeric publication-delay allowance is approved; generic `market_staleness_hours: 24` is not the NIFTY freshness rule. Required NIFTY `UNKNOWN` blocks `FINAL` only when that input is required. The code path does not calculate the approved SMA trend or implement this NIFTY-specific gate. A8-M is OPEN; Phase 0 is OPEN; Phase 1 is UNAUTHORIZED. |
| **A8-S — subscription** | **PARTIALLY IMPLEMENTED — generic connector; A10 runtime handling unverified** | A8 approves S2 (actual final published record) subject to a source identifying the event and source-native as-of time. A generic official NSE/BSE subscription adapter exists on the product line, but no evidence was found that it implements A10's later interim handling. A10 approves preserving NSE, BSE, and separately identified All Exchange observations for evidence/display only; no averaging/substitution or scoring. Source, event, fields/units/denominator, timestamps/cutoff, freshness, scoring eligibility, and missing/unavailable `FINAL` consequence remain unresolved. The VNL discrepancy remains **CLOSED WITH LIMITATION**, not source qualification. |
| **A8-G / A9 — GMP** | **Policy CLOSED for A9; implementation PARTIAL on 4e only** | A9's narrow fail-closed rule is approved and must not be reopened: absent/invalid required qualifying GMP snapshot or required hash withholds `FINAL`; a blocked-input marker is not a qualifying snapshot/hash. It does not select a provider or define event/cutoff/hash serialization. A9 is implemented only on 4e; its relevant inspected tests do not specifically exercise missing/invalid source-hash qualification. The A9 policy/implementation is absent from PR #3 and 01a. Generic payload hashing is not an approved source contract. |
| **A8-P / A5 — peers** | **BLOCKED — evidence and policy decision required** | Approved direction prefers actual quote/valuation observations for a named session and separation of raw observations/universe from later eligibility. No peer provider, session/cutoff, reproducible point-in-time universe, or eligibility contract is approved. A5 remains `CALIBRATION_EVIDENCE_INSUFFICIENT`; do not use legacy 30-day freshness or 3-year listing-history defaults or claim production peer scoring. |
| **Phase 0, A1/A7, canonical evidence/output contracts** | **PARTIALLY IMPLEMENTED; Phase 0 OPEN** | A1 designates Ramki as field-conflict authority, but is not a field-level adjudication; each disputed field needs its own durable decision. A7 approves outcome precedence and separation of final outcome/diagnostics but leaves a terminal outcome case and the concrete serialized contract unresolved. The reviewed `SourceRef`/`Evidence` and supplemental schema contain generic source/hash/retrieval/source/as-of fields; they do not explicitly encode every approved A8 timestamp distinction and A1 resolution record. No Phase 0 freeze/closure or independent acceptance record was located. No schema change is authorized. |
| **Phase 1** | **NOT AUTHORIZED** | No Phase 1 implementation authority was located. Approved semantics, completed investigations, tests, or code on another branch do not grant authority for new schema, provider, scoring, fixture, configuration, or runtime changes. |
| **Track B — Phases 6A–6D** | **IMPLEMENTED — acceptance pending** | Post-listing observations/returns, storage/dataset, analytics, and calibration proposal code/tests exist on PR #3 and 01a; not on main or 4e. The Oct 6 readiness/traceability documents are stale as “future implementation” descriptions. Their test counts are historical branch reports, not independent acceptance. D1's requested scope disposition is not present as a separate decision record; do not infer a new authorization from implementation having occurred. |
| **Track B — D1/D2/D3 governance** | **RECHECK REQUIRED / policy open** | D1 asks for Phase 6A–6D scope authorization; no separate D1 decision record was located. D2's old “UI/Phase 5 parallel or sequential?” question is stale because those workstreams have since been delivered; completion does not prove the requested priority decision. D3's requested future promotion policy is not established by a separate decision record; do not adopt its proposed `N ≥ 15`, positive-IC, downside-firewall, or other figures as general policy. |
| **Phase 7 / v1.6 candidate** | **IMPLEMENTED — acceptance pending; inactive** | PR #3 contains a specific Phase 7 candidate and an approval assertion in `calibration-proposal.v1.6.0.json` / the Ramki-authored Phase 7 commit. The candidate is recorded inactive and its proposal is for controlled verification, not production activation. Product documentation identifies the 120-row calibration material as synthetic/simulated. This audit neither revokes nor extends the specific published candidate approval; it does not treat it as real-world independent validation, a general D3 threshold decision, or activation authority. |
| **Phase 5E–5J** | **IMPLEMENTED — acceptance pending** | Contract/schema preparation, price-band extraction, enrichment, connectors, CLI, and regression work are present in PR #3 and 01a. Connector tests use file/fixture feeds; live streaming providers remain deferred. Later UI/product docs supersede older descriptions that call the presentation layer merely a prototype. Historical pass counts are not new test results. |
| **UI-1–UI-7** | **IMPLEMENTED — acceptance pending on 01a** | Presentation API/read-only service, dashboard/backtest/calibration views, and UI-7 PDF-ingestion workflow are documented and present on 01a, not PR #3 or 4e. UI-7 is an ingestion workflow, **not enterprise authentication/RBAC**. The recorded UI test counts are historical reports only; this audit did not run them or independently accept the product. |
| **CFO/PAT, R.K. Fashion, lifecycle, and UI-7 hardening repairs** | **IMPLEMENTED — acceptance pending on 01a** | CFO/PAT deterministic arithmetic repair (`690d472`), R.K. Fashion repair (`aa4d76a`), evaluation lifecycle/lineage work (`39d9a35`), UI-7 public server-path security fix (`9f55eb6`), and upload-handler fix (`4eb700f`) are present with branch-reported targeted tests. R.K. Fashion work addresses supplier concentration, industry CAGR, and statutory CFO. No repair was repeated. Independent acceptance remains unverified. |
| **GCP reference fixture** | **BLOCKED — policy sign-off required; runtime behavior retained** | The v1.5 behavior keeps undisclosed `[●]` GCP `UNKNOWN` and records the statutory ceiling separately. The old VNL reference fixture discrepancy is described as “resolved, needs sign-off”; the v1.5 artifact manifest's precedence is not itself a separate R. Kapoor/Ramki confirmation that the legacy fixture is superseded. No fixture/scoring change or retrospective approval is made here. |
| **EPC / real estate overlay** | **CLOSED — current shared treatment verified; no split authorized** | The inspected config uses a shared `epc_real_estate` profile/overlay. No authority was found to split EPC and real estate or change scoring. |
| **Sector-relative / bank-NBFC coverage** | **PARTIALLY IMPLEMENTED — evidence/acceptance pending** | Generic sector-relative and financial-institution code/test coverage exists, but the reviewed reports do not establish broad point-in-time real-source coverage or independent acceptance. Synthetic fixtures do not establish those claims. No new code is authorized by a coverage gap alone. |
| **Integration / acceptance** | **BLOCKED — technical prerequisite and independent acceptance required** | There is no unified candidate containing the later 01a app and the 4e governance/A9 line, and no independent review or completed CI on PR #3. Establish the intended delivery tip and reconcile refs only under explicit authority, then obtain a named independent review and appropriate CI/acceptance evidence. |
| **Merge / release / production activation** | **NOT AUTHORIZED** | PR #3 remains open. No merge, release, or activation authority was found. Keep the Phase 7 config inactive. |
| **Deferred roadmap** | **DEFERRED — not current blockers** | Live exchange quote streams, automated corporate-action calendars, SQL/multi-user persistence, infrastructure, and enterprise auth/RBAC remain outside current single-user personal-use scope absent a specific decision. Keep VIX separate from NIFTY trend. |

## 5. Implementation inventory — do not mistake blockers for authorization

| Candidate / gap | Repository evidence | Current classification | Gate before any change |
|---|---|---|---|
| NIFTY SMA-50/200 classification and required-input Final gate | Approved semantics exist in 4e; runtime calculation/gate is absent from inspected app refs. | **BLOCKED — evidence required** (plus implementation authority not granted). | Qualifying source-native session series and availability-by-cutoff rule; Phase 0 contract; explicit implementation scope. Keep VIX, listing gains, scoring weights and legacy aliases separate. |
| A9 GMP rule on product delivery line | A9 policy and partial gate exist only on 4e; absent from PR #3/01a; hash-specific negative-test coverage is not evident in the inspected list. | **PARTIALLY IMPLEMENTED / branch integration and source contract open.** | Preserve A9 as settled; establish provider/event/cutoff and source-specific hash representation; explicit implementation authority; test Final blocking without accepting generic hashes. |
| Canonical A8 provenance/conflict record | Current generic fields do not explicitly capture all approved event/publication/availability/retrieval/cutoff/zone distinctions or field-level adjudication. | **BLOCKED — policy/contract decision required.** | Phase 0 approves a versioned field contract and record semantics first; separate Phase 1/schema authority is required. |
| Subscription/GMP/market/peer provider-specific adapters | No approved provider/source contracts for these A8 categories; generic adapters are not provider qualification. | **BLOCKED — evidence and policy required.** | Select/qualify real source evidence, event and cutoff contract, provenance/hash, missing/stale behavior, and implementation authority per connector. Do not invent a provider. |
| Peer eligibility / A5 thresholds | Generic peer plumbing exists; A5 remains evidence-insufficient and thresholds are not approved. | **BLOCKED — evidence/policy required.** | Actual source/universe snapshot and explicit eligibility/calibration decision; do not copy legacy values. |
| Full branch consolidation | App/UI/Track B work is on 01a/PR #3; latest A8/A9/A10 authority is on 4e. | **BLOCKED — technical prerequisite and authority.** | Name the canonical candidate/ref, authorize reconciliation, then review/test that exact unified tree. No cherry-pick or merge in this audit. |

This is not a claim that every row is a currently approved coding task. Several are prerequisites for deciding whether code is needed at all.

## 6. Dependency-aware implementation sequence

The order below is a **dependency order, not a business-priority ranking**. A9 and NIFTY are separate workstreams and become parallel implementation candidates only after their shared evidence-model/candidate prerequisites are resolved. Nothing in this sequence grants implementation authority.

| Order | Item and what is missing | Already complete | Implementation authority | Dependencies | Acceptance criteria | Smallest next action |
|---|---|---|---|---|---|---|
| **0 — governance gate** | No formal Phase 0 closure/freeze or unified candidate selection; Phase 1 is not authorized. The intended product delivery ref is not settled across PR #3, 01a, and 4e. | Specific A8-M semantics and required-NIFTY UNKNOWN rule are approved; A9's narrow GMP Final rule is approved; A10's interim subscription policy is approved. | **No** for new application/schema changes, branch integration, or release. | None; this is the gate for all subsequent work. | Durable owner decision names scope, branch/candidate, Phase 0 exit criteria, independent reviewer, and separately authorized Phase 1 work. | Request DP-01/DP-07 decisions: close/freeze or enumerate open P0 contracts; name candidate; grant exact implementation scope. Do not select the branch on the owner's behalf. |
| **1 — canonical evidence/output contract** | The generic evidence model lacks explicit, distinct A8 source-event/session, original zone/offset and normalized time, publication/availability, retrieval, cutoff/evaluation, source/hash scope, revision, and field-level adjudication representation. A7's serialized evaluation result also remains incomplete. | Generic `SourceRef`/`Evidence`, tri-state values, provenance and immutable evaluation records exist. A1/A7 policy records exist; they do not themselves authorize schema work or make field-level resolutions. | **No.** Phase 1/schema authority is not granted. | Order 0; an owner-approved field map and versioning decision. | Contract preserves original observations and status; separates event/publication/retrieval/cutoff; links conflicts to attributable field decisions; retains A7 output distinctions; round-trip/validation tests reject missing, ambiguous, conflicting, or unqualified evidence without silently qualifying generic hashes. | Approve the canonical field map and result contract as a decision input first; do not edit schema or fixtures yet. |
| **2A — A9 GMP gate on the selected product candidate** | A9 runtime gate is present only on 4e, absent from PR #3 and 01a; source-specific hash tests are not evident. The actual product candidate is not selected. | A9 policy is settled. Partial `pipeline.py` implementation and a limited test set exist on 4e. | **No.** The A9 record expressly withholds implementation authority. | Orders 0–1; a source/event/cutoff/hash contract; chosen candidate; separate narrow implementation authorization. | On the selected tree, missing or invalid required qualifying snapshot/hash withholds `FINAL`; a blocked marker or generic payload hash cannot qualify; scope stays GMP-only; subscription and unrelated scoring/config remain unchanged; targeted positive/negative tests cover the provider contract. | Obtain the provider/hash contract and explicit permission for only the A9 gate/test integration; do not reopen A9's policy. |
| **2B — NIFTY trend calculation and required-input Final gate** | No application SMA classifier or NIFTY-specific required-input Final gate exists on the inspected application refs. Current saved history is descriptive/unqualified; cutoff availability and deterministic session/publication rule remain open. | Classification and NIFTY-only UNKNOWN-to-Final policy are approved; existing historical calculation/evidence package is complete for its stated limits. | **No.** The approval records explicitly deny implementation authority. | Orders 0–1; source-native qualifying close series, source-defined revision evidence, a complete 200-session window, and supported availability/calendar rule; chosen candidate; separate implementation authority. | Complete valid expected sessions only; strict above/below, mixed/equality neutral; missing/invalid/unqualified/stale/conflicting input UNKNOWN with reason; required UNKNOWN blocks Final; provenance/cutoff preserved; no VIX/listing blend, score-map, alias, or weight change. | Seek explicit authorization for the already-prepared no-cost NDAL factual request (still UNSENT); stop if it requires subscription/payment. That is evidence acquisition, not code approval. |
| **3 — remaining A8 source adapters and metrics** | Subscription source/event/final fields and Final consequence; GMP source beyond A9; peer source/universe/A5 eligibility; plus separate anchor, listing-gain, and VIX contracts remain incomplete. Generic adapters are not provider qualification. | A10 interim subscription policy, P1 peer-observation direction, A8 timestamp safeguards, and generic Phase 5H adapters exist. | **No** for provider configuration, scoring, schema, or adapter changes. | Orders 0–1 plus each metric's own approved source/evidence contract and explicit per-change authority. A5 requires real calibration evidence/parameter approval. | Per metric: evidence of actual event/observation, named source/session/cutoff, separate timestamps, units/denominator, conflict/revision handling, freshness and missing-input consequences; no cross-metric substitution. | Ask for one source/metric contract at a time. Do not initiate broad source re-investigation or invent providers. |
| **4 — other evidence/coverage and existing engineering work** | Phase 5E–5J, UI-1–UI-7, Track B 6A–6D/Phase 7, CFO/PAT and R.K. Fashion repairs already exist across PR #3/01a; the remaining gap is acceptance on one candidate. Sector/bank claims lack demonstrated broad real-source acceptance. GCP fixture supersession still needs sign-off. | The cited code and historical tests/reports are on named refs. EPC/real estate currently shares `epc_real_estate`; no split is approved. | No new implementation authority for edits. Historical implementation does not grant new scope. | Candidate selection; for sector/bank additions, identify a specific unmet requirement and source-backed gap; for GCP, obtain explicit fixture disposition. | Independent review of existing functionality on exact tree; any new sector/bank change must map to an approved real-evidence requirement; GCP fixture treatment must be explicitly signed off before fixture changes. | Do not repeat reported fixes/tests. Obtain GCP sign-off and list any specific acceptance gaps on the selected tree; defer all speculative expansions. |
| **5 — branch integration and independent acceptance** | No ref combines the later 01a application with current 4e A8/A9/A10 governance; PR #3 is older and has no reviews/checks. No independent acceptance record exists. | PR #3 is currently open/CLEAN; implementation reports exist on branches. | **No** for merge/cherry-pick/release. A narrowly authorized docs-only publication would not select a product delivery branch. | Owner names target candidate and authorizes integration; all approved changes completed and tested. | One exact candidate commit/tree; documented ancestry and conflict resolution; CI/test evidence for that exact tree; independent named review; evidence limitations and single-user scope retained. | Request canonical candidate/ref and independent reviewer. Do not merge or cherry-pick in this run. |
| **6 — merge, release, activation** | No merge/release/production authorization. Phase 7 remains inactive. | No merge or activation occurred. | **No.** | Order 5 passed plus separate explicit authority for each release/activation gate. | Release checklist and independent acceptance for exact candidate; separate explicit merge/release/production approval; inactive config remains inactive unless separately authorized. | No action until all prior gates pass and the owner gives explicit release authority. |

Other current items are **decision/evidence gates, not queued implementation**: D1/D2/D3 disposition; A5 calibration; GCP sign-off; and any new source/metric policy. Live quote streams, automated corporate-action calendars, SQL/multi-user persistence, infrastructure, and enterprise auth/RBAC remain deferred under the existing single-user scope.

## 7. Decision packages prepared for the missing authority/evidence

These packages identify decisions/evidence to request; they do not make the decisions.

### DP-01 — Phase 0 exit, canonical contract, and independent acceptance

- **Decision owner:** Ramki/Program Authority; an independent reviewer must be named separately.
- **Decision needed:** Define Phase 0 closure/freeze criteria and the accepted serialized value/evidence/result contracts, including A1 field-level resolution records and A7's still-open terminal-state case. Clarify which source-specific A8 distinctions are mandatory fields and their versioning.
- **Evidence to attach:** Exact candidate commit/tree; v1.5 reconciliation; all unresolved contracts; branch-diff inventory; tests/review plan.
- **Acceptance gate:** Durable, attributable decision; frozen scope; no unresolved required schema/output semantics; independent review of the selected candidate. Phase 1 authorization is a separate decision and must enumerate permitted changes.
- **Do not do:** Treat this audit, tests, or the current generic schema as Phase 0 closure.

### DP-02 — A8-M source qualification and bounded next step

- **Policy not to reopen:** NIFTY price-index SMA classification, required-NIFTY UNKNOWN behavior, metric separation, and no numeric delay allowance are already approved.
- **Evidence gap:** Source-native NSE index records/bytes, index/session/official-close identity, event and revision semantics, availability by an explicit cutoff, original zone/offset, publication vs retrieval, and a complete expected-session series.
- **Decision/action requested:** The existing factual NDAL request in the 4e investigation is **UNSENT**. Obtain explicit authorization before sending it. It should be the already-prepared no-cost factual request; stop if a subscription/purchase or charge is required. Do not rewrite/re-send it, subscribe, or buy data without separate authority.
- **Possible later implementation surfaces (not approved now):** connector/source adapter; canonical provenance and market snapshot models/schema; NIFTY computation; required-input Final gate; focused tests. Acceptance must cover complete windows, missing/invalid expected sessions, strict/mixed/equal comparisons, cutoff/freshness, conflicting revisions, source provenance, and required UNKNOWN blocking Final. No score weights/config changes or VIX coupling.

### DP-03 — A9 implementation contract (without reopening A9)

- **Policy not to reopen:** Missing/invalid required qualifying GMP snapshot/hash blocks Final; a blocked marker is not a qualifying hash.
- **Decision/evidence needed:** Approved source and qualifying actual event/as-of semantics; source-specific cutoff and publication/retrieval treatment; exact source-native bytes/hash scope/serialization and required snapshot representation; explicit implementation authority.
- **Acceptance:** A9 behavior is enforced on the chosen delivery line; invalid/missing required source hash fails Final; a generic JSON/payload hash cannot falsely qualify the provider record; Preliminary and subscription handling remain unchanged; provider-specific tests use evidenced contract data.

### DP-04 — A8-S, A8-P/A5, and other market observations

- **A8-S:** Identify approved sources separately for NSE, BSE, and All Exchange; final-record event/as-of; categories, fields, units, denominator/normalization; publication/retrieval/cutoff; freshness and missing-record Final behavior. A10 remains evidence/display only until the contract is approved.
- **A8-P/A5:** Select source and named session; define point-in-time universe snapshot, listing/valuation dates, source/cutoff, eligibility and calibration evidence/parameters. Explicitly decide any thresholds; do not adopt legacy 30-day/3-year values.
- **Other A8-M metrics:** Separately decide VIX source/meaning/cutoff/use; listing-gain cohort and price/time convention; anchor quality rubric and anchor amount field/units/scope. Do not fold these into NIFTY or infer policy from current implementation.
- **Acceptance:** Each contract has source-native evidence, distinct event/publication/retrieval/cutoff values, conflict behavior, and metric-specific `FINAL` consequence. Each scoring or schema change needs its own implementation authority.

### DP-05 — Track B D1/D2/D3 and Phase 7 status

- **D1:** Record the authoritative disposition of the original Phase 6A–6D scope question for current/future work; do not fabricate a retrospective approval from tests or implementation.
- **D2:** Mark the old Phase 5/UI sequencing question stale or request a new priority only for genuinely remaining work. UI-1–UI-7 and Phase 5E–5J have since been implemented on the product line; that fact alone does not prove the priority decision.
- **D3:** Decide future calibration promotion rules only with an identified real, mature, point-in-time sample and explicit holdout/leakage/downside criteria. The Oct 6 `N ≥ 15` proposal and code maturity tiers are not a new approval. The specific Phase 7 artifact carries a prior approval assertion for an inactive controlled-verification candidate; that is not general D3 policy or production activation.
- **Acceptance:** Durable authority record identifies exact policy and population; independently validated non-synthetic data and holdout; inactive state preserved until a separate activation authorization.

### DP-06 — GCP fixture sign-off

- **Decision owner:** R. Kapoor/Ramki per the historical report.
- **Decision needed:** Explicitly confirm whether the legacy VNL reference fixture is superseded by the authoritative v1.5 treatment, or state the intended conflict handling.
- **Current behavior to preserve:** Undisclosed `[●]` remains UNKNOWN; legal ceiling is separate, never substituted as the amount.
- **Acceptance:** Attributable decision and traceable fixture disposition. No fixture/scoring change or retrospective approval before then.

### DP-07 — Canonical product tip, review, and release

- **Decision needed:** Name the canonical delivery ref/tree and authorize any branch reconciliation; identify independent reviewer and required CI/acceptance matrix. Separately authorize merge/release/production only if intended.
- **Current facts:** PR #3 is open; 01a contains later application code; 4e contains later governance/A9; neither set is integrated in a reviewed, accepted candidate.
- **Acceptance:** One named candidate commit; branch integration reviewed; test results from that exact tree; independent acceptance; release authority. Do not infer these from `CLEAN` mergeability or passing implementation tests.

## 8. Publication authority and tracker candidate

The source repository tracker remains on 4e at `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`, last changed in commit `40a3f1e8`; the source file/ref is untouched. Its “Delivery branch: 4e” label does not distinguish the later product line and open PR.

**Authority determination before the user's confirmation:** GOV-001 authorizes the `handoff/decisions/` location and format, not general publication of a cross-workstream audit or tracker mutation. The A8-M handoff's additive-publication scope covers its two A8-M decision records, its reconciliation addendum, and A8-M tracker status—not these broader artifacts. That existing authority was insufficient by itself.

**Authority now received:** on 2026-10-13, Ramki explicitly selected PUB-1 (publish the audit and tracker-delta proposal to the fixed session branch) and TRK-1 (copy forward the current 4e tracker to the same path on the session branch and apply the delta as a candidate pending review). This grants documentation-only publication/copy-forward in that scope. The 4e source tracker is not mutated; this copy is not canonical and does not select a product delivery branch, authorize Phase 1, or approve the analysis as policy.

The candidate tracker is `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` on the session branch. The companion `handoff/investigation/TRACKER-DELTA-PROPOSAL-DRAFT-2026-10-13.md` records the proposed changes. The separate authorization-request file remains local and is not part of publication.

## 9. Actions taken / not taken

**Completed:** current branch/HEAD/worktree/index and remote refs re-verified; PR #3 state re-queried; the two existing drafts revalidated against only the governing A8/Phase 0 records and cited product/Track B artifacts; corrected the A8-S implementation-vs-policy status, added the requested dependency-aware sequence and later lifecycle/security/upload repairs; received explicit PUB-1/TRK-1 documentation authority; copied the 4e tracker to the session branch and applied the proposal as a review candidate; committed/pushed only the authorized Markdown artifacts to the fixed session branch and verified the remote ref.

**Not done:** no engine or schema edits; no scoring/config/fixture/test changes; no SMA re-calculation or source re-investigation; no provider contact or NDAL request; no subscription or purchase; no Windows verification; no independent acceptance; no change to the source tracker on 4e; no branch switch, PR update/merge, release, or production activation.

## 10. Key source refs inspected

- Governing/evidence line: `origin/arena/4e1080b7-ipo-screening-engine` at `adbd93c5b4450fb113561368d7d101eb4686c842`; A8-M approvals, A8 final-snapshot contract, A9, A10, A8-M source qualification report, and repository tracker.
- Product/evidence line: `origin/arena/01a10b42-ipo-screening-engine` at `4b19faf848a721265597a678926988d484d30e59`; UI-1–UI-7 reports, product/capability/traceability/runbook, final report, canonical model/schema, VNL fixture, and later repair commits.
- PR candidate: `origin/arena/ipo-screening-engine-v1.5` at `49c994430148d327e0afff6d67f31072563d64cc`; Phase 5, Track B, Phase 7 candidate and tests.
- Main/session baseline: `01ba66c12ca1195fd7acbd287c3e39a019808094`.
