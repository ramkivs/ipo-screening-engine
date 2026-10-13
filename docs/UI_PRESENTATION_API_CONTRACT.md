# IPO Screening Engine — UI Presentation API Contract & Read-Model Specification

**Document ID:** `DOC-UI-PRESENTATION-API-CONTRACT-V1`  
**API Version:** `v1`  
**OpenAPI Specification:** `docs/openapi/presentation-api-v1.yaml` (OpenAPI 3.1.0)  
**Authoritative Engine Lineage:** Commit `690d4722294f18b4897676ede8392314f63f3128`  
**Program Authority:** Ramki  
**Governance Mode:** Read-Only Presentation Layer (No Scoring Calculations / No Store Mutation / No v1.6 Activation)  

---

## 1. Purpose & Architectural Principles

This document formalizes the frozen data contract for the **IPO Screening Engine Presentation API (v1)**. 

The Presentation API serves as a decoupled, read-only bridge between the authoritative calculation engine and future user interfaces (web dashboards, analytical views, and audit tools). It adheres to strict foundational principles:

### Core Principles:
1. **Zero Calculation Authority**: The API and the frontend client are **strictly forbidden** from calculating scores, deriving metrics, re-evaluating knockouts, computing post-listing returns, or performing statistical correlation math. All numerical and categorical figures are read directly from immutable records created by the Python engine.
2. **Authoritative Source of Truth**: The on-disk `EvaluationStore` (`<store>/<evaluation_id>/evaluation.json`), child observation stores (`<store>/<evaluation_id>/observations/observation_<horizon>.json`), backtest datasets, and calibration proposal files are the sole sources of truth.
3. **Pure Read-Only Enforcement**: The API exposes **only safe, idempotent read operations** (`GET`, `HEAD`, `OPTIONS`). Mutation methods (`POST`, `PUT`, `PATCH`, `DELETE`) directed at product state or storage are strictly rejected with `405 Method Not Allowed`.
4. **Preservation of Normative Tri-State & UNKNOWN Semantics**: Missing data is never coerced to zero, false, or fabricated values. The API faithfully preserves:
   * Value states: `VALUE`, `UNKNOWN`, `NOT_APPLICABLE`
   * Knockout states: `CLEAR`, `TRIGGERED`, `UNVERIFIED`
   * Confidence levels: `High`, `Medium`, `Low`
   * Verdicts: `APPLY`, `CONSIDER`, `AVOID`, `INSUFFICIENT_DATA`
5. **Deterministic Serialization**: JSON responses are deterministic, featuring stable key ordering, ISO-8601 UTC timestamps, 64-character SHA-256 hex hashes, and exact Decimal string values for financial returns.
6. **Zero Credential Exposure**: No model provider API keys (e.g., Anthropic, OpenAI), database passwords, or private exchange tokens are ever transmitted across the API boundary.

---

## 2. API Resource Model & Schema Definitions

The API defines explicit data schemas corresponding directly to the authoritative engine models:

| Resource Schema | Engine Source | Key Fields | Description |
| :--- | :--- | :--- | :--- |
| **`HealthStatus`** | Service Runtime | `status`, `timestamp`, `read_only` | Liveness and read-only operational state. |
| **`ApiMeta`** | Engine Metadata | `api_version`, `engine_version`, `spec_version`, `active_config_version`, `candidate_config_version`, `golden_result_hash` | Comprehensive system version and governance status. |
| **`IpoSummary`** | Canonical Input | `ipo_id`, `company_name`, `sector_profile`, `evaluation_count`, `latest_score`, `latest_verdict` | Directory-level issuer summary. |
| **`IpoDetail`** | Canonical Input | `ipo_id`, `company_name`, `sector_profile`, `icdr_route`, `evaluations[]` | Authoritative issuer identity and evaluation history. |
| **`EvaluationSummary`**| `EvaluationRecord` | `evaluation_id`, `ipo_id`, `evaluation_mode`, `final_score`, `verdict`, `confidence`, `result_hash` | Compact summary for tabular portfolio listings. |
| **`EvaluationDetail`** | `EvaluationRecord` | Full scorecard (`score`, `modules[]`, `penalties[]`, `knockouts`, `verdict`, `missing_unverified[]`, `provenance`) | Deep, institutional-grade scorecard detail. |
| **`EvidenceDetail`** | `EvidenceRegistry` | `evidence_id`, `field`, `document`, `page`, `locator`, `quote`, `extracted_value`, `unit` | Verbatim prospectus quote and page citation. |
| **`PostListingObservationItem`** | `PostListingObservation` | `observation_id`, `horizon`, `version`, `target_date`, `actual_trading_date`, `status`, `issue_price`, `return_set` | Child observation record with exchange prices and alpha. |
| **`PerformanceSummaryResponse`** | `PostListingObservation` | `listing_day`, `one_week`, `one_month`, `six_month` performance cards | Multi-horizon return and benchmark alpha tracker. |
| **`BacktestDatasetSummary`** | `BacktestDataset` | `dataset_id`, `dataset_hash`, `row_count`, `included_observation_count`, `status_counts` | Multi-IPO assembled dataset manifest metadata. |
| **`BacktestAnalyticsResponse`** | `BacktestAnalysis` | `analysis_hash`, `dataset_hash`, `sample_maturity`, `rank_ic`, `hit_rates`, `avoided_loss_rates`, `decile_buckets` | Empirical backtest analytics and statistical diagnostics. |
| **`CalibrationProposal`** | `CalibrationProposal` | `proposal_id`, `proposal_hash`, `baseline_config_hash`, `candidate_config_hash`, `maturity_gate`, `approval_status` | Governed configuration proposal artifact with shadow evaluation. |
| **`ConfigurationStatusResponse`** | Config Lifecycle | `active_configuration` (v1.5.0), `candidate_configuration` (v1.6.0), `frozen_core_status`, `golden_result_status` | Enforces active vs inactive governance boundary. |
| **`ApiError`** | Error Handling | `error`, `message`, `code`, `details` | Standardized, deterministic error envelope. |

---

## 3. Read-Only Endpoints Specification

### 3.1 System Endpoints
* **`GET /api/v1/health`**: Returns HTTP 200 with `{ "status": "healthy", "read_only": true, "timestamp": "..." }`.
* **`GET /api/v1/meta`**: Returns system metadata, active engine version (`1.5.0`), active config version (`1.5.0`), candidate config version (`1.6.0`), and golden result hash (`e84f8bc0...`).

### 3.2 IPO Issuer Discovery & Detail
* **`GET /api/v1/ipos`**:
  * *Query Parameters*: `page` (int, default 1), `page_size` (int, default 20), `search` (string, case-insensitive substring match against `company_name` or `ipo_id`), `sector_profile` (string).
  * *Response*: Paginated `IpoListResponse` with stable ascending sort by `ipo_id`.
* **`GET /api/v1/ipos/{ipo_id}`**:
  * *Response*: Complete `IpoDetail` containing issuer metadata and chronological list of evaluations. Returns HTTP 404 with `IPO_NOT_FOUND` if unknown.
* **`GET /api/v1/ipos/{ipo_id}/history`**:
  * *Response*: Chronological evaluation lifecycle stages (`PRELIMINARY`, `FINAL`) and preliminary-to-final delta records.

### 3.3 Evaluation Discovery & Detail
* **`GET /api/v1/evaluations`**:
  * *Query Parameters*: `page`, `page_size`, `ipo_id`, `mode` (`PRELIMINARY` / `FINAL`), `verdict`, `confidence`, `engine_version`, `config_version`.
  * *Response*: Paginated `EvaluationListResponse` sorted deterministically by `evaluation_timestamp` descending, then `evaluation_id` ascending.
* **`GET /api/v1/evaluations/{evaluation_id}`**:
  * *Response*: Full `EvaluationDetail` scorecard. Returns HTTP 404 with `EVALUATION_NOT_FOUND` if unknown.

### 3.4 Evidence Explorer
* **`GET /api/v1/evaluations/{evaluation_id}/evidence`**:
  * *Response*: Complete evidence catalog (`EvidenceResponse`) containing all citations, document locators, and verbatim quotes for the evaluation.
