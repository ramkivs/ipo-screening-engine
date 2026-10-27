# Jio 34 — global architecture disposition (2026-10-27)

**Question put to this pass.** The Jio Platforms evaluation returned 34/100
"despite extensive prior implementation work". Are the proposed global
architectural changes real systemic defects, missing evidence, or legitimate
scoring outcomes — and what should be changed?

**Answer in one line.** The 34.0 / `INSUFFICIENT_DATA` record is **stale, not
wrong**: the engine in `main` no longer produces it. Re-running the current
engine on the same committed RHP returns **37.0, `AVOID`, 25–74**, because the
ratified A29 (K2-A) correction now reads the SEBI revision application disclosed
at p. 468 and TRIGGERS K2. Every other proposed change was inspected and is
either already implemented, already correct and retained, or blocked on
authority/external data. **No engine code was changed by this pass.**

Scope: engine-wide, not Jio- or Paras-specific. Nothing here targets a more
favourable score; the one verdict change below is *less* favourable than the
published record.

---

## 0. Method and evidence base

Read-only inspection of `main` at `69a9ff9` / branch tip `cac095d`, plus:

* the retained 2026-10-23 evaluation
  `docs/investigation/jio-fresh-20261023/final-retained/evaluations/JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601/`
  (`result.json`, `input.json`, `evidence.json`, `runtime.json`,
  `extracted-canonical-with-map.json`, `extraction-report.json`);
* a fresh end-to-end run of the **current** engine on the same committed PDF
  (`docs/investigation/jio-current-engine-probe-20261027/`, probe `probe.py`,
  record `…145236Z-final-0fde1451`);
* full-document text searches of the 591-page RHP for every field the engine
  reports `UNKNOWN` for.

No `.venv` persistence across sessions; the venv was recreated (core +
`pypdfium2==5.14.0 Pillow==13.0.0 numpy rapidocr==3.10.0 onnxruntime==1.24.4`).

---

## 1. Workstream 1 — reconstruct and diagnose the 34

### 1.1 The published record is not this engine's result

`runtime.json` fingerprints 66 engine files for the 2026-10-23 run. Comparing
those hashes with `main`:

* **20 of 66 differ** (pinned explicitly in
  `tests/test_jio_current_engine_result_20261027.py::DIVERGENT_ENGINE_FILES`).
* The integrated tree that `JIO-CORRECTION-INTEGRATION-2026-10-23.md` §7 calls
  "byte-identical to the tree that produced `…final-29d9a601`" is **not
  reachable from any ref in this repository** (`git branch -r` shows only
  `main` and `arena/342ccacc`; the commit `514ca599…` recorded in
  `runtime.json` is absent).

So §7's inference — "the published 34.0 *is* this engine's result, therefore no
new evaluation is needed" — does not hold for `main`. That is a
documentation/provenance defect, and it is the reason the 34 looked like an
anomaly worth investigating.

### 1.2 What the current engine actually returns

Same PDF, same five manual terms (`price_band_low/high`, `lot_size`, `ofs`,
`fresh_issue`), no official discovery provider (this sandbox has no TLS egress
to NSE/BSE):

| | published 2026-10-23 | current engine |
|---|---|---|
| `final_score` | 34.0 | **37.0** |
| `verdict` | `INSUFFICIENT_DATA` | **`AVOID`** |
| bounds | 24 – 77 | 25 – 74 |
| `completeness_pct` | 57.0 | 63.0 |
| K2 | `UNVERIFIED` | **`TRIGGERED`** |
| Module C / D | 11 / 5 | 10 / 9 |

Per-criterion movement:

* **K2 `UNVERIFIED` → `TRIGGERED`** — A29 (K2-A) reads p. 468: *"Against the said
  order of the Special Court, SEBI filed a revision application before the
  Hon'ble High Court of Bombay and the same is currently pending."* A proceeding
  pending at the cut-off is an active action; the party is attributed from the
  section heading *"III. Outstanding litigation involving the Directors"* under
  A29 P3. `TRUE` in a Kleene `any` wins → `TRIGGERED` → `AVOID`.
