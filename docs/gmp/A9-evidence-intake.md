# A9 source-specific evidence intake specifications

2026-10-23. Ratified A28/A28.1, D1, D2, D3, A17 and bounded A18 control.
**This document is an intake checklist, not a new closed schema, identity contract,
source approval or production accepting path.** Unknown facts stay UNKNOWN.

## Contract status and current enforcement

| Requirement | Currently enforceable mechanics | Intake/review work, not automated authority |
|---|---|---|
| Source/observation identity | A18 exact source/issuer quote linkage, scoped manifest/artifact refs; A28 subject issuer/issue/source and explicit policy. Snapshot labels/ordinals are not publisher IDs. | Record actual source ID OR equivalent attributable observation/version traceability. Do not invent an ID/timezone or require provider-native IDs. |
| Locators | Exact A28 quote/locator representation; A18 verifies supported line quotes against retained bytes. | Preserve original URL, page/section/row labels, capture representation and excerpt boundaries. Proposed review columns are not canonical input fields. |
| Timing | A17 offset-aware source time, inclusive cutoff/24h; D2 complete window by cutoff; A28 representation checks relationships. | Explain timezone and whether stamp is observation, update, relay fetch or publication time. Capture clock/window is NOT source time. No earlier availability inferred from current history. |
| Corrections/revisions/withdrawals | Multiple supplied GMP candidates rejected; A28 pins applicable evidence/adjudications. Binding integrity alone cannot discover omitted disputes. | Preserve originals/changed records, relationship, reason, publication/effective timing, attributable source explanation and applicability. Missing notice is not evidence of no withdrawal. |
| Conflicts | Explicit-only, no fallback/latest/average; existing A1 safeguards. | Preserve competing declarations and actual authority/adjudication record. Empty lists, inferred precedence and a test-harness declaration do not establish resolution. |
| Provenance/independence | Publisher-reported capture is not authenticated dealer evidence. No automatic qualification. | Record upstream chain and relay transforms; shared upstream is not corroboration. HTTP200/parser success is not independence or approval. |
| Integrity/reproducibility | D1 file integrity; A28 digest; opt-in `verify_binding_files` verifies all declared exact-file pins within root, one read/resolved file per invocation. | Retain source material/method/bounds, raw declarations, scoped qualification evidence and immutable policies for replay. Local manifest/transcription hashes are NOT source signatures. |
| Trend | Absent UNKNOWN permitted; asserted publisher label must match supported linkage, no locally derived trend. | Preserve all competing labels and their scopes. Do not silently omit unsupported/conflicting assertions to manufacture absence. |
| Qualification/Final | Blanket A9 veto remains. New pin checker returns no authority/admission signal and has no pipeline consumer. | Evidence-backed RAMKI/PA scoped decision needed before genuine qualified positives/shared accepting verifier. Other outcome gates still apply. |

No mandatory digital signature, signed correction_history, composite observation
hash, new enum or closed-schema field is introduced. If a signature is supplied,
record what it purports to sign and unknown verification semantics; do not infer
key authority. No request for Q1–Q3 ratification is implied.

## MarketLiveIPOGMP intake

- Source/issue: retain named publisher and exact issue URL/title/offering terms;
  evidence cannot be borrowed across offerings. Preserve selected observation's
  value, percentage and publisher timestamp with exact locators.
- Time: explicit IST may be normalized with its stated offset; retain the raw
  stamp and normalization basis separately. Complete capture by cutoff AND source
  age within24h; historical source time cannot rescue late capture. The latest
  retained₹512/21Oct21:37IST was already expired at capture.
- R7: actual same-observation before/after records, same-stamp changes if any,
  publisher explanation, correction/revision/withdrawal identity, effective time,
  relevant competing records and attributable resolution. About promises alone
  do not demonstrate the mechanism.
- R8: dated prior captures/history/version records available by target cutoff,
  not just chart ranges/deltas or repeated unchanged page views. Equivalent
  attributable versions are acceptable; native bytes/IDs are not prerequisites.
- Provenance: dealer/cross-check assertions remain publisher claims. Request no
  dealer contact; do not count another shared-upstream display as independent.
- Custodian: publisher history/archive operator or existing dated-capture holder;
  records can arrive via existing permitted public route or supplied archive.

## InvestorGain intake

- Source: exact issue2369 URL/title, selected observation versus daily summary,
  intraday row and headline/FAQ. Quote raw labels and preserve each representation.
  Row1/row36 is positional, NEVER a stable observation ID.
- Time: source-provided timezone/year/event-role definitions tied to the selected
  record. Do not infer IST or equate last-updated with observation time. Record
  tool bounds separately and retain earlier availability evidence.
- R7: source version/correction/withdrawal trace, originals, changed value/time,
  relationship and effective timing; equivalent attributable identity is sufficient.
  Explain same-stamp differences and conflicting labels through source evidence
  and A1, not hash-based dedup/precedence.
- R8: the retained41-row and76-row views are bounded captures. Shared rows
  unchanged across them does not prove immutability or absence of intermediate
  withdrawals. Preserve earlier snapshots and applicable historical versions.
- Provenance: document upstream attribution without promoting affiliate/dealer
  claims to verified sourcing. PD/other IG relays are not independent corroboration.
- Custodian: IG source-data/archive operator or dated-capture holder. Unknown
  immutable source-version IDs/time semantics remain explicitly unknown.

## PapsDigital intake

- Source: retain exact relay URL/title and corresponding upstream source identity,
  observation and issue. Explain differing band/time/value representations.
- Time: source observation time, relay-fetch/publication time, timezone semantics,
  propagation delay/effective time and complete capture window separately.
- R7/R8: upstream AND relay versions/corrections/withdrawals/conflict explanation,
  preserved originals and historical availability, not day-wise summaries alone.
- Capture failure: retain forensic outage evidence separately; declared failure/
  known temporary-unavailability is `GmpEvidenceError`, not zero or withdrawal.
  Actual HTTP/DOM acquisition is external; unknown HTTP status is not invented.
- Independence: remains closed/non-independent IG relay. Reconsider independent
  status only on genuine new source evidence, never another copied reading.
- Custodian: PD relay/archive operator plus IG underlying-source custodian.

## Intake workflow and limits

Use [qualification packet template](../../handoff/templates/A9-qualification-packet.md).
Distinguish supplied/declared hashes from verified checks and their actual revision.
A28.1 raw-pin integrity checks do not validate locator semantics, authority,
source time definitions or completeness of declared disputes. A18 covers its
supported quoted format, not arbitrary DOM or all publisher histories.

No new acquisition endpoint/contact/access method is authorized. Do not poll
unchanged pages or repeat old audits absent new records or a concrete failure.
