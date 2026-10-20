# HD Fire / Jio — decision resolution and defect remediation readiness

**Date:** 2026-10-20
**Branch:** `arena/ae4d04e8-ipo-screening-engine`
**Starting commit:** `ebd177c` (remote-verified tip at the start of this pass)
**`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094` — untouched
**PR #6:** OPEN / UNMERGED at head `e05c0ef`

This document closes the four defects/decisions named in the HD Fire RHP evidence
reconciliation (D-1 … D-4), separates **implementation correctness** from **missing source
evidence**, and records the semantic questions that still require operator authorization.

It does not change any scoring weight, threshold, formula, cap, penalty, knockout semantic,
golden fixture, historical evaluation, or result-hash rule. No historical record was re-run,
rewritten or re-hashed. No HD Fire primary source was obtained or claimed.

---

## 0. Starting state (verified, not assumed)

| Item | Value | How verified |
|---|---|---|
| Local branch tip | `ebd177c` + uncommitted work | `git rev-parse HEAD`, `git status` |
| Remote branch tip | `ebd177c` | `git fetch origin refs/heads/arena/ae4d04e8-ipo-screening-engine` + `git rev-parse FETCH_HEAD` |
| `main` | `01ba66c` | `git rev-parse origin/main` |
| PR #6 | OPEN, `mergedAt: null`, head `e05c0ef` | `gh pr view 6` |
| HD Fire RHP in any branch | **absent** | all 17 branches tree-searched (`gh api …/git/trees/<branch>?recursive=1`) — only investigation `.md` files match `hd[-_ ]*fire` |
| `evaluations/` directory | **absent** | `git ls-tree -r --name-only origin/main \| grep -c '^evaluations/'` → 0 |
| Live retrieval | **not possible** | sandbox egress returns HTTP 000; no NSE/BSE/SEBI/issuer claim is made |

Consequence carried forward from the reconciliation pass: every HD Fire value used here is a
**documented claim**, graded by arithmetic and input-contract consistency only. No page, note
number or verbatim excerpt from an HD Fire filing is cited anywhere in this document.

---

## 1. D-1 — going-concern uncertainty (K1)

### 1.1 Contract and code path

* **Config (unchanged):** K1 `required = [auditor_opinion, going_concern_uncertainty,
  net_worth_latest]`; fires when the opinion is `qualified | adverse | disclaimer` **or**
  `going_concern_uncertainty` is true **or** `net_worth_latest < 0`.
* **Schema (unchanged):** `governance.going_concern_uncertainty` is `boolean | null`.
* **Path:** `SectionExtractor._GOING_CONCERN_UNCERTAINTY` (raw phrase regex)
  → `SectionExtractor._going_concern_uncertainty_match()` (polarity filter, the **only**
  consumer) → `RawExtraction` emitted **only on a positive match**
  → `builder.py:334` `_pick_gov("going_concern_uncertainty", None)`
  → canonical `governance.going_concern_uncertainty`
  → `derived.py:2212` passthrough (absent ⇒ UNKNOWN)
  → K1 leaf, evaluated with Kleene three-valued logic (`knockouts.py`).

`grep -rn "_GOING_CONCERN_UNCERTAINTY" engine/` returns exactly two hits in source: the
definition (`sections.py:1204`) and its only use inside
`_going_concern_uncertainty_match()` (`sections.py:1233-1265`). **No call site bypasses the
filter.**

### 1.2 Defect (implementation, confirmed)

The raw regex matches the standard phrase **regardless of polarity**. A sentence such as

> "There is **no material uncertainty** related to going concern."

contains `material uncertainty … going concern` and was emitted as
`going_concern_uncertainty = True`, i.e. **K1 TRIGGERED on the opposite of the disclosed
fact**. Probe over four phrasings (all matched by the raw pattern):

| Sentence | Raw regex | Correct reading |
|---|---|---|
| "There is a material uncertainty related to going concern." | match | positive |
| "There is no material uncertainty related to going concern." | match | **negative** |
| "We did not identify any material uncertainty related to going concern." | match | **negative** |
| "No material uncertainty exists that may cast significant doubt … going concern." | match | **negative** |

### 1.3 Correction (implemented)

`sections.py` now routes every scan through `_going_concern_uncertainty_match()`, which:

