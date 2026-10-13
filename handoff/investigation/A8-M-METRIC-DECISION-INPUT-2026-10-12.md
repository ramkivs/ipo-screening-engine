# A8-M — Metric Decision Input

- **Artifact type:** Investigation and decision-input document; not a decision record or approval.
- **Status:** A8-M source/event/cutoff contracts remain **OPEN / UNRESOLVED**. This artifact does not close them.
- **Prepared:** 2026-10-12 (Asia/Calcutta).
- **Repository:** `ramkivs/ipo-screening-engine`.
- **Accessible checkout:** branch `arena/4e1080b7-ipo-screening-engine`, `HEAD=01ba66c12ca1195fd7acbd287c3e39a019808094`.
- **Governing ref consulted:** `arena/4e1080b7-ipo-screening-engine` at `9085bb6be74a2aa66fa9aaf91ddce557b7ba473c`.
- **Support ref consulted:** `arena/01a10b42-ipo-screening-engine` at `874776f8f283639999dfb4457fbb5119fc7fdc5c`.
- **Authority:** No policy decision, provider qualification, implementation authority, or approval is made or requested here.

## 1. Purpose, scope, and status vocabulary

This document organizes decision inputs for:

1. `market.anchor.quality`
2. `market.anchor.amount`
3. `market.regime.nifty_trend`
4. `market.regime.last_ipo_listing_gains_pct`

It reuses the completed repository-level A8-M investigation rather than repeating it. The latest governing A8 record is `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` (blob `9a96f29befdb3f059e9fce917e41cc86d58ce520` at governing commit `9085bb6…`), especially §§A8-M and common timestamp safeguards.

Status labels in this artifact mean:

- **VERIFIED** — directly established by a governing record or inspected retained artifact.
- **PROPOSED — NOT APPROVED** — an option for later review; not policy, source qualification, or implementation authorization.
- **UNRESOLVED** — evidence or an authorized decision is still required.
- **EVIDENCE REQUIRED** — the specified source record or field definition is not available in the inspected evidence.
- **BLOCKED** — a dependent decision or use must not proceed under current governance.

## 2. Governing direction and project gates

**VERIFIED — approved A8-M direction:** use an official close for metrics established as defined on an actual market session. A separately approved point-in-time rule may be used only for a metric that genuinely requires it. Specify the source, session or observation rule, and cutoff **per metric**; do not silently use a shared timestamp or cutoff.

**UNRESOLVED:** approved source, session-versus-PIT classification, per-metric observation identity/cutoff, and behavior for unavailable observations or non-trading periods. The approved hybrid direction is preserved and not reopened here.

**Current governance boundary:** A8 remains open; Phase 0 remains **OPEN**; Phase 1 remains **UNAUTHORIZED**; implementation authority remains **NOT GRANTED**. No provider is selected or qualified here.

## 3. Source-access and evidence boundary

The prior A8-M packet established that the support-branch fixtures and generic adapters are not official source evidence. This task’s proposed NSE routes are recorded below as **user-provided, uninspected leads**:

- `https://www.nseindia.com/market-data/issue-information?symbol=NSE`
- `https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives`
- `https://www.nseindia.com/all-reports`

The prior A8-M investigation could not reach the official NSE hosts through this environment’s permitted network access. The URLs have not been fetched for this artifact. No Anchor Allocation Report, pre-/post-anchor Security Parameters report, index record, or security-wise price/volume record was inspected or retained. A page link, report title, fixture label, or schema field is not evidence of its source contents or semantics.

**Windows/PowerShell evidence:** none was supplied to or inspected in the accessible workspace. No claim is made about local Windows files.

### Reused repository evidence (not reacquired)

The prior A8-M investigation consulted the support ref `874776f…`, including:

- `schema/ipo-input.v1.5.schema.json` (`1459eaf3…`) and `schema/supplemental-enrichment.v1.schema.json` (`a7ca11f5…`);
- `fixtures/connectors/valid_anchor_snapshot.json` (`ad763623…`) and `fixtures/connectors/03_valid_market_regime.json` (`7f83681c…`);
- `engine/ipo_screening/connectors/adapters.py` (`9b964751…`), `connectors/interfaces.py` (`a93e699a…`), `snapshots.py` (`1b38e7c1…`), and `evaluation.py` (`5519b0e5…`).

