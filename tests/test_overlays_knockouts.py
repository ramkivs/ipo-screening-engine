"""Sector and structure overlays, and the tri-state knockout gate.

Spec v1.5 s14, s15, s16, s25; execution prompt s9, s13, s14. The two central
claims under test are:

1. An overlay is *mandatory and executable* - the plan it resolves to is
   complete, reconciles to 100 points, and is recorded with the result.
2. A knockout that cannot be evaluated is UNVERIFIED, never CLEAR. "We could
   not check" must never read as "we checked and it was fine".
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from conftest import (
    EVAL_AT,
    GOLDEN_DIR,
    criterion,
    derive_for,
    metric,
    minimal_input,
    plan_for,
    prepare,
    run,
)
from ipo_screening.canonical_input import build_canonical_input
from ipo_screening.derived import derive
from ipo_screening.knockouts import (
    Truth,
    evaluate_knockouts,
    evaluate_expression,
    k_and,
    k_not,
    k_or,
)
from ipo_screening.overlays import resolve_overlays


# --------------------------------------------------------------------------
# Kleene three-valued logic
# --------------------------------------------------------------------------


def test_kleene_and_matches_the_specification_table():
    """FALSE dominates in AND; UNKNOWN is the identity."""
    cases = {
        (Truth.TRUE, Truth.TRUE): Truth.TRUE,
        (Truth.TRUE, Truth.FALSE): Truth.FALSE,
        (Truth.TRUE, Truth.UNKNOWN): Truth.UNKNOWN,
        (Truth.FALSE, Truth.FALSE): Truth.FALSE,
        (Truth.FALSE, Truth.UNKNOWN): Truth.FALSE,
        (Truth.UNKNOWN, Truth.UNKNOWN): Truth.UNKNOWN,
    }
    for (left, right), expected in cases.items():
        assert k_and([left, right]) is expected, (left, right)
        assert k_and([right, left]) is expected, (right, left)


def test_kleene_or_matches_the_specification_table():
    """TRUE dominates in OR; UNKNOWN is the identity."""
    cases = {
        (Truth.TRUE, Truth.TRUE): Truth.TRUE,
        (Truth.TRUE, Truth.FALSE): Truth.TRUE,
        (Truth.TRUE, Truth.UNKNOWN): Truth.TRUE,
        (Truth.FALSE, Truth.FALSE): Truth.FALSE,
        (Truth.FALSE, Truth.UNKNOWN): Truth.UNKNOWN,
        (Truth.UNKNOWN, Truth.UNKNOWN): Truth.UNKNOWN,
    }
    for (left, right), expected in cases.items():
        assert k_or([left, right]) is expected, (left, right)
        assert k_or([right, left]) is expected, (right, left)


def test_kleene_not_is_involution():
    for value in Truth:
        assert k_not(k_not(value)) is value
    assert k_not(Truth.TRUE) is Truth.FALSE
    assert k_not(Truth.FALSE) is Truth.TRUE
    assert k_not(Truth.UNKNOWN) is Truth.UNKNOWN


def test_expression_evaluation_is_tri_state(config, golden_input):
    derived = derive_for(json.loads(json.dumps(golden_input)), config)

    # The auditor opinion is known and not in the trigger set; going concern is
    # UNKNOWN. In a conjunction the known-FALSE leg dominates.
    leaves = []
    expression = {
        "all": [
            {"metric": "auditor_opinion", "op": "in", "value": ["qualified"]},
            {"flag": "going_concern_uncertainty"},
        ]
    }
    assert evaluate_expression(expression, derived, leaves) is Truth.FALSE

    # A conjunction with only UNKNOWN legs stays UNKNOWN.
    expression = {
        "all": [
            {"flag": "going_concern_uncertainty"},
            {"flag": "contingent_liab_unquantified"},
        ]
    }
    leaves = []
    assert evaluate_expression(expression, derived, leaves) is Truth.UNKNOWN

    # A disjunction with a known-TRUE operand is TRUE regardless of the unknown.
    expression = {
        "any": [
            {"metric": "net_worth_latest", "op": "<", "value": 0},
            {"flag": "going_concern_uncertainty"},
        ]
    }
    leaves = []
    assert evaluate_expression(expression, derived, leaves) is Truth.UNKNOWN

    expression = {
        "any": [
            {"metric": "net_worth_latest", "op": ">", "value": 0},
            {"flag": "going_concern_uncertainty"},
        ]
    }
    leaves = []
    assert evaluate_expression(expression, derived, leaves) is Truth.TRUE


def test_unrecognised_expression_node_never_returns_a_verdict(config, golden_input):
    """An unknown node kind must not silently read as CLEAR or TRIGGERED.

    ``check_config`` rejects such a node, so this path is reachable only if a
    caller bypasses configuration validation. It must still fail closed.
    """
    derived = derive_for(json.loads(json.dumps(golden_input)), config)
    leaves = []
    truth = evaluate_expression({"fact": "something_undefined"}, derived, leaves)
    assert truth is Truth.UNKNOWN
    assert leaves and leaves[0].truth == "UNKNOWN"


# --------------------------------------------------------------------------
# Knockouts
# --------------------------------------------------------------------------


def test_golden_knockouts_are_a_mix_of_clear_and_unverified(golden_input, config):
    """The golden case must never report an unverified knockout as CLEAR."""
    outcome = run(golden_input, config)
    summary = outcome.record.knockouts
    assert summary["status"] == "UNVERIFIED"

    by_id = {k["rule_id"]: k for k in summary["results"]}
    assert by_id["K1"]["state"] == "UNVERIFIED"
    assert by_id["K5"]["state"] == "UNVERIFIED"
    assert by_id["K6"]["state"] == "UNVERIFIED"
    for clear in ("K2", "K3", "K4"):
        assert by_id[clear]["state"] == "CLEAR", clear

    unverified = {k["rule_id"] for k in summary["results"] if k["state"] == "UNVERIFIED"}
    assert unverified == {"K1", "K5", "K6"}
    # Half the gate resolved: 3 of 6.
    assert summary["completeness_pct"] == pytest.approx(50.0)


def test_unverified_knockout_lists_the_missing_evidence(golden_input, config):
    outcome = run(golden_input, config)
    summary = outcome.record.knockouts
    unverified = [k for k in summary["results"] if k["state"] == "UNVERIFIED"]
    assert unverified
    for item in unverified:
        assert item["missing"], item["rule_id"]
        assert item["explanation"]
    missing = {m for k in unverified for m in k["missing"]}
    assert "going_concern_uncertainty" in missing


def test_triggered_knockout_is_critical(golden_input, config):
    """A triggered knockout must dominate: verdict AVOID regardless of score."""
    document = json.loads(json.dumps(golden_input))
    document["governance"]["going_concern_uncertainty"] = True
    outcome = run(document, config)

    summary = outcome.record.knockouts
    triggered = [k for k in summary["results"] if k["state"] == "TRIGGERED"]
    assert triggered, summary
    assert summary["status"] == "TRIGGERED"
    assert summary["any_triggered"] is True
    assert outcome.score.verdict == "AVOID"
    assert "K1" in triggered[0]["rule_id"]


def test_knockout_facts_are_traced_leaf_by_leaf(golden_input, config):
    """Every knockout records the evidence it used to decide."""
    outcome = run(golden_input, config)
    for rule in outcome.record.knockouts["results"]:
        assert rule["leaves"], rule["rule_id"]
        for leaf in rule["leaves"]:
            assert leaf["truth"] in {"TRUE", "FALSE", "UNKNOWN"}
            assert leaf["kind"] in {"metric", "flag", "fact"}
            if leaf["truth"] == "UNKNOWN":
                assert leaf.get("detail")


def _undisclosed_input():
    """A schema-valid document whose material facts are all withheld."""
    document = minimal_input()
    for period in document["financials"]["periods"]:
        period.clear()
        period["fy"] = "placeholder"
    for index, fy in enumerate(("FY2024", "FY2025", "FY2026")):
        document["financials"]["periods"][index]["fy"] = fy
        document["financials"]["periods"][index]["revenue"] = None
        document["financials"]["periods"][index]["pat"] = None
    document["issue"]["fresh_issue"] = None
    document["issue"]["ofs"] = None
    document["capital_structure"].clear()
    document["peers"] = []
    return document


def test_nothing_is_clear_when_nothing_is_known(config):
    """With nothing disclosed, no knockout may be reported CLEAR."""
    derived = derive_for(_undisclosed_input(), config)
    results = evaluate_knockouts(config, derived)
    assert results
    for rule in results:
        assert rule.state != "CLEAR", rule.rule_id


def test_triggered_knockout_short_circuits_an_unknown(config, golden_input):
    """A true disjunct makes a knockout TRIGGERED even with unknowns present."""
    document = json.loads(json.dumps(golden_input))
    document["governance"]["auditor_opinion"] = "qualified"
    outcome = run(document, config)
    k1 = next(k for k in outcome.record.knockouts["results"] if k["rule_id"] == "K1")
    assert k1["state"] == "TRIGGERED"
    assert k1["missing"] == []


# --------------------------------------------------------------------------
# Overlays
# --------------------------------------------------------------------------


def _plan(document, config):
    return plan_for(document, config)


def test_auto_profile_is_selected_from_the_input(config, make_input):
    """A loss at the latest FY auto-selects the loss-making profile."""
    document = make_input(**{"financials.periods[2].pat": -2497.5})
    plan = _plan(document, config)
    assert plan.auto_profile_applied == "loss_making"
    assert plan.resolved_profile == "loss_making"
    assert plan.sector_overlay == "loss_making"


def test_auto_profile_defers_to_a_requested_sector(config, make_input):
    """Spec s15: ``unless_profile`` protects a sector from being overridden."""
    document = make_input(
        **{"financials.periods[2].pat": -2497.5, "sector_profile": "financial"}
    )
    plan = _plan(document, config)
    assert plan.auto_profile_applied is None
    assert plan.resolved_profile == "financial"
    assert plan.sector_overlay == "financial"


def test_standard_profile_has_no_sector_overlay(config, make_input):
    plan = _plan(make_input(sector_profile="standard"), config)
    assert plan.sector_overlay is None
    assert plan.auto_profile_applied is None


def test_sector_overlay_replaces_criteria(config, make_input):
    """v1.5 s14: a sector rule removes named criteria and supplies its own."""
    plan = _plan(make_input(sector_profile="financial"), config)
    assert plan.sector_overlay == "financial"
    added = {c["id"] for c in plan.added_criteria}
    assert added
    assert set(plan.removed_criteria)


def test_scoring_plan_is_recorded_in_the_result(golden_input, config):
    """Spec s21: the effective scoring plan is part of the frozen record."""
    outcome = run(golden_input, config)
    plan = outcome.record.plan
    assert plan["requested_profile"] == "standard"
    assert plan["total_points"] == pytest.approx(100.0)
    assert outcome.score.plan_hash


def test_every_sector_overlay_reconciles_to_100(config, make_input):
    """Spec s20: the plan an overlay resolves to must reconcile."""
    for sector in config["sector_overlays"]:
        plan = _plan(make_input(sector_profile=sector), config)
        assert plan.total_points == pytest.approx(100.0), sector
        modules = dict(plan.effective_module_totals)
        assert sum(modules.values()) == pytest.approx(100.0), sector


def test_structure_overlays_also_reconcile(config, make_input):
    for structure_input in (
        {"issue.fresh_issue": 0.0, "issue.ofs": 14500.0},
        {"capital_structure.promoter_post_issue_pct": 35.0},
    ):
        document = make_input(**structure_input)
        plan = _plan(document, config)
        assert plan.total_points == pytest.approx(100.0), structure_input


def test_overlay_never_silently_drops_an_unimplemented_metric(config, make_input):
    plan = _plan(make_input(sector_profile="epc_real_estate"), config)
    assert plan.added_criteria
    for item in plan.added_criteria:
        assert item["metric"] in config["derived_metrics"], item["id"]
        assert item["max"] >= 0


def test_plan_hash_is_stable_for_the_same_inputs(config, make_input):
    document = make_input(sector_profile="financial")
    first = _plan(copy.deepcopy(document), config)
    second = _plan(copy.deepcopy(document), config)
    assert first.hash() == second.hash()


def test_plan_hash_differs_when_the_overlay_differs(config, make_input):
    plain = _plan(make_input(), config)
    overlaid = _plan(make_input(sector_profile="financial"), config)
    assert plain.hash() != overlaid.hash()


def test_golden_plan_is_standard_with_no_sector_overlay(golden_input, config):
    """Vishal Nirmiti is an EPC issuer filed under the standard profile."""
    outcome = run(golden_input, config)
    plan = outcome.record.plan
    assert plan["resolved_profile"] == "standard"
    assert plan["auto_profile_applied"] is None
    assert plan["sector_overlay"] is None
    # No sector overlay, but the retail-heavy structure rule still applies:
    # the anchor/QIB criteria are unobservable on this offer and are replaced.
    assert plan["structure_overlays"] == ["retail_heavy"]
    assert plan["removed"] == ["anchor_quality", "qib_subscription"]
    assert plan["added"] == ["overall_subscription", "nii_subscription"]


def test_removed_criteria_points_are_returned(config, make_input):
    """A removal must be offset by additions, or explicitly re-pointed."""
    plan = _plan(make_input(sector_profile="financial"), config)
    assert plan.removed_criteria
    assert plan.added_criteria
    assert plan.total_points == pytest.approx(100.0)
