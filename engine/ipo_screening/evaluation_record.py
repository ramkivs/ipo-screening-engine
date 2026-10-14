"""A15 Canonical Evaluation Record v1 projection.

The v1 artifact is deliberately a projection of the immutable v1.5
:class:`EvaluationRecord`; it does not change the decision engine or its
hashes. Facts absent from that legacy model stay explicitly unresolved and
continue to be available through the referenced sibling artifacts.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .canonical_input import MONETARY_FIELDS
from .hashing import CANONICAL_GRAMMAR_VERSION, sha256_of
from .schema_validation import enforce_schema

RECORD_SCHEMA_VERSION = "1.0.0"
RECORD_ARTIFACT_NAME = "evaluation-record.v1.json"
CANONICALIZATION_ID = f"ipo-engine-canonical-json/{CANONICAL_GRAMMAR_VERSION}"
SERIALIZATION_PROFILE_ID = "ipo-evaluation-record-json/1.0.0"

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schema"
    / "ipo-evaluation-record.v1.schema.json"
)


class EvaluationRecordV1Error(ValueError):
    """The projected record cannot be represented without violating A15."""


def _pointer_escape(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _json_pointer(tokens: Sequence[Any], *, root: str = "/input") -> str:
    if not tokens:
        return root
    return root + "/" + "/".join(_pointer_escape(token) for token in tokens)


def _legacy_path(tokens: Sequence[Any]) -> str:
    """Render a raw input path in canonical_input's historical dotted form."""
    parts: List[str] = []
    for token in tokens:
        if isinstance(token, int):
            if not parts:
                parts.append(f"[{token}]")
            else:
                parts[-1] += f"[{token}]"
        else:
            parts.append(str(token))
    return ".".join(parts)


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:20]}"


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, bool, int, float))


def _walk_scalars(
    node: Any,
    tokens: Tuple[Any, ...] = (),
) -> Iterable[Tuple[Tuple[Any, ...], Any]]:
    """Yield JSON scalar leaves in stable path order; private blocks are excluded."""
    if isinstance(node, Mapping):
        for key in sorted(node, key=lambda item: str(item)):
            if str(key).startswith("_"):
                continue
            yield from _walk_scalars(node[key], tokens + (str(key),))
        return
    if isinstance(node, (list, tuple)):
        for index, item in enumerate(node):
            yield from _walk_scalars(item, tokens + (index,))
        return
    if _is_scalar(node):
        yield tokens, node


def _walk_empty_containers(
    node: Any,
    tokens: Tuple[Any, ...] = (),
) -> Iterable[Tuple[Tuple[Any, ...], Any]]:
    """Yield empty containers that cannot be represented by v1 scalar values."""
    if isinstance(node, Mapping):
        if not node and tokens:
            yield tokens, node
        for key in sorted(node, key=lambda item: str(item)):
            if str(key).startswith("_"):
                continue
            yield from _walk_empty_containers(node[key], tokens + (str(key),))
    elif isinstance(node, (list, tuple)):
        if not node and tokens:
            yield tokens, node
        for index, item in enumerate(node):
            yield from _walk_empty_containers(item, tokens + (index,))


