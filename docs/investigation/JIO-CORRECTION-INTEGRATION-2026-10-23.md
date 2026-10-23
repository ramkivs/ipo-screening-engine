# Jio fresh-ingestion correction integration — 2026-10-23

**Status: integrated and validated on `arena/07f3439f-ipo-screening-engine`.** The eleven corrections demonstrated by the fresh Jio ingestion now execute in this branch's engine. The branch's A9 subsystem is retained **byte-for-byte unchanged**. No new evaluation was created, because the integrated engine is byte-identical to the engine that produced the published `…final-29d9a601` result.

This is a non-authoritative investigation path. It does not touch `main`, either historical Jio evaluation, or any scoring weight, criterion semantic, A9 rule or knockout rule.

---

## 1. Exact baseline

| Item | Value |
|---|---|
| Working branch | `arena/07f3439f-ipo-screening-engine` |
| Branch commit at start | `8a1a37022f00496dd22e67b51319a407f6daf6fb` (diagnostic publication) |
| Local checkout | branch content extracted to a clean tree; the local working copy's unrelated changes (`README.md`, untracked docs/engine of the pre-existing checkout) were **not** touched |
| Diagnostic ingestion | `ing-4c38b470edb24db4` |
| Diagnostic evaluation | `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601` — **34.0**, interval 24–77, `INSUFFICIENT_DATA`, A9 nonterminal |
| Correction patch | `docs/investigation/jio-fresh-20261023/source-lineage/corrections.patch` (29,225 bytes) |
| Patch provenance | `git diff 0d896040adc5e1484fd4835e362f459105ec07ad 36086944a2c321d2613af28972fd887af9f25f8c -- engine tests` |
| Patch destination engine | evidence-line tree `1dd6e14e` + retained A9 files, i.e. the tree the diagnostic run executed |
| Corrections' target here | the branch's own engine at `8a1a3702` |

The diagnostic commit contains the **reports, evidence and patch**, not the corrected engine code. Confirmed by applying the patch to a clean copy of the branch tree: only 4 of the 10 changed files accept all hunks, and **16 hunks are rejected** (`jio-correction-integration-20261023/patch-apply-to-branch.log`).

---

## 2. A9 reconciliation (first, as directed)

### 2.1 Code differences

`a9-divergence.json` records presence and SHA-256 per file on three trees: branch `d9012a2`, the implementation line `e8f9a28`, and the integrated tree.

| A9 asset | Branch | Implementation line | Integrated |
|---|---|---|---|
| `engine/ipo_screening/gmp_binding.py` (A28.1 representation/integrity sidecar) | present, 170 lines | **absent** | present, identical to branch |
| `schema/gmp-qualification-binding.v1.schema.json` | present, 258 lines | **absent** | present, identical to branch |
| `engine/ipo_screening/gmp_evidence.py` | capture-failure guard, "Temporarily unavailable" guard, `GMP_LINK_OPTIONAL_EVIDENCE_FIELDS`, `expected_trend` | lacks all four (−11/+51) | identical to branch |
| `engine/ipo_screening/connectors/coordinator.py` | rejects >1 GMP snapshot (`ConflictingSourceError`, "explicitly selected") | **no such guard** (−9 lines) | identical to branch |
| `engine/ipo_screening/gmp_policy.py` (A17 cutoff/age) | present | present | identical to both |
| A28 test files + harness | `test_gmp_binding.py`, `test_gmp_source_safeguards.py`, `test_gmp_mechanics.py`, `test_gmp_retained_inventory.py`, `gmp_mechanics_harness.py` | **absent** | present |
| Shared A9 tests | `test_gmp_evidence_linkage.py` (25 cases), `test_a17_gmp_policy.py`, `test_d1_d3_gmp_source_policy.py` | present | present |

**Direction of the divergence:** it is not a policy conflict and not a fork of the same change. The branch line carries the *newer* A9 subsystem (A28.1 binding + A12/A18 linkage extensions + safeguard guards); the implementation line simply predates it. The two lines did not independently implement the same decision differently.

### 2.2 Behavioural requirements preserved

Qualification is unchanged in the integrated engine:

