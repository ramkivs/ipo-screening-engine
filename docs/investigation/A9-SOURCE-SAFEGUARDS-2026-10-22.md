# A9 — source-specific safeguards assessment and implementation

Date: 2026-10-22. Verified starting remote/PR7 head:
`e9187f967ba1d88996b6765ce0cf774421d12fc0`, OPEN, unchanged base
`arena/5dd3fe52-ipo-screening-engine` (`e05c0ef…`). A28/A28.1 remains ratified.
Gemini proposals are assessed below, not treated as policy authority.

**A9: OPEN — CONTRACT/IMPLEMENTATION GAP.** These independent fail-closed
safeguards neither qualify a publisher nor enable successful Final admission.

## Already present versus actual gaps

| Boundary / proposal | Existing implementation and precise scope | Assessment / change |
|---|---|---|
| A17 timestamp enforcement | Explicit timezone, no GMP future tolerance, inclusive cutoff/24h in freshness policy/market classification; strict connector rejects stale/future/missing when enabled. Non-strict normalization classifies, not admits. | Preserve. Existing A17 tests cover in-window, exact cutoff, future, missing/offset-less and24h boundaries. Do not turn a normalizer into a qualification verifier. |
| D2 historical availability | `capture_obtained_by` requires complete capture window by cutoff; exact receipt never invented. A18 linker repeats that availability check. | Preserve existing late-window/retroactive-capture tests. A18 VERIFIED means linkage, not fresh/qualified; age remains separately enforced by A17. |
| A28.1 time/binding | `binding_digest` checks capture_start<=capture_end<=cutoff, source<=capture_end and0<=age<=24h, plus exact canonical representations and integrity pins. No authority verifier/Final consumer exists. | Add three missing representation-boundary cases: observation/capture exactly cutoff, capture1µs late despite historical source time, actual ML follow-up timing relationships already expired. Format-only fixtures, not qualified positives. |
| Multiple competing GMP snapshots | Coordinator used `sec_snaps[0]`: first-row/feed order could select among supplied duplicates/revisions/conflicts even though Final remained withheld. | **Real gap fixed:** any multiple secondary GMP candidates raise existing `ConflictingSourceError`, regardless of order/content equality. Caller must supply one explicit selected observation. No dedup/fallback/latest selection or A1 adjudication inferred. |
| IG row identity | No InvestorGain history/DOM parser exists. Normalizer consumes supplied `gmp_pct`/`as_of`, not row ordinal/history. Default `GMP-001` and caller snapshot IDs are reference labels, NOT immutable publisher observation IDs. Payload hash is integrity only. A28 binds issuer/issue/source, exact artifact/manifest pins, quotes, time and explicit selection. | Do NOT adopt proposed composite hash. Tests preserve explicit values across reordered/prepended raw history and reject multiple candidates even with same label, identical content, changed value/time or prepended correction/withdrawal assertions. |
| Canonical serialization/replay | Existing canonical binding serialization, source/issue pin substitution checks, strict JSON/duplicate-key rejection, A18 projection and immutable evaluation replay (including external-byte mutation) already tested. | Preserve. Add supplied-payload key-order/JSON reconstruction and content-change/hash distinction tests. These are component reconstruction tests, not real-source accepted replay. |
| Acquisition failures | Actual automated HTTP/DOM GMP acquisition is NOT in this repository. External rendered-page tool produces manually retained capture manifests. Loader checked bytes but ignored existing `toolResultStatus` and PD's known outage body. | **Real gap fixed:** declared non-success status and verified known `# Temporarily unavailable` rendering raise `GmpEvidenceError` with `capture failed:` message. Existing error convention, no public enum/schema. Retained forensic files remain untouched. |
| HTTP200/error/missing DOM | Tool success is not HTTP200; HTTP headers/status were not captured. No HTML-to-GMP extractor exists. Raw response envelopes are not normalized numeric GMP fields. | Tests exercise200/404/429/500/503 envelopes with outage/HTML-error/empty-element/empty bodies: values/timestamp remain missing, never zero. This is NOT a claim of an HTTP client or exhaustive error-page heuristic. Unknown pages must still satisfy explicit identity/value/time quote linkage; no parser success grants qualification. |
| Explicit withdrawal | D3 does not convert missing to zero; A28/A1 requires attributable applicability/adjudication. No general withdrawal-notice parser/admission verifier exists. | A hypothetical notice stays intact evidence, with no numeric conversion. Multiple snapshots with unresolved correction/conflict/withdrawal assertions are rejected, not adjudicated. One selected snapshot still cannot bypass blanket A9 veto. |

## Proposed signed correction_history

