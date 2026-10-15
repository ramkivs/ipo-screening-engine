# A9 — InvestorGain Publisher-Level GMP Qualification Assessment

**Record ID:** `A9-GMP-INVESTORGAIN-QUALIFICATION-2026-10-15`
**Date:** 2026-10-15
**Candidate:** InvestorGain (`https://www.investorgain.com/`), the first named publisher assessed under the selected Model A policy
**Issue record assessed:** Tonbo Imaging India IPO, publisher page ID `2369`: `https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/`
**Baseline:** `arena/573e69a4-ipo-screening-engine` at `31f04e8f0d50f3bc05a5236f9664e350eefe6e03`, remote-verified 2026-10-15. A9 implementation commit `953b621ed27a2bdd1a2e06232f275687810e59d9` is an ancestor. The authoritative branch advanced to `97b2eb5a2c7fbfa48b51dce1dd9ef84b5ab4cf0a` during this pass; that tip was merged without modification.
**Publication branch:** Arena session branch `arena/ba8f663e-ipo-screening-engine`, a fast-forward descendant of authoritative tip `97b2eb5`.
**Parallel record:** [`A9-INVESTORGAIN-PUBLISHER-QUALIFICATION-2026-10-15.md`](A9-INVESTORGAIN-PUBLISHER-QUALIFICATION-2026-10-15.md) (`97b2eb5`) reaches the same NOT QUALIFIED result but assigns different statuses to some requirements; see §11.
**Evidence package:** [`evidence/gmp-observations/investorgain-tonbo-20261015/`](../../evidence/gmp-observations/investorgain-tonbo-20261015/README.md)
**Determination:** **NOT QUALIFIED.** A9 remains fail-closed. Final, scoring, and implementation are unchanged and not authorized to change.

## 1. Determination

| # | Requirement | Result | Decisive evidence |
|---|---|---|---|
| 1 | Publisher identity and traceable issue-specific observation | **PASS** | Named operator; ₹495 observed on the publisher's own issue page [DS:87, DS:116–122; T0:17; D0:44] |
| 2 | IPO identity and exact semantics of the published GMP value | **FAIL** | Identity and per-share unit resolved. The engine's scored `market.gmp.trend` has no source-defined counterpart, and the page's own GMP statistics conflict (O5, O6, O8). |
| 3 | Observation vs publication/retrieval time, timezone, cutoff compatibility | **FAIL** (cutoff part BLOCKED) | Three undefined time fields for one value; no timezone anywhere; no GMP cutoff defined (O1–O4) |
| 4 | Evidence-backed freshness and stale-observation behavior | **FAIL** | Only "updated regularly throughout the day"; the "updated" time advances without a new entry [T1:7; O2] |
| 5 | Retained artifact and reproducible hash with defined subject | **BLOCKED** | Local-file SHA-256 established; provider bytes, headers, and receipt time not obtainable; A9 hash subject undefined |
| 6 | Missing value vs genuine zero | **FAIL** | One row shows the same state as `--` and as `0`; first entry `+₹0`; unknown derived inputs rendered as 0 (O6, O7) |
| 7 | Conflict, correction, revision, and precedence | **FAIL** | No correction policy; accuracy disclaimed; internal conflicts with no precedence [DS:64–66; O5] |
| 8 | Retained history sufficient to reproduce the evaluated observation | **FAIL** | Mutable table only; positional rows without year or timezone; no versions (O4, O10) |

**Result definitions.**
- **PASS:** accessible evidence satisfies the requirement for a Model A declared source.
- **FAIL:** the publisher's accessible material does not expose, or contradicts, what the requirement needs. Capturing more of the same material cannot cure it.
- **BLOCKED:** cannot be decided with the capture capability or authority available in this pass.

Any FAIL or BLOCKED requirement prevents qualification.

## 2. Scope and authority

- The declared source under assessment is InvestorGain's own published GMP value ([policy-selection record](A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md) §1). Dealer identity is not required, and no dealer verification is claimed.
- No provider contact, account, subscription, or purchase was made. Only public pages were requested; `robots.txt` allows `/` for generic agents [R:2–4]. No API path was queried.
- No change is made to engine code, schemas, configuration, tests, fixtures, scoring, result hashes, the in-repository tracker, or the two earlier A9 records.

