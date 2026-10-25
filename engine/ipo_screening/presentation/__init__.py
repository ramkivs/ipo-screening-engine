"""Presentation API and service package.

Provides deterministic read-model projections plus explicit filing-ingestion
and evaluation-lifecycle workflows over the local EvaluationStore.
"""

from .api import app, create_app, create_router
from .models import (
    ApiError,
    ApiMeta,
    BacktestAnalyticsResponse,
    BacktestDatasetListResponse,
    BacktestDatasetSummary,
    CalibrationProposal,
    CalibrationProposalListResponse,
    ConfigurationStatusResponse,
    EvaluationDetail,
    EvaluationListResponse,
    EvaluationSummary,
    EvidenceDetail,
    EvidenceResponse,
    HealthStatus,
    IpoDetail,
    IpoHistoryResponse,
    IpoListResponse,
    IpoSummary,
    PerformanceSummaryResponse,
    PostListingObservationsResponse,
)
from .service import PresentationConfig, PresentationService

__all__ = [
    "app",
    "create_app",
    "create_router",
    "PresentationConfig",
    "PresentationService",
    "HealthStatus",
    "ApiMeta",
    "IpoSummary",
    "IpoListResponse",
    "IpoDetail",
    "IpoHistoryResponse",
    "EvaluationSummary",
    "EvaluationListResponse",
    "EvaluationDetail",
    "EvidenceDetail",
    "EvidenceResponse",
    "PostListingObservationsResponse",
    "PerformanceSummaryResponse",
    "BacktestDatasetSummary",
    "BacktestDatasetListResponse",
    "BacktestAnalyticsResponse",
    "CalibrationProposal",
    "CalibrationProposalListResponse",
    "ConfigurationStatusResponse",
    "ApiError",
]
