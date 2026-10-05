# Final Report — IPO Screening Engine v1.5

**Repository:** `ramkivs/ipo-screening-engine`
**Branch:** `arena/01a10abc-ipo-screening-engine`
**Baseline:** `main @ 01ba66c`
**Delivery tag:** `v1.5-delivery` — the engine, tests, docs and carrier tooling
added on top of `01ba66c`.
Sandbox-local and **not on GitHub**; see H4 for why, and for the verified
portable carrier (`handoff/delivery/`) that reconstructs it from `01ba66c`
alone.

*Deliberate omission:* the exact diffstat is not repeated here. A file cannot
state the insertion count of the tree that contains it without going stale on
the next edit — measured wrong once already. The generated
`handoff/delivery/carrier/VERIFICATION.txt` records it, correct by construction
because it is written after the commit exists. To check it directly:

```bash
git diff --shortstat 01ba66c v1.5-delivery
```
**Engine / spec / config:** 1.5.0 / 1.5 / 1.5.0
**Date:** 2026-10-05
**Authoritative sources, in precedence order:** Specification v1.5 → Technical
Design v1.5 → Execution Prompt → Artifact Manifest. The six Claude artifacts are
reference/prototype material only.

---

## A. Implementation summary

The v1.5 engine is implemented, executable end to end, and verified against a
golden regression suite of **238 tests**. It scores an IPO from a structured
input, produces a score with a range and a tri-state knockout gate, freezes the
run into an immutable record with eight hashed artifacts, and projects fourteen
Excel sheets from that record.

**What exists now**

| Area | Implementation |
| --- | --- |
| 17 modules | `engine/ipo_screening/` — hashing, canonical model, canonicalisation, snapshots, derived metrics, config validation, overlays, knockouts, scoring, schema validation, semantic validation, evaluation records/store, Excel projection, pipeline |
| 1 CLI | `engine/tools/ipo_screen.py` — `run`, `replay`, `verify`, `project`, `check-config` |
| Executable policy | `config/ipo-config.v1.5.0.json` — 6 modules, 30 criteria, 7 penalty rules, 4 sector overlays, 1 structure overlay, 6 knockouts, 64 policy-declared derived metrics, 10 validated profile × structure plans |
| Metric library | `engine/ipo_screening/derived.py` — 75 derived metrics implemented; the config declares the 64 that carry policy (bands, thresholds or weights) |
| Input contract | `schema/ipo-input.v1.5.schema.json` — draft 2020-12, hard gate |
| Golden case | `fixtures/vishal_nirmiti/` — input with RHP-grounded provenance plus five frozen expected-output files |
| Tests | `tests/` — 238 passing across 8 modules |
| Docs | `docs/TRACEABILITY_MATRIX.md`, `docs/RUNBOOK.md`, this report |

**The six v1.5 guarantees, and where each is enforced**

1. *Unknown is not zero.* Absence becomes `UNKNOWN`, never a default. The 30
   criteria carry 27 unknown points in the golden case and those points widen
   the range instead of lowering the score.
2. *Stale data cannot score as current.* A peer multiple past the 30-day limit
   and a market block past its freshness window are treated exactly like
   missing data.
3. *Knockouts are tri-state.* `CLEAR` / `TRIGGERED` / `UNVERIFIED`, evaluated in
   Kleene logic, with the missing fact named on the row.
4. *Evidence before score.* Every material input can carry a source, page,
   section and quote; provenance gaps are recorded in the run itself.
5. *Configuration is executable policy.* Invalid configuration blocks scoring.
   There is no override.
6. *Excel is a projection.* It is rebuilt from the frozen records and is never
   read back.

**Verification highlights**

* The golden run replays from its frozen artifacts to the **same result hash**,
  in-process and in fresh interpreters under three different `PYTHONHASHSEED`
  values.
* The runbook's fixture-regeneration procedure was executed verbatim: it
  reproduces the five expected files **byte-identically** and leaves the suite
  green.
* The traceability matrix cites 144 test names; a script checked that every one
  of them exists. The suite holds 238 tests in total.
