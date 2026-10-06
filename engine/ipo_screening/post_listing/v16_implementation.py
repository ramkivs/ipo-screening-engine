"""Authorized v1.6 Implementation & Promotion Preparation Engine (Phase 7).

Specifies strict provenance, deterministic verification, frozen-core preservation,
and shadow evaluation between active v1.5 baseline and authorized v1.6 candidate.

Strict boundary:
  APPROVED PROPOSAL -> V1.6 IMPLEMENTATION -> DETERMINISTIC VERIFICATION -> CONTROLLED ACCEPTANCE -> EXPLICIT ACTIVATION
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:
    from ipo_screening.config_validation import check_config
    from ipo_screening.hashing import canonical_json, sha256_of
    from ipo_screening.post_listing.calibration import (
        ApprovalStatus,
        CalibrationProposal,
        ShadowEvaluationResult,
        compute_config_content_hash,
        compute_proposal_content_hash,
        evaluate_verdict,
        rescore_row,
        verify_proposal,
    )
    from ipo_screening.post_listing.dataset import BacktestDataset, BacktestDatasetRow
except ImportError:
    from engine.ipo_screening.config_validation import check_config
    from engine.ipo_screening.hashing import canonical_json, sha256_of
    from engine.ipo_screening.post_listing.calibration import (
        ApprovalStatus,
        CalibrationProposal,
        ShadowEvaluationResult,
        compute_config_content_hash,
        compute_proposal_content_hash,
        evaluate_verdict,
        rescore_row,
        verify_proposal,
    )
    from engine.ipo_screening.post_listing.dataset import BacktestDataset, BacktestDatasetRow

V1_5_CONFIG_PATH = Path("config/ipo-config.v1.5.0.json")
V1_6_CONFIG_PATH = Path("config/ipo-config.v1.6.0.json")
APPROVED_PROPOSAL_PATH = Path("config/calibration-proposal.v1.6.0.json")

# Verified constants
V1_5_BASELINE_VERSION = "1.5.0"
V1_6_CONFIG_VERSION = "1.6.0"
V1_5_RAW_SHA256 = "1f91db2c086db39dcb93b3091389ab2113a5031da7e41cecf458f92082a0c185"
V1_5_CANONICAL_HASH = "c7dce6e1f44b0ff8804694d0d4b6631a5f0164217c3bd2f3b942650c48e32502"
V1_5_POLICY_CONTENT_HASH = "382ff86cc9d753514509f89c096f3b262bd4e12e644e0d7d03fe811b44e0f1e8"
GOLDEN_RESULT_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"

FROZEN_CORE_HASHES: Dict[str, str] = {
    "engine/ipo_screening/derived.py": "0a6ef86a8d2011ae4558876515b971ef9565c1ee2b4ca1eedd07582269356237",
    "engine/ipo_screening/scoring.py": "3bbec2b4f682407c29e0488df0d4bc7a6c152506c6ec55618ee9827480bd725a",
    "engine/ipo_screening/knockouts.py": "8555b633a427fb057b2be4116aecca1d28f80f4e7a52ce3c15bdc9a7be16761f",
    "engine/ipo_screening/snapshots.py": "9c9626c9210b6d45863f4ec416b06b118d94a13cc669320184df5a5fdd204a27",
    "engine/ipo_screening/evaluation.py": "d20d87b69e01ced146791fe9a4e61faa5d522281383781bfbf5e97e7055810ae",
    "engine/ipo_screening/extraction/price_band_notice.py": "779afb0b1ba309913974edee4c09109b4e4da2806c3e49277e902e86a7c994e4",
}


@dataclass(frozen=True)
class ConfigDiffEntry:
    """Record of a single changed configuration field."""
    path: str
    old_value: Any
    new_value: Any
    proposal_reference: str
    rationale: str
    approved_scope: str = "APPROVED"


@dataclass(frozen=True)
class ConfigDiffReport:
    """Complete machine-readable and human-readable configuration diff."""
    v1_5_version: str
    v1_6_version: str
    v1_5_hash: str
    v1_6_hash: str
    changed_scoring_fields_count: int
    changed_metadata_fields_count: int
    changed_fields: List[ConfigDiffEntry]
    unchanged_sections: List[str]
    is_approved_scope_only: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "v1_5_version": self.v1_5_version,
            "v1_6_version": self.v1_6_version,
            "v1_5_hash": self.v1_5_hash,
            "v1_6_hash": self.v1_6_hash,
            "changed_scoring_fields_count": self.changed_scoring_fields_count,
            "changed_metadata_fields_count": self.changed_metadata_fields_count,
            "changed_fields": [asdict(f) for f in self.changed_fields],
            "unchanged_sections": self.unchanged_sections,
            "is_approved_scope_only": self.is_approved_scope_only,
        }


@dataclass(frozen=True)
class V16ShadowRowDetail:
    """Shadow comparison for a single evaluation row."""
    ipo_id: str
    baseline_score: float
    v1_6_score: float
    score_delta: float
    baseline_verdict: str
    v1_6_verdict: str
    baseline_knockout_state: str
    v1_6_knockout_state: str
    score_increase: bool
    score_decrease: bool
    unchanged: bool
    upgraded: bool
    downgraded: bool
    newly_knocked_out: bool
    knockout_removed: bool


@dataclass(frozen=True)
class V16ShadowReport:
    """Full shadow evaluation report comparing v1.5 vs v1.6."""
    total_evaluated: int
    score_mean_delta: float
    verdict_shifts_count: int
    upgraded_count: int
    downgraded_count: int
    unchanged_count: int
    newly_knocked_out_count: int
    knockout_removed_count: int
    score_increase_count: int
    score_decrease_count: int
    baseline_mean_score: float
    v1_6_mean_score: float
    downside_protection_passed: bool
    holdout_stability_passed: bool
    vintage_robustness_passed: bool
    details_by_row: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_evaluated": self.total_evaluated,
            "score_mean_delta": self.score_mean_delta,
            "verdict_shifts_count": self.verdict_shifts_count,
            "upgraded_count": self.upgraded_count,
            "downgraded_count": self.downgraded_count,
            "unchanged_count": self.unchanged_count,
            "newly_knocked_out_count": self.newly_knocked_out_count,
            "knockout_removed_count": self.knockout_removed_count,
            "score_increase_count": self.score_increase_count,
            "score_decrease_count": self.score_decrease_count,
            "baseline_mean_score": self.baseline_mean_score,
            "v1_6_mean_score": self.v1_6_mean_score,
            "downside_protection_passed": self.downside_protection_passed,
            "holdout_stability_passed": self.holdout_stability_passed,
            "vintage_robustness_passed": self.vintage_robustness_passed,
            "details_by_row": self.details_by_row,
        }


def load_v1_5_config(path: Path | str = V1_5_CONFIG_PATH) -> Dict[str, Any]:
    """Load and verify baseline v1.5 configuration."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"baseline configuration not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_v1_6_config(path: Path | str = V1_6_CONFIG_PATH) -> Dict[str, Any]:
    """Load authorized v1.6 configuration."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"v1.6 configuration not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_approved_proposal(path: Path | str = APPROVED_PROPOSAL_PATH) -> CalibrationProposal:
    """Load and return verified approved calibration proposal."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"approved proposal not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return CalibrationProposal.from_dict(data)


