# Jio Platforms: artifact-assisted reconciliation of 33/100

Date: 2026-10-23. **Read-only application/evidence investigation; report-only publication authorized.** No ingestion, extraction, discovery, scoring or evaluation was run. JSON inspection, comparison and independent digest calculation are not an evaluation rerun.

## 1. Executive conclusion

The recovered records establish **33 earned points, zero applied global penalties, 43 UNKNOWN positive-point maxima, and 10 unresolved global downside points**. Consequently the stored interval is **23–76**. Available-point completeness is 57%, not 57 earned points. Known criteria lose 24 points against their maxima; missing criteria are not all that prevents 100.

The latest input contains **`market: {}`**. All four market blocks are constructed as MISSING with empty values, null block timestamps and no source IDs. This is absence at the input-to-snapshot boundary, not evidence of weak market conditions, stale observations or provider rejection. The source upload handler has no market-connector population step. The separate flat/nested enrichment mismatch exists, but **is not demonstrated to have caused this target's empty input**.

The canonical Final outcome is **NONTERMINAL_UNRESOLVED**, reason **MISSING**, because the GMP snapshot has neither percentage nor trend. Its legacy score verdict is INSUFFICIENT_DATA because going-concern and SEBI/ED inputs are UNKNOWN. K1/K2/K5 are UNVERIFIED, not triggered or waived. A diagnostic score can be displayed independently of canonical Final eligibility.

Several earlier hypotheses must be narrowed or withdrawn against the newer publication source: SEBI/ED favourable defaulting, contingent-flag mapping omission, and hardcoded 15-year peer history **are not present in that source**. Positive-evidence governance policies intentionally retain UNKNOWN. Conversely the provenance map loss and extracted-ID/A15 fallback mismatch are demonstrated in the actual records.

**Remaining source-level limits:** the bundle contains normalized results and selected evidence, not the complete pre-normalization extraction report, original field map, provider responses or Windows source identity. It establishes which values failed to reach scoring; it cannot prove original-source absence for every missing field. No speculative defect is promoted into a proven historical cause.

## 2. Artifact integrity and source/runtime correspondence

### 2.1 Publication and inventories

Evidence branch: `evidence/jio-score-33-recovery-20261023`; verified remote tip **ebb8a6c6b0d12e54228ec6b523bda025e927fb0b**. All 28 published evidence-directory blobs were accessible and read: two READMEs, checksum manifest, two inventories, recovery summary, 18 persisted artifacts, and four API captures. [Publication README](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/README.md) identifies 26 recovered originals and two publication additions. [Recovery README](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/README.txt) identifies the Windows source store, recovery time `2026-10-23 11:58:36 +05:30`, and read-only export. Inventories record nine artifacts per evaluation and four HTTP-200 GET captures. Those inventory statements are retained assertions; Arena did not access Windows.

Latest (**L**): `JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794`. Previous (**P**): `JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872`. In this report L/file and P/file refer to the exact publication paths `docs/investigations/jio-ipo-score-33/artifacts/<evaluation-id>/file`. API references use the sibling `api-get-responses/<evaluation-id>/` directory. Links pin the publication commit, not mutable branch names.

### 2.2 Integrity findings—not an unconditional “all checksums passed”

- **16/26** raw recovered-file SHA-256 declarations match published bytes exactly: eight non-lifecycle persisted JSON files for each evaluation.
- **10/26 do not match literal published bytes**: README.txt; both inventories; recovery-summary.json; four API captures; and two lifecycle files.
- For nine mismatches, in-memory restoration from LF to CRLF reproduces the declared digest exactly. README.txt matches with its existing BOM and LF interior retained, changing only its final LF to CRLF. No evidence copy was rewritten to make a check pass.
- Thus all ten mismatches are reproducible line-ending transformations. This is not evidence of semantic financial-data alteration, but **the publication README's byte-for-byte claim does not hold literally for all 26 files**. Preserve the manifest and disclose the discrepancy; obtain the original ZIP if original transport-byte identity is required.
- **All 14 internal manifest artifact digests pass**: seven artifacts per evaluation, including canonical record, evaluation, input, evidence, market, peers and result. These hashes concern parsed canonical JSON, not raw file bytes.
- Both input snapshot hashes and both market material hashes were independently reproduced. Both result hashes were independently reproduced from the frozen payload described by `evaluation.py:528–547`, without evaluating financial inputs. The canonical config hash from both source configurations also equals the stored hash.
- Internal manifests do not cover lifecycle.json or API responses; do not extend the 14 checks to those files.

