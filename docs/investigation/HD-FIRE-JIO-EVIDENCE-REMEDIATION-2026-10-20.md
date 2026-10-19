# HD Fire Protect + Jio Platforms — evidence remediation and verification

**Date:** 2026-10-20 (Asia/Calcutta)
**Branch:** `arena/ae4d04e8-ipo-screening-engine`
**Pre-change HEAD:** `86d4950a07faa19bd1b0f05ee8e49a5d9560edf9`
**Scope:** two separately reported workstreams. No scoring weight, threshold,
formula, knockout rule, penalty rule, golden fixture, historical evaluation or
result hash was changed. Historical evaluations are not rewritten; the new Jio
run is a new record with its own provenance.

Working tree at start: `86d4950` (clean). Only extraction/tests/docs changed:
`builder.py`, `financial_tables.py`, `sections.py`, `toc.py`, four test files,
the new fixture directory and this record. `config/` and `schema/` diffs are
empty (`git diff --stat -- config schema` → nothing).

---

# Report A — HD Fire Protect

**Scorecard under audit:** `2026-10-19 12:31:34 UTC`, result hash
`551a7eab957ec8f6f2fec8cca77ce6951e0a0595b6ec9231e79e696e33c2aa3b`:
7/100, base 10, penalties −3, available 27, unknown 73, confidence 27 %,
`INSUFFICIENT_DATA`, 36 items. Applied penalty `receivable_days_up`;
`auditor_cfo_exit` UNKNOWN and carried in the range.

## A.1 What was verified, and the exact code path

| Element | Location | Verified behaviour |
|---|---|---|
| Peer extraction | `SectionExtractor.extract_peers` (`engine/ipo_screening/extraction/sections.py`) | sole producer of `peers` |
| Sole caller | `DocumentExtractor.extract_from_pdf` (`engine/ipo_screening/extraction/extractor.py`) | called once per ingestion |
| Layout table | `SectionExtractor._PEER_SHAPES` | three recognised layouts, explicit width + column map |
| Cell classification | `_peer_cell` / `_peer_row` | `(bool, Optional[float])`; placeholders occupy a column |
| Name validity | `_peer_name_is_valid` | prose, totals and leaked numeric rows rejected |
| Valuation date | `_peer_as_of_date` | source date only; never a default |
| Pre-evaluation gate | `validate_peer_records` (`schema_validation.py`), called at `presentation/service.py` ingestion | same schema, named peer + field, HTTP 400 before evaluation |
| Evaluation gate | `pipeline.evaluate` → `enforce_schema` | unchanged second line of defence |

Recognised layouts, all mapped by header, never by position:

1. `accounting_ratios` (width 8): Face value, CMP, EPS, diluted EPS, P/E,
   RONW, NAV, PAT — R.K. Fashion / Banaras Beads reference.
2. `listed_peers_closing_price` (width 9): Closing price, face value, revenue,
   EPS basic, EPS diluted, P/E, net worth, RONW, NAV — Vishal Nirmiti.
3. `accounting_ratios_peer_companies` (width 7, new): Face value, revenue,
   EPS basic, diluted EPS, P/E, return on average net worth, NAV — Jio RHP
   p. 130. There is no CMP column; `cmp` is `None`, so no P/B is invented.

Hardening verified in code and tests:

- Any table whose header matches no shape emits **no peers** (`continue`) —
  unsupported layout is rejected, not guessed.
- Placeholder cells (`[●]`, `(●)`, `-`, `--`, `—`, `NA`, `N/A`, `NIL`, `NM`,
  `N.M.`, `[]`, blank markers) keep their column so later values cannot shift
  left.
- A data row is consumed only at exactly the declared width. A shorter row
  with two or more numeric cells is treated as an unmappable data row and
  cannot be accumulated into the next peer's name; a name containing a
  monetary/decimal cell is rejected outright.
- A leading integer is a row serial only when **text follows it**; a row that
  starts with a data value (e.g. face value `10.00`) is not stripped.
- Prose (sentences, "The Company", totals/averages/highest/lowest) is never a
  peer name.
- Peer values pass the unchanged schema (P/E, ROE, P/B bounds; `roe_pct`
  ≤ 10000). Nothing is clamped, substituted or dropped silently.

## A.2 The original failure — reproduction and its limit

