# Four-Field Manual Issue-Term Entry — Initial Screening Without Waiting for Official Sources (2026-10-18)

- **Date:** 2026-10-18 · **Repository:** `ramkivs/ipo-screening-engine` · **Baseline:** session branch `arena/d15866b5-ipo-screening-engine` fast-forwarded to the Windows-verified discovery tip `e05c0efbca1ecb3024e52da73a22e180ea171118` (contains `5d9597c46a0a73171f33daee0db44b6e8e28f194` in ancestry) · PR #6 OPEN, unmerged · **Nature:** implementation record (user-directed scope extension of Step 4 Area C / Step 5 manual entry).
- **Directive:** the user screens an IPO as soon as it appears on a broker platform. All four required issue terms must be manually enterable so initial screening never waits for NSE/BSE/SEBI retrieval. Manual values stay distinguishable from verified official evidence. No scoring, threshold, ranking, knockout, or integrity-safeguard change.

---

## 1. Proven root cause of the OFS manual-entry blockage

Proved against the code at `e05c0ef` (not inferred from prior reports):

1. **Categorical scope restriction.** `presentation/service.py` declared
   `MANUAL_ISSUE_TERM_FIELDS = ("price_band_low", "price_band_high", "lot_size")`.
   Any submission carrying `ofs` was rejected by the service
   (`"Manual issue-term entry is limited to price_band_low, price_band_high
   and lot_size; unsupported field(s): ['ofs']"`), and the API endpoint
   (`POST /api/v1/ingest/manual-terms`) had no `ofs` form field at all.
2. **UI prohibition.** `frontend/app.js` `renderManualTermsPanel()` had
   `ENTERABLE = ['price_band_low', 'price_band_high', 'lot_size']`; a missing
   `issue.ofs` was rendered as "*cannot be entered manually; requires an
   official source or filing disclosure*". The label map already called the
   field "Offer For Sale (₹ lakh)" but the input did not exist.
3. **Downstream strand.** The eligibility gate requires
   `("price_band_low", "price_band_high", "lot_size", "ofs")` complete.
   The approved OFS **derivation** (seller shares × cap price, `SRC-DERIVED`)
   runs only inside `EnrichmentEngine.assemble` — i.e. only when a verified
   notice/prospectus assembly runs, or when `missing_issue_fields == {"ofs"}`
   exactly. For a filing whose four terms are all `[●]` and whose official
   discovery fails (the exact Windows scenario), no assembly runs, so the
   derivation cannot fire; with manual entry unable to supply `ofs` either,
   the workflow stranded on `issue.ofs` forever. The regression
   `test_vishal_real_filing_manual_entry_fills_only_authorized_terms`
   pinned exactly this: three manual terms → `422`, `missing_fields == ["ofs"]`.

So the blockage was a **scope decision implemented end to end**
(service allow-list + API surface + UI enterable list + the awaiting copy),
not a defect in scoring or evaluation. The Step 4 decision record
(`STEP-4-CONTRACT-DECISION-INPUT-2026-10-17.md`, Area C, minimum decision
item 5) had limited scope to the three pricing terms "(OFS remains derived
only)". The 2026-10-18 user directive supersedes that scope item: OFS must
be manually enterable. The other four parameters of the approved minimum
decision (MANUAL_ENTRY/UNVERIFIED labelling, mandatory explanation, conflict
handling with explicit confirmation, no provenance upgrade) are preserved
unchanged and are not weakened by this extension.

## 2. Canonical meaning, type and unit of `issue.ofs`

Established from the v1.5 input contract and the enrichment engine (not
invented here):

- **Schema** (`schema/ipo-input.v1.5.schema.json`): `issue.ofs` is
  `{"type": "number", "minimum": 0, "description": "in reporting_unit"}`.
- **Unit:** the monetary amount is stated **in the filing's
  `financials.reporting_unit`** (`INR_LAKHS` or `INR_CRORES`; e.g. the
  Vishal Nirmiti RHP: `ofs: 3300` with `INR_LAKHS` = ₹3,300 lakh = ₹33 crore).
- **Meaning:** the **Offer-for-Sale monetary amount** — never a share count
  and never a boolean. The approved derivation confirms the semantics:
  `OFS amount = sum(seller shares) × price_band_high / unit_multiplier`
  (`enrichment_engine.py`, `SRC-DERIVED` formula provenance;
  1,500,000 × ₹220 / 100,000 = 3,300 for Vishal).
- **Zero semantics:** `minimum 0` makes an explicit `0` a legitimate
  operator statement of "no offer for sale"; it is **never** a default for
  an unknown value (the fail-closed no-zero-substitution policy stands:
  a missing OFS is missing, not 0).

