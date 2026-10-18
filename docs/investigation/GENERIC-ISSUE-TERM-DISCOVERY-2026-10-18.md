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
