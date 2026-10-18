# Windows discovery outcome: root cause of the 3fea259 acceptance failure and its repair — 2026-10-18

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