Those artifacts establish example shapes and generic implementation behavior only. The anchor and market-regime fixtures are synthetic; provider IDs and fixture timestamps do not authenticate a source or an actual observation. This document does not reacquire or recalculate them.

## 4. Metric decision inputs

### 4.1 `market.anchor.quality`

**Intended meaning — UNRESOLVED.** The field may be intended to express an assessment of the anchor allocation/investor mix. The accessible evidence does not establish that meaning. It must not be inferred from the existence of an allocation report, investor names, or the quantity allocated.

**Non-goals:** do not treat the existence of an Anchor Allocation Report as a “quality” grade; do not infer investor reputation; do not use the field as a proxy for anchor amount or later market performance.

**Candidate official source — PROPOSED, NOT INSPECTED / NOT QUALIFIED:** NSE Issue Information’s Anchor Allocation Report and Security Parameters (Pre Anchor/Post Anchor) for an identified IPO. The exact issue and report are **EVIDENCE REQUIRED**. The supplied Issue Information URL is only a lead.

**Raw fields, definition, and units — EVIDENCE REQUIRED.** The existing canonical schema allows `quality` values `reputed`, `mixed`, `unknown`, or null; the synthetic anchor fixture contains `anchor_quality: "reputed"`. Neither establishes an official field definition, classification criteria, source-native field, or units.

**Transformation options:**

- **Option A — PROPOSED — NOT APPROVED:** pass through a source-published quality category only if the official record and documentation define it.
- **Option B — PROPOSED — NOT APPROVED:** derive a category from allocation/investor attributes only after a separately authorized, explicit rubric exists. This introduces classification judgment and cannot be inferred from current evidence.
- **Option C — PROPOSED — NOT APPROVED:** retain the raw allocation evidence and leave quality unknown when no source-defined category exists. This avoids an unsupported rating but leaves the qualitative metric unavailable.

**Recommended option — PROPOSED — NOT APPROVED:** Option C until evidence establishes a source-defined field; then consider Option A. No heuristic classification is proposed.

**Event/time and cutoff — UNRESOLVED.** Determine from the actual record whether this is an allotment event, a published report, or another observation. Preserve event/as-of, original timestamp and timezone/offset, normalized UTC, publication, retrieval, cutoff, and evaluation times separately where available. A report publication time must not be substituted for an underlying event time. Session/PIT classification and cutoff are not established.

**Missing, stale, and conflicting data — UNRESOLVED.** No source-specific response semantics or freshness interval is evidenced. Do not invent a freshness threshold or convert a missing category into a positive or negative grade. Preserve conflicting source records for the authorized A1 adjudication process; no precedence is selected here.

### 4.2 `market.anchor.amount`

**Intended meaning — UNRESOLVED.** A candidate interpretation is an amount associated with anchor allocation, but the existing field name does not establish whether it means allocated consideration, demand, a category total, or another quantity.

**Non-goals:** do not equate this amount with total offer size, fresh issue, OFS, QIB reservation, subscription demand, or any other reported amount without source definitions. Do not assume pre-anchor, post-anchor, allocation-report, and prospectus quantities should match.

**Candidate official source — PROPOSED, NOT INSPECTED / NOT QUALIFIED:** the same NSE Issue Information Anchor Allocation Report and pre-/post-anchor Security Parameters reports for an identified IPO. Exact report files and field definitions are **EVIDENCE REQUIRED**.

**Raw fields, definition, and units — EVIDENCE REQUIRED.** The canonical schema represents anchor `amount` as a number with no field-level unit. The synthetic fixture’s numeric `anchor_total_amount` and `anchor_total_shares` are not official observations and do not establish currency, scale, scope, or calculation basis.

**Transformation options:**

- **Option A — PROPOSED — NOT APPROVED:** use a source-reported allocation-amount field unchanged, preserving its documented unit and scope.
- **Option B — PROPOSED — NOT APPROVED:** if the official record supplies allocation quantities and an applicable price, derive a value only after the official field definitions establish that the inputs describe the same allocation and do not double-count categories. No calculation is authorized by this artifact.
- **Option C — PROPOSED — NOT APPROVED:** retain the source-native quantity/amount fields separately and leave the canonical amount unavailable until the meaning and unit are settled.

**Recommended option — PROPOSED — NOT APPROVED:** Option A if an official amount field is documented; otherwise Option C. Do not calculate or normalize an amount on the current evidence.

