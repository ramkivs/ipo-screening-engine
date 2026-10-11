# A8-S Evidence Acquisition Register

## Purpose

This register inventories subscription-related evidence preserved in the repository and records the limitations on what that evidence establishes. It is a documentary evidence artifact, not a source-qualification or implementation authorization.

## Repository and publication context

- Repository: `ramkivs/ipo-screening-engine`
- Supporting branch: `arena/01a10b42-ipo-screening-engine`
- Verified parent commit: `951d77d4ae39422c232fd727be89551aeb868ab4`
- Related governance decision: `handoff/decisions/A10-interim-subscription-handling.md`
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