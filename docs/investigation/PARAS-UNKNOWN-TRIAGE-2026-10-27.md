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

## 0. Status update — A34 approved and implemented (2026-10-27, later pass)

**This report's §1 is the pre-PR #13 baseline (43.16%, `lockin` UNKNOWN). Its
§3 "Remediation" described the PR #13 reader, which set
`large_holders_unlocked_early = True` from the Regulation 17(1)(c) carve-out
and produced the intermediate 44.21% / `lockin` SCORED 0 `weak` result. That
intermediate result is retained below as a labelled baseline, not as the
current engine's answer.**

A34 **Alternative B is now approved and implemented**: a category-specific
institutional carve-out alone does not establish an early unlock. The PR #13
carve-out reader has been replaced by a fail-closed evidenced-early-release
rule in `engine/ipo_screening/extraction/sections.py`. Paras prints the
carve-out on p. 117 but no evidenced early release, so the field is `null`
again and C `lockin` is **UNKNOWN**.

**Current Paras result after A34 (freshly reproduced):**
**13.0 / 16.0 / −3.0 / 43.16% / `AVOID` / K5 TRIGGERED / bounds 1.0–67.0 /
`lockin` UNKNOWN / `board_kmp` SCORED 0 `high_churn` / `kmp_exits_2y` 4 /
`large_holders_unlocked_early` `null`.** A33 Alternative A is also approved, so
the counting rule and the `board_kmp` classification are unchanged.

Full before/after tables, quotations, page provenance and verification are in
`A33-A34-ISSUER-REPRODUCTION-2026-10-27.md` and in A34 §0. The remainder of
this report is the historical triage of the other UNKNOWN criteria, which is
unaffected by A34.

---

## 1. Baseline reproduced exactly (pre-PR #13 baseline)

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

## 3. `lockin` / `large_holders_unlocked_early` — reader defect, then semantic correction

`_lockin_bucket` is `intact` only when `promoter_lockin_in_place` is true **and**
`large_holders_unlocked_early` is false; with the second field `None` it returns
UNKNOWN. On the strict real-filing path the builder never sets that field
(`builder.py` supplies it only on the synthetic-template path), so it is `None`
for every real filing unless a reader emits it. **No reader did** before PR #13.

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
separately intact (evidence page 115), so the field is a distinct fact.

### Three states, all measured

| State | `large_holders_unlocked_early` | C `lockin` | completeness | bounds |
| --- | --- | --- | --- | --- |
| §1 pre-PR #13 baseline | `null` | UNKNOWN | 43.16% | 1.0–67.0 |
| PR #13 intermediate (revision 1) | `true` (carve-out, p. 117) | SCORED 0 `weak` | 44.21% | 1.0–66.0 |
| **After A34 (approved, current)** | **`null`** | **UNKNOWN** | **43.16%** | **1.0–67.0** |

The intermediate state emitted a p. 117 evidence row with locator "Early
unlock of large pre-IPO holders" and the quote "VCF or a Category I AIF …
locked -in for a period of at least six months from the date of purchase".
**A34 withdraws the inference, not the quotation**: the quote is verbatim and
correctly page-attributed, but it states a purchase-anchored minimum, not a
release. After A34 there is no evidence row and no `field_map` entry for this
field on Paras.

### Correction and current remediation

`handoff/decisions/A34-early-unlock-carve-out-semantics.md` first recorded the
question as PROPOSED; **Alternative B is now approved and implemented**.
`SectionExtractor.extract_capital_structure` sets the flag `True` only where one
sentence evidences an actual early release of named large / pre-IPO /
institutional holders (holder group + release act + lock-in context + explicit
early / before-expiry timing), and stays UNKNOWN for a carve-out, pledge
release, transferability wording, normal expiry release, or hypothetical /
negated language. Nothing infers a favourable `False`. No weight, boundary,
threshold, penalty, knockout, config, schema or `derived.py` change was made.

A full-text scan of all five real filings examined (2,826 pages) found **no**
evidenced early release, so the genuine positive cases are labelled synthetic
tests. Zero matches in this corpus is **not** proof that early releases never
occur.

### Effect on the pinned record (restated)

Final score **13.0**, verdict **`AVOID`**, K5 **TRIGGERED** — unchanged in all
three states. What moves is completeness: PR #13 moved `lockin` from UNKNOWN to
SCORED 0 and completeness rose **43.16% → 44.21%**; A34 returns it to UNKNOWN
and completeness **43.16%**. The score-record hash changes with the canonical
input in each state; no historical evaluation record was edited.

### Regression tests (current)

`tests/test_lockin_institutional_carveout.py` — 28-test A34 semantic boundary:
Paras p. 117 carve-out quote asserted on the page and the flag absent; Jio,
Moneyview, Vishal Nirmiti and R.K. Fashion; carve-out wording variants,
ambiguous, pledge/transferability, hypothetical/negated and absent cases stay
UNKNOWN; labelled synthetic evidenced releases set the flag; canonical and
criterion consumers pinned.

`tests/test_reading_defects_20261026.py` — the two Paras carve-out phrasings no
longer set the flag; one evidenced release does; promoter-only lock-in and the
builder path are pinned.

`tests/test_paras_evidence_regression.py` — two new A34 tests pin the absent
evidence row on the real filing and the full end-to-end result
(13.0 / 16.0 / −3.0 / 43.16% / `AVOID` / K5 / `lockin` UNKNOWN /
`board_kmp` `high_churn` / `kmp_exits_2y` 4).

See `LOCKIN-INSTITUTIONAL-CARVEOUT-GENERALITY-2026-10-27.md` (revision 2) and
`A33-A34-ISSUER-REPRODUCTION-2026-10-27.md` for the cross-issuer matrix and the
measured before/after values.

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