* **`GET /api/v1/evidence/{evidence_id}`**:
  * *Response*: Specific `EvidenceDetail` item looked up by compound identifier `{evaluation_id}:{field}` or globally across stored evaluations.

### 3.5 Post-Listing & Performance Tracking
* **`GET /api/v1/evaluations/{evaluation_id}/post-listing`**:
  * *Response*: Complete list of child observations (`observation_listing_day.json`, `observation_1w.json`, etc.) stored under `<store>/<evaluation_id>/observations/`.
* **`GET /api/v1/evaluations/{evaluation_id}/performance`**:
  * *Response*: Structured `PerformanceSummaryResponse` mapping `listing_day`, `one_week`, `one_month`, and `six_month` returns, benchmark index movements, and net excess return (alpha). If observations are not yet recorded, returns status `INCOMPLETE` with explicit `null` returns.

### 3.6 Backtesting & Statistical Analytics
* **`GET /api/v1/backtest/datasets`**:
  * *Response*: Summary listing of assembled multi-IPO backtest datasets available in the repository.
* **`GET /api/v1/backtest/analytics`**:
  * *Response*: Authoritative `BacktestAnalyticsResponse` detailing sample maturity, Rank IC, hit rates, avoided-loss rates, decile buckets, and 8-point data leakage audit status. Returns HTTP 404 if no backtest analysis artifact has been generated yet.

### 3.7 Calibration & Configuration Governance
* **`GET /api/v1/calibration/proposals`**:
  * *Response*: List of governed calibration proposals with maturity gate and approval status.
* **`GET /api/v1/calibration/proposals/{proposal_id}`**:
  * *Response*: Full `CalibrationProposal` artifact including proposed module weight adjustments (Module A: 25$\to$30, Module B: 20$\to$15) and shadow evaluation rescoring metrics.
* **`GET /api/v1/configuration/current`**:
  * *Response*: Authoritative configuration lifecycle status proving that `v1.5.0` is `ACTIVE` (`is_active: true`) and candidate `v1.6.0` is `IMPLEMENTED_INACTIVE` (`is_active: false`). Confirms `frozen_core_status: VERIFIED` and `golden_result_status: VERIFIED`.

---

## 4. EvaluationStore & Read Boundary Architecture

The Presentation API encapsulates all filesystem access behind a read-only repository service (`PresentationService` in `engine/ipo_screening/presentation/service.py`):

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation API Router                   │
│                     (FastAPI Endpoints)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Clean Domain DTOs
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     PresentationService                     │
│  - Encapsulates filesystem directory layout                 │
│  - Traverses <store>/<eval_id>/                             │
│  - Traverses <store>/<eval_id>/observations/                │
│  - Loads config/ and build/ artifacts                       │
│  - Pure In-Memory Caching & Projection                      │
│  - Strictly Zero Writes (no open(..., "w"))                 │
└──────────────────────────────┬──────────────────────────────┘
                               │ Read-Only File Handles
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Immutable Filesystem Evaluation Store             │
│   <store>/<eval_id>/evaluation.json, result.json, etc.      │
└─────────────────────────────────────────────────────────────┘
```

* **Filesystem Isolation**: The web API does not expose raw directory paths. All paths are resolved relative to configured store roots.
* **Graceful Missing Data Handling**: If an evaluation exists without post-listing observations, the service returns empty lists or `INCOMPLETE` statuses rather than failing or fabricating placeholder data.

---

## 5. Security & Credential Boundary

* **Zero Client Credentials**: The API does not accept or process LLM API keys (e.g. Anthropic, OpenAI) or exchange credentials.
* **Safe Extraction Boundary**: Future PDF extraction workflows must be proxied server-side through a dedicated backend extraction gateway where API keys are loaded strictly from environment variables or vault secrets.
* **CORS & Framing Protections**: The API includes standard security middleware with configurable CORS origins and frame-ancestor restrictions.

---

## 6. Contract Gaps Inventory

Where the current engine records do not natively provide presentation fields desired for future UI views, they are formally recorded as Contract Gaps rather than fabricated:

| Gap ID | Field / Feature | Target Surface | Authoritative Source Expected | Current Status | UI-2 Impact | Recommended Future Resolution |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| **UI1-GAP-01** | `industry_classification` | IPO Directory / Filters | BSE / NSE Industry taxonomy | Absent from `CanonicalInput` (has `sector_profile` only) | **NON-BLOCKING** | Add optional `industry_name` to `schema/ipo-input.v1.5.schema.json`. |
| **UI1-GAP-02** | `quote_bounding_box` | Evidence Explorer | PDF extraction coordinates | Absent; `Evidence` has `page` and `quote` text | **NON-BLOCKING** | Future PDF extraction engine can record `bbox: [x, y, w, h]`. |
| **UI1-GAP-03** | `realtime_streaming` | Post-Listing Live Tracker | Live Exchange WebSocket | Batch Bhavcopy files used instead | **FUTURE** | Implement live market quote provider adapter in Phase 8. |
| **UI1-GAP-04** | `analyst_annotations` | Scorecard Notes & Watchlist | User state database | Absent; system is stateless filesystem | **FUTURE (UI-7)** | Add PostgreSQL / SQLite user state persistence in Phase UI-7. |

---

## 7. Local Non-Production Execution Runbook

### Prerequisites:
* Python 3.11+
* Installed packages: `fastapi`, `uvicorn`, `pydantic`, `httpx`

### Starting the Presentation API Server:
To run the read-only presentation API locally:
```bash
# Set Python path to include engine/
export PYTHONPATH=engine

