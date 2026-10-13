"""Configuration validation - a hard gate.

Spec v1.5 s3.5: "The engine must validate the configuration before scoring and
refuse to score with an invalid configuration."

Spec v1.5 s20 lists the required assertions:

  * every criterion belongs to exactly one module after overlays;
  * module maxima reconcile;
  * total = 100;
  * overlay replacements reconcile;
  * all referenced metrics exist;
  * all operators are valid;
  * all categorical mappings are complete.

Spec v1.5 s14 adds: if an overlay is selected but one of its required metrics
is not implemented, the engine must fail validation rather than silently
scoring zero.

Validation returns a :class:`ConfigCheck` rather than raising, so a caller can
persist the findings. :func:`compile_config` is the strict entry point used by
the pipeline: it raises :class:`ConfigValidationError` when any error is
present.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .derived import REGISTRY
from .errors import ConfigValidationError, Finding, SEVERITY_ERROR, SEVERITY_WARNING
from .hashing import sha256_of

VALID_OPERATORS: Set[str] = {">", ">=", "<", "<=", "==", "in"}

VALID_RULE_TYPES: Set[str] = {"bands", "categorical", "bands_by_variant"}

VALID_PROFILES: Set[str] = {"standard", "financial", "epc_real_estate", "cyclical", "loss_making"}

#: Buckets each categorical metric can produce. A criterion whose categorical
#: map does not cover the full domain would silently drop cases, so the
#: validator treats an incomplete map as a configuration error.
CATEGORICAL_DOMAIN: Dict[str, Set[str]] = {
    "margin_trend": {"expanding", "stable", "volatile", "declining_or_loss"},
    "margin_trend_5y_avg": {"expanding", "stable", "volatile", "declining_or_loss"},
    "leverage_bucket": {"strong", "ok", "stretched", "weak"},
    "sector_ipo_relative": {"cheaper", "in_line", "richer"},
    "ofs_seller_bucket": {"none_or_small", "pe_vc_exit", "promoter_selling"},
    "use_of_proceeds_bucket": {"growth", "mixed_ok", "debt_heavy", "blind_heavy"},
    "pre_ipo_placement_bucket": {"none_or_near_ipo", "in_between", "deep_discount_12m"},
    "lockin_bucket": {"intact", "weak"},
    "litigation_bucket": {"clean", "minor_civil", "criminal_or_regulatory"},
    "auditor_bucket": {"clean_reputed", "eom_only", "unstable_or_repeated_eom"},
    "board_kmp_bucket": {"independent_stable", "other", "high_churn"},
    "moat_rating": {"leader_with_moat", "strong_niche", "follower", "commoditised"},
    "visibility_rating": {"strong", "moderate", "none"},
    "anchor_bucket": {"reputed", "mixed", "unknown"},
    "gmp_bucket": {"strong", "flat", "falling"},
    "market_regime_bucket": {"supportive", "neutral", "weak"},
    "contribution_bucket": {
        "expanding_2y_gt300bps",
        "positive_improving",
        "positive_flat_or_falling",
        "negative",
    },
    "loss_narrowing_bucket": {"two_years", "one_year", "widening"},
    "nim_cost_income_bucket": {"improving", "stable", "mixed", "deteriorating"},
    "roa_roe_peer_quartile": {"top_quartile", "median", "bottom_half"},
    "asset_quality_bucket": {"improving_strong", "stable", "deteriorating", "stressed"},
    "net_debt_bucket": {"strong", "ok", "stretched", "weak"},
    "eom_materiality": {"none", "low", "medium", "high"},
    # boolean metrics scored through a categorical map use lower-case keys
    "dilution_ok": {"true", "false"},
    "pure_ofs": {"true", "false"},
}

#: Metrics that must be known before a derived metric may be treated as
#: not-applicable rather than unknown. Used for documentation only.
_ = REGISTRY  # imported for the existence check below


@dataclass
class ConfigCheck:
    findings: List[Finding] = field(default_factory=list)
    profile_plans: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_ERROR]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": [f.to_dict() for f in self.errors],
            "warnings": [f.to_dict() for f in self.warnings],
        }


def _err(code: str, message: str, scope: str = "config", location: Optional[str] = None, **detail: Any) -> Finding:
    return Finding(code=code, message=message, severity=SEVERITY_ERROR, scope=scope, location=location, detail=detail)


def _warn(code: str, message: str, scope: str = "config", location: Optional[str] = None, **detail: Any) -> Finding:
    return Finding(code=code, message=message, severity=SEVERITY_WARNING, scope=scope, location=location, detail=detail)


def _all_criteria(config: Mapping[str, Any]) -> Dict[str, Tuple[str, Mapping[str, Any]]]:
    """Map criterion id -> (module id, criterion) across base modules."""
    out: Dict[str, Tuple[str, Mapping[str, Any]]] = {}
    for module in config.get("modules", []):
        for criterion in module.get("criteria", []):
            out[criterion["id"]] = (module["id"], criterion)
    return out


def _overlay_additions(config: Mapping[str, Any]) -> List[Tuple[str, Mapping[str, Any]]]:
    out: List[Tuple[str, Mapping[str, Any]]] = []
    for name, overlay in (config.get("sector_overlays") or {}).items():
        for criterion in overlay.get("add", []) or []:
            out.append((f"sector_overlays.{name}", criterion))
    for name, overlay in (config.get("structure_overlays") or {}).items():
        for criterion in overlay.get("add", []) or []:
            out.append((f"structure_overlays.{name}", criterion))
    return out


def check_expression(expr: Mapping[str, Any], findings: List[Finding], where: str) -> None:
    """Validate a boolean expression node and every metric it references."""
    if "all" in expr:
        if not isinstance(expr["all"], list) or not expr["all"]:
            findings.append(_err("CONFIG_EXPR_EMPTY", "'all' must be a non-empty list", location=where))
            return
        for index, child in enumerate(expr["all"]):
            check_expression(child, findings, f"{where}.all[{index}]")
        return
    if "any" in expr:
        if not isinstance(expr["any"], list) or not expr["any"]:
            findings.append(_err("CONFIG_EXPR_EMPTY", "'any' must be a non-empty list", location=where))
            return
        for index, child in enumerate(expr["any"]):
            check_expression(child, findings, f"{where}.any[{index}]")
        return
    if "not" in expr:
        child = expr["not"]
        if not isinstance(child, Mapping):
            findings.append(
                _err("CONFIG_EXPR_NOT_TYPE", "'not' must wrap a single expression object", location=where)
            )
            return
        check_expression(child, findings, f"{where}.not")
        return
    if "flag" in expr:
        flag_id = expr["flag"]
        if flag_id not in REGISTRY:
            findings.append(
                _err(
                    "CONFIG_FLAG_UNIMPLEMENTED",
                    f"expression references flag {flag_id!r}, which is not implemented by the "
                    "derived-metrics engine; a typo here would leave the rule permanently "
                    "UNVERIFIED instead of failing loudly",
                    location=where,
                    flag=flag_id,
                )
            )
        return
    if "metric" in expr:
        metric_id = expr["metric"]
        if metric_id not in REGISTRY:
            findings.append(
                _err(
                    "CONFIG_METRIC_UNIMPLEMENTED",
                    f"expression references metric {metric_id!r}, which is not implemented by the "
                    "derived-metrics engine; the engine must fail rather than silently score zero",
                    location=where,
                    metric=metric_id,
                )
            )
        if "op" not in expr:
            findings.append(_err("CONFIG_EXPR_NO_OPERATOR", "metric expression has no operator", location=where))
            return
        if expr["op"] not in VALID_OPERATORS:
            findings.append(
                _err(
                    "CONFIG_OPERATOR_INVALID",
                    f"operator {expr['op']!r} is not one of {sorted(VALID_OPERATORS)}",
                    location=where,
                )
            )
        if "value" not in expr:
            findings.append(_err("CONFIG_EXPR_NO_VALUE", "metric expression has no comparison value", location=where))
        elif expr["op"] == "in" and not isinstance(expr["value"], list):
            findings.append(_err("CONFIG_OPERATOR_VALUE", "'in' requires a list value", location=where))
        return
    findings.append(
        _err("CONFIG_EXPR_UNKNOWN", f"expression node {expr!r} is not a flag, metric, all or any node", location=where)
    )


def check_criterion(
    criterion: Mapping[str, Any],
    findings: List[Finding],
    where: str,
) -> None:
    """Validate a single criterion's metric, rule type, operators and bands."""
    criterion_id = criterion.get("id", "<missing-id>")
    if "max" not in criterion:
        findings.append(_err("CONFIG_CRITERION_NO_MAX", f"criterion {criterion_id!r} has no max", location=where))

    if criterion.get("kind") == "penalty":
        if "when" not in criterion:
            findings.append(_err("CONFIG_PENALTY_NO_WHEN", f"penalty {criterion_id!r} has no trigger", location=where))
        else:
            check_expression(criterion["when"], findings, f"{where}.when")
        return

    metric_id = criterion.get("metric")
    if metric_id is None:
        findings.append(_err("CONFIG_CRITERION_NO_METRIC", f"criterion {criterion_id!r} has no metric", location=where))
        return
    if metric_id not in REGISTRY:
        findings.append(
            _err(
                "CONFIG_METRIC_UNIMPLEMENTED",
                f"criterion {criterion_id!r} uses metric {metric_id!r}, which is not implemented by "
                "the derived-metrics engine",
                location=where,
                metric=metric_id,
            )
        )

    for key in ("zero_if", "exempt_if", "cap_if"):
        if key in criterion and isinstance(criterion[key], Mapping) and "metric" in criterion[key]:
            check_expression(criterion[key], findings, f"{where}.{key}")

    rule = criterion.get("rule")
    if rule is None:
        findings.append(_err("CONFIG_CRITERION_NO_RULE", f"criterion {criterion_id!r} has no rule", location=where))
        return
    rule_type = rule.get("type")
    if rule_type not in VALID_RULE_TYPES:
        findings.append(
            _err(
                "CONFIG_RULE_TYPE_INVALID",
                f"criterion {criterion_id!r} rule type {rule_type!r} is not one of {sorted(VALID_RULE_TYPES)}",
                location=where,
            )
        )
        return

    if rule_type == "categorical":
        mapping = rule.get("map")
        if not isinstance(mapping, Mapping) or not mapping:
            findings.append(_err("CONFIG_CATEGORICAL_EMPTY", f"criterion {criterion_id!r} has an empty map", location=where))
            return
        domain = CATEGORICAL_DOMAIN.get(metric_id or "")
        if domain is None:
            findings.append(
                _warn(
                    "CONFIG_CATEGORICAL_DOMAIN_UNKNOWN",
                    f"no bucket domain is declared for metric {metric_id!r}; completeness of the "
                    f"map for criterion {criterion_id!r} could not be proven",
                    location=where,
                )
            )
            domain = set(mapping.keys())
        missing = sorted(domain - set(mapping.keys()))
        if missing:
            findings.append(
                _err(
                    "CONFIG_CATEGORICAL_INCOMPLETE",
                    f"criterion {criterion_id!r} does not map bucket(s) {missing}; those cases would "
                    "be silently dropped rather than scored",
                    location=where,
                    missing=missing,
                )
            )
        extra = sorted(set(mapping.keys()) - domain)
        if extra:
            findings.append(
                _warn(
                    "CONFIG_CATEGORICAL_EXTRA",
                    f"criterion {criterion_id!r} maps bucket(s) {extra} that the metric never produces",
                    location=where,
                )
            )
        _check_scores(mapping.values(), criterion, findings, where, criterion_id)
        return

    if rule_type == "bands":
        _check_bands(rule, criterion, findings, where, criterion_id)
        return

    # bands_by_variant
    variant_metric = rule.get("variant_metric")
    if variant_metric not in REGISTRY:
        findings.append(
            _err(
                "CONFIG_METRIC_UNIMPLEMENTED",
                f"criterion {criterion_id!r} uses variant metric {variant_metric!r}, which is not implemented",
                location=where,
            )
        )
    variants = rule.get("variants")
    if not isinstance(variants, Mapping) or not variants:
        findings.append(_err("CONFIG_VARIANTS_EMPTY", f"criterion {criterion_id!r} has no variants", location=where))
        return
    expected = CATEGORICAL_DOMAIN.get(str(variant_metric))
    if expected is not None:
        missing_variants = sorted(expected - set(variants.keys()))
        if missing_variants:
            findings.append(
                _err(
                    "CONFIG_VARIANTS_INCOMPLETE",
                    f"criterion {criterion_id!r} has no band table for variant(s) {missing_variants}",
                    location=where,
                )
            )
    for variant_name, table in variants.items():
        _check_bands(table, criterion, findings, f"{where}.variants.{variant_name}", criterion_id)


