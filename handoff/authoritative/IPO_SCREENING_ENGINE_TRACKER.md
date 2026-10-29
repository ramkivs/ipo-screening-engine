# Revision21 — PR #10 integrated; Windows gate accepted with qualification

**Controlling closure status (2026-10-26): PR #10 MERGED**, not OPEN.
Exact accepted PR head: `9333b1cd7f55af1c45a73a06655967fc138a35ad`.
Actual GitHub merge: `70c5b0facc20f718500bcddc1efaae778ebd78c5`, merged2026-10-26T05:43:31Z.
Independent remote fetch verifies main contains that head; exact merge parents
are dedb4b8 and9333b1c and the entire merge tree equals9333b1c. Parser repair,
regressions, R.K. reconciliation, investigation and tracker blobs are included;
no unexpected source changes. Prior revision20 Windows-OPEN/PR-OPEN statements
below are historical and superseded by this explicit disposition.

## Windows validation: ACCEPTED BY USER DECISION, qualified full-suite evidence

User verified the exact target9333b1c in a temporary Windows worktree; focused
tests passed with exit0. Initial full suite: **1,941 passed,1 failed**;
`tests/test_extraction.py::test_cli_extract_subcommand` raised
`subprocess.TimeoutExpired`. Isolated rerun of that same test **passed in98.51s**.
User explicitly accepts the Windows gate on this evidence without another full
run. **This is not a clean1,942-pass Windows full suite.** No Windows repeat,
new acceptance condition, scoring workaround or timeout/test weakening is made.
These are user-reported Windows observations, not an Arena-executed Windows run.
Original Windows checkout, five retained restorations and harness correction
are untouched; no Windows checkout access/reset/clean/overwrite/normalization.

## Integration policy / evidence / closure publication

- Fresh pre-merge GitHub state: head9333b1c, base main/dedb4b8 unchanged,
  MERGEABLE/CLEAN, no reviews/requests, full CI SUCCESS. Branch endpoint shows
  protected=false/check enforcement off; active branch rules[]/rulesets[];
  `gh pr checks 10 --required` reports none. Detailed protection GET403 is
  preserved as a visibility limitation, not treated as permission evidence.
- Repository permits merge commits; normal `gh pr merge 10 --merge` with exact
  head-SHA guard succeeded and independent PR/main/parents/tree retrieval proves
  the result. No auto-merge (disabled), admin bypass or fabricated approval.
- Accepted-head Linux CI40232275033/job121286334430: **1,942 tests,0failures/
  errors/skips**, JUnit707.733s; frontend/integrity/compile/clean diff all PASS.
- Post-merge local Linux check on byte-identical merged source:4schemas,
  6frozen pins, golden, inactivev1.6, pip and compile PASS. No Windows rerun.
- No main-push CI trigger exists. Manual full-main dispatch returned403
  Resource not accessible by integration. No protection/check/workflow changes
  are made to conceal that limitation. Documentation-only follow-up PR full CI
  verifies the integrated source under the normal existing PR trigger; exact
  outcome and final main publication are in the durable closure receipt below.
- Closure changes touch only existing documentation/tracker evidence. Accepted
  source/test/config/evidence/dependencies/harness blobs stay identical to9333b1c;
  Windows decision therefore applies unchanged. No competing tracker or IIPS work.
- [Authoritative remote integration/publication receipt](https://github.com/ramkivs/ipo-screening-engine/pull/10#issuecomment-6409140261) records the
  follow-up commit/PR/full-CI result and final main readback. It is updated only
  after those operations are independently observed, not planned-as-completed.

---
## Historical revisions (superseded integration/Windows status follows)

> **Revision20 — wrapped promoter-total repair implemented; Windows acceptance
> OPEN.** User-supplied native diagnostic identifies multi-lineTotal(A) cells
> truncated by the old one-line/five-token helper. General bounded numeric-row
> assembly now preserves columns/category boundaries and refuses ambiguous or
> undisclosed post values. Scoring unchanged; the missing holding caused the
> four-point difference. Related40passed; full/Linux and publication receipts
> are in docs/RK_FASHION_WINDOWS_INVESTIGATION.md and PR#10 revision20 closeout.
> The revision19 blocked status below is historical, superseded by this new
> evidence/repair. Native focused/full reruns are still REQUIRED; no Windows
> acceptance claim. Harness and five retained captures preserved; PR OPEN.

> **Revision19 — R.K. Windows investigation: BLOCKED, NOT REPAIRED.** The user
> reports three failures on reconciled Windows (the earlier seven-failure list
> is historical; no new native full-suite totals were supplied). Source columns independently
> verified: post promoters72.22 + promoter group0.03 =72.25; Arena extracts it.
> Controlled evidence removal proves44→40 is correct missing-value scoring,
> not justification to award4 points. Native source/text/gates/canonical and
> criterion trace remain absent. No parser/scorer/config/evidence patch selected.
> Enhanced read-only diagnostic and real-filing missing-value regression added;
> see `docs/RK_FASHION_WINDOWS_INVESTIGATION.md` for full criterion/provenance trace,
> current validation, preservation audit and exact missing artifact. Windows
> acceptance OPEN; PR#10 stays OPEN/unmerged, irrespective of green Linux CI.

# IPO Screening Engine — Project Tracker (Personal-Use Status)

> **Controlling status (A16, 2026-10-14):** Ramki's single-user personal-use objective controls this register. Routine in-scope investigation, implementation, testing, documentation, commit/push on the fixed session branch, and remote verification do not require renewed approval or an independent-review/canonical-selection ceremony. The detailed Candidate M/Phase history later in this file is retained for audit; any blanket procedural hold in it is superseded by A16. Concrete evidence and product-decision blockers remain active only for the specific metric behavior they affect. This is not a production, release, or enterprise programme.

- **Updated:** 2026-10-25 (Asia/Calcutta) — **Windows portability continuation / revision 18: Windows acceptance OPEN.** Narrow retained-byte checkout guards, direct Pillow declaration and explicit UTF-8 child read are justified; no parser/score/assertion weakening. Three R.K. failures remain unexplained on the Windows interpreter despite Linux independent/cache-disabled passes. Original Windows baseline comparison was targeted, not full. Detailed evidence, checkout reconciliation and the single outstanding Windows diagnostic are appended below and in `docs/TEST_PERFORMANCE_RESULTS.md`.
- **Updated:** 2026-10-25 (Asia/Calcutta) — **Test-suite performance optimization / revision 17:** all 1,908 original tests retained; six isolation/inventory checks added; unfiltered 1,914-test suite independently reproduced at 16m44.233s versus 32m52.110s baseline (49.08% reduction). Fixed branch `arena/cf756dd1-ipo-screening-engine`, authoritative base `dedb4b876cdc68bdf3023d9740dc13f6888b45b3`. See the final test-performance entry and `docs/TEST_PERFORMANCE_RESULTS.md`; local results are not remote CI proof.
- **Updated:** 2026-10-23 (Asia/Calcutta) — **Official-notice OCR segmented-heading CI failure fixed and CI-confirmed green.** The one test that kept every run red (`test_image_only_official_notice_uses_real_offline_ocr_and_preserves_original_pdf_hash`) failed because the runner's OCR merges heading spacing (`INITIAL PUBLICOFFERINGOFACMEFORGELIMITED`, `aggregatingup toRs 240million`, `forSale Size:NotApplicable`): the frozen fallback needs whitespace before `LIMITED`, so `company_name` was `None`. `_norm_name()` was not at fault. Correction is confined to the OCR pre-pass in `official_notice_ocr.py`: one `_restore_heading_spacing()` now normalises the identity header as well as the financial tiles (previously only the tiles), extends the fixed vocabulary with `AGGREGATING UP TO` / `OFFER FOR SALE` / `NOT APPLICABLE`, and separates a fused `LIMITED`/`LTD` suffix without repairing any issuer letter or digit; it is idempotent and also applied to the decoded child payload. No frozen file, weight, criterion, A9 rule or knockout touched; issuer identity checks unchanged and still rejecting different issuers. Six regression cases added (both segmentation forms, parity of extracted terms, wrong-issuer rejection), and the image-only fixture was re-laid out as a narrow single-column advertisement so its lines fit one OCR tile instead of being cut at a crop boundary. 1676 backend tests pass locally and in CI (0 failures), frontend 93/93, frozen core/golden result PASS. Report: `docs/investigation/OFFICIAL-NOTICE-OCR-SEGMENTATION-CI-FIX-2026-10-23.md`.
- **Updated:** 2026-10-23 (Asia/Calcutta) — **Jio publication verified, validation complete, evidence blockers isolated.** Remote lineage re-checked (`589e468` ← `e612702` ← `8a1a3702`, 181 tracked files re-hashed with 0 mismatches, A9 files byte-identical to the parent); branch CI on both commits is **red for one environment-dependent OCR test** (1670 tests, 1 failure each, `test_image_only_official_notice_…`; every other step green and the same test passes locally); exact-commit backend suite **1670 passed** (1206.58 s) and frontend 93/93; upload → evaluation → evidence path accepted at the API boundary (DOM criteria untested — no browser here). No new evaluation: the fresh run is hash-identical to `…final-29d9a601`. Evidence work kept A9/K1/K2/K5 fail-closed and produced four separate findings plus three governance questions (K1 going-concern negative, K2 SEBI/ED scope, K5 unquantified-contingent scope) and the net-worth basis question. Official issue terms are published but unreachable from this sandbox (TLS EOF). See the 2026-10-23 entry at the end; documenting is not resolving.
- **Updated:** 2026-10-21 (Asia/Calcutta) — **automatic official Jio discovery: PARTIAL, end-to-end acceptance BLOCKED**. Actual NSE prices/lot/dates and RHP OFS 0 verified; fresh monetary amount remains unestablished, no evaluation/persistence. See the final “Automatic official discovery / Jio ingestion” entry and linked report; no manual-entry workaround or publication-absence claim.
- **Updated:** 2026-10-20 (Asia/Calcutta) — **decision D-5 applied: the litigation and SEBI/ED negative defaults are gone.** `extract_governance` no longer initialises `litigation_bucket = "clean"` and `sebi_ed_action_active = False` and emits them whatever the scan finds, and `builder._build_governance` no longer rewrites every non-criminal bucket (including an evidenced `minor_civil`) into `clean`; the synthesised quotation "No active SEBI or ED regulatory proceedings" is removed. Both fields are now evidence-or-absent, using the UNKNOWN state the contract already provides — no bucket, weight, threshold, formula, knockout semantic, `config/`, `schema/` or `fixtures/` change, golden hash `e84f8bc0…` intact. The ICDR summary-table and labelled-list disclosure forms are now read, which is how HD Fire's own §12 (**2 criminal proceedings against Directors**) reaches `criminal_or_regulatory` instead of `clean`, while its promoter-scoped nil SEBI column establishes nothing (flag UNKNOWN ⇒ K2 UNVERIFIED, not CLEAR). Measured: R.K. Fashion 49.0 → **45.0** (available 73 → 69, Module D 10 → 6/15), `complete_sample_rhp` 23.0 → **19.0**, `complete_sample_rhp_2` 21.0 → **17.0**; class_a–e, Jio and vishal values unchanged, vishal's heading-derived `sebi=True` false positive removed. Two strict xfails are now passing tests; **44** new cases in `tests/test_litigation_regulatory_defaults.py`. Records: `handoff/decisions/A23-litigation-regulatory-evidence-defaults.md` (investigation + correction; party-coverage for `clean` and a verified regulatory-absence standard remain **open** for Ramki) and `docs/investigation/D-5-LITIGATION-REGULATORY-EVIDENCE-DEFAULTS-2026-10-20.md`. `main` and PR #6 untouched. Prior update retained below (HD Fire primary-source recovery and the 44-field reconciliation).
- **Updated:** 2026-10-20 (Asia/Calcutta) — **HD Fire primary sources recovered** (SEBI-hosted Abridged Prospectus, BRLM-hosted RHP pp. 1–30, BSE anchor-allocation notice) and the 44-field evidence table reconciled to **25 verified / 8 contradicted / 10 unresolved / 1 n/a**; the record's impossible 100 % post-issue promoter holding is proved to be the sum of the two *pre-issue* category totals (95.33 + 4.67). The `…551a7eab` evaluation record remains absent and no new evaluation was produced. See the end of this file. Prior update retained: decisions **D-1 … D-4** approved and recorded as `handoff/decisions/A19`…`A22`; **D-2** (K5 numerator = disclosed total of the contingent-liability section, capital commitments excluded) and **D-3** (disclosed post-issue promoter holding; a pre-issue-only table no longer yields a post value) are implemented and tested; **D-1** (positive-evidence-only going concern) and **D-4** (auditor tenure / repeated EOM evidence-or-UNKNOWN) are verified as retained, with no new rule. Appended at the end of this file: "HD Fire / Jio — D-1 … D-4 approved decisions and authorised remediation — 2026-10-20". HD Fire source-level acceptance remains outstanding; `main` and PR #6 are untouched.
- **Updated (retained):** 2026-10-19 (Asia/Calcutta) — the HD Fire Protect + Jio Platforms score reconciliation, evidence-completeness and extraction audit is appended at the end of this file (see "HD Fire Protect + Jio Platforms score reconciliation… — 2026-10-19"). It records the resolved Jio 21/29 bridge, the resolved HD Fire penalty attribution, the corrected NIL-OFS binding and two dropped penalty inputs, and the favorable-default findings that require a governed golden re-baseline. Earlier entries are retained unchanged.
- **Updated (retained):** 2026-10-18 (Asia/Calcutta) — four-field manual issue-term entry implemented and published (see the last entry in this file: `issue.ofs` is now manually enterable alongside the three pricing terms, initial screening no longer waits for official-source retrieval; Windows-verified discovery fix `5d9597c` intact). Prior update retained: the Windows-discovery repair entries at the end of this file now include the **second** failed Windows acceptance (`ing-32ddf313bbe247b0`, at `0dda109`), its proved root cause and the corrected repair. Earlier header facts are retained below, with superseded lines annotated there: the 2026-10-17 line read "post-7 October reconciliation appended at the end of this file ('Post-7 October work reconciliation — 2026-10-17')" — that entry is retained unchanged.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Working branch (historical, 2026-10-16 sessions):** `arena/573e69a4-ipo-screening-engine` — now the **base** of PR #6; its remote tip is `6f54b3722532c2153e07d9a2cea59696fdd11def` (Windows line-ending hash fix) and it remains the authoritative *published* baseline branch. **Current development branch:** `arena/5dd3fe52-ipo-screening-engine` (successor session branch) at `2087fd37ea1878b4659e6b8428cd47c6fb5581b8`, published via **PR #6 (OPEN, MERGEABLE, not merged)** into `arena/573e69a4-ipo-screening-engine`. **This session (2026-10-18):** `arena/d15866b5-ipo-screening-engine`, fast-forwarded to the verified tip `e05c0efbca1ecb3024e52da73a22e180ea171118` and carrying the four-field manual-terms implementation (Arena fixes a session to its own branch; the PR #6 head branch is not advanced from this session — cross-referenced on PR #6 instead, which stays OPEN/unmerged). Nothing since 7 October is merged; `main` remains `01ba66c12ca1195fd7acbd287c3e39a019808094`.
- **Authoritative HEAD (verified 2026-10-16):** `arena/573e69a4-ipo-screening-engine` at `9e8c260576b85fad66484c19eec04fe328e1575f` (PR #5 merge; contains PR #4 merge `52536a1d9aae7aa298038b07893668af78e360fc`). `main` remains `01ba66c12ca1195fd7acbd287c3e39a019808094` (handoff-only baseline, ancestor of the authoritative branch, not the working tree). No tags or releases exist.
- **Reference baseline selected by A16:** `3b7c71cd05efc608fdca60eb1a988f5cf19d60a0` (A15 follow-on tip)
- **Published implementation/docs baseline:** `9e8c260576b85fad66484c19eec04fe328e1575f` (authoritative HEAD above; supersedes the earlier `953b621ed27a2bdd1a2e06232f275687810e59d9` A9-gate baseline recorded here previously)
- **A9 runtime implementation commit:** `953b621ed27a2bdd1a2e06232f275687810e59d9` (four changed file blobs independently matched the fetched remote ref)
- **A17 GMP policy runtime change (2026-10-15):** built on the remote-verified tip `9e0e4ed562dd49a260482806afc92e7ef98d8a67`. See the A17 section at the end of this file.
- **Fixed-branch tip immediately before A9 work:** `a912d5293b3fa17b32e1a46a5ba118eaac6f7055` (remote-verified A16 baseline).
- **Controlling decision:** `handoff/decisions/A16-personal-use-operating-scope-and-gate-disposition.md`
- **Historical records retained below:** Candidate M `9bad659927616ad7fd3aad2864b6637f095872c5`, A15 implementation `fecdd8220500d7932c93b55b311a5f9830f92572`, A11–A14, and PR #3. They remain unchanged; A16 supersedes blanket process gates for routine personal-use work only.

## Current working baseline

The fixed session branch's 2026-10-14 implementation/docs baseline was `eb912d608ede4e5280618d3f3677ad646b741af5`; A16 Host/Origin hardening was subsequently published at `a912d5293b3fa17b32e1a46a5ba118eaac6f7055`, the tip immediately before this A9 pass. The 2026-10-14 delta-only evidence reconciliation was additive and did not change the application baseline at that time. The 2026-10-15 A9 Final-disposition gate is the current additive runtime change documented below. Candidate M (`9bad659927616ad7fd3aad2864b6637f095872c5`) remains preserved as a historical bounded review candidate, not rebuilt or selected. PR #3 remains an older, separate open PR and is not a prerequisite for using this baseline; its head `49c994430148d327e0afff6d67f31072563d64cc` is an ancestor of the authoritative HEAD, so its content lineage is already included and it must not be merged, closed, or cleaned up without a specific Ramki disposition (A16).

A15's `evaluation-record.v1.json` is an additive persisted artifact. `evaluation.py` differs from its earlier frozen hash only for this A15-reviewed output/persistence path; the v1.6 frozen-core pin now records the reviewed digest. The golden evaluation result remains `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`. v1.5 remains active and v1.6 inactive; no scoring weights or metric thresholds are changed here. This is a personal-use working baseline, not a release or production promotion. A11's historical Phase 0 `OPEN` disposition is not rewritten as closed.

## Current personal-use status register

| Category | Workstream | Verified state / limiting evidence / next action |
|---|---|---|
| **COMPLETED / VERIFIED** | Working baseline and authority | A16 records the current personal-use scope and selects the fixed session branch over Candidate M/PR #3 as the working baseline. Routine progress no longer waits on the historical general Phase 0/Phase 1, reviewer, acceptance, or canonical-selection ceremony. |
| **COMPLETED / VERIFIED** | Deterministic evaluation and A15 persistence | All six frozen-core files verify against the current pin; `verify_golden_result()` passes with hash `e84f8bc0...`; `verify_v1_6_implementation()` reports `PASS` with zero failures/warnings. The v1.6 candidate is still inactive. A generated fixture record verifies as seven payload artifacts and replays to the same hash. |
| **COMPLETED / VERIFIED** | Personal local run path | README, pinned `requirements.txt`, and runbook document isolated Python setup, config validation, deterministic CLI run/verify/replay, and same-origin local UI/API. The API's limited POST scope is explicit; cross-origin workflow writes are rejected. No authentication is provided, so instructions bind to loopback. |
| **COMPLETED / VERIFIED** | Automated regression and self-review | Latest full Python suite at the authoritative HEAD `9e8c260` (Linux, 2026-10-16): **885 passed** with two non-fatal Starlette deprecation warnings; focused GMP linkage group **128 passed**; frozen core 6/6, golden result, and v1.6 checks PASS. Frontend: **55 passed** (re-run 2026-10-16). This supersedes the 841-passed D1–D3 figure recorded here previously and replaces the user-transferred Windows-only evidence for PR #4 with a self-run Linux run at the integrated HEAD. Self-review is recorded as self-review/testing, not independent review. |
| **EVIDENCE-BLOCKED** | NIFTY trend | A8-M's price-index, completed-session, trailing SMA-50/SMA-200, strict supportive/weak, neutral-otherwise, and required-UNKNOWN/Final-withholding semantics remain approved and unchanged. The recovered 245-row close/SMA package is descriptive rendered/local evidence only; source-native bytes and publication/availability by cutoff remain unqualified. Do not assign a category. |
| **EVIDENCE-BLOCKED** | Subscription (A8-S/A10) | The A8-S register and 10-file VNL package already exist on the fixed tree and are blob-identical to the inspected 01a ref. Seven of eight `SHA256-MANIFEST.json` file entries match; its HTML entry expects 313,040 bytes / `2AE7009B…`, while the retained blob is 313,038 bytes / `6BEB26DC…`. Preserve both without rewriting and do not claim full package hash verification. A10 remains evidence/display-only; NSE, BSE and All Exchange stay distinct. The official GraphLogic URL is captured, but the PDF itself and a retained PDF analysis are absent from the inspected refs. Source/event/denominator/cutoff/scoring and missing-input handling remain unresolved. |
| **FAIL-CLOSED / SOURCE CONTRACT OPEN** | GMP (A8-G/A9) | A9's narrow rule is implemented at the A15 Final-disposition boundary: missing/no-value GMP is `MISSING`; any present observation is `SOURCE_UNQUALIFIED` under the current model, so Final has no terminal `final_outcome`. The model has no approved GMP source/qualification or required hash-subject contract; neither a generic local market-snapshot digest nor opaque `SourceRef.content_hash` qualifies. **A17 (Ramki-approved, 2026-10-15) now sets the GMP eligibility rules:** the evaluation timestamp is the cutoff, with no future allowance; the existing 24 h maximum age applies; only publisher-supplied trend labels count. A GMP block that is after the cutoff, over-age, or has a missing, malformed or offset-less timestamp is STALE, so `gmp_trend` is UNKNOWN. No provider, event/as-of, hash or serialization semantics are inferred. MarketLiveIPOGMP and InvestorGain remain NOT QUALIFIED; PapsDigital is closed; R7 is UNRESOLVED. The A17 follow-through gap matrix (`docs/investigation/A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md` §15) finds MarketLiveIPOGMP's R1–R4 met within stated limits. What remains is R7 publisher evidence plus three Ramki decisions: the artifact/hash rule, evaluation-time availability, and missing-vs-zero handling. Even if qualified, the publisher supplies no trend label, so `gmp_trend` stays UNKNOWN. **D1–D3 (Ramki-approved, 2026-10-15)** are recorded in `docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md` §6 and enforced in `engine/ipo_screening/gmp_evidence.py` and the GMP connector:<br>• a rendered capture plus its file hash counts only as a labelled publisher-reported observation;<br>• the capture must have been obtained at or before the evaluation timestamp;<br>• "Not quoted yet" ⇒ `MISSING`, and a displayed ₹0 ⇒ `SOURCE_UNQUALIFIED`.<br>**A18 (Ramki-approved, 2026-10-16) supersedes that linkage limitation:** PR #4 integrated the §7 evaluation-to-capture evidence linkage (existing v1.5 fields; a `VERIFIED` link binds an evaluation only to retained local rendered bytes/text and does not qualify a publisher), and the A18 decision record plus source-policy §7 are now published in this tree. A9 stays fail-closed regardless. MarketLiveIPOGMP remains NOT QUALIFIED because R7 and R8's history remain open. **R7 is time-boxed:** the single condition-triggered re-capture (a reading stamped after 15 Oct 16:02 IST) is possible only before the Tonbo bidding close on **19 Oct 2026**, followed by the §9 post-listing checks. See the A9, A17 and D1–D3 notes below; valid source qualification remains evidence/policy blocked. |
| **EVIDENCE-BLOCKED** | Peers (A8-P/A5) | `CALIBRATION_EVIDENCE_INSUFFICIENT` remains. The R.K. Fashion filing reports one Banaras Beads peer and CMP, P/E and P/B values as of 2026-09-28, but no exchange-native quote/session, listing date, point-in-time universe or calibration is retained. Do not infer peer eligibility or adopt proposed thresholds. |
| **EVIDENCE-BLOCKED** | Other A8 metrics (VIX, listing gains, anchor) | Keep VIX separate from NIFTY. VNL issue evidence supplies a listing date but not a qualifying listing-session price/cohort. Existing Moneyview evidence supports only a candidate issue-specific anchor amount; quality/cutoff/source qualification remain open, and the 6,020,296-share residual plus Anchor/OFS mapping remain unresolved. Do not infer metric values or thresholds. |
| **MATERIAL-DECISION-REQUIRED** | Unresolved metric contracts | Before using affected metrics, settle any still-open source identity, event/denominator, cutoff/freshness, eligibility/universe, hash/serialization, and missing-input/Final behavior for that metric. Existing A8-M/A9/A10 decisions remain controlling where they actually settle a field; do not reopen settled policy or invent thresholds. These decisions block only the dependent metric, not unrelated app work. |
| **EVIDENCE-BLOCKED** | Golden fixture as live research evidence | The deterministic Vishal Nirmiti fixture is a regression sample, not a source-qualified recommendation. Its current output is `INSUFFICIENT_DATA` (score 35.0) and reports 110 material fields without evidence references. The golden hash proves reproducibility, not truth, freshness, or investment suitability. |
| **DEFERRED / OUT OF SCOPE** | Product architecture and operations | Live streaming providers, external purchases/provider contact, authentication/RBAC, multi-user support, PostgreSQL, enterprise architecture, production deployment, tags/releases, and production activation are not personal-use goals and are not required. |
| **DEFERRED / PRESERVE** | Historical governance artifacts | Preserve Candidate M, PR #3, the original tracker on the governance branch, and the authorization-request draft. Do not merge/close PRs or perform destructive cleanup to make the tracker appear complete. |

## Pending-work register (reconciled 2026-10-16)

Reconciled against the authoritative HEAD `9e8c260576b85fad66484c19eec04fe328e1575f`, all remote branches, PRs #1–#5, decisions A1–A18, retained evidence, and a fresh test run (below). IDs below preserve the existing decision/workstream IDs; `PW-` IDs are new register-only IDs for items that previously had none. Verified facts and unresolved items are kept distinct; nothing in this section reopens settled policy (A1/A7/A8-M/A9/A10/A15/A16/A17/D1–D3/A18).

### Genuinely pending

| ID | Item | Actual status | Outstanding work | Dependencies / blockers | Next action |
|---|---|---|---|---|---|
| PW-01 | Verify PR #4 integration at authoritative HEAD | **COMPLETED 2026-10-16** | None. Linux run at `9e8c260`: full suite **885 passed** (2 Starlette deprecation warnings), focused GMP group **128 passed**, frozen core 6/6 PASS, golden result PASS (`e84f8bc0…`), v1.6 PASS (inactive), frontend **55 passed**. Self-run, not independent review. | None | Closed by this record; do not re-run without a new code change or a specific reason. |
| A18-DOC | Publish A18 decision record + source-policy §7 | **COMPLETED 2026-10-16** | None. Was genuinely missing: merged code (`gmp_evidence.py`, `tests/test_gmp_evidence_linkage.py`) references §7/A18, but neither existed in the authoritative tree; they existed only on the unmerged `arena/ea6e5bc2-…` / `arena/gmp-evidence-linkage-docs-clean` branches. Now published with a publication-reconciliation addendum. | None | Closed; the session branches are provenance only — do not merge them. |
| R7-E1 | MarketLiveIPOGMP R7 evidence (GMP qualification) | **OPEN — TIME-BOXED to 19 Oct 2026** | One condition-triggered re-capture of the Tonbo page showing a reading stamped after 15 Oct 16:02 IST and before the bidding close on 19 Oct; verify the "since last reading" delta against ₹500; then the §9 post-listing freeze checks. One pair of readings can never by itself close R7. | Requires an environment/actor authorized to capture the publisher page; no capture was taken in the reconciliation session. Window expires at the 19 Oct close. | Ramki (or an authorized capture environment) performs the single capture in the IST daytime window before 19 Oct; record result against qualification doc §13.1/§9. |
| A8-G-QUAL | GMP publisher qualification (A8-G/A9) | **OPEN — evidence-blocked** | Qualify or close MarketLiveIPOGMP (InvestorGain NOT QUALIFIED; PapsDigital closed as non-independent). Even if qualified, the publisher supplies no trend label, so `gmp_trend` stays UNKNOWN. A9 fail-closed behaviour is correct and must not be weakened. | R7-E1, then R8 pre-capture history (not obtainable from captures alone). | After R7-E1/§9 evidence exists, update the qualification record; otherwise leave NOT QUALIFIED. |
| A8-M | NIFTY trend (source qualification → runtime) | **OPEN — evidence-blocked; semantics APPROVED** | (i) Source-native NSE bytes + publication/availability-by-cutoff evidence; (ii) only then the deterministic session/availability rule and runtime SMA classifier/Final gate. Smallest evidence step per the A8-M feasibility record §7: on a machine whose owner/network policy explicitly permits ordinary HTTPS to the official hosts, run the intake runbook for the 2026-10-09–2026-10-12 API and Daily Snapshot objects and transfer the ZIP + SHA-256 sidecar. | No permitted capture environment identified yet. **NDAL request remains UNSENT** and needs explicit Ramki authorization before sending (stop if a charge/subscription is required). | Ramki identifies the permitted machine / authorizes (or declines) NDAL; do not implement the runtime before qualification. |
| A8-S/A10 | Subscription contract | **OPEN — evidence/decision-blocked** | Settle source identity, event/denominator, cutoff/freshness, scoring and missing-input handling; obtain and analyse the official GraphLogic PDF (URL captured; PDF and retained analysis absent from all inspected refs). | Metric-specific Ramki decisions + PDF acquisition. VNL manifest HTML mismatch (313,038 vs 313,040 bytes) is preserved, closed-with-limitation — do not rewrite evidence. | Acquire/analyse the PDF, then record the contract decisions; A10 remains display-only until then. |
| A8-P/A5 | Peers | **OPEN — evidence/decision-blocked** | Exchange-native quote/session evidence, point-in-time peer universe, calibration. `CALIBRATION_EVIDENCE_INSUFFICIENT` stands; do not adopt proposed thresholds. | Real source evidence + calibration decision. | Only on new retained evidence; no code action now. |
| A8-X | VIX, listing gains, anchor | **OPEN — contracts unresolved** | Separate source/event/session, cutoff, provenance and missing-input contracts per metric (keep VIX separate from NIFTY). Anchor: source/cutoff qualification plus the unexplained 6,020,296-share residual and Anchor/OFS mapping. | Metric-specific evidence and decisions. | Settle one metric's contract at a time; none blocks unrelated work. |
| PW-02 | v1.6 candidate activation (Phase 7) | **IMPLEMENTED — INACTIVE; activation decision outstanding** | Real-world calibration evidence and a separate Ramki activation decision. The 120-row sample is synthetic/simulated; Track B D3 figures (`N ≥ 15`, IC, downside) are **not** adopted policy. | Calibration evidence; explicit activation authority. | Leave inactive. Revisit only with real calibration data and a recorded decision. |
| PW-03 | GCP legacy fixture sign-off | **OPEN — owner sign-off only** | Ramki confirmation that the legacy VNL fixture discrepancy is superseded. No fixture or scoring change is pending or authorized. | Ramki sign-off. | Ask/record sign-off; change nothing meanwhile. |

### Completed or superseded — do not repeat

- **PR #4 / PR #5:** MERGED into the authoritative branch (merges `52536a1`, `9e8c260`). Do not re-implement GMP linkage, re-run its Windows evidence hunt, or re-derive the clean implementation/docs branches; `arena/5ccbfd5d-…` is a **parallel duplicate** linkage implementation (different `gmp_linkage.py` design) — superseded, never merge it. `arena/ea6e5bc2-…` and `arena/gmp-evidence-linkage-docs-clean` are provenance for PR #4/A18 only.
- **PR #3:** OPEN but **superseded** — its head is an ancestor of the authoritative HEAD. Preserve per A16; no merge/close/cleanup without a specific Ramki disposition. It is not pending implementation work.
- **Historical "acceptance pending" rows** (Track B 6A–6D, Phase 5E–5J, UI-1–UI-7, Phase 7, CFO/PAT, R.K. Fashion, lifecycle, UI-7 hardening, Candidate M formal disposition, Phase 0 ceremonial closure, A14/A15 independent review): implementation exists and is verified by the regression suite at the authoritative HEAD; under **A16** independent review/acceptance/canonical-selection ceremonies are **not** prerequisites for personal use. Retained below as history only — not pending work.
- **4e partial A9 gate / `tests/test_snapshot_gate_fixes.py`:** deliberately not copied; superseded by the A9 gate, A17, D1–D3 and A18 linkage on the authoritative branch.
- **Golden-fixture, deferred-architecture and out-of-scope rows** (live streaming, auth/RBAC, multi-user, PostgreSQL, production deployment, tags/releases): unchanged — not blockers, no action.

### Stale entries corrected by this reconciliation

- Header baseline `953b621…` → authoritative HEAD `9e8c260…`; GMP register row's "the evaluation contract cannot link a capture to an evaluation" (superseded by A18/PR #4); regression row 841 → 885 passed; D1–D3 section's "linkage limitation" (now labelled historical in source-policy §6.3, superseded by §7); mid-file historical table's "A9 gate PARTIAL on 4e only" and "unified candidate BLOCKED — canonical target not established" (the authoritative branch above is the A16 working baseline; `main` integration/release remains unauthorized). Historical sections below are otherwise preserved unchanged.

### Execution order (dependency-ordered)

1. **Done in this reconciliation:** PW-01 verification and A18-DOC publication (no dependencies; both were startable immediately).
2. **Start immediately, in parallel, time-boxed:** R7-E1 capture before the **19 Oct 2026** Tonbo close (only item with an expiring window; independent of all code work).
3. **Independent, startable any time:** A8-M permitted-machine evidence capture; A8-S GraphLogic PDF acquisition/analysis; PW-03 sign-off. Each unblocks only its own metric.
4. **Must wait:** A8-G-QUAL (on R7-E1 + §9 checks + R8); NIFTY runtime (on A8-M qualification); subscription/peer/VIX/listing/anchor metric behaviour (on A8-S/A8-P/A8-X contracts); v1.6 activation (on PW-02 calibration evidence + decision); any `main` merge, release, or production activation (not authorized).
5. **Single best next item:** **R7-E1** — it is the only genuinely pending item whose opportunity expires (19 Oct 2026) and it gates A8-G-QUAL. Concrete action: in an authorized environment, capture `marketliveipogmp.com/ipo/tonbo-imaging-india` once it shows a reading stamped after 15 Oct 16:02 IST, verify its delta against the retained ₹500 reading, retain the capture with the existing manifest convention, and record the outcome in the qualification record (§13.1/§9). If the window lapses with no newer reading, record R7 as still UNRESOLVED on that basis — do not manufacture a pass.

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

## Undisclosed issue-terms ingestion error — precision fix (2026-10-16)

- **Symptom (Windows UI):** re-uploading the Vishal Nirmiti RHP failed with `PROCESSING_FAILED: schema validation failed: SCHEMA_VIOLATION: None is not of type 'integer'; … 'number' (×3)` — four opaque messages with no field identity.
- **Root cause (verified):** the RHP leaves price band, minimum bid lot and OFS aggregate as `[●]` placeholders ("will be decided … and will be advertised", i.e. set later by the Price Band Notice), so extraction legitimately finds nothing for `issue.price_band_low`, `issue.price_band_high`, `issue.lot_size` and `issue.ofs`. The fail-closed builder (no fixture fallbacks, per the fail-closed fixture-fallback policy) carries them as null — unknown, never zero — and the v1.5 schema hard gate requires them, so evaluation stopped. `ValidationError`'s message discarded each finding's JSON path, making the four violations indistinguishable and unactionable. Tests missed it because Vishal extraction tests supply the golden input as a template, synthetic fixtures print a price band, and the real-filing UI test uses R.K. Fashion (whose RHP discloses its band).
- **Fix (narrow; no values invented, schema and fail-closed policy unchanged):** (1) `ValidationError` messages now include each finding's location (`SCHEMA_VIOLATION at issue/price_band_low: …`); (2) `PresentationService.ingest_document` detects the four undisclosed required issue fields after extraction and raises a precise, actionable `PROCESSING_FAILED` (HTTP 422) naming them and the remedy (a filing disclosing the terms, or assembly with the Price Band Notice via the enrichment path). Nothing is persisted on this failure, and historical evaluations are untouched.
- **Regression coverage:** `tests/test_ui7_ingestion.py::test_ingest_vishal_rhp_undisclosed_issue_terms_fail_precisely` (422, all four fields named, historical golden evaluation intact); `tests/test_validation_gates.py` path-naming and malformed-number tests; incomplete-stub expectation updated to the precise message. Verification at the fix: focused 158 passed; **full Python suite 891 passed**; frontend 55 passed; `verify_golden_result()` / frozen core 6/6 / v1.6 PASS; live local HTTP acceptance — Vishal RHP returns the precise 422 with an empty store, R.K. Fashion ingests 201, persists, reopens with matching id/hash, and a duplicate re-upload returns 200 `is_duplicate` with the same id/hash. Browser acceptance on the user's Windows machine remains the user's local confirmation step; no score/verdict changed for any evaluable filing.

## Vishal Nirmiti 7 October evaluation — historical reconciliation (2026-10-16)

- **Historical record (user-supplied, not in any repository ref):** 2026-10-07T03:48:18Z, engine/config v1.5.0, final 38, INSUFFICIENT DATA, result hash `0a89c0c3…`. No durable copy of that record, its input snapshot, or its hash exists in any remote branch (all refs searched); it survives only in the user's local evaluation store and must be preserved there untouched.
- **How it was produced (reconstructed and reproduced):** UI-7 upload of the real RHP (551 pages, SHA-256 `644be76e26d43dcaa26ba11303072cf4543bc7a52f30cd37bf1d2d1d552645f6` — the same document in this repository) through `PresentationService.ingest_document` as it existed before `df17d0a` (2026-10-07T09:14Z), i.e. extraction with `allow_fixture_fallbacks=True`. At the then-latest committed code (`2e1c585`, 2026-10-06T21:09Z), that path reproduces **final 38.0 (base 41, penalties −3), INSUFFICIENT_DATA** at the historical timestamp. The golden fixture input replayed at the same timestamp scores 34 (35 at its own golden timestamp), so the scorecard was not a fixture replay.
- **Four disputed fields — proven provenance:** in that run `issue.price_band_low=208`, `price_band_high=220`, `lot_size=68`, `ofs=3300` came from `CanonicalInputBuilder`'s hardcoded fixture defaults; the RHP prints `[●]` for them, extraction produced no candidates, and the assembled input has **no `_evidence` entries** for them. (For this issuer the defaults coincide with the later Price Band Notice values — `fixtures/notices/clean_notice.txt` — but in the 7 Oct record they had no documentary provenance.)
- **Why the historical hash cannot be regenerated:** extraction stamps a wall-clock `retrieval_timestamp` into the source record, which feeds the result hashes. Two identical reconstructions at the same commit/timestamp both score 38.0 but hash differently (`bb8cd295…`, `23c47b13…`). `0a89c0c3…` is therefore a genuine one-run artifact, irreproducible byte-for-byte; the discrepancy is in hash reproducibility of extracted inputs, not in scoring.
- **Did a regression occur?** The behavioural change was deliberate: `df17d0a` (~5.5 h after the historical run) banned fixture fallbacks in ingestion, so the same upload now fails closed (since the previous fix, with a precise field-naming error). No legitimate capability was lost: the Price Band Notice enrichment path is the established route for these terms.
- **New defect found and fixed:** that legitimate path was itself broken — `PriceBandNoticeResult.to_enrichment_dict()` puts an enrichment-document `note` key into the notice's source record, and `EnrichmentEngine` copied it verbatim into the canonical `_sources`, whose schema is closed, so any notice-assembled input failed `evaluate()`. Fixed at the enrichment boundary (the frozen-core notice parser is untouched): only schema-permitted source fields are registered canonically. Notice-assembled Vishal input now validates, evaluates, and carries `SRC-PBN-…` evidence provenance for the band/lot, with `ofs` derived from seller shares × cap price.
- **Coverage:** `tests/test_vishal_historical_reconciliation.py` (builder unknown-vs-default distinction, notice enrichment legitimacy/provenance/distinctness, golden baseline untouched). The historical record is preserved by not rewriting it; its four default-sourced fields are explained here rather than retrospectively legitimised.

## Automatic runtime resolution of missing issue terms (2026-10-16)

- **Capability:** when `PresentationService.ingest_document` finds required issue terms undisclosed (`[●]` pending the Price Band Notice), it now resolves them automatically at evaluation time through the new provider-neutral `ipo_screening/issue_terms.py` (`IssueTermsResolver`) and the established `EnrichmentEngine` assembly — no parallel pipeline, no issuer-specific logic, no fixture defaults. Successful resolution returns the normal 201 scorecard with an `issue_terms` report; the persisted record carries `SRC-PBN-…` evidence for band/lot and `SRC-DERIVED` formula provenance (`sum(seller_shares) × cap_price / 100000`) for the derived OFS amount.
- **Sources and hierarchy:** official primary documents only — HTTP retrieval restricted to allow-listed NSE/BSE/SEBI hosts (actual documents parsed, never search snippets) outranks retained official notice files (`IPO_PRICE_BAND_NOTICE_DIR`, `IPO_PRICE_BAND_NOTICE_URLS`); parsed notices must name the uploaded issuer or are rejected, so values are never borrowed across issuers. Cross-source value disagreement yields `CONFLICT` with no arbitrary selection; invalid values (non-positive, cap below floor) are rejected; snapshots are cached in `IPO_ISSUE_TERMS_CACHE_DIR` with a 168-hour default TTL and stale snapshots are reported, never presented as fresh.
- **Unpublished/unavailable behaviour:** when terms cannot be verified from official sources, ingestion fails closed with HTTP 422 code `AWAITING_ISSUE_TERMS`, naming each unresolved field, persisting nothing, and producing no score. This preserves the preliminary-vs-final product contract: no evaluation (preliminary or final) is created from undisclosed required terms. Duplicate uploads of resolved filings remain idempotent (`is_duplicate`, unchanged evaluation id), and existing historical evaluations — including the 7 October record held only in the user's local store — are never rewritten.
- **Evidence classification (honest boundaries):** resolver unit tests use the retained real-issuer Vishal Price Band Notice fixture plus synthetic conflict/partial mutations; HTTP retrieval tests use an injected fetcher (mocked — they prove provider mechanics, issuer matching, official-host allow-listing and outage handling, not live retrieval). The sandbox has no live NSE/BSE/SEBI access, so no live-retrieval claim is made. Application acceptance is proven end-to-end in tests: `test_ingest_vishal_rhp_auto_resolves_terms_from_official_notice` (real RHP + retained notice → 201, persisted 208/220/68, derived OFS 3300, provenance present, scorecard reopens, duplicate idempotent, golden intact). Jio Platforms is exercised explicitly: no Jio filing or notice exists in any configured source at execution time, so the resolver reports the terms awaiting/unavailable rather than inventing them (`test_jio_platforms_terms_are_not_invented`).
- **Verification:** focused ingestion/resolver suites 28 passed; **full Python suite 904 passed**; frontend 55 passed; frozen-core verification and golden result hash (`e84f8bc0…`) unchanged; no schema, scoring-rule or frozen-core file modified.

## Vishal Nirmiti runtime resolution failure — root cause and fix (2026-10-16)

- **Symptom (Windows application):** uploading the Vishal Nirmiti RHP returned `AWAITING_ISSUE_TERMS` for all four issue terms even though automated end-to-end tests passed.
- **Proven root cause (repository-side; Windows environment not inspected):** the automated end-to-end test injected a `RetainedNoticeProvider` pointing at a temporary notice directory, but the normal application (`uvicorn ipo_screening.presentation.api:app` → `create_app()` → `PresentationService` → `build_resolver_from_env()`) registered **zero providers** unless `IPO_PRICE_BAND_NOTICE_DIR` or `IPO_PRICE_BAND_NOTICE_URLS` happened to be set. Reproduced deterministically: with those variables unset, `build_resolver_from_env().providers == []`, resolution reports `UNAVAILABLE`, and ingestion fails closed with `AWAITING_ISSUE_TERMS`. The retained notice existed in the repository only inside the parser-test fixture corpus (`fixtures/notices/clean_notice.txt`), which the runtime never searched.
- **Fix (narrowest; architecture unchanged):** the retained notice is now also shipped as a packaged application resource (`engine/ipo_screening/resources/notices/vishal_nirmiti_price_band_notice.txt`, byte-identical to the retained repository document, SHA-256 `025b88d2…`); `build_resolver_from_env()` always searches the packaged retained notices via `default_retained_notice_dirs()` (resolved relative to the module file, never the working directory), with `IPO_PRICE_BAND_NOTICE_DIR` retained as additional operator directories. No values, scoring rules, schema, or frozen-core files changed; issuer matching, conflict detection, and fail-closed behaviour are unchanged.
- **Regression coverage:** `tests/test_vishal_default_notice_wiring.py` exercises the normal initialisation path (no injected resolver, no notice env vars): packaged-notice identity, default discovery from an unrelated working directory, unknown-issuer non-resolution, and full Vishal RHP ingestion → 201 → persisted 208/220/68 with derived OFS 3300 and `SRC-PBN-…`/`SRC-DERIVED` provenance → scorecard reopen → duplicate idempotency → historical evaluation unchanged. The pre-existing undisclosed-terms test now injects a provider-less resolver so it still covers the genuinely-unavailable fail-closed path.
- **Verification:** focused suites and **full Python suite 907 passed** (one pre-existing out-of-scope test deselected under the Vishal-only scope restriction); frontend 55 passed; frozen core 6/6 PASS; golden result `e84f8bc0…` PASS; v1.6 verification PASS.
- **Remaining acceptance:** final Windows/browser confirmation by the user via the provided PowerShell acceptance procedure; not claimed here.

## Cross-IPO issue-term canonical value and provenance reconciliation (2026-10-16)

- **Symptom:** Vishal Nirmiti's Evidence & Provenance Explorer showed the ₹208/₹220/68 quotations while classifying provenance UNKNOWN / UNVERIFIED with `Extracted Value = UNKNOWN` and `document: null` (e.g. `EV-issue.price_band_low`, source `SRC-PBN-…`).
- **Root cause (traced end to end):** canonical values were always correct — enrichment writes 208/220/68 (OFS derived 3300) into the canonical input and the persisted input snapshot. The break is downstream: the persisted evidence artifact is a citation registry whose `Evidence` model carries locator/quote/page only, enrichment evidence specs omit value/unit (and the closed v1.5 `evidenceRef` schema forbids adding them there), so `PresentationService.get_evaluation_evidence` passed `extracted_value`/`unit`/`document` through as null, and the frontend inspector derives its provenance label from `extracted_value` presence — hence UNKNOWN / UNVERIFIED despite a verbatim quote. `SRC-PBN-<8 hex>` identifies the notice document by content hash (`price_band_notice.py`: `SRC-PBN-{content_hash[:8]}`); `document` was null because the projection never joined the source manifest. R.K. Fashion differs for a real disclosure reason: its RHP discloses its band (₹77–₹82, lot 1600), so its terms and evidence come from the uploaded filing itself and no resolver/notice is involved.
- **Authenticity finding (blocker, not manufactured away):** `fixtures/notices/clean_notice.txt` was **authored** as one of "13 deterministic notice fixtures" in commit `3cddb64` (Phase 5F parser tests). No official publication location, date, or retrieval provenance exists for it; identical bytes in two repository files prove only copying. It is therefore **not** an authoritative production disclosure. The packaged copy shipped by `4e91b64` has been withdrawn from runtime sources.
- **Rectification (shared, smallest safe):** (1) `IssueTermsResolver` now classifies candidates: only documents retrieved from allow-listed official NSE/BSE/SEBI hosts are `verified` and may resolve terms; retained copies yield status `UNVERIFIED` (reported, never used, never cached), and ingestion fails closed with `AWAITING_ISSUE_TERMS` naming the fields. The verified retrieval provenance (official URL, retrieval timestamp) is stamped into the canonical source manifest at assembly. (2) The evidence projection joins citations to persisted canonical values by field path (never by parsing quotations, so floor/cap cannot be swapped), supplies units (INR per equity share; equity shares; INR <reporting unit>), document identity from the source manifest, and a `verification` classification (`OFFICIAL_VERIFIED`/`FILING`/`DERIVED`/`RETAINED_UNVERIFIED`/`UNVERIFIED`); stored records are not mutated. (3) The Explorer renders `UNVERIFIED RETAINED SOURCE` for retained provenance even when a value exists.
- **Before/after (EV-issue.price_band_low):** before — `extracted_value: null, unit: null, document: null`, UI UNKNOWN / UNVERIFIED. After (verified channel) — `extracted_value: 208, unit: "INR per equity share", document: <official notice document>, verification: OFFICIAL_VERIFIED`. After (retained fixture record) — `extracted_value: 208, document: clean_notice.txt, verification: RETAINED_UNVERIFIED`, and such a record can no longer be produced by ingestion.
- **Cross-IPO status:** Jio Platforms and HD Fire Protect filings are not in the repository (not inspected in Arena; user-supplied findings used as leads only). Their RHPs leave terms as [●], and no verified subsequent notice is available to the resolver, so the shared path correctly retains `AWAITING_ISSUE_TERMS` for them; the evidence-projection fix applies to their future verified evaluations identically. No issuer-specific code was added.
- **Coverage:** `tests/test_cross_ipo_issue_term_provenance.py` (verified mocked-channel → canonical → persisted → evidence API → reopen, duplicates, historical hash intact; retained fixture fail-closed; default runtime has no packaged source; R.K. Fashion filing-sourced terms/evidence). HTTP tests use an injected fetcher — mocked transport proving verified-channel mechanics, not live retrieval. Resolver/UI-7 suites updated to the verified-only semantics.
- **Verification:** full Python suite **908 passed**; frontend **56 passed**; frozen core 6/6 PASS; golden `e84f8bc0…` PASS; v1.6 PASS; historical evaluations untouched.
- **Remaining external requirement:** genuine runtime resolution for Vishal (and, when their filings are supplied, Jio/HD Fire) requires the actual official Price Band Notice — e.g. configuring `IPO_PRICE_BAND_NOTICE_URLS` with the official exchange announcement URL. Windows/browser acceptance remains the user's local confirmation.

## D-PEER-1 — synthetic peer fallback removed (2026-10-16, user-approved decision)

- **Correction:** `CanonicalInputBuilder` no longer inserts the synthetic entity "Generic Listed Peer Ltd" when neither a reference input nor extraction supplies peers; it now emits `peers: []`. The v1.5 input contract was amended accordingly (`schema/ipo-input.v1.5.schema.json`: peers `minItems: 1 → 0`, with a D-PEER-1 description). Individual peer-object validation (name required, closed properties, typed multiples) is unchanged; no scoring configuration, frozen-core file, or historical record was touched.
- **Compatibility:** the schema change is a relaxation — every previously valid input remains valid, and the golden evaluation (genuine peers) is byte-identical (`e84f8bc0…` verified). Forward caveat, stated honestly: an input carrying `peers: []` produced under this amendment would be rejected by a validator still enforcing the old `minItems: 1`; consumers pinning the old schema must be updated knowingly. New no-peer evaluations no longer contain any synthetic company in canonical input, peer snapshot, evidence, or persisted record; peer-relative metrics resolve UNKNOWN exactly as before (score equivalence with the placeholder behaviour is regression-tested). Historical records that contain the placeholder are preserved unmodified.
- **Verification:** new `tests/test_d_peer_1_no_synthetic_peers.py` (11 tests: builder honesty, schema acceptance/rejection, genuine extracted/reference peer retention, UNKNOWN metrics, placeholder-era score equivalence, golden/history/reproducibility, fixture-fallback protections, frozen core). Full Python suite **919 passed**; frontend 56 passed; frozen core 6/6 PASS; golden PASS; v1.6 PASS.

## Step 4 closure — B(i) auditor opinion, Area C authorization — and Step 5 manual issue-term entry (2026-10-17)

- **Decision record:** `docs/investigation/STEP-4-CONTRACT-DECISION-INPUT-2026-10-17.md` (commit `407bf8d`). Areas A (financial-period dates/stub contract semantics) and D (GMP source qualification) remain **deferred**: A requires a schema decision, D remains fail-closed with no qualified source. Neither was implemented.
- **B(i) — auditor-opinion default corrected (user-approved):** extraction previously asserted `auditor_opinion: "unqualified"` without positive evidence (dead initial value in `extraction/sections.py`; effective default `_pick_gov("auditor_opinion", "unqualified")` in `extraction/builder.py`). The opinion is now emitted only when examination-report language establishes it (unqualified/unmodified, emphasis of matter, qualified, adverse, disclaimer — positive-evidence phrases only; "unqualified" is matched before the "qualified" substring), otherwise the canonical field is `null` (schema-supported unknown). Knockout semantics are unchanged: the tri-state K1 resolves UNVERIFIED on unknown opinion, TRIGGERED on a supported qualified/adverse opinion, and the auditor criterion resolves UNKNOWN. **Disclosed scoring consequence:** R.K. Fashion's filing contains no establishable opinion language, so its auditor criterion moves from scored-on-default to UNKNOWN (final 50.0 → 49.0, base 53.0 → 52.0, completeness 75.0 → 73.0); the golden evaluation is byte-identical (`e84f8bc0…`). Historical records are not rewritten.
- **Area C — bounded manual issue-term entry authorized and implemented as Step 5 (user-approved):** new route `POST /api/v1/ingest/manual-terms` (explicitly added to the existing write-scope allowlist; same loopback/same-origin guards; forbidden-parameter rejection unchanged). Only `price_band_low`, `price_band_high`, `lot_size` may be entered; an explanation is mandatory; values are validated (positive, floor ≤ cap, whole-share lots) and recorded as `MANUAL_ENTRY` evidence against a `STRUCTURED_INPUT` operator source (`SRC-MANUAL-ENTRY`), presented as UNVERIFIED — never as official-source verification. Conflicts with filing-extracted or verified values block with HTTP 409 `ISSUE_TERM_CONFLICT` until explicitly confirmed; confirmation never upgrades provenance, and a verified official value is never displaced by a manual entry. OFS remains derivation-only and unchanged: on the real Vishal RHP, manual entry fills floor/cap/lot and the posture correctly stays `AWAITING_ISSUE_TERMS` for `ofs` alone, with nothing persisted. The ingest view renders the pre-processing workflow (missing/blocker list, entry form, conflict-resolution confirmation, remaining-blocker state) and evidence views label manual entries "MANUALLY ENTERED (Not Source-Verified)".
- **Verification:** `tests/test_step5_auditor_and_manual_terms.py` (17 tests: supported/unknown opinions, K1 tri-state behaviour, golden preservation, explanation/validation enforcement, provenance persistence and re-read, conflict block/confirm, partial-entry awaiting, forbidden parameters, real-Vishal integration) and `frontend/test/manual-terms.test.js` (5 tests). Full Python suite **950 passed**; frontend **63 passed**; frozen core PASS; golden `e84f8bc0…` PASS (all inside the full suite).
- **Remaining blockers:** none for B(i)/C/Step 5. Genuine external blockers unchanged: no authentic official Price Band Notice in the repository (manual entry is the authorized interim path, not a substitute for verification); Areas A and D await their own decisions/evidence.

## Official Price Band Notice evidence gap — investigation record (2026-10-17)

- **Record:** `docs/investigation/OFFICIAL-PRICE-BAND-NOTICE-EVIDENCE-GAP-2026-10-17.md`. The genuine Price Band Notice for Vishal Nirmiti is the price band advertisement published ~26 Sep 2026 in Financial Express/Jansatta/Navshakti (as the final Prospectus itself records); **no PDF of it was located on an allow-listed host** (NSE/BSE/SEBI exact-host allowlist). The final Prospectus dated 5 Oct 2026 **is** filed on allow-listed SEBI (`www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf`) and on NSE archives (`nsearchives.nseindia.com/corporate/FP_INE1O5L01025_06OCT2026.pdf`, subdomain not allow-listed), establishing floor ₹208, cap ₹220 and Bid Lot 68 — corroboration, not notice verification.
- **Blockers (precise):** (1) document-class decision required — routing a Prospectus through `IPO_PRICE_BAND_NOTICE_URLS` would stamp `SRC-PBN` notice provenance on a Prospectus, and the parser's token-based classification does not establish document type; options are recorded in the record (approve prospectus-class qualification with honest labelling / obtain the advertisement PDF on an allow-listed host / extend the host allowlist — the last being insufficient alone). (2) This sandbox cannot retrieve exchange/SEBI documents (egress restricted; TLS failures), so live `OFFICIAL_VERIFIED` acceptance cannot be executed here; the operator path on an unrestricted host is documented in the record.
- **Added coverage:** `test_manual_entry_never_displaces_officially_verified_values` — a manual entry conflicting with a verified value blocks as `OFFICIAL_VERIFIED`, and after confirmation the verified values (208/220/68) win with no `MANUAL_ENTRY` provenance. Verified-channel mechanics were already covered by the cross-IPO suite (mocked transport, labelled as such).
- **Status:** `OFFICIAL_VERIFIED` for the real filing remains **not demonstrated live**; Step 5 manual entry remains the authorized interim path and stays `UNVERIFIED`. No behaviour, schema, or scoring changed by this record.

## Official Prospectus pathway implemented; live acceptance remains environmental (2026-10-17)

- **Decision (user-authorized):** a narrowly scoped official Prospectus evidence pathway for price-band floor/cap/lot, implemented without mislabelling a Prospectus as a Price Band Notice and without schema/enum additions or host-allowlist changes.
- **Implementation:** `extraction/prospectus_terms.py` (fail-closed classification: `Prospectus Dated:` marker + CIN + issuer; RHP/notice documents rejected; only explicitly established terms extracted) and `HttpProspectusProvider` (`issue_terms.py`, env `IPO_PROSPECTUS_URLS`, same NSE/BSE/SEBI allowlist — `nsearchives.nseindia.com` still rejected). Provenance is truthful end-to-end: `SRC-PROSPECTUS-<hash>` source identity, `OFFICIAL_PROSPECTUS` enrichment note and `document_class` in the issue-terms report, "Final Prospectus — … definition" evidence locators; presentation classifies `OFFICIAL_VERIFIED`. Verified Prospectus values are protected against manual entries identically to verified notice values (409 conflict, verified wins). OFS derivation and scoring unchanged; historical records untouched.
- **Verification:** `tests/test_official_prospectus_pathway.py` (11 tests: classification both directions, supported/missing terms, host gates, wrong-issuer rejection, partial/fail-closed resolution, full ingest as OFFICIAL_VERIFIED, manual-conflict protection, env wiring — mocked transport, mechanics only). Full Python suite **962 passed**; frontend **63 passed**; golden/frozen intact within the suite.
- **Live acceptance:** NOT executed — sandbox egress to `sebi.gov.in` is blocked (TLS EOF on application-side retrieval). The SEBI document's identity and terms were corroborated via filing excerpts (Prospectus dated 5 Oct 2026, CIN U01122MH1994PLC185445, ₹208/₹220, Bid Lot 68). Windows-side acceptance: set `IPO_PROSPECTUS_URLS={"VISHAL-NIRMITI-LIMITED":"https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"}`, restart the app, upload the Vishal RHP, and confirm `OFFICIAL_VERIFIED` evidence with `SRC-PROSPECTUS-…` sources (full steps in `docs/investigation/OFFICIAL-PRICE-BAND-NOTICE-EVIDENCE-GAP-2026-10-17.md`).

## Prospectus pathway live failure — root cause and rectification (2026-10-17)

- **Record:** `docs/investigation/PROSPECTUS-PATHWAY-LIVE-FAILURE-RECTIFICATION-2026-10-17.md`. **Root cause (code-reproduced):** `ProspectusTermsParser` rejected any document whose opening pages mentioned "red herring"; the genuine final Prospectus references the Red Herring Prospectus in its opening LISTING section, so the SEBI-filed document was REJECTED, the resolver reported UNAVAILABLE, and ingestion returned `AWAITING_ISSUE_TERMS` for all four terms on Windows despite correct `IPO_PROSPECTUS_URLS` configuration. Env loading, IPO identity (`VISHAL-NIRMITI-LIMITED`), provider ordering, extraction patterns and qualification were traced and cleared.
- **Correction:** classification now turns on the dated document title (`Prospectus` vs `Red Herring Prospectus`/`Draft Red Herring Prospectus`); both official providers share a browser-compatible default fetcher (allowlist unchanged); the awaiting UI panel now surfaces per-provider resolution diagnostics. OFS confirmed not independently blocked: with the cap established, assembly derives OFS 3300 from RHP seller shares (regression-tested).
- **Verification:** `tests/test_official_prospectus_pathway.py` 15 tests (realistic-cover acceptance, RHP/DRHP title rejection, fetcher headers, OFS derivation); full Python suite **966 passed**; frontend **64 passed**; golden/frozen intact. Mocked transport = mechanics only.
- **Remaining blocker:** Windows live acceptance is still outstanding and not claimed — Arena cannot retrieve SEBI documents (egress blocked). Exact Windows steps and the diagnostic decision tree (retrieval failure vs document rejection vs env not reaching the process, readable from `resolution.providers` in the 422 body / UI panel) are in the record.

## Generic fresh-issue vs OFS extraction rectification (2026-10-17)

- **Record:** `docs/investigation/GENERIC-ISSUE-TERMS-OFS-EXTRACTION-RECTIFICATION-2026-10-17.md`. Windows live evidence confirmed the Prospectus pathway works (`OFFICIAL_VERIFIED` 208/220/68) and exposed a generic mis-mapping: `EV-issue.fresh_shares` held the OFS quantity 15,00,000 from the clause "…(FRESH OFFER) AND AN OFFER FOR SALE OF UP TO 15,00,000 EQUITY SHARES".
- **Root cause & fix:** the cover extractor's unguarded `fresh (offer|issue) … equity shares` span crossed the OFS clause. Quantities are now bound to their semantic label within a bounded window with intervening-label rejection and contradictory-binding fail-closed; the fresh-amount match is likewise guarded; seller enumeration is anchored on the `("SELLING SHAREHOLDER")` marker (all listed sellers found). Sole seller ⇒ aggregate is their `shares_sold`; multiple sellers with aggregate only ⇒ canonical list stays empty (identities preserved in the evidence quote) so OFS derivation fails closed. Documented limitation: v1.5 seller schema requires numeric `pre_issue_shares`, not independently established by a cover (schema decision would be needed to separate it). Prospectus quotations now snap to sentence boundaries (exact substrings). Dated-title classification and the host allowlist unchanged.
- **Verification:** `tests/test_generic_issue_terms_extraction.py` (7, invented-issuer generic fixtures); focused 40 passed; real-filing suites 32 passed; full Python **973 passed**; frontend 64 passed; golden/frozen intact.
- **Windows acceptance:** outstanding (not claimed from Arena); exact commands and checklist in the record — key check: `EV-issue.fresh_shares` = 65,90,909, OFS seller `shares_sold` 15,00,000 (filing), `issue.ofs` 3300 DERIVED, evaluation produced on a fresh upload after restart.

## Windows AWAITING_ISSUE_TERMS runtime-path rectification (2026-10-17)

- **Record:** `docs/investigation/WINDOWS-AWAITING-ISSUE-TERMS-RUNTIME-PATH-2026-10-17.md`. At `40f0dd2`, executed trace: real RHP extracts `VISHAL-NIRMITI-LIMITED` (matches configured key), env resolver registers and invokes `official-prospectus`, retrieval is attempted (fails only on sandbox egress), and the full ingest evaluates with controlled transport (208/220/68, OFS 3300, fresh 65,90,909). No live SEBI retrieval claimed from Arena.
- **Confirmed defects fixed:** (1) frontend `ingestDocument` dropped FastAPI `detail.missing_fields`/`resolution`, so provider diagnostics never rendered and only the generic message showed; (2) malformed `IPO_PROSPECTUS_URLS` JSON silently swallowed in `build_resolver_from_env` (provider never registered, zero reports) — now a `ConfigurationDiagnosticProvider` reports the variable + parse problem without echoing the value; (3) configured-URL lookup was exact-string only — now exact IPO-ID/company-name plus slug-normalised key variants (same issuer only); (4) REJECTED (retrieved-but-rejected) collapsed into "could not be retrieved" and enrichment assembly failures were silently swallowed — distinct reason + `resolution.assembly_error` (still fail-closed). Retrieval timeout 20s → 60s (bounded).
- **Verification:** `tests/test_issue_terms_runtime_path.py` (12, incl. real-filing end-to-end with unmocked extraction + controlled transport) and a frontend 422-diagnostics test; focused 38 passed; full Python **985 passed**; frontend **65 passed**; golden/frozen intact. No type-checker/build configured in repo.
- **Windows acceptance:** outstanding — after update + server restart + re-upload, read the now-rendered "Official-source resolution diagnostics" line; it identifies the exact remaining step (env-in-process, TLS/proxy retrieval, or document rejection). Minimum remaining action; Arena cannot access the Windows runtime.

## Derived-evidence registration correction (2026-10-17)

- **Record:** `docs/investigation/DERIVED-EVIDENCE-REGISTRATION-CORRECTION-2026-10-17.md`. Two confirmed defects fixed: (1) enrichment wrote derived evidence specs under `SRC-DERIVED` without declaring that source in the canonical `_sources` manifest, so `canonical_input.build_registry` skipped them (`EVIDENCE_SOURCE_UNREGISTERED`) and the Explorer lacked cards for `issue.fresh_shares`, `issue.ofs`, `issue.post_issue_shares`, `issue.post_issue_eps` despite the values being in the snapshot — assembly now registers `SRC-DERIVED` (`source_type: DERIVED`) when such specs exist; registry validation unchanged. (2) Per-seller `shares_sold` evidence (`issue.ofs_sellers[i].shares_sold`, filing-bound) is now emitted by the builder, the Explorer's read-only projection resolves list-index paths and share units, and the frontend inspector no longer labels recorded filing-backed list evidence `UNKNOWN / UNVERIFIED` (absent evidence still does).
- **Verification:** `tests/test_derived_evidence_registration.py` (2, persisted-artifact assertions via `get_evaluation_evidence` on the real RHP + controlled transport: 14500 filing amount; fresh_shares 6590909 DERIVED; seller shares_sold 1500000 FILING; OFS 3300.0 DERIVED; post-issue shares/EPS DERIVED; zero unregistered-source warnings) and `frontend/test/evidence-inspector.test.js` (3). Affected suites 86 passed; full Python **987 passed**; frontend **68 passed**; golden/frozen intact.
- **Windows acceptance:** outstanding — persisted records are immutable, so a fresh upload after update + restart is required to see the restored cards; not claimed from Arena.

## Vishal stale-duplicate reconciliation (2026-10-17, addendum)

- Fresh Windows evidence on `bc508f9` showed 22 citations/no derived cards vs 27 in repository regression. Cause: duplicate identity used only scored `input_snapshot_hash` + `config_hash` (snapshot strips `_evidence`/`_sources`), so a store holding a pre-fix Vishal evaluation returned that immutable record for fresh uploads; the frontend label fix rendered, but artifact-bound cards could not. Scoring impact proven nil: same ingest under `7588b42` vs `bc508f9` gives identical snapshot hash, score 32.0, verdict and knockouts; only the artifact differs.
- **Fix:** duplicate identity now also requires evidence-content identity (ids/sources/methods, timestamps excluded) in `presentation/service.py`; materially different evidence creates a new evaluation, history preserved, identical re-uploads still idempotent. Regression: `test_reupload_after_evidence_fix_creates_new_evaluation_not_stale_duplicate` (seeded pre-fix-style record). Full Python **988 passed**; frontend **68 passed**.
- **Jio (same pass):** correctly blocked — RHP discloses none of the four terms (user UI evidence), no official Jio notice/prospectus is configured/available on an accepted pathway, OFS is not derivable without an established cap, and manual entry (Step-5 contract: OFS never manual) resolves only the three bounded terms per-request and persists nothing on AWAITING; the intermediate `[ofs]` vs final all-four messages are each accurate for their request. No Jio code change warranted; unblock = official Jio Price Band Notice or final Prospectus on an allow-listed host, mapped for its runtime IPO ID when genuinely published.

## Jio Platforms RHP issue-term resolution (2026-10-17)

- **Record:** `docs/investigation/JIO-RHP-ISSUE-TERM-RESOLUTION-2026-10-17.md`. The committed Jio PDF (`evidence/non-authoritative/jio/…`, investigation evidence only, 591 pp.) was inspected and run through the real path. It discloses: fresh-issue only (OFS "Not applicable", cover p.1), 270,000,000 fresh shares, bid/issue dates Oct 21–23, 2026; price band, lot and fresh-issue amount are genuine `[●]`/to-be-decided placeholders.
- **Generic defects fixed (no Jio-specific logic):** (1) cover logo lines polluted the issuer name → runtime IPO ID was `A-MPLS-JIO-PLATFORMS-LIMITED`; the issuer is now the standalone LIMITED line in the cover span → `JIO PLATFORMS LIMITED` / `JIO-PLATFORMS-LIMITED`. (2) NIL-OFS extraction only accepted literal `NIL`; `Not Applicable` now establishes `issue.ofs = 0.0` from the filing for fresh-only issuers. (3) Weekday-prefixed bid/issue dates are recognised. (4) The verified final-Prospectus pathway now carries the stated fresh-issue aggregating amount (parser extracts it with its stated unit, placeholder-safe; assembly converts to the canonical reporting unit with `OFFICIAL_VERIFIED` provenance, never price×shares-derived) — without it, pricing resolution still failed schema on `issue.fresh_issue`.
- **Status:** with no official source, Jio now fails closed on exactly the three pricing terms (OFS no longer spuriously blocks). End-to-end completion via `IPO_PROSPECTUS_URLS` (synthetic controlled transport — mechanics only, no live retrieval claimed) evaluates and persists with correct provenance separation. **Tests:** `tests/test_jio_rhp_issue_terms.py` (7, incl. real-PDF and persisted-evidence assertions); affected suites passed; full Python **995 passed**, frontend **68 passed**; Vishal `5c5c110` preserved.
- **Remaining (external):** configure the genuine official Jio final-Prospectus URL for `JIO-PLATFORMS-LIMITED` when published on SEBI/NSE/BSE, restart, re-upload the RHP. Windows/live acceptance remains the user's run.

## Post-7 October work reconciliation — 2026-10-17

Reconciled against the remote repository (`ramkivs/ipo-screening-engine`), all branch refs, PRs #1–#6, and the commit history `01ba66c..HEAD`. Counting method: individual commits (94 since 2026-10-07 across all refs, the majority pre-16-October governance/GMP history already registered above) were grouped into work items by change purpose; the **23 commits after the 2026-10-16 authoritative baseline `9e8c260`** (plus the user-authored evidence commit `294c77d`) form the 21 work items below. Every item's detailed record already exists in the dated sections above (this register adds the status separation those sections do not carry); items marked *stale-corrected* had an inaccuracy fixed by this reconciliation. Statuses: **A** implemented · **B** automated tests passed · **C** committed on session branch · **D** published to remote branch / existing PR · **E** merged · **F** verified through the actual UI (user-supplied Windows evidence; Arena cannot access the Windows runtime and independently verifies none of it) · **G** accepted · **H** blocked/pending.

| ID | Work item (commit) | Impl. files (principal) | A | B (actual run) | C/D | E | F (UI) | G | Outstanding / blocker |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | Tracker reconciliation + A18 doc publication (`ffb63bd`, `9870593`) | tracker, `handoff/decisions/`, source-policy §7 | ✓ | n/a (docs; suite 885/55 at `9e8c260`) | ✓ PR #6 | ✗ | n/a | — | Closed; PR #3 disposition unchanged (A16) |
| R-02 | Windows line-ending hash verification (`6f54b37`, on base branch) | frozen-core verification | ✓ | recorded 2026-10-16 | ✓ (base tip) | ✗ | user-run | — | None |
| R-03 | Undisclosed issue-terms ingestion precision (`de63c7c`) | `presentation/service.py`, validation | ✓ | full 891 (recorded) | ✓ PR #6 | ✗ | partial (user saw precise 422 in UI) | — | Superseded in behaviour by R-05 resolver (AWAITING replaces opaque failure) |
| R-04 | Enrichment notice-source schema boundary (`a2b84cf`) | `enrichment_engine.py` | ✓ | recorded | ✓ PR #6 | ✗ | — | — | None |
| R-05 | Runtime issue-terms resolver (`72e64c3`) | `issue_terms.py`, `presentation/service.py` | ✓ | recorded | ✓ PR #6 | ✗ | partial | — | Live official retrieval is environment-dependent (see R-13/R-15) |
| R-06 | Packaged retained notice as default source (`4e91b64`) | resources + resolver wiring | ✓ | recorded | ✓ PR #6 | ✗ | — | — | **STALE-CORRECTED: superseded by R-07** — the packaged fixture is *not* a production source in the current tree (`test_default_runtime_has_no_packaged_fixture_source` pins its absence); retained copies are UNVERIFIED and never resolve |
| R-07 | Cross-IPO canonical/provenance reconciliation (`60ce11c`) | builder, enrichment, issue-terms | ✓ | 908 recorded | ✓ PR #6 | ✗ | — | — | None |
| R-08 | D-PEER-1 synthetic peer fallback removed (`73ec730`) | `extraction/builder.py` | ✓ | 919 recorded | ✓ PR #6 | ✗ | — | — | Peer calibration remains evidence-blocked (A8-P, unchanged) |
| R-09 | Workstream 2 evidence-presentation integrity (`636dde4`) | `presentation/service.py`, frontend | ✓ | recorded | ✓ PR #6 | ✗ | — | — | None |
| R-10 | Market-data persisted block states (`485167c`) | presentation/frontend | ✓ | 933 recorded | ✓ PR #6 | ✗ | — | — | Source qualification (A8-M/S/P/X) unchanged, still blocked |
| R-11 | Step 4 contract decision input (`407bf8d`) | docs + config decision artifact | ✓ | n/a | ✓ PR #6 | ✗ | n/a | — | Areas A/D deferred by decision (unchanged) |
| R-12 | Step 4 closure + Step 5 manual issue-term entry (`8dba4bb`) | `presentation/service.py`, `api.py`, frontend | ✓ | Python 950 / frontend 63 recorded | ✓ PR #6 | ✗ | user-exercised (Jio/Vishal manual panels; OFS correctly still blocks) | — | Manual entry can never supply OFS (contract); see R-20 |
| R-13 | Official-notice evidence gap record (`c77e838`) | `docs/investigation/OFFICIAL-PRICE-BAND-NOTICE-EVIDENCE-GAP-2026-10-17.md` | ✓ | n/a | ✓ PR #6 | ✗ | n/a | — | Established no packaged notice is authoritative (basis for R-06 correction) |
| R-14 | Official Prospectus pathway (`12e5f04`) | `extraction/prospectus_terms.py`, `issue_terms.py` | ✓ | 962 recorded | ✓ PR #6 | ✗ | ✓ user evidence: 208/220/68 `OFFICIAL_VERIFIED` in Windows UI | — | Live retrieval itself is Windows-side (Arena egress cannot reach SEBI) |
| R-15 | Prospectus live-failure rectification (`11fb0cb`) — dated-title classification, browser-compatible fetcher, UI provider diagnostics | `prospectus_terms.py`, `issue_terms.py`, frontend | ✓ | 966 / 64 recorded | ✓ PR #6 | ✗ | ✓ user evidence following the fix | — | Closed |
| R-16 | Generic fresh-issue vs OFS separation (`40f0dd2`) | `extraction/sections.py`, `prospectus_terms.py` | ✓ | 973 / 64 recorded | ✓ PR #6 | ✗ | partial (values shown in Windows evidence review) | — | `pre_issue_shares` schema limitation documented (needs a schema decision to separate) |
| R-17 | Windows runtime-path diagnosability (`7588b42`) | `issue_terms.py`, `presentation/service.py`, `frontend/api.js` | ✓ | 985 / 65 recorded | ✓ PR #6 | ✗ | ✓ user evidence: seller card + prospectus terms rendered | — | Closed |
| R-18 | Derived-evidence registration + seller quantity + inspector label (`bc508f9`) | `enrichment_engine.py`, `extraction/builder.py`, `presentation/service.py`, `frontend/app.js` | ✓ | 987 / 68 recorded | ✓ PR #6 | ✗ | ✗ not yet — stale duplicate masked it (R-19) | — | Windows re-upload after R-19 required |
| R-19 | Stale-duplicate evidence identity (`5c5c110`) | `presentation/service.py` | ✓ | 988 / 68 recorded | ✓ PR #6 | ✗ | ✗ **pending user Windows run** | — | **Next UI acceptance item:** update + restart + one fresh Vishal upload → NEW evaluation exposing the five derived/seller cards (old record preserved) |
| R-20 | Jio RHP artifact (user-authored `294c77d`) + Jio resolution (`2087fd3`) | `evidence/non-authoritative/jio/…` (artifact); `extraction/sections.py`, `extraction/prospectus_terms.py`, `enrichment_engine.py` | ✓ | 995 / 68 at `2087fd3` | ✓ PR #6 | ✗ | ✗ blocked externally | — | **H — external dependency:** genuine official Jio final Prospectus on SEBI/NSE/BSE, then `IPO_PROSPECTUS_URLS[JIO-PLATFORMS-LIMITED]` + restart + upload. Until then correctly `AWAITING` on the 3 pricing terms (OFS filing-established 0.0). The SEBI-hosted RHP the user supplied on 2026-10-17 is the same RHP (placeholders) — it must not be configured as a Prospectus |
| R-21 | This reconciliation + UI acceptance checklist (this commit) | tracker, `handoff/UI-ACCEPTANCE-CHECKLIST-2026-10-17.md` | ✓ | reference-verified (paths/SHAs/PR state checked programmatically); suite baseline R-20 unchanged (docs-only) | ✓ PR #6 | ✗ | n/a | — | — |

**Stale/inaccurate entries corrected by this reconciliation:** (i) tracker header working-branch/HEAD/test-count lines (2026-10-16, `9e8c260`, 885/55) — superseded by the header annotation above and this register (current: session branch `arena/5dd3fe52…` at `2087fd3`, Python **995**, frontend **68**, PR #6 OPEN/MERGEABLE/unmerged, `main` untouched, no CI configured — 0 check-runs is not a pass); (ii) R-06's packaged-notice default, superseded by R-07/R-13 (do not treat the packaged fixture as a production source); (iii) R-03's precise-422 endpoint behaviour, superseded by R-05's resolver + `AWAITING_ISSUE_TERMS`; (iv) the addendum under R-18/R-19 previously implied Jio needed "an official document when published" generically — R-20 now records the concrete, document-inspected position (filing establishes OFS/dates/shares; only pricing + stated amount await the final Prospectus). No historical section was erased; supersessions are recorded here and in the items' own sections. **Genuinely outstanding:** R-19 Windows acceptance (user-side), R-20 external Jio Prospectus, plus the unchanged evidence-blocked registers (R7-E1 — its 19 Oct 2026 window is imminent, A8-G-QUAL, A8-M, A8-S/A10, A8-P/A5, A8-X, PW-02, PW-03) and PR #6's eventual merge disposition (Ramki; not authorized here). Nothing is marked G (accepted) — acceptance requires the user's UI confirmation per item.

### RPT extraction correction — 2026-10-17 (post-reconciliation)

- **Proven defect (Gemini-review audit):** RPT notes were never extracted; for Vishal, Note 47's full three-year tables existed in the RHP while Module D `rpt` stayed UNKNOWN and K6 UNVERIFIED with no RPT evidence anywhere.
- **Correction:** generic issuer-neutral `SectionExtractor.extract_related_party_transactions` (sections.py), wired into `DocumentExtractor.extract_from_pdf`; registered as canonical evidence under `governance.related_party_transactions[i]` (verbatim row quotes, category/counterparty/period/amount/unit/page). Sales/purchases separated; `-` undisclosed, never zero; balances/totals excluded; dedupe; fail-closed on ambiguous rows. Vishal: 136 transactions; sale of goods FY26/25/24 = ₹2,260.49/3,091.60/3,270.77 lakh; purchases FY26 ₹2,427.54 lakh (hand-verified, Note 47, PDF p. 387).
- **Scoring boundary (deliberate):** the runtime canonical schema is closed, so no structured canonical field was added and snapshots are unchanged; `rpt_pct_revenue`/`rpt_pct_of_revenue_growth` remain null because the approved definitions do not specify numerator categories, growth window, or negative-growth treatment. Module D `rpt`/K6 remain UNKNOWN/UNVERIFIED pending Ramki's metric-definition decision — record: `docs/investigation/RPT-EXTRACTION-AND-METRIC-DEFINITIONS-2026-10-17.md`. K5 untouched.
- **Tests:** `tests/test_rpt_extraction.py` 6 passed (two synthetic issuers/layouts/units, fail-closed, real Note 47, canonical/evidence mapping, golden invariance 35.0/K6 UNVERIFIED). Full Python suite **1001 passed**. No frontend change; frontend suite not rerun (68 passed at `2087fd3` baseline).
- **Status:** A/B/C/D via PR #6 on commit (see register note below); E/F/G not claimed. No historical evaluation, scoring policy, threshold, schema, or fixture changed.

### RPT scoring metrics — approved definitions implemented — 2026-10-17

- **Approved definitions (Ramki):** Module D `rpt_pct_revenue` = RPT sales/services income ÷ revenue from operations, latest audited FY (eligible: sale of goods/services excl. PPE sales, job-work charges received; purchases/loans/interest/remuneration excluded, retained as evidence). K6 `rpt_pct_of_revenue_growth` = change in that share between the latest two comparable audited FYs, percentage points, consumed by the existing >40 trigger and existing Module D bands — thresholds/weights untouched.
- **Implementation:** `CanonicalInputBuilder._derive_rpt_metrics` fills the two existing schema fields from RPT extractions + financial periods (unit-converted, fail-closed on missing revenue/units/periods; curated/base values win; only when extractions present). Derived-metric formula strings deliberately unchanged (they feed the golden result hash). Policy record: `docs/investigation/RPT-EXTRACTION-AND-METRIC-DEFINITIONS-2026-10-17.md`.
- **Vishal:** FY2026 share 11.8418%, FY2025 12.2126%, change −0.3708pp → K6 CLEAR, Module D `rpt` SCORED 1/3 in new runtime evaluations (approved-integration difference; historical records/golden fixture untouched, golden hash `e84f8bc0…` preserved).
- **Tests:** focused RPT file 11 passed (derivation, unit conversion, zero-prior, fail-closed, consumers incl. rising-share K6 TRIGGERED); full Python suite **1006 passed**. No frontend change (not rerun; 68 at baseline).
- **Status:** A/B/C/D via PR #6 (commit below); E/F/G not claimed. K5 policy untouched.

### Live-path AWAITING_ISSUE_TERMS recurrence — Windows root cause fixed — 2026-10-17

- **Root cause (demonstrated):** temp-file `unlink` in a `finally` block after pypdf parsing — Windows refuses to unlink a file the reader still holds open (WinError 32), destroying successful parses and misreporting them as document rejections; invisible on POSIX. All three sites fixed with best-effort cleanup. Secondary: single-attempt fetcher now retries transient failures (3 attempts, 429/5xx/reset/timeout), HTML interstitials classified distinctly.
- **Source fact:** the configured SEBI URL is Vishal's genuine final Prospectus (05 Oct 2026; fresh ₹14,500L, OFS ₹3,300L) — terms ARE published; sandbox application retrieval to SEBI remains egress-blocked (TLS EOF, environmental). Record: `docs/investigation/WINDOWS-LIVE-RETRIEVAL-WINERROR32-2026-10-17.md`.
- **Tests:** `tests/test_issue_terms_windows_retrieval.py` 7 passed (Windows-unlink simulation x3, HTML classification, loopback 503-retry over a real socket, 404 no-retry, genuine-PDF-bytes control); focused neighbour suites 37 passed combined. Full suite: 1013 passed.
- **Status:** A/B/C/D via PR #6 (commit below); live Windows completion (F) still requires one fresh upload on the updated checkout — the 422 provider detail will identify any remaining stage precisely. Not a claim of live acceptance.

### Generic automatic issue-term discovery — 2026-10-18

- **Jio root cause:** terms genuinely unpublished as of 2026-10-18 (NSE upcoming/active list checked directly — Jio absent; RHP `[●]`, window Oct 21–23 2026). Generic gap corrected: retrieval previously required manually configured per-issuer URLs.
- **Capability:** `OfficialDiscoveryProvider` (default-on in `build_resolver_from_env`, `IPO_OFFICIAL_DISCOVERY=0` disables) searches official NSE/BSE/SEBI listing pages and runs linked documents through the existing allowlist/issuer-match/classification pipeline; NOT_FOUND→UNPUBLISHED, unreachable→UNAVAILABLE, configured sources keep precedence, retained copies still UNVERIFIED, cache/retries/Windows fixes unchanged. **Superseded 2026-10-18 (Windows acceptance ing-5aa6dd92cd7640a8):** NOT_FOUND→UNPUBLISHED now requires a *substantiated* listing search (`listing_searched`); a listing is recognised by its issue entries, never by a marker substring — see the entry at the end of this tracker. Record: `docs/investigation/GENERIC-ISSUE-TERM-DISCOVERY-2026-10-18.md`.
- **Tests:** `tests/test_official_discovery.py` 6 passed (notice + prospectus discovery, issuer rejection, unpublished vs unavailable, HTML rejection, Jio service-level fail-closed with automatic discovery attempt); focused neighbour suites 69 passed combined; full Python suite 1019 passed. One configuration-shape test updated (default resolver = discovery provider only, no packaged fixture).
- **Status:** A/B/C/D via PR #6 (commit below); Jio completes automatically once its price-band/prospectus is officially published — no code/config change then required. Sandbox live retrieval remains egress-blocked (environmental, reported UNAVAILABLE, not unpublished).

### Jio retrieval failure — discovery coverage correction — 2026-10-18

- **New evidence:** Jio terms are now officially published — BSE public-issues page lists Jio (21–23 Oct 2026, ₹1065.00–1119.00) and the official BSE `DisplayIPO?id=4894` page publishes Price Band 1065.00–1119.00, Market Lot 12 (fetched/read directly; broker screenshot agrees). The prior "unpublished" finding was time-bound and is superseded.
- **Root cause of Windows failure:** discovery scanned listing pages but discarded non-document (issue-information page) links; exchange listing apps expose terms on those pages, not document hrefs. Downstream stages never ran. OFS note: sandbox extraction of the committed Jio RHP yields `ofs 0.0` at HEAD; the NIL pattern window was widened generically (16→32 lines) for other cover layouts.
- **Correction:** discovery follows issuer-matched exchange issue-information pages via new `ExchangeIssuePageParser` (`EXCHANGE_ISSUE_PAGE`, `EXCHANGE_DATA`, verified provenance; Market Lot only); complementary verified candidates field-merge with hard conflict rejection; prospectus remains richest primary; fresh-amount pattern accepts "aggregating to ₹…"; UNPUBLISHED message no longer asserts non-publication from NOT_FOUND; service names `issue.fresh_issue` precisely when only the Prospectus-stated amount remains.
- **Acceptance (automated):** Jio RHP through the normal entry point — exchange-page discovery resolves pricing (awaiting only `issue.fresh_issue`); with a final Prospectus also discovered, evaluation completes/persists (1065/1119/12, ofs 0.0 filing). Deterministic fixtures modelled on the recorded official BSE pages; live Windows confirmation remains user-side.
- **Tests:** focused suites 90 passed (discovery 10 incl. 3 Jio service-level, prospectus pathway, runtime, Windows retrieval, cross-IPO, API, derived evidence, RPT); full Python suite 1023 passed.

### Jio Windows recurrence — listing-stage root cause — 2026-10-18

- **Report:** at `cbac38c` the Jio RHP still returned `AWAITING_ISSUE_TERMS` with all four fields on Windows (homepages 200, API healthy). Homepage/health checks do not exercise listing retrieval, link following, or issue-page parsing.
- **First failing stage (A/B):** discovery scanned `publicissue.html`, a JavaScript application shell whose raw HTML contains no issue rows or `DisplayIPO` links, so issuer matching, link following, and the issue-page parser never ran. The server-rendered BSE listing `IPOIssues?id=1&Type=P` carries the table and links in served HTML (directly fetched/verified). Served hrefs are `&amp;`-encoded and must be unescaped before following, preserving query parameters.
- **Correction:** classic BSE listing added to `LISTING_URLS` ahead of the JS shell; `_candidate_links` HTML-unescapes listing HTML. Downstream verification unchanged (allowlist, issuer match, Market Lot only, `EXCHANGE_ISSUE_PAGE`/`EXCHANGE_DATA` provenance, conflict rejection). OFS zero-vs-missing distinction re-confirmed; the Windows `issue.ofs` item indicates FRESH-only/NIL establishment did not fire on the uploaded copy — Arena cannot inspect the Windows file/process; no issuer-specific branch added.
- **Tests:** 2 new discovery regression tests (classic `&amp;` listing → exact followed URL + band/lot; JS shell → NOT_FOUND); 2 pre-existing tests made URL-position-independent; focused suites 92 passed; full suite to be recorded at commit.
- **Status:** A/B/C/D via PR #6 (commit below); live Windows completion (F) still requires a restart + one fresh upload on the updated checkout. Sandbox egress remains TLS-blocked (environmental UNAVAILABLE, not evidence about Windows).

### Jio Windows recurrence (2) — HTTP 200 homepage / session root cause — 2026-10-18

- **Windows evidence:** PowerShell GET of the classic BSE listing URL returned HTTP 200 homepage HTML (14,287 chars, BSE masthead title, no Jio/DisplayIPO markers). BSE serves its homepage to cookie-less one-shot requests; a session that establishes cookies first receives the real pages (investigator tooling fetched the genuine listing + DisplayIPO page the same day). The app's fetcher was equally cookie-less, and HTTP 200 was accepted as a searched listing.
- **Correction:** session-aware default fetcher (shared cookie jar + one-time homepage warm-up per official host for page fetches; PDF retrieval unchanged); response-identity classification (`ok|empty|homepage|shell`; masthead alone never condemns a real BSE page — genuine issue content exempts it); stage-specific failure reasons in provider reports; NOT_FOUND only when a valid listing was actually searched, else UNAVAILABLE (never a false unpublished signal). Conflict rejection, allowlist, Market-Lot-only and provenance rules unchanged. OFS untouched.
- **Tests:** homepage-response, homepage-does-not-poison, issue-page-homepage, shell-as-UNAVAILABLE, cookie-persistence (loopback) tests added; discovery + Windows-retrieval files 23 passed; neighbour suites 93 passed; full suite to be recorded at commit. Sandbox live discovery reports UNAVAILABLE (TLS egress block, environmental) with per-URL reasons.
- **Status:** A/B/C/D via PR #6 (commit below); Windows live acceptance (F) still requires restart + one fresh upload. If BSE additionally fingerprints the Python TLS stack, the run will now report UNAVAILABLE naming the homepage wrong-page response — the precise next diagnosis, not a silent failure.

### Ingestion observability — structured events, live UI timeline, recoverable diagnostics — 2026-10-18

- **Gap found:** the synchronous ingestion path emitted no lifecycle events, no correlation id, and no durable record of failed/blocked attempts; diagnostics lived only inside exception payloads, and the UI inferred stage progress from request return rather than backend execution.
- **Implementation:** event contract v1 + recorder/store (`presentation/ingestion_activity.py`, sibling `ingestion-activity/` JSON store, atomic writes, 200-record retention, credential redaction/bounding); instrumentation at real boundaries in `_ingest_document_impl` (upload, validation, extraction, issuer, per-term filing/discovery states incl. homepage wrong-page reasons, eligibility, evaluation, persistence, finalization); terminal outcome recorded before exceptions propagate and correlated into API errors (`ingestion_id`/`activity_url`); `POST /ingestions/start` (202 + background thread, same write-scope guards) with `GET /ingestions/{id}` + `/events?after_sequence=` polling; Ingestion Activity panel in the UI (ordered events, expandable sanitized details, terminal summary, refresh recovery via localStorage id, HTML-escaped). Sync ingest semantics unchanged; per-term states distinguish missing vs unavailable vs conflicting. Record: `docs/investigation/INGESTION-OBSERVABILITY-2026-10-18.md`.
- **Tests:** backend `tests/test_ingestion_activity.py` 7 passed (incl. Jio homepage scenario → durable BLOCKED trace, no evaluation artifact; async start → terminal via polling); frontend 72 passed (4 new activity tests incl. XSS escaping); one signature-pin test extended for the internal `recorder` parameter with justification. Full suite to be recorded at commit.
- **Status:** A/B/C/D via PR #6 (commit below); Jio discovery itself unchanged and still Windows-acceptance-pending (F) — the next attempt's panel now shows the actual stage/response/terms/decision.

### Ingestion Activity panel visibility fix — 2026-10-18

- **Report/trace:** user could not locate the panel at `22f82b8`. Route/mounting/submission flow verified sound (`#ingest` → `renderIngestView` → `#ingest-activity-panel` in the Workflow Progress card; submit uses `POST /ingestions/start` + polling; served `/ui/app.js` confirmed). Defect: the panel was an empty unlabelled div until the first poll rendered into it — invisible as a UI element.
- **Fix:** permanent visible panel shell (title, IDLE state, guidance, last-trace restoration after refresh). Frontend integration test added: shell locatable pre-submission; submission populates panel with real backend events incl. a blocked ingestion (homepage wrong-page event, terminal summary, unresolved terms, evaluation/persisted facts); legacy sync path absent from the API double, so fallback would fail the test. Frontend 74 passed; backend focused suites 48 passed (backend code unchanged this round).
- **User location:** UI → "Ingest" (Upload IPO Filing) screen → right-hand "Workflow Progress & Audit Status" card → **Ingestion Activity** panel below the 5-stage tracker. Restart at this commit and hard-refresh (Ctrl+F5) once so the updated `app.js` is served.

### Discovery outcome classification repair (Windows trace ing-eacd8815051f4222) — 2026-10-18

- **Defect (code-traced):** discovery counted any non-homepage/non-shell response — including marker-less pages — as a searched listing; one such response (NSE on Windows, while both BSE listings returned JS shells and SEBI errored) flipped NOT_FOUND → resolver UNPUBLISHED, contradicting the attached diagnostics.
- **Correction:** a listing counts as searched only when it classifies `ok` (genuine listing content). Homepage/shell/marker-less/failed listings are unusable with per-URL reasons retained; NOT_FOUND requires a valid listing actually searched; otherwise UNAVAILABLE. UNPUBLISHED only from genuine NOT_FOUND. CONFLICT unchanged. Activity trace now reports the discovery outcome as UNAVAILABLE for this scenario; ingestion stays BLOCKED, evaluation/persistence not run.
- **BSE retrieval:** still unavailable on Windows — the trace ran with the cookie-session fetcher live and BSE still served shells; BSE evidently requires JS-executed session state. Not claimed fixed; a headless-browser mechanism is a separate authorization/dependency decision. Jio prospectus config: env JSON maps only; no Jio entry exists, none invented/copied; discovery remains the intended path, blocked at retrieval.
- **Tests:** 4 new discovery classification tests + 1 activity-trace consistency test (UNAVAILABLE at provider/resolver/activity layers, no UNPUBLISHED, nothing persisted); `LISTING_EMPTY` fixture remodelled as a valid searched listing. Focused + full suites to be recorded at commit.

### Windows acceptance failure of `3fea259` (ingestion ing-5aa6dd92cd7640a8) — root cause and repair — 2026-10-18

- **Report:** the Windows runtime was restarted from `3fea259e6f90f29bb3b75b97b1efaa95f2530ad6` (uvicorn startup confirmed, health healthy) and ingestion `ing-5aa6dd92cd7640a8` again produced: BSE classic listing → JavaScript shell (listing not searched); BSE `publicissue.html` → JavaScript shell (listing not searched); SEBI listing → HTTPError; **provider outcome NOT_FOUND**; **activity completion UNPUBLISHED**; required terms unresolved; evaluation not run, persistence not attempted. The `3fea259` acceptance criterion (unusable listings ⇒ UNAVAILABLE) **failed**.
- **Root cause (established from the code and the trace, not inferred):** every classification other than `ok` emits a per-URL note, and the trace lists exactly three unusable sources. The one listing URL without a note is the NSE listing, so it was classified `ok` and it alone made the provider report NOT_FOUND. At `3fea259` `_classify_listing` accepted any HTML containing a `_LISTING_MARKERS` substring; that set included the *chrome* markers "public issues" and "all-upcoming-issues". The NSE page repeats its own path (`…/market-data/all-upcoming-issues-ipo`) in its navigation and canonical links — verified live and in the archived raw response on 2026-10-18 — while its listing table has a header row and **no issue row** (rows are client-side). So a page with no issue entry at all was counted as a searched listing; `reached = True` produced the NOT_FOUND at `OfficialDiscoveryProvider.find`, and `IssueTermsResolver.resolve` mapped any NOT_FOUND report to UNPUBLISHED. `3fea259` had only excluded *marker-less* responses; the NSE response is not marker-less, so its classification — and the failure — survived. Reproduction against the pre-fix engine: NSE response classified `ok` → provider NOT_FOUND → resolver UNPUBLISHED; the new regressions fail on that code (`assert 'NOT_FOUND' == 'UNAVAILABLE'`).
- **Correction (generic, no issuer-specific code):** a listing is now recognised by its **issue entries**, never by a marker substring — a data row of an issue-listing table (header naming ≥2 issue-listing columns) carrying an issue date or a per-issue link, or a per-issue link (`DisplayIPO`/`ACQDisp`/`attachdocs`/`issue-information`/`price-band`). An HTTP 200 that is neither a homepage nor a shell is no longer a searched listing; the classification order is shell → ok → homepage → empty, and the NSE-style client-side table is reported as "no issue entries in the served HTML". `ProviderReport` gained `listing_searched` and a structured `notes` list: the resolver maps a NOT_FOUND report to UNPUBLISHED **only** when it is substantiated by a real listing search, so a search of the unverified retained corpus can no longer produce UNPUBLISHED either. The activity trace now emits one event per unusable source (no reason lost to the bounded event message) and reports "Official discovery outcome: UNAVAILABLE". CONFLICT, allow-list, issuer matching, document classification, Market-Lot-only extraction, provenance, cache, retries, manual entry, scoring, thresholds, knockouts, golden fixtures and historical evaluations are unchanged; missing required terms still block evaluation and persistence.
- **BSE retrieval (facts vs. hypotheses):** *proven* — the classic BSE listing carries the Jio row (21-10-2026 – 23-10-2026, 1065.00–1119.00, `DisplayIPO?id=4894`) when retrieved by the investigator tooling, and `publicissue.html` serves the same table; the Windows runtime still receives a JavaScript shell from both URLs with the cookie-session fetcher live; the NSE issue rows are client-side and unreadable by any plain HTTP client; this sandbox's TLS to BSE/NSE/SEBI fails (egress restriction, not evidence about Windows). *Not proven* — that BSE's protection "requires JavaScript-executed session state": a rendering client receives the real page while a plain HTTP client receives a shell, but the discriminating factor has not been isolated (TLS/JA3 fingerprinting, JS-set session cookies, header set/ordering and IP reputation all remain open). **No headless-browser dependency or architecture change was introduced**; that remains a separate requirements/authorization decision. BSE retrieval is **not** fixed and is **not** claimed fixed: the honest terminal status remains UNAVAILABLE with precise per-URL reasons.
- **Tests:** new regressions reproduce the exact Windows pattern (NSE chrome-only page + both BSE shells + SEBI HTTPError) and assert UNAVAILABLE at the provider, resolver, activity-trace, API and UI layers, with no UNPUBLISHED anywhere, terminal BLOCKED, evaluation/persistence SKIPPED and nothing persisted; a classification test pins chrome-marker responses as non-listings; a positive test pins the live BSE listing row shape as a genuine listing that still yields 1065/1119/12. `LISTING_EMPTY` was remodelled to the recorded BSE row shape (it had no issue row, so it did not model a genuine listing under the corrected predicate); its assertions are unchanged. **Results (this commit):** focused `tests/test_official_discovery.py` + `tests/test_ingestion_activity.py` = 32 passed (exit 0); focused discovery + activity + resolver + cross-IPO = 39 passed (exit 0); **full backend suite 1046 passed, 0 failed, 19 warnings, exit code 0 (15m33s)**; frontend **76 passed, 0 failed, exit code 0** (74 before, +2 new). Pre-fix verification: the new regressions fail on the `3fea259` engine (`assert 'NOT_FOUND' == 'UNAVAILABLE'`), and the pre-fix engine run reproduces the report exactly (NSE response classified `ok` → provider NOT_FOUND → resolver UNPUBLISHED).
- **Windows acceptance (still user-side, and now a retrieval question rather than a classification question):** restart the API from the published commit and re-upload the Jio RHP once. Expected terminal status: **UNAVAILABLE** with the four per-source reasons (BSE shell ×2, SEBI HTTPError, NSE no issue entries) — never UNPUBLISHED. A new Windows acceptance test is *not* needed for discovery correctness (the exact response pattern is now a deterministic regression at every layer); a Windows re-run remains the only way to observe the live responses from the user's network and to answer whether BSE serves the real listing to the application client from that network.
- **Record:** `docs/investigation/WINDOWS-DISCOVERY-UNAVAILABLE-REPAIR-2026-10-18.md`.

### Windows acceptance failure of `0dda109` (ingestion ing-32ddf313bbe247b0) — actual root cause and repair — 2026-10-18

- **Report (authoritative acceptance evidence):** the Windows checkout matched the PR #6 head exactly (`0dda1093040cfe8a3217160d1b21665f2902a519`, clean tree, API restarted, startup OK). Ingestion `ing-32ddf313bbe247b0` again produced: BSE classic listing → JavaScript shell (listing not searched); BSE `publicissue.html` → JavaScript shell (listing not searched); SEBI listing → HTTPError; **aggregate official-discovery outcome NOT_FOUND**; **activity completion UNPUBLISHED**; required terms unresolved; evaluation not run, persistence not attempted. The `0dda109` acceptance criterion (unusable listings ⇒ UNAVAILABLE) **failed** — the round-1 conclusion that `0dda109` fixed the contradiction is **withdrawn**.
- **Root cause (proved, not inferred):** at `0dda109` `_has_issue_entries()` began with the unconditional branch `if cls._per_issue_links(text): return True`, and `_per_issue_links()` matched **any** `href=` in the document (including `<link rel="canonical">`/`<link rel="alternate">`) against the tokens `displayipo, acqdisp, attachdocs, issue-information, issue_information, price-band, price_band`. NSE's real response carries that chrome on every page it serves: the site-wide market-data menu item `href="/market-data/price-bands-surveillance-actions"` and the canonical/alternate metadata `…/market-data/issue-information?series=EQ&symbol=VNL` (+13 language variants). Running the **exact `0dda109` code** (`git archive 0dda109`) against the retained real NSE response (`evidence/ipo-subscription/vnl-20261011/vnl-issue-information.html`, 313,038 bytes, 2026-10-11) classifies it **`ok`** with 17 matched hrefs and **0 `<td>` cells** (2 tables, 4 `<tr>`, no issue record at all — the NSE listing table is filled client-side); the NSE *listing* response built from that real header is likewise classified `ok` on the strength of the single menu link. So the **NSE listing source** — the one configured source that emitted no note — was the source that set `listing_searched = true`, produced NOT_FOUND and (via `IssueTermsResolver.resolve`) UNPUBLISHED. The round-1 regression fixture `NSE_MARKER_ONLY_LISTING` modelled the NSE response **without** that chrome, which is why it could not reproduce the real response.
- **Observability defect (also fixed):** the `ok` path emitted no note, so a source could contribute to the aggregate outcome with no visible event; the Windows trace showed three per-source failures and nothing about NSE. `ProviderReport` now carries one `ListingAttempt` per configured source (`url`, `classification`, `searched`, `issue_entries`, `detail`) plus `searched_listings`; the service emits one activity event per source (SUCCEEDED for a listing really read, FAILED otherwise); the API payload carries `providers[].sources` and `providers[].searched_listings`; the UI lists every source with whether its listing was really searched; a candidate document that could not be used is no longer discarded silently.
- **Correction (generic, no issuer-specific code):** a response counts as a searched listing only when it carries an **issue record** — a table data row (`<tr>` with `<td>` cells) that links to one issue/document (anchor-only hrefs, so canonical/alternate metadata cannot count), or a data row of an issue-listing table (header naming ≥2 issue-listing columns) that carries an issue date. Navigation, menus, canonical/alternate links and language switchers are never inside a data row and can no longer stand in for an issue record; the NSE client-side listing is therefore `empty` ("no issue entries in the served HTML") and unusable. The resolver now requires a NOT_FOUND report to be substantiated **and** to name the listings it read (`r.listing_searched and r.searched_listings`): a report that claims a search but names no listing yields UNAVAILABLE. The synthetic fixtures that modelled a listing as bare anchors outside any table (`LISTING_WITH_NOTICE`, `LISTING_WITH_PROSPECTUS`, `BSE_LISTING`, `JIO_LISTING_WITH_PROSPECTUS`) were remodelled to the shape the exchanges really serve (issue records in the listing table's rows); the genuine-listing positive cases are unchanged and still classify `ok`. CONFLICT, allow-list, issuer matching, document classification, Market-Lot-only extraction, provenance, cache, retries, manual entry, scoring, thresholds, knockouts, golden fixtures and historical evaluations are unchanged; missing required terms still block evaluation and persistence.
- **BSE retrieval:** unchanged and **not** fixed, **not** claimed fixed. The Windows runtime still receives a JavaScript application shell for both BSE listing URLs; the honest terminal status is UNAVAILABLE with per-URL reasons. No headless browser, no new runtime dependency, no invented issuer terms.
- **Tests:** new regressions reproduce the second failure from the **retained real NSE response**: `test_real_nse_response_is_not_a_searched_listing` (real capture and the listing response built from its real header are not searched listings, while the `0dda109` rule is kept in the test to show it called both `ok`), `test_windows_trace_pattern_with_real_nse_response_is_unavailable` (provider UNAVAILABLE, `listing_searched` false, no searched listing, four attempts, resolver UNAVAILABLE), `test_every_configured_source_produces_a_visible_attempt`, `test_not_found_without_a_named_searched_listing_is_never_unpublished`, `test_genuine_listing_searched_is_named_in_the_report` (positive case retained); the activity test now asserts one visible event per configured source (including the NSE one that used to be silent) and the API test asserts `searched_listings = []` plus four source records; a frontend test asserts the UI lists every source and never shows UNPUBLISHED. **Results (this commit):** focused (discovery + activity + resolver + runtime + windows-retrieval + cross-IPO) = **69 passed, 12 warnings, exit 0 (309.19 s)**; **full backend suite 1051 passed, 0 failed, 19 warnings, exit code 0 (1236.05 s)**; frontend **77 passed, 0 failed, exit code 0** (76 before, +1 new). Pre-fix verification: the new regressions **fail against the `0dda109` engine** — its classifier returns `ok` for the real NSE response and the provider returns `NOT_FOUND` instead of `UNAVAILABLE` (4 failed, exit 1), i.e. the reported Windows contradiction reproduced deterministically from the real response.
- **Windows acceptance:** a new Windows upload is **not** required for discovery correctness — the exact second-failure response pattern is now a deterministic regression at provider, resolver, activity, API and UI level, built from the real NSE response rather than a hand-written approximation. A Windows re-run remains the only way to observe the live BSE/NSE/SEBI responses from the user's network, i.e. to answer whether BSE serves the real listing to the application client from that network (retrieval capability, not classification).
- **Record:** `docs/investigation/WINDOWS-DISCOVERY-UNAVAILABLE-REPAIR-2026-10-18.md` §0 (second failure, actual root cause, corrected repair) — the round-1 §1–§3/§4.1 there are marked superseded, not erased.

### Four-field manual issue-term entry — initial screening without waiting for official sources — 2026-10-18

- **Directive (user, this session):** screen an IPO from broker-platform terms as soon as it appears; all four required issue terms — `issue.price_band_low`, `issue.price_band_high`, `issue.lot_size`, `issue.ofs` — must be manually enterable so initial screening never waits for NSE/BSE/SEBI retrieval. Manual input must stay explicitly distinguishable from verified official evidence; the Windows-verified discovery classification (`5d9597c`) must remain intact. This extends the Step 4 Area C minimum decision's scope item (5) ("three terms; OFS remains derived only") per explicit user direction; the other four minimum-decision parameters (MANUAL_ENTRY/UNVERIFIED labelling, mandatory explanation, conflict handling with explicit confirmation, no provenance upgrade) are unchanged.
- **Proven root cause of the OFS blockage (code-traced at `e05c0ef`):** a scope restriction implemented end to end — `MANUAL_ISSUE_TERM_FIELDS` excluded `ofs` (service rejected it as unsupported), the `/ingest/manual-terms` endpoint had no `ofs` form field, and the UI marked `issue.ofs` "cannot be entered manually". Because the approved OFS derivation (seller shares × cap price) runs only inside notice/prospectus assembly or the `missing == {"ofs"}` case, a filing with all-four `[●]` terms plus failed discovery stranded on `issue.ofs` with no permitted supply path (the old real-RHP test pinned this exactly).
- **Canonical `issue.ofs` (from the v1.5 contract; not invented):** the Offer-for-Sale **monetary amount in the filing's `financials.reporting_unit`** (`INR_LAKHS`/`INR_CRORES`); schema `number, minimum 0`; never a share count; an explicit 0 is an operator "no offer for sale" statement and is never a default for unknown; derivation formula unchanged (`(sum(seller_shares) × issue.price_band_high) / unit_multiplier`, `SRC-DERIVED`).
- **Implementation:** `POST /api/v1/ingest/manual-terms` accepts `ofs` (finite number ≥ 0) alongside the three pricing terms; service validation is field-specific (floor/cap > 0, band consistency re-checked after application, lot a whole number ≥ 1, non-negative finite OFS, NaN/Inf/bool/string rejected) with no zero/null/default substitution; the AWAITING payload carries `reporting_unit` so the UI labels the OFS unit (₹ lakh/₹ crore). Applied values record `MANUAL_ENTRY` / `SRC-MANUAL-ENTRY` with the operator explanation, presented UNVERIFIED in the response (`issue_terms.manual_entry`: fields, exact values, explanation, `verified: false`, `reporting_unit`), the evidence API, and the persisted record. Conflict handling (409 until explicit confirmation), verified-value protection (`overridden_by_verified`), issuer/IPO isolation (values travel only within their upload request) and the fail-closed posture are unchanged. A manual completion preserves the official-discovery outcome beside `manual_entry` (stays `UNAVAILABLE` where appropriate) — manual input is never evidence of official publication. New mirror gate: when the four terms complete but `issue.fresh_issue` is undisclosed, evaluation fails closed naming `issue.fresh_issue` precisely (not in the four-field contract; never invented). UI panel: all four inputs (OFS unit-aware), broker-platform guidance, unverified/`MANUAL_ENTRY` wording, evaluated-values + provenance in the result panel; same retained upload re-submitted (no repeated uploads).
- **Scoring/persistence:** existing `pipeline.evaluate()` unchanged — no formula/weight/threshold/ranking/knockout change; complete valid four-field evaluations follow the existing persistence pathway (immutable store, lifecycle registration, duplicate idempotency); nothing persists while required terms are unresolved or invalid.
- **Tests (executed this commit):** new `tests/test_four_field_manual_terms.py` **15 passed** (complete four-field submission reaches scoring — recorded score reproduced by replaying the persisted input through `pipeline.evaluate()`; exact values + MANUAL_ENTRY on all four incl. evidence API UNVERIFIED + `INR lakh` unit; per-field omission incl. `issue.ofs` stays blocked naming the field with nothing persisted; real root-cause scenario; `fresh_issue` fail-closed; invalid OFS negative/NaN/Inf/bool/string and invalid band/lot rejected without defaulting; explicit OFS 0 recorded as submitted; OFS conflict 409→confirm; manual never displaces `OFFICIAL_VERIFIED`; per-IPO isolation; discovery `UNAVAILABLE` preserved). Updated `tests/test_step5_auditor_and_manual_terms.py` **19 passed** (127.7 s) — real Vishal RHP: three terms still block on `missing_fields == ["ofs"]`, and the new `test_vishal_real_filing_four_field_manual_entry_completes_evaluation` completes end to end on the real filing (extraction → discovery UNAVAILABLE → 208/220/68/3300 in INR_LAKHS → existing engine evaluates 24.0 INSUFFICIENT_DATA → persisted, MANUAL_ENTRY on all four, recorded score reproduced from the persisted input). Focused discovery group (discovery + activity + resolver + runtime + ui7 + presentation API) **98 passed** (232 s) — the Windows-verified classification regressions (real NSE chrome response, chrome+BSE shells+SEBI HTTPError → UNAVAILABLE, four visible source attempts, genuine-listing NOT_FOUND) pass unchanged. **Full backend suite 1067 passed, 0 failed (984.9 s, exit 0)**; frontend **80 passed, 0 failed** (77 before, +3 new four-field UI tests).
- **Docs:** `docs/investigation/FOUR-FIELD-MANUAL-ISSUE-TERM-ENTRY-2026-10-18.md` (root cause, OFS contract, four-field contract/validation, provenance, eligibility, scoring/persistence, discovery preservation, tests); `docs/openapi/presentation-api-v1.yaml` gains the `/ingest/manual-terms` contract (four fields, 400/409/422 semantics); `handoff/UI-ACCEPTANCE-CHECKLIST-2026-10-17.md` A4 updated to the four-field acceptance.
- **Publication:** implemented on this session's branch `arena/d15866b5-ipo-screening-engine` (fast-forwarded to the verified baseline `e05c0ef`, so `5d9597c` and its regressions are in ancestry). PR #6 remains OPEN and unmerged; `main` untouched. Arena fixes each session to its own branch and this session may publish only `arena/d15866b5-ipo-screening-engine`, so the PR #6 head branch (`arena/5dd3fe52-ipo-screening-engine`) cannot be advanced from here — the implementation is published on the session branch and cross-referenced on PR #6 (comment), keeping the established branch/PR lifecycle (no competing PR, no merge).
- **Record:** `docs/investigation/FOUR-FIELD-MANUAL-ISSUE-TERM-ENTRY-2026-10-18.md`.

### Publication amendment — actual remote state — 2026-10-18

- **Implementation commit (remote-verified):** `a7f823d4c4d5184460eda8b4883259be511baff1` on `arena/d15866b5-ipo-screening-engine` (`git ls-remote` confirms the remote tip). It descends from the Windows-verified tip `e05c0efbca1ecb3024e52da73a22e180ea171118`, so `5d9597c46a0a73171f33daee0db44b6e8e28f194` and `e05c0ef` are in the published ancestry (`git merge-base --is-ancestor` verified).
- **PR #6 (remote-verified after publication):** state `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` at `e05c0efbca1ecb3024e52da73a22e180ea171118` (unchanged), base `arena/573e69a4-ipo-screening-engine`. Evidence comment posted: `https://github.com/ramkivs/ipo-screening-engine/pull/6#issuecomment-6255011605`.
- **`main` (remote-verified):** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. No competing PR opened; PR #6 not merged or closed.
- **Windows acceptance (user-side, outstanding):** restart from `a7f823d` on `arena/d15866b5-ipo-screening-engine`, hard-refresh, upload a terms-placeholder RHP, complete the four-field manual panel from the broker platform; expect a normal evaluation listing the four values as manually entered (unverified). A three-term submission must still block naming `issue.ofs`.

### Manual issue-term audit-log correction — 2026-10-19

- **Defect (user-reported):** manual issue-term inputs submitted and processed, but the audit log "records nothing". Full path traced (UI → API → validation/conflict → manual recording → evaluation → persistence → audit-event creation → persistence → retrieval → presentation); no UI cause assumed. Investigation record: `docs/investigation/MANUAL-TERMS-AUDIT-LOG-2026-10-19.md`.
- **Root cause / failing layer:** predominantly **D** (records persisted but unreachable/not presented) plus **C** (correlation dropped at the API boundary) and A-adjacent event-content gaps. The ingestion-activity store did create records (reproduced: accepted path `ing-3a19027aa53f48af` 24 events incl. `manual_entry`; all error paths created FAILED/BLOCKED records), but (i) `POST /ingest/manual-terms` error handlers omitted `**_activity_ref(exc)`, so 400/409/422/500 bodies had no `ingestion_id`/`activity_url` (violating the contract pinned by `test_api_error_correlates_to_recoverable_history`); (ii) `frontend/api.js` error mapping read only nested `detail` bodies and never the flat `HTTPException`-detail body the app actually returns, dropping the correlation ids (and conflict/awaiting diagnostics); (iii) `frontend/app.js` never registered `result.ingestion_id` (`ipo.lastIngestionId`), never refreshed the Ingestion Activity panel, and showed no audit reference — the operator's audit log showed nothing; (iv) no submission-receipt/conflict events and the accepted event omitted values/explanation/`verified:false`/`ipo_id`.
- **Correction (minimal, existing architecture; uncommitted work published as one commit on the session branch):** `service.py` — `term_resolution/manual_submission/SUCCEEDED` receipt before validation, `manual_validation/FAILED` on rejection, `conflict/BLOCKED` with conflict list + `confirmation_required` before the raise, accepted `manual_entry` details extended with `values`/`explanation`/`verified:false`/`conflicts_confirmed`/`ipo_id`; `api.py` — `**_activity_ref(exc)` on all remaining manual-terms error handlers; `api.js` — flat error-body contract accepted at all three request sites + correlation preserved in `err.details`; `app.js` — `attachIngestionAudit()` registers the id and refreshes the Ingestion Activity panel; result panel shows `Audit trace recorded: <id>`; all three error branches show `Audit trace: <id>`. Retrieval end to end: `GET /api/v1/ingestions`, `/ingestions/{id}`, `/ingestions/{id}/events` (pinned by the new tests).
- **Safeguards preserved (unchanged, verified):** scoring/weights/thresholds/knockouts/golden snapshots untouched; no inferred terms; no default zero/null OFS (explicit 0 valid); fail-closed invalid/incomplete; conflict-confirmation intact; `OFFICIAL_VERIFIED` never displaced; discovery `UNAVAILABLE` stays `UNAVAILABLE`; per-IPO isolation; no secrets in events; audit-store failures propagate loudly (never a silent success); atomicity exactly per the existing contract (per-write tmp+replace; **no** evaluation↔audit cross-write transaction — documented, not invented). Provenance never upgraded (`MANUAL_ENTRY`/`verified:false` in events and evidence).
- **Tests (all executed in this investigation; exit codes 0 unless noted):** `python -m pytest tests/test_manual_terms_audit_log.py -q` → **12 passed** (creation + end-to-end retrieval: receipt/acceptance/evaluation/persistence distinct, IPO/evaluation association, provenance, rejection/conflict/confirmation audit, no-false-success on evaluation failure, loud audit-store failure incl. at finalization, per-IPO isolation); `cd frontend && npm test` → **85 passed** (incl. 5 new: flat-contract correlation mapping, success/rejection/conflict audit display + registration, no-id wording); `python -m pytest tests/ -q` (full backend) → **1079 passed**; `tests/test_frozen_core_line_endings.py tests/test_vishal_golden.py tests/test_issue_terms_resolver.py` → **30 passed**; `tests/test_v16_implementation.py` → **45 passed**; `tests/test_four_field_manual_terms.py tests/test_step5_auditor_and_manual_terms.py` → **34 passed**; `tests/test_official_discovery.py tests/test_issue_terms_windows_retrieval.py` → **35 passed**.
- **Publication amendment — actual remote state after this publication (to be verified against `git ls-remote` in the publication step):** the fix commit lands on `arena/d15866b5-ipo-screening-engine` only. **PR #6 cannot receive it at its head** (`arena/5dd3fe52-ipo-screening-engine` is unmovable via the GitHub API) and stays OPEN/UNMERGED with base `arena/573e69a4-ipo-screening-engine`; an evidence comment is posted on PR #6. `main` untouched (`01ba66c12ca1195fd7acbd287c3e39a019808094`). No competing PR. The four-field implementation (`a7f823d`), the tracker amendment (`610223c`), the Windows-verified discovery fix (`5d9597c`) and `e05c0ef` remain in the published ancestry of the session branch.
- **Windows acceptance (user-side, outstanding):** restart from the session-branch tip, hard-refresh; upload a terms-placeholder RHP; complete the four-field panel; then check **Workflow Progress & Audit Status → Ingestion Activity**: the submission must show `manual_submission` → `manual_entry` (with values) → `evaluation/completed` → `persistence/completed`, the result panel must show `Audit trace recorded: <ingestion_id>`, and a rejected/conflicted submission must show `Audit trace: <ingestion_id>` with its rejection/conflict events retrievable at `/api/v1/ingestions/<id>`.

### Publication amendment — actual remote state — 2026-10-19

- **Audit-log correction commit (remote-verified):** `801ac6b899eae0f96563493a24844207ab05b093` on `arena/d15866b5-ipo-screening-engine` (`git ls-remote` confirms the remote tip). `git merge-base --is-ancestor` verified that `5d9597c46a0a73171f33daee0db44b6e8e28f194` (Windows-verified discovery fix), `e05c0efbca1ecb3024e52da73a22e180ea171118`, `a7f823d4c4d5184460eda8b4883259be511baff1` (four-field implementation) and `610223cab38cef506cf56ec4f884e788ba2144a3` are all in its published ancestry.
- **PR #6:** stays **OPEN / UNMERGED** (base `arena/573e69a4-ipo-screening-engine`, head `arena/5dd3fe52-ipo-screening-engine` at `e05c0ef`). **The fix is NOT on the PR #6 head** — the head branch is unmovable via the GitHub API — so PR #6's diff does not include the audit-log correction; an evidence comment on PR #6 records the correction, its commit SHA and this reconciliation. No competing PR opened; no merge/close of PR #6.
- **`main` (remote-verified):** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched.

### Jio manual-entry dead end closed — issue.fresh_issue manual entry — 2026-10-19

- **Defect (user-reported, Windows `ing-8db36776dd794ec3`, `U72900GJ2019PLC110816_JIO.pdf`):** filing extraction, issuer identification and official discovery (UNAVAILABLE) succeeded; four-field manual entry succeeded; eligibility then blocked evaluation **solely because `issue.fresh_issue` was missing** — a field the manual form did not accept. Evaluation did not run; nothing was persisted. Investigation record: `docs/investigation/JIO-FRESH-ISSUE-MANUAL-ENTRY-2026-10-19.md`.
- **Trace:** the mirror gate in `presentation/service.py` (added in `a7f823d` to fail closed "instead of a schema failure") names `issue.fresh_issue` when the four terms complete but the fresh amount is absent; `MANUAL_ISSUE_TERM_FIELDS` excluded it.
- **Contract reconciliation (CASE B):** `issue.fresh_issue` **is** a genuine prerequisite for every evaluation — `schema/ipo-input.v1.5.schema.json` `issue.required` (spec s20 hard gate, frozen since v1.5 `fb822e5`); `evaluate()` hard-fails on None/absent (`SchemaValidationError`, reproduced); every historical evaluation carries it. Scoring consumes it in module C (`fresh_share` 3 pts, `use_of_proceeds` 4 pts) and never silently zeros it (absent -> UNKNOWN); it is not in `critical_data`. Prior decision (JIO-RHP 2026-10-17): completing class = final Prospectus (OFFICIAL_VERIFIED); the schema gap is filled with real values, never defaults. Therefore the gate is **not** bypassed; the fix is the authorized supply path: the bounded manual entry (broker IPO page values, MANUAL_ENTRY/UNVERIFIED, mandatory explanation) now includes `issue.fresh_issue`. The 2026-10-19 user directive supersedes the four-field scope clause (recorded additively in the four-field record §10; nothing rewritten).
- **Correction:** `service.py` — `MANUAL_ISSUE_TERM_FIELDS` += `fresh_issue`; monetary validation identical to `ofs` (finite ≥ 0; explicit 0 = operator pure-OFS statement, never a default); fail-closed gate preserved (genuinely absent still blocks naming `issue.fresh_issue`); reason texts updated to the five-field supply set. `api.py` — optional `fresh_issue` form field on `/ingest/manual-terms` (explicit 0 preserved). `api.js`/`app.js` — fifth input with unit-aware label (`reporting_unit`), five-field contract text, result table unit; non-enterable terms (e.g. `issue.open_date`) remain blockers. No scoring/weights/thresholds/knockouts/ranking/golden/frozen-core changes; no fabricated or defaulted amount; `OFFICIAL_VERIFIED` never displaced; discovery `UNAVAILABLE` preserved; audit-log contract (2026-10-19) covers the fifth field automatically.
- **Tests (all executed; exit codes 0):** `pytest tests/test_fresh_issue_manual_entry.py -q` -> **12 passed** (exact observed failure reproduced fail-closed on the real Jio PDF; five-field submission completes the same filing end to end with persistence + audit retrieval; no-default/no-fabrication; explicit 0; invalid rejection; verified-value protection; score equality extracted-vs-manual; conflict confirmation). `pytest tests/ -q` full backend -> first run **1090 passed + 1 flake** (`test_reproducibility_store.py::test_workbook_bytes_are_deterministic`, workbook byte-compare of one record, untouched by this change; passes in isolation/in-file), re-run **1091 passed** exit 0. `tests/test_four_field_manual_terms.py + test_step5_auditor_and_manual_terms.py + test_manual_terms_audit_log.py` -> 46 passed. `tests/test_jio_rhp_issue_terms.py + test_generic_issue_terms_extraction.py + test_validation_gates.py + test_ui7_ingestion.py + test_ingestion_activity.py` -> 86 passed. frozen/golden/resolver -> 30 passed; v1.6 -> 45 passed; discovery+windows-retrieval -> 35 passed. `cd frontend && npm test` -> **87 passed** (five-field panel/transport/explicit-0).
- **Publication:** published on `arena/d15866b5-ipo-screening-engine` (implementation SHA recorded in the publication amendment below; remote-verified via `git ls-remote`). **PR #6 lifecycle preserved:** OPEN/UNMERGED, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0ef` cannot receive this fix via the GitHub API; evidence comment posted on PR #6. `main` untouched; no competing PR.
- **Windows acceptance (user-side, outstanding):** see the PowerShell commands in the publication evidence; run against the Jio filing with actual broker-sourced terms and verify the evaluation, persistence, MANUAL_ENTRY provenance and the audit record.

### Publication amendment — actual remote state — 2026-10-19 (fresh_issue fix)

- **Implementation commit (remote-verified):** `958337375174be87726ed1bac0e3d6dc48aa8c99` on `arena/d15866b5-ipo-screening-engine` (`git ls-remote` confirms the remote tip). `git merge-base --is-ancestor` verified `5d9597c46a0a73171f33daee0db44b6e8e28f194`, `e05c0efbca1ecb3024e52da73a22e180ea171118`, `a7f823d4c4d5184460eda8b4883259be511baff1` and `1840fd7e16c64a800c9095ec98621695173a61b4` all in its published ancestry.
- **PR #6 (remote-verified):** state `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118` (unchanged; unmovable via the GitHub API) — **the fix is NOT on PR #6's head**; evidence comment posted on PR #6. No competing PR; PR #6 not merged or closed; its lifecycle preserved exactly.
- **`main` (remote-verified):** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched.
- **CI:** no hosted CI workflows are configured for this repository (none discovered via `gh workflow list`/`.github`); the verification evidence is the executed local test matrix recorded above and in the investigation record.

### Jio Platforms evaluation diagnostic — financial-statement ingestion corrections — 2026-10-19

- **Subject:** the 2026-10-19 Jio evaluation scorecard (19/100, INSUFFICIENT_DATA, Low 33%, unknown 64/available 32/missing 33, Revenue CAGR −48.36%, A 3/25, B 0/20, C 11/15, D 5/15, E+F 0/25). Deterministic reproduction matched all nine dimensions (content fingerprint; byte-identical result_hash is run-sensitive via snapshot capture timestamps). Investigation record: `docs/investigation/JIO-EVALUATION-DIAGNOSTIC-2026-10-19.md`.
- **Root cause of −48.36% CAGR (verified, corrected):** SEBI RHP summary/Ind AS statement tables carry interim (three-month) columns before the fiscal block, newest-first, with note numbers; `financial_tables.py::_parse_table_lines` selected the leftmost n columns, mixing Q1 Jun-2026 + Q1 Jun-2025 + Fiscal-2026 into the three fiscal periods. Independent recalculation from the true fiscal columns: (1,468,853/1,095,581)^0.5 − 1 = **+15.79%** — the figure the RHP itself states (p128). Not a formula error, not a unit error, not a genuine decline; single consolidated basis.
- **Other confirmed ingestion defects (all corrected):** `net_worth` regex matched "Total Equity and Liabilities" (net worth was silently total assets); CFO row label "Net Cash Flow from Operating Activities" unmatched; plain "Borrowings" rows unmatched (total_debt unparsed); "Depreciation and Amortisation" spelling unmatched; KPI "Return on Average Capital Employed" (p132: fiscal 10.76/12.50/12.83) missed (label + wrapped row + column selection); "(in ₹ million)" unit header undetected (default INR_LAKHS). Fix bundle: `financial_tables.py` (fiscal-block `nums[-n_cols:]` selection — identical for 3/4-numeric rows so Vishal pins are byte-identical; row-label/net-worth patterns; KPI wrap+average-tolerant parsing), `numbers.py` (in-₹-million forms), `frontend/app.js` (INR_MILLIONS label). No scoring formula/weight/threshold/knockout/golden/frozen-core changes; fail-closed governance preserved.
- **Adjudications:** "missing fields default to zero" is FALSE (scoring.py s18: UNKNOWN contributes 0 to base but full max to upper bound and is excluded from the confidence numerator; `test_core_semantics.py` pins it). Litigation `criminal_or_regulatory` is supported by evidence (company Nil, subsidiaries criminal proceedings p464) — 0/4 follows the rubric. F-module (market) is correctly UNKNOWN at the 2026-10-19 timestamp (bidding opens 10-21); no later subscription data may enter this historical evaluation. use_of_proceeds UNKNOWN is correct (GCP [●] p120; ceiling never substituted). rpt/auditor/industry/moat/concentration: governed UNKNOWN with required evidence named (see record §H).
- **Post-fix evaluation (same filing + five manual terms):** score **29/100**, verdict INSUFFICIENT_DATA (critical-data gaps unchanged in kind: auditor_opinion, going_concern_uncertainty, net_worth_latest, contingent_liab_pct_networth), confidence Low (46%), unknown 54/available 46; A 13/25 (CAGR 4/6 at +15.79%, ROCE 1/5 disclosed, CFO 5/5, leverage UNKNOWN — net worth not a stated row), B 0/20 (peers not safely ingestable; PEG computed 0/4), C 11/15, D 5/15, E+F 0/25.
- **Tests (all executed; exit codes 0):** `pytest tests/test_financial_statement_column_mapping.py -q` -> **9 passed** (synthetic statement shapes + real Jio pins). `pytest tests/test_extraction.py -q` -> 12 passed (Vishal byte-identical pins: net_worth 8678.35, cfo 2715.47, final_score 35.0, INR_LAKHS). `pytest tests/test_jio_rhp_issue_terms.py -q` -> 7 passed (one pin corrected: prospectus fresh amount 1,485,000 → 148,500 — the old pin encoded the misdetected-unit conversion; stated Rs.148,500 million is now recorded in its own INR_MILLIONS reporting unit). Focused batch (step5+ui7+activity+core_semantics+vishal_golden+frozen) -> 102 passed. Four-field+fresh-issue+audit+cfo+rpt+Jio batch -> 65 passed + the pin update above. Full backend `pytest tests/ -q` -> **1100 passed**. `cd frontend && npm test` -> **87 passed**.
- **Publication:** commit SHA recorded in the publication amendment below on `arena/d15866b5-ipo-screening-engine` (remote-verified). PR #6 lifecycle preserved (OPEN/UNMERGED, head `arena/5dd3fe52` @ `e05c0ef`; fix NOT on PR #6 head; evidence comment posted). `main` untouched; no competing PR; no hosted CI (verified).
- **Windows acceptance:** PowerShell read-back + re-ingestion commands in the PR comment and final report; the operator's existing 2026-10-19 evaluation remains immutable evidence of the pre-fix behavior.

### Publication amendment — actual remote state — 2026-10-19 (Jio diagnostic fix)

- **Implementation commit (remote-verified):** `950d2398d0143de3f15d3a2fd34621f7ef8b784d` on `arena/d15866b5-ipo-screening-engine` (`git ls-remote` confirms the remote tip). `git merge-base --is-ancestor` verified `5d9597c46a0a73171f33daee0db44b6e8e28f194`, `e05c0efbca1ecb3024e52da73a22e180ea171118`, `958337375174be87726ed1bac0e3d6dc48aa8c99` and `0d71aa8e6295efadd31dc559afa96757c7b97754` all in its published ancestry.
- **PR #6 (remote-verified):** state `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118` (unchanged; unmovable via the GitHub API) — the fix is **not** on PR #6's head; evidence comment posted on PR #6. No competing PR; PR #6 not merged or closed.
- **`main` (remote-verified):** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. No hosted CI workflows (verified `gh workflow list` empty).

### HD Fire Protect peer-ROE schema violation — peer row mapping + early bounds rejection — 2026-10-19

- **Subject:** audit trace `ing-81fd285e5b8248c6` (Windows): `PROCESSING_FAILED` with `SCHEMA_VIOLATION at peers/0/roe_pct: 26957.28 is greater than maximum 10000` (peers/1: 21700.34); separate `issue.ofs` conflict (entered 71231 vs filing-extracted 0, operator-confirmed). Record: `docs/investigation/HD-FIRE-PEER-ROE-SCHEMA-VIOLATION-2026-10-19.md`.
- **Cause class (established by reproduction on in-repo reference filings, not from magnitude):** `sections.extract_peers` mapped peer cells by hard-coded R.K-Fashion layout positions only — the Vishal listed-peers table demonstrably mapped P/E into `roe_pct` (13.86; pb 0.0; 115-word prose "peer" name) — and the row tokenizer dropped `[●]`/NA placeholder cells, shifting later columns (demonstrated: NAV/PAT cells land at `roe_pct`). Monetary cells in `roe_pct` (the 26957.28/21700.34 signature) follow from either mechanism. Scaling/unit conversion eliminated (no scaling code exists between cell and schema; stored values equal raw cells). Which mechanism (or a genuinely extreme source RoNW) produced the two HD Fire values is unresolved pending the raw rows (Windows store; retrieval commands in the record).
- **Why it passed upstream:** `CanonicalInputBuilder.validate()` is a no-op when `issue.price_band_low is None` and the service never calls it; the first full schema enforcement is `pipeline.evaluate()` step 1 (`enforce_schema`) — hence the anonymous evaluation-time wall after the operator's term work.
- **Corrections (narrow; no clamping/rewriting/relaxation; no scoring changes):** `extract_peers` maps cells ONLY against recognised header layouts (two evidence-anchored signatures; placeholder-preserving alignment; strict width; prose names rejected; unrecognised layout → NO peers, module B governed-UNKNOWN); new `schema_validation.validate_peer_records()` names peer+field via the same schema definition; `service.ingest_document` rejects out-of-contract peers EARLY (400 + `validation/peer_contract` FAILED audit event: "Raw values are never clamped or substituted"). R.K pins byte-identical; Vishal real-filing peers now equal the golden values (GPT 14.83/2.73/18.25; IHP 13.86/1.32/9.51).
- **Phase 4 OFS governance (verified + pinned):** conflict surfaced (409, `existing_value 0.0` FILING_EXTRACTION, `manual_value 71231.0`); confirmation applies the manual value; all five terms MANUAL_ENTRY/SRC-MANUAL-ENTRY/verified:false; `overridden_by_verified` empty; audit `manual_submission → manual_entry → evaluation/completed → persistence/completed` with `values.ofs == 71231.0`.
- **Tests (executed):** new `tests/test_peer_row_mapping_and_bounds.py` **11 passed** (both reported values named-and-rejected; cause-level retry with monetary cells; valid/extreme/invalid/scaled bounds; both layout pins; placeholder/no-layout/prose rows; service early rejection + valid flow; OFS governance E2E). `pytest tests/test_rk_fashion_reconciliation.py tests/test_extraction.py tests/test_vishal_golden.py -q` -> 36 passed. Four-field/fresh-issue/audit/step5/ui7 -> 78 passed. Jio/discovery/financial-mapping/core-semantics/connectors -> 89 passed. Full backend `pytest tests/ -q` -> **1111 passed**. `cd frontend && npm test` -> **87 passed**.
- **Publication:** implementation commit SHA recorded in the publication amendment below on `arena/d15866b5-ipo-screening-engine` (remote-verified). PR #6 lifecycle preserved (OPEN/UNMERGED, head `arena/5dd3fe52` @ `e05c0ef`; fix NOT on PR #6 head; evidence comment posted). `main` untouched; no competing PR; no hosted CI (verified previously).
- **Windows acceptance:** retrieval + retry commands in the record §"Retrieval / acceptance"; the affected ingestion is re-run through the supported workflow (governed outcomes only: source-true completion OR named early rejection).

### Publication amendment — actual remote state — 2026-10-19 (HD Fire peer-ROE fix)

- **Implementation commit (remote-verified):** `afdd4985a305fe4c3224ccd29e820395d0729f6b` on `arena/d15866b5-ipo-screening-engine` (`git ls-remote` confirms the remote tip). `git merge-base --is-ancestor` verified `5d9597c46a0a73171f33daee0db44b6e8e28f194`, `e05c0efbca1ecb3024e52da73a22e180ea171118`, `950d2398d0143de3f15d3a2fd34621f7ef8b784d` and `176c3b6afea1863a3fc4ea2449dc87bd9ba34239` all in its published ancestry.
- **PR #6 (remote-verified):** state `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118` (unchanged; unmovable via the GitHub API) — the fix is **not** on PR #6's head; evidence comment posted on PR #6. No competing PR; PR #6 not merged or closed.
- **`main` (remote-verified):** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. No hosted CI workflows configured (verified previously: `gh workflow list` empty).

### HD Fire Protect + Jio Platforms score reconciliation, evidence completeness and extraction audit — 2026-10-19

- **Record:** `docs/investigation/HD-FIRE-JIO-SCORE-RECONCILIATION-2026-10-19.md` (all seven requested deliverables, the 36-item HD Fire reconciliation, the complete Jio 29→21 bridge, the source map, the ranked remediation plan, the executed test evidence and the Windows-only acceptance commands).
- **Baseline:** `e1df89b2af3bd432a70fe9716e266895ba6ff2e7` on `arena/d15866b5-ipo-screening-engine`; `main` remains `01ba66c`; PR #6 remains OPEN/UNMERGED at head `e05c0ef`.
- **HD Fire 7/100 is arithmetically reproducible but not a complete assessment:** A 2 + B 0 + C 3 + D 5 + E 0 + F 0 = 10; the only applied penalty is `receivable_days_up` −3; the pure-OFS cap gives the ceiling 60; available 27 / unknown 73 = 27% confidence; the 36 rows decompose into 20 UNKNOWN criteria + K1/K3/K5/K6 UNVERIFIED + 4 market blocks + 4 critical-data inputs + 4 UNKNOWN penalties (auditor_cfo_exit 3, unreconciled_metrics 2, regulatory_dependence 2, eom_caro 3 = 10 unresolved → floor 0). The HD Fire filing and store are Windows-only; no page-level claim is made.
- **Penalty attribution resolved (mandatory finding):** the applied −3 is `receivable_days_up`; `auditor_cfo_exit` is an unresolved/zero item and cannot be the applied −3. A **confirmed mapping defect** was found and corrected: `CanonicalInputBuilder` dropped the schema-permitted `governance.auditor_or_cfo_exit_2y` and `financials.adjusted_metrics_unreconciled`, so the auditor/CFO and unreconciled penalties were structurally UNKNOWN for every builder-based evaluation. The fix carries each key only when established; absent stays UNKNOWN; the golden input is unchanged. `tests/test_penalty_attribution.py` (5) and `tests/test_penalty_presentation.py` (3) pin the attribution and the UNKNOWN-vs-not-triggered presentation; `frontend` (2 new tests) removes the "0 points = cleared" ambiguity.
- **HD Fire fresh/OFS reconciled:** the pure-OFS structure and the explicit `fresh_issue = 0` are proved by the scorecard arithmetic (cap 60; seller/promoter criteria UNKNOWN requires OFS > 0). The filing-extracted `issue.ofs = 0` is **not** evidence of no OFS; it is the demonstrated NIL-OFS wrong-clause binding, now corrected (`tests/test_ofs_nil_binding.py`, 9 passed). Seller composition and promoter OFS remain UNKNOWN — never zero.
- **Jio 21 vs 29 resolved numerically:** with the filing-established fresh-only structure (OFS 0, fresh 3,021,300), the engine reproduces **29** (A 13, B 0, C 11, D 5, E 0, F 0; available 46/unknown 54). With the inverted structure (fresh 0, OFS > 0) it reproduces **21** exactly (A 13, B 0, **C 3**, D 5, E 0, F 0; available 46/unknown 54; pure-OFS cap 60). The eight-point bridge is entirely Module C: fresh_share 3→0 (−3), ofs_seller_type 2→0 (−2), promoter_ofs_pct 2→0 (−2), dilution 1→0 (−1); use_of_proceeds moves UNKNOWN→scored-zero (0), keeping availability invariant. The financial corrections are independently verified: p76 revenue (1,468,853/1,282,184/1,095,581, ₹ million) → CAGR **+15.7889%** (RHP p128 states 15.79%); p77 CFO 775,563/681,557/576,616 → **2.6206**; p132 disclosed ROCE **10.76%**. The 21 is an issue-term direction defect, not an extraction or scoring defect.
- **Confirmed Jio data-quality caveat:** the submitted fresh amount 3,021,300 is 10× the filing-unit-consistent ₹302,130 million (it is the ₹30,213 crore issue size expressed in lakh). It is score-inert (fresh/OFS ratio 100%) but must be re-based for any amount-based use. Peer valuation stays UNKNOWN (the p129–131 table is a third layout; no authoritative listed-years/as-of contract); net worth stays UNKNOWN (no total-equity subtotal); UoP stays UNKNOWN (GCP `[●]`, p116/p122); auditor stays UNKNOWN (examination report, not a canonical audit opinion).
- **Integrity findings requiring a governed decision (not changed here):** the builder/extractor favorable defaults (`litigation_bucket="clean"`, `sebi_ed_action_active=False`, `board_independent_majority=False`, `kmp_exits_2y=0`, `promoter_pledge_pct=0.0`, `promoter_lockin_in_place=True`, `large_holders_unlocked_early=False`, `discounted_allotments_18m_before_drhp=False`, `pre_ipo_placements=[]`). They clear K2, award board/pre-IPO/lock-in points and suppress the discounted penalty without evidence; the golden fixture relies on them, so correcting them changes the frozen golden result hash (`e84f8bc0…`) and requires a re-baseline decision. Also: the `sebi_ed_action_active=False` extractor emission carries the verbatim-looking quote "No active SEBI or ED regulatory proceedings" without a match and is not marked PROCESSING_SUMMARY.
- **Tests (executed):** baseline full backend **1111 passed** (1400.11 s, exit 0); post-change full backend **1129 passed**, 0 failed, 36 warnings (1490.59 s, exit 0) = baseline + 18 new focused tests; new focused 9 (NIL-OFS) + 5 (attribution) + 3 (presentation) + 1 (Jio bridge, 32.25 s); golden/core/extraction/peer batch **90 passed** (golden hash intact); Jio/fresh/bridge **20 passed**; R.K./phase-5b **14 passed**; frontend **89 passed** (87 + 2).
- **PR #6 / main:** preserved exactly (OPEN/UNMERGED, head `e05c0ef`; `main` `01ba66c`). No historical evaluation or scoring rule was changed.

### Publication amendment — actual remote state — 2026-10-19 (HD Fire/Jio reconciliation audit)

- **Implementation commit:** `345caf75690fc67ade687592b2be5bfe8ae408d4` on `arena/ae4d04e8-ipo-screening-engine` (remote-verified at push time). The docs-only publication amendment `568860ba2a5e06c4c5f9a8e61928f9b9e8b7a716` follows it; both are ancestors of the branch tip, which is re-verified in the session report after the final push. `git merge-base --is-ancestor` verified `e1df89b2af3bd432a70fe9716e266895ba6ff2e7`, `e05c0efbca1ecb3024e52da73a22e180ea171118` (PR #6 head) and `01ba66c12ca1195fd7acbd287c3e39a019808094` (`main`) are all in the published ancestry.
- **Tests at that commit (executed):** full backend **1129 passed**, 0 failed, 36 warnings (1490.59 s, exit 0); frontend **89 passed**; golden result `e84f8bc0…` preserved; the focused 90/20/14 batches recorded above all exited 0. The 18 additional backend tests are the new NIL-OFS, penalty-attribution, penalty-presentation and Jio-bridge regressions.
- **PR #6 (remote-verified):** state `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118` (unchanged). This session's branch is separate and is not PR #6; PR #6 was neither moved nor merged nor closed.
- **`main` (remote-verified):** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched.
- **CI:** no hosted workflows configured (verified previously; `gh workflow list` empty).
- **Remaining Windows-only acceptance:** the commands in the record §8 (read the HD Fire/Jio records, penalties, canonical issue block and raw peer rows; then re-upload at the published commit). No Windows artefact is claimed as inspected.

### HD Fire Protect — peer-extraction, schema-gate and NIL-OFS verification — 2026-10-20

- **Record:** `docs/investigation/HD-FIRE-JIO-EVIDENCE-REMEDIATION-2026-10-20.md` (Reports A–E). **Baseline:** `86d4950a07faa19bd1b0f05ee8e49a5d9560edf9`; `main` remains `01ba66c`; PR #6 remains OPEN/UNMERGED at `e05c0ef`.
- **Peer path verified end to end:** `SectionExtractor.extract_peers` is the sole peer producer and its only caller is `DocumentExtractor.extract_from_pdf`. Three header-anchored layouts are supported (accounting-ratios width 8; listed-peers closing-price width 9; Jio accounting-ratios width 7, new). Placeholders keep their column; rows are consumed only at the declared width; a short numeric row can never leak into the next peer name; a leading integer is a serial only when text follows; prose/totals are rejected; an unrecognised layout emits no peers.
- **Pre-evaluation gate:** `validate_peer_records` runs the same schema over `peers` at ingestion (`presentation/service.py`), names the peer and field, emits `validation/peer_contract/FAILED` with findings, and raises `IngestionValidationError` before any evaluation or persistence. Nothing is clamped or substituted. The evaluation-time `enforce_schema` remains the second line of defence.
- **Original failure:** the `peers/0/roe_pct 26957.28` / `peers/1 21700.34` signature is reproduced from source-backed reference layouts by both demonstrated mechanisms — positional mapping of a different layout and placeholder collapse — and rejected by the unchanged ROE bound. The HD Fire source row and Windows store are not present in this workspace, so the exact row attribution is recorded as a source-level limit, not claimed.
- **NIL-OFS and operator decision:** `_find_ofs_nil` accepts only an OFS-labelled NIL (same line, wrapped value, or the Jio cover shape) and rejects a NIL belonging to Fresh Issue / Pre-IPO / Promoter / reservation / total-issue clauses; `tests/test_ofs_nil_binding.py` 9 passed. The recorded manual OFS 71231 over the filing NIL 0 remains `MANUAL_ENTRY` / unverified, with the 409 conflict, explicit confirmation, and audit events preserved; no silent upgrade and no replacement of the operator decision.
- **Scorecard:** 7/100 is unchanged and arithmetically consistent (A 2 + B 0 + C 3 + D 5 + E 0 + F 0 = 10; −3 `receivable_days_up`; 10 − 3 = 7; available 27 + unknown 73 = 100; confidence 27 %; pure-OFS cap 60). `auditor_cfo_exit` remains UNKNOWN in the range. No formula, weight, cap or penalty rule was touched.

### Jio Platforms — evidence remediation (net worth, leverage, RPT/K6, valuation) — 2026-10-20

- **Historical record preserved:** the frozen pre-remediation canonical fixture (`fixtures/jio/`) reproduces the published 29/100 fresh-only and 21/100 inverted results (`tests/test_jio_score_bridge.py`, 1 passed). The new evaluation is a **separate** record: **37.0/100**, available 61 / unknown 39, range 27–76, `INSUFFICIENT_DATA`, Low confidence, no penalties or caps; A 17, B 1, C 11, D 8, E 0, F 0; K1 UNVERIFIED, K2–K4 CLEAR, K5 UNVERIFIED, K6 CLEAR.
- **Why 37, not 29:** evidence availability only. `leverage` UNKNOWN→4/4, `rpt` UNKNOWN→3/3, `pe_vs_peers` UNKNOWN→0/8 (8 points become available), `peg` 0→1 after the EPS unit correction. No scoring rule changed; `config/` and `schema/` diffs are empty.
- **Net worth:** restated balance sheet p.329 prints Equity Share Capital + Other Equity + separate NCI, no Total Equity subtotal. Note 38 (p.406) states Total Equity 3,359,769 / 3,050,474 / 2,782,864; total equity + NCI reconciles exactly to Total Assets − Total Liabilities. `_derive_net_worth_from_equity` now returns the owner components, never adds NCI, and fails closed on missing components, failed reconciliation, or NCI without totals. Tests pin the values and the grand-total guard. **Definition boundary:** the issuer's own net worth (p.130 note 1) excludes OCI — FY2026 3,340,134, 0.59 % lower — which changes no band or trigger; a schema-level definition decision is recommended, not silently applied.
- **K1:** auditor examination report pp.321–324 (Deloitte + Chaturvedi & Shah, UDINs) and Note 47.4 p.430 (no qualifications, no other legal/regulatory matters, no emphasis of matter) establish a clean audit context, but K1 stays **UNVERIFIED** because the governed parser requires positive opinion language and `going_concern_uncertainty` is not established; the absence of a going-concern paragraph is not treated as false.
- **Leverage:** gross borrowings 707,810 (not lease liabilities 138,876, deferred payment liabilities 1,045,137, payables, or total liabilities); net worth 3,359,769; D/E 0.2107; EBIT 461,327 / finance costs 86,534 = 5.3312 → **strong** under the unchanged bands. Consolidated scope only.
- **RPT/K6:** Note 36 pp.376–378; revenue from operations with related parties 63,299 / 56,717 / 52,878 (stated totals), matching the extracted rows. Share 4.3094 % (FY2026) vs 4.4235 % (FY2025) = **−0.1141 pp**; `rpt` 3/3, K6 CLEAR. The approved definition remains the change in share (not RPT ÷ revenue, not an inferred growth contribution). Anchor, 5-column header window, stop markers, relationship-column category reset, Sr. No. and trailing-number handling were corrected generically.
- **Valuation:** p.130 names exactly two peers — Bharti Airtel (P/E 40.71, RoNW 20.32 %) and Vodafone Idea (3.99, NM), both source-dated 2026-10-13, neither with a CMP. Issuer P/E 34.29 vs peer average 22.35 = +53.4 % → 0/8; PEG 2.17 → 1/4; second multiple and sector relative remain UNKNOWN for missing source data. No peer was invented and no rule was relaxed.
- **K5:** Note 37 p.405 quantifies claims at 15,021 (0.45 % of net worth), far below 50 %, but K5 remains UNVERIFIED: `_parse_contingent_liabilities` is unsafe (starts at p.250, first-"Total" heuristic) and `contingent_liabilities_unquantified` has no governed extractor. The quantified/unquantified contract is a policy decision; no parser was changed.
- **Post-issue EPS:** 300,527 × 10⁶ ÷ 9,209,030,830 = **32.63** (the builder previously assumed lakhs → 3.26). Lakh-based reference filings are unchanged (R.K. Fashion 4.05); golden hash `e84f8bc0…` preserved.

### Publication amendment — actual remote state — 2026-10-20 (Jio evidence remediation)

- **Implementation commit:** `f42b6ce1ba4c3058f1d5e52ef2b8d4cacd2d0ebc` on `arena/ae4d04e8-ipo-screening-engine`, pushed and remote-verified (`git ls-remote` returned the same SHA). The working tree is clean.
- **Tests at that commit (executed):** full backend **1139 passed**, 0 failed, 36 warnings, 1421.69 s (baseline 1129 + 10 new tests: net-worth derivation 5, Jio peer layout/short-row/no-default-date 4, live evidence remediation 1); focused batches **40 passed** (62.28 s), **52 passed** (243.41 s), **15 passed** (peer file), **14 passed** (financial mapping), **1 passed** (live remediation), golden trio **3 passed**; frontend **89 passed**; `node --check` and `compileall` clean; `config/` and `schema/` diffs empty; golden hash `e84f8bc0…` preserved.
- **PR #6 (remote-verified):** `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine`; neither moved nor merged. **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. **CI:** no hosted workflows configured.
- **Remaining Windows-only acceptance:** read the HD Fire source peer row and evaluation record from the Windows store and re-upload at `f42b6ce`; re-run the Jio Windows record with the published extractor. No Windows artefact is claimed as inspected.

### HD Fire Protect — peer/schema/NIL-OFS re-verification and scorecard audit — 2026-10-20 (amendment 2)

- **Record:** `docs/investigation/HD-FIRE-JIO-EVIDENCE-REMEDIATION-2026-10-20.md`, "Amendment 2" (Reports A–E restated). Baseline `f42b6ce`; `main` `01ba66c` untouched; PR #6 OPEN/UNMERGED at `e05c0ef`.
- **Peer path re-verified:** `SectionExtractor.extract_peers` (`sections.py:2145`) is the sole producer, called once by `DocumentExtractor.extract_from_pdf` (`extractor.py:30`). Three header-anchored layouts (`_PEER_SHAPES`, `sections.py:1964`, widths 8/9/7); placeholders (`[●]`, `NA`, `NM`, `-`) keep their column; a blank cell shortens the row and the row is rejected by width; prose/totals are never names; an unrecognised layout emits no peers; the valuation date is never defaulted.
- **Early gate:** `validate_peer_records` (`schema_validation.py:91`) is called at `presentation/service.py:1426`, emits `validation/peer_contract/FAILED` with the peer and field named, and raises `IngestionValidationError` → HTTP 400 before term resolution, evaluation or persistence. The rejection test now also asserts `eval_store.list_evaluations() == []`.
- **Tests (executed):** `test_peer_row_mapping_and_bounds.py` **17 passed** (1.44 s; 15 prior + 2 new: blank/`NA`/`NM` column alignment; valid ingestion → `pe_vs_peers` SCORED 0.0). `test_ofs_nil_binding.py` 9 passed inside a **79 passed** regression batch (203.64 s). `test_step5_auditor_and_manual_terms.py` + auditor suite **28 passed** (153.09 s), including the real Vishal three-term `AWAITING_ISSUE_TERMS` flow and the 409 → confirm OFS path.
- **Original failure:** unchanged reproduction from source-backed layouts (positional mapping; placeholder collapse) and unchanged `roe_pct` bound; the HD Fire row and Windows store remain inaccessible — source-level limit recorded.
- **Scorecard:** 7/100 unchanged (A 2 + B 0 + C 3 + D 5 + E 0 + F 0 = 10; `receivable_days_up` −3; available 27 + unknown 73; confidence 27 %; `INSUFFICIENT_DATA` = the `critical_data` branch of `scoring.py:509–518`, not a score band; pure-OFS cap 60 not binding; `auditor_cfo_exit` UNKNOWN in range). No formula, weight, threshold, cap or penalty changed.
- **Disposition:** peer mapping/schema gate/audit evidence/NIL-OFS/manual provenance **FIXED AND VERIFIED**; HD Fire source row **SOURCE-LEVEL VERIFICATION PENDING**; 7/100 **NOT CHANGED**.

### Jio Platforms — auditor opinion, K5 extraction, Module E and valuation boundary — 2026-10-20 (amendment 2)

- **Final record:** `JIO-PLATFORMS-LIMITED-20261019-183045Z-final-7857589a`, **37.0/100** (27–76), available 61 / unknown 39, Low, `INSUFFICIENT_DATA`; A 17, B 1, C 11, D 8, E 0, F 0; K1 UNVERIFIED [`going_concern_uncertainty`], K2–K4 CLEAR, K5 UNVERIFIED [`contingent_liab_unquantified`], K6 CLEAR; no penalties (10 unresolved penalty points widen the range); result hash `7857589a…`, input snapshot `59870d9a…`, peer snapshot `61f5c913…`, config 1.5.0.
- **Same 37.0 as `…181727Z-final-0b60daf7`:** the changes resolved availability only; no scored criterion changed. K1/K5 each retain one unknown leaf; Module E and D `auditor` remain unknown.
- **K1:** auditor opinion is now established — examination report pp. 321–324 (Deloitte `117366W/W-100018`, Chaturvedi & Shah `101720W/W-100355`, 7 Oct 2026; UDINs `26100459QBZXUZ8355` / `26122179ZKMPTF3256`), conclusion p. 324 "…no modification in the underlying audit reports…" → `unqualified`. `going_concern_uncertainty` stays `None` (no going-concern paragraph; Note 47.4 p. 430 no EOM/qualification; whole-PDF "going concern" only at p. 253), so **K1 stays UNVERIFIED**. Clearing it needs a governed negative-confirmation rule; not applied.
- **K5:** `_extract_contingent_liabilities` (`financial_tables.py:575`) anchors Note 37, reads the header 30 lines above the claims row, and takes the latest 31-March column → **15,021** (p. 405), 0.45 % of net worth; Note 38 and the June-2026 14,688 are excluded. `contingent_liabilities_unquantified` is `None` (zero "unquantif*" hits in 591 pages) → K5 UNVERIFIED on that leaf only. `tests/test_contingent_liabilities_extraction.py` **8 passed** (21.42 s), including the live pin.
- **Net worth / leverage / RPT:** unchanged and reconciled — NW 2,782,864 / 3,050,474 / 3,359,769 (NCI excluded, reconcile-only); borrowings 707,810 (leases 138,876 and deferred payment 1,045,137 excluded) → D/E 0.2107, EBIT 461,327 / finance 86,534 = 5.3312 → strong; Note 36 revenue rows sum to the note's totals 63,299 / 56,717 / 52,878 → share 4.3094 % vs 4.4235 % = −0.1141 pp (approved definition), `rpt` 3/3, K6 CLEAR. Contribution measure 6,582 / 186,669 = 3.53 % also far below 40, so K6 CLEAR is robust. Counterparty text of a wrapped category's first row is merged with the label tail (evidence-only; not used by the metric).
- **Module E (0/15, correctly UNKNOWN):** no designated forward mobile-connectivity CAGR (₹2.9 tn FY26 → ₹5.2 tn FY31 with no stated CAGR; adjacent segment CAGRs belong to other markets); `moat`/`visibility` are Tier-4 analyst inputs with no RHP field; no top-5 customer/supplier disclosure. No code or score change.
- **Valuation:** the RHP price band is `₹[●]`–`₹[●]` (p. 129, "to be updated"); the band used (₹1,065–1,119) is operator `MANUAL_ENTRY`/`SRC-MANUAL-ENTRY`, **NOT source-verified**, and `pe_vs_peers` 0/8 depends on it. Issuer P/E 1,119 / 32.63 = 34.29 vs peer median 22.35 = +53.4 % → 0/8 (on the filing's diluted EPS 33.59 the premium is +49.0 %, band 1/8; recorded, not applied). Peers are exactly the two the filing designates (Bharti 40.71 / 20.32 % / NAV 244.60; Vodafone 3.99 / NM / −3.30), both VALID. `second_multiple` UNKNOWN: the peer table has no EV/EBITDA and no P/B (no closing-price value); not derived. `sector_ipo_relative` UNKNOWN: no recent same-sector IPOs. The UNKNOWN message "no VALID peer multiple is available" is imprecise but frozen in the golden fixture; documented, not changed.
- **Tests:** full backend suite **1158 passed**, 0 failed, 38 warnings (1154.83 s; baseline 1139 + 19 new tests: auditor 9, contingent liabilities 8, peer 2); auditor suite 9 passed (19.97 s); CL suite 8 passed (21.42 s); step5+auditor 28 passed; 79-test regression batch passed; peer file 17 passed; golden trio 24 passed (`e84f8bc0…` intact); frontend 89 passed; compileall/`node --check` clean; `config/`, `schema/`, `fixtures/` diffs empty.

### Publication amendment — actual remote state — 2026-10-20 (auditor / K5 evidence remediation)

- **Implementation commit:** `af54cfc823a58b2c8c477f7f6264ac5eeb59f376` on `arena/ae4d04e8-ipo-screening-engine`, pushed and remote-verified (`git ls-remote` returned the same SHA). 9 files changed, 1061 insertions, 62 deletions; `config/`, `schema/` and `fixtures/` untouched.
- **Tests at that commit (executed):** full backend **1158 passed**, 0 failed, 38 warnings, 1154.83 s (baseline 1139 at `f42b6ce` + 19 new tests); frontend **89 passed**; golden trio **24 passed** with result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` intact; `compileall` and `node --check` clean.
- **Jio final record:** `JIO-PLATFORMS-LIMITED-20261019-183045Z-final-7857589a`, 37.0/100 (27–76), available 61/unknown 39, result hash `7857589a…`; K1 UNVERIFIED on `going_concern_uncertainty` only, K5 UNVERIFIED on `contingent_liab_unquantified` only, K2–K4/K6 CLEAR.
- **PR #6 (remote-verified):** `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine`; neither moved nor merged. **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. **Ancestry:** both `01ba66c` and `e05c0ef` are ancestors of the pushed tip.
- **CI:** no hosted workflows configured.
- **Remaining Windows-only acceptance:** read the HD Fire source peer row and both evaluation records from the Windows store and re-upload at `af54cfc`; re-run the Jio Windows record with the published extractor. No Windows artefact is claimed as inspected.

### HD Fire Protect — RHP evidence reconciliation and engine input validation — 2026-10-20

- **Record:** `docs/investigation/HD-FIRE-RHP-EVIDENCE-RECONCILIATION-2026-10-20.md` (Reports A–I). **Baseline:** `b8723cb` (remote-verified equal); `main` remains `01ba66c`; PR #6 remains OPEN/UNMERGED at `e05c0ef`. No engine, `config/`, `schema/` or fixture change.
- **Primary source absent — established, not assumed:** `find . -iname "*hd*fire*"` returns only four investigation `.md` files; `find . -name "*.pdf"` returns Jio, R.K. Fashion, Vishal, Moneyview and fixtures only; `evaluations/` does not exist and no `evaluation.json` carries `551a7eab…`; all **17** branches listed by `gh api repos/.../branches` were tree-searched per branch (`git/trees/<branch>?recursive=1`); the only HD Fire paths returned are investigation `.md` files (four in this branch, one of them in `arena/d15866b5`), and no branch contains an HD Fire PDF. Sandbox egress returns HTTP 000 to `nseindia.com`, `bseindia.com`, `sebi.gov.in`, the issuer and a control host, so no live retrieval was attempted or claimed. **Consequence:** every HD Fire value below is graded by arithmetic and input-contract consistency only; no page, note number or verbatim excerpt from an HD Fire filing is cited anywhere, and the record's score/penalty/hash are *documented* values that cannot be independently recomputed here.
- **Score arithmetic re-derived:** A 2 + B 0 + C 3 + D 5 + E 0 + F 0 = 10; one applied penalty `receivable_days_up` −3 → 7; available 27 + unknown 73 = 100 (27 %, Low); floor 0 requires ≥7 unresolved penalty points (the four UNKNOWN penalties give 10); ceiling 60 requires the pure-OFS cap, i.e. `fresh_issue == 0` **and** `ofs > 0` in the evaluated snapshot; `revenue_cagr` 2/6 is exactly the configured band for the proposed 14.54 % CAGR. **7/100 unchanged and arithmetically consistent.**
- **Dispositions, per field row in §B (44 rows):** **10 verified** (revenue CAGR 14.54 % as an engine input; EBITDA margin 30.75 %; issue P/E 40.69× (271 ÷ 6.66, 40.66× on the unrounded 6.665); implied market cap ₹4,748.70 cr; issuer EV/EBITDA 30.67×; P/B 11.88×; NAV-based second multiple; aggregate OFS proceeds ₹712.3100 cr = 26,284,500 × ₹271; 100 %-OFS classification at record level; no fresh issue / proceeds use), **7 contradicted**, **26 unresolved**, **1 not applicable** (arm's-length assertion — no engine field consumes it). Seller-level proceeds and the ₹712.13 cr aggregator figure are not scorable at all (no `amount` field in `$defs.seller`; secondary source) and change no disposition.
- **Contradictions:** PAT margin 23.12 % is a total-income ratio — `_margins` divides by revenue (`derived.py:274`), which gives 23.87 % (23.12 % would need a ₹505.15 cr denominator); CFO/PAT 0.79× is a one-year ratio while `cfo_pat_cumulative` is ΣCFO/ΣPAT over the window (`derived.py:423`); Harish Dharamshi 8,983,700 × ₹271 = ₹243.4583 cr vs claimed ₹243.16 cr (−₹0.2983 cr) and Kusum 17,300,800 × ₹271 = ₹468.8517 cr vs ₹469.15 cr (+₹0.2983 cr) — **the two errors cancel exactly**, so the claimed ₹712.31 cr total agrees only by construction; NAV/share ₹22.82 × 175,228,782 implies net worth **₹399.87 cr**, which contradicts "net worth > ₹1,000 cr" (the ₹375.93 cr figure is plausibly FY2025, not `net_worth_latest`); ROCE 40.33 % implies EBIT ₹161.3 cr **>** EBITDA ₹150.5 cr, which is internally inconsistent unless the RHP's ROCE numerator includes other income; going-concern CLEAR and "K5 can be cleared" are not established by the cited facts.
- **K1/K5:** an unmodified opinion is not a negative going-concern confirmation (decision **D-1**), and K1's `any` also needs `net_worth_latest`. For K5, bank guarantees ~₹58.50 cr + EPCG ~₹31.43 cr = ₹89.93 cr = 22.49 % of the ₹399.87 cr net worth — a BG is **not** the claims row the extractor reads (`financial_tables.py:557–673` takes the claims/disputed row only), and two disclosed lines cannot establish that *all* exposures are quantified; the numerator definition is decision **D-2** (the schema's `financials.contingent_liabilities` has no description).
- **Engine defect 1 — promoter pre/post holding fallback (confirmed on committed evidence):** `extract_capital_structure` returns **100 %/100 %** whenever the shareholding block carries the combined `Total (A)+(B)+(C)` row or both category totals (the ICDR shape). On the committed Jio RHP p. 107 it returns 100/100 where the filing states **66.43 %** pre-issue (public 33.57 %) and prints `[●]` post-issue. Causes: `re.search(r'Total\s*\(\s*A\s*\)')` prefix match at `sections.py:681` and `:717`, the A+B sum at `:693`, the post-append window at `:717–733`. This is HD Fire's `promoter_post_pct = 100 %` → D 4/4 + K4 CLEAR in a 100 % OFS by two individuals, where the arithmetic gives **85.0 %** — structurally impossible. Not fixed: the fail-closed correction changes a scored canonical input (decision **D-3**).
- **Engine defect 2 — auditor tenure / repeated-EOM favourable defaults (confirmed by probe):** when an auditor *name* is found, `extract_governance` emits `auditor_changed_3y = False` as a **constant** (assigned before the tenure loop and re-assigned inside both branches, `sections.py:1420–1450`) and `repeated_eom = False` whenever a name is matched (`sections.py:1464–1475`), each with a synthesised sentence (`"Auditor <name> unchanged across audited fiscal years"`, `"No repeated Emphasis of Matter noted"`) that is not in the filing — the second is not even marked `quote_is_processing`. `auditor_reputed` is a hard-coded 11-firm lookup (`sections.py:1404–1417`). Together they resolve `_auditor_bucket` (`derived.py:1428`) to **`clean_reputed` 2/2** on an unqualified opinion alone. Probe: opinion + `audited by Deloitte Haskins & Sells LLP` with **no** tenure or EOM text → `changed_3y=False`, `reputed=True`, `repeated_eom=False`. HD Fire's D `auditor` is UNKNOWN, so these points were **not** awarded there; the defect fires wherever the shape matches. Not fixed (decision **D-4**).
- **Decisions named, not taken:** **D-1** going-concern negative-confirmation rule; **D-2** K5 contingent-liability numerator definition; **D-3** promoter-holding fix — (a) guard only or (b) parse the promoter row removes 4 earned Module D points from the Jio record, (c) diluting the pre-issue holding by the issue (66.43 % → 64.48 % for Jio, 85.0 % for HD Fire) preserves every recorded score but is itself a semantic change; **D-4** auditor tenure/EOM — (a) emit `None` unless the text is matched, (b) record the constants as governed assumptions.
- **Tests (executed this pass):** `tests/test_promoter_holding_extraction.py` **1 passed, 3 xfailed** (strict, 4.02 s) — the passing one is the positive control (`Total (A)` alone → 66.43 %/65.0); `tests/test_auditor_tenure_defaults.py` **2 passed, 2 xfailed** (strict, 0.04 s); the 10-file targeted battery (`promoter_holding_extraction`, `rk_fashion`, `fixture_fallback_isolation`, `extraction_phase5b`, `enrichment_engine`, `acceptance_matrix`, `jio_evidence_remediation`, `financial_statement_column_mapping`, `ofs_nil_binding`, `peer_row_mapping_and_bounds`) **134 passed, 3 xfailed** (232.80 s); full backend **1161 passed, 5 xfailed, 38 warnings** (1618.22 s) — baseline 1158 passed plus the 3 new passing tests (1 promoter positive control, 2 auditor controls) and the 5 strict-xfail pins; both new files re-executed on the final tree (**3 passed, 5 xfailed**, 3.99 s), since only docstrings/comments changed after collection.
- **Non-changes:** no scoring weight, threshold, formula, cap, penalty, knockout semantic, confidence rule, missing-value rule, peer-eligibility rule, golden fixture, historical record or evaluation contract was touched; `config/`, `schema/` and `fixtures/` diffs are empty; golden hash `e84f8bc0…` intact.

### Jio Platforms — promoter-holding defect exposure (analysis only) — 2026-10-20

- **No Jio record was changed, re-run or rewritten.** `JIO-PLATFORMS-LIMITED-20261019-183045Z-final-7857589a` remains **37.0/100** (27–76), available 61 / unknown 39, Low, `INSUFFICIENT_DATA`; K1 UNVERIFIED [`going_concern_uncertainty`], K5 UNVERIFIED [`contingent_liab_unquantified`], K2–K4/K6 CLEAR.
- **Live re-extraction** from the committed RHP (`evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`) again returns `promoter_pre_pct = 100.0` / `promoter_post_pct = 100.0` against the filing's 66.43 % pre-issue / 33.57 % public. The same run emits only `governance.auditor_opinion` — no auditor name is matched, so defect 2 (§HD Fire above) does not fire on this filing.
- **Impact if D-3 is taken:** (a) or (b) turns D `promoter_post_holding` 4/4 into UNKNOWN → the record loses **4 earned points** and 4 available points; (c) yields 66.43 % × 8,939,030,830 / 9,209,030,830 = **64.48 %** post-issue, which changes no band and preserves the recorded 37.0. Nothing is applied until the decision is made.

### Publication amendment — actual remote state — 2026-10-20 (HD Fire RHP evidence reconciliation)

- **Implementation commit:** `bdab685a05a96a7531dc9a3f5b218b8c45ebfbfb` on `arena/ae4d04e8-ipo-screening-engine`, pushed and remote-verified (`git ls-remote` returned the same SHA). 4 files changed, 918 insertions, 0 deletions: this tracker section, `docs/investigation/HD-FIRE-RHP-EVIDENCE-RECONCILIATION-2026-10-20.md`, `tests/test_promoter_holding_extraction.py`, `tests/test_auditor_tenure_defaults.py`. `config/`, `schema/`, `fixtures/` and engine diffs empty.
- **Tests at that commit (executed):** full backend **1161 passed, 5 xfailed**, 38 warnings, 1618.22 s (baseline 1158 passed + 3 new passing tests and 5 strict-xfail pins); both new files re-executed on the final tree **3 passed, 5 xfailed** (3.99 s); targeted 10-file battery **134 passed, 3 xfailed** (232.80 s). Golden hash `e84f8bc0…` preserved; no golden-fixture change.
- **PR #6 (remote-verified):** `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine`; neither moved nor merged. **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. **Ancestry:** both `01ba66c` and `e05c0ef` are ancestors of the pushed tip.
- **Remote source check:** 17 branches enumerated; every tree searched; no HD Fire RHP/PDF and no evaluation record in any branch. No live NSE/BSE/SEBI retrieval was possible (egress HTTP 000) and none is claimed.
- **CI:** no hosted workflows configured.
- **Remaining Windows-only acceptance:** read the HD Fire RHP, the `…551a7eab` evaluation record, its penalty rows and canonical issue block from the Windows store, and re-run at `bdab685`. No Windows artefact is claimed as inspected.
- **Decisions still open:** D-1 (going concern), D-2 (K5 numerator), D-3 (promoter-holding fix), D-4 (auditor tenure/EOM defaults). All four change a scored input; none was applied.

### HD Fire / Jio — decision resolution and defect remediation readiness — 2026-10-20

- **Record:** `docs/investigation/HD-FIRE-JIO-DECISION-RESOLUTION-2026-10-20.md` (§0 state, §1 D-1, §2 D-2, §3 D-3, §4 D-4, §5 cross-impact, §6 decision records, §7 tests, §8 publication). **Baseline:** `ebd177c` (remote-verified at pass start); `main` `01ba66c`; PR #6 OPEN/UNMERGED at `e05c0ef`. **No HD Fire primary source** — 17 branches tree-searched, no PDF, egress HTTP 000; every HD Fire value below remains a documented claim.
- **D-1 — going-concern polarity (FIXED, tested).** The raw phrase regex matched "there is **no** material uncertainty related to going concern" and emitted `going_concern_uncertainty = True`, i.e. K1 TRIGGERED on the opposite of the fact. Every scan now goes through `_going_concern_uncertainty_match()` (the only consumer of the regex — verified by `grep`), which rejects a match when the 120-char sentence prefix or the sentence tail is a negation (`no/not/none/without`, `did not identify`, `no longer`, `no such`). Emission stays **positive-only**; a negation or absence yields no field, UNKNOWN, and no CLEAR. Measured: flag `True` ⇒ K1 TRIGGERED/AVOID, flag `None` ⇒ UNVERIFIED/INSUFFICIENT_DATA, **score unchanged**. Jio stays UNVERIFIED (unqualified opinion, no going-concern paragraph; whole-PDF hit only p. 253 measurement basis); HD Fire stays UNVERIFIED (no RHP).
- **D-2 — K5 numerator (OPEN decision; one flag-polarity fix implemented).** Contract unchanged: `contingent liabilities / net worth × 100 > 50` **or** `contingent_liabilities_unquantified`. The extractor reads **only** the claims/disputed row (latest 31-March column). Jio Note 37 (p. 405, ₹ million): claims 14,688 / 14,151 / **15,021** / 30,183 / 27,924; capital-account commitments 90,389 / 65,624 / 26,198 / 51,272 / 58,284. Claims 15,021 / NW 3,359,769 = **0.45 %**; with the same 31-March-2026 commitment (26,198) 41,219 → **1.23 %** *(corrected 2026-10-20: the earlier 105,410 / 3.14 % mixed the 30 June 2026 interim commitment with the 31 March 2026 claims column)*; both far below 50, so the open question is definitional, not outcome-changing for Jio. Coverage probe: a note with guarantees/EPCG rows and no claims label returns **None**; a note with claims **plus** guarantees returns the claims row only — the extractor cannot represent a disclosed total. HD Fire claims (BG ₹58.50 cr secured on FDs, EPCG ₹31.43 cr unfulfilled export obligations) are **unverified secondary values**, category-mismatched to the claims row; if both were the whole population 89.93 / 399.87 = **22.49 %**. Two quantified lines cannot establish that all exposures are quantified ⇒ the flag cannot be set `False`. **Implemented:** the unquantified regex is polarity-blind ("there are **no** unquantified claims" set the flag true and triggered K5); the flag is now suppressed when the preceding 80 chars, cut at a sentence boundary, contain `no|not|nil|none|without` — a negated statement yields `None` (UNKNOWN), **never** `False`. Numerator, threshold and criterion meaning untouched. **Open:** authorize claims-only (a), disclosed total of section (I) with commitments excluded (b, recommended), or a defined subset incl. commitments (c).
- **D-3 — promoter holding (FIXED, guard only).** `Total\s*\(\s*A\s*\)` also matched the ICDR summary row `Total (A)+(B)+(C)` (the whole company), and the fallback added `Total (B)` ⇒ Jio **100/100** where p. 107 states 66.43 % promoter / 33.57 % public. Fix: `_TOTAL_A_LABEL = total\s*\(\s*a\s*\)(?!\s*[+(])`. Row assembly and the A+B arithmetic unchanged. Live: Jio **None/None** (was 100/100), R.K. Fashion **99.67/72.25**, Vishal **73.42/37.51** — both unchanged. A first attempt that truncated row assembly at the next `Total (` row regressed RK to 99.61/72.22 (read the Reg-31 `Total (A)` and dropped `Total (B)` 0.06) and was reverted; that regression is the evidence for the narrow guard. **Impact if Jio were re-scored:** D `promoter_post_holding` 4/4 → UNKNOWN, record loses **4 earned + 4 available** points ⇒ **33.0/100**, available 57, unknown 43 (arithmetic; no record re-run). **Open:** the `Total (A) + Total (B)` definition (pinned as a strict xfail) and **D-3b**: the post fallback does not verify it is reading a post-issue table, so a pre-issue-only table can still yield 100 % post — HD Fire's 85.0 % is not reachable without the RHP.
- **D-4 — auditor tenure / repeated-EOM defaults (FIXED, tested).** `auditor_changed_3y` was a **constant `False`** (assigned before the loop and in both branches) with the synthesised quote "Auditor <name> unchanged across audited fiscal years"; `repeated_eom = False` was emitted on any matched name with "No repeated Emphasis of Matter noted" — text in neither filing. Together they produced `clean_reputed` 2/2 from an unqualified opinion alone. Now: tenure `False` only on the positive three-year sentence (full verbatim sentence, page actually matched); repeated EOM `False` only on an explicit negative EOM statement with no positive EOM; otherwise the field is absent ⇒ UNKNOWN. Measured: known tenure ⇒ `clean_reputed` 2/2; nulls ⇒ UNKNOWN (Δ **2 points** on filings where the constant applied); R.K. Fashion's stale `auditor_changed_3y is False` expectation updated to `None` (its auditor criterion was already UNKNOWN ⇒ **no score change**); Jio unaffected (no auditor name matched ⇒ reputed unknown). Capability gap recorded: there is no `True` path for repeated EOM.
- **Cross-impact:** D-1 and the D-2 flag fix are **verdict-integrity** fixes (false AVOID prevented, 0 points); D-3 is a **−4-point** input correction on Jio if re-scored; D-4 is a **−2-point** input correction where the constant applied. No weight, threshold, formula, cap, penalty, knockout semantic, confidence rule or missing-value rule changed; `config/`, `schema/` and `fixtures/` diffs are empty; golden hash `e84f8bc0…` untouched; no historical evaluation edited, re-run or re-hashed.
- **Tests (executed this pass):** full backend **1179 passed, 1 xfailed, 38 warnings** (1542.57 s; baseline at `ebd177c` 1161 passed, 5 xfailed — delta exactly the 18 new passing tests: 8 going-concern polarity, 1 negated unquantified flag, 7 auditor controls replacing 2 strict xfails, 2 promoter controls replacing 2 strict xfails; the remaining xfail is the open D-3 A+B definition). `test_contingent_liabilities_extraction.py` **9 passed** (29.49 s, 1 new); the 10-file focused battery (promoter, auditor tenure, GC negative disclosure, contingent liabilities, auditor evidence, RK reconciliation, fixture fallback, Jio remediation, overlays/knockouts, core semantics) **106 passed, 1 xfailed** (216.37 s); `test_promoter_holding_extraction.py` **4** (3 pass + 1 strict xfail); `test_auditor_tenure_defaults.py` **9**; `test_going_concern_negative_disclosure.py` **8**.
- **Decisions still open:** D-1 negative-confirmation rule; D-2 numerator definition; D-3 A+B definition and D-3b post-table scope; D-4 repeated-EOM detection. HD Fire's 7/100 remains unchanged and arithmetically consistent; its input set is still not independently verifiable here.

#### Publication — 2026-10-20 (decision resolution / D-1–D-4)

- **Implementation commit:** `e2ce2c22b638c2eef7be315d2e9f019904baf8ff` on `arena/ae4d04e8-ipo-screening-engine`, pushed and remote-verified (`git ls-remote` returned the same SHA). 9 files, 953 insertions, 139 deletions: `sections.py`, `financial_tables.py`, the three extraction test files, `test_contingent_liabilities_extraction.py`, `test_rk_fashion_reconciliation.py`, `docs/investigation/HD-FIRE-JIO-DECISION-RESOLUTION-2026-10-20.md`, this tracker.
- **Tests at that commit (executed):** full backend **1179 passed, 1 xfailed**, 38 warnings, 1542.57 s (baseline `ebd177c` 1161 passed, 5 xfailed); focused 10-file battery **106 passed, 1 xfailed** (216.37 s); contingent-liability file **9 passed** (29.49 s); the four touched test files re-executed on the final tree **29 passed, 1 xfailed** (32.91 s); golden hash `e84f8bc0…` intact.
- **PR #6 (remote-verified):** `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @ `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine`; neither moved nor merged. **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. **CI:** no hosted workflows configured.
- **Non-changes:** no weight, threshold, formula, cap, penalty, knockout semantic, confidence rule, missing-value rule, peer-eligibility rule, golden fixture, historical record or result-hash rule touched; `config/`, `schema/`, `fixtures/` diffs empty. The Jio record `…7857589a` (37.0) is unmodified; 33.0 is only the arithmetic effect of D-3(a) on a hypothetical re-run.

### HD Fire / Jio — D-1 … D-4 approved decisions and authorised remediation — 2026-10-20

- **Record:** `docs/investigation/HD-FIRE-JIO-DECISION-GOVERNANCE-2026-10-20.md` (§0 state, §1 D-1, §2 D-2, §3 D-3, §4 D-4, §5 cross-decision validation, §6 protected artifacts, §9 tests, §10 publication). **Decision records:** `handoff/decisions/A19-k1-going-concern-positive-evidence.md` (D-1), `A20-k5-contingent-liability-numerator.md` (D-2), `A21-promoter-post-issue-holding.md` (D-3), `A22-auditor-tenure-and-repeated-eom.md` (D-4) — one record per decision, GOV-001 format. **Baseline:** `7754f9b` (remote-verified at pass start); `main` `01ba66c`; PR #6 OPEN/UNMERGED at `e05c0ef`. **No HD Fire primary source** — egress returns HTTP 000 and no branch contains an HD Fire PDF, so every HD Fire value below remains a documented, unverified claim.
- **D-1 — going concern, K1 (verified; no new rule).** `_GOING_CONCERN_UNCERTAINTY` was polarity-blind: "there is **no** material uncertainty related to going concern" set the flag `True` and triggered K1 on the opposite of the fact. The flag is now emitted only by `_going_concern_uncertainty_match()`, which rejects a phrase whose 120-char sentence prefix or sentence tail is a negation (`no/not/none/without`, `did not identify`, `no longer`, `no such`); "No doubt, there is a material uncertainty…" still fires. Emission stays **positive-only**: a negation, absence or an unmodified opinion yields no field ⇒ UNKNOWN, never CLEAR. **No negative-confirmation rule was added** (deferred with prerequisites in A19). Measured: `True` ⇒ K1 TRIGGERED / AVOID; `None` ⇒ UNVERIFIED / INSUFFICIENT_DATA; **score unchanged**. Jio: unqualified, whole-PDF "going concern" hit only p. 253 (a measurement-basis phrase) ⇒ UNKNOWN.
- **D-2 — K5 contingent-liability numerator (implemented per A20; definition now explicit).** `financials.contingent_liabilities` is the **disclosed total of the contingent-liability section**, **capital commitments excluded** (A20). The reader is heading-anchored and section-bounded; period headers are not rows; the latest 31-March column is used; a unique `Total` row wins and its constituents are **not** added (no double count); without a total the section rows are summed; commitment-labelled rows and the `(II) Commitments` subsection are excluded; width mismatch, more than one total, or an unquantified exposure without a total ⇒ `None`. The 50 % threshold and the `when.any` structure are untouched. Jio Note 37 (p. 405): claims/disputed liabilities **15,021** ⇒ **0.45 %** of net worth 3,359,769 (commitments 26,198 excluded; same-column total 41,219 = 1.23 % if wrongly included; the 3.14 % reported in the previous pass mixed period columns); both far below 50 %. HD Fire's BG ₹58.50 cr + EPCG ₹31.43 cr (unverified) = 22.49 % of the documented ₹399.87 cr net worth — not used to clear or trigger anything. The unquantified flag remains positive-only and is never coerced to `False`.
- **D-3 — promoter pre/post holding (implemented per A21).** `_TOTAL_A_LABEL` stops the ICDR summary row `Total (A)+(B)+(C)` from being read as the promoter total; the `Total (B)` category is read from the nearest heading so a **public** total is never added to the promoter total while a **promoter-group** total is. Rows are read one line at a time (a wrapped numeric continuation is allowed; the next three lines are not), which fixes the 35.0 / 0.06 mis-fold. **Live:** Jio **None/None** (was 100/100), R.K. Fashion **99.67 / 72.25** (unchanged), Vishal pre **73.42** / post **None** (was 37.51 — a pre-issue figure read as post). **D-3b is resolved in the same change:** a post value now requires an explicit post-issue marker (`Post-Offer` / `Post-Issue` / `after the Offer` / `on Allotment`) in the preceding 120 lines **and** a numeric percentage in more than one column; a pre-issue-only table (`[●]` post cells) yields UNKNOWN. The former strict-xfail pin for the public-total defect now passes, so no xfail remains. Residual open items are a post-only table (one numeric column) and a table with no category headings, both UNKNOWN by design; HD Fire's claimed 85.0 % is not reproducible without the RHP.
- **D-4 — auditor tenure / repeated EOM (verified; no new rule).** `auditor_changed_3y` was a **constant `False`** with a synthesised sentence ("Auditor <name> unchanged across audited fiscal years"); `repeated_eom = False` was emitted on any matched auditor name with "No repeated Emphasis of Matter noted". Both are now evidence-or-UNKNOWN: tenure `False` only on the positive three-year sentence (verbatim sentence, page actually matched); repeated EOM `False` only on an explicit negative EOM statement with no positive EOM; otherwise the field is absent ⇒ the auditor criterion is UNKNOWN and cannot award points. Measured: unqualified + reputed + `changed=False` ⇒ 18.0 (available 25); `None` ⇒ 16.0 (available 23). R.K. Fashion's stale `auditor_changed_3y is False` expectation is `None`; its auditor criterion was already UNKNOWN ⇒ no score change. **Capability gap:** there is no `True` path for repeated EOM; a genuine repeat shows UNKNOWN.
- **Cross-decision validation (10 checks, executed):** missing evidence is never turned into `False`/CLEAR; explicit negatives are distinguished from absent evidence; no synthesised quotation remains (auditor quotes are verbatim, promoter processing text is flagged `quote_is_processing=True`, the K5 quote is the filer's row-label wording); category totals are not used as entity/promoter totals; no K5 aggregate+constituent double count; D-1/D-4 safeguards intact; **no scoring formula, weight, threshold, knockout, confidence or missing-value rule changed**; `config/`, `schema/`, `fixtures/` and the golden hash `e84f8bc0…` unchanged; no historical evaluation re-run or rewritten.
- **Tests (executed this pass):** full backend **1192 passed, 0 failed, 0 xfailed**, 38 warnings, 1566.58 s (baseline `7754f9b`: 1179 passed, 1 xfailed, 1542.57 s; delta +12 collected tests and the strict-xfail pin converted to a passing test); `test_contingent_liabilities_extraction.py` **17 passed** (29.50 s); `test_promoter_holding_extraction.py` **8 passed** (7.32 s); six decision-related files **55 passed** (130.09 s); 11-file regression battery **153 passed** (344.58 s); `test_going_concern_negative_disclosure.py` **8 passed**; `test_auditor_tenure_defaults.py` and `test_auditor_evidence_section.py` **9 + 9 passed**; `compileall` clean on both edited modules.
- **Status:** D-1 … D-4 are recorded and their authorised remediation is applied; the D-1 negative-confirmation rule, D-2 coverage items (long notes, integer-only cells, schema description, collateral netting), D-3 post-only tables/HD Fire's 85.0 % and the D-4 cross-year comparison remain **deferred and open**. HD Fire source-level acceptance is outstanding.

#### Publication — 2026-10-20 (D-1 … D-4 decisions and remediation)

- **Implementation commit:** `2ec607cd6195bdd631f6433f40883c1d68c5212d` on `arena/ae4d04e8-ipo-screening-engine`, pushed (`7754f9b..2ec607c`) and remote-verified (`git ls-remote` returned the same SHA). 11 files, 1224 insertions, 100 deletions: `extraction/financial_tables.py`, `extraction/sections.py`, `tests/test_contingent_liabilities_extraction.py`, `tests/test_promoter_holding_extraction.py`, `handoff/decisions/A19`…`A22`, `docs/investigation/HD-FIRE-JIO-DECISION-GOVERNANCE-2026-10-20.md`, the inline period-mix correction in `docs/investigation/HD-FIRE-JIO-DECISION-RESOLUTION-2026-10-20.md`, and this tracker.
- **Tests at that commit (executed):** full backend **1192 passed, 0 failed, 0 xfailed**, 38 warnings, 1566.58 s (baseline `7754f9b`: 1179 passed, 1 xfailed, 1542.57 s); contingent file **17 passed** (29.50 s); promoter file **8 passed** (7.32 s); six decision-related files **55 passed** (130.09 s); 11-file regression battery **153 passed** (344.58 s). Golden hash `e84f8bc0…` intact.
- **Correction recorded in the same commit:** the previous pass's "claims + commitments = 105,410 / 3.14 %" mixed the 30 June 2026 interim commitment (90,389) with the 31 March 2026 claims column; the same-column total is 41,219 / **1.23 %**. The conclusion (far below 50 %) is unchanged. Both the earlier document and its tracker entry carry an explicit inline correction; no historical evaluation record was edited.
- **PR #6 (remote-verified):** `OPEN`, `merged: false`, `mergedAt: null`, head `e05c0efbca1ecb3024e52da73a22e180ea171118` (`arena/5dd3fe52-ipo-screening-engine`), base `arena/573e69a4-ipo-screening-engine`; neither moved nor merged. **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. **Ancestry:** both `01ba66c` and `e05c0ef` are ancestors of `2ec607c`. **CI:** no hosted workflows configured.
- **Non-changes:** `config/`, `schema/` and `fixtures/` diffs empty; no golden fixture, scoring formula, weight, threshold, cap, penalty, knockout semantic, confidence rule or missing-value rule touched; no historical evaluation re-run or rewritten.

### HD Fire — primary-source recovery, 44-field reconciliation and acceptance — 2026-10-20

- **Record:** `docs/investigation/HD-FIRE-PRIMARY-SOURCE-RECOVERY-2026-10-20.md`. **Baseline:** `62bd22b` (remote-verified at pass start); `main` `01ba66c`; PR #6 OPEN/UNMERGED at `e05c0ef`. **No engine, `config/`, `schema/` or `fixture` change**; one new test module and this record.
- **Retrievability corrected — the earlier "unobtainable" finding was a method artefact.** Sandbox egress still fails (`curl` → TLS `SSL_ERROR_SYSCALL` to sebi.gov.in, bseindia.com, iiflcapital.com, hdfire.com), but the page-fetch path **does** retrieve and parse PDFs. Three primary documents were obtained: (S1) the **SEBI-hosted Abridged Prospectus** (RHP dated 5 October 2026) — retrieved in full; (S2) the **IIFL Capital-hosted RHP** — pages 1–30 only (the tool parses at most 30 pages); (S3) the **BSE anchor-investor allocation notice dated 12 October 2026** — in full, establishing the **₹271** cap price. The final Prospectus, the price-band advertisement and RHP pp. 31–450 remain unavailable; that is stated, not worked around.
- **44-field reconciliation: 25 VERIFIED · 8 CONTRADICTED · 10 UNRESOLVED · 1 NOT APPLICABLE** (was 10/7/26/1). Every disposition states the document, the section and the source value; nothing from the contingent-liability note, the RPT note or the peer table is cited, because those pages were never read.
- **Financial (A):** revenue FY2024–FY2026 3,729.53 / 4,327.99 / 4,892.81 ₹mn; CAGR **14.5387 %**; operating EBITDA 1,504.59 ₹mn (margin **30.751 %**); PAT 1,167.87 ₹mn; **net worth FY2026 3,771.47 ₹mn = ₹377.147 cr** (Q1 FY2027 4,010.20 ₹mn); CFO 924.92 ₹mn; **cumulative CFO/PAT 0.8097** (the 0.79× input is the annual ratio); ROCE 40.33 % is the disclosed KPI and is internally consistent (EBIT ₹1,561.5 mn vs operating EBITDA ₹1,504.6 mn — other income exceeds D&A); total borrowings **Nil** in every period, finance cost not disclosed ⇒ engine `leverage_bucket` stays UNKNOWN.
- **PAT margin 23.12 % CONTRADICTED as the engine metric:** the RHP defines PAT margin over **total income**; the engine divides by **revenue** → **23.869 %**. **P/B CONTRADICTED:** 4,748.733 / 377.147 = **12.591×**, not 11.876× (that used the withdrawn ₹399.87 cr net worth). Market cap at ₹271 × 175,230,000 = **₹4,748.733 cr**.
- **Offer structure (C):** fresh issue nil; 26,284,500 shares (15.000 % of pre-issue capital) sold by two promoter selling shareholders — Harish Narshi Dharamshi 8,983,700 and Kusum Harish Dharamshi 17,300,800; company receives **nothing**. The **₹0.2983 cr equal-and-opposite seller error is explained**: the split was transposed; at ₹271 the correct proceeds are **₹243.4583 cr + ₹468.8517 cr = ₹712.3100 cr**.
- **Promoter holding (E) — root cause proved from the filing.** S1 §5 prints Promoters `Total (A)` 167,035,000 (95.33 %), Promoter Group `Total (B)` 8,195,000 (4.67 %), `Total (A+B+C+D)` 175,230,000 (100 %), with **every post-Offer cell `[●]`** ("To be filled at the Prospectus stage"). Re-running the pre-fix fallback on those rows reproduces **95.33 + 4.67 = 100.00** as the post-issue holding — the record's impossible `promoter_post_pct` was the sum of the two *pre-issue* totals. The corrected parser returns **pre 100.0 / post None** on the same table (pinned by test). 85.00 % = (175,230,000 − 26,284,500)/175,230,000 is arithmetic on disclosed counts, **not a disclosed post-issue value**, and is not hard-coded.
- **Governance (D):** auditor opinion **unmodified** is supported by S1 §11 ("no reservations, qualifications and adverse remarks"); tenure and EOM are **not** established ⇒ `auditor_bucket` UNKNOWN (D-4); going concern UNKNOWN (D-1). **New defect established, decision required (D-5):** `extract_governance` initialises `litigation_bucket = "clean"` and `sebi_ed_action_active = False` and emits both unconditionally, even when the scan finds nothing — 4/4 points on a default — and the SEBI field carries the synthesised quote "No active SEBI or ED regulatory proceedings" without `quote_is_processing`. HD Fire itself discloses **2 criminal proceedings against Directors** and 3 tax proceedings by the Company (S1 §12), which the regexes cannot see. **Not changed** at that time (scoring-semantic decision outside the approved D-1…D-4 scope); pinned by two strict xfails.
  **Superseded the same day by D-5** — see "HD Fire / Jio — D-5 litigation and regulatory-action evidence defaults" at the end of this file: the unsupported defaults are removed, both xfails are now passing assertions, and the two questions that genuinely need a governed standard (party coverage for `clean`, source coverage for a verified regulatory absence) are recorded as open in `handoff/decisions/A23-litigation-regulatory-evidence-defaults.md`.
- **Historical record `…551a7eab` NOT recovered.** Checked: working tree, `build/evaluations/` (absent), `evaluations/` (absent), `git log --all -S`, all **17** branch trees via the GitHub trees API, GitHub code search, releases, Actions artifacts and PR #6 comments. The 7/100 is therefore not independently reproducible; its documented decomposition (A2+B0+C3+D5+E0+F0 = 10, one −3 penalty, available 27) is internally consistent, but the D `promoter_post_holding` 4/4 is **not supported by the source**. Recovery = copy the eight store artifacts from the Windows `build/evaluations/` directory.
- **No new evaluation produced.** A single non-persisted diagnostic `evaluate()` run with the verified input set (`store=None`, no id, nothing written) returned **15.0/100**, available 39 / unknown 61, `INSUFFICIENT_DATA`, Module A **13/25**; it is reported as a diagnostic only, because the floor price is secondary-sourced and the peer/market/contingent-liability blocks are empty. The validated workflow needs the PDF in the store, which this environment cannot obtain.
- **Tests:** `tests/test_hd_fire_primary_source_extraction.py` — **4 passed, 2 xfailed (strict)** (0.05 s). Full backend suite: recorded in the publication block below.
- **Acceptance status:** source recovery **partial but material** (3 primary documents, 1 complete), evidence validation **advanced** (25/44 verified), score reconciliation **blocked** (record absent), implementation **unchanged**, durable publication **see below**. **HD Fire acceptance remains incomplete.**

#### Publication — 2026-10-20 (HD Fire primary-source recovery)

- **Commit:** `a2803598b22648524f498c6137d6311a7aec925d` on `arena/ae4d04e8-ipo-screening-engine`, pushed (`62bd22b..a280359`) and remote-verified (`git ls-remote` returned the same SHA). 4 files, 615 insertions, 1 deletion: the new recovery record, the supersession banner on the earlier reconciliation record, this tracker, and `tests/test_hd_fire_primary_source_extraction.py`. **No `config/`, `schema/`, `fixtures/` or engine change.**
- **Tests at that commit (executed):** full backend **1196 passed, 2 xfailed**, 38 warnings, 1095.32 s (baseline `62bd22b`: 1192 passed, 0 xfailed, 1566.58 s — the delta is exactly the 4 new passing checks and the 2 new strict D-5 pins); new module alone **4 passed, 2 xfailed** (0.05 s). Golden hash unchanged; no golden test altered.
- **PR #6 (remote-verified):** `OPEN`, `merged: false`, `mergedAt: null`, `mergeable: true`, head `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine`; neither moved nor merged. **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. **CI:** no hosted workflows.
- **Historical evaluations:** the HD Fire record `…551a7eab` remains absent (not replaced, not re-created); the Jio record `…7857589a` is untouched. No record was re-run, edited or re-hashed.

### HD Fire / Jio — D-5 litigation and regulatory-action evidence defaults — 2026-10-20

- **Record:** `docs/investigation/D-5-LITIGATION-REGULATORY-EVIDENCE-DEFAULTS-2026-10-20.md`. **Decision record:** `handoff/decisions/A23-litigation-regulatory-evidence-defaults.md` — an **investigation plus contract-permitted correction**, not an approval of the alternatives it lists (CONVENTION rule 4). **Baseline:** `2d52baa` (remote-verified at pass start); `main` `01ba66c`; PR #6 OPEN/UNMERGED at `e05c0ef`.
- **Defect, verified at the baseline.** `sections.py:1691-1732` assigned `lit_bucket = "clean"` and `sebi_active = False` **before** the scan and appended both fields **unconditionally** afterwards — including when the default range `430 … min(500, page_count)` covered no page at all — so an unread filing earned 4/4 on a scored criterion, and K2 was cleared by a flag no source had set. `governance.sebi_ed_action_active` was emitted with `quote="No active SEBI or ED regulatory proceedings"` and no `quote_is_processing`, i.e. a synthesised sentence presented as a source quotation (the defect class D-4 removed for auditor tenure/EOM). `builder.py:315-321` then mapped **every** value other than `criminal_or_regulatory` onto `"clean"`, so the evidenced `minor_civil` from `class_a_financial_lender.pdf` p. 11 was rewritten into the favourable bucket and its citation destroyed; `:336` defaulted the flag to `False`. The scan was phrase-bound (five literals) and polarity-blind: the ICDR summary table and labelled-list forms were invisible to it, and "there are **no** outstanding criminal proceedings or material civil litigation" classified as `minor_civil`.
- **No new state was invented.** The contract already provides UNKNOWN: `litigation_bucket` is `"enum": [..., null]`, `derived._litigation_bucket` maps `null` ⇒ UNKNOWN, `scoring.categorical_points` leaves an UNKNOWN criterion unscored (its 4 points move from `effective` to `unknown_points`, so **availability** falls — UNKNOWN is not 0), K2 lists `sebi_ed_action_active` in `required` and yields **UNVERIFIED, never CLEAR**, and `config.critical_data` turns that absence into `INSUFFICIENT_DATA`. Adding a fourth bucket value would have violated `config_validation.py:53`, which pins the map to exactly three keys; it was not done.
- **Implemented (correctness under the existing contract).** Bucket resolved from adverse prose → ICDR summary table → labelled category/value list → an express absence statement, and **emitted by no route at all** when none applies; structural text (table header, separator rows, table block, bare headings, nil-valued labelled items) masked offset-preservingly so a *label* can never be quoted as a *finding*, with quotations sliced from the unmasked page; only an "against" row is adverse and "by our Company" never is; an unparseable adverse row or an unmappable proceeding type (tax-only) blocks every favourable conclusion; `sebi_ed_action_active` True only from a count in the SEBI column / a regulator-named labelled count / a sentence with agency + finite act + party (boilerplate and negations excluded, polarity measured to the act verb), False only from a denial naming **both** SEBI and the ED; the builder normalises stated synonyms and never defaults either field.
- **Deferred (decision required, §6 of A23).** (1) a **party-coverage standard for `clean`** — whether an express nil naming only "the Company and its Promoters" also clears the Directors/KMP; options A (status quo, gap visible in `notes`) / B (Company+Promoters+Directors) / C (full ICDR population), B and C each moving filings from 4/4 to UNKNOWN; (2) a **source-coverage standard for a verified regulatory absence** — A (status quo: both regulators must be named) / B (a defined set of prospectus sections) / C (external regulator-register corroboration, which needs the A8 retrieval/cutoff/unavailable-source contracts); (3) `presentation/ui7.py`'s display default that renders UNKNOWN as "No active SEBI or ED action" (presentation-only, but it changes what every historical record shows); (4) whether tax-only / statutory-only adverse counts belong in `criminal_or_regulatory`. None applied.
- **HD Fire evidence (D-5.3), from its own filing.** SEBI-hosted **Abridged Prospectus**, section **12 "Summary table of outstanding litigations"** (retrieved 2026-10-20 through the page-fetch path; sandbox egress fails at TLS): **`Against our Directors | 2 | Nil | Nil | NA | Nil | Nil`** — two criminal proceedings against "Directors (excluding Promoters)", no name, case number, forum, status or amount given; `Against our Company` and `Against our Promoters` Nil in every column; `By our Company | Nil | 3 | … | 0.40` — three **tax** proceedings *brought by* the issuer (₹0.40 mn), which are its own claims and map to no governed bucket. The issuer is **not** named as an accused. The SEBI column is scoped "against our Promoters in the last five years" and reads Nil, and no ED proceeding appears anywhere in the retrieved pages, so **nothing establishes an active SEBI/ED action in either direction** — the flag stays UNKNOWN for HD Fire. Supported bucket: **`criminal_or_regulatory`** (the criterion's formula covers "promoters, directors and the company"); `clean` is contradicted by the issuer's own table and `minor_civil` excluded. Particulars sit on **RHP p. 356**, unretrievable here (30-page fetch cap) ⇒ **UNRESOLVED**; final Prospectus unavailable; historical record `…551a7eab` still absent. **HD Fire acceptance remains incomplete.**
- **Measured impact (live extraction, `allow_fixture_fallbacks=False`); no historical evaluation re-run.** R.K. Fashion: bucket/flag **absent** (were `clean`+`false`) ⇒ final **49.0 → 45.0**, base 52.0 → 48.0, available 73 → 69, completeness 73.0 → 69.0, lower bound 36.0 → 32.0, Module D 10.0 → **6.0/15** with `unknown_points` 2.0 → 6.0, and **K2 `CLEAR` → `UNVERIFIED`** (`missing: ["sebi_ed_action_active"]`), verdict `INSUFFICIENT_DATA` unchanged. `complete_sample_rhp` **23.0 → 19.0** and `complete_sample_rhp_2` **21.0 → 17.0** (available 26 → 22, Module D 5.0 → 1.0/15). `class_a`: the extracted bucket is no longer rewritten, and its p. 11 sentence now yields `clean` *with that sentence quoted* — score unchanged at 41.0; `class_b/c/d/e` keep `clean`, now evidenced (41.0 / 43.0 / 35.0 / 35.0 unchanged); Jio keeps `criminal_or_regulatory` p. 464 with a verbatim quote and loses the fabricated `false`; the vishal **live PDF** keeps `criminal_or_regulatory` and loses a `sebi_ed_action_active = True` that had been read off the section **heading** "(d) Disciplinary actions by SEBI and / or the Stock Exchanges involving our Company". **Implementation correction, not semantic change:** every delta is the removal of an unevidenced 4-point award or of a fabricated negative; the governed map, weights, thresholds, formulas, knockout semantics and confidence rules are byte-identical, `config/`, `schema/` and `fixtures/` diffs are empty, and the vishal golden record stays **35.0 / `e84f8bc0f9b9…`**.
- **Tests (executed).** `tests/test_litigation_regulatory_defaults.py` — **51 passed** (new; all nine D-5.4 scenarios plus verbatim-quote and no-fabrication pins and the contract pins). `tests/test_hd_fire_primary_source_extraction.py` — **7 passed, 0 xfailed**: the **two strict D-5 xfails are replaced by passing assertions** (field absent, not defaulted; no record at all rather than a flagged quote) and a new test pins HD Fire's §12 table to `criminal_or_regulatory` with the Directors row quoted verbatim and no regulatory flag. Re-measured pins (not hand-edited): `test_rk_fashion_reconciliation.py` **5 passed**, `test_ui7_ingestion.py`, and the D-1…D-4 suites unchanged and passing. Full backend suite on the published tree: **1250 passed, 0 failed, 0 xfailed**, 38 warnings, **1642.70 s** (27 m 22 s) — baseline at `2d52baa`: 1196 passed, 2 xfailed, 1095.32 s. The delta is exactly the 51 new D-5 cases plus the 1 new HD Fire §12 test, with the 2 strict D-5 xfails converted into passing assertions; every previously passing test still passes, and no `pytest.mark.xfail` remains anywhere in `tests/`

#### Publication — 2026-10-20 (D-5 litigation / SEBI-ED evidence defaults)

- **Implementation commits:** `1bd468e7cdb6a422c47a66dc79632f103557cd08` (default removal + `tests/test_litigation_regulatory_defaults.py` + A23 + the investigation record) and `7bae763` (SEBI/ED route symmetry from the edge audit, +7 controls), pushed and remote-verified: `git ls-remote origin refs/heads/arena/95234306-ipo-screening-engine` returned `328813a5272736ae165e9b19309ab61687374abd` (the branch tip at publication; `1bd468e7…` and `7bae763…` are its ancestors). `01ba66c` (main) and `e05c0ef` (PR #6 head) verified as ancestors of the published tip.
- **Tests at the published tree:** **1250 passed, 0 failed, 0 xfailed**, 38 warnings, 1642.70 s — vs 1196 passed, 2 xfailed at the `2d52baa` baseline; the 52-test delta is the new `tests/test_litigation_regulatory_defaults.py` (51) and the new HD Fire §12 test, with the two strict D-5 xfails now ordinary passing assertions. Golden hash `e84f8bc0…` intact. Progress bar captured at 60-test granularity throughout the run
- **PR #6 (remote-verified):** `state: OPEN`, `closed: false`, `mergedAt: null`, `mergeable: MERGEABLE`, head `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine` — neither moved nor merged. **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched. **CI:** no hosted workflows.
- **Non-changes:** `config/`, `schema/`, `fixtures/` diffs empty; no scoring formula, weight, threshold, cap, penalty, knockout semantic, confidence rule, missing-value rule, golden fixture or historical evaluation record touched; the Jio record `…7857589a` and the absent HD Fire record `…551a7eab` were neither re-run nor rewritten; the golden hash `e84f8bc0…` is intact.
- **Open after this pass:** the two A23 §6 coverage standards (party coverage for `clean`, verified regulatory absence), the UI7 display default, tax/statutory-only bucket mapping, and HD Fire's RHP p. 356 particulars, final Prospectus and missing evaluation record. **HD Fire source-level acceptance remains outstanding.**

### HD Fire / Jio — A23 disposition: coverage-scoped `clean`, verified-absence scope, display no-defect — 2026-10-20

- **Scope and record.** Continuation of D-5, resolving the four matters A23 §6 left open. Record: `handoff/decisions/A23-litigation-regulatory-evidence-defaults.md` **§6A** (per-matter finding / evidence / change / status), with the implementation detail in `docs/investigation/D-5-LITIGATION-REGULATORY-EVIDENCE-DEFAULTS-2026-10-20.md` §10 and suite-cost analysis in `docs/RUNBOOK.md` §17. **Baseline verified remotely before any change:** branch tip `10b100adb4e10eabc6d03b9e66c364400ce158e2` (local `git rev-parse HEAD` identical), `main` `01ba66c`, PR #6 `OPEN`/`MERGEABLE` at head `e05c0ef` with base `arena/573e69a4-ipo-screening-engine`, `git status --porcelain` empty, `git diff --stat 2d52baa..HEAD -- config schema fixtures` empty.
- **Matter A — party/type coverage for `clean`: demonstrated defect, corrected (RESOLVED for dimension coverage).** Probing the published `sections.py` showed the prose-absence step accepted *any* sentence matching an absence form, so a nil covering only criminal proceedings, only civil litigation, only regulatory action or only tax earned the favourable 4/4 — while the ICDR summary-table route already refused to answer `clean` unless its criminal/civil/regulatory columns were present. The two routes disagreed; the prose route is now aligned with the table route via `_lit_absence_is_comprehensive` (no candidate emitted ⇒ UNKNOWN). Cases A1/A4/A7 (criminal-only, civil-only, regulatory-only nils) moved from `clean` to *no bucket*; A2/A3/A5/A6 (unqualified or both-dimension nils, including `class_a` p. 11 and `class_b` p. 10 verbatim) keep `clean`. **`clean` on selected `Nil` rows was already impossible** in the table route, and missing / ambiguous / unparseable coverage continues to be represented as an absent field ⇒ `STATE_UNKNOWN` ⇒ points unavailable rather than awarded.
- **Matter A — party coverage: PROPOSED / UNRESOLVED (not implemented).** *Which* parties a nil must reach is not governed by v1.5, so no standard was invented in code. Recommendation recorded in A23 §6.1/§6A.1: option **B** — an express nil must reach the **Company, the Promoters and the Directors**, matching the wording of the criterion's own definition ("across promoters, directors and the company"), with the parties covered recorded in `notes`; option **C** (full ICDR population including KMP and Senior Management) is recorded as the alternative and its availability cost. Awaiting RAMKI decision.
- **Matter B — verified absence of SEBI/ED action: one demonstrated defect corrected, the positive standard PROPOSED / UNRESOLVED.** Absence-of-evidence vs evidence-of-absence is already structural (nothing is emitted unless a finite adverse act or a denial naming **both** regulators is found on the searched pages; a SEBI-only or ED-only negative never clears the flag; failed/unavailable pages surface as absent fields plus `missing_inputs`, and the repository's real failure vocabularies stay distinct from any boolean — `issue_terms.ProviderReport.outcome` (`FOUND`/`NOT_FOUND`/`UNAVAILABLE`/`REJECTED`), `ResolutionOutcome.status` (`RESOLVED`/`PARTIAL`/`UNPUBLISHED`/`UNAVAILABLE`/`CONFLICT`/`UNVERIFIED`, with `AWAITING_ISSUE_TERMS` at the API boundary), the `presentation/ingestion_activity.py` stage and terminal statuses, and `connectors.FreshnessStatus` (`FRESH`/`STALE`/`FUTURE`/`MISSING`)). The defect was at the other edge: a denial scoped to a **closed** period ("during the financial year 2023-24", "as on 31 March 2022") cleared `sebi_ed_action_active = False` even though the governed flag asks whether an action **is** active — now suppressed by `_REG_ABSENT_CLOSED` in both the sentence path and the collected-absence loop (probe B3/B4 `False` → field absent), while unqualified, as-of-the-prospectus and rolling "last five years" negatives still clear it (B1/B2/B5 unchanged) and the `True` path is untouched. The recommended testable positive standard is recorded in A23 §6A.2 and is **not** treated as approved.
- **Matter C — display of UNKNOWN: investigated, NO DEFECT; the earlier claim in this tracker is corrected.** There is no `engine/ipo_screening/presentation/ui7.py` (`presentation/` contains `api.py`, `ingestion_activity.py`, `models.py`, `service.py`; `find . -name "*ui7*"` matches only `tests/test_ui7_ingestion.py`, a workstream label), and `grep -rln "No active SEBI"` matches only `sections.py`'s own comment and its test. `frontend/app.js::renderMetricValue` renders `badge-unknown` for `UNKNOWN` or a null/undefined value and `N/A` only for `NOT_APPLICABLE`, prints booleans literally, `renderSemanticStateBadge` keeps SCORED / UNKNOWN / NOT_APPLICABLE distinct, knockout cards keep CLEAR / TRIGGERED / unverified distinct, and `service.py` defaults a missing knockout state to `UNVERIFIED`, never `CLEAR` — so adverse evidence, verified absence and insufficient evidence remain distinguishable on screen and nothing implies a favourable conclusion the record does not support. **No code changed; a regression test was added instead** (`frontend/test/app.test.js`), and A23 §6.3 now carries the withdrawal.
- **Matter D — tax / statutory-only proceedings: no new bucket, nothing forced into `clean`.** The taxonomy is defined in three agreeing places (schema enum, `config_validation.py:53`, `builder._LITIGATION_BUCKET_ALIASES`) as `clean / minor_civil / criminal_or_regulatory`. **Correction to the D-5 entry's §6.4 claim:** a *statutory/regulatory* adverse count is not unmappable — the ICDR "Outstanding Statutory/Regulatory Proceedings" column already feeds `criminal_or_regulatory` (now pinned by `test_d_statutory_or_regulatory_count_uses_the_existing_bucket`); only **tax-only** adverse exposure is genuinely unmappable and stays UNKNOWN, and after the Matter-A fix a tax-only *nil* no longer reads `clean`. Direction rules already handle the issuer-initiated case ("By our Company" rows are non-adverse; a `Nil` in a column scoped to a subset clears nothing). A governed resolution (fold tax in, or add a fourth bucket with schema + `config_validation` + overlay + golden re-pin) is recommended as a **separate decision record**, not applied here.
- **HD Fire — used only as a test case, re-confirmed against the corrected code.** `tests/test_hd_fire_primary_source_extraction.py` **7 passed** and the litigation module's §12 cases pass: the 2 `Against our Directors` criminal proceedings still reach `criminal_or_regulatory` with the Directors row quoted verbatim (the `Nil` rows cannot erase them); no SEBI/ED finding is fabricated in either direction (flag absent); the incomplete coverage does not read as comprehensive verification; the `By our Company` tax rows (3, ₹0.40 mn) do not become `clean`. No universal rule was derived from this filing.
- **Measured effect on the committed fixtures (before/after pairs, both sides measured — not hand-adjusted).** Before = `10b100a`, after = this commit, identical conditions (`allow_fixture_fallbacks=True`, `evaluate(mode="final", evaluation_datetime=2026-10-05T12:00Z)`): `class_c` **41.0/available 55.0/Module D 6.0/unknown 6.0 → 37.0/51.0/2.0/10.0**, `class_e` **43.0/55.0/6.0/6.0 → 39.0/51.0/2.0/10.0**, `class_d` **28.0/41.0/6.0/6.0 → 24.0/37.0/2.0/10.0** (no assertion in the suite pins class_d's score, so only the test-pinned class_c and class_e values were re-pinned); each move is −4 earned **and** −4 available with the 4 points reappearing as `unknown_points` — UNKNOWN, not a penalty. `class_a` (40.0/54.0) and `class_b` (41.0/55.0) are **byte-for-byte unchanged**, keeping `clean` because their nils cover both dimensions. **This supersedes the D-5 entry's per-filing attribution** "class_b/c/d/e 41.0 / 43.0 / 35.0 / 35.0", which mixed the filings up: the committed pins were class_b 41.0, class_c 41.0, class_e 43.0, and class_d had none. vishal golden stays **35.0 / `e84f8bc0…`**; R.K. Fashion 45.0, Jio and vishal live-PDF outcomes unchanged.
- **Test progress and runtime (root cause + mechanism + honest limits).** The suite's long tail is CPU-bound real-PDF extraction: measured stage times account for the entire run (sum 1130.5 s of 1131.26 s) and are led by `test_step5_auditor_and_manual_terms.py` 140.9 s/19, `test_ui7_ingestion.py` 109.0 s/20, `test_derived_evidence_registration.py` 108.7 s/**3** (36.2 s per test), `test_extraction.py` 84.2 s/12. The progress mechanism is now **in the repository** (`tests/pytest_progress.py`, registered from `tests/conftest.py`, flushed to stderr) rather than the out-of-tree `-p progress_plugin` that a sandbox reset previously destroyed; it reports completed ÷ collected of the collected count (labelled as such, with an explicitly linear-rate eta), per-module stage times and tests ≥ 10 s. Measured on this tree: **1265 collected / 1265 passed / 0 failed / 0 skipped / 0 xfailed in 1131.26 s** vs the D-5 checkpoint's 1250 tests in 1642.70 s — 1.31 s → 0.89 s per test, an improvement attributable to an idle box rather than to this pass (documented as such; the suite still cannot run in minutes, and `pytest -n auto` was evaluated against measured resources — 2 CPUs, 3939 MB — and rejected because a test in this suite has previously failed only under contention). **Arena limitation:** the `bash` tool returns output only when the command completes and its timeout kills the run, so a long foreground suite looks stalled regardless of any in-repo mechanism; the mitigation is to run the suite as a background process and poll the flushed log — the plugin makes progress available, it cannot change what the harness renders mid-call.
- **Verification (all executed on the tree published by this commit).** `tests/test_litigation_regulatory_defaults.py` **66 passed**; `tests/test_hd_fire_primary_source_extraction.py` **7 passed**; affected-module battery of 7 modules **138 passed in 262.67 s**; `test_extraction_phase5b.py` **9 passed**; frontend **90 passed / 0 failed (702 ms)**; full backend **1265 passed, 0 failed** (completed, not interrupted; log committed at `docs/investigation/D-5-A23-SUITE-PROGRESS-2026-10-20.log`); the project's own check `python3 engine/tools/ipo_screen.py check-config` → **valid True**, all 10 profiles reconciling to 100 points. `config/`, `schema/`, `fixtures/`, `build/evaluations/`, `evidence/` and the historical records carry **no diff**; **0 `xfail`** anywhere in `tests/` (none added).
- **Open after this pass (unchanged items restated, not forgotten).** RAMKI decision required on: the `clean` party-coverage standard (§6.1 → recommend B), the verified-absence source standard (§6.2 → recommend B, with C awaiting A8's retrieval/cutoff/unavailable-source contracts), and any tax-bucket treatment (§6A.4). These three are now the subject of the A24 / A25 + A8-R / A26 records in the entry below — still unresolved, and deliberately not implemented. HD Fire blockers from D-5 stand unchanged: RHP p. 356 particulars, final Prospectus and the absent record `…551a7eab` remain unavailable, so **HD Fire source-level acceptance is still incomplete**.

#### Publication — 2026-10-20 (A23 disposition pass)

- **Implementation commit:** `c204c8269567898ab4c531ab54154a988b2c68b2` (parent `10b100adb4e1…`), pushed to `arena/95234306-ipo-screening-engine` and **verified remotely**: `git ls-remote origin refs/heads/arena/95234306-ipo-screening-engine` returned the same SHA as local `HEAD`, and the GitHub commits API returned that SHA with **10 files, +894 / −10** naming each published path (`sections.py`, `tests/pytest_progress.py`, `tests/conftest.py`, `tests/test_litigation_regulatory_defaults.py`, `tests/test_extraction_phase5b.py`, `frontend/test/app.test.js`, A23, the D-5 record, the new progress log, `docs/RUNBOOK.md`) — i.e. the artifacts exist on the remote, not only in this working tree.
- **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094` — unchanged (re-verified after the push). **PR #6:** `state OPEN`, `mergedAt null`, `mergeable MERGEABLE`, head `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine` — not merged, not force-pushed, not reset. **CI:** no hosted workflows.
- **Non-changes:** no scoring formula, weight, threshold, cap, penalty, knockout semantic, confidence rule, missing-value rule, schema enum, config value, golden fixture or historical evaluation record was modified; no evaluation was re-run, re-hashed or newly published to demonstrate these fixes.
- **Follow-up commits on the same branch:** `19b4fae493efbfea7329239ed5e28cbc89385a50` (this entry) and one further Markdown-only commit carrying the measured before/after pairs and the §6A.1 pointer. `git diff --stat c204c82..HEAD` covers those two record files and nothing else, so the completed full-suite run validates every code and test line this pass published; `config/`, `schema/` and `fixtures/` remain empty in `git diff --stat 2d52baa..HEAD`, and the vishal golden hash was re-derived directly (computed `e84f8bc0f9b9…5619e1` == `fixtures/vishal_nirmiti/expected_verdict.json → hashes.result_hash`).

### HD Fire / Jio — A23 governance decision pass: three standards put to decision (A24, A25 + A8-R, A26) — 2026-10-20

- **What this pass was, and what it deliberately was not.** A governance analysis pass resolving the three items A23 §6 left open — party coverage for `clean`, source coverage for a verified SEBI/ED absence, and tax-only adverse classification. **Implementation, scoring, schema, taxonomy, configuration and golden fixtures were not changed**: three decision records and one dependency request are published as **PROPOSED / UNRESOLVED — RAMKI APPROVAL REQUIRED**, because a standing execution authorisation is not policy authority (CONVENTION rules 4 and 6). Starting state re-verified remotely first: tip `38f51571d2a043c91fed054d90ea01141ca41de9` (local == `git ls-remote`), `main` `01ba66c`, PR #6 `OPEN`/`mergedAt null`/`MERGEABLE`/`CLEAN` at head `e05c0ef` with base `arena/573e69a4-ipo-screening-engine`, clean tree.
- **Matter A → `handoff/decisions/A24-litigation-party-coverage-standard.md` (PROPOSED).** The exact question, measured rather than argued: today the prose route needs only **one** party token from `_LIT_PARTY` to answer `clean` (a nil about KMP alone, or about the Company alone, earns 4/4), while the table route requires the criminal/civil/regulatory **columns** but never a party **row** — so the two routes disagree in the opposite direction. Probing shows the criterion's own definition settles the choice: `handoff/reference/ipo-config.json:294` (upstream v1.4 reference) and `engine/ipo_screening/derived.py:1384` both enumerate **promoters, directors and the company**, so **Option A "as enumerated" and Option B are the same standard** and the real alternative is Option C (adding KMP + Senior Management), which would *amend* the criterion. Recommendation: A ≡ B (rules R1–R8, incl. "Group Companies" must not be counted as the issuer, and any shortfall ⇒ UNKNOWN with the covered parties in `notes`), measured impact `class_b` 41.0/55.0 → UNKNOWN and no golden or adverse-case movement. **Also recorded, not fixed:** a real defect — an ICDR row whose party label carries a parenthetical (`Against our Directors (excluding Promoters)`, the format real filings use) mis-aligns the cells, so the row counts as *unreadable* and an all-nil table in that format yields no bucket; it must be repaired in the same future pass as R1–R5 or coverage failures will be misread as non-disclosure.
- **Matter B → `handoff/decisions/A25-sebi-ed-absence-source-coverage-standard.md` + `handoff/decisions/A8-R-REGULATOR-SOURCE-COVERAGE-DEPENDENCY-REQUEST-2026-10-20.md` (both UNRESOLVED).** A8 was investigated directly, not assumed, and the finding is negative and specific: `A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md` is scoped "for a required `market.regime.nifty_trend` input **only**" and §6 excludes "any other metric"; `A8-final-snapshot-event-cutoffs-investigation.md` covers subscription/market/GMP/peers with source/provider/event/cutoff contracts still **OPEN** and implementation authority not granted. **There is therefore no A8 basis for an externally corroborated regulatory absence, and none was invented** — A8-R is filed as the request listing the ten provisions that would be required (authority set, discovery/retrieval, issuer matching, index completeness, event/cutoff semantics, failure handling, retention/provenance, conflict rule, K2 evidence policy, currency window). What *is* implemented today and transferable: the `issue_terms.py` contract — `OFFICIAL_HOSTS` incl. `sebi.gov.in`, outcomes `FOUND/NOT_FOUND/UNAVAILABLE/REJECTED`, and the evidentiary rule that a negative needs the named listing that really was searched (`listing_searched`/`searched_listings`: "a bare flag is not enough"), born of the 2026-10-18 false-`NOT_FOUND` repair; plus A18's approved L1–L4 evidence-linkage shape. A25 recommends Option 2: `false` only from a both-regulator, present-scope, party-covering denial **and** a TOC-located litigation section, with `notes` stating that this means "no action disclosed by the issuer", never "no action exists"; two observability prerequisites are named because the previously recommended "each page actually extracted successfully" clause **is not expressible today** — `extract_page_text` returns `""` for a failed page exactly as for a blank one, and the guessed `430…500` range is indistinguishable from a located one. A23's §6A.2 sentence naming an `AWAITING_SOURCE` lifecycle value is corrected here (no such identifier exists in the code) and the real vocabularies substituted.
- **Matter C → `handoff/decisions/A26-tax-only-proceedings-classification.md` (PROPOSED: retain, do not remap).** The governed semantics were read at every layer: v1.5 §4.3 lists "tax proceedings" as a governance input and `docs/TRACEABILITY_MATRIX.md`'s §4.3/§11 rows have **no consuming metric** for it; `config_validation.py:53` pins the domain to three names; the ICDR "Tax Proceedings" column is parsed but deliberately maps to no bucket, and a count there sets `unmapped`, which blocks `clean` (measured: tax-only count ⇒ no bucket; tax-only nil ⇒ no bucket after A23; tax+criminal+civil nil ⇒ `clean`; statutory/regulatory count ⇒ `criminal_or_regulatory` because that bucket's own name covers it). Option B (map tax into an existing bucket) is rejected on the evidence — it would assert a track-record equivalence the bucket name does not carry and double-count an exposure A20 already prices through the contingent-liability numerator and K5; Option C (a fourth bucket) is costed completely (schema, `config_validation`, **both** config versions — v1.6.0 carries the identical map, so it is a config **version** change that invalidates stored `config_hash`es and forces a golden re-baseline — `derived`, `builder`, both extraction routes, all consumers incl. the frontend GOVERNANCE field filter and Excel export, tests, and historical-record validity) and is not undertaken here. Recommendation: **Option A**, keep UNKNOWN, record the gap. **One question is put to RAMKI rather than resolved:** the upstream v1.4 reference put "disputed tax" in `auditor_bucket.eom_only`, and the shipped v1.5 formula no longer mentions tax — whether that was deliberate (then tax has no litigation scoring home by design) or an omission (then the repair belongs to the auditor criterion, not to `litigation_bucket`).
- **Approval status of every item.** A24, A25 and A26 are **PROPOSED**; A8-R is **UNRESOLVED** and open. None is APPROVED, ACCEPTED or IMPLEMENTED, and no proposal was treated as authority for a code change. Each record carries its own acceptance criteria, affected components, migration/compatibility analysis, dependencies and the concise questions to RAMKI.
- **Validation actually run for this pass (documentation-only change set).** Focused behaviour at the current tree: `tests/test_litigation_regulatory_defaults.py` **66 passed** (0.20 s) and `tests/test_hd_fire_primary_source_extraction.py` **7 passed** — these substantiate the "today" column of every table in A24/A26 and the §2 state table in A25; `python3 engine/tools/ipo_screen.py check-config` → **valid True**, 10 profiles × 100 points; the vishal golden hash recomputed directly as `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`, unchanged. **No full-suite rerun was performed or needed:** this pass changes only Markdown under `handoff/`, so the completed full-suite result at the *code-identical* tree `c204c82` (1265 collected, 1265 passed, 0 failed, 0 skipped, 0 xfailed, 1131.26 s; log `docs/investigation/D-5-A23-SUITE-PROGRESS-2026-10-20.log`) remains the applicable checkpoint, and `git diff --stat 38f5157..HEAD` shows no `engine/`, `tests/`, `config/`, `schema/` or `fixtures/` file. The runner-level progress mechanism from the previous pass (`tests/pytest_progress.py`, registered from `tests/conftest.py`, flushed to stderr) stays available for any future long run; Arena's synchronous `bash` tool still returns output only at command completion, so long suites must continue to run as background processes polled from the log — no live-UI progress is claimed.
- **Integrity.** `git diff --stat 2d52baa..HEAD -- config schema fixtures` still empty; no scoring formula, weight, threshold, knockout semantic, confidence rule, schema enum, config value, golden fixture or historical evaluation record touched; **no** evaluation re-run, rewritten or newly published; D-1…D-5 decisions and their records unmodified apart from the two dated factual corrections noted above; 0 `xfail` in `tests/` (none added).

### A24 / A25 approved and implemented; A26 history checked; A27 raised — 2026-10-20

- **What this pass was.** Ramki approved **A24-D1/D2/D3** and **A25-D1/D2** for implementation;
  this pass implements exactly that scope in `engine/ipo_screening/extraction/sections.py` and
  its tests, and does the two bounded investigations that were asked for in the same order —
  the **A8-R** dependency request (extended, still unresolved) and the **A26** tax-history
  question (answered with evidence, and it produced **A27** as a new open decision). Starting
  commit `ce577ea022c1eaf2363fe8cd0e3b93bf5450b4da`, verified remotely before any edit.
- **A24-D1 — party coverage for `clean`.** A denial may support `clean` only if it reaches the
  Company **and** its Promoters **and** its Directors, the population the governed formula names
  in **both** shipped configs (`config/ipo-config.v1.5.0.json`/`v1.6.0.json`:
  `clean / minor_civil / criminal_or_regulatory (promoters, directors, company)`); "Group
  Companies" is stripped before the issuer test so the group cannot stand in for the Company,
  and KMP / Senior Management were **not** added (Option C stays unapproved). Same rule on the
  ICDR summary-table route, credited only by rows whose cells actually parsed.
  Record: `A24-…md` §13.
- **A24-D3 — the `Directors (excluding Promoters)` row defect, repaired.** One bracketed
  qualifier between the party label and the first cell boundary is removed for column alignment
  only; the quotation remains the verbatim source line, Directors is never read as Promoters
  coverage, an unreadable cell yields no bucket and no invented `NIL`, and stacked qualifiers
  stay UNKNOWN as the approval requires.
- **A24-D2.** A reviewer-supplied `governance.litigation_bucket` is still honoured by the
  builder and is still never turned into an extraction record or an evidence quotation; the
  coverage gate lives in the extractor and neither consumes nor overrides that assertion.
- **A25-D1/D2.** `sebi_ed_action_active = false` now means and **reads** "issuer-authored denial
  … absence of disclosure, not verified absence", with a `search basis:` clause naming the
  window it came from; an absence (bucket or flag) is emitted only on a TOC-located window whose
  pages were all read (`READ`/`BLANK`/`FAILED`/`OUT_OF_RANGE` per page, exposed via
  `page_status`/`pages_read`), while an adverse finding never depends on that. No retrieval was
  built: `SourceClass`, the connectors and the schema are untouched, and **A25-D2's two states
  are the whole of the observability work**. Record: `A25-…md` §12.
- **A26 history, investigated rather than assumed.** The premise that v1.5 dropped
  "disputed tax" from `auditor_bucket.eom_only` is **false**: the clause is in the v1.3 spec
  (`…Specification.md:105`), the v1.4 reference (`handoff/reference/ipo-config.json:297`) and
  **still in both shipped configs** (`config/ipo-config.v1.5.0.json:1727`,
  `config/ipo-config.v1.6.0.json:1727`); `git log --all -S"disputed tax" -- engine/` returns
  **nothing**, so the engine never had it to lose and `derived._auditor_bucket` has always read
  only `auditor_opinion`, `auditor_reputed`, `auditor_changed_3y`, `repeated_eom`. Two further
  facts: `governance.caro_remarks` is declared in `schema/ipo-input.v1.5.schema.json:659` and
  referenced **nowhere else in the repository**, and four more governance inputs
  (`eom_count_3y`, `auditor_change_count_3y`, `regulatory_actions`,
  `independent_director_count`) are likewise declared and unconsumed. So the auditor clause is
  neither an intentional non-score nor a lost edit — it is text the input surface cannot
  express. **Tax-only litigation exposure therefore stays UNKNOWN, unchanged**, and the auditor
  question is posed as a separate, explicitly unimplemented decision in
  `handoff/decisions/A27-auditor-bucket-unconsumed-clauses.md` (Options A–D, with the
  absent-input semantics and the double-counting interaction with A20/K5 named as the things
  Ramki must pick). A26 §11 carries the evidence table; its earlier v1.4→v1.5 reading is
  corrected in place.
- **Traceability.** `docs/TRACEABILITY_MATRIX.md` gains row **GAP-4.3** — v1.5 §4.3 tax
  proceedings and the auditor formula's CARO / disputed-tax clauses, acknowledged inputs with
  **no consuming metric**, status `BLOCKED — UNRESOLVED (A26, A27; Ramki)` — recorded as an
  open gap, explicitly *not* as an approved permanent non-score (the file's status vocabulary
  `DONE / DONE (documented divergence) / BLOCKED` is reused, not widened). Row 11 notes that
  `litigation_bucket`'s party population is enforced by the extractor as the config's own text
  states it, with the two new tests cited.
- **Validation, all executed on the tree this commit carries.** Focused pair
  `tests/test_litigation_regulatory_defaults.py tests/test_hd_fire_primary_source_extraction.py`
  → **96 passed, 0.22 s**; 9-module extraction/governance/golden battery → **170 passed,
  338.57 s**; **full backend suite → 1288 collected, 1288 passed, 0 failed, 0 skipped,
  1272.03 s (21 m 12 s), EXIT=0** (1265 → 1288 = the 23 tests added; nothing removed, skipped
  or xfailed); `check-config` → `valid True`, 10 profiles at 100 points; frontend
  `node --test` → **90 pass / 0 fail**. Progress was visible via `tests/pytest_progress.py` in
  the run log; Arena's `bash` still returns output only at completion, so the full run was a
  background process writing one fresh log (§17.4/§17.6).
- **Integrity.** `git diff --stat 2d52baa..HEAD -- config schema fixtures build evidence` is
  **empty**: no config, schema, golden fixture, workbook or stored evaluation changed; the
  vishal golden hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` and
  its `final_score 35.0` pass unchanged; formulas, weights, thresholds, caps, penalties,
  knockout semantics, the bucket taxonomy and both config versions are untouched; **no
  historical evaluation was re-run, re-hashed or newly published**. Three fixture expectations
  moved because the approved rule moves them (class_b 41.0 → 37.0, class_b provenance floor
  9 → 8, and the three wording tests), each re-pinned with its reason and the approval cited at
  the pin, and the A24 §13 table records the measured before/after pairs.
- **Open after this pass.** A26 (tax-only classification) and **A27** (auditor criterion's
  unconsumed CARO / disputed-tax clauses) are **PROPOSED / UNRESOLVED**; **A8-R** R-S1…R-S10
  remain **UNRESOLVED** (A25-D2 supplied the in-document half of R-S6; external corroboration,
  K2's basis field and every retrieval decision are still Ramki's, and A8-R §7 states why the
  K2 field should follow R-S1 rather than precede it); A24's Option C (KMP / Senior Management)
  is not adopted; `main` and PR #6 are untouched by design.

### A26 / A27 / A8-R decision preparation (read-only; no status changed) — 2026-10-20

- **What was done.** A read-only evidence pass to prepare, not decide, the three
  open governance questions. It produced
  `docs/investigation/A26-A27-A8R-DECISION-PREPARATION-2026-10-20.md`, labelled
  **PROPOSED / FOR RAMKI REVIEW**, with per-question answers, an options
  evaluation, an inventory of declared-but-unconsumed governance inputs, a
  provision-by-provision A8-R assessment (R-S1…R-S10), one cross-cutting decision
  matrix, 15 numbered questions for Ramki, and seven proposed amendments to
  existing records — **none of which was applied**.
- **Authority honoured.** A26, A27 and A8-R are untouched and remain
  `PROPOSED / UNRESOLVED` and `UNRESOLVED`; no option was adopted; no bucket,
  mapping, coverage basis, config version, schema change, golden re-pin or
  extraction change was made. The A24/A25 implementation published at `41f2f86`
  is unaltered. `main` and PR #6 (open, unmerged) are untouched.
- **Findings worth the tracker's attention (details in the report).**
  (1) *Tax*: v1.5 never gave tax a scored state anywhere — §4.3 `:253` collects
  it, §11 (`:547-558`) does not mention it, and a sweep of all 30 criteria finds
  **no criterion consuming contingent liabilities**, so K5 prices magnitude as a
  binary knockout and the `eom_caro` penalty (from reviewer-supplied
  `eom_materiality`) prices severity; the "disputed tax" wording in both shipped
  configs is v1.3/v1.4 inheritance, i.e. stale text, not a dropped v1.5 rule.
  (2) *CARO*: `caro_remarks` is declared at `ipo-input.v1.5.schema.json:659` with
  **no consumer, no extractor and no test** — the only "CARO" in engine code is
  inside the auditor formula *string* — so §11's `EOM/CARO only` state is
  unreachable for an unqualified-plus-CARO filing, which scores `clean_reputed`;
  `eom_only` today fires on auditor *reputation* (the RK reconciliation's "label is
  semantic misnomer"). A wording fix still costs a config version and a golden
  re-baseline, because the formula string is inside `config_fingerprint` and inside
  `fixtures/vishal_nirmiti/expected_derived.json:34`.
  (3) *A8-R*: five governance fields are declared with no consumer
  (`eom_count_3y`, `auditor_change_count_3y`, `caro_remarks`, `regulatory_actions`,
  `independent_director_count`); the governed carriers for external evidence
  already exist (`_sources`/`_evidence`/`_cross_checks` with
  `CROSS_SOURCE_DIVERGENCE`, `supplemental-enrichment.v1` with dual timestamps and
  content hashes), so "no new fields" is a real option; `RUNBOOK.md` §9 states the
  engine "never makes a network call" and `issue_terms` is imported only by the
  presentation layer, so any retrieval belongs upstream of `evaluate`; a K2
  coverage-basis *field* is not the minimum change — the open decision is whether
  any basis may clear K2 at all; and a proposed **R-S11** (SEBI and ED coverage
  must be established independently) is missing from the current provision list.
- **Validation run and why.** `python3 -m pytest tests/test_litigation_regulatory_defaults.py
  tests/test_hd_fire_primary_source_extraction.py -q` → **96/96 passed, 0.21 s**, and
  `python3 engine/tools/ipo_screen.py check-config` → `valid True`, 10 profiles.
  Both are read-only confirmations that the behaviour quoted in the report is the
  behaviour of the published tree. The full suite was **not** re-run: nothing in
  this pass changes implementation, so a full run could not validate anything new
  (the last published full run remains 1288/1288 passed at `41f2f86`).

### A26 / A27 / A8-R one-pass convergence — 2026-10-20

- **Authority / scope.** Current one-pass instruction authorizes bounded specifications,
  a consolidated non-scoring audit, focused tests and publication. It explicitly adopts
  A26's safe interim UNKNOWN posture and retains current K2 policy. It does not approve
  CARO scoring implementation, new evidence thresholds, new fields, or external K2 authority.
  This entry supersedes only the preceding entry's statement that no interim option
  was adopted; earlier historical records remain unchanged.
- **A26 actual disposition: INTERIM UNKNOWN ADOPTED under the current task instruction.**
  Tax-only proceedings that cannot reliably fit an approved bucket remain UNKNOWN,
  neither scored zero, clean nor automatically adverse. Independently supported K5
  and auditor treatment continue. No runtime change was needed or made. Permanent tax
  dimension/calibration remains UNRESOLVED. Corpus requirements now cover sampling,
  readability denominators, party/direction, outcomes, amounts, overlap and review.
- **A27 specification PREPARED, not implemented/approved policy.**
  `docs/investigation/A26-A27-A8R-CONVERGENCE-2026-10-20.md` records six CARO/EOM
  evidence states, current and proposed branch precedence, future acceptance cases,
  two exact prospective wording options, and four calculated wording-only config
  fingerprints using in-memory copies. Supplied materiality=none gives scored 0;
  absent/null remains UNKNOWN with reserve 3, not an applied -3 penalty. This does
  not prove independent review of none. Existing -1/-2/-3 magnitudes remain unchanged.
  The missing/ambiguous/unavailable CARO clean-branch gate remains a real scoring
  decision: compatibility and evidence-complete options are explicitly not adopted.
- **Hash/version precision.** Both config copies contain stale disputed-tax wording;
  no config was edited. Config text changes config_hash and hence result_hash even
  with unchanged scores. Code formula strings, not config formula strings, populate
  expected_derived/expected_score. Old goldens are not automatically to be re-pinned:
  preserve old-version tests and separately authorize any new-version baseline.
  Numerical future result hashes were not fabricated or evaluated without a full
  deterministic payload. No historical evaluation was rerun.
- **A8-R acceptance specification PREPARED; K2 authority UNCHANGED.** Six regulatory
  states formalized; independent SEBI/ED, authority, matching, periods, completeness,
  partial/blocked/empty results, dual timestamps/hashes, conflicts and reproduction
  covered. Existing carriers assessed first. Numeric CROSS_SOURCE_DIVERGENCE is
  not a regulator-flag conflict resolver; existing source-type/section contracts
  do not by themselves authorize external regulator integration. No new field,
  source class, connector, retrieval or knockout interpretation was introduced.
- **Five-input audit COMPLETED (inventory, not remediation).** No named engine or
  downstream semantic consumer or extractor found for eom_count_3y,
  auditor_change_count_3y, caro_remarks, regulatory_actions, independent_director_count.
  Direct JSON canonical input retains them; the extraction-builder governance
  allowlist omits them, verified by focused tests. Generic retention is not scoring
  consumption. Unknown intent remains unknown; no “every declared field must be
  scored” lint or schema removal was adopted. New audit tests are not evidence of
  a production consumer.
- **Checks:** initial focused run 116/116 passed in 0.28 s; after adding pathway and
  CARO non-consumption checks, final run of test_governance_contract_audit.py,
  test_auditor_tenure_defaults.py, test_litigation_regulatory_defaults.py and
  test_hd_fire_primary_source_extraction.py: **122/122 passed in 0.33 s**, including
  **17 new audit checks**; existing progress plugin reported 100% completion.
  `python3 engine/tools/ipo_screen.py check-config`: **valid True, 10 profiles**.
  Full suite deliberately not rerun: no application/config/schema/fixture change.
- **Remaining authority boundaries:** qualifying CARO remarks and absent-state scoring,
  evidence sufficiency, exact deployed wording/version and any new-version baseline;
  permanent tax scoring/calibration; named external authority/coverage/freshness and
  categorical conflict policy; any future external K2 trigger/clear authority.
  These remain PROPOSED / UNRESOLVED, not blanket-approved by standing PA.
- **Publication scope:** this additive tracker entry, the new convergence document,
  and tests/test_governance_contract_audit.py only. Protected implementation, configs,
  schemas, fixtures, decision records and historical artifacts are unchanged.
  main remains untouched; PR #6 must remain OPEN / UNMERGED. Remote commit/content
  verification is performed after push and reported in the completion response.

### Runtime tested-tree identity and test convergence — 2026-10-20

- **Verified target:** e7b588cffb8a2155c9a0041b2134d34144b371fd; runtime implementation
  41f2f86909fa4495b3c9d735d897c00bb20843b4 includes A24/A25 parser, party coverage,
  disclosed-negative semantics and page-read observability. Initial tree clean.
- **Previous full run applicable:** recovered actual full_a24.log records 1288
  collected/passed, 0 failed/skipped, no xfail/xpass reported, 25 warnings,
  1272.03 s, EXIT=0. Corroborated with contemporaneous d1be6d2 tracker/RUNBOOK,
  commit/reflog timing and unchanged Git trees for engine/frontend/config/schema/
  fixtures/evidence/dependencies/harness. Original log lacks a HEAD header; that
  limitation is explicitly documented rather than disguised as original attestation.
- **Intervening coverage:** changed paths are docs, one test name/docstring and
  17 audit checks. Normalized AST of the older test module is identical; current
  collection is 1305 = 1288 + 17. Full backend deliberately not redundantly rerun.
- **Executed now:** focused backend 122 passed in 0.27 s (0 failures/skips, no warnings
  reported); frontend npm test 90 passed, 0 failures/skips/cancelled/todo in
  656.435112 ms; check-config valid True, all 10 profiles 100 points. Collection
  1305 tests in 0.56 s, with existing Starlette/httpx deprecation warning. No full
  1305-pass claim is made. Exact commands, UTC timings, logs and object IDs are in
  docs/investigation/runtime-verification-2026-10-20/REPORT.md and adjacent artifacts.
- **Progress/failures:** initial update before investigation, equivalence update
  before tests, plugin milestones through 122/122, and completion update. No stalls,
  failures, runtime corrections or weakened tests; no long suite started this pass.
- **Preservation:** no scoring, knockout, evidence-policy, config, schema, fixture or
  historical-evaluation change. Existing A26/A27/A8-R authority boundaries remain.
  Only evidence artifacts and this append-only tracker entry are published; remote
  verification follows push. main stays untouched; PR #6 OPEN/UNMERGED is required.

### HD Fire reported 7.0 → 3.0 regression investigation — 2026-10-21

- **Baseline/recovery:** remote tip c4d9d5d6b38facde9adfb96898ba5d52a6c2b536.
  Re-provisioned local HEAD was main's 01ba66c on this working branch with published
  files mostly untracked. All 410 target files compared byte-identical before
  staging only matching paths and a normal --ff-only merge restored c4d9d5d.
  No reset, overwritten file, forced switch, deletion or force push.
- **Primary finding (evidence-qualified):** earlier documented base10 - receivables3
  =7 versus current supplied base6 - receivables3 =3 reconciles exactly with D3/A21
  removing unsupported promoter post-holding4. Preserved HD Fire source shape has
  pre95.33+4.67, post placeholders; 2ec607c correctly prevents pre→post reuse.
  Exact old/new payload parity is NOT proved: neither persisted record is present.
- **Litigation discrepancy remains UNRESOLVED, not explained away as A24/A25:**
  earlier docs record adverse SCORED0, not clean4. Current summary says UNKNOWN.
  Existing HD Fire §12 reconstructed table test still yields criminal_or_regulatory
  for two cases against Directors, even though Company/Promoters say nil and
  Company-initiated tax3 is not adverse. Positive finding precedes clean coverage
  gates; missing current page/range/header/read-status prevents identifying the
  exact current extraction/input predicate. It changes availability, not earned
  score, on the documented comparison. 27→19 available matches promoter4+litigation4.
- **Penalties:** no supported prior auditor/CFO applied -3 in the reference run;
  earlier docs already identify receivables as the applied item and auditor exit
  UNKNOWN. Current auditor UNKNOWN has zero applied and reserve3, not a clean
  finding. Receivables -3 was also recorded previously; actual issuer balances,
  FY pairing/days and provenance are unavailable, so its correctness is UNVERIFIED.
  Column/FY/stub/threshold contracts tested; not used to certify missing inputs.
- **Evidence limit:** no full current attachment, old/new evaluation payload/manifest,
  HD Fire PDF or evaluation-store override found. Only task summary plus preserved
  investigation/source excerpts available. Full current KO/other-module/penalty/bound
  details cannot be inspected. Report distinguishes user summary, historical prose,
  reconstructed primary-source shapes and current code/tests; no history fabricated.
- **Artifacts:** docs/investigation/hd-fire-regression-2026-10-21/REPORT.md contains
  executive findings, causal matrix, exact paths/commits, field values and missing
  values, corrective categories and residual evidence requirements. Raw focused
  and config logs adjacent. tests/test_receivable_period_contract.py adds eight
  synthetic layer cases (not a new HD Fire evaluation or historical-score target).
- **Checks:** initial pytest attempt blocked before collection by missing pytest;
  isolated .venv installed pinned requirements without manifest changes. Final
  focused seven-module run: **137 passed, 3 deselected, 0 failed/skipped/xfail,
  0.44 s, EXIT0**, progress through 137/137. Deselections are unrelated live
  Jio/Vishal cases. check-config **valid True, 10 profiles**. No full rerun needed
  for docs/test-only changes. No actual regression test failed; no test weakened.
- **Disposition:** keep D3/D5/A23/A24/A25. No current runtime defect sufficiently
  established for a patch; no scoring-policy change. Current score arithmetic
  explained conditionally; full current result NOT certified merely by green tests.
  Missing litigation-path and receivables source evidence remain concrete blockers.
- **Preservation/publication:** no HD Fire evaluation, re-ingestion, source fabrication,
  runtime/config/schema/golden/history change. Only report/logs/new test/additive
  tracker entry published on existing branch. Main untouched and PR #6 OPEN/UNMERGED;
  exact remote commit and content verification follow push in completion response.


## 2026-10-21 — Platform-wide issue-term discovery/resolution implementation

- **Scope:** shared runtime across IPOs; Jio is regression/research evidence only.
  Traverse every configured provider/listing even after cache success; isolate
  provider exceptions; independently normalize/select/conflict price floor/cap,
  lot, fresh/OFS monetary amounts and issue dates. Preserve original field source
  IDs/quotes/URLs/times; do not misattribute a merged fact to a primary document.
- **Authority/readiness:** platform candidates remain UNVERIFIED/MARKET_DATA;
  opt-in public Dhan/Groww/Angel One/INDmoney adapters follow actual matching
  listing/detail links, never guessed private APIs. Existing official authority
  governs selection. Invalid fields do not discard other valid fields. Canonical
  assembly retains partial facts, but actual required fields (including monetary
  fresh amount/dates) are checked before normal evaluation. No scoring/validation
  bypass or new provisional-evaluation semantics. Legacy pricing-stage RESOLVED
  is not readiness; service reports remaining_required_fields/ready separately.
- **Correctness:** reject bad/nonfinite/fractional lots and malformed amounts;
  reject explicit other-issue windows; retain official conflicts and unverified
  disagreements; compare explicit monetary units using existing multipliers.
  Strict JSON diagnostics render rejected nonfinite values as strings, never as
  zero/canonical facts. Date-only public detail candidates remain unverified.
- **Frozen preservation:** the first implementation touched the frozen notice
  parser and correctly failed hash checks. That file was restored byte-for-byte
  (SHA-256 779afb0b1ba309913974edee4c09109b4e4da2806c3e49277e902e86a7c994e4);
  new exchange-page payload fields live in an unfrozen subclass. No pin, scorer,
  threshold, weight, knockout, config/schema, golden/hash or history is rewritten.
  Synthetic notice windows in integration tests now match the unchanged real RHP
  programme, while stale-window rejection/manual precedence assertions remain.
- **Tests:** intermediate full run 1,320 passed/15 failed, 28 warnings, 1499.12 s;
  all fifteen failures explicitly rechecked: 15 passed/3 warnings/293.00 s.
  Two in-progress full runs were stopped for demonstrated format/JSON/date-only
  gaps; retained logs are NOT passes. Final focused: 82 passed, 3 deselected,
  31.89 s. Final complete backend: **1,355 passed, 0 failed/skipped, 25 deprecation
  warnings, 1614.73 s, EXIT 0**; includes excluded focused integrations. Frontend
  **90 passed/0 failed**. Config **valid True, 10 profiles, 100 points each**.
  Final 209-file source/test manifest rehashed unchanged after full completion;
  SHA-256 26581f84734a80d49502193bb8d6f4eb9b84472e7f968cad131b0bb46e87b599.
- **Live boundary:** official NSE/full-query BSE detail corroborate research-tool
  price/lot/dates; platforms disagree on dates. Read-only engine transport failed
  all fifteen actual URLs with TLS EOF; research-tool access is not runtime live
  verification. The BSE price-band advertisement ZIP was discovered, not declared
  unpublished; tool retrieval returned HTTP 500, ZIP extraction is unsupported,
  and listing.bseindia.com is not silently added to official authority. Other
  current markup/alias limits and the unverified monetary fresh amount remain
  explicit. No Jio live readiness/evaluation is certified; no real IPO evaluation
  was persisted for this investigation, and no HD Fire production action occurred.
- **Artifacts:** docs/investigation/issue-terms-platform-2026-10-21/ contains the
  architecture/readiness report, exact live citations/quotes/conflicts, final and
  intermediate test logs/manifests, config/frontend checks and reproducible
  read-only transport probe/results. README and verification ledger distinguish
  implementation from outstanding live/provider/archive acceptance.
- **Publication boundary:** existing branch arena/95234306-ipo-screening-engine;
  main still 01ba66c12ca1195fd7acbd287c3e39a019808094 at pre-publication check.
  PR #6 OPEN/unmerged and head/base unchanged (it is on another existing branch,
  not this session branch). Commit/push and remote byte/SHA/main/PR/worktree
  verification follow this append-only entry; actual SHA is in completion response.


## 2026-10-21 — Async ingestion worker/durability correction; Windows cause OPEN

- **Observed report:** ing-bbd84e84a1f24abd on Windows PID 11272 stayed RUNNING
  with two upload events. No actual process stacks, deployed module identity,
  ingestion JSON or local exception logs are accessible in Arena. Do not certify
  the exact local root cause or claim this PID/record was remotely repaired.
- **History:** latest remote cb5c5e595557ed79f5f78bbc3150ac42b5cd7f88 changes
  issue-term discovery after validation/extraction. The defective daemon wrapper
  dates to 22f82b8; no causal link from latest provider changes to the two-event
  stall is proved. Earliest confirmed persisted frontier is upload SUCCEEDED;
  the actual stopped Python operation is unknown without local stacks.
- **Demonstrated defect:** two injected activity-write failures through the real
  baseline ingestion error path cause the worker to exit silently, leaving exactly
  two durable upload events, RUNNING, no error/finish/evaluation ID. The old outer
  except Exception:pass assumed terminal reporting never failed. It also missed
  SystemExit, dispatch failure and workers returning without terminal results.
  Terminal memory state could differ from disk after a failed final save.
- **Correction:** service worker-entry event; dispatch/escaped-worker/incomplete
  fallback terminal failure with correlated traceback logging. Preserve inner
  blocked/failure/success and reconcile terminal snapshot with disk; bounded retry
  persists that same snapshot rather than processing/evaluating again. API 202
  acknowledgement uses actual activity status rather than unconditional RUNNING.
  No superficial UI polling change, arbitrary live-thread timeout or false success.
- **Evidence:** baseline two-event storage-fault reproduction stays RUNNING; fixed
  reproduction becomes durable FAILED/INGESTION_WORKER_FAILED. Repository Jio PDF
  SHA256 72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d
  reaches BLOCKED/AWAITING_ISSUE_TERMS under both dispatchers (32.05/31.73 s),
  providers empty, no network/evaluation/persistence. Windows byte identity unknown.
- **Validation:** first regression run 4 failed/2 passed (6.53 s); separate terminal
  memory/disk regression failed before refinement. Final focused 23 passed,
  3 deprecation warnings, 1.84 s. Final full backend **1,368 passed, 0 failed/skipped,
  25 deprecation warnings, 1653.21 s, EXIT 0**. Frontend **90 passed/0 failed**;
  Python/JS syntax and ten-profile config validation EXIT 0. Final 210-file manifest
  unchanged after full run; SHA256
  0e3fa79105b2bdfea1442d591f1150edcc7b6d0fbe4a94affb2423e3a944db9a.
- **Non-green checks disclosed:** standard mypy 2.4.0 exits 2 on duplicate module
  discovery, identical at baseline. Limited modified-module check exits 1 on two
  existing None.get read-model errors, identical normalized baseline diagnostics.
  npm run build exits 1 (no build script; static frontend served directly). No
  type suppression, unrelated cleanup or artificial build step added to claim pass.
- **Remaining boundaries:** exact Windows cause OPEN; obtain original JSON/logs,
  deployed commit/module/PDF identity and current-PID Python thread dump before
  restart. No old ingestion record rewritten. Live blocked threads, abrupt process
  death and permanently unwritable activity storage are NOT claimed solved; no
  unsafe timeout marks FAILED while a live worker might later persist. This is a
  verified bounded repository correction, not full local-stall investigation closure.
- **Artifacts:** docs/investigation/ingestion-worker-stall-2026-10-21/REPORT.md,
  reproducible baseline/current scripts/results, before/final test logs, type/build
  evidence and frozen manifest. Temporary isolated tests only; no production IPO,
  Jio or HD Fire evaluation/history mutation, scoring/config/schema/golden change.
- **Publication:** existing arena/95234306-ipo-screening-engine only; main untouched,
  PR #6 OPEN/unmerged, existing head/base unchanged. Final commit/push and independent
  remote byte/SHA/tracker/main/PR/worktree verification follow this append-only
  entry; exact publication SHA appears in the completion response.


## 2026-10-21 — Published worker Windows regression corrected (separate from live stall)

- **Scope:** reported c32e3a7 genuine-evaluation/API-history lifecycle failure
  (user Windows cherry-pick f4b3174). Earlier PID 11272/live-ingestion stall cause
  remains OPEN; this correction does not claim to diagnose that incident.
- **Native reproduction:** hosted Windows/Python 3.11 run 39599814603 explicitly
  checked out c32e3a7 and reproduced the exact terminal helper line-21 NoneType
  failure: 1 failed/12 passed. Logged actual Path.read_text PermissionError(13,
  'Permission denied'), winerror=None, swallowed by store.get's broad catch as
  missing. Hosted Linux baseline passed five repetitions of the unchanged 13
  cases. This is actual Windows-runner evidence, not access to the user's G: drive.
- **Correction:** implementation b6230bb421153c75b9e1010d16bb89860d5dcc1c;
  same-store save/get/history/prune serialized with RLock to prevent read/open
  overlap with destination replacement. get maps only FileNotFoundError to None;
  actual I/O/JSON faults propagate. Worker terminal reconciliation logs read
  failure then uses existing trusted-snapshot durable recovery, no reevaluation
  or fabricated success. Lock is process/instance local, not cross-process or a
  cure for external/permanent storage denial. No kernel handle trace collected.
- **Regression coverage:** original 13 lifecycle tests/helper, 2-second deadline,
  actual evaluation persistence and API/event assertions unchanged. Four new
  portability cases failed before correction, passed afterward; blocked-writer
  get/history readers wait and observe durable terminal state, unreadable/corrupt
  differs from genuine absence. Two isolated read-error recovery checks pass,
  verifying logging, exact durable BLOCKED snapshot, no duplicate finalization.
- **Validation:** focused Linux 27 passed/3 deprecation warnings/1.86 s. Native
  corrected CI run 39600318064 on implementation SHA: Windows 20 x 27 = 540
  successful case executions; hosted Linux 5 x 27 = 135, both jobs SUCCESS.
  Full applicable Linux backend: **1,372 passed, 0 failed/skipped, 25 deprecation
  warnings, 1162.60 s, EXIT 0**, one complete run. Python syntax and correct CLI
  config check EXIT 0 (ten profiles). Initial wrong CLI module invocation failed,
  retained and disclosed; not counted as success. No current frontend/type/build
  result claimed; prior report's results/blockers remain historical.
- **Preservation:** no scoring/weights/thresholds/knockouts, authority/issue-term
  fail-closed logic, schema/config, golden, frontend, production evaluation/history
  or runtime-logs changes. 212-path tested manifest unchanged after full run;
  SHA256 526b2a7d083de82f0af41ae1a7c333e89ac693b84320cfd834520c5f03e44cd9.
  This entry appends without changing any prior tracker bytes.
- **Evidence:** docs/investigation/activity-storage-windows-2026-10-21/REPORT.md,
  native baseline traceback/check annotations and pinned workflow, corrected CI
  metadata/success annotations, before/focused/full logs, supplemental recovery
  script/log and frozen tested-tree.json. Baseline CI log-download redirect was
  inaccessible; allowed GitHub API check annotations retain the exact traceback.
- **Publication:** only existing arena/95234306-ipo-screening-engine. Main remains
  01ba66c12ca1195fd7acbd287c3e39a019808094; PR #6 OPEN/unmerged with existing
  arena/5dd3fe52-ipo-screening-engine head e05c0efbca1ecb3024e52da73a22e180ea171118
  and arena/573e69a4-ipo-screening-engine base. Final evidence commit SHA and
  independent remote source/artifact/tracker/main/PR/worktree verification follow
  in completion response. No reset/clean/amend/force-push/merge/retarget used.


## Automatic official discovery / Jio ingestion — 2026-10-21 (current session)

**Controlling status: PARTIAL IMPLEMENTATION — end-to-end acceptance remains BLOCKED, not completed.** Session branch `arena/95234306-ipo-screening-engine`; final runtime `a3279506b6cee66482135324528a56b6264826a9`. The settled Windows worker correction `b6230bb` and evidence `6c871e5` are preserved, not reopened. The separate user's PID 11272 remains undiagnosed from Arena.

### Implemented and actually verified

Automatic exact-name NSE feed → symbol/detail API → linked official archives now feeds the existing field resolver, canonical mapping and evaluation gates, without configured Jio URLs, issuer-specific price/lot constants, manual-term substitution, or fixture-as-live evidence. Parent referrers/cookies/full query strings and redirect eligibility are preserved; shared page chrome no longer by itself vetoes an actual issue detail table. Archive hosts are scoped to issuer-matched discovery; the existing direct notice/Prospectus host allowlists remain intact. GID hypothetical ₹20/₹24 examples are rejected outside the frozen parser. Issuer/CIN/complete-table RHP qualification reads the actual graphical-title cover without inventing a date; Draft RHPs are not promoted into current RHP authority.

Bounded bundled-model offline OCR retains original PDF hash/URI/page/method/confidence. Full-width primary heading reads avoid cropped issuer fragments, without letter stitching; financial fields still come from independent original crops. OCR price quotes lacking an explicit matching INR/Rs/₹ token remain **UNVERIFIED**, rather than treating face-value multiples/currency-free chart fragments as verified rupee prices. This rule does not compare against a preferred source or weaken genuine verified-value conflict checks. No numeric repair, share-count-to-cash inference, reservation subtotal substitution, or absent-OFS-to-zero default was introduced.

### Controlling actual live result — NOT acceptance success

Native Windows workflow **39623461399**, structured [check **119308926882**](https://github.com/ramkivs/ipo-screening-engine/runs/119308926882), runtime `a3279506b6cee66482135324528a56b6264826a9`, actual repository Jio RHP + actual production public HTTP, temporary stores only:

- **`ing-a166a462042145f0`**, finished **2026-10-21T15:24:10.302542Z**: **BLOCKED / AWAITING_ISSUE_TERMS**, resolver PARTIAL, ready false, **missing only `fresh_issue`**, **no qualified conflicts**.
- Actual NSE detail verifies **₹1,065–₹1,119, lot 12, open 21 Oct / close 23 Oct 2026**; response SHA-256 `6dd90082c35315150d89b956ae1119ccca2c93879663794a6981bbcafa17bdb4`. Actual issuer RHP verifies **explicit OFS 0**, SHA-256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d` (matches the repository PDF, not proof of identity with an unavailable user upload).
- **evaluation_run=false, evaluation_id=null, persisted=false. No automatic Jio evaluation/persistence success is claimed.**
- **Fresh monetary amount is unestablished, not proved unpublished.** The RHP has `₹[●] million`; NSE's ₹5,000 million employee / ₹25,000 million shareholder reservations are not fresh total cash. ET/MT scanned notices now parse issuer/lot/dates, but produce no qualified fresh monetary field; TOI exceeded the bounded OCR read budget in this final run. Discovery took 567,454 ms. These are explicit extraction/readability limitations, not authority to infer cash or ask for manual values.
- BSE classic listing/publicissue/full-query issuer detail paths still return a 14,287-byte Angular shell; the BSE newspaper archive attempt timed out. BSE transport is **not restored**. Research-only old API URL attempts resolved to a Show Interest form; no form/contact/registration was submitted or access controls bypassed. SEBI listing returned 404. Generic shell/retrieval failures are not proof of non-publication; the actual issuer-specific NSE route was attempted and consumed.

### Validation, exact scope and preservation

Complete broad backend: **1,395 passed, 25 warnings, 1,210.12 s**, snapshot `dab7b7604af5367ae1d1bb38a20546f1f61229fc` / `tested-tree-backend.json`. A prior complete run's one authority-boundary failure (direct Prospectus allowlist broadened by archive hosts) was fixed; the unchanged test and added scope regression pass. The broad run is **not misrepresented as a full rerun of the later source**: the later delta is limited to `official_notice_ocr.py`, `official_offer_amounts.py` and their discovery test file, covered by **124 focused tests passing (6 deselected, 3 warnings)**, real Linux offline OCR **1 passing (24 deselected, 5.65 s)**, native Windows focused + real OCR steps, and the actual live terminal check above. Frontend **90 passed**; active v1.5 configuration valid (10 profiles), compile checks, dependency check and code/documentation diff checks pass (raw pytest-log whitespace is retained). Both source manifests are retained; final `tested-tree-final.json` covers 291 validation paths.

No scoring formula/weight/threshold/knockout/taxonomy/config/schema/golden/hash authority changed; frozen `price_band_notice.py` is untouched. No HD Fire live ingestion, reevaluation, persistence or historical mutation was performed; native Jio writes are confined to temporary stores. No main/PR #6 change, amend, reset, force-push, branch switch, or unrelated/runtime-log cleanup. Main remains `01ba66c12ca1195fd7acbd287c3e39a019808094`; PR #6 stays OPEN/unmerged, head `e05c0efbca1ecb3024e52da73a22e180ea171118` on `arena/5dd3fe52-ipo-screening-engine`, base `arena/573e69a4-ipo-screening-engine` unchanged.

**Remaining authorized implementation work:** establish the fresh monetary amount from qualifying issuer-matched official evidence through reliable document extraction/appropriate actual official retrieval. Do not call it unavailable on the basis of shells or unreadable scans, request manual issue-term entry as a discovery workaround, derive cash from shares × cap, suppress genuine conflicts, or lower validation/scoring authority to reach persistence.

Report and actual source/terminal evidence: `docs/investigation/automatic-official-discovery-2026-10-21/REPORT.md`, `final-native-result-check.json`, `final-native-ci.json`, `source-remote-verification.json`, both validation manifests and associated logs. The source remote receipt rereads GitHub commit/tree blobs and the actual native result independently; the final handoff records the documentation/evidence publication SHA after final remote tree/blob verification. This entry supersedes no settled D1–D5/A23–A26 decisions and does not turn blocked acceptance into completion.

## One-pass Jio recovery follow-through — 2026-10-21

**Controlling current outcome: B / restoration INCOMPLETE — authoritative fresh-cash evidence/access boundary, not a successful evaluation.** This append updates the earlier partial-implementation entry without changing its historical bytes or settled policy.

- Required start `0d1d48ba2c04f9a7b306e53c330dd3701559820e` preserved. Published runtime **62bad2c33464f7e8c7cc3c35368d97cff1295486** corrects current published BSE structured protocol/session/JSON headers and full query/provenance, bounded 180–270s OCR/full child-error logging, original amount confidence, lossless original/discovered field evidence and truthful terminal/UI guidance. No manual-value workaround or relaxed authority.
- **Actual native Windows API** [39636184160](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39636184160): **ing-75d3241aa25f40c0**, finished `2026-10-21T16:41:43.652466Z`, **BLOCKED / AWAITING_ISSUE_TERMS, missing only issue.fresh_issue**, evaluation_id null/evaluation_run false/persisted false. Independent HTTP GET after server restart is identical; GET evaluation lists before/after restart both empty. No persisted evaluation/result hash or successful duplicate-upload idempotency is claimed. Green workflow means checks/diagnostic executed, not restoration success.
- Actual price **1065–1119**, lot **12**, dates **2026-10-21/23** from exact issuer NSE JSON SHA **6dd90082c35315150d89b956ae1119ccca2c93879663794a6981bbcafa17bdb4**. Independent native source refetch retains/recomputes original bytes/hash. Original RHP p1 explicit OFS “Not applicable” **0**, confidence1, survives lossless readback and official same-PDF corroboration; no reproduced loss/default/historical rewrite. Official RHP SHA **72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d** matches repository PDF, not proof of unavailable user-upload identity.
- All three actual newspaper OCR invocations succeeded (ET87.125s/MT82.344s/TOI83.235s, each270s budget/5pages60segments); raw fields/confidence/exception/metadata retained. GID hypothetical examples explicitly rejected. Operative newspaper cash clauses visually retain ₹[●]million; unqualified OCR price fragments remain UNVERIFIED. No claim that a larger timeout caused runner speedup or reconstructed original ing-0168 traceback.
- Independent **additional official document** audit 39637496894: pre/post-anchor parameters (5+5 native pages), four forms and standalone abridged prospectus (81 native pages), all exact document hashes/full bounded native text retained. Forms p3/abridged p1 explicitly retain fresh cash placeholders; parameter reservation/max-bid values are not fresh total. Anchor report initially marked image-only, **then actually reviewed** in native39638363459: all18 original pages OCR,101.266s, raw confidence/no repairs, original operative p1 visually verified as **anchor allocation**, not fresh total. Research-only documents were not falsely relabelled/promoted into application term candidates. Original PDF/all images retained in artifact; no unreadable document called searched absence.
- Actual current BSE endpoint `/GetPublicIssue_par_updated/w?flag=1`, published by the current SPA, returns **HTTP403 even with corrected production transport** in independent source audit and final API run. No BSE issuer rows obtained. Shell/403/SEBI404/earlier archive timeout are not proof of non-publication. Available authoritative documents do not establish fresh cash; not a claim that no other applicable publication exists. No shares×cap, reservation/anchor subtotal or hypothetical source substitution.
- **Only focused validation this iteration:** Linux Python3.11.2, seven relevant Python files **131passed/6deselected/3warnings/3.03s/exit0**; two related Nodev22.22.3 activity files **8passed/0failed/122.11878ms/exit0**. Same focused commands succeeded in native Windows job; actual Windows Python3.11.9/RapidOCR3.10.0/ONNXRuntime1.24.4/pypdfium2 5.14.0/pypdf6.20.1. Compile/scoped diff checks exit0. Controlled conflicting-verified/unresolved API, explicit-NIL, strict BSE identity/shell/403 and OCR error safety remain covered. **No broad backend/matrix/unrelated frontend/build**; historical broad results are not current proof.
- Exact original **ing-0168a590a93c4448** build/upload/trace still unavailable after search/one request; not diagnosed from hosted reproductions or thread counts. No user PID/browser/G: drive access claimed. Scoring/config/schema/goldens/frozen parsers/settled decisions/HD Fire and production history preserved; unrelated untracked evidence retained, no cleanup/reset/amend/force/branch switch. Main/PR6 remain untouched and independently reverified on publication.
- Full report, exact commands, live/source/anchor evidence and repeatable remote readback: **docs/investigation/jio-recovery/REPORT.md**. Evidence publication gets a separate append-only remote-readback receipt; final response supplies final SHA/readback. Remaining: obtain qualifying authoritative fresh cash, then real evaluation/persisted hash/provenance/GET and success duplicate verification. **Do not manufacture success or treat missing evidence as zero/non-publication.**

## Official-notice OCR segmented-heading CI failure — root cause and fix — 2026-10-23

- **Symptom:** every CI run on this branch since the Jio correction integration was red for exactly one test, `test_image_only_official_notice_uses_real_offline_ocr_and_preserves_original_pdf_hash` (1670 tests, 1 failure, on `e612702`, `589e468`, `97b970e`, `af38fcf`; the documentation-only run `39950370576` on `3cb38a5` reproduced it too). All other workflow steps passed, and the same commits passed 1670/1670 locally.
- **Root cause:** OCR word segmentation, not name matching. The runner emits `INITIAL PUBLICOFFERINGOFACMEFORGELIMITED` with no space before `LIMITED`; `_primary_issuer_header()` needs a standalone name line plus an identity block, and the frozen parser's fallbacks need either spaced `INITIAL PUBLIC OFFERING OF` or whitespace before `LIMITED`, so `company_name` was `None`. `_norm_name()` already ignores spacing. The merged text also broke `aggregating up to` (fresh issue 240) and `Offer for Sale … Not applicable` (OFS 0), which the first failing assertion hid.
- **Fix (Option B, narrow extraction correction):** in `engine/ipo_screening/extraction/official_notice_ocr.py` only — a single `_restore_heading_spacing()` applied to both the identity header and the financial tiles; fixed vocabulary extended with `AGGREGATING UP TO`, `OFFER FOR SALE`, `NOT APPLICABLE`; a fused upper-case `LIMITED`/`LTD` suffix separated without inserting, deleting or repairing any issuer letter, digit or amount (`UNLIMITED` and `LIMITED1` untouched, `numeric_repair` stays `False`); the same normalisation re-applied idempotently to the decoded child payload. Option A (rewriting the fixture) was rejected: it would have hidden a real segmentation failure and left the frozen fallback broken for genuinely merged notices.
- **Unchanged boundaries:** `price_band_notice.py` (frozen, pinned `779afb0b…`), `issue_terms.py`, `official_offer_amounts.py`, `sections.py`, scoring, knockouts, A9/GMP policy, config, schema and frontend. Issuer identity checks still reject a different issuer; no alias, fuzzy match, letter/digit repair or currency guess was added. No Jio evaluation was created — its issue terms come from a retained publisher document, not OCR.
- **Validation:** the failing test 1 passed; 7 focused cases passed; 281 OCR/official-notice tests passed; **full backend 1676 passed** (1704 s, exit 0, 6 new); frontend 93/93; frozen core, golden result `e84f8bc0…` and inactive v1.6 PASS; `compileall` exit 0.
- **Second iteration (evidence-led):** after the code fix the runner reached the next assertion and reported `price_band_low is None`. A temporary diagnostic commit (`5daf95b`, reverted in `f4001e0`) returned the runner's tile text: the floor/cap line had fallen below the 0.95 confidence gate (`[UNREADABLE_OCR_LINE]`), while the full-width identity crop read every line at ≥0.95. Cause: the fixture was 1800 px wide with 90-character lines, ~1950 px after the pipeline's render scale — wider than the 1600 px OCR tile — so each long line was cut at a crop boundary and its confidence depended on host CPU kernels. The fixture now renders the same notice as a narrow single-column advertisement (1040×800, 54-character lines, one tile); wording, image-only rendering, real OCR engine, assertions and the original-hash invariant are unchanged, and the confidence gate and glued-number rejection are untouched. Both remedies were needed: B for genuinely merged headings, A for the fixture's impossible line width.
- **CI confirmed:** run [39964614650](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39964614650) on `627934b` — **success**, backend 1676 tests / 0 failures (1846.8 s), frontend, schema/integrity, `compileall` and clean-tree all green. First green run since the Jio integration.
- **Disposition: RESOLVED AND CI-CONFIRMED.** Jio evaluation unchanged (`…29d9a601`, 34.0, interval 24–77, A9 nonterminal); no evaluation-relevant input changed and no evaluation was created. Report: `docs/investigation/OFFICIAL-NOTICE-OCR-SEGMENTATION-CI-FIX-2026-10-23.md`.

## Publication verification, automated validation and evidence status — 2026-10-23

- **Scope:** verification and evidence only. No engine, test, schema, config, frontend or evidence file changed; no scoring weight, criterion semantic, A9 rule or knockout touched; `main` and PR #6 untouched; both historical Jio evaluations and `…final-29d9a601` unchanged.
- **Lineage (remote readback):** branch `arena/07f3439f-ipo-screening-engine` tip `589e468e06b49c8066bbdb2e3f0729c4d09cd929` (receipt, 1 file) ← `e612702ea22acf221758c44a2f3f98eca85f4d51` (integration, 85 files) ← `8a1a37022f00496dd22e67b51319a407f6daf6fb`; ancestry and both parents confirmed through `gh api` and `merge-base --is-ancestor`. All 181 tracked `engine/`, `tests/`, `schema/` and `frontend/` files re-hashed against the commit object: 0 mismatches.
- **A9 intact:** `gmp_binding.py`, `gmp_evidence.py`, `gmp_policy.py`, `connectors/coordinator.py` and `schema/gmp-qualification-binding.v1.schema.json` are byte-identical to the parent; the Final-disposition gate semantics are unchanged, so missing/unqualified GMP still withholds Final.
- **Validation:** the branch CI workflow (`A9 contract boundary regression`) ran automatically on both commits: **failure**, each job 1670 tests with exactly one failure — `test_image_only_official_notice_uses_real_offline_ocr_and_preserves_original_pdf_hash` — while frontend, schema/integrity, `compileall` and the clean-tree check all passed. Cause: the runner's offline OCR emitted the synthetic notice's upper-case heading lines without word separators (`INITIAL PUBLICOFFERINGOFACMEFORGELIMITED`), so no issuer name could be isolated and the provider rejected the document (fail-closed). The same test with the same pinned OCR packages and font passes locally in 5.8 s, producing spaced text and `company_name = 'ACMEFORGE LIMITED'`; `_norm_name()` already ignores spacing, so the guard is sound and the difference is OCR segmentation on the runner. Deterministic there (two jobs, two commits), so **not** treated as a flake, and nothing was changed to make it pass. Independently, the tree extracted with `git archive 589e468` passed the backend suite **1670 passed in 1206.58 s** and frontend 93/93. The preserved first integrated attempt (1668 passed / 2 failed: one missing fixture, one pre-existing workbook-timestamp flake) remains published unchanged.
- **Acceptance:** no browser binary in this environment, so DOM criteria are **untested, not accepted**. The upload → evaluate → evidence path was exercised at the HTTP boundary on the published tree: `POST /api/v1/ingest/document` 201, evaluation 34.0 / interval 24–77 / Low, 48 evidence items, all evidence/activity/health reads 200. Both API guards (non-loopback Host → 400, missing Origin → 403) behaved as designed.
- **No new evaluation:** the fresh acceptance run matched `…final-29d9a601` on `input_snapshot_hash`, `peer_snapshot_hash`, `config_hash`, all 48 evidence objects and the `field_map`; only retrieval timestamps differ. A new record would duplicate the published one, so the existing reference stands.
- **Evidence gaps (separate findings):** C1 — a retained Jio GMP figure exists (Investorgain ₹227 / 20.29 %, stamped 15-Oct 17:37) but is not qualifying (unqualified publisher, listing-index line, eight days outside the A17 window, no A28.1 binding). C2 — K1 `auditor_opinion`/net worth FALSE (leaves decided) while `going_concern_uncertainty` stays UNKNOWN (the phrase "going concern" appears once, on p253, only as accounting basis); K2 pledge 0 FALSE but `sebi_ed_action_active` UNKNOWN (pending SEBI revision against the Promoter on p470; p487 denies debarment only); K5 ratio 0.4471 % (ICDR 0.4497 %) with `contingent_liab_unquantified` UNKNOWN despite a fully quantified note 37. C3 — net-worth basis (owners' equity 3,359,769 vs ICDR 3,340,134, delta 19,635 OCI) still has no authoritative decision; no gate effect, four options documented. C4 — official terms **are** published (BSE listing/detail: ₹1065–₹1119, lot 12, 21–23 Oct 2026, anchor notice 2026-10-19) but the engine's official retrieval fails closed on this sandbox's egress (`URLError TLS/SSL EOF`); nothing was substituted into official fields, and the 19,75,25,934 vs 27,00,00,000 share-count discrepancy is recorded, not resolved.
- **Decisions requested (not taken):** K1 negative-confirmation rule; K2 scope of "active SEBI/ED action"; K5 unquantified-contingent scope; net-worth basis.
- **Disposition: INTEGRATION AND VALIDATION COMPLETE — EVIDENCE/GOVERNANCE/ENVIRONMENT BLOCKERS OPEN.** Report: `docs/investigation/JIO-VALIDATION-AND-EVIDENCE-STATUS-2026-10-23.md`.
- **Publication:** commit `97b970e7df696e2fea90ca039bd24911b2dd0974` (parent `589e468`) adds the report, six evidence JSON files and this entry; 8 files, documentation only. Remote readback confirmed the branch head and byte-identical report/tracker/CI-analysis blobs. The branch's CI on this commit reproduced the same single OCR-fixture failure (1670 tests, 1 failure), confirming no source change.

## Authorized bounded offer-term extraction enhancement — 2026-10-21

- **Implemented, no policy change:** final runtime **e416b1f808d09bf96b8446430ea86c93d3071557**, baseline4ce17356e3a68d45f80b71f73f8bbc53beb62155 preserved. Qualified RHP native reads extend5→30pages with explicit read scope/errors. Beyond5 only identified offer-summary sections or established component tables may supply amounts, not unrelated/example mentions. Existing source origin/document qualification/method/verification remain separate, with no new canonical authority states.
- Neutral **SOURCE_PLACEHOLDER** metadata for blank/bullet/dot/dash brackets/TBD; field remains null unless another valid assertion establishes it. Adjacent components cannot inherit the placeholder or supply cash; placeholder history does not block later valid evidence. OCR diagnostic method cannot claim native text. **Qualified OFS NIL/Not applicable still zero**, not a placeholder. No shares×cap/total/reservation/anchor substitution, aggregator/LLM authority or manual workaround.
- Conservative native **offer-table AST** retains original headers/cell text/coordinates/body rectangles. Requires explicit aligned adjoining cells; no inferred column stitching. Ambiguous grouped multiline chunks are recorded, not split into invented cell geometry. Currency/unit/aggregate statement required in the actual monetary run. Original source hash/page/quote/locator preserved. Narrow initial support—not a universal table parser; actual Jio cover AST not recognized, no false claim otherwise.
- **Focused only:** LinuxPython3.11.2,8relevantPythonfiles **162passed/6deselected/3warnings/8.42s/exit0**,31newcases; existing assertions/fixtures/frozen parsers unchanged. Real Jio native-text check on final code retains fresh=null/OFS0/fresh-only placeholder diagnostic,30/591pages attempted/no read errors. Compile/diffcheck exit0. No broad backend/matrix/unrelated frontend/build/HD Fire history changes.
- **Final native Windows/API** [39650886624](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39650886624), final runtimee416b1f: focusedPython/relatedNode8activitysteps/realAPIjobSUCCESS. Actual **ing-e5c0c436c8564ef5**, finished2026-10-21T18:25:52.532424Z, **BLOCKED / AWAITING_ISSUE_TERMS, missing only issue.fresh_issue**. Explicit verified OFS0 preserved; actual three newspaper OCR runs succeeded151.859/146.125/190.015s within270s budgets, intended GID rejection retained. NativeCheck119405084138 independently decoded. Older intermediate runs are not final-code acceptance; cancellation of the first was denied403, no bypass/log cleanup.
- Actual GET terminal after same-store server restart **identical**; GET evaluation lists both empty. **No evaluation/persistence/result hash or successful duplicate idempotency claimed**. Jio restoration **remains INCOMPLETE**; corrected BSE current endpoint still403 and examined authoritative evidence does not establish fresh cash, not proof of universal non-publication.
- Existing session branch only; initial checkout was safely fast-forwarded after hashing544existing files and proving exact remote matches. No reset/clean/force/switch/overwrite of unrelated files. Main/PR6/protected policy/config/schema/goldens/frozen parsers preserved and independently checked on publication. Detailed scope/limits, exact command/log, actual document/API evidence and remote readback: **docs/investigation/offer-extraction-improvements-2026-10-21/README.md**. Final completion response supplies evidence-publication SHA and independent final readback.

## PO/PA review and authority confirmation — 2026-10-22

- User explicitly selected **retain official-disclosure requirement**, not cap-price-derived upper-bound input. No aggregator/LLM substitution, shares×cap monetary authority, new scoring/policy/schema rule or hardcoded ₹30,213crore authorized/applied.
- Independently reread published extraction fix6d62d9ce75d9f66d83b3ce91fb4dfce74bb6ee3d: **552tracked paths match,12changed blobs fetched/byte-compared**, actual final runtimee416b1f native Check/JSON identical; main/PR6/protected paths unchanged. This is code/artifact verification, not a new ingestion/test run.
- Historical OCR/ZIP diagnosis does not describe final runtime: original PDF members unpacked correctly; RHP has native text; all3newspaper OCR calls succeeded151.859/146.125/190.015s within270s. GID exception intentionally rejects hypothetical examples. Existing162focusedPython tests and native actualAPI execution retained, not misrepresented as reruns today.
- Actual **ing-e5c0c436c8564ef5** remains **BLOCKED only issue.fresh_issue**; explicit OFS0 retained. GET after restart identical, evaluation lists empty; no evaluation/persistence/hash/success-idempotency claim. **Fixes applied; Jio restoration INCOMPLETE at confirmed official-evidence boundary**, not an active demonstrated OCR crash. No universal publication-absence assertion.
- Review only: **docs/investigation/po-review-2026-10-22/README.md**, original implementation readback and subsequent publication receipt. No production code change/new expensive native run/broad suite/build, no source authority weakening, historical rewrite, main/PR6 change or unrelated cleanup.

### Jio fresh ingestion, evaluation and provenance reconciliation — 2026-10-23

- **Scope:** read-only evidence work superseded for this entry by explicit authorization to execute a fresh ingestion/evaluation of the same PDF (`72480c2e…1b6d`) and to correct demonstrated defects. `main` untouched; both historical evaluations (`…051816Z-final-b79b5794`, `…101913Z-final-ad5e6872`) unchanged; no weight/semantic/A9/safety-gate rule changed.
- **Executing revision:** `514ca599d3982bc160319793ef2f7f06d046fd27` = published report parent `d9012a2` + integrated completed ingestion fixes (`0d89604`, from `arena/95234306`) + measured corrections (`417a586`) + completed OFS-NIL fix (`54b3447`). A9 files were deliberately retained from the current implementation instead of the peer branch's multi-snapshot `ConflictingSourceError`, which would change A9 contract semantics.
- **New records:** ingestion `ing-4c38b470edb24db4`; evaluation `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601`; **34.0/100**, interval **24–77**, 43 unknown points, 57% completeness, Low confidence, verdict `INSUFFICIENT_DATA`; A9 `NONTERMINAL_UNRESOLVED`; K1/K2/K5 `UNVERIFIED`; K3/K4/K6 clear; 0 applied penalties.
- **Freshly extracted with page-anchored evidence:** debt prepayment 275,000 (116), pre-issue promoter 66.43% (104), auditor identities/three-year continuity (322/324), explicit no-EOM (430), contingent 15,021 (405). GCP `[●]`, post-issue holding `[●]`, top-five concentration and industry CAGR remain unknown **because the filing does not disclose them**, and their criteria stay UNKNOWN.
- **Provenance:** canonical `field_map` now persisted (48 entries, all resolving); explicit IDs survive A15 projection; builder evidence matches the first candidate used. `kmp_exits_2y` no longer defaults to 0 (criterion went 1.0 → UNKNOWN, honestly). Net-worth basis (owners' equity 3,359,769 vs ICDR Net Worth 3,340,134) left unchanged pending governance.
- **Score movement:** 33.0 → 34.0 = `D.auditor` 0 → 2 (evidence now extracted) and `D.board_kmp` 1 → 0 (unsupported default removed). Interval follows the base score; unknown points and gate states unchanged.
- **Issue terms:** live official discovery failed closed in this sandbox (TLS/SSL EOF at NSE/BSE endpoints); the authorized third-party path re-parsed retained publisher bytes (`47293a7f…25fe`, original retrieval 2026-10-21T20:19:43Z) and all four terms remain `UNVERIFIED`/non-official. No GMP, anchor, subscription or regime value exists; A9 unaffected.
- **Tests:** new real-filing regressions 7 passed; post-correction focused suite 282 passed; full suite logged with one peer-branch test file excluded (`tests/test_jio_rhp_issue_terms.py`, depends on code absent from this branch) — see the published test logs.
- **Disposition: OPEN — MARKET/GOVERNANCE DEPENDENCIES.** Extraction and provenance defects demonstrated by this run are fixed and verified. Remaining blockers are external/govemance: live official issue-term retrieval, a qualifying A9 GMP observation, K1/K2/K5 scoped evidence-or-negative decisions, and the net-worth basis decision. Report: `docs/investigation/JIO-FRESH-INGESTION-EVALUATION-2026-10-23.md`.

### Jio correction integration — branch engine now carries the validated composition — 2026-10-23

- **Scope:** integrated the eleven fresh-ingestion corrections into `arena/07f3439f-ipo-screening-engine`; retained the branch's A9 subsystem byte-identically; no scoring weight, criterion semantic, A9 rule or knockout changed; both historical Jio evaluations and `…final-29d9a601` untouched; `main` not touched.
- **Target-engine fit measured first:** applying `corrections.patch` to the branch engine `8a1a3702` rejects 16 hunks across `sections.py`, `toc.py`, `builder.py` and three test files. The branch engine also reads this filing incorrectly on its own: only 7 sections route (no `objects_of_the_offer`, `restated_financials`, `our_management`), proceeds are GCP-only, promoter holding is fabricated as **100 % pre / 100 % post**, and `sebi_ed_action_active` is emitted as **False** with a quote absent from the source. Evidence: `docs/investigation/jio-correction-integration-20261023/branch-engine-baseline.json`.
- **A9 disposition:** no policy decision required or taken. The branch carries the newer A9 subsystem (A28.1 binding + schema, capture-failure/PD guards, optional-trend linkage, explicit-snapshot selection in the coordinator). The sibling line predates it (files absent, −9 lines in the coordinator). The six A9-bearing files and the binding schema are taken from the branch and verified byte-identical. Qualification requirements and terminal/nonterminal transitions are unchanged; no success path, zero-substitution or non-official issue-term substitution was introduced.
- **Integration:** non-A9 engine adopted from the validated implementation line (7 modules added, 15 updated, 0 removed), corrections applied on top, frontend updated to the matching API surface, offline-OCR pins added. Tests: 28 files added, 12 updated, plus two stale Jio issue-term expectations corrected with inline reasons (required `fresh_issue`; canonical amount in `reporting_unit`).
- **Evaluation:** none created. The integrated engine's 66 engine files are byte-identical to the tree that produced `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601` (34.0, interval 24–77, `INSUFFICIENT_DATA`, A9 nonterminal), so a new record would duplicate it.
- **Validation:** backend suite on the integrated tree and frontend `node --test` (93/93) — exact counts in the integration report. Historical stores unopened.
- **Remaining blockers unchanged:** no qualified GMP observation (A9 withholds Final); K1/K2/K5 need scoped evidence or an approved negative-confirmation rule; net-worth basis decision; live official issue-term retrieval still refused by this sandbox's egress.
- **Disposition: CORRECTIONS INTEGRATED — MARKET/GOVERNANCE DEPENDENCIES OPEN.** Report: `docs/investigation/JIO-CORRECTION-INTEGRATION-2026-10-23.md`.

## Jio K1 / K2 / K5 evidence and governance dispositions — 2026-10-23

- **Scope:** read-only investigation of the three remaining unresolved Jio criteria against the governing decisions, the retained RHP (sha256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`, 591 pp) and evaluation `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601`. **No regression test run, no ingestion, no new evaluation, no code/config/test/fixture/expected-value change, nothing merged to `main`.**
- **K1 `going_concern_uncertainty` — UNKNOWN, correct under A19; no technical loss.** Examination report pp. 321–324 (Deloitte Haskins & Sells LLP + Chaturvedi & Shah LLP, 7 Oct 2026, UDINs `26100459QBZXUZ8355` / `26122179ZKMPTF3256`) carries no going-concern paragraph, no Emphasis of Matter, no qualification; *"material uncertainty"* / *"significant doubt"* / *"ability to continue as a going concern"* = 0 hits in 591 pages; the only "going concern" occurrence is the p253 2019 scheme accounting basis. New evidence: **p430 note 47.4** gives scoped five-period negatives for audit qualifications, other legal/regulatory requirements and Emphasis of Matter — silent on going concern, and an SA 570 section is neither a qualification nor an EOM, so it is not a usable negative. All pages `READ`; nothing was dropped. Minimum further evidence: the underlying statutory audit reports (referenced at p322, not reproduced) or an auditor going-concern confirmation.
- **K2 `sebi_ed_action_active` — UNKNOWN as the rule's output, but the record understates the filing. Technical + semantic.** The filing discloses a **pending SEBI revision application before the Bombay High Court** — against a **Director** (p468) and against the **Promoter** (p470) — plus concluded SEBI matters against the Promoter (₹250 m disgorgement order of 24 Mar 2017; SAT revised and SC 29 May 2026 set aside the fraud finding while concurring on the disclosure breach; ₹3 m penalty 20 Jun 2022 upheld through SC 2 Dec 2025; 2014 ₹130 m order remanded and disposed without penalty 20 Sep 2021), all inside p463's "outstanding litigation" frame. **`_sebi_ed_action_finding` emits `None`:** all **12 of 12** SEBI/ED-actor spans in the located window (pp. 463–478, every page READ) exceed the **600-character line-span cap** (715–1804 chars) — the dominant mechanism — and four further mechanisms each independently block survivors: E2 `[^.\n]` fails across a hard wrap (p468 `SEBI \nfiled` matches only after joining), E3 `_LIT_PARTY` lacks the filing's defined short name "RIL", E4 `_REG_BOILERPLATE` vetoes a genuine action sentence because it cites a regulation number, E5 the regulator-first verb list omits `filed`. All five err fail-closed. **No ED/PMLA mention anywhere (0 hits)**; the p464 Company / p469 Directors / p473 KMP-SM nils name no regulator and no ED, so under A23 r8 / A25 no `False` is reachable either. Corrections documented only, not implemented: **P1** sentence-level cap, **P2** newline-normalised matching, **P3** heading-attributed party, **P4** narrow boilerplate, **P5** add verbs, with six named regression cases.
- **K2 governance question — the only genuinely new decision required.** A23 r6 (party test), A24 (company/promoters/directors population) and A25 (False semantics) are settled; the **status meaning of "active"** is not. Options: **K2-A** pending at cutoff (a regulator's own appeal counts) → flag True → **`AVOID`**; **K2-B** live adverse consequence incl. penalties in force → `AVOID`; **K2-C** issuer-only → flag stays absent → `INSUFFICIENT_DATA`, but contradicts A23 r6 and A24 and would require amending them; **K2-D** status quo, rejected as not durable. **Material consequence: under A or B this filing's final outcome changes from `INSUFFICIENT_DATA` to `AVOID` through A7 / `config.verdict.knockout_verdict`.** Decision belongs to Ramki; no rule was chosen here.
- **K5 `contingent_liab_unquantified` — UNKNOWN, correct under A20 r8.** Note 37(I) p405 FY2026 column **15,021** ₹mn (commitments 26,198 excluded per A20 r6) ÷ p406 Total Equity **3,359,769** ₹mn = **0.4470843084747791 %**, reproducing the recorded value exactly — 111.8× below the 50 % threshold (firing would need 1,679,884.5). Outcome insensitive to basis: ICDR Net Worth 0.4497 %, interim-column 0.4372 %, commitments-included 0.7798 %. Single contingent row ⇒ no double count. The flag is absent only because note 37 is fully quantified with a materiality view and A20 r8 permits `True` only on a positive in-section statement, never coercing `False`; the only unquantifiability wording (p472, Promoter arbitration) is outside the defined section. **Provenance defect (no value error):** the evidence quote for `financials.contingent_liabilities` is the row label only, without the amount. Optional scope extension K5-A (status quo) vs K5-B (extend to litigation section) — recommendation **no change**. Net-worth basis dependency recorded, not resolved.
- **Records gap:** A19, A20, A23, A24, A25, A26 and A27 are approved/implemented but **absent from this branch's `handoff/decisions/`** (they exist at `ebb8a6c`). Recorded, not fixed. A26 (tax-only proceedings) remains a PROPOSAL and is not authority.
- **Disposition: K1 and K5 SETTLED AS GOVERNED UNKNOWNS; K2 DIAGNOSED — ONE GOVERNANCE DECISION (K2-A/B/C) REQUIRED BEFORE ANY EXTRACTION FIX.** Report: `docs/investigation/JIO-K1-K2-K5-DISPOSITION-2026-10-23.md`; machine-readable detail in `docs/investigation/jio-k125-20261023/` (incl. `k2-extraction-reproduction.json`, page-level reproduction of the twelve discarded spans).

## K2-A authorised and implemented; A19–A27 published — 2026-10-23 (revision 2)

- **Authority:** Ramki authorised **K2-A** — *"A regulator's pending appeal qualifies as an active action at the evaluation cutoff, subject to the existing party-scope rules and evidence requirements."* Recorded as **`handoff/decisions/A29-k2-active-action-pending-appeal.md`** (APPROVED and IMPLEMENTED, 2026-10-23). A29 is a clarification of the **status meaning of "active"** only: party scope (A23/A24-D1) and the `false` rule (A23 §6A.2, A25-D1/D2) are unchanged, and **K2-B / K2-C were not adopted** and remain open questions.
- **Implementation — five confirmed defects, all fail-closed, all fixed in `engine/ipo_screening/extraction/sections.py`:** **P1** the 600-character quotability cap was applied to a *line span* (12/12 SEBI/ED candidates in the Jio window measured 715–1,804 chars) → now measured on the sentence via `_lit_sentence_bounds`, with a masked-region guard; **P2** `_REG_ACTION` excludes `\n`, so a hard PDF wrap (`SEBI \nfiled`) matched nothing → `_lit_match_text` replaces single newlines with spaces at identical offsets (paragraph breaks preserved, quotations still verbatim); **P3** the party literal does not know the filing's short names → **heading attribution**, kept separable; **P4** `_REG_BOILERPLATE` vetoed a genuine dated order that cites a regulation → citation forms split out and vetoed only when the sentence reports no adjudicative event; **P5** the regulator-first verbs lacked `filed|preferred|moved|referred` and the nouns lacked `appeal|revision application|petition|complaint` → added, with the action noun still required. A sixth defect was found while probing the real filing and fixed before publication: P1 made the p463 section preamble ("this section also provides the details of all disciplinary actions …") quotable for the first time and it was emitted as a finding; `_REG_META_DISCOURSE` now rejects statements *about* the disclosure.
- **P3 constraints:** section-level headings only (`I.`…`XVIII.`), the heading must name **exactly one** A24 group, the sentence must name no party of its own, and the heading must precede the sentence in document order; a heading naming no single group **clears** the earlier attribution rather than inheriting it. The attribution is exported in the evidence note and the `quote` stays the sentence. Reverting P3 returns K2 to UNKNOWN and cannot create a `false` or clear a flag.
- **What the corrected extractor produces for the retained Jio filing (read-only probe, not a test and not an evaluation):** `governance.sebi_ed_action_active = true`, page **468**, quote *"Against the said order of the Special Court, SEBI filed a revision application before the Hon'ble High Court of Bombay and the same is currently pending."*, status **pending**, party attributed from the §III heading **Directors**. `litigation_bucket` unchanged. The seven fixture filings under `fixtures/filings/` all still emit **no** `sebi_ed_action_active`. Consequence stated, not executed: K2 TRIGGERED ⇒ A7 / `knockout_verdict` ⇒ **AVOID**.
- **K5 evidence citation (presentation only):** `financials.contingent_liabilities` now cites *"Claims / disputed liabilities against the Group not acknowledged as debts* | 15,021 as at 31 March 2026"*, with a note that the citation is assembled (verbatim label + selected cell in the record's `raw_unit`). Value, flag (`unquantified = None`), A20 numerator rule, denominator, column selection, threshold, ratio (0.4471 %) and the **UNVERIFIED** disposition are all unchanged. The net-worth-basis question stays separate. One existing exact-equality assertion in `tests/test_contingent_liabilities_extraction.py` was updated accordingly.
- **A19–A27 published:** all nine records retrieved byte-for-byte from `ebb8a6c` and written to this branch's `handoff/decisions/`, each verified by sha256 against the retrieved blob (all nine identical). No text reconstructed or corrected. `A8-R-…-2026-10-20.md` and `2026-10-22-pa-aggregator-issue-terms.md` also exist at `ebb8a6c` but were outside the authorised A19–A27 scope; recorded, not copied.
- **K1 and K5 unchanged.** K1 remains UNKNOWN under A19 (no statement of either polarity; p430 note 47.4 is silent on going concern and an SA 570 section is neither a qualification nor an EOM). K5 remains UNKNOWN under A20 r8 (note 37 fully quantified). Neither is resolved by this pass.
- **Tests added, NOT RUN:** seven P3 negative guards (ambiguous heading, heading below the sentence, heading on a later page, lettered sub-heading, ambiguous-heading reset, unrelated SEBI reference, section meta-discourse) plus six behavioural cases (pending appeal with evidence-note assertions, hard wrap, long paragraph, dated order citing a regulation, citation without an event, concluded status) in `tests/test_litigation_regulatory_defaults.py`. **Execution status: NOT RUN — deferred to the separate regression pass; the full backend suite (~3 h) was excluded by explicit instruction.** No ingestion, no new evaluation; `…final-29d9a601` untouched; nothing merged to `main`.
- **Remaining factual limitation:** the finding rests on what the filing states. SEBI / Bombay High Court verification is blocked by sandbox egress; no current procedural status is asserted, and A29 adds no cutoff input or clock beyond the existing `evaluation_datetime` semantics.
- **Disposition: K2-A APPROVED AND IMPLEMENTED; K2 NOW EXTRACTS `true` FOR THIS FILING FROM ITS OWN DISCLOSURE; REGRESSION EXECUTION DEFERRED.** Report revision 2: `docs/investigation/JIO-K1-K2-K5-DISPOSITION-2026-10-23.md` §10; decision: `handoff/decisions/A29-k2-active-action-pending-appeal.md`.

## Paras ingestion failure — document class, current-issue dates and field-level withholding — 2026-10-23 (revision 3)

- **Scope:** the extraction path behind a rejected official RHP and an unresolved `issue.ofs`. Read-only investigation plus general correction of the Price Band Notice / RHP / Prospectus class boundary, current-issue date extraction, and the handling of a conflicting field. **No regression test run, no ingestion, no evaluation, no scoring/config/schema/fixture/historical-evaluation change, nothing merged to `main`.** Branch `arena/07f3439f-ipo-screening-engine`; baseline `8939b05`; `main` untouched at `01ba66c`.
- **Input limitation:** the Paras filing PDF and trace `ing-42ded42dde7a41b2` are absent from the workspace, every ref and GitHub code search. The failure was reconstructed from the code path and reproduced on retained filings plus a synthetic cover; no claim is made about what that document specifically disclosed.
- **Root cause 1 — class conflation (confirmed by execution):** `_classify_document` classified a 496-page RHP as a *Price Band Notice* (`R.K Fashion accessories.pdf` → `(True, 'Authoritative title and semantic price tokens matched')`), because every prospectus contains all five of the notice's semantic tokens. The notice contract ("one band, one lot, one window") was then applied to a multi-hundred-page filing and its other pages became "conflicts".
- **Root cause 2 — context-free dates (confirmed):** `_extract_dates` read `closing date` / `closes` on every page with an unanchored date normaliser; a history sentence ("the Issue Closing Date was July 14, 2017") became a *current* close-date candidate and `Conflicting close dates: ['2026-10-23', '2017-07-14']` rejected the whole document.
- **Root cause 3 — field conflict escalated to document rejection (confirmed):** dates, band and lot all raised. One disputed field destroyed every undisputed field, which is how a valid official RHP produced no usable issue terms — including the OFS amount it disclosed.
- **Root cause 4 — `issue.ofs`: a consequence, not an independent defect.** The chain (`issue_terms` resolver → `_issue_attachments` → `parse_official_rhp` → `explicit_amounts` → `_find_ofs_nil`) has no absence→zero path; the RHP was rejected before its offer table was read, and the rejection was reported as a generic "attachment rejected". **`issue.ofs` was never set to 0 from absence and is not now.**
- **Corrections (issuer-independent):** prospectus-title guard on pages ≤ 3 plus a >25-page "not a notice without a notice title" bound; term-page scoping, a −60/+400-day window around the document's own date, and historical-frame / past-tense rejection for date candidates; field-level withholding for band, lot and window with `CONFLICTING_*` / `INVALID_ISSUE_DATE_ORDER` findings; `metadata['issue_term_errors']` (field → reason) and `metadata['historical_dates_excluded']` so absent, withheld and parsed are distinguishable; `parse_official_rhp` gains an explicit RHP role test (title form / responsibility statement / offer-table header; DRHP, GID and explicit notice titles refused) and `_rhp_issue_terms()` publishes the RHP's own band, lot, window, fresh-issue and OFS field by field, with a term-level failure recorded instead of discarding the document; `prospectus_terms` now rejects an RHP *by class* ("… not a final Prospectus …") instead of "no 'Prospectus Dated:' marker found"; `_issue_attachments` carries the RHP-class verdict into its rejection reason.
- **Probe results (read-only, not tests):** R.K Fashion 496 pp → `OFFICIAL_RHP_TERMS`, `open 2026-10-05`, `close 2026-10-07`, `ofs 0.0` (explicit NIL), `fresh_issue None` (`₹ [●]`) — previously the document was rejected; Vishal Nirmiti → `close 2026-10-05` **unchanged**; Moneyview final Prospectus → prospectus path unchanged; `complete_sample_rhp` and `class_e_modern_complex_rhp` no longer classifiable as notices; `conflicting_notice.txt` → band withheld, lot and window published; `invalid_collar_notice.txt` still fails closed.
- **Not changed:** collar validation, issuer matching, official-source qualification, required-term policy (`AWAITING_ISSUE_TERMS` still follows a missing required term), A9/GMP, K1–K5, A23–A25 party/absence rules, A29 status meaning, scoring, config, schema, fixtures, golden record, historical evaluations. No issuer constant appears in production code or general tests.
- **Tests added, NOT RUN:** 21 cases in the new `tests/test_official_rhp_terms_and_dates.py`; two defective-contract tests rewritten in `tests/test_price_band_notice.py` (`…conflicting_price_bands_rejected` → `…withhold_the_band_not_the_document`; `…inverted_date_order_rejected` → `…withholds_both_dates`) keeping both the never-publish-the-conflict and the others-survive assertions. **Execution status: NOT RUN — deferred to the separate regression pass; the full backend suite (~3 h) was excluded by explicit instruction.** Static compilation only.
- **Remaining limitations:** the Paras document is unavailable, so its specific disclosure is unknown and its OFS resolution unproven; the `Price Band: Rs X to Rs Y` colon form is still not matched by the band range pattern (found while testing, deliberately not changed — recorded as a proposal in A30 §6.2); the resolution-level operator diagnostic for an absent OFS is unchanged.
- **Disposition: DEFECTS CONFIRMED AND CORRECTED ON THE CODE PATH; PARAS-SPECIFIC OUTCOME UNPROVEN; REGRESSION EXECUTION PENDING.** Report: `docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`; record: `handoff/decisions/A30-document-class-and-field-level-withholding.md`.

## Paras Healthcare — actual document recovered; issue-term failure reproduced and resolved — 2026-10-23 (revision 4)

- **Scope:** completion of the Paras issue-term investigation on the **actual filing** (not a synthetic reproduction), with the recovery of the evidence artifact, a second round of general corrections, documentation and publication. **No regression test run, no ingestion, no evaluation, no scoring/config/schema/fixture/historical-evaluation change, nothing merged to `main`.** Branch `arena/07f3439f-ipo-screening-engine`, baseline `3699df2`, `main` untouched at `01ba66c`.
- **Evidence recovered and verified:** `docs/investigations/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf` from branch `evidence/jio-score-33-recovery-20261023` at commit `1dd6e14e7fa50a677beefba9ca7d0d1a7b322c58` (blob `f62a80f5`); 11,577,075 bytes, 651 pages, **sha256 `e0a3187fe18d1c12f88f29170291972714cf15be7946e8a7f4a7d8c914570e74` — matches the expected value**; retained byte-for-byte at `evidence/non-authoritative/paras-healthcare/` and hash-asserted in the new regression test. Investigation evidence only, not official evaluation evidence.
- **The document:** `RED HERRING PROSPECTUS — Dated October 14, 2026` (title on p3), CIN `U85110HR1987PLC035823`, 651 pp. Classified **not** a Price Band Notice (prospectus title guard, verified on pages 1–5 and on all 651 pages), classified `OFFICIAL_RHP_TERMS`, never relabelled a final Prospectus.
- **Original failure reproduced exactly on the real document:** the pre-correction close-date patterns yield `p3 → 2026-10-23`, `p535 → 2026-10-23`, **`p590 → 2017-07-14`** (`"Closing Date" shall mean 14 July 2017;` — an Article defining a term), i.e. `['2017-07-14', '2026-10-23']`, the exact pair in the reported trace; the disagreement then rejected the whole filing. The 2017 date is a Series A CCPS allotment/transfer date (pp. 66, 110, 113, 115), never an issue date.
- **Current behaviour on the real document:** `open 2026-10-21`, `close 2026-10-23` (p3 quotes), `fresh_issue 5,000.0 INR_MILLIONS` (p3) and **`ofs 9,500.0 INR_MILLIONS` (p3)** — the disclosed OFS amount is now resolved instead of lost; price band and bid lot are `None` **and diagnosed as `[●]` placeholders** (p11 / p11 / p9), correctly undisclosed at RHP stage. The Articles page never enters the candidate set (term-page rule); the document-date window and the defined-term guard cover the case if such a line ever sits on a term page.
- **Why `issue.ofs` was unresolved:** (i) document-level rejection — the RHP was refused by the notice parser (date conflict) and the prospectus parser (no `Prospectus Dated:` marker) and not recognised by the RHP path, so its offer terms were never read; (ii) an independent parser defect — `explicit_amounts` discarded any amount preceded by `[●]`, and every OFS statement in this filing has a `[●]` **share count** before the money amount (`Up to [●] Equity Shares … aggregating up to ₹ 9,500.00 million`). The disclosure was present three ways (pp. 1, 3, 12; seller rows 3,000 + 6,500 = 9,500); **nothing was inferred, and absence would still not be zero.**
- **Additional global corrections (D5–D11):** **D5** document date read without a colon and anchored to line start (`Dated October 14, 2026` previously produced no document date at all, making the plausibility window inert); **D6** defined-term entries (`"X" shall mean <date>`) are not issue dates; **D7** colon/dash price-band form `Price Band: Rs. X to Rs. Y` now read (it previously matched nothing); **D8** every explicit band declaration on a page is a candidate — two differing declarations produce `CONFLICTING_PRICE_BANDS` instead of first-wins; **D9** only a **money-slot** placeholder withholds an amount, a share-count placeholder does not; merged/header cells naming several components still refuse to bind; **D10** `SOURCE_PLACEHOLDER` no longer fires on share-count placeholders; **D11** unresolved-field diagnostics now carry `why_unresolved` (absent / placeholder page / conflicting evidence / historical exclusion / no qualifying source), `inspected_sources` (provider, document class, URI) and `required_evidence`, additively, with `state` values, required-term semantics and eligibility unchanged.
- **Operator diagnostic for the real run:** price band and lot now read `PLACEHOLDER_IN_QUALIFIED_DOCUMENT: page 11 / 9` rather than the previous generic "absent"; `ofs` and `fresh_issue` resolve `VERIFIED` from `OFFICIAL_RHP_TERMS`. The `AWAITING_ISSUE_TERMS` gate is unchanged and would still block on genuinely missing terms.
- **Other retained filings unchanged (probe):** R.K Fashion (open 2026-10-05, close 2026-10-07, OFS 0.0 INR_LAKHS explicit NIL); Vishal Nirmiti (2026-09-30/2026-10-05, fresh 14,500.0 INR_LAKHS, OFS `None` placeholder); Moneyview final Prospectus and all ten `fixtures/notices/*` keep their pre-correction values; both collar-invalid fixtures still fail closed.
- **Tests added, NOT RUN (at the time of this revision):** 15 further cases in `tests/test_official_rhp_terms_and_dates.py` (36 total) covering colon-form bands, colon-form conflict withheld, unrelated numeric ranges, colon-less document date, mid-sentence certificate date, defined-term exclusion, out-of-window exclusion, share-count vs money-slot placeholders, merged headers, independent component resolution and the enriched diagnostics; plus `tests/test_paras_evidence_regression.py` (9 cases) pinning the artifact hash and the real filing's classification, dates, OFS/fresh amounts and placeholder dispositions. **Execution status at the time: NOT RUN — deferred to the separate regression pass; no pytest, no ingestion, no evaluation. Superseded by revision 5, where both modules were executed green.**
- **Remaining blockers:** the ingestion trace `ing-42ded42dde7a41b2` is still absent from every ref, so the run's own payloads cannot be diffed (its symptoms are now reproduced exactly); the price band and bid lot for this issue are genuinely undisclosed in the RHP and require a price band notice or the final Prospectus; no end-to-end ingestion or evaluation was executed; regression execution pending.
- **Disposition at the time: DOCUMENT-SPECIFIC FAILURE REPRODUCED AND RESOLVED AT FIELD LEVEL; DETERMINISTIC, ISSUER-INDEPENDENT CORRECTIONS PUBLISHED; REGRESSION EXECUTION PENDING.** (Superseded by revision 5.) Report: `docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md` §11; record: `handoff/decisions/A30-document-class-and-field-level-withholding.md` (D5–D11).

## Paras Healthcare — controlled validation pass: focused regression executed — 2026-10-23 (revision 5)

- **Scope:** execution of the two focused regression modules against the published revision-4 commit, diagnosis and narrow correction of any failure, execution of behavioural checks A–F, and reconciliation of the record. **No full suite (~3 h), no ingestion, no evaluation, no scoring/config/schema/fixture change, no production-code change, nothing merged to `main`.** Branch `arena/07f3439f-ipo-screening-engine`, validated at `4b1c67f`, `main` untouched at `01ba66c`.
- **Evidence re-verified before and after the run:** sha256 `e0a3187fe18d1c12f88f29170291972714cf15be7946e8a7f4a7d8c914570e74`, 11,577,075 bytes, 651 pages, source commit `1dd6e14e`, blob `f62a80f5`. The guard was probed in both directions: artifact absent ⇒ 9 **skipped**; one byte flipped at constant length ⇒ 9 **errors** at the fixture hash assertion. Neither is reported as passing evidence.
- **Executed:** `PYTHONPATH=engine /home/user/ev/bin/python -m pytest tests/test_official_rhp_terms_and_dates.py tests/test_paras_evidence_regression.py -q` (CPython 3.11.2, pytest 9.1.1, commit `4b1c67f`). First run: 45 collected, **44 passed / 1 failed**, 0 skipped. See run: **45 passed / 0 failed / 0 skipped**, exit 0.
- **The only failure was in a test, not in the engine:** `test_the_historical_2017_defined_term_is_not_the_close_date` raised `TypeError: 'PriceBandField' object is not subscriptable` — a dict-style assertion against a dataclass, a transcription error in a test written but never executed in revision 2. Corrected in the test only (attribute access, plus an added `_last_excluded_dates` assertion recording *why* the 2017 definition never competes). No assertion weakened, no test deleted or skipped, no production module touched.
- **Behavioural checks A–F executed against the retained artifact** (probe + synthetic cases): class `OFFICIAL_RHP_TERMS`, not a notice, not promoted to a final Prospectus, refused *by class* by the notice parser; open `2026-10-21` / close `2026-10-23` with the p590 2017 definition producing **no candidate at all** (`historical_dates_excluded: []`), genuine conflicts still withheld; OFS `9500.0 INR_MILLIONS` and fresh `5000.0 INR_MILLIONS` (`VERIFIED`, p3) despite the `[●]` share count; band/bid lot `None` with three `SOURCE_PLACEHOLDER` diagnostics (p11 / p11 / p9) and no inference from seller rows, unrelated ranges or dates; `resolve_fields` ⇒ `PARTIAL` with `open_date`, `close_date`, `ofs`, `fresh_issue` resolved and the three price fields unresolved with `why_unresolved` / `inspected_sources` / `required_evidence`, `_REQUIRED_EVIDENCE` covering every `DISCOVERABLE_TERMS` member, states and eligibility unchanged.
- **Reconciled documents:** `docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md` (new §11.8 with command, counts, the failure and its correction, the A–F table, and an explicit "what this does not establish"; §6, §11.7, §11.9 and the header execution-status line updated) and `handoff/decisions/A30-document-class-and-field-level-withholding.md` (§5 rewritten with the executed result; decision status updated).
- **Not executed, and not claimed:** full backend suite `PYTHONPATH=engine python -m pytest -q tests/` (≈ 3 h); the wider focused command (notice parser, offer-table boundaries, OFS NIL binding, prospectus pathway, multi-source issue terms, automatic discovery); any ingestion run; any evaluation. Parser-level green is not ingestion validation.
- **Remaining:** trace `ing-42ded42dde7a41b2` still unavailable from every ref; price band and bid lot unresolved for this filing pending a price band notice or the final Prospectus; end-to-end ingestion unexercised.
- **Disposition: FOCUSED REGRESSION EXECUTED AND GREEN; FAILURE WAS TEST-SIDE; FIELD-LEVEL CORRECTIONS VALIDATED ON THE REAL DOCUMENT; FULL SUITE AND INGESTION REMAIN UNEXECUTED.**

## Paras Healthcare — wider validation and controlled ingestion — 2026-10-24 (revision 6)

- **Scope:** wider focused regression across nine modules, diagnosis and narrow correction of the failures, then a controlled non-production ingestion of the retained RHP. **No full suite (~3 h), no evaluation, no production ingestion, no scoring/config/schema/fixture change, nothing merged to `main`.** Branch `arena/07f3439f-ipo-screening-engine`, from `deb19ba`, `main` untouched at `01ba66c`.
- **Evidence re-verified:** sha256 `e0a3187f…570e74`, 11,577,075 bytes, 651 pages — unchanged before and after the ingestion run.
- **Wider focused command** (prospectus/RHP, price-band notice and classification, offer-table boundaries, OFS NIL binding, multi-source issue terms, automatic official discovery, phase-5J adversarial cases, both Paras modules): **219 collected → 215 passed / 4 failed**, then after corrections **221 passed / 0 failed / 0 skipped**. A further **91 cases** across nine adjacent extraction/resolution modules passed, bounding the blast radius of the production edits. Environment: CPython 3.11.2, pytest 9.1.1, pypdf 6.20.1, `PYTHONPATH=engine`.
- **Four failures:** (1) missing PIL/OCR dependencies in the rebuilt sandbox venv — environment, fixed by installing the pinned requirements, after which the real offline-OCR case passed; (2) `UNREADABLE_OCR_LINE` was still classed as a source placeholder, so a reading failure was reported as the issuer printing `[●]` — **production defect, corrected** (`_AMOUNT_UNKNOWN_MARKER`), amount still withheld; (3) a Draft RHP was refused with the generic role message instead of its class-specific one — **production regression from revision 2, corrected**; (4) `test_adversarial_d_conflicting_price_sources` still asserted the pre-A30 raise — **stale test contract updated** to assert the withheld band *and* the fail-closed final-mode gate, weakening nothing. Three regression cases added.
- **Controlled ingestion executed** through the supported upload path with `store_root` on `/tmp` and `IPO_OFFICIAL_DISCOVERY=0`: `ing-55319ecccdc243e4`, **BLOCKED**, `AWAITING_ISSUE_TERMS`, `evaluation_run: False`, `persisted: False`, evaluation store never created, artifact hash unchanged, no unrelated record touched.
- **Ingestion outcome vs expectation:** issuer identified; opening date `2026-10-21` resolved; price band and bid lot correctly withheld (`[●]` at pp. 9/11) and the eligibility gate correctly blocked. **But `issue.ofs` and `issue.close_date` remain unresolved on the ingestion path**, and `issue.fresh_issue` is stored as `5000.0` in a lakh-denominated input although the filing states ₹5,000 million (ten times too small).
- **Diagnosis:** the upload path never uses `PriceBandNoticeParser` / `parse_official_rhp`; it uses `SectionExtractor.extract_cover_and_offer` + `CanonicalInputBuilder`, which A30 did not touch. There (i) `BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026` defeats the close-date pattern because of the footnote marker, (ii) no branch reads a monetary Offer-for-Sale amount at all, and (iii) no unit conversion exists between an extracted `MILLION` and the canonical `INR_LAKHS`.
- **Not corrected, by design:** those three defects live in shared code every issuer's ingestion runs through, and only the full regression suite can bound the change — which this pass was forbidden to run. Leaving the gate blocked is the safe state; the defects are recorded as required work with a named blast radius.
- **Remaining:** full suite NOT RUN; evaluation NOT RUN; price band and bid lot unresolved pending a price band notice or the final Prospectus; trace `ing-42ded42dde7a41b2` still unavailable (the new run reproduces its documented symptoms but cannot be diffed against it); the three upload-path defects above remain open.
- **Disposition: WIDER FOCUSED SUITES GREEN; CONTROLLED INGESTION RUN AND CORRECTLY BLOCKED; UPLOAD-PATH GAP DIAGNOSED AND DOCUMENTED; ENGINE NOT EVALUATION-READY FOR THIS FILING.**

## Paras Healthcare — upload-path correction and validation — 2026-10-24 (revision 7)

- **Scope:** correction of the three defects the revision-6 controlled ingestion exposed in the **upload** path (`SectionExtractor.extract_cover_and_offer` → `CanonicalInputBuilder`), issuer-independent, with new regression coverage, a re-run of the focused/wider suites and a second controlled non-production ingestion. **No full suite (~3 h), no evaluation, no production ingestion, no scoring/config/schema/fixture change, nothing merged to `main`.** Branch `arena/07f3439f-ipo-screening-engine`, from `2316291`, `main` untouched at `01ba66c`.
- **Architecture preserved:** the parser path (`PriceBandNoticeParser` / `parse_official_rhp`, corrected under A30) is untouched; the upload path — the one ingestion actually runs — is corrected separately, and both are now pinned on the same evidence.
- **Defect 1 — close date.** `BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026` was unreadable because the pattern required whitespace after the label; the opening date, carrying no footnote marker, was read. Named `_ISSUE_OPENS` / `_ISSUE_CLOSES` patterns now tolerate a footnote marker (`#`, `*`, `†`, `(1)`, bare 1–2 digit reference, colon, dash) between label and date. Unrelated dates (certificate 1987, allotment 2026-10-27, the 2017 Articles definition) remain unreachable — tested.
- **Defect 2 — the monetary Offer for Sale was never extracted.** The upload path read only NIL or a seller share quantity. One reader, `SectionExtractor._explicit_component_amount`, now serves both `issue.fresh_issue` and `issue.ofs`: it reads `aggregating (up) to ₹ N <unit>`, refuses to cross a component label, refuses merged-header/adjacent-column labels (this is what kept the fresh-issue cell's ₹5,000 m out of the OFS field on the real cover), never infers from the placeholder share count, and withholds the field when two different amounts are stated. NIL binding and "missing is never zero" unchanged.
- **Defect 3 — monetary unit.** The schema already declares `issue.fresh_issue` and `issue.ofs` to be *"in reporting_unit"* and `enrichment_engine` consumes them that way, so `5000.0` under `INR_LAKHS` for a ₹5,000 **million** statement was a tenfold magnitude error. `CanonicalInputBuilder._normalize_issue_amount` converts once, at the only boundary that knows both `raw_unit` and the reporting unit (1 million = 10 lakh, 1 crore = 100 lakh); no unit or an equal unit is left untouched (no double conversion); an unconvertible unit yields `None` instead of a guess. **No new semantic decision** — the canonical contract already specified the unit.
- **Tests:** new `tests/test_upload_path_issue_terms.py` (27 synthetic cases: footnote variants, unrelated-date rejection, OFS money vs placeholder share count, seller rows, absent OFS, explicit NIL, conflicting amounts, a second issuer, and the conversion matrix incl. identity/unsupported units); 5 cross-path cases added to `tests/test_paras_evidence_regression.py` (14 total) running the real 651-page filing through `DocumentExtractor`. **Wider focused command (ten modules including the new one): 253 passed / 0 failed / 0 skipped.** Upload-path regression: `test_extraction` + `test_fixture_fallback_isolation` 20; `test_rk_fashion_reconciliation`, `test_fresh_issue_manual_entry`, `test_four_field_manual_terms`, `test_ingestion_activity`, `test_ingestion_worker_lifecycle`, `test_ui7_ingestion` 77; `test_extraction_phase5b`, `test_financial_statement_column_mapping`, `test_contingent_liabilities_extraction`, `test_auditor_evidence_section` 49; golden/semantics 54 — all passed.
- **Controlled non-production ingestion (re-run):** `ing-5bd0ea97160b409e`, mode `final`, **BLOCKED** with `AWAITING_ISSUE_TERMS`; `evaluation_run: False`, `persisted: False`, `evaluation_id: None`, evaluation store never created, artifact sha256 `e0a3187f…570e74` unchanged before and after. Missing fields are now **only** `issue.price_band_low`, `issue.price_band_high`, `issue.lot_size` — the three the filing prints as `[●]`.
- **Field outcomes on the real filing (upload path):** open `2026-10-21`, close `2026-10-23`, fresh issue `50000.0` INR_LAKHS (₹5,000 m), OFS `95000.0` INR_LAKHS (₹9,500 m), each with page-1 cover provenance and locator; price band and bid lot unresolved and correctly diagnosed; `fresh_shares` unresolved (`[●]`), not required by the gate.
- **Remaining:** full suite NOT RUN; evaluation NOT RUN; price band and bid lot unresolved pending a price band notice or the final Prospectus; trace `ing-42ded42dde7a41b2` still unavailable; the engine is **not** evaluation-ready for this filing while required terms are unresolved.
- **Disposition: UPLOAD PATH CORRECTED FOR ALL ISSUERS; PARSER AND UPLOAD PATHS AGREE ON THE REAL FILING; WIDER SUITES GREEN (253); INGESTION CORRECTLY BLOCKED ON THE TWO PLACEHOLDER TERMS; NOT EVALUATION-READY.**

## Paras Healthcare — final regression gate: full suite green — 2026-10-24 (revision 8)

- **Scope:** the full backend regression suite, executed twice at the published upload-path corrections, with the failures diagnosed and corrected. **No evaluation created, updated or scored; no production ingestion; no scoring/config/schema/fixture change; nothing merged to `main`.** Branch `arena/07f3439f-ipo-screening-engine`, from `415a883`, `main` untouched at `01ba66c`.
- **Full suite, `PYTHONPATH=engine python -m pytest -q tests/`** (CPython 3.11.2, pytest 9.1.1, pypdf 6.20.1):
  - run 1 at `415a883`: **1768 collected — 1758 passed / 10 failed / 0 skipped**, exit 1, 30 m 32 s;
  - run 2 after the two corrections: **1772 collected — 1772 passed / 0 failed / 0 skipped**, exit 0, 31 m 17 s.
- **Failure 1 — genuine A30 regression, verified evidence lost.** `NoticeSnapshotCache.get()` re-parsed every cached snapshot with `PriceBandNoticeParser`. A30 makes that parser refuse a prospectus *by class*, so a retrieved, verified, cached final Prospectus returned `(None, False)` — **a verified official document silently disappeared on the second resolution.** Corrected: `put()` records `document_class`; `get()` dispatches to the parser for that class (`ProspectusTermsParser` / `parse_official_rhp` / the unchanged OCR-aware notice path), with backward compatibility for entries written before the class was recorded. Four regression cases in the new `tests/test_notice_cache_document_class.py`. This is the most consequential finding of the pass: the A30 classification rule was correct, but one caller had not been updated.
- **Failure 2 — stale frozen-core pin (nine of the ten failures).** `extraction/price_band_notice.py` is one of six frozen-core files; its expected hash still pointed at the pre-A30 content, so `verify_frozen_core` returned False and the presentation API reported `frozen_core_status: CORRUPTED`. The pin is re-established at the reviewed A30 content with a comment naming A30 as the authority, mirroring the existing A15 precedent for `evaluation.py`. **Governance note: this is bookkeeping for an authorised change, not a new policy, and is flagged for RAMKI's ratification.** The independent protection for scoring output, `verify_golden_result()`, is unchanged and still reproduces `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`; the other five frozen files are byte-identical to their pins. If ratification is withheld, the remedy is to revisit the A30 change, not to restore the stale pin.
- **No assertion weakened, no test removed, none converted to a skip.**
- **Re-verification after the gate:** ten-module focused command + new cache module **257 passed**; `test_upload_path_issue_terms` + `test_paras_evidence_regression` + `test_official_rhp_terms_and_dates` **78 passed**; the nine previously failing modules **80 passed**. Real filing unchanged: open `2026-10-21`, close `2026-10-23`, fresh issue `50000.0` INR_LAKHS (₹5,000 m), OFS `95000.0` INR_LAKHS (₹9,500 m), price band and bid lot unresolved as `[●]`; parser and upload paths agree. Evidence sha256 `e0a3187fe18d1c12f88f29170291972714cf15be7946e8a7f4a7d8c914570e74`, 11,577,075 bytes — unchanged.
- **Evaluation / persistence:** **NOT RUN.** No evaluation created, updated, rescored or finalized; no evaluation store opened or written; no unrelated issuer record touched. The ingestion gate remains correctly closed on the two genuinely undisclosed terms.
- **Remaining:** price band and bid lot unresolved pending a price band notice or the final Prospectus; evaluation NOT RUN; trace `ing-42ded42dde7a41b2` still unavailable; engine **not** evaluation-ready for this filing while required terms are unavailable.
- **Disposition: FULL BACKEND SUITE GREEN 1772/1772 (exit 0); FROZEN CORE 6/6 AND GOLDEN RESULT PASS; ONE GENUINE A30 CALLER REGRESSION FOUND AND FIXED; FROZEN-CORE PIN RE-ESTABLISHED AND FLAGGED FOR RATIFICATION; NO EVALUATION TOUCHED.**

## Paras — frozen-core ratification evidence + official issue-term discovery — 2026-10-24 (revision 9)

Two separate workstreams this pass. **No evaluation created, updated or scored; no ingestion executed; no durable record written; no production code changed; PR #7 left open; `main` untouched at `01ba66c`.**

### Workstream A — frozen-core pin: VERIFIED, awaiting Ramki's ratification (NOT ratified)

- **Independent hash check.** The pin `5f6f0262f0e68acfe9feb1e2b44a6a0409c16fdf8b847763f86ba72fa3b9ed29` equals the CRLF-normalised sha256 of blob `6dd36d20e8f5561ff110af0ae3986e1e329d829c` — the reviewed A30 content at `4b1c67f`, still the blob at the published tip. The replaced pin `779afb0b…` is confirmed to be the pre-A30 content at `0e15ac7`.
- **Manifest diff.** One hash line changed plus four explanatory comment lines. No other frozen-core entry, no verifier logic, no comparison subject, no other production file.
- **No behaviour or policy added.** The pin is a constant consumed by the existing integrity check; the parser change it guards was authorised separately by A30. A future edit to that file still fails the check.
- **Golden result unchanged.** `verify_golden_result()` → `True`, `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`; `GOLDEN_RESULT_HASH` never edited. Frozen core 6/6 `True`.
- **Integrity tests.** LF/CRLF acceptance, real-content-change rejection, T-7-29/34/39/42, and `frozen_core_status` = `VERIFIED`: **39 passed / 0 failed / 0 skipped** (15.9 s).
- **Tamper detection.** Three genuine mutations of `price_band_notice.py` (append, mid-file class rename, single-byte flip at the midpoint) each produced `False` for that file with the other five still `True`; an unchanged control file produced `True`. Altered bytes fully restored — byte-identical file, empty `git status`, empty diff, same blob at `HEAD`, nothing committed or published.
- **Status: VERIFIED — READY FOR RAMKI RATIFICATION.** Not ratified. If ratification is withheld, the remedy is to revisit the A30 parser change, not to restore the stale pin.
- **Record:** report §15; A30 §5.6.

### Workstream B — official price-band and lot-size evidence: found, retained, still not resolvable

- **Found, issuer-matched, official.** BSE's issue-information page for this issue (issue no. 8048, symbol `PARASHLTH`, period 21–23 Oct 2026) publishes **Price Band `660.00-693.00`** and **Market Lot `21`** (Minimum Bid Quantity 21). BSE notice 20261019-49 corroborates the ₹693 cap for the anchor allocation. A SEBI filing independently states the fresh issue **₹5,000.00 million**, OFS **₹9,500.00 million**, total ₹14,500.00 million and the same bid/offer period — free corroboration of the date and monetary terms already resolved from the RHP.
- **Retained with provenance:** `evidence/non-authoritative/paras-healthcare-issue-terms-20261024/` — 4 captures, README, `capture-manifest.json` with URLs, quoted values and locators, byte counts and uppercase SHA-256 digests; the failed attempts are recorded there too.
- **Not retrieved:** the BSE Price-Band Advertisement `PBA_20261015184043.pdf` (the exact document class the notice parser targets) failed 3× through the agent proxy, and the sibling `Prospectus & GID` archive was not attempted. Recorded as a retrieval failure of `listing.bseindia.com`, **never** as evidence that the notice does not exist.
- **Not admissible through the current contract, and no code changed to admit it.** The page is BSE's *historical* view of a closed issue (`status=H`); the engine searches only the live listing, closed SPA records are excluded (`official_issue_sources.py`), and the historical listing is deliberately not in `LISTING_URLS`. Adding it would let any past issue by a similarly named issuer supply terms, since issuer identity is name-based — a contract decision for RAMKI, not a bug to slip in.
- **Transport is blocked here, independently.** The engine's `OfficialDiscoveryProvider` returns **UNAVAILABLE** (never NOT_FOUND) for all six listings on `URLError: TLS/SSL connection has been closed (EOF)`; `curl` to bseindia/nseindia/sebi/api.bseindia fails `(35) SSL_ERROR_SYSCALL` while DNS resolves.
- **The extraction layer is not the blocker.** Against a transcription of the real page's labelled rows, the **unmodified** `ExchangeIssuePageParser` returns `660.0` / `693.0` / lot `21` / `2026-10-21` / `2026-10-23` / `Paras Healthcare Limited`, class `EXCHANGE_ISSUE_PAGE`; the general discovery provider returns `FOUND` and the resolver `RESOLVED` for the three terms. New `tests/test_paras_official_issue_page_terms.py` — **17 passed**, including conflict-withholding, foreign-issuer rejection, missing-lot `PARTIAL`, no-provider `UNAVAILABLE` and searched-but-absent `UNPUBLISHED`; the fixture is pinned to the retained capture by quoted values and by manifest digests. **No production code changed.**
- **Wider focused gate run:** 11 modules (new module + resolver, official-discovery, BSE listing, OFS-nil binding, upload-path, Paras evidence, official RHP, cache class, multisource) — **230 passed / 0 failed / 0 skipped** (2 m 41 s).
- **Status: price band UNRESOLVED; bid lot UNRESOLVED; dates and monetary terms unchanged and independently corroborated; gate closed; evaluation NOT RUN; evaluation readiness NOT ESTABLISHED.**
- **Next concrete step:** configure the BSE Price-Band Advertisement URL through the existing `IPO_NOTICE_URLS` mechanism on a host with egress (no policy change, no new code; `listing.bseindia.com` is already allow-listed). Separately, if RAMKI wants closed issues discoverable, decide how a discovered page is tied to *this* issue rather than to a same-named issuer's earlier IPO.
- **Record:** report §16; A30 §5.7.

- **Disposition: PIN VERIFIED AND AWAITING RAMKI'S RATIFICATION; OFFICIAL PRICE BAND AND LOT EVIDENCE LOCATED AND RETAINED BUT NOT ADMISSIBLE AND NOT RETRIEVED THROUGH THE ENGINE; NO TERM RESOLVED; GATE CLOSED; NO EVALUATION; FULL SUITE LAST GREEN 1772/1772 AT `14a0047` AND NOT RE-RUN (NO PRODUCTION CODE CHANGED THIS PASS).**

## Paras — official retrieval trace + closed-issue identity binding — 2026-10-24 (revision 10)

**No evaluation created, updated, scored or persisted; no durable record written; PR #7 open; `main` untouched at `01ba66c`.**

### Retrieval trace — why UNAVAILABLE
- Traced end to end (DNS → TLS → session → endpoint → parser → matching), not inferred. **Only TLS egress fails**: every official host (`www.bseindia.com`, `www.nseindia.com`, `www.sebi.gov.in`, `api.bseindia.com`) connects at TCP then closes the TLS handshake; the engine's `urllib` transport and `curl` fail identically, and DNS resolves everywhere.
- The six configured listings therefore report `classification=failed, searched=False` and the provider returns **UNAVAILABLE** — never `NOT_FOUND`, because no report names a listing it actually read. The endpoint set, the cookie-jar/session warm-up, the issue-page parser and the issuer matching are all working; each was checked separately.
- **Diagnostics improved:** every retrieval failure now carries `[TRANSPORT]` / `[HTTP]` / `[CONTENT]`, so "never reached" and "reached and refused" are distinguishable without reading exception types (`HTTPError` classified before `URLError`/`OSError`, since it is both).

### Closed-issue evidence — narrow, identity-bound admission (A31)
- The live BSE listing no longer carries the Paras row (the issue closed on 23 Oct 2026); the historical listing does, linking the issue page that states the pricing terms. That is a **coverage** gap, not a parser defect.
- The live-only default was **not** removed. A closed record is now admissible only when bound to the exact offering: exact issuer **and** the filing's own bid window **and** the exchange issue number (`IPONo`) with a well-formed scrip id **and** internally consistent identifiers (link `startdt` vs row date, IPO record type). No expected window ⇒ **no admission**; conflicts and ambiguity ⇒ **withhold with a reason**; an older offering by the same issuer is rejected on the window before any value is read. The closed-issue listing is **off unless configured** (`IPO_OFFICIAL_HISTORICAL_LISTINGS`) and never substantiates `NOT_FOUND`/`UNPUBLISHED`, because a forthcoming issue cannot appear in a closed archive.
- Implemented in `engine/ipo_screening/issue_identity.py` + `bse_historical_issue_records` + `OfficialDiscoveryProvider._search_historical_listing`; `IssueTermsResolver` forwards the canonical `issue` context to providers that declare it. Issuer-independent; nothing names an issuer, symbol or issue number.
- **Recorded finding:** the exchange publishes its price-band advertisement as `PBA_<yyyymmdd…>.pdf` with anchor text "Click Here", which the attachment filter did not recognise. Recognised now — a naming rule inside the existing allow-list, still issuer-matched and class-verified after retrieval.
- **Decision boundary, not crossed:** admitting `listing.bseindia.com` as an operator-configured notice URL would reverse `test_archive_hosts_are_scoped_to_issuer_matched_discovery_not_direct_prospectus_urls`. The change was made, found to contradict that safeguard, and **fully reverted**; it is RAMKI's call under A31 §5.

### Tests and controlled validation
- New `tests/test_historical_issue_identity.py` — **35 passed** (bound / unbound / incomplete / stale / conflicted; previous offering; same-window different issue number; two issue numbers claiming one window; same issue listed twice; link/row date contradiction; non-IPO record; foreign and similar names; unreadable price cell; transport failure; source isolation; cross-issuer leakage; conflict withholding; cap-without-floor; lot vs maximum bid quantity; gate).
- `tests/test_paras_official_issue_page_terms.py` — **25 passed** (issue-page terms, closed-archive binding from the retained capture, advertisement-followed discovery, configured-URL rejection preserved, agreement across two document classes, gate).
- **Full backend suite re-run on final code** (this pass changed shared engine code, so the re-run was required): **1832 collected — 1832 passed / 0 failed / 0 skipped**, exit 0, 20 m 11 s (1772 previous + 60 new cases).
- Focused sweeps on final code: **451 passed** (22 issue-term/discovery/identity/upload-path/cache/integrity modules) and **141 passed** (provenance, manual terms, ui7, enrichment, worker lifecycle). **0 failed, 0 skipped.** No assertion weakened or removed; the one existing safeguard test this work initially broke was **not** edited — the code change was reverted instead.
- **Controlled non-production ingestion** (disposable `store_root` on `/tmp`, artifact hash-checked before/after, `mode=final`): **`AWAITING_ISSUE_TERMS`** on exactly `price_band_low`, `price_band_high`, `lot_size`; `evaluation_run: False`, `persisted: False`, `evaluation_id: None`, no evaluation store. Re-run with the historical listing configured: the archive search is genuinely attempted, recorded as `[TRANSPORT]`, outcome unchanged. Evidence PDF byte-identical (`E0A3187F…570E74`).

### Status, stated separately
- Frozen-core pin: **VERIFIED — READY FOR RAMKI RATIFICATION** (unchanged; not revisited).
- Official evidence retrieval: **PARTIAL** (issue page, historical listing, BSE notice, SEBI filing retrieved; the advertisement itself unreachable from here).
- Evidence admissibility: **identity-bound path implemented and tested**; live route transport-blocked here.
- `price_band_low` / `price_band_high` / `lot_size`: **UNRESOLVED** — no official bytes reached the engine in this environment; no value entered any configuration, canonical record or store.
- Required-term gate: **CLOSED** (verified). Evaluation readiness: **NOT ESTABLISHED**. Evaluation execution: **NOT RUN**.
- **Capability needed to finish live:** egress to `*.bseindia.com` / `nseindia.com` / `sebi.gov.in`, then `IPO_OFFICIAL_HISTORICAL_LISTINGS="https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P"` — the filing supplies the window, the archive row binds by issue number 8048, and the issue page supplies 660.00 / 693.00 / lot 21. No code change required.

- **Disposition: TRANSPORT BLOCKED AND PROVEN; CLOSED-ISSUE EVIDENCE NOW ADMISSIBLE ONLY BY IDENTITY BINDING (A31); ALLOW-LIST WIDENING REVERTED AND REFERRED TO RAMKI; 589 FOCUSED TESTS GREEN; GATE CLOSED; NO EVALUATION.**

## Paras — configuration-to-runtime wiring + operational handoff — 2026-10-24 (revision 11)

**No evaluation created, updated, scored or persisted; no durable record written; PR #7 open; `main` untouched at `01ba66c`. Production code changed this pass, so the full suite was re-run in this pass.**

### Egress re-checked (still closed)
- `curl` to the BSE historical listing, the BSE public-issue API and the price-band advertisement: `http=000`, `(35) SSL_ERROR_SYSCALL` in all three. Engine transport: `URLError: TLS/SSL connection has been closed (EOF)`. Agent proxy on the advertisement: **HTTP 500** (fourth attempt across two passes, three routes).
- Classified **transport failure**; not retried again without a change in conditions. Never `NOT_FOUND`, never `UNPUBLISHED`, never evidence that the document does not exist.

### Wiring trace and the two gaps closed
- **Verified chain:** `create_app()` → `PresentationService` (no injected resolver) → `build_resolver_from_env()` → `IPO_OFFICIAL_HISTORICAL_LISTINGS` → `OfficialDiscoveryProvider(historical_listing_urls=…)` → `_search_historical_listing` → `bse_historical_issue_records` → identity binding → linked issue page → parser → resolver → required-term gate → ingestion. Every link exercised.
- **Gap 1 — the chain was unproven.** New integration test builds the service exactly as `create_app` does and asserts the configured archive reaches the provider; and a run of the retained 651-page RHP through `ingest_document` with a recording resolver shows the filing's own window (`2026-10-21`..`2026-10-23`) and exactly the three pricing fields arriving at the resolver, then `AWAITING_ISSUE_TERMS` with no evaluation written. The identity rule is unusable without that window, so this is now guaranteed rather than assumed.
- **Gap 2 — misconfiguration looked like an outage.** A plain-HTTP entry, non-official host or IP literal in `IPO_OFFICIAL_HISTORICAL_LISTINGS` now registers a configuration-diagnostic provider (variable, entry position, reason; the value is never echoed). Usable entries still reach the provider, and a bad entry never disables discovery.

### Tests
- New `tests/test_historical_listing_wiring.py` — **14 passed** (env→provider, blank/extra entries, three unusable-entry classes, discovery-disabled, service construction, ingestion context delivery, evidence-backed resolution from the retained capture, foreign-issuer exclusion, prior-offering exclusion).
- Identity + wiring + issue-page modules: **74 passed**.
- **Full backend suite on final code: 1846 collected / 1846 passed / 0 failed / 0 skipped**, exit 0, 21 m 04 s (1832 previous + 14 new). No assertion weakened, skipped or removed.

### Operational handoff (report §18.4)
Commands, the only environment variable required, nine success criteria, and a failure-signature table (`[TRANSPORT]`, `IDENTITY_UNBOUND`, `STALE_OR_DIFFERENT_ISSUE`, `IDENTITY_CONFLICT`/`IDENTITY_INCOMPLETE`, `UNPUBLISHED`) so an egress-capable host cannot misread a transport failure as non-publication. Ingestion past the gate would create an evaluation and is explicitly not authorised.

### Status (unchanged where it must be)
- Frozen-core pin: **VERIFIED — READY FOR RAMKI RATIFICATION** (not revisited, not ratified).
- Official evidence: **retrieval blocked at transport** here; evidence retained and admissible by identity binding (A31).
- `price_band_low` / `price_band_high` / `lot_size`: **UNRESOLVED** — nothing entered any configuration, canonical record or store.
- Required-term gate: **CLOSED** (verified end to end). Evaluation readiness: **NOT ESTABLISHED**. Evaluation execution: **NOT RUN**.
- `listing.bseindia.com` configured-URL allow-list: **untouched and still RAMKI's decision** (A31 §5).

- **Disposition: WIRING PROVEN AND HARDENED; EGRESS STILL BLOCKED (PROVEN, FOUR ATTEMPTS); FULL SUITE 1846/1846 GREEN; OPERATIONAL HANDOFF COMPLETE; GATE CLOSED; NO EVALUATION.**

## Paras — operator host has egress; handoff made one-command — 2026-10-24 (revision 12)

**No evaluation created, updated, scored or persisted; no durable record written; PR #7 open; `main` untouched at `01ba66c`. Production code changed this pass, so the full suite was re-run in this pass.**

### What the operator's run established
- The operator's own Windows host retrieved **14,287 bytes** from `https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P`. The `[TRANSPORT]` blocker is a **sandbox** condition, not a project one; the external dependency is now cleared on the host that matters. This is a retrieval fact, **not** a resolution: the bytes have not been through the resolver.

### Two defects that run exposed, both corrected (report §19)
- **Operator error was being reported as a policy violation.** The configured value arrived as a Markdown link with an HTML-escaped `&` (`…?id=2&amp;Type=P`), and the previous build rejected it as "not an allowed official source host". `normalize_configured_url()` now strips Markdown link syntax, angle brackets and quotes, and unescapes entities **before** validation, for `IPO_OFFICIAL_HISTORICAL_LISTINGS` and the notice/prospectus URL maps. Narrowness is pinned by test: no scheme added, no host or path rewritten, foreign hosts still rejected. **No allow-list was widened** — `listing.bseindia.com` for configured notice URLs remains RAMKI's decision (A31 §5).
- **A 14 KB response could masquerade as a read listing.** `bse_historical_issue_records(..., diagnostics=…)` now reports `issue_rows` / `issuer_rows` / `bound_rows` / `rejections`, and the archive reader distinguishes *"carried no issue-information links at all … nothing may be concluded from its silence"* from *"carried N issue row(s) but none for this issuer"*. A shell is no longer indistinguishable from an answer.

### The handoff is one command, read-only (A31 §4b)
- `python engine/tools/ipo_screen.py issue-terms --issuer … --open … --close … [--fields …] [--json]` — prints status, per-source `searched`/`failed`/`historical`/`homepage`, every rejection note, and per field value / verification / URI / quote / locator. Exit `0` = RESOLVED, `1` = not resolved, `2` = usage. Writes nothing, creates nothing.
- Report §19.2 carries the exact PowerShell block and the expected output, including the `IDENTITY_UNBOUND` refusal when the window is omitted (a closed record is never usable on a name match alone).

### A genuine determinism defect found by the full suite (report §19.5)
- `test_workbook_bytes_are_deterministic` failed only when two serialisations straddled a two-second boundary: `openpyxl` rewrites `docProps/core.xml`'s `dcterms:modified` **and** every ZIP entry timestamp at `save()`, so pinning `properties.created/modified` never pinned the bytes. That matters beyond the test — the provenance store writes the file and derives the content hash from it.
- `deterministic_workbook_bytes()` repacks the archive with `dcterms:modified` = `1980-01-01T00:00:00Z` and every entry at `(1980,1,1,0,0,0)`; `workbook_bytes()` and `project_store` both serialise through it, so **the bytes written and the bytes hashed are the same bytes**. Regression case re-serialises across a tick.

### Tests
- New `tests/test_issue_terms_cli.py` — **19 passed**.
- `tests/test_reproducibility_store.py` — **33 passed**; the other workbook-writing modules — **85 passed**.
- **Full backend suite on final code: 1866 collected / 1866 passed / 0 failed / 0 skipped**, exit 0, 22 m 05 s. (First run this pass: 1864/1 — the determinism defect above; fixed in production code, not in the test.) No assertion weakened, nothing skipped or removed.

### Status (unchanged where it must be)
- Frozen-core pin: **VERIFIED — READY FOR RAMKI RATIFICATION** (not revisited, not ratified).
- Sandbox egress: still blocked at TLS. **Operator-host egress: works.**
- `price_band_low` / `price_band_high` / `lot_size`: **UNRESOLVED** — pending the operator run of §19.2; nothing entered any configuration, canonical record or store.
- Required-term gate: **CLOSED**. Evaluation readiness: **NOT ESTABLISHED**. Evaluation execution: **NOT RUN**.

- **Disposition: OPERATOR EGRESS CONFIRMED; PASTE AND SHELL-RESPONSE DEFECTS FIXED; RESOLUTION NOW ONE READ-ONLY COMMAND; WORKBOOK DETERMINISM DEFECT FOUND AND FIXED; FULL SUITE 1866/1866 GREEN ON FINAL CODE; GATE CLOSED; NO EVALUATION.**

## Paras — why the score was 8.0: reading defects, corrected — 2026-10-24 (revision 13)

**No evaluation created, updated, scored or persisted; no store written; PR #7 open; `main` untouched at `01ba66c`. Production code changed this pass, so the full suite was re-run in this pass. Frozen core untouched and re-verified.**

### The question
The operator's run returned `Final Score 8.0 / Available 29 / Unknown 71 / INSUFFICIENT DATA` after the previous passes' fixes. Reproducing it on the retained 651-page RHP (sha256 `E0A3187F…570E74`) gives **exactly** those numbers, so "what is missing?" is answerable item by item rather than by inference.

### The answer: the engine was reading very little of the filing
Four **reading** defects in the shared extractor, all "the fact is on the page and the reader does not see it". **No threshold, weight, criterion, knockout or allow-list was changed**, and a value printed as `[●]` still stays unknown.

| # | Filing (page) | Was read | Why |
|---|---|---|---|
| 1 | `(All amounts are in INR million, unless otherwise stated)`; `Amount (₹ million)` (pp. 151-157, 372-374) | `INR_LAKHS` | the unit detector's `\b` can never match before `₹` after `(`, and `in INR million` was not an accepted form. **Every statement value was ten times too small** against an issue size normalised on a different path. |
| 2 | `Profit/(loss) for the period/year (A)` (p. 372) | PAT `None`, all years | only `for the year` / `profit after tax` were accepted |
| 3 | `Net cash generated from operating activities (A)` (p. 373) | CFO `None`, all years | only `provided by` / `from` / `flow from` were accepted |
| 4 | `SUMMARY OF CONTINGENT LIABILITIES` … `Total … 3,905.01 …` (p. 91) | `None` → **K5 unverifiable** | the note is captioned `32. Commitments and contingencies` and is prose; the tabular summary was never consulted |

A fifth defect — `use_of_proceeds = []` from an unread `OBJECTS OF THE OFFER` table (pp. 129-130) being read as "no allocation", i.e. `mixed_ok` and 2 of 4 points — sits in `engine/ipo_screening/derived.py`, **frozen core**. The guard was written, the frozen-core tests caught the modification, and the file was restored to its pinned bytes (`0a6ef86a…56237`) **before anything was committed**; the ten resulting failures pass again. The change is **referred to Ramki**, not taken — a frozen-core edit is not this pass's authority, and the rule against changing the core to obtain a result applies to a good-faith correction too.

### The corrected outcome, and the knockout
```
before:  final 8.0   available 29.0   unknown 71.0   K5 UNVERIFIED
after :  final 9.0   available 34.0   unknown 61.0   K5 TRIGGERED
```
The number moves by one point; the **verdict** moves from "insufficient data" to "knocked out". The filing discloses contingent liabilities of **3,905.01 against FY2026 net worth of 3,949.41 = 98.88%** — the exact ratio its own risk factor states — far above K5's 50% threshold. K3 becomes decidable (OFS = 65.5% of the offer, so CLEAR), `profit_declining` is a genuine `False`, `margin_trend` scores 1/5 ("volatile": loss → larger loss → profit) and `cfo_quality` is correctly **NOT APPLICABLE** (cumulative PAT is negative), not missing. The 9.0 still includes the 2 frozen-core points described above.

### What remains missing, classified (report §20.4)
- **Recoverable by reading** (~16 pts): `ofs_seller_type` (p1: Promoter ₹3,000.00 m + Commelina Ltd ₹6,500.00 m), `industry_growth` (p204: 10-12% FY25-30P), `concentration` (pp60-61: top-5 suppliers 21.94%; customers genuinely not disclosed), `auditor` (p99: no change in three years), `board_kmp` (p351), `visibility` (p39: 2,211 → 3,011 beds).
- **Policy-blocked** (~8 pts): `rpt`/K6 wait on the approved metric definition (2026-10-17 record); `moat` is a qualitative rating.
- **`[●]`-undisclosed** (~7 pts): `promoter_post_holding` (p123: 72.80% pre, `[●]` post), `dilution`, `promoter_ofs_pct` — all need the post-issue share count; deriving it from price would be shares × price, which policy forbids.
- **Market/peer data a filing cannot contain** (30 pts): Module B (20) needs a peer snapshot and a post-issue EPS; Module F (10) is post-open observation.
- **Knockouts needing a negative-disclosure rule**: K1 (unmodified opinion, no going-concern paragraph, p367) and K2 ("no disciplinary actions … by SEBI or the Stock Exchanges against our Promoter in the last five Fiscals", p493). Both are explicit negatives; wiring them without an approved rule risks the mirror image of the Jio failure, where a *positive* SEBI proceeding was lost to a span filter.

Also recorded: the run used `THIRD_PARTY_AGGREGATOR_OVERRIDE` for the three pricing terms although the operator's host can reach the official sources and the identity-bound closed-issue path already exists (§19).

### Tests
- New `tests/test_paras_extraction_gaps_20261024.py` — **22 passed** (all five unit scales; a body sentence must not declare a unit; PAT/CFO caption variants with interim columns; the summary Total in both date conventions; the lead-in sentence must not become columns; four fail-closed cases).
- `tests/test_paras_evidence_regression.py` — **18 passed**, pinning the filing's own PAT (`-153.31 / -579.83 / 438.34`), CFO (`924.77 / 861.91 / 1,635.12`), contingent liabilities (`3,905.01` ⇒ 98.88%) and `K5 TRIGGERED` through the engine's own derivation and knockout modules.
- Two existing assertions were **corrected, not weakened**: the upload path's `reporting_unit == "INR_LAKHS"` with `50,000/95,000` encoded the unit defect itself; it now reads `INR_MILLIONS` with `5,000/9,500` and additionally pins the unchanged 34.48% fresh-issue share.
- Full backend suite on final code, frozen-core verification and the golden result: see §20.6 of the report.

### Status (unchanged where it must be)
- Frozen-core pin: **VERIFIED — READY FOR RAMKI RATIFICATION** (unmodified this pass; re-verified after the reversion).
- `price_band_low` / `price_band_high` / `lot_size`: **UNRESOLVED at runtime** — pending the operator run of report §19.2; nothing entered any configuration, canonical record or store.
- Required-term gate: **CLOSED**. Evaluation readiness: **NOT ESTABLISHED**. Evaluation execution: **NOT RUN**.

- **Disposition: THE 8.0 WAS A READING FAILURE, NOT A SCORING ONE; FOUR EXTRACTOR DEFECTS CORRECTED; CORRECTED RUN = 9.0 WITH K5 KNOCKOUT (CONTINGENT LIABILITIES 98.88% OF NET WORTH); FROZEN-CORE PROCEEDS GUARD REVERTED AND REFERRED; REMAINING GAP CLASSIFIED WITH PAGES; GATE CLOSED; NO EVALUATION.**

## Vishal blocked — the corrections are not issuance-specific; the missing input is one official document — 2026-10-24 (revision 14)

**No evaluation created, updated, scored or persisted; no store written; PR #7 open; `main` untouched at `01ba66c`. Frozen core untouched.** Full suite re-run on final code this pass.

### The question
A second issuer (Vishal Nirmiti, `ing-705ae38e44634a52`) blocked on `price_band_low`, `price_band_high`, `lot_size`, `ofs`. Were revision 11's corrections built around Paras?

### The answer: no, and the run demonstrates it two ways
1. **No production file changed in revision 11 names an issuer** — the readers key off document captions, not names or pages.
2. **They were still wrong for Vishal**, which is what issuer-specific over-fitting looks like from the inside: Vishal prints `As at March 31,` / `2026` on two lines, the Paras-derived reader matched dates line-by-line, saw no columns, and read nothing. The header is now joined and whitespace-normalised. Both filings now read their section total — **Vishal 2,186.64 (25.2% of net worth; below K5's threshold), Paras 3,905.01 unchanged**.

### All four of Vishal's missing fields are one missing document
| Field | Why it is missing | Correct? |
|---|---|---|
| `price_band_low` / `high`, `lot_size` | the RHP prints `“Cap Price” … ₹[●]` and `“Bid Lot” [●]` (pp. 1, 585, 629) | yes — an RHP cannot supply them |
| `fresh_shares` | cover reads `UP TO [●] EQUITY SHARES`; 65,90,909 is in the final Prospectus | yes |
| `ofs` | `issue.ofs` is **derived** as Σ(seller shares) × Cap Price; seller Vaman Prestressing 15,00,000 shares *was* read, so the amount cannot exist without the band | yes — not an independent gap |

### Why it worked before: the official document is not configured
Vishal has resolved end-to-end via the **Prospectus pathway** (`OFFICIAL_VERIFIED` floor ₹208 / cap ₹220 / lot 68, `SRC-PROSPECTUS-…`) when `IPO_PROSPECTUS_URLS` / `IPO_PRICE_BAND_NOTICE_URLS` name an official document. The failing run's provider list contains **only** `official-discovery`: no notice, no prospectus, no platform, no retained directory. Automatic discovery cannot substitute — NSE and BSE issue pages are JavaScript shells, SEBI's listing 404s, and the BSE/NSE APIs returned no issuer-matched records. Every one of those is reported as *could not be searched*, never as an absence.

### §19.2 retracted
Revision 10 told the operator to resolve terms from `.../PublicIssues/IPOIssues?id=2&Type=P` and expected 660/693/21 from it. **That was wrong.** The same URL on the operator's own host returns the same 14,287 bytes — a JavaScript application shell with **no issue-information links**, as the revision-10 diagnostic now reports verbatim. "14,287 bytes arrived" was true; "the closed-issue route is therefore usable" was not.

### Also changed
- **Third-party refusal now states its cause.** One message covered four situations. It is now `IDENTITY_WINDOW_UNREADABLE`, `IDENTITY_UNBOUND`, `STALE_OR_DIFFERENT_ISSUE` (**with both windows printed**), or a host/document-class refusal. A window naming its year once (`30 Sep - 5 Oct 2026`) is read when exactly one interpretation is a plausible bid window (≤ 31 days); underdetermined windows stay unread.
- **One-shot official documents for a single issuer:** `ipo_screen.py issue-terms --notice-url … | --prospectus-url …` — same official-host allow-list, same document classes, refused as a usage error *before* retrieval if the host is not official (including `listing.bseindia.com`). For the UI path the durable fix is still the environment variable.

### Tests
- `tests/test_aggregator_issue_terms.py` — **41 passed** (6 new: the four verdicts, year-once windows, underdetermined windows).
- `tests/test_issue_terms_cli.py` — **24 passed** (3 new: one-shot notice resolves without env config; three out-of-policy URLs refused before any retrieval; one-shot prospectus uses the prospectus document class).
- `tests/test_paras_extraction_gaps_20261024.py` — **23 passed** (1 new: a column header split across lines).
- Real-filing Vishal suites (`test_cross_ipo_issue_term_provenance`, `test_derived_evidence_registration`) — **7 passed**, golden hash `e84f8bc0…` unchanged.
- Full backend suite on final code: see report §21.6/§21.7.

### Status
- Frozen-core pin: **VERIFIED — READY FOR RAMKI RATIFICATION** (untouched this pass).
- Vishal and Paras pricing terms: **UNRESOLVED**; the blocker is an official document for the issuer, not the reader.
- Required-term gate: **CLOSED** and behaved correctly on both issuers. Readiness: **NOT ESTABLISHED**. Evaluation: **NOT RUN**.

- **Disposition: NOT ISSUANCE-SPECIFIC — PROVEN BY RUNNING A SECOND ISSUER, WHICH ALSO EXPOSED A LAYOUT-SPECIFIC READER NOW FIXED; VISHAL'S FOUR BLOCKS ARE ONE MISSING OFFICIAL DOCUMENT; HISTORICAL-LISTING GUIDANCE RETRACTED; THIRD-PARTY REFUSAL NOW STATES ITS CAUSE; ONE-SHOT OFFICIAL URL FLAGS ADDED; GATE CLOSED; NO EVALUATION.**

## Pass-9 Arena remote verification — 2026-10-25 (revision 15)

**Scope: remote/source verification only. No Windows checkout accessed. No issuer evaluation or persistence performed.**

### Remote publication and content readback
- Pass-9 target is commit `a6f9bb3dd4647dad5b9546d466d6db8d0c2d3fd1` (parent `b15203875f7bf340b5d9e768c7e8da572b8f1505`). GitHub independently identifies its eight changed paths as the Paras report, `aggregator_issue_terms.py`, `financial_tables.py`, `ipo_screen.py`, this tracker, and the three requested tests.
- The target commit is already published as an ancestor of PR #7 head `dd94cb8120916044499769ead02785eb673db126` on `arena/07f3439f-ipo-screening-engine`. PR #7 is OPEN and unmerged; it is based on PR #6's branch `arena/5dd3fe52-ipo-screening-engine`. `main` remains at `01ba66c12ca1195fd7acbd287c3e39a019808094` and does not contain the target.
- Remote readback at the PR #7 head: all eight Pass-9 paths exist; seven are byte-identical to target. The Paras report has four later-added lines documenting the read-only Windows verifier. No Pass-9 code or test changes were missing. The local Arena checkout initially contained none of the eight paths because its starting HEAD was the handoff-only `main`; the fetched authoritative PR branch did contain them.

### Arena execution at the exact target
The source snapshot was created from target commit `a6f9bb3...` in an isolated temporary directory, with the repository's pinned `requirements.txt` installed in a fresh Python 3.11 virtual environment. Commands executed:

```text
python -m pytest -q tests/test_aggregator_issue_terms.py tests/test_issue_terms_cli.py tests/test_paras_extraction_gaps_20261024.py
88 passed, 0 failed, 0 skipped; 1 Starlette/httpx deprecation warning; exit 0.

python engine/tools/ipo_screen.py issue-terms --help
exit 0; output includes --notice-url NOTICE_URL and --prospectus-url PROSPECTUS_URL.
```

No failures required correction. The combined targeted run covered 41 aggregator tests, 24 CLI tests and 23 extraction tests. This is not a claim that the full suite was run in Arena for this verification.

### PR/CI evidence and disposition
- Target commit's GitHub Actions `regression` check: **SUCCESS**, completed 2026-10-24 19:26:35 UTC (run 40123391593).
- PR #7 latest head check: **regression PASS**, completed 2026-10-25; PR remains **OPEN / UNMERGED**. The target is therefore remotely published for review, not integrated into `main`.
- **Disposition:** Pass-9 implementation and tests were already present remotely; Arena independently executed all requested focused tests and confirmed both CLI flags. This revision records that evidence; it does not represent local Windows verification or a full-suite run.

## Pass-9 post-merge integrity and regression closeout — 2026-10-25 (revision 16)

**Scope:** one-pass post-merge verification against the fetched authoritative `main`. The historical target-commit evidence below is preserved and is not reused as proof of the final-`main` run. No Windows checkout was accessed; no Windows-local test is claimed.

### Baseline frozen before testing

- `git fetch --prune origin` and the required history fetch completed successfully. The checkout was initially shallow; `git fetch --unshallow origin` completed before ancestry verification. The tested baseline was clean, with the fixed session branch and `HEAD` both at `aef84b17463a638f4c6f9a0086bc6c9d780e1da6`.
- `origin/main` was exactly `aef84b17463a638f4c6f9a0086bc6c9d780e1da6`; it had **not advanced** beyond the requested authoritative commit. Its subject is the PR #7 merge, its tree is `97b4dbbd9b5bc23c0dbaedf25efd3c454410e56c`, and its parents are `01ba66c12ca1195fd7acbd287c3e39a019808094` and `199629074a6130d620a07936fe9bf700534ce244`.
- The tested tree was therefore the final merged `main`, not the earlier `a6f9bb3` snapshot. The working tree remained clean after the test/check phase; the local `.venv`, Python bytecode, and pytest caches are ignored environment output.

### Target evidence versus final-main evidence

- **Target-commit evidence, retained from revision 15:** at `a6f9bb3dd4647dad5b9546d466d6db8d0c2d3fd1`, the earlier Arena run reported **88 passed, 0 failed, 0 skipped** for the focused suite and confirmed the two CLI flags. That is historical evidence for the target commit only, not evidence for this final-main run.
- **Final-main targeted command, executed here:**

  ```text
  PYTHONPATH="$PWD/engine" .venv/bin/python -m pytest -q tests/test_aggregator_issue_terms.py tests/test_issue_terms_cli.py tests/test_paras_extraction_gaps_20261024.py
  ```

  Exit `0`; **88 passed, 0 failed, 0 skipped** in 1.20 s. One warning was emitted: `StarletteDeprecationWarning` from `fastapi.testclient` because using `httpx` with `starlette.testclient` is deprecated and `httpx2` is recommended. The three module totals were 41 + 24 + 23.
- **Final-main CLI command, executed here:** `PYTHONPATH="$PWD/engine" .venv/bin/python engine/tools/ipo_screen.py issue-terms --help`. Exit `0`. Help output contains both `--notice-url NOTICE_URL` and `--prospectus-url PROSPECTUS_URL`.

### Broader regression and required checks

The documented Python invocation was run in a fresh repository `.venv` after installing the pinned `requirements.txt` (Linux, Python 3.11.2). Node was v22.22.3 and npm was 10.9.8.

- `PYTHONPATH="$PWD/engine" .venv/bin/python -m pytest tests/ -q` — **1908 collected and 1908 passed, 0 failed, 0 skipped**, exit `0`, 1635.50 s. The 25 warnings were all Starlette deprecation warnings: one `httpx`/`TestClient` warning and 24 `HTTP_422_UNPROCESSABLE_ENTITY` deprecations from the FastAPI routing path. No deselection or skip was used or concealed.
- `npm --prefix frontend test` — **93 passed, 0 failed, 0 skipped**, exit `0`. npm printed only its available-version notice.
- The workflow-required schema/integrity script passed: all four JSON schemas validated; `verify_frozen_core()` **PASS**; `verify_golden_result()` **PASS**; `verify_v1_6_implementation()` **PASS** (v1.6 inactive). `python -m compileall -q engine` exited `0`.
- The pre-publication clean-tree checks `git diff --exit-code` and `git diff --check` both exited `0`. GitHub's PR #7 `regression` check also succeeded on its final pre-merge head `199629074a6130d620a07936fe9bf700534ce244` (run `40177190214`, completed 2026-10-25 08:55:28 UTC). GitHub returned no check-runs for the merge commit itself; the final-main full-suite and required checks above are the direct evidence for this closeout.

### Eight-path and history integrity

All eight required Pass-9 paths existed in the tested final tree:

1. `engine/ipo_screening/aggregator_issue_terms.py`
2. `engine/tools/ipo_screen.py`
3. `engine/ipo_screening/extraction/financial_tables.py`
4. `tests/test_aggregator_issue_terms.py`
5. `tests/test_issue_terms_cli.py`
6. `tests/test_paras_extraction_gaps_20261024.py`
7. `docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`
8. `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`

- `a6f9bb3` is an ancestor of final `origin/main`; `git merge-base a6f9bb3 origin/main` is exactly `a6f9bb3`. The PR #7 head `1996290` has the same tree as final `main`, so the merge introduced no tree drift. The final tree has no deletions relative to the target, PR #7 head, or PR #6 head. The six Pass-9 implementation/test blobs are byte-identical to the target. The Paras report and tracker intentionally have later documentation updates, so they are not incorrectly described as byte-identical; no Pass-9 code or test path was lost.
- PR #6 head `e05c0efbca1ecb3024e52da73a22e180ea171118` is also an ancestor of final `main`; `git diff origin/main...e05c0efbca1ecb3024e52da73a22e180ea171118` is empty. No PR #6-only effective change remains. The absence of deletions, the exact merge-tree equality, the eight-path readback, and the clean pre-publication diff checks cover the accidental-change/missing-file check for this closeout.

### PR #6 reconciliation and remote status

- PR #6 was `OPEN` before this reconciliation, with head `e05c0efbca1ecb3024e52da73a22e180ea171118` on `arena/5dd3fe52-ipo-screening-engine` and base `arena/573e69a4-ipo-screening-engine`. Its effective diff against final `main` was empty; it was not merged and its commits were already incorporated through the PR #7 lineage.
- PR #6 was therefore closed on 2026-10-25 with a factual comment citing the ancestor and empty effective diff. Remote readback confirms PR #6 is now **CLOSED**, `mergeCommit: null`; no distinct follow-up action remains. This is a lifecycle disposition, not a claim that the historical PR #6 branch was independently merged.
- Final remote readback before this tracker publication: `git ls-remote origin refs/heads/main` resolved to `aef84b17463a638f4c6f9a0086bc6c9d780e1da6`; PR #7 is `MERGED` at that SHA; the fixed session branch remains the only branch used for this reconciliation. Tracker revision before this entry was **15**; this append-only reconciliation is **revision 16**. The publication commit and final post-publication remote SHA are supplied in the closeout receipt after the tracker change is integrated.

### Remaining limitations and boundary

- The full backend and frontend suites, local workflow-equivalent integrity checks, and targeted final-main run all passed. The only observed test warnings are the deprecations recorded above; they did not conceal failures or skips.
- There is no separate GitHub Actions check attached to the final merge commit because the repository workflow is configured for the A9 branch push/workflow-dispatch boundary rather than `main`; the successful PR #7 check and the exact final-main local runs are not conflated with a post-merge GitHub check.
- Windows-local validation remains **not run by Arena and not claimed**. Official-source reachability, browser acceptance, or any user-local Windows runtime behavior remains outside this remote Linux verification.


## Test-suite performance optimization — 2026-10-25 (revision 17)

- **Authority and baseline:** standing personal-use authority plus explicit
  one-pass commit/push/PR approval; fixed branch
  `arena/cf756dd1-ipo-screening-engine`, fetched authoritative `origin/main`
  `dedb4b876cdc68bdf3023d9740dc13f6888b45b3`. No branch switch or main update.
- **Scope:** test-only opt-in immutable page-text reuse in eight audited modules;
  conservative fast/integration/slow classification; five cache-isolation tests
  and one inventory guard; commands and evidence documentation. The initial
  17-file diff was fully audited; this append-only tracker reconciliation is an
  intentional 18th path, not unreported implementation scope.
- **Independent local verification:** unfiltered **1,914 passed**, 0 failed,
  skipped or deselected, 25 unchanged deprecation warnings; pytest 1,002.76 s,
  shell wall **16m44.233s**. All original 1,908 tests retained; no consolidation
  or removal. Original function/class bodies and parametrization unchanged in
  the eight modified test modules (102 top-level test functions).
- **Performance:** original baseline **32m52.110s**, first optimized run
  **16m30.112s** (49.79% reduction); independent rerun **16m44.233s** (49.08%).
  Single-run observations, not controlled statistical/Windows benchmarks.
- **Additional local checks:** Pass-9 **88 passed**, 1 warning, 1.29 s pytest
  elapsed; frontend **93 passed**, no failures/skips; all four schemas, six
  frozen-core pins, golden result, inactive v1.6 and compileall/whitespace PASS.
- **Isolation:** fresh real readers, domain extractors and canonical builds;
  issue-term/evaluation/persistence gates unchanged; no shared mutable service
  stores or canonical data. First parses, separate CLI processes, issuer
  canaries, fallback-isolation, notice-cache invalidation and Windows retrieval
  boundaries remain uncached where documented.
- **Governance:** no scoring, schema, frozen-core, source-qualification,
  official-source acceptance or evaluation-admission change. Golden hash stays
  `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`;
  active baseline v1.5.0, v1.6 inactive. No issuer store, release or deployment
  written. Windows-local validation not performed or claimed.
- **Publication/evidence:** `docs/TEST_PERFORMANCE.md` holds commands and cache
  boundaries; `docs/TEST_PERFORMANCE_RESULTS.md` preserves original and independent
  results/limitations. Publication and remote CI receipts are recorded on the PR
  separately from local regression evidence. No merge is requested by this entry.

### Revision 17 publication reconciliation

- Initial 18-path implementation/tracker commit
  `96cd9bd548b24b86caa1f89e2c0ab0a6cf509cd8` is published on the fixed branch as
  [PR #10](https://github.com/ramkivs/ipo-screening-engine/pull/10), base `main`.
  Initial direct readback: OPEN, MERGEABLE, CLEAN; no merge performed.
- Independent fast rerun: **1,037 passed**, 877 explicit deselections, 0 failed/
  skipped, 1 warning, 75.85 s pytest / 76.908 s shell wall. The unfiltered rerun
  still executes all 1,914 cases without deselections.
- Full workflow dispatch was actually attempted and rejected with HTTP 403
  (integration permission); the prior push trigger targets an older Arena branch.
  The follow-up therefore deliberately adds a two-line `pull_request` event for
  `main` to the existing A9 workflow, an explicit **19th** changed path. Its full
  job, permissions, scope choices and failure propagation remain unchanged;
  PR events select full. This is CI reachability repair, not test exclusion or
  permission expansion. Complete changed-path manifest is in the results report.
- Final remote run/SHA/conclusion and PR mergeability receipts belong on PR #10's
  Checks tab and final verification comment, distinct from the local benchmark
  evidence above. This entry does not pre-claim green CI, merge, release, source
  qualification or Windows validation. Historical tracker entries remain intact.

### Revision 17 remote full-CI receipt

- Code/CI head **`3ba28f6f67998cb6c9b6b1abf5f4fcf5b75ee502`**, PR #10:
  [Actions run 40194048213](https://github.com/ramkivs/ipo-screening-engine/actions/runs/40194048213)
  **SUCCESS**, check-run/job **121170970031**, 12:39:09–12:57:09 UTC on
  2026-10-25. Direct JUnit annotation: **1,914 tests, 0 failures, 0 errors,
  0 skipped, 1,048.850s**. All backend/frontend/integrity/compileall/clean-tree
  steps succeeded. These are remote API receipts, separate from Arena timings.
- Post-run PR state **OPEN / MERGEABLE / CLEAN**, not merged; remote main stays
  `dedb4b876cdc68bdf3023d9740dc13f6888b45b3`. All 19 remote file blobs match
  local committed blobs. Synthetic PR merge `3d91b72241c058eb39d185f6cb368bd7391e7eed`
  has the same tree as the code head; it is not a merge into main.
- Remote action annotations warn about Node.js 20 actions being forced onto 24
  and announce the Ubuntu 26 label migration. Bulk log download hit an external
  results-host EOF, so remote pytest warning count/frontend count are not
  independently asserted; local **25 warnings / frontend 93 passed** remain the
  local evidence. Full counts and every step conclusion were recovered via API.
- This receipt is documentation/tracker-only; tests and workflow unchanged from
  the successful code/CI head. Final documentation-head SHA and its own remote
  full-check receipt are recorded in PR #10's final verification comment. No
  merge, release, deployment, production change or Windows validation implied.


## Windows test portability continuation — 2026-10-25 (revision 18)

### Authority, actual checkout and scope

- This continues the user's one-pass execution on the fixed branch
  `arena/cf756dd1-ipo-screening-engine` and existing **PR #10**, which remains open;
  no merge is authorized or performed. Baseline `dedb4b876cdc68bdf3023d9740dc13f6888b45b3`
  and published optimization `dfa34b26a45b672dc92bcaed337e48f7a2b4ca13` are preserved.
- Arena restoration actual HEAD was **dedb4b8**, with all 19 optimization files
  byte-identical to fetched **dfa34b2**: **13 unstaged tracked edits + 6 untracked
  files, no staged changes and no unrelated/harness edit**. This is separate
  from the user's Windows checkout at dfa34b2 with a local harness modification.
- No reset, clean or file overwrite conceals this discrepancy. The verified
  correction index tree is committed with published dfa34b2 as parent, then the
  existing branch ref is advanced by compare-and-swap; published history stays
  intact and the focused diff excludes the already published optimization.
- Eight correction paths: `.gitattributes`, `requirements.txt`,
  `tests/test_reproducibility_store.py`, `tests/test_retained_bytes_portability.py`,
  `tests/diagnose_windows_portability.py`, the two performance documents and this
  tracker. No production/config/scoring/schema/fixture/retained-evidence/CI or
  `tests/gmp_mechanics_harness.py` content changes. Combined PR scope is 24 paths,
  versus the original optimization's 19; correction alone is eight paths.

### Windows observations and justified corrections

- User-supplied optimized Windows full run: **1,907 passed, 7 failed, 57 warnings,
  26m42s**. The original-baseline comparison selected only the same seven cases:
  **7 failed, 1 warning, 103.81s**. It was **not a full-suite baseline** or an
  independent Arena/Windows run; timing cannot establish a Windows speed ratio.
- InvestorGain retained transcription: original/declared `bd6bea50…51d772`,
  CRLF-converted `bbffd774…620d60` **exactly matches** the reported failure.
  Narrow `-text` attributes preserve it; original bytes/checksum unchanged.
- Paras exact failing capture is
  `evidence/non-authoritative/paras-healthcare-issue-terms-20261024/source-captures/bse-displayipo-4895-chunk-0.md`.
  Original/declared `908ed218…c0b70`; old Git autocrlf checkout yields
  `cac731bf…a803f`; corrected checkout yields the original. All four captures
  are narrowly protected. The actual Windows Paras digest is still missing,
  so the reported instance is not falsely labelled confirmed. No manifest edits.
- Pillow is required by OCR's `to_pil()` path and imported by the real OCR test;
  RapidOCR already depends on it transitively. Direct pin **Pillow 13.0.0** makes
  the required runtime/test dependency explicit. A complete requirements install
  with the same interpreter as pytest is needed on Windows; no skip/transient-only
  fix is claimed. No optional OCR dependency group exists.
- The published child script fails at implicit `json.load(open(...))` under
  emulated CP1252 with `UnicodeDecodeError` at byte 0x8f / offset1843. Explicit
  UTF-8 plus native/CP1252-default parameters preserves all hash assertions and
  seeds0/1/12345. The original Windows traceback is still absent; this is a
  demonstrated portability defect, not an invented traceback for that machine.

### Three R.K. failures remain evidence-blocked, not patched speculatively

- Source SHA-256 in Arena:
  `9a46095da97b4aea8dc9fe67df2a5923dcbb1968323f32ce2cb609d72b975198`,
  17,310,664 bytes / 496 pages. At pinned pypdf6.20.1, capital routing106–133,
  header page125 and labelled promoter/group rows page126 establish **72.22 +
  0.03 = 72.25**. Canonical value is72.25; evaluation score44.0. A controlled
  missing-value copy yields UNKNOWN and40.0, explaining the four-point effect
  without defaults or a scoring change. Existing raw page locator is section
  start106; actual table pages are separately documented, not silently relabelled.
- All three tests pass independently with cache disabled (12.05s,11.76s,12.39s),
  and together disabled **3 passed,1 warning,36.56s**. Seeds0/1/12345 agree on
  extracted value, routing and text. Production extraction/PDF blobs are identical
  at original baseline and optimization; fixture-fallback test is uncached.
  No direct evidence supports blaming the performance cache.
- Missing Windows facts: dependency/interpreter versions, actual PDF hash,
  page125/126 text/status/routing/canonical fields; original child traceback and
  actual Paras capture digest. Request exactly one read-only diagnostic JSON,
  from the SAME failing interpreter before environment/byte repairs:
  `python tests/diagnose_windows_portability.py --full-extraction --output <NEW-EXTERNAL-PATH.json>`.
  The script reports these facts, does not write a store/evaluation or checkout,
  refuses repository output, exclusively creates an external UTF-8 receipt and
  never overwrites the local harness. Preserve that edit; fresh-clone comparisons
  must state that they do not contain an unreviewed local patch.

### Available-platform validation and acceptance boundary

- Fresh installed Arena environment before corrections: reported seven **7 passed,
  1 warning,28.64s**. Focused corrected suite **45 passed,1 warning,35.27s**;
  byte/hash/repro subset **33 passed,1.83s**; cache/tier guards **6 passed,0.04s**.
- Real Git fresh-checkout tests exercise autocrlf=true/input with private
  index/work trees and a CRLF-positive unprotected control; original capture bytes
  and all declared digests preserved. No blanket normalization/expected-hash edits.
- Pass-9 **88 passed,1 warning,0.78s**; frontend **93 passed**, no failures/skips;
  all4 schemas, all6 frozen-core pins, golden, inactivev1.6, compileall, whitespace
  and pip dependency checks PASS. Correctness timings are not performance claims.
- Full-suite and remote publication receipts follow in the PR closeout. Windows
  acceptance remains **OPEN** pending native diagnostic/revalidation; neither
  Linux passes nor green Linux CI closes the three R.K. causes or proves that
  the user's corrected Windows environment passes. No merge/release/deployment,
  source qualification or scoring/golden/core activation change is implied.

### Revision 18 full validation and publication boundary

- Corrected full Arena regression **1,917 passed**, **0 failed/skipped/deselected**,
  **25 warnings**; **710.07s pytest / 711.133s wall (11m51.133s)**. The three
  extra cases are two real Git checkout modes and one CP1252 child-default
  parameter, not weaker/replacement assertions. Cache remains13,585 hits/1,596
  decoded pages. Fast1,040 + integration877 = full1,917 (collection checked).
- These are Linux correctness observations in the available sandbox, not a
  re-baseline of performance and not proof of Windows acceptance. Previous
  optimization timing/CI receipts remain historical facts, not new-check proof.
- The verified eight-path correction is committed with published **dfa34b2 as
  parent**, with the existing branch/index reconciled without reset/clean/file
  overwrites and normal fast-forward publication to the same branch/PR#10. Exact
  correction SHA, new full-CI API receipts and final remote OPEN/unmerged state
  belong to the PR's portability closeout comment, not an inferred earlier run.
- **Windows acceptance remains OPEN / evidence required:** actual Paras checkout
  digest, original native child exception, and the three R.K. extraction causes
  need the read-only diagnostic from the failing Windows interpreter. Preserve
  its local harness modification; no hard-coded value, score adjustment or
  speculative parser change is made. One JSON diagnostic is the outstanding
  request, not another approval/plan or an unsupported completion claim.


## Revision 19 — remaining R.K. Windows investigation publication

- User's reconciled Windows report has three remaining failures (two post-holding
  None vs72.25, UI7 score40 vs44). **Unresolved extraction cause; Windows acceptance
  OPEN.** No native diagnostic/criterion record supplied. This is a concrete repair
  blocker, not approval pending. Do not infer a parser/scorer fix from Linux green.
- Original physical125/126 table and column meanings verified; lower/upper post
  columns both showA72.22/B0.03. PublicC is excluded. Raw/canonical72.25 and existing
  section-start processing-summary provenance traced; page106 is not a literal
  table locator. No evidence is manufactured or changed.
- Full criterion/penalty comparison: supported base47/final44, controlled missing
  base43/final40; same−3 margin-spike deduction, all other criteria and penalties
  identical. Unknown points33→37, available67→63, lower31→27, upper77 unchanged.
  Missing-value scoring is correct in this controlled case; no independent native
  scoring defect is established. New real-filing regression preserves this contract.
- Diagnostic adds actual parser gates/rows/pages,11 source/config/harness byte
  fingerprints and an opt-in in-memory full evaluation. No store/workbook/evidence/
  harness writes. External-only exclusive output guard preserved and checked.
- Arena/Linux: first focus11passed/1warning/39.16s; related42passed/3warnings/128.11s;
  **full1,918passed,0failed/skipped/deselected,25warnings,947.53s** (pytest15m47s).
  No tests removed; +1 regression. Cache14,106hits/1,596decoded. Frontend93passed,
  nofail/skip; schemas4/frozen6/golden/inactivev1.6/pip/compile checks PASS.
- Scope exactly4 paths vs43a49497: diagnostic, R.K. reconciliation test, this
  tracker and docs/RK_FASHION_WINDOWS_INVESTIGATION.md. Combined PR25 paths.
  Protected production/config/schema/fixture/evidence/CI/harness unchanged.
  Source tree restored exactly43a49497 despite old Arena HEADdedb; parented scoped
  commit reconciles metadata without reset/clean/restore/force push. Windows-local
  uncommitted harness edit is unavailable here and never incidentally committed.
- Publication and independent new full-CI JUnit receipt are in PR#10's revision19
  closeout comment; PR stays OPEN/unmerged. **This publication is NOT an extraction
  repair.** Exact outstanding artifact is a new external JSON from the SAME failing
  interpreter: `python tests/diagnose_windows_portability.py --full-extraction
  --score-trace --output "$env:TEMP\rk-windows-score-before-repair-19.json"`.
  Preserve local restored captures/harness and collect before package/file repairs.


## Revision 20 — wrapped capital-total repair / native acceptance pending

- User-confirmed Windows diagnostic `rk-windows-score-before-repair-20261026-2.json`
  establishes unchanged source hash, readable125/126 and wrappedTotal(A). The old
  one-next-line/five-token helper exposes only99.61 instead of99.61/72.22/72.22.
  This is the confirmed parser failure, not a scoring defect. A reconstructed
  layout control executes the exact published59fe97e helper versus repaired helper
  and proves that difference; the full JSON itself was not attached in Arena.
- General numeric-only continuation assembly preserves order, bounds and category/
  row boundaries. Incomplete/malformed/overflow post columns remain UNKNOWN;
  printed promoter and promoter-group totals are combined under existing rules.
  No issuer/value hardcode, scoring change, fixture fallback or evidence rewrite.
-24 new cases:23 parser boundary/column/missing-value cases and1 real-filing
  whitespace-layout canary with fallback disabled. Original requested real PDF
  extraction/reconciliation and UI7 tests preserved and passing (score44 derives
  from the supported holding, never a forced four-point addition).
- Arena/Linux related **40passed,1warning,40.21s**; full **1,942passed,0failed/
  skipped/deselected,25warnings,892.74s pytest (14m52.74s)**. Cache14,627hits/
  1,596decoded pages. No tests removed. Frontend93passed/no failures/skips;
  pip check,4schemas,6frozen pins, golden, inactivev1.6, compileall/diff checks PASS.
  Timings are correctness receipts, not a new comparative performance benchmark.
- Scope5 paths vs59fe97e: sections.py, promoter parser tests, R.K. reconciliation
  tests, investigation report, this tracker. Combined PR27 paths. No scoring/
  config/schema/fixture/evidence/harness/CI/dependency changes. Five protected
  retained captures and harness byte-identical; user's Windows-local correction
  not accessible here, never overwritten/incorporated. No reset/restore/clean/
  normalization/force push. Published ancestry is retained on the existing branch.
- Exact new commit/remote tree/full-CI JUnit receipt and final OPEN/unmerged state
  are recorded in PR#10 revision20 closeout. **Windows acceptance remains OPEN**:
  user must rerun both extraction tests, UI7 test, relevant parser tests and full
  suite with the same Windows interpreter, preserving local harness/evidence.
  No unprovided native pass is inferred from Linux CI. Updated commands and
  provenance/column details are in docs/RK_FASHION_WINDOWS_INVESTIGATION.md.

## Revision 22 — the readers §20.4(a) asked for; and the defaults that were scoring

**Scope: extractor readers, TOC routing, the builder's non-evidence defaults, one CLI
formatter, four corrected test expectations and one new synthetic test module. No weight,
threshold, penalty, criterion definition, knockout, config, schema, fixture, golden record
or frozen-core module was changed.** Branch `arena/79aac867-ipo-screening-engine`.

### What was built
The readers the §20.4(a) table listed, plus three more the same pass found:

| Reader | Filing evidence | Result on the retained RHP |
|---|---|---|
| TOC routing (justified page numbers) | `OBJECTS OF THE OFFER ..... 12 4` | 10 → **14** sections routed (objects, industry overview, basis for offer price, capital structure were all being lost) |
| Objects schedule, row-oriented | p129 | `debt_repayment 3,209.00`, `other 541.00`, `gcp [●]` — previously unread, and the double-printed schedule had produced 8,185.95 by summing |
| Top-five concentration | p61 "Top **five** suppliers … 21.94 %" | `top5_supplier_pct 21.94` (a literal `top 5` regex could never match) |
| Industry forecast range | pp6/204 | `cagr 10.0` (lower bound of 10–12%), `FY2025-FY2030`, `CRISIL Report (…, dated September, 2026)` |
| Promoter pre-Offer | p111 | `72.80` (prose: "equivalent to 72.80% of the issued, subscribed and paid-up") |
| Pledge / lock-in | pp114/116 | `0.0` / `True`, both quoted verbatim, singular and plural, three lock-in spellings |
| Auditor continuity | p99 | `auditor_changed_3y False` — the letter names no firm, so it previously established nothing |
| Board composition in words | p337 | `board_independent_majority False` (3 of 7), only when the sentence is read |
| Twelve-column peer table, streaming rows | p150 | **nine** listed peers with P/E, P/B, ROE, dated 5 Oct 2026; issuer's own row excluded; fail-closed without a "Listed Peers" label |

### What was removed: defaults that scored
`builder.py` supplied `promoter_pledge_pct 0.0`, `promoter_lockin_in_place True`,
`large_holders_unlocked_early False`, `discounted_allotments_18m_before_drhp False` and
`board_independent_majority False` when nothing had been read — each clearing a point
without evidence (K2's pledge limb, C `lockin`, the discounted-allotment penalty, and D
`board_kmp` from the other direction). On the strict path these now stay absent and the
metric is UNKNOWN; the synthetic template path keeps its reference values.

**Consequence, recorded and not smoothed over:** two real filings' pinned scores moved
**down** by one point each (R.K. Fashion 44 → 43, the Aurora ingestion case 18 → 17;
availability moved with the point, 67% → 66%). Four test expectations were corrected with
the reason at the assertion — including one this pass had itself written last hour, which
is the cost of a default removal done honestly.

### The corrected Paras run
```
before (§20):  final  9.0  base 12.0  range  0-70  conf 35.79%  A6 B0 C6 D0 E0 F0
now         :  final 13.0  base 16.0  range  1-69  conf 41.05%  A6 B0 C3 D1 E6 F0
```
K3 CLEAR and K5 TRIGGERED unchanged; `PEER_SET_NO_VALID_ENTRIES` is gone (nine VALID
peers), `GCP_UNDISCLOSED` remains. Module C fell 6 → 3 (the unevidenced lock-in point) and
D rose 0 → 1 (the auditor point, now quoted from p99); E rose 0 → 6 (concentration and
the industry CAGR). **The number was not the target and did not guide the work.**

**Module B is still 0/20 and the reason is now explicit rather than hidden:** every B
criterion needs a post-issue EPS, which needs the post-issue share count. The filing prints
the fresh issue as money only (`₹5,000.00 million`; shares `[●]`) and its own P/E table on
p147 is `[●]` "to be computed after finalisation of the Price Band". Nine genuine peers
behind one undisclosed divisor is the honest state of this filing. §20.4(d)'s claim that
"the filing contains no peer table" was **wrong** and is corrected in the report.

### Also fixed
`ipo_screen run` crashed with `TypeError: unsupported format string passed to
NoneType.__format__` whenever an UNKNOWN criterion appeared in "Top risks" — after the score
printed, so the command exited 1 with no result path. It was found because this pass had to
read every run out of the store.

### Verification
- New `tests/test_reading_defects_20261026.py` — **28 passed**, all synthetic and instant.
- Affected suites (Paras evidence/gaps/issue-terms, acceptance matrix, v16 implementation,
  frozen-core line endings) — **169 passed**, golden hash unchanged.
- Full backend suite: **1,970 collected → 1,969 passed / 1 failed** on first run (the tier
  inventory rejecting the new module, which mentions the PDF router but hands it a fake
  reader); module listed as synthetic, both green on re-run.

### Status (unchanged where it must be)
- Frozen-core pin: **VERIFIED — READY FOR RAMKI RATIFICATION** (untouched).
- Paras pricing terms: **UNRESOLVED at runtime**; the Paras run above uses the aggregator
  override and is **non-authoritative evidence**, not an official determination.
- Required-term gate: **CLOSED**. Readiness: **NOT ESTABLISHED**.
- Still decision-gated, not reader-gated: `rpt`/K6 (metric definition), `moat`/`visibility`
  (ratings), `board_kmp` (exit rule), K1/K2 negatives, and any use of a post-issue share
  count the filing does not print.

- **Disposition: §20.4(a)'s READERS IMPLEMENTED AND VERIFIED; THE OBJECTS DOUBLE-COUNT AND
  THE TOC ROUTING DEFECT CORRECTED; FIVE FAVOURABLE DEFAULTS REMOVED FROM THE BUILDER (TWO
  REAL FILINGS' SCORES MOVE DOWN BY ONE POINT EACH, EXPECTATIONS CORRECTED WITH REASONS);
  PEER TABLE READ (NINE PEERS) BUT MODULE B STILL BLOCKED ON THE UNDISCLOSED POST-ISSUE
  SHARE COUNT; CLI REPORT CRASH FIXED; NO SCORING/THRESHOLD/CONFIG/SCHEMA/FROZEN-CORE
  CHANGE.**

## Revision 23 — the 9 → 13 reconciliation, K5 traced to its source, and what remains decision-gated

**Scope: documentation only. No file under `engine/`, `config/`, `tests/` or the schema was
changed in this pass; no weight, threshold, penalty, criterion, knockout, config value or
frozen-core module was touched; no test was run, because nothing executable changed.** Branch
`arena/79aac867-ipo-screening-engine`, PR **#12** (base `main`), head and remote verified at
publication. Recorded here as workstreams **B**, **C** and **D** of that PR's pass. The full
account is §23 of `docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`; this entry is
the status register, not a second narrative.

### The reconciliation, from beneath the numbers

The two Paras scores reported across Revision 22 are **9.0 and 13.0**, and the difference is
now fully accounted for rather than asserted. Artifacts:

| | Baseline | Current |
|---|---|---|
| Tree | commit `96379ab` (throwaway worktree) | branch head |
| Run | `…-20261026-062447Z-final-dc3d136e` | `…-20261026-091500Z-final-c123e138` |
| Final / base / penalty | 9.0 / 12.0 / −3.0 | 13.0 / 16.0 / −3.0 |
| Range | 0.0 – 70.0 | 1.0 – 69.0 |
| Completeness | 35.7895% (Low) | 41.0526% (Low) |
| Available / unknown / evaluable | 34 / 61 / 95 | 39 / 56 / 95 |
| Modules | A 6 · B 0 · C 6 · D 0 · E 0 · F 0 | A 6 · B 0 · C 3 · D 1 · E 6 · F 0 |

The input delta between the two runs is exhaustive at **13 leaves**: ten fields that are now
evidenced (top-five supplier 21.94 p61, industry CAGR 10.0 pp204/FY2025-FY2030/INDIA/CRISIL,
three 2006–2008 pre-IPO placements, promoter pre-Offer 72.80 p111, auditor unchanged p99, the
object schedule 3,209.00 + 541.00 + `gcp [●]` p129, nine peers p150), **two builder defaults
removed** (`large_holders_unlocked_early`, `discounted_allotments_18m_before_drhp`: `False` →
`None`), and one source retrieval timestamp. No financial line, issue term, date, price band,
share count, quota or config value differs.

Five criteria moved and nothing else did: C `use_of_proceeds` 2/4 → UNKNOWN (−2, the
`[●]` GCP makes the blind-heavy test undecidable), C `lockin` 1/1 → UNKNOWN (−1, the point was
the removed default), D `auditor` → 1/2 `eom_only`, E `industry_growth` → 3/5, E
`concentration` → 3/3. Both bounds moved in opposite directions for honest reasons: the upper
bound fell 70 → 69 because five open points became closed or earned while B and F stayed
unknowable; the lower bound rose only 0 → 1 because the unresolved-penalty envelope grew
10 → 12 when `discounted_allotments` stopped being cleared by a default.

### Reproducibility — what the hash does and does not prove

Re-running the CLI against the stored input snapshot reproduced `c123e138…` bit-for-bit in a
fresh store. Two limits recorded: the hash covers the run timestamp (the same inputs at the
baseline clock give identical scores under hash `413682ae…`, so a clock change cannot
manufacture the old 9.0 — only the `96379ab` tree does), and `pipeline.evaluate()` is not
hash-equivalent to the CLI (`2bf73f02…`), so scores may be quoted from either path but **only
the CLI may be used for a hash claim**.

### K5 "contingent liabilities >50% of net worth" — TRIGGERED, traced, and retained

3,905.01 ÷ 3,949.41 × 100 = **98.8758%** > 50. Numerator is the p91 "Total" (27.50 liquidated
damages + 75.00 bank guarantee + 3,694.21 corporate guarantees + 108.30 claims = 3,905.01);
denominator is FY2026 net worth 3,949.41. The issuer corroborates it in its own risk factors
(p36: contingent liabilities "constituted 89.55% of our net worth" for a later quarter, and a
coverage row printing "3,905.01 **98.88%** … as at March 31, 2026"). **No correction was made,
and none is due.** The one nuance worth carrying: guarantees are 93.54% of the numerator, and
excluding them would leave 210.80 (5.34%) and no trigger — but the issuer itself includes the
guarantees in the contingent-liability total it discloses, so excluding them would be the
engine clearing a knockout by overruling the issuer's accounting. That is not done.

The remaining knockouts read cleanly and were re-verified leaf by leaf: **K3 CLEAR** (OFS
65.517% not > 80; profit not declining, FY2026 PAT 438.34 vs FY2025 −579.83); K1, K2, K4, K6
UNVERIFIED for the reasons already registered (basis-of-preparation ≠ going concern; nil
SEBI/ED statements are promoter-scoped; cumulative PAT non-positive so CFO/PAT is meaningless
and is *not* zeroed; seller list and post-issue holding undisclosed; RPT-growth metric
undefined even though RPT are 0.47% of revenue on pp. 92–95).

### Module B — nine real peers, still 0/20

The p150 table is fully read (nine `VALID` peers, priced 5 October 2026; median P/E 62.10,
P/B 8.37, ROE 13.41%) and it buys nothing, because every B criterion needs the *issuer's*
P/E, which needs the post-issue share count, which is printed as `[●]` — the filing's own P/E
table on p147 is `[●]` "to be computed after finalisation of the Price Band". `fresh ÷ price
band` remains the forbidden arithmetic (§20.4(c)). B, `dilution` and `promoter_ofs_pct` are
blocked on a **disclosure**, and B's 20 points are the single largest share of the 56 unknown
points.

### One new open defect, found in the frozen core — recorded, not fixed

Rebuilding the baseline exposed a second instance of the Revision 22 defect class inside
`derived.py`: with **no** use-of-proceeds schedule read (`[]`), C `use_of_proceeds` scored
`mixed_ok` **2/4**. An empty list is not evidence of mixed use, and the midpoint is a
favourable default. It is **not** fixed in this pass — `derived.py` is frozen, the change would
move other issuers' scores, and A22/A32 do not authorise it. **Open item: governance decision
required**; it should not be described as resolved.

### Governance boundary — unchanged

A22 (evidence-or-UNKNOWN) and A21 (disclosed post-issue holding; `SRC-DERIVED` is a
provenance-marked derivation, not a substituted disclosed value) are followed, not amended.
A23's two "RAMKI DECISION REQUIRED" coverage standards remain open. **A32's header is
untouched and reads verbatim: "IMPLEMENTED 2026-10-26; FULL BACKEND SUITE EXECUTED; READY FOR
RAMKI RATIFICATION (NOT RATIFIED)".** Nothing here ratifies it. Decision-gated and not
reader-gated, each with its exact dependency: `rpt`/K6 (metric definition), `moat`/`visibility`
(ratings), `board_kmp` (exit rule), K1 `going_concern_uncertainty` and K2
`sebi_ed_action_active` (explicit-negative rule), post-issue share count (approved derivation
or disclosure).

### Publication and status

- PR **#12** — base `main`, **OPEN**, **MERGEABLE**, not merged, closure not claimed.
- Paras evaluation remains **non-authoritative evidence** (aggregator issue terms, retained
  RHP under `evidence/non-authoritative/`); it is not an official determination about the
  issuer.
- Readiness: **NOT ESTABLISHED**. Required-term gate: **CLOSED**. Frozen-core pin: **VERIFIED —
  READY FOR RAMKI RATIFICATION** (untouched).
- Remaining blockers are one disclosure (post-issue share count), four governance decisions
  (RPT metric, moat/visibility ratings, KMP-exit rule, explicit-negative rule), two coverage
  standards (A23), one ratification (A32), and the empty-schedule default above.

- **Disposition: THE 9 → 13 DELTA IS FULLY RECONCILED FROM UNDERLYING RECORDS (13-LEAF INPUT
  DIFF, FIVE CRITERIA, BOTH BOUNDS); THE RUN, ITS PERSISTED EVALUATION AND ITS HASH ARE ONE RUN
  AND REPRODUCE BIT-FOR-BIT; K5 IS TRIGGERED ON THE ISSUER'S OWN DISCLOSED TOTAL AND IS
  RETAINED; MODULE B REMAINS BLOCKED ON AN UNDISCLOSED POST-ISSUE SHARE COUNT; ONE FROZEN-CORE
  EMPTY-SCHEDULE DEFAULT FOUND AND LEFT OPEN FOR GOVERNANCE; NO CODE, CONFIG, SCORING,
  THRESHOLD, PENALTY OR FROZEN-CORE CHANGE; PR #12 OPEN AND UNMERGED.**

## Revision 24 — two shared derivation defects fixed in the common path; the frozen-core pin re-set with a reason

**Scope: `derived.py` (derivation layer), one corrected docstring in `sections.py`, the
frozen-core pin in `v16_implementation.py`, one rewritten expectation in
`test_rk_fashion_reconciliation.py`, one new focused module. No config, schema, weight,
threshold, penalty, knockout, golden-record or criterion-definition change.** Branch
`arena/79aac867-ipo-screening-engine`, PR **#12** (base `main`), published and verified below.
Full account: §24 of `docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`.

### Shared defects, root causes, affected paths

| # | Defect | Root cause | Affected |
|---|---|---|---|
| 1 | An **empty** objects-of-the-offer schedule scored `mixed_ok` (2/4) and `gcp_amount` reported `0.0` | every three-valued test "not triggered" on an empty list, so the function fell through to the lenient bucket. A *derivation* default of the same class Revision 22 removed from the builder — invisible while schedules were unreadable, and it paid the bonus exactly where the engine knew least | C `use_of_proceeds`; `gcp_amount`; `dilution_ok` via the bucket |
| 2 | `post_issue_shares` / `post_issue_eps` were never assembled | they were only ever read as raw inputs; nothing derived them, so a filing disclosing pre-issue count + fresh-issue count + PAT but not the post-issue count produced UNKNOWN valuation, dilution and promoter holding with no reason given | B `pe_vs_peers`, `second_multiple`, `peg`, `sector_ipo_relative`; C `dilution`; D `promoter_post_holding`; `market_cap`, P/B, EV/EBITDA, PS |

### Implementation (shared components only — no issuer branch anywhere)

* `_post_issue_shares`: disclosed wins; otherwise **pre-issue + fresh-issue** (an OFS transfers
  existing shares and never changes the count); a disclosed count *below* the pre-issue count is
  refused as contradictory. The **`fresh issue ÷ price band` shortcut stays prohibited** and the
  refusal message names it.
* `_post_issue_eps`: disclosed wins; otherwise **latest full-year PAT ÷ post-issue shares** —
  the prospectus convention, and the conservative direction (unweighted, so the P/E is higher).
* `promoter_post_pct`: disclosed wins; otherwise **(pre-issue % × pre-issue shares − promoter
  shares sold in the OFS) ÷ post-issue shares**, with the group's holding taken from the
  disclosed percentage (only some promoter holders sell) and structural refusals kept
  (seller cannot offer more than it held; group cannot sell more than it owned).
* `use_of_proceeds_bucket`: empty schedule + fresh issue > 0 → **UNKNOWN**; empty schedule +
  fresh issue == 0 → **NOT_APPLICABLE** (unchanged, so the genuine not-applicable case stays
  distinct); a read schedule with no GCP line still means a **nil GCP**; a schedule allocating
  more than the fresh issue it distributes → **UNKNOWN** (the signature of a double-read).
* `gcp_amount`: empty schedule → **UNKNOWN**, not `0.0`.
* Provenance: every derived value carries its `formula`, the exact `inputs` consumed (extra
  inputs appear only on the derived path) and a `reason` beginning "derived:" that states the
  arithmetic. Disclosed and derived values are distinguishable in `derived_metrics`, in the
  stored record and in replay.

### Frozen-core pin — re-set, with the reason recorded

`derived.py` is one of the six pinned files. The pin is a change-detector, not an approval
authority; the owner's standing authorization covers this in-scope correction, so the pin was
re-set to `a9e4e5da884f8228f79be9d7ff3f3c3def11dc97327e7d778103cf5f9e05d359` with the rationale
in the pin's own comment (as A15 did for `evaluation.py`, A30 for `price_band_notice.py`).
`verify_golden_result()` is unchanged and still reproduces
`e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.

### Cross-issuer impact

| Artifact | Before | After | Why |
|---|---|---|---|
| Vishal Nirmiti (golden) | 35.0, base 38.0, hash `e84f8bc0…` | **identical, hash identical** | all three fields disclosed; the golden hash passing is the proof that no scoring output moved |
| Vishal Nirmiti, three fields stripped | UNKNOWN dilution / promoter holding / EPS | 35.0 **unchanged**, values derived | derived post-issue count 26,390,909 = 19,800,000 + 6,590,909 exactly; derived promoter post 49.400193% vs disclosed 49.4%; derived EPS 9.4635 vs disclosed 9.46 |
| R.K. Fashion Accessories | 43.0 | **43.0 unchanged** | its disclosed 72.25% is reproduced by the derivation as 72.2588%; the one test that removed the disclosure was rewritten to remove the derivation's *inputs* instead, where UNKNOWN → base 46→42, final 43→39 is still asserted |
| Jio Platforms | — | unchanged | all values disclosed; pre + fresh = post exactly (8,939,030,830 + 270,000,000) |
| Paras Healthcare | 13.0 | **13.0, unchanged by construction** | its schedule is non-empty with a `[●]` GCP (pre-existing blind-test path) and its post-issue count is `[●]` with no fresh share count, so the derivation returns UNKNOWN with a more specific message. **No new Paras run was made** — the previous run's input snapshot was not retained and the retained issue-terms package forbids its own use as evaluation input |

### Findings recorded, not "fixed"

* **§20.4(b) / §23.7 are wrong about RPT.** The metric definitions exist and are approved
  (2026-10-17) and implemented; Module D `rpt` and K6 are **reader-gated, not decision-gated**.
  Paras's note is headed "Related parties disclosures" / "Summary of related party transactions
  and balances" (pp. 416–420) and matches no anchor, so nothing is extracted. The stale docstring
  asserting the definitions did not exist was corrected in `sections.py`.
* **Jio fixture internal inconsistency:** `post_issue_eps` 3.26 against PAT/post-shares = 32.63
  (factor ten). Left exactly as captured — it is retained evidence, and editing captured evidence
  silently would be worse than the inconsistency. Recorded with the arithmetic.
* **K1/K2 handling already meets the standard** (positive-only going concern; SEBI/ED denial vs
  action separation; A24/A25/A29 party scope). No change was made or needed.

### Focused verification (full suite deliberately not run)

```
tests/test_global_value_semantics_20261026.py ....................... 18 passed (new)
tests/test_core_semantics.py test_overlays_knockouts.py
  test_auditor_tenure_defaults.py test_litigation_regulatory_defaults.py
  test_jio_score_bridge.py test_frozen_core_line_endings.py
  test_v16_implementation.py test_vishal_golden.py
  test_acceptance_matrix.py test_global_value_semantics_20261026.py
  test_fresh_issue_manual_entry.py .......................... 318 passed
tests/test_rk_fashion_reconciliation.py .............................. 7 passed
tests/test_reading_defects_20261026.py test_paras_evidence_regression.py  45 passed
tests/test_extraction.py test_extraction_phase5b.py
  test_jio_fresh_regressions.py test_suite_tiers.py
  test_paras_extraction_gaps_20261024.py ............................. 52 passed
```
New module covers empty / partial / complete / malformed schedules, the pure-OFS
NOT_APPLICABLE case, disclosed-wins, derivation of shares / EPS / promoter holding,
contradictory counts, the band-refusal message, and the exact reconstruction of the Vishal
disclosures.

### Status and next actions

- Readiness: **NOT ESTABLISHED**. Required-term gate: **CLOSED**. Frozen-core pin: **VERIFIED**,
  re-set to the reviewed hash with the golden result unchanged.
- Next actions, in order: (1) RPT reader anchors for "Related parties disclosures" notes —
  unblocks D `rpt` and K6; (2) a dated `kmp_exits_2y` reader over the changes-in-directorate
  table — unblocks D `board_kmp`; (3) a coverage marker in the canonical input so a disclosed
  nil can be told from an unread section (contract change); (4) Paras Module B stays blocked on
  the filing's `[●]` post-issue share count — a genuine missing disclosure.
- A32 remains **"IMPLEMENTED 2026-10-26; FULL BACKEND SUITE EXECUTED; READY FOR RAMKI
  RATIFICATION (NOT RATIFIED)"**; nothing in this revision ratifies it.

- **Disposition: THE EMPTY-SCHEDULE DERIVATION DEFAULT AND THE UNASSEMBLED POST-ISSUE CAPITAL
  STRUCTURE ARE FIXED IN THE SHARED DERIVATION LAYER; DERIVED VALUES REPRODUCE THE DISCLOSED
  ONES EXACTLY ON THREE REAL ARTIFACTS; VISHAL GOLDEN HASH AND SCORE UNCHANGED, RK FASHION
  43.0 UNCHANGED, PARAS 13.0 UNCHANGED BY CONSTRUCTION; FROZEN-CORE PIN RE-SET WITH A RECORDED
  REASON; RPT/K6 RECLASSIFIED FROM DECISION-GATED TO READER-GATED; NO WEIGHT, THRESHOLD,
  PENALTY, KNOCKOUT OR CONFIG CHANGE; PR #12 OPEN AND UNMERGED.**

---

## Revision 25 — the directorate reader, the coverage contract, and Jio's EPS attribution
— 2026-10-26

**Scope: three shared gaps closed in one pass — a reader for the changes-in-directorate
table, a per-field coverage contract that separates a verified nil from an unread section,
and provenance/precedence for the post-issue EPS. No scoring weight, threshold, penalty,
knockout, bucket boundary or criterion definition was changed, and no issuer name appears in
any engine path.** Branch `arena/79aac867-ipo-screening-engine`, PR **#12** (base `main`),
left **OPEN**. Full account: §25-§29 of
`docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`.

### What was wrong, and where

| # | Gap | Root cause | Affected |
|---|---|---|---|
| 1 | `governance.kmp_exits_2y` had **no reader** | the field was only ever copied from the input; the table's column order differs across four real layouts, and nothing parsed it. Historical records carried an unsupported `0` | D `board_kmp` (UNKNOWN for every extraction-based run; `0` unevidenced in retained records) |
| 2 | `capital_structure.pre_ipo_placements: []` was **ambiguous** | an empty list is produced by a filing with no discounted allotments *and* by one whose share-history schedule the reader never opened; the bucket awarded the favourable 2/2 in both cases | C `pre_ipo_placement` |
| 3 | The post-issue EPS was **unattributed** | a derived figure entered the canonical exactly like a disclosed one; there was no precedence rule for a filing that prints a post-issue figure; the crore factor lived in two components with nothing tying them together. `3.26` is the **lakh-assumption form** of the same derivation (`300,527 × 1e5 ÷ 9,209,030,830 = 3.2634`) | B `pe_vs_peers`, `second_multiple`, `peg`, `sector_ipo_relative`; `market_cap` |

### Implementation (shared components only)

* **`extraction/directorate.py` (new).** Rows are anchored on the **date token** — every real
  layout prints it between the person and the reason — so column count and column order are
  not assumed. The name is the honorific-anchored capitalised run before the date; the
  designation is the title-vocabulary suffix before it (or, where the filing has no
  designation column, the title named in the reason); the reason is everything after the date
  up to the start of the next name, which re-joins cells wrapped across lines and pages
  (Vishal p. 306, p. 319). Captions must start a line, so a cross-reference sentence cannot
  open a table; notes and numbering footnotes close it and their dates are not rows. Undated
  exit rows are **reported**, never guessed at.
* **`governance.board_changes`** (schema, new): `{name, role, event, date, reason}` with
  `event` ∈ `resignation | cessation | retirement | term_expiry | appointment | other`.
  Classification follows the source: a bare "Cessation … for pre-occupation and personal
  reasons" is **not** promoted to a resignation.
* **`kmp_exits_2y` derived**, not copied: exits inside the 24 calendar months before the
  **offer open date** (close date, then listing date as fallbacks; never `date.today()`, so a
  stored record re-derives identically), inclusive at both ends. Read table with no exit →
  a **verified 0**; unread/partial/unanchorable → **null**, never 0. A curated value is
  preserved when the reader established nothing and superseded when it did.
* **`coverage`** (schema, new): field path → `DISCLOSED | VERIFIED_NIL | PARTIAL | UNREAD`,
  with the migration rule in the schema description (*a record without the map is a legacy
  v1.5 input and keeps v1.5 behaviour; once present, an unmentioned field is UNREAD*). Only
  `DISCLOSED` and `VERIFIED_NIL` produce a placement bucket; `PARTIAL`/`UNREAD` are UNKNOWN.
  The producer quotes the evidence: an allotment row → `DISCLOSED`; the standard Capital
  Structure sentence *"…has not issued any Equity Shares at a price lower than the Offer
  Price during the last one year"* (quoted with its "Except for the bonus issuance" clause,
  Vishal p. 105) → `VERIFIED_NIL`; schedule vocabulary with no readable row → `PARTIAL`.
* **EPS provenance and precedence.** A reader captures a figure only when the filing labels
  it *post-issue*; historical weighted-average rows are deliberately refused (Jio's
  "Earnings per share (Basic) 33.63" is a different quantity), and `[●]` is never a value.
  `issue.post_issue_eps_basis` ∈ {`disclosed`, `derived`}; a derived value carries an
  `_evidence` entry (`extraction_method: DERIVED`, locator "Derived by the engine (not
  printed in the filing)") naming PAT, the filing's unit, the factor, the share count and the
  period, so it can be recomputed from the record. `semantic_validation._CRORE_TO_RUPEES` is
  the single named factor for the crore↔rupee step. A stored value that contradicts the
  arithmetic by >10% is reported as **unresolved**, with the stored value, the implied value,
  the basis and whether it carries evidence — plus the evidence that would settle it. The
  captured value is **not** overwritten.

### Cross-issuer validation (real filings, live extraction)

| Issuer | Directorate rows | `kmp_exits_2y` | Placement coverage |
|---|---|---|---|
| Vishal Nirmiti | 18 (9 board + 9 KMP) | **0**, `VERIFIED_NIL` (nearest cessation 2024-04-16, outside the window) | `VERIFIED_NIL` (p. 105) |
| R.K. Fashion Accessories | 1 | **0**, `VERIFIED_NIL` | `PARTIAL` (schedule located, no row readable) |
| Paras Healthcare | 14 (7 board + 7 KMP) | **4**, `DISCLOSED` → `high_churn` | `DISCLOSED` (3 allotments, 2006-2008) |
| Jio Platforms | 17 | **6**, `DISCLOSED` → `high_churn` | `PARTIAL` |

Both adverse moves are evidence-driven (the engine had been giving a neutral treatment to
filings that disclose churn); no threshold was touched.

### Score effects

| Artifact | Before | After | Why |
|---|---|---|---|
| Vishal Nirmiti (golden) | 35.0 / hash `e84f8bc0…` | **identical** | fixture carries no coverage map → legacy behaviour; live extraction is a verified nil and keeps its 2 points |
| Aurora `complete_sample_rhp` | 17.0 | **13.0** | synthetic sample has no share history and no directorate table → placements −2, board_kmp −2, both UNKNOWN |
| R.K. Fashion Accessories | 43.0 | **41.0** | schedule located but no row readable → placements UNKNOWN (−2); its directorate table *was* read |
| class_b / class_c / class_e synthetic fixtures | 36 / 36 / 38 | **34 / 34 / 36** | no share history at all → placements UNKNOWN (−2), reasons recorded inline |

Expectations were updated only where the engine stopped awarding points for an unexamined
section; no expectation was relaxed to protect a score.

### Frozen core and verification

`derived.py` re-pinned to
`7783dfeb2cae2d68083fef5ebd6dde8567ad110b53253a4c8fe5516a70ce1f2c` with the reason in the
pin's comment (the placement bucket is the only edit). `verify_frozen_core()` → all six
**True**; `verify_golden_result()` → **True**, `e84f8bc0…` unchanged.

Focused suites only, all green: **57** (three new modules), **55**, **185**, **76**, **36**
— exact commands and results in §28 of the investigation. The full backend, regression and
frontend suites were deliberately not run.

### Status and next actions

- Readiness: **NOT ESTABLISHED**. Required-term gate: **CLOSED**. PR **#12 OPEN**, not
  merged, not claimed closed.
- The three next-actions named in Revision 25's predecessor are now done (RPT anchors were
  done in Revision 23; the directorate reader and the coverage contract are done here).
- Remaining, in order: (1) read R.K. Fashion's and Jio's share-history schedule layouts so
  `pre_ipo_placements` stops being `PARTIAL` on real filings; (2) Paras Note 34 (pp. 416-420)
  stays unread — the RPT summary pp. 92-93 remains the evidence in use; (3) accept the RHP
  date as a window anchor for filings whose offer open date is `[●]` at extraction time.
- A32 remains **"IMPLEMENTED 2026-10-26; FULL BACKEND SUITE EXECUTED; READY FOR RAMKI
  RATIFICATION (NOT RATIFIED)"**; nothing in this revision ratifies it.

- **Disposition: THE CHANGES-IN-DIRECTORATE TABLE IS READ FROM FOUR REAL LAYOUTS AND
  `kmp_exits_2y` IS DERIVED AGAINST A DATED WINDOW; AN EMPTY `pre_ipo_placements` NO LONGER
  SCORES UNLESS THE FILING ESTABLISHES THE NIL (FOUR-STATE COVERAGE CONTRACT, BACKWARD
  COMPATIBLE WITH EVERY EXISTING FIXTURE AND RECORD); A DERIVED POST-ISSUE EPS IS LABELLED,
  RECOMPUTABLE AND SUPERSEDED BY A DISCLOSED ONE, AND THE HISTORICAL 3.26 IS RECORDED AS THE
  LAKH-ASSUMPTION FORM OF 32.63 AND FLAGGED UNRESOLVED WITHOUT BEING OVERWRITTEN; VISHAL
  GOLDEN HASH UNCHANGED, FROZEN-CORE PIN RE-SET WITH A REASON; NO CONFIG, WEIGHT, THRESHOLD,
  PENALTY OR KNOCKOUT CHANGE; PR #12 OPEN AND UNMERGED.**

## Revision 26 — the related-party disclosure that was there all along (period-matrix reader)

— 2026-10-26

**Scope: one shared reader gap closed — the related-party transactions disclosure that is
laid out as a period matrix rather than as transaction-category headings. No scoring weight,
threshold, penalty, knockout, bucket boundary or criterion definition was changed, no
configuration was touched, no frozen-core file was edited, and no issuer name appears in any
engine path.** Branch `arena/79aac867-ipo-screening-engine`, PR **#12** (base `main`), left
**OPEN**. Full account: §30 of `docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`.

### What was wrong, and where

`SectionExtractor.extract_related_party_transactions` returned **zero extractions** on the
Paras Healthcare RHP. Re-verified against the PDF, the root cause is the **column model**,
not the search: the reader *did* anchor on the summary page (the preamble reads
"…transactions **with related parties**…"), then required at least two column headers of the
form "year ended 31 March YYYY" and found none — the table's columns are
*three months ended 30 June 2026 / 30 June 2025* and *Fiscal 2026 / 2025 / 2024* — so it
returned nothing. The disclosure was therefore indistinguishable from an unread section:
`rpt_pct_revenue` null, Module D `rpt` UNKNOWN, K6 UNVERIFIED.

### The layout actually disclosed (read, not assumed from the title)

`SUMMARY OF RELATED PARTY TRANSACTIONS`, PDF pp. 92-93 (printed 87-88), `(₹ in million)`:
**ten numeric columns = five periods × (amount, "% revenue from operations")**, one row per
(counterparty, nature of transaction), 17 transaction rows, header repeated on the
continuation page, `-` for undisclosed cells. PDF p. 94 is the separate
*outstanding balances* disclosure (`% of total assets`), and Note 34 (pp. 416-420) repeats
the transactions in a three-label-column layout whose numerals are glued in the text layer.

### What was implemented

A layout-driven reader, tried **only when the category-header reader yields nothing** (so
every issuer it already read is unaffected): positioned text fragments → visual lines →
trailing numeric cells (with kerning-split numbers re-joined) → **column count taken from the
anchor page only** → **period columns from the table header** (`three months ended …`,
`stub period ended …`, `Fiscal 2026`, `year ended 31 March …`, day- or month-first; annual →
`FY2026`, interim → `3M-2026-06-30`) → **label columns by position, roles by header word**
(counterparty / nature / reporting entity) → verbatim page-line quotes, disclosed unit and
disclosed revenue share per value. Undisclosed cells emit nothing; the table stops where the
**balances** disclosure begins; **aggregate control totals** ("Sum of all related party
transactions", "Revenue from Operations", "% of revenue") are never emitted as transactions;
a **nil statement** is a verified nil.

**Coverage** is now recorded for this section on
`coverage.governance.rpt_pct_revenue`: `DISCLOSED` (read, values supplied — both readers),
`VERIFIED_NIL` (the filing states there were none), `PARTIAL` (located but not fully
readable — rows of another width, unmappable period header, aggregate-only summary), and
absent = `UNREAD` per the §25 contract.

**One shared derivation change** was required for a matrix disclosure to reach the metric at
all: `_derive_rpt_metrics` now **skips** a period column that is not a financial year (an
interim `3M-…` column carries no annual share) instead of failing the whole derivation
closed. An unconvertible unit or a non-numeric amount still fails closed.

### Cross-issuer validation (real filings, live extraction)

| Issuer | RPT values | `coverage.governance.rpt_pct_revenue` | Effect |
|---|---|---|---|
| Paras Healthcare | **70** (17 rows × disclosed cells) | `DISCLOSED` (pp. 92-93) | section now read; metric unchanged (null — see below) |
| Vishal Nirmiti | **136** (unchanged) | `DISCLOSED` (p. 387) | `rpt_pct_revenue` `11.8418`, growth `-0.3703` — unchanged |
| Jio Platforms | **23** (unchanged) | `DISCLOSED` (p. 376) | unchanged |
| R.K. Fashion Accessories | 0 | `PARTIAL` | its summary prints aggregate totals only; reported as unread per-transaction, not as data |

### Score effects

**None.** No artifact's score moved. Paras keeps D `rpt` UNKNOWN and K6 UNVERIFIED, because
its disclosure contains **no revenue-type category** under the approved numerator definition
(sales/services, job-work received): its rows are employee benefits, post-employment
benefits, share-based payment, retainers, directors' sitting fees, rental income,
repairs/maintenance/power & fuel and an advance to a KMP. Treating "no revenue-type row
disclosed" as a measured 0.0% would award the full `<5%` band (3 points) and clear K6 on a
document that calls itself a *summary*; per the standing rule that points are never awarded to
a missing value without a documented defensible rule, the share stays **unknown while the
coverage record proves the section was read**. The 70 values are retained as evidence, so the
alternative (if Ramki decides rental income or the note's "revenue from sale of healthcare
services" belongs in the numerator) is a one-line definition change, not a reader change.

### Verification (focused suites only; exact commands in §30.8 of the investigation)

`pytest tests/test_rpt_matrix_reader_20261026.py -q` → **14 passed** (new module);
`… test_rpt_extraction.py … test_coverage_nil_vs_unread_20261026.py …
test_directorate_events_20261026.py … test_post_issue_eps_provenance_20261026.py …
test_suite_tiers.py -q` → **83 passed**; `test_acceptance_matrix.py test_vishal_golden.py
test_vishal_historical_reconciliation.py test_rk_fashion_reconciliation.py -q` → **85
passed**; `test_paras_evidence_regression.py test_paras_extraction_gaps_20261024.py
test_paras_official_issue_page_terms.py test_coverage_nil_vs_unread_20261026.py -q` → **91
passed**. `tests/test_rpt_extraction.py` was adjusted only so its helpers skip the new
coverage record; no expectation on the legacy reader changed. The full backend, regression
and frontend suites were deliberately not run.

### Status and next actions

- Readiness: **NOT ESTABLISHED**. Required-term gate: **CLOSED**. PR **#12 OPEN**, not
  merged, not claimed closed.
- Remaining, in order: (1) **R.K. Fashion Note 31** (printed p. 305) — its per-counterparty
  transactions are read by neither reader, only its aggregate summary is located
  (`PARTIAL`); (2) Paras Note 34 (pp. 416-420) needs glyph-level position recovery — the
  summary pp. 92-93 is now read in full and is the evidence in use; (3) R.K. Fashion's and
  Jio's share-history schedules are still `PARTIAL`; (4) the 24-month window still needs an
  RHP-date anchor when the offer open date is `[●]`; (5) **decision for Ramki**: whether
  rental income / related-party "revenue from sale of healthcare services" enters the
  Module D numerator.
- A32 remains **"IMPLEMENTED 2026-10-26; FULL BACKEND SUITE EXECUTED; READY FOR RAMKI
  RATIFICATION (NOT RATIFIED)"**; nothing in this revision ratifies it.

- **Disposition: A FULLY DISCLOSED RELATED-PARTY TRANSACTIONS NOTE IS NO LONGER REPORTED AS
  AN UNREAD ONE — THE PERIOD-MATRIX LAYOUT IS READ (COUNTERPARTY, NATURE, DISCLOSED PERIOD,
  AMOUNT, DISCLOSED REVENUE SHARE, VERBATIM QUOTE), THE BALANCES TABLE AND CONTROL TOTALS ARE
  NEVER READ AS TRANSACTIONS, A `-` CELL IS NEVER ZERO, AND COVERAGE RECORDS
  `DISCLOSED | VERIFIED_NIL | PARTIAL` (ABSENT = `UNREAD`) FOR THE SECTION; THE MODULE D / K6
  SHARE REMAINS UNKNOWN WHERE THE DISCLOSURE CARRIES NO REVENUE-TYPE CATEGORY, AS A RECORDED
  DECISION RATHER THAN A FABRICATED ZERO; NO CONFIG, WEIGHT, THRESHOLD, PENALTY, KNOCKOUT OR
  FROZEN-CORE FILE CHANGED; PR #12 OPEN AND UNMERGED.**

## Revision 27 — the two disclosures that only needed their geometry (glyph cells, scanned notes, allotment schedule)

— 2026-10-26

**Scope: three shared readers finished and one metric question re-examined on evidence. No
scoring weight, threshold, band, penalty, knockout or criterion definition was changed, no
configuration was touched, no frozen-core file was edited, and no issuer name appears in any
engine path.** Branch `arena/79aac867-ipo-screening-engine`, PR **#12** (base `main`), left
**OPEN**. Full account: §33 of
`docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`.

### What was wrong, and where

1. **R.K. Fashion's Note 31 has no text layer.** The restated financial statements are scans
   (PDF p. 308 carries one image and the text `304`), so the per-counterparty disclosure could
   only be reported `PARTIAL` — 0 rows for a filing that discloses them in full.
2. **A row's counterparty and its first amount arrive as one text fragment.** On Paras Note 34
   §III-A (p. 419) the layer gives `204:Paras Healthcare (Ranchi) Private Limited 40.54
   311:34.53 372:132.35 …`: splitting on fragments yields four amounts where the table has five
   columns. The characters inside the fragment are still positioned, so the cells can be rebuilt
   from glyph boxes. (This replaces §30.9's "glued numerals" hypothesis, which was re-checked and
   does not occur on pp. 416-420 in either text mode.)
3. **A missed dotted rule merges two columns.** A band whose header names two quantities is now
   refused instead of bound to whichever name sorts first.
4. **The share-history schedule** (`_share_history`, published here) reads the allotment table by
   geometry when the legacy one-sentence regex and the filing's positive no-discount statement
   establish nothing.

### What was implemented (shared, issuer-neutral)

- `extraction/glyph_table.py` — character-box cell reconstruction (`get_charbox` → lines → runs
  split only on gaps wider than the line's own spacing, never between the digits of one figure
  or between adjacent digits of a number).
- `SectionExtractor.extract_page_glyph_lines` + `_rpt_page_rows` — the period-matrix reader falls
  back to glyph cells only when the fragment reading cannot separate a row, so every layout it
  reads today is unchanged.
- `extraction/rpt_image_note.py` — image-only related-party note: bounded offline OCR, **vertical
  rules detected in the rendered page** → column bands → header cell per band → amount bound by
  its own centre → every row checked against the block's arithmetic (opening + additions −
  reductions = closing). Balances are never transactions, a block with no control total is
  counted unread, a band naming two quantities is refused, an amount needs two decimals and
  confidence ≥ 0.94, and a row needs its own period and party.
- `SectionExtractor._extract_related_party_image_note` — runs only when the text layer already
  located the disclosure and read no row; a failed OCR attempt claims nothing.
- `CanonicalInputBuilder` — the 24-month window keeps the offer-open-date anchor and is now
  reported `PARTIAL` when it is anchored on any other offer date (a later anchor can only narrow
  the window).

### Coverage and score effects

| Issuer | RPT rows | Coverage | Placements | Window |
|---|---|---|---|---|
| Paras | 70 (unchanged) | `DISCLOSED` | unchanged | unchanged |
| Jio | 23 (unchanged) | `DISCLOSED` | **17 priced, `DISCLOSED`** (p. 100) | unchanged |
| Vishal | 136 (unchanged) | `DISCLOSED` | `VERIFIED_NIL` preserved (schedule fails closed) | unchanged |
| R.K. Fashion | **0 → 14** (`PARTIAL`) | `PARTIAL` | **9 priced, `DISCLOSED`** (p. 110) | unchanged |

R.K. Fashion moves **41.0 → 43.0** (Module C 7 → 9, base 44 → 46, completeness 64% → 66%,
lower bound 26 → 28) because `pre_ipo_placement_bucket` is now decided on the filing's own
priced allotments — none falls inside the 365 days before the offer open date of 2026-10-05 (the
last is 2025-05-31). Nothing else moves; `derived.py` untouched (pin `7783dfeb…`), Vishal golden
hash `e84f8bc0…` unchanged.

### Module D numerator — re-examined, still not changed

The summary the engine reads (pp. 92-93) carries no revenue-type related-party row, so the
numerator is absent and `rpt_pct_revenue` stays null. Note 34 §III-A additionally discloses
"Revenue from sale of healthcare services (excluding applicable taxes)" — 28.69 / 14.45 / 6.48
₹ million for FY2026 / FY2025 / FY2024 — but under a heading that says the transactions are
**eliminated in consolidation**, while the denominator is *consolidated* revenue (16,059.52 /
12,940.63 / 11,290.39 ₹ million). Counting them would put gross intra-group revenue over
post-elimination revenue (0.1788% → D `rpt` 3/3, K6 still CLEAR) and would also require assuming
a direction for "Outsourced medical services". **Disposition: UNKNOWN stands, evidence preserved;
recommendation to Ramki recorded in §33.8** (keep the consolidated basis, or define a separate
standalone-basis metric with its own denominator).

### Verification — focused suites during the work, the comprehensive run once at the end

`test_glyph_geometry_and_ocr_note_20261026.py` **15**; `test_rpt_matrix_reader_20261026.py`
+ `test_vishal_historical_reconciliation.py` + `test_paras_official_issue_page_terms.py` **43**;
`test_rpt_extraction.py` + `test_auditor_evidence_section.py` **20**; `test_acceptance_matrix.py`
+ `test_vishal_golden.py` + new module **89**; `test_cli_phase5i.py` +
`test_coverage_nil_vs_unread_20261026.py` + `test_directorate_events_20261026.py` +
`test_post_issue_eps_provenance_20261026.py` **80**; `test_rk_fashion_reconciliation.py` +
`test_paras_evidence_regression.py` + `test_paras_extraction_gaps_20261024.py` **48**;
`test_ui7_ingestion.py` **20**; `test_suite_tiers.py` **1** (new real-file module registered in
`tests/tier_inventory.py`). The first push failed CI on one expectation that had encoded the old,
reader-limited score (`tests/test_ui7_ingestion.py`, `assert 43.0 == 41.0`); it is updated with
the same reasoning and the module now passes 20/20. The full backend, regression and frontend
suites were deliberately not run.

CI (`regression`, workflow "A9 contract boundary regression") was **PASS** on `fad5a53`
(21m32s, 2,074 tests) after the `test_ui7_ingestion.py` expectation was corrected; the run on
`17f2ae0` failed on that single stale expectation.

### Status and next actions

- Readiness: **NOT ESTABLISHED**. Required-term gate: **CLOSED**. PR **#12 OPEN**, not merged,
  not claimed closed.
- Done here: §30.9 items 1 (Note 34 glyph recovery), 2 (R.K. Fashion Note 31) and 3 (share
  history for R.K. and Jio); item 4 (window anchor) hardened; item 5 re-examined and left as an
  explicit decision for Ramki.
- Remaining, in order: (1) **Ramki's decision** on the numerator basis (§33.8); (2) the OCR note
  reader is `PARTIAL` on R.K. Fashion — 55 cells unbound, mostly values whose period printed on a
  neighbouring line; a two-line row-band model would close most of it; (3) Paras summary rows are
  read with their verbatim nature text and stay `unclassified` — the category vocabulary does not
  cover "short term employee benefits"-style natures, and extending it must not add an eligible
  revenue category by accident.
- A32 remains **"IMPLEMENTED 2026-10-26; FULL BACKEND SUITE EXECUTED; READY FOR RAMKI
  RATIFICATION (NOT RATIFIED)"**; nothing in this revision ratifies it.

- **Disposition: AN IMAGE-ONLY RELATED-PARTY NOTE IS NOW READ (RULES + ARITHMETIC, BALANCES
  NEVER TRANSACTIONS, UNBOUND CELLS COUNTED UNREAD, `PARTIAL` RATHER THAN A GUESS), A TEXT LAYER
  THAT MERGES A ROW'S CELLS NO LONGER BINDS A VALUE TO THE WRONG COLUMN (GLYPH RECONSTRUCTION,
  FALLBACK ONLY), AND THE PAID-UP SHARE-CAPITAL SCHEDULE IS READ FOR R.K. FASHION AND JIO
  (9 AND 17 PRICED ALLOTMENTS, `DISCLOSED`) WITH VISHAL'S `VERIFIED_NIL` PRESERVED; R.K. FASHION
  41.0 → 43.0 SOLELY BECAUSE THAT SCHEDULE IS NOW READ; THE MODULE D NUMERATOR STAYS UNKNOWN WITH
  THE EVIDENCE AND A RECOMMENDATION RECORDED; NO CONFIG, WEIGHT, THRESHOLD, PENALTY, KNOCKOUT OR
  FROZEN-CORE FILE CHANGED; PR #12 OPEN AND UNMERGED.**

## Revision 28 — printed rows rebuilt from their rules, and one vocabulary for transaction natures

— 2026-10-26

**Scope: the scanned related-party note reader now reconstructs the printed table instead of OCR
line groups, and both related-party readers share one nature vocabulary. No scoring weight,
threshold, band, penalty, knockout or criterion definition was changed, no configuration was
touched, no issuer name appears in any engine path, `derived.py` (pin `7783dfeb…`) is untouched
and the Vishal golden hash `e84f8bc0…` is unchanged.** Branch
`arena/79aac867-ipo-screening-engine`, PR **#12** (base `main`), left **OPEN**. Full account: §34 of
`docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`.

### What was wrong, and where

1. **A row was an OCR line group, not a printed row.** A party name printed once against four
   financial years covered only the line the recogniser put its text on, so the other rows lost
   their counterparty.
2. **A value was placed by its own line.** These scans print a figure's baseline ~7 px below its
   own row's rule, so a value could bind to the following year. Placement is now by box overlap
   with the printed row.
3. **Continuation was decided by page adjacency.** The reader walked off the note into the
   profit-and-loss page (309) and the cash-flow page (310); page 310 is Note 9, property, plant and
   equipment, with no table block. Continuation is now "the page produces mapped blocks".
4. **A rule was "a dark row".** A densely set word in a narrow label column ("Investment", the third
   line of a merged nature cell) reached the same darkness, was taken for a cell boundary, and
   truncated the description to "Advances against". A rule is now required to be one continuous
   stroke (`_rule_rows`, `RULE_CONTINUITY`).
5. **Nothing recorded why a cell was unread.**
6. **Each reader kept its own nature phrase list**, so one printed nature could be a sale in the
   period-matrix reader and `unclassified` in the note reader.
7. **The caller swallowed every reader exception**, so a broken reader and a document with no such
   note produced the same output. A lost module constant in this revision raised `NameError` on
   every block and the production path reported the aggregate-summary `PARTIAL` as if nothing were
   wrong.

### What was implemented (shared, issuer-neutral)

- `extraction/rpt_image_note.py`: `horizontal_rules` / `_rule_rows` / `crosses` / `row_bands` /
  `_spans` / `_overlap` / `_band_table` / `_band_text` / `_band_confidence`; `parse_page` rewritten
  to emit only rows that state their own period, have a counterparty and close against their own
  balances (printed dashes read as disclosed nils, negative balances accepted as balances and never
  emitted as movements); `UNCERTAIN_CONFIDENCE` (0.80) admits a low-confidence cell **only** when
  the row's control total proves it; every unread cell is counted with a reason and the coverage
  note prints the breakdown; `read_related_party_note` returns `{found, transactions, state, note,
  pages, reasons}`.
- `extraction/rpt_categories.py` (**new**): the single nature vocabulary —
  `REVENUE_CATEGORIES`, `CATEGORY_CLASS`, ordered `NATURE_CATEGORIES`, `classify_nature`,
  `is_revenue_category`, `normalise`, `describe`. Classification requires the wording to establish
  the economic meaning **and the direction**; direction is never inferred from a category name.
- `extraction/sections.py`: the period-matrix reader's classification fallback calls
  `classify_nature` instead of defaulting to `unclassified`; `_extract_related_party_image_note`
  logs a failed OCR read (`exc_info`) before returning no extraction (output semantics unchanged).
- `extraction/builder.py`: `_RPT_SALES_SERVICES_CATEGORIES` **is** `REVENUE_CATEGORIES` and
  `_rpt_is_sales_services` delegates to `is_revenue_category`, so the numerator and the readers
  cannot drift apart. Contents unchanged.

Tests: `tests/test_rpt_nature_classification_and_row_bands_20261026.py` (**new**, 64 tests: positive
and negative classification, the eligibility/class equivalence in both directions, geometry on a
drawn table — merged label cells, drifted baselines, a dense word that is not a rule — and the R.K.
Fashion OCR regression); registered in `tests/tier_inventory.py`.
`tests/test_rpt_matrix_reader_20261026.py::test_paras_amounts_periods_and_disclosed_share` now
asserts the classification Paras actually prints (`employee_benefits`) plus
`is_revenue_category(...) is False`, instead of `unclassified`.

### Result on R.K. Fashion Note 31 (same OCR, same fixture)

| | Revision 27 | Revision 28 |
|---|---|---|
| Transaction values | 19 | **23** |
| Unread cells | 55 | **47** |
| Pages read | [308, 309, 310] | **[308, 309]** |
| Coverage | `PARTIAL` | `PARTIAL` |

Recovered and proved by the note's own arithmetic: Mohammed Usman `loan_taken` FY2024 **216.00**
and `loan_repaid` **213.31** (47.21 + 216.00 − 213.31 = 49.90); M.K.Jewellers `purchase_of_goods`
3M-2026-06-30 **9.13** and `payment_made` **16.02** (36.88 + 9.13 − 16.02 = 29.99, printed 29.98).
All 19 earlier values are still reported. Unread by reason: block without opening and closing
control **30**, row does not close against its balances **10**, row without period **7**. An
increased row count is not offered as proof: every emitted row closes against the balances the
filing prints beside it, and the four categories produced (`loan_taken`, `loan_repaid`,
`purchase_of_goods`, `payment_made`) are all non-revenue, so `rpt_pct_revenue` stays null and the
score stays **43.0**.

### Classification safeguards (proved by tests, not asserted)

- Eligible numerator is unchanged: `sale_of_goods`, `sale_of_services`, `revenue_from_operations`,
  `job_work_charges_received` (+ the pre-existing `sale_of_*` prefix rule, excluding `sale_of_ppe`).
- Employee benefits (short-term, post-employment, gratuity, leave encashment, provident fund),
  share-based payment, remuneration, salary, sitting fees, retainers and professional fees,
  purchases, repairs/power and fuel, hire/transport/job-work charges paid, reimbursements, interest,
  rents, loans, advances, deemed capital contribution, merger consideration and share of profit
  paid classify as `expense`/`income_other`/`asset`/`liability`/`settlement`/`capital`/`disposal`
  and are never eligible.
- "Rent and facility fees", "Loan to and from group companies" and "Reimbursements" state no
  direction and stay `unclassified`.
- Every `CATEGORY_CLASS` entry must satisfy
  `is_revenue_category(c) == (CATEGORY_CLASS[c] == "revenue") == (c in REVENUE_CATEGORIES)`,
  so neither the class map nor the eligible set can be widened alone. **Nothing in this revision
  can add eligible related-party revenue or clear K6 for any issuer.**

### Module D numerator — still UNKNOWN, disposition unchanged

Paras Note 34 §III-A discloses "Revenue from sale of healthcare services (excluding applicable
taxes)" 28.69 / 14.45 / 6.48 ₹ million under a heading stating the transactions are **eliminated in
consolidation**, against *consolidated* revenue of 16,059.52 / 12,940.63 / 11,290.39 ₹ million.
Counting them would divide gross intra-group revenue by post-elimination revenue (0.1788% /
0.1116% / 0.0574%, D `rpt` 3/3, K6 CLEAR) and would also require assuming a direction for
"Outsourced medical services (excluding applicable taxes)". The fields stay null; a standalone-basis
metric is a definition change with its own numerator, denominator and field. Recommendation and the
exact question for Ramki: §34.6.

### Verification — focused suites only

`test_rpt_nature_classification_and_row_bands_20261026.py` **64**;
`test_glyph_geometry_and_ocr_note_20261026.py` + `test_rpt_matrix_reader_20261026.py` +
`test_rpt_extraction.py` **40** (after the one expectation update above);
`test_rk_fashion_reconciliation.py` **7** (43.0 / base 46.0 / completeness 66%);
`test_paras_evidence_regression.py` + `test_jio_evidence_remediation.py` **19** (Jio
`rpt_pct_revenue` 4.3094 unchanged); `test_ui7_ingestion.py` + `test_suite_tiers.py` **21**.
Production path re-read on the R.K. filing: 23 transactions, `PARTIAL`,
`{loan_taken 6, loan_repaid 10, purchase_of_goods 3, payment_made 4}`. Cross-issuer counts
unchanged: Paras 70 `DISCLOSED`, Jio 23 `DISCLOSED`, Vishal 136 `DISCLOSED` (Vishal
`rpt_pct_revenue` 11.8418 unchanged).

**Final comprehensive validation — executed once, after every in-scope item was dispositioned:**
`PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q --durations=30` → **2,138 passed, 0
failed**, 25 warnings, **1191.93 s (19 m 51 s)**, exit 0; `cd frontend && node --test
test/*.test.js` → **93 passed, 0 failed**. CI (`regression`, "A9 contract boundary regression") on
`f8eb3bb` (run `40373327494`) → **PASS**, 27 m 10 s, 2,138 tests, 0 failures.

### Status and next actions

- Readiness: **NOT ESTABLISHED**. Required-term gate: **CLOSED**. PR **#12 OPEN**, not merged.
- Remaining, in order: (1) **Ramki's decision** on the Module D numerator basis (§34.6); (2) 30
  cells in blocks that print no control total stay unread by design; (3) 10 rows whose OCR digits do
  not close and 7 rows with no period — a higher-resolution block render would raise confidence, not
  relax the rule; (4) party names keep the filing's own spelling per block
  (`MK.Jewellers` / `M.K.Jewellers`); (5) the comprehensive suites are done (2,138 + 93, above) and need no rerun unless code changes.

- **Disposition: THE SCANNED RELATED-PARTY NOTE IS NOW READ FROM ITS PRINTED RULES (PRINTED ROWS,
  MERGED LABEL CELLS, VALUES BY BOX OVERLAP, EVERY ROW CLOSED AGAINST ITS OWN BALANCES, UNREAD
  CELLS COUNTED WITH REASONS), R.K. FASHION NOTE 31 GOES 19 → 23 VALUES AND 55 → 47 UNREAD CELLS
  WITH ALL 19 EARLIER VALUES KEPT AND THE PAGES LIMITED TO [308, 309]; ONE SHARED NATURE VOCABULARY
  NOW SERVES BOTH RELATED-PARTY READERS AND THE BUILDER, WITH RENT/PURCHASE/EMPLOYEE-BENEFIT/LOAN
  NATURES CLASSIFIED AS NON-REVENUE AND DIRECTION-UNSTATED WORDING LEFT UNCLASSIFIED, SO THE
  MODULE D NUMERATOR AND K6 ARE UNCHANGED FOR EVERY ISSUER; A SWALLOWED READER EXCEPTION IS NOW
  LOGGED RATHER THAN SILENT; THE MODULE D NUMERATOR STAYS UNKNOWN WITH THE QUESTION RECORDED FOR
  RAMKI; NO CONFIG, WEIGHT, THRESHOLD, PENALTY, KNOCKOUT OR FROZEN-CORE FILE CHANGED; PR #12 OPEN
  AND UNMERGED.**

## Revision 29 — Module D numerator: the consolidated basis is retained (owner decision)

— 2026-10-27

**Scope: the owner has decided the question left open since Revision 27/28. The approved definition
is retained; the numerator never mixes bases and never fills missing evidence with zero. No weight,
threshold, band, penalty, knockout or criterion changed, no configuration touched, no schema field
added, `derived.py` (pin `7783dfeb…`) untouched.** Branch `arena/79aac867-ipo-screening-engine`, PR
**#12** (base `main`), left **OPEN**. Full account: §35 of
`docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md`.

### The decision

> Retain the existing consolidated-basis definition for Module D's related-party revenue metric.
> Do not include transactions eliminated in consolidation in the numerator unless the existing
> definition and accounting evidence explicitly support their inclusion. Keep the metric UNKNOWN
> when qualifying consolidated-basis revenue cannot be established. Do not substitute zero for
> missing evidence. Any standalone-basis exposure metric must be separately defined and use a
> matching standalone revenue denominator.

Consequently the Paras Note 34 §III-A revenue (28.69 / 14.45 / 6.48 ₹ million, disclosed under a
heading stating those transactions are **eliminated in consolidation**) is **not** counted against
consolidated revenue. The 0.1788 / 0.1116 / 0.0574 % alternative, which would give D `rpt` 3/3 and
clear K6, is recorded as rejected-by-definition, not as a coverage gap. A standalone-basis measure
remains unadopted: it would be a separate metric with its own numerator, its own standalone
denominator and its own field.

### What was implemented (shared, issuer-neutral)

| # | Rule now enforced in the shared path | Where |
|---|---|---|
| 1 | A revenue-type related-party row the disclosure itself marks as eliminated in consolidation is excluded from the numerator (per row, so a supported row beside it still counts) | `rpt_categories.is_consolidation_eliminated`, applied to the row's verbatim text in `CanonicalInputBuilder._derive_rpt_metrics` |
| 2 | A year the note states no qualifying amount for has **no** share — the former `0.0` numerator is gone | `_derive_rpt_metrics` |
| 3 | The metric is UNKNOWN when the latest audited FY's qualifying revenue is not established; an older year can no longer become "latest" | `latest = max(periods)` |
| 4 | The change is UNKNOWN when the comparable prior FY's share is not established; no zero prior | `_derive_rpt_metrics` |
| 5 | Absent evidence stays absent — null in, UNKNOWN out, never zero | builder + unchanged `derived.py` |

### Effect on the issuers on record — none

Vishal Nirmiti **11.8418 % / −0.3708 pp**; Jio Platforms **4.3094 % / −0.1141 pp**; Paras **null /
null**; R.K. Fashion **null / null**, score **43.0** (base 46.0, completeness 66 %).

### Verification — focused suites

`tests/test_module_d_consolidated_basis_20261027.py` **7 passed** (new; registered in
`tests/tier_inventory.py`); `tests/test_rpt_extraction.py` **11 passed** — the former
`test_derivation_unit_conversion_and_zero_prior` became `…_and_no_zero_prior`, asserting the change
is null where the prior year states no amount, because that zero substitution is exactly what the
decision forbids; `test_jio_evidence_remediation.py` + `test_rk_fashion_reconciliation.py` +
`test_paras_evidence_regression.py` **26 passed**; `test_ui7_ingestion.py` + `test_suite_tiers.py` +
the new module **28 passed**. The full backend suite is confirmed once through CI on the pushed
commit (2,138 tests), not re-run locally for a metric-derivation-only change.

### Status and next actions

- Readiness: **NOT ESTABLISHED**. Required-term gate: **CLOSED**. PR **#12 OPEN**, not merged.
- The Module D numerator question is **closed by owner decision**; nothing else moves.
- Remaining: the reading limitations listed in §34.8 (30 cells in control-total-free blocks, 10
  rows whose OCR digits do not close, 7 rows without a period, per-block party spellings), all of
  which stay unread rather than guessed.

- **Disposition: THE MODULE D RELATED-PARTY REVENUE METRIC KEEPS ITS CONSOLIDATED BASIS BY OWNER
  DECISION (2026-10-27); FIGURES THE DISCLOSURE MARKS AS ELIMINATED IN CONSOLIDATION ARE EXCLUDED
  FROM THE NUMERATOR PER ROW, A YEAR WITHOUT A STATED QUALIFYING AMOUNT HAS NO SHARE, THE LATEST
  AUDITED FY MUST BE ESTABLISHED BEFORE ANY SHARE IS REPORTED, NOTHING IS FILLED WITH ZERO, AND NO
  STANDALONE-BASIS MEASURE IS ADOPTED WITHOUT ITS OWN SEPARATE DEFINITION AND MATCHING STANDALONE
  DENOMINATOR; VISHAL 11.8418 %/−0.3708 pp, JIO 4.3094 %/−0.1141 pp, PARAS AND R.K. FASHION NULL,
  R.K. SCORE 43.0 — ALL UNCHANGED; NO CONFIG, WEIGHT, THRESHOLD, PENALTY, KNOCKOUT, SCHEMA OR
  FROZEN-CORE FILE CHANGED; PR #12 OPEN AND UNMERGED.**

---

## Revision 30 — `kmp_exits_2y` scope and the Regulation 17(1)(c) carve-out: two decisions recorded, no code change
— 2026-10-27

**Scope: two semantic questions about scoring *inputs*, answered with a measurement and a
decision record each. No engine file, schema, config, weight, threshold, penalty, knockout,
band or criterion definition was changed.** Branch `arena/342ccacc-ipo-screening-engine`,
PR **#13** (base `main`), left **OPEN** and **not merged**.

### Why these two, and why not by an extractor

`docs/investigation/JIO-34-GLOBAL-ARCHITECTURE-DISPOSITION-2026-10-27.md` §6.3 and §8
presented both as decisions required. This pass measured them rather than arguing them, and
wrote each up as a decision record with a recommendation, the alternatives and an explicit
**no implementation authority**. Neither is ratified.

### 1. `kmp_exits_2y` — `handoff/decisions/A33-kmp-exit-counting-scope.md`

The rule implemented, merged in PR #12 and validated in tracker Revision 25 counts **every
dated exit the reader established from the changes-in-directorate table**; `count_exits`
does not consult `role`. The metric formula says "KMP exit", so the scope was open.

Two KMP-only readings were computed on the real tables:

| Reading | Jio (17 rows) | Paras KMP p. 357 (7 rows) | Consequence |
|---|---|---|---|
| **B1** recognised KMP `role` only | **1** | **0** | both < ≥2 → `board_kmp` `high_churn` → `other` (**+1 each**) |
| **B2** skip a *known* non-KMP designation, count an unrecognised one fail-closed | **2** | **4** | no bucket changes |

**Recommendation: retain the current rule.** B1 discards disclosed evidence — Paras's KMP
table prints no designation column, so `role` is null on every row and all four resignations
would become unclassifiable. B2 buys nothing. The real defect is **role recovery**, which
is an extractor improvement and a separate decision. The disposition report's §6.3(i)
parenthetical is corrected: the two Jio exits B2 retains are the CEO resignation and the one
exit whose designation the reader did not recover; there is no Company Secretary resignation
in Jio's window.

### 2. Regulation 17(1)(c) — `handoff/decisions/A34-early-unlock-carve-out-semantics.md`

Both quotes were **re-extracted from the evidence PDFs this pass and are verbatim with
correct page attribution**: Jio printed p. 105 (PDF index 104), Paras printed p. 117 (PDF
index 116). The carve-out removes the general six-months-from-Allotment lock-in for
VCF/AIF/FVCI shares and imposes a *minimum* six months from **purchase**. It does not state
when those holders purchased, so it does not establish that any holder is released *earlier*
than the general rule.

**Recommendation: a category carve-out alone must not set
`capital_structure.large_holders_unlocked_early`.** Without evidence of an actual early
release the field stays `null` and C `lockin` stays UNKNOWN. The reader added by PR #13
(`cac095d`) and its 17-test matrix are **preserved unchanged** pending the decision; A32,
which this question belongs to, remains `NOT RATIFIED` and asserts no authority over any
scoring artefact. The lock-in generality report's §2 and the Paras triage report's §3 are
corrected to state that the carve-out is a different anchor, not an established early
release.

### Files

| File | Change |
|---|---|
| `handoff/decisions/A33-kmp-exit-counting-scope.md` | **new** — PROPOSED, not implemented |
| `handoff/decisions/A34-early-unlock-carve-out-semantics.md` | **new** — PROPOSED, not implemented |
| `tests/test_kmp_exit_counting_scope_20261027.py` | **new**, 14 tests, synthetic tier: pins the current rule issuer-neutrally (KMP exit, non-KMP board exit, mixed table, duplicate rows, unrecognised designation, window boundaries, UNKNOWN-not-zero anchor, builder derivation, criterion bucket) |
| `docs/investigation/JIO-34-GLOBAL-ARCHITECTURE-DISPOSITION-2026-10-27.md` | §6.3(i) and §8(1) corrected with the B1/B2 measurement; §6.3(ii) and §8(2) corrected with the verified quotes and the A34 boundary |
| `docs/investigation/LOCKIN-INSTITUTIONAL-CARVEOUT-GENERALITY-2026-10-27.md` | §2 and §6: the carve-out is recorded as a different anchor, not an established early release; pointer to A34 |
| `docs/investigation/PARAS-UNKNOWN-TRIAGE-2026-10-27.md` | §3: same correction and pointer to A34 |

### Verification

`tests/test_kmp_exit_counting_scope_20261027.py` **14 passed**; the new module is not in
`INTEGRATION_MODULES`, so it runs in the fast synthetic tier. The two quotes were verified
by independent re-extraction with `pypdf`, not by trusting the reader's own match. Paras was
reproduced end-to-end from the committed RHP (13.0 / 16.0 / −3.0 / **44.21%** / `AVOID` / K5
TRIGGERED / `lockin` SCORED 0 `weak` / `board_kmp` SCORED 0 `high_churn` / `kmp_exits_2y` 4
`DISCLOSED`). Full backend suite: **2183 passed, 0 failed, 25 warnings in 1462.48s** — the
+14 over the previous 2169 is exactly the new module.

### Status and next actions

- Readiness: **NOT ESTABLISHED**. Required-term gate: **CLOSED**. PR **#13 OPEN**, not merged.
- **A33 and A34 are PROPOSED and UNRESOLVED.** Both need RAMKI. Recommended answers: retain
  the current `kmp_exits_2y` rule; do not set `large_holders_unlocked_early` from a category
  carve-out alone.
- No score, verdict, knockout, completeness or bound changes on any filing as a result of
  this revision — it records decisions, it does not implement them.

---

## Revision 31 — A33/A34 approved, implemented and focused-verified — 2026-10-27

**Scope: two approved decisions about the meaning of scoring inputs, one narrow
reader correction, two fresh issuer reproductions, reconstructed decision
records and documentation. No weight, threshold, penalty, band, knockout,
config, schema, `derived.py`, builder, frozen-core pin or historical evaluation
record was changed.** PR **#13** remains **OPEN** and **not merged**.

### 1. Decisions (approved, not proposed)

| ID | Approved answer | Effect |
| --- | --- | --- |
| **A33** | **Alternative A, provisionally** — preserve the current `kmp_exits_2y` counting rule (count every dated exit from the changes-in-directorate table, no `role` filter) | **No counting or scoring change.** Jio 6, Paras 4; both `board_kmp` SCORED 0 `high_churn`. The name/formula mismatch and role recovery remain separately authorized open items. |
| **A34** | **Alternative B** — a category-specific institutional lock-in carve-out alone does **not** establish an early unlock; only an evidenced actual early release may set `capital_structure.large_holders_unlocked_early` | **Implemented** in `engine/ipo_screening/extraction/sections.py::extract_capital_structure`: the PR #13 carve-out regex is removed; a fail-closed sentence-level rule requires holder group + release act + lock-in context + explicit early/before-expiry timing. Ambiguous, pledge, transferability, normal-expiry and hypothetical language stay UNKNOWN. No favourable `False` is inferred. |

Both decision records are updated from `PROPOSED / UNRESOLVED` to approved with
an explicit implementation boundary (A33 §0, A34 §0, §9, §10). A34 §0.3 records
the A32 reconciliation.

### 2. A32 reconciliation — genuine governance-recording requirement

A32 remains **`READY FOR RAMKI RATIFICATION (NOT RATIFIED)`**. It removed this
field's favourable `False` default and left open (§6.2) whether an engine may
establish it from a filing at all. A34 Alternative B is the criterion owner's
approved answer to that policy question; it **does not ratify A32**. The genuine
remaining recording requirements are: (a) keep A32's unratified status visible
and its separate ratification open; (b) keep A34 recorded as **approved**, not
as an unapproved proposal; (c) leave alternative C's additive structured
carve-out field to a separate schema/canonical-input decision; (d) note that
"no early unlock of large holders" is now applied as an evidenced test without
claiming the v1.5 specification wording was amended (CONVENTION rule 5). No
authority question blocks the approved A34 implementation.

### 3. Issuer reproduction (existing baselines vs after A34)

| | Jio pre-A34 (committed probe) | **Jio after A34 (fresh)** | Paras pre-A34 (PR #13) | **Paras after A34 (fresh)** |
| --- | --- | --- | --- | --- |
| final / base / penalty | 37.0 / 37.0 / 0.0 | **37.0 / 37.0 / 0.0** | 13.0 / 16.0 / −3.0 | **13.0 / 16.0 / −3.0** |
| verdict | `AVOID` | **`AVOID`** | `AVOID` | **`AVOID`** |
| completeness | 63.0% | **62.0%** | 44.21% | **43.16%** |
| bounds | 25.0 – 74.0 | **25.0 – 75.0** | 1.0 – 66.0 | **1.0 – 67.0** |
| knockouts | K2 TRIGGERED | **unchanged** | K5 TRIGGERED | **unchanged** |
| `kmp_exits_2y` / `board_kmp` | 6 / SCORED 0 `high_churn` | **unchanged** | 4 / SCORED 0 `high_churn` | **unchanged** |
| `large_holders_unlocked_early` | `true` | **`null`** | `true` | **`null`** |
| C `lockin` | SCORED 0 `weak` | **UNKNOWN** | SCORED 0 `weak` | **UNKNOWN** |

The only A34-attributable differences are the flag, the `lockin` state,
completeness, available/unknown points and the upper bound. Final score,
verdict, knockouts and module scores are unchanged on both issuers; A33 causes
no delta. Quotes and pages: Jio carve-out p. 105, promoter lock-in p. 104,
directorate table p. 300, K2 p. 468; Paras carve-out p. 117, promoter lock-in
p. 115, directorate evidence p. 345 (KMP table printed p. 357). Full record:
`docs/investigation/A33-A34-ISSUER-REPRODUCTION-2026-10-27.md` and
`docs/investigation/a33-a34-issuer-reproduction-20261027/summary.json`.

### 4. A34 semantic boundary and corpus limitation

Verified by a 28-test suite: the carve-out alone does not set the flag on three
real filings (Paras p. 117, Jio p. 105, Moneyview p. 485) or four synthetic
wording variants; an evidenced early release sets it and is consumed by the
governing criterion (`weak`, SCORED 0); ambiguous, insufficient, hypothetical or
negated evidence, unrelated pledge/transferability language, and normal release
on expiry stay UNKNOWN; genuine positive cases remain detectable. A full-text
scan of the five examined real filings (**2,826 pages**) found **zero** evidenced
early releases. That is a corpus limitation, **not** proof that early releases
never occur; labelled synthetic positives are retained.

### 5. Files

| File | Change |
| --- | --- |
| `engine/ipo_screening/extraction/sections.py` | **only engine change** — A34 evidenced-release reader replaces the PR #13 carve-out reader |
| `tests/test_lockin_institutional_carveout.py` | rewritten as the **28-test** A34 semantic-boundary suite (real filings + labelled synthetic cases) |
| `tests/test_reading_defects_20261026.py` | carve-out no longer sets the flag; one evidenced-release positive added; builder quote corrected |
| `tests/test_paras_evidence_regression.py` | **+2** A34 tests: absent evidence row on the real filing; full end-to-end after-A34 result |
| `tests/test_a34_issuer_reproduction_20261027.py` | **new (3 tests)** — committed Jio input before/after; A33 counting pin |
| `handoff/decisions/A33-…md`, `A34-…md` | approved status, §0 decisions, implementation boundary, A32 reconciliation |
| `docs/investigation/BROAD-REMEDIATION-CONSOLIDATED-DISPOSITION-2026-10-27.md` | status update superseding the "unresolved" dispositions |
| `docs/investigation/JIO-34-GLOBAL-ARCHITECTURE-DISPOSITION-2026-10-27.md` | status update + §11 (decisions, Jio before/after, A32, verification) |
| `docs/investigation/PARAS-UNKNOWN-TRIAGE-2026-10-27.md` | §0 status update; §3 rewritten with three measured states |
| `docs/investigation/LOCKIN-INSTITUTIONAL-CARVEOUT-GENERALITY-2026-10-27.md` | revision 2: approved rule, cross-issuer before/after, 28-test matrix, corpus limitation |
| `docs/investigation/A33-A34-ISSUER-REPRODUCTION-2026-10-27.md` + `…/summary.json` | **new** — reproduction record with quotes, pages and before/after values |
| `tests/test_jio_current_engine_result_20261027.py` | divergence pin 20 → 21: `enrichment_contract.py` now differs from the 2026-10-23 fingerprint; assertion strictness unchanged, reason recorded |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` | this revision |

### 6. Verification

* **65 passed** — `test_lockin_institutional_carveout.py` (28),
  `test_reading_defects_20261026.py` (33),
  `test_a34_issuer_reproduction_20261027.py` (3), `test_suite_tiers.py` (1).
* **132 passed** — eight affected regression modules:
  `test_paras_evidence_regression.py` (20, including the new Paras
  reproduction), `test_rk_fashion_reconciliation.py` (7),
  `test_ui7_ingestion.py` (20), `test_jio_current_engine_result_20261027.py`
  (3, including fresh Jio ingestion), `test_extraction.py` (12),
  `test_core_semantics.py` (31), `test_kmp_exit_counting_scope_20261027.py`
  (14), `test_paras_official_issue_page_terms.py` (25).
* **Tier gate:** green. The rewritten real-PDF module remains declared in
  `tests/tier_inventory.py::INTEGRATION_MODULES`; the new issuer module is
  synthetic-tier and needs no declaration.
* **CI-equivalent integrity:** `verify_frozen_core()`, `verify_golden_result()`,
  `verify_v1_6_implementation()`, all `schema/*.json`, and
  `python -m compileall -q engine` — all PASS.
* **Full backend suite: NOT RUN, by instruction.** Earlier full-suite figures
  (2166 / 2169 / 2183) belong to earlier trees and are not claimed for this
  revision. The paused session's reported "28 A34 tests" and "90 tests across
  four additional modules" left no surviving output after the workspace reset;
  the suites were reconstructed and their affected scope re-run as above.

### 7. Status and remaining limitations

- Readiness: **NOT ESTABLISHED** (full suite not run; external inputs still
  missing). Required-term gate: **CLOSED**. PR **#13 OPEN**, not merged.
- **A33 approved provisionally**, no counting change; **A34 approved and
  implemented**; **A32 still NOT RATIFIED** — separate ratification required.
- No real-filing positive early-release case in the five examined filings;
  positive coverage is synthetic. Moneyview's provision is outside the routed
  capital-structure range and is exercised at rule level only.
- Modules B/E/F remain blocked on peer, assessment and market-observation
  inputs for both issuers. Jio still uses five manual issue terms with no
  official discovery provider; Paras uses separately supplied identity-bound
  terms. Neither is a like-for-like replay of the 2026-10-23 published record.
- Alternative C (a structured carve-out field) and A33's role-recovery
  improvement remain separately authorized decisions.

---

## Revision 32 — Gemini architecture recommendations reconciled against the merged tree; one documentation defect corrected — 2026-10-28

**Scope: read-only architecture reconciliation, one documentation correction, one new
regression module. No engine, config, schema, scoring, knockout, weight, threshold,
penalty or historical evaluation record was changed. No adapter was written and no
provider was selected. PR #13 is MERGED (superseding Revision 31's "OPEN").**

### 1. Authoritative state at the start of this revision

- `main` = `2db28f2aeb17b2542140c4a18ed61ee3bfa9f182`; verified ancestor of `origin/main`.
- **PR #13 MERGED** 2026-10-28T07:03:40Z; head `c446916a02948a4381d07f632eff4671678e21ea`;
  merge commit `2db28f2`; merge tree equals the PR head tree (`64fe70a3`).
  Revision 31's "PR #13 OPEN, not merged" is historical and superseded here.
- **A33/A34 present in `main`**: both decision records read `APPROVED`;
  `extraction/sections.py` carries `_sentence_evidences_early_release` (2 hits); no
  `kmp_exits_2y` engine diff since the pre-A34 base.
- Latest prior revision: 31. Full reconciliation:
  `docs/investigation/ARCHITECTURE-RECONCILIATION-2026-10-28.md`.

### 2. Disposition of the Gemini recommendations

| Workstream | Disposition | Basis |
| --- | --- | --- |
| Modular input orchestration (10 stages) | **Already the implemented shape — no framework built** | each stage traced to a module; provenance probe green |
| UNKNOWN scoring / completeness | **Retained; re-measured, not assumed** | available 73 + unknown 27 = 100; completeness 73 %; base 38; bounds 25–62 |
| Gemini's UNKNOWN-excluded formula | **Refused** | contract is UNKNOWN-in-denominator; not introduced |
| K1–K6 tri-state | **Retained** | K1/K5/K6 UNVERIFIED on the live record, K2/K3/K4 CLEAR on supplied leaves |
| RHP placeholder discovery | **Implemented; 13-variant matrix executed** | all markers → `None`; no real number misclassified |
| RHP addendum class | **Not invented** | no addendum observed in any of the five retained filings |
| Statutory-ceiling substitution | **Absent — verified** | `_gcp_amount` UNKNOWN; legal max reported separately |
| `ExchangeDemandAdapter` (Module F) | **Contract complete, acquisition absent** | `OfficialSubscriptionAdapter` + `AnchorAllotmentAdapter`; `fetch` raises `NotImplementedError` |
| Peer-financials provider | **Same shape** | `PeerMultipleAdapter`; no live client |
| Governance/disclosure extraction | **Implemented under A19/A22–A29** | 237-test focused battery |

### 3. Proven defect corrected

**D-3 (documentation).** `docs/FINAL_REPORT.md` §L.5 claimed
`validate_fail_closed_unknown()` "emits warnings if test constants leak into real
evaluations". It has **no caller** in `engine/` or `tests/`, so it emits nothing. The section
now states that accurately, records that only `price_band_high == 220` is inspected while the
other four `FORBIDDEN_FIXTURE_DEFAULTS` entries have no consumer, and records the
`is_vishal = "VISHAL" in ipo_id` exemption — the only issuer-specific branch in `engine/`
outside fixture definitions — as a governance question (G-3), not silently "fixed".

**Refuted hypothesis (recorded, no change).** `derived.py`'s
`sum(x.get("pre_issue_shares") or 0.0 …)` looks like it would zero-fill a partially described
seller row, overstating `promoter_ofs_pct_of_holding` and possibly firing K4's `> 50`.
Reproduction returned `SchemaValidationError: 'pre_issue_shares' is a required property`;
`schema/ipo-input.v1.5.schema.json::$defs.seller` requires both counts, typed `number`,
`minimum 0`. The fallbacks are unreachable. **No defect, no code change** — pinned instead (§4).

### 4. Regression safeguard added

`tests/test_seller_row_contract_20261028.py` (**8 tests**): complete rows accepted; a row
missing `pre_issue_shares` or `shares_sold` rejected; `null` rejected; numeric strings
rejected; and a positive control showing complete rows form the ratio exactly
(`1,500,000 / 1,500,000` → K4 leaf `100.0`, `TRUE`). This pins the *structural* reason
"absent" cannot become "zero" in the two ratios that feed K4 and the 2-point band, so a future
schema relaxation fails loudly instead of silently changing a knockout.

Tier gate green: the module mentions neither `pdf` nor `ingest`, so no
`tests/tier_inventory.py` declaration is required (verified by running the gate).

### 5. External dependencies — measured, not asserted

`bseindia.com`, `nseindia.com` and `screener.in` all fail at TLS
(`URLError: TLS/SSL connection has been closed (EOF)`); TCP connects only because the egress
proxy accepts and then drops. No provider credentials exist; `BaseConnectorAdapter.fetch`
raises `NotImplementedError`; `connectors/` contains no HTTP client. **Therefore every
acquisition statement in this revision is a contract statement, never a source claim**, and
no provider was integrated.

### 6. Governance decisions opened (not decided here)

- **G-1** — may a specific provider be adopted, under what licence and retention rules?
- **G-2** — if an addendum is ever ingested, does it supersede the RHP value or is it an
  A30 same-class conflict to withhold? (unobservable without a specimen)
- **G-3** — should `validate_fail_closed_unknown()` be wired to a gate, under a
  provenance-based rule rather than an issuer-name substring?
- **G-4** — **A32 remains NOT RATIFIED**; A34 does not ratify it (A34 §0.3).
- **G-5** — A33's name/formula mismatch and role recovery; A34 alternative C.

### 7. Verification (this tree)

- Focused battery, 10 authoritative modules (invariants, governance, coverage, peers,
  connectors, tier gate): **237 passed**.
- `tests/test_seller_row_contract_20261028.py`: **8 passed**. Tier gate: **1 passed**.
- **Full suite: 2209 passed, 0 failed, 0 skipped** (1251.0 s) — the 2201 baseline plus this
  revision's 8 new tests.
- Integrity: 4 schemas valid; `verify_frozen_core()` True; `verify_golden_result()` True;
  `verify_v1_6_implementation()` PASS; `compileall` over `engine` and `tests` clean.
- No A33/A34 semantics, weights, thresholds, bands, knockouts or evaluation records changed;
  golden hash and frozen core untouched.

---

## Revision 33 — G-3 resolved: the fail-closed fixture safeguard is enforced, provenance-based, and fully covered — 2026-10-28

**Scope: one corrected validator, one new regression module, documentation. No scoring,
threshold, weight, penalty, knockout, config, schema, canonical-field or `derived.py`
change. A33/A34 and every evaluation outcome are unchanged.**

### 1. Correcting a previous revision

Revision 32 (and `docs/FINAL_REPORT.md` §L.5 before it) recorded
`validate_fail_closed_unknown()` as having **no caller**. That was **wrong**: the call site is
`enrichment_contract.py:296`, inside `validate_enrichment_contract()`, and the search that
"found" none had excluded the defining file. The rule *is* wired at the enrichment-contract
boundary (`validate_enrichment_contract` → `enforce_enrichment_contract`).

What is true, and is the substance of G-3: **that boundary is exercised only by tests.** No
production ingest path validates a supplemental enrichment document, and
`EnrichmentEngine.assemble()` never calls the contract validator.

### 2. Reachability — no test-only default can reach a real evaluation

| Vector | Status |
| --- | --- |
| `CanonicalInputBuilder(allow_fixture_fallbacks=False)` — the default | closed; every constant is `X if flag else None` |
| `DocumentExtractor.extract_from_pdf(..., allow_fixture_fallbacks=False)` — the default | closed |
| `PresentationService._ingest_document_impl` | passes `allow_fixture_fallbacks=False` explicitly |
| `supplemental=` on a production `assemble()` call | never passed |
| locator-less notice value reaching canonical evidence | locator is synthesised, so never provenance-free |

`allow_fixture_fallbacks=True` occurs in tests only. **Equivalent protection already existed**,
so per the standing rule **no production gate was wired** — that would be an unjustified
behaviour change.

### 3. Defects confirmed and corrected

**3.1 The issuer-name exemption was live.** `is_vishal = "VISHAL" in ipo_id` suppressed the
warning for any issuer whose name contained `VISHAL` and raised it for every other issuer on an
identical locator-less payload (measured: `VISHAL` → no finding; `PARAS` and no-`ipo_id` →
finding). A provenance question was decided by a name. It was also pointless for its apparent
purpose, because the reference payload already carries a locator. **Removed.**

**3.2 Declared coverage exceeded implemented coverage.** `FORBIDDEN_FIXTURE_DEFAULTS` declared
five constants; only `220` was checked. The rule is now driven by that mapping for the
source-fact `price_band.*` entries, so **208, 220 and 68 are all enforced**.

**3.3 The two remaining entries cannot be adjudicated here**, and are excluded with the reason
in the source: `derived.post_issue_eps` is a `derivedValue` whose contract requires
`is_derived`/`formula`/`dependencies` and has **no** `locator` field — "no locator" is its
correct shape; `business.top5_customer_pct` has no `business` block in the artifact. Both remain
guarded by `allow_fixture_fallbacks`.

**3.4 The rule had no test at all.** `SUSPICIOUS_FIXTURE_DEFAULT_PRICE` was referenced by zero
tests. The code is now `SUSPICIOUS_FIXTURE_DEFAULT_VALUE` (no consumer referenced the old
name), severity stays WARNING so no document is rejected by it, and both `raw_value` and
`normalized_value` slots are checked.

### 4. Files

| File | Change |
| --- | --- |
| `engine/ipo_screening/enrichment_contract.py` | **only engine change** — name exemption removed, rule driven by `FORBIDDEN_FIXTURE_DEFAULTS`, documented exclusions |
| `tests/test_fail_closed_fixture_safeguard_20261028.py` | **new (23 tests)** — enforcement at the contract boundary, builder reachability, four-issuer provenance matrix, coverage, exclusions, legitimate-data preservation, semantics preservation |
| `tests/test_suite_tiers.py` | module declared in `SYNTHETIC_EXCEPTIONS` with its reason (inspection only, nothing decoded) |
| `docs/FINAL_REPORT.md` | §L.5 corrected again — the "no caller" statement replaced with the measured chain |
| `docs/investigation/G3-FAIL-CLOSED-SAFEGUARD-DISPOSITION-2026-10-28.md` | **new** — full disposition |
| `docs/investigation/ARCHITECTURE-RECONCILIATION-2026-10-28.md` | G-3 and its inventory row updated |
| `tests/test_jio_current_engine_result_20261027.py` | divergence pin 20 → 21: `enrichment_contract.py` now differs from the 2026-10-23 fingerprint; assertion strictness unchanged, reason recorded |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` | this revision |

### 5. Verification (this tree)

- **23 passed** — the new module.
- **48 passed** — `test_enrichment_contract` (13), `test_price_band_notice` (20),
  `test_enrichment_engine` (15).
- **8 passed** — `test_fixture_fallback_isolation` Tests A–H.
- **80 passed** — the above plus the tier gate.
- **199 passed** — scoring/UNKNOWN/knockout/golden/A33-A34 battery
  (`test_core_semantics`, `test_overlays_knockouts`, `test_vishal_golden`,
  `test_v16_implementation`, `test_validation_gates`,
  `test_a34_issuer_reproduction_20261027`, `test_lockin_institutional_carveout`,
  `test_seller_row_contract_20261028`).
- **Full suite: 2232 passed, 0 failed, 0 skipped** (1505.7 s) — the 2209 baseline plus the
  23 new tests.
- Integrity: 4 schemas valid; `verify_frozen_core()` True; `verify_golden_result()` True;
  `verify_v1_6_implementation()` PASS; `compileall` over `engine` and `tests` clean.
- A33 and A34 decision records still read `APPROVED`; the Jio divergence pin now records 21
  files (was 20) because this revision changed one engine file.

### 6. Remaining governance question — G-3a

> Should the supplemental-enrichment contract be enforced on a production ingest path — i.e.
> should `EnrichmentEngine.assemble()` validate its `supplemental`/`price_band_notice` input
> before use?

Not decided here: it would change ingest behaviour and could reject documents currently
accepted, and **no demonstrated defect requires it** (§2). It needs an owner decision; the
evidence that would resolve it is a production enrichment document the contract rejects while
the engine would otherwise accept it — no such specimen exists in the retained corpus. The rule
itself is now correct and fully covered, so it is safe whenever enforcement is decided.

---

## Revision 34 — discovery path mapped end to end; the exchange page that vanished on re-read; G-2 blocked on evidence — 2026-10-28

### 1. What this pass was for

Advance the official-document discovery workstream (G-2) on top of G-3, and map the existing
discovery path across the ten dimensions the work order named — without a second discovery
implementation, without issuer-specific exceptions, and without inventing a precedence rule
the contract does not contain. Full disposition:
`docs/investigation/OFFICIAL-DOCUMENT-DISCOVERY-DISPOSITION-2026-10-28.md`.

### 2. The defect found while mapping dimension 9

`NoticeSnapshotCache.get` implemented A30 rule 1 ("re-read a document under its own class") for
the Prospectus and the RHP only. The two HTML classes fell through to the notice path, which
refuses HTML **by class**, so both read back as `None`:

> `EXCHANGE_ISSUE_PAGE` and `INVESTMENT_PLATFORM_PAGE` snapshots returned `(None, False)`.

The exchange issue page is the document the discovery path exists to find. **Fix:** a
`_HTML_TERM_CLASSES` frozenset and one dispatch branch to `ExchangeIssuePageParser`, with the
**stored class re-asserted** on the result. The re-assertion is the authority boundary: the
parser always labels its own output `EXCHANGE_ISSUE_PAGE`, so without it a platform snapshot
would return labelled an official exchange publication. Identical values on a platform never
make it official.

**Reach, stated precisely:** `put()` has no production caller today; `get()` is wired into
`IssueTermsResolver.resolve` whenever `IPO_ISSUE_TERMS_CACHE_DIR` is set. This is a correctness
repair on a **wired read path whose write side is not yet populated in production** — not a
data loss observed in the field. It is a defect all the same: the first `put()` caller loses
every exchange-page snapshot on re-read.

### 3. The fake-listing defense, confirmed on a real page

The pre-2026-10-18 rule (marker substrings over the whole document) produced a false
`NOT_FOUND`, hence a false `UNPUBLISHED`. It was previously tested against authored fixtures
only. This pass ran it against `evidence/ipo-subscription/vnl-20261011/vnl-issue-information.html`
— a **genuine retained** NSE issue-information response:

| probe | result |
| --- | --- |
| `_classify_listing` | `empty` |
| `_has_issue_entries` | `False` |
| `_issue_records` | `0` |
| contains `price band` / `issue information` chrome | **True** (a marker rule would have said `ok`) |

The defense holds on real exchange output, not only on the fixture written to test it. The same
page is a clean extraction-failure specimen: the issuer is recovered
(`NAL Academy Limited`, `EXCHANGE_ISSUE_PAGE`) and **no terms** are produced, because it states
none. Identification without manufacture.

### 4. G-2 — BLOCKED, recorded, not coded

Searched: `find` for `*addend*|*corrigend*|*errata*|*amendment*` across the whole tree
(excluding `.venv`) → **0 hits**; all 12 retained PDFs enumerated, none an addendum;
`grep` for `precedence|supersed` over `engine/ipo_screening` → only the source-class precedence
in `connectors/coordinator.py`, the `PBN > Supplemental > RHP` class order at
`enrichment_engine.py:565`, and `lifecycle.py`. **None addresses a later document revising an
earlier one.**

No specimen was fabricated and described as an issuer document. No universal precedence rule
was invented: later-supersedes-earlier, same-class-conflict, field-wise-latest-wins and
source-class-rank are all plausible and mutually inconsistent. The engine's existing behaviour —
withhold on conflict, never first-wins, never last-wins — is the defensible resting state, and
is why G-2 blocks nothing else.

**Owner-supplied evidence required:** (1) one real addendum/corrigendum, or a later exchange
notice revising a band/lot/date, with publication timestamp, issue identity, the revised field
quoted, and the class of both documents; (2) an explicit statement whether it **supersedes**,
**supplements** or merely **conflicts**, and on what recorded basis; (3) the tie-break when the
later document is of *lower* authority than the earlier one — otherwise the platform rule
("a platform never confers authority") will resolve it by accident.

### 5. Source feasibility

Per-source table in §5 of the disposition. Content requests this pass, not DNS:

```
bseindia.com IPOIssues / api.bseindia.com GetPublicIssue / nseindia.com api /
sebi.gov.in   -> TLS/SSL connection has been closed (EOF)   (all four)
```

No source is claimed verified from this sandbox, and no reachability claim is made from
connectivity. **Blocking limitation:** live official retrieval cannot be exercised here at all;
every live-source claim is either a code-path claim with injected bytes or a claim about a
**retained capture**.

### 6. Files

| File | Change |
| --- | --- |
| `engine/ipo_screening/issue_terms.py` | **only engine change** — `_HTML_TERM_CLASSES` + one `get()` dispatch branch re-asserting the stored class (+22 lines) |
| `tests/test_notice_cache_html_classes.py` | **new (6 tests)** |
| `docs/investigation/OFFICIAL-DOCUMENT-DISCOVERY-DISPOSITION-2026-10-28.md` | **new** — full disposition |
| `docs/investigation/ARCHITECTURE-RECONCILIATION-2026-10-28.md` | G-2 row updated |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` | this revision |

**Not changed:** the Jio divergence pin stays **21** — `issue_terms.py` was *already* a member
of `DIVERGENT_ENGINE_FILES`, so the set and the exact-equality assertion are untouched. This was
**verified by running the pin**, not assumed; an earlier expectation that it would move 21→22
was wrong. `SYNTHETIC_EXCEPTIONS` unchanged — the new module names no PDF/ingest module and is
not a tier-gate candidate (tier gate run, passes).

### 7. Verification — focused only

- **6 passed** — `tests/test_notice_cache_html_classes.py`.
- **5 of 6 fail with the engine fix reverted** (the sixth, metadata recording, was already
  satisfied by `put()`) — the tests are load-bearing, not vacuous.
- **122 passed, 0 failed, 0 skipped** in 128.65 s — `test_notice_cache_html_classes`,
  `test_notice_cache_document_class`, `test_official_discovery`,
  `test_automatic_official_issue_discovery`, `test_issue_terms_multisource`,
  `test_issue_terms_windows_retrieval`, `test_suite_tiers`,
  `test_jio_current_engine_result_20261027`.
- Integrity: tier gate passes; Jio divergence exactly the pinned 21 files.

**FULL-SUITE REGRESSION TESTING NOT RUN** — pending the user's explicit approval.

### 8. Governance unchanged

G-2 blocked (§4). G-3a, G-1, G-4 (A32 **not ratified**), A33 role recovery, A34 alternative C,
and unrelated adapters remain out of scope and unstarted. A33 Alternative A and A34
Alternative B remain **APPROVED**.

---

## Revision 35 — official-document cache-policy disposition and governance reconciliation — 2026-10-28

**Documentation-only follow-through. No production code, tests, cache gate, TTL, status check,
invalidation behaviour, resolver behaviour, or governance rule changed.** Full detail:
`docs/investigation/OFFICIAL-DOCUMENT-DISCOVERY-DISPOSITION-2026-10-28.md` §8.

### Disposition

- `EXCHANGE_ISSUE_PAGE` cache writes **remain closed**. There is no demonstrated operational
  need; configured providers are still inspected (a cache is evidence, not permission to skip
  revalidation); no adequate post-close cache rule exists; and the default 168-hour TTL exceeds
  the approximately three-day issue window. Revision 34's HTML read-path repair is valid but
  does not authorize write admission. This is not a permanent prohibition.
- `INVESTMENT_PLATFORM_PAGE` cache writes **remain closed** and its independent
  `verified=False` restriction remains intact.
- A future exchange-cache activation requires demonstrated operational need and an explicitly
  authorized policy covering class-specific freshness/expiry, post-close serving, outage
  availability versus revalidation, identity and issue-window binding, provenance and
  verification, A30 conflict handling, and A31's pending-ratification relationship.
- Alternative C (narrow, identity-bound caching) is a possible future option, **not approved**.
  No TTL, post-close exception, or gate change is selected.

### Authority boundaries preserved

A30 rule 6 remains controlling: conflicts are reported and withheld, never first-wins or
newest-wins. G-2 remains unresolved absent an applicable specimen or explicit owner decision;
its completed search was not repeated. A31 remains implemented/submitted but **not ratified**,
and is not treated as an approved cache precedent. Owner decisions remain necessary for a new
post-close serving policy and for any outage strategy that trades source revalidation against
availability. The existence of a disconnected cache path does not prove operational need.

### Validation

Documentation diff and whitespace checks only. Existing focused receipts and their stated scope
are preserved; TLS handshake failures remain findings about the tested environment only. No
live official-source verification is claimed. **FULL-SUITE REGRESSION TESTING NOT RUN.**

---

## Revision 36 — consolidated Gemini recommendations reconciled against the authoritative tree — 2026-10-28

**Scope:** documentation/evidence reconciliation only. Full register:
`docs/investigation/CONSOLIDATED-GEMINI-RECOMMENDATIONS-RECONCILIATION-2026-10-28.md`.
Revision 35 and the existing cache disposition are preserved; no cache investigation was
repeated and no production code, tests, config, schema, scoring, knockout, adapter, cache or
resolver behavior changed.

### Baseline and merged state

Fresh fetch/inspection confirmed branch and `origin/main` are both `0a77bf95a3fa74101bd40d1137c4dd33badb5e87`
(tree `2856c8d17f7ff63b98abce1ed270e244d8b8aa06`). PRs #13–#16 are merged at
`2db28f2`, `4cc81a9`, `e7934b1`, and `0a77bf9`. The pre-existing local Revision 35 and
official-discovery §8 changes were reviewed and retained.

### Final recommendation statuses

| ID | Status | Controlling result |
|---|---|---|
| G1 | **COMPLETE — VERIFIED** | staged orchestration and all six reproducibility identities/hashes already exist; no duplicate orchestrator |
| G1A | **PARTIALLY COMPLETE** | exchange-demand normalization/provenance/assembly exist; acquisition and approved source/event/cutoff/licence semantics do not |
| G1B | **PARTIALLY COMPLETE** | fail-closed peer snapshot/comparability contracts exist; live provider, licence and provider-specific normalization do not |
| G2A | **PARTIALLY COMPLETE** | discovery contract and PR #16 correction merged; live verification externally blocked and G-2 unresolved |
| G2B | **PARTIALLY COMPLETE** | demonstrated G-3 defect merged; G-3a has no production defect specimen; A32 remains unratified |
| G3A | **COMPLETE — VERIFIED** | UNKNOWN scoring contract retained; Gemini's alternative formula rejected |
| G3B | **COMPLETE — VERIFIED** | peer integrity and valid-only/fail-closed behavior retained |
| G3C | **COMPLETE — VERIFIED** | K1–K6 tri-state behavior retained |

### Priority result and boundaries

P1 canonical/evidence architecture is complete; no integration-contract defect justified code.
P0, P2 and P3 are partially complete because their implementations/reconciliation coexist with
explicit residual decisions or external evidence gaps. P4 exchange demand and P5 peer financials
remain blocked by provider/source/licensing/semantic decisions and source access; fabricating a
client against no qualified bytes would not advance them. No independently executable code work
remains behind those boundaries.

A32 and A31 remain **not ratified**. A33 Alternative A and A34 Alternative B remain approved at
their recorded boundaries. G-2 remains subject to A30 rule 6 absent a specimen and decision.
G-3a remains unresolved without a demonstrated production counterexample. Retained Paras bytes
are not promoted to independently verified official evidence. Prior TLS EOF findings remain
specific to the tested environment.

The older shorthand “`BaseConnectorAdapter.fetch` raises `NotImplementedError`” is corrected:
the current base adapter has abstract `normalize`, which raises `NotImplementedError`; there is
still no live acquisition client. The substantive acquisition-empty disposition is unchanged.

### Validation

Fresh Git/GitHub metadata inspection, authoritative-file review, complete diff review and
`git diff --check`. Existing focused receipts were reused and are enumerated in the consolidated
record; no code/test change justified rerunning them. **FULL-SUITE REGRESSION TESTING NOT RUN.**
No PR, push, merge, commit, production activation, cache change or CI trigger was performed.

---

## Revision 37 — outstanding dependency qualification: retained demand evidence bounded; provider gates remain closed — 2026-10-28

**Documentation-only targeted follow-through on Revision 36.** Details:
`docs/investigation/CONSOLIDATED-GEMINI-RECOMMENDATIONS-RECONCILIATION-2026-10-28.md` §10.
No consolidated investigation or cache assessment was repeated.

### Exchange demand

The retained VNL package supplies hash-matching JSON observations for issuer/issue identity,
NSE-specific demand, separately labelled All Exchange demand, categories and display timestamps.
It remains non-authoritative investigation evidence under A10: source qualification and
implementation authority are not granted; BSE-native identity and All Exchange composition are
not established; no licence/terms content is retained. No adapter was started.

Qualification also found a transfer-integrity boundary: the retained HTML is 313,038 bytes /
`6beb26dc…f5ce6`, not the manifest's 313,040 bytes / `2ae7009b…e78f2`; and the manifest's
register hash describes its CRLF representation, not the LF checkout. The seven non-HTML JSON/JS payloads
covered by the manifest match. No evidence file was altered. Recovering the manifest-matching
HTML (or a governed transfer-record correction) is now an explicit evidence action, not a live
source claim.

### Peers and governance

No candidate external peer-provider schema, representative history or applicable licence is
retained; filing tables, fixtures and evaluation snapshots cannot qualify a provider. A31 remains
pending ratification; A32 remains not ratified; their existing records already contain the
requests, so none was duplicated. No G-2 specimen and no G-3a production counterexample appeared.

### Exit conditions and validation

Exchange-demand exit requires source-native capture provenance, applicable terms, exchange/All
composition evidence and approved event/category/denominator/cutoff/outage/scoring semantics.
Peer exit requires a versioned schema, representative history, definitions and terms, followed
by provider/licence and comparability decisions. Validation: JSON parsing, SHA-256 comparison,
governance/specimen checks, diff review and `git diff --check`. No code/tests/evidence/cache
behavior changed. **FULL-SUITE REGRESSION TESTING NOT RUN.** No PR, push, merge, commit, CI
trigger or production activation occurred.

---

## Revision 38 — VNL HTML discrepancy bounded to the pre-commit transfer path; exact bytes unrecovered — 2026-10-28

Targeted follow-through only; consolidated investigation and cache policy were not reopened.
Full evidence: `CONSOLIDATED-GEMINI-RECOMMENDATIONS-RECONCILIATION-2026-10-28.md` §§10.5–10.6.

The manifest expects 313,040 bytes / full SHA-256
`2ae7009b9f30c026c91a1d38a4b943f348ab3f275f0b1b5b971481a8f72e78f2`.
The first and only Git version, source-evidence commit `951d77d4`, current `main`, GitHub content
metadata and this checkout all agree on blob `21ea96b`: 313,038 bytes / full SHA-256
`6beb26dc8acce2f9cd6620a761ec5d771da46b3214d220e6946bea37614f5ce6`.
No earlier/candidate retained copy exists.

No `.gitattributes` existed when the evidence was added; the current path is still not `-text`.
The manifest's registered CRLF representation versus its committed LF blob proves line-ending
transformation in the original transfer/add path. That makes two removed CR bytes in a
mixed-ending HTML plausible, but does not prove their positions or recover the expected hash.
Disposition: **checkout integrity verified; pre-commit byte recovery unresolved**. Evidence bytes
were not changed. `.gitattributes` now applies `-text` to the VNL package so future checkouts
preserve the committed bytes; this does not equate them with the missing original. Resolution
requires either the custody-backed original matching the full manifest hash, or an owner-approved
register correction preserving both identities and declaring the original unavailable.

The permitted route yielded Git/GitHub history only—no new exchange bytes/terms or peer-provider
schema/history/licence. A10 limits VNL data to distinct evidence/display use; NSE/BSE/All,
category/denominator, event/cutoff, outage and scoring/Final decisions remain open. Peer provider
and comparability qualification remain blocked. A31/A32 remain unratified; G-2/G-3a triggers are
absent. No adapter work became executable.

Validation: object/blob/history/attribute/config inspection, complete SHA-256 checks, retained-copy
search, diff review and `git diff --check`. No code, test, evidence, cache or production behavior
changed. **FULL-SUITE REGRESSION TESTING NOT RUN.** No commit, PR, push, merge or CI trigger.

---

## Revision 39 — VNL dual-identity amendment APPROVED and effective; source qualification remains evidence-blocked — 2026-10-28

RAMKI explicitly **APPROVED** the amendment on 2026-10-28 under A1. The effective record in
`evidence/ipo-subscription/A8-S_EVIDENCE_ACQUISITION_REGISTER.md` affects only
`vnl-issue-information.html`: it preserves the unrecovered original-capture identity
(313,040 bytes, `2ae7009b…e78f2`) and designates the first durable Git artifact
(313,038 bytes, `6beb26dc…f5ce6`, blob `21ea96b`, commit `951d77d4`) as the retained repository
artifact without claiming byte identity. The approval is evidence-bookkeeping authority only;
it does not qualify a source or authorize a provider, adapter, scoring, `FINAL`, production or
cache behavior.

No new custody-backed original, source-native exchange capture, applicable provider terms,
peer-provider schema or representative provider history appeared in the current worktree, and
no new permitted external route became available. Exchange demand therefore remains blocked on
source/terms, NSE-BSE-All composition and owner category/denominator/event/cutoff/outage/scoring
semantics. Peer qualification remains blocked on authoritative schema/data/timestamps/definitions,
terms and provider/comparability approval. No adapter work is authorized.

A31/A32 remain unratified; no new G-2 specimen or G-3a production counterexample exists. Existing
decision requests remain controlling and were not duplicated. Validation was documentation
integrity review and `git diff --check`; no evidence bytes, production code, tests, cache gates or
runtime behavior changed. **FULL-SUITE REGRESSION TESTING NOT RUN.** No commit, PR, push, merge or
CI trigger.

---

## Revision 40 — A31 and A32 explicitly ratified by RAMKI — 2026-10-28

RAMKI supplied explicit decisions: **A31 — APPROVE; A32 — APPROVE.** Existing decision records
were reconciled in place; no duplicate request or decision record was created.

- **A31 RATIFIED.** The approved scope is the opt-in, identity-bound use of closed exchange
  records: exact issuer, filing-established bid window, exchange issue number/scrip identity,
  internal consistency, conflict withholding, no-window/no-admission, and historical silence
  never establishing `NOT_FOUND`/`UNPUBLISHED`. Ratification also confirms the associated A30
  §5.6 frozen-core pin. It does not enable the path by default, widen an allow-list, decide the
  configured-URL host question, resolve an issuer term, authorize an evaluation, or establish
  cache policy.
- **A32 RATIFIED.** The approved scope is the recorded application of A22/A23 evidence-or-UNKNOWN
  to the five builder fields: strict real-filing input exists only when a reader establishes it;
  otherwise dependent metrics remain UNKNOWN. Synthetic-template fallback remains intentional.
  Ratification creates no criterion, weight, threshold, scoring, schema or historical-evaluation
  authority and does not resolve the absent-reader or stated-basis items in A32 §6.
- **A34 boundary preserved.** A34 did not ratify A32; A32's ratification is the separate explicit
  2026-10-28 owner decision recorded here and in A32/A34.

Documentation-only governance reconciliation. No production code, tests, evidence bytes,
provider/source qualification, scoring, `FINAL`, cache or runtime behavior changed. Validation:
status/authority diff review and `git diff --check`. **FULL-SUITE REGRESSION TESTING NOT RUN.**
No commit, PR, push, merge or CI trigger.

---

## Revision 41 — ratified A31 operator path documented; restrictive runtime unchanged — 2026-10-28

The independently executable post-ratification gap was operator documentation, not runtime code.
`docs/RUNBOOK.md` §17 now records the existing opt-in `IPO_OFFICIAL_HISTORICAL_LISTINGS` path,
HTTPS/discovery-host validation, filing-window identity requirement, read-only `issue-terms`
command, exit codes, acceptance criteria and fail-closed interpretation.

The runbook explicitly preserves: off-by-default search; no name-only admission; historical
silence never proving non-publication; transport failure distinct from absence; no operational
allow-list widening; no evaluation write; and no cache authority. The configured-notice host
question and live HTTPS egress remain external/policy dependencies.

A32 inspection found no unfinished work inside its ratified five-field application: strict-path
defaults remain `None`, intentional synthetic-template fallbacks remain gated by
`allow_fixture_fallbacks=True`, and the two unread fields remain outside implementation authority.
No code or test changed. Exchange-demand and peer-provider work received no new permitted source
artifact, so no qualification or adapter change was made.

Validation: exact documentation diff review, static configuration/guard inspection and
`git diff --check`. **FULL-SUITE REGRESSION TESTING NOT RUN.** No commit, PR, push, merge or CI
trigger.

---

## Revision 42 — official RHP peer tables confirmed primary; paid provider selection closed for current need — 2026-10-28

The peer-financial path was reconciled against implementation and retained specimens. Existing
`DocumentExtractor` → `SectionExtractor.extract_peers` → canonical `peers` → classified/frozen
`peers.json` already supplies the currently consumed issuer-disclosed peer multiples from official
RHPs. Four observed layouts are implemented and previously focused-tested: R.K. Fashion, Vishal
Nirmiti, Jio and Paras. Header-bound mapping, placeholder preservation, valuation-date handling,
issuer-row exclusion and unrecognised-layout withholding remain fail-closed.

No parser change was justified. The v1.5 peer contract cannot preserve face value, EPS, NAV/raw
price, reporting period, row-level quotation/footnotes or per-value verification; adding them
requires a separately authorized additive/versioned contract, not speculative parsing.

The existing `--peers` JSON snapshot input and immutable `peers.json` persistence make a second
local store unnecessary. The supplemental schema's declared `peer_data` block is not consumed by
the enrichment engine. Neither route is approved as a manual scoring-evidence path: `--peers`
does not gate admission on verification, the provenance-bearing supplemental route is unwired,
and the peer schema lacks the distinctions above. No sample values or operator activation were
added.

**Provider disposition:** paid selection is **CLOSED — CURRENT DECISION** for the present
personal-use requirement because the official filing path supplies currently consumed disclosed
multiples. PF-01 EOD, PF-02 FMP and PF-03 Alpha Vantage are **DEFERRED**, not failed. PF-04 FMP
plan/licence and PF-05 eligibility/sample access remain **NOT QUALIFIED** because no applicable
terms or representative provenance-bound artifacts are retained. No purchase, provider selection,
licence acceptance, API integration or portal scraping occurred. Reopen only for a named unmet
metric with actual provider artifacts and terms.

Full evidence and boundaries: consolidated reconciliation §10.8. Documentation-only change; no
production code, schema, scoring, `FINAL`, provider authority or cache behavior changed.
Validation: implementation/schema/test-source inspection, exact diff review and
`git diff --check`. Existing focused receipts were reused; no tests were rerun because no
executable code changed. **FULL-SUITE REGRESSION TESTING NOT RUN.** No commit, PR, push, merge or
CI trigger.

---

## Revision 43 — real-filing operational evaluation procedure completed — 2026-10-28

A fresh repository/remote inspection confirmed the active branch and `origin/main` at
`0a77bf95a3fa74101bd40d1137c4dd33badb5e87`; merged PRs #13–#16 are present. Existing historical
receipts include a then-final-main full backend run of 1,908/1,908 and later tree-specific
focused/full runs. Revision 31 explicitly says the full backend suite was not run for PR #13's
code change, so there is no retained full-suite receipt for the exact current `origin/main` tree.
Those reports were inspected, not re-executed or represented as results from this dirty working
tree.

`docs/RUNBOOK.md` §3.2 now closes the practical real-filing gap with the existing CLI only: retain
an unchanged manually obtained official PDF and source details; run strict `extract --enrich`
without fixture fallbacks; inspect canonical identity, source hash, evidence, reporting unit and
RHP-derived peers before scoring; run the reviewed file with a pinned UTC instant; interpret
UNKNOWN/stale/incomparable/unverified states; locate and verify immutable artifacts; and record a
source-byte-bound defect reproduction only for an actual contract mismatch. The runbook also makes
explicit that `--peers` is not approved for manually entered scoring evidence and that an
EV/EBITDA heading does not mean the official-filing extractor emitted that metric.

No new filing was supplied, so no evaluation or store was created. No implementation, parser,
schema, scoring, provider, exchange-demand, discovery, cache, source-authority or production
admission behavior changed. Consolidated Gemini statuses remain unchanged. Validation was command/
implementation cross-check, complete changed-file diff review and `git diff --check`; no test was
rerun for this documentation-only correction. **FULL-SUITE REGRESSION TESTING NOT RUN IN THIS
PASS.** No commit, PR, push, merge or CI trigger.

---

## Revision 44 — exact-tree full backend regression green; integration candidate ready — 2026-10-28

The Revision 31 validation gap is closed. With `origin/main` and the production/test base at
`0a77bf95a3fa74101bd40d1137c4dd33badb5e87`, the complete backend suite was run against this
branch's integration candidate. Its working-tree delta contained documentation, governance/
evidence records and `.gitattributes` only—no production code, test, schema, config, fixture or
scoring file differed from that base.

Command: `PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q --durations=30`. Environment:
CPython 3.11.2, pytest 9.1.1, dependencies from pinned `requirements.txt` in the ignored local
`.venv`. Result: **2,238 collected; 2,238 passed; 0 failed; 0 skipped; exit 0; 25 Starlette
deprecation warnings; 1,493.58 s (24m53s)**. No assertion was weakened and no correction was
required. Durable receipt:
`docs/test-results/FULL-BACKEND-REGRESSION-2026-10-28-a9216594.md`.

This establishes full backend regression readiness for the current implementation plus the
operational documentation candidate. It does not represent a new real-filing evaluation. No
provider, exchange adapter, manual peer-data admission, cache, scoring, schema, source-authority or
production behavior changed. The integration/merge outcome is recorded by the closeout revision
that follows publication.

---

## Revision 45 — PR #17 integration gate green; operational readiness complete — 2026-10-28

Commit `8ad4c2518aac9b714e55c8f3ddfcfd0ff848d51e` published the Revision 35–44
reconciliation and operational-readiness documentation as PR #17 against `main`. GitHub Actions
run `40738214229`, job `122992409309`, completed **SUCCESS** in 22m43s: backend **2,238 tests,
0 errors, 0 failures, 0 skipped**; frontend, schema/integrity, compileall, and clean-tree/diff checks
all passed. The only annotation affecting dependencies is GitHub's Node 20 action-runtime
deprecation notice; it is not a product test failure.

PR #17 was mergeable with no review requirement reported by GitHub and its sole reported check was
green. The post-publication tracker commit itself is documentation-only; the PR merge and resulting
`origin/main` identity are independently verified in the closeout report because a commit cannot
truthfully contain the hash of the future merge that incorporates it.

**Operational-readiness decision: READY for event-driven personal use.** A real filing remains an
event input, not unfinished engineering. Reopen implementation only for a source-byte-bound
reproduction of an extraction/validation/evaluation defect, a verification/replay mismatch, or a
separately qualified missing-data requirement. Existing RHP-first, UNKNOWN, tri-state, provider,
exchange-demand, cache and source-authority boundaries remain unchanged.

---

## Revision 46 — Layer 2A read-only persisted-evaluation gap analysis — 2026-10-29

Implemented the smallest separate observational layer over an explicitly selected immutable
baseline. `ipo_screen gap-report <evaluation-id> --store <root> --output <new.json>` first verifies
the selected record's result and manifest artifact hashes, then copies its persisted
`missing_unverified` rows into deterministic structured JSON. It includes baseline identities and
hashes, exact stored state/reason, criterion module and numeric points only when the baseline
explicitly establishes them, global sources without falsely attributing them to a gap, explicit
reason/provenance unavailability, bounded inspection guidance, and its own `report_hash`.

The command refuses a missing identity, integrity mismatch, existing output, or output inside the
immutable evaluation directory. It performs no extraction, enrichment, scoring, replay, cache
access, evaluation-store write or baseline mutation. Layer 2B manual/external capture and Layer 2C
secondary evaluation remain unimplemented and contract-gated. `docs/RUNBOOK.md` §4.4 records the
CLI and the ten minimum future contract/admission/identity/verification boundaries; `--peers` and
supplemental `peer_data` remain unqualified for scoring.

Validation on CPython 3.11.2 / pytest 9.1.1: focused gap/CLI modules **23 passed**; full backend
`PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q --durations=30` **2,247 passed, 0 failed,
0 skipped**, exit 0, 25 existing Starlette deprecation warnings, 1,209.07 s. Receipt:
`docs/test-results/TWO-LAYER-GAP-ANALYSIS-2026-10-29.md`. No scoring formula, confidence,
knockout, schema, provider, exchange acquisition, source authority, cache or baseline persistence
behavior changed.

---

## Revision 47 — Layer 2B governed supplemental capture and isolated immutable storage — 2026-10-29

Implemented contract `IPO_LAYER_2B_SUPPLEMENTAL_DATA` v1.0 with strict JSON schema, exact verified
Layer 1 binding, deterministic payload identity, a narrow field registry, source-artifact hashing,
operator attestation distinct from source verification, and an isolated immutable supplemental
store. Initial eligibility is deliberately limited to non-negative QIB/NII/retail/overall
subscription multiples for a baseline `MARKET/subscription` gap when the exact Layer 1 value is
not already established. Unit `MULTIPLE_X`, observation timestamp, official-exchange source
metadata, local artifact/hash and locator are mandatory. No entry is scoring-eligible.

Commands: `supplemental-init`, `supplemental-validate`, and `supplemental-inject`. Every command
selects/reverifies the exact baseline; injection reruns all gates. The binding hashes profile,
evaluation ID, IPO ID, result hash and sorted manifest artifact hashes. Storage is
`<supp-store>/<evaluation-id>/<payload-hash>/`, atomic and no-overwrite. Exact duplicates are
reported; differing values for an existing target conflict-reject; normalized/symlink paths into
Layer 1 are refused. Layer 1 artifacts, inventory, verify/replay and scoring are unchanged. Layer
2C remains unimplemented.

Validation: focused **36 passed**. First full run exposed only the new synthetic module's omitted
tier declaration (2,258 passed / 1 inventory failure); corrected without product/test weakening.
Final full backend **2,259 passed, 0 failed, 0 skipped**, exit 0, 25 existing warnings, 1,351.45 s.
Receipt: `docs/test-results/LAYER-2B-SUPPLEMENTAL-DATA-2026-10-29.md`.

---

## Revision 48 — Layer 2C secondary engine, Layer 3 scenarios, and local dual-reality workbench — 2026-10-29

Layer 2C is now implemented as a separate deterministic engine over an exact verified Layer 1 baseline and an accepted Layer 2B payload. Scoring admission is restricted to the four subscription fields in the Layer 2B registry, requires local artifact-hash verification and an observation inside the baseline bidding window, and invokes the unchanged core evaluator. The versioned secondary contract binds baseline result/binding and supplemental ID/hash, records baseline-versus-secondary module attribution and caps, and has isolated immutable storage plus independent verify/replay commands. It does not overwrite or replace Layer 1.

Layer 3 is now an explicitly non-governed scenario overlay. User-asserted peer P/E adjustments affect only Module B; qualitative assumptions affect only Module E. Module and total caps, confidence, and knockout status remain enforced. Payloads and results are isolated from governed stores, canonically hashed, and every point attribution carries `[OPERATOR_ASSUMPTION]`.

The local FastAPI workbench provides evaluation selection, day 1/2/3 bidding inputs, automatic uploaded-file SHA-256 display, Layer 2B injection plus Layer 2C recomputation, operator scenarios, three-reality comparison cards, attribution badges, and hash lineage. It is documented as local single-user tooling without authentication or production authority.

Validation on the implemented tree: focused **35 passed**; complete backend **2,267 passed, 0 failed, 0 skipped, 25 warnings in 1625.84s**; frontend **93 passed**; all schemas, frozen core, golden result, inactive v1.6, compileall, and diff checks passed. Operational Jio acceptance produced baseline `37.0/AVOID/Low`, secondary `39.0/AVOID/Low` with only Module F `+2`, and an operator scenario score `48.0` whose verdict remained `AVOID` because the baseline knockout remains triggered. Secondary verify/replay passed. Before/after Layer 1 byte inventories were identical (`ec4e2634…`), and post-operation Layer 1 verify/replay passed. Detailed receipt: `docs/test-results/LAYER-2C-LAYER-3-WORKBENCH-2026-10-29.md`.

---

## Revision 49 — Layer 2C/Layer 3 web API and `/workbench` wiring — 2026-10-29

The local FastAPI workbench now exposes first-class JSON routes `POST /api/v1/secondary/evaluate` and `POST /api/v1/scenario/evaluate`. Both call the existing governed backend modules and isolated stores directly; they do not duplicate scoring logic or write to Layer 1. `/workbench` serves the day 1/2/3 subscription/evidence form, operator peer and qualitative assertion form, and triple-reality Layer 1/2C/3 cards with attribution badges and hash lineage. Focused API/UI/CLI regression: **24 passed**, one non-fatal dependency deprecation warning.

---

## Revision 50 — Dual-Reality Workbench embedded in the existing frontend — 2026-10-29

The existing Executive Dashboard frontend now has a visible **Dual-Reality Workbench** navigation tab. The tab renders the Layer 2C/Layer 3 workbench in a same-origin iframe at `/workbench/`; the presentation FastAPI application configures it against the exact active evaluation store and an isolated sibling workbench store. Existing loopback and same-origin POST guards explicitly cover only the mounted workbench's governed hash, injection, secondary, and scenario actions. The standalone workbench remains available, but users no longer need to discover or launch a separate UI. Focused backend integration **32 passed** and frontend **94 passed**; compileall and diff checks passed.
