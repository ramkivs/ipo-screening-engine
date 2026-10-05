"""Validation as a hard gate: schema, semantic, configuration.

Spec v1.5 s20 and s3.5, execution prompt s6 and s18.9-s18.10.

These tests assert *fail-closed* behaviour: an invalid input or configuration
must stop scoring and name the defect, rather than degrade quietly.
"""

from __future__ import annotations

import copy
import json

import pytest

from conftest import CONFIG_PATH, EVAL_AT, metric, run
from ipo_screening.config_validation import check_config, compile_config
from ipo_screening.errors import (
    ConfigValidationError,
    SchemaValidationError,
    SemanticValidationError,
)
from ipo_screening.pipeline import evaluate
from ipo_screening.schema_validation import enforce_schema, validate_schema


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------


def test_reference_style_check_is_no_longer_sufficient(golden_input, schema):
    """The reference prototype only asserted four keys existed."""
    document = copy.deepcopy(golden_input)
    document["issue"]["fresh_shares"] = "6590909"  # numeric string
    findings = validate_schema(document, schema)
    assert findings, "a numeric string must not satisfy a number field"
    assert all(f.severity == "ERROR" for f in findings)


def test_schema_rejects_a_missing_required_section(golden_input, schema):
    document = copy.deepcopy(golden_input)
    del document["governance"]
    findings = validate_schema(document, schema)
    assert any("governance" in (f.message or "") for f in findings)


def test_schema_rejects_an_invalid_enum(golden_input, schema):
    document = copy.deepcopy(golden_input)
    document["governance"]["auditor_opinion"] = "mostly_fine"
    findings = validate_schema(document, schema)
    assert findings


def test_schema_rejects_a_malformed_date(golden_input, schema):
    document = copy.deepcopy(golden_input)
    document["issue"]["open_date"] = "30-09-2026"
    findings = validate_schema(document, schema)
    assert findings


def test_schema_rejects_an_unknown_reporting_unit(golden_input, schema):
    document = copy.deepcopy(golden_input)
    document["financials"]["reporting_unit"] = "INR_BILLIONZ"
    findings = validate_schema(document, schema)
    assert findings


def test_schema_gate_stops_scoring(golden_input, config):
    document = copy.deepcopy(golden_input)
    document["issue"]["fresh_shares"] = "not-a-number"
    with pytest.raises(SchemaValidationError) as excinfo:
        evaluate(document, config, evaluation_datetime=EVAL_AT)
    assert excinfo.value.findings
    assert excinfo.value.gate == "schema"


def test_valid_input_passes_the_schema_gate(golden_input, schema):
    assert validate_schema(golden_input, schema) == []


# --------------------------------------------------------------------------
# Semantic
# --------------------------------------------------------------------------


def test_seller_cannot_offer_more_than_it_held(config, make_input):
    document = make_input(**{"issue.ofs_sellers[0].shares_sold": 2000000})
    with pytest.raises(SemanticValidationError) as excinfo:
        run(document, config)
    assert any(f.code == "SELLER_OVERSELL" for f in excinfo.value.findings)


def test_fewer_than_three_full_fiscal_years_is_rejected(config, make_input):
    document = make_input(**{"financials.periods": [{"fy": "FY2026", "revenue": 1.0, "pat": 1.0}]})
    with pytest.raises((SemanticValidationError, SchemaValidationError)):
        run(document, config)


def test_cyclical_profile_requires_five_fiscal_years(config, make_input):
    document = make_input(**{"sector_profile": "cyclical"})
    with pytest.raises(SemanticValidationError) as excinfo:
        run(document, config)
    assert any(f.code == "PERIODS_CYCLICAL_INSUFFICIENT" for f in excinfo.value.findings)


def test_gcp_ceiling_recorded_as_an_amount_is_rejected(config, make_input):
    """v1.5 s10/s13: 25% of the fresh issue must not appear as the GCP amount.

    This is the reference prototype's defect: it wrote the ICDR legal ceiling
    (36.25 crore == 25% of a 145 crore fresh issue) into the GCP amount slot.
    The check is deliberately strict and fires whether or not a marker is
    supplied, because the ceiling must never be *stored* as an amount.
    """
    document = make_input(**{"use_of_proceeds[2].amount": 3625.0})
    with pytest.raises(SemanticValidationError) as excinfo:
        run(document, config)
    findings = [f for f in excinfo.value.findings if f.code == "GCP_CEILING_RECORDED_AS_AMOUNT"]
    assert findings
    # The finding reports the normalised amount in crore and the ceiling beside it.
    assert findings[0].detail["amount"] == pytest.approx(36.25)
    assert findings[0].detail["ceiling"] == pytest.approx(36.25)