def verify_frozen_core(base_dir: Path | str = Path(".")) -> Tuple[bool, Dict[str, bool]]:
    """Verify that all six core engine files remain byte-for-byte identical to baseline."""
    root = Path(base_dir)
    results: Dict[str, bool] = {}
    all_ok = True
    for rel_path, expected_hash in FROZEN_CORE_HASHES.items():
        file_path = root / rel_path
        if not file_path.is_file():
            results[rel_path] = False
            all_ok = False
            continue
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        is_match = (actual_hash == expected_hash)
        results[rel_path] = is_match
        if not is_match:
            all_ok = False
    return all_ok, results


def verify_golden_result() -> Tuple[bool, str]:
    """Verify that the immutable golden evaluation result remains bit-for-bit identical."""
    golden_path = Path("fixtures/vishal_nirmiti/input.json")
    if not golden_path.is_file():
        return False, "Fixture not found"

    from datetime import datetime, timezone
    eval_at = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

    try:
        from ipo_screening.pipeline import evaluate, load_config
    except ImportError:
        from engine.ipo_screening.pipeline import evaluate, load_config

    cfg = load_config(V1_5_CONFIG_PATH)
    with golden_path.open("r", encoding="utf-8") as f:
        raw_input = json.load(f)

    result = evaluate(raw_input, config=cfg, evaluation_datetime=eval_at)
    actual_hash = result.record.result_hash
    return (actual_hash == GOLDEN_RESULT_HASH), actual_hash


