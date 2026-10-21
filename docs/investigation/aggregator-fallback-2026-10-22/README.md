# Aggregator fallback implementation and acceptance

**Final status: native acceptance PASSED in explicitly enabled aggregator mode.** Runtime `ba7a0694db4714d0f6a53ef1aad48a28330675ca`; Windows run [39667791831](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39667791831). Official-only mode is unchanged and is not claimed to have acquired official fresh cash.

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

The existing Windows native API workflow is explicitly enabled for aggregator mode and still performs real filing extraction, official HTTP/native/OCR discovery, actual aggregator HTTP retrieval, polling/GET, store hash verification, process restart and repeated upload. It retains compressed actual aggregator response bytes for independent provenance checking. The first actual run found an idempotency defect; the corrected real run below is accepted. Controlled tests and the offline diagnostic were not treated as native acceptance.


### First actual run: success path proven, duplicate defect found

Run **39664569074**, runtime **d89deadd89b504f4555cebd8b4e2c7e0e27c090b**, retained in `native-first-duplicate-failure.json`, is **NOT acceptance success**. Both real ingestions evaluated and persisted; the first's independent hashes/restart/evidence warnings passed. The duplicate assertion correctly failed: first ID `JIO-PLATFORMS-LIMITED-20261021-195701Z-final-9bcfc796`, second `JIO-PLATFORMS-LIMITED-20261021-200531Z-final-71aac3cc`. No assertion was weakened and neither record was rewritten.

Captured actual CG response hashes were `1ef79980c4d6bd224e343a64ef15e005f1cb78ad7c61f46a3aca92144d1cc8cd` and `4db7c19476441ec10de1c2aecefc654e98aa9f96e689bc977c019aca18ba5c21`. Diffing original bytes showed changing non-term React payload while qualified IPO table assertions were identical. Whole-HTML-derived source identity incorrectly forced a new evaluation.

Correction: deterministic source identity now fingerprints publisher URL, normalized issuer, issue window and all qualified field values, units, exact quotes and row labels. Unconsumed HTML does not change assertion identity. Raw full-response SHA-256 and retrieval time remain independently recorded. A changed value, unit, quote, row label, publisher or window changes identity. Repeated uploads still fetch live sources, still finish official discovery first, and return the **original immutable evaluation and its original manifest** when qualified assertions are unchanged. The new attempt's raw response hash remains in its activity diagnostics; no cached data, TTL or invented freshness policy is used. Controlled API checks explicitly vary HTML between uploads and verify original artifacts remain byte-for-byte represented by the same stored record. Both actual captured responses now produce the same assertion identity.

Additional focused read-model checks: **4 passed, 17 deselected**, including the exact preexisting golden scorecard/result hash; `read-model-tests.log`. The additive warning field is documented in the presentation OpenAPI only; canonical input schema is unchanged.


## Corrected actual native acceptance — PASSED

Full decoded evidence: `native-accepted.json`; independent readback/qualification checks and GitHub Check IDs: `native-verification.json`. Published implementation tree/all changed blobs independently downloaded and matched: `implementation-remote-readback.json` (**567 paths, 16 changed blobs** at tested runtime).

- Runtime **ba7a0694db4714d0f6a53ef1aad48a28330675ca**, run **39667791831**, job **119457317604**: completed SUCCESS, decoded `accepted=true`. Checks' head SHAs match the tested runtime; this conclusion was not inferred merely from a green workflow.
- Actual first ingestion **ing-85264e8a401045de**, evaluation **JIO-PLATFORMS-LIMITED-20261021-201943Z-final-840c0a14**: SUCCEEDED, evaluation run, persisted, no pending issue fields.
- Actual native official discovery and all three newspaper OCR reads completed before fallback, on **both** uploads. None of those placeholder cash fields was fabricated into a value. NSE pricing/lot terms remain; original filing explicit OFS Not applicable remains **0**.
- Actual CG Fresh Issue **₹30,213 Cr** normalized to **302130 INR_MILLIONS**. Canonical provenance is **MARKET_DATA / TABLE_EXTRACTION**, source **SRC-AGG-AB6F20DC33FD66BE**, note **THIRD_PARTY_AGGREGATOR_OVERRIDE / UNVERIFIED / NOT official**. Summary/detail warnings and evidence classification survived restart.
- Actual first raw response SHA **47293a7fa3a645e55f474c6d0b243912126ec6e7f1ba5bd9affa4d44d73f25fe**; repeat response **0ab4ba192e3d97d69e49384fc2b724f3b49a030d42fdf3d840afa0dedab1eff3**. Independent decompression/rehashing and issuer/window parsing confirmed both have identical qualified assertions. Full original bytes are retained, not substituted fixtures.
- Independent store hash verification: **7 artifacts**, no mismatches. Stored/recomputed/GET result hash **840c0a149d7483fd0ffaed4e5fe107a74afd05617c316c026d35d1fe502df339**. Terminal activity was identical after process restart; evaluation/evidence GETs returned 200.
- Real repeat ingestion **ing-5b3000f86e2d42aa**: SUCCEEDED, **is_duplicate=true**, same evaluation ID, **persisted=false**. Existing orchestration still computes before detecting the persistence duplicate (`evaluation_run=true`); this is not claimed as a computation cache. Original immutable manifest/record is returned; no second evaluation is written.
- Modules **A=17, B=1, C=11, D=4, E=0, F=0**, final **33**, verdict **INSUFFICIENT_DATA**. All six executed. Missing other evidence was not made clean/zero to obtain a favourable verdict.
- The historical harness's extra `/evaluations/{id}/trace` probe returns **404**: the actual API has no such route. It is retained and explicitly NOT claimed as a successful trace GET. Required evaluation/evidence GETs, module details, persisted hashes and restart proof passed; no new endpoint was invented to satisfy this unrelated probe.
- Negative source/policy/conflict/placeholder cases are focused controlled parser/API checks, **not** an induced live-publisher failure. The success/duplicate acceptance above is real hosted Windows HTTP ingestion, not a mocked transport. Scope is the repository Jio PDF (hash `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`); this does not establish the old user's upload identity, PID or G: drive state.

No scoring formulas, ratified config, canonical schema, goldens or existing historical evaluations were changed. `main` and PR6 remain protected; this work is published only on the existing session branch. Opt-in API processes must be launched with the environment setting above; no manual issue-term entry is needed for this validated path.
