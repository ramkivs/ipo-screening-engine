# A8-M — NIFTY Source Qualification, Session Availability, and End-to-End Feasibility

- **Status:** REVIEWED INVESTIGATION REPORT — documentation only; not an approval, implementation specification, or production qualification.
- **Inspection date:** 2026-10-13 (Asia/Calcutta). Exact page-tool retrieval times were not exposed.
- **Current gates:** A8-M OPEN · Phase 0 OPEN · Phase 1 UNAUTHORIZED.
- **Authority:** Implementation NOT GRANTED · Release NOT GRANTED · Production activation NOT AUTHORIZED.

This report reuses the existing A8-M evidence package and the already-approved decisions. It assigns **no current NIFTY trend category or score**. It does not change application files or publish/merge a new project decision.

## 1. Executive conclusion

The official sources establish a viable **content route** for NIFTY 50 PRICE INDEX daily observations and support the meaning of the ordinary `NIFTY 50` close. The current workspace contains a coherent, calendar-reconciled descriptive series of **245 positive closes** from 2025-10-13 through 2026-10-08, enough in count to calculate both SMA windows. Its existing SMA files, source-to-row mapping, local hashes, and a 21-endpoint SMA-50 overlap check make the saved arithmetic reproducible as a **local evidence calculation**.

That is not the same as qualifying 245 source observations under the approved production contract. The 2025–2026 source artifacts are page-tool-rendered JSON fragments or a reused local JSON file; the reconstructed JSON, normalized CSV, and SMA CSV are local files. **No original provider response bytes, HTTP headers, exact receipt/retrieval timestamps, record-level publication times, provider-defined immutable record identifiers, or revision-precedence evidence are retained.** The local SHA-256 values identify local bytes only. No explicit source-qualification decision accepts rendered captures as production evidence. Therefore every row in the current 245-row series remains **UNQUALIFIED for Final**, notwithstanding the date/calendar and arithmetic validations.

A targeted official-source cross-check surfaced a material tail gap in the older broad capture: its request ended on 2026-10-13 but its 70 returned rows ended on 2026-10-08. A targeted NSE historical API request for 2026-10-09 through 2026-10-12 returned 2026-10-09 and 2026-10-12; separate official NSE Indices Daily Snapshot CSVs for those dates display matching NIFTY 50 OHLC/close values. These are separate official outputs with a content-level match; the investigation did not establish independent underlying data provenance or independent generation paths. The values were retrievable from both outputs when inspected, but **historical publication/availability at any earlier evaluation cutoff remains unproven**. The new results were inspected as rendered page-tool text, not saved as source-byte captures, and were not appended to the 245-row dataset or used to recalculate an SMA.

The official session calendar and circulars can support the **session-date** part of a deterministic rule for the inspected historical interval, including the 2025 Muhurat session and the 2026 Union Budget Sunday session. They do not establish when the corresponding close became available. The ordinary market-timings page gives normal equity hours (09:15–15:30 IST); it is not evidence that a final index close was published at 15:30. The 2026-11-08 Muhurat session is listed, but its timings were still to be notified on the inspected calendar page.

**Bottom line:**

- Existing sample: useful and internally consistent descriptive evidence; not presently qualified under the approved observation/provenance/cutoff contract.
- Source/index semantics: supported for plain NIFTY 50 PRICE INDEX, with a clear response-level identifier (`EOD_INDEX_NAME = "NIFTY 50"`) in the inspected NSE API output.
- At least 200 historical closes: demonstrated as a local descriptive series; a **200+ qualifying** source series is only conditionally satisfiable pending provider-native data/record evidence and cutoff availability proof.
- Historical publication availability by explicit cutoff: **not established** by the inspected public history/API, daily-report pages, or old local evidence.
- Deterministic session calendar: date selection is supportable for the inspected interval; the required combined session-and-publication-availability rule remains **OPEN / not currently evidence-supported**.
- No NIFTY category, score, implementation, or Final result is authorized or produced here.

## 2. Approved decisions reused without reopening

This investigation carries forward, without reopening, the approved policy in:

- `handoff/decisions/A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`
- `handoff/decisions/A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`

The reused policy is: `market.regime.nifty_trend` is a completed-session-close-derived NIFTY 50 **PRICE INDEX** classification; `supportive` requires close strictly above both SMA-50 and SMA-200; `weak` requires close strictly below both; `neutral` is every other valid combination; incomplete or invalid required inputs/windows are `UNKNOWN`. Each evaluation needs an explicit cutoff with timezone/offset and must select the latest qualifying completed-session close demonstrably available by that cutoff. Retrieval time is not publication time. Expected missing/invalid closes are not skipped. Unresolved conflicting revisions produce `UNKNOWN`. No numeric delay is invented. If required NIFTY trend is `UNKNOWN`, Final is blocked and the evaluation remains non-final/incomplete. This consequence is NIFTY-only.

