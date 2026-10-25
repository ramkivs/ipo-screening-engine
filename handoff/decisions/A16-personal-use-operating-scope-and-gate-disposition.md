# A16 — Personal-Use Operating Scope and Gate Disposition

- **Decision ID:** A16
- **Status:** APPROVED
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-14 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** Fixed session branch `arena/573e69a4-ipo-screening-engine` at remotely verified commit `3b7c71cd05efc608fdca60eb1a988f5cf19d60a0` (pre-A16 operating-scope record)
- **Scope:** Ramki's single-user, personal-use IPO Screening Engine; routine product implementation, testing, documentation, commit/publication, and remote verification within that scope.

## Approved operating scope

Ramki's explicit 2026-10-14 directive establishes this product as a **single-user personal application**. It is not an enterprise, multi-user, or production-deployment program. Routine in-scope engineering does not require renewed approval for each implementation, test, documentation, commit, or publication step.

For this lane, the most current working product baseline is the fixed session branch at the verified A15 follow-on tip `3b7c71cd05efc608fdca60eb1a988f5cf19d60a0`. It includes the existing 01a product lineage and A15's separately authorized implementation. Candidate M `9bad659927616ad7fd3aad2864b6637f095872c5` remains preserved as the earlier bounded review candidate; it is not rebuilt, rebased, or treated as the current personal-app baseline. PR #3's older head is not a prerequisite for using or improving the current personal application. This is a working-baseline determination, not a release or production promotion.

## Superseding disposition of procedural gates

1. **Phase 0:** A11's historical `OPEN` record is not rewritten as closed. Its broad checklist is no longer a global delivery gate for routine personal-use work. Only a specific missing evidence or product decision that materially affects correctness can block that particular behavior.
2. **Phase 1:** A generic Phase 1 grant is not required for routine in-scope personal-app implementation. This supersedes the prior blanket implementation hold for this lane only; it does not authorize unsupported metric semantics, scoring thresholds, unqualified source behavior, or out-of-scope architecture.
3. **Independent review and product acceptance:** A14's appointment, Candidate M review, and any external review/acceptance ceremony are not prerequisites for Ramki's personal use. Targeted self-review, automated regression tests, schema/compatibility checks, and reproducibility checks are proportionate safeguards. They must be described as self-review/testing, never as independent review or external acceptance. The historical A14 request remains a record of its original candidate scope; it need not be routed merely to advance the personal application.
4. **Canonical selection and promotion:** No separate canonical-selection, PR, merge, tag, release, deployment, or production-activation ceremony is required for the personal-use working baseline. Do not infer that any such action occurred or is authorized by this decision.

## Correctness obligations retained

This decision removes procedural waiting, not engineering safeguards. Preserve deterministic evaluation, existing golden results, fail-closed/missing-data behavior, schema/output compatibility, immutable persistence and verification, and accurate provenance. Do not invent source identity, availability, freshness, cutoffs, thresholds, missing-data behavior, or policy decisions. A metric that materially depends on an absent source contract or evidence remains isolated and unavailable/unknown; unrelated usable product features may continue.

The existing A1/A7/A8-M/A9/A10 and v1.5 decisions remain controlling where they establish concrete semantics. A15's approved output profile remains bounded to its exact implementation. v1.6 remains inactive; this decision does not activate it or change scoring weights.

## Implementation authority and explicit exclusions

Routine changes to the personal application—including its local run path, dependency setup, presentation API/UI, persistence/recovery behavior, tests, compatibility, and supporting documentation—are authorized on `arena/573e69a4-ipo-screening-engine`, with proportionate targeted tests and remote verification. A policy/data decision or real source evidence remains necessary only for the specific metric behavior that depends on it.

This decision does **not** authorize external purchases or provider contact; live-source integrations without evidence/contracts; new scoring thresholds or v1.6 activation; destructive cleanup; authentication/RBAC; multi-user support; PostgreSQL; enterprise architecture; or production deployment. Those are not personal-use objectives.

## Rationale

The previous review and phase gates were created for bounded candidate assembly and controlled promotion. They do not provide material correctness protection for routine single-user development when their reviewers/channels are unavailable. Correctness is better protected by the existing golden fixtures, deterministic persistence, schema checks, explicit unknown semantics, targeted code inspection, and regression tests. Source-specific policy gaps remain real blockers only for the affected metric, not for unrelated app functionality.

## Consequences and next operating rule

- Record Phase 0 as historically OPEN, but do not wait for ceremonial closure to perform authorized personal-use work.
- Use the fixed session branch's latest remotely verified tree as the working baseline; preserve Candidate M and PR #3 without promotion or cleanup actions.
- Record actual test results and self-review limitations. If a test exposes a concrete defect, fix it in scope, rerun the affected tests, publish, and verify the remote result.
- Keep source/evidence-dependent metrics visibly unresolved until their real prerequisites exist; continue with independent application work.