def _check_bands(
    table: Mapping[str, Any],
    criterion: Mapping[str, Any],
    findings: List[Finding],
    where: str,
    criterion_id: Any,
) -> None:
    bands = table.get("bands")
    if not isinstance(bands, list) or not bands:
        findings.append(_err("CONFIG_BANDS_EMPTY", f"criterion {criterion_id!r} has no bands", location=where))
        return
    for index, band in enumerate(bands):
        if not isinstance(band, list) or len(band) != 3:
            findings.append(
                _err(
                    "CONFIG_BAND_SHAPE",
                    f"criterion {criterion_id!r} band {index} must be [operator, value, score]",
                    location=f"{where}.bands[{index}]",
                )
            )
            continue
        operator, _value, score = band
        if operator not in VALID_OPERATORS or operator == "in":
            findings.append(
                _err(
                    "CONFIG_OPERATOR_INVALID",
                    f"criterion {criterion_id!r} band {index} uses operator {operator!r}, which is not "
                    "valid for a numeric band",
                    location=f"{where}.bands[{index}]",
                )
            )
        if not isinstance(score, (int, float)):
            findings.append(
                _err(
                    "CONFIG_BAND_SCORE",
                    f"criterion {criterion_id!r} band {index} score must be numeric",
                    location=f"{where}.bands[{index}]",
                )
            )
    if "else" not in table:
        findings.append(
            _err("CONFIG_BANDS_NO_ELSE", f"criterion {criterion_id!r} has no 'else' score", location=where)
        )
    else:
        _check_scores([table["else"]], criterion, findings, where, criterion_id)
    _check_scores([b[2] for b in bands if isinstance(b, list) and len(b) == 3], criterion, findings, where, criterion_id)


