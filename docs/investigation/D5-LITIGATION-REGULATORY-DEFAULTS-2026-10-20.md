# D-5 — Litigation and regulatory-action defaults: evidence or UNKNOWN

- **Pass date:** 2026-10-20 (Asia/Calcutta)
- **Branch:** `arena/ae4d04e8-ipo-screening-engine`
- **Starting state (remote-verified at pass start):** branch tip
  `2d52baa56cbb4b82061649106745f79d04d9fce6`; `main`
  `01ba66c12ca1195fd7acbd287c3e39a019808094`; PR #6 open, `merged: false`, mergeable,
  head `e05c0efbca1ecb3024e52da73a22e180ea171118`, base
  `arena/573e69a4-ipo-screening-engine`; no hosted workflows.
- **Decision record:** `handoff/decisions/A23-litigation-and-regulatory-negative-defaults.md`.
- **Scope:** `governance.litigation_bucket`, `governance.sebi_ed_action_active` and the
  extraction path that produces them. No scoring change.

---

## 0. Summary

The governance extractor produced two favourable findings from silence:

1. `litigation_bucket` was initialised to `"clean"` before the scan and emitted unconditionally,
   scoring **4/4** in Module D even when the scanned range held no text.
2. `sebi_ed_action_active` was initialised to `False` and emitted with the quotation *"No active
   SEBI or ED regulatory proceedings"* — a sentence that appears in no filing — and without
   `quote_is_processing`, so it was presented as source text. The flag feeds knockout K2.

Both fields are now **evidence-or-UNKNOWN** under the schema's existing null states. The builder
no longer coerces `None` back to `"clean"`, and the litigation section pattern accepts the plural
label used by at least one real prospectus.

The only fixture whose score changes is class B: **41.0 → 37.0** (−4.0, Module D 6.0 → 2.0),
because its single litigation sentence names promoters, directors and group companies but not the
issuer. That exact choice is published in A23.

---

## 1. Contract findings (D-5.1)

| Question | Answer (verified) |
|---|---|
| Permitted `litigation_bucket` values | `["clean", "minor_civil", "criminal_or_regulatory", null]` (`schema/ipo-input.v1.5.schema.json:690`) |
| Permitted `sebi_ed_action_active` | `["boolean", "null"]` (`:698`) |
| Is `governance` required? | No `required` list; absent fields are allowed |
| What does `None` mean downstream? | `derived.py::_litigation_bucket` → UNKNOWN, reason *"the litigation status of the promoters, directors and company is not established"* |
| SEBI/ED `None`? | `derived.py::_sebi_ed_action_active` passthrough → UNKNOWN, reason *"the supplied input does not establish whether an active SEBI/ED action exists"* |
| K2 | `required = [promoter_pledge_pct, sebi_ed_action_active]`, `any[promoter_pledge_pct > 25, flag == true]` |
| Module D criterion | `litigation`, max **4**, categorical map `clean 4 / minor_civil 2 / criminal_or_regulatory 0`, UNKNOWN earns nothing and blocks nothing else |

Conclusion: **no schema or configuration change is needed**; the missing state already exists and
is already interpreted correctly downstream. The defect was that the extractor never used it.

### Why "no result" is not "none"

The scan is bounded by a page range located from the table of contents, with a fixed fallback
(`(430, 500)`) when the section is not located. Every one of the following produced `clean` before
this pass:

- a range whose pages return no extractable text;
- a range outside the document (loop body never executes);
- a filing whose TOC label the pattern did not match (see §2, root cause 4);
- a page whose text is a table the classifier cannot read.

Silence from any of these is a coverage failure, not a finding.

---

## 2. Root causes and code paths

### Root cause 1 — `sections.py::extract_governance` initialised both answers

Before: `lit_bucket = "clean"` and `sebi_active = False` were assigned before the loop and emitted
after it unconditionally; the bucket quote was the processing summary *"Litigation bucket
classified as: clean"* and the SEBI quote was *"No active SEBI or ED regulatory proceedings"*.

After: both start as `None`; each is set only from an explicit statement; the emitted record has
`is_unknown=True`, `quote=None` and an explanatory note when no statement exists.

### Root cause 2 — `builder.py::_build_governance` defaulted and re-coerced

Before: `self._get_field("governance.litigation_bucket", "clean")`, then
`if lit in ("none", None, "clean"): lit = "clean"`. An explicit `None` was converted back into a
clean finding. The SEBI pick used default `False`.

After: missing → `None`; only the legacy synonym `"none"` maps to `clean`; `material_civil`/`civil`
map to `minor_civil`; anything else is `None`. SEBI default is `None`.

### Root cause 3 — the classifier could only see one phrasing

