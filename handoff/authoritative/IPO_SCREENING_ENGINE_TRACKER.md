# IPO Screening Engine — Project Tracker (Personal-Use Status)

> **Controlling status (A16, 2026-10-14):** Ramki's single-user personal-use objective controls this register. Routine in-scope investigation, implementation, testing, documentation, commit/push on the fixed session branch, and remote verification do not require renewed approval or an independent-review/canonical-selection ceremony. The detailed Candidate M/Phase history later in this file is retained for audit; any blanket procedural hold in it is superseded by A16. Concrete evidence and product-decision blockers remain active only for the specific metric behavior they affect. This is not a production, release, or enterprise programme.

- **Updated:** 2026-10-15 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Working branch:** `arena/573e69a4-ipo-screening-engine` (fixed session branch; do not switch branches)
- **Reference baseline selected by A16:** `3b7c71cd05efc608fdca60eb1a988f5cf19d60a0` (A15 follow-on tip)
- **Published implementation/docs baseline:** `953b621ed27a2bdd1a2e06232f275687810e59d9` (A9 runtime gate commit on the fixed session branch; remote-verified)
- **A9 runtime implementation commit:** `953b621ed27a2bdd1a2e06232f275687810e59d9` (four changed file blobs independently matched the fetched remote ref)
- **A17 GMP policy runtime change (2026-10-15):** built on the remote-verified tip `9e0e4ed562dd49a260482806afc92e7ef98d8a67`. See the A17 section at the end of this file.
- **Fixed-branch tip immediately before A9 work:** `a912d5293b3fa17b32e1a46a5ba118eaac6f7055` (remote-verified A16 baseline).
- **Controlling decision:** `handoff/decisions/A16-personal-use-operating-scope-and-gate-disposition.md`
- **Historical records retained below:** Candidate M `9bad659927616ad7fd3aad2864b6637f095872c5`, A15 implementation `fecdd8220500d7932c93b55b311a5f9830f92572`, A11–A14, and PR #3. They remain unchanged; A16 supersedes blanket process gates for routine personal-use work only.

## Current working baseline

The fixed session branch's 2026-10-14 implementation/docs baseline was `eb912d608ede4e5280618d3f3677ad646b741af5`; A16 Host/Origin hardening was subsequently published at `a912d5293b3fa17b32e1a46a5ba118eaac6f7055`, the tip immediately before this A9 pass. The 2026-10-14 delta-only evidence reconciliation was additive and did not change the application baseline at that time. The 2026-10-15 A9 Final-disposition gate is the current additive runtime change documented below. Candidate M (`9bad659927616ad7fd3aad2864b6637f095872c5`) remains preserved as a historical bounded review candidate, not rebuilt or selected. PR #3 remains an older, separate open PR and is not a prerequisite for using this baseline.

A15's `evaluation-record.v1.json` is an additive persisted artifact. `evaluation.py` differs from its earlier frozen hash only for this A15-reviewed output/persistence path; the v1.6 frozen-core pin now records the reviewed digest. The golden evaluation result remains `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`. v1.5 remains active and v1.6 inactive; no scoring weights or metric thresholds are changed here. This is a personal-use working baseline, not a release or production promotion. A11's historical Phase 0 `OPEN` disposition is not rewritten as closed.

## Current personal-use status register

