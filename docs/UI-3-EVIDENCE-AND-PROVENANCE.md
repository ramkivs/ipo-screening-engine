# UI-3: Evidence & Provenance Explorer

**Authoritative Specification & Implementation Report**  
**Engine Baseline:** `v1.5.0` (Active Policy) | `v1.6.0-draft` (Inactive Calibration Proposal)  
**API Protocol:** UI-1 Presentation API (`docs/openapi/presentation-api-v1.yaml`)  
**Presentation Surfaces:** UI-2 Core Dashboard & Scorecard + UI-3 Evidence & Provenance Explorer  
**Status:** DELIVERED & AUDITED  
**Date:** 2026-10-06  

---

## 1. Executive Summary

UI-3 delivers the **Evidence & Provenance Explorer**, an institutional-grade presentation surface connecting screening conclusions to their underlying filings, prospectuses, and cryptographic fingerprints. Built on top of the frozen UI-1 Presentation Read-Model API, UI-3 enables analysts, auditors, and investment committees to trace the complete provenance chain:

$$\text{Evaluation} \longrightarrow \text{Score / Criterion} \longrightarrow \text{Evidence Citation} \longrightarrow \text{Source Document} \longrightarrow \text{Page / Locator} \longrightarrow \text{Extracted Value / Verbatim Quote} \longrightarrow \text{Scoring Provenance}$$

Strictly zero engine scoring formulas or extraction heuristics are duplicated in the presentation layer. The authoritative engine remains the sole computation authority.

### Delivered Capabilities:
1. **Evidence & Provenance Explorer View (`#evidence/{id}`):** Dedicated route featuring full evaluation metadata, cryptographic provenance panel, contract guidance callout, search/filter toolbar, and responsive evidence citation cards.
2. **Cryptographic Provenance Audit Panel:** Exposes immutable SHA-256 fingerprints supplied by UI-1 (`result_hash`, `source_manifest_hash`, `input_snapshot_hash`, `config_hash`, `market_snapshot_hash`, `peer_snapshot_hash`) with copy-to-clipboard controls.
3. **Evidence Detail Inspector Modal / Drawer:** In-depth examination pane providing full verbatim quote citations, canonical field names, source document locators, extracted values, units, and raw JSON provenance payloads.
4. **Verbatim Quotation Integrity:** Quotes extracted from offer documents (RHP/DRHP) are preserved verbatim without paraphrasing, normalization, or silent truncation. Expansion controls are provided for lengthy citations.
5. **Fail-Closed Semantics & Source Distinction:** Unambiguous visual distinction between `SOURCE EVIDENCE` (verbatim filing extracts), `DERIVED VALUE` (engine-computed metrics), and `UNKNOWN / UNVERIFIED` (missing data points). Null extracted values explicitly display `UNKNOWN`, never defaulting to `0` or `0.00`.
6. **Scorecard Integration & Bidirectional Navigation:** Seamless navigation between UI-2 Scorecard and UI-3 Evidence Explorer via header action buttons, per-criterion evidence citation links, and return buttons.
7. **Automated Verification:** 20 Node.js unit tests (`frontend/test/`) and 8 Python integration tests (`tests/test_ui3_evidence.py`), bringing total presentation and regression test count to 55 passing tests.

---

## 2. Provenance Chain & Architectural Boundaries

