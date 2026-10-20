# D-5 — Litigation and Regulatory-Action Evidence Defaults

- **Date:** 2026-10-20 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** branch `arena/95234306-ipo-screening-engine` at remotely verified commit `2d52baa56cbb4b82061649106745f79d04d9fce6`
- **Scope:** decision **D-5** of the HD Fire / Jio decision set — `governance.litigation_bucket` and `governance.sebi_ed_action_active` as produced by the deterministic PDF extraction path
- **Status:** implementation of the *unsupported-negative* correction is complete and tested; the two items that require a governed definition are **deferred** and recorded in `handoff/decisions/A23-litigation-regulatory-evidence-defaults.md` as an investigation (not an approval)
- **Authority note:** the v1.5 specification remains authoritative. Nothing here changes a criterion formula, weight, threshold, knockout semantic, confidence rule or missing-value rule; `config/`, `schema/` and `fixtures/` are untouched.

## 0. Verified starting state

Every statement below was checked against the remote repository and the working tree at `2d52baa` before any file was edited.

| Item | Verified value |
|---|---|
| `main` | `01ba66c12ca1195fd7acbd287c3e39a019808094` (untouched throughout) |
| PR #6 | `OPEN`, `merged: false`, `mergedAt: null`, `mergeable: true`, head `e05c0ef`, base `arena/573e69a4-ipo-screening-engine` (not `main`) |
| Default branch | `main`; `has_issues: true`; no hosted CI workflows |
| Session branch head at pass start | `2d52baa` |
| Golden fixture | `fixtures/vishal_nirmiti/input.json` states `governance.litigation_bucket = "criminal_or_regulatory"`, `sebi_ed_action_active = false`; golden hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` |
| Test suite at `2d52baa` | **1196 passed, 2 xfailed**, 38 warnings, 1095.32 s |
| D-5 pins at `2d52baa` | two **strict** xfails in `tests/test_hd_fire_primary_source_extraction.py` naming decision D-5 |
| Governance extraction code | `engine/ipo_screening/extraction/sections.py` lines 1688–1732 |
| Canonical coercion | `engine/ipo_screening/extraction/builder.py` lines 315–321 and 336 |

## 1. Root cause and exact code paths

Two layers turned *absence of extraction* into a favourable fact, and a third layer made the favourable value unavoidable.

**1.1 `sections.py` — the defaults were assigned before the scan and emitted after it, whatever the scan found (lines 1691–1732 at `2d52baa`):**

```python
lit_range = page_ranges.get("litigation") if page_ranges else None
p_lstart, p_lend = lit_range or (430, min(500, self.page_count))

lit_bucket = "clean"          # ← favourable bucket assumed
sebi_active = False           # ← no regulatory action assumed
found_lit_page = p_lstart

for p in range(p_lstart, p_lend + 1):
    txt = self.extract_page_text(p)
    if re.search(r'criminal proceedings against our promoters|r\.c\.c\.|criminal complaint', txt, re.IGNORECASE):
        lit_bucket = "criminal_or_regulatory"; found_lit_page = p; break
    elif re.search(r'material civil litigation|civil suit', txt, re.IGNORECASE):
        lit_bucket = "minor_civil"; found_lit_page = p

extractions.append(RawExtraction(field_path="governance.litigation_bucket",
    candidate_value=lit_bucket, ..., quote=f"Litigation bucket classified as: {lit_bucket}",
    quote_is_processing=True, ...))
extractions.append(RawExtraction(field_path="governance.sebi_ed_action_active",
    candidate_value=sebi_active, ..., quote="No active SEBI or ED regulatory proceedings", ...))
