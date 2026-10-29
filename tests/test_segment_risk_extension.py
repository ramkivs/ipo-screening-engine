from __future__ import annotations

import copy
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from conftest import criterion, metric, run
from ipo_screening.segment_risk_extension import segment_risk_metrics, with_segment_risk_extension


def _run(document, config):
    with segment_risk_metrics():
        return run(document, with_segment_risk_extension(config))


def _with_financials(golden_input, **values):
    document=copy.deepcopy(golden_input);document["financials"].update(values);return document


@pytest.mark.parametrize(("concentration","penalty"),[(0,0),(20,0),(25,0),(25.01,-2),(50,-2),(50.01,-4),(55,-4),(100,-4)])
def test_top_customer_concentration_boundaries(golden_input,config,concentration,penalty):
    outcome=_run(_with_financials(golden_input,top_customer_revenue_pct=concentration),config)
    criteria=[criterion(outcome,"top_customer_25_to_50_penalty"),criterion(outcome,"top_customer_above_50_penalty")]
    assert sum(item.score or 0 for item in criteria)==penalty


def test_loss_making_segment_true_penalizes_and_false_does_not(golden_input,config):
    risky=_run(_with_financials(golden_input,loss_making_segments_present=True),config)
    assert criterion(risky,"loss_making_segments_penalty").score==-2
    clean=_run(_with_financials(golden_input,loss_making_segments_present=False),config)
    assert criterion(clean,"loss_making_segments_penalty").score==0


def test_missing_segment_fields_remain_unknown_without_penalty(golden_input,config):
    document=copy.deepcopy(golden_input)
    document["financials"].pop("top_customer_revenue_pct",None)
    document["financials"].pop("loss_making_segments_present",None)
    outcome=_run(document,config)
    assert metric(outcome,"top_customer_concentration_25_to_50").is_unknown
    assert metric(outcome,"loss_making_segments_present").is_unknown
    assert criterion(outcome,"loss_making_segments_penalty").effective_score==0


def test_module_a_cap_and_floor_hold_for_combined_segment_risk(golden_input,config):
    outcome=_run(_with_financials(golden_input,top_customer_revenue_pct=100,loss_making_segments_present=True),config)
    module_a=next(module for module in outcome.score.modules if module.module_id=="A")
    assert 0<=module_a.score<=module_a.max


def test_canonical_schema_enforces_percentage_range_and_strict_boolean(golden_input):
    schema=json.loads(Path("schema/ipo-input.v1.5.schema.json").read_text())
    validator=Draft202012Validator(schema)
    assert not list(validator.iter_errors(_with_financials(golden_input,top_customer_revenue_pct=55,loss_making_segments_present=False)))
    assert list(validator.iter_errors(_with_financials(golden_input,top_customer_revenue_pct=101)))
    assert list(validator.iter_errors(_with_financials(golden_input,loss_making_segments_present=1)))