* A GMP block qualifies only through the A9 evidence contract: a **qualified source**, a **qualifying observation** and **its hash subject**. A generic market-snapshot digest, an opaque legacy `SourceRef.content_hash`, a verified local byte-link, a synthetic binding, or a matching version/config is never substituted (`_a9_final_gmp_gate` in `evaluation_record.py`).
* Missing values remain distinct from present-but-unqualified values (`MISSING` versus `SOURCE_UNQUALIFIED` reason codes).
* A17 cutoff/age still applies on top of the frozen snapshot; no promotion of a `STALE` block.
* The A28.1 binding sidecar remains explicitly **not** an admission authority.

### 2.3 Terminal / nonterminal transitions

Unchanged, and identical to the branch before integration:

| Condition | `outcome_resolution` | `final_outcome` |
|---|---|---|
| FINAL and GMP block missing / no non-null `pct` or `trend` | `NONTERMINAL_UNRESOLVED`, code `MISSING` | absent |
| FINAL and GMP present but source not qualified | `NONTERMINAL_UNRESOLVED`, code `SOURCE_UNQUALIFIED` | absent |
| Non-FINAL modes | A9 gate does not apply | A7 precedence retained |
| Knockout `TRIGGERED` | — | `AVOID` |
| Critical safety incomplete | — | `INSUFFICIENT_DATA` |
| Knockout `UNVERIFIED` | `NONTERMINAL_UNRESOLVED`, `UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT` | absent |

The Jio result shows the first row (`MISSING`) and the K1/K2/K5 `UNVERIFIED` row: A9 precedes A7, so no terminal verdict is manufactured.

### 2.4 Tests enforcing A9 behaviour

`test_gmp_source_safeguards.py` (9 cases: explicit-snapshot selection in both orders, content/order independence, failure capture, PD unavailability), `test_gmp_binding.py` (8), `test_gmp_mechanics.py` (14, synthetic and labelled), `test_gmp_retained_inventory.py` (3), `test_gmp_evidence_linkage.py` (25), `test_a17_gmp_policy.py`, `test_d1_d3_gmp_source_policy.py`, plus the A9 assertions inside `test_evaluation_record_v1.py`. All execute in the integrated suite (§6).

### 2.5 Disposition

**No A9 governance decision is required, and none was taken.** Integration adopts the implementation line for the *non-A9* engine only. The A9 modules (`gmp_binding.py`, `gmp_evidence.py`, `gmp_policy.py`), the binding schema and `connectors/coordinator.py` are taken from the branch and verified byte-identical (`engine-parity.json`). Two further branch files are touched, and only by corrections #8 and #9: `pipeline.py` gains `evidence["field_map"]`, and `evaluation_record.py` prefers that map over the dot→hyphen guess. Neither hunk reaches the A9 gate, the qualification rules or the outcome transitions — verified by the two-hunk diffs and by the A9 assertions in the suite. No success path, no zero-substitution, no non-official issue-term substitution and no bypass of the terminal gate was added. If a later change wanted the implementation line's snapshot policy instead, that would be a decision to *remove* the branch's explicit-selection guard — it is not proposed here and not silently applied.

---

## 3. Target-engine fit — and why the engine identity changes

### 3.1 Patch fit against the branch engine

`patch-apply-to-branch.log` (reproducible: extract `8a1a3702`, `git apply --reject corrections.patch`):

| File | Result on branch engine |
|---|---|
| `evaluation_record.py` | applies cleanly |
| `pipeline.py` | applies cleanly |
| `tests/test_extraction.py`, `tests/test_jio_fresh_regressions.py` | apply cleanly |
| `builder.py` | 1 hunk applied (evidence/candidate agreement), 1 rejected (`kmp_exits_2y`) |
| `extraction/sections.py` | 7 hunks applied, **6 rejected** (3 OFS-NIL, sole-promoter, auditor tenure, no-EOM) |
| `extraction/toc.py` | rejected (context: the branch lacks the newer heading patterns) |
| `extraction_phase5b.py`, `test_rk_fashion_reconciliation.py`, `test_ui7_ingestion.py` | rejected (expected-score context) |

