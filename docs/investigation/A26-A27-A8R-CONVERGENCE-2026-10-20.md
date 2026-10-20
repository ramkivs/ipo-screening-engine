# A26 / A27 / A8-R — bounded convergence specification and audit

Date: 2026-10-20. Baseline: `d64cd4a`. No runtime implementation.

## 1. Authority and disposition

**AUTHORIZED / RECORDED:** the current one-pass instruction authorizes this
specification, non-scoring audit, tests, tracker reconciliation and publication.
It explicitly adopts A26's safe interim disposition: tax-only proceedings that
cannot reliably fit an approved bucket remain **UNKNOWN**, not zero, clean or
automatically adverse. Independently supported K5 and auditor treatment continue.
This is not a permanent tax-scoring decision. A26's broader calibration remains open.

**UNCHANGED:** current K2 policy; external evidence gains no authority to trigger
or clear it. Existing scoring, penalty magnitudes, schemas, configs, fixtures,
historical records and A24/A25 implementation remain protected.

**PROPOSED / NOT APPROVED:** future CARO consumption, evidence sufficiency rules
that would change a scored result, exact replacement config wording/version,
new fields/source types/connectors, and external knockout authority. Preparing
acceptance criteria below does not approve those changes. This document supplements,
not rewrites, the earlier decision-preparation report and decision records.

## 2. A27 — bounded CARO/EOM specification

### 2.1 Verified current baseline and precision corrections

`engine/ipo_screening/derived.py:1428–1498` consumes only auditor opinion,
reputation, changed-3y and repeated-EOM. Branch order today:

1. Opinion absent: UNKNOWN.
2. Qualified/adverse/disclaimer: NOT_APPLICABLE for criterion; K1 handles knockout.
3. Auditor-change flag absent: UNKNOWN, even if repeated-EOM is true.
4. Change true or repeated-EOM true: unstable_or_repeated_eom.
5. Unqualified and reputed true: clean_reputed (2/2).
6. EOM opinion or unqualified: eom_only (1/2), except unqualified with reputation
   absent remains UNKNOWN. Unqualified with reputation false reaches the middle tier.
7. Anything else: UNKNOWN.

CARO does not influence these branches. Clean 2/2 therefore remains possible
with CARO remarks when the other prerequisites hold. The authoritative criterion
still names EOM/CARO (`handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md:547–558`).

`derived.py:1500–1513`, `scoring.py:580–608`, and
`config/ipo-config.v1.5.0.json:1400–1407` establish:

| Supplied eom_materiality | Current state | Applied points | Unresolved reserve |
| --- | --- | --- | --- |
| none | SCORED | 0 | 0 |
| absent or null | UNKNOWN | 0 | 3 |
| low | SCORED | -1 | 0 |
| medium | SCORED | -2 | 0 |
| high | SCORED | -3 | 0 |

Reserve is used in lower-bound construction; it is not a penalty applied to the
base score. The runtime does not independently verify a supplied `none`.
The schema recognizes none/low/medium/high/null (`schema/ipo-input.v1.5.schema.json:637–644`).
The extractor has no materiality producer; the builder carries supplied materiality
(`engine/ipo_screening/extraction/builder.py:353–363`). An explicit EOM denial
can establish repeated_eom=false (`tests/test_auditor_tenure_defaults.py:107–124`),
not a reviewed CARO clearance or materiality=none.

Corrections/qualifications to earlier report language: a raw `none` means a supplied
value, not independently verified “checked and clean”; absent CARO does not
currently make the auditor bucket UNKNOWN. A proposed future UNKNOWN rule cannot
be described as preserving all current absent-input scores. Config and code
formula strings differ: only the code string is embedded in derived/score artifacts;
config text affects result hashes through config_hash. No general “every schema
field must have a scoring consumer” lint is adopted.

### 2.2 Six evidence states — proposed semantic contract, not new schema values

