# Windows discovery outcome: root cause of the 3fea259 acceptance failure and its repair — 2026-10-18

> **SUPERSEDED IN PART (2026-10-18, later the same day).** The repair
> described in §4 of this record was itself **rejected by a second
> Windows acceptance** (ingestion `ing-32ddf313bbe247b0`, branch head
> `0dda109`): the same classification contradiction — BSE classic =
> JavaScript shell, BSE `publicissue.html` = JavaScript shell, SEBI =
> HTTPError, aggregate official-discovery = **NOT_FOUND**, activity
> completion = **UNPUBLISHED** — persisted. The round-1 rule still
> read *page chrome* as *issue entries*, only through a different
> predicate. **§0 below records the second failure, the actual root
> cause and the corrected repair**; §4.1, §6 and §7 have been updated
> accordingly. §1–§3 and §5 remain the (superseded) round-1 record
> and are kept as history.

---

# §0. The second Windows acceptance failure and the actual root cause

## 0.1 The reported failure (authoritative acceptance evidence)

Windows runtime, checkout exactly at
`0dda1093040cfe8a3217160d1b21665f2902a519` (PR #6 head, clean tree,
API restarted, startup OK), ingestion `ing-32ddf313bbe247b0`:

| # | Observed | Where it comes from |
|---|---|---|
| 1 | BSE classic listing URL → JavaScript shell, listing not searched | provider note: `…: returned a JavaScript application shell with no issue rows in the served HTML (a listing was not searched)` |
| 2 | BSE `publicissue.html` → JavaScript shell, listing not searched | same note text |
| 3 | SEBI listing → HTTPError | provider note: `…: listing retrieval failed (HTTPError)` |
| 4 | Aggregate official-discovery outcome **NOT_FOUND** | `OfficialDiscoveryProvider.find` |
| 5 | Activity completion **UNPUBLISHED** | `IssueTermsResolver.resolve` → `official_discovery/completed` |
| 6 | Required issue terms remain unresolved | `term_resolution` events |
| 7 | Evaluation not run; persistence not attempted | `evaluation/not_run`, `persistence/not_attempted` |

**Exactly three per-source failure events** appear in the trace — one
per unusable source. The fourth configured source, the NSE listing,
emits **no** event at all.

## 0.2 Which source set `listing_searched = true` (proved, not inferred)

The four configured listing sources
(`OfficialDiscoveryProvider.LISTING_URLS`) and what each did at
`0dda109`:

| # | Listing URL | Windows response | `_classify_listing` at `0dda109` | Note emitted? | Counted as searched? |
|---|---|---|---|---|---|
| 1 | `https://www.nseindia.com/market-data/all-upcoming-issues-ipo` | HTTP 200, site-wide chrome + client-side listing table, **no issue row** | **`ok`** | **no** | **yes** |
| 2 | `https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P` | JavaScript application shell | `shell` | yes | no |
| 3 | `https://www.bseindia.com/publicissue.html` | JavaScript application shell | `shell` | yes | no |
| 4 | `https://www.sebi.gov.in/sebiweb/home/handleAction?doListing=yes&sid=1&ssid=7&smid=0` | HTTPError | (exception) | yes | no |

At `0dda109` **only** a response classified `ok` set
`reached = True`, and `reached` is the sole precondition for the
NOT_FOUND report and for `listing_searched=True`. Three of the four
sources are accounted for by the three failure events; the remaining
one — the **NSE listing** — is therefore the source that was
classified `ok`, i.e. the source that set `listing_searched = true`
and produced the false NOT_FOUND and the false UNPUBLISHED.

**This is not inferred from the absence of an event.** It is proved
by the code path (`kind == "ok"` → `reached = True` → NOT_FOUND →
`listing_searched=True`) plus the fact that every other source
emitted its own failure event. The invisibility is itself a defect:
the `ok` path emitted no note, so a source could contribute to the
aggregate outcome with no trace of its own — which is why the defect
survived one acceptance round.