* Sector overlays are covered on both halves: the plan swap (`test_overlays_knockouts.py`,
  `test_acceptance_matrix.py`) and the derivations themselves (`test_sector_overlays.py`,
  added after a coverage audit found the five financial-overlay metrics had no
  value-level test).

---

## B. Changed files

All files are new on top of `main @ 01ba66c`. No existing file was modified.

```
.gitignore                                    ignore build/ and .cache/
config/ipo-config.v1.5.0.json                 1,986 lines  executable policy
schema/ipo-input.v1.5.schema.json             1,107 lines  input contract

engine/ipo_screening/__init__.py               public API + guiding rules
engine/ipo_screening/version.py                engine/spec/config versions
engine/ipo_screening/errors.py                 Finding, severities, error family
engine/ipo_screening/hashing.py                canonical JSON, SHA-256, evaluate_id
engine/ipo_screening/canonical.py              State, Value, Evidence, registry
engine/ipo_screening/canonical_input.py        CanonicalInput, unit normalisation
engine/ipo_screening/snapshots.py              peer + market snapshots
engine/ipo_screening/derived.py                75 derived metrics
engine/ipo_screening/config_validation.py      15 assertion groups, fingerprint
engine/ipo_screening/overlays.py               EffectiveScoringPlan resolver
engine/ipo_screening/knockouts.py              Kleene logic, K1-K6
engine/ipo_screening/scoring.py                deterministic scorer
engine/ipo_screening/schema_validation.py      JSON Schema gate
engine/ipo_screening/semantic_validation.py    semantic + cross-source gate
engine/ipo_screening/evaluation.py             immutable records + store
engine/ipo_screening/excel.py                  14-sheet projection
engine/ipo_screening/pipeline.py               orchestration, replay
engine/tools/ipo_screen.py                     380 lines  CLI

tests/conftest.py                              shared fixtures + builders
tests/test_sector_overlays.py                  24 tests  overlay metric derivations
tests/test_acceptance_matrix.py                55 tests  P1-P30 and S1-S17
tests/test_validation_gates.py                 40 tests  schema/semantic/config
tests/test_reproducibility_store.py            32 tests  hashes, store, Excel
tests/test_core_semantics.py                   31 tests  UNKNOWN semantics
tests/test_overlays_knockouts.py               23 tests  overlays + tri-state
tests/test_vishal_golden.py                    19 tests  golden regression
tests/test_cli.py                              14 tests  CLI contract

fixtures/vishal_nirmiti/input.json             golden input, 15 evidence items
fixtures/vishal_nirmiti/expected_validation.json
fixtures/vishal_nirmiti/expected_derived.json
fixtures/vishal_nirmiti/expected_knockouts.json
fixtures/vishal_nirmiti/expected_score.json
fixtures/vishal_nirmiti/expected_verdict.json

docs/TRACEABILITY_MATRIX.md                    requirement -> code -> test
docs/RUNBOOK.md                                operator guide
docs/FINAL_REPORT.md                           this document
```

Totals: 17 engine modules (8,876 lines), 1 CLI (380 lines), 8 test modules plus
`conftest.py` (3,746 lines together), 1 config, 1 schema, 6 fixtures, 3 documents.

Generated at runtime and deliberately **not** committed: `build/` (evaluation
stores, workbooks), `.cache/` (cached RHP text), `.pytest_cache/`.

---

## C. Architecture decisions

**C1. Scoring is a pure function of explicitly supplied snapshots.**
`derive(canonical, config, peers, market, at)` mutates nothing and reads
nothing. All staleness classification happens in `snapshots.py` before
derivation, so a metric can never reach past its inputs. When a caller passes no
snapshots, they are normalised to empty ones and every dependent metric returns
`UNKNOWN` — a crash would be worse than a documented gap.

