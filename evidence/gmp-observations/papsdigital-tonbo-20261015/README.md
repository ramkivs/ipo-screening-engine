# PapsDigital — Tonbo Imaging India IPO GMP Capture (2026-10-15)

Status: NON-AUTHORITATIVE INVESTIGATION EVIDENCE. This package is not a source approval, an A9 qualification, a qualifying GMP snapshot, or an A9 required hash. The determination that uses it — **PapsDigital: NOT QUALIFIED** (a declared single-source relay of InvestorGain) — is recorded in [`A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md`](../../../docs/investigation/A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md).

## Contents

All retrieval windows are on 2026-10-15. Each was read from the sandbox UTC clock before and after the tool call; one clock read may close one window and open the next.

| Key | File (`source-captures/`) | Source URL | Chunk | Retrieval window (UTC) |
|---|---|---|---|---|
| PD-L0 | `papsdigital-ipo-gmp-chunk-0.md` | https://www.papsdigital.com/ipo-gmp | 0 of 3 | 13:11:32.551Z – 13:12:01.221Z |
| PD-L1 | `papsdigital-ipo-gmp-chunk-1.md` | same | 1 of 3 | 13:12:01.221Z – 13:12:33.851Z |
| PD-L2 | `papsdigital-ipo-gmp-chunk-2.md` | same | 2 of 3 | 13:12:33.851Z – 13:12:37.335Z |
| PD-T0 | `papsdigital-ipo-gmp-tonbo-imaging-india-chunk-0.md` | https://www.papsdigital.com/ipo-gmp/tonbo-imaging-india | 0 of 2 | 13:12:37.335Z – 13:12:53.473Z |
| PD-T1 | `papsdigital-ipo-gmp-tonbo-imaging-india-chunk-1.md` | same | 1 of 2 | 13:12:53.473Z – 13:14:14.112Z |
| PD-R | `papsdigital-robots.txt` | https://www.papsdigital.com/robots.txt | 0 of 1 | 13:11:09.958Z – 13:11:32.551Z |

No file is redacted or excerpted. [`capture-manifest.json`](capture-manifest.json) records byte counts, SHA-256 digests, page titles, IST conversions of each window, the sandbox clock check, the chunk-join checks, and the items deliberately not retrieved.

## What these files are — and are not

- **They are** the rendered Markdown `content` strings returned by Arena's `functions.fetch_page` tool, transcribed by the agent in JSON-escaped form, JSON-decoded, and written as UTF-8 without a BOM or an added trailing newline.
- **They are not** provider response bytes. Response headers, exact receipt time, and the tool's cache status were unavailable. The sandbox could not connect to `www.papsdigital.com` directly (`curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL`; egress allowlist).
- **Clock labels in these files depend on the capture.** In PD-L0, "Last updated: 15 Oct 2026, 09:11:14 am IST" is 9 h 30 min earlier than the retrieval window (18:41–18:42 IST), while the same rendering says "Updated 22s ago". Rendered-text captures of this page are therefore not expected to reproduce byte-for-byte in another capture environment.
- **Retrieval windows** bracket each tool call. They do not establish when the publisher generated the content. The sandbox clock matched the `api.github.com` `Date` header to its one-second resolution.
- **Transcription fidelity** cannot be machine-verified against the tool output. GMP figures, clock labels, provenance statements, and chunk boundaries were spot-checked.

## Hash subject and verification

**Hash subject:** the exact bytes of each retained file in `source-captures/`. Digests are uppercase SHA-256, following the repository's evidence convention. They establish the integrity of these local files only — not provider-byte identity, source authenticity, or the truth of any GMP value. The A9 decision defines no required GMP hash subject; these digests are not one.

Verify from this directory and compare case-insensitively with `capture-manifest.json`:

```sh
sha256sum source-captures/*
```

## Limits on reuse

The publisher pages are mutable, so re-fetching them will not reproduce these files. `robots.txt` allows `/` and disallows `/api/` for generic agents; only public HTML pages were requested and no `/api/` path was queried. No provider was contacted.
