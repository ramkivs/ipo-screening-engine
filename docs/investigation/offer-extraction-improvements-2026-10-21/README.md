# Authorized offer-term extraction improvements — 21 October 2026

## Scope and implementation

Runtime **e416b1f808d09bf96b8446430ea86c93d3071557**, following existing published baseline **4ce17356e3a68d45f80b71f73f8bbc53beb62155**. No aggregator/LLM authority, new cash derivation, canonical/schema/policy state or scoring change.

- `official_offer_amounts.py`: qualified RHP native text reads extend from 5 to **30 pages**. Record total/attempted pages, limit, whole-document completeness and actual page errors. Beyond the original five-page window, only explicit offer-summary section headings or established component tables can supply amounts; unrelated/example mentions are not silently eligible. Cover qualification still uses actual original pages 1–2. A 30-page read is **not** a claim to read a 591-page document or find every possible offer section.
- `SOURCE_PLACEHOLDER` diagnostics retain component, original page/quote and extraction method, with coordinates for supported cells. `[●]`, blank brackets and `TBD` remain null, not zero. Diagnostic assertion windows stop at another component/reservation heading; OFS is not tagged merely because an adjacent fresh cell has a placeholder. These are **parser metadata diagnostics**, not new canonical verification states or a new UI workflow.
- Existing qualified NIL/“Not applicable” binding still establishes **OFS zero**. Placeholder history does not veto a later explicit applicable amount. Distinct explicit amounts still create the existing conflict diagnostic. Anchor/reservation/total component transitions cannot supply another component's cash.
- `offer_table.py`: deliberately conservative native table AST using existing **pypdf**, with original header/cell text and transformed x/y coordinates plus body rectangles. Requires three unique, aligned Fresh Issue/OFS/Total headers, explicit adjoining header/body rectangles and aligned body cells. Amount parsing stays within the component cell and requires explicit currency, aggregate wording and monetary scale. Original quote/locator/hash/page remain traceable; synthetic internal labels are **not** emitted as source quotations. Shared geometry alone does not grant source authority; existing RHP/issuer qualification remains mandatory upstream.
- No fixed-distance table lookahead, digit repair, column/cell stitching, borrowed currency units, shares×cap, reservation/anchor/total substitution or new source authority. Multiline pypdf callback chunks are retained as **ambiguous**, never split into invented cell coordinates. Recognized table pages are excluded from flattened prose amount extraction; this is conservative and can leave otherwise readable amounts unresolved.

## Explicit limitations

This is **not a universal PDF table parser**. Line-only grids, merged/split headers, rotated/skewed layouts, multi-run amount sentences, unsupported component orientations and currency/units supplied only by another cell are not reconstructed as verified table values. Existing guarded prose extraction remains available where the strict table geometry is not established. Layout-read errors remain separately recorded; text-read errors do not become placeholder or absence findings. The new AST did **not** recognize the actual Jio cover table; no claim otherwise is made.

## Focused validation

Linux Python **3.11.2**, existing pinned runtime requirements installed in `.venv` without requirements changes. Final exact command:

```sh
PYTHONPATH=engine .venv/bin/python -m pytest -q tests/test_offer_table_boundaries.py tests/test_official_discovery.py tests/test_ofs_nil_binding.py tests/test_issue_terms_multisource.py tests/test_automatic_official_issue_discovery.py tests/test_ingestion_activity.py tests/test_bse_current_listing.py tests/test_issue_terms_windows_retrieval.py -m 'not slow'
```

**162 passed, 6 deselected, 3 deprecation warnings, 8.42s; exit 0**. See `focused.log`. Thirty-one new tests cover component/total/reservation separation, source placeholders versus NIL, later explicit resolution, genuine conflicts, native page-12 summary extraction/hash/page provenance, unrelated later-page exclusion, bounded completeness/read failures, cell coordinates, original NIL quotations, unsupported unbounded layouts and ambiguous grouped chunks. Existing assertions/fixtures/frozen parsers unchanged. Initial new-test run failed because its new dataclass fixture omitted required constructor arguments; the fixture was corrected, not existing assertions weakened. Subsequent focused runs culminated in the retained final result.

