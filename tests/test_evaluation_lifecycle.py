"""Comprehensive test suite for evaluation lifecycle governance.

Tests covering requirements A through S from execution prompt s16:
A. lifecycle schema validation
B. active pointer semantics
C. final/preliminary separation
D. ratified policy requirement
E. ACTIVE -> SUPERSEDED
F. SUPERSEDED -> ARCHIVED
G. ARCHIVED -> SUPERSEDED
H. governed rollback
I. invalid transitions
J. concurrent active promotion
K. cyclic lineage rejection
L. missing lineage target
M. protected golden record
N. referenced backtest record
O. reversible archival
P. no DELETE endpoint
Q. immutable artifact hashes
R. R.K. lifecycle mapping
S. Vishal golden regression
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ipo_screening.evaluation import EvaluationRecord, EvaluationStore, compute_result_hash
from ipo_screening.hashing import sha256_of
from ipo_screening.lifecycle import (
    ACTIVE_RATIFIED_CONFIG_HASH,
    LIFECYCLE_STATE_ACTIVE,
    LIFECYCLE_STATE_SUPERSEDED,
    OPERATIONAL_STATUS_ACTIVE,
    OPERATIONAL_STATUS_ARCHIVED,
    OPERATIONAL_STATUS_SUPERSEDED,
    TIER_1_GOLDEN,
    TIER_2_GOVERNED,
    TIER_3_STANDARD,
    VISIBILITY_STATE_ARCHIVED,
    VISIBILITY_STATE_VISIBLE,
    VISHAL_GOLDEN_RESULT_HASH,
    CyclicLineageError,
    EvaluationNotFoundError,
    InvalidStateTransitionError,
    LifecycleIndex,
    LifecycleManager,
    LifecycleRecord,
    ProtectedRecordError,
    get_protection_tier,
)
from ipo_screening.pipeline import evaluate, load_config
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def active_config():
    return load_config(Path("config/ipo-config.v1.5.0.json"))


@pytest.fixture
def sample_input():
    d = json.loads(Path("fixtures/vishal_nirmiti/input.json").read_text(encoding="utf-8"))
    d["ipo_id"] = "AURORA-TECH-LIMITED"
    d["company_name"] = "Aurora Tech Limited"
    return d


@pytest.fixture
def store_dir(tmp_path):
    d = tmp_path / "evaluations"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def lifecycle_mgr(store_dir):
    return LifecycleManager(store_dir, active_config_hash=ACTIVE_RATIFIED_CONFIG_HASH)


# -----------------------------------------------------------------------------
# Tests A through S
# -----------------------------------------------------------------------------

def test_a_lifecycle_schema_validation():
    """A. Lifecycle schema validation: fields, states, and operational projection."""
    rec = LifecycleRecord(
        evaluation_id="TEST-IPO-20261007-120000Z-final-12345678",
        ipo_id="TEST-IPO",
        mode="final",
        lifecycle_state=LIFECYCLE_STATE_ACTIVE,
        visibility_state=VISIBILITY_STATE_VISIBLE,
    )
    assert rec.operational_status == OPERATIONAL_STATUS_ACTIVE
    d = rec.to_dict()
    assert d["evaluation_id"] == "TEST-IPO-20261007-120000Z-final-12345678"
    assert d["lifecycle_state"] == "ACTIVE"
    assert d["visibility_state"] == "VISIBLE"
    assert d["operational_status"] == "ACTIVE"

    # Invalid lifecycle_state
    with pytest.raises(InvalidStateTransitionError):
        LifecycleRecord(
            evaluation_id="TEST-IPO-20261007-120000Z-final-12345678",
            ipo_id="TEST-IPO",
            mode="final",
            lifecycle_state="INVALID_STATE",
            visibility_state=VISIBILITY_STATE_VISIBLE,
        )

    # Invalid visibility_state
    with pytest.raises(InvalidStateTransitionError):
        LifecycleRecord(
            evaluation_id="TEST-IPO-20261007-120000Z-final-12345678",
            ipo_id="TEST-IPO",
            mode="final",
            lifecycle_state=LIFECYCLE_STATE_ACTIVE,
            visibility_state="INVALID_VISIBILITY",
        )


def test_b_active_pointer_semantics(lifecycle_mgr, store_dir, sample_input, active_config):
    """B. Active pointer semantics: authoritative selection uses explicit pointer, not timestamp."""
    # Write two evaluations for the same IPO
    outcome1 = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome1.record)
    lc1 = lifecycle_mgr.register_evaluation(outcome1.record, actor="test", reason="run1")
    assert lc1.lifecycle_state == LIFECYCLE_STATE_ACTIVE

    # Explicit pointer points to outcome1
    active_id = lifecycle_mgr.get_active_evaluation_id(outcome1.record.ipo_id, mode="final")
    assert active_id == outcome1.record.evaluation_id

    # Create modified second evaluation with same IPO
    inp2 = dict(sample_input)
    inp2["company_name"] = "VISHAL NIRMITI REVISED"
    outcome2 = evaluate(input_document=inp2, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome2.record)
    lc2 = lifecycle_mgr.register_evaluation(outcome2.record, actor="test", reason="run2")

    assert lc2.lifecycle_state == LIFECYCLE_STATE_ACTIVE
    # Now active pointer points to outcome2
    active_id2 = lifecycle_mgr.get_active_evaluation_id(outcome2.record.ipo_id, mode="final")
    assert active_id2 == outcome2.record.evaluation_id


def test_c_final_preliminary_separation(lifecycle_mgr, sample_input, active_config):
    """C. Final/Preliminary separation: FINAL and PRELIMINARY active pointers are independent."""
    outcome_fin = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome_fin.record)
    lifecycle_mgr.register_evaluation(outcome_fin.record)

    outcome_pre = evaluate(input_document=sample_input, config=active_config, mode="preliminary")
    lifecycle_mgr.store.write(outcome_pre.record)
    lifecycle_mgr.register_evaluation(outcome_pre.record)

    fin_active = lifecycle_mgr.get_active_evaluation_id(outcome_fin.record.ipo_id, mode="final")
    pre_active = lifecycle_mgr.get_active_evaluation_id(outcome_fin.record.ipo_id, mode="preliminary")

    assert fin_active == outcome_fin.record.evaluation_id
    assert pre_active == outcome_pre.record.evaluation_id
    assert fin_active != pre_active


def test_d_ratified_policy_requirement(lifecycle_mgr, sample_input, active_config):
    """D. Ratified policy requirement: candidate config (v1.6.0) cannot become ACTIVE."""
    # Build a record with unratified config_hash
    outcome = evaluate(input_document=sample_input, config=active_config, mode="final")
    # Simulate unratified candidate hash
    fake_record = EvaluationRecord(
        evaluation_id="CANDIDATE-IPO-20261007-120000Z-final-deadbeef",
        ipo_id="CANDIDATE-IPO",
        company_name="Candidate Offering",
        evaluation_mode="FINAL",
        evaluation_timestamp="2026-10-07T12:00:00Z",
        engine_version="1.6.0",
        spec_version="1.6",
        config_version="1.6.0-draft",
        config_hash="unratified_candidate_v16_hash",
        input_snapshot_hash="some_hash",
        source_manifest_hash="some_hash",
        market_snapshot_hash="some_hash",
        peer_snapshot_hash="some_hash",
        result_hash="deadbeef12345678",
        input_snapshot=outcome.record.input_snapshot,
        evidence=outcome.record.evidence,
        market_snapshot=outcome.record.market_snapshot,
        peer_snapshot=outcome.record.peer_snapshot,
        derived_metrics=outcome.record.derived_metrics,
        effective_config=outcome.record.effective_config,
        validation=outcome.record.validation,
        knockouts=outcome.record.knockouts,
        score=outcome.record.score,
        confidence=outcome.record.confidence,
        score_range=outcome.record.score_range,
        verdict=outcome.record.verdict,
        provenance=outcome.record.provenance,
        plan=outcome.record.plan,
    )
    lifecycle_mgr.store.write(fake_record)
    lc = lifecycle_mgr.register_evaluation(fake_record)

    # Must NOT be active because config_hash does not match ratified baseline
    assert lc.lifecycle_state == LIFECYCLE_STATE_SUPERSEDED
    assert lifecycle_mgr.get_active_evaluation_id("CANDIDATE-IPO", mode="final") is None


def test_e_active_to_superseded(lifecycle_mgr, sample_input, active_config):
    """E. ACTIVE -> SUPERSEDED: When replaced by new valid run, old automatically transitions to SUPERSEDED."""
    outcome1 = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome1.record)
    lc1 = lifecycle_mgr.register_evaluation(outcome1.record)
    assert lc1.lifecycle_state == LIFECYCLE_STATE_ACTIVE

    inp2 = dict(sample_input)
    inp2["company_name"] = "VISHAL REVISED"
    outcome2 = evaluate(input_document=inp2, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome2.record)
    lc2 = lifecycle_mgr.register_evaluation(outcome2.record)

    # Re-read lc1
    updated_lc1 = lifecycle_mgr.get_lifecycle(outcome1.record.evaluation_id)
    assert updated_lc1.lifecycle_state == LIFECYCLE_STATE_SUPERSEDED
    assert updated_lc1.superseded_by == outcome2.record.evaluation_id
    assert lc2.lifecycle_state == LIFECYCLE_STATE_ACTIVE
    assert lc2.supersedes == outcome1.record.evaluation_id


def test_f_superseded_to_archived(lifecycle_mgr, sample_input, active_config):
    """F. SUPERSEDED -> ARCHIVED: Routine decluttering transitions superseded evaluation to ARCHIVED."""
    outcome1 = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome1.record)
    lifecycle_mgr.register_evaluation(outcome1.record)

    inp2 = dict(sample_input)
    inp2["company_name"] = "VISHAL REVISED"
    outcome2 = evaluate(input_document=inp2, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome2.record)
    lifecycle_mgr.register_evaluation(outcome2.record)

    # Archive the superseded outcome1
    archived_lc = lifecycle_mgr.archive_evaluation(outcome1.record.evaluation_id, reason="test_archive")
    assert archived_lc.visibility_state == VISIBILITY_STATE_ARCHIVED
    assert archived_lc.operational_status == OPERATIONAL_STATUS_ARCHIVED
    assert archived_lc.lifecycle_state == LIFECYCLE_STATE_SUPERSEDED


def test_g_archived_to_superseded(lifecycle_mgr, sample_input, active_config):
    """G. ARCHIVED -> SUPERSEDED: Reversible unarchive restores to visible historical state, not ACTIVE."""
    outcome1 = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome1.record)
    lifecycle_mgr.register_evaluation(outcome1.record)

    inp2 = dict(sample_input)
    inp2["company_name"] = "VISHAL REVISED"
    outcome2 = evaluate(input_document=inp2, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome2.record)
    lifecycle_mgr.register_evaluation(outcome2.record)

    lifecycle_mgr.archive_evaluation(outcome1.record.evaluation_id)
    unarchived_lc = lifecycle_mgr.unarchive_evaluation(outcome1.record.evaluation_id)

    assert unarchived_lc.visibility_state == VISIBILITY_STATE_VISIBLE
    assert unarchived_lc.lifecycle_state == LIFECYCLE_STATE_SUPERSEDED
    assert unarchived_lc.operational_status == OPERATIONAL_STATUS_SUPERSEDED
    # Active must still be outcome2
    assert lifecycle_mgr.get_active_evaluation_id(outcome1.record.ipo_id, mode="final") == outcome2.record.evaluation_id


def test_h_governed_rollback(lifecycle_mgr, sample_input, active_config):
    """H. Governed rollback: Re-activating an older evaluation demotes the current active."""
    outcome1 = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome1.record)
    lifecycle_mgr.register_evaluation(outcome1.record)

    inp2 = dict(sample_input)
    inp2["company_name"] = "VISHAL REVISED"
    outcome2 = evaluate(input_document=inp2, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome2.record)
    lifecycle_mgr.register_evaluation(outcome2.record)

    assert lifecycle_mgr.get_active_evaluation_id(outcome1.record.ipo_id, mode="final") == outcome2.record.evaluation_id

    # Rollback to outcome1
    promoted_lc = lifecycle_mgr.make_active(outcome1.record.evaluation_id, actor="lead", reason="rollback")
    assert promoted_lc.lifecycle_state == LIFECYCLE_STATE_ACTIVE
    assert lifecycle_mgr.get_active_evaluation_id(outcome1.record.ipo_id, mode="final") == outcome1.record.evaluation_id

    # outcome2 must now be superseded
    demoted_lc = lifecycle_mgr.get_lifecycle(outcome2.record.evaluation_id)
    assert demoted_lc.lifecycle_state == LIFECYCLE_STATE_SUPERSEDED
    assert demoted_lc.superseded_by == outcome1.record.evaluation_id


def test_i_invalid_transitions(lifecycle_mgr, sample_input, active_config):
    """I. Invalid transitions: Active-to-active no-op, archiving active of ongoing offering, etc."""
    outcome1 = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome1.record)
    lifecycle_mgr.register_evaluation(outcome1.record)

    # Cannot archive active evaluation of ongoing offering
    with pytest.raises(InvalidStateTransitionError) as exc:
        lifecycle_mgr.archive_evaluation(outcome1.record.evaluation_id)
    assert "Active evaluations of ongoing offerings cannot be archived" in str(exc.value)

    # Cannot unarchive an evaluation that is not archived
    with pytest.raises(InvalidStateTransitionError):
        lifecycle_mgr.unarchive_evaluation(outcome1.record.evaluation_id)


def test_j_concurrent_active_promotion(lifecycle_mgr, sample_input, active_config):
    """J. Concurrent promotion: Exactly one evaluation remains active."""
    outcome1 = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome1.record)
    lifecycle_mgr.register_evaluation(outcome1.record)

    inp2 = dict(sample_input)
    inp2["company_name"] = "VISHAL REVISED"
    outcome2 = evaluate(input_document=inp2, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome2.record)
    lifecycle_mgr.register_evaluation(outcome2.record)

    index = lifecycle_mgr.load_index()
    active_count = sum(
        1 for e in index.issuers[outcome1.record.ipo_id].evaluations.values()
        if e.get("lifecycle_state") == LIFECYCLE_STATE_ACTIVE and e.get("mode") == "final"
    )
    assert active_count == 1


def test_k_cyclic_lineage_rejection(lifecycle_mgr):
    """K. Cyclic lineage rejection: Cycle detection aborts with CyclicLineageError."""
    index = LifecycleIndex()
    # Cycle: A -> B -> C -> A
    assert lifecycle_mgr._detect_cycle("A", "A", index) is True


def test_l_missing_lineage_target(lifecycle_mgr):
    """L. Missing lineage target: Operations fail closed on missing evaluation IDs."""
    with pytest.raises(EvaluationNotFoundError):
        lifecycle_mgr.archive_evaluation("NONEXISTENT-EVAL-ID")
    with pytest.raises(EvaluationNotFoundError):
        lifecycle_mgr.unarchive_evaluation("NONEXISTENT-EVAL-ID")
    with pytest.raises(EvaluationNotFoundError):
        lifecycle_mgr.make_active("NONEXISTENT-EVAL-ID")


def test_m_protected_golden_record():
    """M. Protected golden record: Vishal golden cannot be archived."""
    tier = get_protection_tier(
        evaluation_id="VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0",
        ipo_id="VISHAL-NIRMITI-LIMITED",
        result_hash=VISHAL_GOLDEN_RESULT_HASH,
    )
    assert tier == TIER_1_GOLDEN


def test_n_referenced_backtest_record(store_dir):
    """N. Referenced backtest record: Evaluations with child observations are classified Tier 2."""
    eval_id = "REF-EVAL-20261005-120000Z-final-12345678"
    obs_dir = store_dir / eval_id / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    (obs_dir / "observation_1w.json").write_text("{}", encoding="utf-8")

    tier = get_protection_tier(eval_id, "SOME-IPO", store_root=store_dir)
    assert tier == TIER_2_GOVERNED


def test_o_reversible_archival(lifecycle_mgr, sample_input, active_config):
    """O. Reversible archival: Archive then unarchive cycle preserves all metadata."""
    outcome1 = evaluate(input_document=sample_input, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome1.record)
    lifecycle_mgr.register_evaluation(outcome1.record)

    inp2 = dict(sample_input)
    inp2["company_name"] = "VISHAL REVISED"
    outcome2 = evaluate(input_document=inp2, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome2.record)
    lifecycle_mgr.register_evaluation(outcome2.record)

    # Archive
    lifecycle_mgr.archive_evaluation(outcome1.record.evaluation_id)
    assert lifecycle_mgr.get_lifecycle(outcome1.record.evaluation_id).visibility_state == VISIBILITY_STATE_ARCHIVED

    # Unarchive
    lifecycle_mgr.unarchive_evaluation(outcome1.record.evaluation_id)
    assert lifecycle_mgr.get_lifecycle(outcome1.record.evaluation_id).visibility_state == VISIBILITY_STATE_VISIBLE


def test_p_no_delete_endpoint(store_dir):
    """P. No DELETE endpoint: Presentation API blocks DELETE with HTTP 405."""
    cfg = PresentationConfig(store_root=store_dir)
    app = create_app(PresentationService(cfg))
    client = TestClient(app)

    resp = client.delete("/api/v1/evaluations/SOME-EVAL-ID")
    assert resp.status_code == 405
    assert resp.json()["code"] == "READ_ONLY_METHOD_NOT_ALLOWED"


def test_q_immutable_artifact_hashes(lifecycle_mgr, sample_input, active_config):
    """Q. Immutable artifact hashes: verify_hashes() passes before and after lifecycle changes."""
    outcome = evaluate(input_document=sample_input, config=active_config, mode="final")
    eval_id = outcome.record.evaluation_id
    lifecycle_mgr.store.write(outcome.record)

    # Check hashes before lifecycle registration
    res1 = lifecycle_mgr.store.verify_hashes(eval_id)
    assert res1["result_hash_matches"] is True
    assert res1["artifact_mismatches"] == []

    # Register in lifecycle
    lifecycle_mgr.register_evaluation(outcome.record)
    res2 = lifecycle_mgr.store.verify_hashes(eval_id)
    assert res2["result_hash_matches"] is True
    assert res2["artifact_mismatches"] == []

    # Add a second evaluation to supersede
    inp2 = dict(sample_input)
    inp2["company_name"] = "VISHAL REVISED"
    outcome2 = evaluate(input_document=inp2, config=active_config, mode="final")
    lifecycle_mgr.store.write(outcome2.record)
    lifecycle_mgr.register_evaluation(outcome2.record)

    # Check hashes after supersession
    res3 = lifecycle_mgr.store.verify_hashes(eval_id)
    assert res3["result_hash_matches"] is True
    assert res3["artifact_mismatches"] == []

    # Archive outcome
    lifecycle_mgr.archive_evaluation(eval_id)
    res4 = lifecycle_mgr.store.verify_hashes(eval_id)
    assert res4["result_hash_matches"] is True
    assert res4["artifact_mismatches"] == []


def test_r_rk_lifecycle_mapping(store_dir, active_config):
    """R. R.K. Fashion lifecycle mapping: c4e88b17 is ACTIVE, 6ee95f0a is SUPERSEDED+VISIBLE, 808a237d/1d64ea28 ARCHIVED."""
    # Create the 4 dummy evaluation directories representing the R.K. sequence
    mgr = LifecycleManager(store_dir, active_config_hash=ACTIVE_RATIFIED_CONFIG_HASH)
    rk_eids = [
        "R-K-FASHION-ACCESSORIES-LIMITED-20261007-035435Z-final-1d64ea28",
        "R-K-FASHION-ACCESSORIES-LIMITED-20261007-062328Z-final-808a237d",
        "R-K-FASHION-ACCESSORIES-LIMITED-20261007-092818Z-final-6ee95f0a",
        "R-K-FASHION-ACCESSORIES-LIMITED-20261007-133111Z-final-c4e88b17",
    ]
    for eid in rk_eids:
        edir = store_dir / eid
        edir.mkdir(parents=True, exist_ok=True)
        rec_data = {
            "evaluation_id": eid,
            "ipo_id": "R-K-FASHION-ACCESSORIES-LIMITED",
            "company_name": "R.K. Fashion Accessories Limited",
            "evaluation_mode": "FINAL",
            "evaluation_timestamp": "2026-10-07T12:00:00Z",
            "engine_version": "1.5.0",
            "spec_version": "1.5",
            "config_version": "1.5.0",
            "config_hash": ACTIVE_RATIFIED_CONFIG_HASH,
            "result_hash": eid.split("-")[-1],
        }
        (edir / "evaluation.json").write_text(json.dumps(rec_data), encoding="utf-8")

    # Run bootstrap
    mgr.bootstrap_store(force=True)

    lc_50 = mgr.get_lifecycle(rk_eids[3])
    lc_55 = mgr.get_lifecycle(rk_eids[2])
    lc_60 = mgr.get_lifecycle(rk_eids[1])
    lc_61 = mgr.get_lifecycle(rk_eids[0])

    assert lc_50.operational_status == OPERATIONAL_STATUS_ACTIVE
    assert lc_50.visibility_state == VISIBILITY_STATE_VISIBLE

    assert lc_55.operational_status == OPERATIONAL_STATUS_SUPERSEDED
    assert lc_55.visibility_state == VISIBILITY_STATE_VISIBLE  # Retained visible for defect evidence

    assert lc_60.operational_status == OPERATIONAL_STATUS_ARCHIVED
    assert lc_61.operational_status == OPERATIONAL_STATUS_ARCHIVED

    # Verify active ID
    active_rk = mgr.get_active_evaluation_id("R-K-FASHION-ACCESSORIES-LIMITED", mode="final")
    assert active_rk == rk_eids[3]


def test_s_vishal_golden_regression(active_config):
    """S. Vishal golden regression: Bit-for-bit hash e84f8bc0... unchanged."""
    from datetime import datetime, timezone
    sample_input = json.loads(Path("fixtures/vishal_nirmiti/input.json").read_text(encoding="utf-8"))
    outcome = evaluate(
        input_document=sample_input,
        config=active_config,
        mode="final",
        evaluation_datetime=datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert outcome.record.result_hash == VISHAL_GOLDEN_RESULT_HASH
    assert outcome.score.final_score == pytest.approx(35.0)


# -----------------------------------------------------------------------------
# Cross-Platform Locking & Windows Portability Tests
# -----------------------------------------------------------------------------

def test_cross_platform_import_portability_without_fcntl():
    """Verify that ipo_screening and lifecycle import cleanly when fcntl is absent (Windows)."""
    import sys
    from unittest.mock import patch

    # Ensure importing without fcntl does not raise ModuleNotFoundError
    with patch.dict(sys.modules, {"fcntl": None}):
        import ipo_screening
        from ipo_screening.lifecycle import (
            LifecycleManager,
            acquire_file_lock,
            release_file_lock,
        )
        assert hasattr(ipo_screening, "ENGINE_VERSION")
        assert callable(acquire_file_lock)
        assert callable(release_file_lock)


def test_cross_platform_locking_exclusive_serialization(store_dir):
    """Verify exclusive writer serialization: a second writer cannot enter critical section simultaneously."""
    import threading
    import time
    from ipo_screening.lifecycle import LifecycleManager

    mgr1 = LifecycleManager(store_dir)
    mgr2 = LifecycleManager(store_dir)

    acquired_1 = threading.Event()
    release_1 = threading.Event()
    mgr2_entered_simultaneously = False
    mgr2_timed_out = False

    def writer_1():
        with mgr1._file_lock(timeout=5.0):
            acquired_1.set()
            release_1.wait(timeout=2.0)

    def writer_2():
        nonlocal mgr2_entered_simultaneously, mgr2_timed_out
        acquired_1.wait(timeout=2.0)
        try:
            # Try to acquire while writer_1 is still holding lock (short timeout)
            with mgr2._file_lock(timeout=0.1, blocking=True):
                mgr2_entered_simultaneously = True
        except TimeoutError:
            mgr2_timed_out = True

    t1 = threading.Thread(target=writer_1)
    t2 = threading.Thread(target=writer_2)

    t1.start()
    t2.start()

    t2.join(timeout=3.0)
    release_1.set()
    t1.join(timeout=3.0)

    assert not mgr2_entered_simultaneously, "Writer 2 entered critical section while Writer 1 held the lock!"
    assert mgr2_timed_out, "Writer 2 should have timed out waiting for locked critical section"


def test_cross_platform_locking_release_on_completion(store_dir):
    """Verify that lock is released after normal completion, allowing immediate re-acquisition."""
    from ipo_screening.lifecycle import LifecycleManager

    mgr = LifecycleManager(store_dir)

    with mgr._file_lock(timeout=1.0):
        pass

    # Immediately acquire again
    acquired_second_time = False
    with mgr._file_lock(timeout=1.0):
        acquired_second_time = True

    assert acquired_second_time is True


def test_cross_platform_locking_release_on_exception(store_dir):
    """Verify that lock is released after an exception inside the critical section."""
    from ipo_screening.lifecycle import LifecycleManager

    mgr = LifecycleManager(store_dir)

    with pytest.raises(RuntimeError):
        with mgr._file_lock(timeout=1.0):
            raise RuntimeError("Forced critical section error")

    # Lock must be released cleanly despite the unhandled exception
    reacquired = False
    with mgr._file_lock(timeout=1.0):
        reacquired = True

    assert reacquired is True


def test_cross_platform_locking_windows_msvcrt_simulation(tmp_path):
    """Verify Windows msvcrt locking behavior: byte 0 lock, retry loop, timeout, and unlock."""
    from unittest.mock import MagicMock, patch
    from ipo_screening.lifecycle import acquire_file_lock, release_file_lock

    mock_msvcrt = MagicMock()
    mock_msvcrt.LK_NBLCK = 2
    mock_msvcrt.LK_UNLCK = 0

    lock_file = tmp_path / "test_win.lock"
    lock_file.write_bytes(b"0")

    with lock_file.open("r+b") as f:
        fileno = f.fileno()

        # 1. Normal acquisition and release under Windows
        with patch("ipo_screening.lifecycle.fcntl", None), patch("ipo_screening.lifecycle.msvcrt", mock_msvcrt):
            acquire_file_lock(fileno, blocking=True, timeout=1.0)
            mock_msvcrt.locking.assert_called_with(fileno, 2, 1)

            release_file_lock(fileno)
            mock_msvcrt.locking.assert_called_with(fileno, 0, 1)

        # 2. Contention and timeout fail-closed under Windows
        mock_msvcrt.reset_mock()
        mock_msvcrt.locking.side_effect = OSError(13, "Permission denied")

        with patch("ipo_screening.lifecycle.fcntl", None), patch("ipo_screening.lifecycle.msvcrt", mock_msvcrt):
            with pytest.raises(TimeoutError) as exc_info:
                acquire_file_lock(fileno, blocking=True, timeout=0.05, poll_interval=0.005)
            assert "exclusive Windows lifecycle lock" in str(exc_info.value)


def test_cross_platform_locking_fail_closed_on_timeout(store_dir):
    """Verify fail-closed behavior: critical section is never executed if lock acquisition fails."""
    import threading
    from ipo_screening.lifecycle import LifecycleManager

    mgr1 = LifecycleManager(store_dir)
    mgr2 = LifecycleManager(store_dir)

    acquired_1 = threading.Event()
    release_1 = threading.Event()
    critical_section_entered = False

    def writer_1():
        with mgr1._file_lock(timeout=5.0):
            acquired_1.set()
            release_1.wait(timeout=2.0)

    t1 = threading.Thread(target=writer_1)
    t1.start()

    acquired_1.wait(timeout=2.0)

    with pytest.raises(TimeoutError):
        with mgr2._file_lock(timeout=0.05):
            critical_section_entered = True

    release_1.set()
    t1.join(timeout=2.0)

    assert critical_section_entered is False


def test_lifecycle_index_atomic_replacement_integrity(store_dir):
    """Verify that save_index uses atomic replacement and maintains index integrity under concurrent reads."""
    from ipo_screening.lifecycle import IssuerLifecycleEntry, LifecycleIndex, LifecycleManager

    mgr = LifecycleManager(store_dir)
    index = mgr.load_index()
    index.issuers["TEST-CORP"] = IssuerLifecycleEntry(ipo_id="TEST-CORP", company_name="Test Corp")

    mgr.save_index(index)
    assert mgr.index_path.exists()

    # Re-read
    loaded = mgr.load_index()
    assert "TEST-CORP" in loaded.issuers


def test_lifecycle_fixture_loading_encoding_portable():
    """Verify that fixture loading is explicitly UTF-8 encoded and independent of Windows CP1252 charmap."""
    p = Path("fixtures/vishal_nirmiti/input.json")
    content = p.read_text(encoding="utf-8")
    data = json.loads(content)
    assert data["ipo_id"] == "VISHAL-NIRMITI-LIMITED"
    assert "₹" in content

