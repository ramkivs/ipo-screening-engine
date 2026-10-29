from __future__ import annotations

import copy

from conftest import criterion, metric, run
from ipo_screening.financial_health import financial_health_metrics, with_financial_health_extension


def _run_extension(document, config):
    with financial_health_metrics():
        return run(document, with_financial_health_extension(config))


def _with_overrides(golden_input, **values):
    document = copy.deepcopy(golden_input)
    document["financials"].update(values)
    return document


def test_negative_cumulative_ocf_triggers_full_paper_profit_penalty(golden_input, config):
    outcome = _run_extension(_with_overrides(
        golden_input,
        operating_cash_flow_3yr_cumulative=[-10, -20, -30],
        net_income_3yr_cumulative=[100, 100, 100],
    ), config)
    flag = metric(outcome, "cash_flow_quality_below_50pct")
    penalty = criterion(outcome, "cash_flow_quality_penalty")
    assert flag.value is True
    assert penalty.score == -5
    assert penalty.state == "SCORED"


def test_cash_conversion_at_or_above_half_does_not_penalize(golden_input, config):
    outcome = _run_extension(_with_overrides(
        golden_input,
        operating_cash_flow_3yr_cumulative=150,
        net_income_3yr_cumulative=300,
    ), config)
    assert metric(outcome, "cash_flow_quality_below_50pct").value is False
    assert criterion(outcome, "cash_flow_quality_penalty").score == 0


def test_missing_dso_stays_unknown_instead_of_defaulting_to_zero(golden_input, config):
    document = copy.deepcopy(golden_input)
    document["financials"].pop("trade_receivables_days", None)
    for period in document["financials"]["periods"]:
        period.pop("receivable_days", None)
    outcome = _run_extension(document, config)
    assert metric(outcome, "dso_above_60").is_unknown
    assert criterion(outcome, "dso_over_60_penalty").state == "UNKNOWN"


def test_extreme_dso_and_working_capital_apply_sliding_penalties(golden_input, config):
    outcome = _run_extension(_with_overrides(
        golden_input,
        trade_receivables_days=150,
        net_working_capital_pct_revenue=60,
    ), config)
    ids = (
        "dso_over_60_penalty", "dso_over_90_penalty", "dso_over_120_or_spike_penalty",
        "working_capital_over_20_penalty", "working_capital_over_35_penalty",
        "working_capital_over_50_penalty",
    )
    assert sum(criterion(outcome, item).score for item in ids) == -6
    module_a = next(module for module in outcome.score.modules if module.module_id == "A")
    assert 0 <= module_a.score <= module_a.max


def test_dso_upward_spike_applies_final_sliding_step(golden_input, config):
    document = copy.deepcopy(golden_input)
    document["financials"]["trade_receivables_days"] = 55
    document["financials"]["periods"][-2]["receivable_days"] = 40
    document["financials"]["periods"][-1]["receivable_days"] = 55
    outcome = _run_extension(document, config)
    assert metric(outcome, "dso_above_120_or_spike").value is True
    assert criterion(outcome, "dso_over_120_or_spike_penalty").score == -1
