# IPO Screening Engine — Specification v1.4

*Assumption: Indian mainboard IPOs (NSE/BSE), INR, SEBI ICDR framework. SME IPOs need stricter thresholds (see §9).*

## 1. Purpose

Convert an IPO's DRHP/RHP and market data into a **repeatable 0–100 score, a verdict, and a red-flag list** within hours of the price band announcement, so "apply / skip" decisions are rules-based, not hype-based.

## 2. Scope

**In scope:** mainboard IPOs (fresh issue, OFS, or mix); financial, valuation, governance, issue-structure, business and market-signal scoring; knockout rules; peer comparison; output report; post-listing tracking for back-testing.

**Out of scope (v1):** SME IPOs, REIT/InvIT, FPOs, rights issues, auto-bidding/order placement, tax advice, intraday listing-day trading signals.

## 3. Inputs Needed

| Group | Data | Source |
| --- | --- | --- |
| Issue | Price band, lot size, issue size, fresh vs OFS split, seller-wise OFS split (promoter / PE-VC / others) with % of each seller's holding sold, ICDR route (6(1) or 6(2)), employee/shareholder discounts, dates, anchor/QIB/NII/retail quota, lead managers, registrar | RHP, NSE/BSE, SEBI |
| Financials (3 FY + latest stub) | Revenue, EBITDA, PAT, net worth, debt, CFO, capex, receivable/inventory days, ROCE, ROE; sector metrics (CRAR/Tier 1, NIM, GNPA/NNPA, ROA for financials; order book, pre-sales/collections for EPC/real estate); reporting unit as stated | RHP restated financials |
| Capital structure | Pre/post-issue shareholding, promoter holding, pledges, pre-IPO placements, lock-ins | RHP |
| Use of proceeds | Breakdown: capex, debt repayment, WC, acquisitions, general corporate (GCP) | RHP |
| Governance | Promoter profile, board, KMP changes, auditor remarks, litigation table, related-party transactions, SEBI/ED/tax actions | RHP risk factors, litigation section |
| Business | Segments, customer/supplier concentration, geography, capacity utilisation, order book | RHP |
| Peers | 4–6 listed peers: P/E, EV/EBITDA, P/B, P/S, ROCE, growth | Screener, exchange data |
| Market signals | Anchor investor list and size, live subscription (QIB/NII/Retail), GMP (unofficial), Nifty trend, recent IPO listing performance | Exchange, news, trackers |

**Data timing (found on a real RHP):** the RHP is filed with the price band, share counts, GCP amount and net proceeds still blank (₹\[●\]). The price band, lot size and final share counts come from the price band announcement (at least two working days before opening). Peer P/Es in the RHP's "Basis for Offer Price" use a closing price weeks earlier and must be refreshed. Seller and holding details are in the RHP.

## 4. Design

**Pipeline:** Ingest → Extract/Normalise → Validate → Knockout Check → Score (6 modules) → Red-flag Penalties → Verdict → Report → Post-listing Log

- **Ingest:** manual entry or a structured-extraction/OCR service validated on Indian filings (restated tables, footnotes, mixed units); a custom parser only after that. All values normalised to ₹ crore at ingestion. Market data refreshed daily during the open window.
- **Rule config:** all thresholds and weights in one editable JSON/YAML file (no hard-coding), versioned.
- **Scoring modules:** independent functions, each returns `score`, `max`, `reason`, `data_used`.
- **Sector overlays:** financials, EPC/real estate, loss-making and cyclical companies swap in sector-appropriate metrics (§5A).
- **Two running modes:** Preliminary (pre-open) and Final (closing hours of Day 3) (§5B).
- **Output:** one-page scorecard (score by module, verdict, top 3 strengths, top 3 risks, knockout hits), plus an audit trail of inputs.
- **Post-listing log:** listing gain, 1-week, 1-month, 6-month return vs Nifty — used to recalibrate weights.

## 5. Scoring Framework (100 points)

| Module | Max |
| --- | --- |
| A. Financial Quality | 25 |
| B. Valuation | 20 |
| C. Issue Structure & Use of Proceeds | 15 |
| D. Promoter & Governance | 15 |
| E. Business & Moat | 15 |
| F. Market & Demand Signals | 10 |
| **Total** | **100** |

### A. Financial Quality (25)

*Default metrics; §5A overrides apply to financials, EPC/real estate and loss-making companies.*

