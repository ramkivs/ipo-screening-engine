# Fail-Closed Fixture Fallback Policy Correction Report

## 1. Executive Summary & Policy Boundary

This document formalizes the architectural separation between **Real Statutory Prospectus Ingestion** and **Synthetic Test Harness Workflows**, resolving the cross-IPO data contamination vulnerability identified during R.K. Fashion Accessories ingestion analysis.

### The Problem
In earlier iterations, `PresentationService.ingest_document` invoked generic document extraction with `allow_fixture_fallbacks=True`. When a real statutory prospectus (such as `U18109WB2010PLC144256-R.K Fashion accessories.pdf`) was ingested, any field not extracted from the PDF body silently inherited fallback values derived from an unrelated issuer fixture (`fixtures/vishal_nirmiti/input.json`), specifically:
- `business.moat_rating`: `"strong_niche"` (+3.0 pts)
- `business.visibility_rating`: `"strong"` (+2.0 pts)
- Unextracted issue parameters (e.g. `price_band_low: 208`, `price_band_high: 220`, `lot_size: 68`, etc.)

This contamination artificially inflated R.K. Fashion Accessories' score from 55.0 to 60.0, violating core engine fail-closed invariants.

### The Authorized Policy Boundary
1. **Real Document Ingestion (`PresentationService.ingest_document`)**:
   - Strictly enforces `allow_fixture_fallbacks=False`.
   - Any missing qualitative assessments remain `UNKNOWN` (0.0 pts scored, points counted as unavailable in completeness denominator).
   - Incomplete or malformed statutory filings fail closed with HTTP 422 `PROCESSING_FAILED` and do not receive synthetic values.
2. **Generic Extraction Boundary (`DocumentExtractor.extract_from_pdf`)**:
   - Defaults to `allow_fixture_fallbacks: bool = False`.
   - Prevents silent fallback leakage across all standard Python and service call paths.
3. **Synthetic Test / Fixture Harnesses (`tests/test_extraction_phase5b.py`)**:
   - Retains explicit caller override (`allow_fixture_fallbacks=True`) strictly for minimal synthetic stub filings designed to test financial table parser mechanics without full issue sections.
4. **Public API & UI Boundary (`POST /api/v1/ingest/document`)**:
   - Rejects any client attempt to submit `allow_fixture_fallbacks`, `fallback`, `base_path`, or `reference_base_path` with HTTP 400 `SECURITY_VIOLATION_UNAUTHORIZED_PARAMETER`.
   - Never exposes UI toggles or parameters permitting callers to activate fallbacks.

---

## 2. Implementation Audit & Changes

### 2.1 `engine/ipo_screening/presentation/service.py`
In `PresentationService.ingest_document`:
```python
# Before
canonical_dict, extraction_report = extractor.extract_from_pdf(
    pdf_path=temp_pdf_path,
    allow_fixture_fallbacks=True,
)

# After (Enforced Fail-Closed)
canonical_dict, extraction_report = extractor.extract_from_pdf(
    pdf_path=temp_pdf_path,
    allow_fixture_fallbacks=False,
)
```

### 2.2 `engine/ipo_screening/extraction/extractor.py`
In `DocumentExtractor.extract_from_pdf`:
```python
# Before
def extract_from_pdf(
    self,
    pdf_path: str | Path,
    reference_base_path: Optional[str | Path] = None,
    allow_fixture_fallbacks: bool = True,
) -> Tuple[Dict[str, Any], ExtractionReport]:

# After (Fail-Closed Default)
def extract_from_pdf(
    self,
    pdf_path: str | Path,
    reference_base_path: Optional[str | Path] = None,
    allow_fixture_fallbacks: bool = False,
) -> Tuple[Dict[str, Any], ExtractionReport]:
```

### 2.3 `engine/ipo_screening/presentation/api.py`
Added forbidden parameter guard on public ingestion endpoint:
```python
form_data = await request.form()
forbidden_params = {
    "reference_base_path", "base_path", "path", "file_path",
    "allow_fixture_fallbacks", "fallback", "allow_fallbacks"
}
present_forbidden = forbidden_params.intersection(form_data.keys())
if present_forbidden:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "Bad Request",
            "message": f"Unauthorized security parameter(s) detected: {sorted(list(present_forbidden))}. Server filesystem paths and fixture fallback controls are strictly prohibited on the public ingestion boundary.",
            "code": "SECURITY_VIOLATION_UNAUTHORIZED_PARAMETER",
        },
    )
```

