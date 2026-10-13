"""Deterministic scoring engine and points-weighted confidence.

Spec v1.5 s10 requires every criterion to have a defined input, semantic state,
scoring behaviour, weight/points, evidence/provenance and audit information,
and forbids silently substituting defaults.

The reference prototype scored a missing metric as ``0`` (config convention
``missing_data: "a criterion whose metric is null scores 0"``). v1.5 s18
replaces that with three criterion states:

``SCORED``          the metric is VALUE and produced a score;
``UNKNOWN``         the metric is UNKNOWN - contributes 0 to the base score but
                    its full ``max`` to the upper bound, and it is excluded
                    from the confidence numerator;
``NOT_APPLICABLE``  the metric genuinely does not apply - excluded from both
                    the numerator and the denominator of completeness.

Confidence uses point weighting (spec s11, s18):

    completeness = available evaluable positive points / total evaluable
                   positive points x 100

Penalty criteria (max 0) are excluded from the positive-point denominator; the
engine additionally reports critical-data, knockout, valuation and market
completeness so that high overall completeness cannot hide a missing critical
knockout field (tech design s9).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .derived import DerivedMetrics, MetricValue
from .hashing import sha256_of
from .knockouts import KnockoutSummary
from .overlays import EffectiveScoringPlan, effective_criteria

STATE_SCORED = "SCORED"
STATE_UNKNOWN = "UNKNOWN"
STATE_NOT_APPLICABLE = "NOT_APPLICABLE"
STATE_EXCLUDED_BY_MODE = "EXCLUDED_BY_MODE"

OPEATORS = {">", ">=", "<", "<=", "=="}


@dataclass
class CriterionResult:
    criterion_id: str
    label: str
    module: str
    max: float
    metric: Optional[str]
    state: str
    score: Optional[float] = None
    band: Optional[str] = None
    value: Any = None
    reason: str = ""
    kind: str = "criterion"
    min_points: Optional[float] = None
    evidence_refs: Tuple[str, ...] = ()
    capped_by: Optional[str] = None
    exempted_by: Optional[str] = None
    zeroed_by: Optional[str] = None
    formula: str = ""

    @property
    def is_scored(self) -> bool:
        return self.state == STATE_SCORED

    @property
    def is_unknown(self) -> bool:
        return self.state == STATE_UNKNOWN

    @property
    def is_penalty(self) -> bool:
        return self.kind == "penalty"

    @property
    def effective_score(self) -> float:
        return float(self.score) if self.score is not None else 0.0

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "criterion_id": self.criterion_id,
            "label": self.label,
            "module": self.module,
            "max": self.max,
            "metric": self.metric,
            "kind": self.kind,
            "state": self.state,
            "reason": self.reason,
        }
        if self.score is not None:
            out["score"] = self.score
        if self.band is not None:
            out["band"] = self.band
        if self.value is not None:
            out["value"] = self.value
        if self.min_points is not None:
            out["min"] = self.min_points
        if self.evidence_refs:
            out["evidence_refs"] = list(self.evidence_refs)
        for key in ("capped_by", "exempted_by", "zeroed_by"):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        if self.formula:
            out["formula"] = self.formula
        return out


@dataclass
class ModuleResult:
    module_id: str
    name: str
    max: float
    score: float
    criteria: Tuple[CriterionResult, ...]

    @property
    def available_points(self) -> float:
        return sum(c.max for c in self.criteria if c.state == STATE_SCORED and not c.is_penalty)

    @property
    def unknown_points(self) -> float:
        return sum(c.max for c in self.criteria if c.state == STATE_UNKNOWN and not c.is_penalty)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "name": self.name,
            "max": self.max,
            "score": self.score,
            "available_points": self.available_points,
            "unknown_points": self.unknown_points,
            "criteria": [c.to_dict() for c in self.criteria],
        }


def _apply_bands(value: float, table: Mapping[str, Any]) -> Tuple[float, str]:
    for operator, threshold, score in table.get("bands", []):
        if operator == ">":
            hit = value > threshold
        elif operator == ">=":
            hit = value >= threshold
        elif operator == "<":
            hit = value < threshold
        elif operator == "<=":
            hit = value <= threshold
        elif operator == "==":
            hit = value == threshold
        else:  # pragma: no cover - rejected by the config gate
            raise ValueError(f"invalid band operator {operator!r}")
        if hit:
            return float(score), f"{operator} {threshold}"
    return float(table.get("else", 0)), "else"


def evaluate_criterion(
    criterion: Mapping[str, Any],
    module_id: str,
    derived: DerivedMetrics,
    excluded_by_mode: Sequence[str],
) -> CriterionResult:
    """Score one criterion, honouring tri-state semantics."""
    criterion_id = str(criterion["id"])
    label = str(criterion.get("label", criterion_id))
    maximum = float(criterion.get("max", 0))
    kind = str(criterion.get("kind", "criterion"))
    minimum = criterion.get("min")
    metric_id = criterion.get("metric")

    base = CriterionResult(
        criterion_id=criterion_id,
        label=label,
        module=module_id,
        max=maximum,
        metric=metric_id,
        state=STATE_UNKNOWN,
        kind=kind,
        min_points=float(minimum) if minimum is not None else None,
    )

    if criterion_id in excluded_by_mode:
        base.state = STATE_EXCLUDED_BY_MODE
        base.reason = "not applicable in this evaluation mode"
        return base

    # -- penalty criteria ---------------------------------------------------
    if "when" in criterion and metric_id is None:
        truth = _flag_truth(criterion["when"], derived)
        if truth is True:
            base.state = STATE_SCORED
            base.score = float(criterion.get("points", 0))
            base.reason = "triggered"
            base.band = "triggered"
        elif truth is False:
            base.state = STATE_SCORED
            base.score = 0.0
            base.reason = "not triggered"
            base.band = "not triggered"
        else:
            base.state = STATE_UNKNOWN
            base.reason = "the penalty trigger could not be evaluated from the supplied inputs"
        return base

    # -- zero_if: the criterion genuinely does not apply ---------------------
    if "zero_if" in criterion and _flag_truth(criterion["zero_if"], derived) is True:
        base.state = STATE_SCORED
        base.score = 0.0
        base.reason = "not applicable to this offer structure, scoring zero by configuration"
        base.zeroed_by = str(criterion["zero_if"].get("flag", "zero_if"))
        return base

    item: Optional[MetricValue] = derived.metrics.get(metric_id) if metric_id else None
    if item is None:
        base.state = STATE_UNKNOWN
        base.reason = f"metric {metric_id!r} is not implemented"
        return base

    base.formula = item.formula
    base.value = item.value if item.is_value else None

    # -- unknown metrics stay unknown (never silently zero) -----------------
    if item.is_unknown:
        base.state = STATE_UNKNOWN
        base.reason = item.reason or f"{metric_id} is UNKNOWN"
        return base
    if item.is_not_applicable:
        base.state = STATE_NOT_APPLICABLE
        base.reason = item.reason or f"{metric_id} is NOT_APPLICABLE"
        return base

    # -- exempt_if ----------------------------------------------------------
    if "exempt_if" in criterion:
        flag = criterion["exempt_if"].get("flag")
        flag_item = derived.metrics.get(flag) if flag else None
        if flag_item is not None and flag_item.is_value and flag_item.value is True:
            base.state = STATE_SCORED
            base.score = float(criterion["exempt_if"].get("score", 0))
            base.reason = f"exempted by {flag}"
            base.band = "exempt"
            base.exempted_by = flag
            return base

    # -- score --------------------------------------------------------------
    rule = criterion["rule"]
    rule_type = rule["type"]
    value = item.value

    if rule_type == "categorical":
        key = str(value).lower() if isinstance(value, bool) else str(value)
        if key not in rule["map"]:
            base.state = STATE_UNKNOWN
            base.reason = (
                f"bucket {value!r} produced by {metric_id} is not mapped by this criterion, so it "
                "cannot be scored"
            )
            return base
        score = float(rule["map"][key])
        band = key
    elif rule_type == "bands":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            base.state = STATE_UNKNOWN
            base.reason = f"{metric_id} produced a non-numeric value for a banded criterion"
            return base
        score, band = _apply_bands(float(value), rule)
    else:  # bands_by_variant
        variant_metric = rule["variant_metric"]
        variant_item = derived.metrics.get(variant_metric)
        if variant_item is None or not variant_item.is_value:
            base.state = STATE_UNKNOWN
            base.reason = (
                f"the band table depends on {variant_metric}, which is UNKNOWN, so the criterion "
                "cannot be scored"
            )
            return base
        table = rule["variants"].get(str(variant_item.value))
        if table is None:
            base.state = STATE_UNKNOWN
            base.reason = f"no band table for variant {variant_item.value!r}"
            return base
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            base.state = STATE_UNKNOWN
            base.reason = f"{metric_id} produced a non-numeric value for a banded criterion"
            return base
        score, band = _apply_bands(float(value), table)

    base.score = score
    base.band = band
    base.reason = f"matched {band}"
    base.state = STATE_SCORED

    # -- cap_if -------------------------------------------------------------
    if "cap_if" in criterion:
        flag = criterion["cap_if"]["flag"]
        flag_item = derived.metrics.get(flag)
        cap = float(criterion["cap_if"]["cap"])
        if flag_item is not None and flag_item.is_value and flag_item.value is True and base.score > cap:
            base.score = cap
            base.capped_by = flag
            base.reason += f"; capped at {cap} by {flag}"

    if base.score is not None and base.score > maximum:
        base.score = maximum
        base.reason += f"; clamped to the criterion maximum of {maximum}"

    return base


def _flag_truth(expr: Mapping[str, Any], derived: DerivedMetrics) -> Optional[bool]:
    """Evaluate a flag expression, returning None when it is UNKNOWN."""
    if "all" in expr:
        results = [_flag_truth(c, derived) for c in expr["all"]]
        if any(r is False for r in results):
            return False
        return None if any(r is None for r in results) else True
    if "any" in expr:
        results = [_flag_truth(c, derived) for c in expr["any"]]
        if any(r is True for r in results):
            return True
        return None if any(r is None for r in results) else False
    if "flag" in expr:
        item = derived.metrics.get(expr["flag"])
        if item is None or not item.is_value:
            return None
        return bool(item.value)
    metric_id = expr.get("metric")
    item = derived.metrics.get(metric_id) if metric_id else None
    if item is None or not item.is_value:
        return None
    value, target, operator = item.value, expr.get("value"), expr.get("op")
    if operator == "in":
        return value in target
    if operator == ">":
        return value > target
    if operator == ">=":
        return value >= target
    if operator == "<":
        return value < target
    if operator == "<=":
        return value <= target
    if operator == "==":
        return value == target
    raise ValueError(f"unsupported operator {operator!r}")


@dataclass
class ScoreResult:
    mode: str
    modules: Tuple[ModuleResult, ...]
    base_score: float
    penalties_total: float
    score_before_caps: float
    final_score: float
    caps_applied: Tuple[Mapping[str, Any], ...]
    lower_bound: float
    upper_bound: float
    available_points: float
    total_evaluable_points: float
    unknown_points: float
    not_applicable_points: float
    completeness_pct: float
    confidence: str
    completeness_breakdown: Mapping[str, Any]
    verdict: str
    verdict_band_score: str
    verdict_uncertain: bool
    insufficient_data: bool
    criteria: Tuple[CriterionResult, ...]
    unresolved_penalty_points: float
    plan_hash: str
    penalty_items: Tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "penalties": [dict(p) for p in self.penalty_items],
            "base_score": self.base_score,
            "penalties_total": self.penalties_total,
            "score_before_caps": self.score_before_caps,
            "final_score": self.final_score,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "available_points": self.available_points,
            "total_evaluable_points": self.total_evaluable_points,
            "unknown_points": self.unknown_points,
            "not_applicable_points": self.not_applicable_points,
            "unresolved_penalty_points": self.unresolved_penalty_points,
            "completeness_pct": self.completeness_pct,
            "confidence": self.confidence,
            "completeness_breakdown": dict(self.completeness_breakdown),
            "verdict": self.verdict,
            "verdict_band_score": self.verdict_band_score,
            "verdict_uncertain": self.verdict_uncertain,
            "insufficient_data": self.insufficient_data,
            "caps_applied": [dict(c) for c in self.caps_applied],
            "modules": [m.to_dict() for m in self.modules],
            "plan_hash": self.plan_hash,
        }


def _band_verdict(score: float, verdict_cfg: Mapping[str, Any]) -> str:
    for band in verdict_cfg.get("bands", []):
        if score >= band["min"]:
            return str(band["verdict"])
    return str(verdict_cfg.get("else", "AVOID"))


def score(
    config: Mapping[str, Any],
    derived: DerivedMetrics,
    plan: EffectiveScoringPlan,
    knockouts: KnockoutSummary,
    mode: str = "final",
) -> ScoreResult:
    """Run the deterministic scorer for one mode."""
    mode_cfg = (config.get("modes") or {}).get(mode)
    if mode_cfg is None:
        raise ValueError(f"unknown evaluation mode {mode!r}")
    excluded = tuple(mode_cfg.get("exclude", []) or [])

    criteria_by_module = effective_criteria(config, plan)
    modules: List[ModuleResult] = []
    all_criteria: List[CriterionResult] = []

    for module in config.get("modules", []):
        module_id = module["id"]
        evaluated = [
            evaluate_criterion(criterion, module_id, derived, excluded)
            for criterion in criteria_by_module.get(module_id, [])
        ]
        positive_score = sum(c.effective_score for c in evaluated if not c.is_penalty)
        negative_score = sum(c.effective_score for c in evaluated if c.is_penalty)
        modules.append(
            ModuleResult(
                module_id=module_id,
                name=module["name"],
                max=float(module["max"]),
                score=max(0.0, positive_score + negative_score),
                criteria=tuple(evaluated),
            )
        )
        all_criteria.extend(evaluated)

    # -- penalties ----------------------------------------------------------
    penalties_total, penalty_items, unresolved_penalty_points = _evaluate_penalties(config, derived)

    base_score = sum(m.score for m in modules)
    score_before_caps = max(0.0, base_score + penalties_total)

    # -- caps ---------------------------------------------------------------
    caps_applied: List[Mapping[str, Any]] = []
    final_score = score_before_caps
    for cap in config.get("caps", []) or []:
        truth = _flag_truth(cap["when"], derived)
        if truth is True:
            caps_applied.append({"id": cap["id"], "max_score": cap["max_score"]})
            final_score = min(final_score, float(cap["max_score"]))

    # -- completeness and bounds -------------------------------------------
    evaluable = [c for c in all_criteria if not c.is_penalty and c.state != STATE_EXCLUDED_BY_MODE]
    positive = [c for c in evaluable if c.max > 0]
    available_points = sum(c.max for c in positive if c.state == STATE_SCORED)
    unknown_points = sum(c.max for c in positive if c.state == STATE_UNKNOWN)
    not_applicable_points = sum(c.max for c in positive if c.state == STATE_NOT_APPLICABLE)
    total_evaluable_points = available_points + unknown_points

    if total_evaluable_points > 0:
        completeness_pct = available_points / total_evaluable_points * 100.0
    else:
        completeness_pct = 0.0

    confidence_cfg = config.get("confidence") or {}
    if completeness_pct >= float(confidence_cfg.get("high_min_completeness_pct", 95)):
        confidence = "High"
    elif completeness_pct >= float(confidence_cfg.get("medium_min_completeness_pct", 80)):
        confidence = "Medium"
    else:
        confidence = "Low"

    # Lower bound: unknown positive items contribute nothing, and unknown
    # penalties are applied where reasonably possible (spec s18).
    lower_bound = _apply_caps(
        config, max(0.0, base_score + penalties_total - unresolved_penalty_points), derived
    )
    # Upper bound: unknown positive items earn their full available points and
    # unknown penalties are not triggered.
    upper_bound = _apply_caps(config, max(0.0, base_score + unknown_points + penalties_total), derived)

    breakdown = _completeness_breakdown(
        config, all_criteria, derived, knockouts, plan, completeness_pct
    )

    verdict_cfg = config.get("verdict") or {}
    verdict_band_score = _band_verdict(final_score, verdict_cfg)
    lower_verdict = _band_verdict(lower_bound, verdict_cfg)
    upper_verdict = _band_verdict(upper_bound, verdict_cfg)
    verdict_uncertain = lower_verdict != upper_verdict

    critical_missing = [
        name
        for name in (config.get("critical_data") or {}).get("items", [])
        if (derived.metrics.get(name) is None or not derived.metrics[name].is_value)
    ]

    if knockouts.any_triggered:
        verdict = str(verdict_cfg.get("knockout_verdict", "AVOID"))
        verdict_uncertain = False
        insufficient_data = False
    elif critical_missing:
        verdict = str(confidence_cfg.get("low_verdict", "INSUFFICIENT_DATA"))
        insufficient_data = True
    elif verdict_uncertain:
        verdict = str(verdict_cfg.get("uncertain_verdict", "VERDICT_UNCERTAIN"))
        insufficient_data = False
    else:
        verdict = verdict_band_score
        insufficient_data = False

    return ScoreResult(
        mode=mode,
        modules=tuple(modules),
        base_score=base_score,
        penalties_total=penalties_total,
        score_before_caps=score_before_caps,
        final_score=final_score,
        caps_applied=tuple(caps_applied),
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        available_points=available_points,
        total_evaluable_points=total_evaluable_points,
        unknown_points=unknown_points,
        not_applicable_points=not_applicable_points,
        completeness_pct=completeness_pct,
        confidence=confidence,
        completeness_breakdown=breakdown,
        verdict=verdict,
        verdict_band_score=verdict_band_score,
        verdict_uncertain=verdict_uncertain,
        insufficient_data=insufficient_data,
        criteria=tuple(all_criteria),
        unresolved_penalty_points=unresolved_penalty_points,
        plan_hash=plan.hash(),
        penalty_items=tuple(penalty_items),
    )


def _apply_caps(
    config: Mapping[str, Any], value: float, derived: DerivedMetrics
) -> float:
    result = value
    for cap in config.get("caps", []) or []:
        if _flag_truth(cap["when"], derived) is True:
            result = min(result, float(cap["max_score"]))
    return result


def _evaluate_penalties(
    config: Mapping[str, Any], derived: DerivedMetrics
) -> Tuple[float, List[Dict[str, Any]], float]:
    """Return (applied total, items, points held in reserve as unresolved).

    An unverified penalty is *not* automatically applied nor ignored: its
    magnitude is returned as ``unresolved`` so the lower bound can assume it
    applies while the base score does not (spec s17).
    """
    penalty_cfg = config.get("penalties") or {}
    items: List[Dict[str, Any]] = []
    unresolved = 0.0

    for penalty in penalty_cfg.get("items", []):
        penalty_id = str(penalty.get("id"))
        label = str(penalty.get("label", penalty_id))
        points = penalty.get("points")
        scale = penalty.get("scale")

        if scale is not None:
            metric_id = penalty.get("metric")
            item = derived.metrics.get(metric_id)
            if item is None or not item.is_value:
                magnitude = abs(min(scale.values())) if scale else 0.0
                unresolved += magnitude
                items.append(
                    {
                        "id": penalty_id,
                        "label": label,
                        "points": 0,
                        "state": STATE_UNKNOWN,
                        "reason": (
                            f"materiality metric {metric_id} is UNKNOWN; the penalty is neither "
                            "applied nor ignored, and is carried in the lower bound"
                        ),
                    }
                )
                continue
            applied = float(scale.get(str(item.value), 0))
            items.append(
                {
                    "id": penalty_id,
                    "label": label,
                    "points": applied,
                    "state": STATE_SCORED,
                    "reason": f"materiality {item.value}",
                }
            )
            continue

        truth = _flag_truth(penalty["when"], derived)
        if truth is True:
            items.append(
                {
                    "id": penalty_id,
                    "label": label,
                    "points": float(points),
                    "state": STATE_SCORED,
                    "reason": "triggered",
                }
            )
        elif truth is False:
            items.append(
                {
                    "id": penalty_id,
                    "label": label,
                    "points": 0.0,
                    "state": STATE_SCORED,
                    "reason": "not triggered",
                }
            )
        else:
            unresolved += abs(float(points))
            items.append(
                {
                    "id": penalty_id,
                    "label": label,
                    "points": 0.0,
                    "state": STATE_UNKNOWN,
                    "reason": (
                        "the trigger could not be evaluated; the penalty is neither applied nor "
                        "ignored, and is carried in the lower bound"
                    ),
                }
            )

    applied_total = sum(float(i["points"]) for i in items)
    floor = float(penalty_cfg.get("max_total", -15))
    applied_total = max(floor, applied_total)
    return applied_total, items, unresolved


def _completeness_breakdown(
    config: Mapping[str, Any],
    criteria: Sequence[CriterionResult],
    derived: DerivedMetrics,
    knockouts: KnockoutSummary,
    plan: EffectiveScoringPlan,
    overall: float,
) -> Dict[str, Any]:
    """Compute the separate completeness measures required by tech design s9."""

    def pct(available: float, total: float) -> float:
        return round(available / total * 100.0, 6) if total > 0 else 0.0

    valuation_ids = {"pe_vs_peers", "second_multiple", "peg", "sector_ipo_relative",
                     "ps_evsales_vs_peers", "pb_roe_adjusted"}
    market_ids = {"anchor_quality", "qib_subscription", "gmp_trend", "market_regime",
                  "overall_subscription", "nii_subscription"}

    valuation = [c for c in criteria if c.criterion_id in valuation_ids and not c.is_penalty]
    market = [c for c in criteria if c.criterion_id in market_ids and not c.is_penalty]

    valuation_available = sum(c.max for c in valuation if c.state == STATE_SCORED)
    valuation_total = valuation_available + sum(c.max for c in valuation if c.state == STATE_UNKNOWN)

    market_available = sum(c.max for c in market if c.state == STATE_SCORED)
    market_total = market_available + sum(c.max for c in market if c.state == STATE_UNKNOWN)

    critical_items = (config.get("critical_data") or {}).get("items", [])
    critical_available = sum(
        1 for name in critical_items if derived.metrics.get(name) is not None and derived.metrics[name].is_value
    )

    return {
        "overall_pct": round(overall, 6),
        "weighting": "POINTS",
        "valuation_pct": pct(valuation_available, valuation_total),
        "market_pct": pct(market_available, market_total),
        "critical_data_pct": pct(critical_available, len(critical_items)),
        "critical_data_missing": [
            name
            for name in critical_items
            if derived.metrics.get(name) is None or not derived.metrics[name].is_value
        ],
        "knockout_completeness_pct": round(knockouts.completeness_pct(), 6),
        "knockout_unverified": [r.rule_id for r in knockouts.unverified],
        "valuation_points_unknown": sum(c.max for c in valuation if c.state == STATE_UNKNOWN),
        "market_points_unknown": sum(c.max for c in market if c.state == STATE_UNKNOWN),
        "profile": plan.resolved_profile,
        "structure_overlays": list(plan.structure_overlays),
    }


__all__ = [
    "STATE_SCORED",
    "STATE_UNKNOWN",
    "STATE_NOT_APPLICABLE",
    "STATE_EXCLUDED_BY_MODE",
    "CriterionResult",
    "ModuleResult",
    "ScoreResult",
    "evaluate_criterion",
    "score",
]