| Category | Workstream | Verified state / limiting evidence / next action |
|---|---|---|
| **COMPLETED / VERIFIED** | Working baseline and authority | A16 records the current personal-use scope and selects the fixed session branch over Candidate M/PR #3 as the working baseline. Routine progress no longer waits on the historical general Phase 0/Phase 1, reviewer, acceptance, or canonical-selection ceremony. |
| **COMPLETED / VERIFIED** | Deterministic evaluation and A15 persistence | All six frozen-core files verify against the current pin; `verify_golden_result()` passes with hash `e84f8bc0...`; `verify_v1_6_implementation()` reports `PASS` with zero failures/warnings. The v1.6 candidate is still inactive. A generated fixture record verifies as seven payload artifacts and replays to the same hash. |
| **COMPLETED / VERIFIED** | Personal local run path | README, pinned `requirements.txt`, and runbook document isolated Python setup, config validation, deterministic CLI run/verify/replay, and same-origin local UI/API. The API's limited POST scope is explicit; cross-origin workflow writes are rejected. No authentication is provided, so instructions bind to loopback. |
| **COMPLETED / VERIFIED** | Automated regression and self-review | Latest full Python suite (D1–D3 pass, 2026-10-15): 841 passed with two non-fatal Starlette deprecation warnings. Frontend: 55 passed at the prior A16 baseline; no frontend files have changed since. Self-review is recorded as self-review/testing, not independent review. Full evidence and limitations are below. |
| **EVIDENCE-BLOCKED** | NIFTY trend | A8-M's price-index, completed-session, trailing SMA-50/SMA-200, strict supportive/weak, neutral-otherwise, and required-UNKNOWN/Final-withholding semantics remain approved and unchanged. The recovered 245-row close/SMA package is descriptive rendered/local evidence only; source-native bytes and publication/availability by cutoff remain unqualified. Do not assign a category. |
| **EVIDENCE-BLOCKED** | Subscription (A8-S/A10) | The A8-S register and 10-file VNL package already exist on the fixed tree and are blob-identical to the inspected 01a ref. Seven of eight `SHA256-MANIFEST.json` file entries match; its HTML entry expects 313,040 bytes / `2AE7009B…`, while the retained blob is 313,038 bytes / `6BEB26DC…`. Preserve both without rewriting and do not claim full package hash verification. A10 remains evidence/display-only; NSE, BSE and All Exchange stay distinct. The official GraphLogic URL is captured, but the PDF itself and a retained PDF analysis are absent from the inspected refs. Source/event/denominator/cutoff/scoring and missing-input handling remain unresolved. |
| **FAIL-CLOSED / SOURCE CONTRACT OPEN** | GMP (A8-G/A9) | A9's narrow rule is implemented at the A15 Final-disposition boundary: missing/no-value GMP is `MISSING`; any present observation is `SOURCE_UNQUALIFIED` under the current model, so Final has no terminal `final_outcome`. The model has no approved GMP source/qualification or required hash-subject contract; neither a generic local market-snapshot digest nor opaque `SourceRef.content_hash` qualifies. **A17 (Ramki-approved, 2026-10-15) now sets the GMP eligibility rules:** the evaluation timestamp is the cutoff, with no future allowance; the existing 24 h maximum age applies; only publisher-supplied trend labels count. A GMP block that is after the cutoff, over-age, or has a missing, malformed or offset-less timestamp is STALE, so `gmp_trend` is UNKNOWN. No provider, event/as-of, hash or serialization semantics are inferred. MarketLiveIPOGMP and InvestorGain remain NOT QUALIFIED; PapsDigital is closed; R7 is UNRESOLVED. The A17 follow-through gap matrix (`docs/investigation/A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md` §15) finds MarketLiveIPOGMP's R1–R4 met within stated limits. What remains is R7 publisher evidence plus three Ramki decisions: the artifact/hash rule, evaluation-time availability, and missing-vs-zero handling. Even if qualified, the publisher supplies no trend label, so `gmp_trend` stays UNKNOWN. **D1–D3 (Ramki-approved, 2026-10-15)** are recorded in `docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md` §6 and enforced in `engine/ipo_screening/gmp_evidence.py` and the GMP connector:<br>• a rendered capture plus its file hash counts only as a labelled publisher-reported observation;<br>• the capture must have been obtained at or before the evaluation timestamp;<br>• "Not quoted yet" ⇒ `MISSING`, and a displayed ₹0 ⇒ `SOURCE_UNQUALIFIED`.<br>The evaluation contract cannot link a capture to an evaluation, so A9 stays fail-closed. MarketLiveIPOGMP remains NOT QUALIFIED because R7 and R8's history remain open. See the A9, A17 and D1–D3 notes below; valid source qualification remains evidence/policy blocked. |
| **EVIDENCE-BLOCKED** | Peers (A8-P/A5) | `CALIBRATION_EVIDENCE_INSUFFICIENT` remains. The R.K. Fashion filing reports one Banaras Beads peer and CMP, P/E and P/B values as of 2026-09-28, but no exchange-native quote/session, listing date, point-in-time universe or calibration is retained. Do not infer peer eligibility or adopt proposed thresholds. |
| **EVIDENCE-BLOCKED** | Other A8 metrics (VIX, listing gains, anchor) | Keep VIX separate from NIFTY. VNL issue evidence supplies a listing date but not a qualifying listing-session price/cohort. Existing Moneyview evidence supports only a candidate issue-specific anchor amount; quality/cutoff/source qualification remain open, and the 6,020,296-share residual plus Anchor/OFS mapping remain unresolved. Do not infer metric values or thresholds. |
| **MATERIAL-DECISION-REQUIRED** | Unresolved metric contracts | Before using affected metrics, settle any still-open source identity, event/denominator, cutoff/freshness, eligibility/universe, hash/serialization, and missing-input/Final behavior for that metric. Existing A8-M/A9/A10 decisions remain controlling where they actually settle a field; do not reopen settled policy or invent thresholds. These decisions block only the dependent metric, not unrelated app work. |
| **EVIDENCE-BLOCKED** | Golden fixture as live research evidence | The deterministic Vishal Nirmiti fixture is a regression sample, not a source-qualified recommendation. Its current output is `INSUFFICIENT_DATA` (score 35.0) and reports 110 material fields without evidence references. The golden hash proves reproducibility, not truth, freshness, or investment suitability. |
| **DEFERRED / OUT OF SCOPE** | Product architecture and operations | Live streaming providers, external purchases/provider contact, authentication/RBAC, multi-user support, PostgreSQL, enterprise architecture, production deployment, tags/releases, and production activation are not personal-use goals and are not required. |
| **DEFERRED / PRESERVE** | Historical governance artifacts | Preserve Candidate M, PR #3, the original tracker on the governance branch, and the authorization-request draft. Do not merge/close PRs or perform destructive cleanup to make the tracker appear complete. |

## Verification evidence (2026-10-14)

| Check | Result |
|---|---|
| `verify_frozen_core()` | **PASS** — all 6 pinned files match, including the A15-reviewed `evaluation.py` digest. |
| `verify_golden_result()` | **PASS** — `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`. |
| `verify_v1_6_implementation()` | **PASS** — no failures or warnings; this does not activate v1.6. |
| `PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q` | **702 passed**, 2 non-fatal Starlette deprecation warnings. |
| Focused post-review API/UI/lifecycle/record/v1.6 suite | **191 passed**, 2 non-fatal Starlette deprecation warnings. |
| `npm --prefix frontend test` | **55 passed**, 0 failed. |
| Config / persistence / replay smoke check | v1.5 config valid for 10 profile plans; fixture run stored 7 artifacts; `verify` found 0 mismatches; replay reproduced the golden result. Output remains `INSUFFICIENT_DATA`, with provenance gaps noted above. |
| Dependency / API contract check | `pip check` reports no broken requirements; OpenAPI YAML parses and lists only the explicit workflow POST routes; API metadata reports `read_only: false` truthfully. |
| Targeted self-review | Confirmed exact lifecycle path matching, same-origin restriction for browser POSTs, no arbitrary write methods, no score/configuration mutation route, and no client-side score calculation. No independent review or external acceptance is claimed. |
| Remote implementation/docs publication verification (prior A16 baseline) | **PASS** — at the prior implementation/docs publication point, `git ls-remote` and fetched `origin/arena/573e69a4-ipo-screening-engine` both resolved to `eb912d608ede4e5280618d3f3677ad646b741af5`; A16, README, requirements, and the initial categorized tracker version were read from that fetched commit. This is historical verification, not the remote proof for the current evidence-only pass. The unrelated authorization-request draft remains untracked and unchanged. |

## Delta-only evidence reconciliation (2026-10-14)

### Branch and provenance

- Fixed branch remained `arena/573e69a4-ipo-screening-engine`; immediately before this pass, local `HEAD` and `origin/arena/573e69a4-ipo-screening-engine` both resolved to `25e61364970702f770fc4c4a57fe29cbbaa0d10e`. The prior tip is an ancestor of this work. No branch switch, merge, cherry-pick, reset, or cleanup was performed.
- The evidence source ref `origin/arena/4e1080b7-ipo-screening-engine` was verified at `adbd93c5b4450fb113561368d7d101eb4686c842`. The 245-row package originates at `4f6d42e55e3247f3eaa2b0c634a99684c3b3f662`.
- Exactly 26 artifacts were added byte-for-byte from the 4e ref: 24 evidence paths (23 previously absent paths plus a separately named copy of its corrected transfer manifest) and the two A8-M investigation reports. The two reports retain their original draft/investigation status. The four shared findings/data artifacts were already blob-identical and were left untouched. Both approved A8-M decisions, A9, A10, and A16 remain unchanged; no workstream was merged or cherry-picked.

