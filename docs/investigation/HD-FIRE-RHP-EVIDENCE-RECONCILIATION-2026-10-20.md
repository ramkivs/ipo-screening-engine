# HD Fire Protect Limited — RHP evidence reconciliation and engine input validation

- **Date:** 2026-10-20 (Asia/Calcutta)
- **Subject:** the HD Fire Protect Limited scorecard `HD-FIRE-PROTECT-LIMITED-20261019-123134Z-final-551a7eab`
  (7/100, result hash `551a7eab…`) and the 13 financial, 10 valuation, 4 offer-structure,
  2 audit and 4 contingent-liability values proposed for it.
- **Scope:** evidence reconciliation and input-contract validation. No scoring weight,
  threshold, formula, knockout semantic, penalty rule, golden fixture or historical
  evaluation was changed.
- **Branch:** `arena/ae4d04e8-ipo-screening-engine` at `b8723cb` (remote-verified equal
  before this pass; the publication amendment at the end of this file records the
  post-commit state).
- **SUPERSEDED IN PART (2026-10-20, later pass):** the dispositions in §B of this record were
  produced when **no** HD Fire document was retrievable. The primary sources have since been
  recovered and the table re-dispositioned to **25 verified / 8 contradicted / 10 unresolved /
  1 not applicable** in
  `docs/investigation/HD-FIRE-PRIMARY-SOURCE-RECOVERY-2026-10-20.md` (§4). That later table is
  authoritative for field dispositions. The arithmetic, engine findings and §C–§G analysis in
  this record are retained unchanged as the earlier state of the investigation, and its
  "no primary source" premise is now known to be a retrieval-method artefact rather than a
  fact about the world.

---

## 0. Repository state established before any work

