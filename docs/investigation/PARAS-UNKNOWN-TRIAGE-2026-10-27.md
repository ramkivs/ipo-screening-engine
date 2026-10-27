# Paras Healthcare — UNKNOWN triage and reader-defect remediation (2026-10-27)

Companion to `PARAS-INGESTION-FAILURE-2026-10-23.md`. That report pinned the
baseline end-to-end result. This one asks a single question of every UNKNOWN
criterion: **is the UNKNOWN caused by a genuine gap in the filing, or by a
defect in extraction / normalisation / mapping / validation?** Where the filing
does state the fact, the reader is fixed and a regression test is added. Where
it genuinely does not, the required block is documented.

Evidence: `evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf`
(651 pages, sha256 `e0a3187fe18d1c12f88f29170291972714cf15be7946e8a7f4a7d8c914570e74`).

No weight, boundary, threshold, penalty, knockout rule or cap was changed. The
v1.5 config is untouched.

---

## 1. Baseline reproduced exactly

Authoritative path (`engine/ipo_screening/pipeline.py` → `evaluate`), canonical
input built by `DocumentExtractor` from the RHP, the issue-terms notice
supplied separately by the identity-bound `parse_official_rhp` path (price band
660 / 693, lot 21, banding 660–693):

| field | value |
| --- | --- |
| final score | **13.0** |
| base score | 16.0 |
| penalty | −3.0 |
| completeness | 43.16% |
| verdict | **AVOID** |
| knockouts | K5 **TRIGGERED** (critical input `issue.price_band_low` UNKNOWN) |
| score-record hash | `f7fab780…` |
| modules | A 6 / B 0 / C 3 / D 1 / E 6 / F 0 |

This matches PR #12's pinned record byte for byte (including the hash), so the
evaluation is a faithful reproduction of the earlier one.

---

## 2. Disposition of every UNKNOWN criterion

### Module B — Valuation (0/20, all UNKNOWN) — **genuine**

All four criteria (`pe_vs_peers`, `second_multiple`, `peg`, `sector_ipo_relative`)
resolve from `pe_premium_pct` / the issuer's post-issue multiple. The RHP states
**weighted-basic EPS of ₹4.36 / ₹13.03 / ₹20.44 / ₹26.65 for FY2023–FY2026** (pp.
631–632) and the FY2026 net PAT (p. 691), but never the **post-issue share
count**: the pre-Offer count is 100,986,187 (p. 123) and post-Offer is `[●]`
(pp. 3, 123). Post-issue shares cannot be derived without dividing the disclosed
fresh-issue amount by the price band, which is exactly the recovered-price
arithmetic `A21` forbids (`PARAS-INGESTION-FAILURE-2026-10-23.md` §34), and the
engine correctly refuses it.

Required block: a post-issue share count, or a post-issue P/E / EV-EBITDA / P-B
figure and a peer set that is not `UNUSABLE`.

### Module C — Offer Structure, Proceeds & Pre-IPO (3/15)

| criterion | verdict | evidence |
| --- | --- | --- |
| `fresh_share` | scored (1/3) | fresh ₹5,000m of ₹15,500m = 32.3% |
| `ofs_seller_type` | **genuine UNKNOWN** | see below |
| `promoter_ofs_pct` | **genuine UNKNOWN** | see below |
| `dilution` | **genuine UNKNOWN** | needs post-issue share count |
| `use_of_proceeds` | **genuine UNKNOWN** | GCP shown as `[●]` |
| `pre_ipo_placement` | scored (2/2) | three placements at ₹60, 2006–2008 |
| `lockin` | **reader defect — remediated** | see §3 |

**Objects of the offer.** The requirement-of-funds table (pp. 129–130) discloses
prepayment/repayment of borrowings **₹3,209.00m**, investment in the wholly
owned subsidiary PMHPL **₹541.00m**, and general corporate purposes **`[●]`**,
with a 25%-of-gross-proceeds legal ceiling. The reader extracts this correctly.
`gcp_amount` stays UNKNOWN because the row is `[●]` (never 0); the legal maximum
is deliberately not substituted, so the `blind_heavy` test `(GCP +
unidentified acquisition)/fresh > 20%` cannot be evaluated. Genuine.

**OFS seller composition (cover p. 1 and pp. 129).** The cover states:

> DETAILS OF THE OFFER FOR SALE BY SELLING SHAREHOLDERS — Dr. Dharminder Kumar
> Nagar | **Promoter Selling Shareholder** | up to `[●]` Equity Shares
> aggregating up to **₹3,000.00m** — Commelina Ltd | **Investor Selling
> Shareholder** | up to `[●]` Equity Shares aggregating up to **₹6,500.00m**.

The seller *names*, *types* and *amounts* are disclosed; the per-seller
*share counts offered* are `[●]` everywhere (cover, p. 129). `promoter_ofs_pct`
needs promoter shares sold ÷ promoter pre-issue shares, so it is genuinely
UNKNOWN.

