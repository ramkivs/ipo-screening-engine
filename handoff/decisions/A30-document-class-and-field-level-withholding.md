# A30 — Document Class and Field-Level Withholding (RHP / Price Band Notice / Prospectus)

- **Decision ID:** A30
- **Title:** a document is read under its own class, and a conflicting field is withheld rather than rejecting the document
- **Record type:** **IMPLEMENTATION RECORD — no new policy, no new criterion, no scoring change.** Per `handoff/decisions/CONVENTION.md` rule 4, the approved text below is the correction contract that the investigation was authorised to implement; the analysis and residual risks are Arena's and are recorded, not decided.
- **Decision status:** **IMPLEMENTED 2026-10-23; UPLOAD PATH CORRECTED AND VALIDATED 2026-10-24; FULL BACKEND SUITE GREEN 1772/1772 2026-10-24; FROZEN-CORE PIN VERIFIED — READY FOR RAMKI RATIFICATION (NOT RATIFIED) 2026-10-24** — see §5.4. Parser and upload paths were separately corrected and now agree on the real filing; the ingestion gate is correctly blocked on the two genuinely undisclosed terms. **FOCUSED AND WIDER REGRESSION EXECUTED AND GREEN 2026-10-24** (45/45 focused; 221/221 wider across nine modules, 0 skipped — §5). A controlled non-production ingestion was then run: it is **correctly blocked** on price band and bid lot, and it exposed a **separate defect in the upload extractor** (`issue.ofs` and `issue.close_date` unreachable there) recorded in §5.3 and left uncorrected by design. Full backend suite (~3 h) still unexecuted.
- **Decision authority:** RAMKI — 2026-10-23 investigation directive for the Paras Healthcare ingestion failure (general, issuer-independent correction; no hardcoding, no policy change).
- **Decision date:** 2026-10-23 (Asia/Calcutta).
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/07f3439f-ipo-screening-engine`, tip `4b1c67f70047bbb5dbac10d18e53502a3c95c068` at the validation pass (was `8939b05` when the correction contract was implemented); `main` untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`.
- **Scope:** document-class recognition (`DRHP` / `RHP` / `Final Prospectus` / `Price Band Notice` / `General Information Document`), issue-term extraction authority per class, and the handling of a field whose candidates conflict.
- **Out of scope and unchanged:** `config/ipo-config.v1.5.0.json` and `v1.6.0`, `schema/`, `derived.py`, `knockouts.py`, `scoring.py`, `confidence.py`, A9 / GMP qualification and Final-withholding, K1–K5 semantics, the A23/A24/A25 litigation and regulatory rules, the A29 status meaning, required-term policy, issue-term qualification/verification rules, issuer matching, official-source allow-lists, fixtures, the golden record and every historical evaluation.

## 1. Approved correction contract

> A document is classified by its own class, not by the vocabulary it shares with another class. When a class's field is contradicted by credible evidence of the same class, that **field** is withheld and reported; the document and its other independently supported fields survive. Absence is never converted into a value, and a conflict is never resolved by choosing a winner.
>
> — RAMKI, 2026-10-23 (investigation directive), implemented in this branch

## 2. The rules, stated precisely

