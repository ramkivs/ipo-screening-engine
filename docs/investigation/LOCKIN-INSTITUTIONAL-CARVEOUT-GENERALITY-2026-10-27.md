# Regulation 17 institutional lock-in carve-out — general rule and cross-issuer coverage

Companion to `PARAS-UNKNOWN-TRIAGE-2026-10-27.md`. That report found the Paras
`lockin` UNKNOWN was a reader defect; this one asks whether the correction is a
**reusable engine capability** or an issuer-specific patch, and pins the rule.

The canonical field is `capital_structure.large_holders_unlocked_early`
(`schema/ipo-input.v1.5.schema.json`: `boolean` or `null`). It is consumed by
`derived._lockin_bucket` (`engine/ipo_screening/derived.py`):

```
intact  = promoter_lockin_in_place AND NOT large_holders_unlocked_early
weak    = otherwise
UNKNOWN = either input is None
```

`builder._build_capital_structure` forwards the extracted value through
`_cap_value`; `canonical_input.flag` reads it; the builder emits it verbatim as
evidence. No weight, boundary, threshold, penalty, knockout rule or cap is
touched by this work.

---

## 1. Was the implementation issuer-specific?

**No.** The reader added for Paras keys on the disclosed semantics, not on any
issuer's identity:

| potential issuer-specific dependency | present? |
| --- | --- |
| issuer / promoter names or identifiers | none |
| page numbers | none (the range comes from the TOC router) |
| exact quoted passages | none (the regex matches a category + a lock-in term) |
| dates or transaction values | none |
| special-case branches | none |
| scoring adjustments | none |

The rule generalises as written: it matched the same provision in two other
real filings (Jio, Moneyview) and correctly declined two filings that disclose
only a promoter lock-in (Vishal Nirmiti, R.K. Fashion). What it *was* narrow in
is wording coverage, and that is what §2 fixes.

---

## 2. The general extraction rule

`SectionExtractor.extract_capital_structure` (`engine/ipo_screening/extraction/sections.py`)
sets `capital_structure.large_holders_unlocked_early = True` when a filing
discloses the **Regulation 17 pre-Offer lock-in carve-out**:

* an **institutional / venture holder category** — `VCF`, `Venture Capital
  Fund`, `Category I AIF`, `Category II AIF`, `Alternative Investment Fund`,
  `FVCI`, `Foreign Venture Capital Investor`; and
* a lock-in **anchored to the date of purchase (or acquisition)** —
  `locked-in for [at least] six months from the date of [their] purchase` —
  which is a **different commencement date** from the general pre-Offer lock-in
  (six months from Allotment).

A holder that purchased before the Offer is therefore free at Allotment: an
early unlock of a large pre-IPO holder.

Recognition rules:

* **Order independent** — the category may precede or follow the lock-in clause
  (`VCF … locked-in … from the date of purchase` *or* `locked-in … from the date
  of purchase … VCF`).
* **Spelling independent** — abbreviated (`VCF`, `FVCI`) and spelled-out
  (`venture capital fund`, `alternative investment fund`,
  `foreign venture capital investor`) forms.
* **Anchor independent** — `purchase` or `acquisition`; `their` optional.
* **Typography independent** — `locked-in`, `locked in`, `locked -in`;
  `six months` or `6 months`.
* **Fail-closed** — the flag is set **only** where both halves are present in
  the same sentence. It is not set when a filing merely mentions a category,
  when the category gets the general Allotment-anchored lock-in, when the
  purchase-anchored lock-in is longer than six months, when only the promoter
  lock-in is stated, or when there is no lock-in disclosure at all. In every
  such case the field stays absent and `_lockin_bucket` returns UNKNOWN.

The quotation is the matched span of the filing's own text, with page
provenance, `section`, `locator` and `quote_is_processing=False`, so the
evidence contract is unchanged.

---

## 3. Cross-issuer evidence

Real filings in the repository, all read through the standard
`DocumentExtractor` / `SectionExtractor` path unless noted:

| filing | source | carve-out | result |
| --- | --- | --- | --- |
| **Paras Healthcare** | `evidence/non-authoritative/paras-healthcare/` (RHP p. 117) | `VCF or a Category I AIF or a Category II AIF or a FVCI … locked-in for a period of at least six months from the date of purchase` | `True` (page 117) |
| **Jio** | `evidence/non-authoritative/jio/` (RHP p. 105) | `equity shares held by a VCF or Category I AIF or Category II AIF or FVCI shall not be locked-in for six months from the date of Allotment, provided that … at least six months from the date of purchase` | `True` (page 105) |
| **Moneyview** | `handoff/investigation/A8-M-MONEYVIEW-SOURCE-EVIDENCE/` (p. 485) | `the shareholding of VCFs, Category I AIFs or Category II AIFs and FVCIs … was exempt from lock-in requirements, provided that … at least six months from the date of purchase` | `True` (rule level) |
| **Vishal Nirmiti** | `handoff/reference/` (RHP pp. 115–117) | promoter lock-in only; carve-out is only for OFS-transferred shares | absent (UNKNOWN) |
| **R.K. Fashion** | `handoff/reference/` (RHP pp. 121–125) | promoter lock-in only | absent (UNKNOWN) |
| `fixtures/filings/class_a`–`class_e`, `complete_sample_rhp`, `complete_sample_rhp_2` | `fixtures/filings/` | no lock-in disclosure | absent (UNKNOWN) |

**Coverage note (Moneyview).** The Moneyview provision is printed in the
bidder-category section (p. 485), outside the capital-structure page range the
TOC router routes for that filing (`(112, 139)`). The reader is scoped to the
routed range, so Moneyview is exercised **at the rule level** from the real page
text. It is not claimed as an end-to-end positive. Widening the reader's page
scope is a separate routing concern and is deliberately out of scope here.

---

## 4. Test matrix

`tests/test_lockin_institutional_carveout.py` (17 tests):

* **positive — real filings**: Paras p. 117, Jio p. 105, Moneyview p. 485 (rule
  level). Each asserts the value, the page, and a verbatim quotation.
* **negative — real filings**: Vishal Nirmiti and R.K. Fashion, via the
  TOC-routed range — no flag, promoter lock-in still `True`.
* **positive — synthetic wording variations** (labelled): reverse order,
  spelled-out categories, `from the date of their acquisition`, `locked -in`,
  plural `VCFs` / `Category I AIFs`, `6 months`.
* **ambiguous — synthetic**: category named without a purchase-anchored
  lock-in; category given the general Allotment-anchored lock-in; a longer
  (`three years`) purchase-anchored lock-in. All stay absent.
* **absent — synthetic**: no lock-in text; promoter-only lock-in.
* **consumer**: the extraction reaches the canonical field through
  `CanonicalInputBuilder`; `lockin_bucket` maps `True → weak`, `False →
  intact`, absent → UNKNOWN; and setting the flag moves **only** module C.

The synthetic cases are labelled as such in the file; they exist only to cover
wording the corpus does not represent. No evidence is fabricated.

---

## 5. Verification

* Focused suite: `tests/test_lockin_institutional_carveout.py` — 17 passed.
* Paras end-to-end (`DocumentExtractor` → `CanonicalInputBuilder` →
  `pipeline.evaluate`, identity-bound price band 660/693 and lot 21):
  **final 13.0, base 16.0, penalty −3.0, AVOID, K5 TRIGGERED, completeness
  44.21%**, `lockin` SCORED 0 (`weak`). The score, verdict and knockout are
  unchanged from the pinned PR #12 record (13.0 / 43.16% / AVOID); the
  completeness rises because the criterion moves from UNKNOWN to scored-0.
* Full suite: `pytest tests/` — **2166 passed, 0 failed, 0 errors**.

---

## 6. Remaining limitation

* **Period-difference carve-outs.** The rule keys on a *commencement-date*
  difference (purchase vs Allotment), which is the only institutional carve-out
  form present in the repository corpus. A filing that shortened the *period*
  for an institutional category (e.g. "locked-in for three months") would not
  be recognised and would stay UNKNOWN. No such disclosure exists in the
  corpus, so this is left fail-closed rather than guessed.
* **Page scope.** The reader scans the TOC-routed capital-structure range. A
  carve-out printed in another section (Moneyview) is not picked up end-to-end.
