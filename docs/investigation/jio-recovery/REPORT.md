# Jio ingestion recovery — final focused investigation, 21 October 2026

## Disposition: B — restoration INCOMPLETE

Implementation corrections are published and exercised by the real application on hosted native Windows. The remaining required field is **`issue.fresh_issue` (fresh-issue monetary amount)**. It is not established by the examined qualifying evidence. This is **not** a successful automatic evaluation, a claim that no other notice exists, or permission to enter invented/manual values.

The independent investigation went beyond the application's currently eligible RHP/price-band documents: it examined the actual issuer page's pre/post-anchor parameters, all sample forms/abridged prospectus, and the image-only anchor report. Those ancillary archives were **read-only research**, not silently relabelled as RHPs/price-band notices or automatically promoted into verified term candidates. They do not supply a qualifying fresh cash total. BSE's actual current public JSON endpoint remains HTTP 403 even with corrected production transport. That is an external access boundary, not a searched listing or proof of non-publication.

## Exact native result and authority boundary

- Runtime: **`62bad2c33464f7e8c7cc3c35368d97cff1295486`**; required baseline `0d1d48ba2c04f9a7b306e53c330dd3701559820e` retained as ancestor.
- [Windows run 39636184160](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39636184160), actual API job `119347179710`: SUCCESS means the diagnostic/checks ran, **not** that restoration succeeded.
- Actual upload **`ing-75d3241aa25f40c0`**, `mode=final`, began `2026-10-21T16:36:46.989109Z`, finished `2026-10-21T16:41:43.652466Z`.
- **BLOCKED / AWAITING_ISSUE_TERMS**, missing exactly `issue.fresh_issue`; `evaluation_id=null`, `evaluation_run=false`, `persisted=false`, result null; diagnostic `accepted=false`.
- Real HTTP multipart upload and independent terminal GET were followed by terminating/restarting the server against the same isolated durable stores. GET returned an identical terminal record. GET evaluations before/after restart returned `items=[]`, `total=0`.
- Consequently there is **no evaluation/result hash to verify and no persisted Jio evaluation**. Success-path repeated-upload idempotency was not executed/proved. The harness labels that branch NOT_RUN; durable BLOCKED activity is not evaluation persistence.
- Repository PDF: 11,630,670 bytes; SHA-256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`. Native official NSE RHP member has identical bytes/hash. This does not establish identity with an unavailable original user upload.
- Original **`ing-0168a590a93c4448`** build, exact uploaded bytes and original OCR traceback remain unavailable after searching accessible records and requesting them once. The real runs here are identified reproductions, **not reconstruction of that exact incident**. No claim about PID 11272, its nine waiting threads, or the user's browser/G: drive is made.

Full live record: [`latest-api-result.json`](latest-api-result.json). Independently reread published Check [119350592318](https://github.com/ramkivs/ipo-screening-engine/runs/119350592318). Baseline actual API record is retained separately in [`baseline-api-result.json`](baseline-api-result.json): `ing-fc5be918070e4dcc`, same unresolved field. Intermediate runs remain preserved in the workspace/remote Checks; they are not substituted for the final runtime.

## Each issue term: actual evidence, not assumptions

| Field | Actual value / state | Exact applicable evidence |
|---|---|---|
| Price-band low/high | ₹1,065 / ₹1,119, VERIFIED, confidence .95 | Actual NSE `api/ipo-detail?symbol=JPL`, `issueInfo.dataList[7]`, “Rs. 1065 to Rs. 1119 per Equity Share”; EXCHANGE_DATA |
| Lot | 12, VERIFIED, confidence .95 | Same response `dataList[11]`, “12 Equity Shares and in multiples thereof”; independently corroborated by notice OCR |
| Open/close | 2026-10-21 / 2026-10-23, VERIFIED, confidence .95 | Same response `dataList[3]`, “21-Oct-2026 to 23-Oct-2026”; original RHP cover dates retained at confidence .98 |
| OFS | **0**, explicitly qualified, not missing→zero | Original RHP p1 “OFFER FOR SALE SIZE … Not applicable”; original filing evidence confidence 1, INR_MILLIONS; official identical RHP p1 VERIFIED confidence 1, INR_LAKHS. Both zero amounts agree after normalization. |
| Fresh shares | 270,000,000, extracted confidence .98 | RHP p1 “Fresh Issue Up to 270,000,000 Equity Shares”; quantity only, not cash |
| Fresh monetary amount | **UNKNOWN / unresolved** | RHP “aggregating up to ₹[●] million”; available supporting documents below do not replace the placeholder with an applicable fresh cash total |

NSE response SHA-256: **`6dd90082c35315150d89b956ae1119ccca2c93879663794a6981bbcafa17bdb4`**. Independent refetch in run 39636630422 retained original compressed bytes, recomputed their SHA-256, decoded the original JSON and matched the real API source hash. This is independent network/source readback, not two quotations copied from the same extraction result.

Original filing and discovered candidate events retain source ID, URI, document class, exact document hash, page/locator, quote, method, confidence and verification state. Long evidence strings are numbered, SHA-256-bound parts rather than silently truncated quotes. These diagnostics do not upgrade candidate authority or constitute evaluation artifacts. The alleged disappearance of valid OFS 0 was **not reproduced** in available baseline/final API records; no historical value was rewritten. Filing extraction's verification flag is not misreported as VERIFIED; explicit official corroboration supplies that flag separately.

## Examined authoritative sources and the precise cash gap

1. **NSE listing → exact issuer/symbol → detail.** Actual listing SHA `24fe1b1ec7e70f731cfd6bfdd46992283d86c1a7aa5a6f62e2994d19e0a1c804`. Detail `dataList[5]` specifies fresh **share quantity**, employee ₹5,000 million / shareholder ₹25,000 million reservations and anchor share quantity. These are not the fresh cash total. Raw source retained in [`independent-source-audit.json`](independent-source-audit.json).
2. **Official RHP archive**, `https://nsearchives.nseindia.com/content/ipo/RHP_JPL.zip`, member `RHP_JPL/Jio Platforms Limited_RHP.pdf`, SHA `72480c2e…1b6d`. All **591 native pages** independently inventoried with zero page-read errors; five fresh-cash contexts still contain placeholders (including cover and Issue Structure p529). See [`rhp-all-pages-inventory.json`](rhp-all-pages-inventory.json). Explicit OFS “Not applicable” is retained, not guessed. GID examples are not RHP terms.
3. **Three actual newspaper notices** in `RATIOS_JPL.zip`: ET `e4feb7a9…4229`, MT `37fdc730…3a3c`, TOI `4882a03a…0526`. All three five-page OCR invocations completed in the final native run. Original operative p1 clauses were visually reviewed: `₹[●] million`, not an established fresh cash total. OCR price fragments lacking a qualifying matching rupee token remain UNVERIFIED; no digit/decimal repair or preferred-value substitution occurred. Original PDFs remain in the native artifact; selected review images are in `review/`. Those crops are **not verified numerical term evidence** and do not prove universal absence elsewhere.
4. **Pre-anchor parameters** `PREANCHOR_PARAMETERS_JPL.zip`, member SHA **`2052bf5aaeeae79fc84b2ed2a42c324ba37f32be6779ca244a5447ee2e08f263`**, all 5 native PDF pages. P1 fresh shares plus reservation amounts; p3 Total Issue Size is explicitly **shares**, and Max Bid Value is category-specific. Neither is fresh cash.
5. **Post-anchor parameters** `POSTANCHOR_PARAMETERS_JPL.zip`, member SHA **`aecae1e3c007e6c3f8830c0eb0e54d20280ae88c02e42b40fb49b36278362d3f`**, all 5 native PDF pages. Same distinction; post-anchor total is a remaining share count, not full fresh cash.
6. **Sample forms and abridged prospectus** `FORMS_JPL.zip`: four forms ×16 pages plus standalone abridged prospectus ×17 pages = **81 native pages**, fully inventoried. Each form p3, abridged prospectus p1 explicitly retains fresh “aggregating up to ₹[●] million” / OFS “Not applicable”. All five exact member hashes, complete page text and source archive hashes are in [`additional-official-documents.json`](additional-official-documents.json), [run 39637496894](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39637496894). No formulas/macros executed; no bounded/unsupported member was counted as read.
7. **Anchor allocation report**, `ANCHOR_JPL.zip`, member `ANCHOR_JPL/JPL_Anchor_Allocation.pdf`, SHA **`f4122541c1898af248edb2eb50a8e3cd154a2749c551c130b58130ea30893ef4`**. Initial native extraction correctly marked image-only, **not absence**. Follow-up [Windows run 39638363459](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39638363459), research commit `f5e5e8074da8d586f3aff533f217924f84e2c05a`, performed full-original-page OCR on **all 18 pages** in **101.266 seconds**, keeping raw line confidence and no numeric repairs. Original p1 image independently reviewed: the operative statement allocates **7,24,74,066 shares to Anchor Investors at ₹1,119**, followed by anchor-investor allocation/cash tables. Remaining pages are allocation/subcategory tables and closing letter, not an explicit full fresh cash total. **Anchor cash/subtotals cannot be substituted for fresh cash**, and anchor price is not relabelled as both price-band bounds. Diagnostic OCR remains UNVERIFIED, not canonical evidence. See [`anchor-review.json`](anchor-review.json) and [original first-page rendering](review/anchor-page-01.png); original PDF/all page images retained in `jio-anchor-original-page-review` artifact. This follow-up closes the initial image-only inspection gap without pretending OCR proves publication absence.
8. **Current BSE public protocol**, not the legacy shell: published SPA `main-Q26VKYIX.js` SHA `48fff98949b07a2681863bb3e525e5e51e44af3fde2c63dad8311e4ce2300f63` contains `/GetPublicIssue_par_updated/w?flag=1` and real complete detail-query construction. Root env has no active API base; imported config has build placeholders, not usable configuration. Existing public API namespace is separately recorded. Actual **`https://api.bseindia.com/BseIndiaAPI/api/GetPublicIssue_par_updated/w?flag=1`** returned **HTTP 403** with production JSON Accept, public-site Origin/Referer and session warmup in both independent audit and final application. Full exception chains retained. Angular HTML 14,287-byte shells are not searched issue data. No BSE issuer rows were obtained. Earlier old-header failures are not used as proof of corrected transport failure. SEBI listing's actual 404 and earlier BSE newspaper timeout are limitations, not absence findings. No CAPTCHA, authentication, form submission or access-control bypass attempted.

