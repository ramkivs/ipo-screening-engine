"""Immutable evaluation records and the append-only store.

Spec v1.5 s21 (mandatory historical persistence) and s23 (immutable
machine-readable record). Tech design s11 and s13.

Every evaluation receives an ``evaluation_id``, the version and hash stamps,
and a machine-readable record written to disk as a directory of JSON
artifacts:

    evaluation/
      evaluation.json   the full record
      input.json        the canonical input snapshot
      evidence.json     sources and evidence
      market.json       the frozen market snapshot
      peers.json        the frozen peer snapshot
      result.json       score, knockouts, confidence, range, verdict
      manifest.json     hashes of every artifact above

Rules enforced here:

  * never overwrite a prior evaluation - writing to an existing evaluation_id
    raises :class:`ImmutabilityError`;
  * the result hash is computed only over deterministic content, so re-running
    the same inputs, snapshots, configuration and engine version yields the
    same ``result_hash`` (spec s19 acceptance test);
  * a Final evaluation that differs from its Preliminary counterpart stores a
    delta record rather than amending the Preliminary.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .errors import ImmutabilityError
from .hashing import evaluate_id, sha256_of
from .version import ENGINE_VERSION, SPEC_VERSION

LIFECYCLE = (
    "PRELIMINARY",
    "FINAL",
    "POST_LISTING_1W",
    "POST_LISTING_1M",
    "POST_LISTING_6M",
)

ARTIFACT_FILES = (
    "evaluation.json",
    "input.json",
    "evidence.json",
    "market.json",
    "peers.json",
    "result.json",
    "manifest.json",
)


def compute_result_hash(payload: Mapping[str, Any]) -> str:
    """Deterministic hash of the evaluation outcome.

    Deliberately excludes wall-clock stamps and the evaluation id so that the
    same inputs, source snapshots, configuration and engine version always
    produce the same hash (spec s19).
    """
    return sha256_of(payload)


@dataclass
class EvaluationRecord:
    """A complete, immutable evaluation."""

    evaluation_id: str
    ipo_id: str
    company_name: str
    evaluation_mode: str
    evaluation_timestamp: str
    engine_version: str
    spec_version: str
    config_version: str
    config_hash: str
    input_snapshot_hash: str
    source_manifest_hash: str
    market_snapshot_hash: str
    peer_snapshot_hash: str
    result_hash: str
    input_snapshot: Mapping[str, Any]
    evidence: Mapping[str, Any]
    market_snapshot: Mapping[str, Any]
    peer_snapshot: Mapping[str, Any]
    derived_metrics: Mapping[str, Any]
    effective_config: Mapping[str, Any]
    validation: Mapping[str, Any]
    knockouts: Mapping[str, Any]
    score: Mapping[str, Any]
    confidence: Mapping[str, Any]
    score_range: Mapping[str, Any]
    verdict: Mapping[str, Any]
    provenance: Mapping[str, Any]
    plan: Mapping[str, Any]
    penalties: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    missing_unverified: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    preliminary_delta: Optional[Mapping[str, Any]] = None
    notes: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "ipo_id": self.ipo_id,
            "company_name": self.company_name,
            "evaluation_mode": self.evaluation_mode,
            "evaluation_timestamp": self.evaluation_timestamp,
            "engine_version": self.engine_version,
            "spec_version": self.spec_version,
            "config_version": self.config_version,
            "config_hash": self.config_hash,
            "input_snapshot_hash": self.input_snapshot_hash,
            "source_manifest_hash": self.source_manifest_hash,
            "market_snapshot_hash": self.market_snapshot_hash,
            "peer_snapshot_hash": self.peer_snapshot_hash,
            # The artifacts a reader needs in order to audit the result. They
            # are included so that ``to_dict()`` is the *complete* record and
            # any projection built from it (Excel, reports) sees the same data
            # as one built from the persisted artifacts. Omitting them silently
            # emptied the Evidence/Market/Peer sheets (spec s21, s23).
            "input_snapshot": self.input_snapshot,
            "evidence": dict(self.evidence),
            "market_snapshot": dict(self.market_snapshot),
            "peer_snapshot": dict(self.peer_snapshot),
            "derived_metrics": dict(self.derived_metrics),
            "result_hash": self.result_hash,
            "plan": dict(self.plan),
            "score": dict(self.score),
            "confidence": dict(self.confidence),
            "score_range": dict(self.score_range),
            "verdict": dict(self.verdict),
            "knockouts": dict(self.knockouts),
            "penalties": [dict(p) for p in self.penalties],
            "missing_unverified": [dict(m) for m in self.missing_unverified],
            "validation": dict(self.validation),
            "provenance": dict(self.provenance),
            "effective_config": dict(self.effective_config),
            "preliminary_delta": dict(self.preliminary_delta) if self.preliminary_delta else None,
            "notes": list(self.notes),
            "lifecycle_stage": self.evaluation_mode,
        }

    # -- artifact views ----------------------------------------------------

    def input_artifact(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "ipo_id": self.ipo_id,
            "input_snapshot_hash": self.input_snapshot_hash,
            "snapshot": self.input_snapshot,
        }

    def evidence_artifact(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "source_manifest_hash": self.source_manifest_hash,
            "evidence": self.evidence,
        }

    def market_artifact(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "market_snapshot_hash": self.market_snapshot_hash,
            "snapshot": self.market_snapshot,
        }

    def peers_artifact(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "peer_snapshot_hash": self.peer_snapshot_hash,
            "snapshot": self.peer_snapshot,
        }

    def result_artifact(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "result_hash": self.result_hash,
            "plan": dict(self.plan),
            "derived_metrics": dict(self.derived_metrics),
            "score": dict(self.score),
            "knockouts": dict(self.knockouts),
            "confidence": dict(self.confidence),
            "score_range": dict(self.score_range),
            "verdict": dict(self.verdict),
            "penalties": [dict(p) for p in self.penalties],
            "missing_unverified": [dict(m) for m in self.missing_unverified],
        }

    def artifacts(self) -> Dict[str, Any]:
        """The full set of files written for this evaluation."""
        payloads = {
            "evaluation.json": self.to_dict(),
            "input.json": self.input_artifact(),
            "evidence.json": self.evidence_artifact(),
            "market.json": self.market_artifact(),
            "peers.json": self.peers_artifact(),
            "result.json": self.result_artifact(),
        }
        manifest = {
            "evaluation_id": self.evaluation_id,
            "engine_version": self.engine_version,
            "spec_version": self.spec_version,
            "config_version": self.config_version,
            "config_hash": self.config_hash,
            "result_hash": self.result_hash,
            "input_snapshot_hash": self.input_snapshot_hash,
            "source_manifest_hash": self.source_manifest_hash,
            "market_snapshot_hash": self.market_snapshot_hash,
            "peer_snapshot_hash": self.peer_snapshot_hash,
            "evaluation_timestamp": self.evaluation_timestamp,
            "artifacts": {
                name: sha256_of(payload) for name, payload in sorted(payloads.items())
            },
        }
        payloads["manifest.json"] = manifest
        return payloads


def build_record(
    *,
    canonical_snapshot: Mapping[str, Any],
    evidence: Mapping[str, Any],
    market_snapshot: Mapping[str, Any],
    peer_snapshot: Mapping[str, Any],
    derived_metrics: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    validation: Mapping[str, Any],
    knockouts: Mapping[str, Any],
    score_payload: Mapping[str, Any],
    plan: Mapping[str, Any],
    penalties: Sequence[Mapping[str, Any]],
    missing_unverified: Sequence[Mapping[str, Any]],
    ipo_id: str,
    company_name: str,
    mode: str,
    timestamp: str,
    config_version: str,
    config_hash: str,
    preliminary: Optional[Mapping[str, Any]] = None,
    notes: Sequence[str] = (),
) -> EvaluationRecord:
    """Assemble an immutable record and compute every hash."""
    input_snapshot_hash = sha256_of(canonical_snapshot)
    source_manifest_hash = str(evidence.get("manifest_hash", sha256_of(evidence)))
    # Hash the *material* snapshot content. ``content_hash`` is supplied by the
    # snapshot object itself and excludes volatile wall-clock ages, which are
    # audit detail rather than decision inputs (spec s19). Falling back to a
    # plain hash keeps the function usable with hand-built snapshots.
    market_snapshot_hash = str(market_snapshot.get("content_hash") or sha256_of(market_snapshot))
    peer_snapshot_hash = str(peer_snapshot.get("content_hash") or sha256_of(peer_snapshot))

    # Result hash covers only deterministic content: no timestamps, no ids.
    result_payload = {
        "engine_version": ENGINE_VERSION,
        "spec_version": SPEC_VERSION,
        "config_hash": config_hash,
        "input_snapshot_hash": input_snapshot_hash,
        "source_manifest_hash": source_manifest_hash,
        "market_snapshot_hash": market_snapshot_hash,
        "peer_snapshot_hash": peer_snapshot_hash,
        "mode": mode,
        "plan": plan,
        "derived_metrics": derived_metrics,
        "knockouts": knockouts,
        "score": score_payload,
        "penalties": list(penalties),
        "missing_unverified": list(missing_unverified),
    }
    result_hash = compute_result_hash(result_payload)

    record = EvaluationRecord(
        evaluation_id=evaluate_id(ipo_id, timestamp, mode.lower(), result_hash),
        ipo_id=ipo_id,
        company_name=company_name,
        evaluation_mode=mode.upper(),
        evaluation_timestamp=timestamp,
        engine_version=ENGINE_VERSION,
        spec_version=SPEC_VERSION,
        config_version=config_version,
        config_hash=config_hash,
        input_snapshot_hash=input_snapshot_hash,
        source_manifest_hash=source_manifest_hash,
        market_snapshot_hash=market_snapshot_hash,
        peer_snapshot_hash=peer_snapshot_hash,
        result_hash=result_hash,
        input_snapshot=canonical_snapshot,
        evidence=evidence,
        market_snapshot=market_snapshot,
        peer_snapshot=peer_snapshot,
        derived_metrics=derived_metrics,
        effective_config=effective_config,
        validation=validation,
        knockouts=knockouts,
        score=score_payload,
        confidence={
            "level": score_payload.get("confidence"),
            "completeness_pct": score_payload.get("completeness_pct"),
            "weighting": "POINTS",
            "breakdown": score_payload.get("completeness_breakdown"),
        },
        score_range={
            "lower_bound": score_payload.get("lower_bound"),
            "upper_bound": score_payload.get("upper_bound"),
            "base_score": score_payload.get("base_score"),
            "final_score": score_payload.get("final_score"),
            "unknown_points": score_payload.get("unknown_points"),
            "available_points": score_payload.get("available_points"),
            "total_evaluable_points": score_payload.get("total_evaluable_points"),
            "unresolved_penalty_points": score_payload.get("unresolved_penalty_points"),
        },
        verdict={
            "verdict": score_payload.get("verdict"),
            "band_score": score_payload.get("verdict_band_score"),
            "uncertain": score_payload.get("verdict_uncertain"),
            "insufficient_data": score_payload.get("insufficient_data"),
            "mode_label": (effective_config.get("modes") or {}).get(mode, {}).get("verdict_label"),
        },
        provenance={
            "sources": (evidence.get("sources") or []),
            "evidence_count": len(evidence.get("evidence") or []),
            "engine_version": ENGINE_VERSION,
            "spec_version": SPEC_VERSION,
            "note": (
                "Excel is a projection of this record, not the authoritative store "
                "(spec s3.6, s22)"
            ),
        },
        plan=plan,
        penalties=tuple(penalties),
        missing_unverified=tuple(missing_unverified),
        # The delta is computed here rather than stored raw, because it needs
        # this record's own result hash to be a complete comparison (spec s19).
        preliminary_delta=(
            None
            if preliminary is None
            else compute_preliminary_delta(
                preliminary,
                {
                    "evaluation_id": evaluate_id(
                        ipo_id, timestamp, mode.lower(), result_hash
                    ),
                    "result_hash": result_hash,
                    "score": score_payload,
                    "verdict": {
                        "verdict": score_payload.get("verdict"),
                        "uncertain": score_payload.get("verdict_uncertain"),
                    },
                    "knockouts": knockouts,
                },
            )
        ),
        notes=tuple(notes),
    )
    return record


def compute_preliminary_delta(
    preliminary: Mapping[str, Any], final: Mapping[str, Any]
) -> Dict[str, Any]:
    """Delta record between a Preliminary and its Final (spec s19)."""

    def _score(payload: Mapping[str, Any]) -> Optional[float]:
        score = payload.get("score") or {}
        return score.get("final_score")

    pre_score, fin_score = _score(preliminary), _score(final)
    pre_ko = (preliminary.get("knockouts") or {}).get("status")
    fin_ko = (final.get("knockouts") or {}).get("status")
    return {
        "preliminary_evaluation_id": preliminary.get("evaluation_id"),
        "final_evaluation_id": final.get("evaluation_id"),
        # Both hashes are carried so an auditor can see exactly which frozen
        # preliminary this final is being compared against (spec s19).
        "preliminary_result_hash": preliminary.get("result_hash"),
        "final_result_hash": final.get("result_hash"),
        "inputs_changed": preliminary.get("result_hash") != final.get("result_hash"),
        "preliminary_score": pre_score,
        "final_score": fin_score,
        "score_delta": (
            None if pre_score is None or fin_score is None else round(fin_score - pre_score, 6)
        ),
        "preliminary_verdict": (preliminary.get("verdict") or {}).get("verdict"),
        "final_verdict": (final.get("verdict") or {}).get("verdict"),
        "verdict_changed": (preliminary.get("verdict") or {}).get("verdict")
        != (final.get("verdict") or {}).get("verdict"),
        "preliminary_knockout_status": pre_ko,
        "final_knockout_status": fin_ko,
        "knockout_status_changed": pre_ko != fin_ko,
        "note": (
            "The Preliminary evaluation is retained unmodified; this delta record is stored "
            "alongside the Final (spec s19)."
        ),
    }


class EvaluationStore:
    """Append-only store of immutable evaluation records.

    ``write`` refuses to overwrite: writing the same ``evaluation_id`` twice
    raises :class:`ImmutabilityError`, and a rerun against changed inputs or
    configuration produces a *different* id because the result hash changes.
    """

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)

    def path_for(self, evaluation_id: str) -> Path:
        return self.root / evaluation_id

    def exists(self, evaluation_id: str) -> bool:
        return self.path_for(evaluation_id).exists()

    def list_evaluations(self) -> List[str]:
        if not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())

    def write(self, record: EvaluationRecord) -> Path:
        directory = self.path_for(record.evaluation_id)
        if directory.exists():
            raise ImmutabilityError(
                f"evaluation {record.evaluation_id!r} already exists at {directory}; historical "
                "evaluations are immutable and must never be overwritten (spec s21). A corrected "
                "extraction, a new configuration or a new snapshot must create a new evaluation."
            )
        directory.mkdir(parents=True, exist_ok=False)
        for name, payload in sorted(record.artifacts().items()):
            target = directory / name
            # Exclusive create: even a race cannot clobber an existing artifact.
            with target.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.write("\n")
        return directory

    def read(self, evaluation_id: str) -> Dict[str, Any]:
        """Read ``evaluation.json`` for one evaluation."""
        path = self.path_for(evaluation_id) / "evaluation.json"
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def read_artifact(self, evaluation_id: str, name: str) -> Dict[str, Any]:
        """Read one sibling artifact (``input``/``evidence``/``market``/``peers``/``result``)."""
        path = self.path_for(evaluation_id) / f"{name}.json"
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def read_full(self, evaluation_id: str) -> Dict[str, Any]:
        """Read the evaluation merged with its sibling artifacts.

        The projection layer needs the frozen snapshots, which live beside
        ``evaluation.json`` rather than inside it so that the record itself
        stays compact and each artifact keeps its own hash.
        """
        record = self.read(evaluation_id)
        record["input_snapshot"] = self.read_artifact(evaluation_id, "input").get("snapshot", {})
        record["evidence"] = self.read_artifact(evaluation_id, "evidence").get("evidence", {})
        record["market_snapshot"] = self.read_artifact(evaluation_id, "market").get("snapshot", {})
        record["peer_snapshot"] = self.read_artifact(evaluation_id, "peers").get("snapshot", {})
        return record

    def read_all(self, full: bool = True) -> List[Dict[str, Any]]:
        reader = self.read_full if full else self.read
        return [reader(eid) for eid in self.list_evaluations()]

    def latest_for(self, ipo_id: str, mode: Optional[str] = None) -> Optional[Dict[str, Any]]:
        candidates = [
            r
            for r in self.read_all(full=False)
            if r.get("ipo_id") == ipo_id and (mode is None or r.get("evaluation_mode") == mode.upper())
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda r: r.get("evaluation_timestamp", ""))[-1]

    def verify_hashes(self, evaluation_id: str) -> Dict[str, Any]:
        """Re-derive every artifact hash and the result hash from the files.

        This is the auditability check for spec s19/s24: reading a stored
        evaluation back and recomputing its result hash must reproduce the
        stored value.
        """
        directory = self.path_for(evaluation_id)
        record = self.read(evaluation_id)
        manifest_path = directory / "manifest.json"
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        mismatches: List[Dict[str, Any]] = []
        for name, expected in sorted(manifest.get("artifacts", {}).items()):
            with (directory / name).open("r", encoding="utf-8") as handle:
                actual = sha256_of(json.load(handle))
            if actual != expected:
                mismatches.append({"artifact": name, "expected": expected, "actual": actual})

        result_payload = {
            "engine_version": record["engine_version"],
            "spec_version": record["spec_version"],
            "config_hash": record["config_hash"],
            "input_snapshot_hash": record["input_snapshot_hash"],
            "source_manifest_hash": record["source_manifest_hash"],
            "market_snapshot_hash": record["market_snapshot_hash"],
            "peer_snapshot_hash": record["peer_snapshot_hash"],
            "mode": record["evaluation_mode"].lower(),
            "plan": record["plan"],
            "derived_metrics": json.loads(
                (directory / "result.json").read_text(encoding="utf-8")
            )["derived_metrics"],
            "knockouts": record["knockouts"],
            "score": record["score"],
            "penalties": record["penalties"],
            "missing_unverified": record["missing_unverified"],
        }
        recomputed_result_hash = compute_result_hash(result_payload)
        return {
            "evaluation_id": evaluation_id,
            "stored_result_hash": record["result_hash"],
            "recomputed_result_hash": recomputed_result_hash,
            "result_hash_matches": recomputed_result_hash == record["result_hash"],
            "artifact_mismatches": mismatches,
            "artifacts_verified": len(manifest.get("artifacts", {})),
        }


__all__ = [
    "LIFECYCLE",
    "ARTIFACT_FILES",
    "EvaluationRecord",
    "EvaluationStore",
    "build_record",
    "compute_result_hash",
    "compute_preliminary_delta",
]
