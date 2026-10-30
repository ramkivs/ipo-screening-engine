"""FastAPI personal-use presentation API.

GET routes expose read-model views. Only the explicit filing-ingestion and
lifecycle-action POST routes may mutate the local filesystem; arbitrary write
methods and scoring/configuration mutation routes are rejected. Every request
is restricted to a localhost/loopback Host, and workflow POSTs require an
explicit same-origin Origin header.
"""

from __future__ import annotations

import ipaddress
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse

from .models import (
    ApiError,
    ApiMeta,
    BacktestAnalyticsResponse,
    BacktestDatasetListResponse,
    CalibrationProposal,
    CalibrationProposalListResponse,
    ConfigurationStatusResponse,
    EvaluationDetail,
    EvaluationListResponse,
    EvidenceDetail,
    EvidenceResponse,
    HealthStatus,
    IngestionResponse,
    IpoDetail,
    IpoHistoryResponse,
    IpoListResponse,
    LifecycleActionRequest,
    LifecycleActionResponse,
    PerformanceSummaryResponse,
    PostListingObservationsResponse,
)
from ..lifecycle import (
    CyclicLineageError,
    EvaluationNotFoundError,
    InvalidStateTransitionError,
    ProtectedRecordError,
)
from .service import (
    IngestionAwaitingIssueTermsError,
    IngestionError,
    IngestionEvaluationError,
    IngestionIssueTermConflictError,
    IngestionExtractionError,
    IngestionPayloadTooLargeError,
    IngestionValidationError,
    PresentationConfig,
    PresentationService,
)


