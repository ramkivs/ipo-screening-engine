# A26 / A27 / A8-R — Decision Preparation (read-only)

- **Document type:** decision-preparation report. **PROPOSED / FOR RAMKI REVIEW.**
- **Status of every item here:** no decision is recorded, approved, rejected or
  closed by this document. It changes no decision status, and it is not
  implementation authority. The three records it prepares —
  `handoff/decisions/A26-tax-only-proceedings-classification.md`,
  `handoff/decisions/A27-auditor-bucket-unconsumed-clauses.md` (already
  `PROPOSED / UNRESOLVED`) and
  `handoff/decisions/A8-R-REGULATOR-SOURCE-COVERAGE-DEPENDENCY-REQUEST-2026-10-20.md`
  (already `UNRESOLVED`) — are left byte-identical.
- **Baseline verified before reading:** branch `arena/95234306-ipo-screening-engine`,
  HEAD `d1be6d2`, `git status --porcelain` empty; `git ls-remote` showed the same
  SHA as the remote tip (published chain `ce577ea → 41f2f86 → d1be6d2`);
  `main` = `01ba66c12ca1195fd7acbd287c3e39a019808094`; PR #6 open and unmerged
  (head `e05c0ef`, base `arena/573e69a4-ipo-screening-engine`).
- **Labelling used below** (per the instruction that fact, inference,
  recommendation and open question must not be blended):
  **[F]** confirmed fact read from this repository in this pass;
  **[I]** evidence-backed inference (states which facts it rests on);
  **[R]** recommendation to Ramki, no authority;
  **[?]** unresolved question that only Ramki can settle.

---

## 1. What was read, and what was run

Read: the two shipped configs, the input schema, the evaluation-record schema,
the supplemental-enrichment schema, `canonical.py`, `derived.py`, `scoring.py`,
`knockouts.py`, `config_validation.py`, `semantic_validation.py`,
`connectors/interfaces.py`, `issue_terms.py` consumers,
`extraction/sections.py`, `extraction/builder.py`, the v1.5 specification,
the v1.5 execution prompt, the v1.3 reference specification, the v1.4 reference
config, the A8 / A8-M / A18 / A19 / A23–A27 decision records,
`docs/TRACEABILITY_MATRIX.md`, `docs/RUNBOOK.md`, the published RK and HD Fire
reconciliations, the golden fixtures and the litigation test suite. History was
read with `git log`/`git show` (including `-S"disputed tax"` and the v1.6
promotion commit `49c9944`).

Run (both read-only, no artefact written; both re-confirm the published state
rather than testing anything new):

```
python3 -m pytest tests/test_litigation_regulatory_defaults.py \
                  tests/test_hd_fire_primary_source_extraction.py -q
  → [pytest-progress] finished 96/96 tests in 0.2s (passed=96 failed=0 skipped=0)
python3 engine/tools/ipo_screen.py check-config
  → config config/ipo-config.v1.5.0.json | valid True | profiles resolved 10
```

**[F]** The full suite was deliberately **not** re-run: the last published pass
recorded `1288 passed / 0 failed / 0 skipped in 1272.03 s` at `41f2f86`/`d1be6d2`
(`/home/user/full_a24.log`, `EXIT=0`), the tree is unchanged since, and nothing in
this document alters behaviour for the suite to validate. A focused 96-test run
was used only to prove that the *current* behaviour quoted throughout this report
is the behaviour of the code as published, not of my notes about it.

Two further read-only probes were run against the real filings and the litigation
fixtures; their results are reported where they bound a claim (§2.6, §3.5).

---

## 2. A26 — tax-only adverse proceedings

### 2.1 Which screening risk is tax litigation intended to represent? **[F]/[I]**

**[F]** Three governed texts, and only these, speak to it:

| Text | Says |
| --- | --- |
| v1.5 §4.3, `IPO_Screening_Engine_Specification_v1.5.md:253` | `tax proceedings` is an input the governance read must **collect**. No state, no score, no bucket. |
| v1.3 reference, `Claude_IPO Screening Engine v 1.3 — Specification.md:103` | the litigation criterion (4 pts) is about "criminal/regulatory cases **on promoters**" — a track-record/integrity signal. Tax is absent from that row. |
| v1.3 reference `:105` / v1.4 `ipo-config.json:297` | "disputed tax matters only = 1" — attached to the **auditor** criterion, as a middle tier between clean and unstable. |

**[I]** So tax has never, in any governed text in this repository, been a
*litigation-criterion* signal. Its two intended meanings are (a) financial
**exposure** — a disputed assessment is a contingent liability, which is why the
ICDR summary table gives it a column with an *amount* — and (b) an **audit-quality
flag** in the v1.3/v1.4 reading (the auditors remarked on it). Neither meaning is
"the promoter has been prosecuted". Restated as a question: **[?]** does Ramki
want a tax dispute to say anything about promoter *conduct* at all, or only about
exposure and audit quality? The answer decides A26 and A27 together.

### 2.2 Deliberate exclusion, unresolved gap, or neither? **[F]/[I]**

* **[F]** Not a regression: `git log --all -S"disputed tax" -- engine/` is empty,
  the clause never existed in engine code, and v1.5 §11 (`:547-558`) lists the
  auditor states *without* a disputed-tax state. The published A26 §11 already
  records this.
* **[F]** Not resolved-and-dropped either: no decision record in
  `handoff/decisions/` disposes of tax scoring. A20 disposes of the
  contingent-liability **numerator** (unquantified amounts), not of a bucket.
* **[F]** What is genuinely stale is the **config text**, not the code:
  `config/ipo-config.v1.5.0.json:1727` (and the v1.6 copy) still carry the
  `auditor_bucket` formula "eom_only: EOM/CARO only and no change" — the v1.4
  wording — while v1.5 §11 requires precisely `EOM/CARO only` as a state
  (`:554`) and never mentions tax there.
* **[R]** Therefore: A26's real open question is *narrower* than "should tax get
  a bucket" — it is "does v1.5 §4.3's `tax proceedings` input need a scored home
  at all, given that exposure is already governed by K5 and severity by the
  `eom_caro` penalty?" My reading: no new scored home is required; a
  **recorded decision that none is required** is what is missing.

### 2.3 Does A20/K5 already cover the exposure? Magnitude only, or the track-record dimension too? **[F]**

K5 (`config/ipo-config.v1.5.0.json`, `knockouts[4]`) is
`"Contingent liabilities >50% of net worth (or unquantified)"`,
`"required": ["contingent_liab_pct_networth", "contingent_liab_unquantified"]`.
Enumerating **all 30 criteria** in both shipped configs, `contingent_liab_pct_networth`
appears as a *derived metric* only — **no criterion consumes contingent
liabilities**. `Tax matters` is one of the governed `unquantified_types`. So:

