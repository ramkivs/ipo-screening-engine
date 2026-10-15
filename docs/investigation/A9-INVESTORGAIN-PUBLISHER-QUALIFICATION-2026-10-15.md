# A9 InvestorGain Publisher-Level GMP Qualification

- **Record ID:** `A9-INVESTORGAIN-PUBLISHER-QUALIFICATION-2026-10-15`
- **Date:** 2026-10-15
- **Branch:** `arena/573e69a4-ipo-screening-engine`
- **Remote baseline reviewed:** `31f04e8f0d50f3bc05a5236f9664e350eefe6e03`
- **Result:** **NOT QUALIFIED** for A9. This is a source assessment, not provider approval.

## 1. Decision and scope

InvestorGain was assessed as the first named publisher under the selected Model A policy. The declared observation is InvestorGain's own published field, not a verified dealer-native quote. The page says its GMP is sourced from grey-market dealers but does not identify a dealer; dealer identity is not required by Model A and is not claimed here.

The public page is identifiable as InvestorGain's Tonbo Imaging India IPO GMP/history page at record path `2369`. During this retrieval it displayed a latest/last-recorded value of **₹495**. The retained capture shows the publisher page and its 41 displayed history entries. This value is evidence of what InvestorGain displayed, not proof of a dealer quote or its truth.

Four mandatory requirements remain blocked (3, 4, 6 and 7 below). Therefore InvestorGain is **NOT QUALIFIED**. No connector, ingestion, A9 gate change, or Final-mode change is authorized.

## 2. Evidence record and limits

**Directly observed:** The page title is `Tonbo Imaging India IPO GMP Today & History`; the URL ends in `/2369/`; the page identifies Tonbo Imaging India IPO and BSE/NSE. It shows a ₹665–₹700 price band, a current/last-recorded GMP of ₹495, and an estimated listing value of ₹1,195. The page's displayed formula is upper price band plus GMP. It defines GMP as a price at which an IPO is traded in an unofficial/unregulated grey market. The page's `GMP Entries` table displays 41 date/time/value rows, including ₹501 at 15 Oct 02:37 pm, ₹500 at 03:37 pm, and ₹495 at 05:02 pm.

The same page says `Last updated: Oct 15th 2026 05:37 PM` and that the ₹495 field was updated at `05:37:03 PM`. Its daily summary labels a 15-Oct ₹495 row `17:37`, while its detailed history's latest row is ₹495 at `05:02 pm`. Those are displayed labels; their timezone and distinct meanings are not stated. The current page's detailed history lists the earlier 15-Oct ₹500 at 03:37 pm before the later 05:02 pm ₹495; this is a displayed sequence, not proof of what the publisher displayed at any earlier retrieval.

**Publisher claims:** The page says its value is sourced from grey-market dealers and says the GMP is updated regularly throughout the day based on grey-market activity. It also states InvestorGain is an affiliate of Chittorgarh.com. These are publisher statements, not independently verified dealer provenance, update guarantees, or legal-entity verification.

**Supplemental observed display:** InvestorGain's linked live dashboard showed Tonbo at ₹495 with `Updated-On` 15-Oct 17:37. It also showed Shellz and Vaibhav with headline `₹--`, a `0 ↓ / 0 ↑` range and dated `GMP: 0` entries. No definition was displayed for the distinction between `--` and `0`.

**Retained artifact:** [Rendered page capture](../../evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md); [SHA-256 manifest](../../evidence/market-observations/investorgain-tonbo-20261015/SHA256SUMS). The primary page was retrieved through Arena `fetch_page` in the recorded window **2026-10-15 12:28:07–12:28:47 UTC (17:58:07–17:58:47 Asia/Kolkata, UTC+05:30)**. The supplemental dashboard excerpt was retrieved **12:31:33–12:31:42 UTC (18:01:33–18:01:42 Asia/Kolkata)**. These are local-clock request-window bounds, not server timestamps.

The retrieval tool exposed rendered content, URL, title, success status and chunk numbers, but not original response bytes, HTTP status or headers. The capture is explicitly a structured transcription of rendered text, not a raw response. **SHA-256 `bd6bea50eed267ef338b9e0fcacbd905ffce4d3044dc89b3f3d367c9f551d772`** is over the exact byte sequence of `evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md` as committed (UTF-8/LF, no canonicalization), as listed in `SHA256SUMS`. It proves integrity of that local capture only; it does not prove source authenticity or quote truth.

## 3. Eight-requirement assessment