| State | Evidence requirement / interpretation | Future consumption constraint |
| --- | --- | --- |
| Explicit reviewed-none | Identified reviewer, scope, readable annexure, locator, quote and review basis; no relevant remarks found in that scope | Candidate negative only after sufficiency policy approval; never manufacture none from silence |
| Missing | No input supplied / review not established | Preserve missing; no false or none substitution |
| Ambiguous | Unclear scope, remark classification, identity or conflicting text | Preserve reason; no clean inference |
| Unavailable | Annexure absent, unreadable, blocked or only partly read | Record retrieval/readability failure; no clean inference |
| Explicit filing denial | Verbatim issuer/auditor sentence, scoped to EOM or CARO and period | Disclosure-negative only; EOM denial does not clear CARO; not independent verification |
| Present CARO remarks | Located annexure and actual remark quote, party, period and subject | Presence does not itself establish adversity or materiality; assess remark relevance under approved rules |

These states can be described in existing evidence/notes for specification purposes;
there is no six-state enum added to the input. A boolean alone cannot encode scope
or distinguish an irrelevant remark from a material adverse one. Reviewer evidence,
source statements, and extraction conclusions must remain distinguishable.

### 2.3 Future branch precedence and implementation gates

**Proposed target precedence:** preserve branches 1–4 above (including existing
unknown-change precedence); then evaluate a policy-qualified CARO finding before
the clean branch; then retain existing reputation/EOM branches. Relevant CARO true
would select the existing middle tier, not a new category. No renaming is authorized.
K1 remains independent; CARO cannot rescue a qualified opinion. Materiality remains
a separate assessment with existing -1/-2/-3 magnitudes; no automatic magnitude
from a CARO boolean. EOM can already affect both criterion and penalty; do not
add tax-litigation pricing on the same fact without its own policy.

**Actual unresolved scoring boundary:** choosing whether missing, ambiguous or
unavailable CARO blocks clean_reputed changes current scores. Two target options
remain explicitly open: (a) compatibility mode keeps old branches for absent CARO,
while disclosing incomplete CARO coverage; (b) evidence-complete mode makes the
CARO-dependent criterion UNKNOWN until coverage is established. Neither is applied.
Also unresolved: which CARO remarks qualify, reviewed-negative sufficiency, and
whether positive CARO can bypass missing reputation. Proposed precedence would
allow a qualified positive before reputation; that choice requires policy approval.

Future acceptance tests (requirements, not claims of implemented behaviour):

- Qualified/adverse/disclaimer + each CARO state: K1 unaffected; no clean score.
- Missing opinion/change and change/repeated true crossed with CARO states:
  preserve agreed precedence; explicitly test missing-change + repeated true.
- Unqualified/reputed/no change + qualifying positive: selected approved middle tier.
- Explicit denial vs reviewed-none vs missing/ambiguous/unavailable: distinct evidence;
  no automatic materiality=none. Test each absent-input policy option before selection.
- Positive remark irrelevant/material/uncertain: classification and reason preserved.
- Materiality none/null/absent/low/medium/high: exact table above remains pinned.
- EOM denial must not set CARO false; partial/scanned annexure cannot support negative.
- Reviewer-supplied and extracted evidence: preserve locators, quotes, provenance.
- Count fields and flags disagree: report discrepancy in proposed audit, never silently
  derive or override a flag. Test extraction-builder versus direct-input pathways.
- Old-version golden remains untouched; any new-version baseline is separately approved.

### 2.4 Prospective wording options and hash calculation

Both shipped configs at line 1727 imply disputed-tax consumption; no engine
consumer exists. Only in-memory copies are used for the following options.
The exact candidate strings are in the hash table below; neither is adopted.

W1 (recommended interim truthfulness): describe actual current branches and
explicitly disclose both unconsumed inputs. W2: retain intended CARO criterion
while distinguishing its current implementation gap. W2 must not be presented
as executable behaviour. Both remove implied disputed-tax consumption.

`config_fingerprint` hashes all config content except runtime annotations
(`engine/ipo_screening/config_validation.py:771–783`). Formula text alone changes
the fingerprint; assigning a real future version additionally changes it. The
calculated hashes below keep existing version identifiers solely to isolate
wording impact, and are NOT deployable new-version identities.

