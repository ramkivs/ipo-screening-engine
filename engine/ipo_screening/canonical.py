"""Canonical input model, tri-state value semantics and the evidence model.

Spec v1.5 references:
  * s3.2  "Unknown is not zero" - every input and derived metric is VALUE,
          UNKNOWN or NOT_APPLICABLE; ``0`` is a numeric value, not a marker.
  * s3.4  "Evidence before score" - every material input carries source,
          as-of date, document/page reference, extraction method and
          verification status.
  * s5    Data model - raw value, raw unit, normalized value, normalization
          formula, source reference and verification status are all preserved.
  * tech design s3.3 - canonical values carry unit, period, source_ref and
          evidence_ref alongside status.

The two status axes are deliberately orthogonal:

``state``         VALUE | UNKNOWN | NOT_APPLICABLE   (is there a value?)
``verification``  VERIFIED | UNVERIFIED              (how was it established?)

A value may be present but UNVERIFIED (for example LLM-extracted and not yet
checked) - tech design s15 requires such a value to stay UNVERIFIED until
validation and evidence checks pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .hashing import canonical_json, sha256_of


class State(str, Enum):
    """Whether a canonical value exists (spec s3.2)."""

    VALUE = "VALUE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Verification(str, Enum):
    """How a canonical value was established (tech design s3.3)."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class ExtractionMethod(str, Enum):
    """Provenance of an extracted value (tech design s3.2)."""

    MANUAL_ENTRY = "MANUAL_ENTRY"
    STRUCTURED_INPUT = "STRUCTURED_INPUT"
    DETERMINISTIC_PDF = "DETERMINISTIC_PDF"
    TABLE_EXTRACTION = "TABLE_EXTRACTION"
    OCR = "OCR"
    LLM_ASSISTED = "LLM_ASSISTED"
    DERIVED = "DERIVED"
    EXCHANGE_DATA = "EXCHANGE_DATA"
    MARKET_DATA = "MARKET_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SourceType(str, Enum):
    RHP = "RHP"
    DRHP = "DRHP"
    EXCHANGE = "EXCHANGE"
    MARKET_DATA = "MARKET_DATA"
    PEER_DATA = "PEER_DATA"
    STRUCTURED_INPUT = "STRUCTURED_INPUT"
    DERIVED = "DERIVED"


# --------------------------------------------------------------------------
# Unit handling
# --------------------------------------------------------------------------

#: Multiplicative factor converting a unit into the engine currency (INR crore).
UNIT_TO_CRORE: Dict[str, float] = {
    "INR_CRORES": 1.0,
    "INR_LAKHS": 0.01,
    "INR_MILLIONS": 0.1,
    "INR_BILLIONS": 100.0,
}


class UnitError(ValueError):
    """An unrecognised or missing monetary unit.

    Spec s20 requires that currency units be known; an unknown unit is a
    validation failure, never an implicit factor of 1.
    """


def unit_factor(unit: Optional[str]) -> float:
    if unit is None:
        raise UnitError("monetary unit is missing; cannot normalise")
    try:
        return UNIT_TO_CRORE[unit]
    except KeyError as exc:  # pragma: no cover - guarded by schema too
        raise UnitError(f"unknown monetary unit {unit!r}") from exc


# --------------------------------------------------------------------------
# Evidence / provenance
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceRef:
    """Identity of a source document or feed (tech design s3.1)."""

    source_id: str
    source_type: str
    uri: Optional[str] = None
    content_hash: Optional[str] = None
    retrieval_timestamp: Optional[str] = None
    source_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"source_id": self.source_id, "source_type": self.source_type}
        for key in ("uri", "content_hash", "retrieval_timestamp", "source_timestamp"):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        return out

    def is_traceable(self) -> bool:
        return bool(self.source_id and self.source_type)


