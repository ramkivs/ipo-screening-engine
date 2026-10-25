"""Build the canonical input snapshot from a raw input document.

Spec v1.5 s4 requires a canonical input model with evidence and provenance
present *before* scoring, and s5 requires that the raw value, raw unit,
normalised value, normalisation formula, source reference and verification
status are all preserved.

The raw document is the shape defined by ``schema/ipo-input.v1.5.schema.json``.
It may carry two optional blocks that the reference prototypes did not have:

``_sources``
    A list of source identities (``source_id``, ``source_type``, ``uri``,
    ``content_hash``, timestamps).

``_evidence``
    A mapping from JSON path (for example
    ``financials.periods[2].revenue``) to an evidence object
    (``evidence_id``, ``source_id``, ``locator``, ``page``, ``section``,
    ``quote``, ``extraction_method``).

Neither block is required by the schema, but a material scored input without
resolvable evidence is reported as a provenance finding so the gate decisions
stay visible instead of implicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .canonical import (
    Evidence,
    EvidenceRegistry,
    ExtractionMethod,
    SourceRef,
    SourceType,
    UNIT_TO_CRORE,
    Value,
    unit_factor,
)
from .errors import Finding, SEVERITY_WARNING


@dataclass
class FinancialPeriod:
    """One restated financial observation, normalised to INR crore."""

    fy: str
    is_stub: bool
    raw: Mapping[str, Any]
    values: Dict[str, Optional[float]] = field(default_factory=dict)

    def get(self, name: str) -> Optional[float]:
        return self.values.get(name)


MONETARY_FIELDS: Tuple[str, ...] = (
    "revenue",
    "ebitda",
    "ebit",
    "pat",
    "pbt",
    "tax",
    "net_worth",
    "total_debt",
    "interest_expense",
    "finance_cost",
    "depreciation",
    "other_income",
    "cfo",
    "capex",
    "cash_and_equivalents",
    "trade_receivables",
    "inventory",
    "order_book",
    "pre_sales",
    "collections",
)

RATIO_FIELDS: Tuple[str, ...] = (
    "receivable_days",
    "disclosed_roce_pct",
    "contribution_margin_pct",
    "operating_loss_pct_revenue",
    "nim_pct",
    "cost_to_income_pct",
    "gnpa_pct",
    "nnpa_pct",
    "provision_coverage_pct",
    "crar_pct",
    "tier1_pct",
    "roa_pct",
    "roe_pct",
)


@dataclass
class CanonicalInput:
    """Canonicalised input plus the evidence that supports it."""

    raw: Mapping[str, Any]
    ipo_id: str
    company_name: str
    board: str
    icdr_route: str
    sector_profile: str
    reporting_unit: str
    unit_factor: float
    periods: Tuple[FinancialPeriod, ...]
    registry: EvidenceRegistry
    findings: List[Finding] = field(default_factory=list)

    # -- convenience accessors -------------------------------------------

    @property
    def full_periods(self) -> Tuple[FinancialPeriod, ...]:
        """Non-stub observations, oldest first (spec s4.2)."""
        return tuple(p for p in self.periods if not p.is_stub)

    @property
    def latest(self) -> Optional[FinancialPeriod]:
        full = self.full_periods
        return full[-1] if full else None

    @property
    def earliest(self) -> Optional[FinancialPeriod]:
        full = self.full_periods
        return full[0] if full else None

    def issue(self) -> Mapping[str, Any]:
        return self.raw.get("issue", {}) or {}

    def capital_structure(self) -> Mapping[str, Any]:
        return self.raw.get("capital_structure", {}) or {}

    def governance(self) -> Mapping[str, Any]:
        return self.raw.get("governance", {}) or {}

    def business(self) -> Mapping[str, Any]:
        return self.raw.get("business", {}) or {}

    def financials(self) -> Mapping[str, Any]:
        return self.raw.get("financials", {}) or {}

    def market(self) -> Mapping[str, Any]:
        return self.raw.get("market", {}) or {}

    def peers(self) -> Sequence[Mapping[str, Any]]:
        return self.raw.get("peers", []) or []

    def use_of_proceeds(self) -> Sequence[Mapping[str, Any]]:
        return self.raw.get("use_of_proceeds", []) or []

    def money(self, section: str, key: str) -> Optional[float]:
        """Read a monetary value from a top-level section, in INR crore."""
        container = self.raw.get(section) or {}
        return _scale(container.get(key), self.unit_factor)

    def money_in(self, container: Mapping[str, Any], key: str) -> Optional[float]:
        return _scale(container.get(key), self.unit_factor)

    def number(self, section: str, key: str) -> Optional[float]:
        container = self.raw.get(section) or {}
        return _as_float(container.get(key))

    def flag(self, section: str, key: str) -> Optional[bool]:
        """Read a boolean flag, preserving "not supplied" as ``None``.

        Spec s16: a missing knockout input must never be treated as CLEAR,
        so an absent flag is ``None`` (unknown) rather than ``False``.
        """
        container = self.raw.get(section) or {}
        if key not in container:
            return None
        value = container.get(key)
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        return None

    def evidence_for(self, path: str) -> Optional[str]:
        """Return the evidence_id registered for a JSON path, if any."""
        return self._evidence_index.get(path)

    def to_snapshot_dict(self) -> Dict[str, Any]:
        """Canonical, hashable snapshot of everything that was scored."""
        from .hashing import canonical_json  # local import avoids a cycle

        return {
            "ipo_id": self.ipo_id,
            "company_name": self.company_name,
            "board": self.board,
            "icdr_route": self.icdr_route,
            "sector_profile": self.sector_profile,
            "reporting_unit": self.reporting_unit,
            "unit_factor": self.unit_factor,
            "periods": [
                {
                    "fy": p.fy,
                    "is_stub": p.is_stub,
                    "reporting_unit": self.reporting_unit,
                    **{k: v for k, v in sorted(p.values.items()) if v is not None},
                }
                for p in self.periods
            ],
            "input": _strip_private(self.raw),
            "snapshot_grammar": canonical_json({"v": 1}),
        }

    _evidence_index: Dict[str, str] = field(default_factory=dict)


def _as_float(raw: Any) -> Optional[float]:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def _scale(raw: Any, factor: float) -> Optional[float]:
    value = _as_float(raw)
    return None if value is None else value * factor


def _strip_private(raw: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def build_registry(raw: Mapping[str, Any]) -> Tuple[EvidenceRegistry, Dict[str, str], List[Finding]]:
    """Register sources and evidence declared in the input document."""
    registry = EvidenceRegistry()
    findings: List[Finding] = []
    index: Dict[str, str] = {}

    for source in raw.get("_sources", []) or []:
        registry.add_source(
            SourceRef(
                source_id=source["source_id"],
                source_type=source.get("source_type", SourceType.STRUCTURED_INPUT.value),
                uri=source.get("uri"),
                content_hash=source.get("content_hash"),
                retrieval_timestamp=source.get("retrieval_timestamp"),
                source_timestamp=source.get("source_timestamp"),
            )
        )

    for path, spec in (raw.get("_evidence", {}) or {}).items():
        source_id = spec.get("source_id")
        if source_id not in {s.source_id for s in registry.sources}:
            findings.append(
                Finding(
                    code="EVIDENCE_SOURCE_UNREGISTERED",
                    message=(
                        f"evidence for {path!r} references source {source_id!r} "
                        "which is not declared in _sources"
                    ),
                    severity=SEVERITY_WARNING,
                    scope="evidence",
                    location=path,
                )
            )
            continue
        evidence_id = spec.get("evidence_id") or f"EV-{path}"
        registry.add_evidence(
            Evidence(
                evidence_id=evidence_id,
                source_id=source_id,
                locator=spec.get("locator", ""),
                quoted_text=spec.get("quote") if spec.get("quote") is not None else spec.get("quoted_text"),
                extraction_method=spec.get("extraction_method", ExtractionMethod.MANUAL_ENTRY.value),
                extraction_confidence=spec.get("extraction_confidence"),
                page=spec.get("page"),
                section=spec.get("section"),
                as_of=spec.get("as_of"),
                note=spec.get("note"),
                page_note=spec.get("page_note"),
            )
        )
        index[path] = evidence_id

    return registry, index, findings


def _walk_paths(raw: Mapping[str, Any]) -> List[str]:
    """Enumerate leaf JSON paths in a stable order (for provenance checks)."""
    paths: List[str] = []

    def walk(node: Any, prefix: str) -> None:
        if isinstance(node, Mapping):
            for key in node:
                if str(key).startswith("_"):
                    continue
                walk(node[key], f"{prefix}.{key}" if prefix else str(key))
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{prefix}[{i}]")
        else:
            paths.append(prefix)

    walk(raw, "")
    return paths


def build_canonical_input(raw: Mapping[str, Any]) -> CanonicalInput:
    """Canonicalise a raw input document.

    Monetary values in ``financials.periods`` and in the offer/proceeds
    sections are converted to INR crore using the declared reporting unit.
    Absent values become ``None`` and are surfaced as UNKNOWN by the derived
    metrics engine - they are never coerced to ``0``.
    """
    registry, index, findings = build_registry(raw)

    financials = raw.get("financials", {}) or {}
    reporting_unit = financials.get("reporting_unit", "INR_CRORES")
    factor = UNIT_TO_CRORE.get(reporting_unit)
    if factor is None:
        factor = unit_factor(reporting_unit)  # raises UnitError for unknown units

    periods: List[FinancialPeriod] = []
    for period_raw in financials.get("periods", []) or []:
        values: Dict[str, Optional[float]] = {}
        for name in MONETARY_FIELDS:
            values[name] = _scale(period_raw.get(name), factor)
        for name in RATIO_FIELDS:
            values[name] = _as_float(period_raw.get(name))
        periods.append(
            FinancialPeriod(
                fy=str(period_raw.get("fy", "")),
                is_stub=bool(period_raw.get("is_stub", False)),
                raw=period_raw,
                values=values,
            )
        )

    canonical = CanonicalInput(
        raw=raw,
        ipo_id=str(raw.get("ipo_id", "")),
        company_name=str(raw.get("company_name", "")),
        board=str(raw.get("board", "mainboard")),
        icdr_route=str(raw.get("icdr_route", "6(1)")),
        sector_profile=str(raw.get("sector_profile", "standard")),
        reporting_unit=str(reporting_unit),
        unit_factor=factor,
        periods=tuple(periods),
        registry=registry,
        findings=findings,
    )
    canonical._evidence_index = index
    return canonical


def unprovenanced_paths(canonical: CanonicalInput) -> List[str]:
    """Leaf paths in the raw input with no evidence reference.

    Used by the provenance validator. Paths under ``_``-prefixed keys are
    ignored, since those *are* the provenance blocks.
    """
    return [p for p in _walk_paths(canonical.raw) if p not in canonical._evidence_index]


__all__ = [
    "CanonicalInput",
    "FinancialPeriod",
    "MONETARY_FIELDS",
    "RATIO_FIELDS",
    "build_canonical_input",
    "build_registry",
    "unprovenanced_paths",
]
