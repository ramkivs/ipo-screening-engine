"""Phase 6B: Multi-IPO Historical Outcome Dataset Foundation & Assembly.

Constructs an immutable, point-in-time preserved, deterministic dataset linking
pre-listing screening decisions with realized post-listing outcomes across multiple IPOs.
Enforces strict fail-closed validation, restatement resolution, duplicate detection,
and deterministic cryptographic dataset hashing.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .models import Horizon, ObservationStatus, PostListingObservation, VerificationStatus
from .return_engine import CALCULATION_VERSION, compute_observation_hashes, sha256_canonical_dict
from .storage import (
    get_observations_dir,
    list_observations,
    read_observation,
    validate_parent_evaluation,
    verify_observation_hashes,
)


class DatasetAssemblyError(Exception):
    """Base error for dataset assembly failures."""
    pass


class DuplicateEvaluationError(DatasetAssemblyError):
    """Raised when duplicate evaluations or IPO identities are detected."""
    pass


class ConflictingObservationError(DatasetAssemblyError):
    """Raised when contradictory observation versions or conflicting records exist."""
    pass


class DatasetVerificationError(DatasetAssemblyError):
    """Raised when dataset verification fails audit integrity checks."""
    pass


class DatasetRowStatus(str, Enum):
    """Inclusion and completeness status for a backtest dataset row."""
    READY = "READY"            # All three horizons (1W, 1M, 6M) available and verified
    PARTIAL = "PARTIAL"        # At least one horizon available and verified
    INCOMPLETE = "INCOMPLETE"  # Evaluation present, but zero post-listing horizons available
    UNVERIFIED = "UNVERIFIED"  # Contains unverified corporate actions or unverified data
    INVALID = "INVALID"        # Broken linkage, result hash mismatch, or corrupted hash


@dataclass(frozen=True)
class BacktestDatasetRow:
    """A canonical row in the historical backtest dataset."""
    # Identity
    ipo_id: str
    company_name: str
    final_evaluation_id: str
    evaluation_timestamp: str

    # Pre-listing screening decision (point-in-time preserved)
    final_score: float
    verdict: str
    verdict_band_score: Optional[float] = None
    confidence_level: Optional[str] = None
    completeness_pct: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

    # Module scores
    module_a_score: Optional[float] = None
    module_b_score: Optional[float] = None
    module_c_score: Optional[float] = None
    module_d_score: Optional[float] = None
    module_e_score: Optional[float] = None
    module_f_score: Optional[float] = None

    # Screening state
    knockout_status: Optional[str] = None
    knockout_triggered: List[str] = field(default_factory=list)
    insufficient_data: bool = False
    unknown_points: Optional[float] = None

    # IPO reference inputs
    issue_price: float = 0.0
    listing_date: Optional[str] = None

    # Realized outcomes (fail-closed: None when absent, never zero)
    listing_gain_pct: Optional[float] = None
    return_1w_pct: Optional[float] = None
    return_1m_pct: Optional[float] = None
    return_6m_pct: Optional[float] = None
    benchmark_return_1w_pct: Optional[float] = None
    benchmark_return_1m_pct: Optional[float] = None
    benchmark_return_6m_pct: Optional[float] = None
    excess_return_1w_pct: Optional[float] = None
    excess_return_1m_pct: Optional[float] = None
    excess_return_6m_pct: Optional[float] = None

    # Observation state
    observation_1w_status: Optional[str] = None
    observation_1m_status: Optional[str] = None
    observation_6m_status: Optional[str] = None

    # Dataset row inclusion status
    dataset_row_status: str = DatasetRowStatus.INCOMPLETE.value

    # Provenance and verification
    final_result_hash: str = ""
    observation_1w_hash: Optional[str] = None
    observation_1m_hash: Optional[str] = None
    observation_6m_hash: Optional[str] = None
    calculation_version: str = CALCULATION_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Convert row to a canonical dictionary representation."""
        return {
            "ipo_id": self.ipo_id,
            "company_name": self.company_name,
            "final_evaluation_id": self.final_evaluation_id,
            "evaluation_timestamp": self.evaluation_timestamp,
            "final_score": self.final_score,
            "verdict": self.verdict,
            "verdict_band_score": self.verdict_band_score,
            "confidence_level": self.confidence_level,
            "completeness_pct": self.completeness_pct,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "module_a_score": self.module_a_score,
            "module_b_score": self.module_b_score,
            "module_c_score": self.module_c_score,
            "module_d_score": self.module_d_score,
            "module_e_score": self.module_e_score,
            "module_f_score": self.module_f_score,
            "knockout_status": self.knockout_status,
            "knockout_triggered": list(self.knockout_triggered),
            "insufficient_data": self.insufficient_data,
            "unknown_points": self.unknown_points,
            "issue_price": self.issue_price,
            "listing_date": self.listing_date,
            "listing_gain_pct": self.listing_gain_pct,
            "return_1w_pct": self.return_1w_pct,
            "return_1m_pct": self.return_1m_pct,
            "return_6m_pct": self.return_6m_pct,
            "benchmark_return_1w_pct": self.benchmark_return_1w_pct,
            "benchmark_return_1m_pct": self.benchmark_return_1m_pct,
            "benchmark_return_6m_pct": self.benchmark_return_6m_pct,
            "excess_return_1w_pct": self.excess_return_1w_pct,
            "excess_return_1m_pct": self.excess_return_1m_pct,
            "excess_return_6m_pct": self.excess_return_6m_pct,
            "observation_1w_status": self.observation_1w_status,
            "observation_1m_status": self.observation_1m_status,
            "observation_6m_status": self.observation_6m_status,
            "dataset_row_status": self.dataset_row_status,
            "final_result_hash": self.final_result_hash,
            "observation_1w_hash": self.observation_1w_hash,
            "observation_1m_hash": self.observation_1m_hash,
            "observation_6m_hash": self.observation_6m_hash,
            "calculation_version": self.calculation_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BacktestDatasetRow:
        """Construct BacktestDatasetRow from dictionary representation."""
        return cls(
            ipo_id=str(data["ipo_id"]),
            company_name=str(data.get("company_name", "")),
            final_evaluation_id=str(data["final_evaluation_id"]),
            evaluation_timestamp=str(data["evaluation_timestamp"]),
            final_score=float(data["final_score"]),
            verdict=str(data["verdict"]),
            verdict_band_score=_opt_float(data.get("verdict_band_score")),
            confidence_level=_opt_str(data.get("confidence_level")),
            completeness_pct=_opt_float(data.get("completeness_pct")),
            lower_bound=_opt_float(data.get("lower_bound")),
            upper_bound=_opt_float(data.get("upper_bound")),
            module_a_score=_opt_float(data.get("module_a_score")),
            module_b_score=_opt_float(data.get("module_b_score")),
            module_c_score=_opt_float(data.get("module_c_score")),
            module_d_score=_opt_float(data.get("module_d_score")),
            module_e_score=_opt_float(data.get("module_e_score")),
            module_f_score=_opt_float(data.get("module_f_score")),
            knockout_status=_opt_str(data.get("knockout_status")),
            knockout_triggered=list(data.get("knockout_triggered") or []),
            insufficient_data=bool(data.get("insufficient_data", False)),
            unknown_points=_opt_float(data.get("unknown_points")),
            issue_price=float(data.get("issue_price", 0.0)),
            listing_date=_opt_str(data.get("listing_date")),
            listing_gain_pct=_opt_float(data.get("listing_gain_pct")),
            return_1w_pct=_opt_float(data.get("return_1w_pct")),
            return_1m_pct=_opt_float(data.get("return_1m_pct")),
            return_6m_pct=_opt_float(data.get("return_6m_pct")),
            benchmark_return_1w_pct=_opt_float(data.get("benchmark_return_1w_pct")),
            benchmark_return_1m_pct=_opt_float(data.get("benchmark_return_1m_pct")),
            benchmark_return_6m_pct=_opt_float(data.get("benchmark_return_6m_pct")),
            excess_return_1w_pct=_opt_float(data.get("excess_return_1w_pct")),
            excess_return_1m_pct=_opt_float(data.get("excess_return_1m_pct")),
            excess_return_6m_pct=_opt_float(data.get("excess_return_6m_pct")),
            observation_1w_status=_opt_str(data.get("observation_1w_status")),
            observation_1m_status=_opt_str(data.get("observation_1m_status")),
            observation_6m_status=_opt_str(data.get("observation_6m_status")),
            dataset_row_status=str(data.get("dataset_row_status", DatasetRowStatus.INCOMPLETE.value)),
            final_result_hash=str(data.get("final_result_hash", "")),
            observation_1w_hash=_opt_str(data.get("observation_1w_hash")),
            observation_1m_hash=_opt_str(data.get("observation_1m_hash")),
            observation_6m_hash=_opt_str(data.get("observation_6m_hash")),
            calculation_version=str(data.get("calculation_version", CALCULATION_VERSION)),
        )


@dataclass(frozen=True)
class BacktestDatasetManifest:
    """Audit manifest describing the historical backtest dataset."""
    manifest_version: str = "1.0.0"
    dataset_version: str = "1.0.0"
    calculation_version: str = CALCULATION_VERSION
    generation_timestamp: str = ""
    row_count: int = 0
    included_evaluation_count: int = 0
    included_observation_count: int = 0
    dataset_hash: str = ""
    status_counts: Dict[str, int] = field(default_factory=dict)
    source_hashes: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "dataset_version": self.dataset_version,
            "calculation_version": self.calculation_version,
            "generation_timestamp": self.generation_timestamp,
            "row_count": self.row_count,
            "included_evaluation_count": self.included_evaluation_count,
            "included_observation_count": self.included_observation_count,
            "dataset_hash": self.dataset_hash,
            "status_counts": dict(self.status_counts),
            "source_hashes": dict(self.source_hashes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BacktestDatasetManifest:
        return cls(
            manifest_version=str(data.get("manifest_version", "1.0.0")),
            dataset_version=str(data.get("dataset_version", "1.0.0")),
            calculation_version=str(data.get("calculation_version", CALCULATION_VERSION)),
            generation_timestamp=str(data.get("generation_timestamp", "")),
            row_count=int(data.get("row_count", 0)),
            included_evaluation_count=int(data.get("included_evaluation_count", 0)),
            included_observation_count=int(data.get("included_observation_count", 0)),
            dataset_hash=str(data.get("dataset_hash", "")),
            status_counts=dict(data.get("status_counts") or {}),
            source_hashes=dict(data.get("source_hashes") or {}),
        )


@dataclass(frozen=True)
class BacktestDataset:
    """Full backtest outcome dataset containing audit manifest and sorted canonical rows."""
    manifest: BacktestDatasetManifest
    rows: List[BacktestDatasetRow] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict(),
            "rows": [r.to_dict() for r in self.rows],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BacktestDataset:
        manifest_data = data.get("manifest") or {}
        rows_data = data.get("rows") or []
        manifest = BacktestDatasetManifest.from_dict(manifest_data)
        rows = [BacktestDatasetRow.from_dict(r) for r in rows_data]
        return cls(manifest=manifest, rows=rows)


def compute_dataset_hash(rows: Sequence[BacktestDatasetRow | Mapping[str, Any]]) -> str:
    """Compute the deterministic SHA-256 hash of the canonical dataset rows.

    Independent of filesystem enumeration order and ephemeral generation timestamps.
    """
    row_dicts = [r.to_dict() if isinstance(r, BacktestDatasetRow) else dict(r) for r in rows]
    # Canonical JSON string: sorted keys, separators with no extra whitespace
    canonical_repr = json.dumps(row_dicts, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


def get_effective_observations(
    store_root: str | Path,
    final_evaluation_id: str,
) -> Dict[str, PostListingObservation]:
    """Retrieve effective observations for an evaluation using latest superseding version rule.

    If an observation has been superseded (its observation_id appears in another
    observation's supersedes_observation_id), it remains preserved on disk but is
    not returned as the effective observation.
    Returns: Mapping of horizon ("1W", "1M", "6M") -> effective PostListingObservation.
    """
    all_obs = list_observations(store_root, final_evaluation_id)
    if not all_obs:
        return {}

    superseded_ids: Set[str] = {
        obs.supersedes_observation_id for obs in all_obs if obs.supersedes_observation_id
    }

    # Group candidates by horizon
    by_horizon: Dict[str, List[PostListingObservation]] = {}
    for obs in all_obs:
        if obs.observation_id in superseded_ids:
            continue
        by_horizon.setdefault(obs.horizon.upper(), []).append(obs)

    effective: Dict[str, PostListingObservation] = {}
    for h, candidates in by_horizon.items():
        if len(candidates) > 1:
            # Sort by version descending to select latest superseding observation
            candidates.sort(key=lambda o: o.version, reverse=True)
            # Verify no version conflict among non-superseded candidates
            if candidates[0].version == candidates[1].version:
                raise ConflictingObservationError(
                    f"conflicting unlinked observation versions for evaluation {final_evaluation_id} "
                    f"horizon {h}: version {candidates[0].version} duplicated"
                )
        effective[h] = candidates[0]

    return effective


def assemble_dataset(
    store_root: str | Path,
    *,
    strict: bool = False,
    generation_timestamp: str = "2026-10-06T12:00:00Z",
) -> BacktestDataset:
    """Assemble a multi-IPO historical backtest dataset from stored evaluation directories.

    Enforces:
    - Linkage to FINAL evaluations only
    - Exact result_hash verification
    - Restatement resolution to effective observation versions
    - Duplicate evaluation / duplicate IPO detection
    - Deterministic sorting: evaluation_timestamp, then ipo_id, then final_evaluation_id
    - Canonical dataset hashing
    """
    store_path = Path(store_root)
    if not store_path.is_dir():
        raise FileNotFoundError(f"store directory not found: {store_path}")

    # Discover evaluation directories
    eval_dirs = sorted([d for d in store_path.iterdir() if d.is_dir() and (d / "evaluation.json").is_file()])

    rows: List[BacktestDatasetRow] = []
    seen_eval_ids: Set[str] = set()
    seen_ipo_ids: Set[str] = set()
    total_obs_count = 0
    status_counts: Dict[str, int] = {s.value: 0 for s in DatasetRowStatus}
    source_hashes: Dict[str, Dict[str, Any]] = {}

    for edir in eval_dirs:
        eval_id = edir.name
        eval_file = edir / "evaluation.json"

        with eval_file.open("r", encoding="utf-8") as handle:
            eval_record = json.load(handle)

        mode = str(eval_record.get("evaluation_mode", "")).upper()
        if mode != "FINAL":
            # Skip non-FINAL evaluations (do not error, just ignore preliminary runs in store)
            continue

        if eval_id in seen_eval_ids:
            raise DuplicateEvaluationError(f"duplicate evaluation_id encountered: {eval_id}")
        seen_eval_ids.add(eval_id)

        ipo_id = str(eval_record.get("ipo_id") or eval_id)
        if ipo_id in seen_ipo_ids:
            if strict:
                raise DuplicateEvaluationError(f"duplicate ipo_id encountered in FINAL store: {ipo_id}")
        seen_ipo_ids.add(ipo_id)

        result_hash = str(eval_record.get("result_hash", ""))
        timestamp = str(eval_record.get("evaluation_timestamp", ""))
        company_name = str(eval_record.get("company_name", ipo_id))

        score_block = eval_record.get("score") or {}
        score_range = eval_record.get("score_range") or {}
        verdict_block = eval_record.get("verdict") or {}
        knockout_block = eval_record.get("knockouts") or {}

        # Module scores map
        module_scores: Dict[str, float] = {}
        for m in score_block.get("modules", []):
            mid = str(m.get("module_id", "")).upper()
            if mid and m.get("score") is not None:
                module_scores[mid] = float(m["score"])

        # Input snapshot for issue price and listing date
        input_file = edir / "input.json"
        snapshot: Dict[str, Any] = {}
        if input_file.is_file():
            try:
                with input_file.open("r", encoding="utf-8") as handle:
                    in_data = json.load(handle)
                    snapshot = in_data.get("snapshot", {}).get("input", {}) or in_data.get("input", {})
            except Exception:
                snapshot = {}

        issue = snapshot.get("issue") or {}
        valuation = snapshot.get("valuation") or {}
        company = snapshot.get("company") or {}
        post_input = snapshot.get("post_listing") or {}

        issue_price = float(
            issue.get("issue_price")
            or issue.get("price_band_high")
            or valuation.get("issue_price")
            or 0.0
        )
        listing_date = (
            post_input.get("listing_date")
            or issue.get("listing_date")
            or company.get("listing_date")
        )

        # Retrieve effective observations
        obs_dir = edir / "observations"
        has_invalid = False
        has_unverified = False
        obs_map: Dict[str, PostListingObservation] = {}

        if obs_dir.is_dir():
            # Validate observation hashes
            audit_result = verify_observation_hashes(store_path, eval_id)
            if audit_result.get("status") != "OK":
                has_invalid = True

            try:
                obs_map = get_effective_observations(store_path, eval_id)
            except ConflictingObservationError as e:
                has_invalid = True
                if strict:
                    raise

            total_obs_count += len(obs_map)

        # Extract horizon metrics
        obs_1w = obs_map.get("1W")
        obs_1m = obs_map.get("1M")
        obs_6m = obs_map.get("6M")

        # Check linkage integrity
        for obs in obs_map.values():
            if obs.final_evaluation_id != eval_id or obs.final_result_hash != result_hash:
                has_invalid = True
            if obs.verification_status == VerificationStatus.UNVERIFIED.value:
                has_unverified = True

        # Listing date resolution if not in input snapshot
        if not listing_date:
            for obs in (obs_1w, obs_1m, obs_6m):
                if obs and obs.listing_date:
                    listing_date = obs.listing_date
                    break

        # Listing gain
        listing_gain: Optional[float] = None
        for obs in (obs_1w, obs_1m, obs_6m):
            if obs and obs.returns.listing_gain_pct is not None:
                listing_gain = obs.returns.listing_gain_pct
                break

        # Determine dataset row status
        if has_invalid:
            row_status = DatasetRowStatus.INVALID.value
        elif has_unverified:
            row_status = DatasetRowStatus.UNVERIFIED.value
        elif obs_1w and obs_1m and obs_6m:
            row_status = DatasetRowStatus.READY.value
        elif obs_1w or obs_1m or obs_6m:
            row_status = DatasetRowStatus.PARTIAL.value
        else:
            row_status = DatasetRowStatus.INCOMPLETE.value

        status_counts[row_status] += 1

        # Record source hashes for audit manifest
        source_hashes[eval_id] = {
            "result_hash": result_hash,
            "observations": {
                h: obs.calculation.observation_hash for h, obs in obs_map.items()
            },
        }

        row = BacktestDatasetRow(
            ipo_id=ipo_id,
            company_name=company_name,
            final_evaluation_id=eval_id,
            evaluation_timestamp=timestamp,
            final_score=float(score_block.get("final_score", 0.0)),
            verdict=str(verdict_block.get("verdict", "")),
            verdict_band_score=_opt_float(verdict_block.get("band_score")),
            confidence_level=_opt_str((eval_record.get("confidence") or {}).get("level")),
            completeness_pct=_opt_float(score_block.get("completeness_pct")),
            lower_bound=_opt_float(score_range.get("lower_bound")),
            upper_bound=_opt_float(score_range.get("upper_bound")),
            module_a_score=module_scores.get("A"),
            module_b_score=module_scores.get("B"),
            module_c_score=module_scores.get("C"),
            module_d_score=module_scores.get("D"),
            module_e_score=module_scores.get("E"),
            module_f_score=module_scores.get("F"),
            knockout_status=_opt_str(knockout_block.get("status")),
            knockout_triggered=list(knockout_block.get("triggered") or []),
            insufficient_data=bool(verdict_block.get("insufficient_data", False)),
            unknown_points=_opt_float(score_range.get("unknown_points")),
            issue_price=issue_price,
            listing_date=listing_date,
            listing_gain_pct=listing_gain,
            return_1w_pct=obs_1w.returns.absolute_return_pct if obs_1w else None,
            return_1m_pct=obs_1m.returns.absolute_return_pct if obs_1m else None,
            return_6m_pct=obs_6m.returns.absolute_return_pct if obs_6m else None,
            benchmark_return_1w_pct=obs_1w.benchmark.return_pct if obs_1w else None,
            benchmark_return_1m_pct=obs_1m.benchmark.return_pct if obs_1m else None,
            benchmark_return_6m_pct=obs_6m.benchmark.return_pct if obs_6m else None,
            excess_return_1w_pct=obs_1w.returns.excess_return_pct if obs_1w else None,
            excess_return_1m_pct=obs_1m.returns.excess_return_pct if obs_1m else None,
            excess_return_6m_pct=obs_6m.returns.excess_return_pct if obs_6m else None,
            observation_1w_status=obs_1w.observation_status if obs_1w else None,
            observation_1m_status=obs_1m.observation_status if obs_1m else None,
            observation_6m_status=obs_6m.observation_status if obs_6m else None,
            dataset_row_status=row_status,
            final_result_hash=result_hash,
            observation_1w_hash=obs_1w.calculation.observation_hash if obs_1w else None,
            observation_1m_hash=obs_1m.calculation.observation_hash if obs_1m else None,
            observation_6m_hash=obs_6m.calculation.observation_hash if obs_6m else None,
            calculation_version=CALCULATION_VERSION,
        )
        rows.append(row)

    # Deterministic sorting rule:
    # 1. evaluation_timestamp
    # 2. ipo_id
    # 3. final_evaluation_id
    rows.sort(key=lambda r: (r.evaluation_timestamp, r.ipo_id, r.final_evaluation_id))

    dataset_hash = compute_dataset_hash(rows)

    manifest = BacktestDatasetManifest(
        manifest_version="1.0.0",
        dataset_version="1.0.0",
        calculation_version=CALCULATION_VERSION,
        generation_timestamp=generation_timestamp,
        row_count=len(rows),
        included_evaluation_count=len(rows),
        included_observation_count=total_obs_count,
        dataset_hash=dataset_hash,
        status_counts=status_counts,
        source_hashes=source_hashes,
    )

    return BacktestDataset(manifest=manifest, rows=rows)


def export_dataset_json(dataset: BacktestDataset, output_path: str | Path) -> Path:
    """Export the backtest dataset as canonical JSON."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as handle:
        json.dump(dataset.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return out_file


CSV_FIELD_NAMES = [
    "ipo_id",
    "company_name",
    "final_evaluation_id",
    "evaluation_timestamp",
    "final_score",
    "verdict",
    "verdict_band_score",
    "confidence_level",
    "completeness_pct",
    "lower_bound",
    "upper_bound",
    "module_a_score",
    "module_b_score",
    "module_c_score",
    "module_d_score",
    "module_e_score",
    "module_f_score",
    "knockout_status",
    "knockout_triggered",
    "insufficient_data",
    "unknown_points",
    "issue_price",
    "listing_date",
    "listing_gain_pct",
    "return_1w_pct",
    "return_1m_pct",
    "return_6m_pct",
    "benchmark_return_1w_pct",
    "benchmark_return_1m_pct",
    "benchmark_return_6m_pct",
    "excess_return_1w_pct",
    "excess_return_1m_pct",
    "excess_return_6m_pct",
    "observation_1w_status",
    "observation_1m_status",
    "observation_6m_status",
    "dataset_row_status",
    "final_result_hash",
    "observation_1w_hash",
    "observation_1m_hash",
    "observation_6m_hash",
    "calculation_version",
]


def export_dataset_csv(dataset: BacktestDataset, output_path: str | Path) -> Path:
    """Export the backtest dataset as flat CSV projection."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with out_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_FIELD_NAMES)

        for row in dataset.rows:
            d = row.to_dict()
            line = []
            for field in CSV_FIELD_NAMES:
                val = d.get(field)
                if val is None:
                    line.append("")
                elif isinstance(val, (list, tuple)):
                    line.append(";".join(str(v) for v in val))
                else:
                    line.append(str(val))
            writer.writerow(line)

    return out_file


def verify_dataset(
    dataset_path: str | Path,
    store_root: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Audit and verify dataset integrity.

    Checks:
    1. Canonical JSON structure and manifest existence.
    2. Deterministic sorting rule conformity.
    3. Recomputed dataset hash against recorded manifest.dataset_hash.
    4. Duplicate identity detection.
    5. Parent FINAL linkage and result_hash verification if store_root is provided.
    """
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"dataset file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict) or "manifest" not in data or "rows" not in data:
        raise DatasetVerificationError("invalid dataset format: missing manifest or rows")

    dataset = BacktestDataset.from_dict(data)
    manifest = dataset.manifest
    rows = dataset.rows

    # 1. Verify row count
    if len(rows) != manifest.row_count:
        return {
            "status": "FAIL",
            "reason": f"row_count mismatch: {len(rows)} rows vs manifest {manifest.row_count}",
        }

    # 2. Check deterministic ordering
    sorted_rows = sorted(rows, key=lambda r: (r.evaluation_timestamp, r.ipo_id, r.final_evaluation_id))
    ordering_valid = (rows == sorted_rows)
    if not ordering_valid:
        return {
            "status": "FAIL",
            "reason": "rows violate deterministic sorting rule (evaluation_timestamp, ipo_id, final_evaluation_id)",
        }

    # 3. Check for duplicates
    seen_eids: Set[str] = set()
    for r in rows:
        if r.final_evaluation_id in seen_eids:
            return {
                "status": "FAIL",
                "reason": f"duplicate evaluation_id found in dataset: {r.final_evaluation_id}",
            }
        seen_eids.add(r.final_evaluation_id)

    # 4. Recompute dataset hash
    recomputed_hash = compute_dataset_hash(rows)
    hash_match = (recomputed_hash == manifest.dataset_hash)
    if not hash_match:
        return {
            "status": "FAIL",
            "reason": f"dataset_hash mismatch: recomputed {recomputed_hash} != manifest {manifest.dataset_hash}",
        }

    # 5. Optional store linkage verification
    store_verification: List[Dict[str, Any]] = []
    if store_root:
        store_path = Path(store_root)
        for r in rows:
            eval_record = validate_parent_evaluation(store_path, r.final_evaluation_id)
            res_match = (eval_record.get("result_hash") == r.final_result_hash)
            store_verification.append({
                "evaluation_id": r.final_evaluation_id,
                "result_hash_match": res_match,
            })
            if not res_match:
                return {
                    "status": "FAIL",
                    "reason": f"parent result_hash mismatch for {r.final_evaluation_id}",
                    "items": store_verification,
                }

    return {
        "status": "PASS",
        "row_count": len(rows),
        "dataset_hash": manifest.dataset_hash,
        "dataset_hash_match": True,
        "ordering_valid": True,
        "store_verification": store_verification,
    }


def _opt_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _opt_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None
