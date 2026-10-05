# IPO Screening & Qualification Engine --- Specification v1.5

**Status:** Proposed baseline for Arena implementation\
**Supersedes:** `IPO Screening Engine v 1.3 — Specification.md` (which
already contains v1.4 content)\
**Target:** Indian mainboard IPOs (NSE/BSE), INR, SEBI ICDR framework\
**Primary objective:** robust, deterministic, auditable IPO screening
and qualification with historically preserved Excel outputs.

------------------------------------------------------------------------

## 1. Executive Objective

The engine shall convert an IPO's RHP/DRHP, price-band/offer documents,
exchange data, market snapshots and comparable-company data into:

1.  a deterministic 0--100 screening score;
2.  a qualification verdict;
3.  knockout / red-flag findings;
4.  a confidence and data-completeness assessment;
5.  an explicit missing/unverified-data range;
6.  source-level evidence and provenance;
7.  a reproducible historical evaluation record;
8.  an Excel output that preserves every evaluation historically.

The engine is a **screening and qualification aid**, not an
investment-advice or return-guarantee system.

The engine must prefer **correct incompleteness over fabricated
completeness**. Unknown data must never silently become zero, a
favorable category, or a passed knockout.

------------------------------------------------------------------------

# 2. Scope

### In scope

-   Indian mainboard IPOs: fresh issue, OFS, or combination.
-   Offer structure and seller analysis.
-   Restated financial analysis.
-   Sector-specific financial analysis.
-   Post-issue valuation.
-   Peer comparison.
-   Promoter / governance / litigation / RPT analysis.
-   Business quality, concentration, moat and visibility.
-   Market / subscription / anchor / sentiment signals.
-   Knockouts and penalties.
-   Preliminary and Final evaluations.
-   Historical evaluation preservation.
-   Excel reporting.
-   Post-listing performance capture and back-testing.
-   Versioned configuration and reproducibility.

### Out of scope for this release

-   SME IPOs unless explicitly enabled by a separate configuration
    profile.
-   REIT / InvIT.
-   FPO / rights issues.
-   Automated bidding or order placement.
-   Intraday trading signals.
-   Tax advice.
-   Autonomous investment decisions.

------------------------------------------------------------------------

# 3. Non-Negotiable Design Principles

## 3.1 Deterministic scoring

For the same:

-   normalized input snapshot,
-   source snapshot,
-   scoring configuration version,
-   engine version,
-   mode,

the score and verdict must be identical.

## 3.2 Unknown is not zero

Every input and derived metric has one of:

-   `VALUE`
-   `UNKNOWN`
-   `NOT_APPLICABLE`

`0` is a numeric value, not an unknown marker.

The engine must not use JavaScript-style fallback expressions such as
`x || 0` for financial, market, ownership or governance inputs.

## 3.3 Three-state knockout evaluation

Every knockout must resolve to:

-   `TRIGGERED`
-   `CLEAR`
-   `UNVERIFIED`

`UNVERIFIED` must identify the missing evidence/inputs.

A missing knockout input must never be treated as `CLEAR`.

## 3.4 Evidence before score

Every material input must have:

-   value/status,
-   source,
-   source date/as-of,
-   document/page or structured-source reference,
-   extraction method,
-   verification status.

Derived metrics must identify their source inputs and formula.

## 3.5 Configuration is executable policy

Weights, thresholds, bands, overlays and verdict rules live in versioned
configuration.

The engine must validate the configuration before scoring and **refuse
to score with an invalid configuration**.

## 3.6 Excel is an output/preservation surface, not an implicit source of truth

Each evaluation must also have a machine-readable immutable evaluation
record (JSON or equivalent) containing the complete normalized input
snapshot, config version, source hashes, engine version, result,
evidence, assumptions and timestamps.

The Excel workbook is the human-analysis/reporting surface and must be
generated from the immutable evaluation record.

------------------------------------------------------------------------

# 4. Required Inputs

## 4.1 Offer

-   issuer
-   IPO identifier
-   price band
-   lot size
-   issue opening/closing dates
-   listing date when known
-   fresh issue
-   OFS
-   seller-wise OFS
-   seller type
-   seller pre-issue holding
-   shares sold
-   ICDR route
-   quota
-   anchor allocation
-   employee/shareholder discount
-   post-issue shares
-   promoter pre/post holdings
-   lock-in
-   pledge/encumbrance
-   pre-IPO placements

## 4.2 Financials

At least three full FY observations; four full FYs are preferred where
available.

For every period:

-   revenue
-   EBITDA where disclosed or reproducible
-   PAT
-   PBT
-   tax
-   EBIT where disclosed/reproducible
-   finance cost
-   depreciation
-   other income
-   net worth
-   total debt
-   cash/equivalents
-   CFO
-   capex
-   trade receivables
-   inventory where relevant
-   reporting unit
-   stub-period indicator

Sector-specific inputs:

### Financial institutions

-   CRAR
-   Tier 1
-   NIM
-   cost-to-income
-   GNPA
-   NNPA
-   provision coverage
-   ROA
-   ROE

### EPC / infra

-   order book
-   order-book/revenue
-   collections
-   receivable days
-   project debt
-   interest cover

### Real estate

-   pre-sales
-   collections
-   inventory
-   receivables
-   net debt

### Loss-making / new-age

-   contribution margin
-   operating loss
-   cash burn
-   post-issue cash
-   runway
-   EV/Sales / P/S inputs

### Cyclical

-   preferably five FYs
-   normalized/mid-cycle metrics

## 4.3 Governance

-   auditor name/type
-   audit opinion
-   EOM
-   CARO remarks
-   auditor changes and dates
-   CFO changes/resignations
-   KMP changes
-   board composition
-   independent-director count
-   promoter profile
-   promoter litigation
-   company litigation
-   regulatory actions
-   SEBI/ED actions
-   tax proceedings
-   related-party transactions
-   related-party revenue growth contribution
-   contingent liabilities, including whether any amount is unquantified

## 4.4 Business

-   business segments
-   market position
-   moat assessment inputs
-   customer concentration
-   supplier concentration
-   geography
-   capacity
-   utilization
-   order book
-   industry growth
-   industry scope and forecast period
-   major dependencies
-   regulatory dependence

## 4.5 Peers

Prefer 4--6 appropriate peers.

For each peer:

-   name
-   business comparability
-   listing date
-   price date
-   P/E
-   EV/EBITDA
-   P/B
-   P/S where relevant
-   ROCE/ROE
-   growth
-   source

Peers with insufficient listing history or materially mismatched
business models must be rejected or explicitly marked `UNUSABLE`.

## 4.6 Market snapshots

Every market value must carry:

-   as-of timestamp,
-   timezone,
-   source,
-   source timestamp where available.

Inputs include:

-   anchor quality
-   QIB/NII/retail/overall subscription
-   GMP
-   Nifty/regime
-   recent IPO listing performance

------------------------------------------------------------------------

# 5. Data Model

All values must preserve:

1.  raw source value;
2.  source unit;
3.  normalized value;
4.  normalization formula;
5.  source reference;
6.  confidence/verification status.

Example:

``` json
{
  "metric": "revenue",
  "period": "FY2026",
  "raw_value": 33867.73,
  "raw_unit": "INR_LAKHS",
  "normalized_value": 338.6773,
  "normalized_unit": "INR_CRORES",
  "status": "VERIFIED",
  "source": {
    "document": "RHP",
    "page": 366,
    "section": "Restated Financial Statements"
  }
}
```

No field may use numeric zero to mean "not disclosed".

------------------------------------------------------------------------

# 6. Architecture

## 6.1 Required architecture

``` text
                 ┌──────────────────────┐
                 │ RHP / DRHP / Exchange │
                 │ Market / Peer Sources │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Ingestion / Extraction│
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Canonical Input Model │
                 │ + Evidence/Provenance │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Schema Validation     │
                 │ Semantic Validation   │
                 │ Cross-checks          │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Derived Metrics       │
                 │ Deterministic         │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Knockout Evaluation   │
                 │ CLEAR / TRIGGERED /   │
                 │ UNVERIFIED            │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Sector/Structure      │
                 │ Overlay Resolution    │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Deterministic Scorer  │
                 │ A–F / penalties       │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Confidence + Range    │
                 │ + Verdict             │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Immutable Evaluation  │
                 │ Record / Run Artifact │
                 └──────────┬───────────┘
                            ▼
              ┌────────────────────────────┐
              │ Excel Historical Workbook  │
              │ + Scorecard + Audit Sheets │
              └────────────────────────────┘
```

## 6.2 Separation of responsibilities

### Extraction layer

May use deterministic parsers, OCR, LLM-assisted extraction or manual
entry.

### Canonicalization layer

Converts extraction into the canonical schema and attaches evidence.

### Validation layer

Must be independent of scoring.

### Scoring layer

Must never scrape documents or infer missing source values.

### Persistence layer

Must preserve immutable evaluation runs.

### Reporting layer

Must not recompute scores differently from the scoring engine.

------------------------------------------------------------------------

# 7. Growth Definition