| Item | Value | How verified |
|---|---|---|
| Branch | `arena/ae4d04e8-ipo-screening-engine` | `git rev-parse --abbrev-ref HEAD` |
| Commit at start | `b8723cb0b405b052d4ec857c6a868486c72f7a40` | `git rev-parse HEAD`; `git ls-remote origin` returned the same SHA |
| Checkout state | Clean at the start of this pass (only this pass's additions are untracked); HEAD equals the remote tip | `git rev-parse HEAD` = `git ls-remote origin refs/heads/arena/ae4d04e8-…`; `git status --short` |
| Context | This is the **continuation** of the HD Fire/Jio remediation branch (`345caf7` → `568860b` → `86d4950` → `f42b6ce` → `d6c4919` → `af54cfc` → `80a5abb` → `b8723cb`). It is **not** an HD-Fire-specific branch, and it is **not** PR #6 (PR #6 is `arena/5dd3fe52…`, head `e05c0ef`, `OPEN`, `mergedAt: null`, base `arena/573e69a4…`). | `git log`, `gh pr view 6` |
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched | `git ls-remote origin refs/heads/main` |
| Engine / config / spec | 1.5.0 / `config/ipo-config.v1.5.0.json` (1.5.0) / 1.5 | `engine/ipo_screening/version.py`, config header |
| Environment | `.venv` recreated (`python3 -m venv .venv` + `pip install -r requirements.txt`), `PYTHONPATH=engine` | commands in §F |

Relevant paths:

- Implementation: `engine/ipo_screening/extraction/{sections,financial_tables,builder,toc,numbers}.py`,
  `engine/ipo_screening/{derived,scoring,canonical,canonical_input,snapshots,schema_validation}.py`,
  `engine/ipo_screening/enrichment_engine.py`, `engine/ipo_screening/presentation/service.py`
- Contract: `schema/ipo-input.v1.5.schema.json`, `config/ipo-config.v1.5.0.json`
- Tests: `tests/test_{extraction,extraction_phase5b,fixture_fallback_isolation,rk_fashion_reconciliation,
  enrichment_engine,acceptance_matrix,jio_evidence_remediation,financial_statement_column_mapping,
  ofs_nil_binding,peer_row_mapping_and_bounds}.py`, and the new
  `tests/test_promoter_holding_extraction.py`
- Tracker: `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`
- Prior records: `docs/investigation/HD-FIRE-JIO-{SCORE-RECONCILIATION-2026-10-19,EVIDENCE-REMEDIATION-2026-10-20}.md`,
  `docs/investigation/HD-FIRE-PEER-ROE-SCHEMA-VIOLATION-2026-10-19.md`
- Evidence: `evidence/non-authoritative/jio/` (Jio only), `evidence/gmp-observations/*`,
  `evidence/ipo-subscription/vnl-20261011/`, `handoff/reference/*.pdf` (R.K. Fashion, Vishal Nirmiti)

---

## A. Executive conclusion

### A.1 The decisive finding: no HD Fire primary source exists in this repository

There is **no HD Fire Protect RHP, restated consolidated financial statement, auditor's report,
contingent-liability note, shareholding table, offer-for-sale table, basis-for-issue-price section,
peer-comparison table or persisted evaluation record** anywhere in this workspace *or* in any other
remote branch of the repository (17 remote branches were enumerated and their trees searched on
2026-10-20; the only HD Fire paths returned are four investigation `.md` files in this branch
(three preceding this report) and one of them in `arena/d15866b5`). This was established, not assumed:

```bash
find . -not -path "./.git/*" -iname "*hd*fire*"          # four investigation .md files only
grep -ril "hd fire\|hdfire\|harish narshi\|dharamshi" .    # docs + tracker + 4 GMP captures + 3 tests
find . -name "*.pdf" -not -path "./.git/*"                # Jio, R.K. Fashion, Vishal, Moneyview, fixtures
grep -rl "551a7eab…\|HD-FIRE-PROTECT-LIMITED-20261019-123134Z" .   # .md only; no record/JSON
gh api repos/.../branches --paginate                      # 17 branches; every tree searched
gh api repos/.../git/trees/<branch>?recursive=1           # no HD Fire PDF in any branch
```

The only HD Fire artefacts in the repository are:

| Artefact | Path | Nature |
|---|---|---|
| GMP/price capture (InvestorGain) | `evidence/gmp-observations/investorgain-tonbo-20261015/source-captures/investorgain-ipo-gmp-live-331-chunk-0.md:51` | secondary aggregator |
| GMP/price capture (PapsDigital) | `evidence/gmp-observations/papsdigital-tonbo-20261015/source-captures/papsdigital-ipo-gmp-chunk-0.md:97-135` | secondary aggregator |
| GMP/price capture (MarketLiveIPO) | `evidence/gmp-observations/marketliveipogmp-tonbo-20261015/source-captures/marketliveipogmp-home-chunk-0.md:206-218` | secondary aggregator |
| Prior internal analyses | `docs/investigation/HD-FIRE-*.md`, tracker | internal, not source |

Those captures are dated 2026-10-15 and are **not official**: no NSE/BSE/SEBI/issuer document
is involved. Sandbox egress is blocked (`curl` to `nseindia.com`, `bseindia.com`, `sebi.gov.in`,
the issuer and a control host all returned HTTP 000), so no live retrieval was attempted or
is claimed.

**Consequence:** every HD Fire value in this report is graded by *arithmetic and contract
consistency*, never by page/table inspection. No page number, note number or verbatim
excerpt from an HD Fire filing is cited anywhere below, because none can be.

The reference evaluation record is likewise absent: `evaluations/` does not exist and no
`evaluation.json` carries the hash `551a7eab…`. **The score, base, penalty, confidence and hash
could not be retrieved and are therefore not independently confirmed**; only the documented
values are available. What *is* verifiable is that they are arithmetically self-consistent (§A.2).

### A.2 What can be confirmed without the filing

The recorded aggregates reconcile exactly under the governed configuration:

- Module subtotals A 2 + B 0 + C 3 + D 5 + E 0 + F 0 = **10**;
- one applied penalty (`receivable_days_up`, −3); 10 − 3 = **7**;
- available 27 + unknown 73 = 100; completeness 27/100 = **27 %** (Low);
- floor `max(0, 10 − 3 − 10) = 0` requires ≥ 7 unresolved penalty points, which the four
  UNKNOWN penalties (3 + 2 + 2 + 3) supply; ceiling `min(60, 10 + 73 − 3) = 60` requires
  the pure-OFS cap, hence `fresh_issue == 0` **and** `ofs > 0` in the evaluated snapshot.

The recorded `revenue_cagr` 2/6 is consistent with the configured bands
(`>25 → 6`, `≥15 → 4`, `≥8 → 2`) at **14.54 %**, which is exactly the CAGR produced by the
proposed revenue series (`(489.28/372.95)^(1/2) − 1 = 14.539 %`). That is a genuine
cross-check: the proposed FY2024–FY2026 revenues are consistent with a value the engine
actually scored, although it does not make them source-verified.

### A.3 Dispositions at a glance

Counts are **per field row in §B** (44 rows: 14 under A, 11 under B, 8 under C, 5 under D/K1,
4 under K5 and 2 under RPT/K6), so they can be re-derived from the tables:
`awk -F'|' '{print $(NF-2)}'` over §B gives 10 verified, 7 contradicted, 26 unresolved,
1 not applicable = 44.

| Category | Count | Items |
|---|---:|---|
| **Verified** (arithmetic reproduces, engine contract satisfied) | 10 | revenue CAGR 14.54 % (as an engine input); EBITDA margin 30.75 %; issue P/E 40.69×; implied market cap ₹4,748.70 cr; EV/EBITDA 30.67× (issuer side); P/B 11.88×; second multiple (NAV basis); aggregate OFS proceeds ₹712.31 cr; 100 %-OFS classification (record level); no fresh issue / proceeds use |
| **Contradicted** | 7 | PAT margin 23.12 % as an engine input; CFO/PAT 0.79× as the engine metric; Harish Dharamshi proceeds; Kusum Dharamshi proceeds; going-concern CLEAR; "net worth > ₹1,000 cr"; "K5 can be cleared" |
| **Unresolved** (no primary source) | 26 | all raw financial values; cash; NAV/share; peer median P/E 63.0×; peer EV/EBITDA; seller share counts; auditor opinion type; BG/EPCG amounts; RPT 33.10 % and its growth share; and the remaining field rows in §B |
| **Not applicable** | 1 | "transactions are at arm's length" — no engine field consumes it |
| **Engine defects established** | 2 | promoter pre/post-issue holding fallback fabricates 100 % (§C.4); auditor tenure / repeated-EOM favourable defaults (§C.5) |

Two further claims are **not scorable at all** rather than unresolved, and are therefore counted
neither above nor as N/A field rows: seller-level proceeds (no `amount` field exists in
`$defs.seller`, §D.2) and the ₹712.13 cr aggregator issue size (a secondary source that
contradicts the arithmetic by 0.03 %, §D.2). Neither can enter the canonical input, so no
disposition changes a score.

### A.4 Is there a real engine defect?

**Yes — two, both confirmed on committed code and evidence rather than inferred.** The first
is the `Total (A)`/`Total (B)` fallback in `SectionExtractor.extract_capital_structure`, which
returns **100 %** for the promoter holding whenever the block carries the ICDR shape — a combined
`Total (A)+(B)+(C)` summary row, or both category totals (the per-input matrix is in §C.4). On the committed Jio RHP (p. 107) it returns
`promoter_pre_pct = 100.0` / `promoter_post_pct = 100.0` where the filing states
**66.43 %** pre-issue (public 33.57 %) and prints `[●]` post-issue. That value feeds
Module D `promoter_post_holding` (4/4) and K4's `promoter_full_exit` / `<20` leaves.

This bears directly on HD Fire: its record carries `promoter_post_pct = 100 %` → 4/4 and
K4 CLEAR, in an offer that is 100 % OFS by two named individuals. A 100 % post-issue
promoter holding is **structurally impossible** in that structure (the OFS is 15.000 % of the
post-issue shares, so 100 % × (1 − 15.000 %) = 85.0 %; §F.3). The mechanism is demonstrated; the HD Fire instance cannot be re-executed
because the filing is absent.

**The correction was deliberately not applied** — it changes a scored canonical input
(§F.3 quantifies the effect), which is a missing-value/semantic decision the current
authorization does not cover. The defect is pinned by three `xfail(strict=True)` tests so
it cannot be silently "fixed" or silently forgotten.

A **second** defect is in the same class (§C.5): `extract_governance` emits
`auditor_changed_3y = False` and `repeated_eom = False` as constants whenever an auditor name
is found, each carrying a synthesised sentence that is not in the filing. Together with the
hard-coded "reputed firm" list these decide `_auditor_bucket`, so an unqualified opinion from a
listed firm reaches `clean_reputed` **2/2** on two defaults. Jio escaped it only because its
report layout did not yield an auditor name; HD Fire's `auditor` is UNKNOWN in the record, so
these points were not awarded there — but any filing of the matching shape would receive them.

---

## B. Evidence reconciliation table

Legend — **Status**: `VERIFIED` = independently recalculated and consistent with the engine
contract · `CONTRADICTED` = arithmetic or contract contradicts the claim · `UNRESOLVED` = the
primary source is not available, so the claim can be neither confirmed nor refuted ·
`NOT APPLICABLE` = no engine field consumes it.
Every "Primary source" cell reads *absent* for HD Fire; the column is retained so that the gap
is explicit rather than omitted.

### B.1 Module A — Financial quality

| Module / criterion | Proposed value or claim | Primary source (document, page/note) | Source value | Independently calculated value | Existing engine field / contract | Evidence-flow status | Final disposition | Reason and next action |
|---|---|---|---|---|---|---|---|---|
| A `revenue_cagr` | FY2024 revenue ₹372.95 cr | **Absent** | — | — | `financials.periods[].revenue`, `INR_CRORES` after unit conversion; `revenue_cagr_2y_from_3fy` needs 3 full FYs | Not extractable | **UNRESOLVED** | Supply the restated P&L; verify the column is FY (not stub) and the unit |
| A `revenue_cagr` | FY2025 revenue ₹432.80 cr | **Absent** | — | YoY +16.05 % vs FY24 | same | Not extractable | **UNRESOLVED** | as above |
| A `revenue_cagr` | FY2026 revenue ₹489.28 cr | **Absent** | — | YoY +13.05 % vs FY25 | same | Not extractable | **UNRESOLVED** | as above |
| A `revenue_cagr` | CAGR 14.54 % | Absent | — | **14.539 %** = (489.28/372.95)^0.5 − 1 | 2 points at `≥8` and `<15`; **matches the recorded 2/6** | Arithmetic only | **VERIFIED (arithmetic)** | No score change at 14.54 %; source still required |
| A `margin_trend` | FY2026 operating EBITDA ₹150.46 cr | **Absent** | — | — | `periods[].ebitda`; `margin_trend` needs EBITDA **and** PAT margins for ≥2 FYs | Not extractable | **UNRESOLVED** | Supply 2–3 FYs of EBITDA and PAT, not one year |
| A `margin_trend` | EBITDA margin 30.75 % | Absent | — | **30.751 %** = 150.46/489.28 | Margin denominator is **revenue**, not total income | Arithmetic only | **VERIFIED (arithmetic)** | Denominator choice matches the contract |
| A `margin_trend` | FY2026 PAT ₹116.79 cr | **Absent** | — | consistent with 6.66 × 17.523 cr shares = 116.70 cr | `periods[].pat` | Not extractable | **UNRESOLVED** | Supply the PAT series (K3 depends on its trend) |
| A `margin_trend` | PAT margin 23.12 % | Absent | — | **23.870 %** on revenue; 23.12 % needs a ₹505.15 cr denominator | `_margins()` divides by `revenue` — `derived.py:274-283` | Not representable | **CONTRADICTED** | 23.12 % is a total-income ratio and is **not** the engine's metric; use 23.87 % or leave UNKNOWN |
| A `roce` | ROCE 40.33 % | **Absent** | — | implies EBIT = 0.4033 × CE; at CE ≈ ₹399.9 cr → **EBIT ₹161.3 cr > EBITDA ₹150.5 cr** | `roce_latest`: disclosed ROCE wins (`derived.py:376-421`), else EBIT/(net worth + total debt) | Not extractable | **UNRESOLVED** | Internally inconsistent with operating EBITDA unless the RHP's ROCE numerator includes other income; the RHP definition page is required |
| A `cfo_quality` | Cash and cash equivalents ₹134.3 cr | **Absent** | — | — | `periods[].cash_and_equivalents` | Not extractable | **UNRESOLVED** | Feeds EV/EBITDA; supply the balance-sheet line |
| A `cfo_quality` | FY2026 CFO ₹92.49 cr | **Absent** | — | — | `cfo_pat_cumulative` requires `cfo` **and** `pat` for **every** FY in the window (`derived.py:423-460`) | Not extractable | **UNRESOLVED** | A single-year CFO cannot form the metric |
| A `cfo_quality` | CFO/PAT ≈ 0.79× | Absent | — | **0.7919** = 92.49/116.79 | Engine metric is **cumulative** ΣCFO/ΣPAT, explicitly "not the arithmetic mean of annual ratios" | Not representable | **CONTRADICTED** | 0.79× is a one-year ratio; populating it as `cfo_pat_cumulative` would substitute a different definition |
| A `leverage` | Debt-to-equity 0.00× | **Absent** | — | requires `total_debt = 0` **and** `interest_expense = 0` | `leverage_bucket`: debt-free with zero finance cost → `strong` + explicit reason (`derived.py:494-513`); zero cost with debt outstanding → UNKNOWN | Not extractable | **UNRESOLVED** | Supply borrowings and finance costs; a debt-free balance sheet scores 4/4 but only from both lines |
| A `roce` / D `rpt` | Net worth (see §D.3) | **Absent** | — | NAV/share implies **₹399.87 cr**; ROE implies prior year ≈ ₹374–376 cr | `net_worth_latest` = `periods[-1].net_worth`, in ₹ crore after scaling | Not extractable | **UNRESOLVED** | See §D.3; the "> ₹1,000 cr" claim is contradicted |

### B.2 Module B — Valuation

| Module / criterion | Proposed value or claim | Primary source | Source value | Independently calculated value | Engine field / contract | Evidence-flow status | Final disposition | Reason and next action |
|---|---|---|---|---|---|---|---|---|
| B (all) | Upper issue price ₹271 | **Absent** (two independent aggregator captures agree: "Price Band ₹271 – ₹271", lot 55) | — | — | `issue.price_band_high`; `_issue_price()` (`derived.py:546`) | Operator-entered, `MANUAL_ENTRY` | **UNRESOLVED** | The RHP price band page is the only acceptable source; aggregators are secondary |
| B `pe_vs_peers` | FY2026 diluted EPS ₹6.66 | **Absent** | — | 116.79 cr × 10⁷ / 175,228,782 = **6.665** | `issue.post_issue_eps` (unit-aware builder, `builder.py:211-232`); `_issuer_pe = price / eps` | Not extractable | **UNRESOLVED** | EPS must be the post-issue basis at the upper band |
| B `pe_vs_peers` | Issue P/E ≈ 40.7× | Absent | — | **40.691** = 271/6.66 (40.660 on the unrounded 6.665) | `pe_premium_pct = issuer P/E ÷ median VALID peer P/E − 1` | Arithmetic only | **VERIFIED (arithmetic)** | Depends on an operator price |
| B `pe_vs_peers` | Claimed peer median P/E 63.0× | **Absent** — no peer table, no valuation date, no source | — | — | Requires per-peer `pe`, `as_of` within `peer_staleness_days` (30), `listed_years ≥ 3`, `business_match ≠ mismatch`; only `VALID` peers score (`snapshots.py:190-266`) | Nothing to feed | **UNRESOLVED** | At 63.0× the premium is −35.4 % → **8/8**, so the claim must not be accepted without the filing's designated peer set, price date and source |
| B `pe_vs_peers` | Discount to peers ≈ 35 % | Absent | — | **−35.41 %** = 40.691/63.0 − 1 | Band `≤ −20` → 8 points | Arithmetic only | **VERIFIED (arithmetic), invalid as evidence** | Arithmetic is right; the denominator is unverified |
| B `second_multiple` | Implied market capitalisation ₹4,748.7 cr | Absent | — | 271 × 175,228,782 = **₹4,748.70 cr**; implies **175,228,782** post-issue shares | `_market_cap = price × post_issue_shares / 10⁷` (`derived.py:558-565`) | Arithmetic only | **VERIFIED (arithmetic)** | The implied share count is the value the engine actually needs |
| B `second_multiple` | EV/EBITDA ≈ 30.7× | Absent | — | **30.669** = (4,748.70 − 134.3)/150.46 | `_issuer_ev_ebitda = (mcap + debt − cash)/EBITDA`; peer side needs a VALID peer `ev_ebitda` or `pb` | Arithmetic only; peer side empty | **VERIFIED (arithmetic); peer side UNRESOLVED** | Issuer multiple is reproducible; a peer EV/EBITDA median is not available |
| B `second_multiple` | NAV per share ₹22.82 | **Absent** | — | implies net worth **₹399.87 cr** (= 22.82 × 17.5229 cr) | not a scored field; used here as a reconciliation anchor | Not extractable | **UNRESOLVED** | Contradicts the "> ₹1,000 cr" net-worth claim (§D.3) |
| B `second_multiple` | P/B ≈ 11.9× | Absent | — | **11.876** = 271/22.82; engine: mcap/(net worth + fresh) = 4,748.70/399.87 = **11.876** (fresh = 0) | `_issuer_pb` (`derived.py:587-597`) | Arithmetic only | **VERIFIED (arithmetic)** | Same net-worth anchor |
| B `peg` | (not claimed) | Absent | — | 40.691 ÷ PAT CAGR — PAT CAGR unavailable | `peg = post-issue P/E ÷ 2-year PAT CAGR` (`derived.py:695-715`) | Not formable | **UNRESOLVED** | Needs a 3-FY PAT series |
| B `sector_ipo_relative` | (not claimed) | Absent | — | — | Needs ≥1 `recent_sector_ipos[].pe_at_issue` | Empty | **UNRESOLVED** | Genuinely external |

### B.3 Module C — Offer structure, OFS and proceeds

| Module / criterion | Proposed value or claim | Primary source | Source value | Independently calculated value | Engine field / contract | Evidence-flow status | Final disposition | Reason and next action |
|---|---|---|---|---|---|---|---|---|
| C `fresh_share` | 100 % OFS, fresh issue nil | **Absent**; the record itself proves `fresh_issue == 0` and `ofs > 0` (pure-OFS cap 60 + `fresh_share` 0/3 + seller criteria UNKNOWN) | — | — | `issue.fresh_issue`, `issue.ofs` (both in `reporting_unit`); `fresh_share_pct = fresh/(fresh+ofs)` | Manual, `MANUAL_ENTRY` | **VERIFIED at record level; source pending** | The classification is not in doubt; the *amounts* are |
| C `ofs_seller_type` | Seller: Harish Narshi Dharamshi, 8,983,700 shares | **Absent** | — | — | `issue.ofs_sellers[].{name,type,pre_issue_shares,shares_sold,holding_pct_pre_issue,source_id}`; `additionalProperties: false` | Not extractable | **UNRESOLVED** | Seller identity and promoter status are RHP facts |
| C `ofs_seller_type` | Seller: Kusum Harish Dharamshi, 17,300,800 shares | **Absent** | — | — | same | Not extractable | **UNRESOLVED** | as above |
| C `ofs_seller_type` | Aggregate 26,284,500 shares | Absent | — | **15.000 %** of the implied 175,228,782 post-issue shares | `ofs_seller_bucket` needs only `type` + `shares_sold` | Not extractable | **UNRESOLVED (internally consistent)** | A 15.000 % OFS is a strong indication the share counts are right |
| C `promoter_ofs_pct` | Harish proceeds ₹243.16 cr at ₹271 | **Absent** | — | **₹243.46 cr** = 8,983,700 × 271 | Proceeds are **not** a schema field (`$defs.seller`) | Not representable | **CONTRADICTED** | −₹0.298 cr vs its own share count |
| C `promoter_ofs_pct` | Kusum proceeds ₹469.15 cr at ₹271 | **Absent** | — | **₹468.85 cr** = 17,300,800 × 271 | same | Not representable | **CONTRADICTED** | +₹0.298 cr; the two errors cancel exactly (§D.2) |
| C (cap) | Aggregate proceeds ≈ ₹712.31 cr | Absent | — | **₹712.31 cr** = 26,284,500 × 271; record's `ofs` 71,231 lakh = ₹712.31 cr | `issue.ofs` in lakh (the evaluated snapshot's unit) | Manual, consistent | **VERIFIED (arithmetic)** | The aggregator's ₹712.13 cr is a 0.03 % outlier (§D.2) |
| C `use_of_proceeds` | (company proceeds) | — | — | nil by construction | `zero_if: pure_ofs` — a pure OFS raises nothing for the company (`config` C) | Scored 0 by configuration | **VERIFIED (contract)** | The engine *does* distinguish company from selling-shareholder proceeds: `fresh_issue` vs `ofs`, and `_issuer_pb` adds `fresh_issue` to equity |