* magnitude is priced **once, as a binary knockout** (and there is no graduated
  contingent-liability score to be "double counted" against);
* the second governed instrument touching severity is the **`eom_caro` penalty**
  (`config/ipo-config.v1.5.0.json:1400`, `scale {low:-1, medium:-2, high:-3}`,
  `metric: eom_materiality`), which prices "the auditors felt this was material"
  — the v1.3 auditor reading of disputed tax, arrived at by a different route;
* **[F]** the track-record dimension is priced **nowhere**, because the only
  adverse state in the litigation criterion is `criminal_or_regulatory` and its
  text does not include tax.

**[I]** "Magnitude is lost if we leave tax UNKNOWN" is therefore **false** — the
exposure is in K5, and the severity *can* be in `eom_caro`. What is lost is only
an unranked statement that a promoter-facing tax dispute exists, which no governed
text asks the engine to make.

### 2.4 Does leaving a favourable-but-material signal UNKNOWN lose distinct intended signal? **[F]/[R]**

**[F]** `UNKNOWN` is not a soft zero: an unknown criterion is excluded from
`available_points`, the score is `scored_points / available_points × 100`, and
the record states the availability basis. The tax-only case is *favourable*
direction, so the practical effect of UNKNOWN is that the engine declines to
award 4 points for a filing that disclosed 6–15 tax proceedings — conservative,
not flattering.

**[R]** That conservative outcome is acceptable *as policy* only if Ramki records
it. If the intent was "an unquantified statutory demand is itself a
track-record mark", then the criterion text must change first — that is a
specification-level change, not a bucket addition.

### 2.5 Would mapping tax into `criminal_or_regulatory` misrepresent or double count? **[F]/[R]**

* **Misrepresentation — yes, in three ways.** (i) The criterion is labelled
  "Promoter track record & litigation", its config population line reads
  `"clean / minor_civil / criminal_or_regulatory (promoters, directors, company)"`
  (`config/ipo-config.v1.5.0.json:1706`), and `sections.py` counts only `Against …`
  rows while treating `By our Company / Group Companies` rows as non-adverse — so a
  tax count, which is typically disclosed as an appeal *by* the company or against a
  group entity, would need a **new population rule**, not merely a new value;
  (ii) the value carries a 0/4 points AVOID-grade signal with no graduated basis;
  (iii) the last pass already rejected this mapping and no new evidence supports it.
* **Double counting — partly.** **[F]** The magnitude itself cannot be double
  counted against K5 because no criterion prices contingent liabilities. The
  *audit-quality* meaning, however, **is** already priced by the `eom_caro`
  penalty; a tax→`criminal_or_regulatory` mapping plus `eom_materiality` would
  be two scored statements about one disclosed fact (a 4-point criterion at 0
  *and* a −1..−3 penalty), which §17's "retain the existing penalties" does not
  authorise.
* **[F]** Measured prevalence could **not** be established here, and this is
  reported rather than glossed: for all three real filings (vishal 438–503,
  RK 430–496, Jio 463–478) the located litigation range contains **no parsable
  ICDR summary table at all** (`pages_with_table_head=0`, three runs, this
  pass), so a "how many issuers would flip" figure cannot be derived from the
  corpus in this repository. The tabular evidence that *does* exist — HD Fire
  (published A25 record: 2 criminal against Directors, 3 tax by the Company) and
  the `class_b` fixture (tax counts on `By our Company/Group Companies` rows) —
  points the same way: tax counts sit on **non-promoter** rows.
  **[I]** Hence a tax→adverse-bucket mapping would, on the available examples,
  mostly be a mapping of company-level exposure onto a promoter-conduct scale.

### 2.6 Cost of a dedicated bucket (full cross-cutting inventory) **[F]**

Consumer inventory, produced this pass by `grep -c litigation_bucket` over the
whole tree (counts are references, files listed once):

| Layer | File(s) | Note |
| --- | --- | --- |
| Schema | `schema/ipo-input.v1.5.schema.json:1` | 3-member enum; `governance.additionalProperties: false` and root `false`, so no side-loading. |
| Taxonomy pin | `config_validation.py:53` | `CATEGORICAL_DOMAIN["litigation_bucket"] = {clean, minor_civil, criminal_or_regulatory}`. |
| Config | `config/ipo-config.v1.5.0.json`, `v1.6.0.json` (3 each) | criterion `map` **and** `derived_metrics.litigation_bucket.formula`. |
| Derivation | `derived.py:1382-1425` | `@metric("litigation_bucket")` + formula string. |
| Extraction | `extraction/sections.py` (5), `extraction/builder.py` (6) | prose / table / labelled-list routes, alias normalisation. |
| Golden | `fixtures/vishal_nirmiti/expected_derived.json` (3), `expected_score.json` (1), `input.json` (1) | the **code-produced** formula string (`derived.py`) is embedded in the golden expectations → changing that string re-baselines the golden; changing config text alone does not (no golden file pins `config_hash`). |
| Stored canon | `fixtures/jio/jio_canonical_2026-10-19_pre_evidence_remediation.json` (3) | historical canonical snapshot. |
| Tests | `tests/test_litigation_regulatory_defaults.py` (62), `test_hd_fire_primary_source_extraction.py` (4), `test_extraction_phase5b.py` (3), `test_rk_fashion_reconciliation.py` (2) | plus `frontend/test/app.test.js` (1). |
| Reference artifacts | `handoff/reference/ipo-config.json` (2), `ipo-scorer_4.html` (2), `VISHAL-NIRMITI-LIMITED.json` (1) | prototype material, not authoritative. |
| **Not** consumers | `frontend/app.js`, `presentation/*`, `excel.py` | **zero** references: rendering is generic over values and states. |

**[R] Correction to the published A26 §4 item 8:** it lists
`presentation/service.py`+`models.py`, `presentation/api.py`, `frontend/app.js`
(including the `:1073` GOVERNANCE field filter) and `excel.py` as consumers that
must each render a new bucket. That is **overstated** — none of them references
`litigation_bucket`; the honest cost there is one frontend test plus a display
check that a new state is not rendered as favourable. The rest of A26 §4 stands,
and the dominant cost is **not** code:

**[F]** `config_fingerprint` (`config_validation.py:771-783`) hashes the whole
config except `_fingerprint`/`_validation`, and `RUNBOOK.md:393-396` states the
governed consequence verbatim: "Changing the config **invalidates every stored
result hash** by design … Existing records remain valid as history; new runs will
not replay to the old hashes. If you need both, cut a new config version rather
than editing in place." The v1.6 promotion followed exactly that practice
(`49c9944` added `config/ipo-config.v1.6.0.json` as a new file and left v1.5.0
untouched). So a fourth bucket = a new config version + golden re-baseline, i.e.
a decision of a different class.

