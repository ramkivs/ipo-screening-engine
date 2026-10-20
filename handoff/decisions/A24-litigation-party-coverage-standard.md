# A24 — Party Coverage Required for a `clean` Litigation Conclusion

- **Decision ID:** A24
- **Title:** Minimum party coverage for the favourable `clean` bucket of `governance.litigation_bucket`
- **Record type:** **PROPOSAL — decision request.** Under `handoff/decisions/CONVENTION.md` rule 4 this record is *not* an approval and *not* implementation authority; it carries Arena's analysis and recommendation for RAMKI's decision.
- **Decision status:** **PROPOSED / UNRESOLVED — RAMKI APPROVAL REQUIRED.** Nothing in this record is implemented.
- **Decision authority:** RAMKI (per `handoff/decisions/A1-evidence-adjudication-authority.md`).
- **Date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Repository / baseline:** `ramkivs/ipo-screening-engine`, branch `arena/95234306-ipo-screening-engine` at remotely verified commit `38f51571d2a043c91fed054d90ea01141ca41de9`; `main` `01ba66c12ca1195fd7acbd287c3e39a019808094`; PR #6 `OPEN`/`UNMERGED` at `e05c0efbca1ecb3024e52da73a22e180ea171118`.
- **Supersedes / completes:** the "Party-coverage standard for `clean`" item of `handoff/decisions/A23-litigation-regulatory-evidence-defaults.md` §6.1 and §6A.1.
- **Scope:** what an issuer disclosure must cover before the extraction layer may conclude `clean`; the same question for the ICDR summary-table route.
- **Out of scope and unchanged:** the bucket taxonomy, `config/ipo-config.v1.5.0.json` and `config/ipo-config.v1.6.0.json`, `schema/ipo-input.v1.5.schema.json`, `config_validation.py`, `derived.py`, `scoring.py`, `knockouts.py`, confidence rules, `fixtures/` and the golden record, historical evaluations. **No code was changed for this record.**
- **Implementation authority:** NOT GRANTED by this record.

## 1. Problem statement

`litigation` is a scored criterion (Module D, 4 points) whose favourable value `clean` means *"no material litigation across the relevant population"*. The engine currently reaches `clean` from a disclosure that covers **part** of that population. The question this record puts to RAMKI is exactly: **which parties must a denial reach before `clean` may be concluded, and what happens when coverage is partial, ambiguous, or unparseable?**

The two extraction routes answer it differently today, which is itself a defect in the *consistency* of the record even after A23 §6A.1 aligned the *proceeding-type* dimension.

## 2. Existing authoritative rules and evidence

| Layer | Authoritative text | What it fixes |
|---|---|---|
| v1.5 specification §4.3 (`handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md:244-255`) | governance inputs include "promoter litigation", "company litigation", "regulatory actions", "SEBI/ED actions", "tax proceedings" | the *inputs*; **no party-coverage rule, no bucket definition** |
| v1.5 §11 (`:547-556`) | "Retain the 15-point framework"; auditor states | no litigation rubric |
| v1.5 §3.2 (`:85-93`) | `VALUE / UNKNOWN / NOT_APPLICABLE`; "`0` is a numeric value, not an unknown marker"; no `x \|\| 0` fallbacks for governance inputs | absence must stay UNKNOWN — *not* be resolved favourably |
| Upstream reference config `handoff/reference/ipo-config.json:294` (v1.4.0) | `"litigation_bucket": "clean / minor_civil / criminal_or_regulatory (promoters, directors, company)"` | **the party population, explicitly: promoters, directors, company** |
| `engine/ipo_screening/derived.py:1384` | `formula = "clean / minor_civil / criminal_or_regulatory across promoters, directors and the company"`; UNKNOWN reason at `:1390` "the litigation status of the promoters, directors and company is not established" | the same three parties, in the shipped metric definition |
| `config/ipo-config.v1.5.0.json` + `v1.6.0.json` | criterion `litigation`, label "Promoter track record & litigation", `map: {clean: 4, minor_civil: 2, criminal_or_regulatory: 0}` | three buckets only; identical in both config versions |
| `schema/ipo-input.v1.5.schema.json` | `litigation_bucket: {"enum": ["clean","minor_civil","criminal_or_regulatory", null]}` | `null` is the supported UNKNOWN |
| `engine/ipo_screening/config_validation.py:53` | `"litigation_bucket": {"clean","minor_civil","criminal_or_regulatory"}` | a fourth bucket value is rejected |
| `engine/ipo_screening/extraction/sections.py` | `_LIT_PARTY` (`:1476-1482`) accepts *any one* of company / subsidiary / director / promoter / KMP / senior management / group company; `_lit_absence_is_comprehensive` (`:1534-1557`) gates the **type** dimension only; `_litigation_table_finding` (`:2008-2106`) requires the criminal/civil/regulatory **columns** and never requires a party **row** | how far coverage is checked today |
| `engine/ipo_screening/extraction/builder.py:316-333` | `_LITIGATION_BUCKET_ALIASES` maps a **supplied** `"nil"/"none"/"no_litigation"` to `clean` | a human-asserted value is taken at face value (different act, see §5.4) |