Not adopted as a mandatory field, signature requirement or trust model. A28.1
pins actual qualification/revision/adjudication evidence by existing exact-byte
references; a signature alone neither establishes those facts nor source scope.
No signer/key authority, payload canonicalization for signatures, verification
algorithm, historical key/revocation rules or replay semantics is authorized or
defined for the proposal. No new schema or authority is introduced. Actual
attributable correction records can be assessed through the established evidence
and RAMKI/PA governance route without inventing cryptographic requirements.

## Proposed content-derived observation identity

Determinism alone cannot establish historical availability, correction lineage,
source independence or authority. Hashing value/time/issuer can merge distinct
records or split a corrected record without preserving its relationship; source
clock/zone ambiguity also remains. The existing A28 subject/reference contract
already binds an explicitly selected observation to exact scoped bytes. Preserve
it. No global publisher observation ID or row-dedup hash is invented. The newly
closed first-candidate-selection hole was a reconciliation bug, not a need for
another identity schema.

## Actual regression additions

`tests/test_gmp_source_safeguards.py`:45 cases, including both orders of duplicate,
same-stamp conflicting, corrected-time/value and different-label candidates;
prepended unresolved correction/withdrawal/conflict assertions; repeated/raw
history reorder/prepend; deterministic supplied-payload serialization; distinct
integrity digest versus shared snapshot label;20 response-envelope negatives;
recorded acquisition failures; actual retained PD outage; hypothetical explicit
withdrawal retained as evidence, never numeric zero.

`tests/test_gmp_binding.py`:three additional timing cases described above.
The unsupported/revision assertions and notice are deliberately hypothetical
negative fixtures, NOT publisher evidence, qualification decisions or positives.

## Validation/publication

- Local relevant backend suite: **287 passed,17.12s**, comprising new safeguards,
  binding, connectors, A17, D1–D3, linkage/replay tests. Concrete runtime changes
  justify these executions; this is not an unchanged96-suite rerun.
- Local frontend: **77 passed,0 failed/skipped**,653.205ms.
- All current schemas, frozen core, golden result, inactive-v1.6: PASS.
  Compile/diff checks PASS. No canonical/A15/binding schema, config, scoring,
  frozen-core or capture/inventory bytes changed.
- Full remote backend/frontend/schema/integrity CI is requested by normal push
  because shared coordinator behavior changed. Actual aggregate result will be
  recorded only after observation; no inherited result passed off as new CI.
- Original failed39787253029 remains cause UNKNOWN; no log-access retry.

## Evidence, qualification and exact next dependency

No new publisher evidence was retrieved. The immediately preceding targeted
package/inventory remains the latest source evidence; there is no newly identified
record/archive to justify unchanged-page polling or another checksum audit.

- **MarketLiveIPOGMP: NOT QUALIFIED.** Archive custodian still owes attributable
  observation versions/correction/withdrawal timing/history/competing-record
  resolution. Last captured₹512/21Oct21:37IST was already expired at capture.
- **InvestorGain: NOT QUALIFIED.** Data/archive custodian still owes time/zone/
  event-role definitions and equivalent attributable version/correction/withdrawal/
  conflict traceability. Two captured views/76 rows are not an immutable log.
- **PapsDigital: NOT QUALIFIED, closed/non-independent.** PD/IG custodians would
  need upstream-to-relay version/propagation/conflict records before reconsidering;
  no independent evidence exists. Outage never means publisher withdrawal.

Source/archive records -> engineering assessment -> RAMKI/PA scoped qualification
-> genuine multi-issuer/multi-issue positive baseline and shared accepting verifier
with global negative/positive/replay validation. No Q1–Q3 reopening. Independent
engineering safeguards are implemented without pretending this dependency is met.

## Verified full-CI receipt

- Runtime/test commit: `8706bd4c95f47af4dbc46ae9b62eac1594cf5a73`.
  Remote branch/commit/tree identity and exact six changed-file contents matched
  local Git bytes before validation completion.
- Full run **39829866211**, exact head above: **aggregate COMPLETED/SUCCESS**;
  job/check **120002834170 SUCCESS**. GitHub API-visible totals:
  **1163 tests,0 failures,0 errors,0 skipped,817.954s**.
- Backend, frontend, schema/integrity (including frozen core/golden/inactive-v1.6),
  compilation and clean-tree steps all SUCCESS. Node-action/runtime and Ubuntu
  runner-image migration notices were non-fatal; no unrelated upgrade included.
- Local287 backend/77 frontend counts above are actual executions. The new remote
  full run is not inherited from the earlier96-test run.
- Final receipt is documentation-only with CI skipped; runtime/tests/workflow,
  schema/config and all retained captures match the full-CI-tested runtime commit.
  Exact final remote identity/changed bytes and main/PR6 preservation are checked
  after push and recorded in PR7. This is not a claim of another full execution.

Qualification and acceptance remain unchanged: all candidates NOT QUALIFIED,
PD closed/non-independent; no authorized real-source accepting/replay positive.
Independent safeguards and their regression validation are complete.
