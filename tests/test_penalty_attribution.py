"""Penalty attribution and the auditor/CFO + unreconciled mapping defects.

The 2026-10-19 HD Fire reconciliation had to resolve whether the applied
``receivable_days_up`` -3 could have been the ``auditor_cfo_exit`` -3.  It
cannot: every penalty item evaluates its own trigger and the persisted,
API and rendered item ids are one-to-one.  These tests pin that property.

They also pin the two mapping defects found by the same audit:

* ``governance.auditor_or_cfo_exit_2y`` is permitted by the input schema and
  consumed by ``auditor_or_cfo_exit_2y``, but ``CanonicalInputBuilder`` did
  not carry it into the canonical input -- so the penalty was structurally
  UNKNOWN for every builder-based evaluation, even when the input stated
  the flag.
* ``financials.adjusted_metrics_unreconciled`` had the same defect for the
  ``unreconciled_metrics`` penalty.

The fix carries each flag only when the input/extraction establishes it;
an absent flag remains UNKNOWN.  No scoring rule, threshold or weight
changes.  The golden input does not carry either key, so its canonical
input and result hash are unchanged.
"""

from __future__ import annotations

import pytest

from conftest import run


def _items(outcome):
    return {item["id"]: item for item in outcome.score.penalty_items}


def test_receivable_days_penalty_is_attributed_to_receivable_only(config, make_input):
    """The applied -3 belongs to the item whose own trigger fired."""
    document = make_input(**{"financials.periods[2].receivable_days": 80.0})
    outcome = run(document, config)
    items = _items(outcome)

    assert items["receivable_days_up"]["points"] == pytest.approx(-3.0)
    assert items["receivable_days_up"]["state"] == "SCORED"
    assert items["receivable_days_up"]["reason"] == "triggered"

    # The auditor/CFO flag is absent: UNKNOWN, zero applied, carried in the
    # lower bound -- never silently re-labelled as the applied -3.
    assert items["auditor_cfo_exit"]["points"] == 0.0
    assert items["auditor_cfo_exit"]["state"] == "UNKNOWN"
    baseline = run(make_input(), config).score.penalties_total
    assert outcome.score.penalties_total == pytest.approx(baseline - 3.0)
    assert outcome.score.unresolved_penalty_points >= 3.0


def test_auditor_cfo_flag_true_triggers_its_own_penalty(config, make_input):
    """The schema-permitted flag must reach the canonical input and fire."""
    document = make_input(**{"governance.auditor_or_cfo_exit_2y": True})
    outcome = run(document, config)
    items = _items(outcome)

    assert outcome.canonical.governance().get("auditor_or_cfo_exit_2y") is True
    assert items["auditor_cfo_exit"]["points"] == pytest.approx(-3.0)
    assert items["auditor_cfo_exit"]["state"] == "SCORED"
    assert items["receivable_days_up"]["points"] == 0.0
    assert items["receivable_days_up"]["state"] == "SCORED"
    baseline = run(make_input(), config).score.penalties_total
    assert outcome.score.penalties_total == pytest.approx(baseline - 3.0)


def test_auditor_cfo_flag_false_is_scored_not_triggered(config, make_input):
    outcome = run(make_input(**{"governance.auditor_or_cfo_exit_2y": False}), config)
    items = _items(outcome)
    assert items["auditor_cfo_exit"]["points"] == 0.0
    assert items["auditor_cfo_exit"]["state"] == "SCORED"
    assert items["auditor_cfo_exit"]["reason"] == "not triggered"


def test_unreconciled_metrics_flag_true_triggers_its_own_penalty(config, make_input):
    """The second dropped schema field: the -2 penalty now fires."""
    outcome = run(
        make_input(**{"financials.adjusted_metrics_unreconciled": True}), config
    )
    items = _items(outcome)
    assert (
        outcome.canonical.raw["financials"].get("adjusted_metrics_unreconciled") is True
    )
    assert items["unreconciled_metrics"]["points"] == pytest.approx(-2.0)
    assert items["unreconciled_metrics"]["state"] == "SCORED"
    baseline = run(make_input(), config).score.penalties_total
    assert outcome.score.penalties_total == pytest.approx(baseline - 2.0)


def test_two_triggered_penalties_keep_their_own_points_and_ids(config, make_input):
    document = make_input(
        **{
            "financials.periods[2].receivable_days": 80.0,
            "governance.auditor_or_cfo_exit_2y": True,
        }
    )
    outcome = run(document, config)
    items = _items(outcome)
    assert items["receivable_days_up"]["points"] == pytest.approx(-3.0)
    assert items["auditor_cfo_exit"]["points"] == pytest.approx(-3.0)
    baseline = run(make_input(), config).score.penalties_total
    assert outcome.score.penalties_total == pytest.approx(baseline - 6.0)
    # No item's points appear under another id: the baseline margin-spike
    # trigger keeps its own -3 and the untriggered items stay at zero.
    assert items["margin_spike"]["points"] == pytest.approx(-3.0)
    assert items["discounted_allotments"]["points"] == 0.0