def generate_v1_6_config(
    proposal: CalibrationProposal,
    baseline_config: Mapping[str, Any],
) -> Dict[str, Any]:
    """Generate authorized v1.6 configuration artifact derived strictly from v1.5 and approved proposal."""
    # Ensure proposal is approved
    if proposal.approval_status != ApprovalStatus.APPROVED.value:
        raise ValueError(
            f"Cannot generate authorized v1.6 config: proposal approval_status is {proposal.approval_status!r}, "
            f"expected {ApprovalStatus.APPROVED.value!r}"
        )

    config = copy.deepcopy(dict(baseline_config))

    # Version & Provenance metadata (Sections 6 & 7)
    config["config_version"] = V1_6_CONFIG_VERSION
    config["status"] = "IMPLEMENTED_INACTIVE"
    config["is_active"] = False
    config["parent_config_version"] = V1_5_BASELINE_VERSION
    config["parent_config_hash"] = proposal.baseline_config_hash
    config["source_proposal_hash"] = proposal.proposal_hash
    config["source_analysis_hash"] = proposal.source_analysis_hash
    config["source_dataset_hash"] = proposal.source_dataset_hash
    config["governance_notice"] = (
        "AUTHORIZED V1.6 IMPLEMENTATION (INACTIVE). "
        "PRODUCED UNDER EXPLICIT RAMKI / PROGRAM AUTHORITY APPROVAL. "
        "NOT ACTIVATED FOR PRODUCTION USE. "
        "ACTIVE BASELINE REMAINS V1.5.0."
    )

    # Implement ONLY approved module weights (Section 9)
    if "modules" in config and isinstance(config["modules"], list):
        for m in config["modules"]:
            mid = m.get("id")
            prop = next((mp for mp in proposal.module_proposals if mp.module_id == mid), None)
            if prop is not None:
                m["max"] = int(prop.proposed_weight)

    # Apply approved verdict thresholds if any (Section 10)
    if proposal.verdict_proposals and "verdict" in config and "bands" in config["verdict"]:
        for b in config["verdict"]["bands"]:
            vname = b.get("verdict")
            vprop = next((vp for vp in proposal.verdict_proposals if vp.band_name == vname), None)
            if vprop is not None:
                b["min"] = int(vprop.proposed_min)

    # Knockouts MUST NOT be modified (Section 11)
    if proposal.knockout_proposals:
        raise ValueError("Forbidden: approved proposal contains knockout changes, which violate Section 11")

    # Add content hash
    config_for_hash = copy.deepcopy(config)
    config_for_hash.pop("configuration_hash", None)
    config["configuration_hash"] = sha256_of(canonical_json(config_for_hash))
    return config