1. iterates all phrase matches and builds a 120-character **prefix cut at the sentence
   boundary** (`.` / newline / `;`);
2. rejects the match when the prefix matches `_GOING_CONCERN_NEGATION`
   (`there is/are/was/were no|not`, `do/does/did/has/have/had not identify|report|find|note|exist`,
   `no [material] uncertainty`, `without [any] [material] uncertainty`, `none`, trailing `no`);
3. rejects the match when the sentence tail matches `_GOING_CONCERN_POST_NEGATION`
   (`does not exist`, `has not been identified`, `no such`, `no longer`);
4. returns the first surviving match.

The emission remains **positive-only**: a negated or absent statement produces **no
`RawExtraction`**, the canonical field stays `None`, the derived metric is UNKNOWN and K1
cannot be CLEARed or TRIGGERED by that leaf. **A negation never becomes `False`.**

The guards were written as an explicit list rather than a bare `\bno\b` so that an unrelated
negative word in the same sentence ("No doubt, there is a material uncertainty …") does not
suppress a genuine disclosure — pinned by a test.

### 1.4 Evidence status for the two filings

| Filing | Auditor opinion | Going-concern statement | Field | K1 |
|---|---|---|---|---|
| **Jio** (committed RHP) | `unqualified` — examination report pp. 321–324, conclusion p. 324 "…no modification in the underlying audit reports…" | **none located**: no going-concern paragraph; whole-PDF "going concern" occurs once (p. 253, measurement-basis context) | `None` | **UNVERIFIED** |
| **HD Fire** | "unqualified" — *claim only, no RHP inspected* | **not located** — no RHP inspected | `None` | **UNVERIFIED** |

**The contract does not support an evidence-backed negative conclusion here.** An unmodified
opinion says nothing about going-concern material uncertainty (ISA 570 requires a separate
statement when uncertainty exists); the absence of a phrase in the pages scanned is
"no statement found in the inspected document", not "the document establishes no material
uncertainty". A negative-confirmation rule would be a **new governed rule** (it must define
the page coverage, the required auditor language, and the failure mode), not a bug fix.

### 1.5 Measured effect (controlled fixture, not intuition)

Two runs of `evaluate()` on `conftest.minimal_input()` differing only in the flag:

| `going_concern_uncertainty` | Score | K1 | Verdict |
|---|---|---|---|
| `True` | 16.0 (unchanged) | **TRIGGERED** | **AVOID** |
| `None` | 16.0 | **UNVERIFIED** | **INSUFFICIENT_DATA** |

D-1 is a **verdict-integrity** fix: it prevents a false AVOID; it does not move points.

### 1.6 Tests

`tests/test_going_concern_negative_disclosure.py` — **8 passed**:
positive phrase still detected; five negative phrasings not emitted; "going concern basis"
(measurement basis) not emitted; "No doubt, there is a material uncertainty …" still emitted.
`tests/test_auditor_evidence_section.py` (existing positive/absence controls) and the live
Jio pin (`test_jio_evidence_remediation.py::…`) still pass.

---

## 2. D-2 — K5 contingent-liability numerator

### 2.1 Contract, formula, threshold (all unchanged)

* **K5 config:** required `contingent_liab_pct_networth`, `contingent_liab_unquantified`;
  fires when `pct > 50` **or** the unquantified flag is true.
* **Formula:** `contingent liabilities / net worth × 100`, with `net_worth = net_worth_latest`;
  `net worth ≤ 0` ⇒ N/A; a missing numerator or denominator ⇒ UNKNOWN.
* **Schema:** `financials.contingent_liabilities` is `$ref: "$defs/num"` with **no
  description**; `financials.contingent_liabilities_unquantified` is `boolean | null`.
* **Flag derivation:** `derived.py:2252` passes the raw value through; absent or `null` ⇒
  UNKNOWN, never `False`.

### 2.2 What the extractor actually reads

`financial_tables.py::_extract_contingent_liabilities` anchors on a note heading matching
`contingent liabilities (and commitments)?`, then locates a row matching
`claims? (/|and)? disputed liabilit`, reads the period header up to 30 lines above that row,
and takes the **latest 31-March column**. Everything else in the note is outside the numerator.

Coverage probe (synthetic notes with the same header shape; no filing is claimed):

