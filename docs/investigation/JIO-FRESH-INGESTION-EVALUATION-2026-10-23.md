# Jio Platforms — fresh ingestion, evaluation and provenance reconciliation

**Status: completed diagnostic execution on a non-authoritative evidence path.** The filing was ingested again end-to-end by the supported service, a new evaluation was produced, demonstrated extraction/mapping defects were corrected and verified by re-ingestion, and every artifact is published with its generated identifiers.

This report does **not** alter the two historical evaluations, does not change scoring weights, criterion semantics, A9 qualification policy or any safety-gate rule, and does **not** claim a terminal Final outcome.

---

## 1. Executive result

| Item | Value |
|---|---|
| Source PDF | `evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf` |
| PDF SHA-256 (verified before ingestion) | `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d` |
| Executing source revision | `514ca599d3982bc160319793ef2f7f06d046fd27` (integrated baseline `0d896040`, defect corrections `417a586f`, completed OFS correction included) |
| New ingestion ID | `ing-4c38b470edb24db4` |
| New evaluation ID | `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601` |
| Result hash | `29d9a601b94248c58df8f43608a8ca517b870ee8ec0a0e7c70d6be7732d43d62` |
| Score / interval | **34.0 / 100**, interval **24–77** |
| Available / unknown points | 57 / 43 |
| Completeness | 57% |
| Confidence | Low |
| Mode | FINAL (authority warning: third-party issue terms) |
| Verdict | `INSUFFICIENT_DATA` (score band AVOID; interval crosses bands) |
| A9 | `NONTERMINAL_UNRESOLVED` — qualifying GMP evidence absent |
| K1 | `UNVERIFIED` — `going_concern_uncertainty` unknown |
| K2 | `UNVERIFIED` — `sebi_ed_action_active` unknown |
| K5 | `UNVERIFIED` — `contingent_liab_unquantified` unknown |
| K3, K4, K6 | `CLEAR` |

**The score is not a reproduction of 33/100.** It is the output of the current implementation on newly ingested data. The +1 net movement has two identified components: Module D `auditor` 0 → 2 (explicitly evidenced auditor continuity and standing now extracted) and Module D `board_kmp` 1 → 0 (the unsupported zero KMP-exit default is gone; the field is honestly UNKNOWN).

Two independent intake attempts were made before the successful one. The first (live official discovery) failed closed with `AWAITING_ISSUE_TERMS`; the second used the already-authorized PA aggregator opt-in path with **retained publisher bytes**, never fabricated values. Both are published as diagnostic evidence.

---

## 2. Execution baseline

### 2.1 Implementation branch and revision

| Role | Commit | Content |
|---|---|---|
| Prior published report | `d9012a2f570887ab1809e1f634dd7a78d67eecb7` | Parent of this work on `arena/07f3439f-ipo-screening-engine` |
| Integrated baseline | `0d896040adc5e1484fd4835e362f459105ec07ad` | Completed ingestion fixes from `origin/arena/95234306-ipo-screening-engine` integrated into the current implementation, **with the A9 explicit-only GMP safeguard retained** (see §2.3) |
| Defect corrections | `417a586f8985b9b7e582a57dfa88de367a03f6af` | Nine corrections demonstrated by the baseline run (§8) |
| Executing revision | `514ca599d3982bc160319793ef2f7f06d046fd27` | Adds the completed OFS-NIL binding correction (`54b3447`, wrapped `OFFER FOR / SALE SIZE` labels) |
| Validated revision | `36086944a2c321d2613af28972fd887af9f25f8c` | Adds the corrected regression expectations; engine bytes identical to the executing revision |

These three commits are **local integration objects**, not a fork of this branch's engine: they are reconstructible byte-for-byte from remote refs plus the published patch. See `docs/investigation/jio-fresh-20261023/source-lineage/LINEAGE.md`; the reconstruction was executed and verified against every engine/test file hash (`executed-source-sha256.txt`). The branch engine is deliberately not overwritten, because the Arena line and the evidence line carry different A9 implementations (for example `gmp_binding.py` exists only on the Arena line).

`main` was not touched. The historical evaluations were not opened for writing, and no store directory outside this report's own artifact path was used.

### 2.2 What was verified as "the latest fixes"