### Transfer-manifest discrepancy and exact-byte verification

The fixed tree's pre-existing `evidence/market-observations/official-index-history-20261013/transfer-manifest.json` was preserved unchanged. It records the shared alignment-validation JSON as 16,184 bytes with SHA-256 `C7C67B7D…`, while the retained file is 15,659 bytes with SHA-256 `D5776178…`. The 4e copy corrects those values; it is preserved as `transfer-manifest-4e-20261013.json` (source blob `1a6b5436eaa3e7cbf4e83e6393bcc7f3f9d97bba`; file SHA-256 `AD706135…`). The imported `evidence-manifest.json` has 27 entries; all validate by size and SHA-256 when its `transfer-manifest.json` entry is explicitly mapped to that separately named 4e copy. No existing evidence was overwritten. These hashes identify local repository artifacts only and do not authenticate NSE response bytes.

The retained CSV has 245 data rows (2025-10-13 through 2026-10-08); the preserved SMA files have 196 and 46 rows. Their checksums and existing integrity/calendar validations were reused; no SMA was recalculated. Rendered/reconstructed NSE response fragments are not provider response-byte captures. The reported 2026-10-09 and 2026-10-12 Daily Snapshot/history outputs matched at the displayed-text level only; no raw response bytes, exact publication/retrieval times, independent provenance or cutoff-availability evidence were retained, and those dates were not appended or used for SMA calculations.

### Independent workstreams and preserved limits

- **A8-S/A10:** The fixed-tree acquisition register and all 10 VNL evidence files are present and blob-identical to the inspected 01a ref. Seven of eight `SHA256-MANIFEST.json` file entries match; `vnl-issue-information.html` is 313,038 bytes / SHA-256 `6BEB26DC…`, not the manifest's 313,040 bytes / `2AE7009B…`. This discrepancy is recorded, not repaired by overwriting evidence. The package remains non-authoritative, with its VNL discrepancy closed with limitation and NSE/BSE/All Exchange observations distinct. The official `GraphLogic` URL appears in the captured NSE issue-information HTML/API JSON, but no separate PDF or PDF-analysis artifact exists in the inspected fixed, 01a or 4e trees. A10 remains evidence/display only; no scoring, denominator, source qualification or missing-input rule is inferred.
- **A8-G/A9:** The A9 decision remains unchanged. Fixed HEAD has no A9 runtime gate. The partial 4e gate was reviewed but not copied: it specifies generic `VERIFIED`/freshness, timestamp, SHA-256 payload-serialization and retrieval assumptions that A9 itself does not define and the missing source contract does not support. The connector fixture and blocked marker do not establish a qualifying source observation or hash. No provider or hash contract is invented.
- **A8-P/A5:** The retained R.K. Fashion RHP page reports one peer, Banaras Beads, with CMP ₹119.20, P/E 44.31 and P/B 1.36 as of 2026-09-28. It does not retain an exchange-native quote/session, quote timestamp or listing date; no point-in-time peer universe or calibration is available. `CALIBRATION_EVIDENCE_INSUFFICIENT` remains; no 30-day/3-year or proposed v1.6 thresholds are adopted.
- **Other A8 metrics:** Keep VIX separate from NIFTY; the preserved VIX history/alignment is descriptive and does not qualify a trend input. VNL's issue-information record includes listing date 2026-10-08, not a qualifying listing-session price or approved cohort. Existing Moneyview records support only an issue-specific candidate `Total Amount Allocated` of ₹3,275,040,786 at ₹34; anchor quality, source/cutoff and metric-wide contract remain open. Preserve the unexplained 6,020,296-share post-anchor residual and unresolved Anchor/OFS mapping.

No code, config, schema, fixture or test path changed, so application tests were not rerun. Changed-path verification covers exact source-blob matches, the 27-entry NIFTY evidence manifest and row counts, the A8-S inventory/hash comparison (which identified the single mismatch recorded above), and `git diff --check`. The unrelated untracked authorization-request draft remains unchanged. A16 permits routine work; evidence deficiencies—not the superseded blanket procedural gate—are why these metrics remain unimplemented/unqualified. The NDAL request remains UNSENT.

## Remote inventory checked 2026-10-14 (implementation/docs publication point)

| Ref / mechanism | Verified state |
|---|---|
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` |
| `arena/01a10abc-ipo-screening-engine` | `25627497658904caf3e021091c1831a844a70ce2` (PR #1 merged) |
| `arena/01a10b42-ipo-screening-engine` | `4b19faf848a721265597a678926988d484d30e59` (product review base) |
| `arena/4e1080b7-ipo-screening-engine` | `adbd93c5b4450fb113561368d7d101eb4686c842` (governance/evidence ref; original tracker unchanged) |
| `arena/573e69a4-ipo-screening-engine` at implementation/docs publication | `eb912d608ede4e5280618d3f3677ad646b741af5` (A16, personal-use docs/dependencies/API corrections, and validated working baseline; `git ls-remote` matched fetched commit before the tracker-only follow-up) |
| `arena/ipo-handoff-manifest-correction` | `6cb0891faaefbe1c129535fc44cc2ba8e11bc5f4` (PR #2 merged) |
| `arena/ipo-screening-engine-v1.5` | `49c994430148d327e0afff6d67f31072563d64cc` (PR #3, OPEN; no reviews/checks) |
| PRs | #1 and #2 MERGED; #3 OPEN on the old v1.5 head; no PR for the fixed session branch. No review requests, reviews, or status checks were returned for the open PR. |
| Tags / releases / issues / automation | No tags or releases; no GitHub issues; no Actions workflows, runs, or PR check results were found. |

## Historical tracker provenance and preserved evidence

This tracker began as a copy-forward of `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` from `arena/4e1080b7-ipo-screening-engine` (tip `adbd93c5`; source tracker last changed in `40a3f1e8`). Ramki authorized that original candidate copy-forward on the fixed session branch on 2026-10-13. A11 records Phase 0 OPEN, A12 ratifies 01a as a product-code review base, and A13 authorizes the bounded Candidate M assembly; A13's execution addendum records merge commit `9bad659927616ad7fd3aad2864b6637f095872c5`. The source tracker on 4e and Candidate M remain unchanged. The Library tracker was not available in the checkout, and this file is not claimed to be its copy or update. The current personal-use status is the A16-controlled register above.

**Historical A15 status update (2026-10-14; before A16):** The 2026-10-13 A15 semantic approval was followed by Ramki's acceptance-with-specified-amendments of the decision-ready property/schema profile and a separate exact five-path implementation grant, explicitly while Phase 0 remains OPEN. The implementation is at `fecdd8220500d7932c93b55b311a5f9830f92572` / tree `657e6b049156ce14a1b77b495700f34a3a20c068`; the reported focused suite passed 43 tests in the implementation turn, but there are no remote Actions/check results and no independent review or product acceptance. Candidate M `9bad659927616ad7fd3aad2864b6637f095872c5` / tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5` remains unchanged and non-canonical. A14 records Ramki's appointment of Sai and Ramki-reported “no material issues” for M only; Sai's explicit accept/reject, scope confirmation and independence basis remain unrecorded. No extension to review the post-M A15 commit is recorded. The dated A14 Phase 0 assessment still correctly concludes that A11's OPEN disposition remains controlling; its 2026-10-13 A15 serialization findings are superseded by the later A15 profile only.

