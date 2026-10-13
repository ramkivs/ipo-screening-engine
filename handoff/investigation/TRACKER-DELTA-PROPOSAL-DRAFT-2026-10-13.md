# Proposed Tracker Delta — IPO Screening Engine (2026-10-13)

> **Status: PUBLISHED PROPOSAL — APPLIED ONLY TO A SESSION-BRANCH TRACKER CANDIDATE; NOT CANONICAL.** This is not a project decision, acceptance, implementation authority, or release approval, and is not a copy/update of an inaccessible Library tracker. Ramki authorized the documentation-only proposal and candidate copy-forward on 2026-10-13. The source tracker on 4e was not edited; no product delivery branch was selected.

- **Prepared on:** `arena/573e69a4-ipo-screening-engine`, baseline `01ba66c12ca1195fd7acbd287c3e39a019808094`
- **Evidence snapshot:** `main` `01ba66c`; PR #3 `49c9944`; product/evidence branch `01a` `4b19faf`; governance/evidence branch `4e` `adbd93c`
- **Full rationale and decision packages:** `handoff/investigation/IPO-SCREENING-ENGINE-RECONCILIATION-AUDIT-DRAFT-2026-10-13.md`

## Proposed status vocabulary

- **CLOSED — POLICY DECISION VERIFIED:** the cited policy decision is found; this does not close its broader workstream.
- **IMPLEMENTED — ACCEPTANCE PENDING:** code exists on the named ref; no independent acceptance is claimed.
- **PARTIALLY IMPLEMENTED:** only a subset or generic scaffolding exists.
- **BLOCKED — EVIDENCE REQUIRED:** provider/source or real-world evidence prerequisite is absent.
- **BLOCKED — POLICY DECISION REQUIRED:** authority has not approved the required choice.
- **BLOCKED — TECHNICAL PREREQUISITE:** refs/contracts/CI or another technical gate prevents acceptance.
- **RECHECK REQUIRED:** a stale or contradictory record needs an attributable disposition.
- **NOT AUTHORIZED:** do not execute the change absent explicit authority.
- **DEFERRED:** explicitly outside the current single-user scope, not a current blocker.

## Proposed rows