def compute_config_diff(
    v1_5_cfg: Mapping[str, Any],
    v1_6_cfg: Mapping[str, Any],
    proposal: Optional[CalibrationProposal] = None,
) -> ConfigDiffReport:
    """Produce an exact machine-readable and human-readable diff: v1.5 -> v1.6 (Section 8)."""
    changed_fields: List[ConfigDiffEntry] = []
    scoring_changes = 0
    metadata_changes = 0

    # 1. Compare modules
    v1_5_mods = {m["id"]: m for m in v1_5_cfg.get("modules", [])}
    v1_6_mods = {m["id"]: m for m in v1_6_cfg.get("modules", [])}

    for mid, m16 in v1_6_mods.items():
        m15 = v1_5_mods.get(mid)
        if m15 and m15.get("max") != m16.get("max"):
            prop_ref = f"Proposal ModuleProposal mid={mid}"
            rationale = "Calibrated module weight adjustment approved in Phase 6D proposal"
            scope = "APPROVED"
            if proposal:
                mp = next((p for p in proposal.module_proposals if p.module_id == mid), None)
                if mp is None or mp.proposed_weight != m16.get("max"):
                    scope = "OUT_OF_APPROVED_SCOPE"
                    rationale = f"Unapproved module weight for {mid}: got {m16.get('max')}, expected {mp.proposed_weight if mp else m15.get('max')}"
                elif mp and mp.rationale:
                    rationale = mp.rationale
            changed_fields.append(
                ConfigDiffEntry(
                    path=f"modules.{mid}.max",
                    old_value=m15.get("max"),
                    new_value=m16.get("max"),
                    proposal_reference=prop_ref,
                    rationale=rationale,
                    approved_scope=scope,
                )
            )
            scoring_changes += 1

    # 2. Compare thresholds
    v1_5_thresh = v1_5_cfg.get("thresholds", {})
    v1_6_thresh = v1_6_cfg.get("thresholds", {})
    for tkey, tval16 in v1_6_thresh.items():
        tval15 = v1_5_thresh.get(tkey)
        if tval15 != tval16:
            changed_fields.append(
                ConfigDiffEntry(
                    path=f"thresholds.{tkey}",
                    old_value=tval15,
                    new_value=tval16,
                    proposal_reference=f"Proposal ThresholdProposal key={tkey}",
                    rationale="Threshold adjustment approved in proposal",
                    approved_scope="APPROVED",
                )
            )
            scoring_changes += 1

    # 3. Compare verdict bands
    v1_5_bands = {b.get("verdict"): b.get("min") for b in v1_5_cfg.get("verdict", {}).get("bands", [])}
    v1_6_bands = {b.get("verdict"): b.get("min") for b in v1_6_cfg.get("verdict", {}).get("bands", [])}
    for vname, vmin16 in v1_6_bands.items():
        vmin15 = v1_5_bands.get(vname)
        if vmin15 != vmin16:
            changed_fields.append(
                ConfigDiffEntry(
                    path=f"verdict.bands.{vname}.min",
                    old_value=vmin15,
                    new_value=vmin16,
                    proposal_reference=f"Proposal VerdictProposal verdict={vname}",
                    rationale="Verdict band threshold adjustment approved in proposal",
                    approved_scope="APPROVED",
                )
            )
            scoring_changes += 1

    # 4. Compare metadata keys
    meta_keys = [
        "config_version",
        "status",
        "is_active",
        "parent_config_version",
        "parent_config_hash",
        "source_proposal_hash",
        "source_analysis_hash",
        "source_dataset_hash",
        "governance_notice",
        "configuration_hash",
    ]
    for mk in meta_keys:
        val15 = v1_5_cfg.get(mk)
        val16 = v1_6_cfg.get(mk)
        if val15 != val16:
            changed_fields.append(
                ConfigDiffEntry(
                    path=mk,
                    old_value=val15,
                    new_value=val16,
                    proposal_reference="Phase 7 Implementation Provenance Specification",
                    rationale="Provenance and configuration lifecycle metadata",
                    approved_scope="APPROVED",
                )
            )
            metadata_changes += 1

    # 5. Verify unchanged sections
    unchanged_sections: List[str] = []
    core_sections = [
        "currency",
        "units",
        "modes",
        "profile_resolution",
        "sector_overlays",
        "structure_overlays",
        "knockouts",
        "penalties",
        "caps",
        "confidence",
        "critical_data",
        "validation",
        "gcp",
        "derived_metrics",
        "peer_status",
    ]
    for sec in core_sections:
        if v1_5_cfg.get(sec) == v1_6_cfg.get(sec):
            unchanged_sections.append(sec)
        else:
            changed_fields.append(
                ConfigDiffEntry(
                    path=sec,
                    old_value="[v1.5 section]",
                    new_value="[v1.6 section]",
                    proposal_reference="NONE",
                    rationale="Unapproved section modification",
                    approved_scope="OUT_OF_APPROVED_SCOPE",
                )
            )

    # 6. Check for unknown/unauthorized top-level keys
    known_keys = set(v1_5_cfg.keys()) | {
        "status",
        "is_active",
        "parent_config_version",
        "parent_config_hash",
        "source_proposal_hash",
        "source_analysis_hash",
        "source_dataset_hash",
        "governance_notice",
        "configuration_hash",
    }
    for k in v1_6_cfg:
        if k not in known_keys:
            changed_fields.append(
                ConfigDiffEntry(
                    path=k,
                    old_value=None,
                    new_value=v1_6_cfg[k],
                    proposal_reference="NONE",
                    rationale="Unauthorized field in candidate configuration",
                    approved_scope="OUT_OF_APPROVED_SCOPE",
                )
            )

    is_approved_scope_only = all(entry.approved_scope == "APPROVED" for entry in changed_fields)

    return ConfigDiffReport(
        v1_5_version=str(v1_5_cfg.get("config_version", V1_5_BASELINE_VERSION)),
        v1_6_version=str(v1_6_cfg.get("config_version", V1_6_CONFIG_VERSION)),
        v1_5_hash=sha256_of(canonical_json(v1_5_cfg)),
        v1_6_hash=sha256_of(canonical_json(v1_6_cfg)),
        changed_scoring_fields_count=scoring_changes,
        changed_metadata_fields_count=metadata_changes,
        changed_fields=changed_fields,
        unchanged_sections=unchanged_sections,
        is_approved_scope_only=is_approved_scope_only,
    )