| Note shape | Returned amount | Consequence |
|---|---|---|
| `(I) Contingent Liabilities`: claims 1,000 **+** bank guarantees 5,850 | **1,000** | guarantees silently excluded |
| `(I) Contingent Liabilities`: bank guarantees 5,850 + EPCG 3,143 (no claims row) | **None** | no numerator at all ⇒ K5 UNVERIFIED |
| items + "Total contingent liabilities 8,993" (no claims label) | **None** | a stated total is ignored |

So the extractor supports exactly **one** numerator definition — the claims/disputed row —
and cannot represent a note that itemises guarantees or states its own total. That is an
**implementation coverage limit**, independent of which definition is chosen.

### 2.3 Jio — per-component evidence (primary source, committed RHP p. 405, Note 37)

All amounts ₹ million; columns 30-Jun-2026, 30-Jun-2025, **31-Mar-2026**, 31-Mar-2025, 31-Mar-2024:

| Component | 31-Mar-2026 | Status |
|---|---|---|
| (I) Claims / disputed liabilities against the Group not acknowledged as debts | **15,021** | quantified; accepted as the current numerator |
| (II) Estimated contracts remaining to be executed on capital account, not provided for | 26,198 | quantified; **not** a contingent liability (commitment) |
| Note prose | — | claims "not likely to have any material effect"; demands "likely to be either deleted or substantially reduced"; no provision considered necessary |

Against net worth 3,359,769 (same units): **15,021 / 3,359,769 = 0.45 %**.
Including the capital commitment: **105,410 / 3,359,769 = 3.14 %**.
**Neither crosses 50 %**, so the open question is definitional, not outcome-changing for Jio.

`contingent_liabilities_unquantified` = `None`: zero "unquantif\*" hits in 591 pages, and the
prose quantifies the disclosed exposure. Absence of an unquantified statement is **not**
evidence that every exposure is quantified (a completeness statement is required), so the
leaf stays UNKNOWN and K5 stays UNVERIFIED on that leaf.

### 2.4 HD Fire — components are category-mismatched (unverified amounts)

| Claim (secondary source only) | Amount | Category question |
|---|---|---|
| Bank guarantees, secured on fixed deposits | ₹58.50 cr | a financial guarantee is in the scope of Ind AS 109 and may be **recognised** (a liability), not disclosed as contingent; it is not the claims row |
| Unfulfilled EPCG export obligations | ₹31.43 cr | a contractual **commitment**, not necessarily a contingent liability |
| Sum, if both were the whole population | ₹89.93 cr | 89.93 / 399.87 = **22.49 %** of net worth — below the trigger |

Neither amount is verified (no RHP), and neither is a contingent liability by definition
merely because it was summarised as one. Two quantified lines cannot establish that **all**
exposures are quantified or that none is omitted, so `contingent_liabilities_unquantified`
cannot be set to `False`.

### 2.5 Overlap / anti-double-count

* Jio: sections (I) and (II) are disjoint and no row appears twice; summing them mixes
  categories but does not double count.
* General: a bank guarantee issued against a disputed demand can appear both as a "claim"
  and as a "guarantee"; a note's own stated total, or an explicit section boundary, is the
  only safe anti-double-count device. Any future numerator must prefer a stated total.

### 2.6 The one implementation change made (flag polarity, no numerator change)

`_CL_UNQUANTIFIED` is polarity-blind: "There are **no** unquantified claims" contains
`unquantified` and set the flag to `True`, triggering K5 on a statement of completeness. The
extractor now checks the 80 characters preceding the match, cut at the last sentence
separator, for `no | not | nil | none | without`, and suppresses the flag in that case.

* A **positive** unquantified disclosure still yields `True`.
* A negated one now yields `None` (UNKNOWN) — it is **not** converted to `False`, so K5 stays
  UNVERIFIED rather than being cleared.
* An unrelated negative word inside the 80-character window suppresses the flag to UNKNOWN.
  That direction is deliberate: the cost is a missed trigger (never a false CLEAR), and the
  alternative — raising K5 on a statement of completeness — is the error being fixed.
* No numerator, threshold or criterion meaning changed. Jio and HD Fire are unaffected (no
  "unquantif\*" text in Jio; no HD Fire text at all).

Measured (controlled fixture): flag `True` ⇒ K5 **TRIGGERED**, verdict **AVOID**, score
unchanged 16.0; flag `None` ⇒ K5 **UNVERIFIED**, verdict **INSUFFICIENT_DATA**, 16.0.

