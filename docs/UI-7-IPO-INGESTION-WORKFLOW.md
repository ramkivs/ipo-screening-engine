# UI-7 IPO Document Ingestion & Deterministic Evaluation Workflow

## 1. Executive Summary & Objective

Prior to UI-7, the IPO Screening Presentation layer operated purely on pre-evaluated records pre-populated in the local filesystem store. While complete read models, scorecards, evidence explorers, and performance trackers were delivered across UI-1 through UI-6, the system lacked the end-to-end user workflow:
$$\text{Browser Upload (PDF)} \longrightarrow \text{Document Extractor} \longrightarrow \text{Canonical Normalisation} \longrightarrow \text{v1.5 Scoring Engine} \longrightarrow \text{EvaluationStore} \longrightarrow \text{Interactive Presentation UI}$$

**UI-7 delivers this core capability** in full compliance with the institutional invariants of the IPO Screening Engine:
1. **Interactive Upload Surface (`#ingest`)**: High-contrast drag-and-drop dropzone, file validation preview, evaluation mode selection, discrete stage progression (Ready $\rightarrow$ Uploading $\rightarrow$ Extracting $\rightarrow$ Evaluating $\rightarrow$ Completed / Failed), and instant navigation to the generated scorecard.
2. **Bounded Server-Side Ingestion Endpoint (`POST /api/v1/ingest/document`)**: Secure multipart/form-data ingestion with strict boundary guards:
   - File presence and non-empty check.
   - Bounded payload size ($\le 50\text{ MB}$).
   - Strict magic bytes validation (`%PDF-`).
   - Evaluation mode validation (`final` or `preliminary`).
   - Isolated deterministic staging with automated directory cleanup.
3. **Engine Integration Without Duplication**: Direct invocation of authoritative engine modules:
   - `engine/ipo_screening/extraction/extractor.py` (`DocumentExtractor`)
   - `engine/ipo_screening/canonical_input.py` (`build_canonical_input`)
   - `engine/ipo_screening/pipeline.py` (`evaluate`, `load_config`)
   - `engine/ipo_screening/evaluation.py` (`EvaluationStore`)
4. **Idempotency & Duplicate Protection**: Identical filings uploaded repeatedly are detected via matching canonical `input_snapshot_hash` and `config_hash` or `result_hash`, returning `HTTP 200 OK` with `is_duplicate: true` rather than violating immutability invariants or clobbering historical evaluations.
5. **Multi-IPO Coexistence**: Proves via automated integration tests that secondary and tertiary IPO filings (e.g. `Apex Housing Finance Limited`, `Zenith Heavy Forgings Limited`) can be ingested dynamically at runtime without server restart, appearing immediately in directory discovery alongside `Vishal Nirmiti Limited`.
6. **Zero Browser Calculation Authority**: All extraction, OCR, table routing, metric derivation, knockout resolution, and scoring calculations occur strictly server-side.
7. **Absolute Frozen Core Preservation**: Zero functional changes to `derived.py`, `scoring.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`, or `extraction/price_band_notice.py`. The golden Vishal Nirmiti evaluation hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` remains 100% bit-for-bit preserved.

---

## 2. Architecture & Data Flow

```
                           [ Web Browser ]
                                  │
         1. Drag & Drop PDF / File Picker (#ingest view)
         2. Client-side Format & Size Pre-flight (PDF, <= 50 MB)
                                  │
                                  ▼
           [ POST /api/v1/ingest/document (multipart/form-data) ]
                                  │
         3. Strict Read-Only Guard Middleware:
            Allows strictly POST /api/v1/ingest/document;
            Blocks all other mutations with HTTP 405 Method Not Allowed.
                                  │
         4. Server-Side Size Guard: Reject payload > 50 MB (HTTP 413)
         5. Magic Bytes Gate: Enforce %PDF- prefix (HTTP 400)
         6. Mode Gate: Enforce mode in {'final', 'preliminary'} (HTTP 400)
                                  │
                                  ▼
          [ Isolated Deterministic Staging Directory ]
              /tmp/ipo_ingest/<content_sha256[:16]>/filing.pdf
                                  │
                                  ▼
             [ DocumentExtractor.extract_from_pdf() ]
            (TOC routing, domain sections, financial tables)
                                  │
                                  ▼
               [ CanonicalInput & Schema Validation ]
                                  │
                                  ▼
                 [ pipeline.evaluate() (Policy v1.5.0) ]
            (Snapshots, derived metrics, overlays, knockouts, scorer)
                                  │
                                  ▼
             [ Duplicate / Idempotency Check vs Store ]
                     ├── Exists in EvaluationStore?
                     │       └── YES ──> Return 200 OK (is_duplicate: true)
                     │
                     └── NO ───> EvaluationStore.write(record)
                                 └── Return 201 Created (is_duplicate: false)
                                  │
                                  ▼
         [ Stage Progress Completion & Dynamic Navigation ]
             Client UI updates progress stages to COMPLETED,
             renders evaluation summary card, and offers direct
             link to '#evaluations/<evaluation_id>'.
```

---

## 3. OpenAPI 3.1.0 Contract Specification

```yaml
  /ingest/document:
    post:
      summary: Ingest and evaluate an IPO filing document (DRHP/RHP PDF)
      description: |
        Uploads a PDF filing document, extracts domain entities using DocumentExtractor,
        converts into CanonicalInput, validates, runs deterministic evaluation,
        and persists the record to the immutable EvaluationStore.
        Duplicate uploads return the existing evaluation idempotently.
      operationId: ingestDocument
      tags: [Ingestion]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file]
              properties:
                file:
                  type: string
                  format: binary
                  description: PDF filing document (DRHP/RHP)
                mode:
                  type: string
                  enum: [final, preliminary]
                  default: final
                  description: Evaluation mode
                reference_base_path:
                  type: string
                  description: Optional reference base fixture path for fallbacks
      responses:
        '200':
          description: Evaluation already exists (duplicate idempotent return)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/IngestionResponse'
        '201':
          description: Document successfully ingested and new evaluation created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/IngestionResponse'
        '400':
          description: Bad request (invalid PDF magic bytes, empty file, or invalid mode)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiError'
        '413':
          description: Payload too large (file exceeds 50 MB limit)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiError'
        '422':
          description: Document extraction or evaluation failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiError'
