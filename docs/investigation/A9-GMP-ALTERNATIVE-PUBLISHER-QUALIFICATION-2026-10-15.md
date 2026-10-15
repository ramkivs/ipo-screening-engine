# A9 — Alternative Publisher-Level GMP Qualification: PapsDigital and MarketLiveIPOGMP (2026-10-15)

- **Record type:** Non-authoritative investigation record. It assesses two candidate publishers against the Model A source contract; it approves no source.
- **Date:** 2026-10-15 (Asia/Calcutta). Captures were taken between 13:11 and 13:33 UTC (18:41–19:03 IST); the R7 follow-up check in §12 was made at 13:54 UTC (19:24 IST).
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
| 3 | Define how `market.gmp.trend` (strong / flat / falling) is derived. v1.5 defines no derivation for any publisher (`schema/ipo-input.v1.5.schema.json` `market.gmp`; `config/ipo-config.v1.5.0.json` `gmp_trend`). | Ramki decision on a scoring input; the smallest open question is stated in §12.2 | Engine use; not a source requirement |
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

**Single smallest next action:** re-capture https://marketliveipogmp.com/ipo/tonbo-imaging-india once it shows a reading stamped after 15 Oct 4:02 pm IST and before the 19 Oct close. Check that its "since last reading" delta equals its value minus ₹500. This is the first direct test of R7 — the only gap no project rule can close — and it is possible only while Tonbo's bidding window is open. Adopting PR-1 to PR-5 (§8) is the other required step and does not depend on this result. A follow-up check at 19:24 IST found no newer reading (§12.1), so this action remains open.

## 12. Follow-up — 2026-10-15, 13:54 UTC

This addendum reuses the evidence above. R3, R4 and R8 are not reopened, and no determination changes.

### 12.1 R7 follow-up result

- **Check made:** one capture of https://marketliveipogmp.com/ipo/tonbo-imaging-india at 13:54:22.896Z – 13:54:30.144Z (19:24:22–19:24:30 IST).
- **Observed:** the transcription is byte-identical to ML-T (SHA-256 `33516F86…705D`; manifest `derivedChecks.tonboRecaptureR7Followup`). The latest displayed reading was still ₹500, "▲₹32 since last reading", stamped "15 Oct, 4:02 pm IST" — 3 h 22 min before the check.
- **Result:** no newer observation was publicly available, so the delta check could not be performed. Per instruction, no further polling was done.
- **Status:** R7 remains **UNRESOLVED**. MarketLiveIPOGMP remains the leading candidate and **NOT QUALIFIED**.

### 12.2 `market.gmp.trend` — smallest unresolved semantic decision

What v1.5 defines:
- The schema allows `strong`, `flat`, `falling` or `null` (`schema/ipo-input.v1.5.schema.json` l.988–994).
- The config scores the label 2 / 1 / 0 (`config/ipo-config.v1.5.0.json` l.751–763) in every mode except `preliminary` (l.34–41).
- The engine passes a source-supplied label straight through (`engine/ipo_screening/derived.py` l.1721–1723). The connector only normalises synonyms: strong/rising/bullish/up → `strong`; flat/steady/neutral → `flat`; falling/declining/bearish/down → `falling` (`engine/ipo_screening/connectors/adapters.py` l.202–216).
- Tests cover only pass-through, normalisation and rejection (`tests/test_connectors.py` l.107, l.322; `tests/test_evaluation_record_v1.py` l.291). The v1.5 specification, technical design and execution prompt never define GMP trend.

The only written definition is in the reference baseline, `handoff/reference/Claude_IPO Screening Engine v 1.3 — Specification.md` l.123: "GMP trend … Stable/rising >10% = 2; flat = 1; falling = 0". The v1.5 artifact manifest classifies that file as reference material, with v1.5 as the target contract (manifest l.8, l.50). The definition was not carried into v1.5.

MarketLiveIPOGMP publishes no trend label — only a value and a "since last reading" change [ML-T:7–9]. Under the current contract its `trend` would therefore be `null`, and `gmp_trend` would be UNKNOWN.

**Decision needed (Ramki, one question):** do v1.5's `strong / flat / falling` carry the baseline meaning "Stable/rising >10% = strong; flat = flat; falling = falling"? If yes, does ">10%" mean the GMP level as a percentage of the issue price, or the size of the rise?

- **Inference, not adopted:** because the baseline pairs "stable" with ">10%", only the level reading is internally consistent.
- **Follow-on parameter:** if the meaning is adopted, a comparison base for stable/rising/falling must also be named. MarketLiveIPOGMP exposes only "since last reading".
- **No new threshold:** this record introduces none — the 10% figure is the baseline's own — and nothing in scoring, configuration, schemas or result hashes is changed.

### 12.3 Unchanged

- **MarketLiveIPOGMP:** NOT QUALIFIED; the leading candidate.
- **PapsDigital:** closed as an independent alternative.
- **InvestorGain:** NOT QUALIFIED.
- **A9 and Final:** behaviour unchanged.