```
+----------------------------------------------------------------------------------------------------+
|                                         Browser Application                                        |
|                                                                                                    |
|  +----------------------------------------------------------------------------------------------+  |
|  |                             UI-2 Evaluation Detail Scorecard                                 |  |
|  |  - Module Criteria Breakdown  --->  [Inspect Citation (EV)]                                  |  |
|  |  - Missing / Unverified Items --->  [Search in Evidence]                                     |  |
|  |  - Header Action              --->  [Inspect Evidence & Provenance ->]                       |  |
|  +----------------------------------------------------------------------------------------------+  |
|                                                |                                                   |
|                                                v Hash Navigation                                   |
|  +----------------------------------------------------------------------------------------------+  |
|  |                         UI-3 Evidence & Provenance Explorer (#evidence/{id})                 |  |
|  |  +----------------------------------------------------------------------------------------+  |  |
|  |  | Cryptographic Audit Panel: [result_hash] [manifest_hash] [input_hash] [config_hash]      |  |  |
|  |  +----------------------------------------------------------------------------------------+  |  |
|  |  | Contract Guidance: SOURCE EVIDENCE (Quoted) vs DERIVED VALUES (Computed by Engine)     |  |  |
|  |  +----------------------------------------------------------------------------------------+  |  |
|  |  | Filter Toolbar: Search [ ........................ ] [ALL] [FIN] [GOV] [STR] [VAL]       |  |  |
|  |  +----------------------------------------------------------------------------------------+  |  |
|  |  | Evidence Cards Grid:                                                                   |  |  |
|  |  |  - Field: cfo_fy26  |  ID: EV-cfo-fy26  |  [SOURCE EVIDENCE]                            |  |  |
|  |  |  - Value: 27.15 INR_CRORES              |  Document: VISHAL-NIRMITI-LIMITED-RHP.pdf     |  |  |
|  |  |  - Quote: "Net cash generated from..."  |  Page: 74  |  Locator: Cash Flows             |  |  |
|  |  |  - [Inspect Full Detail ->]                                                             |  |  |
|  |  +----------------------------------------------------------------------------------------+  |  |
|  |  | Evidence Detail Inspector (Slide-over drawer with raw JSON & un-truncated quote)       |  |  |
|  |  +----------------------------------------------------------------------------------------+  |  |
|  +----------------------------------------------------------------------------------------------+  |
+------------------------------------------------|---------------------------------------------------+
                                                 | HTTP GET (Read-Only)
                                                 v
+----------------------------------------------------------------------------------------------------+
|                             FastAPI Presentation Service (/api/v1)                                 |
|  - GET /api/v1/evaluations/{id}            (Evaluation detail & cryptographic provenance hashes)   |
|  - GET /api/v1/evaluations/{id}/evidence   (Full evidence citation registry from evidence artifact)|
|  - GET /api/v1/evidence/{evidence_id}      (Individual evidence citation by compound ID)           |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Component Details & Functional Specification

### 3.1 Provenance & Cryptographic Audit Panel
The audit panel displays immutable provenance hashes loaded directly from the evaluation record on disk:
- **Result Hash:** Root cryptographic digest of the complete scoring outcome (`result.json`).
- **Source Manifest Hash:** Hash of the authoritative manifest registering all input documents and filings.
- **Input Snapshot Hash:** Canonical SHA-256 digest of pre-listing financial inputs (`input.json`).
- **Configuration Hash:** Hash of the active scoring configuration (`ipo-config.v1.5.0.json`).
- **Market / Peer Snapshot Hashes:** Cryptographic hashes for supplementary pricing and peer multiples when present.
- **Copy Presentation Control:** Interactive button writing hash to system clipboard with visual confirmation ("Copied!"), facilitating external audit verification.

### 3.2 Evidence Cards & Semantic Classification
Each evidence card categorizes citations into three mutually exclusive provenance states:
1. `SOURCE EVIDENCE` (Blue badge): Verbatim text extracted directly from official filings (RHP/DRHP).
2. `DERIVED VALUE` (Purple badge): Structured or computed metrics generated by engine logic.
3. `UNKNOWN / UNVERIFIED` (Amber badge): Data points unextracted, missing from filings, or unverified.

Each card displays:
- Canonical field name and unique evidence identifier.
- Extracted value and unit tag (or explicit `UNKNOWN` badge; never converted to `0.00`).
- Verbatim quoted text enclosed in blockquote styling with quote expansion toggle for text exceeding 180 characters.
- Source document name, page number, and locator.
- "Inspect Full Detail" action button.

### 3.3 Security & Filesystem Path Protection
In accordance with Section 10 and 13 of the specification:
- **No Server Filesystem Paths:** Source documents are presented solely by document name (e.g. `VISHAL-NIRMITI-LIMITED-RHP.pdf`). Absolute filesystem paths (e.g. `/home/user/...` or `/var/...`) and `file://` URLs are strictly prohibited and scrubbed.
- **No Document Streaming Endpoint:** Because PDF viewing is deferred (UI1-GAP-02), UI-3 provides document and page metadata only without exposing arbitrary server files.
- **Zero Credential Exposure:** Client assets contain zero external API keys, tokens, or model credentials.