## 3. Evidence and capture method

Citation keys refer to retained files in `evidence/gmp-observations/investorgain-tonbo-20261015/source-captures/`. `X:n` means line *n* of file X.

| Key | File | Retrieval window, 2026-10-15 (UTC) |
|---|---|---|
| T0 | `investorgain-gmp-tonbo-2369-chunk-0.md` | 12:29:10.103Z – 12:29:12.222Z |
| T1 | `investorgain-gmp-tonbo-2369-chunk-1-redacted.md` | 12:29:50.668Z – 12:29:51.831Z |
| D0 | `investorgain-ipo-gmp-live-331-chunk-0.md` | 12:34:37.198Z – 12:34:38.218Z |
| D2 | `investorgain-ipo-gmp-live-331-chunk-2-redacted.md` | 12:35:02.011Z – 12:35:02.654Z |
| DS | `investorgain-disclaimer-4-chunk-0-redacted.md` | 12:35:22.034Z – 12:35:23.021Z |
| R | `investorgain-robots.txt` | 12:34:24.387Z – 12:34:25.443Z |

- **Mechanism.** Arena's `functions.fetch_page` returned rendered Markdown, not HTML. The sandbox could not connect to the publisher (`curl: (35) … SSL_ERROR_SYSCALL`), so original response bytes, headers, exact receipt time, and cache status could not be obtained.
- **Time basis.** Each window is a pair of sandbox-clock reads taken immediately before and after the tool call. The clock matched the `api.github.com` `Date` header to that header's 1 s resolution. A window brackets the call, not the publisher's generation time.
- **Integrity.** `capture-manifest.json` records SHA-256 over the exact bytes of each retained local file (the hash subject), plus a digest of the reassembled Tonbo page (T0 followed by T1). These are not provider-byte hashes.
- **Redactions.** R1–R3 removed only third-party user comments and broker authorised-person contact blocks, because the repository is public. No GMP figure, timestamp, or publisher GMP/accuracy statement was removed.
- **Change since the prior review.** The [source-model record](A9-GMP-SOURCE-MODEL-DECISION-2026-10-15.md) §B observed a last-recorded ₹500 at 03:37 PM with 40 history entries. This capture shows ₹495 with 41 entries. The ₹500 (03:37 pm) and ₹501 (02:37 pm) entries are still present [T0:82–83].

## 4. Directly observed facts

- **O1 — Current value.**
  - Headline: "last recorded Grey Market Premium (GMP) is ₹495, updated on Oct 15, 2026 05:37:03 PM" [T0:17].
  - Page header: "Last updated: Oct 15th 2026 05:37 PM" [T0:5]; "Live GMP" ₹495 [T0:30–32].
  - Dashboard row: ₹495 (70.71%), Updated-On "15-Oct 17:37" [D0:44].
- **O2 — Time disagreement.** The newest history entry for ₹495 is "15 Oct, 05:02 pm" [T0:81], 35 minutes before the headline time. There is no 05:37 pm entry, although unchanged values are sometimes logged as "Flat" [T0:84, T0:116].
- **O3 — Daily stamps.** The daily rows for 12, 13, and 14 Oct are stamped "23:37" [T0:58–60]. The newest history entries on those days are at 10:37 pm, 10:37 pm, and 04:02 pm [T0:96, T0:86, T0:84]. Each daily value equals that day's newest history value. The 11 Oct row's 23:37 does match the 11:37 pm entry [T0:61, T0:113].
- **O4 — No timezone, no year.** No time on the issue page or the dashboard states a timezone or UTC offset. History rows carry no year [T0:81–121], and dashboard Updated-On values carry no year [D0:39–64].
- **O5 — Internal conflicts.**
  - FAQ: the highest GMP is "₹500, recorded on 14-10-2026" [T1:11].
  - Summary: over 5 sessions, "a low of ₹270.00 and a high of ₹500.00" [T0:22].
  - History: ₹501 on 15 Oct [T0:83] and ₹265 on 12 Oct [T0:112], both outside those figures.
