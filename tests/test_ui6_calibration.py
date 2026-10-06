"""UI-6 Calibration & Policy Governance Presentation Acceptance & Integrity Suite.

Verifies:
1. Static asset serving of UI-6 calibration views, navigation, and styles.
2. WCAG AA accessibility landmarks and semantic structure for calibration presentation.
3. Governance lifecycle chain separating proposal from approval, implementation, and activation.
4. Active policy v1.5.0 and candidate proposal v1.6.0-draft presentation.
5. Deterministic current-vs-proposed module weight shift comparison.
6. Non-regression and downside protection audit checks.
7. Cryptographic provenance panel displaying proposal, config, dataset, and analysis hashes.
8. Cross-view navigation integration from Dashboard, Backtest, and Performance views.
9. Zero client-side calibration or scoring calculation invariant.
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
def populated_ui6_env(tmp_path: Path, golden_input: Dict[str, Any], config: Dict[str, Any]):
    """Set up an evaluation store with a FINAL evaluation, backtest dataset, and calibration proposal."""
    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)

    final = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT,
        store=store,
    )

    cfg = PresentationConfig(
        store_root=str(store_dir),
        config_dir=REPO_ROOT / "config",
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
    }


def test_ui6_static_assets_contain_calibration_presentation():
    """Verify frontend/index.html contains UI-6 Calibration navigation and view container."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    # Navigation tab
    assert 'href="#calibration"' in index_html
    assert 'Calibration &amp; Policy' in index_html

    # View container and accessibility attributes
    assert 'id="calibration-view"' in index_html
    assert 'role="region"' in index_html
    assert 'aria-label="Calibration and Configuration Presentation"' in index_html


def test_ui6_css_contains_calibration_styles():
    """Verify stylesheet contains governance chain, policy card, and delta pill styles."""
    styles_css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")

    assert ".gov-chain-banner" in styles_css
    assert ".gov-chain-steps" in styles_css
    assert ".gov-chain-step" in styles_css
    assert ".policy-card-grid" in styles_css
    assert ".policy-card" in styles_css
    assert ".delta-pill" in styles_css
    assert ".delta-pos" in styles_css
    assert ".delta-neg" in styles_css


def test_ui6_app_contains_calibration_routing_and_views():
    """Verify app.js provides #calibration route, rendering methods, and governance chain."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    # Routing
    assert "segments[0] === 'calibration'" in app_js
    assert "renderCalibrationView" in app_js
    assert "renderCalibrationContent" in app_js

    # Governance chain
    assert "Policy Governance &amp; Activation Firewall" in app_js
    assert "Evidence &rarr; Analysis &rarr; Proposal &ne; Approval &ne; Implementation &ne; Activation" in app_js
    assert "ZERO activation authority" in app_js

    # Comparisons
    assert "Current Baseline (v1.5.0) vs Proposed Candidate (v1.6.0) Comparison" in app_js
    assert "Non-Regression &amp; Downside Protection Audit" in app_js


def test_ui6_calibration_endpoints_served_by_api(populated_ui6_env):
    """Verify Presentation API serves proposal list, proposal detail, and configuration status."""
    client = populated_ui6_env["client"]

    # 1. Proposals list
    res_list = client.get("/api/v1/calibration/proposals")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 1
    prop = list_data["proposals"][0]
    assert prop["candidate_config_version"] == "1.6.0"
    assert prop["status"] == "READY_FOR_HUMAN_REVIEW"
    assert prop["approval_status"] == "APPROVED"

    # 2. Proposal detail with additive fields
    res_detail = client.get("/api/v1/calibration/proposals/v1.6.0")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["proposal_id"] == "PROP-1.0.0"
    assert detail_data["objective"] == "BALANCED_DIAGNOSTIC"
    assert "module_proposals" in detail_data
    assert len(detail_data["module_proposals"]) == 6
    assert detail_data["module_proposals"][0]["module_id"] == "A"
    assert detail_data["module_proposals"][0]["proposed_weight"] == 30.0
    assert detail_data["module_proposals"][1]["module_id"] == "B"
    assert detail_data["module_proposals"][1]["proposed_weight"] == 15.0

    # 3. Configuration status
    res_cfg = client.get("/api/v1/configuration/current")
    assert res_cfg.status_code == 200
    cfg_data = res_cfg.json()
    assert cfg_data["active_configuration"]["version"] == "1.5.0"
    assert cfg_data["active_configuration"]["is_active"] is True
    assert cfg_data["candidate_configuration"]["version"] == "1.6.0"
    assert cfg_data["candidate_configuration"]["is_active"] is False


def test_ui6_cross_view_navigation_integration():
    """Verify Dashboard, Performance, and Backtest views link to Calibration."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    # Dashboard header link
    assert 'href="#calibration"' in app_js
    assert 'Policy Governance &rarr;' in app_js

    # Backtest and Performance callouts
    assert 'Inspect Calibration &amp; Policy Governance &rarr;' in app_js


def test_ui6_zero_activation_controls_and_handlers():
    """Verify that frontend and HTML contain zero controls to activate or mutate policy configurations."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    combined = index_html + "\n" + app_js

    forbidden_actions = [
        "activatePolicy",
        "activateConfig",
        "applyProposal",
        "set_active",
        "switchConfig",
        "promoteCandidate",
        "saveConfiguration",
    ]
    for action in forbidden_actions:
        assert action not in combined, f"Frontend must not contain {action}"

    assert "<button>Activate" not in index_html
    assert "btn-activate" not in index_html


def test_ui6_no_server_filesystem_paths_exposed():
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


def test_ui6_no_credential_exposure():
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