## 13. Follow-up — 2026-10-15, 15:58 UTC (convergence pass)

This addendum reuses §§1–12 and the retained evidence. Nothing above is edited, and no determination changes.

It is committed on `arena/5ccbfd5d-ipo-screening-engine`, a fast-forward of `arena/ba8f663e-ipo-screening-engine` at `6ecd26c`. Both descend from the authoritative `arena/573e69a4-ipo-screening-engine` at `97b2eb5`, which this pass verified but did not update.

### 13.1 R7 second follow-up

- **Check made:** one capture of https://marketliveipogmp.com/ipo/tonbo-imaging-india at 15:57:54.203Z – 15:57:59.792Z (21:27:54–21:27:59 IST), with no retry.
- **Observed:** byte-identical to ML-T (SHA-256 `33516F86…705D`; manifest `derivedChecks.tonboRecaptureR7Followup2`).
  - The latest reading was still ₹500, "▲₹32 since last reading", stamped "15 Oct, 4:02 pm IST". That is 5 h 25 min before the check.
  - The timeline still showed "Closes 19 Oct" [ML-T:39–43].
- **Status:** no newer observation, so the delta check could not run. R7 remains **UNRESOLVED**. The unchanged page is evidence of neither qualification nor disqualification.

**Condition for the single follow-up capture.** Everything else is as in the §9 protocol.

1. **Trigger:** the Tonbo page shows a reading stamped later than "15 Oct, 4:02 pm IST", before the page's "Closes 19 Oct".
2. **Capture:** one clock-bracketed capture, retained with a manifest entry. No retry in the same pass.
3. **Test:** the displayed "since last reading" change, signed by ▲ or ▼, must equal the new value minus ₹500.
4. **Reading the result:**
   - *Equal:* consistent with an unbroken chain from the 4:02 pm reading. It supports R7 for this pair of readings only; it does not establish the publisher's retention or correction policy.
   - *Unequal:* inconclusive. A reading stamped after the 21:27 IST check could have been published and then superseded unseen.
   - *A different value under the 4:02 pm stamp:* an in-place change, which §9 treats as R7 FAIL.
   - *A new stamp earlier than the 21:27 IST check:* that reading was not displayed at the check. Record it as an anomaly bearing on I2 and R7; it is not a pass.
5. **Timing (inference, not a rule):** InvestorGain's 15 Oct entries were all made during the day (02:37, 03:37 and 05:02 pm [IG-T0:81–83]). This page showed no new reading from 4:02 pm to at least 9:27 pm IST. A capture during the IST day on 16 Oct is therefore the earliest likely to find one.

### 13.2 Minimum open product decisions

These refine PR-1, PR-2 (§8) and §12.2. None is adopted, and this addendum introduces no threshold, lookback, comparison interval or classification rule.

