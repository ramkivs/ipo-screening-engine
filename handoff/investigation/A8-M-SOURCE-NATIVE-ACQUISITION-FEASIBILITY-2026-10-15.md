# A8-M — Source-Native NIFTY Evidence Acquisition Feasibility

- **Assessment date:** 2026-10-15 (Asia/Kolkata)
- **Status:** Targeted feasibility review and intake preparation; no new source capture and no policy decision.
- **A8-M:** OPEN — source qualification / cutoff availability remain blocked.
- **Required branch:** `arena/573e69a4-ipo-screening-engine`

## Executive result

**Arena cannot make a direct source-native capture from the official NSE/NSE Indices hosts under its current outbound-host allowlist.** The allowlist permits only `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, and `files.pythonhosted.org`; it does not include `nseindia.com`, `www.nseindia.com`, `niftyindices.com`, `www.niftyindices.com`, or `nsearchives.nseindia.com`. No request was attempted in this review, so there is no new HTTP response, status, or request failure to report. No restriction was bypassed.

No external Windows or other explicitly permitted execution environment is connected or has been demonstrated here. A normal direct GET or official-page CSV download on a user-authorized machine is a **conditional acquisition route**, not a route proven available. The bounded capture/intake procedure is in [`A8-M-NIFTY-SOURCE-CAPTURE-AND-INTAKE-RUNBOOK-2026-10-15.md`](A8-M-NIFTY-SOURCE-CAPTURE-AND-INTAKE-RUNBOOK-2026-10-15.md). It covers a narrow 2026-10-09–2026-10-12 sample, preserves body/header/local metadata separately, stops on access challenges, and transfers a checksummed archive without assuming a shared filesystem.

Even if a current capture succeeds, **historical availability by an earlier evaluation cutoff remains unproved**. The retained public outputs show session dates and values, not a per-record publication time, a source-defined stable revision ID, or a contemporaneous receipt log. A current response hash or displayed-value match cannot backdate availability. The broader-query versus targeted 9/12 tail discrepancy also remains unresolved.

The existing 245 closes, 196 SMA-50 points and 46 SMA-200 points are reused unchanged. No source body was acquired, no row was appended, no SMA was recalculated, and no application/configuration/schema/scoring behavior changed. The approved NIFTY contract and required-NIFTY `UNKNOWN` → Final withheld rule remain unchanged.

## 1. Verified repository baseline and preserved state

The required local branch name was correct, but this execution checkout initially had `HEAD` at `01ba66c12ca1195fd7acbd287c3e39a019808094`; the fixed remote was already at the reported `d4df058d36aca0bd2a24145ef70467688023eb28`. After fetching the fixed branch, the local remote-tracking ref and `git ls-remote` both identified `d4df058…`. The two previously reported artifacts were present in the remote commit and their local Git blob IDs matched:

- `handoff/investigation/A8-M-SESSION-AVAILABILITY-QUALIFICATION-REVIEW-2026-10-15.md`
- `evidence/market-observations/official-index-history-20261013/a8m-session-availability-review-check-20261015.json`

Before aligning the stale local branch pointer, every one of the **271** paths in the fetched fixed-branch tree was verified present with matching Git blob bytes and file mode. The only worktree path absent from that tree was the unrelated authorization-request draft, SHA-256 `f5a5309cf2180913ec7b756d3e75c7442caf0d264b659bf75f7d7ab433d5238d`. The fixed branch was safely fast-forwarded to `d4df058…`; the draft was left untouched and unstaged. The A8-M investigation therefore starts from the verified fixed-branch commit, not the stale local `01ba66c` pointer.

## 2. Existing evidence reused, without repeating settled work

The scope was limited to acquisition and provenance feasibility. The prior reports and package were reused:

- The close package has **245** calendar-validated observations through **2026-10-08**. Existing outputs are **196 SMA-50** and **46 SMA-200** rows. No close or SMA series was recalculated or extended.
- `source-captures/response-capture-manifest.json` records five historical API windows as `functions.fetch_page` rendered JSON fragments. It records a retrieval **date** of 2026-10-13 but `retrievalTime: null`, with raw provider response bytes, response headers and exact receipt time all marked absent. The reused broad July–October response has no recorded retrieval date/time and its latest session date is 2026-10-08.
- The prior source-qualification report documents the 2026-10-09 and 2026-10-12 API/Daily Snapshot displayed-value matches and the earlier broad-query tail gap. This report does not re-download, reconstruct, or repeat that comparison.
- The approved trend and observation/UNKNOWN decisions remain the policy authority. The prior 2026-10-15 session-availability report and its companion check JSON are retained unchanged.

The repository’s documented NIFTY capture artifacts are page-tool rendered fragments and local manifests. The general `handoff/delivery/stage-downloads.sh` utility creates transports for tracked repository content; it is not an NSE source fetcher or market-data capture mechanism. No dedicated NSE HTTP/file downloader or source-byte intake script was found in the reviewed repository documentation and evidence paths.

## 3. Official source surfaces assessed

| Official surface | Acquisition mechanism and bytes | Close/session fields in prior evidence | Publication, identity and revision metadata | Arena feasibility / result |
|---|---|---|---|---|
| NSE historical-index API: `https://www.nseindia.com/api/historicalOR/indicesHistory` | The documented endpoint URL uses `indexType`, `from` and `to` query parameters; whether a plain unauthenticated client is accepted was not tested. The saved evidence came from rendered page-tool text, not a direct retained HTTP body. A direct GET with separate body and headers could capture an HTTP response body on a permitted host, but that was not attempted here. | Prior rendered output has `EOD_INDEX_NAME = NIFTY 50`, date-valued `EOD_TIMESTAMP`, OHLC and `EOD_CLOSE_INDEX_VAL`. `HI_TIMESTAMP` is present but undocumented in the retained material. | No established per-row publication timestamp, stable record ID, source-defined revision marker or precedence. A date field is not a publication instant. | Host is outside Arena’s allowlist. No source-native bytes, headers or response status obtained.
| NSE Indices Historical Index Data interface: `https://www.niftyindices.com/reports/historical-data` | The earlier review inspected the interface, but did not exercise the selector/download. It exposes a Historical Index Data section, CSV control and a separate Total Returns section. A normal browser download, if available, would preserve the downloaded file bytes; exact current behavior remains untested. | The interface describes date/OHLC/close output. The intended selection is plain NIFTY 50 price index, not Total Returns. | The earlier inspection found no per-record publication time, immutable row ID or revision-precedence description. A downloaded file/date label would not itself prove earlier availability. | Host is outside Arena’s allowlist. Conditional manual UI route only in an explicitly permitted environment.
| NSE Indices Daily Reports and dated Daily Snapshot CSVs: `https://niftyindices.com/reports/daily-reports` and `/Daily_Snapshot/ind_close_all_DDMMYYYY.csv` | The prior report identifies dated CSV links for 2026-10-09 and 2026-10-12 and rendered their contents. A normal direct GET or official download control could save a CSV response body and separate response headers if the host allows it. No exact CSV body/header capture is present in this repository. | Prior rendered CSVs show `Index Name`, `Index Date`, OHLC and close. For 9/12 October their displayed closes match the prior targeted API display. | The date/file name identifies the session/report date. The retained rows do not contain publication/receipt timestamps, a stable record ID or documented revision precedence. HTTP `Date`, `Last-Modified` and `ETag`, if returned by a future capture, must be preserved but not assigned those meanings without documentation. | Host is outside Arena’s allowlist. The direct-file route is a plausible byte-capture candidate elsewhere, not proven available from Arena or from a Windows host in this review.
| Official calendar, holidays, timings and special-session circulars | Existing material consists of rendered holiday-master extracts and rendered extracts of official NSE circulars; no original calendar/API/PDF bytes or HTTP headers were captured in the retained package. | Supports session-date and stated-hours findings for the previously checked interval, including 2025-10-21 Muhurat and the 2026-02-01 Sunday session. Ordinary equity hours were shown as 09:15–15:30 IST. | Calendar/circular dates and trading hours do not specify when the final index close was published, delivered or received. | `nseindia.com` and `nsearchives.nseindia.com` are outside Arena’s allowlist. Prior date evidence is reused; no new calendar retrieval was made.

