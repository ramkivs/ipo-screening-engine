# A8-M — Arena Handoff (2026-10-13)

**Handoff status:** Approved policy and UNKNOWN/Final decisions recorded; source-native qualification and deterministic session-aware freshness prerequisite remain open. **A8-M OPEN; Phase 0 OPEN; Phase 1 UNAUTHORIZED.**

## Approved scope

The user approved, on 2026-10-13 (Asia/Calcutta):

- `market.regime.nifty_trend` as a NIFTY 50 **price-index**, completed-session-close-derived metric.
- The strict close-vs-SMA-50/SMA-200 categories (`supportive` above both, `weak` below both, `neutral` for all other valid cases) and UNKNOWN for incomplete or invalid windows.
- The per-evaluation cutoff, latest demonstrably available completed close, evidence-preserving timestamp/provenance requirements, and session-aware freshness direction; no invented numeric publication-delay allowance.
- The rule that UNKNOWN blocks Final **only when NIFTY trend is required**; score-range/completeness remains diagnostic and cannot override that block.
- Separation of NIFTY trend from VIX, listing gains, subscription, GMP and other metrics.

The durable decision texts are `handoff/decisions/A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md` and `handoff/decisions/A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`.

## Publication and reconciliation scope

This handoff is part of the additive repository documentation update with the two decision records, an addendum to `handoff/investigation/A8-M-DECISION-INPUT-RECONCILIATION-2026-10-13.md`, and the A8-M tracker status. The earlier investigation and evidence remain historical; prior `UNRESOLVED` statements about the NIFTY rule/required-NIFTY Final consequence are superseded by the approvals, while the evidence-quality and implementation prerequisites remain open.

No matching project tracker file was found in the accessible repository/workspace or on either inspected Arena branch. The named Library tracker was not available in the checkout. `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` is therefore a repository-durable reconstruction from the user-approved instruction and existing repository decisions, **not a copy or verification of an inaccessible Library artifact**. Existing unrelated open decision records are retained and remain authoritative for their own scope.

## Remaining source qualification work

The existing NIFTY package documents 245 closes through 2026-10-08 and descriptive SMA-50/SMA-200 values. Its rendered/local captures do not establish original provider bytes, exact retrieval/availability times, or provider response headers. They remain descriptive/unqualified for Final under the approved contract unless a separate evidence-form qualification decision accepts them. Do not calculate or publish a category from these values alone.

Before any NIFTY snapshot can qualify, retain an authoritative NSE-published price-index record that establishes the index, session, official close, source-native event semantics, provenance, and availability by the explicit evaluation cutoff. Retain a complete expected-session series for both SMA windows; conflicts require evidenced source-defined revision precedence.

## Deterministic freshness prerequisite

A deterministic, testable session-calendar/publication-availability rule must be supported by source evidence before production qualification. It must cover weekends, exchange holidays, special sessions, when an official close should have been available, cutoff comparison, future/impossible timestamps, and unresolved timezone information. Do not invent a numeric publication-delay allowance. Fail closed when availability cannot be demonstrated, subject only to an explicitly evidenced and recorded permitted previous-close rule.

This is an open evidence/contract prerequisite, not authority to implement it. The generic 24-hour elapsed-time default is not the approved rule.

## Authority boundaries

- No runtime, adapter, configuration, scoring, schema, fixture, or test behavior was authorized or changed by these decisions.
- The legacy v1.5 score map and aliases are not newly approved as scoring policy.
- VIX and recent IPO listing-gain meanings/Final consequences remain separate and unresolved under their own contracts.
- **Implementation authority: NOT GRANTED. Release authority: NOT GRANTED. Production activation: NOT AUTHORIZED.**
- **A8-M: OPEN. Phase 0: OPEN. Phase 1: UNAUTHORIZED.**

The repository commit and fetched task-branch ref are the durable publication proof; the execution report identifies their exact commit/ref so this handoff need not contain a self-referential commit hash.