### 2.7 Options A / B / C, evaluated against the evidence

| Option | Assessment |
| --- | --- |
| **A — retain UNKNOWN, record the gap** | **Recommended.** v1.5-conformant (§4.3 asks the input to be read; §11 gives it no state). Cost: documentation only. Preserves the "no invented taxonomy" rule. Leaves a known conservative bias, which the record must state as intended rather than incidental. |
| **B — map tax into an existing bucket** | **Rejected on evidence.** The only candidate is `criminal_or_regulatory`, whose governed meaning excludes tax (§2.1), whose population is promoter-facing while tax disclosures are usually company-facing (§2.5), and whose severity dimension is already priced by `eom_caro`. `minor_civil` and `clean` are worse. No mapping passes the test "does the existing meaning support it". |
| **C — dedicated bucket, separately authorised** | **Feasible, and now precisely costed** (§2.6), but it is a schema + config-**version** + golden re-baseline change, and it still needs a points decision that `check-config` will force to reconcile at 100 points across 10 profiles. Not this pass; not by inference. |

**[R]** Sequence for C, if ever approved: (1) Ramki's decision record fixing the
points and the population ("tax proceedings *against promoters/directors* only"
vs any tax row); (2) schema enum + `CATEGORICAL_DOMAIN`; (3) new config version
(not an edit) with the criterion map and both formula strings; (4)
`sections.py`/`builder.py` routes; (5) golden re-baseline as an explicit act;
(6) history policy statement in the tracker; (7) tests per route. Steps 3 and 5
each need their own authorisation.

### 2.8 A26 acceptance criteria (proposed, not implemented) **[R]**

Whichever option is chosen, the outcome is testable as: (a) a tax-only adverse
table or prose disclosure leaves `litigation_bucket` absent and the *reason* in
the record (already true — `test_table_without_the_bucket_columns_cannot_show_clean`,
`test_tax_or_civil_proceedings_are_not_regulatory_actions`); (b) whatever state is
chosen, the record's basis note distinguishes "no adverse proceeding disclosed"
from "not searched/read"; (c) `check-config` reconciles 10 profiles × 100 points;
(d) no stored record is re-run, re-hashed or republished.

---

## 3. A27 — auditor bucket, CARO and the unconsumed clauses

### 3.1 Exact criterion text, as specified and as implemented **[F]**

* Config text, `derived_metrics.auditor_bucket.formula`, at
  `config/ipo-config.v1.5.0.json:1727` and identically at `v1.6.0.json:1727`
  (inherited from the v1.4 reference at `handoff/reference/ipo-config.json:297`):
  `"clean_reputed: reputed firm, unqualified, no change, no EOM; eom_only: Emphasis
  of Matter/CARO/disputed tax only; unstable_or_repeated_eom: auditor change in 3Y
  or repeated EoM. The auditor-change count and repeated-EOM inputs are separate.
  UNKNOWN when the opinion is not supplied. A qualified/adverse/disclaimer opinion
  is a knockout, not a bucket."` — **this is the only place "disputed tax" appears.**
* Code text, which is what actually reaches records:
  `derived.py:1431` `"clean_reputed: unqualified, no auditor change, no EOM;
  eom_only: EOM/CARO only and no change; unstable_or_repeated_eom: auditor change
  within 3 years or repeated EOM. A qualified/adverse/disclaimer opinion is a
  knockout rather than a score."` — copied into the score line by `scoring.py:223`
  (`base.formula = item.formula`) and rendered by `excel.py:319`.
* **[F]** The two strings are **not** the same text, and nothing keeps them in
  agreement: `check-config` rule (14) (`config_validation.py:697-708`) reconciles
  only `implemented` against the metric `REGISTRY`, never the formula wording. So
  "disputed tax" is *config documentation* that the implementation neither states
  nor implements, and the config string has **no reader** (no code path reads
  `derived_metrics.*.formula`; the sole `formula` requirement elsewhere is
  `enrichment_contract.py:358` for enrichment payloads).
* v1.5 §11 (`:547-558`): auditor status must distinguish `clean/unqualified/no
  material instability`; `EOM/CARO only;` (`:554`); `repeated EOM or repeated
  auditor instability`; `qualified/adverse/disclaimer → knockout` (`:556`); and
  "Auditor change count and repeated EOM must be separate inputs" (`:558`).
* v1.5 **never** mentions disputed tax in §11; v1.3 `:105` did.

### 3.2 Inputs actually consumed **[F]**

`_auditor_bucket` (`derived.py:1428-1490`) reads exactly four:
`governance.auditor_opinion`, `governance.auditor_reputed`,
`governance.auditor_changed_3y`, `governance.repeated_eom`. Branch order: opinion
absent → UNKNOWN; qualified/adverse/disclaimer → NOT_APPLICABLE (K1 owns it);
`auditor_changed_3y` absent → UNKNOWN; change or repeated-EOM true →
`unstable_or_repeated_eom`; unqualified **and** `auditor_reputed is True` →
`clean_reputed`; `emphasis_of_matter` or (unqualified with `auditor_reputed`
absent) → `eom_only`.

### 3.3 Declared but not consumed, and the disputed-tax clause **[F]**

`caro_remarks` — declared `{"type": ["boolean","null"]}` in
`schema/ipo-input.v1.5.schema.json:659`, acknowledged at spec §4.3 `:242` — has
**no** consumer, **no** extractor and **no** test anywhere in `engine/` or
`tests/`. The only place "CARO" appears in engine code is inside the auditor
formula *string* (`derived.py:1431`). The opinion extractor
(`sections.py:2473-2497`) recognises EoM / adverse / disclaimer / qualified /
unqualified and has **no CARO route**. There is **no input surface at all** for
disputed tax: the only tax fields in the model are `financials.periods[].tax`
(an expense line, spec `:177`).

**[I]** Consequently the engine *cannot* express §11's `EOM/CARO only` state for
the case that motivates it: unqualified opinion **plus** CARO remarks. If the
auditor is reputed, that filing scores `clean_reputed` (2/2); if not, it scores
`eom_only` — but by the reputation branch, not because of CARO.

### 3.4 Was it deliberate, omitted or never implemented? **[F]/[I]**

* **[F]** `git log --all -S"disputed tax" -- engine/` → empty. `caro_remarks` has
  never appeared in `derived.py`/`sections.py`. So: **never implemented**, in
  both senses — nothing was deleted.
* **[F]** The clause in the config formula text is inherited v1.4 reference
  wording (`handoff/reference/ipo-config.json:297`), and `49c9944` copied that
  config into v1.6.0 verbatim.
