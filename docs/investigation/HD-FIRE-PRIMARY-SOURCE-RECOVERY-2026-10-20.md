# HD Fire Protect Limited — primary-source recovery, evidence reconciliation and acceptance

**Date:** 2026-10-20 (Asia/Calcutta)
**Branch:** `arena/ae4d04e8-ipo-screening-engine`
**Starting commit:** `62bd22ba007663b9f01ae48e00a4fecb90054b6d` (remote-verified at the start of this pass)
**`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094` — untouched
**PR #6:** OPEN / UNMERGED, head `e05c0ef`, base `arena/573e69a4`
**Historical record under review:** `HD-FIRE-PROTECT-LIMITED-20261019-123134Z-final-551a7eab` (7/100)

This pass closes the evidence blocker that every earlier HD Fire pass reported. The filing
is now retrievable **as text** through the page-fetch path even though the sandbox itself
still has no network egress. That changes the disposition of 25 of the 44 field rows and
establishes, from the filing's own numbers, the exact origin of the record's impossible
`promoter_post_pct = 100 %`.

It does **not** close the pass: the persisted evaluation record is still absent, the
contingent-liability note and peer table are beyond the retrievable page range, and no new
evaluation can be produced through the validated workflow. Those are stated as blockers in
§11, not papered over.

---

## 1. Verified repository and PR state (Phase 1)

| Item | Verified value |
|---|---|
| Branch | `arena/ae4d04e8-ipo-screening-engine` |
| HEAD (local = remote) | `62bd22ba007663b9f01ae48e00a4fecb90054b6d` |
| Worktree | clean at pass start |
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` |
| PR #6 | `state: open`, `merged: false`, `merged_at: null`, head `e05c0ef`, base `arena/573e69a4`, `mergeable: true` |
| D-1 … D-4 | published in `handoff/decisions/A19`…`A22` and implemented at `2ec607c`; tracker and the governance record `docs/investigation/HD-FIRE-JIO-DECISION-GOVERNANCE-2026-10-20.md` present |
| Evidence table | `docs/investigation/HD-FIRE-RHP-EVIDENCE-RECONCILIATION-2026-10-20.md` §B — **44 rows** (14 A, 11 B, 8 C, 5 D/K1, 4 K5, 2 RPT/K6) |
| Previous dispositions | 10 verified · 7 contradicted · 26 unresolved · 1 not applicable |

The worktree was re-provisioned at `main` and was moved to the verified branch tip with
`git fetch origin refs/heads/arena/ae4d04e8-ipo-screening-engine` + `git reset --hard FETCH_HEAD`.
No other branch was created, switched to, or pushed. Nothing was merged, reset or force-pushed.

---

## 2. Primary sources recovered (Phase 2)

### 2.1 What the earlier passes got wrong about retrievability

Earlier passes concluded "egress returns HTTP 000, therefore the filing is unobtainable".
That was true for **the sandbox** (`curl` to `sebi.gov.in`, `bseindia.com`, `iiflcapital.com`
and `hdfire.com` all fail at TLS with `SSL_ERROR_SYSCALL` — re-confirmed this pass), but it
was **not** true for the page-fetch path available to this session, which retrieves and parses
PDF text. The blocker was the retrieval method, not the availability of the document.

### 2.2 Documents actually retrieved

| # | Document | URL | Identity / date | Coverage obtained | Grade |
|---|---|---|---|---|---|
| S1 | **Abridged Prospectus** (memorandum of the RHP) | `https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/HD%20Fire%20Protect%20Limited-Abridged%20Prospectus_p.pdf` | SEBI-hosted; issuer-filed; RHP dated **5 October 2026**; RoC Mumbai-I | **complete** (6/6 chunks) | **PRIMARY** |
| S2 | **Red Herring Prospectus** | `https://www.iiflcapital.com/institutional-equities/Upload/InvestmentBanking/Prospects/HD_Fire_Protect_Limited_-_RHP.pdf` | BRLM-hosted (IIFL Capital); RHP dated **5 October 2026** | **pages 1–30 only** (the fetch tool parses at most 30 pages) | **PRIMARY (partial)** |
| S3 | **BSE anchor-investor allocation notice** | `https://www.bseindia.com/downloads/UploadDocs/Notices/Attach/anchor$44c16db2-a994-4cef-9f86-12721d094ebc.pdf` | Exchange filing dated **12 October 2026**, addressed to BSE and NSE, signed by the Company Secretary | **complete** (2/2 chunks) | **PRIMARY** |

