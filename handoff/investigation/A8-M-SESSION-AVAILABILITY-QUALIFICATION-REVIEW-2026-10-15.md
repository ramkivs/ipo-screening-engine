# A8-M — Targeted NIFTY Source-Qualification and Session-Availability Review

- **Review date:** 2026-10-15 (Asia/Kolkata)
- **Status:** Additive evidence assessment; not a source-qualification approval or new policy decision.
- **A8-M status:** OPEN. No current NIFTY category or score is assigned.
- **Baseline:** fixed branch `arena/573e69a4-ipo-screening-engine`, commit `65de3bd91e6a56eaba8d724f22666ffc6b9100ed`.

## Executive finding

The retained material supports a **content route** for ordinary NIFTY 50 price-index daily values and a bounded, calendar-reconciled session-date series through **2026-10-08**. It does not establish original provider bytes for the saved observations, a provider publication/receipt timestamp, stable record or revision identity, or whether a newer completed-session close was demonstrably available by any earlier evaluation cutoff. The date/calendar side is materially better supported than the publication/availability side; the combined deterministic session-and-availability prerequisite remains open.

The newest retained inspection of the tail is the page-tool review dated **2026-10-13**, not a fresh retrieval on this report's date. That earlier review records that targeted NSE API output and separate NSE Indices Daily Snapshot output displayed matching values for **2026-10-09** and **2026-10-12**. It did not save the underlying response bodies as provider bytes, HTTP status/headers, or exact retrieval instants. The matches establish only that the rendered outputs exposed those values during that inspection. They do not prove availability at an earlier cutoff, authenticate the original bytes, or show when the values were first published.

No direct NSE request was made on 2026-10-15. The sandbox's permitted outbound hosts do not include `nseindia.com`, `niftyindices.com`, or `nsearchives.nseindia.com`; therefore a direct HTTP/download capture was not feasible or permitted in this review. No request failed, so there is no HTTP error/status to report. No DevTools WebSocket approach was repeated. No provider contact, NDAL request, subscription, or purchase occurred.

The existing 245-close input and its SMA-50/SMA-200 evidence are reused unchanged. No observation was appended, no close series or moving average was recalculated, and no application/configuration/schema/scoring behavior was changed. The approved price-index, completed-session, trailing SMA-50/SMA-200, strict supportive/weak, neutral-otherwise and UNKNOWN-on-invalid/incomplete/unqualified/conflicting/stale semantics remain untouched; required-NIFTY UNKNOWN still means Final is withheld.

## 1. Scope and policy carried forward

This review reuses, without reopening or amending, the approved records:

- [`A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`](../decisions/A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md)
- [`A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`](../decisions/A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md)

The relevant approved contract is: use the NSE **NIFTY 50 PRICE INDEX** close for a named completed session; record an explicit evaluation cutoff with timezone/UTC offset; select the latest qualifying close demonstrably available by that cutoff; and use complete, valid trailing windows that include the evaluation session. `supportive` is strictly above both SMAs, `weak` strictly below both, and `neutral` is every other valid combination. Missing/invalid expected sessions are not skipped. Unqualified, incomplete, future, stale-under-the-approved-session-policy or unresolved-conflicting inputs yield `UNKNOWN`, with the reason preserved. Retrieval time is not publication time. No numeric publication-delay or freshness threshold is approved. If required NIFTY is `UNKNOWN`, do not issue Final.

This report evaluates evidence sufficiency only. It does not qualify the saved rendered captures, define a new rule, assign a category, alter the A16 personal-use scope, or change v1.5/v1.6/application behavior.

## 2. Review baseline and evidence forms