```

Six defects compose here:

1. **Absence of extraction ⇒ proof of none.** If the loop matched nothing — including when the range is empty, which is the default for any document shorter than 430 pages or without a `page_ranges["litigation"]` map — the bucket is still `"clean"`. `clean` is the favourable end of a scored criterion, so an unread section earns **4/4**.
2. **A fabricated negative, presented as a quotation.** `sebi_ed_action_active` was `False` with `quote="No active SEBI or ED regulatory proceedings"` and **without** `quote_is_processing=True`. That sentence appears in no filing. This is the same defect class D-4 removed from the auditor fields.
3. **The regexes were case-*insensitive* but phrase-*bound*:** three literals for criminal, two for civil. The statutory ICDR disclosure shapes (a summary table of counts per party group and proceeding type, and a labelled "category / Nil / 2" list) were invisible to them — so a filing that *discloses* two criminal proceedings against Directors read as `clean`.
4. **No polarity test.** `re.search(r'material civil litigation|…')` matches "there are **no** outstanding criminal proceedings or material civil litigation involving our Company", so an express denial classified as `minor_civil` — an adverse finding invented from its own negation.
5. **The page recorded was the scan start**, not a page that was matched, so the citation pointed wherever the range happened to begin.
6. **The flag was inferred neither way from evidence:** `False` was not "no SEBI/ED action found after a defined search", it was "the initialiser".

**1.2 `builder.py` — the coercion that destroyed evidenced findings (lines 315–321, 336 at `2d52baa`):**

```python
lit = gov_base["litigation_bucket"] if "litigation_bucket" in gov_base \
      else self._get_field("governance.litigation_bucket", "clean")
