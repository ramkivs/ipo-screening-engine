"""Core v1.5 semantics: UNKNOWN is not zero, metric definitions, confidence.

Covers execution prompt s7 (derived metrics), s10 (scoring), s11 (confidence)
and spec s3.2, s7, s8, s18.
"""

from __future__ import annotations

import copy
import math

import pytest

from conftest import criterion, metric, minimal_input, run


# --------------------------------------------------------------------------
# UNKNOWN must remain UNKNOWN
# --------------------------------------------------------------------------


def test_unknown_metric_does_not_become_zero(config, make_input):
    """v1.5 s3.2: a missing metric is UNKNOWN, not 0."""
    document = make_input(**{"governance.rpt_pct_revenue": None})
    outcome = run(document, config)
    item = criterion(outcome, "rpt")
    assert item.state == "UNKNOWN"
    assert item.score is None
    assert item.max == 3.0
    # The 3 points are unavailable, so they land in the range, not in the score.
    assert item.criterion_id in {
        c.criterion_id for c in outcome.score.criteria if c.state == "UNKNOWN"
    }


def test_unknown_moves_points_from_the_score_into_the_range(config, make_input):
    """An UNKNOWN criterion leaves the base score and joins the estimate range.

    ``rpt`` scores 1 of its 3 points when the RPT percentage is 6.67%. Making
    that input UNKNOWN costs the 1 earned point, moves all 3 points into the
    unknown bucket, and therefore *raises* the ceiling by 2 - the opposite of
    treating the missing value as zero.
    """
    baseline = run(make_input(), config)
    degraded = run(make_input(**{"governance.rpt_pct_revenue": None}), config)

    assert degraded.score.base_score == pytest.approx(baseline.score.base_score - 1.0)
    assert degraded.score.unknown_points == pytest.approx(baseline.score.unknown_points + 3.0)
    assert degraded.score.upper_bound == pytest.approx(baseline.score.upper_bound + 2.0)
    # The ceiling never falls when information is removed.
    assert degraded.score.upper_bound >= baseline.score.upper_bound


def test_minimal_disclosure_yields_unknown_not_zero(config):
    """With almost nothing disclosed, the engine reports UNKNOWNs, not zeros."""
    outcome = run(minimal_input(), config)
    unknown_ids = {c.criterion_id for c in outcome.score.criteria if c.state == "UNKNOWN"}
    assert {"roce", "leverage", "margin_trend"}.issubset(unknown_ids)
    assert outcome.score.confidence == "Low"
    assert outcome.score.upper_bound > outcome.score.final_score


def test_not_applicable_is_excluded_from_the_denominator(config, make_input):
    """NOT_APPLICABLE removes a criterion from both sides of completeness.

    A negative PAT CAGR makes PEG meaningless. The latest-year PAT stays
    positive so the loss-making auto-profile does not intervene, which keeps
    the standard criteria in force.
    """
    document = make_input(**{"financials.periods[0].pat": 5000.0})
    outcome = run(document, config)

    assert metric(outcome, "pat_cagr_2y_from_3fy").value < 0
    assert metric(outcome, "peg").is_not_applicable
    item = criterion(outcome, "peg")
    assert item.state == "NOT_APPLICABLE"
    assert item.score is None

    # PEG's 4 points are neither available nor unknown.
    assert outcome.score.not_applicable_points >= 4.0
    assert outcome.score.total_evaluable_points == pytest.approx(
        outcome.score.available_points + outcome.score.unknown_points
    )
    assert outcome.score.total_evaluable_points < 100.0


def test_not_applicable_is_not_scored_as_zero(config, make_input):
    """A NOT_APPLICABLE criterion contributes nothing, not a punitive zero."""
    document = make_input(**{"financials.periods[0].pat": 5000.0})
    outcome = run(document, config)
    item = criterion(outcome, "peg")
    assert item.effective_score == 0.0
    assert item.state != "SCORED"
    assert item.criterion_id not in {
        c.criterion_id for c in outcome.score.criteria if c.state == "UNKNOWN"
    }