The existing status also remains unchanged: A8-M OPEN; Phase 0 OPEN; Phase 1 UNAUTHORIZED; implementation/release NOT GRANTED; production activation NOT AUTHORIZED.

## 3. Workspace and evidence provenance actually inspected

### 3.1 Repository and publication-target provenance

At initial checkout inspection, before the targeted publication-target fetch, the shallow local repository was on branch `arena/4e1080b7-ipo-screening-engine` at `01ba66c12ca1195fd7acbd287c3e39a019808094`; the current branch had no upstream tracking ref, and `origin/main` was the only remote-tracking ref. The worktree had 139 untracked paths (including the investigation report and existing evidence, code, fixtures, tests, and handoff files), 11 tracked index entries, and no staged or tracked unstaged changes. These are pre-fetch checkout facts, not a statement of the final post-publication status.

Remote and publication-target verification established:

- `git ls-remote origin` reports `arena/4e1080b7-ipo-screening-engine` at `40a3f1e8ff4ff5d1de023b8cbb1c071f9cb1e1a4`, `arena/01a10b42-ipo-screening-engine` at `4b19faf848a721265597a678926988d484d30e59`, and `main` at `01ba66c12ca1195fd7acbd287c3e39a019808094`.
- GitHub's commit API identifies `4f6d42e55e3247f3eaa2b0c634a99684c3b3f662` as the evidence commit, `6a6c8f2caf3a116f3af45b0a646949b92c4f5aeb` as its reconciliation child, and `40a3f1e8ff4ff5d1de023b8cbb1c071f9cb1e1a4` as the documentation child. The latter's five changed paths are the previously reported decision/tracker/handoff publication.
- GitHub compare reports the `4e` and `01a` remote tips as **diverged**, with common ancestor `01ba66c12ca1195fd7acbd287c3e39a019808094`. No merge of those divergent branches was performed.
- Before publication, GitHub compare of local base `01ba66c12ca1195fd7acbd287c3e39a019808094` to the intended remote `4e` tip `40a3f1e8ff4ff5d1de023b8cbb1c071f9cb1e1a4` reported `ahead` by 9 and `behind` by 0, with `01ba66c12ca1195fd7acbd287c3e39a019808094` as merge base. Thus the intended remote tip was a fast-forward descendant of the local base; this did not require merging the `4e` and `01a` branches.
- A targeted fetch of only `refs/heads/arena/4e1080b7-ipo-screening-engine` added `refs/remotes/origin/arena/4e1080b7-ipo-screening-engine` at `40a3f1e8ff4ff5d1de023b8cbb1c071f9cb1e1a4`. Local `HEAD...origin/arena/4e1080b7-ipo-screening-engine` counted 0 commits ahead and 9 behind. The fetch updated Git objects/ref only; it did not check out files or merge branches.
- The target branch tree did not contain this report path and contains 114 files. After a fast-forward ref update and index-only alignment (without updating worktree files), a byte-hash check confirmed all 150 then-present workspace files were unchanged by the alignment operation. The aligned status shows one pre-existing worktree file (`handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md`) differing from the target tree and 36 untracked paths (including this report); no target-tracked file is missing. The unrelated modified path and the other 35 untracked paths were preserved unstaged; publication staging was limited to this report, so it is additive.
- The evidence commit lists 28 paths. All **28/28 local Git blob IDs** computed from the current evidence directory match those remote commit paths. This verifies that the local workspace evidence files match the evidence commit's repository bytes. It does **not** verify that those local Git blobs are original provider bytes.

### 3.2 Existing A8-M files and local hashes

Inspected in `evidence/market-observations/official-index-history-20261013/`:

- `A8-M-EVIDENCE-FINDINGS.md`
- `A8-M-SMA-EVIDENCE-20261013.md`
- `evidence-manifest.json`, `transfer-manifest.json`, and `source-captures/response-capture-manifest.json`
- `nse-cm-session-calendar-validation-20261013.json`
- `nse-index-alignment-validation-20261013.json`
- `nse-nifty50-sma-integrity-validation-20261013.json`
- the normalized close CSV, SMA-50/SMA-200 CSVs, source-response JSON files, and the reused July–October NIFTY/VIX files
- rendered circular extracts for NSE/CMTR/70319 and NSE/CMTR/72349.

