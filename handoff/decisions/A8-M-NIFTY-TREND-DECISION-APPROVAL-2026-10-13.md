# A8-M — NIFTY 50 Price-Index Trend Classification

- **Decision ID:** A8-M-TREND-2026-10-13
- **Decision status:** USER-APPROVED POLICY
- **Decision authority:** RAMKI, as established by `handoff/decisions/A1-evidence-adjudication-authority.md`
- **Approval provenance:** The user explicitly approved the rule in the task instruction received **2026-10-13 (Asia/Calcutta)**. No separate approval time is asserted.
- **Decision date:** 2026-10-13 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** `arena/4e1080b7-ipo-screening-engine`, `6a6c8f2caf3a116f3af45b0a646949b92c4f5aeb`
- **Scope:** Meaning and classification rule for `market.regime.nifty_trend`.
- **Implementation authority:** NOT GRANTED. This policy does not authorize engine, schema, adapter, configuration, scoring, release, or production changes.

## Approved decision

`market.regime.nifty_trend` means the **session-close-derived trend of the NIFTY 50 PRICE INDEX**. It is not a live or point-in-time sentiment estimate. Use the official close of the qualifying completed NSE session and the corresponding trailing simple moving averages.

For evaluation session `t`, calculate SMA-50 and SMA-200 as the arithmetic means of, respectively, the most recent **50** and **200** valid completed NSE trading-session closes, including session `t`:

`SMA_n(t) = mean(C(t), C(t-1), ..., C(t-(n-1)))`

where the sequence contains the most recent qualifying completed trading sessions, not calendar days. The window must be complete and valid. Do not use future-session or partial-session values. Do not silently skip an expected missing or invalid close. If the session sequence, evaluation close, or either moving average cannot be established, the result is **UNKNOWN**.

| Category | Approved condition, with valid complete inputs |
|---|---|
| `supportive` | `close(t) > SMA-50(t)` **and** `close(t) > SMA-200(t)` |
| `weak` | `close(t) < SMA-50(t)` **and** `close(t) < SMA-200(t)` |
| `neutral` | Every other valid case, including mixed signals and equality with either moving average |
| `UNKNOWN` | Required close or either SMA cannot be calculated from a complete, valid, qualifying series |

Invalid, unqualified, partial, future, stale-under-the-approved-session-policy, or unresolved conflicting observations do not become `neutral`; they yield UNKNOWN with the reason preserved. Source, cutoff, availability, freshness and provenance requirements are specified in `handoff/decisions/A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`.

## Metric separation and legacy behavior

Keep NIFTY trend separate from India VIX, recent IPO listing gains, subscription, GMP and all other metrics. None is an input to this classification rule.

This decision approves **classification semantics only**, not a score. The legacy v1.5 category-to-points map and adapter alias normalization are not independently approved as scoring policy. They are unchanged by this record.

## Evidence boundary and current status

The existing `evidence/market-observations/official-index-history-20261013/A8-M-SMA-EVIDENCE-20261013.md` documents 245 historical closes through 2026-10-08 and descriptive SMA-50/SMA-200 calculations; the latest reported values are SMA-50 **23,761.064** and SMA-200 **24,282.7665** (that file, “SMA-50 evidence” and “SMA-200 evidence” subsections). Its source captures are rendered/local text, not original provider response bytes; exact provider availability and retrieval times are not established. These values do not by themselves supply a qualifying close/cutoff or authorize a current category. **No NIFTY category or score is assigned by this decision.**

The policy is approved, but source-native evidence qualification and the deterministic, evidence-supported session-calendar/publication-availability rule remain open prerequisites. **A8-M: OPEN. Phase 0: OPEN. Phase 1: UNAUTHORIZED.**

## Unchanged authority boundaries

- Implementation authority: **NOT GRANTED**.
- Release authority: **NOT GRANTED**.
- Production activation: **NOT AUTHORIZED**.
- This decision does not close A8-M or Phase 0, approve provider bytes/captures, or change runtime behavior.
