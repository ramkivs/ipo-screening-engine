# A9 GMP Source-Model Decision Record

**Record ID:** `A9-GMP-SOURCE-MODEL-DECISION-2026-10-15`
**Date:** 2026-10-15
**Branch:** `arena/573e69a4-ipo-screening-engine`
**Baseline reviewed:** remote branch tip `40317b72f2dbdc9d2e352e8509b8f3b63075c48b`; A9 implementation commit `953b621ed27a2bdd1a2e06232f275687810e59d9`
**Status:** Source-model decision input. Model A is recommended for policy selection only; no source is selected, approved, qualified, or authorized for implementation.

## A. Purpose and status

This record turns the completed public-source review into a decision input for the single-user personal IPO Screening Engine. It does not approve a provider, qualify an A9 source, change the engine, or authorize enabling Final mode.

The preserved A9 baseline is fail-closed: missing GMP is nonterminal with reason `MISSING`; present but unqualified GMP is nonterminal with reason `SOURCE_UNQUALIFIED`. Neither withheld case sets `final_outcome`. A displayed GMP value alone does not satisfy qualification.

Labels used below distinguish **observed page content**, **publisher claims**, **recommendations**, and **unresolved matters**. Observed means visible on a page retrieved during the review; it does not establish the truth of an underlying dealer quote or prove that a page contained the same value historically.

## B. Evidence already established

The public pages reviewed were accessible without an account or paid service during the investigation. The cited pages are mutable. No original response bytes or headers were retained and no evidence hash was computed. The review interface returned rendered page content rather than a preserved raw response. No provider was contacted.

| Publisher/source | Observed page content | Publisher claim and limitation |
|---|---|---|
| **Niva Market Watch** | Its Tonbo Imaging India IPO page displayed GMP ₹500, recorded 15 Oct 2026, and a page update time of 4:00 PM IST. It described three readings from 13–15 Oct with a range of ₹475–₹500. | Niva says its GMP comes from InvestorGain's public report and describes a 30-minute collection schedule. The individual quote time, retrieval time and retained/versioned record are not exposed. |
| **IPOStation** | Its Tonbo GMP page displayed ₹500 with a 4:00 PM IST page update and six dated values: 10 Oct ₹0; 11 Oct ₹280; 12 Oct ₹398; 13 Oct ₹490; 14 Oct ₹500; 15 Oct ₹500. Its issue page refers to 228 readings, but does not expose them individually. | IPOStation says InvestorGain is its primary feed and IPO Watch its cross-check, with material conflicts flagged rather than averaged. That ingest, conflict process and claimed independence were not independently demonstrated. |
| **InvestorGain** | Its Tonbo page displayed a last-recorded ₹500 at 15 Oct 2026, 03:37 PM, with 40 history entries. The visible entries include ₹501 at 02:37 PM and ₹500 at 03:37 PM on 15 Oct. | The page says the GMP is sourced from grey-market dealers but identifies no dealer or dealer-level quote. The displayed times have no stated timezone and do not distinguish quote time from publication or retrieval time. |
| **IPO Watch** | Its Tonbo page displayed ₹500 at 15:40 on 15 Oct, ₹460 on 13 Oct and ₹375 on 12 Oct. Its displayed times have no stated timezone. The page also contained a FAQ stating a ₹285 high/range while its table showed ₹500. | This is an observed page inconsistency, not evidence of how IPOStation resolves conflicts or corrections. |

The publishers' historical values and displayed times differ. Without a shared observation-time definition and timezone, the differences cannot be classified as revisions, different sampling times, or different dealer quotes. Niva and IPOStation both cite InvestorGain; IPOStation also cites IPO Watch. Multiple publishers repeating the same upstream feed do not necessarily provide independent corroboration.

The reviewed pages did not expose an immutable source artifact or a documented GMP export with an explicit hash subject. Both candidate sites' public `robots.txt` files disallow `/api/`; those paths were not queried. Public sitemaps list pages, not versioned GMP observations. A currently visible historical table is not proof that the same record was publicly available at the historical time it describes.

## C. Comparison of source models