| Criterion | Max | Scoring bands |
| --- | --- | --- |
| Revenue CAGR (3Y) | 6 | >25% = 6; 15–25% = 4; 8–15% = 2; \<8% = 0 |
| Profit trend (PAT/EBITDA margin) | 5 | Expanding 3Y = 5; stable = 3; volatile = 1; declining/loss = 0 |
| ROCE / ROE | 5 | ROCE >20% = 5; 15–20% = 3; 10–15% = 1; \<10% = 0 |
| Cash flow quality (CFO ÷ PAT, 3Y avg) | 5 | >0.8 = 5; 0.5–0.8 = 3; 0–0.5 = 1; negative = 0 |
| Leverage (D/E, interest cover) | 4 | D/E \<0.5 & ICR >5 = 4; D/E \<1 = 2; D/E 1–2 = 1; >2 = 0 |

### B. Valuation (20)

| Criterion | Max | Scoring bands |
| --- | --- | --- |
| P/E vs peer median (post-issue EPS) | 8 | ≥20% discount = 8; 0–20% discount = 6; 0–20% premium = 3; >20% premium = 1; >50% premium = 0 |
| EV/EBITDA or P/B (sector-appropriate) vs peers | 4 | Same banding as above, scaled to 4 |
| PEG (P/E ÷ growth) | 4 | \<1 = 4; 1–1.5 = 3; 1.5–2.5 = 1; >2.5 = 0. **Base-year check:** if earliest-year margin is under half the latest-year margin, growth is flattered by a low base; recompute on 3Y-average margin and cap this item at 2 |
| Valuation vs recent sector IPOs/listings | 4 | Cheaper = 4; in line = 2; richer = 0 |

*Loss-making: score P/S and EV/Sales vs peers and path-to-profit (breakeven in ≤2 yrs = full marks on PEG slot, else 0).*

### C. Offer Structure, Proceeds & Pre-IPO (15)

**C1. Offer structure (8)**

| Criterion | Max | Scoring bands |
| --- | --- | --- |
| Fresh issue share of total offer | 3 | >70% = 3; 40–70% = 2; 20–40% = 1; \<20% = 0 |
| OFS seller type | 2 | No OFS, or investor selling \<25% of its holding = 2; PE/VC selling 25–100% of holding = 1; promoter/promoter group selling = 0 |
| Promoter stake sold in OFS | 2 | 0% = 2; ≤10% of promoter holding = 1; >10% = 0 |
| Dilution from fresh issue | 1 | \<25% of post-issue equity, or proceeds clearly fund growth = 1; otherwise 0 |

**C2. Proceeds & pre-IPO (7)**

| Criterion | Max | Scoring bands |
| --- | --- | --- |
| Use of proceeds | 4 | Growth capex/R&D with disclosed plan = 4; mixed, ≤50% debt repayment = 2; >50% debt repayment = 1; GCP + unidentified acquisition >20% of fresh issue = 0 |
| Pre-IPO placements / discounted allotments | 2 | None, or near IPO price = 2; in between = 1; >25% below IPO price within 12 months = 0 |
| Lock-in | 1 | Promoter lock-in intact, no early unlock of large holders = 1; otherwise 0 |

*100% OFS issues: the company receives nothing, so fresh-issue, dilution and use-of-proceeds items score 0 and the §6 verdict cap applies. Employee/shareholder discounts are recorded as inputs only.*

### D. Promoter & Governance (15)

| Criterion | Max | Scoring bands |
| --- | --- | --- |
| Post-issue promoter holding | 4 | >60% = 4; 45–60% = 3; 30–45% = 1; \<30% = 0 |
| Promoter track record & litigation | 4 | Clean = 4; minor civil cases = 2; criminal/regulatory cases on promoters = 0 |
| Related-party transactions (% revenue/costs) | 3 | \<5% = 3; 5–15% = 1; >15% = 0 |
| Auditor quality & remarks | 2 | Reputed, clean opinion = 2; Emphasis of Matter / CARO remarks / disputed tax matters only = 1; frequent auditor change or repeated EoM = 0 (a qualified opinion is a knockout) |
| Board independence & KMP stability | 2 | Independent-majority, stable = 2; high KMP churn = 0 |

### E. Business & Moat (15)

