# A8 — Final Snapshot Policy Directions and Event/Cutoff Contract

- **Decision ID:** A8
- **Title:** Approved policy directions and source-specific event/cutoff requirements for Final snapshots
- **Status:** RAMKI-APPROVED POLICY DIRECTIONS RECORDED; SOURCE/PROVIDER/EVENT/CUTOFF CONTRACTS OPEN; MISSING-GMP FINAL RULE RESOLVED BY A9; PHASE 0 OPEN; PHASE 1 UNAUTHORIZED
- **Decision authority:** RAMKI for approved A8 policy directions and remaining selections (A1 designates RAMKI as conflict-adjudication authority; this record does not adjudicate source conflicts).
- **Approval provenance and date:** Ramki's explicit approval of A8-S, A8-M, A8-G and A8-P, and the common timestamp/evidence safeguards, in the TASK 18 instruction received 2026-10-10 (Asia/Calcutta). Earlier general A8 principles and investigation recorded 2026-10-09 (Asia/Calcutta).
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** Original investigation baseline: branch `arena/4e1080b7-ipo-screening-engine`, pre-record commit `01ba66c12ca1195fd7acbd287c3e39a019808094`. Task 18 amendment baseline: the same session branch at published Task 16 commit `abaac15ed3ffbb4b951c1b3f00b9d725b3ebbc07`.
- **Scope:** Reconciliation of v1.5 requirements and inspectable repository evidence with approved A8 policy directions and the remaining source-specific subscription, market, GMP and peer snapshot contracts.
- **Implementation authority:** NOT GRANTED. This record does not authorize provider configuration, application implementation, peer scoring or Phase 1.

## Previously approved A8 principles (Task 16; retained)

**RAMKI-APPROVED DECISION:** Final snapshots use source-specific actual events and cutoffs; evidence must establish event occurrence; original timestamps and timezone/offset information must be preserved alongside normalized UTC timestamps; scheduled events are not completed events; and no freshness interval or cutoff may be invented. These principles remain in force.

## Task 18 approved policy directions and open source contracts

The following are **RAMKI-APPROVED DECISIONS** recorded from Ramki's explicit Task 18 approvals on 2026-10-10 (Asia/Calcutta). They select policy directions, not actual data providers or complete source-specific event/cutoff contracts.

### A8-S — Subscription

**RAMKI-APPROVED DECISION:** Prefer **S2 — the actual final published subscription record**, conditional on an approved source identifying the underlying event and its source-native as-of timestamp. Keep the underlying event/as-of time, source publication time, retrieval time and final evaluation cutoff separate. Publication time must not substitute for event time. If the source cannot establish the underlying event or relevant timestamp, the record is not a verified final subscription snapshot.

**UNAVAILABLE:** Repository artifacts do not identify an approved subscription provider or establish provider behavior for the final record, event identity, as-of timestamp or publication timing.

**UNRESOLVED:** Approved source; exact qualifying event identity and source-native as-of semantics; publication behavior; the source-specific cutoff and its relationship to Final evaluation; and behavior when a qualifying final record is absent or unavailable.

### A8-M — Market

**RAMKI-APPROVED DECISION:** Use a **hybrid market observation policy**. Use an official close for an explicitly specified actual market session for metrics defined on market sessions. A separately approved point-in-time observation rule may be used for metrics that genuinely require it. Specify the source, applicable session or observation rule and cutoff for each metric; do not silently apply one timestamp or cutoff across all metrics.

**UNAVAILABLE:** Repository artifacts do not identify an approved market-data source, actual session, provider event semantics or metric-specific cutoff.

**UNRESOLVED:** Approved source; which metrics are session-defined versus point-in-time; the actual session or point-in-time observation rule and cutoff for each metric; and behavior for non-trading periods or unavailable observations.

### A8-G — GMP

**RAMKI-APPROVED DECISION:** Require an explicitly approved source and an actual timestamped observation. Preserve observation/as-of, publication and retrieval timestamps separately. Do not infer an official or universally authoritative GMP provider, fabricate an absent observation, or substitute application-generated time for source-event time.

**UNAVAILABLE:** Repository artifacts identify no approved GMP source or qualifying observation/publication semantics.

**RESOLVED BY A9 — MISSING-GMP FINAL POLICY:** If a required qualifying GMP snapshot or its required hash is absent or invalid, withhold `FINAL`. A blocked-input marker is not a qualifying snapshot or hash. No exception is authorized by A9.