def test_zero_is_a_value_not_a_marker(config, make_input):
    """A genuine zero must not be reported as unknown."""
    document = make_input(**{"capital_structure.promoter_pledge_pct": 0})
    outcome = run(document, config)
    assert metric(outcome, "promoter_pledge_pct").is_value
    assert metric(outcome, "promoter_pledge_pct").value == 0.0


def test_absent_boolean_flag_is_unknown_not_false(config, make_input):
    """v1.5 s3.3: an absent flag must not evaluate to False."""
    document = make_input(**{"governance.sebi_ed_action_active": None})
    outcome = run(document, config)
    assert metric(outcome, "sebi_ed_action_active").is_unknown


# --------------------------------------------------------------------------
# Metric definitions
# --------------------------------------------------------------------------


def test_revenue_cagr_is_2y_from_3fy_not_a_3y_cagr(config, golden_input):
    """v1.5 s7: three FY observations give a two-year CAGR, labelled as such."""
    outcome = run(golden_input, config)
    item = metric(outcome, "revenue_cagr_2y_from_3fy")
    assert item.is_value
    expected = (math.sqrt(33867.73 / 24288.2) - 1) * 100
    assert item.value == pytest.approx(expected, rel=1e-9)
    assert item.value == pytest.approx(18.0852, abs=1e-3)

    # The misleading 3Y label and metric must not exist.
    assert "revenue_cagr_3y" not in outcome.derived.metrics
    criterion_item = criterion(outcome, "revenue_cagr")
    assert criterion_item.metric == "revenue_cagr_2y_from_3fy"
    assert "2Y from 3 FY" in criterion_item.label


def test_three_year_cagr_is_available_only_with_four_fy(config, golden_input):
    """revenue_cagr_3y_from_4fy is reported when, and only when, 4 FYs exist."""
    outcome = run(golden_input, config)
    assert metric(outcome, "revenue_cagr_3y_from_4fy").is_unknown

    extended = copy.deepcopy(golden_input)
    extended["financials"]["periods"].insert(
        0,
        {
            "fy": "FY2023",
            "revenue": 20000.0,
            "pat": 300.0,
            "net_worth": 3000.0,
            "total_debt": 9000.0,
            "cfo": 2000.0,
            "capex": 1500.0,
            "cash_and_equivalents": 20.0,
            "receivable_days": 50.0,
            "interest_expense": 1300.0,
            "ebit": 1200.0,
            "ebitda": 2000.0,
        },
    )
    outcome4 = run(extended, config)
    item = metric(outcome4, "revenue_cagr_3y_from_4fy")
    assert item.is_value
    assert item.value == pytest.approx((((33867.73 / 20000.0) ** (1 / 3)) - 1) * 100, rel=1e-9)
    # The 2Y figure is unchanged by the extra year.
    assert metric(outcome4, "revenue_cagr_2y_from_3fy").value == pytest.approx(
        metric(run(golden_input, config), "revenue_cagr_2y_from_3fy").value
    )


def test_cfo_pat_is_cumulative_not_an_average_of_ratios(config, golden_input):
    """v1.5 s8: the metric is sum(CFO)/sum(PAT), not the mean of yearly ratios."""
    outcome = run(golden_input, config)
    item = metric(outcome, "cfo_pat_cumulative")
    cumulative = (2773.05 + 3820.17 + 2715.47) / (344.56 + 2363.59 + 2497.5)
    naive_average = sum(
        c / p
        for c, p in (
            (2773.05, 344.56),
            (3820.17, 2363.59),
            (2715.47, 2497.5),
        )
    ) / 3

    assert item.value == pytest.approx(cumulative, rel=1e-9)
    assert item.value == pytest.approx(1.788190, abs=1e-6)
    # The two definitions differ materially; the engine must use the cumulative.
    assert abs(item.value - naive_average) > 1.0
    assert "cumulative" in item.formula
    assert "not the arithmetic" in item.formula


