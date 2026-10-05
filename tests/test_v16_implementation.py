"""Acceptance test suite for Phase 7: Authorized v1.6 Implementation & Promotion Preparation.

Covers T-7-01 through T-7-45:
- Proposal verification and explicit Ramki authorization
- Exact provenance linkage (Dataset -> Analysis -> Proposal -> v1.6 -> Shadow)
- Baseline v1.5 preservation and Frozen Core integrity
- Configuration diff (scoring deltas, metadata deltas, unchanged sections)
- v1.6 validation, schema reconciliation, and inactive lifecycle state
- Deterministic shadow evaluation, score deltas, verdict transitions, and non-regression
- CLI commands (`config verify`, `config diff`, `post-listing shadow-evaluate`)
- Tamper detection, out-of-scope mutation rejection, and fail-closed error handling
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

if "." not in sys.path:
    sys.path.insert(0, ".")
if "engine" not in sys.path:
    sys.path.insert(0, "engine")

try:
    from tests.test_calibration_phase6d import _make_candidate_dataset
except ImportError:
    from test_calibration_phase6d import _make_candidate_dataset

try:
    from ipo_screening.config_validation import check_config
    from ipo_screening.hashing import canonical_json, sha256_of
    from ipo_screening.post_listing import (
        ApprovalStatus,
        BacktestDataset,
        BacktestDatasetManifest,
        BacktestDatasetRow,
        CalibrationProposal,
        ConfigDiffEntry,
        ConfigDiffReport,
        FROZEN_CORE_HASHES,
        GOLDEN_RESULT_HASH,
        V16ShadowReport,
        V1_5_BASELINE_VERSION,
        V1_5_CANONICAL_HASH,
        V1_5_CONFIG_PATH,
        V1_5_POLICY_CONTENT_HASH,
        V1_5_RAW_SHA256,
        V1_6_CONFIG_PATH,
        V1_6_CONFIG_VERSION,
        compute_config_diff,
        compute_proposal_content_hash,
        export_dataset_json,
        generate_v1_6_config,
        load_approved_proposal,
        load_v1_5_config,
        load_v1_6_config,
        rescore_row,
        run_v1_6_shadow_evaluation,
        verify_frozen_core,
        verify_golden_result,
        verify_proposal,
        verify_v1_6_implementation,
    )
except ImportError:
    from engine.ipo_screening.config_validation import check_config
    from engine.ipo_screening.hashing import canonical_json, sha256_of
    from engine.ipo_screening.post_listing import (
        ApprovalStatus,
        BacktestDataset,
        BacktestDatasetManifest,
        BacktestDatasetRow,
        CalibrationProposal,
        ConfigDiffEntry,
        ConfigDiffReport,
        FROZEN_CORE_HASHES,
        GOLDEN_RESULT_HASH,
        V16ShadowReport,
        V1_5_BASELINE_VERSION,
        V1_5_CANONICAL_HASH,
        V1_5_CONFIG_PATH,
        V1_5_POLICY_CONTENT_HASH,
        V1_5_RAW_SHA256,
        V1_6_CONFIG_PATH,
        V1_6_CONFIG_VERSION,
        compute_config_diff,
        compute_proposal_content_hash,
        export_dataset_json,
        generate_v1_6_config,
        load_approved_proposal,
        load_v1_5_config,
        load_v1_6_config,
        rescore_row,
        run_v1_6_shadow_evaluation,
        verify_frozen_core,
        verify_golden_result,
        verify_proposal,
        verify_v1_6_implementation,
    )


@pytest.fixture
def baseline_v15_config() -> Dict[str, Any]:
    return load_v1_5_config()


@pytest.fixture
def candidate_v16_config() -> Dict[str, Any]:
    return load_v1_6_config()


@pytest.fixture
def approved_proposal() -> CalibrationProposal:
    return load_approved_proposal()


@pytest.fixture
def sample_dataset() -> BacktestDataset:
    return _make_candidate_dataset(120)


# =============================================================================
# 1. Proposal & Authorization Verification (T-7-01 to T-7-04)
# =============================================================================


def test_t7_01_proposal_verification():
    """T-7-01: Proposal verification: durable approved proposal exists and passes cryptographic audit."""
    assert Path("config/calibration-proposal.v1.6.0.json").is_file()
    res = verify_proposal("config/calibration-proposal.v1.6.0.json", config_path="config/ipo-config.v1.5.0.json")
    assert res.get("status") == "PASS"
    assert res.get("proposal_hash_match") is True


def test_t7_02_approval_verification(approved_proposal):
    """T-7-02: Approval verification: proposal reflects explicit authorization by Ramki."""
    assert approved_proposal.approval_status == ApprovalStatus.APPROVED.value
    assert "RAMKI" in approved_proposal.recommendation.upper()


def test_t7_03_proposal_hash_linkage(approved_proposal):
    """T-7-03: Proposal hash linkage: proposal records valid dataset and analysis hashes."""
    assert approved_proposal.source_dataset_hash
    assert len(approved_proposal.source_dataset_hash) == 64
    assert approved_proposal.source_analysis_hash
    assert len(approved_proposal.source_analysis_hash) == 64
    assert approved_proposal.baseline_config_hash == V1_5_POLICY_CONTENT_HASH


def test_t7_04_baseline_config_hash(baseline_v15_config):
    """T-7-04: Baseline configuration hash: verified against authoritative constants."""
    raw_hash = hashlib.sha256(Path(V1_5_CONFIG_PATH).read_bytes()).hexdigest()
    assert raw_hash == V1_5_RAW_SHA256
    canon_hash = sha256_of(canonical_json(baseline_v15_config))
    assert canon_hash == V1_5_CANONICAL_HASH


# =============================================================================
# 2. v1.6 Generation & Baseline Preservation (T-7-05 to T-7-07)
# =============================================================================


def test_t7_05_v1_6_generation(approved_proposal, baseline_v15_config):
    """T-7-05: v1.6 generation: generate_v1_6_config creates schema-compatible v1.6 dict."""
    cfg = generate_v1_6_config(approved_proposal, baseline_v15_config)
    assert cfg["config_version"] == V1_6_CONFIG_VERSION
    assert cfg["status"] == "IMPLEMENTED_INACTIVE"
    assert cfg["is_active"] is False
    assert cfg["parent_config_version"] == V1_5_BASELINE_VERSION
    assert cfg["source_proposal_hash"] == approved_proposal.proposal_hash


def test_t7_06_v1_5_preservation():
    """T-7-06: v1.5 preservation: config/ipo-config.v1.5.0.json remains byte-for-byte identical."""
    p = Path(V1_5_CONFIG_PATH)
    assert p.is_file()
    actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    assert actual_hash == V1_5_RAW_SHA256


def test_t7_07_exact_configuration_diff(baseline_v15_config, candidate_v16_config, approved_proposal):
    """T-7-07: Configuration diff: reports exact changed fields and unchanged sections."""
    diff = compute_config_diff(baseline_v15_config, candidate_v16_config, approved_proposal)
    assert diff.is_approved_scope_only is True
    assert diff.changed_scoring_fields_count == 2
    assert len(diff.unchanged_sections) == 15
    assert "currency" in diff.unchanged_sections
    assert "knockouts" in diff.unchanged_sections


# =============================================================================
# 3. Policy & Scoring Adjustments (T-7-08 to T-7-13)
# =============================================================================


def test_t7_08_approved_weight_changes(candidate_v16_config):
    """T-7-08: Approved weight changes: Module A=30, Module B=15, C-F unchanged, sum=100.0."""
    mods = {m["id"]: m["max"] for m in candidate_v16_config.get("modules", [])}
    assert mods["A"] == 30
    assert mods["B"] == 15
    assert mods["C"] == 15
    assert mods["D"] == 15
    assert mods["E"] == 15
    assert mods["F"] == 10
    assert sum(mods.values()) == 100


def test_t7_09_approved_threshold_changes(baseline_v15_config, candidate_v16_config):
    """T-7-09: Threshold implementation: thresholds match approved proposal (unchanged)."""
    assert candidate_v16_config.get("thresholds") == baseline_v15_config.get("thresholds")
    assert candidate_v16_config.get("verdict") == baseline_v15_config.get("verdict")


def test_t7_10_knockout_firewall(baseline_v15_config, candidate_v16_config):
    """T-7-10: Knockout firewall: knockouts are 100% identical between v1.5 and v1.6."""
    assert candidate_v16_config.get("knockouts") == baseline_v15_config.get("knockouts")
    assert len(candidate_v16_config.get("knockouts", [])) == 6


def test_t7_11_configuration_schema(candidate_v16_config):
    """T-7-11: Configuration schema: v1.6 passes check_config with zero errors."""
    report = check_config(candidate_v16_config)
    assert report.ok is True
    assert len(report.errors) == 0


def test_t7_12_configuration_hash(candidate_v16_config):
    """T-7-12: Configuration hash: deterministic SHA-256 present and verifiable."""
    assert "configuration_hash" in candidate_v16_config
    assert len(candidate_v16_config["configuration_hash"]) == 64


def test_t7_13_provenance_metadata(candidate_v16_config, approved_proposal):
    """T-7-13: Provenance metadata: parent configuration and proposal linkages verified."""
    assert candidate_v16_config.get("parent_config_version") == "1.5.0"
    assert candidate_v16_config.get("parent_config_hash") == approved_proposal.baseline_config_hash
    assert candidate_v16_config.get("source_proposal_hash") == approved_proposal.proposal_hash
    assert candidate_v16_config.get("source_analysis_hash") == approved_proposal.source_analysis_hash
    assert candidate_v16_config.get("source_dataset_hash") == approved_proposal.source_dataset_hash


# =============================================================================
# 4. Shadow Evaluation & Determinism (T-7-14 to T-7-22)
# =============================================================================


def test_t7_14_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-14: Shadow evaluation: executes pure in-memory evaluation across dataset."""
    res = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    assert res.total_evaluated == 120
    assert len(res.details_by_row) == 120


