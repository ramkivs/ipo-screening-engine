# A8-M — Minimal NIFTY Source-Capture and Intake Runbook

**Status:** Conditional procedure only. It was not run in Arena and is not a source capture, source-qualification decision, provider request, subscription, or purchase.

## 1. Permission and stop conditions

Use this only on a Windows or other machine whose owner/network administrator has explicitly permitted ordinary HTTPS access to the official NSE/NSE Indices hosts. Do **not** run it in the Arena checkout: its current outbound allowlist excludes those hosts. Do not bypass a block with a VPN, unapproved proxy, browser-cookie copying, spoofed browser headers, TLS verification disablement, hidden endpoints, DevTools/WebSocket, CAPTCHA handling, retries, or authentication. Whether an ordinary unauthenticated client is accepted has not been established. Do not supply credentials; if a host is blocked, returns a challenge/login page, or requires authentication or another unapproved access method, save the response/error once and stop.

This procedure captures a present-day representation. A successful GET or browser download does **not** establish that the record was published or available by a past evaluation cutoff.

## 2. Bounded official-source sample

The smallest sample addressing the known tail and missing original bytes is the existing targeted interval **2026-10-09 through 2026-10-12**—not another broad history pull:

1. **NSE historical API** (one GET, exact query):
   `https://www.nseindia.com/api/historicalOR/indicesHistory?indexType=NIFTY%2050&from=09-10-2026&to=12-10-2026`
2. **NSE Indices Daily Reports page:**
   `https://niftyindices.com/reports/daily-reports`
3. **Dated Daily Snapshot files** previously rendered for the two dates:
   - `https://niftyindices.com/Daily_Snapshot/ind_close_all_09102026.csv`
   - `https://niftyindices.com/Daily_Snapshot/ind_close_all_12102026.csv`
4. **Optional historical-form export** if needed to test that interface specifically: open `https://www.niftyindices.com/reports/historical-data` in a normal browser; choose **Historical Index Data**, the plain **NIFTY 50** price index (not Total Returns), and 2026-10-09 through 2026-10-12; use the page's own CSV/download control. Save the downloaded file unchanged. Do not use browser internals or an undocumented endpoint.

The targeted sample is for byte/provenance acquisition only. Do not append it to the existing 245-close input, recalculate an SMA, or repeat the previous displayed-value comparison. If the intended observation/cutoff differs, stop and specify the exact session and evaluation cutoff before broadening the sample.

## 3. Direct HTTP capture (PowerShell with `curl.exe`)

Run on the explicitly permitted machine. `curl.exe` must use normal certificate validation. The commands below make one GET per URL: they do not follow redirects, retry, send cookies, request compressed content, or disable TLS checks. `--dump-header` and `--output` keep response headers and body in separate files. `curl` removes HTTP transfer framing; without `--compressed`, it does not request content decompression. These are saved HTTP response-body bytes, not TLS/TCP wire bytes. Preserve any `Content-Encoding` header and do not transform the body.