### B.4 Module D / K1 — auditor and going concern

| Module / criterion | Proposed value or claim | Primary source | Source value | Independently calculated value | Engine field / contract | Evidence-flow status | Final disposition | Reason and next action |
|---|---|---|---|---|---|---|---|---|
| D `auditor`, K1 | Auditor opinion unmodified/clean | **Absent** — no auditor's report | — | — | `governance.auditor_opinion` ∈ {unqualified, qualified, adverse, disclaimer, emphasis_of_matter}; emitted **only from positive opinion language** (`sections.py:1263-1370`) | Not extractable | **UNRESOLVED** | Needs the examination report's conclusion page |
| D `auditor` | (implicit) clean_reputed 2/2 | — | — | requires `auditor_changed_3y` known and `auditor_reputed` True | `_auditor_bucket` (`derived.py:1428-1486`) | `auditor_reputed` comes from a **hard-coded reputed-firm list** (`sections.py:1404-1417`); `auditor_changed_3y` and `repeated_eom` are emitted as constant `False` (§C.5) | **UNRESOLVED / defaulted** | No filing evidence establishes either boolean; see §C.5 and decision D-4 |
| K1 | Going-concern uncertainty none / CLEAR | **Absent** | — | — | `going_concern_uncertainty` is `None` unless positive disclosure language is found; absence is **never** `False` | Not extractable | **CONTRADICTED (as CLEAR)** | An unmodified opinion is not proof; and K1's `any` also needs `net_worth_latest`. See §C.1 |
| K1 | Net worth positive (implied) | Absent | — | positive on every candidate figure (₹375.93 / ₹399.87 cr) | `net_worth_latest < 0` is the third K1 leaf | Arithmetic only | **UNRESOLVED** | Positive but unverified |