| Copy of config | Baseline config hash | W1 wording-only hash | W2 wording-only hash |
| --- | --- | --- | --- |
| 1.5.0 | `4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b` | `32e05c591838d6e098adacd430f1f264c1037855f5693d16dbef4c34496fe55c` | `58f93937f06fb44baf5cc88f07fcfa494ce3ad6b2040e4112f26cbc85da14d9f` |
| 1.6.0 | `3d08816e6ee6cd70a1d5046eb178fea4a835628fa0dd8bf681d57d9b04a8bd86` | `0d39cdc2ecfdfaa55a9239ba3fe61fd46517dda6d45c518b5a785c7b17282f6a` | `834329772013386379adbe5c6e65b14ed55fb3e7085bc34678ba3012cfa7fee5` |

**W1 exact candidate:** Current implementation: auditor opinion, reputation, auditor_changed_3y and repeated_eom determine auditor_bucket. CARO remarks and disputed tax are not consumed. Qualified/adverse/disclaimer opinions are handled by K1.

**W2 exact candidate:** Intended criterion includes EOM/CARO only. Current implementation does not consume caro_remarks; disputed tax is not a scoring input. Existing auditor branches remain unchanged pending separately approved CARO policy and implementation.

Result-hash impact is exact in dependency, not a newly evaluated result:
`H(new result payload) = compute_result_hash(old payload with config_hash replaced)`
when everything else stays equal. `evaluation.py:275–290` includes config_hash.
All four wording-copy hashes differ from their baselines. A new numerical result
hash cannot responsibly be supplied without the complete deterministic result
payload; no historical evaluation is rerun or fabricated here.
`tests/test_vishal_golden.py:46–57` pins the old result hash. Updating its config
in place would break that pin even with score delta 0. A config-text-only edit
does not change code formula strings in expected_derived/expected_score; a code
formula edit does. Keep old-version tests/records replayable; introduce separately
approved new-version tests rather than rewriting old expectations. RUNBOOK
`docs/RUNBOOK.md:380–396` explains versioning and historical hash consequences.
No future version number is allocated by this specification.

## 3. A26 — recorded interim disposition and corpus protocol

**Adopted by this task instruction:** unsupported tax-only classification stays
UNKNOWN. This records a safe interim posture, not a newly implemented rule.
Do not replace a valid independently established criminal/civil/regulatory finding
with UNKNOWN just because tax is also disclosed. K5 uses its existing quantified
and unquantified liability rules; tax existence alone does not establish them.
Likewise, a tax dispute alone supplies neither an audit qualification nor materiality.

Verified basis: `derived.py:1382–1395` reads supplied litigation_bucket, while
`tests/test_litigation_regulatory_defaults.py:379` distinguishes tax/civil from
regulatory action. `config/ipo-config.v1.5.0.json:1314` onward defines K5.
The earlier report §2 documents no calibrated tax-only scored state and no
contingent-liability criterion among the 30 criteria. Its PDF probe had no detected
summary-table headers: no prevalence denominator or estimate can be derived.

**Corpus acceptance protocol (no corpus collected in this pass):**

1. Predeclare a representative sampling frame by issuer, industry, board,
   filing stage/date and document availability; deduplicate filings/amendments.
   Record exclusions, inaccessible/scanned pages and unresolved classifications.
2. Preserve source identity, filing hash, page/table/row, quote, date and reviewer.
   Separate issuer, promoter, director, group company and unrelated parties.
3. Label against/by direction; tax category, disputed/settled/appealed/active
   status, alleged conduct versus assessment, event date and outcome.
4. Record amounts, units, aggregation/overlap, period and net-worth denominator;
   distinguish nil, missing, unquantified, disputed and amounts paid under protest.
5. Link each fact to independently established K5, EOM/CARO and existing litigation
   findings. Do not assume one dispute equals one independent risk signal.
6. Double-review ambiguous rows and record adjudication/disagreement. Measure
   parser recall/readability and report coverage before any prevalence figure.
7. Report tax-only and mixed cases with explicit denominators and uncertainty;
   do not treat inaccessible records as clean or extrapolate from table-detection failures.
8. Only then assess distinct predictive/decision value and calibration, comparing
   UNKNOWN, a factually justified existing classification, and a separate dimension.
   Backtesting on a new approved research dataset requires separate authority;
   no historic evaluation record is to be overwritten.

Completion here is the interim disposition and executable research requirements,
not prevalence measurement, tax calibration or approval of a new dimension.