**Event/time and cutoff — UNRESOLVED.** The actual allocation/event date, report publication time, retrieval time, source-native time, and metric-specific cutoff are not established. Preserve pre-anchor, post-anchor, allocation, and prospectus records as separate observations until their fields and event relationships are documented.

**Missing, stale, and conflicting data — UNRESOLVED.** No source-defined empty, unavailable, stale, malformed, non-trading, or conflict behavior has been inspected. Do not treat absent values as zero or use an unapproved freshness interval.

### 4.3 `market.regime.nifty_trend`

**Intended meaning — UNRESOLVED.** The schema permits `supportive`, `neutral`, `weak`, or null. This is an enum shape, not a definition of trend, index, observation frequency, lookback, or classification boundaries.

**Non-goals:** do not infer a trend from an index name, one index value, a synthetic fixture, or a provider label. Do not invent a lookback, threshold, session rule, or cutoff.

**Candidate official source — PROPOSED, NOT INSPECTED / NOT QUALIFIED:** NSE historical index records through the user-provided Historical Reports/All Reports routes. The exact index, series (for example, price index versus total-return index), record type, and report file are **EVIDENCE REQUIRED**.

**Raw fields and units — EVIDENCE REQUIRED.** Candidate fields to verify in the actual report include index identity, observation/session date, source-native index value, field labels, unit/scale, and any close or other session values. No such NSE record was inspected. The synthetic `nifty_trend: "supportive"` fixture does not establish any of these.

**Transformation options:**

- **Option A — PROPOSED — NOT APPROVED:** pass through an official source-provided trend label only if its field definition and timestamp semantics are documented.
- **Option B — PROPOSED — NOT APPROVED:** derive a trend from retained official index observations only after a methodology, index series, observation dates, lookback, classification thresholds, and session/cutoff are explicitly decided. None is chosen here.
- **Option C — PROPOSED — NOT APPROVED:** preserve the official index observations as raw data and leave the trend classification unavailable until a method is authorized.

**Recommended option — PROPOSED — NOT APPROVED:** Option C for this evidence state. A8’s official-close direction applies only after the metric is established as session-defined; this artifact does not classify it.

**Timing and cutoff — UNRESOLVED.** No named index session, source-native observation timestamp, timezone/offset, publication time, retrieval time, cutoff, or evaluation relationship is evidenced. Do not impose a shared market cutoff.

**Missing, stale, non-trading, and conflict behavior — UNRESOLVED.** No official calendar, source behavior, fallback, freshness interval, or conflicting-record rule was inspected. Preserve raw source records and report their own dates; do not forward-fill or substitute a point-in-time value without an approved rule.

### 4.4 `market.regime.last_ipo_listing_gains_pct`

**Intended meaning — UNRESOLVED.** The field name and numeric-array schema do not establish the IPO cohort, whether entries are individual IPO results or an aggregate, the reference price, the listing-session price, or the percentage calculation.

**Non-goals:** do not invent the IPO cohort, listing-price basis, denominator, aggregation, corporate-action treatment, sample size, or observation cutoff.

**Candidate official source — PROPOSED, NOT INSPECTED / NOT QUALIFIED:** NSE security-wise equity price/volume records and any official issue/listing records needed to identify issue prices and listing dates, reached through the user-provided historical-report routes. Exact report/dataset and cohort membership are **EVIDENCE REQUIRED**.

**Raw fields, definitions, and units — EVIDENCE REQUIRED.** For each identified IPO, obtain the actual security/issue identity, issue-price field and unit, listing date, named listing session, relevant price field and basis, corporate-action adjustments if applicable, and source record identifiers. No such source records were inspected. The existing synthetic array of five numbers supplies no issuer names, dates, prices, or units.

**Transformation options:**

- **Option A — PROPOSED — NOT APPROVED:** pass through an official source-published listing-gain value only if its cohort, price basis, calculation, and timestamps are documented.
- **Option B — PROPOSED — NOT APPROVED:** derive per-IPO results from source-documented issue and listing-session price fields, then aggregate only under an explicitly approved cohort and calculation rule. The formula, denominator, price basis, cohort, and aggregation are all unresolved; no values are calculated here.
- **Option C — PROPOSED — NOT APPROVED:** retain the raw per-IPO issue/listing observations and leave the derived metric unavailable until those definitions are established.

**Recommended option — PROPOSED — NOT APPROVED:** Option C for the current evidence state. This preserves potential reproducibility without choosing a cohort, denominator, price basis, or aggregation.

