# Official-document discovery — end-to-end disposition

**Date:** 2026-10-28
**Base:** `main` @ `e7934b1` (PR #15 merged, tracker Revision 33)
**Scope:** G-2 (addenda/precedence) plus the mapping of the discovery path the tracker asked for.
**Status:** G-2 **BLOCKED — no specimen**; one engine defect found and fixed; nothing else changed.

This document maps the existing discovery path across the ten dimensions named in the
work order, separates what is **implemented** from what is only **documented**, states the
nine evidence states the path must keep distinct, records the source-feasibility position,
and closes out G-2 with the exact evidence an owner must supply.

No issuer-specific exception was added to reproduce Jio. No precedence rule was invented.
No scoring, threshold, penalty, verdict, knockout, schema or UNKNOWN contract was touched.

---

## 1. The defect this pass found and fixed

**File:** `engine/ipo_screening/issue_terms.py` — `NoticeSnapshotCache.get`.

A30 rule 1 (2026-10-23) established that a document must be re-read **under its own class**.
That rule was implemented for the Prospectus and the RHP, and stayed broken for the two HTML
classes. `get()` dispatched every class that was not a prospectus or an RHP to the notice
path. The notice parser refuses HTML **by class**, so both HTML classes read back as `None`:

| stored class | parsed by | before | after |
| --- | --- | --- | --- |
| `PRICE_BAND_NOTICE` | notice parser | round-trips | round-trips (unchanged) |
| `OFFICIAL_PROSPECTUS` | prospectus parser | round-trips | round-trips (unchanged) |
| `OFFICIAL_RHP_TERMS` | RHP parser | round-trips | round-trips (unchanged) |
| `EXCHANGE_ISSUE_PAGE` | `ExchangeIssuePageParser` | **`None`** | round-trips, class preserved |
| `INVESTMENT_PLATFORM_PAGE` | `ExchangeIssuePageParser` | **`None`** | round-trips, class preserved |

The exchange issue page is the document the whole discovery path exists to find. Which class
the stored snapshot is read back as is therefore not cosmetic: a verified official exchange
page was silently reconstructed as "no evidence" on the second resolution.

**Fix:** a `_HTML_TERM_CLASSES` frozenset and one dispatch branch sending those classes to
`ExchangeIssuePageParser`, then **re-asserting the stored class** on the result. The
re-assertion is the authority boundary: the parser always labels its own output
`EXCHANGE_ISSUE_PAGE`, so without it a platform snapshot would come back labelled as an
official exchange publication. Identical values on a platform page never make it official.

**Reach caveat — stated precisely, because it bounds the claim.** `put()` has no production
caller today; only tests write snapshots. `get()` *is* wired into `IssueTermsResolver.resolve`
whenever `IPO_ISSUE_TERMS_CACHE_DIR` is set. So this is a correctness repair on a **wired read
path** whose write side is not yet populated in production — not a live data loss observed in
the field. It is still a defect: the moment anything calls `put()`, every exchange-page
snapshot is lost on re-read.

**Verification.** New module `tests/test_notice_cache_html_classes.py`, 6 tests. Proven
load-bearing by reverting the engine fix: **5 of 6 fail**, and the one that still passes is
the metadata-recording test, which `put()` already satisfied. Restored, 6 pass.

---

## 2. The discovery path, dimension by dimension

Each row says whether the behaviour is **implemented** (in the merged tree), **partial**, or
**documented only**.

| # | Dimension | Where | State |
| --- | --- | --- | --- |
| 1 | Unresolved-field detection | `issue_term_fields.resolve_fields`, field states | **Implemented** |
| 2 | `[●]` placeholder recognition | `extraction/exchange_issue_page.py`, `price_band_notice.py` | **Implemented** (fail-closed) |
| 3 | Issuer / offering identification | `_norm_name`, `official_issue_sources`, `issue_platforms._identity` | **Implemented**; exact-match, fails closed |
| 4 | Configured official sources & methods | `OFFICIAL_HOSTS`, `DISCOVERY_HOSTS`, `LISTING_URLS`, env overrides | **Implemented**, network-gated |
| 5 | Retrieval / inspection | `_default_http_fetch`, `ListingAttempt`, `_classify_listing` | **Implemented** |
| 6 | Classification / validation | `_classify_listing`, `_values_valid`, `_REQUIRED_EVIDENCE` | **Implemented** |
| 7 | Extraction → canonical mapping | `PriceBandField`, `to_enrichment_dict`, `_notice_values` | **Implemented** |
| 8 | Conflicting / superseding documents | intra-response void; cross-document `CONFLICT` | **Partial** — conflict yes, **supersession undefined** |
| 9 | Provenance & retrieval-limitation recording | `SourceRef`, `ProviderReport`, `ListingAttempt` | **Implemented** |
| 10 | Effect of unresolved fields on ingestion/evaluation | resolver → `UNPUBLISHED`/`UNKNOWN` | **Implemented** |

### 2.1 Unresolved-field detection

`resolve_fields` publishes a **state per field**, not a fill. Each unresolved field carries
`why_unresolved` — `ABSENT_FROM_INSPECTED_DOCUMENT` or `NO_QUALIFYING_SOURCE` — and
`required_evidence` naming the document that would settle it. The two diagnostics
`NOT_DISCLOSED_IN_EXAMINED_SOURCES` and `SOURCE_UNAVAILABLE` are kept apart on purpose: "the
document I read did not say" and "I could not read a document" are different facts and only
the first is a statement about the issuer.

### 2.2 `[●]` placeholders

A placeholder yields **no field**, never a zero and never a guess. This was probed directly:
`[●]` in a price band yields `price_band_low = None`. `_REQUIRED_EVIDENCE` also records the
asymmetry that matters in practice — a placeholder **share count** does not block a stated
**monetary amount**, so one placeholder must not void the whole document.

### 2.3 Issuer and offering identification

`_norm_name` is **equality**, applied at every issuer gate (`issue_terms.py:64/173/336` and
`issue_term_fields`). Probed: `"...Limited"` ≠ `"...Ltd"` ≠ `"...Pvt Ltd"`. The direction of
that mismatch is a **rejection**, i.e. fail-closed — a non-matching page is refused rather
than attributed to the wrong issuer. That is the correct failure direction and it was left
alone: widening it to abbreviation matching would be an unsupported semantic change and a
new mis-attribution surface.

`issue_platforms._identity` strips `ipo|limited|ltd`, which is *looser* than `_norm_name` —
correctly, because a platform candidate never confers authority and its only job is to be
found and then corroborated by an official source.

### 2.4 Configured sources

Implemented and network-dependent: NSE listing page + `api/all-upcoming-issues`; BSE
`GetPublicIssue_par_updated`, the server-rendered `IPOIssues?id=1&Type=P` (carries DisplayIPO
links) and `publicissue.html` (JS shell, known unusable); SEBI listing action. Opt-in:
closed-issue history (`IPO_OFFICIAL_HISTORICAL_LISTINGS`) and the four platform providers.
Env-driven: `IPO_PRICE_BAND_NOTICE_URLS`, `IPO_PROSPECTUS_URLS`, `IPO_OFFICIAL_DISCOVERY`,
`IPO_ISSUE_TERMS_CACHE_DIR`.

A configured **directory** of notices (`IPO_PRICE_BAND_NOTICE_DIR`) yields `UNVERIFIED`
candidates that can never resolve a field — retained copies have no attestable provenance.

### 2.5 Retrieval and inspection

One `ListingAttempt` per configured URL, so no source can contribute to the aggregate outcome
without a visible record of what it returned. The host allowlist in `_default_http_fetch` is
the security boundary, and redirects are constrained to eligible hosts.

### 2.6 Classification — an HTTP 200 is not a listing

`_classify_listing` returns `ok | empty | homepage | shell | failed`; only `ok` counts as a
searched listing, and only a searched listing can support `NOT_FOUND` → `UNPUBLISHED`.

**This pass tested that rule against a genuine captured page rather than a synthetic one.**
`evidence/ipo-subscription/vnl-20261011/vnl-issue-information.html` is a real NSE
issue-information response retained in the repository. It contains the strings `price band`,
`issue-information` and `issue information` in its site chrome, and carries **zero** issue
records. The classifier returns:

```
_classify_listing     : empty
_has_issue_entries    : False
_issue_records        : 0
```

A marker-substring rule — the pre-2026-10-18 rule — would have called this `ok` and produced a
false `NOT_FOUND`, hence a false `UNPUBLISHED`. The defense works on real exchange output, not
merely on the fixture that was written to test it.

The same page is also a clean negative extraction case: `ExchangeIssuePageParser` recovers the
issuer (`NAL Academy Limited`) and `document_class = EXCHANGE_ISSUE_PAGE`, and **no terms**,
because the page states none. Correct behaviour — identification without manufacture.

### 2.7 Extraction to canonical

`PriceBandField` carries `locator`, `quote`, `page`, `extraction_method`, `verification` and
`confidence` per field, and `to_enrichment_dict` carries the `SourceRef` through. `_values_valid`
rejects a non-positive or non-integral lot, a non-positive band and an inverted band. The
parser itself accepts a raw negative lot and a zero OFS amount, but both are refused
downstream — the raw acceptance is not separately exploitable, and "fixing" the parser would
duplicate a validation that already exists one layer up.

### 2.8 Conflicts and supersession — the real gap

Implemented: **within** a response, repeated contradictory labels void the field; **across**
documents, conflicting values become a field-level `CONFLICT` and are **withheld**, never
first-wins. Vocabulary: `CONFLICT`, `CONFLICTING_PRICE_BANDS/OPEN_DATES/CLOSE_DATES/LOT_SIZES`.

Not implemented: **supersession**. There is no notion anywhere that document B replaces
document A's value for a field. The precedence that does exist is elsewhere and does not
apply: `enrichment_engine.py:565` orders pricing `PBN > Supplemental > RHP` **by class**, and
`connectors/coordinator.py` orders source classes. Neither answers "this corrigendum revises
that band".

This is dimension 8 and it is the whole of G-2.

### 2.9 Provenance and retrieval limitation

`SourceRef` = `source_id`, `source_type`, `uri`, `content_hash`, `retrieval_timestamp`,
`source_timestamp`. `ProviderReport` = `outcome`, `detail`, `notes`, `sources`,
`listing_searched`. The `FOUND / NOT_FOUND / UNAVAILABLE` split is the recording rule:
`UNAVAILABLE` is **never** evidence of non-publication, and only `NOT_FOUND` with
`listing_searched=True` can reach `UNPUBLISHED`.

### 2.10 Effect on ingestion and evaluation

An unresolved field propagates as a declared absence with a stated reason. The resolver's
default outcome is `UNPUBLISHED`; absent is never a favourable `False`, and a retrieval
failure is never an adverse `True`. Ingestion proceeds and evaluation carries UNKNOWNs rather
than manufactured values.

---

## 3. The nine evidence states

These are the states the path must never collapse. "Implemented" means a distinct outcome,
field state or rejection reason already names it.

| State | Distinguishable today? | By what |
| --- | --- | --- |
| 1. Original filing present | **Yes** | field resolved, `VERIFIED`, with `uri` + `content_hash` |
| 2. Placeholder, later disclosed | **Yes** | `ABSENT_FROM_INSPECTED_DOCUMENT` + `required_evidence` (document differs by `content_hash`) |
| 3. Exchange page available | **Yes** | `EXCHANGE_ISSUE_PAGE` + `FOUND` |
| 4. **Later filing / addendum** | **No** | no class, no precedence — see §4 |
| 5. Wrong issuer / offering | **Yes** | `REJECTED` (identity mismatch); `STALE_OR_DIFFERENT_ISSUE` |
| 6. Conflicting | **Yes** | `CONFLICT` + per-field `CONFLICTING_*`, value withheld |
| 7. Genuinely undisclosed | **Yes** | `NOT_DISCLOSED_IN_EXAMINED_SOURCES` after a searched listing |
| 8. Retrieval failure | **Yes** | `UNAVAILABLE` / `SOURCE_UNAVAILABLE`; never `UNPUBLISHED` |
| 9. Extraction failure | **Yes** | issuer found, no fields (the NAL Academy page is a live specimen) |

States 3, 8 and 9 were exercised this pass against real retained bytes. State 4 is the single
hole, and it is a **governance** hole, not a coding oversight.

---

## 4. G-2 — disposition

### 4.1 The search, recorded

| Looked for | Method | Result |
| --- | --- | --- |
| Addendum / corrigendum / errata / amendment file | `find` over the whole tree excluding `.venv`, case-insensitive | **0 hits** |
| Any such document among retained PDFs | enumerated all 12 retained PDFs | none is an addendum |
| Precedence code | `grep -ri "precedence\|supersed"` over `engine/ipo_screening` | 3 hits, all unrelated (see §2.8) |

The retained corpus is: Jio, Paras Healthcare, the `fixtures/filings/*` authored fixtures,
the Moneyview final prospectus, Vishal Nirmiti, and R.K Fashion. Every one is an **original**
filing. **No addendum, corrigendum, errata or amendment specimen exists in this repository.**

### 4.2 What was deliberately not done

No specimen was fabricated and described as an issuer document. No universal precedence rule
was invented. The four conceivable rules — later-supersedes-earlier, same-class-conflict,
field-wise-latest-wins, source-class-rank — are all *plausible* and mutually inconsistent, and
picking one without a specimen would be a fabricated semantic decision that silently rewrites
issuer-disclosed values. The code was therefore **not** changed for G-2.

### 4.3 The exact evidence an owner must supply

1. **One real addendum/corrigendum/errata** — or a later exchange notice revising an earlier
   price band, lot or date — for an issuer in the corpus, with:
   - the **publication timestamp** and the issue identity it belongs to;
   - the **field(s)** it revises, quoted;
   - the **class** of both the earlier and the later document.
2. **An explicit semantic statement**: does the later document *supersede* (replace the value),
   *supplement* (add a field the earlier one lacked), or merely *conflict* (be withheld)?
   And **on what recorded basis** — publication date, document order, source class, or an
   explicit "in supersession of" clause in the document itself?
3. **The tie-break** for the case where the later document is a *lower* authority than the
   earlier one (e.g. a later platform listing vs an earlier exchange page). The platform rule
   already says a platform never confers authority, so this case must be answered or it will
   be resolved by accident.

Until (1) and (2) arrive, the correct behaviour is what the engine already does: withhold on
conflict, never first-wins, never last-wins. **That is a defensible resting state, and it is
why G-2 does not block any other work.**

### 4.4 Recorded as a contract-level (synthetic) test only

If a precedence decision is later ratified, it can be pinned with a synthetic fixture clearly
labelled as a contract test. Nothing of that kind was added here, because there is no rule to
pin.

---

## 5. Source feasibility

Per configured source: intended data, matching requirement, access method, actual
retrievability **from this sandbox**, restrictions, timestamps/identity, retained provenance,
and the blocking limitation.

| Source | Intended data | Match requirement | Method | Retrievable here | Retained provenance |
| --- | --- | --- | --- | --- | --- |
| `nseindia.com/api/all-upcoming-issues?category=ipo` | live issue list | `_norm_name` equality | HTTPS JSON | **No** — TLS closed by proxy | `ListingAttempt` + notes |
| NSE issue-information page | band, lot, period | `_norm_name` equality | HTTPS HTML | **No** — TLS closed; retained capture classifies `empty` | `EXCHANGE_ISSUE_PAGE` + hash |
| `api.bseindia.com/.../GetPublicIssue_par_updated` | live issue feed | `_norm_name` equality | HTTPS JSON | **No** — TLS closed | `ListingAttempt` |
| `bseindia.com/.../IPOIssues?id=1&Type=P` | DisplayIPO links | `_norm_name` equality | HTTPS HTML | **No** — TLS closed; issue pages return `status=H` | `ListingAttempt` |
| `bseindia.com/publicissue.html` | — | — | HTTPS HTML | **No**, and **unusable by design** (JS shell) | `ListingAttempt` → `shell` |
| `sebi.gov.in` listing action | filings index | `_norm_name` equality | HTTPS HTML | **No** — TLS closed | `ListingAttempt` |
| `IPO_PRICE_BAND_NOTICE_DIR` | operator-supplied notices | issuer identity | local directory | **Yes** | `UNVERIFIED` — never resolves |
| `IPO_PROSPECTUS_URLS` / notice URLs | operator-pinned docs | allowlist host + identity | HTTPS | **No** in sandbox | `SourceRef` + hash |
| Platforms (dhan/groww/angelone/indmoney), opt-in | corroboration only | `_identity` (loose) | HTTPS | **No** | `INVESTMENT_PLATFORM_PAGE` — never authoritative |

**Reachability, measured this pass** — content requests, not DNS:

```
bseindia.com  ipoissues page        -> TLS/SSL connection has been closed (EOF)
api.bseindia.com GetPublicIssue     -> TLS/SSL connection has been closed (EOF)
nseindia.com all-upcoming-issues    -> TLS/SSL connection has been closed (EOF)
sebi.gov.in                         -> TLS/SSL connection has been closed (EOF)
```

Per the work order: these are **content-access failures**, and none of them is evidence that a
source is unreachable in production, nor that an issuer disclosed nothing. DNS and TCP
connectivity would not have established content access either; only a parsed response does,
and there is none here. No source is claimed verified from this sandbox.

**Blocking limitation, stated once:** live official retrieval cannot be exercised in this
sandbox at all. Every live-source claim in this workstream is therefore either a code-path
claim tested with injected bytes, or a claim about a **retained capture** — never a claim
about bseindia.com/nseindia.com/sebi.gov.in as they are today.

---

## 6. What changed

| File | Change |
| --- | --- |
| `engine/ipo_screening/issue_terms.py` | **only engine change** — `_HTML_TERM_CLASSES` + one `get()` dispatch branch re-asserting the stored class (+22 lines) |
| `tests/test_notice_cache_html_classes.py` | **new (6 tests)** — round-trip, field preservation, recorded class, platform-not-upgraded, no-invention |
| `docs/investigation/OFFICIAL-DOCUMENT-DISCOVERY-DISPOSITION-2026-10-28.md` | **new** — this document |
| `docs/investigation/ARCHITECTURE-RECONCILIATION-2026-10-28.md` | G-2 row updated with the recorded search and the exact owner evidence |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` | Revision 34 |

Not changed, deliberately: the Jio divergence pin (`issue_terms.py` was **already** a member of
`DIVERGENT_ENGINE_FILES`, so the set stays 21 and the assertion stays exact — verified by
running it, not assumed); `SYNTHETIC_EXCEPTIONS` (the new module names no PDF/ingest module and
is not a tier-gate candidate — verified by running the gate); any scoring, threshold, verdict,
schema or UNKNOWN rule; any issuer-specific exception.

## 7. Verification

Focused only. **The full suite was not run.**

- **6 passed** — `tests/test_notice_cache_html_classes.py` (new).
- **5 of those 6 fail with the engine fix reverted** — the tests are load-bearing.
- **122 passed, 0 failed, 0 skipped** (128.65 s) —
  `test_notice_cache_html_classes`, `test_notice_cache_document_class`,
  `test_official_discovery`, `test_automatic_official_issue_discovery`,
  `test_issue_terms_multisource`, `test_issue_terms_windows_retrieval`,
  `test_suite_tiers`, `test_jio_current_engine_result_20261027`.
- Integrity gates: tier gate passes; Jio divergence is exactly the pinned 21 files.
