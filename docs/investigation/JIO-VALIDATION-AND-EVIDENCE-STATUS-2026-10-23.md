# Jio Platforms — publication verification, automated validation and evidence status

**Date:** 2026-10-23 · **Branch:** `arena/07f3439f-ipo-screening-engine` · **Status:** integration verified; no new evaluation warranted; four evidence/gate items remain open with named unblock conditions.

This is a non-authoritative investigation path. Nothing here changes scoring, knockout rules, A9 qualification, weights or historical records; `main` is untouched.

---

## 1. What was verified remotely

| Item | Remotely observed value |
|---|---|
| Branch tip | `589e468e06b49c8066bbdb2e3f0729c4d09cd929` |
| Integration commit | `e612702ea22acf221758c44a2f3f98eca85f4d51`, parent `8a1a37022f00496dd22e67b51319a407f6daf6fb`, 85 files (50 added, 35 modified) |
| Receipt commit | `589e468e…`, parent `e612702…`, 1 file |
| Ancestry | `8a1a3702 → e612702 → 589e468`, confirmed with `git merge-base --is-ancestor` |
| Report | `docs/investigation/JIO-CORRECTION-INTEGRATION-2026-10-23.md` (20,111 bytes, blob `cba4bead…`) |
| Evidence directory | `docs/investigation/jio-correction-integration-20261023/` — 9 files |
| Published engine | 66 engine modules; every `engine/`, `tests/`, `schema/`, `frontend/` file re-hashed against the commit object: **0 mismatches** |
| Correction presence | ISSUE routing, debt wording, page-anchored proceeds leaves, sole-promoter row, joint-report tenure, evidence/value agreement, `kmp_exits_2y = None`, `field_map` emission, explicit-map preference and `_find_ofs_nil` all present in the published blob |

### A9 intact

| A9 asset | Blob at `589e468` vs parent `8a1a3702` |
|---|---|
| `engine/ipo_screening/gmp_binding.py` (A28.1 representation/integrity sidecar) | identical |
| `engine/ipo_screening/gmp_evidence.py` (capture-failure guard, PD-unavailability guard, optional-trend linkage) | identical |
| `engine/ipo_screening/gmp_policy.py` (A17 cutoff/freshness) | identical |
| `engine/ipo_screening/connectors/coordinator.py` (explicit-snapshot selection guard) | identical |
| `schema/gmp-qualification-binding.v1.schema.json` | identical |