| Dimension | Model A — publisher-level observation | Model B — dealer-level observation |
|---|---|---|
| **Declared source** | A specific named publisher's own reported GMP value. The engine makes no claim that the underlying dealer quote was verified. | An identifiable dealer quote or equivalent source-native record, traceable to its origin. |
| **Feasibility and evidence** | More practical: public issue-specific pages and values were observed for the reviewed publishers. The current evidence remains page-level and mutable. | Stronger provenance in principle, but no identifiable dealer quote or source-native dealer record was shown to be publicly obtainable in the completed review. |
| **Provenance strength** | Traceability reaches the selected publisher and, where claimed, its upstream aggregator. It does not establish who quoted the value or how the upstream publisher obtained it. | Stronger if the dealer/source identity and original record are actually exposed and retained. That evidence is currently absent. |
| **Timing** | Some pages show a date or page-level update time; observation, publication and retrieval semantics, timezone and cutoff compatibility remain unresolved. | Could provide stronger event-time evidence only if the native record defines those times and their timezone. No such evidence was observed. |
| **History and artifacts** | IPOStation displays a current day-wise history and InvestorGain a current timestamped history table. Neither demonstrates immutable versions, historical availability at the time, or a preserved source response. | Could support more direct historical reproduction if source-native records are retained with revisions distinguishable. This capability has not been established. |
| **Conflicts and corrections** | Publisher policies are claims, not an observed audit trail. Shared upstream feeds are not independent confirmation; published values differ across pages. | Dealer-level evidence could make source precedence and quote differences more assessable, but conflict, revision and correction rules would still need to be defined. |
| **Implementation implication** | Identify one exact publisher as the declared source and qualify its own published observation. Do not label it a verified dealer quote. | Require dealer identity and source-native evidence before any connector or source contract is considered. No such implementation is authorized by this record. |

## D. Recommendation

**Recommendation — Model A is the more practical candidate for this personal-use application**, subject to an explicit source-policy selection and successful qualification of one named publisher against Section F. Public issue-specific publisher pages offer a feasible evidence starting point without claiming dealer-level verification.

This is a recommendation only. Model A is not selected, approved, qualified, active, or implementation-authorized. The review does not establish that Niva Market Watch or IPOStation currently satisfies the qualification contract. Model B offers stronger provenance, but the required dealer-level evidence has not been shown to be publicly obtainable in the completed investigation. No further broad candidate search is recommended before the source-model policy is selected.

## E. Consequences for A9 and Final mode

- A9 remains fail-closed until a source-specific contract and its supporting evidence are established.
- Missing GMP remains nonterminal with reason `MISSING`.
- Present but unqualified GMP remains nonterminal with reason `SOURCE_UNQUALIFIED`.
- `final_outcome` remains unset for both withheld cases.
- Do not enable Final merely because a publisher displays a GMP value.
- Do not change scoring formulas, thresholds, result hashes, schemas, or previously verified behavior as part of this decision input.
- Current evidence supports qualifying neither Niva Market Watch nor IPOStation.

## F. Minimum requirements for a future source-specific contract

A future qualification assessment must establish only these necessary areas:

1. **Named source and traceable observation identity.**
2. **IPO/issue identity and defined value semantics.**
3. **Observation, publication and retrieval-time semantics**, including timezone and explicit evaluation-cutoff compatibility.
4. **Evidence-backed freshness and stale-value behavior.**
5. **A retained, reproducible source artifact and explicitly defined hash subject.**
6. **Explicit representation of missing values versus a genuine zero value.**
7. **Conflict, revision, correction and source-precedence handling.**
8. **Sufficient historical evidence to reproduce the observation used by an evaluation.**

A hash can establish the integrity of the bytes hashed. It does not independently establish the bytes' source authenticity or the truth of an underlying GMP quote.

## G. Next action

Establish the source-model policy selection (Model A or Model B), then assess **one named source** against Section F using concrete source evidence. Do not reopen broad candidate discovery. Until that work establishes the required contract and evidence, preserve the existing A9 fail-closed behavior.

## Evidence references

- [Niva methodology](https://nivamarketwatch.in/methodology) · [Niva Tonbo issue page](https://nivamarketwatch.in/ipos/tonbo-imaging-india-limited-ipo) · [Niva corrections policy](https://nivamarketwatch.in/corrections-policy)
- [IPOStation methodology](https://ipostation.in/methodology) · [IPOStation Tonbo GMP history](https://ipostation.in/ipo/tonbo-imaging-india-ipo-2026/gmp)
- [InvestorGain Tonbo GMP history](https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/) · [IPO Watch Tonbo GMP page](https://ipowatch.in/tonbo-imaging-ipo-gmp-grey-market-premium/)
- [Niva robots.txt](https://nivamarketwatch.in/robots.txt) · [Niva sitemap](https://nivamarketwatch.in/sitemap.xml) · [IPOStation robots.txt](https://ipostation.in/robots.txt) · [IPOStation sitemap](https://ipostation.in/sitemap.xml)
