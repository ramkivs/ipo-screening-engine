"""Small JSON helpers for evaluation-input boundaries that require unique keys.

Python's default JSON decoder silently keeps the last value for duplicate object
keys.  That is unsafe for evaluation inputs and retained GMP manifests because
it can erase contradictory values before schema or integrity checks see them.

This module is intentionally opt-in: config, stored-record, lifecycle, and
post-listing JSON readers keep their existing parsing behavior unless a separate
contract requires strict parsing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, TextIO


class DuplicateJSONKeyError(ValueError):
    """A JSON object contains the same member name more than once."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"duplicate JSON object key {key!r}")


def _unique_object(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKeyError(key)
        result[key] = value
    return result


def loads_strict_json(text: str) -> Any:
    """Parse JSON while rejecting duplicate keys in every nested object."""
    return json.loads(text, object_pairs_hook=_unique_object)


def load_strict_json(source: str | Path | TextIO) -> Any:
    """Parse an evaluation-input JSON file or open text stream strictly."""
    if hasattr(source, "read"):
        return json.load(source, object_pairs_hook=_unique_object)
    with Path(source).open("r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=_unique_object)


__all__ = ["DuplicateJSONKeyError", "load_strict_json", "loads_strict_json"]
