# HD Fire Protect — investigation of reported 7.0 → 3.0

Date: 2026-10-21 (user-local task date). Repository baseline: `c4d9d5d6b38facde9adfb96898ba5d52a6c2b536`.
**Evidence-led investigation; no HD Fire evaluation or ingestion executed.**

## 1. Executive conclusion and strength of evidence

**The four-point decrease is explained by removing four unsupported promoter
post-holding points under D3/A21.** On the recorded earlier aggregates, base
10 minus the same receivables penalty 3 gave 7; the supplied current summary
has base 6 minus 3 = 3. The HD Fire source-shaped regression test confirms that
pre-Offer 95.33% + 4.67% was incorrectly reused as post-Offer 100% before D3.
Post-Offer cells are placeholders, not a disclosed percentage. Removing those
4/4 points is an intended correction, not grounds to restore 7.

**Qualification:** the old and new payloads and source files are unavailable;
this is a strongly supported code/source-shape explanation and exact aggregate
reconciliation, not a reproduced historical-input comparison. The current
report's other modules cannot be inspected from its unavailable full attachment.
No claim that every byte or every field of the two runs was equal is made.

**Litigation is a separate unresolved evidence-path discrepancy, not the four-point
score loss.** Earlier records describe criminal_or_regulatory **0/4**, not clean
4/4. A change from scored adverse zero to UNKNOWN changes availability/confidence,
not earned points. The available HD Fire §12 table supports two criminal cases
against Directors; the current parser still recognizes that table and returns the
adverse bucket. A24/A25 do not suppress positive findings merely for incomplete
negative coverage. Current UNKNOWN is defensible for an unread/unmapped input,
but cannot be certified as a complete reading of the recorded §12 evidence.

**No actual new auditor/CFO penalty removal is established.** Earlier investigation
records already attribute the only applied -3 to receivable_days_up and auditor exit
to UNKNOWN. The alternative prior -3 attribution is an unsupported hypothesis.

**Receivables remain UNVERIFIED at issuer-data level.** Formula, column-selection
contract and threshold pass focused tests, but HD Fire's actual balances, dates,
unit, days, period pairing and provenance are not present. Do not remove or certify
the current -3 without them. This penalty was recorded in the earlier 7.0 run too.

No new runtime defect sufficiently demonstrated to authorize a code fix was found.
Eight uncovered receivables contract cases were added without changing runtime.

## 2. Repository state, recovery and evidence inventory

Initial tools found local HEAD `01ba66c` on the correct branch, a modified README
and 410 published-tip paths mostly appearing untracked. Remote branch was c4d9d5d;
main 01ba66c; PR #6 OPEN/unmerged, head e05c0ef. Before touching the index, a
NUL-safe Git tree inventory compared **all 410 published files byte-for-byte** to
remote c4d9d5d: all identical, none missing. Only those matching paths were staged;
`git merge --ff-only origin/arena/95234306-ipo-screening-engine` restored ancestry
without changing file content. No reset, deletion, force-switch, new branch or
force-push was used. Worktree then clean at c4d9d5d. No unrelated file was discarded.

### Evidence grades

- **U (user-supplied current-run summary):** FINAL, 2026-10-20 18:54:30 UTC,
  engine/config v1.5.0, hash
  `02ce5e46ad12a3f85c59e69ed33c8b17acb23a6d4a53b165e48fe03f73200749`;
  base 6, penalties -3, final 3, available 19/unknown 81, Low 19%, insufficient
  data; D1/15; promoter/litigation/auditor UNKNOWN; board 1/2; receivables -3;
  auditor/CFO and EOM penalties UNKNOWN. Not independently authenticated payload.
- **H (historical documented run, not retrieved record):**
  `HD-FIRE-PROTECT-LIMITED-20261019-123134Z-final-551a7eab`, hash
  `551a7eab957ec8f6f2fec8cca77ce6951e0a0595b6ec9231e79e696e33c2aa3b`.
  `../HD-FIRE-JIO-SCORE-RECONCILIATION-2026-10-19.md:69–160,639–658` and
  `../HD-FIRE-RHP-EVIDENCE-RECONCILIATION-2026-10-20.md:94–112` record
  A2/B0/C3/D5/E0/F0, base10, receivables -3, final7, available27/unknown73.
  These records explicitly disclose that the Windows payload was not inspected.
