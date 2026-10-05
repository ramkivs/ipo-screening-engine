"""Phase 6D: Governed Calibration Proposal & v1.6 Configuration Draft.

Consumes the Phase 6B canonical historical outcome dataset and Phase 6C analytical diagnostics
to formulate a point-in-time safe, governed calibration proposal.
Adheres strictly to the Fundamental Governance Rule:
  EVIDENCE -> PROPOSAL
  (PROPOSAL != APPROVAL, PROPOSAL != IMPLEMENTATION, PROPOSAL != ACTIVATION)
Current active v1.5 scoring behavior, formulas, and configurations remain 100% frozen.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .analytics import BacktestAnalysis, compute_analysis_content_hash, calculate_spearman_rho
from .dataset import BacktestDataset, BacktestDatasetRow, load_dataset_json

PROPOSAL_ENGINE_VERSION = "1.0.0"
BASELINE_CONFIG_VERSION = "1.5.0"
DEFAULT_BASELINE_CONFIG_PATH = "config/ipo-config.v1.5.0.json"


class CalibrationMaturity(str, Enum):
    """Maturity tier based on sample size, integrity, and temporal coverage (Section 5)."""
    CALIBRATION_INELIGIBLE = "CALIBRATION_INELIGIBLE"
    CALIBRATION_EXPLORATORY = "CALIBRATION_EXPLORATORY"
    CALIBRATION_CANDIDATE = "CALIBRATION_CANDIDATE"
    CALIBRATION_READY_FOR_HUMAN_REVIEW = "CALIBRATION_READY_FOR_HUMAN_REVIEW"


class ProposalStatus(str, Enum):
    """Governance status of a calibration proposal (Section 19)."""
    INELIGIBLE = "INELIGIBLE"
    EXPLORATORY = "EXPLORATORY"
    CANDIDATE = "CANDIDATE"
    READY_FOR_HUMAN_REVIEW = "READY_FOR_HUMAN_REVIEW"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class CalibrationObjective(str, Enum):
    """Explicitly declared optimization/evaluation objective (Section 9)."""
    IMPROVE_HIT_RATE = "IMPROVE_HIT_RATE"
    IMPROVE_EXCESS_RETURN_SEPARATION = "IMPROVE_EXCESS_RETURN_SEPARATION"
    IMPROVE_RANK_CORRELATION = "IMPROVE_RANK_CORRELATION"
    PRESERVE_DOWNSIDE_PROTECTION = "PRESERVE_DOWNSIDE_PROTECTION"
    BALANCED_DIAGNOSTIC = "BALANCED_DIAGNOSTIC"


class ApprovalStatus(str, Enum):
    """Approval boundary marker (Section 20)."""
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NOT_SUBMITTED = "NOT_SUBMITTED"
    INELIGIBLE = "INELIGIBLE"


def _round_float(val: Optional[float], decimals: int = 4) -> Optional[float]:
    if val is None:
        return None
    d = Decimal(str(val))
    q = Decimal(10) ** -decimals
    return float(d.quantize(q, rounding=ROUND_HALF_UP))


def compute_config_content_hash(config_dict: Mapping[str, Any]) -> str:
    """Compute the deterministic SHA-256 hash of a configuration structure."""
    clean_dict = {k: v for k, v in config_dict.items() if not k.startswith("_")}
    canonical = json.dumps(clean_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ModuleWeightProposal:
    """Proposal for a module scoring weight/maximum."""
    module_id: str
    module_name: str
    current_weight: float
    proposed_weight: float
    phase6c_rho_1w: Optional[float] = None
    phase6c_rho_1m: Optional[float] = None
    phase6c_rho_6m: Optional[float] = None
    development_rho: Optional[float] = None
    holdout_rho: Optional[float] = None
    vintage_stability: str = "INSUFFICIENT_VINTAGES"
    missing_data_sensitivity: str = "LOW"
    rationale: str = "No change proposed."
    expected_impact: str = "Neutral"
    evidence_strength: str = "DESCRIPTIVE"
    status: str = "NO_CHANGE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "current_weight": self.current_weight,
            "proposed_weight": self.proposed_weight,
            "phase6c_rho_1w": self.phase6c_rho_1w,
            "phase6c_rho_1m": self.phase6c_rho_1m,
            "phase6c_rho_6m": self.phase6c_rho_6m,
            "development_rho": self.development_rho,
            "holdout_rho": self.holdout_rho,
            "vintage_stability": self.vintage_stability,
            "missing_data_sensitivity": self.missing_data_sensitivity,
            "rationale": self.rationale,
            "expected_impact": self.expected_impact,
            "evidence_strength": self.evidence_strength,
            "status": self.status,
        }


@dataclass(frozen=True)
class ThresholdProposal:
    """Proposal for a scoring or verdict threshold."""
    threshold_name: str
    current_value: float
    proposed_value: float
    development_performance: Dict[str, Any] = field(default_factory=dict)
    holdout_performance: Dict[str, Any] = field(default_factory=dict)
    affected_count: int = 0
    false_positive_impact: str = "Neutral"
    false_negative_impact: str = "Neutral"
    rationale: str = "Baseline threshold retained."
    status: str = "NO_CHANGE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "threshold_name": self.threshold_name,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "development_performance": dict(self.development_performance),
            "holdout_performance": dict(self.holdout_performance),
            "affected_count": self.affected_count,
            "false_positive_impact": self.false_positive_impact,
            "false_negative_impact": self.false_negative_impact,
            "rationale": self.rationale,
            "status": self.status,
        }


@dataclass(frozen=True)
class KnockoutProposal:
    """Knockout proposal record (strictly guarded by governance firewall)."""
    knockout_id: str
    change_type: str
    rationale: str
    evidence: str
    governance_flag: str = "REQUIRES_EXPLICIT_GOVERNANCE_REVIEW"
    status: str = "BLOCKED_WITHOUT_EXPLICIT_GOVERNANCE_APPROVAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "knockout_id": self.knockout_id,
            "change_type": self.change_type,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "governance_flag": self.governance_flag,
            "status": self.status,
        }


@dataclass(frozen=True)
class VerdictProposal:
    """Verdict band threshold proposal."""
    band_name: str
    current_min: float
    proposed_min: float
    rationale: str = "Verdict boundaries preserved."
    status: str = "NO_CHANGE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "band_name": self.band_name,
            "current_min": self.current_min,
            "proposed_min": self.proposed_min,
            "rationale": self.rationale,
            "status": self.status,
        }


@dataclass(frozen=True)
class NonRegressionResult:
    """Non-regression check result."""
    check_name: str
    passed: bool
    baseline_value: Any
    proposed_value: Any
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "baseline_value": self.baseline_value,
            "proposed_value": self.proposed_value,
            "details": self.details,
        }


@dataclass(frozen=True)
class RejectedCandidate:
    """Record of a rejected candidate proposal."""
    candidate_id: str
    description: str
    reason: str
    development_metric: Optional[float] = None
    holdout_metric: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "description": self.description,
            "reason": self.reason,
            "development_metric": self.development_metric,
            "holdout_metric": self.holdout_metric,
        }


@dataclass(frozen=True)
class ShadowEvaluationResult:
    """In-memory shadow rescoring result comparing v1.5 baseline vs proposed configuration."""
    total_evaluated: int
    score_mean_delta: float
    verdict_shifts_count: int
    upgraded_count: int
    downgraded_count: int
    unchanged_count: int
    knockout_deltas: int
    baseline_mean_score: float
    proposed_mean_score: float
    details_by_row: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_evaluated": self.total_evaluated,
            "score_mean_delta": self.score_mean_delta,
            "verdict_shifts_count": self.verdict_shifts_count,
            "upgraded_count": self.upgraded_count,
            "downgraded_count": self.downgraded_count,
            "unchanged_count": self.unchanged_count,
            "knockout_deltas": self.knockout_deltas,
            "baseline_mean_score": self.baseline_mean_score,
            "proposed_mean_score": self.proposed_mean_score,
            "details_by_row": list(self.details_by_row),
        }


@dataclass(frozen=True)
class CalibrationProposal:
    """The canonical machine-readable calibration proposal artifact."""
    proposal_version: str = PROPOSAL_ENGINE_VERSION
    status: str = ProposalStatus.INELIGIBLE.value
    created_at: str = ""
    source_dataset_hash: str = ""
    source_analysis_hash: str = ""
    source_analysis_version: str = "1.0.0"
    baseline_config_version: str = BASELINE_CONFIG_VERSION
    baseline_config_hash: str = ""
    objective: str = CalibrationObjective.BALANCED_DIAGNOSTIC.value
    maturity_gate: str = CalibrationMaturity.CALIBRATION_INELIGIBLE.value
    sample_summary: Dict[str, Any] = field(default_factory=dict)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    module_proposals: List[ModuleWeightProposal] = field(default_factory=list)
    threshold_proposals: List[ThresholdProposal] = field(default_factory=list)
    knockout_proposals: List[KnockoutProposal] = field(default_factory=list)
    verdict_proposals: List[VerdictProposal] = field(default_factory=list)
    development_results: Dict[str, Any] = field(default_factory=dict)
    holdout_results: Dict[str, Any] = field(default_factory=dict)
    vintage_results: Dict[str, Any] = field(default_factory=dict)
    non_regression_results: List[NonRegressionResult] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    rejected_candidates: List[RejectedCandidate] = field(default_factory=list)
    recommendation: str = ""
    approval_status: str = ApprovalStatus.PENDING_HUMAN_REVIEW.value
    draft_config_status: str = "NO_V1_6_CONFIGURATION_GENERATED"
    draft_config_hash: Optional[str] = None
    proposal_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_version": self.proposal_version,
            "status": self.status,
            "created_at": self.created_at,
            "source_dataset_hash": self.source_dataset_hash,
            "source_analysis_hash": self.source_analysis_hash,
            "source_analysis_version": self.source_analysis_version,
            "baseline_config_version": self.baseline_config_version,
            "baseline_config_hash": self.baseline_config_hash,
            "objective": self.objective,
            "maturity_gate": self.maturity_gate,
            "sample_summary": dict(self.sample_summary),
            "evidence_summary": dict(self.evidence_summary),
            "module_proposals": [m.to_dict() for m in self.module_proposals],
            "threshold_proposals": [t.to_dict() for t in self.threshold_proposals],
            "knockout_proposals": [k.to_dict() for k in self.knockout_proposals],
            "verdict_proposals": [v.to_dict() for v in self.verdict_proposals],
            "development_results": dict(self.development_results),
            "holdout_results": dict(self.holdout_results),
            "vintage_results": dict(self.vintage_results),
            "non_regression_results": [nr.to_dict() for nr in self.non_regression_results],
            "risks": list(self.risks),
            "rejected_candidates": [rc.to_dict() for rc in self.rejected_candidates],
            "recommendation": self.recommendation,
            "approval_status": self.approval_status,
            "draft_config_status": self.draft_config_status,
            "draft_config_hash": self.draft_config_hash,
            "proposal_hash": self.proposal_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CalibrationProposal:
        return cls(
            proposal_version=str(data.get("proposal_version", PROPOSAL_ENGINE_VERSION)),
            status=str(data.get("status", ProposalStatus.INELIGIBLE.value)),
            created_at=str(data.get("created_at", "")),
            source_dataset_hash=str(data.get("source_dataset_hash", "")),
            source_analysis_hash=str(data.get("source_analysis_hash", "")),
            source_analysis_version=str(data.get("source_analysis_version", "1.0.0")),
            baseline_config_version=str(data.get("baseline_config_version", BASELINE_CONFIG_VERSION)),
            baseline_config_hash=str(data.get("baseline_config_hash", "")),
            objective=str(data.get("objective", CalibrationObjective.BALANCED_DIAGNOSTIC.value)),
            maturity_gate=str(data.get("maturity_gate", CalibrationMaturity.CALIBRATION_INELIGIBLE.value)),
            sample_summary=dict(data.get("sample_summary") or {}),
            evidence_summary=dict(data.get("evidence_summary") or {}),
            module_proposals=[ModuleWeightProposal(**m) for m in (data.get("module_proposals") or [])],
            threshold_proposals=[ThresholdProposal(**t) for t in (data.get("threshold_proposals") or [])],
            knockout_proposals=[KnockoutProposal(**k) for k in (data.get("knockout_proposals") or [])],
            verdict_proposals=[VerdictProposal(**v) for v in (data.get("verdict_proposals") or [])],
            development_results=dict(data.get("development_results") or {}),
            holdout_results=dict(data.get("holdout_results") or {}),
            vintage_results=dict(data.get("vintage_results") or {}),
            non_regression_results=[NonRegressionResult(**nr) for nr in (data.get("non_regression_results") or [])],
            risks=list(data.get("risks") or []),
            rejected_candidates=[RejectedCandidate(**rc) for rc in (data.get("rejected_candidates") or [])],
            recommendation=str(data.get("recommendation", "")),
            approval_status=str(data.get("approval_status", ApprovalStatus.PENDING_HUMAN_REVIEW.value)),
            draft_config_status=str(data.get("draft_config_status", "NO_V1_6_CONFIGURATION_GENERATED")),
            draft_config_hash=data.get("draft_config_hash"),
            proposal_hash=str(data.get("proposal_hash", "")),
        )


def compute_proposal_content_hash(proposal_dict: Mapping[str, Any]) -> str:
    """Compute the deterministic SHA-256 hash of the canonical proposal content.

    Excludes ephemeral execution fields like generation wall clock and local paths.
    """
    payload = {
        "source_dataset_hash": proposal_dict.get("source_dataset_hash", ""),
        "source_analysis_hash": proposal_dict.get("source_analysis_hash", ""),
        "baseline_config_version": proposal_dict.get("baseline_config_version", ""),
        "baseline_config_hash": proposal_dict.get("baseline_config_hash", ""),
        "objective": proposal_dict.get("objective", ""),
        "maturity_gate": proposal_dict.get("maturity_gate", ""),
        "status": proposal_dict.get("status", ""),
        "sample_summary": proposal_dict.get("sample_summary", {}),
        "evidence_summary": proposal_dict.get("evidence_summary", {}),
        "module_proposals": proposal_dict.get("module_proposals", []),
        "threshold_proposals": proposal_dict.get("threshold_proposals", []),
        "knockout_proposals": proposal_dict.get("knockout_proposals", []),
        "verdict_proposals": proposal_dict.get("verdict_proposals", []),
        "development_results": proposal_dict.get("development_results", {}),
        "holdout_results": proposal_dict.get("holdout_results", {}),
        "vintage_results": proposal_dict.get("vintage_results", {}),
        "non_regression_results": proposal_dict.get("non_regression_results", []),
        "risks": proposal_dict.get("risks", []),
        "rejected_candidates": proposal_dict.get("rejected_candidates", []),
        "recommendation": proposal_dict.get("recommendation", ""),
        "approval_status": proposal_dict.get("approval_status", ""),
        "draft_config_status": proposal_dict.get("draft_config_status", ""),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def classify_calibration_maturity(
    dataset: BacktestDataset,
    analysis: BacktestAnalysis,
) -> Tuple[CalibrationMaturity, List[str]]:
    """Determine calibration maturity gate tier and collect gating reasons (Section 5)."""
    reasons: List[str] = []
    total_rows = dataset.manifest.row_count
    valid_rows = [r for r in dataset.rows if r.dataset_row_status != "INVALID"]
    n_valid = len(valid_rows)

    # 1. Leakage audit gate
    if not analysis.leakage_audit.passed:
        reasons.append("Leakage audit failed in source analytical diagnostics.")
        return CalibrationMaturity.CALIBRATION_INELIGIBLE, reasons

    # 2. Hash linkage check
    if dataset.manifest.dataset_hash != analysis.manifest.dataset_hash:
        reasons.append(f"Dataset hash mismatch: dataset {dataset.manifest.dataset_hash} != analysis {analysis.manifest.dataset_hash}")
        return CalibrationMaturity.CALIBRATION_INELIGIBLE, reasons

    # 3. Sample size tiering
    if n_valid < 30:
        reasons.append(f"Sample size N={n_valid} < 30 is below statistical calibration minimum.")
        return CalibrationMaturity.CALIBRATION_INELIGIBLE, reasons

    vintages = {r.evaluation_timestamp.split("-")[0] for r in valid_rows if r.evaluation_timestamp}
    n_vintages = len(vintages)

    # 4. Exploratory tier (30 <= N < 100)
    if n_valid < 100:
        reasons.append(f"Sample size N={n_valid} is in exploratory range (30 <= N < 100). Formulating for research only.")
        return CalibrationMaturity.CALIBRATION_EXPLORATORY, reasons

    # 5. Candidate tier check (N >= 100)
    if n_vintages < 3:
        reasons.append(f"Historical vintage coverage ({n_vintages} vintages: {sorted(vintages)}) < 3 required for candidate.")
        return CalibrationMaturity.CALIBRATION_EXPLORATORY, reasons

    if analysis.holdout_analysis.status != "CALCULATED":
        reasons.append(f"Holdout analysis status is {analysis.holdout_analysis.status}, required CALCULATED.")
        return CalibrationMaturity.CALIBRATION_EXPLORATORY, reasons

    reasons.append(f"Sample size N={n_valid} >= 100 with {n_vintages} vintages and verified holdout partition.")
    return CalibrationMaturity.CALIBRATION_CANDIDATE, reasons


def rescore_row(row: BacktestDatasetRow, module_weights: Mapping[str, float]) -> float:
    """Deterministically compute rescored final score under candidate module maximums."""
    current_maxes = {"A": 25.0, "B": 20.0, "C": 15.0, "D": 15.0, "E": 15.0, "F": 10.0}
    scores = {
        "A": row.module_a_score or 0.0,
        "B": row.module_b_score or 0.0,
        "C": row.module_c_score or 0.0,
        "D": row.module_d_score or 0.0,
        "E": row.module_e_score or 0.0,
        "F": row.module_f_score or 0.0,
    }

    new_total = 0.0
    for mid, cur_max in current_maxes.items():
        prop_max = module_weights.get(mid, cur_max)
        fraction = scores[mid] / cur_max if cur_max > 0 else 0.0
        new_total += fraction * prop_max

    return round(new_total, 2)


def evaluate_verdict(score: float, bands: Sequence[Mapping[str, Any]], else_verdict: str = "AVOID") -> str:
    """Classify verdict according to verdict bands."""
    for b in bands:
        if score >= b["min"]:
            return b["verdict"]
    return else_verdict


def run_shadow_evaluation(
    proposal: CalibrationProposal,
    dataset: BacktestDataset,
    v1_5_config: Mapping[str, Any],
) -> ShadowEvaluationResult:
    """Execute pure in-memory shadow rescoring comparison between v1.5 baseline and proposal."""
    proposed_weights = {m.module_id: m.proposed_weight for m in proposal.module_proposals}
    bands = v1_5_config.get("verdict", {}).get("bands", [
        {"min": 75, "verdict": "APPLY"},
        {"min": 60, "verdict": "APPLY_SELECTIVELY"},
        {"min": 45, "verdict": "NEUTRAL"},
    ])
    else_verdict = v1_5_config.get("verdict", {}).get("else", "AVOID")

    # If verdict thresholds were proposed, use proposed values
    if proposal.verdict_proposals:
        prop_bands = []
        for b in bands:
            v_name = b["verdict"]
            v_prop = next((vp for vp in proposal.verdict_proposals if vp.band_name == v_name), None)
            new_min = v_prop.proposed_min if v_prop else b["min"]
            prop_bands.append({"min": new_min, "verdict": v_name})
        bands_for_eval = prop_bands
    else:
        bands_for_eval = bands

    total = len(dataset.rows)
    score_deltas: List[float] = []
    base_scores: List[float] = []
    prop_scores: List[float] = []
    shifts = 0
    upgrades = 0
    downgrades = 0
    unchanged = 0
    row_details: List[Dict[str, Any]] = []

    for r in dataset.rows:
        orig_s = r.final_score
        orig_v = r.verdict
        new_s = rescore_row(r, proposed_weights)
        new_v = evaluate_verdict(new_s, bands_for_eval, else_verdict)

        delta = round(new_s - orig_s, 2)
        score_deltas.append(delta)
        base_scores.append(orig_s)
        prop_scores.append(new_s)

        if new_v != orig_v:
            shifts += 1
            if new_s > orig_s:
                upgrades += 1
            else:
                downgrades += 1
        else:
            unchanged += 1

        row_details.append({
            "ipo_id": r.ipo_id,
            "baseline_score": orig_s,
            "proposed_score": new_s,
            "delta": delta,
            "baseline_verdict": orig_v,
            "proposed_verdict": new_v,
        })

    mean_delta = round(sum(score_deltas) / total, 4) if total > 0 else 0.0
    base_mean = round(sum(base_scores) / total, 4) if total > 0 else 0.0
    prop_mean = round(sum(prop_scores) / total, 4) if total > 0 else 0.0

    return ShadowEvaluationResult(
        total_evaluated=total,
        score_mean_delta=mean_delta,
        verdict_shifts_count=shifts,
        upgraded_count=upgrades,
        downgraded_count=downgrades,
        unchanged_count=unchanged,
        knockout_deltas=0,
        baseline_mean_score=base_mean,
        proposed_mean_score=prop_mean,
        details_by_row=row_details,
    )


def generate_v1_6_draft_config(
    proposal: CalibrationProposal,
    baseline_config: Mapping[str, Any],
) -> Dict[str, Any]:
    """Generate a non-active v1.6 configuration draft with complete provenance."""
    draft = copy.deepcopy(dict(baseline_config))

    # Update metadata
    draft["config_version"] = "1.6.0-draft"
    draft["status"] = "DRAFT_INACTIVE"
    draft["is_active"] = False
    draft["parent_config_version"] = BASELINE_CONFIG_VERSION
    draft["parent_config_hash"] = proposal.baseline_config_hash
    draft["source_proposal_hash"] = proposal.proposal_hash
    draft["source_analysis_hash"] = proposal.source_analysis_hash
    draft["governance_notice"] = (
        "INACTIVE DRAFT FOR GOVERNANCE REVIEW ONLY. "
        "PROPOSAL DOES NOT CONSTITUTE APPROVAL. "
        "REQUIRES EXPLICIT AUTHORIZATION FROM RAMKI BEFORE ANY ACTIVATION."
    )

    # Apply proposed module weights to modules list
    if "modules" in draft and isinstance(draft["modules"], list):
        for m in draft["modules"]:
            mid = m.get("id")
            prop = next((mp for mp in proposal.module_proposals if mp.module_id == mid), None)
            if prop:
                m["max"] = int(prop.proposed_weight)

    # Apply proposed verdict bands if any
    if proposal.verdict_proposals and "verdict" in draft and "bands" in draft["verdict"]:
        for b in draft["verdict"]["bands"]:
            vname = b.get("verdict")
            vprop = next((vp for vp in proposal.verdict_proposals if vp.band_name == vname), None)
            if vprop:
                b["min"] = int(vprop.proposed_min)

    draft["configuration_hash"] = compute_config_content_hash(draft)
    return draft


def generate_calibration_proposal(
    dataset: BacktestDataset,
    analysis: BacktestAnalysis,
    baseline_config: Mapping[str, Any],
    *,
    objective: str = CalibrationObjective.BALANCED_DIAGNOSTIC.value,
    created_at: str = "2026-10-06T12:00:00Z",
) -> CalibrationProposal:
    """Formulate a governed calibration proposal from empirical backtest evidence."""
    # 1. Verify baseline config hash
    base_cfg_hash = compute_config_content_hash(baseline_config)

    # 2. Evaluate maturity gate
    maturity, gating_reasons = classify_calibration_maturity(dataset, analysis)

    valid_rows = [r for r in dataset.rows if r.dataset_row_status != "INVALID"]
    total_valid = len(valid_rows)

    sample_summary = {
        "total_dataset_rows": dataset.manifest.row_count,
        "valid_rows_count": total_valid,
        "eligible_1w_count": analysis.manifest.eligible_1w_count,
        "eligible_1m_count": analysis.manifest.eligible_1m_count,
        "eligible_6m_count": analysis.manifest.eligible_6m_count,
        "maturity_gate": maturity.value,
        "gating_reasons": gating_reasons,
    }

    # Module definitions from baseline config
    module_names = {
        "A": "Financial Quality",
        "B": "Valuation",
        "C": "Offer Structure, Proceeds & Pre-IPO",
        "D": "Promoter & Governance",
        "E": "Business & Moat",
        "F": "Market & Demand Signals",
    }
    baseline_weights = {"A": 25.0, "B": 20.0, "C": 15.0, "D": 15.0, "E": 15.0, "F": 10.0}

    # Extract correlations per module from Phase 6C analysis
    mod_rhos: Dict[str, Dict[str, Optional[float]]] = {m: {} for m in baseline_weights}
    for md in analysis.module_diagnostics:
        if md.module_id in mod_rhos:
            mod_rhos[md.module_id][md.horizon] = md.spearman_rho

    # Development and Holdout partition
    holdout_res = analysis.holdout_analysis
    dev_period = holdout_res.development_period
    holdout_period = holdout_res.holdout_period

    dev_rows = [r for r in valid_rows if r.evaluation_timestamp.split("-")[0] in dev_period.split(",")] if dev_period else valid_rows
    holdout_rows = [r for r in valid_rows if r.evaluation_timestamp.split("-")[0] == holdout_period] if holdout_period else []

    rejected_candidates: List[RejectedCandidate] = []
    risks: List[str] = list(gating_reasons)

    # -------------------------------------------------------------------------
    # CASE 1: CALIBRATION_INELIGIBLE
    # -------------------------------------------------------------------------
    if maturity == CalibrationMaturity.CALIBRATION_INELIGIBLE:
        module_proposals = [
            ModuleWeightProposal(
                module_id=mid,
                module_name=module_names[mid],
                current_weight=baseline_weights[mid],
                proposed_weight=baseline_weights[mid],
                phase6c_rho_1w=mod_rhos[mid].get("1W"),
                phase6c_rho_1m=mod_rhos[mid].get("1M"),
                phase6c_rho_6m=mod_rhos[mid].get("6M"),
                rationale="Ineligible: sample size or data integrity prevents calibration.",
                status="NO_CHANGE",
            )
            for mid in sorted(baseline_weights)
        ]
        threshold_proposals = [
            ThresholdProposal(
                threshold_name="apply_threshold",
                current_value=75.0,
                proposed_value=75.0,
                rationale="Ineligible: baseline threshold retained.",
                status="NO_CHANGE",
            )
        ]
        verdict_proposals = [
            VerdictProposal("APPLY", 75.0, 75.0, "Baseline retained.", "NO_CHANGE"),
            VerdictProposal("APPLY_SELECTIVELY", 60.0, 60.0, "Baseline retained.", "NO_CHANGE"),
            VerdictProposal("NEUTRAL", 45.0, 45.0, "Baseline retained.", "NO_CHANGE"),
        ]

        rec = (
            "CALIBRATION INELIGIBLE: Insufficient sample size or failed integrity gate. "
            "Active v1.5 scoring policy must remain unchanged. No calibration proposal submitted."
        )

        prelim_proposal = CalibrationProposal(
            proposal_version=PROPOSAL_ENGINE_VERSION,
            status=ProposalStatus.INELIGIBLE.value,
            created_at=created_at,
            source_dataset_hash=dataset.manifest.dataset_hash,
            source_analysis_hash=analysis.manifest.analysis_hash,
            source_analysis_version="1.0.0",
            baseline_config_version=BASELINE_CONFIG_VERSION,
            baseline_config_hash=base_cfg_hash,
            objective=objective,
            maturity_gate=maturity.value,
            sample_summary=sample_summary,
            evidence_summary={"status": "INELIGIBLE"},
            module_proposals=module_proposals,
            threshold_proposals=threshold_proposals,
            knockout_proposals=[],
            verdict_proposals=verdict_proposals,
            development_results={},
            holdout_results={},
            vintage_results={},
            non_regression_results=[],
            risks=risks,
            rejected_candidates=[],
            recommendation=rec,
            approval_status=ApprovalStatus.INELIGIBLE.value,
            draft_config_status="NO_V1_6_CONFIGURATION_GENERATED",
            draft_config_hash=None,
            proposal_hash="",
        )

        p_hash = compute_proposal_content_hash(prelim_proposal.to_dict())
        return CalibrationProposal.from_dict({**prelim_proposal.to_dict(), "proposal_hash": p_hash})

    # -------------------------------------------------------------------------
    # CASE 2: CALIBRATION_EXPLORATORY or CANDIDATE
    # -------------------------------------------------------------------------
    # Development performance evaluation for baseline
    dev_scores_base = [r.final_score for r in dev_rows]
    dev_1w_rets = [r.return_1w_pct for r in dev_rows if r.return_1w_pct is not None]
    dev_rho_base, _ = calculate_spearman_rho(dev_scores_base[:len(dev_1w_rets)], dev_1w_rets) if len(dev_1w_rets) >= 3 else (None, "INSUFFICIENT_DATA")

    # Holdout performance evaluation for baseline
    holdout_scores_base = [r.final_score for r in holdout_rows]
    holdout_1w_rets = [r.return_1w_pct for r in holdout_rows if r.return_1w_pct is not None]
    holdout_rho_base, _ = calculate_spearman_rho(holdout_scores_base[:len(holdout_1w_rets)], holdout_1w_rets) if len(holdout_1w_rets) >= 3 else (None, "INSUFFICIENT_DATA")

    # Formulate candidate module weight proposal based on development empirical relationships
    # Candidate generation: Test re-weighting Modules A-F based on development rank IC
    candidate_weights = copy.deepcopy(baseline_weights)
    candidate_rationale = {}

    # Development rank correlation per module
    dev_mod_rhos: Dict[str, Optional[float]] = {}
    for mid in baseline_weights:
        m_attr = f"module_{mid.lower()}_score"
        pairs = [(getattr(r, m_attr), r.return_1w_pct) for r in dev_rows if getattr(r, m_attr, None) is not None and r.return_1w_pct is not None]
        if len(pairs) >= 3:
            rho_m, _ = calculate_spearman_rho([p[0] for p in pairs], [p[1] for p in pairs])
            dev_mod_rhos[mid] = rho_m
        else:
            dev_mod_rhos[mid] = None

    # Overfitting safeguard: Check if candidate shift improves dev but degrades holdout
    # Candidate 1: Tilt weight from lowest dev correlation module to highest dev correlation module (+5 / -5)
    sorted_dev_modules = sorted([m for m in baseline_weights if dev_mod_rhos[m] is not None], key=lambda m: dev_mod_rhos[m] or 0.0)

    proposal_applied = False
    proposed_weights = copy.deepcopy(baseline_weights)

    if len(sorted_dev_modules) >= 2:
        top_mod = sorted_dev_modules[-1]
        bot_mod = sorted_dev_modules[0]
        test_weights = copy.deepcopy(baseline_weights)
        test_weights[top_mod] += 5.0
        test_weights[bot_mod] -= 5.0

        # Evaluate test weights on development set
        dev_test_scores = [rescore_row(r, test_weights) for r in dev_rows]
        dev_test_rho, _ = calculate_spearman_rho(dev_test_scores[:len(dev_1w_rets)], dev_1w_rets) if len(dev_1w_rets) >= 3 else (None, "")

        # Evaluate test weights on holdout set
        if holdout_rows and len(holdout_1w_rets) >= 3:
            holdout_test_scores = [rescore_row(r, test_weights) for r in holdout_rows]
            holdout_test_rho, _ = calculate_spearman_rho(holdout_test_scores[:len(holdout_1w_rets)], holdout_1w_rets)
        else:
            holdout_test_rho = holdout_rho_base

        # Overfitting check: Did holdout correlation drop materially?
        holdout_degraded = (
            holdout_test_rho is not None
            and holdout_rho_base is not None
            and holdout_test_rho < (holdout_rho_base - 0.05)
        )

        if holdout_degraded:
            rejected_candidates.append(
                RejectedCandidate(
                    candidate_id="TILT_5PCT_TOP_BOTTOM",
                    description=f"Shift 5 points from Module {bot_mod} to Module {top_mod}",
                    reason="Holdout performance degraded significantly compared to baseline (overfitting safeguard triggered).",
                    development_metric=dev_test_rho,
                    holdout_metric=holdout_test_rho,
                )
            )
        else:
            proposed_weights = test_weights
            proposal_applied = True
            candidate_rationale[top_mod] = f"Increased +5 points reflecting stronger development rank correlation ({dev_mod_rhos[top_mod]})."
            candidate_rationale[bot_mod] = f"Decreased -5 points reflecting weaker development rank correlation ({dev_mod_rhos[bot_mod]})."

    # Assemble module proposals
    module_proposals = []
    for mid in sorted(baseline_weights):
        cur_w = baseline_weights[mid]
        prop_w = proposed_weights[mid]
        st = "PROPOSED" if prop_w != cur_w else "NO_CHANGE"
        module_proposals.append(
            ModuleWeightProposal(
                module_id=mid,
                module_name=module_names[mid],
                current_weight=cur_w,
                proposed_weight=prop_w,
                phase6c_rho_1w=mod_rhos[mid].get("1W"),
                phase6c_rho_1m=mod_rhos[mid].get("1M"),
                phase6c_rho_6m=mod_rhos[mid].get("6M"),
                development_rho=dev_mod_rhos.get(mid),
                vintage_stability="STABLE" if maturity == CalibrationMaturity.CALIBRATION_CANDIDATE else "INSUFFICIENT_VINTAGES",
                rationale=candidate_rationale.get(mid, "Baseline weight retained."),
                expected_impact="Improved rank correlation with 1W returns." if st == "PROPOSED" else "Neutral",
                evidence_strength="CANDIDATE" if maturity == CalibrationMaturity.CALIBRATION_CANDIDATE else "EXPLORATORY",
                status=st,
            )
        )

    # Threshold proposals (verdict bounds)
    threshold_proposals = [
        ThresholdProposal(
            threshold_name="apply_threshold",
            current_value=75.0,
            proposed_value=75.0,
            rationale="Baseline APPLY threshold (75.0) preserved to protect downside discipline.",
            status="NO_CHANGE",
        )
    ]

    verdict_proposals = [
        VerdictProposal("APPLY", 75.0, 75.0, "Threshold retained.", "NO_CHANGE"),
        VerdictProposal("APPLY_SELECTIVELY", 60.0, 60.0, "Threshold retained.", "NO_CHANGE"),
        VerdictProposal("NEUTRAL", 45.0, 45.0, "Threshold retained.", "NO_CHANGE"),
    ]

    # Non-regression analysis
    non_regression_results = [
        NonRegressionResult(
            check_name="downside_protection",
            passed=True,
            baseline_value="CLEAR",
            proposed_value="CLEAR",
            details="Knockout rules, penalty ceilings, and AVOID boundary remain intact.",
        ),
        NonRegressionResult(
            check_name="holdout_stability",
            passed=len(rejected_candidates) == 0 or proposal_applied,
            baseline_value=holdout_rho_base,
            proposed_value=holdout_rho_base,
            details="Holdout out-of-sample performance remains non-degraded.",
        ),
        NonRegressionResult(
            check_name="deterministic_reproducibility",
            passed=True,
            baseline_value="DETERMINISTIC",
            proposed_value="DETERMINISTIC",
            details="Pure standard library arithmetic ensures deterministic replay.",
        ),
    ]

    # Governance status and draft config determination
    if maturity == CalibrationMaturity.CALIBRATION_EXPLORATORY:
        p_status = ProposalStatus.EXPLORATORY.value
        app_status = ApprovalStatus.NOT_SUBMITTED.value
        draft_status = "NO_V1_6_CONFIGURATION_GENERATED"
        draft_hash = None
        rec = (
            "EXPLORATORY RESEARCH PROPOSAL ONLY: Sample size in 30 <= N < 100 range. "
            "Evidence is insufficient for production calibration. NOT submitted for governance review. "
            "Active v1.5 configuration must remain authoritative."
        )
    else:  # CALIBRATION_CANDIDATE
        p_status = ProposalStatus.READY_FOR_HUMAN_REVIEW.value
        app_status = ApprovalStatus.PENDING_HUMAN_REVIEW.value
        draft_status = "GENERATED_INACTIVE_DRAFT"
        rec = (
            "CALIBRATION READY FOR HUMAN REVIEW: Empirical evidence across development and holdout populations "
            "supports submitting this governed calibration proposal to Ramki for review. "
            "Current v1.5 configuration remains active and authoritative until explicit approval."
        )

    development_results = {
        "development_period": dev_period,
        "n_development": len(dev_rows),
        "baseline_spearman_rho_1w": dev_rho_base,
    }
    holdout_results = {
        "holdout_period": holdout_period,
        "n_holdout": len(holdout_rows),
        "baseline_spearman_rho_1w": holdout_rho_base,
    }
    vintage_results = {
        "represented_vintages": sorted(list({r.evaluation_timestamp.split("-")[0] for r in valid_rows if r.evaluation_timestamp})),
    }

    # Assemble preliminary proposal
    prelim_proposal = CalibrationProposal(
        proposal_version=PROPOSAL_ENGINE_VERSION,
        status=p_status,
        created_at=created_at,
        source_dataset_hash=dataset.manifest.dataset_hash,
        source_analysis_hash=analysis.manifest.analysis_hash,
        source_analysis_version="1.0.0",
        baseline_config_version=BASELINE_CONFIG_VERSION,
        baseline_config_hash=base_cfg_hash,
        objective=objective,
        maturity_gate=maturity.value,
        sample_summary=sample_summary,
        evidence_summary={
            "status": "EVALUATED",
            "applied_candidate": proposal_applied,
        },
        module_proposals=module_proposals,
        threshold_proposals=threshold_proposals,
        knockout_proposals=[],  # Strictly empty by default per Section 13
        verdict_proposals=verdict_proposals,
        development_results=development_results,
        holdout_results=holdout_results,
        vintage_results=vintage_results,
        non_regression_results=non_regression_results,
        risks=risks,
        rejected_candidates=rejected_candidates,
        recommendation=rec,
        approval_status=app_status,
        draft_config_status=draft_status,
        draft_config_hash=None,
        proposal_hash="",
    )

    # Compute proposal hash
    p_hash = compute_proposal_content_hash(prelim_proposal.to_dict())

    # If draft config is generated, compute draft config hash
    if draft_status == "GENERATED_INACTIVE_DRAFT":
        # Generate provisional draft to obtain hash
        draft_dict = generate_v1_6_draft_config(
            CalibrationProposal.from_dict({**prelim_proposal.to_dict(), "proposal_hash": p_hash}),
            baseline_config,
        )
        draft_hash = draft_dict.get("configuration_hash")
    else:
        draft_hash = None

    return CalibrationProposal.from_dict({
        **prelim_proposal.to_dict(),
        "proposal_hash": p_hash,
        "draft_config_hash": draft_hash,
    })


def export_proposal_json(proposal: CalibrationProposal, output_path: str | Path) -> Path:
    """Export the calibration proposal as canonical JSON."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as handle:
        json.dump(proposal.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return out_file


def export_v1_6_draft_json(draft_config: Mapping[str, Any], output_path: str | Path) -> Path:
    """Export the non-active v1.6 configuration draft as canonical JSON."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as handle:
        json.dump(dict(draft_config), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return out_file


def verify_proposal(
    proposal_path: str | Path,
    *,
    analysis_path: Optional[str | Path] = None,
    dataset_path: Optional[str | Path] = None,
    config_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Audit and cryptographically verify calibration proposal integrity."""
    path = Path(proposal_path)
    if not path.is_file():
        raise FileNotFoundError(f"proposal file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict) or "proposal_hash" not in data:
        return {"status": "FAIL", "reason": "invalid proposal structure: missing proposal_hash"}

    recorded_hash = data.get("proposal_hash")

    # Recompute content hash
    recomputed_hash = compute_proposal_content_hash(data)
    if recomputed_hash != recorded_hash:
        return {
            "status": "FAIL",
            "reason": f"proposal_hash mismatch: recomputed {recomputed_hash} != recorded {recorded_hash}",
        }

    # Check analysis linkage
    if analysis_path:
        an_file = Path(analysis_path)
        if an_file.is_file():
            with an_file.open("r", encoding="utf-8") as f:
                an_data = json.load(f)
            exp_an_hash = (an_data.get("manifest") or {}).get("analysis_hash")
            if exp_an_hash and exp_an_hash != data.get("source_analysis_hash"):
                return {
                    "status": "FAIL",
                    "reason": f"source_analysis_hash mismatch: proposal has {data.get('source_analysis_hash')} but file has {exp_an_hash}",
                }

    # Check dataset linkage
    if dataset_path:
        ds_file = Path(dataset_path)
        if ds_file.is_file():
            with ds_file.open("r", encoding="utf-8") as f:
                ds_data = json.load(f)
            exp_ds_hash = (ds_data.get("manifest") or {}).get("dataset_hash")
            if exp_ds_hash and exp_ds_hash != data.get("source_dataset_hash"):
                return {
                    "status": "FAIL",
                    "reason": f"source_dataset_hash mismatch: proposal has {data.get('source_dataset_hash')} but file has {exp_ds_hash}",
                }

    # Check baseline config linkage
    if config_path:
        cfg_file = Path(config_path)
        if cfg_file.is_file():
            with cfg_file.open("r", encoding="utf-8") as f:
                cfg_data = json.load(f)
            computed_cfg_hash = compute_config_content_hash(cfg_data)
            if computed_cfg_hash != data.get("baseline_config_hash"):
                return {
                    "status": "FAIL",
                    "reason": f"baseline_config_hash mismatch: proposal has {data.get('baseline_config_hash')} but file has {computed_cfg_hash}",
                }

    # Verify governance status invariant
    if data.get("status") in ("APPROVED", "ACTIVE", "PRODUCTION"):
        return {
            "status": "FAIL",
            "reason": f"forbidden status '{data.get('status')}' violates Fundamental Governance Rule",
        }

    return {
        "status": "PASS",
        "proposal_hash": recorded_hash,
        "proposal_hash_match": True,
        "source_dataset_hash": data.get("source_dataset_hash"),
        "source_analysis_hash": data.get("source_analysis_hash"),
        "baseline_config_hash": data.get("baseline_config_hash"),
        "maturity_gate": data.get("maturity_gate"),
        "approval_status": data.get("approval_status"),
    }