The completed ingestion fixes exist on `origin/arena/95234306-ipo-screening-engine` (e.g. `ba7a069` aggregator assertions, `75df573` accepted live evaluation, `54b3447`/`e8f9a28` OFS NIL split-header correction) and were **not** present in the published report branch tree. `git diff origin/evidence/jio-score-33-recovery-20261023 origin/arena/95234306-ipo-screening-engine -- engine` is confined to `extraction/sections.py`, so the integration is small and auditable.

**Deliberate exception (A9).** The peer branch converts the second GMP snapshot into a hard `ConflictingSourceError`. That is an A9 contract change: A9's standing direction in this session is explicit-only/optional/delegated, and a duplicate-list rule is not a qualification rule. The A9 files from the current branch (`gmp_evidence.py`, `gmp_binding.py`, `gmp_policy.py`, their tests and schema) were therefore **retained**, and only ingestion-path files were integrated. This is recorded as a scope decision, not an oversight.

### 2.3 Runtime identity

| Item | Value |
|---|---|
| Interpreter | CPython 3.11.2, Linux 6.1.158+ (`jio-env` virtualenv) |
| Engine / spec / config version | 1.5.0 / 1.5 / 1.5.0 |
| Config SHA-256 | `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b` |
| Dependency pin set | `docs/investigation/jio-fresh-20261023/dependencies.txt` |
| Source fingerprints | `final-retained/runtime.json` (`source_fingerprints`, per-file SHA-256 of every engine module) |
| Working-tree execution | Executed from an extracted tree of the executing commit, not from the local dirty checkout |

The runtime identity above authenticates **this** execution. It does not retroactively authenticate the historical Windows runtime; that remains outside this report's scope and unchanged.

### 2.4 Entry point and persistence

`PresentationService.ingest_document` → `DocumentExtractor.extract_from_pdf` → `CanonicalInputBuilder.build` → issue-term resolution → `evaluate` → `EvaluationStore` (immutable, exclusive-create artifacts). The observation harness (`run_fresh.py`) only *wraps* those functions (`extract_from_pdf`, `CanonicalInputBuilder.build`, the module-level `evaluate`) to record their real inputs and outputs. It never injects a canonical input, a candidate, a score, or a market block.

Store roots were redirected to `docs/investigation/jio-fresh-20261023/<run>/evaluations`, so no historical artifact could be overwritten.

---

## 3. Execution sequence and the two intake attempts

### 3.1 Attempt 1 — live official discovery (fail-closed, correct)

`ing-1c55b52a23574673` → `IngestionAwaitingIssueTermsError`.

Transport was attempted live and every official endpoint was refused at the network boundary of this sandbox:

| URL | Result |
|---|---|
| `https://www.nseindia.com/market-data/all-upcoming-issues-ipo` | `URLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF)'))` |
| `https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P` | same TLS/SSL EOF |
| `https://www.bseindia.com/publicissue.html` | same |
| `https://api.bseindia.com/BseIndiaAPI/api/GetPublicIssue_par_updated/w?flag=1` | same |
| `https://www.nseindia.com/api/all-upcoming-issues?category=ipo` | same |

Exact rows: `initial-live/source-transport.json`. The runtime refused to assume terms, produced no evaluation, and persisted nothing. This is the correct fail-closed behaviour and is **not** evidence that the terms are unpublished.

### 3.2 Attempt 2/3 — PA-authorized aggregator path over retained publisher bytes

The supported opt-in path (`THIRD_PARTY_AGGREGATOR_OVERRIDE`, policy `pa-aggregator-issue-terms-v1`) was exercised. This sandbox cannot reach the publishers, so the **already-retained publisher response bytes** from the accepted 2026-10-21 run were re-parsed, with an integrity check before use:

* Container: `docs/investigation/aggregator-fallback-2026-10-22/native-accepted.json`, entry `aggregator_source_bytes` whose `sha256` equals the persisted source `47293a7fa3a645e55f474c6d0b243912126ec6e7f1ba5bd9affa4d44d73f25fe`.
* Decompressed bytes re-hashed = `47293a7f…25fe` (matches); written to `final-retained/retained-publisher.html`.
* Original retrieval timestamp `2026-10-21T20:19:43.817744Z` is carried on the source and echoed in `retained-source-receipt.json`.

