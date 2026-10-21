# PA-authorized third-party issue-term fallback

The user's explicit 22 October 2026 instruction supersedes the previous official-disclosure-only choice **for the opt-in aggregator mode**. It does not authorize fabrication, shares × cap cash derivation, issuer exceptions, or changes to scoring, schema, goldens, historical evaluations or prior policy records.

## Active contract

- Set `IPO_ALLOW_AGGREGATOR_ISSUE_TERMS=1` in the API process environment. Default `0` preserves official-only behavior; other values fail configuration validation. The native acceptance workflow explicitly enables `1`.
- Finish existing filing extraction and official discovery/native/OCR resolution first. An official conflict or assembly failure cannot be overridden.
- Fill only missing fresh issue, OFS, band or lot fields. Preserve existing values, including explicit OFS NIL → 0. Unknown/placeholder is not zero. Dates must already be established by filing/official evidence; the aggregator does not create the issue window.
- Accept only allowed public HTTPS issuer-detail pages, exact issuer IPO heading and the same explicit open/close window. Use explicit currency and scale on fresh/OFS table rows, not total issue size, prose, GMP, reservations or share-count multiplication. Unsupported layouts, missing scale, stale periods, ambiguous/repeated conflicting rows and incompatible prices fail closed.
- Automatic detail discovery follows actual issuer links on the qualified listings. Optional `IPO_AGGREGATOR_ISSUE_URLS` is a JSON IPO-ID → allowed public detail-URL mapping, **not a table of values**. There are no issuer-specific engine rules or configured prices. InvestorGain listing leads that are only GMP links are not consumed as issue terms.
- Preserve existing official values; a publisher contradicting an existing term is rejected as a source. Conflicting qualified publishers are not first-wins. A source must satisfy the implemented table contract; an allowed hostname alone is insufficient.
- Persist source URI, actual response SHA-256/retrieval time, original quote, row locator and `TABLE_EXTRACTION` under existing `MARKET_DATA` schema. Source/evidence carry `THIRD_PARTY_AGGREGATOR_OVERRIDE`, policy `pa-aggregator-issue-terms-v1` and explicit UNVERIFIED / NOT official wording. Never promote this path to `OFFICIAL_VERIFIED` or feed it through the official verification gate.
- Evaluation summary/detail warnings and evidence classification disclose this authority after restart; activity records the separate fallback stage. No suitable value leaves the original placeholder and awaiting gate intact.

This is a deliberately explicit authority-policy change, not an extraction fix or an assertion that the third-party statement is an official disclosure. Existing financial/scoring/knockout/confidence rules are unchanged. Module execution does not imply a favourable investment verdict.

Idempotency is scoped to qualified assertions (publisher URL, issuer/window, field values/units/quotes/row labels), not unrelated changing HTML. Every raw response keeps its full content hash. Identical asserted inputs return the original immutable evaluation/manifest, while the latest retrieval remains visible in ingestion diagnostics. No transport cache, TTL or freshness policy is introduced.
