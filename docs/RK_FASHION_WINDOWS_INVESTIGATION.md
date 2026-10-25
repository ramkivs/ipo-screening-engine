# R.K. Fashion: remaining Windows failures — investigation, NOT a repair

## Revision 19 status / concrete blocker

Base: `43a49497c7c13ed09126f0b7831b5f71b3ef2bce`, PR #10. User reports that the
reconciled Windows checkout still fails two promoter-post extraction assertions
(None versus72.25) and the real UI7 ingestion score assertion (40 versus44).
**Windows acceptance remains OPEN. The native extraction cause is NOT established.**
No failing-interpreter diagnostic/text/evaluation record was supplied with this
continuation. Linux is not Windows: an implementation patch cannot responsibly be
selected from these symptoms alone. No parser, canonical builder, scoring config,
production scoring, expected source value, hash or fixture fallback is changed.
This continuation publishes diagnostic observability and a missing-evidence scoring
regression, not a claim to have repaired the three failures.

## Checkout reconciliation / preservation

The restored Arena HEAD again starts at `dedb4b8` while its24 modified/untracked
paths are **byte-for-byte the requested43a49497 tree**. Git fetch, NUL-delimited
path comparisons and per-file blob comparison establish this before any edits.
No unrelated change is found; index starts at the old baseline. The new focused
commit uses published43a49497 as parent and an explicitly verified staged tree;
no reset, clean, branch switch, file restore/overwrite or force push is used.

The Arena harness equals the published blob, SHA256
`eeff90136ec06b6179a56c0baa05586b925961e636f2d742cbdfb70255e0c273`.
The user's **Windows-local uncommitted harness correction is not available here**;
it is neither modified nor incidentally committed. All five retained capture
bytes/digests match the protected original captures before/after investigation.
They are not normalized, regenerated or restored. External logs/JSON go under
`/home/user/rk-investigation/`, not Git.

## Original source and column meaning

- Source: `handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`;
 17,310,664 bytes,496 pages, SHA256
 `9a46095da97b4aea8dc9fe67df2a5923dcbb1968323f32ce2cb609d72b975198`.
- TOC routes Capital Structure to physical pages106–133. The relevant heading
 and column labels are on physical125 (printed121); category totals on physical126
 (printed122). They explicitly describe holding **before and after the Offer**.
- Columns are pre-offer share count/percentage, then post-offer count/percentage
 **at the lower price-band end ₹77**, then post-offer count/percentage
 **at the upper end ₹82**. Thus repeated percentages are distinct labelled
 post-offer scenarios, not extra promoter categories or unrelated numeric cells.
- `Promoters / Total(A)`: pre99.61; post72.22 at each price-band end.
 `Promoter Group / Total(B)`: pre0.06; post0.03 at each end.
 `Public / Total(C)`: pre0.33; post0.25 at each end.
 The parser combines only the **disclosed percentage cells** of promoter +
 promoter group: pre99.67 and post72.25. This is not a new calculation from
 unrounded share counts; summing rounded printed percentages can differ from
 rounding a combined count ratio. Public is never added. The combinedA+B+C row
 is not the promoter total and must remain excluded.

## Source → parser → canonical → provenance

`load_pdf_source` hashes binary bytes and opens a fresh pypdf reader.
`TOCRouter` supplies106–133; `SectionExtractor` reads/caches text, separates
nonempty stripped lines, identifies standaloneTotal(A), reads percentage cells,
requires explicit post-offer context within120 preceding section lines and
classifies the nearest heading beforeTotal(B) within60 lines (B scan bounded200).
These are **observed existing gates**, not an assumption about native Windows.

In Arena pypdf6.20.1, Total(A) is section line1723 on page126:
`Total (A) 1,12,06,672 99.61 1,12,06,672 72.22 1,12,06,672 72.22`.
The actual table header is56 lines before it (page125); “before and after the
Offer” is58 lines before it. Total(B) is
`Total (B) 5,100 0.06 5,100 0.03 5,100 0.03`, classified`promoter group`.
All post-value gates succeed. Raw post72.25 normalizes asPERCENT;
`CanonicalInputBuilder._build_capital_structure` retains72.25, with no fixture
fallback. Missing raw extraction would instead map toNone as designed.

Existing provenance attaches source`RHP-U18109WB2010PLC144256-R.-9a46095d`,
DETERMINISTIC_PDF and a **PROCESSING_SUMMARY** (not a verbatim source quote), with
page106/Capital Structure (the section start). That locator is approximate, NOT
proof that the table is on106; physical125/126 are separately verified above.
No new evidence quote/page is manufactured or changed to disguise this limitation.

