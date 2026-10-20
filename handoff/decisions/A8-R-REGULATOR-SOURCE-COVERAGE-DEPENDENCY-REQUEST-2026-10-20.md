# A8-R — Regulator-Source Coverage Dependency Request (for a verified absence of SEBI/ED action)

- **Record ID:** A8-R-REGULATOR-SOURCE-COVERAGE-2026-10-20
- **Record type:** **DEPENDENCY REQUEST — open question posed to the A8 decision set.** Not a decision, not an approval, not implementation authority (CONVENTION rules 4 and 6).
- **Status:** **UNRESOLVED / AWAITING RAMKI DECISION.** Filed 2026-10-20 as the A8 dependency identified by `handoff/decisions/A25-sebi-ed-absence-source-coverage-standard.md` §6.
- **Raised against:** `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` (status: policy directions recorded; **source/provider/event/cutoff contracts OPEN**; implementation authority not granted) and the A8-M approvals of 2026-10-13.
- **Does not amend:** A8-M's approved NIFTY scope (which explicitly excludes other metrics), A9/A17/A18 GMP rules, K2, or any schema/config/scoring artefact.

## 1. Why this request exists

A25 asks when the engine may report that no SEBI/ED action is active. A8 was inspected directly for this purpose, and the result is negative and specific: **the A8 material contains no source contract for regulator enforcement information at all.**

* `A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md` — Scope: "for a required `market.regime.nifty_trend` input **only**"; §6: "does not decide UNKNOWN/Final consequences for … **any other metric**".
* `A8-final-snapshot-event-cutoffs-investigation.md` — covers A8-S subscription, A8-M market, A8-G GMP, A8-P peers; its own Unresolved-dependencies list still includes the canonical evidence contract for event occurrence, timestamps, publication/retrieval times, cutoffs and hashes.
* Even for NIFTY, source-native evidence qualification is **OPEN** and the retained captures are recorded as unqualified ("a local-capture hash identifies only those local bytes, never provider response bytes").

So the proposal that an *external* check could upgrade a regulatory absence has no contractual basis to stand on. Rather than invent one, this request lists the provisions that would have to be decided.

## 2. Provisions requested (one decision each; nothing here is assumed answered)

1. **R-S1 Authority set for absence.** Which sources, if any, are authoritative for concluding that no SEBI/ED action is active — SEBI's enforcement/order pages, the whole-of-India register, MHA/ED communication, exchange disciplinary pages — and whether *absence from any of them* may ever be treated as evidence rather than as a coverage gap.
2. **R-S2 Discovery and retrieval contract.** Host allow-list and URL/registration discipline (the repository already constrains `issue_terms.py` to `OFFICIAL_HOSTS`, `sebi.gov.in` included), sandbox/production egress assumptions, and what counts as a *usable* response — with the `issue_terms` rule as precedent: an HTTP 200 that is a homepage or a JavaScript shell is `UNAVAILABLE`, never `NOT_FOUND`.
3. **R-S3 Issuer/party matching.** How an enforcement record is matched to the evaluated issuer and to its promoters/directors (entity-name normalisation, aliases, "excluding promoters" scoping), and the rule that a name match without identity verification supports neither presence nor absence.
4. **R-S4 Completeness of the searched index.** What evidence establishes that the searched source covers the relevant population and period, so that a negative result is a *finding* and not an artefact of the index. A25 §3.4 shows the repository already refuses bare negatives for issue terms ("a bare flag is not enough; the report has to name a listing that really was read").
5. **R-S5 Event and cutoff semantics.** What "active" means at what instant (evaluation cutoff vs record status date), with event/observation time kept distinct from retrieval time as A8-M §2 requires, and no invented publication-delay allowance.
6. **R-S6 Failure, partial and stale handling.** Mapped to the existing `UNAVAILABLE` / `PARTIAL` / `UNVERIFIED` / `STALE` vocabulary and never to a boolean; retries so a transient failure is not converted into a permanent negative.
7. **R-S7 Retention and provenance.** Capture bytes, per-source attempt records, hashes labelled by what they actually hash (`LOCAL_COMPUTED` vs provider bytes), following A18 L1–L2 — no new fields or schema versions unless Ramki approves them.
8. **R-S8 Conflict rule.** Issuer denial versus a located order, and unresolved conflict ⇒ UNKNOWN, mirroring `ResolutionOutcome.status = CONFLICT`.
9. **R-S9 Consequence for K2.** Whether an externally corroborated negative may clear K2 differently from an issuer-only negative, and whether K2's `required` list grows a coverage field. This is a knockout/scoring decision and must be recorded as one.
10. **R-S10 Currency window.** A defined freshness/staleness rule for a negative claim (the ICDR disclosure window is "last five years"; whether that or something else governs the external check is a decision, not a default to copy).

## 3. Interim consequences while this request is open

* A25's Option 2 standard (issuer-authored denial, gated) is the strongest available basis for `false`; nothing in the repository may describe that `false` as externally verified.
* `True` continues to require disclosed adverse action; absence of a search match continues to mean **absent field ⇒ UNKNOWN ⇒ K2 `UNVERIFIED`**, and `config.critical_data` continues to yield `INSUFFICIENT_DATA`.
* No connector, host, provider, cache or retrieval implementation is authorised by this request; `SourceClass` gains nothing; the `connectors` coordinator continues to ingest supplied snapshots only.

## 4. Evidence base (all read on 2026-10-20, no assumption beyond it)

`handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md`; `A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`; `A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`; `A8-M-ARENA-HANDOFF-2026-10-13.md`; `A9-missing-gmp-final-fail-closed.md`, `A17`, `A18-gmp-evidence-linkage-contract.md` (approved evidence-linkage shape); `engine/ipo_screening/issue_terms.py` (allow-list, provider outcomes, listing-searched evidence rule, status vocabulary); `engine/ipo_screening/connectors/interfaces.py`, `coordinator.py`; `engine/ipo_screening/extraction/sections.py:112-123,2566-2567`; `engine/ipo_screening/extraction/toc.py:121-138`; `config/ipo-config.v1.5.0.json` (K2, `critical_data`).
