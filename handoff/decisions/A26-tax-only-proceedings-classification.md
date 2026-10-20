# A26 — Classification of Tax-Only Adverse Proceedings in the Litigation Criterion

- **Decision ID:** A26
- **Title:** Whether adverse tax proceedings belong in `litigation_bucket`, and what their absence from the taxonomy costs
- **Record type:** **PROPOSAL — taxonomy decision request.** CONVENTION rule 4: this record is not an approval and not implementation authority.
- **Decision status:** **PROPOSED / UNRESOLVED — RAMKI APPROVAL REQUIRED.** **No mapping, bucket, schema, config or fixture change was made in this pass.**
- **Date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Repository / baseline:** branch `arena/95234306-ipo-screening-engine` at remotely verified `38f51571d2a043c91fed054d90ea01141ca41de9`; `main` `01ba66c…`; PR #6 `OPEN`/`UNMERGED` at `e05c0ef…`.
- **Completes:** A23 §6.4 / §6A.4. **Related:** A24 (party/dimension coverage), A20 (K5 contingent-liability numerator, approved).
- **Implementation authority:** NOT GRANTED by this record.

## 1. Problem statement

v1.5 §4.3 lists **"tax proceedings"** among the governance inputs the engine must handle, alongside "regulatory actions" and "SEBI/ED actions". The litigation criterion's bucket map, however, has exactly three values — `clean`, `minor_civil`, `criminal_or_regulatory` — none of which names tax. So an issuer disclosure of *only* adverse tax proceedings cannot be placed: it is not "clean" (something is disclosed), and calling it "criminal or regulatory" is a taxonomy claim nobody has made. Today such a filing gets **no bucket ⇒ UNKNOWN ⇒ the criterion's 4 points are unavailable**, which is safe but leaves a spec-listed input unconsumed. `docs/TRACEABILITY_MATRIX.md` rows for §4.3 and §11 list `litigation_bucket` and `sebi_ed_action_active` as DONE with **no metric for tax proceedings**, which is the documented form of the same gap.

## 2. Existing semantics, precisely

| Place | Text | Meaning |
|---|---|---|
| `config/ipo-config.v1.5.0.json` / `v1.6.0.json` | criterion `litigation`, label "Promoter track record & litigation", `map {clean: 4, minor_civil: 2, criminal_or_regulatory: 0}` | identical in both versions; the label ties the criterion to **track record**, i.e. conduct, not to financial magnitude |
| `derived.py:1384` | "clean / minor_civil / criminal_or_regulatory across promoters, directors and the company" | party population; no type taxonomy for tax |
| `schema/ipo-input.v1.5.schema.json` | `"enum": ["clean","minor_civil","criminal_or_regulatory", null]` | `null` is the supported "not established" |
| `config_validation.py:53` | `CATEGORICAL_DOMAIN["litigation_bucket"]` = those three names | a fourth value is **rejected by validation** |
| `builder.py:316-333` | aliases `criminal`/`regulatory` → `criminal_or_regulatory`; `nil`/`none`/`no_litigation` → `clean` | supplied synonyms; nothing for tax |
| `sections.py` `_LIT_TABLE_COLUMNS` | the ICDR table's **"Tax Proceedings"** column *is* parsed (as `tax`) | the disclosure form is recognised, deliberately without a bucket |
| `sections.py::_litigation_table_finding` | a count in a column that maps to no governed bucket sets `unmapped` ⇒ `clean` blocked, no bucket emitted | "disclosed but unclassifiable" already has a defined effect |
| A23 §6A.1 | a prose nil covering **only** tax does not establish `clean` | measured: `C4 prose tax denial only` ⇒ no bucket |
| A20 (D-2, approved) | `financials.contingent_liabilities` = the disclosed total of the contingent-liabilities section, commitments excluded | a tax demand disclosed in that note is **already counted** in the K5 numerator and in the contingent-liability criteria |
| K5 | "Contingent liabilities >50% of net worth (or unquantified)" | where the **financial magnitude** of tax disputes is governed |
| v1.5 §11 / reference `handoff/reference/ipo-config.json:297` | v1.5: auditor states are "clean/unqualified", "EOM/CARO only", "repeated EOM…", "qualified → knockout". The **upstream v1.4** text read `eom_only: reputed firm, unqualified, no change; …disputed tax only` | the reference taxonomy placed *disputed tax* in the **auditor** criterion; the v1.5 formula string (`derived.py:1431`) no longer mentions tax |

