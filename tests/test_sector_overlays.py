"""Sector-overlay behaviour: what each overlay's metrics actually compute.

The overlay *plan* (which criteria replace which, and that each reconciles to
100 points) is covered in ``test_overlays_knockouts.py``. This module covers the
other half: the derived metrics that only a sector profile uses. A bank's
NIM/cost-to-income trend, its asset-quality trend and its CRAR buffer are not
the same facts as a manufacturer's, so each is derived separately and each is
exercised here against an input engineered so the expected bucket is
unambiguous.

Spec s14: overlays are mandatory, and a metric that cannot be derived must
surface as UNKNOWN rather than as a zero.
"""

from __future__ import annotations

import copy
from typing import Any, Dict

import pytest

from conftest import metric, run

FRESH = "2026-09-20"  # inside the 30-day peer staleness window at EVAL_AT

# fy -> NIM, cost/income, GNPA, coverage, CRAR. NIM rising with cost falling
# ("improving"); GNPA falling with coverage rising ("improving_strong"); CRAR
# 20.10 against a 15.00 statutory minimum, i.e. a 5.1pt buffer.
FINANCIAL_PERIODS = {
    0: dict(nim_pct=3.10, cost_to_income_pct=52.0, gnpa_pct=4.20,
            provision_coverage_pct=68.0, crar_pct=18.40),
    1: dict(nim_pct=3.45, cost_to_income_pct=49.0, gnpa_pct=3.10,
            provision_coverage_pct=74.0, crar_pct=19.20),
    2: dict(nim_pct=3.70, cost_to_income_pct=46.5, gnpa_pct=2.40,
            provision_coverage_pct=79.0, crar_pct=20.10),
}

BANK_PEERS = [
    {"name": "Peer Bank One Limited", "business_match": "match", "listed_years": 9,
     "as_of": FRESH, "pe": 12.0, "pb": 1.50, "ps": 2.40, "roe_pct": 8.00,
     "source_id": "PEER-SCREENER"},
    {"name": "Peer Bank Two Limited", "business_match": "match", "listed_years": 14,
     "as_of": FRESH, "pe": 14.0, "pb": 1.70, "ps": 2.80, "roe_pct": 10.00,
     "source_id": "PEER-SCREENER"},
]


def _bank_input(make_input):
    """The golden input restated as a lender, with fresh comparable banks."""
    overrides: Dict[str, Any] = {
        "sector_profile": "financial",
        "financials.regulatory_crar_min_pct": 15.0,
        "peers": copy.deepcopy(BANK_PEERS),
    }
    for index, values in FINANCIAL_PERIODS.items():
        for key, value in values.items():
            overrides[f"financials.periods[{index}].{key}"] = value
    return make_input(**overrides)


def _epc_input(make_input):
    """The golden contractor, explicitly routed to the EPC/real-estate overlay."""
    return make_input(**{"sector_profile": "epc_real_estate"})


def _loss_input(make_input):
    """A pre-profit issuer: a negative latest PAT flips the auto profile.

    ``operating_loss_pct_revenue`` is the loss as a POSITIVE share of revenue
    (the reference configuration reads "operating loss (% of revenue)
    narrowing"), so a narrowing loss is a falling number: 22 -> 14 -> 6.
    Contribution margin expands over 300 bps two years running, the latest year
    consumed cash, and peer P/S is well above the issuer's.
    """
    return make_input(
        **{
            "financials.periods[0].contribution_margin_pct": 4.0,
            "financials.periods[0].operating_loss_pct_revenue": 22.0,
            "financials.periods[0].cfo": -1200.0,
            "financials.periods[1].contribution_margin_pct": 8.5,
            "financials.periods[1].operating_loss_pct_revenue": 14.0,
            "financials.periods[1].cfo": -900.0,
            "financials.periods[2].contribution_margin_pct": 13.0,
            "financials.periods[2].operating_loss_pct_revenue": 6.0,
            "financials.periods[2].cfo": -600.0,
            "financials.periods[2].pat": -250.0,
            "financials.periods[2].cash_and_equivalents": 3100.0,
            "peers": [
                {"name": "Peer Loss Co One Limited", "business_match": "match",
                 "listed_years": 4, "as_of": FRESH, "pe": 30.0, "pb": 3.00,
                 "ps": 6.00, "roe_pct": -4.00, "source_id": "PEER-SCREENER"},
                {"name": "Peer Loss Co Two Limited", "business_match": "match",
                 "listed_years": 6, "as_of": FRESH, "pe": 40.0, "pb": 4.00,
                 "ps": 8.00, "roe_pct": -7.00, "source_id": "PEER-SCREENER"},
            ],
        }
    )