| Item | What existing artifacts establish | What remains undefined | Smallest decision (Ramki) | Recommendation |
|---|---|---|---|---|
| **Cutoff and time eligibility** (PR-1) | Final is "Generated at a defined evaluation timestamp on/after closing" and freezes the GMP snapshot (spec v1.5 §19 l.784–790); the v1.3 baseline put Final, "incl. … GMP", in the "Closing hours of Day 3" (v1.3 l.149). Market values carry as-of time, zone and source (spec §4.6 l.297–302). Cutoffs are source-specific and may not be invented; a scheduled event is not a completed one (A8 l.15). Observation, publication and retrieval times stay separate (A8 l.39, l.57). The engine measures GMP age from the evaluation timestamp (`snapshots.py` l.450). | The value of `GMP_CUTOFF`. A8 l.45 and A9 l.30, l.50 leave the GMP cutoff open. | Is `GMP_CUTOFF` the Final evaluation timestamp or the actual bid close? The answer decides whether readings published after the close but before listing can be used. | **Use the evaluation timestamp as the mechanism.** It is the only instant v1.5 defines, it is the engine's existing age reference, and it is the per-evaluation cutoff Ramki approved for NIFTY (A8-M observation contract l.23). **Ramki's judgment:** whether also to exclude post-close readings. A bid-close cutoff would need evidence that the close actually occurred (A8 l.15). |
| **Maximum age and freshness** (PR-2) | Thresholds are versioned policy (spec §3.5 l.122–123). The v1.5 config sets `thresholds.market_staleness_hours: 24` (`config/ipo-config.v1.5.0.json` l.104), which `pipeline.py` reads at l.232. The GMP block is STALE when evaluation time − `as_of` exceeds 24 h, or when `as_of` is missing or unparseable (`snapshots.py` l.443–465). STALE makes `gmp_bucket` UNKNOWN (`derived.py` l.1664–1670) and yields the A9 reason `SOURCE_UNQUALIFIED` (`tests/test_evaluation_record_v1.py` l.299–318). The connector's 24 h default affects confidence only (`connectors/interfaces.py` l.243; `adapters.py` l.239). The v1.3 baseline used the same 24 h (l.209). | Whether the generic 24 h is the A9 qualification `MAX_AGE`. A8 l.45 leaves GMP "stale or unverifiable handling" open, and the A9 gate infers no freshness semantics (`evaluation_record.py` l.929–937). A8-M rejected the generic 24 h only for the session-close NIFTY metric (observation contract l.37) and excludes GMP (l.76). PR-2 did not cite the existing value. | Ratify `market_staleness_hours` (24 h, measured from `GMP_CUTOFF`) as `MAX_AGE`, or name a GMP-specific value? | **Ratify 24 h.** It is the only value in the v1.5 contract and is already enforced on the GMP block. Ratifying it adds no new number (A8 l.15) and needs no code or config change. With the cutoff at the evaluation timestamp, PR-2 and the engine compute the same age. **Adoption is Ramki's** (A8 l.45). |
| **Trend labels:** strong / flat / falling | Only the labels and their points: the schema enum (`schema/ipo-input.v1.5.schema.json` l.988–994) and the 2 / 1 / 0 map, excluded in `preliminary` (`config/ipo-config.v1.5.0.json` l.751–763, l.34–41). `gmp_bucket` passes `market.gmp.trend` through (config l.1950–1956; `derived.py` l.1721–1723). The connector only normalises synonyms (`adapters.py` l.202–216). Tests cover only pass-through, normalisation and rejection (`tests/test_connectors.py` l.107, l.322; `tests/test_evaluation_record_v1.py` l.291). Spec v1.5 says only that GMP is "sentiment-only and cannot dominate the result" (§13 l.589). | **v1.5 does not explicitly adopt the v1.3 definition.** The v1.5 spec, technical design and execution prompt never define GMP trend. The v1.5 config copies the labels and points from the reference config (`handoff/reference/ipo-config.json` l.125–126) without any definition. The manifest ranks v1.3 as reference material that yields to v1.5 on conflict, with no adoption statement (manifest l.8–9, l.19–22, l.50–52). The prototype treats the label as a manual choice (`ipo-scorer_4.html` l.257). v1.3 says "Stable/rising >10% = 2; flat = 1; falling = 0" (l.123) but does not say whether ">10%" means GMP as a share of the issue price or the size of a rise. It also defines no comparison interval, no lookback and no line between "stable" and "flat". That ambiguity is preserved here; §12.2's inference is not relied on. | Is `market.gmp.trend` **(a)** a publisher-supplied label passed through, as v1.5 implements today, or **(b)** derived by the project with the v1.3 meaning? Only under (b): what ">10%" measures, and the comparison interval. | **None; this is Ramki's product judgment.** Under (a), MarketLiveIPOGMP publishes no label [ML-T:7–9], so `trend` is null and `gmp_trend` is UNKNOWN, with no change needed. Under (b), a derivation rule, implementation authority and tests are needed. |

### 13.3 Implementation dependencies (documented; nothing changed)

- **PR-1 vs the future-stamp tolerance.** The generic snapshot accepts an `as_of` up to 1 h after the evaluation time as FRESH (`snapshots.py` l.460). PR-1 requires a stamp at or before `GMP_CUTOFF`, so the A9 qualified path would have to enforce that itself. Changing the generic tolerance would alter existing scoring behaviour.
- **PR-1 vs the input schema.** PR-1's condition "retrieved at or before the evaluation timestamp" cannot be represented today. `market.gmp` carries only `as_of`, `pct`, `trend` and `source_id`, with `additionalProperties: false` (`schema/ipo-input.v1.5.schema.json` l.978–1000). This falls under §9 item 4, which needs implementation authority.

### 13.4 Unchanged

- **MarketLiveIPOGMP:** NOT QUALIFIED; the leading candidate.
- **PapsDigital:** closed as an alternative.
- **InvestorGain:** NOT QUALIFIED.
- **R7:** UNRESOLVED.
- **A9:** fail-closed; Final withheld.
- **No code or contract change.** No engine, schema, configuration, test, fixture or result-hash change. The full test suite passed on `6ecd26c` (710 tests, fresh run); this addendum changes only documentation and evidence metadata.

**Files cited in §13 by short name:**

| Short name | File |
|---|---|
| A8 | `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` |
| A8-M observation contract | `handoff/decisions/A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md` |
| A9 | `handoff/decisions/A9-missing-gmp-final-fail-closed.md` |
| spec v1.5 | `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` |
| v1.3 | `handoff/reference/Claude_IPO Screening Engine v 1.3 — Specification.md` |
| manifest | `handoff/authoritative/ARENA_IPO_Screening_Artifact_Manifest_v1.5.md` |
| `ipo-scorer_4.html` | `handoff/reference/ipo-scorer_4.html` |
| engine files | under `engine/ipo_screening/` |

## 14. Decisions adopted — 2026-10-15 (A17)

