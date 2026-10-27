# A33/A34 — issuer reproduction, semantic boundary and focused verification
— 2026-10-27 (resumed execution)

**Authority.** A33 Alternative A **approved**: preserve the current
`kmp_exits_2y` counting rule provisionally; no counting or scoring change.
A34 Alternative B **approved**: a category-specific institutional lock-in
carve-out alone does not establish an early unlock; only an evidenced early
release may set `capital_structure.large_holders_unlocked_early`.

This record reports **measured reproductions**, not expectations. Every
"before" value was re-evaluated from a committed input snapshot; every "after"
value came from a fresh end-to-end run of the corrected engine on the same
committed filing. The machine-readable summary is
`docs/investigation/a33-a34-issuer-reproduction-20261027/summary.json`.

---

## 1. Workflow actually executed

| Issuer | Committed inputs | Evaluation workflow |
|---|---|---|
| Jio Platforms | `evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf` (591 pp.); the five committed manual terms from `docs/investigation/jio-current-engine-probe-20261027/probe.py` (band 1065/1119, lot 12, OFS 0, fresh 302130); no official discovery provider (`IssueTermsResolver(providers=[])`) | `PresentationService.ingest_document(mode="final", confirm_conflicts=True)` into a disposable temp store; the persisted `input.json`, `result.json`, `evidence.json` were read back. Before-A34 baseline = the committed probe record `JIO-PLATFORMS-LIMITED-20261027-145236Z-final-0fde1451` (`input.json` / `result.json` / `evidence.json`) re-evaluated through `pipeline.evaluate`. |
| Paras Healthcare | `evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf` (651 pp., sha256 `E0A3187F…570E74`); identity-bound issue terms band 660/693, lot 21 supplied separately (the RHP prints `[●]`) | `DocumentExtractor().extract_from_pdf(..., allow_fixture_fallbacks=False)` → canonical input → `pipeline.evaluate(mode="final", evaluation_datetime=2026-10-05T12:00:00Z)` with `config/ipo-config.v1.5.0.json`. Before-A34 baseline = the same canonical input with only `large_holders_unlocked_early = True` restored. |

Both issuers were also re-evaluated with the flag flipped on the *same*
canonical input, so the A34 delta is isolated from every other input. No
weight, threshold, penalty, band, knockout, config, schema, `derived.py` or
builder change is involved.

**Fresh after-A34 Jio evaluation id:**
`JIO-PLATFORMS-LIMITED-20261027-212245Z-final-4e28d0ac` (temp store, not
committed as a product evaluation). Paras was evaluated without a store.

---

## 2. Jio Platforms — before and after A34

