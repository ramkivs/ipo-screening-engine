# A23 — Litigation and SEBI/ED Negative Defaults: Investigation and Contract-Permitted Correction

- **Decision ID:** A23 (decision **D-5** of the HD Fire / Jio decision set)
- **Title:** litigation bucket and regulatory-action flag are evidence-or-UNKNOWN; two coverage standards remain open
- **Record type:** **INVESTIGATION plus a recorded correction.** Per `handoff/decisions/CONVENTION.md` rule 4, this record is **not** an approval of the alternatives in §"Open decisions"; it separates Ramki-approved material from v1.5 requirements, Arena analysis, and unresolved proposals.
- **Decision status:** **RAMKI DECISION REQUIRED** for the two coverage standards (clean's party coverage; a verified regulatory absence). The removal of the unsupported defaults was executed under the existing contract and needed no new rule — see "What needed no approval".
- **Disposition after the 2026-10-20 continuation pass (§6A):** matters **A** (dimension coverage) and **B** (closed-period denials) produced demonstrated implementation defects and were corrected in `sections.py`; matter **C** was **investigated and found to be no defect** (the §6.3 premise was wrong and is withdrawn); matter **D** needs **no new bucket** (statutory/regulatory already maps; tax-only stays UNKNOWN). The two *coverage standards* — which parties a nil must reach (§6.1) and what search may call a regulatory absence verified (§6.2) — remain **PROPOSED / UNRESOLVED** and are **not** treated as approved authority.
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

**6.3 Display-layer default.** ~~`presentation/ui7.py` renders an UNKNOWN flag as "No active SEBI or ED action"~~ — **this sentence was wrong and is withdrawn; see §6A.3.** The original claim was checked against the repository on 2026-10-20: there is **no** `engine/ipo_screening/presentation/ui7.py` (`ls engine/ipo_screening/presentation/` → `api.py`, `ingestion_activity.py`, `models.py`, `service.py`), `find . -name "*ui7*"` matches only `tests/test_ui7_ingestion.py` (a workstream label, not a module), and `grep -rln "No active SEBI"` matches only `engine/ipo_screening/extraction/sections.py` (a comment) and `tests/test_litigation_regulatory_defaults.py`. No presentation surface renders a governance flag as an all-clear, so there was **no defect to fix**; the investigation and its evidence are in §6A.3.

**6.4 Adverse counts with no governed bucket.** *Corrected 2026-10-20:* the two halves of this sentence are not the same case. A **statutory/regulatory** adverse count is already inside the taxonomy — the bucket is literally named `criminal_or_regulatory`, and the summary-table route already reads the ICDR "Outstanding Statutory/Regulatory Proceedings" column into it (pinned by `test_d_statutory_or_regulatory_count_uses_the_existing_bucket`). Only **tax-only** (and any other type with no column of its own) leaves the bucket UNKNOWN. Deciding to fold tax into `criminal_or_regulatory` would be a semantic change to the criterion; deciding to fold it into `clean` would re-create the defect in a new place. Neither is done; see §6A.4.

## 6A. Disposition of §6 (continuation pass, 2026-10-20)

Four matters were examined against the published implementation, not against the
prose of this record. Each is reported as **finding → evidence → what changed →
status**, and no undecided question was implemented.

**6A.1 Party coverage for `clean` — one demonstrable defect fixed, the party question stays open.**

*Finding.* The prose route did treat partial coverage as comprehensive, but the
dimension that mattered in code was the **type of proceeding**, not the party: any
sentence matching an absence form set `clean` whether or not it spoke about both
halves of the bucket. A nil covering only criminal proceedings, only civil
litigation, only regulatory action, or only tax proceedings therefore earned 4/4.
The structured summary-table route already refused this (it needs the criminal,
civil and regulatory columns present before it may answer `clean`), so the two
routes disagreed with each other.
*Evidence.* Twelve-case probe over the published code: criminal-only nil,
civil-only nil and regulatory-only nil each returned `clean`; the class_a
sentence (both dimensions) and class_b ("material litigation or criminal cases")
returned `clean` correctly; a tax-only nil returned `clean`.
*Change.* `SectionExtractor._lit_absence_is_comprehensive` — a prose denial now
has to deny unqualified litigation, or litigation **and** the criminal dimension,
or the criminal **and** civil dimensions, before it can answer `clean`;
otherwise no candidate is emitted (UNKNOWN). This aligns prose with the table
route that D-5 published; it introduces no new value, no weight and no threshold.
Measured before/after pairs for the affected synthetic filings are in the §7 addendum.
*Status.* **RESOLVED for dimension coverage.** **PARTY** coverage — whether a nil
must reach Company **and** Promoters **and** Directors, or the full ICDR
population — remains a governed choice; **PROPOSED: option B**, aligned with the
wording of the criterion's own definition ("across promoters, directors and the
company"), recorded in §6.1 and not implemented. Selected `Nil` rows in the ICDR
summary table are *not* sufficient for `clean` — that is already how the table
route behaves (it reads every column, and an unreadable row does not cancel an
affirmative bucket), so no change was needed. Missing / ambiguous / unparseable
coverage is already represented as an absent field ⇒ `STATE_UNKNOWN` ⇒ points
unavailable rather than awarded, with the reason in `missing_inputs`.

**6A.2 Source coverage for a verified SEBI/ED absence — one defect fixed, the positive standard stays open.**

*Finding.* The distinction between absence-of-evidence and evidence-of-absence is
structural in the current code: nothing is emitted unless a finite adverse act or
a denial naming **both** regulators is found on the searched pages, so "no search
match" cannot become a verified absence. A real hole did exist at the other edge:
a denial scoped to a **closed period** ("…during the financial year 2023-24",
"…as on 31 March 2022") cleared `sebi_ed_action_active = False`, i.e. it answered
"no active action" with "nothing happened in a window that has closed".
*Evidence.* Probe cases B3/B4 (closed FY, closed date) both produced `False`;
B1/B2/B5 (unqualified, "as on the date of this RHP", "in the last five years")
legitimately produce `False`.
*Change.* `_REG_ABSENT_CLOSED` suppresses the `False` when the negative's stated
scope is a closed financial year / period / date window. A rolling window
("last five years" — the ICDR disclosure window) and an as-of-the-prospectus
denial still clear, because both speak to the present; the flag's own word is
"active". Unavailable / incomplete / failed sources keep their existing
representation (absent field + `missing_inputs`, and the ingestion lifecycle
values `AWAITING_SOURCE` / `UNAVAILABLE` / `STALE` / `NOT_FOUND`) — none of them
maps to `False`.
*Status.* **RESOLVED for the closed-period confusion.** **UNRESOLVED / PROPOSED**
for the positive standard. Recommended testable wording: `False` may clear K2
only from a present-scope denial naming SEBI, the Stock Exchanges and the ED,
retrieved from (i) the Outstanding Litigation section, (ii) the ICDR summary
table, (iii) "Our Promoters and Promoter Group" and (iv) the statutory
declarations in "Promoters", with every one of those pages *actually extracted
successfully* in the same ingestion run and inside the filing-date currency
window; a page that failed to extract, was not searched, or is stale marks the
absence **unverified** rather than false. Option C (external register
corroboration) stays the alternative until A8's retrieval contract exists. This
is a coverage/scoring decision and is explicitly **not approved**.

**6A.3 `ui7.py` UNKNOWN display — no defect; the record was wrong, not the code.**

*Finding.* Nothing in the presentation layer converts UNKNOWN / missing / null /
unverified into a favourable reading, and no `ui7.py` exists.
*Evidence (all read this pass).* `frontend/app.js::renderMetricValue(val, state)`
returns `<span class="badge badge-unknown">UNKNOWN</span>` whenever
`state === 'UNKNOWN'` or the value is null/undefined, and `N/A` only for
`NOT_APPLICABLE`; booleans render literally as `<code>True</code>` /
`<code>False</code>` with no wording asserting an all-clear.
`renderSemanticStateBadge` keeps SCORED / UNKNOWN / NOT_APPLICABLE distinct.
Knockout cards render `CLEAR` / `TRIGGERED` / `badge-unverified`, and
`service.py` defaults a missing knockout state to `"UNVERIFIED"` (never
`CLEAR`); `models.py` documents that state as `CLEAR, TRIGGERED, UNVERIFIED`.
`grep -rln "No active SEBI"` over the repository matches only `sections.py` and
its test. The adverse / verified-absence / insufficient-evidence distinction
therefore survives display.
*Change.* No code change (none was warranted). Added
`frontend/test/app.test.js` — "Governance metric rendering keeps UNKNOWN
distinct from a verified absence" — pinning adverse vs verified-absence vs
null/UNKNOWN rendering, the absence of any all-clear wording, the state badge,
and that a missing verdict renders UNKNOWN rather than a pass.
*Status.* **RESOLVED — documented as no-defect**, with the inaccurate §6.3 claim
withdrawn above.

**6A.4 Tax and statutory-only proceedings — no new bucket, no `clean`.**

*Finding.* Buckets are defined in exactly three places and all three agree: the
schema enum, `config_validation.py` (which rejects anything but the three), and
`builder.py::_LITIGATION_BUCKET_ALIASES`; the taxonomy is
`clean / minor_civil / criminal_or_regulatory`. Direction matters and is already
handled: only proceedings *against* the issuer or its parties are adverse —
issuer-initiated ("By our Company") rows are non-adverse by rule — and a nil in a
column scoped to a subset (HD Fire's SEBI column is "against our Promoters")
clears nothing.
*Gap that is genuinely unmappable:* adverse **tax-only** exposure has no bucket of
its own. It is not forced into `criminal_or_regulatory` (that would invent a
scored category) and it never earned `clean`: after §6A.1 a tax-only nil emits
nothing, and an adverse tax count already blocked `clean` without inventing a
category.
*Status.* **RESOLVED for the boundary; UNRESOLVED for the policy.** Recommended
resolution, to be decided separately: either fold tax/statutory-only adverse
proceedings into `criminal_or_regulatory` by explicit definition (cheapest, but
it makes a tax demand equivalent to a criminal case), or add a fourth governed
bucket, which requires a schema change, a `config_validation` change, an overlay
mapping and a re-pinned golden fixture — i.e. its own decision record, not this
one. Until then tax-only exposure stays UNKNOWN and the tracker records it as a
known coverage gap.

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

**Addendum for §6A.1 (continuation pass — the table above is the D-5 record and is not edited retroactively).** Both columns were measured on this tree and on
`10b100a` respectively, under identical conditions (`extract_from_pdf(..., allow_fixture_fallbacks=True)` then
`evaluate(..., mode="final", evaluation_datetime=2026-10-05T12:00:00Z)`, i.e. exactly what the tests do), so the pairs are comparable with each other; the "Before"
column above reports the D-5 pass's own measurement path and differs for class_a for that reason, not because of this pass.

| Filing | Litigation sentence (verbatim substance) | Before (published code) | After (this pass) |
|---|---|---|---|
| `class_a_financial_lender.pdf` p. 11 | criminal **and** material civil, named parties | `clean`; 40.0, available 54.0, Module D 6.0, unknown 2.0 | **identical** — `clean`; 40.0, 54.0, 6.0, 2.0 |
| `class_b_cyclical_manufacturing.pdf` p. 10 | "material litigation **or criminal cases**" | `clean`; 41.0, 55.0, 6.0, 6.0 | **identical** — `clean`; 41.0, 55.0, 6.0, 6.0 |
| `class_c_epc_infrastructure.pdf` p. 10 | criminal + SEBI/Stock-Exchange disciplinary **only** | `clean`; 41.0, 55.0, 6.0, 6.0 | **absent (UNKNOWN)**; 37.0, 51.0, 2.0, 10.0 |
| `class_d_loss_making_tech.pdf` p. 10 | "No criminal or active regulatory proceedings" **only** | `clean`; 28.0, 41.0, 6.0, 6.0 | **absent (UNKNOWN)**; 24.0, 37.0, 2.0, 10.0 |
| `class_e_modern_complex_rhp.pdf` p. 9 | criminal + SEBI/Stock-Exchange regulatory **only** | `clean`; 43.0, 55.0, 6.0, 6.0 | **absent (UNKNOWN)**; 39.0, 51.0, 2.0, 10.0 |
| `complete_sample_rhp.pdf` / `_2.pdf` | no absence sentence at all | absent | absent — unchanged |
| Jio (591 pp.), vishal nirmiti (551 pp.), R.K. Fashion | adverse rows present / unread litigation section | `criminal_or_regulatory` (pp. 464 / 439, verbatim), flag absent; RK fields absent | **unchanged** — re-measured this pass, same pages, same quotes, flag still absent |
| vishal golden record | — | 35.0, hash `e84f8bc0…` | **35.0, hash `e84f8bc0…` — unchanged** |

Every moved number is −4 points of *earned* score **and** −4 of *available* score: the criterion stops being paid for unevidenced coverage, it does not become an adverse finding. `tests/test_extraction_phase5b.py` was re-measured (not hand-adjusted) and now also pins `canonical["governance"]["litigation_bucket"] is None` for class_c and class_e with the reason in a comment.

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

**Addendum — verification of the §6A disposition pass (all executed 2026-10-20 on the tree published by this pass).**

| Check | Result |
|---|---|
| `tests/test_litigation_regulatory_defaults.py` | **66 passed** (51 from D-5 + 15 new: 4 dimension-scoped-nil cases, 4 comprehensive-nil cases, the unrecognised-wording limitation, 3 closed-period regulatory denials, 3 present/rolling-window denials, and the statutory/regulatory mapping pin) |
| `tests/test_hd_fire_primary_source_extraction.py` | **7 passed** — HD Fire's §12 shapes re-confirmed against the corrected code (Directors' 2 criminal proceedings survive the nil rows; no SEBI/ED finding in either direction; the `By our Company` tax rows never read as `clean`) |
| `tests/test_extraction_phase5b.py` | **9 passed** on re-measured values — `class_c` 41.0 → **37.0**, `class_e` 43.0 → **39.0** (each −4 earned, −4 available, because their disclosure denies one dimension only), with `litigation_bucket is None` pinned and the reason in a comment; `class_a`/`class_b` keep `clean`; vishal stays 35.0 |
| Affected-module battery (the 7 extraction/governance modules above, 138 tests) | **138 passed**, 262.67 s |
| `tests/test_rk_fashion_reconciliation.py`, `tests/test_vishal_golden.py`, `tests/test_extraction.py`, `tests/test_ui7_ingestion.py` | passed inside that battery — no pinned value was moved except the two re-measurements above |
| `frontend` node harness (`node --test test/*.test.js`) | **90 passed, 0 failed** in 702 ms (89 before this pass; the new test is §6A.3's display-state pin) |
| Full backend suite | **1265 collected, 1265 passed, 0 failed, 0 skipped, 0 xfailed, 25 warnings, 1131.26 s (18 m 51 s)**, exit 0 — a completed run, not an interrupted one, with the runner-level progress lines from `tests/pytest_progress.py` throughout. The run's log is committed (`docs/investigation/D-5-A23-SUITE-PROGRESS-2026-10-20.log`: 132 progress lines + the summary + `EXIT=0`); root cause and stage breakdown are in `docs/RUNBOOK.md` §17 |
| `config/`, `schema/`, `fixtures/`, `build/evaluations/`, `evidence/`, historical records | **no diff**; vishal golden hash `e84f8bc0…` verified by the golden tests in that run |

## 9. Consequences and constraints

* An unread filing no longer scores as litigation-free; it scores as **unknown**, and K2 refuses to clear. Screening becomes stricter **only** in the sense that unsupported favourable evidence stops earning points.
* `UNKNOWN ≠ 0`: availability shrinks with the missing evidence, so the confidence band widens rather than the score collapsing to zero.
* Any future widening of the `False` path (§6.2) must be paired with a defined `True` standard, so the two remain complementary rather than asymmetric by accident.
* **HD Fire acceptance is not claimed.** Its litigation bucket is now `criminal_or_regulatory` on the strength of its own table, and its regulatory flag stays UNKNOWN because the available pages do not speak to it.

## 10. Implementation authority

The §3 corrections are published with this record on `arena/95234306-ipo-screening-engine`. The §6 items require Ramki's decision before any implementation; none of them is applied.