```

### IngestionResponse Schema:
```json
{
  "evaluation_id": "APEX-HOUSING-FINANCE-LIMITED-20261006-120000Z-final-79385bca",
  "ipo_id": "APEX-HOUSING-FINANCE-LIMITED",
  "company_name": "APEX HOUSING FINANCE LIMITED",
  "evaluation_mode": "FINAL",
  "result_hash": "79385bca35358a030d61d5e12d16f6fb78b9183f2e99971aa8d82aec7dd88cfa",
  "final_score": 40.0,
  "verdict": "INSUFFICIENT_DATA",
  "confidence": "Low",
  "is_duplicate": false,
  "message": "Filing successfully ingested, extracted, and evaluated.",
  "evaluation_url": "/#evaluations/APEX-HOUSING-FINANCE-LIMITED-20261006-120000Z-final-79385bca",
  "evaluation": { ... }
}
```

---

## 4. Invariant Verification & Delivery Metrics

### Test Suite Execution Summary:
- **Python Tests**: 67 presentation and golden acceptance tests passed in 2.69s (100%).
  - `tests/test_ui7_ingestion.py`: 9 passed
  - `tests/test_presentation_api.py`: 21 passed
  - `tests/test_ui2_frontend.py`: 7 passed
  - `tests/test_ui3_evidence.py`: 8 passed
  - `tests/test_ui4_performance.py`: 8 passed
  - `tests/test_ui5_backtest.py`: 8 passed
  - `tests/test_ui6_calibration.py`: 8 passed
  - `tests/test_vishal_golden.py`: 19 passed
- **Node.js Test Suites**: 53 passed in 0.50s across 7 suites (`api.test.js`, `app.test.js`, `evidence.test.js`, `performance.test.js`, `backtest.test.js`, `calibration.test.js`, `ingest.test.js`).
- **Frozen Core Hash**: Verified identical across all 6 core modules via `verify_frozen_core()`.
- **Golden Evaluation Hash**:
  $$\text{Golden Hash} = \texttt{e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1}$$
  Strictly preserved and verified bit-for-bit identical.
- **Read-Only Enforcement**: Middleware strictly blocks `PUT`, `PATCH`, `DELETE` across the entire API, and blocks `POST` on all routes except `/api/v1/ingest/document`.
- **Zero Browser Authority**: Frontend code contains no mathematical weight constants, scoring formulas, or metric derivations.
