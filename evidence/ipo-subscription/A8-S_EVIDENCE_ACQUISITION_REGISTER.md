# A8-S Evidence Acquisition Register

## Purpose

This register inventories subscription-related evidence preserved in the repository and records the limitations on what that evidence establishes. It is a documentary evidence artifact, not a source-qualification or implementation authorization.

## Repository and publication context

- Repository: `ramkivs/ipo-screening-engine`
- Supporting branch: `arena/01a10b42-ipo-screening-engine`
- Verified parent commit: `951d77d4ae39422c232fd727be89551aeb868ab4`
- Related governance decision: [A10 - A8-S Interim Subscription Handling](https://github.com/ramkivs/ipo-screening-engine/blob/9085bb6be74a2aa66fa9aaf91ddce557b7ba473c/handoff/decisions/A10-interim-subscription-handling.md)
- Scope: evidence inventory and acquisition limitations only.

## Preserved evidence inventory

The following files were present in the local checkout when this register was prepared. File sizes and SHA-256 values identify the local contents at inventory time. They do not independently authenticate the original source or establish a complete source-to-capture chain.

- `evidence/ipo-subscription/vnl-20261011/api-disclaimer.json` — 762 bytes; SHA-256 `3133b433fea4390893239b8e9f04164063a1b1675a578935c50dbf3ee1de26b9`.
- `evidence/ipo-subscription/vnl-20261011/api-ipo-active-category-VNL.json` — 2684 bytes; SHA-256 `3f58b12ec21241d1cb63806686419eafbc90efbe6709f55ea360ae499ed86acc`.
- `evidence/ipo-subscription/vnl-20261011/api-ipo-bid-details-VNL-EQ.json` — 2557 bytes; SHA-256 `c61f4bcb90c13b4b99f1debddee60d5e3ac029b678c7b04feeae2ef02e091a64`.
- `evidence/ipo-subscription/vnl-20261011/api-ipo-chart-demand-VNL-ALL.json` — 2 bytes; SHA-256 `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
- `evidence/ipo-subscription/vnl-20261011/api-ipo-chart-demand-VNL-NSE.json` — 2 bytes; SHA-256 `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
- `evidence/ipo-subscription/vnl-20261011/api-ipo-detail-VNL.json` — 12331 bytes; SHA-256 `4219115872222145d2062e306fcea1022017ee1344e189f07daac9fe4bad5874`.
- `evidence/ipo-subscription/vnl-20261011/issue-information.js` — 42019 bytes; SHA-256 `41292fa8c23cdcd949f922fd7f6f639bcc22b5545835f631ea009bc716c972e1`.
- `evidence/ipo-subscription/vnl-20261011/README.md` — 2170 bytes; SHA-256 `1543b7249c7851d5fc1c146cb5dc5f9dc503a79e7bd87e51fc8155a39937e181`.
- `evidence/ipo-subscription/vnl-20261011/SHA256-MANIFEST.json` — 1489 bytes; SHA-256 `26cf9fd19f9fa348961f891e560a5874548811c09544f4ccd25cfcbacb746d6d`.
- `evidence/ipo-subscription/vnl-20261011/vnl-issue-information.html` — 313040 bytes; SHA-256 `2ae7009b9f30c026c91a1d38a4b943f348ab3f275f0b1b5b971481a8f72e78f2`.

## Acquisition and interpretation limitations

1. Preserved repository files establish what files were retained in this checkout. Their presence alone does not independently authenticate an exchange response, establish the original responding host, or prove an unaltered source-to-capture chain.
2. Captured page labels, JavaScript, relative API routes, and response fields do not by themselves establish a qualified source contract or prove the underlying subscription event's source-native as-of time.
3. Event time, source-native as-of time, publication time, retrieval time, cutoff time, and evaluation time must remain distinct unless source evidence establishes their relationship.
4. A cumulative bid graph must not be assumed to be a subscription multiple or final subscription snapshot without a documented field mapping and denominator.
5. NSE-specific, BSE-specific, and separately identified All Exchange observations must remain distinct. Do not average, combine, substitute, or infer equivalence between them.
6. An empty field or response collection is not evidence of zero demand unless its semantics are independently established.
7. Display-policy notes, including UPI display-update notes, do not by themselves prove the final underlying event or its source-native as-of time.
8. This register does not establish an approved subscription source, source qualification contract, scoring eligibility, or the consequence of missing subscription data for `FINAL`.
9. The previously recorded VNL discrepancy remains **CLOSED WITH LIMITATION**. This register does not recalculate or reopen it.
10. The related A10 decision remains limited to its recorded interim handling approval. This register does not enlarge that authority.

## Governance boundary

This register does not authorize provider configuration, external integration, implementation, scoring changes, subscription-source qualification, or an exception to existing `FINAL` requirements. Such changes require the applicable explicit, durable governance decision.

## Verification note

This inventory was generated from files present in the local checkout immediately before publication. Remote durability is established separately by verifying the published commit and remote branch reference. This file alone does not claim remote publication verification.

## A10 Historical Reference Reconciliation

Historical decision: [A10 - A8-S Interim Subscription Handling](https://github.com/ramkivs/ipo-screening-engine/blob/9085bb6be74a2aa66fa9aaf91ddce557b7ba473c/handoff/decisions/A10-interim-subscription-handling.md)

Retrieved from commit `9085bb6be74a2aa66fa9aaf91ddce557b7ba473c`; blob `0500933b3578530cd30d1e548c97807e6b9dfbf9`.

The A10 record identifies three distinct baselines:
- Governing decision branch `arena/4e1080b7-ipo-screening-engine`: `71bbe81b0f4fa2c0f1c57751d9743a768d8597e5`
- `main`: `01ba66c12ca1195fd7acbd287c3e39a019808094`
- Supporting branch `arena/01a10b42-ipo-screening-engine`: `951d77d4ae39422c232fd727be89551aeb868ab4`

This reconciliation records provenance only. A10 remains approved for interim handling only; source qualification, implementation, Phase 1, and subscription scoring remain unauthorized.

---

## VNL HTML dual-identity amendment — APPROVED AND EFFECTIVE (2026-10-28)

**Disposition:** **APPROVED by RAMKI and EFFECTIVE 2026-10-28 (Asia/Calcutta).** The explicit
approval was supplied in the owner's execution directive titled “OWNER APPROVAL ALREADY
GRANTED.” This amendment applies the prepared A1 disposition without rewriting the historical
inventory entry above.

### Exact affected record

The affected inventory entry is only:

`evidence/ipo-subscription/vnl-20261011/vnl-issue-information.html`

No JSON/JavaScript payload identity, VNL value, A10 rule, source qualification, scoring rule or
`FINAL` consequence is included in this amendment.

### Competing byte identities and provenance

| Identity | Bytes | SHA-256 | Provenance and status |
|---|---:|---|---|
| **Original-capture identity recorded by the transfer manifest/register** | 313,040 | `2ae7009b9f30c026c91a1d38a4b943f348ab3f275f0b1b5b971481a8f72e78f2` | Recorded in `SHA256-MANIFEST.json` and this register. The matching bytes have **not been recovered**, so this remains a historical capture assertion rather than a currently verifiable artifact. |
| **First durable Git artifact** | 313,038 | `6beb26dc8acce2f9cd6620a761ec5d771da46b3214d220e6946bea37614f5ce6` | Git blob `21ea96b6f0f694d0a65076ce5bd4209c84558a7d`, introduced by source-evidence commit `951d77d4ae39422c232fd727be89551aeb868ab4`; current `main` and checkout carry the same bytes. Protected against future text conversion by `.gitattributes`. |

The repository-history disposition is recorded in
`docs/investigation/CONSOLIDATED-GEMINI-RECOMMENDATIONS-RECONCILIATION-2026-10-28.md`
§10.5 and tracker Revision 38. It bounds the discrepancy to the pre-commit capture/transfer/add
path. Line-ending transformation is evidenced for the manifest and is a plausible explanation
for the two-byte HTML difference, but the missing bytes and their positions are unavailable; no
cause is asserted as proved.

### Approved owner disposition

> Preserve the 313,040-byte / `2ae7009b…e78f2` identity as the **unrecovered
> original-capture identity recorded by the transfer manifest**. Designate the 313,038-byte /
> `6beb26dc…f5ce6` Git blob as the **durable retained repository artifact**, effective from
> commit `951d77d4`. Do not state or imply that the durable Git artifact is byte-identical to the
> original capture. Keep both identities visible and do not rewrite the original observation.

**Decision authority:** RAMKI under A1. **Decision:** APPROVE. **Decision date:** 2026-10-28
(Asia/Calcutta). **Authorization evidence:** the owner's explicit execution directive stating
that the existing VNL dual-identity amendment is approved and must be applied. This approval is
limited to evidence identity bookkeeping; it grants no source, provider, scoring, `FINAL`,
adapter, production or cache authority.

### Rationale

- The original identity must remain visible because deleting it would erase the transfer
  observation.
- The Git identity is the only artifact whose bytes are durably available and reproducible.
- Designating the Git blob as retained does not manufacture the missing original or conceal the
  discrepancy.
- The amendment changes evidence bookkeeping only. It cannot qualify NSE, establish a source
  contract, or confer licensing/implementation authority.

### Effective consequences

1. Repository-byte integrity checks may use `6beb26dc…f5ce6` for the durable HTML artifact from
   `951d77d4` onward.
2. Historical capture-chain claims must continue to report the unrecovered
   `2ae7009b…e78f2` identity and the pre-commit discrepancy.
3. The HTML may support code-path and retained-page observations only with this limitation. It
   cannot prove an unaltered source-to-capture chain, original responding host, retrieval
   headers/time, applicable terms, BSE identity, All Exchange composition, final-event semantics,
   or production/source qualification.
4. The seven matching non-HTML manifest artifacts are unaffected.
5. A later custody-backed recovery matching the full original hash must be preserved as a
   separate artifact and reconciled; it must not silently replace the Git blob.

### Continuing limitation

Two identities remain reported: the original bytes are unavailable, and the Git blob is
reproducible but not claimed capture-identical. The HTML remains non-authoritative investigation
evidence. This approved bookkeeping disposition does not make the evidence screenable and does
not authorize scoring, adapter, source-qualification or `FINAL` behavior.