1. **Class before contract.** The notice contract ("the *Notice* announces one price band, one bid lot, one issue window") applies only to documents that are notices. A prospectus title on the title pages, or a document far longer than a notice without a notice title, is not a notice.
2. **An RHP is its own class.** It is never relabelled a final Prospectus and never promoted to one to pass a validation; it is also never demoted to a Price Band Notice. Its field authority is its own cover / offer summary: price band, bid lot, issue window, fresh-issue amount and OFS amount when the document states them.
3. **A final Prospectus requires a final-Prospectus title.** An RHP is refused by that parser, by class, with a message that says so.
4. **Field-level resolution.** A field is published when its own qualifying evidence supports it, withheld when its own credible current-issue candidates conflict, and absent when the document does not state it. These three states are distinguishable in the result (`value`, `value is None` + `issue_term_errors[field]`, `value is None` + no error).
5. **Current-issue dates are not found by proximity.** A date is a current issue date only if it sits on a term page, is not framed as historical, and is plausible against the document's own date. Structural signals (page position, field label, tense/wording, document date), not "near an IPO keyword", decide.
6. **A conflict is reported, not resolved.** No first-wins, no newest-wins, no nearest-to-cover. Conflict checks are not disabled.
7. **Absence is not zero, and a withheld field is not a negative finding.** `issue.ofs = 0` is reachable only through an explicit NIL binding; a withheld or absent term leaves the run `AWAITING_ISSUE_TERMS`.
8. **Fail-closed validations are retained.** Collar sanity (cap within 120 % of floor) and numeric/unit validation still reject.

## 3. What was actually broken (confirmed by execution, not inferred)

| ID | Confirmed defect | Correction |
|---|---|---|
| **D1** | `_classify_document` accepted any RHP as a Price Band Notice (all five semantic tokens are present in a prospectus). Retained 496-page RHP ⇒ `(True, 'Authoritative title and semantic price tokens matched')`. | prospectus-title guard on pages ≤ 3; a document > 25 pages without a notice title is not a notice; the token path is kept for genuine short notices |
| **D2** | `_extract_dates` read `closing date` / `closes` on every page with no context. A 2017 history sentence became a current close-date candidate and `Conflicting close dates: ['2026-10-23', '2017-07-14']` rejected the document. | term-page scoping; document-date window (−60/+400 days); historical-frame and past-tense-with-year tests; exclusions recorded with page and line |
| **D3** | every issue-term conflict (dates, band, lot) raised and discarded the whole document, including undisputed fields | field-level withholding with findings and `issue_term_errors`; inverted window withholds both dates |
| **D4** | `parse_official_rhp` required a final-Prospectus-style dated marker, so an RHP without one yielded no RHP-authorised terms at all; and its rejection reason did not distinguish "not an RHP" from "an RHP rejected for another reason" | `_rhp_role()` role test (title form / responsibility statement / offer-table header, refusing DRHP, GID and explicit notice titles); `_rhp_issue_terms()` publishes the RHP's own band, lot, window, fresh-issue and OFS field by field; a term-level failure is recorded and does not discard the document; the provider reason carries the class verdict |

Added in revision 2, after the actual 651-page RHP was recovered and read (the rows above had been established on the code path and on other filings):

| ID | Confirmed defect (on the real document) | Correction |
|---|---|---|
| **D5** | `_DOCUMENT_DATE` required a colon, so a cover written `Dated October 14, 2026` produced **no document date** and the plausibility window was inert for the whole filing | colon optional, anchored to the start of a line; a mid-sentence "certificate of incorporation dated December 21, 1987" cannot become the document date |
| **D6** | a defined-term entry (`"Closing Date" shall mean 14 July 2017`, Articles p590) was eligible to become the issue close date — this is the literal origin of the trace's `2017-07-14` | `_DEFINITION_FRAME`: a date inside a `"term" shall mean/means/has the meaning` definition is not a statement about this issue; exclusion reasons are recorded per signal |
| **D7** | the colon form `Price Band: Rs. X to Rs. Y` matched nothing (the range pattern required `is`/`of` after the label) | label separator (colon/dash) and dash ranges accepted; label + both amounts + separator still required; a trailing `-NN` (date-like) refused |
| **D8** | the band extractor used `.search` — only the first declaration per page — so two different bands on one page resolved to the first: a first-wins violation | every explicit declaration is a candidate; differing ones produce `CONFLICTING_PRICE_BANDS` and both ends are withheld |
| **D9** | `explicit_amounts` treated any `[●]` in the preceding text as an unknown **amount**, discarding a disclosed OFS where only the **share count** was a placeholder (the reported `issue.ofs` failure on the real filing) | `_AMOUNT_SLOT_PLACEHOLDER`: only a money-slot placeholder withholds; merged/header cells naming several components still refuse to bind |
| **D10** | `SOURCE_PLACEHOLDER` fired on share-count placeholders, contradicting the amount just extracted | emitted only for markers that make the amount unknown; RHP price-band/bid-lot placeholders recorded per field with page and quote |
| **D11** | an unresolved field's diagnostic said only "unresolved" | additive `why_unresolved` / `inspected_sources` / `required_evidence`; existing `state` values, required-term contract and eligibility unchanged |