Targeted SHA-256 checks matched the local `evidence-manifest.json` for the normalized close CSV (51,377 bytes; `A3F6CA34732B22447A263A613820EB0B22FBC2E64888E2B59036012FF40A4B3D`), the SMA-50 CSV, SMA-200 CSV, SMA integrity validation, the reused 70-record NIFTY JSON, and the capture manifest. These digests identify the **exact local files checked**, not NSE provider response bytes. The evidence manifest itself says the same and excludes itself from its file list.

The response-capture manifest says the five new date windows were fetched through `functions.fetch_page`; what is saved is rendered JSON text in chunks and reconstructed JSON after removing tool-added Markdown fences/joining chunks. It records retrieval date only and `retrievalTime: null`; it says raw provider bytes, headers, and exact receipt times were not captured. The reused 70-session file has no recorded retrieval time. The normalized CSV's `source_record_index` is a local ordinal into a saved/reconstructed response, not an NSE-issued record ID.

### 3.3 Observation-scoped qualification matrix

| Evidence form / population | What is present | Publication, receipt, identity and revision evidence | Current qualification result |
|---|---|---|---|
| Original provider-delivered NSE/NSE Indices bytes | **None** in the inspected package | No original response body, HTTP headers, server receipt log, or provider-byte hash | Missing; cannot authenticate the saved rendering retrospectively |
| Official NSE history endpoint content as rendered by the page tool — five new windows, 175 records | Request URL, `indexType=NIFTY 50`, response text, `EOD_INDEX_NAME`, `EOD_TIMESTAMP`, OHLC fields including `EOD_CLOSE_INDEX_VAL`; counts 70, 26, 28, 30, 21 | No exact provider bytes, headers, response receipt time, publication time, documented meaning of `HI_TIMESTAMP`, provider record ID, or revision precedence | Source/content route is descriptive; individual observations remain unqualified for production/Final |
| Reused official NSE history response — 70 records, 2026-07-01 through 2026-10-08 | Local JSON file and hash; 70 rows; `EOD_INDEX_NAME` and OHLC/date fields | The local evidence package records no retrieval date/time for this reused file; hash is local | Descriptive/unqualified under the same contract gaps |
| Reconstructed response JSON and normalized 245-row CSV | Local transformations; every CSV row maps to a source-response filename, query range, and local record index | No provider-defined record ID; no publication/availability or receipt timestamp carried into the normalized rows | Reproducible local data lineage, not provider authentication |
| SMA-50/SMA-200 CSVs and validation | Local calculation method, window start/end and counts; 196 SMA-50 and 46 SMA-200 endpoints; latest endpoint 2026-10-08 | The inputs inherit the source limitations above | Arithmetic is reproducible from the retained local input; not a qualified production snapshot |
| Direct targeted API and Daily Snapshot CSV cross-check for 2026-10-09 and 2026-10-12 | Separate official rendered API responses and CSV outputs display matching OHLC/close values | Tool did not expose original bytes, HTTP headers, exact receipt time, source publication time, or revision information; independent underlying data provenance was not established; observations were not saved as raw files | Useful current content-level cross-check only; historical cutoff availability remains unproven and these observations are not part of the 245-row validated dataset |

The 245-row calendar validator reports 245 unique dates, 245 expected sessions, 245 observed sessions, zero missing expected dates, zero unexpected dates, and positive finite close values. I inspected the validation artifact and representative source-row mappings, **not all 245 observations individually**. The package has no indicated date exception beyond the sessions called out below; nevertheless, all 245 observations require source-native/provenance qualification before any is treated as eligible for Final.

## 4. Official sources examined and index-selection findings

### 4.1 NSE Indices Historical Data interface

