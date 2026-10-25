# A17 — GMP Cutoff, Maximum Age and Trend Labels

- **Decision ID:** A17 (sub-decisions A17-1, A17-2, A17-3)
- **Title:** GMP observation eligibility cutoff, maximum age, and trend-label semantics
- **Decision status:** RAMKI-APPROVED PRODUCT POLICY. These are user-approved decisions, not Arena recommendations.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-15 (Asia/Calcutta)
- **Authorization basis:** Ramki's explicit approval of the three decisions quoted below in the 2026-10-15 instruction "Record approved GMP policy decisions and complete focused convergence". No decision time is supplied or asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** fixed session branch `arena/573e69a4-ipo-screening-engine` at remotely verified commit `9e0e4ed562dd49a260482806afc92e7ef98d8a67`.
- **Scope:** Time eligibility, maximum age and trend-label meaning for a GMP observation. Source selection and source qualification are out of scope.
- **Implementation authority:** GRANTED for the narrow enforcement listed in "Implementation" below, by the same instruction and within A16's personal-use scope. Nothing else is authorized.
- **Publication status:** recorded in the tracker's A17 section. This record does not cite its own commit.

The three sub-decisions are recorded together because A17-2's age is measured from A17-1's cutoff, and all three were approved in one instruction. Each is identified separately below.

## Approved decisions

### A17-1 — GMP cutoff and timestamp eligibility

> The evaluation timestamp defined by the applicable v1.5 specification is the GMP eligibility cutoff. A GMP observation whose source timestamp is later than the evaluation timestamp is ineligible. The existing one-hour future-timestamp allowance must not override this rule. Do not silently substitute bid-close time or invent another cutoff. Do not invent missing source timestamps or timezones. Where eligibility cannot be established, fail closed.

### A17-2 — Maximum age

> Retain the existing 24-hour maximum-age threshold as the initial GMP freshness policy. Apply it relative to the evaluation timestamp and consistently with PR-1. Missing, invalid, future-dated, or over-age timestamps must not qualify the source observation. Reuse the existing versioned configuration and freshness mechanisms where possible. Do not introduce a second competing threshold or unnecessary configuration changes.

### A17-3 — Trend semantics

> Use publisher-supplied trend labels only. Do not derive trend from GMP history, percentage movement, issue price, or the superseded v1.3 reference definition. If the publisher does not supply a trend label that can be mapped unambiguously to the existing accepted v1.5 labels, trend remains unknown/unqualified. Do not infer a label from price movement. Preserve existing schema labels and scoring semantics.

**Naming note.** The approval instruction labels these PR-1, PR-2 and PR-3. A17-1 and A17-2 adopt the proposals PR-1 and PR-2 drafted in [`docs/investigation/A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md`](../../docs/investigation/A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md) §8, to the extent of the approved text above. **A17-3 is not that record's PR-3** (artifact and hash), which remains unadopted.

## Relationship to v1.5 and existing decisions

- **v1.5 requirement, not changed:** Final is "Generated at a defined evaluation timestamp on/after closing" and freezes the GMP snapshot (spec v1.5 §19). Market values carry an as-of time, timezone and source (§4.6, §13).
- **Ambiguities A17 resolves:** v1.5 states neither a GMP cutoff, a GMP maximum age, nor any meaning for the `market.gmp.trend` labels. A17 is a project-level resolution of those ambiguities. It does not amend v1.5 or present these rules as v1.5 text.
- **A8 (GMP):** A17 settles the GMP cutoff and maximum-age items that A8-G left open. The source-specific remainder stays open (see "Unresolved dependencies").
- **A8 principles respected:** A17-1 does not substitute a scheduled event for an actual one and invents no cutoff (A8 l.15). It does not replace source time with application time (A8-G l.39). A17-2 re-adopts an existing configured value rather than inventing an interval.
- **A9:** unchanged. A17 eligibility is not source qualification. The A9 gate still withholds `FINAL` for every present GMP observation (`SOURCE_UNQUALIFIED`) and for a missing one (`MISSING`).
- **A16:** unchanged. A16's personal-use scope covers the routine implementation and testing below.

## Implementation (narrow, required)

`engine/ipo_screening/snapshots.py` and `derived.py` are hash-pinned frozen-core files (`FROZEN_CORE_HASHES`, `post_listing/v16_implementation.py`). Neither is modified, and `verify_frozen_core()` still passes.

| # | Change | Why it was necessary |
|---|---|---|
| 1 | **New `engine/ipo_screening/gmp_policy.py`** (`apply_gmp_cutoff`), called once in `pipeline.py` right after `build_market_snapshot`. It demotes a FRESH GMP block to STALE in two cases:<br>• its timestamp is after the evaluation timestamp;<br>• its timestamp has no explicit UTC offset, or the evaluation time has no timezone.<br>It never promotes a block and never changes another block. | **A17-1.** The frozen builder accepts an `as_of` up to 1 h after the evaluation time as FRESH (`snapshots.py` l.460).<br>`canonical.parse_datetime` assumes UTC for an offset-less timestamp (`canonical.py` l.421–424).<br>Schema `format: date-time` is not enforced, because the optional `rfc3339-validator` is not installed, so offset-less and malformed strings reach the snapshot.<br>Measured before the change, with evaluation at 12:00Z: +1 s, +30 min, +59 min, IST +1 s and an offset-less stamp were all FRESH and scored `gmp_trend`. |
| 2 | **`connectors/interfaces.py`:**<br>• new optional `FreshnessPolicy.require_explicit_offset` (default `False`, so existing policies are unchanged);<br>• new `GMP_FRESHNESS_POLICY`, derived from `MARKET_FRESHNESS_POLICY` with the same 24 h, no future tolerance, and an explicit offset required.<br>**`connectors/adapters.py`:** `GmpSignalAdapter` defaults to that policy. | **A17-1/A17-2 consistency.** The GMP connector reported FRESH for a stamp 30 min after the reference time and for an offset-less stamp, assuming UTC.<br>The 24 h threshold stays single-sourced, and other connectors keep their policies.<br>A malformed stamp still raises `ValueError`, as before. |
| 3 | **`connectors/adapters.py`:**<br>• labels are mapped only through the existing exact-match table;<br>• an unmapped label becomes `None` instead of passing through raw;<br>• `trend` and `gmp_trend` labels that map differently also become `None`. | **A17-3.** An unmapped label (e.g. `sideways`) was passed through as a raw string. The synonym set is unchanged (`rising`/`up` → `strong`, etc.); each token maps to exactly one accepted label. |