def _check_scores(
    scores: Sequence[Any],
    criterion: Mapping[str, Any],
    findings: List[Finding],
    where: str,
    criterion_id: Any,
) -> None:
    maximum = criterion.get("max")
    if not isinstance(maximum, (int, float)):
        return
    for score in scores:
        if not isinstance(score, (int, float)):
            continue
        if score > maximum:
            findings.append(
                _err(
                    "CONFIG_SCORE_EXCEEDS_MAX",
                    f"criterion {criterion_id!r} awards {score} which exceeds its max of {maximum}",
                    location=where,
                )
            )
        if score < 0 and criterion.get("kind") != "penalty":
            findings.append(
                _err(
                    "CONFIG_NEGATIVE_SCORE",
                    f"criterion {criterion_id!r} awards a negative score {score} without kind=penalty",
                    location=where,
                )
            )


def _module_max(module_id: str, criteria: Sequence[Mapping[str, Any]]) -> float:
    return float(sum(c.get("max", 0) for c in criteria if c.get("kind") != "penalty"))


def _effective_criteria(
    config: Mapping[str, Any],
    module_id: str,
    sector_overlay: Optional[str],
    structure_overlays: Sequence[str],
) -> List[Mapping[str, Any]]:
    """Resolve the criteria that would apply for a given overlay combination."""
    base = {c["id"]: c for m in config.get("modules", []) if m["id"] == module_id for c in m.get("criteria", [])}

    removed: Set[str] = set()
    added: List[Mapping[str, Any]] = []
    overrides: Dict[str, str] = {}

    if sector_overlay and sector_overlay != "standard":
        overlay = (config.get("sector_overlays") or {}).get(sector_overlay)
        if overlay:
            removed |= set(overlay.get("remove", []) or [])
            added.extend(c for c in overlay.get("add", []) or [] if c.get("module") == module_id)
            overrides.update(overlay.get("metric_override", {}) or {})
    for name in structure_overlays:
        overlay = (config.get("structure_overlays") or {}).get(name)
        if overlay:
            removed |= set(overlay.get("remove", []) or [])
            added.extend(c for c in overlay.get("add", []) or [] if c.get("module") == module_id)

    result: List[Mapping[str, Any]] = []
    for criterion_id, criterion in base.items():
        if criterion_id in removed:
            continue
        if criterion_id in overrides:
            criterion = dict(criterion)
            criterion["metric"] = overrides[criterion_id]
        result.append(criterion)
    result.extend(added)
    return result