if lit in ("none", None, "clean"):       lit = "clean"
elif lit in ("material_civil", "civil"): lit = "minor_civil"
elif lit != "criminal_or_regulatory":    lit = "clean"   # ← every other value becomes clean
…
"sebi_ed_action_active": _pick_gov("sebi_ed_action_active", False),
```

Fixing `sections.py` alone would therefore have changed nothing: an evidenced `minor_civil` was rewritten to `clean` on the way into the canonical input. Measured at `2d52baa`, `fixtures/filings/class_a_financial_lender.pdf` p. 11 produced `RawExtraction(governance.litigation_bucket, "minor_civil")` whose own note read `PROCESSING_SUMMARY: Litigation bucket classified as: minor_civil`, while the canonical input carried `clean` — the extraction and the scored input disagreed, and the more favourable one won.

**1.3 Consequences in the scoring path (read, not changed):** `derived.py` maps `governance.litigation_bucket` to `metrics.litigation_bucket` (`None` ⇒ `UNKNOWN`) and `governance.sebi_ed_action_active` to `metrics.sebi_ed_action_active` (`None` ⇒ `UNKNOWN`). `scoring.py` turns an UNKNOWN criterion into *unavailable* rather than zero points (`effective` only counts `state == "SCORED"`, `unknown_points` accumulates the criterion's `max`, and the confidence model subtracts `unknown_penalty = 10 × unknown / 25`). `knockouts.py::_litigation_and_regulatory` (K2) lists both inputs in `required`; a missing input yields **UNVERIFIED, never CLEAR**, and because `sebi_ed_action_active` is in `config.critical_data.items`, its absence also forces verdict `INSUFFICIENT_DATA`. So the engine already had the right destination for "not established"; the extractor was simply never allowed to send anything there.

## 2. Contract findings — no new category was needed

| Question (D-5.1 / D-5.2) | Contract answer | Source |
|---|---|---|
| What do the buckets mean? | `clean` / `minor_civil` / `criminal_or_regulatory`, scored 4 / 2 / 0 by a `categorical` rule on metric `litigation_bucket` | `config/ipo-config.v1.5.0.json`, criterion `litigation` (Module D, max 4) |
| Is UNKNOWN supported? | **Yes.** The input field is `"enum": ["clean","minor_civil","criminal_or_regulatory",null]`; `null`/absent ⇒ `STATE_UNKNOWN` with reason "the litigation status of the promoters, directors and company is not established"; `config_validation.py:53` requires exactly those three *known* keys, so adding a fourth value (`"unknown"`) would violate the governed map | `schema/ipo-input.v1.5.schema.json`; `scoring.py::categorical_points` + `resolve_value`; `config_validation.py:53` |
| Issuer vs director attribution | The criterion's own formula is *"clean / minor_civil / criminal_or_regulatory **across promoters, directors and the company**"* ⇒ a proceeding against a Director is inside the governed population; there is **no** separate issuer-only field, so the distinction is carried by evidence text and the `notes` ("parties named in the quoted text"), not by a scored category | `config/…v1.5.0.json` (`litigation.formula`); `spec/…v1.5…md` lines 240–256 |
| Pending / disposed / criminal / civil / regulatory representation | Pending-ness is not a scored dimension; the disclosed *type* selects the bucket (criminal or regulatory → 0, material civil → 2, express nil → 4). Disposed matters remain in the bucket if the filing counts them. Statutory/regulatory/tax proceedings have **no** governed bucket, so a filing whose only adverse count is of that kind must not be resolved to `clean` | v1.5 spec governance criteria; ICDR "Summary table of outstanding litigation" column set |
| Is absence-of-extraction proof-of-none? | **No.** `metric_present` treats only `None`/`""` as absent, and `_UNRESOLVED_INPUTS` (`[●]`, `NA`, `Nil`, …) as unknown; `litigation_bucket` is in `critical_data.items` and in K2's `required` list — i.e. the contract expects "unknown" to be expressible and consequential | `metrics.py`; `derived.py:2225`; `knockouts.py` |
| Does a criminal proceeding imply a SEBI/ED action? | No — they are different inputs: the bucket is `categorical`, the flag is `boolean | null` and K2 tests only the flag | as above |

All four states D-5.2 asks for are therefore already representable:

| State | Representation after the fix |
|---|---|
| verified active SEBI/ED action | `sebi_ed_action_active = true` + verbatim sentence + page ⇒ K2 **TRIGGERED**, verdict `AVOID` |
| explicitly verified absence | `sebi_ed_action_active = false` **only** from a negative that names both regulators, quoting that sentence (the source-coverage standard itself is deferred, §5) |
| incomplete / inaccessible / absent evidence | field **absent** ⇒ UNKNOWN ⇒ K2 **UNVERIFIED**, verdict `INSUFFICIENT_DATA`, points unavailable rather than awarded |
| proceeding involving a Director rather than the issuer | reaches `litigation_bucket` (in scope per the formula) with the party group quoted in the evidence and `notes`; it does **not** set the regulatory flag |

## 3. What was changed (narrowest correction)

**`engine/ipo_screening/extraction/sections.py::extract_governance`** — the litigation block now resolves the bucket from evidence, in this order, and emits **nothing** if no route yields a finding:

1. **prose sentences** (strongest applicable bucket wins: criminal/regulatory before material civil); a sentence is *adverse* only if it names a party **and** is not negated — the negation window is measured up to the agency token so "there are no outstanding criminal proceedings…" is an absence, not a finding;
2. the **ICDR summary table** (`Category | Criminal | Tax | Statutory or Regulatory | Disciplinary actions by SEBI or stock exchanges… | Material civil litigation | Aggregate amount`): rows whose label begins "against" are adverse; a numeric count in the criminal or regulatory column ⇒ `criminal_or_regulatory`, in the civil column ⇒ `minor_civil`, `Nil`/`NA`/`—` ⇒ nil; a row that cannot be parsed, or a proceeding type the header does not carry, means **coverage is incomplete ⇒ UNKNOWN**, never `clean`; rows "by our Company/Directors/Promoters" (receivables) are never adverse;
3. the **labelled list** form ("a) Criminal proceedings against the Company / Nil"), including the regulator named between the proceeding type and the party ("(d) Disciplinary actions by SEBI … involving our Company / Nil");
4. an **express absence statement** ⇒ `clean`, with the sentence quoted verbatim and the party groups it names recorded in `notes`.

**`sebi_ed_action_active`** is emitted `True` only from a non-nil SEBI/ED cell in an "against" row, or from a sentence naming the agency **and** a finite act (`initiated | issued | passed | imposed | conducted | attached | registered | taken | served | filed | raised | recorded | framed`, or "… pending before SEBI") **and** a party, excluding registration/disclaimer boilerplate and excluding negations; `False` only from an explicit negative naming **both** SEBI and the Enforcement Directorate. Everything else: no field.

**Structural masking.** Table headers, separator rows, the table block's own rows and bare category headings are blanked (offset-preserving) before prose scanning, so a *column label* ("Material civil litigation", "Disciplinary actions by SEBI…") or a *section heading* can no longer be read as a finding. Quotations are sliced from the **unmasked** page, so every emitted `quote` is a verbatim substring of the cited page.

**`engine/ipo_screening/extraction/builder.py::_build_governance`** — no default, no rewriting: the extracted/input value is normalised through an explicit alias table (`none`/`nil`/`no_litigation`→`clean`, `civil`/`material_civil`→`minor_civil`, `criminal`/`regulatory`→`criminal_or_regulatory`) and anything unrecognised becomes `None` (UNKNOWN) instead of `clean`; `sebi_ed_action_active` defaults to `None`.

**Not changed:** `derived.py`, `scoring.py`, `knockouts.py`, `penalties.py`, `confidence.py`, `eligibility.py`, `config/`, `schema/`, `fixtures/`, the golden hash, and every historical evaluation record. `presentation/ui7.py`'s display-only fallback for `sebi_ed_action_active` is untouched and out of scope for this decision (recorded in §5.3).

## 4. HD Fire source evidence (D-5.3)

**Document.** "HD Fire Protect Limited — Abridged Prospectus", SEBI-hosted:
`https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/HD%20Fire%20Protect%20Limited-Abridged%20Prospectus_p.pdf`, referring to a Red Herring Prospectus dated **5 October 2026**.
**Retrieved** 2026-10-20 through the agent's page-fetch path (direct sandbox egress fails with TLS `SSL_ERROR_SYSCALL`); the fetcher parses at most 30 pages of a PDF, which is why the RHP body is unavailable (see *Limits*).

**Section.** "**12. Summary table of outstanding litigations**" of the Abridged Prospectus. Its closing note reads: *"For details of outstanding litigation, see 'Outstanding Litigation and Material Developments' beginning on **page 356 of the Red Herring Prospectus**."*

**Table as published** (column order and cell values verbatim; line breaks follow the rendered table):

| Category of individuals / entities | Criminal Proceedings | Tax Proceedings | Statutory or Regulatory Proceedings | Disciplinary actions by SEBI or stock exchanges against our Promoters in the last five years, including outstanding action | Material civil litigation# | Aggregate amount involved* (₹ in million) |
|---|---|---|---|---|---|---|
| *Company* (heading) | | | | | | |
| Against our Company | Nil | Nil | Nil | NA | Nil | Nil |
| By our Company | Nil | 3 | Nil | NA | Nil | 0.40 |
| *Directors (excluding Promoters)* (heading) | | | | | | |
| **Against our Directors** | **2** | Nil | Nil | NA | Nil | Nil |
| By our Directors | Nil | Nil | Nil | NA | Nil | Nil |
| Against our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |
| By our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |

`#` In accordance with the Materiality Policy. `*` To the extent quantifiable.

