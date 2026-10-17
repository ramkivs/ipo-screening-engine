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