Canonical digest calculation used the inspected hash grammar: NFC strings, floats represented as `{"__float__": repr(value)}`, sorted JSON keys and compact UTF-8. This was a standalone standard-library data audit, not an engine import or score execution. See [hashing.py:22-72](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/hashing.py#L22-L72) and [evaluation.py:508-547](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/evaluation.py#L508-L547).

### 2.3 Three revisions must not be conflated

| Identity | Established state |
|---|---|
| Arena source reference | `1096f3e978d80df3358e984afe481f947a74f804`; all 380 local published-file bytes match |
| Evidence publication | `ebb8a6c6b0d12e54228ec6b523bda025e927fb0b`, parent `75df573e96a8499ad06865cf5cd29e4da244ade7` |
| Relationship | GitHub compare reports **diverged**, common ancestor `e05c0efbca1ecb3024e52da73a22e180ea171118`; publication side ahead 91 / behind 19 relative to Arena reference |
| Windows runtime | **UNVERIFIED**: artifacts report engine/config 1.5.0 and spec 1.5, but contain no authenticated deployed commit/tree fingerprint |
| Stored config | `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b`, matching canonical configuration at both source references |

Publication-source `derived.py`, `scoring.py`, `snapshots.py`, `canonical_input.py`, `evaluation.py` and `semantic_validation.py` byte-match the Arena reference. Extraction/builder/service/enrichment and canonical-record files differ. Therefore this report inspects **both**; publication-source line references below are candidate producing-path evidence, **not proof of deployed revision**. The evidence-only publication does not retroactively authenticate Windows code. A matching config cannot do so either.

The retained local PDF SHA-256 independently equals the target filing hash `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`. Target registry also contains an official-RHP URL with this hash. Byte identity is established; source authenticity/coverage cannot be inferred merely from the local file's former non-authoritative label or a recorded URL. No PDF extraction was executed in this task.

## 3. Verified score, known-value losses and interval

Authoritative baseline: [L/result.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/result.json) `/score`, `/score_range`, `/confidence`, `/penalties`; repeated identically in [P/result.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/result.json) apart from evaluation identity/result hash.

| Module | Max | Earned | Known scored maxima | UNKNOWN positive maxima |
|---|---:|---:|---:|---:|
| A | 25 | 17 | 25 | 0 |
| B | 20 | 1 | 12 | 8 |
| C | 15 | 11 | 11 | 4 |
| D | 15 | 4 | 9 | 6 |
| E | 15 | 0 | 0 | 15 |
| F | 10 | 0 | 0 | 10 |

**Totals: 100 maximum, 33 earned, 57 known criterion maxima, 43 UNKNOWN criterion maxima.** All module scores sum to 33. `penalties_total=0`; `score_before_caps=33`; no caps applied. The stored plan is standard, no structure overlays. Retail-heavy overlay selection is itself unresolved because `qib_quota_pct` is UNKNOWN; the record says it was not applied. No overlay change is assumed.

The recorded unresolved global downside is exactly:

| Penalty ID | Trigger metric/input | Potential magnitude | Stored applied points | State |
|---|---|---:|---:|---|
| `auditor_cfo_exit` | `governance.auditor_or_cfo_exit_2y` | 3 | 0 | UNKNOWN |
| `unreconciled_metrics` | `financials.adjusted_metrics_unreconciled` | 2 | 0 | UNKNOWN |
| `regulatory_dependence` | `business.regulatory_dependence` | 2 | 0 | UNKNOWN |
| `eom_caro` | `governance.eom_materiality` | 3, worst configured scale | 0 | UNKNOWN |

Margin spike, receivable-days growth and discounted-allotment penalties are recorded SCORED/not triggered, each zero. UNKNOWN penalties are **not already-applied deductions**.

Arithmetic: `57/(57+43) × 100 = 57%` (the unrounded stored scalar is `56.99999999999999`); confidence Low under 95/80 thresholds. Lower bound `33 + 0 − (3+2+2+3) = 23`. Upper bound `33 + 0 + 43 = 76`. Known criteria forgo `57−33=24` points; UNKNOWN points are not all recoverable, and 76 is not a promised future score.

Source: `scoring.py:429–491` aggregates modules, applies global penalties/caps and constructs bounds; `570–650` carries unknown trigger magnitude and worst EOM scale. Config `1346–1409` gives global penalty magnitudes. This is an arithmetic reconciliation of stored values, not a scoring rerun.

`retail_nii_penalty` is an additional UNKNOWN **module criterion** with max 0/min −2, not one of those four global penalties and not part of 43 or 10. Subscription inputs are missing, so no actual retail/NII deduction is made. Module F currently floors at zero. The interval implementation counts unresolved *global* penalties; it does not add this module penalty to the ten.

## 4. Complete 27-entry missing/unverified reconciliation

All rows below reproduce array order, category, exact `item` identifier and `state` from L/result.json `/missing_unverified[i]`. Each pointer also identifies its stored `detail` and `points_affected`. “Confirmed” refers to the consumed state/cause stated in the row; original source absence is not claimed unless established. The exact diagnostic wording is included in Appendix A.

| # / artifact pointer | Category / exact identifier | State | Effect | Resolution requirement | Cause certainty |
|---|---|---|---|---|---|
| 1: `/missing_unverified/0` | CRITERION / `second_multiple` | UNKNOWN | 4 upper-bound points | Both peer EV/EBITDA absent and P/B null; obtain eligible second-multiple evidence and issuer pair. | Confirmed data absent at input; original table/provider availability unproven |
| 2: `/missing_unverified/1` | CRITERION / `sector_ipo_relative` | UNKNOWN | 4 upper-bound points | Supply justified historically eligible same-sector IPO issue P/Es; no array is supplied. | Confirmed input absence; acquisition cause unproven |
| 3: `/missing_unverified/2` | CRITERION / `use_of_proceeds` | UNKNOWN | 4 upper-bound points | Read actual GCP allocation schedule/placeholder and any eligible later disclosure; preserve unknown. | Confirmed GCP null/marker; genuine source nondisclosure not independently settled |
| 4: `/missing_unverified/3` | CRITERION / `promoter_post_holding` | UNKNOWN | 4 upper-bound points | Disclosed post-issue promoter/group percentage and applicable column/party evidence under A21. | Confirmed pre/post null; extraction versus nondisclosure unproven |
| 5: `/missing_unverified/4` | CRITERION / `auditor` | UNKNOWN | 2 upper-bound points | Supported three-FY auditor tenure first; reputation and EOM evidence also remain null. | Confirmed missing tenure; original source recognition unproven |
| 6: `/missing_unverified/5` | CRITERION / `industry_growth` | UNKNOWN | 5 upper-bound points | Applicable forward CAGR, scope, forecast period and source together. | Confirmed four nulls; source availability unproven |
| 7: `/missing_unverified/6` | CRITERION / `moat` | UNKNOWN | 5 upper-bound points | Attributed authorized qualitative assessment with supporting rationale. | Confirmed no consumed assessment; not automatic document extraction |
| 8: `/missing_unverified/7` | CRITERION / `concentration` | UNKNOWN | 3 upper-bound points | Supported top-five customer or supplier percentage; inspect routing/table recognition. | Confirmed both null; original disclosure unproven |
| 9: `/missing_unverified/8` | CRITERION / `visibility` | UNKNOWN | 2 upper-bound points | Attributed visibility assessment supported by contracts/capacity/revenue evidence. | Confirmed no consumed assessment |
| 10: `/missing_unverified/9` | CRITERION / `anchor_quality` | UNKNOWN | 3 upper-bound points | Governed anchor allocation and justified quality, nested block with timestamp/source. | Confirmed block absent; source availability unproven |
| 11: `/missing_unverified/10` | CRITERION / `qib_subscription` | UNKNOWN | 3 upper-bound points | Eligible official category subscription snapshot with timestamp/source. | Confirmed block absent; source availability unproven |
| 12: `/missing_unverified/11` | CRITERION / `gmp_trend` | UNKNOWN | 2 upper-bound points; A9 related | Attributable selected publisher observation/trend plus qualification; no synthesized trend. | Confirmed block absent; qualification also unresolved |
| 13: `/missing_unverified/12` | CRITERION / `market_regime` | UNKNOWN | 2 upper-bound points | A8-M-qualified NIFTY series/session/cutoff and authorized producer. | Confirmed block absent; qualification/implementation prerequisites open |
| 14: `/missing_unverified/13` | CRITERION / `retail_nii_penalty` | UNKNOWN | Potential module −2; no applied deduction | Eligible retail/NII category subscription values. | Confirmed input missing; distinct from four global penalties |
| 15: `/missing_unverified/14` | KNOCKOUT / `K1` | UNVERIFIED | Safety gate; not fixed points | Going-concern positive evidence or separately approved negative-confirmation rule; no false default. | Confirmed missing going_concern_uncertainty; A19 limits negative inference |
| 16: `/missing_unverified/15` | KNOCKOUT / `K2` | UNVERIFIED | Safety and critical-data gate | Regulator-specific party/time coverage under A23/A25; no absent=clear inference. | Confirmed missing sebi_ed_action_active; original coverage unproven |
| 17: `/missing_unverified/16` | KNOCKOUT / `K5` | UNVERIFIED | Safety gate; not fixed points | Positive unquantified exposure evidence or governed negative-confirmation policy under A20. | Confirmed quantified ratio known; unquantified flag null |
| 18: `/missing_unverified/17` | MARKET / `anchor` | MISSING | Duplicate block diagnostic for anchor criterion | Populate qualified nested anchor observation, not just a flat alias. | Confirmed block not supplied |
| 19: `/missing_unverified/18` | MARKET / `subscription` | MISSING | Duplicate block diagnostic; QIB and retail/NII | Populate eligible nested subscription observation. | Confirmed block not supplied |
| 20: `/missing_unverified/19` | MARKET / `gmp` | MISSING | Duplicate block diagnostic; A9 Final withheld | Selected attributable observation and separately accepted qualification/hash contract. | Confirmed missing; generic digest cannot resolve |
| 21: `/missing_unverified/20` | MARKET / `regime` | MISSING | Duplicate block diagnostic for market_regime | Qualified NIFTY evidence and approved integration. | Confirmed block not supplied |
| 22: `/missing_unverified/21` | PENALTY / `auditor_cfo_exit` | UNKNOWN | 3 lower-bound exposure; applied 0 | Evidence for auditor/CFO resignation in two years; map flag if supported. | Confirmed flag absent; dropping not shown in publication builder |
| 23: `/missing_unverified/22` | PENALTY / `unreconciled_metrics` | UNKNOWN | 2 lower-bound exposure; applied 0 | Evidence whether adjusted metrics are reconciled to Ind AS; map flag if supported. | Confirmed flag absent; dropping not shown in publication builder |
| 24: `/missing_unverified/23` | PENALTY / `regulatory_dependence` | UNKNOWN | 2 lower-bound exposure; applied 0 | Evidence-backed single-licence/price-control dependence determination. | Confirmed null; assessment/source route unproven |
| 25: `/missing_unverified/24` | PENALTY / `eom_caro` | UNKNOWN | 3 lower-bound exposure; applied 0 | Supported EOM/CARO materiality; do not turn unqualified opinion into no EOM. | Confirmed materiality null; source/assessment unproven |
| 26: `/missing_unverified/25` | CRITICAL_DATA / `going_concern_uncertainty` | UNKNOWN | Critical-data INSUFFICIENT_DATA; duplicates K1 | Same evidence/policy requirement as K1. | Confirmed critical missing; not extra point loss |
| 27: `/missing_unverified/26` | CRITICAL_DATA / `sebi_ed_action_active` | UNKNOWN | Critical-data INSUFFICIENT_DATA; duplicates K2 | Same evidence/coverage requirement as K2. | Confirmed critical missing; not extra point loss |

The exact composition is **14 CRITERION entries** (13 positive criteria plus retail/NII penalty), **3 KNOCKOUT**, **4 MARKET**, **4 PENALTY**, **2 CRITICAL_DATA** = **27**. This corrects the earlier incomplete 13+4+3 accounting. Categories overlap causally: one missing SEBI flag creates K2 and critical-data rows; one missing subscription block affects QIB and retail/NII. No PEER rejection rows exist: both peers were VALID. N/A is not one of these 27 target rows.

## 5. Criterion-by-criterion values and resolution requirements

Every row below is read from L/result.json `/score/modules` and its `criteria` array. No new criterion value was computed by the engine.

| Module / exact criterion | Stored value | State | Earned / max | Resolution / interpretation |
|---|---|---|---:|---|
| A / `revenue_cagr` | 15.788898186863264 | SCORED | 4 / 6 | 15.788898% earns 4, not max 6; audited FY2024–FY2026 inputs. |
| A / `margin_trend` | "stable" | SCORED | 3 / 5 | Stable is a known 3/5 band, not missing. |
| A / `roce` | 10.76 | SCORED | 1 / 5 | Disclosed latest ROCE 10.76% takes precedence; earns 1/5. |
| A / `cfo_quality` | 2.6205574239437164 | SCORED | 5 / 5 | Cumulative CFO/PAT 2.620557 earns full 5. |
| A / `leverage` | "strong" | SCORED | 4 / 4 | Strong earns full 4. |
| B / `pe_vs_peers` | 53.43890313809292 | SCORED | 0 / 8 | Premium 53.438903% exceeds 50%; configured else band correctly earns 0. |
| B / `second_multiple` | null / absent | UNKNOWN | — / 4 | Both peer EV/EBITDA absent and P/B null; obtain eligible second-multiple evidence and issuer pair. |
| B / `peg` | 1.8627215745378736 | SCORED | 1 / 4 | 1.8627215745 is above 1.5 and at most 2.5; correctly earns 1. |
| B / `sector_ipo_relative` | null / absent | UNKNOWN | — / 4 | Supply justified historically eligible same-sector IPO issue P/Es; no array is supplied. |
| C / `fresh_share` | 100.0 | SCORED | 3 / 3 | Fresh share 100% earns 3; fresh amount carries aggregator authority warning. |
| C / `ofs_seller_type` | "none_or_small" | SCORED | 2 / 2 | Explicit OFS 0 and empty sellers: no/small seller bucket. |
| C / `promoter_ofs_pct` | 0.0 | SCORED | 2 / 2 | OFS 0 yields zero sale share; not a missing promoter holding substitute. |
| C / `dilution` | true | SCORED | 1 / 1 | Known true, full point. |
| C / `use_of_proceeds` | null / absent | UNKNOWN | — / 4 | Read actual GCP allocation schedule/placeholder and any eligible later disclosure; preserve unknown. |
| C / `pre_ipo_placement` | "none_or_near_ipo" | SCORED | 2 / 2 | Empty placements currently score none/near IPO; no primary evidence link proves completeness. |
| C / `lockin` | "intact" | SCORED | 1 / 1 | Intact from lock-in true; absent leaf provenance warrants review, not automatic nullification. |
| D / `promoter_post_holding` | null / absent | UNKNOWN | — / 4 | Disclosed post-issue promoter/group percentage and applicable column/party evidence under A21. |
| D / `litigation` | "criminal_or_regulatory" | SCORED | 0 / 4 | Adverse criminal/regulatory classification, source quote identifies RJIL criminal complaints; entity scope remains to review. |
| D / `rpt` | 4.3094 | SCORED | 3 / 3 | 4.3094% is below 5%, full 3; source transactions exist but scalar evidence linkage is absent. |
| D / `auditor` | null / absent | UNKNOWN | — / 2 | Supported three-FY auditor tenure first; reputation and EOM evidence also remain null. |
| D / `board_kmp` | "other" | SCORED | 1 / 2 | Other from independence false and exits 0; earns 1. Independence has registry evidence, exits lack direct linkage. |
| E / `industry_growth` | null / absent | UNKNOWN | — / 5 | Applicable forward CAGR, scope, forecast period and source together. |
| E / `moat` | null / absent | UNKNOWN | — / 5 | Attributed authorized qualitative assessment with supporting rationale. |
| E / `concentration` | null / absent | UNKNOWN | — / 3 | Supported top-five customer or supplier percentage; inspect routing/table recognition. |
| E / `visibility` | null / absent | UNKNOWN | — / 2 | Attributed visibility assessment supported by contracts/capacity/revenue evidence. |
| F / `anchor_quality` | null / absent | UNKNOWN | — / 3 | Governed anchor allocation and justified quality, nested block with timestamp/source. |
| F / `qib_subscription` | null / absent | UNKNOWN | — / 3 | Eligible official category subscription snapshot with timestamp/source. |
| F / `gmp_trend` | null / absent | UNKNOWN | — / 2 | Attributable selected publisher observation/trend plus qualification; no synthesized trend. |
| F / `market_regime` | null / absent | UNKNOWN | — / 2 | A8-M-qualified NIFTY series/session/cutoff and authorized producer. |
| F / `retail_nii_penalty` | null / absent | UNKNOWN | — / 0 | Eligible retail/NII category subscription values. |

### Valuation dependency trace

[L/input.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/input.json) `/snapshot/input/peers` contains Bharti P/E **40.71**, Vodafone P/E **3.99**, both `as_of=2026-10-13`, `business_match=partial`, `listed_years=null`, `pb=null`; neither supplies `ev_ebitda`. [L/peers.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/peers.json) includes two VALID observations, no rejections, no second-multiple values. Issuer financial/share inputs are present. Median P/E is 22.35; issuer P/E uses 1119/32.63; the stored premium **53.43890313809292** and PEG **1.8627215745378736** are consistent with the unchanged bands. P/E zero is a real scored band—not a P/E penalty.

`derived.py:644–661` tries peer median EV/EBITDA + issuer EV/EBITDA, then peer median P/B + issuer P/B. Both peer-side medians are absent here. This is a **confirmed target dependency failure**. Its reason string “no VALID peer multiple… Rejected peers: none supplied” is misleading: VALID P/E peers exist; required second-multiple observations do not. Improve diagnostic precision only under later implementation authority.

`PeerMultipleAdapter.normalize` already carries EV/EBITDA/P/B, while the filing extractor calculates P/B only with usable CMP/NAV and does not emit EV/EBITDA. It supplies partial comparability by convention, not independent eligibility adjudication. Publication-source [extraction/sections.py:3443-3473](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/extraction/sections.py#L3443-L3473) now uses header-aligned rows, `listed_years=None` and actual parsed date: the earlier alleged 15-year/date fallback is **contradicted for this revision and target**. Target metadata agrees with the newer shape, without proving runtime commit. Classifier allows missing listing history and partial match; VALID is not proof of a justified comparable universe.

`recent_sector_ipos` is **absent**, not rejected/stale. The derivation reads any supplied numeric `pe_at_issue`, at most four schema items, and uses their median. It does not enforce four samples, sector identity, chronological sorting, date cutoff or recency window. Names/formula text are not implemented eligibility checks. A justified historical selection must be established upstream; no convenient replacement peers/IPO values are proposed. [derived.py:743-779](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/derived.py#L743-L779); [connectors/adapters.py:431-504](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/connectors/adapters.py#L431-L504).

### Business and assessment trace

All nine business fields are null: CAGR, scope, forecast period, source, moat, regulatory dependence, top-five customer, top-five supplier, visibility. There are **no business extraction evidence items** in the 42-item registry. The metric requires all four industry elements; concentration requires at least one usable percentage (then maximum available); moat/visibility are explicit assessments. Order-book extraction alone is not a visibility rating. Existing business extraction and analyst reconciliation are capabilities, not proof that source evidence was found and discarded. Publication-source [extraction/sections.py:2883-3148](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/extraction/sections.py#L2883-L3148) and [enrichment_engine.py:681-760](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/enrichment_engine.py#L681-L760); unchanged [derived.py:1553-1611](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/derived.py#L1553-L1611).

The first observed gap is the absent normalized value/assessment. Source document coverage, pattern failure, applicability of an industry forecast and missed concentration tables remain **UNPROVEN** without raw page/routing output. The filing scanner's bounded page/pattern approach is a risk, not a demonstrated Jio failure for those fields.

## 6. Four-block market data and A9 diagnosis

### 6.1 Stored shape and source-to-snapshot break

Both [L/input.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/input.json) `/snapshot/input/market` and [P/input.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/input.json) have **`{}`**, with no flat or nested observations. In both market snapshots, `/snapshot/blocks/0..3` are respectively anchor/subscription/gmp/regime, each:

```json
{"as_of": null, "block": "<name>", "reason": "block not supplied", "status": "MISSING", "values": {}}
```

No per-block `source_id` or `age_hours` is present. Snapshot-level `as_of`/`captured_at` are evaluation-time audit/fallback timestamps, **not market observation times**. Source registry has filing, official RHP, BSE/NSE issue-term responses and one aggregator issue-term response, but no linked market-block observation. Do not confuse a source's schema type MARKET_DATA or an IPO-detail page with a populated GMP snapshot.

| Block | Expected canonical shape | Available producer capability | Confirmed target first break | Unproven upstream explanation |
|---|---|---|---|---|
| anchor | `market.anchor.quality`, `as_of`, source; optional amount | `AnchorAllotmentAdapter` → coordinator | No input block, no values/source/time | Whether an eligible allocation/assessment was acquired for this run |
| subscription | `market.subscription.qib_x/retail_x/nii_x/overall_x`, `as_of`, source | `OfficialSubscriptionAdapter` → coordinator | No input block | Whether eligible category observations existed by the applicable cutoff |
| gmp | `market.gmp.pct/trend`, `as_of`, source | `GmpSignalAdapter`, explicit selection, evidence/linkage | No input block; A9 MISSING | Whether attributable eligible observation existed; qualification separately absent |
| regime | `market.regime.nifty_trend`, `as_of`, source; listing gains separately | `MarketRegimeAdapter`; A8-M policy | No input block | Complete qualified NSE series, session/availability rule and integration authority |

Schema `ipo-input.v1.5.schema.json:927–1029` defines optional blocks without universally requiring all subfields. Structurally valid input can therefore lack market content. `pipeline.py:284–299` calls `build_market_snapshot(canonical.market())`. `snapshots.py:423–435` gives exactly the stored MISSING shape for absent/nonmapping/empty blocks. A nonempty block lacking as-of takes STALE instead. Here the absent input-to-snapshot transition is **demonstrated**, not hypothetical.

### 6.2 Actual entry-point evidence and source comparison

Both lifecycle records identify `actor=system_ingest`, reason `statutory_filing_ingest`. Source records show a temporary `ipo_ingest/.../filing.pdf` and resolved exchange/aggregator issue terms. These are strong evidence of the PDF ingest family, not a complete function-call trace or commit attestation.

Publication-source [presentation/service.py:1470-1484](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/presentation/service.py#L1470-L1484) calls `extract_from_pdf(...allow_fixture_fallbacks=False)` without a reference base. Official-term assembly at `1653–1658`, the OFS branch at `1673+`, subsequent aggregator assembly and the final evaluate call `1973–1979` do not pass market/peer/analyst snapshots. No `ConnectorCoordinator` call exists in that handler. Builder copies market only from base. Thus this source's upload route has **no step acquiring/attaching those observations**. The normalized empty market agrees with that omission. Runtime identity remains UNVERIFIED; do not claim an executed connector discarded a fetched value.

Adapters and coordinator exist as supplied-payload normalization capabilities, not automatic live providers. `ConnectorCoordinator.ingest_snapshot/reconcile_snapshots` normalizes/reconciles input snapshots and outputs nested blocks. The **separate** enrichment helper writes flat aliases such as `market.qib_subscription`, `market.anchor_quality`, `market.nifty_trend`; the evaluator consumes `market.subscription.qib_x`, `market.anchor.quality`, `market.regime.nifty_trend`. This mismatch is present in both inspected references. Publication source [enrichment_engine.py:767-833](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/enrichment_engine.py#L767-L833); coordinator `150–224`; derived `1661–1729`.

**Classification: confirmed source mismatch, target causation not demonstrated.** The target has neither flat nor nested data, no market snapshot source and no trace showing execution of this path. Correcting aliases alone would not acquire values or satisfy qualification. Strict canonical additional-properties rules also make flat additions a schema-contract issue, not simply fields silently ignored after a successful compliant input.

Retained publication-side `docs/investigation/jio-recovery/anchor-review.json` contains diagnostic OCR lines of a document labelled October 19 and remains UNVERIFIED. It demonstrates retained candidate evidence outside this evaluation's field registry, not a qualified anchor quality or proof that the target workflow processed it. This new task did not run OCR or make a fresh source request.

### 6.3 Exact A9 branch and legitimate success boundary

[L/evaluation-record.v1.json](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/docs/investigations/jio-ipo-score-33/artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evaluation-record.v1.json) `/result/outcome_resolution` is NONTERMINAL_UNRESOLVED, reason.code MISSING. `/result/diagnostics` contains A9_GMP_FINAL_WITHHELD; `/result/final_outcome` is absent. Same state in previous canonical record.

`evaluation_record.py:1013–1077` first checks FINAL, then searches projected GMP blocks. It classifies missing when the block is absent, status MISSING, or both `pct` and `trend` are null/absent. This target satisfies all relevant missing conditions. For a present observation the function returns SOURCE_UNQUALIFIED. **Neither inspected revision has a qualified-success branch for Final.** For non-Final it returns no A9 veto; that is not an authorized workaround for this Final target.

A9 policy requires a qualifying snapshot and required hash, but the legacy `market.gmp` schema has no accepted qualification-hash field and the gate does not validate a qualifying hash or consume a binding sidecar. Generic market SHA-256, an opaque source content hash or local evidence-byte linkage is not qualification. The Arena source has newer A28 representation/pin-checking mechanics; they return no authority/admission signal and do not add a successful Final branch.

A legitimate completion requires (1) attributable issuer/issue-matched selected GMP observation, its original publisher label/value, timestamp semantics/offset, availability and full relevant capture by cutoff, freshness, dispute/revision/withdrawal handling, source/independence review; (2) an actual scoped qualification/adjudication and hash subject/representation supported by that contract; and (3) separately authorized integration of an accepting verifier. No generic digest substitution, publisher-name allowlist alone, inferred trend, or invented positive observation closes it. Other safety/outcome gates still apply. Relevant policy: `handoff/decisions/A9-missing-gmp-final-fail-closed.md`, A17/A18; newer Arena `docs/gmp/A9-evidence-intake.md` remains an intake checklist, not admission authority.

A8-M separately requires completed-session NSE NIFTY 50 **price index** closes and complete SMA windows, known availability/session freshness and approved producer. Missing is not weak or neutral. That policy does not qualify GMP, subscription or SEBI/ED absence.

### 6.4 Score/API versus canonical outcome

Stored score verdict: INSUFFICIENT_DATA, uncertain=true, band_score=AVOID. Canonical critical_safety: INCOMPLETE, missing exactly going_concern_uncertainty and sebi_ed_action_active. A9 precedes this safety outcome at `evaluation_record.py:1455–1480` and withholds terminal Final.

Both API detail captures return score 33, interval 23–76, missing list and legacy verdict, but **no canonical `outcome_resolution`/`final_outcome` field**. Source detail projection reads stored score/legacy verdict (`presentation/service.py:~519–575`), while frontend formats final_score; it need not read the canonical record. Thus display of 33 or `mode=final`, ACTIVE lifecycle, COMPLETED processing and PASSED validation **does not mean a terminal Final decision**.

### 6.5 Additional authority fact—not GMP evidence

`input.json /snapshot/input/issue/fresh_issue=302130.0` in INR_MILLIONS came from Chittorgarh's quoted **₹30,213 Cr**, not an official cash-total disclosure. Registry `EV-issue.fresh_issue` explicitly says THIRD_PARTY_AGGREGATOR_OVERRIDE, policy `pa-aggregator-issue-terms-v1`, UNVERIFIED/NOT official, with row locator and source hash. Both API captures retain the authority warning. The publication's `handoff/decisions/2026-10-22-pa-aggregator-issue-terms.md` authorizes an opt-in issue-term fallback, superseding earlier official-only choice **for that mode**; it does not qualify market GMP or authorize derived cash. Recorded authority is not independently verified publisher truth. No policy/runtime switch was changed in this investigation.

## 7. Provenance and governance diagnosis: hypotheses reconciled

### 7.1 Demonstrated record linkage facts

L/evidence.json `/evidence/evidence` contains **42** evidence items and `/evidence/sources` contains **5** sources. Canonical `field_values` has **102** scalar rows. Only **7** rows contain external EV references: company name and six dotted-ID issue terms (close date, fresh issue, lot, open date, high/low prices). Other rows retain local A15 input-snapshot references; those prove the stored value, not original source support.

Concrete example: registry `EV-governance-auditor_opinion` quotes the auditor's page-324 sentence “do not require any adjustment for modification as there is no modification in the underlying audit reports”. Input opinion is unqualified, and K1 consumes it as false for adverse opinion. Yet canonical `/input/governance/auditor_opinion` lacks that EV reference. `_input_field_rows` looks for `EV-governance.auditor_opinion`. The hyphenated extraction ID and dotted fallback do not match. Same defect affects other extracted scalar fields.

`RawExtraction.to_evidence_dict` creates hyphenated IDs; builder indexes them by exact `field_path`; `canonical_input.build_registry` has a working in-memory path map. `to_snapshot_dict` strips private metadata. Evaluation persists registry content but not the complete original map. A15 explicitly emits LEGACY_FIELD_EVIDENCE_MAPPING_INCOMPLETE and reconstructs only `EV-<dotted path>`. Source: interfaces `73–98`, builder `_build_evidence`, `canonical_input.py:231–283,355–361`, `evaluation.py:154–167`, [evaluation_record.py:782-812](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/evaluation_record.py#L782-L812) and `1350–1373`.

### 7.2 The 82-leaf warning: exact boundary and reconstructable paths

L/evaluation.json `/validation/warnings[code=PROVENANCE_MISSING_FOR_FIELDS]` preserves count **82** and **20 examples**, starting `issue.post_issue_shares`, `issue.post_issue_eps`, then financial-period fields. Canonical validation retains the warning message but does not preserve its entire detail object. This warning is generated **before** persistence and A15 reconstruction: the A15 ID mismatch does **not cause the original 82 count**.

The validator walks scalar leaves, including nulls and metadata, filters material prefixes and demands exact evidence-index membership. It does not inherit `financials.periods`, `peers` or `use_of_proceeds` container evidence into every child. In this target: financial periods have registry summary evidence; peer list and proceeds list likewise have container records. RPT transaction evidence exists but scalar RPT metrics have no direct field reference. A registry can therefore be nonempty while leaf provenance is incomplete.

Using the retained scalar input paths and **both** stored ID conventions reconstructs **96 material leaf paths: 14 directly linked, 82 without a direct corresponding scalar EV ID**. This exactly matches the warning count and all 20 stored examples. Appendix B enumerates the reconstructed 82. It is a transparent reconstruction, **not recovery of the discarded original field map**. Null leaves are counted; this is not evidence of 82 unsupported non-null financial quantities.

Of the original 14 directly linked material leaves, only the six dotted issue-term IDs are externally linked by A15; the eight hyphenated scalar IDs are missed. Company name is the seventh linked row but is outside the validator's material prefixes. Source names and page summaries do not automatically establish leaf-specific quotations or dependency evidence.

### 7.3 Hypothesis disposition

| Earlier finding | Artifact/source reconciliation | Classification |
|---|---|---|
| 82-leaf warning | Count and examples directly present; reconstructed path deficit reproduces 82 | **Confirmed, target-relevant** |
| Field map lost during persistence | No original map in input snapshot; registry retained; canonical warning explicitly documents limitation | **Confirmed, target-relevant** |
| Extracted ID versus fallback mismatch | Actual hyphenated auditor EV exists; exact canonical row lacks it; code checks dotted ID | **Confirmed, target-relevant** |
| Old builder defaults SEBI/ED false | Arena reference has old default; publication builder instead defaults null and extractor is evidence-driven; target null agrees | **Contradicted for publication source; not demonstrated as target cause** |
| Unquantified-contingency mapping absent | Publication builder reads raw extraction and base flag; extractor can emit positive true; target has null and no EV for flag | **Contradicted for publication source**; absence versus non-match still unproven |
| Penalty flags discarded | Publication builder carries optional adjusted-metric and auditor/CFO flags when supplied; target omits both and registry has neither | **Old defect exists in Arena reference, target impact unproven; do not prescribe duplicate fix** |
| Peer age fabricated as 15 | Target listed_years null; publication emitter uses null and parsed date | **Contradicted for target/publication source** |
| Market alias mismatch | Static contract mismatch exists; target market empty, no supplied alias values or connector trace | **Confirmed but causal target impact unproven** |
| Litigation classified merely because missing | Actual category adverse with page-464 criminal-complaint quotation | **Contradicted**; entity scope still merits review |
| All missing fields are failed extraction | Several are intentionally governed assessments or positive-only safety flags | **Not demonstrated** |

### 7.4 Governance producing paths and missing evidence

**Auditor:** opinion is unqualified and evidenced. `auditor_changed_3y`, reputation and repeated EOM are null. The derived bucket stops specifically at missing three-year-change evidence (`derived.py:1462–1469`). Publication extractor `2554–2669` first needs a recognized auditor name; tenure needs a positive same-auditor-three-FY statement. A22 records a historical Jio name non-match and forbids unconditional false/cross-year inference. This explains a plausible earlier extraction limit, not a newly verified whole-document absence. Obtain actual report/tenure text before proposing a pattern correction.

**Going concern:** input null and no EV item. Publication extractor `2675–2701` only emits true for positive, non-negated uncertainty language. A19 explicitly keeps absent paragraphs, unmodified opinions and even negated uncertainty language UNKNOWN; negative-confirmation rule is deferred. This is a **governed asymmetry**, not permission to fill false. Registry's unqualified-opinion quote does not establish the missing flag.

**SEBI/ED:** input null and no corresponding EV. Publication builder `335–366` defaults null, extractor `2766–2800` emits only supported regulator/party/time findings. A23/A25 distinguish issuer denials, active action, party/time scope, incomplete searches and regulator-source coverage. An RJIL criminal complaint by local panchayat secretaries is not a SEBI/ED action. No external regulator search evidence exists in this target. The previous apparent old-source contradiction is resolved by publication-source divergence, although exact deployed commit is still unknown.

**Contingencies:** quantified amount **15021.0 INR million**, net worth **3359769.0 INR million**, ratio **0.4470843084747791%**. Registry page405 identifies the claims/disputed-liabilities note. Unquantified flag is null, with no flag EV. Publication financial extractor `617–776` supports a defined contingent section total excluding commitments and emits true only on positive unquantified language; builder `257–271` maps it. A20 governs this asymmetry. Numeric ratio is not a proof that all material exposures are quantified; no false flag may be inferred.

**Promoter holding:** both pre and post null; no corresponding EV. This also prevents the existing enrichment dilution derivation from running. A21 requires a disclosed post-issue promoter/category percentage, not dilution of pre-issue holding, and distinguishes public from promoter-group category B. The candidate source still contains a legacy enrichment derivation, but it did not run successfully here and must not be used as an unauthorized remedy. Original table/placeholder and routing are needed to separate genuine nondisclosure from missed extraction.

**RPT/board:** RPT 4.3094 scores3; growth-share delta −0.1141 clears K6. Twenty-three transaction EVs on page376 exist, but transaction list is not present in frozen input and the two derived scalar RPT fields lack source links. Builder `_derive_rpt_metrics` computes them from selected revenue transactions; audit numerator/category/year selection from retained transactions rather than treating generic RPT totals as revenue. Board independence false has an extraction EV; exits0 lacks leaf evidence. Their known inputs produce `other` (1 point), not missing data. Defaults/source completeness remain audit concerns, not demonstrated causes of UNKNOWN.

## 8. Proceeds extraction diagnosis

**Confirmed target:** L/input.json `/snapshot/input/use_of_proceeds` contains exactly one record: `{"category":"gcp","amount":null,"undisclosed_marker":"[●]"}`. No debt, capex, R&D or acquisition records are present. `issue.fresh_issue=302130.0` is present, so the immediate blocker is specifically **GCP**, not unknown fresh cash and not an observed unidentified-acquisition amount.

Registry `EV-use_of_proceeds` refers to page120, locator Schedule of Implementation and Deployment, with **PROCESSING_SUMMARY** “Use of proceeds categories: ['gcp']”; it does not retain the actual source amount/placeholder sentence. Semantic GCP_UNDISCLOSED and the bucket reason are consequences of this normalized state, not independent original-document verification.

Publication-source [extraction/sections.py:982-1061](https://github.com/ramkivs/ipo-screening-engine/blob/ebb8a6c6b0d12e54228ec6b523bda025e927fb0b/engine/ipo_screening/extraction/sections.py#L982-L1061) scans at most the first six pages in its routed objects window, recognizes working capital/debt/capex/GCP, and returns null+marker on a recognized placeholder. Builder forwards the schedule. Additional schema categories such as R&D and identified/unidentified acquisitions have no corresponding emitting branch here. The chosen category detector scans a limited number of nearby lines/numbers; raw page text/routing are needed to determine exact match. This is a demonstrated coverage limitation, **not yet proof that it missed a disclosed target amount**.

`derived.py:1203–1252` marks a category unknown when an entry has no numeric amount. Its ordered blind-heavy test cannot skip unknown GCP to later debt/growth tests. It correctly returns the exact stored UNKNOWN diagnostic; the legal ceiling is not the allocation. The same code treats **absent categories as zero** on an exhaustive-schedule assumption. An incomplete extraction can violate that assumption; here GCP already blocks scoring, so that risk is not what produced the stored reason.

Additional retained research `docs/investigation/jio-recovery/rhp-all-pages-inventory.json` pins the same filing SHA and includes a page116 Objects of the Issue excerpt: fresh cash is `[●]` and the text starts the debt-prepayment object. This is evidence of related objects outside the one-item normalized schedule; its truncated context does not establish numerical debt/GCP allocations or prove routing offsets. Do not conflate printed page numbers, physical page indices and the extractor's page120 locator without the route map.

**Disposition:** null/placeholder classification is confirmed in normalized input. Genuine GCP source nondisclosure is **plausible and explicitly recorded, but not independently established by the retained source quotation**. Failure to capture other objects is likewise not fully adjudicated. Minimum settling evidence: original matched Objects pages and table, physical/printed-page mapping, raw extraction candidates and actual routing window; then a historically eligible later allocation disclosure if one exists. Do not replace null with zero, 25% ceiling, residual proceeds, or shares × cap-price cash.

## 9. K1, K2 and K5: exact leaf reconciliation

Authoritative observations: L/result.json `/knockouts/results`; config K1/K2/K5 expressions at `1194–1253,1314–1344`; unchanged Kleene evaluation `knockouts.py:151+,252–277`.

| Rule | False/non-triggering known leaves | UNKNOWN leaf | Stored rule | Resolution requirement |
|---|---|---|---|---|
| K1 | `auditor_opinion=unqualified` not in qualified/adverse/disclaimer; `net_worth_latest=335976.9` not negative | `going_concern_uncertainty` | UNVERIFIED | Positive uncertainty evidence triggers; clearing needs evidence and an authorized negative-confirmation contract, not silence/unqualified opinion |
| K2 | `promoter_pledge_pct=0` not >25 | `sebi_ed_action_active` | UNVERIFIED | Specific current agency/party evidence under regulator coverage contract; no nil-subset/failed-search shortcut |
| K5 | `contingent_liab_pct_networth=0.4470843084747791` not >50 | `contingent_liab_unquantified` | UNVERIFIED | Resolve material unquantified exposure under A20; ratio alone cannot clear |

No knockout is triggered; K3/K4/K6 are CLEAR, overall knockout status UNVERIFIED, completeness50%. K4 can be CLEAR despite unknown promoter holding because other AND conditions are definitively false; unknown leaves are not universally cleared. Critical-data completeness is60%, missing exactly going concern and SEBI/ED. The unquantified flag affects K5 but is not itself the critical-list ratio item. A9 currently preempts canonical terminal outcome regardless; removing one missing condition would not establish a safe Final by itself.

## 10. Latest versus previous: field-level comparison

| Field / artifact | Previous | Latest | Interpretation |
|---|---|---|---|
| evaluation/manifest `evaluation_timestamp` | `2026-10-22T10:19:13Z` | `2026-10-23T05:18:16Z` | Changed |
| evaluation/manifest `input_snapshot_hash` | `95cbd54abf578169267bd8e46c396d23aa85204dd82a6247ce5cd8d490f4508f` | `95cbd54abf578169267bd8e46c396d23aa85204dd82a6247ce5cd8d490f4508f` | Unchanged |
| evaluation/manifest `peer_snapshot_hash` | `61f5c9132e97baf987f2693568ab5b4b5ec748136b05453f0e2d155b842edb9b` | `61f5c9132e97baf987f2693568ab5b4b5ec748136b05453f0e2d155b842edb9b` | Unchanged |
| evaluation/manifest `market_snapshot_hash` | `63760030294cfaa3886a881eff806d728f83faa4b88601b0b2857661d1c08d71` | `0c3f7c86c49482d4162256332407e20c26d5c583037f6e4bd22bc35d51594897` | Changed |
| evaluation/manifest `source_manifest_hash` | `5b0346140af4088ad3890502a1e347d3f77cb6c8308639ad036252df8239f508` | `da76543515f40f69c4f6effad3166a99a0fc63b8bb926c84e1b57e55c15d7202` | Changed |
| evaluation/manifest `result_hash` | `ad5e6872e816bd3614bb915765bc36d2b1237786829d543975925aceda880dcc` | `b79b57944add9193cf661ceb550832d17425fb1859eeb83887e36d3445a6df04` | Changed |
| Content comparison | Verified outcome |
|---|---|
| input.json | Exactly one parsed difference: evaluation_id; complete snapshot identical |
| result.json | Exactly two parsed differences: evaluation_id and result_hash; every criterion value/state/award/reason, derived metric, plan, penalty, missing row, range and verdict identical |
| market.json | Five parsed differences: evaluation ID, top-level market hash, snapshot content hash, snapshot as_of and captured_at. Four block objects identical |
| peers.json | Four parsed differences: evaluation ID, captured_at, two age_days. Both VALID; peer material hash unchanged |
| canonical record | 39 positional leaf differences, in identity, timestamps, source/locator/digest metadata; `/result` and `/field_values` identical |
| evidence.json | 22 parsed leaf differences including evaluation ID, source manifest hash, retrieval times, changed BSE/NSE response IDs/hashes, aggregator response hash and BSE row locators; no new field observations |
| lifecycle | Previous now SUPERSEDED by latest; latest ACTIVE and supersedes previous. Both VISIBLE. Transition `2026-10-23T05:18:17Z`, actor system_ingest, statutory_filing_ingest |
| API details | Both score33/Low/57%/INSUFFICIENT_DATA, four MISSING blocks, same aggregator warning; no canonical outcome field. Previous superseded status agrees with lifecycle |
| API evidence | 42 evidence entries each; changed source retrieval/locator metadata agrees with persisted registry; GET captures are not original store files |

Market hash explanation is **verified, not guessed**. `snapshots.py:480–486` assigns snapshot-level as_of from evaluation time when block as-of values are absent. `hash_payload:388–403` includes that fallback as_of (but excludes captured_at and ages). Actual previous as_of is `2026-10-22T10:19:13Z`; latest is `2026-10-23T05:18:16Z`. Independently canonical-hashing those exact payloads reproduces both stored market hashes. Therefore a new empty-snapshot hash does not demonstrate a market fetch. Peer ages/capture time are excluded from peer hash, correctly preserving it.

BSE locator changed `Table[2]` → `Table[0]`; its source ID/hash changed BA18F07E → 2079D39A. NSE source BCC14D8C → 755E240F; aggregator response content hash changed while assertion/quote stayed the same. Source-manifest and result hashes therefore legitimately differ despite identical scoring inputs. An exact original-call explanation requires activity logs; no cache/fetch hypothesis is inferred from these differences.

Both canonical records have `/evaluation/evaluation_cutoff.state=UNKNOWN` with reason UNAVAILABLE: no single global cutoff was stored. Their evaluated_at timestamps are known. Do not relabel retrieval/evaluation timestamps as an established global policy cutoff. GMP code uses evaluation time for its specific eligibility cutoff; that does not populate the legacy record's missing global field.

## 11. Ranked root causes, confidence and hypothesis limits

| Rank | Finding | Evidence and confidence | Causal classification |
|---|---|---|---|
| 1 | Missing market population at consumed-input boundary; all four blocks absent | Identical input.market={}, snapshot blocks, criterion reasons and API; **HIGH** | Confirmed actual break. Upload integration omission exists in candidate source; exact Windows commit/call path not authenticated |
| 2 | A9 withholds Final for no GMP observation; no accepting Final branch in inspected code | Canonical reason MISSING and source branch logic; **HIGH** | Confirmed outcome blocker plus governed qualification/integration dependency |
| 3 | Known criteria genuinely earn only33/57 | Complete result criteria, P/E53.4389%/litigation adverse/financial bands; **HIGH** | Not a missing-data defect; resolving unknowns is not guaranteed to improve score |
| 4 | Positive-evidence safety contracts leave K1/K2/K5 unverified | Exact nulls/leaves; A19/A20/A23/A25; **HIGH** for record, **MEDIUM** for historical producing policy binding | Governance/evidence coverage requirement, not automatic false-fill correction |
| 5 | Second multiple has no usable peer-side EV/EBITDA or P/B; sector IPO array absent | Input and peer snapshots, derived reasons; **HIGH** | Data not supplied; document/provider acquisition failure versus genuine unavailability unsettled |
| 6 | Industry/concentration values and qualitative assessments absent | Nine business nulls, no business EVs, assessment path separate; **HIGH** | Source coverage/assessment acquisition unresolved, not demonstrated data discarding |
| 7 | Proceeds GCP unknown blocks first ordered test | One null-marker entry and exact bucket reason; **HIGH** for normalized gap, **LOW/MEDIUM** for genuine document nondisclosure | Requires original page/routing reconciliation; cannot declare a parser defect or source absence from summary alone |
| 8 | Provenance cannot trace many leaf facts despite registry evidence | 82 warning, containers, lost map, 7 external-linked canonical rows, actual ID mismatch; **HIGH** | Confirmed auditability defect; not proven cause of33 because provenance check warns rather than withholding criterion points |
| 9 | Flat/nested market helper mismatch | Source at both references; **HIGH** static, **UNPROVEN** historical target effect | Do not identify as the sole cause of empty market without supplied payload/execution trace |
| 10 | Transport-byte integrity differs for10 exported files | Literal hashes fail; original representations reproducible by line endings; **HIGH** | Evidence-publication fidelity issue, not demonstrated semantic scoring corruption |

Litigation source supports that criminal proceedings are discussed, rather than no disclosure: quote names **RJIL**, summons and complaints by panchayat secretaries on page464. Whether the configured entity population appropriately includes that subsidiary/group exposure and whether all proceeding/status context is represented remains unresolved. The stored note says parties named “not stated” despite RJIL appearing, which is a metadata/party-recognition limitation to review. Do not reclassify to clean or call it a SEBI/ED action. A24 clean-coverage policy and A26 tax-only review do not authorize automatically changing this non-tax criminal classification; A27 CARO/disputed-tax auditor changes remain PROPOSED/UNRESOLVED.

## 12. Exact remaining technical evidence needed

1. **Runtime identity:** Windows `git HEAD`, branch/dirty status, hashes of loaded extractor/builder/service/enrichment/canonical projection files and package resolution at the two evaluation times; ingestion activity IDs/logs tying uploaded PDF hash to the normalized inputs. Current HEAD alone cannot retrospectively attest a prior process.
2. **Original pre-canonical extraction output:** raw candidates, values, field paths, pages, quotes, page routing, page-read errors and original `_evidence` map. This settles extraction omission versus mapping/override. The frozen input deliberately excludes that private map.
3. **Objects/shareholding/auditor/business source excerpts:** hash-bound full relevant pages, actual numeric/placeholder tables and printed/physical mapping; no need to rerun scoring. Existing records locate auditor324, peers126, contingencies405, litigation464, proceeds120, financials330 and RPT376. Full subsidiary/legal scope and complete contingent section are necessary before strong coverage claims.
4. **Market acquisition/selection record:** actual provider payloads or explicit evidence that no population path executed; anchor allocation/assessment, category subscription observation, selected GMP source observation/qualification and NIFTY session-series evidence. Historical availability must be demonstrated, not backfilled from today's data.
5. **Missing scalar assessments/flags:** actual analyst industry/moat/visibility rationale; tenure evidence; auditor/CFO exit, adjusted-metric reconciliation, regulatory dependence and EOM materiality evidence. No corresponding EV should be fabricated to silence the warning.
6. **Original recovery ZIP/Windows byte receipts:** required only to independently authenticate original transport bytes for the ten newline-transformed files. Existing normalized JSON and all14 internal digests already support semantic artifact reconciliation; do not edit the published manifest.
7. **Qualification/authority records:** actual GMP accepting contract and scoped source decision; approved safety negative-confirmation coverage where currently deferred; any entity-scope decision needed for subsidiary litigation. Policy documents are not evidence that an authority action happened in this particular runtime.

No additional evaluation is required to resolve the current record's arithmetic or list entries. These requests concern source/trace/authority evidence missing from the bundle, not repetition of target discovery.

## 13. Recommended execution sequence and authority

1. **Evidence reconciliation first (read-only):** attach exact runtime/ingestion identity and original extraction/field map; inspect existing relevant source pages. Preserve both evaluations. Observable result: each null has a documented source/path classification, including a resolution or explicit unavailable reason.
2. **Safety/governance adjudication:** resolve K1/K2/K5 coverage and litigation entity scope under existing approved policies; identify genuinely deferred decisions. Observable result: supported safety states or retained UNKNOWN, never clearance by convenience. Policy changes require separate explicit approval.
3. **Provenance data-path correction proposal:** preserve field associations and leaf/dependency evidence; fix ID reconstruction only after tests are authorized. Observable result: existing supported values link to original sources, snapshots remain distinguishable, no invented provenance. Do not rewrite old evaluation artifacts.
4. **Data acquisition and assessments:** gather eligible second multiples, recent-sector IPO evidence, source-backed industry/concentration data and attributed moat/visibility assessments. Classify genuinely unavailable evidence without a development task. Observable result: an evidence package, not promised points.
5. **Market integration proposal:** specify one canonical nested block contract across providers/coordinator/enrichment/upload; qualify each source/event/cutoff. Fix flat/nested mismatch and add population only under new implementation authority. Do not execute it against Windows now.
6. **A9 accepting-path governance then implementation:** scoped GMP qualification, explicit selection/dispute handling and accepted hash subject must precede an authorized positive admission verifier. Keep veto until all conditions and other gates are met; generic hash or mode change is not a remedy.
7. **Only if later authorized:** focused tests and a new immutable evaluation with a traceable new input/evidence set; compare with both historical records. No rule/weight changes are proposed merely to increase33. User/runtime acceptance and deployment need their own authority.

### Integrity attestation and publication scope

No application/test/config/fixture/evidence/evaluation changes, runtime/environment changes, ingestion/extraction/discovery/scoring/evaluation, test runs, Windows access, server operations or deployment occurred. Read-only GitHub GETs downloaded unchanged reference copies outside the repository. Independent JSON/digest/data comparison was performed. The only repository content addition is this report. Report-only commit/push is explicitly authorized by this mission; it must not be described as “no commits performed.” Existing Arena branch name is preserved; no checkout of the evidence branch or source merge is authorized or performed.

**Next concrete action:** obtain the original ingestion/extraction trace and runtime source fingerprint for the latest evaluation, then inspect the hash-matched Objects and governance pages. That will distinguish real nondisclosure and governed UNKNOWN from source-recognition/integration defects before any fix or new evaluation.

## Appendix A — Exact missing/unverified diagnostic text

Source: latest result.json `/missing_unverified`; identifiers/order are unchanged.

1. **CRITERION `second_multiple` — UNKNOWN**, `points_affected=4.0`. no VALID peer multiple is available; valuation cannot be scored as current. Rejected peers: none supplied

2. **CRITERION `sector_ipo_relative` — UNKNOWN**, `points_affected=4.0`. no recent same-sector IPO valuations were supplied, so the relative test cannot be evaluated

3. **CRITERION `use_of_proceeds` — UNKNOWN**, `points_affected=4.0`. the blind_heavy test ((GCP + unidentified acquisition)/fresh > 20%) cannot be evaluated because a GCP or unidentified-acquisition amount is undisclosed. The legal maximum is not substituted, and an undisclosed amount is not read as zero, because either would let a blind-heavy offer pass the test

4. **CRITERION `promoter_post_holding` — UNKNOWN**, `points_affected=4.0`. post-issue promoter holding is not disclosed

5. **CRITERION `auditor` — UNKNOWN**, `points_affected=2.0`. it is not established whether the auditor changed within the last three years

6. **CRITERION `industry_growth` — UNKNOWN**, `points_affected=5.0`. the forward industry CAGR is not disclosed

7. **CRITERION `moat` — UNKNOWN**, `points_affected=5.0`. the market-position and moat assessment is not recorded

8. **CRITERION `concentration` — UNKNOWN**, `points_affected=3.0`. neither top-5 customer nor top-5 supplier concentration is disclosed

9. **CRITERION `visibility` — UNKNOWN**, `points_affected=2.0`. the capacity and order-book visibility assessment is not recorded

10. **CRITERION `anchor_quality` — UNKNOWN**, `points_affected=3.0`. anchor market data is not usable: block not supplied

11. **CRITERION `qib_subscription` — UNKNOWN**, `points_affected=3.0`. subscription market data is not usable: block not supplied

12. **CRITERION `gmp_trend` — UNKNOWN**, `points_affected=2.0`. gmp market data is not usable: block not supplied

13. **CRITERION `market_regime` — UNKNOWN**, `points_affected=2.0`. regime market data is not usable: block not supplied

14. **CRITERION `retail_nii_penalty` — UNKNOWN**, `points_affected=0.0`. the penalty trigger could not be evaluated from the supplied inputs

15. **KNOCKOUT `K1` — UNVERIFIED**, `points_affected=0`. The supplied input does not establish whether going_concern_uncertainty applies: the supplied input does not establish whether going-concern uncertainty exists.

16. **KNOCKOUT `K2` — UNVERIFIED**, `points_affected=0`. The supplied input does not establish whether sebi_ed_action_active applies: the supplied input does not establish whether an active SEBI/ED action exists.

17. **KNOCKOUT `K5` — UNVERIFIED**, `points_affected=0`. The supplied input does not establish whether contingent_liab_unquantified applies: the supplied input does not establish whether any material contingent liability is unquantified.

18. **MARKET `anchor` — MISSING**, `points_affected=null`. block not supplied

19. **MARKET `subscription` — MISSING**, `points_affected=null`. block not supplied

20. **MARKET `gmp` — MISSING**, `points_affected=null`. block not supplied

21. **MARKET `regime` — MISSING**, `points_affected=null`. block not supplied

22. **PENALTY `auditor_cfo_exit` — UNKNOWN**, `points_affected=null`. the trigger could not be evaluated; the penalty is neither applied nor ignored, and is carried in the lower bound

23. **PENALTY `unreconciled_metrics` — UNKNOWN**, `points_affected=null`. the trigger could not be evaluated; the penalty is neither applied nor ignored, and is carried in the lower bound

24. **PENALTY `regulatory_dependence` — UNKNOWN**, `points_affected=null`. the trigger could not be evaluated; the penalty is neither applied nor ignored, and is carried in the lower bound

25. **PENALTY `eom_caro` — UNKNOWN**, `points_affected=null`. materiality metric eom_materiality is UNKNOWN; the penalty is neither applied nor ignored, and is carried in the lower bound

26. **CRITICAL_DATA `going_concern_uncertainty` — UNKNOWN**, `points_affected=null`. critical input required for a safe verdict is UNKNOWN

27. **CRITICAL_DATA `sebi_ed_action_active` — UNKNOWN**, `points_affected=null`. critical input required for a safe verdict is UNKNOWN

## Appendix B — Reconstructed 82 missing scalar provenance paths

These paths reproduce the diagnostic count and all20 persisted examples using both literal dotted and extraction-generated ID conventions. The original discarded field map is not available; this is not an assertion that every path lacks source evidence. Financial periods, peers and proceeds have container evidence; RPT has transaction evidence.

```text
business.industry_cagr_pct
business.industry_forecast_period
business.industry_scope
business.industry_source
business.moat_rating
business.regulatory_dependence
business.top5_customer_pct
business.top5_supplier_pct
business.visibility_rating
capital_structure.discounted_allotments_18m_before_drhp
capital_structure.large_holders_unlocked_early
capital_structure.promoter_lockin_in_place
capital_structure.promoter_pledge_pct
capital_structure.promoter_post_pct
capital_structure.promoter_pre_pct
financials.contingent_liabilities_unquantified
financials.periods[0].cash_and_equivalents
financials.periods[0].cfo
financials.periods[0].disclosed_roce_pct
financials.periods[0].ebit
financials.periods[0].ebitda
financials.periods[0].fy
financials.periods[0].interest_expense
financials.periods[0].net_worth
financials.periods[0].pat
financials.periods[0].receivable_days
financials.periods[0].revenue
financials.periods[0].total_debt
financials.periods[1].cash_and_equivalents
financials.periods[1].cfo
financials.periods[1].disclosed_roce_pct
financials.periods[1].ebit
financials.periods[1].ebitda
financials.periods[1].fy
financials.periods[1].interest_expense
financials.periods[1].net_worth
financials.periods[1].pat
financials.periods[1].receivable_days
financials.periods[1].revenue
financials.periods[1].total_debt
financials.periods[2].cash_and_equivalents
financials.periods[2].cfo
financials.periods[2].disclosed_roce_pct
financials.periods[2].ebit
financials.periods[2].ebitda
financials.periods[2].fy
financials.periods[2].interest_expense
financials.periods[2].net_worth
financials.periods[2].pat
financials.periods[2].receivable_days
financials.periods[2].revenue
financials.periods[2].total_debt
governance.auditor_changed_3y
governance.auditor_reputed
governance.eom_materiality
governance.going_concern_uncertainty
governance.kmp_exits_2y
governance.repeated_eom
governance.rpt_pct_of_revenue_growth
governance.rpt_pct_revenue
governance.sebi_ed_action_active
issue.post_issue_eps
issue.post_issue_shares
peers[0].as_of
peers[0].business_match
peers[0].listed_years
peers[0].name
peers[0].pb
peers[0].pe
peers[0].roe_pct
peers[0].source_id
peers[1].as_of
peers[1].business_match
peers[1].listed_years
peers[1].name
peers[1].pb
peers[1].pe
peers[1].roe_pct
peers[1].source_id
use_of_proceeds[0].amount
use_of_proceeds[0].category
use_of_proceeds[0].undisclosed_marker
```

## Appendix C — Literal export checksum results

All references below are relative to the published evidence directory. The publication additions README.md and SHA256SUMS.txt are not in the26 recovered-file declarations.

| File | Literal SHA-256 matches | Explanation if different |
|---|---|---|
| `README.txt` | NO | Existing BOM/LF retained; final LF→CRLF reproduces declared digest |
| `api-get-responses/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/detail.json` | NO | LF→CRLF reproduces declared digest |
| `api-get-responses/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/evidence.json` | NO | LF→CRLF reproduces declared digest |
| `api-get-responses/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/detail.json` | NO | LF→CRLF reproduces declared digest |
| `api-get-responses/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evidence.json` | NO | LF→CRLF reproduces declared digest |
| `api-inventory.json` | NO | LF→CRLF reproduces declared digest |
| `artifact-inventory.json` | NO | LF→CRLF reproduces declared digest |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/evaluation-record.v1.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/evaluation.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/evidence.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/input.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/lifecycle.json` | NO | LF→CRLF reproduces declared digest |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/manifest.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/market.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/peers.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872/result.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evaluation-record.v1.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evaluation.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/evidence.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/input.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/lifecycle.json` | NO | LF→CRLF reproduces declared digest |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/manifest.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/market.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/peers.json` | YES | — |
| `artifacts/JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794/result.json` | YES | — |
| `recovery-summary.json` | NO | LF→CRLF reproduces declared digest |