The checkout initially had local `HEAD` at `01ba66c12ca1195fd7acbd287c3e39a019808094` while the fixed remote branch was at `65de3bd91e6a56eaba8d724f22666ffc6b9100ed`. Before aligning it, all 269 paths in the fetched fixed-branch tree were verified to exist locally with matching Git blob bytes and file modes. Although the initial Git status showed many of those paths as untracked because the local branch pointer was stale, the only worktree path not present in the fetched fixed-branch tree was the unrelated authorization-request draft. The local branch was safely fast-forwarded to the already-published `65de3bd…` tip without changing the verified worktree contents. The draft remains untouched and unstaged. The following evidence review is based on that fixed-branch baseline.


The principal reusable artifacts are in [`evidence/market-observations/official-index-history-20261013/`](../../evidence/market-observations/official-index-history-20261013/):

- `A8-M-SMA-EVIDENCE-20261013.md` and `A8-M-EVIDENCE-FINDINGS.md`;
- `source-captures/response-capture-manifest.json` and its rendered JSON fragments;
- `nse-cm-session-calendar-validation-20261013.json` and the two rendered circular extracts;
- `nse-nifty50-close-observations-20251013-20261013.csv`, the two SMA CSVs, and the existing validation artifacts;
- the reused `nse-nifty50-20260701-20261013.json` file.

The capture manifest explicitly identifies the five new historical windows as `functions.fetch_page` **rendered JSON text fragments**, with local reconstructed JSON made by removing page-tool fences and joining fragments. It says `rawProviderResponseBytesCaptured: false`, `responseHeadersCaptured: false`, and `exactReceiptTimeCaptured: false`. It records `retrievedDate: 2026-10-13` but `retrievalTime: null` for those five windows. The reused 70-row July–October response has both retrieval fields null. Its local SHA-256 and the hashes of the fragments/reconstructed JSON identify retained workspace files only; they are not provider-response hashes.

Accordingly, the currently retained material does **not** include the original HTTP response body bytes, HTTP status, headers, content type, a server-side publication/receipt record, or exact retrieval instants for these captures. The local `source_record_index` in the normalized close CSV is an ordinal into a local saved/reconstructed response, not an NSE-issued record ID. The source manifest and hashes are useful for local file integrity and lineage, but do not authenticate provider bytes or establish historical availability.

### Source-route assessment

| Route | What the earlier inspection showed | Evidence boundary / qualification result |
|---|---|---|
| Official NSE historical-index API, `https://www.nseindia.com/api/historicalOR/indicesHistory` | `indexType=NIFTY 50`; response fields include `EOD_INDEX_NAME`, date-valued `EOD_TIMESTAMP`, `EOD_CLOSE_INDEX_VAL` and OHLC values. Five saved windows contain 175 rendered rows; the reused broad response contains 70 rows in descending session-date order, with 2026-10-08 as its latest session date. The official NIFTY 50 label plus the previously inspected NSE Indices FAQ supports the plain price-index identity rather than a TR series. | Plausible official content route, but retained rendered/local material is not provider-native evidence. `HI_TIMESTAMP` is present in inspected output but its meaning/timezone was not documented; it is not promoted to event, publication, receipt or revision time. No row ID or source-defined correction precedence was found. Not qualified for Final under the approved observation contract. |
| NSE Indices Historical Data interface | The prior review inspected the dynamic historical-data interface, but did not select an index and did not submit/download its historical CSV. Its page describes date/OHLC/close output and separately distinguishes a Total Returns section. | The exact interactive selection/result path remains unexercised. A proposed selection of plain `NIFTY 50` is not itself evidence that a downloaded row was received or available by a cutoff. |
| NSE Indices Daily Snapshot CSVs for 2026-10-09 and 2026-10-12 | The prior report records rendered CSV outputs with `Index Name`, `Index Date`, OHLC and closing value, with closes matching the targeted API display for each date. It identifies the dated files as `ind_close_all_09102026.csv` and `ind_close_all_12102026.csv`. | This is a content-level match between separate rendered outputs. The record does not establish independent underlying data provenance, exact original bytes, HTTP metadata, publication time or earlier cutoff availability. The targeted outputs were not retained as exact provider-byte captures. |
| Official holiday master, market-timings page and NSE special-session circulars | The prior calendar review used rendered NSE `CM` holiday-master entries for the bounded interval; the circular extracts support the 2025 Muhurat and 2026 Union Budget sessions. Ordinary equity hours were shown as 09:15–15:30 IST. | Supports session-date/timetable reasoning for the inspected period only. The holiday payload was not retained as provider bytes, and calendar/timetable evidence does not say when an EOD close was published or delivered. |
| Paid EOD / Historical Order & Trade products | Existing investigation documents a possible product route and the limits of the visible v1.19 text; no representative current Index Data file, SFTP receipt, or product-specific availability record is present. | Not a qualified substitute for the public rendered history. No sample, subscription, purchase, or NDAL request was made. No delivery guarantee or numeric timing rule is inferred. |