### 2.7 Verdict: D-2 is a semantic decision, not an implementation defect

| Option | Numerator | Jio | HD Fire | Assessment |
|---|---|---|---|---|
| **(a) current** | claims / disputed liabilities row only | 15,021 → 0.45 % | no claims row ⇒ UNKNOWN | supported by code and tests, **inconsistent with the K5 label** ("contingent liabilities > 50 % of net worth") and with the field name |
| **(b) total disclosed contingent liabilities** | sum of section (I) rows, or the note's stated total; commitments (II) excluded | same 0.45 % (one row) | depends on the note; BG/EPCG may not be section (I) | aligns implementation with the existing label; **changes extracted values for multi-row notes** ⇒ semantic decision |
| **(c) defined subset incl. commitments** | (I) + capital commitments, etc. | 105,410 → 3.14 % | not computable without the note | mixes commitments into a contingent-liability numerator; needs explicit anti-double-count rules |

**Recommendation (not a decision):** adopt **(b)** — the disclosed total of the contingent
liabilities section, commitments excluded, stated total preferred over summed rows — then
extend the extractor to read the section rather than one label. Rationale: it is the only
option that matches the existing K5 label and the field name without redefining either; it
leaves Jio unchanged; and it is implementable without new semantics **once the numerator is
authorized**. It still would not by itself clear or trigger HD Fire's K5, because the note
structure and completeness are unknown.

**Authorization needed before any numerator change:** approve (a), (b) or (c) explicitly; a
change to (b)/(c) requires a re-extraction review of every filing whose note has more than one
row and a documented re-scoring decision. **No numerator code was changed in this pass.**

---

## 3. D-3 — promoter pre/post holding

### 3.1 Defect and correction

`extract_capital_structure` scanned the shareholding block for a line matching
`Total\s*\(\s*A\s*\)`. That prefix also matches the ICDR summary row
`Total (A)+(B)+(C)`, i.e. **the whole company**, and the fallback then added `Total (B)`
(public) — producing **100 % / 100 %** where the filing states 66.43 % promoter / 33.57 %
public (Jio p. 107; post-issue `[●]`).

Correction (narrow, guard only):

```python
_TOTAL_A_LABEL = re.compile(r"total\s*\(\s*a\s*\)(?!\s*[+(])", re.IGNORECASE)
```

The trailing lookahead rejects `Total (A)+(B)+(C)` (and `Total (A) + …`). **Row assembly and
the A+B arithmetic are unchanged**; that arithmetic is recorded as the separate semantic
question it is (see 3.4).

### 3.2 Live reproduction

| Filing | Before | After |
|---|---|---|
| Jio (p. 107; 66.43 % stated) | 100.0 / 100.0 | **None / None** |
| R.K. Fashion | 99.67 / 72.25 | **99.67 / 72.25** (unchanged) |
| Vishal Nirmiti | 73.42 / 37.51 | **73.42 / 37.51** (unchanged) |

### 3.3 The regression found during implementation, and why the narrow fix was kept

The first attempt truncated row assembly at the next `Total (` row. On R.K. Fashion that made
the parser read the **Reg-31** `Total (A)` line (99.61 %) and drop the `Total (B)` 0.06 %
line ⇒ **99.61 / 72.22** and a failing deterministic-extraction test. The rewrite was
reverted; the guard-only fix restores 99.67 / 72.25 and leaves the category arithmetic intact.
This is the evidence that the narrow correction is the safe one.

### 3.4 Options and measured effects

| Option | Behaviour | Jio | HD Fire claim (85.0 %) | Points |
|---|---|---|---|---|
| **(a) guard only — implemented** | combined summary row never read as promoter | UNKNOWN / UNKNOWN | indeterminate without the RHP | Jio loses **4 earned + 4 available** (D 8 → 4) |
| (b) parse the promoter row explicitly | read the promoter line item, not a category total | 66.43 / 65.0 | 85.0 (claim) | same availability change as (a); larger rewrite |
| (c) dilute pre-issue holding by the issue | 66.43 % × 8,939,030,830 / 9,209,030,830 = **64.48 %** | 64.48 | **85.0** | preserves every recorded band ⇒ no score change |

