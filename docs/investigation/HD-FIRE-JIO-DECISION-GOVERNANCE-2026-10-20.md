# HD Fire / Jio — governance decisions D-1 … D-4 and authorised remediation

**Date:** 2026-10-20
**Branch:** `arena/ae4d04e8-ipo-screening-engine`
**Starting commit:** `7754f9b397696e72ab025eca964325aa074f2796` (remote-verified at the start of this pass)
**`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094` — untouched
**PR #6:** OPEN / UNMERGED at head `e05c0ef`

This pass records the four approved dispositions as authoritative decision records
(`handoff/decisions/A19…A22`), implements the two corrections those decisions authorise
(the K5 numerator and the D-3 table scope), verifies the two retained behaviours (D-1 and
D-4), and re-checks that no scoring rule, threshold, golden fixture or historical
evaluation changed.

HD Fire's primary source remains unavailable. No HD Fire page, note number, figure or
quotation is cited as verified anywhere in this document.

---

## 1. Starting state (verified from the remote)

| Item | Value |
|---|---|
| Branch tip (local = remote) | `7754f9b397696e72ab025eca964325aa074f2796` |
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` |
| PR #6 | `OPEN`, `mergedAt: null`, head `e05c0ef`, base `arena/573e69a4-ipo-screening-engine` |
| Working tree | clean at the start of the pass |
| Existing decision register | `handoff/decisions/` with `CONVENTION.md` (GOV-001) and records A1 … A18 |
| Prior pass | `e2ce2c2` (polarity / promoter guard / auditor defaults), `1462ebc`, `7754f9b` (publication records) |
| HD Fire RHP / evaluation record | absent from every branch; `evaluations/` absent |

`CONVENTION.md` requires one Markdown record per decision in `handoff/decisions/`, named
`A<id>-<short-kebab-title>.md`, with status, authority, date, baseline, scope, approved text,
evidence, rationale, consequences, unresolved dependencies and implementation authority.
The four records below follow that format.

---

## 2. Decision records published

| Record | Decision | Status |
|---|---|---|
| `A19-k1-going-concern-positive-evidence.md` | K1 input is positive-evidence only; negation/absence/opinion alone ⇒ UNKNOWN; negative-confirmation rule deferred with prerequisites | RAMKI-APPROVED |
| `A20-k5-contingent-liability-numerator.md` | K5 numerator = disclosed total of the contingent-liability section, commitments excluded, aggregate-over-constituents, ambiguous ⇒ UNKNOWN | RAMKI-APPROVED |
| `A21-promoter-post-issue-holding.md` | `promoter_post_pct` = disclosed post-issue promoter holding; combined row never used; public never added; pre-issue table never read as post; ambiguous ⇒ UNKNOWN | RAMKI-APPROVED |
| `A22-auditor-tenure-and-repeated-eom.md` | Tenure/EOM are evidence-or-UNKNOWN; no constants, no synthesised quotations; cross-year comparison deferred | RAMKI-APPROVED |

Each record contains the required fields: decision, rationale, scope, explicit exclusions,
implementation implications, verification evidence, deferred work and limitations.

---

## 3. D-1 — verification only (no code change)

The approved disposition retains the positive-only behaviour published in `e2ce2c2`.

* `_going_concern_uncertainty_match()` remains the **only** consumer of the phrase regex
  (`grep` shows the definition at `sections.py:1204` and its use inside the matcher).
* A negative confirmation is not emitted; nothing is emitted as `False`; an absent statement
  leaves the field `None`.
* K1 therefore returns UNVERIFIED when the only missing leaf is this one — it can be neither
  CLEARed nor triggered by absence.
* **No negative-confirmation rule was added.**

Verification: `tests/test_going_concern_negative_disclosure.py` **8 passed** (positive phrase,
five negative phrasings, measurement-basis phrase, unrelated "No doubt" control);
`tests/test_auditor_evidence_section.py` positive/absence/live-Jio controls pass.
Live Jio remains `None` / K1 UNVERIFIED.

Deferred prerequisites (also in A19): evidence-coverage definition, required auditor
language, false-negative measurement, re-score decision.

---

## 4. D-2 — numerator implemented

### 4.1 Definition

`financials.contingent_liabilities` = the **disclosed total of the contingent-liability
section** of the note, **excluding capital commitments**. Threshold (50 %), the `when.any`
structure, the unquantified leg and scoring are unchanged.

### 4.2 Row scope (implemented in `financial_tables.py`)

| Element | Rule |
|---|---|
| Section start | the note heading matching `Contingent Liabilities (and Commitments)` |
| Section end | an `(II) Commitments` heading, or the next numbered note heading on the same page |
| Row | a line that **ends** with amount cells; label = accumulated wrapped lines + text before the first amount |
| Period headers | excluded from row labels; latest **31 March** column selected, never the interim column |
| Total row | a unique row labelled `Total`; if it exists, constituent rows are **not** added |
| Sum | used only when no total row exists |
| Commitments | a `(II) Commitments` subsection or a commitment-labelled row (`commitments`, `capital account`, `contracts remaining`) is excluded |
| Fail-closed | width mismatch, more than one total, no rows, or an unquantified exposure without a total ⇒ `None` |
| Unquantified flag | positive language only; negated language ⇒ `None`; never `False` |

### 4.3 Anti-double-count and overlap

* A unique disclosed total wins; its constituent rows are ignored (verified by a test whose
  total equals its parts: 8,993 is returned, not 17,986).
* Six-row sections are summed only when no total is disclosed.
* Commitments are excluded whether they appear under a subsection heading or as a labelled
  row.
* Collateral is not netted: a guarantee secured on deposits remains the disclosed amount.
  Netting is not authorised by this decision.

### 4.4 Evidence — Jio (primary source, p. 405)

| Component | 31 Mar 2026 | Treatment |
|---|---|---|
| Claims / disputed liabilities | **15,021** | the section's only row ⇒ numerator |
| Capital-account commitments | 26,198 | excluded (commitments section) |
| Ratio | 15,021 / 3,359,769 = **0.45 %** | far below 50 % |
| Unquantified flag | `None` | no unquantified language in 591 pages |

Jio's K5 remains UNVERIFIED on the flag leaf only.

**Period-mix correction.** The earlier reconciliation document reported a
"claims + commitments" figure of 105,410 / 3.14 %. That added the **30 June 2026**
capital-commitment column (90,389) to the **31 March 2026** claims column. Same-column arithmetic
is 15,021 + 26,198 = **41,219 → 1.23 %**. The conclusion is unchanged (far below 50 %), but the
3.14 % figure is withdrawn; the earlier document carries an inline correction.

### 4.5 Measured effect of the definition

Controlled fixture, net worth 10,000:

| Numerator | Ratio | K5 | Verdict |
|---|---|---|---|
| 1,000 (claims-only, old behaviour) | 10.0 % | **CLEAR** | INSUFFICIENT_DATA |
| 6,850 (claims 1,000 + guarantees 5,850) | 68.5 % | **TRIGGERED** | AVOID |
| 5,000 (exactly 50 %) | 50.0 % | **CLEAR** | strict `> 50` unchanged |
| `None` + unquantified true | — | **TRIGGERED** | AVOID |

The score is unchanged in every run (K5 is a knockout); the **verdict** changes when the
section total crosses the threshold. This is the materiality the approved definition can have.

### 4.6 HD Fire's BG / EPCG

₹58.50 cr of bank guarantees and ₹31.43 cr of unfulfilled EPCG obligations are **unverified
secondary values**. Under this decision they count only if the RHP places them inside the
contingent-liability section; if they sit under commitments they are excluded. Without the
note, neither the numerator nor the 22.49 % arithmetic is established, and nothing here is
used to clear or trigger K5.

### 4.7 Tests

`tests/test_contingent_liabilities_extraction.py` — **17 passed** (29.50 s): claims-only;
guarantees/EPCG without a claims row; multiple categories; aggregate + constituents; two
totals; commitments excluded; unquantified with and without a total; negated unquantified
language; width mismatch; missing headers; next-note boundary; adjacent note with the same
header; live Jio.

---

## 5. D-3 — metric meaning, D-3b resolution and code changes

### 5.1 Meaning (approved)

`promoter_post_pct` is the disclosed post-issue holding of the promoter category (plus the
promoter-group category where the filing's category (B) is the promoter group). Diluting the
pre-issue holding is explicitly not authorised.

### 5.2 D-3b — how the parser establishes that a table is post-issue

The previous fallback read the last numeric percentage of a `Total (A)` row and added
`Total (B)`. Investigation of the two reference filings:

| Filing | Table | Previous result | Correct result |
|---|---|---|---|
| R.K. Fashion | pre + post columns numeric (`99.61 / 72.22`; group `0.06 / 0.03`) | 99.67 / 72.25 | **99.67 / 72.25** (unchanged) |
| Vishal Nirmiti | **pre-issue-only** table; post cells `[●]` | pre 73.42 / post **37.51** (a pre-issue figure) | pre **73.42** / post **None** |

Rules now applied:

1. a `Total (A)` row must carry a numeric percentage in **more than one** column;
2. a **post-issue marker** must appear in the preceding 120 lines (`Post-Offer`, `Post-Issue`,
   `after the Offer`, `on Allotment`);
3. the category of a `Total (B)` row is read from the nearest heading: promoter /
   promoter group ⇒ added; public / non-promoter ⇒ not added; unknown ⇒ UNKNOWN;
4. percentages are read from the total row itself, not from the following category block;
5. no category heading ⇒ UNKNOWN (the public/groups distinction cannot be guessed).

### 5.3 Live results

| Filing | Pre | Post |
|---|---|---|
| R.K. Fashion | 99.67 | 72.25 |
| Jio | None | None |
| Vishal Nirmiti | 73.42 | **None** (was 37.51) |

### 5.4 Measured effect

Controlled fixture: `promoter_post_pct = 37.51` ⇒ score **14.0**, available 23; `None` ⇒
**13.0**, available 19. A re-scored Vishal would therefore lose one earned point and four
available points; its historical scorecard was **not** re-run or rewritten.

### 5.5 Tests

`tests/test_promoter_holding_extraction.py` — **8 passed** (7.32 s): combined summary row;
standalone total; public total not added; promoter-group total added; pre-issue-only table ⇒
post UNKNOWN; unlabelled (B) ⇒ UNKNOWN; live Jio; live Vishal. R.K. Fashion and the
fixture-fallback isolation tests pass unchanged.

### 5.6 What is *not* claimed

HD Fire's 85.0 % remains a documented arithmetic claim. It would be accepted only if the RHP
discloses it as the post-issue holding of the promoter category; a derived value, if produced
by the separate `enrichment_engine` path, is provenance-marked `SRC-DERIVED` and is not a
disclosed figure.

---

## 6. D-4 — verification only (no code change)

* `auditor_changed_3y` is emitted `False` only on the positive three-year sentence, with the
  verbatim sentence and the page actually matched.
* `repeated_eom` is emitted `False` only on an explicit negative EOM statement with no
  positive EOM.
* Otherwise both fields are absent ⇒ `auditor_bucket` UNKNOWN ⇒ no points.
* No synthetic quotation is emitted; the previous constants are gone.
* `clean_reputed` semantics (unqualified + reputed + no change + no repeated EOM) are unchanged.
* There is **no** `True` path for repeated EOM — recorded as a capability gap.

Verification: `tests/test_auditor_tenure_defaults.py` **9 passed**. R.K. Fashion's stale
`auditor_changed_3y is False` expectation remains updated to `None`; its auditor criterion was
already UNKNOWN, so no score changed. Jio is unaffected (no auditor name matched).

---

## 7. Cross-decision validation

| Check | Result |
|---|---|
| Missing evidence vs explicit negative vs positive vs ambiguous | The four fields distinguish them: positive ⇒ value; explicit negative ⇒ `False` only where the contract defines it; absent/ambiguous ⇒ `None`; nothing is coerced to `False` or CLEAR |
| No fabricated quotations | Auditor quotes are verbatim source sentences; the contingent-liability quote is the source row labels; promoter `quote_is_processing=True` strings are flagged processing text, not source quotations |
| Category totals not used as entity/promoter totals | `Total (A)+(B)+(C)` excluded; `Total (B)` classified by its category label |
| K5 aggregate vs constituents | A unique total wins; constituents are not added |
| K5 commitments excluded | Subsection and labelled-row exclusions, both tested |
| D-1/D-4 safeguards intact | Verified above; no new rules introduced |
| Scoring rules unchanged | No weight, threshold, formula, cap, penalty, knockout, confidence or missing-value rule edited |
| Protected artifacts | `config/`, `schema/`, `fixtures/` untouched; golden hash unchanged |

---

## 8. Protected artifacts and historical records

* `config/ipo-config.v1.5.0.json`: unchanged (`git status` clean for `config/`).
* `schema/ipo-input.v1.5.schema.json`: unchanged. `financials.contingent_liabilities` remains
  `$ref: num`; its definition now lives in A20 rather than in the schema.
* `fixtures/`: unchanged; the golden result hash is asserted by the existing golden tests
  inside the full suite.
* No historical evaluation record was re-run, edited or re-hashed. Jio's `…7857589a` record
  remains 37.0; Vishal's historical scorecard remains 38.0/35.0 as recorded.

---

## 9. Tests executed

| Command | Result |
|---|---|
| `pytest tests/test_contingent_liabilities_extraction.py -q` | **17 passed** (29.50 s) |
| `pytest tests/test_promoter_holding_extraction.py -q` | **8 passed** (7.32 s) |
| six decision-related files (D-1, D-2, D-3, D-4, R.K. Fashion) | **55 passed** (130.09 s) |
| 11-file extraction/regression battery | **153 passed** (344.58 s) |
| `compileall` on the two edited engine modules | clean |
| full backend suite | see §9.1 |

### 9.1 Full suite

`PYTHONPATH=engine:tests ./.venv/bin/python -m pytest tests -q`

| Tree | Result |
|---|---|
| Baseline `7754f9b` (start of pass) | **1179 passed, 1 xfailed**, 38 warnings, 1542.57 s |
| Final tree (this pass) | **1192 passed, 0 failed, 0 xfailed**, 38 warnings, 1566.58 s |

Delta: **+12 collected tests** (contingent-liability file 9 → 17, promoter file
4 → 8) and the one strict-xfail pin (the public `Total (B)` defect) now **passes** because A21
corrects that defect; no xfail remains in either affected file. The 38 warnings are the
pre-existing Starlette deprecation and unregistered `slow`-mark warnings.

---

## 10. Publication

The implementation commit, its remote verification, the test counts at that commit and the PR/`main` state are recorded in the immediately following publication-record commit (`handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`, same section).

---

## 11. Remaining blockers and deferred work

1. **HD Fire primary source** — the RHP, restated financials, auditor report and the
   `…551a7eab` evaluation record are not in this environment. HD Fire source-level acceptance
   remains outstanding; its 7/100 record is unchanged and only arithmetically consistent.
2. **D-1 negative-confirmation rule** — deferred pending coverage definition, required
   language, false-negative measurement and a re-score decision (A19).
3. **D-2 long-note coverage, integer-only cells, schema description, collateral netting** —
   each needs its own rule (A20).
4. **D-3 post-only tables, unlabelled categories, HD Fire's 85.0 %** — remain UNKNOWN (A21).
5. **D-4 cross-year repeated-EOM comparison** — prerequisites recorded in A22; no `True` path
   exists.
