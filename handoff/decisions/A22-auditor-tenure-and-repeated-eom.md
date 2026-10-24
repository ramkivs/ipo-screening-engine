# A22 — Auditor Tenure and Repeated Emphasis of Matter: Evidence or UNKNOWN

- **Decision ID:** A22 (decision **D-4** of the HD Fire / Jio decision set)
- **Title:** auditor tenure and repeated-EOM fields are evidence-or-UNKNOWN
- **Decision status:** RAMKI-APPROVED POLICY. Cross-year repeated-EOM comparison is deferred.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Authorization basis:** Ramki's direct 2026-10-20 instruction approving the D-4 recommendation: *"Retain the current evidence-or-UNKNOWN behaviour. Defer automated repeated-EOM comparison across years."* The same instruction preserves the removal of unsupported constant defaults and synthesised quotations.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/ae4d04e8-ipo-screening-engine` at remotely verified commit `7754f9b397696e72ab025eca964325aa074f2796`.
- **Scope:** `governance.auditor_changed_3y`, `governance.repeated_eom`, `governance.auditor_reputed`, and `derived.py::_auditor_bucket`'s use of them.
- **Implementation authority:** none required in this pass; the correction was published in `e2ce2c2` and is verified here. No cross-year comparison is authorized.
- **Publication status:** recorded in the authoritative tracker; the implementation commit is identified there.

## Decision

1. `auditor_changed_3y` is `False` **only** when the auditors' report contains a positive
   statement that the same auditor audited the three fiscal years. Otherwise the field is
   absent and the value is UNKNOWN. There is no unconditional default.
2. `repeated_eom` is `False` **only** when the report contains an explicit negative Emphasis
   of Matter statement and no positive EOM statement. Otherwise the field is UNKNOWN. It is
   never emitted `True` by inference.
3. Emitted quotations are the **verbatim matched source sentence** and the page actually
   matched; a sentence that is not in the filing is never attributed to it.
4. `_auditor_bucket` semantics are unchanged: unknown tenure ⇒ UNKNOWN; `clean_reputed`
   requires unqualified + reputed + `auditor_changed_3y = False`; `eom_only` covers
   EOM/unqualified-without-reputed; `unstable_or_repeated_eom` requires changed true or
   repeated EOM true.
5. A **cross-year repeated-EOM comparison is deferred**.

## Rationale

- Before `e2ce2c2`, `aud_changed_3y` was a constant `False` (assigned before the tenure loop
  and re-assigned inside both branches) and `repeated_eom` was emitted `False` on any matched
  auditor name, each with a synthesised quotation that appears nowhere in the filing. Together
  they resolved `clean_reputed` (2/2) from an unqualified opinion alone — missing evidence was
  converted into a favourable fact.
- The schema allows `boolean | null`, and `_auditor_bucket` already treats `None` as UNKNOWN.
  Removing the constants is therefore implementation correctness under the existing contract,
  not a new rule.

## Scope

- `engine/ipo_screening/extraction/sections.py::extract_governance` (tenure and EOM blocks).
- `derived.py::_auditor_bucket` (unchanged).
- Module D auditor criterion (unchanged).

## Explicit exclusions

- No change to the auditor score bands (2 / 1 / 0) or to `clean_reputed` semantics.
- No automated comparison of two years' reports; no `True` path for repeated EOM.
- No change to `auditor_reputed`'s established reputed-firm lookup.
- No fabricated history, tenure or quotation.

## Implementation implications

None in this pass. The corrected behaviour requires a positive tenure sentence for `False`
(verbatim sentence, page actually matched) and an explicit negative EOM statement for `False`.
Both fields stay absent when the evidence is missing, so the criterion is UNKNOWN and cannot
award points.

## Verification evidence

| Check | Result |
|---|---|
| `tests/test_auditor_tenure_defaults.py` | **9 passed** — name/reputed; no tenure ⇒ no field; no EOM ⇒ no field; tenure sentence ⇒ `False` + verbatim quote; explicit negative EOM ⇒ `False` + verbatim quote; positive EOM does not set repeated EOM; quotes are verbatim; unknown tenure ⇒ `auditor_bucket` UNKNOWN; known tenure ⇒ `clean_reputed` |
| R.K. Fashion | `auditor_changed_3y` is `None` (was asserted `False`); its auditor criterion was already UNKNOWN ⇒ no score change |
| Jio live filing | no auditor name matched ⇒ fields absent ⇒ auditor criterion UNKNOWN |
| Controlled evaluation | unqualified + reputed, changed `False` ⇒ score 18.0 (available 25); `None` ⇒ 16.0 (available 23) |
| Full backend suite (`pytest tests -q`, final tree) | **1192 passed, 0 failed, 0 xfailed**, 38 warnings, 1566.58 s (baseline `7754f9b`: 1179 passed, 1 xfailed, 1542.57 s) |

## Deferred work — prerequisites for cross-year repeated-EOM comparison

1. **Two-report coverage:** both years' auditors' reports must be present and identifiable in
   the supplied document set; a single RHP carries the current year's report only.
2. **Matching key:** auditor identity (firm registration number / name) must be matched across
   years without relying on a hard-coded firm list.
3. **EOM comparison semantics:** what counts as "repeated" — same matter, same wording, same
   financial statement line — and how a changed but related matter is treated.
4. **Failure modes:** missing prior-year report, auditor change, restated comparatives.
5. **A governed `True` path** with a citation to both reports before the field may be set true.

## Limitations and unresolved blockers

- No positive repeated-EOM detection exists; a filing that genuinely repeats an EOM will show
  UNKNOWN, not `True`. This is a documented capability gap, not a silent pass.
- HD Fire's auditor report is unavailable; its auditor inputs remain UNKNOWN and no tenure or
  EOM claim is made for it.
