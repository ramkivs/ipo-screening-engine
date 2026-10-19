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

> **Superseded in part by Amendment 2 (same date):** the auditor opinion *is*
> now established from the examination report's conclusion (p. 324), and the
> extractor also accepts that conclusion shape. K1 remains UNVERIFIED, but
> only on `going_concern_uncertainty`. See "Amendment 2", Report B.

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

> **Superseded in part by Amendment 2 (same date):** the unsafe parser has
> been replaced by a note-anchored extractor with a latest-March column and a
> quantified/unquantified contract; the live filing now yields 15,021 and
> `None`. K5 remains UNVERIFIED on the unquantified leaf only. See
> "Amendment 2", Report B.

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

---

# Amendment 2 — final verification of auditor evidence, K5 and valuation (2026-10-20)

This amendment records the work done after Reports A–E were published at
`f42b6ce`. It supersedes exactly two earlier conclusions (B.1's K1 text and
B.5's K5 text, both marked above); everything else re-verifies unchanged
behaviour. No scoring weight, threshold, formula, knockout rule, penalty,
golden fixture or historical evaluation was touched. `git diff --stat --
config schema fixtures` is empty.

## What changed in code

1. **Auditor opinion resolution** (`engine/ipo_screening/extraction/sections.py`).
   `_examination_report_pages` (l. 1224) anchors the report at its heading and
   follows it through the auditors' UDIN signature block, bounded to 8 pages
   and stopped by the restated balance-sheet heading. Within that section the
   order of precedence is: adverse / disclaimer / positive Emphasis of Matter
   / qualification, then the examination-report conclusion ("we report that
   the Restated Consolidated Financial Information … no modification in the
   underlying audit reports"), then explicit unqualified/unmodified language.
   A component auditor's paragraph-7 confirmation about one subsidiary's
   standalone statements is not accepted in place of the group conclusion.
   `_has_positive_emphasis_of_matter` (l. 1198) and `_opinion_sentence`
   (l. 1214) keep the verbatim quote and page attribution (the clause offset,
   not the paragraph start).
   The qualification regex is `(?<!un)qualified\s+opinion`: a plain
   "qualified opinion" match reads "unqualified opinion" as a qualification.
   That regression was caught by
   `test_step5_auditor_and_manual_terms.py::test_supported_unqualified_opinion_is_extracted`
   (1 failed / 19 passed) and fixed; the batch then passed 28/28.
   `going_concern_uncertainty` is emitted only on positive uncertainty
   language. It is never emitted as `False`, so an absent disclosure cannot
   clear K1.
2. **K5 contingent liabilities** (`engine/ipo_screening/extraction/financial_tables.py`).
   `_extract_contingent_liabilities` (l. 575) replaces the old first-"Total"
   heuristic. It anchors on the contingent-liabilities note heading, finds the
   claims/disputed-liabilities row, reads the header only from the 30 lines
   immediately above that row, takes the latest **31 March** column, and
   fails closed on a width mismatch or an absent header. The
   unquantified-claim disclosure is scanned inside the note block
   (row −30 … row +8), so a neighbouring note cannot supply it. `builder.py`
   (l. 264–271) passes `financials.contingent_liabilities_unquantified`
   through; `derived.py` (l. 2254) keeps the leaf tri-state (True / False /
   UNKNOWN), never coercing absent to False.

## Report A — HD Fire Protect (re-verified; no change)

| Element | Location | Verified behaviour |
|---|---|---|
| Peer extraction | `SectionExtractor.extract_peers` (`sections.py:2145`) | sole producer of `peers` |
| Layout table | `SectionExtractor._PEER_SHAPES` (`sections.py:1964`) | three header-anchored layouts (widths 8 / 9 / 7), explicit column maps |
| Cell classification | `_peer_cell` / `_peer_row` | placeholders (`[●]`, `NA`, `NM`, `-`) occupy their column; a blank cell shortens the row and the row is rejected by width |
| Name validity | `_peer_name_is_valid` | prose, totals/averages and leaked numeric rows rejected |
| Valuation date | `_peer_as_of_date` | disclosed date only; never defaulted |
| Sole caller | `DocumentExtractor.extract_from_pdf` (`extractor.py:30`) | one call per ingestion |
| Pre-evaluation gate | `validate_peer_records` (`schema_validation.py:91`), called at `presentation/service.py:1426` | same schema, named peer + field, `validation/peer_contract/FAILED`, `IngestionValidationError` → HTTP 400 before any evaluation or persistence |
| Evaluation gate | `pipeline.evaluate` → `enforce_schema` | unchanged second line of defence |

**Tests executed this pass (exact):**

- `PYTHONPATH=engine ./.venv/bin/python -m pytest tests/test_peer_row_mapping_and_bounds.py -q`
  → **17 passed**, 1 warning, 1.44 s. The file now has two new tests:
  - `test_blank_and_non_numeric_cells_keep_their_columns` — a blank/`NA`
    revenue cell and an `NM` RONW cell keep their columns (RONW stays 18.25 /
    None, P/B stays a real ratio, never a shifted cell);
  - `test_valid_peer_ingestion_reaches_a_scored_valuation` — a contract-valid
    peer survives ingestion, is snapshotted `VALID`, and `pe_vs_peers` is
    `SCORED` 0.0 (issuer P/E 23.26 vs peer 12.5 = +86 %, a scored zero — the
    positive control for the rejection tests).
- The early-rejection test now also asserts
  `service.eval_store.list_evaluations() == []`: a filing that fails the peer
  contract leaves **no** evaluation behind, so failed extraction cannot become
  a successful evaluation.
- `tests/test_ofs_nil_binding.py` — 9 passed inside the regression batch
  below; `tests/test_step5_auditor_and_manual_terms.py` — 19 passed (28/28
  together with the auditor suite), including the real Vishal filing's three
  manual terms kept `AWAITING_ISSUE_TERMS` and the Jio-style OFS conflict
  path.

**Original failure.** Unchanged from A.2: the `26957.28` / `21700.34`
signature is reproduced from source-backed reference tables by both
demonstrated mechanisms (positional mapping of a different layout; placeholder
collapse), and rejected by the unchanged `roe_pct` bound (−1000 … 10000) with
a peer-and-field-named diagnostic. The HD Fire filing and its Windows
evaluation store are absent from this workspace; the exact source row remains
a recorded limit, not a claim.

**NIL-OFS and the operator decision.** Unchanged from A.3 / A.4. A NIL bound
to a Fresh Issue, Pre-IPO, Promoter-group, reservation or total-issue clause is
not `ofs = 0`; a genuine OFS amount is never turned into NIL; the recorded
manual OFS 71,231 over the filing's NIL remains `MANUAL_ENTRY` /
`SRC-MANUAL-ENTRY`, `verified` unset, `overridden_by_verified == []`, with the
409 conflict, explicit confirmation and audit events preserved.

**Scorecard.** 7/100 is unchanged and arithmetically consistent:
A 2 + B 0 + C 3 + D 5 + E 0 + F 0 = 10; `receivable_days_up` −3; 10 − 3 = 7;
available 27 + unknown 73 = 100; confidence 27 %; `auditor_cfo_exit` UNKNOWN
inside the range; pure-OFS cap 60 not binding. `INSUFFICIENT_DATA` is the
`critical_data` branch of `scoring.py:509–518`, not a score band; the low
confidence alone does not decide it. No formula or rule was changed.
The recorded issue structure (filing NIL-OFS, operator OFS 71,231, fresh issue
not stated by the filing) makes `pure_ofs` true, so the ceiling is 60; 7 is far
below it, so the OFS structure does not alter the result. The favourable-default
dependency recorded in A.5 (litigation `clean`, `sebi_ed_action_active=False`,
etc.) is unchanged and still needs a governed re-baseline decision.

**Disposition.** FIXED AND VERIFIED (peer mapping, placeholder/width handling,
prose exclusion, unsupported-layout fail-closed, early schema gate, audit
evidence, NIL-OFS binding, manual-entry provenance). SOURCE-LEVEL VERIFICATION
PENDING: the HD Fire peer row and Windows record only. NOT CHANGED: 7/100 and
all scoring semantics.

## Report B — Jio Platforms (final record)

**Final run:** `JIO-PLATFORMS-LIMITED-20261019-183045Z-final-7857589a`

| Field | Value |
|---|---|
| Score | **37.0** / 100 (range 27–76) |
| Availability | available 61, unknown 39, confidence **Low** (61 %) |
| Verdict | `INSUFFICIENT_DATA` (`critical_data`: `going_concern_uncertainty`) |
| Modules | A 17, B 1, C 11, D 8, E 0, F 0 |
| Knockouts | K1 UNVERIFIED [`going_concern_uncertainty`]; K2 CLEAR; K3 CLEAR; K4 CLEAR; K5 UNVERIFIED [`contingent_liab_unquantified`]; K6 CLEAR |
| Penalties | none applied; 10 unresolved penalty points widen the range |
| Hashes | result `7857589af33bbf61bc720443f32bf2ae0e0efa2f47e6d03926932cace478b8a7`; input snapshot `59870d9a…`; peer snapshot `61f5c913…`; config 1.5.0 `4a5d92e8…` |

The previous run (`…181727Z-final-0b60daf7`) scored 37.0 with the same module
points. The two source fixes resolved *availability* (auditor opinion; K5
amount) but changed no scored criterion: K1 and K5 still have one unknown leaf
each, and Module E and D's `auditor` remain unknown. That is why the score did
not move — not a defect.

**K1 — auditor opinion now established; going concern still unknown.**
The joint auditors' examination report (PDF pp. 321–324: Deloitte Haskins &
Sells LLP `117366W/W-100018` and Chaturvedi & Shah LLP `101720W/W-100355`,
Mumbai, 7 October 2026; UDINs `26100459QBZXUZ8355` /
`26122179ZKMPTF3256`) concludes, verbatim: "…no modification in the underlying
audit reports…" → `governance.auditor_opinion = "unqualified"`, page 324,
quote preserved. `going_concern_uncertainty` and `eom_materiality` remain
`None`: the report contains no going-concern paragraph, Note 47.4 (p. 430)
states there are no qualifications, other legal/regulatory matters or emphasis
of matter, and a whole-PDF sweep finds "going concern" only in the 2019 scheme
text (p. 253). Absence is not treated as `False`, so **K1 stays UNVERIFIED**
and `going_concern_uncertainty` stays a missing `critical_data` item.
A governed "negative confirmation" rule (complete examination report +
conclusion + no going-concern section + no EOM ⇒ False) would clear K1 and
change the verdict family for filings like this one; that is a policy
decision, and it was **not** taken here.

**K5 — extraction fixed; the unquantified leaf is genuinely absent.**
`_extract_contingent_liabilities` returns (p. 405, 15,021.0, None, verbatim
claims-row quote) — the latest 31 March column, not the June-2026 interim
14,688 and not Note 38's header. 15,021 / 3,359,769 = **0.45 %**, far below
50 %. `contingent_liabilities_unquantified` is `None`: no unquantified-claim
disclosure exists anywhere in the 591-page filing ("unquantif*" has zero
hits), so that leaf is UNKNOWN and K5 stays UNVERIFIED. The eight new tests
(`tests/test_contingent_liabilities_extraction.py`: 5-column note, adjacent
note header, 3-column fiscal note, width mismatch, missing headers, absent
note, unquantified positive vs absence, live Jio pin) all pass.

**Net worth.** Unchanged and reconciled: 2,782,864 / 3,050,474 / 3,359,769
(Equity Share Capital + Other Equity; NCI 11,353 / 11,338 / 10,993
reconcile-only), tying exactly to Total Assets − Total Liabilities. The
issuer's own ICDR net worth (excludes OCI) is 3,340,134 at FY2026 (0.59 %
lower) — no band or trigger changes; the definition decision remains open.

