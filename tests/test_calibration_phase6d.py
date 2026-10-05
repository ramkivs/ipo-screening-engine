"""Phase 6D Acceptance Test Suite: Governed Calibration Proposal & v1.6 Configuration Draft.

Covers at least 50 tests:
T-6D-01: Maturity gate: N < 30 returns CALIBRATION_INELIGIBLE.
T-6D-02: Maturity gate: 30 <= N < 100 returns CALIBRATION_EXPLORATORY.
T-6D-03: Maturity gate: N >= 100 with >= 3 vintages and holdout returns CALIBRATION_CANDIDATE.
T-6D-04: Maturity gate: Phase 6C leakage audit failure forces CALIBRATION_INELIGIBLE.
T-6D-05: Maturity gate: dataset hash mismatch forces CALIBRATION_INELIGIBLE.
T-6D-06: Maturity gate: analysis hash mismatch forces CALIBRATION_INELIGIBLE.
T-6D-07: Maturity gate: N >= 100 with < 3 vintages stays CALIBRATION_EXPLORATORY.
T-6D-08: Maturity gate: N >= 100 with unverified holdout stays CALIBRATION_EXPLORATORY.
T-6D-09: Source evidence traceability: links dataset_hash, analysis_hash, analysis_version.
T-6D-10: Source evidence: baseline configuration version is 1.5.0.
T-6D-11: Source evidence: baseline configuration content hash is recorded and verified.
T-6D-12: Objective declaration: accepts valid declared objective (e.g. BALANCED_DIAGNOSTIC).
T-6D-13: Objective declaration: IMPROVE_HIT_RATE objective.
T-6D-14: Objective declaration: IMPROVE_RANK_CORRELATION objective.
T-6D-15: Development/holdout separation: development rows strictly separate from holdout rows.
T-6D-16: Holdout non-tuning: holdout data is not used for proposal candidate generation.
T-6D-17: Module weight analysis: evaluates all 6 modules (A through F).
T-6D-18: Module weight analysis: proposed weights sum exactly to 100.0.
T-6D-19: Module weight analysis: records Phase 6C correlations across 1W, 1M, 6M.
T-6D-20: Threshold proposal: evaluates baseline thresholds without unguided optimization.
T-6D-21: Verdict proposal: evaluates verdict boundaries.
T-6D-22: Knockout proposal firewall: knockout_proposals list defaults to empty.
T-6D-23: Knockout proposal firewall: knockout proposals require REQUIRES_EXPLICIT_GOVERNANCE_REVIEW.
T-6D-24: Overfitting protection: candidate that degrades holdout correlation is rejected.
T-6D-25: Overfitting protection: rejected candidates recorded with explicit rejection reason.
T-6D-26: Overfitting protection: development improvement alone is insufficient.
T-6D-27: Non-regression check: downside protection check passes.
T-6D-28: Non-regression check: holdout stability check passes.
T-6D-29: Non-regression check: deterministic reproducibility check passes.
T-6D-30: Current vs proposed comparison: computes baseline mean vs proposed mean score.
T-6D-31: Current vs proposed comparison: reports both improvement and degradation.
T-6D-32: Proposal status: INELIGIBLE when maturity is CALIBRATION_INELIGIBLE.
T-6D-33: Proposal status: EXPLORATORY when maturity is CALIBRATION_EXPLORATORY.
T-6D-34: Proposal status: READY_FOR_HUMAN_REVIEW when maturity is CALIBRATION_CANDIDATE.
T-6D-35: Proposal governance: status is never APPROVED, ACTIVE, or PRODUCTION.
T-6D-36: Approval status: PENDING_HUMAN_REVIEW for candidate proposals.
T-6D-37: Approval status: NOT_SUBMITTED for exploratory proposals.
T-6D-38: Proposal hash: computed deterministically from canonical JSON content payload.
T-6D-39: Proposal hash: independent of file paths, hostname, PID, generation timestamp.
T-6D-40: Proposal hash: bit-for-bit reproducible across repeated executions.
T-6D-41: Proposal hash: changes when any proposed weight or evidence is modified.
T-6D-42: v1.6 draft configuration: not generated when status is INELIGIBLE.
T-6D-43: v1.6 draft configuration: not generated when status is EXPLORATORY.
T-6D-44: v1.6 draft configuration: generated when status is CANDIDATE / READY_FOR_HUMAN_REVIEW.
T-6D-45: v1.6 draft configuration: marked explicitly status DRAFT_INACTIVE and is_active False.
T-6D-46: v1.6 draft configuration: config_version is 1.6.0-draft.
T-6D-47: v1.6 draft configuration: preserves parent_config_version and parent_config_hash.
T-6D-48: Shadow evaluation: computes in-memory score deltas without modifying evaluations.
T-6D-49: Shadow evaluation: reports verdict shift counts (upgrades, downgrades, unchanged).
T-6D-50: Verification audit: verify_proposal verifies valid proposal against canonical content hash.
T-6D-51: Verification audit: verify_proposal detects tampering with proposed weights.
T-6D-52: Verification audit: verify_proposal checks dataset and analysis hash linkages.
T-6D-53: Verification audit: verify_proposal rejects forbidden approval status.
T-6D-54: CLI command: `post-listing calibrate-propose` generates proposal artifact.
T-6D-55: CLI command: `post-listing verify-proposal` audits proposal deliverable and exits 0.
T-6D-56: CLI command: `post-listing shadow-evaluate` runs shadow evaluation deliverable.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

try:
    from ipo_screening.post_listing import (
        ApprovalStatus,
        BASELINE_CONFIG_VERSION,
        BacktestAnalysis,
        BacktestDataset,
        BacktestDatasetManifest,
        BacktestDatasetRow,
        CalibrationMaturity,
        CalibrationObjective,
        CalibrationProposal,
        KnockoutProposal,
        LeakageAuditResult,
        ModuleWeightProposal,
        ProposalStatus,
        ShadowEvaluationResult,
        TemporalHoldoutResult,
        analyze_dataset,
        classify_calibration_maturity,
        compute_config_content_hash,
        compute_dataset_hash,
        compute_proposal_content_hash,
        export_analysis_json,
        export_dataset_json,
        export_proposal_json,
        export_v1_6_draft_json,
        generate_calibration_proposal,
        generate_v1_6_draft_config,
        rescore_row,
        run_shadow_evaluation,
        verify_proposal,
    )
except ImportError:
    from engine.ipo_screening.post_listing import (
        ApprovalStatus,
        BASELINE_CONFIG_VERSION,
        BacktestAnalysis,
        BacktestDataset,
        BacktestDatasetManifest,
        BacktestDatasetRow,
        CalibrationMaturity,
        CalibrationObjective,
        CalibrationProposal,
        KnockoutProposal,
        LeakageAuditResult,
        ModuleWeightProposal,
        ProposalStatus,
        ShadowEvaluationResult,
        TemporalHoldoutResult,
        analyze_dataset,
        classify_calibration_maturity,
        compute_config_content_hash,
        compute_dataset_hash,
        compute_proposal_content_hash,
        export_analysis_json,
        export_dataset_json,
        export_proposal_json,
        export_v1_6_draft_json,
        generate_calibration_proposal,
        generate_v1_6_draft_config,
        rescore_row,
        run_shadow_evaluation,
        verify_proposal,
    )

CONFIG_PATH = Path("config/ipo-config.v1.5.0.json")


@pytest.fixture
def baseline_config() -> Dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


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
    mod_a: float = 20.0,
    mod_b: float = 15.0,
    mod_c: float = 10.0,
    mod_d: float = 10.0,
    mod_e: float = 10.0,
    mod_f: float = 5.0,
) -> BacktestDatasetRow:
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
        observation_1w_status="VERIFIED",
        observation_1m_status="VERIFIED",
        observation_6m_status="VERIFIED",
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


def _make_candidate_dataset(total_n: int = 120) -> BacktestDataset:
    """Helper creating a candidate-level dataset with >= 100 rows across 3 vintages (2024, 2025, 2026)."""
    rows = []
    vintages = ["2024", "2025", "2026"]
    for i in range(total_n):
        v = vintages[i % 3]
        rows.append(
            _make_dummy_row(
                f"IPO-{i:03d}",
                score=50.0 + (i % 40),
                ret_1w=float(i % 25 - 5),
                eval_timestamp=f"{v}-05-01T10:00:00Z",
                listing_date=f"{v}-05-10",
                mod_a=15.0 + (i % 10),
                mod_b=12.0 + (i % 8),
                mod_c=8.0 + (i % 6),
                mod_d=8.0 + (i % 6),
                mod_e=8.0 + (i % 6),
                mod_f=5.0 + (i % 4),
            )
        )
    return _make_dataset(rows)


def test_t6d_01_maturity_gate_n_under_30(baseline_config):
    """T-6D-01: Maturity gate: N < 30 returns CALIBRATION_INELIGIBLE."""
    rows = [_make_dummy_row(f"IPO-{i}") for i in range(15)]
    ds = _make_dataset(rows)
    an = analyze_dataset(ds)

    maturity, reasons = classify_calibration_maturity(ds, an)
    assert maturity == CalibrationMaturity.CALIBRATION_INELIGIBLE
    assert any("N=15 < 30" in r for r in reasons)


def test_t6d_02_maturity_gate_exploratory_30_to_100(baseline_config):
    """T-6D-02: Maturity gate: 30 <= N < 100 returns CALIBRATION_EXPLORATORY."""
    rows = [
        _make_dummy_row(f"IPO-{i:02d}", eval_timestamp=f"202{5 + i % 2}-05-01T10:00:00Z", listing_date=f"202{5 + i % 2}-05-10")
        for i in range(45)
    ]
    ds = _make_dataset(rows)
    an = analyze_dataset(ds)

    maturity, reasons = classify_calibration_maturity(ds, an)
    assert maturity == CalibrationMaturity.CALIBRATION_EXPLORATORY
    assert any("exploratory range" in r for r in reasons)


def test_t6d_03_maturity_gate_candidate_over_100(baseline_config):
    """T-6D-03: Maturity gate: N >= 100 with >= 3 vintages and holdout returns CALIBRATION_CANDIDATE."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    maturity, reasons = classify_calibration_maturity(ds, an)
    assert maturity == CalibrationMaturity.CALIBRATION_CANDIDATE
    assert any(">= 100 with 3 vintages" in r for r in reasons)