**Direction rules already in force** (measured, unchanged here): only `Against our …` rows are adverse; `By our Company | Nil | 3 | … | 0.40` — three tax proceedings *brought by* the issuer — are the issuer's own claims and are not adverse exposure; a `Nil` in a column or row scoped to a subset covers only that subset; an amount cell that cannot be read blocks the favourable conclusion without creating an adverse one.

## 3. Measured current behaviour

| Case | Today |
|---|---|
| ICDR table, `Against our Company \| Nil \| 4 \| Nil \| Nil \| Nil \| 120.00` (tax-only adverse count) | no bucket ⇒ UNKNOWN; the count is *not* read as clean, *not* read as criminal |
| ICDR table, all columns nil including tax | `clean` (correct: nothing of any kind is disclosed) |
| ICDR table, `Statutory or Regulatory Proceedings = 1` | `criminal_or_regulatory` — the bucket's own name covers it, so no new category was needed (this corrects A23's earlier §6.4 wording) |
| prose nil naming only tax | no bucket ⇒ UNKNOWN |
| prose nil naming criminal **and** civil **and** tax | `clean` — tax coverage is extra, not required |
| labelled list "Tax proceedings pending against our Company: 2" | no bucket ⇒ UNKNOWN |
| issuer-initiated tax rows | never adverse |

## 4. Options and consequences

**Option A — retain the existing taxonomy; tax-only adverse exposure stays UNKNOWN.**
*Effect:* no code, schema, config, fixture or historical change; the criterion neither rewards nor punishes an exposure its own value set cannot express; the *financial* dimension is still governed where A20/K5 put it; the *track-record* dimension stays undisclosed, and `notes`/`missing_inputs` say so.
*Cost:* a filing whose only litigation is tax litigation cannot be scored on this criterion at all, and its Module D availability shrinks by 4 points; two filings in the repository (and any real SME filing of that shape) sit in that state.

**Option B — map tax into an existing bucket.** Two variants, both rejected on the evidence:
* `criminal_or_regulatory`: the bucket name is the only available text, and reading tax into it asserts that a tax dispute is equivalent to a criminal prosecution or a regulatory disciplinary action for *track-record* purposes. It would also double-count: the same disclosed demand is already in the K5 numerator via A20, so one disclosure would pay 0/4 on D and >50% on K5. And `minor_civil` is not a refuge either — a tax assessment is not civil litigation "material" in the sense the map uses.
* `clean`: re-creates the exact defect class D-5 and A23 removed (an unevidenced favourable conclusion), and would let a filing with four unresolved tax demands score the maximum on promoter track record.

