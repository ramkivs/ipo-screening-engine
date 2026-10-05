"""Exception types and validation finding records.

v1.5 treats validation as a hard gate (spec s20, s3.5): schema, semantic and
configuration failures stop scoring rather than degrading quietly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

SEVERITY_ERROR = "ERROR"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"


@dataclass(frozen=True)
class Finding:
    """A single validation finding.

    Findings are persisted with the evaluation record so that the reason a
    run was accepted or rejected is auditable (spec s20, s24).
    """

    code: str
    message: str
    severity: str = SEVERITY_ERROR
    scope: str = "generic"
    location: Optional[str] = None
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "scope": self.scope,
            "message": self.message,
        }
        if self.location:
            out["location"] = self.location
        if self.detail:
            out["detail"] = self.detail
        return out


class EngineError(Exception):
    """Base class for all engine errors."""


class ValidationError(EngineError):
    """Raised when a hard validation gate fails.

    Carries the structured findings so that callers can persist them instead
    of a bare string.
    """

    def __init__(self, gate: str, findings: List[Finding]):
        self.gate = gate
        self.findings = list(findings)
        errors = [f for f in self.findings if f.severity == SEVERITY_ERROR]
        preview = "; ".join(f"{f.code}: {f.message}" for f in errors[:5])
        if len(errors) > 5:
            preview += f"; ... ({len(errors) - 5} more)"
        super().__init__(f"{gate} validation failed: {preview}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "errors": [f.to_dict() for f in self.findings if f.severity == SEVERITY_ERROR],
            "warnings": [f.to_dict() for f in self.findings if f.severity == SEVERITY_WARNING],
        }


class SchemaValidationError(ValidationError):
    """JSON Schema validation failed (spec s20 'Schema')."""

    def __init__(self, findings: List[Finding]):
        super().__init__("schema", findings)


class SemanticValidationError(ValidationError):
    """Semantic / financial / cross-source validation failed (spec s20)."""

    def __init__(self, findings: List[Finding]):
        super().__init__("semantic", findings)


class ConfigValidationError(ValidationError):
    """Configuration is not executable policy (spec s3.5, s14, s20)."""

    def __init__(self, findings: List[Finding]):
        super().__init__("config", findings)


class UnknownMetricError(EngineError):
    """A criterion or knockout referenced a metric that is not implemented.

    v1.5 s14: if an overlay is selected but one of its required metrics is
    not implemented, the engine must fail validation rather than silently
    score zero.
    """


class ImmutabilityError(EngineError):
    """An attempt was made to overwrite an existing evaluation record.

    v1.5 s21, tech design s13: never overwrite a prior evaluation.
    """


__all__ = [
    "Finding",
    "SEVERITY_ERROR",
    "SEVERITY_WARNING",
    "SEVERITY_INFO",
    "EngineError",
    "ValidationError",
    "SchemaValidationError",
    "SemanticValidationError",
    "ConfigValidationError",
    "UnknownMetricError",
    "ImmutabilityError",
]
