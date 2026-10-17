# Generic Issue-Terms / OFS Extraction Rectification

- **Date:** 2026-10-17 · **Baseline:** `11fb0cb85abc85fa73b1e760702f5f8ed85a9d86` · **Trigger:** Windows live evidence (Vishal Nirmiti): Prospectus pathway verified working (`OFFICIAL_VERIFIED` floor ₹208 / cap ₹220 / lot 68 from `SRC-PROSPECTUS-6C8D0346`), but `EV-issue.fresh_shares` recorded **1,500,000** — the OFS quantity — against the quotation *"…(FRESH OFFER) AND AN OFFER FOR SALE OF UP TO 15,00,000 EQUITY SHARES"*.

## Proven root cause

`SectionExtractor.extract_cover_and_offer` (`extraction/sections.py`) matched fresh shares with `fresh (?:offer|issue)[^\n]*?(?:of )?(?:up to )?([0-9,]+) equity shares`. The lazy span crosses the intervening *"AND AN OFFER FOR SALE OF UP TO"* clause and captures the OFS quantity as `issue.fresh_shares`. The same unguarded-span shape existed in the fresh-issue amount match. Separately, OFS seller enumeration required every seller to be preceded by "by", so sellers listed after commas/"and" were missed, and the single captured seller was silently attributed the aggregate OFS quantity.

## Correction (generic; no issuer-specific logic)

- **Label-bound quantity resolution** (`_labelled_quantity_candidates` / `_resolve_labelled_quantity`): a quantity is bound to its semantic label (`fresh offer|issue`, `offer for sale`) only within a bounded window and only when no other component's label intervenes; distinct surviving values for one label are contradictory and fail closed (no extraction). Fresh amount matching received the same guard.
- **Before/after (regression case):** `fresh_shares` 1,500,000 (OFS quantity, wrong) → **65,90,909** from its own fresh clause where stated; where the fresh quantity is stated only as an amount, `fresh_shares` is now absent rather than misassigned. `ofs_sellers[0].shares_sold` = 1,500,000, separately mapped from the OFS clause.
- **Seller enumeration** is anchored on the `("SELLING SHAREHOLDER")` marker, so all listed sellers are found. Sole named seller ⇒ the cover's aggregate OFS quantity is that seller's `shares_sold`. Multiple sellers with only an aggregate ⇒ canonical `ofs_sellers` stays empty (identity preserved in the evidence quotation) so OFS derivation fails closed rather than attributing the aggregate to an individual. Known model limitation (documented, not silently fixed): the v1.5 seller schema requires numeric `pre_issue_shares`, which a cover does not independently establish; for the sole-seller case it continues to carry the established sold quantity, as in existing records — separating it requires a schema decision.
- **OFS value semantics unchanged:** the established derivation (`sum(shares_sold) × cap ÷ 100000`, `SRC-DERIVED` evidence, labelled derived — never `OFFICIAL_VERIFIED` as a quoted fact) runs only when quantity scope and cap are established; blocked otherwise. It yields the maximum indicated OFS value at cap (1,500,000 × ₹220 = ₹330 lakh in the regression case), not final proceeds.
- **Quotation quality:** `ProspectusTermsParser._quote_window` now snaps to sentence boundaries (exact source substring, whitespace-normalised as before): the cap quotation renders as *“Cap Price” The higher end of the Price Band, in this case being, ₹ 220 per Equity Share above which no Bids were accepted.* instead of a mid-text fragment.
- The dated-title Prospectus classification from `11fb0cb` was re-verified and not altered; the host allowlist was not broadened; a Prospectus is still never labelled a Price Band Notice.

## Tests

- `tests/test_generic_issue_terms_extraction.py` (7, new): Windows regression shape; amount-only fresh clause; fresh-only and OFS-only covers; multiple sellers (aggregate unattributed, identities in quotation); contradictory quantities fail closed; quote-boundary snapping. Fixtures use invented issuers with distinct quantities.
- Focused: generic + prospectus pathway + Step 5 suites **40 passed**. Real-filing suites (RK reconciliation, cross-IPO provenance, Vishal golden/historical) **32 passed**.
- **Full Python suite: 973 passed. Frontend: 64 passed** (no frontend change). Golden `e84f8bc0…` and frozen core intact within the suite. No live SEBI retrieval was exercised from this sandbox and none is claimed; Windows acceptance remains the user's run.

## Windows live acceptance

```powershell
cd G:\ipo-screening-engine\ipo-screening-engine
git fetch origin
git checkout arena/5dd3fe52-ipo-screening-engine
git pull origin arena/5dd3fe52-ipo-screening-engine
$env:PYTHONPATH = "engine"
$env:IPO_PROSPECTUS_URLS = '{"VISHAL-NIRMITI-LIMITED":"https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"}'
python -m uvicorn ipo_screening.presentation.api:app --host 127.0.0.1 --port 8000
```

Restart the server and upload the Vishal RHP fresh (new evaluation, so stale evidence cannot mask the correction). Checklist: `git log --oneline -1` shows this rectification commit; evidence shows floor/cap/lot `OFFICIAL_VERIFIED` (`SRC-PROSPECTUS-…`) with bounded definition quotations; `EV-issue.fresh_shares` = **65,90,909** (not 15,00,000); `EV-issue-ofs_sellers` names Vaman Prestressing with `shares_sold` 15,00,000 from `RHP-FILING-…`; `issue.ofs` = 3300 (₹ lakh) with `DERIVED` provenance; final evaluation is produced. If any term remains unresolved, read `resolution.providers` in the 422 body / UI diagnostics panel.

For another issuer, populate the same contract generically: `IPO_PROSPECTUS_URLS` maps that IPO's runtime `ipo_id` (as extracted from its filing) to its final Prospectus URL on an allow-listed official host (SEBI/NSE/BSE); `IPO_PRICE_BAND_NOTICE_URLS` likewise for a genuine Price Band Notice. No code change per issuer is required or permitted.
