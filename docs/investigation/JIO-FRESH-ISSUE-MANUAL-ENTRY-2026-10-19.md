# Closing the Jio Manual-Entry Dead End — `issue.fresh_issue` — 2026-10-19

**Branch:** `arena/d15866b5-ipo-screening-engine` **Base (this work):** `1840fd7e16c64a800c9095ec98621695173a61b4`
**Observed failure:** Windows ingestion `ing-8db36776dd794ec3`, `U72900GJ2019PLC110816_JIO.pdf`
**Protocol:** VERIFY → TRACE → RECONCILE CONTRACT → IMPLEMENT → TEST → PUBLISH → VERIFY → RECONCILE TRACKER (single pass)

## 1. Observed dead end

Filing extraction, issuer identification and official discovery (`UNAVAILABLE`) succeeded; the
four-field manual entry was accepted (price-band floor/cap, lot size, OFS). Eligibility then
blocked evaluation **solely because `issue.fresh_issue` was missing** — a field the manual form
did not accept. Evaluation did not run; nothing was persisted. The UI contract (all required
issue terms enterable from the broker platform) and the eligibility gate contradicted each
other; the workflow had no completion path.

## 2. Trace — the exact gate

- `engine/ipo_screening/presentation/service.py`: after the four-term eligibility path and the
  manual-entry completion, a **mirror gate** (added in `a7f823d`, 2026-10-18) sets
  `pending_awaiting = (["fresh_issue"], ...)` when `issue.fresh_issue is None`, naming the
  field "instead of a schema failure". The official-resolution path has the same fail-closed
  mirror (`still_missing = ["fresh_issue"]`).
- The manual contract was deliberately scoped to four fields (`MANUAL_ISSUE_TERM_FIELDS`);
  the UI marked `issue.fresh_issue` "cannot be entered manually".

## 3. Contract reconciliation — is `fresh_issue` required for initial screening?

| Authority | Finding |
|---|---|
| **Canonical input contract v1.5** (`schema/ipo-input.v1.5.schema.json`, spec s20 hard gate, frozen since the v1.5 implementation `fb822e5`) | `issue.required` = `price_band_low, price_band_high, fresh_issue, ofs, open_date, close_date`. Empirically: `evaluate()` raises `SchemaValidationError` for `fresh_issue=None` ("None is not of type 'number'") and for a missing key ("'fresh_issue' is a required property"). Every historical evaluation carries it (golden `fixtures/vishal_nirmiti/input.json`: `fresh_issue = 14500`). **It is a mandatory input for every evaluation.** |
| **Scoring contract** (spec s18; `scoring.py`, frozen core) | Consumes it in module C: `fresh_share` (`fresh_share_pct`, 3 pts) and `use_of_proceeds` (`use_of_proceeds_bucket`, 4 pts), plus the `pure_ofs` `zero_if` flag and the loss-making overlay's `cash_runway_months`. Missing scored metrics are contract-sanctioned as `UNKNOWN` (0 points + full upper bound + confidence exclusion) — the engine would tolerate absence, but the pipeline never reaches scoring without schema validity. |
| **`critical_data`** (config v1.6) | Does **not** list `fresh_issue`: its absence is not a "verdict-unsafe" critical gap. |
| **Semantic validation** | Optional-guarded (`if fresh_issue and fresh_issue > 0`): proceeds-limit checks run only when present. |
| **Runtime required-issue-terms** (`issue_terms.REQUIRED_ISSUE_TERMS`) | Exactly the four manually resolvable pricing terms; `fresh_issue` is resolved from a different document class, not by the pricing resolver. |
| **Prior decisions** (JIO-RHP investigation, 2026-10-17) | "Fresh-issue amount unobtainable on the verified pathway: evaluation failed schema validation (`issue/fresh_issue: None`)... the final Prospectus states it." The established completing document class is the **final Prospectus** (OFFICIAL_VERIFIED); the schema failure was treated as a genuine data gap to fill with a real value — never a relaxed schema, never a default. |
| **Four-field directive** (2026-10-18) | Scoped manual entry to exactly four fields; added the mirror gate so the failure names the field "instead of a schema failure. Nothing is invented." — fail-closed, not fabricated. |

**Conclusion — CASE B.** `issue.fresh_issue` is a genuine prerequisite for every evaluation
under the authoritative input contract (not an assumption invented by a later guard: the schema
requirement predates all guards). The gate must **not** be bypassed. What must change is the
supply path: the bounded manual entry — already the authorized supply path for required issue
terms the filing does not disclose and official sources cannot supply (Step 4 Area C +
directives; broker IPO pages state the fresh-issue amount alongside the other terms) — now
includes `issue.fresh_issue`, on exactly the existing MANUAL_ENTRY/UNVERIFIED authority.
CASE A does not apply: "initial screening" in this architecture is `evaluate()`, and the
canonical input contract's hard gate (s20) is a downstream operation that genuinely requires
the field; relaxing the frozen v1.5 schema would change the input contract, which is not
authorized. The scoring contract needed no change either way.

Scope authority: the user's 2026-10-19 directive resolves the dead end and explicitly
authorizes implementing the missing field end to end when the contract requires it. This
supersedes the four-field scope limitation exactly as the 2026-10-18 directive superseded the
three-term scope; no authoritative record was rewritten (the four-field record remains as
written, with the addendum below).

## 4. Correction (minimal; existing architecture and contracts untouched)