A repository tracker row does not itself grant implementation, source qualification, scoring, schema, release, or production-activation authority. The cross-workstream audit and dependency-aware implementation sequence are in `handoff/investigation/IPO-SCREENING-ENGINE-RECONCILIATION-AUDIT-DRAFT-2026-10-13.md`; that audit is analysis, not an approval record.

## A8-M — NIFTY trend

| Work item | Status | Current state / next evidence or gate |
|---|---|---|
| NIFTY trend meaning and classification | **APPROVED — policy only** | Session-close-derived NIFTY 50 PRICE INDEX; strict comparison with trailing SMA-50 and SMA-200; mixed/equal valid signals are neutral; incomplete/invalid qualifying windows are UNKNOWN. See `handoff/decisions/A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`. No current category is assigned. |
| Observation, cutoff and provenance policy | **APPROVED — policy only** | Explicit cutoff; latest qualifying completed official NSE close demonstrably available by cutoff; event/session, publication/availability, retrieval and evaluation timestamps remain distinct; complete, valid session windows; no unqualified fallback. See `handoff/decisions/A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`. |
| Required NIFTY UNKNOWN → Final eligibility | **APPROVED — NIFTY only** | If NIFTY trend is required and UNKNOWN, withhold Final, return non-final/incomplete, identify the input/reason, and keep score range/completeness diagnostic only. Does not set Final policy for other metrics. |
| Source-native evidence qualification | **OPEN / BLOCKED — evidence required** | Fixed HEAD now contains 245 descriptive closes from 2025-10-13 through 2026-10-08, 196 SMA-50 endpoints, 46 SMA-200 endpoints, and the retained rendered-response/calendar/integrity artifacts. The source manifest validates exact local artifact bytes, not provider response bytes. Official-output content matches for 2026-10-09 and 2026-10-12 were inspected as rendered text only; neither is a source-byte capture, appended observation or SMA input. Publication/retrieval provenance and availability by cutoff remain unproven. Do not assign a category. |
| Deterministic session calendar/publication-availability rule | **OPEN PREREQUISITE** | The recovered calendar evidence supports historical date alignment only. It does not establish source publication/availability times, a complete future/special-session rule, or availability by cutoff. Keep cutoff, weekends/holidays/special sessions, unresolved timezones and publication delay unresolved; do not invent a numeric delay or skip expected sessions. |
| NIFTY runtime calculation / Final gate | **NOT IMPLEMENTED — evidence blocked, not a procedural denial** | No application SMA classifier or required-NIFTY Final gate was found on the fixed branch. A16 permits routine in-scope implementation, but this metric remains blocked because the source-native observation and deterministic session/availability evidence do not qualify. Keep the required-UNKNOWN → Final-withheld rule; do not infer a category or threshold. |
| A8-M overall | **OPEN** | Policy is approved; source-native qualification and deterministic session/availability prerequisites remain open. No current trend category/score or production-ready metric is established. |
| Phase 0 / Phase 1 | **Phase 0 historically OPEN; blanket Phase 1 gate superseded by A16 for personal use** | A11's historical `OPEN` status is preserved, not formally closed. A16 removes Phase 0/Phase 1 as global blockers for routine personal-use work; affected metrics still require their specific evidence and policy contracts. |
| Implementation / release / production activation | **NO RUNTIME CHANGE — evidence blocked; no release scope** | A16's routine-work authority is not the blocker. No NIFTY runtime change is supported until the specific source and cutoff/availability evidence qualifies. No release or production activation is required or claimed. |

## Historical cross-workstream status (Candidate M review snapshot; A16 controls current personal-use work)

