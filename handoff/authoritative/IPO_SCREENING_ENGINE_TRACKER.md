# IPO Screening Engine — Project Tracker

- **Tracker status:** OPEN / PENDING / BLOCKED / DEFERRED / RECHECK; this is a work tracker, not an approval or implementation grant.
- **Updated:** 2026-10-13 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Delivery branch:** `arena/4e1080b7-ipo-screening-engine`
- **Authority:** Decisions are governed by the individual records in `handoff/decisions/`.

## Tracker provenance

A repository-wide search of the current checkout and the two inspected Arena task branches found no existing project tracker file. The `IPO_SCREENING_ENGINE_TRACKER.md` Library reference was not present in the accessible workspace. This file is a **repository-durable reconstruction** from the user-approved 2026-10-13 task and existing repository decision records; it is not claimed to be copied from or to verify an inaccessible Library artifact. It adds the A8-M status below and does not replace unrelated decision records or assert that unprovided Library rows were reviewed.

## A8-M — NIFTY trend

| Work item | Status | Current state / next evidence or gate |
|---|---|---|
| NIFTY trend meaning and classification | **APPROVED** | Session-close-derived NIFTY 50 PRICE INDEX; strict comparison with trailing SMA-50 and SMA-200; mixed/equal valid signals are neutral; incomplete/invalid qualifying windows are UNKNOWN. See `handoff/decisions/A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`. No current category is assigned. |
| Observation, cutoff and provenance policy | **APPROVED** | Explicit cutoff; latest qualifying completed official NSE close demonstrably available by cutoff; event/session, publication/availability, retrieval and evaluation timestamps remain distinct; complete, valid session windows; no unqualified fallback. See `handoff/decisions/A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`. |
| Required NIFTY UNKNOWN → Final eligibility | **APPROVED** | If NIFTY trend is required and UNKNOWN, withhold Final, return non-final/incomplete, identify the input/reason, and keep score range/completeness diagnostic only. Does not set Final policy for other metrics. |
| Source-native evidence qualification | **OPEN / BLOCKED** | Existing NSE history/SMA package is descriptive rendered/local evidence through 2026-10-08; latest reported SMA-50/SMA-200 are 23,761.064 / 24,282.7665. Exact provider bytes and availability-before-cutoff evidence are unavailable. Qualify an authoritative NSE price-index record, source-native session/close semantics, provenance and availability before using it for Final. Do not assign a category from these historical averages alone. |
| Deterministic session calendar/publication-availability rule | **OPEN PREREQUISITE** | Support a deterministic, testable rule with NSE session/special-session and source-availability evidence. Cover cutoff, weekends, holidays, special sessions, future/impossible times and unresolved timezone. No numeric publication-delay allowance is authorized. |
| A8-M | **OPEN** | Policy is approved; source-native qualification and the deterministic freshness prerequisite remain open. No current trend category/score or production-ready metric is established. |
| Phase 0 | **OPEN** | Other Phase 0 contracts and the A8-M evidence/availability prerequisites remain outstanding. |
| Phase 1 | **UNAUTHORIZED** | No implementation work is authorized. |
| Implementation / release / production activation | **NOT GRANTED / NOT AUTHORIZED** | No runtime, configuration, scoring, schema or release changes are authorized by the A8-M policy publication. |

## Deferred and recheck boundaries

- **DEFERRED / OUT OF SCOPE:** Do not combine NIFTY trend with India VIX, recent IPO listing gains, subscription, GMP or other metrics. Their source, semantics, freshness and Final consequences remain separate contracts.
- **RECHECK:** After source-native evidence and the session-calendar/publication-availability rule are evidenced, confirm the cutoff-qualified close and complete SMA input windows; only then reevaluate the metric and, if appropriate, rerun the evaluation. A missing or unqualified input remains UNKNOWN and blocks Final when NIFTY trend is required.

## Other open work retained by reference

This A8-M update closes no unrelated work and removes no other tracker item. Existing decision records remain authoritative, including:

- A5 peer calibration/eligibility remains blocked (`handoff/decisions/CONVENTION.md`; see also `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md`).
- A8-S subscription source/event/cutoff details remain open (`handoff/decisions/A10-interim-subscription-handling.md`).
- A8-G GMP source/evidence contract remains open; the distinct missing-required-GMP Final rule remains governed by A9 (`handoff/decisions/A9-missing-gmp-final-fail-closed.md`).
- A8-P peer source/session/universe details remain open, with A5 prerequisites still in force (`handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md`).

No item for VIX, listing gains, subscription or GMP is reclassified by the NIFTY-only UNKNOWN/Final decision.
