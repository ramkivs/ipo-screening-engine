# A34 — Regulation 17(1)(c): does the institutional carve-out establish an *early unlock* of large pre-IPO holders?

- **Decision ID:** A34
- **Title:** what `capital_structure.large_holders_unlocked_early` may be set from — a category carve-out, or evidence of an actual early release
- **Record type:** **DECISION RECORD — APPROVED (Alternative B) and IMPLEMENTED.**
  The investigation text below is retained as the evidence base. §0 records the
  decision, the implemented change and its governance boundary. Per
  `handoff/decisions/CONVENTION.md` rule 4, the approval is distinguished from
  v1.5 specification text; rule 5 is respected because the specification is not
  amended here.
- **Decision status:** **APPROVED 2026-10-27 — Alternative B.**
  A category-specific institutional lock-in carve-out alone does **not**
  establish an early unlock. **Implemented in this branch.**
- **Decision authority:** RAMKI.
- **Date:** 2026-10-27 (Asia/Calcutta); no decision time is asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/342ccacc-ipo-screening-engine`, from `main`
  `69a9ff9d77c9886a1b30c31ed327d5a9d747a1a7`.
- **Scope:** the semantics of `capital_structure.large_holders_unlocked_early` — its
  reader (`engine/ipo_screening/extraction/sections.py::extract_capital_structure`), its
  consumer (`engine/ipo_screening/derived.py::_lockin_bucket`), the C `lockin` criterion,
  and the documentation that describes both readings.
- **Out of scope and unchanged:** every weight, threshold, penalty, band and knockout;
  `config/ipo-config.v1.5.0.json` and `v1.6.0`; `schema/`; the frozen-core pin on
  `engine/ipo_screening/derived.py`; `canonical_input.py`; the builder.
- **In scope and changed by the approved decision:** the PR #13 reader
  (commit `cac095d`) in `engine/ipo_screening/extraction/sections.py` — the
  carve-out rule is replaced by an evidenced-early-release rule (§0).

---

## 0. Approved decision and implementation (2026-10-27)

**Decision (RAMKI, via the governing instruction for the resumed A33/A34
execution):** **Alternative B is approved.** A category-specific institutional
lock-in carve-out alone does **not** establish an early unlock.
`capital_structure.large_holders_unlocked_early` may be set only from evidence
of an **actual early release** of large pre-IPO holders. Where the filing
discloses only the Regulation 17(1)(c) carve-out, the field stays `null` and C
`lockin` stays **UNKNOWN**.

### 0.1 What was implemented

`engine/ipo_screening/extraction/sections.py::extract_capital_structure`:

- the PR #13 carve-out regex (institutional category + purchase-anchored
  lock-in) was **removed**; a carve-out no longer emits any extraction;
- a fail-closed, sentence-level rule now sets the flag `True` only where one
  sentence contains (a) a named large / pre-IPO / institutional holder group,
  (b) a release act, (c) a lock-in context, and (d) explicit early /
  before-expiry timing. The matched sentence becomes the verbatim quotation
  with its page;
- pledge release, ordinary transferability, a release on normal expiry, and
  hypothetical, conditional or negated language all stay **UNKNOWN**. No
  favourable `False` is inferred either (A32's rule is preserved);
- no weight, threshold, penalty, band, knockout, config, schema,
  `derived.py`, builder or historical evaluation record was changed.

### 0.2 Semantic boundary, verified

`tests/test_lockin_institutional_carveout.py` (28 tests),
`tests/test_reading_defects_20261026.py`,
`tests/test_paras_evidence_regression.py` and
`tests/test_a34_issuer_reproduction_20261027.py` pin: the carve-out alone does
not set the flag; an evidenced early release is handled by the governing
criterion (`weak`, SCORED 0); insufficient/ambiguous evidence stays UNKNOWN;
unrelated pledge/transferability language does not trigger; and genuine
positive cases remain detectable.

**Corpus limitation.** A full-text scan of the five real filings examined
(Paras 651 pp., Jio 591, Moneyview 537, Vishal Nirmiti 551, R.K. Fashion 496)
found **zero** sentences evidencing an early release. That is a limitation of
this corpus, **not** proof that early releases never occur. Genuine positive
cases are therefore retained as labelled synthetic fixtures in
`tests/test_lockin_institutional_carveout.py::EVIDENCED_EARLY_RELEASES` and in
the reading-defects module. No real-filing positive is claimed.

### 0.3 Reconciliation with A32 — genuine governance-recording requirement

A32 (`A32-builder-defaults-evidence-or-unknown.md`, status
`READY FOR RAMKI RATIFICATION (NOT RATIFIED)`) removed the favourable `False`
default for this field and, in §6.2, explicitly left open the policy question
"whether an engine may ever establish [this field] from a filing at all".
**A34 Alternative B is the criterion owner's approved answer to that policy
question for this field**: an engine may establish it, but only from an
evidenced release, never from a structurally different lock-in anchor.

This does **not** retroactively ratify A32. The genuine governance-recording
requirement that remains is:

1. **Record A32 as still `NOT RATIFIED`** wherever this decision is cited, and
   keep its separate ratification as an open action for RAMKI. A34's approval is
   an approval of the A34 semantic question, not an assertion that every
   artefact covered by A32 has been ratified.
2. **Do not treat A34 Alternative B as an unapproved proposal.** It is approved
   and implemented; documents that still call it PROPOSED are historical and
   are superseded by this §0.
3. **Alternative C remains a separate schema decision.** If the carve-out
   structure itself is to be recorded (category + "six months from purchase"),
   that needs an additive structured field, a schema/canonical-input migration
   and its own approval. It was not implemented here.
4. The v1.5 phrase "no early unlock of large holders" is now applied as an
   **evidenced** test rather than a structural test. Per CONVENTION rule 5 this
   decision record documents the resolution of an ambiguity; it does not claim
   the v1.5 specification text was changed. Amending that text, if wanted, is a
   separate specification action.

### 0.4 Measured issuer effect

See `docs/investigation/A33-A34-ISSUER-REPRODUCTION-2026-10-27.md` for the full
before/after tables, quotes and page provenance. Summary: neither final score
nor verdict nor knockout state changes (Jio 37.0 / `AVOID` / K2 TRIGGERED;
Paras 13.0 / `AVOID` / K5 TRIGGERED). `lockin` moves SCORED 0 `weak` →
**UNKNOWN** on both; completeness drops one point (Jio 63.0% → **62.0%**,
Paras 44.21% → **43.16%**) and the upper bound rises one point. A33's
`kmp_exits_2y` / `board_kmp` values are unchanged (Jio 6, Paras 4; both
`high_churn`).

---

## 1. The question

`_lockin_bucket` is `intact` only when `promoter_lockin_in_place` is true **and**
`large_holders_unlocked_early` is false; with the second field `null` the metric is
UNKNOWN and C `lockin` is unscored. On the strict real-filing path the builder never sets
that field, so it is set only if a reader emits it.

PR #13 (commit `cac095d`) added such a reader. It sets the flag when a filing discloses
**both** an institutional/VC holder category **and** a lock-in anchored to the **date of
purchase** rather than to the general six-months-from-Allotment lock-in. That is the
Regulation 17(1)(c) carve-out.

> Does the carve-out establish that large pre-IPO holders are unlocked **early** — so the
> flag may be set — or does it establish only a *different anchor* for the same six-month
> minimum, whose effect on the Offer date depends on each holder's purchase date, which
> the filing does not state?

## 2. The text, quoted and page-verified (independently re-extracted this pass)

**Jio Platforms**, printed p. 105 (PDF index 104), `evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`:

> In terms of Regulation 17 (1)(c) of the SEBI ICDR Regulations, equity shares held by a
> VCF or Category I AIF or Category II AIF or FVCI shall not be locked-in for a period of
> six months from the date of Allotment, provided that such equity shares shall be locked
> in for a period of at least six months from the date of purchase by such shareholders.

**Paras Healthcare**, printed p. 117 (PDF index 116),
`evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf`:

> …will be locked-in for a period of six months from the date of Allotment, except for …
> (iii) the Equity Shares held by a VCF or a Category I AIF or a Category II AIF or a
> FVCI, provided that such Equity Shares will be locked-in for a period of at least six
> months from the date of purchase by the VCF or Category I AIF or Category II AIF or
> FVCI shareholders.

Both quotes are verbatim and both page attributions are correct. The reader's provenance
is sound; the open question is purely about what the text *means*.

## 3. What the text establishes, and what it does not

The carve-out does three things:

1. it **removes** the general Regulation 17(1) lock-in (six months from Allotment) for
   shares held by the named categories;
2. it **imposes** instead a *minimum* lock-in of six months from **purchase**;
3. it says **nothing** about when those holders purchased.

Whether the result is an *early* unlock therefore depends on a fact the filing does not
state. A holder that purchased more than six months before Allotment is free at Allotment
(earlier than the general rule); a holder that purchased shortly before this issue is
locked until purchase + six months, which can be *later* than Allotment + six months.
One filing's carve-out can therefore produce an early release, a same-time release, or a
later release.

What the filing does state, on its face, is a **different commencement date and a
minimum** — which is what the disposition report's own §6.3(ii) called "arguably not an
early unlock".

## 4. The governing contracts, and the authority boundary

| Source | Wording / status |
|---|---|
| `handoff/reference/Claude_IPO Screening Engine v 1.3 — Specification.md` line 94 | "Lock-in \| 1 \| Promoter lock-in intact, **no early unlock of large holders** = 1; otherwise 0" |
| `config/ipo-config.v1.5.0.json` → `lockin_bucket` | "intact: promoter lock-in in place and **no early unlock of large pre-IPO holders**; else weak" |
| `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §4.1 | lists "lock-in" as a required input; defines no criterion row |
| **A32** (`handoff/decisions/A32-builder-defaults-evidence-or-unknown.md`) §6.2 | "`large_holders_unlocked_early` and `discounted_allotments_18m_before_drhp` have **no reader**. Whether an engine may ever establish them from a filing at all — for example from a lock-in table that lists which holders are released early — is a **policy question** (A21/A25 family), not an extractor improvement." |
| **A32** status and §7 | "**READY FOR RAMKI RATIFICATION (NOT RATIFIED)**"; "Granted for this branch only … **no authority is asserted over any scoring artefact.** Ratification by RAMKI is requested." |