**Reproducible boundary:** with these exact authoritative bytes, the missing monetary field remains unknown; BSE's corrected current endpoint denies access. A different accessible authoritative applicable document explicitly establishing fresh cash could change this outcome. This report does not prove such a document does not exist. Share count × cap, reservation/anchor subtotals, total bid capacity, rumours, hypothetical GID examples and low-confidence/currency-free OCR are not authorized substitutes. No new derived-money/domain rule was introduced merely to pass the gate.

## Corrected defects and files

- `official_issue_sources.py`, `issue_terms.py`: current published BSE structured feed, strict issuer/current IPO qualification, actual Price_Band/date provenance and complete detail query; proper API JSON headers, public session warmup/Origin/Referer; discovery-only API host, not a widened direct notice/Prospectus authority. Controlled protocol tests, **not live 200 JSON success**, validate parsing because the real endpoint denies access.
- `official_notice_ocr.py`: bounded adaptive **180–270 s** budget for larger multi-page notices; full original child failure stderr logged, partial timed-out output discarded. Existing bundled local models, four inference threads, original PDF hashing/page mapping, numeric safety and GID rejection preserved.
- `issue_term_fields.py`: retain original amount-field confidence when normalized amount serialization omits it; does not invent a confidence/value.
- `presentation/service.py`, `ingestion_activity.py`: original/discovered field evidence, dates and fresh-share context retained even if another field blocks. Correct terminal advice no longer assumes an unpublished notice or prescribes manual values as a discovery workaround. Existing store/worker locking fix not reopened.
- `frontend/app.js`: truthful BLOCKED terminal guidance; no endless polling/false success to mask backend failure.
- Focused tests: `tests/test_bse_current_listing.py`, `tests/test_ingestion_activity.py`, `frontend/test/ingestion-activity.test.js`. Existing fixtures/assertions/goldens/frozen parsers untouched.
- Focused Windows/API workflow and bounded read-only source inventories/observer added under `.github/workflows/` and this directory. Redundant older live workflow is manual-only to avoid duplicate expensive runs.