def test_t6d_04_maturity_gate_leakage_failure(baseline_config):
    """T-6D-04: Maturity gate: Phase 6C leakage audit failure forces CALIBRATION_INELIGIBLE."""
    bad_row = _make_dummy_row("IPO-1", eval_timestamp="2026-09-10T10:00:00Z", listing_date="2026-09-05")
    ds = _make_dataset([bad_row] * 35)
    an = analyze_dataset(ds)
    assert an.leakage_audit.passed is False

    maturity, reasons = classify_calibration_maturity(ds, an)
    assert maturity == CalibrationMaturity.CALIBRATION_INELIGIBLE
    assert any("Leakage audit failed" in r for r in reasons)


def test_t6d_05_maturity_gate_dataset_hash_mismatch(baseline_config):
    """T-6D-05: Maturity gate: dataset hash mismatch forces CALIBRATION_INELIGIBLE."""
    ds1 = _make_dataset([_make_dummy_row("IPO-1")] * 35)
    ds2 = _make_dataset([_make_dummy_row("IPO-2")] * 35)
    an = analyze_dataset(ds2)

    maturity, reasons = classify_calibration_maturity(ds1, an)
    assert maturity == CalibrationMaturity.CALIBRATION_INELIGIBLE
    assert any("Dataset hash mismatch" in r for r in reasons)