- **O6 — Derived zeros.** The row "11-Oct 23:37 | ₹270 (0.00%) | ₹270 | ₹0" [T0:61] is inconsistent with the basis displayed for the other rows (cap ₹700 [T0:55]; lot 21 [D0:44]). On that basis ₹270 would show 38.57%, ₹970, and ₹5,670. Later rows reconcile: ₹495 × 21 = ₹10,395 and 495/700 = 70.71% [T0:57].
- **O7 — `--` and `0` for one state.**
  - The GMP cell shows "₹ **--** (0.00%)" while the same row shows "0 ↓ / 0 ↑" and "GMP: 0": Shellz India [D0:45], Vaibhav Vyapaar [D0:52], Paramount Syntex [D0:54], Eventions [D0:59], Dove Soft [D0:62], Unitec Fibres [D2:2].
  - Omara Ventures India shows "--" with "0 ↓ / 0 ↑"; its row is truncated at the chunk boundary [D0:64].
  - TNA Solutions shows "--" with "0 ↓ / 10 ↑" and "GMP: 0" at listing [D0:56].
  - Tonbo's oldest entry is "+₹0 | 09 Oct, 11:02 pm | -- Flat" [T0:121].
- **O8 — Trend output.** Trend labels come from "InvestorGain's AI-powered IPO GMP trend model" [T0:53], which has seven classes, Strong Upward through Initial [T1:19]. History rows carry per-entry ▲/▼/-- markers [T0:81–121].
- **O9 — Issue identity.**
  - Name: "Tonbo Imaging India IPO" [T0:11]; "Aerospace & Defense|IPO|BSE, NSE" [T0:13].
  - Dates: opened 15 Oct 2026, closes 19 Oct 2026, listing 23 Oct 2026 [T0:15].
  - Terms: price band ₹665.00–700.00 [T0:26]; issue size ₹852.18 Cr [T0:38]; lot 21 [D0:44].
  - No ISIN or exchange symbol appears.
- **O10 — No versioning.** No correction, revision, or version marker appears in any capture. History numbering is positional, with #1 the newest [T0:79–121], and individual entries have no permalink.

## 5. Publisher claims (not independently verified)

- **C1 — Operator.** "Primish Infotech Pvt. Ltd. ( www.investorgain.com)" [DS:87], with a registered office in Udaipur, Rajasthan [DS:118] and CIN U72900RJ2017PTC056875 [DS:122]. "InvestorGain is an affiliate of Chittorgarh.com" [T0:170].
- **C2 — Provenance, stated inconsistently.**
  - Dealer-based: "GMP is sourced from grey market dealers" [T0:47]; "GMP is traded over the counter through GMP dealers" [D2:84].
  - Not dealer-based: "does not associate with any GMP market operators" [D2:24]; "based on market perception and publicly available sources only" [D2:26]; "based on market sources and perception. We do not work with any GMP operators" [DS:34]; "There is no official dealer" [D2:53].
- **C3 — Unit and basis.**
  - "GMP is the premium per share", distinct from Kostak (per application) and Sub2 (per allotted application) [D2:47–49].
  - Estimated listing price is described three ways: "cap price + today's GMP" [T0:17], "adding up GMP and IPO cap price" [D2:10], and "adding to issue price" [D2:8].
  - Estimated profit is "GMP × Market Lot" [T0:63].
  - The ₹700 cap is called the "issue price" [T0:192].
- **C4 — Update frequency.** "updated regularly throughout the day based on grey market activity" [T1:7].
- **C5 — Accuracy.** InvestorGain does "not guarantee the accuracy, adequacy, or completeness" of any information and is "not responsible for any errors, omissions" [DS:64–66].
- **C6 — Special states.** "Seller Only" and "Buyer Only" market states [D2:84, D2:88]. "GMP activity can start before the price band announcement" [D2:56].

## 6. Inferences (labelled; none is relied on for a PASS)