@pytest.fixture
def bank_input(make_input):
    return _bank_input(make_input)


@pytest.fixture
def epc_input(make_input):
    return _epc_input(make_input)


@pytest.fixture
def loss_input(make_input):
    return _loss_input(make_input)


def _bank_input_dict(document):
    """An independent copy of a bank document, safe to mutate in a test."""
    return copy.deepcopy(document)


def _criterion(outcome, criterion_id):
    for module in outcome.score.modules:
        for item in module.criteria:
            if item.criterion_id == criterion_id:
                return item
    raise AssertionError(f"criterion {criterion_id!r} not found in the result")


# --------------------------------------------------------------------------
# financial -- NIM, asset quality, CRAR, ROE-adjusted P/B
# --------------------------------------------------------------------------


def test_financial_profile_swaps_in_the_lender_criteria(bank_input, config):
    outcome = run(bank_input, config)
    ids = [c.criterion_id for module in outcome.score.modules for c in module.criteria]
    for expected in ("nim_cost_income", "roa_roe_vs_peers", "asset_quality",
                     "crar_buffer", "pb_roe_adjusted"):
        assert expected in ids, f"{expected} missing from the financial plan"
    for replaced in ("margin_trend", "roce", "cfo_quality", "leverage", "second_multiple"):
        # s14: a replaced criterion leaves the plan rather than being duplicated.
        assert replaced not in ids, f"{replaced} should have been replaced"


def test_financial_overlay_derives_all_five_metrics(bank_input, config):
    outcome = run(bank_input, config)
    for metric_id in ("nim_cost_income_bucket", "roa_roe_peer_quartile",
                      "asset_quality_bucket", "crar_buffer_pts",
                      "pb_roe_adjusted_premium_pct"):
        derived = metric(outcome, metric_id)
        assert derived.state == "VALUE", f"{metric_id} -> {derived.state}: {derived.reason}"


def test_nim_cost_income_bucket_reads_nim_up_with_cost_down(bank_input, config):
    assert metric(run(bank_input, config), "nim_cost_income_bucket").value == "improving"


def test_asset_quality_bucket_reads_falling_gnpa_with_rising_coverage(bank_input, config):
    assert metric(run(bank_input, config), "asset_quality_bucket").value == "improving_strong"


def test_crar_buffer_is_measured_against_the_disclosed_minimum(bank_input, config):
    outcome = run(bank_input, config)
    assert metric(outcome, "crar_buffer_pts").value == pytest.approx(5.1)  # 20.10 - 15.00
    criterion = _criterion(outcome, "crar_buffer")
    assert criterion.state == "SCORED"
    assert criterion.score == 4.0  # >= 5pts over the minimum earns the top band


def test_a_thin_crar_buffer_scores_zero_without_becoming_an_error(bank_input, config):
    bank_input["financials"]["regulatory_crar_min_pct"] = 19.5
    outcome = run(bank_input, config)
    assert metric(outcome, "crar_buffer_pts").value == pytest.approx(0.6)
    criterion = _criterion(outcome, "crar_buffer")
    assert criterion.state == "SCORED"
    assert criterion.score == 0.0


def test_crar_buffer_falls_back_to_the_statutory_minimum_when_undisclosed(bank_input, config):
    """An undisclosed minimum is not a zero and does not make the metric UNKNOWN.

    The engine falls back to the 15% Basel III / ICDR minimum rather than
    treating the buffer as undefined.
    """
    bank_input["financials"].pop("regulatory_crar_min_pct", None)
    derived = metric(run(bank_input, config), "crar_buffer_pts")
    assert derived.state == "VALUE"
    assert derived.value == pytest.approx(20.10 - 15.0)