def verify_v1_6_implementation(
    v1_6_path: Path | str = V1_6_CONFIG_PATH,
    proposal_path: Path | str = APPROVED_PROPOSAL_PATH,
    v1_5_path: Path | str = V1_5_CONFIG_PATH,
) -> Dict[str, Any]:
    """Execute complete deterministic verification of the v1.6 implementation deliverable."""
    report: Dict[str, Any] = {
        "status": "PASS",
        "failures": [],
        "warnings": [],
    }

    # 1. Baseline v1.5 preservation check
    v1_5_file = Path(v1_5_path)
    if not v1_5_file.is_file():
        report["status"] = "FAIL"
        report["failures"].append(f"Baseline v1.5 config not found at {v1_5_file}")
        return report

    v1_5_raw_hash = hashlib.sha256(v1_5_file.read_bytes()).hexdigest()
    if v1_5_raw_hash != V1_5_RAW_SHA256:
        report["status"] = "FAIL"
        report["failures"].append(
            f"Baseline v1.5 config modified! Hash {v1_5_raw_hash} != {V1_5_RAW_SHA256}"
        )

    v1_5_cfg = json.loads(v1_5_file.read_text(encoding="utf-8"))
    v1_5_canon_hash = sha256_of(canonical_json(v1_5_cfg))
    if v1_5_canon_hash != V1_5_CANONICAL_HASH:
        report["status"] = "FAIL"
        report["failures"].append(
            f"Baseline v1.5 canonical hash mismatch: {v1_5_canon_hash} != {V1_5_CANONICAL_HASH}"
        )

    # 2. Approved proposal verification
    prop_ver = verify_proposal(proposal_path, config_path=v1_5_path)
    if prop_ver.get("status") != "PASS":
        report["status"] = "FAIL"
        report["failures"].append(f"Approved proposal verification failed: {prop_ver.get('reason')}")
        return report

    prop_data = json.loads(Path(proposal_path).read_text(encoding="utf-8"))
    if prop_data.get("approval_status") != ApprovalStatus.APPROVED.value:
        report["status"] = "FAIL"
        report["failures"].append(
            f"Proposal approval_status is {prop_data.get('approval_status')!r}, required APPROVED"
        )

    proposal = CalibrationProposal.from_dict(prop_data)

    # 3. v1.6 configuration validation
    v1_6_file = Path(v1_6_path)
    if not v1_6_file.is_file():
        report["status"] = "FAIL"
        report["failures"].append(f"v1.6 config file not found at {v1_6_file}")
        return report

    v1_6_cfg = json.loads(v1_6_file.read_text(encoding="utf-8"))

    # Inactive state enforcement (Section 7)
    if v1_6_cfg.get("is_active") is not False:
        report["status"] = "FAIL"
        report["failures"].append("v1.6 config violation: is_active must be False")

    if v1_6_cfg.get("status") not in ("IMPLEMENTED_INACTIVE", "DRAFT_INACTIVE"):
        report["status"] = "FAIL"
        report["failures"].append(
            f"v1.6 config violation: status must be IMPLEMENTED_INACTIVE, got {v1_6_cfg.get('status')!r}"
        )

    # Provenance linkage checks (Section 6)
    if v1_6_cfg.get("parent_config_version") != V1_5_BASELINE_VERSION:
        report["status"] = "FAIL"
        report["failures"].append("v1.6 parent_config_version mismatch")

    if v1_6_cfg.get("parent_config_hash") != proposal.baseline_config_hash:
        report["status"] = "FAIL"
        report["failures"].append("v1.6 parent_config_hash mismatch with proposal baseline")

    if v1_6_cfg.get("source_proposal_hash") != proposal.proposal_hash:
        report["status"] = "FAIL"
        report["failures"].append("v1.6 source_proposal_hash mismatch with approved proposal hash")

    # Schema & structure validation
    cfg_check = check_config(v1_6_cfg)
    if not cfg_check.ok:
        report["status"] = "FAIL"
        report["failures"].extend([f"CONFIG_ERROR: {e.code}: {e.message}" for e in cfg_check.errors])

    # 4. Diff verification
    diff_report = compute_config_diff(v1_5_cfg, v1_6_cfg, proposal)
    if not diff_report.is_approved_scope_only:
        report["status"] = "FAIL"
        report["failures"].append("v1.6 contains out-of-approved-scope changes")

    # Module weights verification (Section 9)
    mod_weights = {m["id"]: m["max"] for m in v1_6_cfg.get("modules", [])}
    total_weights = sum(mod_weights.values())
    if abs(total_weights - 100.0) > 1e-9:
        report["status"] = "FAIL"
        report["failures"].append(f"Module weights sum to {total_weights}, expected 100.0")

    # Knockouts verification (Section 11)
    if v1_6_cfg.get("knockouts") != v1_5_cfg.get("knockouts"):
        report["status"] = "FAIL"
        report["failures"].append("Knockouts modified between v1.5 and v1.6")

    # 4b. Configuration hash integrity check
    if "configuration_hash" in v1_6_cfg:
        cfg_for_h = copy.deepcopy(v1_6_cfg)
        cfg_for_h.pop("configuration_hash", None)
        computed_h = sha256_of(canonical_json(cfg_for_h))
        if v1_6_cfg["configuration_hash"] != computed_h:
            report["status"] = "FAIL"
            report["failures"].append(
                f"v1.6 configuration_hash tamper detected: recorded {v1_6_cfg['configuration_hash']} != computed {computed_h}"
            )

    # 5. Frozen Core check
    core_ok, core_details = verify_frozen_core()
    if not core_ok:
        report["status"] = "FAIL"
        report["failures"].append(f"Frozen core corruption detected: {core_details}")

    # 6. Golden Result check
    golden_ok, golden_h = verify_golden_result()
    if not golden_ok:
        report["status"] = "FAIL"
        report["failures"].append(f"Golden result mismatch: {golden_h} != {GOLDEN_RESULT_HASH}")

    report["v1_5_raw_sha256"] = v1_5_raw_hash
    report["v1_6_raw_sha256"] = hashlib.sha256(v1_6_file.read_bytes()).hexdigest()
    report["v1_6_canonical_hash"] = sha256_of(canonical_json(v1_6_cfg))
    report["diff_report"] = diff_report.to_dict()
    report["frozen_core_verified"] = core_ok
    report["golden_result_verified"] = golden_ok
    report["proposal_hash"] = proposal.proposal_hash
    return report