### B.5 K5 — contingent liabilities

| Module / criterion | Proposed value or claim | Primary source | Source value | Independently calculated value | Engine field / contract | Evidence-flow status | Final disposition | Reason and next action |
|---|---|---|---|---|---|---|---|---|
| K5 | Bank guarantees ≈ ₹58.50 cr, secured on fixed deposits | **Absent** | — | — | `financials.contingent_liabilities` — the extractor reads **only** the "claims/disputed liabilities" row (`_CL_CLAIMS_LABEL`, `financial_tables.py:568`) | No category for guarantees | **UNRESOLVED** | Category mismatch: a BG is not the claims row; see §C.2 |
| K5 | Unfulfilled EPCG export obligations ≈ ₹31.43 cr | **Absent** | — | — | same | No category | **UNRESOLVED** | A contractual export obligation is not necessarily a contingent liability |
| K5 | Net worth > ₹1,000 cr | **Absent** | — | **₹399.87 cr** from NAV/share; ≈ ₹374–376 cr for the prior year | `net_worth_latest` | Arithmetic only | **CONTRADICTED** | §D.3 |
| K5 | "Contingent liabilities are quantified; K5 can be cleared" | Absent | — | BG + EPCG = ₹89.93 cr = **22.5 %** of ₹399.87 cr (below the 50 % trigger) | K5 = `pct > 50` **OR** `contingent_liab_unquantified` (`config` K5); the flag is tri-state, never coerced (`derived.py:2252-2270`) | Neither leaf established | **CONTRADICTED (as a conclusion)** | Two disclosed lines cannot establish that *all* exposures are quantified; see §C.2 |

### B.6 Related-party transactions

| Module / criterion | Proposed value or claim | Primary source | Source value | Independently calculated value | Engine field / contract | Evidence-flow status | Final disposition | Reason and next action |
|---|---|---|---|---|---|---|---|---|
| D `rpt` | RPTs ≈ 33.10 % of FY2026 revenue | **Absent** — no RPT note | — | 33.10 % × 489.28 = ₹161.95 cr implied numerator | `governance.rpt_pct_revenue`; approved definition = **related-party sales/services income ÷ revenue from operations, latest audited FY** (`builder.py:361-380`) | Not extractable | **UNRESOLVED** | If 33.10 % is gross RPT turnover it is **not** the approved metric; it would score 0/3 (`<5 → 3`, `≤15 → 1`, else 0) |
| K6 | (implied) RPT-driven growth | Absent | — | — | `rpt_pct_of_revenue_growth` = change in that share between the latest two FYs, in pp (`builder.py:395-450`) | Not formable | **UNRESOLVED** | Needs two comparable FYs of the same numerator and denominator |
| — | "Transactions were at arm's length" | Absent | — | — | **no field**; nothing consumes it | n/a | **NOT APPLICABLE** | A disclosure, a board approval or an auditor certificate is not evidence of pricing; it cannot be scored and must not be recorded as a verified fact |

---

## C. K1 and K5 deep dive

### C.1 K1 — auditor opinion, going concern, negative net worth

**Contract** (`config/ipo-config.v1.5.0.json`, knockout K1): three required leaves, combined with
an `any`:

1. `auditor_opinion ∈ {qualified, adverse, disclaimer}`;
2. `going_concern_uncertainty` is true;
3. `net_worth_latest < 0`.

`required` means an UNKNOWN leaf prevents a CLEAR resolution (Kleene logic: `any(F, U, F) = U`).
This is why the Jio record — unmodified opinion, positive net worth, no going-concern paragraph —
is still **UNVERIFIED** rather than CLEAR.

**What the engine actually needs to clear K1:** `auditor_opinion` established as
`unqualified` (or `emphasis_of_matter`), `going_concern_uncertainty` established as **`False`**,
and `net_worth_latest` established as positive. The middle value is the blocker:
`extract_governance` emits `going_concern_uncertainty` **only** when positive uncertainty
language is present; it is never emitted as `False` (`sections.py:1370-1420` region, and the
regression `tests/test_auditor_evidence_section.py::test_absent_going_concern_disclosure_is_never_emitted_as_false`).

So the proposed disposition "unmodified opinion → going concern none/CLEAR" is **wrong in kind**,
not merely unverified: an unmodified opinion addresses the financial statements' fair
presentation; going-concern uncertainty is a separate, explicitly reported matter. Absence of a
going-concern paragraph is evidence *about the document*, not a scoreable `False`, because the
engine has no negative-confirmation rule that would let it treat "no paragraph in a complete,
verified report" as a determination.

Even if the HD Fire report were supplied and stated an unmodified opinion, K1 would remain
UNVERIFIED until a governed negative-confirmation rule exists (the same decision flagged for
Jio). **Decision required (D-1):** adopt, or refuse, a rule of the form "complete examination
report + explicit conclusion + no going-concern section + no emphasis of matter ⇒
`going_concern_uncertainty = False`". Until then, K1 stays UNVERIFIED for any filing without a
positive going-concern disclosure.

