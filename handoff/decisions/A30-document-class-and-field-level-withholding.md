# A30 — Document Class and Field-Level Withholding (RHP / Price Band Notice / Prospectus)

- **Decision ID:** A30
- **Title:** a document is read under its own class, and a conflicting field is withheld rather than rejecting the document
- **Record type:** **IMPLEMENTATION RECORD — no new policy, no new criterion, no scoring change.** Per `handoff/decisions/CONVENTION.md` rule 4, the approved text below is the correction contract that the investigation was authorised to implement; the analysis and residual risks are Arena's and are recorded, not decided.
- **Decision status:** **IMPLEMENTED 2026-10-23; regression execution PENDING.**
- **Decision authority:** RAMKI — 2026-10-23 investigation directive for the Paras Healthcare ingestion failure (general, issuer-independent correction; no hardcoding, no policy change).
- **Decision date:** 2026-10-23 (Asia/Calcutta).
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/07f3439f-ipo-screening-engine`, tip `8939b05be00a23d5733163cdb6a280b0578cfd10`; `main` untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`.
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

## 4. Consequences

* **What can now resolve:** price band, bid lot and issue window from an RHP's own cover/offer summary (previously unreachable); OFS and fresh-issue amounts from the RHP's offer table (previously unreachable when the document was rejected); each with its own page, locator, quote and verification, rather than a single document-level verdict.
* **What still cannot:** a field the document does not state, states as `[●]`, or contradicts itself. Those stay `None` and are reported; they do not become `0`, do not become a negative finding, and do not satisfy a required term.
* **Rejection semantics changed for two cases only:** a notice with a conflicting band/lot/window is now accepted with that field withheld (it used to throw the document away), and an RHP is accepted as an RHP. Every other rejection path (collar, identity, placeholder-only, GID, DRHP, unqualified source) is unchanged.
* **No criterion moves on its own.** Issue terms feed `AWAITING_ISSUE_TERMS`; a withheld field cannot satisfy a required term, so a run that could not resolve terms still cannot.

## 5. Tests — NOT RUN

Added `tests/test_official_rhp_terms_and_dates.py` (21 cases) and rewrote two tests in `tests/test_price_band_notice.py` whose assertions encoded the old contract (`test_conflicting_price_bands_rejected` → `…_withhold_the_band_not_the_document`; `test_inverted_date_order_rejected` → `…_withholds_both_dates`). The rewrites keep the failure assertion (the conflicting value is never published) and add the survival assertion (the undisputed fields are).

**Execution status: NOT RUN — deferred to the separate regression pass** (full backend suite ≈ 3 h, excluded by explicit instruction). Static compilation only.

## 6. Residual risks and open items

1. **Not verified against the original failing document** — the Paras PDF and trace are absent from the repository. The defects are confirmed on the shipped code path and reproduced on other retained filings.
2. **`Price Band: Rs X to Rs Y` (colon form) is not matched** by the band range pattern. Recorded as a **proposal**, not adopted: widening it changes notice behaviour (one band vs. a conflict) in a way this pass cannot regression-check. It is the reason a cover whose only band statement uses the colon form leaves the band `None`.
3. **Operator diagnostic for an absent OFS** is unchanged at resolution level; only the provider reason string now carries the class verdict.
4. **Retention of the old conflict contract elsewhere** — any sibling branch or tool that catches `PriceBandNoticeParseError` to detect "conflicting notice" will now see a successful parse with `issue_term_errors`. In this branch the four call sites were reviewed: each treats an exception as "not a notice", which is still correct, and none depends on the conflict raise.

## 7. Implementation authority

**GRANTED** for this pass, limited to: document-class recognition, RHP-authorised field extraction, field-level withholding, the metadata needed to distinguish absent / withheld / parsed, the provider reason string, and focused tests. **Not granted:** any change to scoring, criteria, thresholds, required-term policy, qualification or verification rules, the party/complaint rules of A23–A25, the A29 status meaning, fixtures, the golden record, or any evaluation — and no evaluation run.