## 4. A8-R — external-evidence acceptance specification

### 4.1 Six states, none granting new K2 authority

| Evidence state | Required interpretation | K2 consequence in this pass |
| --- | --- | --- |
| Issuer says no action | Disclosed negative, scope and period retained | Current approved in-document policy only |
| In-document search finds no action | Search fact; unread/absent section is not proof | No expanded authority |
| Completed authoritative external search with adequate coverage | Candidate corroboration, not universal absence | No new trigger/clear authority |
| Failed/incomplete/blocked/empty external search | Diagnostic; empty results without coverage do not prove absence | No new trigger/clear authority |
| Positive action located | Preserve order, identity, status and quote; escalate for review | No automatically imported external trigger |
| Conflicting findings | Preserve both; unresolved without approved precedence | No silent external override |

K2 reads a bare flag (`config/ipo-config.v1.5.0.json:1224` onward); it cannot
currently distinguish reviewer/extracted false on the governance scalar alone
(`canonical_input.py:136–137`). The no-new-authority constraint is governance for
this pass, not a claim that runtime enforces an external-source gate.
A25's disclosed-negative test remains the in-document limit
(`tests/test_litigation_regulatory_defaults.py:483`).

### 4.2 Existing carriers first — fit and gaps

- `_sources[]` already carries source identity, URI, hash, source and retrieval
  timestamps (`schema/ipo-input.v1.5.schema.json:214` onward, `:1095` onward).
- `_evidence{}` supports path-linked quotes/locators; use existing carriers when
  semantically valid, but do not attach external findings to the active K2 flag
  in a way that silently changes it. Descriptive captures can remain separate
  governed research artifacts pending an approved integration contract.
- `_cross_checks[]` and `semantic_validation.py:411–446` provide numeric
  incomplete/divergence diagnostics, not a categorical regulator conflict resolver.
  Do not coerce action conflicts into numeric values to reuse this mechanism.
- `schema/supplemental-enrichment.v1.schema.json` has hashes and dual timestamps,
  but no regulator source type and closed section shapes. Existing carriers do
  not by themselves authorize a regulator mapping or new enum member.
- `connectors/interfaces.py:37–45` has no regulator class. `canonical.py:42–61`
  distinguishes verification and extraction method; VERIFIED is not publisher
  authentication. A hash establishes captured-content identity, not completeness.
- `docs/RUNBOOK.md:530–531`: the scoring engine never makes a network call.
  Any later retrieval must be upstream and separately specified/authorized.

### 4.3 Acceptance matrix for a future upstream contract (not a network design)

| Requirement | Acceptance case / failure posture | Authority still needed |
| --- | --- | --- |
| Independent SEBI and ED | SEBI complete + ED unavailable is incomplete combined coverage; neither substitutes for the other | Named source set for each regulator |
| Authority and identity | Official-looking host, aggregator or HTTP 200 alone insufficient; record publisher/index purpose | Approved authority set and scope |
| Issuer/party matching | Exact identity plus approved alias/entity evidence; identical-name sister entity cannot establish an action or clearance | Covered parties and matching standard |
| Relevant period/status | Record event period, publication date, evaluation as-of and active/closed status separately from retrieval time | Active-action definition and freshness/window justification; no invented number |
| Completeness/pagination | Missing page, continuation token, attachment or undocumented index coverage prevents absence conclusion | Coverage proof requirements |
| Blocked/unavailable/partial | Timeout, login wall, script shell, parse failure and truncated PDF have distinct diagnostics; none clears | Outcome/retry specification without treating retries as policy |
| Empty result | Preserve successful query and search terms; zero rows without adequate coverage is search-no-result only | Negative-evidence sufficiency |
| Durable provenance | Pin source/retrieval timestamps, content hash, URI, locator, query and capture; missing source time stays missing | Capture/authentication requirements |
| Conflicts/hierarchy | Preserve denial plus order; no automatic precedence by recency or hostname; surface unresolved conflict | Source hierarchy and conflict-resolution authority |
| Audit/reproduction | A reviewer can reconstruct searched sources, period, identity, pagination and parsing outcome from pinned evidence | Retention and reproducibility criteria |
| K2 isolation | External research artifacts cannot alter runtime flag merely by being retrieved | Separate knockout decision before any integration |