def check_config(config: Mapping[str, Any]) -> ConfigCheck:
    """Run every configuration assertion and collect the findings."""
    findings: List[Finding] = []
    plans: Dict[str, Dict[str, Any]] = {}

    for key in ("config_version", "spec_version", "modules", "verdict", "knockouts"):
        if key not in config:
            findings.append(_err("CONFIG_MISSING_KEY", f"configuration has no {key!r}", location=key))

    modules = config.get("modules", [])
    if not modules:
        findings.append(_err("CONFIG_NO_MODULES", "configuration defines no modules"))
        return ConfigCheck(findings=findings, profile_plans=plans)

    declared_total = float((config.get("validation") or {}).get("assert_total", 100))

    # (1) criterion belongs to exactly one module.
    seen: Dict[str, str] = {}
    for module in modules:
        for criterion in module.get("criteria", []):
            criterion_id = criterion.get("id")
            if criterion_id in seen:
                findings.append(
                    _err(
                        "CONFIG_DUPLICATE_CRITERION",
                        f"criterion {criterion_id!r} appears in modules {seen[criterion_id]!r} and "
                        f"{module['id']!r}; it must belong to exactly one module",
                        location=f"modules.{module['id']}",
                    )
                )
            seen[criterion_id] = module["id"]

    base_criteria = _all_criteria(config)
    for overlay_name, criterion in _overlay_additions(config):
        criterion_id = criterion.get("id")
        if criterion_id in base_criteria:
            findings.append(
                _err(
                    "CONFIG_OVERLAY_ADD_EXISTING",
                    f"overlay {overlay_name!r} adds criterion {criterion_id!r} which already exists in "
                    f"module {base_criteria[criterion_id][0]!r}",
                    location=overlay_name,
                )
            )

    is_v1_6 = str(config.get("config_version", "")).startswith("1.6")

    # (2) base module maxima reconcile.
    module_maxima: Dict[str, float] = {}
    for module in modules:
        criteria = module.get("criteria", [])
        computed = _module_max(module["id"], criteria)
        declared_mod_max = float(module.get("max", 0))
        module_maxima[module["id"]] = declared_mod_max if is_v1_6 else computed
        if not is_v1_6 and abs(computed - declared_mod_max) > 1e-9:
            findings.append(
                _err(
                    "CONFIG_MODULE_MAX_MISMATCH",
                    f"module {module['id']!r} declares max {module.get('max')} but its criteria sum to "
                    f"{computed}",
                    location=f"modules.{module['id']}",
                )
            )
        for criterion in criteria:
            check_criterion(criterion, findings, f"modules.{module['id']}.{criterion.get('id')}")

    # (3) total = 100.
    total = sum(module_maxima.values())
    if abs(total - declared_total) > 1e-9:
        findings.append(
            _err(
                "CONFIG_TOTAL_MISMATCH",
                f"module maxima sum to {total}, but the configuration asserts a total of {declared_total}",
            )
        )

    # (4) overlay additions are individually valid.
    for overlay_name, criterion in _overlay_additions(config):
        check_criterion(criterion, findings, f"{overlay_name}.{criterion.get('id')}")
        module_id = criterion.get("module")
        if module_id not in module_maxima:
            findings.append(
                _err(
                    "CONFIG_OVERLAY_UNKNOWN_MODULE",
                    f"overlay {overlay_name!r} adds criterion {criterion.get('id')!r} to unknown module "
                    f"{module_id!r}",
                    location=overlay_name,
                )
            )

    # (5) overlay replacements reconcile, per profile and structure combination.
    structure_names = sorted((config.get("structure_overlays") or {}).keys())
    structure_combos: List[Tuple[str, ...]] = [()]
    structure_combos.extend((name,) for name in structure_names)

    profiles = sorted(VALID_PROFILES)
    for profile in profiles:
        for combo in structure_combos:
            key = profile if not combo else f"{profile}+{'+'.join(combo)}"
            plan_modules: Dict[str, float] = {}
            for module in modules:
                module_id = module["id"]
                effective = _effective_criteria(config, module_id, profile, combo)
                computed = _module_max(module_id, effective)
                if is_v1_6:
                    base_criteria_sum = _module_max(module_id, module.get("criteria", []))
                    if abs(computed - base_criteria_sum) > 1e-9:
                        findings.append(
                            _err(
                                "CONFIG_OVERLAY_RECONCILE",
                                f"profile {key!r}: module {module_id!r} totals {computed} after overlays but "
                                f"base criteria total {base_criteria_sum}; overlay criteria do not reconcile",
                                location=f"profile:{key}",
                            )
                        )
                    plan_modules[module_id] = float(module.get("max", 0))
                else:
                    plan_modules[module_id] = computed
                    if abs(computed - float(module.get("max", 0))) > 1e-9:
                        findings.append(
                            _err(
                                "CONFIG_OVERLAY_RECONCILE",
                                f"profile {key!r}: module {module_id!r} totals {computed} after overlays but "
                                f"must remain {module.get('max')}; removed and added maxima do not reconcile",
                                location=f"profile:{key}",
                            )
                        )
            plan_total = sum(plan_modules.values())
            if abs(plan_total - declared_total) > 1e-9:
                findings.append(
                    _err(
                        "CONFIG_OVERLAY_TOTAL",
                        f"profile {key!r}: effective criteria total {plan_total}, expected {declared_total}",
                        location=f"profile:{key}",
                    )
                )
            plans[key] = {"module_maxima": plan_modules, "total": plan_total}

    # (6) overlay removals reference criteria that actually exist.
    for overlay_group, key_name in (("sector_overlays", "remove"), ("structure_overlays", "remove")):
        for name, overlay in (config.get(overlay_group) or {}).items():
            for criterion_id in overlay.get(key_name, []) or []:
                if criterion_id not in base_criteria:
                    findings.append(
                        _err(
                            "CONFIG_OVERLAY_REMOVE_UNKNOWN",
                            f"overlay {overlay_group}.{name!r} removes unknown criterion {criterion_id!r}",
                            location=f"{overlay_group}.{name}",
                        )
                    )

    # (7) metric_override targets exist.
    for name, overlay in (config.get("sector_overlays") or {}).items():
        for criterion_id, metric_id in (overlay.get("metric_override") or {}).items():
            if criterion_id not in base_criteria:
                findings.append(
                    _err(
                        "CONFIG_METRIC_OVERRIDE_UNKNOWN_CRITERION",
                        f"overlay {name!r} overrides metric for unknown criterion {criterion_id!r}",
                        location=f"sector_overlays.{name}",
                    )
                )
            if metric_id not in REGISTRY:
                findings.append(
                    _err(
                        "CONFIG_METRIC_UNIMPLEMENTED",
                        f"overlay {name!r} maps criterion {criterion_id!r} to unimplemented metric "
                        f"{metric_id!r}; the engine must fail rather than silently score zero",
                        location=f"sector_overlays.{name}",
                    )
                )

    # (8) knockouts: tri-state requires each rule to declare its inputs, and
    # every referenced metric must exist.
    for knockout in config.get("knockouts", []):
        knockout_id = knockout.get("id", "<missing-id>")
        where = f"knockouts.{knockout_id}"
        if "when" not in knockout:
            findings.append(_err("CONFIG_KNOCKOUT_NO_WHEN", f"knockout {knockout_id!r} has no expression", location=where))
        else:
            check_expression(knockout["when"], findings, f"{where}.when")
        if not knockout.get("required"):
            findings.append(
                _warn(
                    "CONFIG_KNOCKOUT_NO_REQUIRED",
                    f"knockout {knockout_id!r} does not declare the inputs required to clear it; "
                    "UNVERIFIED will still be reported for unknown leaves",
                    location=where,
                )
            )

    # (9) penalties.
    for penalty in (config.get("penalties") or {}).get("items", []):
        where = f"penalties.{penalty.get('id')}"
        if "when" in penalty:
            check_expression(penalty["when"], findings, f"{where}.when")
        elif "metric" in penalty:
            if penalty["metric"] not in REGISTRY:
                findings.append(
                    _err(
                        "CONFIG_METRIC_UNIMPLEMENTED",
                        f"penalty {penalty.get('id')!r} uses unimplemented metric {penalty['metric']!r}",
                        location=where,
                    )
                )
        else:
            findings.append(_err("CONFIG_PENALTY_NO_WHEN", f"penalty {penalty.get('id')!r} has no trigger", location=where))

    # (10) caps.
    for cap in config.get("caps", []) or []:
        if "when" in cap:
            check_expression(cap["when"], findings, f"caps.{cap.get('id')}")

    # (11) verdict bands must be ordered and the fallback present.
    bands = (config.get("verdict") or {}).get("bands") or []
    if not bands:
        findings.append(_err("CONFIG_VERDICT_NO_BANDS", "no verdict bands defined"))
    mins = [b.get("min") for b in bands]
    if mins != sorted(mins, reverse=True):
        findings.append(_err("CONFIG_VERDICT_BANDS_UNORDERED", "verdict bands must descend by min"))
    if not (config.get("verdict") or {}).get("else"):
        findings.append(_err("CONFIG_VERDICT_NO_ELSE", "verdict has no fallback band"))

    # (12) confidence weighting must be points-based (spec s11/s18).
    confidence = config.get("confidence") or {}
    if confidence.get("weighting", "POINTS") != "POINTS":
        findings.append(
            _err(
                "CONFIG_CONFIDENCE_WEIGHTING",
                "confidence must be weighted by scoring points, not by the count of populated "
                "criteria (spec s11/s18)",
                location="confidence",
            )
        )

    # (13) critical data items must map to implemented metrics or known flags.
    for item in (config.get("critical_data") or {}).get("items", []):
        if item not in REGISTRY:
            findings.append(
                _err(
                    "CONFIG_CRITICAL_DATA_UNKNOWN",
                    f"critical_data references {item!r}, which is not an implemented metric",
                    location="critical_data",
                )
            )

    # (14) derived_metrics registry must agree with the implementation.
    declared = config.get("derived_metrics") or {}
    for metric_id, spec in declared.items():
        if spec.get("implemented") and metric_id not in REGISTRY:
            findings.append(
                _err(
                    "CONFIG_METRIC_DECLARED_NOT_IMPLEMENTED",
                    f"configuration declares metric {metric_id!r} as implemented, but the engine has "
                    "no implementation for it",
                    location=f"derived_metrics.{metric_id}",
                )
            )

    # (15) modes must reference real criteria, and the exclusion set must be
    # consistent with the tri-state range calculation.
    for mode_name, mode in (config.get("modes") or {}).items():
        for criterion_id in mode.get("exclude", []) or []:
            if criterion_id not in base_criteria and criterion_id not in {
                c.get("id") for _, c in _overlay_additions(config)
            }:
                findings.append(
                    _err(
                        "CONFIG_MODE_EXCLUDE_UNKNOWN",
                        f"mode {mode_name!r} excludes unknown criterion {criterion_id!r}",
                        location=f"modes.{mode_name}",
                    )
                )

    # (16) v1.6 provenance and lifecycle assertions.
    if is_v1_6:
        for pkey in ("parent_config_version", "parent_config_hash", "source_proposal_hash"):
            if not config.get(pkey):
                findings.append(
                    _err(
                        "CONFIG_MISSING_PROVENANCE",
                        f"v1.6 configuration missing required provenance field {pkey!r}",
                        location=pkey,
                    )
                )
        if config.get("is_active") is not False:
            findings.append(
                _err(
                    "CONFIG_ACTIVE_STATE_VIOLATION",
                    "v1.6 configuration must have 'is_active: false'",
                    location="is_active",
                )
            )
        if config.get("status") not in ("IMPLEMENTED_INACTIVE", "DRAFT_INACTIVE"):
            findings.append(
                _err(
                    "CONFIG_STATUS_INVALID",
                    f"v1.6 configuration status must be inactive, got {config.get('status')!r}",
                    location="status",
                )
            )

    return ConfigCheck(findings=findings, profile_plans=plans)


def compile_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate the configuration and return it with a compiled fingerprint.

    Raises :class:`ConfigValidationError` when any assertion fails, which is
    what makes configuration validity a hard gate (spec s3.5, s20).
    """
    check = check_config(config)
    if not check.ok:
        raise ConfigValidationError(check.findings)
    compiled = dict(config)
    compiled["_fingerprint"] = config_fingerprint(config)
    compiled["_validation"] = check.to_dict()
    return compiled


def config_fingerprint(config: Mapping[str, Any]) -> str:
    """Stable hash of the executable policy.

    Only the policy is hashed; runtime annotations (``_fingerprint`` and
    ``_validation``) are excluded so that the fingerprint is stable across
    repeated compilations.
    """
    payload = {
        k: v
        for k, v in config.items()
        if k not in ("_fingerprint", "_validation")
    }
    return sha256_of(payload)


__all__ = [
    "VALID_OPERATORS",
    "VALID_RULE_TYPES",
    "VALID_PROFILES",
    "CATEGORICAL_DOMAIN",
    "ConfigCheck",
    "check_config",
    "compile_config",
    "config_fingerprint",
    "check_criterion",
    "check_expression",
]