## 3. Current behaviour, measured on this commit

Synthetic-page probes against the published `SectionExtractor` (script run in this pass; same code path the builder consumes). "Parties noted" is the `notes` audit string the record already emits.

| Shape | Today | Comment |
|---|---|---|
| nil naming Company + Promoters (no Directors) | `clean` [Company, Promoters] | partial party coverage is enough |
| nil naming Company only | `clean` [Company] | same |
| nil naming Directors + Promoters (no issuer) | `clean` [Directors, Promoters] | same |
| nil naming **KMP only** | `clean` [KMP] | a party *outside* the criterion's population produces the favourable bucket |
| nil naming Company + Directors + Promoters | `clean` [all three] | correct |
| ICDR table with only `Against our Company` rows, all nil | `clean` (header quoted) | **table route has no party-row requirement** |
| ICDR table with `Company` + `Promoters` rows, no `Directors` row | `clean` | same gap |
| ICDR table with all party rows nil | — (see §3.1) | |
| adverse row present (`Against our Directors \| 2`) | `criminal_or_regulatory` [Directors] | adverse side unaffected by any party gate |
| unreadable adverse row | no bucket (UNKNOWN) | fail-closed already correct |

**3.1 A defect found while probing, recorded here rather than fixed.** A party label carrying a parenthetical — the format real filings use, e.g. `Against our Directors (excluding Promoters)` — shifts the cell alignment of `_LIT_TABLE_ROW`, so `len(parts) != len(keys)` and the row is counted **unreadable**: an all-nil table in that format yields *no bucket* (`UNKNOWN`) instead of `clean`, and if such a row were the only adverse row, the bucket would stay UNKNOWN even though the disclosure is readable to a human. The direction is safe (it never fabricates a favourable value) but it loses disclosure evidence, and it interacts with this decision: under Option A/B the *table* route would newly require party rows, so the parenthetical parsing gap must be repaired in the same change or a filing will be marked UNKNOWN for a reason that has nothing to do with its coverage. It is recorded here as an open, unfixed defect with an exact reproduction.

## 4. Options considered

All three options keep the same rule for adverse evidence (an adverse proceeding against *any* party in `_LIT_PARTY` is in scope and reaches the unfavourable buckets) and the same rule that proceedings **initiated by** the issuer ("By our Company") are not adverse exposure. They differ only in what a *denial* must cover before it may conclude `clean`.

### Option A — "the parties the existing criterion establishes, enumerated"

Coverage must reach every party the criterion's own definition names, enumerated here as **the Company, the Promoters, and the Directors** (including Directors described as "excluding Promoters"). No other party category is required, because the criterion does not name one.

### Option B — "Company + Promoters + Directors"

Identical to A. **The two options converge**: A asks for the criterion's population "with the precise categories explicitly enumerated", and the enumeration is fixed by the reference config and `derived.py:1384`, both of which say exactly those three. There is therefore no behavioural difference left to choose between A and B; what must be decided is A/B versus C.

### Option C — the full ICDR disclosure population (Company, Promoters, Directors, KMP, Senior Management)

Requires the denial to reach every party class the ICDR summary table can carry. Effect measured in this pass: **both** committed filings that earn `clean` today (`class_a`, `class_b`) move to `UNKNOWN`; only wording that also names KMP and Senior Management retains `clean`. Adverse routes are untouched. This *extends* the criterion beyond its stated population, so under CONVENTION rule 5 it would need an explicit amendment of the metric definition, not just a coverage rule.

### Comparison on the dimensions this decision has to settle