* **[I]** Therefore: the *disputed-tax* half is **stale documentation** (v1.5
  §11 dropped it; CONVENTION rule "v1.5 governs" applies), while the *CARO* half
  is a **live conformance gap** (v1.5 §11 requires a state the code cannot
  represent). Those two need **opposite** remedies and must not be decided as one
  package. **[?]** Ramki should confirm that reading, because A26 §5.4 framed it
  as an either/or.

### 3.5 The five absence states, as expressible today **[F]**

| State | Expressible? | Mechanism today |
| --- | --- | --- |
| no remarks disclosed | no | `caro_remarks` absent → indistinguishable from "not looked". |
| remarks disclosed, none found | **only for EoM** | `eom_materiality: "none"` (schema enum member) → `scoring.py:598` `scale.get(value, 0)` → penalty **scored 0**, i.e. "checked and clean" is a *scored* fact, not an absence. |
| remarks present | yes, as a value | `caro_remarks: true` or `auditor_opinion: "emphasis_of_matter"`; only the latter changes any score. |
| input not supplied | yes, as absence | field absent / `null` → `eom_materiality` UNKNOWN; `scoring.py:580-596` carries the **worst** magnitude in the lower bound ("neither applied nor ignored", spec §17). |
| evidence not accessible / unavailable | partial | the `eom_caro` penalty is UNKNOWN; the *opinion* itself still has a value, so the auditor criterion can be `clean_reputed` while CARO is unreadable — documented in the RK reconciliation (`:254`: CARO annexure on scanned pp. 294-299, no digital text → penalty correctly UNKNOWN). |

**[F]** The published RK reconciliation also records the mid-tier's real
semantics: `auditor_bucket = eom_only` with **zero** Emphasis of Matter in the
filing, annotated "**label is semantic misnomer**" (`:102`, `:233`). The bucket
named `eom_only` is in practice a "reputation-deducted middle tier".

### 3.6 Recommended absent-field semantics **[R]**

Do not let `caro_remarks` be the field that carries absence, and do not invent a
new field. The repository already has the right pattern, twice:

1. **Extraction:** emit a value only from the filing's own words —
   `test_explicit_negative_eom_is_recorded_verbatim` /
   `test_positive_eom_does_not_assert_repeated_eom`
   (`tests/test_auditor_tenure_defaults.py:107-124`) show `repeated_eom=False`
   sourced from an explicit "no Emphasis of Matter" sentence with a verbatim
   quote, and **no assertion** without one. CARO should follow that template
   exactly: `true` from a positive CARO remark, `false` only from an explicit
   negative, absent otherwise (A24/A25's `allow_absence` gate — absence credited
   only from a located, fully read section, with the basis appended to `notes`).
2. **Scoring:** absence must not be neutral and must not be zero. `eom_caro`'s
   existing treatment (UNKNOWN ⇒ worst magnitude held in the lower bound, never
   applied to the base score) is the governed precedent for what to do with an
   unconsumable-but-material input.

### 3.7 What consuming `caro_remarks` would require **[F]/[R]**

| Surface | Requirement |
| --- | --- |
| Input schema | none for the field itself (already declared); a *new* state (e.g. `auditor_opinion: caro_only`) **would** be a schema-version change — the enum is closed and `additionalProperties: false`. |
| Validation | `sections.py` CARO annexure locator + verbatim quote rule; a `page_status`/readability gate before any negative (A24/A25 machinery already exists). |
| Provenance | existing `Evidence.extraction_method` / `_evidence` route; a reviewer-supplied value would otherwise be indistinguishable from an extracted one. |
| Derivation | `_auditor_bucket` gains a fifth input; the **code** formula string (`derived.py:1431`) must then be updated in the same change, because that string — not the config's — is what the record and the workbook display (`scoring.py:223`, `excel.py:319`). Nothing enforces the two texts agreeing (§3.1), so consistency is an obligation of the change, not a check that will catch its absence. |
| Double-count guard | must state explicitly that `eom_only` (criterion) **and** `eom_caro` (penalty) both fire for one EoM today — see §3.8 — so the change must not add a third. |
| UI/API/Excel | none code-wise: `presentation/*`, `frontend/app.js`, `excel.py` carry no auditor-bucket-specific logic (0 references, verified this pass); display shows the bucket string verbatim. |
| Config version | the config text at `:1727` has **no reader** other than the hash, but `config_fingerprint` (`config_validation.py:771-783`) hashes the whole config except `_fingerprint`/`_validation`, so *any* wording edit flips `config_hash`; `RUNBOOK.md:393-396` then requires a new version file rather than an in-place edit. |
| Golden | **unavoidable for either edit, and double for the code string.** `config_fingerprint` hashes the whole config, and `evaluation.py:275-289` puts `config_hash` inside the `result_payload`, so a *wording-only* edit to `config/ipo-config.v1.5.0.json:1727` already flips `result_hash` — which `tests/test_vishal_golden.py:52` pins to `e84f8bc0f9b9…5619e1`. A code-string edit additionally changes the text embedded at `fixtures/vishal_nirmiti/expected_derived.json:34` and `expected_score.json:324`. Either way the re-baseline is an explicit act, not a test edit. The golden *input* has no `caro_remarks` key, so **absent-input behaviour remains the semantic hinge**: absent ⇒ unchanged branch order ⇒ every score moves by 0 even though the hash moves. |
| History | stored records stay valid as history only; replay against a new config version will not reproduce old hashes. |

**[R] Correction to the published A27 §3:** its claim that Option A/B "cannot
change a score, so no golden or historical artefact moves" is **wrong about the
artefacts**. Even a wording-only edit to the config formula flips `config_hash`,
and `config_hash` sits inside the `result_payload` that `result_hash` covers
(`evaluation.py:275-290`) — so the golden assertion at `tests/test_vishal_golden.py:52`
breaks with **every score unchanged**. A wording-only change is cheaper in
*behaviour* than in *artefacts*, which is precisely why it still needs its own
authorisation.

### 3.8 A20/K5 and the `eom_caro` penalty: double counting **[F]**

An EoM already prices twice under the shipped config: once as `eom_only` (1/2 on
the auditor criterion) and once as the `eom_caro` penalty (−1..−3 via
`eom_materiality`). That is not an accident to fix: v1.5 §17 says "**Retain the
existing penalties**", and the two instruments answer different questions (what
tier is the auditor relationship / how material is the remarked matter). So
consuming CARO in the bucket is **consistent with how EoM is already handled**
and is not a new double count — provided the disputed-tax magnitude is *not* also
scored in the litigation bucket (A26 Option B is what would create a third
counting of one fact).

### 3.9 Options A27-A…D, evaluated