- **S (preserved source excerpt/reconstruction):**
  `tests/test_hd_fire_primary_source_extraction.py:1–121,155–198`, and
  `../HD-FIRE-PRIMARY-SOURCE-RECOVERY-2026-10-20.md` §§2,4,5,6 record the
  SEBI-hosted Abridged Prospectus §§5/12, RHP dated 5 October 2026. Test line
  breaks are reconstructed; not an original PDF/OCR dump or the current run's PDF.
- **C (confirmed current code/history/test):** locations and outcomes below.

### Missing artifacts — searches and consequences

Search covered `/home/user` filenames (PDF/report/XLSX/DOCX/HTML/evaluation JSON),
repository tracked JSON/logs, configured default `build/evaluations`, `evaluations`,
store/upload/attachment directories, IPO store environment overrides and Git
history for both hashes. Only investigation documents describe the old hash;
no current hash record, persisted HD Fire input/output, evaluation manifest or
HD Fire PDF was found. No store-root override was configured. Other issuers' PDFs
and schema files are not HD Fire evidence. No other score-7 record was recovered.

**The full attached report is not exposed as a readable workspace attachment.**
Only the summary supplied in the task is available here. Therefore the complete
criterion list, K1–K6 statuses, missing-field list, other penalty dispositions,
bounds, provenance and config/input hashes cannot be independently inspected.
The summary is not silently relabelled as full-report inspection. All independent
code/history/source-shape work continued despite that boundary.

## 3. Causal regression matrix

Repository-relative paths below use `engine/ipo_screening/` unless qualified.
Classifications apply to demonstrated mechanisms; run-specific uncertainty is explicit.

| Item | Earlier evidence | Current evidence | Exact mechanism / relevant change / provenance | Classification and confidence | Effects and next action |
| --- | --- | --- | --- | --- | --- |
| promoter_post_holding | H: post100%, 4/4 | U: UNKNOWN, no earned points | S: Total A 167,035,000 /95.33%; B 8,195,000 /4.67%; post cells [●]. Old fallback added pre percentages. D3/A21 at 2ec607c, sections.py:837–893 now requires len(values)>=2 plus explicit post context and correct category; derived.py:1054–1061 propagates absent post | INTENDED CORRECTION; high for source-shaped mechanism, medium-high for exact remote run without payload | Earned/base/final -4; available -4; unknown +4; can affect K4 inputs. Keep D3. Explicit post disclosure would require its actual table/quote, never dilution arithmetic |
| litigation | H: criminal_or_regulatory, SCORED 0/4 (not four earned points) | U: UNKNOWN, no earned points | S: Against Directors: criminal2; Against Company/Promoters nil; By Company tax3, amount Rs0.40mn. sections.py:2154–2214 reads against criminal/regulatory count before clean gates; derived.py:1382–1395 reads bucket. HD Fire table test passes | UNRESOLVED run-specific source/extraction/input discrepancy; high that A24/A25 do not block this readable positive | If H→U state change, earned/final delta0; available -4; unknown +4. Need current scanned-page text/ranges/read status and table mapping, not a weakened clean gate |
| auditor_cfo_exit | H: UNKNOWN, 0 applied; no supported prior -3 | U: UNKNOWN carried in range | governance.auditor_or_cfo_exit_2y absent ⇒ passthrough UNKNOWN (derived.py:2299–2310); scoring.py:632–644 reserves 3. 345caf7 fixed builder dropping an explicitly supplied flag; builder.py:372–387 carries only established values | UNRESOLVED source evidence; high that no newly demonstrated applied-penalty delta explains -4 | UNKNOWN changes lower bound, not base penalty. Keep unknown absent dated resignation evidence. Do not infer from auditor tenure/change/appointment |
| trade receivables / receivable_days_up | H: -3 already applied; actual balances/days unavailable | U: -3, actual days not supplied | financial_tables.py:169–200,273–334 selects fiscal arrays, days=round(receivables/revenue*365,1); canonical_input.py:80–81,116–118,323–332 preserves days and excludes marked stub periods; derived.py:1789–1816 compares last two full FYs; config:1357–1365 >30 gives -3 | UNRESOLVED actual source correctness, not established new regression; high code contract, low issuer-data verification | Reported delta0. Require paired balances/revenues/dates, units and raw period array; do not erase penalty merely because current score is low |
| board_kmp, auditor and other subtotal components | H: D board1, auditor UNKNOWN; A2/C3 and B/E/F0 documented | U: board1, auditor UNKNOWN; D1, other module detail unavailable | derived.py:1428–1513 auditor needs opinion/change evidence; builder.py:359–370 still has board=False/exits=0 defaults. No new policy fixing those defaults authorized here | No demonstrated score change; unresolved complete input parity | D5→D1 matches promoter -4. Preserve known limitations; no silent broad governance-default repair |
| config/input/evidence/hash | H hash551a…; no payload/config hash | U hash02ce…; same version labels, no actual config/input hashes | evaluation.py:275–290 hashes deterministic payload incl config hash, input/evidence/snapshot hashes, derived, score etc. Config text fingerprint in config_validation.py:771–783 | INPUT OR EVIDENCE CHANGE is possible; exact partition UNRESOLVED | A differing hash does not identify cause. Compare immutable stored components when available; do not synthesize history or equate version string with code identity |