### 3.2 What the branch engine actually does with this filing

Measured directly (`branch-engine-baseline.json`, same PDF, `capture.py`):

| Observation | Branch engine `8a1a3702` | Integrated engine |
|---|---|---|
| Routed sections | 7 — `objects_of_the_offer`, `our_management`, `restated_financials`, `basis_for_offer_price` **not routed** | 11 |
| `use_of_proceeds` | `[{gcp: null, "[●]"}]` on page 120 — debt row missed, container page wrong | debt `275000.0` p116 + GCP `[●]` p116, with page-anchored leaves |
| `capital_structure.promoter_pre_pct` / `post_pct` | **`100.0` / `100.0`** (page 99) — fabricated, contradicting the filed 66.43 % pre and `[●]` post | `66.43` p104, post absent |
| `governance.sebi_ed_action_active` | **`False`** with the quote "No active SEBI or ED regulatory proceedings" — a sentence that does not appear in the source | field not emitted → UNKNOWN, K2 stays `UNVERIFIED` |
| Auditor fields | none (the report span is never recognised) | opinion, continuity, standing and no-EOM, all page-anchored |
| `governance.going_concern_uncertainty` | not emitted | not emitted (positive-only contract) |

The branch's governance block additionally hard-codes `auditor_changed_3y = False` and `repeated_eom = False` with synthesised quotes, and gives `litigation_bucket` a `"clean"` default — the exact fail-open pattern that the A19/A22/A23/A24 decisions removed on the sibling lines. A sole-promoter `pre_quote` hunk cannot even be applied there because the surrounding evidence contract does not exist.

### 3.3 Decision

Two integration shapes were available:

1. **Re-implement six approved safety contracts inside the branch engine**, then apply the corrections — duplicating A19/A22/A23/A24 work that already exists, tested, on a sibling line, inside an engine that still routes this filing incorrectly.
2. **Adopt the implementation line as the branch engine**, keep the branch's A9 subsystem byte-identical, and apply the corrections on top — the exact composition that produced the published evaluation.

Shape 2 was taken. It is the smaller *semantic* change, it removes fabricated K2/promoter values rather than preserving them, and it makes the published evaluation reproducible from the branch itself. Exact inventory in §5.

---

## 4. Correction-by-correction disposition

| # | Correction | Defect | Fix | Fit on branch engine alone | Integrated | Regression test |
|---|---|---|---|---|---|---|
| 1 | Objects-of-the-Issue routing | `OBJECTS OF THE ISSUE` never matched `OBJECTS OF THE OFFER`; `restated_financials`/`our_management` also unmatched, so the auditor block could not run | heading patterns accept ISSUE and the definite-article management form (plus the newer `RESTATED CONSOLIDATED FINANCIAL INFORMATION` form) | hunk rejected; pattern applied to newer router | **yes** | `test_jio_fresh_regressions.py::test_issue_heading_routes_actual_objects`, `test_extraction_phase5b` |
| 2 | Debt-prepayment wording | "Prepayment, in full or in part…" matched no proceeds pattern; only GCP survived | alternative added to the debt category | hunk applied cleanly | **yes** | `…::test_real_debt_and_unknown_gcp_with_amount_page` |
| 3 | Page-anchored proceeds | container stamped with the GCP page; no leaf carried a page/quote | per-category page trace; `use_of_proceeds[i].amount` emitted with the verbatim row | hunks applied cleanly | **yes** | same |
| 4 | Sole-promoter row | pre-issue `66.43` unread; engine fabricated 100 % pre and 100 % post | read the sole-promoter row (identical pre/post counts, post `[●]`) and quote it verbatim; no post derivation | rejected (needs `pre_quote` contract) | **yes** | `…::test_pre_holding_not_copied_into_post`, `test_promoter_holding_extraction` |
| 5 | Auditor identities, tenure, no-EOM | branch emitted constant `False`/`False` with synthesised quotes; identities unread | signed `For … LLP` lines in the report span; joint three-year sentence; explicit negative EOM page-anchored | rejected (no `report_pages`, no positive-only contract) | **yes** | `…::test_auditor_explicit_evidence_no_safety_inference`, `test_auditor_tenure_defaults`, `test_auditor_evidence_section` |
| 6 | Candidate/evidence agreement | evidence `last` overwrote value `first` | `setdefault` keeps the evidence aligned with the candidate actually used | hunk applied cleanly | **yes** | `…::test_builder_first_value_and_evidence_agree` |
| 7 | `kmp_exits_2y` default | default `0` with no disclosed count | default `None` | rejected only for context; one-line change | **yes** | `…::test_builder_unknown_kmp_not_zero` |
| 8 | Canonical field-map persistence | `_evidence_index` computed then discarded | emit `evidence["field_map"]` | applies cleanly | **yes** | `test_jio_fresh_regressions`, `test_evaluation_record_v1` |
| 9 | A15 explicit-map preference | projection guessed IDs by dot→hyphen; "incomplete mapping" warning unconditional | prefer the explicit map, fall back to convention; warn only when no map exists | applies cleanly | **yes** | `…::test_explicit_map_survives_projection` |
| 10 | OFS-NIL binding | bare regex could bind another label's NIL to `issue.ofs = 0`, and missed reader-wrapped labels | `_find_ofs_nil` with label group, amount guard and wrapped bare-label guards | rejected (branch has an inline regex and no helper) | **yes** | `test_ofs_nil_binding.py` (7 cases), `test_jio_rhp_issue_terms.py` |