The old tail comparison is preserved at [`A8-M-SOURCE-QUALIFICATION-AND-AVAILABILITY-INVESTIGATION-DRAFT-2026-10-13.md`, §4.3 and §5](A8-M-SOURCE-QUALIFICATION-AND-AVAILABILITY-INVESTIGATION-DRAFT-2026-10-13.md). This review does not repeat the API-versus-snapshot comparison or reconstruct its responses.

## 3. Session date, calendar, weekends, holidays and special sessions

The saved calendar validation covers **2025-10-13 through 2026-10-08**. It records 259 weekday candidates, 15 weekday CM closures, 245 expected sessions, 245 observed unique sessions, and no missing expected or unexpected observed dates. The two noted special sessions are:

- **2025-10-21:** Diwali Muhurat normal market, 13:45–14:45 local exchange time, supported by NSE Circular `NSE/CMTR/70319 (124/2025)`; this date is a weekday candidate, not an extra weekend session.
- **2026-02-01 (Sunday):** Union Budget live session, normal market 09:15–15:30, supported by NSE Circular `NSE/CMTR/72349 (11/2026)`; this contributes the one Sunday session beyond the weekday candidates.

The count reconciles as 259 weekday candidates minus 15 weekday closures plus the 2026-02-01 Sunday session = 245 expected sessions. The calendar artifact reports all 245 closes present, finite, numeric and positive. That is a date/session and local-series validation through 2026-10-08; it does not establish provider-byte qualification, source completeness after that endpoint, or when any close became available. The circular extracts and calendar payload are rendered/local evidence, not original provider-byte captures.

Within this bounded interval, ordinary weekdays not listed as CM closures are candidate regular sessions; weekends are not regular CM sessions unless an official circular schedules a special session. A listed holiday does not override a later special-session notice. The 2026-11-08 Muhurat entry was described in the 2026-10-13 calendar inspection as having timings to be notified; no later calendar/circular retrieval was made in this review, so no newer timing claim is made.

Session date and time must remain distinct:

- NSE API `EOD_TIMESTAMP` is a **date field** in the inspected output; it carries no time or UTC offset. The Daily Snapshot `Index Date` and the dated filename likewise identify a date/report, not publication time.
- The API's `HI_TIMESTAMP` has no field specification in the retained investigation; do not assign it a timezone, event meaning, publication meaning or revision meaning.
- The regular-market timetable (09:15–15:30 IST) and special-session windows identify trading hours. They do **not** establish that the final index close is published at the session end.
- A local manifest field such as `retrievedDate` is capture metadata, not a source-provided timestamp. The saved records lack an exact retrieval time with timezone/offset.

## 4. Cutoff position and session-aware availability assessment

No evaluation-specific cutoff was supplied for this review. The report date, the session date, a page footer, and a local retrieval date are not interchangeable with that cutoff. Under the approved contract, each evaluation must carry its own explicit instant and timezone/offset.

