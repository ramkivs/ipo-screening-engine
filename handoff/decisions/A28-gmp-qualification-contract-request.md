# A28 — GMP qualification contract resolution request

- **Decision ID:** A28 (renumbered from PR #7's conflicting A19 request label; no semantic disposition)
- **Status:** Q1/Q2 RATIFIED; Q3 BOUNDED DESIGN AUTHORIZED — SOURCE QUALIFICATION STILL OPEN
- **Decision authority requested:** RAMKI / PA
- **Preparation date:** 2026-10-22 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Implementation baseline:** `e05c0efbca1ecb3024e52da73a22e180ea171118`, inherited without modification on `arena/07f3439f-ipo-screening-engine`.
- **Evidence-policy baseline:** `e8f9a28219aab69673c74e3b049729b77f1dfef5`.
- **Scope:** Shared A9 accepting path; not a source approval, scoring change or schema amendment.
- **Current approval:** explicit RAMKI choices in the ratification section supersede earlier open-request text. No publisher is qualified and no accepting path is enabled by this record.

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

These proposals do not approve MarketLiveIPOGMP or InvestorGain. Source approval
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

## Governance identity correction — 2026-10-22 continuation

The remote-tree recheck found that A19 was already assigned to the RAMKI-approved
K1 going-concern positive-evidence policy on `arena/95234306-ipo-screening-engine`
(and `arena/ae4d04e8-ipo-screening-engine`). Its record is
`handoff/decisions/A19-k1-going-concern-positive-evidence.md`, Git blob
`27ab99f470e93b2b6fa91e550b03ca3b83c0ec0c` at `e8f9a282…`.
That policy has no GMP qualification scope. A20–A27 are also already assigned.
All 19 current remote branch trees were checked; no A28 record was found before
this correction. GOV-001 requires unique IDs, so this OPEN GMP request is A28.
No existing approved decision is renamed, imported or modified.

Historical PR #7 references to the GMP “A19 request” mean this request only,
never the approved K1 A19 policy. The prior request remains retrievable at
`f3e1e0fe9d5e7c5305f9053a14a70cef3cdfae10:handoff/decisions/A19-gmp-qualification-contract-request.md`.
The renumbering neither ratifies the proposal nor changes any requested choice.
The status remains **OPEN DECISION REQUEST — NOT APPROVED**; approved text NONE.

## Bounded disposition — A9/A28 contract-disposition instruction, 2026-10-22

**Disposition authority:** Arena records settled requirements and engineering
findings under the user's current instruction, A16 and GOV-001. It does not act
as RAMKI to ratify new policy. This section is the current disposition; earlier
request/status text is preserved as history. The request's accepting-contract
choices remain unapproved. A19 continues to mean the separate K1 policy.

### A. Publisher authority and scope — settled safeguards

**Disposition:** retain Model A, one named publisher's reported observation,
without dealer-native/authenticated claims. Publisher qualification, observation
identity/timing, local integrity verification and Final eligibility are separate
judgments. No evidence verifier or input author can self-qualify a publisher.
RAMKI/PA is the governance route for an attributable substantive disposition;
Arena can assess evidence and prepare it, not silently grant approval. A1 already
resolves conflict-adjudication authority in RAMKI's favour; that question is NOT
being resubmitted. A1 does not itself qualify any publisher or delegate source
approval to Arena.

**Authority/rationale:** selected Model A source-policy section 1, A1 approved
items 1–6, A9, and A18 qualification limits. R1–R8 source-specific assessment
remains necessary. Rejected: treating a candidate, intact file, successful link,
allowlisted hostname, aggregator issue-term authorization or dealer claim as GMP
publisher approval. MarketLiveIPOGMP and InvestorGain remain NOT QUALIFIED.

### B. Selection, corrections, withdrawals and conflicts — bounded disposition

**Already settled:** preserve competing observations and provenance. Under A1,
a disputed canonical field stays non-screenable until RAMKI's attributable,
field-specific durable adjudication identifies the field, alternatives, evidence,
rationale, decision and date. No agent adjudication or majority vote. Never erase
the original. A specific conflict can therefore be resolved through A1 now if
actual evidence and RAMKI's adjudication are supplied; a new general authority
mechanism is not needed for that case.

| Condition | Defensible present disposition | Boundary |
|---|---|---|
| Identical returned text across retrievals | Limited returned-text stability only | Does not establish append-only history or absence of corrections |
| Changed value under same publisher stamp | Incompatible assertions; preserve both, withhold while unresolved | Do not infer which is corrected, authentic or applicable |
| Explicit revision/correction | Preserve original, changed record, publisher explanation and timing | Do not automatically infer whether it supersedes historically or prospectively |
| Withdrawal | Preserve withdrawal evidence; never turn it into numeric zero | Do not keep using a reading whose continued applicability is unresolved |
| Conflicting observations | A1 non-screenable pending attributable adjudication | No latest-capture, majority, preferred-host or cross-source averaging shortcut |
| One unambiguous captured observation | Identity/integrity/cutoff checks may pass | No publisher approval or Final admission follows |

**PR-4f:** unresolved-correction/conflict withholding follows existing safeguards;
a blanket rule that *every* same-stamp correction permanently disqualifies an
observation/publisher is NOT adopted. **PR-5:** publisher-reported labelling is
settled; a general automatic single-source/fallback/corroboration and precedence
policy is NOT adopted. Model A is not such a selection algorithm. Deterministic
successful selection still needs an explicit policy describing the eligible set,
same-time ties, corrections, withdrawals and effective historical versions.
Until then, do not implement selection by list order or newest retrieval.

**Evidence status:** retained copies contain no actual same-stamp mutation,
correction/withdrawal trail or complete earlier-reading history. The Hero Motors
prelisting/final timestamp inconsistency remains adverse but unexplained. No
claim about its cause is adopted. PR-4f/PR-5 cannot be settled by inventing events.

### C. Required fields and trend — current contract settled, admission choice open

**Operative disposition:** exact percentage and explicit-offset publisher as-of,
issuer/title and source/evidence linkage use A18. A17 maps only unambiguous
publisher-supplied labels; absent, unsupported or conflicting labels remain
UNKNOWN/unqualified trend. Never derive trend from movements/history. A18's
current evidence contract binds no trend label and its non-null-trend rejection
must remain intact. Null trend may produce a VERIFIED *link*; that is neither a
qualified publisher nor a Final-eligible observation. The current code/tests are
consistent with these rules and require no corrective runtime change.

**Precisely unresolved:** whether an otherwise legitimately qualified observation
with absent trend may pass A9 while trend remains UNKNOWN, or trend is mandatory
for admission. A17 fixes meaning, not this admission rule; A18 explicitly leaves
A9 fail-closed. Adopting either branch changes successful-Final semantics. The
current instruction advances disposition but supplies neither choice nor an
explicit supersession of those limits. It is not an implicit policy ratification.

**Narrow recommendation, NOT adopted:** decide this Boolean admission requirement
explicitly before introducing trend linkage. If mandatory, authorize exact-label
locators/quotes and accepted mapping linkage; if optional, encode absence
explicitly, preserve UNKNOWN scoring and still reject unsupported/conflicting
asserted labels. No new mapping, inferred label or silent change to A18.

### D. Signal, required hash and replay — relationship fixed, contract open

**Confirmed separation:** a future authorized publisher disposition must be
checked within its actual scope; a selected observation must be tied to that
publisher, issuer, distinct issue and retained evidence; A17/D2 timing and the
applicable evaluation context must be verified; A9 may then cease its own veto
only if the ratified required qualification binding passes. Other gates still
apply. The A18 VERIFIED result, D1 artifact digest, A18 manifest digest and generic
market snapshot digest do not implement that signal.

**Hash subjects actually authorized now:** D1 = exact retained rendered-file
bytes, SHA-256; A18 = exact pinned manifest bytes and declared artifact bytes,
recomputed and labelled local raw-artifact integrity. These are not undefined and
are not being resubmitted. There is NO approved exact A9 qualification subject,
qualification signal or deterministic serialization. No formula/field name is
promoted from the earlier proposal to approved status in this disposition.

The proposed composite material above is the narrow engineering recommendation:
authorized disposition/scope and evidence, specific publisher/issuer/issue and
selected observation, values/labels/time, capture and manifest/artifact pins,
selection/version evidence, and immutable policy/evaluation context. Exact field
names/types, decimal and timestamp normalization, optionality, canonical byte
encoding and contract version need one explicit ratification; “use a JSON hash”
is not sufficient. Correctly hashing unapproved material cannot authorize it.

**Replay/invariants retained:** immutable evidence and raw conflicting declarations
must survive; replay cannot silently consult today's publisher page or rewrite
old approval/results. Existing result hashes/IDs and schemas remain unchanged.
The recommended new upstream subject excludes itself, result hash and the derived
evaluation ID; policy/evaluation cutoff can be fixed before results, then linked
by the final record. This acyclic design is a recommendation, not an implemented
or approved new digest. Do not add closed-schema fields, overload content_hash,
or bump a version until representation authority is explicit. Whether extension
is necessary depends on the ratified representation; no schema change is assumed.

### E. Evidence dependencies — exact scope, no new discovery

Publisher qualification needs actual evidence of correction/withdrawal/revision
behaviour, same-stamp handling, conflicts and retained historical readings under
R7/R8, together with the already bounded R1–R6 findings. Publisher statements
must remain labelled claims. A capture of the stored readings/attributable
version archive could address these questions if it exists; a later mutable page
or repeated identical capture cannot manufacture missing earlier availability.
The source/evidence custodian owns those records; Arena can assess supplied
records or a specifically permitted retrieval route. No new route/archive was
identified in the published baseline, and no new capture was obtained here.

A genuine positive evaluation additionally needs a specifically scoped authorized
publisher disposition, applicable issue/observation evidence captured by its own
cutoff, publisher time within the inclusive 24h window, required value/trend
semantics, and the ratified qualification binding. Multi-issuer/issue positives
must use real supported observations, not mutations granting synthetic approval.
The Tonbo October15 capture is expired for later evaluations. D1 rendered text
remains acceptable; provider-native bytes are not a prerequisite.

### Remaining authority decisions — isolated, not a routine-work hold

| Item | Exact ratification needed | Owner / downstream dependency |
|---|---|---|
| Q1 | Successful selection/precedence, revision/withdrawal applicability and any automatic fallback/corroboration rule beyond A1 withholding/adjudication | RAMKI/PA; selection engine and correction/replay positives |
| Q2 | Trend mandatory versus explicitly optional/UNKNOWN for A9 admission, plus any required trend-link extension | RAMKI/PA; accepted-observation fields and trend tests |
| Q3 | Scoped publisher-qualification authorization consumed by A9, exact qualification subject/serialization and retained policy/evaluation binding; compatibility extension only if necessary | RAMKI/PA; accepting branch, digest verifier, schemas and qualified replay |

Independently, source/evidence custodian must supply sufficient R7/R8 evidence.
Neither a decision nor a checksum creates it. No conditional implementation
prerequisite is satisfied by this bounded disposition. Routine investigation,
preparation and validation remain authorized; no repeated routine approval is
requested. **A9: OPEN — CONTRACT/IMPLEMENTATION GAP.**

## Final continuation: mechanical consequences and evidence handoff

No newer ratification was present at the verified PR #7 starting head
`1459731f0231c6f236e42ed04e76fcd54869692d`. A28's bounded disposition stands;
this continuation grants no new policy and leaves Q1–Q3's exact open choices
unchanged. A19 is not a GMP approval.

- **Q1 mechanical consequence:** identical captured text supplies no precedence
  or revision fact. A1 withholding/adjudication applies to actual disputes; an
  automatic successful-selection rule remains a new substantive choice. Missing
  correction/withdrawal histories are evidence gaps, not authority requests.
- **Q2 mechanical consequence:** absent labels stay UNKNOWN; A18's null-trend link
  can verify while A9 remains withheld. A17 supplies no successful-Final rule for
  absence. Neither mandatory nor optional admission can be inferred from that
  existing component behaviour. Actual publisher labels are evidence; choosing
  their necessity for admission is the remaining policy decision.
- **Q3 mechanical consequence:** an external pinned capture must be rechecked,
  not trusted merely because a stored link once verified. Existing store-hash
  verification certifies the store, not today's external manifest/artifact bytes.
  New tests demonstrate these distinct integrity boundaries without defining a
  qualification hash. Exact-byte hashing and existing linkage replay are fixed;
  an authorization signal, composite subject/serialization and qualified replay
  representation remain unratified. No new field or digest meaning is adopted.

### Exact evidence acquisition handoff (existing retained baseline)

All paths below are relative to
`evidence/gmp-observations/marketliveipogmp-tonbo-20261015/`.

| Requirement | Retained artifact and demonstrated fact | Unproven / exact record needed | Custodian / permitted route |
|---|---|---|---|
| Publisher qualification | About/issue rendered captures establish named publisher and stated methodology; assessment preserves bounded R1–R6 passes | Completed R7/R8 evidence assessment AND attributable scoped qualification disposition, not merely page integrity | Publisher owns underlying records; RAMKI/PA owns qualification disposition; Arena assesses supplied evidence |
| Observation identity/value | `source-captures/marketliveipogmp-ipo-tonbo-imaging-india-chunk-0.md`: Tonbo context, ₹500/+71.4%, explicit publisher stamp | Distinct-issue evidence for every new offering; no cross-issuer or cross-offering borrowing | A genuinely issue-specific permitted capture, retained with locators; no new capture obtained here |
| Observation/capture timing | `capture-manifest.json`: complete bracket ending October15 13:17:58.770Z; publisher stamp October15 10:32Z | An actual observation/capture appropriate to each requested later evaluation; earlier availability cannot be backfilled | Previously obtained capture with honest window at/before the cutoff, or a new capture for a genuinely new cutoff through an identified authorized route |
| Same-stamp change / correction / revision | About promises and byte-identical recapture declarations only | Actual before/after records, observation identifiers/stamps, correction declaration, what changed and timing; preserve old version | Publisher/site archive custodian; supplied archive/captures or specifically authorized public history retrieval if identified |
| Withdrawal | No retained withdrawal example | Actual withdrawal notice identifying affected observation and when it ceased applicability, with original preserved | Publisher/archive custodian; no demonstrated archive/endpoint in current evidence |
| Conflict / precedence | Cross-check claims, no traceable competing-reading resolution; Hero Motors assurance/timestamp inconsistency unexplained | Competing scoped observations plus source explanation and any RAMKI A1 adjudication; auto precedence additionally requires Q1 | Source custodian supplies facts; RAMKI adjudicates, Arena does not select by majority/latest |
| Historical reproducibility | Exact captured bytes reproduce one observation; chart reading list is absent | Retained identifiable historical readings and versions plus independently established availability at the relevant cutoff | Publisher/archive custodian supplies dated history; later mutable page alone is insufficient |

D1 rendered captures remain acceptable. No provider-native bytes are imposed.
The historical Tonbo timing-only interval ended October16 10:32Z and cannot
support a later Final. No new evidence, public-history endpoint or permitted
external acquisition route was discovered or assumed in this continuation.
A checksum does not qualify the publisher, and a ratified policy would not create
missing historical evidence. Conditional accepting implementation remains blocked
only on its concrete authority/evidence dependencies, not routine engineering.

## RAMKI/PA ratification and bounded design delegation — 2026-10-22

**CURRENT CONTROLLING DISPOSITION:** Q1 and Q2 RATIFIED; Q3 bounded technical
representation/design AUTHORIZED and specified below. Earlier OPEN statements
are historical and superseded only to this extent. No publisher is approved.

**Authority:** in the current Arena question interaction RAMKI selected:

- Q1 `explicit_only`: “Explicit observation; no automatic fallback”. Use only the
  explicitly referenced evidence-bound observation. No latest-reading selection,
  source fallback or averaging. Preserve competing versions; unresolved conflicts,
  corrections or withdrawals withhold admission until attributable A1 adjudication
  establishes applicability.
- Q2 `optional`: “Allow absent trend as UNKNOWN”. Absence may pass A9 only if ALL
  other qualification requirements pass; scoring keeps UNKNOWN. Asserted trend
  must be publisher-supplied and evidence-linked under the bounded A18 extension;
  unsupported/conflicting assertions fail closed. No derived trend.
- Q3 `delegate`: “Authorize bounded Q3 design”. Exact fields, deterministic
  canonical-JSON/SHA-256 and minimum versioned compatibility extensions may bind
  authorized publisher disposition/scope, issuer/specific issue, selected
  observation, exact evidence/manifest/artifact pins, immutable policy versions
  and evaluation cutoff. Retain replay dependencies; exclude digest itself,
  result hash and derived evaluation ID. No publisher approval, scoring/freshness
  or other-gate changes. Publish exact contract and validate it before dependent
  implementation. This is explicit substantive authority, not inferred silence.

### Exact delegated representation: A28.1

An optional standalone artifact `gmp-qualification-binding.v1.json` has exactly
`subject` and `sha256`. It is NOT added to canonical input or A15. Existing closed
schemas and historical readers remain unchanged. No engine consumer/admission
branch is enabled by defining it. Its normative closed schema is
`schema/gmp-qualification-binding.v1.schema.json`.

The exact hash subject is `subject` ONLY, with these required members:

| Member | Exact material |
|---|---|
| `contract_version` | Constant `A28.1` |
| `publisher_id`, `issuer_id`, `issue_id` | Nonempty stable identities; issuer and offering remain distinct |
| `publisher_issue_url` | Explicit HTTPS issue URL |
| `qualification_decision` | Pin `{ref, sha256}` to actual attributable approved publisher disposition |
| `qualification_scope` | Pin `{ref, sha256}` identifying its exact scope, including issue and temporal applicability |
| `qualification_evidence` | Nonempty pins to supporting R1–R8 records |
| `observation` | `{source_id, pct, as_of, trend}`: exact decimal string; publisher instant; mapped `strong`/`flat`/`falling` or null |
| `evidence` | `{manifest, artifact_id, artifact, capture_start, capture_end, identity_quote, pct_quote, as_of_quote, trend_quote}`; manifest/artifact are exact-byte pins; quotes are `{locator, quote}`; trend quote null iff absent |
| `selection` | `{policy, adjudications}`; policy constant `explicit-only-a1`; pins to every applicable A1 adjudication, possibly empty only without unresolved disputes |
| `context` | `{evaluation_at, mode, engine_version, spec_version, config_sha256, policy_refs}`; mode `FINAL`, immutable applicable policy pins |

Pins identify repository-relative retained files, optionally a fragment, and a
lowercase SHA-256 of the WHOLE exact file bytes (fragment selects semantic scope,
not a different byte subject). Arrays of pins are lexically sorted by `ref`,
unique by ref; ordering is not a priority signal. All object properties are
required, unknown properties rejected; nullable absence is explicit. Strings
must already be NFC. Percentage is a plain base-10 string, no exponent/leading
plus/leading zeros/trailing fractional zeros/negative zero; nonzero and within
existing input percentage bounds. No new positivity policy is introduced.
Instants are UTC `YYYY-MM-DDTHH:MM:SS.ffffffZ` with exactly six fractional digits;
conversion must start with an explicit-offset source instant, never guessed UTC.
Quote text/locators retain exact publisher evidence, not reconstructed values.

**Canonical bytes:** existing `hashing.canonical_json(subject).encode('utf-8')`,
canonical grammar `1.5.0` (NFC, sorted keys, separators comma/colon, no whitespace).
Subject numbers are strings, avoiding binary-float ambiguity. `sha256` equals
lowercase SHA-256 hex of those bytes; no prefix. Envelope, digest, result hash and
evaluation ID are excluded. This uses, but does not change, existing hashing.
Version/grammar changes require a new contract version, not silent reinterpretation.
D1/A18 retained artifact bytes are always hashed exactly, not NFC-reconstructed.

### Verification, authority signal and replay semantics

The eventual qualification signal is an INTERNAL verified decision, not an
input approval Boolean: actual attributable approved publisher disposition AND
its issuer/issue/time scope, R1–R8 evidence, bound explicit observation, policy
versions and evaluation context all pass, with recomputed qualification digest.
No record ID, hostname, digest equality, schema validity or A18 VERIFIED status
by itself produces that signal. Open requests and invented approval records fail.
A28 ratification is NOT itself a publisher disposition.

Before successful admission, read each pinned file once and recompute its exact
raw digest; validate authority/scope, evidence semantics, actual identity/value/
time/trend and snapshot equality. Validate A17's inclusive cutoff/24h and D2's
complete capture window. Apply Q1 including all competing declarations and relevant
revision/withdrawal/adjudication records; an empty adjudication list cannot prove
absence of conflicts. A mechanically well-formed envelope with invented record
pins never authorizes Final. Binding tooling in isolation checks representation,
relationships and digest only, and must say so explicitly.

Replay retains the envelope and EVERY exact referenced byte plus raw declarations
and applicable authority/policy evidence. It must not query mutable pages/current
approval lists or reconstruct missing prior availability. Verification failures
remain failures; replay never mutates the original record. Missing/corrupt policy,
authority or external evidence fails verification. Qualification must be upstream
of result hash/derived evaluation ID; persist/link after verification. Retroactive
revocation/adjudication is never silently applied to rewrite historical results.

### Bounded A18 trend extension

Reuse `_evidence['market.gmp.trend']`, canonical ID `EV-market.gmp.trend`, same
source, exact `line <n>` locator and MANUAL_ENTRY quote. Supported rendered layout
is a single unambiguous `Trend: <publisher label>` line; quote is the exact label.
Reuse A17's existing label map (case-insensitive/trimmed only). Multiple trend
lines, unsupported labels, contradictory aliases, quote/value mismatch or missing
asserted-label evidence fail linkage. If input trend is absent, trend evidence
must also be absent; no hidden asserted label is ignored. Null trend retains
legacy three-field linkage; declared trend adds the fourth evidence reference and
projection/replay checks. Existing unlinked/historical inputs are unchanged.
This extension authorizes label linkage only, never source qualification/scoring.

### Implementation sequencing / remaining evidence boundary

Publish this exact contract first; validate its schema/serialization and trend
extension. Implement those independent bounded components with mechanical unit
fixtures (not qualified positives). Do NOT add an accepting A9 branch until real
R7/R8 evidence permits an attributable publisher qualification and genuine
multi-issuer/issue baseline. MarketLiveIPOGMP and InvestorGain remain NOT QUALIFIED;
PapsDigital remains closed/non-independent. Source/archive custodian still owns
the exact missing records in the evidence handoff above. **A9 remains OPEN —
CONTRACT/IMPLEMENTATION GAP**, now for source evidence/qualification and dependent
accepting implementation, not unresolved Q1–Q3 policy delegation.
