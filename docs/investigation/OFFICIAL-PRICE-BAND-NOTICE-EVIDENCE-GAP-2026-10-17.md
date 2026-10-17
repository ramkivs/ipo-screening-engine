# Official Price Band Notice — Evidence Gap Record (Vishal Nirmiti)

- **Date:** 2026-10-17 · **Baseline:** `8dba4bb0f3b0758e960bb62ef6f120eaf134419b` (Step 5) · PR #6 · **Nature:** evidence record. It promotes nothing to official status and changes no behaviour.

## What the authentic official record establishes

The Vishal Nirmiti IPO (CIN `U01122MH1994PLC185445`; offer 30 Sep – 5 Oct 2026; listed 8 Oct 2026) concluded, and its final offer documents are filed on official hosts:

| Document | Official location | Terms established | Document type |
|---|---|---|---|
| Final Prospectus dated 5 Oct 2026 | SEBI: `https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf` (host `www.sebi.gov.in` — allow-listed) | Floor ₹208, Cap ₹220 ("Floor Price … ₹ 208"; maximum ₹220) | **Prospectus — not a Price Band Notice** |
| Final Prospectus dated 5 Oct 2026 | NSE archives: `https://nsearchives.nseindia.com/corporate/FP_INE1O5L01025_06OCT2026.pdf` | Floor ₹208, Cap ₹220, **"Bid Lot 68 Equity Shares and in multiples of 68"** | Prospectus; host subdomain `nsearchives.nseindia.com` is **not** in `OFFICIAL_HOSTS` (exact-host allowlist: `nseindia.com`, `www.nseindia.com`, `bseindia.com`, `www.bseindia.com`, `sebi.gov.in`, `www.sebi.gov.in`) |
| Price Band Notice (price band advertisement) | Published ~26 Sep 2026 in Financial Express, Jansatta and Navshakti, as the Prospectus itself records ("The Price Band and the minimum Bid Lot … was advertised in all editions of Financial Express … Jansatta … Navshakti"); newspaper reports of the company's advertisement appeared 26 Sep 2026 | Floor ₹208 / Cap ₹220 / lot 68 (as advertised) | **The genuine Price Band Notice — no PDF of it was located on any allow-listed host.** The BRLM (Saffron Capital Advisors, `saffronadvisor.com`) hosts the DRHP/RHP only, and is not an allow-listed host. |

The official Prospectus therefore *corroborates* 208/220/68. Corroboration is not notice verification: no third-party report, summary, or snippet was treated as official evidence.

## Precise blockers

1. **Document-class contract gap (decision required).** The only allow-listed-host documents located are the final Prospectus. Routing a Prospectus through `IPO_PRICE_BAND_NOTICE_URLS` would stamp `SRC-PBN-…` exchange-notice provenance onto a Prospectus. The existing parser's document classification is token-based (`price_band_notice.py::_classify_document`: notice-title pattern or ≥4 semantic tokens) and does not establish that a document *is* a Price Band Notice rather than a Prospectus that mentions one. Accepting prospectus-class filings as qualifying issue-term evidence is a new document-class contract decision. Options: (a) approve the final Prospectus filed on SEBI/exchange as a qualifying official document class for issue terms (with honest provenance labelling — not `SRC-PBN` notice labelling as-is); (b) obtain the actual price band advertisement PDF from an allow-listed host (exchange/issuer publication) and configure its URL; (c) extend the host allowlist (e.g. `nsearchives.nseindia.com`) — necessary for the NSE copy but insufficient alone, since the document-type question remains.
2. **Environment cannot execute live verification.** This sandbox's egress is restricted (GitHub/npm/PyPI only): HTTPS retrieval of `sebi.gov.in`/`nseindia.com` fails (TLS EOF), and page fetch of the SEBI PDF failed. Live `OFFICIAL_VERIFIED` resolution therefore cannot be executed or acceptance-claimed from this environment. On an unrestricted host, the operator path is: decide (1), set `IPO_PRICE_BAND_NOTICE_URLS` to the approved official URL for `VISHAL-NIRMITI-LIMITED`, restart the app, and re-upload the RHP — resolution, persistence, and reopening are already implemented and test-covered.

## What is already proven (mechanics, not live authenticity)

- Verified-channel resolution → canonical 208/220/68 + derived OFS 3300 → persisted → evidence API `OFFICIAL_VERIFIED` with document identity and verbatim quotation (`tests/test_cross_ipo_issue_term_provenance.py`; mocked transport, as labelled there).
- Manual entries remain `UNVERIFIED`; unresolved terms fail closed `AWAITING_ISSUE_TERMS`; retained copies never resolve (Step 5 suite).
- **New:** a manual entry conflicting with an officially verified value blocks with `existing_origin: OFFICIAL_VERIFIED`, and even after explicit confirmation the verified value wins with no `MANUAL_ENTRY` provenance recorded (`test_manual_entry_never_displaces_officially_verified_values`).

## Bottom line

`OFFICIAL_VERIFIED` resolution of the real filing is **not yet demonstrated against a live authentic notice**, for two independent, precisely identified reasons: the genuine notice document has not been located on an allow-listed host (only the final Prospectus has, raising a document-class decision), and this environment cannot retrieve exchange/SEBI documents at all. Manual entry (Step 5) remains the authorized interim path and stays `UNVERIFIED`.
