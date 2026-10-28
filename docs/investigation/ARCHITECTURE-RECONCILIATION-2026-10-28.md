# Architecture reconciliation — Gemini global recommendations vs. the merged tree (2026-10-28)

**Question.** Gemini's global architecture recommendations (modular input orchestration,
RHP/placeholder discovery, governance extraction, UNKNOWN scoring, peer financials,
`ExchangeDemandAdapter` for Module F, tri-state knockouts) — which are already done,
which are real defects, which are genuinely new, and which cannot be decided here?

**Answer in one line.** The engine already implements the *contracts* the recommendations
ask for (provenance, freshness, fail-closed UNKNOWN, Kleene knockouts, provider-neutral
connector interfaces); the **only** proven defect found this pass is a documentation
overstatement, and the two adapter proposals are **contract-complete but
acquisition-empty**, blocked by an environment that cannot reach any provider.

- **Repository:** `ramkivs/ipo-screening-engine`
- **Starting `main`:** `2db28f2aeb17b2542140c4a18ed61ee3bfa9f182`
- **PR #13:** **MERGED** 2026-10-28T07:03:40Z, head `c446916a02948a4381d07f632eff4671678e21ea`,
  merge commit = `2db28f2` (verified ancestor of `origin/main`; merge tree equals the PR head tree)
- **A33/A34:** present in `main` — decision records read `APPROVED`, and
  `extraction/sections.py` carries `_sentence_evidences_early_release`
- **Tracker:** was at Revision 31; this pass is Revision 32
- **Engine code changed by this pass:** **none**

**Method.** Remote state verified first (`git fetch`, `git ls-remote`, `gh pr view`);
then read-only inspection of the modules the recommendations touch, plus *execution* —
a measured UNKNOWN-contract probe, a knockout-state read, a placeholder-variant matrix,
a seller-row contract probe, and an egress probe. Where a hypothesis could be tested
against the contract, it was, and one was **refuted** (§D-1).

---

## 0. Reuse, not repetition

A previous pass already reconciled these same recommendations:
`docs/investigation/JIO-34-GLOBAL-ARCHITECTURE-DISPOSITION-2026-10-27.md` (workstreams 1–7)
and `docs/investigation/BROAD-REMEDIATION-CONSOLIDATED-DISPOSITION-2026-10-27.md`.
That work is **not repeated**; every row below states what this pass *re-verified* against
the post-A33/A34 merged tree, and what is newly established. Nothing in this document
reopens A33 or A34.

---

## 1. Data-flow trace — what exists today (recommendation §3)

The recommendation proposes a modular input-orchestration architecture. Traced against the
implementation, the ten stages are **already separated**; what is missing is not structure
but *sources*.

| # | Stage | Implementation in `main` | State |
|---|---|---|---|
| 1 | Document discovery | `official_issue_sources.py`, `issue_platforms.py`, `aggregator_issue_terms.py` (allow-listed `urllib` fetch) | present; **needs network** |
| 2 | RHP/DRHP parsing | `extraction/sections.py`, `financial_tables.py`, `directorate.py`, `official_notice_ocr.py` | present, heavily revised (R22–R28) |
| 3 | Supplemental/authoritative discovery | `issue_terms.py` precedence + `THIRD_PARTY_AGGREGATOR_OVERRIDE` authority surface, A30 document classes | present |
| 4 | External acquisition | `connectors/adapters.py` (5 adapters), `coordinator.py`; **`BaseConnectorAdapter.fetch` raises `NotImplementedError`** | **contract only** |
| 5 | Normalisation to canonical | `canonical_input.py`, `extraction/builder.py`, `enrichment_engine.py` | present |
| 6 | Evidence validation/provenance | `enrichment_contract.py`, `evidence.json`, per-field locators/pages | present |
| 7 | Canonical inputs/snapshots | `input_snapshot`, `peer_snapshot`, `market_snapshot` (+ hashes) | present |
| 8 | Scoring/knockouts | `scoring.py`, `derived.py`, `knockouts.py` (Kleene) | present |
| 9 | Persistence/reproduction | `evaluation.py` `EvaluationStore`, `result_hash`, `runtime.json` fingerprints | present |
| 10 | Re-evaluation on updated evidence | issue-term precedence + duplicate/evaluation-id handling | present |

