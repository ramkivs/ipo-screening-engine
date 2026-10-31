"""Governed Layer 2C secondary evaluations over accepted Layer 2B demand data."""
from __future__ import annotations

import copy
import json
import os
import tempfile
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from jsonschema import Draft202012Validator

from .evaluation import EvaluationStore
from .financial_health import FINANCIAL_HEALTH_TARGETS, financial_health_metrics, with_financial_health_extension
from .governance_extension import GOVERNANCE_EXTENSION_TARGETS, governance_extension_metrics, with_governance_extension
from .segment_risk_extension import SEGMENT_RISK_TARGETS, segment_risk_metrics, with_segment_risk_extension
from .regulatory_risk_extension import REGULATORY_RISK_TARGETS, regulatory_risk_metrics, with_regulatory_risk_extension
from .hashing import sha256_of
from .pipeline import evaluate, load_config
from .supplemental_data import ELIGIBILITY_REGISTRY, baseline_binding, payload_hash
from .score_input_overrides import SCORE_OVERRIDE_TARGETS, score_override_metrics

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "secondary-evaluation.v1.schema.json"
WHITELIST = frozenset(ELIGIBILITY_REGISTRY)
MODULE_CAPS = {"A": 25.0, "B": 20.0, "C": 15.0, "D": 15.0, "E": 15.0, "F": 10.0}


def _verified_baseline(store: EvaluationStore, evaluation_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    check = store.verify_hashes(evaluation_id)
    if not check["result_hash_matches"] or check["artifact_mismatches"]:
        raise ValueError("baseline integrity verification failed")
    return store.read_full(evaluation_id), store.read_artifact(evaluation_id, "manifest")


def find_supplemental(supp_root: Path, baseline_id: str, supplemental_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], Path]:
    parent = supp_root.resolve() / baseline_id
    if not parent.is_dir():
        raise FileNotFoundError(f"no supplemental records for {baseline_id!r}")
    matches = []
    for child in parent.iterdir():
        payload_path = child / "supplemental_payload.json"
        manifest_path = child / "supplemental_manifest.json"
        if payload_path.is_file() and manifest_path.is_file():
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            if payload.get("supplemental_payload_id") == supplemental_id:
                matches.append((payload, json.loads(manifest_path.read_text(encoding="utf-8")), child))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly one accepted supplemental payload {supplemental_id!r}; found {len(matches)}")
    payload, manifest, path = matches[0]
    computed = payload_hash(payload)
    if computed != payload.get("canonical_payload_hash") or computed != manifest.get("payload_hash"):
        raise ValueError("supplemental payload hash mismatch")
    if manifest.get("validation_outcome") != "SUPPLEMENTAL_STORAGE_ACCEPTED":
        raise ValueError("supplemental payload was not accepted")
    return payload, manifest, path


def _score_view(record: Mapping[str, Any]) -> Dict[str, Any]:
    score = record.get("score") or {}
    verdict = record.get("verdict") or {}
    confidence = record.get("confidence") or {}
    return {
        "score": float(score.get("final_score", 0)),
        "verdict": str(verdict.get("verdict") or score.get("verdict")),
        "confidence": str(confidence.get("level") or score.get("confidence")),
        "knockout_status": str((record.get("knockouts") or {}).get("status") or "UNKNOWN"),
        "knockouts": [
            {"rule_id": str(item.get("rule_id")), "state": str(item.get("state"))}
            for item in ((record.get("knockouts") or {}).get("results") or [])
        ],
    }


def _module_map(record: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(m["module_id"]): m for m in (record.get("score") or {}).get("modules", [])}


def build_inspection(baseline: Mapping[str, Any], enriched: Mapping[str, Any]) -> Dict[str, Any]:
    before_modules, after_modules = _module_map(baseline), _module_map(enriched)
    modules = []
    for module_id in MODULE_CAPS:
        before = before_modules.get(module_id, {})
        after = after_modules.get(module_id, {})
        before_criteria = {str(item.get("criterion_id")): item for item in before.get("criteria", [])}
        raw_points = sum(float(item.get("score", 0)) for item in after.get("criteria", []))
        module_score = float(after.get("score", 0))
        capped = raw_points > module_score or module_score >= MODULE_CAPS[module_id]
        criteria = []
        for item in after.get("criteria", []):
            prior = before_criteria.get(str(item.get("criterion_id")), {})
            state = str(item.get("state") or "UNKNOWN")
            if state not in {"SCORED", "UNKNOWN"}:
                state = "UNKNOWN"
            if capped and state == "SCORED" and raw_points > module_score:
                state = "CAPPED"
            criteria.append({
                "criterion_id": str(item.get("criterion_id")),
                "label": str(item.get("label") or item.get("criterion_id")),
                "metric": str(item.get("metric") or ""),
                "baseline_value": prior.get("value"),
                "secondary_value": item.get("value"),
                "score": float(item.get("score", 0)),
                "max": float(item.get("max", 0)),
                "state": state,
                "explanation": str(item.get("reason") or item.get("formula") or "No rule explanation recorded."),
            })
        modules.append({
            "module_id": module_id, "name": str(after.get("name") or before.get("name") or module_id),
            "baseline_points": float(before.get("score", 0)), "secondary_points": module_score,
            "cap": MODULE_CAPS[module_id], "delta": module_score-float(before.get("score", 0)),
            "cap_applied": capped, "criteria": criteria,
        })
    confidence = enriched.get("confidence") or {}
    return {
        "completeness_pct": float(confidence.get("completeness_pct", 0)),
        "confidence": str(confidence.get("level") or "UNKNOWN"),
        "modules": modules,
    }


