# A8-M — NIFTY 50 Simple Moving-Average Evidence

**Status: EVIDENCE ONLY — NON-AUTHORITATIVE. A8-M remains open.**

This additive note records descriptive NIFTY 50 SMA-50 and SMA-200 calculations. It does not define or assign the engine's `market.regime.nifty_trend`, approve a cutoff or freshness rule, change missing-data semantics, alter scoring, or authorize implementation/configuration changes.

## Source observations and coverage

The official NSE NIFTY 50 history endpoint returned five newly captured, non-overlapping windows covering **13 October 2025 through 30 June 2026**. The previously published 70-session NIFTY 50 source file for **1 July through 13 October 2026** was reused unchanged; its last returned close is dated **8 October 2026**. The combined, calendar-validated source series therefore contains **245 unique positive numeric closes**, from 13 October 2025 through 8 October 2026:

| Source window | Returned observations |
| --- | ---: |
| 2025-10-13–2026-01-22 | 70 |
| 2026-01-23–2026-02-27 | 26 |
| 2026-03-02–2026-04-15 | 28 |
| 2026-04-16–2026-05-29 | 30 |
| 2026-06-01–2026-06-30 | 21 |
| Reused published 2026-07-01–2026-10-13 response | 70 |
| **Total** | **245** |

The five new windows were queried from the official endpoint at `https://www.nseindia.com/api/historicalOR/indicesHistory` with `indexType=NIFTY 50`. The returned JSON text fragments and reconstructed, parse-checked payloads are listed in `source-captures/response-capture-manifest.json`. The 245-row normalized close series is `nse-nifty50-close-observations-20251013-20261013.csv`; it records a source-response file, query range, and record index for every close.

The earlier broad date-range request did not expose the entire requested history in its rendered output. Rather than reuse an incomplete result, the intervening period was collected in the narrower windows above. No VIX extension was needed for this calculation.

### Source integrity limits

For the five new requests, Arena's page tool exposed rendered JSON text in chunks, not provider HTTP bytes, headers, or exact receipt times. The local chunk files preserve the returned rendered text; the matching `source-responses/*-rendered-response.json` files are reconstructed by removing Markdown fences and joining those chunks. Their hashes and all other hashes in these files identify **local workspace bytes only**; they are not provider-byte hashes. The reused July–October source likewise has no recorded retrieval time. These limitations are retained in the capture manifest rather than inferred away.

## Session and close validation

The combined source dates were checked against NSE's Capital Market (`CM`) holiday-master entries for 2025 and 2026. There are **259 weekday dates**, of which **15** are weekday CM closures in the observation window. Two date exceptions are supported by official NSE live-session circulars and were included as valid observations:

- **21 October 2025:** Diwali Muhurat normal-market session; NSE Circular `NSE/CMTR/70319` (124/2025), normal market 13:45–14:45.
- **1 February 2026 (Sunday):** Union Budget live session; NSE Circular `NSE/CMTR/72349` (11/2026), normal market 09:15–15:30.

Thus the expected session count is 259 weekday dates minus 15 weekday closures, plus the 1-February Sunday session = **245**. The calendar comparison found **zero missing expected sessions and zero unexpected observed dates**. All 245 closes are present, finite, numeric, and greater than zero. The holiday extract, special-session references, and targeted result are in `nse-cm-session-calendar-validation-20261013.json` and `nse-nifty50-sma-integrity-validation-20261013.json`.

The earlier published 70-session source was reused, not reacquired. As a focused seam check, all **21** SMA-50 endpoints available from that 70-session file (8 September–8 October 2026) match the corresponding calculations from the combined 245-session source exactly: first `24196.319`, last `23761.064`.

## Calculation method

For each eligible endpoint session `t`, let `C(t)` be its NSE NIFTY 50 EOD close, and let the ordered observations be consecutive validated NSE Capital Market sessions. The simple moving average is:

`SMA_n(t) = (C(t) + C(t-1) + ... + C(t-(n-1))) / n`

The endpoint session is included. There is no calendar-day resampling, forward fill, missing-close imputation, or intermediate rounding. CSV values contain the exact decimal arithmetic mean of the input closes. Each output row identifies its window's first session, last session, and observation count. The source observation CSV is the input to both calculations.

### SMA-50 evidence

- Eligible source closes: 245
- Output points: **196**
- First eligible endpoint: **23 December 2025**, using 50 closes from 13 October–23 December 2025; SMA-50 = **25874.062**
- Latest endpoint: **8 October 2026**, using 50 closes from 29 July–8 October 2026; SMA-50 = **23761.064**
- Full series: `nse-nifty50-sma50-20261013.csv`

### SMA-200 evidence

- Eligible source closes: 245 (more than the required 200)
- Output points: **46**
- First eligible endpoint: **4 August 2026**, using 200 closes from 13 October 2025–4 August 2026; SMA-200 = **24772.9665**
- Latest endpoint: **8 October 2026**, using 200 closes from 17 December 2025–8 October 2026; SMA-200 = **24282.7665**
- Full series: `nse-nifty50-sma200-20261013.csv`

These numbers are descriptive moving averages only. No SMA value is mapped to `supportive`, `neutral`, or `weak`, and no score is assigned.

## Existing alignment-manifest correction

A targeted integrity check found that the existing `transfer-manifest.json` declared `nse-index-alignment-validation-20261013.json` as 16,184 bytes with SHA-256 `C7C67B7DD929D27CAD6D37FC025A5088805B49B0D3D0B6B2091028C204AB1A48`, while the unchanged artifact in the published Git tree is 15,659 bytes with SHA-256 `D5776178EF7198F9E9B73D3B1191F80FEE2BF48945BCF338D25F26AFBC8D1E1A`. The manifest now records the artifact's actual local size/hash. The alignment JSON content itself was not changed; its input hashes and 70 close rows were independently checked against the unchanged NIFTY/VIX files. This corrects local file-copy metadata only and does not assert provider-byte integrity.

## Evidence classes and unresolved decisions

| Class | This investigation records |
| --- | --- |
| Source observations | Official NSE NIFTY 50 EOD closes, the published NIFTY/VIX files, the rendered-history response captures, and the relevant NSE session-calendar/circular records. |
| Derived statistics | The SMA-50 and SMA-200 values in the separate CSV files, with explicitly identified consecutive-session windows. |
| Unresolved rule decisions | Trend formula and boundaries, point-in-time cutoff, freshness policy, and missing-data semantics remain unresolved. Legacy point allocations do not approve a current classification formula. |
| Data limitations | Original provider response bytes, response headers, exact retrieval timestamps for the rendered fetches, and a provider-byte hash are unavailable. The returned source history ends on 8 October 2026 despite the request ending on 13 October. |

No product behavior or configuration was changed. No full-suite tests were run. Targeted source, calendar, manifest, and arithmetic validations are recorded in the accompanying JSON manifests. **This evidence does not close A8-M.**