from __future__ import annotations

import copy
import pytest

from conftest import criterion, metric, run
from ipo_screening.governance_extension import governance_extension_metrics, with_governance_extension


def _run(document, config):
    with governance_extension_metrics():
        return run(document, with_governance_extension(config))


def _with_governance(golden_input, **values):
    document=copy.deepcopy(golden_input);document["governance"].update(values);return document


@pytest.mark.parametrize(("pledged","criterion_id","penalty"),[
    (0,None,0),(25,"promoter_pledge_upto_25_penalty",-2),(25.01,"promoter_pledge_25_to_50_penalty",-4),
    (50,"promoter_pledge_25_to_50_penalty",-4),(50.01,"promoter_pledge_above_50_penalty",-7),(100,"promoter_pledge_above_50_penalty",-7),
])
def test_promoter_pledge_threshold_boundaries(golden_input,config,pledged,criterion_id,penalty):
    outcome=_run(_with_governance(golden_input,promoter_pledged_shares_pct=pledged),config)
    criteria=[item for module in outcome.score.modules for item in module.criteria if item.criterion_id.startswith("promoter_pledge_")]
    assert sum(item.score or 0 for item in criteria)==penalty
    if criterion_id: assert criterion(outcome,criterion_id).score==penalty


def test_missing_pre_issue_holding_remains_unknown(golden_input,config):
    document=copy.deepcopy(golden_input);document["governance"].pop("pre_issue_promoter_holding_pct",None)
    outcome=_run(document,config)
    assert metric(outcome,"low_pre_issue_promoter_holding").is_unknown
    assert criterion(outcome,"low_pre_issue_promoter_holding_penalty").state=="UNKNOWN"


def test_low_holding_penalty_and_professionally_managed_exemption(golden_input,config):
    low=_run(_with_governance(golden_input,pre_issue_promoter_holding_pct=19.99),config)
    assert criterion(low,"low_pre_issue_promoter_holding_penalty").score==-2
    exempt=_run(_with_governance(golden_input,pre_issue_promoter_holding_pct=10,professionally_managed_without_identifiable_promoters=True),config)
    assert criterion(exempt,"low_pre_issue_promoter_holding_penalty").score==0


def test_module_d_cap_and_floor_hold_under_severe_penalties(golden_input,config):
    outcome=_run(_with_governance(golden_input,promoter_pledged_shares_pct=100,pre_issue_promoter_holding_pct=10),config)
    module_d=next(module for module in outcome.score.modules if module.module_id=="D")
    assert 0<=module_d.score<=module_d.max