Two further points specific to the HD Fire record:

- The recorded K1 is UNVERIFIED on **all three** leaves, because `auditor_opinion` and net worth
  are UNKNOWN in that evaluation (§2.8 of the 2026-10-19 reconciliation).
- If the opinion leaf is ever established, note that D `auditor` (2 points) *and* the K1
  disposition can be reached through defaults rather than evidence — see §C.5.
- `promoter_pledge_pct = 0.0` and `sebi_ed_action_active = False` are **builder defaults**, not
  evidence (known finding, unchanged; in this record `litigation_bucket` was instead a *negative*
  extracted bucket, `criminal_or_regulatory`, which is what keeps D `litigation` at 0/4). K2 CLEAR
  rests on those two defaults.

### C.2 K5 — contingent liabilities

**Contract:** `contingent_liab_pct_networth > 50` **or** `contingent_liab_unquantified` is true.
Both leaves must be resolvable for a CLEAR; the flag is tri-state.

**What the extractor actually captures:** `_extract_contingent_liabilities`
(`financial_tables.py:575-673`) anchors on a note heading matching
`contingent liabilities (and commitments)?`, locates a row matching
`claims? (/|and)? disputed liabilit`, reads the period header **30 lines above that row**, and
takes the latest **31 March** column. It fails closed on a width mismatch or an absent header.
Everything else in the note — guarantees, letters of comfort, EPCG export obligations, statutory
demands, excise/customs matters — is **outside** the numerator.

That is a definitional boundary, not an implementation accident, but it is **not documented in
the schema**: `financials.contingent_liabilities` is a bare `$ref: num` with no description, so
the field's meaning exists only in code and in the K5 label ("Contingent liabilities >50 % of net
worth"). **Decision required (D-2):** define whether the K5 numerator is (a) the
claims/disputed-liabilities line (current behaviour), (b) the total of all disclosed contingent
liabilities, or (c) a defined subset with anti-double-counting rules. Option (b)/(c) is a
semantic change with an extraction rewrite and a direct knockout effect; it is not applied here.

Consequences for the Gemini claim:

- ₹58.50 cr of bank guarantees secured by fixed deposits and ₹31.43 cr of unfulfilled EPCG
  obligations are **category-mismatched** to the current extractor even if the amounts are
  correct. Under Ind AS, financial guarantees are in the scope of Ind AS 109 and may be
  *recognised* (a liability) rather than disclosed as contingent; an unfulfilled export
  obligation is a contractual commitment. Whether either belongs in a contingent-liability total
  is exactly what D-2 must settle.
- The materiality leaf, if those were the whole population: 89.93 / 399.87 = **22.5 %**, below
  the 50 % trigger. So the *pct* leaf would be False — but only after D-2 defines the numerator.
- The unquantified leaf cannot be set from two lines. Clearing it requires evidence that **no**
  disclosed exposure is unquantified across the whole note (and that no exposure is omitted).
  Setting `contingent_liabilities_unquantified = false` from two quantified bullets would be
  precisely the "all contingent liabilities are quantified because selected exposures are"
  inference the task forbids.

**Net:** the engine **cannot** legitimately clear K5 for HD Fire on the evidence described. Even
with the RHP in hand it would need a defined numerator (D-2) plus a complete note review.

### C.3 Why K3 and K4 deserve the same caution

- **K3** = `ofs_share_pct > 80` **and** `profit_declining`. HD Fire's `ofs_share_pct` is 100 from
  the pure-OFS structure, so K3 turns entirely on `profit_declining` = "latest PAT < prior PAT,
  or 2-year PAT CAGR < 0" (`derived.py:1738-1759`). A single FY2026 PAT cannot resolve it, and
  guessing a favourable trend would either clear a triggered knockout or trigger a clear one.
  **K3 must stay UNVERIFIED until 2–3 FYs of PAT are supplied.**
- **K4** = `pe_promoter_sold_pct_combined > 50` **and** (`promoter_full_exit` or
  `promoter_post_pct < 20`) **and** (`profit_declining` or `roce < 10` or `cfo_pat < 0.5`).
  Its current CLEAR in the HD Fire record rests on a fabricated `promoter_post_pct = 100`
  (§C.4). Note that even the corrected 85.0 % keeps the second conjunct false, so K4 would
  remain CLEAR — but for a defensible reason rather than an artefact.

### C.4 The promoter-holding defect (engine, confirmed)

`SectionExtractor.extract_capital_structure` (`sections.py:676-733`) falls back to a
`Total (A)` / `Total (B)` scan when the primary "Shareholding of our Promoters and Promoter
Group" anchor does not match. Three defects compound:

| # | Code | Effect |
|---|---|---|
| 1 | `re.search(r'Total\s*\(\s*A\s*\)', l)` (`sections.py:681`, `717`) is a **prefix** match | the `Total (A)+(B)+(C)` summary row is read as the promoter total; because the loop keeps assigning, the **last** match wins and overwrites a genuine `Total (A)` row |
| 2 | `pre_pct = round(tot_a_pre + (tot_b_pre or 0.0), 2)` (`sections.py:693`) | adds the **public** category to the promoter category; under the ICDR format this reconstructs 100 % by construction |
| 3 | the post-issue scan appends `cap_lines[idx+1:idx+3]` to the matched row (`sections.py:717-733`) | percentages from the **next** category leak into the promoter calculation |

Demonstrated (executed, §F.1):

| Input | Correct | Extractor |
|---|---|---|
| Jio p.107 shape (promoter row + public row + `Total (A)+(B)+(C)`) | pre 66.43 %, post `[●]` | **100.0 / 100.0** |
| Standalone `Total (A)` 66.43 / `Total (B)` 33.57 | pre 66.43 %, post 65.0 % | **100.0 / 35.0** |
| Standalone `Total (A)` 66.43 + `Total (A)+(B)+(C)` 100.00 | pre 66.43 % | **100.0 / 100.0** |
| Standalone `Total (A)` only | pre 66.43 %, post 65.0 % | 66.43 / 65.0 (correct) |

Live confirmation on the committed Jio RHP (re-executed this pass): the extractor returns
`capital_structure.promoter_pre_pct = 100.0` and `promoter_post_pct = 100.0`, attributed to
PDF page 80 (the anchor page it matched, not the table page), while the shareholding tables on
PDF pp. 107–109 state Promoter & Promoter Group **66.43 %** pre-issue (public 33.57 %) and print
the post-issue percentages as `[●]`.

**Why it was not corrected in this pass:** any correction changes the scored canonical input for
filings of this shape — a missing-value/semantic decision. §F.3 quantifies the two candidate
repairs. The defect is pinned by `tests/test_promoter_holding_extraction.py`
(1 passed, 3 `xfail(strict=True)`) so that a future correction flips them to XPASS and forces the
decision into the open.

---

### C.5 Auditor tenure and repeated-EOM defaults (engine, confirmed)

`extract_governance` step 1b (`sections.py:1385-1475`) runs only when an auditor **name** is
found by one of two regexes. When it runs, it appends:

| Field | Value | Quote emitted | Evidence |
|---|---|---|---|
| `governance.auditor_changed_3y` | **constant `False`** — assigned before the loop and reassigned to `False` inside it (`sections.py:1420-1450`); no branch can produce `True` | "Auditor <name> unchanged across audited fiscal years" | none: the sentence is synthesised (`quote_is_processing=True`) |
| `governance.auditor_reputed` | `any(firm in auditor_name.lower() for firm in [...11 firms...])` (`sections.py:1404-1417`) | "Auditor: <name>, reputed network: <bool>" | a hard-coded list, i.e. a curated governance input, not a filing fact |
| `governance.repeated_eom` | **constant `False`** (`sections.py:1464-1475`) | "No repeated Emphasis of Matter noted" | none, and the quote is **not** marked as processing — it reads as a verbatim filing sentence |