S2 confirms the document identity that S1 summarises (cover page, issuer, CIN
`U29270MH1997PLC107536`, 26,284,500 offer shares, both promoter selling shareholders and their
share counts, statutory auditors **KKC & Associates LLP**, offer dates 13–15 October 2026).
S3 establishes the **cap price of ₹271** as an official exchange filing:
"allocation of 78,64,008 Equity Shares in aggregate, to Anchor Investors at the Anchor Investor
Allocation Price of ₹ 271/- per Equity Share (including share premium of ₹ 266/- per Equity
Share)".

### 2.3 Documents not obtained, and the exact reason

| Document / section | Status | Exact reason |
|---|---|---|
| RHP **pp. 31–450+** — includes "Basis of Offer Price" (p. 122), "Restated Financial Information" (p. 282), the contingent-liability note, the RPT note and the auditor's examination report | **not obtained** | the fetch path parses at most the first 30 pages of a PDF; the sandbox cannot download the file (`curl` → TLS failure), so no local copy exists to parse |
| Final **Prospectus** (post-pricing, the document that must carry the completed post-Offer shareholding table) | **not found** | SEBI's public-issue listing shows only the 5 October 2026 RHP and Abridged Prospectus; no Prospectus for this issue was retrievable |
| Price-band advertisement of 6 October 2026 | **not obtained** | referenced by S3; the advertisement itself was not retrievable. The ₹258 floor therefore remains secondary-sourced (§4) |
| NSE/BSE issue pages | **not obtained** | not retrievable through the page-fetch path in usable form |

**Consequence.** Every fact below is anchored to S1, S2 (pp. 1–30) or S3. Nothing from the
contingent-liability note, the RPT note, the peer-comparison table or the auditors' report is
cited, because none of those pages was read. No page number, note number or quotation is
invented anywhere in this record.

### 2.4 Secondary sources (used only to locate, never as evidence)

Aggregator/research pages agree on a ₹258–271 price band, a 55-share lot, 26,284,500 offered
shares, ₹712.31 crore at the cap and a 100 % → 85 % promoter move. They are recorded as
**secondary** and are not the basis of any disposition. Where a disposition depends only on a
secondary value (the ₹258 floor, the peer median P/E) it is marked UNRESOLVED.

---

## 3. Historical evaluation record (Phase 3)

**The record was not recovered.** Every configured location was checked:

| Location | Method | Result |
|---|---|---|
| Working tree | `grep -rn "551a7eab"` | only investigation documents; no record |
| `build/evaluations/` (default `EvaluationStore` root) | directory listing | **directory does not exist** |
| `evaluations/` | directory listing | absent |
| Full git history, all local refs | `git log --all -S "551a7eab"` | only documents that *describe* the record |
| All **17** remote branches | GitHub trees API per branch, filtered for `551a7eab` / `evaluation.json` | the only hit in every branch is `tests/test_strict_evaluation_json.py` (a test name), never a record |
| GitHub code search | `search/code?q=551a7eab+repo:…` | 0 hits |
| Releases / Actions artifacts | `gh api …/releases`, `…/actions/artifacts` | 0 releases, 0 artifacts |
| PR #6 comments | `issues/6/comments` filtered for `551a7eab` | none |

**Required recovery path.** The record is a store directory named exactly
`HD-FIRE-PROTECT-LIMITED-20261019-123134Z-final-551a7eab` containing the eight artifacts the
store writes (`evaluation.json`, `input.json`, `evidence.json`, `market.json`, `peers.json`,
`result.json`, `evaluation-record.v1.json`, `manifest.json`). It was produced on the Windows
machine whose store root is `build/evaluations` (or `IPO_STORE_ROOT`). Recovery = copy that
directory into this checkout unchanged (or attach the eight files). The `manifest.json` hashes
would then allow an independent integrity check and the stored `input.json` would allow the
7/100 to be recomputed. **Nothing in this pass reconstructs it from prose, and no substitute
record was manufactured.**

---

## 4. The 44-field reconciliation (Phase 4)

Legend — **VERIFIED**: the value matches a retrieved primary-source document (S1/S2/S3), with
the location recorded. **CONTRADICTED**: the arithmetic, the contract or the source contradicts
the claim. **UNRESOLVED**: the primary source was not obtained for that item. **NOT
APPLICABLE**: no engine field consumes it.

`₹ in million` is the source unit; ₹1 crore = ₹10 million throughout. "S1 §6" is the
"Summary of Restated Financial Information", "S1 §7" the KPI table, "S1 §5" the pre/post-Offer
shareholding table — all in the Abridged Prospectus.

### 4.1 Module A — Financial quality (14 rows)