## 4. Commit and path trace: hypotheses accepted/rejected

### Promoter — demonstrated first divergence is extraction, not scoring

`2ec607c` implements A21/D3 explicit post-issue scope after `e2ce2c2`'s combined-row
guard. The old pre-fix `Total(A)` fallback searched numeric percentages and added
B without checking a disclosed post column. On the preserved HD Fire shape:
95.33 + 4.67 = 100.00; the two post columns remain `[●]`. The current fallback's
`len(values)<2` check (`sections.py:852–854`) prevents that substitution even
when the header says Post-Offer. A numeric second post column and correct category
remain accepted by positive-control tests. Thus this is not wholesale rejection
of valid post disclosure. The 85% arithmetic from 175,230,000 minus 26,284,500
sold shares is not an explicit post disclosure and is not supplied to the engine.

Canonical builder passes the extracted post field; absent post becomes UNKNOWN
at derived.py:1059–1060; criterion config:487–513 retains its existing bands.
The source-shaped test proves this first-layer divergence. Current run's exact
source identity/override path remains unavailable, so a newer completed Prospectus
with an explicit post figure cannot be excluded by examining the older RHP excerpt.

### Litigation — positive proof and negative-coverage proof differ

- `1bd468e` removes unsupported clean/SEBI false defaults (D5); `7bae763` adds
  symmetric regulatory handling. No match becomes UNKNOWN, not fabricated clean.
- `c204c82` (A23) makes negative coverage comprehensive by type and treats
  closed-period regulator denials as disclosed-negative, not universal absence.
- `41f2f86` (A24/A25 runtime) enforces company+promoters+directors for clean,
  strips a parenthetical party qualifier only for cell alignment, and records
  located/fallback/readability status before accepting absence.
- `_litigation_table_finding` requires detected header and row/key cell counts;
  only **against** rows establish adverse exposure. At :2209–2214 a positive
  criminal/regulatory count wins before unreadable-row/type/party clean gates
  (:2215–2238). A malformed or unrecognized layout can still produce UNKNOWN.
- `extract_governance` scans the located litigation window or fallback (:2709–2733).
  Seeing a positive remains sufficient on a fallback or partial window. No text
  scanned, an unreadable relevant page or absent table mapping can explain UNKNOWN;
  none of these is established as the exact current-run condition without its report.

Existing tests cover Director-only findings, qualifiers, nil rows, unreadable rows,
company-initiated proceedings, independent SEBI/ED negatives, and positive findings
on incomplete/fallback windows. The actual preserved HD Fire table returns
criminal_or_regulatory with a verbatim Director quote; nil SEBI does not clear ED.
The Company tax3 row is **by**, not against; no tax→criminal mapping is justified.
An unreadable positive must not be invented, but a readable positive must not be
discarded merely for lack of complete clean-population coverage.

### Auditor/CFO — input semantics, not penalty migration

No extraction producer for `auditor_or_cfo_exit_2y` exists in sections.py (history
search finds only the builder carry fix). A real supplied true triggers its own -3;
false is SCORED/not-triggered; absent reserves 3 with zero applied. Normalization
and derived passthrough do not translate `auditor_changed_3y` into resignation.
Current UNKNOWN does not establish no resignation; actual event/date evidence is
absent. An earlier *different* run applying -3 cannot be ruled out without its
payload, but neither the recorded reference run nor available evidence supports it.
The exact 18:54:30 reference time alone does not establish an event in its two-year window.

### Receivables — full period/normalization trace and limits

The canonical financial field is `financials.periods[].receivable_days`;
`trade_receivables` is the extracted balance-sheet amount used to calculate it.
No separately consumed `trade_receivable_days` field was found on this path.

1. Detect full FY labels from March31/FY/Fiscal headers; `financial_tables.py:387–399`.
2. Select rightmost n fiscal cells after note/interim columns (:401–429). The
   `950d239` correction predates the documented 2026-10-19 baseline `e1df89b`
   (see earlier score-reconciliation report header), so it is not established as
   a new change between that 7.0 baseline and current runtime.