Ramki approved three product decisions, recorded as user-approved policy in [`handoff/decisions/A17-gmp-cutoff-freshness-and-trend-labels.md`](../../handoff/decisions/A17-gmp-cutoff-freshness-and-trend-labels.md). This addendum maps them onto this record. Nothing above is edited.

| This record | Disposition under A17 |
|---|---|
| §8 PR-1 (cutoff); §13.2 row 1 | **Adopted as A17-1.** `GMP_CUTOFF` is the evaluation timestamp. A reading stamped after it is ineligible, with no one-hour allowance. A missing, malformed or offset-less stamp fails closed. PR-1's "latest reading" selection and "retrieved at or before the evaluation timestamp" clause are not part of the approved text and stay open. |
| §8 PR-2 (maximum age); §13.2 row 2 | **Adopted as A17-2.** `MAX_AGE` is the existing `market_staleness_hours` (24 h), measured from the evaluation timestamp. |
| §9 item 3; §12.2; §13.2 row 3 (trend) | **Resolved by A17-3.** Only publisher-supplied labels count; the v1.3 definition is not adopted. MarketLiveIPOGMP publishes no trend label [ML-T:7–9], so its `trend` is null and `gmp_trend` is UNKNOWN. |
| §8 PR-3 (artifact and hash), PR-4 (fail-closed mapping), PR-5 (single source) | **Not adopted.** The approval instruction's "PR-3" is A17-3 (trend), not this record's PR-3. |
| §13.3 dependency 1 (future-stamp tolerance) | **Implemented for GMP only**, without modifying the frozen `snapshots.py` (A17, "Implementation"). |
| §13.3 dependency 2 (no retrieval-time field) | **Still open.** It belongs with §9 item 4. |

**Determinations are unchanged.** §7 recorded R3 and R4 as UNRESOLVED only because PR-1 and PR-2 had not been adopted. A17 adopts them, but this addendum does not re-score R3, R4 or any other requirement.
- **MarketLiveIPOGMP: NOT QUALIFIED** (the leading candidate). R5–R8 remain open, and R7 needs source evidence.
- **PapsDigital:** closed as a non-independent alternative.
- **InvestorGain:** NOT QUALIFIED.
- **A9:** fail-closed; Final is withheld.

**R7 is unchanged.** No capture was made in this pass. It ran at 22:07 IST, 40 minutes after the last capture (§13.1) and before the 16 Oct IST daytime window inferred there. The single follow-up capture condition in §13.1 still applies. The approved cutoff, freshness and trend policy says nothing about the publisher's retention, append-only behaviour, corrections or historical availability.

## 15. A17 follow-through — 2026-10-15, 17:17 UTC (focused qualification gap matrix)

This addendum applies the approved A17 decisions to MarketLiveIPOGMP's outstanding requirements. It reuses §§1–14 and the retained evidence; nothing above is edited, and no publisher page was captured.

- "A17-1/2/3" are Ramki's approved decisions.
- "§8 PR-n" always means this record's proposals, which remain unadopted except as mapped in §14.
- §7's source-fact findings for R3, R4 and R8 are not reopened.
- In two cases §7's overall status waited only on a project rule that A17 now supplies: the cutoff for R3 and the maximum age for R4. The resulting status for those is given below.
- R8's dependency on §8 PR-3 is not supplied by A17.

### 15.1 Verification and limits

- **Baseline:** `arena/573e69a4-ipo-screening-engine` and `arena/5ccbfd5d-ipo-screening-engine` were both at `5bb5eae1f35d41e6f670af0be77064bc178390a5` (tree `d619a5a`), verified with `git ls-remote` and a fetch at 17:17 UTC. This addendum is committed on `arena/5ccbfd5d-ipo-screening-engine`.
- **Evidence integrity:** all 20 retained files in the three `evidence/gmp-observations/` packages match their capture-manifest byte counts and SHA-256 digests.
- **Capability:** direct retrieval is still impossible.
  - `curl` to `https://marketliveipogmp.com/robots.txt` failed with `(35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL` at 17:26:00.814Z–17:26:00.885Z, and no content was retrieved.
  - The sandbox clock matched the `api.github.com` `Date` header (17:26:01 GMT).
- **Cache limit (applies to every capture in this record):** the fetch tool does not disclose cache status (capture manifest `captureMethod.toolCacheStatusDisclosed: false`).
  - Content returned inside a retrieval window was therefore published no later than the window's end.
  - A byte-identical recapture shows what the tool returned. It does not prove that the publisher's page was unchanged at that moment.

### 15.2 R7 — condition not met; no capture

- **Trigger (§13.1):** a Tonbo reading stamped after "15 Oct, 4:02 pm IST", before "Closes 19 Oct". It can be checked only by capturing.
- **When the decision was made:** 17:26 UTC (22:56 IST) on 15 Oct.
  - That was 1 h 28 min after the last capture (21:27 IST).
  - It was before the 16 Oct IST daytime that §13.1 item 5 infers is the earliest likely time for a new reading.