def test_t7_15_score_delta(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-15: Score delta: calculates exact score delta for every evaluation."""
    res = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    for row in res.details_by_row:
        expected_delta = round(row["v1_6_score"] - row["baseline_score"], 2)
        assert abs(row["score_delta"] - expected_delta) < 1e-6


def test_t7_16_verdict_delta(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-16: Verdict delta: categorizes upgrades, downgrades, and unchanged verdicts."""
    res = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    assert res.upgraded_count + res.downgraded_count + res.unchanged_count == res.total_evaluated
    assert res.verdict_shifts_count == res.upgraded_count + res.downgraded_count


def test_t7_17_knockout_delta(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-17: Knockout delta: exactly zero newly knocked out and zero knockout removed."""
    res = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    assert res.newly_knocked_out_count == 0
    assert res.knockout_removed_count == 0


def test_t7_18_historical_non_mutation(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-18: Historical non-mutation: inputs and dataset rows remain untouched."""
    orig_scores = [r.final_score for r in sample_dataset.rows]
    _ = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    after_scores = [r.final_score for r in sample_dataset.rows]
    assert orig_scores == after_scores


def test_t7_19_golden_result_preservation():
    """T-7-19: Golden result preservation: golden evaluation hash remains bit-for-bit identical."""
    ok, actual_h = verify_golden_result()
    assert ok is True
    assert actual_h == GOLDEN_RESULT_HASH


def test_t7_20_deterministic_replay(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-20: Deterministic replay: shadow evaluation replayed produces identical metrics."""
    res1 = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    res2 = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    assert res1.score_mean_delta == res2.score_mean_delta
    assert res1.verdict_shifts_count == res2.verdict_shifts_count
    assert res1.details_by_row == res2.details_by_row


def test_t7_21_repeated_configuration_hashing(candidate_v16_config):
    """T-7-21: Repeated configuration hashing: 10 repeated hashing runs produce identical hash."""
    hashes = [sha256_of(canonical_json(candidate_v16_config)) for _ in range(10)]
    assert len(set(hashes)) == 1


def test_t7_22_repeated_evaluation_hashing(sample_dataset):
    """T-7-22: Repeated evaluation rescoring: individual row scores are 100% deterministic."""
    weights = {"A": 30.0, "B": 15.0, "C": 15.0, "D": 15.0, "E": 15.0, "F": 10.0}
    scores_1 = [rescore_row(r, weights) for r in sample_dataset.rows]
    scores_2 = [rescore_row(r, weights) for r in sample_dataset.rows]
    assert scores_1 == scores_2


# =============================================================================
# 5. Non-Regression & Quality Assertions (T-7-23 to T-7-28)
# =============================================================================


def test_t7_23_regression_against_v1_5(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-23: Regression verification: downside protection, holdout, and vintage pass."""
    res = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    assert res.downside_protection_passed is True
    assert res.holdout_stability_passed is True
    assert res.vintage_robustness_passed is True


def test_t7_24_unknown_preservation():
    """T-7-24: Unknown preservation: missing values map to UNKNOWN in v1.6 criteria."""
    from ipo_screening.derived import DerivedMetrics, MetricValue
    from ipo_screening.scoring import evaluate_criterion

    criterion_spec = {
        "id": "revenue_cagr",
        "name": "Revenue CAGR",
        "metric": "revenue_cagr",
        "max": 6.0,
        "rule": {
            "type": "bands",
            "metric": "revenue_cagr",
            "bands": [
                {"min": 0.20, "score": 6.0},
                {"min": 0.10, "score": 3.0},
                {"min": None, "score": 0.0},
            ],
        },
    }
    derived = DerivedMetrics(metrics={"revenue_cagr": MetricValue(metric_id="revenue_cagr", state="UNKNOWN", value=None)})
    res = evaluate_criterion(criterion_spec, "A", derived, [])
    assert res.state == "UNKNOWN"
    assert res.score is None  # Must never be defaulted to zero


def test_t7_25_missing_data_semantics():
    """T-7-25: Missing data semantics: critical metrics without data fail-closed."""
    from ipo_screening.derived import DerivedMetrics
    from ipo_screening.knockouts import evaluate_knockouts

    config = {
        "knockouts": [
            {
                "id": "K1",
                "label": "Promoter Selling Ratio",
                "when": {"op": ">", "field": "ofs_promoter_ratio", "value": 0.5},
            }
        ]
    }
    derived = DerivedMetrics(metrics={})
    results = evaluate_knockouts(config, derived)
    assert len(results) == 1
    assert results[0].state == "UNVERIFIED"


def test_t7_26_holdout_comparison(approved_proposal):
    """T-7-26: Holdout comparison: proposal records holdout diagnostic results."""
    assert "baseline_spearman_rho_1w" in approved_proposal.holdout_results
    assert approved_proposal.holdout_results["holdout_period"] == "2026"


def test_t7_27_vintage_comparison(approved_proposal):
    """T-7-27: Vintage comparison: proposal records vintage diagnostic results."""
    assert "represented_vintages" in approved_proposal.vintage_results
    assert len(approved_proposal.vintage_results["represented_vintages"]) >= 3


def test_t7_28_downside_comparison(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-28: Downside comparison: no row with AVOID baseline receives APPLY verdict."""
    res = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    for r in res.details_by_row:
        if r["baseline_verdict"] == "AVOID":
            assert r["v1_6_verdict"] != "APPLY"


# =============================================================================
# 6. CLI Commands & Verification (T-7-29 to T-7-33)
# =============================================================================


def test_t7_29_cli_config_verify():
    """T-7-29: CLI config verify: runs deterministic verification and exits 0."""
    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "config",
        "verify",
        "--config",
        "config/ipo-config.v1.6.0.json",
        "--proposal",
        "config/calibration-proposal.v1.6.0.json",
        "--baseline",
        "config/ipo-config.v1.5.0.json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "V1.6 CONFIGURATION VERIFICATION: PASS" in proc.stdout


def test_t7_30_cli_config_diff():
    """T-7-30: CLI config diff: runs diff tool and exits 0."""
    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "config",
        "diff",
        "--baseline",
        "config/ipo-config.v1.5.0.json",
        "--candidate",
        "config/ipo-config.v1.6.0.json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "CONFIGURATION DIFF: 1.5.0 -> 1.6.0" in proc.stdout
    assert "modules.A.max: 25 -> 30" in proc.stdout
    assert "modules.B.max: 20 -> 15" in proc.stdout


def test_t7_31_cli_shadow_evaluate_config(sample_dataset, tmp_path):
    """T-7-31: CLI shadow evaluate with configs: runs shadow evaluation and exits 0."""
    ds_path = tmp_path / "dataset.json"
    export_dataset_json(sample_dataset, ds_path)

    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "post-listing",
        "shadow-evaluate",
        "--config-v1-5",
        "config/ipo-config.v1.5.0.json",
        "--config-v1-6",
        "config/ipo-config.v1.6.0.json",
        "--dataset",
        str(ds_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "V1.6 SHADOW EVALUATION EXECUTED (IN-MEMORY ONLY)" in proc.stdout
    assert "Total Evaluated:      120" in proc.stdout


def test_t7_32_cli_shadow_evaluate_proposal(sample_dataset, tmp_path):
    """T-7-32: CLI shadow evaluate with proposal: runs proposal shadow evaluation and exits 0."""
    ds_path = tmp_path / "dataset.json"
    export_dataset_json(sample_dataset, ds_path)

    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "post-listing",
        "shadow-evaluate",
        "--proposal",
        "config/calibration-proposal.v1.6.0.json",
        "--dataset",
        str(ds_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "SHADOW EVALUATION EXECUTED (IN-MEMORY ONLY)" in proc.stdout


def test_t7_33_cli_verify_proposal():
    """T-7-33: CLI verify proposal: verifies proposal integrity and exits 0."""
    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "post-listing",
        "verify-proposal",
        "--proposal",
        "config/calibration-proposal.v1.6.0.json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Audit Status:         ALL PASS" in proc.stdout


# =============================================================================
# 7. Frozen Core & Security Firewall (T-7-34 to T-7-39)
# =============================================================================


def test_t7_34_frozen_core_verification():
    """T-7-34: Frozen core verification: all six engine files remain bit-for-bit identical."""
    ok, details = verify_frozen_core()
    assert ok is True, f"Frozen core mismatch: {details}"
    assert len(details) == 6
    assert all(details.values())


def test_t7_35_unauthorized_field_rejection(baseline_v15_config, candidate_v16_config):
    """T-7-35: Unauthorized field rejection: adding unapproved field fails diff check."""
    corrupt_cfg = copy.deepcopy(candidate_v16_config)
    corrupt_cfg["unauthorized_bonus"] = 50.0
    diff = compute_config_diff(baseline_v15_config, corrupt_cfg)
    assert diff.is_approved_scope_only is False
    assert any(cf.path == "unauthorized_bonus" and cf.approved_scope == "OUT_OF_APPROVED_SCOPE" for cf in diff.changed_fields)


def test_t7_36_out_of_scope_mutation_rejection(candidate_v16_config, tmp_path):
    """T-7-36: Out of scope mutation rejection: mutating knockouts fails verification."""
    corrupt_cfg = copy.deepcopy(candidate_v16_config)
    corrupt_cfg["knockouts"][0]["id"] = "K_UNAUTHORIZED"
    corrupt_path = tmp_path / "corrupt_v16.json"
    corrupt_path.write_text(json.dumps(corrupt_cfg), encoding="utf-8")

    res = verify_v1_6_implementation(v1_6_path=corrupt_path)
    assert res.get("status") == "FAIL"
    assert any("Knockouts modified" in f for f in res.get("failures", []))


def test_t7_37_active_pointer_preservation():
    """T-7-37: Active pointer preservation: CLI defaults remain pointing to v1.5.0."""
    from engine.tools.ipo_screen import DEFAULT_CONFIG_PATH
    assert DEFAULT_CONFIG_PATH == "config/ipo-config.v1.5.0.json"


def test_t7_38_v1_6_inactive_state_enforcement(candidate_v16_config):
    """T-7-38: v1.6 inactive state enforcement: is_active is strictly False."""
    assert candidate_v16_config["is_active"] is False
    assert candidate_v16_config["status"] == "IMPLEMENTED_INACTIVE"


def test_t7_39_provenance_chain_verification():
    """T-7-39: Provenance chain verification: Dataset -> Analysis -> Proposal -> v1.6 is verified."""
    report = verify_v1_6_implementation()
    assert report.get("status") == "PASS"
    assert report.get("frozen_core_verified") is True
    assert report.get("golden_result_verified") is True


# =============================================================================
# 8. Malformed Configurations, Tamper Detection & Workflow (T-7-40 to T-7-45)
# =============================================================================


def test_t7_40_malformed_configuration_rejection(tmp_path):
    """T-7-40: Malformed configuration rejection: invalid JSON is rejected cleanly."""
    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text("{ incomplete json ...", encoding="utf-8")

    cmd = [
        sys.executable,
        "engine/tools/ipo_screen.py",
        "config",
        "verify",
        "--config",
        str(malformed_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode != 0


def test_t7_41_tamper_detection(candidate_v16_config, tmp_path):
    """T-7-41: Tamper detection: tampering with module weights without updating hash fails verification."""
    tampered_cfg = copy.deepcopy(candidate_v16_config)
    tampered_cfg["modules"][0]["max"] = 35  # Unauthorized weight change
    tampered_cfg["modules"][1]["max"] = 10
    tampered_path = tmp_path / "tampered.json"
    tampered_path.write_text(json.dumps(tampered_cfg), encoding="utf-8")

    res = verify_v1_6_implementation(v1_6_path=tampered_path)
    assert res.get("status") == "FAIL"


def test_t7_42_end_to_end_v15_v16_workflow(sample_dataset, baseline_v15_config, candidate_v16_config):
    """T-7-42: End-to-end workflow: verifies v1.5 baseline, v1.6 implementation, diff, and shadow eval."""
    # 1. Baseline check
    assert baseline_v15_config["config_version"] == "1.5.0"
    # 2. Candidate check
    assert candidate_v16_config["config_version"] == "1.6.0"
    # 3. Diff check
    diff = compute_config_diff(baseline_v15_config, candidate_v16_config)
    assert diff.is_approved_scope_only is True
    # 4. Verification check
    ver_res = verify_v1_6_implementation()
    assert ver_res["status"] == "PASS"
    # 5. Shadow rescoring check
    shadow_res = run_v1_6_shadow_evaluation(sample_dataset, baseline_v15_config, candidate_v16_config)
    assert shadow_res.total_evaluated == len(sample_dataset.rows)


def test_t7_43_unapproved_proposal_rejection(baseline_v15_config):
    """T-7-43: Unapproved proposal rejection: generating v1.6 from unapproved proposal raises ValueError."""
    fake_proposal_dict = {
        "proposal_version": "1.0.0",
        "status": "READY_FOR_HUMAN_REVIEW",
        "approval_status": "PENDING_HUMAN_REVIEW",  # Not APPROVED
        "source_dataset_hash": "a" * 64,
        "source_analysis_hash": "b" * 64,
        "baseline_config_hash": "c" * 64,
        "proposal_hash": "d" * 64,
        "module_proposals": [],
        "threshold_proposals": [],
        "knockout_proposals": [],
        "verdict_proposals": [],
    }
    fake_prop = CalibrationProposal.from_dict(fake_proposal_dict)
    with pytest.raises(ValueError, match="Cannot generate authorized v1.6 config"):
        generate_v1_6_config(fake_prop, baseline_v15_config)


def test_t7_44_module_weight_sum_assertion(candidate_v16_config):
    """T-7-44: Module weight sum assertion: sum of module weights strictly equals 100.0."""
    total = sum(m["max"] for m in candidate_v16_config["modules"])
    assert total == 100.0


def test_t7_45_diff_unchanged_sections_count(baseline_v15_config, candidate_v16_config):
    """T-7-45: Diff unchanged sections count: exactly 15 unchanged policy sections recorded."""
    diff = compute_config_diff(baseline_v15_config, candidate_v16_config)
    assert len(diff.unchanged_sections) == 15
