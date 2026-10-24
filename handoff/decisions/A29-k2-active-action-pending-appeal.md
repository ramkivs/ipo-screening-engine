# A29 — K2 `sebi_ed_action_active`: a Pending Appeal Is an Active Action

- **Decision ID:** A29 (authorisation of interpretation **K2-A** from `docs/investigation/JIO-K1-K2-K5-DISPOSITION-2026-10-23.md` §2.5)
- **Title:** the status meaning of "active" for `governance.sebi_ed_action_active`
- **Record type:** **RAMKI-APPROVED CLARIFICATION plus implementation authorization.** Per `handoff/decisions/CONVENTION.md` rule 4 this record distinguishes the approved text (below) from Arena's evidence analysis and from the residual risks, which are recorded rather than decided.
- **Decision status:** **APPROVED (K2-A) and IMPLEMENTED 2026-10-23.** Party scope and the `false` path are **not** reopened by this record.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-23 (Asia/Calcutta); no decision time is asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/07f3439f-ipo-screening-engine` at confirmed remote tip `dab1aacaa57340cef26ce2ae280db347ae4a671b` (the K1/K2/K5 disposition commit); `main` untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`.
- **Scope:** the meaning of the *status* of a disclosed regulatory action, and the deterministic extraction path that must establish it (`engine/ipo_screening/extraction/sections.py::_sebi_ed_action_finding` and the regexes it consumes). Criterion K2, field `governance.sebi_ed_action_active`.
- **Out of scope and unchanged:** `config/ipo-config.v1.5.0.json` and `v1.6.0`, `schema/`, `derived.py`, `knockouts.py`, `scoring.py`, `confidence.py`, A9 / GMP qualification and Final-withholding, K1, K3, K4, K5, the party population (A24), the `false` rule (A25), all fixtures, the golden record and every historical evaluation.

## 1. Approved decision text

> A regulator's pending appeal qualifies as an active action at the evaluation cutoff, subject to the existing party-scope rules and evidence requirements.
>
> — RAMKI, 2026-10-23 (authorising **K2-A**)

## 2. The rule, stated precisely

1. **Status is part of the finding.** A disclosed SEBI or Enforcement Directorate action is `active` when the filing states that the proceeding is **pending** at the point the filing speaks for — including where the regulator itself is the appellant or revisionist against an order that went against it below.
2. **Concluded actions are not excluded.** A penalty imposed and finally disposed of remains a disclosed action and still yields `true` under the pre-existing rule (a regulator named as the actor, a finite act, a party, no negation, not boilerplate). A29 changes only what used to be *unreachable*: the "regulator files an appeal" construction. It does not narrow the class of qualifying actions, and it does not re-open anything already concluded.
3. **The distinction is recorded, not inferred.** The evidence record states the status the quotation itself expresses — `pending`, `concluded` or `unspecified` — so that "active" is never manufactured from a past-tense verb on the one hand, nor silently equated with "still uncertain" on the other.
4. **Party scope is unchanged.** The party must still be the Company, a Promoter, a Director, a Subsidiary, KMP or Senior Management (A23, A24-D1). A29 adds no party; it adds a *source* for a party statement already inside that population (§5, P3).
5. **The negative side is unchanged.** `false` still requires an explicit denial naming **both** SEBI and the Enforcement Directorate over a genuinely searched, fully readable range (A23 §6A.2, A25-D1/D2). A pending appeal found on one page does not authorise a denial anywhere, and a missing action is still UNKNOWN rather than `false`.

## 3. What was already authoritative, and what this record adds

| Question | Already settled | By |
|---|---|---|
| Which parties count | Company / Promoters / Directors; KMP and Senior Management **not** adopted as a widening | A23; A24-D1 (approved 2026-10-20, `41f2f86`) |
| What a `false` means | "no SEBI/ED action is disclosed on the searched pages", never verified absence | A25-D1 (approved) |
| When `false` may be emitted | both regulators named, present-tense scope, located range, every page read | A23 §6A.2; A25-D2 |
| A positive requires | regulator + finite act + party, boilerplate and negation excluded | A23 (as implemented in `sections.py`) |
| A tiered "clean" bucket for litigation | party coverage over the criterion's own three-party formula | A24-D3 |
| **What "active" means for a pending appeal** | **not previously stated anywhere** | **A29 — this record** |