| Dimension | A ≡ B | C | Status quo (D) |
|---|---|---|---|
| Parties that must be covered | Company, Promoters, Directors | + KMP, Senior Management | any one party token, incl. KMP alone |
| Must each party be covered across criminal / civil / regulatory / tax? | The existing A23 §6A.1 rule already requires the **criminal/regulatory** and **material civil** dimensions; regulatory is part of that first dimension; **tax is not required**, because the bucket does not score tax (A26) | same, but KMP/Senior-Mgmt rows must also be nil | dimension rule only |
| What counts as adequate disclosure | (i) a prose nil naming all three parties and both dimensions, or (ii) a summary table whose `Against our Company / Promoters / Directors` rows are present, readable, and nil across the criminal/civil/regulatory columns, located in the litigation section | as B, plus KMP and Senior Management rows | any matching sentence |
| Partial coverage | **no bucket** ⇒ `STATE_UNKNOWN`, 4 points unavailable (not zero), reason in `missing_inputs`/`notes`; parties actually named are recorded in `notes` | as B | favourable |
| Ambiguous ("except as stated below", "other than the below") | treated as today: an affirmative disclosure found elsewhere governs; a nil alone cannot be read as blanket | as B | as B |
| Missing / unparseable rows | no favourable conclusion (already the rule: `unreadable_adverse_rows` blocks); §3.1 must be repaired so *readable* rows are not mis-counted as unparseable | as B | as B |
| Issuer-initiated proceedings | never adverse; a nil in a column scoped to a subset (e.g. "against our Promoters") clears nothing | as B | as B |
| Effect on dispositions | `clean` becomes rarer and *earned*; adverse buckets unchanged; filings with genuinely nil disclosures keep 4/4 | also penalises filings whose disclosure follows the criterion's population but not the ICDR row list | unchanged |
| Compatibility | no schema, config, taxonomy or scoring change; consistent with v1.5 §3.2 (absence ⇒ UNKNOWN) | needs a metric-definition amendment + both configs | inconsistent with the criterion's own formula |

## 5. Recommended option and exact proposed semantics

**Recommend Option A ≡ B.** Not because it was recommended before — it was re-tested against the actual wording, and the decisive evidence is that the criterion's own definition, in both the upstream reference config (`:294`) and the shipped metric formula (`derived.py:1384`), enumerates exactly **promoters, directors and the company**. A coverage standard drawn from that enumeration is the *same* claim the metric already makes; anything narrower lets a one-party denial earn a three-party conclusion, and anything wider (C) silently amends the criterion.

Proposed normative text (for approval, then implementation in a separate authorized pass):

