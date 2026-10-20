# A23 — Litigation and SEBI/ED Negative Defaults: Investigation and Contract-Permitted Correction

- **Decision ID:** A23 (decision **D-5** of the HD Fire / Jio decision set)
- **Title:** litigation bucket and regulatory-action flag are evidence-or-UNKNOWN; two coverage standards remain open
- **Record type:** **INVESTIGATION plus a recorded correction.** Per `handoff/decisions/CONVENTION.md` rule 4, this record is **not** an approval of the alternatives in §"Open decisions"; it separates Ramki-approved material from v1.5 requirements, Arena analysis, and unresolved proposals.
- **Decision status:** **RAMKI DECISION REQUIRED** for the two coverage standards (clean's party coverage; a verified regulatory absence). The removal of the unsupported defaults was executed under the existing contract and needed no new rule — see "What needed no approval".
- **Decision authority:** RAMKI
- **Date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/95234306-ipo-screening-engine` at remotely verified commit `2d52baa56cbb4b82061649106745f79d04d9fce6`; `main` `01ba66c12ca1195fd7acbd287c3e39a019808094`; PR #6 `OPEN`/`UNMERGED` at head `e05c0ef` (base `arena/573e69a4-ipo-screening-engine`).
- **Scope:** `governance.litigation_bucket`, `governance.sebi_ed_action_active` as produced by the deterministic PDF extraction path, and their treatment by `extraction/sections.py::extract_governance` and `extraction/builder.py::_build_governance`.
- **Out of scope and unchanged:** `config/ipo-config.v1.5.0.json` (`litigation` criterion, `critical_data`, K2 definition), `schema/ipo-input.v1.5.schema.json`, `fixtures/` and the golden record, `derived.py`, `scoring.py`, `knockouts.py`, `penalties.py`, `confidence.py`, `eligibility.py`, all historical evaluation records.

## 1. The defect, as verified on the baseline

At `2d52baa`:

* `sections.py:1691-1732` assigned `lit_bucket = "clean"` and `sebi_active = False` **before** the scan and appended **both** fields unconditionally afterwards — so a filing whose litigation section was never located (default range `430 … min(500, page_count)`) earned the favourable end of a scored criterion, 4/4, and cleared a `critical_data` flag.
* `governance.sebi_ed_action_active` was emitted with `quote="No active SEBI or ED regulatory proceedings"` and **without** `quote_is_processing=True`: a synthesised sentence presented as a source quotation (the defect class D-4 removed for auditor tenure and repeated EOM).
* The scan was phrase-bound (`criminal proceedings against our promoters`, `r.c.c.`, `criminal complaint`, `material civil litigation`, `civil suit`) and polarity-blind, so (a) the statutory ICDR shapes — the **summary table of outstanding litigation** and the labelled "category / Nil / 2" list — were invisible, and (b) an express denial ("there are **no** outstanding criminal proceedings or material civil litigation") classified as `minor_civil`.
* `builder.py:315-321` then mapped **any** value other than `criminal_or_regulatory` onto `"clean"`, so the evidenced `minor_civil` from `fixtures/filings/class_a_financial_lender.pdf` p. 11 was rewritten into the favourable bucket and its evidence destroyed; `builder.py:336` defaulted `sebi_ed_action_active` to `False`.
* Net effect on committed filings (measured): R.K. Fashion and both `complete_sample_rhp` fixtures asserted `"clean"` + `false` on pages that were never read; HD Fire's published §12 table — **two criminal proceedings against Directors** — was reported `clean`.

## 2. Contract analysis: UNKNOWN already exists, so no new category was invented

| Requirement | Existing contract | Evidence |
|---|---|---|
| A missing/unreadable litigation input is representable | `governance.litigation_bucket` enum is `["clean","minor_civil","criminal_or_regulatory", null]` | `schema/ipo-input.v1.5.schema.json` |
| Absent ⇒ UNKNOWN, not 0 | `resolve_value` returns `None` ⇒ `CriterionResult(state="UNKNOWN", score=None, reason="the litigation status of the promoters, directors and company is not established")` | `scoring.py::categorical_points`, `resolve_value` |
| UNKNOWN points are unavailable, not forfeited | `effective` counts only `SCORED`; `unknown_points += criterion.max`; completeness and `unknown_penalty = 10 × unknown / 25` follow | `scoring.py`, `confidence.py` |
| A missing regulatory flag cannot read as "no problem" | K2 lists `required: ["promoter_pledge_pct","sebi_ed_action_active"]`; a missing input ⇒ **UNVERIFIED**, never CLEAR | `knockouts.py::_litigation_and_regulatory` |
| …and it degrades the verdict | `sebi_ed_action_active ∈ config.critical_data.items` ⇒ verdict `INSUFFICIENT_DATA` | `config/ipo-config.v1.5.0.json`; `verdict` precedence (A7) |
| Director-only proceedings are inside the criterion | formula: *"clean / minor_civil / criminal_or_regulatory across promoters, directors and the company"* | `config/ipo-config.v1.5.0.json`, criterion `litigation` |
| A fourth scored bucket is **not** available | `config_validation.py:53` requires the categorical map to define exactly `["clean","minor_civil","criminal_or_regulatory"]` | `config_validation.py` |

**Conclusion:** removing an unsupported negative default is implementation correctness under the existing contract (the same reasoning that carried D-1 and D-4), not a new rule. Adding a `"unknown"` bucket value **would** have violated the contract, and was not done.

## 3. What needed no approval, and was therefore corrected

1. **No default emission.** `governance.litigation_bucket` and `governance.sebi_ed_action_active` are emitted only from text on the page cited; otherwise the field is absent (UNKNOWN).
2. **No fabricated quotation.** Both synthesised sentences are gone from `sections.py` and `builder.py`; every emitted quotation is a verbatim slice of the cited page, and structural text (table headers, separator rows, bare category headings) is masked so a *label* can never be quoted as a *finding*.
3. **Polarity.** A negated "no litigation" sentence is an absence statement, not a civil finding.
4. **The statutory disclosure forms are read** — the ICDR summary table and the labelled category/value list — so disclosed counts reach the bucket instead of being invisible. This *narrows* to the disclosed direction and party: "against" rows are adverse, "by our Company" rows are not, a promoter-scoped SEBI column cannot speak for the issuer, and a row or column that cannot be parsed makes coverage **incomplete ⇒ UNKNOWN** rather than `clean`.
5. **No coercion in the builder.** `minor_civil` stays `minor_civil`; only explicitly stated synonyms normalise; an unrecognised value is UNKNOWN, never the favourable bucket.
6. **The flag is not inferred from a criminal proceeding.** `sebi_ed_action_active = True` requires SEBI or the ED as actor **and** a finite act (`initiated / issued / passed / imposed / conducted / attached / registered / taken / served / filed / raised / recorded / framed`, or "pending before SEBI") **and** a party, with registration/disclaimer boilerplate excluded. The same affirmative is accepted from the summary table's SEBI column and from a labelled count, so a disclosed action is not missed merely because it was printed as a number; neither structured route may answer `False`, because a `Nil` there is scoped by its own heading and never mentions the ED.
7. **Polarity is measured against the act, not the sentence start:** "SEBI has **not** imposed any penalty on our Promoters" does not trigger K2 — a prefix-only test would have.
8. **`False` requires both regulators named**, since the governed flag is `sebi_ed_action_active`; a negative covering only one of them leaves the field UNKNOWN. An explicit both-regulator denial needs no act verb, and a positive finding anywhere in the range outranks such a general denial (prospectuses open the section with "except as stated below").

No weight, band, threshold, cap, penalty, knockout semantic, confidence rule, missing-value rule, golden fixture or historical record was touched. The governed map (`clean 4 / minor_civil 2 / criminal_or_regulatory 0`) is asserted unchanged by the new tests, and the golden hash `e84f8bc0f9b9…` is intact.

## 4. The four states D-5.2 requires

| State | Representation | How it is established |
|---|---|---|
| Verified active SEBI/ED action | `sebi_ed_action_active: true` | a non-nil SEBI/ED cell in an adverse table row, a labelled count under a regulator-named category, **or** a sentence with agency + finite act + party; K2 **TRIGGERED** ⇒ `AVOID` |
| Explicitly verified absence | `sebi_ed_action_active: false` | only a negative naming **both** SEBI and the ED, with or without an act verb, and only when no positive finding exists in the range (the coverage standard that would widen this is **open**, §6.2) |
| Incomplete / inaccessible / absent coverage | field **absent** | nothing matched, page range empty, unmappable proceeding type, unparseable adverse row ⇒ K2 **UNVERIFIED**, verdict `INSUFFICIENT_DATA`, litigation points unavailable |
| Proceeding involving a Director, not the issuer | `litigation_bucket` reflects the disclosure (in scope per the formula); `sebi_ed_action_active` stays absent | evidence quote names the party group; the `notes` field lists the parties named in the quoted text so the attribution is visible without a new scored category |

## 5. HD Fire evidence and its limits (no inference beyond the retrieved pages)

From the SEBI-hosted **Abridged Prospectus** (RHP dated 5 October 2026), section **"12. Summary table of outstanding litigations"**: `Against our Directors | 2 | Nil | Nil | NA | Nil | Nil` — two **criminal** proceedings against **Directors (excluding Promoters)**; `Against our Company` and `Against our Promoters` nil across all columns; `By our Company | Nil | 3 | Nil | NA | Nil | 0.40` — three **tax** proceedings *brought by* the Company, ₹0.40 mn aggregate. No name, case number, forum or status appears in the table; the issuer is not named as an accused; the SEBI/stock-exchange column is scoped "against our Promoters in the last five years" and no ED proceeding appears.

* Supported `litigation_bucket`: **`criminal_or_regulatory`** (criterion covers promoters, directors and the company). `clean` is contradicted by the issuer's own table; `minor_civil` is excluded.
* **Does not** establish an active SEBI/ED action; `sebi_ed_action_active` for HD Fire is **UNKNOWN**, not `False`.
* **Limits:** the particulars sit on **RHP p. 356**, which is unretrievable here (the fetch path parses at most 30 pages; sandbox egress to BSE/IIFL/HD Fire fails at TLS); the final Prospectus is unavailable; the historical evaluation record `…551a7eab` is absent. **HD Fire source-level acceptance remains outstanding** and is not claimed by this record.

## 6. Open decisions — RAMKI choice required (this section is a proposal, not a rule)

**6.1 Party-coverage standard for `clean`.** Does an express nil that names only some of the population (e.g. "our Company and its Promoters", omitting Directors/KMP/Senior Management) satisfy `clean`?
* **A (current behaviour):** accept the filer's own sentence; the covered parties are recorded in `notes`. *Consequence:* 4/4 stands on partial party coverage; the gap is visible in evidence but not in the score.
* **B:** require Company **and** Promoters **and** Directors. *Consequence:* filings whose nil names fewer parties move from `SCORED 4/4` to `UNKNOWN` (−4 earned, −4 available) — e.g. it would reduce a favourable award on a partial statement, and would make `clean` mean "the disclosure covered everyone".
* **C:** require the full ICDR population (Company, Promoters, Directors, KMP, Senior Management), as the summary-table rows do. *Consequence:* prose-only disclosures almost never clear `clean`; most Indian RHPs in this repository move to UNKNOWN, which is defensible but a large availability change.
This is a change to **what satisfies a governed criterion**, so it is not implemented.

A related limitation recorded now: the ICDR column merges "**SEBI or stock exchanges**", so a stock-exchange-only disciplinary action would set the flag `True`. That is the fail-closed direction (K2 `TRIGGERED` ⇒ `AVOID`, reviewable by a human) and no committed filing exercises it, but it is a reading of the merged column, not a governed definition — resolved by the same §6.2 decision.

**6.2 Source-coverage standard for a verified regulatory absence.** Under what search may `sebi_ed_action_active = false` mean "explicitly verified absence" rather than "not found"?
* **A (current behaviour):** only a negative naming both regulators clears it; a SEBI-only negative (the wording real filings actually use, and every ICDR table's promoter-scoped SEBI column) leaves UNKNOWN. *Consequence:* K2 stays UNVERIFIED and verdicts stay `INSUFFICIENT_DATA` for filings that may well be clean.
* **B:** define a coverage set — litigation section + summary table + "Our Promoters and Promoter Group" + the statutory declarations in "Promoters" — where a nil naming SEBI, the Stock Exchanges **and** the ED (or an explicit ED-free declaration) clears the flag. *Consequence:* `False` becomes an evidenced claim on issuer-drafted text only; K2 can clear without any external register.
* **C:** require corroboration from a regulator source (SEBI order/press-release retrieval) before `False` may clear K2. *Consequence:* consistent with D-2's "no adverse finding from one document" stance, but needs the retrieval contract, a cutoff rule and an unavailable-source policy (A8 territory) before it is implementable.
Until this is decided, the asymmetry is deliberate: **True needs a finite act (or a disclosed count); False needs both regulators named; everything else is UNKNOWN.** The asymmetry is directional in the safe sense: a `True` that turns out to be a stock-exchange action rather than a SEBI one is visible and correctable, a `False` that clears K2 without coverage is silent.

**6.3 Display-layer default.** `presentation/ui7.py` renders an UNKNOWN flag as "No active SEBI or ED action" (`… if metrics.get(...) is True else "No active …"`). Presentation only, but it changes what every historical record shows in the UI, so it needs its own authority.

**6.4 Adverse counts with no governed bucket.** Tax-only or statutory/regulatory-only adverse litigation currently leaves the bucket UNKNOWN. Deciding to fold them into `criminal_or_regulatory` would be a semantic change to the criterion; deciding to fold them into `clean` would re-create the defect in a new place.

## 7. Measured effect (no historical evaluation re-run)

| Filing | Before (asserted) | After (measured, this branch) |
|---|---|---|
| R.K. Fashion | `clean` + `false` + fabricated quote; **49.0**, base 52.0, available 73, completeness 73.0, Module D 10.0/15 (unknown 2), K2 `CLEAR` | fields **absent** (UNKNOWN); **45.0**, base 48.0, available 69, completeness 69.0, Module D **6.0/15** (unknown 6), K2 **`UNVERIFIED`** `missing: ["sebi_ed_action_active"]`, verdict `INSUFFICIENT_DATA` |
| `complete_sample_rhp.pdf` | `clean` + `false`; 23.0, available 26, completeness 26.0 | absent; **19.0**, available 22, completeness 22.0 |
| `complete_sample_rhp_2.pdf` | `clean` + `false`; 21.0, available 26 | absent; **17.0**, available 22 |
| `class_a_financial_lender.pdf` | extraction said `minor_civil`, canonical said `clean` | `clean` **from the page's own express nil**; 41.0 unchanged |
| `class_b/c/d/e` | `clean` (default) | `clean` **with the filing's sentence quoted**; scores 41/43/35/35 unchanged |
| Jio live filing | `criminal_or_regulatory` + `false` + fabricated quote | `criminal_or_regulatory`, verbatim p. 464; flag **absent** |
| vishal nirmiti live PDF | `criminal_or_regulatory` + **`true` inferred from a section heading** | `criminal_or_regulatory`; flag **absent** |
| vishal golden input | 35.0, hash `e84f8bc0…` | **35.0, hash `e84f8bc0…` — unchanged** |

All deltas are the removal of a 4-point award that had no evidence, or the removal of a fabricated negative. **Implementation correction vs semantic change:** every number above comes from the correction class (§3); the deferred items (§6) are the ones that would change a governed meaning.

## 8. Verification

| Check | Result |
|---|---|
| `tests/test_litigation_regulatory_defaults.py` (new — D-5.4's nine scenarios, the structured regulatory routes and the contract pins) | **51 passed** |
| `tests/test_hd_fire_primary_source_extraction.py` | **7 passed, 0 xfailed** — the two strict D-5 xfails are replaced by passing assertions; a new test pins HD Fire's §12 table to `criminal_or_regulatory` with the Directors row quoted verbatim and no regulatory flag |
| `tests/test_rk_fashion_reconciliation.py` | **5 passed** on re-measured values (45.0 / 48.0 / 69.0 / Module D 6.0 / K2 UNVERIFIED) |
| `tests/test_ui7_ingestion.py` | passed on re-measured 19.0 and 45.0/48.0/69.0 |
| `tests/test_extraction_phase5b.py` | **9 passed** — class_* scores unchanged (41.0 / 41.0 / 43.0 / 35.0 / 35.0) and vishal 35.0; the provenance floor moved from 10 to 9 because the unevidenced SEBI/ED record no longer exists, and its absence is asserted |
| D-1…D-4 suites (going concern, contingent liabilities, promoter holding, auditor tenure/evidence, GMP policy, overlays/knockouts, acceptance matrix, fixture-fallback isolation, golden replay) | **unchanged and passing** |
| `config/`, `schema/`, `fixtures/` | **no diff**; golden hash intact |
| Historical evaluation records | not re-run, not edited, not re-hashed |
| Full backend suite on the published tree | recorded in the investigation record §8 with the progress capture |
| Expected failures | **0 `pytest.mark.xfail` remain in `tests/`** — the two strict D-5 pins became passing assertions; the deferred §6 items are undecided questions, so they are pinned by fail-closed assertions on today's behaviour rather than by expected failures |

## 9. Consequences and constraints

* An unread filing no longer scores as litigation-free; it scores as **unknown**, and K2 refuses to clear. Screening becomes stricter **only** in the sense that unsupported favourable evidence stops earning points.
* `UNKNOWN ≠ 0`: availability shrinks with the missing evidence, so the confidence band widens rather than the score collapsing to zero.
* Any future widening of the `False` path (§6.2) must be paired with a defined `True` standard, so the two remain complementary rather than asymmetric by accident.
* **HD Fire acceptance is not claimed.** Its litigation bucket is now `criminal_or_regulatory` on the strength of its own table, and its regulatory flag stays UNKNOWN because the available pages do not speak to it.

## 10. Implementation authority

The §3 corrections are published with this record on `arena/95234306-ipo-screening-engine`. The §6 items require Ramki's decision before any implementation; none of them is applied.
