# Durable Decision-Record Convention

- **Record ID:** GOV-001
- **Status:** APPROVED
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-09 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** branch `arena/4e1080b7-ipo-screening-engine`, commit `01ba66c12ca1195fd7acbd287c3e39a019808094`
- **Scope:** Markdown records in `handoff/decisions/` for approved project decisions and explicitly open decision investigations.

## Approved convention

1. Store decision records in `handoff/decisions/` as Markdown.
2. Use one record per decision, named `A<id>-<short-kebab-title>.md` (for example, `A1-evidence-adjudication-authority.md`). IDs must be unique within the project decision register.
3. Each record identifies its status, decision authority, decision or investigation date, repository/baseline, scope, approved text (if any), supporting evidence and v1.5 references, rationale, consequences/constraints, unresolved dependencies and implementation-authority status.
4. Distinguish a Ramki-approved decision from v1.5 requirements, Arena analysis/recommendations and unresolved proposals. An investigation record is not an approval of its proposed alternatives.
5. The v1.5 specification remains authoritative. A decision record may document a Ramki-approved resolution of an ambiguity but must not represent that resolution as text already present in v1.5. A direct conflict with an explicit v1.5 requirement must be reported and not silently overridden.
6. Decision records do not authorize application implementation unless a record expressly says so. The current Phase 1 implementation authority remains withheld.

## Supporting evidence

- Ramki's explicit TASK 16 authorization establishes `handoff/decisions/` and Markdown as the approved record location and format.
- `handoff/authoritative/ARENA_IPO_Screening_Artifact_Manifest_v1.5.md` establishes the v1.5 artifact precedence that decision records must preserve.

## Rationale

Ramki expressly authorized this directory and Markdown format in TASK 16. The repository had no prior decision-record path or governance-record convention. This record establishes only the authorized recordkeeping convention; it does not amend the v1.5 specification or resolve A8 source/cutoff choices.

## Consequences and constraints

- A1 and A7 are recorded separately from the still-open A8 investigation.
- Task 16 A8 event/cutoff alternatives were proposals; Task 18 later approved policy directions are recorded in A8, while source/provider/event/cutoff contracts and missing-GMP Final handling remain open.
- A5 remains `CALIBRATION_EVIDENCE_INSUFFICIENT`; peer scoring remains blocked.
- No application, schema, configuration, scoring, eligibility or provider behavior is changed by this convention.

## Unresolved dependencies

A8 source/provider selection, actual-event/cutoff rules, event evidence and unavailable-snapshot behavior remain for Ramki's decision. Other unresolved Phase 0 contracts remain governed by their existing decision status.

## Implementation authority

**Not granted.** Phase 1 remains unauthorized.
