# A10 — A8-S Interim Subscription Handling

- **Decision ID:** A10
- **Decision:** Approved interim subscription handling
- **Approval status:** APPROVED — INTERIM HANDLING ONLY
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-11 (Asia/Calcutta)
- **Approval provenance:** Ramki's explicit approval of the interim-handling direction in the instruction authorizing this publication, received 2026-10-11 (Asia/Calcutta). No decision time is supplied or asserted. The approval is limited to this interim-handling decision.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** Governing decision branch `arena/4e1080b7-ipo-screening-engine` at `71bbe81b0f4fa2c0f1c57751d9743a768d8597e5`; `main` at `01ba66c12ca1195fd7acbd287c3e39a019808094`; supporting evidence branch `arena/01a10b42-ipo-screening-engine` at `951d77d4ae39422c232fd727be89551aeb868ab4`.
- **Scope:** Interim handling of NSE-specific, BSE-specific, and separately identified All Exchange subscription observations.
- **Source qualification authority:** NOT GRANTED.
- **Implementation authority:** NOT GRANTED. Phase 1 remains unauthorized.

## Approved interim-handling decision

Ramki approves only the following interim subscription-data handling:

1. Preserve NSE-specific, BSE-specific, and separately identified All Exchange subscription observations as distinct evidence, retaining their source references and provenance.
2. Permit evidence/display use only, subject to the existing evidence limitations.
3. Do not permit scoring use until the applicable source-specific contract is approved and its source, qualifying event, timestamps, fields, units, denominator, normalization, and provenance have been verified.
4. Do not average, combine, substitute, or infer equivalence between observation types.
5. Apply A1 to disputed evidence: preserve competing observations, do not resolve conflicts by majority vote, and keep disputed fields non-screenable until a durable field-level Ramki adjudication is made.
6. Keep A9 limited to its existing GMP-specific rule. Do not extend it to subscription data.
7. Do not infer from this decision whether missing, stale, unavailable, incomplete, or unverifiable subscription data blocks `FINAL`. Those consequences remain undecided as specified below.

This decision creates no fallback, source equivalence, provider approval, source qualification, scoring eligibility, or `FINAL` exception.

## Open decisions retained

The following questions remain open; this record establishes no default or answer for them:

- Source approval for each observation type.
- The qualifying final event and source-native as-of semantics for each observation type.
- The relationships among event/as-of, publication, retrieval, cutoff, and evaluation times.
- Required categories and quantity fields, units, denominator, and normalization.
- Freshness thresholds.
- Handling of missing, stale, unavailable, incomplete, or unverifiable subscription data, including any effect on `FINAL`.
- Scoring eligibility of any observation type.

## Relationship to existing authority and boundaries

- **A8-S remains unchanged.** Its approved S2 direction continues to prefer the actual final published subscription record, conditional on an approved source establishing the underlying event and source-native as-of timestamp. Event/as-of, publication, retrieval, and evaluation cutoff remain separate. This interim decision does not complete the A8-S source, event, timestamp, or cutoff contract.
- **A1 remains unchanged.** Ramki remains the conflict-adjudication authority. Preserve original observations and provenance; no majority-vote resolution; disputed fields remain non-screenable pending the required durable field-level adjudication.
- **A9 remains unchanged and GMP-specific.** Its approved missing-or-invalid required qualifying GMP snapshot/hash consequence is not extended to subscription data.
- **v1.5 remains unchanged and authoritative.** This decision does not amend the specification. It does not modify application behavior, scoring logic, or an existing `FINAL` policy.
- **Authority remains limited.** No source is approved for scoring. No source qualification, provider configuration, integration, scoring change, Phase 1 work, or `FINAL` exception is authorized. Phase 0 remains OPEN and Phase 1 remains UNAUTHORIZED, consistent with the governing A8 record.
- **Existing evidence status is preserved.** Source captures are evidence, not source approval. The VNL discrepancy remains **CLOSED WITH LIMITATION**; this decision does not reopen or recalculate it. In the reviewed VNL evidence, the README identifies the package as non-authoritative investigation evidence and says the All Exchange scope remains unverified. No scoring-source qualification is established here.

## Rationale and consequences

A8-S prefers an actual final published record but leaves source-specific qualification and missing-record handling open. A1 supplies the conflict safeguards, and A9 resolves only its stated GMP case. The interim direction preserves useful observations for evidence/display while preventing these unqualified observations from being treated as scoring inputs. It intentionally leaves subscription `FINAL` consequences, source contracts, and scoring eligibility for separate decisions.

## Evidence references

Governing records, as read at `71bbe81b0f4fa2c0f1c57751d9743a768d8597e5`:

- [`handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md`](https://github.com/ramkivs/ipo-screening-engine/blob/71bbe81b0f4fa2c0f1c57751d9743a768d8597e5/handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md), especially A8-S and the common timestamp/provenance safeguards.
- [`handoff/decisions/A1-evidence-adjudication-authority.md`](https://github.com/ramkivs/ipo-screening-engine/blob/71bbe81b0f4fa2c0f1c57751d9743a768d8597e5/handoff/decisions/A1-evidence-adjudication-authority.md), approved conflict safeguards.
- [`handoff/decisions/A9-missing-gmp-final-fail-closed.md`](https://github.com/ramkivs/ipo-screening-engine/blob/71bbe81b0f4fa2c0f1c57751d9743a768d8597e5/handoff/decisions/A9-missing-gmp-final-fail-closed.md), limited GMP rule and boundaries.
- [`handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md`](https://github.com/ramkivs/ipo-screening-engine/blob/71bbe81b0f4fa2c0f1c57751d9743a768d8597e5/handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md), §§4.6, 5, and 19.
- [`handoff/decisions/CONVENTION.md`](https://github.com/ramkivs/ipo-screening-engine/blob/71bbe81b0f4fa2c0f1c57751d9743a768d8597e5/handoff/decisions/CONVENTION.md), approved Markdown decision-record location, format, and authority boundaries.

Supporting evidence branch `arena/01a10b42-ipo-screening-engine` at `951d77d4ae39422c232fd727be89551aeb868ab4`:

- [`evidence/ipo-subscription/vnl-20261011/README.md`](https://github.com/ramkivs/ipo-screening-engine/blob/951d77d4ae39422c232fd727be89551aeb868ab4/evidence/ipo-subscription/vnl-20261011/README.md), labelled NON-AUTHORITATIVE INVESTIGATION EVIDENCE and recording the VNL discrepancy as CLOSED WITH LIMITATION. This evidence is not a provider approval or scoring-source contract.

## Implementation and qualification authority

**Source qualification authority: NOT GRANTED.** **Implementation authority: NOT GRANTED.** Phase 1 remains unauthorized.