The original regexes looked for `criminal proceedings against our promoters`, `r.c.c.`,
`criminal complaint`, `material civil litigation`, `civil suit` — and only checked the *presence*
of a marker, ignoring negation. That both missed real disclosures (HD Fire's summary table) and
would have read *"no criminal complaint has been filed"* as a positive.

After: page text is split into sentences; a positive finding requires a criminal/civil marker, a
quantity or live-status word, and a named covered party, with no negation in the sentence. A
flattened ICDR summary row (`Against our Directors | 2`) counts only when the page also carries the
`Criminal Proceedings` header. Table blobs and column headers are excluded by
`_is_disclosure_sentence`.

### Root cause 4 — the TOC pattern did not accept the plural

`toc.py` matched `OUTSTANDING LITIGATION` only. R.K. Fashion's table of contents reads
`OUTSTANDING LITIGATIONS AND MATERIAL DEVELOPMENTS`, so the section was never located and the scan
fell back to pages 1–50. Fixed to `OUTSTANDING\s+LITIGATIONS?`; that filing's range became
358–406 and its own statements are now read.

---

## 3. SEBI/ED semantics (D-5.2)

`_classify_sebi_action` requires, in one sentence, a regulator term (SEBI / Securities and Exchange
Board / Enforcement Directorate), an action term (proceedings, actions, investigations, show-cause,
penalty, orders) and a covered party. The sentence is split at the regulator's name:

- negation **before** the regulator (*"there are no … actions by SEBI … against the Promoters"*) ⇒
  `False`, quoted verbatim;
- an assertion **after** it (*"SEBI has initiated proceedings …"*) ⇒ `True`;
- an assertion that is itself negated in its own clause (*"nor any penalties have been imposed"*) is
  not treated as positive;
- a criminal proceeding never sets `True`; a bare reference to the SEBI (ICDR) Regulations never
  sets `True`; an action against an unrelated party, or one with no covered party in the sentence,
  leaves the field UNKNOWN.

An explicit active action against our Company, Promoters or Directors also sets the litigation
bucket to `criminal_or_regulatory`, because an active regulatory proceeding is itself regulatory
exposure. The converse is not applied.

The fabricated quotation is gone. Verified: the string *"No active SEBI or ED regulatory
proceedings"* no longer exists in the engine.

---

## 4. Implementation

| File | Change |
|---|---|
| `engine/ipo_screening/extraction/sections.py` | Evidence-or-UNKNOWN litigation/SEBI block; new `_LIT_*`/`_SEBI_*` patterns; `_litigation_sentences`, `_is_disclosure_sentence`, `_classify_litigation_text`, `_accumulate_clean_coverage`, `_classify_sebi_action` |
| `engine/ipo_screening/extraction/builder.py` | No `clean`/`False` defaults; unknown stays `None`; legacy synonyms still normalised |
| `engine/ipo_screening/extraction/toc.py` | `OUTSTANDING\s+LITIGATIONS?` |
| `tests/test_litigation_regulatory_defaults.py` | New: 20 regressions (nine D-5.4 cases) |
| `tests/test_hd_fire_primary_source_extraction.py` | Two strict xfails replaced by passing assertions of the corrected contract |
| `tests/test_extraction_phase5b.py` | Class B expectation 41.0 → 37.0 with inline provenance |
| `tests/test_ui7_ingestion.py` | Aurora Systems expectation 23.0 → 19.0 (two assertions) with inline provenance |

No change to `derived.py`, `scoring.py`, `knockouts.py`, `config/`, `schema/` or `fixtures/`.

---

## 5. HD Fire director-proceeding evidence (D-5.3)

Source: SEBI-hosted **Abridged Prospectus (RHP dated 5 October 2026)**, §12 *"Outstanding
Litigation and Material Developments"* — the same primary source recorded in
`docs/investigation/HD-FIRE-PRIMARY-SOURCE-RECOVERY-2026-10-20.md` §8.

| Item | Disclosed | Establishes |
|---|---|---|
| Criminal proceedings against **Directors** (excluding Promoters) | **2** | director-level criminal exposure |
| Criminal/civil/regulatory proceedings against the **Company** (summary cells) | Nil | no issuer-level proceeding in the summary table |
| Tax proceedings by the Company | 3, ₹0.40 million | tax (non-SEBI) exposure |

Limits, stated rather than worked around:

- The table is read through the Abridged Prospectus only; RHP pages 31–450 and the final Prospectus
  are not available in this environment, so no further detail (parties, forum, status) is asserted.
- The two proceedings are **not** a SEBI/ED action; `sebi_ed_action_active` must stay UNKNOWN.
- They support `criminal_or_regulatory` under the metric's own *"promoters, directors and company"*
  definition. The synthetic-table regression asserts exactly this and asserts the SEBI field stays
  UNKNOWN.
- No full HD Fire acceptance is claimed; the historical `…551a7eab` record remains absent.

---

## 6. Impact (D-5.5) — measured, not estimated

Method: extract each fixture with `DocumentExtractor`, evaluate with `config/ipo-config.v1.5.0.json`
at the fixed test instant, then re-evaluate the same extraction with the two fields forced to the
pre-D-5 defaults. The delta therefore isolates the correction from everything else.

| Fixture | After (lit / sebi) | Final | Pre-D-5 defaults | Δ | Module D |
|---|---|---|---|---|---|
| class A financial lender | `clean` / `False` | 40.0 | 40.0 | 0.0 | unchanged |
| class B cyclical manufacturing | `None` / `None` | **37.0** | 41.0 | **−4.0** | 6.0 → 2.0 |
| class C EPC infrastructure | `clean` / `False` | 41.0 | 41.0 | 0.0 | unchanged |
| class D loss-making tech | `clean` / `None` | 28.0 | 28.0 | 0.0 | unchanged |
| class E modern complex RHP | `clean` / `False` | 43.0 | 43.0 | 0.0 | unchanged |
| `complete_sample_rhp.pdf` (Aurora Systems, UI-7) | `None` / `None` | **19.0** | 23.0 | **−4.0** | 5.0 → 1.0 |

- **Existing behaviour:** A, C, E still yield `clean`/`False`, now backed by their own sentences.
- **Corrected behaviour:** B loses 4 points it never earned; D's SEBI flag becomes UNKNOWN (no
  score effect, but K2 is no longer given a false clean bill).