Option (c) **changes the definition** of the field (pre-issue holding diluted by the offer
rather than the disclosed post-issue holding) and was therefore rejected: it would preserve
scores by construction. Option (a) is implemented because it is the only change that removes a
demonstrably wrong value without choosing a new definition.

**Measured (controlled fixture):** `promoter_post_pct = 100` ⇒ score 17.0, available 23;
`None` ⇒ score 13.0, available 19. **Δ = 4 points.**
**Jio if re-scored under (a):** 37.0 → **33.0**, available 61 → 57, unknown 39 → 43,
Module D 8 → 4. *No Jio record was re-run or rewritten.*

### 3.5 Residual issue (D-3b, open — not fixed)

The post-issue fallback does not verify that the table it reads is the **post-issue** table; a
pre-issue-only table with `Total (A) = 100` and `Total (B) = 0` still yields 100 % post. If
HD Fire's shareholding section has that shape, a re-run would still show 100 % post even after
D-3(a), whereas the arithmetic of a 100 % OFS by two individuals gives **85.0 %**
(26,284,500 of 175,228,782 shares). Fixing this needs the RHP (to see whether a post-issue
table exists and what it states) and is a separate decision; it is recorded, not applied.

### 3.6 Tests

`tests/test_promoter_holding_extraction.py` — **4 tests**:
standalone promoter total extracted (66.43 / 65.0); combined row is not the promoter holding
(⇒ None/None); `Total (A) + Total (B)` summation pinned as a **strict xfail** (the open
semantic question, reason cites D-3 and the RK 99.67 → 99.61 regression); live Jio pin (skips
if the PDF is absent). `tests/test_rk_fashion_reconciliation.py` and
`tests/test_fixture_fallback_isolation.py` pass unchanged.

---

## 4. D-4 — auditor tenure and repeated-EOM defaults

### 4.1 Contract mapping (unchanged)

`derived.py::_auditor_bucket` (formula text unchanged):

| Condition | Bucket | Module D |
|---|---|---|
| opinion `qualified/adverse/disclaimer` | N/A — handled by K1 | 0 |
| `auditor_changed_3y` unknown | **UNKNOWN** | 0 (unavailable) |
| changed true **or** `repeated_eom` true | `unstable_or_repeated_eom` | 0 |
| unqualified **and** reputed true | `clean_reputed` | 2 |
| EOM, or unqualified without reputed | `eom_only` | 1 |
| unqualified but reputed unknown | **UNKNOWN** | 0 |

### 4.2 Defects (implementation, confirmed)

1. `aud_changed_3y = False` was assigned **before** the tenure loop and again inside both
   branches — a **constant** `False`. The tenure regex was effectively decorative.
2. The emitted quote was synthesised: `"Auditor <name> unchanged across audited fiscal
   years"` — text that appears nowhere in the filing (`quote_is_processing=True`).
3. `repeated_eom = False` was emitted whenever an auditor name was found, with the quote
   `"No repeated Emphasis of Matter noted"` — again not in the source, and not even marked as
   a processing quote.

Together these resolved `clean_reputed` (**2/2**) from an unqualified opinion alone, i.e.
missing evidence was converted into a favourable fact.

### 4.3 Correction (implemented)

* `aud_changed_3y = None` unless the **singular** tenure sentence matches
  (`financial year ended March 31, 2026, March 31, 2025 and March 31, 2024 … audited by`, or
  the inverse form). On a match: `False`, the **full source sentence** (via
  `_opinion_sentence`), and the **page actually matched**.
* `repeated_eom = False` **only** when the report contains an explicit negative statement
  (`no | nil | without [any] emphasis of matter`) **and** no positive EOM statement; the quote
  is the verbatim source sentence. Otherwise the field is not emitted (⇒ UNKNOWN).
* No field is emitted on absence; nothing is coerced to `False`.

### 4.4 Measured effects

| Case | Before | After |
|---|---|---|
| Known tenure (fixture) | `clean_reputed` 2/2 | `clean_reputed` 2/2 (unchanged) |
| No tenure text | `False` ⇒ `clean_reputed` 2/2 | `None` ⇒ **UNKNOWN** (−2 points) |
| No EOM text | `False` | `None` (no point change on its own) |
| R.K. Fashion | `auditor_changed_3y = False` asserted | `None` — stale expectation updated; auditor criterion was already UNKNOWN ⇒ **no score change** |
| Jio | no auditor name matched ⇒ field never emitted | unchanged — auditor criterion already UNKNOWN ⇒ **no score change** |

