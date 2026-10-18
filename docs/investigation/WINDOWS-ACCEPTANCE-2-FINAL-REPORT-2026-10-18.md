# Windows acceptance #2 — final report (ingestion `ing-32ddf313bbe247b0`)

**Status: root-caused, repaired, tested, published.**
Commit `5d9597c46a0a73171f33daee0db44b6e8e28f194` on the session branch
`arena/42628121-ipo-screening-engine` and on the PR #6 head branch
`arena/5dd3fe52-ipo-screening-engine`. PR #6 is **OPEN, MERGEABLE,
unmerged**; `main` is untouched at `01ba66c`.

---

## 1. What the second Windows acceptance reported

Windows checkout exactly at the PR #6 head `0dda109` (clean tree, API
restarted, startup OK), ingestion `ing-32ddf313bbe247b0`:

| Observed | Value |
|---|---|
| BSE classic listing (`…/markets/PublicIssues/IPOIssues?id=1&Type=P`) | JavaScript shell — listing **not** searched |
| BSE `publicissue.html` | JavaScript shell — listing **not** searched |
| SEBI listing (`…/handleAction?doListing=yes&sid=1&ssid=7&smid=0`) | `HTTPError` |
| Per-source failure events in the trace | exactly **3** (one per unusable source) |
| Aggregate official-discovery outcome | **NOT_FOUND** |
| Activity completion | **UNPUBLISHED** |
| Required terms | still missing |
| Evaluation / persistence | correctly skipped |

The round-1 conclusion (“`0dda109` fixes the contradiction; a Windows
re-run is optional”) is **withdrawn** — it was wrong.

---

## 2. Exact source that produced NOT_FOUND

**`https://www.nseindia.com/market-data/all-upcoming-issues-ipo`** — the
NSE listing source.

It is the one configured source that emitted **no** note (the three
notes in the trace account for the other three sources), and at
`0dda109` only a response classified `ok` could set
`reached = True`, which is the sole precondition for the NOT_FOUND
report and for `listing_searched=True`. So the NSE source set
`listing_searched = true` → NOT_FOUND → (resolver) UNPUBLISHED.

This was **not** inferred from the absence of an event: it follows from
the code path plus the fact that every other source emitted its own
failure event — and it is independently confirmed below.

---

## 3. The faulty predicate (and the proof)

At `0dda109`, `OfficialDiscoveryProvider._has_issue_entries()` began
with an unconditional, document-wide branch:

```python
if cls._per_issue_links(text):        # <-- the defect
    return True
```

and `_per_issue_links()` matched **any** `href=` attribute in the
document — including `<link rel="canonical">` / `<link rel="alternate">`
metadata — against the tokens
`displayipo, acqdisp, attachdocs, issue-information, issue_information,
price-band, price_band`.

NSE serves that chrome on **every** page it renders:

* the site-wide market-data menu item
  `<a class="nav-link" role="menuitem" id=Price Bands &amp; Surveillance
  Actions href="/market-data/price-bands-surveillance-actions">`
* the canonical/alternate metadata
  `…/market-data/issue-information?series=EQ&symbol=VNL` (+13 language
  variants).

### Proof, run against the exact `0dda109` code

`git archive 0dda109` → scratch tree, imported ahead of the working
engine, over the **retained real NSE response**
`evidence/ipo-subscription/vnl-20261011/vnl-issue-information.html`
(313,038 bytes, captured 2026-10-11):

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

The response carries **no issue record at all** (2 tables, 4 `<tr>`,
**0 `<td>` cells**): NSE’s listing table is filled client-side. So the
`ok` verdict, and with it the false NOT_FOUND/UNPUBLISHED, came from
*page chrome*, not from a listing.

### Why round 1 missed it

The round-1 regression fixture `NSE_MARKER_ONLY_LISTING` modelled the
NSE response **without** the site-wide menu and canonical/alternate
chrome. The fixture was unfaithful to the real response, so it could
not reproduce the failure.

---

## 4. The repair (generic, no issuer-specific code)

