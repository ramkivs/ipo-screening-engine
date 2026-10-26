# Generic RPT extraction; metric-definition boundary — 2026-10-17

## Proven defect and root cause

The Gemini-review audit (2026-10-17) proved that related-party
transaction notes in RHPs were never extracted: no extractor read the
related-party note, so no RPT evidence existed anywhere in the pipeline.
For Vishal Nirmiti, Note 47 (RHP PDF pp. 386–388, printed pp. 380–382)
discloses full three-year transaction tables, yet the runtime left
`governance.rpt_pct_revenue` and `governance.rpt_pct_of_revenue_growth`
null, Module D's `rpt` criterion UNKNOWN and knockout K6 UNVERIFIED.

First point of loss: **PDF extraction** (no consumer of the RPT note),
compounded by the closed runtime canonical schema, which admits no
structured RPT field in `governance`.

## What was implemented (issuer-neutral, deterministic)

`SectionExtractor.extract_related_party_transactions`
(`engine/ipo_screening/extraction/sections.py`), wired into
`DocumentExtractor.extract_from_pdf`:

- locates the "Transactions with related parties" table in the
  related-party note (TOC financial range first, full-document fallback);
- parses counterparty rows under transaction-category headers
  (sales/purchases of goods and PPE, services, interest, rent, salary,
  remuneration, reimbursements, hiring/job-work charges, loans, share of
  profit; unknown categories slugified, never dropped silently into a
  known bucket);
- handles wrapped counterparty names, category+counterparty on one
  line, split or single-line period headers, and two- or three-year
  column layouts;
- emits one extraction per (category, counterparty, period) with the
  verbatim source row as quote, PDF page, section and locator;
- excludes outstanding-balance tables and "Total" rows (no
  double-counting); deduplicates identical
  (category, counterparty, period) rows;
- treats `-` cells as undisclosed — never zero, never emitted;
- fails closed on rows whose amount count does not match the disclosed
  period columns, and when fewer than two period columns are disclosed;
- records the disclosed unit (note-level or inherited from the restated
  financial statements' unit declaration, e.g. "(Amount in Lakhs, unless
  otherwise stated)"), searching a bounded window before the note.

The extractions are registered as canonical evidence under
`governance.related_party_transactions[i]` paths by the existing
`CanonicalInputBuilder._build_evidence` mechanism. Because the runtime
canonical schema (`governance`) is closed, **no structured canonical
field is added and no input snapshot changes** — proven by test:
evaluating the golden fixture is byte-identical in outcome, and the
real-PDF canonical governance contains no new key.

## Vishal verification (hand-checked against Note 47)

- Sale of goods: FY2026 ₹2,260.49L (Samruddhi Industries 2,197.56;
  Raghvendra 56.77; Siddhi Ferrous 5.32; Gita Gazebo 0.84), FY2025
  ₹3,091.60L, FY2024 ₹3,270.77L — unit INR_LAKHS, source PDF p. 387.
- Purchase of goods FY2026 ₹2,427.54L (Prestress Steel LLP 1,357.19;
  Siddhi Ferrous 905.68; …), kept strictly separate from sales.
- 136 transaction extractions in total for Vishal, every quote a
  verbatim substring of its source page (asserted in tests).

## Approved metric definitions (Ramki, 2026-10-17) — IMPLEMENTED

**Module D — RPT exposure (`rpt_pct_revenue`).** Related-party
sales/services income ÷ total revenue from operations, latest audited
financial year, %. Eligible numerator categories are revenue-type only:
sale of goods, sale of services (any `sale_of_*` except sale of PPE),
and job-work charges received. Purchases, loans, interest paid,
remuneration, reimbursements and balances are excluded from the
numerator and retained as extracted evidence. Existing Module D bands
(<5 → 3, ≤15 → 1, else 0 of 3) unchanged.

**K6 — change in RPT revenue exposure (`rpt_pct_of_revenue_growth`).**
The share above is computed for the latest two comparable audited
financial years; the metric is the change between the two annual
shares, in percentage points (latest − prior). It is consumed by the
existing K6 rule (`> 40` triggers, config unchanged). A declining share
is negative and cannot trigger. A zero prior-year share needs no
division: the change is the latest share minus zero. Both annual
shares are reproducible from the preserved transaction evidence,
financial periods and the formulas recorded in
`CanonicalInputBuilder._derive_rpt_metrics`.

**Edge rules (deterministic, fail-closed).** A year's numerator is
zero only when eligible categories are disclosed in the note but no
amount is disclosed for that year (`-` cells); missing revenue,
non-positive revenue, unknown/unconvertible RPT units, missing
periods, or the absence of any eligible transaction leave the fields
null (Module D UNKNOWN / K6 UNVERIFIED). Amounts are converted into
the filing's reporting unit via INR lakh/crore/million/billion
factors. Curated/base-supplied values always win; derivation only
fills nulls, and only when RPT extractions are present (so
fixture-fallback behaviour and the golden record are unchanged).

**Implementation.** `CanonicalInputBuilder._derive_rpt_metrics`
(extraction builder — the canonical-mapping layer) computes the two
existing schema fields from the RPT extractions + financial periods;
`derived.py` metric formulas were intentionally left byte-identical
because formula text feeds the golden result hash (verified:
`e84f8bc0…` preserved). Vishal result: FY2026 share
(2,260.49 + 1,750.07) / 33,867.73 = **11.8418%**; FY2025
(3,091.60 + 798.16) / 31,851.62 = **12.2126%**; change **−0.3708 pp**
(declining) → K6 CLEAR, Module D `rpt` SCORED 1/3 under the existing
band. New Vishal runtime evaluations therefore differ from before
(K6 UNVERIFIED → CLEAR; D `rpt` UNKNOWN → SCORED) solely because of
this approved integration; historical records are not rewritten.