def _is_loopback_authority(authority: str) -> bool:
    """Return whether an HTTP authority names only an explicit loopback host.

    The API is unauthenticated and intended to bind to loopback. Checking the
    Host authority prevents DNS-rebinding origins from making a remote site
    appear same-origin to a browser after its DNS answer changes to loopback.
    """
    if not authority:
        return False
    try:
        parsed = urlsplit(f"//{authority}")
        hostname = parsed.hostname
        # Accessing ``port`` validates malformed and out-of-range port text.
        _ = parsed.port
    except ValueError:
        return False

    if (
        not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        return False

    normalized = hostname.lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def create_router(service: PresentationService) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    # -------------------------------------------------------------------------
    # 6.1 Health & Metadata
    # -------------------------------------------------------------------------

    @router.get("/health", response_model=HealthStatus, tags=["System"])
    def get_health() -> HealthStatus:
        return HealthStatus(
            status="healthy",
            timestamp=datetime.now(timezone.utc).isoformat(),
            read_only=False,
        )

    @router.get("/meta", response_model=ApiMeta, tags=["System"])
    def get_meta() -> ApiMeta:
        return service.get_meta()

    # -------------------------------------------------------------------------
    # 6.2 & 6.3 IPO Discovery & Detail
    # -------------------------------------------------------------------------

    @router.get("/ipos", response_model=IpoListResponse, tags=["IPOs"])
    def list_ipos(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: Optional[str] = Query(None),
        sector_profile: Optional[str] = Query(None),
    ) -> IpoListResponse:
        return service.list_ipos(
            page=page,
            page_size=page_size,
            search=search,
            sector_profile=sector_profile,
        )

    @router.get("/ipos/{ipo_id}", response_model=IpoDetail, tags=["IPOs"])
    def get_ipo(ipo_id: str) -> IpoDetail:
        res = service.get_ipo_detail(ipo_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"IPO issuer '{ipo_id}' not found in store", "code": "IPO_NOT_FOUND"},
            )
        return res

    @router.get("/ipos/{ipo_id}/history", response_model=IpoHistoryResponse, tags=["IPOs"])
    def get_ipo_history(
        ipo_id: str,
        include_archived: bool = Query(False, description="Include archived historical evaluations"),
    ) -> IpoHistoryResponse:
        res = service.get_ipo_history(ipo_id, include_archived=include_archived)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"IPO issuer '{ipo_id}' not found in store", "code": "IPO_NOT_FOUND"},
            )
        return res

    # -------------------------------------------------------------------------
    # 6.4 & 6.5 Evaluation Discovery & Detail
    # -------------------------------------------------------------------------

    @router.get("/evaluations", response_model=EvaluationListResponse, tags=["Evaluations"])
    def list_evaluations(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        ipo_id: Optional[str] = Query(None),
        mode: Optional[str] = Query(None),
        verdict: Optional[str] = Query(None),
        confidence: Optional[str] = Query(None),
        engine_version: Optional[str] = Query(None),
        config_version: Optional[str] = Query(None),
    ) -> EvaluationListResponse:
        return service.list_evaluations(
            page=page,
            page_size=page_size,
            ipo_id=ipo_id,
            mode=mode,
            verdict=verdict,
            confidence=confidence,
            engine_version=engine_version,
            config_version=config_version,
        )

    @router.get("/evaluations/{evaluation_id}", response_model=EvaluationDetail, tags=["Evaluations"])
    def get_evaluation(evaluation_id: str) -> EvaluationDetail:
        res = service.get_evaluation_detail(evaluation_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"Evaluation '{evaluation_id}' not found in store", "code": "EVALUATION_NOT_FOUND"},
            )
        return res

    @router.get("/evaluations/{evaluation_id}/input", tags=["Evaluations"])
    def get_evaluation_input(evaluation_id: str) -> Dict[str, Any]:
        res = service.get_evaluation_input(evaluation_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"Evaluation '{evaluation_id}' not found in store", "code": "EVALUATION_NOT_FOUND"},
            )
        return res.model_dump() if hasattr(res, "model_dump") else res

    @router.get("/comparison/{evaluation_id}", tags=["Evaluations"])
    def get_evaluation_comparison(evaluation_id: str) -> Dict[str, Any]:
        res = service.get_evaluation_comparison(evaluation_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"Evaluation '{evaluation_id}' not found in store", "code": "EVALUATION_NOT_FOUND"},
            )
        return res

    # -------------------------------------------------------------------------
    # 6.6 Evidence
    # -------------------------------------------------------------------------

    @router.get("/evaluations/{evaluation_id}/evidence", response_model=EvidenceResponse, tags=["Evidence"])
    def get_evaluation_evidence(evaluation_id: str) -> EvidenceResponse:
        res = service.get_evaluation_evidence(evaluation_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"Evaluation '{evaluation_id}' not found in store", "code": "EVALUATION_NOT_FOUND"},
            )
        return res

    @router.get("/evidence/{evidence_id}", response_model=EvidenceDetail, tags=["Evidence"])
    def get_evidence_item(evidence_id: str) -> EvidenceDetail:
        res = service.get_evidence_item(evidence_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"Evidence item '{evidence_id}' not found in store", "code": "EVIDENCE_NOT_FOUND"},
            )
        return res

    # -------------------------------------------------------------------------
    # 6.8 & 6.9 Post-Listing & Performance
    # -------------------------------------------------------------------------

    @router.get("/evaluations/{evaluation_id}/post-listing", response_model=PostListingObservationsResponse, tags=["Post-Listing"])
    def get_post_listing_observations(evaluation_id: str) -> PostListingObservationsResponse:
        res = service.get_post_listing_observations(evaluation_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"Evaluation '{evaluation_id}' not found in store", "code": "EVALUATION_NOT_FOUND"},
            )
        return res

    @router.get("/evaluations/{evaluation_id}/performance", response_model=PerformanceSummaryResponse, tags=["Post-Listing"])
    def get_performance_summary(evaluation_id: str) -> PerformanceSummaryResponse:
        res = service.get_performance_summary(evaluation_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"Evaluation '{evaluation_id}' not found in store", "code": "EVALUATION_NOT_FOUND"},
            )
        return res

    # -------------------------------------------------------------------------
    # 6.10 Backtest Datasets & Analytics
    # -------------------------------------------------------------------------

    @router.get("/backtest/datasets", response_model=BacktestDatasetListResponse, tags=["Backtest"])
    def list_backtest_datasets() -> BacktestDatasetListResponse:
        return service.list_backtest_datasets()

    @router.get("/backtest/analytics", response_model=BacktestAnalyticsResponse, tags=["Backtest"])
    def get_backtest_analytics() -> BacktestAnalyticsResponse:
        res = service.get_backtest_analytics()
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": "Backtest analytics report not found on disk", "code": "ANALYTICS_NOT_FOUND"},
            )
        return res

    # -------------------------------------------------------------------------
    # 6.11 Calibration
    # -------------------------------------------------------------------------

    @router.get("/calibration/proposals", response_model=CalibrationProposalListResponse, tags=["Calibration"])
    def list_calibration_proposals() -> CalibrationProposalListResponse:
        return service.list_calibration_proposals()

    @router.get("/calibration/proposals/{proposal_id}", response_model=CalibrationProposal, tags=["Calibration"])
    def get_calibration_proposal(proposal_id: str) -> CalibrationProposal:
        res = service.get_calibration_proposal(proposal_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": f"Calibration proposal '{proposal_id}' not found", "code": "PROPOSAL_NOT_FOUND"},
            )
        return res

    # -------------------------------------------------------------------------
    # 6.12 Configuration Status
    # -------------------------------------------------------------------------

    @router.get("/configuration/current", response_model=ConfigurationStatusResponse, tags=["Configuration"])
    def get_configuration_status() -> ConfigurationStatusResponse:
        return service.get_configuration_status()

    # -------------------------------------------------------------------------
    # 6.13 Ingestion & Evaluation Workflow (UI-7)
    # -------------------------------------------------------------------------

    @router.post("/ingest/document", response_model=IngestionResponse, tags=["Ingestion"])
    async def ingest_document(
        request: Request,
        file: UploadFile = File(...),
        mode: str = Form("final"),
    ) -> Response:
        """Upload and evaluate an IPO filing document (DRHP/RHP PDF)."""
        # Strict Security Boundary: reject any attempt to supply caller-controlled server paths or fallback controls
        form_data = await request.form()
        forbidden_params = {"reference_base_path", "base_path", "path", "file_path", "allow_fixture_fallbacks", "fallback", "allow_fallbacks"}
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

        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "message": "Filing PDF file is required.", "code": "VALIDATION_ERROR"},
            )

        max_size = 50 * 1024 * 1024
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={"error": "Payload Too Large", "message": "File size exceeds 50 MB limit.", "code": "PAYLOAD_TOO_LARGE"},
            )

        try:
            contents = await file.read()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "message": f"Failed to read uploaded file: {exc}", "code": "FILE_READ_ERROR"},
            )

        if len(contents) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={"error": "Payload Too Large", "message": f"File size ({len(contents)} bytes) exceeds 50 MB limit.", "code": "PAYLOAD_TOO_LARGE"},
            )

        try:
            ingest_res = service.ingest_document(
                file_bytes=contents,
                filename=file.filename,
                mode=mode,
            )
            res_code = status.HTTP_200_OK if ingest_res.is_duplicate else status.HTTP_201_CREATED
            return JSONResponse(status_code=res_code, content=ingest_res.model_dump())
        except IngestionPayloadTooLargeError as exc:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={"error": "Payload Too Large", "message": str(exc), "code": "PAYLOAD_TOO_LARGE"},
            )
        except IngestionValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "message": str(exc), "code": "VALIDATION_ERROR"},
            )
        except IngestionAwaitingIssueTermsError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Awaiting Issue Terms",
                    "message": str(exc),
                    "code": "AWAITING_ISSUE_TERMS",
                    "missing_fields": exc.missing_fields,
                    "resolution": exc.resolution,
                    **_activity_ref(exc),
                },
            )
        except (IngestionExtractionError, IngestionEvaluationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Unprocessable Entity", "message": str(exc), "code": "PROCESSING_FAILED", **_activity_ref(exc)},
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal Error", "message": f"Unexpected ingestion error: {exc}", "code": "INGESTION_INTERNAL_ERROR", **_activity_ref(exc)},
            )

    @router.post("/ingest/manual-terms", response_model=IngestionResponse, tags=["Ingestion"])
    async def ingest_document_manual_terms(
        request: Request,
        file: UploadFile = File(...),
        mode: str = Form("final"),
        price_band_low: Optional[float] = Form(None),
        price_band_high: Optional[float] = Form(None),
        lot_size: Optional[float] = Form(None),
        ofs: Optional[float] = Form(None),
        fresh_issue: Optional[float] = Form(None),
        explanation: Optional[str] = Form(None),
        confirm_conflicts: bool = Form(False),
    ) -> Response:
        """Step 5: filing ingestion with bounded, provenance-labelled manual
        entry of the required issue terms (price_band_low /
        price_band_high / lot_size / ofs / fresh_issue).

        issue.ofs is the Offer-for-Sale monetary amount in the filing's
        reporting unit (v1.5 contract: number, minimum 0). issue.fresh_issue
        is the fresh-issue monetary amount in the same reporting unit
        (v1.5 contract: number, minimum 0; explicit 0 states a pure-OFS
        offer). Manual values are recorded as MANUAL_ENTRY and are never
        presented as official-source verification. Conflicts with extracted
        or verified values block with 409 until explicitly confirmed; a
        verified official value is never displaced by a manual entry.
        """
        form_data = await request.form()
        forbidden_params = {"reference_base_path", "base_path", "path", "file_path", "allow_fixture_fallbacks", "fallback", "allow_fallbacks"}
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
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "message": "Filing PDF file is required.", "code": "VALIDATION_ERROR"},
            )
        max_size = 50 * 1024 * 1024
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={"error": "Payload Too Large", "message": "File size exceeds 50 MB limit.", "code": "PAYLOAD_TOO_LARGE"},
            )
        try:
            contents = await file.read()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "message": f"Failed to read uploaded file: {exc}", "code": "FILE_READ_ERROR"},
            ) from exc
        if len(contents) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={"error": "Payload Too Large", "message": f"File size ({len(contents)} bytes) exceeds 50 MB limit.", "code": "PAYLOAD_TOO_LARGE"},
            )

        manual_terms = {}
        if price_band_low is not None:
            manual_terms["price_band_low"] = price_band_low
        if price_band_high is not None:
            manual_terms["price_band_high"] = price_band_high
        if lot_size is not None:
            manual_terms["lot_size"] = lot_size
        if ofs is not None:
            # Explicit 0 is an operator statement of "no offer for sale"
            # and is preserved exactly; only an absent field is omitted.
            manual_terms["ofs"] = ofs
        if fresh_issue is not None:
            # Explicit 0 is an operator statement of a pure-OFS offer (no
            # fresh issue) and is preserved exactly; absent stays absent.
            manual_terms["fresh_issue"] = fresh_issue

        try:
            ingest_res = service.ingest_document(
                file_bytes=contents,
                filename=file.filename,
                mode=mode,
                manual_terms=manual_terms,
                manual_explanation=explanation,
                confirm_conflicts=confirm_conflicts,
            )
            res_code = status.HTTP_200_OK if ingest_res.is_duplicate else status.HTTP_201_CREATED
            return JSONResponse(status_code=res_code, content=ingest_res.model_dump())
        except IngestionPayloadTooLargeError as exc:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={"error": "Payload Too Large", "message": str(exc), "code": "PAYLOAD_TOO_LARGE", **_activity_ref(exc)},
            ) from exc
        except IngestionValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "message": str(exc), "code": "VALIDATION_ERROR", **_activity_ref(exc)},
            ) from exc
        except IngestionIssueTermConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Issue Term Conflict",
                    "message": str(exc),
                    "code": "ISSUE_TERM_CONFLICT",
                    "conflicts": exc.conflicts,
                    **_activity_ref(exc),
                },
            ) from exc
        except IngestionAwaitingIssueTermsError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Awaiting Issue Terms",
                    "message": str(exc),
                    "code": "AWAITING_ISSUE_TERMS",
                    "missing_fields": exc.missing_fields,
                    "resolution": exc.resolution,
                    **_activity_ref(exc),
                },
            ) from exc
        except (IngestionExtractionError, IngestionEvaluationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Unprocessable Entity", "message": str(exc), "code": "PROCESSING_FAILED", **_activity_ref(exc)},
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal Error", "message": f"Unexpected ingestion error: {exc}", "code": "INGESTION_INTERNAL_ERROR", **_activity_ref(exc)},
            ) from exc

    # -------------------------------------------------------------------------
    # Ingestion Activity (durable diagnostics, separate from evaluations)
    # -------------------------------------------------------------------------

    def _activity_ref(exc: Exception) -> Dict[str, Any]:
        ingestion_id = getattr(exc, "ingestion_id", None)
        if not ingestion_id:
            return {}
        return {
            "ingestion_id": ingestion_id,
            "correlation_id": ingestion_id,
            "activity_url": f"/api/v1/ingestions/{ingestion_id}",
        }

    def _activity_404(ingestion_id: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Not Found",
                "message": f"No ingestion activity record exists for id '{ingestion_id}'.",
                "code": "INGESTION_NOT_FOUND",
                "ingestion_id": ingestion_id,
            },
        )

    @router.post("/ingestions/start", tags=["Ingestion"])
    async def start_ingestion(
        request: Request,
        file: UploadFile = File(...),
        mode: str = Form("final"),
    ) -> Response:
        """Start a traced ingestion in the background (202).

        Returns the ingestion/correlation id immediately; the client
        polls ``/ingestions/{id}`` and ``/ingestions/{id}/events`` for
        the live, durable activity trace.  Processing itself is the
        unchanged synchronous service path running on a thread.
        """
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "message": "Filing PDF file is required.", "code": "VALIDATION_ERROR"},
            )
        contents = await file.read()
        if len(contents) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={"error": "Payload Too Large", "message": "File size exceeds 50 MB limit.", "code": "PAYLOAD_TOO_LARGE"},
            )
        recorder = service.start_ingestion_async(
            file_bytes=contents, filename=file.filename, mode=mode
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "ingestion_id": recorder.ingestion_id,
                "correlation_id": recorder.ingestion_id,
                "status": recorder.snapshot()["status"],
                "activity_url": f"/api/v1/ingestions/{recorder.ingestion_id}",
                "events_url": f"/api/v1/ingestions/{recorder.ingestion_id}/events",
            },
        )

    @router.get("/ingestions/{ingestion_id}", tags=["Ingestion"])
    def get_ingestion_activity(ingestion_id: str) -> Dict[str, Any]:
        record = service.get_ingestion_activity(ingestion_id)
        if record is None:
            raise _activity_404(ingestion_id)
        return record

    @router.get("/ingestions/{ingestion_id}/events", tags=["Ingestion"])
    def get_ingestion_events(
        ingestion_id: str, after_sequence: int = Query(0, ge=0)
    ) -> Dict[str, Any]:
        record = service.get_ingestion_activity(ingestion_id)
        if record is None:
            raise _activity_404(ingestion_id)
        events = [
            e for e in record.get("events", []) if int(e.get("sequence", 0)) > after_sequence
        ]
        return {
            "ingestion_id": ingestion_id,
            "correlation_id": record.get("correlation_id", ingestion_id),
            "status": record.get("status"),
            "evaluation_run": bool(record.get("evaluation_run")),
            "persisted": bool(record.get("persisted")),
            "evaluation_id": record.get("evaluation_id"),
            "error_code": record.get("error_code"),
            "missing_fields": record.get("missing_fields") or [],
            "result": record.get("result"),
            "events": events,
        }

    @router.get("/ingestions", tags=["Ingestion"])
    def list_ingestion_activities(limit: int = Query(50, ge=1, le=200)) -> Dict[str, Any]:
        return {"items": service.list_ingestion_activities(limit)}

    # -------------------------------------------------------------------------
    # 6.14 Lifecycle Governance Operations
    # -------------------------------------------------------------------------

    @router.post("/evaluations/{evaluation_id}/archive", response_model=LifecycleActionResponse, tags=["Lifecycle"])
    def archive_evaluation(
        evaluation_id: str,
        payload: Optional[LifecycleActionRequest] = None,
    ) -> LifecycleActionResponse:
        reason = payload.reason if payload else None
        actor = payload.actor if payload else None
        try:
            return service.archive_evaluation(evaluation_id, reason=reason, actor=actor)
        except EvaluationNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": str(exc), "code": "EVALUATION_NOT_FOUND"},
            ) from exc
        except ProtectedRecordError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "message": str(exc), "code": "PROTECTED_RECORD"},
            ) from exc
        except InvalidStateTransitionError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Conflict", "message": str(exc), "code": "INVALID_STATE_TRANSITION"},
            ) from exc

    @router.post("/evaluations/{evaluation_id}/unarchive", response_model=LifecycleActionResponse, tags=["Lifecycle"])
    def unarchive_evaluation(
        evaluation_id: str,
        payload: Optional[LifecycleActionRequest] = None,
    ) -> LifecycleActionResponse:
        reason = payload.reason if payload else None
        actor = payload.actor if payload else None
        try:
            return service.unarchive_evaluation(evaluation_id, reason=reason, actor=actor)
        except EvaluationNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": str(exc), "code": "EVALUATION_NOT_FOUND"},
            ) from exc
        except InvalidStateTransitionError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Conflict", "message": str(exc), "code": "INVALID_STATE_TRANSITION"},
            ) from exc

    @router.post("/evaluations/{evaluation_id}/make-active", response_model=LifecycleActionResponse, tags=["Lifecycle"])
    def make_evaluation_active(
        evaluation_id: str,
        payload: Optional[LifecycleActionRequest] = None,
    ) -> LifecycleActionResponse:
        reason = payload.reason if payload else None
        actor = payload.actor if payload else None
        try:
            return service.make_evaluation_active(evaluation_id, reason=reason, actor=actor)
        except EvaluationNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "message": str(exc), "code": "EVALUATION_NOT_FOUND"},
            ) from exc
        except CyclicLineageError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "message": str(exc), "code": "CYCLIC_LINEAGE"},
            ) from exc
        except InvalidStateTransitionError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Conflict", "message": str(exc), "code": "INVALID_STATE_TRANSITION"},
            ) from exc

    return router