| Field | Before A34 (PR #13 reader; committed probe) | After A34 (fresh run) |
|---|---|---|
| `final_score` / base / penalty | **37.0 / 37.0 / 0.0** | **37.0 / 37.0 / 0.0** |
| `verdict` | **`AVOID`** | **`AVOID`** |
| completeness | **63.0%** (available 63, unknown 37) | **62.0%** (available 62, unknown 38) |
| bounds (lower–upper) | **25.0 – 74.0** | **25.0 – 75.0** |
| knockouts | K1 UNVERIFIED, **K2 TRIGGERED**, K3 CLEAR, K4 CLEAR, K5 UNVERIFIED, K6 CLEAR | **identical** |
| modules A–F | 17 / 1 / 10 / 9 / 0 / 0 | **identical** |
| `governance.kmp_exits_2y` | **6** | **6** (A33: unchanged) |
| `board_kmp` | **SCORED 0.0, `high_churn`** | **SCORED 0.0, `high_churn`** |
| `capital_structure.large_holders_unlocked_early` | **`true`** (evidence row p. 105) | **`null`** (no evidence row, no `field_map` entry) |
| `promoter_lockin_in_place` | `true` | `true` |
| C `lockin` | **SCORED 0.0, `weak`** | **UNKNOWN** (no score) |

**Isolated A34 delta.** Removing only the carve-out-derived flag moves exactly
one point from scored-0 to available: completeness −1 pp, upper bound +1.
Final score, verdict, knockouts and all module scores are unchanged. A33
contributes **no** delta: the count stays 6 and the bucket stays `high_churn`.

### Source quotations and page provenance (Jio)

* Regulation 17(1)(c) carve-out, printed **p. 105** (PDF index 104) — before
  A34 the flagged evidence row quoted:
  > "VCF or Category I AIF or Category II AIF or FVCI shall not be locked-in
  > for a period of six months from the date of Allotment, provided that such
  > equity shares shall be locked in for a period of at least six months from
  > the date of purchase"

  Re-extracted independently for this record from
  `U72900GJ2019PLC110816_JIO.pdf`; the full sentence begins "In terms of
  Regulation 17 (1)(c) of the SEBI ICDR Regulations …". After A34 it is still
  present in the filing (test `test_jio_rhp_carve_out_does_not_set_the_flag`
  asserts it) but produces **no** extraction.
* Promoter lock-in, evidence page **104**, locator "Promoter lock-in
  disclosure", quote: **"locked-in for a period of three years"**.
* Directorate table, evidence page **300**, locator "Changes in our Board of
  Directors", quote begins: **"The changes in the Board during the three years
  immediately preceding the date of this Red Herring Prospectus are set forth
  below: Name of Director* Date of change Reasons Mr. John William Hegeman
  March 21, 2026 Resignation as non-executive director …"**. This is the table
  from which `kmp_exits_2y = 6` is counted.
* K2 (unchanged, not an A34 effect): A29 reads p. 468, "SEBI filed a revision
  application before the Hon'ble High Court of Bombay and the same is
  currently pending", which TRIGGERS K2 → `AVOID`.

---

## 3. Paras Healthcare — before and after A34

| Field | Before A34 (PR #13 reader) | After A34 (fresh run) |
|---|---|---|
| `final_score` / base / penalty | **13.0 / 16.0 / −3.0** | **13.0 / 16.0 / −3.0** |
| `verdict` | **`AVOID`** | **`AVOID`** |
| completeness | **44.21%** (available 42, unknown 53) | **43.16%** (available 41, unknown 54) |
| bounds (lower–upper) | **1.0 – 66.0** | **1.0 – 67.0** |
| knockouts | K1 UNVERIFIED, K2 UNVERIFIED, K3 CLEAR, K4 UNVERIFIED, **K5 TRIGGERED**, K6 UNVERIFIED | **identical** |
| modules A–F | 6 / 0 / 3 / 1 / 6 / 0 | **identical** |
| `governance.kmp_exits_2y` | **4** | **4** (A33: unchanged) |
| `board_kmp` | **SCORED 0.0, `high_churn`** | **SCORED 0.0, `high_churn`** |
| `capital_structure.large_holders_unlocked_early` | **`true`** (evidence row p. 117) | **`null`** (no evidence row) |
| `promoter_lockin_in_place` | `true` | `true` |
| C `lockin` | **SCORED 0.0, `weak`** | **UNKNOWN** (no score) |

The before value reproduces the published PR #13 result (13.0 / 44.21% /
`lockin` SCORED 0 `weak`) from the same canonical input. The after value
returns to the pre-PR #13 pinned record's completeness (43.16%). The only
A34-attributable differences are `large_holders_unlocked_early`, `lockin`,
completeness, available/unknown points and the upper bound.

### Source quotations and page provenance (Paras)

* Regulation 17(1)(c) carve-out, printed **p. 117** (PDF index 116) — before
  A34 the flagged evidence row quoted:
  > "VCF or a Category I AIF or a Category II AIF or a FVCI, provided that
  > such Equity Shares will be locked -in for a period of at least six months
  > from the date of purchase by the VCF or Category I AIF or Category II AIF
  > or FVCI shareholders"

  Re-extracted independently for this record; the surrounding sentence begins
  "…(iii) the Equity Shares held by a VCF …". After A34 the test
  `test_paras_rhp_carve_out_does_not_set_the_flag` asserts the sentence is
  present on p. 117 and that it produces **no** extraction.
* Promoter lock-in, evidence page **115**, quote: **"locked in for three
  years"**.
* Directorate table, evidence page **345**, locator "Changes in our Board of
  Directors", quote begins: **"Except as mentioned below, there have been no
  changes in our Directors in the last three years: 340 Name Designation (at
  the time of appointment / change in designation / cessation) … Ramesh
  Abhishek Independent Director July 12, 2024 Resignation due to personal
  commitments …"**. The KMP table discussed in A33 is separately recorded at
  printed p. 357; it prints no designation column, which is why A33's
  provisional "count the table" rule is retained.
* K5 (unchanged): contingent liabilities 3,905.01 against FY2026 net worth
  3,949.41 = 98.88% > 50% → TRIGGERED.

---

## 4. A34 semantic boundary — verification

Approved rule: **a carve-out alone does not set the flag; an evidenced actual
early release does; insufficient or ambiguous evidence stays UNKNOWN.**

| Requirement | Verification |
|---|---|
| Carve-out alone does not set the flag | 3 real filings (Paras p. 117, Jio p. 105, Moneyview p. 485) + 4 synthetic wording variants + 3 ambiguous disclosures → no extraction; `large_holders_unlocked_early` is `null` in both fresh issuer reproductions |
| Actual early release handled by the governing criterion | 3 labelled synthetic positives set the flag with a verbatim sentence quotation; the extraction reaches the canonical field; `lockin_bucket` maps `True → weak`, SCORED 0; a positive is also detectable when a carve-out sentence is present on the same page |
| Insufficient / ambiguous evidence unresolved | category-only mention, Allotment-anchored lock-in, longer purchase-anchored lock-in, normal release on expiry, and hypothetical / conditional / negated release language all stay UNKNOWN |
| Unrelated language does not trigger | 4 pledge / transferability sentences (pledge release, freely transferable, pledge over promoter shares released, lock-in applies only to promoter contribution) stay UNKNOWN |
| Genuine positives remain detectable | retained as labelled synthetic tests; see limitation below |

**Corpus limitation.** A full-text scan of all five examined real filings
(2,826 pages total: Paras 651, Jio 591, Moneyview 537, Vishal Nirmiti 551,
R.K. Fashion 496) found **zero** sentences evidencing an actual early release.
This is a limitation of the available corpus, **not** proof that early releases
never occur. No real-filing positive case is claimed; the synthetic positives
are retained explicitly because the corpus cannot exercise that path.

A separate additive structured field recording the carve-out itself (A34
alternative C) was **not** implemented: it needs a schema/canonical-input
decision of its own.

---

## 5. Focused verification actually run (full suite not run)

* **65 passed** — `tests/test_lockin_institutional_carveout.py` (**28 A34
  tests**), `tests/test_reading_defects_20261026.py` (33),
  `tests/test_a34_issuer_reproduction_20261027.py` (3), and the tier gate
  `tests/test_suite_tiers.py` (1). One assertion in the new issuer module was
  corrected (`criteria["lockin"].get("score")` for an UNKNOWN criterion, which
  has no `score` key) and the batch was re-run clean.
* **132 passed** — eight affected regression modules:
  `test_paras_evidence_regression.py` (20, including the two new A34
  end-to-end Paras tests), `test_rk_fashion_reconciliation.py` (7),
  `test_ui7_ingestion.py` (20),
  `test_jio_current_engine_result_20261027.py` (3, including the fresh Jio
  ingestion), `test_extraction.py` (12), `test_core_semantics.py` (31),
  `test_kmp_exit_counting_scope_20261027.py` (14),
  `test_paras_official_issue_page_terms.py` (25).
* **Tier gate:** `test_suite_tiers.py::test_real_file_and_ingestion_modules_have_an_explicit_tier`
  passed. The rewritten real-PDF module remains declared in
  `tests/tier_inventory.py::INTEGRATION_MODULES`; the new issuer-reproduction
  module is synthetic-tier (committed JSON snapshot only) and needs no
  declaration.
* **CI-equivalent integrity checks passed:** `verify_frozen_core() = True`,
  `verify_golden_result() = True`, `verify_v1_6_implementation() = PASS`,
  every `schema/*.json` valid, `python -m compileall -q engine` clean.
* **Full backend suite was NOT run, by instruction.** The earlier reported
  "28 A34 tests" and "90 tests across four additional modules" from the paused
  session left no surviving test output in this workspace (the checkout was
  reset to a fresh base and the PR #13 head tree had to be recovered). Those
  suites were reconstructed and their scope re-run as above rather than
  accepted on an unverifiable report.

---

## 6. Remaining limitations

1. No real-filing positive early-release case exists in the five examined
   filings; positive coverage is synthetic only.
2. The reader scans the TOC-routed capital-structure range; Moneyview's p. 485
   provision is exercised at rule level only.
3. A32 remains `NOT RATIFIED`. A34's approval does not ratify it; A32's
   separate ratification, and alternative C's structured carve-out field, are
   genuine open governance-recording actions (see A34 §0.3 and §9).
4. A33's approval is provisional: the name/formula mismatch ("KMP exit" vs
   the whole directorate table) and the role-recovery improvement remain open,
   separately authorized decisions. No counting change was made.
5. Jio's 37.0 result still uses five manual issue terms and no official
   discovery provider (environmental restriction), and Paras uses separately
   supplied identity-bound terms; neither is a like-for-like replay of the
   2026-10-23 published record.
6. Modules B/E/F remain blocked on peer, assessment and market-observation
   inputs for both issuers; no substitution was made.