def test_roa_roe_peer_quartile_ranks_the_issuer_against_fresh_peers(bank_input, config):
    """Issuer ROE is ~34% against peer ROEs of 8% and 10%, so top quartile."""
    assert metric(run(bank_input, config), "roa_roe_peer_quartile").value == "top_quartile"


def test_roa_roe_peer_quartile_degrades_to_unknown_when_peers_go_stale(bank_input, config):
    """s13: a stale peer is not a peer. The quartile must not be invented."""
    for peer in bank_input["peers"]:
        peer["as_of"] = "2026-06-01"
    outcome = run(bank_input, config)
    derived = metric(outcome, "roa_roe_peer_quartile")
    assert derived.state == "UNKNOWN"
    assert "peer" in derived.reason.lower()


def test_pb_roe_adjusted_premium_scales_the_peer_multiple_to_the_issuer_roe(bank_input, config):
    """The peer P/B is restated at the issuer's ROE before the premium is taken.

    Unit-free check of the ROE adjustment: halving every peer ROE doubles the
    adjusted peer multiple, so the issuer's P/B is half as far above it and
    ``(premium + 100)`` halves too. Either using the raw peer P/B or ignoring
    the ROE adjustment entirely would leave the premium unchanged.
    """
    baseline = metric(run(bank_input, config), "pb_roe_adjusted_premium_pct")
    assert baseline.state == "VALUE"

    adjusted_document = _bank_input_dict(bank_input)
    for peer in adjusted_document["peers"]:
        peer["roe_pct"] = peer["roe_pct"] / 2.0  # 8.00, 10.00 -> 4.00, 5.00
    halved = metric(run(adjusted_document, config), "pb_roe_adjusted_premium_pct")
    assert halved.state == "VALUE"

    assert (halved.value + 100.0) == pytest.approx((baseline.value + 100.0) / 2.0, rel=1e-9)


def test_pb_roe_adjusted_premium_rewards_cheap_book_value(bank_input, config):
    """P/B 51% below the ROE-adjusted peer multiple earns the top band, 4 points."""
    outcome = run(bank_input, config)
    derived = metric(outcome, "pb_roe_adjusted_premium_pct")
    assert derived.value < -20.0
    criterion = _criterion(outcome, "pb_roe_adjusted")
    assert criterion.state == "SCORED"
    assert criterion.score == 4.0


def test_a_lender_without_cost_to_income_data_is_unknown_not_zero(bank_input, config):
    """s3.3 and s14: a missing overlay input must not score as a zero."""
    for period in bank_input["financials"]["periods"]:
        period.pop("cost_to_income_pct", None)
    outcome = run(bank_input, config)
    derived = metric(outcome, "nim_cost_income_bucket")
    assert derived.state == "UNKNOWN"
    assert "cost-to-income" in derived.reason
    criterion = _criterion(outcome, "nim_cost_income")
    assert criterion.state == "UNKNOWN"
    assert criterion.score is None  # no score at all, rather than a zero
    # The 5 points are reported as unknown rather than dropped from the
    # denominator, so the range accounts for them.
    assert outcome.score.unknown_points >= 5.0


def test_a_lender_without_asset_quality_data_is_unknown(bank_input, config):
    for period in bank_input["financials"]["periods"]:
        period.pop("gnpa_pct", None)
    outcome = run(bank_input, config)
    derived = metric(outcome, "asset_quality_bucket")
    assert derived.state == "UNKNOWN"
    assert _criterion(outcome, "asset_quality").state == "UNKNOWN"


# --------------------------------------------------------------------------
# epc_real_estate -- order book / CFO and net debt
# --------------------------------------------------------------------------


def test_epc_profile_swaps_in_order_book_and_net_debt(epc_input, config):
    outcome = run(epc_input, config)
    ids = [c.criterion_id for module in outcome.score.modules for c in module.criteria]
    assert "cfo_or_orderbook" in ids and "net_debt_trend_icr" in ids
    assert "cfo_quality" not in ids and "leverage" not in ids


