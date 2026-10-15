# MarketLiveIPOGMP — Tonbo Imaging India IPO GMP Capture (2026-10-15)

Status: NON-AUTHORITATIVE INVESTIGATION EVIDENCE. This package is not a source approval, an A9 qualification, a qualifying GMP snapshot, or an A9 required hash. The determination that uses it — **MarketLiveIPOGMP: NOT QUALIFIED, conditionally viable** — is recorded in [`A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md`](../../../docs/investigation/A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md).

## Contents

All retrieval windows are on 2026-10-15. Each was read from the sandbox UTC clock before and after the tool call; one clock read may close one window and open the next.

| Key | File (`source-captures/`) | Source URL | Chunk | Retrieval window (UTC) | Excerpt |
|---|---|---|---|---|---|
| ML-T | `marketliveipogmp-ipo-tonbo-imaging-india-chunk-0.md` | https://marketliveipogmp.com/ipo/tonbo-imaging-india | 0 of 1 | 13:15:14.096Z – 13:17:58.770Z | none |
| ML-A | `marketliveipogmp-about-chunk-0.md` | https://marketliveipogmp.com/about | 0 of 1 | 13:14:14.112Z – 13:14:56.997Z | none |
| ML-H | `marketliveipogmp-home-chunk-0.md` | https://marketliveipogmp.com/ | 0 of 1 | 13:14:56.997Z – 13:15:14.096Z | none |
| ML-L | `marketliveipogmp-learn-chunk-0.md` | https://marketliveipogmp.com/learn | 0 of 1 | 13:22:53.942Z – 13:24:26.607Z | none |
| ML-TR | `marketliveipogmp-track-record-chunk-0.md` | https://marketliveipogmp.com/track-record | 0 of 4 | 13:18:17.492Z – 13:18:32.503Z | none |
| ML-HM | `marketliveipogmp-ipo-hero-motors-chunk-0.md` | https://marketliveipogmp.com/ipo/hero-motors | 0 of 1 | 13:18:32.503Z – 13:22:53.942Z | none |
| ML-S | `marketliveipogmp-sitemap-chunk-0-prefix.txt` | https://marketliveipogmp.com/sitemap.xml | 0 of 4 | 13:17:58.770Z – 13:18:17.492Z | contiguous prefix (first 20 entries) |
| ML-R | `marketliveipogmp-robots.txt` | https://marketliveipogmp.com/robots.txt | 0 of 1 | 13:11:09.958Z – 13:11:32.551Z | none |

A second retrieval of the Tonbo page at 13:32:55.692Z – 13:33:04.729Z (19:02–19:03 IST) produced a transcription byte-identical to ML-T, so it is recorded in the manifest (`derivedChecks.tonboRecapture`) rather than retained as a duplicate file. The R7 follow-up retrieval at 13:54:22.896Z – 13:54:30.144Z (19:24 IST) was also byte-identical: no reading newer than 15 Oct 4:02 pm IST was displayed (`derivedChecks.tonboRecaptureR7Followup`).

[`capture-manifest.json`](capture-manifest.json) records byte counts, SHA-256 digests, page titles, IST conversions of each window, the sandbox clock check, the excerpt boundary for ML-S, and the items not retrieved.

## What these files are — and are not

- **They are** the rendered Markdown `content` strings returned by Arena's `functions.fetch_page` tool, transcribed by the agent in JSON-escaped form, JSON-decoded, and written as UTF-8 without a BOM or an added trailing newline. ML-H contains literal `\\` line-break markers produced by the tool inside link text; they are retained as returned.
- **They are not** provider response bytes. Response headers, exact receipt time, and the tool's cache status were unavailable. The sandbox could not connect to `marketliveipogmp.com` directly (`curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL`; egress allowlist).
- **ML-S is an excerpt.** It is the contiguous prefix of the chunk-0 content string through the `hero-motors` entry. The rest of chunk 0 and chunks 1–3 were not retained or not retrieved.
- **The GMP history chart is not in these files.** The rendered text exposes only the range line and the axis labels (ML-T lines 15 and 17).
- **Retrieval windows** bracket each tool call. They do not establish when the publisher generated the content. The sandbox clock matched the `api.github.com` `Date` header to its one-second resolution.
- **Transcription fidelity** cannot be machine-verified against the tool output. GMP figures, timestamps, missing-value markers, and the 546 line-break markers in ML-H were spot-checked.

## Hash subject and verification

**Hash subject:** the exact bytes of each retained file in `source-captures/`. Digests are uppercase SHA-256, following the repository's evidence convention. They establish the integrity of these local files only — not provider-byte identity, source authenticity, or the truth of any GMP value. The A9 decision defines no required GMP hash subject; these digests are not one.

Verify from this directory and compare case-insensitively with `capture-manifest.json`:

```sh
sha256sum source-captures/*
```

## Limits on reuse

The publisher pages are mutable, so re-fetching them will not reproduce these files. `robots.txt` allows `/` for generic agents; only public pages and the sitemap it lists were requested, and no API path was queried. No provider was contacted.
