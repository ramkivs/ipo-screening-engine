# IPO Screening & Qualification Engine --- Technical Design v1.5

## 1. Purpose

This design translates the v1.5 specification into an implementation
architecture suitable for a robust, deterministic IPO screening engine
with historical Excel preservation.

The current Claude artifacts are treated as **reference/prototype
material**, not as an architecture that must be preserved.

------------------------------------------------------------------------

## 2. Design Decision

### Adopt a layered architecture

``` text
Sources
  ↓
Extraction
  ↓
Canonical Data + Evidence
  ↓
Schema Validation
  ↓
Semantic / Cross-source Validation
  ↓
Derived Metrics
  ↓
Overlay Resolution
  ↓
Knockout Evaluation
  ↓
Deterministic Scoring
  ↓
Confidence / Range / Verdict
  ↓
Immutable Evaluation Record
  ↓
Excel Projection
  ↓
Post-listing / Backtest
```

The scorer must never directly consume raw PDF text.

------------------------------------------------------------------------

## 3. Components

### 3.1 Source Adapter

Responsibilities:

-   accept RHP/DRHP PDFs;
-   exchange snapshots;
-   peer snapshots;
-   market snapshots;
-   manually supplied structured inputs.

Output:

`SourceDocument` / `SourceSnapshot`.

Every source receives:

-   source ID;
-   retrieval timestamp;
-   source timestamp;
-   content hash;
-   source type;
-   URI/file reference.

------------------------------------------------------------------------

### 3.2 Extraction Layer

Possible extraction mechanisms:

-   deterministic PDF extraction;
-   table extraction;
-   OCR;
-   LLM-assisted extraction;
-   manual correction.

Extraction output must never directly enter scoring.

Output:

`RawExtraction`.

Each extracted field should carry:

-   candidate value;
-   raw text;
-   page;
-   table/section;
-   extraction method;
-   extraction confidence.

------------------------------------------------------------------------

### 3.3 Canonical Data Layer

Convert extraction into:

`IPOInput`.

Each value is:

``` text
value
status
unit
period
source_ref
evidence_ref
```

Statuses:

-   VERIFIED
-   UNVERIFIED
-   UNKNOWN
-   NOT_APPLICABLE

------------------------------------------------------------------------

## 4. Validation Engine

Validation has three layers.

### 4.1 Structural validation

JSON Schema.

Reject:

-   wrong types;
-   missing required fields;
-   invalid enums;
-   malformed arrays.

### 4.2 Semantic validation

Examples:

-   share counts cannot be negative;
-   fresh + OFS must reconcile;
-   post-issue shares must reconcile;
-   seller shares sold cannot exceed seller holding;
-   percentages must be in valid ranges;
-   financial periods must be ordered;
-   currency units must be known.

### 4.3 Financial/source validation

Examples:

-   PAT/PBT/tax;
-   balance sheet;
-   EBITDA;
-   post-issue EPS;
-   RHP vs exchange;
-   peer staleness;
-   proceeds limits;
-   OFS route rules.

Validation results are persisted.

------------------------------------------------------------------------

## 5. Derived Metrics Engine

Derived metrics must be pure functions.

``` text
derive(input_snapshot, config)
    → derived_metrics
```

No source access.

No mutation.

No default-to-zero.

Each metric returns:

``` json
{
  "value": null,
  "status": "UNKNOWN",
  "formula": "...",
  "inputs": ["..."]
}
```

This prevents accidental favorable defaults.

------------------------------------------------------------------------

## 6. Overlay Resolver

The resolver produces an explicit effective scoring plan.

Example:

``` json
{
  "profile": "epc_real_estate",
  "removed": ["cfo_quality", "leverage"],
  "added": ["cfo_or_orderbook", "net_debt_trend_icr"],
  "effective_module_totals": {
    "A": 25,
    "B": 20
  }
}
```

The resolver must validate the resulting configuration before scoring.

------------------------------------------------------------------------

## 7. Knockout Engine

Every rule returns:

``` text
TRIGGERED
CLEAR
UNVERIFIED
```

A rule evaluation includes:

-   rule ID;
-   state;
-   inputs;
-   evidence;
-   explanation.

Example:

``` json
{
  "rule_id": "K1",
  "state": "UNVERIFIED",
  "missing": ["going_concern_uncertainty"],
  "explanation": "The supplied input does not establish whether going-concern uncertainty exists."
}
```

------------------------------------------------------------------------

## 8. Scoring Engine

The scorer is deterministic.

``` text
score(input, derived, effective_config, mode)
```

Each criterion returns:

``` json
{
  "criterion_id": "A1",
  "status": "SCORED",
  "score": 4,
  "max": 6,
  "metric": "revenue_cagr_2y_from_3fy",
  "value": 18.7,
  "reason": "...",
  "evidence": [...]
}
```

Unknown criterion:

``` json
{
  "status": "UNKNOWN",
  "score": null,
  "max": 6
}
```

The aggregate scorer then computes:

-   base score;
-   lower bound;
-   upper bound;
-   available points;
-   confidence.

------------------------------------------------------------------------

## 9. Confidence Engine