**C2. The result hash covers decision inputs, not the wall clock.**
`build_record` hashes an explicit payload of engine version, config hash, the
four snapshot hashes, mode, plan, derived metrics, knockouts, score, penalties
and missing items. It excludes timestamps and the evaluation id, which live only
in the record identity. Snapshot hashing excludes the derived `age_days` /
`age_hours` and the capture instant: the snapshot's `as_of` is the newest
**source** timestamp. Staleness *reasons* likewise cite the observation date and
the limit rather than "74 days old", because reasons are copied into
derived-metric explanations and would otherwise leak the clock into the hash.
Consequence: two runs minutes apart with unchanged material content hash
identically, and the hash still moves when data genuinely goes stale (score
35 → 34 in the golden case at +24h).

**C3. Immutability is enforced by the filesystem, not by convention.**
`EvaluationStore.write` creates the directory with `exist_ok=False` and raises
`ImmutabilityError` if it exists. Because the directory name embeds the result
hash, a changed input produces a *different* id rather than a collision — so a
correction cannot silently replace history, and no deletion is ever needed.

**C4. The record is self-sufficient.**
`EvaluationRecord.to_dict()` includes `input_snapshot`, `evidence`,
`market_snapshot`, `peer_snapshot` and `derived_metrics` alongside the summary.
This was a defect fix: without it, any projection built from a record produced
three silently empty sheets. Both `to_dict()` and the artifact-merged
`read_full()` now yield the same data.

**C5. Tri-state logic is implemented once and reused.**
`knockouts.Truth` with `k_and`/`k_or`/`k_not` is the only three-valued
evaluator. `use_of_proceeds_bucket` uses the same discipline for its three
sequential tests, so an undisclosed leg yields `UNKNOWN` for the bucket rather
than being read as "not blind-heavy".

**C6. Excel is a projection, and its determinism is tested.**
`SHEET_ORDER` matches Spec s22 exactly. `workbook_bytes` produces byte-identical
output for the same record. `build_workbook` accepts a single record or a
sequence — passing a bare mapping previously iterated its keys and rendered
fourteen empty sheets without error.

**C7. Configuration is validated against the *implementation*, not itself.**
`check_config` verifies that every criterion, overlay addition, knockout and
penalty references a metric that exists in `derived.REGISTRY`, that each overlay
reconciles to exactly 100 points, and that knockout expressions are
well-formed. A misspelled flag is a hard error (`CONFIG_FLAG_UNIMPLEMENTED`),
not a rule that quietly stops working.

**C8. Two-layer validation, both fail-closed.**
Schema (structure, types, enums, formats) then semantics (PBT−tax=PAT, EBITDA,
share-count/EPS, seller over-sell, percentage ranges, proceeds limits, OFS 6(2),
cross-source tolerance, peer and market staleness, GCP ceiling). Errors stop the
run; warnings are recorded in the run and printed by the CLI.

**C9. The CLI is a first-class surface with meaningful exit codes.**
`0` success, `1` refused by a validation or configuration gate, `2` usage error,
`3` audit mismatch. Every command prints the hashes it used, so an operator can
always see what was compared.

**C10. Replay defaults to the original instant.**
`pipeline.replay` re-evaluates from the frozen artifacts at the stored
`evaluation_timestamp`. Replaying at "now" would classify the snapshot
differently and could fail legitimately, which would make the reproducibility
check meaningless.

---

## D. Spec-to-code traceability

The full matrix is `docs/TRACEABILITY_MATRIX.md`: every Specification section
(s3–s27), every Execution Prompt s19 matrix item (P1–P30), every Specification
s26 item (S1–S17) and all 14 s27 acceptance criteria, each mapped to the file
and symbol that implements it and the named test that proves it.

| Family | Items | Covered |
| --- | --- | --- |
| Spec s3–s27 requirements | 60 rows | 60 |
| Execution Prompt s19 matrix | 30 | 30 |
| Specification s26 minimum list | 17 | 17 |
| Spec s27 acceptance criteria | 14 | 14 |

The matrix also records the **three deliberate divergences** from the reference
prototype (stale peers not scored zero; GCP ceiling not substituted for the
amount; knockouts tri-state rather than the 29/58 pair), five non-behavioural
divergences, three resolved ambiguities and the defects found during
verification — each with the test that pins it.

---

## E. Test results

