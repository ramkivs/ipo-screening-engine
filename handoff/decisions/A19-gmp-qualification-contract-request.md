# A19 — GMP qualification contract resolution request

- **Decision ID:** A19
- **Status:** OPEN DECISION REQUEST — NOT APPROVED
- **Decision authority requested:** RAMKI / PA
- **Preparation date:** 2026-10-22 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Implementation baseline:** `e05c0efbca1ecb3024e52da73a22e180ea171118`, inherited without modification on `arena/07f3439f-ipo-screening-engine`.
- **Evidence-policy baseline:** `e8f9a28219aab69673c74e3b049729b77f1dfef5`.
- **Scope:** Shared A9 accepting path; not a source approval, scoring change or schema amendment.
- **Approved text:** NONE. No runtime authority or publisher qualification follows from this record.

## Authority reconciliation

A16 and the 2026-10-22 one-pass execution directive authorize routine preparation,
testing, documentation, publication and remote verification. They do not select
unapproved source semantics. A9 deliberately excludes provider selection and the
qualifying observation/hash representation. A17, D1–D3 and A18 settle narrower
contracts but never turn a linked observation into qualified evidence. GOV-001
provides this durable request mechanism. No synchronous PA decision service or
additional recorded ratification was found. Publication of this request is NOT
its approval; no repeated routine approval is being requested.

## Questions actually requiring disposition

| Decision | Why not already settled | Narrow recommendation (UNAPPROVED) | Dependent work |
|---|---|---|---|
| Qualification authority, scope and effective policy | Named publisher-reported Model A is not approval; no authorization signal is consumed by A9 | Retain an explicit authorized disposition, publisher identity, issue coverage, evidence and policy revision. Input authors cannot self-certify approval. Define temporal effectiveness; never retroactively imply missing historical approval. | Source approval, qualification validator, policy fixtures |
| Observation selection / correction semantics (PR-4f / PR-5) | Fail-closed on unresolved conflict is settled; resolving supersession/selection beyond withholding is not | Preserve settled withholding when conflict or correction leaves validity unresolved. Do not select newest/preferred capture, combine sources, or treat a withdrawal as zero. Specify authorized supersession and historical validity before selection is implemented. | Conflict/revision/selection admission tests |
| Required values and trend | A17 disallows derived trend, but A18 binds percentage/time only and rejects non-null trend | Prefer evidence-linked publisher label using existing accepted mappings if trend is required; reject unsupported/conflicting labels. Explicitly decide whether absent label permits qualification with UNKNOWN metric. No implicit relaxation or new mapping. | Trend linkage extension and accepting fixtures |
| Qualification signal and exact hash subject | D1 artifact bytes and A18 manifest hashes are defined, but neither is the A9 qualification subject | Ratify the bounded composite subject below; verify authorizing evidence as well as digest equality. | Accepting A9 branch, persisted qualification, hash-negative tests |
| Representation / compatibility | Input GMP is closed; A18 authorizes no new fields/version | Reuse existing evidence/source references where sufficient; separately approve any new input/output fields, enum meanings, digest subjects or versions. Never overload content_hash or VERIFIED as approval. | Schema, serialization and migration implementation |

These decisions do not approve MarketLiveIPOGMP or InvestorGain. Source approval
also depends on actual R7/R8 evidence. Failure to obtain that evidence remains a
separate blocker even after contract ratification.

## Proposed minimal hash and verification design — NOT an approved contract

The proposed required qualification digest would cover one immutable composite
subject containing ALL of:

1. The exact authorized qualification-disposition identity/content digest,
   publisher identity, covered issue scope, temporal effectiveness and referenced
   supporting evidence digests.
2. Issuer identity AND distinct offering identity, publisher issue URL, selected
   observation identity, exact signed percentage, publisher as-of instant, and
   required publisher trend label plus accepted mapping (or explicit absence,
   only if authorized). No delta-to-trend derivation.
3. The A18 source reference, exact pinned manifest digest, artifact identity and
   exact artifact-byte digest, evidence locators/quotes for identity/value/time
   and any newly authorized trend linkage, and the complete capture window.
4. Applicable immutable source/qualification/selection policy revisions and
   engine contract version, evaluation mode and explicit-offset evaluation
   cutoff, with the selection/revision evidence used at that cutoff.

Recommendation: ratify one canonical JSON representation of that subject,
UTF-8 encoded, hashed with SHA-256 using the existing canonical hashing facility
only after exact field names, types, decimal/timestamp normalization, optionality,
ordering and version are agreed. Those serialization details remain OPEN;
there is deliberately no executable hash formula or new input field here.
Artifact-byte hashing stays exact-byte hashing, not reconstructed Markdown.

Verification must independently reconstruct the subject from retained authorized
disposition, evidence and stable evaluation context; verify all references and
byte hashes; verify issue/value/label/time linkage; apply cutoff, freshness and
approved selection rules; then recompute/compare the required digest. A correct
digest over unauthorized or substituted evidence still fails qualification.

The subject must exclude the final result hash, derived evaluation ID, itself,
and mutable current approval state. The final record links its qualification
material after upstream verification. Replay uses retained policy/disposition/
evidence, not current publisher pages or approval-list contents. Missing or
altered dependencies fail verification; later revocation must not silently
rewrite earlier results. Any separate historical-revocation behavior needs an
explicit policy disposition.

## Evidence resolution and implementation boundary

See `docs/investigation/A9-GLOBAL-QUALIFICATION-CONTINUATION-2026-10-22.md`
for R7/R8 dispositions, recoverability, dependency sequencing and test readiness.
No accepting path is authorized by this request. Existing A9 withholding,
Preliminary behavior, scoring and all other gates remain unchanged. Approved
rendered captures remain usable under D1; provider-native bytes are not required.

## Response/closure mechanism

Record the actual authority response in this decision record (or an explicitly
superseding approved record), preserving the request and its evidence. Separate
publisher qualification must identify the evidence supporting R7/R8. Until both
are resolved, retain **OPEN — CONTRACT/IMPLEMENTATION GAP**. No implicit approval
is inferred from commit, PR, CI success, silence or a routine-work authorization.