| # | Field | Proposed value | Source location | Source value | Independent calculation | Disposition |
|---|---|---|---|---|---|---|
| 1 | `revenue_cagr` | FY2024 revenue ₹372.95 cr | S1 §6 | **3,729.53 ₹mn** = ₹372.953 cr | — | **VERIFIED** |
| 2 | `revenue_cagr` | FY2025 revenue ₹432.80 cr | S1 §6 | **4,327.99 ₹mn** = ₹432.799 cr | YoY +16.05 % | **VERIFIED** |
| 3 | `revenue_cagr` | FY2026 revenue ₹489.28 cr | S1 §6 | **4,892.81 ₹mn** = ₹489.281 cr | YoY +13.05 % | **VERIFIED** |
| 4 | `revenue_cagr` | CAGR 14.54 % | S1 §6 (derived) | — | **14.5387 %** = (4,892.81/3,729.53)^½ − 1 | **VERIFIED** |
| 5 | `margin_trend` | FY2026 operating EBITDA ₹150.46 cr | S1 §6, §7 | **1,504.59 ₹mn** = ₹150.459 cr | — | **VERIFIED** |
| 6 | `margin_trend` | EBITDA margin 30.75 % | S1 §7 (disclosed 30.75 %) | 1,504.59 / 4,892.81 | **30.751 %** | **VERIFIED** |
| 7 | `margin_trend` | FY2026 PAT ₹116.79 cr | S1 §6 | **1,167.87 ₹mn** = ₹116.787 cr | EPS 6.66 × 175.23 mn = ₹116.70 cr | **VERIFIED** |
| 8 | `margin_trend` | PAT margin 23.12 % | S1 §7 note (7): *"PAT Margin is calculated as profit after tax (PAT) as a percentage of Total Income"* | 23.12 % is a **total-income** ratio (implies total income ₹505.13 cr) | engine metric = PAT / **revenue** = **23.869 %** | **CONTRADICTED as the engine metric** |
| 9 | `roce` | ROCE 40.33 % | S1 §7 (disclosed 40.33 %) | — | 0.4033 × average capital employed 3,871.9 = EBIT ₹1,561.5 mn | **VERIFIED** |
| 10 | `cfo_quality` | Cash and cash equivalents ₹134.3 cr | not in pp. 1–30 / abridged | — | — | **UNRESOLVED** |
| 11 | `cfo_quality` | FY2026 CFO ₹92.49 cr | S1 §6 | **924.92 ₹mn** = ₹92.492 cr | — | **VERIFIED** |
| 12 | `cfo_quality` | CFO/PAT 0.79× | S1 §6 (three years) | annual FY2026 0.7920 | engine metric is **cumulative**: 2,545.78 / 3,144.25 = **0.8097** | **CONTRADICTED as the engine metric** |
| 13 | `leverage` | Debt-to-equity 0.00× | S1 §6 note (6): *"total borrowings Nil"* in all four columns; *"zero fund-based outstanding borrowings"* | Nil / 3,771.47 | D/E = 0.00 | **VERIFIED (debt)** — finance cost is not disclosed in the retrieved pages, so the engine's `strong` band (which also needs interest cover) stays UNKNOWN |
| 14 | `roce` / `rpt` | Net worth (was ≈ ₹375.93 cr or "> ₹1,000 cr") | S1 §6 | FY2024 3,434.13 · FY2025 3,972.32 · **FY2026 3,771.47** · Q1 FY2027 4,010.20 (₹mn) | FY2026 = **₹377.147 cr** | **VERIFIED — the "> ₹1,000 cr" claim is CONTRADICTED** |

### 4.2 Module B — Valuation (11 rows)

