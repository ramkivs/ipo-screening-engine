"""UI-1 FastAPI Presentation Read-Model API Implementation.

Implements read-only REST endpoints matching docs/openapi/presentation-api-v1.yaml.
Strictly read-only: rejects POST / PUT / PATCH / DELETE with 405 Method Not Allowed.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
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
    IpoDetail,
    IpoHistoryResponse,
    IpoListResponse,
    PerformanceSummaryResponse,
    PostListingObservationsResponse,
)
from .service import PresentationConfig, PresentationService


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
            read_only=True,
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
    def get_ipo_history(ipo_id: str) -> IpoHistoryResponse:
        res = service.get_ipo_history(ipo_id)
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

    return router


def create_app(service: Optional[PresentationService] = None) -> FastAPI:
    """FastAPI application factory with strict read-only enforcement."""
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
        description="Deterministic read-only presentation API for Indian Mainboard IPO Screening Engine.",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for local preview/development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "HEAD", "OPTIONS"],
        allow_headers=["*"],
    )

    # Strict Read-Only Middleware: blocks POST, PUT, PATCH, DELETE
    @app.middleware("http")
    async def read_only_guard(request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={
                    "error": "Method Not Allowed",
                    "message": f"Method {request.method} is prohibited. The Presentation API is strictly read-only.",
                    "code": "READ_ONLY_METHOD_NOT_ALLOWED",
                },
                headers={"Allow": "GET, HEAD, OPTIONS"},
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
