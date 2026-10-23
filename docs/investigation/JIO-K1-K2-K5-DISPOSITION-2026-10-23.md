# Jio Platforms — K1, K2 and K5: evidence, mechanics and governance dispositions

**Date:** 2026-10-23 · **Branch:** `arena/07f3439f-ipo-screening-engine` · **Tip at start of pass:** `d894ba5`
**Reference evaluation:** `JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601` (34.0 / 100, interval 24–77, `INSUFFICIENT_DATA`, A9 `NONTERMINAL_UNRESOLVED`)
**Retained source:** `evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`, sha256 `72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d`, 591 pages

This pass was **evidence and governance only**. No regression test was run, no ingestion was performed, no evaluation was created, and no application, test, schema, config or frontend file was modified. The engine's own extractor and regexes were applied read-only to the retained PDF, in a probe script, to establish where evidence stops travelling.

---

## 0. Bottom line

| Criterion | State | Why |
|---|---|---|
| **K1** `going_concern_uncertainty` | UNKNOWN (governed) | The filing contains **no** going-concern statement of either polarity. A19 (approved) forbids deriving a negative from silence, from an unmodified opinion, or from a negated statement. No evidence was lost — the pages were read. |
| **K2** `sebi_ed_action_active` | UNKNOWN (fail-closed, but **evidence was lost**) | The filing discloses a **pending SEBI proceeding against the Promoter and a Director** plus concluded SEBI penalties against the Promoter, inside a TOC-located, fully-readable litigation window. The extractor discards all of it: **all twelve** SEBI/ED-actor spans in the window exceed its 600-character cap, and four further mechanical filters would each have blocked the survivors. This is the only one of the three where the record understates the filing. |
| **K5** `contingent_liab_unquantified` | UNKNOWN (governed) | Note 37 is fully quantified (15,021 INR million at 31 March 2026), the ratio reproduces exactly at 0.4470843085 %, and the flag is absent only because A20 rule 8 permits a `True` from a positive in-section statement and nothing else. No parsing or arithmetic error exists. |

Two findings are new relative to the 2026-10-23 validation report: **note 47.4 on p430** (a scoped five-period negative for audit qualifications, other legal/regulatory matters and Emphasis of Matter) and the **complete mechanical explanation of the K2 null** (§2.4).

---

## 1. Governing rules actually in force

Nothing here was assumed from the config alone. All three criteria are also governed by approved decisions that are **not present in this branch's `handoff/decisions/`** — they exist at commit `ebb8a6c6b0d12e54228ec6b523bda025e927fb0b` and are cited by the tracker and by code comments.

| Criterion | Config (v1.5.0, unchanged) | Approved decision | Code path |
|---|---|---|---|
| K1 | `required: [auditor_opinion, going_concern_uncertainty, net_worth_latest]`; `when.any` includes `{"flag": "going_concern_uncertainty"}` | **A19** (D-1, RAMKI-APPROVED 2026-10-20): positive evidence only; absent paragraph, negated language and an unmodified opinion never set the field; **negative-confirmation rule deferred** with four prerequisites | `sections.py::_going_concern_uncertainty_match` → `builder._pick_gov(…, None)` → `derived._going_concern_uncertainty` (pass-through) |
| K2 | `required: [promoter_pledge_pct, sebi_ed_action_active]`; `when.any` includes `{"flag": "sebi_ed_action_active"}`; the flag is also in `critical_data` | **A23** rule 6 (True: SEBI/ED as actor + finite act + party, boilerplate excluded) and rule 8 (False: both regulators named, present scope); **A24** (approved, D1–D3): population = company, promoters, directors, KMP/SM not adopted; **A25** (D1/D2 approved): a False is "no action disclosed on the pages searched", never verified absence | `sections.py::_sebi_ed_action_finding` → `builder` → `derived._sebi_ed_action_active` → `knockouts` |
| K5 | `required: [contingent_liab_pct_networth, contingent_liab_unquantified]`; `when.any(ratio > 50, flag)`; formula `contingent liabilities / net worth × 100` | **A20** (D-2, RAMKI-APPROVED 2026-10-20): latest fiscal-year column; commitments excluded; **rule 8: the unquantified flag is `True` only on a positive in-section statement, never coerced to `False`** | `financial_tables.py::_extract_contingent_liabilities` → `derived._contingent_liab_unquantified` |