| # | Field | Proposed value | Source location | Source value | Independent calculation | Disposition |
|---|---|---|---|---|---|---|
| 15 | `issue.price_band_high` | Upper price ₹271 | **S3** (anchor allocation at ₹271); S1/S2 print `[●]` because the RHP predates the band | ₹271 per share | — | **VERIFIED** (cap price). The **₹258 floor is secondary-only ⇒ part of §11 blockers |
| 16 | `post_issue_eps` | FY2026 diluted EPS ₹6.66 | S1 §6 | **₹6.66** | 1,167.87 / 175.23 = 6.665 | **VERIFIED** |
| 17 | `pe_vs_peers` | Issue P/E ≈ 40.7× | derived | — | 271 / 6.66 = **40.691** | **VERIFIED** |
| 18 | `pe_vs_peers` | Peer median P/E 63.0× | not retrieved (basis section p. 122) | — | — | **UNRESOLVED** |
| 19 | `pe_vs_peers` | Discount to peers ≈ 35 % | depends on #18 | — | arithmetic −35.41 % is correct | **UNRESOLVED** (denominator unverified) |
| 20 | `second_multiple` | Implied market cap ₹4,748.7 cr | S1 §5 total shares 175,230,000 | — | 271 × 175,230,000 = **₹4,748.733 cr** | **VERIFIED** (the old figure used 175,228,782 implied from rounding) |
| 21 | `second_multiple` | EV/EBITDA ≈ 30.7× | depends on cash | — | debt 0; without cash **31.56×**; with the unverified ₹134.3 cr cash 30.67× | **UNRESOLVED** |
| 22 | `second_multiple` | NAV per share ₹22.82 | S1 §6 | Q1 FY2027 **₹22.82**; FY2026 **₹21.45** | 4,010.20 / 22.82 = 175.7 mn (weighted average, not total shares) | **VERIFIED** — the earlier ₹399.87 cr "net worth" divided Q1 NAV by *total* shares and is withdrawn |
| 23 | `second_multiple` | P/B ≈ 11.9× | derived | — | 4,748.733 / 377.147 = **12.591×** | **CONTRADICTED** (11.876 used the withdrawn ₹399.87 cr) |
| 24 | `peg` | (not claimed) | derived | — | P/E 40.691 ÷ PAT CAGR **15.253 %** = **2.668×** | **VERIFIED (computed)** — the engine scores it 0 (`else`) |
| 25 | `sector_ipo_relative` | (not claimed) | — | — | — | **UNRESOLVED** (no recent same-sector IPO data) |

### 4.3 Module C — Offer structure, OFS and proceeds (8 rows)

| # | Field | Proposed value | Source location | Source value | Independent calculation | Disposition |
|---|---|---|---|---|---|---|
| 26 | `fresh_share` | 100 % OFS, fresh issue nil | S1 cover table (*"SIZE OF FRESH ISSUE: Not applicable"*); S2 p. 1 | 26,284,500 shares, all OFS | fresh share of offer = **0.0 %** | **VERIFIED** |
| 27 | `ofs_seller_type` | Harish Narshi Dharamshi — 8,983,700 | S1 cover table; S2 p. 1 | *"Up to 8,983,700 Equity Shares … Promoter Selling Shareholder"*; pre-issue 98,351,000 (56.13 %) | 8,983,700 / 98,351,000 = 9.13 % of his holding | **VERIFIED** |
| 28 | `ofs_seller_type` | Kusum Harish Dharamshi — 17,300,800 | S1 cover table; S2 p. 1 | *"Up to 17,300,800 Equity Shares … Promoter Selling Shareholder"*; pre-issue 31,240,000 (17.83 %) | 17,300,800 / 31,240,000 = 55.38 % of her holding | **VERIFIED** |
| 29 | `ofs_seller_type` | Aggregate 26,284,500 | S1 cover; S2 p. 1 | 26,284,500 | **15.000 %** of 175,230,000 | **VERIFIED** |
| 30 | `promoter_ofs_pct` | Harish proceeds ₹243.16 cr | derived at ₹271 | — | 8,983,700 × 271 = **₹243.4583 cr** | **CONTRADICTED** (the ₹243.16 cr figure is ₹0.2983 cr low) |
| 31 | `promoter_ofs_pct` | Kusum proceeds ₹469.15 cr | derived at ₹271 | — | 17,300,800 × 271 = **₹468.8517 cr** | **CONTRADICTED** (₹0.2983 cr high — the two errors cancel exactly) |
| 32 | cap | Aggregate ₹712.31 cr | derived | — | 26,284,500 × 271 = **₹712.3100 cr** | **VERIFIED** |
| 33 | `use_of_proceeds` | Company receives nothing | S1 §4 | *"Our Company will not receive any proceeds from the Offer."* | — | **VERIFIED** |

**The ₹0.2983 crore discrepancy is now fully explained**: the aggregate is right, the split was
transposed between the two sellers. The correct split at the cap price is ₹243.4583 cr
(Harish) + ₹468.8517 cr (Kusum) = ₹712.3100 cr. Company proceeds are zero by construction —
the entire amount accrues to the selling shareholders, and the engine already separates
`fresh_issue` from `ofs`.

### 4.4 Module D / K1 — auditor and going concern (5 rows)

