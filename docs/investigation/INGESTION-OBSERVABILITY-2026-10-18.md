# Ingestion Observability — Structured Events, Live UI Timeline & Recoverable Diagnostics (2026-10-18)

## Initial findings

- The ingestion lifecycle was a single synchronous path
  (`POST /ingest/document` → `PresentationService.ingest_document` →
  extraction → issue-terms resolver → `evaluate()` →
  `EvaluationStore.write`) with **no lifecycle events, no correlation
  id, and no durable record of attempts that failed or were blocked**.
  Diagnostics existed only inside the exception payload (`resolution`
  provider reports on `IngestionAwaitingIssueTermsError`), discarded
  with the HTTP response; the UI additionally fabricated stage
  progress (it marked extraction/evaluation stages from the mere fact
  that the request returned).
- Persistence primitives reused: the filesystem `EvaluationStore`
  conventions (JSON artifacts, sibling directories) — with the strict
  separation that activity traces live in a **sibling**
  `ingestion-activity/` directory, never inside the evaluation store,
  so a failed ingestion's durable diagnostic record can never be
  mistaken for an evaluation artifact. No database, no streaming
  stack: single-user scope, polling over the existing REST API.

## Implementation

- **Event contract v1** (`presentation/ingestion_activity.py`): each
  event carries `ingestion_id`, `correlation_id` (same id),
  `sequence` (deterministic order), `timestamp`, `stage`,
  `event_type`, `status` (`PENDING/RUNNING/SUCCEEDED/FAILED/BLOCKED/
  SKIPPED/CANCELLED`), `message`, sanitized `details`, `duration_ms`,
  `source_reference`, `error_code`, `retryable`. Overall ingestion
  status is distinct from stage status; every attempt ends in exactly
  one terminal status (`SUCCEEDED/FAILED/BLOCKED/CANCELLED`).
- **Backend instrumentation at real boundaries** in
  `_ingest_document_impl`: upload received, document validation,
  filing extraction, issuer identification, per-term filing states,
  official discovery start, per-provider source attempts (provider,
  outcome, detail, response-identity reasons — including the BSE
  homepage wrong-page classification), per-term resolution states
  (extracted/accepted/missing/conflicting/unavailable), manual entry,
  evaluation eligibility (blocked with reasons), evaluation,
  persistence (incl. duplicate-skip), and a finalization summary.
  Terminal recording happens in the `ingest_document` wrapper before
  any exception propagates; the exception carries `ingestion_id` so
  API errors correlate to the recoverable history. Unexpected
  exceptions produce a safe FAILED trail (exception type only, no
  stack traces or content).
- **Persistence/retention**: one JSON file per ingestion, atomically
  replaced on each event; bounded retention (newest 200). Sanitizer
  drops credential/cookie/token keys, truncates strings, bounds
  nesting; no document content or raw response bodies are stored.
- **API**: `POST /api/v1/ingestions/start` (202, background thread
  running the unchanged synchronous service path; added to the
  write-scope guard's authorized POST list under the same loopback +
  same-origin rules), `GET /ingestions/{id}`, `GET
  /ingestions/{id}/events?after_sequence=`, `GET /ingestions`.
  Synchronous ingest endpoints unchanged in semantics; their error
  payloads (and success responses, via `IngestionResponse`) now carry
  `ingestion_id`/`correlation_id`/`activity_url`. Unknown ids return a
  safe 404 `INGESTION_NOT_FOUND`.
- **UI**: an Ingestion Activity panel in the ingest view renders the
  persisted backend events in sequence (status badges, expandable
  sanitized details, durations, source references), a current-status
  header, and a terminal summary (evaluation run? persisted?
  unresolved terms, reason, next action). Submission uses
  start + polling (1.2s, duplicate-safe by full-record re-render,
  connection-failure tolerant); completion-before-attach and
  page-refresh recovery are handled by re-fetching the durable record
  (last ingestion id kept in localStorage). All rendered diagnostic
  text is HTML-escaped. Clients without the activity API keep the
  previous synchronous flow.
- **Per-term observability**: `issue.price_band_low/high`,
  `issue.lot_size`, `issue.ofs`, `issue.fresh_issue` each get filing
  and post-discovery states; retrieval failure is labelled
  `unavailable`, distinct from `missing` — never unpublished-by-default.

## Regression coverage

Backend (`tests/test_ingestion_activity.py`, 7 tests): contract
ordering/persistence, sanitization/redaction, bounded retention, the
**Jio homepage scenario end-to-end** (durable BLOCKED trace naming the
homepage wrong-page reason, evaluation/persistence SKIPPED, no
evaluation artifact), successful-ingestion trace fidelity, API error
correlation → recoverable history, unknown-id 404, and async
start → live polling to terminal. Frontend
(`frontend/test/ingestion-activity.test.js`, 4 tests): start-endpoint
FormData, event polling parameters, ordered rendering + terminal
summary, XSS escaping of untrusted diagnostic text. One pre-existing
signature-pin test was extended for the internal `recorder`
parameter (not request-controlled; justification recorded in the
test). Fixture-driven throughout — **not live-source acceptance**.

## Known limitations / acceptance

- Live delivery is polling (chosen over SSE as the smallest reliable
  mechanism for this architecture); the trace itself is durable
  regardless of the live connection.
- Jio discovery itself is unchanged by this work: on the user's
  Windows runtime it remains accepted-or-failing on its own evidence.
  What changes is that the next attempt's activity panel shows the
  actual stage, source response classification, unresolved terms and
  final decision without manual log/PowerShell archaeology.
- Windows acceptance: restart at this commit, upload the Jio RHP, and
  read the Ingestion Activity panel (it survives refresh; the trace
  is also returned by `GET /api/v1/ingestions/{id}`).

## Addendum 2026-10-18: panel visibility fix

**User report:** the Ingestion Activity panel could not be located in
the running UI at `22f82b8`. **Trace:** route `#ingest` →
`renderIngestView()` mounts `#ingest-activity-panel` inside the
"Workflow Progress & Audit Status" card, and the submit handler does
use `POST /ingestions/start` + polling when the real `ApiClient` is
present (verified by simulation and by fetching the served
`/ui/app.js`). **Defect:** the panel was an empty, unlabelled `<div>`
until the first poll returned — nothing on screen identified an
Ingestion Activity panel before, between, or after submissions
unless a trace happened to render into it. **Fix:** the panel now
renders a permanent visible shell (title, IDLE state, guidance, and
automatic restoration of the most recent trace after refresh).
**Integration test** (`frontend/test/ingestion-activity-flow.test.js`):
the shell is present in the rendered view before submission, and a
submission through the view (activity endpoints only — the legacy
sync method is absent from the double) populates the panel with the
blocked-ingestion backend events, terminal summary, unresolved
terms, and evaluation-run/persisted facts.