# Start the read-only server on port 8000
uvicorn ipo_screening.presentation.api:app --host 0.0.0.0 --port 8000 --reload
```

### Environment Configuration:
The service respects the following environment variables:
* `IPO_STORE_ROOT`: Path to evaluation store root (defaults to `build/evaluations` or `fixtures/store`).
* `IPO_CONFIG_DIR`: Path to configuration directory (defaults to `config`).
* `IPO_DATASET_PATH`: Path to backtest dataset JSON (defaults to `build/dataset/dataset.json`).
* `IPO_ANALYTICS_PATH`: Path to backtest analytics JSON (defaults to `build/analytics/analytics.json`).
* `IPO_PROPOSAL_PATH`: Path to calibration proposal JSON (defaults to `config/calibration-proposal.v1.6.0.json`).

## 8. Artifact Verification Hashes

* **OpenAPI 3.1 YAML Contract (`docs/openapi/presentation-api-v1.yaml`)**:
  `8abfcef70f30df6c42ab4a22a54a88bca507689c0c30a69dd07caf0cb2ffe1f7`
* **Presentation Contract Document (`docs/UI_PRESENTATION_API_CONTRACT.md`)**:
  `00765c5a6eb0e08791db8b4d0c3552f1af6f3829e27eaa79a2edb65ecc905f5f` (prior to hash insertion)
* **Presentation Service Models (`engine/ipo_screening/presentation/models.py`)**:
  `00487baba9769a79649328fc93e2ff590dabaaeb25c551ae95e7da7b9e8f379a`
* **Presentation Service Implementation (`engine/ipo_screening/presentation/service.py`)**:
  `9ce3f5191a1a7caedfea7a67c206c159ec505f2f27da88833af3463b9d2758e0`
* **Presentation API Router (`engine/ipo_screening/presentation/api.py`)**:
  `d08d0428070b53dc8b99e2971021c2012515508c7ab4e2d23d9e7c0591e928ef`
* **Presentation API Acceptance Suite (`tests/test_presentation_api.py`)**:
  `8332afad33af40b48a68aee6af3780e90cfd7848de59f4b0dcbe1465da94c0d6`
* **Test Verification Total**: 21 passed / 0 failed in `tests/test_presentation_api.py` (244 tests passing across full targeted regression suite).
* **Golden Result Hash Invariant**: `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` (100% verified).
* **Frozen Core Check**: 6 files bit-for-bit unchanged (VERIFIED).