```
$ PYTHONPATH=engine python3 -m pytest tests/ -q
238 passed in 7.81s
```

| Module | Tests | Scope |
| --- | --- | --- |
| `test_acceptance_matrix.py` | 55 | P1–P30 and S1–S17, named and traceable |
| `test_validation_gates.py` | 40 | schema, semantic and configuration gates |
| `test_reproducibility_store.py` | 32 | reproducibility, immutability, Excel projection |
| `test_core_semantics.py` | 31 | UNKNOWN-vs-zero, metric definitions, confidence |
| `test_overlays_knockouts.py` | 23 | Kleene logic, K1–K6, overlay resolution |
| `test_vishal_golden.py` | 19 | the golden regression |
| `test_cli.py` | 14 | CLI contract and exit codes |
| `test_sector_overlays.py` | 24 | the metrics each sector overlay derives |
| **Total** | **238** | |

**Coverage against the two governing lists:** 30/30 Prompt matrix items,
17/17 Spec s26 items, 14/14 Spec s27 acceptance criteria.

**Overlay coverage.** `test_sector_overlays.py` was added after an audit showed
that the overlay tests asserted the *plan* (criteria added and removed, 100-point
reconciliation) but never the *derived metrics* those criteria read: the five
financial-overlay metrics had no value-level test at all. The audit also
established the sign convention for `operating_loss_pct_revenue` (the loss as a
positive share of revenue, so a narrowing loss is a falling number), which the
reference configuration implies and the engine implements; it is now pinned by
test.

**Reproducibility evidence:**

* Same instant, four runs → one distinct result hash.
* Fresh interpreters at `PYTHONHASHSEED` 0, 1 and 12345 → the golden hash each
  time.
* `replay` from the frozen artifacts → `match True`.
* Key order and wall-clock time changes → identical hash while the snapshot is
  materially unchanged; the hash moves only when the snapshot genuinely changes.
* Runbook regeneration → byte-identical expected files.

**Fourteen defects were found and fixed during verification**, each now pinned
by a regression test. The most consequential:

1. `use_of_proceeds_bucket` dropped the first amount seen for each category, so
   every fully-disclosed offer fell through to `mixed_ok` and `blind_heavy` /
   `debt_heavy` / `growth` could never be detected — the largest signal in
   Module C was inert.
2. The same function used `x or 0.0`, silently reading an undisclosed leg as
   zero and letting a blind-heavy offer pass — the exact failure mode v1.5
   exists to prevent.
3. The GCP ceiling check compared lakhs against crore, reporting 2500% instead
   of 25%.
4. Snapshot hashes embedded the evaluation instant, so two runs a minute apart
   disagreed without any material change.

---

## F. Vishal Nirmiti result

Evaluated at `2026-10-05T12:00:00Z`, ratio nothing — every number below comes
from the frozen record.

| Field | Value |
| --- | --- |
| Evaluation id | `VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0` |
| **Final score** | **35.0** — base 38.0, penalties −3.0 |
| **Score range** | **25.0 – 62.0** |
| **Verdict** | **`INSUFFICIENT_DATA`** (band score `AVOID`, `verdict_uncertain: true`) |
| **Confidence** | **`Low`** — 73 of 100 evaluable points available |
| **Knockouts** | `UNVERIFIED` — K1, K5, K6 unverified; K2, K3, K4 clear |
| Penalties | −3.0 (margin spike +506 bps YoY); 10 points unresolved across four unverifiable penalties |
| Completeness | overall 73.0%, valuation 20.0%, market 100.0%, critical data 80.0%, knockouts 50.0% |
| Missing critical input | `going_concern_uncertainty` |
| **Result hash** | `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` |

**Module scores**

| Module | Score | Max | Known | Unknown |
| --- | --- | --- | --- | --- |
| A Financial Quality | 18 | 25 | 25 | 0 |
| B Valuation | 2 | 20 | 4 | 16 |
| C Offer Structure, Proceeds & Pre-IPO | 7 | 15 | 11 | 4 |
| D Promoter & Governance | 5 | 15 | 13 | 2 |
| E Business & Moat | 5 | 15 | 10 | 5 |
| F Market & Demand Signals | 1 | 10 | 10 | 0 |