- **Outcome:** a capture then would have been an immediate repeat, so **none was warranted or taken**.
- **Status:** R7 remains **UNRESOLVED**. The §13.1 condition, test and reading of results are unchanged, and the capture remains possible until bidding closes on 19 Oct.

### 15.3 Additional observations and inferences from retained evidence

No new capture underlies these.

- **ML-O12 — One stamp for every displayed reading.**
  - All nine home-page cards that show a GMP value, covering open and upcoming issues, end with the same "4:02 pm" [ML-H:57, 82, 107, 132, 180, 205, 230, 283, 306]. This matches "Updated Thu, 15 Oct, 2026 at 4:02 pm IST" [ML-H:5].
  - The two "Not quoted yet" cards show no time [ML-H:141–155, 239–253].
  - Eight of the nine show a non-zero "since last" change. Paras Healthcare shows a value and the stamp but no change line [ML-H:284–306].
- **ML-O13 — Signed values.** The site displays negative premiums ("₹-51" [ML-TR:42]; "Range so far: -₹2 low" [ML-HM:15]) as well as "₹0" [ML-HM:7] and "Not quoted yet".
- **I4 — Stamp granularity (inference).**
  - ML-O12 fits a batch sync time applied to every displayed reading, consistent with I2.
  - Paras's missing change line fits either of two readings: a first reading, or an unchanged value re-stamped at the sync with its zero change not displayed. The evidence therefore does not show whether a stamp marks when a value was first recorded or the latest sync that carried it.
  - ML-O7, a reading described as published "before listing" but stamped on listing day, fits either re-stamping or an inaccurate claim.
- **I5 — Zero is numeric (inference).** Because signed values are displayed (ML-O13), "₹0" sits on a numeric scale rather than acting as a missing-value marker. The publisher does not say so.

### 15.4 Gap matrix — MarketLiveIPOGMP

| Row | Requirement | Disposition | What closes the gap |
|---|---|---|---|
| Q1 | Publisher identity and its relationship to the displayed observation (R1) | **PASS** | — |
| Q2 | Displayed value and its source-native context (R2; R5 representation) | **PASS** for the value; **BLOCKED** for source-native context | D1, or a capture environment that can reach the host |
| Q3 | Meaning of the displayed timestamp (R3) | **PASS**, with a limitation carried to Q7 | — |
| Q4 | Availability by the A17 cutoff (R8) | **UNRESOLVED** | D2, then a prospective capture |
| Q5 | Evidence artifact and hash subject/representation (R5) | **UNRESOLVED** | D1, then IMP-1 |
| Q6 | Missing, zero, stale, corrected and conflicting observations (R6; R4; R7) | Stale **PASS**; missing vs zero **UNRESOLVED**; corrected and conflicting **UNRESOLVED** | D3; E1 |
| Q7 | Corrections, historical retention and append-only behaviour (R7; R8) | R7 **UNRESOLVED**; R8 partly open | E1, then the §9 post-listing checks |

Each row below gives:
- (a) existing evidence;
- (b) what it proves;
- (c) what it does not prove;
- (d) whether more evidence is obtainable with this environment and permissions;
- (e) the resulting disposition.

D1–D3, E1 and IMP-1 are defined in §15.5.

**Q1 — Publisher identity and its relationship to the displayed observation (R1)**

- **(a) Existing evidence:**
  - the named site and domain [ML-A:1];
  - the issue page, which carries the value and its stamp [ML-T:1–13, 84];
  - readings presented as the site's own: "Every premium we published" [ML-TR:3]; "the one published here" [ML-HM:49];
  - the sourcing claim ML-C1 and a corrections contact [ML-A:27];
  - no operating entity named (ML-O11);
  - value overlap with InvestorGain, with one counter-example (ML-O9).
- **(b) Proves:** the observation is this named publisher's own reported reading for the identified issue, which is what Model A requires (policy §1).
- **(c) Does not prove:**
  - who operates the site;
  - that the quotes come from "dealer channels";
  - what the cross-check is, or what it found;
  - independence from InvestorGain (I3).
- **(d) Obtainable:** no.
  - Operator and sourcing facts would need provider contact, which is excluded, or hosts this environment cannot reach.
  - Independence would need the publisher's stored readings, which are unreachable (§15.1).
- **(e) Disposition:** **PASS** (R1, §7). Two constraints carry forward:
  - it is labelled as MarketLiveIPOGMP's reported value, never as a dealer quote (policy §1);
  - it is never corroborated with InvestorGain (I3).

**Q2 — Displayed value and its source-native context (R2; R5 representation)**

- **(a) Existing evidence:**
  - the ML-T rendered text (1,693 B, SHA-256 `33516F86…705D`), retrieved 13:15:14–13:17:58Z;
  - three byte-identical recaptures, the last ending 15:57:59Z;
  - the value, percentage, change and stamp [ML-T:7–13], restated with year and weekday [ML-T:84];
  - arithmetic that reproduces (ML-O2);
  - the definition and units [ML-L:7, 25].