`ofs_seller_type` is genuinely UNKNOWN too, and for a structural reason: the v1.5
`$defs/seller` model makes `pre_issue_shares` and `shares_sold` **required
numbers**, and `_ofs_seller_bucket` decides `promoter_selling` from
`promoter shares sold > 0`. Inserting a seller row without a share count would
be schema-invalid; inserting one with `shares_sold = 0` would silently score the
case as `none_or_small` (2/2) while the promoter is in fact selling — the
exact deceptive outcome §25.2 of the earlier report warns about. The fail-closed
behaviour (leave `issue.ofs_sellers` absent) is therefore the correct one, and
the reader is not remediated here. Required block: per-seller **number of
Equity Shares offered** in the Offer for Sale (both the cover and p. 129 print
`up to [●]`).

**Dilution** needs either a disclosed dilution percentage or a `growth`
use-of-proceeds bucket; neither is available (post-issue count `[●]`; the bucket
is itself UNKNOWN because GCP is undisclosed). Genuine.

### Module D — Promoter & Governance (1/15)

| criterion | verdict | evidence |
| --- | --- | --- |
| `promoter_post_holding` | **genuine UNKNOWN** | post-issue holding `[●]` (p. 123) |
| `litigation` | scored (0/4) | criminal/regulatory |
| `rpt` | **decision-gated UNKNOWN** | see below |
| `auditor` | scored (1/2) | EOM on FY24–26 (p. 440) |
| `board_kmp` | scored (0/2) | ≥2 KMP exits in 2 years |

`promoter_post_holding`: the shareholding-pattern table (p. 123) states
**72.80%** of 100,986,187 shares pre-Offer and `[●]` post-Offer. The post-issue
count cannot be derived without recovered-price arithmetic (A21). Genuine.

`rpt`: the MRPT table (`final_rpt_rows`) is **PARTIAL** — one summary row plus
only 10 transaction rows read from a 66-row table — and §35 makes the MRPT
measure decision-gated (it depends on decision **D-35**, the consolidated vs
standalone basis, which is not made here). Genuine, pending that decision.

### Module E — Business & Moat (6/15)

`moat` (5) and `visibility` (2) are UNKNOWN because the `moat_rating` and
`visibility_rating` inputs are not supplied; both are decision-gated
assessment inputs. Genuine. The other three criteria (`industry_growth` 3/5,
`concentration` 3/3) are scored from the industry CAGR and customer
concentration.

### Module F — Market & Demand Signals (0/10, all UNKNOWN) — **genuine**

Every criterion is UNKNOWN with the reason "block not supplied". No
`market_data` block (anchor subscription, QIB/NII subscription, GMP, market
regime) exists in the evidence corpus, the supported data providers, or the
evaluation input for Paras. The repository does carry `official-index-history`
and an `ipo-subscription` block for a different issuer (Vishal Nirmiti), not for
Paras. Genuine.

Required block: a market-observation block for the Paras issue — anchor
subscription %, QIB and NII subscription, grey-market premium, and the Nifty
regime on the issue window.

### Knockouts

- **K5 TRIGGERED** — `issue.price_band_low` is UNKNOWN *within the RHP* (the band
  is printed `[●]` on the abbreviations/definitions pages). The identity-bound
  official-issue path resolves 660–693 from the separate issue-terms notice,
  which is what the pinned 13.0 uses.
- **K1** (`going_concern_uncertainty`) — genuine UNKNOWN: unmodified opinion, no
  EOM for FY24–FY26 (p. 440), prepared on a going-concern basis (p. 366). An
  RHP that states the accounts are prepared on a going-concern basis does not
  state an uncertainty.
- **K2** (`sebi_ed_action_active`) — genuine UNKNOWN: the RHP's "nil"
  statements are promoter-scoped and say nothing about an active SEBI ED action
  against the company.
- **K4** (`promoter_exit` / CFO-to-PAT) — genuine: needs the post-issue
  holding and a promoted-share sale, neither disclosed.
- **K6** (`rpt_pct_of_revenue_growth`) — decision-gated with `rpt` (D-35).

---

## 3. The one confirmed reader defect — `lockin` / `large_holders_unlocked_early`

`_lockin_bucket` is `intact` only when `promoter_lockin_in_place` is true **and**
`large_holders_unlocked_early` is false; with the second field `None` it returns
UNKNOWN. On the strict real-filing path the builder never sets that field
(`builder.py` supplies it only on the synthetic-template path), so it is `None`
for every real filing unless a reader emits it. **No reader did.**

Paras does disclose the Regulation 17(1)(c) carve-out, on **p. 117**:

> the entire pre -Offer Equity Share capital of our Company shall be locked -in
> for a period of six months from the date of Allotment, except for … (iii) the
> Equity Shares held by a **VCF or a Category I AIF or a Category II AIF or a
> FVCI**, provided that such Equity Shares will be **locked-in for a period of at
> least six months from the date of purchase** by the VCF or Category I AIF or
> Category II AIF or FVCI shareholders.

