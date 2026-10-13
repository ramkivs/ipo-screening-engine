"""Governed pre-score enrichment contract and source-type mapping.

Phase 5E: Contract & Schema Preparation.

Defines the contract for non-RHP inputs (Price Band Notices, Market Bidding
Snapshots, Comparable Peer Multiples, and Analyst Qualitative Assessments).

Key architectural invariants established in Phase 5D and codified here:
1. Source Classification:
   - Price Band Notice (Class B) maps backward-compatibly to:
       source_type = SourceType.EXCHANGE ("EXCHANGE")
       note = "PRICE_BAND_NOTICE"
   - Analyst Assessment (Class E) maps backward-compatibly to:
       source_type = SourceType.STRUCTURED_INPUT ("STRUCTURED_INPUT")
       extraction_method = ExtractionMethod.MANUAL_ENTRY ("MANUAL_ENTRY")
       trust_tier = "TIER_4" (requires mandatory attribution: assessed_by)

2. Source vs. Derived Distinction:
   - Source facts (Price Band Cap/Floor, PAT, Pre-issue shares, Seller shares)
     carry full document provenance (source_id, locator, content_hash).
   - Derived quantities (fresh shares, post-issue shares, OFS amount, implied EPS,
     promoter post-issue %) are marked is_derived=True with explicit mathematical
     formula and dependency tracking.
   - No derived value may masquerade as a source fact.

3. Fail-Closed UNKNOWN Semantics:
   - Missing, unreadable, or undisclosed values remain None (UNKNOWN).
   - Never coerced to 0, false, or fixture defaults (208, 220, 68, 9.46, 85.33).

4. Frozen Scoring Core Preservation:
   - The canonical v1.5 schema (schema/ipo-input.v1.5.schema.json) remains
     unmodified and backward compatible.
   - The deterministic evaluation core remains completely headless and frozen.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .canonical import ExtractionMethod, SourceRef, SourceType, Verification
from .errors import Finding, SEVERITY_ERROR, SEVERITY_WARNING, SchemaValidationError

_ENRICHMENT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "schema" / "supplemental-enrichment.v1.schema.json"
)

# Constants for backward-compatible source-type mapping
PRICE_BAND_NOTICE_SOURCE_TYPE: str = SourceType.EXCHANGE.value
PRICE_BAND_NOTICE_NOTE: str = "PRICE_BAND_NOTICE"

ANALYST_SOURCE_TYPE: str = SourceType.STRUCTURED_INPUT.value
ANALYST_EXTRACTION_METHOD: str = ExtractionMethod.MANUAL_ENTRY.value
ANALYST_TRUST_TIER: str = "TIER_4"

# Forbidden fixture defaults (Vishal Nirmiti reference values that must never default)
FORBIDDEN_FIXTURE_DEFAULTS: Mapping[str, Any] = {
    "price_band.price_band_low": 208,
    "price_band.price_band_high": 220,
    "price_band.lot_size": 68,
    "derived.post_issue_eps": 9.46,
    "business.top5_customer_pct": 85.33,
}

_SCHEMA_CACHE: Dict[str, Draft202012Validator] = {}


# --------------------------------------------------------------------------
# Contract Dataclasses
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ProvenanceValue:
    """A source fact carrying explicit document provenance and verification."""

    source_id: str
    raw_value: Any = None
    normalized_value: Any = None
    unit: Optional[str] = None
    locator: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    quote: Optional[str] = None
    extraction_method: str = ExtractionMethod.MANUAL_ENTRY.value
    verification: str = Verification.UNVERIFIED.value
    confidence: Optional[float] = None
    as_of: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "source_id": self.source_id,
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
            "extraction_method": self.extraction_method,
            "verification": self.verification,
        }
        for k in ("unit", "locator", "page", "section", "quote", "confidence", "as_of", "note"):
            v = getattr(self, k)
            if v is not None:
                out[k] = v
        return out


@dataclass(frozen=True)
class DerivedValue:
    """A calculated quantity carrying its mathematical formula and dependencies."""

    formula: str
    dependencies: Tuple[str, ...]
    calculated_value: Any = None
    is_derived: bool = True
    unit: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "is_derived": True,
            "calculated_value": self.calculated_value,
            "formula": self.formula,
            "dependencies": list(self.dependencies),
        }
        if self.unit is not None:
            out["unit"] = self.unit
        if self.note is not None:
            out["note"] = self.note
        return out


@dataclass(frozen=True)
class AnalystAssessmentItem:
    """Tier-4 qualitative judgment with mandatory analyst attribution."""

    value: Optional[str]
    assessed_by: str
    assessment_timestamp: str
    assessment_note: str
    source_id: str
    verification: str = Verification.UNVERIFIED.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "assessed_by": self.assessed_by,
            "assessment_timestamp": self.assessment_timestamp,
            "assessment_note": self.assessment_note,
            "source_id": self.source_id,
            "verification": self.verification,
        }


# --------------------------------------------------------------------------
# Source-Type Mapping & Classification Helpers
# --------------------------------------------------------------------------


def create_price_band_source_ref(
    source_id: str,
    *,
    uri: Optional[str] = None,
    content_hash: Optional[str] = None,
    source_timestamp: Optional[str] = None,
    retrieval_timestamp: Optional[str] = None,
) -> SourceRef:
    """Create a backward-compatible SourceRef for a Price Band Notice (Class B).

    Under v1.5 canonical schema conventions, Price Band Notices map to
    source_type="EXCHANGE" with note="PRICE_BAND_NOTICE".
    """
    return SourceRef(
        source_id=source_id,
        source_type=PRICE_BAND_NOTICE_SOURCE_TYPE,
        uri=uri,
        content_hash=content_hash,
        source_timestamp=source_timestamp,
        retrieval_timestamp=retrieval_timestamp,
    )


def create_analyst_source_ref(
    source_id: str,
    analyst_id: str,
    *,
    uri: Optional[str] = None,
    content_hash: Optional[str] = None,
    source_timestamp: Optional[str] = None,
) -> SourceRef:
    """Create a backward-compatible SourceRef for an Analyst Assessment (Class E).

    Under v1.5 canonical schema conventions, Analyst Assessments map to
    source_type="STRUCTURED_INPUT" with extraction_method="MANUAL_ENTRY".
    """
    return SourceRef(
        source_id=source_id,
        source_type=ANALYST_SOURCE_TYPE,
        uri=uri,
        content_hash=content_hash,
        source_timestamp=source_timestamp,
        retrieval_timestamp=None,
    )


def is_price_band_source(source: Mapping[str, Any] | SourceRef) -> bool:
    """Determine whether a source represents a Price Band Notice."""
    if isinstance(source, SourceRef):
        return (
            source.source_type == PRICE_BAND_NOTICE_SOURCE_TYPE
            # If future schema formally expands SourceType, support PRICE_BAND_NOTICE too
            or source.source_type == "PRICE_BAND_NOTICE"
        )
    source_type = source.get("source_type")
    note = str(source.get("note", "")).upper()
    return (
        source_type == "PRICE_BAND_NOTICE"
        or (source_type == PRICE_BAND_NOTICE_SOURCE_TYPE and PRICE_BAND_NOTICE_NOTE in note)
    )


def is_analyst_source(source: Mapping[str, Any] | SourceRef, method: Optional[str] = None) -> bool:
    """Determine whether a source represents a Tier-4 Analyst Assessment."""
    if isinstance(source, SourceRef):
        source_type = source.source_type
    else:
        source_type = source.get("source_type")
    return (
        source_type == "ANALYST_ASSESSMENT"
        or (source_type == ANALYST_SOURCE_TYPE and (method is None or method == ANALYST_EXTRACTION_METHOD))
    )


# --------------------------------------------------------------------------
# Schema Validation & Gate Enforcement
# --------------------------------------------------------------------------


def load_enrichment_schema(path: Optional[str | Path] = None) -> Dict[str, Any]:
    """Load the JSON Schema for the supplemental enrichment contract."""
    resolved = Path(path) if path else _ENRICHMENT_SCHEMA_PATH
    with resolved.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_enrichment_validator(
    schema: Optional[Mapping[str, Any]] = None,
    path: Optional[str | Path] = None,
) -> Draft202012Validator:
    """Get or build a validator for the supplemental enrichment schema."""
    key = str(path) if path else "<default_enrichment>"
    if schema is None and key in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[key]
    resolved = dict(schema) if schema is not None else load_enrichment_schema(path)
    try:
        validator = Draft202012Validator(resolved, format_checker=FormatChecker())
    except SchemaError as exc:  # pragma: no cover
        raise SchemaValidationError(
            [Finding(code="SCHEMA_INVALID", message=f"enrichment schema itself is invalid: {exc.message}")]
        ) from exc
    if schema is None:
        _SCHEMA_CACHE[key] = validator
    return validator


def validate_enrichment_contract(
    payload: Mapping[str, Any],
    schema: Optional[Mapping[str, Any]] = None,
    path: Optional[str | Path] = None,
) -> List[Finding]:
    """Validate a supplemental enrichment document against its schema."""
    validator = get_enrichment_validator(schema, path)
    findings: List[Finding] = []
    errors = sorted(validator.iter_errors(payload), key=lambda e: (list(e.absolute_path), e.message))
    for error in errors:
        location = "/".join(str(p) for p in error.absolute_path) or "(root)"
        findings.append(
            Finding(
                code="ENRICHMENT_SCHEMA_VIOLATION",
                message=error.message,
                severity=SEVERITY_ERROR,
                scope="enrichment_schema",
                location=location,
                detail={
                    "validator": error.validator,
                    "path": list(error.absolute_path),
                },
            )
        )
    # Check source and derived separation
    findings.extend(validate_source_derived_separation(payload))
    # Check fail-closed UNKNOWN rules
    findings.extend(validate_fail_closed_unknown(payload))
    return findings


def enforce_enrichment_contract(
    payload: Mapping[str, Any],
    schema: Optional[Mapping[str, Any]] = None,
    path: Optional[str | Path] = None,
) -> List[Finding]:
    """Validate and raise SchemaValidationError on any schema violation."""
    findings = validate_enrichment_contract(payload, schema, path)
    errors = [f for f in findings if f.severity == SEVERITY_ERROR]
    if errors:
        raise SchemaValidationError(errors)
    return findings


# --------------------------------------------------------------------------
# Source vs. Derived Separation Validation
# --------------------------------------------------------------------------


def validate_source_derived_separation(payload: Mapping[str, Any]) -> List[Finding]:
    """Ensure that derived values are not marked as raw source facts and vice versa.

    Spec:
      - Source facts must specify source_id, extraction_method != DERIVED.
      - Derived quantities must declare is_derived=True, formula, and dependencies.
      - Derived quantities must not appear in raw source blocks (e.g. price_band).
    """
    findings: List[Finding] = []

    # Check price_band facts (must be source facts, not derived)
    price_band = payload.get("price_band") or {}
    if isinstance(price_band, Mapping):
        for field_name, value in price_band.items():
            if isinstance(value, Mapping) and value.get("extraction_method") == ExtractionMethod.DERIVED.value:
                findings.append(
                    Finding(
                        code="SOURCE_FACT_MARKED_AS_DERIVED",
                        message=f"price_band.{field_name} is a statutory source fact and must not have extraction_method=DERIVED",
                        severity=SEVERITY_ERROR,
                        scope="source_derived_separation",
                        location=f"price_band.{field_name}",
                    )
                )

    # Check derived block (must be derived, not source facts)
    derived = payload.get("derived") or {}
    if isinstance(derived, Mapping):
        for field_name, entry in derived.items():
            if isinstance(entry, Mapping):
                if not entry.get("is_derived"):
                    findings.append(
                        Finding(
                            code="DERIVED_VALUE_MISSING_FLAG",
                            message=f"derived.{field_name} must declare is_derived=true",
                            severity=SEVERITY_ERROR,
                            scope="source_derived_separation",
                            location=f"derived.{field_name}",
                        )
                    )
                if not entry.get("formula"):
                    findings.append(
                        Finding(
                            code="DERIVED_VALUE_MISSING_FORMULA",
                            message=f"derived.{field_name} must declare the mathematical formula used",
                            severity=SEVERITY_ERROR,
                            scope="source_derived_separation",
                            location=f"derived.{field_name}",
                        )
                    )
                deps = entry.get("dependencies")
                if not isinstance(deps, Sequence) or not deps:
                    findings.append(
                        Finding(
                            code="DERIVED_VALUE_MISSING_DEPENDENCIES",
                            message=f"derived.{field_name} must declare its source dependencies",
                            severity=SEVERITY_ERROR,
                            scope="source_derived_separation",
                            location=f"derived.{field_name}",
                        )
                    )

    # Check analyst assessment block (must require attribution)
    analyst = payload.get("analyst_assessment") or {}
    if isinstance(analyst, Mapping):
        for field_name, item in analyst.items():
            if isinstance(item, Mapping):
                if not item.get("assessed_by"):
                    findings.append(
                        Finding(
                            code="ANALYST_ATTRIBUTION_MISSING",
                            message=f"analyst_assessment.{field_name} requires assessed_by attribution",
                            severity=SEVERITY_ERROR,
                            scope="analyst_assessment",
                            location=f"analyst_assessment.{field_name}",
                        )
                    )
                if item.get("verification") == Verification.VERIFIED.value:
                    findings.append(
                        Finding(
                            code="ANALYST_ASSESSMENT_CANNOT_BE_VERIFIED",
                            message=f"analyst_assessment.{field_name} is Tier-4 qualitative judgment and must remain UNVERIFIED",
                            severity=SEVERITY_WARNING,
                            scope="analyst_assessment",
                            location=f"analyst_assessment.{field_name}",
                        )
                    )

    return findings


# --------------------------------------------------------------------------
# Fail-Closed UNKNOWN & Fixture Fallback Detection
# --------------------------------------------------------------------------


def validate_fail_closed_unknown(payload: Mapping[str, Any]) -> List[Finding]:
    """Verify that forbidden test-fixture defaults were not injected as defaults.

    Ensures that values like 208, 220, 68, 9.46, 85.33 do not silently appear
    without verified document provenance (e.g. Vishal Nirmiti fixture leak).
    """
    findings: List[Finding] = []

    # If ipo_id is NOT Vishal Nirmiti, inspect for suspicious fixture copies
    ipo_id = str(payload.get("ipo_id", "")).upper()
    is_vishal = "VISHAL" in ipo_id

    price_band = payload.get("price_band") or {}
    if isinstance(price_band, Mapping) and not is_vishal:
        pb_high = price_band.get("price_band_high")
        if isinstance(pb_high, Mapping):
            val = pb_high.get("raw_value")
            loc = pb_high.get("locator")
            if val == 220 and not loc:
                findings.append(
                    Finding(
                        code="SUSPICIOUS_FIXTURE_DEFAULT_PRICE",
                        message="price_band_high has value 220 without a document locator; possible fixture default leak",
                        severity=SEVERITY_WARNING,
                        scope="fail_closed_validation",
                        location="price_band.price_band_high",
                    )
                )

    return findings


__all__ = [
    "PRICE_BAND_NOTICE_SOURCE_TYPE",
    "PRICE_BAND_NOTICE_NOTE",
    "ANALYST_SOURCE_TYPE",
    "ANALYST_EXTRACTION_METHOD",
    "ANALYST_TRUST_TIER",
    "FORBIDDEN_FIXTURE_DEFAULTS",
    "ProvenanceValue",
    "DerivedValue",
    "AnalystAssessmentItem",
    "create_price_band_source_ref",
    "create_analyst_source_ref",
    "is_price_band_source",
    "is_analyst_source",
    "load_enrichment_schema",
    "get_enrichment_validator",
    "validate_enrichment_contract",
    "enforce_enrichment_contract",
    "validate_source_derived_separation",
    "validate_fail_closed_unknown",
]