Inspected: [NSE Indices Historical Data](https://www.niftyindices.com/reports/historical-data).

The rendered interface exposes a `Historical Index Data` section, selectors for index type, sub-index type, index, and time period, a CSV control, and a result table with `Date`, `Open`, `High`, `Low`, and `Close`. It also exposes a separate `Total returns Index Values` section/table. In the page-tool rendering used here no index was selected and the historical table showed no data; the dynamic dropdown choices were not available to inspect, and I did **not** submit this form or download its CSV.

A defensible UI selection is therefore: use **Historical Index Data**, choose the equity NIFTY 50 entry labelled plain `NIFTY 50`, not a total-return series, and retain the output index label with the CSV. The returned `NIFTY 50` name should be checked, not inferred from a filename alone. The exact dynamic selection path was not exercised in this investigation.

### 4.2 Official index and close semantics

Inspected: [NSE Indices FAQ](https://www.niftyindices.com/resources/index-concepts/faqs). It explicitly states that what is commonly reported as NIFTY 50 is the **NIFTY 50 Price Index**, and distinguishes the NIFTY 50 Total Returns (TR) index, which includes reinvested dividends. It also states that NIFTY 50 closing prices are calculated using the last half-hour weighted-average closing prices of the constituents. This supports the semantic choice and close methodology; it does not authenticate an individual downloaded row or give a row's publication time.

The direct NSE history endpoint route inspected in the existing evidence and targeted checks is `https://www.nseindia.com/api/historicalOR/indicesHistory?indexType=NIFTY%2050&from=...&to=...`. Its rendered rows say `EOD_INDEX_NAME: "NIFTY 50"` and include `EOD_TIMESTAMP` (date string), `EOD_CLOSE_INDEX_VAL`, and OHLC fields. That name plus the official FAQ distinguishes the plain price index from TR for the inspected responses. The API's `HI_TIMESTAMP` field is also present, but no field specification was found in the inspected API/documentation; it is **not** treated as event time, publication time, receipt time, or revision time.

### 4.3 Targeted official cross-check of the tail

Inspected the [NSE Indices Daily Reports page](https://niftyindices.com/reports/daily-reports) and its dated CSVs for 2026-10-09 and 2026-10-12, plus targeted NSE history endpoint requests with `indexType=NIFTY 50` for 2026-10-09–2026-10-12 and 2026-10-09–2026-10-13.

| Session date | API-rendered NIFTY 50 open / high / low / close | Daily Snapshot CSV NIFTY 50 close | Cross-check |
|---|---|---:|---|
| 2026-10-09 | 22,314.95 / 22,580.75 / 22,294.75 / **22,520.45** | **22,520.45** | Matching values in separate rendered outputs |
| 2026-10-12 | 22,593.20 / 22,651.10 / 22,304.45 / **22,363.35** | **22,363.35** | Matching values in separate rendered outputs |

The targeted API responses and dated Daily Snapshot CSVs are separate official outputs that display matching values. This is a content-level cross-check only: the inspected evidence does not establish independent underlying data provenance or independent generation paths. Neither output establishes historical publication/availability or receipt by an earlier evaluation cutoff; that availability remains unproven.

Official CSV links inspected: [`ind_close_all_09102026.csv`](https://niftyindices.com/Daily_Snapshot/ind_close_all_09102026.csv) and [`ind_close_all_12102026.csv`](https://niftyindices.com/Daily_Snapshot/ind_close_all_12102026.csv). Their displayed columns include `Index Name`, `Index Date`, OHLC/closing index value, changes, volume/turnover and valuation fields. Their filenames and `Index Date` identify the report/session date; the rendered CSV rows contain no publication/availability timestamp, receipt time, immutable row ID, or revision precedence.

The earlier broad saved query `from=01-07-2026&to=13-10-2026` contains 70 observations and ends on 2026-10-08, despite the requested end date. The targeted request returns 2026-10-09 and 2026-10-12; the daily-report page also lists those dated files. The cause of the broad response's shorter tail (request behavior, capture behavior, or another limitation) is **not established**. The 2026-10-09 and 2026-10-12 observations were not appended to the local 245-row file, and no new SMA calculation was performed.

The 2026-10-09–2026-10-13 API query also returned only the 2026-10-09 and 2026-10-12 rows. No 2026-10-13 row was present in that rendered result or in the inspected daily-report listing. The page-tool output displayed an NSE page footer of `13-Oct-2026 | 16:55 (IST)`, but the tool did not expose HTTP headers or exact receipt time and that footer is not a per-file publication time. The absence of an Oct-13 record from this rendered response is a current inspection finding, **not proof of when an Oct-13 close became available or unavailable at any earlier cutoff**.

### 4.4 NSE paid EOD and historical products

Inspected the [NSE Paid End of Day / Historical Data page](https://www.nseindia.com/static/market-data/eod-historical-data-subscription) and its linked [CM End of Day Technical Specification (version 1.2, 13-Oct-2025)](https://nsearchives.nseindia.com/web/mediaattachment/2025-11/EOD_CM_20251120105001.pdf).

The page describes separate products. Its CM EOD specification lists a daily `MAddmmyyyy.csv` Cash Market Activity report with an `Indices Information` section containing `Index Name`, previous close, open, high, low, close, and gain/loss fields. This is a plausible daily-close record route. The page/spec inspected here does **not** provide a sample `MAdd` file proving that this product contains the exact `NIFTY 50` PRICE INDEX row for a specified session, nor does it supply a source-defined row ID, revision precedence, or a historical publication timestamp. The spec says CM EOD files are delivered through SFTP and access requires client setup (SSH public key/static public IP and NDAL-provided credentials); the page directs users to NDAL for subscription and tariff information. No subscription, SFTP access, sample file, or file receipt was obtained in this investigation. Retention and a product-specific, guaranteed publication/availability time were not established from the material inspected.

The current NSE page separately describes EOD Order & Trade delivery by SFTP and Historical Order & Trade access through an online platform; it states that the Capital Market product includes index value. Its linked current [Historical Order & Trade specification v1.19 (dated 03-Aug-2026)](https://nsearchives.nseindia.com/web/mediaattachment/2026-09/NSE_Hist_Order_Trade_Data_1.19_20260902144045.pdf) lists a `3.1.9 Index Data` section at page 56. The PDF text tool only exposed the first 30 pages; I did **not** inspect that current section or the later EOD availability FAQ. Thus this is a candidate product route, not proof of its current index-row schema or that its record is the official daily close needed here.

For comparison only, the official older [Order and Trade specification v1.15 (13-Aug-2025)](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Hist_Order_Trade_Data_1.15.pdf) exposes section 1.3 `Index Data`: all ticks, date, transaction time (`HH:MM:SS`), NIFTY 50 value, and NIFTY Next 50 value. That older all-ticks layout is not by itself a dedicated final EOD close record; the current v1.19 page-56 schema was not available in the parsed output, so no assumption is made that the schema is unchanged.

An official v1.15 Order & Trade SFTP FAQ states that its documented file-availability timings are **provisional** and source-side delays may affect availability; it also says the previous three days' files are available on that SFTP route. Those statements are product/version-scoped to Order & Trade SFTP. They are not guarantees for an actual file and must not be transferred to the separate NSE Indices Historical Data CSV/API or the distinct CM EOD `MAdd` product without explicit product-specific documentation. The three-day note is not evidence of retention for the online historical-data platform or the index data section in the current v1.19 specification. Likewise, any full Orders/Trades cooling-off rule must not be applied to the Index Data record without confirmation in the applicable specification. None of these notes establishes historical receipt of a particular record. No numeric delay allowance is adopted.

### 4.5 Calendar, market timings, special sessions, and historical background

Inspected the [NSE 2026 trading-holidays page](https://www.nseindia.com/resources/exchange-communication-holidays), [NSE Market Timings page](https://www.nseindia.com/static/market-data/market-timings), and the local rendered extracts of NSE circulars `NSE/CMTR/70319 (124/2025)` and `NSE/CMTR/72349 (11/2026)` in the evidence package.

The official calendar lists weekday CM holidays and notes a 2026-11-08 Muhurat session, with timing to be notified later. The ordinary equity schedule shows 09:15–15:30 IST; special-session timing must come from its own circular. The existing rendered circular extracts confirm:

- 2025-10-21: NSE scheduled live Diwali Muhurat trading, normal market 13:45–14:45.
- 2026-02-01 (Sunday): NSE scheduled live Union Budget trading, normal market 09:15–15:30.

These explain the observed special-session dates in the local series. The existing calendar validator records rendered NSE holiday-master results for 2025/2026, 259 weekday candidates, 15 weekday closures, the Sunday 2026-02-01 session, and 245 expected/observed sessions from 2025-10-13 through 2026-10-08. Its calendar payload and circular extracts are rendered/local text, not original provider bytes. A calendar identifies when a session was scheduled; it does **not** show when its official close was published.

Also inspected the older NSE [Historical Data Dissemination of Capital Market Segment document](https://nsearchives.nseindia.com/content/press/Data_details_CM.pdf). It describes historical Index data and an official closing field, but it is legacy documentation and does not establish the present-day delivery route, current revision behavior, or publication availability for the current historical CSV/EOD products. It is background only.

## 5. Publication-availability and provenance analysis

| Time/evidence concept | What was observed | What it proves / does not prove |
|---|---|---|
| Session date | `EOD_TIMESTAMP` in the NSE API and `Index Date` in Daily Snapshot CSVs; local series stores normalized session dates | Identifies a date in the displayed response. The API date field has no time/offset. |
| Source-native close/event time | Public history output has an undocumented `HI_TIMESTAMP` in addition to `EOD_TIMESTAMP`; historical page CSV displays a date and OHLC/close | No inspected field specification establishes the time field's semantics or a 15:30 close timestamp. The FAQ documents close methodology, not row availability. |
| Publication time | No per-row publication time found in the historical API output, public history page, daily-report CSV rows, or retained local package | Cannot establish when a historical close first became public. |
| Provider delivery / receipt | No SFTP receipt, provider trigger/checksum log, HTTP response headers, or original source file timestamps in the current evidence package | Cannot establish receipt of any existing row by a particular cutoff. Paid SFTP documentation is a possible future evidence route, not a receipt record. |
| Retrieval time | Existing manifest records a retrieval date for five rendered windows but `retrievalTime: null`; reused 70-row file has no recorded retrieval timestamp. The page tool did not expose exact retrieval/receipt time for the targeted queries. | A date-only entry is not an instant. A download today would not prove availability at a past cutoff. |
| Evaluation cutoff | No evaluation-specific cutoff was supplied for this investigation | No “latest eligible close” can be selected for an actual evaluation. A future evaluation must record an explicit time and timezone/offset. |
| Record identity / revision | Local `source_record_index` and file/query range are present; public rows have index/date/close fields; no stable provider record ID or source-defined revision precedence was found | Local ordinals are not provider IDs. Conflicting/revised source records cannot be deterministically resolved from inspected evidence. |
| Hash | Local SHA-256 values match the retained evidence manifest; local Git blobs match all 28 paths from remote evidence commit `4f6d42e…` | Verifies local repository artifact integrity/provenance. It never proves provider-byte integrity, publication time, or availability. |

**Historical cutoff result:** not established. The dated daily-report link and current historical API output show that dated values can be retrieved now. Neither contains contemporaneous historical publication/receipt evidence. The provisional Order & Trade SFTP schedule is not evidence for a different product and is not a guaranteed timestamp. A historical cutoff cannot be backfilled by assigning today's retrieval time or by inferring a delay from the market close.

**Prospective route:** conditionally plausible if a product-specific contract/file specification confirms the exact index record and an ingestion process retains provider-delivered bytes, the source file/record identity, checksum/version, and a trustworthy receipt/availability timestamp with timezone/offset. That would support a record's availability by a future cutoff. It would still need evidence that no newer expected-session close should have been available, plus documented revision precedence. None of those receipts or product confirmations is present here.

## 6. Proposed evidence-backed session decision table

This table restates the approved policy as an investigation aid; it is **not** an implementation specification. `Latest close` below means the latest qualifying completed-session close demonstrably available by an explicitly recorded cutoff—not simply the newest date in a file.

| Case | Required evidence | Proposed eligibility/result under approved policy | Remaining support status |
|---|---|---|---|
| Before the regular session completes | Applicable CM calendar/circular and session timetable; cutoff with timezone | Do not treat live/indicative values or the in-progress session as a completed-session close. A prior close can remain eligible only if it is still the latest qualifying completed session and no newer close should have been available by cutoff. | Session calendar/timings are documented; source publication/availability remains open. |
| Session completed, but close not demonstrably published/available | Completed-session proof; source publication or delivery evidence; cutoff | Do not invent a delay. If the new close should be available or availability cannot be determined, do not silently reuse the prior close; `UNKNOWN` for the required observation. | Not supported by the inspected public historical data. |
| Qualifying close demonstrably available by cutoff | Exact source record/bytes, NIFTY 50 price-index identity, session date, documented close field, publication/receipt evidence before cutoff, source/revision identity | Eligible as the latest qualifying completed close; retain all timestamps distinctly and proceed only with complete valid SMA windows. | Conditional on acquiring the product-native record and availability evidence. |
| Weekend | Official CM calendar and any special-session circular; latest-source availability evidence | No regular session is assumed. A prior session close may remain eligible only while it remains the latest qualifying completed session and no newer close should have been available. Do not apply a 24-hour elapsed-time test. | Calendar dates are supportable; publication side remains open. |
| Declared exchange holiday | Applicable year/segment holiday source and any overriding session circular | No regular CM close is expected on the declared holiday unless a special session is officially scheduled. Retain the prior close only under the approved latest-session/availability condition. | Historical dates checked against rendered 2025/2026 CM calendar; availability unresolved. |
| Muhurat or other special session | Session-specific NSE circular with date and actual timings; source close/session identity; availability evidence | Treat as a session only when the official notice establishes it; use that session's close and exact calendar position. Do not infer normal hours or publication time. | 2025-10-21 and 2026-02-01 are supported by rendered circular extracts. For 2026-11-08 the calendar says timing will be notified later. |
| Expected session has no close row | Official calendar/circular plus complete source-file coverage/receipt; source error or missing-row evidence | Do not skip the expected close or substitute a convenient older close. `UNKNOWN`; preserve the missing-session reason. | The existing 245-date validator reports no missing dates through 2026-10-08, but the API's broad returned window missed 2026-10-09/12 until targeted requests; the cause is unresolved. |
| Delayed publication | Product-specific documented availability scope and actual per-file publication/receipt time, all with timezone/offset; explicit cutoff | If first demonstrable availability is after cutoff, it is ineligible for that cutoff. If availability cannot be established, `UNKNOWN`; no numeric delay allowance. | No actual file receipt or per-record publication evidence in this investigation. |
| Conflicting or revised rows for same session | Exact original/revised records, source revision identifier/order, source-defined correction precedence | Apply only documented source-defined precedence; otherwise reject conflict and return `UNKNOWN`. | No revision identifier or precedence evidence was found in the inspected public rows. |
| Future/impossible timestamp or source event after cutoff | Source-native timestamp definition/timezone and explicit cutoff | Reject a future/impossible event or an observation not available by cutoff; `UNKNOWN` if no qualifying alternative. | Existing public date fields have no time; `HI_TIMESTAMP` is undocumented. |
| Missing/unresolved timezone or timestamp semantics | Original timestamp and its source timezone/offset; documented meaning of each field | Do not compare ambiguous times to cutoff. If session date is known but availability cannot be compared, `UNKNOWN` for the cutoff-controlled input. | Open for public history output and old captures. |
| Fewer than 50/200 qualifying closes | Complete expected-session calendar and qualified records through evaluation session | SMA-50 or SMA-200 cannot be computed as required; trend `UNKNOWN`. | The local series has 245 dates, but they are not source-qualified for production. |
| Missing/invalid expected close inside a required window | Session calendar, exact source records and validation reason | Do not silently skip or impute the close; trend `UNKNOWN`, with reason retained. | General approved rule is settled; no such runtime behavior was implemented/tested here. |

The date-calendar evidence can make the session-date decisions deterministic for the inspected historical interval. The source does not currently support the publication-availability branch of this table with a deterministic, testable, source-backed rule. Therefore the combined prerequisite remains open.

## 7. SMA and end-to-end feasibility

The existing local package documents 245 unique closes, 245 expected/observed session dates, and calculation windows that include each endpoint session. It reports:

- latest SMA-50 endpoint 2026-10-08: **23,761.064**, using 50 observations;
- latest SMA-200 endpoint 2026-10-08: **24,282.7665**, using 200 observations;
- 196 SMA-50 and 46 SMA-200 endpoints overall;
- 21 overlapping SMA-50 endpoints matching a previous calculation.

I verified local manifest hashes for the close CSV, both SMA files, the SMA validation, the reused 70-row response, and capture manifest; I did **not** recalculate all 245 rows or recalculate either full SMA series. The 2026-10-09 and 2026-10-12 close cross-checks were not merged into the local series. Because those later dates exist in official rendered sources, the 2026-10-08 averages must not be treated as the latest SMA endpoints for a later session/cutoff. No trend is derived from these averages.

| End-to-end requirement | Classification | Evidence-backed finding / limiting condition |
|---|---|---|
| Plain NIFTY 50 PRICE INDEX meaning, distinct from TR | **SATISFIABLE** | Official FAQ distinguishes plain NIFTY 50 Price Index from NIFTY 50 TR; NSE API output labels records `NIFTY 50`. |
| Daily close/session fields exist on official routes | **SATISFIABLE** for the inspected response form | API output includes `EOD_INDEX_NAME`, `EOD_TIMESTAMP`, and `EOD_CLOSE_INDEX_VAL`; historical UI and daily reports show date/OHLC/close. Full native byte/schema qualification is separate. |
| Existing descriptive series contains at least 200 distinct session dates | **SATISFIABLE** | Local validated series contains 245 dates, 2025-10-13–2026-10-08, with no date gaps against its retained calendar validation. |
| 200+ **qualifying** provider-native closes for a cutoff-controlled SMA window | **CONDITIONALLY SATISFIABLE** | Official routes and 245 descriptive records make a plausible route; exact provider bytes, product/record semantics, per-record availability, and latest-session completeness remain outstanding. |
| Historical session calendar for 2025-10-13–2026-10-08 | **SATISFIABLE** at the date/session level from inspected official information | Rendered NSE CM calendar/master plus special-session circular extracts align to the local 245 dates. This does not establish publication time. |
| Deterministic session-calendar **and publication-availability** decision rule | **NOT CURRENTLY SATISFIABLE** from evidence inspected | Calendar side is supported; publication timing is not. No numeric allowance may be inferred from market close or a separate product's provisional schedule. |
| Historical publication availability relative to an earlier explicit cutoff | **NOT CURRENTLY SATISFIABLE** from retained/public history evidence | Current historical retrieval/page presence is not evidence of availability at a past cutoff; no historical receipt/publication logs exist in the package. |
| Reproducible SMA arithmetic from the exact local 245-row normalized input | **SATISFIABLE** as a descriptive local calculation | Inputs, calculation method, windows, outputs, local hashes and the targeted 21-point overlap check are recorded. This does not authenticate provider bytes or establish cutoff eligibility. |
| Reproducible SMA values for the latest qualifying close at a specified cutoff | **CONDITIONALLY SATISFIABLE** | Requires current complete 200-session qualifying inputs, cutoff-visible availability, and resolved source/revision semantics. No cutoff was specified here; no new SMA was calculated. |
| Provider-defined stable record/revision IDs and revision precedence | **UNRESOLVED** | No stable ID or revision ordering was found in the inspected public output. The current v1.19 index-data schema page was not exposed by the PDF parser, and no subscribed sample was retrieved. |
| Exact current paid-product access, retention, and index row coverage | **UNRESOLVED** | The official page/specs show subscription/SFTP or online-platform routes; no subscription, actual sample, retention schedule, or source receipt was inspected. |

## 8. Exact remaining evidence required

Before this source route can satisfy A8-M qualification, obtain or explicitly resolve all of the following:

1. **Record/product identity:** Current product specification for the exact chosen route, including the full current v1.19 `Index Data` section if used; a representative actual file/sample showing the plain NIFTY 50 PRICE INDEX record and the official daily close, not just an index tick or stock bhavcopy. For the CM EOD route, inspect a representative `MAdd` file and confirm its NIFTY 50 row, date semantics and close meaning.
2. **Provider-native evidence:** Exact original provider-delivered file/response bytes, source URL/product, query parameters, product/version, original file name, complete byte count, source-native row locator/ID, and a hash of the exact object received. Keep any rendered excerpt as a separate evidence form.
3. **Event/session semantics:** Specification of date and timestamp fields, including `EOD_TIMESTAMP`/`HI_TIMESTAMP` if the current API is retained; timezone/offset and whether a time denotes index event, file creation, publication, or something else. Do not promote `HI_TIMESTAMP` based on its appearance alone.
4. **Availability by cutoff:** Product-specific publication/delivery definition and trustworthy per-file publication/receipt evidence with timezone/offset. Preserve actual file arrival/ingestion records for future cutoffs. For retrospective cutoffs, obtain contemporaneous archive/server/client receipt logs or other source-native evidence; today's downloads are insufficient.
5. **Latest-session logic:** Evidence that identifies which completed close was the latest one available at each cutoff, including after a new session, delayed or absent files, weekends, holidays, and special sessions. The ordinary market timetable is not a delivery schedule.
6. **Revision precedence:** Source documentation and records for correction/reissue behavior, stable revision identifiers, and precedence. Until source-defined precedence is proved, conflicting rows stay `UNKNOWN`.
7. **Calendar:** Retain the applicable versioned CM holiday/session calendar and every relevant special-session circular. In particular, obtain the 2026-11-08 Muhurat timetable circular when issued; do not assume its normal-market hours.
8. **Coverage and completeness:** Capture the missing 2026-10-09 and 2026-10-12 records in native form, reconcile why the broad 2026-07-01–2026-10-13 rendering stopped at 2026-10-08, and verify a complete expected-session series including the evaluated session. Use segmented queries if required and record all source inputs; do not assume the current 245 rows are the latest 200-row window.
9. **Evidence-form decision if needed:** If original provider bytes remain unobtainable and rendered captures are proposed for production qualification, obtain a separate explicit decision accepting that evidence form. No such acceptance is made by this report.
10. **Evaluation cutoff:** For each actual evaluation, record its explicit timestamp and timezone/UTC offset. This report does not select a cutoff or a latest observation.

## 9. Read-only implementation note and scope boundary

A targeted read of `engine/ipo_screening/connectors/adapters.py` confirmed that the current `MarketRegimeAdapter` normalizes an incoming `nifty_trend` category; it does not derive the category from NIFTY closes. It also defaults a missing `retrieval_timestamp` to local `datetime.now(UTC)`. Such a fallback is not evidence of provider publication/receipt time and must not be treated as satisfying this source contract. No code/configuration was changed and this report does not authorize changing that behavior. Earlier VIX and recent-IPO listing-gain qualification issues remain separate and are not reopened here.

## 10. Status, destination, and publication boundary

- **Source-native qualification of existing 245 observations:** OPEN / not qualified for Final.
- **Historical availability by explicit cutoff:** OPEN; not established by inspected sources.
- **Deterministic calendar/publication-availability rule:** OPEN prerequisite; calendar dates are supportable, publication component is not.
- **At least 200 descriptive closes and local SMA arithmetic:** demonstrated; 200 qualifying closes for a cutoff are not yet established.
- **Current NIFTY category/score:** none assigned.
- **A8-M:** OPEN. **Phase 0:** OPEN. **Phase 1:** UNAUTHORIZED.
- **Implementation authority:** NOT GRANTED. **Release authority:** NOT GRANTED. **Production activation:** NOT AUTHORIZED.

This reviewed investigation record is maintained under `handoff/investigation/`. Its publication is documentation-only: it does not amend the approved decision records or close any gate. No tracker or reconciliation cross-reference is changed in this publication.