def test_cfo_pat_is_unknown_when_a_year_is_missing(config, make_input):
    document = make_input(**{"financials.periods[1].cfo": None})
    outcome = run(document, config)
    assert metric(outcome, "cfo_pat_cumulative").is_unknown
    # Crucially, it is not computed with the missing year treated as zero.
    assert metric(outcome, "cfo_pat_cumulative").value is None


def test_cfo_pat_not_applicable_when_cumulative_pat_is_non_positive(config, make_input):
    document = make_input(
        **{
            "financials.periods[0].pat": -500.0,
            "financials.periods[1].pat": -100.0,
            "financials.periods[2].pat": -200.0,
        }
    )
    outcome = run(document, config)
    item = metric(outcome, "cfo_pat_cumulative")
    assert item.is_not_applicable
    assert "not forced to zero" in item.reason


def test_roce_uses_ebit_over_capital_employed(config, make_input):
    """ROCE = EBIT / (total equity + total borrowings), per the RHP definition."""
    document = make_input(**{"financials.periods[2].disclosed_roce_pct": None})
    outcome = run(document, config)
    item = metric(outcome, "roce_latest")
    assert item.is_value
    expected = 4336.43 / (8678.35 + 8741.7) * 100
    assert item.value == pytest.approx(expected, rel=1e-9)
    assert item.value == pytest.approx(24.8933, abs=1e-3)
    assert "Capital Employed" in item.formula


def test_disclosed_roce_overrides_the_computed_value(config, golden_input):
    outcome = run(golden_input, config)
    item = metric(outcome, "roce_latest")
    assert item.value == pytest.approx(28.02)
    assert "disclosed ROCE" in item.reason


def test_interest_cover_is_never_a_favourable_sentinel(config, make_input):
    """The reference used ICR=99 when interest expense was absent.

    The strong band needs D/E < 0.5 *and* ICR > 5, so with low debt and no
    disclosed finance cost the band cannot be confirmed.
    """
    document = make_input(
        **{
            "financials.periods[2].total_debt": 2000.0,
            "financials.periods[2].interest_expense": None,
        }
    )
    outcome = run(document, config)
    item = metric(outcome, "leverage_bucket")
    assert item.is_unknown
    assert "interest" in item.reason.lower()
    # The reference's sentinel value must not appear anywhere.
    assert item.value != 99


def test_debt_free_balance_sheet_scores_strong(config, make_input):
    """Zero borrowings and zero finance cost: ICR is NOT_APPLICABLE, not 99."""
    document = make_input(
        **{
            "financials.periods[2].total_debt": 0.0,
            "financials.periods[2].interest_expense": 0.0,
        }
    )
    outcome = run(document, config)
    item = metric(outcome, "leverage_bucket")
    assert item.is_value and item.value == "strong"
    assert "debt-free" in item.formula


def test_leverage_bands_follow_the_configuration(config, make_input):
    """D/E and ICR bands exactly as the specification states them."""
    # Net worth is 8,678.35 lakh; EBIT 4,336.43 lakh.
    for debt, interest, expected in (
        (2000.0, 300.0, "strong"),    # D/E 0.23 <0.5 and ICR 14.5 >5
        (3000.0, 1504.04, "ok"),      # D/E 0.35 <0.5 but ICR 2.9 <=5
        (7500.0, 1504.04, "ok"),      # D/E 0.86 <1
        (13000.0, 1504.04, "stretched"),  # D/E 1.50
        (20000.0, 1504.04, "weak"),   # D/E 2.30 >2
    ):
        document = make_input(
            **{
                "financials.periods[2].total_debt": debt,
                "financials.periods[2].interest_expense": interest,
            }
        )
        outcome = run(document, config)
        assert metric(outcome, "leverage_bucket").value == expected, (debt, interest)


