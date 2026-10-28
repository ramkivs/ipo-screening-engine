# Consolidated Gemini recommendations — authoritative reconciliation

**Date:** 2026-10-28
**Repository:** `ramkivs/ipo-screening-engine`
**Scope:** IPO Screening Engine only
**Mode:** local evidence reconciliation; no publication or production activation

## 1. Baseline lock

Fresh verification before this record was written:

| Item | Verified state |
|---|---|
| Remote | `origin` = `https://github.com/ramkivs/ipo-screening-engine.git` |
| `origin/main` | `0a77bf95a3fa74101bd40d1137c4dd33badb5e87`; tree `2856c8d17f7ff63b98abce1ed270e244d8b8aa06` |
| Branch / HEAD | `arena/a9216594-ipo-screening-engine` / `0a77bf95a3fa74101bd40d1137c4dd33badb5e87`; same tree as `origin/main` |
| Ancestry | HEAD and `origin/main` are identical (both ancestor checks succeed) |
| Tags | none returned by `git tag --list` |
| Existing worktree | two unstaged documentation changes; no staged or untracked files |
| Existing local changes | cache-policy §8 in `OFFICIAL-DOCUMENT-DISCOVERY-DISPOSITION-2026-10-28.md`; tracker Revision 35 |

A read-only `git fetch origin main --no-tags` confirmed the remote ref without publishing or
triggering CI. The two existing local changes were reviewed first and preserved. This record
uses them; it does not repeat their cache investigation.

GitHub metadata confirms PRs **#13, #14, #15 and #16 are MERGED**, respectively at merge commits
`2db28f2`, `4cc81a9`, `e7934b1` and `0a77bf9`. Current `origin/main` therefore includes their
merged effects. No stale pre-merge wording in an older investigation record overrides current
GitHub state, current decisions, or the tracker.

## 2. Recommendation reconciliation

Status vocabulary is the work order's vocabulary. “Complete” describes the recommendation's
supported contract or safeguard, not live acquisition where the source layer is absent.