Executed probe (unqualified opinion + `audited by Deloitte Haskins & Sells LLP`, **no** tenure
sentence and **no** EOM discussion):

```
governance.auditor_opinion      = 'unqualified'
governance.auditor_changed_3y   = False   | quote='Auditor Deloitte Haskins & Sells LLP unchanged across audited fiscal y…'
governance.auditor_reputed      = True    | quote='Auditor: Deloitte Haskins & Sells LLP, reputed network: True'
governance.repeated_eom         = False   | quote='No repeated Emphasis of Matter noted'
```

That combination resolves `_auditor_bucket` to **`clean_reputed` 2/2** — two points, and the
best band, produced by two constants and a firm-name lookup. The `repeated_eom = False` default
also suppresses the `unstable_or_repeated_eom` band that a genuinely repeated emphasis of matter
should produce.

Relationship to HD Fire: the record shows D `auditor` **UNKNOWN** and `auditor_opinion`
**UNKNOWN**, which is consistent with step 1b not firing (no name matched) — so these particular
points were *not* wrongly awarded in the 7/100. The defect matters for the re-run: if the HD
Fire examination report yields an auditor name from the reputed list, D `auditor` would score
2/2 on `changed_3y = False` and `repeated_eom = False`, neither of which the RHP establishes.

**Not corrected**, for the same reason as §C.4: setting these to `None` when the evidence is
absent changes a scored input. Pinned by `tests/test_auditor_tenure_defaults.py`
(2 passed, 2 `xfail(strict=True)`).
**Decision required (D-4):** either (a) emit `None` unless the tenure/EOM text is actually
matched, or (b) accept the constants as governed assumptions and record them as such. Option (a)
is the fail-closed behaviour the engine's own K1 principle already requires.

## D. Metric discrepancies

### D.1 PAT margin: 23.12 % versus 23.87 %

- 116.79 / 489.28 = **23.870 %** (revenue from operations).
- 116.79 / **505.12** = **23.121 %** → the 23.12 % figure is 116.79 ÷ total income, i.e. revenue
  plus other income of ≈ ₹15.84 cr.
- The engine's margin is `numerator / revenue` for **both** EBITDA and PAT
  (`derived.py:274-283`), and `margin_trend` compares two years of that series. Total income has
  no place in the contract; introducing it would silently change the metric definition.
- **Disposition: CONTRADICTED as an engine input.** The engine-consistent value is **23.87 %**,
  and even that is only an arithmetic derivation until the RHP is read.

### D.2 Seller-level OFS proceeds versus share counts

| Seller | Shares | × ₹271 | Claimed | Difference |
|---|---:|---:|---:|---:|
| Harish Narshi Dharamshi | 8,983,700 | **₹243.4583 cr** | ₹243.16 cr | **−₹0.2983 cr** |
| Kusum Harish Dharamshi | 17,300,800 | **₹468.8517 cr** | ₹469.15 cr | **+₹0.2983 cr** |
| Total | 26,284,500 | **₹712.3100 cr** | ₹712.31 cr | 0 |

- The two individual amounts are wrong by **equal and opposite** ₹0.298 cr, so the aggregate is
  right by construction. The share of the offer (34.179 % / 65.821 %) does not match the claimed
  amount split (34.137 % / 65.863 %). This is the signature of a **plug**: the totals were fixed
  first and the components adjusted to add up.
- A third, unrelated discrepancy: the repository's own GMP captures (InvestorGain and PapsDigital,
  both 2026-10-15) report an **issue size of ₹712.13 cr**, not 712.31 — i.e. 71,213 lakh, which is
  a digit transposition of the operator's recorded 71,231 lakh. ₹712.13 cr ÷ ₹271 =
  26,277,859.8 shares, not an integer, so the aggregator figure is itself a rounding/derivation.
  The share-count arithmetic (26,284,500 × 271 = 712.30995 cr) and the exact **15.000 %** OFS
  ratio both favour **712.31 cr / 71,231 lakh**.
- **Disposition:** aggregate **VERIFIED (arithmetic)**; individual amounts **CONTRADICTED**;
  the 712.13 vs 712.31 conflict **UNRESOLVED** pending the RHP's offer table. Nothing was
  silently changed: the evaluated snapshot's `ofs = 71,231` (lakh) stands as a `MANUAL_ENTRY`
  with `verified` unset.
- Note also that individual **proceeds are not a schema field** (`$defs.seller` has
  `additionalProperties: false` and no `amount`), so they can never enter the evaluation; only
  `shares_sold` and `pre_issue_shares` do.

### D.3 Net worth: "> ₹1,000 cr" versus "≈ ₹375.93 cr"

The two claims are both wrong for FY2026, and the arithmetic says by how much:

| Anchor | Calculation | Implied FY2026 net worth |
|---|---|---|
| NAV per share ₹22.82 × 17.5229 cr shares | 22.82 × 175,228,782 / 10⁷ | **₹399.87 cr** |
| Implied market cap ₹4,748.7 cr ÷ P/B 11.9 | 4,748.70 / 11.876 | ₹399.87 cr (same anchor) |
| ROE 30.17 % with PAT ₹116.79 cr | avg NW = 116.79/0.3017 = ₹387.11 cr → prior = 2×387.11 − 399.87 | **₹374.34 cr** prior year |
| Claimed secondary figure ₹375.93 cr | — | consistent with **FY2025**, not FY2026 |
| Gemini "> ₹1,000 cr" | — | would require NAV/share ≈ ₹57.06 |

- "> ₹1,000 cr" is **CONTRADICTED** by the company's own NAV/share and by any consistent
  ROE/NAV/EPS set. It is also inconsistent with the ₹89.93 cr BG+EPCG being 22.5 % of net worth
  (it would be 9.0 % of ₹1,000 cr) — the materiality story changes with the denominator, which is
  why K5 cannot be argued from a net-worth figure that has not been established.
- ₹375.93 cr is **plausibly FY2025** and therefore **not** the `net_worth_latest` the engine
  consumes (latest full FY). Marked **UNRESOLVED**, with the period question flagged.
- Also note the definitional boundary already recorded for Jio: the issuer's own "net worth"
  (ICDR) may exclude OCI, so the RHP's own definition must be read before the figure is entered.

### D.4 Other valuation, period and cash-flow inconsistencies

| # | Inconsistency | Detail | Disposition |
|---|---|---|---|
| 1 | ROCE 40.33 % vs operating EBITDA ₹150.46 cr | At capital employed ≈ ₹399.9 cr (debt-free), ROCE 40.33 % implies **EBIT ≈ ₹161.3 cr**, which exceeds the operating EBITDA. Only reconcilable if the ROCE numerator includes non-operating income or capital employed is defined differently (e.g. excluding cash). | **UNRESOLVED** — read the RHP's ROCE definition and numerator; do not enter 40.33 % as `disclosed_roce_pct` until then |
| 2 | CFO/PAT 0.79× vs cumulative contract | The engine sums CFO and PAT over all FYs; a one-year ratio is a different metric. With only FY2026 available, `cfo_pat_cumulative` must stay UNKNOWN. | **CONTRADICTED as contract input** |
| 3 | EPS 6.66 vs 6.665 | 116.79 cr / 175,228,782 = 6.665; the engine derives and rounds to 2 dp. Immaterial, but the disclosed diluted EPS must be cross-checked against the RHP's own EPS table (which may use a different share count). | **VERIFIED within rounding** |
| 4 | Issue size ₹712.13 cr (aggregator) vs ₹712.31 cr (shares × price) | 0.03 % apart; neither exactly reproduces the other. | **UNRESOLVED** |
| 5 | Peer median P/E 63.0× | Feeds an 8-point criterion; no peer identity, no valuation date, no source. A 63× median for "engineering peers" is implausible on its face. | **UNRESOLVED** — must not be entered |
| 6 | Price band "₹271 – ₹271" | A single-price band; `price_band_low == price_band_high` is schema-valid but must be confirmed from the RHP, not an aggregator. | **UNRESOLVED** |

---

## E. Engine data-flow findings

