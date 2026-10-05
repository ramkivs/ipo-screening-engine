# ARENA EXECUTION PROMPT

## IPO Screening & Qualification Engine --- v1.5 Correctness-Hardening + Rebuild

### Mission

Implement a robust, deterministic, auditable **IPO Screening &
Qualification Engine** for Indian mainboard IPOs.

The current artifacts were produced by Claude and are being supplied as
**reference/prototype artifacts only**. Do not assume the current
implementation is architecturally correct. Redesign where necessary.

The final engine must:

1.  screen and qualify IPOs;
2.  produce deterministic 0--100 scores;
3.  handle missing/unverified data safely;
4.  implement sector/structure overlays correctly;
5.  apply knockout rules safely;
6.  validate financial/source integrity;
7.  preserve source-level evidence;
8.  support Preliminary and Final evaluations;
9.  write results to Excel;
10. preserve every evaluation historically and immutably;
11. support post-listing tracking/back-testing;
12. reproduce historical results exactly.

------------------------------------------------------------------------

# 1. AUTHORITATIVE ARTIFACTS

The following artifacts are supplied in this task:

1.  `IPO Screening Engine v 1.3 — Specification.md`
    -   Current specification file; contents identify themselves as
        v1.4.
    -   Treat the **new v1.5 specification supplied with this prompt as
        the target contract**.
2.  `ipo-config.json`
    -   Current Claude scoring configuration.
    -   Use as policy/reference, but validate and modify as required by
        v1.5.
3.  `ipo-input.schema.json`
    -   Current canonical input schema.
    -   Use as starting point; revise as required by the v1.5
        evidence/status model.
4.  `ipo-scorer_4.html`
    -   Current Claude implementation.
    -   Reference implementation only.
    -   Do not preserve defects merely for compatibility.
5.  `VISHAL-NIRMITI-LIMITED.json`
    -   Test input/reference fixture.
6.  `U01122MH1994PLC185445-vishal nirmiti.pdf`
    -   RHP/source document for the Vishal Nirmiti fixture.

------------------------------------------------------------------------

# 2. REQUIRED REFERENCE REVIEW

Before changing code:

1.  Read the complete v1.5 specification.
2.  Read the complete current config.
3.  Read the complete current schema.
4.  Inspect the current implementation.
5.  Inspect the Vishal input.
6.  Use the Vishal RHP as ground truth where relevant.
7.  Produce a traceability matrix mapping:
    -   specification requirement
    -   current implementation
    -   gap
    -   target implementation
    -   test coverage.

Do not silently discard a requirement.

------------------------------------------------------------------------

# 3. CRITICAL CORRECTIONS REQUIRED

The current Claude implementation has known correctness problems.
Address all of these.

## 3.1 Unknown must never become favorable

Do not use constructs equivalent to:

``` js
x || 0
```

for material financial, ownership, governance, valuation or market
fields.

Represent:

-   VALUE
-   UNKNOWN
-   NOT_APPLICABLE

explicitly.

Examples that must remain UNKNOWN when not disclosed:

-   GCP amount shown as `[●]`;
-   promoter pre-issue holding;
-   seller classification;
-   pre-IPO placement history;
-   cash/debt if absent;
-   governance facts;
-   knockout facts.

Do not convert GCP `[●]` into the 25% legal ceiling.

------------------------------------------------------------------------

# 4. TRI-STATE KNOCKOUTS

Every knockout must return:

-   `TRIGGERED`
-   `CLEAR`
-   `UNVERIFIED`

Never interpret a missing knockout input as CLEAR.

`UNVERIFIED` must list missing inputs and evidence requirements.

------------------------------------------------------------------------

# 5. SCHEMA VALIDATION

Implement actual JSON Schema validation before scoring.

The current Vishal fixture contains values such as seller
`pre_issue_shares` represented as a string. Do not rely on JavaScript
coercion.

Invalid type/schema → scoring must stop.

Then run semantic validation.

------------------------------------------------------------------------

# 6. CONFIG VALIDATION

At configuration load:

-   validate schema;
-   validate operators;
-   validate metric references;
-   validate categorical maps;
-   validate overlay replacement references;
-   validate module sums;
-   validate total = 100;
-   validate no criterion is double-counted;
-   validate all overlay replacement totals.

Invalid config → **do not score**.

Do not merely attach a warning and continue.

