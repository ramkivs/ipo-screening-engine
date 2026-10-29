"""Layer 2C contingent-liability and regulatory-dispute extension for Module E."""
from __future__ import annotations

import copy
from contextlib import contextmanager
from threading import RLock
from typing import Any, Dict, Iterator, Mapping, Optional

from .canonical import State
from .derived import MetricValue, REGISTRY

REGULATORY_RISK_TARGETS = frozenset({
    "risks.contingent_liabilities_pct_net_worth",
    "risks.material_regulatory_disputes_present",
})

REGULATORY_RISK_CRITERIA = (
    {"id":"contingent_liabilities_10_to_25_penalty","label":"Contingent liabilities exceed 10% and are at most 25% of net worth","max":0,"min":-2,"kind":"penalty","when":{"flag":"contingent_liabilities_10_to_25"},"points":-2},
    {"id":"contingent_liabilities_above_25_penalty","label":"Contingent liabilities exceed 25% of net worth","max":0,"min":-5,"kind":"penalty","when":{"flag":"contingent_liabilities_above_25"},"points":-5},
    {"id":"material_regulatory_disputes_penalty","label":"Material regulatory or tax disputes are disclosed","max":0,"min":-3,"kind":"penalty","when":{"flag":"material_regulatory_disputes_present"},"points":-3},
)

_LOCK = RLock()
_VALUE, _UNKNOWN = State.VALUE.value, State.UNKNOWN.value

def _metric(metric_id: str, state: str, value: Any = None, reason: str = "") -> MetricValue:
    return MetricValue(metric_id, state, value=value, kind="boolean", reason=reason)

def _risks(ctx: Any) -> Mapping[str, Any]:
    return ctx.canonical.raw.get("risks", {}) or {}

def _intensity(ctx: Any) -> Optional[float]:
    value = _risks(ctx).get("contingent_liabilities_pct_net_worth")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None

def _intensity_band(metric_id: str, lower: float, upper: Optional[float]):
    def calculate(ctx: Any) -> MetricValue:
        value = _intensity(ctx)
        if value is None:
            return _metric(metric_id, _UNKNOWN, reason="contingent-liability intensity is not supplied")
        return _metric(metric_id, _VALUE, value > lower and (upper is None or value <= upper))
    return calculate

def _disputes(ctx: Any) -> MetricValue:
    metric_id = "material_regulatory_disputes_present"
    value = _risks(ctx).get(metric_id)
    if not isinstance(value, bool):
        return _metric(metric_id, _UNKNOWN, reason="material regulatory-dispute disclosure is not supplied")
    return _metric(metric_id, _VALUE, value)

_METRICS = {
    "contingent_liabilities_10_to_25": _intensity_band("contingent_liabilities_10_to_25", 10, 25),
    "contingent_liabilities_above_25": _intensity_band("contingent_liabilities_above_25", 25, None),
    "material_regulatory_disputes_present": _disputes,
}

def with_regulatory_risk_extension(config: Mapping[str, Any]) -> Dict[str, Any]:
    extended = copy.deepcopy(dict(config))
    module = next(item for item in extended["modules"] if item["id"] == "E")
    existing = {item["id"] for item in module["criteria"]}
    module["criteria"].extend(copy.deepcopy(item) for item in REGULATORY_RISK_CRITERIA if item["id"] not in existing)
    return extended

@contextmanager
def regulatory_risk_metrics() -> Iterator[None]:
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

__all__ = ["REGULATORY_RISK_TARGETS", "with_regulatory_risk_extension", "regulatory_risk_metrics"]