```powershell
$ErrorActionPreference = 'Stop'
$CaptureRoot = Join-Path $PWD ('A8M-NIFTY-capture-' + [DateTimeOffset]::Now.ToString('yyyyMMddTHHmmsszzz').Replace(':',''))
New-Item -ItemType Directory -Path $CaptureRoot | Out-Null

function Save-OfficialGet([string]$Name, [string]$Url) {
    $bodyPath = Join-Path $CaptureRoot ($Name + '.body.bin')
    $headersPath = Join-Path $CaptureRoot ($Name + '.headers.txt')
    $stderrPath = Join-Path $CaptureRoot ($Name + '.curl-stderr.txt')
    $metaPath = Join-Path $CaptureRoot ($Name + '.local-metadata.json')
    $curlVersion = (& curl.exe --version | Select-Object -First 1)
    $started = [DateTimeOffset]::Now
    $writeOut = & curl.exe --silent --show-error --max-time 45 `
        --dump-header $headersPath `
        --output $bodyPath `
        --write-out 'http_code=%{http_code}\ncontent_type=%{content_type}\nurl_effective=%{url_effective}\n' `
        $Url 2> $stderrPath
    $exitCode = $LASTEXITCODE
    $finished = [DateTimeOffset]::Now

    $bodyBytes = $null
    $bodySha256 = $null
    if (Test-Path $bodyPath) {
        $bodyBytes = (Get-Item $bodyPath).Length
        $bodySha256 = (Get-FileHash $bodyPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $meta = [ordered]@{
        captureName = $Name
        requestMethod = 'GET'
        requestUrl = $Url
        localRetrievalStart = $started.ToString('o')
        localRetrievalEnd = $finished.ToString('o')
        localTimezoneOffset = $started.Offset.ToString()
        systemClockSynchronization = 'Not independently verified; record the machine time-sync status if known.'
        curlVersion = $curlVersion
        curlExitCode = $exitCode
        curlWriteOut = ($writeOut -join "`n")
        responseHeadersFile = [IO.Path]::GetFileName($headersPath)
        responseBodyFile = [IO.Path]::GetFileName($bodyPath)
        responseBodyBytes = $bodyBytes
        responseBodySha256 = $bodySha256
        bodyHashScope = 'SHA-256 of the exact body file saved by curl.exe; not a provider signature or historical-availability proof.'
        stderrFile = [IO.Path]::GetFileName($stderrPath)
        redirectFollowed = $false
        retries = 0
        cookiesOrAuthenticationUsed = $false
        contentDecompressionRequested = $false
        tlsVerificationDisabled = $false
    }
    $meta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $metaPath -Encoding UTF8
    Write-Host "$Name : curlExit=$exitCode ; $($meta.curlWriteOut) ; bodyBytes=$bodyBytes ; sha256=$bodySha256"
    Write-Host "Headers: $headersPath ; body: $bodyPath ; local metadata: $metaPath"
}

Save-OfficialGet 'api-tail-20261009-12' 'https://www.nseindia.com/api/historicalOR/indicesHistory?indexType=NIFTY%2050&from=09-10-2026&to=12-10-2026'
Save-OfficialGet 'daily-snapshot-20261009' 'https://niftyindices.com/Daily_Snapshot/ind_close_all_09102026.csv'
Save-OfficialGet 'daily-snapshot-20261012' 'https://niftyindices.com/Daily_Snapshot/ind_close_all_12102026.csv'
```

`curl.exe`'s header file and `--write-out` output are local client observations. Preserve them verbatim as produced; do not label an HTTP `Date` header as per-record publication time. Preserve `Last-Modified`, `ETag`, `Age`, `Cache-Control`, `Content-Length`, `Content-Type`, `Content-Encoding`, `Content-Disposition`, status lines and any redirect response if present. These headers are potentially useful metadata, but their meaning and any relationship to a particular close/revision must not be inferred without source documentation.

Inspect status/content type only after capture. A 3xx, 4xx/5xx, empty body, HTML challenge, or unexpected content is a recorded outcome, **not** a reason to retry with cookies or browser-like headers. Do not treat an error/challenge body as market data. If `curl.exe` is unavailable or the normal GET is blocked, use only the official page's ordinary UI if that route is explicitly permitted; otherwise stop and record the limitation.

### Historical Index Data UI fallback

If the form is used, preserve the downloaded file byte-for-byte under its original download name. Record the exact page URL, selected section (`Historical Index Data`), selected index label, date range, browser/download time with timezone, local byte length and SHA-256. If the browser does not expose response status/headers/content type through its ordinary download information, mark them **not captured**. Do not open/save the CSV through a spreadsheet, which may reserialize it. A UI download supplies current file bytes; it does not supply a publication timestamp unless the source explicitly provides one.

## 4. Intake manifest and evidence separation

Keep each response body/file, response headers, local metadata, and any notes in separate files. A compact capture directory should contain:

```text
A8M-NIFTY-capture-<local-time-offset>/
  api-tail-20261009-12.body.bin
  api-tail-20261009-12.headers.txt
  api-tail-20261009-12.local-metadata.json
  daily-snapshot-20261009.body.bin
  daily-snapshot-20261009.headers.txt
  daily-snapshot-20261009.local-metadata.json
  daily-snapshot-20261012.body.bin
  daily-snapshot-20261012.headers.txt
  daily-snapshot-20261012.local-metadata.json
  optional-historical-ui-original.csv
  capture-notes.txt
