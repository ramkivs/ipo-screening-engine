# Manual Issue-Term Submissions Not Recorded in the Audit Log — 2026-10-19

**Branch:** `arena/d15866b5-ipo-screening-engine` **Base commit (this investigation):** `610223cab38cef506cf56ec4f884e788ba2144a3`
**Protocol:** VERIFY → REPRODUCE → TRACE → FIX → TEST → PUBLISH → RECONCILE (single pass)
**Status:** backend + frontend correction implemented and regression-tested; published on the
session branch. PR #6 remains OPEN/UNMERGED and cannot receive this fix at its head (GitHub API
cannot move `arena/5dd3fe52-ipo-screening-engine`); reconciliation recorded in the tracker.

## 1. Reported defect

When the user manually submits issue terms and the app processes them, the audit log must
accurately record the event. Reported behaviour: *"manual inputs submitted and processed but
audit log records nothing."* No UI-level cause was assumed; the full path was traced:
UI → API → validation/conflict → manual recording → evaluation → persistence → audit-event
creation → persistence → retrieval → presentation.

## 2. What the authoritative audit log is

The ingestion activity store (`engine/ipo_screening/presentation/ingestion_activity.py`): one
durable JSON trace per ingestion attempt in `ingestion-activity/` (event contract v1:
sequence/timestamp/stage/event_type/status/message/details/source_reference/error_code,
atomic tmp+replace writes), retrieved via `GET /api/v1/ingestions`, `GET /api/v1/ingestions/{id}`
and `GET /api/v1/ingestions/{id}/events` and presented in the UI's *Ingestion Activity* panel
(the panel inside the "Workflow Progress & Audit Status" card). This is the surface the report
means by "audit log"; `lifecycle.py` is the governance register (actor/reason) and was left
unchanged.

## 3. Reproduction (pre-fix evidence, captured at the reported state)

TestClient-driven reproduction against the reported behaviour (golden-based document with the
four issue terms nulled):

1. **Accepted submission** (`POST /api/v1/ingest/manual-terms`, four terms + explanation):
   `201`, response carried `ingestion_id`, and a persisted record existed with 24 events
   including `term_resolution/manual_entry/SUCCEEDED`. The backend store *did* record it —
   but the response's `ingestion_id` was never registered or displayed by the UI, and the
   audit panel (`#ingest-activity-panel`, outside `#ingest-view`) was never refreshed by the
   manual flow, so the operator's audit log showed nothing about the submission (a stale
   previous trace remained).
2. **Rejected submissions** (invalid OFS value, missing explanation): `400` bodies carried
   **no** `ingestion_id`/`activity_url`; `409` conflict body also had **no** correlation.
   The corresponding persisted records (FAILED/VALIDATION_ERROR, BLOCKED/CONFLICT) were
   therefore unreachable from the very flow that created them. `422` (unresolved terms) did
   carry `ingestion_id`.
3. **Event-content gaps** (found by reading the persisted records): no submission-receipt
   event (what was submitted was not recorded before validation), no conflict event with the
   conflict list, and the accepted event omitted the recorded values, the explanation and the
   `verified: false`/`ipo_id` facts.
4. **UI API client** (`frontend/api.js`): the error mapping read only nested
   `detail`/`details` payloads, but the app's `custom_http_exception_handler` returns the
   `HTTPException` detail dict **as the flat body** (`{error, message, code, ...extras,
   ingestion_id, correlation_id, activity_url}`). Correlation ids and diagnostics
   (conflicts/missing_fields/resolution) were dropped at this boundary even when present.

**Failing-layer classification:** predominantly **D (persisted but unreachable/not presented)**,
with **C (correlation lost at the API boundary)** and **A-adjacent event-content gaps**
(receipt/conflict events absent; accepted event lacked values). No layer B failure: the store
did create and persist records on every path. The defect description "records nothing" is what
the *operator* sees; the durable records existed but were invisible/unfindable, and the
rejected submissions' records could not be reached at all.