- **I1 — Timezone.** The displayed times are most likely Asia/Kolkata.
  - Read as UTC, the 17:37:03 update would fall about five hours after T0's window closed (12:29:12.222Z), so any offset below +05:07:51 is excluded.
  - Under IST the update precedes retrieval by about 22 minutes, and the operator is registered in Udaipur.
  - This is still not a source-native offset.
- **I2 — Headline time.** The headline and dashboard time is probably a refresh time, not the time ₹495 was first recorded (O2). The prior review saw the headline time equal the newest entry time (03:37 PM), so the relationship between the two is not stable.
- **I3 — Daily snapshots.** The "23:37" rows are probably end-of-day snapshots of the latest value (O3). The FAQ maximum and the 5-session range probably use those snapshots, which would explain why ₹501 is missing (O5).
- **I4 — Unknown inputs as zero.** The 11 Oct derived fields were probably computed before a price band and lot existed (C6), with unknown inputs rendered as 0 (O6).
- **I5 — Schedule.** All 41 entries fall at :02 or :37 past the hour [T0:81–121], which suggests an undocumented processing schedule.
- **I6 — Downstream sampling.**
  - IPOStation's earlier daily values of ₹280 (11 Oct) and ₹398 (12 Oct) (source-model record §B) match InvestorGain intraday entries [T0:118, T0:102], not InvestorGain's own daily values of ₹270 and ₹425 [T0:60–61].
  - IPOStation's 10 Oct ₹0 matches no 10 Oct InvestorGain entry; the nearest earlier InvestorGain entry is ₹0 on 09 Oct [T0:121].
  - This is consistent with re-publication sampled at different times, not with independent corroboration.

## 7. Requirement assessment

### 7.1 Publisher identity and traceable issue-specific observation — PASS

**Evidence:** C1; O1; O9; issue URL with page ID 2369; the dashboard row links to the same URL [D0:44].

The declared source can be named exactly: InvestorGain, operated by Primish Infotech Pvt. Ltd. according to its own disclaimer. The observation is the publisher's own issue-specific value, ₹495 [T0:17], and the same publisher's dashboard row agrees [D0:44]. Model A does not need dealer identity.

Because C2 contradicts itself, the value may be labelled only as *InvestorGain-reported GMP*. It must not be described as a dealer quote or a verified market observation.

**Limitations:** there is no stable per-observation identifier (O10), and the trace to a specific observation exists only through a retained capture (7.5, 7.8).

### 7.2 IPO identity and exact semantics of the published GMP value — FAIL

**Evidence:** O5, O6, O8, O9; C2, C3, C6.
- Engine input contract: `market.gmp` consists of `as_of`, `pct`, `trend` ∈ {`strong`, `flat`, `falling`, null}, and `source_id` (`schema/ipo-input.v1.5.schema.json`).
- Scored component: `gmp_trend` is a categorical map (strong 2, flat 1, falling 0) over `gmp_bucket` = `market.gmp.trend` (`config/ipo-config.v1.5.0.json`, `gmp_trend` rule and `gmp_bucket` metric).

**Resolved:**
- Issue identity at publisher level (O9). Limitation: no ISIN or exchange symbol.
- Unit and basis of the rupee value: a per-share premium over the cap price (C3), confirmed by the displayed arithmetic [T0:57].

**Unresolved (each is sufficient to fail):**
- (a) **No source counterpart for the scored input.** `market.gmp.trend` is the engine's only scored GMP input. InvestorGain's trend is a seven-class output of an undisclosed model (O8), and its arrows compare only adjacent entries. Neither the publisher nor the repository defines a mapping, and creating one would invent semantics.
- (b) **Undefined `pct` basis.** The engine schema does not define what `pct` is a percentage of. The publisher's own percentage is wrong in at least one row (O6), and it calls the cap price the "issue price" (C3).
- (c) **Conflicting series.** The page publishes several undefined GMP series whose statistics disagree (O5).
- (d) **Unrepresented states.** "Seller Only" and "Buyer Only" (C6) have no defined representation.

