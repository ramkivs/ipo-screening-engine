# IPO Screening Engine — Project Tracker (Review Candidate)

> **Candidate status:** DOCUMENTATION-ONLY COPY-FORWARD — PENDING REVIEW. This tracker candidate is not yet the canonical delivery tracker, a policy decision, implementation authority, acceptance, or release approval. The original tracker on 4e is unchanged.

- **Updated:** 2026-10-13 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Tracker candidate branch:** `arena/573e69a4-ipo-screening-engine` (session branch; candidate pending review)
- **Governance/evidence reference:** `arena/4e1080b7-ipo-screening-engine` at `adbd93c5b4450fb113561368d7d101eb4686c842`
- **Product-code continuation:** `arena/01a10b42-ipo-screening-engine` at `4b19faf848a721265597a678926988d484d30e59`
- **Open PR candidate:** PR #3, `arena/ipo-screening-engine-v1.5` at `49c994430148d327e0afff6d67f31072563d64cc`
- **Canonical delivery candidate:** NOT SELECTED. These refs are not one accepted release.
- **Authority:** Individual project decisions remain governed by their cited records in `handoff/decisions/`. This tracker is a status summary only.

## Tracker provenance and publication boundary

This is a copy-forward of `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` from `arena/4e1080b7-ipo-screening-engine` (tip `adbd93c5`; source tracker last changed in `40a3f1e8`). Ramki authorized documentation-only publication and a tracker candidate copy-forward on the fixed session branch on 2026-10-13. This candidate is pending review; it does not mutate the source tracker on 4e, select the product delivery branch, or approve the findings as project decisions. The Library tracker was not available in the checkout, and this is not claimed to be its copy or update.

A repository tracker row does not itself grant implementation, source qualification, scoring, schema, release, or production-activation authority. The cross-workstream audit and dependency-aware implementation sequence are in `handoff/investigation/IPO-SCREENING-ENGINE-RECONCILIATION-AUDIT-DRAFT-2026-10-13.md`; that audit is analysis, not an approval record.

## A8-M — NIFTY trend

| Work item | Status | Current state / next evidence or gate |
|---|---|---|
| NIFTY trend meaning and classification | **APPROVED — policy only** | Session-close-derived NIFTY 50 PRICE INDEX; strict comparison with trailing SMA-50 and SMA-200; mixed/equal valid signals are neutral; incomplete/invalid qualifying windows are UNKNOWN. See `handoff/decisions/A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`. No current category is assigned. |
| Observation, cutoff and provenance policy | **APPROVED — policy only** | Explicit cutoff; latest qualifying completed official NSE close demonstrably available by cutoff; event/session, publication/availability, retrieval and evaluation timestamps remain distinct; complete, valid session windows; no unqualified fallback. See `handoff/decisions/A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`. |
| Required NIFTY UNKNOWN → Final eligibility | **APPROVED — NIFTY only** | If NIFTY trend is required and UNKNOWN, withhold Final, return non-final/incomplete, identify the input/reason, and keep score range/completeness diagnostic only. Does not set Final policy for other metrics. |
| Source-native evidence qualification | **OPEN / BLOCKED — evidence required** | Existing NSE history/SMA package is descriptive rendered/local evidence through 2026-10-08; latest reported SMA-50/SMA-200 are 23,761.064 / 24,282.7665. Exact provider bytes and availability-before-cutoff evidence are unavailable. Qualify an authoritative NSE price-index record, source-native session/close semantics, provenance and availability before using it for Final. Do not assign a category from these historical averages alone. |
| Deterministic session calendar/publication-availability rule | **OPEN PREREQUISITE** | Support a deterministic, testable rule with NSE session/special-session and source-availability evidence. Cover cutoff, weekends, holidays, special sessions, future/impossible times and unresolved timezone. No numeric publication-delay allowance is authorized. |
| NIFTY runtime calculation / Final gate | **NOT AUTHORIZED; NOT IMPLEMENTED on inspected app refs** | No application SMA classifier or required-NIFTY Final gate was found. Implementation authority is expressly not granted. Wait for evidence, Phase 0 contract, and separate implementation authority. |
| A8-M overall | **OPEN** | Policy is approved; source-native qualification and deterministic freshness prerequisite remain open. No current trend category/score or production-ready metric is established. |
| Phase 0 / Phase 1 | **Phase 0 OPEN / Phase 1 UNAUTHORIZED** | No formal Phase 0 closure/freeze or independent acceptance record was located. |
| Implementation / release / production activation | **NOT GRANTED / NOT AUTHORIZED** | No runtime, configuration, scoring, schema or release changes are authorized by the A8-M policy publication. |