- **(b) Proves:** one internally consistent observation, as returned by the fetch tool:
  - ₹500 per share over the ₹700 price (+71.4%);
  - "▲₹32 since last reading";
  - "as of 4:02 pm IST on Thu, 15 Oct, 2026".
- **(c) Does not prove:**
  - provider response bytes, headers or receipt time (none was captured);
  - the chart's stored readings, or anything rendered client-side (ML-O8; README l.31);
  - transcription fidelity against the tool output (README l.33);
  - the price band (ML-O10).
  - Rendered or local evidence leaves source-native qualification open (tracker l.30, l.107). These are the precedent rows cited above as l.29 and l.106; A17's header bullet renumbered them.
- **(d) Obtainable:** no. Direct retrieval fails (§15.1), and the fetch tool returns rendered text only.
- **(e) Disposition:**
  - Value: **PASS** (R2, §7).
  - Source-native context: **BLOCKED** here. Only D1, or a capture environment that can reach the host, can close it.

**Q3 — Meaning of the displayed timestamp (R3)**

- **(a) Existing evidence:**
  - One stamp per reading: "15 Oct, 4:02 pm" with "IST" [ML-T:11–13].
  - The publisher's own words:
    - the value is "as of 4:02 pm IST on Thu, 15 Oct, 2026" [ML-T:84];
    - a final reading was "recorded at 3:37 pm IST" [ML-HM:128];
    - "Each reading is stored with a timestamp" [ML-A:11].
  - The same instant appears as (ML-O3):
    - the "Last data sync" [ML-A:3];
    - the site-wide "Updated" line [ML-H:5];
    - the sitemap `lastmod` `2026-10-15T16:02:00+05:30` [ML-S:1];
    - the subscription "as of" [ML-T:60].
  - Every displayed reading shares it (ML-O12).
  - An ageing reading keeps its stamp (ML-O5).
  - A final reading is stamped on listing day (ML-O7).
- **(b) Proves:**
  - The stamp is a source-supplied IST time, fully dated (the year is given in [ML-T:84]).
  - The publisher itself calls it the reading's "as of" and "recorded at" time.
  - It is the site-wide data-sync (batch) time.
  - **Classification: publisher update (recording/sync) time.** It is not an event time.
  - Normalising "IST" to +05:30 uses the publisher's own sitemap offset, not an assumed zone.
- **(c) Does not prove:**
  - when the underlying grey-market quote prevailed (never exposed; I2);
  - when the reading first became publicly visible (no separate publication time is shown; see Q4);
  - whether a stamp marks the first recording of a value or the latest sync that carried it (I4).
- **(d) Obtainable:** no. That would need the publisher's stored readings or a statement from the publisher. The pending R7 capture could show one new stamp with its change, but cannot define the stamp's meaning.
- **(e) Disposition:** **PASS** on source facts (§7, not reopened).
  - A17-1 now supplies the cutoff that §7 found missing. This stamp, the only source time exposed, is what A17-1 compares.
  - This answers A17's unresolved dependency 2 for this publisher. It is an investigation finding, not an approval.
  - A17-1 also excludes listing-day recordings (ML-O7) from any evaluation timed before them.
  - **Limitation, carried to Q7:** if a sync re-stamps unchanged values (I4), A17-2 measures age from the latest "as of" stamp rather than from when the value was first recorded. Whether a re-stamp reflects re-confirmation is unverified publisher behaviour.

**Q4 — Availability by the A17 cutoff (R8 "evaluation-time availability")**

- **(a) Existing evidence:**
  - Retrieval windows are bracketed by a sandbox clock checked against `api.github.com` (capture manifest).
  - ML-T's window ends at 13:17:58.770Z. The stamp normalises to 10:32:00Z (capture manifest `normalizedSourceTimeUtc`).
  - A17-1 and A17-2 compare only the stamp. §8 PR-1's "retrieved at or before the evaluation timestamp" clause was not adopted (§14).
  - `market.gmp` has no retrieval-time field (schema l.978–1000; §13.3).
- **(b) Proves:**
  - The ₹500 reading had been published by 13:17:58.770Z (see the §15.1 cache limit).
  - For an evaluation timestamp between then and 2026-10-16T10:32:00Z (the A17-2 limit), the retained capture shows the reading was available by the cutoff.
- **(c) Does not prove:**
  - Availability before 13:15:14Z. The stamp asserts "as of" 10:32Z, but no publication time is exposed and no earlier capture exists.
  - The engine also cannot record retrieval evidence, and A17 does not make availability an eligibility condition.
  - **Tonbo Final:** for an evaluation on or after the 19 Oct close, every retained reading is more than 24 h old. All are therefore ineligible under A17-2, whatever the qualification outcome.
