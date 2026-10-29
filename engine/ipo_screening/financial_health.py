"""Governed Layer 2C financial-health scoring extension for Module A.

The active Layer 1 v1.5 policy and frozen scoring core remain byte-identical.
These metrics and penalty criteria are installed only while evaluating an
accepted secondary payload carrying explicit financial-health fields.
"""
from __future__ import annotations

import copy
from contextlib import contextmanager
from decimal import Decimal
from threading import RLock
from typing import Any, Dict, Iterator, Mapping, Optional

from .canonical import State
from .derived import MetricValue, REGISTRY

FINANCIAL_HEALTH_TARGETS = frozenset({
    "financials.operating_cash_flow_3yr_cumulative",
    "financials.net_income_3yr_cumulative",
    "financials.trade_receivables_days",
    "financials.net_working_capital_pct_revenue",
})

FINANCIAL_HEALTH_CRITERIA = (
    {"id":"cash_flow_quality_penalty","label":"Paper-profit risk: cumulative OCF below 50% of cumulative net income","max":0,"min":-5,"kind":"penalty","when":{"flag":"cash_flow_quality_below_50pct"},"points":-5},
    {"id":"dso_over_60_penalty","label":"DSO above 60 days","max":0,"min":-1,"kind":"penalty","when":{"flag":"dso_above_60"},"points":-1},
    {"id":"dso_over_90_penalty","label":"Additional DSO penalty above 90 days","max":0,"min":-1,"kind":"penalty","when":{"flag":"dso_above_90"},"points":-1},
    {"id":"dso_over_120_or_spike_penalty","label":"Additional DSO penalty above 120 days or a >25% annual spike","max":0,"min":-1,"kind":"penalty","when":{"flag":"dso_above_120_or_spike"},"points":-1},
    {"id":"working_capital_over_20_penalty","label":"Net working capital above 20% of revenue","max":0,"min":-1,"kind":"penalty","when":{"flag":"working_capital_above_20"},"points":-1},
    {"id":"working_capital_over_35_penalty","label":"Additional net working capital penalty above 35% of revenue","max":0,"min":-1,"kind":"penalty","when":{"flag":"working_capital_above_35"},"points":-1},
    {"id":"working_capital_over_50_penalty","label":"Additional net working capital penalty above 50% of revenue","max":0,"min":-1,"kind":"penalty","when":{"flag":"working_capital_above_50"},"points":-1},
)

_LOCK = RLock()
_VALUE, _UNKNOWN, _NA = State.VALUE.value, State.UNKNOWN.value, State.NOT_APPLICABLE.value


def _metric(metric_id: str, state: str, value: Any = None, reason: str = "") -> MetricValue:
    return MetricValue(metric_id, state, value=value, kind="boolean", reason=reason)


def _sum_override(ctx: Any, name: str) -> Optional[float]:
    raw = ctx.canonical.financials().get(name)
    if raw is None: return None
    values = raw if isinstance(raw, list) else [raw]
    if not values or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in values): return None
    return float(sum(Decimal(str(v)) for v in values)) * ctx.canonical.unit_factor


def _cash_quality(ctx: Any) -> MetricValue:
    ocf = _sum_override(ctx, "operating_cash_flow_3yr_cumulative")
    income = _sum_override(ctx, "net_income_3yr_cumulative")
    if ocf is None or income is None: return _metric("cash_flow_quality_below_50pct", _UNKNOWN, reason="both three-year cumulative values are required")
    if income <= 0: return _metric("cash_flow_quality_below_50pct", _NA, reason="cumulative net income is non-positive")
    return _metric("cash_flow_quality_below_50pct", _VALUE, ocf / income < .5)


def _dso(ctx: Any) -> Optional[float]:
    value = ctx.canonical.financials().get("trade_receivables_days")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _dso_flag(metric_id: str, threshold: float, spike: bool = False):
    def calculate(ctx: Any) -> MetricValue:
        value = _dso(ctx)
        if value is None: return _metric(metric_id, _UNKNOWN, reason="trade receivables days is not supplied")
        spiked = False
        if spike and len(ctx.periods) >= 2:
            prior, latest = ctx.periods[-2].get("receivable_days"), ctx.periods[-1].get("receivable_days")
            spiked = prior is not None and prior > 0 and latest is not None and latest / prior > 1.25
        return _metric(metric_id, _VALUE, value > threshold or spiked)
    return calculate


def _wc_flag(metric_id: str, threshold: float):
    def calculate(ctx: Any) -> MetricValue:
        value = ctx.canonical.financials().get("net_working_capital_pct_revenue")
        if not isinstance(value, (int, float)) or isinstance(value, bool): return _metric(metric_id, _UNKNOWN, reason="net working capital intensity is not supplied")
        return _metric(metric_id, _VALUE, float(value) > threshold)
    return calculate

_METRICS = {
    "cash_flow_quality_below_50pct": _cash_quality,
    "dso_above_60": _dso_flag("dso_above_60", 60),
    "dso_above_90": _dso_flag("dso_above_90", 90),
    "dso_above_120_or_spike": _dso_flag("dso_above_120_or_spike", 120, True),
    "working_capital_above_20": _wc_flag("working_capital_above_20", 20),
    "working_capital_above_35": _wc_flag("working_capital_above_35", 35),
    "working_capital_above_50": _wc_flag("working_capital_above_50", 50),
}


def with_financial_health_extension(config: Mapping[str, Any]) -> Dict[str, Any]:
    extended = copy.deepcopy(dict(config))
    module = next(item for item in extended["modules"] if item["id"] == "A")
    existing = {item["id"] for item in module["criteria"]}
    module["criteria"].extend(copy.deepcopy(item) for item in FINANCIAL_HEALTH_CRITERIA if item["id"] not in existing)
    return extended


@contextmanager
def financial_health_metrics() -> Iterator[None]:
    """Temporarily register extension metrics without mutating frozen Layer 1."""
    with _LOCK:
        prior = {name: REGISTRY.get(name) for name in _METRICS}
        REGISTRY.update(_METRICS)
        try:
            yield
        finally:
            for name, value in prior.items():
                if value is None: REGISTRY.pop(name, None)
                else: REGISTRY[name] = value


__all__ = ["FINANCIAL_HEALTH_TARGETS", "FINANCIAL_HEALTH_CRITERIA", "with_financial_health_extension", "financial_health_metrics"]
