"""Governed Layer 2C overrides for existing Module B/C/E/F score inputs.

The frozen derived/scoring modules are not modified.  During one secondary
calculation only, supplied evidence-backed values replace the corresponding
derived metric functions; all other metrics retain normal fail-closed logic.
"""
from __future__ import annotations

from contextlib import contextmanager
from threading import RLock
from typing import Any, Iterator, Mapping

from .canonical import State
from .derived import MetricValue, REGISTRY

SCORE_OVERRIDE_TARGETS = {
    "business.industry_cagr_pct": "industry_cagr_pct",
    "business.moat_rating": "moat_rating",
    "business.top5_concentration_pct": "top5_concentration_pct",
    "business.visibility_rating": "visibility_rating",
    "valuation.second_multiple_premium_pct": "second_multiple_premium_pct",
    "valuation.sector_ipo_relative": "sector_ipo_relative",
    "issue.use_of_proceeds_bucket": "use_of_proceeds_bucket",
    "capital_structure.lockin_bucket": "lockin_bucket",
    "market.anchor_bucket": "anchor_bucket",
    "market.gmp_bucket": "gmp_bucket",
    "market.market_regime_bucket": "market_regime_bucket",
}

_CATEGORICAL = frozenset({
    "moat_rating", "visibility_rating", "sector_ipo_relative",
    "use_of_proceeds_bucket", "lockin_bucket", "anchor_bucket", "gmp_bucket",
    "market_regime_bucket",
})
_LOCK = RLock()


def _constant_metric(metric_id: str, value: Any):
    kind = "categorical" if metric_id in _CATEGORICAL else "numeric"
    def calculate(_ctx: Any) -> MetricValue:
        return MetricValue(
            metric_id, State.VALUE.value, value=value, kind=kind,
            formula="evidence-backed Layer 2C governed override",
            inputs=[next(target for target, name in SCORE_OVERRIDE_TARGETS.items() if name == metric_id)],
        )
    return calculate


@contextmanager
def score_override_metrics(values: Mapping[str, Any]) -> Iterator[None]:
    replacements = {
        SCORE_OVERRIDE_TARGETS[target]: _constant_metric(SCORE_OVERRIDE_TARGETS[target], value)
        for target, value in values.items() if target in SCORE_OVERRIDE_TARGETS
    }
    with _LOCK:
        prior = {name: REGISTRY.get(name) for name in replacements}
        REGISTRY.update(replacements)
        try:
            yield
        finally:
            for name, value in prior.items():
                if value is None:
                    REGISTRY.pop(name, None)
                else:
                    REGISTRY[name] = value


__all__ = ["SCORE_OVERRIDE_TARGETS", "score_override_metrics"]