| Option | What it actually does | Verdict |
| --- | --- | --- |
| **A — amend config/code wording to v1.5** | drops "disputed tax" from the auditor formula text (and, if kept, annotates that CARO is not yet wired) | **Correct for the tax half; not sufficient alone.** Cheapest option, but it *does* touch `config_hash` + golden strings (§3.7), so it needs its own small authorisation. |
| **B — consume `caro_remarks` in `_auditor_bucket`** | makes §11's `EOM/CARO only` reachable: unqualified + CARO ⇒ `eom_only`, not `clean_reputed` | **The only option that closes a real conformance gap.** Needs §3.6 semantics first; must not invent the negative; needs a new config version for the formula text. |
| **C — leave as is** | keeps a favourable-direction over-score available for CARO-only filings (2/2 where §11 implies 1/2) | Acceptable **only** if Ramki records that he accepts the divergence; otherwise it is a silent divergence from an explicit §11 requirement. |
| **D — new `auditor_opinion` state (`caro_only`)** | richer taxonomy | **Rejected as disproportionate:** the closed enum makes it a schema-version change, and `caro_remarks` + opinion already carry the same information once B is implemented. |

**[R] Recommended staged sequence** (each stage separately authorised):
1. Record the two findings as decisions (A27 Option A for tax wording; B
   approved-in-principle or declined, explicitly, for CARO).
2. Semantics before wiring: approve the extraction contract for `caro_remarks`
   (positive / explicit-negative / absent, verbatim quote, readability gate) —
   this is the A24/A25 pattern re-applied, no new machinery.
3. Then, and only then, wire `caro_remarks` into `_auditor_bucket` with a new
   config version, formula-string update, and an explicit golden re-baseline act;
   `test_auditor_tenure_defaults.py` (10 tests) is the existing pin that must
   keep passing, with absent-input ⇒ unchanged behaviour asserted.
4. Rename the mid-tier (`eom_only` → a name that does not claim what the code
   does) **as part of stage 3**, since stage 3 already re-baselines the strings —
   the RK "semantic misnomer" finding then stops recurring.

---

## 4. Inventory: declared governance inputs with no consumer (Section D) **[F]**

Method: for each name, grep over `engine/` (consumers), `tests/`, `fixtures/`,
`frontend/`, and the schema. `regulatory_actions`' single test hit was the
substring `..._are_not_regulatory_actions` in a test *name*, not the field.

| Field (`governance.*`) | Declared in schema | Acknowledged in v1.5 | Consumers found | Extractor | Tests | Separate gap? |
| --- | --- | --- | --- | --- | --- | --- |
| `eom_count_3y` (int ≥0 / null) | yes | §4.3 `:241` (EOM), §11 `:558` ("change count and repeated EOM must be separate inputs") | **none** | none | none | **Yes** — a distinct required input with no route; `repeated_eom` is a boolean proxy, not a count. |
| `auditor_change_count_3y` (int ≥0 / null) | yes | §11 `:558` | **none** | none | none | **Yes** — §11 explicitly demands separation from repeated-EOM; `auditor_changed_3y` is a boolean, so "3 changes in 3 years" and "1 change" are identical today. |
| `caro_remarks` (bool / null) | yes `:659` | §4.3 `:242`, §11 `:554` | **none** | none | none | **Yes** — §3 above. |
| `regulatory_actions` (array of open objects) | yes | §4.3 `:251` | **none** | none | none | **Yes, but different in kind** — the *information* is consumed by `litigation_bucket`/`sebi_ed_action_active` extraction; the *structured list* is unused, so the record cannot name which action established a flag. Whether that is a gap depends on R-S3/R-S7. |
| `independent_director_count` (int ≥0 / null) | yes | §4.3 `:247` | **none** | none | none | **Probably not a scoring gap** — `board_kmp_bucket` uses `board_independent_majority`, which is the governed majority test; the count is a supporting disclosure. **[?]** confirm no decision expects the count itself. |

**[F]** All five are inert under validation: the schema accepts them,
`additionalProperties: false` merely prevents *other* names, and nothing rejects
a supplied-but-unconsumed field. **[I]** So a reviewer supplying `caro_remarks:
true` today sees it in the stored input and in no derived value — which is exactly
the "declared but not consumed" failure mode, invisible unless someone reads the
formula strings. **[R]** A cheap, decision-free guard worth approving
separately: a `check-config`-style lint that every `properties.governance` field
is referenced by at least one of derived/extractor/tests, failing with the field
name. That is a tooling change, not a scoring change, and would have surfaced
this whole A27 class automatically.

---

## 5. A8-R — assessment of R-S1 … R-S10

### 5.1 What exists as a governed precedent (established this pass) **[F]**

* **The engine never fetches.** `docs/RUNBOOK.md` §9, "What the engine will not
  do": "**It will not fetch data.** Extraction is upstream and out of the
  scoring path; the engine never makes a network call."
* **`issue_terms.py` is not in the scoring path**: the only importers are
  `presentation/models.py` and `presentation/service.py` (grep over `engine/`).
  It is nonetheless the repository's one working official-source contract:
  `OFFICIAL_HOSTS` allow-list including `sebi.gov.in`, outcomes
  `FOUND / NOT_FOUND / UNAVAILABLE / REJECTED`, the HTTP-200-JS-shell rule
  (`UNAVAILABLE`, never `NOT_FOUND`), and `listing_searched` /
  `searched_listings` provenance (the 2026-10-18 false-`NOT_FOUND` failure mode
  it exists to prevent).
* **`connectors/`** classifies supplied snapshots only: `SourceClass` =
  `OFFICIAL_EXCHANGE / SECONDARY_TRACKER / MARKET_REGIME / PEER_MULTIPLE /
  ANCHOR_BOOK` (no regulator-enforcement class), `FreshnessStatus` =
  `FRESH / STALE / FUTURE / MISSING`.
* **Provenance primitives already exist** — `Value.verification`
  (`VERIFIED`/`UNVERIFIED`, `canonical.py:42-46`; `Value.verified` `:206-222`,
  `Value.unverified` `:224-243`); `SourceRef.uri/content_hash/retrieval_timestamp/
  source_timestamp` (`:110-121`); `Evidence.locator` documented to accept "a page
  number, a table name, a section heading **or a URL fragment**"; `ExtractionMethod`
  (`:49-61`); and the knockout result's own `missing: [...]` + explanation
  (`knockouts.py:1-18`, `:268-277`).