**Provenance check** (measured on the golden record, not inferred). Every identity the
recommendation asks for is persisted:

```
ipo_id / company_name / spec_version / engine_version      present
config_hash, source_manifest_hash                          present
evaluation_timestamp            2026-10-05T12:00:00Z       present (as-of / evaluation instant)
input_snapshot_hash 4388606993c604bb56d5f3cab1e9b061414fbfca63c6ac2c7b4e2638484f0614
peer_snapshot_hash  79deb530f65c8708b52626757017c114ddce6ebb008ac94f847f03e14cbd736a
market_snapshot_hash 605f48ea5159ca7d71f7a045ac871a331d6e263cc7ebf2cb32b491274cb2c3cb
result_hash         e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1
input_snapshot / evidence / provenance / validation blocks  all present
```

Per-observation fields (source identity, `as_of`, `age_days`, `status`, `reason`,
`source_id`) are carried in `peer_snapshot.observations[]`; publication-vs-retrieval time is
carried on the source reference where the reader produces one
(`exchange_issue_page.py:69`, `prospectus_terms.py:102`).

**Verdict.** The proposed orchestration is **already the implemented shape**. Building a new
framework would be a parallel architecture, so **none was built**. The real gap is stage 4:
acquisition. See §6.

---

## 2. The mandatory invariants, re-measured (recommendation §§6, 9)

### 2.1 UNKNOWN scoring and completeness — **retained exactly as contracted**

Measured on the golden input at `EVAL_AT` (not quoted from an earlier report):

```
available_points        = 73.0
unknown_points          = 27.0
total_evaluable_points  = 100.0          (= available + unknown)
completeness_pct        = 73.0           (= available / total, NOT available/100)
base_score              = 38.0           (UNKNOWN contributes 0)
final_score             = 35.0
lower_bound             = 25.0           (38 − 3 penalties − 10 unresolved)
upper_bound             = 62.0           (38 + 27 unknown + (−3) penalties)
```

This is the four properties the task requires: UNKNOWN contributes **zero** to base, its
**full max** to the upper bound, stays in the **denominator**, and is excluded from the
**numerator**. **Gemini's alternative formula — excluding UNKNOWN from both numerator and
denominator — is refused**, and was not introduced anywhere.

### 2.2 K1–K6 tri-state — **retained; missing input never becomes CLEAR**

Read from the same live record:

| KO | State | Why |
|---|---|---|
| K1 | **UNVERIFIED** | `going_concern_uncertainty` UNKNOWN (A19 positive-only rule); the other two leaves were FALSE and did not clear it |
| K2 | CLEAR | `promoter_pledge_pct = 0.0`, `sebi_ed_action_active = False` — both *supplied* |
| K3 | CLEAR | `ofs_share_pct = 18.54`, `profit_declining = False` |
| K4 | CLEAR | `pe_promoter_sold_pct_combined = 100.0` TRUE, but `promoter_full_exit=False`, `promoter_post_pct=49.4` — the `any` failed |
| K5 | **UNVERIFIED** | `contingent_liab_unquantified` unknown; quantified leaf FALSE |
| K6 | **UNVERIFIED** | `rpt_pct_of_revenue_growth` not disclosed |

A decisive FALSE wins an `all` (K4 is CLEAR although one leaf is TRUE), a decisive TRUE wins
an `any`, and UNKNOWN propagates with `missing` named. No retrieval failure was converted
into an adverse TRUE and no absence into a favourable FALSE anywhere in this path.

---

## 3. Placeholder and addendum discovery (recommendation §4)

