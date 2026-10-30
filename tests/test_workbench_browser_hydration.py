"""Browser-level regression for Workbench initial evaluation hydration."""
from __future__ import annotations

import copy
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ipo_screening.evaluation import EvaluationStore
from ipo_screening.pipeline import evaluate

ROOT = Path(__file__).resolve().parents[1]
BROWSER_CHECK = ROOT / "frontend/test/workbench-hydration.browser.mjs"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(port: int, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"Workbench exited during startup:\n{process.stdout.read()}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=.1):
                return
        except OSError:
            time.sleep(.05)
    raise AssertionError("Workbench did not start within 15 seconds")


@pytest.mark.parametrize("workbench_path", ["/workbench", "/workbench/"])
def test_workbench_starts_blank_then_hydrates_explicit_selection(tmp_path, golden_input, config, workbench_path):
    document = copy.deepcopy(golden_input)
    document["financials"].update({
        "operating_cash_flow_3yr_cumulative": 100,
        "net_income_3yr_cumulative": 300,
        "trade_receivables_days": 100,
        "net_working_capital_pct_revenue": 40,
        "top_customer_revenue_pct": 55,
        "loss_making_segments_present": True,
    })
    document["governance"].update({
        "promoter_pledged_shares_pct": 30,
        "pre_issue_promoter_holding_pct": 50,
    })
    document["risks"] = {
        "contingent_liabilities_pct_net_worth": 50,
        "material_regulatory_disputes_present": True,
    }
    document["market"] = {"subscription": {
        "qib_x": 25, "nii_x": 12, "retail_x": 8, "overall_x": 15,
        "as_of": "2026-10-05T11:00:00Z", "source_id": "BROWSER-E2E",
    }}
    store = EvaluationStore(tmp_path / "build/evaluations")
    outcome = evaluate(
        document, config, mode="final",
        evaluation_datetime=datetime(2026, 10, 5, 12, tzinfo=timezone.utc),
        store=store,
    )
    evaluation_id = outcome.record.evaluation_id
    port = _free_port()
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "engine"),
        "IPO_EVALUATION_STORE": str(store.root),
        "IPO_WORKBENCH_ROOT": str(tmp_path / "build/workbench"),
        "PORT": str(port),
    }
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "engine/tools/ui_dashboard.py")],
        cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_server(port, process)
        browser = subprocess.run(
            ["node", str(BROWSER_CHECK), f"http://127.0.0.1:{port}{workbench_path}", evaluation_id],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        assert browser.returncode == 0, f"Browser hydration failed:\n{browser.stdout}\n{browser.stderr}"
        report = json.loads(browser.stdout.strip().splitlines()[-1])
        assert report["controls"] == 27
        assert report["hydrated"] == 21
        assert report["requests"][:3] == [
            "/api/v1/evaluations",
            f"/api/v1/evaluations/{evaluation_id}/input",
            f"/api/v1/comparison/{evaluation_id}",
        ]
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