**Timing, session, and cutoff — UNRESOLVED.** A listing date alone would not establish which listing-session price is intended. Preserve event date, actual session identity, source-native observation time/timezone, publication, retrieval, cutoff, and evaluation time separately where available. No common cutoff is proposed.

**Missing, stale, non-trading, and conflicting data — UNRESOLVED.** No source-specific semantics are evidenced for missing issue prices, delayed listings, non-trading dates, incomplete histories, corporate actions, stale prices, or conflicting records. No fallback or freshness threshold is proposed.

## 5. Moneyview anchor discrepancy

**Status: UNRESOLVED — EVIDENCE REQUIRED. No numeric reconciliation is possible from the inspected evidence.**

The inspected governing/support tree paths contained no Moneyview-named source file or anchor-allocation record. The support evidence paths previously reviewed contain A8-S subscription material; the retained references include R.K. Fashion and Vishal Nirmiti materials, not Moneyview anchor records. A repository code-search endpoint was unavailable, so this is a bounded path/evidence inspection, not proof that Moneyview material cannot exist elsewhere. No NSE Moneyview record was accessed.

| Required record | Exact Moneyview file/field/value inspected | Meaning/unit/scope | Status |
|---|---|---|---|
| Security Parameters (Pre Anchor) | None available in inspected scope | Not established | **EVIDENCE REQUIRED** |
| Security Parameters (Post Anchor) | None available in inspected scope | Not established | **EVIDENCE REQUIRED** |
| Anchor Allocation Report | None available in inspected scope | Not established | **EVIDENCE REQUIRED** |
| Final prospectus/RHP | None available in inspected scope | Not established | **EVIDENCE REQUIRED** |

Before reconciling, the issuer/legal entity, IPO symbol/series, exact report versions, field labels, and units must be identified. Total offer, fresh issue, OFS, QIB portion, anchor investor allocation, and any report-specific quantities must remain distinct. No assumption of equality, additivity, or common denominator is made. No discrepancy amount is calculated.

**Smallest evidence needed:** the actual four Moneyview records (or source URLs and retained files), their issue identity, the relevant field labels/units, publication and retrieval metadata, and any official definitions needed to compare the quantities. Until then, the discrepancy remains **UNRESOLVED — EVIDENCE REQUIRED**.

## 6. Consolidated cross-cutting decision inputs

| Topic | Verified direction / current state | Decision input still required |
|---|---|---|
| Source qualification | **UNRESOLVED.** No official source was accessed or qualified. | Identify and assess actual source records and documentation; do not infer qualification from a route or report title. |
| Observation identity | A8 requires evidence that the actual event/observation occurred. | Source-native record/event identifiers and metric-specific observation identity. |
| Session versus PIT | A8 hybrid direction is **VERIFIED**. | Decide per metric only after records establish its semantics. Do not use a shared cutoff. |
| Timestamps | A8 requires original timestamp/timezone-offset alongside normalized UTC; publication, retrieval, cutoff, and evaluation remain distinct where applicable. | Actual source support and meanings for each time field; no source record was obtained. |
| Freshness | No freshness interval may be invented; no metric-specific threshold is approved here. | Source behavior and any later authorized metric-specific rule. |
| Reproducibility | A8 requires evidence/source hashes. | Retain exact source record, URI/report identity, raw fields, retrieval metadata, and required hashes under an approved evidence contract. This artifact chooses no hash serialization or source contract. |
| Missing/unavailable data | **UNRESOLVED per metric.** Do not infer zero or a fallback. | Source-defined response semantics and a separately authorized consequence where required. |
| Conflicting evidence | A1 assigns conflict adjudication authority to Ramki. | Preserve competing observations and provenance; no precedence or adjudication is made here. |
| Raw versus derived | Raw observations must remain distinguishable from derived values. | Metric-specific, explicit transformations after source fields and units are verified and authorized. |

## 7. Decision-input readiness and next evidence-only action

**No specific provider, formula, session, cutoff, cohort, denominator, threshold, freshness interval, missing-data consequence, or Moneyview reconciliation is evidence-ready.** All proposed options in this document are **PROPOSED — NOT APPROVED**. A8-M remains open; no decision is requested.

**Recommended next evidence-only action:** in an environment that can access NSE, retrieve and retain the exact Moneyview pre-anchor, post-anchor, Anchor Allocation, and final-prospectus records; then retrieve representative official index and security-wise listing-price records for identified issues. Record exact source URL/report identity, issue/security identity, file bytes, retrieval time, and source-published date/time where available. First document the source-native field labels and definitions; do not calculate or reconcile quantities until their units and scopes are established. This action does not select or qualify a provider and does not change the approved A8-M direction.