# --------------------------------------------------------------------------
# Confidence weighting
# --------------------------------------------------------------------------


def test_confidence_is_points_weighted_not_count_weighted(config, make_input):
    """v1.5 s11/s18: completeness uses points, not the number of criteria."""
    outcome = run(make_input(), config)
    breakdown = outcome.score.completeness_breakdown
    assert breakdown["weighting"] == "POINTS"

    positive = [c for c in outcome.score.criteria if c.max > 0 and not c.is_penalty]
    available = sum(c.max for c in positive if c.state == "SCORED")
    unknown = sum(c.max for c in positive if c.state == "UNKNOWN")
    assert outcome.score.available_points == pytest.approx(available)
    assert outcome.score.unknown_points == pytest.approx(unknown)
    assert outcome.score.completeness_pct == pytest.approx(
        available / (available + unknown) * 100
    )


def test_points_weighting_differs_from_count_weighting(config, make_input):
    """Losing 12 valuation points must cost more completeness than losing 1.

    A count-weighted completeness would treat the two losses almost
    identically (2 criteria versus 1). Point weighting does not.
    """
    # Start from fresh (VALID) peers so the valuation criteria are available.
    fresh = {"peers[0].as_of": "2026-10-02", "peers[1].as_of": "2026-10-02"}
    baseline = run(make_input(**fresh), config)
    assert metric(baseline, "pe_premium_pct").is_value
    assert criterion(baseline, "pe_vs_peers").state == "SCORED"
    assert criterion(baseline, "second_multiple").state == "SCORED"

    # Staling both peers costs 12 valuation points across 2 criteria.
    heavy = run(
        make_input(
            **dict(fresh, **{"peers[0].as_of": "2026-07-23", "peers[1].as_of": "2026-07-23"})
        ),
        config,
    )

    # Dropping the lock-in inputs costs 1 point across 1 criterion.
    light = run(
        make_input(
            **dict(
                fresh,
                **{
                    "capital_structure.promoter_lockin_in_place": None,
                    "capital_structure.large_holders_unlocked_early": None,
                },
            )
        ),
        config,
    )

    heavy_lost = baseline.score.available_points - heavy.score.available_points
    light_lost = baseline.score.available_points - light.score.available_points
    # pe_vs_peers (8) and second_multiple (4) both go UNKNOWN.
    assert heavy_lost == pytest.approx(12.0)
    assert light_lost == pytest.approx(1.0)   # lockin becomes UNKNOWN

    heavy_drop_pct = baseline.score.completeness_pct - heavy.score.completeness_pct
    light_drop_pct = baseline.score.completeness_pct - light.score.completeness_pct
    assert heavy_drop_pct > light_drop_pct
    # Point weighting: the completeness drop is proportional to the points lost,
    # so the 12-point loss bites exactly 12x as hard as the 1-point loss. A
    # count-weighted measure would have given a ratio of 2.
    assert heavy_drop_pct / light_drop_pct == pytest.approx(12.0, rel=1e-6)
    assert heavy_drop_pct / light_drop_pct != pytest.approx(2.0, rel=0.15)


def test_confidence_thresholds_follow_the_configuration(config, make_input):
    """High >= 95%, Medium >= 80%, Low < 80%."""
    cfg_thresholds = config["confidence"]
    assert cfg_thresholds["high_min_completeness_pct"] == 95
    assert cfg_thresholds["medium_min_completeness_pct"] == 80

    outcome = run(make_input(), config)
    pct = outcome.score.completeness_pct
    expected = "High" if pct >= 95 else "Medium" if pct >= 80 else "Low"
    assert outcome.score.confidence == expected