Use weighted point availability.

``` text
completeness =
available_evaluable_positive_points /
total_evaluable_positive_points
```

Also separately calculate:

-   critical-data completeness;
-   knockout completeness;
-   valuation-data completeness;
-   market-data completeness.

A high overall completeness must not hide a missing critical knockout
field.

------------------------------------------------------------------------

## 10. Valuation Engine

Valuation receives an explicit peer snapshot.

Each peer:

``` text
peer_id
business_match
listing_date
valuation_date
source
P/E
EV/EBITDA
P/B
P/S
ROE
ROCE
```

Peer status:

-   VALID
-   STALE
-   UNUSABLE
-   MISSING

The engine must not silently substitute stale data.

------------------------------------------------------------------------

## 11. Historical Persistence

Every run creates an immutable:

`EvaluationRecord`.

Recommended ID:

``` text
IPOID-YYYYMMDD-HHMMSS-MODE-<short-hash>
```

Record contains:

-   IPO input snapshot;
-   evidence;
-   market snapshot;
-   peer snapshot;
-   derived metrics;
-   effective configuration;
-   validation results;
-   knockout results;
-   score;
-   penalties;
-   confidence;
-   range;
-   verdict;
-   engine/spec/config versions;
-   source hashes.

Never update an old record.

------------------------------------------------------------------------

## 12. Excel Projection

Excel is generated from EvaluationRecord.

### Workbook

`IPO_Screening_History.xlsx`

### Sheets

#### IPO_Master

One row per IPO.

#### Evaluations

One row per evaluation/run.

Columns include:

-   evaluation_id
-   ipo_id
-   company
-   mode
-   evaluation_timestamp
-   score
-   lower_bound
-   upper_bound
-   confidence
-   verdict
-   knockout_status
-   engine_version
-   spec_version
-   config_version
-   input_hash
-   result_hash

#### Module_Scores

One row per module per evaluation.

#### Criteria_Detail

One row per criterion.

#### Knockouts

One row per knockout.

#### Penalties

One row per penalty.

#### Missing_Unverified

One row per missing/unverified item.

#### Evidence

One row per evidence item.

#### Market_Snapshots

Immutable market observations.

#### Peer_Snapshots

Immutable peer observations.

#### Post_Listing

Listing/1W/1M/6M outcomes.

#### Backtest

Score vs realized outcome.

#### Config_Versions

Configuration history.

#### Run_Log

Execution status, validation status and errors.

------------------------------------------------------------------------

## 13. Historical Preservation Rules

Never:

-   delete an old evaluation;
-   overwrite an old score;
-   regenerate an old evaluation under a new config without creating a
    new evaluation ID.

A corrected extraction creates:

`evaluation_v2`.

A new config creates a new evaluation.

A new market snapshot creates a new evaluation.

Historical records remain immutable.

------------------------------------------------------------------------

## 14. Excel Integrity

Every Excel row should include:

-   evaluation_id;
-   source/evaluation timestamp;
-   result hash.

The workbook should be generated deterministically from stored
evaluation records.

Recommended:

-   freeze panes;
-   filters;
-   data validation;
-   formulas only where appropriate;
-   no manual score editing.

The displayed score should come from the persisted result, not an
editable Excel formula.

------------------------------------------------------------------------

## 15. Extraction Architecture

The current Claude `locate()`/regex approach may remain as an optional
extraction adapter but must not be the authoritative architecture.

Preferred:

``` text
PDF
 ↓
TOC / heading detection
 ↓
section extraction
 ↓
table extraction
 ↓
candidate fields
 ↓
evidence attachment
 ↓
canonical input
 ↓
validation
```

If an LLM extracts a field, the field remains `UNVERIFIED` until
validation/evidence checks pass.

------------------------------------------------------------------------

## 16. API-Key Security

Do not ship a browser application that requires users to paste a
long-lived model-provider API key into a distributed client.

For local development, a manual provider adapter may exist.

For shared/deployed use:

``` text
UI → backend/provider adapter → model API
```

Secrets remain server-side.

------------------------------------------------------------------------

## 17. Test Architecture

Use golden fixtures.

Each fixture contains:

``` text
input.json
expected_validation.json
expected_derived.json
expected_knockouts.json
expected_score.json
expected_verdict.json
```

The Vishal Nirmiti case becomes the first comprehensive regression
fixture.

Additional synthetic fixtures must test every knockout, overlay,
missing-data path and validation failure.

------------------------------------------------------------------------

## 18. Build Order

1.  Canonical schema.
2.  Evidence model.
3.  Config validator/compiler.
4.  Validation engine.
5.  Derived metric engine.
6.  Overlay resolver.
7.  Knockout engine.
8.  Scoring engine.
9.  Confidence/range engine.
10. Immutable evaluation record.
11. Excel projection.
12. Extraction adapters.
13. Post-listing/backtesting.

Do not begin by improving the current HTML scorer.

------------------------------------------------------------------------

## 19. Acceptance Test

A run is accepted only if:

``` text
same inputs
+ same source snapshot
+ same config
+ same engine version
=
same result hash
```

Any difference must be explainable by a changed input/config/engine
version.