* **R1 — Population.** `clean` may be concluded only where the disclosure denies material litigation and criminal/regulatory action **as to the Company, its Promoters and its Directors** (Directors "excluding Promoters" count), across both scored dimensions (criminal/regulatory and material civil), per the A23 §6A.1 type rule.
* **R2 — Evidence forms.** Either (a) prose naming all three parties, or (b) the ICDR summary table with a present, readable, nil row for each of the three parties on the `Against our …` side. A `Nil` in a column or row scoped to a subset covers only that subset.
* **R3 — Issuer identity precision.** "our Company" / "the Company" must be matched as the issuer; a reference to *Group Companies* must not be counted as coverage of the issuer (measured: `class_b`'s sentence names "our Promoters, Directors, or Group Companies" and would otherwise pass on a substring match).
* **R4 — Shortfall ⇒ UNKNOWN, never a penalty.** If coverage is partial, ambiguous, absent or unparseable, no bucket is emitted: the criterion is `STATE_UNKNOWN`, its 4 points move to `unknown_points` (availability falls; score is not reduced to 0), the reason is listed, and `notes` records which parties *were* named.
* **R5 — Symmetry across routes.** R1–R4 apply to the prose and table routes identically; implementing them for one route only re-creates the A23 §6A.1 inconsistency in the opposite direction.
* **R6 — Adverse direction unchanged.** Any adverse proceeding against any party in `_LIT_PARTY` still sets the unfavourable bucket, regardless of R1; R1 constrains only the favourable conclusion.
* **R7 — Supplied inputs.** A human-supplied `governance.litigation_bucket: "nil"|"none"` normalised to `clean` by `builder._LITIGATION_BUCKET_ALIASES` is an *assertion by the reviewer*, not an inference by the engine, and is out of scope for R1; if RAMKI wishes coverage requirements to bind supplied inputs too, that is a separate canonical-evidence rule (A15 territory) and should be decided as such.
* **R8 — Prerequisite.** §3.1's parenthetical-row parsing defect is repaired in the same pass, with a test, so that table-route coverage failures mean *the filing did not disclose*, not *the parser mis-read the row*.

## 6. Rationale and trade-offs

* Rationale: the bucket is a statement about three parties; a conclusion must not exceed its evidence (the same principle D-1…D-5 applied to defaults, headings and quotations). The rule is verifiable against the filing's own text, needs no external source, and closes a two-route inconsistency.
* Trade-off 1 — **availability.** Filings whose nil covers fewer parties lose 4/4 and gain 4 `unknown_points`. Measured on this repository with the gate applied in memory and then evaluated exactly as the tests do: `class_b` moves to UNKNOWN — **41.0 → 37.0**, available **55.0 → 51.0**, Module D **6.0 → 2.0/15**, unknown points **6.0 → 10.0**; `class_a` is unchanged at `clean`; class_c/d/e are already UNKNOWN from A23; adverse cases and the golden record are unaffected (vishal PDF still `criminal_or_regulatory`; golden hash `e84f8bc0f9b9…5619e1` recomputed intact after this pass).
* Trade-off 2 — **false negatives on condensed documents.** Abridged prospectus extracts sometimes omit the Directors row while disclosing it in the full RHP; under R1 those become UNKNOWN rather than `clean`. The A23 §5 evidence limit (HD Fire's §12 points to RHP p. 356, unretrievable here) is exactly this case, so the safe answer is UNKNOWN pending the complete document.
* Trade-off 3 — **no scoring change.** Points, weights, thresholds, knockout semantics and the three-value map are untouched; only *when* a value may be asserted changes. UNKNOWN already has governed behaviour, so nothing needs a new state.

## 7. Required acceptance criteria and regression tests (to accompany approval)

1. Company+Promoters-only prose nil ⇒ no bucket; Company-only ⇒ no bucket; KMP-only ⇒ no bucket; all three parties + both dimensions ⇒ `clean` with the sentence quoted verbatim.
2. "Group Companies" does not satisfy the issuer requirement (R3), and a sentence naming both the issuer and Group Companies does.
3. Table route: `Against our Company` nil alone ⇒ no bucket; all three parties' `Against our …` rows nil with the criminal/civil/regulatory columns present ⇒ `clean` quoting the header; a `Directors (excluding Promoters)` row parses without a cell shift (R8).
4. Unchanged-behaviour pins: `class_a` keeps `clean`; vishal and Jio keep `criminal_or_regulatory` with their page-cited quotes; `complete_sample_rhp*` emit no bucket; HD Fire's §12 shapes keep their A23-confirmed outcomes; 0 `xfail` introduced.
5. Score/availability pairs re-measured and recorded, not hand-edited, for any fixture that moves — for `class_b` the gate was measured above (41.0/55.0 → 37.0/51.0, Module D 6.0 → 2.0/15, unknown 6.0 → 10.0) and the implementation pass must reproduce those numbers rather than restate them — with `check-config` still `valid True` and the vishal golden hash unchanged.
6. Both config versions (v1.5.0, v1.6.0) still reconcile to 100 points with no criterion change.

## 8. Affected components and downstream consumers

`extraction/sections.py` (prose-absence gate, table row/coverage logic, `_lit_parties_named` notes), `extraction/builder.py` (no change under R7), `derived.py` (no change; the formula string is the source of the enumeration), tests `tests/test_litigation_regulatory_defaults.py`, `tests/test_extraction_phase5b.py` (class_* pins), `tests/test_hd_fire_primary_source_extraction.py`, `tests/test_rk_fashion_reconciliation.py`, `tests/test_ui7_ingestion.py`; documentation `docs/TRACEABILITY_MATRIX.md` §4.3/§11 rows and `docs/RUNBOOK.md`; the presentation/API layer and Excel export consume the bucket value only and need no change (they already render UNKNOWN distinctly — A23 §6A.3). Historical evaluation records are not re-run.

## 9. Compatibility and migration

No schema, config or taxonomy change, so stored records remain valid and replayable; a record evaluated before approval keeps its `clean` conclusion, and any *re-evaluation* after approval would move the affected filings to UNKNOWN — that asymmetry is why approval must state whether the rule applies prospectively only (recommended, consistent with D-5's "no historical re-run" discipline). `fixtures/vishal_nirmiti/input.json` supplies `criminal_or_regulatory` (adverse) and the Jio fixture likewise, so **no golden or historical fixture needs re-pinning** (measured: the golden hash is not on this decision's path).

## 10. Dependencies on other decisions or contracts

* **A26 (tax classification)** — R1 deliberately does not require tax coverage; if A26 decides tax belongs in a bucket, R1's dimension list must be revisited in the same change.
* **A8 / A25** — none. This decision is about coverage of the issuer's own document and needs no external retrieval, which is why it is decidable now.
* A23 §6A.1's type-dimension rule is a precondition and is already published.

## 11. Questions for RAMKI (answerable as posed)

1. Do you approve R1–R6 (prospective only) as the party-coverage standard for `clean`, i.e. Company + Promoters + Directors as named by the criterion's own definition?
2. Do you reject Option C (KMP + Senior Management), keeping the criterion's population as written, or do you prefer to amend the metric definition to the full ICDR population?
3. Do you confirm R7 — that human-supplied bucket values remain reviewer assertions outside this standard?
4. Do you authorise, in the same future pass, the §3.1 parenthetical-row repair (R8)?

## 12. Interim behaviour while this record is unapproved

Today's rule stands: the A23 §6A.1 dimension gate is enforced; party coverage is not required beyond one party token, and the recorded `notes` string names the parties actually covered. This is the fail-closed-but-incomplete state, and no part of this proposal has been applied.
