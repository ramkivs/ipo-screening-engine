# A23 — Litigation and SEBI/ED action: evidence or UNKNOWN, never a default

- **Decision ID:** A23 (decision **D-5** of the HD Fire / Jio decision set)
- **Title:** `governance.litigation_bucket` and `governance.sebi_ed_action_active` are evidence-or-UNKNOWN
- **Decision status:** RAMKI-AUTHORIZED IMPLEMENTATION — D-5.1 … D-5.6 executed in this pass.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Authorization basis:** Ramki's 2026-10-20 D-5 instruction: correct the unsupported negative defaults in litigation and regulatory-action extraction, using the existing UNKNOWN/missing contract state; invent no new scored category; do not infer an absence of action from a search result, an inaccessible source or a director-only disclosure; do not infer a SEBI/ED action from a criminal proceeding; publish the exact choice if a governed criterion meaning or scoring changes.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/ae4d04e8-ipo-screening-engine` at remotely verified commit `2d52baa56cbb4b82061649106745f79d04d9fce6` (`main` `01ba66c`, PR #6 open/unmerged).
- **Scope:** `extraction/sections.py::extract_governance` and its new classifiers; `extraction/builder.py::_build_governance`; `extraction/toc.py` litigation section pattern; the tests named below.
- **Implementation authority:** granted for this correction only. No new scored category, formula, weight, threshold, knockout semantic, schema or config change is authorized.
- **Publication status:** see the publication block in the authoritative tracker.

## Contract facts this decision relies on (verified, unchanged)

- `schema/ipo-input.v1.5.schema.json` — `governance.litigation_bucket` enum is
  `["clean", "minor_civil", "criminal_or_regulatory", null]`; `governance.sebi_ed_action_active`
  is `["boolean", "null"]`; `governance` has **no** `required` list.
- `derived.py::_litigation_bucket` already returns UNKNOWN for `None` with the reason *"the
  litigation status of the promoters, directors and company is not established"*.
- `derived.py::_sebi_ed_action_active` is a passthrough whose UNKNOWN reason is *"the supplied
  input does not establish whether an active SEBI/ED action exists"*.
- K2 is `required = [promoter_pledge_pct, sebi_ed_action_active]`, with
  `any[promoter_pledge_pct > 25, flag sebi_ed_action_active]`.

**The UNKNOWN state is fully contract-supported.** No schema, config, formula, weight,
threshold or knockout semantic is changed by this decision.

## Decision

1. **No defaults.** `litigation_bucket = "clean"` and `sebi_ed_action_active = False` are
   findings. They are emitted only from an explicit statement in the filing. When the scanned
   litigation range contains no such statement, both fields are `null` with `is_unknown = True`,
   no `quote`, and a note explaining the limitation. A range that cannot be read, is empty or is
   outside the document is **not** evidence of no proceeding.
2. **`clean` coverage standard.** A clean verdict requires an explicit negative statement that
   names **the issuer** and at least one individual category (**promoters or directors**).
   - One sentence may cover several parties (*"our Company and Promoters"*).
   - The possessive phrase *"Directors of the Company"* / *"Promoters of the Company"* describes
     the individuals and is stripped before the issuer is looked for.
   - **Group companies are not the issuer.** A statement about *"Promoters, Directors, or Group
     Companies"* does not establish the issuer's status.
3. **Positive discovery outranks `clean`.** If the filing discloses a proceeding, the bucket is
   that category whatever else the section says. A finding must name a covered party; a
   proceeding against an unrelated party is not the issuer's exposure.
4. **Director-level proceedings are litigation exposure.** The criterion's own definition is
   *"clean / minor_civil / criminal_or_regulatory (promoters, directors, company)"*, so a
   disclosed criminal proceeding against directors sets `criminal_or_regulatory`. It does **not**
   establish a SEBI/ED action.