| File | Change |
|---|---|
| `engine/ipo_screening/presentation/service.py` | `MANUAL_ISSUE_TERM_FIELDS` += `fresh_issue` (five bounded fields); monetary validation for `fresh_issue` identical to `ofs` (finite, ≥ 0; explicit 0 = operator statement of a pure-OFS offer, never a default); mirror-gate and official-path comments/reason text updated to the new supply set — **the fail-closed gate itself is preserved** (genuinely absent `fresh_issue` still blocks naming `issue.fresh_issue`). |
| `engine/ipo_screening/presentation/api.py` | `/ingest/manual-terms` accepts an optional `fresh_issue` form field (explicit 0 preserved exactly; absent field omitted); docstring records the five-field contract. |
| `frontend/api.js` | Posts `fresh_issue` (explicit `0` preserved, never treated as empty). |
| `frontend/app.js` | Fifth input (`#mt-fresh-issue`) with unit-aware label from the awaiting payload's `reporting_unit`; enterable-set updated (genuinely non-enterable terms such as `issue.open_date` remain blockers); contract text states five terms; result table shows the manual fresh amount with its unit. |

No scoring formula, weight, threshold, knockout, ranking, golden fixture or frozen-core file
changed (`derived.py`, `scoring.py`, `knockouts.py`, `evaluation.py`, `snapshots.py`,
`price_band_notice.py` untouched; `verify_frozen_core` green). No fabricated or defaulted
amount: the value is either extracted, officially resolved, or explicitly operator-supplied
with a mandatory explanation and `MANUAL_ENTRY` / `verified: false` provenance. The
`OFFICIAL_VERIFIED`-never-displaced rule applies to `fresh_issue` as to every other field.
Discovery `UNAVAILABLE` stays `UNAVAILABLE` beside `manual_entry`. The audit-log contract
(manual submission/receipt/validation/conflict/acceptance events with values and correlation
ids, 2026-10-19) covers the fifth field automatically.

## 5. Proven end to end (Phase 4 matrix)

New suite `tests/test_fresh_issue_manual_entry.py` (12 tests) — the exact observed failure, not
helper functions:

1. **Reproduction preserved fail-closed:** real Jio PDF (`U72900GJ2019PLC110816_JIO.pdf`) +
   four-field submission → `422 AWAITING_ISSUE_TERMS`, `missing_fields == ["fresh_issue"]`,
   nothing persisted. (The gate follows the contract.)
2. **Dead end closed:** the same real Jio PDF + five-field submission (broker-page-style
   values) → `201`; all five values in the canonical evaluation input exactly as submitted;
   `MANUAL_ENTRY` / `verified: false` evidence on every field; `issue_terms.status ==
   "UNAVAILABLE"` (discovery preserved); evaluation persisted with a score; audit record
   retrievable at `GET /api/v1/ingestions/{id}` with `manual_submission` → `manual_entry` →
   `evaluation/completed` → `persistence/completed`, the accepted event carrying
   `values.fresh_issue`.
3. Fast synthetic five-field completion (golden-based filing, all five nulled).
4. **No fabricated/defaulted value:** unsupplied `fresh_issue` stays fail-closed with the
   precise field named; partial submission of only `fresh_issue` keeps the other terms
   blocked; explicit `0` is preserved as an operator pure-OFS statement; negative/NaN/Inf are
   rejected with `400 VALIDATION_ERROR` and nothing persisted.
5. **Semantics unchanged:** manual `fresh_issue` never displaces an `OFFICIAL_VERIFIED` value
   (`overridden_by_verified`); identical values score identically whether extracted or
   manually supplied (same `final_score`/`verdict`); a conflicting manual value blocks with
   `409 ISSUE_TERM_CONFLICT` until explicitly confirmed and then stays `MANUAL_ENTRY`.

## 6. Tests (all executed; exit codes in the tracker entry)

| Command | Result |
|---|---|
| `pytest tests/test_fresh_issue_manual_entry.py -q` | 12 passed |
| `pytest tests/ -q` (full backend, first run) | 1090 passed, **1 flake**: `test_reproducibility_store.py::test_workbook_bytes_are_deterministic` (two immediate `workbook_bytes` projections of one record compared for byte-equality; unrelated to this change — no workbook/scoring file touched; passes in isolation and in-file) |
| `pytest tests/ -q` (full backend, re-run) | **1091 passed**, exit 0 |
| `pytest tests/test_four_field_manual_terms.py tests/test_step5_auditor_and_manual_terms.py tests/test_manual_terms_audit_log.py -q` | 46 passed |
| `pytest tests/test_jio_rhp_issue_terms.py tests/test_generic_issue_terms_extraction.py tests/test_validation_gates.py tests/test_ui7_ingestion.py tests/test_ingestion_activity.py -q` | 86 passed |
| `pytest tests/test_frozen_core_line_endings.py tests/test_vishal_golden.py tests/test_issue_terms_resolver.py -q` | 30 passed |
| `pytest tests/test_v16_implementation.py -q` | 45 passed |
| `pytest tests/test_official_discovery.py tests/test_issue_terms_windows_retrieval.py -q` | 35 passed |
| `cd frontend && npm test` | 87 passed (incl. new: five-field panel/labels/transport, explicit-0 preservation) |

Existing tests and historical evaluations intact: the four-field suite (15) keeps its
fail-closed pin (docstring updated to the new contract); the Jio prospectus-pathway,
discovery-classification, audit-log, acceptance-matrix, golden (`GOLDEN_RESULT_HASH`) and
frozen-core suites all pass unchanged.

## 7. Verified vs inherited claims

**Verified here:** repository/branch/PR state; the exact gate and its origin (`a7f823d`); the
schema hard failure (empirical `SchemaValidationError` for None/absent); scoring consumption
(module C criteria); the full test matrix above; the Jio dead-end closure on the real filing
through the API (evaluation persisted, audit retrievable). **Inherited:** earlier operator
Windows acceptance runs; real-world broker-page contents (tests use test-scoped magnitudes;
no Jio value is asserted as a real-world fact).
