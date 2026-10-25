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


def validate_peer_records(
    peers: Any,
    schema: Optional[Mapping[str, Any]] = None,
) -> List[Finding]:
    """Validate the canonical ``peers`` array against the input schema, early.

    The full document gate runs at evaluation time
    (:func:`ipo_screening.pipeline.evaluate` -> ``enforce_schema``), but peer
    rows enter the canonical input at ingestion time -- before issue terms
    exist. Out-of-contract peer values have therefore historically surfaced
    only at evaluation time as an anonymous wall (audit trace
    ing-81fd285e5b8248c6: ``SCHEMA_VIOLATION at peers/0/roe_pct: 26957.28 is
    greater than maximum 10000``). This runs the SAME schema definition over
    the peers array at ingestion and term-submission time and names the peer
    and field so the diagnostic is actionable. Values are never clamped or
    substituted; the bounds are exactly the schema's.
    """
    resolved = dict(load_schema()) if schema is None else dict(schema)
    peers_schema = dict(resolved.get("properties", {}).get("peers") or {"type": "array"})
    if "$defs" in resolved:
        peers_schema.setdefault("$defs", resolved["$defs"])
    validator = get_validator(peers_schema)
    document = [] if peers is None else peers
    findings: List[Finding] = []
    errors = sorted(validator.iter_errors(document), key=lambda e: (list(e.absolute_path), e.message))
    for error in errors:
        loc = list(error.absolute_path)
        location = "peers" + "".join(f"/{part}" for part in loc)
        name = None
        if loc and isinstance(document, list):
            try:
                row = document[loc[0]]
                name = row.get("name") if isinstance(row, Mapping) else None
            except (IndexError, TypeError, AttributeError):
                name = None
        prefix = f"peer {name!r} " if name else ""
        findings.append(
            Finding(
                code="SCHEMA_VIOLATION",
                message=f"{prefix}{error.message}",
                severity=SEVERITY_ERROR,
                scope="schema",
                location=location,
                detail={
                    "validator": error.validator,
                    "path": loc,
                    "schema_path": list(error.absolute_schema_path),
                    "peer_name": name,
                },
            )
        )
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
    "validate_peer_records",
    "validate_input_schema_path",
]