| # | Field | Proposed value | Source location | Source value | Disposition |
|---|---|---|---|---|---|
| 34 | `governance.auditor_opinion` | Unmodified / clean | S1 §11 *"Auditor Qualifications"*: *"There are no reservations, qualifications and adverse remarks included by the Statutory Auditors in the Restated Financial Information."*; auditor is KKC & Associates LLP (S2, defined terms, “Auditors”) | no qualification | **VERIFIED** (issuer's explicit statement; the auditors' own report is beyond the retrieved pages) |
| 35 | `auditor_bucket` | clean_reputed 2/2 | — | tenure and EOM are **not** established in the retrieved pages | **UNRESOLVED** — the 2/2 cannot be awarded (D-4) |
| 36 | K1 | Going concern CLEAR | no going-concern language in the retrieved pages | — | **CONTRADICTED as CLEAR** (D-1: absence is UNKNOWN, never a clear) |
| 37 | K1 | Net worth positive | S1 §6 | ₹377.15 cr > 0 | **VERIFIED** |
| 38 | K5 | Bank guarantees ₹58.50 cr | contingent-liability note not retrieved | — | **UNRESOLVED** |

### 4.5 K5 and RPT/K6 (6 rows)

| # | Field | Proposed value | Source | Disposition |
|---|---|---|---|---|
| 39 | K5 | EPCG obligations ₹31.43 cr | note not retrieved | **UNRESOLVED** |
| 40 | K5 | Net worth "> ₹1,000 cr" | contradicted by S1 §6 (₹377.15 cr) | **CONTRADICTED** |
| 41 | K5 | "Contingent liabilities quantified; K5 can be cleared" | no note retrieved; two disclosed lines cannot prove completeness | **CONTRADICTED as a conclusion** |
| 42 | `rpt_pct_revenue` | RPTs ≈ 33.10 % of FY2026 revenue | RPT note not retrieved | **UNRESOLVED** |
| 43 | K6 | RPT-driven growth | requires two FYs of the same numerator | **UNRESOLVED** |
| 44 | — | "Transactions were at arm's length" | no engine field consumes it | **NOT APPLICABLE** |

### 4.6 Counts

| Disposition | Before this pass | After this pass |
|---|---:|---:|
| VERIFIED | 10 | **25** |
| CONTRADICTED | 7 | **8** |
| UNRESOLVED | 26 | **10** |
| NOT APPLICABLE | 1 | **1** |
| **Total** | 44 | **44** |

Rows 19 and 21 moved from "verified arithmetic" to UNRESOLVED because their denominators
(peer median, cash) were never established; that is a stricter, not a looser, reading. Row 23
(P/B) moved to CONTRADICTED on the corrected net worth. Row 3 (FY2026 revenue) moved from
UNRESOLVED to VERIFIED. The remaining 10 unresolved rows are exactly the items that live on
pages the retrieval path could not reach.

---

## 5. Resolved discrepancies (Phase 4 A–E)

**A. Financial quality**
* Revenue CAGR **14.5387 %** — the recorded 2/6 band is exactly right for the source data.
* EBITDA margin **30.751 %** — confirmed against the disclosed KPI.
* **PAT margin**: the RHP's 23.12 % is PAT ÷ **total income** (its own note says so). The
  engine divides by **revenue** → **23.869 %**. The recorded input was a different ratio.
* **ROCE 40.33 %**: no longer an inconsistency. Operating EBITDA (₹150.46 cr) subtracts other
  income and adds back D&A without adding it back for EBIT; disclosed ROCE implies EBIT
  ₹156.15 cr, i.e. other income exceeds D&A by ~₹5.7 cr. Internally coherent.
* **CFO/PAT**: annual FY2026 0.7920; the engine's cumulative metric is **0.8097** (sum CFO
  2,545.78 ÷ sum PAT 3,144.25 over FY2024–FY2026). The two land in different bands
  (>0.8 → 5 points vs ≥0.5 → 3 points), so the basis matters.
* **Leverage**: debt is Nil in every period; finance cost is not in the retrieved pages, so the
  engine returns UNKNOWN rather than the 4-point `strong` band.

**B. Valuation**
* Issue P/E **40.691×** on the source EPS 6.66 and the official ₹271.
* Market cap **₹4,748.733 cr** at 175,230,000 shares (3 shares different from the old implied
  175,228,782).
* **P/B 12.591×**, not 11.876× — the earlier figure used a net worth that has now been
  withdrawn.
* EV/EBITDA cannot be fixed without the cash line: 31.56× (no cash) to 30.67× (₹134.3 cr).
* Peer median P/E, peer eligibility, valuation date and the peer multiple remain
  **UNRESOLVED** — the "Basis of Offer Price" pages were not retrievable.