**Not a ground for failure under Model A:** the publisher does not disclose what market quantity the value represents (quote, trade, or aggregate) and describes it inconsistently (C2). This is acceptable only if the value is labelled as publisher-reported.

**Would resolve:** publisher-published definitions of its trend classes and value series (not exposed), or a Ramki-approved mapping or derivation rule for `trend` and `pct`. The latter is a contract decision, not evidence.

### 7.3 Observation, publication, and retrieval time; timezone; cutoff compatibility — FAIL (cutoff part BLOCKED)

**Evidence:** O1–O4; I1–I2. Ramki-approved A8 directions in `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` at l.15, l.39, and l.57; unresolved GMP items at l.45. Policy-selection record §3, row 3.

One value carries three times:
- 05:37:03 PM in the headline [T0:5, T0:17];
- 05:02 pm in the history [T0:81];
- 17:37 in the daily row [T0:57].

None is defined as an observation, publication, or processing time. None has a timezone, and history rows also lack a year.

The approved A8 directions require all of the following:
- an actual, source-native timestamped observation;
- the original timestamp and timezone/UTC offset, preserved alongside normalized UTC;
- observation/as-of, publication, and retrieval times kept separate;
- no fabricated observation and no application-generated time in place of source-event time.

IST is well supported (I1), but an inferred offset is not an original offset. Retrieval time exists only as this pass's bracketed windows.

No GMP evaluation cutoff exists (A8-G l.45 lists the source-specific cutoff as UNRESOLVED; the policy record §3 sets none). Compatibility therefore cannot be assessed, and that part is BLOCKED.

**Would resolve:** publisher-defined time fields with a timezone, plus a Ramki-defined cutoff. Raw HTML might carry machine-readable offsets; that is unknown and could not be retrieved here. Otherwise, only an explicit A8-G clarification permitting declared terms could change this result.

### 7.4 Evidence-backed freshness and stale-observation behavior — FAIL

**Evidence:** C4 [T1:7]; O2; I2; I5. A gap from 14 Oct 04:02 pm to 15 Oct 02:37 pm carries no staleness marker [T0:83–84]. A8 l.15 forbids inventing a freshness interval. Policy-selection record §3, row 4.

The publisher states no update interval, stale indicator, or stale-value behavior. Its "updated" time advanced to 05:37:03 PM without a new entry (O2), so that time cannot be used as the age of the underlying value. No allowed-age rule exists, and none is proposed here.

**Would resolve:** publisher-defined update and stale semantics (not exposed), plus a Ramki allowed-age rule. A longitudinal capture series could describe update cadence, but it could not establish stale-value semantics.

### 7.5 Retained source artifact and reproducible integrity hash — BLOCKED

**Evidence:**
- `capture-manifest.json` (`captureMethod`, `artifacts`).
- `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` l.29 and l.106: rendered/local captures leave source-native qualification "OPEN / BLOCKED — evidence required".
- `handoff/decisions/A9-missing-gmp-final-fail-closed.md`, "Unresolved dependencies": the hash algorithm and snapshot representation are undefined.

**Established:** this pass retained the closest representation available, with an explicit, reproducible hash subject: the exact bytes of each local file. That proves the integrity of those files only.

**Blocking:**
- Provider bytes, headers, receipt time, and cache status could not be obtained (§3).
- The repository's own precedent classifies such captures as descriptive evidence that leaves source-native qualification blocked.
- A9's required hash subject is still undefined.

**Would resolve:**
- a raw HTTP capture of the issue page (body bytes, response headers, receipt time) from an environment allowed to reach the publisher, hashed over the raw body;
- a Ramki decision fixing the A9 hash subject.

### 7.6 Missing value versus genuine zero — FAIL

**Evidence:** O6; O7; C6; [T0:121].

The publisher shows one state as `--` in the GMP cell and as `0` / `GMP: 0` elsewhere in the same row (O7). Tonbo's first entry is `+₹0` with no legend [T0:121], and unknown derived inputs appear as zero (O6, I4). Nothing distinguishes "no observation" from "zero premium", and "Seller Only" and "Buyer Only" add undefined non-numeric cases.

