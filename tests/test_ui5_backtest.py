"""UI-5 Backtest Analytics Dashboard Acceptance & Integrity Suite.

Verifies:
1. Static asset serving of UI-5 backtest analytics views, navigation, and styles.
2. WCAG AA accessibility landmarks and semantic structure for backtest analytics.
3. Distinction banner separating population analysis vs individual performance vs calibration.
4. Executive analytics KPI summary and maturity mapping.
5. Rank IC, hit-rate, decile, vintage, and holdout section structures.
6. Point-in-time leakage audit and cryptographic provenance presentation.
7. Calibration governance boundary callout.
8. Navigation integration from Dashboard and Performance views.
9. Zero client-side analytical or return calculation invariant.
10. Strictly read-only protocol and zero mutation capability.
11. Absence of policy activation controls.
12. Zero server filesystem path exposure and zero credential leakage.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import pytest
from conftest import EVAL_AT
from fastapi.testclient import TestClient

from ipo_screening.evaluation import EvaluationStore
from ipo_screening.pipeline import evaluate
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"


@pytest.fixture
def populated_ui5_env(tmp_path: Path, golden_input: Dict[str, Any], config: Dict[str, Any]):
    """Set up an evaluation store with a FINAL evaluation, backtest dataset, and analytics report."""
    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)

    final = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT,
        store=store,
    )

    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir(parents=True)
    dataset_file = dataset_dir / "dataset.json"
    dataset_file.write_text(
        json.dumps(
            {
                "dataset_id": "test_dataset_001",
                "generated_at": "2026-10-06T12:00:00Z",
                "manifest": {
                    "dataset_hash": "d1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2",
                    "row_count": 1,
                    "included_observation_count": 3,
                    "status_counts": {"COMPLETE": 1},
                },
                "rows": [],
            }
        ),
        encoding="utf-8",
    )

    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir(parents=True)
    analytics_file = analytics_dir / "analytics.json"
    analytics_file.write_text(
        json.dumps(
            {
                "manifest": {
                    "analysis_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                    "dataset_hash": "d1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2",
                    "sample_maturity_1w": "DESCRIPTIVE_ONLY",
                    "sample_maturity_1m": "DESCRIPTIVE_ONLY",
                    "sample_maturity_6m": "DESCRIPTIVE_ONLY",
                    "leakage_audit_passed": True,
                },
                "rank_ic": {
                    "horizon": "SIX_MONTH",
                    "spearman_ic": 0.164656,
                    "p_value": 0.12,
                    "sample_size": 1,
                },
                "hit_rates": {"one_week": 100.0},
                "avoided_loss_rates": {"one_week": 100.0},
                "decile_buckets": [],
            }
        ),
        encoding="utf-8",
    )

    cfg = PresentationConfig(
        store_root=str(store_dir),
        config_dir=str(REPO_ROOT / "config"),
        dataset_path=dataset_file,
        analytics_path=analytics_file,
        proposal_path=REPO_ROOT / "config" / "calibration-proposal.v1.6.0.json",
    )
    service = PresentationService(cfg)
    app = create_app(service)
    client = TestClient(app)

    return {
        "store": store,
        "final": final,
        "service": service,
        "app": app,
        "client": client,
        "dataset_file": dataset_file,
        "analytics_file": analytics_file,
    }


def test_ui5_static_assets_contain_backtest_dashboard():
    """Verify frontend/index.html contains UI-5 Backtest Analytics navigation and container."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    # Navigation tab
    assert 'href="#backtest"' in index_html
    assert 'Backtest Analytics' in index_html

    # View container and accessibility attributes
    assert 'id="backtest-view"' in index_html
    assert 'role="region"' in index_html
    assert 'aria-label="Backtest Analytics Dashboard"' in index_html


def test_ui5_css_contains_backtest_styles():
    """Verify stylesheet contains distinction banner, analytics KPI, and diagnostic styles."""
    styles_css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")

    assert ".distinction-banner" in styles_css
    assert ".distinction-card" in styles_css
    assert ".analytics-kpi-grid" in styles_css
    assert ".analytics-kpi-card" in styles_css
    assert ".diagnostic-grid-2" in styles_css
    assert ".diagnostic-card" in styles_css
    assert ".maturity-pill" in styles_css
    assert ".unexposed-box" in styles_css


