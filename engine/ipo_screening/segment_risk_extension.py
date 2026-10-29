"""Layer 2C segment concentration and operating-risk extension for Module A.

The active Layer 1 policy and frozen scoring core remain untouched. Metrics are
registered only while evaluating a secondary payload that contains one of the
governed segment-risk fields.
"""
from __future__ import annotations

import copy
from contextlib import contextmanager
from threading import RLock
from typing import Any, Dict, Iterator, Mapping, Optional

from .canonical import State
from .derived import MetricValue, REGISTRY

SEGMENT_RISK_TARGETS = frozenset({
    "financials.top_customer_revenue_pct",
    "financials.loss_making_segments_present",
})

SEGMENT_RISK_CRITERIA = (
    {"id":"top_customer_25_to_50_penalty","label":"Largest customer contributes above 25% and up to 50% of revenue","max":0,"min":-2,"kind":"penalty","when":{"flag":"top_customer_concentration_25_to_50"},"points":-2},
    {"id":"top_customer_above_50_penalty","label":"Largest customer contributes above 50% of revenue","max":0,"min":-4,"kind":"penalty","when":{"flag":"top_customer_concentration_above_50"},"points":-4},
    {"id":"loss_making_segments_penalty","label":"Material loss-making operating segments are disclosed","max":0,"min":-2,"kind":"penalty","when":{"flag":"loss_making_segments_present"},"points":-2},
)

_LOCK = RLock()
_VALUE, _UNKNOWN = State.VALUE.value, State.UNKNOWN.value


def _metric(metric_id: str, state: str, value: Any = None, reason: str = "") -> MetricValue:
    return MetricValue(metric_id, state, value=value, kind="boolean", reason=reason)


def _concentration(ctx: Any) -> Optional[float]:
    value = ctx.canonical.financials().get("top_customer_revenue_pct")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _concentration_band(metric_id: str, lower: float, upper: Optional[float]):
    def calculate(ctx: Any) -> MetricValue:
        value = _concentration(ctx)
        if value is None:
            return _metric(metric_id, _UNKNOWN, reason="top-customer revenue concentration is not supplied")
        return _metric(metric_id, _VALUE, value > lower and (upper is None or value <= upper))
    return calculate


def _loss_segments(ctx: Any) -> MetricValue:
    metric_id = "loss_making_segments_present"
    value = ctx.canonical.financials().get(metric_id)
    if not isinstance(value, bool):
        return _metric(metric_id, _UNKNOWN, reason="loss-making segment disclosure is not supplied")
    return _metric(metric_id, _VALUE, value)


_METRICS = {
    "top_customer_concentration_25_to_50": _concentration_band("top_customer_concentration_25_to_50", 25, 50),
    "top_customer_concentration_above_50": _concentration_band("top_customer_concentration_above_50", 50, None),
    "loss_making_segments_present": _loss_segments,
}


def with_segment_risk_extension(config: Mapping[str, Any]) -> Dict[str, Any]:
    extended = copy.deepcopy(dict(config))
    module = next(item for item in extended["modules"] if item["id"] == "A")
    existing = {item["id"] for item in module["criteria"]}
    module["criteria"].extend(copy.deepcopy(item) for item in SEGMENT_RISK_CRITERIA if item["id"] not in existing)
    return extended


@contextmanager
def segment_risk_metrics() -> Iterator[None]:
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


__all__ = ["SEGMENT_RISK_TARGETS", "with_segment_risk_extension", "segment_risk_metrics"]