- **(d) Obtainable:** only going forward. That means a capture whose retrieval window ends at or before the chosen evaluation timestamp, of a reading stamped within the 24 h before it. A mutable page cannot supply this after the fact.
- **(e) Disposition:** **UNRESOLVED** — it needs D2, then prospective evidence. Until then, A17-1 accepts a reading stamped at or before the cutoff without proof that it was visible by then.

**Q5 — Evidence artifact and hash subject/representation (R5)**

- **(a) Existing evidence:**
  - The retained rendered-text files and the capture manifest.
  - The hash subject is the exact local file bytes, digested with SHA-256 in uppercase hex (README "Hash subject"). All 20 files were re-verified (§15.1).
  - The A9 decision defines no GMP hash subject (A9 l.30, l.50).
  - The A9 gate refuses a generic market-snapshot digest and an opaque `SourceRef.content_hash` (`evaluation_record.py` l.929–937).
  - §8 PR-3 was drafted but not adopted (§14).
- **(b) Proves:** the integrity of the retained local files, and a reproducible procedure for re-hashing them.
- **(c) Does not prove:**
  - provider-byte identity, source authenticity or transcription fidelity (capture manifest `a9HashStatement`);
  - that any artifact is acceptable as A9 GMP evidence, because no rule says which is.
  - Nor is there anywhere to carry a GMP artifact hash:
    - `market.gmp` holds only `as_of`, `pct`, `trend` and `source_id`;
    - the A15 record's generic digests, such as `market_snapshot_hash`, are deliberately not accepted by the gate.
- **(d) Obtainable:** no provider bytes (§15.1). More rendered captures are possible, but they add nothing until D1 decides whether rendered text is acceptable.
- **(e) Disposition:** **UNRESOLVED** — it needs D1, then IMP-1. No evidence obtainable here closes it.

**Q6 — Missing, zero, stale, corrected and conflicting observations (R6; R4; R7)**

| State | (a) Displayed by the source (observed) | (b) Established | (c) Not established |
|---|---|---|---|
| Missing | "Not quoted yet", with no stamp and "Est. listing —" [ML-H:141–155, 239–253]. For listed issues: "Final GMP … Not quoted yet" and "GMP said —" (ML-O6). | Displayed distinctly from any number. | A definition. How missing finals are retained: the unquoted listings are absent from the track-record chunk (ML-O6). |
| Zero | "₹0" / "0.0%" [ML-HM:5–7], counted in the track record (ML-O6). Signed values are shown (ML-O13). | Displayed as a number on a signed scale (I5). | A definition. The only example is a listing-day recording (ML-O7); no pre-listing zero was observed. |
| Stale | No stale marker; the original stamp stays (ML-O5). Claim ML-C3. | The stamp is the staleness signal, and A17-2 computes staleness from it. | Refresh failure beyond the stamp. ML-O5 is subject to the §15.1 cache limit. |
| Corrected | Nothing observed. Claim ML-C4. | — | Any correction marker or disclosure. No corrections page appears among the retained site-level sitemap entries [ML-S:1]; chunks 1–3 were not retrieved. |
| Conflicting | One value per reading. Claim ML-C1 ("cross-checked"). | — | The cross-check outcome, precedence, or any conflict marker. |

- **(d) Obtainable:**
  - Definitions: no, because provider contact is excluded.
  - A pre-listing ₹0 or a correction would have to appear unprompted. Searching other issue pages for one would be the broad search this pass excludes.
  - The §13.1 capture tests only for an in-place change.
- **(e) Disposition:**
  - Stale: **PASS** (R4). The §7 source facts stand, and A17-2 now sets the maximum age.
  - Missing vs zero: **UNRESOLVED** (R6). D3 can close it.
  - Corrected and conflicting: **UNRESOLVED** (R7). This needs source evidence (Q7). §8 PR-4f and PR-5 would limit exposure, but cannot establish the publisher's behaviour.

**Q7 — Corrections, historical retention and append-only behaviour (R7; R8)**

- **(a) Existing evidence:**
  - Claims ML-C2 (never overwritten), ML-C4 (corrections disclosed) and ML-C5 (final frozen).
  - The text shows only the range and axis labels, with no list of readings (ML-O8).
  - "▲₹32 since last reading" implies a previous reading of ₹468 (ML-O9).
  - Four retrievals of the 4:02 pm reading, from 13:15:14Z to 15:57:59Z, are byte-identical (capture manifest `derivedChecks`).
  - ML-O7 contradicts the "before listing" part of ML-C5.
- **(b) Proves:**
  - As returned by the tool, the 4:02 pm reading's value and stamp were the same at all four retrievals across those 2 h 43 min (subject to the §15.1 cache limit).
  - The publisher keeps at least the previous value and the range. That is consistent with stored readings, but does not prove them.
- **(c) Does not prove:**
  - append-only storage;
  - disclosure of corrections;
  - freezing of final readings;
  - any reading before 13:15Z on 15 Oct;
  - whether past readings stay available to third parties.
  - A future pair of readings can only be consistent for that pair (§13.1).