### E.1 The path every proposed field must travel

```
PDF filing
  → SectionExtractor / FinancialTableExtractor        (extraction)
  → RawExtraction(field_path, value, page, quote)     (evidence, with provenance)
  → CanonicalInputBuilder._build_*                    (mapping)
  → build_canonical_input + unit normalisation        (INR crore, canonical_input.py:305-340)
  → enrichment_engine derivations                     (post-issue EPS, promoter post %)
  → derived.py @metric registry                       (criterion resolution)
  → scoring.py                                        (module points, knockouts, penalties)
  → EvaluationRecord + immutability store             (persistence)
```

A source extraction is **not** canonical population, and canonical population is **not** criterion
resolution. The three stages fail independently, which is why this report separates them.

### E.2 Field-by-field contract map

| Proposed field | Canonical path | Type / semantics | Produced by | Consumed by | Missing ⇒ |
|---|---|---|---|---|---|
| Revenue / EBITDA / PAT / CFO / borrowings / cash / net worth / interest | `financials.periods[].*` | number in `reporting_unit` (min 3, max 6 periods, oldest first) | `FinancialTableExtractor` | A, B, D, K1, K3, K4, K5 | UNKNOWN criterion |
| Contingent liabilities | `financials.contingent_liabilities` | number, `reporting_unit` | `_extract_contingent_liabilities` (claims row only) | K5 | UNKNOWN |
| Unquantified flag | `financials.contingent_liabilities_unquantified` | `boolean|null` | positive-disclosure scan only | K5 | UNKNOWN |
| Auditor opinion | `governance.auditor_opinion` | enum | `extract_governance` (positive language only) | D `auditor`, K1 | UNKNOWN |
| Going concern | `governance.going_concern_uncertainty` | `bool|null` | positive uncertainty language only | K1 | UNKNOWN |
| Auditor change / repute / EOM | `governance.auditor_changed_3y`, `.auditor_reputed`, `.repeated_eom` | `bool|null` | `sections.py:1385-1475`: repute from a hard-coded firm list; change/`repeated_eom` emitted as constant `False` with synthesised quotes (§C.5) | D `auditor`, `K1` opinion leaf | defaulted, not UNKNOWN — the defect |
| RPT share | `governance.rpt_pct_revenue` | percent | `_derive_rpt_metrics` from transaction rows | D `rpt` | UNKNOWN |
| RPT growth contribution | `governance.rpt_pct_of_revenue_growth` | percentage points | same | K6 | UNKNOWN |
| Issue terms | `issue.price_band_{low,high}`, `lot_size`, `fresh_issue`, `ofs` | numbers; `fresh_issue`/`ofs` in `reporting_unit` | filing extraction → governed manual/enrichment path | C, D, B | `AWAITING_ISSUE_TERMS`, no evaluation |
| Share counts | `issue.{pre,post}_issue_shares`, `fresh_shares` | absolute shares | capital-structure extraction; `post = pre + fresh` when absent | B (market cap), C (dilution) | UNKNOWN |
| EPS | `issue.post_issue_eps` | ₹/share at upper band | filing, else derived from PAT × unit factor ÷ post shares | B `pe_vs_peers`, `peg` | UNKNOWN |
| Sellers | `issue.ofs_sellers[]` | `{name?, type, pre_issue_shares, shares_sold, holding_pct_pre_issue?, source_id?}`, `additionalProperties: false` | manual / enrichment | C `ofs_seller_type`, `promoter_ofs_pct`, K4 | UNKNOWN (never "no promoter sold") |
| Promoter holding | `capital_structure.promoter_{pre,post}_pct` | percent | extraction **or** the defective fallback (§C.4); post also derived in `enrichment_engine.py:1046-1092` | D `promoter_post_holding`, K4 | UNKNOWN |
| Peers | `peers[]` | `{name, pe, pb, ev_ebitda, ps, roe_pct, as_of, listed_years, business_match, source_id}` | `extract_peers` (3 header-anchored layouts) or manual | B | UNKNOWN; schema-violating rows rejected pre-evaluation |
| Business assessments | `business.{industry_cagr_pct, industry_scope, industry_forecast_period, industry_source, moat_rating, visibility_rating, top5_customer_pct, top5_supplier_pct}` | mixed | extraction (CAGR) / Tier-4 analyst | E | UNKNOWN |

### E.3 Validation and provenance

- `validate_peer_records` runs the same JSON schema over `peers` at ingestion
  (`presentation/service.py:1426`), names the peer and field, emits
  `validation/peer_contract/FAILED` and raises before any evaluation or persistence. The
  evaluation-time `enforce_schema` remains the second line.
- Manual issue terms keep `MANUAL_ENTRY` / `SRC-MANUAL-ENTRY`, `verified` unset, and the operator
  explanation; a conflict is a 409 requiring explicit confirmation. Confirmation never becomes
  source verification.
- `EvaluationStore.write` refuses to overwrite; a corrected run must create a new evaluation id.

### E.4 What is genuinely missing versus what is merely unextracted

For HD Fire the distinction cannot be drawn, because **nothing can be extracted without the
filing**. That is the honest state: not "extraction failure", not "mapping gap", but
**source not supplied to this environment**. The prior 2026-10-19 analysis classified the four
Module A gaps as "suspected extraction" on the strength of the Jio evidence; this pass does not
upgrade that to a finding, and the Jio-style recoveries (disclosed ROCE KPI, CFO row label,
borrowings rows, unit detection) remain *candidates* to test the moment the filing is uploaded.

---

## F. Implementation and test results

### F.1 What was executed

| Command | Result |
|---|---|
| `python3 -m venv .venv && ./.venv/bin/pip install -q -r requirements.txt` | ok |
| `PYTHONPATH=engine ./.venv/bin/python -m pytest tests/test_promoter_holding_extraction.py -q` | **1 passed, 3 xfailed** (4.02 s) |
| `PYTHONPATH=engine ./.venv/bin/python -m pytest tests/test_auditor_tenure_defaults.py -q` | **2 passed, 2 xfailed** (0.04 s) |
| `… pytest tests/test_promoter_holding_extraction.py tests/test_rk_fashion_reconciliation.py tests/test_fixture_fallback_isolation.py tests/test_extraction_phase5b.py tests/test_enrichment_engine.py tests/test_acceptance_matrix.py tests/test_jio_evidence_remediation.py tests/test_financial_statement_column_mapping.py tests/test_ofs_nil_binding.py tests/test_peer_row_mapping_and_bounds.py -q` | **134 passed, 3 xfailed**, 3 warnings, 232.80 s |
| Ad-hoc extraction probes against the committed Jio RHP (capital structure, governance, RPT) | outputs quoted in §C.4 / §F.2 |
| Synthetic governance probe (unqualified opinion + auditor name, no tenure or EOM text) | `changed_3y=False`, `reputed=True`, `repeated_eom=False` — quoted in §C.5 |
| `PYTHONPATH=engine ./.venv/bin/python -m pytest -q` (full backend suite) | **1161 passed, 5 xfailed**, 38 warnings, 1618.22 s (baseline 1158 passed + 3 new passing tests and 5 strict-xfail pins) |
| `… pytest tests/test_promoter_holding_extraction.py tests/test_auditor_tenure_defaults.py -q` (re-run on the final tree) | **3 passed, 5 xfailed**, 3.99 s — the full suite was collected before the last docstring/comment edits |
| `git status --short` after the pass | two new test files and this document (untracked) plus the tracker section; `git diff --stat` on tracked paths shows only the tracker — no engine, `config/`, `schema/` or fixture change |

### F.2 Live Jio extraction observed during this pass (context, not a new evaluation)

| Field | Extracted | Filing states |
|---|---|---|
| `capital_structure.promoter_pre_pct` | **100.0** | 66.43 % (p. 107) |
| `capital_structure.promoter_post_pct` | **100.0** | `[●]` (p. 109) — undisclosed |
| `issue.pre_issue_shares` | 8,939,030,830 | 8,939,030,830 (p. 99) |
| `governance.auditor_opinion` | unqualified | examination report conclusion (p. 324) |
| `governance.going_concern_uncertainty` | None | no disclosure; absence not treated as false |
| `governance.rpt_pct_revenue` | 4.3094 | Note 36 totals 63,299 / revenue 1,468,853 |