| Cutoff/session position | What can be concluded from retained evidence | Approved fail-closed treatment |
|---|---|---|
| Before regular session completion or during the session | The applicable session timetable can identify the session window; no live/indicative value is established as the completed-session close. | Do not use a partial/in-progress value. A prior close is eligible only if it is still the latest qualifying completed session and the source evidence supports its availability/latest-session status at cutoff. |
| At/after the normal 15:30 IST close | 15:30 is the ordinary market close time, not a documented publication timestamp for the final index value. | Do not infer availability at 15:30 or add a fixed delay. Availability must be evidenced separately. |
| Weekend or declared CM holiday | The date calendar can show no regular session, subject to any special-session circular. | Do not apply a 24-hour or calendar-day fallback. A prior close may remain eligible only while it is the latest qualifying completed session and no newer close should have been available by cutoff. |
| Muhurat or other special session | The applicable circular can establish that a session was scheduled and its stated hours. | Use the special session only when the notice establishes it; do not assume regular hours or publication time. |
| A later close is retrievable now, but cutoff is earlier | A current rendered response or CSV can show that a value is retrievable at the inspection time/date. It cannot backdate publication or receipt. | Exclude it from an earlier cutoff unless contemporaneous source/receipt evidence proves availability by that cutoff. If the required latest close cannot be established, trend is UNKNOWN. |
| No expected row, conflicting revisions, future date/time, or ambiguous timezone | The retained public responses do not define revision precedence or enough timestamp semantics to compare all records with a cutoff. | Do not skip expected sessions, select an arbitrary revision, or interpret an undocumented timestamp. Preserve the issue and return UNKNOWN when it affects a required close/window. |

### Tail discrepancy and newer-close evidence

The retained broad query requested 2026-07-01–2026-10-13 but returned 70 rows in descending order, with 2026-10-08 as the latest session date. The prior report records separate targeted API and Daily Snapshot displays for 2026-10-09 (close **22,520.45**) and 2026-10-12 (close **22,363.35**), matching at the displayed-value level. It also records that a targeted 2026-10-09–2026-10-13 API rendering showed those two rows but no 2026-10-13 row at that inspection. The reason the broad response stopped at 2026-10-08 is unresolved. The earlier report's displayed page footer `13-Oct-2026 | 16:55 (IST)` is a page-footer string, not a response-receipt instant or per-file publication timestamp.

These later values were not appended to the 245-row close file and were not used to recalculate either SMA. The 245-row package therefore remains a validated descriptive series only through 2026-10-08; it cannot be treated as a qualified latest-session input for a later evaluation merely because its local calendar validation has no gaps through that earlier endpoint. The prior rendered 2026-10-09/12 results are not a new 2026-10-15 retrieval, and the old October 13 observation is not a cutoff-availability record.

The 2026-10-09/12 displayed matches prove neither independent source generation nor original provider bytes. A close date/value match, a saved local hash, presence in a history table now, or a file's date-named URL does not prove availability by an earlier cutoff. For a **newer close** to qualify for a specific cutoff, the evidence must tie the exact NIFTY 50 price-index/session close to a source identity and exact record/file bytes, establish the relevant source time semantics and revision identity, and show by a trustworthy source publication or recipient-availability/receipt timestamp (with timezone/offset) that it was available no later than that cutoff. Completeness evidence must also establish that no newer expected session close should have been available. A current retrieval can prove, at most, that the retrieved representation was exposed at that later retrieval; it cannot establish historical availability retrospectively.

## 5. Missing, conflicting, future and revised records

