"""Phase 6A: Linked child observation storage.

Persists PostListingObservation artifacts under <store>/<final-evaluation-id>/observations/
with an independent observation manifest. Strictly preserves parent evaluation artifacts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import PostListingObservation
from .return_engine import compute_observation_hashes, sha256_canonical_dict


class ObservationStorageError(Exception):
    """Base error for observation storage operations."""
    pass


class NotFinalEvaluationError(ObservationStorageError):
    """Raised when attempting to attach an observation to a non-FINAL evaluation."""
    pass


class ResultHashMismatchError(ObservationStorageError):
    """Raised when final evaluation result hash does not match."""
    pass


class EvaluationNotFoundError(ObservationStorageError):
    """Raised when parent evaluation directory or evaluation.json does not exist."""
    pass


def get_observations_dir(store_root: str | Path, final_evaluation_id: str) -> Path:
    """Return the observations child directory for a given final evaluation."""
    return Path(store_root) / final_evaluation_id / "observations"


def validate_parent_evaluation(store_root: str | Path, final_evaluation_id: str) -> Dict[str, Any]:
    """Validate that the parent evaluation exists, is FINAL, and return its evaluation.json."""
    eval_dir = Path(store_root) / final_evaluation_id
    eval_file = eval_dir / "evaluation.json"

    if not eval_file.is_file():
        raise EvaluationNotFoundError(f"parent evaluation not found: {eval_file}")

    with eval_file.open("r", encoding="utf-8") as handle:
        record = json.load(handle)

    mode = str(record.get("evaluation_mode", "")).upper()
    if mode != "FINAL":
        raise NotFinalEvaluationError(
            f"cannot attach post-listing observation to evaluation {final_evaluation_id} "
            f"with mode {mode!r} (must be FINAL)"
        )

    return record


def save_observation(
    observation: PostListingObservation,
    store_root: str | Path,
) -> Path:
    """Persist an observation to <store>/<final_evaluation_id>/observations/.

    Ensures parent evaluation is validated and untouched.
    Updates child observations/manifest.json.
    """
    store_path = Path(store_root)
    eval_record = validate_parent_evaluation(store_path, observation.final_evaluation_id)

    # Check result hash consistency
    expected_hash = eval_record.get("result_hash")
    if expected_hash and expected_hash != observation.final_result_hash:
        raise ResultHashMismatchError(
            f"observation final_result_hash {observation.final_result_hash} does not match "
            f"evaluation.json result_hash {expected_hash}"
        )

    obs_dir = get_observations_dir(store_path, observation.final_evaluation_id)
    obs_dir.mkdir(parents=True, exist_ok=True)

    # File name convention: observation_1w.json or observation_1w_v2.json
    h_lower = observation.horizon.lower()
    if observation.version > 1:
        file_name = f"observation_{h_lower}_v{observation.version}.json"
    else:
        file_name = f"observation_{h_lower}.json"

    target_file = obs_dir / file_name

    # Write observation JSON canonically
    obs_dict = observation.to_dict()
    with target_file.open("w", encoding="utf-8") as handle:
        json.dump(obs_dict, handle, indent=2, sort_keys=True)
        handle.write("\n")

    # Update child manifest inside observations directory
    _update_observations_manifest(obs_dir)

    return target_file


def _update_observations_manifest(obs_dir: Path) -> Path:
    """Regenerate child manifest.json inside obs_dir."""
    manifest_entries: Dict[str, Dict[str, Any]] = {}

    for f in sorted(obs_dir.glob("observation_*.json")):
        with f.open("rb") as handle:
            raw_bytes = handle.read()
        file_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
            obs_id = data.get("observation_id", f.stem)
            horizon = data.get("horizon", "")
            version = data.get("version", 1)
            obs_hash = (data.get("calculation") or {}).get("observation_hash", "")
        except Exception:
            obs_id = f.stem
            horizon = ""
            version = 1
            obs_hash = ""

        manifest_entries[f.name] = {
            "observation_id": obs_id,
            "horizon": horizon,
            "version": version,
            "file_sha256": file_sha256,
            "observation_hash": obs_hash,
            "byte_count": len(raw_bytes),
        }

    manifest_payload = {
        "manifest_version": "1.0.0",
        "observations": manifest_entries,
    }
    manifest_file = obs_dir / "manifest.json"
    with manifest_file.open("w", encoding="utf-8") as handle:
        json.dump(manifest_payload, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return manifest_file


def list_observations(store_root: str | Path, final_evaluation_id: str) -> List[PostListingObservation]:
    """Read all observations for a given final evaluation, sorted by horizon and version."""
    obs_dir = get_observations_dir(store_root, final_evaluation_id)
    if not obs_dir.is_dir():
        return []

    observations: List[PostListingObservation] = []
    for f in sorted(obs_dir.glob("observation_*.json")):
        with f.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        observations.append(PostListingObservation.from_dict(data))

    return observations


def read_observation(
    store_root: str | Path,
    final_evaluation_id: str,
    horizon: str,
    version: Optional[int] = None,
) -> Optional[PostListingObservation]:
    """Read a specific observation by horizon and optional version."""
    obs_dir = get_observations_dir(store_root, final_evaluation_id)
    if not obs_dir.is_dir():
        return None

    h_lower = horizon.lower()
    if version is not None and version > 1:
        f = obs_dir / f"observation_{h_lower}_v{version}.json"
        if not f.is_file():
            return None
        with f.open("r", encoding="utf-8") as handle:
            return PostListingObservation.from_dict(json.load(handle))

    # Look for unversioned / latest version
    candidates: List[PostListingObservation] = []
    for f in obs_dir.glob(f"observation_{h_lower}*.json"):
        with f.open("r", encoding="utf-8") as handle:
            obs = PostListingObservation.from_dict(json.load(handle))
            if version is None or obs.version == version:
                candidates.append(obs)

    if not candidates:
        return None

    # Return latest version
    candidates.sort(key=lambda o: o.version)
    return candidates[-1]


def verify_observation_hashes(
    store_root: str | Path,
    final_evaluation_id: str,
) -> Dict[str, Any]:
    """Audit verification of all observations stored under final_evaluation_id.

    Checks:
    1. Child manifest existence and hash consistency.
    2. Recomputed inputs hash and observation hash for each observation.
    3. Consistency with parent evaluation result hash.
    """
    obs_dir = get_observations_dir(store_root, final_evaluation_id)
    if not obs_dir.is_dir():
        return {"status": "NO_OBSERVATIONS", "evaluation_id": final_evaluation_id, "items": []}

    parent_record = validate_parent_evaluation(store_root, final_evaluation_id)
    expected_result_hash = parent_record.get("result_hash")

    items: List[Dict[str, Any]] = []
    all_ok = True

    for f in sorted(obs_dir.glob("observation_*.json")):
        with f.open("rb") as handle:
            raw_bytes = handle.read()
        file_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        data = json.loads(raw_bytes.decode("utf-8"))
        obs = PostListingObservation.from_dict(data)

        # Check result hash
        res_hash_match = (obs.final_result_hash == expected_result_hash)

        # Recompute observation hash
        re_inputs_hash, re_obs_hash = compute_observation_hashes(
            final_evaluation_id=obs.final_evaluation_id,
            final_result_hash=obs.final_result_hash,
            ipo_id=obs.ipo_id,
            horizon=obs.horizon,
            listing_date=obs.listing_date,
            target_date=obs.target_observation_date,
            actual_date=obs.actual_observation_date,
            prices_dict=obs.prices.to_dict(),
            benchmark_dict=obs.benchmark.to_dict(),
            returns_dict=obs.returns.to_dict(),
            provenance_dict=obs.provenance.to_dict(),
            calc_version=obs.calculation.calculation_version,
        )

        calc_hash_match = (re_obs_hash == obs.calculation.observation_hash)
        inputs_hash_match = (re_inputs_hash == obs.calculation.calculation_inputs_hash)

        ok = res_hash_match and calc_hash_match and inputs_hash_match
        if not ok:
            all_ok = False

        items.append({
            "file": f.name,
            "observation_id": obs.observation_id,
            "horizon": obs.horizon,
            "version": obs.version,
            "file_sha256": file_sha256,
            "result_hash_match": res_hash_match,
            "observation_hash_match": calc_hash_match,
            "inputs_hash_match": inputs_hash_match,
            "status": "OK" if ok else "MISMATCH",
        })

    return {
        "status": "OK" if all_ok else "MISMATCH",
        "evaluation_id": final_evaluation_id,
        "items": items,
    }