The allowed-host list is an execution-policy restriction, not a measured DNS failure or an HTTP response. Since no source request was attempted, the report does not claim a 403, timeout, or other source-side failure. Previous page-tool access to rendered text does not establish that this execution has permission or capability to capture direct provider bytes.

## 4. Finding classification

| Finding | Classification | Boundary |
|---|---|---|
| Official rendered API output names `NIFTY 50` and exposes date/close fields; official rendered calendar/circular extracts show session dates and stated hours. | **Source-native fact directly evidenced** in the previously inspected official-source content. | The evidence form is rendered/local text; original provider/PDF bytes and their hashes are not retained, so this is not authenticated source-byte capture. |
| The five-window manifest records retrieval date 2026-10-13 and null exact retrieval time; the reused broad response has no retrieval timestamp. | **Local retrieval observation.** | Manifest metadata only; not source-provided publication time or proof of earlier availability. |
| The prior report’s 9/12 API and Daily Snapshot outputs display matching close values. | **Rendered-content comparison.** | The output bodies were not retained as exact provider bytes; independent underlying generation is not established. |
| A permitted external machine might save the public API/CSV bodies and response headers using an ordinary, non-authenticated GET or official page download. | **Inference / conditional feasibility.** | No external environment was connected or tested. If blocked or challenged, stop; do not bypass access controls. |
| Whether an observation was available by an earlier cutoff; what `HI_TIMESTAMP` means; stable record/revision identity and precedence; why the broad query stopped at 2026-10-08 while targeted outputs showed 9/12 October; whether any response header denotes publication. | **Unresolved.** | No contemporary publication/receipt records or applicable source definitions are present. |