| # | Status | Assessment and evidence |
|---|---|---|
| **1. Publisher identity and traceable issue-specific observation** | **PASS** | At Model A's publisher level, InvestorGain is named by the public domain/page title, and the issue-specific page is traceable by URL and path identifier `2369`. The page links the displayed field to Tonbo Imaging India IPO. This does not verify the publisher's legal entity or the upstream dealer. [Capture](../../evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md) |
| **2. IPO identity and exact semantics of the published GMP value** | **PASS** | For the publisher-reported field, the source identifies Tonbo Imaging India IPO, labels the latest field `last recorded GMP`, displays ₹495, defines GMP as an unofficial grey-market price, and calculates estimated listing value as upper band plus GMP. This establishes the meaning of the publisher's displayed observation only; it does not explain how dealer inputs were selected or aggregated, nor establish a dealer quote. [Source page](https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/) · [Capture](../../evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md) |
| **3. Observation vs publication/retrieval time, timezone, and evaluation-cutoff compatibility** | **BLOCKED** | The page presents `Last updated`, `updated on`, `GMP Date` and detailed-history times, but does not define which are quote-observation, publication or retrieval times. The top field time (`05:37:03 PM`) differs from the latest detailed-history time (`05:02 pm`). Source timestamps have no timezone label, and no evaluation-cutoff compatibility can be established. The capture's UTC/IST window is our retrieval window, not the source observation time. [Capture](../../evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md) |
| **4. Evidence-backed freshness and stale-observation behavior** | **BLOCKED** | The page claims regular updates throughout the day and currently displays recent update/history labels. It supplies no maximum age, stale-value rule, or behavior when a source quote is delayed or unavailable. No freshness threshold is inferred. [Source page](https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/) |
| **5. Retained source artifact and reproducible integrity hash with defined hash subject** | **PASS** | The capture retains selected rendered issue fields, the complete 41-row history table, and a selected dashboard excerpt; its manifest reproducibly hashes the exact capture-file bytes. It is a structured rendered-text record, not the complete tool output or raw source response. Raw response bytes, HTTP status and headers were not exposed. [Capture](../../evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md) · [Manifest](../../evidence/market-observations/investorgain-tonbo-20261015/SHA256SUMS) |
| **6. Explicit missing-value versus genuine-zero semantics** | **BLOCKED** | The Tonbo history includes `+₹0`; the linked live dashboard displays `₹--` with a zero range and separate `GMP: 0` entries for other issues. The reviewed pages do not define whether `--` means missing/unavailable or whether `0` is a genuine zero observation or sentinel. [Capture](../../evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md) · [Live GMP dashboard](https://www.investorgain.com/report/ipo-gmp-live/331/) |
| **7. Conflict, correction, revision, and precedence behavior** | **BLOCKED** | The reviewed issue page and linked dashboard do not define conflict resolution, source precedence, correction/revision history, or how overwritten values are distinguished. The difference between page-level update time and history-row time is not itself classified as a conflict; the source supplies no semantics to resolve it. [Source page](https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/) · [Live GMP dashboard](https://www.investorgain.com/report/ipo-gmp-live/331/) |
| **8. Sufficient retained history to reproduce the observation used by an evaluation** | **PASS** | For this captured observation only, the retained file includes the displayed ₹495 field and all 41 history rows returned on the page, so the publisher value can be reproduced and integrity-checked. This does not establish historical availability before capture, publisher-side immutability, or future retention behavior. [Capture](../../evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md) |

## 4. Qualification outcome and remaining blockers

InvestorGain is **NOT QUALIFIED** because requirements **3, 4, 6 and 7** remain blocked. The minimum concrete evidence needed is:

- **Time contract:** a source-specific definition of observation versus publication/update timestamps, timezone, and a basis for explicit evaluation-cutoff compatibility.
- **Freshness contract:** evidence-backed update and stale/unavailable behavior, with any allowed-age rule explicitly set by policy rather than inferred from a displayed update time.
- **Missing/zero contract:** an explicit definition and retained examples that distinguish absent/unavailable GMP from a genuine zero.
- **Conflict/revision contract:** documented source precedence and conflict, correction, and revision behavior, with enough version information to distinguish a correction from an overwritten value.

No such rules or thresholds are invented here. The page's dealer-source statement is not a blocker under Model A, but it cannot be restated as dealer verification.

## 5. A9 behavior and next action

A9 remains fail-closed. Missing GMP remains nonterminal with reason `MISSING`; present but unqualified GMP remains nonterminal with reason `SOURCE_UNQUALIFIED`; neither sets `final_outcome`. Final remains withheld for unqualified GMP. Scoring formulas, schemas, serialization, and established result hashes are unchanged. No provider connector or ingestion was implemented.

**Smallest next action:** assess only whether InvestorGain publishes source-specific evidence resolving the four blocked requirements above. If that evidence is not available through public, permitted pages, keep InvestorGain **NOT QUALIFIED**; no provider contact or broad candidate search is initiated.

## References

- [InvestorGain Tonbo issue page](https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/)
- [InvestorGain live GMP dashboard](https://www.investorgain.com/report/ipo-gmp-live/331/)
- [A9 source-model investigation](A9-GMP-SOURCE-MODEL-DECISION-2026-10-15.md)
- [Selected Model A policy](A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md)
- A9 fail-closed implementation commit: `953b621ed27a2bdd1a2e06232f275687810e59d9`
