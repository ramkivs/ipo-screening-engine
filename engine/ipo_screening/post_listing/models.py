"""Phase 6A: Post-listing observation data models.

Defines the immutable data structures for recording realized post-listing outcomes,
price observations, benchmark returns, and calculation provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Horizon(str, Enum):
    """Observation horizons for post-listing performance."""
    W1 = "1W"
    M1 = "1M"
    M6 = "6M"


class ObservationStatus(str, Enum):
    """Status of a post-listing observation."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    INCOMPLETE = "INCOMPLETE"
    SUSPENDED = "SUSPENDED"
    REFUSED = "REFUSED"


class VerificationStatus(str, Enum):
    """Verification status for corporate actions and price sources."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    UNADJUSTED = "UNADJUSTED"


@dataclass(frozen=True)
class PriceObservation:
    """Observed price metrics for an IPO at a specific horizon."""
    issue_price: float
    listing_open: Optional[float] = None
    listing_close: Optional[float] = None
    raw_observed_close: Optional[float] = None
    corporate_action_factor: float = 1.0
    adjusted_observed_close: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_price": self.issue_price,
            "listing_open": self.listing_open,
            "listing_close": self.listing_close,
            "raw_observed_close": self.raw_observed_close,
            "corporate_action_factor": self.corporate_action_factor,
            "adjusted_observed_close": self.adjusted_observed_close,
        }


@dataclass(frozen=True)
class BenchmarkObservation:
    """Observed benchmark values and returns."""
    symbol: str
    raw_listing_value: Optional[float] = None
    raw_observed_value: Optional[float] = None
    adjusted_listing_value: Optional[float] = None
    adjusted_observed_value: Optional[float] = None
    return_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "raw_listing_value": self.raw_listing_value,
            "raw_observed_value": self.raw_observed_value,
            "adjusted_listing_value": self.adjusted_listing_value,
            "adjusted_observed_value": self.adjusted_observed_value,
            "return_pct": self.return_pct,
        }


@dataclass(frozen=True)
class ReturnSet:
    """Calculated percentage returns for an observation."""
    listing_gain_pct: Optional[float] = None
    absolute_return_pct: Optional[float] = None
    secondary_return_pct: Optional[float] = None
    benchmark_return_pct: Optional[float] = None
    excess_return_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing_gain_pct": self.listing_gain_pct,
            "absolute_return_pct": self.absolute_return_pct,
            "secondary_return_pct": self.secondary_return_pct,
            "benchmark_return_pct": self.benchmark_return_pct,
            "excess_return_pct": self.excess_return_pct,
        }


@dataclass(frozen=True)
class ProvenanceRecord:
    """Source provenance and audit metadata for price observations."""
    source_id: str
    source_type: str
    source_uri_or_file: str
    retrieval_timestamp: str
    content_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "source_uri_or_file": self.source_uri_or_file,
            "retrieval_timestamp": self.retrieval_timestamp,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True)
class CalculationMetadata:
    """Deterministic calculation metadata."""
    calculation_version: str = "1.0.0"
    calculation_inputs_hash: str = ""
    observation_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calculation_version": self.calculation_version,
            "calculation_inputs_hash": self.calculation_inputs_hash,
            "observation_hash": self.observation_hash,
        }


@dataclass(frozen=True)
class PostListingObservation:
    """An immutable, linked post-listing observation artifact."""
    observation_id: str
    final_evaluation_id: str
    final_result_hash: str
    ipo_id: str
    horizon: str  # "1W", "1M", "6M"
    listing_date: str  # YYYY-MM-DD
    target_observation_date: str  # YYYY-MM-DD
    actual_observation_date: str  # YYYY-MM-DD
    prices: PriceObservation
    benchmark: BenchmarkObservation
    returns: ReturnSet
    provenance: ProvenanceRecord
    calculation: CalculationMetadata
    observation_status: str = ObservationStatus.VERIFIED.value
    verification_status: str = VerificationStatus.VERIFIED.value
    version: int = 1
    supersedes_observation_id: Optional[str] = None
    restatement_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "observation_id": self.observation_id,
            "final_evaluation_id": self.final_evaluation_id,
            "final_result_hash": self.final_result_hash,
            "ipo_id": self.ipo_id,
            "horizon": self.horizon,
            "listing_date": self.listing_date,
            "target_observation_date": self.target_observation_date,
            "actual_observation_date": self.actual_observation_date,
            "prices": self.prices.to_dict(),
            "benchmark": self.benchmark.to_dict(),
            "returns": self.returns.to_dict(),
            "provenance": self.provenance.to_dict(),
            "calculation": self.calculation.to_dict(),
            "observation_status": self.observation_status,
            "verification_status": self.verification_status,
            "version": self.version,
        }
        if self.supersedes_observation_id:
            out["supersedes_observation_id"] = self.supersedes_observation_id
        if self.restatement_reason:
            out["restatement_reason"] = self.restatement_reason
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PostListingObservation:
        prices_dict = data.get("prices", {})
        benchmark_dict = data.get("benchmark", {})
        returns_dict = data.get("returns", {})
        provenance_dict = data.get("provenance", {})
        calc_dict = data.get("calculation", {})

        return cls(
            observation_id=data["observation_id"],
            final_evaluation_id=data["final_evaluation_id"],
            final_result_hash=data["final_result_hash"],
            ipo_id=data["ipo_id"],
            horizon=data["horizon"],
            listing_date=data["listing_date"],
            target_observation_date=data["target_observation_date"],
            actual_observation_date=data["actual_observation_date"],
            prices=PriceObservation(
                issue_price=float(prices_dict.get("issue_price", 0.0)),
                listing_open=_opt_float(prices_dict.get("listing_open")),
                listing_close=_opt_float(prices_dict.get("listing_close")),
                raw_observed_close=_opt_float(prices_dict.get("raw_observed_close")),
                corporate_action_factor=float(prices_dict.get("corporate_action_factor", 1.0)),
                adjusted_observed_close=_opt_float(prices_dict.get("adjusted_observed_close")),
            ),
            benchmark=BenchmarkObservation(
                symbol=benchmark_dict.get("symbol", "NIFTY_50_TRI"),
                raw_listing_value=_opt_float(benchmark_dict.get("raw_listing_value")),
                raw_observed_value=_opt_float(benchmark_dict.get("raw_observed_value")),
                adjusted_listing_value=_opt_float(benchmark_dict.get("adjusted_listing_value")),
                adjusted_observed_value=_opt_float(benchmark_dict.get("adjusted_observed_value")),
                return_pct=_opt_float(benchmark_dict.get("return_pct")),
            ),
            returns=ReturnSet(
                listing_gain_pct=_opt_float(returns_dict.get("listing_gain_pct")),
                absolute_return_pct=_opt_float(returns_dict.get("absolute_return_pct")),
                secondary_return_pct=_opt_float(returns_dict.get("secondary_return_pct")),
                benchmark_return_pct=_opt_float(returns_dict.get("benchmark_return_pct")),
                excess_return_pct=_opt_float(returns_dict.get("excess_return_pct")),
            ),
            provenance=ProvenanceRecord(
                source_id=provenance_dict.get("source_id", ""),
                source_type=provenance_dict.get("source_type", ""),
                source_uri_or_file=provenance_dict.get("source_uri_or_file", ""),
                retrieval_timestamp=provenance_dict.get("retrieval_timestamp", ""),
                content_hash=provenance_dict.get("content_hash", ""),
            ),
            calculation=CalculationMetadata(
                calculation_version=calc_dict.get("calculation_version", "1.0.0"),
                calculation_inputs_hash=calc_dict.get("calculation_inputs_hash", ""),
                observation_hash=calc_dict.get("observation_hash", ""),
            ),
            observation_status=data.get("observation_status", ObservationStatus.VERIFIED.value),
            verification_status=data.get("verification_status", VerificationStatus.VERIFIED.value),
            version=int(data.get("version", 1)),
            supersedes_observation_id=data.get("supersedes_observation_id"),
            restatement_reason=data.get("restatement_reason"),
        )


def _opt_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