Every other pre-Offer holder is locked six months from allotment. For the
carve-out, the lock-in is instead a *minimum* six months from **purchase** — a
different commencement date, not a shorter period. Whether that is an *early*
unlock depends on when each holder purchased, which the filing does not state: a
holder that purchased more than six months before the Offer is free at allotment,
while one that purchased shortly before the Issue can be locked up to *later*
than allotment + six months. The spec's lock-in row is "promoter lock-in intact,
**no early unlock of large holders** = 1; otherwise 0". The promoter lock-in is
separately intact (p. 116), so the field is a distinct fact.

> **Correction, 2026-10-27.** This report's first draft stated that Paras
> "discloses the early unlock". Paras discloses the **carve-out**, not an early
> release; the two sentences above are what the text actually establishes. The
> reader and its tests are preserved unchanged, but whether a Regulation
> 17(1)(c) carve-out may set `capital_structure.large_holders_unlocked_early` is
> recorded as an open decision in
> `handoff/decisions/A34-early-unlock-carve-out-semantics.md` (PROPOSED, not
> implemented). **A category carve-out alone must not set the flag; without
> evidence of an actual early release the field stays `null` and C `lockin`
> stays UNKNOWN.**

### Remediation

`SectionExtractor.extract_capital_structure` now reads the carve-out and emits
`capital_structure.large_holders_unlocked_early = True` with a verbatim
quotation (matched span on the page, `quote_is_processing=False`):

```
locator: Early unlock of large pre-IPO holders
quote:   "VCF or a Category I AIF or a Category II AIF or a FVCI, provided that such
         Equity Shares will be locked -in for a period of at least six months from
         the date of purchase"
page:    117
```

The rule keys on the disclosed semantics -- an institutional / venture holder
category (`VCF`, `Venture Capital Fund`, `Category I AIF`, `Category II AIF`,
`Alternative Investment Fund`, `FVCI`, `Foreign Venture Capital Investor`)
stated together with a lock-in anchored to the **date of purchase** rather than
the general six-months-from-Allotment lock-in -- not on any issuer's names,
pages, passages, dates or values. It matches the category and the lock-in clause
in either order and in abbreviated or spelled-out form, and it sets the flag
only where both halves appear in the same sentence. A filing that merely lists
a category, that gives the category the general Allotment-anchored lock-in, that
anchors a longer lock-in to purchase, or that states only the promoter lock-in
leaves the flag unset (UNKNOWN). The builder already forwards the extracted
value through `_cap_value`. The rule, its generality and its cross-issuer
coverage are pinned in `LOCKIN-INSTITUTIONAL-CARVEOUT-GENERALITY-2026-10-27.md`.

### Effect on the pinned record

The final score is unchanged at **13.0**, verdict **AVOID**, K5 **TRIGGERED** —
UNKNOWN criteria already contributed 0 to the score. What changes is the
completeness: `lockin` moves from UNKNOWN (1 point available) to SCORED **0**
(`weak`), so available points fall by one and completeness rises
**43.16% → 44.21%**. The score-record hash changes accordingly
(`f7fab780…` → `15502025…`) because the canonical input now carries the new
extracted field. No weight, boundary or threshold moved.

### Regression tests

`tests/test_reading_defects_20261026.py`:

- `test_an_early_unlock_of_large_pre_ipo_holders_is_read` — both phrasings
  ("six months" and "6 months ... their purchase") set the flag to `True` with a
  verbatim quote and page.
- `test_a_promoter_lock_in_alone_does_not_set_the_early_unlock_flag` — the flag
  is not inferred from the promoter lock-in.
- `test_an_early_unlock_extraction_reaches_the_canonical_field` — the builder
  does not overwrite the reader's value.

`tests/test_lockin_institutional_carveout.py` — the cross-issuer matrix
(positive / negative / ambiguous / absent, real filings and labelled synthetic
wording variants, plus the `lockin_bucket` consumer and the
module-isolation check). See the generality report for the case list.

---

## 4. Required blocks for the genuine gaps

| module / criterion | required block |
| --- | --- |
| B — all four | post-issue share count (or a post-issue P/E / EV-EBITDA / P-B and a usable peer set) |
| C — `use_of_proceeds` | the actual general-corporate-purposes amount (RHP prints `[●]`; the 25% legal ceiling is not substituted) |
| C — `ofs_seller_type`, `promoter_ofs_pct` | per-seller number of Equity Shares offered in the OFS (cover and p. 129 print `up to [●]`) |
| C — `dilution` | post-issue share count |
| D — `promoter_post_holding` | post-issue share count |
| D — `rpt` | decision D-35 (consolidated vs standalone MRPT basis) + the full MRPT transaction table |
| E — `moat`, `visibility` | the `moat_rating` / `visibility_rating` assessment inputs |
| F — all five | a market-observation block: anchor subscription, QIB/NII subscription, GMP, market regime |
| K1, K2, K4 | explicit going-concern-uncertainty, SEBI ED action, and promoter-exit / CFO-to-PAT disclosures |
| K6 | the same MRPT basis as D |
