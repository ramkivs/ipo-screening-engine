# A11 — Phase 0 Remains Open

- **Record ID:** A11
- **Title:** Phase 0 open disposition and remaining blockers
- **Status:** RAMKI-APPROVED DISPOSITION — PHASE 0 REMAINS OPEN
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-13 (Asia/Calcutta)
- **Approval provenance:** Ramki's explicit instruction in the Arena conversation received 2026-10-13 (Asia/Calcutta). No decision time is supplied or asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** Session branch `arena/573e69a4-ipo-screening-engine` at `de8d5f82442eff3ef77437c1fe96fa73c7a62c2c`; governing evidence ref `arena/4e1080b7-ipo-screening-engine` at `adbd93c5b4450fb113561368d7d101eb4686c842`.
- **Scope:** Current Phase 0 status and classification of unresolved obligations. This is not a Phase 0 closure record.
- **Implementation authority:** NOT GRANTED. Phase 1 remains unauthorized.

## Approved disposition

1. **Phase 0 remains OPEN.** It must not be closed to unblock implementation.
2. The Phase 0 exit criteria proposed in `handoff/investigation/PROGRAM-AUTHORITY-PHASE0-CANDIDATE-AND-IMPLEMENTATION-DECISION-PACKAGE-DRAFT-2026-10-13.md` remain a proposal. This record does not approve them as a complete closure checklist.
3. The following obligations remain **BLOCKERS** to the affected gate and to any claim that the related Phase 0 contract is complete. They are not silently deferred by this record:

| Obligation | Status and safe consequence |
|---|---|
| **A1 canonical evidence / field adjudication** | The schema/evidence representation remains incomplete. For any actual conflict, preserve competing observations and provenance; the disputed field remains non-screenable until its own durable Ramki decision and validation. No field-level adjudication is made here. |
| **A7 result representation** | The logical outcome rules remain approved, but the serialized result contract and unverified-only terminal case remain unresolved. Do not infer a terminal label; the result serializer and dependent implementation remain blocked for that case. |
| **A8-M NIFTY evidence and availability** | Source-native qualification, a complete valid 200-session series, and deterministic session/publication-availability evidence remain unmet. No current category is assigned. If required NIFTY is UNKNOWN, withhold Final under the approved NIFTY rule. NDAL remains UNSENT. |
| **A8-G / A9 source contract** | Provider, event/as-of, cutoff, and hash/snapshot representation remain open. A9's approved narrow rule remains: an absent or invalid required qualifying snapshot/hash withholds Final. This record does not authorize A9 integration. |
| **A8-S / A10 subscription contract** | Source, qualifying event/as-of, publication/retrieval/cutoff, fields/units/denominator and subscription Final consequences remain unresolved. A10 permits evidence/display only; no scoring use or inferred missing-data Final rule. |
| **A8-P / A5 peers** | Source, named session, point-in-time universe, cutoff, eligibility and calibration evidence/parameters remain unresolved. `CALIBRATION_EVIDENCE_INSUFFICIENT` remains; peer eligibility/scoring stays blocked. |
| **D1/D2/D3 and GCP fixture disposition** | No complete current disposition was located for the remaining D1/D3 and GCP sign-off questions; D2's old sequencing question is stale for already-delivered UI/Phase 5 work. These are not deemed formally deferred here. Do not claim the affected scope closed or change thresholds/fixtures absent a separate decision. |
| **Other A8 metrics** | Subscription, GMP source qualification beyond A9, VIX, listing gains, anchor and other market metrics retain their own source/policy contracts. No substitution, coupling, scoring or implementation is authorized by this disposition. Keep VIX separate from NIFTY. |

4. Existing explicitly deferred single-user roadmap items remain deferred under their prior scope; that does not defer or close the source, output, or evidence obligations above.
5. Phase 0 closure, candidate assembly, Phase 1 implementation, independent acceptance, merge/release and production activation are distinct gates. This record grants none of them except the Phase 0 status disposition itself.

## Rationale and evidence

The A8 final-snapshot record on 4e (`adbd93c`) states Phase 0 OPEN and Phase 1 UNAUTHORIZED and records open source/event/cutoff contracts. A1 identifies Ramki as field-conflict authority and requires attributable field-level decisions. A7 leaves the exact serialized result and one terminal case open. A9 and A10 remain narrow and expressly do not authorize implementation or source qualification. The published reconciliation audit and the current 4e tracker report no formal Phase 0 closure or independent acceptance.

### Supporting evidence and v1.5 references

- `handoff/decisions/A1-evidence-adjudication-authority.md`, `A7-knockout-verdict-precedence.md`, current A8/A8-M records, `A9-missing-gmp-final-fail-closed.md`, and `A10-interim-subscription-handling.md` at the pinned 4e baseline above.
- `handoff/investigation/IPO-SCREENING-ENGINE-RECONCILIATION-AUDIT-DRAFT-2026-10-13.md` and the published Program Authority package at the session baseline above.
- `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md` §§3.2–3.4, 4.5–4.6, 5, 16, 18–20, 23; `ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md` §§3–5, 9–15, 23. These remain authoritative; A11 records project status and does not amend them.

## Consequences and constraints

- Do not close Phase 0 by treating an unqualified input as safe or by making a silent deferral.
- A safe deferral requires a separate attributable Ramki decision naming the affected contract and consequence.
- No schema, scoring, configuration, fixture, application or test changes are authorized by A11.

## Unresolved dependencies

The canonical field map/serialization decision; A7's unverified-only terminal representation; each source-specific A8 contract; the disposition of D1/D3/GCP items; and independent acceptance remain open as applicable.

---
