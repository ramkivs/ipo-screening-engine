"""Tri-state knockout engine.

Spec v1.5 s3.3: every knockout resolves to TRIGGERED, CLEAR or UNVERIFIED, and
UNVERIFIED must identify the missing evidence/inputs. "A missing knockout
input must never be treated as CLEAR."

Spec v1.5 s16 retains K1-K6 but requires tri-state evaluation.

The reference prototype computed ``triggered: cond(when)`` with ordinary
two-valued logic, so an absent input (``undefined``) evaluated to falsy and the
knockout silently reported CLEAR. The technical design gives the intended
replacement behaviour explicitly:

    {"rule_id": "K1", "state": "UNVERIFIED",
     "missing": ["going_concern_uncertainty"],
     "explanation": "The supplied input does not establish whether
                     going-concern uncertainty exists."}

This module implements the rule tree over Kleene three-valued logic (TRUE /
FALSE / UNKNOWN) so that:

  * a decisive TRUE always wins - a knockout is triggered even if other
    leaves are unknown;
  * an ``all`` node with any FALSE child is decisively FALSE (and therefore
    CLEAR), because that single counter-example settles the conjunction;
  * otherwise an UNKNOWN child makes the node UNKNOWN, never FALSE.

Knockout evaluation is independent of scoring: it reads the same derived
metrics but never the score, so a knockout finding can be audited on its own
(spec s9 "Knockout evaluation must be independently auditable").
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .derived import DerivedMetrics

STATE_TRIGGERED = "TRIGGERED"
STATE_CLEAR = "CLEAR"
STATE_UNVERIFIED = "UNVERIFIED"

_TRUTH_NAMES = {True: "TRUE", False: "FALSE", None: "UNKNOWN"}


class Truth(enum.Enum):
    """Kleene three-valued truth."""

    TRUE = True
    FALSE = False
    UNKNOWN = None

    def __bool__(self) -> bool:  # pragma: no cover - guards accidental use
        raise TypeError(
            "Truth must be compared explicitly; a three-valued result has no truthiness"
        )


def k_not(value: Truth) -> Truth:
    if value is Truth.UNKNOWN:
        return Truth.UNKNOWN
    return Truth.FALSE if value is Truth.TRUE else Truth.TRUE


def k_and(values: Sequence[Truth]) -> Truth:
    """Kleene AND: FALSE if any FALSE; else UNKNOWN if any UNKNOWN; else TRUE."""
    result = Truth.TRUE
    for value in values:
        if value is Truth.FALSE:
            return Truth.FALSE
        if value is Truth.UNKNOWN:
            result = Truth.UNKNOWN
    return result


def k_or(values: Sequence[Truth]) -> Truth:
    """Kleene OR: TRUE if any TRUE; else UNKNOWN if any UNKNOWN; else FALSE."""
    result = Truth.FALSE
    for value in values:
        if value is Truth.TRUE:
            return Truth.TRUE
        if value is Truth.UNKNOWN:
            result = Truth.UNKNOWN
    return result


@dataclass
class LeafTrace:
    kind: str  # metric | flag
    reference: str
    truth: str
    detail: str
    value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "reference": self.reference,
            "truth": self.truth,
            "detail": self.detail,
            **({"value": self.value} if self.value is not None else {}),
        }


@dataclass
class KnockoutResult:
    """Outcome of one knockout rule, independently auditable."""

    rule_id: str
    label: str
    state: str
    missing: Tuple[str, ...]
    explanation: str
    leaves: Tuple[LeafTrace, ...] = ()
    required: Tuple[str, ...] = ()

    @property
    def triggered(self) -> bool:
        return self.state == STATE_TRIGGERED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "label": self.label,
            "state": self.state,
            "missing": list(self.missing),
            "explanation": self.explanation,
            "required": list(self.required),
            "leaves": [leaf.to_dict() for leaf in self.leaves],
        }


def _compare(value: Any, operator: str, target: Any) -> bool:
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


def evaluate_expression(
    expr: Mapping[str, Any],
    derived: DerivedMetrics,
    leaves: List[LeafTrace],
) -> Truth:
    """Evaluate a knockout expression over Kleene three-valued logic."""
    if "all" in expr:
        return k_and([evaluate_expression(child, derived, leaves) for child in expr["all"]])
    if "any" in expr:
        return k_or([evaluate_expression(child, derived, leaves) for child in expr["any"]])
    if "not" in expr:
        return k_not(evaluate_expression(expr["not"], derived, leaves))

    if "flag" in expr:
        reference = str(expr["flag"])
        item = derived.metrics.get(reference)
        if item is None:
            leaves.append(
                LeafTrace(
                    kind="flag",
                    reference=reference,
                    truth="UNKNOWN",
                    detail=f"flag {reference!r} is not an implemented metric",
                )
            )
            return Truth.UNKNOWN
        if item.is_unknown:
            leaves.append(
                LeafTrace(
                    kind="flag",
                    reference=reference,
                    truth="UNKNOWN",
                    detail=(
                        item.reason
                        or f"the supplied input does not establish {reference!r}"
                    ),
                )
            )
            return Truth.UNKNOWN
        if item.is_not_applicable:
            leaves.append(
                LeafTrace(
                    kind="flag",
                    reference=reference,
                    truth="UNKNOWN",
                    detail=item.reason or f"{reference!r} is not applicable, so it cannot clear the rule",
                )
            )
            return Truth.UNKNOWN
        truth = Truth.TRUE if item.value is True else Truth.FALSE
        leaves.append(
            LeafTrace(
                kind="flag",
                reference=reference,
                truth=truth.name,
                detail=f"{reference} = {item.value!r}",
                value=item.value,
            )
        )
        return truth

    reference = str(expr.get("metric"))
    operator = expr.get("op")
    target = expr.get("value")
    item = derived.metrics.get(reference)
    if item is None:
        leaves.append(
            LeafTrace(
                kind="metric",
                reference=reference,
                truth="UNKNOWN",
                detail=f"metric {reference!r} is not implemented, so the rule cannot be evaluated",
            )
        )
        return Truth.UNKNOWN
    if not item.is_value:
        leaves.append(
            LeafTrace(
                kind="metric",
                reference=reference,
                truth="UNKNOWN",
                detail=item.reason or f"{reference!r} is {item.state}",
            )
        )
        return Truth.UNKNOWN
    result = _compare(item.value, operator, target)
    leaves.append(
        LeafTrace(
            kind="metric",
            reference=reference,
            truth=(Truth.TRUE if result else Truth.FALSE).name,
            detail=f"{reference} = {item.value!r} {operator} {target!r} -> {result}",
            value=item.value,
        )
    )
    return Truth.TRUE if result else Truth.FALSE


def evaluate_knockouts(
    config: Mapping[str, Any],
    derived: DerivedMetrics,
) -> Tuple[KnockoutResult, ...]:
    """Evaluate every configured knockout rule in declaration order."""
    results: List[KnockoutResult] = []
    for rule in config.get("knockouts", []):
        rule_id = str(rule["id"])
        label = str(rule.get("label", rule_id))
        required = tuple(rule.get("required", []) or [])
        leaves: List[LeafTrace] = []
        truth = evaluate_expression(rule["when"], derived, leaves)

        if truth is Truth.TRUE:
            state = STATE_TRIGGERED
            missing: Tuple[str, ...] = ()
            explanation = "The knockout condition is satisfied by the supplied inputs."
        elif truth is Truth.FALSE:
            state = STATE_CLEAR
            missing = ()
            explanation = (
                "Every condition in the rule has been evaluated against supplied inputs and none "
                "is met."
            )
        else:
            state = STATE_UNVERIFIED
            blocked = sorted({leaf.reference for leaf in leaves if leaf.truth == "UNKNOWN"})
            missing = tuple(blocked)
            explanation = _unverified_explanation(blocked, leaves)

        results.append(
            KnockoutResult(
                rule_id=rule_id,
                label=label,
                state=state,
                missing=missing,
                explanation=explanation,
                leaves=tuple(leaves),
                required=required,
            )
        )
    return tuple(results)


def _unverified_explanation(blocked: Sequence[str], leaves: Sequence[LeafTrace]) -> str:
    if not blocked:
        return "The rule could not be resolved to CLEAR or TRIGGERED."
    if len(blocked) == 1:
        reference = blocked[0]
        detail = next((l.detail for l in leaves if l.reference == reference and l.truth == "UNKNOWN"), "")
        return (
            f"The supplied input does not establish whether {reference} applies"
            + (f": {detail}." if detail and detail != reference else ".")
        )
    return (
        "The supplied input does not establish {}".format(", ".join(blocked))
        + "; the rule cannot be cleared or triggered on the available evidence."
    )


@dataclass
class KnockoutSummary:
    results: Tuple[KnockoutResult, ...]

    @property
    def triggered(self) -> Tuple[KnockoutResult, ...]:
        return tuple(r for r in self.results if r.state == STATE_TRIGGERED)

    @property
    def clear(self) -> Tuple[KnockoutResult, ...]:
        return tuple(r for r in self.results if r.state == STATE_CLEAR)

    @property
    def unverified(self) -> Tuple[KnockoutResult, ...]:
        return tuple(r for r in self.results if r.state == STATE_UNVERIFIED)

    @property
    def any_triggered(self) -> bool:
        return bool(self.triggered)

    @property
    def all_clear(self) -> bool:
        return not self.triggered and not self.unverified

    @property
    def status(self) -> str:
        """Headline status: TRIGGERED dominates, then UNVERIFIED, then CLEAR."""
        if self.triggered:
            return STATE_TRIGGERED
        if self.unverified:
            return STATE_UNVERIFIED
        return STATE_CLEAR

    def completeness_pct(self) -> float:
        """Share of knockout rules that resolved to CLEAR or TRIGGERED."""
        if not self.results:
            return 100.0
        resolved = len(self.clear) + len(self.triggered)
        return resolved / len(self.results) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "any_triggered": self.any_triggered,
            "all_clear": self.all_clear,
            "completeness_pct": round(self.completeness_pct(), 6),
            "results": [r.to_dict() for r in self.results],
        }


__all__ = [
    "STATE_TRIGGERED",
    "STATE_CLEAR",
    "STATE_UNVERIFIED",
    "Truth",
    "k_and",
    "k_or",
    "k_not",
    "LeafTrace",
    "KnockoutResult",
    "KnockoutSummary",
    "evaluate_expression",
    "evaluate_knockouts",
]