def test_epc_net_debt_bucket_reads_the_balance_sheet_ratio(epc_input, config):
    outcome = run(epc_input, config)
    derived = metric(outcome, "net_debt_bucket")
    assert derived.state == "VALUE"
    latest, prior = epc_input["financials"]["periods"][-1], epc_input["financials"]["periods"][-2]
    ratio = (latest["total_debt"] - latest["cash_and_equivalents"]) / latest["net_worth"]
    prior_ratio = (prior["total_debt"] - prior["cash_and_equivalents"]) / prior["net_worth"]
    expected = ("strong" if ratio < 0.5 else
                "ok" if ratio < 1 else
                "stretched" if ratio <= 2 else "weak")
    if ratio < prior_ratio and expected in ("stretched", "weak"):
        expected = "ok"  # an improving ratio is not held against the issuer
    assert derived.value == expected
    assert derived.value == "ok"


def test_epc_reuses_the_standard_cumulative_cfo_ratio(epc_input, config):
    """cfo_pat_cumulative is a base metric; the overlay must not recompute it."""
    derived = metric(run(epc_input, config), "cfo_pat_cumulative")
    assert derived.state == "VALUE"
    assert derived.value == pytest.approx(1.788190, rel=1e-6)


# --------------------------------------------------------------------------
# loss_making -- contribution, runway, P/S and loss narrowing
# --------------------------------------------------------------------------


def test_loss_making_profile_is_selected_from_a_negative_latest_pat(loss_input, config):
    outcome = run(loss_input, config)
    assert outcome.record.plan["resolved_profile"] == "loss_making"
    assert outcome.record.plan["auto_profile_applied"] == "loss_making"
    ids = [c.criterion_id for module in outcome.score.modules for c in module.criteria]
    for expected in ("contribution_margin", "cash_runway", "ps_evsales_vs_peers",
                     "operating_loss_narrowing"):
        assert expected in ids
    for replaced in ("margin_trend", "roce", "cfo_quality", "pe_vs_peers", "peg"):
        assert replaced not in ids


def test_contribution_bucket_reads_two_years_of_expansion(loss_input, config):
    assert metric(run(loss_input, config), "contribution_bucket").value == "expanding_2y_gt300bps"


def test_loss_narrowing_bucket_reads_two_consecutive_years(loss_input, config):
    assert metric(run(loss_input, config), "loss_narrowing_bucket").value == "two_years"


def test_a_widening_loss_is_reported_as_widening(loss_input, config):
    """The mirror case: the loss share grows, so the bucket must flip."""
    for period, loss in zip(loss_input["financials"]["periods"], (6.0, 14.0, 22.0)):
        period["operating_loss_pct_revenue"] = loss
    assert metric(run(loss_input, config), "loss_narrowing_bucket").value == "widening"


def test_cash_runway_is_cash_plus_the_fresh_issue_over_the_monthly_burn(loss_input, config):
    outcome = run(loss_input, config)
    derived = metric(outcome, "cash_runway_months")
    assert derived.state == "VALUE"
    latest = loss_input["financials"]["periods"][-1]
    burn = -latest["cfo"] / 12.0
    expected = (latest["cash_and_equivalents"] + loss_input["issue"]["fresh_issue"]) / burn
    assert derived.value == pytest.approx(expected, rel=1e-9)


def test_runway_is_not_applicable_when_the_issuer_is_not_burning_cash(loss_input, config):
    """s3.1: the third state exists -- 'not burning cash' is not 'no data'."""
    for period in loss_input["financials"]["periods"]:
        period["cfo"] = 500.0
    derived = metric(run(loss_input, config), "cash_runway_months")
    assert derived.state == "NOT_APPLICABLE"
    assert "not cash-consumptive" in derived.reason


def test_loss_making_ps_premium_uses_the_peer_median(loss_input, config):
    derived = metric(run(loss_input, config), "ps_premium_pct")
    assert derived.state == "VALUE"
    # Peer P/S of 6.00 and 8.00 -> median 7.00; the issuer trades well below it.
    assert derived.value < 0


def test_loss_making_overlay_reports_its_own_completeness(loss_input, config):
    """A profile swap changes the denominator, so the totals must follow it."""
    outcome = run(loss_input, config)
    assert outcome.score.available_points > 0
    assert outcome.score.unknown_points >= 0
    assert outcome.score.available_points + outcome.score.unknown_points == 100.0