| ID | Final status | Evidence-backed disposition | Exact remaining action / exit condition |
|---|---|---|---|
| **G1** modular input orchestrator | **COMPLETE — VERIFIED** | The staged flow already exists: discovery → extraction → canonical/enrichment → snapshots → scoring → evaluation persistence. `evaluation.py` persists `input_snapshot_hash`, `source_manifest_hash`, `market_snapshot_hash`, `peer_snapshot_hash`, `result_hash`, and `evaluation_timestamp`. `ARCHITECTURE-RECONCILIATION-2026-10-28.md` §1 measured the hashes on the golden record. A second orchestrator would duplicate architecture. | None. Preserve deterministic inputs and hashes. |
| **G1A** exchange-demand adapter | **PARTIALLY COMPLETE** | `OfficialSubscriptionAdapter`, `AnchorAllotmentAdapter`, `ConnectorCoordinator`, provenance, freshness, conflict rejection and canonical assembly exist. Acquisition does not: `BaseConnectorAdapter.normalize` is abstract and there is no live connector client. Existing A10 permits distinct NSE/BSE/All Exchange observations for evidence/display; it does not establish equivalence or the still-open source/event/cutoff/failure contract. | Decide an official source contract and provider/licence; obtain reachable source-native bytes; establish NSE/BSE/All identity, event/cutoff/as-of and outage semantics. Exit: approved contract + qualified source + bounded client with focused tests. |
| **G1B** external peer financials | **PARTIALLY COMPLETE** | `PeerMultipleAdapter`, `PeerSnapshot`, immutable hashes, as-of/staleness, business-match and minimum-listing-history checks, valid-only medians, and fail-closed UNKNOWN propagation exist. No live acquisition client/provider is selected. Matching labels alone do not prove period, currency, unit or accounting comparability. | Approve provider/licence and provider-neutral field/period/unit/currency normalization against actual source bytes. Exit: qualified source and bounded acquisition implementation retaining existing fail-closed classification. |
| **G2A** official-document discovery/addenda | **PARTIALLY COMPLETE** | PR #16 merged the HTML read correction and Revision 34 mapped issuer/issue matching, provenance, positive/negative/unavailable outcomes and conflict withholding. Retained Paras bytes demonstrate parsing, not independent live verification. G-2 supersession remains unsupported by a specimen or decision. Local Revision 35 keeps both cache gates closed. | For live verification, use a permitted environment that can retrieve official bytes. For G-2, supply an applicable addendum/corrigendum plus an explicit supersede/supplement/conflict rule. Cache activation remains a separate owner-policy boundary. |
| **G2B** governance/NLP extraction | **PARTIALLY COMPLETE** | A19/A22–A30 positive-evidence and withholding rules, ratified A32, A33 Alternative A, and A34 Alternative B are implemented. PR #15 removed the G-3 issuer-name exemption and completed source-fact fixture-default coverage with 23 focused tests. No production specimen demonstrates the proposed G-3a enforcement defect. | G-3a requires an owner decision only if production enforcement is desired, ideally supported by a production enrichment specimen accepted by assembly but rejected by the contract. |
| **G3A** UNKNOWN scoring | **COMPLETE — VERIFIED** | Existing contract is preserved: UNKNOWN adds zero to base numerator, its full maximum to upper bound, remains in completeness denominator, and is excluded from numerator. Gemini's contrary formula is rejected. Evidence: architecture reconciliation §2.1 and `test_core_semantics.py` receipt. | None; retain invariant. |
| **G3B** peer-data integrity | **COMPLETE — VERIFIED** | Stale, missing, incomparable and unverified peers do not silently score; no synthetic-peer safeguard and valid-only snapshot calculations remain in place. Evidence: `snapshots.py`, `test_d_peer_1_no_synthetic_peers.py`, peer mapping/bounds and freshness receipts in the architecture reconciliation. | None; live acquisition remains G1B, not an integrity-contract gap. |
| **G3C** tri-state knockouts | **COMPLETE — VERIFIED** | K1–K6 Kleene behavior remains: missing evidence produces `UNVERIFIED`, not favorable `CLEAR` or adverse `TRIGGERED`; decisive true/false behavior is preserved. Evidence: architecture reconciliation §2.2 and existing knockout/default test receipts. | None; retain invariant. |

No recommendation has independent implementation work remaining that can safely bypass the
identified source-contract, external-access, provider/licensing, specimen, or owner-decision
boundaries.

## 3. Priority reconciliation

| Priority | Classification | Reconciled outcome |
|---|---|---|
| **P0** broad remediation | **partially complete** | Reconciliation is complete and PRs #13–#16 are merged. A31 and A32 are ratified; A33/A34 approved boundaries are intact. G-2, G-3a, A33 role recovery/Alternative C, and A34 Alternative C remain explicit boundaries. Jio/Paras retained evidence is not promoted to independently verified live evidence. |
| **P1** canonical contracts | **complete** | Existing orchestration, canonical evidence, source identity, issue matching, snapshots/hashes, conflict/missing handling and persistence are sufficient. The real gap is acquisition/source semantics, not another canonical contract. No defect justified code changes. |
| **P2** official discovery | **partially complete** | Discovery and resolver contracts are implemented and PR #16 is merged; live official-source verification is externally blocked in the recorded environment and G-2 is decision/specimen-blocked. Cache disposition is preserved without change. |
| **P3** governance/extraction | **partially complete** | Demonstrated G-3 defect was merged in PR #15 and A32 was ratified on 2026-10-28. No evidence demonstrates a G-3a production defect, so speculative enforcement was not added. |
| **P4** exchange demand | **blocked by an explicit decision** | Normalization/assembly contract exists, but provider/source, licence, exchange identity, cutoff/event, failure and outage semantics are not approved. Source access is also an external prerequisite. |
| **P5** peer financials | **blocked by an explicit decision** | Fail-closed normalization/snapshot contract exists; provider, licence and actual cross-provider comparability mapping are not approved. Source access is also an external prerequisite. |
| **Continuous safeguards** | **complete** | Current merged receipts cover UNKNOWN, peer integrity and tri-state behavior. No code changed in this pass, so no new focused regression run was necessary. |