### 3.1 The eight states — what the engine can actually distinguish

| State the recommendation names | Established? | Evidence |
|---|---|---|
| Issuer-disclosed value | **yes** | `ProvenanceValue` + locator/page |
| Placeholder `[●]` | **yes** | `extraction/numbers.py::is_undisclosed_marker` |
| Value in a later authoritative filing | **yes** | A30 classes (`PRICE_BAND_NOTICE` > supplemental > `OFFICIAL_PROSPECTUS`) |
| Value from an issuer/issue-matched official exchange page | **partly** | `EXCHANGE_ISSUE_PAGE` class + identity binding exist; **no live fetch in this environment** |
| Value missed by extraction though present | **by design UNKNOWN** | fail-closed: the reader emits nothing rather than guessing |
| Genuinely undisclosed | **yes** | `[●]` → `None` with an explicit note (`derived.py::_gcp_amount`) |
| Unretrievable (access/infra) | **yes** | `UNAVAILABLE` status + `reason` (A9/A17 surfaces) |
| Conflicting or invalid | **yes** | A30 rule 4/6 — field withheld, `issue_term_errors[field]`, never first-wins |

Placeholder vocabulary, measured across 13 representations (executed, not read):

```
[●] [•] [*] [-] []  NIL  N.A.  NA  "Not Applicable"  —  -  [â]  ""   → all markers, all parse to None
"1,234.56" "0" "100.00" "Rs. 10/-"                                   → none misclassified as markers
```

One cosmetic asymmetry: `is_undisclosed_marker(" ")` is `False` (only the empty string is a
marker), but `parse_indian_number(" ")` still returns `None`, so no value is fabricated.
Recorded, **not changed** — the behaviour is already correct.

### 3.2 Addendum — investigated; **no change justified**

There is no addendum/corrigendum *document class*. A separately published addendum would
arrive as another document and be classified by A30's role tests on its own text. No
addendum appears anywhere in the examined corpus (Paras, Jio, Moneyview, Vishal, R.K.
Fashion), so **no class was invented for a document shape that has never been observed**.
The precise gap and its trigger are in §8 (G-2).

### 3.3 No statutory-maximum substitution — **verified retained**

`_gcp_amount` returns UNKNOWN for `[●]`; `_gcp_legal_max` (Reg. 7(2) ceiling) is reported
**separately**; `_use_of_proceeds_bucket` treats a category containing any undisclosed entry
as unknown, so a partial total cannot understate the `blind_heavy` share. An empty schedule
is UNKNOWN — not `mixed_ok`, not zero.

### 3.4 Issuer-specific special cases — **one found, in dead code**

`enrichment_contract.py:424` keys a check on the issuer name:
`is_vishal = "VISHAL" in ipo_id`. It is the only issuer-specific branch in `engine/` outside
fixture definitions. It sits inside `validate_fail_closed_unknown()`, which **has no caller**
(`grep` over `engine/`, `tests/`, `docs/`, `handoff/` → only `docs/FINAL_REPORT.md` mentions
it), so it cannot affect any evaluation. See §D-3.

---

## 4. Proven defects

### D-1 (refuted, not a defect) — "partial seller rows are silently summed as zero"

**Hypothesis.** `derived.py` writes
`sum(x.get("pre_issue_shares") or 0.0 ...)` / `shares_sold`, so a seller row missing either
number would be counted as **zero**. That would understate the denominator (overstating
`promoter_ofs_pct_of_holding`, a 2-point band) and could fire **K4's `> 50`** on a count the
filing never printed.

**Reproduction.** Constructed a two-seller document with one complete row and one row
missing `pre_issue_shares`:

```
SchemaValidationError: SCHEMA_VIOLATION at issue/ofs_sellers/1:
  'pre_issue_shares' is a required property
```

**Contract check.** `schema/ipo-input.v1.5.schema.json` `$defs.seller` requires
`pre_issue_shares` and `shares_sold`, both `type: number`, `minimum: 0`, with
`additionalProperties: false`.