## Cross-workstream status update

| Workstream | Status | Current verified state / next gate |
|---|---|---|
| **A8-S — subscription** | **PARTIALLY IMPLEMENTED — generic adapter; A10 runtime unverified** | A generic official NSE/BSE subscription adapter exists on the product line. No evidence was found that it implements A10's later interim handling. A10 approves distinct NSE, BSE, and All Exchange observations for evidence/display only, not scoring or equivalence. Source/event/fields/units/denominator/cutoff/freshness and missing/unavailable Final consequence remain open. VNL discrepancy remains CLOSED WITH LIMITATION. |
| **A8-G / A9 — GMP** | **A9 policy CLOSED; gate PARTIAL on 4e only** | A9's narrow rule is approved: an absent/invalid required qualifying GMP snapshot or required hash withholds Final; a blocked marker is not a qualifying snapshot/hash. It does not select a source or define event/cutoff/hash serialization. The gate is absent from PR #3 and 01a; inspected tests do not specifically cover missing/invalid source-hash qualification. Generic payload hashing is not an approved source contract. Do not reopen A9 or extend it to subscription. |
| **A8-P / A5 — peer data** | **BLOCKED — evidence and policy decision required** | Approved direction prefers actual quote/valuation observations for a named session and separates raw observations/universe from eligibility. No provider, session/cutoff, reproducible point-in-time universe, or eligibility contract is approved. A5 remains `CALIBRATION_EVIDENCE_INSUFFICIENT`. Do not adopt legacy 30-day/3-year defaults or claim production peer scoring. |
| **Phase 0 / A1, A7, canonical evidence/output contract** | **OPEN — policy/technical prerequisites** | A1 designates Ramki as conflict-adjudication authority but is not a field-level adjudication; each disputed field needs its own durable decision. A7 policy exists, but concrete serialized output and a terminal-state case remain unresolved. Current generic source/evidence fields do not explicitly encode every approved A8 timestamp distinction and A1 resolution record. No schema change is authorized. |
| **Phase 1** | **UNAUTHORIZED** | No Phase 1 implementation authority was located. Approved semantics, completed investigations, or code on another branch do not grant implementation authority. |
| **Track B — Phases 6A–6D** | **IMPLEMENTED — ACCEPTANCE PENDING** | Code/tests exist on PR #3 and 01a, not main or 4e. Oct 6 readiness/traceability descriptions are stale where they present these phases as future implementation. Branch-reported tests are not independent acceptance. D1's separate scope disposition was not located. |
| **Track B — D1/D2/D3** | **RECHECK REQUIRED / POLICY OPEN** | No separate D1/D2/D3 disposition record was located. D2's UI/Phase 5 sequencing question is stale after those deliveries; completion does not prove a priority decision. D3's proposed future sample/promotion thresholds are not established as general policy. Do not adopt `N ≥ 15`, IC, downside, or other figures absent an attributable decision and suitable evidence. |
| **Phase 7 / v1.6 candidate** | **IMPLEMENTED — ACCEPTANCE PENDING; INACTIVE** | PR #3 has a specific proposal/approval assertion and inactive candidate for controlled verification. Product docs describe its 120-row sample as synthetic/simulated. This is not independent real-world validation, general D3 policy, or production activation. Keep inactive absent separate activation authority. |
| **Phase 5E–5J** | **IMPLEMENTED — ACCEPTANCE PENDING** | Contract/schema preparation, price-band extraction, enrichment, connectors, CLI and regression work exist on PR #3/01a. File/fixture feeds are implemented; live streaming is deferred. Historical reported tests are not new runs or independent acceptance. |
| **UI-1–UI-7** | **IMPLEMENTED — ACCEPTANCE PENDING on 01a** | Presentation API, dashboards, calibration views, and UI-7 PDF-ingestion workflow exist on 01a, not PR #3/4e. UI-7 is not enterprise authentication/RBAC. Reported test counts are historical. |
| **CFO/PAT, R.K. Fashion, lifecycle, UI-7 hardening** | **IMPLEMENTED — ACCEPTANCE PENDING on 01a** | CFO/PAT repair (`690d472`), R.K. Fashion repair (`aa4d76a`), lifecycle/lineage (`39d9a35`), UI-7 security fix (`9f55eb6`), and upload-handler fix (`4eb700f`) exist with branch-reported targeted tests. No independent acceptance is established. Do not repeat the repairs. |
| **GCP fixture** | **RECHECK REQUIRED — owner sign-off** | v1.5 runtime keeps undisclosed `[●]` UNKNOWN and the statutory ceiling separate. Legacy VNL fixture discrepancy is described as “resolved, needs sign-off”; no separate R. Kapoor/Ramki confirmation that it is superseded was located. No fixture/scoring change or retrospective approval. |
| **EPC / real estate** | **CURRENT SHARED OVERLAY VERIFIED; no split authorized** | Current profile is `epc_real_estate`. No authority to split or change scoring was located. |
| **Sector-relative / bank-NBFC coverage** | **PARTIALLY IMPLEMENTED — evidence/acceptance pending** | Generic code/test coverage exists; reviewed reports do not establish broad point-in-time real-source coverage or independent acceptance. Synthetic fixtures do not establish broad coverage. |
| **Integration / independent acceptance** | **BLOCKED — technical prerequisite and independent acceptance required** | No ref unifies the later 01a application with current 4e governance/A9; PR #3 is an older separate candidate. PR #3 currently has no reviews or checks. Name a candidate and independent reviewer, then validate that exact tree. |
| **Merge / release / production activation** | **NOT AUTHORIZED** | PR #3 remains OPEN. `CLEAN` mergeability is not acceptance. No merge, release, or activation authority was found. Keep Phase 7 inactive. |
| **Deferred roadmap** | **DEFERRED — not current blockers** | Live exchange quote streams, automated corporate-action calendars, SQL/multi-user persistence, infrastructure, and enterprise auth/RBAC are outside the current single-user personal-use scope absent a specific decision. Keep VIX separate from NIFTY trend. |
| **NDAL request** | **UNSENT** | Existing factual request is prepared in the 4e A8-M investigation. No contact, subscription, or purchase is authorized here. Obtain explicit authorization before sending; stop if a charge or subscription is required. |