def _assert_json_safe(value: Any, path: str = "$") -> None:
    """Reject non-finite numbers and non-JSON Python objects before validation."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EvaluationRecordV1Error(f"non-finite number at {path} is not allowed")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise EvaluationRecordV1Error(f"non-string object key at {path}: {key!r}")
            _assert_json_safe(child, f"{path}/{_pointer_escape(key)}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_json_safe(child, f"{path}/{index}")
        return
    raise EvaluationRecordV1Error(
        f"unsupported JSON value at {path}: {type(value).__name__}"
    )


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvaluationRecordV1Error(f"{name} must be a non-empty string")
    return value


def _date_time_with_offset(text: str) -> Optional[datetime]:
    """Parse an ISO/RFC 3339 date-time only when an explicit offset is present."""
    candidate = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _normalised_utc(parsed: datetime) -> str:
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _timestamp_reason(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def _timestamp_fact(
    kind: str,
    source_text: Any,
    *,
    evidence_refs: Sequence[str] = (),
) -> Dict[str, Any]:
    """Preserve a timestamp string and normalize only evidenced offsets."""
    refs = sorted(set(str(ref) for ref in evidence_refs if ref))
    text = source_text if isinstance(source_text, str) else str(source_text)
    known_date = False
    if kind == "SOURCE_VALUE_AS_OF" and len(text) == 10:
        try:
            known_date = date.fromisoformat(text).isoformat() == text
        except ValueError:
            known_date = False
    parsed = _date_time_with_offset(text)

    if known_date:
        return {
            "kind": kind,
            "state": "KNOWN",
            "source_text": text,
            "evidence_refs": refs,
        }
    if parsed is not None:
        return {
            "kind": kind,
            "state": "KNOWN",
            "source_text": text,
            "normalized_utc": _normalised_utc(parsed),
            "evidence_refs": refs,
        }

    parsed_naive: Optional[datetime] = None
    try:
        if "T" in text or " " in text:
            parsed_naive = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed_naive = None
    if parsed_naive is not None and parsed_naive.tzinfo is None:
        code = "TIMEZONE_UNRESOLVED"
        message = "The original timestamp has no evidenced timezone or UTC offset."
    else:
        code = "INVALID"
        message = "The original timestamp is not a recognized ISO/RFC 3339 date or date-time."
    return {
        "kind": kind,
        "state": "UNKNOWN",
        "source_text": text,
        "evidence_refs": refs,
        "reason": _timestamp_reason(code, message),
    }


def _timestamp_state_unknown(code: str, message: str) -> Dict[str, Any]:
    return {
        "state": "UNKNOWN",
        "evidence_refs": [],
        "reason": _timestamp_reason(code, message),
    }


def _local_source_id(base: str, occupied: Iterable[str]) -> str:
    used = set(occupied)
    candidate = base
    suffix = 1
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _append_finding(
    findings: List[Dict[str, Any]],
    code: str,
    message: str,
    *,
    field_path: Optional[str] = None,
    evidence_refs: Sequence[str] = (),
    severity: str = "WARNING",
) -> None:
    finding: Dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "evidence_refs": sorted(set(ref for ref in evidence_refs if ref)),
    }
    if field_path:
        finding["field_path"] = field_path
    findings.append(finding)


def _raw_input_document(record: Any) -> Mapping[str, Any]:
    snapshot = getattr(record, "input_snapshot", {}) or {}
    raw = snapshot.get("input", {}) if isinstance(snapshot, Mapping) else {}
    return raw if isinstance(raw, Mapping) else {}


def _record_evidence(record: Any) -> Mapping[str, Any]:
    evidence = getattr(record, "evidence", {}) or {}
    return evidence if isinstance(evidence, Mapping) else {}


def _record_sources(record: Any) -> List[Mapping[str, Any]]:
    items = _record_evidence(record).get("sources") or []
    return [item for item in items if isinstance(item, Mapping)]


def _record_evidence_items(record: Any) -> List[Mapping[str, Any]]:
    items = _record_evidence(record).get("evidence") or []
    return [item for item in items if isinstance(item, Mapping)]


def _source_registry_hash(evidence: Mapping[str, Any]) -> Optional[str]:
    sources = evidence.get("sources")
    evidence_items = evidence.get("evidence")
    if not isinstance(sources, list) or not isinstance(evidence_items, list):
        return None
    try:
        return sha256_of({"sources": sources, "evidence": evidence_items})
    except (TypeError, ValueError):
        return None


def _market_hash_subject(snapshot: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    blocks = snapshot.get("blocks")
    if not isinstance(blocks, list):
        return None
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "as_of": snapshot.get("as_of"),
        "staleness_hours": snapshot.get("staleness_hours"),
        "blocks": [
            {key: value for key, value in block.items() if key != "age_hours"}
            for block in blocks
            if isinstance(block, Mapping)
        ],
    }


def _peer_hash_subject(snapshot: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    observations = snapshot.get("observations")
    if not isinstance(observations, list):
        return None
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "as_of": snapshot.get("as_of"),
        "staleness_days": snapshot.get("staleness_days"),
        "min_listed_years": snapshot.get("min_listed_years"),
        "observations": [
            {key: value for key, value in observation.items() if key != "age_days"}
            for observation in observations
            if isinstance(observation, Mapping)
        ],
    }


def _result_hash_subject(record: Any) -> Mapping[str, Any]:
    return {
        "engine_version": record.engine_version,
        "spec_version": record.spec_version,
        "config_hash": record.config_hash,
        "input_snapshot_hash": record.input_snapshot_hash,
        "source_manifest_hash": record.source_manifest_hash,
        "market_snapshot_hash": record.market_snapshot_hash,
        "peer_snapshot_hash": record.peer_snapshot_hash,
        "mode": str(record.evaluation_mode).lower(),
        "plan": record.plan,
        "derived_metrics": record.derived_metrics,
        "knockouts": record.knockouts,
        "score": record.score,
        "penalties": [dict(item) for item in record.penalties],
        "missing_unverified": [dict(item) for item in record.missing_unverified],
    }


def _digest_entry(
    digest_id: str,
    digest_value: Any,
    *,
    local_subject_kind: Optional[str] = None,
    local_subject_ref: Optional[str] = None,
    locally_recomputed: bool = False,
    reason_message: str = "The legacy record does not establish this digest's algorithm, subject, or origin.",
) -> Dict[str, Any]:
    value = _require_text(digest_value, f"integrity digest {digest_id}.digest_value")
    if locally_recomputed and local_subject_kind and local_subject_ref:
        entry: Dict[str, Any] = {
            "digest_id": digest_id,
            "algorithm": "SHA-256",
            "digest_value": value,
            "subject_kind": local_subject_kind,
            "subject_ref": local_subject_ref,
            "origin": "LOCAL_COMPUTED",
            "evidence_refs": [],
        }
        if local_subject_kind in {"CANONICAL_JSON_OBJECT", "V1_5_RESULT_PAYLOAD"}:
            entry["canonicalization_id"] = CANONICALIZATION_ID
        return entry
    return {
        "digest_id": digest_id,
        "algorithm": "UNKNOWN",
        "digest_value": value,
        "subject_kind": "LEGACY_UNSPECIFIED",
        "subject_ref": "UNKNOWN",
        "origin": "LEGACY_UNRESOLVED",
        "evidence_refs": [],
        "reason": {
            "code": "LEGACY_UNRESOLVED",
            "message": reason_message,
            "evidence_refs": [],
        },
    }


def _build_integrity_digests(record: Any, sources: Sequence[Mapping[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    digests: List[Dict[str, Any]] = []
    by_source: Dict[str, str] = {}
    snapshot = getattr(record, "input_snapshot", {}) or {}
    evidence = _record_evidence(record)
    market = getattr(record, "market_snapshot", {}) or {}
    peers = getattr(record, "peer_snapshot", {}) or {}

    try:
        input_local = sha256_of(snapshot) == record.input_snapshot_hash
    except (TypeError, ValueError):
        input_local = False
    digests.append(
        _digest_entry(
            "input-snapshot",
            record.input_snapshot_hash,
            local_subject_kind="CANONICAL_JSON_OBJECT",
            local_subject_ref="input.json#snapshot",
            locally_recomputed=input_local,
        )
    )

    registry_hash = _source_registry_hash(evidence)
    source_local = registry_hash is not None and registry_hash == record.source_manifest_hash
    digests.append(
        _digest_entry(
            "source-manifest",
            record.source_manifest_hash,
            local_subject_kind="CANONICAL_JSON_OBJECT",
            local_subject_ref="evidence.json#sources+evidence",
            locally_recomputed=source_local,
        )
    )

    market_subject = _market_hash_subject(market) if isinstance(market, Mapping) else None
    try:
        market_local = (
            market_subject is not None
            and sha256_of(market_subject) == record.market_snapshot_hash
        )
    except (TypeError, ValueError):
        market_local = False
    digests.append(
        _digest_entry(
            "market-snapshot",
            record.market_snapshot_hash,
            local_subject_kind="CANONICAL_JSON_OBJECT",
            local_subject_ref="market.json#snapshot.hash_payload",
            locally_recomputed=market_local,
        )
    )

    peer_subject = _peer_hash_subject(peers) if isinstance(peers, Mapping) else None
    try:
        peers_local = (
            peer_subject is not None
            and sha256_of(peer_subject) == record.peer_snapshot_hash
        )
    except (TypeError, ValueError):
        peers_local = False
    digests.append(
        _digest_entry(
            "peer-snapshot",
            record.peer_snapshot_hash,
            local_subject_kind="CANONICAL_JSON_OBJECT",
            local_subject_ref="peers.json#snapshot.hash_payload",
            locally_recomputed=peers_local,
        )
    )

    try:
        result_local = sha256_of(_result_hash_subject(record)) == record.result_hash
    except (AttributeError, TypeError, ValueError):
        result_local = False
    digests.append(
        _digest_entry(
            "v1.5-result",
            record.result_hash,
            local_subject_kind="V1_5_RESULT_PAYLOAD",
            local_subject_ref="result_payload.v1.5",
            locally_recomputed=result_local,
        )
    )

    for source in sources:
        source_id = source.get("source_id")
        content_hash = source.get("content_hash")
        if isinstance(source_id, str) and isinstance(content_hash, str) and content_hash:
            digest_id = _stable_id("source-content-hash", source_id)
            by_source[source_id] = digest_id
            digests.append(
                _digest_entry(
                    digest_id,
                    content_hash,
                    reason_message=(
                        "The legacy SourceRef.content_hash is preserved verbatim, but its "
                        "algorithm, subject, and provenance are not established by the record."
                    ),
                )
            )
    return sorted(digests, key=lambda item: item["digest_id"]), by_source


def _source_timestamp_findings(
    sources: Sequence[Mapping[str, Any]],
    evidence_items: Sequence[Mapping[str, Any]],
    findings: List[Dict[str, Any]],
) -> None:
    evidence_by_source: Dict[str, List[str]] = {}
    for item in evidence_items:
        source_id = item.get("source_id")
        evidence_id = item.get("evidence_id")
        if isinstance(source_id, str) and isinstance(evidence_id, str):
            evidence_by_source.setdefault(source_id, []).append(evidence_id)
    for index, source in enumerate(sources):
        source_text = source.get("source_timestamp")
        if source_text is None:
            continue
        source_id = str(source.get("source_id") or "")
        _append_finding(
            findings,
            "LEGACY_SOURCE_TIMESTAMP_UNCLASSIFIED",
            (
                "The legacy source_timestamp is retained in evidence.json but is not assigned "
                "an A15 timestamp kind because its source-event, value-as-of, and publication "
                "semantics are not distinguished."
            ),
            field_path=f"evidence.json#/evidence/sources/{index}/source_timestamp",
            evidence_refs=evidence_by_source.get(source_id, []),
        )


def _source_object(source: Mapping[str, Any]) -> Dict[str, Any]:
    source_id = _require_text(source.get("source_id"), "source.source_id")
    source_type = source.get("source_type")
    if not isinstance(source_type, str) or not source_type:
        source_type = "UNKNOWN"
    out: Dict[str, Any] = {
        "source_id": source_id,
        "source_type": source_type,
        "timestamps": [],
    }
    for key in ("uri", "source_record_id", "source_revision_id"):
        value = source.get(key)
        if isinstance(value, str) and value:
            out[key] = value
    retrieval = source.get("retrieval_timestamp")
    if retrieval is not None:
        out["timestamps"].append(
            _timestamp_fact("LOCAL_RETRIEVED_AT", retrieval)
        )
    out["timestamps"].sort(
        key=lambda item: (item["kind"], item.get("source_text", ""))
    )
    return out


def _input_evidence_id(path: str) -> str:
    return _stable_id("A15-INPUT", path)


def _result_evidence_id(path: str) -> str:
    return _stable_id("A15-RESULT", path)


def _external_evidence_object(
    raw: Mapping[str, Any],
    *,
    index: int,
    source_ids: set[str],
    findings: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    evidence_id_value = raw.get("evidence_id")
    if not isinstance(evidence_id_value, str) or not evidence_id_value:
        raw_json = json.dumps(raw, sort_keys=True, ensure_ascii=False, allow_nan=False)
        evidence_id_value = _stable_id("A15-LEGACY-EVIDENCE", f"{index}:{raw_json}")
        _append_finding(
            findings,
            "LEGACY_EVIDENCE_ID_MISSING",
            "A legacy evidence entry has no evidence_id; a stable local reference was assigned.",
            field_path=f"/evidence/{index}",
        )
    evidence_id = evidence_id_value
    source_id = raw.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        _append_finding(
            findings,
            "LEGACY_EVIDENCE_SOURCE_MISSING",
            "A legacy evidence entry has no source_id and cannot be linked to an external source.",
            field_path=f"/evidence/{index}",
        )
        return None
    if source_id not in source_ids:
        # This preserves the unresolved reference without assigning a provider.
        source_ids.add(source_id)
        _append_finding(
            findings,
            "EVIDENCE_SOURCE_UNREGISTERED",
            "The legacy evidence source_id is not registered; source_type remains UNKNOWN.",
            field_path=f"/evidence/{index}/source_id",
            evidence_refs=[evidence_id],
        )

    locator = raw.get("locator")
    if not isinstance(locator, str) or not locator:
        locator = f"evidence.json#/evidence/evidence/{index}"
        _append_finding(
            findings,
            "LEGACY_EVIDENCE_LOCATOR_MISSING",
            "No source locator is present; the output points to the preserved evidence artifact entry.",
            field_path=f"/evidence/{index}/locator",
            evidence_refs=[evidence_id],
        )
    extraction_method = raw.get("extraction_method")
    if not isinstance(extraction_method, str) or not extraction_method:
        extraction_method = "UNKNOWN"
        _append_finding(
            findings,
            "LEGACY_EXTRACTION_METHOD_MISSING",
            "The legacy evidence entry does not retain an extraction method.",
            field_path=f"/evidence/{index}/extraction_method",
            evidence_refs=[evidence_id],
        )
    out: Dict[str, Any] = {
        "evidence_id": evidence_id,
        "source_id": source_id,
        "locator": locator,
        "extraction_method": extraction_method,
        "timestamps": [],
        "artifact_ref": f"evidence.json#/evidence/evidence/{index}",
    }
    confidence = raw.get("extraction_confidence", raw.get("confidence"))
    if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
        out["confidence"] = confidence
    as_of = raw.get("as_of")
    if as_of is not None:
        out["timestamps"].append(
            _timestamp_fact(
                "SOURCE_VALUE_AS_OF",
                as_of,
                evidence_refs=[evidence_id],
            )
        )
    out["timestamps"].sort(
        key=lambda item: (item["kind"], item.get("source_text", ""))
    )
    return out


def _normalization_for_input_field(
    tokens: Sequence[Any],
    raw_value: Any,
    snapshot: Mapping[str, Any],
    spec_version: str,
) -> Tuple[Any, Optional[str], Optional[str], Dict[str, Any], bool]:
    """Return normalized value/unit/profile; the final flag is availability."""
    monetary = False
    normalized: Any = raw_value
    raw_unit: Optional[str] = None
    normalized_unit: Optional[str] = None
    field_name = str(tokens[-1]) if tokens else ""
    if (
        len(tokens) >= 4
        and tokens[0] == "financials"
        and tokens[1] == "periods"
        and isinstance(tokens[2], int)
        and field_name in MONETARY_FIELDS
    ):
        period_index = tokens[2]
        periods = snapshot.get("periods") or []
        if period_index < len(periods) and isinstance(periods[period_index], Mapping):
            normalized = periods[period_index].get(field_name)
            monetary = True
    elif (
        tuple(tokens) in {
            ("issue", "fresh_issue"),
            ("issue", "ofs"),
            ("financials", "contingent_liabilities"),
        }
        or (
            len(tokens) == 3
            and tokens[0] == "use_of_proceeds"
            and isinstance(tokens[1], int)
            and tokens[2] == "amount"
        )
    ):
        factor = snapshot.get("unit_factor")
        if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool) and isinstance(factor, (int, float)):
            normalized = float(raw_value) * float(factor)
            monetary = True
        else:
            return None, None, None, {
                "kind": "IDENTITY"
            }, False

    if monetary:
        raw_input = snapshot.get("input") or {}
        financials = raw_input.get("financials", {}) if isinstance(raw_input, Mapping) else {}
        raw_unit_value = (
            financials.get("reporting_unit")
            if isinstance(financials, Mapping)
            else None
        )
        raw_unit = raw_unit_value if isinstance(raw_unit_value, str) and raw_unit_value else None
        normalized_unit = "INR_CRORES"
        normalization = {
            "kind": "NORMALIZED",
            "formula_id": "UNIT_TO_CRORE",
            "formula_version": spec_version,
            "input_field_refs": [_json_pointer(tokens)],
        }
        return normalized, raw_unit, normalized_unit, normalization, normalized is not None
    return raw_value, None, None, {"kind": "IDENTITY"}, True


def _input_field_rows(
    record: Any,
    *,
    input_source_id: str,
    legacy_evidence_by_id: Mapping[str, Mapping[str, Any]],
    evidence_objects: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    snapshot = getattr(record, "input_snapshot", {}) or {}
    raw = _raw_input_document(record)
    spec_version = _require_text(getattr(record, "spec_version", ""), "record.spec_version")
    observations: List[Dict[str, Any]] = []
    field_values: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []

    for tokens, raw_value in _walk_scalars(raw):
        pointer = _json_pointer(tokens)
        legacy_path = _legacy_path(tokens)
        local_evidence_id = _input_evidence_id(pointer)
        evidence_refs = [local_evidence_id]
        fallback_id = f"EV-{legacy_path}"
        if fallback_id in legacy_evidence_by_id:
            evidence_refs.append(fallback_id)
        evidence_refs = sorted(set(evidence_refs))
        observation_id = _stable_id("A15-OBS", pointer)
        evidence_objects.append(
            {
                "evidence_id": local_evidence_id,
                "source_id": input_source_id,
                "locator": f"input.json#/snapshot/input{pointer[len('/input'):]}",
                "extraction_method": "STRUCTURED_INPUT",
                "timestamps": [],
                "artifact_ref": "input.json",
            }
        )
        if raw_value is None:
            observation: Dict[str, Any] = {
                "observation_id": observation_id,
                "field_path": pointer,
                "source_id": input_source_id,
                "evidence_refs": evidence_refs,
                "value_state": "UNKNOWN",
                "timestamps": [],
                "reason": {
                    "code": "MISSING",
                    "message": "The frozen v1.5 input snapshot contains null; no zero or substitute is recorded.",
                    "evidence_refs": evidence_refs,
                },
            }
            field_value: Dict[str, Any] = {
                "field_path": pointer,
                "value_state": "UNKNOWN",
                "verification_status": "UNVERIFIED",
                "qualification_status": "PENDING",
                "source_observation_ids": [observation_id],
                "evidence_refs": evidence_refs,
                "reason": {
                    "code": "MISSING",
                    "message": "The frozen input value is null; the canonical value remains UNKNOWN.",
                    "evidence_refs": evidence_refs,
                },
            }
        else:
            observation = {
                "observation_id": observation_id,
                "field_path": pointer,
                "source_id": input_source_id,
                "evidence_refs": evidence_refs,
                "value_state": "VALUE",
                "raw_value": raw_value,
                "timestamps": [],
            }
            normalized, raw_unit, normalized_unit, normalization, available = (
                _normalization_for_input_field(tokens, raw_value, snapshot, spec_version)
            )
            if not available:
                field_value = {
                    "field_path": pointer,
                    "value_state": "UNKNOWN",
                    "verification_status": "UNVERIFIED",
                    "qualification_status": "PENDING",
                    "source_observation_ids": [observation_id],
                    "evidence_refs": evidence_refs,
                    "reason": {
                        "code": "UNAVAILABLE",
                        "message": (
                            "The raw source value is preserved as an observation, but the legacy "
                            "record does not provide the canonical normalized value."
                        ),
                        "evidence_refs": evidence_refs,
                    },
                }
            else:
                field_value = {
                    "field_path": pointer,
                    "value_state": "VALUE",
                    "value_origin": "SOURCE",
                    "raw_value": raw_value,
                    "normalized_value": normalized,
                    "normalization": normalization,
                    "verification_status": "UNVERIFIED",
                    "qualification_status": "PENDING",
                    "source_observation_ids": [observation_id],
                    "evidence_refs": evidence_refs,
                    "reason": {
                        "code": "UNVERIFIED",
                        "message": (
                            "The legacy EvaluationRecord does not retain field-level verification "
                            "or source-qualification status; this value remains UNVERIFIED and PENDING."
                        ),
                        "evidence_refs": evidence_refs,
                    },
                }
                if raw_unit:
                    field_value["raw_unit"] = raw_unit
                if normalized_unit:
                    field_value["normalized_unit"] = normalized_unit
        observations.append(observation)
        field_values.append(field_value)

    for tokens, _empty_value in _walk_empty_containers(raw):
        pointer = _json_pointer(tokens)
        local_evidence_id = _input_evidence_id(pointer)
        evidence_objects.append(
            {
                "evidence_id": local_evidence_id,
                "source_id": input_source_id,
                "locator": f"input.json#/snapshot/input{pointer[len('/input'):]}",
                "extraction_method": "STRUCTURED_INPUT",
                "timestamps": [],
                "artifact_ref": "input.json",
            }
        )
        _append_finding(
            findings,
            "LEGACY_NONSCALAR_FIELD_PRESERVED_BY_REFERENCE",
            (
                "This empty JSON container cannot be represented by the v1 scalar field-value "
                "shape; its exact value remains in input.json."
            ),
            field_path=pointer,
            evidence_refs=[local_evidence_id],
        )

    observations.sort(key=lambda item: (item["field_path"], item["observation_id"]))
    field_values.sort(key=lambda item: item["field_path"])
    return observations, field_values, findings


def _result_artifact_evidence(
    record: Any,
    *,
    result_source_id: str,
    evidence_objects: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    knockouts = getattr(record, "knockouts", {}) or {}
    results = knockouts.get("results", []) if isinstance(knockouts, Mapping) else []
    output_knockouts: List[Dict[str, Any]] = []
    unverified_refs: List[str] = []
    for index, result in enumerate(results or []):
        if not isinstance(result, Mapping):
            continue
        rule_id = _require_text(result.get("rule_id"), "knockout.rule_id")
        state = _require_text(result.get("state"), f"knockout {rule_id}.state")
        pointer = f"result.json#/knockouts/results/{index}"
        evidence_id = _result_evidence_id(pointer)
        evidence_objects.append(
            {
                "evidence_id": evidence_id,
                "source_id": result_source_id,
                "locator": pointer,
                "extraction_method": "DERIVED",
                "timestamps": [],
                "artifact_ref": "result.json",
            }
        )
        item = {
            "rule_id": rule_id,
            "state": state,
            "evidence_refs": [evidence_id],
            "missing_input_refs": sorted(
                set(str(value) for value in (result.get("missing") or []) if value is not None)
            ),
        }
        output_knockouts.append(item)
        if state == "UNVERIFIED":
            unverified_refs.append(evidence_id)

    missing_rows = list(getattr(record, "missing_unverified", ()) or ())
    critical_refs: List[str] = []
    for index, missing in enumerate(missing_rows):
        if not isinstance(missing, Mapping) or missing.get("category") != "CRITICAL_DATA":
            continue
        pointer = f"result.json#/missing_unverified/{index}"
        evidence_id = _result_evidence_id(pointer)
        evidence_objects.append(
            {
                "evidence_id": evidence_id,
                "source_id": result_source_id,
                "locator": pointer,
                "extraction_method": "DERIVED",
                "timestamps": [],
                "artifact_ref": "result.json",
            }
        )
        critical_refs.append(evidence_id)

    score = getattr(record, "score", {}) or {}
    breakdown = score.get("completeness_breakdown") if isinstance(score, Mapping) else None
    critical_names = list(breakdown.get("critical_data_missing") or []) if isinstance(breakdown, Mapping) else []
    if critical_names and not critical_refs:
        for index, _name in enumerate(critical_names):
            if not _name:
                continue
            pointer = f"result.json#/score/completeness_breakdown/critical_data_missing/{index}"
            evidence_id = _result_evidence_id(pointer)
            evidence_objects.append(
                {
                    "evidence_id": evidence_id,
                    "source_id": result_source_id,
                    "locator": pointer,
                    "extraction_method": "DERIVED",
                    "timestamps": [],
                    "artifact_ref": "result.json",
                }
            )
            critical_refs.append(evidence_id)

    output_knockouts.sort(key=lambda item: (item["rule_id"], item["state"]))
    return output_knockouts, sorted(set(unverified_refs)), sorted(set(critical_refs))


def _critical_safety(record: Any, available_refs: Sequence[str]) -> Dict[str, Any]:
    score = getattr(record, "score", {}) or {}
    missing = []
    breakdown = score.get("completeness_breakdown") if isinstance(score, Mapping) else None
    if isinstance(breakdown, Mapping):
        missing = list(breakdown.get("critical_data_missing") or [])
    if not missing:
        missing = [
            item.get("item")
            for item in (getattr(record, "missing_unverified", ()) or ())
            if isinstance(item, Mapping)
            and item.get("category") == "CRITICAL_DATA"
            and item.get("item")
        ]
    missing = sorted(set(str(item) for item in missing if item))
    if missing:
        refs = sorted(set(available_refs))
        reason = "Configured v1.5 critical-data inputs are UNKNOWN: " + ", ".join(missing)
        if not refs:
            reason += "; the legacy result does not retain resolvable evidence references for these items."
        return {
            "status": "INCOMPLETE",
            "missing_evidence_refs": refs,
            "reason": reason,
        }
    if bool(score.get("insufficient_data")):
        return {
            "status": "UNKNOWN",
            "missing_evidence_refs": sorted(set(available_refs)),
            "reason": (
                "The legacy score marks insufficient_data, but the persisted record does not "
                "identify the critical-safety evidence reference."
            ),
        }
    return {
        "status": "COMPLETE",
        "missing_evidence_refs": [],
        "reason": (
            "Configured v1.5 critical-data items are present. This is the existing data-completeness "
            "check only; it does not assert field-level verification or source qualification."
        ),
    }


def _validation_projection(
    record: Any,
    findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    legacy = getattr(record, "validation", {}) or {}
    if not isinstance(legacy, Mapping):
        legacy = {}
    schema_status = legacy.get("schema_status")
    # A pipeline EvaluationRecord can exist only after input Draft 2020-12
    # validation succeeds. This does not describe validation of the new file.
    if schema_status not in {"NOT_RUN", "PASSED", "FAILED"}:
        schema_status = "PASSED"
    semantic_ok = legacy.get("ok")
    if semantic_ok is True:
        semantic_status = "PASSED"
    elif semantic_ok is False:
        semantic_status = "FAILED"
    else:
        semantic_status = legacy.get("semantic_status", "NOT_RUN")
        if semantic_status not in {"NOT_RUN", "PASSED", "FAILED"}:
            semantic_status = "NOT_RUN"

    for section, fallback_severity in (("errors", "ERROR"), ("warnings", "WARNING")):
        for index, item in enumerate(legacy.get(section, []) or []):
            if not isinstance(item, Mapping):
                continue
            code = item.get("code")
            message = item.get("message")
            if not isinstance(code, str) or not code:
                code = "LEGACY_VALIDATION_FINDING"
            if not isinstance(message, str) or not message:
                message = "A legacy validation finding has no message."
            severity = item.get("severity", fallback_severity)
            if severity not in {"INFO", "WARNING", "ERROR"}:
                severity = fallback_severity
            finding: Dict[str, Any] = {
                "code": code,
                "severity": severity,
                "message": message,
                "evidence_refs": [],
            }
            location = item.get("location", item.get("field_path"))
            if isinstance(location, str) and location:
                finding["field_path"] = location
            findings.append(finding)
    deduplicated: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    for item in findings:
        key = (
            item.get("code", ""),
            item.get("severity", ""),
            item.get("field_path", ""),
            item.get("message", ""),
        )
        deduplicated[key] = item
    ordered = sorted(
        deduplicated.values(),
        key=lambda item: (
            item.get("code", ""),
            item.get("field_path", ""),
            item.get("message", ""),
            item.get("severity", ""),
        ),
    )
    return {
        "schema_status": schema_status,
        "semantic_status": semantic_status,
        "findings": ordered,
    }


def _project_evaluation_record(record: Any) -> Dict[str, Any]:
    legacy_sources = _record_sources(record)
    legacy_evidence = _record_evidence_items(record)
    findings: List[Dict[str, Any]] = []

    source_by_id: Dict[str, Dict[str, Any]] = {}
    raw_source_by_id: Dict[str, Mapping[str, Any]] = {}
    for source in legacy_sources:
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            _append_finding(
                findings,
                "LEGACY_SOURCE_ID_MISSING",
                "A legacy source entry without source_id is preserved only in evidence.json.",
                field_path="/sources",
            )
            continue
        if source_id in raw_source_by_id and raw_source_by_id[source_id] != source:
            raise EvaluationRecordV1Error(
                f"source_id {source_id!r} appears more than once with conflicting metadata"
            )
        raw_source_by_id[source_id] = source

    for raw_source in legacy_sources:
        source_id = raw_source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            continue
        # Source content hashes are attached after projection and are never
        # promoted to a provider or trust assertion.
        source_by_id[source_id] = _source_object(raw_source)

    occupied_source_ids = set(source_by_id)
    occupied_source_ids.update(
        item.get("source_id")
        for item in legacy_evidence
        if isinstance(item.get("source_id"), str) and item.get("source_id")
    )
    input_source_id = _local_source_id("A15-LOCAL-INPUT", occupied_source_ids)
    occupied_source_ids.add(input_source_id)
    result_source_id = _local_source_id("A15-LOCAL-RESULT", occupied_source_ids)
    source_by_id[input_source_id] = {
        "source_id": input_source_id,
        "source_type": "STRUCTURED_INPUT",
        "timestamps": [],
    }
    source_by_id[result_source_id] = {
        "source_id": result_source_id,
        "source_type": "DERIVED",
        "timestamps": [],
    }

    # Any evidence whose source registration is absent remains explicitly
    # unresolved; the placeholder is local metadata, not a provider identity.
    source_ids = set(source_by_id)
    for item in legacy_evidence:
        source_id = item.get("source_id")
        if isinstance(source_id, str) and source_id and source_id not in source_ids:
            source_by_id[source_id] = {
                "source_id": source_id,
                "source_type": "UNKNOWN",
                "timestamps": [],
            }
            source_ids.add(source_id)
            _append_finding(
                findings,
                "EVIDENCE_SOURCE_UNREGISTERED",
                "The legacy evidence source_id is not declared in the source registry; its type remains UNKNOWN.",
                field_path=f"/evidence/{_pointer_escape(item.get('evidence_id') or '')}/source_id",
                evidence_refs=[str(item.get("evidence_id"))] if item.get("evidence_id") else [],
            )

    digests, source_digest_refs = _build_integrity_digests(record, legacy_sources)
    for source_id, digest_id in source_digest_refs.items():
        if source_id in source_by_id:
            source_by_id[source_id]["digest_refs"] = [digest_id]

    evidence_objects: List[Dict[str, Any]] = []
    evidence_id_set: set[str] = set()
    for index, raw_item in enumerate(legacy_evidence):
        output = _external_evidence_object(
            raw_item,
            index=index,
            source_ids=source_ids,
            findings=findings,
        )
        if output is None:
            continue
        evidence_id = output["evidence_id"]
        if evidence_id in evidence_id_set:
            raise EvaluationRecordV1Error(f"duplicate evidence_id {evidence_id!r}")
        evidence_id_set.add(evidence_id)
        if output["source_id"] not in source_by_id:
            source_by_id[output["source_id"]] = {
                "source_id": output["source_id"],
                "source_type": "UNKNOWN",
                "timestamps": [],
            }
        evidence_objects.append(output)

    legacy_evidence_by_id = {
        str(item.get("evidence_id")): item
        for item in legacy_evidence
        if isinstance(item.get("evidence_id"), str) and item.get("evidence_id")
    }
    observations, field_values, input_findings = _input_field_rows(
        record,
        input_source_id=input_source_id,
        legacy_evidence_by_id=legacy_evidence_by_id,
        evidence_objects=evidence_objects,
    )
    findings.extend(input_findings)

    # Record the limited, known evidence mapping without treating the
    # evidence registry as a complete field-path map.
    has_external_evidence = bool(legacy_evidence)
    if has_external_evidence:
        _append_finding(
            findings,
            "LEGACY_FIELD_EVIDENCE_MAPPING_INCOMPLETE",
            (
                "The legacy EvaluationRecord retains the evidence registry but not the original "
                "field-path map. Only generated EV-<path> IDs are linked; other evidence remains "
                "available through evidence.json and is not assigned to a field by inference."
            ),
        )
    _source_timestamp_findings(legacy_sources, legacy_evidence, findings)

    knockout_rows, unverified_knockout_refs, critical_refs = _result_artifact_evidence(
        record,
        result_source_id=result_source_id,
        evidence_objects=evidence_objects,
    )
    critical_safety = _critical_safety(record, critical_refs)

    # Add an auditable diagnostic if the legacy score says insufficient data
    # but the missing critical reference list is not recoverable.
    if critical_safety["status"] == "UNKNOWN" and not critical_safety["missing_evidence_refs"]:
        _append_finding(
            findings,
            "CRITICAL_SAFETY_REFERENCE_UNAVAILABLE",
            critical_safety["reason"],
            field_path="/result/critical_safety",
        )

    score = getattr(record, "score", {}) or {}
    verdict = getattr(record, "verdict", {}) or {}
    if not isinstance(score, Mapping):
        score = {}
    if not isinstance(verdict, Mapping):
        verdict = {}
    score_verdict_value = score.get("verdict", verdict.get("verdict"))
    if score_verdict_value is None:
        score_verdict_value = verdict.get("verdict")
    score_verdict_value = _require_text(score_verdict_value, "score.verdict")
    uncertain = score.get("verdict_uncertain", verdict.get("uncertain", False))
    insufficient_data = score.get("insufficient_data", verdict.get("insufficient_data", False))
    if not isinstance(uncertain, bool):
        raise EvaluationRecordV1Error("score.verdict_uncertain must be a boolean")
    if not isinstance(insufficient_data, bool):
        raise EvaluationRecordV1Error("score.insufficient_data must be a boolean")

    result: Dict[str, Any] = {
        "outcome_resolution": {"state": "TERMINAL"},
        "knockouts": knockout_rows,
        "critical_safety": critical_safety,
        "score": {
            key: score.get(key)
            for key in (
                "base_score",
                "final_score",
                "completeness_pct",
                "available_points",
                "unknown_points",
                "total_evaluable_points",
                "unresolved_penalty_points",
            )
        },
        "score_interval": {},
        "score_verdict": {
            "value": score_verdict_value,
            "uncertain": uncertain,
            "insufficient_data": insufficient_data,
        },
        "diagnostics": [],
    }
    result["score"]["completeness_pct"] = score.get("completeness_pct")
    score_range = getattr(record, "score_range", {}) or {}
    lower = score_range.get("lower_bound") if isinstance(score_range, Mapping) else None
    upper = score_range.get("upper_bound") if isinstance(score_range, Mapping) else None
    if isinstance(lower, (int, float)) and not isinstance(lower, bool) and isinstance(upper, (int, float)) and not isinstance(upper, bool):
        result["score_interval"] = {
            "state": "AVAILABLE",
            "lower_bound": lower,
            "upper_bound": upper,
        }
    else:
        result["score_interval"] = {"state": "UNKNOWN"}

    # A7 precedence: triggered knockout, then missing critical-safety data,
    # then the unverified-only nonterminal state, then the configured v1.5
    # verdict unchanged. Diagnostics and score_verdict remain independent.
    if any(item["state"] == "TRIGGERED" for item in knockout_rows):
        result["final_outcome"] = "AVOID"
    elif critical_safety["status"] != "COMPLETE":
        result["final_outcome"] = "INSUFFICIENT_DATA"
    elif any(item["state"] == "UNVERIFIED" for item in knockout_rows):
        result["outcome_resolution"] = {
            "state": "NONTERMINAL_UNRESOLVED",
            "reason": {
                "code": "UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT",
                "evidence_refs": unverified_knockout_refs,
            },
        }
        # The property is intentionally absent for this nonterminal case.
    else:
        configured_verdict = _require_text(verdict.get("verdict"), "verdict.verdict")
        result["final_outcome"] = configured_verdict

    if uncertain:
        result["diagnostics"].append(
            {
                "code": "VERDICT_UNCERTAIN",
                "message": "The existing v1.5 score interval crosses configured verdict bands.",
                "evidence_refs": [],
            }
        )
    if insufficient_data:
        result["diagnostics"].append(
            {
                "code": "INSUFFICIENT_DATA",
                "message": "The existing v1.5 score marks one or more configured critical inputs unavailable.",
                "evidence_refs": critical_safety["missing_evidence_refs"],
            }
        )
    result["diagnostics"].sort(key=lambda item: (item["code"], item["message"]))

    source_objects = sorted(
        source_by_id.values(),
        key=lambda item: item["source_id"],
    )
    evidence_objects.sort(key=lambda item: item["evidence_id"])
    evidence_ids = [item["evidence_id"] for item in evidence_objects]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise EvaluationRecordV1Error("duplicate evidence_id after projecting local artifact references")

    # A schema-valid record exists only after the pipeline's input-schema gate;
    # a single global evaluation cutoff is not stored in the legacy model.
    evaluation_cutoff = _timestamp_state_unknown(
        "UNAVAILABLE",
        "No single global cutoff is stored in the legacy record; do not substitute evaluation or retrieval time.",
    )
    evaluation_timestamp = _require_text(
        getattr(record, "evaluation_timestamp", None), "record.evaluation_timestamp"
    )
    record_section = {
        "evaluation_id": _require_text(getattr(record, "evaluation_id", None), "record.evaluation_id"),
        "ipo_id": _require_text(getattr(record, "ipo_id", None), "record.ipo_id"),
        "company_name": _require_text(getattr(record, "company_name", None), "record.company_name"),
        "engine_version": _require_text(getattr(record, "engine_version", None), "record.engine_version"),
        "spec_version": _require_text(getattr(record, "spec_version", None), "record.spec_version"),
        "config_version": _require_text(getattr(record, "config_version", None), "record.config_version"),
        "config_hash": _require_text(getattr(record, "config_hash", None), "record.config_hash"),
    }
    payload: Dict[str, Any] = {
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "serialization_profile": {
            "profile_id": SERIALIZATION_PROFILE_ID,
            "encoding": "UTF-8",
            "indent": 2,
            "sort_keys": True,
            "ensure_ascii": False,
            "line_ending": "LF",
            "final_newline": True,
            "string_normalization": "PRESERVE_SOURCE_TEXT",
            "non_finite_numbers": "REJECT",
            "array_order": "stable-id/path; timestamp-kind/source-text",
        },
        "record": record_section,
        "evaluation": {
            "mode": _require_text(getattr(record, "evaluation_mode", None), "record.evaluation_mode"),
            "evaluated_at": evaluation_timestamp,
            "evaluation_cutoff": evaluation_cutoff,
            "processing_status": "COMPLETED",
            "validation": _validation_projection(record, findings),
        },
        "sources": source_objects,
        "evidence": evidence_objects,
        "observations": observations,
        "field_values": field_values,
        "adjudications": [],
        "snapshots": {
            "input_snapshot_hash": _require_text(getattr(record, "input_snapshot_hash", None), "record.input_snapshot_hash"),
            "source_manifest_hash": _require_text(getattr(record, "source_manifest_hash", None), "record.source_manifest_hash"),
            "market_snapshot_hash": _require_text(getattr(record, "market_snapshot_hash", None), "record.market_snapshot_hash"),
            "peer_snapshot_hash": _require_text(getattr(record, "peer_snapshot_hash", None), "record.peer_snapshot_hash"),
            "artifact_refs": {
                "input": "input.json",
                "evidence": "evidence.json",
                "market": "market.json",
                "peers": "peers.json",
                "result": "result.json",
                "manifest": "manifest.json",
            },
        },
        "result": result,
        "integrity": {"digests": digests},
    }
    _assert_json_safe(payload)
    return payload


def _validate_references(document: Mapping[str, Any]) -> None:
    sources = document["sources"]
    evidence = document["evidence"]
    observations = document["observations"]
    field_values = document["field_values"]
    adjudications = document["adjudications"]
    digests = document["integrity"]["digests"]

    def unique(items: Sequence[Mapping[str, Any]], key: str, namespace: str) -> set[str]:
        values = [item[key] for item in items]
        if len(values) != len(set(values)):
            raise EvaluationRecordV1Error(f"duplicate {namespace} in canonical evaluation record")
        return set(values)

    source_ids = unique(sources, "source_id", "source_id")
    evidence_ids = unique(evidence, "evidence_id", "evidence_id")
    observation_ids = unique(observations, "observation_id", "observation_id")
    adjudication_ids = unique(adjudications, "adjudication_id", "adjudication_id")
    digest_ids = unique(digests, "digest_id", "digest_id")
    field_paths = [item["field_path"] for item in field_values]
    if len(field_paths) != len(set(field_paths)):
        raise EvaluationRecordV1Error("duplicate field_path in field_values")

    def require_refs(refs: Sequence[str], valid: set[str], label: str) -> None:
        unknown = sorted(set(refs) - valid)
        if unknown:
            raise EvaluationRecordV1Error(f"unresolved {label} reference(s): {unknown}")

    def check_timestamp_refs(timestamp: Mapping[str, Any]) -> None:
        require_refs(timestamp.get("evidence_refs", []), evidence_ids, "timestamp evidence")

    def check_reason_refs(reason: Optional[Mapping[str, Any]]) -> None:
        if reason is not None:
            require_refs(reason.get("evidence_refs", []), evidence_ids, "reason evidence")

    for source in sources:
        require_refs(source.get("digest_refs", []), digest_ids, "digest")
        for timestamp in source["timestamps"]:
            check_timestamp_refs(timestamp)
    for item in evidence:
        if item["source_id"] not in source_ids:
            raise EvaluationRecordV1Error(f"evidence {item['evidence_id']!r} has unknown source_id")
        for timestamp in item["timestamps"]:
            check_timestamp_refs(timestamp)
    for observation in observations:
        if observation["source_id"] not in source_ids:
            raise EvaluationRecordV1Error(
                f"observation {observation['observation_id']!r} has unknown source_id"
            )
        require_refs(observation["evidence_refs"], evidence_ids, "observation evidence")
        for timestamp in observation["timestamps"]:
            check_timestamp_refs(timestamp)
        check_reason_refs(observation.get("reason"))
    for field_value in field_values:
        require_refs(field_value["source_observation_ids"], observation_ids, "source observation")
        require_refs(field_value["evidence_refs"], evidence_ids, "field evidence")
        check_reason_refs(field_value.get("reason"))
        normalization = field_value.get("normalization") or {}
        require_refs(normalization.get("input_field_refs", []), set(field_paths), "input field")
        if normalization.get("kind") == "IDENTITY":
            raw_value = field_value["raw_value"]
            normalized_value = field_value["normalized_value"]
            if type(raw_value) is not type(normalized_value) or raw_value != normalized_value:
                raise EvaluationRecordV1Error(
                    f"identity normalization disagrees for field {field_value['field_path']!r}"
                )
        if field_value["value_state"] == "NOT_APPLICABLE" and field_value["qualification_status"] != "NOT_APPLICABLE":
            raise EvaluationRecordV1Error(
                f"NOT_APPLICABLE field {field_value['field_path']!r} must have NOT_APPLICABLE qualification"
            )
    for item in adjudications:
        require_refs(item["competing_observation_ids"], observation_ids, "competing observation")
        require_refs(item["authorization_evidence_refs"], evidence_ids, "adjudication evidence")
        if item.get("selected_observation_id") and item["selected_observation_id"] not in item["competing_observation_ids"]:
            raise EvaluationRecordV1Error("adjudication selected_observation_id is not a competing observation")
    validation = document["evaluation"]["validation"]
    for finding in validation["findings"]:
        require_refs(finding["evidence_refs"], evidence_ids, "validation evidence")
    cutoff = document["evaluation"]["evaluation_cutoff"]
    require_refs(cutoff["evidence_refs"], evidence_ids, "evaluation cutoff evidence")
    check_reason_refs(cutoff.get("reason"))

    result = document["result"]
    for knockout in result["knockouts"]:
        require_refs(knockout["evidence_refs"], evidence_ids, "knockout evidence")
    require_refs(result["critical_safety"]["missing_evidence_refs"], evidence_ids, "critical safety evidence")
    for diagnostic in result["diagnostics"]:
        require_refs(diagnostic["evidence_refs"], evidence_ids, "diagnostic evidence")
    outcome_reason = result["outcome_resolution"].get("reason")
    if outcome_reason is not None:
        require_refs(outcome_reason["evidence_refs"], evidence_ids, "outcome evidence")
    for digest in digests:
        require_refs(digest["evidence_refs"], evidence_ids, "digest evidence")
        check_reason_refs(digest.get("reason"))


def _validate_outcome(document: Mapping[str, Any]) -> None:
    result = document["result"]
    knockouts = result["knockouts"]
    triggered = any(item["state"] == "TRIGGERED" for item in knockouts)
    unverified = [item for item in knockouts if item["state"] == "UNVERIFIED"]
    critical_status = result["critical_safety"]["status"]
    resolution = result["outcome_resolution"]

    if triggered:
        if resolution["state"] != "TERMINAL" or result.get("final_outcome") != "AVOID":
            raise EvaluationRecordV1Error("A7 triggered-knockout precedence requires terminal AVOID")
        return
    if critical_status != "COMPLETE":
        if resolution["state"] != "TERMINAL" or result.get("final_outcome") != "INSUFFICIENT_DATA":
            raise EvaluationRecordV1Error("A7 critical-safety precedence requires terminal INSUFFICIENT_DATA")
        return
    if unverified:
        if resolution["state"] != "NONTERMINAL_UNRESOLVED" or "final_outcome" in result:
            raise EvaluationRecordV1Error(
                "A7 unverified-only case must be nonterminal and omit final_outcome"
            )
        reason = resolution.get("reason") or {}
        if reason.get("code") != "UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT":
            raise EvaluationRecordV1Error("A7 unverified-only case has the wrong reason code")
        required = {
            evidence_id
            for item in unverified
            for evidence_id in item.get("evidence_refs", [])
        }
        if not required.issubset(set(reason.get("evidence_refs", []))):
            raise EvaluationRecordV1Error(
                "A7 unverified-only outcome reason omits an unresolved knockout evidence reference"
            )
        return
    if resolution["state"] != "TERMINAL":
        raise EvaluationRecordV1Error("ordinary outcomes must be terminal")
    score_verdict = result["score_verdict"]["value"]
    if result.get("final_outcome") != score_verdict:
        raise EvaluationRecordV1Error(
            "ordinary final_outcome must copy the existing v1.5 score verdict"
        )


def validate_evaluation_record_v1(document: Mapping[str, Any]) -> None:
    """Run strict JSON, Draft 2020-12 and semantic/reference validation."""
    _assert_json_safe(document)
    enforce_schema(document, path=str(_SCHEMA_PATH))
    _validate_references(document)
    _validate_outcome(document)


def build_evaluation_record_v1(record: Any) -> Dict[str, Any]:
    """Project a v1.5 ``EvaluationRecord`` to its schema-validated A15 form."""
    payload = _project_evaluation_record(record)
    validate_evaluation_record_v1(payload)
    return payload


def serialize_evaluation_record_v1(document: Mapping[str, Any]) -> str:
    """Serialize an already projected record using the separate file profile.

    This is intentionally not ``canonical_json``: JSON numbers remain ordinary
    JSON numbers in the file, strings retain their original Unicode code
    points, and the existing v1.5 object-hash grammar remains unchanged.
    """
    validate_evaluation_record_v1(document)
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )


__all__ = [
    "CANONICALIZATION_ID",
    "RECORD_ARTIFACT_NAME",
    "RECORD_SCHEMA_VERSION",
    "SERIALIZATION_PROFILE_ID",
    "EvaluationRecordV1Error",
    "build_evaluation_record_v1",
    "validate_evaluation_record_v1",
    "serialize_evaluation_record_v1",
]