**Conclusion: hypothesis refuted — no defect and no code change.** A row cannot reach the
derivation without both numbers, so the `or 0.0` fallbacks are unreachable defence-in-depth.
What prevents "absent → zero" here is the **schema gate**, not the arithmetic. The
investigation is preserved as a regression test (§R-3) precisely because the safety rests on
a schema property that a future revision could relax.

### D-2 (no defect found) — placeholder dialects differ between modules

`connectors/adapters.py::_safe_float` special-cases only `[●]` while
`enrichment_engine.py:605` lists `[●] [•] [*] NIL N.A.`. Both return `None` for every other
placeholder because `float()` raises and the exception is caught, so the observable behaviour
is identical. **No change** — unifying the spellings would be cosmetic churn.

### D-3 (proven, documentation) — `docs/FINAL_REPORT.md` overstated a validator

**Defect.** §L.5 stated: *"Detection rule: `validate_fail_closed_unknown()` checks for
suspicious unprovenanced fixture values and emits warnings if test constants leak into real
evaluations."* It emits nothing — the function has no caller.

**Corrected this pass** (documentation only): the section now says the validator exists but is
not wired to any gate, notes that only `price_band_high == 220` is inspected while the other
four `FORBIDDEN_FIXTURE_DEFAULTS` entries have no consumer at all, and records the
`"VISHAL" in ipo_id` exemption.

**Not corrected** (authority boundary — wiring a validator into a live evaluation changes
behaviour, and choosing its rule is a decision): see G-3.

**Severity:** documentation accuracy; **no scoring, knockout or reproducibility impact.**

---

## 5. Consolidated inventory

Statuses: **CV** complete & verified · **II** implemented, incomplete · **PI** partially
implemented · **NJ** investigated, no change justified · **PD** proven defect · **BL** blocked.

| # | Item | Status | Evidence | Priority |
|---|---|---|---|---|
| A33 `kmp_exits_2y` counting scope | Approved (Alternative A, provisional); no counting change | **CV** | `handoff/decisions/A33-…md` APPROVED; `test_kmp_exit_counting_scope_20261027.py` | done |
| A34 early-unlock carve-out | Approved (Alternative B), implemented, merged | **CV** | `sections.py::_sentence_evidences_early_release`; 28-test suite; `test_a34_issuer_reproduction_20261027.py` | done |
| A32 builder defaults | Separate ratification **still open** | **BL** | A34 §0.3; A32 reads NOT RATIFIED | governance |
| UNKNOWN scoring/completeness | Contract intact, re-measured | **CV** | §2.1; `test_core_semantics.py` | protected |
| K1–K6 tri-state | Intact; missing → UNVERIFIED | **CV** | §2.2; `test_overlays_knockouts.py` | protected |
| Peer freshness/staleness policy | Intact; tests pin the instant, policy untouched | **CV** | `conftest.pinned_evaluation_clock`; commit `c446916`; `peer_staleness_days: 30` unchanged | protected |
| Peer integrity (no synthetic peers) | Enforced | **CV** | `test_d_peer_1_no_synthetic_peers.py`, `test_peer_row_mapping_and_bounds.py` | done |
| Peer second multiple / sector IPO | Missing data, no substitution rule | **BL** | Jio peers supply P/E only | P6 |
| Governance extraction (A19/A22–A29) | Positive-evidence rules implemented | **CV** | 237-test battery §7; decision records | protected |
| Coverage NIL vs UNREAD | Distinguishable | **CV** | `test_coverage_nil_vs_unread_20261026.py` | done |
| Document classes / field withholding | A30 implemented | **CV** | A30 §3 D1–D4; `test_notice_cache_document_class.py` | done |
| Official issue-term discovery | Implemented; **network-dependent** | **II** | `issue_terms.py`; sandbox lacks provider bytes | P3 |
| RHP addendum class | Never observed; not invented | **NJ** | §3.2 | P3 (trigger-gated) |
| Module F market blocks | 4 blocks defined, all MISSING without a provider | **BL** | `MARKET_BLOCK_NAMES`; Jio run all-MISSING | P5 |
| `ExchangeDemandAdapter` | **Contract-complete, acquisition-empty** | **II** | `OfficialSubscriptionAdapter`, `AnchorAllotmentAdapter`; `fetch` raises `NotImplementedError` | P5 |
| Peer-financials provider | Same shape (`PeerMultipleAdapter`) | **II** | same | P6 |
| Seller-row "absent ≠ zero" | Structurally guaranteed | **CV** | §D-1 + new `test_seller_row_contract_20261028.py` | protected |
| `validate_fail_closed_unknown` | Invoked by the contract validator; **name exemption removed, coverage completed** 2026-10-28 | **PD** (fixed) | §D-3; `G3-FAIL-CLOSED-SAFEGUARD-DISPOSITION-2026-10-28.md` | done |
| Orchestration framework | Already the implemented shape | **NJ** | §1 | refused |

