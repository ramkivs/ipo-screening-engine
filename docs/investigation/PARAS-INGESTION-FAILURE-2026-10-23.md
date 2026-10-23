# Paras Healthcare ingestion failure — root cause and general correction

- **Record type:** engineering investigation and correction record. Not a new policy, not a scoring change, not an evaluation.
- **Investigation date:** 2026-10-23 (Asia/Calcutta).
- **Branch:** `arena/07f3439f-ipo-screening-engine` (working branch; `main` untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`).
- **Baseline this pass:** `8939b05be00a23d5733163cdb6a280b0578cfd10`.
- **Scope:** the extraction path that produced a rejected official document and an unresolved `issue.ofs`: Price Band Notice classification, current-issue date extraction, field-conflict handling, the RHP document class, and the OFS resolution chain. Corrections are issuer-independent.
- **Execution status:** **regression tests NOT RUN** — deferred to the separate regression pass by explicit instruction. No ingestion, no evaluation, no scored artifact was produced or modified. Behaviour statements below come from read-only extraction probes on retained filings and on synthetic text; they are **not** a substitute for the regression run.

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

## 6. Tests added or updated — **NOT EXECUTED**

Execution status: **NOT RUN — deferred to the separate regression pass.** The full backend suite takes roughly three hours and was excluded by explicit instruction for this pass. Nothing below is claimed as passing.

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