- **Resulting UNKNOWN:** B (`litigation`, `sebi`), D (`sebi`), Aurora (`litigation`, `sebi`).
- **Second measured change (UI-7):** `complete_sample_rhp.pdf` is a 4-page sample with **no
  litigation section at all**; it previously received `clean` / `False` and 23.0, and now receives
  UNKNOWN / UNKNOWN and **19.0**. The UI-7 test expectations were updated in the same commit.
- **Points/confidence:** −4.0 earned on B; confidence on the corrected fields is 0.95 when
  evidenced and 0.90 when UNKNOWN — the report now distinguishes the two.
- **Implementation correction vs semantic change:** the null states, criterion, bands and K2 are
  untouched. The only semantic judgement is the coverage standard for `clean` (A23 §"Decision"),
  published with the rejected alternative and its 41.0 consequence.

R.K. Fashion: `clean` / `False`, final score unchanged, quotations now verbatim:
- litigation — *"355 As on the date of this Red Herring Prospectus, there are no outstanding
  criminal proceedings initiated against the Company."* (p. 359)
- SEBI — *"Further, except as disclosed in this section, there are no (a) disciplinary actions
  including penalty imposed by the SEBI or any stock exchange against any of our Promoters in the
  last five Financial Years preceding the date of this Red Herring Prospectus ;"* (p. 358)

No historical evaluation was re-run, edited or re-hashed; `build/evaluations` is untouched.

---

## 7. Tests executed (D-5.4 / D-5.6)

| Battery | Result | Elapsed |
|---|---|---|
| `tests/test_litigation_regulatory_defaults.py` (new) | **20 passed** | 0.72 s |
| `tests/test_rk_fashion_reconciliation.py` + `test_extraction_phase5b.py` + `test_hd_fire_primary_source_extraction.py` | **15 passed** | 27.54 s |
| Focused battery (core semantics, acceptance matrix, evaluation record, GMP policy ×2, extraction, fixture-fallback isolation) | **255 passed** | 135.74 s |
| Full backend suite, `pytest tests` (1218 collected) | **1218 passed**, 0 failed, 0 xfailed, 38 warnings | **1211.19 s** |

The two strict xfails that pinned the D-5 defects now pass and were converted; **no expected
failure was removed for an unresolved capability**.

The first full run on the corrected engine surfaced one further affected expectation:
`tests/test_ui7_ingestion.py::test_ingest_document_success_and_coexistence` failed with
**19.0 ≠ 23.0** on the Aurora Systems sample. That document is a 4-page sample with no litigation
section at all, so it is the same defect as class B in its purest form. The expectation (two
assertions in that file) was updated with inline provenance and the file re-run: **20 passed**.
The full suite was then re-run on the final tree: **1218 passed in 1211.19 s**.

Progress: both full runs were executed with pytest's percentage indicator (the log shows
`[ 3%]`, `[ 55%]`, `[ 88%]`, …). The first run reached 100 % with 1 failed / 1217 passed; the
final run reached 100 % with 1218 passed.

---

## 8. Invariants verified

- Golden evaluation hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`
  — PASS.
- `verify_frozen_core()` — PASS on all six pinned files (`derived.py`, `scoring.py`,
  `knockouts.py`, `snapshots.py`, `evaluation.py`, `price_band_notice.py`).
- `verify_v1_6_implementation()` — PASS, zero failures/warnings, v1.6 still inactive.
- `config/`, `schema/`, `fixtures/` — `git status` clean; no diff.
- `main` — untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`.
- PR #6 — open, unmerged, not moved.
- Historical evaluations — not re-run, not edited, not re-hashed.

---

## 9. Remaining blockers

1. **HD Fire full acceptance** — RHP pp. 31–450, the final Prospectus and the `…551a7eab` record
   remain unavailable; D-5.3 is limited to S1 §12.
2. **Positive-detection conservatism** — a disclosure with no count and no live-status word
   ("a criminal complaint was filed against our Company") stays UNKNOWN rather than risking a
   heading being read as a punitive finding.
3. **Section location** — a filing with no litigation TOC entry falls back to pages 430–500 and now
   yields UNKNOWN (correct, but possibly under-reads short filings).
4. **Completeness** — an explicit negative is accepted at face value; the engine cannot verify that
   the statement covers every proceeding.
