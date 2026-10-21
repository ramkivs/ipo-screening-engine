# Automatic official issue discovery / Jio ingestion — 2026-10-21

## Controlling outcome

**Automatic discovery is implemented, but end-to-end Jio acceptance is not achieved.** Actual public exchange retrieval establishes the price band, lot size, dates and explicit NIL OFS. The required **fresh-issue monetary amount** remains unestablished. This is not evidence that the term is unpublished. No manual-entry workaround, inferred amount, exception to required terms, or successful-evaluation claim is substituted.

The settled Windows worker correction (`b6230bb`, evidence `6c871e5`) is preserved, not reopened. The user's separate PID 11272 was not inspected or diagnosed here.

## Starting point and root causes

Starting published tree: `6c871e5ff7253145ecc4a7cf67af62b70c844a85`, on the fixed session branch `arena/95234306-ipo-screening-engine`.

1. Listing discovery depended on issuer links in server-rendered HTML. An NSE listing shell is not its issuer feed; a BSE Angular shell is not a rendered issue table. Treating those bodies as the end of the search missed issuer-specific official evidence.
2. NSE's exact-name issue feed supplies a symbol and issuer-specific detail API. The detail response carries labelled price/lot/date facts and links to official offer archives. These representations and ZIP members were not followed through the existing resolver.
3. Exchange-page classification could reject an actual detail page because shared site chrome looked like a homepage. Full detail query strings, parent referrers, cookies, warm-up order and redirect eligibility need preservation. This correction does **not** prove BSE's current raw HTTP transport returns a usable table: actual tested BSE routes still returned the same Angular shell.
4. Attachment roles matter. A bundled General Information Document contains hypothetical ₹20/₹24 book-building examples, not Jio pricing. Actual live investigation exposed a false conflict with NSE's ₹1,065/₹1,119. The runtime adapter now rejects GIDs before the frozen parser runs; genuine conflicting evidence still fails closed.
5. The actual RHP's graphical dated title is not readable as text. Its issuer responsibility assertion, complete offer table, legal name and CIN establish the RHP role without inventing a date. Its table explicitly says OFS is not applicable; its fresh monetary amount is a placeholder. Shares, total issue size and reservation amounts are not substitutes.
6. ET/MT/TOI archive PDFs are image-only. Native-text extraction cannot establish their terms. Offline OCR is now attempted automatically, with explicit provenance, confidence/readability guards and a bounded read-only subprocess; failure is not publication absence.

## Retrieval and integration changes

- `engine/ipo_screening/official_issue_sources.py`: structured NSE listing/detail adapters; exact legal-name matching; symbol-derived detail URLs; dates and explicit labelled values; ordinary HTML links with full query strings; bounded ZIP decoding and original member URIs. No issuer-specific price or lot constants.
- `engine/ipo_screening/issue_terms.py`: automatic feed/detail/document traversal; page classification; parent referrers and cookie session reuse; eligible redirect validation; canonical integration and per-source diagnostics. Archive hosts are scoped to issuer-matched discovery, **not** a broadening of existing direct notice/final-Prospectus URL allowlists. Configured direct providers retain their old authority boundary.
- `engine/ipo_screening/extraction/exchange_issue_page.py` and `issue_term_fields.py`: explicit fresh monetary fields and canonical/provenance mapping, using the existing units and resolver/evaluation gates.
- `engine/ipo_screening/extraction/official_offer_amounts.py`: separate RHP role, issuer/CIN checks, explicit component amounts and the existing governed OFS-NIL binding. No total-to-fresh substitution, shares-times-price inference, reservation subtotal or absent-OFS-to-zero default.
- `engine/ipo_screening/extraction/official_notice_ocr.py`: bundled offline RapidOCR ONNX models, pypdfium rendering, at most six pages, 4,500-pixel longest side, overlapping 1,600-pixel crops and a bounded CPU inference cap (initially one thread; final cap is at most four available CPUs). A 180-second child read budget discards partial output on failure/deadline; that child performs no evaluation or persistence. Low-confidence lines remain unreadable markers. Only fixed structural heading whitespace is normalized; no issuer letters, digits, currency or numbers are repaired. Standalone primary issuer headings require an adjacent identity/registered-office block and still must pass the caller's exact issuer match. Original PDF hash/URI/page and OCR method/confidence remain explicit. Cache reparsing uses the same adapter.
- `requirements.txt`: pinned `pypdfium2==5.14.0`, `rapidocr==3.10.0`, `onnxruntime==1.24.4`; model paths are local and no runtime model download is attempted.
- Tests cover real loopback HTTP cookies/referrers/request order, genuine conflicts, partial evidence, issuer mismatch, GID examples, actual Jio RHP cover classification, source provenance, guarded evaluation/persistence and a real generated image-only PDF through offline OCR. Mocked transports are labelled unit evidence, not live acceptance.