def create_app(service: Optional[PresentationService] = None) -> FastAPI:
    """FastAPI application factory with explicit, scoped write routes."""
    if service is None:
        cfg = PresentationConfig(
            store_root=os.getenv("IPO_STORE_ROOT", "build/evaluations"),
            config_dir=os.getenv("IPO_CONFIG_DIR", "config"),
            dataset_path=os.getenv("IPO_DATASET_PATH", "build/dataset/dataset.json"),
            analytics_path=os.getenv("IPO_ANALYTICS_PATH", "build/analytics/analytics.json"),
            proposal_path=os.getenv("IPO_PROPOSAL_PATH", "config/calibration-proposal.v1.6.0.json"),
        )
        service = PresentationService(cfg)

    app = FastAPI(
        title="IPO Screening Engine — Presentation Read-Model API",
        version="1.0.0",
        description="Personal-use IPO presentation API: deterministic GET read models plus scoped filing-ingestion and evaluation-lifecycle POST actions. Requests require a localhost/loopback Host, and workflow POSTs require an explicit same-origin Origin. Scoring and configuration are not mutable through this API.",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Restrict every browser-facing route to loopback Host authorities. This
    # prevents DNS rebinding from making an untrusted site appear same-origin.
    # Only explicit local workflow POSTs are accepted, and those require an
    # exact same-origin Origin header (missing Origin fails closed).
    @app.middleware("http")
    async def write_scope_guard(request: Request, call_next):
        request_host = request.headers.get("host", "")
        if not _is_loopback_authority(request_host):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Bad Request",
                    "message": "The personal-use API accepts only localhost or loopback Host authorities.",
                    "code": "LOOPBACK_HOST_REQUIRED",
                },
            )

        if request.method not in ("GET", "HEAD", "OPTIONS"):
            normalized_path = request.url.path.rstrip("/")
            segments = normalized_path.strip("/").split("/")
            is_ingest = normalized_path in (
                "/api/v1/ingest/document",
                # Step 5: bounded manual issue-term entry (authorized route,
                # subject to the same origin/loopback guards below).
                "/api/v1/ingest/manual-terms",
                # Ingestion activity: start a traced ingestion (same guards).
                "/api/v1/ingestions/start",
            )
            is_lifecycle_action = (
                len(segments) == 5
                and segments[:3] == ["api", "v1", "evaluations"]
                and bool(segments[3])
                and segments[4] in {"archive", "unarchive", "make-active"}
            )
            is_workbench_action = normalized_path in {
                "/workbench/api/hash",
                "/workbench/api/v1/secondary/evaluate",
                "/workbench/api/v1/scenario/evaluate",
                "/workbench/actions/inject-rescore",
                "/workbench/actions/scenario",
            }
            if request.method != "POST" or not (is_ingest or is_lifecycle_action or is_workbench_action):
                return JSONResponse(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    content={
                        "error": "Method Not Allowed",
                        "message": (
                            f"Method {request.method} is not enabled on this endpoint. "
                            "Only GET/HEAD/OPTIONS and the documented ingestion/lifecycle POST actions are supported."
                        ),
                        "code": "READ_ONLY_METHOD_NOT_ALLOWED",
                    },
                    headers={"Allow": "GET, HEAD, OPTIONS"},
                )

            origin = request.headers.get("origin")
            if not origin:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Forbidden",
                        "message": "Workflow POST requests require an explicit same-origin Origin header.",
                        "code": "ORIGIN_REQUIRED",
                    },
                )

            try:
                origin_parts = urlsplit(origin)
                # Reject malformed/out-of-range ports before comparing origins.
                _ = origin_parts.port
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Forbidden",
                        "message": "Workflow POST requests require a valid same-origin Origin header.",
                        "code": "CROSS_ORIGIN_WRITE_REJECTED",
                    },
                )

            if (
                origin_parts.scheme.lower() != request.url.scheme.lower()
                or origin_parts.netloc.lower() != request_host.lower()
                or not _is_loopback_authority(origin_parts.netloc)
                or origin_parts.path not in ("", "/")
                or origin_parts.query
                or origin_parts.fragment
            ):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Forbidden",
                        "message": "Cross-origin workflow requests are not accepted by the local personal-use API.",
                        "code": "CROSS_ORIGIN_WRITE_REJECTED",
                    },
                )

        response: Response = await call_next(request)
        return response

    # Custom exception handler for HTTPException with consistent JSON envelope
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            content = exc.detail
        else:
            content = {
                "error": "Client Error",
                "message": str(exc.detail),
                "code": f"HTTP_{exc.status_code}",
            }
        return JSONResponse(status_code=exc.status_code, content=content)

    router = create_router(service)
    app.include_router(router)

    # Embed the governed Layer 2C / Layer 3 workbench in the existing UI host.
    # The sub-application shares the exact evaluation store selected by this
    # presentation service while keeping supplemental/secondary/operator bytes
    # in a sibling isolated workbench directory.
    from tools import ui_dashboard as workbench

    workbench.configure_workbench(
        service.config.store_root,
        Path(service.config.store_root).resolve().parent / "workbench",
    )
    app.mount("/workbench", workbench.app, name="workbench")

    # Mount UI-2 frontend presentation layer if present
    frontend_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend"
    if frontend_dir.exists() and (frontend_dir / "index.html").exists():
        from fastapi.responses import RedirectResponse
        from fastapi.staticfiles import StaticFiles

        app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")

        @app.get("/", include_in_schema=False)
        def root_redirect():
            return RedirectResponse(url="/ui/")

    # App-level reference to the service
    app.state.service = service

    return app


# Default singleton instance for uvicorn
app = create_app()