What this is: a genuine fresh ingestion of the PDF with **new** issue-term resolution, a **new** ingestion ID, **new** evaluation ID, and current implementation. What it is **not**: a live HTTP fetch in this sandbox, an official disclosure, or a GMP observation. The four issue terms remain tagged `UNVERIFIED` / `THIRD_PARTY_AGGREGATOR_OVERRIDE`, and every consumer message repeats that authority warning.

No GMP, anchor, subscription or regime value is supplied by this path.

---

## 4. Document disclosures — verified end-to-end in the fresh run

Path notation: **page → candidate → evidence ID → canonical field → consumer state**.

### A. Use of proceeds

| Element | Result |
|---|---|
| Source | Page 116, Objects of the Offer, schedule row 1: “Prepayment, in full or in part, of certain outstanding borrowings availed by the Material Subsidiary, RJIL 275,000 275,000” |
| Candidate | `use_of_proceeds` = `[{debt_repayment: 275000.0}, {gcp: null, undisclosed_marker: "[●]"}]`; leaf `use_of_proceeds[0].amount` = `275000.0` (page 116) |
| Evidence | `EV-use_of_proceeds_0-amount`, `EV-use_of_proceeds_1-amount` (verbatim row quotes); container `EV-use_of_proceeds` |
| Canonical | `use_of_proceeds[0].amount = 275000.0` INR million; `use_of_proceeds[1]` amount `null` with marker `[●]` |
| Consumer | `C.use_of_proceeds` → **UNKNOWN**. Reason: the `blind_heavy` test needs a GCP/unidentified-acquisition amount; a placeholder is not zero and no legal maximum is substituted |

Debt prepayment is now extracted with the right amount and unit and points at page 116. GCP correctly remains unknown. **The score cannot move on this criterion**; that is the intended fail-closed behaviour, not a remaining extraction bug.

### B. Promoter holding

| Element | Result |
|---|---|
| Source | Page 104: RIL row `5,937,841,645 | 66.43 | 5,937,841,645 | [●]`; pages 109–110: post-issue percentages remain `[●]` |
| Candidate | `capital_structure.promoter_pre_pct = 66.43` (page 104, verbatim row quote) |
| Evidence | `EV-capital_structure-promoter_pre_pct` |
| Canonical | `promoter_pre_pct = 66.43`; `promoter_post_pct = null` |
| Consumer | `D.promoter_post_holding` → **UNKNOWN** (“post-issue promoter holding is not disclosed”) |

No post-issue dilution was derived from the pre-issue percentage; the post field has no candidate and no evidence.

### C. Auditor and governance

| Field | Page | Candidate | Evidence | Canonical | Consumer |
|---|---|---|---|---|---|
| `auditor_opinion` | 324 | `unqualified` | `EV-governance-auditor_opinion` | `unqualified` | `D.auditor` → SCORED 2.0 (`clean_reputed`) |
| `auditor_changed_3y` | 322 | `false` — joint reports dated 2026/2025/2024 for FY2026/25/24 | `EV-governance-auditor_changed_3y` | `false` | as above |
| `auditor_reputed` | 324 | `true` — Deloitte Haskins & Sells LLP; Chaturvedi & Shah LLP | `EV-governance-auditor_reputed` | `true` | as above |
| `repeated_eom` | 430 | `false` — “no Emphasis of matters in auditor’s report” for all five periods | `EV-governance-repeated_eom` | `false` | no scorer consumes it directly; see below |
| `kmp_exits_2y` | 312 | **no candidate** — the page records CEO and Company Secretary resignations only | — | `null` | `D.board_kmp` → **UNKNOWN** |

No CFO resignation was inferred from the CEO resignation, no absence of an exit was inferred from silence, and no governance flag was fabricated. The previously hard-coded `kmp_exits_2y = 0` default is gone (§8).

### D. Contingent liabilities and net worth

| Element | Result |
|---|---|
| Source | Page 405, Note 37: FY2026 (31 March 2026) claims `15,021`; commitments `26,198` excluded as commitments |
| Candidate | `financials.contingent_liabilities = 15021.0` INR million (page 405) |
| Evidence | `EV-financials-contingent_liabilities` |
| Canonical | `contingent_liabilities = 15021.0`; `contingent_liabilities_unquantified = null` |
| Consumer | K5 **UNVERIFIED**; module penalty state UNKNOWN |

