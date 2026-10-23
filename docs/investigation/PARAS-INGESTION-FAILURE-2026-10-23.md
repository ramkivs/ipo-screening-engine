# Paras Healthcare ingestion failure — root cause and general correction

- **Record type:** engineering investigation and correction record. Not a new policy, not a scoring change, not an evaluation.
- **Investigation date:** 2026-10-23 (Asia/Calcutta).
- **Branch:** `arena/07f3439f-ipo-screening-engine` (working branch; `main` untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`).
- **Baseline this pass:** `8939b05be00a23d5733163cdb6a280b0578cfd10`.
- **Scope:** the extraction path that produced a rejected official document and an unresolved `issue.ofs`: Price Band Notice classification, current-issue date extraction, field-conflict handling, the RHP document class, and the OFS resolution chain. Corrections are issuer-independent.
- **Execution status:** the two focused regression modules were **executed and passed on 2026-10-23** (45 collected / 45 passed / 0 skipped, commit `4b1c67f`) — see **§11.8**, which records the command, the one test-side defect that was fixed, and the checks performed. The **full backend suite (~3 h) was NOT run**, and **no ingestion, evaluation or scored artifact** was produced or modified. Statements in §§1–10 that predate the document remain as written; where they say "not executed", §11.8 supersedes them for these two modules only.
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
