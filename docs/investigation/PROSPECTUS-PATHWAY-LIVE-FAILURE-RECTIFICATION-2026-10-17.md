# Prospectus Pathway Live Failure — Root Cause and Rectification

- **Date:** 2026-10-17 · **Baseline:** `12e5f043c0c82c033c457aaa1a9f6e2a5d782c09` · **Symptom (Windows, live):** with `IPO_PROSPECTUS_URLS={"VISHAL-NIRMITI-LIMITED":"https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"}` set, re-uploading the Vishal Nirmiti RHP still returned `AWAITING_ISSUE_TERMS` for `price_band_low, price_band_high, lot_size, ofs` — "official sources could not be retrieved or verified".

## Root cause (confirmed in code, reproduced)

The trace A–I was executed against the code and the real document's cover text:

- **A. Env loading:** `build_resolver_from_env()` parses `IPO_PROSPECTUS_URLS` and registers `HttpProspectusProvider`; `PresentationService` installs it when no resolver is injected. Not the failure (a JSON-malformed value would silently skip registration — see diagnostics below).
- **B. IPO identity:** the filing's runtime `ipo_id` is `VISHAL-NIRMITI-LIMITED`, matching the configured key. Not the failure.
- **C. Provider order/invocation:** notice providers (none configured) then the prospectus provider; invoked. Not the failure.
- **D. HTTP:** default fetcher used a bare library user agent (`ipo-screening-engine/1.5`) — a retrieval-compat risk against SEBI's bot filtering, hardened (below), but not provable as the live failure from this environment.
- **E. Classification — THE CONFIRMED DEFECT:** `ProspectusTermsParser` rejected any document whose first two pages mentioned "red herring". The genuine final Prospectus's opening pages *reference* the Red Herring Prospectus in the LISTING section ("The Equity Shares issued through the Red Herring Prospectus and this Prospectus are proposed to be listed on … NSE … BSE"), as confirmed in the SEBI-filed document text. The parser therefore raised `ProspectusClassificationError` on the real document → provider `REJECTED` → no verified candidates → resolver `UNAVAILABLE` → the exact user-visible message. Reproduced deterministically with cover text modelled on the real filing (rejected before the fix, parses 208/220/68 after).
- **F. Extraction:** floor/cap/Bid-Lot patterns match the real definition language; not the failure once classification passes.
- **G. Qualification/persistence:** unchanged and covered; not the failure.
- **H. OFS:** not an independent blocker. Once the cap is established, the established assembly derivation (`sum(ofs_sellers.shares_sold) × cap / 100000`, seller shares from the RHP) supplies OFS 3300 — regression-tested. OFS appeared in the live missing list only because pricing never resolved and assembly never ran.
- **I. Awaiting condition:** fires when unresolved fields remain after resolution/assembly — the downstream consequence of (E).

## Correction (smallest, fail-closed preserved)

1. `extraction/prospectus_terms.py`: classification now turns on the **dated document title** — `((?:Draft )? (?:Red Herring )?Prospectus) Dated:` — instead of a blanket text search. A final Prospectus that references the RHP in its body is accepted; documents titled Red Herring Prospectus / Draft Red Herring Prospectus are still rejected. CIN + issuer-identity gates unchanged.
2. `issue_terms.py`: shared `_default_http_fetch` with a browser-compatible header set for both official providers (the host allowlist remains the security boundary; it was not broadened).
3. `frontend/app.js`: the awaiting panel now surfaces the resolver's per-provider diagnostics (`resolution.providers`: provider / outcome / detail), so retrieval failure vs document rejection vs unconfigured sources are distinguishable in the UI and in the raw 422 API body.

No values were hard-coded; 208/220/68 remain expected results validated against retrieved document evidence. No schema, scoring, allowlist, or provenance changes.

## Tests

- `tests/test_official_prospectus_pathway.py` — 15 tests (4 new): realistic final-Prospectus cover with an RHP body reference is accepted and yields 208/220/68; RHP and DRHP dated titles rejected; default fetcher sends browser-compatible headers (captured request); Prospectus ingest derives OFS 3300 from RHP seller shares once the cap resolves. Full Python suite and frontend suite re-run at the rectification commit (results in the tracker entry).
- Mocked transport proves mechanics only. **Live SEBI retrieval was not tested from this sandbox** (egress blocked, TLS EOF) and is not claimed.

## Remaining blockers and Windows live acceptance

The confirmed code defect is fixed. What cannot be verified from Arena: whether the Windows host's retrieval of the SEBI PDF now succeeds end-to-end (network/TLS/UA behaviour is environment-specific). After deploying this commit on Windows:

1. Pull `arena/5dd3fe52-ipo-screening-engine` (this rectification commit) in `G:\ipo-screening-engine\ipo-screening-engine`.
2. Start exactly as before (`IPO_PROSPECTUS_URLS` set as reported, `PYTHONPATH=engine`, uvicorn on 127.0.0.1:8000).
3. Re-upload the Vishal Nirmiti RHP. Expected: `201` evaluation with no manual entry; evidence shows `issue.price_band_low/high/lot_size` as `OFFICIAL_VERIFIED` with `SRC-PROSPECTUS-…` sources and "Final Prospectus" locators, `issue.ofs` derived, and the issue-terms report carrying `document_class: OFFICIAL_PROSPECTUS`, provider `official-prospectus`.
4. If it still awaits: open the browser dev-tools network response (or `curl` the same POST) and read `resolution.providers` in the 422 body — `official-prospectus / UNAVAILABLE: official source retrieval failed: …` indicates a Windows-side network/TLS problem with the exact exception; `REJECTED: retrieved document is not an established final Prospectus: …` indicates a document-content/parser issue with the exact reason; absence of the `official-prospectus` provider line indicates the env var did not reach the server process (check the PowerShell session that launched uvicorn). The UI panel now displays the same diagnostics.