---

## 6. External dependencies and technical limits (measured)

| Dependency | Status | Evidence |
|---|---|---|
| `bseindia.com`, `nseindia.com`, `screener.in` | **UNREACHABLE** | TCP connects but TLS is closed by the egress proxy: `URLError: TLS/SSL connection has been closed (EOF)` for all three |
| Any provider credential | **none configured** | no provider env vars exist; only `IPO_TERM_PLATFORM_PROVIDERS` (a host allow-list) |
| Live connector client | **does not exist** | `BaseConnectorAdapter.fetch` → `NotImplementedError`; no `requests`/`httpx` in `connectors/` |
| Aggregator fallback bytes | absent | previously recorded as missing (`…/aggregator-fallback-2026-10-22/native-accepted.json`) |

**Consequence.** Every acquisition claim in this pass is a *contract* claim, never a *source*
claim. No adapter was built against a source whose bytes, licensing or schema could not be
inspected — that would be a speculative integration.

**Provider selection (G-1) is a governance question, not a technical one**, and cannot be
resolved by inspection from here: coverage of Indian listed companies, API terms, licensing
and redistribution, historical depth and definitional alignment all require reading terms of
service this sandbox cannot fetch.

---

## 7. Verification performed this pass

Focused battery (10 authoritative modules — invariants, governance, coverage, peers,
connectors, tier gate):

```
237 passed
```

New guard module:

```
tests/test_seller_row_contract_20261028.py   8 passed
tests/test_suite_tiers.py                    1 passed   (tier gate green; no declaration needed)
```

Full suite on this exact tree:

```
PYTHONPATH=engine:. python -m pytest tests/ -q
2209 passed, 0 failed, 0 skipped   (1251.0 s)
```

2201 prior passes plus this revision's 8 new guard tests; no failures, no skips.

Integrity:

```
schemas: PASS (4)      frozen_core: True
golden_result: True    v1_6: PASS      compileall (engine, tests): clean
```

---

## 8. Governance decisions outstanding