Observed Windows failure (audit trace `ing-81fd285e5b8248c6`):
`SCHEMA_VIOLATION at peers/0/roe_pct: 26957.28 is greater than maximum 10000`
(and `peers/1 21700.34`). The two demonstrated mechanisms are reproduced from
source-backed reference tables in `tests/test_peer_row_mapping_and_bounds.py`:

- positional mapping of a different layout puts a P/E cell into `roe_pct`
  (Vishal replay produced `roe_pct = 13.86`, a P/E value, and a synthetic
  `pb = 0.0` before the fix);
- placeholder collapse shifts monetary/NAV cells into the percentage column,
  producing the exact `26957.28 / 21700.34` signature
  (`test_monetary_column_cells_never_land_in_roe_pct`,
  `test_short_data_row_never_leaks_into_the_next_peer_name`).

The HD Fire RHP and its Windows evaluation store are not present in this
workspace (`evidence/` contains no HD Fire filing). The exact source row
cannot therefore be attributed to one mechanism; the failure signature, the
schema rejection and the corrected mapping are reproduced, and the
source-row confirmation remains Windows-only. This is a recorded limit, not
a claim of page-level inspection.

## A.3 NIL-OFS clause binding

`SectionExtractor._find_ofs_nil` (`sections.py`) no longer searches a fixed
32-line window after any "offer for sale" occurrence. It now:

- accepts same-line `Offer for Sale Size: Not applicable`, the wrapped OFS
  label + value, and the real Jio three-row cover shape;
- rejects an OFS label line that itself states an amount/quantity;
- rejects a NIL that is the value of a bare Fresh Issue / Pre-IPO / Promoter /
  reservation / total-issue label, on the same or the immediately previous
  line.

`tests/test_ofs_nil_binding.py` (9 tests) pins every accepted and rejected
clause, including: fresh-issue NIL is not OFS zero; pre-IPO NIL is not OFS
zero; promoter-group NIL is not OFS zero; a genuine OFS amount is never turned
into NIL; and the real Jio cover still establishes `ofs = 0`.

## A.4 Manual terms, OFS conflict and the recorded operator decision

The recorded operator decision (filing `issue.ofs = 0` from the NIL-OFS cover;
operator entered `71231`) is preserved, not replaced:

- the conflict is surfaced as HTTP 409 `ISSUE_TERM_CONFLICT` with
  `existing_value 0.0 / FILING_EXTRACTION` and `manual_value 71231.0`;
- explicit confirmation applies the manual value; the evaluation then uses
  `ofs = 71231`;
- every manual term keeps `MANUAL_ENTRY`, `SRC-MANUAL-ENTRY`, `verified = false`
  and the operator explanation; `overridden_by_verified == []`;
- the audit trail records `manual_submission`, `manual_entry`, `evaluation
  completed`, `persistence completed` with the accepted value.

This is pinned by
`test_confirmed_ofs_override_stays_manual_entry_and_unverified`. The engine
does not silently promote operator confirmation to source verification, and
does not overwrite the recorded decision. The scorecard's pure-OFS cap
(ceiling 60) is consistent with that recorded decision (OFS > 0, fresh 0).

## A.5 Scorecard semantics and arithmetic

- Module subtotals: A 2 + B 0 + C 3 + D 5 + E 0 + F 0 = **10**.
- Applied penalty: `receivable_days_up` −3. `auditor_cfo_exit` is UNKNOWN and
  remains inside the range; it is not the applied −3.
- `10 − 3 = 7`; available 27 + unknown 73 = 100; confidence 27 % = available
  points; floor 0; pure-OFS ceiling 60. The 7/100 is arithmetically consistent
  and was **not changed**.
- UNKNOWN vs scored-zero: UNKNOWN criteria are excluded from available points
  and reported in the missing inventory; a scored zero is an evaluated zero.
  K1/K3/K5/K6 UNVERIFIED do not reduce the score; they reduce confidence and
  widen the range. Module B stays 0/20 because `peer_snapshot` is absent.
- Caveat retained from the prior audit: HD Fire's K2 CLEAR depends on
  builder/extractor favourable defaults (`litigation_bucket="clean"`,
  `sebi_ed_action_active=False`, etc.). Those defaults are unchanged here;
  correcting them requires a governed golden re-baseline and is out of scope
  for this pass.

## A.6 HD Fire disposition