Knockout semantics are Kleene three-valued (`knockouts.py`): `any(FALSE, UNKNOWN)` is UNKNOWN, and a decisive TRUE wins. A verified TRIGGERED knockout yields final outcome `AVOID` (`config.verdict.knockout_verdict`, A7).

---

## 2. K2 — `sebi_ed_action_active`

### 2.1 What the filing actually says

The whole of SECTION VI is framed as live: p463 opens *"Except as disclosed in this section there are no outstanding litigation as of the date of this RHP, pertaining to … (ii) actions taken by statutory and/ or regulatory authorities against the Relevant Parties"*, and adds that the section discloses *"all disciplinary actions initiated or taken and penalties imposed by SEBI or the Stock Exchanges against the Promoter in the last five financial years including outstanding actions"*.

Inside that frame:

| Page | Party | What is disclosed | Status at RHP date |
|---|---|---|---|
| **468** | **Director** — Mr. Mukesh Dhirubhai Ambani, in his capacity as a director of RIL and as part of the promoter/promoter group | "SEBI had filed a complaint on July 16, 2020 … for taking cognizance of alleged offences under Regulations 3, 5 and 6 of [PFUTP], 1995 … The Special Court, Mumbai, vide order dated September 30, 2020, **dismissed SEBI's complaint as barred by limitation**. Against the said order of the Special Court, **SEBI filed a revision application before the Hon'ble High Court of Bombay and the same is currently pending**." | **pending** |
| **470** | **Promoter** — RIL | The same matter, with the same outcome and the same pending revision application (*"SEBI has filed a revision application … currently pending"*), under the heading *"c) Actions by statutory/ regulatory authorities against RIL"*. | **pending** |
| 470–471 | Promoter — RIL | 2010 show-cause notice → 24 March 2017 order (fraud finding, ₹4,473 million disgorgement, one-year F&O prohibition) → SAT 5 November 2020 → Supreme Court **29 May 2026**: *"fraud" under the PFUTP Regulations is not made out against RIL*; RIL *"has only violated the disclosure requirements under 2001 SEBI Circular … and is liable to be penalized …, and concurred with the observations of the SAT as regards the penalty levied on RIL"*. | **concluded** |
| 472–473 | Promoter — RIL | 22 December 2021 show-cause notice → 20 June 2022 order imposing **₹3 million** → SAT dismissed RIL's appeal 2 May 2025 → **Supreme Court dismissed RIL's appeal 2 December 2025**. Separately: 8 August 2014 order (₹130 million) → set aside and remanded → fresh notice 5 April 2016 → **AO disposed of the notice without penalty on 20 September 2021**. | **concluded** |

Counter-statements, in full, are weaker than they look:

- p486: *"The Company, the Promoter, members of the Promoter Group, the Directors, and the persons in control of the Promoter confirm that **they are not debarred** from accessing the capital market …"* — **debarment only**; says nothing about pending proceedings.
- p487: the Regulation 5/7 eligibility conditions, including *(c) neither the Company nor any of the Directors or Promoter are a Wilful Defaulter or a Fraudulent Borrower* — again not an action denial.
- p464 *"c) Actions by statutory and regulatory authorities against the Company — Nil"*; p469 *"c) Actions by statutory/ regulatory authorities against the Directors — Nil"*; p473 KMP/Senior Management *Nil*. These are **subset nils** in the filing's own categories, name no regulator and never the Enforcement Directorate, so under A23 rule 8 and A25 C3–C4 they clear nothing. The Directors' Nil also coexists with the SEBI criminal complaint against a Director disclosed on the previous page under a different heading — a filing-side classification the engine must not flatten.
- **"Enforcement Directorate", "PMLA", "ED" — 0 occurrences in 591 pages.** So neither a positive nor a both-regulator negative is available from the ED side; no ED claim is made in either direction.

### 2.2 Why the engine emits nothing — measured, not assumed

`_sebi_ed_action_finding()` returns `None` on the located window (pp. 463–478, every page `READ`). Every SEBI/ED-actor span it considers was captured and tested:

| Page | Span length | > 600 cap | Boilerplate veto | Party token | Negated |
|---|---|---|---|---|---|
| 463 (section opener, ×3) | 1154 | **yes** | no | yes | no |
| 470 (RIL debentures + pending revision) | 801 | **yes** | no | **no** | no |
| 470 (2010 notice → 2017 order) | 1804 | **yes** | **yes** | yes | no |
| 470 (adjudicating officer, 2021 order) | 770 | **yes** | no | **no** | no |
| 472 (disciplinary-actions intro) | 1212 | **yes** | **yes** | no | no |
| 472 (2021 notice / ₹3 million) ×2 | 1115 | **yes** | **yes** | no | no |
| 472 (2014 order) ×3 | 715 | **yes** | no | no | no |

**Twelve of twelve are over the cap; none reaches the party test.** The cap is applied to a *line span* — text joined until a line happens to end with a period — not to a sentence, and this filing's paragraphs run 715–1804 characters.

Five distinct mechanisms are involved, each reproduced individually:

| ID | Mechanism | Reproduction | Effect here |
|---|---|---|---|
| **E1** | 600-character span cap | p470 span = 801 characters → skipped | removes **all 12** candidates |
| **E2** | `_REG_ACTION` uses `[^.\n]`, so a hard line wrap breaks the match | p468: `SEBI \nfiled a revision application` → `search` False; after joining the wrap → True | the Director-scoped pending-revision sentence is never a candidate at all |
| **E3** | `_LIT_PARTY` does not know the filing's own defined short name (`RIL`), and is applied to the matched span only | `…against RIL` → False; `…against RIL, the Promoter` → True | p470/p472 sentences name only "RIL" |
| **E4** | `_REG_BOILERPLATE` matches any sentence citing a regulation number | the 24 March 2017 SEBI order sentence contains "…Regulations, 2003" → vetoed | removes a genuine action sentence that would otherwise pass |
| **E5** | the regulator-first alternation omits `filed` | "SEBI filed a revision application" does not match that branch (the noun-first branch rescues it only when "order … filed" happens to sit on one line) | a regulator that files or appeals is not recognised in that word order |

Every mechanism errs in the **fail-closed** direction: none can produce a false `True`, and the negation and boilerplate guards are not bypassed by any of them. The reproduction is saved with page-level detail in `jio-k125-20261023/k2-extraction-reproduction.json`.

### 2.3 Sentence-level counterfactual (simulation only — nothing was changed)

Applying the engine's own regexes to sentence-sized text, with no code change:

| Page | Sentence | Act | Party | Boilerplate | Length | Remaining blocker |
|---|---|---|---|---|---|---|
| 468 | "Against the said order of the Special Court, SEBI filed a revision application … and the same is currently pending." | ✓ | ✗ | ✓ | 153 | E2 (match), E3 (party) |
| 470 | "… SEBI has filed a revision application before the Hon'ble High Court of Bombay and the same is currently pending." | ✓ | ✓ (via "the Promoter" in the same span) | ✓ | ~154 as a sentence (879 as spanned) | E1 only |
| 472 | "The Adjudicating Officer of … SEBI passed an order on June 20, 2022, imposing a penalty of ₹3 million." | ✓ | ✗ | ✓ | 135 | E3 (party) |

So a single structural change (match sentences, not line spans) would surface the p470 pending proceeding; the party vocabulary and the boilerplate rule are separately needed for the rest.

### 2.4 Is UNKNOWN justified?

**As the output of the current rule: yes** — the field is evidence-or-absent, nothing was fabricated, and K2 correctly stays UNVERIFIED rather than CLEAR.
**As a description of the filing: no** — the filing discloses a pending SEBI proceeding against the Promoter and a Director, and two concluded SEBI penalties against the Promoter, in a section the filing itself labels outstanding.

### 2.5 Governance question (genuinely open)

Party scope for adverse evidence is **already settled** (A23 rule 6, A24 population), and the `False` path is settled (A23 rule 8, A25 D1/D2). What no decision defines is the **status meaning of "active"** for a positive finding:

| Option | Rule | Consequence for this filing |
|---|---|---|
| **K2-A** | Active = a proceeding pending at the evaluation cutoff. A regulator's own appeal/revision against a dismissal counts; concluded penalties do not. | `True` on p468/p470 → K2 **TRIGGERED** → final outcome **AVOID** (A7, `knockout_verdict`). Score, other criteria and the A9 nonterminal state unchanged. |
| **K2-B** | Active = any SEBI/ED action with a live adverse consequence: pending proceeding **or** a penalty still in force. | `True` on the ₹250 million / ₹3 million penalties that survived appeal → **AVOID**. |
| **K2-C** | Active = an enforcement action against the issuer itself only; promoter/director matters feed `litigation_bucket` but never this flag. | Flag stays absent (the Company's own `Nil` at p464) → K2 UNVERIFIED → `INSUFFICIENT_DATA`. This is what A23's *"Proceeding involving a Director, not the issuer"* row literally says, but it contradicts A23 rule 6's promoter-permitting party test and the K2 label's promoter framing; adopting it would require amending A23. |
| **K2-D** | Status quo: no policy statement; the flag appears only when the sentence happens to survive the extractor. | UNKNOWN persists for reasons invisible to a reader of the record. Not a durable answer. |

**Consequence to weigh before choosing:** under K2-A or K2-B the Jio verdict changes from `INSUFFICIENT_DATA` to `AVOID`. That is a material outcome change produced entirely by a governance choice plus an extraction fix, not by new facts about the issuer — which is exactly why it must be decided explicitly rather than by patching the extractor.

### 2.6 Smallest correction — documented, not implemented

| ID | Change | Fixes | Risk |
|---|---|---|---|
| **P1** | Apply the 600-character cap to a **sentence** inside the line span (split at sentence-final periods that are followed by a capital, a quote or a `(i)`-style marker). | E1 | low — the quote remains a verbatim slice |
| **P2** | Treat a hard line wrap as whitespace when matching (normalise for the match, map offsets back to the original text). | E2 | medium — must keep sentence-boundary discipline |
| **P3** | Party attribution: when the sentence names no party but the enclosing filing **heading** does (the filing's headings read "…against RIL, the Promoter"), attribute the heading's party and include the heading in the quote. A larger alternative — reading the filing's own Definitions section for short names — introduces an alias mechanism A23 does not authorise. | E3 | medium-high — mis-attribution would create the one thing A23 guards hardest: a false `True` |
| **P4** | Narrow `_REG_BOILERPLATE` so it vetoes sentences that name an agency but describe no act, not every sentence that cites a regulation number. | E4 | medium — needs negative cases for circulars and registration language |
| **P5** | Add `filed`, `preferred`, `moved`, `referred` to the regulator-first verb alternation. | E5 | low |

Required regression cases when this is implemented: newline-wrapped sentence found / same words across two sentences not found; a 900-character paragraph matched through its constituent sentence with that sentence as the quote; heading-supplied party attributions working and failing correctly; a regulation-citing circular still rejected; all existing both-regulator-denial, closed-period, subset-nil and negation pins unchanged; **no new `False`**.

---

## 3. K1 — `going_concern_uncertainty`

### 3.1 What the filing contains

| Page | Content | Bearing on K1 |
|---|---|---|
| 321–324 | The **Independent Auditor's Examination Report** on the Restated Consolidated Financial Information, jointly issued by Deloitte Haskins & Sells LLP and Chaturvedi & Shah LLP, dated **7 October 2026** (UDINs `26100459QBZXUZ8355`, `26122179ZKMPTF3256`). Complete text inspected: **no going-concern paragraph, no "material uncertainty", no Emphasis of Matter, no qualification, no adverse opinion, no disclaimer.** | No positive evidence. |
| 323 | *"Our opinion … is not modified in respect of above matters with respect to our reliance on work done and the reports of the other auditors…"* | An unmodified opinion is explicitly **not** evidence of the absence of going-concern uncertainty (A19). |
| **430** | Note 47.4 "Non-adjusting events": **(a)** *"There are no audit qualification in auditor's report for the financial period / year ended 30th June, 2026, 30th June, 2025, 31st March, 2026, 31st March, 2025 and 31st March, 2024 which require adjustments."* **(b)** *"There are no matters reported with respect to Other Legal and Regulatory Requirements in auditor's report for [the same five periods]."* **(c)** *"There are no Emphasis of matters in auditor's report for the period / year ended 30th June, 2026, 30th June, 2025, 31st March, 2026, 31st March, 2025 and 31st March, 2024."* | **New this pass.** A scoped, five-period negative about the auditor's reports — but silent on going concern, and located in the notes, not in the auditor's report. |
| 253 | The only occurrence of the phrase "going concern" in 591 pages: *"…on a going concern basis with effect from March 31, 2019…"* — the accounting basis of a 2019 Composite Scheme transfer. | Neither evidence of uncertainty nor of its absence. |
| 322 (para 5) | The examination report relies on auditor's reports dated 7 October 2026, 24 April 2026, 24 April 2025 and 22 April 2024 for the underlying consolidated financial statements. **Those reports are not reproduced in the filing.** | The documents that would carry an SA 570 material-uncertainty paragraph are referenced but absent. |

Phrase searches over all 591 pages: `material uncertainty` — 0; `significant doubt` — 0; `ability to continue as a going concern` — 0; `no material uncertainty` — 0. The engine's polarity guard was therefore never even reached.

### 3.2 Is the unknown technical or semantic?

**Semantic, with no technical loss.** The scan ran over the examination report (pp. 320–324), every page reported `READ` — no page failed, no candidate was dropped. The field is absent because the filing contains no qualifying statement, and A19 forbids manufacturing one.

### 3.3 Disposition and what would change it

UNKNOWN is **correct under A19** and K1 remains UNVERIFIED, with `critical_data` turning the missing flag into `INSUFFICIENT_DATA` rather than a favourable verdict. No new governance requirement is invented here: A19 already decided the question and **deferred** the negative rule behind four named prerequisites (coverage definition, required-language specification, false-negative measurement, re-score policy).

If that deferral is ever revisited, the question is now sharper than "silence": **would note 47.4 (a)+(b)+(c) — a five-period negative for qualifications, other legal/regulatory matters and Emphasis of Matter — together with the examination report's silence, count as a negative confirmation of going-concern uncertainty?** A19's text rules out "unmodified opinion alone"; it does not address this broader scoped negative. It should not be accepted automatically: an SA 570 material-uncertainty section is neither a qualification nor an Emphasis of Matter, so a "no qualification / no EOM" statement is logically silent on going concern.

**Minimum additional evidence:** the statutory auditor's report(s) on the consolidated financial statements for FY2026 (and the June 2026 interim statements), or an auditor confirmation scoped to going concern. Both are external documents, not inferable from what is retained.

---

## 4. K5 — `contingent_liab_unquantified`

### 4.1 The note, verbatim

p405, Note 37:

> **(I) Contingent Liabilities** — *Claims / disputed liabilities against the Group not acknowledged as debts\** — **14,688 / 14,151 / 15,021 / 30,183 / 27,924** (30 June 2026 · 30 June 2025 · **31 March 2026** · 31 March 2025 · 31 March 2024). *"The claims/disputed liabilities are not likely to have any material effect on financial position of the Group."* *"…The Group has been advised that the demand is likely to be either deleted or substantially reduced and accordingly no provision is considered necessary."*
> **(II) Commitments** — *Estimated amount of contracts remaining to be executed on Capital account not provided for* — 90,389 / 65,624 / **26,198** / 51,272 / 58,284.

p406: *"Total Equity (As per Restated Consolidated Statement of Assets and Liabilities) (B) — **3,359,769**"* at 31 March 2026.

### 4.2 Arithmetic verified (all three bases)

| Basis | Numerator | Denominator | Ratio | Matches the record? |
|---|---|---|---|---|
| **Engine** (FY2026 note total ÷ FY2026 total equity) | 15,021 | 3,359,769 | **0.4470843085 %** | **yes** — record value `0.4470843084747791` |
| ICDR Net Worth denominator (p487: equity share capital + other equity **excluding OCI**) | 15,021 | 3,340,134 | 0.4497124966 % | no record uses it; this is the separate C3 question |
| Interim column (30 June 2026 claims ÷ FY2026 equity) — **not permitted** by A20 rule 3 | 14,688 | 3,359,769 | 0.4371729128 % | no |

Threshold: `> 50 %`. The ratio is **~112× below** the threshold; firing would need contingent liabilities of ₹1,679,884.5 million. Even adding the A20-excluded commitments (26,198) would give 0.7798 % — still ~64× below. **No numerator, denominator, unit, period or rounding error exists**, and the FY2026 column is the correct one under A20 rule 3 (this note carries an interim 30 June 2026 column that the rule deliberately excludes, and the note has exactly one contingent row, so there is no aggregate-plus-constituents double count).

### 4.3 Why K5 is still UNKNOWN

K5 is `any(ratio > 50, flag)`. The ratio limb resolves **FALSE**, so the knockout is decided entirely by the second limb, whose canonical input `financials.contingent_liabilities_unquantified` is absent. That absence is **policy, not parsing**: A20 rule 8 sets the flag `True` only on a positive unquantified statement **inside the same section**, leaves negated language `None`, and never coerces to `False`. Note 37 contains no such statement; the only unquantifiability language in the filing is at p472 (a Promoter arbitration: *"any claim cannot be determined until quantification is done by the Tribunal in the final award"*), which sits outside the defined note and outside the issuer's own liability.

Search results across 591 pages: `unquantified` / `not quantifiable` / `cannot be quantified` / `unascertained` — 0 hits in note 37 (and only the p472 paraphrase elsewhere).

### 4.4 One provenance defect (no value error)

The emitted evidence for `financials.contingent_liabilities` quotes only the row label — *"Claims / disputed liabilities against the Group not acknowledged as debts\*"* — and **not the amount**. The value 15,021 is correct on p405, but a reader of the evidence panel cannot verify it from the citation. Smallest documented fix (not applied): extend the quote to the amount row (label plus the five cells, or at least the 31 March 2026 cell) when the value is taken from that row.

### 4.5 Governance

**No new decision is needed to keep K5 UNKNOWN** — A20 rule 8 settles it, and clearing the knockout on silence would require a new negative-confirmation rule. The only optional variant is a **scope extension**: should the unquantified limb look beyond the issuer's contingent-liability note to material unquantified exposures disclosed elsewhere? Recommendation: **no change** — adopting it would import promoter-level exposure (p472) into an issuer-level ratio and would need its own materiality and scope contract first.

**Separate dependency, not resolved here:** the denominator is the net-worth basis question (`jio-validation-20261023/c3-net-worth-basis.json`). No authoritative decision exists on this branch. Both bases give 0.4471 % / 0.4497 %, so K5's outcome does not depend on the choice; the dependency is recorded, not decided.

---

## 5. Provenance and association defects found

| # | Field | Path | Defect | Direction | Smallest fix |
|---|---|---|---|---|---|
| 1 | `governance.sebi_ed_action_active` | `sections.py::_sebi_ed_action_finding` | Line-span cap of 600 chars (E1) removes every SEBI/ED candidate in this filing | fail-closed (missed action) | P1 |
| 2 | same | `_REG_ACTION` `[^.\n]` | A PDF line wrap breaks the match (E2) | fail-closed | P2 |
| 3 | same | `_LIT_PARTY` | The filing's own defined short name ("RIL") is not a party token (E3) | fail-closed | P3 |
| 4 | same | `_REG_BOILERPLATE` | Vetoes genuine action sentences that cite a regulation (E4) | fail-closed | P4 |
| 5 | same | `_REG_ACTION` | Regulator-first verbs omit `filed` (E5) | fail-closed | P5 |
| 6 | `financials.contingent_liabilities` | `financial_tables.py` → evidence item | Quote carries the label, not the amount | display only | extend the quote |
| 7 | K1 | — | No defect: pages read, no candidate dropped | — | — |

**Records gap (not a defect in the engine):** `handoff/decisions/A19`, `A20`, `A23`, `A24`, `A25`, `A26`, `A27` are authoritative and are implemented in code, but **do not exist in this branch's `handoff/decisions/`** — they live at commit `ebb8a6c`. Anyone auditing this branch's behaviour from its own tree would find code comments citing decisions that are not there. Recorded, not fixed: copying decision records between branches is a records action, not an investigation edit.

---

## 6. Dispositions

| | **K1** `going_concern_uncertainty` | **K2** `sebi_ed_action_active` | **K5** `contingent_liab_unquantified` |
|---|---|---|---|
| **1. Current engine disposition** | UNKNOWN → K1 UNVERIFIED | UNKNOWN → K2 UNVERIFIED | UNKNOWN → K5 UNVERIFIED (ratio leaf FALSE at 0.4471 %) |
| **2. Governing rule and source** | config K1 + **A19** (approved, D-1) + `sections.py` matcher | config K2 + **A23** r6/r8, **A24** population, **A25** D1/D2 + `_sebi_ed_action_finding` | config K5 + **A20** r3/r6/r8 + `_extract_contingent_liabilities` |
| **3. Evidence found** | Examination report pp. 321–324 (no GC/EOM/qualification); note 47.4 on p430 (five-period negative for qualifications, other legal/regulatory matters, EOM); p253 scheme narrative | Pending SEBI revision against the **Promoter** (p470) and a **Director** (p468); concluded SEBI matters against the Promoter (p470–473); p463 "outstanding" framing | Note 37 quantified: 15,021 (31 Mar 2026), commitments 26,198 excluded; equity 3,359,769 |
| **4. Evidence not found / not qualifying** | Any going-concern statement of either polarity; the underlying audit reports (referenced, not reproduced) | Any regulator record after the RHP; any ED/PMLA mention (0); any both-regulator denial; any SEBI action against the Company itself (p464 Nil) | Any unquantified statement in note 37; any completeness statement; the p472 promoter arbitration is outside the note |
| **5. Nature** | Semantic / governance (A19 deferral); no technical loss | **Technical** (5 mechanisms) **+ semantic** ("active" undefined) | Semantic / governance (A20 r8); plus one display-only provenance weakness |
| **6. Is UNKNOWN justified?** | **Yes**, fully | **As the rule's output: yes. As a description of the filing: no** | **Yes**, fully |
| **7. Minimum additional evidence** | Statutory audit reports on the consolidated FS (FY2026 + interim) or an auditor going-concern confirmation | A SEBI/HC record of the revision's current status (external, egress-blocked); not needed to establish it was pending at the RHP date | None for the ratio; for the flag only a positive in-section statement or an approved negative rule |
| **8. Governance decision required** | **None now** — A19alreadydefersit; four prerequisites listed | **Yes — one**: K2-A / K2-B / K2-C (status meaning of "active"). Party scope and the `False` path are already decided | **None now** — A20 r8 settles it. Optional scope extension K5-A/K5-B, recommendation: no change |
| **9. Recommended next action / authority** | No action on the record. Optionally acquire the audit reports in a later evidence pass (Ramki / evidence owner) | Ramki decides K2-A/B/C. If A or B: authorise P1, P2, P4 (+P5) as one implementation pass; P3 separately with negative tests. Until then UNKNOWN stands | No action. If the provenance quote is to be fixed, it is a small display fix requiring implementation authority |

---

## 7. Work classification

**Actionable now (no external dependency, no new decision)**
1. Nothing that changes a recorded value. This pass's deliverable is the diagnosis itself.
2. *Optional, small, needs implementation authority only:* extend the contingent-liability quote to include the amount (provenance defect #6); publish A19–A27 into this branch's `handoff/decisions/` so the code's citations resolve locally.

**Awaiting an authorised governance decision**
1. **K2 status meaning** (K2-A / K2-B / K2-C) — the only genuinely new decision required. Material consequence: A or B ⇒ this filing's K2 becomes TRIGGERED ⇒ `AVOID`.
2. K5 optional scope extension (recommendation: no change).

**Awaiting external evidence access**
1. The underlying statutory auditor's reports (FY2026 + June 2026 interim) or an auditor going-concern confirmation — the only route to a factual resolution of K1 without a new rule.
2. A SEBI / Bombay High Court record of the current status of the revision application — would date the "active" question, though it cannot be obtained from this sandbox (TLS/egress blocked).

**Blocked by technical–environmental limitation**
1. Regulator docket retrieval (as above) — blocked by the same sandbox egress that blocks official issue-term discovery.

---

## 8. Execution statement

- **No regression test was run.** No `pytest`, no `npm test`, no CI trigger.
- **No ingestion and no evaluation** were performed; no evaluation record was created, replaced or re-scored. `…29d9a601` remains the reference.
- **No application, test fixture, schema, config, frontend or expected value was modified.**
- The only engine use was read-only: the published extractor class and its compiled patterns were imported and applied to page text of the retained PDF to locate the exact loss points. The page text was read with `pypdf`, the same reader the engine uses.
- Nothing was merged into `main`; nothing was promoted.

## 9. Files added by this pass

| Path | Content |
|---|---|
| `docs/investigation/JIO-K1-K2-K5-DISPOSITION-2026-10-23.md` | This report |
| `docs/investigation/jio-k125-20261023/k1-going-concern.json` | K1 rule, evidence, technical findings, governance status |
| `docs/investigation/jio-k125-20261023/k2-sebi-ed-action.json` | K2 rule, quotes, mechanism analysis, options and consequences, correction proposal |
| `docs/investigation/jio-k125-20261023/k2-extraction-reproduction.json` | Page-level reproduction of the twelve discarded spans and each mechanism |
| `docs/investigation/jio-k125-20261023/k5-contingent-liability.json` | K5 rule, verified arithmetic on three bases, provenance defect, scope question |
| `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` | Tracker entry |
