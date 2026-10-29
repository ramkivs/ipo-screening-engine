"""Layer 2B supplemental capture, validation, and isolated immutable storage.

Storage acceptance proves contract and integrity checks only.  It never changes
Layer 1 and never grants scoring eligibility or publisher authenticity.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from jsonschema import Draft202012Validator, FormatChecker

from .evaluation import EvaluationStore
from .hashing import sha256_of

CONTRACT_NAME = "IPO_LAYER_2B_SUPPLEMENTAL_DATA"
CONTRACT_VERSION = "1.0"
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "supplemental-data.v1.schema.json"

# Deliberately narrow initial registry. These are recordable, never score-eligible.
ELIGIBILITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    target: {
        "category": "EXCHANGE_DEMAND",
        "type": "number",
        "unit": "MULTIPLE_X",
        "currency": None,
        "requires_observation_time": True,
        "gap_category": "MARKET",
        "gap_item": "subscription",
        "source_types": ("OFFICIAL_EXCHANGE_DOCUMENT",),
        "minimum": 0,
        "recordable": True,
        "scoring_eligible": False,
    }
    for target in (
        "market.subscription.qib_x",
        "market.subscription.nii_x",
        "market.subscription.retail_x",
        "market.subscription.overall_x",
    )
}
ELIGIBILITY_REGISTRY.update({
    "financials.operating_cash_flow_3yr_cumulative": {
        "category": "FINANCIAL_HEALTH", "type": "number_or_array", "unit": "REPORTING_UNIT",
        "currency": "INR", "requires_observation_time": False, "requires_gap": False,
        "gap_category": "FINANCIAL", "gap_item": "operating_cash_flow_3yr_cumulative",
        "source_types": ("OFFICIAL_FILING",), "minimum": None, "recordable": True, "scoring_eligible": True,
    },
    "financials.net_income_3yr_cumulative": {
        "category": "FINANCIAL_HEALTH", "type": "number_or_array", "unit": "REPORTING_UNIT",
        "currency": "INR", "requires_observation_time": False, "requires_gap": False,
        "gap_category": "FINANCIAL", "gap_item": "net_income_3yr_cumulative",
        "source_types": ("OFFICIAL_FILING",), "minimum": None, "recordable": True, "scoring_eligible": True,
    },
    "financials.trade_receivables_days": {
        "category": "FINANCIAL_HEALTH", "type": "number", "unit": "DAYS", "currency": None,
        "requires_observation_time": False, "requires_gap": False,
        "gap_category": "FINANCIAL", "gap_item": "trade_receivables_days",
        "source_types": ("OFFICIAL_FILING",), "minimum": 0, "recordable": True, "scoring_eligible": True,
    },
    "financials.net_working_capital_pct_revenue": {
        "category": "FINANCIAL_HEALTH", "type": "number", "unit": "PERCENT", "currency": None,
        "requires_observation_time": False, "requires_gap": False,
        "gap_category": "FINANCIAL", "gap_item": "net_working_capital_pct_revenue",
        "source_types": ("OFFICIAL_FILING",), "minimum": None, "recordable": True, "scoring_eligible": True,
    },
})

@dataclass(frozen=True)
class SupplementalValidation:
    accepted: bool
    outcome: str
    errors: Tuple[str, ...]
    payload_hash: Optional[str] = None
    payload_id: Optional[str] = None
    baseline_binding: Optional[str] = None


def _verified_baseline(store: EvaluationStore, evaluation_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not store.exists(evaluation_id):
        raise FileNotFoundError(f"no stored evaluation {evaluation_id!r} under {store.root}")
    check = store.verify_hashes(evaluation_id)
    if not check["result_hash_matches"] or check["artifact_mismatches"]:
        raise ValueError(f"baseline {evaluation_id!r} failed artifact/result integrity verification")
    record = store.read_full(evaluation_id)
    manifest = store.read_artifact(evaluation_id, "manifest")
    return record, manifest


def baseline_binding(record: Mapping[str, Any], manifest: Mapping[str, Any]) -> str:
    """Bind exact identity/result to the sorted immutable artifact digest inventory."""
    subject = {
        "profile": "ipo-layer2b-baseline-binding/1.0",
        "evaluation_id": record.get("evaluation_id"),
        "ipo_id": record.get("ipo_id"),
        "result_hash": record.get("result_hash"),
        "artifacts": dict(sorted((manifest.get("artifacts") or {}).items())),
    }
    return sha256_of(subject)


def _payload_subject(payload: Mapping[str, Any]) -> Dict[str, Any]:
    subject = dict(payload)
    subject.pop("canonical_payload_hash", None)
    subject.pop("supplemental_payload_id", None)
    return subject


def payload_hash(payload: Mapping[str, Any]) -> str:
    return sha256_of(_payload_subject(payload))


def _schema_errors(payload: Mapping[str, Any]) -> List[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"SCHEMA {'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}" for e in sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))]


def initialize_template(store: EvaluationStore, evaluation_id: str) -> Dict[str, Any]:
    record, manifest = _verified_baseline(store, evaluation_id)
    gaps = {(g.get("category"), g.get("item")) for g in record.get("missing_unverified") or []}
    entries = []
    excluded = []
    snapshot = record.get("input_snapshot") or {}
    raw_input: Any = snapshot.get("input", snapshot) if isinstance(snapshot, Mapping) else {}
    for target, rule in sorted(ELIGIBILITY_REGISTRY.items()):
        existing: Any = raw_input
        for part in target.split("."):
            existing = existing.get(part) if isinstance(existing, Mapping) else None
        if existing is not None:
            excluded.append({"target": target, "reason": "value is already established in Layer 1"})
            continue
        if rule.get("requires_gap", True) and (rule["gap_category"], rule["gap_item"]) not in gaps:
            excluded.append({"target": target, "reason": "baseline does not establish the required eligible gap"})
            continue
        entries.append({
            "target": target, "category": rule["category"], "value": None,
            "unit": rule["unit"], "currency": rule["currency"],
            "reporting_period": None, "observation_time": None,
            "source": {"source_type": rule["source_types"][0], "source_id": "", "title": "", "publisher": "", "publication_date": "", "official_url": None, "artifact_ref": "", "artifact_sha256": "", "locator": ""},
            "operator_attestation": {"operator_id": "", "attested_at": "", "statement": ""},
            "verification": {"status": "UNVERIFIED", "procedure_note": "Storage acceptance is not source or value verification."},
            "limitations": ["Storage acceptance alone does not prove source authenticity, value truth, or scoring admission."],
        })
    # Gap rows outside the explicit registry are visible but never made fillable.
    supported_gap = {(r["gap_category"], r["gap_item"]) for r in ELIGIBILITY_REGISTRY.values()}
    for category, item in sorted(gaps, key=lambda x: (str(x[0]), str(x[1]))):
        if (category, item) not in supported_gap:
            excluded.append({"gap_category": category, "gap_item": item, "reason": "not in the Layer 2B eligibility registry"})
    return {
        "contract_name": CONTRACT_NAME, "contract_version": CONTRACT_VERSION,
        "evaluation_id": record["evaluation_id"], "ipo_id": record["ipo_id"],
        "company_name": record["company_name"],
        "baseline_binding": baseline_binding(record, manifest),
        "supplemental_payload_id": None, "created_at": "",
        "canonical_payload_hash": None, "entries": entries,
        "template_metadata": {"excluded_gaps": excluded, "scoring_eligibility": "NOT_GRANTED"},
    }


def validate_payload(payload: Mapping[str, Any], store: EvaluationStore, *, payload_base: Path) -> SupplementalValidation:
    errors = _schema_errors(payload)
    evaluation_id = str(payload.get("evaluation_id") or "")
    try:
        record, manifest = _verified_baseline(store, evaluation_id)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        errors.append(f"BASELINE {exc}")
        return SupplementalValidation(False, "CONTRACT_REJECTED", tuple(errors))
    binding = baseline_binding(record, manifest)
    if payload.get("baseline_binding") != binding:
        errors.append("BASELINE_BINDING_MISMATCH")
    if payload.get("ipo_id") != record.get("ipo_id") or payload.get("company_name") != record.get("company_name"):
        errors.append("BASELINE_IDENTITY_MISMATCH")

    gaps = {(g.get("category"), g.get("item")) for g in record.get("missing_unverified") or []}
    seen = set()
    for i, entry in enumerate(payload.get("entries") or []):
        prefix = f"ENTRY[{i}]"
        target = entry.get("target")
        if target in seen:
            errors.append(f"{prefix} DUPLICATE_TARGET")
        seen.add(target)
        rule = ELIGIBILITY_REGISTRY.get(str(target))
        if not rule:
            errors.append(f"{prefix} UNSUPPORTED_TARGET {target!r}")
            continue
        if rule.get("requires_gap", True) and (rule["gap_category"], rule["gap_item"]) not in gaps:
            errors.append(f"{prefix} TARGET_NOT_A_BASELINE_GAP")
        parts = str(target).split(".")
        snapshot = record.get("input_snapshot") or {}
        existing: Any = snapshot.get("input", snapshot) if isinstance(snapshot, Mapping) else None
        for part in parts:
            existing = existing.get(part) if isinstance(existing, Mapping) else None
        if existing is not None:
            errors.append(f"{prefix} TARGET_ALREADY_ESTABLISHED_IN_LAYER1")
        value = entry.get("value")
        values = value if isinstance(value, list) else [value]
        if (rule["type"] != "number_or_array" and isinstance(value, list)) or not values or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in values):
            errors.append(f"{prefix} VALUE_TYPE must be number" + (" or numeric array" if rule["type"] == "number_or_array" else ""))
        elif isinstance(value, list) and len(value) != 3:
            errors.append(f"{prefix} VALUE_ARRAY must contain exactly three FY observations")
        elif rule.get("minimum") is not None and any(item < rule["minimum"] for item in values):
            errors.append(f"{prefix} VALUE_RANGE must be >= {rule['minimum']}")
        if entry.get("category") != rule["category"] or entry.get("unit") != rule["unit"] or entry.get("currency") != rule["currency"]:
            errors.append(f"{prefix} SEMANTIC_METADATA_MISMATCH")
        if rule["requires_observation_time"] and not entry.get("observation_time"):
            errors.append(f"{prefix} OBSERVATION_TIME_REQUIRED")
        source = entry.get("source") or {}
        if source.get("source_type") not in rule["source_types"]:
            errors.append(f"{prefix} SOURCE_TYPE_NOT_PERMITTED")
        artifact_ref = source.get("artifact_ref")
        artifact_path = (payload_base / str(artifact_ref)).resolve() if artifact_ref else None
        if not artifact_path or not artifact_path.is_file():
            errors.append(f"{prefix} SOURCE_ARTIFACT_MISSING")
        else:
            actual = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            if actual != source.get("artifact_sha256"):
                errors.append(f"{prefix} SOURCE_ARTIFACT_HASH_MISMATCH")
        verification = (entry.get("verification") or {}).get("status")
        if verification == "SOURCE_ARTIFACT_HASH_VERIFIED" and (not artifact_path or not artifact_path.is_file()):
            errors.append(f"{prefix} VERIFICATION_STATUS_UNSUPPORTED")
        # Explicitly no value-authenticity status exists in v1.

    computed = payload_hash(payload)
    expected_id = f"SUPP-{computed[:16]}"
    if payload.get("canonical_payload_hash") != computed:
        errors.append("CANONICAL_PAYLOAD_HASH_MISMATCH")
    if payload.get("supplemental_payload_id") != expected_id:
        errors.append("SUPPLEMENTAL_PAYLOAD_ID_MISMATCH")
    return SupplementalValidation(not errors, "SUPPLEMENTAL_STORAGE_ACCEPTABLE" if not errors else "CONTRACT_REJECTED", tuple(errors), computed, expected_id, binding)


def finalize_payload(template: Mapping[str, Any]) -> Dict[str, Any]:
    """Fill deterministic identity fields after an operator completes a template."""
    payload = dict(template)
    payload.pop("template_metadata", None)
    digest = payload_hash(payload)
    payload["canonical_payload_hash"] = digest
    payload["supplemental_payload_id"] = f"SUPP-{digest[:16]}"
    return payload


def store_payload(payload: Mapping[str, Any], store: EvaluationStore, supp_root: Path, *, payload_base: Path) -> Tuple[str, Path, SupplementalValidation]:
    validation = validate_payload(payload, store, payload_base=payload_base)
    if not validation.accepted:
        return "CONTRACT_REJECTED", supp_root, validation
    evaluation_dir = store.path_for(str(payload["evaluation_id"])).resolve()
    root = supp_root.resolve()
    if root == evaluation_dir or evaluation_dir in root.parents:
        return "CONTRACT_REJECTED", root, SupplementalValidation(False, "CONTRACT_REJECTED", ("SUPPLEMENTAL_STORE_INSIDE_BASELINE",))
    # Resolve an existing parent to catch symlinks before writing.
    probe = root
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    resolved_root = probe.resolve() / root.relative_to(probe)
    if resolved_root == evaluation_dir or evaluation_dir in resolved_root.parents:
        return "CONTRACT_REJECTED", root, SupplementalValidation(False, "CONTRACT_REJECTED", ("SUPPLEMENTAL_STORE_SYMLINKS_INSIDE_BASELINE",))

    target = root / str(payload["evaluation_id"]) / str(validation.payload_hash)
    if target.exists():
        return "EXACT_DUPLICATE", target, validation
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    # Reject conflicting values for the same target in accepted sibling payloads.
    incoming = {e["target"]: e["value"] for e in payload["entries"]}
    for sibling in parent.iterdir():
        candidate = sibling / "supplemental_payload.json"
        if not candidate.is_file():
            continue
        prior = json.loads(candidate.read_text(encoding="utf-8"))
        prior_values = {e["target"]: e["value"] for e in prior.get("entries", [])}
        conflicts = sorted(k for k in incoming.keys() & prior_values.keys() if incoming[k] != prior_values[k])
        if conflicts:
            return "CONFLICT_REJECTED", target, SupplementalValidation(False, "CONTRACT_REJECTED", tuple(f"CONFLICTING_TARGET {k}" for k in conflicts))

    manifest = {
        "store_profile": "ipo-layer2b-supplemental-store/1.0",
        "contract_name": CONTRACT_NAME, "contract_version": CONTRACT_VERSION,
        "evaluation_id": payload["evaluation_id"], "baseline_binding": validation.baseline_binding,
        "payload_hash": validation.payload_hash, "payload_id": validation.payload_id,
        "stored_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "validation_outcome": "SUPPLEMENTAL_STORAGE_ACCEPTED",
        "source_verification": "PER_ENTRY; STORAGE_ACCEPTANCE_IS_NOT VALUE AUTHENTICITY",
        "scoring_eligibility": "NOT_GRANTED",
    }
    temp = Path(tempfile.mkdtemp(prefix=f".{validation.payload_hash}.tmp-", dir=parent))
    try:
        for name, value in (("supplemental_payload.json", payload), ("supplemental_manifest.json", manifest)):
            with (temp / name).open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.write("\n")
        os.rename(temp, target)
    except Exception:
        for child in temp.glob("*"):
            child.unlink()
        temp.rmdir()
        raise
    return "SUPPLEMENTAL_STORAGE_ACCEPTED", target, validation

__all__ = ["CONTRACT_NAME", "CONTRACT_VERSION", "ELIGIBILITY_REGISTRY", "SupplementalValidation", "baseline_binding", "initialize_template", "finalize_payload", "validate_payload", "store_payload"]