**Recorded findings, strictly as disclosed:**

* **Named party and role as stated:** "Against our **Directors**", under the group heading "**Directors (excluding Promoters)**". No individual director is named in this table; no company, complainant, case number, forum, filing date or status is given.
* **Proceeding type and status as stated:** **Criminal Proceedings = 2**. The table states a count only — it does not say whether either proceeding is pending, disposed, or settled.
* **Is the issuer itself named as an accused?** **No.** The "Against our Company" row is `Nil` in every column, and "By our Company" carries **3 tax proceedings** for **₹0.40 million** in aggregate — proceedings *brought by* the issuer (receivables-side), not against it.
* **Does this establish an active SEBI or ED action?** **No.** The SEBI/stock-exchange disciplinary column is scoped *"against our Promoters in the last five years"* and reads `Nil`; the same column is `NA` for the Company and Director rows. No Enforcement Directorate proceeding appears anywhere in the retrieved pages. **Nothing about the issuer's or its Directors' SEBI/ED position is established by this section — in either direction.**
* **Which existing `litigation_bucket` value does the evidence support?** **`criminal_or_regulatory`**, because the governing formula covers *"promoters, directors and the company"* and the Directors row is a non-nil criminal count. `clean` is **contradicted by the issuer's own table**; `minor_civil` is excluded (the material-civil column is `Nil` for every adverse row). The tax count maps to no governed bucket and is not used to justify any value.
* **What the engine does with it under D-5:** bucket `criminal_or_regulatory` (0/4, quote = the Directors row verbatim, page = the page carrying the table); `sebi_ed_action_active` **not emitted** ⇒ UNKNOWN ⇒ K2 **UNVERIFIED** (not CLEAR, not TRIGGERED).
* **Pre-fix behaviour for the same published text:** `litigation_bucket = "clean"` (4/4) and `sebi_ed_action_active = False` with the fabricated quotation — i.e. the engine awarded the maximum to a filing that discloses criminal proceedings, and cleared a critical-data knockout with a sentence the filing does not contain.