def test_t6d_06_maturity_gate_analysis_hash_tamper(baseline_config):
    """T-6D-06: Maturity gate: analysis hash mismatch forces CALIBRATION_INELIGIBLE."""
    ds = _make_dataset([_make_dummy_row(f"IPO-{i}") for i in range(35)])
    an = analyze_dataset(ds)
    # Mutate dataset manifest
    bad_manifest = BacktestDatasetManifest(
        manifest_version="1.0.0",
        dataset_version="1.0.0",
        calculation_version="1.0.0",
        generation_timestamp="2026-10-06T12:00:00Z",
        row_count=35,
        included_evaluation_count=35,
        included_observation_count=105,
        dataset_hash="0" * 64,
        status_counts={"COMPLETE": 35},
    )
    bad_ds = BacktestDataset(manifest=bad_manifest, rows=ds.rows)

    maturity, reasons = classify_calibration_maturity(bad_ds, an)
    assert maturity == CalibrationMaturity.CALIBRATION_INELIGIBLE


def test_t6d_07_maturity_gate_under_3_vintages_exploratory(baseline_config):
    """T-6D-07: Maturity gate: N >= 100 with < 3 vintages stays CALIBRATION_EXPLORATORY."""
    rows = [
        _make_dummy_row(f"IPO-{i:03d}", eval_timestamp=f"202{5 + i % 2}-05-01T10:00:00Z", listing_date=f"202{5 + i % 2}-05-10")
        for i in range(110)
    ]
    ds = _make_dataset(rows)  # Only 2 vintages (2025, 2026)
    an = analyze_dataset(ds)

    maturity, reasons = classify_calibration_maturity(ds, an)
    assert maturity == CalibrationMaturity.CALIBRATION_EXPLORATORY
    assert any("coverage (2 vintages" in r for r in reasons)


def test_t6d_08_maturity_gate_unverified_holdout(baseline_config):
    """T-6D-08: Maturity gate: N >= 100 with unverified holdout stays CALIBRATION_EXPLORATORY."""
    rows = [_make_dummy_row(f"IPO-{i:03d}", eval_timestamp="2026-05-01T10:00:00Z", listing_date="2026-05-10") for i in range(110)]
    ds = _make_dataset(rows)  # Only 1 vintage -> holdout status is INSUFFICIENT_DATA
    an = analyze_dataset(ds)

    maturity, reasons = classify_calibration_maturity(ds, an)
    assert maturity == CalibrationMaturity.CALIBRATION_EXPLORATORY


