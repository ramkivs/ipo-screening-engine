"""UI-1 Presentation Read-Model Package.

Provides a decoupled, deterministic read-only presentation API and service
boundary projecting authoritative EvaluationStore and post-listing records.
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
