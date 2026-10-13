# A8-M — Official Index History Evidence Findings

Status: EVIDENCE ONLY — NON-AUTHORITATIVE

## Published evidence

The accompanying package contains official NSE historical index responses for NIFTY 50 and India VIX, covering 1 July through 8 October 2026.

- 70 unique NIFTY 50 sessions.
- 70 unique India VIX sessions.
- 70 shared sessions.
- No unmatched sessions.
- Both indices have closing observations for all shared sessions.
- The alignment validation artifact records source file hashes and calculated close-to-close percentage changes.

The files preserve the locally saved responses. Their hashes identify local file bytes; retrieval timestamps were not recorded.

## A8-M implications

### NIFTY trend

The observations establish historical NIFTY 50 index closes. They do not independently establish the engine's categorical `market.regime.nifty_trend` value.

The existing engine expects `supportive`, `neutral`, or `weak`. The A8-M investigation records the trend definition and decision rules as unresolved. No classification is assigned here.

### India VIX

The observations establish historical India VIX OHLC and closing values. The alignment report also contains derived close-to-close percentage changes.

These observations do not, by themselves, establish an approved production snapshot, point-in-time cutoff, freshness rule, or regime threshold. No such rules are introduced here.

### Scoring and implementation

- No scoring formulas or thresholds changed.
- No synthetic values or categorical classifications were added.
- No missing value was converted to zero.
- No provider qualification or implementation authority is implied.
- Existing A8-M unresolved decisions remain unresolved.

## Evidence location

- `nse-nifty50-20260701-20261013.json`
- `nse-india-vix-20260701-20261013.json`
- `nse-index-alignment-validation-20261013.json`
- `transfer-manifest.json`

This note documents the evidence and its limits. It does not approve a metric contract or authorize implementation.