Net worth: page 329/406 owners’ equity `3,359,769` is the value in `financials.periods[2].net_worth` (period container evidence `EV-financials-periods`); page 451/487 defines statutory Net Worth as `3,340,134`. The existing methodology is unchanged. Choosing between the owner-equity basis and the ICDR-defined Net Worth basis is a **governance decision**; this pass did not silently swap the denominator, and it records that the K5 ratio therefore depends on a basis choice that is still open.

### E. Concentration

`business.top5_customer_pct` and `business.top5_supplier_pct` remain `null`, with no candidate and no evidence (`E.concentration` → UNKNOWN). Pages 44–45 disclose a top-**seven** network-vendor table plus related-party percentages, and a restricted capex denominator. Nothing in the current implementation promotes that disclosure to a top-five metric, and this pass added no such conversion. Eligibility is preserved: an ineligible metric cannot become a scored concentration input.

---

## 5. Market evidence and safety gates (unchanged by design)

| Block | State | Reason |
|---|---|---|
| anchor | MISSING | block not supplied |
| subscription | MISSING | block not supplied |
| gmp | MISSING | block not supplied |
| regime | MISSING | block not supplied |

* **A9** stays `NONTERMINAL_UNRESOLVED`: “A9 requires a qualifying GMP snapshot and its required hash for FINAL … The generic market-snapshot digest is a local digest over all market blocks, not a GMP qualification hash. FINAL is withheld.”
* **K1** retains `UNVERIFIED` on `going_concern_uncertainty`; an unqualified opinion is not a negative confirmation.
* **K2** retains `UNVERIFIED` on `sebi_ed_action_active`; the pending promoter matter in the filing was not adjudicated here.
* **K5** retains `UNVERIFIED` on `contingent_liabilities_unquantified`; no positive unquantified disclosure exists in the defined note.

No market value was invented, no gate was cleared by keyword absence, and the `INSUFFICIENT_DATA` verdict follows from the existing policy rather than from this pass.

---

## 6. New evaluation record

| Field | Value |
|---|---|
| Evaluation ID | `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601` |
| Ingestion / correlation ID | `ing-4c38b470edb24db4` |
| Input snapshot hash | `ba27fc4b99e3ac6ad28ec065e788d7beb57cfb8b9f1fc71e09b3839b93a8f04f` |
| Source manifest hash | `e439b9462bfc707587a348cd576dd39f7a25a87b50854defa09cf21d6f54b915` |
| Market snapshot hash | `f17cf31d29b7d79a207be85d91034e4842e0b418e1b75a3cff919edc234b382a` |
| Peer snapshot hash | `61f5c9132e97baf987f2693568ab5b4b5ec748136b05453f0e2d155b842edb9b` |
| Result hash | `29d9a601b94248c58df8f43608a8ca517b870ee8ec0a0e7c70d6be7732d43d62` |
| Missing / unverified entries | 27, as reported in the API evaluation response; the A15 projection expresses the same gaps through criterion state and `field_values` rows (it does not duplicate the list) |
| Penalties applied | 0 |

Module scores: A 17/25, B 1/20, C 11/15, D 5/15, E 0/15, F 0/10.

Criterion outcomes that moved relative to the pre-fix run of this pass:

| Criterion | Before | After | Cause |
|---|---|---|---|
| `D.auditor` | UNKNOWN, 0 | SCORED 2.0, `clean_reputed` | auditor identity, three-year continuity and explicit no-EOM now extracted with page-anchored evidence |
| `D.board_kmp` | SCORED 1.0, `other` | UNKNOWN, 0 | unsupported `kmp_exits_2y = 0` default removed; the filing discloses exits but not a governed count |

All other criteria, the 43 unknown points, the 57% completeness and the gate states are unchanged from the reproduced baseline.

---

## 7. Provenance and association results

The fresh run proves the following about the current implementation, with artifacts:

* **Field map is persisted.** `evidence.json` now carries `field_map` (48 entries) alongside the 48 evidence objects and 2 sources (filing + retained publisher). No `field_map` entry points at a non-existent evidence ID.
* **Explicit associations survive projection.** In `evaluation-record.v1.json`, `field_values` rows now reference the real evidence IDs: `/input/use_of_proceeds/0/amount → EV-use_of_proceeds_0-amount`, `/input/governance/auditor_opinion → EV-governance-auditor_opinion`, `/input/governance/repeated_eom → EV-governance-repeated_eom`, `/input/financials/contingent_liabilities → EV-financials-contingent_liabilities`, `/input/capital_structure/promoter_pre_pct → EV-capital_structure-promoter_pre_pct`.
* **Unknown fields carry no false evidence.** `/input/capital_structure/promoter_post_pct` and `/input/governance/going_concern_uncertainty` reference only their local-input rows, which is correct for a value that does not exist in the source.
* **First-value/evidence agreement.** Where duplicate candidates exist, the builder's first-candidate selection and the evidence block now describe the same candidate; the observation wrapper records the ordered candidates (`builder-stages.json`) so the choice is auditable.
* **Field-map loss warning is now conditional.** `LEGACY_FIELD_EVIDENCE_MAPPING_INCOMPLETE` is only raised when no explicit map is present.

The distinction between *proven source fact*, *reproducible code defect* and *unproven historical causation* from the prior investigation is preserved: this run demonstrates what the current implementation does on this document. It does not retroactively prove what the October 22/23 Windows runs executed.

---

## 8. Corrections made, with exact files

All corrections are within existing implementation authority: they make the extractor read evidence that is actually printed, stop an unsupported default, and preserve associations the pipeline already computes. No weight, semantic, policy or gate rule changed.

| # | File | Defect demonstrated by the fresh run | Correction |
|---|---|---|---|
| 1 | `engine/ipo_screening/extraction/toc.py` | The filing's `OBJECTS OF THE ISSUE` heading was not recognised (`Objects of the Offer` only); `OUR MANAGEMENT` was not recognised in the `THE MANAGEMENT` form | Accept the ISSUE form and the definite-article form |
| 2 | `engine/ipo_screening/extraction/sections.py` | Debt row “Prepayment, in full or in part…” matched no proceeds pattern; the schedule emitted only `gcp` | Added the wording alternative; records each category's own page |
| 3 | `engine/ipo_screening/extraction/sections.py` | The proceeds container was stamped with the GCP page (120) rather than the section page | Container page now derives from the actual matched rows (116) |
| 4 | `engine/ipo_screening/extraction/sections.py` | Only the container was emitted, so no leaf had a page-anchored quote | Emit `use_of_proceeds[i].amount` with the verbatim row text |
| 5 | `engine/ipo_screening/extraction/sections.py` | Pre-issue promoter percentage was `null` for the sole-promoter table | Detect the named sole-promoter row (identical pre/post share counts, post `[●]`) and record the raw row as quote |
| 6 | `engine/ipo_screening/extraction/sections.py` | Auditors were unnamed when the signature is not on the opinion page; the joint three-year report wording matched no tenure expression; no-EOM on page 430 lay outside the selected report span | Read signed `For … LLP` lines in the report span; accept the joint-report tenure sentence; explicit no-EOM is searched in the report span with page-anchored quoting |
| 7 | `engine/ipo_screening/extraction/builder.py` | Evidence and value could disagree when a path had duplicate candidates (`last` overwrote `first`) | `setdefault` keeps evidence aligned with the first candidate actually used |
| 8 | `engine/ipo_screening/extraction/builder.py` | `kmp_exits_2y` defaulted to `0` with no disclosed count | Default removed; absence is `null` → criterion UNKNOWN |
| 9 | `engine/ipo_screening/pipeline.py` | The canonical field→evidence map was computed and then discarded before the evidence block | Emit it as `evidence["field_map"]` |
| 10 | `engine/ipo_screening/evaluation_record.py` | A15 projection guessed IDs by replacing `.` with `-`, so declared IDs were lost; the “incomplete mapping” finding was unconditional | Prefer the explicit map, fall back to the legacy convention; warn only when no map exists |
| 11 | `engine/ipo_screening/extraction/sections.py` | Completed OFS-NIL correction (`54b3447`) covering reader-wrapped `OFFER FOR / SALE SIZE` and wrapped competing labels | Applied verbatim from the completed fix |

Authoritative confirmation of the debt, auditor and EOM wording is in `final-retained/extraction-report.json` and `final-retained/source-page-contexts.json` (pages 5, 44, 45, 93, 94, 104, 109, 116, 117, 122, 312, 322, 324, 405, 430, 451, 487).

### Behavior change is measured, not assumed

The same harness was executed before and after: `initial-retained` (33.0, `…final-4220b641`) and `final-retained` (34.0, `…final-29d9a601`). The three pre-fix artifacts (extraction report, canonical map, builder stages) remain published so the before/after difference is auditable rather than asserted.

