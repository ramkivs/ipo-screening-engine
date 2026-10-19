# HD Fire Protect + Jio Platforms — Score Reconciliation, Evidence Completeness and Extraction Audit

- **Date:** 2026-10-19 (Asia/Calcutta)
- **Subject:** the operator's 2026-10-19 Windows scorecards — HD Fire Protect 7/100 and Jio Platforms 21/100 — and Arena's 29/100 Jio reproduction.
- **Mode:** investigate first; evidence-based correction only. No scoring weight, threshold, formula, knockout semantic or penalty rule is changed by this record.
- **Baseline adopted for reproduction:** `e1df89b2af3bd432a70fe9716e266895ba6ff2e7` (tip of `arena/d15866b5-ipo-screening-engine`; contains the Jio financial-statement correction `950d239`, the five-field manual issue-term path `9583373`/`0d71aa8`, and the HD Fire peer-row correction `afdd498`). `main` remains `01ba66c12ca1195fd7acbd287c3e39a019808094`.
- **Arena evidence boundary:** the operator's Windows store, browser, API runtime and the HD Fire filing are **not** accessible from Arena. Every statement below is labelled **CONFIRMED** (reproduced or code-traced in Arena), **INFERRED** (exact arithmetic from the reported scorecard and the governed configuration, but not read from the operator's record), or **WINDOWS-ONLY** (requires the operator's record/filing). No Windows artefact is claimed as inspected.

---

## 0. Executive findings

### 0.1 HD Fire Protect — 7/100

| Question | Finding |
|---|---|
| Current reported score | **7/100** (base 10, applied penalties −3, floor 0, ceiling 60; available 27, unknown 73, confidence 27%, verdict INSUFFICIENT_DATA). |
| Is the score reproducible? | **Yes at the arithmetic/component level (CONFIRMED by exact reconstruction from the governed configuration).** The score decomposes uniquely into A 2/25 + B 0/20 + C 3/15 + D 5/15 + E 0/15 + F 0/10 = 10, minus the one applied penalty (−3) = 7, capped at 60 by the pure-OFS cap. A re-execution on the filing is not possible in Arena (filing absent). |
| Is it trustworthy as a complete fundamental assessment? | **No.** 73 of 100 evaluable points are UNKNOWN; the verdict is correctly INSUFFICIENT_DATA. Four of the six knockouts are UNVERIFIED. The score is a partial-coverage floor, not a verdict on the company. |
| Principal confirmed defects | (1) The applied −3 is `receivable_days_up`, **not** `auditor_cfo_exit`; the alternative attribution is an external interpretation error. The auditor/CFO penalty was structurally UNKNOWN because the builder dropped its schema-permitted input — now corrected. (2) The NIL-OFS matcher can bind an unrelated "NIL"/"Not applicable" cell to `issue.ofs`; the demonstrated false positive exactly matches the operator's `issue.ofs` conflict (filing 0 vs entered 71,231). (3) `board_kmp` 1/2 is produced by unverified builder defaults;  `pre_ipo_placement` 2/2 is produced by an empty default list; (4) K2 is CLEAR on unverified defaults (pledge 0.0, SEBI/ED False), not on evidence. |
| Principal suspected defects | The filing's financial statements may contain the missing margin/ROCE/CFO/leverage inputs that the pre-`e1df89b` extraction missed (the same class of defects proved on Jio: interim/fiscal column mixing, CFO row label, borrowings rows, unit detection, net-worth overmatch). This is **not asserted** for HD Fire until the filing is re-run. |
| Genuine source-data gaps | Market blocks (anchor/subscription/GMP/regime) were not supplied; bidding had not opened. No later market data may be inserted into this historical record. Peer valuation and sector comparables were not supplied. Moat/visibility are unrecorded qualitative assessments. |
| Scoring or presentation defect? | **No scoring formula defect found.** There is a presentation false-assurance defect: a 0-point penalty does not distinguish "not triggered" from "UNKNOWN, carried in the lower bound"; this is corrected in this session (state and reason are now projected and rendered). |
| Is a new evaluation warranted? | **Yes**, after (a) the filing is re-run at the corrected extraction baseline, (b) the issue structure is confirmed from the RHP, and (c) the unverified-default and K2 default-clear decisions are authorized. The 7/100 record must remain immutable. |

### 0.2 Jio Platforms — 21/100 versus 29/100

| Question | Finding |
|---|---|
| Current reported score | **21/100** (INSUFFICIENT_DATA, Low 46%, unknown 54, available 46, Revenue CAGR +15.79%, ROCE 10.76%, CFO/PAT 2.62). |
| Arena reproduction | **29/100** at `e1df89b` from the committed RHP with price band 1065–1119, lot 12, OFS 0 and fresh amount 3,021,300 (in the submitted unit): A 13/25, B 0/20, C 11/15, D 5/15, E 0/15, F 0/10; available 46, unknown 54, Low 46%, missing rows 31. This is the previously published 29. |
| Is the score reproducible? | **Yes, both numbers.** The 21 is reproduced **exactly** by the same engine and the same financial inputs with the issue structure inverted to `fresh_issue = 0` and `ofs > 0`: A 13, B 0, C 3, D 5, E 0, F 0 = 21; available 46, unknown 54, Low 46%, pure-OFS cap 60, missing rows 32. |
| Cause of the 8-point difference | **One component, four criteria, entirely Module C.** `fresh_share` 3→0 (−3), `ofs_seller_type` 2→0 (−2), `promoter_ofs_pct` 2→0 (−2), `dilution` 1→0 (−1). `use_of_proceeds` moves UNKNOWN→SCORED-zero (score unchanged) and `dilution`/`uop` become scored by `zero_if: pure_ofs`; the two seller criteria become UNKNOWN. Availability is invariant (46) because −4 available points from the seller criteria are exactly offset by +4 from the `zero_if` scoring of use-of-proceeds. |
| Is the financial extraction correction real? | **Yes (CONFIRMED against the RHP).** Page 76 (in ₹ million): FY2026 1,468,853; FY2025 1,282,184; FY2024 1,095,581 → CAGR **+15.7889%**, the figure the RHP states on page 128. Page 77: CFO 775,563/681,557/576,616 → cumulative CFO/PAT **2.6206**. Page 132: disclosed ROCE **10.76%/12.50%/12.83%**. The pre-fix −48.36% is the same formula over the wrong columns (391,729/1,468,853). |
| Is the 21 a scoring defect? | **No.** It is an issue-term (`issue.fresh_issue`/`issue.ofs`) data defect in the Windows evaluation: the filing and the RHP cover establish a fresh-only offer (OFS "Not applicable", 270,000,000 fresh shares); the 21 is what the engine produces when that structure is inverted. The exact submitted values and canonical issue block in the Windows record will confirm which side was inverted. |
| Trustworthy as a complete assessment? | **No.** The 21/29 is dominated by governed UNKNOWNs (peers, net worth, auditor, RPT, industry, moat, market). The financial quality metrics are now correctly extracted, but the score is not a complete fundamental view. |
| New evaluation? | **Yes** — a new evaluation with the filing-established structure and corrected unit is warranted. The Windows 21 record must remain immutable. |

---

## 1. Environments, commits and artefacts

| Item | Value | Verification |
|---|---|---|
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` | Remote ref; untouched. |
| PR #6 | **OPEN, UNMERGED**, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118` | `gh pr view 6`; not merged, not closed by this session. |
| Published baseline adopted | `arena/d15866b5-ipo-screening-engine` @ `e1df89b2af3bd432a70fe9716e266895ba6ff2e7` | Ancestry includes `e05c0ef` → `950d239` → `176c3b6` → `afdd498` → `e1df89b`. |
| Jio financial correction | `950d2398d0143de3f15d3a2fd34621f7ef8b784d` | Fiscal-column selection, row labels, `(in ₹ million)` unit, net-worth overmatch, ROCE KPI, borrowings. |
| Jio five-field manual terms | `958337375174be87726ed1bac0e3d6dc48aa8c99` (path) / `0d71aa8` (publication) | `issue.fresh_issue` became a bounded manual term. |
| HD Fire peer-row correction | `afdd4985a305fe4c3224ccd29e820395d0729f6b` | Layout-anchored peer mapping; early out-of-contract rejection. |
| Engine/spec/config | 1.5.0 / 1.5 / `ipo-config.v1.5.0.json` (config 1.5.0) | `version.py`, config header. |
| Jio RHP | `evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`, 591 pp. | SHA-256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`. It is non-authoritative investigation evidence (not an official source). |
| HD Fire filing | **Not present in the repository.** | Cannot be inspected in Arena; no page/table evidence is claimed. |
| Windows store/API/browser | **Not accessible.** | No Windows evaluation artefact is claimed as inspected. |

### 1.1 Reproduction commands used in Arena

```bash
# Correct (filing-established) structure: fresh-only, OFS = 0
PYTHONPATH=engine ./.venv/bin/python /tmp/reproduce_jio.py 3021300 0 correct
# Inverted structure: fresh = 0, OFS > 0
PYTHONPATH=engine ./.venv/bin/python /tmp/reproduce_jio.py 0 3021300 inverted
```

Both runs ingest the committed RHP through `PresentationService` with the five manual terms (price band 1065/1119, lot 12, OFS as stated, fresh amount as stated) and the explanation recorded. The first run reproduced **29.0 / 46 available / 54 unknown / 31 missing rows / no cap**; the second reproduced **21.0 / 46 / 54 / 32 / pure_ofs cap 60**. The numeric summaries are quoted in §3.

---

## 2. PART A — HD Fire Protect

### 2.1 Exact scorecard reconciliation (CONFIRMED arithmetic)

The reported aggregates are sufficient to identify every module total unambiguously:

| Module | Max | Score | Available | Unknown | Criteria scored / unknown |
|---|---:|---:|---:|---:|---|
| A Financial Quality | 25 | **2** | 6 | 19 | `revenue_cagr` 2/6 at 14.54%; `margin_trend`, `roce`, `cfo_quality`, `leverage` UNKNOWN |
| B Valuation | 20 | **0** | 0 | 20 | all four criteria UNKNOWN |
| C Offer Structure | 15 | **3** | 11 | 4 | `fresh_share` 0/3 (0.00%); `ofs_seller_type` 0/2 UNKNOWN; `promoter_ofs_pct` 0/2 UNKNOWN; `dilution` 0/1 `zero_if pure_ofs`; `use_of_proceeds` 0/4 `zero_if pure_ofs`; `pre_ipo_placement` 2/2; `lockin` 1/1 |
| D Promoter & Governance | 15 | **5** | 10 | 5 | `promoter_post_holding` 4/4 (100%); `litigation` 0/4 (`criminal_or_regulatory`); `rpt` 0/3 UNKNOWN; `auditor` 0/2 UNKNOWN; `board_kmp` 1/2 (`other`) |
| E Business & Moat | 15 | **0** | 0 | 15 | all four UNKNOWN |
| F Market & Demand | 10 | **0** | 0 | 10 | all four UNKNOWN |
| **Total** | **100** | **10** | **27** | **73** | completeness 27/100 = **27%** |

Penalties: **−3** applied (one item); floor `max(0, 10 − 3 − unresolved) = 0` ⇒ unresolved penalty points **≥7**; upper `min(60, 10 + 73 − 3) = 60` ⇒ the pure-OFS cap is applied. Final `10 − 3 = 7`, floor 0, ceiling 60. This is exactly the reported scorecard.

**What the arithmetic proves independently of the missing record:**
1. `issue.fresh_issue` was present and **exactly 0** (the schema requires the field for evaluation; the cap fires only on `pure_ofs`, derived from `fresh_issue == 0`).
2. `issue.ofs` was **> 0** (otherwise `ofs_seller_type` and `promoter_ofs_pct` would be scored `none_or_small`/0%, adding 4 available points and 4 score points — the observed C score/available is 3/11).
3. Therefore the offer is **pure OFS** and the ~71,231 manual OFS value was the one used (the filing-extracted 0 was overridden after the conflict).
4. The 20 UNKNOWN criteria + 4 UNVERIFIED knockouts (K1, K3, K5, K6) + 4 missing market blocks + **4** missing critical-data inputs (`sebi_ed_action_active` is a (defaulted) value, so it is not in `critical_data_missing`) + **4** UNKNOWN penalty items (`auditor_cfo_exit` 3, `unreconciled_metrics` 2, `regulatory_dependence` 2, `eom_caro` 3 = 10 unresolved points, which makes the floor `max(0, 10−3−10) = 0`) = **36** rows, exactly matching the reported "36 missing/unverified items". The applied `receivable_days_up` (−3) is the only SCORED penalty; the other two penalties (`margin_spike`, `discounted_allotments`) are SCORED at zero. This is the same unknown-penalty set as the reproduced Jio record (whose 31 rows include the same four).

### 2.2 Module A — Financial Quality (field by field)

| Canonical field | Engine value / status | Score | Source location expected | Extracted? | Normalised? | Reached evaluation? | Cause class | Evidence needed |
|---|---|---:|---|---|---|---|---|---|
| `revenue_cagr` (`revenue_cagr_2y_from_3fy`) | 14.54% **SCORED** | 2/6 | RHP restated consolidated P&L, revenue from operations, FY2024–FY2026 | Yes (value is in the record) | Not established in Arena | Yes | **Source value; not a defect.** Band `>=8` and `<15` ⇒ 2 | RHP page/columns to confirm the periods and unit |
| `margin_trend` | UNKNOWN | 0/5 | Restated P&L: revenue, EBITDA/operating profit, PAT for ≥2 full FYs | No | n/a | Yes (UNKNOWN) | **Extraction gap — suspected, not confirmed.** The Jio audit proved the same statement shapes can mix interim/fiscal columns and miss EBITDA row labels | RHP statement pages + re-run at `e1df89b` |
| `roce` (`roce_latest`) | UNKNOWN | 0/5 | "Basis for Offer Price" KPI table (disclosed ROCE), or EBIT / (net worth + total debt) | No | n/a | Yes | **Extraction gap — suspected.** The disclosed-ROCE KPI path was only corrected on 2026-10-19 (`950d239`); HD Fire's evaluation predates/does not exercise it | RHP KPI table page + re-run |
| `cfo_quality` (`cfo_pat_cumulative`) | UNKNOWN | 0/5 | Restated consolidated cash-flow statement, "Net Cash Flow from Operating Activities" | No | n/a | Yes | **Extraction gap — suspected.** The CFO row label was corrected on 2026-10-19 | RHP cash-flow page + re-run |
| `leverage` (`leverage_bucket`) | UNKNOWN | 0/4 | Balance sheet: total equity/net worth and non-current + current borrowings | No | n/a | Yes | **Extraction gap — suspected for borrowings; net worth may be genuinely absent as a stated subtotal** (Jio's statements have no "Total Equity" row, only components). The metric requires **both** inputs and fails closed | RHP balance sheet + any stated total-equity row; otherwise a governed cross-section/derivation decision |

**Module A conclusion:** the only scored point is the revenue CAGR. The other four metrics are UNKNOWN. On the Jio evidence, all four are plausible extraction recoveries from a standard RHP; on the HD Fire evidence available in Arena, **none can be called a parser defect**. The correct first action is a re-run at `e1df89b` with the filing, not a code change.

### 2.3 Module B — Valuation

| Canonical field | Engine value / status | Score | Source location expected | Cause class | Evidence needed |
|---|---|---:|---|---|---|
| `pe_vs_peers` | UNKNOWN | 0/8 | Issue P/E (price band / post-issue EPS) and peer P/E table | **Missing/unsupported peer inputs.** The HD Fire peer rows failed schema (`roe_pct` 26957.28 / 21700.34) and the evaluation could not use them; the early-rejection correction is `afdd498` | Valid peer rows with identity, period, unit, as-of; issue EPS basis |
| `second_multiple` | UNKNOWN | 0/4 | Peer P/B or EV/EBITDA and the corresponding issuer multiple | Same | Same |
| `peg` | UNKNOWN | 0/4 | Issue P/E and PAT CAGR | Issue P/E/EPS inputs unavailable or not mapped | Post-issue EPS basis and price |
| `sector_ipo_relative` | UNKNOWN | 0/4 | Recent same-sector IPO valuation observations | **Genuine external gap** — no same-sector IPO comparables were supplied | Governed market-comparables source |

**Do not** manufacture a post-issue EPS or a peer median. The peer correction now emits **no peers** for an unrecognised layout (governed UNKNOWN), which is the correct fail-closed outcome.

### 2.4 Module C — Offer structure, proceeds and pre-IPO

| Canonical field | Engine value / status | Score | Reconciliation |
|---|---|---:|---|
| `fresh_share` | 0.00% **SCORED** | 0/3 | Pure-OFS structure. `fresh_issue` is explicitly 0 (proved by the cap and the schema gate), **not missing**. The band `else` is 0. |
| `ofs_seller_type` | UNKNOWN | 0/2 | An OFS is present (`ofs > 0`) and the seller list was not supplied. **Unknown seller composition must remain unknown.** The engine does not infer "no promoter sold". |
| `promoter_ofs_pct` | UNKNOWN | 0/2 | Same reason: no seller-level pre-issue shares/sold shares. **Do not infer zero.** |
| `dilution` | SCORED 0, `zeroed_by: pure_ofs` | 0/1 | Configured `zero_if: pure_ofs`; the criterion is not applicable to a no-fresh-issue offer. This is a scored zero by configuration, not an unknown. |
| `use_of_proceeds` | SCORED 0, `zeroed_by: pure_ofs` | 0/4 | Same; a pure OFS raises no proceeds for the company. |
| `pre_ipo_placement` | `none_or_near_ipo` **SCORED** | 2/2 | **Not evidenced in Arena.** No extractor emits `capital_structure.pre_ipo_placements`; the builder defaults it to `[]`, and the derived bucket treats `[]` as "none disclosed". The 2/2 is therefore **unverified/defaulted**, not source-established. |
| `lockin` | `intact` **SCORED** | 1/1 | The section extractor emits `promoter_lockin_in_place=True` only when the text says "locked in for a period of 18 months" or the builder default applies. The record must show whether evidence exists; if not, 1/1 is unsupported. |

**Fresh vs OFS reconciliation:** this is a **100% OFS offer**. The fresh-issue amount is explicit zero; the OFS amount is the manual 71,231 (₹ lakh, ≈ ₹712.31 crore, against the GMP-captured issue size ₹712.13 crore). The filing extraction's `issue.ofs = 0` was wrong for a pure-OFS cover and was surfaced as a conflict; the operator confirmed the manual value. The seller composition is genuinely unknown in the record and must not be converted to "no promoter selling".

**Likely cause of the filing's `ofs = 0`:** the NIL-OFS matcher in `extraction/sections.py` searches from "offer for sale" across **up to 32 newlines** for any `NIL`/`Not applicable`, without binding to the OFS row. A pure-OFS cover whose *fresh issue* row says `NIL` (a standard two-column layout) matches and sets `ofs = 0`. This is demonstrated with a synthetic cover in §2.7 and corrected in this session.

### 2.5 Module D — Promoter and governance

| Canonical field | Engine value / status | Score | Evidence |
|---|---|---:|---|
| `promoter_post_holding` | 100% **SCORED** | 4/4 | Extracted value (the builder default is `None`, so 100% must come from extraction/reference). For a pure OFS this means no promoter shares were sold, which must be checked against the shareholding table; it is not assumed. |
| `litigation` | `criminal_or_regulatory` **SCORED** | 0/4 | Extracted bucket. The exact proceeding, subject and materiality are **not established in Arena**. The adverse finding must not be removed to improve the score; the record must identify the triggering text. |
| `rpt` | UNKNOWN | 0/3 | Canonical `governance.rpt_pct_revenue` absent. The RPT extractor exists, but the approved metric requires a stated/derived RPT-sales share; the record must show whether the filing's RPT note was parsed. |
| `auditor` | UNKNOWN | 0/2 | `governance.auditor_opinion` absent/unmapped. The taxonomy (unqualified/qualified/adverse/disclaimer) may not match the document class; this is a governed unknown. |
| `board_kmp` | `other` **SCORED** | 1/2 | **Defaulted, not evidenced.** `board_independent_majority=False` and `kmp_exits_2y=0` are builder defaults; no extractor emits them. The `other` bucket follows mechanically. This point is unsupported. |

### 2.6 Penalties — the −3 attribution (mandatory finding)

**Conclusion: the applied −3 belongs to `receivable_days_up`. `auditor_cfo_exit` contributed 0 applied points. Gemini's attribution is wrong.**

Code trace (all lines verified in Arena):

1. **Configuration** (`config/ipo-config.v1.5.0.json`, `penalties.items`):
   - `receivable_days_up`: −3 when `receivable_days_yoy_pct > 30`.
   - `auditor_cfo_exit`: −3 when the flag `auditor_or_cfo_exit_2y` is true.
2. **Metric derivation** (`derived.py`):
   - `receivable_days_yoy_pct = (receivable_days latest / prior − 1) × 100`; UNKNOWN if either year is missing; NOT_APPLICABLE if prior is 0.
   - `auditor_or_cfo_exit_2y` is a **passthrough** of `governance.auditor_or_cfo_exit_2y`; UNKNOWN when the input is absent.
3. **Penalty evaluation** (`scoring.py::_evaluate_penalties`): each item evaluates **its own** `when`; there is no shared index, no label lookup, no cross-item mutation. True ⇒ points −3, state SCORED; False ⇒ points 0, state SCORED, reason "not triggered"; unknown ⇒ points 0, state UNKNOWN, reason "carried in the lower bound", and its magnitude is added to `unresolved_penalty_points`.
4. **Persistence**: `score_result.penalty_items` is stored verbatim in the evaluation record (`penalties[]`), and the penalty total is the sum of the item points floored at −15.
5. **API projection** (`presentation/service.py`): `PenaltyItem(id, label, points, state, trigger)` is built from the same stored item, one-to-one, with no re-ordering.
6. **Renderer** (`frontend/app.js`): iterates `evaluation.penalties` and prints `p.id`, `p.label`, `p.points`.
7. **Therefore** a scorecard line `receivable_days_up: −3` and `auditor_cfo_exit: 0` is exactly the stored per-item attribution. No code path can transfer the −3 from one item to the other. The only way `auditor_cfo_exit` could be −3 is if its own flag were true, in which case the total would be **−6**, not −3.

**A confirmed mapping defect makes the ambiguity one-sided.** The input schema permits `governance.auditor_or_cfo_exit_2y` and the derived metric consumes it, but `CanonicalInputBuilder._build_governance` did not carry the key into the canonical input at all. The same was true of `financials.adjusted_metrics_unreconciled` and the `unreconciled_metrics` penalty. For **every builder-based evaluation**, therefore, `auditor_cfo_exit` was structurally UNKNOWN — never "not triggered" — regardless of what the filing or input said. This is a confirmed **correct-value-lost-between-stages** defect (not a penalty-rule defect), and it makes the attribution question conclusive: the HD Fire scorecard's 0-point `auditor_cfo_exit` is an unresolved penalty, and the applied −3 can only be `receivable_days_up`.

**Corrected in this session:** both keys are now carried when the input/extraction establishes them, and left absent (UNKNOWN) when it does not. The golden input carries neither key, so its canonical input and result hash are byte-identical (`e84f8bc0…` re-verified). No scoring rule changed. `tests/test_penalty_attribution.py` fails against the pre-fix builder for the True cases and passes after the fix.

**The floor corroborates the trace.** The reported floor is 0, below `base 10 − applied 3 = 7`. That requires `unresolved_penalty_points ≥ 7`. So at least one penalty (and in practice several) was UNKNOWN and carried in the lower bound. `auditor_cfo_exit` at 0 applied points is therefore either "not triggered" or "UNKNOWN — carried"; in neither case is it the applied −3. Gemini appears to have conflated the unresolved-penalty effect in the range with the single applied penalty.

**Presentation defect corrected in this session:** the persisted item already carries `state` and `reason`, but the API model dropped `reason` and the scorecard rendered neither state nor reason, so "0 points" was ambiguous between a cleared flag and an unevaluated one. The projection now carries `reason`, and the scorecard displays `UNKNOWN — carried in range` versus `Not triggered` with the trigger reason. This is an auditability fix; no scoring rule changed and no historical record was rewritten.

### 2.7 The NIL-OFS extraction defect (confirmed and corrected)

**Defect class:** wrong-clause binding (correct value/zero fabricated from an unrelated cell) — an "unknown becomes explicit zero" violation.

The pre-fix pattern:

```python
r'offer for sale(?: size)?[^\n]*?(?:[^\n]*?\n){0,32}?\s*(?:NIL|Not\s+Applicable)\b'
```

It scans up to 32 newlines after any "offer for sale" occurrence. A pure-OFS cover commonly has:

```
Offer for Sale Size
26,280,000 Equity Shares
Fresh Issue
NIL
```

The pattern matches `Offer for Sale Size ... Fresh Issue\nNIL` and sets `issue.ofs = 0.0` and `ofs_sellers = []`, discarding the actual OFS quantity. The same happens with `Pre-IPO Placement\nNIL` or `Promoter Group\nNIL`. This is exactly the HD Fire symptom (a ₹712 Cr pure-OFS offer filing-extracted as OFS 0, later overridden by the operator's 71,231).

**Correction:** the match is accepted only when it is genuinely the OFS row's value:
- the OFS label line itself must not carry an amount/quantity;
- the NIL must not be the value of a bare preceding/adjacent structural label (`Fresh Issue`, `Pre-IPO Placement`, `Promoter Group`, `Anchor Investor`, reservation, total issue size, …);
- the NIL may be on the same line as the OFS label or on the following value line.

The real Jio cover (`OFFER FOR SALE SIZE` … `aggregating up to ₹[●] million` / `Not applicable`) still extracts `ofs = 0.0`; the synthetic Vishal/Jio positives are preserved. A genuine pure-OFS cover with a `Fresh Issue / NIL` cell now leaves `issue.ofs` unknown and available for the governed manual/derivation path instead of fabricating a zero. No scoring, schema, golden or historical record is touched.

### 2.8 Knockouts K1–K6

| Rule | Reconstructed state | Inputs | Why | Evidence needed |
|---|---|---|---|---|
| K1 — auditor opinion/going concern/negative net worth | **UNVERIFIED** | `auditor_opinion`, `going_concern_uncertainty`, `net_worth_latest` | All three are UNKNOWN | Statutory audit opinion; going-concern statement; total equity/net worth |
| K2 — pledge >25% or active SEBI/ED action | **CLEAR — NOT EVIDENCED** | `promoter_pledge_pct` = 0.0 **default**; `sebi_ed_action_active` = False **default** | Both builder defaults are favorable; no extractor found a pledge or an action. Kleene logic then returns CLEAR | Pledge disclosure and SEBI/ED confirmation. Until then K2 must be UNVERIFIED |
| K3 — OFS >80% with declining profits | **UNVERIFIED** | `ofs_share_pct` = 100 (>80 TRUE); `profit_declining` unknown | One child unknown ⇒ all/any cannot resolve to CLEAR | PAT trend over the full FYs |
| K4 — promoter/PE-VC sell >50% and weak financials | **CLEAR** (logic) | `promoter_post_pct` = 100 ⇒ `promoter_full_exit` FALSE and `<20` FALSE ⇒ the nested `any` is FALSE ⇒ `all` CLEAR | A necessary condition is false. This is sound only if 100% is correctly extracted | Shareholding table page |
| K5 — contingent liabilities >50% net worth or unquantified | **UNVERIFIED** | `contingent_liab_pct_networth`, `contingent_liab_unquantified` | Both UNKNOWN | Contingent-liability note + net worth |
| K6 — related parties >40% of revenue growth | **UNVERIFIED** | `rpt_pct_of_revenue_growth` | UNKNOWN | RPT note and revenue periods |

**Material finding:** K2 is **not** a valid CLEAR. The scorecard's K2 state is produced by two favorable defaults, not by evidence. This is a direct violation of the spec's "a missing knockout input must never be treated as CLEAR" (§3.3) and of the prompt's acceptance requirement. The fix is identified below (§5, P0), but it changes the frozen golden result if applied to the shared builder defaults; it therefore requires a governed golden re-baseline decision. It is **not** silently changed here.

### 2.9 Peer extraction correction — verification and HD Fire limitation

**Verified on in-repo reference filings (executed):**
- R.K. Fashion: Banaras Beads pins unchanged — P/E 44.31, RoNW 3.08, P/B 1.36.
- Vishal Nirmiti real filing: GPT Infraprojects 14.83/2.73/18.25; Indian Hume Pipe 13.86/1.32/9.51 — now exactly the golden peers; previously the P/E cell was mapped into `roe_pct` (13.86) with `pb = 0.0` and a 115-word prose "peer" name.
- Placeholder-preserving alignment: `[●]` keeps its column; an unrecognised layout emits no peers; strict row width; prose/total rows are not peers.
- Service-level early rejection: out-of-contract peers produce HTTP 400 with `peers/i/field` and the peer name; nothing is evaluated or persisted; raw values are never clamped.

**HD Fire-specific limitation:** the raw HD Fire peer rows (`26957.28`, `21700.34`) live in the Windows store. Arena has neither the filing nor the store, so it **cannot** say which mechanism produced those exact cells. The two demonstrated mechanisms (layout-position mapping and placeholder-collapse) can both produce monetary-scale cells in `roe_pct`; a genuinely extreme source RoNW cannot be excluded without the raw row. The exact retrieval command is in §9.

### 2.10 The 36 missing/unverified items (reconstructed set)

The count 36 is exactly reproduced by the governed enumerator over the reconstructed state:

- **20 UNKNOWN criteria:** `margin_trend`, `roce`, `cfo_quality`, `leverage`; `pe_vs_peers`, `second_multiple`, `peg`, `sector_ipo_relative`; `ofs_seller_type`, `promoter_ofs_pct`; `rpt`, `auditor`; `industry_growth`, `moat`, `concentration`, `visibility`; `anchor_quality`, `qib_subscription`, `gmp_trend`, `market_regime`.
- **4 UNVERIFIED knockouts:** K1, K3, K5, K6.
- **4 missing market blocks:** anchor, subscription, GMP, regime.
- **4 missing critical-data inputs:** `auditor_opinion`, `going_concern_uncertainty`, `net_worth_latest`, `contingent_liab_pct_networth` (`sebi_ed_action_active` is present as a value, although defaulted).
- **4 UNKNOWN penalties (10 unresolved points):** `auditor_cfo_exit` (3), `unreconciled_metrics` (2), `regulatory_dependence` (2), `eom_caro` (3). `auditor_or_cfo_exit_2y` and `adjusted_metrics_unreconciled` were structurally dropped by the builder (see §2.6); `regulatory_dependence` and `eom_materiality` were not supplied. The floor 0 is exact: `max(0, 10 − 3 − 10) = 0`.

That is **36**. The four penalty identities are the same set as the reproduced Jio record (where the four UNKNOWN penalties are exactly those four); if one of them were SCORED in HD Fire, another penalty would have to be UNKNOWN to keep the count at 36 and the unresolved points at ≥7. The only remaining Windows-side check is confirming the four penalty rows in `penalties[]`; the mapping defect makes `auditor_cfo_exit` definitively UNKNOWN for a builder-based evaluation (it could not be "not triggered" unless the input omitted the key, in which case it is UNKNOWN). The full field table is in Appendix A.

---

## 3. PART B — Jio Platforms

### 3.1 Environment/identity map

| Dimension | Windows 2026-10-19 scorecard | Arena reproduction |
|---|---|---|
| Code | The operator's checkout at the date; the financial corrections require `950d239` or later; the five-field manual path requires `9583373` or later. **Exact commit is Windows-only.** | `e1df89b` (contains all the above plus `afdd498`) |
| Config | v1.5.0 (assumed; must be read from the record) | `ipo-config.v1.5.0.json`, hash from `load_config` |
| Filing | The operator's uploaded `U72900GJ2019PLC110816_JIO.pdf` | Same committed PDF, SHA-256 `72480c2e…` |
| Issue terms | Reported: 1065/1119/12; OFS/fresh not stated in the prompt | Correct run: 1065/1119/12, OFS 0, fresh 3,021,300; inverted run: OFS 3,021,300, fresh 0 |
| Revenue CAGR | +15.79% | +15.7889% |
| ROCE | 10.76 | 10.76 |
| CFO/PAT | 2.62 | 2.6206 |
| Available / unknown | 46 / 54 | 46 / 54 (both runs) |
| Verdict | INSUFFICIENT_DATA | INSUFFICIENT_DATA (both) |
| Final score | 21 | **29** (correct structure) / **21** (inverted structure) |

### 3.2 The 29 reproduction (CONFIRMED)

Command: `PYTHONPATH=engine ./.venv/bin/python /tmp/reproduce_jio.py 3021300 0 correct`

| Output | Value |
|---|---|
| Evaluation id / result hash | `JIO-PLATFORMS-LIMITED-20261019-132115Z-final-9b662f7c` / `9b662f7cc9c8a0dfd064b645c41419a5978415beddd43e958b613e8367c662a3` (run-sensitive via snapshot capture timestamps; see §3.7) |
| Final / base / penalties | 29.0 / 29.0 / 0.0 |
| Caps | none |
| Available / unknown / completeness | 46 / 54 / 46.0% |
| Confidence / verdict | Low / INSUFFICIENT_DATA |
| Modules | A 13/25, B 0/20, C 11/15, D 5/15, E 0/15, F 0/10 |
| Module C | fresh_share 3 (100%), ofs_seller_type 2 (`none_or_small`), promoter_ofs_pct 2 (0%), dilution 1 (true), use_of_proceeds UNKNOWN, pre_ipo 2, lockin 1 |
| Issue block | price 1065/1119, lot 12, ofs 0.0, fresh 3,021,300.0, fresh_shares 270,000,000, post_issue_shares 9,209,030,830; reporting unit `INR_MILLIONS` |
| Penalties | margin 0, receivable 0, auditor UNKNOWN, discounted 0 (default false), unreconciled UNKNOWN, regulatory UNKNOWN, eom UNKNOWN; applied 0; unresolved 10; lower bound 19 |
| Missing rows | 31 (16 criteria + 3 knockouts + 4 market + 4 penalties + 4 critical) |

This matches the previously published 29/100 on all nine dimensions (score, verdict, confidence, available, unknown, missing count, CAGR, module totals, and the A/C/D split).

### 3.3 The 21 reproduction (CONFIRMED)

Command: `PYTHONPATH=engine ./.venv/bin/python /tmp/reproduce_jio.py 0 3021300 inverted`

| Output | Value |
|---|---|
| Evaluation id / result hash | `JIO-PLATFORMS-LIMITED-20261019-132157Z-final-8b151c83` / `8b151c83c9383ba442164e4c2804977901254d82bd167ad201fbadf98c5e9086` |
| Final / base / penalties | **21.0** / 21.0 / 0.0 |
| Caps | **`pure_ofs` max_score 60** |
| Available / unknown / completeness | **46 / 54 / 46.0%** |
| Confidence / verdict | Low / INSUFFICIENT_DATA |
| Lower / upper | 11 / 60 |
| Modules | A **13**, B **0**, C **3**, D **5**, E 0, F 0 |
| Module C | fresh_share **0** (0.0%), ofs_seller_type **UNKNOWN**, promoter_ofs_pct **UNKNOWN**, dilution **0 (`zeroed_by pure_ofs`)**, use_of_proceeds **0 (`zeroed_by pure_ofs`)**, pre_ipo 2, lockin 1 |
| Missing rows | 32 |

Every headline number matches the Windows Jio scorecard exactly: 21, 46 available, 54 unknown, Low 46%, INSUFFICIENT_DATA, +15.79% CAGR, ROCE 10.76, CFO/PAT 2.62. The pure-OFS cap also predicts a **ceiling of 60** on the Windows scorecard; if the Windows card shows `Ceiling 60`, the inversion is confirmed without further reading.

### 3.4 The complete eight-point bridge

| Component | Correct structure (29) | Inverted structure (21) | Delta | Why |
|---|---:|---:|---:|---|
| A Financial Quality | 13 | 13 | 0 | Same financial periods/metrics |
| B Valuation | 0 | 0 | 0 | Peg 0/4; peers/sector absent in both |
| C `fresh_share` | 3 | 0 | **−3** | `fresh = 0` ⇒ band `else` = 0 |
| C `ofs_seller_type` | 2 (SCORED) | 0 (UNKNOWN; max 2) | **−2** | OFS present, sellers not supplied |
| C `promoter_ofs_pct` | 2 (SCORED 0%) | 0 (UNKNOWN; max 2) | **−2** | Same |
| C `dilution` | 1 | 0 (`zero_if pure_ofs`) | **−1** | Pure-OFS configuration zero |
| C `use_of_proceeds` | 0 (UNKNOWN) | 0 (`zero_if pure_ofs`) | 0 | Unknown becomes a scored zero; score unchanged |
| C `pre_ipo_placement` | 2 | 2 | 0 | Defaulted in both |
| C `lockin` | 1 | 1 | 0 | Defaulted in both |
| D Promoter & Governance | 5 | 5 | 0 | Same |
| E + F | 0 | 0 | 0 | Same |
| Applied penalties | 0 | 0 | 0 | Same |
| **Base / final** | **29** | **21** | **−8** | |

**Availability invariance (the fingerprint):** correct C available = 3+2+2+1+2+1 = 11 (uop unknown 4); inverted C available = 3+0+0+1+4+2+1 = 11 (seller+promoter unknown 4; uop scored-zero 4). Therefore available stays 46 and unknown stays 54 even though four criteria changed state. No other combination of issue terms reproduces 21 with 46/54 and the pure-OFS cap. The inversion is **uniquely determined**.

**Falsifiability:** this bridge is falsified if the Windows `input.json` shows `fresh_issue > 0` and `ofs = 0`. In that case the 8 points must come from a source not reproduced here — a different applied penalty total, or a different Module A/C/D band — and the record's `penalties[]` and module table decide. No such alternative is consistent with the reported +15.79%/10.76/2.62 metrics and 46/54 availability in the reproduction; the Windows read commands are in §8.

**What this means:** the discrepancy is **not** an extraction difference, not a scoring difference, and not a financial-metric difference. It is an `issue.fresh_issue`/`issue.ofs` data difference in the Windows evaluation. The correct structure from the RHP is fresh-only (OFS "Not applicable", p1; fresh 270,000,000 shares; OFS amount not applicable). The record will show which side was inverted; the two governed possibilities are:
- the operator entered `fresh_issue = 0` and `ofs > 0` (the entered amount) (an operator-entry inversion), or
- a pathway wrote the two canonical fields in the wrong direction (a mapping defect).
Both are distinguished by comparing the manual submission audit values with the canonical `input.json`; the command is in §9.

### 3.5 Source validation of the corrected Jio values (CONFIRMED)

| Metric | Source (page) | Raw values | Calculation | Result |
|---|---|---|---|---|
| Revenue FY2026/25/24 | RHP p76, "Summary of restated consolidated statement of profit and loss", `(in ₹ million)`; five columns newest-first: 3M Jun-26, 3M Jun-25, FY26, FY25, FY24 | 1,468,853 / 1,282,184 / 1,095,581 | `(1468853/1095581)^(1/2) − 1` | **+15.7889%** |
| Corroboration | RHP p128 | "grew at a CAGR of 15.79% … between Fiscal 2024 and Fiscal 2026" | — | matches |
| CFO FY26/25/24 | RHP p77, "Net Cash Flow from Operating Activities (A)" | 775,563 / 681,557 / 576,616 | `(775563+681557+576616)/(300527+261203+214340)` | **2.6206** |
| ROCE FY26 | RHP p132, "Return on Average Capital Employed" KPI | 10.76% (FY26), 12.50% (FY25), 12.83% (FY24) | disclosed value takes precedence | **10.76** |
| Net worth | RHP p75 | no "Total Equity" subtotal; "Total Equity and Liabilities" 6,155,940 = total assets | must not be used as net worth | **UNKNOWN** (correct) |
| Total debt | RHP p75 | Borrowings non-current 514,548 + current 193,262 | sum | **707,810** (₹ million) |
| Unit | RHP p75–77 headers | `(in ₹ million, unless otherwise specified)` | detected | **INR_MILLIONS** |
| OFS | RHP p1 cover table | "Not applicable" | filing-established | **0.0** |
| Fresh shares | RHP p1 | up to 270,000,000 | filing-established | **270,000,000** |
| Fresh amount | RHP p1 | `₹[●] million` | placeholder → **not invented**; supplied manually | **3,021,300** (submitted; see §3.6) |
| UoP | RHP p116/p122 | Net Proceeds; GCP `[●]` | GCP unknown ⇒ bucket UNKNOWN | **UNKNOWN** (correct) |
| Litigation | RHP p464 | Company: criminal/regulatory/civil **Nil**; subsidiaries: criminal proceedings (RJIL) | group-level bucket | **criminal_or_regulatory** (evidence-supported) |
| Auditor | RHP p321 | "Independent Auditor's Examination Report on Restated Consolidated Financial Information" | not a canonical audit opinion taxonomy | **UNKNOWN** (correct) |
| Peer table | RHP p129–131 | Face value, Revenue FY26, EPS basic/diluted, P/E, RONW, NAV; Bharti Airtel P/E 40.71, RONW 20.32%, NAV 244.60; Vodafone Idea revenue 448,730; Company P/E `[●]`; P/E as of 13 Oct 2026 (footnote 4) | a **third layout** not among the two recognised signatures; listed-years and authoritative as-of metadata are not established | **no peers** (fail-closed) |

**Evidence linkage in the reproduced record (read back from the persisted store):**

| Field | Evidence id | Source id | Method | Page |
|---|---|---|---|---|
| Financial periods (revenue/PAT/CFO/ROCE inputs) | `EV-financials-periods` | `RHP-FILING-72480c2e` (content hash of the committed PDF) | DETERMINISTIC_PDF | 76 (the disclosed ROCE KPI itself is on p132; see the provenance caveat below) |
| Reporting unit | `EV-financials-reporting_unit` | `RHP-FILING-72480c2e` | DETERMINISTIC_PDF | 76 |
| `issue.ofs` | `EV-issue-ofs` | `SRC-MANUAL-ENTRY` | MANUAL_ENTRY (unverified) | 1 (filing) / manual |
| `issue.fresh_shares` | `EV-issue-fresh_shares` | `RHP-FILING-72480c2e` | DETERMINISTIC_PDF | 1 |
| `issue.ofs_sellers` | `EV-issue-ofs_sellers` | `RHP-FILING-72480c2e` | DETERMINISTIC_PDF | 1 |
| `governance.litigation_bucket` | `EV-governance-litigation_bucket` | `RHP-FILING-72480c2e` | DETERMINISTIC_PDF | 464 |
| `governance.sebi_ed_action_active` | `EV-governance-sebi_ed_action_active` | `RHP-FILING-72480c2e` | DETERMINISTIC_PDF (defaulted value; see §4.2) | 464 |
| `capital_structure.promoter_post_pct` | `EV-capital_structure-promoter_post_pct` | `RHP-FILING-72480c2e` | DETERMINISTIC_PDF | 99 |
| `governance.board_independent_majority` | `EV-governance-board_independent_majority` | `RHP-FILING-72480c2e` | DETERMINISTIC_PDF (defaulted value; see §4.2) | 290 |

**Provenance caveat:** the financial-periods item is a single aggregated evidence record; the disclosed ROCE (p132) is carried into the periods but the evidence page shown is 76. That is sufficient for the value but weaker than a per-field citation. It is recorded here as a provenance-quality observation, not a value defect. The `sebi_ed_action_active` and `board_independent_majority` items illustrate the favorable-default/fabricated-quote finding in §4.2.

### 3.6 The corrected financial-extraction defects — verification

| # | Defect | Evidence | Correction at `950d239` | Verified in Arena |
|---|---|---|---|---|
| 1 | Interim columns selected as fiscal years | p76: 391,729 (3M Jun-26) / 350,323 (3M Jun-25) / 1,468,853 (FY26) …; pre-fix CAGR −48.36% = (391,729/1,468,853)^0.5 − 1 | `nums[-n_cols:]` fiscal-block selection | **Yes** — correct run gives 29 and +15.7889% |
| 2 | `net_worth` matched "Total Equity and Liabilities" (= total assets) | p75 has no total-equity subtotal | `total equity(?! and liabilit)` | **Yes** — net worth stays UNKNOWN |
| 3 | CFO row label "Net Cash Flow from Operating Activities" unmatched | p77 | added label | **Yes** — CFO 775,563 |
| 4 | Plain "Borrowings" rows unmatched | p75 | non-current + current captured | **Yes** — total debt 707,810 |
| 5 | "Depreciation and Amortisation" (British spelling) unmatched | p76 | `amorti[sz]ation` | code-verified |
| 6 | ROCE KPI "Return on Average Capital Employed" wrapped/missed | p132 | label + wrap join + fiscal columns | **Yes** — ROCE 10.76 |
| 7 | `(in ₹ million)` not detected, defaulted to INR_LAKHS | p75–77 | unit forms added | **Yes** — `reporting_unit = INR_MILLIONS` |

**Independent CAGR check:** the RHP itself states 15.79% (p128); the exact arithmetic on the fiscal columns gives 15.7889%. The reported −48.36% is the correct formula over the wrong columns, not a genuine decline, not a formula error, not a unit error, and not a standalone/consolidated mix.

### 3.7 Unit consistency of the submitted fresh amount

`issue.fresh_issue` is a monetary amount **in the filing's reporting unit**. For this filing the unit is `INR_MILLIONS` (₹ million). The operator's value 3,021,300 (reproduced exactly) equals ₹3.0213 trillion — **10×** the issue size implied by the broker/GMP record (₹30,213 crore = ₹302,130 million) and 10× the value that the filing's own price band × fresh shares implies (270,000,000 × ₹1,065–1,119 = ₹287,550–302,130 million). It is the same number expressed in **lakh** (₹30,213 crore = 3,021,300 lakh), i.e. a unit/entry mismatch, not a parser value.

- **Score effect: none.** Module C uses the fresh/OFS **ratio** (100% for any fresh > 0 with OFS 0); the amount itself is not a band input.
- **Data-correctness effect: material.** The persisted amount is 10× the filing-consistent amount and must not be used for any amount-based comparison or display without correction. A cross-field plausibility check (fresh amount vs fresh shares × price band, in the same unit) is recommended; it must be a validation/flag, not a derivation, and it must not fabricate the amount.
- **Not a substitute for evidence:** the corrected evaluation should either use the stated amount from the final Prospectus or a manual value explicitly re-based to the displayed reporting unit.

### 3.8 Module-by-module Windows-versus-Arena comparison

| Module | Windows 21 | Arena 29 (correct structure) | Arena 21 (inverted structure) | Difference explained |
|---|---:|---:|---:|---|
| A | 13 | 13 | 13 | None: CAGR 4, margin 3, ROCE 1, CFO 5; leverage UNKNOWN |
| B | 0 | 0 | 0 | None: peers absent; peg 0/4; sector absent |
| C | **3** | **11** | **3** | Four criteria; see §3.4 |
| D | 5 | 5 | 5 | None: promoter 4, litigation 0, board 1 (default) |
| E | 0 | 0 | 0 | None |
| F | 0 | 0 | 0 | None |
| Penalties | 0 | 0 | 0 | None applied; four UNKNOWN carried in the lower bound |
| **Final** | **21** | **29** | **21** | **−8 = C only** |

**Conclusion:** the eight-point difference is fully explained and reproducible. It is an issue-term direction defect, not the financial extraction correction. The financial correction explains the earlier 19 → 29 movement (CAGR −48.36 → +15.79, A 3 → 13); the 29 → 21 movement is the pure-OFS inversion.

---

## 4. PART C — Cross-cutting audit

### 4.1 First failing stage for each material field

| Field / item | Value/status | First failing stage | Classification | Confidence |
|---|---|---|---|---|
| Jio `issue.fresh_issue` / `issue.ofs` (21 vs 29) | 0 / >0 in the 21 record; 3,021,300 / 0 in the correct record | Canonical issue-term assembly (manual entry or pathway) | **Wrong canonical value** (direction inversion) — operator-entry or mapping; distinguished by the audit values | CONFIRMED numerically; Windows record required for the exact source |
| Jio `fresh_issue` unit | 3,021,300 in INR_MILLIONS | Manual entry / unit labelling | Unit mismatch (10×) | CONFIRMED |
| Jio financial periods/unit/ROCE/CFO | Correct at `950d239` | Extraction (pre-fix) | **Corrected** | CONFIRMED |
| Jio net worth | UNKNOWN | Extraction/source | Genuine stated-row absence; cross-section sourcing not authorized | CONFIRMED |
| Jio peers | UNKNOWN | Peer extraction (layout coverage) | Evidence discovered but not parsed (third layout); metadata (listed years/as-of) not established | CONFIRMED code; source page verified |
| Jio RPT | UNKNOWN | Canonical input (no stated % of revenue) | Missing governed input; derivation contract requires a stated/derived definition | CONFIRMED |
| Jio auditor | UNKNOWN | Extraction taxonomy | Document class (examination report) does not map to the canonical opinion taxonomy | CONFIRMED |
| Jio UoP | UNKNOWN | Source (`GCP [●]`) | Genuine source placeholder; fail-closed | CONFIRMED |
| Jio market blocks | MISSING | Source collection (evaluation before bidding) | Genuine external absence; as-of correct | CONFIRMED |
| HD Fire `margin_trend`/`roce`/`cfo`/`leverage` | UNKNOWN | Extraction (suspected) | Extraction gap — not proved without the filing | SUSPECTED |
| HD Fire `ofs` filing value | 0 (wrong) → manual 71,231 | Extraction (NIL-OFS binding) | Wrong-clause binding, corrected | CONFIRMED code; HD Fire occurrence strongly indicated |
| HD Fire `ofs_seller_type`/`promoter_ofs_pct` | UNKNOWN | Extraction/source | Seller list not supplied/parsed; must remain unknown | UNRESOLVED (Windows) |
| HD Fire `board_kmp` | `other` 1/2 | Canonical input defaults | Unsupported favorable default | CONFIRMED code |
| HD Fire `pre_ipo_placement` | `none_or_near_ipo` 2/2 | Canonical input defaults | Unsupported favorable default (empty list) | CONFIRMED code |
| HD Fire `lockin` | `intact` 1/1 | Extraction or default | Evidence status must be read from the record | UNRESOLVED (Windows) |
| HD Fire `promoter_post_holding` | 100% 4/4 | Extraction | Extracted; source page needed | UNRESOLVED (Windows) |
| HD Fire `litigation` | `criminal_or_regulatory` 0/4 | Extraction | Extracted bucket; exact proceeding needed | UNRESOLVED (Windows) |
| HD Fire K2 | CLEAR | Canonical input defaults | **UNKNOWN silently converted to CLEAR** | CONFIRMED code |
| HD Fire K1/K3/K5/K6 | UNVERIFIED | Missing inputs | Correct fail-closed | CONFIRMED arithmetic |
| HD Fire peer rows | schema violation | Peer extraction (pre-fix) | Wrong-field mapping / placeholder collapse; corrected | CONFIRMED code class; raw cells Windows-only |
| HD Fire market blocks | MISSING | Source collection | Genuine external absence (pre-bid) | CONFIRMED arithmetic |

### 4.2 Unknown-data governance review

**Correct in the scoring layer (verified):**
- `scoring.py` defines `SCORED` / `UNKNOWN` / `NOT_APPLICABLE` / `EXCLUDED_BY_MODE`; UNKNOWN contributes 0 to the base but its full max to the upper bound and is excluded from the confidence numerator; NOT_APPLICABLE is excluded from both.
- Unknowns never silently become zero in derived metrics: `derived.py` returns typed UNKNOWN with a reason (e.g., `fresh_share_pct`, `cfo_pat_cumulative`, `leverage_bucket`, `receivable_days_yoy_pct`).
- Explicit zero is accepted only where the contract makes it meaningful (e.g., `issue.ofs = 0` from a filing "Not applicable", `fresh_issue = 0` from an operator pure-OFS statement), and provenance distinguishes FILING / MANUAL_ENTRY / DERIVED.
- Confidence and available/unknown points use point weighting; penalty criteria are excluded from the positive denominator.
- Peer data is rejected with named diagnostics; issue terms fail closed with `AWAITING_ISSUE_TERMS`; a manual value is never labelled official.

**Violations found (the material integrity finding):**
1. **Builder favorable defaults:** `litigation_bucket="clean"`; `sebi_ed_action_active=False`; `board_independent_majority=False`; `kmp_exits_2y=0`; `promoter_pledge_pct=0.0`; `promoter_lockin_in_place=True`; `large_holders_unlocked_early=False`; `discounted_allotments_18m_before_drhp=False`; `pre_ipo_placements=[]`. These are used when the filing/reference does not establish the field. They make K2 CLEAR, board KMP "other", lock-in "intact", the discounted penalty "not triggered", and pre-IPO "none" — without evidence. The golden fixture relies on several of these defaults, so changing them **changes the frozen golden result hash**. This is a governed re-baseline decision, not a silent code change.
2. **Extractor defaults with fabricated/synthesized quotes:** `governance.sebi_ed_action_active` is emitted as `False` with the quote "No active SEBI or ED regulatory proceedings" even when no such text was matched (the quote is not marked `quote_is_processing`). `litigation_bucket` defaults to `"clean"` with a processing quote. `board_independent_majority` defaults to `False` with a processing quote. These violate "evidence before score" and the Workstream-2 rule that synthesized text must be marked as processing, not presented as a quotation.
3. **Pre-IPO placement ambiguity:** an empty `pre_ipo_placements` cannot distinguish "none disclosed" from "not extracted". The schema requires an array, so a governed input-contract decision (e.g., an explicit `pre_ipo_placements_disclosed` flag) is required; no value is invented here.
4. **NIL-OFS binding:** a false explicit zero was possible; corrected in this session.
5. **Missing list includes NOT_APPLICABLE rows:** `build_missing_unverified_rows` emits NOT_APPLICABLE criteria in the same list as UNKNOWN criteria (state retained, points 0), so a "missing" count can include genuinely inapplicable items. The state is preserved, so this is a presentation/semantics gap, not a data-loss defect. It does not affect the HD Fire or Jio counts reconstructed here (neither has N/A criteria in the missing set).

**Not changed in this session:** the favorable-default cluster and the golden-dependent behaviour. They are documented as the top remediation and require an explicit decision because fixing them changes the golden result hash and the published score/knockout baseline.

### 4.3 Peer extraction (Jio/HD Fire)

- The correction's contract is sound: recognised layouts only, placeholder-preserving alignment, strict width, prose rejection, no peers for unknown layouts, named early rejection.
- **Coverage gap:** the Jio p129–131 peer table is a valid third layout (Face value, Revenue, P/E, RONW, NAV) that the two recognised signatures do not match. Emitting no peers is correct fail-closed behaviour, but it leaves Module B at 0/20. Adding the layout requires an authoritative peer as-of/listed-years contract; the document's footnote provides an as-of (13 Oct 2026) but not listed years. Do not hard-code the metadata.
- **HD Fire raw cells:** not available in Arena. The 26957.28/21700.34 values are consistent with the demonstrated column-shift/positional-mapping mechanisms but cannot be attributed to one mechanism without the raw row. Windows command in §9.

---

## 5. Deliverable 5 — Root-cause-ranked remediation plan

Ranking criteria: (1) financial/governance correctness; (2) score/knockout effect; (3) false-assurance risk; (4) number of IPOs affected; (5) independent testability.

### P0 — Confirmed integrity defects ready for implementation

| Rank | Defect | Effect | Fix | Decision needed? |
|---|---|---|---|---|
| 1 | **Favorable canonical-input defaults** (`litigation=clean`, `sebi=False`, `board_independent=False`, `kmp_exits=0`, `pledge=0`, `lockin=True`, `large_holders_unlocked=False`, `discounted=False`, `pre_ipo=[]`) | Clears K2, awards board KMP/pre-IPO/lock-in points and suppresses the discounted penalty without evidence; affects every uploaded filing; explains part of HD Fire's 7 and Jio's 29 | Set the fields to `None` when no evidence; make `pre_ipo` explicitly disclosed/unknown via a contract decision. Apply only after the golden re-baseline (the golden fixture relies on the defaults; changing them changes `e84f8bc0…`) | **Yes — golden re-baseline + schema decision for pre-IPO** |
| 2 | **K2 CLEAR on defaults** | A knockout resolved CLEAR with no evidence — the spec's forbidden conversion | Follows from #1; K2 becomes UNVERIFIED when pledge/SEBI are unknown | Yes (same decision) |
| 3 | **Extractor emits favorable defaults with fabricated quotes** (`sebi_ed_action_active` false + "No active SEBI or ED regulatory proceedings"; litigation clean; board majority false) | False evidence/assurance in the record; affects every filing without a match | Emit nothing when the text is not found; mark any synthesized wording as PROCESSING_SUMMARY; tie the default to explicit "no …" language only | Yes for the score effect; the quote-marking fix is independently safe |
| 4 | **Penalty inputs dropped by the builder** (`governance.auditor_or_cfo_exit_2y`, `financials.adjusted_metrics_unreconciled`) | The auditor/CFO and unreconciled penalties were structurally UNKNOWN for every builder-based evaluation; a correct input value was lost between stages | Implemented: conditional passthrough; absent stays UNKNOWN; golden input unchanged | No — implemented |
| 5 | **NIL-OFS wrong-clause binding** | Fabricates an explicit `issue.ofs = 0` (HD Fire's conflict) | Implemented in this session with focused regressions | No — implemented |
| 6 | **Penalty state/reason presentation** | A 0-point UNKNOWN looks like "cleared"; enabled the Gemini misattribution | Implemented: `reason` projected; UI shows UNKNOWN-carried vs not-triggered | No — implemented |

### P1 — Additional investigation / narrowly scoped work

| Rank | Item | Why | Next |
|---|---|---|---|
| 7 | HD Fire financial extraction re-run at `e1df89b` | Margin/ROCE/CFO/leverage unknowns may be the same Jio-class extraction defects | Re-upload the filing; compare A and the missing rows; no code change until proved |
| 8 | Jio issue-term inversion guard | Prevents a repeat of the 21 path; the existing OFS conflict is confirmed but the fresh/OFS pair is not cross-checked | Add a generic consistency warning when filing-established fresh shares/OFS 0 contradict a manual pure-OFS pair; preserve the conflict-confirmation governance |
| 9 | Manual monetary unit plausibility | The Jio fresh amount is 10× the unit-consistent amount | Range-check against fresh shares × price band in the same unit; warn (not derive) |
| 10 | Jio peer layout | A valid peer table exists; Module B is 0/20 | Add an evidence-anchored layout signature + an authoritative as-of/listed-years decision |
| 11 | HD Fire seller composition | OFS sellers are the core of the governance analysis | Retrieve the "Offer for Sale"/"Selling Shareholders" pages and re-run; never infer zero |
| 12 | HD Fire litigation record | The `criminal_or_regulatory` bucket must be traceable | Identify the exact proceeding/subject/status; keep the 0/4 if valid |

### P2 — External evidence or governed human assessment

| Item | Blocker |
|---|---|
| HD Fire RHP and Windows evaluation record | Not in Arena; operator must export/read it |
| Jio final Prospectus (stated fresh amount, official terms) | External official source; the RHP has placeholders |
| Peer as-of/listed-years contract | Governance decision; document gives an as-of but not listed years |
| Net worth cross-section sourcing | Governance decision; the statements have no total-equity subtotal |
| Auditor opinion taxonomy vs examination report | Governance decision; the document class is not a statutory audit opinion |
| Industry CAGR scope/period/source | A single designated statement is required; the RHP has multiple CAGRs |
| RPT % of revenue | Requires a stated/derived definition; model/visibility require recorded assessments |
| Market blocks (GMP/subscription/regime) | Genuinely unavailable at the evaluation timestamp; a later evaluation is required |

### P3 — Do not repeat / explicitly not done

- Do not merge PR #6, rewrite `main`, or rewrite any historical evaluation.
- Do not clamp, scale or "fix" the HD Fire peer values in place; reject and re-upload.
- Do not substitute a peer median, post-issue EPS, fresh amount, GMP or subscription value.
- Do not change scoring weights, thresholds, formulas, knockout semantics or penalties.
- Do not mark K2 CLEAR, seller composition, or promoter OFS as zero without evidence.

---

## 6. Deliverable 6 — Tests and regression evidence

### 6.1 Baseline (before this session's changes)

| Command | Result |
|---|---|
| `PYTHONPATH=engine ./.venv/bin/python -m pytest tests/ -q` | See §6.4 (final execution) |
| `cd frontend && npm test` | See §6.4 |
| `pytest tests/test_vishal_golden.py -q` | Golden result `e84f8bc0…` preserved |
| Focused Jio reproduction (real RHP) | 29 with correct structure; 21 with inverted structure |
| Full RHP source reads | p75/76/77/128/132/464/120/116 confirmed the values in §3.5 |

### 6.2 New regressions added by this session

1. **OFS NIL binding** (`tests/test_ofs_nil_binding.py`): the exact pure-OFS false positive (`Fresh Issue / NIL`, `Pre-IPO Placement / NIL`, `Promoter Group / NIL`), the amount-on-the-label-line case, the same-line positive, the Jio two-column positive, and the real Jio cover pin. Both the correct and the incorrect cases are asserted; the fix must not turn a stated OFS amount into a zero.
2. **Penalty attribution** (`tests/test_penalty_attribution.py`):
   - receivable days up >30% + auditor flag false ⇒ the −3 is `receivable_days_up`; `auditor_cfo_exit` is 0/not-triggered;
   - receivable flat + auditor flag true ⇒ the −3 is `auditor_cfo_exit`; receivable is 0;
   - auditor flag absent ⇒ UNKNOWN, 0 applied, carried in the lower bound;
   - the total cannot exceed the configured floor and no item's points can appear under another id.
3. **Jio score bridge** (`tests/test_jio_score_bridge.py`): one real-RHP extraction, two evaluations differing only in the issue structure; asserts 29/C 11 vs 21/C 3, available 46/54 invariant, pure-OFS cap, and the exact four-criterion delta. `@pytest.mark.slow`.
4. **Penalty presentation** (`tests/test_penalty_presentation.py` + one frontend assertion): the API projects `state`/`reason`; an UNKNOWN item renders "carried in range", a zero SCORED item renders "not triggered"; historical records are read-only.

### 6.3 Golden / historical invariants

- No scoring file, config weight, threshold, knockout, penalty rule or frozen-core file is changed by the NIL-OFS or presentation fixes.
- The golden fixture is untouched; the golden result hash and frozen-core verification are re-run and reported in §6.4.
- Historical evaluation records are not rewritten; the new tests read records without mutating them.

### 6.4 Executed results

All results below were executed in this session; the exact command and the real exit status are recorded.

| When | Command | Result |
|---|---|---|
| Baseline before changes | `PYTHONPATH=engine ./.venv/bin/python -m pytest tests/ -q` | **1111 passed**, 0 failed, 35 warnings in 1400.11 s (23:20), exit 0. This reproduces the reported 1,111 backend count. |
| New extraction regressions | `pytest tests/test_ofs_nil_binding.py -q` | **9 passed** |
| New penalty attribution regressions | `pytest tests/test_penalty_attribution.py -q` | **5 passed** (the True-flag cases fail on the pre-fix builder, proving the mapping defect) |
| New presentation regressions | `pytest tests/test_penalty_presentation.py -q` | **3 passed** |
| New Jio bridge | `pytest tests/test_jio_score_bridge.py -q` | **1 passed** in 32.25 s (real RHP; 29 vs 21) |
| Golden + core semantics + extraction + peer | `pytest tests/test_ofs_nil_binding.py tests/test_penalty_attribution.py tests/test_penalty_presentation.py tests/test_vishal_golden.py tests/test_core_semantics.py tests/test_extraction.py tests/test_peer_row_mapping_and_bounds.py -q` | **90 passed** in 95.77 s; golden hash `e84f8bc0…` intact |
| Jio RHP + bridge + fresh-issue manual path | `pytest tests/test_jio_rhp_issue_terms.py tests/test_jio_score_bridge.py tests/test_fresh_issue_manual_entry.py -q` | **20 passed** in 177.21 s |
| R.K. Fashion + phase-5b reference filings | `pytest tests/test_rk_fashion_reconciliation.py tests/test_extraction_phase5b.py -q` | **14 passed** in 100.49 s |
| Frontend | `cd frontend && npm test` | **89 passed**, 0 failed (87 baseline + 2 new penalty-rendering tests) |
| Post-change full backend | `PYTHONPATH=engine ./.venv/bin/python -m pytest tests/ -q` | **1129 passed**, 0 failed, 36 warnings in 1490.59 s (24:50), exit 0. Baseline 1111 + 18 new focused tests (9 NIL-OFS + 5 attribution + 3 presentation + 1 Jio bridge). |

Frozen-core and golden verification are part of `test_vishal_golden.py` and the frozen-core tests in the 90-passed batch; the golden result hash is unchanged. No test result is reported as passing unless it was executed with exit status 0.

---

## 7. Deliverable 7 — Publication and remote state

- **Branch:** `arena/ae4d04e8-ipo-screening-engine`, based on the published `e1df89b` baseline.
- **Implementation commit:** `345caf75690fc67ade687592b2be5bfe8ae408d4` (this record, the extraction/builder/presentation corrections, the tests, the OpenAPI update and the tracker entry), followed by the docs-only publication amendment `568860ba2a5e06c4c5f9a8e61928f9b9e8b7a716`. Both were remote-verified; `git merge-base --is-ancestor` confirms `e1df89b`, `e05c0ef` (PR #6 head) and `01ba66c` (`main`) are ancestors.
- **PR #6:** remains **OPEN and UNMERGED**; head unchanged at `e05c0ef`; this session does not move, merge or close it. (Verified `state=OPEN`, `mergedAt=null`.)
- **`main`:** `01ba66c`, untouched (remote-verified).
- **CI:** no hosted workflows are configured; the executed local test matrix in §6.4 is the verification evidence.
- The publication amendment that follows this record is a docs-only commit on the same branch.

---

## 8. Windows-side verification (exact commands)

Arena cannot read the Windows store. The following PowerShell reads the exact evidence needed to close the remaining Windows-only items; nothing is modified.

```powershell
cd C:\path\to\ipo-screening-engine
$env:PYTHONPATH = "$PWD\engine"
$store = ".\build\evaluations"   # adjust to the operator's store root if different

# 1) Locate the HD Fire and Jio evaluations and print the identity block.
Get-ChildItem $store -Directory | ForEach-Object {
  $e = Get-Content (Join-Path $_.FullName "evaluation.json") -Raw | ConvertFrom-Json
  [pscustomobject]@{ id=$e.evaluation_id; ipo=$e.ipo_id; mode=$e.evaluation_mode;
    score=$e.score.final_score; base=$e.score.base_score; penalties=$e.score.penalties_total;
    available=$e.score_range.available_points; unknown=$e.score_range.unknown_points;
    lower=$e.score_range.lower_bound; upper=$e.score_range.upper_bound;
    confidence=$e.confidence.level; verdict=$e.verdict.verdict; hash=$e.result_hash }
} | Format-Table -AutoSize

# 2) HD Fire penalties and the 36 missing rows.
$hd = Get-ChildItem $store -Directory | Where-Object { (Get-Content (Join-Path $_.FullName "evaluation.json") -Raw) -match "HD-FIRE" } | Select-Object -First 1
$r = Get-Content (Join-Path $hd.FullName "result.json") -Raw | ConvertFrom-Json
$r.penalties | Format-Table id,points,state,reason -AutoSize
$r.missing_unverified | Format-Table category,item,state,points_affected,detail -AutoSize
$r.missing_unverified.Count

# 3) HD Fire canonical issue structure and evidence presence.
$inp = Get-Content (Join-Path $hd.FullName "input.json") -Raw | ConvertFrom-Json
$inp.snapshot.input.issue | Format-List price_band_low,price_band_high,lot_size,fresh_issue,ofs,fresh_shares,post_issue_shares
$inp.snapshot.input.capital_structure | Format-List *
$inp.snapshot.input.governance | Format-List *
$inp.snapshot._evidence.PSObject.Properties.Name | Sort-Object

# 4) Jio: the canonical issue block and the manual submission values.
$jio = Get-ChildItem $store -Directory | Where-Object { (Get-Content (Join-Path $_.FullName "evaluation.json") -Raw) -match "JIO" } | Select-Object -First 1
$j = Get-Content (Join-Path $jio.FullName "input.json") -Raw | ConvertFrom-Json
$j.snapshot.input.issue | Format-List price_band_low,price_band_high,lot_size,fresh_issue,ofs,fresh_shares,post_issue_shares
# Audit log: the submitted values and the evaluation/persistence chain
Get-ChildItem .\build\ingestions -Recurse -Filter activity.jsonl |
  Select-String '"manual_submission"|"manual_entry"|"evaluation"|"persistence"' |
  ForEach-Object { $_.Line } | Select-Object -Last 20

# 5) HD Fire raw peer rows (the unresolved cell question).
Get-Content (Join-Path $hd.FullName "input.json") -Raw | ConvertFrom-Json |
  Select-Object -ExpandProperty snapshot | Select-Object -ExpandProperty input |
  Select-Object -ExpandProperty peers | Format-List name,pe,pb,roe_pct

# 6) HD Fire cap/floor/ceiling and the penalty attribution in the scorecard.
$r.score | Format-List final_score,base_score,penalties_total,caps_applied
$r.score_range | Format-List lower_bound,upper_bound,available_points,unknown_points
```

**What each answers:**
- Step 2 confirms the four UNKNOWN penalty rows (`auditor_cfo_exit`, `unreconciled_metrics`, `regulatory_dependence`, `eom_caro`) and the exact 36 items; `auditor_cfo_exit` is necessarily UNKNOWN because the pre-fix builder dropped its flag.
- Step 3/5 resolves whether the 100% promoter holding and 4/4, the lock-in 1/1, the board KMP 1/2 and the criminal litigation bucket are extracted or defaulted, and identifies the raw HD Fire peer cells.
- Step 4 resolves which Jio issue field was inverted and whether the audit values agree with the canonical input.

**Re-run acceptance (after the fixes):**
1. Update to the published session commit; restart the API.
2. Upload the HD Fire RHP once. Expected governed outcomes: (a) evaluation completes with source-true values and an explicit peer diagnostic if the peer rows are genuinely out of contract, or (b) early named rejection — never a silent clamp. The OFS conflict must surface with `existing 0` vs `manual 71231`; confirming it must keep `MANUAL_ENTRY`/`UNVERIFIED`.
3. Upload the Jio RHP with the filing-established structure (price 1065/1119, lot 12, OFS 0, fresh amount in the displayed unit). Expected: a new evaluation with the correct Module C, not the pure-OFS path; the old 21 record remains immutable.
4. Confirm the scorecard shows the penalty state/reason (`UNKNOWN — carried in range` vs `Not triggered`).

---

## Appendix A — HD Fire field reconciliation table

Status legend: **S** = SCORED, **U** = UNKNOWN, **Z** = scored zero by `zero_if`, **N/A** = not applicable. "Reported" values are exact from the scorecard aggregates; "Source" is the expected RHP location; "Extracted" is what Arena can prove (the filing is absent, so most are `unverified`).

| # | Field | Module/rule | Reported value/status | Score/text | Expected source | Extracted? | Normalised? | Reached eval? | Cause class | Evidence to close |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | `revenue_cagr` | A / `revenue_cagr_2y_from_3fy` | 14.54% **S** | 2/6 | Restated P&L, revenue FY24–FY26 | Value present in record; page unverified | — | Yes | Source value | RHP page/columns |
| 2 | `margin_trend` | A | **U** | 0/5 | Revenue + EBITDA + PAT | No | — | Yes | Extraction (suspected) | RHP statement pages |
| 3 | `roce` | A / `roce_latest` | **U** | 0/5 | Basis-for-Offer KPI or EBIT/equity+debt | No | — | Yes | Extraction (suspected) | KPI page |
| 4 | `cfo_quality` | A / `cfo_pat_cumulative` | **U** | 0/5 | Cash-flow statement CFO | No | — | Yes | Extraction (suspected) | Cash-flow page |
| 5 | `leverage` | A / `leverage_bucket` | **U** | 0/4 | Net worth + borrowings | No | — | Yes | Extraction/net-worth absence | Balance sheet |
| 6 | `pe_vs_peers` | B | **U** | 0/8 | Peer P/E + issue P/E | Rejected peers | — | Yes | Peer contract / source | Valid peers |
| 7 | `second_multiple` | B | **U** | 0/4 | Peer P/B/EV-EBITDA | No | — | Yes | Missing peer data | Valid peers |
| 8 | `peg` | B | **U** | 0/4 | Issue P/E + PAT CAGR | No | — | Yes | Missing issue EPS/price | EPS basis |
| 9 | `sector_ipo_relative` | B | **U** | 0/4 | Same-sector IPO comparables | No | — | Yes | Genuine external gap | Market source |
| 10 | `fresh_share` | C | 0.00% **S** | 0/3 | Issue terms | Yes (explicit zero) | Ratio | Yes | Correct | Filing page |
| 11 | `ofs_seller_type` | C | **U** | 0/2 | Offer for Sale/selling shareholders | No | — | Yes | Extraction/source | Seller list |
| 12 | `promoter_ofs_pct` | C | **U** | 0/2 | Shareholding + seller shares | No | — | Yes | Extraction/source | Shareholding table |
| 13 | `dilution` | C | **Z** | 0/1 | Pure-OFS config | n/a | n/a | Yes | Correct N/A-by-config | — |
| 14 | `use_of_proceeds` | C | **Z** | 0/4 | Pure-OFS config | n/a | n/a | Yes | Correct N/A-by-config | — |
| 15 | `pre_ipo_placement` | C | `none_or_near_ipo` **S** | 2/2 | Capital structure/pre-IPO | **No extractor** | n/a | Yes | **Defaulted** | Filing statement |
| 16 | `lockin` | C | `intact` **S** | 1/1 | Capital structure | Text-dependent | — | Yes | Extracted or defaulted | Evidence item |
| 17 | `promoter_post_holding` | D | 100% **S** | 4/4 | Shareholding table | Yes (not default) | % | Yes | Extracted; verify | Shareholding page |
| 18 | `litigation` | D | `criminal_or_regulatory` **S** | 0/4 | Litigation section | Yes | bucket | Yes | Extracted; verify | Exact proceeding |
| 19 | `rpt` | D | **U** | 0/3 | RPT note | No | — | Yes | Missing canonical input | RPT % |
| 20 | `auditor` | D | **U** | 0/2 | Auditor report | No | — | Yes | Taxonomy/document class | Opinion |
| 21 | `board_kmp` | D | `other` **S** | 1/2 | Board/KMP | **No extractor for inputs** | n/a | Yes | **Defaulted** | Board composition/KMP exits |
| 22 | `industry_growth` | E | **U** | 0/5 | Industry report | No | — | Yes | Scope/evidence | Designated CAGR |
| 23 | `moat` | E | **U** | 0/5 | Business section | No | — | Yes | Human assessment | Recorded rating |
| 24 | `concentration` | E | **U** | 0/3 | Customer/supplier concentration | No | — | Yes | Extraction/source | Top-5 % |
| 25 | `visibility` | E | **U** | 0/2 | Order book/capacity | No | — | Yes | Human assessment | Recorded rating |
| 26 | `anchor_quality` | F | **U** | 0/3 | Anchor block | No | — | Yes | Market block missing | Anchor data |
| 27 | `qib_subscription` | F | **U** | 0/3 | Subscription block | No | — | Yes | Market block missing | Subscription data |
| 28 | `gmp_trend` | F | **U** | 0/2 | GMP block | No | — | Yes | Market block missing | GMP data |
| 29 | `market_regime` | F | **U** | 0/2 | Regime block | No | — | Yes | Market block missing | Regime data |
| 30 | K1 | Knockout | **UNVERIFIED** | — | Auditor/going concern/net worth | No | — | Yes | Missing inputs | Three inputs |
| 31 | K2 | Knockout | **CLEAR (defaults)** | — | Pledge + SEBI/ED | Defaults | — | Yes | **False clear** | Pledge/SEBI evidence |
| 32 | K3 | Knockout | **UNVERIFIED** | — | OFS 100% + profit trend | OFS known; profit unknown | — | Yes | Missing profit trend | PAT periods |
| 33 | K4 | Knockout | **CLEAR (logic)** | — | Promoter post 100% | Value present | — | Yes | Correct if 100% is true | Shareholding page |
| 34 | K5 | Knockout | **UNVERIFIED** | — | Contingent liabilities/net worth | No | — | Yes | Missing inputs | Note + net worth |
| 35 | K6 | Knockout | **UNVERIFIED** | — | RPT growth | No | — | Yes | Missing input | RPT note |
| 36 | Penalty: `receivable_days_up` | Penalty | **−3 applied** | −3 | Receivables/revenue FY25–FY26 | Value present (trigger) | days | Yes | Correct attribution | Receivables pages |
| 37 | Penalty: `auditor_cfo_exit` | Penalty | 0 applied; **UNKNOWN** (builder dropped the flag) | 0 | Governance flag | No | — | Yes | Unknown carried (mapping defect, now fixed) | Resignation disclosure |
| 38 | Penalty: `unreconciled_metrics` | Penalty | 0 applied; **UNKNOWN** (builder dropped the flag) | 0 | `adjusted_metrics_unreconciled` | No | — | Yes | Unknown carried (mapping defect, now fixed) | Reconciliation disclosure |
| 39 | Penalty: `regulatory_dependence` | Penalty | 0 applied; **UNKNOWN** | 0 | Business flag | No | — | Yes | Unknown carried | Licence/price-control disclosure |
| 40 | Penalty: `eom_caro` | Penalty | 0 applied; **UNKNOWN** | 0 | EOM materiality | No | — | Yes | Unknown carried | Auditor report |
| 41 | Market blocks (4) | F | **MISSING** | — | Anchor/subscription/GMP/regime | No | — | Yes | Genuine absence | Later market evaluation |
| 42 | Critical data (4) | Verdict | **UNKNOWN** | — | Auditor/going concern/net worth/contingent | No | — | Yes | Missing inputs | Filing/evidence |

**Row-count note:** rows 1–29 + 30–35 (six knockouts) + 36–40 (five penalty rows) + 41 (four blocks) + 42 (four critical items) are *more* than 36 rows because the 36 list counts **only the missing/unverified members**: 20 criteria (rows 2–5, 6–9, 11–12, 19–20, 22–25, 26–29) + 4 knockouts (K1, K3, K5, K6) + **4** unknown penalties (rows 37–40; `receivable_days_up` is the applied one and is not a missing item) + 4 blocks + 4 critical = **36**. Scored fields (rows 1, 10, 13–18, 21, 36) and the two CLEAR knockouts (K2, K4) are included for the penalty/OFS reconciliation but are **not** part of the 36.

---

## Appendix B — Commands and reproduction record

```bash
# Durable reproduction: the correct structure (29) and the inverted structure (21)
PYTHONPATH=engine ./.venv/bin/python -m pytest tests/test_jio_score_bridge.py -q
# The investigation harness (not committed): the same two runs through
# PresentationService with manual terms; the summary JSON is quoted in §3.
# PYTHONPATH=engine ./.venv/bin/python /tmp/reproduce_jio.py 3021300 0 correct
# PYTHONPATH=engine ./.venv/bin/python /tmp/reproduce_jio.py 0 3021300 inverted

# Source reads (pypdf): p1, p75-77, p116-117, p120, p122, p128, p130-133, p321, p464
# PDF SHA-256: 72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d
```

**No claim is made that Arena inspected the Windows store, the HD Fire filing, the Windows browser, or the Windows API runtime.**