As a result, a displayed ₹0 cannot be classified as a genuine zero, and `--` cannot be classified as missing.

**Would resolve:** publisher-defined representations (not exposed), or a conservative mapping approved by Ramki (for example, `--` and ₹0 → MISSING). The latter is a contract decision.

### 7.7 Conflict, correction, revision, and precedence — FAIL

**Evidence:** C5 [DS:64–66]; O2; O5; O10; C2; I6; source-model record §B (shared upstream).

- **No policy.** The publisher states no correction, revision, or precedence policy, and it disclaims accuracy and completeness.
- **No precedence.** The page's own conflicts (O2, O5) carry no stated precedence.
- **No revision trail.** There are no revision markers. Two entries are unchanged between the prior review and this capture, which is consistent with append-only behavior but does not prove it.
- **Undisclosed reconciliation.** How multiple "market sources" are reconciled is not disclosed.
- **No independent corroboration.** Niva Market Watch and IPOStation repeat InvestorGain and cannot corroborate it (source-model record §B; I6).

**Would resolve:** a published correction policy with revision markers (not exposed), or a Ramki precedence rule (for example, "the headline value in the evaluation-time capture governs; later changes are not tracked"). The latter is a contract decision.

### 7.8 Sufficient retained history to reproduce the evaluated observation — FAIL

**Evidence:** O3; O4; O10; §7.5. Policy-selection record §2 ("A currently displayed history is not proof that the same observation was available historically") and §3, row 8.

The publisher's only history is the mutable current table. Its numbering is positional and its rows carry no year or timezone. It has no version or correction information and no immutable or permalinked record.

Reproduction would therefore rest entirely on project-side captures made at evaluation time, which this pass could produce only in rendered form (§7.5). Even then, later publisher revisions could not be detected or classified.

**Would resolve:** immutable or versioned publisher records (not exposed), or a Ramki decision that a raw evaluation-time capture is the reproducibility record.

## 8. Remaining blockers

| Class | Blockers | Resolvable within current scope? |
|---|---|---|
| **Source-intrinsic** (publisher does not expose) | Value-series and trend semantics (7.2); defined time fields and timezone (7.3); freshness and stale semantics (7.4); missing vs zero (7.6); correction and precedence policy (7.7); versioned history (7.8) | No. More capture cannot supply these, and provider contact is out of scope. |
| **Capture capability** | Provider body bytes, headers, and receipt time (7.5); whether raw HTML carries machine-readable times (7.3) | Only outside this sandbox. This would improve 7.5 but cannot cure the source-intrinsic failures. |
| **Policy (Ramki)** | GMP evaluation cutoff (7.3); allowed-age rule (7.4); A9 hash subject (7.5); and, gating every source-intrinsic item, whether declared terms may replace absent source-native semantics | Yes, but only by explicit decision. Nothing is decided here. |

**Smallest useful deliverable (Phase 4B).** This record delivers the evidence package. Because the failures are source-intrinsic, neither further capture nor broad source discovery would change the outcome:
- Niva Market Watch and IPOStation cite InvestorGain as their source.
- The reviewed IPO Watch page also showed times without a timezone (source-model record §B).

The only lever within scope is a narrowly scoped source-contract decision.

## 9. A9 and Final consequences

These behaviors are unchanged:
- Missing GMP remains `MISSING`.
- Present but unqualified GMP remains `SOURCE_UNQUALIFIED`.
- Neither case sets `final_outcome`.
- Final remains withheld.

The runtime gate (`_a9_final_gmp_gate` in `engine/ipo_screening/evaluation_record.py`, from `953b621`) has no qualified path, and none is added.

InvestorGain values must not be entered or labelled as a qualifying GMP snapshot, and the evidence-package digests are not an A9 required hash. Scoring formulas, configuration, schemas, serialization, fixtures, and existing result hashes are unchanged.

## 10. Next action

**Single smallest next action:** a Ramki yes/no decision, with no implementation. The question: may an A9 Model A source contract replace source-native semantics that a publisher does not expose with explicitly labelled, project-declared terms?