The criterion's *concept* ("no early unlock of large holders") is in the specification.
What is **not** settled anywhere is whether a Regulation 17(1)(c) carve-out is evidence of
that concept, or evidence of something else that happens to touch the same shares. A32
expressly leaves the question open and expressly withholds authority over the artefact.

## 5. Measured effect of the two readings

| Issuer | Field today | If the carve-out is *not* an early unlock |
|---|---|---|
| Jio Platforms | `large_holders_unlocked_early = true` → C `lockin` **SCORED 0** (`weak`) | flag unset → `null` → C `lockin` **UNKNOWN** (1 point moves from scored-0 to available) |
| Paras Healthcare | `large_holders_unlocked_early = true` → C `lockin` **SCORED 0** (`weak`) | flag unset → `null` → C `lockin` **UNKNOWN** |

No weight, boundary or threshold moves either way; the effect is on completeness and on
whether the criterion is scored at all. That is precisely why the decision belongs to the
criterion's owner rather than to the extractor.

## 6. Recommendation

**A category carve-out alone must not set the flag.** `large_holders_unlocked_early`
should be set only where the filing evidences an **actual early release** — for example a
dated lock-in table that lists which holders are released and when, or an explicit
statement that named holders' shares are released before the general lock-in expires.
Where the filing discloses only the Regulation 17(1)(c) carve-out, the field must stay
`null` and C `lockin` must stay **UNKNOWN**.

