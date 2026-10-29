"""Governed Layer 2C promoter pledge extension for Module D.

Metrics are registered only during a secondary evaluation, preserving the
frozen Layer 1 policy, derived-metric inventory, and historical result hashes.
"""
from __future__ import annotations

import copy
from contextlib import contextmanager
from threading import RLock
from typing import Any, Dict, Iterator, Mapping, Optional

from .canonical import State
from .derived import MetricValue, REGISTRY

GOVERNANCE_EXTENSION_TARGETS = frozenset({
    "governance.promoter_pledged_shares_pct",
    "governance.pre_issue_promoter_holding_pct",
})

GOVERNANCE_EXTENSION_CRITERIA = (
    {"id":"promoter_pledge_upto_25_penalty","label":"Promoter pledged shares above 0% and up to 25%","max":0,"min":-2,"kind":"penalty","when":{"flag":"promoter_pledge_upto_25"},"points":-2},
    {"id":"promoter_pledge_25_to_50_penalty","label":"Promoter pledged shares above 25% and up to 50%","max":0,"min":-4,"kind":"penalty","when":{"flag":"promoter_pledge_25_to_50"},"points":-4},
    {"id":"promoter_pledge_above_50_penalty","label":"Promoter pledged shares above 50%","max":0,"min":-7,"kind":"penalty","when":{"flag":"promoter_pledge_above_50"},"points":-7},
    {"id":"low_pre_issue_promoter_holding_penalty","label":"Pre-issue promoter holding below 20%","max":0,"min":-2,"kind":"penalty","when":{"flag":"low_pre_issue_promoter_holding"},"points":-2},
)

_LOCK = RLock()
_VALUE, _UNKNOWN = State.VALUE.value, State.UNKNOWN.value


def _metric(metric_id: str, state: str, value: Any = None, reason: str = "") -> MetricValue:
    return MetricValue(metric_id, state, value=value, kind="boolean", reason=reason)


def _number(ctx: Any, field: str) -> Optional[float]:
    value = ctx.canonical.governance().get(field)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _pledge_band(metric_id: str, lower: float, upper: Optional[float]):
    def calculate(ctx: Any) -> MetricValue:
        value = _number(ctx, "promoter_pledged_shares_pct")
        if value is None:
            return _metric(metric_id, _UNKNOWN, reason="promoter pledged shares percentage is not supplied")
        hit = value > lower and (upper is None or value <= upper)
        return _metric(metric_id, _VALUE, hit)
    return calculate


def _low_holding(ctx: Any) -> MetricValue:
    metric_id = "low_pre_issue_promoter_holding"
    value = _number(ctx, "pre_issue_promoter_holding_pct")
    if value is None:
        return _metric(metric_id, _UNKNOWN, reason="pre-issue promoter holding is not supplied")
    exempt = ctx.canonical.governance().get("professionally_managed_without_identifiable_promoters") is True
    return _metric(metric_id, _VALUE, value < 20 and not exempt)


_METRICS = {
    "promoter_pledge_upto_25": _pledge_band("promoter_pledge_upto_25", 0, 25),
    "promoter_pledge_25_to_50": _pledge_band("promoter_pledge_25_to_50", 25, 50),
    "promoter_pledge_above_50": _pledge_band("promoter_pledge_above_50", 50, None),
    "low_pre_issue_promoter_holding": _low_holding,
}


def with_governance_extension(config: Mapping[str, Any]) -> Dict[str, Any]:
    extended = copy.deepcopy(dict(config))
    module = next(item for item in extended["modules"] if item["id"] == "D")
    existing = {item["id"] for item in module["criteria"]}
    module["criteria"].extend(copy.deepcopy(item) for item in GOVERNANCE_EXTENSION_CRITERIA if item["id"] not in existing)
    return extended


@contextmanager
def governance_extension_metrics() -> Iterator[None]:
    with _LOCK:
        prior = {name: REGISTRY.get(name) for name in _METRICS}
        REGISTRY.update(_METRICS)
        try:
            yield
        finally:
            for name, value in prior.items():
                if value is None:
                    REGISTRY.pop(name, None)
                else:
                    REGISTRY[name] = value


__all__ = ["GOVERNANCE_EXTENSION_TARGETS", "with_governance_extension", "governance_extension_metrics"]