**Deferred: none of the eleven.** No correction was dropped. Nothing in the patch was applied that overwrites A9 work: the six A9-bearing files are excluded from the adopted set and verified unchanged (§2.1).

---

## 5. Integrated inventory

Relative to the branch engine at `8a1a3702` (`engine-parity.json`):

* **7 modules added** — `aggregator_issue_terms.py`, `extraction/offer_table.py`, `extraction/official_notice_ocr.py`, `extraction/official_offer_amounts.py`, `issue_platforms.py`, `issue_term_fields.py`, `official_issue_sources.py`.
* **15 modules updated** — including `extraction/sections.py`, `extraction/toc.py`, `extraction/builder.py`, `extraction/financial_tables.py`, `extraction/numbers.py`, `extraction/exchange_issue_page.py`, `issue_terms.py`, `enrichment_engine.py`, `schema_validation.py` and the four presentation modules.
* **0 modules removed.** `gmp_binding.py`, `gmp_evidence.py`, `gmp_policy.py`, `connectors/coordinator.py` and `schema/gmp-qualification-binding.v1.schema.json` are byte-identical to the branch. `pipeline.py` and `evaluation_record.py` differ from the branch by exactly the two field-map hunks (corrections #8 and #9) — nothing else.
* **Tests** — 28 files added (A19/A22/A23/A24 governance contracts, aggregator, issue-terms discovery, OFS binding, promoter holding, evaluator-record v1, and the new `test_jio_fresh_regressions.py`), 12 updated.
* **Frontend** — updated to the matching implementation (no branch-only file was lost) because the API gained the aggregator authority surface. `requirements.txt` gains the offline OCR pin set.
* **Untouched** — `config/`, `docs/`, `handoff/`, `evidence/`, `fixtures/`, and every published investigation report.

Two pre-existing expectations in `tests/test_jio_rhp_issue_terms.py` encoded behaviour the adopted engine deliberately changed; both were updated with the reason inline:

| Expectation | Old | New | Why |
|---|---|---|---|
| Fail-closed fields for the Jio RHP | `[price_band_low, price_band_high, lot_size]` | `+ fresh_issue` | the cover prints `aggregating up to ₹[●] million`; the older reader derived an amount from shares × cap price, a price-band substitution the contract forbids |
| Prospectus-stated amount | `1485000.0` (INR lakhs) | `148500.0` (reporting unit) | the input schema defines `issue.fresh_issue` "in reporting_unit"; this filing's unit is INR_MILLIONS |

---

## 6. Validation (integrated engine, actual runs)

| Run | Command | Result |
|---|---|---|
| Backend full suite | `pytest -q tests` on the integrated tree | **1670 passed, 0 failed**, 25 warnings, 20m17s (`tests-integrated-final.log`) |
| Frontend suite | `node --test test/*.test.js` | **93 passed, 0 failed** (`frontend-tests.log`) |
| A9 negative controls | subset in the full suite | pass — missing GMP withholds Final; duplicates/unqualified sources never admitted |
| Historical records | none opened for writing | unchanged (`b79b5794`, `ad5e6872`, `29d9a601`) |

**Discrepancies seen and resolved before that final run** (`tests-integrated-attempt1.log`, 1668 passed / 2 failed):

* `test_jio_score_bridge.py` failed on a **missing fixture** (`fixtures/jio/jio_canonical_2026-10-19_pre_evidence_remediation.json`). The adopted tests reference fixtures that exist only on the implementation line; they were added (`fixtures/jio/` plus the two `fixtures/non-authoritative/` root files). Re-run: pass.
* `test_reproducibility_store.py::test_workbook_bytes_are_deterministic` failed once under full-suite load and passed **5/5** in isolation on re-run. Root cause is pre-existing and outside this integration: `workbook_bytes()` serialises through openpyxl, whose ZIP entries take the wall-clock time at second granularity, while the workbook *properties* are fixed (`FIXED_TIMESTAMP`). `excel.py` is unmodified by this integration and identical on both lines. Recorded as a known flake, not silently "fixed" and not counted as a pass.

Targeted checks confirmed in the integrated engine: `field_map` persists with 48 entries and no dangling IDs; unknown fields carry only their local-input reference; `kmp_exits_2y` stays `null`; K1/K2/K5 remain `UNVERIFIED`; A9 stays `NONTERMINAL_UNRESOLVED` with code `MISSING`.

---

## 7. Evaluation: none created, and why that is correct

The directive allows skipping a re-evaluation when the corrections are semantically identical to those already executed. That is provable here rather than asserted:

* `engine-parity.json` records that the integrated tree's **66 engine files are byte-identical** to the tree that produced `…final-29d9a601` (including every A9 file).
* Therefore the published 34.0 / 24–77 / `INSUFFICIENT_DATA` result *is* this engine's result; producing a second record would duplicate it under a new timestamp and add no evidence.

Both historical evaluations remain untouched, and the earlier diagnostic artifacts (`initial-live`, `initial-retained`, `final-retained`) remain the record of the before/after run.

---

## 8. Remaining blockers (unchanged by integration)

1. **Market evidence** — anchor, subscription, GMP and regime blocks are all `MISSING`. A9 cannot reach a terminal Final without a qualified GMP observation; no unqualified publisher was used to force one.
2. **K1 / K2 / K5** — each needs positive source evidence or an approved negative-confirmation rule plus governance scope:
   * K1: going-concern uncertainty (an unqualified opinion is not a negative confirmation).
   * K2: active SEBI/ED action definition and current case status for the pending promoter matter.
   * K5: quantified-versus-unquantified contingent scope (the filing has no unquantified disclosure in the defined note).
3. **Net-worth basis** — owners' equity `3,359,769` versus ICDR Net Worth `3,340,134`; the engine is unchanged and the choice is a governance decision.
4. **Live official issue terms** — this sandbox's egress still refuses NSE/BSE (TLS/SSL EOF); the last run used the authorized third-party path over retained bytes, tagged non-official.
5. **Frontend build/deploy** — the suite runs headless in Node; no browser acceptance run was performed here.

---

## 9. Reproduction

```bash
# branch content, integrated engine
git checkout <this commit>
python -m pytest -q tests                     # backend
cd frontend && node --test test/*.test.js     # frontend

# target-engine fit re-check (read-only)
git archive 8a1a37022f00496dd22e67b51319a407f6daf6fb | tar -x -C /tmp/base
cd /tmp/base && git init -q . && git add -A && git commit -qm base
git apply --reject docs/investigation/jio-fresh-20261023/source-lineage/corrections.patch

# extraction before/after on the real filing
python docs/investigation/jio-correction-integration-20261023/capture.py <tree> out.json
```

`capture.py` imports the tree's own extractor, runs it on the committed PDF and writes routing plus governance/proceeds/promoter candidates; it writes no evaluation store.