## 4. P0 authoritative state and residual register

| Item | Current state | Authority/evidence |
|---|---|---|
| PR #13 | merged (`2db28f2`) | GitHub metadata; A34 implementation |
| PR #14 | merged (`4cc81a9`) | architecture reconciliation |
| PR #15 | merged (`e7934b1`) | G-3 correction and 23-test module |
| PR #16 | merged (`0a77bf9`) | discovery/read-path correction and Revision 34 |
| A31 | **RATIFIED 2026-10-28** | Identity-bound closed-record rule and associated A30 §5.6 pin ratified; no cache/source-policy expansion |
| A32 | **RATIFIED 2026-10-28** | Application of A22/A23 evidence-or-UNKNOWN principle ratified; A34 was not the source of ratification |
| A33 | Alternative A approved provisionally; counting unchanged | A33 §§0, 8; role recovery and structured Alternative C remain separate |
| A34 | Alternative B approved and implemented | A34 §0; structured Alternative C remains separate |
| G-2 | unresolved | no applicable specimen; A30 rule 6 withholds conflicts |
| G-3 | resolved and merged | PR #15; issuer-neutral fixture safeguard |
| G-3a | unresolved; no demonstrated production defect | `G3-FAIL-CLOSED-SAFEGUARD-DISPOSITION-2026-10-28.md` §7 |
| Jio | issuer/offering matching contracts exist; source acquisition remains limited | current discovery records and retained captures; no new live claim |
| Paras | retained capture can exercise parsing; retained bytes alone do not independently verify authority | Paras investigation and official-discovery disposition |
| Cache | both write gates closed | local disposition §8 and tracker Revision 35 |

Older documents that say PR #13 was open or A33/A34 were proposed are historical snapshots and
are stale on those points; current GitHub metadata and the approved decision-record headers are
controlling. Their underlying evidence remains useful.

## 5. Contract and integration-gap map

| Layer | Implemented contract | Actual gap | Classification |
|---|---|---|---|
| Issuer disclosure | PDF extraction, evidence locators, explicit missing/ambiguous handling | issuer-specific facts still require documents | external evidence, not architecture defect |
| Official issue terms | issuer equality, issue-window/identity binding, document classes, source references, conflict withholding | live access; G-2 semantics | external + explicit decision |
| External adapters | normalization, sanitization, provenance, freshness, snapshot hashes, conflict behavior | acquisition client and qualified source contracts | explicit decision + external |
| Canonical/evidence | builder/enrichment contract and provenance | G-3a production enforcement not demonstrated necessary | explicit decision if pursued |
| Evaluation | immutable snapshots, six recorded identities/hashes, deterministic result and replay | none demonstrated | complete |
| Subscription/anchor | category normalization and coordinator assembly | source-native exchange identity, event/cutoff/failure semantics | explicit decision + external |
| Peers | comparability flags, listing history, as-of freshness, valid-only multiples | provider-specific fields, periods, currency/units/licence | explicit decision + external |

`BaseConnectorAdapter` has no `fetch` method in the current tree; its abstract operation is
`normalize`, which raises `NotImplementedError`. The substantive prior finding remains correct:
there is no live acquisition client. This wording corrects the older shorthand without changing
its disposition.

## 6. Discovery, extraction and cache boundaries

No official-source probe was rerun: no concrete network change justified repeating the completed
investigation. The authoritative record remains that the tested environment reached DNS/TCP but
encountered TLS handshake EOFs; that is not a universal source-unavailability claim.

A30 rule 6 remains controlling. G-2 is not silently resolved. A31 was ratified on 2026-10-28;
that ratification supplies no cache-policy authority.
G-3a was not implemented because no production defect/specimen demonstrates a need. Explicit
negative evidence remains distinct from absent, ambiguous, retained-only, unavailable or
conflicting evidence.