## 0.3 The faulty predicate, and the proof that it fires on the real response

At `0dda109` the recognition of "a listing was really searched" was
(`engine/ipo_screening/issue_terms.py`):

```python
    @classmethod
    def _has_issue_entries(cls, text: str) -> bool:
        if cls._per_issue_links(text):        # <-- the faulty branch
            return True
        for table in re.findall(r"<table\b.*?</table>", text, re.DOTALL):
            …

    @classmethod
    def _per_issue_links(cls, text: str) -> List[str]:
        return [
            href
            for href in re.findall(r"href\s*=\s*[\"']([^\"']*)[\"']", text, re.IGNORECASE)
            if any(marker in href for marker in cls._PER_ISSUE_LINK_MARKERS)
        ]
```

`_PER_ISSUE_LINK_MARKERS` =
`displayipo, acqdisp, attachdocs, issue-information, issue_information,
price-band, price_band`.

The branch is unconditional and **document-wide**: a single `href`
carrying one of those tokens anywhere in the response — in the
site-wide navigation menu, in a `<link rel="canonical">` element, in a
language-alternate list — is accepted as proof that the listing's
issue records were read.

**Proof against the real response** (run with the exact `0dda109`
code, `git archive 0dda109`, and the retained real NSE capture
`evidence/ipo-subscription/vnl-20261011/vnl-issue-information.html`,
313,038 bytes, captured 2026-10-11):

```
0dda109 classification of REAL retained NSE response (313 KB)    -> 'ok'
        per-issue hrefs matched by 0dda109 : 17
            /market-data/issue-information?series=eq&amp;symbol=vnl
            https://www.nseindia.com/market-data/issue-information?series=eq&amp;symbol=vnl
            …
        <td> cells in the response         : 0

0dda109 classification of NSE listing response w/ real chrome    -> 'ok'
        per-issue hrefs matched by 0dda109 : 1
            /market-data/price-bands-surveillance-actions
        <td> cells in the response         : 0
```

The matched hrefs are **page chrome**, not issue records:

* `…/market-data/price-bands-surveillance-actions` — the site-wide
  market-data menu item, literally
  `<a class="nav-link" role="menuitem" id=Price Bands &amp; Surveillance
  Actions href="/market-data/price-bands-surveillance-actions">`;
* `…/market-data/issue-information?series=EQ&symbol=VNL` — the
  `<link rel="canonical">` and `<link rel="alternate" hreflang=…>`
  metadata of the page itself, plus its 13 language variants.