* **Two governed carriers for externally sourced facts already exist:** the input
  schema's `_sources[]` / `_evidence{}` / `_cross_checks[]` (with
  `CROSS_SOURCE_INCOMPLETE` / `CROSS_SOURCE_DIVERGENCE` emitted by
  `semantic_validation.py:296` and the rule that divergence is "reported, never
  silently resolved", spec §20); and `schema/supplemental-enrichment.v1.schema.json`,
  "Governed pre-score enrichment contract for non-RHP data … assembled upstream
  of schema validation and deterministic scoring", whose `sourceRef` carries
  `source_type`, `uri`, `content_hash`, `retrieval_timestamp` **and**
  `source_timestamp`. Its `source_type` enum has **no** regulator member
  (`RHP, DRHP, EXCHANGE, MARKET_DATA, PEER_DATA, STRUCTURED_INPUT, DERIVED`) and
  its root is `additionalProperties: false` with sections
  `price_band / market_data / peer_data / analyst_assessment / derived / overrides`.
* **[F] A25-D2 supplied only the in-document half of R-S6.** `sections.py` has a
  structured route that sets `sebi_ed_action_active=False` when the located, fully
  read, issuer-scoped disclosure names **both** regulators and reports none — the
  published rename of that test to
  `…_is_a_disclosed_negative_not_a_verified_absence` states the limit in its own
  name. **[F]** Canonical governance values are **plain scalars**
  (`CanonicalInput.governance()` returns a dict; no `Value` wrapper), so basis is
  recorded only in `_evidence`/`notes`, and a reviewer-typed `false` and an
  extracted `false` are indistinguishable in the governance dict itself.

### 5.2 Per-provision assessment **[F]** = established by the texts cited

| # | Specified today | Implemented today | Absent / ambiguous | Prerequisite for a corroborated external absence? | Recommended acceptance criteria (proposed) |
| --- | --- | --- | --- | --- | --- |
| **R-S1** authority set | **[F]** A8 approved safeguards require source identity + event evidence "before a snapshot is treated as verified"; A18 limits it: "A `VERIFIED` link … does not authenticate a publisher or qualify a source" | **[F]** none for regulators; `OFFICIAL_HOSTS` is a *host* allow-list for issue terms | **[F]** no source is designated authoritative for "no SEBI/ED action" | **Yes — it is the root.** Without a named authority the words "verified absence" have no referent | One named authority per regulator; a test that a negative from a *non*-listed host can never raise confidence above UNVERIFIED; A18-style disclaimer that a local hash is not publisher authentication |
| **R-S2** discovery & retrieval | **[F]** `issue_terms` contract exists (allow-list, outcomes, JS-shell rule); **RUNBOOK §9 forbids network calls in the engine** | **[F]** `issue_terms` only, and only in the presentation/ingestion layer | **[F]** no register-coverage rule for K2; no egress contract for scoring | **Yes** | Reuse the four outcomes verbatim; a test that an HTTP-200 shell, a redirect and a 0-result page each yield `UNAVAILABLE`/`NOT_FOUND` per the existing rule; a test that `evaluate` performs no I/O |
| **R-S3** issuer/party matching | **[F]** v1.5 §4.3 requires promoter vs company litigation separately (`:249-250`); A24 established "against/by" scoping in-document | **[F]** `_LIT_PARTY_QUALIFIER` / `_lit_row_cells` / `_lit_party_class`; issuer+Promoters+Directors coverage rule (A24) | **[F]** no name-normalisation/alias rule across registers; no rule that a name match without identity verification proves nothing | **Yes** | Fixture per ambiguity (alias, "Private Limited" variance, sister entity); an identical-name-different-entity test asserting *no* conclusion either way |
| **R-S4** index completeness | **[F]** A8-M §2/§4: an expected-but-missing record ⇒ UNKNOWN, never skip | **[F]** in-document only (`_lit_absence_covers_population` — population of *parties*, not of *sources*) | **[F]** nothing establishes that a searched register covers population × period | **Yes — this is the binding one.** An absence claim is only as strong as the index's stated coverage | Record must name the searched index and its period; a test that "searched, 0 results, coverage unknown" reports UNVERIFIED, not CLEAR |
| **R-S5** event vs retrieval time | **[F]** A8-M §2 preserved list; A18 L2-a forbids inventing a retrieval instant; A18 L1 route (`_sources` pin) exists | **[F]** `SourceRef.source_timestamp` vs `retrieval_timestamp` supported; `_sources` usable today | **[F]** "active as at what instant" for a K2 flag is undefined | **Yes** | Assert `as_of` ≠ retrieval time in any K2-relevant negative; retrieval time alone fails the test |
| **R-S6** failed / unavailable retrieval | **[F]** A18 L4-a: link failures are **non-terminal diagnostics**; A9 stays fail-closed for Final | **[F]** `issue_terms` outcomes; `page_status` for in-document readability | **[F]** no retry policy; no rule that a transient failure must not become a permanent negative | **Yes** | Each of timeout / 5xx / malformed / empty-HTML / parse-success-but-zero-rows asserted to leave K2 **UNVERIFIED** with the reason preserved and score unchanged |
| **R-S7** partial / inaccessible documents | **[F]** A24 (blank ≠ failed ≠ out-of-range; absence needs a located, fully read section) is the in-document analogue | **[F]** `page_status` + `pages_read`; scanned raster stays unread (RK pp. 294-299) | **[F]** no equivalent for external pages (truncated HTML, paginated register, login walls, PDFs beyond a fetch cap) | **Yes** | A negative derived from an unreadable page is rejected; partial capture ⇒ `PARTIAL`-style reason + UNVERIFIED, never CLEAR |
| **R-S8** conflicting evidence | **[F]** A8-M §2 "conflict without evidenced precedence ⇒ UNKNOWN"; `_cross_checks` ⇒ `CROSS_SOURCE_DIVERGENCE`, "reported, never silently resolved" (spec §20) | **[F]** numeric only (`primary`/`secondary` are numbers, so a boolean flag cannot ride it today) | **[F]** no rule for issuer denial vs a located order | **Yes** | Issuer denial + located order ⇒ UNKNOWN with both quotes preserved and a validation finding; a test that resolution requires a *source-defined* precedence, else no resolution |
| **R-S9** durable provenance and K2 consequence | **[F]** tri-state rule "a missing knockout input must never be treated as CLEAR"; `critical_data` lists `sebi_ed_action_active`; K2's `when` is a **bare flag read** | **[F]** basis is *descriptive* today: `_evidence` entries and `notes` strings ("`; search basis:`", "`coverage basis:`") — **K2 does not consult them** | **[F]** **[?]** whether a corroborated negative may clear K2 differently | **Yes — and it is a knockout-semantics decision, not a storage one** | See §5.4: the record already stores basis; the decision is which basis may clear. Acceptance: two evaluations differing only in basis must not report the same K2 state if only one basis is permitted to clear |
| **R-S10** currency / event window | **[F]** A8 §5 "Common evidence — UNRESOLVED"; A5 blocked as `CALIBRATION_EVIDENCE_INSUFFICIENT` with "the legacy v1.4 30-day value is not adopted"; A8-M §3 "No numeric publication-delay allowance is approved or may be invented" | **[F]** `FreshnessStatus` thresholds (`market_staleness_hours: 24`) for market snapshots only | **[F]** no window for a regulator negative; the ICDR "last five years" is a *disclosure* window, not a source-coverage rule | **Yes** | The window and its source must be recorded as an approved parameter with the evidence that justified it; a test that an out-of-window negative cannot clear |