The cache-policy investigation was not reopened. `EXCHANGE_ISSUE_PAGE` and
`INVESTMENT_PLATFORM_PAGE` writes remain closed; platform verification remains `verified=False`;
no TTL, invalidation, serving, resolver or post-close behavior changed.

## 7. Validation and evidence use

### Performed in this pass

- Fresh Git/GitHub baseline and PR metadata inspection.
- Read-only implementation and governance inspection.
- Documentation diff review.
- `git diff --check` after documentation updates.

### Existing receipts reused, not rerun

- Revision 34: 6 new cache HTML tests; 122 focused tests; full suite explicitly not run in that pass.
- PR #15 / Revision 33: 23 new G-3 tests; focused batteries recorded in its disposition.
- Architecture reconciliation / PR #14: 237 focused tests, 8 seller-row tests, tier gate and its
  historical full-suite receipt. That historical receipt is not validation newly performed here.
- A33/A34 decision records and focused issuer-reproduction/carve-out receipts.

No production code or test changed in this pass, so running code tests solely to reproduce these
receipts would violate the no-repeat instruction. **No full-suite regression test was run in this
pass.**

## 8. Decisions, blockers and minimum next actions

| Dependency | Why it matters | Minimum next action / exit evidence |
|---|---|---|
| A32 ratification | Governs whether the builder-default application is formally ratified | owner records ratify/decline; do not infer from A34 |
| A31 ratification | Identity-bound historical-record policy remains pending | owner ratification; not a cache precedent beforehand |
| G-2 semantics | Determines whether a later official document replaces or conflicts | applicable real specimen plus explicit supersede/supplement/conflict rule |
| G-3a | Could change accepted production enrichment behavior | production counterexample and owner enforcement decision |
| Exchange-demand source contract | Determines exchange identity, event/cutoff, categories and outage behavior | inspect source-native bytes/terms, then approve provider and semantics |
| Peer provider/comparability | Determines whether values are licensed, reproducible and truly comparable | inspect provider schema/terms and approve field/period/unit/currency mapping |
| External access | Live source claims cannot be established without bytes | permitted capture environment or owner-supplied hashed source-native capture |
| Cache post-close/outage policy | Required before any cache activation | explicit owner policy; no gate change before it |

## 9. Next execution sequence

1. Obtain source-native, hash-pinned exchange-demand evidence and provider terms in a permitted
   environment; then decide source identity, licence, event/cutoff and failure semantics.
2. Obtain peer-provider schema/sample history and terms; then decide provider and explicit
   financial-period/unit/currency comparability mapping.
3. Independently, record owner dispositions for A32 and A31 when available.
4. Resolve G-2 only when an applicable amendment specimen and explicit semantic decision exist.
5. Revisit G-3a only if a production specimen demonstrates the contract/assembly discrepancy.
6. Revisit caching only after demonstrated operational need and the already-recorded policy
   prerequisites are satisfied.

No completed work is listed as future work.

## 10. Dependency qualification follow-through (2026-10-28)

This is a targeted advancement of §8–§9, not a repeat of the consolidated investigation.

### 10.1 Exchange-demand evidence — partial evidence available, qualification still blocked

The repository already retains a source-shaped VNL package at
`evidence/ipo-subscription/vnl-20261011/`. It supplies useful schema and event evidence but is
explicitly labelled **NON-AUTHORITATIVE INVESTIGATION EVIDENCE** and A10 denies source
qualification and implementation authority.

| Evidence | Current checkout SHA-256 | What it supports |
|---|---|---|
| `api-ipo-detail-VNL.json` | `4219115872222145d2062e306fcea1022017ee1344e189f07daac9fe4bad5874` | issuer `Vishal Nirmiti Limited`, symbol `VNL`, ISIN `INE1O5L01025`; NSE and separately labelled All Exchange graph objects; graph timestamps |
| `api-ipo-bid-details-VNL-EQ.json` | `c61f4bcb90c13b4b99f1debddee60d5e3ac029b678c7b04feeae2ef02e091a64` | category rows, offered shares, bid shares and multiples |
| `api-ipo-active-category-VNL.json` | `3f58b12ec21241d1cb63806686419eafbc90efbe6709f55ea360ae499ed86acc` | consolidated category rows and `Updated as on 05-Oct-2026 19:00:00` |
| `api-disclaimer.json` | `3133b433fea4390893239b8e9f04164063a1b1675a578935c50dbf3ee1de26b9` | display rule: accepted/blocked UPI bids; final demand display updated up to 19:00 on last day |
| chart-demand NSE / ALL | each `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` | valid empty arrays only; not zero demand |