**UNRESOLVED:** Approved source; qualifying actual observation; source-native event/as-of and timestamp semantics; source-specific cutoff; snapshot/hash representation; and stale or unverifiable handling beyond the A9 condition. Do not infer any other provider-specific behavior.

### A8-P — Peers

**RAMKI-APPROVED DECISION:** Prefer **P1 — capture actual quote/valuation observations for a named market session**, once an approved source and session are established. Preserve raw peer observations and the peer-universe snapshot separately from subsequent eligibility decisions. Record listing date, valuation/price date, source and relevant timestamps. Do not finalize peer eligibility while A5 remains unresolved; do not adopt legacy freshness thresholds or listing-history defaults.

**UNAVAILABLE:** Repository artifacts do not establish an approved peer quote/valuation source, a qualifying actual session, an observation cutoff or a peer-universe snapshot rule.

**UNRESOLVED:** Approved source; named actual market session and observation cutoff; and the reproducible peer-universe snapshot rule. A5 evidence and parameter approval remain prerequisites to peer eligibility and production peer scoring.

### Common timestamp, provenance and event-occurrence safeguards

**RAMKI-APPROVED DECISION (Task 18):** Preserve source identity/reference; the source-native event/observation timestamp; the original timestamp and timezone/UTC offset; normalized UTC timestamp; publication timestamp where applicable; retrieval timestamp; applicable snapshot cutoff and evaluation timestamp; required source/content hashes; and evidence that the actual event or observation occurred. A scheduled event is not evidence that it occurred. These requirements do not establish that a particular provider exposes each item; provider support must be established by the approved source contract.

## v1.5 requirements and reconciliation