- **If no:** InvestorGain remains NOT QUALIFIED and closed. A9 stays fail-closed, and no further InvestorGain work is needed.
- **If yes:** an A8-G clarification is required first, because A8 requires the original timezone/offset. A narrow InvestorGain contract draft would then need to settle:
  - the timezone;
  - which displayed time is the observation time;
  - handling of `--` and ₹0;
  - precedence among conflicting figures;
  - the `trend`/`pct` mapping;
  - an allowed-age rule;
  - the GMP cutoff;
  - the A9 hash subject over a raw-byte capture.

  The draft would still require separate implementation authority.

## 11. Relationship to the parallel InvestorGain record

While this pass was in progress, another session published [`A9-INVESTORGAIN-PUBLISHER-QUALIFICATION-2026-10-15.md`](A9-INVESTORGAIN-PUBLISHER-QUALIFICATION-2026-10-15.md) to the authoritative branch at `97b2eb5` (committed 12:38:56 UTC). It assessed the same issue page with the same retrieval tool about a minute earlier (12:28:07–12:28:47 UTC). Its evidence is under `evidence/market-observations/investorgain-tonbo-20261015/`.

This record does not modify, supersede, or withdraw that record. Ramki should designate which record governs.

**Agreement.**
- Both records conclude **NOT QUALIFIED**.
- Both leave A9 and Final unchanged.
- Both pass requirement 1 and treat requirements 3, 4, 6, and 7 as unmet.
- The two independent transcriptions match exactly on all 41 history rows, the ₹495 headline, "updated on Oct 15, 2026 05:37:03 PM", and the price band.
- That record's `SHA256SUMS` verifies against its capture.

**Differences.**

| # | Parallel record | This record | Basis for this record's status |
|---|---|---|---|
| 2 | PASS | FAIL | The engine's only scored GMP input, `market.gmp.trend`, has no source-defined counterpart (O8). The page's GMP statistics conflict (O5), and its derived fields render unknown inputs as 0 (O6). |
| 3, 4, 6, 7 | BLOCKED | FAIL | The underlying gaps are the same. This record classifies publisher-intrinsic gaps that more capture cannot cure as FAIL (§1 definitions). The full disclaimer (DS), which that record did not retain, adds no definitions or correction policy and disclaims accuracy and completeness. |
| 5 | PASS | BLOCKED | Repository precedent treats rendered/local captures as leaving source-native qualification "OPEN / BLOCKED — evidence required" (tracker l.29, l.106). A9 defines no required hash subject. |
| 8 | PASS | FAIL | The policy-selection record §3 row 8 requires relevant version or correction information. The publisher exposes none (O10). |

**Next action.** The parallel record proposes checking whether InvestorGain publishes evidence that resolves the open requirements. This pass checked the publisher pages most likely to carry it: the issue page, the dashboard's methodology/FAQ text, and the full disclaimer (T0, T1, D2, DS). None defines time fields, freshness, missing values, or corrections. This record therefore treats the §10 policy decision as the smaller next step, without precluding a further publisher-page check.

## References

- [A9 GMP source-policy selection](A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md) §§1–5
- [A9 GMP source-model decision record](A9-GMP-SOURCE-MODEL-DECISION-2026-10-15.md) §B
- `handoff/decisions/A9-missing-gmp-final-fail-closed.md` (approved decision; unresolved dependencies)
- `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` l.15, l.39, l.45, l.57 (Ramki-approved A8 directions and unresolved GMP items)
- `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` l.29, l.106 (precedent for rendered/local captures)
- `schema/ipo-input.v1.5.schema.json` (`market.gmp`); `config/ipo-config.v1.5.0.json` (`gmp_trend`, `gmp_bucket`)
- [Evidence package README](../../evidence/gmp-observations/investorgain-tonbo-20261015/README.md) and `capture-manifest.json`
- [Parallel InvestorGain record](A9-INVESTORGAIN-PUBLISHER-QUALIFICATION-2026-10-15.md) (`97b2eb5`) and `evidence/market-observations/investorgain-tonbo-20261015/`