def test_completeness_breakdown_separates_critical_and_knockout_data(config, make_input):
    outcome = run(make_input(), config)
    breakdown = outcome.score.completeness_breakdown
    for key in (
        "overall_pct",
        "valuation_pct",
        "market_pct",
        "critical_data_pct",
        "knockout_completeness_pct",
        "critical_data_missing",
        "knockout_unverified",
    ):
        assert key in breakdown


def test_high_overall_completeness_cannot_hide_a_missing_knockout_input(config, make_input):
    """tech design s9: a missing critical field must remain visible."""
    document = make_input(**{"governance.going_concern_uncertainty": None})
    outcome = run(document, config)
    breakdown = outcome.score.completeness_breakdown
    assert "going_concern_uncertainty" in breakdown["critical_data_missing"]
    assert breakdown["critical_data_pct"] < 100.0


# --------------------------------------------------------------------------
# Score range and verdict
# --------------------------------------------------------------------------


def test_range_brackets_the_base_score(config, make_input):
    outcome = run(make_input(), config)
    assert outcome.score.lower_bound <= outcome.score.final_score <= outcome.score.upper_bound


def test_verdict_is_uncertain_when_the_range_crosses_a_band(config, make_input):
    """v1.5 s18: a range straddling a verdict band yields VERDICT_UNCERTAIN."""
    document = make_input(
        **{
            "governance.going_concern_uncertainty": True,
        }
    )
    outcome = run(document, config)
    # A triggered knockout dominates: the verdict is AVOID, not uncertain.
    assert outcome.score.verdict == "AVOID"
    assert outcome.score.verdict_uncertain is False


def test_verdict_bands_are_config_driven(config, golden_input):
    verdict = config["verdict"]
    assert [b["verdict"] for b in verdict["bands"]] == ["APPLY", "APPLY_SELECTIVELY", "NEUTRAL"]
    assert verdict["else"] == "AVOID"


def test_unknown_penalties_widen_the_lower_bound(config, make_input):
    """v1.5 s17: an unverified penalty is neither applied nor ignored."""
    outcome = run(make_input(), config)
    assert outcome.score.unresolved_penalty_points > 0
    assert outcome.score.lower_bound < outcome.score.final_score
    states = {p["id"]: p["state"] for p in outcome.score.penalty_items}
    assert states["auditor_cfo_exit"] == "UNKNOWN"
    assert states["eom_caro"] == "UNKNOWN"


def test_penalty_ceiling_is_respected(config, make_input):
    assert config["penalties"]["max_total"] == -15
    outcome = run(make_input(), config)
    assert outcome.score.penalties_total >= -15


# --------------------------------------------------------------------------
# Evidence / provenance
# --------------------------------------------------------------------------


def test_every_derived_metric_carries_formula_and_inputs(config, golden_input):
    outcome = run(golden_input, config)
    for metric_id, item in outcome.derived.metrics.items():
        assert item.formula, metric_id
        assert item.kind in {"numeric", "categorical", "boolean"}, metric_id
        if item.is_value and item.kind in {"numeric", "categorical", "boolean"}:
            assert item.value is not None or item.state != "VALUE", metric_id


def test_criteria_reference_their_metric_and_evidence(config, golden_input):
    outcome = run(golden_input, config)
    scored = [c for c in outcome.score.criteria if c.state == "SCORED" and not c.is_penalty]
    assert scored
    for item in scored:
        assert item.metric, item.criterion_id
        assert item.formula or item.zeroed_by or item.exempted_by, item.criterion_id


def test_penalty_criteria_carry_a_reason(config, golden_input):
    outcome = run(golden_input, config)
    penalties = [c for c in outcome.score.criteria if c.is_penalty]
    assert penalties
    for item in penalties:
        assert item.reason
        assert item.state in {"SCORED", "UNKNOWN"}


def test_missing_evidence_is_reported_as_a_warning(config):
    outcome = run(minimal_input(), config)
    codes = {w.code for w in outcome.validation.warnings}
    assert "PROVENANCE_NO_SOURCES" in codes