## 8. Governance and publication boundary

This is an additive investigation artifact in the existing `handoff/investigation/` documentation area, following the repository’s separation between investigation material and approved decision records. It is not a new A8 decision and does not overwrite the governing A8 record or any pre-existing untracked file. This artifact was subsequently committed and published on `arena/01a10b42-ipo-screening-engine` at commit `9416da27aed5835c01bf3fd0e729c33062734a54`. The approved decision-record convention remains governing; publication/approval authority is not claimed here.

**Implementation authority: NOT GRANTED. Phase 1: UNAUTHORIZED. Phase 0: OPEN.**

## 9. Addendum — Published Moneyview source evidence

**Prepared:** 2026-10-12 (Asia/Calcutta). **Status:** Investigation-only addendum; no metric definition, provider, policy, gate, or implementation is approved.

This addendum records the Moneyview evidence made accessible in the repository commit below. Earlier statements in §§3 and 5 that no Moneyview records were available describe the evidence set inspected for the original artifact; they are retained as that investigation’s historical finding. This addendum supersedes only the prior evidence-availability gap. It does not supersede the A8-M governance boundaries or approve a metric contract.

### 9.1 Remote commit and file verification

The GitHub API showed `refs/heads/arena/01a10b42-ipo-screening-engine` pointing to commit `96bfd9d1e08697966081b9938a933e2a0baa06b9` on both initial verification and re-verification. The commit message is `Add A8-M Moneyview source evidence`; its parent is `874776f8f283639999dfb4457fbb5119fc7fdc5c` and tree is `2c45bc6f365fe22dcd0a33e1334e69435c0948e2`. The four files listed below were retrieved from that exact commit through the GitHub API. Each downloaded file’s Git blob hash matched the blob ID in the commit tree. The active session checkout was not switched or synchronized.

| Published file | Bytes | Commit-tree blob | SHA-256 |
|---|---:|---|---|
| `handoff/investigation/A8-M-MONEYVIEW-SOURCE-EVIDENCE/ANCHOR_MONEYVIEW.zip` | 284,007 | `1a10baa1c9371febe3a33ce2cc636863eb74c2f4` | `e4c6e4ca2a519bf6d8454cee7f1d6ffd4ceaf1b09ea888b3dfeef55126cd856f` |
| `handoff/investigation/A8-M-MONEYVIEW-SOURCE-EVIDENCE/PREANCHOR_PARAMETERS_MONEYVIEW.zip` | 358,633 | `942e42d4763406e6ec31dffc3f3978b0facf6d4b` | `4832abd2f502b39c84dae98aa544475b6e46b3b11e6c18160ca475d5d94cfff8` |
| `handoff/investigation/A8-M-MONEYVIEW-SOURCE-EVIDENCE/POSTANCHOR_PARAMETERS_MONEYVIEW.zip` | 359,904 | `cbf867adf6695f8fcc29139a01c454b30afd4d4d` | `8556053230b81bb830a075e05790649990b177467adf6720ebcdd2c47a9e72fe` |
| `handoff/investigation/A8-M-MONEYVIEW-SOURCE-EVIDENCE/Moneyview_Final_Prospectus_Full.pdf` | 15,839,834 | `cae4afd10aff77793c27b090f784209cbee70ec4` | `b29ea6b6c7474d91da14d3be2492f02df9501c8346bb61e429b0d29d0c03555f` |

All three ZIP archives passed CRC integrity checks and each contains one PDF:

- `ANCHOR_MONEYVIEW.zip` → `ANCHOR_MONEYVIEW/MV_Intimation_Anchor_to SEs.pdf` (4 pages; SHA-256 `5f0b561c64c7585694f7cd1e4d399c9c1471070b066ac86a10acc9eb787bcc08`).
- `PREANCHOR_PARAMETERS_MONEYVIEW.zip` → `PREANCHOR_PARAMETERS_MONEYVIEW/PREANCHOR_PARAMETERS_MONEYVIEW.pdf` (3 pages; SHA-256 `5f1b05443acf82a23154371de0b420fe6020ef1d5d09d169b0d4df3bf436e5fb`).
- `POSTANCHOR_PARAMETERS_MONEYVIEW.zip` → `POSTANCHOR_PARAMETERS_MONEYVIEW/POSTANCHOR_PARAMETERS_MONEYVIEW.pdf` (3 pages; SHA-256 `d49cafb23ef633af920d9a51999e1e4ae1de87ec1ebd45f73a0f75011d88897b`).

