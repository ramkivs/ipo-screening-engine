from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from conftest import criterion, metric, run
from ipo_screening.regulatory_risk_extension import regulatory_risk_metrics, with_regulatory_risk_extension


def _run(document, config):
    with regulatory_risk_metrics():
        return run(document, with_regulatory_risk_extension(config))


def _with_risks(golden_input, **values):
    document=copy.deepcopy(golden_input);document["risks"]={**document.get("risks",{}),**values};return document


@pytest.mark.parametrize(("intensity","penalty"),[(0,0),(10,0),(10.01,-2),(25,-2),(25.01,-5),(50,-5),(100,-5)])
def test_contingent_liability_intensity_boundaries(golden_input,config,intensity,penalty):
    outcome=_run(_with_risks(golden_input,contingent_liabilities_pct_net_worth=intensity),config)
    criteria=[criterion(outcome,"contingent_liabilities_10_to_25_penalty"),criterion(outcome,"contingent_liabilities_above_25_penalty")]
    assert sum(item.score or 0 for item in criteria)==penalty


def test_material_dispute_true_penalizes_and_false_does_not(golden_input,config):
    risky=_run(_with_risks(golden_input,material_regulatory_disputes_present=True),config)
    assert criterion(risky,"material_regulatory_disputes_penalty").score==-3
    clean=_run(_with_risks(golden_input,material_regulatory_disputes_present=False),config)
    assert criterion(clean,"material_regulatory_disputes_penalty").score==0


def test_missing_risk_fields_remain_unknown_without_penalty(golden_input,config):
    document=copy.deepcopy(golden_input);document.pop("risks",None)
    outcome=_run(document,config)
    assert metric(outcome,"contingent_liabilities_10_to_25").is_unknown
    assert metric(outcome,"material_regulatory_disputes_present").is_unknown
    assert criterion(outcome,"material_regulatory_disputes_penalty").effective_score==0


def test_module_e_cap_and_floor_hold(golden_input,config):
    outcome=_run(_with_risks(golden_input,contingent_liabilities_pct_net_worth=100,material_regulatory_disputes_present=True),config)
    module=next(item for item in outcome.score.modules if item.module_id=="E")
    assert 0<=module.score<=module.max


def test_canonical_schema_enforces_nonnegative_number_and_strict_boolean(golden_input):
    schema=json.loads(Path("schema/ipo-input.v1.5.schema.json").read_text())
    validator=Draft202012Validator(schema)
    assert not list(validator.iter_errors(_with_risks(golden_input,contingent_liabilities_pct_net_worth=50.5,material_regulatory_disputes_present=False)))
    assert list(validator.iter_errors(_with_risks(golden_input,contingent_liabilities_pct_net_worth=-0.01)))
    assert list(validator.iter_errors(_with_risks(golden_input,material_regulatory_disputes_present=1)))