**Controlled fixture:** unqualified + reputed, `changed=False` ⇒ 18.0 (available 25);
`changed=None` ⇒ 16.0 (available 23). **Δ = 2 points** on filings where the constant used to
award `clean_reputed`.

### 4.5 Capability gap (documented, not fabricated)

There is **no `True` path** for `repeated_eom`: detecting a repeated EOM requires comparing
two years' auditors' reports, which the extractor does not do. A positive EOM statement
therefore leaves the field UNKNOWN. This is recorded as a capability limit, not an error.

### 4.6 Tests

`tests/test_auditor_tenure_defaults.py` — **9 passed**: name/reputed extraction; tenure not
asserted without tenure language; repeated EOM not asserted without evidence; tenure language
⇒ `False` + verbatim quote; explicit negative EOM recorded verbatim; positive EOM does not
assert repeated EOM; every emitted quote is verbatim; unknown tenure ⇒ `auditor_bucket`
UNKNOWN; known tenure ⇒ `clean_reputed`.

---

## 5. Phase 5 — cross-impact table

| ID | Defect | Root cause | Fix under the existing contract? | Measured score impact | Verdict impact | Governance needed? | Tests |
|---|---|---|---|---|---|---|---|
| **D-1** | GC phrase matched regardless of polarity ⇒ false K1 trigger | polarity-blind regex, no negation filter | **Yes** — positive-only emission is already the contract; rejecting negations restores it | 0 points | false **AVOID** prevented; K1 stays UNVERIFIED | No | 8 new + existing controls |
| **D-2 flag** | "no unquantified claims" set the flag true | polarity-blind unquantified regex | **Yes** — flag must not be raised by a statement of completeness | 0 points | false **AVOID** prevented; K5 stays UNVERIFIED | No | 9 (1 new) |
| **D-2 numerator** | numerator is one label, not the disclosed total | no defined numerator; schema has no description | **No** — choosing the population changes extracted values | 0 for Jio (both 0.45 % vs 3.14 % < 50 %) | none for Jio; undeterminable for HD Fire | **Yes — open decision** | 9 extraction tests pin current behaviour |
| **D-3** | combined `Total (A)+(B)+(C)` read as promoter total | prefix regex + A+B addition | **Partly** — the guard removes the wrong row; the A+B definition question stays open | Jio **−4 points** (37 → 33) if re-scored; RK/Vishal 0 | Jio D 8 → 4; K4 stays CLEAR | **Yes** for the A+B definition (xfail pin) | 4 (1 strict xfail) |
| **D-3b** | post value may be read from a pre-issue table | no table-scope check | **No** — needs a defined rule + the RHP | undeterminable | possibly HD Fire only | **Yes — open** | none (documented) |
| **D-4** | constant `False` + synthesised quotes ⇒ free `clean_reputed` | unconditional assignment | **Yes** — the bucket already treats unknown as UNKNOWN | up to **−2 points** where the constant applied; Jio/RK 0 | none observed on live filings | No | 9 |

**Live filing matrix after the fixes (executed):**

| Filing | Promoter pre/post | Auditor | K1 | K5 |
|---|---|---|---|---|
| Jio | None / None (was 100/100) | UNKNOWN (no name matched) | UNVERIFIED | UNVERIFIED |
| R.K. Fashion | 99.67 / 72.25 (unchanged) | UNKNOWN (opinion not extracted) | — | — |
| Vishal Nirmiti | 73.42 / 37.51 (unchanged) | unchanged | — | — |

No historical evaluation record was edited, re-run or re-hashed. The Jio 37.0 record remains
the record; 33.0 is the arithmetic consequence of D-3(a) **if** it were re-scored.

---

## 6. Phase 6 — decision records

Each record is separate. A recommendation is **not** an accepted decision.

### D-1 — going-concern negative confirmation

* **Exact question:** may K1's `going_concern_uncertainty` be set to `False` (or CLEAR be
  concluded) when an unmodified audit opinion is present and no going-concern paragraph is
  found?