## 5. Publication/availability and the 9/12 October discrepancy

The latest retained retrieval observation is the earlier page-tool inspection dated **2026-10-13**; exact retrieval time is absent. The targeted 9/12 results were described in the prior report as rendered page-tool output, not saved response-byte captures. There was no new retrieval on 2026-10-15. Consequently:

- The prior rendered values show what the tool displayed during that inspection; they do not establish the source’s first publication time or recipient receipt time.
- The local query/capture manifest has no original HTTP status/headers for the reused broad response, no exact retrieval instant, and no source-side publication log.
- `EOD_TIMESTAMP` and Daily Snapshot `Index Date` are session dates. `HI_TIMESTAMP` remains undocumented. None can be treated as publication time.
- A present-day response, current CSV, body hash, matching value, server `Date` header or date-named filename cannot establish availability at a prior evaluation cutoff without relevant source definitions and contemporaneous evidence.

The discrepancy remains **OPEN**: the broad request for 2026-07-01–2026-10-13 returned 70 observations with **2026-10-08 as its latest session date**, while prior targeted rendered outputs showed 2026-10-09 and 2026-10-12. Its cause is not established. Re-running a query now could show current behavior but cannot reconstruct the original response or establish when the later values first became available. The smallest evidence that could resolve its historical aspect is the original broad-request body/headers/receipt log from the time it was made, or source-side publication/version records tied to those records; none is present in the existing package.

To establish availability by a particular earlier cutoff, the evidence must link (a) the exact NIFTY 50 price-index close and session, (b) source identity and record/file revision, and (c) a trustworthy source publication or recipient-availability/receipt instant no later than the explicit cutoff, all with documented timezone/semantics. To select the **latest** eligible close, it must also establish complete expected-session coverage and whether a newer session’s close should have been available. A capture made later can support only the later retrieval observation unless contemporaneous historical evidence accompanies it.

## 6. Session-calendar feasibility

The existing validator covers 2025-10-13 through 2026-10-08: 259 weekday candidates, 15 weekday CM closures, and one Sunday special session yield 245 expected sessions; 245 were observed with no missing or unexpected dates in that bounded local series. The two retained special-session extracts identify 2025-10-21 Muhurat hours and the 2026-02-01 Sunday Union Budget session. This supports a bounded **session-date** sequence, subject to the rendered-evidence limitation. It does not establish current/future calendar coverage or close-publication time.

The normal 09:15–15:30 IST schedule is not a publication guarantee. A prior close may remain eligible on a weekend or holiday only if it is still the latest qualifying completed session and evidence supports that no newer close should have been available at cutoff. A special session must be supported by its own applicable official notice. The publication/availability branch is unsupported; therefore the combined deterministic, testable session-aware availability rule is **not currently established**. No numeric delay, 24-hour fallback, or new runtime semantics is introduced.

## 7. Qualification prerequisites and smallest next action

The evidence blocker is now specific:

1. **Environment:** Arena’s allowed outbound hosts exclude all identified NSE/NSE Indices source hosts. No explicitly permitted external environment is connected or verified.
2. **Native capture:** no original API or CSV response bytes, HTTP status/headers/content type, exact local retrieval time, source file identity, or body-byte hash exists for the targeted 9/12 October output.
3. **Historical availability:** no provider publication record or contemporaneous receipt log tied to those observations and an earlier cutoff exists in the package.
4. **Source semantics:** publication-time field semantics, stable record/revision identity, correction precedence and complete latest-session behavior remain undocumented/unresolved in the retained evidence.
5. **Tail completeness:** the broad-vs-targeted result has no original request/response metadata or established cause.

**Smallest next action:** Ramki identifies a Windows or other machine whose owner/network policy explicitly permits ordinary HTTPS access to the named official hosts, then runs the bounded runbook for the 2026-10-09–2026-10-12 API and Daily Snapshot objects. Transfer the resulting ZIP and separate SHA-256 sidecar through an approved attachment/storage mechanism; do not assume a shared filesystem. Separately search only for already-existing contemporaneous download/receipt/publication logs relevant to the earlier cutoff. If none exist, record historical availability as unprovable for that cutoff; do not seek a provider response or purchase access under this task.

A8-M remains **OPEN / BLOCKED — SOURCE QUALIFICATION**. No current category is assigned, the approved price-index/session/SMA semantics remain unchanged, and required NIFTY `UNKNOWN` continues to withhold Final.
