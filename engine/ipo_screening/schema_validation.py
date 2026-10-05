"""Structural validation via JSON Schema - a hard gate.

Spec v1.5 s20: "Use actual JSON Schema validation. Invalid types, missing
required fields and malformed structures stop scoring."

The reference prototype's ``check()`` only asserted that four top-level keys
existed. v1.5 requires the schema in ``schema/ipo-input.v1.5.schema.json`` to
be enforced in full, including formats (so a numeric string where a number is
required is rejected rather than coerced).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .errors import Finding, SEVERITY_ERROR, SchemaValidationError

_DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "ipo-input.v1.5.schema.json"

_CACHE: Dict[str, Draft202012Validator] = {}


def load_schema(path: Optional[str] = None) -> Dict[str, Any]:
    schema_path = Path(path) if path else _DEFAULT_SCHEMA_PATH
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_validator(schema: Optional[Mapping[str, Any]] = None, path: Optional[str] = None) -> Draft202012Validator:
    key = path or "<default>"
    if schema is None and key in _CACHE:
        return _CACHE[key]
    resolved = dict(schema) if schema is not None else load_schema(path)
    try:
        validator = Draft202012Validator(resolved, format_checker=FormatChecker())
    except SchemaError as exc:  # pragma: no cover - a broken schema is a build error
        raise SchemaValidationError(
            [Finding(code="SCHEMA_INVALID", message=f"the JSON Schema itself is invalid: {exc.message}")]
        ) from exc
    if schema is None:
        _CACHE[key] = validator
    return validator


def validate_schema(
    document: Mapping[str, Any],
    schema: Optional[Mapping[str, Any]] = None,
    path: Optional[str] = None,
) -> List[Finding]:
    """Return findings for every schema violation, ordered deterministically."""
    validator = get_validator(schema, path)
    findings: List[Finding] = []
    errors = sorted(validator.iter_errors(document), key=lambda e: (list(e.absolute_path), e.message))
    for error in errors:
        location = "/".join(str(p) for p in error.absolute_path) or "(root)"
        findings.append(
            Finding(
                code="SCHEMA_VIOLATION",
                message=error.message,
                severity=SEVERITY_ERROR,
                scope="schema",
                location=location,
                detail={
                    "validator": error.validator,
                    "path": list(error.absolute_path),
                    "schema_path": list(error.absolute_schema_path),
                },
            )
        )
    return findings


def enforce_schema(
    document: Mapping[str, Any],
    schema: Optional[Mapping[str, Any]] = None,
    path: Optional[str] = None,
) -> List[Finding]:
    """Validate and raise :class:`SchemaValidationError` on any violation."""
    findings = validate_schema(document, schema, path)
    if findings:
        raise SchemaValidationError(findings)
    return findings


def validate_input_schema_path(path: str) -> None:
    """Validate a candidate input file against the schema, for CLI use."""
    with Path(path).open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    enforce_schema(document)


__all__ = [
    "load_schema",
    "get_validator",
    "validate_schema",
    "enforce_schema",
    "validate_input_schema_path",
]