@dataclass(frozen=True)
class Evidence:
    """A pointer to the material that establishes a value (spec s3.4).

    ``locator`` is human-checkable: a page number, a table name, a section
    heading or a URL fragment. It is what lets the engine answer "which
    page/table supplied it?" (spec s24).
    """

    evidence_id: str
    source_id: str
    locator: str
    quoted_text: Optional[str] = None
    extraction_method: str = ExtractionMethod.MANUAL_ENTRY.value
    extraction_confidence: Optional[float] = None
    page: Optional[int] = None
    section: Optional[str] = None
    as_of: Optional[str] = None
    note: Optional[str] = None
    page_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "locator": self.locator,
            "extraction_method": self.extraction_method,
        }
        for key in ("quoted_text", "page", "section", "as_of", "note", "page_note"):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        if self.extraction_confidence is not None:
            out["extraction_confidence"] = self.extraction_confidence
        return out


# --------------------------------------------------------------------------
# Canonical value
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Value:
    """A canonical, provenance-carrying value (spec s5).

    Construct one of these with :meth:`verified`, :meth:`unverified`,
    :meth:`unknown` or :meth:`not_applicable`. There is deliberately no
    constructor that accepts a missing argument and quietly yields ``0``.
    """

    state: str
    value: Optional[float] = None
    unit: Optional[str] = None
    period: Optional[str] = None
    raw_value: Optional[float] = None
    raw_unit: Optional[str] = None
    normalization: Optional[str] = None
    source_ref: Optional[SourceRef] = None
    evidence_ref: Optional[str] = None
    verification: Optional[str] = None
    note: Optional[str] = None

    # -- constructors ------------------------------------------------------

    @staticmethod
    def verified(
        value: float,
        *,
        unit: str,
        source_ref: SourceRef,
        evidence_ref: str,
        period: Optional[str] = None,
        raw_value: Optional[float] = None,
        raw_unit: Optional[str] = None,
        normalization: Optional[str] = None,
        note: Optional[str] = None,
    ) -> "Value":
        return Value(
            state=State.VALUE.value,
            value=value,
            unit=unit,
            period=period,
            raw_value=raw_value,
            raw_unit=raw_unit,
            normalization=normalization,
            source_ref=source_ref,
            evidence_ref=evidence_ref,
            verification=Verification.VERIFIED.value,
            note=note,
        )

    @staticmethod
    def unverified(
        value: float,
        *,
        unit: str,
        source_ref: SourceRef,
        evidence_ref: Optional[str] = None,
        period: Optional[str] = None,
        normalization: Optional[str] = None,
        note: Optional[str] = None,
    ) -> "Value":
        return Value(
            state=State.VALUE.value,
            value=value,
            unit=unit,
            period=period,
            normalization=normalization,
            source_ref=source_ref,
            evidence_ref=evidence_ref,
            verification=Verification.UNVERIFIED.value,
            note=note,
        )

    @staticmethod
    def unknown(*, note: Optional[str] = None, period: Optional[str] = None) -> "Value":
        return Value(state=State.UNKNOWN.value, period=period, note=note)

    @staticmethod
    def not_applicable(*, note: Optional[str] = None, period: Optional[str] = None) -> "Value":
        return Value(state=State.NOT_APPLICABLE.value, period=period, note=note)

    # -- queries -----------------------------------------------------------

    @property
    def is_value(self) -> bool:
        return self.state == State.VALUE.value

    @property
    def is_unknown(self) -> bool:
        return self.state == State.UNKNOWN.value

    @property
    def is_not_applicable(self) -> bool:
        return self.state == State.NOT_APPLICABLE.value

    def as_float(self) -> Optional[float]:
        """Numeric value, or ``None`` when the state is not VALUE.

        Callers must branch on the state rather than relying on ``None``
        meaning zero.
        """
        return self.value if self.is_value else None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"state": self.state}
        if self.value is not None:
            out["value"] = self.value
        if self.unit is not None:
            out["unit"] = self.unit
        if self.period is not None:
            out["period"] = self.period
        if self.raw_value is not None:
            out["raw_value"] = self.raw_value
        if self.raw_unit is not None:
            out["raw_unit"] = self.raw_unit
        if self.normalization is not None:
            out["normalization"] = self.normalization
        if self.source_ref is not None:
            out["source"] = self.source_ref.to_dict()
        if self.evidence_ref is not None:
            out["evidence_ref"] = self.evidence_ref
        if self.verification is not None:
            out["verification"] = self.verification
        if self.note is not None:
            out["note"] = self.note
        return out