## 4. Consequences

* **What can now resolve:** price band, bid lot and issue window from an RHP's own cover/offer summary (previously unreachable); OFS and fresh-issue amounts from the RHP's offer table (previously unreachable when the document was rejected); each with its own page, locator, quote and verification, rather than a single document-level verdict.
* **What still cannot:** a field the document does not state, states as `[●]`, or contradicts itself. Those stay `None` and are reported; they do not become `0`, do not become a negative finding, and do not satisfy a required term.
* **Rejection semantics changed for two cases only:** a notice with a conflicting band/lot/window is now accepted with that field withheld (it used to throw the document away), and an RHP is accepted as an RHP. Every other rejection path (collar, identity, placeholder-only, GID, DRHP, unqualified source) is unchanged.
* **No criterion moves on its own.** Issue terms feed `AWAITING_ISSUE_TERMS`; a withheld field cannot satisfy a required term, so a run that could not resolve terms still cannot.

## 5. Tests — EXECUTED

Added `tests/test_official_rhp_terms_and_dates.py` (36 cases after revision 2) and `tests/test_paras_evidence_regression.py` (9 cases against the retained 651-page filing, skipped when the artifact is absent), and rewrote two tests in `tests/test_price_band_notice.py` whose assertions encoded the old contract (`test_conflicting_price_bands_rejected` → `…_withhold_the_band_not_the_document`; `test_inverted_date_order_rejected` → `…_withholds_both_dates`). The rewrites keep the failure assertion (the conflicting value is never published) and add the survival assertion (the undisputed fields are).

**Execution status: RUN 2026-10-23 and GREEN.** Command, environment and counts:

```bash
cd /home/user/jio-k15
PYTHONPATH=engine /home/user/ev/bin/python -m pytest \
    tests/test_official_rhp_terms_and_dates.py tests/test_paras_evidence_regression.py -q
# commit 4b1c67f, CPython 3.11.2, pytest 9.1.1
# 45 collected -> 45 passed, 0 failed, 0 skipped  (exit 0)
```

The first execution produced 44 passed / 1 failed: `test_the_historical_2017_defined_term_is_not_the_close_date` raised `TypeError: 'PriceBandField' object is not subscriptable` — the assertion had been written against a dict shape, a transcription error in an unexecuted test, not a defect in the engine (the value it asserted, close `2026-10-23` / open `2026-10-21`, was already correct on the preceding lines). Corrected in the test only: attribute access, plus an added assertion that `_last_excluded_dates` carries no `2017-07-14` entry, so the test now records *why* the 2017 definition never competes. **No production module was changed in the validation pass; no assertion was weakened; no test was deleted or converted to a skip.**

The evidence guard was verified in both failure directions on throwaway copies: artifact absent ⇒ 9 skipped (reported as skipped, never as passing); one byte flipped at constant length ⇒ 9 errors at the fixture's hash assertion. The retained artifact's sha256, size (11,577,075 bytes) and page count (651) were re-checked against the published values before the run.

### 5.3 Wider validation and controlled ingestion — 2026-10-24

