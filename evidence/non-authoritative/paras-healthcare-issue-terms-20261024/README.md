# Paras Healthcare — Official Issue-Term Source Capture (2026-10-24)

Status: NON-AUTHORITATIVE INVESTIGATION EVIDENCE. This package is not a source approval, not an issue-term resolution, not a canonical record, and not an evaluation input. **The values captured here were not written into the engine, into any configuration, into any store, and into no evaluation.** The assessment that uses them is recorded in [`docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md` §15](../../../docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md).

## Why this package exists

The retained RHP (`evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf`) prints `[●]` for `issue.price_band_low`, `issue.price_band_high` and `issue.lot_size`. Those three terms are the only reason the ingestion gate stays closed. This package records the official sources that disclose them, so the gap is documented with provenance instead of being argued from memory or from press coverage.

## Contents

| Key | File (`source-captures/`) | Official source | Chunk | Result |
|---|---|---|---|---|
| BSE-DETAIL | `bse-displayipo-4895-chunk-0.md` | BSE Limited — issue-information page, `DisplayIPO?id=4895&…&IPONo=8048` | 0 of 1 | **Price Band `660.00-693.00`; Market Lot `21`; Minimum Bid Quantity `21`; Issue Period `21 Oct 2026 to 23 Oct 2026`; Symbol `PARASHLTH`; Face Value `1.00`** |
| BSE-LIST | `bse-historical-listing-chunk-0-prefix.md` | BSE Limited — Historical Public Issues listing | 0 of 2 (prefix) | Paras row: `21-10-2026 | 23-10-2026 | 660.00 - 693.00 | 1.00 | Book Building`, linking `IPONo=8048` |
| BSE-NOTICE | `bse-notice-20261019-49-chunk-0.md` | BSE Limited — Notice 20261019-49 (19 Oct 2026) | 0 of 1 | Anchor portion of the same issue subscribed at **Rs. 693/- per equity share** — corroborates the cap price |
| SEBI-RHP | `sebi-abridged-prospectus-chunk-0-prefix.md` | SEBI — abridged prospectus / RHP memorandum PDF | 0 of 8 (prefix) | Fresh issue **₹5,000.00 million**, OFS **₹9,500.00 million**, total **₹14,500.00 million**; bid/offer period 21–23 Oct 2026 — corroborates the already-resolved date and monetary terms; **no price band or lot in the retained prefix** |

[`capture-manifest.json`](capture-manifest.json) records the URLs, the quoted values and locators, byte counts, SHA-256 digests, and everything that was attempted and **not** retrieved.

## Issuer and issue identity

Every artifact names the same issuer and the same issue: `Paras Healthcare Limited`, CIN `U85110HR1987PLC035823`, BSE issue `8048`, symbol `PARASHLTH`, period 21–23 October 2026. The identity match is on the exchange's own page — company name in the issue-table heading, its own symbol, its own issue number — not on a name-similarity heuristic.

## What these files are — and are not

- **They are** the rendered Markdown `content` strings returned by Arena's `functions.fetch_page` tool, written as UTF-8 files.
- **They are not** provider response bytes. Headers, exact receipt time and the tool's cache status were unavailable, and no per-artifact retrieval window is claimed: this pass did not bracket each call with sandbox clock reads.
- **BSE-LIST and SEBI-RHP are excerpts** and say so in the file text. BSE-DETAIL and BSE-NOTICE are complete chunk 0s.
- **Transcription fidelity cannot be machine-verified** against the tool output. The figures that matter — `660.00-693.00`, `21`, the issue period, `₹5,000.00 million`, `₹9,500.00 million` — were checked against the rendered page text at capture time.

## Hash subject and verification

**Hash subject:** the exact bytes of each retained file under `source-captures/`. Digests are uppercase SHA-256. They establish the integrity of these local files only — not provider-byte identity, source authenticity, or the truth of any value.

```sh
sha256sum source-captures/*
```

## Limits on reuse — read before citing

1. **This is not admissible to the engine as it stands.** BSE serves the issue page under `status=H` (historical/closed). The discovery contract follows only BSE records with `Status` of `F` (forthcoming) or `L` (live) — `engine/ipo_screening/official_issue_sources.py`. The page therefore cannot supply a term through the supported path, and no code was changed to admit it. See §15.4 of the investigation report.
2. **The sandbox cannot retrieve any of this directly.** Sandbox egress to `bseindia.com`, `nseindia.com`, `sebi.gov.in` and `api.bseindia.com` fails at TLS (`curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL`; the engine's urllib transport fails identically). The engine's discovery therefore reports `UNAVAILABLE`, which is a transport statement and never evidence that the terms are unpublished.
3. **The price-band advertisement itself was not retrieved.** `https://listing.bseindia.com/Download/8888888/PreAnchor/PBA_20261015184043.pdf` — the document class the engine's notice parser is built for — failed three times through the proxy. Whether it exists is not in question; whether this environment can read it is.
4. **No third-party value is used.** Many aggregators publish 660–693 and a 21-share lot. None was retained or used: a snippet is not an official source.
5. **Nothing here resolves a term.** Recording evidence is not resolving a term; the gate stays closed and no evaluation may follow from these files.