## 4. Root cause

The manual-terms flow was never wired into the ingestion-activity audit contract end to end:

- `POST /api/v1/ingest/manual-terms` error handlers omitted `**_activity_ref(exc)` (except the
  awaiting case), violating the established correlation contract pinned by
  `test_api_error_correlates_to_recoverable_history` ("every error response that identifies an
  ingestion includes both the ingestion_id and activity_url").
- `frontend/api.js` error mapping did not read the flat error-body contract, dropping
  `ingestion_id`/`correlation_id`/`activity_url` (and conflicts/missing_fields) even when the
  backend sent them.
- `frontend/app.js`'s manual-terms panel never registered `result.ingestion_id` into
  `localStorage` (`ipo.lastIngestionId`), never refreshed the Ingestion Activity panel, and
  never displayed any audit reference on the success or error result surfaces.
- `_ingest_document_impl`'s manual block emitted only the one `manual_entry` event — no
  submission receipt, no validation-rejection event, no conflict event — so rejected and
  conflicted submissions left traces that recorded the outcome but not the submission itself.

## 5. Correction (minimal, within the existing architecture)

No parallel audit subsystem, no schema invention; all new events stay inside the established
event contract v1 (stage `term_resolution`, statuses SUCCEEDED/FAILED/BLOCKED, sanitized
details):

| Layer | File | Change |
|---|---|---|
| Service | `engine/ipo_screening/presentation/service.py` | `term_resolution/manual_submission/SUCCEEDED` receipt (fields + submitted values + `explanation_supplied`) emitted **before** validation; `term_resolution/manual_validation/FAILED` (fields+values, `error_code=VALIDATION_ERROR`) on rejection; `term_resolution/conflict/BLOCKED` (conflicts + `confirmation_required: true`, `error_code=ISSUE_TERM_CONFLICT`) before the conflict raise; accepted `manual_entry` event extended with `values`, `explanation`, `verified: false`, `conflicts_confirmed`, `ipo_id` (existing `fields`/`overridden_by_verified`/`provenance`/`reporting_unit` retained). |
| API | `engine/ipo_screening/presentation/api.py` | `**_activity_ref(exc)` added to the remaining manual-terms error handlers (413/400/409/422-processing/500), so every failure body carries `ingestion_id`/`correlation_id`/`activity_url`. |
| API client | `frontend/api.js` | Error mapping at all three request sites now accepts the flat error-body contract (the `HTTPException` detail dict is the body) as well as nested `detail`, and preserves the audit correlation ids in `err.details`. |
| UI | `frontend/app.js` | `attachIngestionAudit()`: registers the submission's `ingestion_id` as `ipo.lastIngestionId` (even if the detail fetch fails) and re-renders the Ingestion Activity panel from `GET /api/v1/ingestions/{id}`; the manual result panel shows `Audit trace recorded: <ingestion_id>`; every error branch (conflict/awaiting/generic) shows `Audit trace: <ingestion_id>` and refreshes the panel when the error carries an id. |

Audit-evidence semantics after the correction (all seven distinctions required by the
workflow):

| Stage of the submission | Auditable evidence |
|---|---|
| submitted | `manual_submission/SUCCEEDED` event: fields (bare names), submitted values, `explanation_supplied` |
| validation-rejected | `manual_validation/FAILED` event naming the field(s) + rejection message; record `status=FAILED`, `error_code=VALIDATION_ERROR`; no evaluation, no persistence |
| conflict / confirmation-required | `conflict/BLOCKED` event with the conflict list (`field`/`manual_value`/`existing_value`/`existing_origin`) and `confirmation_required: true`; record `status=BLOCKED`, `error_code=ISSUE_TERM_CONFLICT` |
| accepted-and-recorded | `manual_entry/SUCCEEDED` event: fields, **values**, explanation (or reference), `provenance: MANUAL_ENTRY`, `verified: false`, `conflicts_confirmed`, `ipo_id`, `reporting_unit`, `overridden_by_verified`; correlated to the evaluation via `record.result.evaluation_id` / `result.ipo_id` |
| evaluation-completed | `evaluation/started` + `evaluation/completed` (`final_score`/`verdict`), `persistence/completed`, `finalization/completed` — recorded as distinct steps from the submission events |
| processing-failed-after-submission | record `status=FAILED` (`PROCESSING_FAILED`), `finalization/terminated/FAILED`, `evaluation_run=false`, `persisted=false`, `result=null` — no false success |
| audit-recording-failed (if detectable) | audit save failures propagate loudly (existing contract): the operation returns an error (422/500), never a 201; no silent swallowing |

Retrieval (end to end): `GET /api/v1/ingestions/{id}` (record + events),
`GET /api/v1/ingestions/{id}/events?after_sequence=` (incremental), `GET /api/v1/ingestions`
(listing) — and the Ingestion Activity panel in the UI.

## 6. Safeguards preserved (explicitly verified, not changed)

- No scoring, weights, thresholds, knockout or ranking changes; no golden-snapshot changes.
- No inferred terms; no default/zero-fill for `issue.ofs` (explicit 0 valid; negatives and
  non-finite rejected; fail-closed for invalid/incomplete).
- Conflict-confirmation semantics unchanged; `OFFICIAL_VERIFIED` values never displaced.
- `discovery: UNAVAILABLE` stays `UNAVAILABLE` (discovery path untouched).
- Per-IPO isolation; no secrets or document contents in event details (sanitizer bounds apply).
- Existing actor/ownership conventions untouched (no invented user identity).
- Provenance never upgraded: `MANUAL_ENTRY` + `verified: false` in events and evaluation
  evidence; no `SRC-PBN-`/`SRC-PROSPECTUS-` source claimed for manual values.
- Atomicity: unchanged per the existing contract — each activity write is atomic
  (tmp+replace); there is **no** transaction spanning evaluation persistence and audit
  persistence. If the audit store fails at finalization, the API reports failure (never a
  silent success); an evaluation artifact may exist. This is documented, not "fixed"
  (no new guarantee invented).
- The Windows-verified discovery fix (`5d9597c`) and its regressions remain in ancestry
  (nothing on those paths was touched).

## 7. Tests (all executed; commands and exit codes in the tracker entry)

New `tests/test_manual_terms_audit_log.py` (12 tests) — creation **and** end-to-end retrieval:
successful submission → retrievable record/events/listing with receipt/acceptance/evaluation/
persistence steps distinct; IPO/evaluation association; MANUAL_ENTRY provenance never upgraded;
rejected submissions recorded as rejections with correlation and no false success (parametrized
invalid OFS/inverted band/non-integer lot + missing explanation); conflict/confirmation
audited with existing semantics; evaluation failure without false success; audit-store failure
never reported as success (both at-recording and at-finalization); per-IPO isolation.

Frontend `frontend/test/manual-terms.test.js` (+5 tests): flat error-contract mapping
preserves the audit correlation ids (reproduces the boundary defect); successful manual
submission registers the id and displays the audit trace (result panel + Ingestion Activity
panel refreshed from the record); rejected submission and conflict responses show their audit
references; failures without an id keep the established wording.

## 8. Verified vs inherited claims

**Verified here (executed in this investigation):** pre-fix reproduction (items 1–4 above);
the full trace; the correction's behaviour via the new regression suites; full backend suite
(1079 passed, exit 0); frontend suite (85 passed, exit 0); frozen/golden/resolver (30),
v1.6 (45), four-field + step5 (34), discovery + Windows-retrieval (35); audit-record contents
(events, values, provenance, ids) read back through the retrieval API.

**Inherited from earlier reports (not re-verified here):** operator Windows acceptance runs
(5d9597c discovery fix, real-RHP E2E in the four-field report) — still outstanding for this
fix; external source behaviour beyond the fixtures.