---

## 4. Scorecard Integration & Bidirectional Navigation

UI-3 connects seamlessly with UI-2 without modifying the frozen core engine:
1. **Scorecard Header Action:** Scorecard banner includes an `Inspect Evidence & Provenance ->` primary button routing to `#evidence/{evaluation_id}`.
2. **Criteria Table Citations:** Each criterion row in Modules A–F includes an `Inspect Citation [EV] ->` link routing to `#evidence/{evaluation_id}?field={criterion_id}`, pre-filtering the evidence explorer to matching citations.
3. **Missing Data Explorer Link:** Missing and unverified items in the scorecard provide `Search in Evidence ->` links for immediate verification.
4. **Return Navigation:** Evidence Explorer header provides a persistent `<- Return to Scorecard` action button routing back to `#evaluations/{evaluation_id}`.

---

## 5. Contract Limitations & Gap Analysis

In accordance with Section 3, 7, and 18, all limitations are documented as formal gaps without altering UI-1:

| Gap ID | Classification | Description & Current State in UI-3 |
| :--- | :--- | :--- |
| **UI1-GAP-01** | Industry Taxonomy | Sector profiles are displayed as standard tags (`STANDARD`). Dynamic SEBI industry taxonomy remains deferred to future data service. |
| **UI1-GAP-02** | Quote Bounding Boxes | Visual PDF coordinate bounding boxes are deferred. UI-3 presents verbatim text and page numbers as metadata. |
| **UI1-GAP-03** | Real-Time WebSockets | Real-time streaming is deferred. UI-3 operates purely over deterministic REST read endpoints. |
| **UI1-GAP-04** | Annotation Persistence | Analyst annotations are deferred. UI-3 is strictly read-only with zero database persistence. |
| **UI3-GAP-01** | Criterion-to-Evidence Linkage | The UI-1 `EvidenceDetail` schema exposes `field` but not a direct foreign key to `criterion_id`. UI-3 performs heuristic linking via canonical field matching. Formal criterion-to-evidence relation should be added in UI-4 presentation schema. |
| **UI3-GAP-02** | Server-Side Evidence Pagination | For exceptionally large filings (>100 citations), client-side filtering is performed over retrieved records. Server-side search and pagination should be considered for large multi-volume offerings. |

---

## 6. Verification & Acceptance Results

### 6.1 Node.js Frontend Test Suite (`frontend/test/`)
```
> ipo-screening-engine-ui@1.0.0 test
> node --test test/*.test.js

TAP version 13
ok 1 - ApiClient - Initialisation and read-only protocol
ok 2 - ApiClient - System endpoints (getHealth, getMeta, getConfigurationStatus)
ok 3 - ApiClient - listIpos builds query parameters accurately
ok 4 - ApiClient - listEvaluations builds query parameters accurately
ok 5 - ApiClient - Detail endpoints encode URL parameters correctly
ok 6 - ApiClient - handles 404 and API error schemas
ok 7 - ApiClient - handles network disconnection error cleanly
ok 8 - ApiClient - rejects empty or missing IDs in getIpo and getEvaluation
ok 9 - App - Formatting helpers produce valid accessible HTML markup
ok 10 - App - Zero Score Calculation Invariant: source files contain no arithmetic weighting or scoring formulas
ok 11 - App - Governance Invariant: no policy activation or modification controls in frontend
ok 12 - App - Fail-Closed Invariant: missing/null values never default to zero
ok 13 - UI-3 ApiClient - getEvidence and getEvaluationEvidence protocols
ok 14 - UI-3 ApiClient - rejects missing evidence identifiers
ok 15 - UI-3 App - Provenance & Cryptographic Audit Panel formatting
ok 16 - UI-3 App - Contract Guidance & Distinction between Source Evidence vs Derived Values
ok 17 - UI-3 App - Verbatim Quote Preservation and Fail-Closed Unknown Semantics
ok 18 - UI-3 App - Source document, page, and locator presentation security
ok 19 - UI-3 App - Scorecard-to-evidence navigation integration
ok 20 - UI-3 App - Evidence Detail Inspector dialog structure
1..20
# tests 20
# pass 20
# fail 0
```