The previous specification used the label "3Y CAGR" while three FY
observations actually provide a two-year CAGR.

The canonical metric is now:

**`revenue_cagr_2y_from_3fy`**

For FY2024, FY2025, FY2026:

``` text
(FY2026 revenue / FY2024 revenue)^(1/2) - 1
```

If four full FY observations are available, an optional:

**`revenue_cagr_3y_from_4fy`**

may be reported.

The same convention applies to PAT CAGR.

------------------------------------------------------------------------

# 8. Financial Quality --- 25 Points

  ------------------------------------------------------------------------
  Criterion                                      Max Rule
  --------------------- ---------------------------- ---------------------
  Revenue CAGR                                     6 \>25%=6; 15--25%=4;
                                                     8--15%=2; \<8%=0

  Profit trend                                     5 Expanding=5;
                                                     stable=3; volatile=1;
                                                     declining/loss=0

  ROCE                                             5 \>20%=5; 15--20%=3;
                                                     10--15%=1; \<10%=0

  Cumulative CFO/PAT                               5 \>0.8=5; 0.5--0.8=3;
                                                     0--0.5=1; \<0=0

  Leverage                                         4 D/E\<0.5 & ICR\>5=4;
                                                     D/E\<1=2; D/E 1--2=1;
                                                     \>2=0
  ------------------------------------------------------------------------

`Cumulative CFO/PAT = ΣCFO / ΣPAT`.

If the denominator is non-positive, the metric is
`UNVERIFIED`/`NOT_APPLICABLE` rather than forced to zero.

------------------------------------------------------------------------

# 9. Valuation --- 20 Points

Use post-issue share count and post-issue EPS.

  Criterion                                   Max
  ----------------------------------------- -----
  P/E vs peer median                            8
  EV/EBITDA or P/B, sector appropriate          4
  PEG / loss-making valuation replacement       4
  Recent sector IPO valuation                   4

### Critical valuation rule

A stale peer multiple is not automatically usable.

Peer valuation status:

-   `VALID`
-   `STALE`
-   `UNUSABLE`
-   `MISSING`

If valuation cannot be refreshed, the engine must produce a valuation
range and identify the affected points.

It must not silently score stale valuation data as current.

------------------------------------------------------------------------

# 10. Issue Structure & Proceeds --- 15 Points

Retain the existing 15-point framework, but require unknown-safe
semantics.

### GCP

If the RHP shows `[●]` or otherwise undisclosed GCP:

-   record `amount = UNKNOWN`;
-   record legal maximum separately;
-   do not substitute the maximum as the actual amount;
-   calculate a score range if the missing amount affects the criterion.

Example:

``` text
GCP disclosed amount: UNKNOWN
GCP legal maximum: 25% of fresh issue
```

------------------------------------------------------------------------

# 11. Governance --- 15 Points

Retain the 15-point framework.

Auditor status must distinguish:

-   clean/unqualified/no material instability;
-   EOM/CARO only;
-   repeated EOM or repeated auditor instability;
-   qualified/adverse/disclaimer → knockout.

Auditor change count and repeated EOM must be separate inputs.

------------------------------------------------------------------------

# 12. Business & Moat --- 15 Points

Retain the framework, with evidence-backed assessment.

Industry CAGR must include:

-   value,
-   scope (India/global),
-   forecast period,
-   source,
-   whether it is the issuer's primary industry.

Customer concentration must use the higher of relevant customer/supplier
concentration where the rule calls for it.

------------------------------------------------------------------------

# 13. Market & Demand --- 10 Points

Market data must be snapshot-based.

No market input without:

-   timestamp,
-   source,
-   mode applicability.

GMP remains sentiment-only and cannot dominate the result.

------------------------------------------------------------------------

# 14. Sector Overlays

Sector overlays are mandatory implementations, not decorative config.

## Financial

Implement all:

-   NIM/cost-income trend;
-   ROA/ROE peer quartile;
-   asset quality;
-   CRAR/Tier-1 buffer;
-   ROE-adjusted P/B.

## EPC / real estate

Implement:

-   CFO/order-book exception;
-   net debt/equity trend;
-   project debt interest cover;
-   receivable trend condition.

## Loss-making

Implement:

-   contribution margin;
-   operating loss narrowing;
-   cash runway;
-   EV/Sales or P/S.

## Cyclical

Implement:

-   five-year average margin where available;
-   mid-cycle P/E;
-   mid-cycle EV/EBITDA.

If an overlay is selected but one of its required metrics is not
implemented, the engine must fail validation rather than silently score
zero.

------------------------------------------------------------------------

# 15. Structure Overlay

