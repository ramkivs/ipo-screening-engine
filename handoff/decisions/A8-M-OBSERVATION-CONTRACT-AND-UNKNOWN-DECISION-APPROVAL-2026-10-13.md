# A8-M — Observation Contract and UNKNOWN/Final Eligibility

- **Decision ID:** A8-M-OBSERVATION-CONTRACT-2026-10-13
- **Decision status:** USER-APPROVED POLICY; SOURCE-NATIVE EVIDENCE QUALIFICATION AND DETERMINISTIC FRESHNESS PREREQUISITE OPEN
- **Decision authority:** RAMKI, as established by `handoff/decisions/A1-evidence-adjudication-authority.md`
- **Approval provenance:** The user explicitly reviewed and approved the policy in the task instruction received **2026-10-13 (Asia/Calcutta)**. No separate approval time is asserted.
- **Decision date:** 2026-10-13 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** `arena/4e1080b7-ipo-screening-engine`, `6a6c8f2caf3a116f3af45b0a646949b92c4f5aeb`
- **Scope:** Observation, source, cutoff, session-aware freshness, provenance, UNKNOWN semantics, and Final eligibility for a required `market.regime.nifty_trend` input only.
- **Implementation authority:** NOT GRANTED. This record does not authorize runtime, schema, adapter, configuration, scoring, release, or production changes.

## 1. Approved metric and source class

`market.regime.nifty_trend` is the session-close-derived classification of the **NSE NIFTY 50 PRICE INDEX**. It is not a live/PIT market-sentiment estimate. Use an authoritative NSE-published close for a named, completed NSE trading session, together with the SMA-50/SMA-200 rule approved in `handoff/decisions/A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`.

This approves the required source class and evidence standard; it does **not** automatically qualify every NSE URL, rendered page, local capture, parsed file, or hash. The particular record must establish the index identity, session, closing value, source identity/provenance, and source-native event/session semantics. Prefer a retrievable source-native record or exact provider bytes. If only a rendered/local capture exists, it remains descriptive and unqualified unless a separate explicit source-qualification decision accepts that evidence form. A local-capture hash identifies only those local bytes, never provider response bytes.

If the evidence cannot distinguish the official NIFTY 50 **price-index** session close from a live quote, revised value without evidenced precedence, partial session, or total-return index, it is not qualifying evidence and the trend is UNKNOWN.

## 2. Evaluation cutoff and session selection

Every evaluation must record an explicit cutoff timestamp with timezone/UTC offset (UTC is acceptable when explicitly marked). Select the latest qualifying completed NSE trading-session close demonstrably available by that cutoff. Do not use a future-session or partial-session value. Do not select a record whose availability before the cutoff cannot be established.

Preserve, separately whenever available:

- Session date and event/session identity.
- Source-native event/session timestamp and its original timezone/UTC offset.
- Publication/availability time.
- Retrieval time.
- Evaluation cutoff and its timezone/UTC offset.

Retrieval time is not event time or evidence of publication/availability. If multiple records conflict for the same index/session, apply source-defined revision precedence only when the source evidence establishes it; otherwise the trend is UNKNOWN.

## 3. Session-aware freshness policy and open prerequisite

The generic v1.5 `market_staleness_hours: 24` elapsed-time default is **not** the governing freshness rule for this session-close metric. Freshness must account for NSE trading sessions, weekends, exchange holidays, special sessions, source-close publication/availability, the evaluation cutoff, future/impossible timestamps, and missing or unresolved timezone information.

A previous close may remain eligible outside market hours, on weekends, and on holidays only while it remains the latest qualifying completed session and no newer close should have been available by the cutoff. After a new session has completed, do not keep using the prior close merely because a generic elapsed-time threshold has not expired. If publication timing is unresolved, fail closed unless an explicitly permitted previous-close rule is evidenced and recorded.

**No numeric publication-delay allowance is approved or may be invented.** A deterministic, testable session-calendar/publication-availability rule must be supported by source evidence before production qualification. This is an open prerequisite, not implementation authorization.

## 4. Missing, invalid, stale, unqualified, or conflicting inputs

If a required close, SMA window, session, timestamp, source identity, availability-by-cutoff fact, freshness condition, or conflict resolution is missing, invalid, insufficient, stale under the approved session-aware policy, conflicting without evidenced precedence, or unqualified, `nifty_trend` is **UNKNOWN**. Preserve the specific reason.

Do not substitute zero, `neutral`, a previous category, an unqualified source, an incomplete window, or a convenient conflicting value. Do not silently skip an expected missing or invalid session close in either SMA window. Required closes include the evaluated session; if the expected sequence or its completeness cannot be established, return UNKNOWN.

## 5. Provenance retained

Retain the following as available for each evaluated trend:

- Provider/source identity and source location/reference.
- Index identity, session date, and close value.
- Source-native event/session timestamp and timezone/offset.
- Publication/availability time and retrieval time as distinct values.
- Evaluation cutoff and timezone/offset.
- Source record identifier or exact source bytes.
- Hash algorithm, digest, and the exact object hashed.
- SMA input session range and observation count for each window.
- Calculation method and SMA-50/SMA-200 results.
- Qualification status and the precise rejection/UNKNOWN reason.

Explicitly record when provider-native bytes, source-native timestamps, or availability-before-cutoff evidence are unavailable. Do not silently promote a local rendered capture to provider-authenticated evidence.

## 6. Approved UNKNOWN-to-Final consequence

If NIFTY trend is UNKNOWN and is required by the active IPO evaluation:

1. **Do not issue a Final disposition.** Return an explicit non-final/incomplete status.
2. Identify the missing, invalid, conflicting, stale, or unqualified NIFTY market-regime input and its reason.
3. Do not convert UNKNOWN to zero, neutral, a previous category, or another source.
4. Preserve score-range/completeness information for diagnostics only; that diagnostic range does not override the Final block.
5. Final may be reconsidered only after qualifying evidence is available and the evaluation is rerun under the documented rules.

This decision applies **only** to required NIFTY trend. It does not decide UNKNOWN/Final consequences for India VIX, recent IPO listing gains, subscription, GMP, or any other metric; those remain subject to separate contracts and explicit decisions.

## 7. Existing evidence limits and qualification status

`evidence/market-observations/official-index-history-20261013/A8-M-SMA-EVIDENCE-20261013.md` records 245 historical NIFTY 50 closes through 2026-10-08, with latest reported SMA-50 **23,761.064** and SMA-200 **24,282.7665**. The retained rendered captures do not provide original provider response bytes, exact provider headers/receipt times, or source-native availability times. Their local hashes are not provider-byte hashes. These records remain descriptive/unqualified for the approved Final contract unless accepted by a separate source-qualification decision. The historical averages do not establish a qualifying close/cutoff or a current trend category; none is assigned here.

The VNL observation package separately records secondary-source IPO listing prices and unqualified VIX observations. Those metrics are not inputs to NIFTY trend and are not qualified or redefined by this decision.

## 8. Status and authority boundary

- NIFTY classification semantics, observation policy, and required-NIFTY UNKNOWN-to-Final block: **APPROVED**.
- Source-native evidence qualification: **OPEN**.
- Deterministic session-calendar/publication-availability rule: **OPEN PREREQUISITE**.
- **A8-M: OPEN. Phase 0: OPEN. Phase 1: UNAUTHORIZED.**
- Implementation authority: **NOT GRANTED**.
- Release authority: **NOT GRANTED**.
- Production activation: **NOT AUTHORIZED**.

This is a durable policy decision, not a claim that the source data or implementation prerequisites are complete. It does not amend v1.5, qualify the existing captures, or authorize runtime behavior changes.