The final prospectus PDF has 537 pages. Text was extracted from the PDFs with `pypdf 6.20.0` and the relevant source pages below were inspected; no OCR was used. Prospectus page references below give PDF page first and printed folio where visible. The bundle supplies no original NSE download URLs, HTTP retrieval headers, or NSE publication timestamps. Embedded PDF creation/modification metadata is recorded as file metadata only, not treated as a source publication time or event time.

### 9.2 Source fields and report context

#### NSE-labelled Security Parameters — Pre Anchor and Post Anchor

Both reports are titled `Security Parameters Moneyview Limited - EQ (Mainboard) IPO` and show Security symbol `MONEYVIEW`, Series `EQ`, and Company Name `Moneyview Limited` (PDF p.1). They show a price range of Rs. 32 to Rs. 34 per Equity Share and an issue period of 24-Sep-2026 to 28-Sep-2026. The schedule also shows bidding 10:00 a.m.–5:00 p.m., QIB/NIB close at 4:00 p.m. on 28-Sep-2026, and UPI mandate confirmation cutoff at 5:00 p.m. These are issue-window details, not a metric observation timestamp.

The source row labelled `Issue size` reads, in the Pre Anchor report, “Initial public offering comprising of aggregating up to 7500 million and offer for sale up to 10,04,94,200 Equity Shares.” The Post Anchor report repeats this and appends “(including Anchor portion of 9,63,24,729 Equity Shares).” The NSE row itself does not put a currency symbol beside `7500 million`; the final prospectus identifies the fresh-issue amount as ₹7,500 million. Do not treat this prose row as a single anchor-amount field.

On PDF p.2, the table labelled `Main Category` / `No of equity shares reserved for the main category` and `Total Issue size (1+2+3)` reports:

| Source field | Pre Anchor | Post Anchor | Source unit/context |
|---|---:|---:|---|
| QIB | Not more than 16,74,34,600 | Not more than 6,50,89,575, **excluding** the stated anchor portion of 9,63,24,729 | Equity Shares; the QIB row in the Post Anchor report explicitly excludes anchors |
| NIB (Total) | Not less than 5,02,30,380 | Not less than 5,02,30,380 | Equity Shares |
| Retail | Not less than 11,72,04,220 | Not less than 11,72,04,220 | Equity Shares |
| Total Issue size (1+2+3) | 33,48,69,200 | 23,25,24,175 | Equity Shares; each report says the above numbers are calculated at the lower end of the price band, Rs. 32 |

The category rows sum to each report’s displayed total. In Post Anchor, because the QIB row explicitly excludes 9,63,24,729 anchor shares, the displayed category total is the non-anchor sum; it is not directly comparable to the Pre Anchor total without accounting for that exclusion. The reports also have a distinct `Max Bid quantity` table; those bid limits are not the `No of equity shares reserved` fields or an anchor-allocation total and are not used in the reconciliation below.

Embedded PDF metadata gives Pre Anchor creation/modification `2026-09-23 12:58:05 +05:30` and Post Anchor `2026-09-23 15:54:40 +05:30`. These values do not establish publication time or the exact event ordering. In particular, the issuer’s anchor letter states a committee-meeting date but no time; the `POSTANCHOR` filename and PDF metadata alone do not prove when the underlying allocation event occurred.

#### Issuer anchor-allocation intimation to the exchanges

The PDF `MV_Intimation_Anchor_to SEs.pdf` identifies Moneyview Limited (formerly Moneyview Private Limited and Whizdm Innovations Private Limited), CIN `U72200KA2014PLC075775`, and is addressed to the listing departments of BSE and NSE. It is dated September 23, 2026, and says the IPO Committee finalized the allocation at a meeting held on September 23, 2026. The letter says **96,324,729 Equity Shares** were allocated to Anchor Investors at an Anchor Investor Allocation Price of **₹34 per Equity Share**, including a share premium of ₹33 (face value ₹1).