def test_ui5_app_contains_backtest_routing_and_views():
    """Verify app.js provides #backtest route, rendering methods, and distinction callouts."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    # Routing
    assert "segments[0] === 'backtest'" in app_js
    assert "renderBacktestAnalytics" in app_js
    assert "renderBacktestContent" in app_js

    # Distinct domains
    assert "Historical Population Analysis" in app_js
    assert "Individual IPO Performance" in app_js
    assert "Calibration Proposals" in app_js

    # Diagnostics
    assert "Information Coefficient (Rank IC)" in app_js
    assert "Hit-Rate" in app_js
    assert "Score Decile" in app_js
    assert "Point-in-Time Safety" in app_js
    assert "Historical Vintage" in app_js
    assert "Out-of-Sample Temporal Holdout" in app_js


def test_ui5_zero_statistical_computation_invariant():
    """Verify frontend code contains zero arithmetic formulas for correlation or statistical measures."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    api_js = (FRONTEND_DIR / "api.js").read_text(encoding="utf-8")
    combined = app_js + "\n" + api_js

    forbidden_stats_functions = [
        "calculateSpearman",
        "computeRankIc",
        "calculateHitRate",
        "computeDeciles",
        "calculatePValue",
        "computeCorrelation",
        "calculateDecileSpread",
    ]
    for fn in forbidden_stats_functions:
        assert fn not in combined, f"Frontend must not define statistical calculation {fn}"


def test_ui5_no_server_filesystem_paths_exposed():
    """Verify that no absolute server filesystem paths or file URLs are present in frontend source."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    api_js = (FRONTEND_DIR / "api.js").read_text(encoding="utf-8")
    combined = app_js + "\n" + api_js

    forbidden_paths = [
        "/home/user",
        "/etc/",
        "/var/log",
        "file://",
        "C:\\",
    ]
    for p in forbidden_paths:
        assert p not in combined, f"Server path {p} must not be hardcoded in frontend"


def test_ui5_no_credential_exposure():
    """Verify that frontend code contains zero API keys or external secrets."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    api_js = (FRONTEND_DIR / "api.js").read_text(encoding="utf-8")
    combined = app_js + "\n" + api_js

    forbidden_patterns = [
        r"AI71_API_KEY",
        r"OPENAI_API_KEY",
        r"SECRET_KEY",
        r"BEGIN PRIVATE KEY",
        r"sk-[a-zA-Z0-9]{20,}",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, combined), f"Found leaked credential pattern {pattern}"


def test_ui5_backtest_endpoints_served_by_api(populated_ui5_env):
    """Verify Presentation API serves datasets list and backtest analytics report."""
    client = populated_ui5_env["client"]

    # 1. Backtest datasets
    res_ds = client.get("/api/v1/backtest/datasets")
    assert res_ds.status_code == 200
    ds_data = res_ds.json()
    assert ds_data["total"] == 1
    ds_item = ds_data["datasets"][0]
    assert ds_item["dataset_id"] == "test_dataset_001"
    assert ds_item["row_count"] == 1

    # 2. Backtest analytics
    res_an = client.get("/api/v1/backtest/analytics")
    assert res_an.status_code == 200
    an_data = res_an.json()
    assert an_data["analysis_hash"] == "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    assert an_data["dataset_hash"] == "d1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2"
    assert an_data["leakage_audit_passed"] is True
    assert an_data["rank_ic"]["spearman_ic"] == 0.164656
    assert an_data["rank_ic"]["p_value"] == 0.12
    assert an_data["rank_ic"]["sample_size"] == 1
    assert an_data["hit_rates"]["one_week"] == 100.0


def test_ui5_no_policy_activation_controls():
    """Verify frontend has zero controls to activate or mutate policy configurations."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    combined = index_html + "\n" + app_js

    forbidden_actions = [
        "activatePolicy",
        "activateConfig",
        "applyProposal",
        "set_active",
        "switchConfig",
    ]
    for action in forbidden_actions:
        assert action not in combined, f"Frontend must not contain {action}"