**Leverage.** Unchanged: gross borrowings 707,810 (leases 138,876 and deferred
payment liabilities 1,045,137 excluded; not total liabilities), net worth
3,359,769 → D/E **0.2107**; EBIT 461,327 / finance costs 86,534 → interest
cover **5.3312**; `leverage` SCORED 4/4 (strong) under the unchanged bands.
Consolidated scope only.

**RPT and K6.** Note 36 (pp. 376–377) yields 23 structured transaction extractions
(category × counterparty × period).
The revenue category sums to the note's own totals — FY2026
36,442 + 25,526 + 447 + 884 = **63,299**; FY2025 35,997 + 19,704 + 499 + 517 =
**56,717**; FY2024 35,449 + 16,654 + 385 + 390 = **52,878** — over revenue
from operations 1,468,853 / 1,282,184. Share **4.3094 %** vs **4.4235 %** =
**−0.1141 pp** (`rpt` 3/3, K6 CLEAR). The approved definition
(`RPT-EXTRACTION-AND-METRIC-DEFINITIONS-2026-10-17.md`, implemented) is the
change in share, in percentage points. For completeness only, the alternative
contribution measure ΔRPT/ΔRevenue = 6,582 / 186,669 = **3.53 %** is also far
below the 40 threshold, so K6 CLEAR does not depend on the choice. Known
limitation: for a category whose label wraps, the counterparty text of the
category's first row is merged with the label tail (e.g. "and Other Intangible
Assets Parent"); the category and amounts are correct and the metric does not
use counterparty text. Recorded, not fixed (evidence-only, cosmetic).