The table’s exact labels include `Name of Anchor Investor`, `No. of Equity Shares Allocated`, `% of Anchor Investor Portion`, `Bid Price (₹ per Equity Share)`, and `Total Amount Allocated (₹)`. Its total row reports **96,324,729 shares**, **100.00%**, and **₹3,275,040,786.00**. The amount is arithmetically consistent with 96,324,729 × ₹34 = ₹3,275,040,786. The letter also reports 69,632,136 shares (72.29%) allocated to seven domestic mutual funds through 14 schemes, and separately lists HDFC Life Insurance Company Limited with 2,942,793 shares (3.06%). These are source-reported allocation/composition fields; the letter contains no anchor “quality” grade or quality rubric.

The PDF letter is dated September 23. Its embedded metadata records CreationDate `2026-09-23 20:56:20 +05:30` and ModDate `2026-09-23 21:04:49 +05:30`; neither is treated as the event time or proof of exchange publication.

#### Moneyview final prospectus

The document is titled a Prospectus dated September 28, 2026; its cover identifies Moneyview Limited and CIN `U72200KA2014PLC075775`. The cover and Offer sections state a final Offer Price of ₹34 per Equity Share (face value ₹1, including ₹33 premium). The relevant fields are:

| Prospectus field | Reported quantity/amount | Context |
|---|---:|---|
| Offer / Total Offer | 321,082,435 Equity Shares; ₹10,916.80 million | PDF pp.1, 92/printed p.87, and 473/printed p.468; starred quantities/amounts are subject to finalization of Basis of Allotment |
| Fresh Issue | 220,588,235 Equity Shares; ₹7,500.00 million | Same pages; Capital Structure PDF p.112/printed p.107 gives ₹7,499,999,990 |
| Offer for Sale | 100,494,200 Equity Shares; ₹3,416.80 million | Same pages; Capital Structure gives ₹3,416,802,800 |
| QIB Portion | 160,541,216 Equity Shares; ₹5,458.40 million | PDF p.92/printed p.87; includes Anchor Investor Portion |
| Anchor Investor Portion | 96,324,729 Equity Shares | Same table; a component of the QIB Portion |
| Net QIB Portion | 64,216,487 Equity Shares | Same table; 96,324,729 + 64,216,487 = 160,541,216 |
| Non-Institutional Portion | 48,162,366 Equity Shares; ₹1,637.52 million | Same table |
| Retail Portion | 112,378,853 Equity Shares; ₹3,820.88 million | Same table |

The three investor-category quantities (QIB, Non-Institutional, Retail) sum to the 321,082,435-share Offer. Capital Structure (PDF p.112/printed p.107) gives exact aggregate values of ₹10,916,802,790 for the Offer, ₹7,499,999,990 for the Fresh Issue, and ₹3,416,802,800 for the Offer for Sale. The Offer Structure (PDF p.473/printed p.468) and offer summary identify the Anchor Investor Portion under QIB; the cited tables do not cross-tab anchor allocations by Fresh Issue versus Offer for Sale. The Prospectus PDF metadata’s ModDate is `1900-01-01 00:00:00 +05:30`, which is not used as a publication timestamp.

### 9.3 Reconciliation — comparable values and unresolved differences