Meanwhile the real response carries **no issue record at all**: 2
tables, 4 `<tr>` rows, **0 `<td>` cells**. The NSE listing table is
filled client-side; the served HTML has the header row
("Company Name | Security type | Issue Start Date | Issue End Date |
Status | NSE Bid Details") and no issue row.

**So the round-1 predicate still mistook the *page* for a *listing* —
it only moved the test from "marker substrings" to "href substrings",
and the chrome satisfies both.** The round-1 regression fixture
(`NSE_MARKER_ONLY_LISTING`) modelled the NSE response *without* the
site-wide menu and canonical/alternate chrome, so it could not
reproduce the real response; the fixture was unfaithful, and the
acceptance failed.

## 0.4 The corrected repair

### 0.4.1 A response counts as a searched listing only if it carries an ISSUE RECORD

`OfficialDiscoveryProvider._issue_records()` (new) extracts the rows
that really are issue records:

* a **table data row** (`<tr>` containing `<td>` cells) that links to
  one issue or to one official document (`DisplayIPO`, `ACQDisp`,
  `attachdocs`, `issue-information`, `price-band` …) — matched on
  **anchor** elements only, so `<link rel="canonical">` metadata can
  no longer count; or
* a **table data row of an issue-listing table** (a table whose header
  names ≥ 2 issue-listing columns: Security Name / Company Name /
  Exchange Platform / Start Date / End Date / Issue Start Date /
  Issue End Date / Issue Status / Offer Price / Price Band / Market
  Lot / Issue Size / No. of Shares / Bid Lot / Issue Period / Issue
  Name / Issue Type / Face Value / Type of Issue) that carries an
  issue date (`21-10-2026`, `21/10/2026`, `21 Oct 2026`, `October
  2026`).

Navigation, menus, canonical/alternate metadata and language
switchers are never inside a data row, so they can no longer stand in
for an issue record. A page whose listing table is filled client-side
carries no record → `empty` → unusable.

The synthetic fixtures that modelled a listing as *bare anchors
outside any table* (`LISTING_WITH_NOTICE`, `LISTING_WITH_PROSPECTUS`,
`BSE_LISTING`, `JIO_LISTING_WITH_PROSPECTUS`) were remodelled to the
shape the exchanges really serve — issue records in the listing
table's rows. No real listing serves bare anchors, and such a page
is indistinguishable from chrome. The genuine-listing positive cases
(the live BSE row shape, the recorded BSE classic listing, the
recorded genuine listing) are unchanged and still classify `ok`.

### 0.4.2 NOT_FOUND must carry evidence, not a flag

`ProviderReport` now carries, besides `listing_searched`:

* `sources`: one `ListingAttempt` per configured listing URL —
  `url`, `classification` (`ok`/`empty`/`homepage`/`shell`/`failed`),
  `searched`, `issue_entries`, `detail`; and
* `searched_listings`: the URLs of the listings that were really read.

The resolver maps a NOT_FOUND report to UNPUBLISHED only when the
report is substantiated **and** names what it read:

```python
searched = any(
    r.outcome == "NOT_FOUND" and r.listing_searched and r.searched_listings
    for r in outcome.provider_reports
)
outcome.status = "UNPUBLISHED" if searched else "UNAVAILABLE"
```

A report that claims a search but names no listing is treated as
unsubstantiated and yields UNAVAILABLE.

### 0.4.3 No source may contribute invisibly

* The provider now records an attempt for **every** configured source,
  including the ones it searched.
* The service emits **one activity event per source** (status
  `SUCCEEDED` for a listing that was really read, `FAILED` for one
  that could not be used), each naming the URL, its classification
  and how many issue entries were read.
* The provider event's details carry the full attempt list, and the
  API payload carries `providers[].sources` and
  `providers[].searched_listings`.
* The official-source diagnostics panel in the UI lists every source
  with its classification and whether its listing was really searched.
* A candidate document that could not be used is no longer discarded
  silently: its reason is kept as a note and emitted as an event.

## 0.5 Regression coverage added for the second failure

* `tests/test_official_discovery.py`
  * `test_real_nse_response_is_not_a_searched_listing` — the **retained
    real NSE response** (313 KB) and the listing response built from
    its real site-wide header: both are not a searched listing, both
    carry the chrome that broke `0dda109`, and the `0dda109` rule is
    kept in the test to show that it called both `ok`.
  * `test_windows_trace_pattern_with_real_nse_response_is_unavailable`
    — the exact second-failure pattern (real NSE response, two BSE
    JavaScript shells, SEBI HTTPError) → provider UNAVAILABLE,
    `listing_searched` false, no searched listing, four attempts,
    resolver UNAVAILABLE.
  * `test_every_configured_source_produces_a_visible_attempt` — the
    failed source and the searched source are both visible; the
    searched listing is named.
  * `test_not_found_without_a_named_searched_listing_is_never_unpublished`
    — a NOT_FOUND report with the flag but no evidence → UNAVAILABLE.
  * `test_genuine_listing_searched_is_named_in_the_report` — the
    positive case is retained: a genuine listing really read, with no
    matching issuer, is NOT_FOUND and names every listing it read.
* `tests/test_ingestion_activity.py`
  * `test_windows_trace_pattern_is_unavailable_end_to_end` — service,
    resolver and activity trace: UNAVAILABLE, all four sources named
    with their own events (including the NSE one that used to be
    silent), no UNPUBLISHED anywhere, terminal BLOCKED,
    evaluation/persistence SKIPPED, nothing persisted.
  * `test_windows_trace_pattern_is_unavailable_through_the_api` — the
    API carries `status = UNAVAILABLE`, `listing_searched = false`,
    `searched_listings = []`, four source records and no UNPUBLISHED.
* `frontend/test/manual-terms.test.js` — the official-source
  diagnostics list every source with its classification and whether
  its listing was really searched, and never show UNPUBLISHED.

**Pre-fix verification (the regressions really reproduce the reported
failure).** The new tests were executed against the **exact `0dda109`
engine** (`git archive 0dda109` into a scratch tree, imported ahead of
the working engine):

```
$ PYTHONPATH=/tmp/old-0dda109/engine:engine python -m pytest \
      tests/test_official_discovery.py -q \
      -k "real_nse_response or windows_trace_pattern_with_real_nse or visible_attempt or unsubstantiated"
module under test: /tmp/old-0dda109/engine/ipo_screening/issue_terms.py
has ListingAttempt (0dda109?): False

FAILED test_real_nse_response_is_not_a_searched_listing
    assert OfficialDiscoveryProvider._classify_listing(real) != "ok"
    assert 'ok' != 'ok'          # the real 313 KB NSE response classified as a searched listing
FAILED test_windows_trace_pattern_with_real_nse_response_is_unavailable
    assert report.outcome == "UNAVAILABLE"
    assert 'NOT_FOUND' == 'UNAVAILABLE'   # the reported Windows contradiction, reproduced
FAILED test_every_configured_source_produces_a_visible_attempt
FAILED test_not_found_without_a_named_searched_listing_is_never_unpublished
4 failed, exit code 1
```

With the repaired engine the same tests pass (see the results table
below). The second failure is therefore reproduced deterministically
from the **real** NSE response — no Windows machine required.

### 0.7 Test results for this repair (all run locally, output visible)

| Run | Command | Result | Exit code |
|---|---|---|---|
| Focused discovery + activity + resolver + runtime + Windows-retrieval + cross-IPO | `.venv/bin/python -m pytest tests/test_official_discovery.py tests/test_ingestion_activity.py tests/test_issue_terms_resolver.py tests/test_issue_terms_runtime_path.py tests/test_issue_terms_windows_retrieval.py tests/test_cross_ipo_issue_term_provenance.py -q` | **69 passed**, 12 warnings (309.19 s) | **0** |
| Full backend suite | `.venv/bin/python -m pytest tests/ -q` | **1051 passed**, 0 failed, 19 warnings (1236.05 s) | **0** |
| Frontend suite | `node --test test/*.test.js` (in `frontend/`) | **77 passed**, 0 failed | **0** |
| Pre-fix reproduction | the new regressions against the `0dda109` engine | **4 failed** (`assert 'ok' != 'ok'`, `assert 'NOT_FOUND' == 'UNAVAILABLE'`) | **1** |

Full backend log: `/tmp/pytest-full-final.log` (`PYTEST_EXIT=0`).
No test was skipped, deselected or filtered; the 19 warnings are the
pre-existing `PytestUnknownMarkWarning: Unknown pytest.mark.slow` and
the Starlette/httpx deprecation warnings that also occur on
`0dda109`. The five new backend tests (four in
`tests/test_official_discovery.py`, one extra assertion set in
`tests/test_ingestion_activity.py`) raise the backend count from 1046
to 1051; the frontend count rises from 76 to 77.

## 0.6 What this does NOT claim

* **BSE retrieval is not fixed and is not claimed fixed.** The Windows
  runtime still receives a JavaScript application shell for both BSE
  listing URLs; the correct terminal behaviour is UNAVAILABLE with
  per-URL reasons.
* No headless browser, no new runtime dependency, no invented issuer
  terms.
* Scoring, thresholds, knockout behaviour, golden fixtures, historical
  evaluations, provenance and conflict handling are untouched; missing
  required terms still block evaluation and persistence.

---

## 1. The reported failure (authoritative acceptance evidence)

Windows runtime, checkout at `3fea259e6f90f29bb3b75b97b1efaa95f2530ad6`
("Repair discovery outcome classification: shells are not searched
listings"), server restarted from that checkout, uvicorn startup
confirmed, health endpoint healthy. Latest ingestion
`ing-5aa6dd92cd7640a8`:

| # | Observed | Where it comes from |
|---|---|---|
| 1 | BSE classic listing URL → JavaScript shell, no issue rows, listing not searched | provider note: `…: returned a JavaScript application shell with no issue rows in the served HTML (a listing was not searched)` |
| 2 | BSE `publicissue.html` → JavaScript shell, no issue rows, listing not searched | same note text |
| 3 | SEBI listing → HTTPError | provider note: `…: listing retrieval failed (HTTPError)` |
| 4 | Provider outcome **NOT_FOUND** | `OfficialDiscoveryProvider.find` |
| 5 | Activity completion **UNPUBLISHED** | `IssueTermsResolver.resolve` → `official_discovery/completed` event |
| 6 | Required issue terms remain unresolved | `term_resolution` events |
| 7 | Evaluation not run; persistence not attempted | `evaluation/not_run`, `persistence/not_attempted` |

The reported correction (`3fea259`) was supposed to make unusable
listings yield UNAVAILABLE. **Its acceptance criterion failed.**

## 2. What each configured source returned, and how it was classified

`OfficialDiscoveryProvider.LISTING_URLS` (engine/ipo_screening/issue_terms.py)
is the only listing source set:

| # | Listing URL | Windows response at 3fea259 | `_classify_listing` at 3fea259 | Note emitted? | Counted as searched? |
|---|---|---|---|---|---|
| 1 | `https://www.nseindia.com/market-data/all-upcoming-issues-ipo` | HTTP 200, page chrome only (see §3) | `ok` | **no** | **yes** |
| 2 | `https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P` | JavaScript application shell | `shell` | yes | no |
| 3 | `https://www.bseindia.com/publicissue.html` | JavaScript application shell | `shell` | yes | no |
| 4 | `https://www.sebi.gov.in/sebiweb/home/handleAction?doListing=yes&sid=1&ssid=7&smid=0` | HTTPError | (exception) | yes | no |

The trace lists exactly three unusable sources (items 1–3 above) and
one NOT_FOUND provider outcome. Every classification other than `ok`
emits a per-URL note, so the absence of a note for the NSE URL proves
it was classified `ok` — it was the response that made the provider
report NOT_FOUND. This is the only listing URL the trace does not
account for, and the only one that could have produced NOT_FOUND.

## 3. Why the NSE response classified as `ok` — the faulty predicate

At `3fea259` the predicate was (engine/ipo_screening/issue_terms.py,
`_classify_listing`):

```python
_LISTING_MARKERS = (
    "displayipo", "issue-information", "issue_information",
    "public issues", "public issue", "security name", "attachdocs",
    "all-upcoming-issues", "price band",
)
...
if has_issue_content or any(marker in text for marker in cls._LISTING_MARKERS):
    return "ok"
```

`_LISTING_MARKERS` is a **substring test over the whole served HTML**.
A marker that identifies the *page* — not an issue record — therefore
constitutes "a genuine listing":

* the NSE listing URL's own path is `…/market-data/**all-upcoming-issues**-ipo`;
* the served page repeats that path in its navigation link, its
  canonical link and every URL that carries the same route.

**Evidence (retrieved 2026-10-18, this investigation):** the live NSE
page (`https://www.nseindia.com/market-data/all-upcoming-issues-ipo`)
and its archived raw response (2026-09-09 snapshot) both contain
`https://www.nseindia.com/market-data/all-upcoming-issues-ipo` in the
navigation (`[IPO](…/all-upcoming-issues-ipo)`) and elsewhere. The
served listing table carries a header row ("Company Name | Security
type | Issue Start Date | Issue End Date | Status | NSE Bid Details")
and **no issue row at all** — the rows are filled client-side
(`Fetching…`). The string `all-upcoming-issues` is therefore present
while the page carries no issue entry whatsoever.

So the response satisfied `_LISTING_MARKERS` ("all-upcoming-issues")
→ `ok` → `reached = True`.

**The exact statement that produced the provider's NOT_FOUND**
(`OfficialDiscoveryProvider.find`, at `3fea259`):

```python
        if reached:
            detail = ("valid official listings searched; no issuer-matched official "
                      "document was found (this does not by itself establish non-publication)")
            …
            return None, ProviderReport(self.name, "NOT_FOUND", detail)
```

**The exact conversion that produced UNPUBLISHED**
(`IssueTermsResolver.resolve`):

```python
        if not candidates:
            searched = any(r.outcome == "NOT_FOUND" for r in outcome.provider_reports)
            outcome.status = "UNPUBLISHED" if searched else "UNAVAILABLE"
```

Any NOT_FOUND provider report was enough — the resolver never checked
that a listing had really been searched.

**Why `3fea259` did not fix it:** that commit added an exclusion for
the *marker-less* response (`empty` → not counted). The NSE response
is not marker-less: it carries a chrome marker. Marker-only
recognition was never removed, so the NSE response kept classifying
as `ok`, `reached` stayed `True`, and the outcome stayed NOT_FOUND →
UNPUBLISHED. The commit fixed the *symptom* it had diagnosed
(marker-less pages) and not the *predicate* (a marker is not a
listing).

**Reproduction against the pre-fix code** (engine at `3fea259`, new
regression fixture as the Windows response pattern):

```
classification of the NSE response : ok
provider outcome                   : NOT_FOUND
provider detail                    : valid official listings searched; no issuer-matched official document was found (this does not by itself establish non-publication); https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P…
resolver status                    : UNPUBLISHED
```

and the new regression tests fail against that code
(`assert 'NOT_FOUND' == 'UNAVAILABLE'`), pass after the repair.

## 4. The repair

### 4.1 Listing recognition is now structural, not marker-based

> **Superseded by §0.4.1.** The rule below still accepted a *page-wide*
> href scan as evidence of issue entries; the corrected rule requires
> an **issue record inside a table data row** (anchor-only links), so
> that site-wide chrome can no longer stand in for a listing.

`OfficialDiscoveryProvider._classify_listing` now returns `ok` only
when the served response actually carries **issue entries**:

* a data row of an **issue-listing table** (a table whose header names
  at least two issue-listing columns: Security Name / Company Name /
  Issue Start Date / Open Date / Close Date / Start Date / End Date /
  Issue Status / Offer Price / Price Band / Market Lot / Issue Size /
  No. of Shares / Bid Lot / Issue Period / Issue Name / Issue Type)
  that carries an issue date (`21-10-2026`, `21/10/2026`, `21 Oct
  2026`, `October 2026`) or a per-issue link; or
* a **per-issue link** — `DisplayIPO`, `ACQDisp`, `attachdocs`,
  `issue-information`/`issue_information`, `price-band`/`price_band` —
  i.e. exactly the links discovery follows.

A response that is merely an HTTP 200, or that is neither a homepage
nor a shell, is **not** a searched listing. The chrome markers
("public issues", "all-upcoming-issues") are no longer evidence of
anything; a page whose table is filled client-side carries no issue
entry and is classified `empty` (unusable) with a precise reason.

Classification order: `shell` → `ok` (issue entries) → `homepage`
(masthead, no issue entries) → `empty`. The homepage verdict still
requires the masthead **and** the absence of issue entries, so a real
BSE page that shares the masthead in its chrome is not misclassified.

### 4.2 NOT_FOUND must be substantiated

`ProviderReport` gained `listing_searched` (and a structured `notes`
list, so no per-source reason is lost to the bounded event message).
The discovery provider sets `listing_searched=True` only when it
really searched at least one genuine listing. The resolver maps a
NOT_FOUND report to UNPUBLISHED **only** when it is substantiated:

```python
searched = any(r.outcome == "NOT_FOUND" and r.listing_searched
                for r in outcome.provider_reports)
outcome.status = "UNPUBLISHED" if searched else "UNAVAILABLE"
```

A search of the retained local corpus (unverified documents, not a
listing) therefore no longer yields UNPUBLISHED; it stays
UNAVAILABLE. UNPUBLISHED now arises only from a genuine listing
search with no issuer-matched candidate — the rule the specification
states.

### 4.3 Preserved

CONFLICT handling, the allow-list, issuer matching, document
classification, Market-Lot-only extraction, provenance labels, the
snapshot cache, retries, the Windows temp-file fix, manual entry,
scoring, thresholds, knockouts, golden fixtures and historical
evaluations are untouched. Missing required terms still block
evaluation and persistence.

## 5. BSE retrieval — proven facts vs. hypotheses

**Proven (retrieved 2026-10-18 in this investigation):**

1. The BSE classic listing page carries the issuer's row when it is
   retrieved with a client that is allowed through: the live page
   lists `Jio Platforms Limited | MainBoard | 21-10-2026 | 23-10-2026 |
   1065.00 - 1119.00 | IPO | Forthcoming` with the link
   `…/markets/publicIssues/DisplayIPO?id=4894&type=IPO&idtype=1&status=F&IPONo=8047&startdt=21/10/2026`.
   The same table is served by `https://www.bseindia.com/publicissue.html`.
2. The Windows runtime received a **JavaScript application shell** for
   both BSE listing URLs, with the cookie-session fetcher live
   (commit `589159a`) — so the warm-up/cookie mechanism does not by
   itself get the real page.
3. The NSE listing page's issue rows are client-side: the served HTML
   has the table header and no rows. The application therefore cannot
   read NSE issue rows with a plain HTTP client at all.
4. From this sandbox, TLS to www.bseindia.com, www.nseindia.com and
   www.sebi.gov.in fails (`SSLZeroReturnError: TLS/SSL connection has
   been closed (EOF)`) — an egress restriction of this environment,
   not evidence about the Windows runtime.

**Hypotheses (NOT proven):**

* that BSE's protection "requires JavaScript-executed session state"
  (the wording of the `3fea259` commit message). The evidence is
  consistent with it but does not establish it: a *rendering* client
  (the investigator tooling used here) receives the real page, while
  a plain HTTP client receives a shell. The discriminating factor
  between the two clients has not been isolated. Competing
  explanations that remain open: TLS/JA3 fingerprinting, per-session
  cookies the site sets through JavaScript, header-set/ordering
  discrimination, and IP reputation. **No headless-browser
  dependency or architectural change has been introduced**: that would
  be a new runtime dependency and an architecture decision, and it
  requires its own requirements analysis, authorization and evidence.
* That the SEBI listing URL (`doListing=yes&sid=1&ssid=7&smid=0`) is
  a usable issue listing at all: the response obtained here is a
  general SEBI announcements page, not a table of issues. It is
  therefore never counted as a searched listing.

**Consequence, stated honestly:** with the current retrieval
mechanism the application cannot read the BSE listing on the Windows
runtime. The correct terminal behaviour is UNAVAILABLE with precise
per-URL reasons — never UNPUBLISHED. BSE retrieval is **not** fixed
and is **not** claimed fixed.

## 6. Regression coverage (new)

* `tests/test_official_discovery.py`
  * `test_chrome_marker_only_response_is_not_a_searched_listing` —
    a response that repeats the listing page's own path is not a
    searched listing; shell/homepage/empty/genuine-listing
    classifications are pinned.
  * `test_windows_trace_pattern_is_unavailable_never_not_found` — the
    exact Windows pattern (NSE chrome-only page, both BSE listings as
    JavaScript shells, SEBI HTTPError) at the provider and resolver
    layers → UNAVAILABLE, never NOT_FOUND, never UNPUBLISHED.
  * `test_live_bse_listing_shape_is_still_a_searched_listing` — the
    genuine BSE row shape (captured live 2026-10-18) is still a
    searched listing and still yields 1065/1119/12: the repair narrows
    the predicate, it does not disable discovery.
  * `LISTING_EMPTY` was remodelled to the recorded BSE listing row
    shape (it previously had no issue row at all, so it did not model
    a genuine listing under the corrected predicate). Its assertions
    are unchanged.
* `tests/test_ingestion_activity.py`
  * `test_windows_trace_pattern_is_unavailable_end_to_end` — service,
    resolver and activity trace: UNAVAILABLE, all four unusable
    sources named, no UNPUBLISHED anywhere, terminal BLOCKED,
    evaluation/persistence SKIPPED, nothing persisted.
  * `test_windows_trace_pattern_is_unavailable_through_the_api` — the
    API response carries `resolution.status = UNAVAILABLE` and no
    UNPUBLISHED.
* `frontend/test/ingestion-activity.test.js` and
  `frontend/test/manual-terms.test.js` — the activity panel and the
  official-source diagnostics render UNAVAILABLE with every per-source
  reason, and never UNPUBLISHED.

Test results for this repair (all run locally, output visible):

| Run | Command | Result | Exit code |
|---|---|---|---|
| Focused discovery + activity | `PYTHONPATH=engine python -m pytest tests/test_official_discovery.py tests/test_ingestion_activity.py -q` | 32 passed | 0 |
| Focused discovery + activity + resolver + cross-IPO | `PYTHONPATH=engine python -m pytest tests/test_official_discovery.py tests/test_ingestion_activity.py tests/test_issue_terms_resolver.py tests/test_cross_ipo_issue_term_provenance.py -v` | 39 passed | 0 |
| Full backend suite | `PYTHONPATH=engine python -m pytest tests/ -v --tb=short` | **1046 passed**, 0 failed, 19 warnings (933.53 s) | 0 |
| Frontend suite | `npm --prefix frontend test` | **76 passed**, 0 failed | 0 |
| Pre-fix reproduction | new regressions against the `3fea259` engine | 2 failed (`assert 'NOT_FOUND' == 'UNAVAILABLE'`) | 1 |

No test was skipped, deselected or filtered; the 19 warnings are the
pre-existing `PytestUnknownMarkWarning: Unknown pytest.mark.slow` and
two Starlette/httpx deprecation warnings that also occur on `3fea259`.

## 7. Is another Windows acceptance test necessary?

**Not as a discovery-correctness test.** The exact Windows response
pattern is now reproduced deterministically at provider, resolver,
activity, API and UI level, and it fails against the code that
produced the reported acceptance failure. That regression is the
effective acceptance test and it does not need a Windows machine.

**Yes, but for a different purpose:** a Windows re-run is still the
only way to observe the *live* BSE/NSE/SEBI responses from the user's
network, and therefore the only way to confirm (a) that the terminal
status is now UNAVAILABLE for the live pattern, and (b) whether BSE
serves the real listing to the application's client from that network
(it does not today). That is a retrieval-capability question, not a
classification question, and it is not resolvable by any further code
change on this side.