A canonical structured field (e.g. `governance.related_party_transactions`
as data, not only evidence) would still require a schema decision; it
is not added here.

## K5 boundary

Untouched. K5's >50% threshold and its treatment of unquantified
contingent liabilities are unchanged; the previously identified
unascertainable-recovery language in Note 42(a)(i) is neither extracted
as `unquantified=True` nor used to clear K5. That remains a separate
policy decision.

## Tests

`tests/test_rpt_extraction.py` (6 tests): two synthetic issuers with
distinct names/layouts/units (wrapped names, split headers, `-` cells,
balances exclusion, crores, two-year layout); fail-closed no-note case;
real Vishal Note 47 extraction (category totals hand-verified, verbatim
quotes); real-PDF canonical mapping (evidence registered, scoring
fields null, no schema change); golden-fixture consumer invariance
(score 35.0, K6 UNVERIFIED, curated `rpt_pct_revenue` 6.67 untouched).

## Numerator basis — evidence added 2026-10-26, definition unchanged

Reading the scanned/dislocated disclosures (investigation §33) made one open question concrete
without answering it: the Paras summary that the engine reads (pp. 92-93) discloses no
revenue-type related-party row, while Note 34 §III-A adds "Revenue from sale of healthcare
services (excluding applicable taxes)" — 28.69 / 14.45 / 6.48 ₹ million for FY2026 / FY2025 /
FY2024 — under a heading stating that those transactions are **eliminated in consolidation**. The
denominator is *consolidated* revenue from operations (16,059.52 / 12,940.63 / 11,290.39 ₹
million), which by construction cannot contain eliminated intra-group revenue, and the
neighbouring "Outsourced medical services" rows state no direction.

Counting them would change the metric, not the extraction: the share would become
0.1788% / 0.1116% / 0.0574% (D `rpt` 3/3, K6 change +0.067 pp → still CLEAR). **Nothing was
redefined.** The approved definition stands, the fields stay null on this evidence, and the
choice is recorded for Ramki in §33.8: keep the consolidated basis (no eligible numerator for
Paras, UNKNOWN correct), or adopt a separate standalone-basis exposure metric with its own
standalone revenue denominator — never a consolidated denominator divided into intra-group
revenue.

## Numerator basis — owner decision 2026-10-27: the consolidated basis is retained

Ramki's decision (recorded verbatim in effect, not paraphrased into a new definition):

- **Retain the existing consolidated-basis definition** for Module D's related-party revenue
  metric (`governance.rpt_pct_revenue` = revenue-type related-party transactions / revenue from
  operations, latest audited FY, %; `governance.rpt_pct_of_revenue_growth` = change in that share
  between the latest two comparable audited FYs, in percentage points).
- **Do not include transactions eliminated in consolidation in the numerator** unless the existing
  definition and the accounting evidence explicitly support their inclusion. The metric is
  divided by *consolidated* revenue, which by construction cannot contain eliminated intra-group
  revenue, so the two bases are never mixed.
- **Keep the metric UNKNOWN where qualifying consolidated-basis revenue cannot be established.**
- **Do not substitute zero for missing evidence.**
- Any **standalone-basis exposure metric must be separately defined** and must use a **matching
  standalone revenue denominator**. It is not implemented, and no field, weight or threshold is
  changed by this decision.

What this changed in the shared path (no definition change, one fail-closed tightening):

| Behaviour | Before | Now |
|---|---|---|
| A revenue-type row whose disclosure says it is eliminated in consolidation | would have been counted if a reader ever emitted it | excluded — `rpt_categories.is_consolidation_eliminated` reads the row's own verbatim text (nature, printed label, captured heading); no category name and no issuer name is involved |
| A year for which the note states no eligible amount | numerator filled with `0.0` and a share computed | that year has **no** share; absence of a disclosed amount is missing evidence, not a disclosed nil |
| The latest audited FY has no established qualifying amount | older year's share could become "latest" | `rpt_pct_revenue` **and** `rpt_pct_of_revenue_growth` stay null (UNKNOWN) |
| The preceding comparable FY has no established share | change computed against a zero prior | growth stays null; the latest share is still reported when it is established |

Effect on the issuers on record: **none.** Vishal Nirmiti keeps 11.8418% and −0.3708 pp (both years
state their amounts), Jio Platforms keeps 4.3094% and −0.1141 pp, Paras keeps null/null (its
summary discloses no revenue-type related-party row, and Note 34 §III-A is marked as eliminated in
consolidation — the case this decision is about), R.K. Fashion keeps null/null and 43.0.

Tests: `tests/test_module_d_consolidated_basis_20261027.py` (7 tests: the wording test, the
per-row exclusion, the exclusion not hiding a supported row, missing amount → unknown, latest year
must be established, a properly disclosed year still counted in full, and the Paras filing keeping
both fields null). `tests/test_rpt_extraction.py::test_derivation_unit_conversion_and_zero_prior`
became `…_and_no_zero_prior`: it used to assert that a prior year with no stated amount contributes
a zero share, which is the substitution this decision forbids; it now asserts the change is null
while the latest share is still computed.
