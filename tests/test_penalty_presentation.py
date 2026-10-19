"""Penalty state/reason presentation: zero-applied is not always "cleared".

The persisted evaluation already distinguishes a ``SCORED`` zero
("not triggered") from an ``UNKNOWN`` zero ("carried in the lower bound").
The presentation layer dropped that distinction (it carried ``state`` but
not ``reason`` and rendered neither), so an unevaluated penalty could be
read as a cleared one.  These tests pin the projection and the API-level
contract; they do not change any scoring rule or stored record.
"""

from __future__ import annotations

from conftest import EVAL_AT, REPO_ROOT
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.pipeline import evaluate
from ipo_screening.presentation.service import PresentationConfig, PresentationService


def _service(tmp_path):
    return PresentationService(
        PresentationConfig(
            store_root=tmp_path / "evaluations",
            config_dir=REPO_ROOT / "config",
            issue_terms_resolver=IssueTermsResolver(providers=[]),
        )
    )


def _evaluate(service, document, config):
    outcome = evaluate(
        document,
        config,
        store=service.eval_store,
        evaluation_datetime=EVAL_AT,
    )
    detail = service.get_evaluation_detail(outcome.record.evaluation_id)
    assert detail is not None
    return detail


def test_unknown_penalty_is_presented_as_carried_not_cleared(tmp_path, config, golden_input):
    service = _service(tmp_path)
    detail = _evaluate(service, golden_input, config)
    items = {p.id: p for p in detail.penalties}

    auditor = items["auditor_cfo_exit"]
    assert auditor.state == "UNKNOWN"
    assert auditor.points == 0.0
    assert auditor.reason and "carried in the lower bound" in auditor.reason

    margin = items["margin_spike"]
    assert margin.state == "SCORED"
    assert margin.points == -3.0
    assert margin.reason == "triggered"


def test_not_triggered_penalty_is_presented_as_scored_zero(tmp_path, config, make_input):
    service = _service(tmp_path)
    detail = _evaluate(
        service,
        make_input(**{"governance.auditor_or_cfo_exit_2y": False}),
        config,
    )
    auditor = {p.id: p for p in detail.penalties}["auditor_cfo_exit"]
    assert auditor.state == "SCORED"
    assert auditor.points == 0.0
    assert auditor.reason == "not triggered"


def test_triggered_penalty_is_presented_with_its_own_points(tmp_path, config, make_input):
    service = _service(tmp_path)
    detail = _evaluate(
        service,
        make_input(**{"governance.auditor_or_cfo_exit_2y": True}),
        config,
    )
    items = {p.id: p for p in detail.penalties}
    assert items["auditor_cfo_exit"].state == "SCORED"
    assert items["auditor_cfo_exit"].points == -3.0
    assert items["auditor_cfo_exit"].reason == "triggered"
    assert items["receivable_days_up"].points == 0.0
    assert items["receivable_days_up"].reason == "not triggered"