## 3. Four-field manual-input contract

`POST /api/v1/ingest/manual-terms` (unchanged route and guards) now accepts:

| Form field | Canonical field | Type / constraints |
|---|---|---|
| `price_band_low` | `issue.price_band_low` | finite number > 0 (₹ per equity share) |
| `price_band_high` | `issue.price_band_high` | finite number > 0 (₹ per equity share); `price_band_low ≤ price_band_high` |
| `lot_size` | `issue.lot_size` | finite whole number ≥ 1 (equity shares) |
| `ofs` | `issue.ofs` | finite number ≥ 0 (monetary amount in the filing's reporting unit; explicit 0 = no OFS) |

- All four are **individually optional per submission** (the engine names
  whatever is still missing), but all four are **required to complete**
  evaluation eligibility. A complete valid set proceeds; an incomplete or
  invalid set remains `AWAITING_ISSUE_TERMS` (or 400 for invalid values).
- **Validation** (service-level, field-specific messages): numeric type
  (bool rejected), finiteness (NaN/Inf rejected), positivity for
  floor/cap/lot, whole-number lot, non-negative OFS, band consistency
  (also re-checked after application). Invalid submissions are rejected
  outright — nothing is coerced to 0/null/defaults and nothing persists.
- **Explanation** remains mandatory for any manual entry (unchanged).
- **`issue.fresh_issue` is not part of the manual contract** (the directive
  scopes exactly four fields). When the filing does not state the fresh
  amount, evaluation now fails closed naming `issue.fresh_issue` precisely
  (both after official resolution — existing behaviour — and after manual
  completion — new mirror gate) instead of a schema failure. Nothing is
  invented.

## 4. Provenance and conflict handling (unchanged policy)

- Every applied value is recorded with `extraction_method: MANUAL_ENTRY`,
  `source_id: SRC-MANUAL-ENTRY`, the operator's explanation verbatim in the
  evidence note, and presented `UNVERIFIED` ("MANUALLY ENTERED (Not
  Source-Verified)") — in the ingest response (`issue_terms.manual_entry`),
  the evidence API, and the persisted record. `verified: false` is explicit.
- The exact submitted values are preserved (manual OFS recorded as entered).
- A conflict with an existing value blocks with `409 ISSUE_TERM_CONFLICT`
  until explicitly confirmed; confirmation never upgrades provenance.
- A verified official value (`SRC-PBN-*` / `SRC-PROSPECTUS-*`) is **never**
  displaced by a manual entry, even after confirmation
  (`overridden_by_verified` is reported).
- Issuer/IPO isolation: manual terms travel only within their own upload
  request; nothing is cached or reused across issuers (regression-tested).
- **Discovery outcome preservation:** a manual completion reports the
  official-discovery outcome alongside `manual_entry` (status stays
  `UNAVAILABLE` where appropriate, `verified: false`). Manual input is a
  separate source of screening input and never evidence that an official
  source published or verified anything. Discovery classification
  (`issue records not page chrome`, `5d9597c`) is untouched; its regressions
  pass unchanged.

## 5. Evaluation eligibility, scoring and persistence

- With all four terms present (any accepted combination of filing
  extraction, verified official resolution/derivation, and manual entry),
  the **existing** `pipeline.evaluate()` runs unchanged; the manual pathway
  introduces no parallel scoring engine and changes no formula, weight,
  threshold, ranking, or knockout.
- Valid four-field evaluations follow the existing persistence pathway
  (immutable `EvaluationStore`, lifecycle registration, duplicate
  idempotency). Nothing persists while required terms are unresolved or
  invalid (fail-closed preserved).
- Result identification: the response `issue_terms` carries
  `manual_entry` (fields, exact values, explanation, `provenance:
  MANUAL_ENTRY`, `verified: false`, `reporting_unit`) next to the discovery
  outcome; the UI result panel shows the evaluated values with the
  "MANUALLY ENTERED (Not Source-Verified)" badge.

## 6. UI

The AWAITING panel (`renderManualTermsPanel`) now provides all four inputs,
with the OFS label carrying the canonical unit taken from the engine payload
(`resolution.reporting_unit` → "amount in ₹ lakh" / "amount in ₹ crore").
The panel states: all four values are required for the manual initial-
screening pathway; values may be supplied from the broker platform; manual
values are unverified and carry `MANUAL_ENTRY`; manual input does not
establish official-source verification; invalid or incomplete values prevent
evaluation. After submission the result panel shows the values the engine
actually evaluated with their provenance and the operator explanation. The
same filing is re-submitted from the retained upload (no re-pick); no extra
confirmation steps were added.

## 7. Tests (all executed; see tracker entry for commands/exit codes)

`tests/test_four_field_manual_terms.py` (new, 15 tests):
complete four-field submission reaches scoring (recorded score reproduced by
replaying the persisted input through `pipeline.evaluate()`), exact values +
MANUAL_ENTRY provenance on all four, evidence API UNVERIFIED; omission of
each field individually (parametrized, `issue.ofs` included) stays blocked
with the precise field named; OFS omission on a fully unresolved issue
(root-cause regression); missing `fresh_issue` fails closed precisely;
invalid OFS (negative/NaN/Inf/bool/string) and invalid band/lot rejected
without defaulting; explicit OFS 0 accepted as submitted; OFS conflict with
filing value blocks until confirmed; manual never displaces
`OFFICIAL_VERIFIED`; per-IPO isolation; manual completion preserves
`UNAVAILABLE` discovery outcome.

`tests/test_step5_auditor_and_manual_terms.py` (updated):
the real Vishal RHP regression keeps the three-term omission blocked on
`issue.ofs`, and the new
`test_vishal_real_filing_four_field_manual_entry_completes_evaluation`
proves the **complete path end to end on the real filing** — extraction →
discovery UNAVAILABLE → four manual terms (208/220/68/3300 in INR_LAKHS) →
existing engine evaluates (24.0 INSUFFICIENT_DATA) → persisted with
MANUAL_ENTRY on all four, recorded score reproduced from the persisted
input.

Frontend `frontend/test/manual-terms.test.js` (extended, +3 tests):
four fields posted (OFS preserved, explicit 0 preserved, absent fields never
fabricated), panel offers all four with unit-aware OFS label and states the
contract, four-field submission shows evaluated values + provenance.

Discovery regressions (`tests/test_official_discovery.py`,
`tests/test_ingestion_activity.py`, resolver/runtime/API suites) run
unchanged and pass — the Windows-verified classification behaviour is
intact.

## 8. Governance note

This record implements the user's explicit 2026-10-18 directive to extend
the Step 4 Area C minimum decision's scope item (5) from three terms to the
four required terms. The other minimum-decision parameters are unchanged.
No authoritative governance record was rewritten to manufacture authority:
the Step 4 record remains as written (its Area C scope clause is now
superseded by this directive, recorded here and in the tracker). No
genuine unresolved governance issue blocks this feature; `issue.ofs`'s
canonical contract was unambiguous (monetary amount in `reporting_unit`).

## 9. Audit trail for manual submissions (added 2026-10-19)

Every manual issue-term submission — accepted, rejected or conflicted — now has an accurate,
retrievable audit record in the ingestion activity log (see
`MANUAL-TERMS-AUDIT-LOG-2026-10-19.md` for the investigation, reproduction evidence and
full contract):

- **Submitted:** `term_resolution/manual_submission/SUCCEEDED` — fields (bare names), the
  submitted values, and whether an explanation was supplied. Emitted *before* validation, so a
  rejected submission still records exactly what was submitted.
- **Rejected:** `term_resolution/manual_validation/FAILED` — the offending field(s) and the
  rejection message; record `FAILED/VALIDATION_ERROR`; nothing evaluated or persisted.
- **Conflict / confirmation required:** `term_resolution/conflict/BLOCKED` — the conflict list
  (`field`, `manual_value`, `existing_value`, `existing_origin`) and `confirmation_required:
  true`; record `BLOCKED/ISSUE_TERM_CONFLICT`.
- **Accepted:** `term_resolution/manual_entry/SUCCEEDED` — fields, applied **values**,
  the operator explanation (or reference), `provenance: MANUAL_ENTRY`, `verified: false`,
  `conflicts_confirmed`, `ipo_id`, `reporting_unit`, `overridden_by_verified`. Evaluation and
  persistence are separate, later events; the record links the evaluation via
  `result.evaluation_id` and `result.ipo_id`.
- **Correlation:** every manual-terms API response — including 400/409/422/500 errors —
  carries `ingestion_id`, `correlation_id` and `activity_url`
  (`/api/v1/ingestions/{ingestion_id}`). The UI registers the id (`ipo.lastIngestionId`),
  refreshes the *Ingestion Activity* panel and shows `Audit trace: <id>` on both success and
  error surfaces.
- **Retrieval:** `GET /api/v1/ingestions` (list), `GET /api/v1/ingestions/{id}` (record + full
  event list), `GET /api/v1/ingestions/{id}/events?after_sequence=` (incremental).

Provenance is never upgraded by recording: manual values remain `MANUAL_ENTRY` / unverified in
both the audit events and the evaluation evidence. If the audit store itself fails, the
operation fails loudly (422/500) — it is never presented as an auditable success.