def test_gcp_ceiling_check_is_unit_aware(config, make_input):
    """A ceiling-sized value in the reporting unit must not slip through.

    ``amount_unit: lakhs`` with a fresh issue of 14,500 lakh (145 crore) means
    the ceiling is 3,625 lakh. The comparable reference defect therefore stays
    detectable after normalisation.
    """
    document = make_input(
        **{
            "financials.reporting_unit": "INR_LAKHS",
            "issue.fresh_issue": 14500.0,
            "use_of_proceeds[2].amount": 3625.0,
        }
    )
    with pytest.raises(SemanticValidationError) as excinfo:
        run(document, config)
    assert any(f.code == "GCP_CEILING_RECORDED_AS_AMOUNT" for f in excinfo.value.findings)


def test_gcp_above_the_legal_ceiling_is_rejected(config, make_input):
    document = make_input(**{"use_of_proceeds[2].amount": 5000.0})
    with pytest.raises(SemanticValidationError) as excinfo:
        run(document, config)
    assert any(f.code == "PROCEEDS_GCP_LIMIT" for f in excinfo.value.findings)


def test_undisclosed_gcp_warns_and_does_not_block(config, make_input):
    """The golden fixture discloses [●]; that is a warning, not an error."""
    outcome = run(make_input(), config)
    codes = {w.code for w in outcome.validation.warnings}
    assert "GCP_UNDISCLOSED" in codes


def test_ofs_6_2_selling_limit_breach_is_rejected(config, make_input):
    """Spec s26.13: a 6(2) route holder selling more than its cap is a breach."""
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


def test_ofs_6_2_limit_is_not_applied_on_the_6_1_route(config, make_input):
    """The same seller on the 6(1) route is not a breach."""
    document = make_input(
        **{
            "icdr_route": "6(1)",
            "issue.ofs_sellers[0].holding_pct_pre_issue": 7.58,
        }
    )
    outcome = run(document, config)
    assert not any(f.code == "OFS_6_2_BREACH" for f in outcome.validation.findings)


def test_cross_source_divergence_is_reported_not_resolved(config, make_input):
    """Spec s20 'Cross-source': differences are reported, not silently fixed."""
    document = make_input(**{"_cross_checks": [{"field": "FY2026 revenue", "primary": 33867.73, "secondary": 31000.0}]})
    outcome = run(document, config)
    codes = {w.code for w in outcome.validation.warnings}
    assert "CROSS_SOURCE_DIVERGENCE" in codes


def test_cross_source_within_tolerance_is_quiet(config, make_input):
    document = make_input(**{"_cross_checks": [{"field": "FY2026 revenue", "primary": 33867.73, "secondary": 33900.0}]})
    outcome = run(document, config)
    codes = {w.code for w in outcome.validation.warnings}
    assert "CROSS_SOURCE_DIVERGENCE" not in codes


def test_percentage_out_of_range_is_rejected(config, make_input):
    document = make_input(**{"governance.rpt_pct_revenue": 99999.0})
    with pytest.raises((SemanticValidationError, SchemaValidationError)):
        run(document, config)


def test_unknown_unit_raises(config, make_input):
    from ipo_screening.canonical import UnitError

    document = make_input()
    document["financials"]["reporting_unit"] = "INR_CRORES"
    document["financials"]["periods"][0]["revenue"] = 24288.2
    # A well-formed document normalises fine; an unknown unit must raise.
    from ipo_screening.canonical_input import build_canonical_input

    document["financials"]["reporting_unit"] = "NOT_A_UNIT"
    with pytest.raises(UnitError):
        build_canonical_input(document)


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------


def _base_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_config_compiles(raw_config):
    compiled = compile_config(raw_config)
    assert compiled["_fingerprint"]
    assert compiled["_validation"]["ok"] is True


def test_module_max_mismatch_is_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["modules"][0]["max"] = 30
    check = check_config(broken)
    assert not check.ok
    assert any(f.code in {"CONFIG_MODULE_MAX_MISMATCH", "CONFIG_TOTAL_MISMATCH"} for f in check.errors)


def test_total_not_100_is_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["modules"][0]["criteria"][0]["max"] = 1
    broken["modules"][1]["criteria"][0]["max"] = 3
    check = check_config(broken)
    assert not check.ok


def test_unimplemented_metric_is_rejected(raw_config):
    """v1.5 s14: an overlay needing an unimplemented metric must fail."""
    broken = copy.deepcopy(raw_config)
    broken["modules"][2]["criteria"][0]["metric"] = "metric_that_does_not_exist"
    check = check_config(broken)
    assert any(f.code == "CONFIG_METRIC_UNIMPLEMENTED" for f in check.errors)


def test_overlay_metric_not_implemented_is_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["sector_overlays"]["financial"]["add"][0]["metric"] = "nim_metric_not_built"
    check = check_config(broken)
    assert any(f.code == "CONFIG_METRIC_UNIMPLEMENTED" for f in check.errors)
    assert any(
        (f.location or "").startswith("sector_overlays.financial") for f in check.errors
    )


def test_overlay_that_does_not_reconcile_is_rejected(raw_config):
    """Spec s20: 'overlay replacements reconcile'."""
    broken = copy.deepcopy(raw_config)
    # Remove 5 points and add back only 4.
    for criterion in broken["sector_overlays"]["epc_real_estate"]["add"]:
        if criterion["id"] == "cfo_or_orderbook":
            criterion["max"] = 4
    check = check_config(broken)
    assert any(f.code == "CONFIG_OVERLAY_RECONCILE" for f in check.errors)


