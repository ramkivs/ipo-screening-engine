"""Duplicate JSON keys are rejected at evaluation-input boundaries.

Covers the entry points that read a candidate evaluation input or a GMP
manifest. Stored records, config and post-listing or lifecycle reads are out of
scope and are not exercised here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from ipo_screening.pipeline import evaluate_file
from ipo_screening.schema_validation import validate_input_schema_path
from ipo_screening.strict_json import DuplicateJSONKeyError, loads_strict

sys.path.insert(0, str(REPO_ROOT / "engine" / "tools"))
import ipo_screen  # noqa: E402

VISHAL = REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json"


def _duplicated_input(tmp_path: Path) -> Path:
    text = VISHAL.read_text(encoding="utf-8")
    needle = '"board": "mainboard",'
    assert text.count(needle) == 1
    # A second, different value for the same member: last-wins would silently change it.
    mutated = text.replace(needle, needle + ' "board": "sme",', 1)
    path = tmp_path / "input.json"
    path.write_text(mutated, encoding="utf-8")
    return path


def test_the_retained_vishal_input_is_unaffected():
    document = loads_strict(VISHAL.read_bytes())
    assert document["board"] == "mainboard"


def test_loads_strict_rejects_duplicates_at_any_depth():
    with pytest.raises(DuplicateJSONKeyError, match="'pct'"):
        loads_strict('{"market": {"gmp": {"pct": 71.4, "pct": 9.9}}}')
    with pytest.raises(DuplicateJSONKeyError):
        loads_strict('[{"k": 1}, {"k": 1, "k": 2}]')


def test_loads_strict_keeps_equal_keys_in_different_objects():
    assert loads_strict('{"a": {"x": 1}, "b": {"x": 2}}') == {"a": {"x": 1}, "b": {"x": 2}}


def test_evaluate_file_rejects_duplicate_key_input(tmp_path):
    with pytest.raises(DuplicateJSONKeyError, match="'board'"):
        evaluate_file(_duplicated_input(tmp_path))


def test_schema_validation_rejects_duplicate_key_input(tmp_path):
    with pytest.raises(DuplicateJSONKeyError, match="'board'"):
        validate_input_schema_path(str(_duplicated_input(tmp_path)))


def test_cli_run_refuses_duplicate_key_input(tmp_path, capsys):
    code = ipo_screen.main(["run", str(_duplicated_input(tmp_path))])
    assert code == ipo_screen.EXIT_REFUSED
    assert "duplicate JSON key 'board'" in capsys.readouterr().err


def test_cli_assemble_refuses_duplicate_key_base_input(tmp_path, capsys):
    code = ipo_screen.main(["assemble", str(_duplicated_input(tmp_path))])
    assert code == ipo_screen.EXIT_REFUSED
    assert "duplicate JSON key" in capsys.readouterr().err


def test_load_json_or_file_refuses_duplicate_key_inline_json():
    with pytest.raises(DuplicateJSONKeyError):
        ipo_screen.load_json_or_file('{"pct": 1, "pct": 2}')
