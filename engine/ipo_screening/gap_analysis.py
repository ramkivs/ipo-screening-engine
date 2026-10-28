"""Read-only gap analysis for one immutable persisted evaluation.

This module observes the baseline record; it never evaluates, enriches, or writes
to an :class:`EvaluationStore`.  Every reported gap is copied from the stored
``missing_unverified`` projection and is therefore bounded by what the baseline
actually established.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

from .evaluation import EvaluationStore
from .hashing import sha256_of

REPORT_VERSION = "1.0"


def _criterion_index(record: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    indexed: Dict[str, Mapping[str, Any]] = {}
    for module in (record.get("score") or {}).get("modules", []):
        for criterion in module.get("criteria", []):
            criterion_id = criterion.get("criterion_id")
            if criterion_id:
                indexed[str(criterion_id)] = {
                    "module_id": module.get("module_id"),
                    "module_name": module.get("name"),
                    "criterion": criterion,
                }
    return indexed


def _next_step(category: str) -> str:
    steps = {
        "CRITERION": "Inspect the stored criterion reason, canonical input, and existing evidence references; the report does not establish whether the source omitted the value or a reader missed it.",
        "KNOCKOUT": "Inspect the stored knockout explanation and named missing inputs before making any decision; preserve UNVERIFIED unless eligible evidence is established.",
        "PEER": "Inspect the frozen peer observation and its stated status/reason; do not substitute manually entered or undated multiples.",
        "MARKET": "Inspect the frozen market block timestamp, status, and reason; obtain only category-appropriate qualified evidence if needed.",
        "PENALTY": "Inspect the stored penalty reason and dependencies; do not resolve an unknown dependency by assumption.",
        "CRITICAL_DATA": "Inspect the named critical input in the frozen canonical input and evidence artifact; the baseline verdict remains unchanged.",
    }
    return steps.get(category, "Inspect the selected evaluation artifacts; no more specific cause is established by the stored report row.")


def build_gap_report(store: EvaluationStore, evaluation_id: str) -> Dict[str, Any]:
    """Build a deterministic report after verifying one explicitly selected record.

    Raises ``FileNotFoundError`` for an unavailable identity and ``ValueError``
    when any baseline artifact/result hash is inconsistent.
    """
    if not store.exists(evaluation_id):
        raise FileNotFoundError(
            f"no stored evaluation {evaluation_id!r} under {store.root}"
        )

    verification = store.verify_hashes(evaluation_id)
    if not verification["result_hash_matches"] or verification["artifact_mismatches"]:
        raise ValueError(
            f"stored evaluation {evaluation_id!r} failed integrity verification; "
            "gap analysis refused"
        )

    record = store.read_full(evaluation_id)
    manifest = store.read_artifact(evaluation_id, "manifest")
    criteria = _criterion_index(record)
    gaps = []
    for index, original in enumerate(record.get("missing_unverified") or []):
        category = str(original.get("category") or "UNSPECIFIED")
        item = original.get("item")
        points = original.get("points_affected")
        linked = criteria.get(str(item)) if category == "CRITERION" else None
        score_effect_established = isinstance(points, (int, float)) and points > 0
        gap: Dict[str, Any] = {
            "index": index,
            "category": category,
            "item": item,
            "state": original.get("state"),
            "reason": original.get("detail") or None,
            "reason_availability": "STORED_EXPLANATION" if original.get("detail") else "UNDETERMINED",
            "module_id": linked.get("module_id") if linked else None,
            "module_name": linked.get("module_name") if linked else None,
            "score_effect": {
                "connection": "ESTABLISHED_BY_BASELINE" if score_effect_established else "NOT_ESTABLISHED_BY_AVAILABLE_ARTIFACTS",
                "points_affected": points if score_effect_established else None,
                "note": (
                    "Stored UNKNOWN criterion maximum contributes to the baseline score range; this is not a replacement score."
                    if score_effect_established
                    else "The available row does not establish a numeric score effect."
                ),
            },
            "evidence_references": [],
            "provenance_availability": "NO_GAP_SPECIFIC_REFERENCE_IN_BASELINE_ROW",
            "next_inspection_step": _next_step(category),
        }
        gaps.append(gap)

    report: Dict[str, Any] = {
        "report_type": "READ_ONLY_BASELINE_GAP_ANALYSIS",
        "report_version": REPORT_VERSION,
        "observational_only": True,
        "baseline": {
            "evaluation_id": record.get("evaluation_id"),
            "ipo_id": record.get("ipo_id"),
            "company_name": record.get("company_name"),
            "evaluation_mode": record.get("evaluation_mode"),
            "evaluation_timestamp": record.get("evaluation_timestamp"),
            "engine_version": record.get("engine_version"),
            "spec_version": record.get("spec_version"),
            "hashes": {
                "config_hash": record.get("config_hash"),
                "input_snapshot_hash": record.get("input_snapshot_hash"),
                "source_manifest_hash": record.get("source_manifest_hash"),
                "market_snapshot_hash": record.get("market_snapshot_hash"),
                "peer_snapshot_hash": record.get("peer_snapshot_hash"),
                "result_hash": record.get("result_hash"),
            },
            "artifact_hashes": dict(manifest.get("artifacts") or {}),
            "integrity_verified": True,
        },
        "summary": {
            "gap_count": len(gaps),
            "complete": len(gaps) == 0,
            "numeric_score_effect_gap_count": sum(
                1 for gap in gaps if gap["score_effect"]["connection"] == "ESTABLISHED_BY_BASELINE"
            ),
        },
        "gaps": gaps,
        "sources": list((record.get("evidence") or {}).get("sources") or []),
        "limitations": [
            "The report copies stored baseline states and explanations; it does not infer why a source value is absent unless the baseline says why.",
            "An empty evidence_references list means the baseline gap row did not carry a gap-specific reference; global sources are not attributed to that gap.",
            "The report is not source evidence, supplemental input, verification of a new value, or a scoring result.",
            "The baseline evaluation and all of its hashes remain authoritative and unchanged.",
        ],
    }
    report["report_hash"] = sha256_of(report)
    return report


__all__ = ["REPORT_VERSION", "build_gap_report"]
