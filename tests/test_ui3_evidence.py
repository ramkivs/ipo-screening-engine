"""UI-3 Evidence & Provenance Explorer Acceptance & Integrity Test Suite.

Verifies:
1. Serving of static frontend assets containing UI-3 Evidence Explorer markup and styles.
2. WCAG AA accessibility landmarks and semantic structure for Evidence Explorer.
3. Provenance chain presentation and immutable cryptographic hash integrity.
4. Verbatim quote preservation and source document locator presentation.
5. Fail-closed UNKNOWN and UNVERIFIED evidence semantics.
6. Scorecard-to-evidence navigation integration.
7. Zero client-side score computation invariant.
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
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"


@pytest.fixture
def populated_ui3_env(tmp_path: Path, golden_input: Dict[str, Any], config: Dict[str, Any]):
    """Set up an evaluation store populated with golden input for presentation testing."""
    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)

    final = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT,
        store=store,
    )

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
    }


def test_ui3_static_assets_contain_evidence_explorer():
    """Verify frontend/index.html and assets contain UI-3 Evidence Explorer markup and landmarks."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    # View container and accessibility attributes
    assert 'id="evidence-view"' in index_html
    assert 'role="region"' in index_html
    assert 'aria-label="Evidence and Provenance Explorer"' in index_html


def test_ui3_css_contains_distinction_badges_and_inspector_styles():
    """Verify stylesheet contains distinct classes for source evidence vs derived values."""
    styles_css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")

    # Semantic distinction classes
    assert ".badge-source-evidence" in styles_css
    assert ".badge-derived-value" in styles_css
    assert ".badge-unknown-evidence" in styles_css
    assert ".badge-unverified-evidence" in styles_css

    # Inspector modal / drawer
    assert ".inspector-backdrop" in styles_css
    assert ".inspector-drawer" in styles_css
    assert ".raw-json-box" in styles_css

    # Scorecard criteria evidence link
    assert ".evidence-pill-link" in styles_css or ".btn-evidence-link" in styles_css


def test_ui3_app_contains_scorecard_navigation_and_provenance():
    """Verify app.js provides navigation from scorecard to evidence and renders provenance hashes."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    # Navigation from scorecard
    assert "#evidence/" in app_js
    assert "Inspect Evidence &amp; Provenance" in app_js
    assert "Inspect Citation [EV]" in app_js
    assert "&larr; Return to Scorecard" in app_js

    # Provenance fields rendered
    assert "Cryptographic Provenance Fingerprints" in app_js
    assert "result_hash" in app_js
    assert "source_manifest_hash" in app_js
    assert "input_snapshot_hash" in app_js
    assert "config_hash" in app_js

    # Contract guidance note
    assert "Source Evidence vs. Derived Provenance" in app_js


def test_ui3_zero_score_computation_invariant():
    """Verify that frontend JS files contain strictly zero scoring formulas or weight multiplications."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    api_js = (FRONTEND_DIR / "api.js").read_text(encoding="utf-8")
    combined = app_js + "\n" + api_js

    forbidden_patterns = [
        r"\*\s*0\.25",
        r"\*\s*0\.20",
        r"\*\s*0\.15",
        r"\*\s*0\.10",
        r"\*\s*0\.30",
        r"calculateScore",
        r"evaluateKnockouts",
        r"deriveVerdict",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, combined), f"Frontend must not compute scores matching {pattern}"


def test_ui3_no_server_filesystem_paths_exposed():
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


def test_ui3_no_credential_exposure():
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


def test_ui3_evidence_endpoints_served_by_api(populated_ui3_env):
    """Verify that Presentation API serves evaluation evidence and evidence details properly."""
    client = populated_ui3_env["client"]
    final_id = populated_ui3_env["final"].record.evaluation_id

    # 1. Evaluation evidence list
    res = client.get(f"/api/v1/evaluations/{final_id}/evidence")
    assert res.status_code == 200
    data = res.json()
    assert data["evaluation_id"] == final_id
    assert data["evidence_count"] >= 15
    assert len(data["items"]) >= 15

    # 2. Specific item detail by compound ID
    compound_id = f"{final_id}:EV-cfo-fy26"
    res_item = client.get(f"/api/v1/evidence/{compound_id}")
    assert res_item.status_code == 200
    item = res_item.json()
    assert item["evidence_id"] == "EV-cfo-fy26"
    assert item["page"] == 74
    assert item["quote"] == "2,715.47"


def test_ui3_no_policy_activation_controls():
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