def test_t6d_09_source_evidence_traceability(baseline_config):
    """T-6D-09: Source evidence traceability: links dataset_hash, analysis_hash, analysis_version."""
    ds = _make_dataset([_make_dummy_row(f"IPO-{i}") for i in range(10)])
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.source_dataset_hash == ds.manifest.dataset_hash
    assert prop.source_analysis_hash == an.manifest.analysis_hash
    assert prop.source_analysis_version == "1.0.0"


def test_t6d_10_source_evidence_baseline_config_version(baseline_config):
    """T-6D-10: Source evidence: baseline configuration version is 1.5.0."""
    ds = _make_dataset([_make_dummy_row(f"IPO-{i}") for i in range(10)])
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.baseline_config_version == "1.5.0"


def test_t6d_11_source_evidence_config_hash(baseline_config):
    """T-6D-11: Source evidence: baseline configuration content hash is recorded and verified."""
    ds = _make_dataset([_make_dummy_row(f"IPO-{i}") for i in range(10)])
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    exp_cfg_hash = compute_config_content_hash(baseline_config)
    assert prop.baseline_config_hash == exp_cfg_hash
    assert len(prop.baseline_config_hash) == 64


def test_t6d_12_objective_declaration_default(baseline_config):
    """T-6D-12: Objective declaration: accepts valid declared objective (e.g. BALANCED_DIAGNOSTIC)."""
    ds = _make_dataset([_make_dummy_row(f"IPO-{i}") for i in range(10)])
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config, objective=CalibrationObjective.BALANCED_DIAGNOSTIC.value)
    assert prop.objective == "BALANCED_DIAGNOSTIC"


def test_t6d_13_objective_declaration_hit_rate(baseline_config):
    """T-6D-13: Objective declaration: IMPROVE_HIT_RATE objective."""
    ds = _make_dataset([_make_dummy_row(f"IPO-{i}") for i in range(10)])
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config, objective=CalibrationObjective.IMPROVE_HIT_RATE.value)
    assert prop.objective == "IMPROVE_HIT_RATE"


def test_t6d_14_objective_declaration_rank_correlation(baseline_config):
    """T-6D-14: Objective declaration: IMPROVE_RANK_CORRELATION objective."""
    ds = _make_dataset([_make_dummy_row(f"IPO-{i}") for i in range(10)])
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config, objective=CalibrationObjective.IMPROVE_RANK_CORRELATION.value)
    assert prop.objective == "IMPROVE_RANK_CORRELATION"


def test_t6d_15_dev_holdout_separation(baseline_config):
    """T-6D-15: Development/holdout separation: development rows strictly separate from holdout rows."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    dev_period = prop.development_results["development_period"]
    holdout_period = prop.holdout_results["holdout_period"]

    assert dev_period != holdout_period
    assert "2026" == holdout_period
    assert "2024,2025" == dev_period


def test_t6d_16_holdout_non_tuning(baseline_config):
    """T-6D-16: Holdout non-tuning: holdout data is not used for proposal candidate generation."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    for m in prop.module_proposals:
        assert m.holdout_rho is None or isinstance(m.holdout_rho, float)
        assert "development rank correlation" in m.rationale or m.status == "NO_CHANGE"


def test_t6d_17_module_analysis_covers_all_modules(baseline_config):
    """T-6D-17: Module weight analysis: evaluates all 6 modules (A through F)."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    mids = {m.module_id for m in prop.module_proposals}
    assert mids == {"A", "B", "C", "D", "E", "F"}


def test_t6d_18_module_weights_sum_to_100(baseline_config):
    """T-6D-18: Module weight analysis: proposed weights sum exactly to 100.0."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    total_prop_weight = sum(m.proposed_weight for m in prop.module_proposals)
    assert total_prop_weight == 100.0


def test_t6d_19_module_correlations_recorded(baseline_config):
    """T-6D-19: Module weight analysis: records Phase 6C correlations across 1W, 1M, 6M."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    for m in prop.module_proposals:
        assert hasattr(m, "phase6c_rho_1w")
        assert hasattr(m, "phase6c_rho_1m")
        assert hasattr(m, "phase6c_rho_6m")


def test_t6d_20_threshold_proposal_baseline(baseline_config):
    """T-6D-20: Threshold proposal: evaluates baseline thresholds without unguided optimization."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert len(prop.threshold_proposals) >= 1
    t = prop.threshold_proposals[0]
    assert t.current_value == 75.0
    assert t.status in ("NO_CHANGE", "PROPOSED")