- **Missing expected session:** The bounded local validator reports no missing sessions through 2026-10-08, but the broader response's later tail omission and the targeted later records show why source-response coverage must be checked against the applicable calendar. If an expected close is missing or invalid in a required window, do not silently skip it or reuse a convenient older row; the approved result is UNKNOWN.
- **Conflicting records/revisions:** No stable provider record ID, revision identifier/order or source-defined correction precedence is established in the inspected API, daily snapshots or local files. If two records conflict for the same index/session, no local file order, retrieval order or matching displayed value supplies precedence. Preserve the conflict and return UNKNOWN unless authoritative revision evidence resolves it.
- **Future/impossible record:** A session date after the evaluation session/cutoff is not eligible. The current date-only `EOD_TIMESTAMP` cannot locate a value within a session, and undocumented `HI_TIMESTAMP` cannot be compared safely with the cutoff. If a required source timestamp is missing or its timezone/meaning is unresolved, do not infer it; return UNKNOWN when cutoff eligibility cannot be established.
- **Timezone:** Keep the date of the trading session, any source-native event timestamp and timezone, local receipt/retrieval instant and timezone, source publication time and timezone, and evaluation cutoff and timezone as separate facts. No timezone is inferred from the date string or from the local machine.

No record in this review is assigned a freshness age or numeric fallback. The existing generic elapsed-hour setting is not substituted for the approved session-aware policy.

## 6. Minimum evidence that would resolve availability

For a **prospective** cutoff, retain a source-native file/response body as exact bytes separately from headers and local capture metadata. Record the exact URL/parameters or product/version, retrieval/receipt timestamp with timezone/UTC offset, HTTP status, headers and content type where applicable, body/file byte length and SHA-256 of those exact received bytes, and any source-provided timestamp, record/file ID or revision marker. Label source-provided facts separately from local observations; a local hash authenticates only the bytes retained locally, not their origin.

Also obtain authoritative definitions for the exact record's index/close/session fields and every timestamp field, source-side availability/publication semantics, completeness/expected-file coverage, correction/revision precedence and applicable calendar/special sessions. A client receipt log can establish that exact bytes were received by a particular cutoff if its timestamp and linkage are trustworthy; it is not automatically the source's original publication time. To call a close the **latest** one, the evidence must also show complete coverage through the latest expected session and whether a newer close should already have been available. Market close time alone is not that proof.

For a **historical earlier cutoff**, a later download or current historical-table result is insufficient. The needed evidence is contemporaneous publication/availability or recipient receipt metadata (or equivalent source-native archive/log evidence) tied to the exact record and revision. If that evidence does not exist, historical availability remains unproven; do not synthesize a timestamp from the session date, retrieval date, market timetable or local hash.

## 7. Disposition and changes

| Question | Bounded finding as of this review |
|---|---|
| Is the official NIFTY 50 content route plausible? | Yes for displayed daily price-index values; not enough to qualify retained rows as provider-native Final inputs. |
| Are session dates deterministic in the validated historical interval? | Supported at the date/session level by the retained rendered CM calendar and two circular extracts for 2025-10-13–2026-10-08. |
| Is a deterministic publication/availability-by-cutoff rule established? | No. No per-record publication time, provider delivery/receipt log, exact captured HTTP response metadata, or source-backed delay rule is present. |
| Does current retrieval establish an earlier cutoff? | No. The latest retained retrieval observation is dated 2026-10-13, with exact time absent; no 2026-10-15 source retrieval was made. |
| Is a current NIFTY trend category assigned? | No. The approved UNKNOWN and required-NIFTY Final-withheld behavior remains unchanged. |
| Was the 245-close/SMA evidence altered? | No. It was reused unchanged; no records were appended and no SMA was recalculated. |
| Were code, configuration, schema, scoring or application behavior changed? | No. This publication adds an investigation report and a local review/check record only. |

A8-M remains **OPEN**. The session-date calendar evidence is not a substitute for source qualification or availability-by-cutoff evidence. No current NIFTY category, score or Final result is produced. No provider request, subscription, purchase, merge of a pull request, release or deployment is part of this work.

The companion local check record is [`a8m-session-availability-review-check-20261015.json`](../../evidence/market-observations/official-index-history-20261013/a8m-session-availability-review-check-20261015.json). It records the bounded checks and explicitly identifies itself as a local assessment artifact, not a new NSE source capture.