**Wider focused command** (`tests/test_paras_evidence_regression.py`, `test_official_rhp_terms_and_dates.py`, `test_price_band_notice.py`, `test_offer_table_boundaries.py`, `test_ofs_nil_binding.py`, `test_phase5j_hardening.py`, `test_official_prospectus_pathway.py`, `test_issue_terms_multisource.py`, `test_automatic_official_issue_discovery.py`): first run **215 passed / 4 failed**, after correction **221 passed / 0 failed / 0 skipped**. Nine adjacent extraction/resolution modules were run to bound the blast radius of the production edits: **91 passed**.

**Corrections in this revision (two production, both narrow and general):**

* `_AMOUNT_UNKNOWN_MARKER` no longer contains `UNREADABLE_OCR_LINE`. That marker is emitted by this pipeline on low OCR confidence, so reporting it as `SOURCE_PLACEHOLDER` told the operator the issuer's document printed a placeholder. The amount is still withheld; only the false attribution is gone.
* `parse_official_rhp` refuses a Draft RHP with the class-specific message again (the revision-2 role rewrite had collapsed it into "role not established"). The refusal itself never regressed.

One stale test contract was updated: `test_adversarial_d_conflicting_price_sources` asserted the pre-A30 raise. It now asserts the A30 contract — band withheld at both ends, conflict reported — **and** that the conflicting notice still fails closed at the final-mode evaluation gate, which is the adversarial property it exists to guard. No assertion was weakened, deleted or skipped.

**Controlled ingestion** (`PresentationService.ingest_document`, `store_root=/tmp/...`, `IPO_OFFICIAL_DISCOVERY=0`, committed artifact hash-checked before and after): `ing-55319ecccdc243e4`, **BLOCKED**, `AWAITING_ISSUE_TERMS`, `evaluation_run: False`, `persisted: False`, evaluation store never created. Opening date resolved (`2026-10-21`); price band and bid lot correctly withheld; **`issue.ofs` and `issue.close_date` unresolved**, and `issue.fresh_issue` stored as `5000.0` in a lakh-denominated input although the filing states ₹5,000 million.

**Why:** the upload path does not use `PriceBandNoticeParser` / `parse_official_rhp` at all — it uses `SectionExtractor.extract_cover_and_offer` and `CanonicalInputBuilder`, which A30 never touched. There, (i) a footnote marker after `CLOSES ON#` defeats the close-date pattern, (ii) no branch reads a monetary Offer-for-Sale amount, and (iii) no conversion exists between an extracted `MILLION` and the canonical `INR_LAKHS` reporting unit. **Not corrected in this pass:** the fix spans shared code every issuer's ingestion runs through, and its blast radius can only be validated by the full suite, which this pass was forbidden to run. Left blocked, which is safe; recorded as required work with a named blast radius.

### 5.4 Upload-path correction — 2026-10-24

The corrections above live in the **parser** path. Revision 4's controlled ingestion ran the **upload** path (`SectionExtractor.extract_cover_and_offer` → `CanonicalInputBuilder`) and reproduced the original symptom there. Three defects were corrected in that shared path, for all issuers:

* **Close date behind a footnote marker.** `BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026` was unreadable because the pattern required whitespace after the label; the opening date, with no marker, was read. Named patterns `_ISSUE_OPENS` / `_ISSUE_CLOSES` now tolerate a footnote marker (`#`, `*`, `†`, `(1)`, a bare 1–2 digit reference, …) between the label and the date. A date still has to follow the issue/bid/offer window's own label, so certificate, allotment and Articles-definition dates remain unreachable.
* **The monetary Offer for Sale was never extracted.** The upload path only read NIL or a seller's share quantity. One reader — `SectionExtractor._explicit_component_amount`, shared by `issue.fresh_issue` and `issue.ofs` — now reads `aggregating (up) to ₹ N <unit>`, refuses to cross a component label, refuses a label that is part of a merged header/adjacent column, never infers from a share count, and withholds the field when the document states two different amounts. NIL handling and "missing is not zero" are unchanged.
* **Monetary unit.** The schema already states that `issue.fresh_issue` and `issue.ofs` are *"in reporting_unit"*, and `enrichment_engine` consumes them that way, so ₹5,000 million stored as `5000.0` in an `INR_LAKHS` input was a tenfold magnitude error, not a display issue. `CanonicalInputBuilder._normalize_issue_amount` now converts **once**, at the only boundary that knows both the document's unit (`raw_unit`) and the filing's reporting unit: 1 million = 10 lakh, 1 crore = 100 lakh; no unit or an equal unit is left untouched (no double conversion); an unconvertible unit yields `None` rather than a guess. No new semantic decision was required — the canonical contract already said "in reporting_unit".