**C. Offer structure** — fresh 0 %, 26,284,500 shares sold by two promoter selling shareholders,
15.000 % of pre-issue capital, ₹712.3100 cr at ₹271, company proceeds nil. The two seller
proceeds figures were transposed by ±₹0.2983 cr; the aggregate was always right.

**D. Governance and knockouts** — auditor opinion unmodified (S1 §11); going concern not
establishable (UNKNOWN under D-1); contingent liabilities and RPT not retrievable; net worth
₹377.15 cr, so the "> ₹1,000 cr" claim is contradicted; arm's length is not a scorable fact.

**E. Promoter holding** — the decisive finding of this pass:

| Item | Value | Basis |
|---|---|---|
| Promoters — `Total (A)` | 167,035,000 shares · **95.33 %** | S1 §5 |
| Promoter group — `Total (B)` | 8,195,000 shares · **4.67 %** | S1 §5 |
| Total `(A+B+C+D)` | 175,230,000 · 100 % | S1 §5 |
| Post-Offer columns | **`[●]`** at both ends of the band — *"To be filled at the Prospectus stage"* | S1 §5 |
| Pre-issue promoter + promoter group | **100.00 %** | 95.33 + 4.67 |
| Post-issue, **if** the offer is fully subscribed | **85.00 %** | (175,230,000 − 26,284,500) / 175,230,000 |

The 85.00 % is **arithmetic on disclosed share counts**, not a disclosed post-issue percentage.
It is what the engine would legitimately compute only if the filing itself presented it as the
post-issue holding; the RHP does not. The **published parser** therefore returns
`promoter_pre_pct = 100.0`, `promoter_post_pct = None` on this table (test pinned in §7), which
is the correct UNKNOWN. **No 85.0 % is hard-coded, and no diluted pre-issue percentage is
substituted for the post-issue metric.**

---

## 6. Historical score reconciliation (Phase 6)

### 6.1 Why the recorded 100 % existed — proved, not inferred

The pre-fix fallback (at `7754f9b`, before `2ec607c`) took the *last* percentage in the
`Total (A)` window restricted to 10–100 (→ **95.33**) and added the `Total (B)` percentage
restricted to 0–10 (→ **4.67**), emitting **100.00** as the post-issue holding. Re-running that
exact algorithm on the filing's two rows reproduces **100.0**:

```
pre-fix a_pct 95.33  b_pct 4.67  => post_pct 100.0
```

So the record's `promoter_post_pct = 100 %` is the sum of the two **pre-issue** category totals.
This is the strongest possible confirmation of the D-3/A21 correction: the input was not merely
conservative, it was arithmetically impossible for a 100 %-OFS issue.

### 6.2 Is the recorded 7/100 reproducible?

**Not independently, because the record itself is absent** (§3). Its documented decomposition
(A 2 + B 0 + C 3 + D 5 + E 0 + F 0 = 10, one `receivable_days_up` penalty −3, final 7,
available 27 / unknown 73) is internally consistent, and two of its inputs can now be checked
against the source:

| Recorded element | Source check | Result |
|---|---|---|
| A `revenue_cagr` 2/6 | CAGR 14.5387 % matches the `≥8` band | **consistent** |
| D `promoter_post_holding` 4/4 | the 100 % input is the pre-issue A+B sum; the filing discloses no post value | **not supported by the source** |
| D `auditor` (part of D = 5) | opinion unmodified is supported; tenure/EOM are not | **partially supported** |

A fresh run of the corrected extractor would therefore treat `promoter_post_holding` as UNKNOWN
(0/4, +4 unknown), and the historical D score is not reproducible from the source. The
historical record has **not** been edited, re-hashed or superseded.

### 6.3 Non-persisted diagnostic run (not an evaluation)

To see what the current engine does with the **verified** input set, `evaluate()` was run once
with `store=None` — nothing was written, no evaluation id was created, and no record exists as a
result:

| Element | Value |
|---|---|
| Inputs | S1 §6/§7 financials (INR_MILLIONS), S3 cap price 271, 175,230,000 post-issue shares, 0 fresh / ₹71,231 lakh OFS, two promoter sellers, `promoter_pre_pct` 100.0, `promoter_post_pct` null, `auditor_opinion` unqualified, no peers, no market block |
| Module A | **13/25** (revenue 2, margin_trend 1 `volatile`, ROCE 5, CFO 5, leverage UNKNOWN) |
| Module B | 0/20 (available 4; PEG 2.668× → 0; peers UNKNOWN) |
| Module C | 2/15 (pre-IPO placement 2; fresh 0, seller 0, promoter-OFS 20.28 % → 0, lock-in UNKNOWN) |
| Module D | 0/15 (all UNKNOWN — including promoter post-holding) |
| E / F | 0/15 and 0/10 (no industry/market inputs) |
| Result | base 15.0, no penalty applied, pure-OFS cap 60, **15.0/100**, available 39, unknown 61, verdict `INSUFFICIENT_DATA`, confidence Low |

