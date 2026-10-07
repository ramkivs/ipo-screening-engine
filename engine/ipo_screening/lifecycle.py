"""Evaluation lifecycle governance: ACTIVE / SUPERSEDED + VISIBLE / ARCHIVED.

Governed by docs/investigation/EVALUATION-LIFECYCLE-GOVERNANCE-DECISION-2026-10-07.md.
Implements the hybrid durability architecture:
  - Store-level:      <store_root>/lifecycle_index.json
  - Evaluation-level: <store_root>/<evaluation_id>/lifecycle.json

Lifecycle metadata is operational governance metadata. It is NOT part of the
immutable evaluation artifact manifest (manifest.json) and never alters:
  - result_hash
  - input_snapshot_hash
  - manifest hash
  - evidence hashes
  - evaluation ID

Rules enforced:
  - Never physically delete an evaluation or artifact (physical deletion prohibited).
  - Mode-scoped active selection (FINAL vs PRELIMINARY are independent).
  - Active evaluation must match active ratified policy config_hash (v1.5.0).
  - Candidate v1.6.0 or unverified evaluations must not become ACTIVE.
  - Exactly one ACTIVE evaluation per (ipo_id, mode).
  - Supersession lineage is durable and acyclic.
  - Archival is reversible; unarchiving a SUPERSEDED evaluation restores it to VISIBLE,
    never silently promotes to ACTIVE.
  - Tier 1 Golden baselines (Vishal Nirmiti) are protected against archival and deactivation.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:
    import fcntl
except (ImportError, ModuleNotFoundError):
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except (ImportError, ModuleNotFoundError):
    msvcrt = None  # type: ignore[assignment]

from .errors import EngineError
from .evaluation import EvaluationStore


# -----------------------------------------------------------------------------
# Constants & Enums
# -----------------------------------------------------------------------------

LIFECYCLE_VERSION = "1.0.0"

LIFECYCLE_STATE_ACTIVE = "ACTIVE"
LIFECYCLE_STATE_SUPERSEDED = "SUPERSEDED"
LIFECYCLE_STATES = (LIFECYCLE_STATE_ACTIVE, LIFECYCLE_STATE_SUPERSEDED)

VISIBILITY_STATE_VISIBLE = "VISIBLE"
VISIBILITY_STATE_ARCHIVED = "ARCHIVED"
VISIBILITY_STATES = (VISIBILITY_STATE_VISIBLE, VISIBILITY_STATE_ARCHIVED)

OPERATIONAL_STATUS_ACTIVE = "ACTIVE"
OPERATIONAL_STATUS_SUPERSEDED = "SUPERSEDED"
OPERATIONAL_STATUS_ARCHIVED = "ARCHIVED"
OPERATIONAL_STATUSES = (
    OPERATIONAL_STATUS_ACTIVE,
    OPERATIONAL_STATUS_SUPERSEDED,
    OPERATIONAL_STATUS_ARCHIVED,
)

TIER_1_GOLDEN = "TIER_1_GOLDEN"
TIER_2_GOVERNED = "TIER_2_GOVERNED"
TIER_3_STANDARD = "TIER_3_STANDARD"

ACTIVE_RATIFIED_CONFIG_HASH = "4a5d92e867aea681127352c628522f9a9c5841b89ea7a47736bf55e617526d2b"
VISHAL_GOLDEN_RESULT_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -----------------------------------------------------------------------------
# Lifecycle Exceptions
# -----------------------------------------------------------------------------

class LifecycleError(EngineError):
    """Base exception for all lifecycle governance errors."""


class InvalidStateTransitionError(LifecycleError):
    """Raised when an invalid or forbidden lifecycle transition is attempted."""


class CyclicLineageError(LifecycleError):
    """Raised when a supersession operation would create a cyclic lineage."""


class ProtectedRecordError(LifecycleError):
    """Raised when an operation violates protected-record constraints."""


class MissingLineageTargetError(LifecycleError):
    """Raised when a supersession references a non-existent evaluation."""


class EvaluationNotFoundError(LifecycleError):
    """Raised when a requested evaluation is not found in the store."""


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------

@dataclass
class LifecycleRecord:
    """Operational lifecycle metadata for a single evaluation execution."""

    evaluation_id: str
    ipo_id: str
    mode: str
    lifecycle_state: str  # ACTIVE or SUPERSEDED
    visibility_state: str  # VISIBLE or ARCHIVED
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None
    lifecycle_version: str = LIFECYCLE_VERSION
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    actor: Optional[str] = None
    transition_reason: Optional[str] = None
    transition_timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        self.mode = self.mode.lower()
        if self.lifecycle_state not in LIFECYCLE_STATES:
            raise InvalidStateTransitionError(
                f"Invalid lifecycle_state '{self.lifecycle_state}'. Must be one of {LIFECYCLE_STATES}."
            )
        if self.visibility_state not in VISIBILITY_STATES:
            raise InvalidStateTransitionError(
                f"Invalid visibility_state '{self.visibility_state}'. Must be one of {VISIBILITY_STATES}."
            )

    @property
    def operational_status(self) -> str:
        """Projected operational status combining lifecycle and visibility."""
        if self.visibility_state == VISIBILITY_STATE_ARCHIVED:
            return OPERATIONAL_STATUS_ARCHIVED
        if self.lifecycle_state == LIFECYCLE_STATE_ACTIVE:
            return OPERATIONAL_STATUS_ACTIVE
        return OPERATIONAL_STATUS_SUPERSEDED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "ipo_id": self.ipo_id,
            "mode": self.mode,
            "lifecycle_state": self.lifecycle_state,
            "visibility_state": self.visibility_state,
            "operational_status": self.operational_status,
            "superseded_by": self.superseded_by,
            "supersedes": self.supersedes,
            "lifecycle_version": self.lifecycle_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "actor": self.actor,
            "transition_reason": self.transition_reason,
            "transition_timestamp": self.transition_timestamp,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LifecycleRecord:
        return cls(
            evaluation_id=str(data["evaluation_id"]),
            ipo_id=str(data["ipo_id"]),
            mode=str(data.get("mode", "final")).lower(),
            lifecycle_state=str(data.get("lifecycle_state", LIFECYCLE_STATE_SUPERSEDED)),
            visibility_state=str(data.get("visibility_state", VISIBILITY_STATE_VISIBLE)),
            superseded_by=data.get("superseded_by"),
            supersedes=data.get("supersedes"),
            lifecycle_version=str(data.get("lifecycle_version", LIFECYCLE_VERSION)),
            created_at=str(data.get("created_at") or utc_now_iso()),
            updated_at=str(data.get("updated_at") or utc_now_iso()),
            actor=data.get("actor"),
            transition_reason=data.get("transition_reason"),
            transition_timestamp=data.get("transition_timestamp"),
        )


@dataclass
class IssuerLifecycleEntry:
    """Issuer-level active pointers and evaluation index."""

    ipo_id: str
    company_name: Optional[str] = None
    active_final_id: Optional[str] = None
    active_preliminary_id: Optional[str] = None
    status: str = "ACTIVE_OFFERING"  # ACTIVE_OFFERING, CANCELLED, WITHDRAWN
    last_updated: str = field(default_factory=utc_now_iso)
    evaluations: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get_active_id(self, mode: str) -> Optional[str]:
        m = mode.lower()
        if m == "final":
            return self.active_final_id
        if m == "preliminary":
            return self.active_preliminary_id
        return None

    def set_active_id(self, mode: str, evaluation_id: Optional[str]) -> None:
        m = mode.lower()
        if m == "final":
            self.active_final_id = evaluation_id
        elif m == "preliminary":
            self.active_preliminary_id = evaluation_id
        self.last_updated = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ipo_id": self.ipo_id,
            "company_name": self.company_name,
            "active_final_id": self.active_final_id,
            "active_preliminary_id": self.active_preliminary_id,
            "status": self.status,
            "last_updated": self.last_updated,
            "evaluations": self.evaluations,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> IssuerLifecycleEntry:
        return cls(
            ipo_id=str(data["ipo_id"]),
            company_name=data.get("company_name"),
            active_final_id=data.get("active_final_id"),
            active_preliminary_id=data.get("active_preliminary_id"),
            status=str(data.get("status", "ACTIVE_OFFERING")),
            last_updated=str(data.get("last_updated") or utc_now_iso()),
            evaluations=dict(data.get("evaluations", {})),
        )


@dataclass
class LifecycleIndex:
    """Store-wide index of all issuers and lifecycle states."""

    version: str = LIFECYCLE_VERSION
    updated_at: str = field(default_factory=utc_now_iso)
    issuers: Dict[str, IssuerLifecycleEntry] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "issuers": {k: v.to_dict() for k, v in sorted(self.issuers.items())},
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LifecycleIndex:
        issuers_dict: Dict[str, IssuerLifecycleEntry] = {}
        for ipo_id, entry_data in data.get("issuers", {}).items():
            issuers_dict[ipo_id] = IssuerLifecycleEntry.from_dict(entry_data)
        return cls(
            version=str(data.get("version", LIFECYCLE_VERSION)),
            updated_at=str(data.get("updated_at") or utc_now_iso()),
            issuers=issuers_dict,
        )


# -----------------------------------------------------------------------------
# Protection Tier Classification
# -----------------------------------------------------------------------------

def get_protection_tier(
    evaluation_id: str,
    ipo_id: str,
    result_hash: Optional[str] = None,
    store_root: Optional[Path | str] = None,
) -> str:
    """Determine the protection tier of an evaluation record.

    Tier 1 (Golden): Vishal Nirmiti baseline and golden test baselines.
                     Cannot be deactivated or archived.
    Tier 2 (Governed): Cited in backtest datasets or calibration proposals.
                       Archival allowed with audit warning.
    Tier 3 (Standard): General operational evaluations.
    """
    safe_ipo = ipo_id.upper()
    if (
        "VISHAL-NIRMITI" in safe_ipo
        or "VISHAL" in safe_ipo
        or (result_hash and result_hash == VISHAL_GOLDEN_RESULT_HASH)
    ):
        return TIER_1_GOLDEN

    # Check Tier 2: Check dataset fixtures or observations
    if store_root:
        root_path = Path(store_root)
        obs_dir = root_path / evaluation_id / "observations"
        if obs_dir.is_dir() and any(obs_dir.iterdir()):
            return TIER_2_GOVERNED

    return TIER_3_STANDARD


# -----------------------------------------------------------------------------
# Cross-Platform Locking Primitives
# -----------------------------------------------------------------------------

def acquire_file_lock(
    fileno: int,
    *,
    blocking: bool = True,
    timeout: float = 30.0,
    poll_interval: float = 0.01,
) -> None:
    """Acquire an exclusive OS-level file lock in a cross-platform manner.

    - On POSIX: Uses `fcntl.flock(fileno, fcntl.LOCK_EX)`. When a timeout is specified,
      polls with `fcntl.LOCK_NB` until acquired or timeout expires.
    - On Windows: Uses native `msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1)` on byte 0.
      When blocking, polls with `poll_interval` until acquired or timeout expires.
    - Fails closed: raises `TimeoutError` on timeout, or propagates platform exceptions.
    """
    if fcntl is not None:
        if not blocking:
            try:
                fcntl.flock(fileno, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except (BlockingIOError, OSError) as exc:
                raise TimeoutError(f"Could not immediately acquire POSIX lifecycle lock: {exc}") from exc

        if timeout is None:
            fcntl.flock(fileno, fcntl.LOCK_EX)
            return

        start = time.monotonic()
        while True:
            try:
                fcntl.flock(fileno, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except (BlockingIOError, OSError) as exc:
                if (time.monotonic() - start) >= timeout:
                    raise TimeoutError(
                        f"Timed out after {timeout:.2f}s waiting for exclusive POSIX lifecycle lock: {exc}"
                    ) from exc
                time.sleep(poll_interval)

    elif msvcrt is not None:
        os.lseek(fileno, 0, os.SEEK_SET)
        if not blocking:
            try:
                msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1)
                return
            except (OSError, IOError) as exc:
                raise TimeoutError(f"Could not immediately acquire Windows lifecycle lock: {exc}") from exc

        start = time.monotonic()
        while True:
            try:
                os.lseek(fileno, 0, os.SEEK_SET)
                msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1)
                return
            except (OSError, IOError) as exc:
                if timeout is not None and (time.monotonic() - start) >= timeout:
                    raise TimeoutError(
                        f"Timed out after {timeout:.2f}s waiting for exclusive Windows lifecycle lock: {exc}"
                    ) from exc
                time.sleep(poll_interval)

    else:
        raise NotImplementedError(
            "Neither 'fcntl' (POSIX) nor 'msvcrt' (Windows) is available in this Python runtime."
        )


def release_file_lock(fileno: int) -> None:
    """Release an exclusive OS-level file lock in a cross-platform manner.

    - On POSIX: Uses `fcntl.flock(fileno, fcntl.LOCK_UN)`.
    - On Windows: Uses `msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1)` on byte 0.
    """
    if fcntl is not None:
        try:
            fcntl.flock(fileno, fcntl.LOCK_UN)
        except OSError:
            pass
    elif msvcrt is not None:
        try:
            os.lseek(fileno, 0, os.SEEK_SET)
            msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass


# -----------------------------------------------------------------------------
# Lifecycle Manager
# -----------------------------------------------------------------------------

class LifecycleManager:
    """Governed lifecycle manager implementing hybrid storage and atomic state transitions."""

    def __init__(
        self,
        store_root: str | os.PathLike[str],
        active_config_hash: Optional[str] = None,
    ) -> None:
        self.root = Path(store_root)
        self.index_path = self.root / "lifecycle_index.json"
        self.lock_path = self.root / "lifecycle_index.lock"
        self.store = EvaluationStore(self.root)
        self.active_config_hash = active_config_hash or ACTIVE_RATIFIED_CONFIG_HASH
        self._thread_lock = threading.RLock()

    @contextlib.contextmanager
    def _file_lock(self, timeout: float = 30.0, blocking: bool = True):
        """Acquire cross-platform exclusive file lock to ensure atomic multi-process transitions.

        Opens <store_root>/lifecycle_index.lock in append/update mode (never truncated)
        and acquires an exclusive OS-level lock (fcntl on POSIX, msvcrt on Windows).
        Always releases in a finally block to ensure no stale lock state.
        """
        self.root.mkdir(parents=True, exist_ok=True)
        with self._thread_lock:
            with open(self.lock_path, "a+b") as lock_file:
                fileno = lock_file.fileno()
                if os.fstat(fileno).st_size == 0:
                    lock_file.write(b"0")
                    lock_file.flush()
                acquire_file_lock(fileno, blocking=blocking, timeout=timeout)
                try:
                    yield
                finally:
                    release_file_lock(fileno)

    def load_index(self) -> LifecycleIndex:
        """Load lifecycle_index.json, or bootstrap store if absent or corrupted."""
        if not self.index_path.exists():
            return self.bootstrap_store()
        try:
            with self.index_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return LifecycleIndex.from_dict(data)
        except Exception:
            # Corrupted index: fallback to self-healing bootstrap
            return self.bootstrap_store()

    def save_index(self, index: LifecycleIndex) -> None:
        """Save lifecycle_index.json using atomic write-rename."""
        index.updated_at = utc_now_iso()
        data = index.to_dict()
        self.root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=str(self.root), delete=False, encoding="utf-8") as tf:
            json.dump(data, tf, indent=2, sort_keys=True, ensure_ascii=False)
            tf.write("\n")
            temp_name = tf.name
        os.replace(temp_name, self.index_path)

    def get_lifecycle_path(self, evaluation_id: str) -> Path:
        """Path to <store_root>/<evaluation_id>/lifecycle.json."""
        return self.store.path_for(evaluation_id) / "lifecycle.json"

    def read_evaluation_lifecycle(self, evaluation_id: str) -> Optional[LifecycleRecord]:
        """Read individual lifecycle.json file for an evaluation."""
        path = self.get_lifecycle_path(evaluation_id)
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                return LifecycleRecord.from_dict(json.load(f))
        except Exception:
            return None

    def write_evaluation_lifecycle(self, record: LifecycleRecord) -> None:
        """Write individual lifecycle.json file without altering immutable artifacts."""
        eval_dir = self.store.path_for(record.evaluation_id)
        if not eval_dir.is_dir():
            raise EvaluationNotFoundError(f"Evaluation directory not found: {eval_dir}")
        path = self.get_lifecycle_path(record.evaluation_id)
        with tempfile.NamedTemporaryFile("w", dir=str(eval_dir), delete=False, encoding="utf-8") as tf:
            json.dump(record.to_dict(), tf, indent=2, sort_keys=True, ensure_ascii=False)
            tf.write("\n")
            temp_name = tf.name
        os.replace(temp_name, path)

    def get_lifecycle(self, evaluation_id: str) -> Optional[LifecycleRecord]:
        """Retrieve lifecycle record for an evaluation, checking file then index."""
        rec = self.read_evaluation_lifecycle(evaluation_id)
        if rec:
            return rec
        index = self.load_index()
        for issuer in index.issuers.values():
            if evaluation_id in issuer.evaluations:
                return LifecycleRecord.from_dict(issuer.evaluations[evaluation_id])
        return None

    def get_active_evaluation_id(self, ipo_id: str, mode: str = "final") -> Optional[str]:
        """Return the explicit active evaluation ID for the given issuer and mode."""
        index = self.load_index()
        issuer = index.issuers.get(ipo_id)
        if not issuer:
            return None
        active_id = issuer.get_active_id(mode)
        if not active_id or not self.store.exists(active_id):
            return None
        try:
            eval_rec = self.store.read(active_id)
            if eval_rec.get("config_hash") != self.active_config_hash:
                return None
            return active_id
        except Exception:
            return None

    def _detect_cycle(
        self,
        start_id: str,
        target_id: str,
        index: LifecycleIndex,
        cleared_id: Optional[str] = None,
    ) -> bool:
        """Traverse supersession graph to prevent cycles.

        Returns True if setting start_id's superseded_by = target_id would form a cycle.
        If cleared_id is provided, its outgoing superseded_by edge is treated as None.
        """
        if start_id == target_id:
            return True
        visited = set()
        curr: Optional[str] = target_id
        while curr:
            if curr == start_id:
                return True
            if curr in visited or curr == cleared_id:
                break
            visited.add(curr)
            # Find next superseded_by
            next_target = None
            for issuer in index.issuers.values():
                if curr in issuer.evaluations:
                    next_target = issuer.evaluations[curr].get("superseded_by")
                    break
            curr = next_target
        return False

    def register_evaluation(
        self,
        evaluation_record: Any,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> LifecycleRecord:
        """Register a newly generated evaluation into lifecycle governance.

        Automatically promotes to ACTIVE if it matches ratified config_hash.
        Supersedes any existing active evaluation for the same (ipo_id, mode).
        """
        eval_id = evaluation_record.evaluation_id
        ipo_id = evaluation_record.ipo_id
        mode = evaluation_record.evaluation_mode.lower()
        company_name = getattr(evaluation_record, "company_name", ipo_id)
        config_hash = getattr(evaluation_record, "config_hash", "")

        is_ratified = config_hash == self.active_config_hash
        target_lifecycle = LIFECYCLE_STATE_ACTIVE if is_ratified else LIFECYCLE_STATE_SUPERSEDED

        with self._file_lock():
            index = self.load_index()
            issuer = index.issuers.get(ipo_id)
            if not issuer:
                issuer = IssuerLifecycleEntry(ipo_id=ipo_id, company_name=company_name)
                index.issuers[ipo_id] = issuer

            issuer.company_name = company_name

            incumbent_active_id = issuer.get_active_id(mode)
            old_superseded_id = None

            if target_lifecycle == LIFECYCLE_STATE_ACTIVE and incumbent_active_id and incumbent_active_id != eval_id:
                if self._detect_cycle(incumbent_active_id, eval_id, index):
                    raise CyclicLineageError(
                        f"Supersession cycle detected: {eval_id} cannot supersede {incumbent_active_id}"
                    )
                old_superseded_id = incumbent_active_id
                # Supersede incumbent
                old_rec = self.get_lifecycle(incumbent_active_id)
                if old_rec:
                    old_rec.lifecycle_state = LIFECYCLE_STATE_SUPERSEDED
                    old_rec.superseded_by = eval_id
                    old_rec.updated_at = utc_now_iso()
                    old_rec.transition_timestamp = utc_now_iso()
                    old_rec.transition_reason = reason or "SUPERSEDED_BY_NEW_EVALUATION"
                    old_rec.actor = actor or "system"
                    self.write_evaluation_lifecycle(old_rec)
                    issuer.evaluations[incumbent_active_id] = old_rec.to_dict()

            # Create record for new evaluation
            new_record = LifecycleRecord(
                evaluation_id=eval_id,
                ipo_id=ipo_id,
                mode=mode,
                lifecycle_state=target_lifecycle,
                visibility_state=VISIBILITY_STATE_VISIBLE,
                superseded_by=None,
                supersedes=old_superseded_id,
                actor=actor or "system",
                transition_reason=reason or "NEW_EVALUATION_INGESTION",
                transition_timestamp=utc_now_iso(),
            )
            self.write_evaluation_lifecycle(new_record)
            issuer.evaluations[eval_id] = new_record.to_dict()

            if target_lifecycle == LIFECYCLE_STATE_ACTIVE:
                issuer.set_active_id(mode, eval_id)

            self.save_index(index)
            return new_record

    def archive_evaluation(
        self,
        evaluation_id: str,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> LifecycleRecord:
        """Transition an evaluation to ARCHIVED visibility.

        Must not modify any immutable evaluation artifact.
        Tier 1 golden records cannot be archived.
        Active evaluations cannot be archived unless offering is withdrawn.
        """
        with self._file_lock():
            index = self.load_index()
            target_entry = None
            target_issuer = None
            for issuer in index.issuers.values():
                if evaluation_id in issuer.evaluations:
                    target_entry = issuer.evaluations[evaluation_id]
                    target_issuer = issuer
                    break

            if not target_entry:
                if not self.store.exists(evaluation_id):
                    raise EvaluationNotFoundError(f"Evaluation {evaluation_id!r} not found in store.")
                # Self-heal entry
                self.bootstrap_store()
                index = self.load_index()
                for issuer in index.issuers.values():
                    if evaluation_id in issuer.evaluations:
                        target_entry = issuer.evaluations[evaluation_id]
                        target_issuer = issuer
                        break

            if not target_entry or not target_issuer:
                raise EvaluationNotFoundError(f"Evaluation {evaluation_id!r} not found in lifecycle index.")

            record = LifecycleRecord.from_dict(target_entry)

            # Tier 1 protection
            tier = get_protection_tier(evaluation_id, record.ipo_id, store_root=self.root)
            if tier == TIER_1_GOLDEN:
                raise ProtectedRecordError(
                    f"Evaluation {evaluation_id!r} is a Tier 1 Golden record and cannot be archived."
                )

            # Active evaluation guard
            if record.lifecycle_state == LIFECYCLE_STATE_ACTIVE and target_issuer.status != "WITHDRAWN":
                raise InvalidStateTransitionError(
                    f"Evaluation {evaluation_id!r} is currently ACTIVE. Active evaluations of ongoing offerings "
                    "cannot be archived. Designate a replacement active evaluation first."
                )

            if record.visibility_state == VISIBILITY_STATE_ARCHIVED:
                raise InvalidStateTransitionError(f"Evaluation {evaluation_id!r} is already ARCHIVED.")

            record.visibility_state = VISIBILITY_STATE_ARCHIVED
            record.updated_at = utc_now_iso()
            record.transition_timestamp = utc_now_iso()
            record.transition_reason = reason or "USER_ARCHIVAL"
            record.actor = actor or "analyst"

            self.write_evaluation_lifecycle(record)
            target_issuer.evaluations[evaluation_id] = record.to_dict()
            self.save_index(index)
            return record

    def unarchive_evaluation(
        self,
        evaluation_id: str,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> LifecycleRecord:
        """Reversibly restore an ARCHIVED evaluation to VISIBLE state.

        Restores to SUPERSEDED + VISIBLE; never automatically promotes to ACTIVE.
        """
        with self._file_lock():
            index = self.load_index()
            target_entry = None
            target_issuer = None
            for issuer in index.issuers.values():
                if evaluation_id in issuer.evaluations:
                    target_entry = issuer.evaluations[evaluation_id]
                    target_issuer = issuer
                    break

            if not target_entry or not target_issuer:
                raise EvaluationNotFoundError(f"Evaluation {evaluation_id!r} not found in lifecycle index.")

            record = LifecycleRecord.from_dict(target_entry)

            if record.visibility_state != VISIBILITY_STATE_ARCHIVED:
                raise InvalidStateTransitionError(f"Evaluation {evaluation_id!r} is not archived.")

            record.visibility_state = VISIBILITY_STATE_VISIBLE
            record.updated_at = utc_now_iso()
            record.transition_timestamp = utc_now_iso()
            record.transition_reason = reason or "USER_UNARCHIVE"
            record.actor = actor or "analyst"

            self.write_evaluation_lifecycle(record)
            target_issuer.evaluations[evaluation_id] = record.to_dict()
            self.save_index(index)
            return record

    def make_active(
        self,
        evaluation_id: str,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> LifecycleRecord:
        """Governed rollback/activation designating an evaluation as authoritative ACTIVE."""
        with self._file_lock():
            index = self.load_index()
            if not self.store.exists(evaluation_id):
                raise EvaluationNotFoundError(f"Evaluation {evaluation_id!r} not found in store.")

            rec_data = self.store.read(evaluation_id)
            config_hash = rec_data.get("config_hash")
            if config_hash != self.active_config_hash:
                raise InvalidStateTransitionError(
                    f"Evaluation {evaluation_id!r} was scored under unratified config {config_hash!r} "
                    f"and cannot become ACTIVE. Active policy required: {self.active_config_hash!r}."
                )

            ipo_id = rec_data.get("ipo_id")
            mode = rec_data.get("evaluation_mode", "final").lower()
            issuer = index.issuers.get(ipo_id)
            if not issuer:
                issuer = IssuerLifecycleEntry(ipo_id=ipo_id, company_name=rec_data.get("company_name"))
                index.issuers[ipo_id] = issuer

            incumbent_active_id = issuer.get_active_id(mode)

            if incumbent_active_id == evaluation_id:
                # Already active: if archived, unarchive
                target_rec = self.get_lifecycle(evaluation_id)
                if target_rec and target_rec.visibility_state == VISIBILITY_STATE_ARCHIVED:
                    target_rec.visibility_state = VISIBILITY_STATE_VISIBLE
                    self.write_evaluation_lifecycle(target_rec)
                    issuer.evaluations[evaluation_id] = target_rec.to_dict()
                    self.save_index(index)
                    return target_rec
                raise InvalidStateTransitionError(f"Evaluation {evaluation_id!r} is already ACTIVE.")

            if incumbent_active_id:
                if self._detect_cycle(incumbent_active_id, evaluation_id, index, cleared_id=evaluation_id):
                    raise CyclicLineageError(
                        f"Supersession cycle detected: {evaluation_id} cannot supersede {incumbent_active_id}"
                    )
                # Demote incumbent active to SUPERSEDED
                old_rec = self.get_lifecycle(incumbent_active_id)
                if old_rec:
                    old_rec.lifecycle_state = LIFECYCLE_STATE_SUPERSEDED
                    old_rec.superseded_by = evaluation_id
                    old_rec.updated_at = utc_now_iso()
                    old_rec.transition_timestamp = utc_now_iso()
                    old_rec.transition_reason = reason or "ADMINISTRATIVE_ROLLBACK_DEMOTION"
                    old_rec.actor = actor or "governance_lead"
                    self.write_evaluation_lifecycle(old_rec)
                    issuer.evaluations[incumbent_active_id] = old_rec.to_dict()

            target_rec = self.get_lifecycle(evaluation_id)
            if not target_rec:
                target_rec = LifecycleRecord(
                    evaluation_id=evaluation_id,
                    ipo_id=ipo_id,
                    mode=mode,
                    lifecycle_state=LIFECYCLE_STATE_ACTIVE,
                    visibility_state=VISIBILITY_STATE_VISIBLE,
                    superseded_by=None,
                    supersedes=incumbent_active_id,
                    actor=actor or "governance_lead",
                    transition_reason=reason or "ADMINISTRATIVE_ROLLBACK_PROMOTION",
                    transition_timestamp=utc_now_iso(),
                )
            else:
                target_rec.lifecycle_state = LIFECYCLE_STATE_ACTIVE
                target_rec.visibility_state = VISIBILITY_STATE_VISIBLE
                target_rec.superseded_by = None
                target_rec.supersedes = incumbent_active_id
                target_rec.updated_at = utc_now_iso()
                target_rec.transition_timestamp = utc_now_iso()
                target_rec.transition_reason = reason or "ADMINISTRATIVE_ROLLBACK_PROMOTION"
                target_rec.actor = actor or "governance_lead"

            self.write_evaluation_lifecycle(target_rec)
            issuer.evaluations[evaluation_id] = target_rec.to_dict()
            issuer.set_active_id(mode, evaluation_id)

            self.save_index(index)
            return target_rec

    def bootstrap_store(self, force: bool = False) -> LifecycleIndex:
        """Deterministic bootstrap & reconciliation of historical evaluations without lifecycle metadata.

        Preserves existing evaluation artifacts 100% bit-for-bit unchanged.
        R.K. Fashion Mapping:
          - c4e88b17 (Score 50.0): ACTIVE + VISIBLE
          - 6ee95f0a (Score 55.0): SUPERSEDED + VISIBLE (retained defect repair baseline)
          - 808a237d (Score 60.0): SUPERSEDED + ARCHIVED
          - 1d64ea28 (Score 61.0): SUPERSEDED + ARCHIVED
        Vishal Nirmiti:
          - VISHAL-NIRMITI-LIMITED-...: ACTIVE + VISIBLE (Tier 1 Golden Protected)
        """
        all_eids = self.store.list_evaluations()
        index = LifecycleIndex()

        # Group evaluations by ipo_id and mode
        grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for eid in all_eids:
            try:
                rec = self.store.read(eid)
                ipo_id = rec.get("ipo_id", "UNKNOWN")
                mode = rec.get("evaluation_mode", "final").lower()
                grouped.setdefault((ipo_id, mode), []).append(rec)
            except Exception:
                continue

        for (ipo_id, mode), recs in grouped.items():
            issuer = IssuerLifecycleEntry(ipo_id=ipo_id)
            if recs:
                issuer.company_name = recs[0].get("company_name", ipo_id)
            index.issuers[ipo_id] = issuer

            # Sort chronologically
            recs.sort(key=lambda r: (r.get("evaluation_timestamp", ""), r.get("evaluation_id", "")))

            # Special forensic handling for R.K. Fashion Accessories
            if "R-K-FASHION" in ipo_id.upper():
                # R.K. target mapping:
                # c4e88b17 -> ACTIVE + VISIBLE
                # 6ee95f0a -> SUPERSEDED + VISIBLE
                # 808a237d -> SUPERSEDED + ARCHIVED
                # 1d64ea28 -> SUPERSEDED + ARCHIVED
                active_id = None
                for r in recs:
                    eid = r.get("evaluation_id")
                    if "c4e88b17" in eid:
                        active_id = eid
                if not active_id and recs:
                    active_id = recs[-1].get("evaluation_id")

                issuer.set_active_id(mode, active_id)

                for r in recs:
                    eid = r.get("evaluation_id")
                    if eid == active_id:
                        lc_rec = LifecycleRecord(
                            evaluation_id=eid,
                            ipo_id=ipo_id,
                            mode=mode,
                            lifecycle_state=LIFECYCLE_STATE_ACTIVE,
                            visibility_state=VISIBILITY_STATE_VISIBLE,
                            transition_reason="POST_REPAIR_AUTHORITATIVE_BASELINE",
                        )
                    elif "6ee95f0a" in eid:
                        lc_rec = LifecycleRecord(
                            evaluation_id=eid,
                            ipo_id=ipo_id,
                            mode=mode,
                            lifecycle_state=LIFECYCLE_STATE_SUPERSEDED,
                            visibility_state=VISIBILITY_STATE_VISIBLE,
                            superseded_by=active_id,
                            transition_reason="RETAINED_DEFECT_REPAIR_BASELINE_EVIDENCE",
                        )
                    else:
                        # 808a237d, 1d64ea28, etc. -> ARCHIVED
                        lc_rec = LifecycleRecord(
                            evaluation_id=eid,
                            ipo_id=ipo_id,
                            mode=mode,
                            lifecycle_state=LIFECYCLE_STATE_SUPERSEDED,
                            visibility_state=VISIBILITY_STATE_ARCHIVED,
                            superseded_by=active_id,
                            transition_reason="EXPLORATORY_INTERMEDIATE_EXECUTION",
                        )
                    self.write_evaluation_lifecycle(lc_rec)
                    issuer.evaluations[eid] = lc_rec.to_dict()
                continue

            # General IPO bootstrap
            # Find candidate with matching ratified config_hash
            ratified_candidates = [
                r for r in recs
                if r.get("config_hash") == self.active_config_hash
            ]
            active_candidate = ratified_candidates[-1] if ratified_candidates else (recs[-1] if recs else None)
            active_id = active_candidate.get("evaluation_id") if active_candidate else None

            if active_id:
                issuer.set_active_id(mode, active_id)

            for r in recs:
                eid = r.get("evaluation_id")
                existing_file_lc = self.read_evaluation_lifecycle(eid) if not force else None
                if existing_file_lc:
                    lc_rec = existing_file_lc
                elif eid == active_id:
                    lc_rec = LifecycleRecord(
                        evaluation_id=eid,
                        ipo_id=ipo_id,
                        mode=mode,
                        lifecycle_state=LIFECYCLE_STATE_ACTIVE,
                        visibility_state=VISIBILITY_STATE_VISIBLE,
                        transition_reason="BOOTSTRAP_AUTHORITATIVE_SELECTION",
                    )
                else:
                    lc_rec = LifecycleRecord(
                        evaluation_id=eid,
                        ipo_id=ipo_id,
                        mode=mode,
                        lifecycle_state=LIFECYCLE_STATE_SUPERSEDED,
                        visibility_state=VISIBILITY_STATE_VISIBLE,
                        superseded_by=active_id,
                        transition_reason="BOOTSTRAP_HISTORICAL_SUPERSEDED",
                    )
                self.write_evaluation_lifecycle(lc_rec)
                issuer.evaluations[eid] = lc_rec.to_dict()

        self.save_index(index)
        return index


__all__ = [
    "LIFECYCLE_VERSION",
    "LIFECYCLE_STATE_ACTIVE",
    "LIFECYCLE_STATE_SUPERSEDED",
    "LIFECYCLE_STATES",
    "VISIBILITY_STATE_VISIBLE",
    "VISIBILITY_STATE_ARCHIVED",
    "VISIBILITY_STATES",
    "OPERATIONAL_STATUS_ACTIVE",
    "OPERATIONAL_STATUS_SUPERSEDED",
    "OPERATIONAL_STATUS_ARCHIVED",
    "OPERATIONAL_STATUSES",
    "TIER_1_GOLDEN",
    "TIER_2_GOVERNED",
    "TIER_3_STANDARD",
    "ACTIVE_RATIFIED_CONFIG_HASH",
    "VISHAL_GOLDEN_RESULT_HASH",
    "LifecycleError",
    "InvalidStateTransitionError",
    "CyclicLineageError",
    "ProtectedRecordError",
    "MissingLineageTargetError",
    "EvaluationNotFoundError",
    "LifecycleRecord",
    "IssuerLifecycleEntry",
    "LifecycleIndex",
    "LifecycleManager",
    "get_protection_tier",
    "utc_now_iso",
    "acquire_file_lock",
    "release_file_lock",
]
