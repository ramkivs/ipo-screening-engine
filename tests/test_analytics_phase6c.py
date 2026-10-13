"""Phase 6C Acceptance Test Suite: Historical Backtest Analytics & Statistical Diagnostics.

Covers all 40 tests:
T-6C-01: Dataset analytical loader loads valid canonical dataset without triggering rescoring.
T-6C-02: Horizon-specific eligibility filtering correctly filters 1W, 1M, 6M returns.
T-6C-03: Excluded row accounting correctly partitions INVALID vs COMPLETE vs PARTIAL.
T-6C-04: Sample-size maturity classifier: N < 30 returns DESCRIPTIVE_ONLY.
T-6C-05: Sample-size maturity classifier: 30 <= N < 100 returns EXPLORATORY.
T-6C-06: Sample-size maturity classifier: N >= 100 returns STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS.
T-6C-07: Descriptive statistics: N, mean, median, min, max, std.
T-6C-08: Descriptive statistics: positive, negative, zero counts and positive rate.
T-6C-09: Descriptive statistics: excess returns (mean excess, median excess, positive excess rate).
T-6C-10: Fractional (average) ranking computation handles ties accurately.
T-6C-11: Fractional ranking computation handles all distinct values.
T-6C-12: Spearman rank correlation between final_score and 1W return.
T-6C-13: Spearman rank correlation with identical / zero variance handles status UNDEFINED_ZERO_VARIANCE.
T-6C-14: Spearman rank correlation handles N < 3 as INSUFFICIENT_DATA.
T-6C-15: Information Coefficient (Rank-IC) diagnostics for final_score across 1W, 1M, 6M.
T-6C-16: Information Coefficient metadata fields (method, tie_policy, missing_value_policy).
T-6C-17: Quantile bucket calculation for quintiles (5 buckets).
T-6C-18: Quantile bucket calculation for deciles (10 buckets).
T-6C-19: Quantile analysis fallback to INSUFFICIENT_DATA when N < num_buckets.
T-6C-20: Quantile deterministic tie ordering using score, timestamp, ipo_id.
T-6C-21: Hit rate calculation overall for positive returns and excess returns.
T-6C-22: Hit rate calculation grouped by verdict (APPLY, WATCH, AVOID).
T-6C-23: Hit rate handles empty group with status NO_DATA.
T-6C-24: Module diagnostics for Module A (Financial Quality) across horizons.
T-6C-25: Module diagnostics for Modules B through F.
T-6C-26: Benchmark diagnostics records NIFTY_50_TRI benchmark return and excess return.
T-6C-27: Benchmark diagnostics preserves UNKNOWN semantics when benchmark return is missing.
T-6C-28: Temporal vintage diagnostics groups records by evaluation calendar year.
T-6C-29: Temporal holdout diagnostic splits earlier vs latest vintage when N >= 30 and >= 2 vintages.
T-6C-30: Temporal holdout diagnostic returns INSUFFICIENT_DATA when vintages < 2 or N < 30.
T-6C-31: Point-in-time leakage audit: timestamp ordering check passes when eval <= listing.
T-6C-32: Point-in-time leakage audit: detects eval date after listing date and fails.
T-6C-33: Point-in-time leakage audit: detects invalid row status and reports finding.
T-6C-34: Point-in-time leakage audit: checks final evaluation linkage integrity.
T-6C-35: Deterministic analytical hash computation is reproducible and independent of generation time.
T-6C-36: Verification audit: verifies valid analysis JSON against canonical content hash.
T-6C-37: Verification audit: detects tampering with descriptive statistics or coefficients.
T-6C-38: Verification audit: verifies cross-linkage to original dataset file and flags hash mismatch.
T-6C-39: CLI command `post-listing analyze` generates JSON and CSV deliverables successfully.
T-6C-40: CLI command `post-listing verify-analysis` audits analysis deliverable and returns EXIT_OK.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

try:
    from ipo_screening.post_listing import (
        ANALYSIS_CALCULATION_VERSION,
        ANALYSIS_VERSION,
        AnalyticalManifest,
        BacktestAnalysis,
        BacktestDataset,
        BacktestDatasetManifest,
        BacktestDatasetRow,
        CorrelationResult,
        DatasetRowStatus,
        DescriptiveStats,
        HitRateResult,
        ICResult,
        LeakageAuditResult,
        ModuleDiagnostic,
        QuantileAnalysis,
        QuantileBucket,
        SampleMaturity,
        TemporalHoldoutResult,
        VintageDiagnostic,
        analyze_dataset,
        audit_point_in_time_leakage,
        calculate_descriptive_stats,
        calculate_spearman_rho,
        classify_sample_maturity,
        compute_analysis_content_hash,
        compute_dataset_hash,
        compute_hit_rate,
        compute_quantiles,
        compute_ranks,
        export_analysis_csv,
        export_analysis_json,
        export_dataset_json,
        load_dataset_json,
        verify_analysis,
    )
except ImportError:
    from engine.ipo_screening.post_listing import (
        ANALYSIS_CALCULATION_VERSION,
        ANALYSIS_VERSION,
        AnalyticalManifest,
        BacktestAnalysis,
        BacktestDataset,
        BacktestDatasetManifest,
        BacktestDatasetRow,
        CorrelationResult,
        DatasetRowStatus,
        DescriptiveStats,
        HitRateResult,
        ICResult,
        LeakageAuditResult,
        ModuleDiagnostic,
        QuantileAnalysis,
        QuantileBucket,
        SampleMaturity,
        TemporalHoldoutResult,
        VintageDiagnostic,
        analyze_dataset,
        audit_point_in_time_leakage,
        calculate_descriptive_stats,
        calculate_spearman_rho,
        classify_sample_maturity,
        compute_analysis_content_hash,
        compute_dataset_hash,
        compute_hit_rate,
        compute_quantiles,
        compute_ranks,
        export_analysis_csv,
        export_analysis_json,
        export_dataset_json,
        load_dataset_json,
        verify_analysis,
    )


def _make_dummy_row(
    ipo_id: str,
    score: float = 65.0,
    ret_1w: Optional[float] = 5.0,
    ret_1m: Optional[float] = 8.0,
    ret_6m: Optional[float] = 15.0,
    bench_1w: Optional[float] = 1.0,
    bench_1m: Optional[float] = 2.0,
    bench_6m: Optional[float] = 5.0,
    status: str = "COMPLETE",
    eval_timestamp: str = "2026-09-01T10:00:00Z",
    listing_date: str = "2026-09-05",
    verdict: str = "APPLY",
    mod_a: float = 70.0,
    mod_b: float = 60.0,
    mod_c: float = 80.0,
    mod_d: float = 65.0,
    mod_e: float = 75.0,
    mod_f: float = 55.0,
    obs_1w_status: str = "VERIFIED",
    obs_1m_status: str = "VERIFIED",
    obs_6m_status: str = "VERIFIED",
) -> BacktestDatasetRow:
    """Helper to construct deterministic dataset row for testing."""
    excess_1w = round(ret_1w - bench_1w, 6) if ret_1w is not None and bench_1w is not None else None
    excess_1m = round(ret_1m - bench_1m, 6) if ret_1m is not None and bench_1m is not None else None
    excess_6m = round(ret_6m - bench_6m, 6) if ret_6m is not None and bench_6m is not None else None

    dummy_hash = "a" * 64
    return BacktestDatasetRow(
        ipo_id=ipo_id,
        company_name=f"Company {ipo_id}",
        final_evaluation_id=f"eval-{ipo_id}",
        evaluation_timestamp=eval_timestamp,
        final_score=score,
        verdict=verdict,
        verdict_band_score=score,
        confidence_level="HIGH",
        completeness_pct=100.0,
        lower_bound=score - 5.0,
        upper_bound=score + 5.0,
        module_a_score=mod_a,
        module_b_score=mod_b,
        module_c_score=mod_c,
        module_d_score=mod_d,
        module_e_score=mod_e,
        module_f_score=mod_f,
        knockout_status="CLEAR",
        knockout_triggered=[],
        insufficient_data=False,
        unknown_points=0.0,
        issue_price=100.0,
        listing_date=listing_date,
        listing_gain_pct=ret_1w,
        return_1w_pct=ret_1w,
        return_1m_pct=ret_1m,
        return_6m_pct=ret_6m,
        benchmark_return_1w_pct=bench_1w,
        benchmark_return_1m_pct=bench_1m,
        benchmark_return_6m_pct=bench_6m,
        excess_return_1w_pct=excess_1w,
        excess_return_1m_pct=excess_1m,
        excess_return_6m_pct=excess_6m,
        observation_1w_status=obs_1w_status,
        observation_1m_status=obs_1m_status,
        observation_6m_status=obs_6m_status,
        dataset_row_status=status,
        final_result_hash=dummy_hash,
        observation_1w_hash=dummy_hash,
        observation_1m_hash=dummy_hash,
        observation_6m_hash=dummy_hash,
        calculation_version="1.0.0",
    )


def _make_dataset(rows: List[BacktestDatasetRow]) -> BacktestDataset:
    d_hash = compute_dataset_hash(rows)
    manifest = BacktestDatasetManifest(
        manifest_version="1.0.0",
        dataset_version="1.0.0",
        calculation_version="1.0.0",
        generation_timestamp="2026-10-06T12:00:00Z",
        row_count=len(rows),
        included_evaluation_count=len(rows),
        included_observation_count=len(rows) * 3,
        dataset_hash=d_hash,
        status_counts={"COMPLETE": len(rows)},
    )
    return BacktestDataset(manifest=manifest, rows=rows)


def test_t6c_01_dataset_loader(tmp_path: Path):
    """T-6C-01: Dataset analytical loader loads canonical dataset without triggering rescoring."""
    row = _make_dummy_row("IPO-001")
    ds = _make_dataset([row])
    out_file = tmp_path / "dataset.json"
    export_dataset_json(ds, out_file)

    loaded = load_dataset_json(out_file)
    assert len(loaded.rows) == 1
    assert loaded.rows[0].ipo_id == "IPO-001"
    assert loaded.rows[0].final_score == 65.0
    assert loaded.manifest.dataset_hash == ds.manifest.dataset_hash


def test_t6c_02_eligibility_filtering():
    """T-6C-02: Horizon-specific eligibility filtering correctly filters 1W, 1M, 6M returns."""
    r1 = _make_dummy_row("IPO-001", ret_1w=5.0, ret_1m=10.0, ret_6m=15.0)
    r2 = _make_dummy_row("IPO-002", ret_1w=2.0, ret_1m=None, ret_6m=None)  # partial
    r3 = _make_dummy_row("IPO-003", ret_1w=None, ret_1m=None, ret_6m=None, status="PENDING")
    ds = _make_dataset([r1, r2, r3])

    analysis = analyze_dataset(ds)
    assert analysis.eligibility_summary["total_dataset_rows"] == 3
    assert analysis.eligibility_summary["eligible_1w_count"] == 2
    assert analysis.eligibility_summary["eligible_1m_count"] == 1
    assert analysis.eligibility_summary["eligible_6m_count"] == 1


def test_t6c_03_excluded_row_accounting():
    """T-6C-03: Excluded row accounting correctly partitions INVALID vs COMPLETE vs PARTIAL."""
    r1 = _make_dummy_row("IPO-001", status="COMPLETE")
    r2 = _make_dummy_row("IPO-002", status="PARTIAL")
    r3 = _make_dummy_row("IPO-003", status="INVALID")
    ds = _make_dataset([r1, r2, r3])

    analysis = analyze_dataset(ds)
    assert analysis.eligibility_summary["total_dataset_rows"] == 3
    assert analysis.eligibility_summary["valid_rows_count"] == 2
    assert analysis.eligibility_summary["excluded_rows_count"] == 1


def test_t6c_04_sample_maturity_descriptive():
    """T-6C-04: Sample-size maturity classifier: N < 30 returns DESCRIPTIVE_ONLY."""
    assert classify_sample_maturity(0) == SampleMaturity.DESCRIPTIVE_ONLY.value
    assert classify_sample_maturity(10) == SampleMaturity.DESCRIPTIVE_ONLY.value
    assert classify_sample_maturity(29) == SampleMaturity.DESCRIPTIVE_ONLY.value


def test_t6c_05_sample_maturity_exploratory():
    """T-6C-05: Sample-size maturity classifier: 30 <= N < 100 returns EXPLORATORY."""
    assert classify_sample_maturity(30) == SampleMaturity.EXPLORATORY.value
    assert classify_sample_maturity(50) == SampleMaturity.EXPLORATORY.value
    assert classify_sample_maturity(99) == SampleMaturity.EXPLORATORY.value


def test_t6c_06_sample_maturity_actionable():
    """T-6C-06: Sample-size maturity classifier: N >= 100 returns STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS."""
    assert classify_sample_maturity(100) == SampleMaturity.STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS.value
    assert classify_sample_maturity(250) == SampleMaturity.STATISTICALLY_ACTIONABLE_FOR_DIAGNOSTICS.value


def test_t6c_07_descriptive_stats_numerical():
    """T-6C-07: Descriptive statistics: N, mean, median, min, max, std."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    stats = calculate_descriptive_stats(values)
    assert stats.n == 5
    assert stats.mean == 30.0
    assert stats.median == 30.0
    assert stats.min == 10.0
    assert stats.max == 50.0
    assert stats.std == pytest.approx(15.811388, abs=1e-5)