def evaluation_inspection(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the presentation-safe structured view for a Layer 1 record."""
    return {"secondary": _score_view(record), "inspection": build_inspection(record, record)}


def _subject(document: Mapping[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(dict(document))
    out.pop("canonical_secondary_hash", None)
    out.pop("secondary_evaluation_id", None)
    return out


def secondary_hash(document: Mapping[str, Any]) -> str:
    return sha256_of(_subject(document))


def build_secondary(baseline_id: str, store: EvaluationStore, supp_root: Path, supplemental_id: str) -> Dict[str, Any]:
    baseline, manifest = _verified_baseline(store, baseline_id)
    payload, supp_manifest, _ = find_supplemental(supp_root, baseline_id, supplemental_id)
    if payload.get("evaluation_id") != baseline_id or payload.get("baseline_binding") != baseline_binding(baseline, manifest):
        raise ValueError("supplemental payload is not bound to the exact baseline")
    entries = payload.get("entries") or []
    targets = [str(e.get("target")) for e in entries]
    if not entries or len(targets) != len(set(targets)) or any(t not in WHITELIST for t in targets):
        raise ValueError("Layer 2C admits only unique governed subscription, financial-health, segment-risk, regulatory-risk, or governance targets")
    if any((e.get("verification") or {}).get("status") != "SOURCE_ARTIFACT_HASH_VERIFIED" for e in entries):
        raise ValueError("Layer 2C requires SOURCE_ARTIFACT_HASH_VERIFIED entries")

    snapshot = baseline.get("input_snapshot") or {}
    raw = copy.deepcopy(snapshot.get("input", snapshot))
    evidence_artifact = store.read_artifact(baseline_id, "evidence").get("evidence") or {}
    raw["_sources"] = copy.deepcopy(evidence_artifact.get("sources") or [])
    raw["_evidence"] = {
        item["evidence_id"]: item for item in (evidence_artifact.get("evidence") or [])
        if isinstance(item, Mapping) and isinstance(item.get("evidence_id"), str)
    }
    observation_times = [str(e["observation_time"]) for e in entries]
    at_text = max(observation_times)
    issue = raw.get("issue") or {}
    observation_date = at_text[:10]
    if not issue.get("open_date") or not issue.get("close_date") or not (str(issue["open_date"]) <= observation_date <= str(issue["close_date"])):
        raise ValueError("supplemental observation is outside the baseline bidding window")
    demand_values = {e["target"].rsplit(".", 1)[1]: e["value"] for e in entries if str(e["target"]).startswith("market.subscription.")}
    if demand_values:
        demand_values.update({"as_of": at_text, "source_id": payload["supplemental_payload_id"]})
        raw.setdefault("market", {})["subscription"] = demand_values
    financial_values = {e["target"].rsplit(".", 1)[1]: e["value"] for e in entries if str(e["target"]).startswith("financials.")}
    if financial_values:
        raw.setdefault("financials", {}).update(financial_values)
    governance_values = {e["target"].rsplit(".", 1)[1]: e["value"] for e in entries if str(e["target"]).startswith("governance.")}
    if governance_values:
        raw.setdefault("governance", {}).update(governance_values)
    # The governed Workbench names guardrail assertions under risks, while the
    # frozen Layer 1 metrics retain their canonical governance/financial paths.
    guardrail_values = {str(e["target"]): e["value"] for e in entries}
    if "risks.going_concern_uncertainty" in guardrail_values:
        raw.setdefault("governance", {})["going_concern_uncertainty"] = guardrail_values["risks.going_concern_uncertainty"]
    if "risks.contingent_liab_unquantified" in guardrail_values:
        raw.setdefault("financials", {})["contingent_liabilities_unquantified"] = guardrail_values["risks.contingent_liab_unquantified"]
    if "governance.promoter_pledged_shares_pct" in guardrail_values:
        raw.setdefault("capital_structure", {})["promoter_pledge_pct"] = guardrail_values["governance.promoter_pledged_shares_pct"]
    risk_values = {
        e["target"].rsplit(".", 1)[1]: e["value"] for e in entries
        if str(e["target"]).startswith("risks.")
        and e["target"] not in {"risks.going_concern_uncertainty", "risks.contingent_liab_unquantified"}
    }
    if risk_values:
        raw.setdefault("risks", {}).update(risk_values)
    moment = datetime.fromisoformat(at_text.replace("Z", "+00:00")).astimezone(timezone.utc)
    scoring_config = load_config()
    financial_extension = any(target in FINANCIAL_HEALTH_TARGETS for target in targets)
    governance_extension = any(target in GOVERNANCE_EXTENSION_TARGETS for target in targets)
    segment_extension = any(target in SEGMENT_RISK_TARGETS for target in targets)
    regulatory_extension = any(target in REGULATORY_RISK_TARGETS for target in targets)
    if financial_extension:
        scoring_config = with_financial_health_extension(scoring_config)
    if governance_extension:
        scoring_config = with_governance_extension(scoring_config)
    if segment_extension:
        scoring_config = with_segment_risk_extension(scoring_config)
    if regulatory_extension:
        scoring_config = with_regulatory_risk_extension(scoring_config)
    score_overrides = {str(e["target"]): e["value"] for e in entries if e["target"] in SCORE_OVERRIDE_TARGETS}
    with ExitStack() as extensions:
        if score_overrides:
            extensions.enter_context(score_override_metrics(score_overrides))
        if financial_extension:
            extensions.enter_context(financial_health_metrics())
        if governance_extension:
            extensions.enter_context(governance_extension_metrics())
        if segment_extension:
            extensions.enter_context(segment_risk_metrics())
        if regulatory_extension:
            extensions.enter_context(regulatory_risk_metrics())
        outcome = evaluate(raw, scoring_config, mode=str(baseline["evaluation_mode"]).lower(), evaluation_datetime=moment)
    enriched = outcome.record.to_dict()
    before_modules, after_modules = _module_map(baseline), _module_map(enriched)
    breakdown = []
    for module_id in MODULE_CAPS:
        before = float(before_modules.get(module_id, {}).get("score", 0))
        after = float(after_modules.get(module_id, {}).get("score", 0))
        cap = MODULE_CAPS[module_id]
        if after > cap:
            raise ValueError(f"module {module_id} exceeds cap {cap}")
        breakdown.append({"module_id": module_id, "baseline_points": before, "secondary_points": after, "delta": after-before, "cap": cap, "cap_applied": after >= cap})
    document = {
        "contract_name": "IPO_LAYER_2C_SECONDARY_EVALUATION", "contract_version": "1.0",
        "secondary_evaluation_id": None, "baseline_evaluation_id": baseline_id,
        "baseline_result_hash": baseline["result_hash"], "baseline_binding": payload["baseline_binding"],
        "supplemental_payload_id": payload["supplemental_payload_id"],
        "supplemental_payload_hash": payload["canonical_payload_hash"],
        "evaluated_at": at_text, "admitted_fields": targets,
        "baseline": _score_view(baseline), "secondary": _score_view(enriched),
        "module_breakdown": breakdown, "inspection": build_inspection(baseline, enriched),
        "secondary_result_hash": enriched["result_hash"],
        "scoring_profile": "CORE_ENGINE_UNCHANGED", "canonical_secondary_hash": None,
    }
    digest = secondary_hash(document)
    document["canonical_secondary_hash"] = digest
    document["secondary_evaluation_id"] = f"SEC-{digest[:16]}"
    errors = list(Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).iter_errors(document))
    if errors:
        raise ValueError("secondary schema violation: " + "; ".join(e.message for e in errors))
    return document


def store_secondary(document: Mapping[str, Any], root: Path, baseline_store: EvaluationStore | None = None) -> Tuple[str, Path]:
    root = root.resolve()
    baseline_id = str(document["baseline_evaluation_id"])
    if Path(baseline_id).name != baseline_id:
        raise ValueError("unsafe baseline evaluation identity")
    if baseline_store is not None:
        evaluation_dir = baseline_store.path_for(baseline_id).resolve()
        if root == evaluation_dir or evaluation_dir in root.parents:
            raise ValueError("secondary store must be outside the immutable baseline directory")
    target = root / baseline_id / str(document["secondary_evaluation_id"])
    if target.exists():
        existing = json.loads((target / "secondary_evaluation.json").read_text(encoding="utf-8"))
        if existing == document:
            return "EXACT_DUPLICATE", target
        raise ValueError("secondary evaluation identity conflict")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".secondary.tmp-", dir=target.parent))
    try:
        (temp / "secondary_evaluation.json").write_text(json.dumps(document, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        os.rename(temp, target)
    except Exception:
        for child in temp.glob("*"): child.unlink()
        temp.rmdir(); raise
    return "SECONDARY_EVALUATION_STORED", target


def verify_secondary(document: Mapping[str, Any]) -> Dict[str, Any]:
    errors = [e.message for e in Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).iter_errors(document)]
    digest = secondary_hash(document)
    expected_id = f"SEC-{digest[:16]}"
    if digest != document.get("canonical_secondary_hash"): errors.append("canonical secondary hash mismatch")
    if expected_id != document.get("secondary_evaluation_id"): errors.append("secondary evaluation id mismatch")
    return {"valid": not errors, "errors": errors, "canonical_secondary_hash": digest}
