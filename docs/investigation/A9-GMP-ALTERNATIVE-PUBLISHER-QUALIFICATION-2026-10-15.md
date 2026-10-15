# A9 — Alternative Publisher-Level GMP Qualification: PapsDigital and MarketLiveIPOGMP (2026-10-15)

- **Record type:** Non-authoritative investigation record. It assesses two candidate publishers against the Model A source contract; it approves no source.
- **Date:** 2026-10-15 (Asia/Calcutta). Captures were taken between 13:11 and 13:33 UTC (18:41–19:03 IST).
- **Repository and baseline:** `ramkivs/ipo-screening-engine`, session branch `arena/ba8f663e-ipo-screening-engine` at `643b91a`. That commit descends from the authoritative branch `arena/573e69a4-ipo-screening-engine` at `97b2eb5`, which was unchanged when this pass began (13:10:06 UTC).
- **Contract applied:** [A9 GMP source-policy selection](A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md) §3, requirements R1–R8 (Model A: one named publisher's own reported observation, never presented as a dealer quote).
- **Evidence:**
  - PapsDigital captures: [`evidence/gmp-observations/papsdigital-tonbo-20261015/`](../../evidence/gmp-observations/papsdigital-tonbo-20261015/README.md).
  - MarketLiveIPOGMP captures: [`evidence/gmp-observations/marketliveipogmp-tonbo-20261015/`](../../evidence/gmp-observations/marketliveipogmp-tonbo-20261015/README.md).
  - InvestorGain cross-references reuse the retained [`evidence/gmp-observations/investorgain-tonbo-20261015/`](../../evidence/gmp-observations/investorgain-tonbo-20261015/README.md); nothing there was re-fetched.
- **Implementation authority:** NOT GRANTED. No engine, schema, configuration, test, fixture, or result-hash change is made or proposed for implementation.

## 1. Determination

| Candidate | Verdict | Decisive finding |
|---|---|---|
| **MarketLiveIPOGMP** — best candidate | **NOT QUALIFIED — conditionally viable** | No requirement fails on source facts. R1 and R2 pass. R3, R4, R5 and R8 pass on source facts but each still needs a project rule that has not been adopted. R6 can be closed by an explicit fail-closed rule. **R7 is the one gap no project rule can close:** the publisher claims readings are never overwritten, corrections are disclosed, and final readings are frozen, but no reading history is exposed in the captured text and its own final-reading timestamp contradicts the "before listing" claim (ML-O7). |
| **PapsDigital** | **NOT QUALIFIED — closed** | It is a declared single-source relay of InvestorGain's IPO GMP Live report [PD-L1:27–32]: every GMP figure and source stamp is InvestorGain's by its own definition. Its observation semantics cannot exceed InvestorGain's, which is NOT QUALIFIED in both InvestorGain records. Its captured clock labels also contradict themselves (PD-O4), and the Tonbo page shows no source time at all (PD-O5). Every path to qualifying it runs through InvestorGain. |

**A9 and Final are unchanged.** Missing GMP remains `MISSING`; present but unqualified GMP remains `SOURCE_UNQUALIFIED`; neither sets `final_outcome`; Final remains withheld. No value from either candidate may be entered or labelled as a qualifying GMP snapshot.

**InvestorGain is not re-assessed.** It remains NOT QUALIFIED; both InvestorGain records stand as published.

## 2. Status vocabulary and the fact/rule split

| Status | Meaning in this record |
|---|---|
| **PASS** | Retained evidence satisfies the requirement's source-fact part. |
| **FAIL** | The publisher's accessible material contradicts the requirement or does not expose what it needs, and more capture of the same material cannot cure it. |
| **BLOCKED** | Cannot be decided with this environment's capture capability (rendered text only; no response bytes). |
| **UNRESOLVED** | Evidence is incomplete, or the requirement also needs a project rule that has not been adopted. Each row says which. |

**Source facts** must be evidenced: publisher identity, issue identity, value meaning and units, exposed timestamps and their zone, and actual displayed behaviour (staleness, missing values, revisions).

**Project rules** may be defined explicitly, subject to Ramki's adoption: the GMP evaluation cutoff, the maximum permitted age, the acceptable artifact and hash procedure, and fail-closed handling. A project rule may not supply a timezone, a value meaning, a historical observation, or a conflict outcome. §8 drafts the rules for MarketLiveIPOGMP; none is adopted by this record.

## 3. Capture method and limits

- **Tool:** the rendered-page fetch tool (`functions.fetch_page`). Each call was bracketed by sandbox UTC clock reads. The sandbox clock matched the `api.github.com` `Date` header at 13:24:26 UTC.
- **No raw bytes:** the sandbox cannot connect to either host (`curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL`). No response bytes, headers, or receipt times exist; the retained files are rendered text.
- **Access:** PapsDigital's `robots.txt` allows `/` and disallows `/api/` [PD-R:4–6]; no `/api/` path was queried. MarketLiveIPOGMP's allows `/` [ML-R:1–2].
- **Scope kept narrow:** only the two candidates' own pages were fetched (14 files retained, plus one byte-identical recapture). No other publisher was searched, no provider was contacted, and nothing was purchased.

## 4. Source facts — PapsDigital

### Observed

- **PD-O1 — Declared upstream.** "Grey market premium, price band, lot size, subscription and the IPO calendar are read from [InvestorGain's public IPO GMP Live report] … There is no second source and no merged data, so a figure is either that source's published value or it is absent." [PD-L1:27–31; repeated on the Tonbo page, PD-T0:142–146]
- **PD-O2 — Figures equal the upstream row.** Tonbo shows "+₹495+70.71%" and "270 ↓ / 500 ↑" [PD-L0:61–63; PD-T0:3–5]. InvestorGain's dashboard row shows "₹ 495 (70.71%)" and "270 ↓ / 500 ↑" [IG-D0:44].
- **PD-O3 — A filled-in price band.** PapsDigital shows "Price band ₹700 – ₹700" [PD-T0:7; PD-L0:67]. InvestorGain's dashboard field is a single "Price (₹) 700" [IG-D0:44], and InvestorGain's issue page gives the band as "₹665.00-700.00 per share" [IG-T0:26]. PapsDigital states "Nothing is averaged, merged, inferred or filled in." [PD-L1:23]
- **PD-O4 — Self-contradicting clock labels.**
  - The page shows "Updated 22s ago" [PD-L0:29], "source stamped 08:32 am" with no date or zone [PD-L0:31], and "Last updated: 15 Oct 2026, 09:11:14 am IST" [PD-L0:401].
  - The retrieval window was 13:11:32.551Z–13:12:01.221Z, i.e. 18:41:32–18:42:01 IST.
  - Read as IST, 09:11:14 is 9 h 30 min before retrieval, which contradicts "Updated 22s ago".
- **PD-O5 — No source time on the issue page.** Neither Tonbo chunk contains a clock time. "Source updated" appears only in the methodology definition [PD-T0:151].
- **PD-O6 — Date-level history only.** The day-wise table has one value per date, with no time: ₹495, ₹500, ₹490, ₹425, ₹270 for 15–11 Oct [PD-T0:37–41], described as "the premium our source published on that date" [PD-T0:43]. InvestorGain's history, captured at 12:29 UTC, already showed three values on 15 Oct — ₹501 at 02:37 pm, ₹500 at 03:37 pm, ₹495 at 05:02 pm [IG-T0:81–83] — and values from ₹125 to ₹310 on 11 Oct [IG-T0:113–120]. The table is a date-level summary, not the source's observation history.
- **PD-O7 — Missing markers and zero counts.** Shellz India shows "GMP unavailable" with derived fields "N/A" [PD-L0:369, 387–393], where InvestorGain shows "₹ -- (0.00%)" [IG-D0:45]. The 11 Oct row shows "N/A" for derived fields [PD-T0:41]. The filter bar counts "Positive125 Zero21 Negative5" [PD-L0:47].

### Publisher claims

- **PD-C1 — Two clocks.** "Source updated" is "the time InvestorGain itself stamped the row, in IST"; "Updated N ago" is the time since PapsDigital last fetched [PD-L1:36–38].
- **PD-C2 — Refresh failure.** The page shows the figures as delayed, and shows no figures when nothing can be verified [PD-L1:39–40].
- **PD-C3 — Missing values.** "A field the source has not filled in shows N/A — never a substituted zero." [PD-L1:32]
- **PD-C4 — Per-figure source time.** The page "shows … the time our source itself published each figure" [PD-L2:5].
- **PD-C5 — Units.** GMP "is quoted per share … the premium over the issue price" [PD-L2:21]; estimated listing price is the upper end of the price band plus GMP [PD-L1:45, 152].
- **PD-C6 — Attribution only.** Naming the source "is attribution, not a claim that the figure is correct" [PD-L1:53; PD-T1:8].

## 5. Source facts — MarketLiveIPOGMP

### Observed

- **ML-O1 — The issue observation.**
  - Header: "Mainboard · ₹700 · 21 shares/lot · BSE, NSE" [ML-T:3].
  - Reading: "₹500+71.4%", "▲₹32 since last reading", "15 Oct, 4:02 pm" and "IST" [ML-T:7–13].
  - FAQ: "₹500 as of 4:02 pm IST on Thu, 15 Oct, 2026. That is +71.4% over the ₹700 price." [ML-T:84]; and "an indicative listing price of ₹1200 per share" [ML-T:88].
- **ML-O2 — The arithmetic reproduces.** 500 / 700 = 71.43% (shown as +71.4%); 700 + 500 = ₹1,200 [ML-T:19–21]; 500 × 21 = ₹10,500 [ML-T:23–25]. Issue size ₹852.18 Cr [ML-T:72] matches InvestorGain and PapsDigital.
- **ML-O3 — The reading stamp equals the site-wide sync time.**
  - "Last data sync Thu, 15 Oct, 2026, 4:02 pm IST" [ML-A:3] and "Updated Thu, 15 Oct, 2026 at 4:02 pm IST" [ML-H:5].
  - The sitemap's site-level `lastmod` is `2026-10-15T16:02:00+05:30` [ML-S:1].
  - Subscription is shown "as of 15 Oct, 4:02 pm" [ML-T:60].
- **ML-O4 — The IST label is consistent with real time.** 16:02 IST is 10:32 UTC, before retrieval at 13:15–13:18 UTC. InvestorGain's history shows ₹500 from 03:37 pm until its ₹495 entry at 05:02 pm [IG-T0:81–82], so ₹500 at 16:02 IST agrees with the stamp read as IST.
- **ML-O5 — An ageing reading keeps its original stamp.** The same "₹500 … 15 Oct, 4:02 pm IST" reading was displayed at 18:45–18:47 IST (ML-T) and again at 19:02:55–19:03:04 IST. The recapture's transcription is byte-identical (manifest `derivedChecks.tonboRecapture`). The stamp was not refreshed, while InvestorGain had moved to ₹495 at 05:02 pm [IG-T0:81].
- **ML-O6 — Missing and zero are displayed differently.**
  - "Not quoted yet" is shown for Shellz India and Vaibhav Vyapaar [ML-H:141, 239]. For five listed issues, the page shows "Final GMP … Not quoted yet" and "GMP said —" [ML-H:389, 399–401, 527, 550, 573, 596].
  - Hero Motors shows "Final GMP before listing" "₹0" / "0.0%" [ML-HM:5–7] and is counted in the track record as "0.0%" [ML-TR:515–521].
  - The five "Not quoted yet" listings (8–9 Oct) do not occur in the track-record chunk covering listings from 12 Oct back to 22 Sept [ML-TR:59–529].
- **ML-O7 — The final reading was recorded on listing day.**
  - The page says "recorded at 3:37 pm IST on Wed, 23 Sept, 2026" [ML-HM:128], with "Listing date Wed, 23 Sept, 2026" [ML-HM:108] and "Listed at ₹82" [ML-HM:19–21]. The sitemap `lastmod` is `2026-09-23T15:37:00+05:30` [ML-S:1].
  - The page also calls it "the one published here before listing, frozen at the bell and never revised afterwards" [ML-HM:49].
  - Subscription is shown "as of 23 Sept, 3:37 pm" [ML-HM:80] for an issue that closed on 18 Sept [ML-HM:59–63].
- **ML-O8 — No reading history in the text.** The rendered page shows only "Range so far: ₹270 low ·₹500 high" and the chart axis labels "12 Oct15 Oct" [ML-T:15–17]. No list of readings or their stamps appears.
- **ML-O9 — The values also occur in InvestorGain's history.**
  - ₹500 (current), ₹468 (= 500 − 32, the previous reading) and ₹270 (the low) all appear as InvestorGain history values [IG-T0:82, 84, 91, 113, 115].
  - InvestorGain's history also contains values outside MarketLiveIPOGMP's displayed range: ₹501 [IG-T0:83], ₹265 [IG-T0:112], and ₹125–₹140 [IG-T0:119–120].
  - Counter-example: TNA Solutions' final GMP is ₹2 here [ML-H:366], whereas InvestorGain's TNA row shows "₹ --" with GMP 7 / 3 / 0 [IG-D0:56].
- **ML-O10 — Minor issue-term gaps.** The page shows "Price ₹700" only [ML-T:66], not the ₹665–700 band [IG-T0:26], although About says every IPO gets a price band [ML-A:7]. The track-record page title says "195 Listings" while its body says 199 [ML-TR:7] (manifest `derivedChecks.pageTitleVsBody`).
- **ML-O11 — No operator named.** About names no operating entity [ML-A:1–29], and the sitemap's site-level entries list no legal or terms page [ML-S:1].

### Publisher claims

- **ML-C1 — Sourcing.** "GMP quotes are collected from grey market dealer channels and cross-checked against other public trackers before publishing." [ML-A:11]
- **ML-C2 — Append-only readings.** "Each reading is stored with a timestamp and never overwritten, which is why every IPO here has a GMP history chart" [ML-A:11].
- **ML-C3 — Freshness.** "Through the bidding window, GMP is refreshed several times a day and always carries a visible IST timestamp. If a number looks stale, the timestamp will say so" [ML-A:17].
- **ML-C4 — Corrections.** "If a number on this site is wrong, tell us and we will fix it and say what changed." [ML-A:27]
- **ML-C5 — Frozen final reading.** "frozen at the bell and never revised afterwards" [ML-HM:49].
- **ML-C6 — Definition.** GMP is "the extra amount, per share, that buyers … are willing to pay for IPO shares before they list"; expected listing price is "Cap price + current GMP" [ML-L:7, 25].

## 6. Inferences (labelled; none is relied on for a PASS)

- **I1 — PapsDigital clock labels.** PD-O4 would be explained if the page formats its clock in the capturing browser's zone and appends a fixed "IST":
  - 09:11:14 at UTC−04:00 is 13:11:14 UTC, 18 s before the window opened at 13:11:32 UTC — consistent with "Updated 22s ago".
  - "08:32 am" at UTC−04:00 is 18:02 IST, which fits InvestorGain's :02/:37 update cadence [IG-T0:81–121].
  - Whatever the cause, the captured "IST" labels cannot be relied on.
- **I2 — Meaning of MarketLiveIPOGMP's stamp.** The single stamp is the publisher's recording (sync) time (ML-O3, ML-O7), not the time a dealer quote prevailed. NSE/BSE normal trading on listing day starts at 10:00 IST (an external market-hours fact; not captured), so a 3:37 pm listing-day stamp cannot mark a pre-listing quote. Pre-listing readings — the only kind a Final evaluation at or after the close would use — are not affected.
- **I3 — MarketLiveIPOGMP independence.** ML-O9 is consistent with sparse sampling of InvestorGain or a shared upstream; the TNA value is consistent with independent collection. Independence is UNRESOLVED. Model A does not require it, but neither publisher may be used to corroborate the other.

## 7. Requirement-by-requirement assessment

MarketLiveIPOGMP is shown twice: its source-fact status and its overall status. Overall status includes the project rule each requirement still needs.

| # | Requirement (policy §3) | MarketLiveIPOGMP — source facts | MarketLiveIPOGMP — overall | PapsDigital |
|---|---|---|---|---|
| R1 | Publisher identity; traceable issue-specific observation | **PASS.** Named publisher and domain; the issue page carries the value and its stamp [ML-T:3–13, 84]. No operator entity is named (ML-O11). | **PASS** | **PASS.** Named relay; issue page [PD-T0:3]; names its upstream [PD-L1:28]. The observation itself is InvestorGain's (PD-O1). |
| R2 | Issue identity; GMP value meaning and units | **PASS.** GMP is ₹ per share over the cap price [ML-L:7, 25; ML-T:84, 88]; the percentage and lot arithmetic reproduce (ML-O2); identity matches. The band is not shown (ML-O10). | **PASS** | **PASS (with defect).** Units are defined [PD-L2:21; PD-L1:45]; the value is InvestorGain's by definition (PD-O1). The relay fills in a band the source does not publish, contradicting its own claim (PD-O3). |
| R3 | Source time distinct from retrieval time; zone; cutoff | **PASS.** One stamp per reading, with date, year and explicit IST [ML-T:11–13, 84; ML-HM:128]; `+05:30` offsets in the sitemap [ML-S:1]; consistent with real time (ML-O4). Meaning: the publisher's recording time (I2). Publication time is not separately exposed; retrieval time is in the manifest. Post-listing anomaly: ML-O7. | **UNRESOLVED** — GMP cutoff (PR-1) not adopted | **FAIL.** The issue page shows no source time (PD-O5); the listing stamp has no date or zone [PD-L0:31]; the "IST" footer contradicts the retrieval clock and "Updated 22s ago" (PD-O4). The relay's "in IST" label for InvestorGain's stamp [PD-L1:36] is a third-party assertion InvestorGain itself does not make (InvestorGain record §4 O4, §7.3). |
| R4 | Freshness, delayed/stale and refresh-failure behaviour | **PASS.** Documented [ML-A:17] and observed: the 16:02 IST reading was still shown with that stamp, not refreshed, at 19:03 IST (ML-O5). Refresh failure beyond "the timestamp will say so" is not separately documented. | **UNRESOLVED** — maximum permitted age (PR-2) not adopted | **BLOCKED.** Relay refresh-failure behaviour is documented [PD-L1:39–40] but was not observed. The per-figure source times it claims [PD-L2:5] are absent from the captured views (PD-O5), possibly existing only in a client-side Table view the tool cannot render. "Updated N ago" measures fetch age only [PD-L1:37]. |
| R5 | Retainable artifact; defined hash subject | **PASS** for retainability: `robots.txt` allows access [ML-R:1–2], and stamps render identically on three pages, consistent with real IST. **BLOCKED** for response bytes in this environment. | **UNRESOLVED** — artifact and hash rule (PR-3) not adopted; tracker l.29 and l.106 precedent applies until it is | **BLOCKED.** Rendered text only. The relay's clock labels appear capture-dependent (PD-O4, I1), so rendered-text hashes would not reproduce across environments. `/api/` is disallowed [PD-R:6]. |
| R6 | Explicit missing-versus-zero semantics | **UNRESOLVED.** Missing and zero are displayed and retained differently (ML-O6) but neither is defined. The only zero example is a post-listing recording (ML-O7), so a genuine pre-listing zero is not evidenced. | **UNRESOLVED** — closable by fail-closed rule PR-4a/4b | **FAIL.** The N/A rule covers unfilled fields only [PD-L1:32; PD-L0:369]. Numeric zeros pass through ("Zero21" [PD-L0:47]) carrying InvestorGain's zero semantics, which are unmet in both InvestorGain records. |
| R7 | Conflicts, corrections, revisions, precedence | **UNRESOLVED.** Claims ML-C1, ML-C2, ML-C4 and ML-C5 are unverified: no reading list is exposed (ML-O8), no correction disclosure was observed, and the cross-check outcome and precedence are unstated. ML-O7 contradicts ML-C5's "before listing". | **UNRESOLVED** — needs source evidence (§9); PR-4f and PR-5 limit project exposure but cannot establish source behaviour | **FAIL.** A single upstream by design [PD-L1:31] removes inter-source conflict, but no revision or correction record exists. Values are replaced on each 15-second refresh [PD-L2:5], and correctness is disclaimed [PD-L1:53]. |
| R8 | Reproducible historical observation | **PASS** for the captured observation: each reading has a complete identity (value plus dated IST stamp) [ML-T:84], so a retained capture reproduces the exact observation with its version identity and retrieval window. **BLOCKED** for history before capture (ML-O8). | **UNRESOLVED** — depends on PR-3, and on R7 for correction information | **FAIL.** Date-level rows only, one value per date although the source published several (PD-O6); no times, versions, or corrections. |

**Scope note on R2.** This author's [InvestorGain record](A9-GMP-INVESTORGAIN-QUALIFICATION-2026-10-15.md) §7.2 counted the engine's `market.gmp.trend` mapping under R2. This record limits R2 to the source's value definition and units, as the Phase 2 criteria state. The mapping is listed separately (§9, item 3) because it is not a source fact and applies identically to every candidate. InvestorGain is not re-scored; it remains NOT QUALIFIED on R3, R4, R6 and R7 in both records.

## 8. Project rules drafted for MarketLiveIPOGMP (PROPOSED — not adopted)

These are proposals for Ramki. They define project handling only and assert no source fact. Numeric values are deliberately left unset: A8 forbids inventing freshness intervals or cutoffs (A8 l.15).

- **PR-1 — GMP cutoff.** Ramki sets `GMP_CUTOFF` per issue, for example tied to the Final evaluation timestamp (spec §19: "on/after closing"). The observation used is the latest reading whose source stamp, normalized from IST (UTC+05:30) to UTC, is at or before `GMP_CUTOFF` and that was retrieved at or before the evaluation timestamp.
- **PR-2 — Maximum permitted age.** Ramki sets `MAX_AGE`. Age is `GMP_CUTOFF` minus the source stamp.
- **PR-3 — Artifact and hash.**
  - The artifact is the rendered-text capture of the issue page, following this package's convention: the tool content string, JSON-decoded, UTF-8, no BOM, no added newline. It is accompanied by a manifest giving the URL, chunk, UTC retrieval window, and clock check.
  - The hash subject is the exact retained file bytes, digested with SHA-256 in uppercase hex. The hash proves capture integrity only.
  - Adopting PR-3 departs, for A9 GMP only, from the tracker precedent that rendered captures leave source-native qualification open (tracker l.29, l.106). A raw-byte capture from an environment that can reach the host would supersede it.
- **PR-4 — Fail-closed mapping.** Only existing A9 codes are used, and none of these outcomes sets `final_outcome`.
  - **a.** No reading at or before `GMP_CUTOFF`, or "Not quoted yet" ⇒ `MISSING`.
  - **b.** A displayed ₹0 ⇒ `SOURCE_UNQUALIFIED` (zero semantics are undocumented).
  - **c.** A missing or unparsable stamp, or no "IST" label ⇒ `SOURCE_UNQUALIFIED`.
  - **d.** A stamp on or after the listing date ⇒ `SOURCE_UNQUALIFIED` (ML-O7).
  - **e.** Age greater than `MAX_AGE` ⇒ `SOURCE_UNQUALIFIED`.
  - **f.** A later capture before Final generation shows a different value under the same stamp, or a publisher correction covers the reading ⇒ `SOURCE_UNQUALIFIED`.
- **PR-5 — Single source.** No fallback to, precedence over, or corroboration by another publisher. The value is labelled "MarketLiveIPOGMP reported GMP", never a dealer-verified quote.

## 9. Remaining blockers and minimum remaining work

### MarketLiveIPOGMP

| # | Item | Type | Closes |
|---|---|---|---|
| 1 | Evidence that readings are append-only and final readings are frozen | Source evidence (public pages only) | R7; R8 together with item 2 |
| 2 | Adopt PR-1 to PR-5, with values for `GMP_CUTOFF` and `MAX_AGE` | Ramki decision | R3, R4, R5, R6; R8 together with item 1 |
| 3 | Define how `market.gmp.trend` (strong / flat / falling) is derived. v1.5 defines no derivation for any publisher (`schema/ipo-input.v1.5.schema.json` `market.gmp`; `config/ipo-config.v1.5.0.json` `gmp_trend`). | Ramki decision on a scoring input | Engine use; not a source requirement |
| 4 | Capture tooling, snapshot and hash representation, an A9 gate qualified path, and tests | Requires implementation authority | Final eligibility |

**Evidence protocol for item 1.** Public pages only; no provider contact.

- **During bidding (to the 19 Oct close):** capture `/ipo/tonbo-imaging-india` after each new reading.
  - Each new reading's "since last reading" delta must equal its value minus the previously captured value.
  - No captured reading may show a different value under the same stamp.
  - If an unseen intermediate reading could explain a mismatch, the result is inconclusive, not a failure.
- **After listing (23 Oct):** capture the "Final GMP before listing" and re-capture it later.
  - It must not change.
  - Its stamp shows whether a pre-listing reading was frozen.
- **Raw-HTML alternative:** a raw capture from an environment that can reach the host may expose the chart's stored readings with their stamps, which would be direct evidence.
- **Outcome:** consistent results across these checks would support R7 PASS for this publisher. An in-place change, or a broken chain with no possible intermediate reading, makes R7 FAIL and closes MarketLiveIPOGMP as PapsDigital is closed.

### PapsDigital

No remaining work is useful. Its value, zero, revision, and history semantics are InvestorGain's by its own definition (PD-O1). Its relay-specific defects (PD-O3 to PD-O6) would remain even if InvestorGain were later qualified.

### Common to every publisher reviewed so far (InvestorGain, PapsDigital, MarketLiveIPOGMP)

- No response bytes are obtainable from this environment, so any qualification needs PR-3 or a capable capture environment.
- The project rules in §8 are not yet adopted.
- The `market.gmp.trend` derivation is undefined (item 3).

## 10. Consequences

- **A9 and Final:** unchanged (§1). The A9 gate (`_a9_final_gmp_gate` in `engine/ipo_screening/evaluation_record.py`) still has no qualified path, and none is added.
- **Code changes:** none is justified. No candidate qualifies; implementation authority is not granted (A8, A9); and the gate's `MISSING` / `SOURCE_UNQUALIFIED` behaviour is correct for this evidence.
- **Tests:** none were rerun, because no code, schema, configuration, or fixture changed. Scoring formulas, serialization, and existing result hashes are untouched.
- **Labelling:** a publisher observation must never be presented as a verified dealer quote. Neither candidate exposes a dealer identity, and Model A does not require one.

## 11. Next action

**Single smallest next action:** re-capture https://marketliveipogmp.com/ipo/tonbo-imaging-india once it shows a reading stamped after 15 Oct 4:02 pm IST and before the 19 Oct close. Check that its "since last reading" delta equals its value minus ₹500. This is the first direct test of R7 — the only gap no project rule can close — and it is possible only while Tonbo's bidding window is open. Adopting PR-1 to PR-5 (§8) is the other required step and does not depend on this result.

## Evidence keys

Line references are `[KEY:line]` against these retained files. Quotations omit Markdown emphasis markers (for example, `₹ **495**` is quoted as "₹ 495").

| Key | File |
|---|---|
| PD-L0, PD-L1, PD-L2 | `evidence/gmp-observations/papsdigital-tonbo-20261015/source-captures/papsdigital-ipo-gmp-chunk-{0,1,2}.md` |
| PD-T0, PD-T1 | `…/papsdigital-tonbo-20261015/source-captures/papsdigital-ipo-gmp-tonbo-imaging-india-chunk-{0,1}.md` |
| PD-R | `…/papsdigital-tonbo-20261015/source-captures/papsdigital-robots.txt` |
| ML-T | `evidence/gmp-observations/marketliveipogmp-tonbo-20261015/source-captures/marketliveipogmp-ipo-tonbo-imaging-india-chunk-0.md` |
| ML-A, ML-H, ML-L | `…/marketliveipogmp-tonbo-20261015/source-captures/marketliveipogmp-{about,home,learn}-chunk-0.md` |
| ML-TR, ML-HM | `…/marketliveipogmp-tonbo-20261015/source-captures/marketliveipogmp-track-record-chunk-0.md`, `…-ipo-hero-motors-chunk-0.md` |
| ML-S, ML-R | `…/marketliveipogmp-tonbo-20261015/source-captures/marketliveipogmp-sitemap-chunk-0-prefix.txt`, `…-robots.txt` |
| IG-T0, IG-D0 | `evidence/gmp-observations/investorgain-tonbo-20261015/source-captures/investorgain-gmp-tonbo-2369-chunk-0.md`, `…/investorgain-ipo-gmp-live-331-chunk-0.md` |

## References

- [A9 GMP source-policy selection](A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md) §§1–5 (Model A and requirements R1–R8)
- [InvestorGain qualification — this author](A9-GMP-INVESTORGAIN-QUALIFICATION-2026-10-15.md) and [InvestorGain qualification — parallel record](A9-INVESTORGAIN-PUBLISHER-QUALIFICATION-2026-10-15.md) (both NOT QUALIFIED; unmodified)
- `handoff/decisions/A9-missing-gmp-final-fail-closed.md` (approved fail-closed rule; hash subject undefined)
- `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` l.15, l.39, l.45, l.57 (Ramki-approved timestamp and evidence directions; unresolved GMP items)
- `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` l.29, l.106 (precedent for rendered captures)
- `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §4.6, §13, §19 (GMP snapshot requirements)