**Already compliant, so not changed:**
- **A17-2 on the scoring path:** the configured `thresholds.market_staleness_hours: 24` (`config/ipo-config.v1.5.0.json` l.104) is applied from the evaluation timestamp. A block exactly 24 h old is FRESH; one second older is STALE.
- **A17-3 in the scorer:** `gmp_bucket` passes `market.gmp.trend` through without derivation (`derived.py` l.1721–1723). The input schema rejects a non-enum label before any scoring or store write (`tests/test_evaluation_record_v1.py` l.289).
- **Enrichment path:** it writes flat legacy keys. A non-object `market.gmp` is MISSING in the snapshot, so that path cannot inject a trend.
- **Missing and malformed timestamps** were already STALE on the scoring path.

**Deliberately not changed:**
- scoring formulas, weights and configuration;
- the input and A15 record schemas;
- the A9 gate and its messages;
- the frozen core;
- the golden result hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`.

The A9 message clause "it does not define source-specific cutoff or freshness semantics" remains accurate: A17's rules apply to every GMP source, and source-specific semantics stay with source qualification. Changing that text would alter persisted A15 record content.

## Evidence and tests

- **Focused tests:** `tests/test_a17_gmp_policy.py` (47 tests). Coverage:
  - the exact-cutoff, +1 s, inside-the-former-allowance and IST-offset cases;
  - the 24 h boundary, missing, malformed and offset-less timestamps;
  - GMP-only scope;
  - connector freshness and the strict coordinator;
  - valid, missing, unsupported, ambiguous and never-derived trend labels;
  - end-to-end unknown trend;
  - A9 withholding for fresh, stale and missing GMP.
- **Mutation check:** reverting each change in a scratch copy fails its tests:
  - removing the pipeline cutoff fails 7;
  - restoring the generic connector policy fails 5;
  - restoring the old trend pass-through fails 6.
- **Full suite and integrity checks:** the full Python suite, `verify_frozen_core()`, `verify_golden_result()` and `verify_v1_6_implementation()` results are recorded in the tracker's A17 section.

## Unresolved dependencies

1. **Source qualification is unchanged.**
   - MarketLiveIPOGMP: NOT QUALIFIED (leading candidate).
   - InvestorGain: NOT QUALIFIED.
   - PapsDigital: closed as a non-independent alternative.
   - R7: UNRESOLVED. It needs a single capture of a genuinely newer publisher reading (investigation record §13.1). A17 proves nothing about publisher reliability, append-only retention, corrections or historical availability.
2. **Source-specific timestamp meaning is not decided here.** Whether a given publisher's displayed stamp is the "source timestamp" A17-1 compares remains part of that publisher's R3 qualification. For example, MarketLiveIPOGMP's stamp is a recording or sync time (investigation record I2).
3. **Not adopted by A17:**
   - the investigation record's §8 PR-3 (artifact and hash), PR-4 (fail-closed A9 code mapping) and PR-5 (single source and labelling);
   - §8 PR-1's "latest reading" selection and its "retrieved at or before the evaluation timestamp" clause. The latter cannot be represented today: `market.gmp` has no retrieval-time field (investigation record §13.3).
   - *Cross-reference (2026-10-15).* Ramki later approved D1–D3, recorded in [`docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md`](../../docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md) §6. They adopt the substance of the following, and leave A17 itself unchanged:
     - §8 PR-3 (D1);
     - the retrieval clause above (D2);
     - PR-4a/4b (D3).
4. **Remaining A8-G items:** snapshot and hash representation, an A9 qualified path, and capture tooling. These require separate decisions and evidence.
5. **Connector reference time:** `GmpSignalAdapter` uses the current time when the caller supplies no `reference_time`. For evaluation eligibility, the pipeline check against the evaluation timestamp is authoritative.
6. **Synonym table:** the existing exact-match synonyms are retained unchanged. Narrowing them would be a separate decision.
7. **Pre-existing behaviour, unchanged:**
   - `parse_datetime` still assumes UTC for offset-less timestamps in non-GMP blocks.
   - The pipeline writes the recorded evaluation-timestamp string with a literal `Z`. Every in-repository caller supplies UTC: CLI `parse_instant`, replay, the golden check and the `now(timezone.utc)` default. A17 compares instants, not that string.

## Evidence references

- `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §3.5, §4.6, §13, §19.
- `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` l.15, l.39, l.45, l.57 (A8-G).
- `handoff/decisions/A9-missing-gmp-final-fail-closed.md`.
- `handoff/decisions/A16-personal-use-operating-scope-and-gate-disposition.md`.
- `handoff/decisions/CONVENTION.md` (GOV-001).
- `docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md` §3. R3 and R4 require an explicitly selected cutoff and allowed-age rule; A17-1 and A17-2 supply them.
- `docs/investigation/A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md` §8, §12.2, §13.2–13.3 and §14.
- `handoff/reference/Claude_IPO Screening Engine v 1.3 — Specification.md` l.123. This is the superseded trend definition, which is not adopted.