| Criterion | Max | Scoring bands |
| --- | --- | --- |
| Industry growth outlook | 5 | Structural tailwind >12% CAGR = 5; 8–12% = 3; cyclical/flat = 1; declining = 0 |
| Market position & moat (rank, brand, IP, switching cost, scale) | 5 | Top 3 with clear moat = 5; strong niche = 3; follower = 1; commoditised = 0 |
| Customer/supplier concentration | 3 | Top 5 customers \<30% = 3; 30–50% = 1; >50% = 0 |
| Operating leverage/capacity visibility (order book, utilisation) | 2 | Strong visibility = 2; moderate = 1; none = 0 |

### F. Market & Demand Signals (10)

| Criterion | Max | Scoring bands |
| --- | --- | --- |
| Anchor investor quality | 3 | Reputed long-only/MF/insurance, ≥50% of anchor book = 3; mixed = 1; mostly unknown funds = 0 |
| QIB subscription (final day) | 3 | Normal market: >20x = 3; 10–20x = 2; 1–10x = 1; \<1x = 0. Hot market (≥3 of last 5 IPOs listed >20% above issue price): >50x = 3; 20–50x = 2; 2–20x = 1; \<2x = 0 |
| GMP trend (treat as sentiment only) | 2 | Stable/rising >10% = 2; flat = 1; falling = 0 |
| Market regime (Nifty trend, recent IPO listings) | 2 | Supportive = 2; neutral = 1; weak = 0 |
| Retail/NII under-subscription (Final mode) | –2 | Deduct 2 if Retail or NII is subscribed \<1x at close (module floor 0) |

## 5A. Sector Overlays

| Sector | Default metric | Replaced by |
| --- | --- | --- |
| Banks / NBFCs | Debt/Equity, ICR (4) | CRAR / Tier 1 buffer over regulatory minimum: ≥5 pts = 4; 2–5 = 2; \<2 = 0 |
|  | EBITDA/PAT margin trend (5) | NIM and cost-to-income trend |
|  | ROCE (5) | ROA / ROE vs listed peers: top quartile = 5; median = 3; bottom half = 1 |
|  | CFO ÷ PAT (5) | Asset quality (GNPA/NNPA trend, provision coverage); CFO not meaningful |
|  | EV/EBITDA (4) | P/B vs peers, adjusted for ROE |
| EPC / real estate / infra | CFO ÷ PAT (5) | Negative CFO accepted if order book ≥2x revenue (EPC) or collections ≥ pre-sales trend (real estate) **and** receivable days not up >15% YoY; else score default |
|  | Leverage (4) | Net debt/equity trend and interest cover on project debt |
| Loss-making / new-age | P/E, PEG (12) | EV/Sales or P/S vs peers (12), same bands scaled |
|  | Margin trend (5) | Restated operating loss (% of revenue) narrowing 2 consecutive years = 5, 1 year = 2.5, widening = 0. Management breakeven guidance is noted, not scored |
|  | ROCE (5) | Restated contribution margin: positive and up >300 bps YoY for 2 consecutive years = 5; positive and improving = 3; positive but flat/falling = 1; negative = 0 |
|  | CFO ÷ PAT (5) | Cash runway ≥24 months post-issue = 5; 12–24 = 2; \<12 = 0 |
| Cyclical (metals, commodities) | Margins, P/E | 5Y-average margins and mid-cycle EV/EBITDA; discount peak-year numbers |

## 5B. Running Modes

| Mode | When | Points used | Verdict |
| --- | --- | --- | --- |
| Preliminary | After price band; anchor allocation (day before opening) | A–E (90) + anchor quality (3) + market regime (2) = 95 absolute points, **not scaled** | Provisional, judged on the raw score |
| Final | Closing hours of Day 3 | All 100, incl. final QIB subscription and GMP | Final; alert if it differs from Preliminary |

*Preliminary score X/95 is shown unscaled (X/92 for retail-heavy issues, §5C, where overall subscription, NII subscription and GMP are pending, +8). In standard issues only QIB subscription (+3) and GMP (+2) are pending, and the Retail/NII penalty can deduct 2, so the final lies between X–2 and X+5. Flag "band may change" if that range crosses a verdict band edge.*

## 5C. Structure Overlays