### 5.3 The six evidence states must stay six **[R]**

| # | State | Correct engine posture |
| --- | --- | --- |
| 1 | issuer disclosure says "no action disclosed" | disclosed negative, in-document basis only (A25 behaviour) — never called verified absence |
| 2 | search run, no matching result found | a *search* fact; not an absence finding unless R-S1+R-S4 hold |
| 3 | completed search of authoritative, adequately scoped sources for population × period | the only state that could support a corroborated absence — **and only if R-S9 approves the consequence** |
| 4 | search unavailable or incomplete | UNVERIFIED with reason (never a boolean) |
| 5 | positive adverse evidence located | TRIGGERED path, with locator + quote |
| 6 | conflicting evidence | UNKNOWN + reported divergence, precedence only if the source establishes it |

**[F]** The repository already distinguishes 1 and 4 in-document (A24/A25) and
already refuses "no results = absence" for issue terms. **[R]** Nothing may be
merged: no "no results" string becomes state 3 without an approved R-S1/R-S4.

### 5.4 Does K2 need a coverage-basis field? **[F]/[R]**

**[F]** Mechanically the record *can already* carry it: `_sources[]` (uri +
`content_hash` + both timestamps + `note`), `_evidence` with
`extraction_method`, and the knockout's own `missing` list; A18 L1's rule was
explicitly "**do not add fields or schema versions**" while achieving a verified
external link.

**[R]** Therefore a new field is **not** the minimum change. Two smaller,
sharper questions are: (i) K2's `when` reads a boolean, so no basis can influence
it without either reading a *second* input (a `sebi_ed_action_basis`-style
categorical, i.e. a real schema+config change) or (ii) accepting that basis is a
*displayed* fact and K2 stays basis-blind. Choosing (ii) is a legitimate policy
("the flag is the flag"); choosing (i) is a knockout-semantics change and must be
recorded as one, with a config version and a golden decision. **[?]** Ramki must
pick; A8-R §7 says R-S1's authority answer should drive it, and this pass agrees.

**[R] Proposed R-S11, absent from the current provision list: independence of
the two regulators.** A source covering SEBI's pages cannot clear an ED action.
Today this is enforced only inside the document (both regulators must be named for
the structured negative, `sebi_named and ed_named`). Any external contract should
state that a K2-relevant negative requires per-regulator coverage, and the
acceptance test should be: an SEBI-only external result leaves the flag UNVERIFIED.

### 5.5 Recommended staging for A8-R (sequence, not approval) **[R]**

1. **Answer R-S1 and R-S11 only.** Without an authority set and the per-regulator
   rule, everything downstream is ungrounded, and no code question arises.
2. **Decide R-S9's policy consequence** (does any external basis change K2?) —
   explicitly a knockout decision, with config-version and golden consequences
   named at that point, before any retrieval work.
3. **Contract the upstream surface, not engine code:** an enrichment/`_sources`
   evidence package following A18 L1 (existing fields), A8-M §5's preserved list,
   and `issue_terms`' four outcomes. This respects RUNBOOK §9 by keeping
   `evaluate` free of I/O; the retrieval sits where `issue_terms` and the
   connectors' snapshot ingestion already sit.
4. **Then** R-S2/R-S3/R-S4/R-S7 acceptance suites as fixtures with the six states
   of §5.3, each asserting the *state*, never a boolean.
5. **R-S5/R-S10** need approved numeric parameters with evidence, on the A5
   precedent (which shows a plausible number — v1.4's 30 days — is *not* adopted
   without evidence).
6. Keep the current interim consequences (UNKNOWN/disclosure-only) until 1–2 are
   answered; A8's own restriction already forbids using policy directions to claim
   a provider-backed snapshot is verified.

---

## 6. Cross-cutting decision matrix

| Field | A26 — tax-only proceedings | A27 — auditor / CARO / disputed tax | A8-R — regulator source coverage |
| --- | --- | --- | --- |
| **Business question** | Does a statutory tax dispute say anything about promoter track record? | Can the engine state §11's `EOM/CARO only`, and is the "disputed tax" wording policy or residue? | May an absence of a regulator action ever be *verified* rather than disclosed-not-contradicted? |
| **Authoritative criterion today** | §4.3 `:253` collect tax; v1.3 `:103` adverse = criminal/regulatory **on promoters**; no §11-like litigation-state list in v1.5 | §11 `:547-558`; config `:1727` formula text; §17 retain penalties | none: A8 scope excludes regulator data; A8-M scoped to `nifty_trend` **only**; A8 implementation authority "**Not granted**" |
| **Implementation today** | tax ignored by the bucket; K5 prices magnitude; `eom_caro` prices severity if supplied | 4 inputs, no CARO route, `eom_only` fires on *reputation*; RK shows the misnomer | A24/A25 in-document negatives; `sebi_ed_action_active` boolean; `_evidence`/`notes` basis |
| **Confirmed evidence / history** | `git log -S"disputed tax" -- engine/` empty; 30-criterion sweep finds no CL-consuming criterion | v1.4 `:297` → `49c9944` copied into v1.6; `caro_remarks` schema-only at `:659` | `pages_with_table_head=0` on all 3 real filings; RUNBOOK §9 no-fetch; A18/A8-M limits verbatim |
| **Unresolved ambiguity** | **[?]** whether exposure-only treatment is *intended* | **[?]** whether §11's CARO clause must be met by wiring `caro_remarks` or by re-scoping §11; whether `eom_only` should be renamed | **[?]** authority set, per-regulator independence, and the K2 consequence |
| **Options** | A retain UNKNOWN · B map to `criminal_or_regulatory` · C new bucket (new version) | A wording fix · B consume `caro_remarks` · C accept divergence explicitly · D new opinion state | stay in-document · external authority contract · richer record basis |
| **Recommendation** | **A**, recorded as intended policy; B rejected on three grounds; C only with its own record | **A + B in that order**, with the semantics decision before wiring; D rejected | answer R-S1+R-S11 then R-S9; **no** engine retrieval; keep six states distinct |
| **Required approval** | decision record only (no version change) | config **version** + golden re-baseline act + (for B) extraction-contract approval | a new source contract + a knockout-semantics decision + schema/taxonomy change if any basis field is added |
| **Scope if approved** | ~schema enum, `CATEGORICAL_DOMAIN`, 2 configs, `derived`, `builder`, `sections`, golden, tests-per-route (§2.6 table) | `sections.py` CARO route + `_auditor_bucket` + formula strings + 10 tenure tests + golden strings | upstream enrichment package + `_sources` pins + acceptance fixtures; engine scoring path untouched |
| **Risk of acting prematurely** | invents a scored category; over-penalises routine disputes; breaks the 100-point reconciliation and stored hashes | a bare boolean becomes "clean" by inference; second penalty on one fact | turns "no results" into verified absence; breaks the no-network design; grants de-facto source qualification the A18 limit forbids |
| **Acceptance criteria** | tax-only filing keeps bucket absent + stated reason; basis noted; `check-config` 10×100; stored records untouched | absent `caro_remarks` ⇒ identical output; explicit negative ⇒ scored; unqualified+CARO ⇒ `eom_only`; golden re-baseline recorded | six states asserted per §5.3; per-regulator independence test; UNAVAILABLE/timeout never CLEAR; no I/O in `evaluate` |
| **Dependencies** | A27 (the auditor criterion is where tax lived); A20 (CL numerator) — settled, not reopened | A19 K1 (qualified → knockout) settled; `eom_materiality` governance (D-1) | A1 authority; A5 parameter precedent; A8 implementation authority (not granted); A18 L1 (no new fields) |

