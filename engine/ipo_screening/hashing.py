"""Canonical serialisation and deterministic hashing.

Determinism (spec s3.1) and reproducibility (spec s19 acceptance test) both
depend on a byte-exact canonical form. Every hash in the engine is produced
from :func:`canonical_json` so that logically equal payloads always hash
equally, regardless of dict insertion order, float formatting or unicode
normalisation.
"""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from typing import Any

#: Any change to this string invalidates all previously produced hashes and
#: must be treated as an engine-version change.
CANONICAL_GRAMMAR_VERSION = "1.5.0"


def _normalise(obj: Any) -> Any:
    """Recursively normalise a payload into a canonical, hashable structure."""
    if obj is None or isinstance(obj, bool):
        return obj
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, int):
        # Bools are handled above; a real int stays an int.
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(f"non-finite float is not canonicalisable: {obj!r}")
        # repr() of a float round-trips exactly in Python 3 and gives a stable
        # shortest representation, so 1.0 and 1.00 canonicalise identically.
        return {"__float__": repr(obj)}
    if isinstance(obj, dict):
        return {
            str(_normalise(k)): _normalise(v)
            for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))
        }
    if isinstance(obj, (list, tuple)):
        return [_normalise(v) for v in obj]
    if hasattr(obj, "to_dict"):
        return _normalise(obj.to_dict())
    raise TypeError(f"cannot canonicalise object of type {type(obj).__name__}")


def canonical_json(obj: Any) -> str:
    """Return the canonical JSON text for *obj*.

    Deterministic across runs and machines: sorted keys, no insignificant
    whitespace, NFC-normalised strings, exact float representation.
    """
    return json.dumps(
        _normalise(obj),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def sha256_of(obj: Any) -> str:
    """SHA-256 (hex) of the canonical JSON form of *obj*."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def hash_bytes(data: bytes) -> str:
    """SHA-256 (hex) of raw bytes (used for source document content hashes)."""
    return hashlib.sha256(data).hexdigest()


def short_hash(full: str, length: int = 8) -> str:
    return full[:length]


def evaluate_id(ipo_id: str, timestamp: str, mode: str, result_hash: str) -> str:
    """Build the recommended v1.5 evaluation identifier.

    Tech design s11: ``IPOID-YYYYMMDD-HHMMSS-MODE-<short-hash>``.
    """
    compact = timestamp.replace("-", "").replace(":", "").replace("T", "-")
    # timestamp is ISO-8601 like 2026-10-05T14:03:11Z -> 20261005-140311
    parts = compact.split("-")
    date = parts[0] if parts else "00000000"
    time = parts[1] if len(parts) > 1 else "000000"
    safe_ipo = "".join(c if c.isalnum() or c in "-_" else "-" for c in ipo_id).strip("-")
    return f"{safe_ipo}-{date}-{time}-{mode}-{short_hash(result_hash)}"


__all__ = [
    "CANONICAL_GRAMMAR_VERSION",
    "canonical_json",
    "sha256_of",
    "hash_bytes",
    "short_hash",
    "evaluate_id",
]