* **Current rule:** K1 requires the flag; `True` triggers; absent ⇒ UNKNOWN ⇒ K1 UNVERIFIED.
* **Established evidence:** Jio — unqualified opinion, no going-concern paragraph (one
  incidental "going concern" at p. 253); HD Fire — unqualified *claim*, no RHP.
* **Options:** (a) keep UNKNOWN (status quo; implemented polarity fix) — honest, but K1 can
  never be CLEAR without a positive statement; (b) governed negative-confirmation rule
  (define coverage + required language) — would let most unqualified filings clear K1, but
  asserts a conclusion from absence and needs a precision/recall study.
* **Impact:** none on scores; (b) would change K1 states (and potentially verdicts) across
  all filings — a **semantic** change.
* **Arena preference:** (a) until (b) is specified and authorized.
* **Authorization scope if (b) is wanted:** new rule text, page-coverage definition,
  false-negative analysis, config/spec version bump, re-score decision for existing records.
* **Status:** implementation polarity fixed; semantic question **open** (operator).

### D-2 — K5 numerator

* **Exact question:** does `financials.contingent_liabilities` mean the claims/disputed row,
  the disclosed contingent-liability total, or a defined subset (incl./excl. capital
  commitments)?
* **Current rule:** claims row only (code), while the K5 label and field name say
  "contingent liabilities"; schema has no description.
* **Established evidence:** Jio Note 37 — claims 15,021 (0.45 %); commitments 26,198 (3.14 %
  combined); HD Fire — BG 58.50 + EPCG 31.43 = 22.49 % (unverified, category-mismatched).
* **Options:** (a) claims-only; (b) total section (I), commitments excluded; (c) defined
  subset incl. commitments.
* **Impact:** no Jio outcome change; changes extracted values for multi-row notes; would
  require re-extraction review.
* **Arena preference:** (b) with stated-total preference; (a) remains in force until
  authorized.
* **Status:** **open decision**; only the flag-polarity fix was implemented.

### D-3 — promoter holding definition

* **Exact question:** is `promoter_post_pct` the disclosed post-issue promoter total, or the
  pre-issue total diluted by the offer? And must `Total (A)` exclude the combined summary row?
* **Current rule:** disclosed value; combined row now excluded (implemented); post fallback
  still adds `Total (B)` to `Total (A)`.
* **Established evidence:** Jio 66.43 % / 33.57 % (p. 107); RK 99.67 / 72.25; the
  `(A)+(B)` addition is arithmetically wrong for a promoter figure when B is public.
* **Options:** (a) guard only (implemented); (b) explicit promoter-row parse; (c) dilution
  (64.48 % / 85.0 %).
* **Impact:** (a)/(b) −4 Jio points if re-scored; (c) preserves scores by construction.
* **Arena preference:** (a) as the defect fix; (b) only as part of a defined re-extraction;
  (c) rejected.
* **Open sub-question:** whether the post value may be read from a pre-issue table (D-3b).
* **Status:** (a) **implemented**; definition and D-3b **open**.

### D-4 — auditor tenure / repeated EOM

* **Exact question:** what evidence establishes "same auditor for three years" and "no
  repeated EOM"?
* **Current rule:** tenure `False` only on a positive three-year sentence; repeated EOM
  `False` only on an explicit negative statement; otherwise UNKNOWN (implemented).
* **Established evidence:** RK has no tenure sentence ⇒ UNKNOWN (score unchanged); Jio has no
  name/tenure/EOM evidence ⇒ UNKNOWN; the old constants were synthesised, not evidence.
* **Options:** (a) unknown unless matched (implemented); (b) record the constants as governed
  assumptions with a source citation requirement.
* **Impact:** up to −2 points where the constant applied; no live filing changed.
* **Arena preference:** (a).
* **Status:** **implemented**; repeated-EOM `True` detection remains a capability gap.

---

## 7. Tests executed in this pass

| Command | Result |
|---|---|
| `pytest tests/test_contingent_liabilities_extraction.py -q` | **9 passed** (29.5 s) |
| `pytest tests/test_promoter_holding_extraction.py tests/test_auditor_tenure_defaults.py tests/test_going_concern_negative_disclosure.py tests/test_contingent_liabilities_extraction.py tests/test_auditor_evidence_section.py tests/test_rk_fashion_reconciliation.py tests/test_fixture_fallback_isolation.py tests/test_jio_evidence_remediation.py tests/test_overlays_knockouts.py tests/test_core_semantics.py -q` | **106 passed, 1 xfailed** (216.37 s) |
| `pytest tests -q` (full backend) | see §7.1 |
| the four touched test files, re-run on the final tree after the docstring edits | **29 passed, 1 xfailed** (32.91 s) |