### 6.2 Python Static Serving & Integrity Suite (`tests/test_ui3_evidence.py`)
```
============================= test session starts ==============================
collected 8 items

tests/test_ui3_evidence.py::test_ui3_static_assets_contain_evidence_explorer PASSED
tests/test_ui3_evidence.py::test_ui3_css_contains_distinction_badges_and_inspector_styles PASSED
tests/test_ui3_evidence.py::test_ui3_app_contains_scorecard_navigation_and_provenance PASSED
tests/test_ui3_evidence.py::test_ui3_zero_score_computation_invariant PASSED
tests/test_ui3_evidence.py::test_ui3_no_server_filesystem_paths_exposed PASSED
tests/test_ui3_evidence.py::test_ui3_no_credential_exposure PASSED
tests/test_ui3_evidence.py::test_ui3_evidence_endpoints_served_by_api PASSED
tests/test_ui3_evidence.py::test_ui3_no_policy_activation_controls PASSED

============================== 8 passed in 0.56s ===============================
```

### 6.3 Combined Presentation & Golden Acceptance Suite
```
============================= test session starts ==============================
collected 55 items

tests/test_presentation_api.py .....................                     [ 38%]
tests/test_ui2_frontend.py .......                                       [ 50%]
tests/test_ui3_evidence.py ........                                      [ 65%]
tests/test_vishal_golden.py ...................                          [100%]

======================== 55 passed, 1 warning in 2.56s =========================
```

### 6.4 Golden Result Hash & Governance Integrity
- **Golden Result Hash:** `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` (Bit-for-bit identical).
- **Frozen Core Engine:** 100% UNTOUCHED (`scoring.py`, `derived.py`, `knockouts.py`, `snapshots.py`, `evaluation.py`, `price_band_notice.py`).
- **Policy Lifecycle:** `v1.5.0` ACTIVE; `v1.6.0-draft` INACTIVE.
- **Git Invariant:** `origin/main` untouched (`01ba66c12ca1195fd7acbd287c3e39a019808094`), PR #3 untouched.

---

## 7. Artifact Cryptographic SHA-256 Checksums

| File Path | SHA-256 Digest |
| :--- | :--- |
| `frontend/index.html` | `68985133e7ebbc239598c72f5b8e7ad2f9b81c5fe7f1f142224adf3e90fff3a3` |
| `frontend/styles.css` | `b95d0af0195db34eea4bf85f16d06aa64774fc42c8020524cb2bbb1f5eb9408e` |
| `frontend/api.js` | `214f4547c93efacf83308680ffd52d3ca2f4f92e32777b78c4a3ec119cb18b3f` |
| `frontend/app.js` | `0de9e02e8d53419d47a5a08d96f205643cf6089f6087d68bd2642a10836d750c` |
| `frontend/test/evidence.test.js` | `71d837bc7f53b900e92cf1141a89b948a138d068ee90aa4ec6166c648d71cc4b` |
| `tests/test_ui3_evidence.py` | `ce37419ace52d2f7e8d8f0f860d7647b45eebb98a95154fc56a5fa237dc7264b` |
| `docs/UI-3-EVIDENCE-AND-PROVENANCE.md` | Authoritative |
