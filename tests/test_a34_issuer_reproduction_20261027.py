"""Pin the A33/A34 issuer reproduction on the committed Jio input snapshot.

The committed current-engine probe record

``docs/investigation/jio-current-engine-probe-20261027/evaluations/
JIO-PLATFORMS-LIMITED-20261027-145236Z-final-0fde1451/input.json``

carries the PR #13 (pre-A34) canonical input: ``kmp_exits_2y = 6`` and
``large_holders_unlocked_early = True``.  Re-evaluating that exact input with
the shipped config reproduces the recorded 37.0 / AVOID / 63.0% result.
Removing only the A34-invalid flag (which is what the corrected reader now
does) isolates the approved semantic change: no weight, threshold, penalty or
knockout moves; C ``lockin`` becomes UNKNOWN, one point returns to the
available pool, and completeness drops by exactly one point.

A33 alternative A is approved, so the counting rule is deliberately *not*
changed: both readings keep ``kmp_exits_2y = 6`` and ``board_kmp`` high_churn.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from conftest import REPO_ROOT
from ipo_screening.pipeline import evaluate, load_config

INPUT_SNAPSHOT = (
    REPO_ROOT
    / "docs/investigation/jio-current-engine-probe-20261027/evaluations"
    / "JIO-PLATFORMS-LIMITED-20261027-145236Z-final-0fde1451/input.json"
)
EVALUATION_AT = datetime(2026, 10, 27, 14, 52, 36, tzinfo=timezone.utc)
CONFIG_PATH = REPO_ROOT / "config" / "ipo-config.v1.5.0.json"
EARLY_PATH = "capital_structure.large_holders_unlocked_early"


def _input() -> dict:
    if not INPUT_SNAPSHOT.is_file():
        import pytest

        pytest.skip("committed current-engine Jio input snapshot is not present")
    return json.loads(INPUT_SNAPSHOT.read_text())["snapshot"]["input"]


def _evaluate(early_flag: bool | None):
    document = copy.deepcopy(_input())
    if early_flag is None:
        document["capital_structure"].pop("large_holders_unlocked_early", None)
    else:
        document["capital_structure"]["large_holders_unlocked_early"] = early_flag
    outcome = evaluate(
        document,
        load_config(CONFIG_PATH),
        mode="final",
        evaluation_datetime=EVALUATION_AT,
    )
    record = outcome.record.to_dict()
    score = record["score"]
    criteria = {
        c["criterion_id"]: c
        for module in score["modules"]
        for c in module["criteria"]
    }
    knockouts = {r["rule_id"]: r["state"] for r in record["knockouts"]["results"]}
    return score, criteria, knockouts, record["verdict"]["verdict"]


def test_committed_probe_input_is_the_pre_a34_baseline():
    document = _input()
    assert document["capital_structure"]["large_holders_unlocked_early"] is True
    assert document["governance"]["kmp_exits_2y"] == 6
    score, criteria, knockouts, verdict = _evaluate(True)
    assert score["final_score"] == 37.0
    assert score["completeness_pct"] == 63.0
    assert score["lower_bound"] == 25.0
    assert score["upper_bound"] == 74.0
    assert verdict == "AVOID"
    assert knockouts["K2"] == "TRIGGERED"
    assert criteria["lockin"]["state"] == "SCORED"
    assert criteria["lockin"]["band"] == "weak"
    assert criteria["lockin"]["score"] == 0.0


def test_a34_only_makes_lockin_unknown_and_returns_one_available_point():
    score, criteria, knockouts, verdict = _evaluate(None)
    assert score["final_score"] == 37.0
    assert score["base_score"] == 37.0
    assert score["penalties_total"] == 0.0
    assert score["completeness_pct"] == 62.0
    assert score["lower_bound"] == 25.0
    assert score["upper_bound"] == 75.0
    assert score["available_points"] == 62.0
    assert score["unknown_points"] == 38.0
    assert verdict == "AVOID"
    assert knockouts["K2"] == "TRIGGERED"
    assert criteria["lockin"]["state"] == "UNKNOWN"
    assert criteria["lockin"].get("score") is None


def test_a33_approved_alternative_a_keeps_the_counting_rule():
    """No counting or scoring change: Jio 6 -> board_kmp high_churn, both ways."""
    assert _input()["governance"]["kmp_exits_2y"] == 6
    for flag in (True, None):
        _, criteria, _, _ = _evaluate(flag)
        assert criteria["board_kmp"]["state"] == "SCORED"
        assert criteria["board_kmp"]["band"] == "high_churn"
        assert criteria["board_kmp"]["score"] == 0.0