1. **Issue records, not page chrome.** A response counts as a searched
   listing only when it carries an *issue record*: a table data row
   (`<tr>` with `<td>` cells) that links to one issue or one official
   document — matched on **anchor elements only**, so canonical/
   alternate metadata can no longer count — or a data row of an
   issue-listing table (header naming ≥ 2 issue-listing columns:
   Security Name / Company Name / Exchange Platform / Start Date /
   End Date / Issue Start Date / Issue End Date / Issue Status /
   Offer Price / Price Band / Market Lot / Issue Size / No. of Shares /
   Bid Lot / Issue Period / Issue Name / Issue Type / Face Value /
   Type of Issue) that carries an issue date (`21-10-2026`, `21/10/2026`,
   `21 Oct 2026`, `October 2026`). Navigation, menus and language
   switchers are never inside a data row → the client-side NSE listing
   is `empty` (“no issue entries in the served HTML”) and unusable.
2. **Evidence, not a flag.** `ProviderReport` now carries one
   `ListingAttempt` per configured source (`url`, `classification`,
   `searched`, `issue_entries`, `detail`) and the searched listings by
   URL. The resolver maps a NOT_FOUND report to UNPUBLISHED only when
   it is substantiated **and** names the listings it read:
   `r.outcome == "NOT_FOUND" and r.listing_searched and r.searched_listings`.
   A report that claims a search but names no listing → UNAVAILABLE.
3. **No source may contribute invisibly.** The `ok` path used to emit
   no note, which is why the NSE source was silent in the Windows
   trace. Now: one activity event per configured source (SUCCEEDED for
   a listing really read, FAILED otherwise); `providers[].sources` and
   `providers[].searched_listings` in the API payload; the UI’s
   official-source diagnostics list every source with whether its
   listing was really searched; a candidate document that could not be
   used is no longer discarded silently.
4. **Fixtures made faithful.** The synthetic fixtures that modelled a
   listing as bare anchors outside any table (`LISTING_WITH_NOTICE`,
   `LISTING_WITH_PROSPECTUS`, `BSE_LISTING`,
   `JIO_LISTING_WITH_PROSPECTUS`) were remodelled to the shape the
   exchanges really serve (issue records in the listing table’s rows).
   The genuine-listing positive cases are unchanged and still classify
   `ok`.

### Behaviour after the repair (same reproduction, final code)

```
REPRODUCED WINDOWS FAILURE PATTERN (real NSE chrome + 2 BSE shells + SEBI HTTPError)
  provider outcome     : UNAVAILABLE  (was NOT_FOUND at 0dda109)
  listing_searched     : False
  searched_listings    : []
    - https://www.nseindia.com/market-data/all-upcoming-issues-ipo   empty   searched=False entries=0
    - https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P shell searched=False entries=0
    - https://www.bseindia.com/publicissue.html                      shell   searched=False entries=0
    - https://www.sebi.gov.in/sebiweb/home/handleAction?doListing=yes&sid=1&ssid=7&smid=0 failed searched=False entries=0
  resolver status      : UNAVAILABLE  (was UNPUBLISHED at 0dda109)
  unresolved terms     : ['price_band_low', 'price_band_high', 'lot_size', 'ofs']

POSITIVE CASE (a genuine listing really read, issuer absent):
  provider outcome     : NOT_FOUND | searched_listings: [all four listing URLs]
  resolver status      : UNPUBLISHED   (genuine listing searched -> UNPUBLISHED retained)
```

---

## 5. New regressions

`tests/test_official_discovery.py`

* `test_real_nse_response_is_not_a_searched_listing` — the **retained
  real NSE response** and the listing response built from its real
  site-wide header are not searched listings; the `0dda109` rule is
  kept inside the test to show it called both `ok`.
* `test_windows_trace_pattern_with_real_nse_response_is_unavailable` —
  the exact second-failure pattern (real NSE response, two BSE shells,
  SEBI HTTPError) → provider UNAVAILABLE, `listing_searched` false, no
  searched listing, four attempts, resolver UNAVAILABLE.
* `test_every_configured_source_produces_a_visible_attempt` — the
  failed source and the searched source are both visible; the searched
  listing is named.
* `test_not_found_without_a_named_searched_listing_is_never_unpublished`
  — a NOT_FOUND report with the flag but no evidence → UNAVAILABLE.
* `test_genuine_listing_searched_is_named_in_the_report` — the positive
  case is retained.

`tests/test_ingestion_activity.py` — the end-to-end and API tests now
serve the **real** NSE response and assert one visible event per
configured source (including the NSE one that used to be silent),
`searched_listings == []`, four source records, no UNPUBLISHED
anywhere, terminal BLOCKED, evaluation/persistence SKIPPED, nothing
persisted.