| Workstream | Status | Current verified state / next gate |
|---|---|---|
| **A8-S — subscription** | **PARTIALLY IMPLEMENTED — generic adapter; A10 runtime unverified** | A generic official NSE/BSE subscription adapter exists on the product line. No evidence was found that it implements A10's later interim handling. A10 approves distinct NSE, BSE, and All Exchange observations for evidence/display only, not scoring or equivalence. Source/event/fields/units/denominator/cutoff/freshness and missing/unavailable Final consequence remain open. VNL discrepancy remains CLOSED WITH LIMITATION. |
| **A8-G / A9 — GMP** | **A9 policy CLOSED; gate PARTIAL on 4e only** | A9's narrow rule is approved: an absent/invalid required qualifying GMP snapshot or required hash withholds Final; a blocked marker is not a qualifying snapshot/hash. It does not select a source or define event/cutoff/hash serialization. The gate is absent from PR #3 and 01a; inspected tests do not specifically cover missing/invalid source-hash qualification. Generic payload hashing is not an approved source contract. Do not reopen A9 or extend it to subscription. |
| **A8-P / A5 — peer data** | **BLOCKED — evidence and policy decision required** | Approved direction prefers actual quote/valuation observations for a named session and separates raw observations/universe from eligibility. No provider, session/cutoff, reproducible point-in-time universe, or eligibility contract is approved. A5 remains `CALIBRATION_EVIDENCE_INSUFFICIENT`. Do not adopt legacy 30-day/3-year defaults or claim production peer scoring. |
| **Other A8 metrics — VIX, listing gain, anchor** | **OPEN — metric/source contracts unresolved** | Keep VIX, recent listing gain and anchor observations separate from NIFTY, subscription, GMP and peers. Source/event/session, cutoff, freshness, provenance and missing-input consequences are not established for these metrics; no provider, threshold or implementation is authorized by the A15 work. |
| **Phase 0 / A1, A7, canonical evidence/output contract** | **OPEN — CLOSURE UNSUPPORTED; BOUNDED A15 INCREMENT COMPLETE** | A11 keeps Phase 0 OPEN and its proposed closure checklist is not approved as exhaustive. The exact A15 property/schema profile and its five-path implementation are approved/completed (see A15 row below); this does not close Phase 0. A7's unverified-only serialization is fixed only in that approved output profile as nonterminal with no `final_outcome`. A1 field-level adjudications remain case-specific; other Phase 0 contracts/prerequisites remain open. Sai's A14 review of Candidate M still lacks explicit disposition and substantiated independence, and it does not cover the A15 commit. The 2026-10-13 A14 assessment is date-bound; A11's OPEN disposition remains controlling. No general Phase 1 authority is granted. |
| **A15 — canonical evaluation record** | **IMPLEMENTATION COMPLETE — TESTS REPORTED PASSING; INDEPENDENT REVIEW / PRODUCT ACCEPTANCE PENDING** | Ramki accepted the decision-ready profile with specified amendments and authorized only the five paths in the A15 implementation package, as an explicit overlap while Phase 0 remains OPEN. Commit `fecdd8220500d7932c93b55b311a5f9830f92572`, tree `657e6b049156ce14a1b77b495700f34a3a20c068`, changes exactly those five paths. The prior focused run reported 43 passed (`tests/test_evaluation_record_v1.py` + `tests/test_reproducibility_store.py`); the tree is unchanged, so it was not rerun. No GitHub Actions workflow/run/check exists. This is implementation verification, not independent review, product acceptance, canonical selection or Phase 0 closure. A14's Sai appointment targets Candidate M only; A15 needs a separately extended appointment or reviewer disposition. |
| **Phase 1 / personal-use implementation** | **Routine personal-use work authorized under A16; historical blanket hold superseded** | A16 authorizes routine implementation, testing, documentation, commit/push, and remote verification on the fixed branch. It does not authorize unsupported metric semantics, source qualification, new scoring thresholds, v1.6 activation, or out-of-scope architecture. Phase 0 remains historically OPEN; no formal closure is claimed. |
| **Track B — Phases 6A–6D** | **IMPLEMENTED — ACCEPTANCE PENDING** | Code/tests exist on PR #3 and 01a, not main or 4e. Oct 6 readiness/traceability descriptions are stale where they present these phases as future implementation. Branch-reported tests are not independent acceptance. D1's separate scope disposition was not located. |
| **Track B — D1/D2/D3** | **RECHECK REQUIRED / POLICY OPEN** | No separate D1/D2/D3 disposition record was located. D2's UI/Phase 5 sequencing question is stale after those deliveries; completion does not prove a priority decision. D3's proposed future sample/promotion thresholds are not established as general policy. Do not adopt `N ≥ 15`, IC, downside, or other figures absent an attributable decision and suitable evidence. |
| **Phase 7 / v1.6 candidate** | **IMPLEMENTED — ACCEPTANCE PENDING; INACTIVE** | PR #3 has a specific proposal/approval assertion and inactive candidate for controlled verification. Product docs describe its 120-row sample as synthetic/simulated. This is not independent real-world validation, general D3 policy, or production activation. Keep inactive absent separate activation authority. |
| **Phase 5E–5J** | **IMPLEMENTED — ACCEPTANCE PENDING** | Contract/schema preparation, price-band extraction, enrichment, connectors, CLI and regression work exist on PR #3/01a. File/fixture feeds are implemented; live streaming is deferred. Historical reported tests are not new runs or independent acceptance. |
| **UI-1–UI-7** | **IMPLEMENTED — ACCEPTANCE PENDING on 01a** | Presentation API, dashboards, calibration views, and UI-7 PDF-ingestion workflow exist on 01a, not PR #3/4e. UI-7 is not enterprise authentication/RBAC. Reported test counts are historical. |
| **CFO/PAT, R.K. Fashion, lifecycle, UI-7 hardening** | **IMPLEMENTED — ACCEPTANCE PENDING on 01a** | CFO/PAT repair (`690d472`), R.K. Fashion repair (`aa4d76a`), lifecycle/lineage (`39d9a35`), UI-7 security fix (`9f55eb6`), and upload-handler fix (`4eb700f`) exist with branch-reported targeted tests. No independent acceptance is established. Do not repeat the repairs. |
| **GCP fixture** | **RECHECK REQUIRED — owner sign-off** | v1.5 runtime keeps undisclosed `[●]` UNKNOWN and the statutory ceiling separate. Legacy VNL fixture discrepancy is described as “resolved, needs sign-off”; no separate R. Kapoor/Ramki confirmation that it is superseded was located. No fixture/scoring change or retrospective approval. |
| **EPC / real estate** | **CURRENT SHARED OVERLAY VERIFIED; no split authorized** | Current profile is `epc_real_estate`. No authority to split or change scoring was located. |
| **Sector-relative / bank-NBFC coverage** | **PARTIALLY IMPLEMENTED — evidence/acceptance pending** | Generic code/test coverage exists; reviewed reports do not establish broad point-in-time real-source coverage or independent acceptance. Synthetic fixtures do not establish broad coverage. |
| **Unified product candidate / branch integration** | **BLOCKED — CANONICAL TARGET AND INTEGRATION AUTHORITY NOT ESTABLISHED** | 01a is the product-code review base; PR #3 is the older v1.5 head; 4e carries later governance and a partial A9 gate. Candidate M imports only the explicitly pinned governance records and remains bounded/noncanonical; the post-M A15 branch does not consolidate the remaining A8/A9 work. No single canonical delivery ref, integration authorization, independent review or CI result for a unified current product tree is recorded. Do not cherry-pick, merge or create an integration PR as cleanup. |
| **Bounded candidate assembly / independent acceptance** | **ASSEMBLED — RAMKI-REPORTED NO MATERIAL FINDINGS; FORMAL DISPOSITION PENDING** | Candidate M `9bad659927616ad7fd3aad2864b6637f095872c5` (tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5`) has first parent A11–A13 authorization `7e25d1e2f97d162d97ff837c7dd40fb3d070aea1` and second parent product base 01a `4b19faf848a721265597a678926988d484d30e59`; selected 4e governance files are pinned by A13. Ramki reports Sai found no material issues; no Sai-authored exact-target `ACCEPT`/`REJECT`, scope report or independence evidence is recorded. The 85 scoped tests are baseline evidence, not acceptance. A14 is M-only; later A15 commit `fecdd8220500d7932c93b55b311a5f9830f92572` is outside M and outside that appointment. See A14 assessment. PR #3 remains separate. |
| **Merge / release / production activation** | **NOT AUTHORIZED** | PR #3 remains OPEN. `CLEAN` mergeability is not acceptance. No merge, release, or activation authority was found. Keep Phase 7 inactive. |
| **Deferred roadmap** | **DEFERRED — not current blockers** | Live exchange quote streams, automated corporate-action calendars, SQL/multi-user persistence, infrastructure, and enterprise auth/RBAC are outside the current single-user personal-use scope absent a specific decision. Keep VIX separate from NIFTY trend. |
| **NDAL request** | **UNSENT** | Existing factual request is prepared in the 4e A8-M investigation. No contact, subscription, or purchase is authorized here. Obtain explicit authorization before sending; stop if a charge or subscription is required. |

## Historical dependency-aware next sequence (superseded by A16 for routine personal-use work)

This former process sequence is retained for provenance only; it is not the next-action order for Ramki's personal app. A16 removes its global Phase 0, reviewer, and general implementation prerequisites. Metric-specific evidence and policy dependencies remain as categorized in the current register above. In its original context, this order was by prerequisite, not business priority, and did not rank A9 against NIFTY.

1. **Phase 0 / owner gate:** Phase 0 remains OPEN under A11. The bounded candidate is assembled for review only; it is not canonical and does not close Phase 0. Resolve remaining contracts, then separately decide any implementation authority.
2. **Canonical evidence/output contract:** Ramki approved the A15 profile with specified amendments and separately authorized/received the exact five-path implementation at `fecdd8220500d7932c93b55b311a5f9830f92572` while Phase 0 remained OPEN. The property/schema choices in the accepted package are no longer pending. The implementation still requires exact-target independent review and separate product acceptance; this does not authorize other schema work or general Phase 1, and `P1-CANON-01` remains NOT AUTHORIZED.
3. **Parallel source-specific gates:** only after the canonical contract and separate implementation authority, (a) integrate/test the A9 GMP gate once its source/hash contract is resolved; and (b) implement NIFTY only after source-native closes and cutoff/session-availability evidence, then test the approved UNKNOWN/final behavior. Neither is currently authorized.
4. **Other A8 integrations:** settle each subscription, GMP-source, peer/A5, VIX, listing-gain, and anchor contract with actual source/evidence before proposing code. Do not invent sources or thresholds.
5. **Existing work / coverage:** obtain independent acceptance of Phase 5E–5J, UI-1–UI-7, Track B, Phase 7 and the named repairs on the exact candidate. Add sector/bank code only for a specific approved gap supported by evidence. Obtain GCP fixture sign-off before any fixture change.
6. **Review, acceptance and promotion:** The prepared A14 request remains unsent. Sai's existing appointment is only for Candidate M; the smallest A14 review completion is Sai's written exact-target `ACCEPT`/`REJECT`, scope/checks and independence/conflict declaration. A15 commit `fecdd8220500d7932c93b55b311a5f9830f92572` / tree `657e6b049156ce14a1b77b495700f34a3a20c068` needs a separately authorized review-scope extension or a reviewer appointment; M's review cannot cover it. Ramki's product acceptance and canonical selection remain separate, unrecorded decisions. No PR disposition, merge, release or production activation is authorized.

The audit draft contains the item-by-item missing/completed/authority/dependency/acceptance/next-action table. This sequence grants no work.

## Deferred and recheck boundaries

- **DEFERRED / OUT OF SCOPE:** Do not combine NIFTY trend with VIX, recent IPO listing gains, subscription, GMP or peers. Their source, semantics, freshness and Final consequences remain separate contracts.
- **RECHECK:** Reassess source-qualified NIFTY evidence only after the evidence and session/publication-availability prerequisites are satisfied. A missing or unqualified required input remains UNKNOWN and blocks Final when NIFTY is required.
- **NO RETROSPECTIVE APPROVAL:** Implementation, tests, or completed investigation do not substitute for missing policy or implementation authority.

## A9 Final disposition gate — implementation (2026-10-15)

**Status:** Implemented in the fixed session branch under Ramki's current scoped A9 task. The A9 decision itself remains unchanged; source/provider qualification and hash semantics remain open. No provider was contacted and no source was purchased or subscribed to.

### Repository-supported contract and boundaries

- The v1.5 `market.gmp` input object contains only `as_of`, `pct`, `trend`, and `source_id`; it has no field for approved-provider status, verification, a GMP-specific hash, publication/retrieval distinction, event identity, or blocked-input state. Generic `_sources` registration and field presence do not establish qualification.
- `GmpSignalAdapter` is a secondary-tracker adapter marked `UNVERIFIED`; it computes a local hash over sanitized payload content. The coordinator copies normalized values/as-of/source ID but not the adapter's verification/freshness status into the GMP block. It takes the first `SECONDARY_TRACKER` snapshot and does not preserve GMP-specific competing-observation adjudication.
- A15 classifies `market-snapshot` as a locally computed digest over the generic market snapshot. A legacy `SourceRef.content_hash` is retained with unspecified algorithm/subject/origin; neither can satisfy an A9 GMP qualification requirement. Generic FRESH/STALE/MISSING status is retained only as existing generic snapshot classification, not promoted to source qualification or a source-specific cutoff/freshness rule.
- Consequently, this checkout cannot establish any qualifying GMP observation/hash. A present value is not a valid qualifying case under the current contract; a valid Final pass case is not constructible without an approved source/evidence/hash contract. Conflicting tracker behavior likewise remains unresolved rather than being silently adjudicated.

### Runtime effect

- The gate is at A15 Final disposition/persistence (`build_evaluation_record_v1`, invoked by `EvaluationRecord.artifacts()` and `EvaluationStore.write()`), not in scoring formulas or the UI. In `FINAL`, a missing/no-value GMP observation is persisted as `NONTERMINAL_UNRESOLVED` with reason `MISSING`; a present observation is persisted with reason `SOURCE_UNQUALIFIED`. Both omit `final_outcome`, retain `score_verdict` and add linked A9 diagnostics/evidence. Thus all current Final A15 records remain withheld until a qualifying contract is represented.
- A9 eligibility precedes A7's terminal AVOID/INSUFFICIENT_DATA rules in Final, because A9 requires withholding Final rather than emitting any terminal Final outcome when GMP qualification is absent. A7 precedence remains exercised for non-Final lifecycle modes. The A9 branch does not run for Preliminary or other non-Final modes; formulas, v1.5 score/result hashes, market metrics, configuration, fixtures, and frozen-core files are unchanged.
- The A15 record schema is now 1.1.0 to add the bounded nonterminal reasons and message; the validator continues to accept existing 1.0.0 records. The JSON serialization profile remains 1.0.0 because its encoding/format did not change. No historical artifact or result hash is rewritten.

### Verification (2026-10-15)

- Missing GMP plus a non-empty generic `market-snapshot` digest was reproduced through `evaluate(..., mode="final", store=...)`: before the gate it persisted `TERMINAL` / `VERDICT_UNCERTAIN`; after the change the A15 record is nonterminal with `MISSING`, no `final_outcome`, and a local market-block evidence reference. The generic digest remains `LOCAL_COMPUTED` and is not referenced as GMP qualification evidence.
- A synthetic in-repository adapter/coordinator path supplies a fresh, non-null GMP value and locally computed connector payload hash, but remains nonterminal with `SOURCE_UNQUALIFIED`; A15 preserves the opaque source hash as `LEGACY_UNRESOLVED`. The same input in Preliminary remains terminal under existing behavior.
- `PYTHONPATH=engine .venv/bin/python -m pytest tests/test_evaluation_record_v1.py tests/test_reproducibility_store.py -q` — **49 passed**. The A15 persisted bytes are deterministic across identical runs; `EvaluationStore.verify_hashes()` reports no artifact mismatches and the v1.5 result hash matches.
- `PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q` — **710 passed**, with two non-fatal Starlette deprecation warnings.
- Direct integrity checks: `verify_frozen_core()` **PASS** (all six pinned files), `verify_golden_result()` **PASS** (`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`), and `verify_v1_6_implementation()` **PASS** (zero failures/warnings; v1.6 remains inactive).
- Remote verification (2026-10-15): `git ls-remote` and the fetched `origin/arena/573e69a4-ipo-screening-engine` resolved to A9 code commit `953b621ed27a2bdd1a2e06232f275687810e59d9`; its four code/schema/test/tracker blobs matched. This tracker-only follow-up records that proof. No PR, merge, release, or deployment was created or required.

## A17 GMP cutoff, maximum age and trend labels — implementation (2026-10-15)

**Status:** A17 is recorded as Ramki-approved product policy in `handoff/decisions/A17-gmp-cutoff-freshness-and-trend-labels.md`, and its narrow enforcement is implemented. Source qualification is unchanged:
- MarketLiveIPOGMP: NOT QUALIFIED (leading candidate).
- InvestorGain: NOT QUALIFIED.
- PapsDigital: closed as a non-independent alternative.
- R7: UNRESOLVED.

No provider was contacted, and no GMP page was captured in this pass.

### Runtime effect

- **Cutoff on the scoring path (A17-1).** `pipeline.evaluate` calls `gmp_policy.apply_gmp_cutoff` right after the frozen `build_market_snapshot`. It demotes a FRESH GMP block to STALE when:
  - its `as_of` is later than the evaluation timestamp (the builder's generic one-hour allowance no longer applies to GMP);
  - its `as_of` has no explicit UTC offset (it is never assumed UTC);
  - the evaluation time has no timezone.
- **Scope of the demotion.** It never promotes a block and never changes the anchor, subscription or regime blocks. A STALE GMP block makes `gmp_bucket` and the `gmp_trend` criterion UNKNOWN through the existing frozen logic.
- **Maximum age (A17-2).** The existing configured 24 h, measured from the evaluation timestamp, was already enforced by the builder and is unchanged. Exactly 24 h old is FRESH; one second older is STALE.
- **Connector freshness.** `GmpSignalAdapter` defaults to `GMP_FRESHNESS_POLICY`, which is `MARKET_FRESHNESS_POLICY` with no future tolerance and an explicit offset required:
  - a stamp after the reference time is FUTURE;
  - an offset-less stamp is MISSING;
  - a malformed stamp still raises `ValueError`;
  - other connectors keep their policies.
- **Trend labels (A17-3).** The adapter maps a publisher label only through the existing exact-match table. An unmapped label becomes `None` instead of passing through raw, and conflicting `trend`/`gmp_trend` labels become `None`. Nothing derives trend from values, movement, history or issue price.
- **A9 is unchanged.** In Final, any present GMP stays `NONTERMINAL_UNRESOLVED` with `SOURCE_UNQUALIFIED`, missing GMP stays `MISSING`, and `final_outcome` is never set.
- **Not modified:** frozen-core files, scoring formulas and weights, configuration, the input and A15 record schemas, A9 messages, fixtures, frontend, and the golden result hash.

### Verification (2026-10-15)

- **Before vs after** (scoring path, evaluation at `2026-10-05T12:00:00Z`):
  - GMP `as_of` at +1 s, +30 min and +59 min, IST +1 s, and an offset-less stamp were FRESH and scored before; all are now STALE and UNKNOWN.
  - At the cutoff, the same instant in IST, and exactly 24 h old: FRESH both before and after.
  - Over 24 h old, +90 min, malformed and missing: STALE both before and after.
- **Focused tests:** `PYTHONPATH=engine python -m pytest tests/test_a17_gmp_policy.py -q` — **47 passed**.
- **Mutation check:** reverting each change in a scratch copy fails its tests:
  - removing the pipeline cutoff fails 7;
  - restoring the generic connector policy fails 5;
  - restoring the raw trend pass-through fails 6.
- **Full suite:** `PYTHONPATH=engine python -m pytest tests/ -q` — **757 passed** (710 existing plus 47 new), with two non-fatal Starlette deprecation warnings. No existing test was modified.
- **Direct integrity checks:**
  - `verify_frozen_core()`: **PASS** (6/6 pinned files).
  - `verify_golden_result()`: **PASS** (`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`).
  - `verify_v1_6_implementation()`: **PASS** (zero failures or warnings; v1.6 inactive).
- **Frontend:** `npm --prefix frontend test` was not re-run, because no frontend file or API contract changed. Python API/UI tests are part of the full suite.
- **Remaining limitation:** schema `format: date-time` is not enforced in the pinned environment (the optional `rfc3339-validator` is absent). The A17 runtime check does not depend on it.

## GMP source-policy decisions D1–D3 — implementation (2026-10-15)

**Status:** D1–D3 are Ramki-approved product policy, recorded in `docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md` §6. They were applied to MarketLiveIPOGMP in `docs/investigation/A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md` §16. Built on the remote-verified tip `9dba813b88d9f4ff238a4f94c80dd1e7cbb11dd4`.

Source qualification is unchanged:
- MarketLiveIPOGMP: NOT QUALIFIED. R7 needs source evidence, and R8's history remains open.
- InvestorGain: NOT QUALIFIED.
- PapsDigital: closed as a non-independent alternative.

No provider was contacted, and no GMP page was captured. The R7 capture condition was not met: the pass ran at 23:28 IST on 15 Oct.

### Runtime effect

- **New `engine/ipo_screening/gmp_evidence.py`.** It makes D1–D3 executable over the existing capture-manifest convention:
  - **D1** — `load_rendered_capture` classifies a retained rendered-text capture as `PUBLISHER_REPORTED_RENDERED_CAPTURE` with a fixed publisher-reported label, and verifies the declared file's SHA-256 and byte count. The capture is never source-native, never publisher-authenticated and never dealer-verified.
  - **D2** — `capture_obtained_by` is true only when the end of the capture's retrieval window is at or before the evaluation timestamp. Both instants need explicit offsets, and the publisher's displayed time is never used.
  - **D3** — `classify_displayed_gmp` maps "Not quoted yet" to `MISSING`, a displayed zero to `SOURCE_UNQUALIFIED`, a well-formed non-zero amount to candidate only, and anything else to rejected.
  - `assess_capture` combines the three. Its best result is "eligible for cutoff consideration", which is not qualification.
- **GMP connector.**
  - "Not quoted yet" gives no value.
  - A displayed zero stays a present 0.0, and a rupee-only zero records `pct` 0.0, so A9 reports `SOURCE_UNQUALIFIED`, not `MISSING`.
  - Malformed or contradictory displays raise `ConnectorPayloadError`.
  - A missing retrieval time is no longer filled with the normalisation clock. `ExternalSnapshot.to_source_ref()` omits an unknown retrieval time, so no invented `LOCAL_RETRIEVED_AT` reaches the A15 record.
- **A9 and A17 are unchanged.** Present GMP stays `SOURCE_UNQUALIFIED`, missing GMP stays `MISSING`, and `final_outcome` is never set. A17's cutoff, 24 h age and publisher-label rules are untouched.
- **Not modified:**
  - the input and A15 schemas, configuration, scoring formulas and weights;
  - the frozen core, the pipeline, the A17 module and the A9 gate and messages;
  - fixtures, evidence, frontend and the golden result hash.
- **Limitation (documented, fail-closed).** The v1.5 input and A15 contracts cannot link an evaluation's `market.gmp` to a retained capture, so D1 and D2 cannot be established while an evaluation runs. An A9 qualified path would need a persisted evidence reference plus a matching A15 digest subject. That requires its own decision and a schema change (source-policy record §6.3).

### Verification (2026-10-15)

- **Focused tests:** `PYTHONPATH=engine python -m pytest tests/test_d1_d3_gmp_source_policy.py -q` — **84 passed**.
- **Mutation check:** each of eight reversions in a scratch copy fails the focused tests (failures in brackets):
  - the adapter's D3 parsing (11);
  - the invented capture time (1);
  - always emitting the retrieval time (1);
  - window start used as capture time (3);
  - hash verification skipped (1);
  - a zero mapped to `MISSING` (13);
  - no rupee-only zero (1);
  - malformed coerced to `MISSING` (21).
- **Full suite:** `PYTHONPATH=engine python -m pytest tests/ -q` — **841 passed** (757 existing plus 84 new), with two non-fatal Starlette deprecation warnings. No existing test was modified.
- **Direct integrity checks:**
  - `verify_frozen_core()`: **PASS** (6/6).
  - `verify_golden_result()`: **PASS** (`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`).
  - `verify_v1_6_implementation()`: **PASS** (zero failures or warnings).
  - No schema file changed. The input schema still rejects a display string in `market.gmp.pct` before scoring.
- **Frontend:** not re-run, because no frontend file or API contract changed.

## GMP retained-evidence linkage — PR #4 integration record (2026-10-16)

- **Remote integration verified:** [PR #4](https://github.com/ramkivs/ipo-screening-engine/pull/4) is MERGED into `arena/573e69a4-ipo-screening-engine`. Implementation commit: `c0577d85f268164c6dcccc74fa42125d3f2ba48b`; verified merge commit and authoritative starting SHA: `52536a1d9aae7aa298038b07893668af78e360fc`. This tracker-only publication starts directly from that authoritative commit, not an excluded historical session branch.
- **Eight approved implementation/test paths merged:** `engine/ipo_screening/evaluation_record.py`, `engine/ipo_screening/gmp_evidence.py`, `engine/ipo_screening/json_strict.py`, `engine/ipo_screening/pipeline.py`, `engine/tools/ipo_screen.py`, `tests/test_d1_d3_gmp_source_policy.py`, `tests/test_gmp_evidence_linkage.py`, and `tests/test_strict_evaluation_json.py`. Direct GitHub Contents API blob SHA verification at the merge commit succeeded for all eight paths in this session: each matched both the implementation commit's blob and the fetched authoritative merge tree. This verifies integration bytes, not runtime results or source qualification; the earlier D1–D3 linkage limitation above describes the pre-PR #4 baseline.
- **Windows evidence — user-transferred, not independently inspected in this session:** the first Windows full run had three encoding failures; UTF-8-mode targeted tests and the subsequent full suite reportedly passed, along with compile, frozen-core, golden-result and v1.6 checks. No Windows tests were repeated and no independent confirmation of these results is claimed here.
- **GitHub review/CI evidence:** PR #4 had no reviews, no review decision, no check runs and no status contexts (verified from PR metadata and the implementation commit's check-runs/status APIs). Absent review/CI evidence is not a passing result.
- **Qualification boundaries unchanged:** MarketLiveIPOGMP — **NOT QUALIFIED**; InvestorGain — **NOT QUALIFIED**; PapsDigital — non-independent alternative; R7 — **UNRESOLVED**, no capture taken; R8 history remains open; A9 remains **fail-closed**. This integration record neither qualifies a source nor closes these evidence gaps.