**FIXED AND VERIFIED (code + tests):** layout-aware peer mapping, placeholder
and row-width handling, prose exclusion, unsupported-layout fail-closed,
pre-evaluation schema gate with named diagnostics and audit evidence,
NIL-OFS clause binding, and manual-entry provenance.

**SOURCE-LEVEL VERIFICATION PENDING:** the exact HD Fire peer row and the
Windows evaluation store; no filing exists in this workspace.

**NOT CHANGED (by instruction):** the 7/100 result and all scoring semantics.

---

# Report B — Jio Platforms

**Historical record preserved:** the 2026-10-19 scorecard
`ce7bfe8eacffd3abb442a1f6b8daa657760e4f698efdc35b26396aa2e8f00f88`
(29/100, floor 19, ceiling 83) and the 21/100 inverted-structure result are
reproduced from the frozen pre-remediation canonical fixture
`fixtures/jio/jio_canonical_2026-10-19_pre_evidence_remediation.json`
(`tests/test_jio_score_bridge.py`, 1 passed). The fixture is not a scoring
input and is not source evidence.

**New evidence-backed evaluation** (new record, own provenance): live
extraction + the same manual terms (band 1065/1119, lot 12, OFS 0, fresh
3,021,300), explanation "2026-10-19 Windows issue-structure reproduction
(Arena re-run, net-worth evidence remediation)", evaluation run on
2026-10-19 (Arena, UTC; the service assigns the record timestamp):

| Measure | Value |
|---|---|
| Final score | **37.0 / 100** |
| Available / unknown | 61 / 39 |
| Range | 27 – 76 |
| Verdict | `INSUFFICIENT_DATA`, confidence Low (61 %) |
| Penalties / caps | 0 / none |
| Modules | A 17, B 1, C 11, D 8, E 0, F 0 |
| Knockouts | K1 UNVERIFIED, K2–K4 CLEAR, K5 UNVERIFIED, K6 CLEAR |

The 29 → 37 delta is entirely evidence availability, not a rule change:

| Criterion | Old (frozen input) | New (live) | Effect |
|---|---|---|---|
| `leverage` | UNKNOWN | SCORED 4/4 | +4 points, +4 available |
| `rpt` | UNKNOWN | SCORED 3/3 | +3 points, +3 available |
| `pe_vs_peers` | UNKNOWN | SCORED 0/8 | +8 available, 0 points |
| `peg` | SCORED 0 | SCORED 1 | +1 point (already available) |

## B.1 Net worth and K1

**Correction.** The restated balance sheet (PDF p. 329) prints Equity Share
Capital, Other Equity and a separate Non-Controlling Interest line; it prints
no Total Equity subtotal. Note 38, "Capital Management" (PDF p. 406), states
"Total Equity (As per Restated Consolidated Statement of Assets and
Liabilities)":

| FY | Equity share capital | Other equity | Total equity (Note 38) | NCI (separate) |
|---|---:|---:|---:|---:|
| 2026 | 89,390 | 3,270,379 | **3,359,769** | 10,993 |
| 2025 | 89,390 | 2,961,084 | **3,050,474** | 11,338 |
| 2024 | 89,390 | 2,693,474 | **2,782,864** | 11,353 |

Total equity + NCI reconciles exactly to Total Assets − Total Liabilities
(FY2026: 3,359,769 + 10,993 = 6,155,940 − 2,785,178 = 3,370,762).

`_derive_net_worth_from_equity` now returns the owner components and **never
adds NCI**; it fails closed when the components do not reconcile, when a
component is missing, or when NCI is present but the totals are absent. The
governed real-filing pin in
`tests/test_financial_statement_column_mapping.py` was updated from
`net_worth is None` to the Note 38 values, with the grand-total guard retained
(`Total Equity and Liabilities` is never used); four new component/reconciliation
tests pin the behaviour.

**Definition boundary (reported, not silently applied).** The issuer's own
"net worth" definition (p. 130 note 1) excludes other comprehensive income;
for FY2026 that is 3,340,134, i.e. 19,635 (0.59 %) below disclosed total
equity. The same definition is used for NAV per share (₹373.66) and the
p. 79 summary (NW 3,417,785 at 30 June 2026). The canonical field stores the
disclosed total equity because the balance-sheet components do not expose the
OCI reserve split; the difference changes no band, ratio trigger or verdict
(D/E 0.2107 vs 0.2118; K5 0.45 % vs 0.44 %). A schema-level decision on whether
`net_worth` means ICDR net worth or total equity is recommended before any
filing where that 0.6 % could matter.

