"""Sector and structure overlay resolution.

Spec v1.5 s14: "Sector overlays are mandatory implementations, not decorative
config." The resolver emits an explicit, auditable effective scoring plan -
which criteria were removed, which replaced them, the metric overrides in
force and the resulting module totals - and then validates that plan before
scoring begins.

Spec v1.5 s15: the retail-heavy structure overlay must be validated to ensure
that removed criteria are actually removed, that replacement criteria exist,
that replacement maxima reconcile and that the module total remains correct.

Spec v1.5 s14: "If an overlay is selected but one of its required metrics is
not implemented, the engine must fail validation rather than silently score
zero." Because the configuration gate already proves every metric exists, the
resolver re-asserts it for the *selected* overlay so the failure is attributed
to the overlay rather than to the config as a whole.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .derived import REGISTRY, DerivedMetrics
from .errors import Finding, SEVERITY_ERROR, ValidationError
from .hashing import sha256_of

PROFILE_STANDARD = "standard"
PROFILE_LOSS_MAKING = "loss_making"


def _eval_condition(expr: Mapping[str, Any], derived: DerivedMetrics) -> bool:
    """Evaluate a resolver predicate.

    Only used to decide *whether* an overlay applies (for example
    ``pat_latest < 0``). The predicate is evaluated with the same tri-state
    discipline as the scorer: an UNKNOWN leaf makes the predicate UNKNOWN,
    which is treated as "not selected" and surfaced as a warning by the
    resolver rather than being silently treated as False.
    """
    if "all" in expr:
        return all(_eval_condition(c, derived) for c in expr["all"])
    if "any" in expr:
        return any(_eval_condition(c, derived) for c in expr["any"])
    if "flag" in expr:
        item = derived.metrics.get(expr["flag"])
        return bool(item.is_value and item.value is True)
    metric_id = expr.get("metric")
    item = derived.metrics.get(metric_id) if metric_id else None
    if item is None or not item.is_value:
        return False
    value = item.value
    target = expr.get("value")
    operator = expr.get("op")
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
    raise ValueError(f"unsupported operator {operator!r} in overlay predicate")


def _predicate_is_unknown(expr: Mapping[str, Any], derived: DerivedMetrics) -> bool:
    if "flag" in expr:
        item = derived.metrics.get(expr["flag"])
        return item is None or not item.is_value
    if "metric" in expr:
        item = derived.metrics.get(expr["metric"])
        return item is None or not item.is_value
    for key in ("all", "any"):
        if key in expr:
            return any(_predicate_is_unknown(c, derived) for c in expr[key])
    return False


@dataclass
class EffectiveScoringPlan:
    """The explicit, auditable result of overlay resolution (tech design s6)."""

    requested_profile: str
    resolved_profile: str
    auto_profile_applied: Optional[str]
    sector_overlay: Optional[str]
    structure_overlays: Tuple[str, ...]
    removed_criteria: Tuple[str, ...]
    added_criteria: Tuple[Mapping[str, Any], ...]
    metric_overrides: Mapping[str, str]
    effective_module_totals: Mapping[str, float]
    total_points: float
    findings: List[Finding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requested_profile": self.requested_profile,
            "resolved_profile": self.resolved_profile,
            "auto_profile_applied": self.auto_profile_applied,
            "sector_overlay": self.sector_overlay,
            "structure_overlays": list(self.structure_overlays),
            "removed": list(self.removed_criteria),
            "added": [c["id"] for c in self.added_criteria],
            "metric_overrides": dict(self.metric_overrides),
            "effective_module_totals": dict(self.effective_module_totals),
            "total_points": self.total_points,
            "findings": [f.to_dict() for f in self.findings],
        }

    def hash(self) -> str:
        return sha256_of(self.to_dict())


def resolve_overlays(
    config: Mapping[str, Any],
    derived: DerivedMetrics,
    requested_profile: str,
) -> EffectiveScoringPlan:
    """Resolve the effective scoring plan and validate it.

    Raises :class:`ValidationError` if the selected overlay does not reconcile.
    """
    findings: List[Finding] = []
    thresholds = config.get("thresholds", {})

    # -- profile resolution -------------------------------------------------
    resolved_profile = requested_profile
    auto_profile: Optional[str] = None
    for rule in (config.get("profile_resolution") or {}).get("auto_rules", []):
        if resolved_profile in (rule.get("unless_profile") or []):
            continue
        if _eval_condition(rule["when"], derived):
            resolved_profile = rule["profile"]
            auto_profile = rule["profile"]
            break

    # -- sector overlay -----------------------------------------------------
    sector_name = resolved_profile if resolved_profile != PROFILE_STANDARD else None
    sector_overlay = (config.get("sector_overlays") or {}).get(sector_name) if sector_name else None
    if sector_name and sector_overlay is None:
        raise ValidationError(
            "overlay",
            [
                Finding(
                    code="OVERLAY_SELECTED_BUT_NOT_IMPLEMENTED",
                    message=(
                        f"profile {sector_name!r} was selected but no sector overlay is defined; "
                        "spec s14 requires the engine to fail rather than silently score the "
                        "standard criteria"
                    ),
                    severity=SEVERITY_ERROR,
                    scope="overlay",
                    location=f"sector_overlays.{sector_name}",
                )
            ],
        )

    # -- structure overlays -------------------------------------------------
    structure_names: List[str] = []
    structure_trigger_unknown: List[str] = []
    for name, overlay in (config.get("structure_overlays") or {}).items():
        condition = overlay.get("when")
        if condition is None:
            continue
        if _eval_condition(condition, derived):
            structure_names.append(name)
        elif _predicate_is_unknown(condition, derived):
            structure_trigger_unknown.append(name)
            findings.append(
                Finding(
                    code="OVERLAY_TRIGGER_UNKNOWN",
                    message=(
                        f"structure overlay {name!r} could not be evaluated because the metric that "
                        "triggers it is UNKNOWN; the overlay is treated as not applied"
                    ),
                    severity="WARNING",
                    scope="overlay",
                    location=f"structure_overlays.{name}",
                    detail={"predicate": dict(condition)},
                )
            )

    # -- assemble removal / addition ---------------------------------------
    removed: List[str] = []
    added: List[Mapping[str, Any]] = []
    overrides: Dict[str, str] = {}

    if sector_overlay:
        removed.extend(sector_overlay.get("remove", []) or [])
        added.extend(sector_overlay.get("add", []) or [])
        overrides.update(sector_overlay.get("metric_override", {}) or {})
    for name in structure_names:
        overlay = config["structure_overlays"][name]
        removed.extend(overlay.get("remove", []) or [])
        added.extend(overlay.get("add", []) or [])

    duplicates = sorted({c for c in removed if removed.count(c) > 1})
    if duplicates:
        findings.append(
            Finding(
                code="OVERLAY_DOUBLE_REMOVE",
                message=(
                    f"criteria {duplicates} are removed by more than one applicable overlay; the "
                    "overlays are not independent and the module totals may not reconcile"
                ),
                severity=SEVERITY_ERROR,
                scope="overlay",
            )
        )

    # -- validate the selected overlay's required metrics -------------------
    required_metrics: Dict[str, str] = {}
    for criterion in added:
        required_metrics[str(criterion.get("metric"))] = str(criterion.get("id"))
    for criterion in added:
        for dependency in criterion.get("requires", []) or []:
            required_metrics.setdefault(str(dependency), str(criterion.get("id")))
    for criterion_id, metric_id in overrides.items():
        required_metrics[metric_id] = criterion_id

    missing_metrics = sorted(m for m in required_metrics if m not in REGISTRY and not m.endswith("_snapshot"))
    if missing_metrics:
        findings.append(
            Finding(
                code="OVERLAY_METRIC_NOT_IMPLEMENTED",
                message=(
                    f"the selected overlay requires metric(s) {missing_metrics} which the engine does "
                    "not implement; spec s14 requires validation to fail rather than silently "
                    "scoring zero"
                ),
                severity=SEVERITY_ERROR,
                scope="overlay",
                detail={"metrics": missing_metrics},
            )
        )

    # -- effective module totals -------------------------------------------
    base_modules = {m["id"]: m for m in config.get("modules", [])}
    base_criteria = {
        c["id"]: c for m in config.get("modules", []) for c in m.get("criteria", [])
    }
    removed_set = set(removed)
    effective_totals: Dict[str, float] = {}
    for module_id, module in base_modules.items():
        total = 0.0
        seen: set = set()
        for criterion in module.get("criteria", []):
            if criterion["id"] in removed_set:
                continue
            if criterion.get("kind") != "penalty":
                total += criterion.get("max", 0)
            seen.add(criterion["id"])
        for criterion in added:
            if criterion.get("module") != module_id or criterion["id"] in seen:
                continue
            if criterion.get("kind") != "penalty":
                total += criterion.get("max", 0)
        effective_totals[module_id] = round(total, 6)
        declared = float(module.get("max", 0))
        if abs(total - declared) > 1e-9:
            findings.append(
                Finding(
                    code="OVERLAY_MODULE_TOTAL_UNRECONCILED",
                    message=(
                        f"after applying overlays {sector_name or 'none'}"
                        f"{' + ' + ', '.join(structure_names) if structure_names else ''}, module "
                        f"{module_id!r} totals {total} but must remain {declared}; removed and added "
                        "maxima do not reconcile"
                    ),
                    severity=SEVERITY_ERROR,
                    scope="overlay",
                    location=f"modules.{module_id}",
                )
            )

    total_points = round(sum(effective_totals.values()), 6)
    declared_total = float((config.get("validation") or {}).get("assert_total", 100))
    if abs(total_points - declared_total) > 1e-9:
        findings.append(
            Finding(
                code="OVERLAY_TOTAL_UNRECONCILED",
                message=(
                    f"effective criteria total {total_points}, but the configuration asserts "
                    f"{declared_total}"
                ),
                severity=SEVERITY_ERROR,
                scope="overlay",
            )
        )

    # -- replacement criteria must genuinely exist --------------------------
    if sector_overlay:
        for criterion_id in sector_overlay.get("remove", []) or []:
            if criterion_id not in base_criteria:
                findings.append(
                    Finding(
                        code="OVERLAY_REMOVE_MISSING",
                        message=f"overlay removes criterion {criterion_id!r} which does not exist",
                        severity=SEVERITY_ERROR,
                        scope="overlay",
                    )
                )
        for criterion_id in (sector_overlay.get("metric_override") or {}):
            if criterion_id in removed_set:
                findings.append(
                    Finding(
                        code="OVERLAY_OVERRIDE_ON_REMOVED",
                        message=(
                            f"metric override targets criterion {criterion_id!r}, which the same "
                            "overlay removes; the override can never take effect"
                        ),
                        severity=SEVERITY_ERROR,
                        scope="overlay",
                    )
                )

    errors = [f for f in findings if f.severity == SEVERITY_ERROR]
    if errors:
        raise ValidationError("overlay", findings)

    return EffectiveScoringPlan(
        requested_profile=requested_profile,
        resolved_profile=resolved_profile,
        auto_profile_applied=auto_profile,
        sector_overlay=sector_name,
        structure_overlays=tuple(structure_names),
        removed_criteria=tuple(sorted(removed_set)),
        added_criteria=tuple(added),
        metric_overrides=dict(overrides),
        effective_module_totals=effective_totals,
        total_points=total_points,
        findings=findings,
    )


def effective_criteria(
    config: Mapping[str, Any],
    plan: EffectiveScoringPlan,
) -> Dict[str, List[Mapping[str, Any]]]:
    """Return the criteria that actually score, grouped by module.

    Removal happens before the metric override is applied, so an override on a
    removed criterion can never resurrect it.
    """
    removed = set(plan.removed_criteria)
    result: Dict[str, List[Mapping[str, Any]]] = {}
    for module in config.get("modules", []):
        criteria: List[Mapping[str, Any]] = []
        for criterion in module.get("criteria", []):
            if criterion["id"] in removed:
                continue
            if criterion["id"] in plan.metric_overrides:
                criterion = dict(criterion)
                criterion["metric"] = plan.metric_overrides[criterion["id"]]
            criteria.append(criterion)
        criteria.extend(
            c for c in plan.added_criteria if c.get("module") == module["id"]
        )
        result[module["id"]] = criteria
    return result


__all__ = [
    "PROFILE_STANDARD",
    "PROFILE_LOSS_MAKING",
    "EffectiveScoringPlan",
    "resolve_overlays",
    "effective_criteria",
]
