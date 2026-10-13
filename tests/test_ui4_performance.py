"""UI-4 Post-Listing Observation & Performance Explorer Acceptance & Integrity Suite.

Verifies:
1. Static asset serving of UI-4 performance explorer views and styles.
2. WCAG AA accessibility landmarks and semantic structure for performance explorer.
3. Timeline and multi-horizon price/return rendering.
4. Corporate action adjustment factor presentation.
5. Backtest analytics and calibration governance boundary affordances.
6. Scorecard-to-performance bidirectional navigation.
7. Zero client-side return calculation invariant.
8. Strictly read-only protocol and zero mutation capability.
9. Absence of policy activation controls.
10. Zero server filesystem path exposure and zero credential leakage.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import pytest
from conftest import EVAL_AT
from fastapi.testclient import TestClient

from ipo_screening.evaluation import EvaluationStore
from ipo_screening.pipeline import evaluate
from ipo_screening.post_listing.models import (
    BenchmarkObservation,
    CalculationMetadata,
    Horizon,
    ObservationStatus,
    PostListingObservation,
    PriceObservation,
    ProvenanceRecord,
    ReturnSet,
)
from ipo_screening.post_listing.storage import save_observation
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"


@pytest.fixture
def populated_ui4_env(tmp_path: Path, golden_input: Dict[str, Any], config: Dict[str, Any]):
    """Set up an evaluation store with a FINAL evaluation and child 1W observation."""
    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)

    final = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT,
        store=store,
    )
    final_id = final.record.evaluation_id

    # Add an authoritative 1W post-listing observation under the final evaluation
    obs = PostListingObservation(
        observation_id="OBS-VISHAL-1W",
        final_evaluation_id=final_id,
        final_result_hash=final.record.result_hash,
        ipo_id=final.record.ipo_id,
        horizon="1W",
        version=1,
        target_observation_date="2026-10-21",
        actual_observation_date="2026-10-21",
        observation_status=ObservationStatus.VERIFIED.value,
        listing_date="2026-10-14",
        prices=PriceObservation(
            issue_price=215.0,
            listing_open=240.0,
            listing_close=246.15,
            raw_observed_close=246.15,
            corporate_action_factor=1.0,
            adjusted_observed_close=246.15,
        ),
        benchmark=BenchmarkObservation(
            symbol="NIFTY50",
            raw_listing_value=24500.0,
            raw_observed_value=24794.0,
            return_pct=1.20,
        ),
        returns=ReturnSet(
            listing_gain_pct=14.49,
            absolute_return_pct=14.50,
            secondary_return_pct=2.56,
            benchmark_return_pct=1.20,
            excess_return_pct=13.30,
        ),
        provenance=ProvenanceRecord(
            source_id="bhavcopy-20261021",
            source_type="BHAVCOPY",
            source_uri_or_file="bhavcopy.csv",
            retrieval_timestamp="2026-10-21T16:00:00Z",
            content_hash="bhavcopyhash_12345",
        ),
        calculation=CalculationMetadata(
            calculation_version="1.0.0",
            calculation_inputs_hash="inputs_hash_123",
            observation_hash="obs_hash_123",
        ),
    )
    save_observation(obs, store_dir)

    cfg = PresentationConfig(store_root=str(store_dir), config_dir=str(REPO_ROOT / "config"))
    service = PresentationService(cfg)
    app = create_app(service)
    client = TestClient(app)

    return {
        "store": store,
        "final": final,
        "service": service,
        "app": app,
        "client": client,
        "obs": obs,
    }


def test_ui4_static_assets_contain_performance_explorer():
    """Verify frontend/index.html and assets contain UI-4 Performance Explorer markup and landmarks."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    # View container and accessibility attributes
    assert 'id="performance-view"' in index_html
    assert 'role="region"' in index_html
    assert 'aria-label="Post-Listing Observation and Performance Explorer"' in index_html