### 7.1 Full suite

`PYTHONPATH=engine:tests ./.venv/bin/python -m pytest tests -q` (whole repository, executed on
the final tree with the new engine code and tests):

| Run | Result |
|---|---|
| Baseline at `ebd177c` | 1161 passed, 5 xfailed, 38 warnings, 1618.22 s |
| **This pass (final tree)** | **1179 passed, 1 xfailed, 38 warnings, 1542.57 s** |

The delta is exactly the tests added or converted by this pass: **+18 passing tests** (8
going-concern polarity, 1 negated unquantified flag, 7 auditor-tenure controls that replaced 2
strict xfails, 2 promoter controls that replaced 2 strict xfails). The single remaining xfail
is the deliberate pin on the **open** D-3 `Total (A) + Total (B)` definition.

Golden fixture hash and `config/`, `schema/`, `fixtures/` diffs are checked at publication
(§8); no golden, config or schema file was modified by this pass.

---

## 8. Publication record

* **Implementation commit:** `e2ce2c22b638c2eef7be315d2e9f019904baf8ff` on
  `arena/ae4d04e8-ipo-screening-engine`, pushed and remote-verified (`git ls-remote origin
  refs/heads/arena/ae4d04e8-ipo-screening-engine` returned the same SHA). **9 files changed,
  953 insertions, 139 deletions:** this document, the tracker, `sections.py`,
  `financial_tables.py`, `test_promoter_holding_extraction.py`,
  `test_auditor_tenure_defaults.py`, `test_going_concern_negative_disclosure.py` (new),
  `test_contingent_liabilities_extraction.py`, `test_rk_fashion_reconciliation.py`.
* **Tests at that commit (executed):** full backend **1179 passed, 1 xfailed**, 38 warnings,
  1542.57 s; focused 10-file battery **106 passed, 1 xfailed**, 216.37 s; contingent-liability
  file **9 passed**, 29.49 s.
* **Non-changes:** `git status` after the commit shows no modification under `config/`,
  `schema/` or `fixtures/`; golden hash `e84f8bc0…` asserted unchanged by the golden tests
  inside the full suite; no historical evaluation rewritten or re-hashed.
* **PR #6:** `OPEN`, `mergedAt: null`, head `arena/5dd3fe52-ipo-screening-engine` @
  `e05c0efbca1ecb3024e52da73a22e180ea171118`, base `arena/573e69a4-ipo-screening-engine` —
  neither moved nor merged.
* **`main`:** `01ba66c12ca1195fd7acbd287c3e39a019808094`, untouched.
* **CI:** no hosted workflows configured (`.github/workflows` absent; Actions workflow count 0).
* **Remote source check:** 17 branches enumerated this pass; every tree searched; no HD Fire
  RHP/PDF and no evaluation record in any branch.
* **Remaining Windows-only acceptance:** the HD Fire RHP, the `…551a7eab` evaluation record,
  its penalty rows and canonical issue block from the Windows store, and a re-run at
  `e2ce2c2`. No Windows artefact is claimed as inspected.

---

## 9. What is fixed, what is open

**Fixed (implementation correctness, tested):**

1. D-1 polarity filter for going-concern uncertainty (positive-only emission preserved).
2. D-2 unquantified-flag polarity (a statement of completeness no longer triggers K5).
3. D-3 combined `Total (A)+(B)+(C)` no longer read as the promoter total.
4. D-4 auditor tenure / repeated-EOM defaults no longer synthesised.

**Open (semantic or evidence-bound; no code change without authorization):**

1. D-1 negative-confirmation rule (may an unmodified opinion + absent paragraph clear K1?).
2. D-2 numerator definition (claims-only vs disclosed total vs defined subset).
3. D-3 A+B definition (strict-xfail pin) and D-3b post-table scope.
4. D-4 repeated-EOM `True` detection (capability gap).
5. HD Fire: no RHP, no evaluation record, no Windows store access — every HD Fire value
   remains a documented claim; 7/100 is unchanged and arithmetically consistent.