3. Sort extracted FYs chronologically (:273–280), compute rec/revenue*365 rounded
   to one decimal (:299–303); no explicit annualization of interim revenue occurs
   on this path. Stock/flow in the same currency cancel units in the ratio.
4. Canonical RATIO_FIELDS preserves days without monetary scaling; supplied
   period order is retained, is_stub defaults false when absent. Derivation context
   selects canonical.full_periods (derived.py:155–156); last two full FYs enter
   `(latest/prior-1)*100`. Missing either gives UNKNOWN; zero prior gives NA.
5. Config strict >30 triggers -3; exactly supplied metric30 does not. Unknown
   trigger reserves magnitude rather than applying it (scoring.py:614–644).

**Contract limit:** full-FY validity is only as good as extracted/supplied labels
and stub metadata. Runtime cannot detect a mislabeled interim observation from its
numeric value alone, does not independently authenticate dates and does not prove
that every source table has the expected rightmost fiscal layout. A year-gap or
incorrectly labeled period needs inspection of actual payload/header; no new
comparability policy is invented here. Synthetic tests demonstrate exclusion of
marked annualized interim days, not absence of contamination in this issuer's run.

No actual HD Fire trade-receivable balances, derived days or fiscal pair can be
reported. The earlier primary-source report lists FY2024/25/26 revenue
Rs3,729.53/4,327.99/4,892.81 million, but those source excerpt values do not prove
that the same numbers reached either persisted evaluation or pair with any known
receivables. Do not mix them with invented balances to validate a -3.

## 5. Score, completeness and range reconciliation

| Quantity | Earlier documented H | Current supplied U | Explanation / limit |
| --- | --- | --- | --- |
| Base | 10 | 6 | -4 exactly matches removal of promoter4 |
| Applied penalties | -3 receivables | -3 receivables | No demonstrated change in applied total |
| Final | max(0,10-3)=7 | max(0,6-3)=3 | Confidence is not subtracted or multiplied into this score |
| Module D | promoter4 + litigation0 + board1 =5, RPT/auditor unknown | promoter unknown + litigation unknown + board1 =1 | Promoter explains earned loss; litigation does not |
| Available / unknown | 27 /73 | 19 /81 | -8/+8 consistent with promoter4 and litigation4 becoming UNKNOWN |
| Completeness | 27% Low | 19% Low | Available maximum points, not earned points; adverse scored0 still counted available previously |
| Other modules | A2/B0/C3/E0/F0 recorded | Sum other modules must be5 given base6,D1 | Retaining A2/C3 is consistent, not independently verified without full report |
| Unresolved penalties / bounds | Four UNKNOWN penalties totaling10 documented | Auditor/CFO and EOM UNKNOWN listed; other items not supplied | Known two reserve3+3. Full current reserve, caps, bounds and KO statuses cannot be reconstructed as facts |

`scoring.py:449–491` separately computes base, applied penalties, caps,
availability, confidence and bounds. An adverse litigation SCORED0 and an UNKNOWN
are not semantically interchangeable despite no earned-point difference. Changes
in K2/K4 or critical-data completeness may alter insufficiency/knockout states,
not a confidence-based score penalty; their full current status is unavailable.
The summary's INSUFFICIENT DATA is consistent with extensive unknown critical
inputs, but its exact deciding predicate cannot be certified from that summary.

This reconciles both the 4-point earned loss and the additional 4-point availability
loss without presuming a newly applied penalty or awarding litigation four points.
It is an evidence-bounded explanation, not proof of unchanged omitted fields.

## 6. Hash/input parity and exact residual evidence requirements

The same engine/config **version labels** do not prove equal source code, config
hashes, inputs or evidence. The scoring code has no recent commits changing its
formula (`git log -- scoring.py`: original fb822e5); recent extraction changes
can change canonical values while keeping version labels fixed. Result hashing
includes config/input/source manifest/market/peer hashes, plan, derived values,
knockouts, scores and penalties (`evaluation.py:275–290`); timestamps/IDs alone
are excluded. The two reported result hashes are leads, not causal proof.

No historical record was recovered to authenticate either hash or compare payload
components; the record IDs in documents are not the records themselves. A21's
extraction output difference is sufficient to plausibly change the hash, but cannot
account for the *entire* difference without those deterministic payloads.