### Actual OCR invocation/exception evidence

Hosted Windows **Python 3.11.9**, RapidOCR **3.10.0**, ONNX Runtime **1.24.4**, pypdfium2 **5.14.0**, pypdf **6.20.1**. Real OCR delegate observation changes no return values:

| Original notice | Elapsed seconds | Actual read budget | Outcome |
|---|---:|---:|---|
| ET | 87.125 | 270 | succeeded, 5 pages / 60 independent segments |
| MT | 82.344 | 270 | succeeded, 5 pages / 60 independent segments |
| TOI | 83.235 | 270 | succeeded, 5 pages / 60 independent segments |

Native GID invocation explicitly raised the intended `ValueError: General Information Document examples are not issuer issue terms`; complete traceback retained. It is classification protection, not a required-document OCR failure. Final filing extraction 20,469 ms; official discovery 276,156 ms. Earlier 180-second timeout/near-budget runs motivated the margin correction; this faster runner's timings **do not establish that the budget change caused a speedup**, nor reconstruct the unavailable original exception. UTF-8 child protocol, dependency versions, real exception/elapsed/source/document metadata and stderr are retained; no thread-count symptom is called a root cause.

## Focused validation only

Linux: Python **3.11.2** virtualenv, Node **v22.22.3**. Exact last production-delta commands:

```sh
PYTHONPATH=engine .venv/bin/python -m pytest -q tests/test_official_discovery.py tests/test_bse_current_listing.py tests/test_ingestion_activity.py tests/test_issue_terms_multisource.py tests/test_ofs_nil_binding.py tests/test_automatic_official_issue_discovery.py tests/test_issue_terms_windows_retrieval.py -m 'not slow'
# 131 passed, 6 deselected, 3 warnings, 3.03s; exit 0
node --test frontend/test/ingestion-activity.test.js frontend/test/ingestion-activity-flow.test.js
# 8 passed, 0 failed, 122.11878ms; exit 0
python -m py_compile docs/investigation/jio-recovery/*.py
# syntax checks exit 0; .venv interpreter used where imports required
```

The same focused Python/Node commands also **succeeded on native Windows** in run 39636184160 (job step conclusions retained). Local counts/times above are not misrepresented as captured Windows console counts/times. New research helpers compiled; scoped `git diff --check` passed. The independent readback script executes after publication and its receipt records actual results.

Negative controls are controlled/mock tests, **not fabricated live market conflicts**: verified contradictory candidates remain BLOCKED and both candidates appear in API evidence (`test_conflicting_verified_terms_remain_blocked_with_both_candidates_in_api`); unresolved API readback retains original OFS zero and lossless quotes; current-feed foreign/non-IPO/closed/malformed/shell records cannot provide values; 403 cannot claim searched absence; missing lot/fresh/OFS cannot default or borrow total size; bounded OCR failure discards partial terms and logs full stderr. The final live unresolved upload independently demonstrates fail-closed/no evaluation.

**No broad backend regression, broad matrix, unrelated frontend suite or production build was run for this iteration.** Historical broad results in earlier tracker entries are historical, not current acceptance. Browser behavior was checked with focused Node tests, not claimed as a session inside the user's browser. Native hosted Windows is not the user's computer.

## Publication, preservation and remaining work

Runtime `62bad2c…` and read-only research commits `0f5e226…`, `3d53cb0…`, `f5e5e80…` are published only on the existing session branch. Documentation/evidence publication is followed by **independent remote commit/tree and individual changed-blob byte readback**, re-decoding the real native/source/anchor Checks and asserting exact local-artifact agreement, unchanged main/PR6 and protected paths. See [`verify_publication.py`](verify_publication.py) and the subsequently published [`publication-readback.json`](publication-readback.json). The completion response identifies the final receipt-publication SHA and its independent final readback; a receipt cannot include its own future commit hash.

No scoring formula, weight, threshold, knockout, taxonomy, config/schema, fixture/golden, frozen `price_band_notice.py`/`prospectus_terms.py`, settled D1–D5/A23–A26 policy, HD Fire evaluation/history, production evaluation store or unrelated logs were altered. All existing unrelated/untracked artifacts preserved; no reset/clean/amend/force-push/branch switch/merge/retarget. Main `01ba66c12ca1195fd7acbd287c3e39a019808094`; PR6 OPEN/unmerged with original head `e05c0efbca1ecb3024e52da73a22e180ea171118` and base `arena/573e69a4-ipo-screening-engine` are independently rechecked, not assumed.

**Remaining authority boundary:** establish `issue.fresh_issue` from applicable authoritative evidence (or separately authorized valid domain derivation), then rerun the real upload, independently GET/hash-verify the persisted evaluation/provenance and repeat the identical upload for success-path idempotency. Until then automatic Jio restoration remains **INCOMPLETE**; no evaluation is manufactured and manual entry is not offered as the workaround.
