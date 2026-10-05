"""The command-line runner.

The CLI is the operational surface for the engine, so its exit codes and its
refusals are part of the contract: a refused run must exit non-zero and say
what was wrong, and the audit commands must fail loudly on a mismatch.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ENGINE_ROOT, GOLDEN_DIR, REPO_ROOT

CLI = ENGINE_ROOT / "tools" / "ipo_screen.py"


def cli(*args: str, expect: int = 0) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=180,
    )
    assert completed.returncode == expect, (
        f"exit {completed.returncode} (wanted {expect})\n"
        f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
    )
    return completed


def test_cli_help_lists_every_command():
    out = cli("--help").stdout
    for command in ("run", "replay", "verify", "project", "check-config"):
        assert command in out


def test_check_config_passes_on_the_shipped_configuration():
    out = cli("check-config").stdout
    assert "valid              True" in out
    assert "profiles resolved  10" in out
    assert "100 points" in out


def test_check_config_refuses_a_broken_configuration(tmp_path):
    from conftest import CONFIG_PATH

    broken = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    broken["modules"][0]["max"] = 30
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(broken), encoding="utf-8")

    result = cli("--config", str(path), "check-config", expect=1)
    assert "valid              False" in result.stdout
    assert "CONFIG_MODULE_MAX_MISMATCH" in result.stdout or "CONFIG_TOTAL_MISMATCH" in result.stdout


def test_run_prints_the_report_and_exits_zero(tmp_path):
    store = tmp_path / "evaluations"
    out = cli(
        "run", str(GOLDEN_DIR / "input.json"),
        "--at", "2026-10-05T12:00:00Z",
        "--store", str(store),
    ).stdout
    assert "Vishal Nirmiti Limited" in out
    assert "INSUFFICIENT_DATA" in out
    assert "35.0" in out
    assert store.exists()


def test_run_persists_a_verifiable_record(tmp_path):
    store = tmp_path / "evaluations"
    cli("run", str(GOLDEN_DIR / "input.json"),
        "--at", "2026-10-05T12:00:00Z", "--store", str(store))
    out = cli("verify", "--store", str(store)).stdout
    assert "OK " in out
    assert "0 mismatch(es)" in out


def test_run_replays_to_the_same_hash(tmp_path):
    store = tmp_path / "evaluations"
    run_out = cli("run", str(GOLDEN_DIR / "input.json"),
                  "--at", "2026-10-05T12:00:00Z", "--store", str(store)).stdout
    identifier = next(
        line.split()[-1] for line in run_out.splitlines()
        if line.strip().startswith("VISHAL-NIRMITI-LIMITED-") and "Z-" in line
    )
    out = cli("replay", identifier, "--store", str(store)).stdout
    assert "match             True" in out


def test_run_warns_that_no_instant_was_pinned(tmp_path):
    result = cli("run", str(GOLDEN_DIR / "input.json"), "--store", str(tmp_path / "e"))
    assert "no --at supplied" in result.stderr


def test_run_refuses_an_invalid_input(tmp_path):
    document = json.loads((GOLDEN_DIR / "input.json").read_text(encoding="utf-8"))
    document["issue"]["fresh_shares"] = "6590909"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    result = cli("run", str(path), "--at", "2026-10-05T12:00:00Z", expect=1)
    assert "schema validation failed" in result.stderr


def test_run_refuses_an_unknown_mode(tmp_path):
    result = cli(
        "run", str(GOLDEN_DIR / "input.json"), "--mode", "quarterly_review",
        expect=2,
    )
    assert "invalid choice" in result.stderr


def test_run_rejects_a_bad_timestamp(tmp_path):
    result = cli(
        "run", str(GOLDEN_DIR / "input.json"), "--at", "yesterday", expect=1,
    )
    assert "ISO 8601" in result.stderr


def test_project_rebuilds_every_sheet(tmp_path):
    store = tmp_path / "evaluations"
    cli("run", str(GOLDEN_DIR / "input.json"),
        "--at", "2026-10-05T12:00:00Z", "--store", str(store))
    workbook = tmp_path / "IPO_Screening_History.xlsx"
    out = cli("project", "--store", str(store), "--workbook", str(workbook)).stdout
    assert workbook.exists()
    assert "Evidence               16" in out
    assert "Knockouts              6" in out


def test_verify_detects_a_tampered_artifact(tmp_path):
    store = tmp_path / "evaluations"
    cli("run", str(GOLDEN_DIR / "input.json"),
        "--at", "2026-10-05T12:00:00Z", "--store", str(store))
    directory = next(p for p in store.iterdir() if p.is_dir())
    result_path = directory / "result.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["score"]["final_score"] = 99.0
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    result = cli("verify", "--store", str(store), expect=3)
    assert "FAIL" in result.stdout
    assert "result.json" in result.stdout


def test_verify_on_an_empty_store_is_not_an_error(tmp_path):
    out = cli("verify", "--store", str(tmp_path / "nothing")).stdout
    assert "no evaluations found" in out


def test_cli_is_importable_and_has_a_stable_main():
    """Guard the module entry point used by the operator runbook."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("ipo_screen_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert callable(module.main)
    assert module.EXIT_REFUSED == 1
    assert module.EXIT_AUDIT_MISMATCH == 3
