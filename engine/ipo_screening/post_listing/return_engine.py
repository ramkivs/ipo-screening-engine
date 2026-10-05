"""Phase 6A: Deterministic Return and Excess Return Calculation Engine.

Calculates listing gain, absolute return, secondary market return, benchmark return,
and excess return with fail-closed semantics and deterministic observation hashing.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple

from .models import (
    BenchmarkObservation,
    CalculationMetadata,
    Horizon,
    ObservationStatus,
    PostListingObservation,
    PriceObservation,
    ProvenanceRecord,
    ReturnSet,
    VerificationStatus,
)
from .price_adapter import DailyPriceRecord, PriceDataset
from .trading_calendar import resolve_observation_date

CALCULATION_VERSION = "1.0.0"


def _round_float(val: Optional[float], decimals: int = 6) -> Optional[float]:
    if val is None:
        return None
    d = Decimal(str(val))
    q = Decimal(10) ** -decimals
    return float(d.quantize(q, rounding=ROUND_HALF_UP))


def calculate_listing_gain(issue_price: float, listing_open: Optional[float]) -> Optional[float]:
    """Calculate listing gain percentage: (listing_open - issue_price) / issue_price * 100."""
    if issue_price <= 0.0:
        raise ValueError(f"issue_price must be positive: {issue_price}")
    if listing_open is None:
        return None
    gain = (listing_open - issue_price) / issue_price * 100.0
    return _round_float(gain, 6)


def calculate_absolute_return(
    issue_price: float,
    raw_observed_close: Optional[float],
    corporate_action_factor: float = 1.0,
) -> Tuple[Optional[float], Optional[float]]:
    """Calculate adjusted close and absolute return from issue price.

    Returns: (adjusted_observed_close, absolute_return_pct)
    """
    if issue_price <= 0.0:
        raise ValueError(f"issue_price must be positive: {issue_price}")
    if raw_observed_close is None:
        return None, None
    if corporate_action_factor <= 0.0:
        raise ValueError(f"corporate_action_factor must be positive: {corporate_action_factor}")

    adj_close = _round_float(raw_observed_close * corporate_action_factor, 6)
    ret = (adj_close - issue_price) / issue_price * 100.0
    return adj_close, _round_float(ret, 6)


def calculate_secondary_return(
    listing_open: Optional[float],
    adjusted_observed_close: Optional[float],
) -> Optional[float]:
    """Calculate secondary return from listing open to observed close."""
    if listing_open is None or adjusted_observed_close is None or listing_open <= 0.0:
        return None
    ret = (adjusted_observed_close - listing_open) / listing_open * 100.0
    return _round_float(ret, 6)


def calculate_benchmark_return(
    listing_benchmark: Optional[float],
    observed_benchmark: Optional[float],
) -> Optional[float]:
    """Calculate percentage benchmark return."""
    if listing_benchmark is None or observed_benchmark is None or listing_benchmark <= 0.0:
        return None
    ret = (observed_benchmark - listing_benchmark) / listing_benchmark * 100.0
    return _round_float(ret, 6)


def calculate_excess_return(
    absolute_return_pct: Optional[float],
    benchmark_return_pct: Optional[float],
) -> Optional[float]:
    """Calculate excess return: absolute_return - benchmark_return.

    Fail-closed: if either is None, returns None (never default to zero).
    """
    if absolute_return_pct is None or benchmark_return_pct is None:
        return None
    excess = absolute_return_pct - benchmark_return_pct
    return _round_float(excess, 6)


def sha256_canonical_dict(payload: Dict[str, Any]) -> str:
    """Deterministic SHA-256 hash over canonical JSON representation."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_observation_hashes(
    final_evaluation_id: str,
    final_result_hash: str,
    ipo_id: str,
    horizon: str,
    listing_date: str,
    target_date: str,
    actual_date: str,
    prices_dict: Dict[str, Any],
    benchmark_dict: Dict[str, Any],
    returns_dict: Dict[str, Any],
    provenance_dict: Dict[str, Any],
    calc_version: str = CALCULATION_VERSION,
) -> Tuple[str, str]:
    """Compute canonical inputs hash and observation hash."""
    inputs_payload = {
        "final_result_hash": final_result_hash,
        "issue_price": prices_dict.get("issue_price"),
        "horizon": horizon,
        "listing_date": listing_date,
        "target_date": target_date,
        "actual_date": actual_date,
        "listing_open": prices_dict.get("listing_open"),
        "raw_observed_close": prices_dict.get("raw_observed_close"),
        "corporate_action_factor": prices_dict.get("corporate_action_factor", 1.0),
        "benchmark_symbol": benchmark_dict.get("symbol"),
        "raw_listing_benchmark": benchmark_dict.get("raw_listing_value"),
        "raw_observed_benchmark": benchmark_dict.get("raw_observed_value"),
        "calculation_version": calc_version,
    }
    inputs_hash = sha256_canonical_dict(inputs_payload)

    full_payload = {
        "final_evaluation_id": final_evaluation_id,
        "final_result_hash": final_result_hash,
        "ipo_id": ipo_id,
        "horizon": horizon,
        "listing_date": listing_date,
        "target_observation_date": target_date,
        "actual_observation_date": actual_date,
        "prices": prices_dict,
        "benchmark": benchmark_dict,
        "returns": returns_dict,
        "provenance": provenance_dict,
        "calculation_inputs_hash": inputs_hash,
        "calculation_version": calc_version,
    }
    obs_hash = sha256_canonical_dict(full_payload)
    return inputs_hash, obs_hash