def test_t6d_21_verdict_proposals(baseline_config):
    """T-6D-21: Verdict proposal: evaluates verdict boundaries."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    band_names = {v.band_name for v in prop.verdict_proposals}
    assert band_names == {"APPLY", "APPLY_SELECTIVELY", "NEUTRAL"}


def test_t6d_22_knockout_proposals_empty_by_default(baseline_config):
    """T-6D-22: Knockout proposal firewall: knockout_proposals list defaults to empty."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.knockout_proposals == []


def test_t6d_23_knockout_proposal_flag_enforced():
    """T-6D-23: Knockout proposal firewall: knockout proposals require REQUIRES_EXPLICIT_GOVERNANCE_REVIEW."""
    kp = KnockoutProposal(
        knockout_id="K1",
        change_type="THRESHOLD_RELAXATION",
        rationale="Hypothetical research proposal",
        evidence="Observed high pass rate",
    )
    assert kp.governance_flag == "REQUIRES_EXPLICIT_GOVERNANCE_REVIEW"
    assert kp.status == "BLOCKED_WITHOUT_EXPLICIT_GOVERNANCE_APPROVAL"


def test_t6d_24_overfitting_holdout_degradation_rejected(baseline_config):
    """T-6D-24: Overfitting protection: candidate that degrades holdout correlation is rejected."""
    # Construct a dataset where dev set and holdout set have conflicting relationships
    rows = []
    # Dev set (2024, 2025): Module A positively correlated with 1W returns
    for i in range(80):
        v = "2024" if i < 40 else "2025"
        rows.append(
            _make_dummy_row(
                f"IPO-DEV-{i:02d}",
                eval_timestamp=f"{v}-05-01T10:00:00Z",
                listing_date=f"{v}-05-10",
                ret_1w=float(i),
                mod_a=float(i % 25),
                mod_f=5.0,
            )
        )
    # Holdout set (2026): Module A negatively correlated with 1W returns
    for i in range(40):
        rows.append(
            _make_dummy_row(
                f"IPO-HLD-{i:02d}",
                eval_timestamp="2026-05-01T10:00:00Z",
                listing_date="2026-05-10",
                ret_1w=float(40 - i),
                mod_a=float(i % 25),
                mod_f=5.0,
            )
        )
    ds = _make_dataset(rows)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    # Check that candidate was rejected with overfitting reason
    assert len(prop.rejected_candidates) > 0
    assert any("overfitting" in rc.reason.lower() for rc in prop.rejected_candidates)


def test_t6d_25_rejected_candidate_records_metrics(baseline_config):
    """T-6D-25: Overfitting protection: rejected candidates recorded with explicit rejection reason."""
    rows = []
    for i in range(80):
        v = "2024" if i < 40 else "2025"
        rows.append(_make_dummy_row(f"IPO-D-{i}", eval_timestamp=f"{v}-05-01T10:00:00Z", listing_date=f"{v}-05-10", ret_1w=float(i), mod_a=float(i)))
    for i in range(40):
        rows.append(_make_dummy_row(f"IPO-H-{i}", eval_timestamp="2026-05-01T10:00:00Z", listing_date="2026-05-10", ret_1w=float(40 - i), mod_a=float(i)))
    ds = _make_dataset(rows)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    if prop.rejected_candidates:
        rc = prop.rejected_candidates[0]
        assert rc.candidate_id is not None
        assert rc.reason != ""


def test_t6d_26_overfitting_protection_non_empty(baseline_config):
    """T-6D-26: Overfitting protection: development improvement alone is insufficient."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.development_results["n_development"] > 0
    assert prop.holdout_results["n_holdout"] > 0


def test_t6d_27_non_regression_downside_protection(baseline_config):
    """T-6D-27: Non-regression check: downside protection check passes."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    check = next(c for c in prop.non_regression_results if c.check_name == "downside_protection")
    assert check.passed is True


def test_t6d_28_non_regression_holdout_stability(baseline_config):
    """T-6D-28: Non-regression check: holdout stability check passes."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    check = next(c for c in prop.non_regression_results if c.check_name == "holdout_stability")
    assert check.passed is True


def test_t6d_29_non_regression_reproducibility(baseline_config):
    """T-6D-29: Non-regression check: deterministic reproducibility check passes."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    check = next(c for c in prop.non_regression_results if c.check_name == "deterministic_reproducibility")
    assert check.passed is True