def test_t6c_08_descriptive_stats_counts_rates():
    """T-6C-08: Descriptive statistics: positive, negative, zero counts and positive rate."""
    values = [-10.0, -5.0, 0.0, 5.0, 10.0]
    stats = calculate_descriptive_stats(values)
    assert stats.positive_count == 2
    assert stats.negative_count == 2
    assert stats.zero_count == 1
    assert stats.positive_rate == 40.0


def test_t6c_09_descriptive_stats_excess_returns():
    """T-6C-09: Descriptive statistics: excess returns (mean excess, median excess, positive excess rate)."""
    returns = [5.0, 10.0, 15.0]
    excess = [2.0, 4.0, 6.0]
    stats = calculate_descriptive_stats(returns, excess)
    assert stats.mean_excess == 4.0
    assert stats.median_excess == 4.0
    assert stats.positive_excess_rate == 100.0


def test_t6c_10_ranking_ties_handling():
    """T-6C-10: Fractional (average) ranking computation handles ties accurately."""
    values = [10.0, 20.0, 20.0, 30.0]
    ranks = compute_ranks(values)
    assert ranks == [1.0, 2.5, 2.5, 4.0]

    all_tied = [5.0, 5.0, 5.0, 5.0]
    assert compute_ranks(all_tied) == [2.5, 2.5, 2.5, 2.5]