Supported semantics are narrow:

- `demandGraph` explicitly labels **cumulative NSE bid quantity**, timestamp
  `05-Oct-2026 19:00:04 IST`, total bids `10,020,004`, cut-off bids `5,970,264`.
- `demandGraphALL` labels cumulative demand and an hourly update, timestamp
  `05-Oct-2026 19:00:00 IST`, total bids `14,471,488`, cut-off bids `8,963,828`.
- `demandDataBSE` is empty. A field hosted in the NSE response does not establish a BSE-native
  observation, and the All Exchange composition remains unverified.
- QIB, NII (including subcategories), RII, cut-off and price-bid labels are observable, but a
  production canonical mapping, parent/subcategory aggregation rule, denominator, final-event
  rule and scoring/Final consequence remain unapproved. A10 permits distinct evidence/display
  observations only and prohibits averaging, substitution or inferred equivalence.

**Integrity limitation discovered during qualification.** Eight payloads covered by
`SHA256-MANIFEST.json` match their recorded hashes except
`vnl-issue-information.html`: the manifest records 313,040 bytes and
`2ae7009b…e78f2`, while this checkout has 313,038 bytes and
`6beb26dc…f5ce6`. The evidence register repeats the manifest value. Also, the manifest file
itself is checked out with LF (1,443 bytes, `37c4f0…2295`) while its register hash describes its
CRLF representation (1,489 bytes, `26cf9f…6d6d`). This is an evidence-transfer/checkout
integrity limitation, not proof of source alteration. No evidence bytes were modified. The JSON
payload hashes used above match and remain usable as retained observations; the HTML cannot be
claimed byte-identical to its recorded capture without recovery of the manifest-matching bytes.

Applicable provider terms are **not retained**. The captured page links to NSE Terms of Use,
Copyright and Disclaimer pages, but their content is absent; `api-disclaimer.json` defines data
display behavior, not licensing, retention or redistribution permission. Current permitted
network routes do not provide access to the exchange pages. Therefore no provider/licence is
qualified and no adapter implementation is authorized.

**Minimum evidence to exit:** (1) source-native response plus request URL/headers and retrieval
time from a permitted capture environment; (2) the applicable NSE terms/licence text with
capture date and hash; (3) proof of NSE/BSE/All composition and final-publication event; (4)
owner approval of source, category/denominator mapping, cutoff, missing/outage and scoring/Final
semantics. Separately recover the manifest-matching HTML bytes or issue a governed correction to
its transfer record.

### 10.2 Peer-financials evidence — provider qualification unavailable

Repository peer material consists of authored connector fixtures, filing-disclosed peer tables
and retained evaluation snapshots. These establish the engine contract and issuer-disclosed
comparisons, not a candidate external provider's schema, representative history, source-native
market session or licence. No retained terms establish commercial use, storage or redistribution
rights. The current permitted route cannot access the previously named candidate host.

Evidence supports retaining these provider-neutral requirements: named peer/source; business
comparability; listing date/history; valuation/price as-of date and timezone; currency and units;
actual reporting period and accounting basis; raw financial inputs separately from derived
P/E/P/B/EV/EBITDA; immutable source and snapshot hashes; and fail-closed handling of stale,
missing, conflicting or incomparable observations. It does **not** support selecting a provider,
mapping provider-specific fields, choosing period-alignment tolerances, or licensing stored
history.

