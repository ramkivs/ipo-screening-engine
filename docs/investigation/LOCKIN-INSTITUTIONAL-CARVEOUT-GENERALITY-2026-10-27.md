# Regulation 17 institutional lock-in carve-out — generality, and the A34 semantic correction
— 2026-10-27 (revision 2: A34 approved and implemented)

Companion to `PARAS-UNKNOWN-TRIAGE-2026-10-27.md`,
`handoff/decisions/A34-early-unlock-carve-out-semantics.md` and
`A33-A34-ISSUER-REPRODUCTION-2026-10-27.md`.

**Revision 1 (PR #13, commit `cac095d`) asked whether the carve-out reader was
a reusable engine capability and answered yes: it recognised the carve-out in
three real filings and set `capital_structure.large_holders_unlocked_early`.
That *recognition* was general and its provenance was sound. Its *meaning* was
wrong.** A34 Alternative B is now approved: a category carve-out alone is not
evidence of an early unlock. The reader has been corrected, the 17-test matrix
has been replaced by a 28-test semantic-boundary suite, and the issuer results
have been re-measured. Values from revision 1 are labelled **pre-A34 baseline**
below and are retained, not rewritten.

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
evidence. **No weight, boundary, threshold, penalty, knockout rule, cap,
config, schema or frozen-core file is touched by A34.**

---

## 1. Was the original implementation issuer-specific?

**No — and that was never the defect.** The revision-1 reader keyed on the
disclosed semantics, not on any issuer's identity:

| potential issuer-specific dependency | present? |
| --- | --- |
| issuer / promoter names or identifiers | none |
| page numbers | none (the range comes from the TOC router) |
| exact quoted passages | none (the regex matched a category + a lock-in term) |
| dates or transaction values | none |
| special-case branches | none |
| scoring adjustments | none |

It matched the same provision in two other real filings (Jio, Moneyview) and
declined two filings that disclose only a promoter lock-in (Vishal Nirmiti,
R.K. Fashion). The defect was **semantic, not geographic**: the rule generalised
an inference the text does not support.

## 2. The general extraction rule after A34

`SectionExtractor.extract_capital_structure`
(`engine/ipo_screening/extraction/sections.py`) sets
`capital_structure.large_holders_unlocked_early = True` **only** where a single
sentence evidences an **actual early release** of large pre-IPO holders. Four
elements must co-occur in that sentence:

1. a named holder group — `large holders`, `pre-IPO shareholders`,
   `institutional investors`, `promoters`, `VCF` / `Venture Capital Fund`,
   `Category I/II AIF`, `AIF` / `Alternative Investment Fund`, `FVCI` /
   `Foreign Venture Capital Investor`;
2. a release act — `released`, `unlocked`, `exempted`, `waived`, `relaxed`,
   `removed` (or the noun forms);
3. a lock-in context — `lock-in` / `locked-in`;
4. explicit early timing — `early` / `premature(ly)` near the release or
   lock-in, or `before` / `prior to` / `ahead of` / `in advance of` the
   `expiry` / `expiration` / `end` / `completion` of a lock-in.

A sentence containing hypothetical, conditional, requested, proposed or
negated language (`may seek`, `subject to`, `no`, `not`, `never`, `unless`,
`sought`, `proposed`, …) is **ambiguous** and stays UNKNOWN. The matched
sentence — the filing's own words, whitespace-normalised — is the quotation,
with page, `section`, `locator` and `quote_is_processing=False`.

**What is deliberately ignored.** The Regulation 17(1)(c) carve-out — an
institutional category plus a lock-in of at least six months from the date of
purchase — states a *different commencement date and a minimum*. It prints no
purchase dates, so it can produce an earlier, equal or later release. It is
therefore **not** evidence of an early release and no longer emits anything.
A pledge release, ordinary transferability wording, a release on normal expiry,
a category mention alone, an Allotment-anchored lock-in, a longer
purchase-anchored lock-in, an absent disclosure and a promoter-only lock-in all
leave the flag unset (UNKNOWN). No favourable `False` is inferred either.

> **Correction history.** Revision 1 inferred an early unlock from the
> carve-out ("a holder that purchased before the Offer is therefore free at
> Allotment"). That inference is withdrawn. It was first recorded as an open
> decision (A34, PROPOSED) and is now resolved: **A34 Alternative B is
> approved and implemented.**

## 3. Cross-issuer evidence (same five real filings, re-measured)

| filing | source | carve-out printed? | revision-1 (pre-A34) result | **after A34** |
| --- | --- | --- | --- | --- |
| **Paras Healthcare** | `evidence/non-authoritative/paras-healthcare/`, RHP p. 117 | yes — "VCF or a Category I AIF … at least six months from the date of purchase" | `True` (page 117), `lockin` SCORED 0 `weak`, completeness 44.21% | **absent (UNKNOWN)**, `lockin` UNKNOWN, completeness 43.16% |
| **Jio** | `evidence/non-authoritative/jio/`, RHP p. 105 | yes — "VCF or Category I AIF … at least six months from the date of purchase" | `True` (page 105), `lockin` SCORED 0 `weak`, completeness 63.0% | **absent (UNKNOWN)**, `lockin` UNKNOWN, completeness 62.0% |
| **Moneyview** | `handoff/investigation/A8-M-MONEYVIEW-SOURCE-EVIDENCE/`, p. 485 | yes (purchase-anchored minimum) | `True` (rule level) | **absent (UNKNOWN)** |
| **Vishal Nirmiti** | `handoff/reference/`, RHP pp. 115–117 | no — promoter lock-in only | absent (UNKNOWN) | **absent (UNKNOWN)** |
| **R.K. Fashion** | `handoff/reference/`, RHP pp. 121–125 | no — promoter lock-in only | absent (UNKNOWN) | **absent (UNKNOWN)** |
| `fixtures/filings/*` | synthetic fixtures | no lock-in disclosure | absent (UNKNOWN) | **absent (UNKNOWN)** |

The carve-out quotes were re-extracted with `pypdf` for the A34 reproduction
and are asserted verbatim in the regression suite, so the reader is proven to
*see* the text and deliberately decline it — the tests would fail if the
quotation or page moved.

**Coverage note (Moneyview).** Its provision is printed in the bidder-category
section (p. 485), outside the capital-structure range the TOC router routes for
that filing (`(112, 139)`). It is exercised at the **rule level** from the real
page text, not end-to-end. Widening the reader's page scope is a separate
routing concern and was not done.

**Corpus limitation — stated explicitly.** A full-text scan of all 2,826 pages
of the five real filings found **zero** sentences evidencing an actual early
release. This is a limitation of the corpus, **not proof that early releases
never occur**, and it is not offered as such. Genuine positive cases are
retained as labelled synthetic tests because no real filing exercises the
positive path. A filing that prints a dated lock-in table showing an early
release is exactly the case the corrected reader is designed to catch.

## 4. Test matrix after A34

`tests/test_lockin_institutional_carveout.py` — **28 tests**:

* **real filings, carve-out does not set the flag**: Paras p. 117, Jio p. 105,
  Moneyview p. 485 (rule level), with the carve-out quote asserted on the page;
  Vishal Nirmiti and R.K. Fashion (TOC-routed range): no flag, promoter lock-in
  still `True`.
* **carve-out wording variants (synthetic)**: reverse order, spelled-out
  categories, `from the date of their acquisition`, `locked -in`, plural
  `VCFs`, `6 months` — all stay UNKNOWN.
* **ambiguous disclosures (synthetic)**: category-only mention,
  Allotment-anchored lock-in, longer (`three years`) purchase-anchored lock-in
  — all stay UNKNOWN.
* **unrelated language (synthetic)**: pledge release, freely transferable,
  pledge over promoter shares released, promoter-only lock-in — all stay
  UNKNOWN.
* **hypothetical / negated release (synthetic)**: `may seek`, `No early
  release`, `were not released early` — all stay UNKNOWN.
* **genuine positives (synthetic, labelled)**: a dated release three months
  before expiry of the six-month lock-in; an explicitly named "early release of
  the lock-in" to VCF/AIF shareholders; and a page containing both a carve-out
  and a separate evidenced release. Each asserts `True`, the page, a verbatim
  quotation and `quote_is_processing=False`.
* **normal release on expiry** stays UNKNOWN; **absent disclosure** stays
  UNKNOWN; the extraction reaches the canonical field; `lockin_bucket` maps
  `True → weak` / `False → intact` / absent → UNKNOWN; setting the flag moves
  **only** module C.

`tests/test_reading_defects_20261026.py` additionally pins that the two Paras
carve-out phrasings no longer set the flag and that one evidenced release does.

## 5. Verification (this pass)

* Focused A34 suite: **28 passed**; batch with the reading-defects module,
  issuer-reproduction module and tier gate: **65 passed**; eight affected
  regression modules: **132 passed**. Tier gate green. Full backend suite
  **not run by instruction** — see `A33-A34-ISSUER-REPRODUCTION-2026-10-27.md`
  §5 for the exact scope and the surviving-evidence caveat.
* Frozen core, golden result, inactive v1.6, all schemas and `compileall`
  engine: **PASS**.
* Paras end-to-end after A34: **13.0 / 16.0 / −3.0 / 43.16% / `AVOID` / K5
  TRIGGERED / `lockin` UNKNOWN / `board_kmp` SCORED 0 `high_churn`**.
* Jio end-to-end after A34: **37.0 / 37.0 / 0.0 / 62.0% / `AVOID` / K2
  TRIGGERED / 25–75 / `lockin` UNKNOWN / `board_kmp` SCORED 0 `high_churn`**.
* Revision-1 figures retained as baselines only: Paras 13.0 / 44.21% and
  Jio 37.0 / 63.0%, both with `lockin` SCORED 0 `weak`. Revision 1's full-suite
  figures (2166, then 2169, then 2183) belong to earlier trees; **no new full
  suite figure is claimed here.**

## 6. Remaining limitations

* **No real-filing positive case.** Positive coverage is synthetic; the five
  examined filings disclose carve-outs or promoter lock-ins, not releases.
* **Page scope.** The reader scans the TOC-routed capital-structure range;
  Moneyview's provision is exercised at rule level only.
* **Wording coverage.** The evidenced-release rule is intentionally narrow and
  fail-closed; a filing that words an early release in an unrecognised form
  stays UNKNOWN rather than being guessed.
* **Structured carve-out field (alternative C) not implemented.** Recording the
  carve-out itself as a category + anchor structure needs a schema and
  canonical-input decision of its own.
* **Governance recording.** A32 remains `NOT RATIFIED`; A34's approval does not
  ratify it. Both facts must stay visible in the tracker (A34 §0.3).
