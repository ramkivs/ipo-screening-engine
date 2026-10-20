# A27 — The Auditor Criterion's Unconsumed Clauses: CARO Remarks and Disputed Tax

- **Decision ID:** A27
- **Title:** Whether `derived.auditor_bucket` must implement the "CARO" and "disputed tax" triggers its governed formula names, or whether the formula text should state what the engine scores
- **Record type:** **PROPOSAL — decision request.** Per `handoff/decisions/CONVENTION.md` rule 4 this record is neither an approval nor implementation authority; per rule 5 it does not present any resolution as v1.5 text.
- **Decision status:** **PROPOSED / UNRESOLVED — RAMKI APPROVAL REQUIRED. Nothing in this record is implemented.**
- **Decision authority:** RAMKI (per `handoff/decisions/A1-evidence-adjudication-authority.md`).
- **Date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Repository / baseline:** branch `arena/95234306-ipo-screening-engine` at `41f2f86` (the A24/A25 implementation commit); `main` `01ba66c12ca1195fd7acbd287c3e39a019808094`; PR #6 `OPEN`/`UNMERGED`.
- **Raised by:** the A26 historical investigation requested on 2026-10-20, which found that the question Ramki was asked ("was `disputed tax` dropped in v1.5?") rests on a premise the history does not support. See `handoff/decisions/A26-tax-only-proceedings-classification.md` §11.
- **Scope:** one governed formula string, one declared input field, and the criterion `auditor` (Module D, `max 2`, map `clean_reputed 2 / eom_only 1 / unstable_or_repeated_eom 0`).
- **Out of scope and untouched:** the criterion's weight, its map, `config_validation.py`, both config versions, `schema/`, K1 (qualified-opinion knockout), `litigation_bucket` and its buckets, extraction, fixtures, the golden record, and every historical evaluation.
- **Implementation authority:** NOT GRANTED by this record.

## 1. The divergence, in the two texts

`config/ipo-config.v1.5.0.json:1727` and `config/ipo-config.v1.6.0.json:1727` (identical):

> `clean_reputed: reputed firm, unqualified, no change, no EOM; eom_only: Emphasis of Matter/CARO/disputed tax only; unstable_or_repeated_eom: auditor change in 3Y or repeated EoM. … UNKNOWN when the opinion is not supplied. A qualified/adverse/disclaimer opinion is a knockout, not a bucket.`

`engine/ipo_screening/derived.py:1428-1436`, the implementation the config's `metric`
field points at:

> `clean_reputed: unqualified, no auditor change, no EOM; eom_only: EOM/CARO only and no change; unstable_or_repeated_eom: auditor change within 3 years or repeated EOM. …`

with `inputs = ["governance.auditor_opinion", "governance.auditor_reputed",
"governance.auditor_changed_3y", "governance.repeated_eom"]`.

So the config formula names **three** triggers for the 1-point bucket. The code consumes
one of them: EoM, reached through `auditor_opinion == "emphasis_of_matter"` or
`repeated_eom is True` (`derived.py:1458-1490`). "CARO" appears in the code's own formula
string but no CARO input is read; "disputed tax" appears in neither.

## 2. Why this is not a scoring bug Arena may fix, and not a settled design either

| Fact | Evidence (all read 2026-10-20) |
| --- | --- |
| The clause is not new, and was never removed | v1.3 spec `handoff/reference/Claude_IPO Screening Engine v 1.3 — Specification.md:105` already scored "Emphasis of Matter / CARO remarks / disputed tax matters only = 1"; `handoff/reference/ipo-config.json:297` (v1.4) carried it; `git show fb822e5:config/ipo-config.v1.5.0.json` contains it (the commit that implemented v1.5); `git log --all -S"disputed tax" -- engine/` returns **nothing** |
| The engine never had the clause to lose | same `git log` search over `engine/`; `derived._auditor_bucket`'s four inputs |
| `caro_remarks` exists as a governed input and is consumed by nothing | `schema/ipo-input.v1.5.schema.json:659`; a repository-wide search for `caro_remarks` across `*.py`, `*.js`, `*.json`, `*.md` matches **that one line and no other** — not the engine, not the builder, not an extractor, not a test, not the frontend, not any fixture or stored evaluation |
| Disputed tax has no input at all | the governance block of the input schema has 19 properties, none tax-related; `"tax"` occurs only as `financials.periods[].tax`, the tax expense line |
| Four other governance inputs are in the same state | `eom_count_3y`, `auditor_change_count_3y`, `regulatory_actions`, `independent_director_count` are declared and have no reference anywhere in `engine/` |