**Minimum evidence to exit:** one candidate provider's versioned schema and representative
multi-period payloads for multiple peers, source-native quote/session timestamps, definitions for
financial periods/units/currency/accounting basis, and applicable access/storage/redistribution
terms, all captured with hashes; then an owner provider/licence decision and explicit
comparability mapping.

### 10.3 Governance dependency check

- **A31:** **RATIFIED by RAMKI 2026-10-28.** Ratification confirms the identity-bound closed-record
  rule and associated A30 §5.6 pin; it does not approve cache or allow-list policy.
- **A32:** **RATIFIED by RAMKI 2026-10-28.** Ratification confirms the recorded A22/A23
  evidence-or-UNKNOWN application. A34 did not ratify A32; this is a separate owner decision.
- **G-2:** no addendum/corrigendum/errata/amendment specimen is present. A30 rule 6 remains the
  resting behavior; no supersession semantics were invented.
- **G-3a:** no production enrichment document rejected by the contract but accepted by assembly
  is present. The question remains unresolved and no enforcement was added.

### 10.4 Work and validation disposition

No adapter work became independently executable: source qualification, licensing and semantic
prerequisites remain unresolved. No code, tests, evidence bytes, cache policy or cache gates were
changed. Validation was limited to JSON parsing/schema inspection, SHA-256 inventory comparison,
governance-status checks, specimen-name checks, final diff review and `git diff --check`. No live
source was claimed verified and no full-suite regression test was run.

### 10.5 VNL HTML integrity resolution attempt — repository history exhausted

Targeted history and object inspection establishes these verified facts:

1. `SHA256-MANIFEST.json` records 313,040 bytes and full SHA-256
   `2ae7009b9f30c026c91a1d38a4b943f348ab3f275f0b1b5b971481a8f72e78f2`.
2. The HTML entered Git once, in source-evidence commit
   `951d77d4ae39422c232fd727be89551aeb868ab4` (2026-10-11), as Git blob
   `21ea96b6f0f694d0a65076ce5bd4209c84558a7d`: 313,038 bytes, full SHA-256
   `6beb26dc8acce2f9cd6620a761ec5d771da46b3214d220e6946bea37614f5ce6`.
   Current `main`, the working file, and GitHub's content API for that original commit all
   identify the same blob and size. There is no earlier repository version.
3. No second retained copy or 313,040-byte candidate exists in the repository. The parent of
   `951d77d4` does not contain the package.
4. `.gitattributes` did not exist at the source-evidence commit. Current attributes protect
   selected later evidence paths with `-text`, but not `evidence/ipo-subscription/**`; the VNL
   HTML therefore has unspecified `text`/`eol` attributes. Current repository config has no
   explicit `core.autocrlf`, `core.eol`, or `core.safecrlf` value.
5. The committed HTML contains 4,713 LF and zero CR bytes. The committed manifest is 1,443-byte
   LF text, while the evidence register's recorded 1,489-byte manifest hash is reproduced by
   converting its 46 LF endings to CRLF. This proves line-ending transformation occurred for
   at least the manifest during the original transfer/add path. It makes loss of two CR bytes
   from a mixed-ending HTML source a plausible explanation for the HTML's two-byte difference,
   but the missing source bytes are unavailable, so the exact two positions and the expected
   HTML hash cannot be reconstructed or proved from repository evidence.

**Disposition:** the discrepancy is **UNRESOLVED AT THE BYTE-RECOVERY LEVEL, bounded to the
pre-commit capture→Git-add path**. It is not a current checkout drift: the checkout exactly
matches the first and only Git blob. The manifest-matching HTML was not recovered, and the
existing evidence file was not modified. The seven non-HTML artifacts in that manifest continue
to match exactly. As an independently executable preservation correction, `.gitattributes` now
marks `evidence/ipo-subscription/vnl-20261011/** -text`; future checkouts must preserve the
committed bytes rather than apply another text conversion. This protects the durable Git blob
and does not claim that it is the missing manifest-matching original.

