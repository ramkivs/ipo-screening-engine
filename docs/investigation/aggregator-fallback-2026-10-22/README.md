# Aggregator fallback implementation and acceptance

Authority: [PA decision](../../../handoff/decisions/2026-10-22-pa-aggregator-issue-terms.md).

Implementation separates publisher parsing/policy from the existing official resolver and from the presentation orchestrator. Official discovery remains first. The additional API read-model warning is additive; canonical schema, scoring and historical files are unchanged.

## Operation

Set `IPO_ALLOW_AGGREGATOR_ISSUE_TERMS=1` before starting the existing API launcher. In PowerShell:

```powershell
$env:IPO_ALLOW_AGGREGATOR_ISSUE_TERMS = '1'
# Run the normal application launcher in this environment.
```

No manual issue values or Jio-specific resolver configuration are required. Default `0` deliberately retains official-only behavior. Third-party terms always remain visibly non-official. A publisher/layout/access failure may legitimately leave an IPO blocked.

## Source research

`source-research.json` retains the actual hosted source-research response, including compressed original HTML. Research run **39661966205**, commit **ed75bc846f4cf2db110bd39a9eb4abab4dc7be6b**.

Actual issuer page: https://www.chittorgarh.com/ipo/jio-platforms-ipo/3152/

- SHA-256 `a91ca2307b0c7c85a1ac41217df1e8d717398739a337e0e3489056b18fe75eb6`.
- Separate **Fresh Issue** row: `27,00,00,000 shares (agg. up to ₹30,213 Cr)`.
- IPO date 21–23 October 2026, band ₹1065–₹1119, lot 12.
- No explicit OFS row was used; the filing's valid OFS 0 must survive.
- ₹30,213 crore normalizes to **302130 INR_MILLIONS**. This is a publisher-stated amount, not engine-derived cash. The separate Total Issue Size row is not consumed.

## Checks before native acceptance

- Focused backend: **193 passed, 6 deselected**, three dependency deprecation warnings; `focused-tests.log`.
- Focused frontend: **10 passed**; `frontend-tests.log`. Warning escaping included; no unrelated frontend build.
- Controlled fixtures/API tests cover opt-in/default, source identity/period, currency/scale/ambiguity, total/share rejection, explicit NIL, placeholders, official and publisher conflicts, A–F execution, immutable hashes, restart GET, summary/evidence warnings and duplicate upload. Fixtures are explicitly not live acceptance.
- An offline diagnostic used the actual repository Jio PDF and captured original aggregator response, with official transport intentionally disabled: all six modules executed and seven stored artifacts/hash verified. This diagnostic is **not native/live acceptance**.

## Real native acceptance

The existing Windows native API workflow is explicitly enabled for aggregator mode and still performs real filing extraction, official HTTP/native/OCR discovery, actual aggregator HTTP retrieval, polling/GET, store hash verification, process restart and repeated upload. It retains compressed actual aggregator response bytes for independent provenance checking. Native outcome is pending at implementation publication; no restoration claim is made from the controlled tests or the offline diagnostic.


### First actual run: success path proven, duplicate defect found

Run **39664569074**, runtime **d89deadd89b504f4555cebd8b4e2c7e0e27c090b**, retained in `native-first-duplicate-failure.json`, is **NOT acceptance success**. Both real ingestions evaluated and persisted; the first's independent hashes/restart/evidence warnings passed. The duplicate assertion correctly failed: first ID `JIO-PLATFORMS-LIMITED-20261021-195701Z-final-9bcfc796`, second `JIO-PLATFORMS-LIMITED-20261021-200531Z-final-71aac3cc`. No assertion was weakened and neither record was rewritten.

Captured actual CG response hashes were `1ef79980c4d6bd224e343a64ef15e005f1cb78ad7c61f46a3aca92144d1cc8cd` and `4db7c19476441ec10de1c2aecefc654e98aa9f96e689bc977c019aca18ba5c21`. Diffing original bytes showed changing non-term React payload while qualified IPO table assertions were identical. Whole-HTML-derived source identity incorrectly forced a new evaluation.

Correction: deterministic source identity now fingerprints publisher URL, normalized issuer, issue window and all qualified field values, units, exact quotes and row labels. Unconsumed HTML does not change assertion identity. Raw full-response SHA-256 and retrieval time remain independently recorded. A changed value, unit, quote, row label, publisher or window changes identity. Repeated uploads still fetch live sources, still finish official discovery first, and return the **original immutable evaluation and its original manifest** when qualified assertions are unchanged. The new attempt's raw response hash remains in its activity diagnostics; no cached data, TTL or invented freshness policy is used. Controlled API checks explicitly vary HTML between uploads and verify original artifacts remain byte-for-byte represented by the same stored record. Both actual captured responses now produce the same assertion identity.

Additional focused read-model checks: **4 passed, 17 deselected**, including the exact preexisting golden scorecard/result hash; `read-model-tests.log`. The additive warning field is documented in the presentation OpenAPI only; canonical input schema is unchanged.