5. **SEBI/ED is a separate fact.** `sebi_ed_action_active` is set only on a sentence that names
   SEBI or the Enforcement Directorate, contains an action term (proceedings / actions /
   investigations / show-cause / penalty / orders) and names a covered party.
   - An explicit active action ⇒ `True`; because an active regulatory proceeding against our
     Company, Promoters or Directors is itself a regulatory exposure, it also sets the litigation
     bucket to `criminal_or_regulatory`.
   - A negated action bound to the party ⇒ `False` (e.g. *"there are no outstanding actions by
     SEBI … against the Promoters"*).
   - A criminal proceeding, a bare reference to the SEBI (ICDR) Regulations, an action against an
     unrelated party, or an action reported without a covered party ⇒ `null` (UNKNOWN), **never**
     `True` and **never** `False`.
6. **No synthesised text.** Every emitted `quote` is a verbatim source sentence from the matched
   page. The previously emitted *"No active SEBI or ED regulatory proceedings"* — present in no
   filing — is removed. UNKNOWN records carry no quotation at all.
7. **TOC pluralisation (implementation correctness).** The litigation section pattern matched
   only `OUTSTANDING LITIGATION`; R.K. Fashion's table of contents reads `OUTSTANDING
   LITIGATIONS`, so its litigation pages were never scanned and fell through to the generic
   `(1, 50)` range. The pattern now accepts the plural. No semantic change: without this fix the
   corrected classifier cannot see the filing's own statement.

## The exact choice published at the decision boundary

The correction changes the evidence reaching an unchanged scoring rule, and for one fixture it
changes the recorded score. The choice is recorded here rather than applied silently.

**Fixture `fixtures/filings/class_b_cyclical_manufacturing.pdf`.** Its entire litigation section is
one sentence:

> *"None of our Promoters, Directors, or Group Companies are involved in any material litigation or
> criminal cases."*

The sentence names promoters, directors and group companies — **not the issuer**. Under the
coverage standard above the issuer's status is therefore UNKNOWN.

| | Before D-5 | After D-5 |
|---|---|---|
| `litigation_bucket` | `"clean"` (default) | `null` (UNKNOWN) |
| `sebi_ed_action_active` | `False` (default) | `null` (UNKNOWN) |
| Module D score | 6.0 / 15 (litigation 4/4) | 2.0 / 15 (litigation UNKNOWN) |
| **Final score** | **41.0** | **37.0** |

**Alternative considered and rejected:** treating *"Group Companies"* as covering the issuer would
restore `clean` and the 41.0 score, but it asserts a fact the filing does not state — a group
company is a different legal person from the issuer, and the omission of the Company from an
otherwise exhaustive enumeration is exactly the case D-5 exists to stop converting into a
favourable finding. The 4 points are not "lost to a bug": they were never supported by evidence.

The same standard produces the second measured change: `fixtures/filings/complete_sample_rhp.pdf`
(Aurora Systems Limited, used by the UI-7 ingestion test) is a **4-page sample with no litigation
section anywhere in the document**. It previously scored `clean` / `False` and **23.0**; the
corrected input is UNKNOWN / UNKNOWN and **19.0** (Module D 5.0 → 1.0). The UI-7 expectation was
updated in the same commit with that provenance recorded inline.

No scoring formula, weight, threshold, band, cap, penalty or knockout semantic was changed to
produce 37.0 or 19.0; the same formula receives a corrected input.

## Evidence semantics established (D-5.1, D-5.2)

- **What `clean` means.** No disclosed proceeding across promoters, directors and the issuer,
  stated by the filing — not the absence of a regex hit.
- **Why absence is not proof.** The scan is bounded by a located page range; an unlocated
  section, an unreadable page, an empty page and an incomplete scan are all indistinguishable
  from a clean filing if silence is scored. The contract's null state exists for exactly this.
- **Issuer vs director.** A director-only statement does not speak for the issuer; a
  director-only proceeding is nevertheless scored exposure under the metric's own definition.
- **Pending / disposed / criminal / civil / regulatory** are not separate scored categories; only
  the existing three enum values and null are used. A disclosed criminal proceeding maps to
  `criminal_or_regulatory`; a material civil suit maps to `minor_civil`; an active SEBI/ED action
  against a covered party maps to `criminal_or_regulatory`.
- **The fabricated quotation** *"No active SEBI or ED regulatory proceedings"* is removed from the
  codebase; no emitted quote is synthesised.

## D-5.3 — HD Fire director-proceeding evidence (recorded, not scored)

From the SEBI-hosted Abridged Prospectus (RHP dated 5 October 2026), §12:

- Summary table: **2 criminal proceedings against our Directors** (excluding promoters); issuer
  cells for criminal, civil and regulatory proceedings are Nil.
- 3 tax proceedings by the Company, ₹0.40 million.

Disposition: a **director-level criminal disclosure**, not a SEBI/ED action and not an issuer-level
proceeding; it supports `criminal_or_regulatory` under the metric definition *"across promoters,
directors and the company"* and supports nothing about SEBI/ED. Full HD Fire acceptance remains
outstanding: RHP pages 31–450, the final Prospectus and the historical record `…551a7eab` are not
available in this environment, and nothing is inferred beyond the pages read.

## Measured impact (D-5.5, executed on the fixtures)

| Fixture | Before | After | Δ final | What changed |
|---|---|---|---|---|
| class_a financial lender | `clean` / `False` — 40.0 | `clean` / `False` — 40.0 | 0.0 | none |
| class_b cyclical manufacturing | `clean` / `False` — 41.0 | `None` / `None` — 37.0 | **−4.0** | issuer not named (see above) |
| class_c EPC infrastructure | `clean` / `False` — 41.0 | `clean` / `False` — 41.0 | 0.0 | none |
| class_d loss-making tech | `clean` / `False` — 28.0 | `clean` / `None` — 28.0 | 0.0 | SEBI now UNKNOWN (no score effect) |
| class_e modern complex RHP | `clean` / `False` — 43.0 | `clean` / `False` — 43.0 | 0.0 | none |
| `complete_sample_rhp.pdf` (Aurora Systems, UI-7) | `clean` / `False` — 23.0 | `None` / `None` — 19.0 | **−4.0** | 4-page sample has **no litigation section at all** |
| R.K. Fashion prospectus | `clean` / `False` | `clean` / `False` | 0.0 | now with real quotations; reconciliation tests unchanged |
| HD Fire synthetic §12 table | `criminal_or_regulatory` / `False` | `criminal_or_regulatory` / `None` | n/a | SEBI no longer inferred from the table |

"Before" for a fixture whose corrected value is `null` is the pre-D-5 default applied to the same
extraction, so the delta isolates the correction. No historical evaluation record was re-run,
rewritten or re-hashed.

## Explicit exclusions

- No new scored category, enum value, metric, formula, weight, threshold, cap, penalty or
  knockout semantic.
- No change to `config/`, `schema/` or `fixtures/` (diffs empty; golden hash
  `e84f8bc0…19e1` unchanged; frozen core PASS).
- No change to K2's `required` list or to `sebi_ed_action_active`'s type.
- No inference of an absence of proceedings from an unsearched, inaccessible or empty source.
- No SEBI/ED finding from a criminal proceeding or from a director-only disclosure.
- No HD Fire acceptance claim; no historical evaluation re-run.

## Unresolved / deferred

- **HD Fire:** RHP pp. 31–450, the final Prospectus, the historical `…551a7eab` record and the
  remaining acceptance items are outstanding. D-5.3 records only what S1 §12 states.
- **Positive-detection conservatism:** a disclosure sentence without a count or a live-status word
  (*"a criminal complaint was filed against our Company"*, no number, no "pending") is not accepted
  as a finding; the field stays UNKNOWN. This is deliberate — the alternative risks converting a
  heading into a punitive finding — and is recorded as a capability limit, not a defect.
- **Section location:** a filing without a litigation TOC entry falls back to pages 430–500; since
  D-5 that yields UNKNOWN rather than `clean`, which is correct but may under-read short filings.
- **No completeness proof:** an explicit negative statement is accepted at face value; the engine
  cannot verify that the statement covers every proceeding.

## Tests

- `tests/test_litigation_regulatory_defaults.py` — **20 passed**, covering the nine D-5.4
  regressions: no evidence; documented clean; issuer-level proceeding; director-only proceeding;
  criminal not establishing SEBI/ED; explicit active SEBI/ED; missing/inaccessible/incomplete
  coverage; no synthesised quotation; no accidental scoring change (4/2/0 map, UNKNOWN reason,
  golden score reproduction).
- `tests/test_hd_fire_primary_source_extraction.py` — the two strict xfails that pinned these
  defects are replaced by passing assertions of the corrected contract (null candidate,
  `is_unknown`, no quote). Expected failures were not removed for any unresolved capability.
- `tests/test_extraction_phase5b.py` — class B expectation updated from 41.0 to 37.0 with its
  provenance recorded inline (see "the exact choice" above).
- `tests/test_rk_fashion_reconciliation.py` — unchanged and passing with real quotations.
- `tests/test_ui7_ingestion.py` — the Aurora Systems sample (no litigation section) expectation
  changed from 23.0 to 19.0 in two assertions, with provenance inline; the file passes 20/20.
- Full backend suite on the final tree: **1218 passed, 0 failed, 0 xfailed, 38 warnings,
  1211.19 s**. The first run (before the UI-7 expectation was corrected) failed only that one
  assertion, which is how the second affected fixture was found.
