"""End-to-end evaluation pipeline.

Implements the required architecture (spec s6.1, tech design s2):

    Sources
      -> Extraction
      -> Canonical Input + Evidence
      -> Validation (schema, semantic, config)
      -> Derived Metrics
      -> Sector / Structure Overlay Resolver
      -> Knockout Engine
      -> Deterministic Scorer
      -> Confidence / Range / Verdict
      -> Immutable Evaluation Record
      -> Excel Projection
      -> Post-listing / Backtest

Each stage is a separate module; the pipeline only sequences them. Validation
gates are hard: an invalid configuration or an invalid input stops the run
before any score is produced (spec s3.5, s20).

The pipeline is deterministic: given the same input document, the same
configuration and the same engine version, it produces the same
``result_hash`` (spec s19 acceptance test).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import excel as excel_module
from .canonical import SourceType, Verification, parse_datetime
from .canonical_input import CanonicalInput, build_canonical_input
from .config_validation import compile_config, config_fingerprint
from .derived import DerivedMetrics, derive
from .errors import Finding, SEVERITY_ERROR, ValidationError
from .evaluation import (
    EvaluationRecord,
    EvaluationStore,
    build_record,
    compute_preliminary_delta,
)
from .knockouts import KnockoutSummary, evaluate_knockouts
from .overlays import EffectiveScoringPlan, resolve_overlays
from .schema_validation import enforce_schema, load_schema
from .scoring import ScoreResult, score
from .semantic_validation import ValidationReport, validate_semantics
from .snapshots import MARKET_FRESH, MarketSnapshot, build_market_snapshot, classify_peers
from .version import DEFAULT_CONFIG_PATH, ENGINE_VERSION, SPEC_VERSION

DEFAULT_MARKET_STALENESS_HOURS = 24


@dataclass
class EvaluationOutcome:
    """Everything a caller needs after a run."""

    record: EvaluationRecord
    score: ScoreResult
    knockouts: KnockoutSummary
    plan: EffectiveScoringPlan
    derived: DerivedMetrics
    validation: ValidationReport
    canonical: CanonicalInput
    stored_at: Optional[Path] = None
    workbook_path: Optional[Path] = None

    # -- reporting helpers -------------------------------------------------

    def top_strengths(self, limit: int = 3) -> List[Dict[str, Any]]:
        scored = [
            c
            for m in self.score.modules
            for c in m.criteria
            if c.state == "SCORED" and not c.is_penalty and c.score and c.max > 0
        ]
        scored.sort(key=lambda c: (-(c.score / c.max), -c.score, c.criterion_id))
        return [
            {
                "criterion_id": c.criterion_id,
                "label": c.label,
                "score": c.score,
                "max": c.max,
                "reason": c.reason,
            }
            for c in scored[:limit]
        ]

    def top_risks(self, limit: int = 3) -> List[Dict[str, Any]]:
        risks: List[Dict[str, Any]] = []
        for c in self.score.criteria:
            if c.is_penalty and c.score and c.score < 0:
                risks.append(
                    {
                        "kind": "PENALTY",
                        "id": c.criterion_id,
                        "label": c.label,
                        "impact": c.score,
                        "reason": c.reason,
                    }
                )
            elif c.state == "SCORED" and not c.is_penalty and c.max > 0 and (c.score or 0) == 0:
                risks.append(
                    {
                        "kind": "ZERO_SCORE",
                        "id": c.criterion_id,
                        "label": c.label,
                        "impact": 0,
                        "reason": c.reason,
                    }
                )
            elif c.state == "UNKNOWN":
                risks.append(
                    {
                        "kind": "UNKNOWN",
                        "id": c.criterion_id,
                        "label": c.label,
                        "impact": None,
                        "reason": c.reason,
                    }
                )
        order = {"PENALTY": 0, "ZERO_SCORE": 1, "UNKNOWN": 2}
        risks.sort(key=lambda r: (order.get(r["kind"], 9), r["id"]))
        return risks[:limit]

    def to_report(self) -> Dict[str, Any]:
        record = self.record
        return {
            "evaluation_id": record.evaluation_id,
            "ipo_id": record.ipo_id,
            "company_name": record.company_name,
            "mode": record.evaluation_mode,
            "evaluation_timestamp": record.evaluation_timestamp,
            "versions": {
                "engine": record.engine_version,
                "spec": record.spec_version,
                "config": record.config_version,
                "config_hash": record.config_hash,
            },
            "hashes": {
                "input_snapshot_hash": record.input_snapshot_hash,
                "source_manifest_hash": record.source_manifest_hash,
                "market_snapshot_hash": record.market_snapshot_hash,
                "peer_snapshot_hash": record.peer_snapshot_hash,
                "result_hash": record.result_hash,
            },
            "result": {
                "final_score": self.score.final_score,
                "base_score": self.score.base_score,
                "penalties_total": self.score.penalties_total,
                "lower_bound": self.score.lower_bound,
                "upper_bound": self.score.upper_bound,
                "verdict": self.score.verdict,
                "verdict_band_score": self.score.verdict_band_score,
                "verdict_uncertain": self.score.verdict_uncertain,
                "insufficient_data": self.score.insufficient_data,
                "confidence": self.score.confidence,
                "completeness_pct": round(self.score.completeness_pct, 2),
                "available_points": self.score.available_points,
                "unknown_points": self.score.unknown_points,
                "total_evaluable_points": self.score.total_evaluable_points,
            },
            "knockouts": {
                "status": self.knockouts.status,
                "triggered": [r.rule_id for r in self.knockouts.triggered],
                "unverified": [r.rule_id for r in self.knockouts.unverified],
                "clear": [r.rule_id for r in self.knockouts.clear],
            },
            "plan": self.plan.to_dict(),
            "module_scores": {
                m.module_id: {"score": m.score, "max": m.max} for m in self.score.modules
            },
            "top_strengths": self.top_strengths(),
            "top_risks": self.top_risks(),
            "validation": self.validation.to_dict(),
            "preliminary_delta": record.preliminary_delta,
            "excel_is_projection_not_truth": True,
        }


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    """Load and validate the executable policy (hard gate)."""
    resolved = Path(path) if path else Path(__file__).resolve().parents[2] / DEFAULT_CONFIG_PATH
    with resolved.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return compile_config(raw)


def validate_final_gmp_snapshot(
    canonical: CanonicalInput,
    market: MarketSnapshot,
    evaluation_datetime: Optional[datetime] = None,
) -> List[Finding]:
    """Return fail-closed GMP findings for the FINAL evaluation boundary.

    This validates generic snapshot identity, source-reference, timestamp,
    verification, freshness and hash integrity. It does not select or name a
    provider, invent an event/cutoff contract, or affect subscription data.
    """
    findings: List[Finding] = []

    def reject(code: str, message: str, location: str = "market.gmp") -> None:
        findings.append(
            Finding(
                code=code,
                message=message,
                severity=SEVERITY_ERROR,
                scope="final_gmp",
                location=location,
            )
        )

    raw_gmp = canonical.market().get("gmp")
    gmp_block = market.block("gmp")
    if not isinstance(raw_gmp, Mapping) or not raw_gmp:
        reject("GMP_SNAPSHOT_MISSING", "FINAL requires a GMP snapshot; no GMP block was supplied")
        return findings
    if gmp_block is None or gmp_block.status == "MISSING":
        reject("GMP_SNAPSHOT_MISSING", "FINAL requires a non-empty GMP market snapshot")
        return findings
    if gmp_block.status != MARKET_FRESH:
        reject(
            "GMP_SNAPSHOT_NOT_FRESH",
            f"GMP snapshot is {gmp_block.status}; it is not qualifying for FINAL"
            + (f": {gmp_block.reason}" if gmp_block.reason else ""),
        )

    values = gmp_block.values
    if values.get("freshness") != "FRESH":
        reject("GMP_FRESHNESS_UNVERIFIED", "GMP snapshot freshness is absent or not FRESH")
    if values.get("verification") != Verification.VERIFIED.value:
        reject("GMP_SNAPSHOT_UNVERIFIED", "GMP snapshot must be explicitly VERIFIED for FINAL")
    if values.get("is_statutory") is not False:
        reject("GMP_STATUTORY_FLAG_INVALID", "GMP must remain explicitly non-statutory")
    if values.get("trend") not in {"strong", "flat", "falling"}:
        reject("GMP_OBSERVATION_NONQUALIFYING", "GMP trend observation is missing or not a supported value")

    snapshot_id = values.get("snapshot_id")
    raw_payload = values.get("raw_payload")
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        reject("GMP_SNAPSHOT_ID_MISSING", "GMP snapshot identity is missing")
    if not isinstance(raw_payload, Mapping) or not raw_payload:
        reject("GMP_RAW_SNAPSHOT_MISSING", "GMP raw source snapshot is missing")
    elif raw_payload.get("snapshot_id") != snapshot_id:
        reject("GMP_SNAPSHOT_ID_MISMATCH", "GMP snapshot identity does not match the retained raw source snapshot")

    source_id = gmp_block.source_id
    if not source_id:
        reject("GMP_SOURCE_MISSING", "GMP snapshot source_id is missing")
        source_ref = None
    else:
        source_ref = next((ref for ref in canonical.registry.sources if ref.source_id == source_id), None)
        if source_ref is None:
            reject("GMP_SOURCE_UNREGISTERED", f"GMP source {source_id!r} is not registered in _sources")
        elif source_ref.source_type != SourceType.MARKET_DATA.value:
            reject("GMP_SOURCE_TYPE_INVALID", "GMP source reference must identify market data")

    content_hash = values.get("content_hash")
    if not isinstance(content_hash, str) or re.fullmatch(r"[0-9a-fA-F]{64}", content_hash) is None:
        reject("GMP_CONTENT_HASH_INVALID", "GMP snapshot must carry a valid 64-character SHA-256 content hash")
    if source_ref is not None:
        if source_ref.content_hash != content_hash:
            reject("GMP_CONTENT_HASH_MISMATCH", "GMP snapshot hash does not match its registered source hash")
        if (
            not isinstance(source_ref.content_hash, str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", source_ref.content_hash) is None
        ):
            reject("GMP_SOURCE_HASH_INVALID", "registered GMP source content hash is missing or invalid")
        if source_ref.retrieval_timestamp is None:
            reject("GMP_RETRIEVAL_TIMESTAMP_MISSING", "GMP source retrieval timestamp is missing")

    if isinstance(raw_payload, Mapping) and isinstance(content_hash, str):
        try:
            from .connectors.interfaces import compute_payload_hash

            computed_hash = compute_payload_hash(raw_payload)
        except (TypeError, ValueError, OverflowError):
            computed_hash = None
        if computed_hash != content_hash:
            reject("GMP_CONTENT_HASH_MISMATCH", "GMP raw source payload does not match its SHA-256 content hash")

    event_timestamp = gmp_block.as_of
    source_timestamp = source_ref.source_timestamp if source_ref is not None else None
    raw_event_timestamp = raw_payload.get("as_of") if isinstance(raw_payload, Mapping) else None
    if not event_timestamp or not source_timestamp or not raw_event_timestamp:
        reject("GMP_EVENT_TIMESTAMP_MISSING", "GMP source-event/as-of timestamp is missing")
    elif not (event_timestamp == source_timestamp == raw_event_timestamp):
        reject("GMP_EVENT_TIMESTAMP_MISMATCH", "GMP block, raw source snapshot and source reference timestamps differ")
    else:
        try:
            parsed_event = parse_datetime(event_timestamp)
        except (ValueError, TypeError, OverflowError):
            parsed_event = None
            reject("GMP_EVENT_TIMESTAMP_INVALID", "GMP source-event/as-of timestamp is not parseable")
        if parsed_event is not None and evaluation_datetime is not None:
            eval_moment = evaluation_datetime
            if eval_moment.tzinfo is None:
                eval_moment = eval_moment.replace(tzinfo=timezone.utc)
            if parsed_event > eval_moment.astimezone(timezone.utc):
                reject("GMP_EVENT_TIMESTAMP_FUTURE", "GMP source-event timestamp is after the Final evaluation time")
        if not re.search(r"(?:Z|[+-]\d{2}:\d{2})$", str(event_timestamp)):
            reject("GMP_EVENT_TIMEZONE_MISSING", "GMP source-event timestamp must retain its timezone/UTC offset")

    retrieval_timestamp = values.get("retrieval_timestamp")
    source_retrieval_timestamp = source_ref.retrieval_timestamp if source_ref is not None else None
    raw_retrieval_timestamp = raw_payload.get("retrieval_timestamp") if isinstance(raw_payload, Mapping) else None
    if not retrieval_timestamp or not source_retrieval_timestamp or not raw_retrieval_timestamp:
        reject("GMP_RETRIEVAL_TIMESTAMP_MISSING", "GMP source retrieval timestamp is missing")
    elif not (retrieval_timestamp == source_retrieval_timestamp == raw_retrieval_timestamp):
        reject("GMP_RETRIEVAL_TIMESTAMP_MISMATCH", "GMP retrieval timestamps differ across the snapshot and source reference")
    else:
        try:
            parse_datetime(retrieval_timestamp)
        except (ValueError, TypeError, OverflowError):
            reject("GMP_RETRIEVAL_TIMESTAMP_INVALID", "GMP retrieval timestamp is not parseable")
        if not re.search(r"(?:Z|[+-]\d{2}:\d{2})$", str(retrieval_timestamp)):
            reject("GMP_RETRIEVAL_TIMEZONE_MISSING", "GMP retrieval timestamp must retain its timezone/UTC offset")

    for numeric_key in ("gmp_rupees", "pct"):
        value = values.get(numeric_key)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            reject("GMP_OBSERVATION_INVALID", f"GMP {numeric_key} must be a finite numeric value when supplied")

    return findings


def evaluate(
    input_document: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    mode: str = "final",
    schema: Optional[Mapping[str, Any]] = None,
    evaluation_datetime: Optional[datetime] = None,
    store: Optional[EvaluationStore] = None,
    workbook_path: Optional[str | Path] = None,
    preliminary: Optional[Mapping[str, Any]] = None,
) -> EvaluationOutcome:
    """Run one evaluation end to end.

    ``config`` must already have passed :func:`compile_config` so that the
    configuration gate cannot be bypassed.
    """
    if not isinstance(input_document, Mapping):
        from .enrichment_engine import EnrichmentResult

        if not isinstance(input_document, EnrichmentResult):
            raise TypeError("input_document must be a canonical mapping or EnrichmentResult")
        if not input_document.is_valid:
            errors = [finding for finding in input_document.findings if finding.severity == SEVERITY_ERROR]
            raise ValidationError("enrichment", errors)
        input_document = input_document.canonical_input

    if "_fingerprint" not in config:
        config = compile_config(config)

    moment = evaluation_datetime or datetime.now(timezone.utc)
    timestamp = moment.strftime("%Y-%m-%dT%H:%M:%SZ")

    # -- 1. structural validation (hard gate) -------------------------------
    enforce_schema(input_document, schema)

    # -- 2. canonicalisation + evidence -------------------------------------
    canonical = build_canonical_input(input_document)

    # -- 3. snapshots --------------------------------------------------------
    thresholds = config.get("thresholds", {})
    peer_eligibility = config.get("peer_eligibility", {}) or {}
    peers = classify_peers(
        canonical.peers(),
        evaluation_datetime=moment,
        staleness_days=peer_eligibility.get("staleness_days"),
        min_listed_years=peer_eligibility.get("min_listed_years"),
    )
    market = build_market_snapshot(
        canonical.market(),
        evaluation_datetime=moment,
        staleness_hours=int(thresholds.get("market_staleness_hours", DEFAULT_MARKET_STALENESS_HOURS)),
    )
    if mode.lower() == "final":
        gmp_findings = validate_final_gmp_snapshot(canonical, market, evaluation_datetime=moment)
        if gmp_findings:
            raise ValidationError("final_gmp", gmp_findings)

    # -- 4. semantic validation (hard gate) ---------------------------------
    report = validate_semantics(canonical, config, peers, market)
    report.extend(canonical.findings)
    if not report.ok:
        from .errors import SemanticValidationError

        raise SemanticValidationError(report.errors)

    # -- 5. derived metrics -------------------------------------------------
    derived = derive(canonical, config, peers, market, evaluation_datetime=moment)

    # -- 6. overlay resolution (hard gate) ----------------------------------
    plan = resolve_overlays(config, derived, canonical.sector_profile)
    report.extend(plan.findings)

    # -- 7. knockouts -------------------------------------------------------
    knockouts = KnockoutSummary(results=evaluate_knockouts(config, derived))

    # -- 8. scoring ---------------------------------------------------------
    score_result = score(config, derived, plan, knockouts, mode=mode)

    # -- 9. immutable evaluation record -------------------------------------
    missing_rows = excel_module.build_missing_unverified_rows(
        {
            "score": score_result.to_dict(),
            "knockouts": knockouts.to_dict(),
            "peer_snapshot": peers.to_dict(),
            "market_snapshot": market.to_dict(),
            "penalties": [dict(p) for p in score_result.penalty_items],
        }
    )

    # A Final evaluation is compared against the latest stored Preliminary for
    # the same issuer, unless the caller supplied one explicitly. The
    # Preliminary itself is never modified (spec s19).
    if preliminary is None and store is not None and mode.lower() == "final":
        preliminary = store.latest_for(canonical.ipo_id, "preliminary")

    record = build_record(
        canonical_snapshot=canonical.to_snapshot_dict(),
        evidence=canonical.registry.to_dict(),
        market_snapshot=market.to_dict(),
        peer_snapshot=peers.to_dict(),
        derived_metrics=derived.to_dict(),
        effective_config=_config_summary(config),
        validation=report.to_dict(),
        knockouts=knockouts.to_dict(),
        score_payload=score_result.to_dict(),
        plan=plan.to_dict(),
        penalties=score_result.penalty_items,
        missing_unverified=missing_rows,
        ipo_id=canonical.ipo_id,
        company_name=canonical.company_name,
        mode=mode,
        timestamp=timestamp,
        config_version=str(config.get("config_version")),
        config_hash=str(config.get("_fingerprint") or config_fingerprint(config)),
        preliminary=preliminary,
        notes=(
            "Excel is a projection of this record, not the authoritative store (spec s3.6).",
            "Unknown values are never converted to zero; they widen the score range (spec s3.2).",
        ),
    )

    outcome = EvaluationOutcome(
        record=record,
        score=score_result,
        knockouts=knockouts,
        plan=plan,
        derived=derived,
        validation=report,
        canonical=canonical,
    )

    # -- 10. persistence ----------------------------------------------------
    if store is not None:
        outcome.stored_at = store.write(record)
        if workbook_path is not None:
            outcome.workbook_path = excel_module.project(store, workbook_path).path
    elif workbook_path is not None:
        single = excel_module.build_workbook([record.to_dict()])
        target = Path(workbook_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        single.save(target)
        outcome.workbook_path = target

    return outcome


def evaluate_file(
    input_path: str | Path,
    config_path: str | Path | None = None,
    *,
    mode: str = "final",
    store_root: str | Path | None = None,
    workbook_path: str | Path | None = None,
    evaluation_datetime: Optional[datetime] = None,
) -> EvaluationOutcome:
    """Convenience wrapper: evaluate an input JSON file against a config file."""
    with Path(input_path).open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    config = load_config(config_path)
    store = EvaluationStore(store_root) if store_root else None
    return evaluate(
        document,
        config,
        mode=mode,
        store=store,
        workbook_path=workbook_path,
        evaluation_datetime=evaluation_datetime,
    )


def replay(
    store: EvaluationStore,
    evaluation_id: str,
    config: Optional[Mapping[str, Any]] = None,
    *,
    evaluation_datetime: Optional[datetime] = None,
) -> EvaluationOutcome:
    """Re-evaluate a stored run from its own frozen snapshots.

    Reproducibility check (spec s19): the same inputs, source snapshot,
    configuration and engine version must yield the same ``result_hash``.
    """
    record = store.read(evaluation_id)
    # Default to the instant the evaluation was originally taken. Freshness
    # classification (which peers are VALID, which market blocks are FRESH) is
    # a function of that instant, so replaying at "now" could legitimately
    # produce a different snapshot and would not be a reproducibility check.
    if evaluation_datetime is None:
        stored = str(record.get("evaluation_timestamp") or "")
        if stored:
            evaluation_datetime = datetime.fromisoformat(
                stored.replace("Z", "+00:00")
            ).astimezone(timezone.utc)
    # Read the frozen artifacts rather than the evaluation summary: the input
    # snapshot and the provenance blocks live in their own files (spec s23).
    input_artifact = store.read_artifact(evaluation_id, "input")
    snapshot = input_artifact.get("snapshot") or {}
    input_document = dict(snapshot.get("input") or {})

    evidence_artifact = store.read_artifact(evaluation_id, "evidence")
    evidence = evidence_artifact.get("evidence") or {}
    input_document["_sources"] = evidence.get("sources") or []
    input_document["_evidence"] = {
        item["evidence_id"]: item for item in evidence.get("evidence", [])
    }
    resolved_config = config
    if resolved_config is None:
        with (Path(__file__).resolve().parents[2] / DEFAULT_CONFIG_PATH).open("r", encoding="utf-8") as handle:
            resolved_config = compile_config(json.load(handle))
    return evaluate(
        input_document,
        resolved_config,
        mode=str(record["evaluation_mode"]).lower(),
        evaluation_datetime=evaluation_datetime,
    )


def _config_summary(config: Mapping[str, Any]) -> Dict[str, Any]:
    """The configuration content that materially shaped the result."""
    return {
        "config_version": config.get("config_version"),
        "spec_version": config.get("spec_version"),
        "config_hash": config.get("_fingerprint"),
        "currency": config.get("currency"),
        "thresholds": config.get("thresholds"),
        "peer_eligibility": config.get("peer_eligibility", {"staleness_days": None, "min_listed_years": None}),
        "verdict": config.get("verdict"),
        "confidence": config.get("confidence"),
        "gcp": config.get("gcp"),
        "modes": config.get("modes"),
        "profile_resolution": config.get("profile_resolution"),
        "knockouts": [{"id": k["id"], "label": k.get("label"), "required": k.get("required")} for k in config.get("knockouts", [])],
        "penalties": config.get("penalties"),
        "caps": config.get("caps"),
        "validation": config.get("validation"),
    }


__all__ = [
    "EvaluationOutcome",
    "evaluate",
    "evaluate_file",
    "load_config",
    "replay",
    "validate_final_gmp_snapshot",
]