A governed correction needs either (a) the original 313,040-byte capture whose full hash matches
`2ae7009b…e78f2`, with custody provenance, or (b) an owner-approved evidence-register amendment
that preserves both identities, declares the original bytes unavailable, and designates the
first committed Git blob as the durable retained artifact. Merely inserting two bytes until a
hash matches is prohibited and would not establish provenance.

### 10.6 Qualification progress after integrity resolution

The permitted route supplied repository/GitHub history and blob metadata only. It supplied no
new exchange response, NSE/BSE terms text, peer-provider schema, representative peer history, or
provider licence. Exchange and candidate-provider hosts remain unavailable through the current
route. Consequently:

- the retained VNL JSON remains useful only under A10's distinct evidence/display limitation;
- NSE, BSE and All Exchange identity/equivalence remain separate and unresolved;
- no source, licence, category/denominator, final-event/cutoff, outage or scoring/`FINAL`
  decision became available;
- no peer provider, field mapping, period alignment, units/currency/accounting mapping or
  licence became qualifiable; and
- no adapter implementation became independently executable.

The minimum next actions remain those in §§10.1–10.2, with the HTML custody/correction choice
above added as a separate evidence-integrity dependency. A31 and A32 were ratified on 2026-10-28;
no G-2 specimen or G-3a production counterexample was found.

### 10.7 VNL evidence amendment approved and effective; current qualification route

RAMKI explicitly **APPROVED** the narrowly scoped amendment on 2026-10-28. The effective record
in `evidence/ipo-subscription/A8-S_EVIDENCE_ACQUISITION_REGISTER.md` preserves the unrecovered
313,040-byte / `2ae7009b…e78f2` original-capture identity and designates the first committed
313,038-byte / `6beb26dc…f5ce6` blob as the durable retained repository artifact, without
equating the two. The approval is limited to evidence-identity bookkeeping and does not qualify
a source or authorize provider, adapter, scoring, `FINAL`, production or cache behavior.

No genuinely new custody-backed original, exchange-source material, provider terms,
peer-provider schema or representative provider history is present in the current worktree. The
permitted route has not expanded beyond repository/GitHub material already used in §§10.5–10.6.
No previously open source-qualification gap can therefore be closed without inventing evidence.
The concrete blocker is external evidence acquisition plus owner source/licence/semantic
approval, not adapter code.

The concise acceptance criteria remain:

- **Exchange demand:** custody-backed source-native bytes with request/response provenance and
  applicable terms; explicit NSE/BSE/All composition; approved category/denominator,
  final-event/cutoff, outage and scoring/`FINAL` semantics.
- **Peer financials:** authoritative versioned provider schema, multi-period/multi-peer sample,
  source-native timestamps and definitions, access/storage/redistribution terms, followed by
  provider/licence and comparability approval.
- **Governance:** A31 and A32 ratification is complete; G-2 still needs an applicable specimen
  plus semantics, and G-3a still needs a reproducible production counterexample plus enforcement
  decision. Existing records are reused and no duplicate request was created.

## 10.8 Official-document-first peer financials disposition (2026-10-28)

This is a bounded reconciliation against the implemented extraction path and retained specimens,
not a new provider search.

### Implemented path and qualified support

`DocumentExtractor.extract_from_pdf` already invokes `SectionExtractor.extract_peers` and the
builder carries the resulting `peers` into canonical input. The parser is header-bound and
fail-closed. Four observed layouts are implemented in `_PEER_SHAPES`:

| Layout / retained evidence | Implemented mapping |
|---|---|
| R.K. Fashion accounting ratios | CMP, P/E, RoNW, NAV; P/B derived as CMP/NAV |
| Vishal Nirmiti listed-industry peers | closing price, P/E, RoNW, NAV; P/B derived |
| Jio peer companies | P/E and RoNW; no CMP, therefore no invented P/B |
| Paras listed peers with EV/EBITDA columns and wrapped rows | closing price, P/E, RoNW, NAV; wrapped rows and issuer-row exclusion |

