# Platform-wide IPO issue-term resolution

Date: 2026-10-21. Working branch: `arena/95234306-ipo-screening-engine`.
Baseline: `4e7cb27aefd5aa7bacc99172f56af103b914d2d6`.

## Architecture and scope

Upload → existing canonical extraction and issuer identity → missing required issue terms → all configured providers → issuer-matched detail/documents → field candidates → normalization and existing authority gate → independent per-field selection/conflict → one multi-source enrichment payload → canonical assembly → recomputed required-term gate → existing normal evaluation only if ready.

This is shared production logic, not a Jio exception. No issuer-specific runtime condition, term value, URL mapping or scoring change is introduced. Live research URLs are documentation/probe inputs only. No real IPO evaluation, filing ingestion or historical record mutation was performed as part of this investigation; integration tests use isolated temporary stores.

### Changes

- `issue_terms.py`: traverse every provider even after cache success, isolate exceptions, traverse every configured official listing, retain independent component documents. Existing provider/caching interfaces remain available.
- `issue_term_fields.py`: independently resolve low/high, lot, OFS, fresh amount, opening and closing dates. Reject malformed values without discarding other valid fields; compare monetary amounts in INR using existing unit multipliers; retain equivalent and conflicting candidates. Official conflicts affect only the conflicting fields. Explicit mismatched issue windows reject stale/different issues rather than mixing offerings.
- Rejected NaN/Infinity values are reported as diagnostic strings so the strict JSON API stays usable; they remain rejected, never zero or canonical values.
- Field diagnostics expose original raw/normalized values, units, source ID/URL/provider, issuer, retrieval/source time when available, quote/locator/page/method, validity, verification, qualifications and unresolved state. Missing publication dates remain unknown. The frozen standalone notice parser still contains its pre-existing legacy `as_of` fallback; the shared resolver's merged payload does not carry or interpret that fallback as publication evidence. No global cleanup of that frozen interface is claimed. An unverified disagreement does not override an eligible official value.
- Multi-source assembly registers every selected source and carries each field's original source ID. Explicit stated fresh/OFS amounts convert to the canonical reporting unit; absence is never zero. A conflicting existing amount raises rather than silently overwriting.
- Service discovery includes the actual existing schema requirements for fresh amount and issue dates, not just pricing/lot/OFS. Partial canonical assembly is retained but does not authorize evaluation: the service recomputes required fields before proceeding. `partial_issue_terms` only relaxes the assembly-stage pricing completeness check, not scoring or service readiness; the result mode remains the requested mode.
- `issue_platforms.py`: opt-in public listing → bounded same-host detail-link traversal → exact issuer heading → candidate extraction. All platform candidates are unverified; none can satisfy the authority gate. No private APIs or guessed issuer detail paths are used.
- Exchange parsing adds explicit unit-bearing fresh/OFS amounts and observed NSE currency/lot/date aliases. Shares, minimum investment, reservation amounts and total issue size are not converted into monetary issue components.

### Configuration and authority boundary

Existing official discovery, configured official notice/prospectus URLs, retained sources and cache remain supported. Enable optional platform evidence with:

```sh
export IPO_TERM_PLATFORM_PROVIDERS=dhan,groww,angelone,indmoney
```

Unknown provider names produce a configuration diagnostic. Third-party use is opt-in because neither availability nor parsing creates verification authority. No `OFFICIAL_HOSTS` expansion, third-party verification promotion, arbitrary newer-wins rule, numeric freshness policy, price-times-shares inference or no-OFS-by-silence rule is added.

`ResolutionOutcome.status` remains a backward-compatible pricing-stage summary: `RESOLVED` is NOT evaluation readiness, especially when OFS needs existing downstream derivation. Use `unresolved_fields`, field diagnostics and the service's `remaining_required_fields` / `ready` for readiness. The old aggregate `UNPUBLISHED` token remains for searched-listing/no-match compatibility; its new field diagnostic explicitly says only not disclosed in examined sources, not proof of global non-publication. HTTP failures never produce this token.

### Known limits / not claimed

This implementation is not a universal browser scraper. The adapters support public same-host exact-name anchors and exact-name H1 details; a JS-only unlinked row, editorial alias, changed HTML layout, or separately labelled platform dates may remain unusable. No aliases are invented. See `live-evidence.md` for current provider-specific limitations and actual date disagreements. Source detail failures remain visible and do not prevent the remaining configured providers from running. BSE's actual detail exposes advertisement/RHP ZIP archives; archive-member parsing is not implemented, and `listing.bseindia.com` is outside current authority. These concrete live coverage boundaries remain open; the work is not claimed as complete live-provider acceptance.

Arena research-tool page access is not the engine runtime transport. Read-only runtime transport failures are recorded separately from research-tool observations (`runtime-transport.json`). No successful Jio live engine extraction/readiness/evaluation is claimed. Examined official content establishes price/lot/dates and explicit no-OFS language, but does not establish a usable total monetary fresh-issue amount. Outstanding acceptance requires permitted-network retrieval and authoritative monetary evidence, not a policy bypass.

## Final test results

| Check | Actual result |
|---|---|
| Full backend, final frozen tree | **1,355 passed, 0 failed/skipped, 25 warnings, 1614.73 s, EXIT 0** |
| Focused resolver/discovery/Windows | **82 passed, 3 deselected, 31.89 s**; excluded integrations included in full run |
| All intermediate full-run failures rechecked | **15 passed, 3 warnings, 293.00 s** |
| Frontend | **90 passed, 0 failed** |
| Configuration | **valid True, 10 profiles, each 100 points** |
| Frozen-tree identity | **209/209 matching files**; manifest SHA-256 `26581f84734a80d49502193bb8d6f4eb9b84472e7f968cad131b0bb46e87b599` |

The 25 full-run warnings are Starlette/httpx and HTTP 422 deprecations, not test failures. The source/test bytes stayed unchanged throughout the final full run. No frozen parser pin, config/schema, golden or scoring/history file changed. Publication SHA and actual remote verification are supplied in the completion response; PR #6 is not the PR for this session branch and remains untouched.

## Verification artifacts

- `tested-tree.json`: SHA-256 identity of runtime/tests/config/schema/fixtures/frontend files for the full run; verification notes state any subsequent correction and rerun scope.
- `focused.log`: deterministic focused result including Windows real-socket retry/cookie coverage (localhost test infrastructure only, no live IPO dependency).
- `full-backend.log`: full backend regression progress, counts, failures/warnings and exit code.
- `frontend.log`: 90 frontend tests passed, zero failed.
- `config-check.log`: config validation; 10 profiles each total 100 points.
- `runtime-transport.json`, `.log`, `probe_runtime.py`: reproducible read-only actual transport failures.
- `live-evidence.md`: tool-observed official and platform citations, exact excerpts, field conflicts and outstanding live acceptance.

Two in-progress full runs were interrupted for demonstrated correctness gaps (observed live NSE formats, then strict-JSON/date-only diagnostics); their logs/identities are retained, never counted as passes. Intermediate failed runs remain distinguishable from final acceptance. No scoring/config/schema/golden/history edits are authorized or required by this work.
