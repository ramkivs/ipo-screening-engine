# Generic automatic issue-term discovery — 2026-10-18

## Jio root cause (established, not assumed)

Jio Platforms' RHP (committed at `294c77d`, resolved at `2087fd3`)
discloses a fresh-issue-only offer with price band, lot size and fresh
amount as `[●]` placeholders and a Bid/Offer window of Oct 21–23,
2026. As of this investigation (18 Oct 2026), **the terms are not yet
officially published**: the NSE upcoming/active IPO list (checked
directly) shows Tonbo, Bonfiglioli, Sahajanand and Zetwerk — Jio is
absent; no Jio price-band notice or final Prospectus exists on the
official sources checked (NSE listings, SEBI filings; the SEBI-hosted
Jio document is the same placeholder RHP, verified earlier). Jio is
therefore an *unpublished-terms* case, not a resolver defect — but it
exposed a genuine generic gap: **the engine only retrieved terms from
manually configured per-issuer URLs**. When terms are published, an
operator still had to find the document and configure its URL by hand
for every issuer.

## Generic capability implemented

`OfficialDiscoveryProvider` (`engine/ipo_screening/issue_terms.py`),
wired into `build_resolver_from_env` by default (disable with
`IPO_OFFICIAL_DISCOVERY=0`):

- Searches the official listing pages of NSE, BSE and SEBI for
  documents linked for the issuer (issuer-name tokens / slug match on
  official listing pages only — no search engines, no snippets).
- Considers only candidate documents on the existing allow-listed
  official hosts; runs each through the **existing** verification
  pipeline (`HttpNoticeProvider` / `HttpProspectusProvider`): host
  allowlist, document classification, issuer matching, fail-closed
  parsing. Discovery never fabricates URLs or values.
- Outcomes keep the established semantics: FOUND (verified
  candidate), NOT_FOUND → resolver `UNPUBLISHED` (listings reached;
  terms genuinely not published yet), UNAVAILABLE (listings
  unreachable — transient, never treated as non-publication), with
  conflicts still detected across all candidates by the resolver.
- Configured sources keep precedence (they are consulted first);
  retained copies remain UNVERIFIED; the snapshot cache, bounded
  retries, HTML-interstitial classification and Windows temp-file
  handling from `b649ce6` are unchanged.
- Coverage limit (honest): documents hosted on official subdomains
  outside the allowlist (e.g. `nsearchives.nseindia.com`, deliberately
  never broadened) and listing pages that require interactive
  sessions may not yield candidates; configured URLs remain the
  fallback for those cases.

## Field contract

Required terms (unchanged): `price_band_low`, `price_band_high`,
`lot_size` (resolver) plus `ofs` (filing-established, or derived as
seller-shares × verified cap under the existing rule, or the
Prospectus-stated route). Discovery supplies the first three from a
verified notice/prospectus; OFS handling is exactly as before.
Provenance: discovered candidates carry provider
`official-discovery`, the listing page and document URL, retrieval
timestamp, document classification and field-level evidence via the
existing candidate/evidence machinery.

## Jio result

- Sandbox (application path): resolver returns `UNAVAILABLE` with
  `official-discovery` reporting all three listings unreachable —
  sandbox egress blocks NSE/BSE/SEBI, recorded as environmental, and
  correctly *not* reported as unpublished.
- Through the normal ingestion entry point with listings reached
  (automated test): discovery is attempted automatically with **no
  per-issuer configuration**, and ingestion fails closed as
  `AWAITING_ISSUE_TERMS` with the NOT_FOUND discovery report — the
  correct disposition while Jio's terms remain unpublished. When the
  price-band notice/prospectus is published on an official listing,
  the same path resolves without any code or configuration change.

## Regression matrix (tests/test_official_discovery.py, 6 tests)

Notice discovery without configuration; final-Prospectus discovery;
other-issuer documents rejected by the pipeline; unpublished
(NOT_FOUND → UNPUBLISHED with all four fields unresolved);
unavailable ≠ unpublished; HTML document responses rejected; Jio
service-level ingestion (automatic discovery attempt, fail-closed).
Existing matrices for split terms, conflicts, cache freshness,
retries, Windows temp files and issuer isolation remain in their
established suites and pass unchanged (one configuration-shape test
updated: the default resolver now contains exactly the discovery
provider and no packaged fixture source).

## Addendum — 2026-10-18 (Windows failure + broker evidence)

The user reported the Windows runtime still returning
`AWAITING_ISSUE_TERMS` (all four fields) after the discovery commit,
and supplied broker-displayed Jio terms (band ₹1,065–₹1,119, lot 12,
Oct 21–23). Re-investigation established:

1. **The terms are now officially published.** BSE's official
   public-issues page lists "Jio Platforms Limited, 21-10-2026 –
   23-10-2026, Offer Price 1065.00 - 1119.00, Forthcoming", and the
   official BSE issue-information page (`DisplayIPO?id=4894`)
   publishes Price Band 1065.00-1119.00, **Market Lot 12**, Issue
   Period 21–23 Oct 2026 and 27,00,00,000 shares (fetched and read
   directly in this investigation). The earlier "unpublished"
   conclusion was correct only until the price-band announcement;
   the broker values agree with the official exchange page.
2. **First failing stage: discovery coverage.** The three listing
   pages scanned by `OfficialDiscoveryProvider` do not expose
   document links for the issuer in fetchable HTML (exchange listing
   apps are JS-driven; BSE links its *issue-information page*, which
   the document-only link filter discarded). Retrieval, parsing,
   mapping and assembly downstream were never reached.
3. **OFS discrepancy:** at the current HEAD, extraction of the
   committed Jio RHP yields `issue.ofs = 0.0` (filing, "Not
   Applicable") in this environment, so a Windows run listing
   `issue.ofs` as missing implies its uploaded copy's cover layout
   defeats the bounded NIL pattern (or a stale process) — the NIL
   window was widened generically (16 → 32 lines). This cannot be
   verified against the user's file from here.
4. **Message defect:** the UNPUBLISHED reason text asserted
   non-publication from a NOT_FOUND outcome. It now states that no
   issuer-matched document was found by discovery/configured sources
   and that this does not by itself establish non-publication.

**Correction implemented:** discovery now follows issuer-matched
official exchange issue-information pages (`DisplayIPO`,
`issue-information`) and parses them with
`ExchangeIssuePageParser` (`document_class = EXCHANGE_ISSUE_PAGE`,
`EXCHANGE_DATA` extraction, verified official-host provenance;
Market Lot only — never minimum bid quantity/investment);
complementary verified candidates are field-merged with a hard
conflict check (disagreement → REJECTED, never silently preferred);
a final Prospectus remains the richest primary when also discovered.
The fresh-issue aggregating-amount pattern now accepts the genuine
"aggregating to ₹…" phrasing (as in Vishal's real Prospectus).
Service: when the four terms resolve but the stated fresh-issue
amount is still unestablished, ingestion fails closed naming
`issue.fresh_issue` precisely instead of a schema error.

**Jio acceptance (automated, normal entry point):** with BSE-shaped
official pages, pricing resolves from the exchange page and only
`issue.fresh_issue` awaits; with a final Prospectus also discovered,
the Jio evaluation **completes and persists** (1065/1119/12,
`ofs 0.0` filing). These fixtures are deterministic mechanics
evidence (modelled on the recorded official BSE pages), not a claim
of live retrieval from this sandbox, whose egress still cannot reach
the exchanges. Live completion on the user's Windows runtime remains
theirs to confirm with one fresh upload.

## Addendum 2026-10-18: first failing stage after the issue-page correction

**User-reported Windows acceptance at `cbac38c`:** the Jio RHP still
returned `AWAITING_ISSUE_TERMS` naming all four fields, even though
bseindia.com and sebi.gov.in homepages loaded (HTTP 200) and the API
health was healthy. Those checks prove homepage reachability only;
they do not exercise the listing retrieval, link following, or
issue-page parsing stages.

**Stage trace (A-L):** A. listing retrieval; B. listing parsing;
C. issuer matching; D. issue-detail link extraction; E. link following;
F. issue-page retrieval; G. exchange-page parser; H. source/issuer
validation; I. candidate resolution/merging; J. canonical population
(+ OFS); K. required-field gate; L. persisted evaluation.

**First failing stage: A/B (listing discovery).** Discovery scanned
`https://www.bseindia.com/publicissue.html`, which is a JavaScript
application shell: the raw HTML a plain HTTP client receives contains
no issue rows and no `DisplayIPO` links, so stages C-L never run and
discovery honestly reports NOT_FOUND while the terms are in fact
published. The server-rendered BSE listing
`https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P`
carries the full issue table with the issuer's `DisplayIPO` link in
the served HTML (verified by direct fetch through the investigator
tooling, 2026-10-18). Additionally, hrefs in served HTML encode query
separators as `&amp;`; raw URLs must be HTML-unescaped before
following, with decoded query parameters (`idtype`, `IPONo`,
`startdt`) preserved exactly.

**Sandbox limitation (explicit):** this environment's application-side
HTTPS to BSE/NSE/SEBI fails at TLS (egress restrictions documented in
earlier sections); live retrieval from here is UNAVAILABLE and is not
evidence about the Windows runtime. The classic-listing fixtures are
deterministic mechanics evidence modelled on the directly fetched
server-rendered page, not a claim of application-side live retrieval.

**Correction (generic, no issuer-specific code):** (1) the classic
server-rendered BSE listing was added to `LISTING_URLS` ahead of the
JS shell; (2) `_candidate_links` HTML-unescapes listing text before
href extraction. Downstream stages are unchanged: allowlist hosts,
issuer matching, `ExchangeIssuePageParser` (labelled Price Band /
Market Lot / Issue Period; Market Lot only), verified `EXCHANGE_DATA`
provenance as `EXCHANGE_ISSUE_PAGE`, hard conflict rejection, and
the richest-primary (Prospectus) preference.

**OFS (separate investigation):** zero and missing remain distinct
(`issue.get(field) is None`). Sandbox extraction of the committed
Jio RHP at HEAD establishes fresh-only content (no offer-for-sale)
and yields `ofs 0.0` from the filing itself; the service-level Jio
tests confirm `ofs 0.0` in the persisted evaluation. The Windows
report's `issue.ofs` therefore indicates that in the Windows run the
FRESH-only/NIL establishment did not fire — consistent with the
uploaded document's cover layout differing from the committed copy,
a stale runtime process, or discovery having been invoked on a
record whose filing evidence differs. Arena cannot inspect the
Windows file/process and does not claim otherwise; no issuer-specific
branch was added for it. The generic NIL window was already widened
(16→32 lines) in `cbac38c`; any further change requires the actual
Windows document's cover text as evidence.

**Regression tests added:** classic BSE listing with `&amp;`-encoded
hrefs (exact followed URL asserted, band/lot extracted), JS-shell
listing yielding NOT_FOUND (not a crash, not a false unpublished
claim about the issuer). Two index-shifted pre-existing discovery
tests were made position-independent — no assertions weakened.

**Windows acceptance (still user-side):** restart the API from the
updated checkout and upload the Jio RHP once. Expected: pricing
resolves from the official BSE issue page; if the uploaded filing
establishes fresh-only content, `ofs 0.0` is filing-sourced and only
`issue.fresh_issue` awaits until the final Prospectus is published.

## Addendum 2026-10-18 (2): HTTP 200 homepage — response identity and session

**New Windows evidence:** a direct PowerShell GET of the classic BSE
listing URL returned HTTP 200, `text/html`, 14,287 characters, the BSE
**homepage** (masthead title "LIVE Stock/Share Market | … | BSE
SENSEX | BSE (formerly Bombay Stock Exchange)"), with no Jio text and
no `DisplayIPO`/`IPONo` markers. HTTP 200 was therefore being treated
as a searched listing when no listing had been retrieved at all.

**Why the homepage is served:** the same URLs return the real pages
to a browser-like session (investigator tooling fetched the genuine
listing — title "IPOs Listing|New Live Public Issues on BSE", Jio row
present — and the genuine `DisplayIPO` page with Price Band / Market
Lot, 2026-10-18). The distinguishing factor is the session: BSE
serves its homepage to cookie-less one-shot requests (the Windows
PowerShell GET, and equally this app's previous cookie-less urllib
fetches), while a session that first establishes cookies from the
site receives the real pages. Homepage reachability checks (200) do
not exercise any of this.

**Correction (generic):**
1. **Session-aware retrieval** — `_default_http_fetch` now installs a
   shared cookie-jar opener and performs a one-time best-effort
   homepage warm-up per official host before fetching listing/issue
   pages (skipped for PDF document URLs, so single-document retrieval
   and its retry accounting are unchanged), with a browser header set
   including `Referer`.
2. **Response-identity validation** — fetched listings are classified
   `ok | empty | homepage | shell` before use. Homepage fingerprints
   require the BSE masthead AND absence of genuine issue content
   (issue-detail links, Price Band, Market Lot, Issue Period), because
   real BSE pages share the masthead in their chrome — a real
   DisplayIPO page is never misclassified. A homepage or JS shell
   never counts as a searched listing.
3. **Specific failure reasons** — every stage (listing retrieval,
   listing wrong-page/shell, issue-page retrieval, wrong-page,
   non-HTML, parse, issuer mismatch, missing labelled terms) records
   a precise note carried into the provider report. Outcomes:
   FOUND only for a verified candidate; NOT_FOUND only when at least
   one *valid* listing was actually searched; otherwise UNAVAILABLE
   with the per-URL reasons (resolver maps this to UNAVAILABLE, not
   UNPUBLISHED). Conflicting verified terms still reject outright.

**Honesty bounds:** this sandbox's own HTTPS to BSE/NSE/SEBI fails at
TLS (egress policy), so live retrieval from here reports UNAVAILABLE
with per-URL retrieval reasons — verified above. Mocked/fixture tests
prove the validation and session mechanics (including cookie
persistence over a real loopback socket); they do not prove the
Windows runtime now receives the real BSE pages. If BSE's protection
additionally fingerprints the Python TLS stack, the Windows run will
now fail as UNAVAILABLE naming the homepage wrong-page response —
a precise diagnosis rather than a false unpublished signal — and the
next step would be a browser-session retrieval mechanism, which
would need its own authorization and evidence.

**Regression tests:** observed homepage response → UNAVAILABLE
(+ resolver UNAVAILABLE); homepage on one listing does not poison a
valid listing (FOUND preserved); issue page returning the homepage →
NOT_FOUND-with-valid-listing-searched and the detail names the
wrong-page stage; JS shell → UNAVAILABLE (supersedes the earlier
NOT_FOUND expectation for shells — a shell means no listing was
searched); valid classic listing, `&amp;` decoding and full
query-parameter preservation unchanged; cookie persistence pinned
over loopback. OFS handling is untouched by this correction
(fresh-only filing establishment remains the only zero source).

## Addendum 2026-10-18 (3): Windows activity trace — classification defect repaired; BSE retrieval remains unavailable

**Primary evidence (user's Windows trace `ing-eacd8815051f4222`, at
`ea437f3`, 76.2s):** both BSE listing URLs returned JavaScript
application shells (classified as shells — a listing was *not*
searched), the SEBI listing failed with HTTPError, yet the provider
reported NOT_FOUND and the resolver reported **UNPUBLISHED**. No
evaluation ran; nothing persisted.

**Root cause of the misclassification (code-path traced):** in
`OfficialDiscoveryProvider.find`, any fetched listing that was not a
homepage/shell counted as "reached" — including marker-less `empty`
responses (the NSE listing response on Windows). One such response
flipped the outcome to NOT_FOUND, and `IssueTermsResolver.resolve`
maps any NOT_FOUND provider report to UNPUBLISHED. The conclusion
"unpublished" was therefore unsupported by the very diagnostics
attached to it.

**Corrected semantics (implemented):** a listing counts as *searched*
only when it classifies `ok` (genuine listing content markers:
issue-detail links, Public Issues/Security Name structure,
attachdocs, price-band content). Homepage, shell, and marker-less
responses are unusable and never searched; transport failures
likewise. NOT_FOUND requires at least one valid listing actually
searched; otherwise UNAVAILABLE with every per-URL reason retained.
UNPUBLISHED now arises only from a genuine NOT_FOUND (a valid listing
searched, no issuer-matched document) or a genuinely searched
retained-document set — per the existing resolver rule, unchanged.
CONFLICT semantics unchanged. The activity trace now shows
"Official discovery outcome: UNAVAILABLE" for this scenario, and the
ingestion terminal remains BLOCKED (AWAITING_ISSUE_TERMS) with
evaluation/persistence explicitly not run.

**Why the cookie-session fix did not resolve Windows discovery:**
the trace was produced with the session-aware fetcher (`589159a`)
already live, and BSE still returned the application shell for both
listing URLs. BSE's protection evidently requires JavaScript-executed
session state (the investigator's rendering fetcher receives the real
server-rendered/pages content; raw HTTP clients — PowerShell,
urllib with or without cookie warm-up — receive the homepage or the
shell). Cookie persistence is proven only as a mechanism (loopback);
it does not make BSE accept the request, and no further header/cookie
variation is evidence-supported. **BSE retrieval status: still
unavailable to this application on the Windows runtime; not fixed,
and not claimed fixed.** A headless-browser retrieval mechanism
would be a new runtime dependency and architecture decision requiring
separate authorization and its own evidence; until then the correct
terminal behaviour is UNAVAILABLE with precise per-URL reasons —
never UNPUBLISHED.

**Jio official-prospectus configuration (investigated):**
issuer-specific official URLs are operator configuration via
environment JSON maps (`IPO_PRICE_BAND_NOTICE_URLS`,
`IPO_PROSPECTUS_URLS` in `build_resolver_from_env`). The Windows
environment evidently has a prospectus map (the provider ran and
reported no URL *for this issuer*); it contains no Jio entry, and
none may be invented or copied from another issuer's configuration.
Automatic discovery remains the intended configuration-free path; it
is currently blocked at the BSE/SEBI retrieval stage above, not at
configuration. No Jio URL or term values were hardcoded.

**Regression tests:** all-shell listings → UNAVAILABLE (resolver
explicitly not UNPUBLISHED); marker-less pages → UNAVAILABLE with
reason; valid listing searched with no match → NOT_FOUND →
UNPUBLISHED (the genuine rule); shell-on-one-listing + valid
unmatched listing → NOT_FOUND with the shell reason retained;
service/activity consistency test reproducing the Windows trace
(resolution status UNAVAILABLE, "Official discovery outcome:
UNAVAILABLE", no UNPUBLISHED anywhere in the trace, BLOCKED terminal,
evaluation SKIPPED, nothing persisted). The `LISTING_EMPTY` fixture
now models a valid searched listing with no matching issuer, which
is what NOT_FOUND means under the corrected semantics.