---

## 9. Tests executed

| Run | Scope | Result |
|---|---|---|
| Baseline integration | auditor tenure, contingent liabilities, GMP safeguards/binding/linkage, aggregator terms, worker lifecycle | 209 passed, 1 failed — the failure was a **missing checked-in evidence file** (`evidence/gmp-observations/targeted-followup-20261022/source-captures/pd-unavailable.md`), not a code defect; the file exists in the workspace and was restored for later runs |
| After corrections | the above plus evaluation-record v1, financial column mapping, governance contract audit, going-concern disclosure and the new real-filing regressions | **282 passed**, 1 warning |
| New real-filing regressions | see below | **7 passed** |
| Full suite (final revision) | every test except one cross-branch file | **1663 passed, 0 failed** in 18m44s (`source-lineage/tests-final.log`) |

Eight pre-existing expectations encoded the old behaviour and were updated **with the reason stated inline**, after each failure was traced to an intended consequence rather than an unexplained drift:

| Test | Old expectation | New expectation | Cause |
|---|---|---|---|
| `tests/test_extraction.py::test_section_extractor_objects_of_offer_fail_closed_gcp` | exactly 1 proceeds extraction | 4 (container + 3 page-anchored rows); GCP leaf still `None` | correction #4 now emits one candidate per disclosed allocation row |
| `tests/test_promoter_holding_extraction.py::test_live_jio_shareholding_pattern_is_not_fabricated` | Jio pre-issue `None` | `66.43`, post still `None`, no 100 % | correction #5 reads the printed sole-promoter row; the old assertion contradicted the filing's own disclosure |
| `tests/test_extraction_phase5b.py` (classes B, C, E) | 37/37/39 | 36/36/38 | correction #8 removes the unsupported `kmp_exits_2y = 0` default |
| `tests/test_rk_fashion_reconciliation.py` | 45, base 48, completeness 69, bounds 32–76, module D 6/6 | 44, base 47, completeness 67, bounds 31–77, module D 5/8 | same default removal; the criterion becomes UNKNOWN and its 2 points move to unknown |
| `tests/test_ui7_ingestion.py` (two RK/synthetic end-to-end tests) | 19 / 45 | 18 / 44 (base 47, completeness 67) | same |

No weight, bucket boundary, knockout rule or market block changed; every updated number is a −1 score consequence (plus its availability accounting) of deleting a fabricated default. The same effect is visible in the Jio result: `D.board_kmp` 1.0 → UNKNOWN while `D.auditor` rose 0 → 2.

New `tests/test_jio_fresh_regressions.py` asserts, against the actual PDF:

1. `OBJECTS OF THE ISSUE` routes page 116;
2. debt `275000.0` is extracted on page 116 with the verbatim quote, and GCP stays `null` with `[●]`;
3. pre-issue `66.43` is captured from page 104 and **no** post-issue candidate is invented;
4. auditor continuity is `False` from page 322, standing `True`, no-EOM `False` from page 430, and no going-concern field is invented;
5. builder default for `kmp_exits_2y` is `None`;
6. first-candidate value and evidence quote agree;
7. an explicitly declared non-generated evidence ID survives projection.

`tests/test_ofs_nil_binding.py` and its fixture are included with the completed OFS correction. `tests/test_jio_rhp_issue_terms.py` from the peer branch was **excluded**: it depends on prospectus-pathway code that is not part of this branch, and publishing a failing test would misrepresent the verified state.

No test writes to a historical store; store roots are temporary or this report's directory.

---

## 10. Comparison with the historical evaluations

| | Historical `…20261023-051816Z-final-b79b5794` | Historical `…20261022-101913Z-final-ad5e6872` | Before-fix baseline (`…final-4220b641`) | New (`…final-29d9a601`) |
|---|---|---|---|---|
| Score | 33.0 | 33.0 | 33.0 | **34.0** |
| Interval | 23–76 | 23–76 | 23–76 | **24–77** |
| Unknown points | 43 | 43 | 43 | 43 |
| Missing/unverified entries | 27 | 27 | 27 | 27 |
| A9 | withheld | withheld | withheld | withheld |
| K1/K2/K5 | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| Market blocks | 4 MISSING | 4 MISSING | 4 MISSING | 4 MISSING |