- **SPECIFICATION REQUIREMENT —** `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §§4.5–4.6 requires peer listing date, price date and source, and market-value as-of timestamp, timezone, source and source timestamp where available.
- **SPECIFICATION REQUIREMENT —** Specification §§9, 13, 19–21 makes stale peer multiples non-automatically-usable, requires valuation status/range handling, requires timestamped/source-backed market snapshots, freezes subscription, market, GMP and peer valuation snapshots plus configuration version and source hashes in Final, and validates peer listing age, comparability, stale date and source.
- **TARGET ARCHITECTURE REQUIREMENT —** `handoff/authoritative/IPO_Screening_Engine_Technical_Design_v1.5.md` §§3.1 and 10–14 describes generic adapters and source ID, retrieval timestamp, source timestamp, content hash, source type and URI/file reference; it also describes peer listing/valuation dates and immutable snapshots/records. This is generic architecture, not evidence of a currently integrated or approved provider.
- **EXECUTION-PROMPT REQUIREMENT —** `handoff/authoritative/ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md` §§10, 12, 13 and 15 addresses configured peer freshness, timestamp validation, provenance, immutable evaluation records and a relevant Day-3/closing snapshot. It does not name the source or define provider-specific event/cutoff semantics.
- **AUTHORITY —** `handoff/authoritative/ARENA_IPO_Screening_Artifact_Manifest_v1.5.md` establishes the v1.5 specification as authoritative, the technical design as target architecture and legacy assets as references.

**UNAVAILABLE in authoritative v1.5 artifacts:** These artifacts do not select actual subscription, market, GMP or peer providers, or define the source-specific event/observation identities and cutoffs. The v1.5 specification itself does not prescribe missing-GMP `FINAL` handling; the project-level resolution for the absent/invalid required qualifying GMP snapshot/hash condition is recorded in A9. The Task 18 directions remain project decisions layered onto v1.5, not requirements already stated in v1.5.

## Task 17 source findings and ARENA recommendations (historical)

The following findings and alternatives were recorded in the 2026-10-09 investigation, before the Task 18 approvals. The alternatives were **ARENA RECOMMENDATION / design proposals**, not approvals at that time. Task 18 now approves the policy directions in the preceding section; the historic candidates below do not supply provider behavior, exact source events or cutoffs. The current unresolved choices are stated with each Task 18 direction above.

| Snapshot | Explicit requirements | Existing source/provider behavior supported by repository evidence | Task 17 ARENA RECOMMENDATION / candidate event class (unapproved at that time) | Decisions still required |
|---|---|---|---|---|
| **Subscription** | Subscription inputs are listed in specification §4.6; the Final record must freeze a subscription snapshot (§19). The execution prompt refers to Day-3/closing. Timestamp, timezone and source are required for market values. | No named provider, endpoint, source-native timestamp semantics, publication event or cutoff is documented. The technical design generically accepts exchange snapshots; it does not define a subscription-source contract. The legacy browser prototype accepts manual subscription input and stamps it with a prototype-generated ISO `now` (`new Date().toISOString()`, `ipo-scorer_4.html`, around line 268); that does not prove an issue-close or publication event. | **S1:** an approved exchange source's actual subscription/bid-book snapshot as of the issue-closing event, retaining any later publication/retrieval time separately. **S2:** an approved source's final post-close subscription record, retaining both the record's as-of event time and its publication/retrieval times. These are candidate event classes, not verified current provider behavior. | Which source is authoritative? Is the freeze based on the closing-event snapshot or a later final publication? Which timestamp controls the cutoff? What evidence establishes closure/finalization? What happens if the final record is unavailable? |
| **Market** | Market values are snapshot-based and require timestamp, source and mode applicability (§13); market snapshots require as-of time, timezone and source (§4.6); Final freezes a market snapshot (§19). | No named market-data provider, exchange session, closing event or evaluation-time cutoff is documented. The source adapter accepts generic market snapshots. The legacy prototype stamps manually supplied market fields with a prototype-generated ISO `now` (`new Date().toISOString()`, `ipo-scorer_4.html`, around line 267), not a source-observation timestamp. | **M1:** an approved source's official close for a specified actual market session. **M2:** an approved source's timestamped market observation at a specified Final evaluation time. Each requires a named source/session and actual source timestamp. | Which source and session apply to each market metric? Is the cutoff a session close or the Final evaluation time? How are non-trading days, differing market sessions and missing observations handled? |
| **GMP** | GMP is listed as an input and sentiment-only (§§4.6, 13); Final freezes a GMP snapshot (§19). A source and timestamp are required for market inputs. | No GMP provider, quote event, publication timestamp semantics or source-selection rule is documented. No official GMP source is identified by the repository. The legacy prototype accepts manual GMP input and stamps it with a prototype-generated ISO `now` (`new Date().toISOString()`, `ipo-scorer_4.html`, around line 269), which is not evidence of a source quote's observation time. | **G1:** an explicitly approved source's actual GMP observation at or before a source-specific cutoff, preserving the source's as-of/published time and retrieval time. **G2:** if a source cannot establish an observation time, record it as unavailable rather than assigning a timestamp; Ramki must decide whether that prevents Final acceptance or is retained as missing input. | Which provider(s) are approved? What timestamp means “the observation occurred”? What is the cutoff? Can Final be accepted when no qualifying GMP observation exists, or must it be blocked? |
| **Peer valuation** | Peer records require listing date, price date and source (§4.5); stale data cannot silently be used and unavailable valuation affects score range (§9); Final freezes a peer valuation snapshot (§19); validation checks listing age, comparability, stale date and source (§20). | Technical Design §10 specifies `listing_date`, `valuation_date` and source, but no provider, quote event, session cutoff or eligibility-snapshot rule. The repository has no current peer-source contract. The legacy prototype checks a user-supplied peer `as_of` against local `Date.now()` and the reference-config `peer_staleness_days` value (`ipo-scorer_4.html`, around line 147); it emits a warning and does not establish source-native event behavior. A5 freshness and minimum-history parameters remain blocked. | **P1:** use an approved source's quote/valuation observation for a named actual market session. **P2:** use the latest approved-source observation at or before the cutoff, with age measured only after Ramki approves A5's measurement basis and threshold. Neither candidate supplies a numeric freshness or history rule. | Which source and actual quote event/session are authoritative? Which date/time is the peer cutoff? How is the eligible-peer set frozen? What happens to stale, missing or insufficient-history peers? A5 values and the treatment of an insufficient eligible set remain unresolved. |

## Legacy reference behavior (not authoritative source evidence)

The repository also contains v1.4 reference schema and prototype behavior, which the manifest explicitly classifies as non-authoritative:

- `handoff/reference/ipo-input.schema.json` has peer `listed_years` and an `as_of` field constrained by a date definition, but no per-peer source or source-native timestamp field in that peer object. Its market blocks use `as_of` date-time fields but do not define the A8 event, source timezone/offset, publication time or retrieval time contract.
- Static code in `handoff/reference/ipo-scorer_4.html` assigns manually entered subscription, GMP and market/regime blocks a prototype-generated ISO timestamp (`new Date().toISOString()`). That is an entry-generation time, not evidence of the underlying source event. Its peer staleness check compares a supplied `as_of` against `Date.now()` and the legacy config threshold, producing a warning rather than a source-event/cutoff contract.
- The prototype's visible Anthropic API call is for extraction assistance, not a subscription, market, GMP or peer-data feed. No market-data provider integration was found.

These reference fields and code do not establish actual provider behavior, event occurrence or approved cutoffs and are not adopted as v1.5 policy.

## Timestamp, provenance and event-occurrence evidence

**RAMKI-APPROVED DECISION (Tasks 16 and 18):** The common safeguards above require preservation of source identity/reference; source-native event/observation timestamp; original timestamp and timezone/UTC offset; normalized UTC timestamp; publication timestamp when applicable; retrieval timestamp separately from event/observation time; applicable snapshot cutoff and evaluation timestamp; required source/content hashes; and evidence that the actual event/observation occurred. Scheduled dates or forecasts alone do not prove occurrence.

**SPECIFICATION REQUIREMENT:** v1.5's technical design describes source ID, source/retrieval timestamps and content hash; the specification requires source/as-of evidence and freezes source hashes in Final. **UNAVAILABLE:** The repository does not prescribe a canonical proof format, provider fallback, provider-specific timestamp semantics or a common cross-source cutoff, and it does not show that any candidate provider exposes the complete approved evidence set. Each source contract must establish that before a snapshot is treated as verified.

## Task 17 evidence-backed alternatives and current unresolved decisions

The historic alternatives in the Task 17 table are grounded in v1.5's generic distinction between source/as-of time, retrieval time, source identity and immutable snapshots. They were **ARENA RECOMMENDATIONS / design alternatives**, not evidence that any provider emits such records. No provider behavior or external market source was verified in that repository investigation. Task 18 approved policy directions, but source-specific decisions remain:

1. **Subscription — UNRESOLVED:** approved source; exact final-record event identity and source-native as-of semantics; publication behavior; source-specific cutoff and its relation to evaluation time; and absent/unavailable-record handling.
2. **Market — UNRESOLVED:** approved source and, metric by metric, whether an actual session close or a separately approved point-in-time rule applies; the session/observation identity and cutoff; and non-trading/unavailable handling.
3. **GMP — PARTIALLY RESOLVED BY A9:** An absent or invalid required qualifying GMP snapshot or required hash blocks `FINAL`; a blocked-input marker does not qualify. **UNRESOLVED:** Approved source, qualifying observation, event/as-of and timestamp semantics, source-specific cutoff, snapshot/hash representation, and stale/unverifiable handling beyond A9.
4. **Peers — UNRESOLVED:** approved source, named actual session, observation cutoff, and reproducible peer-universe snapshot rule. Do not finalize peer eligibility or production scoring before A5 is resolved.
5. **Common evidence — UNRESOLVED:** the source-specific evidence contract must establish original-timezone/offset capture, UTC normalization, event occurrence, publication/retrieval separation and required hashes. Do not presume a shared cutoff or fallback.

**A5 BLOCK —** The Task 14 determination remains `CALIBRATION_EVIDENCE_INSUFFICIENT`. No numerical peer freshness or minimum listing-history parameter has been approved; the legacy v1.4 30-day value is not adopted. Appropriate evidence and parameter approval are required before peer eligibility or production peer scoring.

## Rationale and consequences

The v1.5 contract requires immutable, reproducible snapshots, while its artifacts and the inspected repository do not establish provider-specific events or cutoffs. Ramki's approved directions constrain policy without converting scheduled milestones into completed events, substituting publication/retrieval time for event time, or inventing freshness intervals.

**Restriction:** The policy directions do not complete the four source-specific contracts. They must not be used to claim that a provider-backed Final snapshot is verified or to finalize peer eligibility. A9 resolves only the missing/invalid required qualifying GMP snapshot/hash Final consequence; GMP source-specific contracts remain open. A5 continues to block peer freshness/listing-history parameters and production peer scoring. This governance record does not change the v1.5 specification, configuration, source integrations or evaluation behavior.

## Unresolved dependencies

- Subscription source, actual final-record event/as-of semantics, publication behavior, cutoff and missing-record handling.
- Market source and metric-specific session/point-in-time rule, cutoff and non-trading/unavailable handling.
- GMP source, qualifying-observation/event/as-of/timestamp/cutoff contract, snapshot/hash representation and stale/unverifiable handling beyond A9. A9 has resolved the missing/invalid required qualifying snapshot/hash Final consequence.
- Peer source, named session, observation cutoff and peer-universe snapshot rule; A5 evidence and parameter approval before eligibility/scoring.
- A source-specific canonical evidence contract for event occurrence, original timezone/offset and UTC timestamps, publication/retrieval times, cutoffs/evaluation time and required hashes.

## Implementation authority

**Not granted.** Phase 1 remains unauthorized.