**Limits — what is *not* claimed.**
1. **RHP p. 356 (the particulars) is unavailable**: the fetch path caps at 30 pages, the BRLM/IIFL-hosted RHP was only obtainable for pp. 1–30, and no mirror is reachable from the sandbox. The identities, forums, status and amounts of the two Director proceedings are **UNRESOLVED**; no inference about them is made here.
2. The **final Prospectus** (which would fill the `[●]` placeholders and any updates after 5 October 2026) is unavailable.
3. The historical HD Fire evaluation record `…551a7eab` (documented 7/100) remains **absent** from this repository and all 17 branch trees, so the score-level effect on that record is stated as arithmetic only; **no historical evaluation was re-run, edited or re-hashed**.
4. Consequently **HD Fire acceptance remains incomplete** — this pass establishes litigation/regulatory *source evidence and the engine's treatment of it*, not full source-level acceptance.

## 5. Deferred: decisions that require a governed choice

These are recorded, **not** silently resolved (A23 is an investigation record).

**5.1 Party-coverage standard for `clean`.** Should an express nil that names only some of the population — "no outstanding litigation involving our Company and its Promoters" — clear the bucket when Directors/KMP/Senior Management are not named? Current behaviour: `clean` is emitted and the *covered* parties are listed in `notes`, so the gap is visible but does not change the 4 points.
*Option A (status quo, evidence-visible):* accept the filer's own sentence as the disclosure. *Option B:* require the sentence or table to name Company **and** Promoters **and** Directors, else UNKNOWN. *Option C:* require the full ICDR population (Company, Promoters, Directors, KMP, Senior Management).
Consequence to weigh: B and C move filings that today earn 4/4 to UNKNOWN (−4 earned, −4 available), which is a change in *how a governed criterion is satisfied*, not in the map.

**5.2 Source-coverage standard for a verified absence.** `sebi_ed_action_active` is defined over **SEBI and the Enforcement Directorate**, while every prospectus disclosure D-5 can see is scoped to *SEBI, the Stock Exchanges and (sometimes) the RBI*. Current behaviour: only a negative naming **both** SEBI and the ED clears the flag; a SEBI-only negative leaves it UNKNOWN, and K2 stays UNVERIFIED. To let `False` mean "explicitly verified absence" as D-5.2 phrases it, the project must define (i) the pages/sections that must be searched (the litigation section, the summary table, "Our Promoters and Promoter Group", the statutory declarations in "Promoters", and/or an external regulator register), and (ii) whether a nil inside one issuer-drafted section counts as a verification at all. Absent that definition, a *favourable* `False` would just replace an *unfavourable* default.

**5.3 Display-layer default.** `presentation/ui7.py` renders `metrics.sebi_ed_action_active` through `if metrics.get(...) is True else "No active …"`, so UNKNOWN displays as "No active SEBI or ED action". This is presentation text, not a scored input, and changing it alters what users see for every historical record in the UI; it needs its own authority.

**5.4 Regulatory proceeding types that have no bucket.** An adverse count that is only *tax* or only *statutory/regulatory* (not SEBI/ED, not criminal, not civil) currently leaves the bucket UNKNOWN, because no governed bucket covers it. A decision is needed on whether such matters belong to `criminal_or_regulatory` (semantic change to the criterion) or remain UNKNOWN.

**5.5 No positive-only `True` asymmetry to fix.** `sebi_ed_action_active = True` requires a finite act and a party; there is deliberately no heuristic that sets it from "a criminal proceeding exists". Any future widening of the `True` path should be paired with 5.2, so that `True`/`False` mean complementary things under one coverage standard.

## 6. Measured impact on the committed fixtures

Live extraction (`DocumentExtractor().extract_from_pdf(path, allow_fixture_fallbacks=False)`), before = the state pinned at `2d52baa`, after = measured on this branch:

| Filing | Litigation before → after | SEBI/ED before → after | final score before → after | available before → after | completeness before → after | Module D before → after | verdict |
|---|---|---|---|---|---|---|---|
| `handoff/reference/…R.K Fashion accessories.pdf` (168 pp.) | `"clean"` (default, no page read) → **absent (UNKNOWN)** | `false` + fabricated quote → **absent** | **49.0 → 45.0** | 73 → **69** | 73.0 → **69.0** | 10.0/15 (unknown 2) → **6.0/15 (unknown 6)** | `INSUFFICIENT_DATA` (unchanged) |
| `fixtures/filings/complete_sample_rhp.pdf` | `"clean"` → **absent** | `false` + fabricated quote → **absent** | **23.0 → 19.0** | 26 → **22** | 26.0 → **22.0** | 5.0/15 → **1.0/15** | unchanged |
| `fixtures/filings/complete_sample_rhp_2.pdf` | `"clean"` → **absent** | `false` + fabricated quote → **absent** | **21.0 → 17.0** | 26 → **22** | 26.0 → **22.0** | 5.0/15 → **1.0/15** | unchanged |
| `class_a_financial_lender.pdf` | `minor_civil` extracted → **`clean` evidenced** (builder no longer rewrites it; the page's own sentence is an express nil) | `false` + fabricated quote → **absent** | 41.0 → **41.0** | unchanged | unchanged | unchanged | unchanged |
| `class_b/c/d/e` (synthetic RHPs) | `"clean"` (default) → **`clean` with the filing's own sentence quoted**, page 10/10/10/9 | `false` → **absent** | 41 / 43 / 35 → **unchanged** | unchanged | unchanged | unchanged | unchanged |
| `evidence/non-authoritative/jio/…JIO.pdf` (591 pp.) | `criminal_or_regulatory` → **`criminal_or_regulatory`** (same value, now verbatim-quoted from p. 464) | `false` + fabricated quote → **absent** | historical record not re-run (arithmetic: no change; bucket already favourable-to-adverse) | — | — | — | — |
| vishal nirmiti PDF | `criminal_or_regulatory` → **`criminal_or_regulatory`** (p. 439) | **`false` read off the section heading "(d) Disciplinary actions by SEBI and / or the Stock Exchanges involving our Company" → absent** | 35.0 → **35.0** | unchanged | unchanged | unchanged | unchanged |
| `fixtures/vishal_nirmiti/input.json` (golden) | `criminal_or_regulatory` → **identical** | `false` → **identical** | **35.0, hash `e84f8bc0…` — unchanged** | 73 | 73.0 | 5.0/15 | `INSUFFICIENT_DATA` |

Reading the table:

* **No scoring semantics moved.** Every delta above comes from *one* bucket changing between `SCORED` and `UNKNOWN` (4 points, earned and available) or from a fabricated `False` becoming absent. The 35.0 / hash of the golden record is bit-for-bit intact, and the two −4 moves (R.K. Fashion, complete samples) are the *removal of points that were never earned*.
* **UNKNOWN ≠ 0.** The corrected filings do not score 0 for litigation; their litigation points become unavailable, which is why `available` falls by 4 (69 instead of 73 for R.K. Fashion) while the score falls by 4.
* **K2 honesty improved without changing K2.** R.K. Fashion's K2 moved from `CLEAR` (cleared by a defaulted flag) to `UNVERIFIED` with `missing: ["sebi_ed_action_active"]`; the verdict was already `INSUFFICIENT_DATA`, so no verdict flips in the committed set.
* **The class_* filings demonstrate the polarity fix**: they used to reach `clean` *via* a mis-parsed `minor_civil` (two wrongs cancelling), and now reach `clean` directly from the express nil, with the sentence itself as the quotation.

## 7. Tests

* **New:** `tests/test_litigation_regulatory_defaults.py` — **44 cases** covering all nine required D-5.4 scenarios: no litigation evidence (including an empty page range); explicitly documented clean (three forms: express sentence, negated civil wording, all-nil summary table); issuer-level proceeding (prose and table row); Director-only proceeding (HD Fire's §12 table verbatim) and the "by our Company" non-adverse direction; criminal ≠ SEBI/ED action (plus tax/civil); explicit active action (four wordings, parametrised) and K2 `TRIGGERED` ⇒ verdict `AVOID`; missing / inaccessible / ambiguous coverage (SEBI-only negative, promoter-scoped nil column, heading, boilerplate, empty range ⇒ K2 `UNVERIFIED`, verdict `INSUFFICIENT_DATA`, end-to-end on `complete_sample_rhp.pdf`); no synthesised quotation (verbatim-substring check over a six-text battery **plus** a source-level pin that neither fabricated sentence may return in code); and no accidental scoring change (governed map asserted as `clean 4 / minor_civil 2 / criminal_or_regulatory 0`, schema enums unchanged, three scored buckets unchanged, UNKNOWN ≠ 0, golden 35.0 + hash `e84f8bc0…`, builder alias/`None`/unrecognised-value and input-override behaviour).
* **Converted strict xfails → passing:** `test_litigation_bucket_is_not_clean_without_evidence` (now asserts the field is absent) and `test_sebi_action_default_quote_is_not_presented_as_source_text` (now asserts **no record at all**, i.e. no quote to misread). A third test was added to the same module pinning HD Fire's §12 table: `criminal_or_regulatory`, page 12, verbatim Directors row, `sebi_ed_action_active` absent.
* **Pinned expectations re-measured, not hand-edited:** `tests/test_rk_fashion_reconciliation.py` (litigation/SEBI fields ⇒ `None`; final 49.0 → **45.0**, base 52.0 → 48.0, completeness 73.0 → 69.0, lower bound 36.0 → 32.0, Module D 10.0 → 6.0 with `unknown_points` 6.0; new assertions for `litigation` UNKNOWN and K2 `UNVERIFIED` with `missing == ["sebi_ed_action_active"]`); `tests/test_ui7_ingestion.py` (complete-sample 23.0 → **19.0** in two places; R.K. Fashion 49.0 → **45.0**, base 52.0 → 48.0, completeness 73.0 → 69.0).
* **Unchanged and still passing** (evidence that the correction did not leak): `test_extraction_phase5b.py` (class_a 41.0, class_b 41.0, class_c 43.0, class_d/e 35.0), `test_extraction.py` (vishal 35.0), `test_fixture_fallback_isolation.py`, `test_golden_replay.py`, `test_overlays_knockouts.py`, `test_acceptance_matrix.py`, `test_jio_score_bridge.py`, and the D-1…D-4 suites (`test_going_concern_negative_disclosure.py`, `test_contingent_liabilities_extraction.py`, `test_promoter_holding_extraction.py`, `test_auditor_tenure_defaults.py`, `test_auditor_evidence_section.py`, `test_d1_d3_gmp_source_policy.py`).
* **Exact full-suite result:** see §8 — recorded after the final tree, with the progress bar captured in `build`-free log `/home/user/final_after_d5.log`.

## 8. Publication and independent verification

Recorded after the commit and push; the SHA below is the one returned by `git ls-remote` for `arena/95234306-ipo-screening-engine`, not merely a local `git rev-parse`.

* **Implementation + tests + records commit:** `__COMMIT_SHA__`
* **Remote verification:** `git ls-remote origin refs/heads/arena/95234306-ipo-screening-engine` → `__COMMIT_SHA__` (identical).
* **Full backend suite on the published tree:** `__SUITE_RESULT__`
* **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094` — unchanged. **PR #6:** `OPEN`, `merged: false`, `mergedAt: null`, head `e05c0ef`, base `arena/573e69a4-ipo-screening-engine` — neither moved nor merged.
* **Protected artifacts:** `git diff --stat 2d52baa..__SHORT__ -- config schema fixtures` is empty; golden hash `e84f8bc0…` verified by the golden tests in the suite; no file under `handoff/authoritative/` evaluation records, `build/evaluations/`, `evidence/` or the historical Jio record `…7857589a` was modified.

## 9. Remaining HD Fire blockers

1. RHP pp. 31–450 — including **p. 356**, the particulars of the two Director criminal proceedings and of the tax litigation (identities, forums, status, amounts) — **unavailable**: the fetch path caps at 30 pages and sandbox egress to bseindia.com / iiflcapital.com / hdfire.com fails at TLS. The counts in §12 are all this pass can cite.
2. The **final Prospectus** and the price-band advertisement are unavailable, so post-RHP updates to the litigation disclosure cannot be checked.
3. The historical **evaluation record `…551a7eab` is absent**, so HD Fire's recorded 7/100 cannot be re-derived or reconciled field-by-field; its D-module 5/15 decomposition remains a documented claim.
4. Peer set, market snapshot, contingent-liability and RPT note pages were never read, so those inputs stay unverified (D-2 territory, unchanged by this pass).
5. §5.1 / §5.2 decisions are outstanding, so `clean`'s party coverage and a *verified* regulatory absence are not yet defined by the project; until they are, absence of coverage resolves to UNKNOWN — the safe side of both.

**HD Fire source-level acceptance therefore remains incomplete.** What D-5 removes is the engine's authority to call a filing litigation-free because it was not read.