## Dependency-aware next sequence

This order is by prerequisite, not business priority. A9 and NIFTY are independent consumer workstreams after the shared evidence/candidate prerequisites; this tracker does not rank one above the other.

1. **Owner gate:** decide Phase 0 closure/remaining contracts, name the canonical candidate, and separately grant exact implementation scope. No grant is present here.
2. **Canonical evidence/output contract:** approve the field map, serialization, revision and field-level conflict record before any schema change. Phase 1 authority is still required.
3. **Parallel source-specific gates:** after the canonical contract, (a) integrate/test the A9 GMP gate on the selected product candidate once its source/hash contract and implementation permission exist; and (b) implement NIFTY only after source-native closes and cutoff/session-availability evidence, then test the approved UNKNOWN/final behavior. Neither is currently authorized.
4. **Other A8 integrations:** settle each subscription, GMP-source, peer/A5, VIX, listing-gain, and anchor contract with actual source/evidence before proposing code. Do not invent sources or thresholds.
5. **Existing work / coverage:** obtain independent acceptance of Phase 5E–5J, UI-1–UI-7, Track B, Phase 7 and the named repairs on one exact tree. Add sector/bank code only for a specific approved gap supported by evidence. Obtain GCP fixture sign-off before any fixture change.
6. **Integration and release:** authorize branch reconciliation, review/tests, and independent acceptance for the named candidate; merge/release/production remain separate unauthorized decisions.

The audit draft contains the item-by-item missing/completed/authority/dependency/acceptance/next-action table. This sequence grants no work.

## Deferred and recheck boundaries

- **DEFERRED / OUT OF SCOPE:** Do not combine NIFTY trend with VIX, recent IPO listing gains, subscription, GMP or peers. Their source, semantics, freshness and Final consequences remain separate contracts.
- **RECHECK:** Reassess source-qualified NIFTY evidence only after the evidence and session/publication-availability prerequisites are satisfied. A missing or unqualified required input remains UNKNOWN and blocks Final when NIFTY is required.
- **NO RETROSPECTIVE APPROVAL:** Implementation, tests, or completed investigation do not substitute for missing policy or implementation authority.