Both historical records were left untouched; their identifiers and hashes are unchanged by this pass.

**Every material difference, attributed:**

* **+1 net score.** `D.auditor` 0 → 2 is caused by implementation change #6 (and #2/#5 for the surrounding evidence). `D.board_kmp` 1 → 0 is caused by implementation change #8. Both effects are visible in the before/after artifacts; neither touches a weight or bucket boundary.
* **Interval 23–76 → 24–77.** The bounds follow the base score; the unknown-point total is unchanged at 43, as are the four missing market blocks.
* **Newly populated extraction values (no score effect).** Debt prepayment `275000.0` (page 116), promoter pre-issue `66.43` (page 104), auditor identities and continuity (322/324), explicit no-EOM (430). `use_of_proceeds`, `promoter_post_holding` and `concentration` remain UNKNOWN **because the source itself does not disclose the required inputs**, not because extraction failed.
* **Unchanged criteria are unchanged for evidence reasons**, not for lack of attention: GCP placeholder, post-issue promoter placeholder, no top-five metric, no industry CAGR/scope, no moat/visibility assessment, no peer EV/EBITDA or P/B, no market observations.
* **Zero applied penalties** in all four records; 33 − 10 = 23 downside exposure remains an exposure statement, not a penalty.

The historical criterion-level detail is not retained in this repository, so the comparison against `b79b5794`/`ad5e6872` is aggregate (score, interval, unknown points, entry count, gate states). Criterion-level comparison is made against the reproduced pre-fix baseline from this pass and is labelled as such.

---

## 11. Remaining blockers and the next concrete action

1. **Live official issue terms from this sandbox** — blocked by egress (TLS/SSL EOF at NSE and BSE, listed in §3.1). The values used are the authorized third-party terms over retained bytes and are marked UNVERIFIED. *Next action:* run the same service on a host with official egress; the only expected difference is provenance of the four issue terms.
2. **A9 Final** — no qualifying GMP observation exists for this IPO. Withheld correctly. *Next action:* the separately authorized A9 intake produces a qualifying observation; no code change is proposed here.
3. **K1, K2, K5** — each needs either positive source evidence or an approved negative-confirmation rule, plus governance adjudication of the specific scope (going concern; SEBI/ED active-action definition; quantified-vs-unquantified contingent scope). Not cleared by absence.
4. **Net-worth basis** — owner equity `3,359,769` versus ICDR Net Worth `3,340,134`. The existing denominator is unchanged; a governance decision is required before any swap.
5. **Top-five concentration and industry CAGR/scope** — the filing does not supply metrics in the required definitions; derivation requires an approved methodology, not a parser change.
6. **Historical runtime authentication** — unchanged by this pass. The runtime identity here authenticates this execution only.

---

## 12. Published artifacts and reproduction boundary

Directory: `docs/investigation/jio-fresh-20261023/`

| Artifact | Content |
|---|---|
| `run_fresh.py` | The observation harness used; imports the real service |
| `dependencies.txt` | `pip freeze` of the execution environment |
| `initial-live/` | Attempt-1 failure, activity trace, extraction report, canonical map, transport log |
| `initial-retained/` | Pre-fix baseline: response, extraction report, canonical map, builder stages, aggregator resolution, evaluations store, retained bytes |
| `final-retained/` | Corrected run: same set plus source page contexts and the final evaluation store |
| `source-lineage/` | `LINEAGE.md`, `corrections.patch`, `executed-source-sha256.txt`, the new regression test, and the three test logs |
| `tests-final.log` | Full-suite output for the executing revision |

Key hashes: final `response.json` `76b46e9c…9adc4`, final `extraction-report.json` `e138d81f…5a84`, final `extracted-canonical-with-map.json` `ccfe8ec7…516c`, final `evaluation.json` `cf2a8b2c…0991`, retained publisher bytes `47293a7f…25fe` (= persisted source hash), harness `ac5e68e6…b8bb`.

Reproduction: `JIO_SOURCE_COMMIT=<executing commit> python docs/investigation/jio-fresh-20261023/run_fresh.py retained <dir>` from a tree of that commit. The run is deterministic apart from timestamps, ingestion ID and the resulting evaluation ID/time.

**Non-authoritative.** This is a diagnostic investigation path. It does not replace any authoritative evidence record, does not establish a Final outcome, and does not modify the two historical evaluations.
