# Paras Healthcare ingestion failure — root cause and general correction

- **Record type:** engineering investigation and correction record. Not a new policy, not a scoring change, not an evaluation.
- **Investigation date:** 2026-10-23 (Asia/Calcutta).
- **Branch:** `arena/07f3439f-ipo-screening-engine` (working branch; `main` untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`).
- **Baseline this pass:** `8939b05be00a23d5733163cdb6a280b0578cfd10`.
- **Scope:** the extraction path that produced a rejected official document and an unresolved `issue.ofs`: Price Band Notice classification, current-issue date extraction, field-conflict handling, the RHP document class, and the OFS resolution chain. Corrections are issuer-independent.
- **Execution status (2026-10-24, revision 10 — operator host has egress):** the operator's own Windows host retrieved **14,287 bytes** from the BSE historical listing, so the `[TRANSPORT]` blocker is specific to this sandbox and the external dependency is cleared on the host that matters. That run exposed two defects, both corrected here: a URL pasted as a Markdown link with an HTML-escaped `&` was reported as a *policy violation* (now normalised before validation, with no scheme or host invented), and a retrieved page that carried no issue rows was indistinguishable from one that carried a different answer (the archive reader now reports `issue_rows` / `issuer_rows` / `bound_rows` / `rejections` and distinguishes a shell from a read listing). The resolution step is now a read-only CLI subcommand (`issue-terms`) instead of a pasted Python snippet — §19. Diagnosing a full-suite failure also found a **genuine determinism defect** in workbook serialisation (`dcterms:modified` and ZIP timestamps were rewritten at save, so the same workbook could produce two different hashes); it is fixed and regression-tested — §19.5. **No term is resolved, the gate stays closed and no evaluation exists.**
- **Execution status (2026-10-24, revision 9 — wiring + operational handoff):** the configuration-to-runtime chain was traced end to end and is now asserted by test; a misconfigured archive variable used to look exactly like a network outage and now surfaces as a configuration diagnostic (variable, position, reason — never the value) — §18. Full suite 1846/1846 on that pass's final code. **No evaluation.**
- **Execution status (2026-10-24, revision 8 — retrieval trace + issue-identity binding):** the `UNAVAILABLE` verdict was traced to **TLS egress blocking** from this sandbox (all six official listings fail before any content is read), not to a parser, endpoint or matching defect; failures now carry a `[TRANSPORT]`/`[HTTP]`/`[CONTENT]` class. A **closed-issue record can now be used only through an identity-bound path** (A31: exact issuer + the filing's own bid window + the exchange issue number + internally consistent identifiers; no window ⇒ no admission; conflicts withhold), leaving the live search and every allow-list untouched — §17. Two further findings are recorded rather than silently absorbed: the exchange's own `PBA_` advertisement naming was not recognised by the attachment filter (now recognised), and the configured-URL allow-list deliberately excludes `listing.bseindia.com` (a change was attempted, contradicted an existing safeguard's test, and was **reverted**; it is RAMKI's decision, A31 §5). **The three terms remain UNRESOLVED, the gate stays closed, and no evaluation exists.**
- **Execution status (2026-10-24, revision 7 — ratification evidence + official-source discovery):** the frozen-core re-pin is independently verified against the published bytes and recorded **VERIFIED — READY FOR RAMKI RATIFICATION** (**not ratified**) — §15. Issuer-matched **official** sources for the three `[●]` terms were located and retained with provenance (BSE issue page: price band `660.00-693.00`, market lot `21`; SEBI filing corroborating ₹5,000.00 m / ₹9,500.00 m) — but they are **not admissible through the current contract**: the carrying page is BSE's *historical* view of a closed issue, the engine searches only the live listing, and this sandbox cannot reach any official host at all. **The terms remain unresolved and the gate stays closed**; nothing was written into the engine, a store or an evaluation — §16.
- **Execution status (2026-10-24, revision 6 — final regression gate):** the **full backend suite was executed** against the corrected tree: **1772 collected / 1772 passed / 0 failed / 0 skipped** (31 m 17 s, exit 0). Ten failures in the first full run were diagnosed: nine were one stale frozen-core pin for the A30-corrected parser, and one was a genuine A30 regression in the snapshot cache that turned a *verified cached Prospectus* into "no evidence". Both are corrected and documented in **§14**; the golden result still reproduces `e84f8bc0…` exactly. Evaluation remains NOT RUN and no evaluation was created.
- **Execution status (2026-10-24, revision 5):** the **upload path** — the extractor `PresentationService.ingest_document` actually uses — is corrected for all issuers: the closed issue window behind a footnote marker, the disclosed monetary Offer for Sale, and the monetary unit of both issue components. A controlled non-production re-ingestion of the retained RHP now resolves the issuer, opening date, closing date, fresh issue and OFS, and is **correctly blocked** on price band and bid lot alone. No evaluation was created; nothing was persisted. See **§13**. The **full backend suite (~3 h) was still NOT run**.
- **Execution status (2026-10-24, revision 4):** the **wider focused suites** were executed (221 passed / 0 failed / 0 skipped across nine modules) and a **controlled non-production ingestion** was run against the retained RHP. The ingestion is **correctly blocked** on price band and bid lot, but it **also** leaves `issue.ofs` and `issue.close_date` unresolved — a defect in the *upload* extraction path (`sections.py`) that the A30 corrections never reached. It is diagnosed and documented in **§12**, not corrected in this pass. No evaluation was created, no durable state changed. The **full backend suite (~3 h) was still NOT run**.
- **Execution status (2026-10-23, revision 3):** the two focused regression modules were **executed and passed on 2026-10-23** (45 collected / 45 passed / 0 skipped, commit `4b1c67f`) — see **§11.8**, which records the command, the one test-side defect that was fixed, and the checks performed. The **full backend suite (~3 h) was NOT run**, and **no ingestion, evaluation or scored artifact** was produced or modified. Statements in §§1–10 that predate the document remain as written; where they say "not executed", §11.8 supersedes them for these two modules only.
- **Revision 10 (2026-10-24):** operator-host egress confirmed (14,287 bytes from the BSE historical listing); pasted-URL normalisation before allow-list validation; row-count diagnostics that separate a shell response from a read listing with no matching issuer; a read-only `issue-terms` CLI replacing the pasted Python handoff; and a determinism defect in workbook byte serialisation found by the full suite, fixed and regression-tested. No evaluation.
- **Revision 9 (2026-10-24):** configuration-to-runtime wiring trace and hardening — the archive variable is proven to reach the provider through `create_app`, an ingestion run shows the filing's own bid window reaching the resolver, and unusable entries surface as configuration diagnostics rather than as outages. Full suite green on final code. No evaluation.
- **Revision 8 (2026-10-24):** end-to-end retrieval trace (transport vs absence), issue-identity binding for closed exchange records (A31, 32 new cases), exchange advertisement-name recognition, a reverted allow-list experiment, and a controlled non-production ingestion confirming the gate. No evaluation.
- **Revision 7 (2026-10-24):** frozen-core ratification dossier (independent hash, manifest-diff, golden-result, integrity and tamper checks, all reverted) and the official price-band / lot-size evidence workstream (4 official sources retained, 2 not retrieved, contract and transport blockers stated, 17 new focused cases). No code change to extraction or discovery.
- **Revision 6 (2026-10-24):** final regression gate — full suite run twice (first run 10 failed, final run 1772/1772), two corrections (snapshot-cache document class; frozen-core pin re-established with authority recorded), plus four cache regression cases.
- **Revision 5 (2026-10-24):** upload-path correction pass — the three defects found by revision 4's ingestion are corrected in the shared extractor and builder, with 27 new upload-path cases and five cross-path cases on the real filing.
- **Revision 4 (2026-10-24):** wider validation and controlled ingestion pass — four failures across the wider suites diagnosed, two narrow production corrections made (unreadable-OCR marker, Draft-RHP class message), one stale test contract updated, three new regression cases; then a controlled non-production ingestion which surfaced the upload-path gap recorded in **§12**.
- **Revision 3 (2026-10-23):** controlled validation pass — the focused modules were run, one test-side defect corrected, and the behavioural checks A–F executed against the retained artifact (§11.8). No production code was changed in this revision.
- **Revision 2 (2026-10-23):** the actual Paras RHP was recovered from the evidence branch and verified. §1's "the document is not present" limitation is **superseded**; the document-specific findings are in **§11**, which distinguishes them from the earlier synthetic reproduction. Sections 1–10 are left as written (they record what was known before the document was available) with this pointer.

---

## 1. What the failing trace implies, and what was actually reproduced

The Paras filing PDF and trace `ing-42ded42dde7a41b2` are **not present** in this workspace, in any git ref, or in the GitHub code search. The failure was therefore reconstructed from the code path the trace names, and reproduced on retained real filings plus a synthetic two-date cover.

**Reproduced from the code, exactly:**

| Observation | Reproduction |
|---|---|
| A real 496-page RHP is classified as a *Price Band Notice* | `handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf` → `_classify_document → (True, 'Authoritative title and semantic price tokens matched')` |
| Notice-only "one band, one lot, one window" rules then abort a valid RHP | same filing → `PriceBandNoticeParseError` on conflicting price bands `[(20.0,24.0),(32.77,34.14),(77.0,82.0)]`, and independently on lot sizes `[3200,1600]` |
| A historical sentence becomes a *current* close-date candidate, and two candidates reject the document | synthetic cover (`ISSUE CLOSES ON: OCTOBER 23, 2026`) + history sentence (`the Issue Closing Date was July 14, 2017`) → `PriceBandNoticeParseError: Conflicting close dates: ['2026-10-23', '2017-07-14']` — the same shape as the trace |

The synthetic reproduction is legitimate because it exercises the shipped code, not a hypothesis: no issuer name, CIN, date, URL or expected value from the Paras filing is used anywhere in production code or in the tests added by this pass.

---

## 2. Root causes

### RC-1 — Document-class conflation (a notice is not a prospectus)

`PriceBandNoticeParser._classify_document` accepted a document when it had a notice *title marker* **or** four of five semantic tokens (`cap price`, `floor price`, `bid lot`, `price band`, `equity shares`). Every RHP and final Prospectus contains all five, because a prospectus defines those terms. The notice parser was therefore entered for a multi-hundred-page filing, and the notice's contract — *the Notice announces one price band, one bid lot, one issue window* — was applied to a document whose other pages legitimately mention other bands, other lots and other dates.

This is the defect that converts harmless historical content into document-level rejection: under the notice contract, a second value is a contradiction.

### RC-2 — Context-free date capture

`_extract_dates` ran label patterns — `… closing date:`, `… closes …`, and a bare `closing date:` — over **every page**, with an unanchored date normaliser and no notion of what the document is or when it was written. Any sentence in a history section, an "our previous public issue" narrative, or a worked example matched. Two distinct normalised values then raised `PriceBandNoticeParseError`.

Nothing in the old code could distinguish:

* a date on the cover from a date on page 420;
* an issue-window field from a narrative sentence about a 2017 listing;
* a plausible issue date from a date that is nine years outside the document's own date.

### RC-3 — A field conflict escalated to document rejection

All three issue-term extractors raised on disagreement: conflicting dates, conflicting price bands, conflicting lot sizes. A document was therefore either fully accepted or fully discarded, and an unrelated field's conflict destroyed fields nothing disputed. This is the mechanism by which a valid, issuer-matched, official RHP produced *no* usable issue terms — including the OFS amount it did disclose.

### RC-4 — OFS was a *consequence*, not an independent defect

The OFS chain was traced end to end (`issue_terms.py` resolver → `OfficialDiscoveryProvider._issue_attachments` → `parse_official_rhp` → `explicit_amounts` → `_find_ofs_nil`). **No path anywhere infers `issue.ofs = 0` from absence.** The chain is:

`ofs` is required (`REQUIRED_ISSUE_TERMS = PRICING_TERMS + ("ofs",)`); its only sources are an official notice/RHP/exchange page carrying an explicit OFS amount, an explicit governed NIL, or an exchange page field. In the failing run the RHP was rejected at document level before any of its offer terms were reached, so `ofs` could not be filled — and the rejection was reported to the operator as a generic "attachment rejected", not as "this is an RHP whose fields conflicted".

So the OFS gap was: **(document rejection) primarily, with (parser/classification defect) as the cause, plus (genuine non-disclosure or placeholder) as the residual possibility per document.** It was **not** an "extraction failure that dropped a stated value", and it was **not** a missing→zero substitution.

---

## 3. Corrections

All corrections are general: they depend on document structure, field labels, page position, the document's own date and the wording that frames a date — never on an issuer.

### 3.1 Classification: explicit document classes (`price_band_notice.py`)

* `_classify_document(text, pages=None)` now rejects a document whose title pages (pages ≤ 3) establish a **prospectus** (`Draft Red Herring Prospectus`, `Red Herring Prospectus`, `Prospectus Dated:`) — an explicit class decision, not token arithmetic.
* A document longer than `_NOTICE_MAX_PAGES = 25` without a notice title is not a notice, even if it uses the notice's vocabulary. A notice is a short, single-purpose announcement; this catches filings whose cover title is graphical.
* The token path is retained for genuine short notices (verified: a 1-page untitled notice still classifies by tokens).

### 3.2 Dates: term scoping, document-date window, historical framing

`_extract_dates` now:

1. reads **term pages only** — pages ≤ 5, or pages that carry explicit issue-term labels (`_ISSUE_TERM_PAGE`);
2. computes the **document's own date** from its title pages (`Dated:`) and rejects candidates outside `−60 / +400` days (`_DATE_WINDOW_DAYS_BEFORE/AFTER`);
3. rejects a candidate whose enclosing line is **framed as historical** (`previous`, `earlier`, `erstwhile`, `initial public offering in …`, `has been listed` …) or states the date in the **past tense with a year** (`the Issue Closing Date was July 14, 2017`);
4. records every exclusion with field, value, page and the exact line (`HISTORICAL_DATES_EXCLUDED`, one entry per page even when two label patterns match the same sentence);
5. **withholds the field** on a genuine current-issue conflict instead of raising (`CONFLICTING_OPEN_DATES` / `CONFLICTING_CLOSE_DATES`);
6. withholds **both** window fields when the pair is inverted (`INVALID_ISSUE_DATE_ORDER`).

Forbidden behaviours are not implemented: conflict checks are not disabled, no first-wins, no newest-wins, no nearest-to-cover guess. Two credible current-issue candidates leave the field `None` and reported.

### 3.3 Field-level withholding (`price_band_notice.py`)

`_extract_price_band` / `_extract_lot_size` no longer raise on multiple candidates. They return `None` for that field and append `CONFLICTING_PRICE_BANDS` / `CONFLICTING_LOT_SIZES`. Every withheld field is published in `metadata['issue_term_errors']` (field → reason), so a *withheld* field is distinguishable from a field the document never stated, and from a field that was parsed. Excluded historical dates are published in `metadata['historical_dates_excluded']`.

Unchanged: the SEBI ICDR collar validation (`PriceCollarValidationError` still fails closed for a cap > 120 % of floor), numeric sanity, and every acceptance rule for a genuine notice.

### 3.4 RHP document class with its own field authority (`official_offer_amounts.py`)

`parse_official_rhp` previously required a **dated final-Prospectus-style marker** (`Red Herring Prospectus Dated:`) or a responsibility-statement+table combination, and did nothing in between: it did not read the RHP's own terms.

Now:

* `_rhp_role()` establishes the class from any of — an RHP **title form** (line-initial `Red Herring Prospectus`, or followed by `Dated:`), the issuer responsibility statement, or the complete offer-table header. A mid-sentence reference ("the Red Herring Prospectus dated … has been filed") is not a title; an explicit notice title (`Price Band Notice`, `Pre-bid advertisement`, `Notice to Investors`) is not an RHP; `Draft Red Herring Prospectus` and `General Information Document` are refused.
* **No final-Prospectus marker is required** — an RHP is not a final prospectus, and requiring the marker is what lost RHP-authorised fields.
* Identity (CIN + name) is required and read from pages ≤ 5 with a whole-document fallback, so a graphical cover does not lose identity; issuer matching upstream is unchanged.
* RHP-authorised terms are attached **field by field** by `_rhp_issue_terms()`: price band, bid lot and issue window from the cover/offer-summary pages (band and lot from pages ≤ 5; the window through the same term-page and historical-date rules), plus the fresh-issue and OFS amounts and explicit NIL through the existing `explicit_amounts` / `_find_ofs_nil` chain.
* A term-level failure inside `_rhp_issue_terms` is recorded (`issue_term_errors['rhp_terms']`) and **never discards** a document whose identity and offer amounts are good.
* `document_class` stays `OFFICIAL_RHP_TERMS`; the result is never relabelled `OFFICIAL_PROSPECTUS` and never routed through the notice parser's classifier as if it were a notice.

`prospectus_terms.py`: the rejection now names the class — *"document is a Red Herring Prospectus, not a final Prospectus: it establishes RHP-authorized terms … and cannot establish final-Prospectus terms"* — instead of the old *"no 'Prospectus Dated:' title marker found"*, which described the missing test rather than the document. The final-Prospectus parser still refuses RHPs/DRHPs (no promotion to bypass validation).

`issue_terms.py`: `OfficialDiscoveryProvider._issue_attachments` now carries the RHP-class verdict into its rejection reason (`"attachment rejected; RHP class: <reason>; …"`), so "not an RHP" and "an RHP rejected for another reason" are distinguishable in the provider report.

---

## 4. Source-to-field path, before and after

| Field | Before (failing path) | After |
|---|---|---|
| document class | token score ⇒ **Price Band Notice** for a 496-page RHP | prospectus title ⇒ not a notice; RHP role established by title/responsibility statement/offer-table header ⇒ **`OFFICIAL_RHP_TERMS`** |
| `quote`/`ofs` | RHP rejected before its offer table was read ⇒ `issue.ofs` empty, provider reason generic | RHP terms read field by field; an explicit OFS amount or governed NIL is published with page, locator, quote and `VERIFIED`; a placeholder or absent OFS leaves the field `None` with a diagnostic |
| `open_date` / `close_date` | any page, any sentence; two values ⇒ document rejected | term pages only, historical framing and document-date window applied; conflict ⇒ field withheld and reported |
| `price_band_low/high`, `lot_size` | one unique pair/lot required document-wide; conflict ⇒ document rejected | cover window only on the RHP path; conflict ⇒ that field withheld, others published |
| `fresh_issue` | RHP rejected ⇒ never reached | offer table / offer summary, `[●]` ⇒ `SOURCE_PLACEHOLDER` and `None` |

### Read-only probe results (retained filings, not tests)

| Filing | Result after correction |
|---|---|
| `R.K Fashion accessories.pdf` (496 pp RHP) | class `OFFICIAL_RHP_TERMS` via `RHP title`; `open_date 2026-10-05`, `close_date 2026-10-07`, `ofs_amount 0.0` from an explicit NIL, `fresh_issue None` (cover states `₹ [●]`) — previously the whole document was rejected on band/lot conflicts |
| `vishal nirmiti.pdf` (551 pp RHP) | class `OFFICIAL_RHP_TERMS`; `open_date 2026-09-30`, `close_date 2026-10-05` — **unchanged** from the pre-correction value |
| `Moneyview_Final_Prospectus_Full.pdf` (537 pp) | not a notice (prospectus title); unchanged path |
| `fixtures/filings/complete_sample_rhp.pdf`, `class_e_modern_complex_rhp.pdf` | no longer classifiable as notices (both carry an RHP title) |
| `fixtures/notices/clean_notice.txt`, `alternative_notice.txt` | unchanged: full band, lot and window, no findings |
| `fixtures/notices/conflicting_notice.txt` | band withheld with `CONFLICTING_PRICE_BANDS`; lot and window still published |
| `fixtures/notices/invalid_collar_notice.txt` | still fails closed (collar spread) |

---

## 5. Which fields resolve, and which correctly stay unresolved

**Resolve** when a qualifying document states them: price band and bid lot (cover/offer table, explicit currency, no confusable glyphs); issue open/close date (term page, non-historical, inside the document-date window); fresh issue and OFS amount (explicit `aggregating up to ₹ N lakhs/millions/crores` outside reservation/face-value/subtotal runs); explicit OFS NIL through the governed two-column binding; issuer identity (name + CIN) from the document itself.

**Stay unresolved — deliberately:**

* OFS when the document states `[●]` (placeholder, `SOURCE_PLACEHOLDER`), omits it, or contradicts itself (`issue_term_errors['ofs']`) — the field is `None` and the term remains required, so the run stays `AWAITING_ISSUE_TERMS`. **`issue.ofs` is never set to 0 from absence; an explicit NIL is the only zero.**
* The issue window when two credible current-issue dates conflict, or when the pair is inverted.
* The price band when the document's own current band candidates conflict — both ends are withheld so no half-verified collar is published.
* Any date the document frames as historical or that falls outside its own date window: excluded and reported, never promoted.

---

## 6. Tests added or updated — **EXECUTED (revision 3)**

Execution status: these cases now form part of `tests/test_official_rhp_terms_and_dates.py`, which was **executed green** (36/36) on 2026-10-23 — see §11.8 for the command, environment and counts. The full backend suite (~3 h) remains unexecuted.

**Added** — `tests/test_official_rhp_terms_and_dates.py` (21 cases):

* historical "closing date" sentence does not become the current close date; exclusion carries page and value; one report per page;
* historical wording works even two days from the document date (inside the window);
* two credible current close dates genuinely conflict ⇒ field withheld, open date untouched;
* unlabelled narrative history deep in a filing yields no candidates;
* RHP is not classified as a Price Band Notice; the notice parser rejects it **by class**, naming the prospectus title; a genuine notice still classifies; short untitled notice still classifies by tokens; long untitled document is not a notice;
* one conflicting field does not discard the others (lot + window survive a band conflict);
* OFS: `[●]` ⇒ `None` + `SOURCE_PLACEHOLDER` diagnostics for OFS *and* fresh issue; governed explicit NIL ⇒ `0.0` `INR_LAKHS`; explicit positive OFS ⇒ value, unit, page and quote;
* RHP cover terms extracted field by field with per-field provenance (`page`, `quote`, `DETERMINISTIC_PDF`, `VERIFIED`);
* RHP class boundaries: GID refused, DRHP refused, identity-less document refused, missing field stays `None` (not defaulted), historical date excluded inside the RHP path;
* RHP keeps its own `document_class` and `SRC-OFFICIAL-RHP-…` provenance and never adopts a requested issuer name.

**Updated** — `tests/test_price_band_notice.py`:

* `test_conflicting_price_bands_rejected` → `test_conflicting_price_bands_withhold_the_band_not_the_document` (the old assertion encoded the defect: it required the document to be discarded);
* `test_inverted_date_order_rejected` → `test_inverted_date_order_withholds_both_dates` (same: the raise was the old contract; neither date is published now).

Both rewrites keep the *failure* assertion (the conflicting value is never published) and add the *survival* assertion (the undisputed fields are), so no assertion was weakened.

**Focused commands (for the deferred pass):**

```bash
cd /home/user/jio-k15
PYTHONPATH=engine python -m pytest -q tests/test_official_rhp_terms_and_dates.py \
    tests/test_price_band_notice.py tests/test_phase5j_hardening.py \
    tests/test_official_prospectus_pathway.py tests/test_enrichment_engine.py \
    tests/test_offer_table_boundaries.py tests/test_vishal_historical_reconciliation.py
```

**Full suite (for the deferred pass):**

```bash
cd /home/user/jio-k15
PYTHONPATH=engine python -m pytest -q tests/
```

---

## 7. Verification actually performed (and what it is not)

* the Price Band Notice parser, the RHP extractor and the notice fixtures were applied **read-only** to the retained PDFs listed in §4 and to synthetic documents;
* the synthetic two-date reproduction in §1 was executed against the corrected module and now yields `close_date 2026-10-23` with `HISTORICAL_DATES_EXCLUDED`, and `close_date None` + `CONFLICTING_CLOSE_DATES` for a genuine current-issue conflict;
* the inverted pair now yields `INVALID_ISSUE_DATE_ORDER` with both dates withheld instead of an exception;
* `py_compile` was run on every changed module and test file.

**No pytest, no ingestion, no evaluation, no scoring artifact.** No historical evaluation (including the Jio records) was opened, modified or re-created.

---

## 8. Boundaries preserved

* No issuer-specific constant: no Paras name, CIN, date, URL, term or expected value appears in production code or in the general tests.
* No missing→zero: absence of OFS stays `None`; only an explicit NIL binds to `0`.
* No relaxation of issuer matching, official-source qualification, or the required-term policy; `AWAITING_ISSUE_TERMS` still results from a missing required term.
* No third-party→official promotion, no scoring weight, criterion semantic, threshold, gate or confidence change; no config/schema change; no fixture or golden-record change; no historical evaluation touched; no new evaluation; nothing merged to `main`; unrelated branch work preserved.

---

## 9. Remaining limitations and open questions

1. **The Paras document itself is not in this repository.** The defect is demonstrated on the code path and reproduced on other filings; it is **not** confirmed against the original trace input. No claim is made about what the Paras RHP specifically disclosed.
2. **`Price Band: Rs X to Rs Y` (colon form) is not matched** by `_extract_price_band`'s range pattern; only `price band of/is Rs X to Rs Y` and the floor/cap forms are. Found while building the tests and **deliberately not changed** in this pass: widening it would change which notices yield one band vs. a conflict, and that cannot be regression-checked inside this pass. Recorded as a known extraction gap (it explains why a cover whose only band statement is the colon form leaves the band `None`).
3. **R.K Fashion's band and lot remain `None`** because its cover states `₹ [●]` / `[●]` placeholders; the three conflicting pairs found document-wide are historical and are no longer read as current terms. This is the intended outcome, not a residual defect, but it means the probe does not demonstrate a *positive* band from that filing.
4. **Provider reason strings** now carry the RHP-class verdict, but the resolver's operator-facing summary for a genuinely absent OFS is unchanged (it still reports the term as unresolved rather than diagnosing "the document says `[●]`"). A resolution-level diagnostic is a possible follow-up, not implemented here.
5. **`issue.ofs` resolution for the Paras run** remains unproven: whether the document disclosed an OFS amount, an explicit NIL, a placeholder, or nothing at all is unknowable without the document. The correction makes each of those states *representable and distinguishable*; it does not assert which one applies.
6. **Regression execution is pending** — the corrections are statically inspected and probe-verified only.

---

## 10. Change inventory

| File | Change |
|---|---|
| `engine/ipo_screening/extraction/price_band_notice.py` | prospectus-title guard and notice length bound; term-page/document-date/historical date rules; field-level withholding for band, lot and window; `issue_term_errors` and `historical_dates_excluded` metadata; `_last_excluded_dates` |
| `engine/ipo_screening/extraction/official_offer_amounts.py` | `_rhp_role()` document class; `_rhp_issue_terms()` field-by-field RHP terms; identity scope widened to pages ≤ 5 with unchanged matching |
| `engine/ipo_screening/extraction/prospectus_terms.py` | RHP-class rejection message |
| `engine/ipo_screening/issue_terms.py` | RHP-class verdict carried into the attachment rejection reason |
| `tests/test_price_band_notice.py` | two defective-contract tests rewritten to the withhold-don't-discard contract |
| `tests/test_official_rhp_terms_and_dates.py` | **new** — 21 cases across dates, classification, partial resolution, OFS states, RHP boundaries and provenance |
| `handoff/decisions/A30-document-class-and-field-level-withholding.md` | **new** — implementation record for the contract change (no new policy) |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` | tracker entry for this pass |

---

# 11. Revision 2 — the actual document, verified (2026-10-23)

Everything in this section was produced from the **real Paras Healthcare RHP**, not from a synthetic reproduction. Where a statement is still general (synthetic or structural), it says so.

## 11.1 Evidence recovery and integrity

| Item | Value |
|---|---|
| Branch | `evidence/jio-score-33-recovery-20261023` |
| Commit | `1dd6e14e7fa50a677beefba9ca7d0d1a7b322c58` |
| Path at that commit | `docs/investigations/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf` |
| Blob | `f62a80f5e69702885da59462464023ca300ade0d` |
| Bytes | 11,577,075 |
| SHA-256 | `e0a3187fe18d1c12f88f29170291972714cf15be7946e8a7f4a7d8c914570e74` — **matches the expected value exactly** |
| Pages | 651 |
| PDF metadata | `Producer: Microsoft® Word for Microsoft 365`, `Author: AZB & Partners`, `CreationDate 2026-10-14T09:36:26+05:30`, `ModDate 2026-10-14T12:15:32+05:30` |
| Retained at | `evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf` (original filename and bytes preserved) |

The bytes are asserted in `tests/test_paras_evidence_regression.py`, so a substituted or truncated artifact fails loudly. The document is **investigation evidence only**; it is not registered as official evaluation evidence, and no evaluation was produced.

**Trace provenance.** The ingestion trace `ing-42ded42dde7a41b2` is **not in the repository** — it is not in the evidence branch, not in any local ref and not in a GitHub code search. Only what was supplied in the investigation context is used: the trace identifier, the two competing close dates (`2026-10-23`, `2017-07-14`), the document-rejection reasons (`Prospectus classification failed: no 'Prospectus Dated:' title marker found`; `Price band notice parsing failed: the parser found conflicting close dates`; `RHP terms not established (no recognised RHP cover…)`), `blockedFields: ['fresh_issue']` with `issue.ofs` unresolved, and the discovered official documents list. No missing trace field was reconstructed or invented.

## 11.2 What the document is

`RED HERRING PROSPECTUS — Dated October 14, 2026` (title on **page 3**, not page 1), 100% Book Building Offer, 651 pages, CIN `U85110HR1987PLC035823`.

Current implementation:

| Question | Actual result |
|---|---|
| Classified as a Price Band Notice? | **No.** `_classify_document` → `(False, 'document title establishes a prospectus (Red Herring Prospectus), not a Price Band Notice')`, both on pages 1–5 and on the full 651-page text. `PriceBandNoticeParser.parse_from_file` raises `PriceBandNoticeClassificationError`. |
| Classified as an RHP? | **Yes** — `parse_official_rhp` → `document_class = OFFICIAL_RHP_TERMS`, role basis `RHP title`, issuer `PARAS HEALTHCARE LIMITED`, CIN from the document. |
| Treated as a final Prospectus? | **No.** `ProspectusTermsParser` refuses it by class ("… is a Red Herring Prospectus / DRHP, not a final Prospectus"). It is not relabelled to pass a validation. |

This is exactly the conflation RC-1 described, now measured on the real filing: before the correction, `_classify_document` returned `True` for any RHP (all five semantic tokens are present in a prospectus), and the notice contract then rejected it.

## 11.3 The dates, and where they come from

| Candidate | Page | Source text (verbatim) | Verdict |
|---|---|---|---|
| open `2026-10-21` | 3 | `BID/OFFER OPENS ON WEDNESDAY OCTOBER 21, 2026 BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026` | **current issue open date** — published, page 3, quote, `VERIFIED` |
| close `2026-10-23` | 3 | `BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026` | **current issue close date** — published, page 3, quote, `VERIFIED` |
| close `2026-10-23` | 535 | `BID/OFFER CLOSES ON FRIDAY, OCTOBER 23, 2026(2)` | same value — corroborates, no conflict |
| close `2017-07-14` | 590 | `"Closing Date" shall mean 14 July 2017;` (Articles of Association, definitions) | **not a candidate**: page 590 is not an issue-term page |

**Where the historical date comes from — the precise mechanism, reproduced.** Applying the *pre-correction* close-date patterns to the real document yields exactly three candidates:

```
p3   → 2026-10-23   'BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026'
p535 → 2026-10-23   'BID/OFFER CLOSES ON FRIDAY, OCTOBER 23, 2026(2)'
p590 → 2017-07-14   'Closing Date" shall mean 14 July 2017;'
unique close dates: ['2017-07-14', '2026-10-23']
```

That is precisely the pair in the reported trace, produced by an unanchored `closing\s+date\s*[:\-]?\s*([^\n\r]+)` pattern that treated a **defined term in the Articles** as the issue's closing date, and then raised on disagreement. The 2017 date is a Series A CCPS allotment/transfer date (also at pp. 66, 110, 113, 115), never an issue date.

**Actual current behaviour** (read-only probe): the issue window resolves to `2026-10-21` / `2026-10-23` with no findings, over the whole 651 pages and over the cover alone. The 2017 date never enters the candidate set: the Articles page carries no issue-term label, so the term-page rule excludes it structurally. The defined-term guard and the document-date window are the defence if such a line ever appears on a term page (see 11.5 and the synthetic tests).

## 11.4 `issue.ofs` — the disclosure, and what happened to it

The RHP **does disclose the Offer for Sale amount**, three ways:

| Page | Text |
|---|---|
| 1 | `DETAILS OF THE OFFER TO THE PUBLIC … Offer for Sale Size … Up to [●] Equity Shares of face value of ₹1 each aggregating up to ₹ 9,500.00 million` |
| 1 | per seller: Dr. Dharminder Kumar Nagar `₹ 3,000.00 million`, Commelina Ltd `₹ 6,500.00 million` (sum = ₹9,500.00 million) |
| 3 | `… AND AN OFFER FOR SALE OF UP TO [●] EQUITY SHARES OF FACE VALUE OF ₹ 1 EACH ("OFFERED SHARES") AGGREGATING UP TO ₹ 9,500.00 MILLION …` |
| 12 | `"Offer for Sale" The offer for sale comprising of up to [●] Equity Shares aggregating up to ₹ 9,500.00 million …` |

**Field disposition of the six states for this document**

| State | Applies? | Evidence |
|---|---|---|
| explicit zero OFS | no | no NIL wording; two positive amounts stated |
| explicit positive OFS | **yes** — ₹9,500.00 million | p1, p3, p12 |
| absent from the document | no | stated on three pages |
| placeholder `[●]` | only for the **share count**, not the amount | `Up to [●] Equity Shares … aggregating up to ₹ 9,500.00 million` |
| present but unparseable | no | parses exactly |
| conflicting credible values | no | p1/p3/p12 all give ₹9,500.00 million; seller rows sum to it |
| no qualifying source | no | the RHP is issuer-matched and official |

**Why it was unresolved in the original trace — two causes, both technical, neither a missing disclosure**

1. **Document-level rejection (dominant).** The RHP was rejected by the notice parser (date conflict) and by the prospectus parser (no `Prospectus Dated:` marker), and `parse_official_rhp` did not recognise the cover (the RHP-role test demanded a dated-title/responsibility-statement shape this cover does not carry). Its offer terms were therefore never read at all.
2. **Placeholder guard too coarse (independent).** Even when the RHP path was reached, `explicit_amounts` discarded any amount whose preceding text contained `[●]`. Every OFS statement in this filing has a `[●]` **share count** immediately before the money amount, so the disclosed ₹9,500.00 million was treated as an unknown amount.

**Measured before/after on the real document**

| | Before this pass | After |
|---|---|---|
| `fresh_issue_amount` | `None` | **5,000.0 `INR_MILLIONS`**, page 3, quote, `VERIFIED` |
| `ofs_amount` | `None` | **9,500.0 `INR_MILLIONS`**, page 3, quote, `VERIFIED` |
| `open_date` / `close_date` | conflict → document rejected | `2026-10-21` / `2026-10-23`, pages 3/3 |
| `price_band_low/high`, `lot_size` | `None` (document rejected before reading) | `None` — **and now diagnosed as `[●]` placeholders** (p11 / p11 / p9), i.e. genuinely undisclosed at RHP stage, not a parse failure |

`issue.ofs` is resolved for this document by its own explicit disclosure. Nothing was inferred: the value is a verbatim cell of the offer summary, and an explicit NIL is still the only route to zero.

## 11.5 Additional global corrections made in this revision

Each is issuer-independent and was found by working the real document.

| ID | Defect (confirmed) | Correction |
|---|---|---|
| **D5** | `_DOCUMENT_DATE` required a colon (`Dated:`), so a cover written `Dated October 14, 2026` produced **no document date** and the plausibility window was inert for the entire filing | colon optional, anchored to the **start of a line** (a cover date stands alone; this also stops a mid-sentence "certificate of incorporation dated December 21, 1987" being read as the document's date). Verified: Paras `2026-10-14`, R.K Fashion `2026-09-29`, Vishal Nirmiti `2026-09-24`, Moneyview `2026-09-28` |
| **D6** | a **defined-term entry** (`"Closing Date" shall mean 14 July 2017`) was eligible to become the issue close date | `_DEFINITION_FRAME` — a date inside a `"term" shall mean / means / has the meaning` definition is not a statement about this issue; exclusions now record *which* signal fired |
| **D7** | colon-form price band `Price Band: Rs. X to Rs. Y` matched **nothing** (the range pattern required the literal `is`/`of` after the label), so a standard notice wording yielded no band | label separator (colon or dash) and en-dash/em-dash ranges accepted; label + both amounts + a range separator still required, and a trailing `-NN` (a date written `2026-10-23`) is refused |
| **D8** | `_extract_price_band` used `.search`, i.e. only the **first** declaration per page, so two different bands on one page silently resolved to the first — a first-wins violation | every explicit declaration on the page is a candidate; identical repeats collapse, differing ones produce `CONFLICTING_PRICE_BANDS` and both ends are withheld |
| **D9** | `explicit_amounts` treated **any** `[●]` in the preceding text as an unknown amount, discarding disclosed OFS/fresh-issue money where only the *share count* was a placeholder | `_AMOUNT_SLOT_PLACEHOLDER`: only a placeholder in the **money slot** (`₹ [●]`, `[●] million`, `aggregating up to [ ]`) withholds the amount. A merged/header cell naming several components (`Fresh Issue and Offer for Sale`, `TYPE FRESH ISSUE SIZE  OFFER FOR SALE SIZE …`) still refuses to bind, because column order is not recoverable from text |
| **D10** | `SOURCE_PLACEHOLDER` diagnostics fired on share-count placeholders, reporting an "unknown amount" for an amount the parser had just extracted | the diagnostic is emitted only for markers that make the *amount* unknown (money-slot placeholder, `TBD`, unreadable OCR); RHP price-band/bid-lot placeholders are recorded per field with page and quote |
| **D11** | an unresolved field's diagnostic said only *unresolved* | additive `why_unresolved` (`ABSENT_FROM_INSPECTED_DOCUMENT`, `PLACEHOLDER_IN_QUALIFIED_DOCUMENT: page N`, `CONFLICTING_EVIDENCE_IN_DOCUMENT: …`, `HISTORICAL_VALUE_EXCLUDED: …`, `NO_QUALIFYING_SOURCE`), `inspected_sources` (provider, document class, URI, verification) and `required_evidence` per field. Existing `state` values, the required-term contract and evaluation eligibility are unchanged |

**Real-document effect of D5/D6 on the original failure:** with the document date now available (`2026-10-14`), a 2017 date anywhere on a term page falls outside the −60/+400-day window, so the historical value would be excluded even without the term-page rule. Verified synthetically: `[('2017-07-14', 590, 'defined-term entry, not a statement about this issue')]` and, with an issue-labelled line, `'outside the document's own date window (2017-07-14 vs document date 2026-10-14, -3379 days)'`.

**D7 verification** (probe, not a test run): `Price Band: Rs. 100 to Rs. 110`, `PRICE BAND: Rs 100 to Rs 110`, `Price Band: ₹100 – ₹110`, `Price Band: Rs. 100 - Rs. 110` → `100/110`; two colon-form declarations on one page → `None/None` + `CONFLICTING_PRICE_BANDS`; `Lot sizes range from 100 to 110 Equity Shares`, `The Offer opens 2026-10-21 to 2026-10-23`, `Bid/offer period 100 to 110 days` → no band. All ten notice fixtures keep their pre-correction values (`clean_notice` 208/220, `alternative_notice` 475/500, `conflicting_notice` withheld band with lot and window intact, both collar-invalid fixtures still raise).

## 11.6 Regression of the other retained filings (probe, not a test run)

| Filing | Result after revision 2 |
|---|---|
| R.K Fashion (496 pp RHP) | `open 2026-10-05`, `close 2026-10-07`, `ofs 0.0 INR_LAKHS` (explicit NIL), `fresh None`, band/lot `None` with placeholder diagnostics — **unchanged** from revision 1 |
| Vishal Nirmiti (551 pp RHP) | `open 2026-09-30`, `close 2026-10-05`, `fresh 14,500.0 INR_LAKHS`, `ofs None` with placeholder diagnostics — **unchanged** values |
| Moneyview final Prospectus (537 pp) | still not a notice, not an RHP; prospectus path unchanged |
| `fixtures/notices/*` (10 files) | bands, lots, windows and collisions unchanged; the two collar-invalid fixtures still fail closed |

## 11.7 Tests added — EXECUTED (revision 3)

`tests/test_official_rhp_terms_and_dates.py` gains 15 cases (36 total): colon-form band, en-dash/rupee band, colon-form conflict withheld, unrelated numeric ranges rejected, document date without a colon, mid-sentence certificate date not adopted, defined-term close date excluded, out-of-window issue date excluded, share-count placeholder does not hide a stated OFS amount, money-slot placeholders still withheld, merged header does not bind the wrong amount, two explicit component sentences resolve independently, OFS absent is diagnosed not zeroed, unresolved-field diagnostic names sources and required evidence, and every discoverable term has required-evidence text.

`tests/test_paras_evidence_regression.py` (new, 9 cases) asserts the artifact hash and pins the real document's behaviour: not a notice, RHP class and identity, cover read for the issue window, the p590 defined term not competing, the ₹9,500.00 million OFS and ₹5,000.00 million fresh issue with page/quote provenance, and price band/bid lot staying `None` as diagnosed placeholders. It is skipped when the evidence artifact is absent.

**Execution status: EXECUTED on 2026-10-23 — 45 collected, 45 passed, 0 failed, 0 skipped (see §11.8).**

The broader focused command below (notice parser, offer-table boundaries, OFS NIL binding, prospectus pathway, multi-source issue terms, automatic discovery) was **not** run in this pass — only the two modules named in the first command. The full suite is likewise **not run**.

```bash
cd /home/user/jio-k15
PYTHONPATH=engine python -m pytest -q tests/test_paras_evidence_regression.py \
    tests/test_official_rhp_terms_and_dates.py tests/test_price_band_notice.py \
    tests/test_offer_table_boundaries.py tests/test_ofs_nil_binding.py \
    tests/test_phase5j_hardening.py tests/test_official_prospectus_pathway.py \
    tests/test_issue_terms_multisource.py tests/test_automatic_official_issue_discovery.py
PYTHONPATH=engine python -m pytest -q tests/          # full suite
```

## 11.8 Validation pass (revision 3) — executed results

**Date:** 2026-10-23. **Commit under test:** `4b1c67f70047bbb5dbac10d18e53502a3c95c068` on `arena/07f3439f-ipo-screening-engine` (`main` untouched at `01ba66c`). **Environment:** CPython 3.11.2, pytest 9.1.1, `PYTHONPATH=engine`, interpreter `/home/user/ev/bin/python` (the repository `.venv` has no `pypdf`).

### Evidence integrity re-checked before the run

| Check | Result |
|---|---|
| SHA-256 of the working-tree artifact | `E0A3187FE18D1C12F88F29170291972714CF15BE7946E8A7F4A7D8C914570E74` — matches the published value |
| Size / page count | 11,577,075 bytes / 651 pages |
| Source | commit `1dd6e14e7fa50a677beefba9ca7d0d1a7b322c58`, path `docs/investigations/paras-healthcare/…pdf`, blob `f62a80f5e69702885da59462464023ca300ade0d`; re-verified from `origin` after publication |
| Fixture uses that artifact | yes — the module resolves the single committed path, and the fixture asserts the hash before any test body runs |

**The hash guard is effective, not decorative** (probed both ways on throwaway copies):

* artifact absent ⇒ **9 skipped** at module scope — the module reports *skipped*, never passed;
* one byte of the same-length artifact flipped ⇒ **9 errors**, each `AssertionError` at the hash line in the fixture — a substituted or truncated file fails loudly instead of quietly testing different bytes.

A skip is therefore not evidence of correctness; the numbers below are the run **with** the artifact present at the published hash.

### Command and results

```bash
cd /home/user/jio-k15
PYTHONPATH=engine /home/user/ev/bin/python -m pytest \
    tests/test_official_rhp_terms_and_dates.py \
    tests/test_paras_evidence_regression.py -q
```

| Run | Collected | Passed | Failed | Skipped | Exit |
|---|---|---|---|---|---|
| 1 (first execution) | 45 | 44 | 1 | 0 | 1 |
| 2 (after the test-side fix) | 45 | **45** | 0 | 0 | 0 |

Case counts: 36 in `tests/test_official_rhp_terms_and_dates.py`, 9 in `tests/test_paras_evidence_regression.py`.

### The one failure — a defect in the test, not in the engine

`test_the_historical_2017_defined_term_is_not_the_close_date` (real-artifact module), line 128:

```
TypeError: 'PriceBandField' object is not subscriptable
    assert all(item["value"] != "2017-07-14" for item in [close_field])
```

**Root cause:** the assertion was written against a dict shape; `_extract_dates` returns `PriceBandField` dataclasses. This was a transcription error in a test written during revision 2 and never executed. **The production behaviour it asserted was already correct** — the run had printed `close_field.value == "2026-10-23"` and `open_field.value == "2026-10-21"` on the two preceding assertions.

**Correction (test only):** attribute access (`close_field.value != "2017-07-14"`), plus an added assertion that the structural exclusion left `_last_excluded_dates` with no `2017-07-14` entry — which records *why* the date never competes (p590 is a definitions page, so no candidate is ever produced) rather than only that it lost. No assertion was weakened, no test removed or converted to a skip, and **no production module was touched** in this revision.

### Behavioural checks executed (A–F)

Run as read-only probes against the retained artifact plus the synthetic cases in the executed module.

| Check | Executed result |
|---|---|
| **A** Document class | `parse_official_rhp` ⇒ `source_type=RHP`, `document_class=OFFICIAL_RHP_TERMS`, basis "RHP title". Not a price-band notice; not promoted to a final Prospectus. The notice parser refuses it **by class** (`PriceBandNoticeClassificationError` naming the prospectus title), while genuine notice fixtures still classify. A missing `Prospectus Dated:` is not disqualifying (the synthetic RHP without that line is still an RHP); GID and DRHP are still refused. |
| **B** Dates | open `2026-10-21`, close `2026-10-23`, both from p3 with quote/locator. The p590 `"Closing Date" shall mean 14 July 2017` definition never enters the candidate set (`historical_dates_excluded: []` — structural exclusion, not a rejected candidate). Synthetic cases show an in-window historical sentence *is* excluded with `HISTORICAL_DATES_EXCLUDED` and that two credible current close dates still yield `close_date=None` + `CONFLICTING_CLOSE_DATES`. No date is excluded merely for being old: the same 2017-style window is read normally when it *is* the current issue. |
| **C** Offer amounts | OFS `9500.0 INR_MILLIONS`, fresh `5000.0 INR_MILLIONS`, both `DETERMINISTIC_PDF` / `VERIFIED`, p3, with the seller rows (₹3,000 + ₹6,500 million) as the corroborating disclosure. The `[●]` **share count** in the same sentence does not discard the monetary amount (`_AMOUNT_SLOT_PLACEHOLDER` only withholds a money-slot placeholder). The rule is general: the amount-binding test uses an issuer other than Paras. |
| **D** Band / bid lot | `price_band_low=None`, `price_band_high=None`, `lot_size=None`, `collar_spread_pct=None`, `collar_valid=None`; three `SOURCE_PLACEHOLDER` diagnostics (band low p11, band high p11, bid lot p9) each with quote. No substitution from the seller price (₹3,000/₹6,500 million) or any unrelated range; nothing inferred from dates. Colon-form bands parse real numerics, unrelated numeric ranges are refused, and two differing declarations are withheld rather than first-won (synthetic cases) — cross-issuer values were never consulted. |
| **E** Resolution | `resolve_fields` ⇒ `status=PARTIAL`; resolved `open_date`, `close_date`, `ofs`, `fresh_issue`; unresolved `price_band_low`, `price_band_high`, `lot_size`. `issue_term_errors: {}`. Undisclosed OFS in a different document stays unresolved rather than zero (synthetic); only an explicit NIL binds `0.0`; a conflicting field withholds that field alone. |
| **F** Operator diagnostics | each unresolved field carries `state=UNRESOLVED_AFTER_DISCOVERY`, `why_unresolved=["PLACEHOLDER_IN_QUALIFIED_DOCUMENT: page 11"]` (p9 for `lot_size`), `inspected_sources=[{document_class: OFFICIAL_RHP_TERMS, …}]` and a `required_evidence` sentence. The absent / placeholder / conflicting / historical-excluded / no-source states are distinguishable in the synthetic cases. `_REQUIRED_EVIDENCE` covers every member of `DISCOVERABLE_TERMS`. These are **additive** keys: existing `state` values, required-term contract and eligibility are unchanged, and an unresolved field is never reported as verified. |

### What this run does **not** establish

* It is **not** an ingestion run. The service gate, the `AWAITING_ISSUE_TERMS` payload, discovery, provider fetch and any evaluation were not executed; "the parser reads this document" is not "the ingestion path works".
* It is **not** the full regression suite (~3 h, `PYTHONPATH=engine python -m pytest -q tests/`) — not run, no claim made.
* Price band and bid lot remain **unresolved** for this filing, because the document prints `[●]`; no separate official band notice or final Prospectus was consulted.
* Trace `ing-42ded42dde7a41b2` remains unavailable.

## 11.9 What is still open

1. **The trace itself.** `ing-42ded42dde7a41b2` remains unavailable; the reconstruction matches its reported symptoms exactly (the two close dates, with the mechanism now known), but the run's own request/discovery payload cannot be diffed against this pass's probes.
2. **Price band and bid lot for this filing are genuinely undisclosed.** The RHP states `[●]` at pp. 9 and 11. A separate price band notice or the final Prospectus would be required; the engine now says exactly that instead of "absent".
3. **No ingestion was run end to end.** The resolution was exercised at the field-resolution layer with the real document as the candidate; the service gate, the `AWAITING_ISSUE_TERMS` payload it would now produce and any evaluation remain unexecuted by instruction.
4. **Regression execution is partial by design.** The two focused modules are green (§11.8); the full backend suite (~3 h) was not run and no claim is made about it. The ingestion path was not exercised end to end, so "parser tests pass" is not "ingestion validated".

---

## 12. Wider validation and controlled ingestion — 2026-10-24 (revision 4)

**Baseline:** `deb19bab08525a6dd143677c3669d6a6e98ea46f` on `arena/07f3439f-ipo-screening-engine` (`main` untouched at `01ba66c`). **Environment:** CPython 3.11.2, pytest 9.1.1, pypdf 6.20.1, `PYTHONPATH=engine`, interpreter `/home/user/ev/bin/python` (the previous sandbox virtualenv was gone; it was rebuilt from `requirements.txt`).

### 12.1 Evidence, re-verified before the run

sha256 `E0A3187FE18D1C12F88F29170291972714CF15BE7946E8A7F4A7D8C914570E74`, 11,577,075 bytes, 651 pages — unchanged, and unchanged again after the ingestion run.

### 12.2 Wider focused suites — executed

```bash
cd /home/user/jio-k15
PYTHONPATH=engine /home/user/ev/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_paras_evidence_regression.py tests/test_official_rhp_terms_and_dates.py \
  tests/test_price_band_notice.py tests/test_offer_table_boundaries.py \
  tests/test_ofs_nil_binding.py tests/test_phase5j_hardening.py \
  tests/test_official_prospectus_pathway.py tests/test_issue_terms_multisource.py \
  tests/test_automatic_official_issue_discovery.py
```

| Run | Collected | Passed | Failed | Skipped | Exit |
|---|---|---|---|---|---|
| 1 (baseline) | 219 | 215 | **4** | 0 | 1 |
| 2 (after corrections) | 221 | **221** | 0 | 0 | 0 |

The PDF-backed module ran with the artifact present at the published hash: its nine cases are **passes, not skips**, and the synthetic cases in `test_official_rhp_terms_and_dates.py` remain distinguishable from them. Coverage by area: price-band-notice parsing and classification (`test_price_band_notice.py`, 20 cases); offer-table boundaries and explicit amounts (`test_offer_table_boundaries.py`); OFS NIL/placeholder binding (`test_ofs_nil_binding.py`); prospectus/RHP pathways (`test_official_prospectus_pathway.py`, `test_official_rhp_terms_and_dates.py`); multi-source resolution and conflict withholding (`test_issue_terms_multisource.py`, `test_phase5j_hardening.py`); automatic official discovery (`test_automatic_official_issue_discovery.py`); the Paras regression modules.

A further **91 cases** across adjacent extraction/resolution modules (`test_extraction.py`, `test_extraction_phase5b.py`, `test_generic_issue_terms_extraction.py`, `test_issue_terms_resolver.py`, `test_jio_rhp_issue_terms.py`, `test_rk_fashion_reconciliation.py`, `test_cross_ipo_issue_term_provenance.py`, `test_issue_terms_runtime_path.py`, `test_official_discovery.py`) were run to bound the blast radius of the two production edits: **91 passed**.

### 12.3 The four failures, and what each was

| # | Failure | Root cause | Correction |
|---|---|---|---|
| 1 | `test_automatic_official_issue_discovery.py::test_image_only_official_notice_uses_real_offline_ocr_and_preserves_original_pdf_hash` — `ModuleNotFoundError: PIL` | **environment**, not code: the rebuilt sandbox venv lacked the OCR stack that `requirements.txt` pins | installed `pypdfium2 5.14.0`, `rapidocr 3.10.0`, `onnxruntime 1.24.4`, `pillow`; the case then **passed** against the real offline OCR models. No test or production change. |
| 2 | `test_offer_table_boundaries.py::test_unreadable_is_not_a_placeholder_or_cash` | **production defect** (introduced with D9/D10): `_AMOUNT_UNKNOWN_MARKER` still contained `UNREADABLE_OCR_LINE`, which the *pipeline itself* emits on low OCR confidence, so a reading failure was reported to the operator as `SOURCE_PLACEHOLDER` — the document was said to print a placeholder it never printed | `UNREADABLE_OCR_LINE` removed from the *source* marker; the amount is still withheld by the intervening-text guard. Two regression cases: the unreadable run reports no placeholder, and it still yields no amount and no unit. |
| 3 | `test_automatic_official_issue_discovery.py::test_draft_offer_document_is_never_promoted_to_current_rhp_authority` — expected `Draft Red Herring Prospectus cannot be promoted`, got `RHP title or issuer responsibility/offer-table role not established` | **production regression** from the revision-2 rewrite of `parse_official_rhp`: the DRHP guard became a silent `None` role, so a DRHP was refused with the wrong reason. Refusal itself was never lost | DRHP checked explicitly after the role test, and refused with its own message. Two regression cases: the DRHP gets the class-specific message, an unrelated attachment keeps the role message. |
| 4 | `test_phase5j_hardening.py::test_adversarial_d_conflicting_price_sources` — `DID NOT RAISE` | **stale test contract**: it asserted the pre-A30 behaviour (a conflicting band throws and discards the document). A30 changed that deliberately | test updated to the current contract **without weakening it**: the parse succeeds, the band is `None` at both ends, `CONFLICTING_PRICE_BANDS` is reported, and the conflicting notice still **fails closed at the final-mode evaluation gate** (`EnrichmentValidationError`). The adversarial property it guards — a conflicting band never reaches an evaluation — is unchanged. |

### 12.4 Controlled ingestion — executed, and what it showed

Path: `PresentationService.ingest_document` — the repository's supported upload ingestion (extraction → canonical builder → issue-term resolution → eligibility gate). **Non-production and non-mutating by construction:** `store_root` was pointed at `/tmp/paras-ingest/evaluations` (disposable), the policy directory stayed the read-only repository `config/`, and `IPO_OFFICIAL_DISCOVERY=0` disabled network discovery (egress is blocked in this sandbox anyway). The input was the committed artifact, hash-checked immediately before and after.

```
ingestion_id : ing-55319ecccdc243e4
mode         : final        status: BLOCKED        error: AWAITING_ISSUE_TERMS
evaluation_run: False       persisted: False       duration: 48.8 s
missing_fields: issue.price_band_low, issue.price_band_high, issue.lot_size,
                issue.ofs, issue.close_date
store_root   : /tmp/paras-ingest/evaluations — never created (nothing persisted)
```

Activity trace: `/tmp/paras-ingest/ingestion-activity/ing-55319ecccdc243e4.json` (27 events, outside the repository).

**What the trace shows (`filing_extraction` → `term_resolution`):**

| Field | Ingestion result | Expected from the RHP | Verdict |
|---|---|---|---|
| company / ipo_id | `PARAS HEALTHCARE LIMITED` / `PARAS-HEALTHCARE-LIMITED` | same | ✅ |
| `open_date` | `2026-10-21` (page 1, quote) | 21 Oct 2026 | ✅ |
| `close_date` | **not established** | 23 Oct 2026 | ❌ **defect** |
| `ofs` | **not established** | ₹9,500 million | ❌ **defect** |
| `fresh_issue` | `5000.0` labelled `INR_LAKHS` | ₹5,000 million | ⚠️ **value read, unit wrong** |
| `price_band_low/high` | not established | `[●]` placeholder | ✅ correct |
| `lot_size` | not established | `[●]` placeholder | ✅ correct |

The gate then blocked (`evaluation_eligibility/blocked`, `evaluation/not_run`, `persistence/not_attempted`) and nothing was written. **No evaluation was created or updated, no unrelated record changed, and the evidence artifact's hash is unchanged.**

### 12.5 Why ingestion still fails where the parser succeeds — the upload path

The A30 corrections live in `PriceBandNoticeParser` and `parse_official_rhp`, which the **discovery/resolver** path uses. The **upload** path uses a different, older extractor — `SectionExtractor.extract_cover_and_offer` in `extraction/sections.py` plus `CanonicalInputBuilder`. That path was never part of the A30 change, and it has three independent defects on this document:

1. **Close date not read.** The RHP cover prints `BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026`. The extractor's pattern requires whitespace after `CLOSES ON`, so the footnote marker `#` defeats it. The opening date, which has no footnote marker, is read normally.
2. **No monetary OFS extraction.** The upload path only ever sets `issue.ofs` from an explicit NIL (0.0) or from derived seller/share data. It has no branch that reads "…an Offer for Sale aggregating up to ₹ 9,500.00 million" at all, so a disclosed OFS is unreachable there regardless of placeholders. This is the **original reported symptom, still live on the ingestion path**.
3. **Monetary unit not converted.** `issue.fresh_issue` is extracted as `5000.0` with `raw_unit='MILLION'` and stored in a canonical input whose `reporting_unit` is `INR_LAKHS`, with no conversion anywhere in the builder. ₹5,000 million is 50,000 lakh, so the stored figure is **ten times too small**. It is harmless only while the run is blocked; it would mis-scale the offer if the terms were ever completed.

These are **not corrected in this pass**, deliberately. A correct fix touches the shared upload extractor and the builder's unit conversion — code that every issuer's ingestion runs through (`Vishal Nirmiti`, `R.K Fashion`, `Jio`, the fixtures) — and the only adequate validation of that blast radius is the full regression suite, which this pass is forbidden to run. Making an unvalidated cross-issuer change to a monetary path would breach the "preserve existing behaviour for unrelated issuers" and "no broad rewrites" constraints far more seriously than leaving the ingestion gate blocked, which is the safe state. They are recorded here as **required corrections with a named blast radius**, to be done in a pass where the full suite can run.

### 12.6 What the ingestion run does and does **not** establish

* **Establishes:** the upload ingestion path accepts this filing, identifies the issuer, reads the opening date, refuses to invent a price band or bid lot, blocks at `AWAITING_ISSUE_TERMS`, runs no evaluation, and persists nothing.
* **Does not establish:** that the reported failure is resolved end to end. It is **not** — `issue.ofs` and `issue.close_date` are still unresolved on the ingestion path, for reasons that are now known exactly (§12.5). Parser-level green is not ingestion-level green, and this section exists because the difference turned out to be real.
* **Trace equivalence:** `ing-42ded42dde7a41b2` remains unavailable, so this run cannot be diffed against it. It reproduces its *documented symptoms* — OFS unresolved on a filing that discloses it, issue dates not resolved — but identity with the historical run cannot be asserted.

### 12.7 Status after this revision

| Claim | State |
|---|---|
| Wider focused suites | **GREEN** — 221/221, 0 skipped; 91/91 adjacent modules |
| Parser-level Paras behaviour (§11.8) | unchanged and green |
| Ingestion gate | **correctly blocked** — price band and bid lot are genuinely `[●]` |
| `issue.ofs` / `issue.close_date` at ingestion | **unresolved — defect diagnosed, not corrected** (§12.5) |
| Evaluation created/updated | **none** — verified: store never created, `persisted: False` |
| Durable or unrelated state changed | **none** — repository diff is the intended files only |
| Full regression suite | **NOT RUN** |
| Engine evaluation-ready for this filing | **No** — required terms unresolved |

---

## 13. Upload-path correction — 2026-10-24 (revision 5)

**Baseline:** `231629180b6404dc58b2a90264645af7c36f094f` on `arena/07f3439f-ipo-screening-engine` (`main` untouched at `01ba66c`). **Environment:** CPython 3.11.2, pytest 9.1.1, pypdf 6.20.1, `PYTHONPATH=engine`, interpreter `/home/user/ev/bin/python`.

### 13.1 Why the previous revision's green parser did not help the ingestion

Two extraction paths, deliberately kept separate:

| | Path | Used by |
|---|---|---|
| **Parser** | `PriceBandNoticeParser`, `parse_official_rhp` (`extraction/price_band_notice.py`, `official_offer_amounts.py`) | official discovery, the issue-term resolver, the A30 field-level diagnostics |
| **Upload** | `SectionExtractor.extract_cover_and_offer` (`extraction/sections.py`) → `CanonicalInputBuilder` (`extraction/builder.py`) | every uploaded filing, i.e. `PresentationService.ingest_document` |

A30 corrected the first. The controlled ingestion of revision 4 ran the second and reproduced the original failure. The corrections below are in the **upload** path, are issuer-independent, and change no parser behaviour.

### 13.2 Defect A — the issue window behind a footnote marker

**Symptom.** `issue.close_date` was never extracted from the RHP, while `issue.open_date` was.

**Root cause.** The cover extractor's patterns required whitespace immediately after the label. The filing prints

```
BID/OFFER OPENS ON WEDNESDAY OCTOBER 21, 2026 BID/OFFER CLOSES ON# FRIDAY OCTOBER 23, 2026
```

where `#` is the UPI-mandate footnote reference. The opening label carried no marker, the closing label did, so the window arrived half-populated and the field was reported as "not established by filing extraction" — indistinguishable from a document that never states it.

**Correction** (`extraction/sections.py`). The two ad-hoc patterns became named module-level patterns, `_ISSUE_OPENS` / `_ISSUE_CLOSES`, sharing one tail: the label, an optional footnote marker (whitespace, `#`, `*`, `†`, `‡`, `§`, `¶`, a short hyphen, a parenthesised number, or a bare 1–2 digit reference), an optional colon, an optional weekday, then `Month D, YYYY`. Canonical ISO parsing downstream is untouched.

**What did not change.** A date still has to follow the *issue/bid/offer window's own* `opens on` / `closes on` label. A certificate-of-incorporation date, an allotment date, a mid-sentence certificate date, and the Articles' `"Closing Date" shall mean 14 July 2017` remain unreachable from this pattern, which is verified by tests.

### 13.3 Defect B — the disclosed monetary Offer for Sale

**Symptom.** `issue.ofs` was unknown on a filing that states ₹9,500 million three times.

**Root cause.** The upload path only ever set `issue.ofs` from (i) an explicit NIL, or (ii) a *share quantity* attributed to a sole selling shareholder. It had no branch that read a monetary statement of the Offer for Sale at all. The amount was therefore **never extracted** — it was not extracted-then-discarded, and it was not rejected during canonicalization.

**Correction** (`extraction/sections.py`). A single reader, `SectionExtractor._explicit_component_amount`, now resolves `aggregating (up) to ₹ N <unit>` for a component label and is used for **both** `issue.fresh_issue` and `issue.ofs` (the fresh-issue loop it replaces was the same logic inline, so there is one implementation, not two). It enforces:

* **no cross-component binding** — the search stops at the next component label, and a match whose own text runs through an excluded label is rejected, so an Offer-for-Sale amount can never be bound to the fresh issue or the reverse;
* **no column guessing** — a label immediately preceded by another component label joined by "and"/"&"/"," (a merged header cell, `Fresh Issue and Offer for Sale`, or an adjacent column) is skipped. On the real cover this is what kept the *fresh-issue* cell's ₹5,000 million out of the OFS field;
* **no inference** — the amount is read independently of the share count, which is a `[●]` placeholder on this filing; nothing is derived from shares × price;
* **fail closed on conflict** — two different amounts for the same component withhold the field rather than taking the first;
* **no substitution of a seller row** for the aggregate.

The NIL path is unchanged and takes precedence: an explicit NIL still binds `0.0`, and a missing OFS is still never zero. Provenance follows the existing cover convention: `page=1`, `section="Cover"`, a locator (`Cover page, Offer for Sale Amount` / `Cover page, Fresh Offer`) and the verbatim quotation.

### 13.4 Defect C — monetary unit normalization

**Symptom.** The controlled ingestion persisted `issue.fresh_issue = 5000.0` under `reporting_unit = INR_LAKHS` for a filing that states ₹5,000 **million**. That is ₹5,000 lakh instead of ₹50,000 lakh: a tenfold magnitude error, and not a display problem — `enrichment_engine` derives fresh shares as `fresh_issue × reporting-unit factor ÷ cap price`, so the error would propagate into a derived field the moment a price band existed.

**The canonical contract already answers the question.** `schema/ipo-input.v1.5.schema.json` documents `issue.fresh_issue` and `issue.ofs` as *"in reporting_unit"*, and `enrichment_engine._compute_derivations` consumes them as such. No new semantic or governance decision was needed: the stored value must be expressed in `financials.reporting_unit`.

**Where the boundary is.** `CanonicalInputBuilder` — the only component that knows both the extracted amount (with its `raw_unit`) and the filing's reporting unit. Extraction keeps the document's own wording (`raw_unit='MILLION'`), so the conversion happens **exactly once** and no component can convert twice.

**Conversions** (₹1 million = ₹10 lakh, ₹1 crore = ₹100 lakh):

| Document statement | `raw_unit` | Reporting unit | Stored value |
|---|---|---|---|
| ₹5,000.00 million fresh issue | `MILLION` | `INR_LAKHS` | **50,000.0 lakh** |
| ₹9,500.00 million OFS | `MILLION` | `INR_LAKHS` | **95,000.0 lakh** |
| ₹14,500.00 lakh (Vishal Nirmiti cover) | `LAKHS` | `INR_LAKHS` | 14,500.0 (identity) |
| ₹1,100.00 crore | `CRORE` | `INR_LAKHS` | 1,10,000.0 |
| amount in millions, filing reports in millions | `MILLIONS` | `INR_MILLIONS` | unchanged |

**Rules** (`CanonicalInputBuilder._normalize_issue_amount`): no unit stated ⇒ already canonical, returned unchanged; unit equal to the reporting unit ⇒ unchanged (identity, no double conversion); convertible ⇒ scaled and rounded to 2 decimals; **unconvertible ⇒ `None`**, because a wrong magnitude is worse than an unknown. Only `issue.fresh_issue` and `issue.ofs` pass through it — no other monetary field, no scoring input, and no reference/manual input (which is already canonical) is touched.

### 13.5 Tests

New `tests/test_upload_path_issue_terms.py` — **27 cases**, all synthetic (a stub PDF reader, no fixture dependency):

* **A:** the footnote close date; ten marker variants (`#`, `*`, `†`, `(1)`, `(#)`, `*1`, `:`, ` - `, `#1`); unrelated dated sentences (certificate 1987, allotment 2026-10-27) not adopted; the 2017 Articles definition not adopted.
* **B:** explicit OFS money read independently of a placeholder share count; the fresh-issue figure never bound to the OFS; seller rows summing to the aggregate not substituted; absent OFS not zero; explicit NIL still `0.0`; two conflicting amounts withheld; a different issuer (`NORTHWIND LOGISTICS LIMITED`, crore-stated) read the same way.
* **C:** million→lakh conversion for both fields; identity conversion; a millions reporting unit; crore→lakh; a second issuer; unsupported unit → `None`; no unit → unchanged; unrelated monetary fields untouched.

`tests/test_paras_evidence_regression.py` gained **5 cross-path cases** (14 total) that run the real 651-page filing through `DocumentExtractor` and assert that the upload path and the parser path agree once units are normalised.

| Run | Command target | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|---|
| targeted | `tests/test_upload_path_issue_terms.py` | 27 | **27** | 0 | 0 |
| real filing (parser + upload) | `tests/test_paras_evidence_regression.py` | 14 | **14** | 0 | 0 |
| wider focused (nine modules + the new module) | see below | 253 | **253** | 0 | 0 |
| upload-path regression | `test_extraction`, `test_fixture_fallback_isolation` | 20 | **20** | 0 | 0 |
| upload-path regression | `test_rk_fashion_reconciliation`, `test_fresh_issue_manual_entry`, `test_four_field_manual_terms`, `test_ingestion_activity`, `test_ingestion_worker_lifecycle`, `test_ui7_ingestion` | 77 | **77** | 0 | 0 |
| upload-path regression | `test_extraction_phase5b`, `test_financial_statement_column_mapping`, `test_contingent_liabilities_extraction`, `test_auditor_evidence_section` | 49 | **49** | 0 | 0 |
| golden / semantics | `test_vishal_golden`, `test_vishal_historical_reconciliation`, `test_core_semantics` | 54 | **54** | 0 | 0 |

```bash
cd /home/user/jio-k15
PYTHONPATH=engine /home/user/ev/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_paras_evidence_regression.py tests/test_official_rhp_terms_and_dates.py \
  tests/test_price_band_notice.py tests/test_offer_table_boundaries.py \
  tests/test_ofs_nil_binding.py tests/test_phase5j_hardening.py \
  tests/test_official_prospectus_pathway.py tests/test_issue_terms_multisource.py \
  tests/test_automatic_official_issue_discovery.py tests/test_upload_path_issue_terms.py
# 253 passed
```

### 13.6 Controlled non-production ingestion — re-run

Same supported path and same safety envelope as revision 4: `PresentationService.ingest_document`, `store_root` on `/tmp/paras-ingest2/evaluations` (disposable, outside the repository), policy directory read-only repository `config/`, `IPO_OFFICIAL_DISCOVERY=0`, input = the committed artifact, hash-checked before and after.

```
ingestion_id            : ing-5bd0ea97160b409e     mode: final
status                  : BLOCKED   error: AWAITING_ISSUE_TERMS
evaluation_run          : False     persisted: False     evaluation_id: None
missing_fields          : issue.price_band_low, issue.price_band_high, issue.lot_size
store_root              : never created
artifact sha256         : E0A3187F…570E74 before and after (unchanged)
duration                : 47.0 s
```

| Field | Value recorded | Provenance |
|---|---|---|
| issuer | `PARAS HEALTHCARE LIMITED` / `PARAS-HEALTHCARE-LIMITED` | filing extraction |
| `open_date` | `2026-10-21` | page 1, "Cover page, Issue Opening Date" |
| `close_date` | **`2026-10-23`** | page 1, "Cover page, Issue Closing Date" |
| `fresh_issue` | **`50000.0` (INR_LAKHS = ₹5,000 m)** | page 1, "Cover page, Fresh Offer" |
| `ofs` | **`95000.0` (INR_LAKHS = ₹9,500 m)** | page 1, "Cover page, Offer for Sale Amount" |
| `price_band_low` / `price_band_high` | unresolved | `[●]` at p11 |
| `lot_size` | unresolved | `[●]` at p9 |
| `fresh_shares` | unresolved (not required by the gate) | `[●]` share count |

The gate then blocked on the three genuinely undisclosed terms, ran no evaluation and persisted nothing. **This is the correct safe result:** the filing does not state a price band or a bid lot, and the engine says so instead of inferring one.

### 13.7 Status after this revision

| Claim | State |
|---|---|
| Upload path reads the disclosed terms | **yes** — dates, fresh issue and OFS, issuer-independent |
| Parser path unchanged | **yes** — 36 + 9 cases still green, no file in that path modified |
| Unit contract | **"in reporting_unit"**, conversions applied once in the builder |
| Ingestion gate | **correctly blocked** on price band and bid lot |
| Evaluation created/updated | **none** — store never created, `persisted: False` |
| Engine evaluation-ready for this filing | **No** — a price band notice or the final Prospectus is required |
| Full regression suite | **NOT RUN** |

---

## 14. Final regression gate — 2026-10-24 (revision 6)

**Baseline:** `415a883e709c87aeda02aa36d254b534145c2f07`. **Environment:** CPython 3.11.2, pytest 9.1.1, pypdf 6.20.1 (from `requirements.txt`), `PYTHONPATH=engine`, interpreter `/home/user/ev/bin/python`.

### 14.1 The full suite, run twice

```bash
cd /home/user/jio-k15
PYTHONPATH=engine /home/user/ev/bin/python -m pytest -q -p no:cacheprovider tests/
```

| Run | Commit | Collected | Passed | Failed | Skipped | Exit | Duration |
|---|---|---|---|---|---|---|---|
| 1 (first full run in this project's recent history) | `415a883` | 1768 | 1758 | **10** | 0 | 1 | 30 m 32 s |
| 2 (after the two corrections below) | `415a883` + fixes | 1772 | **1772** | 0 | 0 | **0** | 31 m 17 s |

The four extra cases in run 2 are the new cache regressions (§14.3).

### 14.2 What the ten failures were

Nine of the ten shared **one** root cause; the tenth was a separate, genuine regression.

| # | Failure(s) | Root cause | Correction |
|---|---|---|---|
| 1 | `test_d_peer_1_no_synthetic_peers::test_frozen_core_unchanged`, `test_frozen_core_line_endings` ×3, `test_presentation_api::test_configuration_status_governance_invariants`, `test_v16_implementation::t7_29/t7_34/t7_39/t7_42` | The **frozen-core pin** for `engine/ipo_screening/extraction/price_band_notice.py` was still the pre-A30 hash (`779afb0b…`, commit `0e15ac7`). A30 legitimately changed that file, but the pin was never re-established, so the engine reported the file — and the presentation API's `frozen_core_status` — as `CORRUPTED`. The control worked; the record was stale. | The pin is re-established at the reviewed A30 content (`5f6f0262…`), with a comment naming A30 as the authorising decision, exactly as the existing A15 precedent pinned `evaluation.py`. **The golden-result check is unchanged and still reproduces `e84f8bc0…`**, which is the independent proof that no scoring output moved. |
| 2 | `test_issue_terms_windows_retrieval::test_cache_read_survives_windows_unlink_failure` | **Genuine A30 regression, and a real evidence-loss bug.** `NoticeSnapshotCache.get()` re-parsed every cached snapshot with `PriceBandNoticeParser`. A30 made that parser refuse a prospectus **by class**, so a final Prospectus that had been retrieved, verified and cached came back from the cache as `(None, False)` — *verified official evidence silently disappeared on the second resolution*. The `[●]` unlink simulation in the test was incidental: the cache failed for any prospectus, patched unlink or not. | The cache records `document_class` at `put()` and dispatches on read: `OFFICIAL_PROSPECTUS` → `ProspectusTermsParser`, `OFFICIAL_RHP_TERMS` → `parse_official_rhp`, otherwise the existing OCR-aware notice path. Entries written before the class was recorded fall back to the provider name, then to the notice path, so no existing cache file becomes unreadable. |

No assertion was weakened, no test removed, and nothing converted to a skip.

### 14.3 Cache regression coverage (new)

`tests/test_notice_cache_document_class.py` — 4 cases: a cached Prospectus round-trips as a Prospectus (this is the case that returned `None` before the fix); the class is recorded beside the snapshot with the existing provenance fields intact; a cached notice still round-trips through the notice path with its values intact; and an entry written before `document_class` existed is still read.

### 14.4 Frozen-core amendment — stated explicitly

Re-pinning a frozen-core hash is a governance-relevant act, so it is recorded rather than absorbed:

* **What changed:** one expected hash in `FROZEN_CORE_HASHES`.
* **Why:** A30 (RAMKI-authorised, 2026-10-23) authorised corrections in `price_band_notice.py`; the reviewed result was committed and is covered by 36 parser cases plus 14 real-filing cases. Leaving the stale pin would have made the engine report `CORRUPTED` permanently, which is both a false alarm about scoring integrity and camouflage for a genuine future corruption.
* **What protects the scoring path instead:** `verify_golden_result()` — unchanged, still `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`. The five other frozen files are byte-identical to their pins.
* **Authority note:** this is bookkeeping for an authorised change, not a new policy. It is flagged for RAMKI's ratification in the tracker (revision 8); if ratification is withheld, the correct remedy is to revisit the A30 change, not to restore the stale pin.

### 14.5 Focused re-verification against the final code

| Command target | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| ten-module focused command + `test_notice_cache_document_class.py` | 257 | **257** | 0 | 0 |
| `test_upload_path_issue_terms.py` + `test_paras_evidence_regression.py` + `test_official_rhp_terms_and_dates.py` | 78 | **78** | 0 | 0 |
| frozen-core / v16 / peer / presentation modules (the nine failures) | 80 | **80** | 0 | 0 |

Verified on the real filing after the full suite: open `2026-10-21`, close `2026-10-23`, fresh issue `50000.0` INR_LAKHS (₹5,000 m), OFS `95000.0` INR_LAKHS (₹9,500 m), price band and bid lot still unresolved and diagnosed as `[●]`, parser and upload path in agreement. Evidence artifact sha256 `E0A3187FE18D1C12F88F29170291972714CF15BE7946E8A7F4A7D8C914570E74`, 11,577,075 bytes — unchanged.

### 14.6 Status after the gate

| Claim | State |
|---|---|
| Full backend suite | **PASSED** — 1772/1772, 0 failed, 0 skipped, exit 0, against the final code |
| Frozen core | 6/6 verified; golden result `e84f8bc0…` reproduced |
| Parser ↔ upload path agreement | Verified on the 651-page filing |
| Ingestion gate | Correctly blocked on price band and bid lot (`[●]`) |
| Evaluation | **NOT RUN** — none created, updated or persisted |
| Engine evaluation-ready for this filing | **No** — required issue terms remain unavailable |

---

## 15. Frozen-core pin — independent verification for ratification — 2026-10-24 (revision 7)

The re-pin in §14.4 was performed by the same pass that diagnosed the failure, so it is verified here separately, from the published tree, before it is put in front of RAMKI. **Every check below was executed on the published commit `14a0047`, not on an intention.**

### 15.1 The replacement hash is the byte identity of the reviewed file

The verifier hashes `file.read_bytes().replace(b'\r\n', b'\n')`, so the check is on the CRLF-normalised content — the same subject the pin is compared against.

```bash
for c in 0e15ac7 3699df2 4b1c67f HEAD; do
  git show $c:engine/ipo_screening/extraction/price_band_notice.py \
    | python -c "import sys,hashlib;print(hashlib.sha256(sys.stdin.buffer.read().replace(b'\r\n',b'\n')).hexdigest())"
done
```

| Commit | Meaning | CRLF-normalised sha256 | Blob |
|---|---|---|---|
| `0e15ac7` | pre-A30 content — **the stale pin** | `779afb0b1ba309913974edee4c09109b4e4da2806c3e49277e902e86a7c994e4` | — |
| `3699df2` | A30, first pass | `395977ae7744429353e6183189a8780c174a776041802a13b7dacb3c4364c28f` | `2ca043c2…` |
| `4b1c67f` | A30, reviewed final content | `5f6f0262f0e68acfe9feb1e2b44a6a0409c16fdf8b847763f86ba72fa3b9ed29` | `6dd36d20e8f5561ff110af0ae3986e1e329d829c` |
| `HEAD` | published tree | `5f6f0262…` — **identical** | `6dd36d20…` — **identical** |

The pin equals the sha256 of the exact blob committed at `4b1c67f` and still present at `HEAD`: the pin records published bytes, not a working copy.

### 15.2 The manifest diff contains only the one entry and its comment

```
@@ -65,7 +65,12 @@ FROZEN_CORE_HASHES: Dict[str, str] = {
     # A15 adds only an output artifact to evaluation.py; pin that reviewed hash
     # here while the golden-result check independently protects scoring output.
     "engine/ipo_screening/evaluation.py": "1258cd82…",
-    "engine/ipo_screening/extraction/price_band_notice.py": "779afb0b…",
+    # A30 (RAMKI-authorized 2026-10-23) corrected document-class recognition and
+    # field-level withholding in this file; the reviewed result is pinned here,
+    # exactly as A15 pinned evaluation.py.  The golden-result check
+    # (verify_golden_result) remains the independent protection for scoring
+    # output, and it is unchanged: it still reproduces e84f8bc0... exactly.
+    "engine/ipo_screening/extraction/price_band_notice.py": "5f6f0262…",
 }
```

One hash line changed, four comment lines added. No other frozen-core entry, no verifier logic, no comparison subject, and no other production file is touched by the re-pin.

### 15.3 The pin adds no behaviour and no policy

`verify_frozen_core` is unchanged; its comparison is unchanged; the six paths are unchanged. The pin is a constant consumed by an integrity check that already existed. The parser behaviour it guards was authorised separately by **A30** (RAMKI-authorised 2026-10-23, `handoff/decisions/A30-document-class-and-field-level-withholding.md`), and that change is covered by the parser, upload-path and real-filing suites. Re-pinning therefore asserts "this file is the reviewed A30 file", not "any change to this file is allowed": the next edit to that file will fail the check exactly as this one did.

### 15.4 Golden result unchanged

| Check | Command | Result |
|---|---|---|
| Frozen core (6/6) | `verify_frozen_core(Path('.'))` | `True` for all six files |
| Golden result | `verify_golden_result()` | `True`, `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` |

`GOLDEN_RESULT_HASH` is byte-identical to its pre-A30 value and was not edited in `14a0047` or `415a883`. The scoring output is reproduced from the frozen inputs, so it independently protects what the pin cannot.

### 15.5 Integrity tests pass with the replacement pin

```bash
PYTHONPATH=engine python -m pytest -q tests/test_frozen_core_line_endings.py \
  tests/test_d_peer_1_no_synthetic_peers.py \
  tests/test_v16_implementation.py::test_t7_29_cli_config_verify \
  tests/test_v16_implementation.py::test_t7_34_frozen_core_verification \
  tests/test_v16_implementation.py::test_t7_39_provenance_chain_verification \
  tests/test_v16_implementation.py::test_t7_42_end_to_end_v15_v16_workflow \
  tests/test_presentation_api.py
```

**39 passed, 0 failed, 0 skipped, 15.9 s.** This includes the LF/CRLF acceptance cases, the real-content-change rejection, the CLI `config verify` path, the provenance chain, and the presentation API's `frozen_core_status` = `VERIFIED`.

### 15.6 Tamper detection — a real alteration is caught

A controlled alteration of the frozen file was made and reverted in the working tree. Three genuine mutations were used, because a check that only appends bytes would not show that a *semantic* edit is caught:

| Mutation | File changed? | `verify_frozen_core` | Other five files |
|---|---|---|---|
| append `# tamper probe` | yes | **False** (`price_band_notice.py` False) | all True |
| rename `class PriceBandNoticeParser:` → `…ParserX:` (mid-file, semantic) | yes | **False** | all True |
| single-byte flip at the file midpoint | yes | **False** | all True |
| (control) no-op replacement of a non-existent string | no | True | all True |

The control row matters: an unchanged file is reported unchanged, so the three `False` verdicts above come from the verifier detecting the edit, not from a check that always fails. An earlier attempt at the semantic probe targeted a symbol that does not exist in the file; it changed nothing and the verifier (correctly) said so — which is why the control row is recorded rather than quietly dropped.

### 15.7 The alteration was fully reverted

| Check | Result |
|---|---|
| restored bytes identical to the pre-tamper file | `True` |
| restored CRLF-normalised sha256 | `5f6f0262…b9ed29` |
| `verify_frozen_core` after restore | `True` for all six |
| `git status --porcelain` | empty |
| `git diff HEAD` | empty |
| blob at `HEAD` | `6dd36d20e8f5561ff110af0ae3986e1e329d829c` (unchanged) |

No altered file was committed or published: the published tip predates the tamper probe, and the probe never entered an index.

### 15.8 Ratification status

**VERIFIED — READY FOR RAMKI RATIFICATION.**

That is a technical statement: the pin matches the reviewed published bytes, changes nothing but the constant and its comment, adds no policy, leaves the golden result intact, passes the integrity tests, catches a real tamper, and left no residue. **It is not ratification.** RAMKI has not ratified it, and the record says so wherever the pin is described.

---

## 16. Official price-band and lot-size evidence — 2026-10-24 (revision 7)

This section is a separate workstream from §15. It asks one question: **do issuer-matched official sources disclose the three terms the RHP leaves as `[●]`?** It does not resolve them in the engine (§16.5).

### 16.1 What was searched, and with what

Two retrieval routes were used, and the difference between them is the whole result:

| Route | What it is | Reachability on 2026-10-24 |
|---|---|---|
| The engine's own transport (`OfficialDiscoveryProvider`, `urllib`, cookie-jar session) | the supported discovery path | **blocked** — every official host fails at TLS from this sandbox |
| Arena's `functions.fetch_page` proxy | agent-side retrieval, outside the engine | **working** — BSE and SEBI pages were read |

The engine was run first, unmodified:

```
OfficialDiscoveryProvider(timeout_seconds=15).find("PARAS HEALTHCARE LIMITED", "paras-healthcare")
→ provider: official-discovery | outcome: UNAVAILABLE | candidate: None
  "no valid official listing could be retrieved: https://www.nseindia.com/…: listing retrieval failed
   (URLError: <urlopen error TLS/SSL connection has been closed (EOF) (_ssl.c:992)>)"  × 6 listings
```

`UNAVAILABLE` is the correct verdict and the important one: it is **not** `NOT_FOUND`, so nothing in this run may be read as "the terms are unpublished". The same TLS failure blocks this sandbox for all four hosts:

```
curl https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P  → curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL
curl https://www.nseindia.com/api/all-upcoming-issues?category=ipo      → curl: (35) …
curl https://www.sebi.gov.in/sebiweb/home/handleAction?…                → curl: (35) …
curl https://api.bseindia.com/BseIndiaAPI/api/GetPublicIssue…           → curl: (35) …
```

DNS resolves for all four, so this is egress filtering, not a broken URL.

### 16.2 Sources retrieved — every one of them official

Retained in `evidence/non-authoritative/paras-healthcare-issue-terms-20261024/` with a README, a capture manifest and SHA-256 digests.

| # | Source | Publisher / type | Issuer + issue identity | Disclosed values | Result |
|---|---|---|---|---|---|
| 1 | `DisplayIPO?id=4895&type=IPO&idtype=2&status=H&IPONo=8048&startdt=21/10/2026` | BSE — official exchange issue-information page | heading `Paras Healthcare Limited`; **Symbol `PARASHLTH`**; **Issue Period `21 Oct 2026 to 23 Oct 2026`** | **Price Band `660.00-693.00`**; **Market Lot `21`**; Minimum Bid Quantity `21`; Face Value `1.00` | **retrieved** |
| 2 | `https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P` | BSE — official historical public-issues listing | row `Paras Healthcare Limited` → `IPONo=8048` | `21-10-2026 | 23-10-2026 | 660.00 - 693.00 | 1.00 | Book Building` | **retrieved** (chunk 0 of 2, prefix retained) |
| 3 | `https://www.bseindia.com/downloads/UploadDocs/Notices/20261019-49/20261019-49.pdf` | BSE — official notice 20261019-49 (19 Oct 2026) | "Public Issue of **Paras Healthcare Limited** — Allocation to Anchor Investor" | anchor portion subscribed "at **Rs. 693/-** per equity share" | **retrieved** — corroborates the cap price only; an allocation price is not a price-band declaration |
| 4 | `https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/Paras%20Healthcare%20Limited_p.pdf` | SEBI — official filing (abridged prospectus / RHP memorandum) | `PARAS HEALTHCARE LIMITED`, CIN `U85110HR1987PLC035823` | fresh issue **₹5,000.00 million**, OFS **₹9,500.00 million**, total **₹14,500.00 million**; bid/offer 21–23 Oct 2026; **no price band or lot in the retained prefix** | **retrieved** — independently corroborates the date and monetary terms already resolved from the RHP |
| 5 | `https://listing.bseindia.com/Download/8888888/PreAnchor/PBA_20261015184043.pdf` | BSE — **Price-Band Advertisement** linked from source 1 (dated 2026-10-15) | same issue | not read | **NOT retrieved** — `functions.fetch_page` returned "Failed to fetch page" on 3 attempts. Cause not diagnosed (host-level proxy restriction, block, or unrenderable PDF). **A retrieval failure of that host, never evidence that the notice does not exist.** |
| 6 | `https://listing.bseindia.com/download/8888888/preanchor/rhp_20261016122004.zip` | BSE — Prospectus & GID archive linked from source 1 | same issue | not read | not attempted after the sibling `listing.bseindia.com` URL failed 3× |

Nothing third-party was used. A dozen aggregators publish "₹660–₹693, lot 21"; none was retained, cited as authority, or entered into evidence, because a snippet is not an official source and an aggregator is not the issuer or the exchange.

### 16.3 The evidence is genuinely there; it is also genuinely out of reach

Two independent obstacles stand between this evidence and a resolved term, and neither is a parser defect:

1. **Transport.** The engine cannot fetch any official host from this sandbox (§16.1). This would be solved by running on a host with egress; it is not a code problem.
2. **Discoverability, by contract.** Source 1 is served under `status=H` — BSE's *historical* view of a closed issue. The engine searches BSE's **live** public-issues listing (`IPOIssues?id=1&Type=P`), which no longer carries the Paras row: the live page was retrieved and, as of its own `23 Oct 26 | 16:00` stamp, the issue had moved to the historical view (source 2). Two separate mechanisms reinforce this and both are deliberate:
   * the BSE SPA record path follows only records whose `Status` is `F` or `L` (`official_issue_sources.py:175`) — a closed record supplies nothing;
   * the historical listing (`id=2`) is not among `OfficialDiscoveryProvider.LISTING_URLS`.

   **No code was changed to admit the closed page.** Adding the historical listing would let *any* past issue by a similarly named issuer supply terms — the engine matches issuer by name, not by issue identity, so an issuer with two IPOs in different years could be resolved from the wrong one. That is a contract decision for RAMKI, not a bug to slip in.

So the honest classification of the outstanding evidence is: **official evidence exists and was retrieved; it is not admissible through the current contract, and it is not retrievable from this environment.** That is different from "unpublished", and it is different from "the parser cannot read it" (§16.4).

### 16.4 The shared path reads this field set correctly — no correction needed

The BSE issue page is exactly the page class `ExchangeIssuePageParser` was built for. Its labelled rows were transcribed into a BSE-shaped table (documented as a transcription, not provider bytes: `functions.fetch_page` returns rendered text, and the sandbox cannot fetch the HTML). Against that input the **unmodified** parser returns:

| Expected | Parsed | Note |
|---|---|---|
| price band low `660.00` | `660.0` | quote `Price Band\n660.00-693.00`; class `EXCHANGE_ISSUE_PAGE` |
| price band high `693.00` | `693.0` | same quote |
| market lot `21` | `21` | locator `Exchange issue information - Market Lot` |
| issue period | `2026-10-21` / `2026-10-23` | both dates |
| issuer | `Paras Healthcare Limited` | from the page's own heading |

and, through the general discovery provider, `outcome: FOUND` with all three values, and `resolver.resolve(missing_fields=PRICE_AND_LOT) → RESOLVED`. **The parser and the discovery path already handle the official page; nothing in the extraction layer needed changing**, and none was changed.

New coverage: `tests/test_paras_official_issue_page_terms.py` — 17 cases. They are issuer-independent in their logic (they exercise the shared parser, the shared provider and the shared resolver), and they pin the fixture to the retained capture two ways: every quoted value must still appear in `bse-displayipo-4895-chunk-0.md`, and every manifest digest must match its file. Also covered: the lot is never taken from a maximum bid quantity; two contradictory `Market Lot` values withhold the field with an `issue_term_errors` entry; another issuer's page cannot supply these terms; a similarly named issuer's listing row is not followed; a missing lot leaves the term unresolved (`PARTIAL`); no provider yields `UNAVAILABLE` and no resolved field; a searched listing without the issuer yields `UNPUBLISHED` with all four required terms unresolved.

### 16.5 Decision

**No term was resolved. Nothing was written into the engine, a config, a store or an evaluation.** The values `660.00`, `693.00` and `21` appear in this repository **only** as investigator evidence and as test input; they are not in any issuer configuration, canonical record, snapshot or evaluation.

| Term | Status | Reason |
|---|---|---|
| `issue.price_band_low` | **UNRESOLVED** | official evidence exists (BSE issue page: 660.00) but is a closed-issue page, not searchable under the current contract, and not retrievable from this sandbox |
| `issue.price_band_high` | **UNRESOLVED** | same (693.00) |
| `issue.lot_size` | **UNRESOLVED** | same (market lot 21) |
| `issue.open_date` | resolved `2026-10-21` | unchanged from the RHP, cross-confirmed by sources 1, 2 and 4 |
| `issue.close_date` | resolved `2026-10-23` | unchanged from the RHP, cross-confirmed by sources 1, 2 and 4 |
| `issue.fresh_issue` | resolved `50000.0` lakh (₹5,000 m) | unchanged; source 4 independently states ₹5,000.00 million |
| `issue.ofs` | resolved `95000.0` lakh (₹9,500 m) | unchanged; source 4 independently states ₹9,500.00 million |

The last two rows are a free corroboration worth recording: an official SEBI filing states the same two monetary totals the upload path extracted, so that part of §13 is now confirmed by a second official document.

### 16.6 Next concrete discovery step

In order, and none of them is a code change to make the terms appear:

1. **Retrieve on a host with egress**, then re-run the unmodified engine: `OfficialDiscoveryProvider.find("PARAS HEALTHCARE LIMITED", …)` will still be UNAVAILABLE while the issue is closed — this step alone cannot resolve the terms and is listed to close the transport question, not to produce a resolution.
2. **Configure the price-band notice URL through the existing supported mechanism** — `IPO_NOTICE_URLS` for this issuer — pointing at the BSE Price-Band Advertisement (`…/PBA_20261015184043.pdf`). `listing.bseindia.com` is already an allow-listed official host and the notice path is not restricted to live issues, so this needs **no policy change and no new code**. It is blocked here only by transport: the URL could not be read from this sandbox (§16.2, source 5).
3. **If RAMKI wants closed issues discoverable at all**, decide the contract explicitly — including how a discovered page is tied to *this* issue (issue number, symbol or issue period) rather than to a same-named issuer's earlier IPO. Until that decision exists, the historical listing stays out of `LISTING_URLS`.

---

## 17. Retrieval trace, issue-identity binding, and controlled validation — 2026-10-24 (revision 8)

Baseline for this section: `0cf9d54` → this pass's commit. Environment: CPython 3.11.2, pytest 9.1.1, pypdf 6.20.1, `PYTHONPATH=engine`.

### 17.1 Why the engine says UNAVAILABLE while a browser can read the same pages

The trace was run end to end, not inferred. Four distinct causes exist; only one of them is live in this environment, and the other two were found by reading the code and then proved with tests.

| Layer | Observed | Verdict |
|---|---|---|
| DNS | `www.bseindia.com`, `www.nseindia.com`, `www.sebi.gov.in`, `api.bseindia.com` all resolve | working |
| TCP/TLS egress | `curl` → `(35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL` on every host; engine `urllib` → `URLError: <urlopen error TLS/SSL connection has been closed (EOF)>` | **blocked** |
| Session/cookies | `_default_http_fetch` already carries a cookie jar plus per-host homepage warm-up; irrelevant here because the connection never completes | not the cause |
| Endpoint selection | the six configured listings are the right ones; the issue page and its advertisement are correctly linked | not the cause |
| Parser | `ExchangeIssuePageParser` reads the published field set correctly (§16.4) | not the cause |
| Candidate matching | issuer matching works; a closed record is excluded by contract, which is now addressed by §17.2 | design, not defect |

The engine's own run is the evidence:

```
OfficialDiscoveryProvider(timeout_seconds=15).find("PARAS HEALTHCARE LIMITED", …)
→ outcome: UNAVAILABLE | candidate: None
  all six listings: classification=failed, searched=False
  note: "…: listing retrieval failed [TRANSPORT] (URLError: <urlopen error TLS/SSL connection
         has been closed (EOF) (_ssl.c:992)>)"
```

**`UNAVAILABLE` is not `NOT_FOUND` and not `UNPUBLISHED`.** The resolver maps `NOT_FOUND` to `UNPUBLISHED` only when a report names a listing it genuinely read; a transport failure names none, so the conclusion can never be drawn.

**Diagnostic improvement made this pass.** Every retrieval failure now carries a `[TRANSPORT]` / `[HTTP]` / `[CONTENT]` class, both in the listing loop and in issue-page retrieval, so an operator repairing a network no longer has to read an exception type to know whether the source was read and refused or never reached. `HTTPError` is classified before `URLError`/`OSError` (it is both) so "the server answered with a status" is not misfiled as "the connection failed".

### 17.2 The closed-issue problem, and the narrow solution

Both the live and the historical BSE listings were retrieved this pass. The live listing (`IPOIssues?id=1`) no longer carries the Paras row — as of its own `23 Oct 26 | 16:00` stamp the issue had closed — while the historical listing (`IPOIssues?id=2`) does, linking the issue page that states the price band and market lot. This is a **coverage** gap: the evidence exists, in the exchange's own archive, past the edge of the live search.

The prior contract (live records only; historical listing never searched) is correct as a default and was **not** removed. Instead, a closed record can now be used only through an identity-bound path, recorded as **A31** (`handoff/decisions/A31-historical-record-issue-identity-binding.md`) and implemented in `engine/ipo_screening/issue_identity.py`:

1. the closed-issue listing is **off unless an operator configures it** (`IPO_OFFICIAL_HISTORICAL_LISTINGS`, allow-listed HTTPS official hosts);
2. a record is admitted only when the issuer matches exactly **and** the row's bid window equals the window the **filing itself** establishes **and** the row carries the exchange issue number (`IPONo`) with a well-formed scrip id **and** its own identifiers agree (a link `startdt` contradicting the row date, a non-IPO record type or a missing scrip id is a conflict);
3. an expected issue number or symbol, when supplied, must match;
4. **no expected window ⇒ no admission** (`IDENTITY_UNBOUND`);
5. conflicts and ambiguity **withhold** the record with a stated reason — nothing is first-won or defaulted;
6. a closed-issue search never substantiates `NOT_FOUND`/`UNPUBLISHED` (class `historical`, `searched=False` for that purpose), because a forthcoming issue cannot appear in a closed archive.

An older offering by the same issuer is therefore rejected on the **window**, before any of its values are read; the field-level `STALE_OR_DIFFERENT_ISSUE` check in `issue_term_fields.resolve_fields` remains a second, independent barrier.

### 17.3 A second finding: the exchange's own advertisement could not be reached even by link

BSE publishes the price-band advertisement — the exact document class `HttpNoticeProvider` parses — as `…/PreAnchor/PBA_20261015184043.pdf`, and the rendered anchor text is "Click Here". The discovery attachment filter recognised only textual names (`price-band`, `prospectus`, `rhp`, …), so the exchange's own `PBA_` naming resolved to nothing. The filter now recognises the exchange's archival stem `PBA_<yyyymmdd…>`. This is a **naming** rule, not a widened source list: the URL must still be on an allow-listed official host, and the document is still issuer-matched and class-verified after retrieval. With it, an issuer-matched issue page that links its advertisement now yields the advertisement's terms through the unmodified notice parser (test: `test_discovery_follows_the_linked_advertisement_and_reads_band_and_lot`).

### 17.4 Decision boundary — deliberately NOT crossed

Tracing the configured-URL path showed that a `IPO_PRICE_BAND_NOTICE_URLS` entry pointing at `listing.bseindia.com` is **REJECTED** before retrieval: that host is in `DISCOVERY_HOSTS` but not `OFFICIAL_HOSTS`, a scoping that exists on purpose and is pinned by `tests/test_automatic_official_issue_discovery.py::test_archive_hosts_are_scoped_to_issuer_matched_discovery_not_direct_prospectus_urls`.

Admitting it would reverse a deliberate safeguard and require editing the test that encodes it, which is a **source-policy decision for RAMKI**, not an implementation choice. The change was made, found to contradict that test, and **reverted in full**; `OFFICIAL_HOSTS` and both configured-URL providers are exactly as they were. The discovery-followed route in §17.3 closes the practical gap without touching the allow-list. If RAMKI prefers configured URLs, the change is a two-line, well-understood amendment to that allow-list — recorded in A31 §5, not taken here.

### 17.5 Controlled validation (no evaluation, no store)

All runs below are on the **final** code of this pass (the last edit was the cross-row ambiguity rule in `bse_historical_issue_records`; the two sweeps were re-run after it).

| Check | Command scope | Result |
|---|---|---|
| Issue terms, discovery, resolver, identity, ingestion activity, upload path, Paras evidence, official RHP, notice cache, frozen core, presentation, v16, prospectus, OFS-nil, price-band notice | 22 modules incl. both new ones | **451 passed / 0 failed / 0 skipped** (3 m 8 s) |
| Provenance, manual terms, ui7 ingestion, enrichment, worker lifecycle | 13 modules | **141 passed / 0 failed / 0 skipped** (8 m 51 s) |
| New identity module | `tests/test_historical_issue_identity.py` | **35 passed** |
| Issue-page + closed archive + advertisement | `tests/test_paras_official_issue_page_terms.py` | **25 passed** |
| **Full backend suite** (re-run because this pass changed shared engine code) | `PYTHONPATH=engine python -m pytest -q tests/` | **1832 collected — 1832 passed / 0 failed / 0 skipped**, exit 0, 20 m 11 s |

The full suite grew from 1772 to 1832 tests: the 60 added here (35 + 25 new cases). Nothing else changed shape.

No test was weakened, skipped or removed. The one existing test that this work initially broke — `test_archive_hosts_are_scoped_to_issuer_matched_discovery_not_direct_prospectus_urls` — was **not** edited; the code change that broke it was reverted instead (§17.4), and it passes on its original text.

**Controlled non-production ingestion** (disposable `store_root` on `/tmp`, artifact hash-checked before and after, `mode=final`): **`AWAITING_ISSUE_TERMS`** on exactly `issue.price_band_low`, `issue.price_band_high`, `issue.lot_size`; trace `evaluation_run: False`, `persisted: False`, `evaluation_id: None`; no evaluation store created. Re-run with `IPO_OFFICIAL_HISTORICAL_LISTINGS` set: the closed-issue listing is genuinely attempted and recorded as `[TRANSPORT]`; the outcome is unchanged. The evidence PDF is byte-identical afterwards (`E0A3187F…570E74`, 11,577,075 bytes).

### 17.6 Status, stated separately

| Dimension | Status |
|---|---|
| Frozen-core pin | **VERIFIED — READY FOR RAMKI RATIFICATION** (§15), unchanged and not revisited |
| Official evidence retrieval | **PARTIAL** — issue page, historical listing, BSE notice and SEBI filing retrieved; the price-band advertisement itself not retrievable from this sandbox |
| Evidence admissibility | **ADMISSIBLE IN PRINCIPLE** — identity-bound closed-issue path implemented (A31); the live route is transport-blocked here |
| Issue identity | **IMPLEMENTED AND TESTED** — bound / unbound / incomplete / stale / conflicted verdicts, all fail-closed |
| `price_band_low`, `price_band_high`, `lot_size` | **UNRESOLVED** — no official bytes reached the engine in this environment |
| Required-term gate | **CLOSED** — verified by controlled ingestion |
| Evaluation readiness | **NOT ESTABLISHED** while the three terms are unresolved |
| Evaluation execution | **NOT RUN** — none created, updated or persisted |

### 17.7 The one capability needed to finish live

A host with egress to `*.bseindia.com` (and `nseindia.com`, `sebi.gov.in`). Then, with no code change:

```
IPO_OFFICIAL_HISTORICAL_LISTINGS="https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P"
PYTHONPATH=engine python -m pytest -q tests/   # or a normal ingestion of the retained RHP
```

The filing supplies the expected window (`2026-10-21`..`2026-10-23`), the historical row binds to it by issue number `8048`, and the issue page supplies `660.00` / `693.00` / lot `21`. Until then the gate stays closed and nothing is inferred from the RHP's `[●]`.

---

## 18. Configuration-to-runtime trace, wiring completion and the operational handoff — 2026-10-24 (revision 9)

Baseline `be531fc` → this pass's commit. Same environment as §17.

### 18.1 Egress re-checked (and still closed)

Re-tested at the start of this pass rather than assumed:

```
curl https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P          → http=000  (35) SSL_ERROR_SYSCALL
curl https://api.bseindia.com/BseIndiaAPI/api/GetPublicIssue_par_updated/w?flag=1 → http=000  (35)
curl https://listing.bseindia.com/Download/8888888/PreAnchor/PBA_2026101518…pdf   → http=000  (35)
engine _default_http_fetch(...)                                                   → URLError: TLS/SSL connection has been closed (EOF)
```

The agent-side retrieval proxy was also re-tried on the price-band advertisement (the one document class still unread): **HTTP 500**. Four independent attempts across two passes, three different routes, no change in conditions — the operation is not retried again blindly. **Transport failure, classified as such; not `NOT_FOUND`, not `UNPUBLISHED`, and not evidence that the advertisement does not exist.**

### 18.2 The wiring trace, layer by layer

| Step | Where | Verified |
|---|---|---|
| Configuration → provider | `build_resolver_from_env()` reads `IPO_OFFICIAL_HISTORICAL_LISTINGS` and builds `OfficialDiscoveryProvider(historical_listing_urls=…)` | ✅ test + live call |
| Provider construction in the **application** | `create_app()` → `PresentationService(cfg)` with **no resolver injected** → `build_resolver_from_env()` (`service.py:161-166`) | ✅ asserted by constructing the service exactly as `create_app` does |
| Dispatcher | `IssueTermsResolver.resolve` → `_provider_find` inspects the provider signature and passes `issue_context` only where declared | ✅ |
| Retrieval | same transport, allow-list and TLS rules as every other official source | ✅ |
| Historical discovery | `_search_historical_listing` → `bse_historical_issue_records` | ✅ |
| Identity binding | `issue_identity.check_issue_identity` (A31) | ✅ 35 cases |
| Linked issue page | `_from_issue_page` on the bound record's disclosure URL | ✅ |
| Field parsing | `ExchangeIssuePageParser` (unchanged) | ✅ |
| Resolver / gate | `issue_term_fields.resolve_fields`, `REQUIRED_ISSUE_TERMS` | ✅ |
| Ingestion | `PresentationService.ingest_document` → `AWAITING_ISSUE_TERMS` when unresolved | ✅ real filing |

**The gap this pass closed.** Everything above was individually proven in §17, but nothing proved the *chain*: that the application an operator runs actually builds the provider with the configured archive, and that the ingest path actually delivers the filing's own bid window — the one input identity binding cannot work without — to that provider. Both are now asserted by `tests/test_historical_listing_wiring.py`, including a run of the real 651-page RHP through `ingest_document` where the resolver records what it received:

```
company_name  : PARAS HEALTHCARE LIMITED
missing_fields: ['price_band_low', 'price_band_high', 'lot_size']
issue_context : open_date '2026-10-21', close_date '2026-10-23'  → binds_window True
outcome       : AWAITING_ISSUE_TERMS (transport offline by construction), no evaluation, no store
```

**A second gap closed: configuration errors are now visible.** An unusable `IPO_OFFICIAL_HISTORICAL_LISTINGS` entry (plain HTTP, a non-official host, an IP literal) previously surfaced only as a per-ingestion note, so a typo produced an identical "unavailable" verdict to an unreachable network on every run. `_historical_listing_urls_from_env()` now validates each entry at build time and registers a `ConfigurationDiagnosticProvider` naming the variable, the entry's position and the reason — without echoing the value. Usable entries still reach the provider; a broken entry never disables discovery itself.

### 18.3 What is *not* claimed

- **No live official-source retrieval occurred in this environment.** Every retrieval test in this repository is synthetic or evidence-backed; the transport is injected.
- **No term was resolved by the engine.** `660.00` / `693.00` / `21` appear only as investigation evidence and as test input.
- **The `listing.bseindia.com` allow-list question remains open** and untouched (A31 §5). The route that works — discovery following the exchange's own link, §17.3 — needed no such change.

### 18.4 Operational handoff — exactly what an egress-capable host runs

**Prerequisites:** this repository at the published tip; `python -m venv` from `requirements.txt`; outbound HTTPS to `*.bseindia.com`, `*.nseindia.com`, `*.sebi.gov.in`.

```bash
cd <repo>
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export PYTHONPATH=engine

# 1. Prove egress BEFORE interpreting any UNAVAILABLE verdict.
.venv/bin/python - <<'EOF'
from ipo_screening.issue_terms import _default_http_fetch
body = _default_http_fetch("https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P", 30)
print("egress OK, bytes:", len(body))
EOF
#    Expect: "egress OK, bytes: <n>".  Any URLError here means the host is still
#    blocked and nothing below can be interpreted.

# 2. Name the exchange's closed-issue archive (the only configuration needed).
export IPO_OFFICIAL_HISTORICAL_LISTINGS="https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P"

# 3. Resolve through the real runtime, with the filing's own issue window.
.venv/bin/python - <<'EOF'
from ipo_screening.issue_terms import build_resolver_from_env
outcome = build_resolver_from_env().resolve(
    company_name="PARAS HEALTHCARE LIMITED",
    ipo_id="PARAS-HEALTHCARE-LIMITED",
    missing_fields=["price_band_low", "price_band_high", "lot_size"],
    issue_context={"open_date": "2026-10-21", "close_date": "2026-10-23"})
print(outcome.status, outcome.resolved_fields, outcome.unresolved_fields)
for f in ("price_band_low", "price_band_high", "lot_size"):
    c = outcome.field_diagnostics[f]["candidates"]
    print(f, c[0]["value"], c[0]["uri"], c[0]["verification"])
EOF
```

**Success criteria — all of them, or it did not succeed:**

| # | Observable | Expected |
|---|---|---|
| 1 | step 1 | prints `egress OK, bytes: <n>` |
| 2 | `outcome.status` | `RESOLVED` |
| 3 | `resolved_fields` | `['price_band_low', 'price_band_high', 'lot_size']` |
| 4 | values | `660.0`, `693.0`, `21.0` |
| 5 | `uri` per field | the BSE issue page or its linked advertisement, never a third-party host |
| 6 | `verification` | `VERIFIED` for each |
| 7 | `outcome.conflicts` | empty |
| 8 | `outcome.provider_reports[].sources` | one attempt with `classification="historical"`, and a note naming the bound issue number `8048` |
| 9 | optional, ingestion | a normal `ingest_document(..., mode="final")` of the retained RHP proceeds past `AWAITING_ISSUE_TERMS` — **that step would create an evaluation and is NOT authorised here** |

**Failure signatures, and what each means** — so a failure is never misread as absence:

| Symptom | Meaning | Action |
|---|---|---|
| `[TRANSPORT]` in the note | the host was never reached | fix egress; nothing is concluded about publication |
| `IDENTITY_UNBOUND` | no expected window reached the resolver | check the filing's own `issue.open_date`/`issue.close_date` |
| `STALE_OR_DIFFERENT_ISSUE` | the archive row is a different offering | correct the expected window or the archive URL |
| `IDENTITY_CONFLICT` / `IDENTITY_INCOMPLETE` | the row contradicts itself or lacks `IPONo` | a data problem at the exchange; report, do not force |
| `UNPUBLISHED` | a **live** listing was genuinely read and carried no issuer document | nothing else to do; the terms are not published |

### 18.5 Validation on the final code

| Scope | Result |
|---|---|
| New wiring/integration module (`tests/test_historical_listing_wiring.py`) | **14 passed** |
| Identity + wiring + issue-page/closed-archive modules | **74 passed** |
| **Full backend suite** (production code changed this pass) | **1846 collected — 1846 passed / 0 failed / 0 skipped**, exit 0 |

### 18.6 Status, unchanged where it must be

Frozen-core pin: **VERIFIED — READY FOR RAMKI RATIFICATION** (not revisited, not ratified). Official evidence retrieval: **blocked at transport** in this environment. `price_band_low` / `price_band_high` / `lot_size`: **UNRESOLVED**. Required-term gate: **CLOSED**, verified end to end. Evaluation: **NOT RUN**, none created, updated or persisted. Evaluation readiness: **NOT ESTABLISHED**.

---

## 19. Operator host has egress — handoff exercised, and made one-command — 2026-10-24 (revision 10)

Baseline `ce5a238` → this pass's commit. **No evaluation; no store; no ingestion of a resolved filing.**

### 19.1 What changed in the environment picture

The operator's own host (`G:\ipo-screening-engine\ipo-screening-engine`) ran the handoff's transport probe and received **14,287 bytes** from `https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P`. That is a **successful official-source retrieval** — the long-standing `[TRANSPORT]` blocker is specific to the sandbox, not to the project, and the external dependency is now cleared on the host that matters.

Two things about that run needed fixing, and both are fixed here rather than described:

1. **The value pasted into the environment variable was not a URL.** It arrived as a Markdown link with an HTML-escaped ampersand:
   `[https://…IPOIssues?id=2&amp;Type=P](https://…IPOIssues?id=2&Type=P)`.
   That is what a URL looks like after being copied out of a rendered document or chat. Fed to the previous build, validation would have rejected it as "not an allowed official source host" — an **operator error reported as a policy problem**, which is the worst possible diagnostic. `normalize_configured_url()` now strips Markdown link syntax, surrounding angle brackets and quotes, and unescapes `&amp;`/entities *before* validation, for both `IPO_OFFICIAL_HISTORICAL_LISTINGS` and the `IPO_PRICE_BAND_NOTICE_URLS` / `IPO_PROSPECTUS_URLS` maps. It removes presentation artifacts only: no scheme is added, no host or path is rewritten, and a genuinely wrong value is still rejected with the same reasons as before.
2. **A retrieved page could look like a read listing.** A 14 KB response proves bytes arrived; it does not prove the page carried issue rows. If the served HTML is a shell, an interstitial or an error page, the previous build silently produced no candidates and no explanation. The archive reader now reports what the page actually contained: `issue_rows`, `issuer_rows`, `bound_rows`, `rejections`, and the provider says which case happened —

   * *"the served HTML carried no issue-information links at all (14,287 bytes, starts b'<!DOCTYPE …'); this is not a usable closed-issue listing and nothing may be concluded from its silence"* — wrong document, fix the URL; or
   * *"the served page carried N issue row(s) but none for this issuer"* — right document, different answer.

### 19.2 The one-command diagnostic

The handoff previously required pasting a multi-line Python snippet. It is now a CLI subcommand, read-only, with no evaluation and no writes:

```powershell
$env:PYTHONPATH = "$PWD\engine"
$env:IPO_OFFICIAL_HISTORICAL_LISTINGS = "https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P"
python engine\tools\ipo_screen.py issue-terms --issuer "PARAS HEALTHCARE LIMITED" `
    --open 2026-10-21 --close 2026-10-23
```

It prints the issuer, the expected window, the requested terms, the resolution status, then every provider with **one line per source** marked `searched` / `failed` / `historical` / `homepage` / `shell`, every rejection note, and for each field the value, its verification state, its URI, its quote and its locator. `--json` prints the full `ResolutionOutcome`. Exit code `0` means `RESOLVED`, `1` means not resolved (the same refusal code the rest of the CLI uses).

**Expected output on a working host:**

```
status             RESOLVED
resolved           price_band_low, price_band_high, lot_size
terms
  price_band_low     VERIFIED
    value 660.0  VERIFIED  https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4895&…IPONo=8048…
      quote: 660.00 - 693.00
  price_band_high    VERIFIED
    value 693.0  VERIFIED  …
  lot_size           VERIFIED
    value 21  VERIFIED  …
```

### 19.3 What is still not claimed

* **No live retrieval happened in this repository's own environment.** The retrieval tests remain synthetic or evidence-backed; nothing above is a claim that this sandbox reached BSE.
* **No term has been resolved by the engine yet.** The operator's 14,287-byte response has not been run through the resolver; §19.2 is the command that does it and the output above is the expected, not the observed, result.
* **Ingestion is not authorised to proceed past the gate.** Once `issue-terms` prints `RESOLVED`, ingestion would produce an evaluation — a separate authority step, unchanged by this pass.

### 19.4 Status

| Dimension | Status |
|---|---|
| Frozen-core pin | **VERIFIED — READY FOR RAMKI RATIFICATION** (untouched) |
| Sandbox egress | blocked at TLS (unchanged; irrelevant now) |
| **Operator-host egress** | **WORKS** — 14,287 bytes retrieved from the BSE historical listing |
| Configuration robustness | paste artifacts normalised; unusable entries diagnosed without echoing the value |
| Retrieved-page diagnostics | row counts and a shell-vs-answer distinction added |
| `price_band_low` / `price_band_high` / `lot_size` | **still UNRESOLVED pending the operator run in §19.2** |
| Required-term gate | CLOSED (fail-closed behaviour unchanged) |
| Evaluation | **NOT RUN**, none created, updated or persisted |

### 19.5 A determinism defect the full suite found, and what was actually wrong

Running the whole backend suite for this pass produced **one** failure that no focused module reproduces: `test_workbook_bytes_are_deterministic` failed only on a run where the two serialisations happened to straddle a two-second boundary. That is not a flaky test — it is a real defect in the artifact contract, and it was diagnosed rather than retried.

* **Symptom.** Two calls to `workbook_bytes()` for the same `Workbook` a couple of seconds apart differed at byte offset 10 — the local ZIP header's DOS timestamp.
* **Cause.** `openpyxl` rewrites `docProps/core.xml`'s `dcterms:modified` **and** every ZIP entry's date/time at `save()`. Pinning `workbook.properties.created` / `.modified` (`excel.py:843-844`) therefore does **not** pin the bytes: the writer stamps the moment of saving, at two-second resolution. Two immediate saves agree by luck; a slow run does not.
* **Consequence for the project, not just the test.** The provenance store writes the workbook file and derives the content hash used to identify it. If the same logical artifact can serialise two ways, the hash does not identify the artifact — a re-run can produce a "different" workbook with identical content, and `dcterms:modified` records the machine's clock rather than the data.
* **Fix.** `deterministic_workbook_bytes()` serialises to memory and repacks the archive: `dcterms:modified` pinned to `1980-01-01T00:00:00Z` and every entry's timestamp pinned to `(1980, 1, 1, 0, 0, 0)` — the earliest value the ZIP/DOS format can represent, so no writer can silently substitute "now". Both `workbook_bytes()` and `project_store` go through it, so **the bytes written and the bytes hashed are the same bytes**. The archive stays intact (verified entry-by-entry), and a regression case re-serialises across a tick (`tests/test_reproducibility_store.py`).

This is recorded because it is exactly the class of defect a "green focused tests" claim hides: nothing about the feature under test changed, and the failure only appears when the clock is unlucky.

### 19.6 Verification actually run this pass

| Run | Result |
|---|---|
| `tests/test_issue_terms_cli.py` (new: normalisation, diagnostics, exit codes, rendering) | **19 passed** |
| `tests/test_reproducibility_store.py` (workbook determinism, including the tick-crossing case) | **33 passed** |
| `tests/test_acceptance_matrix.py` + `tests/test_dataset_phase6b.py` (the other modules that import the workbook writer) | **85 passed** |
| Full backend suite, against the final code | **1866 collected / 1866 passed / 0 failed / 0 skipped**, exit 0, 22 m 05 s |

The first full-suite run of this pass was **1864 passed / 1 failed**; the failure was the determinism defect in §19.5, not a test defect. It was fixed in the production writer, re-tested, and the suite was then run again **in full against the final tree** — the table above is that second run. No assertion was weakened, no test converted to a skip, and no test removed.

A passing suite remains evidence about the code, not about the network: **no test in this repository reached an official host**, and nothing here shows that the operator's retrieval will bind. §19.2 is the step that decides that.

**Publication and CI.** The code above is commit `1ad6412` on `arena/07f3439f-ipo-screening-engine`; the repository's `regression` job for that commit passed (21 m 04 s, run `40086752768`), independently of the local runs in the table. A documentation-only commit follows it and changes no code. PR #7 remains **open** with `main` untouched at `01ba66c`.
