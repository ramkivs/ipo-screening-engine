# Jio 33/100 — final evidence recovery and field reconciliation

**2026-10-23 · Documentation-only, non-authoritative investigation.** This is a read-only evidence investigation, not an evaluation, source amendment, clearance or implementation. It follows the [prior report at 18d0eb9](https://github.com/ramkivs/ipo-screening-engine/blob/18d0eb91549ba14534c750b2305ec3147be02c6f/docs/investigation/JIO-33-ARTIFACT-RECONCILIATION-2026-10-23.md), whose arithmetic and 27-entry baseline are not repeated here.

Target **L**: `JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794`.
Target **P**: `JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872`.

## 1. Executive outcome: what this pass actually closes

1. **GCP nondisclosure is now source-verified, not merely inferred from normalized null.** The hash-matched filing's page 116 deployment table explicitly leaves GCP `[●]`, to be finalized with the issue price/Prospectus. Debt prepayment **275,000 INR million** is disclosed on116–117 but absent from target schedule. No separate unidentified-acquisition object is listed in the inspected Objects section116–125. Neither the ceiling nor a cash residual is the actual GCP amount.
2. **Post-issue promoter percentage is genuinely deferred in the inspected ownership disclosures.** Page104 names RIL, 5,937,841,645 shares, pre-issue66.43%; post-issue percentage `[●]`. Page109 repeats post-allotment placeholders. The null post percentage is not proven extraction failure. The *pre*-issue null, however, coexists with an explicit66.43% source value.
3. **Auditor facts were recoverable.** Pages93–94 identify the joint auditors and explicitly state no statutory-auditor change in five years. Page322 explicitly links their reports to all three fiscal years. Page430 expressly says no EOM across the listed periods. None of the corresponding tenure/reputation/repeated-EOM fields reached this target. Source-level matching/section limitations are reproducible; exact original stage of omission still requires the missing intermediates.
4. **Concentration is not a simple missing-table bug.** Pages44–45 disclose *top seven non-related network vendors*, separate related parties, and a restricted capex denominator—not the governed top-five supplier/customer scalar. A different ranking/denominator cannot silently become that scalar.
5. **The quantified contingent amount is directly verified.** Note37/page 405 has FY2026 claims15,021; commitments26,198 are separate/excluded. No unquantified declaration appears in that defined note. Broader RIL/promoter litigation contains an unquantifiable arbitration claim and a pending SEBI revision, requiring scope/status adjudication, not inference that every exposure is quantified or a knockout is clear.
6. **Two extra source/consumer discrepancies emerged:** target `net_worth=3,359,769` matches owners' equity rather than the filing's explicitly defined FY2026 Net Worth3,340,134; target `kmp_exits_2y=0` conflicts with disclosed CEO and company-secretary resignations on312 as a literal exit count. Neither is corrected here; definitions and original producing path must be reconciled before implementation.
7. **Runtime conclusion: `RUNTIME_REVISION_UNVERIFIABLE_FROM_RETAINED_EVIDENCE`.** History contains an authenticatable *different* hosted-Windows run and source lineage, but no target ingestion record/source fingerprint. The original raw extraction/field map was not recovered from reachable repository text. Seventeen Actions artifacts are listed, but artifact-byte download was blocked by the sandbox's storage-host boundary, so inaccessible archives are not declared searched or empty.

**No score or outcome changed.** 33, A9 NONTERMINAL_UNRESOLVED and K1/K2/K5 UNVERIFIED remain the historical recorded states. Recovering facts does not authorize modifying those immutable records or promise additional points.

## 2. Bounded repository search: exact scope, locations and exclusions

### 2.1 Reference correction and immutable baseline

The directive spells the evidence SHA `ebb8a6c6b0d12e54228ec6b523dba025e927fb0b`; that object does not resolve (`git cat-file -e ...^{commit}`). The actual published commit used by the prior report and recovered evidence is **`ebb8a6c6b0d12e54228ec6b523bda025e927fb0b`** (the `bda`/`dba` transposition matters). All source/evidence links here pin that existing object, not a fabricated replacement.

At this pass, evidence branch tip is **`1dd6e14e7fa50a677beefba9ca7d0d1a7b322c58`**. Its only change after ebb8a6c is the Paras Healthcare PDF; **Jio artifacts and source are unchanged**. It was inspected, not checked out or merged. Arena publication parent is18d0eb91549ba14534c750b2305ec3147be02c6f. All remote heads/tags were enumerated and fetched into remote-tracking refs without switching branches.

### 2.2 Method and search result

`git ls-remote --heads --tags`, `git for-each-ref`, `git log --all`, `git rev-list --all --objects` and `git cat-file --batch` inspected **269 reachable commits, 3,218 named reachable objects and 1,354 non-NUL text blobs**. All text blobs, including the 5MB anchor-review JSON, were searched for both exact target IDs and the full filing SHA. There were **70 matching unique blobs**:19 contain L,19 contain P,51 contain the filing SHA (overlap). ID hits outside the recovered bundle were the prior report, not a separate target trace. File/path searches additionally covered raw/extract/routing/ingest/activity/runtime/build/deploy/manifest/log names (340 candidate text blobs), so records not containing the full ID were not excluded solely for that reason. Binary PDFs were handled separately. This is reachable remote/local history, not inaccessible deleted refs, Windows disks or every blob ever hosted by GitHub.

| Search location / reference | Records inspected / result | Boundary |
|---|---|---|
| `docs/investigations/jio-ipo-score-33/` at ebb8a6c | All 28 publication files; nine normalized artifacts per target, four API captures, inventories/README/checksums/recovery summary | No original ExtractionReport, private map, ingestion activity or loaded-code fingerprint; existing export manifest identifies the store but not those additional files |
| `docs/investigation/aggregator-fallback-2026-10-22/{README.md,native-accepted.json,native-first-duplicate-failure.json}` | Runtime SHA, full terminal event array, source candidates/conflicts, API evidence/trace, restart/duplicate proof and source-request diagnostics exist | **Different** October 21 evaluation, not L/P; useful comparator, not recovered target builder input |
| `docs/investigation/jio-recovery/{REPORT.md,baseline-api-result.json,latest-api-result.json}` | Explicit hosted-Windows runtime62bad2c, blocked `ing-75d3241aa25f40c0`, no evaluation; original `ing-0168a590a93c4448` already unavailable | Same PDF ≠ same ingestion. No latest target linkage |
| Same directory: `rhp-all-pages-inventory.json`, `independent-source-audit.json`, `additional-official-documents.json`, `anchor-review.json` | Existing591-page RHP inventory, source response records, parameters/forms, full18-page diagnostic anchor OCR with original-document hashes | Independent prior research; anchor OCR remains UNVERIFIED, not accepted market input |
| `docs/investigation/offer-extraction-improvements-2026-10-21/{jio-native-text.json,native-api-result.json,publication-readback.json}` | Native-text diagnostic names runtime e416b1f and PDF hash; cover placeholders/OFS and limited official-term native read scope | Not complete pre-normalization domain extraction for L/P |
| `docs/investigation/automatic-official-discovery-2026-10-21/` | `native-39609728737/live-ingestion-records.json`, `native-39612462531/live-ingestion-records.json`, result checks, `tested-tree-{backend,final}.json`, source summaries/annotations | Earlier discovery attempts, not target logs; no field map for current target |
| `docs/investigation/ingestion-worker-stall-2026-10-21/{REPORT.md,available-jio-results.json,available-jio.log,tested-tree.json}` | Existing failures/reproductions and test-tree context | Earlier diagnostic evidence, not original L/P execution |
| `docs/investigation/activity-storage-windows-2026-10-21/` | REPORT, baseline/corrected Windows annotations, tested-tree, terminal-read recovery and storage logs | Establishes durable-activity capability, not that L/P activity was exported |
| `docs/investigation/runtime-verification-2026-10-20/{REPORT.md,tree-identity.json,checks.json}`; `issue-terms-platform-2026-10-21/` manifests | Existing tree-equivalence/testing and runtime-transport records | Authenticates their own tested trees only; not October 22/23 user Windows process |
| `HD-FIRE-JIO-EVIDENCE-REMEDIATION-2026-10-20.md`, `HD-FIRE-JIO-SCORE-RECONCILIATION-2026-10-19.md`, `fixtures/jio/jio_canonical_2026-10-19_pre_evidence_remediation.json` | Older values/source corrections and snapshot fixture | Not original field map; fixture cannot replace target inputs |
| `engine/ipo_screening/extraction/{extractor,toc,sections,financial_tables,builder,interfaces}.py`, `canonical_input.py`, `evaluation.py`, `evaluation_record.py`, `presentation/service.py` | Candidate flow, first-candidate lookup, map serialization/stripping and A15 ID fallback; commit history for each | Reconstructed source path; no engine functions executed |
| `.github/workflows/`, hosted run API, artifact API, tags/releases/deployments API | 42 listed workflow runs (queried via the paginated runs API),17 listed artifacts; no tags, releases or deployments returned at inspection | Metadata inspection, not new workflow dispatch/test run |
| Local checkout and persisted read-only copies | Existing filing and publication copies; no Windows/build evaluation store or extra target raw extraction found | User Windows filesystem and localhost are not accessible from this sandbox |

### 2.3 Actions artifact boundary—do not hide the inaccessible evidence

The 17 listed archives comprise **1 `aggregator-source-research`**, **5 `bse-public-source-contract`**, **1 `jio-anchor-original-page-review`**, **10 `jio-native-api-evidence`**. All listed creation dates are October 21. The newest native archive belongs to run **39667791831**, head **ba7a0694db4714d0f6a53ef1aad48a28330675ca**. `gh run download 39667791831` reached GitHub metadata but its Azure `productionresultssa12.blob.core.windows.net` download returned EOF under this sandbox's outbound-host restrictions. No archive bytes were recovered; signed URLs/credentials are intentionally omitted here. No repeated blocked download was attempted.

Retained repository JSON from that very run supplies its evaluation ID and runtime (section3). Therefore even this likely-rich archive is not represented as a target original. Nevertheless unavailable archive contents cannot be ruled out exhaustively; arrange an authorized GitHub-hosted text export of any additional target-correlated records if present. Existing workflow Checks/annotations and publication readbacks were also inspected in retained JSON; no target-ID linkage was found. No new CI run was deliberately started; repository push may independently trigger configured CI.

Artifact-name counts from the API (authoritative enumeration for the preceding paragraph): `{"aggregator-source-research": 1, "bse-public-source-contract": 5, "jio-anchor-original-page-review": 1, "jio-native-api-evidence": 10}`. Listed run IDs: 39667791831, 39664569074, 39661966205, 39650886624, 39648966250, 39649331505, 39648816070, 39638363459, 39637496894, 39636630422, 39636184160, 39634675822, 39633024785, 39632247777, 39633470712, 39630698170, 39634283261.

## 3. Runtime/source identity conclusion

**`RUNTIME_REVISION_UNVERIFIABLE_FROM_RETAINED_EVIDENCE` for L and P.** This is the evidence-limited conclusion, not a claim that the runtime could never be authenticated by a retained Windows activity/backup elsewhere.

| Evidence | What it establishes | What it cannot establish |
|---|---|---|
| L/evaluation.json and P/evaluation.json: engine1.5.0, config1.5.0, spec1.5; canonical record versions | Declared product/config contract | Loaded Python/module identity |
| Config SHA `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b`, matching both inspected configurations | Scoring-config equivalence; prior report independently reproduced it | Engine/extractor/service/deployment SHA |
| Filing source URI `C:\Users\USER\AppData\Local\Temp\ipo_ingest\72480c2e249eb8da\filing.pdf`, hash, retrieval `2026-10-23T05:16:22Z` | Source metadata records a Windows-shaped staging path and exact PDF bytes | An ingestion ID: that directory is the PDF hash prefix, shared by uploads, not `ing-*`; not proof of current access |
| Latest evaluated_at `2026-10-23T05:18:16Z`, prior `2026-10-22T10:19:13Z`; lifecycle actor system_ingest/statutory_filing_ingest | Stored evaluation identity/time and ingestion-family lifecycle labels | Exact activity correlation, startup checkout or clean/dirty state |
| Publication lineage at75df573 → ba7a069 runtime; all target core functions compatible | Plausible code family and concrete candidate implementation to inspect | Proven ancestry/version of an unrecorded user process; not enough for NARROWED revision label |
| `native-accepted.json`: platform win32, runtime **ba7a0694db4714d0f6a53ef1aad48a28330675ca**, PDF hash match, `ing-85264e8a401045de`, evaluated_at Oct21 T20:19:43Z, **JIO-PLATFORMS-LIMITED-20261021-201943Z-final-840c0a14** | A separately recorded hosted-Windows execution with explicit revision and ingestion correlation exists | That execution is neither target; it cannot authenticate their runtime retroactively |
| `runtime-verification-2026-10-20/tree-identity.json` and tested-tree receipts | Content equivalence for specific earlier tested trees; limitations recorded in their reports | A deployment record connecting those trees to L/P |
| Recovery README: `G:\ipo-screening-engine\ipo-screening-engine\build\evaluations` | Exporter's asserted source location and read-only recovery method | Runtime identity, original extraction persistence or existence of source backups |

**Source conclusions that remain valid:** the stored consumer values/outcomes and source-page findings; exact static limitations at pinned source commits; demonstrated external-EV association omission in canonical records; lack of an accepting Final A9 branch in inspected code. **Historical causation still unproven:** which extractor revision ran, actual routing/text provider output, candidate conflicts or builder precedence for L/P, whether an unsupported default rather than a real candidate supplied a particular scalar, and whether a connector was attempted. Code compatibility and matching source hash are not a new fingerprint.

## 4. Original filing bytes and direct page examination

File: [evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf).

- Size: **11,630,670 bytes**; SHA-256 **`72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`**, independently reverified before reading.
- **591 pages**. Existing `rhp-all-pages-inventory.json` was reused for coverage/source context but its truncated Objects snippet was insufficient. This pass used an isolated `pypdf` reader to read original page text, producing591 nonempty page texts with no page-read exception. **No application extractor, section extractor, builder, ingestion or evaluator was imported or run.** Text artifacts are scratch material outside the repository, not rewritten evidence. No claim of OCR, visual image review, or new live source retrieval is made.
- Physical PDF page number and printed page label agree on the directly inspected key pages (e.g.5 TOC;44–45;79;93–94;104;109;116;312;322;405;430;470–474;487). No TOC offset is assumed from another filing. Financial pages carry the printed number at the bottom.
- Recorded official archive/member source is `https://nsearchives.nseindia.com/content/ipo/RHP_JPL.zip#zip-member=RHP_JPL%2FJio%20Platforms%20Limited_RHP.pdf` with the same hash. Hash identity links the source pages to the target bytes; it does not independently verify a live publisher response today. The local directory label “non-authoritative” is not silently upgraded into regulator confirmation.

### 4.1 Source page registry for the new findings

| Pages / section or table | Precise inspected evidence | Limit |
|---|---|---|
|5 / TOC | “OBJECTS OF THE ISSUE …116”, “THE MANAGEMENT …293”, “RESTATED CONSOLIDATED FINANCIAL INFORMATION …320” | Actual heading differs from candidate router's OFFER/OUR MANAGEMENT patterns |
|44–45 / Risk16, vendor table | A=capex excluding spectrum/other intangible/certain leased assets; FY2026 A286,997; seven non-related vendors B43,032,14.99%; related D50,246,17.51%; combined32.50% | Not top-five all-supplier concentration, not revenue denominator |
|79 / Summary of contingent liabilities | June2026 claims14,688, Net Worth3,417,785, ratio0.43% | Interim summary; not FY2026 pair used by target |
|93–94 / Joint Statutory Auditors; Changes in auditors | Deloitte Haskins & Sells LLP and Chaturvedi & Shah LLP; “There has been no change in the statutory auditors of the Company in the last five years preceding the date of this Red Herring Prospectus.” | Explicit continuity evidence, not inference from silence; A22 report-evidence path also examined |
|104 / Capital Structure4(b) | RIL pre/post share count5,937,841,645; pre66.43%; post `[●]`; “To be updated prior to filing of the Prospectus with the RoC.” Promoter-group members/directors hold no shares | No disclosed numeric post percentage |
|107–108 / Reg31 shareholding table | As-of-RHP shareholding; category(A) promoter/group vs(B) public; total-share denominator A+B+C2 | No post-issue column; cannot turn66.43 into post percentage |
|109–110 / Aggregate pre/post-allotment shareholders | RIL pre66.43%; post low/high-band counts/percentages `[●]`; assumes full subscription, actual allotment-dependent | No filed post-allotment percentage/denominator result |
|116 / Deployment of Net Proceeds | Debt prepayment RJIL275,000 for total/FY2027; GCP `[●]`/`[●]`; Net Proceeds `[●]`; footnote “To be finalised upon determination of the Issue Price and updated in the Prospectus” |25% is a ceiling, not an allocation |
|117 / Details of Objects1 | Up to275,000 from Net Proceeds for RJIL borrowing prepayment; shortfall in debt use goes to GCP subject to25% | No determinable actual residual GCP |
|122 / Objects2 | GCP may include branding, working capital, investments in subsidiaries, acquisitions, inorganic growth etc.; allocation determined by Board | Mention of acquisitions within GCP is not a separately quantified unidentified-acquisition object |
|312 / Changes in KMP/SM over last3years | CEO Kiran Mathew Thomas resigned March23,2026; company secretary Jyoti Jain resigned June19,2026 (continues in RJIL); CEO/CFO are different roles | Does not establish CFO resignation; does contradict literal KMP exits0 |
|321–324 / Joint examination report |322 para5(b): “Auditors’ report jointly issued by us dated April24,2026, April24,2025 and April22,2024 respectively … years ended March31,2026,2025 and2024”;324 signed by both named firms | Actual positive three-FY report linkage, not merely names repeated on signature pages |
|324 / Opinion clause8(b) | “do not require any adjustment for modification as there is no modification in the underlying audit reports” | Supports stored unqualified classification, not no going-concern uncertainty |
|329 / Restated assets/liabilities | FY2026 Equity Share Capital89,390 +Other Equity3,270,379 =3,359,769 | Owners' equity basis differs from expressly defined Net Worth |
|405 / Note37(I), five-period table | Claims14,688 /14,151 /**15,021** /30,183 /27,924 (June26/June25/March26/March25/March24); (II) commitments90,389 /65,624 /**26,198** /51,272 /58,284 | “Not likely to have any material effect” is management assessment, not no unquantified exposures |
|430 / Note47.4(b),(c) | No reported Other Legal/Regulatory matters and “There are no Emphasis of matters in auditor’s report” for June26/June25/March26/March25/March24 | Explicit statement; not a full independent CARO materiality/coverage adjudication |
|450–453 / Non-GAAP measures | Definitions and arithmetic bridges for EBITDA, EBIT, debt, net worth, ROCE etc.;451FY2026 Net Worth3,340,134 excluding OCI,452explicitly SEBI ICDR basis | Existence of bridges does not establish *all* adjusted metrics reconciled |
|470(a)(iii) / Promoter litigation | SEBI complaint dismissed as time-barred; SEBI revision before Bombay HC “currently pending” | Positive pending promoter matter, not issuer/ED-wide absence; current authoritative status still needed |
|470(c)–471 / RPL trades |2026 Supreme Court disposal including fraud finding set aside and disclosure-penalty part upheld | Do not read historic orders alone as still-active fraud case |
|472–473 / SEBI actions on RIL |2022penalty appeal dismissed Dec2025; EPS show-cause disposed Sep2021 without penalty | Resolved matters do not independently prove no other active action |
|472 / RIL PMT arbitration | “any claim cannot be determined until quantification is done by the Tribunal in the final award” | Unquantified claim belongs to promoter litigation, outside Note37 section; not an automatic issuer contingent-flag positive |
|473–474 / Tax/legal scope | Claims “to the extent quantifiable and excluding interest”;67,955 tax disputes not recognized as contingent liabilities by management | No adding all promoter/subsidiary legal claims into Note37 numerator |
|487 / Regulatory disclosures | Company/directors/promoter/group not debarred from accessing capital markets by SEBI | A scoped debarment denial is not no active SEBI/ED action |

Source quotations above are transcribed from original PDF text; line wraps/spacing are normalized in short quotations, not financial values. They are new investigation observations, not EV registry insertions.

## 5. Extraction-to-consumer reconstruction and concrete failure boundaries

Legend: **H** = directly evidenced historical *stored state/association*; **D** = this pass's direct source-page observation; **R** = reproducible reconstruction from pinned code, not an attested historical execution. No newly read source value was assigned to either target.

### 5.1 Common stages, persistence and evidence-ID transformation

Candidate pipeline: [extraction/extractor.py:35-112](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/extraction/extractor.py#L35-L112) returns `(canonical_dict, ExtractionReport)`; report metadata includes `page_routing`, raw candidate objects include field_path/value/page/quote/confidence. The service assigns `extraction_report` at1481 but has **no later reference** to it. `filing_extraction` completion events at1492+ contain issuer/IPO ID only; issue-term-specific events retain selected term evidence/candidate diagnostics, not every domain-field candidate or routing result. This is a concrete persistence coverage gap in that source; the files were not necessarily ever durably written for L/P.

Builder [extraction/builder.py:131-154](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/extraction/builder.py#L131-L154) `_get_field` returns the **first** candidate for a field; `_build_evidence` assigns dictionary entries in iteration order, so duplicate-field evidence can be **last** candidate. That static first-value/last-map asymmetry is a separate conflict risk; **no original duplicate candidate list exists to prove it happened here**. Builder references/base precedence are inspected, not assumed executed.

[extraction/interfaces.py:73-94](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/extraction/interfaces.py#L73-L94) transforms `governance.auditor_opinion` into `EV-governance-auditor_opinion` (dots→hyphens, `[`→underscore, `]` removed). The builder's map is keyed by **field path**, not EV ID. `canonical_input.py:231–283,355–361` builds an in-memory registry/path association but strips private metadata from input snapshot; persisted `EvaluationRecord` retains the registry, not full map. [evaluation_record.py:782-812](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/evaluation_record.py#L782-L812) then checks only `EV-<dotted legacy path>` during scalar projection.

**H:** canonical validation explicitly says LEGACY_FIELD_EVIDENCE_MAPPING_INCOMPLETE. The original map is absent. **H:** auditor opinion and quantified contingent value have matching extracted EVs in evidence.json but their canonical field rows contain only local A15 input evidence. **R:** the exact fallback-ID expression explains both lost external associations. It does not change either value, create either null or cause A9/knockout missing inputs. A missing container-to-leaf association (proceeds/financial periods) is also not the same as ID mismatch.

### 5.2 Target values/associations actually preserved (H)

The table below is generated solely by reading L/input.json, evidence.json and canonical field_values. “Not retained” means no corresponding scalar EV, not proof that the original PDF lacks the fact. Stored unit is INR_MILLIONS for financial/proceeds amounts. P has the same consumed values and corresponding association limitation.

| Field | Frozen input | Matching registry ID | Canonical external EV refs |
|---|---|---|---|
| `use_of_proceeds` | `[{"amount":null,"category":"gcp","undisclosed_marker":"[●]"}]` | `EV-use_of_proceeds` | None |
| `capital_structure.promoter_pre_pct` | `null` | Not retained | None |
| `capital_structure.promoter_post_pct` | `null` | Not retained | None |
| `governance.auditor_opinion` | `"unqualified"` | `EV-governance-auditor_opinion` | None |
| `governance.auditor_changed_3y` | `null` | Not retained | None |
| `governance.auditor_reputed` | `null` | Not retained | None |
| `governance.repeated_eom` | `null` | Not retained | None |
| `governance.eom_materiality` | `null` | Not retained | None |
| `governance.auditor_or_cfo_exit_2y` | `"ABSENT"` | Not retained | None |
| `governance.kmp_exits_2y` | `0` | Not retained | None |
| `business.top5_customer_pct` | `null` | Not retained | None |
| `business.top5_supplier_pct` | `null` | Not retained | None |
| `financials.contingent_liabilities` | `15021.0` | `EV-financials-contingent_liabilities` | None |
| `financials.contingent_liabilities_unquantified` | `null` | Not retained | None |
| `governance.going_concern_uncertainty` | `null` | Not retained | None |
| `governance.sebi_ed_action_active` | `null` | Not retained | None |

### 5.3 Field-specific traces, with unobserved transitions explicitly retained

| Field | Source → candidate → route (D / R) | EV/map → builder → persisted input (H where stated) | Consumer / conclusion |
|---|---|---|---|
| `use_of_proceeds[gcp].amount` | D116/122:placeholder; raw candidate not recovered. R objects extractor982–1061 scans first6pages of route/default120–145, matches GCP and placeholder | H `EV-use_of_proceeds`, page120, PROCESSING_SUMMARY only; R list forwarded by builder; H sole gcp/null/marker item. Container map cannot prove leaf/page-specific source quote | H use_of_proceeds UNKNOWN; source now confirms amount deferred, independently of incomplete schedule |
| `use_of_proceeds[debt_repayment]` | D116–117:275000; historical candidate/route unavailable. R Objects heading fails router's OFFER-only pattern and default120 misses116–117; debt patterns do not recognize “Prepayment, in full or in part” | H no debt item/EV. Source-to-target schedule omission **confirmed**; exact historical route versus non-match not identifiable. No proof builder dropped a candidate | Missing debt item is a real coverage defect, **not** what resolves unknown GCP; ordered bucket still cannot use undisclosed GCP |
| `capital_structure.promoter_pre_pct` | D104/109:66.43 for RIL; Dgroup other members hold none. R sections744–834 heading/Total(A) parser does not handle all named-table layouts | H null/noEV; R builder carry/defaultNone; original candidate/map unavailable | Source value found but missing at consumer; not a proven candidate-to-builder mapping loss |
| `capital_structure.promoter_post_pct` | D104/109–110:post percentages `[●]`; R A21 requires genuine post column and numeric percentage, rejects pre-only rows | H null/noEV; R builderNone; canonical UNKNOWN | D4promoter criterion UNKNOWN; K4 remains its stored CLEAR via other false conditions. No authorized dilution substitute |
| `governance.auditor_opinion` | D324matches exact registry quote. Candidate not retained; R report-span321–324 recognizes conclusion | H `EV-governance-auditor_opinion`; H input unqualified; original map absent; canonical omits that EV and keeps local reference | K1adverse-opinion leaf false; **MAPPING_FAILURE_CONFIRMED for external association**, not value loss |
| `governance.auditor_changed_3y` | D94five-year continuity +322explicit three-FY reports jointly issued by both auditors. R name recognition prerequisite and narrow same-line tenure regex | H null/noEV. R builderNone. Missing original raw list prevents proving whether extraction, precedence or a different runtime caused omission | Auditor bucket stops at missing tenure. Recoverable source evidence exists under A22; no automatic field rewrite authorized |
| `governance.auditor_reputed` | D93/324named Deloitte/Chaturvedi; R name-regex and existing reputed-firm lookup | H null/noEV. No retained candidate. Manual observer can identify name but cannot attest historical matcher execution | Source-name coverage failure reproducible; reputation is an established lookup classification, not PDF's self-certified assessment |
| `governance.repeated_eom` | D430explicit no EOM for all five dates; R negative-EOM detector only examines report span and is nested under successful auditor-name branch | H null/noEV; canonical UNKNOWN. Source present but not in consumed evidence | A22allows explicit negative, no need to invent cross-year positive detection; provenance/coverage fix would require separate authority |
| `governance.eom_materiality` | D430no EOM/other reported legal-regulatory matters; D473tax matters still exist; no accepted scalar assessment retained | H null/noEV; R builderNone; no definition-approved materiality candidate proven | Global penalty UNKNOWN; no-EOM sentence alone cannot assign low/none across EOM/CARO/disputed-tax contract (A27 unresolved) |
| `governance.auditor_or_cfo_exit_2y` | D94no auditor change5years; D312scoped KMP-change schedule contains CEO/CS resignations but no CFO exit. R builder can carry optional flag, no domain emitter for it shown | H field absent/noEV; candidate/map unobserved | Auditor/CFO-exit penalty UNKNOWN; CEO is not CFO. Need complete governed personnel/period coverage before asserting combined false |
| `governance.kmp_exits_2y` | D312CEO/CS resignations; no retained count candidate. R builder default0 (370), no section emitter found | H0/noEV; cannot distinguish historical default from another source solely by value | Existing board/KMP bucket input is insufficiently supported and conflicts with literal source count. Definition/role coverage review, not a new score |
| `business.top5_customer_pct` | Full text search customer/top5/topfive; inspected risk/business/concentration contexts. No exact five-customer metric located | H null/noEV; R extractor mainly pages1–54; builderNone | No derivable grouped market-share-to-top5 substitution. Source-absence conclusion limited to inspected text, not universal proof about unavailable annexures |
| `business.top5_supplier_pct` | D44–45top7network vendors and related parties; R extractor2960+requires “suppliers”/“top5” labels, never constructs a governed five-vendor rank from this table | H null/noEV; R builderNone | Qualitatively material supplier concentration found; exact top5metric requires denominator/entity/method decision, not32.50%,14.99%or first5rows by label |
| `financials.contingent_liabilities` | D405FY March 2026 column 15,021, commitments excluded; raw candidate absent. R section-total extractor617–776aligns fiscal columns | H hyphenated EV quoted row label; H15021; canonical1502.1000000000001crore local-only EV. R ×0.1unit normalization | K5ratio leaf0.4470843084747791%; matches stored denominator, not proof every exposure quantified |
| `financials.periods[2].net_worth` (FY2026) | D:329 owners’ equity 3,359,769; D:451/487 defined Net Worth 3,340,134. R financial extractor uses equity labels | H FY2026 target 3359769; financial-period containerEV, no scalar association. Origin selection not independently logged | K1positive net-worth leaf and K5denominator; source-basis difference now explicit. Do not silently recast owners'equity as statutory Net Worth |
| `financials.contingent_liabilities_unquantified` | D405defined note has no positive unquantified sentence and no scoped negative completeness statement. D472unquantifiable promoter arbitration lies outside note | H null/noEV. R extractor only positive in same section; builder maps supplied flag. No candidate-loss evidence | K5UNKNOWN intentional under A20; promoter claim needs scope/materiality adjudication, not raw keyword true/false |
| `governance.going_concern_uncertainty` | D321–324no positive uncertainty clause located; no explicit scoped denial of uncertainty. “going concern” on253is scheme accounting, not auditor uncertainty | H null/noEV. R positive-only matcher; builderNone | K1UNVERIFIED and critical safety INCOMPLETE; A19requiresUNKNOWN absent positive evidence; no approved negative-confirmation rule |
| `governance.sebi_ed_action_active` | D470pendingSEBIrevisionagainstRIL;487debarmentdenial;472–473resolvedSEBImatters. No completeED/agencycoverage | H null/noEV. R litigation parser/search selects supported scope/status; no original candidate/rejection record | K2UNVERIFIED. Positive pending promoter matter is found, but active-condition/entity/status adjudication and authoritative coverage still needed; never convert debarment denial into both-agencyclearance |

**Index clarification:** the table's net-worth FY label is authoritative; the precise input array position is recorded below from frozen input, rather than assumed from chronological display.

- Frozen `financials.periods[0]`: FY=`FY2024`, net_worth=`2782864.0` INR_MILLIONS.

- Frozen `financials.periods[1]`: FY=`FY2025`, net_worth=`3050474.0` INR_MILLIONS.

- Frozen `financials.periods[2]`: FY=`FY2026`, net_worth=`3359769.0` INR_MILLIONS.

### 5.4 Static route/pattern checks made in this pass—not an extraction rerun

The TOC at5 uses OBJECTS OF THE **ISSUE**. Pinned `toc.py:29` only recognizes OBJECTS OF THE **OFFER**; `extract_objects_of_offer` fallback is120. The actual debt table at116–117 lies outside that default's six-page read120–125. A second independent mismatch is the supported debt phrases (`repayment and/ or pre`, `repayment of term loans`, `debt repayment`) versus source “Prepayment, in full or in part”. These are **source-qualified static defects/limitations**, not merely guessed page-offset failures. The target's summaryEV points to120, consistent with defaulting, but no original route metadata proves that branch ran.

Auditor route is Restated Financial Information320→next routed section432. A standalone text/regex comparison of the two pinned auditor-name expressions and two tenure expressions against pages320–432 returned **zero matches**, despite actual named signatories and322's explicit three-year joint reports. This comparison did not import/run SectionExtractor or generate candidates. It reproduces the specific static limitation: source layout/phrasing outside accepted expressions; tenure is also gated on a recognized name. Report-span logic limits no-EOM detection to321–324 and misses430's explicit note. A94general-information continuity sentence is outside that financial scan. Source text is recoverable; exact original pypdf version/layout/run path remains unverified.

### 5.5 Code-level failure dispositions (not historical-runtime attestations)

- **EXTRACTION_FAILURE_CONFIRMED — inspected Objects recognizer/route contract:** the exact filing uses ISSUE and “Prepayment, in full or in part”; the pinned route/category recognizers do not cover those forms. This is confirmed from literal source and document text. The original run's actual route/candidates remain unavailable; the historical field disposition is therefore SOURCE_VALUE_FOUND, not a fabricated original parser trace.
- **EXTRACTION_FAILURE_CONFIRMED — inspected auditor name/tenure coverage:** the named signatures and explicit three-FY report statement do not match the inspected expressions across the reconstructed financial page range. The no-EOM note is outside the selected report span. This is a source-level failure to cover the actual disclosed evidence, not proof of an executed target function call.
- **MAPPING_FAILURE_CONFIRMED — target canonical external association:** retained opinion and quantified-contingency EVs are not linked in the exact canonical scalar rows. The original map is not recovered; local snapshot references and the values themselves are preserved. The source ID-convention mismatch explains these specific missing associations.

### 5.6 Meaning of “confirmed failure” here

- **Historically proven stored discrepancy:** debt allocation and pre-holding/tenure/EOM facts exist in exact target source but are absent from consumed target fields; auditor/contingentEVs exist but are not externally linked by canonical field rows. This is enough to establish specific source-to-consumer coverage/association gaps.
- **Not historically proven intermediate cause:** absent raw candidates/routes/maps prevent attributing all source-to-consumer omissions to a specific original extraction function, builder drop, rejected candidate or deployed patch. The source-level route/regex defects are reproducible at ebb8a6c, not a counterfeit original execution trace.
- **Provenance defects do not explain every UNKNOWN:** no missing EV association can supply a numeric GCP/post-promoter value that the document expressly defers. The ID mismatch cannot acquire market observations, qualify GMP or authorize a negative safety flag.

## 6. Consolidated dispositions and safety adjudication boundary

These dispositions describe **evidence recovery**, not authorization to change target values. Multiple dispositions are used only where distinct layers genuinely differ. “Retained” means answerable from accessible source/records; “Windows” means original-history evidence; “external” means a qualified provider/regulator/source record is still needed.

| Exact field / gate | Existing target state | Disposition | Evidence, extraction/mapping finding and historical confidence | Required resolution; access |
|---|---|---|---|---|
| `use_of_proceeds[gcp].amount` / criterion | null+marker /UNKNOWN | **SOURCE_DISCLOSURE_CONFIRMED_ABSENT** (numeric allocation in inspected filing) |116/122 expressly defers amount; normalized state consistent. No map defect necessary to explain UNKNOWN | No recovery of actual amount from these bytes; eligible later Prospectus/allocation disclosure externally required. Preserve null |
| `use_of_proceeds[debt_repayment]` | Item absent | **SOURCE_VALUE_FOUND** |116–117 discloses 275,000; end-to-end omission proven. Static route/phrase defects confirmed, historical exact branch unproven | Retained pages settle value; Windows raw route/candidates settle omission stage; later implementation authority separate |
| `use_of_proceeds[unidentified_acquisitions]` | Item absent, not independently assessed amount | **NOT_APPLICABLE_WITH_SUPPORTING_EVIDENCE** (separate scheduled object only) |116 lists only debt/GCP; 122 permits acquisitions within GCP, not a separate allocation | Retained Objects schedule supports no separate object, not zero underlying spending. No invented amount |
| `capital_structure.promoter_pre_pct` | null | **SOURCE_VALUE_FOUND** |104/109: 66.43%, sole RIL promoter; raw candidate/map missing | Retained sufficient to document fact; Windows needed for original omission stage |
| `capital_structure.promoter_post_pct` / promoter criterion | null /UNKNOWN | **SOURCE_DISCLOSURE_CONFIRMED_ABSENT** (numeric post percentage) |104/109–110: placeholders, no numeric post column; A21 bars pre-only substitution | Later applicable allotment/Prospectus external evidence; no dilution backfill |
| `governance.auditor_opinion` external association | unqualified | **MAPPING_FAILURE_CONFIRMED** (canonical external association) |324 + stored EV versus canonical local-only row; exact ID fallback explains association loss, not value | Retained sufficient to diagnose; future mapping change separately authorized |
| `governance.auditor_changed_3y` | null | **SOURCE_VALUE_FOUND** |94 explicitly states no change in five years; 322 provides positive joint three-FY report evidence satisfying the substantive A22 requirement; no raw/EV | Retained source sufficient to support an evidence proposal; original emission/override needs Windows; do not silently update |
| `governance.auditor_reputed` | null | **SOURCE_VALUE_FOUND** (auditor identities) |93/324: Deloitte and Chaturvedi; pinned lookup would recognize Deloitte if name extracted, matcher finds none | Apply existing authorized firm lookup only in a later authorized correction; Windows settles original stage |
| `governance.repeated_eom` | null | **SOURCE_VALUE_FOUND** (explicit negative) |430: no EOM in five periods; A22 negative path exists, but selected report-span/name gate misses source | Retained sufficient to cite negative; no new cross-year true inference; future extraction separately authorized |
| `governance.eom_materiality` / eom_caro penalty | null /UNKNOWN | **GOVERNANCE_DECISION_REQUIRED** |430 negative EOM is not an approved scalar CARO/disputed-tax materiality assessment; 473 tax matters; A27 proposal remains unresolved | Retained pages inform adjudication; no unilateral low/none or waiver |
| `governance.auditor_or_cfo_exit_2y` / auditor_cfo_exit penalty | absent /UNKNOWN | **GOVERNANCE_DECISION_REQUIRED** |94 auditor continuity and 312 scoped KMP schedule found; CEO≠CFO; no combined flag/EV | Determine accepted period/entity completeness for compound flag; source records available, external employment/audit records only if scope demands |
| `governance.kmp_exits_2y` |0 | **SOURCE_VALUE_FOUND**; **GOVERNANCE_DECISION_REQUIRED** for counting |312: at least CEO/CS resignations, raw count absent; builder default 0 is a static risk | Define/confirm counting/exclusions and source-window alignment; Windows for original count/default; no new score |
| `business.top5_customer_pct` | null | **EVIDENCE_UNAVAILABLE** (exact scoped metric) |No exact metric located in 591-page text search and inspected risk/business contexts; population/market share is not concentration | No universal absence claim; issuer customer schedule or qualified disclosure if available; no runtime rerun required to establish current gap |
| `business.top5_supplier_pct` / concentration | null /UNKNOWN | **GOVERNANCE_DECISION_REQUIRED** |44–45: top-seven capex vendors and related parties found, not a disclosed top-five metric. No existing governed conversion found | Need denominator/population/ranking method before derivation, or explicit top-five disclosure externally; no 32.50% substitution |
| `financials.contingent_liabilities` |15,021 INR million | **SOURCE_VALUE_FOUND** |405 FY2026 claims; commitments excluded under A20; exact amount matches target | Retained verifies numerator; do not replace with interim or aggregate litigation |
| Same field external association | Local A15 reference only | **MAPPING_FAILURE_CONFIRMED** |Actual `EV-financials-contingent_liabilities` absent from canonical scalar references; lost-map/dotted-ID mismatch | Retained diagnosis sufficient; no value/KO changes |
| `financials.periods[FY2026].net_worth` |3,359,769 INR million | **SOURCE_VALUE_FOUND**; **GOVERNANCE_DECISION_REQUIRED** for basis |329/406 owners’ equity matches stored value; 451/487 defined Net Worth 3,340,134. No original selection trace | Confirm existing engine net-worth contract versus source statutory definition; recover Windows candidates; no silent denominator change |
| `financials.contingent_liabilities_unquantified` | null | **GOVERNANCE_DECISION_REQUIRED** |405 has neither a positive unquantified nor a complete-negative claim; 472 unquantifiable RIL claim is outside the defined note. Builder does map a supplied flag | A20 requires a positive in-section statement; never false from silence. Scope decision needed for other records; no mapping-loss evidence |
| `governance.going_concern_uncertainty` | null /critical UNKNOWN | **GOVERNANCE_DECISION_REQUIRED** |No qualifying positive / explicit negative in 321–324; A19 positive-only policy intentionally retains UNKNOWN | Any positive auditor evidence externally/current report coverage; clearing needs separately approved negative-confirmation rule, not opinion inference |
| `governance.sebi_ed_action_active` | null /critical UNKNOWN | **SOURCE_VALUE_FOUND** (pending promoter matter); **GOVERNANCE_DECISION_REQUIRED**; **QUALIFIED_EXTERNAL_EVIDENCE_REQUIRED** |470: pending SEBI revision; 487 debarment denial insufficient; no candidate/EV or ED coverage | Scope/status review under A23/A25 plus exact case docket/regulator records by applicable time. Do not automatically assert true/false |
| **K1** |UNVERIFIED | **GOVERNANCE_DECISION_REQUIRED** |Unqualified and positive net worth give false leaves; GC UNKNOWN persists | Keep recorded gate. Need scoped GC condition resolution under A19, not recovering an auditor tenure field |
| **K2** |UNVERIFIED | **GOVERNANCE_DECISION_REQUIRED** / **QUALIFIED_EXTERNAL_EVIDENCE_REQUIRED** |Pledge 0 gives a false leaf; SEBI/ED UNKNOWN; positive promoter matter requires adjudication | No waive/clear; review case status/entity match and both-agency coverage |
| **K5** |UNVERIFIED | **GOVERNANCE_DECISION_REQUIRED** |Known ratio gives a false leaf; unquantified UNKNOWN; denominator-basis discrepancy is separate | No clearance from ratio. Scope/positive evidence or approved negative contract required |
| `financials.adjusted_metrics_unreconciled` / unreconciled_metrics |absent /UNKNOWN | **GOVERNANCE_DECISION_REQUIRED** |450–453 actual Ind AS / non-GAAP bridges found; no complete-field assessment/candidate/EV | Review all relevant adjusted metrics, not just EBITDA; retained evidence improves assessment but does not prove universal reconciliation |
| `business.regulatory_dependence` / penalty |null /UNKNOWN | **GOVERNANCE_DECISION_REQUIRED** |Regulatory chapters 235–248 and risk page 51 discuss spectrum/authorisations; no accepted scalar assessment | Specific single-licence/price-control exposure test with scope/rationale; no “regulated telecom implies true” shortcut |
| Industry CAGR value+scope+period+source (`business.industry_cagr_pct`, `business.industry_scope`, `business.industry_forecast_period`, `business.industry_source`) |Four nulls /industry_growthUNKNOWN | **SOURCE_VALUE_FOUND** (candidate forecast); **GOVERNANCE_DECISION_REQUIRED** |165: 18.90% Q1FY2027–FY2031 fixed-broadband customer CAGR, Analysys Mason; not automatically whole-industry revenue CAGR. 152–153 GDP forecasts are ineligible industry substitutes | Retained segment forecast available; choose applicable issuer industry/metric under existing governance with exact attribution, or external applicable forecast |
| `business.moat_rating` / moat; `business.visibility_rating` / visibility |null /UNKNOWN | **GOVERNANCE_DECISION_REQUIRED** |No attributed assessment in target; product/customer/network facts are inputs, not rating | Authorized analyst evidence/rationale; do not invent deterministic high/strong assessment from prospectus marketing |
| Second multiple / EV/EBITDA or P/B |UNKNOWN | **QUALIFIED_EXTERNAL_EVIDENCE_REQUIRED** |126 peer P/Es retained; target peer EV/PB null; issuer amounts alone cannot make a peer comparison | Comparable issuer/peer financial periods, enterprise value/EBITDA or book value and market date, method/source; no PE reuse |
| `recent_sector_ipos` / sector_ipo_relative |absent /UNKNOWN | **QUALIFIED_EXTERNAL_EVIDENCE_REQUIRED** |No qualifying recent-sector comparables in target/source registry | Applicable same-sector dated IPO comparables/window with provenance; not a fresh unsupported numeric array |
| `market.anchor` / anchor_quality |MISSING /UNKNOWN | **QUALIFIED_EXTERNAL_EVIDENCE_REQUIRED** |Retained 18-page anchor OCR candidate exists but is unverified/not populated; no accepted quality assessment | Original official allocation member hash, issuer, date, table and governed quality mapping; availability/cutoff and freshness; provider/authoritative bytes |
| `market.subscription` / QIB and retail/NII |MISSING /UNKNOWN | **QUALIFIED_EXTERNAL_EVIDENCE_REQUIRED** |No observations in target; filing quota/reservations are not actual subscription | Official exchange eligible category time series / close observation as required; timestamp/timezone/cutoff and QIB/retail/NII match. At target time issue had not yet reached closing evening; do not backfill later-close facts |
| `market.gmp` / gmp_trend / **A9** |MISSING /UNKNOWN /withheld | **QUALIFIED_EXTERNAL_EVIDENCE_REQUIRED**; **GOVERNANCE_DECISION_REQUIRED** for accepting contract |No Jio observation in target; other retained publisher investigations are for Tonbo, not Jio. Generic digest is not qualification; no present qualified-Final accepting branch | Attributable selected Jio observation, time semantics/offset, original version, capture/cutoff, dispute/revision/withdrawal/independence review, plus scoped qualification/hash subject and a separately authorized verifier; no gate change here |
| `market.regime` / market_regime |MISSING /UNKNOWN | **QUALIFIED_EXTERNAL_EVIDENCE_REQUIRED** |No target NIFTY observation; retained other-IPO/index research is not automatic input | A8-M NIFTY 50 price-index completed-session closes / full SMA windows, availability/session cutoff, freshness and producer qualification; policy authorization ≠ implementation |
| Original ExtractionReport / page_routing / candidate conflicts / private map / target ingestion ID |Not in recovered records | **EVIDENCE_UNAVAILABLE** |Reachable-text/history search did not recover it; earlier native events concern a different incident; archive access blocked | Minimal Windows activity + original debug/backup bundle in section 8; do not rerun to manufacture historical records |
| Target loaded source revision |UNVERIFIED | **EVIDENCE_UNAVAILABLE** |No target-correlated build/deployment identity; matching versions/config insufficient | Historical process/source fingerprint + activity correlation, not current HEAD alone |

Raw field names for business assessments are confirmed against the frozen object below.

Frozen business object (read-only verbatim JSON; no inferred assessments):
```json
{
  "industry_cagr_pct": null,
  "industry_forecast_period": null,
  "industry_scope": null,
  "industry_source": null,
  "moat_rating": null,
  "regulatory_dependence": null,
  "top5_customer_pct": null,
  "top5_supplier_pct": null,
  "visibility_rating": null
}
```

### 6.1 Safety evidence coverage: five-way classification

| Gate leaf | Positive condition evidence | Explicit negative evidence | Coverage / no consumer evidence | Governing result |
|---|---|---|---|---|
| Going concern /K1 |No positive uncertainty located in report 321–324; 253 scheme “going concern” is not uncertainty |No sufficiently scoped negative uncertainty statement; unqualified opinion is not a negative |No EV/candidate in target; underlying reports beyond incorporated examination have not been independently acquired |A19 retains UNKNOWN. No authorized negative-confirmation rule |
| SEBI/ED /K2 |470: positive pending SEBI revision against promoter; resolved cases also found |487: specific SEBI debarment denial; 473: KMP/SM regulatory Nil subsets |No target EV; ED and complete agency/party/time/status coverage missing. Not safe to assume all pending agency matters equivalent under active-action definition |A23/A25 scope and status review required; neither denial nor historical penalty alone clears/triggers target |
| Unquantified /K5 |472: positive unquantifiability of promoter arbitration, not Note 37 issuer section |No explicit complete negative in 405 |No target flag EV; defined-note absence ≠ globally quantified |A20 positive-only same-section contract intentionally UNKNOWN; scope extension is governance,notad-hocparsercatchall |

This distinguishes actual source evidence from what reached the consumer. For SEBI/ED the new pending-case observation is material: it deserves immediate adjudication rather than another generic “no evidence” label. No authoritative agency/docket response was obtained in this pass; the filing's report of a case is not independent current status confirmation.

## 7. Findings separated by evidentiary class

**Historically proven retained-state/association failures:** source debt object 275,000 absent from normalized schedule; pre-holding 66.43 and explicit tenure/no-EOM evidence absent from target; quantified contingent/opinion source EVs present but absent from canonical external field associations. Source/consumer discrepancy is proved, the exact unlogged internal step is not.

**Reproducible source-code defects/coverage limits at pinned source:** Objects ISSUE/OFFER route mismatch; debt wording mismatch; narrow auditor name/tenure expressions and report-span exclusion of430; ID-convention mismatch after private-map loss; first-candidate-value/last-candidate-map asymmetry (potential, not observed collision); KMP default 0 without emitted count; flat/nested market mismatch (no new target-causal proof). No application function or test was executed to produce these conclusions; source/text inspection only.

**Source nondisclosure now demonstrated:** GCP actual amount deferred on116/122; post-promoter percentage deferred on104/109–110. These are scoped to this exact filing, not all later offer documents. No numeric zero/legal limit/residual/dilution replacement is justified.

**Governance decisions, not simple extraction failures:** top-seven vendor/capex → top-five supplier mapping, net-worth basis, EOM/CARO materiality, KMP count scope, compound auditor/CFO exit coverage, complete adjusted-metric assessment, regulatory dependence, industry selection, positive-only safety negative confirmation, SEBI pending-promoter-case scope/status, A9 qualification/accepting contract.

**Unavailable evidence:** exact target raw extraction, original map, routing/provider responses, target ingestion correlation and contemporaneous loaded-code identity. Reachable repository evidence is exhausted within the stated scope; restricted-host artifact archives and Windows source are explicit uninspected boundaries, not “proven not to exist.”

## 8. Exact minimal additional Windows/archived evidence

Do not export the whole machine, credentials, new evaluations or a newly fabricated “original” map. A read-only export of the following existing items is sufficient to test the remaining historical paths:

1. **One matching durable ingestion-activity JSON for L**, selected by terminal `evaluation_id=JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794`, and P only if comparing execution revisions. Candidate source store follows the inspected service: `G:\ipo-screening-engine\ipo-screening-engine\build\ingestion-activity` (sibling to the exported `build\evaluations`; this is a code-derived location, **not a directory whose existence was accessed**). Preserve `ingestion_id`, `correlation_id`, original started/finished/event timestamps, source hash, term candidates/rejections and final evaluation linkage. Search event timestamps near **05:16:22–05:18:17Z Oct 23** and **10:17:26–10:19:14Z Oct 22** only as narrowing hints; start can precede filing retrieval. Hash-prefix staging directory is not the ingestion ID.
2. **Only if already retained:** original debug/trace/cache/backup containing the `(canonical_dict, ExtractionReport)` from that ingestion: ordered RawExtraction objects (field_path, candidate_value, unit, page, locator, verbatim quote vs processing note, confidence, unknown flag), `metadata.page_routing`, source text-read errors, builder reference/base and `_sources`/`_evidence` **before** stripping, plus any post-term-assembly canonical dictionary. Limit to investigated fields and required container dependencies; preserve ordering and hashes. If absent, explicitly attest “not retained”; a new extraction cannot reconstruct the historical candidate list. The inspected service does not itself persist the full report, so this request may close as **unrecoverable** rather than demand a rerun.
3. **Target-correlated historical launch/build evidence:** original server startup/launcher log or process/backup manifest giving executable/interpreter, application module root/installed distribution, commit/tree and dirty-patch/file hashes **at execution**, configuration/environment switches (redacted, only policy-relevant flags) and correlation with the activity/time. Relevant source fingerprints: extractor/toc/sections/financial_tables/builder/interfaces, presentation/service, canonical_input/evaluation/evaluation_record, config and dependency lock/version manifest. Current `git rev-parse HEAD`/status can be supplied as **current-only context**, never treated as original process identity. If no contemporaneous/backup link exists, retain UNVERIFIABLE.
4. **Conditional archive export, not broad provider re-fetch:** if any listed GitHub artifact or Windows debug source registry actually contains target-correlated original provider payloads/field maps, export just those existing bytes and original timestamps/metadata to an allowed GitHub evidence location. The oldest/October 21 APIs already identified are not substitutes. GMP/market source qualification still requires the separate authoritative evidence contract; a stored hash alone never upgrades a source.

For each recovered file: original relative path, byte size, SHA-256, collection time, original mtime as metadata (not proof of event time), related ingestion/evaluation ID and a read-only export statement. **No need to re-export the9artifacts, alter their map, or submit the PDF again.** Authenticated historical runtime identity may remain impossible if those records were never captured; say that explicitly rather than fingerprint today's files as yesterday's code.

## 9. Next concrete execution sequence

1. **Recover history only:** read-only export matching ingestion activity and any already-retained intermediates/fingerprint (section8). This is the next concrete Windows action. No server restart, ingestion, scoring or pipeline run is needed.
2. **Adjudicate recovered source facts:** prioritize the pending SEBI promoter revision, K5scope/net-worth basis and KMP count; attach page 322/430auditor evidence,116 debt and GCP,104/109 post-holding. Classify source-deferred fields as unavailable *in this filing*, not development bugs.
3. **Prepare a separately authorized implementation proposal:** generic Objects heading/debt matching; auditor-name/tenure/EOMcoverage; durable provenance map and ID matching; candidate ordering consistency; unsupported default review. Tests/deployment/new evaluation need new authority. Do not change thresholds, weights or historical records.
4. **Acquire qualified external/assessment evidence:** later actual allocations/postholding; applicable peers/industry/analyst assessments; official market blocks and scoped GMP qualification. Keep independent issue-term PA authority separate from market admission.
5. **Only after explicit later authorization:** implement/test/deploy eligible changes and create a *new* immutable evaluation. Missing safety/A9conditions remain vetoes until legitimately resolved; no scoretargeting.

### Scope and publication integrity

Only this follow-up Markdown report is added to the Arena branch. Existing application, rules, fixtures, source PDFs, normalized artifacts, published evidence and prior report remain unchanged. Scratch searches/download attempts/PDF text live outside the repository. No application ingestion/extraction/builder/evaluation/scoring, tests, provider calls, Windows filesystem access, server operation, outcome change or merge into main occurred. The isolated PDF-library installation/page-text reading was document inspection, not an application pipeline execution. GitHub repository/API reads and authorized report-only publication are the only remote operations performed deliberately.

## Appendix A. Enumerated branch tips searched

No remote tags were returned. Every branch below was fetched into remote-tracking refs for object inspection, not checked out.

| Branch | Observed tip |
|---|---|
| `arena/01a10abc-ipo-screening-engine` | `25627497658904caf3e021091c1831a844a70ce2` |
| `arena/01a10b42-ipo-screening-engine` | `4b19faf848a721265597a678926988d484d30e59` |
| `arena/07f3439f-ipo-screening-engine` | `18d0eb91549ba14534c750b2305ec3147be02c6f` |
| `arena/42628121-ipo-screening-engine` | `e05c0efbca1ecb3024e52da73a22e180ea171118` |
| `arena/4e1080b7-ipo-screening-engine` | `adbd93c5b4450fb113561368d7d101eb4686c842` |
| `arena/573e69a4-ipo-screening-engine` | `6f54b3722532c2153e07d9a2cea59696fdd11def` |
| `arena/5ccbfd5d-ipo-screening-engine` | `c3d05a165ee1f607771c3291a342c4da060d89ea` |
| `arena/5dd3fe52-ipo-screening-engine` | `e05c0efbca1ecb3024e52da73a22e180ea171118` |
| `arena/95234306-ipo-screening-engine` | `e8f9a28219aab69673c74e3b049729b77f1dfef5` |
| `arena/ae4d04e8-ipo-screening-engine` | `9b09526c2fd089609b7ebabbeaf26d488631c1a3` |
| `arena/ba8f663e-ipo-screening-engine` | `6ecd26c821ac6e859481a1f2f3fb06b46265bb6f` |
| `arena/c2d9b0bd-ipo-screening-engine` | `9e074ec8200871afab2121102ba7421b568c4c05` |
| `arena/d15866b5-ipo-screening-engine` | `e1df89b2af3bd432a70fe9716e266895ba6ff2e7` |
| `arena/ea6e5bc2-ipo-screening-engine` | `bbe445a34196b93c98e9fa018888eb1536151f02` |
| `arena/gmp-evidence-linkage-docs-clean` | `4ab0ae30a5a4183a1a36ca676d9b41ae95fabee2` |
| `arena/gmp-evidence-linkage-impl-clean` | `c0577d85f268164c6dcccc74fa42125d3f2ba48b` |
| `arena/ipo-handoff-manifest-correction` | `6cb0891faaefbe1c129535fc44cc2ba8e11bc5f4` |
| `arena/ipo-screening-engine-v1.5` | `940ed701857538d10bf37ad53468d5a36d5952c8` |
| `evidence/jio-score-33-recovery-20261023` | `1dd6e14e7fa50a677beefba9ca7d0d1a7b322c58` |
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` |

## Appendix B. Stable source/evidence entry points

- [docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/input.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/input.json)

- [docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evidence.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evidence.json)

- [docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evaluation-record.v1.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evaluation-record.v1.json)

- [docs/investigation/aggregator-fallback-2026-10-22/native-accepted.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigation/aggregator-fallback-2026-10-22/native-accepted.json)

- [docs/investigation/jio-recovery/rhp-all-pages-inventory.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigation/jio-recovery/rhp-all-pages-inventory.json)

- [docs/investigation/jio-recovery/anchor-review.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigation/jio-recovery/anchor-review.json)

- [docs/investigation/runtime-verification-2026-10-20/tree-identity.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigation/runtime-verification-2026-10-20/tree-identity.json)

- [handoff/decisions/A19-k1-going-concern-positive-evidence.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A19-k1-going-concern-positive-evidence.md)

- [handoff/decisions/A20-k5-contingent-liability-numerator.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A20-k5-contingent-liability-numerator.md)

- [handoff/decisions/A21-promoter-post-issue-holding.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A21-promoter-post-issue-holding.md)

- [handoff/decisions/A22-auditor-tenure-and-repeated-eom.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A22-auditor-tenure-and-repeated-eom.md)

- [handoff/decisions/A23-litigation-regulatory-evidence-defaults.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A23-litigation-regulatory-evidence-defaults.md)

- [handoff/decisions/A24-litigation-party-coverage-standard.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A24-litigation-party-coverage-standard.md)

- [handoff/decisions/A25-sebi-ed-absence-source-coverage-standard.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A25-sebi-ed-absence-source-coverage-standard.md)

- [handoff/decisions/A26-tax-only-proceedings-classification.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A26-tax-only-proceedings-classification.md)

- [handoff/decisions/A27-auditor-bucket-unconsumed-clauses.md](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/handoff/decisions/A27-auditor-bucket-unconsumed-clauses.md)

## Appendix C. Reproduction boundary

Search procedure: enumerate refs → fetch remote heads/tags → enumerate reachable commits/objects → read every text blob through cat-file → search exact targetIDs/filinghash plus candidate paths → inspect positive-hit JSON/logs/source/history and manifest records → verify PDFSHA → read PDFpages directly → compare limited source expressions to page text → read frozen field values/EVrefs. No engine result was regenerated. Counts refer to the pre-follow-up search snapshot; a later report commit naturally increases reachable history. The82/27counts from the prior report are not rerun as substitutes for this recovery work; only field-specific stored associations were independently read here.