**Why the verdict is `INSUFFICIENT_DATA` rather than a score-derived band:**
`going_concern_uncertainty` is a declared critical input, the input does not
establish it, and no knockout triggered. Spec s18 requires that state to be
reported as insufficient data rather than resolved into a band.

**Why the range is 37 points wide:** 27 of 100 points are unknown (16 valuation,
4 proceeds, 2 governance, 5 business) and 10 more are unresolved penalties.
Rather than guess, the engine reports the floor and ceiling those gaps imply.

**Hand-checked derivations** (independent recomputation, matching the engine to
the stated precision): revenue CAGR 18.0852% (`sqrt(33867.73/24288.2) − 1`);
PAT CAGR 169.2281% on a low base year (PEG capped); ΣCFO:ΣPAT 1.788190 — the
cumulative ratio, versus 3.583874 for the naive average of yearly ratios;
ROCE disclosed 28.02 against 24.8933 computed as EBIT / (equity + borrowings);
D/E 1.0073; margin deltas +506.55 bps then +50.31 bps; P/E 23.2558; fresh/OFS
split 81.46% / 18.54%; dilution 24.97%; contingent liabilities 25.20% of net
worth; receivable days +26.35% YoY.

**The three deliberate non-reproductions, visible in this result:** the GCP is
`UNKNOWN` rather than the 25% ceiling; the P/E and second-multiple criteria are
`UNKNOWN` on stale peers rather than scored zero; and the knockout line is
tri-state rather than the prototype's `CLEAR` with its 29/58 range.

---

## G. Excel sample

`build/vishal/IPO_Screening_History.xlsx`, 14 sheets, rebuilt from the store.
Row counts: `IPO_Master` 1, `Evaluations` 1, `Module_Scores` 6,
`Criteria_Detail` 30, `Knockouts` 6, `Penalties` 7, `Missing_Unverified` 16,
`Evidence` 16, `Market_Snapshots` 4, `Peer_Snapshots` 2, `Post_Listing` 0,
`Backtest` 0, `Config_Versions` 1, `Run_Log` 1.

**`Evaluations`** — one append-only row per run, every hash present:

```
evaluation_id             VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0
mode                      FINAL        evaluation_timestamp  2026-10-05T12:00:00Z
score                     35           base_score            38
lower_bound               25           upper_bound           62
confidence                Low          completeness_pct      73
verdict                   INSUFFICIENT_DATA
verdict_band_score        AVOID        verdict_uncertain     True
insufficient_data         True         knockout_status       UNVERIFIED
penalties_total           -3           available_points      73
total_evaluable_points    100          unknown_points        27
engine_version            1.5.0        spec_version          1.5
config_version            1.5.0        config_hash           4a5d92e867ae…
input_hash                4388606993c6…  source_manifest_hash 3bd2a7b2f803…
market_snapshot_hash      605f48ea5159…  peer_snapshot_hash   79deb530f65c…
result_hash               e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1
```

**`Module_Scores`** — the six rows shown in section F, each carrying
`available_points`, `unknown_points` and the `result_hash` they came from.

**`Knockouts`** — tri-state with the missing input named on the row:

```
rule_id  label                                    state       missing_inputs
K1       Qualified/adverse/disclaimer opinion,     UNVERIFIED  going_concern_uncertainty
         going concern, or negative net worth
K2       Promoter pledge >25% or active SEBI/ED    CLEAR
K3       OFS >80% with declining profits           CLEAR
K5       Contingent liabilities >50% of net worth  UNVERIFIED  contingent_liab_unquantified
K6       RPT growth >40%                           UNVERIFIED  rpt_pct_of_revenue_growth
```

**`Missing_Unverified`** — 16 rows; the action list. It opens with the two
valuation criteria (`pe_vs_peers`, 8.0 points; `second_multiple`, 4.0 points)
under category `CRITERION`, state `UNKNOWN`, then `sector_ipo_relative`,
`use_of_proceeds`, `auditor`, the three knockouts, the three unrecognised
penalties, and the stale peer and missing market block.

