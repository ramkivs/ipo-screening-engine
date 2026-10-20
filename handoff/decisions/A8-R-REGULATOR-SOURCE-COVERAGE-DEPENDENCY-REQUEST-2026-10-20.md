# A8-R — Regulator-Source Coverage Dependency Request (for a verified absence of SEBI/ED action)

- **Record ID:** A8-R-REGULATOR-SOURCE-COVERAGE-2026-10-20
- **Record type:** **DEPENDENCY REQUEST — open question posed to the A8 decision set.** Not a decision, not an approval, not implementation authority (CONVENTION rules 4 and 6).
- **Status:** **UNRESOLVED / AWAITING RAMKI DECISION.** Filed 2026-10-20 as the A8 dependency identified by `handoff/decisions/A25-sebi-ed-absence-source-coverage-standard.md` §6. A25's D1/D2 were approved and implemented the same day (`41f2f86`), which supplies R-S6's *in-document* half; nothing in this request is thereby decided — see §5.
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

## 5. What the A25 implementation changed for this request, and what it did not

| This request's need | State after A25-D1/D2 (`41f2f86`) | Still open |
| --- | --- | --- |
| Distinguish "we did not look" from "we looked and found nothing" **inside the filing** | `SectionExtractor.page_status` / `pages_read()` and the located-vs-fallback window flag; an absence is emitted only on a located, completely-read window | the same distinction for **external** sources: there is no regulator-source retrieval at all, so an external negative has no representation to attach it to |
| A `false` that cannot be over-read | the emitted record says "absence of disclosure, not verified absence" and names its search basis | any wording that could legitimately say "verified" — which is precisely what R-S1 must decide is possible, if anything is |
| A precedent for provider outcome states | unchanged: `issue_terms.py` remains the only code in the repository that separates `FOUND` / `NOT_FOUND` / `UNAVAILABLE` / `REJECTED`, with `listing_searched` required before a `NOT_FOUND` is trusted | whether a regulator-source check may reuse that machinery, or must have its own (R-S2) |
| K2's handling of missing evidence | unchanged: absent field ⇒ UNKNOWN ⇒ `UNVERIFIED`, `critical_data` ⇒ `INSUFFICIENT_DATA` | whether an externally corroborated negative should clear K2 differently (R-S9) |

## 6. Acceptance tests and outcome states a decision must define (none is implemented)

Each provision is testable; a decision that cannot state the failure case is not a decision.
The states below reuse the repository's existing vocabulary (`FOUND` / `NOT_FOUND` /
`UNAVAILABLE` / `REJECTED`, `FreshnessStatus`, `ResolutionOutcome.status`) — no new state
name is proposed here, because that would be a taxonomy change.

| Provision | Test that must pass | Outcome states the test pins |
| --- | --- | --- |
| R-S1 authority | a `false` derived *only* from an external source is rejected unless the approved authority set covers that source | `false` allowed / `false` refused → field absent |
| R-S2 discovery, identity | a query whose response is an index page, a homepage, a JavaScript shell, or a different registration number, yields no negative | `FOUND`, `NOT_FOUND` (only with a named, read listing), `UNAVAILABLE`, `REJECTED` |
| R-S3 party matching | an enforcement record naming a similarly-named entity that is not the issuer neither condemns nor clears | match / no-match / **identity-unverified ⇒ no conclusion** |
| R-S4 index completeness | a negative from a source whose coverage of the period is not established cannot clear the flag | covered / coverage-unestablished ⇒ `UNAVAILABLE`-class refusal |
| R-S5 event and cutoff | an action that closed before the cutoff, and one opened after it, are both excluded from "active at the cutoff"; observation time ≠ event time ≠ retrieval time | active-at-cutoff / closed-before / opened-after / indeterminate |
| R-S6 failure vs genuine negative | a timeout, a 5xx, an empty result set and a genuinely empty register are four different outcomes, and only the last is a negative | `UNAVAILABLE` vs `NOT_FOUND` vs `PARTIAL` vs `STALE` |
| R-S7 partial / inaccessible | a partially retrieved register is never a negative; a `REJECTED` (paywalled, blocked) is never a negative | complete / partial / rejected |
| R-S8 conflict | issuer denial + a located adverse order ⇒ `CONFLICT` ⇒ UNKNOWN, not the favourable value and not the adverse one unless the order is identity-verified | agree / conflict / unverifiable |
| R-S9 K2 | whichever negative is admitted, K2 must be able to say *which* basis cleared it; today `UNVERIFIED` on absence is unchanged | CLEAR only on the approved basis, TRIGGERED on a verified action, `UNVERIFIED` otherwise |
| R-S10 currency | a negative older than the approved window is `STALE` and yields no clearance | fresh / stale / unknown-as-of |

## 7. Does K2 need a new field? The question, posed precisely

K2 currently consumes exactly two required inputs (`governance.sebi_ed_action_active` plus
its companion), and its three-state semantics do not record *why* a limb cleared. If
external corroboration were ever admitted, `true`/`false` would no longer be enough to
explain a `CLEAR`, and a coverage/basis field would be needed — which is a schema and
record-format change, not an extraction change, and is the reason A25's approved work
expressed the new states in the evidence **notes** instead. Three facts are settled, so
the question is narrower than it looks:

1. No field is needed for what is implemented today: an issuer denial is already
   distinguishable, in the record's notes, from an unsearched section (absence of the
   field ⇒ `UNVERIFIED`).
2. A field **would** be needed for R-S1..R-S10, because `false` would then carry two
   different evidentiary weights (issuer-authored vs externally corroborated) that a
   boolean cannot hold.
3. Adding one is not within A8-R's subject: it needs Ramki's approval of a schema change,
   a config version decision, and re-baselining of stored records' validity — the same
   class of change costed in A26 §4 for the fourth bucket. Arena recommends the field be
   decided **after** R-S1, not before, so it is designed around an authority set rather
   than guessed at.

## 8. Bounded investigation actually performed (2026-10-20)

Real A8 artifacts read, in full or in the relevant sections: `A8-final-snapshot-event-cutoffs-investigation.md`
(policy directions recorded; source/provider/event/cutoff contracts left open; implementation authority
withheld), `A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md` (scope: a required
`market.regime.nifty_trend` input "only"; it states it does not decide any other metric),
`A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`, `A8-M-ARENA-HANDOFF-2026-10-13.md`,
`A9-missing-gmp-final-fail-closed.md`, `A17`, `A18-gmp-evidence-linkage-contract.md` (retention layers L1–L2,
cited by R-S7), `A23` §6A.2, `A24` and `A25` in full. Code inspected: `issue_terms.py` (the `OFFICIAL_HOSTS`
allow-list, the four provider outcomes, the `listing_searched` rule and its 2026-10-18 failure note, response
identity fingerprints), `connectors/interfaces.py` and `connectors/coordinator.py` (snapshot ingestion only —
no fetch path exists), `config/ipo-config.v1.5.0.json` and `v1.6.0.json` (K2's `required` list and
`critical_data`, identical in both), `extraction/sections.py`, `extraction/toc.py`, `schema/ipo-input.v1.5.schema.json`.
**No A8 text authorises regulator-source retrieval, and none was built or is proposed as built.**