------------------------------------------------------------------------

# 7. SECTOR OVERLAYS

All declared sector overlays must be genuinely implemented.

At minimum:

### Financial

-   NIM/cost-income trend;
-   ROA/ROE peer quartile;
-   asset quality;
-   CRAR/Tier-1 buffer;
-   ROE-adjusted P/B.

### EPC/real estate

-   CFO/order-book exception;
-   net debt/equity trend;
-   project-debt interest cover;
-   receivable trend test.

### Loss-making/new-age

-   contribution margin;
-   operating loss narrowing;
-   cash runway;
-   P/S or EV/Sales.

### Cyclical

-   5Y margin normalization;
-   mid-cycle P/E;
-   mid-cycle EV/EBITDA.

If an overlay is selected and required metrics are not implemented, fail
configuration validation rather than scoring the missing overlay as
zero.

------------------------------------------------------------------------

# 8. GROWTH SEMANTICS

Do not call a latest/oldest calculation over three FY observations "3Y
CAGR".

Use:

`revenue_cagr_2y_from_3fy`

for three full FY observations.

Optionally calculate a true 3Y CAGR when four full FY observations
exist.

Apply the same convention to PAT CAGR.

------------------------------------------------------------------------

# 9. WEIGHTED COMPLETENESS

Do not calculate completeness by counting fields/criteria.

Calculate weighted completeness using available evaluable points.

Also report critical-data completeness separately for:

-   knockouts;
-   valuation;
-   governance;
-   market.

A 97% overall completeness score must not hide a missing knockout field.

------------------------------------------------------------------------

# 10. STALENESS

Peer multiples older than the configured freshness threshold must be:

`STALE`

not simply a warning.

Do not silently use stale valuation data as current.

Produce valuation score/range reflecting the unavailable current
valuation input.

Apply timestamp validation to market snapshots.

------------------------------------------------------------------------

# 11. AUDITOR LOGIC

Separate:

-   auditor changes count;
-   repeated EOM;
-   qualified opinion;
-   EOM/CARO;
-   clean opinion.

Do not classify a single auditor change as equivalent to repeated
instability unless policy explicitly says so.

Qualified/adverse/disclaimer remains a knockout.

------------------------------------------------------------------------

# 12. PROVENANCE

Every material input must have evidence.

Minimum evidence:

-   source ID;
-   document/source;
-   page/table/section or structured-source reference;
-   source timestamp/as-of;
-   extraction method;
-   verification status.

Derived metric must record:

-   formula;
-   input metrics;
-   result.

------------------------------------------------------------------------

# 13. IMMUTABLE EVALUATION RECORD

Every evaluation must receive:

-   evaluation_id
-   IPO ID
-   mode
-   timestamp
-   engine version
-   specification version
-   config version
-   input snapshot hash
-   source manifest hash
-   result hash

Persist a complete machine-readable evaluation record before generating
Excel.

Never overwrite prior evaluations.

------------------------------------------------------------------------

# 14. EXCEL REQUIREMENT

Excel is mandatory.

Generate:

`IPO_Screening_History.xlsx`

with at least:

1.  IPO_Master
2.  Evaluations
3.  Module_Scores
4.  Criteria_Detail
5.  Knockouts
6.  Penalties
7.  Missing_Unverified
8.  Evidence
9.  Market_Snapshots
10. Peer_Snapshots
11. Post_Listing
12. Backtest
13. Config_Versions
14. Run_Log

Historical evaluations must be append-only.

A corrected/re-run evaluation creates a new evaluation ID.

Do not overwrite historical score rows.

Excel is a projection of the immutable evaluation records, not the
calculation engine.

------------------------------------------------------------------------

# 15. PRELIMINARY / FINAL

Implement both.

### Preliminary

Use information available after price band/anchor stage.

Clearly identify pending information and score range.

### Final

Freeze the relevant Day-3/closing snapshot.

Persist it permanently.

If Final differs from Preliminary, record the delta.

Never mutate Preliminary.

------------------------------------------------------------------------

# 16. EXTRACTION

The current Claude browser regex/PDF extraction can be reused only as an
adapter if useful.

Do not make raw PDF extraction the scoring layer.

Required:

``` text
PDF/source
→ extraction
→ candidate values
→ evidence
→ canonical schema
→ validation
→ scoring
```

LLM extraction may assist but cannot bypass validation.