This is **not** a new evaluation and must not be read as one: the floor price is secondary-sourced,
the peer/market/contingent-liability blocks are empty, and it bypasses the ingestion workflow. It
is reported because it shows the score is dominated by missing inputs (61 of 100 points), not by
a difference in scoring semantics.

### 6.4 Was a new evaluation legitimately produced?

**No.** The validated workflow ingests a source document; no copy of the filing can be placed in
this environment (egress blocked, fetch returns text only, first 30 pages), the post-issue
shareholding and the contingent-liability note are not retrievable, and manufacturing a document
or hand-entering values as though they were extracted would destroy provenance. The correct path
is: place the RHP PDF in the Windows store, run ingestion with the environment's normal entry
point, and let the corrected extractor produce a *new* evaluation alongside the untouched
historical one.

---

## 7. Verification of the published fixes against HD Fire (Phase 5)

New file `tests/test_hd_fire_primary_source_extraction.py` (6 tests) pins the published
behaviour on HD Fire's own published shapes:

| Check | Result |
|---|---|
| Pre/post not conflated: A+B summed for **pre**, `[●]` post ⇒ `None` | **pass** |
| Combined `Total (A+B+C+D)` alone fabricates nothing | **pass** |
| Auditor text with no tenure sentence ⇒ no `auditor_changed_3y` (D-4) | **pass** |
| No explicit negative EOM ⇒ no `repeated_eom` (D-4) | **pass** |
| No going-concern paragraph ⇒ no `going_concern_uncertainty` (D-1) | **pass** |
| Litigation default (see §8) | **xfail (strict), 2** |

The test module documents in its docstring that the table is a line-break *reconstruction* of
S1 §5; the values are the published values, and the reconstruction is stated rather than passed
off as the original file.

---

## 8. Newly established defect — requires a decision (D-5), not a silent fix

> **Superseded 2026-10-20 (D-5 implemented).** This section records the defect as it stood
> before the decision. It was resolved under decision **A23**
> (`handoff/decisions/A23-litigation-and-regulatory-negative-defaults.md`); the evidence and
> measured impact are in `docs/investigation/D5-LITIGATION-REGULATORY-DEFAULTS-2026-10-20.md`.
> The two strict xfails named below were replaced by passing assertions of the corrected
> contract. The historical findings in this section are preserved as written, including its
> pre-implementation score estimate; nothing here is rewritten.

Verifying the governance path against HD Fire exposed a **third favourable-default class**, of
the same family as D-1 and D-4 but outside their approved scope:

`SectionExtractor.extract_governance` (`sections.py`, "2. Litigation bucket & SEBI action")
initialises `lit_bucket = "clean"` and `sebi_active = False` **before** the scan and emits both
unconditionally afterwards, whatever the scan found — including when every page in the range is
empty. Consequences:

1. `litigation_bucket = "clean"` scores **4/4** in Module D on the strength of a default.
2. `sebi_ed_action_active = False` is emitted with the quote
   *"No active SEBI or ED regulatory proceedings"* — text that appears nowhere in the source —
   and without `quote_is_processing=True`, so it is presented as a source quotation. That is the
   same fabricated-quotation defect D-4 removed from the auditor fields.
3. The classification regexes look for `criminal proceedings against our promoters`,
   `r.c.c.`, `criminal complaint`, `material civil litigation`, `civil suit`. HD Fire's filing
   reports, in S1 §12, **2 criminal proceedings against Directors (excluding Promoters)** and
   **3 tax proceedings by the Company (₹0.40 million)**, presented as table counts — text the
   regexes cannot see. The engine would therefore call this filing **clean** and award 4/4.

