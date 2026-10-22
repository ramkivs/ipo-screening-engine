# A9 — evidence intake and synthetic qualification readiness

2026-10-23. Verified starting remote PR7 head
`dd3295167f9ca6df70908c1e8595ea1fdaab6bed`, OPEN, base `e05c0ef…` unchanged.
Latest existing full CI39829866211 COMPLETED/SUCCESS at8706bd4. Local Git metadata
had again reverted to the main ancestor while working files remained at the
published checkpoint; compared remote tracked-file contents before same-branch
mixed reset, with no file changes. This was metadata recovery, not a repeat of
source checksums. Main/PR6 preserved.

## Completed deliverables and authority boundary

- [Source-specific intake specifications](../gmp/A9-evidence-intake.md): common
  enforced mechanics versus proposed review metadata; separate ML/IG/PD source,
  locator, timing, revisions/withdrawals/conflicts, provenance and reproduction
  requirements. Prose checklist, NOT new closed-schema fields or trust model.
- [Reusable packet](../../handoff/templates/A9-qualification-packet.md): evidence
  ledger, R7/R8, applicability, A28/A18/A17/D2 results, negative/replay checks,
  recommendation/limits, named decision authority and durable decision reference.
- `verify_binding_files` in existing `gmp_binding.py` fills a concrete gap:
  independently recomputes ALL declared exact-file pins after existing A28.1
  representation/digest validation. Whole-file hash even with fragments; bounded
  root including symlink resolution; each resolved file read once per invocation;
  no replay/evaluation cache. Missing/unreadable/mutated files fail using existing
  BindingIntegrityError. **Integrity ONLY; returns no authority/admission signal.**
- Existing A18 linkage/projection, A17/D2 timing, A28 explicit selection and
  source safeguards, trend semantics, Final veto and production replay are reused,
  not duplicated/redesigned. New helper has NO pipeline consumer or admission hook.
- Test-only multi-issuer/issue composition in `tests/gmp_mechanics_harness.py` and
  fixtures under `fixtures/non-authoritative/gmp-mechanics/`. Every case bears
  **SYNTHETIC — NOT QUALIFICATION EVIDENCE**. Fake qualification files explicitly
  say NOT-A-DECISION/NOT-A-SCOPE/NOT-R7-R8, only in pytest temp directories.
  Harness conflict/correction/withdrawal declarations are test metadata, not a
  new production schema or source-completeness/authorization verifier.

## Synthetic coverage and non-qualification safeguards

Two invented issuers, including two offerings for the same issuer. Positive
mechanics return `production_admission=False` and qualification NOT ESTABLISHED.
Tests also run real engine Final resolution and prove those mechanics-positive
cases cannot unlock Final (SOURCE_UNQUALIFIED, no final_outcome).

Coverage: malformed/missing envelopes; stale/future/exact-cutoff/inclusive24h;
unresolved conflicts/corrections/withdrawals; absent/linked/unsupported trend;
artifact/manifest mutation and restore/replay; explicit acquisition failure;
rehashed malformed content; issuer/issue/evaluation substitutions; canonical JSON
and offline saved-envelope reconstruction; missing files; symlink escape and
whole-file fragment hashing; read-once/no cross-call cache. Existing A18 tests
still exercise production evaluation replay, quoted-field projection and mutations.

The test-only harness does not prove the existence/absence of source disputes or
production authority/scope. The engine helper verifies bytes for even fake labelled
qualification files: tests intentionally demonstrate that integrity != approval.
No synthetic case satisfies R7/R8, qualifies a real source or is a genuine
source-backed multi-issuer accepting baseline.

## Populated readiness packet — existing evidence only

This section applies the reusable template to all three current candidates;
UNKNOWN and NOT ESTABLISHED are intentional, not implicit passing results.
Common baseline: latest [inventory](A9-EVIDENCE-TO-ACCEPTANCE-INVENTORY-2026-10-22.md)
and `evidence/gmp-observations/targeted-followup-20261022/` manifest/README.
No new retrieval, publisher contact, unchanged-page polling or old digest audit.
All byte hashes/retrieval details remain in their original retained manifests;
these are declared/prior-audited findings, not a new certification here.