* **D `promoter_post_holding` `UNKNOWN` → 4.0** — derived arithmetically from the
  disclosed pre-issue holding (66.43%) and the disclosed pre/post share counts
  (8,939,030,830 → 9,209,030,830) with a zero OFS. The RHP's own post-issue
  column is `[●]`; the derived value is reported as `derived`, not as a
  disclosed figure.
* **D `board_kmp` `UNKNOWN` → 0.0 (`high_churn`)** — the changes-in-directorate
  table is now read; `kmp_exits_2y` = 6 in the 24-month window anchored on the
  offer open date.
* **C `lockin` 1.0 → 0.0 (`weak`)** — `large_holders_unlocked_early` is now
  **extracted as `true`** (p. 105, `DETERMINISTIC_PDF`, confidence 1.0) instead
  of being defaulted to `false`.
* **A, B, E, F unchanged** in structure; B remains 1/20 and E and F remain 0.

### 1.3 Two defaults that were fabricating answers are gone

The published `input.json` carries `promoter_pledge_pct: 0.0`,
`promoter_lockin_in_place: true`, `large_holders_unlocked_early: false` and
`discounted_allotments_18m_before_drhp: false`, **none of which appear in the
extraction report** — they were builder defaults. On the current engine
`promoter_pledge_pct` is `null` (the filing states no pledge) and
`large_holders_unlocked_early` is an evidenced `true`. This is the intended
direction: the old defaults cleared K2's pledge limb and the C `lockin`
criterion *without evidence*; they are removed.

### 1.4 Classification of the low/missing criteria

| Criterion | State | Class | Basis |
|---|---|---|---|
| A `roce` 1/5 | SCORED | legitimate | disclosed ROCE 10.76 vs a ≥10 band |
| B `pe_vs_peers` 0/8 | SCORED | legitimate | premium vs peer median, band `else` |
| B `second_multiple` | UNKNOWN | missing evidence | both peers have `pb: null`; no second multiple exists |
| B `sector_ipo_relative` | UNKNOWN | missing input | no recent same-sector IPO valuations supplied |
| C `use_of_proceeds` | UNKNOWN | **correct withholding** | GCP printed `[●]`; absence is not zero |
| D `promoter_post_holding` | SCORED | derived | see §1.2 |
| D `board_kmp` | SCORED 0 | see §6.3 | count semantics unresolved |
| E `industry_growth` | UNKNOWN | **correct withholding** | see §6.1 |
| E `moat`, `visibility` | UNKNOWN | authority boundary | analyst-owned (Tier 4) by contract |
| E `concentration` | UNKNOWN | genuinely not disclosed | full-document search found no top-5 customer/supplier table |
| F all five | UNKNOWN | missing external data | no market block supplied; egress blocked |

**No low score on this filing is evidence of a scoring defect.** The score is
low because 43 of 100 points sit in criteria whose inputs were never supplied.

### 1.5 All eleven Jio corrections are present in `main`

The prior line's central worry was that the eleven corrections integrated on
`arena/07f3439f` might be branch-only. They are not. Each was located in
`main` at `69a9ff9`:

| # | Correction | Marker found in `main` |
|---|---|---|
| 1 | Objects-of-the-Issue routing | `toc.py:29` — `OBJECTS\s+OF\s+(?:THE\s+)?(?:OFFER\|ISSUE)` |
| 2 | Debt-prepayment wording | `sections.py` proceeds patterns (prepayment/pre-payment rows) |
| 3 | Page-anchored proceeds | per-category page trace in the objects-of-offer reader |
| 4 | Sole-promoter row | `sections.py` `pre_quote` / `sentence_pre_quote` contract |
| 5 | Auditor identities, tenure, no-EOM | `sections.py:4916` — `re.findall(r"\bFor\s+([^\n]+?\bLLP)\b", text)` |
| 6 | Candidate/evidence agreement | `builder.py:213` — `evidence_dict.setdefault(...)` |
| 7 | `kmp_exits_2y` default `None` | `builder.py:542` + `_derive_board_changes` (§1.3) |
| 8 | Canonical field-map persistence | `pipeline.py:341` — `evidence={…, "field_map": …}` |
| 9 | A15 explicit-map preference | `evaluation_record.py:801-802, 1367` |
| 10 | OFS-NIL binding | `sections.py:120` — `_find_ofs_nil` (imported by `official_offer_amounts.py`) |
| 11 | A9 subsystem | `gmp_binding.py`, `gmp_evidence.py`, `gmp_policy.py`, `schema/gmp-qualification-binding.v1.schema.json` |

A29 (K2-A) is likewise present: `handoff/decisions/A29-k2-active-action-pending-appeal.md`
and `sections.py:3591` — `_LIT_HEADING_PARTY_ATTRIBUTION = True`.

The twenty divergent files listed in §1.1 are therefore **not** missing
corrections; they are later work on the same files. What `main` lacks is only
the *exact byte content* of the 2026-10-23 tree, which makes the published
record non-reproducible but does not invalidate its evidence.

---

## 2. Workstream 2 — UNKNOWN scoring and completeness: **retained, correct**

Inspected `engine/ipo_screening/scoring.py` and every consumer of criterion
scores, module totals, confidence, completeness, bounds and verdicts.

The implemented model is exactly the proportional available-weight design the
workstream asks to compare against:

```
available_points  = Σ max(c) for positive c with state == SCORED
unknown_points    = Σ max(c) for positive c with state == UNKNOWN
total_evaluable   = available_points + unknown_points
completeness_pct  = available_points / total_evaluable × 100
base_score        = Σ c.effective_score           (UNKNOWN → 0)
lower_bound       = base_score + penalties − unresolved_penalty_points
upper_bound       = base_score + unknown_points + penalties
```

Verified behaviour:

* `UNKNOWN` contributes **0** to `base_score` and its **full `max`** to
  `upper_bound`; it is counted in the completeness **denominator** and excluded
  from the **numerator**.
* `NOT_APPLICABLE` is excluded from both numerator and denominator; penalty
  criteria (`max == 0`) are excluded from the positive-point denominator.
* Confidence bands (`high_min_completeness_pct` 95 / `medium_min_completeness_pct`
  80) are driven by `completeness_pct`, and `_completeness_breakdown` reports
  valuation, market, critical-data and knockout completeness **separately** so
  high overall completeness cannot hide a missing knockout input.
* Verdict precedence is knockout → critical-missing → band-uncertainty → band.
  Jio's `INSUFFICIENT_DATA` came from the *critical-missing* branch
  (`going_concern_uncertainty`, `sebi_ed_action_active`); the current run's
  `AVOID` comes from the *knockout* branch, which correctly takes precedence and
  clears `insufficient_data`.

**Disposition: (b) existing behaviour correct and retained.** No normalisation
was introduced; the raw `base_score` is still reported alongside the bounds, so
an incomplete IPO cannot be made to look complete. The anti-inflation property
is structural (UNKNOWN earns nothing in the base score) and is pinned by
`tests/test_core_semantics.py`.

---

## 3. Workstream 3 — knockout verification-state semantics: **retained**

`engine/ipo_screening/knockouts.py` already implements the tri-state model the
workstream proposes:

* `TRIGGERED` / `CLEAR` / `UNVERIFIED` over **Kleene three-valued logic**
  (`k_and` / `k_or` / `k_not`, `Truth.__bool__` raises so a three-valued result
  cannot be used as a Python truth value);