| Structure | Trigger | Replaced | With |
| --- | --- | --- | --- |
| Retail-heavy | QIB portion ≤10% of the offer (e.g. Reg 32(1) issues with a 1% QIB portion) | Anchor quality (3), QIB subscription (3) | Overall subscription at close (3): >10x = 3; 3–10x = 2; 1–3x = 1; \<1x = 0. NII subscription at close (3): same bands as QIB, with the hot-market tiers |

With a tiny QIB portion there is no meaningful anchor book and QIB subscription carries no signal, so scoring them would only reward or punish noise. Thresholds are uncalibrated.

## 6. Knockout Rules and Verdict Caps

**Knockouts (auto-AVOID regardless of score):**

1. Qualified, adverse or disclaimer audit opinion, going-concern uncertainty, or negative net worth. (Emphasis of Matter and CARO remarks are not knockouts; see §7.)
2. Promoter pledge >25% of holding, or active SEBI/ED action against promoters/company.
3. OFS >80% and declining profits.
4. Promoters and PE/VC together selling >50% of their combined pre-issue holding (including 100% OFS), with promoters fully exiting or left below 20% post-issue, **and** any of: falling profits, ROCE \<10%, CFO/PAT \<0.5.
5. Undisclosed or unquantified contingent liabilities >50% of net worth.
6. Related parties driving >40% of revenue growth.

**Verdict cap:** any issue with 0% fresh issue is capped at 60 (APPLY SELECTIVELY at best).

## 7. Red-Flag Penalties (deduct after scoring, max –15)

| Flag | Penalty |
| --- | --- |
| EBITDA margin up >500 bps YoY in either of the last two FYs (check whether it is recovery from a trough) | –3 |
| Receivable days rising >30% YoY | –3 |
| Auditor/CFO resignation in last 2 years | –3 |
| Heavy non-pro-rata discounted allotments/ESOPs within 18 months before DRHP filing (pro-rata bonus and rights issues excluded; older ones ignored) | –2 |
| Aggressive "adjusted" metrics (EBITDA, GMV) with no GAAP/Ind AS reconciliation | –2 |
| Regulatory dependence (single licence, price control) | –2 |
| Emphasis of Matter / CARO remarks (e.g. pending tax appeals) | –1 to –3 by materiality |

## 8. Verdict Bands

| Score | Verdict |
| --- | --- |
| 75–100 | **APPLY** — long-term + listing gain candidate |
| 60–74 | **APPLY SELECTIVELY** — smaller allocation; listing-gain bias |
| 45–59 | **NEUTRAL** — skip unless strong subscription/GMP |
| \<45 or any knockout | **AVOID** |

Preliminary-mode verdicts are labelled provisional. **Missing data:** the engine reports a verdict floor (every missing item scores 0) and a ceiling (every missing item earns full marks). When confidence is Low and floor and ceiling differ, the verdict is INSUFFICIENT_DATA with the range shown, so missing disclosures are never read as a bad score. Also output a **confidence rating** (High/Medium/Low) based on data completeness (\<80% of inputs available = Low).

## 9. Checks (Validation Layer)

- **Data integrity:** restated financials sum correctly; PAT = PBT – tax; balance sheet balances; units normalised to ₹ crore (RHPs mix million/lakh/crore); flag any ratio that moves >10x on conversion.
- **Cross-check:** RHP numbers vs exchange/Screener data; flag differences >5%.
- **Post-issue EPS:** recomputed using post-issue share count, not pre-issue.
- **Peer set sanity:** peers similar in business mix and size; reject peers with \<3 years listing.
- **Proceeds limits:** flag a data error if GCP >25%, unidentified acquisition >25%, or both together >35% of the fresh issue (SEBI ICDR caps); re-verify against the RHP.
- **OFS limits (6(2) route):** significant shareholders may sell at most 50% (holders >20%) or 10% (holders \<20%) of their pre-issue holding; flag breaches.
- **Source quirks (seen in a real RHP):** a cash-flow column header repeated one year twice, so check column labels against the balance sheet; EBITDA is a KPI-defined figure (PBT + finance costs + depreciation – other income), not a line in the restated P&L, so recompute it; only 3 fiscal years may be given, so growth rates cover 2 years.
- **Peer multiples:** flag any peer multiple older than 30 days and refresh before scoring valuation. An RHP may list as few as 2 peers.
- **Selling shareholder type:** a promoter-group entity selling counts as promoter selling.
- **Config integrity:** at load, assert each module's max equals the sum of its criteria maxima and all modules sum to 100; reject the config otherwise.
- **Staleness:** price band, subscription, GMP timestamped; reject data older than 24h in open window.
- **Missing data:** missing field = 0 points plus a flag, never silently skipped.
- **Reproducibility:** same inputs + same config version = same score.
- **SME variant:** raise thresholds (e.g. minimum 3Y profitability, promoter holding >60%, subtract 10 points by default for liquidity/manipulation risk).