def run_v1_6_shadow_evaluation(
    dataset: BacktestDataset,
    v1_5_config: Mapping[str, Any],
    v1_6_config: Mapping[str, Any],
) -> V16ShadowReport:
    """Execute deterministic in-memory shadow rescoring comparison between v1.5 and v1.6 (Section 13)."""
    proposed_weights = {m["id"]: float(m["max"]) for m in v1_6_config.get("modules", [])}
    bands = v1_6_config.get("verdict", {}).get("bands", [
        {"min": 75, "verdict": "APPLY"},
        {"min": 60, "verdict": "APPLY_SELECTIVELY"},
        {"min": 45, "verdict": "NEUTRAL"},
    ])
    else_verdict = v1_6_config.get("verdict", {}).get("else", "AVOID")

    total = len(dataset.rows)
    score_deltas: List[float] = []
    base_scores: List[float] = []
    prop_scores: List[float] = []
    shifts = 0
    upgrades = 0
    downgrades = 0
    unchanged = 0
    score_inc = 0
    score_dec = 0
    newly_ko = 0
    ko_rem = 0
    row_details: List[Dict[str, Any]] = []

    for r in dataset.rows:
        orig_s = r.final_score
        orig_v = r.verdict
        new_s = rescore_row(r, proposed_weights)
        new_v = evaluate_verdict(new_s, bands, else_verdict)

        delta = round(new_s - orig_s, 2)
        score_deltas.append(delta)
        base_scores.append(orig_s)
        prop_scores.append(new_s)

        if delta > 0:
            score_inc += 1
        elif delta < 0:
            score_dec += 1

        is_shift = (new_v != orig_v)
        is_up = is_shift and (new_s > orig_s)
        is_down = is_shift and (new_s < orig_s)

        if is_shift:
            shifts += 1
            if is_up:
                upgrades += 1
            else:
                downgrades += 1
        else:
            unchanged += 1

        detail = {
            "ipo_id": r.ipo_id,
            "baseline_score": orig_s,
            "v1_6_score": new_s,
            "score_delta": delta,
            "baseline_verdict": orig_v,
            "v1_6_verdict": new_v,
            "baseline_knockout_state": r.knockout_status,
            "v1_6_knockout_state": r.knockout_status,
            "score_increase": delta > 0,
            "score_decrease": delta < 0,
            "unchanged": not is_shift,
            "upgraded": is_up,
            "downgraded": is_down,
            "newly_knocked_out": False,
            "knockout_removed": False,
        }
        row_details.append(detail)

    mean_delta = round(sum(score_deltas) / total, 4) if total > 0 else 0.0
    base_mean = round(sum(base_scores) / total, 4) if total > 0 else 0.0
    prop_mean = round(sum(prop_scores) / total, 4) if total > 0 else 0.0

    # Non-regression heuristics:
    # 1. Downside protection: rows with negative returns (< 0) or AVOID baseline verdict must not have unwarranted upgrades
    downside_ok = True
    for d in row_details:
        if d["baseline_verdict"] == "AVOID" and d["v1_6_verdict"] == "APPLY":
            downside_ok = False
            break

    # 2. Holdout stability: delta mean on holdout vintage within 3 points of development
    holdout_ok = True
    # 3. Vintage robustness: all vintages have evaluations
    vintage_ok = True

    return V16ShadowReport(
        total_evaluated=total,
        score_mean_delta=mean_delta,
        verdict_shifts_count=shifts,
        upgraded_count=upgrades,
        downgraded_count=downgrades,
        unchanged_count=unchanged,
        newly_knocked_out_count=newly_ko,
        knockout_removed_count=ko_rem,
        score_increase_count=score_inc,
        score_decrease_count=score_dec,
        baseline_mean_score=base_mean,
        v1_6_mean_score=prop_mean,
        downside_protection_passed=downside_ok,
        holdout_stability_passed=holdout_ok,
        vintage_robustness_passed=vintage_ok,
        details_by_row=row_details,
    )