| Workstream / item | Proposed status | Current verified state | Next gate / owner input |
|---|---|---|---|
| NIFTY classification semantics | **CLOSED — POLICY DECISION VERIFIED** | 2026-10-13 policy approves NIFTY 50 price-index close vs. trailing SMA-50/200, strict above/below categories, neutral for other valid cases, and UNKNOWN for incomplete/invalid inputs. | Do not reopen. This is policy only; it does not grant runtime/schema/config/scoring/release authority. |
| A8-M evidence and session/publication availability | **BLOCKED — EVIDENCE REQUIRED** | Existing history/SMA material is descriptive and not qualified under the approved source-native/cutoff contract. 10/09 and 10/12 cross-check observations were not appended or recalculated. No current category assigned. | Obtain source-native qualifying record(s), complete expected-session window, provenance and availability-by-cutoff evidence; support deterministic session/publication rule. NDAL request remains **UNSENT**; obtain explicit authorization before sending and stop if any cost/subscription is required. |
| NIFTY runtime calculation / required Final gate | **NOT AUTHORIZED; BLOCKED — EVIDENCE REQUIRED** | No application implementation found for the approved SMA-derived category and required-NIFTY UNKNOWN-to-Final behavior. | After evidence and Phase 0 contract close, request explicit implementation scope. Keep VIX/listing gains separate; no score-map, alias, configuration, or release changes. |
| A8-S subscription source/final snapshot | **PARTIALLY IMPLEMENTED — generic connector; A10 runtime handling unverified** | A generic official NSE/BSE subscription adapter exists on the product line, but no evidence was found that it implements A10's later interim handling. A10 allows evidence/display for distinct NSE/BSE/All Exchange observations. S2 actual final record is preferred conditionally; source/event/timestamp/fields/denominator/cutoff and missing-record Final consequence remain open. VNL discrepancy is CLOSED WITH LIMITATION. | Approve source-specific contracts and any Final consequence separately. No subscription scoring or equivalence by inference. |
| A8-G / A9 | **CLOSED — POLICY DECISION VERIFIED; PARTIALLY IMPLEMENTED** | A9's narrow missing/invalid required qualifying GMP snapshot/hash rule blocks Final. A9 runtime gate exists on 4e only; absent from PR #3/01a. Source, cutoff, and source-specific hash contract remain open. | Do not reopen A9 or extend it to subscription. Define qualifying provider/evidence/hash contract and obtain implementation authority; verify hash-specific fail-closed tests. Generic payload hash is not source qualification. |
| A8-P / A5 peers | **BLOCKED — EVIDENCE AND POLICY DECISION REQUIRED** | Actual-session quote direction is approved; provider, named session, point-in-time universe, cutoff, eligibility, and calibration evidence remain unresolved. `CALIBRATION_EVIDENCE_INSUFFICIENT` remains. | Establish source/universe evidence and explicit eligibility/calibration parameters. Do not adopt legacy 30-day/3-year defaults. |
| Phase 0 / canonical A1, A7, A8 contract | **OPEN — BLOCKED BY POLICY/TECHNICAL PREREQUISITES** | A1 identifies Ramki as conflict-adjudication authority but makes no field-level decision. A7 policy exists, but serialized result contract and one terminal-state case remain unresolved. Generic `SourceRef`/`Evidence` fields do not explicitly encode every approved A8 time/provenance distinction or field-level decision. No formal Phase 0 closure/freeze or independent acceptance found. | Approve canonical evidence/value/result model and closure criteria; record field-level adjudications where required; obtain independent review. Do not alter schema while Phase 1 is unauthorized. |
| Phase 1 | **NOT AUTHORIZED** | No Phase 1 implementation authority located. | Require explicit, bounded authority for named files/behaviors and separate approval for merge/release/activation. |
| Track B — 6A–6D | **IMPLEMENTED — ACCEPTANCE PENDING** | Code/tests exist on PR #3 and 01a; readiness/traceability prose last updated Oct 6 and is stale where it says these are future implementation. Historical test results are not independent acceptance. | Resolve D1 authority/status for current/future scope; independently review the exact unified candidate. Do not infer authorization from implementation history. |
| Track B — D1/D2/D3 | **RECHECK REQUIRED / POLICY OPEN** | No separate D1/D2/D3 disposition record located. D2's old UI/Phase 5 sequencing question is stale after delivery. D3's proposed future sample/promotion criteria are not approved as general policy by this audit. | Record current disposition. D3 requires explicit authority and suitable real, mature, point-in-time evidence. Do not adopt proposed N/IC/downside numbers absent that decision. |
| Phase 7 / v1.6 candidate | **IMPLEMENTED — ACCEPTANCE PENDING; INACTIVE** | PR #3 contains a particular approval assertion/candidate; it is recorded inactive for controlled verification. Product reconciliation describes the 120-row sample as synthetic/simulated. No production activation is implied. | Preserve the existing artifact status. Do not treat it as independent real-world validation, general D3 policy, or production authority. Obtain separate activation authorization if ever proposed. |
| Phase 5E–5J | **IMPLEMENTED — ACCEPTANCE PENDING** | Code is present on PR #3/01a; live streaming feeds remain deferred. | No repeat implementation work identified by this audit. Acceptance belongs to the exact selected candidate and requires independent review. |
| UI-1–UI-7 | **IMPLEMENTED — ACCEPTANCE PENDING on 01a** | Presentation API, dashboard, calibration views, and UI-7 PDF-ingestion workflow exist on 01a, not PR #3/4e. UI-7 is not enterprise authentication/RBAC. Test totals in reports are historical. | Integrate only under authority; independently accept. Keep enterprise auth/RBAC deferred under the personal-use scope. |
| CFO/PAT, R.K. Fashion, lifecycle, and UI-7 hardening repairs | **IMPLEMENTED — ACCEPTANCE PENDING on 01a** | CFO/PAT determinism repair (`690d472`), R.K. Fashion supplier concentration/industry CAGR/statutory CFO repair (`aa4d76a`), lifecycle/lineage (`39d9a35`), UI-7 security fix (`9f55eb6`), and upload-handler fix (`4eb700f`) are documented on 01a. | Do not repeat repairs; obtain independent acceptance on a unified candidate. |
| GCP reference fixture | **RECHECK REQUIRED — POLICY SIGN-OFF** | Runtime behavior keeps undisclosed `[●]` UNKNOWN and the statutory cap separate. Historical report calls the VNL fixture conflict “resolved, needs sign-off”; no separate R. Kapoor/Ramki supersession confirmation located. | Obtain explicit fixture disposition. Do not alter fixture/scoring or invent retrospective approval. |
| EPC / real estate profile | **CLOSED — current shared overlay verified** | Current profile is `epc_real_estate`; no split decision found. | No change unless explicitly authorized. |
| Sector-relative and bank/NBFC coverage | **PARTIALLY IMPLEMENTED — EVIDENCE/ACCEPTANCE PENDING** | Generic code/test coverage exists; available reports do not demonstrate broad real-source point-in-time coverage or independent acceptance. | Obtain representative source evidence and separate acceptance. Do not equate synthetic fixtures with field coverage. |
| Branch integration / canonical candidate | **BLOCKED — TECHNICAL PREREQUISITE** | 01a contains later application/UI work; 4e contains later A8/A9/A10 governance; PR #3 is an older separate candidate. No single independently reviewed tree contains both. | Name the canonical candidate and authorize reconciliation; then run/review against that exact tree. No cherry-pick or merge by inference. |
| Independent acceptance | **BLOCKED — INDEPENDENT ACCEPTANCE REQUIRED** | No independent reviewer/review decision or completed PR checks were found. Branch-reported tests alone are not acceptance. | Name independent reviewer and acceptance matrix; do not self-certify. |
| Merge, release, production activation | **NOT AUTHORIZED** | PR #3 remains open; no merge/release/activation authority located. | Obtain explicit authority for each gate. Keep Phase 7 inactive. |
| Live quote feeds, automatic corporate-action calendar, SQL/multi-user persistence, infrastructure, enterprise auth/RBAC | **DEFERRED** | These are outside current single-user personal-use scope absent a specific decision. | Keep out of current blockers unless the user explicitly changes scope. |
| NDAL request | **UNSENT** | Existing factual request is already prepared on the 4e A8-M report; no contact or subscription has occurred. | Do not send without explicit authority; stop if a charge or subscription is required. |

## Proposed branch-label correction

If authorized, replace the single ambiguous “Delivery branch” label with three separate fields:

| Role | Current ref | Tip | Caveat |
|---|---|---|---|
| Governance/evidence | `arena/4e1080b7-ipo-screening-engine` | `adbd93c5` | Contains current A8/A9/A10 records and A9 gate, but not the later full app/UI/Track B tree. |
| Product-code continuation | `arena/01a10b42-ipo-screening-engine` | `4b19faf` | Contains later app/UI/repairs, but not current 4e A8-M/A9/A10 records. |
| Open PR candidate | PR #3, `arena/ipo-screening-engine-v1.5` | `49c9944` | Open to `main`; no reviews or checks; behind 01a and separate from 4e. Not independently accepted. |

**Publication gate:** These proposed rows should be reconciled with the authorized owner and the canonical branch choice before being copied into the existing repository tracker or an external Library tracker. No such publication is made in this draft.