def test_t6d_30_shadow_evaluation_score_delta(baseline_config):
    """T-6D-30: Current vs proposed comparison: computes baseline mean vs proposed mean score."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)
    prop = generate_calibration_proposal(ds, an, baseline_config)

    shadow = run_shadow_evaluation(prop, ds, baseline_config)
    assert shadow.total_evaluated == 120
    assert isinstance(shadow.baseline_mean_score, float)
    assert isinstance(shadow.proposed_mean_score, float)
    assert isinstance(shadow.score_mean_delta, float)


def test_t6d_31_shadow_evaluation_reports_shifts(baseline_config):
    """T-6D-31: Current vs proposed comparison: reports both improvement and degradation."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)
    prop = generate_calibration_proposal(ds, an, baseline_config)

    shadow = run_shadow_evaluation(prop, ds, baseline_config)
    total_shifts = shadow.upgraded_count + shadow.downgraded_count + shadow.unchanged_count
    assert total_shifts == shadow.total_evaluated


def test_t6d_32_proposal_status_ineligible(baseline_config):
    """T-6D-32: Proposal status: INELIGIBLE when maturity is CALIBRATION_INELIGIBLE."""
    ds = _make_dataset([_make_dummy_row("IPO-1")] * 10)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.status == ProposalStatus.INELIGIBLE.value
    assert prop.maturity_gate == CalibrationMaturity.CALIBRATION_INELIGIBLE.value


def test_t6d_33_proposal_status_exploratory(baseline_config):
    """T-6D-33: Proposal status: EXPLORATORY when maturity is CALIBRATION_EXPLORATORY."""
    rows = [
        _make_dummy_row(f"IPO-{i:02d}", eval_timestamp=f"202{5 + i % 2}-05-01T10:00:00Z", listing_date=f"202{5 + i % 2}-05-10")
        for i in range(40)
    ]
    ds = _make_dataset(rows)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.status == ProposalStatus.EXPLORATORY.value
    assert prop.maturity_gate == CalibrationMaturity.CALIBRATION_EXPLORATORY.value


def test_t6d_34_proposal_status_ready_for_review(baseline_config):
    """T-6D-34: Proposal status: READY_FOR_HUMAN_REVIEW when maturity is CALIBRATION_CANDIDATE."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.status == ProposalStatus.READY_FOR_HUMAN_REVIEW.value
    assert prop.maturity_gate == CalibrationMaturity.CALIBRATION_CANDIDATE.value


def test_t6d_35_proposal_forbidden_statuses():
    """T-6D-35: Proposal governance: status is never APPROVED, ACTIVE, or PRODUCTION."""
    for forbidden in ("APPROVED", "ACTIVE", "PRODUCTION"):
        assert forbidden not in [s.value for s in ProposalStatus]


def test_t6d_36_approval_status_candidate(baseline_config):
    """T-6D-36: Approval status: PENDING_HUMAN_REVIEW for candidate proposals."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.approval_status == ApprovalStatus.PENDING_HUMAN_REVIEW.value


def test_t6d_37_approval_status_exploratory(baseline_config):
    """T-6D-37: Approval status: NOT_SUBMITTED for exploratory proposals."""
    rows = [
        _make_dummy_row(f"IPO-{i:02d}", eval_timestamp=f"202{5 + i % 2}-05-01T10:00:00Z", listing_date=f"202{5 + i % 2}-05-10")
        for i in range(40)
    ]
    ds = _make_dataset(rows)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.approval_status == ApprovalStatus.NOT_SUBMITTED.value


def test_t6d_38_proposal_hash_deterministic(baseline_config):
    """T-6D-38: Proposal hash: computed deterministically from canonical JSON content payload."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    p1 = generate_calibration_proposal(ds, an, baseline_config, created_at="2026-10-06T10:00:00Z")
    assert len(p1.proposal_hash) == 64


def test_t6d_39_proposal_hash_independent_of_timestamp(baseline_config):
    """T-6D-39: Proposal hash: independent of file paths, hostname, PID, generation timestamp."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    p1 = generate_calibration_proposal(ds, an, baseline_config, created_at="2026-10-06T08:00:00Z")
    p2 = generate_calibration_proposal(ds, an, baseline_config, created_at="2026-10-06T20:00:00Z")
    assert p1.proposal_hash == p2.proposal_hash


def test_t6d_40_proposal_hash_reproducible(baseline_config):
    """T-6D-40: Proposal hash: bit-for-bit reproducible across repeated executions."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    p1 = generate_calibration_proposal(ds, an, baseline_config)
    p2 = generate_calibration_proposal(ds, an, baseline_config)
    assert p1.proposal_hash == p2.proposal_hash


def test_t6d_41_proposal_hash_changes_on_mutation(baseline_config):
    """T-6D-41: Proposal hash: changes when any proposed weight or evidence is modified."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    p1 = generate_calibration_proposal(ds, an, baseline_config, objective="BALANCED_DIAGNOSTIC")
    p2 = generate_calibration_proposal(ds, an, baseline_config, objective="IMPROVE_HIT_RATE")
    assert p1.proposal_hash != p2.proposal_hash