**K1 evidence.** The independent auditors' examination report (PDF pp. 321–324,
Deloitte Haskins & Sells LLP and Chaturvedi & Shah LLP, UDINs recorded) covers
the restated statements; Note 47.4 (PDF p. 430) states there are no audit
qualifications, no other legal/regulatory matters and **no emphasis of matter**
for the five periods. The only "going concern" string in the 591-page RHP is
the 2019 scheme text on p. 253, not a going-concern uncertainty.

K1 nevertheless remains **UNVERIFIED**: the governed extractor classifies an
opinion only from positive opinion language ("unqualified opinion" /
"unmodified opinion"), which this examination-report layout does not carry,
and `going_concern_uncertainty` has no positive/negative disclosure to bind.
The absence of a going-concern paragraph is not treated as
`going_concern_uncertainty = false`. K1 is therefore not cleared on net worth
alone, exactly as required.

## B.2 Leverage

Source: Note 38 (p. 406) and balance sheet (p. 329), INR millions.

| Input | FY2026 | Use |
|---|---:|---|
| Borrowings (gross debt) | 707,810 | `total_debt` |
| Total equity (owner components) | 3,359,769 | `net_worth` |
| EBIT | 461,327 | interest cover numerator |
| Finance costs | 86,534 | interest cover denominator |
| D/E | 0.2107 | < 0.5 |
| Interest cover | 5.3312 | > 5 |

Lease liabilities (138,876), deferred payment liabilities (1,045,137), trade
payables (89,316) and other financial liabilities (201,775) are **not**
borrowings and are not folded into total debt; total liabilities are never
used as debt. Consolidated scope only. `leverage_bucket` = **strong**, using
the unchanged thresholds (<0.5 and >5 strong; <1 ok; 1–2 stretched; >2 weak).
Scoring changed only because both inputs are now evidence-backed.

## B.3 RPT and K6

Source: Note 36, Related Party Disclosures (PDF pp. 376–378), INR millions.
The approved metric definitions (Ramki, 2026-10-17;
`docs/investigation/RPT-EXTRACTION-AND-METRIC-DEFINITIONS-2026-10-17.md`) are
unchanged:

- `rpt_pct_revenue` = related-party revenue-type transactions ÷ revenue from
  operations, latest audited FY;
- `rpt_pct_of_revenue_growth` = latest share − prior share, in percentage
  points (not "RPT ÷ revenue" and not a contribution inferred from totals);
- eligible numerator categories are revenue-type only (`sale_of_*` except
  `sale_of_ppe`, plus job-work charges received).