### 2.4 Synthetic Test Harnesses (`tests/test_extraction_phase5b.py`)
Explicitly updated minimal synthetic stub test cases to pass `allow_fixture_fallbacks=True`:
- `test_fixture_class_a_financial_lender`
- `test_fixture_class_b_cyclical_manufacturing_5fy`
- `test_fixture_class_c_epc_infrastructure`
- `test_fixture_class_d_loss_making_tech`
- `test_fixture_class_e_modern_complex_rhp`
- `test_evidence_provenance_and_auditability`

### 2.5 Ingestion Test Suite (`tests/test_ui7_ingestion.py`)
- Integrated synthetic complete statutory fixtures (`complete_sample_rhp.pdf` and `complete_sample_rhp_2.pdf`) ensuring zero-fallback multi-IPO coexistence and idempotency validation execute in under 2 seconds.
- Added regression test `test_public_ingestion_rejects_fallback_parameters` (HTTP 400).
- Added regression test `test_ingest_incomplete_stub_fails_closed_without_fallbacks` (HTTP 422).
- Added regression test `test_ingest_rk_fashion_accessories_real_statutory_filing` proving full 236-page statutory PDF ingestion via presentation service matches exact 55.0 / 100 benchmark.

---

## 3. Verification & Benchmark Assertions

### 3.1 Vishal Nirmiti Baseline Golden Preservation
- Golden Hash: `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1`
- Score: 35.0 / 100
- Base Score: 38.0
- Penalties: -3.0
- Verdict: `INSUFFICIENT_DATA`
- Result: **Bit-for-bit identical (19/19 tests passing)**.

### 3.2 R.K. Fashion Accessories Statutory Verification
- Filing: `handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`
- Ingestion Path: `PresentationService.ingest_document(..., allow_fixture_fallbacks=False)`
- Final Score: **55.0 / 100**
- Base Score: **58.0**
- Penalties Total: **-3.0** (`margin_spike`: +51.16% revenue growth, EBITDA margin 16.7% to 24.2%)
- Lower Bound: **42.0**
- Upper Bound: **80.0**
- Data Completeness: **75.0%** (75.0 available pts, 25.0 unknown pts)
- Confidence Level: **Low**
- Verdict: **`INSUFFICIENT_DATA`**
- Cross-IPO Contamination: **Zero** (no 208, 220, 68, 9.46, "strong_niche", or "strong" present).

### 3.3 Scoring Shift Audit (60.0 -> 55.0)

| Criterion | Ingested under Fallbacks (60.0) | Ingested Fail-Closed (55.0) | Delta | Reason |
| :--- | :--- | :--- | :--- | :--- |
| **Module E `moat`** | 3.0 pts (`strong_niche` from Vishal) | 0.0 pts (`UNKNOWN`, value: `None`) | -3.0 pts | Missing qualitative moat rating evaluates to UNKNOWN |
| **Module E `visibility`** | 2.0 pts (`strong` from Vishal) | 0.0 pts (`UNKNOWN`, value: `None`) | -2.0 pts | Missing qualitative visibility rating evaluates to UNKNOWN |
| **Total Base Score** | 63.0 pts | 58.0 pts | -5.0 pts | Exact difference |
| **Total Penalties** | -3.0 pts (`margin_spike`) | -3.0 pts (`margin_spike`) | 0.0 pts | Preserved |
| **Final Score** | 60.0 pts | 55.0 pts | -5.0 pts | Exact difference |
| **Available Points** | 82.0 pts | 75.0 pts | -7.0 pts | 5 pts moat + 2 pts visibility move to unknown |
| **Unknown Points** | 18.0 pts | 25.0 pts | +7.0 pts | Correct fail-closed accounting |
| **Completeness** | 82.0% | 75.0% | -7.0% | Corrected |
| **Confidence Level** | Medium (>=80%) | Low (<80%) | Shifted | Correctly reflects missing qualitative inputs |

---

## 4. Frozen Core Invariant Verification

As mandated by engine design and system governance:
- `engine/ipo_screening/derived.py`: Byte-for-byte untouched.
- `engine/ipo_screening/scoring.py`: Byte-for-byte untouched.
- `engine/ipo_screening/knockouts.py`: Byte-for-byte untouched.
- `engine/ipo_screening/snapshots.py`: Byte-for-byte untouched.
- `engine/ipo_screening/evaluation.py`: Byte-for-byte untouched.
- `engine/ipo_screening/extraction/price_band_notice.py`: Byte-for-byte untouched.
- Active Configuration: `config/ipo-config.v1.5.0.json` (fingerprint: `4a5d92e8...`).
- Candidate Configuration: v1.6.0-draft remains strictly inactive.