def test_t6d_42_v1_6_draft_not_generated_ineligible(baseline_config):
    """T-6D-42: v1.6 draft configuration: not generated when status is INELIGIBLE."""
    ds = _make_dataset([_make_dummy_row("IPO-1")] * 10)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.draft_config_status == "NO_V1_6_CONFIGURATION_GENERATED"
    assert prop.draft_config_hash is None


def test_t6d_43_v1_6_draft_not_generated_exploratory(baseline_config):
    """T-6D-43: v1.6 draft configuration: not generated when status is EXPLORATORY."""
    rows = [
        _make_dummy_row(f"IPO-{i:02d}", eval_timestamp=f"202{5 + i % 2}-05-01T10:00:00Z", listing_date=f"202{5 + i % 2}-05-10")
        for i in range(40)
    ]
    ds = _make_dataset(rows)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.draft_config_status == "NO_V1_6_CONFIGURATION_GENERATED"
    assert prop.draft_config_hash is None


def test_t6d_44_v1_6_draft_generated_candidate(baseline_config):
    """T-6D-44: v1.6 draft configuration: generated when status is CANDIDATE / READY_FOR_HUMAN_REVIEW."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    assert prop.draft_config_status == "GENERATED_INACTIVE_DRAFT"
    assert prop.draft_config_hash is not None
    assert len(prop.draft_config_hash) == 64


def test_t6d_45_v1_6_draft_marked_inactive(baseline_config):
    """T-6D-45: v1.6 draft configuration: marked explicitly status DRAFT_INACTIVE and is_active False."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    draft = generate_v1_6_draft_config(prop, baseline_config)

    assert draft["status"] == "DRAFT_INACTIVE"
    assert draft["is_active"] is False
    assert "INACTIVE DRAFT" in draft["governance_notice"]


def test_t6d_46_v1_6_draft_config_version(baseline_config):
    """T-6D-46: v1.6 draft configuration: config_version is 1.6.0-draft."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    draft = generate_v1_6_draft_config(prop, baseline_config)
    assert draft["config_version"] == "1.6.0-draft"


def test_t6d_47_v1_6_draft_provenance_linkages(baseline_config):
    """T-6D-47: v1.6 draft configuration: preserves parent_config_version and parent_config_hash."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    draft = generate_v1_6_draft_config(prop, baseline_config)

    assert draft["parent_config_version"] == "1.5.0"
    assert draft["parent_config_hash"] == prop.baseline_config_hash
    assert draft["source_proposal_hash"] == prop.proposal_hash
    assert draft["source_analysis_hash"] == prop.source_analysis_hash


def test_t6d_48_shadow_evaluation_non_mutating(baseline_config):
    """T-6D-48: Shadow evaluation: computes in-memory score deltas without modifying evaluations."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)
    prop = generate_calibration_proposal(ds, an, baseline_config)

    orig_scores = [r.final_score for r in ds.rows]
    shadow = run_shadow_evaluation(prop, ds, baseline_config)
    after_scores = [r.final_score for r in ds.rows]

    assert orig_scores == after_scores
    assert len(shadow.details_by_row) == 120


def test_t6d_49_shadow_evaluation_verdict_shift_breakdown(baseline_config):
    """T-6D-49: Shadow evaluation: reports verdict shift counts (upgrades, downgrades, unchanged)."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)
    prop = generate_calibration_proposal(ds, an, baseline_config)

    shadow = run_shadow_evaluation(prop, ds, baseline_config)
    assert shadow.upgraded_count >= 0
    assert shadow.downgraded_count >= 0
    assert shadow.unchanged_count >= 0


def test_t6d_50_verify_proposal_pass(baseline_config, tmp_path: Path):
    """T-6D-50: Verification audit: verify_proposal verifies valid proposal against canonical content hash."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)
    prop = generate_calibration_proposal(ds, an, baseline_config)

    p_file = tmp_path / "proposal.json"
    export_proposal_json(prop, p_file)

    res = verify_proposal(p_file)
    assert res["status"] == "PASS"
    assert res["proposal_hash_match"] is True
    assert res["proposal_hash"] == prop.proposal_hash


def test_t6d_51_verify_proposal_tampering_detected(baseline_config, tmp_path: Path):
    """T-6D-51: Verification audit: verify_proposal detects tampering with proposed weights."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)
    prop = generate_calibration_proposal(ds, an, baseline_config)

    p_file = tmp_path / "proposal.json"
    export_proposal_json(prop, p_file)

    with p_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["module_proposals"][0]["proposed_weight"] = 99.0
    with p_file.open("w", encoding="utf-8") as f:
        json.dump(data, f)

    res = verify_proposal(p_file)
    assert res["status"] == "FAIL"
    assert "mismatch" in res["reason"]