Syntax checks and scoped `git diff --check`: exit0. No broad backend/matrix, unrelated frontend suites, production build or HD Fire ingestion/history mutation. Existing related Node activity checks run as part of the native workflow; no frontend implementation changed.

## Actual Jio evidence and native API validation

Local native-text check: same repository Jio PDF SHA **72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d**, matching the prior independently fetched official RHP. **Fresh amount null, explicit OFS zero**. Read scope 30/591 pages, no text read failures, no recognized table columns, fresh-only SOURCE_PLACEHOLDER diagnostic. `jio-native-text.json` was captured on the final runtime e416b1f. This is an offline real-document check, **not live/API success**.

Final native run **39650886624** on **e416b1f808d09bf96b8446430ea86c93d3071557**. Actual evidence is in `native-api-result.json`, independently decoded from Check **119405084138**. Earlier runs 39648816070/d6612d0, 39648966250/dc2a281 and 39649331505/c8ebb6a are superseded, not final-runtime acceptance. GitHub's cancellation endpoint denied cancellation of the first run (403 integration permission); no access-control bypass attempted and logs were preserved.

### Final actual Windows result

[Run 39650886624](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39650886624), final runtime **e416b1f808d09bf96b8446430ea86c93d3071557**, job119398583597: **SUCCESS for the checks/diagnostic, not restoration**. Focused Python and related Node activity steps succeeded. Windows Python3.11.9; RapidOCR3.10.0, ONNXRuntime1.24.4, pypdfium2 5.14.0, pypdf6.20.1. Final real HTTP upload **ing-e5c0c436c8564ef5**, started2026-10-21T18:15:36.257734Z, finished2026-10-21T18:25:52.532424Z: **BLOCKED / AWAITING_ISSUE_TERMS, missing only issue.fresh_issue**. Price band1065–1119, lot12, dates2026-10-21/23 and explicitly qualified OFS0 remain evidenced; no fresh money inferred.

Actual independent HTTP GET after terminating/restarting the server against the same isolated store returned the **identical terminal activity**. Evaluation lists before/after restart both empty, total0. **evaluation_id=null, evaluation_run=false, persisted=false, result=null, accepted=false**. There is no evaluation/result hash to verify. Successful repeated-upload idempotency is explicitly NOT_RUN, not proven. No user's production store or historical evaluations touched.

All three actual five-page/60-segment newspaper OCR invocations completed: **ET151.859s, MT146.125s, TOI190.015s**, each270s bounded budget, no child failure. GID hypothetical examples were intentionally rejected with their original full traceback, not treated as issue terms. Actual source hashes and raw OCR fields/method/confidence/budget/exception metadata are retained in the native record. Corrected BSE current feed still returns403; no unavailable endpoint is called a searched listing or evidence of non-publication.

**Jio restoration remains INCOMPLETE.** This patch improves supported extraction and diagnostics; it does not establish a cash value absent from the examined authoritative assertions. Prior independently reviewed official RHP/forms/parameters/anchor evidence remains documented in `../jio-recovery/REPORT.md`. No manual workaround, aggregator authority, LLM value, shares×cap derivation or reserved/anchor subtotal was introduced.

## Publication and preservation

Only existing session branch; checkout reconstruction was safely reconciled by independently hashing **all 544 existing remote tracked files**, finding exact byte matches, staging only those exact matches and **fast-forwarding** to the already-published branch. No reset/clean/force/switch, unrelated file replacement or untracked cleanup. Subsequent changes are the scoped extraction/test/workflow changes and this evidence/documentation update.

After publication, `verify_publication.py` independently reads the remote commit/tree and changed blobs, decodes the actual final runtime Checks and checks terminal/evaluation-list equality across real server restart, explicit OFS evidence, protected paths and unchanged main/PR6. Receipt publication is a separate append-only commit; a final independent readback verifies that commit too. Prior recovery reports remain historical, unmodified; enhancements do not manufacture fresh cash or supersede settled decisions.