**`Evidence`** — 16 rows, each with source, source type, source URI, content
hash, evidence id, locator, page, section, quote, extraction method and as-of.
Shaded for visibility, as are `Market_Snapshots` and `Peer_Snapshots`.

**`Penalties`** — 7 rows. `margin_spike` −3 `SCORED` "triggered";
`receivable_days_up` 0 `SCORED` "not triggered"; the remainder `UNKNOWN`, which
is where the 10 unresolved penalty points come from.

Reproduce it with:

```bash
python3 engine/tools/ipo_screen.py project \
    --store build/evaluations --workbook build/IPO_Screening_History.xlsx
```

---

## H. Known residual issues

**H1. GCP: specification rule versus reference fixture — resolved, needs sign-off.**
The reference fixture records the ICDR ceiling (3625 lakh, exactly 25% of the
₹14,500 lakh fresh offer) in the GCP amount slot. Spec s10/s13 requires an
undisclosed `[●]` GCP to be `UNKNOWN` with the ceiling held separately. The
engine implements the specification; the unmodified reference fixture is
therefore rejected by two gates (string share count, and
`GCP_CEILING_RECORDED_AS_AMOUNT`). **This needs confirmation from R. Kapoor /
Ramki that the reference fixture is superseded**, per the Spec s21 ambiguity
rule. It was not silently resolved.

**H2. EPC and real estate share one overlay.**
Spec s14 lists "EPC / real estate" as a single subsection, so v1.5 ships one
`epc_real_estate` overlay. Acceptance items P19 and P20 are both satisfied by
it. If two separate profiles were intended, that is a policy decision requiring
a second overlay in the configuration; it was not guessed.

**H3. Branch name differs from the prompt.**
Work is on `arena/01a10abc-ipo-screening-engine`, not the prompt-mandated
`arena/ipo-screening-engine-v1.5-implementation`. This session is pinned to its
own branch and cannot create or push another. **No merge to `main` was
performed, and no production deployment was created**, as required.

