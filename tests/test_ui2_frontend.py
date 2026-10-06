"""UI-2 Frontend Delivery & Integrity Test Suite.

Verifies:
1. Serving of static frontend assets via presentation API.
2. Structural compliance of UI-2 Executive Dashboard & Scorecard.
3. WCAG AA accessibility landmarks and semantic tagging.
4. Zero score calculation invariant (no frontend formulas or weighting).
5. Read-only invariant (zero mutation endpoints, methods, or activation buttons).
6. Fail-closed invariant (UNKNOWN states preserved, never converted to 0.00).
7. Governance display invariant (v1.5 ACTIVE, v1.6 INACTIVE, no activation controls).
"""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ipo_screening.presentation.api import create_app

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_ui2_static_assets_served(client):
    """Test that frontend static assets are served properly via /ui and root redirect."""
    # Root redirect
    res_root = client.get("/", follow_redirects=False)
    assert res_root.status_code in (301, 302, 307, 308)
    assert res_root.headers.get("location") == "/ui/"

    # Index HTML
    res_index = client.get("/ui/")
    assert res_index.status_code == 200
    assert "text/html" in res_index.headers.get("content-type", "")
    assert "IPO Screening Engine" in res_index.text
    assert "Executive Dashboard" in res_index.text
    assert "Evaluation Scorecard" in res_index.text

    # Javascript application modules
    res_app = client.get("/ui/app.js")
    assert res_app.status_code == 200
    assert "javascript" in res_app.headers.get("content-type", "")

    res_api = client.get("/ui/api.js")
    assert res_api.status_code == 200
    assert "javascript" in res_api.headers.get("content-type", "")

    # CSS Stylesheet
    res_css = client.get("/ui/styles.css")
    assert res_css.status_code == 200
    assert "text/css" in res_css.headers.get("content-type", "")


def test_ui2_html_structure_and_aria_landmarks():
    """Verify semantic HTML5 structure, ARIA landmarks, and accessibility compliance."""
    index_path = FRONTEND_DIR / "index.html"
    assert index_path.exists(), "frontend/index.html must exist"
    content = index_path.read_text(encoding="utf-8")

    # Semantic ARIA landmarks
    assert 'role="banner"' in content
    assert 'role="navigation"' in content
    assert 'role="main"' in content
    assert 'role="region"' in content
    assert 'aria-label="Executive Dashboard"' in content
    assert 'aria-label="IPO Directory"' in content
    assert 'aria-label="Evaluation Scorecard"' in content

    # View containers
    assert 'id="dashboard-view"' in content
    assert 'id="directory-view"' in content
    assert 'id="scorecard-view"' in content

    # Engine badge
    assert "v1.5.0" in content


def test_ui2_zero_calculation_invariant():
    """Verify that frontend source code contains strictly zero engine scoring logic or weight math."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    api_js = (FRONTEND_DIR / "api.js").read_text(encoding="utf-8")

    combined = app_js + "\n" + api_js

    # No scoring weights
    forbidden_weight_patterns = [
        r"\*\s*0\.25",  # Module A weight
        r"\*\s*0\.20",  # Module B weight
        r"\*\s*0\.15",  # Module C weight
        r"\*\s*0\.10",  # Module D weight
        r"\*\s*0\.30",  # Module E weight
    ]
    for pattern in forbidden_weight_patterns:
        match = re.search(pattern, combined)
        assert match is None, f"Frontend must not compute weighted scores matching {pattern}"

    # No calculation functions
    forbidden_identifiers = [
        "calculateScore",
        "computeScore",
        "evaluateKnockouts",
        "calculatePenalties",
        "deriveVerdict",
        "computeConfidence",
    ]
    for identifier in forbidden_identifiers:
        assert identifier not in combined, f"Frontend must not define {identifier}"


def test_ui2_zero_mutation_and_read_only_protocol():
    """Verify frontend API client and router do not support HTTP mutations."""
    api_js = (FRONTEND_DIR / "api.js").read_text(encoding="utf-8")

    # No mutation methods in ApiClient
    assert "POST" not in api_js
    assert "PUT" not in api_js
    assert "PATCH" not in api_js
    assert "DELETE" not in api_js

    # ApiClient must only use GET
    assert "method: 'GET'" in api_js


def test_ui2_fail_closed_unknown_representation():
    """Verify UNKNOWN state classes and fail-closed handling in CSS and JS."""
    styles_css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    # CSS classes for fail-closed states
    assert ".badge-unknown" in styles_css
    assert ".badge-insufficient" in styles_css
    assert ".ko-unverified" in styles_css
    assert ".ko-triggered" in styles_css
    assert ".ko-clear" in styles_css

    # JS handling
    assert "UNKNOWN" in app_js
    assert "NOT_APPLICABLE" in app_js
    assert "INSUFFICIENT_DATA" in app_js


def test_ui2_no_configuration_activation_controls():
    """Verify that frontend provides zero mechanisms or UI controls to activate draft configurations."""
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    combined = index_html + "\n" + app_js

    forbidden_governance_actions = [
        "activateConfig",
        "activatePolicy",
        "set_active",
        "applyDraft",
        "switchConfig",
        "acceptProposal",
    ]
    for action in forbidden_governance_actions:
        assert action not in combined, f"Frontend must not contain {action}"


def test_ui2_no_credential_exposure():
    """Verify that frontend code contains zero API keys or external secrets."""
    app_js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    api_js = (FRONTEND_DIR / "api.js").read_text(encoding="utf-8")
    index_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    combined = app_js + "\n" + api_js + "\n" + index_html

    forbidden_patterns = [
        r"AI71_API_KEY",
        r"OPENAI_API_KEY",
        r"SECRET_KEY",
        r"BEGIN PRIVATE KEY",
        r"sk-[a-zA-Z0-9]{20,}",
    ]
    for pattern in forbidden_patterns:
        match = re.search(pattern, combined)
        assert match is None, f"Found leaked credential pattern {pattern}"