**Module E — 0/15, correctly UNKNOWN (not a defect).**

- `industry_growth`: the Analysys Mason report (pp. 152–196) gives the India
  mobile-connectivity market as ₹2.9 tn FY2026 → ₹5.2 tn FY2031 (p. 159)
  without stating a CAGR. The adjacent segment CAGRs (10 % entertainment,
  25 % productivity, 27 % smart-home, 23 % cloud, 18 % enterprise comms, etc.)
  belong to different markets; picking one, or deriving 12.38 % from the two
  endpoints, would designate a scope and a value the report does not state.
  The 2026-10-19 decision stands: UNKNOWN.
- `moat` / `visibility`: Tier-4 analyst assessments; the RHP has no structured
  field and no authority exists to fabricate ratings.
- `concentration`: no top-5 customer or supplier disclosure exists in the
  filing (keyword sweep); UNKNOWN.

**Valuation.** The RHP does not fix the price band: p. 129 prints "Price Band
of ₹[●] to ₹[●] per Equity Share" and "To be updated on finalisation of the
Price Band", and the Company's P/E and post-issue NAV rows are `[●]`. The band
used in the evaluation (₹1,065–1,119) is therefore the operator's
`MANUAL_ENTRY` (`EV-issue.price_band_high`: `SRC-MANUAL-ENTRY`, note "Manually
entered by the operator; NOT source-verified"). The `pe_vs_peers` 0/8 depends
on that operator band — recorded as such, not upgraded.

- Peer set: exactly the two companies the filing designates (p. 130), both
  `VALID`, both dated 2026-10-13, no invented peers: Bharti Airtel P/E 40.71,
  RoNW 20.32 %, NAV/share 244.60, diluted EPS 44.37; Vodafone Idea P/E 3.99,
  RoNW NM, NAV/share −3.30 (printed as "(3.30)"). Median P/E 22.35.
- Issuer P/E = 1,119 / 32.63 = **34.29** (+53.4 % vs 22.35) → `pe_vs_peers`
  SCORED **0/8**. Sensitivity: on the filing's own FY2026 diluted EPS 33.59,
  the premium would be +49.0 % (band 1/8). The criterion is defined on
  **post-issue** EPS (300,527 × 10⁶ / 9,209,030,830 = 32.63), so the engine's
  basis is kept and the alternative is recorded, not applied.
- `second_multiple` UNKNOWN: the peer table (face value, revenue, EPS basic,
  EPS diluted, P/E, RoNW, NAV) discloses **no EV/EBITDA and no P/B**, and no
  closing price value. A P/B could only be obtained by a two-step derivation
  (price = P/E × diluted EPS, then ÷ NAV/share), which the peer contract does
  not authorise; Vodafone's negative NAV (NM) would leave a single peer.
  Not derived, not invented.
- `sector_ipo_relative` UNKNOWN: no recent same-sector IPO valuations were
  supplied.
- Known diagnostic limitation: the UNKNOWN reason for `second_multiple` reads
  "no VALID peer multiple is available … Rejected peers: none supplied",
  although both peers are VALID and only their EV/EBITDA and P/B are absent.
  That string is frozen in `fixtures/vishal_nirmiti/expected_derived.json`;
  changing it would break the golden comparison, so it is recorded here
  instead.

**Disposition.** Net worth, leverage and RPT/K6: VERIFIED (unchanged).
Auditor opinion and K5 extraction: FIXED AND VERIFIED. K5's unquantified leaf
and K1's going-concern leaf: EVIDENCE STILL MISSING — one is genuinely absent
from the filing, the other needs a governed negative-confirmation rule.
Module E: EVIDENCE STILL MISSING BY DESIGN. Valuation: INVESTIGATION
COMPLETE; `pe_vs_peers` verified on an operator band, `second_multiple` and
`sector_ipo_relative` UNKNOWN for missing source data.

## Report C — Validation (exact commands)

| Command | Result |
|---|---|
| `PYTHONPATH=engine ./.venv/bin/python -m pytest tests/test_contingent_liabilities_extraction.py -q` | **8 passed**, 1 warning, 21.42 s |
| `… pytest tests/test_auditor_evidence_section.py -q` | **9 passed**, 19.97 s |
| `… pytest tests/test_step5_auditor_and_manual_terms.py tests/test_auditor_evidence_section.py -q` (after the `(?<!un)` fix) | **28 passed**, 5 warnings, 153.09 s (before the fix: 1 failed, 19 passed) |
| `… pytest` regression batch: CL, Jio remediation, RK Fashion, FS mapping, Jio RHP terms, peers, NIL-OFS, RPT, penalties, bridge | **79 passed**, 6 warnings, 203.64 s |
| `… pytest tests/test_peer_row_mapping_and_bounds.py -q` | **17 passed**, 1.44 s |
| `… pytest tests/test_cfo_pat_determinism.py tests/test_cross_ipo_issue_term_provenance.py tests/test_d_peer_1_no_synthetic_peers.py -q` | **24 passed**, 93.39 s; golden result `e84f8bc0…` unchanged |
| `cd frontend && npm test` | **89 passed**, 0 failed (798.68 ms) |
| `./.venv/bin/python -m compileall -q engine` | clean |
| `cd frontend && node --check api.js app.js` | clean |
| `PYTHONPATH=engine ./.venv/bin/python -m pytest tests -q` (full backend suite) | **1158 passed**, 0 failed, 38 warnings, 1154.83 s (baseline 1139 at `f42b6ce` + 19 new tests: 9 auditor, 8 contingent liabilities, 2 peer) |
| `git diff --stat -- config schema fixtures` | empty (no policy, schema or golden change) |

## Report D — Publication

- **Branch:** `arena/ae4d04e8-ipo-screening-engine`. **Base:** `main`
  `01ba66c12ca1195fd7acbd287c3e39a019808094` (untouched).
- **Implementation commit:** `af54cfc823a58b2c8c477f7f6264ac5eeb59f376`
  (remote-verified), carrying the auditor and K5 extractor changes, the two
  new test files, the updated pin and the two new peer tests. This Markdown
  amendment is published in the following docs-only commit; the tracker
  publication amendment records it.
- **PR #6:** must remain OPEN and UNMERGED; state re-verified after the push
  (`mergedAt: null`, head unchanged at `e05c0ef…`).
- **Tracker:** separate HD Fire and Jio sections plus the publication
  amendment appended to
  `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`.
- **Blockers:** HD Fire source row and both Windows evaluation stores remain
  inaccessible from Arena; Windows-only acceptance is outstanding. Module E
  needs a designated industry-scope decision, moat/visibility need analyst
  assessments, and K1's going-concern leaf needs a governed negative-
  confirmation rule.

## Report E — Final disposition

| Item | Disposition |
|---|---|
| HD Fire peer extraction / schema gate / audit failure / NIL-OFS / manual provenance | **FIXED AND VERIFIED** (code + executed tests) |
| HD Fire 7/100 arithmetic and semantics | **VERIFIED, NOT CHANGED** |
| HD Fire exact source peer row | **SOURCE-LEVEL VERIFICATION PENDING** (Windows only) |
| Jio auditor opinion (K1 first leaf) | **FIXED AND VERIFIED** (source + tests + live run) |
| Jio K5 quantified extraction | **FIXED AND VERIFIED**; K5 itself remains UNVERIFIED on the unquantified leaf (**EVIDENCE STILL MISSING** — genuinely absent) |
| Jio net worth / leverage / RPT / K6 | **VERIFIED** (unchanged) |
| Jio Module E | **EVIDENCE STILL MISSING BY DESIGN** (no designated CAGR, no analyst ratings, no concentration disclosure) |
| Jio valuation | **INVESTIGATION COMPLETE**; `pe_vs_peers` verified on the operator band; `second_multiple` / `sector_ipo_relative` **EVIDENCE STILL MISSING** |
| Jio K1 clearing | **NOT FIXED** — requires a governed going-concern negative-confirmation rule; evidence indicates no uncertainty, but absence is not treated as `False` |
| Scoring methodology / golden / historical records | **UNCHANGED** |