Retain the retail-heavy overlay.

The overlay must be validated to ensure:

-   removed criteria are actually removed;
-   replacement criteria exist;
-   replacement maxima reconcile;
-   module total remains correct.

------------------------------------------------------------------------

# 16. Knockouts

Retain K1--K6 but use tri-state evaluation.

## K1

Qualified/adverse/disclaimer, going-concern uncertainty, or negative net
worth.

## K2

Promoter pledge \>25% or active SEBI/ED action.

## K3

OFS \>80% and declining profits.

## K4

Combined promoter/PE-VC selling \>50%, promoter exit/\<20%, and weak
financials.

## K5

Contingent liabilities \>50% of net worth or unquantified material
contingent liabilities.

## K6

Related parties drive \>40% of revenue growth.

### Knockout output

``` text
K1: CLEAR
K2: UNVERIFIED
K3: CLEAR
...
```

For `UNVERIFIED`, show missing evidence.

------------------------------------------------------------------------

# 17. Penalties

Retain the existing penalties, but do not evaluate a penalty against
fabricated data.

Penalty status:

-   `TRIGGERED`
-   `CLEAR`
-   `UNVERIFIED`

An unverified penalty is included in the uncertainty range, not
automatically applied or ignored.

------------------------------------------------------------------------

# 18. Missing Data / Confidence / Score Range

This is a major upgrade.

For every scoring criterion:

``` text
AVAILABLE
UNKNOWN
NOT_APPLICABLE
```

The engine calculates:

### Base score

Score from available inputs.

### Lower bound

Assume unknown scoring items contribute zero and unknown penalties are
applied where reasonably possible.

### Upper bound

Assume unknown positive scoring items earn their full available points
and unknown penalties are not triggered.

### Weighted completeness

``` text
available evaluable points / total evaluable points × 100
```

Confidence:

-   High ≥95%
-   Medium ≥80%
-   Low \<80%

A knockout with `UNVERIFIED` status prevents a normal "CLEAR"
interpretation.

If the score range crosses a verdict band, output:

`VERDICT_UNCERTAIN`

If critical safety information is missing, output:

`INSUFFICIENT_DATA`

rather than `AVOID` merely because the score is incomplete.

------------------------------------------------------------------------

# 19. Preliminary vs Final

## Preliminary

Generated after price band / before opening, using available pre-open
information.

It must explicitly show:

-   points available;
-   points pending;
-   score range;
-   provisional verdict;
-   missing market inputs.

## Final

Generated at a defined evaluation timestamp on/after closing.

Final must freeze:

-   subscription snapshot;
-   market snapshot;
-   GMP snapshot;
-   peer valuation snapshot;
-   configuration version;
-   source hashes.

A Final evaluation is never overwritten.

If Final differs from Preliminary, store a delta record.

------------------------------------------------------------------------

# 20. Validation Layer

Validation is a hard gate.

## Schema

Use actual JSON Schema validation.

Invalid types, missing required fields and malformed structures stop
scoring.

## Financial

Validate:

-   PBT/tax/PAT relationship;
-   balance sheet;
-   units;
-   derived EBITDA;
-   share-count arithmetic;
-   post-issue EPS.

## Cross-source

Compare RHP vs exchange/secondary source within configured tolerance.

Differences must be reported, not silently resolved.

## Proceeds

Validate GCP/acquisition/legal limits.

## OFS

Validate 6(2) selling limits where applicable.

## Peers

Validate:

-   listing age;
-   business comparability;
-   stale date;
-   source;
-   outlier handling.

## Configuration

Reject invalid config.

Assertions:

-   every criterion belongs to exactly one module after overlays;
-   module maxima reconcile;
-   total = 100;
-   overlay replacements reconcile;
-   all referenced metrics exist;
-   all operators are valid;
-   all categorical mappings are complete.

------------------------------------------------------------------------

# 21. Historical Persistence

This is mandatory.

Every evaluation receives:

-   `evaluation_id`
-   `ipo_id`
-   `evaluation_mode`
-   `evaluation_timestamp`
-   `engine_version`
-   `spec_version`
-   `config_version`
-   `input_snapshot_hash`
-   `source_manifest_hash`
-   `result_hash`

Never overwrite a prior evaluation.

A rerun creates a new immutable evaluation.

### Minimum historical lifecycle

``` text
PRELIMINARY
   ↓
FINAL
   ↓
POST_LISTING_1W
   ↓
POST_LISTING_1M
   ↓
POST_LISTING_6M
```

------------------------------------------------------------------------

# 22. Excel Historical Workbook

The Excel output is a required deliverable.

Recommended workbook sheets:

1.  `IPO_Master`
2.  `Evaluations`
3.  `Module_Scores`
4.  `Criteria_Detail`
5.  `Knockouts`
6.  `Penalties`
7.  `Missing_Unverified`
8.  `Evidence`
9.  `Market_Snapshots`
10. `Peer_Snapshots`
11. `Post_Listing`
12. `Backtest`
13. `Config_Versions`
14. `Run_Log`

### Historical rule

Never replace historical rows.

Each evaluation is an append-only row keyed by `evaluation_id`.

### Excel must contain

-   score;
-   verdict;
-   score range;
-   confidence;
-   module scores;
-   knockout states;
-   penalties;
-   missing inputs;
-   source evidence;
-   timestamps;
-   versions;
-   post-listing outcomes when available.

------------------------------------------------------------------------

# 23. Immutable Evaluation Record

Before Excel generation, persist a complete machine-readable record.

Suggested structure:

``` text
evaluation/
  evaluation.json
  input.json
  evidence.json
  market.json
  peers.json
  result.json
  manifest.json
```

The manifest records hashes of all source and result artifacts.

Excel is generated from these records.

------------------------------------------------------------------------

# 24. Auditability

The engine must be able to answer:

-   Why did this criterion receive this score?
-   Which source supplied the value?
-   Which page/table supplied it?
-   What formula produced the derived metric?
-   Which config version supplied the threshold?
-   What was unknown at the time?
-   What market data was current at the time?
-   Can the exact historical score be reproduced?

------------------------------------------------------------------------

# 25. Security / Extraction

LLM-assisted extraction may be used, but:

-   extracted values must enter the canonical schema;
-   schema validation must run afterward;
-   source evidence must be attached;
-   LLM output must not directly control scoring;
-   browser-exposed API keys are not acceptable for a distributed
    production implementation.

------------------------------------------------------------------------

# 26. Testing Requirements

Create a golden regression suite.

At minimum:

1.  Vishal Nirmiti --- normal/mainboard/retail-heavy.
2.  Pure OFS IPO.
3.  Qualified audit opinion.
4.  Missing GCP.
5.  Missing promoter holding.
6.  Stale peers.
7.  Financial institution.
8.  EPC with negative CFO but strong order book.
9.  Loss-making/new-age.
10. Cyclical company.
11. Unquantified contingent liabilities.
12. Active SEBI/ED action.
13. 6(2) OFS breach.
14. Invalid schema/type.
15. Invalid config.
16. Preliminary → Final delta.
17. Historical rerun reproducibility.

Every bug discovered becomes a regression test.

------------------------------------------------------------------------

# 27. Acceptance Criteria

Arena implementation is accepted only when:

-   schema validation is enforced;
-   unknown values cannot become favorable values;
-   all sector overlays are implemented or explicitly rejected at
    config-validation time;
-   knockout state is tri-state;
-   stale valuation data cannot silently score as current;
-   GCP `[●]` is not converted into an assumed actual amount;
-   weighted completeness and score ranges work;
-   config invalidity blocks scoring;
-   every score has evidence/provenance;
-   Preliminary and Final are immutable historical records;
-   Excel output is append-only and historically preserved;
-   exact prior results are reproducible;
-   golden regression suite passes;
-   Vishal Nirmiti test demonstrates expected unknown/stale behavior.

------------------------------------------------------------------------

# 28. Build Sequence

### Phase 0 --- Contract

Freeze:

-   v1.5 specification;
-   canonical schema;
-   configuration;
-   evidence model;
-   historical record model.

### Phase 1 --- Core correctness

Implement:

-   schema validation;
-   unknown semantics;
-   derived metrics;
-   validation;
-   tri-state knockouts;
-   config compiler.

### Phase 2 --- Scoring

Implement:

-   A--F;
-   overlays;
-   penalties;
-   confidence/ranges;
-   Preliminary/Final.

### Phase 3 --- Persistence

Implement:

-   immutable evaluation record;
-   source manifest;
-   historical IDs/hashes.

### Phase 4 --- Excel

Implement append-only workbook generation.

### Phase 5 --- Extraction

Integrate extraction only after the deterministic core is correct.

### Phase 6 --- Back-testing

Implement post-listing tracking and calibration.

------------------------------------------------------------------------

# 29. Important Implementation Rule

Do not preserve the current Claude implementation merely because it
already exists.

It is a reference implementation/prototype.

Arena may redesign the architecture where necessary, provided the
resulting implementation satisfies this specification and preserves the
required scoring policy.

Correctness, auditability and historical reproducibility take priority
over minimizing code changes.