* a decisive `TRUE` wins an `any` even when other leaves are `UNKNOWN`;
* an `all` with one `FALSE` is decisively `FALSE` (CLEAR);
* otherwise `UNKNOWN` propagates — **a missing input never becomes CLEAR**;
* every `UNVERIFIED` carries `missing` references and a per-leaf `LeafTrace`;
* `KnockoutSummary.completeness_pct()` is the share resolved to CLEAR or
  TRIGGERED, reported in the final result and the completeness breakdown.

Every default used by knockout evaluators was inspected. In
`extraction/builder.py` the knockout-relevant fields
(`promoter_pledge_pct`, `promoter_lockin_in_place`, `large_holders_unlocked_early`,
`discounted_allotments_18m_before_drhp`, `promoter_pre_pct`,
`board_independent_majority`, `rpt_pct_revenue`) fall back to **`None`** whenever
`allow_fixture_fallbacks` is false, and `allow_fixture_fallbacks` defaults to
  `False` (builder signature). The only surviving defaults are
  `financials.reporting_unit` → `"INR_LAKHS"`, `board` → `"mainboard"` and
  `company_name` → `"Unknown Limited"`; **none of them is read by a knockout**.
  `sebi_ed_action_active`, `going_concern_uncertainty` and
  `board_independent_majority` all fall back to `None`.

The proposed fourth state — *procedurally blocked* — has **no current
consumer**. None of K1–K6's inputs (`auditor_opinion`, `going_concern_uncertainty`,
`net_worth_latest`, `promoter_pledge_pct`, `sebi_ed_action_active`,
`ofs_share_pct`, `profit_declining`, `pe_promoter_sold_pct_combined`,
`promoter_full_exit`, `promoter_post_pct`, `contingent_liab_pct_networth`,
`contingent_liab_unquantified`, `rpt_pct_of_revenue_growth`) is fetched from a
network or a provider; all are derived from the filing or supplied input. A
procedural block therefore cannot arise inside a knockout today, and both a
missing value and a blocked retrieval already resolve to `UNVERIFIED`, which
satisfies "must not be CLEAR" and "must not be TRIGGERED".

**Disposition: (b) existing behaviour correct and retained.** Introducing an
explicit `PROCEDURALLY_BLOCKED` state would add a state no caller can produce;
the tri-state model already satisfies both safety requirements. A future
knockout whose input comes from a connector should add the state then, with a
test for each of the four states.

---

## 4. Workstream 4 — final-filing discovery and GCP extraction

### 4.1 GCP: **correct, no statutory-ceiling substitution**

`derived.py::_gcp_amount` returns `UNKNOWN` when the schedule shows `[●]`:

> *"the general corporate purposes amount is shown as [●] in the RHP and is
> therefore undisclosed; the legal maximum is recorded separately and is NOT
> substituted for the actual amount"*

`_gcp_legal_max` computes `legal_max_pct_of_fresh_offer × fresh_issue`
(SEBI ICDR Reg. 7(2)) and is reported **separately**. `_use_of_proceeds_bucket`
treats any category with an undisclosed entry as unknown *for the whole
category*, so a partial total cannot understate the `blind_heavy` share and
silently clear it. An **empty** schedule is `UNKNOWN`, not `mixed_ok` and not
zero. Jio's `use_of_proceeds` shows `debt_repayment 275,000` and
`gcp [●]` → `UNKNOWN` for the 4-point criterion. **Disposition: (b).**

### 4.2 Authoritative final-filing discovery: **implemented**

`engine/ipo_screening/aggregator_issue_terms.py`, `official_issue_sources.py`,
`issue_platforms.py`, `issue_term_fields.py`, `extraction/official_offer_amounts.py`,
`extraction/official_notice_ocr.py`, `extraction/offer_table.py` and the
`THIRD_PARTY_AGGREGATOR_OVERRIDE` authority surface are present in `main`. The
2026-10-23 run exercised them and emitted four `authority_warnings` naming
every field taken from the PA-authorized third party. **Disposition: (b) —
implemented; the remaining limitation is that this sandbox cannot re-fetch the
aggregator bytes (`docs/investigation/aggregator-fallback-2026-10-22/native-accepted.json`
is absent), so the probe used the same five manual terms instead.**

