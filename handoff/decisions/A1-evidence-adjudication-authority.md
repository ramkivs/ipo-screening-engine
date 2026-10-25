# A1 — Evidence Adjudication Authority

- **Decision ID:** A1
- **Title:** RAMKI as conflict-adjudication authority
- **Status:** APPROVED
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-09 (Asia/Calcutta)
- **Decision source / authorization evidence:** Ramki's explicit A1 direction in TASK 15 and reaffirmation in TASK 16. This record is the durable project record of that standing authority decision; it is not a field-level adjudication.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/4e1080b7-ipo-screening-engine`, pre-record commit `01ba66c12ca1195fd7acbd287c3e39a019808094`
- **Scope:** Authority and safeguards for adjudicating conflicting source evidence at the canonical field level under A1.
- **Implementation authority:** NOT GRANTED. This decision does not authorize Phase 1 or application implementation.

## Approved decision text

1. **RAMKI is the designated authority** for conflict adjudication under A1.
2. Arena may investigate, preserve source observations and provenance, identify discrepancies and recommend resolutions.
3. Arena may not independently adjudicate a conflict or promote disputed evidence to `VERIFIED`.
4. Each field-level conflict adjudication requires a durable decision record attributable to RAMKI. That record must identify the affected field, competing observations and provenance, rationale, decision, authorization evidence and decision date.
5. Until the required authorization and evidence are recorded, the disputed field remains non-screenable.
6. Original observations and their evidence statuses are preserved; adjudication does not erase or rewrite them.
7. Majority-vote resolution is prohibited.
8. Only appropriately validated `VERIFIED` fields may enter screening. `CORROBORATED` remains informational; conflicting, unavailable or unverified evidence does not become screenable through this authority decision.

## Supporting evidence and v1.5 references

- `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §§3.4–3.5, 5 and 20: evidence before score; preservation of raw/normalized values, source references and verification status; cross-source differences must be reported, not silently resolved; invalid configuration blocks scoring.
- `handoff/authoritative/ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md` §12: material-input provenance and evidence requirements.
- `handoff/authoritative/ARENA_IPO_Screening_Artifact_Manifest_v1.5.md` §Artifact precedence: the v1.5 specification is authoritative over legacy reference artifacts.

## Rationale

A durable, attributable adjudication preserves auditability without allowing an automated agent, extraction result or majority vote to resolve contradictory source observations. Keeping source observations, evidence resolution and value state distinct supports the v1.5 requirement to prefer correct incompleteness over fabricated certainty.

## Consequences and constraints

- This is a standing authority decision, **not** authorization of any particular disputed field value.
- A field remains non-screenable until its own adjudication record and required authorization evidence exist and the resulting value passes validation.
- A1 does not establish a general source-precedence hierarchy, decide any source conflict, alter the v1.5 state model, or authorize changes to scoring or eligibility.
- This decision supplements governance records; it does not rewrite the authoritative v1.5 specification.

## Unresolved dependencies

- The canonical schema/evidence contract must represent source observations and field-level resolution without collapsing value state and evidence status.
- Every future adjudication must provide its own durable record and evidence. No such field-level adjudication is made by this record.

## Implementation authority

**Not granted.** Phase 1 remains unauthorized.