**H4. The delivery is not reachable from GitHub — action required.**
GitHub remote access for this session was revoked ("This coding session has
ended because its pull request was merged or closed"), so nothing was pushed and
no pull request was opened. **Do not go looking for a commit hash**: a commit
exists only in the clone that created it, and this clone is sandbox-local.

Three separate losses occurred; only the third could have damaged the work.

1. *No push.* The delivery never left the sandbox, so `origin/main` remains at
   the baseline `01ba66c` — which independently confirms nothing was merged.
2. *A verification ran in a different sandbox.* A fresh clone contains only the
   baseline, so that session found no tag, no carrier and no `engine/`. It
   correctly reported NOT ACCEPTED and correctly refused to reimplement
   anything. The finding was right; the workspace was wrong.
3. *The sandbox `.git` was replaced* by a fresh shallow clone (`HEAD` `7f846dc`),
   destroying every original commit object (`6a9ceb3` … `c8887dc`). The working
   tree survived intact: rebuilding a tree from it reproduced
   `5f7a24d04b8576fc64f7f9fbd201d1cfe31f547c`, bit-for-bit the hash recorded
   before the loss. That hash is the proof the content was undamaged, and it is
   what allowed the delivery to be re-established on `01ba66c` under the
   `v1.5-delivery` tag with evidence rather than guesswork. Two corrections were
   then folded in — the diffstat note above and this section — so the tagged tree
   is one deliberate revision on from the restored one.
   `handoff/delivery/carrier/VERIFICATION.txt` records the current commit and
   tree.

A fresh clone of the repository therefore shows only:

| Ref | Points at | Meaning |
| --- | --- | --- |
| `origin/main` | `01ba66c` | The required baseline, unmodified |
| older implementation branch | `2562749` | Not this delivery |

**Consequence: a tree hash is usable evidence here; a commit hash is not.** The
durable carriers are the workspace files, the local branch history, and the
tracked artifacts in `handoff/delivery/carrier/` (bundle, checksums, and a
verification record naming the tip, tree and diffstat). Each reconstructs the
delivery from `01ba66c` alone, so publication does not depend on this sandbox
surviving.

Run `handoff/delivery/verify-delivery.sh` to check any workspace. It exits `0`
ACCEPTED, `1` NOT ACCEPTED, or `2` CANNOT VERIFY — the last covering case 2
above, which is a property of the workspace rather than a defect in the
delivery. Note that the carrier is tracked rather than ignored on purpose: the
restore in case 3 dropped every git-ignored path (`build/`, `.cache/`, and an
earlier ignored copy of the carrier), so an ignored carrier does not survive to
do its job.

To publish, use whichever of these matches what you hold:

```bash
# First: generate the carrier if it is not already present.
./handoff/delivery/make-carrier.sh

# A. You have the working tree (the session workspace, or a copy including .git).
git push -u origin arena/01a10abc-ipo-screening-engine

# B. You have the generated bundle. Its prerequisite 01ba66c is origin/main.
git fetch handoff/delivery/carrier/ipo-screening-engine-v1.5.bundle \
    'refs/tags/v1.5-delivery:refs/heads/arena/01a10abc-ipo-screening-engine'
git checkout arena/01a10abc-ipo-screening-engine
git push -u origin arena/01a10abc-ipo-screening-engine

# C. You have only the plain files (no git objects at all).
git checkout -B arena/01a10abc-ipo-screening-engine 01ba66c
PATCHES=1 ./handoff/delivery/make-carrier.sh
git am handoff/delivery/carrier/patches/*.patch
```

Verify before publishing, and after:

```bash
./handoff/delivery/verify-delivery.sh                       # expect: ACCEPTED
cd handoff/delivery/carrier && sha256sum -c SHA256SUMS      # carrier integrity
```

The intended publisher is the human who can see this workspace: a *new* coding
session starts from a fresh clone of GitHub and therefore cannot see this work
either.

**H5. Untested at the margins.**
* The `sector_ipo_relative` criterion has no fixture with a populated
  `recent_sector_ipos` list, so its scoring bands are exercised only through
  their `UNKNOWN` path.
* The sector overlays' metrics are now covered at value level
  (`tests/test_sector_overlays.py`, added after a coverage audit found the five
  financial-overlay metrics had none), but on **synthetic** inputs engineered to
  make each bucket unambiguous — not on a real bank's or NBFC's statements. A
  real filing would exercise the same code paths with messier disclosure, so the
  formulas are verified while their behaviour on real-world gaps is not.
* `cyclical` is exercised on a synthetic five-year series, not a real cyclical
  issuer.
* Automated extraction is not implemented — there is no extraction code in
  `engine/ipo_screening/extraction/`. Every input in this delivery was authored
  by hand from the RHP, and the fixture records the page and quote for each
  value. Extraction is out of the v1.5 scoring path and remains future work.

**H6. Market data is a point-in-time snapshot.**
Subscription, GMP and regime come from the input's `market` block with an
`as_of`. Nothing polls an exchange. If the block is not refreshed, the criteria
go `UNKNOWN` and the range widens — by design, not by omission.

**H7. No back-test history yet.**
The `Post_Listing` and `Backtest` sheets and the three post-listing modes are
implemented and tested, but no real listings have been tracked through them, so
the sheets are empty in the golden workbook. Back-test value accrues only as
issuers list.

---

## I. Run and reproduction instructions

Everything below runs from the repository root.

### I.1 Setup

```bash
cd /home/user/ipo-screening-engine
python3 -m pip install --break-system-packages jsonschema openpyxl pytest pypdf
export PYTHONPATH=$PWD/engine
python3 -c "import ipo_screening as e; print(e.__version__, e.SPEC_VERSION)"   # 1.5.0 1.5
```

### I.2 Reproduce the Vishal Nirmiti result

```bash
python3 engine/tools/ipo_screen.py run fixtures/vishal_nirmiti/input.json \
    --at 2026-10-05T12:00:00Z \
    --store build/evaluations \
    --workbook build/IPO_Screening_History.xlsx
```

Expected: `35.0`, range `25.0 – 62.0`, `INSUFFICIENT_DATA`, `Low`, knockouts
`UNVERIFIED` (K1/K5/K6), and

```
result hash  e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1
```

### I.3 Prove the hash is reproducible

```bash
# Re-derive from the frozen artifacts, at the original instant.
python3 engine/tools/ipo_screen.py replay \
    VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0 \
    --store build/evaluations
# -> match  True

# Re-derive every artifact hash from disk.
python3 engine/tools/ipo_screen.py verify --store build/evaluations
# -> OK  … artifacts=6 ; 0 mismatch(es)

# Same hash across interpreters with different hash seeds.
for seed in 0 1 12345; do
  PYTHONHASHSEED=$seed python3 -c "
import json
from datetime import datetime, timezone
from ipo_screening.pipeline import evaluate, load_config
out = evaluate(json.load(open('fixtures/vishal_nirmiti/input.json')), load_config(),
               evaluation_datetime=datetime(2026,10,5,12,0,0,tzinfo=timezone.utc))
print(out.record.result_hash)"
done
```

### I.4 Rebuild the workbook

```bash
python3 engine/tools/ipo_screen.py project \
    --store build/evaluations --workbook build/IPO_Screening_History.xlsx
```

### I.5 Validate the configuration

```bash
python3 engine/tools/ipo_screen.py check-config
# -> valid True ; 10 resolved profile x structure plans, each 100 points
```

### I.6 Run the full suite

```bash
python3 -m pytest tests/ -q          # 238 passed
python3 -m pytest tests/ -q -k matrix   # the acceptance matrix only
python3 -m pytest tests/test_vishal_golden.py -q
```

### I.7 A Preliminary → Final lifecycle, from scratch

```bash
rm -rf build/lifecycle
python3 engine/tools/ipo_screen.py run fixtures/vishal_nirmiti/input.json \
    --mode preliminary --at 2026-10-05T12:00:00Z --store build/lifecycle
python3 engine/tools/ipo_screen.py run fixtures/vishal_nirmiti/input.json \
    --mode final --at 2026-10-05T14:00:00Z --store build/lifecycle \
    --workbook build/lifecycle/IPO_Screening_History.xlsx
python3 engine/tools/ipo_screen.py project \
    --store build/lifecycle --workbook build/lifecycle/IPO_Screening_History.xlsx
```

The `Evaluations` sheet then holds two append-only rows (PRELIMINARY and FINAL),
and the Final's `preliminary_delta` records both hashes and the score change.

### I.8 Regenerating the golden expected files

Only after a deliberate change, and only when the intended new result is
understood. `docs/RUNBOOK.md` section 8 carries the exact procedure; it was
executed verbatim during this delivery and reproduces the five files
byte-identically.

---

## Sign-off checklist (Spec s27)

| Criterion | Status |
| --- | --- |
| Schema validation is enforced | ✅ |
| Unknown values cannot become favourable values | ✅ |
| All sector overlays implemented or explicitly rejected at config-validation time | ✅ |
| Knockout state is tri-state | ✅ |
| Stale valuation data cannot silently score as current | ✅ |
| GCP `[●]` is not converted into an assumed actual amount | ✅ |
| Weighted completeness and score ranges work | ✅ |
| Config invalidity blocks scoring | ✅ |
| Every score has evidence/provenance | ✅ |
| Preliminary and Final are immutable historical records | ✅ |
| Excel output is append-only and historically preserved | ✅ |
| Exact prior results are reproducible | ✅ |
| Golden regression suite passes | ✅ 238 tests |
| Vishal Nirmiti test demonstrates expected unknown/stale behaviour | ✅ |

**Awaiting decision, not implementation:** H1 (GCP reference fixture sign-off),
H2 (EPC versus real estate). **Awaiting infrastructure:** H4 (a session
with remote access to push and open the pull request; the carrier in
`handoff/delivery/` makes that a copy operation rather than a re-implementation).

No merge to `main`. No production deployment.