`frontend/test/manual-terms.test.js` — the official-source diagnostics
list every source with its classification and whether its listing was
really searched, and never show UNPUBLISHED.

---

## 6. Test results (output visible, real exit codes)

| Run | Result | Exit |
|---|---|---|
| Focused: discovery + activity + resolver + runtime + windows-retrieval + cross-IPO | **69 passed**, 12 warnings (309.19 s) | **0** |
| Full backend suite (`pytest tests/ -q`) | **1051 passed**, 0 failed, 19 warnings (1236.05 s) | **0** |
| Frontend suite (`node --test test/*.test.js`) | **77 passed**, 0 failed | **0** |
| New regressions **against the `0dda109` engine** | **4 failed** (`assert 'ok' != 'ok'`, `assert 'NOT_FOUND' == 'UNAVAILABLE'`) | **1** |

Full backend log: `/tmp/pytest-full-final.log` (`PYTEST_EXIT=0`).
No test skipped, deselected or filtered; the 19 warnings are the
pre-existing `PytestUnknownMarkWarning: Unknown pytest.mark.slow` and
the Starlette/httpx deprecation warnings that also occur on `0dda109`.
Backend count 1046 → 1051; frontend 76 → 77.

---

## 7. Published state (verified remotely)

```
$ git ls-remote origin refs/heads/arena/42628121-ipo-screening-engine \
                      refs/heads/arena/5dd3fe52-ipo-screening-engine \
                      refs/heads/main
5d9597c46a0a73171f33daee0db44b6e8e28f194  refs/heads/arena/42628121-ipo-screening-engine
5d9597c46a0a73171f33daee0db44b6e8e28f194  refs/heads/arena/5dd3fe52-ipo-screening-engine
01ba66c12ca1195fd7acbd287c3e39a019808094  refs/heads/main

PR #6: state OPEN, mergedAt null, mergeable MERGEABLE,
      headRefName arena/5dd3fe52-ipo-screening-engine,
      headRefOid 5d9597c46a0a73171f33daee0db44b6e8e28f194
```

The PR #6 head branch was fast-forwarded from `0dda109` to the
identical commit; no other branch was created or pushed; `main` was
not touched. The PR carries a comment with this report’s substance.

---

## 8. What is explicitly **not** claimed

* **BSE retrieval is not fixed and is not claimed fixed.** The Windows
  runtime still receives a JavaScript application shell for both BSE
  listing URLs. The honest terminal status for that situation is
  **UNAVAILABLE** with per-URL reasons — never UNPUBLISHED. The
  hypothesis that BSE’s protection “requires JavaScript-executed
  session state” remains **unproven** (TLS/JA3 fingerprinting, JS-set
  session cookies, header order and IP reputation all stay open).
* No headless browser, no new runtime dependency, no invented Jio terms.
* No changes to scoring, thresholds, knockout behaviour, golden
  fixtures, historical evaluations, provenance or conflict handling.
* Missing required terms still block evaluation and persistence.

---

## 9. What is needed from you (nothing, unless you want to observe live traffic)

* **No further Windows upload is required for discovery correctness** —
  the second failure is now a deterministic regression at provider,
  resolver, activity, API and UI level, built from the *real* NSE
  response rather than a hand-written approximation, and it fails
  against the `0dda109` engine.
* A Windows re-run remains the only way to observe the **live**
  BSE/NSE/SEBI responses from your network, i.e. to answer whether BSE
  serves the real listing to the application client from that network.
  That is a retrieval-capability question, not a classification
  question, and no code change here can resolve it.
* If you do re-run: the expected terminal status is **UNAVAILABLE**
  with four per-source reasons (NSE no issue entries, BSE shell ×2,
  SEBI HTTPError) — never UNPUBLISHED — and the activity trace will now
  show one event per source, including NSE.

---

## 10. Where the records live

* `docs/investigation/WINDOWS-DISCOVERY-UNAVAILABLE-REPAIR-2026-10-18.md`
  §0 — second failure, actual root cause, corrected repair (§1–§3 and
  §4.1 of that file are the superseded round-1 record, marked, not
  erased).
* `docs/investigation/GENERIC-ISSUE-TERM-DISCOVERY-2026-10-18.md`
  Addendum (5).
* `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` — new entry
  at the end of the file.
* This report: `docs/investigation/WINDOWS-ACCEPTANCE-2-FINAL-REPORT-2026-10-18.md`.