Extracted FY2026 revenue from operations with related parties:
Parent 36,442 + Fellow Subsidiaries 25,526 + Associate/JV 447 + Others 884 =
**63,299** (the note's stated total). FY2025 = 56,717; FY2024 = 52,878.

| Measure | Value |
|---|---:|
| FY2026 share | 63,299 / 1,468,853 = **4.3094 %** |
| FY2025 share | 56,717 / 1,282,184 = **4.4235 %** |
| Change | **−0.1141 pp** |
| Module D `rpt` | SCORED 3/3 (<5 %) |
| K6 | CLEAR (declining share cannot exceed +40) |

The extraction fixes in this pass: the anchor now recognises "Transactions
with **the** related parties" and "Transactions during the period / year with
Related Parties"; the period-header window is 30 lines and accepts "31st
March, 2026"; balance/outstanding and "major related-party transactions"
tables stop parsing (no double counting); a Relationship-column row with an
unrecognised category can no longer inherit the previous category; a leading
Sr. No. and trailing numeric tokens are stripped from the counterparty label.
Residual limitation: some non-revenue counterparty labels still carry wrapped
category text ("… and Other Intangible Assets Parent"). The amounts and every
metric are unaffected; the verbatim quote remains the audit evidence.

## B.4 Valuation and peers

Source: Basis for Issue Price, "Comparison of accounting ratios" (PDF p. 130)
and notes (p. 131). The issuer names exactly two listed peers; no other named
company is added. Both pass the unchanged peer schema and are VALID for the
2026-10-13 valuation date.

| Peer | P/E | Return on average net worth | NAV/share | P/B |
|---|---:|---:|---:|---:|
| Bharti Airtel Limited | 40.71 | 20.32 % | 244.60 | not disclosed (no CMP) |
| Vodafone Idea Limited | 3.99 | NM | (3.30) | not disclosed (no CMP) |

Issuer P/E at the cap price = 1119 / 32.63 = **34.29**; peer average P/E
(issuer-disclosed, p. 129) = 22.35; premium = **+53.4 %** → `pe_vs_peers`
0/8. PEG = 34.29 / 15.79 = **2.17** → 1/4. `second_multiple` stays UNKNOWN
(the table supplies no peer price or EV/EBITDA, so no P/B or EV multiple can
be formed), and `sector_ipo_relative` stays UNKNOWN (no same-sector recent-IPO
dataset). No peer metric was invented and no eligibility rule was relaxed.
Module B = 1/20.

Post-issue EPS itself is unit-correct: 300,527 (INR millions) × 10⁶ ÷
9,209,030,830 = **32.63** (the pre-fix builder assumed lakhs and produced
3.26). The lakh-based reference filings are unchanged (R.K. Fashion 4.05).

## B.5 K5 (contingent liabilities)

Source: Note 37 (PDF p. 405): claims/disputed liabilities not acknowledged as
debts FY2026 **15,021** (FY2025 30,183; FY2024 27,924); commitments are
separate. Against net worth, 15,021 / 3,359,769 = **0.45 %**, far below the
50 % trigger, and the note quantifies every disclosed claim.

K5 nevertheless remains **UNVERIFIED**, for two independent reasons:

1. `_parse_contingent_liabilities` is unsafe: it starts scanning at page 250,
   misses both the p. 79 summary and the p. 405 note, and its "first line
   containing Total plus a decimal" heuristic would return the compensation
   total (534) if pointed at Note 37.
2. `contingent_liabilities_unquantified` has no governed extractor; the
   builder carries it only from a curated base. Absence of an unquantified
   disclosure is not evidence that it is false, and K5 requires both leaves.

No parser change was made: choosing a latest-period column and a
"quantified/unquantified" contract is a policy decision, and any wrong value
would directly affect a knockout. The evidence is recorded; K5 stays
UNVERIFIED.

---

# Report C — Validation

All runs below were executed in this workspace on 2026-10-20 with
`PYTHONPATH=engine ./.venv/bin/python` (Python 3.11, pytest 9.1.1).

| # | Command (exact) | Result |
|---|---|---|
| 1 | `pytest tests/test_peer_row_mapping_and_bounds.py tests/test_ofs_nil_binding.py tests/test_jio_score_bridge.py tests/test_jio_evidence_remediation.py tests/test_financial_statement_column_mapping.py -q` | **40 passed**, 3 warnings, 62.28 s |
| 2 | `pytest tests/test_enrichment_engine.py tests/test_fixture_fallback_isolation.py tests/test_rk_fashion_reconciliation.py tests/test_cfo_pat_determinism.py tests/test_d_peer_1_no_synthetic_peers.py tests/test_cross_ipo_issue_term_provenance.py -q` | **52 passed**, 2 warnings, 243.41 s |
| 3 | `pytest tests/test_cli_phase5i.py::test_frozen_core_integrity tests/test_cli_phase5i.py::test_golden_evaluation_regression tests/test_evaluation_lifecycle.py::test_s_vishal_golden_regression -q` | **3 passed**, 0.72 s |
| 4 | `pytest tests/test_peer_row_mapping_and_bounds.py -q` (after the final serial/name fix) | **15 passed**, 1.29 s |
| 5 | `pytest tests/test_jio_evidence_remediation.py -q` | **1 passed**, 28.47 s |
| 6 | `pytest tests/test_financial_statement_column_mapping.py -q` | **14 passed**, 28.76 s |
| 7 | `cd frontend && npm test` | **89 pass, 0 fail**, 847.68 ms |
| 8 | `node --check frontend/api.js && node --check frontend/app.js` | both OK |
| 9 | `python -m compileall -q engine tests` | OK |
| 10 | `git diff --stat -- config schema` | empty (no policy/schema change) |
| 11 | `pytest tests/ -q` (full backend; final code/test tree at commit `f42b6ce`) | **1139 passed**, 0 failed, 36 warnings, 1421.69 s, exit 0 |

Golden result hash: **`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`**
unchanged; frozen-core check passes. The Jio bridge test preserves 29 (fresh
only) and 21 (inverted) from the frozen pre-remediation input. No historical
record, hash or golden fixture was edited.

Source hashes: Jio RHP
`evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`
SHA-256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`.
Jio historical fixture: `fixtures/jio/jio_canonical_2026-10-19_pre_evidence_remediation.json`.

---

# Report D — Publication

- Branch: `arena/ae4d04e8-ipo-screening-engine` (fixed session branch).
- Implementation commit: `f42b6ce1ba4c3058f1d5e52ef2b8d4cacd2d0ebc`
  (records the four extraction changes, three modified test files, the new
  remediation test, the frozen fixture and this record).
- Remote verification: `git ls-remote origin
  refs/heads/arena/ae4d04e8-ipo-screening-engine` returned
  `f42b6ce1ba4c3058f1d5e52ef2b8d4cacd2d0ebc` after the push; the working
  tree is clean. `git merge-base --is-ancestor` confirms `e1df89b…`,
  `e05c0ef…` (PR #6 head) and `01ba66c…` (`main`) are in the published
  ancestry.
- PR #6: OPEN, unmerged; head `arena/5dd3fe52-ipo-screening-engine` @
  `e05c0efbca1ecb3024e52da73a22e180ea171118`; base
  `arena/573e69a4-ipo-screening-engine`; untouched by this session.
- `main`: `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched.
- Tracker: `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`, new
  sections for HD Fire and Jio appended.
- CI: no hosted workflows configured.
- Cross-repository tracker writes: unavailable in this environment; recorded
  as a handoff only.

**Blockers / outstanding acceptance:** HD Fire's source filing and Windows
evaluation store are not in this workspace; the exact 26957.28/21700.34 source
row and the Windows re-upload remain outstanding. Jio's Windows record
`ce7bfe8e…` was not re-run on Windows. K1/K5 remain unverified by design.

---

# Report E — Disposition

| # | Item | Disposition |
|---|---|---|
| A1 | Peer layout mapping, placeholders, row width, prose, unsupported layout | **FIXED AND VERIFIED** |
| A2 | Pre-evaluation peer schema gate, named diagnostics, audit event | **FIXED AND VERIFIED** |
| A3 | Failed extraction cannot become a successful valuation | **FIXED AND VERIFIED** (Module B stays UNKNOWN; no scoring) |
| A4 | NIL-OFS clause binding | **FIXED AND VERIFIED** (9 tests) |
| A5 | Operator-confirmed manual OFS preserved, never upgraded | **FIXED AND VERIFIED** |
| A6 | HD Fire 7/100 arithmetic and scorecard semantics | **INVESTIGATION COMPLETE; unchanged** (10 − 3 = 7; 27 + 73 = 100) |
| A7 | Exact HD Fire raw peer row / Windows store | **SOURCE-LEVEL VERIFICATION PENDING / NOT ACCESSIBLE** |
| B1 | Jio net worth derivation (owner components, NCI excluded, reconciled) | **FIXED IN CODE AND VERIFIED**; ex-OCI definition (3,340,134) **reported, decision pending** |
| B2 | Jio K1 (auditor opinion, going concern) | **EVIDENCE STILL MISSING** — source evidence located, governed fields remain UNKNOWN; K1 UNVERIFIED |
| B3 | Jio leverage (borrowings, not total liabilities; bands unchanged) | **FIXED AND VERIFIED** (D/E 0.2107, ICR 5.3312, strong) |
| B4 | Jio RPT/K6 (Note 36, approved share-change definition) | **FIXED AND VERIFIED** (4.3094 %, −0.1141 pp, K6 CLEAR) |
| B5 | Jio valuation peers (2 source peers, P/E 0/8, PEG 1/4) | **FIXED AND VERIFIED**; second multiple and sector relative **UNKNOWN (source missing)** |
| B6 | Jio K5 contingent liabilities | **NOT FIXED (policy decision outstanding)**; K5 UNVERIFIED |
| B7 | Jio post-issue EPS units | **FIXED AND VERIFIED** (32.63; lakh-based filings unchanged) |
| B8 | Historical 29/21 bridge and immutable records | **PRESERVED AND VERIFIED** (frozen fixture) |

No scoring rule, threshold, weight, cap, penalty rule, golden fixture or
historical result was changed. The new Jio 37/100 is a new evaluation on
newly established evidence, not a rewrite of the 29/100 record.