A29 is therefore a **clarification of one undefined term**, not a new standard. It is also not a re-litigation of K2-B (below), which it explicitly does not adopt.

## 4. Evidence: what the retained filing says, and what it does not

Retained source: `evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`, 591 pages, sha256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d` (the same bytes registered as `RHP-FILING-72480c2e` in the retained evaluation's source manifest). Section VI, "Outstanding Litigation and Other Material Developments", pp. 463–478 — located through the filing's table of contents, every page in the window `READ`.

**p468, §III "Outstanding litigation involving the Directors", under Mr. Mukesh Dhirubhai Ambani** — the sentence the corrected engine now emits as the finding:

> "Against the said order of the Special Court, SEBI filed a revision application before the Hon'ble High Court of Bombay and the same is currently pending."

Its antecedent, same page: SEBI's complaint of **16 July 2020** before the Special Court, Mumbai against Mr. Ambani "in his capacity as a director of RIL" and "being part of the promoter and promoter group of RIL"; the Special Court dismissed it as barred by limitation by order dated **30 September 2020**.

**p470, §IV "Outstanding litigation involving RIL, the Promoter", item (iii)** — the same matter stated for the Promoter:

> "In this matter, SEBI had filed a complaint on July 16, 2020, inter alia against RIL before the Special Court, Mumbai … The Special Court, Mumbai, vide order dated September 30, 2020, dismissed SEBI's complaint as barred by limitation. Against the said order of the Special Court, **SEBI has filed a revision application before the Hon'ble High Court of Bombay and the same is currently pending**."

**Evidence identifiers.** Field path `governance.sebi_ed_action_active`; the record minted by `extract_governance` carries `EV-governance-sebi_ed_action_active`, `source_id` `RHP-FILING-72480c2e`, page 468, section "Outstanding Litigation", locator "Disciplinary actions by SEBI or Stock Exchanges", `extraction_method` `DETERMINISTIC_PDF`. The retained evaluation `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601` carries `sebi_ed_action_active = null` and **no** evidence entry for this field: that record predates the correction and is not edited by it.

**Filing-reported versus independently verified.** The filing reports the pendency; **no regulator or court record was consulted**. Direct retrieval of SEBI and Bombay High Court material from this sandbox is blocked by egress (recorded as finding C4 in `docs/investigation/JIO-VALIDATION-AND-EVIDENCE-STATUS-2026-10-23.md`), so the claim in this record is exactly what the filing states as at its date, plus the separately verifiable fact of the 2026-10-21/23 offer (BSE listing row and issuer issue page, publication check only). No independent confirmation of the revision application's current status exists in this repository and none is claimed.

## 5. Implementation (2026-10-23)

Five defects were confirmed against the current implementation before any edit; each is fixed at its own point, and every one of the five errs **fail-closed** except where noted.

| ID | Confirmed defect | Correction | Separability |
|---|---|---|---|
| **P1** | the 600-character quotability cap was applied to a **line span**, so a normal filing paragraph of 715–1,804 characters was discarded before any test ran (12 of 12 SEBI/ED candidates in the Jio window) | `_lit_sentence_bounds` narrows the span to the sentence containing the match; the cap now measures a sentence. A match may not cross a masked region (`_LIT_MASKED_REGION`) | independent |
| **P2** | `_REG_ACTION` excludes `\n`, so a hard PDF wrap split a sentence and it matched nothing (`SEBI \nfiled`) | `_lit_match_text` replaces a **single** newline with a space at identical offsets (paragraph breaks, i.e. `\n\n`, are preserved), so quotations stay verbatim slices | independent |
| **P3** | the party literal does not know the filing's own defined short names (`RIL`), so a sentence naming only the short name had no party | **heading attribution, kept separable** (see §6) | **separate commit-able unit** |
| **P4** | `_REG_BOILERPLATE` vetoed any sentence citing a regulation number, including a genuine dated order ("…PFUTP Regulations, 2003") | citation forms moved to `_REG_BOILERPLATE_CITE` and vetoed only when the sentence reports no adjudicative event (`_REG_ADJUDICATIVE_EVENT`: a dated order/notice/complaint, or a named forum) | independent |
| **P5** | the regulator-first alternation lacked `filed` / `preferred` / `moved` / `referred`, and the action-noun list lacked the thing a regulator files (`revision application`, `appeal`, `petition`, `complaint`) | added; the action noun is still required, so a bare filing reference is not an action | independent |

One further defect surfaced **during** the implementation and was corrected rather than published: narrowing a span to a sentence made the *section preamble* on p463 ("this section also provides the details of all disciplinary actions … including outstanding actions") quotable for the first time, and it was emitted as a finding. `_REG_META_DISCOURSE` now rejects a statement **about** the disclosure; the section preamble describes the document, not an event.

**Not changed:** the boolean contract (a 4th tuple element carries status/attribution metadata), the negation test, the both-regulator requirement for `false`, the closed-period suppression (`_REG_ABSENT_CLOSED`), the structured table and labelled-list routes, `derived.py`, `knockouts.py`, config, schema and scoring. The five failure modes are documented with page-level reproduction in `docs/investigation/jio-k125-20261023/k2-extraction-reproduction.json`.

## 6. P3 — heading-attributed party, and why it is separable

A filing states party scope in a **section-level heading** ("IV. Outstanding litigation involving RIL, the Promoter") and then names the party by a short name the party literal cannot know. P3 reads those headings from the original page text (the prose routes mask them) and attributes the party to a sentence that names none, under four constraints:

1. only a heading of the form `I.` … `XVIII.` + title — never a lettered sub-heading such as "c) Actions by statutory/ regulatory authorities against RIL", which scopes one item;
2. the heading must name **exactly one** A24 group; a heading naming several ("Outstanding tax claims involving the Company, Promoter, Subsidiaries and Directors") attributes nothing;
3. attribution applies only when the quoted sentence itself names **no** party group, so a sentence's own party always wins;
4. the heading must precede the sentence in document order — a heading below the sentence, or on a later page, attributes nothing; and a heading that names no single group **clears** the earlier attribution rather than inheriting it.

The attribution is exported in the evidence note ("party attributed under A29 (P3) from the section heading "…" -> Directors"), so it can be audited without reading the code, and the `quote` remains the sentence — a verbatim slice of the page.

**Separability is mechanical, not merely structural.** The behaviour sits behind one class flag, `SectionExtractor._LIT_HEADING_PARTY_ATTRIBUTION = True`. Setting it to `False` restores the pre-A29 party test exactly — a sentence that names no party emits nothing and K2 returns to UNKNOWN — with no other behaviour touched. Verified on the retained filing (probe: flag on ⇒ `true`; flag off ⇒ no field) and on the synthetic cases. The P3 tests are the cases to re-baseline if the flag is ever turned off.

**Reverting P3 alone is safe and is the intended containment:** without it, sentences that name only a short name have no party, emit nothing, and K2 returns to UNKNOWN. P3 can add a party to a finding; it can never turn a denial into an action, never clear a flag, and never create a `false`.

## 7. Cutoff semantics

The evaluation cutoff is the evaluation's own `evaluation_timestamp`, passed to `evaluate(..., evaluation_datetime=…)`; A9's GMP freshness uses the same value. **A29 adds no cutoff input and no clock.**

* The finding is dated by the filing: what the quotation says about the proceeding, as at the RHP date. The evidence note records the **status stated in the quotation**, not a status observed today.
* A29 does **not** substitute the present date, does not assume an action remains pending indefinitely, and does not infer today's status from a filing statement.
* For a *positive* this is sound: a proceeding the filing calls pending was pending when the filing spoke, and the filing is what the engine evaluates. For a *negative* the existing closed-period rule still applies — a denial scoped to a period that has closed cannot speak for the present (A23 §6A.2), and A29 does not relax it.
* Any statement about the position **after** the filing date would require a separately sourced observation, which the engine does not have and this record does not authorise it to invent.

## 8. Consequences

**When K2 becomes `true`.** When the searched litigation range contains a sentence in which SEBI or the ED is the actor of a finite act against a party in scope, with no negation before the act, no disqualifying boilerplate, and no meta-discourse — including an action the regulator has taken by way of appeal. Concretely for Jio: the p468 sentence, with party attributed from the §III heading ("Directors") and status `pending`.

**What evidence is necessary.** (a) the regulator named as actor; (b) a finite act; (c) the party, either in the sentence or from a single-group section heading that precedes it; (d) the status the sentence states. Missing (c) with no usable heading leaves the flag absent, i.e. UNKNOWN. Nothing about the amount, the merits or the outcome is required, and no inference from the filing's silence is permitted.

**How the knockout responds.** K2 is `required: [promoter_pledge_pct, sebi_ed_action_active]`; `true` triggers the knockout, `knockouts.py` returns `TRIGGERED`, and the verdict precedence in A7 (`config.verdict.knockout_verdict = "AVOID"`) makes the final outcome `AVOID` regardless of score. `false` clears K2 as absence-of-disclosure (A25-D1); absent leaves K2 `UNVERIFIED` and the verdict `INSUFFICIENT_DATA` through `critical_data`. **No such evaluation was created in this pass** — §11.

**What did not change for Jio.** The retained evaluation `…29d9a601` (34.0, interval 24–77, `INSUFFICIENT_DATA`, A9 nonterminal) is untouched. Its verdict reflects the pre-correction input; a future evaluation would reflect the corrected extraction, and that would be a new record, not an edit.

## 9. Non-goals

No change to A9 / GMP qualification or Final-withholding; none to K1, K3, K4 or K5; none to scoring weights, criterion semantics, thresholds, gate transitions or confidence rules; none to the A24 party population or the A25 `false` rule; none to the schema, config, fixtures, golden record or any historical evaluation. **K2-B is not adopted** (a penalty still in force alone does not establish "active"), and **K2-C is not adopted** (an issuer-only reading of the flag contradicts A23's party test and A24). Those remain open policy questions for Ramki; this record settles only K2-A.

## 10. Tests added — NOT RUN

Focused tests were added in `tests/test_litigation_regulatory_defaults.py` (P1, P2, P4, P5 and the pending/concluded distinction) and in the new P3 block (heading attribution, and the four negative guards: ambiguous heading, heading below the sentence, heading on a later page, lettered sub-heading, and an unrelated SEBI reference). One existing expectation was updated because the K5 citation deliberately changed shape (`tests/test_contingent_liabilities_extraction.py`, label-only quote ⇒ label + selected cell).

**Execution status: NOT RUN — deferred to a separate regression pass.** The full backend suite takes roughly three hours and was excluded by explicit instruction for this pass. What was done instead is recorded in §11 and is not a substitute for the regression run.

## 11. Verification actually performed (and what it is not)

* the extractor was applied **read-only** to the retained Jio PDF: the finding is `true`, page 468, status `pending`, party attributed from the §III heading, quotation verified verbatim against the page;
* the extractor was applied **read-only** to the seven fixture filings under `fixtures/filings/`: `governance.sebi_ed_action_active` remains absent for all seven, so no fixture's K2 changes;
* twelve synthetic scenarios (the pending appeal, the hard wrap, the long paragraph, the dated order citing a regulation, a citation without an event, and the five P3 negative guards) were probed to confirm the intended branch behaviour;
* `_extract_contingent_liabilities` was applied to the retained Jio note: page 405, 15,021, `unquantified = None` and the extended citation, unchanged values.

These are extraction probes on real and synthetic text. **No pytest, no ingestion and no evaluation were run.**

## 12. Unresolved dependencies

1. **External corroboration of the appeal's status** — blocked by sandbox egress; the finding rests on the filing.
2. **K2-B / K2-C** — the remaining status interpretations, undecided, not implemented.
3. **A8-R** — the regulator-source coverage standard for a verified absence; still open.
4. **K1 / K5** — unchanged by this record; both remain governed UNKNOWNs.

## 13. Implementation authority

**GRANTED** by Ramki's K2-A authorisation of 2026-10-23, limited to: the status interpretation above, the five extraction corrections, the P3 heading attribution as a separable unit, the evidence-note status/attribution wording, and focused tests. **Not granted:** anything in §9, any widening of the party population, any new negative rule, and any evaluation run.
