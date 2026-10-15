"""Strict JSON parsing for evaluation inputs and GMP evidence manifests.

Python's ``json`` module keeps the *last* of several equal object keys without
any error. An input such as ``{"pct": 71.4, "pct": 9.9}`` would then be
evaluated as ``9.9`` while a reviewer reads ``71.4``, and an evidence reference
could silently point at a different line, hash or window. RFC 8259 section 4
says such names SHOULD be unique and that behaviour is otherwise unpredictable.

:func:`loads_strict` rejects every object that repeats a member name, at any
depth, before any downstream validation sees a collapsed value. It is used only
at the evaluation-input boundaries and in the GMP manifest parser; it does not
change how other stored or generated JSON is read.
"""

from __future__ import annotations

import json
from typing import Any, List, Tuple, Union


class DuplicateJSONKeyError(ValueError):
    """An object in a JSON document repeats a member name."""


def _reject_duplicates(pairs: List[Tuple[str, Any]]) -> dict:
    seen: dict = {}
    for name, value in pairs:
        if name in seen:
            raise DuplicateJSONKeyError(f"duplicate JSON key {name!r}")
        seen[name] = value
    return seen


def loads_strict(data: Union[str, bytes]) -> Any:
    """Parse JSON text or UTF-8 bytes, rejecting duplicate keys at every depth."""
    if isinstance(data, (bytes, bytearray)):
        data = bytes(data).decode("utf-8")
    return json.loads(data, object_pairs_hook=_reject_duplicates)


def load_strict(handle: Any) -> Any:
    """Read and parse a JSON file object with duplicate-key rejection."""
    return loads_strict(handle.read())


__all__ = ["DuplicateJSONKeyError", "load_strict", "loads_strict"]