------------------------------------------------------------------------

# 17. SECURITY

Do not make a distributed production client depend on pasted
browser-side long-lived API keys.

Use a backend/provider adapter for shared/deployed operation.

Local/manual mode is acceptable for development.

------------------------------------------------------------------------

# 18. VISHAL NIRMITI REGRESSION FIXTURE

Use the supplied Vishal Nirmiti RHP and JSON as a comprehensive golden
fixture.

Specifically verify:

-   price band;
-   fresh issue;
-   promoter-group OFS;
-   1% QIB structure;
-   FY2024--FY2026 financials;
-   post-issue valuation;
-   stale peer data;
-   customer concentration;
-   contingent liabilities;
-   litigation;
-   related parties;
-   auditor/EOM information;
-   `[●]` GCP handling;
-   promoter selling;
-   receivable trend;
-   final score;
-   confidence/range.

The expected behavior is more important than reproducing the current
Claude score.

------------------------------------------------------------------------

# 19. REQUIRED TEST MATRIX

Create tests for:

1.  normal profitable IPO;
2.  pure OFS;
3.  qualified audit;
4.  going-concern uncertainty;
5.  negative net worth;
6.  promoter pledge \>25%;
7.  active SEBI/ED action;
8.  OFS \>80% + declining profits;
9.  K4 combined-sale condition;
10. contingent liabilities;
11. unquantified contingent liabilities;
12. RPT growth;
13. stale peers;
14. missing GCP;
15. missing promoter holding;
16. invalid schema;
17. invalid config;
18. financial institution overlay;
19. EPC overlay;
20. real-estate overlay;
21. loss-making overlay;
22. cyclical overlay;
23. retail-heavy structure overlay;
24. Preliminary evaluation;
25. Final evaluation;
26. Preliminary-to-Final delta;
27. historical rerun;
28. Excel append-only behavior;
29. post-listing updates;
30. reproducibility hash.

------------------------------------------------------------------------

# 20. HISTORICAL REPRODUCIBILITY TEST

This is mandatory:

``` text
same input snapshot
+ same source snapshot
+ same config
+ same engine version
=
same result hash
```

If not, identify and eliminate hidden nondeterminism.

------------------------------------------------------------------------

# 21. REQUIRED DELIVERABLES FROM ARENA

Produce:

### Architecture

-   architecture document;
-   module/component map;
-   data-flow diagram;
-   persistence model;
-   Excel data model.

### Specification implementation

-   revised canonical schema;
-   revised config;
-   derived metric definitions;
-   validation rules;
-   knockout engine;
-   scoring engine;
-   confidence/range engine.

### Persistence

-   immutable evaluation record;
-   source manifest;
-   historical ID/hash model.

### Excel

-   workbook generator;
-   workbook schema;
-   sample workbook from Vishal fixture.

### Tests

-   complete regression suite;
-   Vishal golden test;
-   validation failure tests;
-   overlay tests;
-   reproducibility test.

### Documentation

-   README;
-   runbook;
-   scoring methodology;
-   evidence/provenance guide;
-   historical data/versioning guide.

------------------------------------------------------------------------

# 22. IMPORTANT --- DO NOT STOP AT REVIEW

The goal is not merely to report defects.

Proceed to implement the corrected architecture.

If an existing Claude artifact conflicts with the v1.5 specification:

**v1.5 specification wins.**

If the specification itself contains an ambiguity discovered during
implementation:

1.  identify it;
2.  propose the minimum policy decision;
3.  ask Ramki only when an actual policy choice is required;
4.  do not silently invent a policy.

------------------------------------------------------------------------

# 23. ACCEPTANCE GATE

Do not declare complete until:

-   all P0 correctness defects are fixed;
-   all required overlays work;
-   unknown values remain unknown;
-   knockout tri-state works;
-   schema validation is enforced;
-   config validation blocks invalid configs;
-   stale data is handled correctly;
-   provenance exists;
-   score ranges work;
-   historical records are immutable;
-   Excel output is append-only;
-   Vishal regression passes;
-   reproducibility passes;
-   documentation is complete.

At completion provide:

1.  implementation summary;
2.  changed files;
3.  architecture decisions;
4.  spec-to-code traceability matrix;
5.  test results;
6.  Vishal Nirmiti result;
7.  Excel sample;
8.  known residual issues, if any;
9.  exact run/reproduction instructions.
