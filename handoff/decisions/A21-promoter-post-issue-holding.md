# A21 — Promoter Post-Issue Holding: Disclosed Figure and Table Scope

- **Decision ID:** A21 (decision **D-3** of the HD Fire / Jio decision set)
- **Title:** `promoter_post_pct` means the disclosed post-issue promoter holding
- **Decision status:** RAMKI-APPROVED POLICY, with the narrow implementation authorized.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Authorization basis:** Ramki's direct 2026-10-20 instruction approving the D-3 recommendation: *"`promoter_post_pct` means the disclosed post-issue promoter holding. Do not substitute a diluted pre-issue percentage merely to preserve scores. The narrow combined-row guard already implemented is retained."* The same instruction requires the D-3b table-scope resolution and the listed regression cases.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/ae4d04e8-ipo-screening-engine` at remotely verified commit `7754f9b397696e72ab025eca964325aa074f2796`.
- **Scope:** `capital_structure.promoter_pre_pct` / `promoter_post_pct` extraction, Module D `promoter_post_holding`, and K4's `promoter_full_exit` / `< 20` leaves.
- **Implementation authority:** GRANTED for `extract_capital_structure` only. No weight, threshold, fixture or record change.
- **Publication status:** recorded in the authoritative tracker; the implementation commit is identified there.

## Decision

1. `promoter_post_pct` is the **disclosed post-issue holding of the promoter category**, and of
   the promoter-group category where the filing's category (B) is the promoter group. It is
   not a diluted or otherwise inferred pre-issue percentage.
2. The combined summary row `Total (A)+(B)+(C)` is the whole company and is **never** read as a
   promoter total.
3. The public category is **never** added to the promoter holding. When the filing labels
   category (B) as the promoter group, its total is added; when (B) is public, it is not.
4. A post-issue value is read only from a table that **explicitly** declares a post-issue
   column (`Post-Offer`, `Post-Issue`, `after the Offer`, `on Allotment`) and whose total row
   carries a numeric percentage in more than one column. A row whose post-issue cells are
   `[●]`, or a pre-issue-only table, leaves the post-issue holding **UNKNOWN**.
5. When the category of a `Total (B)` row cannot be established, the promoter total is
   **UNKNOWN** rather than guessed.
6. Diluting the pre-issue holding by the offer size is **not** an authorised substitute; it
   changes the meaning of the field and was rejected for that reason.

## Rationale

- The field feeds Module D `promoter_post_holding` and K4; fabricating it (100 % where the
  filing states 66.43 %) both awarded points and kept K4 CLEAR on a structurally impossible
  value.
- The combined-row guard (`_TOTAL_A_LABEL` with `(?!\s*[+(])`) removes that artefact without
  choosing a new definition. It is retained.
- **D-3b evidence:** Vishal Nirmiti's section 11 table is a **pre-issue-only** table whose
  post-issue cells are `[●]`; the previous fallback read its pre-issue `Total (A)` of 37.51 %
  as the post-issue holding. R.K. Fashion's table, by contrast, has numeric pre- and
  post-issue columns (99.61 / 72.22 for promoters and 0.06 / 0.03 for the promoter group), so
  its 99.67 / 72.25 must be preserved.
- Reading the category label is not a new metric definition: it is what distinguishes
  "(B) Public" from "(B) Promoter Group" in the filing itself.

## Scope

- `engine/ipo_screening/extraction/sections.py::extract_capital_structure`:
  `_TOTAL_A_LABEL`, `_PROMOTER_CATEGORY_LABEL`, `_POST_ISSUE_CONTEXT`, and the pre/post
  fallbacks.
- Downstream: canonical `capital_structure.promoter_{pre,post}_pct`; `derived.py`
  Module D and K4 leaves (unchanged).

## Explicit exclusions

- No scoring weight, band, threshold or knockout change; no golden-fixture change.
- No re-run or rewrite of any historical evaluation record.
- No hard-coded Jio 66.43 % or HD Fire 85.0 %.
- No dilution-based derivation as a substitute for a disclosed post-issue figure. (The
  separate `enrichment_engine` derivation, which computes a post-issue percentage from
  disclosed pre-issue shares, disclosed OFS seller shares and post-issue shares and marks it
  `SRC-DERIVED`, is unchanged; it is a provenance-marked derivation, not a disclosed value.)
- No change to `promoter_post_pct`'s schema type or to the Module D criterion.

## Implementation implications

The fallbacks now: (i) require a standalone `Total (A)`; (ii) read percentages from the row
itself, never the following category block; (iii) determine the category of a `Total (B)` row
from the nearest heading (promoter / promoter group / public / non-promoter); (iv) require a
post-issue marker before using a second numeric percentage as the post-issue value; (v) return
`None` when the category or the post-issue cell is not established.

## Verification evidence

| Check | Result |
|---|---|
| `tests/test_promoter_holding_extraction.py` | **8 passed** (7.32 s) — combined row; standalone total; public not added; promoter group added; pre-issue-only table ⇒ post UNKNOWN; unlabelled (B) ⇒ UNKNOWN; live Jio; live Vishal |
| R.K. Fashion | **99.67 / 72.25** unchanged (`test_rk_fashion_reconciliation`, `test_fixture_fallback_isolation`) |
| Jio (committed RHP) | pre/post **None / None** (was 100 / 100) |
| Vishal (reference RHP) | pre **73.42**; post **None** (was 37.51, a pre-issue figure) |
| Focused regression battery (11 files) | **153 passed** (344.58 s) |
| Controlled evaluation | `promoter_post_pct` 37.51 ⇒ score 14.0, available 23; `None` ⇒ 13.0, available 19 (one earned point and four available points differ) |
| Full backend suite (`pytest tests -q`, final tree) | **1192 passed, 0 failed, 0 xfailed**, 38 warnings, 1566.58 s; the former strict-xfail pin for the public `Total (B)` defect now passes, so no xfail remains in this file |

The Vishal change is a live-extraction effect. Its historical scorecard was **not** re-run or
rewritten; the arithmetic above is the measured consequence on the engine's controlled fixture.

## Deferred work

1. **HD Fire's 85.0 %:** the proposed figure is unverified. Under this decision it would be
   accepted only if the RHP discloses it as the post-issue holding of the promoter category.
2. **Post-only tables** (a table with a single numeric post-issue column and no pre-issue
   column) remain UNKNOWN; supporting them requires an explicit table-type rule.
3. **Filings without category headings** remain UNKNOWN even if their arithmetic is
   unambiguous; a label-inference rule would need its own decision.
4. **Integer-only percentage cells** are not read by the row helper; they fail closed.

## Limitations and unresolved blockers

- HD Fire's shareholding table is unavailable; the 85.0 % arithmetic (26,284,500 of
  175,228,782 shares) is a documented claim, not a verified extraction, and is not presented
  as one.
- The extraction's processing quotations remain explicitly flagged `quote_is_processing=True`;
  they are not source quotations and no source page is cited for a computed percentage.