Windows could differ in source bytes, text, routing, read failures, a gate,
canonical mapping or test-only context. **None is asserted to be the cause.**
The enhanced read-only diagnostic exposes actual parser-gate rows/pages/context,
raw extractions, dependency versions, eleven implementation fingerprints (raw
and LF-normalized hashes, without modifying files), checkout status, canonical
capital/evidence and full native
criterion/penalty/bounds/knockout/provenance evaluation when requested.

## Score causality, without inventing four points

The complete Arena evaluation of the real canonical input gives modules
A20+B10+C10+D5+E2+F0 = **base47**, applied margin-spike penalty **−3**, final**44**,
no final-score caps. CriterionD/promoter_post_holding is SCORED, value72.25,
matched`>60`, score4/4. Existing auditor/litigation/KMP/moat/visibility/market
unknowns stay unknown; their defaults are not restored.

A controlled deep-copy intervention removes **only** promoter_post_pct and its
field evidence, then evaluates again with the same config/time, without a store:

| Quantity | Source-supported input | Controlled missing holding |
|---|---:|---:|
| ModuleD earned / unknown | 5 /8 | 1 /12 |
| Base | 47 | 43 |
| Applied penalties | −3 | −3 |
| Final | 44 | 40 |
| Available / unknown points | 67 /33 | 63 /37 |
| Lower / upper bound | 31 /77 | 27 /77 |

All other criterion records and penalty records are identical. This is now a
regression assertion using the real extracted filing, not a production fallback
or a claim to have reproduced native Windows. For a genuinely missing holding,
**40 is correct under the existing evidence-based rules**. For the verified
source-supported input,44 is the correct current expectation. A separate scoring
defect is not established. The native criterion trace is still needed to confirm
that no additional differences occur in the user's run. Do not patch the scorer
or simply add4 points.

### Complete source-supported criterion trace (Arena)

| Module | Criterion | State | Earned | Value | Decision |
|---|---|---|---:|---|---|
| A | `revenue_cagr` | SCORED | 6.0 | 51.164912073894264 | matched > 25 |
| A | `margin_trend` | SCORED | 5.0 | expanding | matched expanding |
| A | `roce` | SCORED | 5.0 | 57.74 | matched > 20 |
| A | `cfo_quality` | SCORED | 0.0 | -0.09835461822593398 | matched else |
| A | `leverage` | SCORED | 4.0 | strong | matched strong |
| B | `pe_vs_peers` | SCORED | 8.0 | -54.30622076225025 | matched <= -20 |
| B | `second_multiple` | SCORED | 0.0 | 82.89560258664743 | matched else |
| B | `peg` | SCORED | 2.0 | 0.12851182365505426 | matched < 1; capped at 2.0 by low_base_year |
| B | `sector_ipo_relative` | UNKNOWN | — | — | no recent same-sector IPO valuations were supplied, so the relative test cannot be evaluated |
| C | `fresh_share` | SCORED | 3.0 | 100.0 | matched > 70 |
| C | `ofs_seller_type` | SCORED | 2.0 | none_or_small | matched none_or_small |
| C | `promoter_ofs_pct` | SCORED | 2.0 | 0.0 | matched == 0 |
| C | `dilution` | SCORED | 0.0 | False | matched false |
| C | `use_of_proceeds` | UNKNOWN | — | — | the blind_heavy test ((GCP + unidentified acquisition)/fresh > 20%) cannot be evaluated because a GCP or unidentified-acquisition amount is undisclosed. The legal maximum is not substituted, and an undisclosed amount is not read as zero, because either would let a blind-heavy offer pass the test |
| C | `pre_ipo_placement` | SCORED | 2.0 | none_or_near_ipo | matched none_or_near_ipo |
| C | `lockin` | SCORED | 1.0 | intact | matched intact |
| D | `promoter_post_holding` | SCORED | 4.0 | 72.25 | matched > 60 |
| D | `litigation` | UNKNOWN | — | — | the litigation status of the promoters, directors and company is not established |
| D | `rpt` | SCORED | 1.0 | 10.79 | matched <= 15 |
| D | `auditor` | UNKNOWN | — | — | the audit opinion is not disclosed, so auditor status cannot be established |
| D | `board_kmp` | UNKNOWN | — | — | the number of KMP exits in the last two years is not disclosed |
| E | `industry_growth` | SCORED | 1.0 | 4.45 | matched >= 0 |
| E | `moat` | UNKNOWN | — | — | the market-position and moat assessment is not recorded |
| E | `concentration` | SCORED | 1.0 | 34.1 | matched <= 50 |
| E | `visibility` | UNKNOWN | — | — | the capacity and order-book visibility assessment is not recorded |
| F | `gmp_trend` | UNKNOWN | — | — | gmp market data is not usable: block not supplied |
| F | `market_regime` | UNKNOWN | — | — | regime market data is not usable: block not supplied |
| F | `retail_nii_penalty` | UNKNOWN | — | — | the penalty trigger could not be evaluated from the supplied inputs |
| F | `overall_subscription` | UNKNOWN | — | — | subscription market data is not usable: block not supplied |
| F | `nii_subscription` | UNKNOWN | — | — | subscription market data is not usable: block not supplied |

