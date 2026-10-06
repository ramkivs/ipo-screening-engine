"""UI-1 Presentation Read-Model Pydantic Schemas.

Declares deterministic, read-only DTOs for the Presentation API matching
OpenAPI specification docs/openapi/presentation-api-v1.yaml.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str = "healthy"
    timestamp: str
    read_only: bool = True


class ApiMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    api_version: str = "v1"
    engine_version: str = "1.5.0"
    spec_version: str = "1.5"
    active_config_version: str = "1.5.0"
    candidate_config_version: str = "1.6.0"
    candidate_config_status: str = "IMPLEMENTED_INACTIVE"
    golden_result_hash: str = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
    read_only: bool = True


class IpoSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ipo_id: str
    company_name: str
    sector_profile: Optional[str] = None
    evaluation_count: int = 0
    latest_evaluation_id: Optional[str] = None
    latest_evaluation_mode: Optional[str] = None
    latest_score: Optional[float] = None
    latest_verdict: Optional[str] = None
    latest_confidence: Optional[str] = None


class IpoListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    items: List[IpoSummary]
    total: int
    page: int
    page_size: int
    pages: int


class EvaluationSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evaluation_id: str
    ipo_id: str
    company_name: str
    evaluation_mode: str
    evaluation_timestamp: str
    final_score: float
    base_score: Optional[float] = None
    penalties_total: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    verdict: str
    confidence: str
    completeness_pct: Optional[float] = None
    engine_version: str = "1.5.0"
    config_version: str = "1.5.0"
    result_hash: str


class EvaluationListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    items: List[EvaluationSummary]
    total: int
    page: int
    page_size: int
    pages: int


class IpoDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ipo_id: str
    company_name: str
    sector_profile: Optional[str] = None
    icdr_route: Optional[str] = None
    evaluations: List[EvaluationSummary] = Field(default_factory=list)


class CriterionScore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    label: str
    max: float
    score: float
    metric: Optional[str] = None
    value: Optional[Any] = None
    state: str = "SCORED"
    reason: Optional[str] = None
    capped_by: Optional[str] = None


class ModuleScore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    max: float
    score: float
    criteria: List[CriterionScore] = Field(default_factory=list)


class KnockoutRule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    label: str
    state: str  # CLEAR, TRIGGERED, UNVERIFIED
    missing_inputs: List[str] = Field(default_factory=list)


class KnockoutSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str
    rules: List[KnockoutRule] = Field(default_factory=list)


class PenaltyItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    label: str
    points: float
    state: str
    trigger: Optional[bool] = None


class MissingUnverifiedItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    category: str
    item: str
    rule_id: Optional[str] = None
    description: Optional[str] = None


class EvaluationScoreDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    final_score: float
    base_score: float
    penalties_total: float
    lower_bound: float
    upper_bound: float
    available_points: Optional[float] = None
    unknown_points: Optional[float] = None
    total_evaluable_points: Optional[float] = None
    confidence: str
    completeness_pct: float
    modules: List[ModuleScore] = Field(default_factory=list)


class EvaluationDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evaluation_id: str
    ipo_id: str
    company_name: str
    evaluation_mode: str
    evaluation_timestamp: str
    engine_version: str
    spec_version: str
    config_version: str
    config_hash: str
    input_snapshot_hash: str
    source_manifest_hash: str
    market_snapshot_hash: Optional[str] = None
    peer_snapshot_hash: Optional[str] = None
    result_hash: str
    score: EvaluationScoreDetail
    knockouts: KnockoutSummary
    penalties: List[PenaltyItem] = Field(default_factory=list)
    verdict: Dict[str, Any]
    missing_unverified: List[MissingUnverifiedItem] = Field(default_factory=list)
    preliminary_delta: Optional[Dict[str, Any]] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class EvidenceDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evidence_id: str
    field: str
    source: Optional[str] = None
    document: Optional[str] = None
    page: Optional[int] = None
    locator: Optional[str] = None
    quote: Optional[str] = None
    extracted_value: Optional[Any] = None
    unit: Optional[str] = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evaluation_id: str
    source_manifest_hash: str
    sources: List[Any] = Field(default_factory=list)
    evidence_count: int
    items: List[EvidenceDetail] = Field(default_factory=list)


class IpoHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ipo_id: str
    company_name: str
    history: List[EvaluationSummary] = Field(default_factory=list)
    delta: Optional[Dict[str, Any]] = None


class PostListingObservationItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    observation_id: str
    horizon: str
    version: int
    target_date: str
    actual_trading_date: str
    status: str
    issue_price: str
    prices: Optional[Dict[str, Any]] = None
    benchmark: Optional[Dict[str, Any]] = None
    returns: Optional[Dict[str, Any]] = None


class PostListingObservationsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    final_evaluation_id: str
    ipo_id: str
    observation_count: int
    observations: List[PostListingObservationItem] = Field(default_factory=list)


class HorizonPerformance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str
    ipo_return_pct: Optional[str] = None
    benchmark_return_pct: Optional[str] = None
    excess_return_pct: Optional[str] = None


class PerformanceSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    final_evaluation_id: str
    ipo_id: str
    company_name: str
    issue_price: Optional[str] = None
    listing_date: Optional[str] = None
    horizons: Dict[str, HorizonPerformance] = Field(default_factory=dict)


class BacktestDatasetSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dataset_id: str
    dataset_hash: str
    row_count: int
    included_observation_count: int = 0
    generated_at: Optional[str] = None
    status_counts: Dict[str, int] = Field(default_factory=dict)


class BacktestDatasetListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    datasets: List[BacktestDatasetSummary] = Field(default_factory=list)
    total: int = 0


class BacktestAnalyticsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    analysis_hash: str
    dataset_hash: str
    sample_maturity: Dict[str, str] = Field(default_factory=dict)
    leakage_audit_passed: bool
    rank_ic: Optional[Dict[str, Any]] = None
    hit_rates: Optional[Dict[str, Any]] = None
    avoided_loss_rates: Optional[Dict[str, Any]] = None
    decile_buckets: Optional[List[Dict[str, Any]]] = None


class CalibrationProposal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    proposal_id: str
    proposal_hash: str
    baseline_config_version: str
    candidate_config_version: str
    baseline_config_hash: str
    candidate_config_hash: str
    source_dataset_hash: str
    source_analysis_hash: str
    maturity_gate: str
    status: str
    approval_status: str
    module_weight_adjustments: Optional[Dict[str, Any]] = None
    overfitting_safeguards: Optional[Dict[str, Any]] = None
    knockout_firewall_status: Optional[str] = None


class CalibrationProposalListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    proposals: List[CalibrationProposal] = Field(default_factory=list)
    total: int = 0


class ConfigLifecycleItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    version: str
    status: str
    is_active: bool
    config_hash: str
    description: Optional[str] = None
    source_proposal_hash: Optional[str] = None


class ConfigurationStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    active_configuration: ConfigLifecycleItem
    candidate_configuration: ConfigLifecycleItem
    frozen_core_status: str = "VERIFIED"
    golden_result_status: str = "VERIFIED"


class ApiError(BaseModel):
    model_config = ConfigDict(extra="ignore")
    error: str
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None