---

## 7. Exact questions for Ramki

A26 — answerable as posed:
1. Is a statutory tax dispute intended to say anything about **promoter**
   track record, yes/no? If no, do you record Option A as the intended policy?
2. If yes: which population — tax proceedings *against promoters/directors*
   only, or any disclosed tax proceeding?
3. Do you accept that exposure is governed by **K5 only** (no graduated
   contingent-liability criterion exists) and severity by **`eom_caro` only**?
4. Do you authorise a **config-version** change (never an in-place edit) as the
   vehicle for any new litigation bucket, together with a golden re-baseline act?

A27:
5. Does §11's `EOM/CARO only` require CARO to affect `auditor_bucket`, or is the
   `eom_caro` penalty the correct home for CARO severity and §11 read that way?
6. What should `caro_remarks: false` mean: "issuer states no CARO exceptions",
   "we looked and found none", or nothing at all? (Recommended: only the first,
   sourced from the filing's own sentence.)
7. Should absence (field not supplied) hold the worst CARO magnitude in the lower
   bound exactly as `eom_caro` already does for `eom_materiality`?
8. Do you accept the config's "disputed tax" wording as **stale text to be
   corrected** (Option A), and if so, in a new config version or as a documented
   non-policy annotation?
9. Should the mid-tier be renamed away from `eom_only`, given the RK
   "semantic misnomer" finding?
10. Do the five unconsumed governance inputs get a lint that every declared
    governance field has a consumer (tooling only, no scoring change)?

A8-R:
11. Which sources, if any, are authoritative for a *negative* on SEBI and on ED —
    separately (R-S1, R-S11)?
12. May any external negative change **K2's** state, or is basis display-only
    (R-S9)? If it may change, is that a knockout-semantics decision recorded as
    such, with a config version?
13. What population × period must a searched index establish for a negative to be
    a finding (R-S4)?
14. Which currency window governs a negative claim, and with what evidence
    (R-S10, on the A5 precedent)?
15. Do you confirm external corroboration stays **upstream** (enrichment /
    `_sources`), with `evaluate` performing no network I/O (RUNBOOK §9)?

---

## 8. Changes this investigation would *propose* to existing records — not applied

Recorded here so a future authorised pass can act on them; the three decision
records were deliberately left untouched:

1. **A26 §4 item 8 overstates the consumer surface** — `frontend/app.js`,
   `presentation/*` and `excel.py` contain no `litigation_bucket` reference
   (verified by counting across the tree); the real UI cost is one test plus a
   favourability check on the displayed string.
2. **A26 §5.4's either/or resolves** — v1.5 §11 never contained a disputed-tax
   state; the wording in the shipped configs is v1.3/v1.4 inheritance, so the
   "lost in translation" branch is not supported and the tax question belongs to
   §4.3's unscored input list, not to the auditor criterion.
3. **A26 §5.2 understates the magnitude coverage** — besides A20/K5, the
   `eom_caro` penalty prices EoM/CARO severity from reviewer-supplied
   `eom_materiality` (no extractor exists), which strengthens rather than
   weakens the retain-UNKNOWN case.
4. **A27 §3 understates Option A/B's cost, in two stages.** A *config*-wording
   edit changes no behaviour but flips `config_hash` → `result_hash` → the golden
   assertion (`tests/test_vishal_golden.py:52`), so it needs a config version and a
   golden re-baseline act. A *code*-string edit additionally changes text embedded
   at `fixtures/vishal_nirmiti/expected_derived.json:34` and
   `expected_score.json:324`. And the two texts are not reconciled by anything:
   `check-config` rule (14) compares only `implemented` with the metric registry,
   so a config formula that describes an unimplemented clause can sit there
   indefinitely — the "disputed tax" clause is an instance of exactly that.
5. **A27 should split into two decisions** — one for the stale tax wording (A) and
   one for CARO wiring (B), because they need different approvals.
6. **A8-R's provision list is missing per-regulator independence** (proposed
   R-S11) and should record that the governed carriers for external evidence
   (`_sources`/`_evidence`/`_cross_checks`, `supplemental-enrichment.v1`) already
   exist, so "no new fields" is available as an option rather than an assumption.
7. **A8-R should cite RUNBOOK §9** ("the engine never makes a network call") as a
   design constraint any R-S2 approval must confront — a fact not currently stated
   in that record.

---

## 9. Integrity confirmation

* **[F]** No implementation file, test, fixture, schema, config, scoring constant
  or historical evaluation was modified: `git status --porcelain` was empty before
  this document was written and the only files touched by this pass are this
  report and one dated tracker entry.
* **[F]** The A24/A25 code published at `41f2f86` is unaltered; the 96-test
  focused run above passes against it unchanged.
* **[F]** `main` (`01ba66c`) untouched; PR #6 remains open and unmerged with head
  `e05c0ef` and base `arena/573e69a4-ipo-screening-engine`; no amend, reset or
  force-push; nothing pushed beyond this branch.
* **[F]** No historical evaluation was re-run, re-hashed or republished; no golden
  hash was regenerated. The only numbers re-measured here are the read-only
  greps/probes in §2.5 and §3.7, which assert nothing about stored records.
* **[R]** Nothing in this document is an approval. Each recommendation above
  requires Ramki's explicit decision, and the items with config, schema, golden or
  knockout consequences additionally require a separately authorised change.