Existing focused modules (`test_peer_row_mapping_and_bounds.py`,
`test_reading_defects_20261026.py`, `test_jio_evidence_remediation.py`,
`test_rk_fashion_reconciliation.py`) pin recognised headers, placeholders, multi-line names,
missing cells, `NM`, absent valuation dates, wrapped rows, issuer-row exclusion, monetary-column
misalignment and unrecognised-layout withholding. The retained tracker receipts record actual
RHP results for R.K. Fashion, Jio and Paras. No additional layout is claimed tested here.

The architecture already preserves document identity in `_sources`, one table-level `peers`
evidence object with page/locator/header quotation, peer name, source id, table valuation date,
P/E, P/B and RoNW in canonical input, and the immutable `peers.json` evaluation snapshot/hash.
This is adequate for the engine's currently consumed peer multiples and makes the official RHP
table the primary available source without an external provider.

### Precise contract boundary

The current closed peer schema does **not** retain face value, EPS, NAV, raw closing price,
reporting-period identity, row-level page/quote, footnotes or per-value verification status.
The parser reads some of those cells to map/derive current canonical multiples but cannot publish
them without changing `ipo-input.v1.5.schema.json` and the immutable snapshot contract. Such an
additive contract/version decision is not authorized here. No schema or scoring change was made.
Unrecognised layouts continue to emit no peers and therefore preserve UNKNOWN.

### Local supplementary data

A local mechanism already exists: CLI `extract --peers` / `assemble --peers` accepts a JSON peer
snapshot, `EnrichmentEngine` consumes its `peers` and `_source_ref`, canonical schema validation
bounds the peer fields, and evaluation persists `peers.json` plus `peer_snapshot_hash`. A second
`peers.json` store is unnecessary. The existing supplemental-enrichment schema also declares a
`peer_data` block, but `_reconcile_market_and_peers` does not consume it; claiming that
`--supplemental` presently enriches peers would be incorrect.

Neither existing route is yet a qualified manual-evidence mechanism: the working `--peers` route
does not condition admission on verification, while the provenance-bearing supplemental route is
not wired for peers. In addition, the v1.5 peer object has no reporting-period, currency/unit,
row-level provenance or per-value verification fields. Therefore a manually curated snapshot
could affect scoring merely by being supplied. No operator procedure, sample real values or
production use is authorized until an approved contract defines admission and verification.
Fixtures remain test-only and are not supplementary evidence.

### Provider-register disposition for the current personal-use requirement

No PF-01–PF-05 source/terms artifacts are present in this checkout, so no provider is newly
qualified and no licensing claim is made. Given the implemented official-RHP path for currently
consumed issuer-disclosed multiples, paid provider selection is **CLOSED — CURRENT DECISION** for
this workstream, meaning “not needed now,” not “technically failed” or permanently prohibited.
Individual dispositions:

| ID | Provider/work item | Disposition | Basis / revisit trigger |
|---|---|---|---|
| PF-01 | EOD Historical Data | **DEFERRED** | No retained qualified schema/terms/sample; revisit only for a concrete metric the filing/local governed path cannot provide. |
| PF-02 | Financial Modeling Prep | **DEFERRED** | No current need or qualified artifacts; no integration selected. |
| PF-03 | Alpha Vantage | **DEFERRED** | No retained qualified schema/terms/sample; not failed. |
| PF-04 | FMP plan and licence assessment | **NOT QUALIFIED** | Applicable plan, storage/retention/redistribution terms are not retained and were not accepted. |
| PF-05 | FMP plan eligibility and sample access | **NOT QUALIFIED** | No representative, provenance-bound multi-period/multi-peer sample is retained. |

FMP Ultimate is not purchased or recommended by this work. No automated portal scraping is
approved. Provider qualification may be reopened only when a named missing requirement, actual
provider artifacts and applicable terms are available.

### Implementation outcome

No parser/code change was justified: the existing parser already covers the four retained
layouts, and the missing distinctions require a separately authorized contract extension rather
than additional positional parsing. No local data file was created because the existing snapshot
input/persistence mechanism is sufficient structurally but not yet qualified for manual scoring
admission. This avoids a competing store and preserves UNKNOWN, provenance and fail-closed
behavior.
