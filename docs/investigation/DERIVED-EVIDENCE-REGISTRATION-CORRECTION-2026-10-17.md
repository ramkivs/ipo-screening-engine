# Derived-Evidence Registration Correction

- **Date:** 2026-10-17 · **Baseline:** `7588b42353e686a3615c0f3277071e8b05d92461` · **Trigger:** Vishal acceptance reconciliation — derived values (`issue.ofs` 3300.0, `issue.fresh_shares` 6590909) existed in the persisted input snapshot but had no Evidence Explorer cards; `EV-issue-ofs_sellers` was labelled `UNKNOWN / UNVERIFIED` in the inspector despite `verification: FILING` with a recorded quotation.

## Root causes (established by the preceding read-only investigation, revalidated during implementation)

1. Enrichment assembly writes derived evidence specifications under source `SRC-DERIVED`, but that source was never declared in the canonical `_sources` manifest. `canonical_input.build_registry` correctly refuses evidence whose source is unregistered, so the specifications for `issue.fresh_shares`, `issue.post_issue_shares`, `issue.ofs` and `issue.post_issue_eps` were skipped with `EVIDENCE_SOURCE_UNREGISTERED` warnings and never reached the persisted evidence artifact.
2. The runtime builder emitted only list-level evidence for `issue.ofs_sellers`, so the seller-specific `shares_sold` quantity had no evidence record (the Explorer shows scalars or a name summary, never list internals).
3. The frontend inspector's label precedence let a null scalar `extracted_value` outrank a recorded filing quotation, mislabelling list-valued filing evidence as unknown.

## Correction

- `enrichment_engine.EnrichmentEngine.assemble`: when any evidence specification references `SRC-DERIVED`, the source is now declared in `canonical["_sources"]` with `source_type: DERIVED` (registered by the producer of the specifications — the registry's validation is unchanged and still rejects genuinely unregistered sources). Derived records keep `extraction_method: DERIVED`, their formula notes and `quote: None`; they are never presented as filing quotations.
- `extraction/builder._build_evidence`: one evidence spec per selling shareholder for `issue.ofs_sellers[i].shares_sold`, bound to the same filing source, page and locator as the seller list, with a note recording the quantity linkage (identity quotation stays on `issue.ofs_sellers`).
- `presentation/service.get_evaluation_evidence` (read-only projection): canonical path resolution now handles list indices (`issue.ofs_sellers[0].shares_sold`) and share-count fields carry an `equity shares` unit. No persisted record is mutated.
- `frontend/app.js` inspector: a recorded quotation with `FILING`/`OFFICIAL_VERIFIED` verification is classified as source evidence regardless of a null scalar value; genuinely absent evidence (no value, no quote) still reads `UNKNOWN / UNVERIFIED`, and quoteless values still read `DERIVED VALUE`.

## Validation (repository-controlled; controlled transport — not live SEBI retrieval, not Windows UI acceptance)

- `tests/test_derived_evidence_registration.py` (2): real Vishal RHP end-to-end (unmocked extraction, injected prospectus transport) asserting on the **persisted artifact via `get_evaluation_evidence`**: derived cards for fresh shares (6590909), OFS (3300.0), post-issue shares (26390909) and post-issue EPS (9.46), all `DERIVED`/`SRC-DERIVED` with formulas and no quotation; `SRC-DERIVED` declared with type `DERIVED`; zero `EVIDENCE_SOURCE_UNREGISTERED` warnings; seller-quantity card `EV-issue.ofs_sellers[0].shares_sold` = 1500000, `FILING`, `RHP-FILING-…`, distinct from the derived aggregate.
- `frontend/test/evidence-inspector.test.js` (3): seller-list item is `SOURCE EVIDENCE (Extracted from Filing)` (never UNKNOWN); absent evidence stays UNKNOWN; derived stays DERIVED.
- Affected suites: 86 passed. **Full Python: 987 passed. Frontend: 68 passed.** Golden/frozen intact (golden evaluation does not pass through assembly). No type-checker or production build is configured in this repository; `compileall` and `node --check` are clean.

## Remaining

Windows UI acceptance of the restored cards is the user's run (fresh upload after update + restart, since persisted records are immutable and are not rewritten). Jio remains a separate subsequent test path (upload its actual RHP; fail closed if official terms are unavailable) — untouched by this correction.

## Addendum (same day): why fresh Windows uploads still showed 22 citations

The user's fresh evaluation on `bc508f9` showed 22 citations and no derived cards, while the repository regression (fresh store) showed 27. Targeted reconciliation (no repeated investigation):

- **Scoring impact: none, established deterministically.** Identical ingest executed under `7588b42` and `bc508f9` code (real RHP + controlled transport) produced identical `input_snapshot_hash` (`79f929b7…`, the snapshot strips `_evidence`/`_sources` — everything scored), identical `final_score` 32.0, confidence, verdict (`INSUFFICIENT_DATA`) and knockouts; only the evidence artifact differed (22 vs 27 items). The defect was confined to evidence registration/persistence/presentation.
- **Divergence mechanism:** duplicate detection treated a stored record as interchangeable when `input_snapshot_hash` + `config_hash` matched (and the `result_hash` branch was bypassed because the result hash covers the evidence manifest, which the fix legitimately changed). A store already holding a pre-fix Vishal evaluation therefore returned that immutable record — with its 22-item artifact — for every fresh upload. The corrected seller label appeared (frontend renders old artifacts with new code), but the artifact-bound cards could not. Repository tests used fresh stores, so they never hit the stale-duplicate path.
- **Correction:** duplicate identity now also requires evidence-content identity (evidence ids/sources/methods; volatile retrieval timestamps excluded) — `presentation/service.py`. Identical re-uploads remain idempotent; a materially different evidence registry produces a new evaluation and never rewrites the old record.
- **Regression:** `test_reupload_after_evidence_fix_creates_new_evaluation_not_stale_duplicate` emulates the pre-fix registry outcome against a seeded store: re-upload creates a new evaluation exposing the cards, the legacy record stays untouched, and a third identical upload is again a duplicate. Full Python 988 passed; frontend 68 passed.
- **Windows acceptance (only remaining user-side step):** update, restart, re-upload the Vishal RHP once — a new evaluation (new ID) with the restored cards is expected; the pre-fix evaluation remains in history by design. Jio remains correctly blocked until an official Jio issue-term document exists on an accepted pathway (manual entry alone cannot supply OFS under the Step-5 contract; the differing intermediate/final missing-term messages are per-request accurate).