**Option C — introduce a dedicated bucket** (e.g. `tax_statutory_only` at 2 points, or a fourth value with its own weight).
Complete impact, enumerated rather than estimated:
1. `schema/ipo-input.v1.5.schema.json` — a new enum member (and any v1.6 schema counterpart).
2. `config_validation.py:53` — the pinned three-name domain must change; `check-config` reconciles every profile to 100 points, so the *points* assignment is itself a config decision.
3. `config/ipo-config.v1.5.0.json` **and** `v1.6.0.json` — the criterion map; changing `config` invalidates every stored `config_hash`-bearing result by design (RUNBOOK §7.1), so this is a *version* decision, not an edit.
4. `derived.py` — the formula string, which is the only place the bucket population is stated.
5. `builder.py` aliases — accept/reject synonyms, without reviving "anything not criminal is clean".
6. `sections.py` — table `tax` column, labelled-list and prose routes; A23 §6A.1's dimension rule and A24 R1 must be restated to include or exclude tax explicitly.
7. Overlays — none currently reference `litigation` (checked), so no profile needs a new reconciliation; still must be re-validated for all 10 profiles.
8. Consumers — `presentation/service.py`+`models.py` (state handling), `presentation/api.py`, `frontend/app.js` metric/state rendering and the GOVERNANCE field filter at `:1073`, `excel.py`; each must render the new bucket without implying favourability.
9. Tests — `tests/test_litigation_regulatory_defaults.py`, `test_extraction_phase5b.py`, `test_hd_fire_*`, `test_rk_fashion_reconciliation.py`, `test_v16_implementation.py`, plus a new case per route.
10. Fixtures/golden — `fixtures/vishal_nirmiti/input.json` (`criminal_or_regulatory`) and the Jio fixture are adverse and would be unaffected, **but any config-version change invalidates the golden `result_hash` `e84f8bc0f9b9…5619e1`**, which is a governed re-baseline decision (already identified in the tracker's integrity findings), not a test edit.
11. History — existing evaluation records would carry a bucket value that a newer config rejects on replay; the replay/verification path must state whether old records remain valid as history (RUNBOOK §7.1's answer: yes as history, no as re-playable under the new config).

## 5. Recommendation

**Adopt Option A for now: retain the existing taxonomy and leave tax-only adverse exposure UNKNOWN, with the gap recorded — and take no mapping decision in code.** Reasons, in order of weight:

1. No existing bucket's governed meaning supports tax. `criminal_or_regulatory`'s text is the only definition available and it does not say tax; `clean` would be indefensible.
2. The magnitude is not lost. A20 (approved) puts disclosed contingent liabilities — including disputed tax in that note — into K5, so the engine already prices the *financial* exposure; what the litigation criterion cannot say is whether it says something about the promoter's track record.
3. Option C's cost is not "a new enum value" but a config **version** change with hash invalidation across stored results and a golden re-baseline — a decision of a different class than this pass may take.
4. There is an unresolved textual question that must be answered *before* any bucket decision: the upstream reference config assigned "disputed tax" to the **auditor** bucket (`eom_only`), and the shipped v1.5 `auditor_bucket` formula no longer mentions tax. Either the clause was deliberately dropped (then tax has no scoring home except K5, and A26's Option A is right by design) or it was lost in translation (then the fix belongs to the **auditor** criterion, not to `litigation_bucket`). RAMKI should say which; Arena will not infer it.

**Do not** implement a fourth bucket, a mapping, or a fixture re-pin in this pass; if Option C is chosen, it needs its own record covering items 1–11 of §4 and a config-version decision.

## 6. Acceptance criteria if any option is approved

* **Retain (A):** the measured table/prose/labelled cases in §3 become pinned tests (tax-only count ⇒ no bucket; tax-only nil ⇒ no bucket; tax+criminal+civil nil ⇒ `clean`; issuer-initiated tax never adverse; `Nil` in a subset-scoped column clears nothing), plus one case pinning that a tax count is *not* silently converted into `minor_civil`.
* **If B were ever approved:** a test that the same disclosed tax demand does not double-count — D's 0/4 and K5's numerator must be asserted together — and a re-measured impact table for every committed filing, with `check-config` still valid.
* **If C were ever approved:** schema + `config_validation` + both config versions + `derived` formula updated in one commit; all 10 profiles reconciling to 100 points; every consumer rendering the new value without favourable wording; golden re-baseline recorded as an explicit decision with the old hash preserved in history; no historical evaluation re-run or re-hashed.

## 7. Affected components and downstream consumers

See §4 C-items 1–11 (the union of A and C's surfaces). For Option A the change set is **tests and documentation only** — `tests/test_litigation_regulatory_defaults.py` gains the pins listed in §6, and `docs/TRACEABILITY_MATRIX.md`'s §4.3 row gains a note that "tax proceedings" has no consuming metric.

## 8. Dependencies

A24 (whether tax coverage is part of the population a nil must reach — recommended *not* required), A20/K5 (approved; the reason magnitude is not lost), and Ramki's answer to the auditor-bucket textual question in §5.4. No A8 dependency: this is a taxonomy decision, not a source-coverage one.

## 9. Questions for RAMKI

1. Do you confirm Option A — tax-only adverse exposure stays `UNKNOWN` in `litigation_bucket` and its magnitude remains governed through the A20/K5 contingent-liability route?
2. Is "disputed tax" intended to be absent from `auditor_bucket` in v1.5 (the reference v1.4 text included it in `eom_only`), or is that an omission to repair — and if a repair, in which criterion?
3. If you want tax-only exposure scored at all, do you authorise opening a config **version** (Option C) with the full impact list in §4, including the golden-hash re-baseline decision, or prefer a documented, permanent non-score?
4. Should `docs/TRACEABILITY_MATRIX.md` record "v1.5 §4.3 tax proceedings: input acknowledged, no consuming metric" as a known coverage gap until 1–3 are answered?

## 10. Interim behaviour

Exactly what §3 measured, unchanged by this record: tax-only adverse disclosure produces no bucket ⇒ `STATE_UNKNOWN` ⇒ 4 points unavailable (not zero), reason recorded; tax never contributes to `clean`, and issuer-initiated tax claims are not adverse.
