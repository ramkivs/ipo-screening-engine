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

## Metric semantics — decision still required (scoring NOT wired)

The existing definitions are **not complete enough to wire scoring
without inventing policy**:

- Module D `rpt_pct_revenue` — config label "Related-party transactions
  (% revenue/costs)", derived formula "related-party transactions /
  revenue, latest FY, %". Unspecified: which transaction categories form
  the numerator (revenue-type only — sale of goods/services, job-work,
  rent/interest received — or all transactions including purchases?);
  why the label says "revenue/costs"; whether remuneration/balances
  count.
- K6 `rpt_pct_of_revenue_growth` — formula "share of revenue growth
  attributable to related parties, %", trigger > 40%. Unspecified:
  numerator categories; the growth window (latest FY vs prior FY, or
  two-year); the denominator (total revenue growth over the same
  window); behaviour when total revenue growth is zero/negative or RPT
  revenue declines; stub-period handling.

**Decision needed (Ramki):** approve precise numerator/denominator/
window/sign rules for both metrics. Candidate formulations recorded for
approval, NOT adopted: (D) revenue-type RPT categories ÷ latest-FY
revenue; (K6) Δ(revenue-type RPT) ÷ Δ(total revenue), latest vs prior
FY, undefined (UNKNOWN) when Δ(total revenue) ≤ 0. Until approved,
`rpt_pct_revenue`/`rpt_pct_of_revenue_growth` remain null on the
runtime path, Module D `rpt` stays UNKNOWN and K6 stays UNVERIFIED —
now with the underlying transaction evidence extracted and citable.

A canonical structured field (e.g. `governance.related_party_transactions`
as data, not only evidence) likewise requires a schema decision; it is
not added here.

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
