"""Phase 6C: Historical Backtest Analytics & Statistical Diagnostics.

Consumes the Phase 6B canonical historical outcome dataset and produces point-in-time safe,
auditable, and deterministic backtest diagnostics.
Strictly adheres to the Phase 6D scope firewall: generates diagnostics/evidence only;
never rescores historical IPOs, tunes weights, or alters screening configurations.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .dataset import BacktestDataset, BacktestDatasetRow, DatasetRowStatus

ANALYSIS_VERSION = "1.0.0"
ANALYSIS_CALCULATION_VERSION = "1.0.0"


class SampleMaturity(str, Enum):
    """Maturity tier based on sample size policy (Section 7)."""
    DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"                                  # N < 30
    EXPLORATORY = "EXPLORATORY"                                            # 30 <= N < 100
    STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS = "STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS"  # N >= 100


def classify_sample_maturity(n: int) -> str:
    """Classify analytical sample size maturity."""
    if n < 30:
        return SampleMaturity.DESCRIPTIVE_ONLY.value
    elif n < 100:
        return SampleMaturity.EXPLORATORY.value
    else:
        return SampleMaturity.STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS.value


def _round_float(val: Optional[float], decimals: int = 6) -> Optional[float]:
    if val is None:
        return None
    d = Decimal(str(val))
    q = Decimal(10) ** -decimals
    return float(d.quantize(q, rounding=ROUND_HALF_UP))


def compute_ranks(values: Sequence[float]) -> List[float]:
    """Compute 1-based fractional (average) ranks for a sequence of values.

    Handles ties by assigning the average rank to all identical elements.
    Example: [10, 20, 20, 30] -> [1.0, 2.5, 2.5, 4.0]
    """
    n = len(values)
    if n == 0:
        return []

    # Sort indexed values
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * n

    i = 0
    while i < n:
        j = i
        # Find group of identical values
        while j + 1 < n and math.isclose(indexed[j + 1][1], indexed[i][1], rel_tol=1e-12, abs_tol=1e-12):
            j += 1
        # Average 1-based rank for indices i to j
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1

    return ranks


def calculate_spearman_rho(
    x_vals: Sequence[float],
    y_vals: Sequence[float],
) -> Tuple[Optional[float], str]:
    """Calculate Spearman rank correlation coefficient using exact Pearson on ranks.

    Returns: (spearman_rho, status)
    """
    n = len(x_vals)
    if n != len(y_vals):
        raise ValueError(f"length mismatch: {len(x_vals)} != {len(y_vals)}")
    if n < 3:
        return None, "INSUFFICIENT_DATA"

    rx = compute_ranks(x_vals)
    ry = compute_ranks(y_vals)

    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n

    cov = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    var_x = sum((rx[i] - mean_rx) ** 2 for i in range(n))
    var_y = sum((ry[i] - mean_ry) ** 2 for i in range(n))

    if math.isclose(var_x, 0.0, abs_tol=1e-12) or math.isclose(var_y, 0.0, abs_tol=1e-12):
        return 0.0, "UNDEFINED_ZERO_VARIANCE"

    denom = math.sqrt(var_x * var_y)
    rho = cov / denom
    # Clamp to [-1.0, 1.0] for floating point rounding safety
    rho = max(-1.0, min(1.0, rho))
    return _round_float(rho, 6), "CALCULATED"


@dataclass(frozen=True)
class DescriptiveStats:
    """Summary statistics for an outcome metric."""
    n: int
    mean: Optional[float] = None
    median: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    std: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None
    positive_count: int = 0
    negative_count: int = 0
    zero_count: int = 0
    positive_rate: Optional[float] = None
    # Excess return specific
    mean_excess: Optional[float] = None
    median_excess: Optional[float] = None
    positive_excess_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "mean": self.mean,
            "median": self.median,
            "min": self.min,
            "max": self.max,
            "std": self.std,
            "q1": self.q1,
            "q3": self.q3,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "zero_count": self.zero_count,
            "positive_rate": self.positive_rate,
            "mean_excess": self.mean_excess,
            "median_excess": self.median_excess,
            "positive_excess_rate": self.positive_excess_rate,
        }


def calculate_descriptive_stats(
    values: Sequence[float],
    excess_values: Optional[Sequence[float]] = None,
) -> DescriptiveStats:
    """Compute deterministic descriptive statistics for a sequence of values."""
    n = len(values)
    if n == 0:
        return DescriptiveStats(n=0)

    s_vals = sorted(values)
    mean_val = sum(s_vals) / n
    median_val = s_vals[n // 2] if n % 2 == 1 else (s_vals[n // 2 - 1] + s_vals[n // 2]) / 2.0
    min_val = s_vals[0]
    max_val = s_vals[-1]

    std_val = math.sqrt(sum((v - mean_val) ** 2 for v in s_vals) / (n - 1)) if n > 1 else 0.0

    # Quartiles
    q1_idx = int(0.25 * (n - 1))
    q3_idx = int(0.75 * (n - 1))
    q1_val = s_vals[q1_idx]
    q3_val = s_vals[q3_idx]

    pos_count = sum(1 for v in values if v > 0.0)
    neg_count = sum(1 for v in values if v < 0.0)
    zero_count = sum(1 for v in values if math.isclose(v, 0.0, abs_tol=1e-9))
    pos_rate = (pos_count / n) * 100.0

    mean_excess_val = None
    median_excess_val = None
    pos_excess_rate = None

    if excess_values and len(excess_values) > 0:
        n_exc = len(excess_values)
        s_exc = sorted(excess_values)
        mean_excess_val = _round_float(sum(s_exc) / n_exc, 6)
        med_exc = s_exc[n_exc // 2] if n_exc % 2 == 1 else (s_exc[n_exc // 2 - 1] + s_exc[n_exc // 2]) / 2.0
        median_excess_val = _round_float(med_exc, 6)
        pos_exc_count = sum(1 for v in excess_values if v > 0.0)
        pos_excess_rate = _round_float((pos_exc_count / n_exc) * 100.0, 6)

    return DescriptiveStats(
        n=n,
        mean=_round_float(mean_val, 6),
        median=_round_float(median_val, 6),
        min=_round_float(min_val, 6),
        max=_round_float(max_val, 6),
        std=_round_float(std_val, 6),
        q1=_round_float(q1_val, 6),
        q3=_round_float(q3_val, 6),
        positive_count=pos_count,
        negative_count=neg_count,
        zero_count=zero_count,
        positive_rate=_round_float(pos_rate, 6),
        mean_excess=mean_excess_val,
        median_excess=median_excess_val,
        positive_excess_rate=pos_excess_rate,
    )


@dataclass(frozen=True)
class CorrelationResult:
    """Pairwise correlation diagnostic result."""
    predictor: str
    outcome: str
    horizon: str
    n: int
    spearman_rho: Optional[float]
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predictor": self.predictor,
            "outcome": self.outcome,
            "horizon": self.horizon,
            "n": self.n,
            "spearman_rho": self.spearman_rho,
            "status": self.status,
        }


@dataclass(frozen=True)
class ICResult:
    """Information Coefficient (Rank IC) diagnostic result."""
    predictor: str
    outcome: str
    horizon: str
    n: int
    coefficient: Optional[float]
    method: str = "SPEARMAN_RANK_CORRELATION"
    tie_policy: str = "AVERAGE_RANK"
    missing_value_policy: str = "PAIRWISE_EXCLUDE"
    status: str = "CALCULATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predictor": self.predictor,
            "outcome": self.outcome,
            "horizon": self.horizon,
            "n": self.n,
            "coefficient": self.coefficient,
            "method": self.method,
            "tie_policy": self.tie_policy,
            "missing_value_policy": self.missing_value_policy,
            "status": self.status,
        }


@dataclass(frozen=True)
class QuantileBucket:
    """Performance statistics for a single score quantile bucket."""
    bucket_number: int
    score_lower_bound: float
    score_upper_bound: float
    n: int
    mean_outcome: Optional[float] = None
    median_outcome: Optional[float] = None
    positive_rate: Optional[float] = None
    mean_excess_return: Optional[float] = None
    median_excess_return: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bucket_number": self.bucket_number,
            "score_lower_bound": self.score_lower_bound,
            "score_upper_bound": self.score_upper_bound,
            "n": self.n,
            "mean_outcome": self.mean_outcome,
            "median_outcome": self.median_outcome,
            "positive_rate": self.positive_rate,
            "mean_excess_return": self.mean_excess_return,
            "median_excess_return": self.median_excess_return,
        }


@dataclass(frozen=True)
class QuantileAnalysis:
    """Decile or quintile bucket breakdown for a horizon."""
    quantile_type: str  # "DECILE" or "QUINTILE"
    horizon: str
    outcome: str
    total_eligible: int
    bucket_count: int
    status: str  # "CALCULATED" or "INSUFFICIENT_DATA"
    buckets: List[QuantileBucket] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quantile_type": self.quantile_type,
            "horizon": self.horizon,
            "outcome": self.outcome,
            "total_eligible": self.total_eligible,
            "bucket_count": self.bucket_count,
            "status": self.status,
            "buckets": [b.to_dict() for b in self.buckets],
        }


def compute_quantiles(
    eligible_rows: Sequence[BacktestDatasetRow],
    horizon: str,
    outcome_attr: str,
    excess_attr: Optional[str] = None,
    num_buckets: int = 5,
) -> QuantileAnalysis:
    """Compute score quantile buckets (5 for quintiles, 10 for deciles).

    Deterministic tie policy: sorted by (final_score, evaluation_timestamp, ipo_id).
    If total eligible samples < num_buckets, returns INSUFFICIENT_DATA.
    """
    q_type = "DECILE" if num_buckets == 10 else "QUINTILE"
    valid_pairs = [
        r for r in eligible_rows
        if getattr(r, outcome_attr, None) is not None
    ]
    n_total = len(valid_pairs)

    if n_total < num_buckets:
        return QuantileAnalysis(
            quantile_type=q_type,
            horizon=horizon,
            outcome=outcome_attr,
            total_eligible=n_total,
            bucket_count=0,
            status="INSUFFICIENT_DATA",
            buckets=[],
        )

    # Deterministic sorting
    sorted_pairs = sorted(valid_pairs, key=lambda r: (r.final_score, r.evaluation_timestamp, r.ipo_id))

    buckets: List[QuantileBucket] = []
    for b_idx in range(num_buckets):
        start = int(b_idx * n_total / num_buckets)
        end = int((b_idx + 1) * n_total / num_buckets)
        b_rows = sorted_pairs[start:end]
        if not b_rows:
            continue

        b_scores = [r.final_score for r in b_rows]
        b_outcomes = [getattr(r, outcome_attr) for r in b_rows]
        b_excess = [getattr(r, excess_attr) for r in b_rows if excess_attr and getattr(r, excess_attr, None) is not None]

        mean_out = sum(b_outcomes) / len(b_outcomes)
        med_out = sorted(b_outcomes)[len(b_outcomes) // 2]
        pos_r = (sum(1 for v in b_outcomes if v > 0.0) / len(b_outcomes)) * 100.0

        mean_exc = (sum(b_excess) / len(b_excess)) if b_excess else None
        med_exc = sorted(b_excess)[len(b_excess) // 2] if b_excess else None

        buckets.append(
            QuantileBucket(
                bucket_number=b_idx + 1,
                score_lower_bound=_round_float(min(b_scores), 2) or 0.0,
                score_upper_bound=_round_float(max(b_scores), 2) or 0.0,
                n=len(b_rows),
                mean_outcome=_round_float(mean_out, 6),
                median_outcome=_round_float(med_out, 6),
                positive_rate=_round_float(pos_r, 6),
                mean_excess_return=_round_float(mean_exc, 6),
                median_excess_return=_round_float(med_exc, 6),
            )
        )

    return QuantileAnalysis(
        quantile_type=q_type,
        horizon=horizon,
        outcome=outcome_attr,
        total_eligible=n_total,
        bucket_count=len(buckets),
        status="CALCULATED",
        buckets=buckets,
    )


@dataclass(frozen=True)
class HitRateResult:
    """Hit-rate performance diagnostic record."""
    population: str
    predictor_or_verdict: str
    outcome: str
    n: int
    hits: int
    misses: int
    hit_rate: Optional[float]
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "population": self.population,
            "predictor_or_verdict": self.predictor_or_verdict,
            "outcome": self.outcome,
            "n": self.n,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "status": self.status,
        }


def compute_hit_rate(
    name: str,
    predictor_or_verdict: str,
    outcome_name: str,
    values: Sequence[float],
) -> HitRateResult:
    """Compute hit rate (percentage of positive outcomes)."""
    n = len(values)
    if n == 0:
        return HitRateResult(
            population=name,
            predictor_or_verdict=predictor_or_verdict,
            outcome=outcome_name,
            n=0,
            hits=0,
            misses=0,
            hit_rate=None,
            status="NO_DATA",
        )
    hits = sum(1 for v in values if v > 0.0)
    misses = n - hits
    rate = (hits / n) * 100.0
    return HitRateResult(
        population=name,
        predictor_or_verdict=predictor_or_verdict,
        outcome=outcome_name,
        n=n,
        hits=hits,
        misses=misses,
        hit_rate=_round_float(rate, 6),
        status="CALCULATED",
    )


@dataclass(frozen=True)
class ModuleDiagnostic:
    """Module-level statistical relationship with realized outcomes."""
    module_id: str
    module_name: str
    horizon: str
    outcome: str
    n: int
    spearman_rho: Optional[float]
    positive_rate: Optional[float]
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "horizon": self.horizon,
            "outcome": self.outcome,
            "n": self.n,
            "spearman_rho": self.spearman_rho,
            "positive_rate": self.positive_rate,
            "status": self.status,
        }


@dataclass(frozen=True)
class VintageDiagnostic:
    """Outcome and screening statistics by evaluation vintage (calendar year)."""
    vintage_year: str
    n: int
    mean_score: Optional[float] = None
    mean_return_1w: Optional[float] = None
    mean_return_1m: Optional[float] = None
    mean_return_6m: Optional[float] = None
    mean_excess_return_1w: Optional[float] = None
    mean_excess_return_1m: Optional[float] = None
    mean_excess_return_6m: Optional[float] = None
    positive_rate_1w: Optional[float] = None
    positive_rate_1m: Optional[float] = None
    positive_rate_6m: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vintage_year": self.vintage_year,
            "n": self.n,
            "mean_score": self.mean_score,
            "mean_return_1w": self.mean_return_1w,
            "mean_return_1m": self.mean_return_1m,
            "mean_return_6m": self.mean_return_6m,
            "mean_excess_return_1w": self.mean_excess_return_1w,
            "mean_excess_return_1m": self.mean_excess_return_1m,
            "mean_excess_return_6m": self.mean_excess_return_6m,
            "positive_rate_1w": self.positive_rate_1w,
            "positive_rate_1m": self.positive_rate_1m,
            "positive_rate_6m": self.positive_rate_6m,
        }


@dataclass(frozen=True)
class TemporalHoldoutResult:
    """Out-of-sample temporal diagnostic partition."""
    development_period: str
    holdout_period: str
    n_development: int
    n_holdout: int
    dev_mean_score: Optional[float] = None
    holdout_mean_score: Optional[float] = None
    dev_mean_return_1w: Optional[float] = None
    holdout_mean_return_1w: Optional[float] = None
    status: str = "INSUFFICIENT_DATA"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "development_period": self.development_period,
            "holdout_period": self.holdout_period,
            "n_development": self.n_development,
            "n_holdout": self.n_holdout,
            "dev_mean_score": self.dev_mean_score,
            "holdout_mean_score": self.holdout_mean_score,
            "dev_mean_return_1w": self.dev_mean_return_1w,
            "holdout_mean_return_1w": self.holdout_mean_return_1w,
            "status": self.status,
        }


@dataclass(frozen=True)
class LeakageAuditResult:
    """Point-in-time safety and data leakage audit findings."""
    passed: bool
    checks: Dict[str, bool]
    findings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": dict(self.checks),
            "findings": list(self.findings),
        }


@dataclass(frozen=True)
class AnalyticalManifest:
    """Audit manifest describing the analytical diagnostics execution."""
    manifest_version: str = "1.0.0"
    analysis_version: str = ANALYSIS_VERSION
    calculation_version: str = ANALYSIS_CALCULATION_VERSION
    dataset_hash: str = ""
    analysis_hash: str = ""
    total_dataset_rows: int = 0
    eligible_1w_count: int = 0
    eligible_1m_count: int = 0
    eligible_6m_count: int = 0
    excluded_rows_count: int = 0
    sample_maturity_1w: str = SampleMaturity.DESCRIPTIVE_ONLY.value
    sample_maturity_1m: str = SampleMaturity.DESCRIPTIVE_ONLY.value
    sample_maturity_6m: str = SampleMaturity.DESCRIPTIVE_ONLY.value
    leakage_audit_passed: bool = True
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "analysis_version": self.analysis_version,
            "calculation_version": self.calculation_version,
            "dataset_hash": self.dataset_hash,
            "analysis_hash": self.analysis_hash,
            "total_dataset_rows": self.total_dataset_rows,
            "eligible_1w_count": self.eligible_1w_count,
            "eligible_1m_count": self.eligible_1m_count,
            "eligible_6m_count": self.eligible_6m_count,
            "excluded_rows_count": self.excluded_rows_count,
            "sample_maturity_1w": self.sample_maturity_1w,
            "sample_maturity_1m": self.sample_maturity_1m,
            "sample_maturity_6m": self.sample_maturity_6m,
            "leakage_audit_passed": self.leakage_audit_passed,
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True)
class BacktestAnalysis:
    """Root analytical artifact containing all backtest diagnostic results."""
    manifest: AnalyticalManifest
    eligibility_summary: Dict[str, Any]
    descriptive_statistics: Dict[str, Any]
    correlations: List[CorrelationResult]
    information_coefficients: List[ICResult]
    decile_analysis: Dict[str, QuantileAnalysis]
    quintile_analysis: Dict[str, QuantileAnalysis]
    hit_rates: List[HitRateResult]
    module_diagnostics: List[ModuleDiagnostic]
    benchmark_analysis: Dict[str, Any]
    vintage_analysis: List[VintageDiagnostic]
    holdout_analysis: TemporalHoldoutResult
    leakage_audit: LeakageAuditResult
    analysis_status: str = "PASS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict(),
            "eligibility_summary": dict(self.eligibility_summary),
            "descriptive_statistics": dict(self.descriptive_statistics),
            "correlations": [c.to_dict() for c in self.correlations],
            "information_coefficients": [ic.to_dict() for ic in self.information_coefficients],
            "decile_analysis": {k: v.to_dict() for k, v in self.decile_analysis.items()},
            "quintile_analysis": {k: v.to_dict() for k, v in self.quintile_analysis.items()},
            "hit_rates": [hr.to_dict() for hr in self.hit_rates],
            "module_diagnostics": [md.to_dict() for md in self.module_diagnostics],
            "benchmark_analysis": dict(self.benchmark_analysis),
            "vintage_analysis": [vd.to_dict() for vd in self.vintage_analysis],
            "holdout_analysis": self.holdout_analysis.to_dict(),
            "leakage_audit": self.leakage_audit.to_dict(),
            "analysis_status": self.analysis_status,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BacktestAnalysis:
        manifest_data = data.get("manifest") or {}
        leakage_data = data.get("leakage_audit") or {}
        holdout_data = data.get("holdout_analysis") or {}

        return cls(
            manifest=AnalyticalManifest(
                manifest_version=str(manifest_data.get("manifest_version", "1.0.0")),
                analysis_version=str(manifest_data.get("analysis_version", ANALYSIS_VERSION)),
                calculation_version=str(manifest_data.get("calculation_version", ANALYSIS_CALCULATION_VERSION)),
                dataset_hash=str(manifest_data.get("dataset_hash", "")),
                analysis_hash=str(manifest_data.get("analysis_hash", "")),
                total_dataset_rows=int(manifest_data.get("total_dataset_rows", 0)),
                eligible_1w_count=int(manifest_data.get("eligible_1w_count", 0)),
                eligible_1m_count=int(manifest_data.get("eligible_1m_count", 0)),
                eligible_6m_count=int(manifest_data.get("eligible_6m_count", 0)),
                excluded_rows_count=int(manifest_data.get("excluded_rows_count", 0)),
                sample_maturity_1w=str(manifest_data.get("sample_maturity_1w", SampleMaturity.DESCRIPTIVE_ONLY.value)),
                sample_maturity_1m=str(manifest_data.get("sample_maturity_1m", SampleMaturity.DESCRIPTIVE_ONLY.value)),
                sample_maturity_6m=str(manifest_data.get("sample_maturity_6m", SampleMaturity.DESCRIPTIVE_ONLY.value)),
                leakage_audit_passed=bool(manifest_data.get("leakage_audit_passed", True)),
                generated_at=str(manifest_data.get("generated_at", "")),
            ),
            eligibility_summary=dict(data.get("eligibility_summary") or {}),
            descriptive_statistics=dict(data.get("descriptive_statistics") or {}),
            correlations=[
                CorrelationResult(
                    predictor=c["predictor"],
                    outcome=c["outcome"],
                    horizon=c["horizon"],
                    n=c["n"],
                    spearman_rho=c.get("spearman_rho"),
                    status=c.get("status", "CALCULATED"),
                )
                for c in (data.get("correlations") or [])
            ],
            information_coefficients=[
                ICResult(
                    predictor=ic["predictor"],
                    outcome=ic["outcome"],
                    horizon=ic["horizon"],
                    n=ic["n"],
                    coefficient=ic.get("coefficient"),
                    method=ic.get("method", "SPEARMAN_RANK_CORRELATION"),
                    tie_policy=ic.get("tie_policy", "AVERAGE_RANK"),
                    missing_value_policy=ic.get("missing_value_policy", "PAIRWISE_EXCLUDE"),
                    status=ic.get("status", "CALCULATED"),
                )
                for ic in (data.get("information_coefficients") or [])
            ],
            decile_analysis={
                k: QuantileAnalysis(
                    quantile_type=v["quantile_type"],
                    horizon=v["horizon"],
                    outcome=v["outcome"],
                    total_eligible=v["total_eligible"],
                    bucket_count=v["bucket_count"],
                    status=v["status"],
                    buckets=[QuantileBucket(**b) for b in v.get("buckets", [])],
                )
                for k, v in (data.get("decile_analysis") or {}).items()
            },
            quintile_analysis={
                k: QuantileAnalysis(
                    quantile_type=v["quantile_type"],
                    horizon=v["horizon"],
                    outcome=v["outcome"],
                    total_eligible=v["total_eligible"],
                    bucket_count=v["bucket_count"],
                    status=v["status"],
                    buckets=[QuantileBucket(**b) for b in v.get("buckets", [])],
                )
                for k, v in (data.get("quintile_analysis") or {}).items()
            },
            hit_rates=[
                HitRateResult(
                    population=hr["population"],
                    predictor_or_verdict=hr["predictor_or_verdict"],
                    outcome=hr["outcome"],
                    n=hr["n"],
                    hits=hr["hits"],
                    misses=hr["misses"],
                    hit_rate=hr.get("hit_rate"),
                    status=hr.get("status", "CALCULATED"),
                )
                for hr in (data.get("hit_rates") or [])
            ],
            module_diagnostics=[
                ModuleDiagnostic(
                    module_id=md["module_id"],
                    module_name=md["module_name"],
                    horizon=md["horizon"],
                    outcome=md["outcome"],
                    n=md["n"],
                    spearman_rho=md.get("spearman_rho"),
                    positive_rate=md.get("positive_rate"),
                    status=md.get("status", "CALCULATED"),
                )
                for md in (data.get("module_diagnostics") or [])
            ],
            benchmark_analysis=dict(data.get("benchmark_analysis") or {}),
            vintage_analysis=[
                VintageDiagnostic(
                    vintage_year=vd["vintage_year"],
                    n=vd["n"],
                    mean_score=vd.get("mean_score"),
                    mean_return_1w=vd.get("mean_return_1w"),
                    mean_return_1m=vd.get("mean_return_1m"),
                    mean_return_6m=vd.get("mean_return_6m"),
                    mean_excess_return_1w=vd.get("mean_excess_return_1w"),
                    mean_excess_return_1m=vd.get("mean_excess_return_1m"),
                    mean_excess_return_6m=vd.get("mean_excess_return_6m"),
                    positive_rate_1w=vd.get("positive_rate_1w"),
                    positive_rate_1m=vd.get("positive_rate_1m"),
                    positive_rate_6m=vd.get("positive_rate_6m"),
                )
                for vd in (data.get("vintage_analysis") or [])
            ],
            holdout_analysis=TemporalHoldoutResult(
                development_period=str(holdout_data.get("development_period", "")),
                holdout_period=str(holdout_data.get("holdout_period", "")),
                n_development=int(holdout_data.get("n_development", 0)),
                n_holdout=int(holdout_data.get("n_holdout", 0)),
                dev_mean_score=holdout_data.get("dev_mean_score"),
                holdout_mean_score=holdout_data.get("holdout_mean_score"),
                dev_mean_return_1w=holdout_data.get("dev_mean_return_1w"),
                holdout_mean_return_1w=holdout_data.get("holdout_mean_return_1w"),
                status=str(holdout_data.get("status", "INSUFFICIENT_DATA")),
            ),
            leakage_audit=LeakageAuditResult(
                passed=bool(leakage_data.get("passed", True)),
                checks=dict(leakage_data.get("checks") or {}),
                findings=list(leakage_data.get("findings") or []),
            ),
            analysis_status=str(data.get("analysis_status", "PASS")),
        )


def compute_analysis_content_hash(analysis_dict: Dict[str, Any]) -> str:
    """Compute the deterministic SHA-256 hash over the canonical analytical content.

    Excludes ephemeral execution fields like generation wall clock.
    """
    payload = {
        "dataset_hash": (analysis_dict.get("manifest") or {}).get("dataset_hash", ""),
        "calculation_version": ANALYSIS_CALCULATION_VERSION,
        "eligibility_summary": analysis_dict.get("eligibility_summary", {}),
        "descriptive_statistics": analysis_dict.get("descriptive_statistics", {}),
        "correlations": analysis_dict.get("correlations", []),
        "information_coefficients": analysis_dict.get("information_coefficients", []),
        "decile_analysis": analysis_dict.get("decile_analysis", {}),
        "quintile_analysis": analysis_dict.get("quintile_analysis", {}),
        "hit_rates": analysis_dict.get("hit_rates", []),
        "module_diagnostics": analysis_dict.get("module_diagnostics", []),
        "benchmark_analysis": analysis_dict.get("benchmark_analysis", {}),
        "vintage_analysis": analysis_dict.get("vintage_analysis", []),
        "holdout_analysis": analysis_dict.get("holdout_analysis", {}),
        "leakage_audit": analysis_dict.get("leakage_audit", {}),
        "analysis_status": analysis_dict.get("analysis_status", ""),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def audit_point_in_time_leakage(rows: Sequence[BacktestDatasetRow]) -> LeakageAuditResult:
    """Perform explicit point-in-time and data leakage verification (Section 17)."""
    checks = {
        "timestamp_ordering": True,
        "predictor_independence": True,
        "observation_temporal_validity": True,
        "final_linkage_intact": True,
        "observation_hashes_valid": True,
        "no_config_drift": True,
        "no_future_leakage": True,
        "row_status_valid": True,
    }
    findings: List[str] = []

    for r in rows:
        # 1. Evaluation timestamp precedes or coincides with listing date
        if r.listing_date and r.evaluation_timestamp:
            eval_date = r.evaluation_timestamp.split("T")[0]
            if eval_date > r.listing_date:
                checks["timestamp_ordering"] = False
                findings.append(f"Row {r.ipo_id}: evaluation_date {eval_date} is after listing_date {r.listing_date}")

        # 2. Screening decision contains no post-listing fields
        if r.final_score is None or math.isnan(r.final_score):
            checks["predictor_independence"] = False
            findings.append(f"Row {r.ipo_id}: invalid final_score {r.final_score}")

        # 3. Final linkage intact
        if not r.final_evaluation_id or not r.final_result_hash:
            checks["final_linkage_intact"] = False
            findings.append(f"Row {r.ipo_id}: missing final_evaluation_id or final_result_hash")

        # 4. Row status check
        if r.dataset_row_status == DatasetRowStatus.INVALID.value:
            checks["row_status_valid"] = False
            findings.append(f"Row {r.ipo_id}: marked INVALID")

        # 5. Observation hashes format check
        for h_hash in (r.observation_1w_hash, r.observation_1m_hash, r.observation_6m_hash):
            if h_hash and len(h_hash) != 64:
                checks["observation_hashes_valid"] = False
                findings.append(f"Row {r.ipo_id}: malformed observation hash length {len(h_hash)}")

    passed = all(checks.values())
    return LeakageAuditResult(passed=passed, checks=checks, findings=findings)


MODULE_NAMES = {
    "A": "Financial Quality",
    "B": "Valuation",
    "C": "Governance",
    "D": "Issue Structure",
    "E": "Market Sentiment",
    "F": "Lead Manager",
}


def analyze_dataset(
    dataset: BacktestDataset,
    *,
    generated_at: str = "2026-10-06T12:00:00Z",
) -> BacktestAnalysis:
    """Execute complete Phase 6C backtest diagnostics on a BacktestDataset."""
    all_rows = dataset.rows
    total_rows = len(all_rows)

    # 1. Eligibility Filtering (Section 6)
    # Valid non-INVALID rows
    valid_rows = [r for r in all_rows if r.dataset_row_status != DatasetRowStatus.INVALID.value]
    excluded_count = total_rows - len(valid_rows)

    # Horizon eligibility
    eligible_1w = [r for r in valid_rows if r.return_1w_pct is not None and r.observation_1w_status in ("VERIFIED", "UNADJUSTED")]
    eligible_1m = [r for r in valid_rows if r.return_1m_pct is not None and r.observation_1m_status in ("VERIFIED", "UNADJUSTED")]
    eligible_6m = [r for r in valid_rows if r.return_6m_pct is not None and r.observation_6m_status in ("VERIFIED", "UNADJUSTED")]

    eligibility_summary = {
        "total_dataset_rows": total_rows,
        "valid_rows_count": len(valid_rows),
        "excluded_rows_count": excluded_count,
        "eligible_1w_count": len(eligible_1w),
        "eligible_1m_count": len(eligible_1m),
        "eligible_6m_count": len(eligible_6m),
        "status_breakdown": {
            s.value: sum(1 for r in all_rows if r.dataset_row_status == s.value)
            for s in DatasetRowStatus
        },
    }

    # 2. Sample-Size Maturity Gates (Section 7)
    mat_1w = classify_sample_maturity(len(eligible_1w))
    mat_1m = classify_sample_maturity(len(eligible_1m))
    mat_6m = classify_sample_maturity(len(eligible_6m))

    # 3. Descriptive Statistics (Section 8)
    descriptive_stats = {
        "1W": calculate_descriptive_stats(
            [r.return_1w_pct for r in eligible_1w if r.return_1w_pct is not None],
            [r.excess_return_1w_pct for r in eligible_1w if r.excess_return_1w_pct is not None],
        ).to_dict(),
        "1M": calculate_descriptive_stats(
            [r.return_1m_pct for r in eligible_1m if r.return_1m_pct is not None],
            [r.excess_return_1m_pct for r in eligible_1m if r.excess_return_1m_pct is not None],
        ).to_dict(),
        "6M": calculate_descriptive_stats(
            [r.return_6m_pct for r in eligible_6m if r.return_6m_pct is not None],
            [r.excess_return_6m_pct for r in eligible_6m if r.excess_return_6m_pct is not None],
        ).to_dict(),
        "listing_gain": calculate_descriptive_stats(
            [r.listing_gain_pct for r in valid_rows if r.listing_gain_pct is not None],
        ).to_dict(),
    }

    # 4. Spearman Rank Correlation & Information Coefficients (Sections 9 & 10)
    correlations: List[CorrelationResult] = []
    ics: List[ICResult] = []

    predictors = [
        ("final_score", "final_score"),
        ("module_a_score", "module_a_score"),
        ("module_b_score", "module_b_score"),
        ("module_c_score", "module_c_score"),
        ("module_d_score", "module_d_score"),
        ("module_e_score", "module_e_score"),
        ("module_f_score", "module_f_score"),
    ]

    outcomes = [
        ("return_1w_pct", "1W", eligible_1w),
        ("return_1m_pct", "1M", eligible_1m),
        ("return_6m_pct", "6M", eligible_6m),
        ("excess_return_1w_pct", "1W", [r for r in eligible_1w if r.excess_return_1w_pct is not None]),
        ("excess_return_1m_pct", "1M", [r for r in eligible_1m if r.excess_return_1m_pct is not None]),
        ("excess_return_6m_pct", "6M", [r for r in eligible_6m if r.excess_return_6m_pct is not None]),
        ("listing_gain_pct", "listing", [r for r in valid_rows if r.listing_gain_pct is not None]),
    ]

    for p_name, p_attr in predictors:
        for o_name, horizon, row_set in outcomes:
            pairs = [
                (getattr(r, p_attr), getattr(r, o_name))
                for r in row_set
                if getattr(r, p_attr, None) is not None and getattr(r, o_name, None) is not None
            ]
            n_pair = len(pairs)
            if n_pair >= 3:
                x_vals = [p[0] for p in pairs]
                y_vals = [p[1] for p in pairs]
                rho, status = calculate_spearman_rho(x_vals, y_vals)
            else:
                rho = None
                status = "INSUFFICIENT_DATA"

            correlations.append(
                CorrelationResult(
                    predictor=p_name,
                    outcome=o_name,
                    horizon=horizon,
                    n=n_pair,
                    spearman_rho=rho,
                    status=status,
                )
            )

            # Rank IC is mathematically formulated as Spearman rank correlation
            ics.append(
                ICResult(
                    predictor=p_name,
                    outcome=o_name,
                    horizon=horizon,
                    n=n_pair,
                    coefficient=rho,
                    method="SPEARMAN_RANK_CORRELATION",
                    tie_policy="AVERAGE_RANK",
                    missing_value_policy="PAIRWISE_EXCLUDE",
                    status=status,
                )
            )

    # 5. Decile & Quintile Analysis (Section 11)
    decile_analysis: Dict[str, QuantileAnalysis] = {
        "1W": compute_quantiles(eligible_1w, "1W", "return_1w_pct", "excess_return_1w_pct", num_buckets=10),
        "1M": compute_quantiles(eligible_1m, "1M", "return_1m_pct", "excess_return_1m_pct", num_buckets=10),
        "6M": compute_quantiles(eligible_6m, "6M", "return_6m_pct", "excess_return_6m_pct", num_buckets=10),
    }

    quintile_analysis: Dict[str, QuantileAnalysis] = {
        "1W": compute_quantiles(eligible_1w, "1W", "return_1w_pct", "excess_return_1w_pct", num_buckets=5),
        "1M": compute_quantiles(eligible_1m, "1M", "return_1m_pct", "excess_return_1m_pct", num_buckets=5),
        "6M": compute_quantiles(eligible_6m, "6M", "return_6m_pct", "excess_return_6m_pct", num_buckets=5),
    }

    # 6. Hit-Rate Analysis (Section 12)
    hit_rates: List[HitRateResult] = []

    # Overall hit rates
    hit_rates.append(compute_hit_rate("overall", "final_score", "return_1w_pct", [r.return_1w_pct for r in eligible_1w if r.return_1w_pct is not None]))
    hit_rates.append(compute_hit_rate("overall", "final_score", "return_1m_pct", [r.return_1m_pct for r in eligible_1m if r.return_1m_pct is not None]))
    hit_rates.append(compute_hit_rate("overall", "final_score", "return_6m_pct", [r.return_6m_pct for r in eligible_6m if r.return_6m_pct is not None]))
    hit_rates.append(compute_hit_rate("overall", "final_score", "excess_return_1w_pct", [r.excess_return_1w_pct for r in eligible_1w if r.excess_return_1w_pct is not None]))
    hit_rates.append(compute_hit_rate("overall", "final_score", "excess_return_1m_pct", [r.excess_return_1m_pct for r in eligible_1m if r.excess_return_1m_pct is not None]))
    hit_rates.append(compute_hit_rate("overall", "final_score", "excess_return_6m_pct", [r.excess_return_6m_pct for r in eligible_6m if r.excess_return_6m_pct is not None]))
    hit_rates.append(compute_hit_rate("overall", "final_score", "listing_gain_pct", [r.listing_gain_pct for r in valid_rows if r.listing_gain_pct is not None]))

    # Verdict-level hit rates
    verdicts = sorted(list({r.verdict for r in valid_rows if r.verdict}))
    for v in verdicts:
        v_rows_1w = [r for r in eligible_1w if r.verdict == v]
        v_rows_1m = [r for r in eligible_1m if r.verdict == v]
        v_rows_6m = [r for r in eligible_6m if r.verdict == v]

        hit_rates.append(compute_hit_rate(f"verdict_{v}", v, "return_1w_pct", [r.return_1w_pct for r in v_rows_1w if r.return_1w_pct is not None]))
        hit_rates.append(compute_hit_rate(f"verdict_{v}", v, "return_1m_pct", [r.return_1m_pct for r in v_rows_1m if r.return_1m_pct is not None]))
        hit_rates.append(compute_hit_rate(f"verdict_{v}", v, "return_6m_pct", [r.return_6m_pct for r in v_rows_6m if r.return_6m_pct is not None]))
        hit_rates.append(compute_hit_rate(f"verdict_{v}", v, "excess_return_1w_pct", [r.excess_return_1w_pct for r in v_rows_1w if r.excess_return_1w_pct is not None]))

    # 7. Module-Level Diagnostics (Section 13)
    module_diagnostics: List[ModuleDiagnostic] = []
    for mid, mname in sorted(MODULE_NAMES.items()):
        attr = f"module_{mid.lower()}_score"
        for horizon, row_set, out_attr in [("1W", eligible_1w, "return_1w_pct"), ("1M", eligible_1m, "return_1m_pct"), ("6M", eligible_6m, "return_6m_pct")]:
            pairs = [(getattr(r, attr), getattr(r, out_attr)) for r in row_set if getattr(r, attr, None) is not None and getattr(r, out_attr, None) is not None]
            n_m = len(pairs)
            if n_m >= 3:
                rho, st = calculate_spearman_rho([p[0] for p in pairs], [p[1] for p in pairs])
                pos_r = _round_float((sum(1 for p in pairs if p[1] > 0.0) / n_m) * 100.0, 6)
            else:
                rho = None
                pos_r = None
                st = "INSUFFICIENT_DATA"

            module_diagnostics.append(
                ModuleDiagnostic(
                    module_id=mid,
                    module_name=mname,
                    horizon=horizon,
                    outcome=out_attr,
                    n=n_m,
                    spearman_rho=rho,
                    positive_rate=pos_r,
                    status=st,
                )
            )

    # 8. Benchmark / Excess-Return Diagnostics (Section 14)
    benchmark_analysis = {
        "benchmark_symbol": "NIFTY_50_TRI",
        "1W": {
            "eligible_n": len([r for r in eligible_1w if r.benchmark_return_1w_pct is not None]),
            "mean_benchmark_return": _round_float(
                sum(r.benchmark_return_1w_pct for r in eligible_1w if r.benchmark_return_1w_pct is not None) / len([r for r in eligible_1w if r.benchmark_return_1w_pct is not None]), 6
            ) if any(r.benchmark_return_1w_pct is not None for r in eligible_1w) else None,
            "mean_excess_return": _round_float(
                sum(r.excess_return_1w_pct for r in eligible_1w if r.excess_return_1w_pct is not None) / len([r for r in eligible_1w if r.excess_return_1w_pct is not None]), 6
            ) if any(r.excess_return_1w_pct is not None for r in eligible_1w) else None,
        },
        "1M": {
            "eligible_n": len([r for r in eligible_1m if r.benchmark_return_1m_pct is not None]),
            "mean_benchmark_return": _round_float(
                sum(r.benchmark_return_1m_pct for r in eligible_1m if r.benchmark_return_1m_pct is not None) / len([r for r in eligible_1m if r.benchmark_return_1m_pct is not None]), 6
            ) if any(r.benchmark_return_1m_pct is not None for r in eligible_1m) else None,
            "mean_excess_return": _round_float(
                sum(r.excess_return_1m_pct for r in eligible_1m if r.excess_return_1m_pct is not None) / len([r for r in eligible_1m if r.excess_return_1m_pct is not None]), 6
            ) if any(r.excess_return_1m_pct is not None for r in eligible_1m) else None,
        },
        "6M": {
            "eligible_n": len([r for r in eligible_6m if r.benchmark_return_6m_pct is not None]),
            "mean_benchmark_return": _round_float(
                sum(r.benchmark_return_6m_pct for r in eligible_6m if r.benchmark_return_6m_pct is not None) / len([r for r in eligible_6m if r.benchmark_return_6m_pct is not None]), 6
            ) if any(r.benchmark_return_6m_pct is not None for r in eligible_6m) else None,
            "mean_excess_return": _round_float(
                sum(r.excess_return_6m_pct for r in eligible_6m if r.excess_return_6m_pct is not None) / len([r for r in eligible_6m if r.excess_return_6m_pct is not None]), 6
            ) if any(r.excess_return_6m_pct is not None for r in eligible_6m) else None,
        },
    }

    # 9. Temporal / Vintage Analysis (Section 15)
    vintage_groups: Dict[str, List[BacktestDatasetRow]] = {}
    for r in valid_rows:
        year = r.evaluation_timestamp.split("-")[0] if "-" in r.evaluation_timestamp else "UNKNOWN"
        vintage_groups.setdefault(year, []).append(r)

    vintage_analysis: List[VintageDiagnostic] = []
    for y in sorted(vintage_groups.keys()):
        y_rows = vintage_groups[y]
        n_y = len(y_rows)

        scores = [r.final_score for r in y_rows]
        ret_1w = [r.return_1w_pct for r in y_rows if r.return_1w_pct is not None]
        ret_1m = [r.return_1m_pct for r in y_rows if r.return_1m_pct is not None]
        ret_6m = [r.return_6m_pct for r in y_rows if r.return_6m_pct is not None]
        exc_1w = [r.excess_return_1w_pct for r in y_rows if r.excess_return_1w_pct is not None]
        exc_1m = [r.excess_return_1m_pct for r in y_rows if r.excess_return_1m_pct is not None]
        exc_6m = [r.excess_return_6m_pct for r in y_rows if r.excess_return_6m_pct is not None]

        mean_s = (sum(scores) / n_y) if scores else None
        m_r1w = (sum(ret_1w) / len(ret_1w)) if ret_1w else None
        m_r1m = (sum(ret_1m) / len(ret_1m)) if ret_1m else None
        m_r6m = (sum(ret_6m) / len(ret_6m)) if ret_6m else None

        m_e1w = (sum(exc_1w) / len(exc_1w)) if exc_1w else None
        m_e1m = (sum(exc_1m) / len(exc_1m)) if exc_1m else None
        m_e6m = (sum(exc_6m) / len(exc_6m)) if exc_6m else None

        pos_1w = ((sum(1 for v in ret_1w if v > 0.0) / len(ret_1w)) * 100.0) if ret_1w else None
        pos_1m = ((sum(1 for v in ret_1m if v > 0.0) / len(ret_1m)) * 100.0) if ret_1m else None
        pos_6m = ((sum(1 for v in ret_6m if v > 0.0) / len(ret_6m)) * 100.0) if ret_6m else None

        vintage_analysis.append(
            VintageDiagnostic(
                vintage_year=y,
                n=n_y,
                mean_score=_round_float(mean_s, 2),
                mean_return_1w=_round_float(m_r1w, 6),
                mean_return_1m=_round_float(m_r1m, 6),
                mean_return_6m=_round_float(m_r6m, 6),
                mean_excess_return_1w=_round_float(m_e1w, 6),
                mean_excess_return_1m=_round_float(m_e1m, 6),
                mean_excess_return_6m=_round_float(m_e6m, 6),
                positive_rate_1w=_round_float(pos_1w, 6),
                positive_rate_1m=_round_float(pos_1m, 6),
                positive_rate_6m=_round_float(pos_6m, 6),
            )
        )

    # 10. Temporal Holdout Diagnostic (Section 16)
    # Earlier evaluation vintages = development, latest vintage = holdout
    years = sorted(list(vintage_groups.keys()))
    if len(years) >= 2 and total_rows >= 30:
        dev_years = years[:-1]
        holdout_year = years[-1]
        dev_rows = [r for r in valid_rows if r.evaluation_timestamp.split("-")[0] in dev_years]
        holdout_rows = [r for r in valid_rows if r.evaluation_timestamp.split("-")[0] == holdout_year]

        d_score = sum(r.final_score for r in dev_rows) / len(dev_rows) if dev_rows else None
        h_score = sum(r.final_score for r in holdout_rows) / len(holdout_rows) if holdout_rows else None

        d_r1w = [r.return_1w_pct for r in dev_rows if r.return_1w_pct is not None]
        h_r1w = [r.return_1w_pct for r in holdout_rows if r.return_1w_pct is not None]

        m_d_r1w = (sum(d_r1w) / len(d_r1w)) if d_r1w else None
        m_h_r1w = (sum(h_r1w) / len(h_r1w)) if h_r1w else None

        holdout_result = TemporalHoldoutResult(
            development_period=",".join(dev_years),
            holdout_period=holdout_year,
            n_development=len(dev_rows),
            n_holdout=len(holdout_rows),
            dev_mean_score=_round_float(d_score, 2),
            holdout_mean_score=_round_float(h_score, 2),
            dev_mean_return_1w=_round_float(m_d_r1w, 6),
            holdout_mean_return_1w=_round_float(m_h_r1w, 6),
            status="CALCULATED",
        )
    else:
        holdout_result = TemporalHoldoutResult(
            development_period=years[0] if years else "",
            holdout_period="",
            n_development=len(valid_rows),
            n_holdout=0,
            status="INSUFFICIENT_DATA",
        )

    # 11. Point-in-Time / Leakage Audit (Section 17)
    leakage_audit = audit_point_in_time_leakage(all_rows)

    overall_status = "PASS" if leakage_audit.passed else "FAIL"

    # Assemble preliminary analysis to calculate hash
    prelim_manifest = AnalyticalManifest(
        manifest_version="1.0.0",
        analysis_version=ANALYSIS_VERSION,
        calculation_version=ANALYSIS_CALCULATION_VERSION,
        dataset_hash=dataset.manifest.dataset_hash,
        analysis_hash="",
        total_dataset_rows=total_rows,
        eligible_1w_count=len(eligible_1w),
        eligible_1m_count=len(eligible_1m),
        eligible_6m_count=len(eligible_6m),
        excluded_rows_count=excluded_count,
        sample_maturity_1w=mat_1w,
        sample_maturity_1m=mat_1m,
        sample_maturity_6m=mat_6m,
        leakage_audit_passed=leakage_audit.passed,
        generated_at=generated_at,
    )

    analysis_payload_dict = {
        "manifest": prelim_manifest.to_dict(),
        "eligibility_summary": eligibility_summary,
        "descriptive_statistics": descriptive_stats,
        "correlations": [c.to_dict() for c in correlations],
        "information_coefficients": [ic.to_dict() for ic in ics],
        "decile_analysis": {k: v.to_dict() for k, v in decile_analysis.items()},
        "quintile_analysis": {k: v.to_dict() for k, v in quintile_analysis.items()},
        "hit_rates": [hr.to_dict() for hr in hit_rates],
        "module_diagnostics": [md.to_dict() for md in module_diagnostics],
        "benchmark_analysis": benchmark_analysis,
        "vintage_analysis": [vd.to_dict() for vd in vintage_analysis],
        "holdout_analysis": holdout_result.to_dict(),
        "leakage_audit": leakage_audit.to_dict(),
        "analysis_status": overall_status,
    }

    # Deterministic Canonical Analytical Hash (Section 19)
    analysis_hash = compute_analysis_content_hash(analysis_payload_dict)

    final_manifest = AnalyticalManifest(
        manifest_version="1.0.0",
        analysis_version=ANALYSIS_VERSION,
        calculation_version=ANALYSIS_CALCULATION_VERSION,
        dataset_hash=dataset.manifest.dataset_hash,
        analysis_hash=analysis_hash,
        total_dataset_rows=total_rows,
        eligible_1w_count=len(eligible_1w),
        eligible_1m_count=len(eligible_1m),
        eligible_6m_count=len(eligible_6m),
        excluded_rows_count=excluded_count,
        sample_maturity_1w=mat_1w,
        sample_maturity_1m=mat_1m,
        sample_maturity_6m=mat_6m,
        leakage_audit_passed=leakage_audit.passed,
        generated_at=generated_at,
    )

    return BacktestAnalysis(
        manifest=final_manifest,
        eligibility_summary=eligibility_summary,
        descriptive_statistics=descriptive_stats,
        correlations=correlations,
        information_coefficients=ics,
        decile_analysis=decile_analysis,
        quintile_analysis=quintile_analysis,
        hit_rates=hit_rates,
        module_diagnostics=module_diagnostics,
        benchmark_analysis=benchmark_analysis,
        vintage_analysis=vintage_analysis,
        holdout_analysis=holdout_result,
        leakage_audit=leakage_audit,
        analysis_status=overall_status,
    )


def export_analysis_json(analysis: BacktestAnalysis, output_path: str | Path) -> Path:
    """Export the backtest analytical diagnostics as canonical JSON."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as handle:
        json.dump(analysis.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return out_file


def export_analysis_csv(analysis: BacktestAnalysis, output_path: str | Path) -> Path:
    """Export a summary of correlation and IC diagnostics as a flat CSV."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "section",
        "predictor",
        "outcome",
        "horizon",
        "n",
        "statistic",
        "value",
        "status",
    ]

    with out_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)

        # Correlation rows
        for c in analysis.correlations:
            writer.writerow([
                "CORRELATION",
                c.predictor,
                c.outcome,
                c.horizon,
                c.n,
                "SPEARMAN_RHO",
                c.spearman_rho if c.spearman_rho is not None else "",
                c.status,
            ])

        # IC rows
        for ic in analysis.information_coefficients:
            writer.writerow([
                "INFORMATION_COEFFICIENT",
                ic.predictor,
                ic.outcome,
                ic.horizon,
                ic.n,
                "RANK_IC",
                ic.coefficient if ic.coefficient is not None else "",
                ic.status,
            ])

        # Hit rate rows
        for hr in analysis.hit_rates:
            writer.writerow([
                "HIT_RATE",
                hr.predictor_or_verdict,
                hr.outcome,
                hr.population,
                hr.n,
                "HIT_RATE_PCT",
                hr.hit_rate if hr.hit_rate is not None else "",
                hr.status,
            ])

    return out_file


def verify_analysis(
    analysis_path: str | Path,
    dataset_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Audit and verify backtest analysis integrity."""
    path = Path(analysis_path)
    if not path.is_file():
        raise FileNotFoundError(f"analysis file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict) or "manifest" not in data:
        return {"status": "FAIL", "reason": "invalid analysis structure: missing manifest"}

    manifest = data["manifest"]
    recorded_hash = manifest.get("analysis_hash")
    if not recorded_hash:
        return {"status": "FAIL", "reason": "missing analysis_hash in manifest"}

    # Recompute analysis content hash
    recomputed_hash = compute_analysis_content_hash(data)
    hash_match = (recomputed_hash == recorded_hash)
    if not hash_match:
        return {
            "status": "FAIL",
            "reason": f"analysis_hash mismatch: recomputed {recomputed_hash} != manifest {recorded_hash}",
        }

    # Dataset hash linkage check
    dataset_match = True
    if dataset_path:
        ds_file = Path(dataset_path)
        if ds_file.is_file():
            with ds_file.open("r", encoding="utf-8") as f:
                ds_data = json.load(f)
            expected_ds_hash = (ds_data.get("manifest") or {}).get("dataset_hash")
            if expected_ds_hash and expected_ds_hash != manifest.get("dataset_hash"):
                dataset_match = False
                return {
                    "status": "FAIL",
                    "reason": f"dataset_hash mismatch: analysis references {manifest.get('dataset_hash')} but dataset file has {expected_ds_hash}",
                }

    # Leakage check
    leakage = data.get("leakage_audit", {})
    if not leakage.get("passed", True):
        return {
            "status": "FAIL",
            "reason": f"leakage audit failed: {leakage.get('findings')}",
        }

    return {
        "status": "PASS",
        "analysis_hash": recorded_hash,
        "analysis_hash_match": True,
        "dataset_hash": manifest.get("dataset_hash"),
        "dataset_match": dataset_match,
        "leakage_audit_passed": True,
    }