1. **Anchor allocation quantity — reconciled.** The issuer’s dated intimation, the Post Anchor Security Parameters text, and the final Prospectus each report **96,324,729 Equity Shares** for the anchor portion. The issuer intimation separately gives its amount at ₹34 as **₹3,275,040,786**. This amount is not the Offer size, the Offer for Sale size, or the whole QIB Portion.
2. **Final Offer total — reconciled within the Prospectus.** 220,588,235 Fresh Issue shares + 100,494,200 Offer for Sale shares = 321,082,435 Offer shares. The category split also reconciles: 160,541,216 QIB + 48,162,366 Non-Institutional + 112,378,853 Retail = 321,082,435. Within QIB, 96,324,729 Anchor + 64,216,487 Net QIB = 160,541,216. Keep these distinct dimensions separate: Fresh Issue/Offer for Sale describe offer components; QIB/NIB/Retail describe investor categories; Anchor is a sub-portion of QIB.
3. **Pre Anchor lower-band total versus final-price total — explained by price basis, with an explicitly derived check.** The Pre Anchor report says its share counts use the lower price-band end, ₹32. Using the Prospectus’s ₹7,500,000,000 Fresh Issue amount, ₹7,500,000,000 ÷ ₹32 = **234,375,000 implied Fresh Issue shares** at that price; adding the explicitly reported 100,494,200 Offer for Sale shares gives **334,869,200**, exactly the Pre Anchor `Total Issue size (1+2+3)`. This 234,375,000 is an arithmetic derivation, not a source-displayed field. At the final ₹34 price, the Prospectus reports 220,588,235 Fresh Issue shares plus the same 100,494,200 Offer for Sale shares, totaling 321,082,435. The 13,786,765-share change between the floor-basis total and final-price total is consistent with the Fresh Issue share count changing as the price moves from the floor to the final price. This arithmetic explains the pre-versus-final share-count difference; it does not establish that every source-level issue-size definition reconciles.
4. **Post Anchor category total — UNRESOLVED — EVIDENCE REQUIRED.** The Post Anchor table reports 232,524,175 shares across its displayed categories, with the QIB figure expressly excluding 96,324,729 anchor shares. Adding that expressly excluded quantity gives 328,848,904. Against the Pre Anchor lower-band total of 334,869,200, **6,020,296 shares remain unexplained**. Equivalently, subtracting the anchor portion from the Pre Anchor QIB maximum 167,434,600 would leave 71,109,871, while the Post Anchor report states 65,089,575 excluding anchors—a 6,020,296-share difference. NIB and Retail rows are unchanged between these two reports. The published files do not explain this residual or establish whether a revision, adjustment, or different reservation basis accounts for it. Do not force equality or use the Post Anchor total as a substitute for the final Prospectus Offer total.
5. **Anchor versus OFS — UNRESOLVED — EVIDENCE REQUIRED.** The Post Anchor `Issue size` prose appends “including Anchor portion of 9,63,24,729 Equity Shares” to the sentence that also mentions the Offer for Sale. The Prospectus separately reports the Offer for Sale and classifies Anchor as part of QIB, but the cited tables do not state whether/how the anchor shares are sourced between Fresh Issue and Offer for Sale. The wording is insufficient to equate the Anchor Investor Portion with the Offer for Sale or to allocate it between those offer components.

### 9.4 Effect on A8-M metric inputs

| Metric | Evidence-supported update | Remaining status |
|---|---|---|
| `market.anchor.quality` | The issuer letter supplies investor names, allocated shares, percentage of the Anchor Investor Portion, bid price, and amount. It supplies no quality label or rubric. | **UNRESOLVED.** Retain the prior proposed “unknown absent a source-defined category” option; no investor-reputation heuristic or quality grade is authorized. |
| `market.anchor.amount` | The issuer letter contains the source field `Total Amount Allocated (₹)` and aggregate ₹3,275,040,786 at ₹34 for this issue. | Candidate source-native amount is now evidenced for this record. Pass-through remains **PROPOSED — NOT APPROVED**; provider qualification, metric-wide meaning/unit contract, event/cutoff, and missing/conflict rules remain open. Do not generalize this one record to all IPOs. |
| `market.regime.nifty_trend` | No new index observation or trend evidence in this bundle. | Unchanged; **UNRESOLVED**. |
| `market.regime.last_ipo_listing_gains_pct` | No listing-price or cohort evidence in this bundle. | Unchanged; **UNRESOLVED**. |

### 9.5 Remaining evidence and governance boundary

To resolve the **6,020,296-share Post Anchor residual**, obtain the original NSE publication/version details and a source explanation or corrected record for the Post Anchor `No of equity shares reserved for the main category` / `Total Issue size (1+2+3)` fields. To resolve the **Anchor-versus-OFS wording**, obtain an authoritative field definition or offer/allotment record that explicitly maps Anchor shares to Fresh Issue and/or Offer for Sale. The repository bundle has not preserved NSE source URLs, publication timestamps, retrieval timestamps, or a source explanation for either point. The PDF metadata above cannot fill that gap. The Moneyview-record retrieval portion of the earlier §7 action is therefore partially fulfilled by these commit-sourced copies; direct-source provenance and the post-anchor residual explanation remain outstanding. The bundle contains no Nifty index or IPO listing-price observations, so those evidence actions remain outstanding.

This evidence improves the Moneyview amount and quantity record but does not qualify NSE or the issuer letter as a provider for production use. No source/session/cutoff, quality formula, missing-data behavior, freshness rule, or conflict precedence is approved. A8-M and Phase 0 remain open; Phase 1 remains unauthorized; implementation authority remains not granted. This addendum was published with the artifact on `arena/01a10b42-ipo-screening-engine` at commit `9416da27aed5835c01bf3fd0e729c33062734a54`.