```

For every item, record separately:

- **Local observations:** retrieval start/end time including UTC offset, machine/time-sync status if known, tool/version, exact requested URL/parameters, HTTP status and saved response headers if available, saved filename, byte length, hash algorithm/digest, and any error/redirect/challenge.
- **Source-provided content:** index label, session-date field/value, close field/value, any source timestamp, record/file ID or revision marker exactly as present. Preserve the original spelling/value. Do not promote `EOD_TIMESTAMP` (a date in the previously inspected output) or undocumented `HI_TIMESTAMP` into publication or availability time.
- **Interpretation/unknowns:** explicit notes on source field semantics, completeness, absent fields, and whether the source documents revision precedence. Keep `Date`, `Last-Modified` and `ETag` as response metadata unless a source specification establishes their meaning for the observation.

Do not place headers into the body file or reconstruct JSON/CSV before hashing. A local hash identifies the bytes actually received and saved; it does not authenticate the provider or prove a historical publication time.

## 5. Historical availability is a separate evidence request

A capture made today can show that the returned representation was retrieved today, subject to the local clock and captured response metadata. It cannot establish that the same close was available by an earlier evaluation cutoff. To resolve an earlier cutoff, add only contemporaneous records that already exist—such as source publication logs, an original download/receipt log, or archived response metadata—unaltered and with their source, timestamp/timezone, exact record/file linkage, and integrity details. Do not manufacture or backdate these records. If no contemporaneous evidence exists, record `historicalAvailabilityByCutoff: unresolved`.

The API date field, Daily Snapshot `Index Date`, date-named filename, local retrieval time, present-day `Date`/`Last-Modified` header, or current matching values alone are not proof that a close was available earlier. A source-defined stable revision ID and documented precedence are still needed to resolve corrections/conflicting records. To call a close the *latest* eligible one, also establish complete expected-session coverage and whether a newer close should have been available by the cutoff; do not use a numeric delay or elapsed-hour fallback.

## 6. Transfer from an independent machine to Arena

Do not assume the Windows machine and Arena share a filesystem. After capture, leave the original files untouched and create a ZIP plus a separately transferable ZIP checksum:

```powershell
$ZipPath = "$CaptureRoot.zip"
Compress-Archive -Path (Join-Path $CaptureRoot '*') -DestinationPath $ZipPath
$ZipHash = (Get-FileHash $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$ZipHash  $(Split-Path $ZipPath -Leaf)" | Set-Content -LiteralPath ($ZipPath + '.sha256') -Encoding ASCII
```

Transfer both files using an explicitly approved upload/attachment or storage mechanism; do not publish through an unapproved public link. If no approved transfer channel is available, stop and report that blocker. In Arena, verify the ZIP against the separately transferred `.sha256` file before extraction, then verify every body/file length and SHA-256 against the included local metadata. Preserve the received ZIP and extracted files; do not overwrite the existing 245-close package. A checksum match proves transfer integrity only, not source authenticity or historical availability.

## 7. Stop / handoff result

After an authorized run, report one of: (a) exact official files and response metadata captured, with limitations; (b) exact HTTP status/error/challenge captured and no bypass attempted; or (c) no authorized execution/transfer environment available. In every case, keep A8-M qualification blocked unless source identity, complete expected-session data, source/revision semantics, and availability by the explicit evaluation cutoff are all evidenced. Do not assign a category or change runtime behavior as a consequence of this capture.