| Packet field | MarketLiveIPOGMP | InvestorGain | PapsDigital |
|---|---|---|---|
| Existing disposition | NOT QUALIFIED | NOT QUALIFIED | NOT QUALIFIED; closed/non-independent |
| Proposed/authorized qualification scope | No scope authorized | No scope authorized | No independent source or scope authorized |
| Candidate/observation refs | ML-T22/ML-A22 plus Oct15 ML-T/ML-A | IG-T22-0/-1 plus Oct15 T0/T1 and parallel transcription | PD-T22 outage plus Oct15 PD issue/listing |
| Source locator/provenance | Named public issue/About URL in manifest; manual rendered transcription | Named issue2369 URL/chunks, rendered excerpts; affiliate/dealer claims not verification | Named relay issue URL; original declared IG upstream, outage is not source observation |
| Latest raw timestamp/semantics |21Oct21:37IST, explicit UTC normalization;₹512/+73.1% |22Oct09:37:03PM/headline₹445; original source zone/event-role UNKNOWN | Latest outage has no observation; earlier relay clocks contradictory |
| Capture bounds | First group22Oct17:42:32.252218–17:43:12.825118Z; About second group ends17:43:35.200412Z | Same first group for chunk0; second for FAQ, use latest required end | Same first-group bounds; outage only |
| Hash/proof status | Exact local-byte pins in capture manifest; original headers/version/cache UNKNOWN | Same; excerpts/ordinals are not stable source IDs; source version UNKNOWN | Same; tool success is not HTTP200 or independence |
| R7 | Claims only; actual correction/version/withdrawal/conflict trail missing | No attributable version/correction/withdrawal chain/resolution | Upstream AND relay version/propagation/conflict trail missing |
| R8 | Two current displays not immutable history; latest reading expired BEFORE capture |41 shared rows match later76-row view,35 added; earlier per-row availability still unproven | Day summaries/outage do not prove historical source/relay availability |
| A28.1 real binding / decision record | NONE | NONE | NONE |
| Real authority/scope verification | NOT ESTABLISHED | NOT ESTABLISHED | NOT ESTABLISHED |
| Real selected-observation eligibility | Latest captured reading timing-ineligible | UNKNOWN/unestablished timing/traceability | No new numeric observation |
| Negative/replay results | Shared component tests only; not accepted real-source replay | Same | Same |
| Recommendation / limitation | Retain NOT QUALIFIED | Retain NOT QUALIFIED | Retain closed/non-independent NOT QUALIFIED |
| Custodian / decision owner | ML archive/capture holder -> engineering -> RAMKI/PA | IG data/archive/capture holder -> engineering -> RAMKI/PA | PD relay archive AND IG original records -> engineering/RAMKI/PA |

Capture lower bound for first group is conservative fetch-mtime, not exact tool
receipt; original package discloses that limitation. New helper/file pins do not
supply missing source facts. Rendered D1 evidence remains permitted; provider-native
bytes and digital signatures are not reinstated as requirements.

## Validation/publication status

Local mechanics+binding+production linkage/replay suite:171 passed16.54s. This
includes new read-once/isolation/negative cases, not an unchanged successful-suite
rerun. CI focused target is extended for the new mechanics suite; remote result
will be recorded only after observation. No active pipeline/canonical schema/
config/scoring/capture changes. Full1163 backend run at8706bd4 remains inherited;
opt-in unused helper/test harness does not warrant duplicating that full run.

**A9 OPEN — CONTRACT/IMPLEMENTATION GAP.** Exact external dependency remains
attributable source/archive records specified in intake/inventory, then evidence
assessment and RAMKI/PA scoped decision. Genuine multi-issue source-backed positives,
shared accepting verifier and corresponding global/replay validation remain future
conditional work. Q1–Q3 are not reopened; original failed-run cause stays UNKNOWN.

## Verified validation/publication receipt

- Implementation/intake/test commit: `b3ce4312969322f07e1a85774c5b13d6a360610a`.
  Actual remote branch/commit/tree and all ten changed-file bytes matched local
  Git before recording this receipt.
- New focused CI **39838046080**, exact head above: **aggregate COMPLETED/SUCCESS**;
  job/check **120031445595 SUCCESS**. API-visible totals **175 tests,0 failures,
  0 errors,0 skipped,18.363s**. Includes76 new synthetic cases plus current binding,
  production linkage/replay and retained-inventory regression. New helper and
  extended CI target warrant this run; it is not an unchanged96-suite repetition.
- Remote schema/integrity (frozen/golden/inactive-v1.6), compilation and clean-tree
  steps SUCCESS. Frontend deliberately skipped by focused scope; actual LOCAL
  frontend77 passed0failed/skipped,659.068ms. Local relevant backend171 passed16.54s.
- Workflow YAML/shell syntax, document links and synthetic-label checks PASS.
  All current schemas/frozen/golden/inactive-v1.6 and compile/diff PASS locally.
- Previous full39829866211 at8706bd4 remains inherited1163/backend+frontend success;
  it is not misrepresented as a new full test run for this delta. New helper is
  opt-in/integrity-only and not imported into the unchanged admission pipeline.
- Final receipt documentation-only, CI skipped; helper/tests/workflow/fixtures,
  schemas/config/capture bytes match focused-testedb3ce431. Final remote identity
  and exact changed bytes are checked after push in PR7 receipt. Main/PR6 preserved.

Intake specs, packet template/population, file-pin component and synthetic suite
are complete. ML/IG NOT QUALIFIED; PD NOT QUALIFIED/closed/non-independent. No
source facts, scoped authority or genuine accepting positive were manufactured.
**A9 remains OPEN — CONTRACT/IMPLEMENTATION GAP.**
