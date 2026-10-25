# InvestorGain — Tonbo Imaging India IPO GMP Capture (2026-10-15)

Status: NON-AUTHORITATIVE INVESTIGATION EVIDENCE. This package is not a source approval, an A9 qualification, a qualifying GMP snapshot, or an A9 required hash. The determination that uses it — **InvestorGain: NOT QUALIFIED** — is recorded in [`A9-GMP-INVESTORGAIN-QUALIFICATION-2026-10-15.md`](../../../docs/investigation/A9-GMP-INVESTORGAIN-QUALIFICATION-2026-10-15.md).

## Contents

All retrieval windows are on 2026-10-15, read from the sandbox UTC clock immediately before and after each tool call.

| Key | File (`source-captures/`) | Source URL | Chunk | Retrieval window (UTC) | Redaction |
|---|---|---|---|---|---|
| T0 | `investorgain-gmp-tonbo-2369-chunk-0.md` | https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/ | 0 of 2 | 12:29:10.103Z – 12:29:12.222Z | none |
| T1 | `investorgain-gmp-tonbo-2369-chunk-1-redacted.md` | same | 1 of 2 | 12:29:50.668Z – 12:29:51.831Z | R1 — user comments |
| D0 | `investorgain-ipo-gmp-live-331-chunk-0.md` | https://www.investorgain.com/report/ipo-gmp-live/331/ | 0 of 4 | 12:34:37.198Z – 12:34:38.218Z | none |
| D2 | `investorgain-ipo-gmp-live-331-chunk-2-redacted.md` | same | 2 of 4 | 12:35:02.011Z – 12:35:02.654Z | R2 — user comments |
| DS | `investorgain-disclaimer-4-chunk-0-redacted.md` | https://www.investorgain.com/article/disclaimer/4/ | 0 of 2 | 12:35:22.034Z – 12:35:23.021Z | R3 — broker/individual contact blocks |
| R | `investorgain-robots.txt` | https://www.investorgain.com/robots.txt | 0 of 1 | 12:34:24.387Z – 12:34:25.443Z | none |

[`capture-manifest.json`](capture-manifest.json) records byte counts, SHA-256 digests, tool metadata, redaction details, the sandbox clock check, and items retrieved but not retained (dashboard chunk 3: user comments only) or not retrieved.

## What these files are — and are not

- **They are** the rendered Markdown `content` strings returned by Arena's `functions.fetch_page` tool, transcribed by the agent in JSON-escaped form, JSON-decoded, and written as UTF-8 without a BOM or an added trailing newline.
- **They are not** provider response bytes. Response headers, exact receipt time, and the tool's cache status were unavailable. The sandbox could not connect to `www.investorgain.com` directly (`curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL`; egress allowlist).
- **Retrieval windows** bracket each tool call. They do not establish when the publisher generated the content. The sandbox clock matched the `api.github.com` `Date` header to its one-second resolution.
- **Transcription fidelity** cannot be machine-verified against the tool output; invisible code points (for example emoji variation selectors) are the most likely to differ. GMP figures, timestamps, row counts, and chunk boundaries were spot-checked.
- **Redactions R1–R3** removed only third-party user comments (names, an email address, comment text) and broker authorised-person contact blocks, because this repository is public. No GMP figure, GMP timestamp, or publisher GMP/accuracy statement was removed. Each redaction is marked in its file.

## Hash subject and verification

**Hash subject:** the exact bytes of each retained file in `source-captures/`. Digests are uppercase SHA-256, following the repository's evidence convention. They establish the integrity of these local files only — not provider-byte identity, source authenticity, or the truth of any GMP value. The A9 decision defines no required GMP hash subject; these digests are not one.

Verify from this directory and compare case-insensitively with `capture-manifest.json`:

```sh
sha256sum source-captures/*
cat source-captures/investorgain-gmp-tonbo-2369-chunk-0.md \
    source-captures/investorgain-gmp-tonbo-2369-chunk-1-redacted.md | sha256sum
```

## Limits on reuse

The publisher pages are mutable, so re-fetching them will not reproduce these files. `robots.txt` allows `/` for generic agents; only public pages were requested and no API path was queried. No provider was contacted.