def test_invalid_operator_is_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["modules"][0]["criteria"][0]["rule"]["bands"][0][0] = "=>"
    check = check_config(broken)
    assert any(f.code == "CONFIG_OPERATOR_INVALID" for f in check.errors)


def test_incomplete_categorical_map_is_rejected(raw_config):
    """A bucket with no mapping would be silently dropped."""
    broken = copy.deepcopy(raw_config)
    del broken["modules"][0]["criteria"][1]["rule"]["map"]["volatile"]
    check = check_config(broken)
    assert any(f.code == "CONFIG_CATEGORICAL_INCOMPLETE" for f in check.errors)


def test_typo_in_a_knockout_flag_is_rejected(raw_config):
    """A misspelled flag would leave the knockout permanently UNVERIFIED."""
    broken = copy.deepcopy(raw_config)
    broken["knockouts"][0]["when"]["any"][1]["flag"] = "going_conern_uncertainty"
    check = check_config(broken)
    assert any(f.code == "CONFIG_FLAG_UNIMPLEMENTED" for f in check.errors)


def test_knockout_flag_must_reference_an_implemented_metric(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["knockouts"][2]["when"]["all"][1]["flag"] = "no_such_flag"
    check = check_config(broken)
    findings = [f for f in check.errors if f.code == "CONFIG_FLAG_UNIMPLEMENTED"]
    assert findings
    assert findings[0].detail["flag"] == "no_such_flag"


def test_negation_node_is_supported_and_validated(raw_config):
    ok = copy.deepcopy(raw_config)
    ok["knockouts"][2]["when"]["all"][1] = {
        "not": {"metric": "profit_declining", "op": "==", "value": True}
    }
    assert check_config(ok).ok

    broken = copy.deepcopy(raw_config)
    broken["knockouts"][2]["when"]["all"][1] = {
        "not": {"metric": "profit_declining", "op": "xor", "value": True}
    }
    assert any(f.code == "CONFIG_OPERATOR_INVALID" for f in check_config(broken).errors)


def test_negation_of_a_non_object_is_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["knockouts"][2]["when"]["all"][1] = {"not": ["profit_declining"]}
    assert any(f.code == "CONFIG_EXPR_NOT_TYPE" for f in check_config(broken).errors)


def test_unrecognised_expression_node_is_rejected(raw_config):
    """Spec s14: an unparseable expression node must fail, never degrade."""
    broken = copy.deepcopy(raw_config)
    broken["knockouts"][0]["when"]["any"][0] = {"fact": "auditor_is_qualified"}
    assert any(f.code == "CONFIG_EXPR_UNKNOWN" for f in check_config(broken).errors)


def test_duplicate_criterion_across_modules_is_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["modules"][1]["criteria"].append(copy.deepcopy(broken["modules"][0]["criteria"][0]))
    check = check_config(broken)
    assert any(f.code == "CONFIG_DUPLICATE_CRITERION" for f in check.errors)


def test_score_exceeding_max_is_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["modules"][0]["criteria"][0]["rule"]["bands"][0][2] = 99
    check = check_config(broken)
    assert any(f.code == "CONFIG_SCORE_EXCEEDS_MAX" for f in check.errors)


def test_count_weighted_confidence_config_is_rejected(raw_config):
    """v1.5 s11 forbids count-weighted confidence."""
    broken = copy.deepcopy(raw_config)
    broken["confidence"]["weighting"] = "COUNT"
    check = check_config(broken)
    assert any(f.code == "CONFIG_CONFIDENCE_WEIGHTING" for f in check.errors)


def test_unordered_verdict_bands_are_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["verdict"]["bands"] = list(reversed(broken["verdict"]["bands"]))
    check = check_config(broken)
    assert any(f.code == "CONFIG_VERDICT_BANDS_UNORDERED" for f in check.errors)


def test_invalid_config_blocks_scoring(golden_input, raw_config):
    """Spec s3.5: the engine must refuse to score with an invalid configuration."""
    broken = copy.deepcopy(raw_config)
    broken["modules"][0]["max"] = 26
    with pytest.raises(ConfigValidationError):
        compile_config(broken)


def test_declared_but_unimplemented_metric_is_rejected(raw_config):
    broken = copy.deepcopy(raw_config)
    broken["derived_metrics"]["a_metric_i_never_wrote"] = {"implemented": True}
    check = check_config(broken)
    assert any(f.code == "CONFIG_METRIC_DECLARED_NOT_IMPLEMENTED" for f in check.errors)


def test_every_profile_and_structure_combination_reconciles(raw_config):
    """All 5 profiles x structure combinations must total 100."""
    check = check_config(raw_config)
    assert check.ok
    assert len(check.profile_plans) == 10
    for name, plan in check.profile_plans.items():
        assert plan["total"] == pytest.approx(100.0), name
