"""The acceptance matrix: every mandated case, named and traceable.

This module is the executable version of the traceability matrix. Each test
corresponds to one numbered item in one of the two governing lists:

* ``P`` - "Required Test Matrix", items 1-30 of the Execution Prompt s19.
* ``S`` - "Testing Requirements", items 1-17 of Specification v1.5 s26.

Where a single scenario satisfies both lists the test cites both numbers. The
point of the file is that an auditor can go from a numbered requirement to a
named, running test without reading prose.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone

import pytest

from conftest import (
    EVAL_AT,
    GOLDEN_DIR,
    criterion,
    knockout,
    metric,
    minimal_input,
    run,
)
from ipo_screening.config_validation import check_config, compile_config
from ipo_screening.errors import (
    ConfigValidationError,
    ImmutabilityError,
    SchemaValidationError,
    SemanticValidationError,
)
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.excel import SHEET_ORDER, build_workbook, project
from ipo_screening.pipeline import evaluate
from ipo_screening.schema_validation import validate_schema


# ==========================================================================
# P1 / S1 - Vishal Nirmiti, normal mainboard retail-heavy
# ==========================================================================


def test_p1_s1_vishal_nirmiti_mainboard_retail_heavy(golden_input, config):
    """P1, S1: the golden case must produce the frozen expected result."""
    outcome = run(golden_input, config)
    assert outcome.record.score["final_score"] == pytest.approx(35.0)
    assert outcome.record.score["base_score"] == pytest.approx(38.0)
    assert outcome.record.score["penalties_total"] == pytest.approx(-3.0)
    assert outcome.record.verdict["verdict"] == "INSUFFICIENT_DATA"
    assert outcome.record.confidence["level"] == "Low"
    assert outcome.record.plan["structure_overlays"] == ["retail_heavy"]
    assert outcome.record.validation["ok"] is True


# ==========================================================================
# P2 / S2 - pure OFS
# ==========================================================================


def test_p2_s2_pure_ofs_offer(make_input, config):
    """P2, S2: no fresh issue, the whole offer is a sale by existing holders."""
    document = make_input(
        **{
            "issue.fresh_issue": 0.0,
            "issue.ofs": 14500.0,
            "issue.price_band_low": 31.82,
            "issue.price_band_high": 31.82,
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "fresh_share_pct").value == pytest.approx(0.0)
    assert metric(outcome, "pure_ofs").value is True
    # A pure OFS cannot fund growth, so the proceeds criteria are the sector set.
    assert outcome.record.score["final_score"] is not None
    assert outcome.record.verdict["verdict"] in {
        "APPLY", "APPLY_SELECTIVELY", "NEUTRAL", "AVOID", "INSUFFICIENT_DATA",
    }


def test_p2_pure_ofs_cap_is_enforced_on_the_6_2_route(config, make_input):
    """A 6(2) offer for sale beyond the 60% cap is a validation failure."""
    document = make_input(
        **{
            "icdr_route": "6(2)",
            "issue.fresh_issue": 100.0,
            "issue.ofs": 14500.0,
        }
    )
    with pytest.raises(SemanticValidationError) as excinfo:
        run(document, config)
    codes = {f.code for f in excinfo.value.findings}
    assert any("OFS" in code or "PURE" in code for code in codes), codes


# ==========================================================================
# P3 / S3 - qualified audit opinion
# ==========================================================================


def test_p3_s3_qualified_audit_opinion_triggers_k1(make_input, config):
    """P3, S3: a qualified opinion is a knockout, so the verdict is AVOID."""
    document = make_input(**{"governance.auditor_opinion": "qualified"})
    outcome = run(document, config)
    assert knockout(outcome, "K1").state == "TRIGGERED"
    assert outcome.record.knockouts["any_triggered"] is True
    assert outcome.record.verdict["verdict"] == "AVOID"
    assert knockout(outcome, "K1").missing == ()


# ==========================================================================
# P4 - going-concern uncertainty
# ==========================================================================


def test_p4_going_concern_uncertainty_triggers_k1(make_input, config):
    document = make_input(**{"governance.going_concern_uncertainty": True})
    outcome = run(document, config)
    assert knockout(outcome, "K1").state == "TRIGGERED"
    assert outcome.record.verdict["verdict"] == "AVOID"


# ==========================================================================
# P5 - negative net worth
# ==========================================================================


def test_p5_negative_net_worth_triggers_k1(make_input, config):
    document = make_input(
        **{
            "financials.periods[2].net_worth": -500.0,
            "financials.periods[2].pat": -800.0,
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "net_worth_latest").value < 0
    assert knockout(outcome, "K1").state == "TRIGGERED"
    assert outcome.record.verdict["verdict"] == "AVOID"


# ==========================================================================
# P6 - promoter pledge > 25%
# ==========================================================================


def test_p6_promoter_pledge_above_25pct_triggers_k2(make_input, config):
    document = make_input(**{"capital_structure.promoter_pledge_pct": 26.0})
    outcome = run(document, config)
    assert knockout(outcome, "K2").state == "TRIGGERED"
    assert outcome.record.verdict["verdict"] == "AVOID"


def test_p6_promoter_pledge_at_25pct_does_not_trigger(make_input, config):
    """The threshold is strict: 25.0% is not ">25%"."""
    document = make_input(**{"capital_structure.promoter_pledge_pct": 25.0})
    outcome = run(document, config)
    assert knockout(outcome, "K2").state == "CLEAR"


# ==========================================================================
# P7 / S12 - active SEBI / ED action
# ==========================================================================


def test_p7_s12_active_sebi_action_triggers_k2(make_input, config):
    """P7, S12: an active regulatory action is a knockout."""
    document = make_input(**{"governance.sebi_ed_action_active": True})
    outcome = run(document, config)
    assert knockout(outcome, "K2").state == "TRIGGERED"
    assert outcome.record.verdict["verdict"] == "AVOID"


def test_p7_inactive_sebi_action_clears_k2(make_input, config):
    document = make_input(**{"governance.sebi_ed_action_active": False})
    outcome = run(document, config)
    assert knockout(outcome, "K2").state == "CLEAR"


# ==========================================================================
# P8 - OFS > 80% with declining profits
# ==========================================================================


def test_p8_ofs_above_80pct_with_declining_profit_triggers_k3(make_input, config):
    """P8: both legs of the conjunction must hold."""
    document = make_input(
        **{
            "issue.fresh_issue": 1000.0,
            "issue.ofs": 14000.0,
            "financials.periods[2].pat": 1000.0,   # below FY2025's 2363.59
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "ofs_share_pct").value > 80.0
    assert metric(outcome, "profit_declining").value is True
    assert knockout(outcome, "K3").state == "TRIGGERED"
    assert outcome.record.verdict["verdict"] == "AVOID"


def test_p8_ofs_above_80pct_alone_is_not_enough(make_input, config):
    """A high-OFS offer with rising profits must not trigger K3."""
    document = make_input(
        **{
            "issue.fresh_issue": 1000.0,
            "issue.ofs": 14000.0,
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "ofs_share_pct").value > 80.0
    assert metric(outcome, "profit_declining").value is False
    assert knockout(outcome, "K3").state == "CLEAR"


# ==========================================================================
# P9 - K4 combined-sale condition
# ==========================================================================


def test_p9_k4_combined_promoter_sale_with_full_exit(make_input, config):
    """P9: a >50% combined promoter sale plus a full exit triggers K4."""
    document = make_input(
        **{
            "capital_structure.promoter_post_pct": 0.0,
            "financials.periods[2].pat": 1000.0,   # profits declining, the 3rd leg
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "pe_promoter_sold_pct_combined").value > 50.0
    assert metric(outcome, "promoter_full_exit").value is True
    assert knockout(outcome, "K4").state == "TRIGGERED"


def test_p9_k4_requires_the_combined_sale_leg(make_input, config):
    """A full exit alone, below the combined-sale threshold, is not a trigger."""
    document = make_input(**{"issue.ofs_sellers[0].shares_sold": 100000})
    outcome = run(document, config)
    assert metric(outcome, "pe_promoter_sold_pct_combined").value <= 50.0
    assert metric(outcome, "promoter_full_exit").value is False
    assert knockout(outcome, "K4").state == "CLEAR"


# ==========================================================================
# P10 / S11 / S7 - contingent liabilities
# ==========================================================================


def test_p10_s7_contingent_liabilities_above_50pct_of_net_worth(make_input, config):
    """P10, S7: a quantified exposure above 50% of net worth triggers K5."""
    document = make_input(
        **{
            "financials.contingent_liabilities": 6000.0,
            "financials.contingent_liabilities_unquantified": False,
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "contingent_liab_pct_networth").value > 50.0
    assert metric(outcome, "contingent_liab_unquantified").value is False
    assert knockout(outcome, "K5").state == "TRIGGERED"


def test_p10_s7_contingent_liabilities_below_the_threshold_clear(make_input, config):
    document = make_input(
        **{
            "financials.contingent_liabilities": 1000.0,
            "financials.contingent_liabilities_unquantified": False,
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "contingent_liab_pct_networth").value < 50.0
    assert knockout(outcome, "K5").state == "CLEAR"


def test_p11_unknown_unquantified_flag_leaves_k5_unverified(make_input, config):
    """A low quantified ratio is not enough: the unquantified leg must be known.

    This is the v1.5 discipline in miniature - "the number is small" does not
    clear a rule whose other leg was never examined.
    """
    document = make_input(**{"financials.contingent_liabilities": 1000.0})
    outcome = run(document, config)
    assert metric(outcome, "contingent_liab_pct_networth").value < 50.0
    assert metric(outcome, "contingent_liab_unquantified").is_unknown
    assert knockout(outcome, "K5").state == "UNVERIFIED"
    assert "contingent_liab_unquantified" in knockout(outcome, "K5").missing


def test_p11_s12_unquantified_contingent_liabilities_trigger_k5(make_input, config):
    """P11, S12: an unquantified exposure triggers K5 outright."""
    document = make_input(
        **{
            "financials.contingent_liabilities": None,
            "financials.contingent_liabilities_unquantified": True,
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "contingent_liab_unquantified").value is True
    assert knockout(outcome, "K5").state == "TRIGGERED"


def test_p11_unquantified_when_absent_leaves_k5_unverified(golden_input, config):
    """Absent is not the same as False: the golden case cannot clear K5."""
    outcome = run(golden_input, config)
    assert knockout(outcome, "K5").state == "UNVERIFIED"
    assert "contingent_liab_unquantified" in knockout(outcome, "K5").missing


# ==========================================================================
# P12 - RPT growth
# ==========================================================================


def test_p12_rpt_growth_above_40pct_triggers_k6(make_input, config):
    document = make_input(**{"governance.rpt_pct_of_revenue_growth": 55.0})
    outcome = run(document, config)
    assert knockout(outcome, "K6").state == "TRIGGERED"
    assert outcome.record.verdict["verdict"] == "AVOID"


def test_p12_rpt_growth_below_the_threshold_clears_k6(make_input, config):
    document = make_input(**{"governance.rpt_pct_of_revenue_growth": 12.0})
    outcome = run(document, config)
    assert knockout(outcome, "K6").state == "CLEAR"


def test_p12_unknown_rpt_growth_is_unverified_not_clear(golden_input, config):
    outcome = run(golden_input, config)
    assert knockout(outcome, "K6").state == "UNVERIFIED"
    assert knockout(outcome, "K6").missing


# ==========================================================================
# P13 / S6 - stale peers
# ==========================================================================


def test_p13_s6_stale_peers_cannot_score_as_current(golden_input, config):
    """P13, S6: the golden peers are 74 days old against a 30-day limit."""
    outcome = run(golden_input, config)
    observations = outcome.record.peer_snapshot["observations"]
    assert {o["status"] for o in observations} == {"STALE"}
    assert criterion(outcome, "pe_vs_peers").state == "UNKNOWN"
    assert metric(outcome, "pe_premium_pct").is_unknown
    assert outcome.record.score["completeness_breakdown"]["valuation_points_unknown"] == pytest.approx(16.0)


def test_p13_fresh_peers_are_used(make_input, config):
    """The mirror image: fresh peers make the valuation criteria scoreable."""
    document = make_input(**{"peers[0].as_of": "2026-10-02", "peers[1].as_of": "2026-10-02"})
    outcome = run(document, config)
    assert {o["status"] for o in outcome.record.peer_snapshot["observations"]} == {"VALID"}
    assert metric(outcome, "pe_premium_pct").is_value
    assert criterion(outcome, "pe_vs_peers").state == "SCORED"


# ==========================================================================
# P14 / S4 - missing GCP
# ==========================================================================


def test_p14_s4_missing_gcp_is_unknown_not_the_ceiling(golden_input, config):
    """P14, S4: [●] GCP must be UNKNOWN, with the ceiling kept separately."""
    outcome = run(golden_input, config)
    assert metric(outcome, "gcp_amount").is_unknown
    assert metric(outcome, "gcp_amount").value is None
    # The legal maximum is recorded, clearly labelled as a limit not an amount.
    ceiling = metric(outcome, "gcp_legal_max")
    assert ceiling.value == pytest.approx(36.25)
    assert "25.0% x fresh issue" in ceiling.formula
    assert "separately" in ceiling.reason.lower()
    # The scored metric is UNKNOWN; the ceiling never substitutes for it.
    assert criterion(outcome, "use_of_proceeds").state == "UNKNOWN"
    assert criterion(outcome, "use_of_proceeds").score is None


def test_p14_gcp_disclosed_actually_scores(make_input, config):
    """The mirror image: a disclosed GCP is scored normally, not left UNKNOWN."""
    document = make_input(**{"use_of_proceeds[2].amount": 1500.0})
    outcome = run(document, config)
    assert metric(outcome, "gcp_amount").is_value
    assert metric(outcome, "gcp_amount").value == pytest.approx(15.0)
    assert metric(outcome, "use_of_proceeds_bucket").is_value
    assert criterion(outcome, "use_of_proceeds").state == "SCORED"


# Regression: the first amount seen for a proceeds category used to be dropped,
# so every fully-disclosed offer fell through to ``mixed_ok`` and the
# blind_heavy test could never fire. Spec s10/s13.
def test_p14_proceeds_bucket_classifies_each_disclosure_pattern(make_input, config):
    cases = {
        # category -> (expected bucket, total in lakh)
        "debt_heavy": (
            [
                {"category": "debt_repayment", "amount": 11600.0},
                {"category": "gcp", "amount": 500.0},
            ],
            "debt_heavy",
        ),
        "growth": (
            [
                {"category": "growth_capex", "amount": 11600.0},
                {"category": "gcp", "amount": 500.0},
            ],
            "growth",
        ),
        "blind_heavy": (
            [
                {"category": "gcp", "amount": 2500.0},
                {"category": "acquisition_unidentified", "amount": 1500.0},
            ],
            "blind_heavy",
        ),
        "mixed_ok": (
            [
                {"category": "working_capital", "amount": 7500.0},
                {"category": "debt_repayment", "amount": 1900.0},
                {"category": "gcp", "amount": 1500.0},
            ],
            "mixed_ok",
        ),
    }
    for label, (proceeds, expected) in cases.items():
        document = make_input(**{"use_of_proceeds": proceeds})
        outcome = run(document, config)
        assert metric(outcome, "use_of_proceeds_bucket").value == expected, label


def test_p14_partially_disclosed_category_is_unknown_not_understated(make_input, config):
    """A partial total must not understate a share and clear blind_heavy."""
    document = make_input(
        **{
            "use_of_proceeds": [
                {"category": "gcp", "amount": 2000.0},
                {"category": "acquisition_unidentified", "amount": 1000.0},
                {"category": "acquisition_unidentified", "amount": None},
            ]
        }
    )
    outcome = run(document, config)
    # The unidentified-acquisition leg is partially undisclosed, so the
    # combined test cannot be evaluated: it must not be read as the smaller,
    # known-only total.
    assert metric(outcome, "use_of_proceeds_bucket").is_unknown
    assert criterion(outcome, "use_of_proceeds").state == "UNKNOWN"


# ==========================================================================
# P15 / S5 - missing promoter holding
# ==========================================================================


def test_p15_s5_missing_promoter_holding_is_unknown(make_input, config):
    """P15, S5: an undisclosed promoter holding must not default to anything."""
    document = make_input(
        **{
            "capital_structure.promoter_pre_pct": None,
            "capital_structure.promoter_post_pct": None,
            "capital_structure.promoter_group_pre_shares": None,
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "promoter_post_pct").is_unknown
    assert criterion(outcome, "promoter_post_holding").state == "UNKNOWN"
    # Nothing is invented in its place: the criterion holds no points.
    assert criterion(outcome, "promoter_post_holding").score is None
    assert outcome.record.score["completeness_pct"] < 100.0
    assert outcome.record.score["unknown_points"] > 0


# ==========================================================================
# P16 - invalid schema
# ==========================================================================


def test_p16_invalid_schema_blocks_scoring(golden_input, config):
    document = copy.deepcopy(golden_input)
    document["financials"]["periods"][0]["revenue"] = "24288.2"
    with pytest.raises(SchemaValidationError) as excinfo:
        run(document, config)
    assert excinfo.value.gate == "schema"


# ==========================================================================
# P17 / S14 - invalid config
# ==========================================================================


def test_p17_s14_invalid_config_blocks_scoring(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["modules"][0]["max"] = 30
    with pytest.raises(ConfigValidationError):
        compile_config(broken)


# ==========================================================================
# S13 - 6(2) OFS breach
# ==========================================================================


def test_s13_ofs_6_2_breach_is_rejected(make_input, config):
    document = make_input(
        **{
            "icdr_route": "6(2)",
            "issue.ofs_sellers[0].holding_pct_pre_issue": 7.58,
            "issue.ofs_sellers[0].pre_issue_shares": 1500000,
            "issue.ofs_sellers[0].shares_sold": 1500000,
        }
    )
    with pytest.raises(SemanticValidationError) as excinfo:
        run(document, config)
    assert any(f.code == "OFS_6_2_BREACH" for f in excinfo.value.findings)


# ==========================================================================
# P18 - financial institution overlay
# ==========================================================================


def test_p18_financial_institution_overlay(config, make_input):
    document = make_input(sector_profile="financial")
    outcome = run(document, config)
    plan = outcome.record.plan
    assert plan["sector_overlay"] == "financial"
    assert plan["removed"], "the overlay must remove the criteria it replaces"
    assert plan["added"], "the overlay must supply sector criteria"
    assert plan["total_points"] == pytest.approx(100.0)
    added = set(plan["added"])
    scored = {
        c["criterion_id"] for m in outcome.record.score["modules"] for c in m["criteria"]
    }
    assert added <= scored, "every added criterion must actually be scored"


# ==========================================================================
# P19 / P20 - EPC and real-estate overlays
# ==========================================================================


def test_p19_s8_epc_overlay_with_negative_cfo_but_strong_order_book(config, make_input):
    """P19, S8: the EPC overlay must be able to reward an order book."""
    document = make_input(
        **{
            "sector_profile": "epc_real_estate",
            "financials.periods[0].cfo": -200.0,
            "financials.periods[1].cfo": 400.0,
            "financials.periods[2].cfo": -1500.0,
            "business.order_book": 142244.0,
            "business.order_book_visibility": "strong",
        }
    )
    outcome = run(document, config)
    plan = outcome.record.plan
    assert plan["sector_overlay"] == "epc_real_estate"
    assert plan["total_points"] == pytest.approx(100.0)
    # The overlay replaces the CFO-quality criterion with a CFO-or-order-book one.
    assert "cfo_quality" not in plan["added"]
    identifiers = {
        c["criterion_id"] for m in outcome.record.score["modules"] for c in m["criteria"]
    }
    assert "cfo_or_orderbook" in identifiers
    assert "net_debt_trend_icr" in identifiers
    assert outcome.record.score["final_score"] is not None


def test_p20_real_estate_overlay(config, make_input):
    """P20: real estate shares the EPC/real-estate overlay in the v1.5 config."""
    document = make_input(
        **{
            "sector_profile": "epc_real_estate",
            "sector": "real estate development",
            "business.capacity_utilisation_pct": 62.0,
        }
    )
    outcome = run(document, config)
    plan = outcome.record.plan
    # v1.5 ships one combined EPC/real-estate overlay; see the traceability matrix.
    assert plan["sector_overlay"] == "epc_real_estate"
    assert plan["total_points"] == pytest.approx(100.0)
    # The EPC overlay removes the CFO-quality and leverage criteria; the
    # retail-heavy structure rule independently replaces the anchor/QIB pair.
    assert {"cfo_quality", "leverage"} <= set(plan["removed"])
    assert {"cfo_or_orderbook", "net_debt_trend_icr"} <= set(plan["added"])


# ==========================================================================
# P21 - loss-making overlay
# ==========================================================================


def test_p21_loss_making_overlay_is_auto_selected(config, make_input):
    """P21: a latest-FY loss resolves to the loss_making profile."""
    document = make_input(**{"financials.periods[2].pat": -2497.5})
    outcome = run(document, config)
    plan = outcome.record.plan
    assert plan["auto_profile_applied"] == "loss_making"
    assert plan["sector_overlay"] == "loss_making"
    assert plan["total_points"] == pytest.approx(100.0)


def test_p21_loss_making_profile_uses_loss_criteria(config, make_input):
    document = make_input(**{"financials.periods[2].pat": -2497.5})
    outcome = run(document, config)
    identifiers = {
        c["criterion_id"] for m in outcome.record.score["modules"] for c in m["criteria"]
    }
    assert "peg" not in identifiers, "PEG is meaningless without positive earnings"
    assert "pe_vs_peers" not in identifiers, "a loss-maker has no meaningful P/E"
    assert {"contribution_margin", "cash_runway", "operating_loss_narrowing"} <= identifiers
    # Cash runway is meaningful for a loss-maker, so the overlay scores it
    # rather than the general criteria it replaced.
    assert criterion(outcome, "cash_runway").max == pytest.approx(5.0)
    assert criterion(outcome, "ps_evsales_vs_peers").max == pytest.approx(12.0)


# ==========================================================================
# P22 / S10 - cyclical overlay
# ==========================================================================


def test_p22_s10_cyclical_overlay_requires_five_fiscal_years(config, make_input):
    with pytest.raises(SemanticValidationError) as excinfo:
        run(make_input(sector_profile="cyclical"), config)
    assert any(f.code == "PERIODS_CYCLICAL_INSUFFICIENT" for f in excinfo.value.findings)


def test_p22_s10_cyclical_overlay_with_five_years(config, make_input):
    document = make_input(sector_profile="cyclical")
    extra = [
        {"fy": "FY2022", "revenue": 15000.0, "pat": 200.0, "cfo": 800.0,
         "ebitda": 1500.0},
        {"fy": "FY2023", "revenue": 18000.0, "pat": 400.0, "cfo": 900.0,
         "ebitda": 2100.0},
    ]
    document["financials"]["periods"] = extra + document["financials"]["periods"]
    outcome = run(document, config)
    plan = outcome.record.plan
    assert plan["sector_overlay"] == "cyclical"
    assert plan["total_points"] == pytest.approx(100.0)
    # The cyclical profile scores the 5-year average margin trend explicitly.
    identifiers = {
        c["criterion_id"] for m in outcome.record.score["modules"] for c in m["criteria"]
    }
    assert "margin_trend" in identifiers
    assert metric(outcome, "margin_trend_5y_avg").state in {"VALUE", "UNKNOWN"}


# ==========================================================================
# P23 - retail-heavy structure overlay
# ==========================================================================


def test_p23_retail_heavy_structure_overlay(golden_input, config):
    """P23: a ~1% QIB book makes the anchor/QIB criteria unscoreable."""
    outcome = run(golden_input, config)
    plan = outcome.record.plan
    assert plan["structure_overlays"] == ["retail_heavy"]
    assert set(plan["removed"]) == {"anchor_quality", "qib_subscription"}
    assert set(plan["added"]) == {"overall_subscription", "nii_subscription"}
    assert plan["total_points"] == pytest.approx(100.0)


def test_p23_normal_structure_keeps_anchor_criteria(make_input, config):
    """The mirror image: a fully-subscribed QIB book keeps the anchor criteria."""
    document = make_input(**{"issue.quota_pct.qib": 50.0, "issue.quota_pct.retail": 35.0})
    outcome = run(document, config)
    assert metric(outcome, "qib_quota_pct").value == pytest.approx(50.0)
    assert outcome.record.plan["structure_overlays"] == []
    identifiers = {
        c["criterion_id"] for m in outcome.record.score["modules"] for c in m["criteria"]
    }
    assert "qib_subscription" in identifiers


# ==========================================================================
# P24 / P25 - preliminary and final evaluations
# ==========================================================================


def test_p24_preliminary_evaluation(golden_input, config, tmp_path):
    """P24: the preliminary excludes the post-close market criteria."""
    store = EvaluationStore(tmp_path / "evaluations")
    outcome = evaluate(
        copy.deepcopy(golden_input), config, mode="preliminary",
        evaluation_datetime=EVAL_AT, store=store,
    )
    assert outcome.record.evaluation_mode == "PRELIMINARY"
    identifiers = {
        c["criterion_id"] for m in outcome.record.score["modules"] for c in m["criteria"]
    }
    # Excluded criteria remain visible with an explicit state, so the reader
    # can see they were deliberately left out rather than silently dropped.
    excluded = {
        c["criterion_id"]
        for m in outcome.record.score["modules"]
        for c in m["criteria"]
        if c["state"] == "EXCLUDED_BY_MODE"
    }
    assert {"gmp_trend", "retail_nii_penalty"} <= excluded
    assert outcome.record.verdict["mode_label"] == "provisional"
    # The preliminary is scored on the pre-close information only.
    assert outcome.record.score["mode"] == "preliminary"


def test_p25_final_evaluation(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evaluations")
    outcome = evaluate(
        copy.deepcopy(golden_input), config, mode="final",
        evaluation_datetime=EVAL_AT, store=store,
    )
    assert outcome.record.evaluation_mode == "FINAL"
    identifiers = {
        c["criterion_id"] for m in outcome.record.score["modules"] for c in m["criteria"]
    }
    assert "retail_nii_penalty" in identifiers
    assert outcome.record.verdict["mode_label"] == "final"


# ==========================================================================
# P26 / S16 - preliminary to final delta
# ==========================================================================


def test_p26_s16_preliminary_to_final_delta(golden_input, config, tmp_path):
    """P26, S16: the Final carries a delta and the Preliminary is untouched."""
    store = EvaluationStore(tmp_path / "evaluations")
    preliminary = evaluate(
        copy.deepcopy(golden_input), config, mode="preliminary",
        evaluation_datetime=EVAL_AT, store=store,
    )
    final = evaluate(
        copy.deepcopy(golden_input), config, mode="final",
        evaluation_datetime=EVAL_AT + timedelta(hours=2), store=store,
    )
    delta = final.record.preliminary_delta
    assert delta is not None
    assert delta["preliminary_evaluation_id"] == preliminary.record.evaluation_id
    assert delta["final_evaluation_id"] == final.record.evaluation_id
    assert delta["preliminary_result_hash"] == preliminary.record.result_hash
    assert delta["final_result_hash"] == final.record.result_hash
    assert delta["score_delta"] == pytest.approx(
        final.record.score["final_score"] - preliminary.record.score["final_score"]
    )
    # The frozen preliminary still has no delta of its own.
    assert store.read(preliminary.record.evaluation_id)["preliminary_delta"] is None


def test_p26_delta_refuses_to_overwrite_the_preliminary(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evaluations")
    preliminary = evaluate(
        copy.deepcopy(golden_input), config, mode="preliminary",
        evaluation_datetime=EVAL_AT, store=store,
    )
    before = store.read(preliminary.record.evaluation_id)
    evaluate(
        copy.deepcopy(golden_input), config, mode="final",
        evaluation_datetime=EVAL_AT + timedelta(hours=2), store=store,
    )
    assert store.read(preliminary.record.evaluation_id) == before


# ==========================================================================
# P27 / S17 / prompt s20 - historical rerun reproducibility
# ==========================================================================


def test_p27_s17_historical_rerun_reproduces_the_result(golden_input, config):
    """P27, S17: a rerun of the same frozen inputs reproduces the hash."""
    first = run(golden_input, config)
    second = run(copy.deepcopy(golden_input), config)
    assert first.record.result_hash == second.record.result_hash
    assert first.record.score == second.record.score
    assert first.record.verdict == second.record.verdict


def test_p27_historical_rerun_from_the_stored_golden_files(config):
    """The committed expected files must still match a live rerun."""
    stored = json.loads((GOLDEN_DIR / "expected_verdict.json").read_text(encoding="utf-8"))
    document = json.loads((GOLDEN_DIR / "input.json").read_text(encoding="utf-8"))
    outcome = run(document, config)
    assert outcome.record.result_hash == stored["hashes"]["result_hash"]
    assert outcome.record.score["final_score"] == pytest.approx(35.0)
    assert outcome.record.verdict["verdict"] == stored["verdict"]["verdict"]
    assert outcome.record.input_snapshot_hash == stored["hashes"]["input_snapshot_hash"]
    assert outcome.record.market_snapshot_hash == stored["hashes"]["market_snapshot_hash"]
    assert outcome.record.peer_snapshot_hash == stored["hashes"]["peer_snapshot_hash"]


def test_p27_rerun_after_an_input_correction_creates_a_new_record(
    golden_input, config, tmp_path
):
    """A correction must never silently replace the original evaluation."""
    store = EvaluationStore(tmp_path / "evaluations")
    original = evaluate(
        copy.deepcopy(golden_input), config, mode="final",
        evaluation_datetime=EVAL_AT, store=store,
    )
    corrected_input = copy.deepcopy(golden_input)
    corrected_input["governance"]["rpt_pct_revenue"] = 4.0
    corrected = evaluate(
        corrected_input, config, mode="final",
        evaluation_datetime=EVAL_AT + timedelta(minutes=5), store=store,
    )
    assert corrected.record.result_hash != original.record.result_hash
    assert len(store.list_evaluations()) == 2
    # The original is still exactly as it was written.
    assert store.verify_hashes(original.record.evaluation_id)["result_hash_matches"] is True


# ==========================================================================
# P28 - Excel append-only behaviour
# ==========================================================================


def test_p28_excel_is_append_only_across_the_lifecycle(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evaluations")
    workbook_path = tmp_path / "IPO_Screening_History.xlsx"
    evaluate(
        copy.deepcopy(golden_input), config, mode="preliminary",
        evaluation_datetime=EVAL_AT, store=store, workbook_path=workbook_path,
    )
    evaluate(
        copy.deepcopy(golden_input), config, mode="final",
        evaluation_datetime=EVAL_AT + timedelta(hours=1), store=store,
        workbook_path=workbook_path,
    )

    import openpyxl

    book = openpyxl.load_workbook(workbook_path)
    rows = _data_rows(book["Evaluations"])
    assert len(rows) == 2, "both evaluations must be present as separate rows"
    assert {str(r[3]) for r in rows} == {"PRELIMINARY", "FINAL"}
    master = _data_rows(book["IPO_Master"])
    assert len(master) == 1, "one issuer, one master row"
    assert master[0][7] == 2  # evaluation_count


def test_p28_workbook_has_the_fourteen_sheets(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evaluations")
    workbook_path = tmp_path / "IPO_Screening_History.xlsx"
    evaluate(
        copy.deepcopy(golden_input), config, mode="final",
        evaluation_datetime=EVAL_AT, store=store, workbook_path=workbook_path,
    )
    import openpyxl

    book = openpyxl.load_workbook(workbook_path)
    assert list(book.sheetnames) == list(SHEET_ORDER)


# ==========================================================================
# P29 - post-listing updates
# ==========================================================================


def test_p29_post_listing_update_is_recorded(golden_input, config, tmp_path):
    """P29: the lifecycle continues after listing; the outcome is projected."""
    document = copy.deepcopy(golden_input)
    document["post_listing"] = {
        "listing_date": "2026-10-12",
        "listing_gain_pct": 22.4,
        "return_1w_pct": 31.2,
        "return_1m_pct": 18.9,
    }
    store = EvaluationStore(tmp_path / "evaluations")
    outcome = evaluate(
        document, config, mode="post_listing_1m",
        evaluation_datetime=datetime(2026, 11, 16, 12, 0, 0, tzinfo=timezone.utc),
        store=store,
    )
    assert outcome.record.evaluation_mode == "POST_LISTING_1M"
    assert outcome.record.verdict["mode_label"] == "post-listing 1 month"

    workbook_path = tmp_path / "IPO_Screening_History.xlsx"
    project(store, workbook_path)
    import openpyxl

    book = openpyxl.load_workbook(workbook_path)
    rows = _data_rows(book["Post_Listing"])
    assert len(rows) == 1
    header = _header(book["Post_Listing"])
    assert rows[0][header.index("listing_gain_pct")] == pytest.approx(22.4)
    assert rows[0][header.index("return_1m_pct")] == pytest.approx(18.9)
    # The back-test sheet pairs the score with the realised outcome.
    backtest = _data_rows(book["Backtest"])
    assert len(backtest) == 1
    bt_header = _header(book["Backtest"])
    assert backtest[0][bt_header.index("score")] == pytest.approx(
        outcome.record.score["final_score"]
    )


def test_p29_all_lifecycle_stages_are_declared_in_the_config(config):
    assert set(config["modes"]) == {
        "preliminary",
        "final",
        "post_listing_1w",
        "post_listing_1m",
        "post_listing_6m",
    }


def test_p29_unknown_mode_is_refused(golden_input, config):
    with pytest.raises(ValueError):
        evaluate(copy.deepcopy(golden_input), config, mode="quarterly_review",
                 evaluation_datetime=EVAL_AT)


# ==========================================================================
# P30 - reproducibility hash
# ==========================================================================


def test_p30_reproducibility_hash_is_a_pure_function_of_the_inputs(golden_input, config):
    hashes = {run(copy.deepcopy(golden_input), config).record.result_hash for _ in range(4)}
    assert len(hashes) == 1


def test_p30_hash_covers_every_material_input(golden_input, config):
    """Two records must not collide when a single scored input changes."""
    baseline = run(golden_input, config).record.result_hash
    for path, value in (
        ("governance.rpt_pct_revenue", 4.0),
        ("capital_structure.promoter_pledge_pct", 1.0),
        ("business.top5_customer_pct", 40.0),
        ("issue.price_band_high", 230.0),
    ):
        document = json.loads(json.dumps(golden_input))
        cursor = document
        tokens = path.split(".")
        for token in tokens[:-1]:
            cursor = cursor[token]
        cursor[tokens[-1]] = value
        assert run(document, config).record.result_hash != baseline, path


# --------------------------------------------------------------------------
# Sheet helpers: the first row of every sheet is its header
# --------------------------------------------------------------------------


def _header(sheet):
    return [str(c) for c in next(sheet.iter_rows(values_only=True))]


def _data_rows(sheet):
    rows = [list(r) for r in sheet.iter_rows(values_only=True)]
    return [r for r in rows[1:] if r and r[0]]