The frozen `price_band_notice.py`, scoring/configuration/schema, taxonomy, thresholds, knockout semantics, goldens and historical evaluation records are unchanged. No HD Fire live ingestion, reevaluation or history mutation was performed. Application writes in the native Jio verification are isolated in temporary stores.

## Actual official evidence

First independently readable structured terminal check: [check 119279537609](https://github.com/ramkivs/ipo-screening-engine/runs/119279537609), head `0f2343cafda63e79008c8c7b79d47c40df37771c`, workflow run `39614788402`.

`ing-17da4a995e0a49e7`, completed `2026-10-21T14:25:31.095399Z`: **BLOCKED**, `AWAITING_ISSUE_TERMS`, missing only `fresh_issue`; resolver `PARTIAL`, ready false, no conflicts, no assembly error. **evaluation_run=false; evaluation_id=null; persisted=false.**

| Field | Actual supported value | Official evidence |
|---|---|---|
| Floor / cap | ₹1,065 / ₹1,119 | `https://www.nseindia.com/api/ipo-detail?symbol=JPL`, literal quote “Rs. 1065 to Rs. 1119 per Equity Share” |
| Lot | 12 shares | Same response, “12 Equity Shares and in multiples thereof” |
| Open / close | 2026-10-21 / 2026-10-23 | Same response, “21-Oct-2026 to 23-Oct-2026” |
| OFS | Explicit 0, not a default | Issuer RHP offer table: “OFFER FOR SALE SIZE … Not applicable” |
| Fresh monetary amount | **Unestablished** | RHP has `₹[●] million`; feed's ₹5,000 million employee and ₹25,000 million shareholder reservation figures are not the fresh amount. Newspaper and BSE attempts require the source-level diagnostics below. |

NSE response SHA-256: `6dd90082c35315150d89b956ae1119ccca2c93879663794a6981bbcafa17bdb4`.

Official RHP: `https://nsearchives.nseindia.com/content/ipo/RHP_JPL.zip#zip-member=RHP_JPL%2FJio%20Platforms%20Limited_RHP.pdf`, 11,630,670 bytes, SHA-256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`. This matches the repository PDF used in native verification. It does not prove identity with an unavailable user upload.

Earlier actual archive investigation retained these additional original hashes:

- GID: `05d3158b7b194c9d185ea4a73d0fa2f1818c9f97ec6358c775f48beaf377df36` — rejected as instructional examples.
- `RATIOS_JPL.zip` / ET.pdf: `e4feb7a9c4ce0b80087e9c4b38446c1cbd17d93c0b10b7e10d575488c0504229`.
- Same archive / MT.pdf: `37fdc73024395fded5f60393391b02cc036a7354bc62962e2055858cb0213a3c`.
- Same archive / TOI.pdf: `4882a03ab6264f7fedfa3ba9c438876185a3b41fe73c8aabcc2602e8f8970526`.

Actual BSE listing, publicissue and full-query issuer-specific `DisplayIPO?id=4894&type=IPO&idtype=1&status=L&IPONo=8047&startdt=21/10/2026` requests returned a 14,287-byte Angular shell, SHA-256 `7e4904994cfef3e8e2ec2b72ee3153b9f6a9c868b4eef44dd25febb266f0fb2a`. Lowercase variants did not correct this. The public BSE newspaper ZIP attempt timed out; the SEBI listing endpoint returned 404. Neither is absence evidence. Browser-rendered/search-readable BSE pricing was research context, not canonical live-HTTP evidence.

### Final source-level readback

The authority-preserving candidate `dab7b7604af5367ae1d1bb38a20546f1f61229fc` was independently read back through [check 119286817565](https://github.com/ramkivs/ipo-screening-engine/runs/119286817565), workflow `39617115902`. `ing-042e9c81cd0a4295` ended **BLOCKED / AWAITING_ISSUE_TERMS** at `2026-10-21T14:40:38.724701Z`, missing only fresh monetary amount, no conflicts, evaluation false and persistence false. Its source diagnostics expressly establish that **each of ET.pdf, MT.pdf and TOI.pdf exceeded the 180-second read-only OCR budget**. They were not established as final Prospectuses either. Generic NSE/BSE shells are recorded as not searched, while the exact issuer-matched NSE feed is recorded as searched. Discovery took 564,250 ms. The original RHP's OFS remains verified.

This is an **implementation/extraction performance limitation**, not proof that a fresh amount is unpublished, that the issuer differs, or that all official sources lack it. BSE transport is also not restored. Research-only attempts at the old official `GetPublicIssue/w` and `GetMkt_ISSUE_BBS_IPO/w?IPO_NO=8047` API URLs resolved in the page-fetch tool to a BSE Show Interest form; no registration/contact form was submitted and no access controls were bypassed. This research is not production/native transport verification or authority for any financial value; see `bse-api-research.json`.

The throughput correction (`1139e01523a1ae35b09c0da8227151ce0a96cb1c`) raises ONNX intra-operation CPU parallelism to `min(4, os.cpu_count() or 1)`. It does not increase the read budget, reduce confidence, change rendering limits, repair text or weaken any validation. Its actual native readback, [check 119293644140](https://github.com/ramkivs/ipo-screening-engine/runs/119293644140), run `39619242232`, remained BLOCKED: `ing-897c2daa17f74f56` ended `2026-10-21T14:53:50.971796Z`, fresh only unresolved, no evaluation or persistence. Discovery completed in 495,375 ms. All three scans now completed rather than timing out, exposing an identity-layout defect: the 1,600-pixel crops split the actual issuer heading into fragments such as `JIO PLATF` / `ATFORMS LIMITED`; another crop yielded the promoter name `RELIANCE INDUSTRIES LIMITED`. These are failed OCR identity interpretations, **not proof that the actual clippings belong to another issuer**.

The final layout correction (`9ba5e58`) reads the full-width first-page header separately, using it only for a standalone primary issuer heading followed by CIN/registered-office or “TO BE LISTED ON” context. It does not stitch or repair letters and the complete source-derived name must still pass exact matching. Financial text from this header read is never consumed; monetary/price fields continue to use the original independent crops and original guards. The actual layout-candidate result [check 119300131866](https://github.com/ramkivs/ipo-screening-engine/runs/119300131866), run `39621317022`, proved complete heading recovery and lot/date agreement across all three scans, but exposed **unqualified OCR price assertions**: currency-free `106.50` / `111.90` and `lower end 1,055: at upper end 1,119` entered the INR price fields. That run correctly failed closed on conflict, `ing-2a07410f2fea46ff` at `2026-10-21T15:06:37.982322Z`, with no evaluation or persistence. It is not acceptance success and not proof that the original publishers actually disagree.

Final correction `a327950` requires an OCR price assertion's captured quote to contain an **explicit INR/Rs/₹ token matching that value**. Otherwise the OCR hypothesis remains visible but **UNVERIFIED**, using the existing field-verification gate. This distinguishes currency-free/multiple/chart assertions from verified rupee prices; it never compares against a preferred provider, changes a digit, computes a face-value multiple, or suppresses disagreement between genuinely verified monetary values. New regression assertions expressly preserve a different, currency-qualified value as eligible for the existing conflict check. A separate final guard (`cd7b445`) prevents a dated Draft RHP from being promoted into current RHP authority.

### Final controlling native result

[Check **119308926882**](https://github.com/ramkivs/ipo-screening-engine/runs/119308926882), workflow [**39623461399**](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39623461399), exact runtime head **`a3279506b6cee66482135324528a56b6264826a9`**, is the controlling actual-source evidence (`final-native-result-check.json`).

- Ingestion **`ing-a166a462042145f0`** finished **`2026-10-21T15:24:10.302542Z`**.
- **BLOCKED / AWAITING_ISSUE_TERMS**, resolver **PARTIAL**, ready false, **missing only `fresh_issue`**, **no qualified conflicts** and no assembly error.
- **evaluation_run=false; evaluation_id=null; persisted=false.** End-to-end automatic Jio evaluation/persistence is **not restored**.
- NSE's actual ₹1,065/₹1,119, lot 12, issue dates, and the actual RHP's explicit OFS 0 remain verified. Currency-free OCR price hypotheses remain visible as **UNVERIFIED**, not silently repaired, preferred against, or converted into official rupee amounts. The raw OCR capture alone does not prove whether a particular unsupported number is a multiple, chart datum or recognition error.
- **ET and MT parsed with issuer identity recovered**, agreeing on lot 12 and the 21–23 October issue dates, but returning **no qualified fresh monetary amount**. **TOI exceeded the 180-second OCR budget in this final run**; earlier completion does not guarantee later completion. Discovery took **567,454 ms**.
- Generic NSE/BSE shells remain explicitly **not searched**; the exact-name NSE structured feed is searched and yields one issuer record. BSE raw transport remains un-restored; SEBI listing retrieval failed. These facts are not non-publication evidence.

The remaining acceptance blocker is **unestablished fresh monetary evidence / extraction coverage**, not an approved policy change or a request for manual values. Improve issuer-matched official document monetary extraction or retrieve an appropriate official disclosure when available; do not infer cash from shares × cap price, promote reservation subtotals, bypass BSE access controls, weaken conflict/verification gates, or label this task fully completed. A green diagnostic workflow alone is not ingestion success; the structured result uses neutral/BLOCKED rather than success when required terms remain unresolved.

## Validation and corrections during investigation

- A first broad run was interrupted after obsolete four-listing assumptions and live document-role gaps were identified. Three activity assertions now require **all configured listing sources**, rather than a hardcoded count of four; status, failure and persistence assertions remain intact.
- Reducing OCR render scale caused the Windows Arial-image regression to lose its monetary amount. Restoring reading resolution retained the guards and made the real offline OCR regression pass again; no test was weakened.
- The first OCR-enabled live diagnostic exceeded its 20-minute job budget. Duplicate OCR was removed from the separate native-text diagnostic; actual ingestion still executes real runtime OCR. Read-only OCR is isolated and deadline failures cannot consume partial output or persist anything.
- A completed broad run at the earlier candidate produced **1,393 passed / 1 failed / 25 warnings, 1,198.06 seconds**. Its unchanged direct Prospectus allowlist test exposed overly broad archive eligibility. This was corrected in `3f8bb49`; the test was preserved and passed, with an added direct-notice/direct-Prospectus versus discovery-scope regression. This earlier run is not represented as a full pass.
- Final post-correction focused suite: **124 passed, 6 deselected, 3 warnings, 4.29 seconds**. Includes the existing Prospectus authority-boundary tests and frozen-hash tests.
- Real Linux image-only PDF / offline OCR: supported amounts, band, lot, OCR method and original PDF SHA verified. Native Windows real-OCR step passed on corrected rendering.
- Frontend: **90 passed**; active v1.5 config valid, ten profiles; Python compile checks and code/documentation `git diff --check` passed. Raw pytest trace whitespace is retained verbatim in captured `.log` evidence; generated logs are excluded from formatting-only diff checks.
- Complete backend run: **1,395 passed, 25 warnings, 1,210.12 seconds**, no skips/failures. This run started against `dab7b7604af5367ae1d1bb38a20546f1f61229fc`; its exact 291-path snapshot is `tested-tree-backend.json`. The later runtime delta is confined to the OCR module (bounded CPU inference, full-width identity-only heading read and explicit price-currency qualification), the narrow Draft-RHP exclusion in `official_offer_amounts.py`, and regression assertions/tests in `test_automatic_official_issue_discovery.py`. These changes are separately validated by the **124-pass focused group**, real Linux OCR **1 passed / 24 deselected / 5.65 seconds**, and final native verification. This is not falsely described as a second full-suite run at the later SHA. `tested-tree-final.json` records the final 291-path candidate. All other runtime/test/config/schema/fixture/frontend bytes remain identical to the broad-run snapshot.

## Publication / preservation

Runtime implementation: `575c572`, `b75a136`, `5cc9f36`, `eac080f`, authority-scope correction **`3f8bb49`**, OCR throughput correction **`1139e01523a1ae35b09c0da8227151ce0a96cb1c`**, full-width identity correction **`9ba5e58`**, Draft-RHP exclusion **`cd7b445`**, and final explicit price-currency qualification **`a3279506b6cee66482135324528a56b6264826a9`**. Broad-suite snapshot including evidence transport: **`dab7b7604af5367ae1d1bb38a20546f1f61229fc`**. Final targeted/native-validated runtime: **`a3279506b6cee66482135324528a56b6264826a9`**. All are published on the existing session branch; no amend, reset, force-push or branch switch.

`source-remote-verification.json` independently reads back GitHub commit/tree objects for runtime **`a3279506b6cee66482135324528a56b6264826a9`**, matches all **291** final validation-path SHA-256 values and Git blob identities, and rereads the exact native check's structured output. The controlling native result is neutral/BLOCKED, not success. The authoritative tracker records this as **PARTIAL / acceptance blocked**, not completed.

Main remains **`01ba66c12ca1195fd7acbd287c3e39a019808094`**. PR #6 remains **OPEN/unmerged**, head `arena/5dd3fe52-ipo-screening-engine` / **`e05c0efbca1ecb3024e52da73a22e180ea171118`**, base `arena/573e69a4-ipo-screening-engine` (API base SHA `9e8c260576b85fad66484c19eec04fe328e1575f`; remote base-branch tip `6f54b3722532c2153e07d9a2cea59696fdd11def`). No PR was merged, closed, retargeted or advanced. The final documentation/evidence publication is on this same session branch; the final handoff supplies its commit SHA after an additional GitHub tree/blob readback. That publication changes no runtime/test/config/fixture bytes relative to the controlling native head.

Unrelated work, runtime logs and earlier untracked investigation files are preserved. Native HTTP evidence and terminal-result checks, not mocked HTTP tests or green diagnostic status, control the Jio acceptance statement. Remote readback is self-run object verification, not a claim of independent human review.