Precise evidence needed to close remaining causal questions (not an instruction
to rerun or change policy): read-only copies of each stored evaluation's input,
result/derived/score/penalties, evidence manifest/source hashes, config hash and
captured filing identity; the exact source page texts/header/cells and page-status
metadata covering capital structure, litigation and financial statements. In
particular:

- post field's extraction versus reviewer/enrichment override and completed table;
- litigation selected range, reader result, header mapping, against-Director row;
- any resignation event/absence statement and two-year date basis;
- latest/prior FY labels, stub flags, receivable balances/revenues/days, unit and
  raw row mapping. Establish source parity before alleging parser regression.

No need to re-ingest or generate another evaluation to compare these immutable
artifacts if they become accessible. No request to repeat supplied information
or wholesale implementation approval is made.

## 7. Focused validation and uncovered-contract checks

Initial attempt `python3 -m pytest ...` failed before collection:
`No module named pytest`. Re-provisioning had removed installed dependencies.
Created ignored `.venv` and installed exact `requirements.txt` pins. No dependency
manifest was edited. No test failure was hidden by that environment restoration.

Actual successful command (log `focused-tests.log`):

```
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
 tests/test_receivable_period_contract.py tests/test_penalty_attribution.py \
 tests/test_promoter_holding_extraction.py tests/test_hd_fire_primary_source_extraction.py \
 tests/test_litigation_regulatory_defaults.py tests/test_auditor_tenure_defaults.py \
 tests/test_financial_statement_column_mapping.py \
 -k 'not jio_real_filing and not live_' -q
```

**137 passed, 3 deselected in 0.44 seconds; exit0; 0 failed/skipped/xfail/xpass,
no warnings reported.** Plugin progress through 25/50/75/100/125/137 is preserved.
Three deselections exclude unrelated live Jio/Vishal PDF checks; no HD Fire test
is excluded and no test is weakened. Synthetic penalty tests call the generic
fixture pipeline without a store; no HD Fire evaluation occurs. Existing HD Fire
tests only extract preserved text shapes; no ingestion, source download or evaluation.

Eight new tests in `tests/test_receivable_period_contract.py` pin previously
uncovered layer contracts: marked interim excluded despite annualized days;
one FY plus stub insufficient; missing latest FY not backfilled; valid full-FY
YoY and zero prior; three strict threshold cases; revenue/receivables same fiscal
column pairing. These encode existing semantics, not a target HD Fire score.
No source values in these synthetic examples are attributed to HD Fire.

` .venv/bin/python engine/tools/ipo_screen.py check-config` → **valid True,
10 profiles** (raw log `check-config.log`). No full backend/frontend rerun: no
runtime/frontend change, prior tested-tree evidence at c4d9d5d remains applicable;
focused tests cover the new test-only addition. Passing tests support the traced
contracts, not certification of the absent current payload's source correctness.

## 8. Corrective dispositions and completion boundary

**A. Verified implementation defect requiring a new fix:** none established in
available current code for this run. No runtime patch made. The known historic
pre/post bug is already fixed; the optional auditor-flag carry bug was fixed at
345caf7 and remains tested. A narrower litigation/table fix requires actual failed
page text or field mapping demonstrating it, not merely current UNKNOWN.

**B. Keep valid governance corrections:** D3 post disclosure, D5 no fabricated
negative, A23 type coverage, A24 party/readable-row controls and A25 absence
observability all remain. Their positive/negative asymmetry is confirmed.

**C. Missing/defective source/input evidence:** the current litigation discrepancy
needs actual page/range/payload inspection. Receivables' -3 needs actual financial
pair/provenance verification. Auditor resignation remains unknown absent event
support; no penalty reinstated from generic auditor change.

**D. Policy boundary:** no weight, threshold, formula, bucket, knockout, schema,
blanket default, golden or evidence-threshold change is authorized. General period
comparability validation beyond established stub/FY contracts, alternate promoter
derivation or broader audit/CARO semantics would require their own governed scope.
None is silently implemented here.

Completed: code-history/source-shape investigation, qualified score reconciliation,
causal matrix, independent contract tests, and tracker reconciliation. **Still
unverified:** byte-level old/new input parity, exact source of current litigation
UNKNOWN, actual receivables calculation, full current KO/penalty/range details and
any claim about multiple unavailable historical score7 runs. The score arithmetic
is justified conditionally; the current entire evaluation is not certified.

Publication is restricted to this report/log directory, the new test file and an
additive tracker entry. Protected paths and historical records remain unchanged.
Remote commit/content and main/PR state are verified after push and reported in
the completion response. Worktree cleanliness is checked then, not presumed here.