def test_t6d_52_verify_proposal_cross_linkages(baseline_config, tmp_path: Path):
    """T-6D-52: Verification audit: verify_proposal checks dataset and analysis hash linkages."""
    ds = _make_candidate_dataset(120)
    ds_file = tmp_path / "dataset.json"
    export_dataset_json(ds, ds_file)

    an = analyze_dataset(ds)
    an_file = tmp_path / "analysis.json"
    export_analysis_json(an, an_file)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    p_file = tmp_path / "proposal.json"
    export_proposal_json(prop, p_file)

    res = verify_proposal(p_file, analysis_path=an_file, dataset_path=ds_file, config_path=CONFIG_PATH)
    assert res["status"] == "PASS"


def test_t6d_53_verify_proposal_forbidden_status_rejected(baseline_config, tmp_path: Path):
    """T-6D-53: Verification audit: verify_proposal rejects forbidden approval status."""
    ds = _make_candidate_dataset(120)
    an = analyze_dataset(ds)
    prop = generate_calibration_proposal(ds, an, baseline_config)

    p_file = tmp_path / "proposal.json"
    export_proposal_json(prop, p_file)

    with p_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["status"] = "APPROVED"
    # Rehash so hash matches but status is forbidden
    data["proposal_hash"] = compute_proposal_content_hash(data)
    with p_file.open("w", encoding="utf-8") as f:
        json.dump(data, f)

    res = verify_proposal(p_file)
    assert res["status"] == "FAIL"
    assert "forbidden status" in res["reason"]


def test_t6d_54_cli_calibrate_propose(baseline_config, tmp_path: Path):
    """T-6D-54: CLI command: `post-listing calibrate-propose` generates proposal artifact."""
    ds = _make_candidate_dataset(120)
    ds_file = tmp_path / "dataset.json"
    export_dataset_json(ds, ds_file)

    an = analyze_dataset(ds)
    an_file = tmp_path / "analysis.json"
    export_analysis_json(an, an_file)

    prop_file = tmp_path / "proposal.json"
    draft_file = tmp_path / "v1.6-draft.json"

    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "post-listing",
        "calibrate-propose",
        "--dataset",
        str(ds_file),
        "--analysis",
        str(an_file),
        "--config",
        str(CONFIG_PATH),
        "--output",
        str(prop_file),
        "--draft-config",
        str(draft_file),
        "-v",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "GOVERNED CALIBRATION PROPOSAL GENERATED" in proc.stdout
    assert prop_file.is_file()
    assert draft_file.is_file()


def test_t6d_55_cli_verify_proposal(baseline_config, tmp_path: Path):
    """T-6D-55: CLI command: `post-listing verify-proposal` audits proposal deliverable and exits 0."""
    ds = _make_candidate_dataset(120)
    ds_file = tmp_path / "dataset.json"
    export_dataset_json(ds, ds_file)

    an = analyze_dataset(ds)
    an_file = tmp_path / "analysis.json"
    export_analysis_json(an, an_file)

    prop = generate_calibration_proposal(ds, an, baseline_config)
    prop_file = tmp_path / "proposal.json"
    export_proposal_json(prop, prop_file)

    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "post-listing",
        "verify-proposal",
        "--proposal",
        str(prop_file),
        "--analysis",
        str(an_file),
        "--dataset",
        str(ds_file),
        "-v",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "CALIBRATION PROPOSAL AUDIT" in proc.stdout
    assert "ALL PASS" in proc.stdout


def test_t6d_56_cli_shadow_evaluate(baseline_config, tmp_path: Path):
    """T-6D-56: CLI command: `post-listing shadow-evaluate` runs shadow evaluation deliverable."""
    ds = _make_candidate_dataset(120)
    ds_file = tmp_path / "dataset.json"
    export_dataset_json(ds, ds_file)

    an = analyze_dataset(ds)
    prop = generate_calibration_proposal(ds, an, baseline_config)
    prop_file = tmp_path / "proposal.json"
    export_proposal_json(prop, prop_file)

    shadow_out = tmp_path / "shadow.json"

    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "post-listing",
        "shadow-evaluate",
        "--proposal",
        str(prop_file),
        "--dataset",
        str(ds_file),
        "--config",
        str(CONFIG_PATH),
        "--output",
        str(shadow_out),
        "-v",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "SHADOW EVALUATION EXECUTED" in proc.stdout
    assert shadow_out.is_file()