This is not corrected here. Whether "no litigation text found" should mean UNKNOWN, and whether
a criminal proceeding disclosed against a Director forces `criminal_or_regulatory` (the
criterion's own formula says "across promoters, directors and the company"), is a scoring-semantic
decision the current authorisation does not cover. **Decision D-5 required**, with three
sub-questions: (a) absence of evidence ⇒ UNKNOWN rather than `clean`; (b) director-level criminal
proceedings ⇒ `criminal_or_regulatory`; (c) removal of the synthesised SEBI quote. Both defects
are pinned as strict xfails so they cannot be silently fixed or forgotten.

**Score consequence if D-5(a) were adopted:** up to **4 earned and 4 available points** change on
any filing whose litigation pages yield no marker — including HD Fire. No change is made now.

---

## 9. Tests actually executed

| Command | Result |
|---|---|
| `pytest tests/test_hd_fire_primary_source_extraction.py -q` | **4 passed, 2 xfailed** (0.05 s) |


### 9.1 Full suite

`PYTHONPATH=engine:tests ./.venv/bin/python -m pytest tests -q`

| Tree | Result |
|---|---|
| Baseline `62bd22b` (start of pass) | **1192 passed, 0 xfailed**, 38 warnings, 1566.58 s |
| This tree (with the new module) | **1196 passed, 2 xfailed**, 38 warnings, **1095.32 s** |

Delta is exactly the new module: **4 passed** (the D-1/D-3/D-4 checks on HD Fire's own table
and auditor text) and **2 xfailed** (the strict pins for the D-5 litigation/SEBI defaults).
No pre-existing test changed state. The 38 warnings are the same pre-existing Starlette
deprecation and unregistered `slow`-mark warnings as at the baseline.

---

## 10. Protected artifacts and non-changes

* `config/`, `schema/`, `fixtures/`: **diff empty**. The golden result hash is asserted by the
  golden tests inside the full suite; it is not re-pinned.
* No scoring weight, threshold, band, formula, cap, penalty, knockout semantic, confidence rule
  or missing-value rule was changed.
* No historical evaluation was re-run, edited or re-hashed; the Jio record `…7857589a` and the
  HD Fire record `…551a7eab` are untouched (the latter is absent, not replaced).
* D-1 … D-4 (A19 … A22) are intact; the new defect is recorded as a *required decision*, not
  implemented.

---

## 11. Remaining blockers and what would close them

| # | Blocker | Exact evidence required |
|---|---|---|
| 1 | **Historical record absent** | the eight artifacts of `HD-FIRE-PROTECT-LIMITED-20261019-123134Z-final-551a7eab` from the Windows `build/evaluations/` store — then the 7/100 can be recomputed and its hash checked |
| 2 | **RHP pages 31–450 unavailable** (basis-for-offer-price p. 122, restated financials p. 282, contingent-liability note, RPT note, auditors' report) | the PDF itself, or those pages as text; without them rows 18, 21, 25, 35, 38, 39, 42, 43 stay UNRESOLVED and K5 stays unverified |
| 3 | **Price-band floor ₹258 is secondary-only** | the 6 October 2026 price-band advertisement (referenced by S3) or the exchange issue page |
| 4 | **Final Prospectus not published/available** | the Prospectus carries the completed post-Offer shareholding table; it is the only document that can *disclose* the post-issue promoter percentage |
| 5 | **No new evaluation** | a local copy of the filing in the store + the normal ingestion run |
| 6 | **D-5 decision** | approval of the litigation/SEBI default rule; until then the behaviour is pinned by xfail |

**HD Fire acceptance is therefore NOT complete.** Source recovery is partial-but-material
(three primary documents, one complete), evidence validation moved from 10 to 25 verified rows,
the score reconciliation is blocked on the missing record, no new evaluation exists, and the
implementation unchanged. Those five states are distinct and are not to be conflated.

---

## 12. Publication

### 12.1 Implementation commit

`a2803598b22648524f498c6137d6311a7aec925d` on `arena/ae4d04e8-ipo-screening-engine`,
pushed as `62bd22b..a280359` and verified with `git ls-remote` (remote returned the same SHA).
**4 files, 615 insertions, 1 deletion:** this record, the supersession banner on the earlier
reconciliation record, the tracker entry, and the new test module. **No engine, `config/`,
`schema/` or `fixtures/` change.**

### 12.2 Tests at that commit

The engine is byte-identical to the tree the full suite ran on (only documentation and one new
test file changed).

| Run | Result |
|---|---|
| Full backend (`pytest tests -q`) | **1196 passed, 2 xfailed**, 38 warnings, 1095.32 s |
| `tests/test_hd_fire_primary_source_extraction.py` | 4 passed, 2 xfailed (strict) |

### 12.3 PR #6 and `main` (remote-verified)

| Item | Remote value |
|---|---|
| PR #6 | `state: open`, `merged: false`, `merged_at: null`, `mergeable: true` |
| PR #6 head | `e05c0efbca1ecb3024e52da73a22e180ea171118` (`arena/5dd3fe52-ipo-screening-engine`) |
| PR #6 base | `arena/573e69a4-ipo-screening-engine` |
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` (unchanged) |
| CI | no hosted workflows |

PR #6 was neither moved nor merged; there was no force-push, reset, rebase or branch switch.