---

## 5. Workstream 5 — global market-data ingestion

`market.json` from the current run: all four blocks (`anchor`, `subscription`,
`gmp`, `regime`) are `MISSING` with reason `"block not supplied"`, `as_of: null`.
Module F is 0/10 with all five criteria `UNKNOWN`.

* The provider-neutral architecture exists (`connectors/{interfaces,adapters,coordinator}.py`,
  `presentation/` market-block surfaces, `market_snapshot_hash` in the record).
* No block is mapped to a zero or to a fabricated value; each block carries its
  own `status`, `reason`, `as_of` and `values`, and the record carries a
  `market_snapshot_hash`.
* GMP is kept **distinct** from exchange demand data and is documented as
  sentiment-only (`gcp_trend` / `A17`/`A18` policy modules present).
* This sandbox has no TLS egress to `bseindia.com` / `nseindia.com`; the BSE
  issue page returns `status=H` so discovery returns `UNAVAILABLE`. That is an
  **environment limit, not an engine defect**.

**Disposition: (c) missing data / external dependency, with a defined
requirement.** The requirement is a live, provider-neutral adapter that can
populate `anchor`, `subscription`, `gmp` and `regime` blocks with
source/provenance metadata, freshness and identity matching. It cannot be
built or verified inside this sandbox, and no part of it may be simulated.

---

## 6. Workstream 6 — peer comparison and valuation

### 6.1 Module E's zero is legitimate, and a plausible "fix" is a fabrication

The RHP *does* print many CAGRs (pp. 152–181). A first hypothesis was that
`extract_business`'s period regex (`20[2-3]\d\s*(?:to|-|–)\s*20[2-4]\d`,
requiring a full four-digit year pair immediately after the value) was too
strict, because the filing writes `FY2026-31`.

That hypothesis was tested and **rejected**. Instrumenting the loop shows the
filing's CAGRs are almost all *value-before-acronym* ("grow at a 25% CAGR
(FY2026 - 2031)", p. 174) or *segment-level*. Adding a value-before-acronym
pattern and an abbreviated-year normaliser makes the reader emit
`business.industry_cagr_pct = 11.77` from **p. 152** — India's *nominal GDP*
CAGR — because the generic pattern has no way to prefer the market forecast over
the GDP forecast. That is a fabricated industry growth figure, not a
correction. **The change was reverted; the working tree is clean.**

The filing names its industry report (p. 8 *"The industry report titled
'Overview of digital connectivity and digital services markets'"*, p. 25/30
*"Analysys Mason Report"*), but `_industry_report_source()` returns `None`
because `_INDUSTRY_REPORT_DEF` requires a `"X Report", … Industry Report titled
"…", dated <date>` shape. Even with the source established, Jio's RHP contains
no sentence matching `_CAGR_RANGE`. A defensible rule for *which* of the
filing's many segment CAGRs is "the industry CAGR" does not exist in the
contract, so `UNKNOWN` is the correct, non-fabricated outcome.

**Disposition: (b) for `industry_growth`; (a) for none.**

### 6.2 Module B is blocked on peer data, not on extraction

`peers.json` carries exactly two observations (Bharti Airtel P/E 40.71,
Vodafone Idea P/E 3.99), both `status: VALID`, `business_match: partial`,
`pb: null`, `as_of: 2026-10-13`, `age_days ≈ 14.6`, `rejected_count: 0`. The
peer table is read from the filing (p. 130). `pe_vs_peers` is evaluated (0/8);
`second_multiple` is `UNKNOWN` because no peer supplies a second multiple;
`sector_ipo_relative` is `UNKNOWN` because no recent same-sector IPO valuations
were supplied. No peer metric is substituted for an unavailable one.