- **(d) Obtainable:**
  - the single §13.1 capture, which needs a newer reading (§15.2);
  - the §9 post-listing checks after 23 Oct.
  - The chart's stored readings are unreachable here (§15.1).
- **(e) Disposition:**
  - R7: **UNRESOLVED** — it needs source evidence, and no project rule can close it.
  - R8: **PASS** for the identity of a captured observation (§7, not reopened).
  - R8: **UNRESOLVED** for history before capture, for correction information (R7) and for evaluation-time availability (Q4).

### 15.5 What remains

| ID | Exact missing item | Type | Closes | Obtainable here |
|---|---|---|---|---|
| E1 | The §13.1 single capture of a reading stamped after 15 Oct 4:02 pm IST, before "Closes 19 Oct"; then the §9 post-listing checks | Source evidence | R7, progressively; one pair never closes it | Yes. One capture, during IST daytime on 16 Oct or later (§13.1 item 5), before bidding closes on 19 Oct |
| D1 | Artifact and hash rule for A9 GMP: accept the rendered-text capture with a file-byte SHA-256 (§8 PR-3), or require provider bytes. §8 PR-3 departs, for GMP only, from the rendered-capture precedent (tracker l.30, l.107). Requiring provider bytes blocks qualification from this environment (§15.1). | Ramki decision | R5; part of R8 | — |
| D2 | Evaluation-time availability: require a retained capture whose window ends at or before the evaluation timestamp (§8 PR-1's unadopted clause), or accept a later capture of an earlier-stamped reading. For NIFTY only, A8-M's approved contract already requires the close to be "demonstrably available by that cutoff" (A8-M observation contract l.23). | Ramki decision | R8 availability (Q4) | — |
| D3 | Missing vs zero: "Not quoted yet" ⇒ `MISSING` and a displayed ₹0 ⇒ `SOURCE_UNQUALIFIED` (§8 PR-4a/4b), or another fail-closed rule | Ramki decision | R6 | — |
| IMP-1 | The A9 qualified path; GMP snapshot, hash and retrieval-time representation; capture tooling; and tests | Implementation | Final eligibility | Not before D1–D3. Not incidental work: no retrieval-time field, hash contract or schema change is made here |

The rest of §8 PR-4 is already covered:
- PR-4c (a missing or unparsable stamp, or no IST label) is covered by A17-1's fail-closed rule.
- PR-4d (a stamp on or after the listing date) is covered by A17-1 for any evaluation timed before the listing-day stamp.
- PR-4e (over-age) is covered by A17-2.

§8 PR-4f and PR-5 stay open with IMP-1.

### 15.6 Consequences — no change made

- **No scoring effect, even if qualified.**
  - MarketLiveIPOGMP publishes no trend label [ML-T:7–9].
  - `gmp_bucket` reads only `market.gmp.trend` (`derived.py` l.1721–1723).
  - `pct` is not scored. It only separates `MISSING` from `SOURCE_UNQUALIFIED` in the A9 gate (`evaluation_record.py` l.956–958).
  - Under A17-3, qualifying this publisher could therefore never make `gmp_trend` scorable unless it begins publishing a label. After D1–D3 and IMP-1, it could only let a `pct` observation meet A9's Final snapshot requirement.
- **The retained reading has no scoring effect in any mode.**
  - Under A17-2 it is fresh only for evaluations up to 2026-10-16T10:32:00Z, while Tonbo's bidding is still open.
  - A9 applies only to Final, and the reading carries no trend label.
- **No runtime or evidence change.**
  - Only this record and the tracker's GMP row changed.
  - No engine, schema, configuration, test, fixture or evidence file was changed.
  - No application test was rerun, because nothing executable changed.

### 15.7 Determination — unchanged

- **MarketLiveIPOGMP: NOT QUALIFIED** (the leading candidate).
  - After A17, R1–R4 are met within the limits stated in Q1–Q3 and Q6.
  - R5 (D1), R6 (D3), R7 (E1) and R8 (D2, R7 and D1) remain open.
- **InvestorGain:** NOT QUALIFIED.
- **PapsDigital:** closed as a non-independent alternative.
- Neither InvestorGain nor PapsDigital is reassessed; no new evidence bears on them.
- **A9:** fail-closed; Final is withheld.
- **Smallest next actionable step:** E1 — one capture during IST daytime on 16 Oct, under §13.1. The opportunity ends when bidding closes on 19 Oct.
- Qualification also needs D1–D3. Even then, `gmp_trend` stays UNKNOWN (§15.6).

**Files cited in §15 by short name** (in addition to the §13 table):

| Short name | File |
|---|---|
| policy | `docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md` |
| A17 | `handoff/decisions/A17-gmp-cutoff-freshness-and-trend-labels.md` |
| tracker | `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` |
| capture manifest, README | `evidence/gmp-observations/marketliveipogmp-tonbo-20261015/capture-manifest.json`, `…/README.md` |
| schema | `schema/ipo-input.v1.5.schema.json` |

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
