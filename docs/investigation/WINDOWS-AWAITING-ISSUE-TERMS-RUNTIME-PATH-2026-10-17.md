# Recurring Windows `AWAITING_ISSUE_TERMS` — Runtime-Path Investigation

- **Date:** 2026-10-17 · **Baseline:** `40f0dd2064b46ed8cc4db95a1b63964d3ee1091d` · **Symptom (Windows, user-reported):** upload of `U01122MH1994PLC185445-vishal nirmiti.pdf` with `IPO_PROSPECTUS_URLS` configured returns the generic 422 for all four terms (`price_band_low`, `price_band_high`, `lot_size`, `ofs`). Arena cannot access the Windows runtime; this record states exactly what was established from code + controlled execution, and what remains Windows-side.

## End-to-end trace (executed in sandbox at `40f0dd2`)

| Step | Evidence | Result |
|---|---|---|
| Env parsing | `build_resolver_from_env()` with the documented `IPO_PROSPECTUS_URLS` JSON | provider `official-prospectus` registered with the configured mapping |
| Filing → runtime IPO ID | Real RHP PDF (repo reference copy, sha `644be76e…`) through unmocked `DocumentExtractor` | `company_name = "VISHAL NIRMITI LIMITED"`, `ipo_id = "VISHAL-NIRMITI-LIMITED"` — **matches the configured key**; all four terms correctly missing (`[●]`); OFS seller `shares_sold = 15,00,000` from the filing |
| Provider invocation | `resolver.resolve(...)` with env-built resolver | prospectus provider **is invoked** after the (unconfigured) notice path; retrieval attempted against the SEBI URL |
| Retrieval | sandbox HTTPS to `sebi.gov.in` | fails in the sandbox (`TLS/SSL connection has been closed (EOF)`) — sandbox egress is restricted to package/GitHub hosts; this is **environmental here and proves nothing about Windows** |
| Downstream | Full `PresentationService.ingest_document` with the real filing + controlled transport returning final-Prospectus text | **evaluates**: 208/220/68, OFS 3300.0 derived (15,00,000 × ₹220), `fresh_shares = 65,90,909` (not the OFS quantity), `RESOLVED`/`OFFICIAL_PROSPECTUS` |

**Conclusion:** config loading, IPO-ID matching, provider registration/invocation, parsing, assembly, OFS derivation and evaluation are all functional at `40f0dd2`. The Windows failure occurs at (or before) the retrieval step in the Windows process — e.g. the env var not being present in the server process environment, TLS/proxy interference, an SEBI error response, or a read timeout — **or** the genuine document being rejected in that environment. At `40f0dd2` these were indistinguishable to the operator, for the defects below.

## Why the failure was undiagnosable (confirmed code defects)

1. **Frontend dropped the diagnostics (primary upload path).** `ApiClient.ingestDocument` (`frontend/api.js`) extracted error details as `errPayload.details || errPayload.detail.details`, but FastAPI nests the payload under `detail` with sibling keys `missing_fields`/`resolution` — so `err.details` was always `null`, the "Official-source resolution diagnostics" panel never rendered, and the operator saw only the generic message quoted in the report. (The manual-terms path extracted them correctly.)
2. **Malformed env JSON was silently swallowed.** `build_resolver_from_env` wrapped `json.loads` in `except Exception: pass`: a malformed `IPO_PROSPECTUS_URLS` meant the provider was never registered and the resolution carried **zero** provider reports — identical in appearance to a network failure.
3. **Exact-string key matching.** Configured-URL lookup used `urls_by_ipo.get(ipo_id) or .get(company_name)` verbatim; keying by a differently-cased/separated issuer name silently missed.
4. **Failure classes collapsed.** Retrieved-but-rejected documents (classification/issuer/value `REJECTED`) surfaced with the reason *"could not be retrieved or verified"*; enrichment-assembly failures were swallowed by bare `except: pass`, discarding verified terms with no diagnostic (assembly is intentionally all-or-nothing in final mode — e.g. unverified `lot_size` — but it must say so).

Why prior tests missed this: pathway tests mocked `DocumentExtractor` (never exercising filing→runtime-ID→config matching), the env-wiring test asserted only that a provider registers, and frontend tests never fed a FastAPI-shaped 422 through `ingestDocument`.

## Rectification (generic; allowlist, fail-closed and provenance semantics unchanged)

- `frontend/api.js`: `ingestDocument` now preserves `detail.missing_fields` / `detail.resolution` / `detail.conflicts`, so the diagnostics panel renders provider outcomes for the primary upload path.
- `issue_terms.py`: env URL mappings parse via `_url_map_from_env`; malformed/non-object/unusable mappings register a `ConfigurationDiagnosticProvider` reporting `UNAVAILABLE` with the variable name and parse problem (the configured value is never echoed). URL lookup (`_lookup_configured_url`) accepts exact IPO-ID, exact company name, or slug-normalised key variants — same issuer only, never another issuer's URL. Default retrieval timeout raised 20s → 60s (official PDFs are large; still bounded).
- `service.py`: retrieved-but-`REJECTED` outcomes get a distinct operator reason; assembly failures are recorded as `resolution.assembly_error` (still fail-closed — nothing is evaluated or persisted).

## Regression coverage

- `tests/test_issue_terms_runtime_path.py` (12): malformed/non-object env reporting (value never echoed); valid env wiring; key-variant matching ×4 + other-issuer never borrowed; API-level retrieval-failure diagnostics; rejected-vs-retrieval distinction in the operator message; partial prospectus fails closed with `assembly_error` naming the missing term; **real-filing end-to-end** (unmocked extraction, controlled transport) asserting 208/220/68, OFS 3300, fresh/OFS separation.
- `frontend/test/ingest.test.js`: FastAPI-shaped 422 through `ingestDocument` keeps `missing_fields` + provider diagnostics.
- Results: focused 38 passed; **full Python 985 passed; frontend 65 passed**; `compileall`/`node --check` clean. No type-checker or production build is configured in this repository (static frontend served directly). All transport in tests is controlled/mocked — **no live SEBI retrieval was exercised from Arena, and none is claimed.**

## Remaining Windows acceptance (minimum action)

Update, restart the server (env is read at startup), re-upload, and **read the now-rendered "Official-source resolution diagnostics"** in the manual-terms panel / 422 body. It will state the exact failing step, e.g.: `official-prospectus — UNAVAILABLE: IPO_PROSPECTUS_URLS is not valid JSON …` (fix the env value in the *same* shell that starts uvicorn), `… official source retrieval failed: <TLS/HTTP detail>` (Windows network/TLS/proxy to `sebi.gov.in`; verify the URL opens in a browser on that machine), `… REJECTED: …` (document classification/identity), or success (`RESOLVED`, evaluation produced). That single diagnostic line distinguishes every remaining cause; no further code change can be specified truthfully until it is observed.
