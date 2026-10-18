# Jio Platforms RHP — Issue-Term Resolution

- **Date:** 2026-10-17 · **Baseline:** `294c77d847bc080fdd6397036afc5fd771d67909` (adds the NON-AUTHORITATIVE investigation PDF `evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`, 591 pages) · The PDF is investigation evidence only; it is not an accepted official source and confers no provenance.

## What the document actually states (inspected + executed)

| Field | PDF disclosure | Page/evidence |
|---|---|---|
| Identity | `JIO PLATFORMS LIMITED`, CIN `U72900GJ2019PLC110816` | Cover p.1 |
| `price_band_low` / `price_band_high` | `₹[●]` placeholders ("Floor Price of ₹[●] … to the Cap Price of ₹[●]") | Definitions p.13; cover p.1 |
| `lot_size` | "minimum Bid Lot … will be decided" — not disclosed | p.3, p.13 |
| `ofs` | **Fresh-issue only**: "OFFER FOR SALE SIZE … Not applicable" | Cover table p.1 |
| Fresh shares | Up to 270,000,000 Equity Shares | Cover p.1 |
| Fresh-issue amount | "aggregating up to ₹[●] million" — placeholder | Cover p.1 |
| Dates | Bid/Issue opens Wed, October 21, 2026; closes Fri, October 23, 2026 | p.2 |

## Demonstrated defects found by running the real path (all generic, none Jio-specific)

1. **Company-identity pollution:** cover logo/header lines (`A \nMPLS`) were swallowed into the issuer name, producing company `A \nMPLS … JIO PLATFORMS LIMITED` and runtime IPO ID `A-MPLS-JIO-PLATFORMS-LIMITED`. Fix (`extraction/sections.py`): within the cover span, the issuer name is the standalone multi-token line ending in `LIMITED` (document-title prefixes were already stripped; logo matter was not).
2. **Fresh-only OFS unrecognised:** the NIL-OFS extraction accepted only the literal `NIL`; the standard cover-table wording `Not applicable` left `issue.ofs = None`, which would block evaluation forever for any fresh-only issuer (pricing sources cannot supply it). Fix: the bound cover-table pattern now accepts `NIL | Not Applicable`. After the fix the filing itself establishes `issue.ofs = 0.0`, `ofs_sellers = []`.
3. **Weekday-prefixed dates unrecognised:** "BID/ ISSUE OPENS ON WEDNESDAY, OCTOBER 21, 2026" did not match the date patterns. Fix: optional weekday prefix in both open/close patterns. The filing now establishes both dates.
4. **Fresh-issue amount unobtainable on the verified pathway:** with pricing resolved, evaluation failed schema validation (`issue/fresh_issue: None`). The RHP amount is genuinely `[●]`; the final Prospectus states it on its cover but `ProspectusTermsParser` never extracted it and assembly never carried it. Fix: the parser extracts the stated fresh-issue aggregating amount **with its stated unit** (only when explicitly established; `[●]` stays `None`), `to_enrichment_dict` carries it, and `EnrichmentEngine` applies it — converted into the canonical reporting unit, with the document's own `OFFICIAL_VERIFIED` provenance. It is never computed from price × shares.

After the fixes, real extraction yields: `JIO PLATFORMS LIMITED` / `JIO-PLATFORMS-LIMITED`, `ofs 0.0` (FILING), `fresh_shares 270000000` (FILING), open/close `2026-10-21`/`2026-10-23` (FILING), pricing + amount still missing — correctly fail-closed: with no official source, `AWAITING_ISSUE_TERMS` names exactly `price_band_low, price_band_high, lot_size` (OFS no longer blocks spuriously).

## Completion path (validated with controlled transport — mechanics, not live retrieval)

With an official final Prospectus retrievable through `IPO_PROSPECTUS_URLS` (allow-listed host, keyed `JIO-PLATFORMS-LIMITED` or the company name), the same RHP evaluates end-to-end: pricing/lot and fresh-issue amount `OFFICIAL_VERIFIED` (amount unit-converted, e.g. stated ₹ million → canonical INR lakhs), OFS `0.0` remains `FILING`, and the evaluation persists. The repository-controlled run used a synthetic prospectus text via injected fetcher — it proves the pathway, not the existence, availability or contents of any real Jio Prospectus, and no Jio values in any test are asserted as real-world facts. Manual entry remains unchanged in scope (3 bounded terms, `MANUAL_ENTRY`); it cannot and need not supply OFS here.

## Validation

- `tests/test_jio_rhp_issue_terms.py` (7): real-PDF disclosure/identity/OFS/dates/placeholders; logo-name, Not-Applicable-OFS and weekday-date stub regressions; parser amount stated-vs-placeholder; fail-closed-on-pricing-only; full prospectus-pathway completion with persisted evidence assertions.
- Affected suites (generic extraction, RK, Vishal golden, prospectus pathway, derived evidence, UI7, Step-5, cross-IPO, runtime path): all passed. **Full Python: 995 passed. Frontend: 68 passed.** Golden/frozen intact. Vishal correction (`5c5c110`) preserved — shared-component changes (sections extraction) are covered by the Vishal/RK/golden suites above.

## Remaining action (external only)

When Jio's official final Prospectus (or Price Band Notice) is genuinely published on SEBI/NSE/BSE, configure its URL for `JIO-PLATFORMS-LIMITED` in `IPO_PROSPECTUS_URLS`/`IPO_PRICE_BAND_NOTICE_URLS`, restart, and upload the RHP: no further code or manual entry is required. Note the notice alone does not state the fresh-issue amount in this pathway; the final Prospectus is the completing document class. Windows acceptance of that live run remains the user's — Arena exercised controlled transport only and claims no live SEBI retrieval.