The RPT rows (`extract_related_party_transactions`) still merge the counterparty of a wrapped
category's first row into the category label (e.g. `'and Other Intangible Assets Parent'`); the
category and amounts are right and the metric does not read counterparty text. Recorded, not
changed (evidence-only).

### F.3 The correction that was *not* applied, and why

Three candidate repairs for §C.4, with their consequences:

| Option | Behaviour | In-repo effect | Assessment |
|---|---|---|---|
| (a) Guard only: `Total (A)` must not match `Total (A)+(B)+(C)`, and drop the A+B sum | Jio → pre UNKNOWN, post UNKNOWN | Jio D `promoter_post_holding` 4 → UNKNOWN: **−4 points** (37 → 33 on a re-run) | Minimal and correct, but it turns a fabricated CLEAR into UNKNOWN and changes a score |
| (b) Parse the promoter row of the shareholding-pattern table | Jio pre = 66.43 %, post = `[●]` → UNKNOWN | same −4 for Jio | More correct, bigger change |
| (c) Derive post-issue holding from pre-issue holding diluted by the issue | Jio 66.43 % × 8,939,030,830 / 9,209,030,830 = **64.48 %**; HD Fire 100 % × (1 − 15.000 %) = **85.0 %** | no score change for either filing | Requires a new derivation rule (a contract decision) |

All three remove the fabrication; only (c) preserves the recorded scores, and only (c) is a
semantic change. **Decision required (D-3):** choose (a), (b) or (c). Because acceptance
criteria forbid introducing a scoring change or a missing-value policy change without authority,
this pass stops at the diagnosis and pins the current behaviour with `xfail(strict=True)` tests.

### F.4 Why no other code change was made

Every other candidate was checked and rejected for the same reason (it would change a governed
contract) or because it was not a defect:

- The peer gate, the NIL-OFS binding, the auditor-opinion resolver and the contingent-liability
  extractor were verified in the previous pass and are covered by 17 + 9 + 9 + 8 executed tests;
  none regressed here.
- The `second_multiple` UNKNOWN message ("no VALID peer multiple is available … Rejected peers:
  none supplied") is imprecise but frozen in `fixtures/vishal_nirmiti/expected_derived.json`;
  changing it would break the golden comparison.
- There is no `amount` field in the seller schema, so seller proceeds cannot be represented;
  adding one would be a contract change with no scoring effect — not justified.
- The auditor tenure / repeated-EOM defect (§C.5) is the same kind: the fail-closed correction
  is one line (`None` instead of `False`), but it removes 2 scored points wherever it fires, so
  it is a missing-value decision (D-4), not a mechanical fix.

---

## G. Explicit non-changes

| Item | State |
|---|---|
| Scoring formulas, module weights, band thresholds, knockout semantics, penalty rules | **unchanged** (`config/`, `schema/` diffs empty) |
| Golden fixture and golden result hash `e84f8bc0…` | **unchanged**; the 134-test battery includes `test_rk_fashion_reconciliation`, `test_fixture_fallback_isolation`, `test_acceptance_matrix` |
| Historical evaluations (HD Fire `551a7eab…`, Jio `ce7bfe8e…` / `7857589a…`) | **not touched, not re-run, not rewritten** |
| `main` | `01ba66c`, untouched |
| PR #6 | **OPEN / UNMERGED**, head `e05c0ef`, `mergedAt: null` — not merged, not closed, not moved |
| The 7/100 HD Fire score | **not changed**; the record is not reproducible in this environment and was not altered |
| The evaluated HD Fire snapshot | not re-created; the operator's `MANUAL_ENTRY` terms and the confirmed OFS override stand as recorded |

---

## H. Next actions (each with its blocker)

| # | Action | Blocker / prerequisite |
|---|---|---|
| 1 | Upload the **HD Fire Protect RHP** (or the restated financial statements + auditor report + notes extract) through the established evidence workflow | The document does not exist in this repository and cannot be fetched (egress blocked). Everything in §B is blocked on this. |
| 2 | Re-run the evaluation at the current commit as a **new** record with its own provenance | Requires (1) and the operator's re-entry of the issue terms |
| 3 | Populate Module A from the restated P&L/balance sheet/cash-flow: 3 FYs of revenue, EBITDA, PAT, CFO, borrowings, cash, finance cost, net worth | Requires (1); must be the FY columns, not the interim stub; `margin_trend` and `cfo_pat_cumulative` need the whole window |
| 4 | Resolve the PAT margin denominator | Requires the RHP's own ratio table; the engine uses revenue (23.87 %), not total income (23.12 %) |
| 5 | Verify ROCE 40.33 % (definition + numerator) | Requires the RHP's "Basis for Issue Price" and the ROCE note; the current figures are internally inconsistent with EBITDA (§D.4 #1) |
| 6 | Populate `issue.ofs_sellers` (name, type, shares_sold, **pre_issue_shares**, source) | Requires the RHP's "Offer for Sale" seller table; proceeds are not representable and `pre_issue_shares` is not in the claim set |
| 7 | Enter the issue terms from the RHP price-band page | Aggregators agree on ₹271 / lot 55 but are secondary; the ₹712.13 vs ₹712.31 conflict needs the RHP offer table |
| 8 | Establish the peer set (names, P/E, P/B or EV/EBITDA, valuation date, source) | Requires the RHP's peer-comparison table; **the 63.0× median must not be used** until then |
| 9 | Establish `auditor_opinion` | Requires the examination report; the extractor accepts only positive opinion language |
| 10 | Clear K1 | **Decision D-1** (going-concern negative-confirmation rule) + (9) + net worth |
| 11 | Clear K5 | **Decision D-2** (definition of the K5 numerator) + a complete contingent-liability note + `unquantified` determination |
| 12 | Reproduce or set aside the HD Fire **record** (score, penalty attribution, hash) | The record lives in the operator's Windows store; only the documented values are available here |
| 13 | Choose D-3 (a/b/c) for the promoter-holding defect and remove the `xfail` markers | Governed decision; changes Jio under (a)/(b), preserves both scores under (c) |
| 14 | Choose D-4 (a/b) for the auditor tenure / repeated-EOM defaults and remove the `xfail` markers | Governed decision; option (a) removes 2 defaulted points wherever it fires |

Not an action, deliberately: nothing in this report improves the HD Fire score. The score can only
move when the filing is supplied and its values pass the existing contracts.

---

## I. Publication

- **Branch:** `arena/ae4d04e8-ipo-screening-engine` (this session's branch only).
- **Changes in this pass:** `docs/investigation/HD-FIRE-RHP-EVIDENCE-RECONCILIATION-2026-10-20.md`
  (this file), `tests/test_promoter_holding_extraction.py` (new),
  `tests/test_auditor_tenure_defaults.py` (new), and a tracker section. No engine, config, schema
  or fixture change.
- **Implementation commit:** `bdab685a05a96a7531dc9a3f5b218b8c45ebfbfb` on
  `arena/ae4d04e8-ipo-screening-engine`, pushed and remote-verified (`git ls-remote
  origin refs/heads/arena/ae4d04e8-ipo-screening-engine` returned the same SHA). 4 files, 918
  insertions, 0 deletions; `config/`, `schema/` and `fixtures/` untouched.
- **Publication amendment:** the commit that records this SHA in the tracker is the branch tip and
  a child of `bdab685`; `git log` on the pushed branch shows both. It changes only this document
  and the tracker.
- **Tracker:** `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`, section
  "HD Fire Protect — RHP evidence reconciliation — 2026-10-20".
- **Remaining Windows-only acceptance:** the HD Fire RHP, the evaluation record `…551a7eab`, its
  penalty rows and its canonical issue block. None is claimed as inspected.