## 10. Do's

- Score on **post-issue** valuation and **restated** numbers.
- Read the litigation, related-party and contingent liability sections first.
- Compare against peers and against *recent* comparable IPOs.
- Re-run scoring on the final day with QIB subscription and anchor data.
- Keep thresholds in config; log every change with a date.
- Back-test every IPO after listing and recalibrate quarterly.
- Size positions by score band, with a cap per IPO.

## 11. Don'ts

- Don't let GMP, influencer buzz or listing-day hype drive the score (max 2 points).
- Don't score an IPO from news summaries — use the RHP.
- Don't compare P/E of a loss-making company with profitable peers.
- Don't ignore OFS-heavy issues from PE/VC exits without checking the reason.
- Don't treat "adjusted" or "proforma" numbers as audited.
- Don't override knockout rules manually without recording a reason.
- Don't over-fit weights to last year's few IPOs.
- Don't present the score as a guarantee of returns — it is a screening aid, not investment advice.

## 12. Build Phases

1. **MVP (2–3 weeks):** manual input form with unit normalisation, scoring modules A–E, verdict, one-page report (HTML/Excel).
2. **v1.1:** add market signals (F), Preliminary/Final modes, sector overlays, knockout rules, red-flag penalties, config file.
3. **v1.2:** peer comparison automation, validation layer; RHP table extraction via a structured-extraction/OCR service tested on Indian filings before any custom parser.
4. **v2:** post-listing tracking, back-testing dashboard, weight calibration, SME variant.

## 13. Success Metrics

- Hit rate: % of APPLY IPOs with positive 6-month return vs Nifty.
- Avoided-loss rate: % of AVOID IPOs that underperformed.
- Score-vs-return correlation (listing gain and 6M).
- Time to produce scorecard (target: \<30 minutes per IPO).

## 14. Worked Example: Vishal Nirmiti Ltd (RHP dated 24 Sep 2026)

Illustrative only; a screening aid, not advice. Data: RHP for offer terms, financials and holdings; price band, subscription (2 Oct) and GMP from public trackers.

**Issue:** 100% book-built, Reg 6(1), bidding 30 Sep – 5 Oct 2026, price band ₹208–220. Fresh issue ₹145 cr plus an OFS of 15 lakh shares (₹33 cr) by a promoter-group entity. QIB portion is capped at 1%, so the retail-heavy overlay applies. Financials are in ₹ lakhs (FY2024–26).

**Result (Final mode):** floor **29/100 (AVOID)**, ceiling **58 (NEUTRAL)**. Confidence is Low because 29 points of criteria had no data, so the verdict is INSUFFICIENT_DATA with that range. Even if every missing item earned full marks the issue could not reach APPLY.

| Pulled the score down | Why |
| --- | --- |
| OFS seller type, promoter stake sold (0 of 4) | A promoter-group entity sells about 82% of its holding |
| P/E vs peers (0 of 8) | Issue P/E about 23.3x vs peers' 13.9–14.8x (stale, dated 23 Jul) |
| Concentration (0 of 3) | Top 5 customers are 85.3% of revenue, Indian Railways 40.6% |
| Use of proceeds (0 of 4) | Working capital and debt repayment; general corporate purposes assumed at the 25% ceiling |
| Leverage (1 of 4) | Debt/equity about 1.0 |
| Margin spike (–3) | EBITDA margin up about 506 bps in FY2025 |

| Scored well | Why |
| --- | --- |
| ROCE, CFO/PAT (5 each) | ROCE 28%; 3-year CFO/PAT about 1.8 |
| Fresh share (3 of 3) | About 81% of the offer is fresh |
| Pre-IPO placement (2 of 2) | None contemplated |

**Not yet entered:** litigation, related-party share of revenue, board and KMP stability, industry growth, moat, recent sector IPOs, EV/EBITDA and P/B peers, market regime. These need the RHP sections beyond the ones used here.