def build_observation(
    final_evaluation_id: str,
    final_result_hash: str,
    ipo_id: str,
    symbol: str,
    issue_price: float,
    listing_date: str,
    horizon: str,
    price_dataset: PriceDataset,
    benchmark_symbol: str = "NIFTY_50_TRI",
    corporate_action_factor: float = 1.0,
    corporate_action_unverified: bool = False,
    version: int = 1,
    supersedes_observation_id: Optional[str] = None,
    restatement_reason: Optional[str] = None,
    retrieval_timestamp: str = "2026-10-06T12:00:00Z",
) -> PostListingObservation:
    """Build a complete, verified PostListingObservation for a given horizon."""
    if issue_price <= 0.0:
        raise ValueError(f"issue_price must be positive: {issue_price}")

    # Resolve dates
    target_date, actual_date = resolve_observation_date(
        listing_date=listing_date,
        horizon=horizon,
        available_dates=price_dataset.trading_dates if price_dataset.trading_dates else None,
    )

    # Price lookups
    listing_rec = price_dataset.get_price(symbol, listing_date)
    observed_rec = price_dataset.get_price(symbol, actual_date)

    listing_open = listing_rec.open if listing_rec else None
    listing_close = listing_rec.close if listing_rec else None
    raw_observed_close = observed_rec.close if observed_rec else None

    # Merge corporate action factor if record has non-default factor
    if observed_rec and observed_rec.corporate_action_factor != 1.0 and corporate_action_factor == 1.0:
        effective_factor = observed_rec.corporate_action_factor
    else:
        effective_factor = corporate_action_factor

    adj_observed_close, absolute_return = calculate_absolute_return(
        issue_price=issue_price,
        raw_observed_close=raw_observed_close,
        corporate_action_factor=effective_factor,
    )
    listing_gain = calculate_listing_gain(issue_price, listing_open)
    sec_return = calculate_secondary_return(listing_open, adj_observed_close)

    # Benchmark lookups
    b_sym = benchmark_symbol.upper()
    listing_bench = price_dataset.get_benchmark_close(b_sym, listing_date)
    # If not found under exact b_sym, try fallback normalized symbol
    if listing_bench is None and b_sym == "NIFTY_50_TRI":
        listing_bench = price_dataset.get_benchmark_close("NIFTY_50", listing_date)
        if listing_bench is not None:
            b_sym = "NIFTY_50"

    observed_bench = price_dataset.get_benchmark_close(b_sym, actual_date)
    bench_return = calculate_benchmark_return(listing_bench, observed_bench)
    excess_return = calculate_excess_return(absolute_return, bench_return)

    # Status assessment
    if corporate_action_unverified:
        verification_status = VerificationStatus.UNVERIFIED.value
        obs_status = ObservationStatus.UNVERIFIED.value
    elif effective_factor != 1.0:
        verification_status = VerificationStatus.VERIFIED.value
        obs_status = ObservationStatus.VERIFIED.value
    else:
        verification_status = VerificationStatus.UNADJUSTED.value
        obs_status = ObservationStatus.VERIFIED.value

    if raw_observed_close is None:
        obs_status = ObservationStatus.INCOMPLETE.value

    prices_obj = PriceObservation(
        issue_price=issue_price,
        listing_open=listing_open,
        listing_close=listing_close,
        raw_observed_close=raw_observed_close,
        corporate_action_factor=effective_factor,
        adjusted_observed_close=adj_observed_close,
    )

    benchmark_obj = BenchmarkObservation(
        symbol=b_sym,
        raw_listing_value=listing_bench,
        raw_observed_value=observed_bench,
        adjusted_listing_value=listing_bench,
        adjusted_observed_value=observed_bench,
        return_pct=bench_return,
    )

    returns_obj = ReturnSet(
        listing_gain_pct=listing_gain,
        absolute_return_pct=absolute_return,
        secondary_return_pct=sec_return,
        benchmark_return_pct=bench_return,
        excess_return_pct=excess_return,
    )

    provenance_obj = ProvenanceRecord(
        source_id=f"FILE-{price_dataset.content_hash[:12]}",
        source_type=price_dataset.source_type,
        source_uri_or_file=price_dataset.source_path,
        retrieval_timestamp=retrieval_timestamp,
        content_hash=price_dataset.content_hash,
    )

    # Construct observation_id
    version_suffix = f"-v{version}" if version > 1 else ""
    obs_id = f"OBS-{final_evaluation_id}-{horizon.upper()}{version_suffix}"

    inputs_hash, obs_hash = compute_observation_hashes(
        final_evaluation_id=final_evaluation_id,
        final_result_hash=final_result_hash,
        ipo_id=ipo_id,
        horizon=horizon.upper(),
        listing_date=listing_date,
        target_date=target_date,
        actual_date=actual_date,
        prices_dict=prices_obj.to_dict(),
        benchmark_dict=benchmark_obj.to_dict(),
        returns_dict=returns_obj.to_dict(),
        provenance_dict=provenance_obj.to_dict(),
        calc_version=CALCULATION_VERSION,
    )

    calc_obj = CalculationMetadata(
        calculation_version=CALCULATION_VERSION,
        calculation_inputs_hash=inputs_hash,
        observation_hash=obs_hash,
    )

    return PostListingObservation(
        observation_id=obs_id,
        final_evaluation_id=final_evaluation_id,
        final_result_hash=final_result_hash,
        ipo_id=ipo_id,
        horizon=horizon.upper(),
        listing_date=listing_date,
        target_observation_date=target_date,
        actual_observation_date=actual_date,
        prices=prices_obj,
        benchmark=benchmark_obj,
        returns=returns_obj,
        provenance=provenance_obj,
        calculation=calc_obj,
        observation_status=obs_status,
        verification_status=verification_status,
        version=version,
        supersedes_observation_id=supersedes_observation_id,
        restatement_reason=restatement_reason,
    )
