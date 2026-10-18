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