**Disposition: (c) for `second_multiple` and `sector_ipo_relative` — defined
requirement: a second multiple (EV/EBITDA or P/B) and a recent same-sector IPO
series, both with provenance. No substitution rule is authorised.**

### 6.3 Two semantic questions that need a governance decision, not a silent change

**(i) `kmp_exits_2y` counts board exits, not only KMP exits.**
`directorate.py::count_exits` counts every event whose `event` is in
`{resignation, cessation, retirement, term_expiry}` — including
non-executive-director and independent-director resignations — although the
field name and the consuming formula (`board_kmp_bucket`: *"high_churn: >=2
KMP exits"*) both say KMP. For Jio that yields 6. `is_exit()` never looks at
`role`, even though the reader records one.

Two KMP-only readings were computed on the real tables this pass, and they are
not the same rule:

| Reading | Jio (17 rows) | Paras KMP p. 357 (7 rows) | Consequence |
|---|---|---|---|
| **B1** — count only a recognised KMP `role` | **1** | **0** | both fall below ≥2 → `board_kmp` `high_churn` → `other` (**+1 each**) |
| **B2** — skip a *known* non-KMP designation, count an unrecognised one fail-closed | **2** | **4** | no bucket changes on either filing |

B1 is the reading that destroys evidence: Paras's KMP table prints **no
designation column**, so the reader leaves `role` null on every row, and all four
disclosed resignations would become unclassifiable. B2 is the rule this report's
§8(1) describes, and its estimate ("effect on Jio: none") is correct **under B2** —
but it still keys a count on a field whose absence is an extraction artifact.

The two Jio exits B2 retains are the CEO resignation (2026-03-23) and the one exit
whose designation the reader did not recover (2026-06-19); there is **no Company
Secretary resignation in Jio's window**. Recorded in
`handoff/decisions/A33-kmp-exit-counting-scope.md` (PROPOSED, not implemented).
**Recommendation: retain the current rule.**

**(ii) `large_holders_unlocked_early = true` rests on one sentence.**
The reader matched p. 105: *"equity shares held by a VCF or Category I AIF or
Category II AIF or FVCI shall not be locked-in for a period of six months from
the date of Allotment, provided that such equity shares shall be locked in for a
period of at least six months from the date of purchase"*. That is Regulation
17(1)(c)'s *minimum* lock-in, arguably not an early unlock; the alternative
reading makes it the same six months from allotment. The match turned
`lockin_bucket` from `intact` to `weak` (−1 point) relative to the published
record.

The sentence was re-extracted from
`evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf` this pass and is
verbatim on printed p. 105 (PDF index 104); Paras's parallel sentence is verbatim
on printed p. 117 (PDF index 116). The provenance is sound. What the sentence does
**not** state is when those holders purchased, and that date is what decides
whether the carve-out produces a release *earlier* than the general rule, at the
same time, or later. The flag as set therefore asserts a release the filing does
not evidence. Recorded in
`handoff/decisions/A34-early-unlock-carve-out-semantics.md` (PROPOSED, not
implemented). **Recommendation: a category carve-out alone must not set the flag;
without evidence of an actual early release the field stays `null` and C `lockin`
stays UNKNOWN.**

**Disposition: (d) for both — not implemented.** Each changes the meaning of a
scoring input while leaving thresholds and weights untouched, so they are
*derivation* decisions rather than mechanical extraction bugs, and each needs
the ratifying authority that A19–A32 used. The specific decisions required are
stated in §8.

---

## 7. Workstream 7 — regression matrix and validation

Jio and Paras are diagnostic cases, not the validation set. This pass used:

| Case | Inputs | Exercises | Result |
|---|---|---|---|
| Jio RHP, complete-as-supplied | financials + governance + 2 peers, no market block | modules A–F, K1–K6, both verdict branches | 37.0 / `AVOID`, K2 TRIGGERED |
| Jio RHP, published input | same, 2026-10-23 tree | fingerprint parity | 34.0 / `INSUFFICIENT_DATA` (historical) |
| Paras + Vishal Nirmiti fixtures | synthetic deltas from the golden input | UNKNOWN handling, knockout states, extractor boundaries | unchanged |
| `tests/test_litigation_regulatory_defaults.py` | A23/A24/A25/A29 pins | K2 party scope, negative confirmation | 102 passed |
| `tests/test_directorate_events_20261026.py` | board + KMP tables | 24-month window, `None` anchor | passed |
| `tests/test_contingent_liabilities_extraction.py` | Note 37 | K5 numerator and citation | 17 passed |
| `tests/test_jio_fresh_regressions.py` | auditor / proceeds / K2 | remediation pins | 7 passed |

**Actual test runs this pass.** No engine file was changed; the only source
change is one test file plus its tier declaration.

```
tests/test_jio_current_engine_result_20261027.py          3 passed   (23.9s)
tests/test_jio_score_bridge.py + evidence_remediation + fresh_regressions
  + litigation_regulatory_defaults + directorate_events_20261026
  + jio_rhp_issue_terms + core_semantics                 171 passed  (85.7s)
tests/test_suite_tiers.py + test_jio_current_engine_result_20261027.py
                                                          4 passed   (22.7s)

full suite, first run     2168 passed, 1 failed, 25 warnings  (1166.5s)
full suite, re-run        2169 passed, 0 failed, 25 warnings  (1173.1s)
```

The single first-run failure was the conservative tier gate
`tests/test_suite_tiers.py::test_real_file_and_ingestion_modules_have_an_explicit_tier`:
the new file mentions `ingest_document`, so it must be declared in
`INTEGRATION_MODULES` (`tests/tier_inventory.py`) — a hard gate, not a
selection. `test_jio_current_engine_result_20261027.py` was added to that
frozenset; the re-run above is the clean full-suite result.

`tests/test_reproducibility_store.py::test_workbook_bytes_are_deterministic`
is the one known pre-existing openpyxl-ZIP-timestamp flake. It is untouched by
this pass and was not the failure above.

---

## 8. Dispositions, and the two decisions required

**(a) confirmed global defect and remediated** — none found in engine code this
pass. The two real defects found were documentation/provenance (§1.1) and the
stale-result claim (§1.2); both are remediated by
`tests/test_jio_current_engine_result_20261027.py`, which pins the 20 divergent
files and the current engine's actual result so neither can be asserted away
again.

**(b) existing behaviour correct and retained** — UNKNOWN scoring/completeness
(§2); knockout tri-state semantics and default hygiene (§3); GCP handling and
no statutory-ceiling substitution (§4.1); final-filing discovery (§4.2);
`industry_growth`, `moat`, `visibility`, `concentration` for Jio (§6.1).

**(c) missing data / external dependency** — all four market blocks (§5);
`second_multiple` and `sector_ipo_relative` (§6.2). Defined requirements are
stated inline; nothing was simulated.

**(d) not implemented — authority boundary** — §6.3 (i) and (ii).

### Decisions required (presented, not implemented)

1. **`kmp_exits_2y` scope.** Does "KMP exit" mean *only* Key Managerial Personnel
   (CEO/MD/WTD/CFO/Company Secretary/Manager), or does it include board-of-
   directors exits? If the former, `directorate.py::count_exits` must skip exits
   whose `role` is a known non-KMP designation and count exits with an unknown
   role (fail-closed). Estimated effect on Jio: none (2 KMP exits still ≥2).

   *Correction, measured this pass.* The "fail-closed on an unknown role" form is
   one of two KMP-only readings and the milder one. It gives Jio **2** and Paras
   **4**, so no filing's bucket changes — the estimate above holds **for that
   form**. The stricter form (count only a *recognised* KMP role) gives Jio **1**
   and Paras **0**, which is below the ≥2 boundary: `board_kmp` would move
   `high_churn` → `other` on both (+1 each). The stricter form is rejected because
   Paras's KMP table has no designation column, so the reader leaves `role` null on
   every row and all four disclosed resignations would become unclassifiable.
   Recorded in `handoff/decisions/A33-kmp-exit-counting-scope.md` (PROPOSED, not
   implemented). **Recommendation: retain the current rule.**
2. **`large_holders_unlocked_early` reading.** Is Regulation 17(1)(c)'s
   purchase-anchored minimum lock-in an *early unlock* of large pre-IPO holders,
   or the same six-month lock-in measured from a different date? If the latter,
   the p. 105 match should not set the flag. Estimated effect on Jio: `lockin`
   1.0 → 0.0 reversed.

   Recorded in `handoff/decisions/A34-early-unlock-carve-out-semantics.md`
   (PROPOSED, not implemented). The two quotes are verbatim and correctly
   page-attributed (Jio p. 105, Paras p. 117, both re-extracted this pass); what
   they do not state is the holders' purchase dates, which is what decides whether
   the carve-out is an early release at all. **Recommendation: a category
   carve-out alone must not set the flag; absent evidence of an actual early
   release the field stays `null` and C `lockin` stays UNKNOWN.**

Neither decision changes a threshold, weight or verdict band. Both change what a
scoring *input* means, which is why they are presented rather than implemented.
Both are now written up as decision records (A33, A34) with a recommendation, the
measured alternatives and an explicit **no implementation authority**; neither is
ratified, and A32 — which A34 is part of — remains `NOT RATIFIED`.

---

## 9. What this pass did not do

No engine file was modified (the one candidate correction, §6.1, was implemented,
tested against the real filing and **reverted**). No new evaluation was published
as a product result — `docs/investigation/jio-current-engine-probe-20261027/` is
a diagnostic probe with its own `probe.py`, retained record and input snapshot.
No historical evaluation artifact was edited. No scoring rule, knockout
threshold, weight or verdict policy was changed. K1 and K5 remain `UNVERIFIED`
(K1: no statement of either polarity on going concern; K5: Note 37 is fully
quantified at 0.45% of net worth and the `unquantified` flag is not established
by any governed extractor). No version upgrade was performed.

## 10. Reproduction and publication

```bash
# fingerprint divergence + current-engine result pin
python -m pytest -q tests/test_jio_current_engine_result_20261027.py

# the diagnostic probe that produced …145236Z-final-0fde1451
python docs/investigation/jio-current-engine-probe-20261027/probe.py
```

**Publication.** The disposition commit is the tip of
`arena/342ccacc-ipo-screening-engine` and has been pushed; at the time of
writing `git rev-parse HEAD` and `git rev-parse origin/arena/342ccacc-ipo-screening-engine`
both resolve to the same SHA, and `git status` is clean. The commit was amended
while this report was being written, so the branch tip changed hash across
pushes; `--force-with-lease` was used each time and the remote tip now matches
the local tip exactly. (The report deliberately does not pin its own commit
SHA — a self-reference that cannot stay correct across amends.)

`gh pr create` enforces one open pull request per head branch, and this branch
already had PR #13 open, so the commit could not be given its own PR. It rides
on **PR #13 (OPEN)** — `ramkivs/ipo-screening-engine#13`,
`arena/342ccacc-ipo-screening-engine` → `main`, now carrying two commits:
`cac095d` (the Regulation 17 lock-in reader generalisation) and the disposition
commit (this report, the probe and the test). The separation is recorded in a
comment on PR #13 rather than silently folded in. **PR #13 has not been
merged.**

Verified remotely: `gh pr view 13` reports state `OPEN`, base `main`, and a
`headRefOid` equal to the local `HEAD`.