The gate itself (`_a9_final_gmp_gate` in `evaluation_record.py`) is unchanged: FINAL is withheld with `NONTERMINAL_UNRESOLVED` and reason `MISSING` when the GMP block has no non-null observation, and `SOURCE_UNQUALIFIED` when an observation exists without qualification. The only edits in that file are the two field-map hunks (corrections #8/#9), which sit on the projection path, not the gate.

### Reported vs remotely verified state

No discrepancy was found between the state described at the end of the previous pass and the repository. One clarification is worth stating explicitly: my **local checkout** (`/home/user/ipo-screening-engine`, HEAD `01ba66c`) still carries the unrelated pre-existing working-tree changes it had before this workstream; the published commits were created with `commit-tree` against the remote-parent tree and the branch is updated only to those commits. Nothing in the local dirty tree is part of the published branch, and no unpublished file is claimed as delivered.

---

## 2. Automated validation

### 2.1 CI on the exact commits

Both published commits are covered by the branch's `A9 contract boundary regression` workflow, triggered automatically on push (no dispatch was needed or used).

| Run | Commit | Backend suite | Other steps | Result |
|---|---|---|---|---|
| [39942804962](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39942804962) | `e612702` (integration) | 1670 tests, **1 failure** (1589 s) | frontend ✅, schema/integrity ✅, `compileall` ✅, clean tree ✅ | **failure** |
| [39942848045](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39942848045) | `589e468` (receipt) | 1670 tests, **1 failure** (1822 s) | same, all ✅ | **failure** |

The workflow runs, in this order: full backend suite with JUnit diagnostics, `npm test --prefix frontend`, schema + frozen-core + golden + inactive-v1.6 integrity checks, `compileall`, and a clean-tree assertion (`git diff --exit-code`).

**The same single test failed on both commits**, and on neither is any other step red:

`tests/test_automatic_official_issue_discovery.py::test_image_only_official_notice_uses_real_offline_ocr_and_preserves_original_pdf_hash`

```
AssertionError: retrieved notice names a different issuer: None; OCR header: PRICEBANDADVERTISEMENT
INITIAL PUBLICOFFERINGOFACMEFORGELIMITED
NOTICE TO INVESTORS
...
assert None is not None
```

This test renders a synthetic price-band notice to an image-only PDF and requires the offline OCR path to recover the issuer name, the ₹100–₹120 band, lot 50, the ₹240 million fresh issue and the original PDF hash. On the runner, the OCR engine returned the two upper-case heading lines **without word separators** (`PRICEBANDADVERTISEMENT`, `…OFACMEFORGELIMITED`), so no issuer name could be isolated and the provider rejected the document.

**Diagnosis.** The failure is in the OCR engine's word segmentation, not in the matching logic: `_norm_name()` already strips every non-alphanumeric character, so `ACME FORGE LIMITED` and `ACMEFORGELIMITED` are the same key; the guard failed because `company_name` came back as `None`. The same test, with the same pinned packages (`rapidocr 3.10.0`, `onnxruntime 1.24.4`, `pypdfium2 5.14.0`, `pillow 13.0.0`) and the same DejaVuSans 28 pt rendering, **passes locally in 5.8 s**, where the identical input produced `PRICEBANDADVERTISEMENT` / `INITIAL PUBLICOFFERINGOF ACME FORGE LIMITED` and yielded `company_name = 'ACMEFORGE LIMITED'`. Only the spacing differed.

So this is an environment-dependent OCR-artifact difference between the GitHub runner and this sandbox, deterministically reproducing on the runner (both commits, two separate jobs). It is **fail-closed** — an ambiguous OCR header causes rejection, never acceptance — and it is unrelated to Jio or to any evaluation input. It has nothing to do with Jio: the image-only notice reader and this test were added by the integration, while the broad-fallback name capture that returns `None` lives in the frozen notice parser, which this branch did not modify. No test, engine or config file was changed to make CI pass.

**Open item, with a decision required.** Two remedies exist and I did not choose between them:

| Option | Change | Risk |
|---|---|---|
| **A. Make the fixture realistic** | Give the synthetic notice the identity block real notices carry (CIN / registered office / "to be listed on"), which routes through `_primary_issuer_header` instead of the frozen parser's broad fallback. | Test-only; but it would leave the underlying broad-fallback fragility untested. |
| **B. Normalise OCR headings** | Add a space-tolerant heading normalisation in the OCR pre-pass (outside the frozen parser). | Touches a verification-adjacent path; needs review, and must not repair digits or weights. |

Neither was applied, because both change acceptance behaviour and A16 does not cover rewriting the synthetic fixture to make a red run green.

### 2.2 Independent local run on the exact published tree

The tree was extracted from the commit object with `git archive 589e468…` (not from the reconstructed working directory) and executed in a clean environment.

| Suite | Result |
|---|---|
| Backend `pytest -q tests` | **1670 passed**, 25 warnings, 1206.58 s, exit 0 |
| Frontend `node --test test/*.test.js` | 93 passed, 0 failed |

### 2.3 Test-result lineage (previous pass, preserved)

The first integrated-suite attempt is retained as published evidence, not overwritten: `docs/investigation/jio-correction-integration-20261023/tests-integrated-attempt1.log` — 1668 passed, 2 failed. Causes: one missing fixture (added; passes) and one pre-existing workbook-timestamp flake in `excel.py`, reproduced 0/5 on isolated reruns and unrelated to this integration.

### 2.4 Browser / API acceptance

No browser automation exists in this environment (no WebDriver/Playwright and no browser binary), so a real DOM session was **not** performed and no acceptance is claimed. Instead the complete upload → evaluate → evidence-display path was exercised at the HTTP boundary the browser uses, on the published tree:

| Call | Result |
|---|---|
| `POST /api/v1/ingest/document` (real 11.6 MB PDF, `mode=final`) | **201** |
| `GET /api/v1/evaluations/{id}` | 200 — 34.0, interval 24–77, Low confidence |
| `GET /api/v1/evaluations/{id}/evidence` | 200 — 48 items, page-anchored quotes |
| `GET /api/v1/evidence/{evidence_id}` | 200 |
| `GET /api/v1/ingestions/{id}/events`, `/ingestions`, `/ipos`, `/health` | 200 |

Two API guards were exercised and behave correctly: a non-loopback Host returns `400 LOOPBACK_HOST_REQUIRED`, and a workflow POST without an `Origin` header returns `403`. Evidence display verified end to end for the corrected fields (page 116 proceeds, page 104 promoter row, page 322 tenure, page 430 no-EOM, page 405 contingent total). Detail: `jio-validation-20261023/api-acceptance.json`.

**Untested acceptance criteria (explicit):** real browser rendering of the upload widget, live progress polling in the UI, DOM/CSS presentation of the evidence panel, file-picker validation messages, and keyboard/accessibility behaviour. These remain unverified, not accepted.

---

## 3. Evidence investigation

### 3.1 C1 — GMP / A9

A retained issuer-matched Jio GMP row **does exist**, which sharpens the earlier "no observation" statement:

| Field | Value |
|---|---|
| Container | `evidence/gmp-observations/investorgain-tonbo-20261015/source-captures/investorgain-ipo-gmp-live-331-chunk-0.md` |
| Publisher page | `investorgain.com/report/live-ipo-gmp/331/` (listing index), issue link `/gmp/jio-platforms-ipo/2306/` |
| Printed | `₹227 (20.29%) · 148 ↓ / 227 ↑ · price 1,119 · ₹30,213.00 Cr · lot 12 · 21-Oct → 23-Oct · Updated-On 15-Oct 17:37 · anchor ✅` |
| Second reference | `marketliveipogmp` home capture (21-Oct) shows Jio GMP as `—` (no value) |

It does **not** qualify, for five independent reasons: the publisher is recorded NOT QUALIFIED; the row is a listing-index line rather than a captured issue-page observation; it is rendered Markdown with no provider bytes, headers or receipt time; its observation time (15-Oct 17:37) is eight days outside the A17 24-hour freshness window for a 23-Oct evaluation; and no A28.1 binding or A9 hash subject exists for it.

**Minimum evidence to unblock:** (1) a RAMKI/PA A28-scope source-qualification decision naming publisher, page scope and observation semantics; (2) a capture through the existing capture contract (provider bytes, headers, receipt window, offset-bearing observation time, issuer/issue match) inside the A17 cutoff; (3) a valid A28.1 binding over that observation; (4) the separately authorized accepting verifier that consumes bindings. Nothing was inferred from price or issue size, and A9 stays fail-closed.

### 3.2 C2 — K1, K2, K5

Governing rules were read from `config/ipo-config.v1.5.0.json`; no rule was altered.

| Gate | Leaves and observed state | Document evidence | Missing / decision |
|---|---|---|---|
| **K1** | `auditor_opinion = unqualified` (p324) → FALSE; `net_worth_latest = 3,359,769` → FALSE; `going_concern_uncertainty = UNKNOWN` | The phrase "going concern" occurs **once in 591 pages**, on p253, describing the accounting basis of a 2019 scheme transfer. No "no material uncertainty" sentence exists anywhere. | The filing is *silent* on going concern. Needs either a scoped auditor confirmation, or an approved rule that an unqualified SEBI-format examination report with no GC/EOM paragraph sets the flag False. |
| **K2** | `promoter_pledge_pct = 0` → FALSE; `sebi_ed_action_active = UNKNOWN` | p470: SEBI's 2020 complaint against **RIL (the Promoter)** was dismissed as time-barred and "SEBI has filed a revision application before the Hon'ble High Court of Bombay and the same is currently pending". p487 denies **debarment** only. p463 negates only *undisclosed* matters. | Neither a verified positive nor a verified negative. Requires a scope decision: entity (Company vs Promoter), nature (complaint/revision vs penalty vs debarment), and status (pending revision after dismissal). ED is not mentioned at all. |
| **K5** | ratio `15,021 / 3,359,769 = 0.4471%` → FALSE; `contingent_liab_unquantified = UNKNOWN` | Note 37 (p405) quantifies all five periods; commitments (26,198) are commitments, excluded; no "unquantified/unascertained/cannot be quantified" language appears in the whole document. | Requires a scope decision on whether a complete quantified note with no unquantified language sets the flag False (A20 extension) or the flag stays UNKNOWN without a positive disclosure. |

None of these gates was cleared, and no negative-confirmation rule was implemented.

### 3.3 C3 — net-worth basis

| Basis | Value (₹ million, FY2026) | Source |
|---|---|---|
| Total owners' equity (includes OCI) — **what the engine stores** | 3,359,769 | p329 / p406 |
| ICDR Net Worth (equity share capital + other equity **excluding OCI**) | 3,340,134 | p451: `H 89,390 + I 3,250,744 = J 3,340,134`; definition on p487 |
| Difference | 19,635 | other comprehensive income |

Impact: the K5 ratio moves only from 0.4471 % to 0.4497 % — no gate effect either way; the K1 negative-net-worth leaf is false on both. Net worth also feeds leverage/ROCE style derived metrics, so a change would move those values slightly and needs tests.

**No authoritative decision exists.** Searches across `handoff/decisions/`, config and docs found no net-worth basis ruling (A10/A11 discuss denominators only for subscription data). The narrow question — *should `financials.periods[].net_worth` use the issuer's ICDR Net Worth where printed, instead of total owners' equity including OCI?* — is a governance choice. Options and consequences are recorded in `c3-net-worth-basis.json`; nothing was changed.

### 3.4 C4 — official issue terms

**Engine workflow (authoritative path), run 2026-10-23T11:14:52Z:** `UNAVAILABLE`. Every configured endpoint failed at the transport layer with `URLError: TLS/SSL connection has been closed (EOF)` — NSE upcoming-issues and BSE public-issues among them. This is the sandbox's egress allowlist, **not** evidence of non-publication.

**Independent publication check (rendering client, not an official capture):** the BSE public-issue listing shows *Jio Platforms Limited, MainBoard, 21-10-2026 → 23-10-2026, ₹1065.00–₹1119.00, face value ₹10, Live*; the issue detail page carries **Market Lot 12 / Minimum Bid Quantity 12** and an **anchor-allocation notice dated 2026-10-19**. So the official terms are published; the engine simply cannot reach them from here.

Nothing from that check was written into an official field; the engine's issue terms remain the PA-authorized third-party values tagged `UNVERIFIED` (four authority warnings in every evaluation).

One discrepancy is recorded, not resolved: BSE prints **Issue Size – No. of Shares 19,75,25,934**, while the filing cover and the retained aggregator use **27,00,00,000** fresh shares (₹30,213 Cr at the cap). No value was changed; the reconciliation requires the Prospectus/notice.

---

## 4. Evaluation: not re-run

| Evaluation input | Published `…final-29d9a601` | Fresh acceptance run `…final-66c25a0a` | Equal |
|---|---|---|---|
| Engine source | published tree | same tree (`589e468`) | yes (66 modules, 0 hash mismatches) |
| Config fingerprint | `4a5d92e8…526d2b` | `4a5d92e8…526d2b` | yes |
| `input_snapshot_hash` | `ba27fc4b…3a8f04f` | `ba27fc4b…3a8f04f` | **yes** |
| `peer_snapshot_hash` | `61f5c913…42edb9b` | `61f5c913…42edb9b` | **yes** |
| Evidence objects | 48 items + 48-entry `field_map` | 48 items + 48-entry `field_map` | yes (ignoring retrieval timestamps) |
| Market blocks | anchor/subscription/gmp/regime all MISSING | same | yes |
| Score / interval | 34.0 / 24–77 | 34.0 / 24–77 | yes |

Only the source-manifest and market-snapshot digests differ, and the file diffs show that the difference is confined to embedded timestamps (`as_of`, `captured_at`, `age_days`, retrieval instants) — no value moved.

**Conclusion: no new evaluation is warranted.** The existing `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601` is the correct reference, and this is now demonstrated by hash equality rather than argued from byte-identity alone. The two API-acceptance records created in temporary stores (`…111613Z-final-c8d148c1`, `…111642Z-final-66c25a0a`) are test artifacts of the transport check; they are not published as evaluation records and add no evidence beyond the equivalence table above.

A new evaluation becomes warranted only if one of the following lands: a qualified GMP observation, an official issue-term retrieval that replaces the third-party values, or an approved gate/basis decision that changes a canonical input.

---

## 5. Files added by this pass

| Path | Content |
|---|---|
| `docs/investigation/JIO-VALIDATION-AND-EVIDENCE-STATUS-2026-10-23.md` | This report |
| `docs/investigation/jio-validation-20261023/c1-gmp-retained-observation.json` | Retained Jio GMP row, why it is ineligible, minimum unblock evidence |
| `…/c2-knockout-evidence.json` | K1/K2/K5 rules, leaves, document quotes, required decisions |
| `…/c3-net-worth-basis.json` | Competing denominators, impacts, options |
| `…/c4-official-issue-terms.json` | Engine retrieval failure, independent publication check, share-count discrepancy |
| `…/api-acceptance.json` | Endpoint results, guard behaviour, evidence samples, equivalence table |
| `…/ci-failure-analysis.json` | Both CI runs, the failing test, runner OCR text, local comparison, diagnosis and open options |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` | Tracker entry |

No engine, test, schema, config, frontend or evidence file was modified in this pass.

---

## 6. Outstanding items by class

| Class | Item | Unblock condition |
|---|---|---|
| **Actionable now / decision needed** | Red CI: one deterministic OCR-fixture test fails on the runner only (§2.1). | Choose option A (realistic fixture with an identity block) or option B (space-tolerant OCR heading normalisation), then re-run the workflow. Neither was applied unilaterally. |
| **Actionable now** | Optional hardening: make `workbook_bytes()` deterministic (byte-stable ZIP members) so the historical flake cannot recur. | Separate authorization (touches a frozen-ish projection module). |
| **Awaiting external evidence/access** | Official issue terms | One successful `OfficialDiscoveryProvider` run on a host with exchange egress (recorded blocker: this sandbox's allowlist; TLS EOF at NSE/BSE). Would also settle the 19,75,25,934 vs 27,00,00,000 discrepancy. |
| **Awaiting external evidence/access** | Qualifying GMP observation | A28-scope qualification + capture contract + A28.1 binding + accepting verifier, per §3.1. |
| **Awaiting external evidence/access** | K1 going-concern | Either a scoped auditor confirmation (current-period report covering going concern) or the K1 rule below. |
| **Awaiting governance decision** | K1 negative rule | Approve/disapprove: does an unqualified SEBI-format examination report with no GC/EOM paragraph establish `going_concern_uncertainty = False`? |
| **Awaiting governance decision** | K2 definition and status | Entity scope (Company vs Promoter), nature (pending revision vs penalty vs debarment), and whether ED must be explicitly addressed. |
| **Awaiting governance decision** | K5 unquantified scope | Approve/disapprove treating a complete quantified note with no unquantified language as `False`. |
| **Awaiting governance decision** | Net-worth basis | Choose owners' equity (status quo) vs ICDR Net Worth vs storing both (§3.3). |
| **Blocked by environmental limitation** | Real browser acceptance | Needs a browser-capable environment; API-boundary acceptance passed, DOM criteria untested. |

---

## 7. Status table

| Completed this pass | Result |
|---|---|
| Remote lineage verification | branch `589e468`, ancestry and receipt confirmed via API + `merge-base` |
| Artifact/engine byte verification | 181 published engine/test/schema/frontend files re-hashed → 0 mismatches |
| A9 intactness | 5 A9 files byte-identical to parent; gate semantics unchanged |
| CI | automatic runs on both commits: **red** — 1670 tests, 1 failure each, the same OCR fixture test; every other step green (§2.1) |
| Local exact-commit suite | backend **1670 passed**; frontend 93/93 |
| API acceptance | 201 ingest, 200 on evaluation/evidence/activity reads; evidence quotes verified |
| Evidence investigation | C1–C4 completed; four specific gaps and their unblock conditions recorded |
| Evaluation decision | no re-run; hash-level equivalence to the published 34/100 demonstrated |

**Overall:** integration is verified and the published engine behaves as expected; the remaining blockers are external evidence, four governance decisions (plus one test-fixture/CI remedy), and one environmental limitation (browser session). CI is honestly red on one environment-dependent OCR fixture test that passes locally on the same commit — it is fail-closed, unrelated to Jio, and was not papered over. No safety gate was cleared or weakened to change any of that.

---

## Addendum — publication receipt (2026-10-23, verified remotely)

- **Commit:** `97b970e7df696e2fea90ca039bd24911b2dd0974`, parent `589e468e06b49c8066bbdb2e3f0729c4d09cd929`, 8 files (7 added, 1 modified), pushed to `arena/07f3439f-ipo-screening-engine`; branch head read back from the API equals that commit.
- **Remote ↔ local byte match:** this report (sha256 `55c7c211…`), the tracker (sha256 `46a86ee1…`) and `ci-failure-analysis.json` (sha256 `8e0d10c7…`) were re-downloaded from the commit and hashed locally: all three identical.
- **CI on this documentation-only commit:** run [39947292394](https://github.com/ramkivs/ipo-screening-engine/actions/runs/39947292394) — 1670 tests, **1 failure**, the same `test_image_only_official_notice_…` OCR test (1296 s); every other step and the clean-tree assertion green. Third consecutive reproduction of the same environment-dependent failure, and it confirms that no source file changed here: the only difference from `589e468` is documentation.
- **Nothing promoted:** `main` untouched, PR #6 untouched, no tag or release, no evaluation record added.