### Additional penalties (Arena)

| Penalty | State | Points | Decision |
|---|---|---:|---|
| `margin_spike` | SCORED | -3.0 | triggered |
| `receivable_days_up` | UNKNOWN | 0.0 | the trigger could not be evaluated; the penalty is neither applied nor ignored, and is carried in the lower bound |
| `auditor_cfo_exit` | UNKNOWN | 0.0 | the trigger could not be evaluated; the penalty is neither applied nor ignored, and is carried in the lower bound |
| `discounted_allotments` | SCORED | 0.0 | not triggered |
| `unreconciled_metrics` | UNKNOWN | 0.0 | the trigger could not be evaluated; the penalty is neither applied nor ignored, and is carried in the lower bound |
| `regulatory_dependence` | UNKNOWN | 0.0 | the trigger could not be evaluated; the penalty is neither applied nor ignored, and is carried in the lower bound |
| `eom_caro` | UNKNOWN | 0 | materiality metric eom_materiality is UNKNOWN; the penalty is neither applied nor ignored, and is carried in the lower bound |

UNKNOWN penalty rows are not evidence of an inactive trigger. Unresolved penalty
exposure remains13 points in the lower bound, including the ModuleF subscription
penalty; this investigation does not convert them to safe defaults.

## Validation and publication receipt

- Original three + related promoter parser tests: **11passed,1warning,39.16s**.
- Four complete related modules after the new governance regression:
 **42passed,3warnings,128.11s**.
- Full suite: **1,918passed,0failed/skipped/deselected,25warnings,947.53s**
 (15m47s pytest, Linux only). Count+1 is the real-filing missing-value
 governance regression; no tests removed. Cache14,106hits/1,596decoded pages.
 Timing is correctness evidence, not a new comparative performance baseline.
- Frontend **93passed**,0failed/skipped; pip check,4schemas,6frozen pins,
 unchanged golden, inactivev1.6, compileall PASS. Diagnostic --score-trace produces
 a complete external JSON; attempting output to the harness is refused before
 extraction, harness bytes unchanged.
- New scope relative43a49497 is four paths: this report, tracker,
 `tests/diagnose_windows_portability.py`, `tests/test_rk_fashion_reconciliation.py`.
 The combined PR has25 paths. All production/config/schema/evidence/fixture/CI/
 harness paths remain unchanged by this continuation.
- Exact publication SHA, new full-CI JUnit receipt and final remote OPEN/unmerged
 state are recorded in PR#10's revision19 investigation closeout comment.
 This is a blocked investigation publication, **not a Windows extraction repair**.

## Exact missing evidence / next action

From the SAME failing Windows pytest interpreter, with the local harness and
restored evidence left untouched, collect one new external UTF-8 JSON:

```powershell
python tests/diagnose_windows_portability.py --full-extraction --score-trace --output "$env:TEMP\rk-windows-score-before-repair-19.json"
```

Use a new filename if it exists; share that JSON before changing packages or
repairing files. It includes actual PDF/capture hashes, runtime metadata, read
status, raw text on125/126, parser gates, raw/canonical capital fields, evidence
and complete native evaluation record. No store/workbook/checkout writes;
existing output files cannot be overwritten. If standalone extraction succeeds
but pytest still fails, that distinction is evidence: obtain failing-test locals/
trace next rather than assigning a parser cause from a successful standalone run.
**Blocked:** establish the native extraction divergence before selecting a general
implementation repair; validate it on Windows. No routine approval is requested.
