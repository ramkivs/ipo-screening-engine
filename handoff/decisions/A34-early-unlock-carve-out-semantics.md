# A34 — Regulation 17(1)(c): does the institutional carve-out establish an *early unlock* of large pre-IPO holders?

- **Decision ID:** A34
- **Title:** what `capital_structure.large_holders_unlocked_early` may be set from — a category carve-out, or evidence of an actual early release
- **Record type:** **OPEN DECISION INVESTIGATION.** No decision is recorded and no code
  change is made or authorized by this record. Per `handoff/decisions/CONVENTION.md`
  rules 4 and 6, this is an investigation of an ambiguity, with a recommendation; it is
  not an approval of that recommendation and it grants no implementation authority.
- **Decision status:** **PROPOSED / UNRESOLVED (not implemented).**
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
  `engine/ipo_screening/derived.py`; the reader added by PR #13 (commit `cac095d`), which
  is **preserved unchanged**.

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
  does not support.
* **B. Carve-out alone never sets the flag (recommended).** See §6. Effect measured in §5.
* **C. Add a separate structured field for the carve-out**, leaving the boolean for
  evidenced releases only. Most informative; needs a schema decision and a
  canonical-input/`field_map` migration.
* **D. Require the purchase date** before setting the flag. Rejected as a reader rule:
  the filing does not print it, so the flag would be unreachable and the criterion would
  be structurally UNKNOWN — the outcome A32 already documents for this field.

## 8. Consequences and constraints

* No code, schema, config, test expectation or historical record is changed by this
  record. The reader added by PR #13 (`cac095d`) and its 17-test matrix
  (`tests/test_lockin_institutional_carveout.py`) are preserved.
* `docs/investigation/LOCKIN-INSTITUTIONAL-CARVEOUT-GENERALITY-2026-10-27.md` §2 and
  `docs/investigation/PARAS-UNKNOWN-TRIAGE-2026-10-27.md` §3 present the inference as
  established ("A holder that purchased before the Offer is therefore free at Allotment";
  "Paras does disclose the early unlock"). Both are corrected to state that the carve-out
  is a different anchor whose effect on the Offer date is not disclosed, and both point
  at this record.
* No weight, boundary, threshold, penalty or knockout is touched by any of the above.

## 9. Unresolved dependencies

1. **RAMKI's decision** on §1. Recommended answer: alternative B.
2. **Ratification of A32**, which this question is part of and which is still
   `NOT RATIFIED`.
3. Whether the specification's phrase "no early unlock of large holders" is meant to be
   read as a *structural* test (the carve-out) or an *evidenced* test (an actual release).
   That is a criterion-definition question and is not this record's authority to settle.

## 10. Implementation authority

**Not granted.** This record is an investigation with a recommendation. No change to the
reader, to `_lockin_bucket`, to the C `lockin` criterion or to any documentation beyond
the corrections named in §8 is authorized by it.