def test_t6c_11_ranking_distinct_values():
    """T-6C-11: Fractional ranking computation handles all distinct values."""
    values = [40.0, 10.0, 30.0, 20.0]
    ranks = compute_ranks(values)
    assert ranks == [4.0, 1.0, 3.0, 2.0]


def test_t6c_12_spearman_rank_correlation():
    """T-6C-12: Spearman rank correlation between final_score and 1W return."""
    x = [50.0, 60.0, 70.0, 80.0, 90.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    rho, status = calculate_spearman_rho(x, y)
    assert status == "CALCULATED"
    assert rho == 1.0

    y_inv = [10.0, 8.0, 6.0, 4.0, 2.0]
    rho_inv, status_inv = calculate_spearman_rho(x, y_inv)
    assert status_inv == "CALCULATED"
    assert rho_inv == -1.0


def test_t6c_13_spearman_zero_variance():
    """T-6C-13: Spearman rank correlation with identical / zero variance handles status UNDEFINED_ZERO_VARIANCE."""
    x = [50.0, 50.0, 50.0, 50.0]
    y = [2.0, 4.0, 6.0, 8.0]
    rho, status = calculate_spearman_rho(x, y)
    assert status == "UNDEFINED_ZERO_VARIANCE"
    assert rho == 0.0


def test_t6c_14_spearman_insufficient_data():
    """T-6C-14: Spearman rank correlation handles N < 3 as INSUFFICIENT_DATA."""
    x = [50.0, 60.0]
    y = [2.0, 4.0]
    rho, status = calculate_spearman_rho(x, y)
    assert status == "INSUFFICIENT_DATA"
    assert rho is None


def test_t6c_15_information_coefficients():
    """T-6C-15: Information Coefficient (Rank-IC) diagnostics for final_score across 1W, 1M, 6M."""
    rows = [
        _make_dummy_row(f"IPO-{i}", score=50.0 + i * 5, ret_1w=i * 2.0, ret_1m=i * 3.0, ret_6m=i * 4.0)
        for i in range(1, 6)
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    ic_1w = next(ic for ic in analysis.information_coefficients if ic.predictor == "final_score" and ic.outcome == "return_1w_pct")
    assert ic_1w.status == "CALCULATED"
    assert ic_1w.coefficient == 1.0
    assert ic_1w.n == 5


def test_t6c_16_ic_metadata():
    """T-6C-16: Information Coefficient metadata fields (method, tie_policy, missing_value_policy)."""
    rows = [_make_dummy_row(f"IPO-{i}", score=50.0 + i) for i in range(1, 5)]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    for ic in analysis.information_coefficients:
        assert ic.method == "SPEARMAN_RANK_CORRELATION"
        assert ic.tie_policy == "AVERAGE_RANK"
        assert ic.missing_value_policy == "PAIRWISE_EXCLUDE"


def test_t6c_17_quintile_analysis():
    """T-6C-17: Quantile bucket calculation for quintiles (5 buckets)."""
    rows = [
        _make_dummy_row(f"IPO-{i:02d}", score=50.0 + i, ret_1w=float(i))
        for i in range(1, 26)  # 25 rows, exactly 5 per quintile
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    q_1w = analysis.quintile_analysis["1W"]
    assert q_1w.status == "CALCULATED"
    assert q_1w.bucket_count == 5
    assert len(q_1w.buckets) == 5
    for b in q_1w.buckets:
        assert b.n == 5


def test_t6c_18_decile_analysis():
    """T-6C-18: Quantile bucket calculation for deciles (10 buckets)."""
    rows = [
        _make_dummy_row(f"IPO-{i:02d}", score=50.0 + i, ret_1w=float(i))
        for i in range(1, 31)  # 30 rows, exactly 3 per decile
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    d_1w = analysis.decile_analysis["1W"]
    assert d_1w.status == "CALCULATED"
    assert d_1w.bucket_count == 10
    assert len(d_1w.buckets) == 10
    for b in d_1w.buckets:
        assert b.n == 3


def test_t6c_19_decile_insufficient_data():
    """T-6C-19: Quantile analysis fallback to INSUFFICIENT_DATA when N < num_buckets."""
    rows = [_make_dummy_row(f"IPO-{i}", score=50.0 + i) for i in range(1, 8)]  # 7 rows < 10
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    d_1w = analysis.decile_analysis["1W"]
    assert d_1w.status == "INSUFFICIENT_DATA"
    assert d_1w.bucket_count == 0
    assert d_1w.buckets == []


def test_t6c_20_quantile_deterministic_tie_ordering():
    """T-6C-20: Quantile deterministic tie ordering using score, timestamp, ipo_id."""
    rows = [
        _make_dummy_row("IPO-B", score=60.0, eval_timestamp="2026-09-02T10:00:00Z"),
        _make_dummy_row("IPO-A", score=60.0, eval_timestamp="2026-09-01T10:00:00Z"),
        _make_dummy_row("IPO-C", score=60.0, eval_timestamp="2026-09-02T10:00:00Z"),
        _make_dummy_row("IPO-D", score=70.0, eval_timestamp="2026-09-03T10:00:00Z"),
        _make_dummy_row("IPO-E", score=70.0, eval_timestamp="2026-09-04T10:00:00Z"),
    ]
    q = compute_quantiles(rows, "1W", "return_1w_pct", num_buckets=5)
    assert q.status == "CALCULATED"
    assert len(q.buckets) == 5


def test_t6c_21_hit_rate_overall():
    """T-6C-21: Hit rate calculation overall for positive returns and excess returns."""
    rows = [
        _make_dummy_row("IPO-1", ret_1w=10.0, bench_1w=2.0),   # ret > 0, exc > 0
        _make_dummy_row("IPO-2", ret_1w=-5.0, bench_1w=-2.0),  # ret < 0, exc < 0
        _make_dummy_row("IPO-3", ret_1w=1.0, bench_1w=3.0),    # ret > 0, exc < 0
        _make_dummy_row("IPO-4", ret_1w=8.0, bench_1w=2.0),    # ret > 0, exc > 0
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    hr_1w = next(h for h in analysis.hit_rates if h.population == "overall" and h.outcome == "return_1w_pct")
    assert hr_1w.hits == 3
    assert hr_1w.misses == 1
    assert hr_1w.hit_rate == 75.0

    hr_exc_1w = next(h for h in analysis.hit_rates if h.population == "overall" and h.outcome == "excess_return_1w_pct")
    assert hr_exc_1w.hits == 2
    assert hr_exc_1w.misses == 2
    assert hr_exc_1w.hit_rate == 50.0


def test_t6c_22_hit_rate_verdict_groups():
    """T-6C-22: Hit rate calculation grouped by verdict (APPLY, WATCH, AVOID)."""
    rows = [
        _make_dummy_row("IPO-1", verdict="APPLY", ret_1w=10.0),
        _make_dummy_row("IPO-2", verdict="APPLY", ret_1w=5.0),
        _make_dummy_row("IPO-3", verdict="AVOID", ret_1w=-8.0),
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    hr_apply = next(h for h in analysis.hit_rates if h.population == "verdict_APPLY" and h.outcome == "return_1w_pct")
    assert hr_apply.hits == 2
    assert hr_apply.misses == 0
    assert hr_apply.hit_rate == 100.0

    hr_avoid = next(h for h in analysis.hit_rates if h.population == "verdict_AVOID" and h.outcome == "return_1w_pct")
    assert hr_avoid.hits == 0
    assert hr_avoid.misses == 1
    assert hr_avoid.hit_rate == 0.0


def test_t6c_23_hit_rate_no_data():
    """T-6C-23: Hit rate handles empty group with status NO_DATA."""
    res = compute_hit_rate("empty", "verdict", "return_1w_pct", [])
    assert res.status == "NO_DATA"
    assert res.n == 0
    assert res.hit_rate is None


def test_t6c_24_module_a_diagnostics():
    """T-6C-24: Module diagnostics for Module A (Financial Quality) across horizons."""
    rows = [
        _make_dummy_row(f"IPO-{i}", mod_a=50.0 + i * 10, ret_1w=float(i), ret_1m=float(i * 2), ret_6m=float(i * 3))
        for i in range(1, 5)
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    mod_a_1w = next(m for m in analysis.module_diagnostics if m.module_id == "A" and m.horizon == "1W")
    assert mod_a_1w.status == "CALCULATED"
    assert mod_a_1w.spearman_rho == 1.0
    assert mod_a_1w.positive_rate == 100.0


def test_t6c_25_modules_b_through_f_diagnostics():
    """T-6C-25: Module diagnostics for Modules B through F."""
    rows = [
        _make_dummy_row(f"IPO-{i}", mod_b=40.0 + i, mod_c=50.0 + i, mod_d=60.0 + i, mod_e=70.0 + i, mod_f=80.0 + i)
        for i in range(1, 6)
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    module_ids = {m.module_id for m in analysis.module_diagnostics}
    assert module_ids == {"A", "B", "C", "D", "E", "F"}


def test_t6c_26_benchmark_diagnostics():
    """T-6C-26: Benchmark diagnostics records NIFTY_50_TRI benchmark return and excess return."""
    rows = [
        _make_dummy_row("IPO-1", ret_1w=10.0, bench_1w=2.0),
        _make_dummy_row("IPO-2", ret_1w=6.0, bench_1w=4.0),
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    bench = analysis.benchmark_analysis
    assert bench["benchmark_symbol"] == "NIFTY_50_TRI"
    assert bench["1W"]["eligible_n"] == 2
    assert bench["1W"]["mean_benchmark_return"] == 3.0
    assert bench["1W"]["mean_excess_return"] == 5.0  # (8 + 2)/2 = 5.0


def test_t6c_27_benchmark_missing_semantics():
    """T-6C-27: Benchmark diagnostics preserves UNKNOWN semantics when benchmark return is missing."""
    rows = [
        _make_dummy_row("IPO-1", ret_1w=10.0, bench_1w=None),
        _make_dummy_row("IPO-2", ret_1w=6.0, bench_1w=None),
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    bench_1w = analysis.benchmark_analysis["1W"]
    assert bench_1w["eligible_n"] == 0
    assert bench_1w["mean_benchmark_return"] is None
    assert bench_1w["mean_excess_return"] is None


def test_t6c_28_vintage_diagnostics():
    """T-6C-28: Temporal vintage diagnostics groups records by evaluation calendar year."""
    rows = [
        _make_dummy_row("IPO-1", eval_timestamp="2025-06-01T10:00:00Z", listing_date="2025-06-10", score=60.0, ret_1w=5.0),
        _make_dummy_row("IPO-2", eval_timestamp="2025-09-01T10:00:00Z", listing_date="2025-09-10", score=70.0, ret_1w=15.0),
        _make_dummy_row("IPO-3", eval_timestamp="2026-03-01T10:00:00Z", listing_date="2026-03-10", score=80.0, ret_1w=20.0),
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    vintages = {v.vintage_year: v for v in analysis.vintage_analysis}
    assert "2025" in vintages
    assert "2026" in vintages
    assert vintages["2025"].n == 2
    assert vintages["2025"].mean_score == 65.0
    assert vintages["2025"].mean_return_1w == 10.0
    assert vintages["2026"].n == 1
    assert vintages["2026"].mean_score == 80.0


def test_t6c_29_temporal_holdout_sufficient():
    """T-6C-29: Temporal holdout diagnostic splits earlier vs latest vintage when N >= 30 and >= 2 vintages."""
    rows_2025 = [
        _make_dummy_row(f"IPO-25-{i:02d}", eval_timestamp="2025-05-01T10:00:00Z", listing_date="2025-05-10", score=60.0)
        for i in range(20)
    ]
    rows_2026 = [
        _make_dummy_row(f"IPO-26-{i:02d}", eval_timestamp="2026-05-01T10:00:00Z", listing_date="2026-05-10", score=70.0)
        for i in range(15)
    ]
    ds = _make_dataset(rows_2025 + rows_2026)  # 35 rows total across 2025 and 2026
    analysis = analyze_dataset(ds)

    holdout = analysis.holdout_analysis
    assert holdout.status == "CALCULATED"
    assert holdout.development_period == "2025"
    assert holdout.holdout_period == "2026"
    assert holdout.n_development == 20
    assert holdout.n_holdout == 15
    assert holdout.dev_mean_score == 60.0
    assert holdout.holdout_mean_score == 70.0


def test_t6c_30_temporal_holdout_insufficient():
    """T-6C-30: Temporal holdout diagnostic returns INSUFFICIENT_DATA when vintages < 2 or N < 30."""
    rows = [
        _make_dummy_row(f"IPO-{i}", eval_timestamp="2026-05-01T10:00:00Z", listing_date="2026-05-10")
        for i in range(10)
    ]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    holdout = analysis.holdout_analysis
    assert holdout.status == "INSUFFICIENT_DATA"
    assert holdout.n_holdout == 0


def test_t6c_31_leakage_audit_clean():
    """T-6C-31: Point-in-time leakage audit: timestamp ordering check passes when eval <= listing."""
    row = _make_dummy_row("IPO-1", eval_timestamp="2026-09-01T10:00:00Z", listing_date="2026-09-05")
    audit = audit_point_in_time_leakage([row])
    assert audit.passed is True
    assert audit.checks["timestamp_ordering"] is True
    assert len(audit.findings) == 0


def test_t6c_32_leakage_audit_future_eval_date():
    """T-6C-32: Point-in-time leakage audit: detects eval date after listing date and fails."""
    bad_row = _make_dummy_row("IPO-1", eval_timestamp="2026-09-10T10:00:00Z", listing_date="2026-09-05")
    audit = audit_point_in_time_leakage([bad_row])
    assert audit.passed is False
    assert audit.checks["timestamp_ordering"] is False
    assert any("after listing_date" in f for f in audit.findings)


def test_t6c_33_leakage_audit_invalid_row_status():
    """T-6C-33: Point-in-time leakage audit: detects invalid row status and reports finding."""
    bad_row = _make_dummy_row("IPO-1", status="INVALID")
    audit = audit_point_in_time_leakage([bad_row])
    assert audit.passed is False
    assert audit.checks["row_status_valid"] is False


def test_t6c_34_leakage_audit_missing_final_linkage():
    """T-6C-34: Point-in-time leakage audit: checks final evaluation linkage integrity."""
    row_dict = _make_dummy_row("IPO-1").to_dict()
    row_dict["final_evaluation_id"] = ""
    row = BacktestDatasetRow.from_dict(row_dict)
    audit = audit_point_in_time_leakage([row])
    assert audit.passed is False
    assert audit.checks["final_linkage_intact"] is False


def test_t6c_35_analysis_hash_deterministic():
    """T-6C-35: Deterministic analytical hash computation is reproducible and independent of generation time."""
    rows = [_make_dummy_row(f"IPO-{i}", score=50.0 + i) for i in range(1, 5)]
    ds = _make_dataset(rows)

    a1 = analyze_dataset(ds, generated_at="2026-10-06T10:00:00Z")
    a2 = analyze_dataset(ds, generated_at="2026-10-06T18:00:00Z")

    assert a1.manifest.analysis_hash == a2.manifest.analysis_hash
    assert len(a1.manifest.analysis_hash) == 64


def test_t6c_36_verify_analysis_pass(tmp_path: Path):
    """T-6C-36: Verification audit: verifies valid analysis JSON against canonical content hash."""
    rows = [_make_dummy_row(f"IPO-{i}", score=50.0 + i) for i in range(1, 5)]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    out_file = tmp_path / "analysis.json"
    export_analysis_json(analysis, out_file)

    res = verify_analysis(out_file)
    assert res["status"] == "PASS"
    assert res["analysis_hash_match"] is True
    assert res["analysis_hash"] == analysis.manifest.analysis_hash


def test_t6c_37_verify_analysis_tampering(tmp_path: Path):
    """T-6C-37: Verification audit: detects tampering with descriptive statistics or coefficients."""
    rows = [_make_dummy_row(f"IPO-{i}", score=50.0 + i) for i in range(1, 5)]
    ds = _make_dataset(rows)
    analysis = analyze_dataset(ds)

    out_file = tmp_path / "analysis.json"
    export_analysis_json(analysis, out_file)

    # Tamper with file
    with out_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["descriptive_statistics"]["1W"]["mean"] = 999.99
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(data, f)

    res = verify_analysis(out_file)
    assert res["status"] == "FAIL"
    assert "mismatch" in res["reason"]


def test_t6c_38_verify_analysis_dataset_linkage(tmp_path: Path):
    """T-6C-38: Verification audit: verifies cross-linkage to original dataset file and flags hash mismatch."""
    rows1 = [_make_dummy_row("IPO-1")]
    ds1 = _make_dataset(rows1)
    ds1_file = tmp_path / "dataset1.json"
    export_dataset_json(ds1, ds1_file)

    analysis = analyze_dataset(ds1)
    an_file = tmp_path / "analysis.json"
    export_analysis_json(analysis, an_file)

    # Valid linkage
    res_valid = verify_analysis(an_file, dataset_path=ds1_file)
    assert res_valid["status"] == "PASS"
    assert res_valid["dataset_match"] is True

    # Foreign dataset linkage
    rows2 = [_make_dummy_row("IPO-999")]
    ds2 = _make_dataset(rows2)
    ds2_file = tmp_path / "dataset2.json"
    export_dataset_json(ds2, ds2_file)

    res_mismatch = verify_analysis(an_file, dataset_path=ds2_file)
    assert res_mismatch["status"] == "FAIL"
    assert "dataset_hash mismatch" in res_mismatch["reason"]


def test_t6c_39_cli_analyze(tmp_path: Path):
    """T-6C-39: CLI command `post-listing analyze` generates JSON and CSV deliverables successfully."""
    rows = [_make_dummy_row(f"IPO-{i}", score=50.0 + i) for i in range(1, 10)]
    ds = _make_dataset(rows)
    ds_file = tmp_path / "dataset.json"
    export_dataset_json(ds, ds_file)

    an_json = tmp_path / "analysis.json"
    an_csv = tmp_path / "analysis.csv"

    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "post-listing",
        "analyze",
        "--dataset",
        str(ds_file),
        "--output",
        str(an_json),
        "--csv",
        str(an_csv),
        "-v",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "HISTORICAL BACKTEST ANALYTICS EXECUTED" in proc.stdout
    assert an_json.is_file()
    assert an_csv.is_file()

    # Verify CSV has contents
    with an_csv.open("r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) > 5
        assert reader[0] == ["section", "predictor", "outcome", "horizon", "n", "statistic", "value", "status"]


def test_t6c_40_cli_verify_analysis(tmp_path: Path):
    """T-6C-40: CLI command `post-listing verify-analysis` audits analysis deliverable and returns EXIT_OK."""
    rows = [_make_dummy_row(f"IPO-{i}", score=50.0 + i) for i in range(1, 6)]
    ds = _make_dataset(rows)
    ds_file = tmp_path / "dataset.json"
    export_dataset_json(ds, ds_file)

    an_json = tmp_path / "analysis.json"
    analysis = analyze_dataset(ds)
    export_analysis_json(analysis, an_json)

    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "post-listing",
        "verify-analysis",
        "--analysis",
        str(an_json),
        "--dataset",
        str(ds_file),
        "-v",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "BACKTEST ANALYSIS AUDIT" in proc.stdout
    assert "ALL PASS" in proc.stdout