# --------------------------------------------------------------------------
# Evidence registry
# --------------------------------------------------------------------------


class EvidenceRegistry:
    """Collects :class:`SourceRef` and :class:`Evidence` objects for a run.

    Guarantees that every ``evidence_ref`` attached to a :class:`Value`
    resolves, which is what makes "every material scored input is traceable"
    (spec s3.4) checkable rather than aspirational.
    """

    def __init__(self) -> None:
        self._sources: Dict[str, SourceRef] = {}
        self._evidence: Dict[str, Evidence] = {}

    def add_source(self, source: SourceRef) -> SourceRef:
        existing = self._sources.get(source.source_id)
        if existing is not None and existing != source:
            raise ValueError(
                f"source_id {source.source_id!r} registered twice with different metadata"
            )
        self._sources[source.source_id] = source
        return source

    def add_evidence(self, evidence: Evidence) -> Evidence:
        if evidence.source_id not in self._sources:
            raise ValueError(
                f"evidence {evidence.evidence_id!r} references unregistered source "
                f"{evidence.source_id!r}"
            )
        existing = self._evidence.get(evidence.evidence_id)
        if existing is not None and existing != evidence:
            raise ValueError(
                f"evidence_id {evidence.evidence_id!r} registered twice with different content"
            )
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    def source(self, source_id: str) -> SourceRef:
        return self._sources[source_id]

    def evidence(self, evidence_id: str) -> Evidence:
        return self._evidence[evidence_id]

    def has_evidence(self, evidence_id: str) -> bool:
        return evidence_id in self._evidence

    @property
    def sources(self) -> Sequence[SourceRef]:
        return [self._sources[k] for k in sorted(self._sources)]

    @property
    def evidence_items(self) -> Sequence[Evidence]:
        return [self._evidence[k] for k in sorted(self._evidence)]

    def manifest_hash(self) -> str:
        """Stable hash of the whole source manifest (spec s21)."""
        return sha256_of(
            {
                "sources": [s.to_dict() for s in self.sources],
                "evidence": [e.to_dict() for e in self.evidence_items],
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sources": [s.to_dict() for s in self.sources],
            "evidence": [e.to_dict() for e in self.evidence_items],
            "manifest_hash": self.manifest_hash(),
        }


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def optional_value(raw: Any, *, unit: str, factor: float) -> Value:
    """Convert a possibly-absent raw number into a canonical :class:`Value`.

    ``None`` yields ``UNKNOWN`` - never ``0``. This is the single choke point
    that enforces spec s3.2 across the canonicaliser.
    """
    if raw is None:
        return Value.unknown()
    if isinstance(raw, str):
        raise UnitError(f"expected a number, got the string {raw!r}; strings are not implicit numbers")
    value = float(raw) * factor
    return Value(
        state=State.VALUE.value,
        value=value,
        unit=unit,
        raw_value=float(raw),
        raw_unit=unit,
        normalization=f"{raw} {unit} x {factor} -> {value} INR_CRORES",
    )


def utc_now_iso() -> str:
    """Current UTC timestamp in a stable, sortable form."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


__all__ = [
    "State",
    "Verification",
    "ExtractionMethod",
    "SourceType",
    "UNIT_TO_CRORE",
    "UnitError",
    "unit_factor",
    "SourceRef",
    "Evidence",
    "Value",
    "EvidenceRegistry",
    "optional_value",
    "utc_now_iso",
    "parse_date",
    "parse_datetime",
    "canonical_json",
]