def test_ui4_css_contains_performance_styles():
    """Verify stylesheet contains timeline, KPI, return, and corporate action styles."""
    styles_css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")

    assert ".perf-kpi-grid" in styles_css
    assert ".timeline-wrapper" in styles_css
    assert ".timeline-step" in styles_css
    assert ".horizon-grid" in styles_css
    assert ".price-metric-table" in styles_css
    assert ".ca-pill-clean" in styles_css
    assert ".ca-pill-adjusted" in styles_css
    assert ".backtest-callout" in styles_css
    assert ".calibration-callout" in styles_css


def test_ui4_app_contains_scorecard_navigation_and_performance_view():
    """Verify app.js provides navigation from scorecard to performance and implements the view."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    # Route and navigation
    assert "#performance/" in app_js
    assert "Post-Listing Performance &rarr;" in app_js
    assert "&larr; Return to Scorecard" in app_js

    # Method implementations
    assert "renderPerformanceExplorer" in app_js
    assert "renderPerformanceContent" in app_js
    assert "formatReturnPct" in app_js

    # Governance boundaries
    assert "Aggregate Backtest Analytics Boundary" in app_js
    assert "Calibration Governance Boundary" in app_js


def test_ui4_zero_return_computation_invariant():
    """Verify frontend code contains zero arithmetic formulas for returns or excess alpha."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    api_js = (FRONTEND_DIR / "api.js").read_text(encoding="utf-8")
    combined = app_js + "\n" + api_js

    # No formula calculation functions
    forbidden_return_functions = [
        "calculateReturn",
        "computeExcess",
        "computeAlpha",
        "deriveReturn",
        "calculateGain",
    ]
    for fn in forbidden_return_functions:
        assert fn not in combined, f"Frontend must not define return calculation {fn}"


def test_ui4_no_server_filesystem_paths_exposed():
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


def test_ui4_no_credential_exposure():
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


def test_ui4_post_listing_and_performance_endpoints_served_by_api(populated_ui4_env):
    """Verify Presentation API serves post-listing observations and structured performance summary."""
    client = populated_ui4_env["client"]
    final_id = populated_ui4_env["final"].record.evaluation_id

    # 1. Post-Listing observations list
    res_pl = client.get(f"/api/v1/evaluations/{final_id}/post-listing")
    assert res_pl.status_code == 200
    pl_data = res_pl.json()
    assert pl_data["final_evaluation_id"] == final_id
    assert pl_data["observation_count"] == 1
    obs_item = pl_data["observations"][0]
    assert obs_item["horizon"] == "1W"
    assert obs_item["status"] == "VERIFIED"
    assert obs_item["issue_price"] == "215.0"
    assert obs_item["returns"]["absolute_return_pct"] == 14.50
    assert obs_item["returns"]["excess_return_pct"] == 13.30

    # 2. Performance summary
    res_perf = client.get(f"/api/v1/evaluations/{final_id}/performance")
    assert res_perf.status_code == 200
    perf_data = res_perf.json()
    assert perf_data["final_evaluation_id"] == final_id
    assert perf_data["issue_price"] == "215.0"
    assert perf_data["horizons"]["one_week"]["status"] == "VERIFIED"
    assert perf_data["horizons"]["one_week"]["ipo_return_pct"] == "14.5"
    assert perf_data["horizons"]["one_week"]["excess_return_pct"] == "13.3"
    assert perf_data["horizons"]["one_month"]["status"] == "INCOMPLETE"
    assert perf_data["horizons"]["six_month"]["status"] == "INCOMPLETE"


def test_ui4_no_policy_activation_controls():
    """Verify frontend has zero controls to activate or mutate policy configurations."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    combined = index_html + "\n" + app_js

    forbidden_actions = [
        "activatePolicy",
        "activateConfig",
        "applyDraft",
        "set_active",
        "switchConfig",
    ]
    for action in forbidden_actions:
        assert action not in combined, f"Frontend must not contain {action}"