| ID | Exact question | Status | What resolves it |
|---|---|---|---|
| **G-1** | May a *specific* peer-financials / exchange-demand provider be adopted (which one, under what licence, storing what history), and who bears the redistribution restriction? | **OPEN** — no provider is authorised | Access to the provider's actual terms + an owner decision. Until then, no integration. |
| **G-2** | If an addendum/corrigendum is ever ingested, does it *supersede* the RHP value for its field, or is it a same-class conflict to be withheld under A30 rule 6? | **OPEN — unobserved case** | One real addendum. Inventing a precedence rule without a specimen would be a fabricated semantic decision. |
| **G-3** | Should `validate_fail_closed_unknown()` be wired into a gate, and if so is its fixture-leak rule provenance-based (locator absence) rather than issuer-name-based? | **RESOLVED 2026-10-28, except G-3a** — see `G3-FAIL-CLOSED-SAFEGUARD-DISPOSITION-2026-10-28.md`. The rule was already invoked by `validate_enrichment_contract` (the "no caller" note in §D-3 was an imprecise search); it is now provenance-based, the issuer-name exemption is removed, and all three source-fact constants are enforced. **No gate was wired** — the builder's `allow_fixture_fallbacks=False` already closes the leak vector. Remaining: **G-3a**, whether to enforce the enrichment contract on a production ingest path (no defect requires it; needs an owner decision). |
| **G-4** | A32 remains **not ratified** while A34 is approved and merged. | **OPEN — recording requirement only** | Separate ratification. A34 does **not** ratify A32 (recorded in A34 §0.3). |
| **G-5** | A33's name/formula mismatch and role recovery; A34 alternative C (a structured carve-out field). | **OPEN — separately authorised** | Already scoped in the decision records; not touched here. |

---

## 9. Regression safeguards to keep protected

| ID | Invariant | Pinned by |
|---|---|---|
| R-1 | UNKNOWN → 0 base, full max to upper bound, in denominator, out of numerator | `test_core_semantics.py` |
| R-2 | Missing input → `UNVERIFIED`, never CLEAR/TRIGGERED | `test_overlays_knockouts.py`, `test_litigation_regulatory_defaults.py` |
| R-3 | Per-seller numbers are all-or-nothing, so "absent" cannot become "zero" in the ratios feeding K4 and the 2-point band | **new** `test_seller_row_contract_20261028.py` |
| R-4 | No synthetic/fabricated peers | `test_d_peer_1_no_synthetic_peers.py` |
| R-5 | Peer staleness policy unchanged; tests pin the instant instead | `conftest.pinned_evaluation_clock`, `test_peer_freshness_follows_the_evaluation_instant` |
| R-6 | Going-concern/auditor/litigation polarity (no absence→False, no negation→False) | `test_going_concern_negative_disclosure.py`, `test_auditor_evidence_section.py` |
| R-7 | Coverage NIL vs UNREAD | `test_coverage_nil_vs_unread_20261026.py` |
| R-8 | A34 carve-out alone never sets the unlock flag | `test_lockin_institutional_carveout.py` (28) |
| R-9 | Golden result hash + frozen core | `verify_golden_result`, `verify_frozen_core` |

---

## 10. Reconciled priority sequence

The proposed order is retained, with two corrections forced by evidence: **stage 2 needs no
work** (the contracts already exist and were re-measured), and **stages 5–6 cannot be
implemented** — they can only be *specified* — because no provider is reachable or
authorised.

| P | Workstream | State | Exit criterion |
|---|---|---|---|
| P1 | Broad remediation disposition | **done** | A33/A34 merged; prior findings dispositioned |
| P2 | Canonical input / evidence / reproducibility contracts | **done — verified §1** | provenance probe green |
| P3 | Official-document discovery + placeholder resolution | **contract done**, live path blocked | a reachable allow-listed host, or an owner-supplied document set |
| P4 | Governance/disclosure extraction | **done — A19/A22–A29 verified** | 237-test battery green |
| P5 | `ExchangeDemandAdapter` contract | **contract exists; acquisition absent** | G-1 decided **and** a reachable source |
| P6 | Peer-financials adapter | **same** | G-1 + reachable source |
| P7 | Continuous UNKNOWN / peer / knockout regression | **continuous, green** | R-1…R-9 stay pinned |

Parallel-safe: P3's contract work and P7. Sequential: P5/P6 both wait on G-1; nothing else
depends on them.

---

## 11. What this pass did not do

No engine, config, schema, scoring, knockout, weight, threshold, penalty or evaluation record
was changed. No adapter was written. No A33/A34 semantics were reopened. No provider was
selected, and no live source was claimed as verified. The only source changes are one new
test module, one documentation correction, this document and the tracker revision.