Neither reading can be adopted as truth: the clause may be an aspiration the input surface
was never built for, or a rule the specification still states and the engine is simply wrong
about. Choosing between them is a governed decision about what the criterion *means*, which
A1 reserves to RAMKI. Arena does not infer intent from the absence of code.

## 3. Options (one decision each; no option is recommended as approved)

**Option A — amend the formula text to match the engine.** The config would read
"eom_only: Emphasis of Matter only and no change", and CARO / disputed tax would be recorded
as out-of-scope inputs. Cheapest, no score movement anywhere, but it *narrows the governed
semantics* by deleting a disclosure the specification still lists. Status: not taken.

**Option B — consume `governance.caro_remarks` in `auditor_bucket`.** A declared, schema-valid
input, so **no schema change and no config change** is needed: `eom_only` would fire when
`caro_remarks` states remarks and the opinion is unqualified. Downstream effects, measured
where the repository allows it:

1. No historical result can move. No stored input, fixture, or evaluation supplies
   `caro_remarks` (evidence in §2: across the repository's `*.py`, `*.js`, `*.json` and `*.md` files the key appears exactly once, in the schema), so its absence must keep producing today's answer. That
   forces the semantics decision first: an **absent** `caro_remarks` must mean "not
   established" and must **not** be read as "no CARO remarks" — otherwise this pass would
   reintroduce exactly the favourable default D-5 and A24 removed. If absent ⇒ UNKNOWN,
   then every filing without the field becomes UNKNOWN on the auditor criterion, which is a
   large availability loss; if absent ⇒ no-remarks, the change is inert for existing inputs
   and only affects filings that do supply it. **Both readings are defensible; neither is
   Arena's to pick.**
2. PDF-only pipelines would still not benefit: no extractor emits `caro_remarks` (search
   above), so the clause would be reachable only through reviewer-supplied input unless an
   extraction route is also authorised.
3. A scoring movement is expected where CARO remarks exist without an EoM: 2 → 1 on
   `auditor`, i.e. Module D and the available base shift by 1 point for those filings. No
   such filing exists in this repository, so no pin here would need re-baselining — verified
   by the absence of the key in every fixture and stored record, not assumed.

**Option C — implement disputed tax too.** Requires a new governance input (name, type,
nullability), a schema change and version decision, extraction of tax disputes from the audit
report / contingent-liabilities note, and the same absent-vs-nil rule as Option B. It also
interacts with A26: the ICDR "Tax Proceedings" column is already parsed in the litigation
route and deliberately maps to no bucket; using the same disclosure as an auditor input must
not double-count the exposure A20 already prices through the contingent-liability numerator
and K5. Status: not taken.

**Option D — record the clauses as governed-but-unscored inputs, explicitly.** Keep both
texts as they are and mark the divergence as an accepted, documented non-score in
`docs/TRACEABILITY_MATRIX.md`. **Not adopted in this pass:** Ramki's instruction was to record
it as a *known unresolved gap*, which is what GAP-4.3 in that matrix now says. If Ramki wants
the gap closed as permanent instead, that is a positive decision to record, not a silence.

## 4. What is needed to answer

1. Which of A / B / C / D governs the auditor criterion?
2. If B or C: how is an **absent** input to be read — `no remarks` (favourable) or `not
   established` (UNKNOWN)? This is the same question A24 answered for litigation coverage and
   A25 for regulatory absence, and the answer must be consistent across the three.
3. If B or C: is an extraction route authorised, or is the clause reviewer-supplied-input only?
4. If A: does the v1.5 §11 wording in `docs/TRACEABILITY_MATRIX.md` get amended to match, and
   does the v1.3 spec row get recorded as superseded (rule 5: the spec remains authoritative,
   so a supersession must be stated, not implied)?
5. `eom_count_3y`, `auditor_change_count_3y`, `regulatory_actions`,
   `independent_director_count` are declared and unconsumed as well: is that list deliberate,
   or is a general "declared-but-unconsumed input" review warranted? A review costs nothing
   here (the search is one grep); the fixes it would recommend do not exist yet.

## 5. Consequences while this record is unapproved

- `auditor_bucket` keeps scoring EoM only, exactly as it has since `fb822e5`; nothing in this
  record changed that, and no test expectation moved.
- `docs/TRACEABILITY_MATRIX.md` row **GAP-4.3** records the divergence as `BLOCKED —
  UNRESOLVED`, not as a completed non-score.
- A26 remains the record for tax-only *litigation* classification; this record is only about
  the auditor criterion, and the two must be decided separately — a decision on one does not
  license the other.
