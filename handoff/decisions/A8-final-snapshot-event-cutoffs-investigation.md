# A8 — Final Snapshot Event and Cutoff Investigation

- **Decision ID:** A8
- **Title:** Source-specific actual-event and cutoff requirements for Final snapshots
- **Status:** INVESTIGATION COMPLETE; SOURCE/EVENT/CUTOFF DECISIONS OPEN
- **Decision authority:** RAMKI for unresolved A8 selections (A1 designates RAMKI as conflict-adjudication authority; this investigation does not adjudicate source conflicts).
- **Decision date:** Not applicable—no A8 event/cutoff has been selected. **Investigation date:** 2026-10-09 (Asia/Calcutta).
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/4e1080b7-ipo-screening-engine`, pre-record commit `01ba66c12ca1195fd7acbd287c3e39a019808094`
- **Scope:** Read-only reconciliation of v1.5 requirements, repository-documented source behavior and candidate A8 decisions for subscription, market, GMP and peer valuation snapshots.
- **Implementation authority:** NOT GRANTED. This record does not authorize provider configuration, application implementation or Phase 1.

## Explicit A8 principles

Ramki has approved the requirement that Final snapshots use source-specific actual events and cutoffs; evidence must establish event occurrence; original timestamps and timezone/offset information must be preserved alongside normalized UTC timestamps; scheduled events are not completed events; and no freshness interval or cutoff may be invented.

This record does **not** select a provider, event, cutoff, freshness interval or missing-snapshot outcome.

## Authoritative requirements inspected

- `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §§4.5–4.6: peer listing date, price date and source; timestamp, timezone, source and source timestamp where available for market values.
- Specification §§9, 13, 19–21: stale-peer treatment and valuation ranges; timestamped, source-backed market snapshots; Final on/after closing freezes subscription, market, GMP and peer valuation snapshots, configuration version and source hashes; peer validation includes listing age, business comparability, stale date and source.
- `handoff/authoritative/IPO_Screening_Engine_Technical_Design_v1.5.md` §§3.1 and 10–14: generic source adapters; source ID, retrieval timestamp, source timestamp, content hash, source type and URI/file reference; peer listing/valuation dates and source; immutable snapshots and records.
- `handoff/authoritative/ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md` §§10, 12 and 15: configured peer freshness, timestamp validation, provenance requirements, and a relevant Day-3/closing snapshot.
- `handoff/authoritative/ARENA_IPO_Screening_Artifact_Manifest_v1.5.md`: the v1.5 specification is authoritative; the technical design is target architecture; legacy assets are references.

These requirements establish what must be captured, but not the source-specific actual event or cutoff for any of the four snapshots.

## Source-by-source findings and decision package

| Snapshot | Explicit requirements | Existing source/provider behavior supported by repository evidence | Candidate event/cutoff definitions for Ramki (unapproved) | Decisions still required |
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

The artifacts distinguish source time from retrieval time and require source identifiers and hashes in the technical design. Ramki's A8 direction additionally requires preservation of each original timestamp and timezone/offset plus a UTC-normalized timestamp. The following are candidate evidence elements for an approved source contract—not a claim that current providers supply them:

- source identity/reference and immutable snapshot or document;
- the observation's as-of/event timestamp in its original form and timezone/offset;
- source publication timestamp, if distinct and available;
- retrieval timestamp, recorded separately from the observation time;
- content hash and a record linking the snapshot to the IPO/evaluation cutoff;
- evidence that the actual event/observation occurred, rather than a scheduled date or forecast.

The repository defines no event-occurrence proof format, source freshness window, provider fallback rule or common cross-source cutoff. The four sources must not be forced to share one timestamp rule.

## Evidence-backed alternatives and unresolved Ramki decisions

The alternatives in the table are grounded in the documented distinction between source/as-of time, retrieval time, source identity and immutable snapshots. They are **design alternatives**, not evidence that any particular provider currently emits such records. No provider behavior or external market source was verified in this repository investigation.

Ramki must decide, independently for each snapshot:

1. approved source/provider or source class;
2. actual event/observation that qualifies;
3. which time is the effective as-of/cutoff when event time and publication time differ;
4. how original timezone/offset and UTC are stored and checked;
5. evidence sufficient to prove event occurrence;
6. whether an unavailable required snapshot blocks Final or is retained as missing under the approved completeness/range rules;
7. whether the snapshot cutoff is shared or source-specific (no shared cutoff is presumed).

For peers, A5 must also be resolved before freshness-based eligibility can be determined. The Task 14 classification remains `CALIBRATION_EVIDENCE_INSUFFICIENT`; no numeric freshness or listing-history parameter is approved, and the legacy v1.4 30-day value is not adopted.

## Rationale and consequences

The v1.5 contract requires immutable, reproducible snapshots, while the current artifacts leave the actual source event and cutoff unspecified. Recording observation, publication and retrieval times separately allows Ramki to choose a defensible event without converting scheduled milestones into completed events or inventing freshness intervals.

Until the choices above are approved, this investigation must not be used to accept a Final snapshot or enable peer scoring. It does not change the v1.5 specification, configuration, source integrations or evaluation behavior.

## Unresolved dependencies

- Ramki's source/provider, event, cutoff and unavailable-snapshot decisions for each of the four snapshots.
- The A5 peer freshness and listing-history parameters and eligible-set policy.
- The Phase 0 canonical record representation for source timestamps, timezone/offset, UTC normalization and event-occurrence evidence.

## Implementation authority

**Not granted.** Phase 1 remains unauthorized.