Future test fixtures must cover each row, SEBI-only/ED-only negatives, same-name
entities, superseded orders, unavailable attachments, contradictory periods and
repeated retrievals of changed content. Store results reproducibly without calling
the engine over the network. No new data field or connector is proposed as necessary
until an approved semantics-to-existing-carrier fit assessment demonstrates a gap.

## 5. Consolidated non-scoring declared-input audit — completed inventory

Method: exact-token tracked-file searches across engine/tests/frontend/fixtures,
plus schema, direct canonical builder and extraction-builder inspection. All five
have **confirmed no named semantic consumer**, not confirmed intent to exclude.
A substring-only test name ending `are_not_regulatory_actions` is not a consumer.
Generic raw-input retention/serialization must not be mistaken for derivation.

Shared trace: `canonical_input.py:136–137,306` onward retains raw governance for
direct JSON input; the new parameterized checks verify each value survives without
input mutation. Extraction uses a separate allowlist (`extraction/builder.py:335–387`)
which omits all five; no named producer is found in extraction. No named downstream
API/UI/Excel/presentation consumer or field-specific pre-existing test/fixture was
found in tracked paths. Generic raw serialization may carry retained input; it does
not turn these declarations into scored metrics. Tests added now are audit checks,
not proof of extraction or scoring consumption.

| Input | Schema line / type | Related actual consumer, not this field | Established intended role and unresolved intent | Compatibility implication |
| --- | --- | --- | --- | --- |
| eom_count_3y | 646, nonnegative integer/null | repeated_eom boolean in derived.py:1435–1441 | Spec §4.3 collects EOM; §11 separates auditor change count from repeated EOM. Exact count-to-flag rule not established | Do not derive repeated_eom automatically or remove accepted key |
| auditor_change_count_3y | 671, nonnegative integer/null | auditor_changed_3y boolean in same derivation | Auditor changes/dates and separate inputs required by spec §4.3/§11; count threshold/precedence unresolved | Disagreement with boolean needs an approved reconciliation policy |
| caro_remarks | 659, boolean/null | No CARO consumer; opinion/reputation branches only | Explicit EOM/CARO criterion, confirmed conformance gap; qualifying remarks/absence unresolved | Wiring changes scores and absent-input semantics; new-version baseline planning required |
| regulatory_actions | 704, array/null of open objects | sebi_ed_action_active and litigation_bucket, not the list | Spec §4.3 requires regulatory-action information; list-to-flag/party/status mapping not defined | Retain accepted object shapes; do not promote arbitrary action objects to K2 |
| independent_director_count | 726, nonnegative integer/null | board_independent_majority and kmp_exits_2y in derived.py:1516–1545 | Spec §4.3 collects count; supporting disclosure is an inference, not approved scoring intent | Count alone cannot establish majority without denominator; removal breaks accepted input shape |

Specification path: `handoff/authoritative/IPO_Screening_Engine_Specification_v1.5.md:239–256,547–558`.
No field is assigned “must be scored”. Recommended maintenance is a role inventory
with evidence-only/validation/future-policy possibilities, not a blanket failing
consumer lint. Field removal, wiring and renaming are outside this pass.

## 6. Completion boundaries and validation

Completed: A26 interim disposition recorded under explicit task authority; bounded
A27 and A8-R specifications prepared; five-field audit completed; in-memory wording
hashes calculated; focused baseline/audit checks added. Not completed or claimed:
CARO conformance implementation, regulator retrieval, tax prevalence/calibration,
new-version adoption or any K2 change. Proposed acceptance criteria remain proposed.

Validation commands and observed results are recorded in the additive tracker entry.
The 17 new tests check existing direct-input retention, extraction-projection
omission, current CARO non-consumption, materiality handling and wording hash
sensitivity. Final focused run: 122/122 passed in 0.33 s; check-config: valid True,
10 profiles. They do not test unimplemented future policies.
A full-suite rerun is unnecessary for these documentation/audit-only additions;
focused existing evidence/absence tests are run instead. Historical results are
not rerun or overwritten. Publication must be verified by remote commit, content
comparison, tracker comparison and PR state, not merely by a local commit.