Rationale:

1. The instruction that governs this work is explicit: **do not infer that an
   institutional carve-out automatically establishes an early unlock.** The carve-out is
   a *minimum* measured from purchase; the early release is a *consequence* that depends
   on a purchase date the filing does not print.
2. Setting the flag from the carve-out asserts a fact the filing does not state, in the
   direction that *costs* the issuer a point. A32's rule is that missing evidence is
   UNKNOWN, never a finding in either direction; a carve-out is not evidence about the
   holders' actual release dates.
3. An UNKNOWN is honest and recoverable: the point stays available and the gap is
   visible. A wrongly-set flag is not recoverable from the record, because the record
   then carries a `true` with a quotation that does not say what the field claims.
4. The reader's own fail-closed boundaries already accept this principle elsewhere: it
   refuses to set the flag on a category mention alone, on an Allotment-anchored lock-in,
   or on a longer purchase-anchored lock-in. Refusing it on the carve-out alone is the
   same principle applied to the one case where the temptation is greatest.

**Follow-up (recommended, separate decision):** if the intent is to capture the
Regulation 17(1)(c) structure, the honest representation is not a boolean. It is a
separate, additive field recording that the carve-out exists and what it anchors to
(category + "six months from purchase") — a fact the filing does state — leaving
`large_holders_unlocked_early` to be set only by evidence of a release. That is a schema
and canonical-input change and is a separate decision.

