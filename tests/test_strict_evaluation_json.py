"""Strict duplicate-key parsing at evaluation-input JSON boundaries."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ipo_screening.json_strict import DuplicateJSONKeyError, load_strict_json, loads_strict_json
from ipo_screening.pipeline import evaluate_file

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "engine" / "tools" / "ipo_screen.py"


def _cli_module():
    name = "ipo_screen_strict_json_test_cli"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, CLI_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _duplicate_object_member(text: str, *, object_start: str, member: str, duplicate: str) -> str:
    start = text.index(object_start)
    key = json.dumps(member, ensure_ascii=False) + ":"
    position = text.index(key, start)
    line_start = text.rfind("\n", 0, position) + 1
    line_end = text.find("\n", position)
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end]
    indent = line[: len(line) - len(line.lstrip())]
    duplicate_line = indent + json.dumps(member) + ": " + duplicate + ","
    # Insert before the original member so the duplicate line is always followed
    # by another property and does not create a trailing-comma parse error.
    replacement = duplicate_line + "\n" + line
    return text[:line_start] + replacement + text[line_end:]


def _duplicate_evaluation_inputs(golden_input: dict[str, Any]) -> dict[str, str]:
    inputs: dict[str, str] = {}

    top = json.dumps(golden_input, indent=2, ensure_ascii=False)
    old_ipo_id = json.dumps(golden_input["ipo_id"], ensure_ascii=False)
    needle = f'"ipo_id": {old_ipo_id},'
    assert needle in top
    inputs["top-level"] = top.replace(
        needle,
        needle + '\n  "ipo_id": "CONTRADICTORY-IPO-ID",',
        1,
    )

    gmp_doc = copy.deepcopy(golden_input)
    gmp_doc["market"]["gmp"]["pct"] = 15.91
    gmp = json.dumps(gmp_doc, indent=2, ensure_ascii=False)
    inputs["market.gmp"] = _duplicate_object_member(
        gmp,
        object_start='"gmp": {',
        member="pct",
        duplicate="999.0",
    )

    source_doc = copy.deepcopy(golden_input)
    source_doc["_sources"] = [{"source_id": "DUP-SOURCE", "source_type": "MARKET_DATA"}]
    sources = json.dumps(source_doc, indent=2, ensure_ascii=False)
    inputs["_sources entry"] = _duplicate_object_member(
        sources,
        object_start='"_sources": [',
        member="source_id",
        duplicate='"CONTRADICTORY-SOURCE-ID"',
    )

    evidence_doc = copy.deepcopy(golden_input)
    evidence_doc["_evidence"] = {
        "market.gmp.pct": {
            "evidence_id": "EV-market.gmp.pct",
            "source_id": "DUP-SOURCE",
            "locator": "line 7",
            "quote": "+15.91%",
        }
    }
    evidence = json.dumps(evidence_doc, indent=2, ensure_ascii=False)
    inputs["_evidence entry"] = _duplicate_object_member(
        evidence,
        object_start='"_evidence": {',
        member="quote",
        duplicate='"+1.0%"',
    )
    return inputs


@pytest.mark.parametrize("case", ["top-level", "market.gmp", "_sources entry", "_evidence entry"])
def test_strict_parser_rejects_duplicate_keys_at_every_input_depth(golden_input, case):
    raw = _duplicate_evaluation_inputs(golden_input)[case]
    with pytest.raises(DuplicateJSONKeyError):
        loads_strict_json(raw)


@pytest.mark.parametrize("case", ["top-level", "market.gmp", "_sources entry", "_evidence entry"])
def test_evaluate_file_rejects_duplicate_keys_before_schema_or_scoring(
    tmp_path, golden_input, case
):
    source = tmp_path / "duplicate-input.json"
    source.write_text(_duplicate_evaluation_inputs(golden_input)[case], encoding="utf-8")
    with pytest.raises(DuplicateJSONKeyError):
        evaluate_file(source, evaluation_datetime=None)


def test_strict_file_loader_and_cli_run_and_assemble_boundaries(tmp_path, golden_input):
    duplicate = _duplicate_evaluation_inputs(golden_input)["top-level"]
    source = tmp_path / "duplicate-input.json"
    source.write_text(duplicate, encoding="utf-8")
    with pytest.raises(DuplicateJSONKeyError):
        load_strict_json(source)

    cli = _cli_module()
    with pytest.raises(DuplicateJSONKeyError):
        cli.cmd_run(SimpleNamespace(input=str(source)))
    with pytest.raises(DuplicateJSONKeyError):
        cli.cmd_assemble(SimpleNamespace(input=str(source)))


def test_json_enrichment_and_price_notice_inputs_reject_duplicate_keys(tmp_path):
    cli = _cli_module()
    duplicate = '{"gmp":{"pct":71.4,"pct":0}}'
    enrichment_path = tmp_path / "market.json"
    enrichment_path.write_text(duplicate, encoding="utf-8")
    with pytest.raises(DuplicateJSONKeyError):
        cli.load_json_or_file(str(enrichment_path))
    with pytest.raises(DuplicateJSONKeyError):
        cli.load_json_or_file(duplicate)

    notice_path = tmp_path / "notice.json"
    notice_path.write_text(
        '{"price_band_high":700,"price_band_high":710}',
        encoding="utf-8",
    )
    with pytest.raises(DuplicateJSONKeyError):
        cli.load_notice(str(notice_path))
    with pytest.raises(DuplicateJSONKeyError):
        cli.load_notice('{"price_band_high":700,"price_band_high":710}')


def test_strict_reader_is_scoped_and_does_not_change_permissive_json_api():
    # `json.loads` remains the standard parser outside the explicitly strict
    # evaluation-input/manifest paths.
    assert json.loads('{"value":1,"value":2}') == {"value": 2}
    with pytest.raises(DuplicateJSONKeyError):
        loads_strict_json('{"value":1,"value":2}')
