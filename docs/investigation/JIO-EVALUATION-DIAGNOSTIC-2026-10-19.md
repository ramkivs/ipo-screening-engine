# Jio Platforms Evaluation Diagnostic — 2026-10-19

**Mode:** investigate first; evidence-based correction only. **Branch:** `arena/d15866b5-ipo-screening-engine` (base `0d71aa8e6295efadd31dc559afa96757c7b97754`)
**Subject scorecard** (generated 19 October 2026 on the operator's Windows run): score 19/100, verdict INSUFFICIENT DATA, confidence Low (33%), unknown points 64, available 32, missing/unverified 33, Revenue CAGR −48.36%, modules A 3/25, B 0/20, C 11/15, D 5/15, E+F 0/25.

## A. Exact evaluation and persistence identity

The operator's evaluation lives in the Windows store (Arena cannot read it). The engine is
deterministic; the evaluation was reproduced here from the same filing
(`evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`) with the five broker-platform
manual terms and **matches the subject scorecard on all nine reported dimensions** (score 19.0,
INSUFFICIENT_DATA, confidence Low = 32/96 ≈ 33%, unknown 64, available 32, missing rows 33,
CAGR value −48.35792374341301%, A 3/25, B 0/20, C 11/15, D 5/15, E 0/15 + F 0/10). This
content fingerprint positively identifies the evaluation. Reproduction record (pre-fix):
`JIO-PLATFORMS-LIMITED-20261019-075245Z-final-2dce45cb`, result_hash `2dce45cb…5355ca8`
(fresh store re-read succeeded: the record, its `input_snapshot`, `evidence`, `peer_snapshot`,
`market_snapshot`, `missing_unverified` (33 rows), `score` and `provenance` all read back from
durable storage). Byte-identical `result_hash` cannot match across separate runs: the hash
subject (`evaluation_record._result_hash_subject`) includes `market_snapshot_hash` /
`peer_snapshot_hash`, whose snapshots embed capture timestamps — the operator's own
`evaluation_id`/`result_hash` should be read from their store with the acceptance commands.

## B. Revenue CAGR source-to-score trace

**Source:** RHP "Summary of restated consolidated statement of profit and loss", page 76
(derived from the Restated Consolidated Financial Information, p320/330), **(in ₹ million)**,
five columns newest-first:

| Row | 3M Jun-2026 | 3M Jun-2025 | Fiscal 2026 | Fiscal 2025 | Fiscal 2024 |
|---|---|---|---|---|---|
| Revenue from Operations | 391,729 | 350,323 | **1,468,853** | **1,282,184** | **1,095,581** |

**What the pre-fix extractor read** (`financial_tables.py::_parse_table_lines`, `nums[:n_cols]`
= leftmost 3 columns, mapped newest-first to FY2026/25/24): FY2024 ← 1,468,853 (actually
Fiscal 2026), FY2025 ← 350,323 (actually 3-month Jun-2025), FY2026 ← 391,729 (actually 3-month
Jun-2026). Periods were a mix of one full fiscal year and two interim quarters.

**Independent calculation from the source fiscal columns:** (1,468,853 / 1,095,581)^(1/2) − 1 =
**+15.7889%**. The RHP itself states "Our revenue from operations … grew at a CAGR of 15.79%"
(p128) — corroborating. The reported −48.36% is (391,729 / 1,468,853)^(1/2) − 1 =
−48.3579% — arithmetically correct over the **wrong columns**.

**Cause classification: financial-period mapping defect (interim vs fiscal columns), not
formula error, not unit error, not a genuine decline.** (Standalone/consolidated: single
consolidated basis throughout — "Restated Consolidated" statements; no mixing.) The same
column defect also corrupted PAT, expenses, finance costs, cash and receivable-days inputs.

## C. Five-field input/provenance verification

Canonical/persisted input (reproduction; identical pipeline as the operator's run):
`price_band_low=1065.0`, `price_band_high=1119.0`, `lot_size=12`, `ofs=0.0`,
`fresh_issue=3021300.0` — exactly as submitted; evidence items (`EV-issue-ofs`,
`EV-issue.fresh_issue`, `EV-issue.lot_size`, `EV-issue.price_band_high`,
`EV-issue.price_band_low`) all `source_id=SRC-MANUAL-ENTRY`, `extraction_method=MANUAL_ENTRY`,
explanation in the note, `verified:false`. Audit trail (`GET /api/v1/ingestions/{id}`): `manual_submission → manual_entry → evaluation/completed → persistence/completed` with the
five values in the accepted event. No discrepancy between submitted, canonical and persisted
values; the scorecard's "MANUALLY ENTERED" rows render from the same `manual_entry` report.
Caveat: the exact values the operator submitted are theirs; the fingerprint is insensitive to
the fresh-issue magnitude (all module-C paths are magnitude-independent here — UoP UNKNOWN,
fresh-share = 100% for any fresh > 0 with ofs = 0), so the operator's exact five values are
confirmed against their own audit record with the acceptance commands.

## D. Criterion-by-criterion missing-data diagnosis

| Criterion | State (pre→post) | Evidence status |
|---|---|---|
| revenue_cagr | 0/6 (−48.36%) → **4/6 (+15.79%)** | **Verified mapping defect, corrected** (§B) |
| margin_trend | 3/5 stable → 3/5 stable | Computed from mixed columns pre-fix; same band on true columns |
| roce | UNKNOWN → **1/5 (10.76%)** | **Evidence existed but was not parsed:** the Basis-for-Offer-Price KPI table (p132) discloses "Return on Average Capital Employed": 2.56/3.01 (quarters) 10.76/12.50/12.83 (fiscals). Missed: page/title pattern ("Return on Capital Employed" ≠ "Return on Average Capital …"), row wrapped across two lines, and leftmost-column selection. **Corrected** (disclosed ROCE overrides computation). |
| cfo_quality | UNKNOWN → **5/5 (2.62)** | **Evidence existed but was not parsed:** CF statement p77 "Net Cash Flow from Operating Activities (A) 234,459 209,065 775,563 681,557 576,616" — label missed the row pattern ("Net Cash Flow…" vs "net cash from…"). **Corrected**; fiscal columns selected. |
| leverage | UNKNOWN → UNKNOWN | `total_debt` **was** unparsed (plain "Borrowings" rows, p75/p329, note numbers + 5 columns) — **corrected** (non-current 514,548 + current 193,262 = 707,810 for FY2026). `net_worth` remained UNKNOWN: the statements carry no "Total Equity" subtotal row (equity components only). Pre-fix `net_worth` was **wrongly** the "Total Equity and Liabilities" grand total (= Total Assets) via a `total equity\b` regex overmatch — **corrected to governed UNKNOWN** (frozen-core `leverage_bucket` requires net worth AND debt; never silently zeroed). Required evidence: a stated Total Equity/Net Worth row (e.g. the MD&A non-GAAP table p453 "Total Equity (F) 3,448,919 …"; the Basis-for-Offer-Price definition p130 n.2: equity share capital + other equity ex-OCI) — cross-section sourcing is not an authorized ingestion path here. |
| pe_vs_peers, second_multiple | UNKNOWN → UNKNOWN | **Evidence exists but is not safely ingestable:** a peer comparison table sits at p129–131 ("Industry Peer P/E ratio"; footnotes cite Bharti Airtel / Vodafone Idea, P/E as on Oct 13, 2026). The peers parser (`sections.py::extract_peers`) scans only pages 140–180 and expects a "PEER GROUP" row shape; it also stamps hard-coded `listed_years=15` and a hard-coded `as_of` fallback (2026-09-28). Enabling it would inject fabricated provenance metadata, and the document discloses no listed-years → peers would be rejected fail-closed anyway (`min_listed_years=3`). No correction applied; required evidence: peer listed-years/as-of in the document (or authority for their sourcing) and a scoped table-shape mapping. |
| peg | NOT_APPLICABLE → 0/4 (18.6) | Post-fix: PAT CAGR is positive on true columns → PEG computed (P/E over PAT CAGR); band `else` = 0. Semantics unchanged. |
| sector_ipo_relative | UNKNOWN | no same-sector IPO comparables supplied — genuinely absent |
| use_of_proceeds | UNKNOWN | **Genuinely undisclosed:** the Objects-of-Offer schedule (p120) states GCP as `[●]`; v1.5 rule: GCP unknown → bucket UNKNOWN; the 25% legal ceiling is never substituted. Correct fail-closed behavior. |
| fresh_share / ofs_seller / promoter_ofs / dilution / pre_ipo / lockin | scored 11/15 | Correct on extracted structure (ofs = 0 filing-established; fresh_shares 270mn; lock-in intact; no pre-IPO placements) |
| litigation | 0/4 criminal_or_regulatory | **Classification verified from evidence:** company-level litigation is all Nil (p464 I(a)–(e)); subsidiaries (RJIL) have criminal proceedings (tower-radiation petitions; IPC complaint re: security-deposit refund, p464 II(a)). The bucket is group-level and is supported; the 0/4 follows the rubric. Note: a zero score is not itself proof of severity — the evidence is subsidiary-level, company-level Nil. |
| rpt | UNKNOWN | **Genuinely not disclosed in canonical form:** `governance.rpt_pct_revenue` is a stated input (derived metric consumes only that input); the RHP's RPT tables (p56–57, 61, 80) do not state a percentage of revenue. Contract forbids deriving it here. |
| auditor | UNKNOWN | The RHP carries the Joint Statutory Auditors' **examination report** (p321–328; "in our opinion…" p323), not an audit opinion in the canonical taxonomy (unqualified/qualified/adverse/disclaimer); the extractor's classification keywords do not apply to this document class. Fail-closed UNKNOWN is correct; required evidence: the statutory audit opinion or authority to map examination-report language. |
| industry_growth / moat / concentration / visibility | UNKNOWN | industry data is sourced to the Analysys Mason Report with multiple CAGRs (GDP 11.77% p152, digital economy 10.82% p153, overall market 25% p174 …) — selecting "the" industry CAGR requires a designated scope (canonical input needs cagr+scope+period+source as one statement); moat/visibility are un-recorded assessments (no authority to fabricate ratings); top-5 concentration is not disclosed (scanned hits are false positives). |
| anchor / qib / gmp / market_regime | UNKNOWN | **Timestamp-respecting (verified):** evaluation as of 2026-10-19 precedes bidding (2026-10-21–23); `market_snapshot` shows all four blocks MISSING "block not supplied". Later subscription data must not be inserted into this historical evaluation (and the immutable record cannot change). |

## E. Actual unknown-scoring semantics (Gemini claim adjudication)

**The claim "missing fields default to zero" is not accurate for this evaluation.** Verified
code paths: `scoring.py` (spec v1.5 s18; frozen core) defines three criterion states —
`SCORED`, `UNKNOWN` ("contributes 0 to the base score but its full max to the upper bound, and
it is excluded from the confidence numerator"), `NOT_APPLICABLE` (excluded from numerator and
denominator). Unknowns are counted explicitly (`unknown_points` 64 → upper bound 83; confidence
= available/(available+unknown) = 32/96 = 33% → `low_verdict = INSUFFICIENT_DATA`). Missing
metrics never silently become 0: `derived.py` returns typed UNKNOWN with reasons (e.g.
"the fresh issue or the OFS amount is not disclosed"), and `test_core_semantics.py`
(`test_unknown_metric_does_not_become_zero`, `test_unknown_moves_points_from_the_score_into_the_range`)
pins this. A scored criterion whose metric is a real 0 (e.g. `fresh_share_pct = 0` or
`promoter_ofs_pct = 0`) is a `SCORED` band match, visibly distinct from `UNKNOWN`.

## F. Defects confirmed vs hypotheses rejected/unresolved

**Confirmed (all corrected, §G):**
1. Fiscal/interim column mixing in statement tables (root cause of the −48.36% CAGR and of wrong PAT/cash/expense inputs).
2. `net_worth` mapped from "Total Equity and Liabilities" (= total assets) — silent wrong data.
3. CFO row label "Net Cash Flow from Operating Activities" not matched (evidence existed).
4. Plain "Borrowings" rows not matched (evidence existed; note-number columns also polluted rows).
5. "Depreciation and Amortisation" (British spelling) row not matched (evidence existed).
6. KPI "Return on Average Capital Employed" row missed (label + wrap + column selection) — the disclosed ROCE 10.76/12.50/12.83 existed on p132.
7. Unit detection missed "(in ₹ million)" → default INR_LAKHS (statements are ₹ million).

**Hypotheses rejected:** genuine revenue decline (false — RHP states 15.79% growth);
standalone/consolidated mismatch (single consolidated basis); unit conversion error in CAGR
(ratio is unit-free; the cause is column mapping); formula defect (formula correct);
missing-fields-zeroed scoring (false, §E); litigation misclassification (evidence supports the
group-level bucket); F-module penalty for missing market data (it is UNKNOWN, not zero-scored
with false precision).

**Unresolved (no safe correction; required evidence named in §D/H):** peer ingestion
(provenance metadata not in document), net-worth row (cross-section sourcing unauthorized),
auditor-opinion taxonomy mapping for examination reports, industry-CAGR scope designation,
RPT-as-%-of-revenue disclosure, moat/visibility assessments.

## G. Corrections applied (ingestion layer only; no scoring/contract changes)

| File | Fix |
|---|---|
| `engine/ipo_screening/extraction/financial_tables.py` | `nums[-n_cols:]` fiscal-block selection in `_parse_table_lines`, `_extract_all_borrowings`, `_parse_kpi_line`, and the KPI-summary fallback `_get_val` (identical to prior behavior for 3/4-numeric rows — Vishal pins unchanged); `net_worth` pattern `total equity(?! and liabilit)`; CFO label `net cash flow from operating activities`; depreciation `amorti[sz]ation`; KPI detection + `_parse_kpi_line` accept "Return on (Average) Capital Employed" with one-line wrap join |
| `engine/ipo_screening/extraction/numbers.py` | `in ₹ million(s)` / `₹ millions?` unit forms → `INR_MILLIONS` (contract-supported: `canonical.UNIT_TO_CRORE`) |
| `frontend/app.js` | manual-entry unit label case for `INR_MILLIONS` |

Post-fix evaluation (same filing + same five manual terms): score **29/100**, verdict
INSUFFICIENT_DATA (unchanged governance: critical-data gaps — auditor_opinion,
going_concern_uncertainty, net_worth_latest, contingent_liab_pct_networth), confidence Low
(46%), unknown 54 / available 46; A **13/25** (CAGR 4/6 at +15.79%, margin_trend 3/5, ROCE 1/5
disclosed, CFO 5/5), B 0/20 (peers absent; PEG now computed 0/4), C 11/15, D 5/15, E/F 0/25.
Missing rows 31. No scoring formula, weight, threshold, knockout, golden fixture or frozen-core
file changed; fail-closed governance preserved (each corrected unknown is either now correctly
SCORED from source evidence or honestly UNKNOWN with the missing evidence named).

**Regression tests:** `tests/test_financial_statement_column_mapping.py` (9 new: synthetic
5-column/note-number/row-label/unit shapes + the exact real Jio filing pins including
CAGR ≈ 15.79%, fiscal cfo/roce/debt, net-worth-governed-unknown). One pin updated:
`test_jio_rhp_issue_terms.py::test_jio_completes_via_verified_prospectus_pathway` — the fresh
amount pin (1,485,000) encoded the misdetected-unit conversion; with `reporting_unit` correctly
`INR_MILLIONS` the stated Rs.148,500 million is recorded as 148,500 in its own unit (commented
in the test). Vishal pins (`test_extraction.py`, 12) unchanged and green — byte-identical
extraction preserved for 3/4-numeric statement layouts.

## H. Remaining evidence requirements and blockers

- Peer valuation: peer listed-years and an authoritative as-of (the doc's footnote says Oct 13, 2026 but the parser stamps hard-coded metadata — unsafe) + a scoped mapping of the p129–131 table.
- Net worth: a stated Total Equity/Net Worth row in the statements (available only in MD&A p453 / capitalisation p432 / definition p130 n.2) or authority for cross-section sourcing or component derivation (ex-OCI).
- Auditor quality: the statutory audit opinion, or authority to treat the examination report as the canonical `auditor_opinion`.
- Industry growth: designation of which disclosed CAGR is the industry metric (scope).
- RPT: a disclosed RPT-as-%-of-revenue figure (or authority to derive it).
- Moat/visibility: recorded assessments (operator/analyst input class).
- Market-demand (F): correct as UNKNOWN for this timestamp; subscription/anchor/GMP data becomes available after 2026-10-21 and belongs to a NEW evaluation, never this historical record.

## I. Repository / branch / commit / PR / remote status

Published on `arena/d15866b5-ipo-screening-engine` (commit recorded in the tracker publication
amendment; remote-verified via `git ls-remote`). **PR #6 lifecycle preserved:** OPEN/UNMERGED,
head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0ef` (unmovable via the GitHub API); this fix
is **not** on PR #6's head; evidence comment posted. `main` untouched (`01ba66c`); no
competing PR; no hosted CI workflows configured (verified `gh workflow list` empty).

## J. Tracker

Updated additively in `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` (work status
materially changed: diagnosis + correction + publication).