## 7. Alternatives considered

* **A. Carve-out alone sets the flag (status quo, PR #13).** Retained unchanged pending
  this decision, per the instruction to preserve prior work, but recorded here as
  resting on an unratified policy question (A32 §6.2) and on an inference the filing
  does not support. **Rejected by the approved decision (§0).**
* **B. Carve-out alone never sets the flag (recommended).** See §6. Effect measured in §5.
  **APPROVED 2026-10-27 and implemented (§0).**
* **C. Add a separate structured field for the carve-out**, leaving the boolean for
  evidenced releases only. Most informative; needs a schema decision and a
  canonical-input/`field_map` migration.
* **D. Require the purchase date** before setting the flag. Rejected as a reader rule:
  the filing does not print it, so the flag would be unreachable and the criterion would
  be structurally UNKNOWN — the outcome A32 already documents for this field.

## 8. Consequences and constraints (historical investigation text, superseded by §0)

The investigation as first written changed no code, schema, config, test
expectation or historical record: the PR #13 reader (`cac095d`) and its 17-test
matrix were preserved pending RAMKI's decision. That preservation ended with
the approval. **After §0:**

* the PR #13 carve-out reader is corrected and its test matrix is rewritten as
  the 28-test A34 semantic-boundary suite;
* `docs/investigation/LOCKIN-INSTITUTIONAL-CARVEOUT-GENERALITY-2026-10-27.md`
  and `docs/investigation/PARAS-UNKNOWN-TRIAGE-2026-10-27.md` are revised to
  state the approved evidenced-release rule and to label the earlier
  carve-out-based results as pre-A34 baselines;
* the Jio disposition, consolidated disposition and authoritative tracker are
  updated with the before/after issuer results;
* still unchanged: no weight, boundary, threshold, penalty, knockout, config,
  schema, `derived.py`, builder, frozen-core pin or historical evaluation
  record.

## 9. Remaining dependencies (updated 2026-10-27)

1. **RESOLVED.** RAMKI approved Alternative B on 2026-10-27 (§0).
2. **OPEN — genuine governance-recording requirement.** Ratification of A32 is
   still outstanding (`NOT RATIFIED`). A34's approval does not ratify it; see
   §0.3. This must remain visible in the tracker, not be silently absorbed.
3. **RESOLVED for this engine, not for the specification text.** The phrase "no
   early unlock of large holders" is applied as an *evidenced* test. Amending
   the v1.5 / v1.3 specification wording, if desired, is a separate
   specification action (CONVENTION rule 5).
4. **OPEN — separate decision.** Alternative C's additive structured carve-out
   field (§6 follow-up). No schema change was made.
5. **OPEN — corpus limitation.** No real filing in the five examined evidences
   an early release, so the positive cases in the regression suite are
   synthetic. This is not evidence that early releases never occur.

## 10. Implementation authority (updated 2026-10-27)

**Granted and exercised, within a narrow boundary.** Authority is granted for
the reader change described in §0.1 and its regression tests / documentation
only. No authority is granted or claimed for `_lockin_bucket`, the C `lockin`
criterion definition beyond applying the approved evidenced reading, any
scoring artefact, any schema/config change, or any retrospective edit to a
historical evaluation record. The original "not granted" status applied to the
unapproved investigation and is superseded by the approved decision.