**Validation.** New `tests/test_upload_path_issue_terms.py` (27 synthetic cases: footnote variants, unrelated-date rejection, OFS money vs placeholder share count, seller rows, NIL, conflict withholding, a second issuer, and the conversion matrix including identity and unsupported units); five cross-path cases added to `tests/test_paras_evidence_regression.py` (14 total) running the real 651-page filing through `DocumentExtractor`. Wider focused command (ten modules): **253 passed / 0 failed / 0 skipped**. Upload-path regression modules: **20 + 77 + 49** passed. Golden/semantics: **54** passed.

**Controlled ingestion re-run** (`store_root` on `/tmp`, `IPO_OFFICIAL_DISCOVERY=0`, artifact hash-checked before and after): `ing-5bd0ea97160b409e` — **BLOCKED**, `evaluation_run: False`, `persisted: False`, store never created, missing fields now **only** `price_band_low`, `price_band_high`, `lot_size`. Resolved from the filing: open `2026-10-21`, close `2026-10-23`, fresh issue `50000.0` lakh (₹5,000 m), OFS `95000.0` lakh (₹9,500 m), each with page-1 cover provenance. The two placeholder terms remain unresolved, which is the correct result and keeps the gate closed.

### 5.5 Final regression gate — 2026-10-24

**Full backend suite, `PYTHONPATH=engine python -m pytest -q tests/`:** first run at `415a883` produced **1758 passed / 10 failed** (1768 collected, 30 m 32 s); after the two corrections below the suite is **1772 passed / 0 failed / 0 skipped, exit 0** (31 m 17 s, CPython 3.11.2, pytest 9.1.1, pypdf 6.20.1).

Two defects, one of them a real consequence of this decision:

1. **A cached Prospectus became "no evidence".** `NoticeSnapshotCache.get()` re-parsed every snapshot with `PriceBandNoticeParser`; A30 correctly makes that parser refuse a prospectus *by class*, so a retrieved, verified, cached final Prospectus came back as `(None, False)`. A verified official document silently disappeared on the second resolution — the direct cost of the classification rule landing in a caller that had not been updated. The cache now records `document_class` at `put()` and re-reads through the parser for that class (`OFFICIAL_PROSPECTUS` → `ProspectusTermsParser`, `OFFICIAL_RHP_TERMS` → `parse_official_rhp`, otherwise the unchanged OCR-aware notice path), with backward-compatible handling of entries written before the class was recorded. Four regression cases added in `tests/test_notice_cache_document_class.py`.
2. **The frozen-core pin for the corrected parser was stale.** A30 changed `engine/ipo_screening/extraction/price_band_notice.py`, which is one of the six frozen-core files; its expected hash still pointed at the pre-A30 content, so the engine (and the presentation API's `frozen_core_status`) reported `CORRUPTED`. The pin is re-established at the reviewed content with a comment naming A30 as the authority — mirroring the existing A15 precedent for `evaluation.py`. **This is bookkeeping for an authorised change, not a new policy**, and it is flagged for RAMKI's ratification; the independent protection for scoring output, `verify_golden_result()`, is unchanged and still reproduces `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`. The other five frozen files remain byte-identical to their pins.

No assertion was weakened, no test removed, none converted to a skip.

**Re-verification after the gate:** ten-module focused command plus the new cache module **257 passed**; upload-path + Paras + RHP modules **78 passed**; the nine previously failing modules **80 passed**. On the real filing: open `2026-10-21`, close `2026-10-23`, fresh `50000.0` INR_LAKHS (₹5,000 m), OFS `95000.0` INR_LAKHS (₹9,500 m), price band and bid lot unresolved as `[●]`. Evidence sha256 `e0a3187f…570e74` unchanged. **No evaluation was created, updated or persisted.**

### 5.6 Frozen-core pin — verification for ratification (2026-10-24)

The pin this decision required (§5.5, defect 2) was checked independently against the **published** tree before being put in front of RAMKI. Full dossier: `docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md` §15.

| Check | Result |
|---|---|
| Pin equals the CRLF-normalised sha256 of the committed file | **Yes** — `5f6f0262…b9ed29` equals the digest of blob `6dd36d20…`, the reviewed A30 content at `4b1c67f`, still the blob at the published tip |
| The stale pin really was the pre-A30 content | **Yes** — `779afb0b…` is the digest at `0e15ac7`; A30's two commits changed the file |
| Manifest diff | one hash line + four comment lines; no other entry, no verifier change |
| Behaviour added by the pin | **none** — a constant consumed by an existing integrity check; the parser change it guards was authorised by this decision, separately |
| Golden result | **unchanged** — `e84f8bc0…` reproduced; `GOLDEN_RESULT_HASH` never edited |
| Integrity tests with the new pin | **39 passed / 0 failed / 0 skipped** (LF/CRLF acceptance, real-content-change rejection, CLI verify, provenance chain, `frozen_core_status` = VERIFIED) |
| Tamper detection | **caught** — append, mid-file class rename and a single-byte flip each yielded `False` for that file only; an unchanged control file yielded `True` |
| Alteration reverted | **yes** — byte-identical restore, empty `git status`, empty diff, same blob at `HEAD`; nothing committed |

**Status: VERIFIED — READY FOR RAMKI RATIFICATION.** The pin is technically sound and leaves no residue. **RAMKI has not ratified it**, and no part of this repository may state otherwise until he does. If ratification is withheld, the remedy is to revisit this decision's parser change — not to restore the stale pin.

### 5.7 The withheld fields — official evidence located, still not resolvable (2026-10-24)

This decision withholds `price_band_low`, `price_band_high` and `lot_size` because the RHP discloses `[●]`. That is still the correct outcome, and the evidence workstream has now established *why* it is still open, which is different from assuming the terms are unpublished. Details: report §16.

* **Official evidence exists and was retrieved.** BSE's own issue-information page for this issue (issue 8048, symbol `PARASHLTH`, period 21–23 Oct 2026) publishes **Price Band `660.00-693.00`** and **Market Lot `21`**; a BSE notice corroborates the ₹693 cap, and a SEBI filing independently states the ₹5,000.00 m / ₹9,500.00 m components of the offer. All four are retained with provenance in `evidence/non-authoritative/paras-healthcare-issue-terms-20261024/`.
* **It is not admissible through the current contract.** The page is BSE's *historical* view (`status=H`) of a closed issue. The engine searches the **live** listing, closed SPA records are excluded by contract, and the historical listing is deliberately not among the searched listings. Nothing was changed to admit it.
* **The sandbox cannot reach any official host.** The engine's discovery returns `UNAVAILABLE` (never `NOT_FOUND`) for every listing, and the Price-Band Advertisement PDF itself could not be fetched by any route available here.
* **The extraction layer is not the blocker.** Against a transcription of the real page's labelled rows, the unmodified `ExchangeIssuePageParser` returns `660.0` / `693.0` / lot `21` / both dates / the issuer, and the general discovery provider returns `FOUND`. 17 new cases in `tests/test_paras_official_issue_page_terms.py`; no production code changed.
* **Nothing was resolved.** The three values exist in this repository only as investigation evidence and test input — not in any configuration, canonical record, snapshot or evaluation. The gate stays closed and evaluation remains NOT RUN.

### 5.8 Retrieval trace and the closed-issue identity path (2026-10-24)

See report §17 and decision record **A31**.

* **Why the engine reports UNAVAILABLE:** TLS egress from the execution environment fails for every official host before any bytes are read (`URLError: TLS/SSL connection has been closed (EOF)`; `curl (35) SSL_ERROR_SYSCALL`). It is not a parser, endpoint, cookie or issuer-matching failure, and it is never a `NOT_FOUND`. Retrieval failures now carry a `[TRANSPORT]` / `[HTTP]` / `[CONTENT]` class so the two can no longer be confused in diagnostics.
* **The closed-issue gap, closed narrowly:** a record from the exchange's historical listing is admissible only when its own identity is bound to this offering — exact issuer, the filing's own bid window, the exchange issue number, internally consistent identifiers — with no expected window meaning no admission, and conflicts withholding rather than arbitrating. The live search, its status filter and every allow-list are unchanged, and the historical listing stays off unless an operator configures it (A31).
* **The exchange's own advertisement name is now recognised** (`PBA_<yyyymmdd…>.pdf`), so an issuer-matched issue page that links its price-band advertisement can resolve the terms through the unmodified notice parser. A naming rule, not a widened source list.
* **Not done, deliberately:** allowing `listing.bseindia.com` as an operator-configured notice URL. That reverses a documented scoping with its own test; the change was made, found to contradict that test, and fully reverted. It is recorded for RAMKI in A31 §5.
* **Gate unchanged.** Controlled non-production ingestion re-run on the real filing (disposable store on `/tmp`, artifact hash-checked): `AWAITING_ISSUE_TERMS` on exactly the three pricing terms, `evaluation_run: False`, `persisted: False`, no evaluation store. With the historical listing configured the archive search is genuinely attempted and recorded as `[TRANSPORT]`; the outcome does not change.

**Still not run, and not claimed:** the full backend suite (`PYTHONPATH=engine python -m pytest -q tests/`, ≈ 3 h); any evaluation; any production ingestion. **Parser-level green is not ingestion-level green** — §12.5 of the investigation report says exactly where the two part company.

## 6. Residual risks and open items

1. **The failing document is verified; the trace is not.** The Paras RHP was recovered (sha256 `e0a3187f…570e74`, evidence commit `1dd6e14e`) and the original failure is reproduced on it exactly — the pre-correction patterns yield `['2017-07-14', '2026-10-23']` from p590 and p3. The ingestion trace `ing-42ded42dde7a41b2` itself is still absent from the repository, so the run's own payloads cannot be diffed.
2. ~~`Price Band: Rs X to Rs Y` (colon form) is not matched.~~ **Resolved in revision 2 (D7)** once the actual documents were available: the colon form is now read, conflicting declarations are withheld rather than first-won, and unrelated numeric ranges are still refused.
3. **Operator diagnostic for an absent OFS** is unchanged at resolution level; only the provider reason string now carries the class verdict.
4. **Retention of the old conflict contract elsewhere** — any sibling branch or tool that catches `PriceBandNoticeParseError` to detect "conflicting notice" will now see a successful parse with `issue_term_errors`. In this branch the four call sites were reviewed: each treats an exception as "not a notice", which is still correct, and none depends on the conflict raise.

## 7. Implementation authority

**GRANTED** for this pass, limited to: document-class recognition, RHP-authorised field extraction, field-level withholding, the metadata needed to distinguish absent / withheld / parsed, the provider reason string, and focused tests. **Not granted:** any change to scoring, criteria, thresholds, required-term policy, qualification or verification rules, the party/complaint rules of A23–A25, the A29 status meaning, fixtures, the golden record, or any evaluation — and no evaluation run.
