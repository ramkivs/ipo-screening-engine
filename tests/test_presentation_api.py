"""UI-1 Presentation API & Read-Model Test Suite.

Asserts contract adherence, read-only enforcement, UNKNOWN semantics,
deterministic ordering, provenance preservation, and governance boundaries.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
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


@pytest.fixture
def populated_env(tmp_path: Path, golden_input: Dict[str, Any], config: Dict[str, Any]):
    """Set up a test environment with preliminary and final evaluations and observations."""
    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)

    prelim = evaluate(
        golden_input,
        config,
        mode="preliminary",
        evaluation_datetime=EVAL_AT - timedelta(hours=1),
        store=store,
    )
    final = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT,
        store=store,
    )

    # Add a mock post-listing observation under the final evaluation
    obs = PostListingObservation(
        observation_id="OBS-VISHAL-1W",
        final_evaluation_id=final.record.evaluation_id,
        final_result_hash=final.record.result_hash,
        ipo_id=golden_input["ipo_id"],
        horizon=Horizon.W1.value,
        listing_date="2026-10-06",
        target_observation_date="2026-10-13",
        actual_observation_date="2026-10-13",
        prices=PriceObservation(
            issue_price=100.0,
            listing_open=110.0,
            raw_observed_close=115.5,
            corporate_action_factor=1.0,
            adjusted_observed_close=115.5,
        ),
        benchmark=BenchmarkObservation(
            symbol="NIFTY_50_TRI",
            raw_listing_value=25000.0,
            raw_observed_value=25250.0,
            return_pct=1.0,
        ),
        returns=ReturnSet(
            listing_gain_pct=10.0,
            absolute_return_pct=15.5,
            secondary_return_pct=5.0,
            benchmark_return_pct=1.0,
            excess_return_pct=14.5,
        ),
        provenance=ProvenanceRecord(
            source_id="BHAV-TEST-001",
            source_type="CSV_BHAVCOPY",
            source_uri_or_file="bhav.csv",
            retrieval_timestamp="2026-10-06T12:00:00Z",
            content_hash="mockcontenthash123",
        ),
        calculation=CalculationMetadata(
            calculation_version="1.0.0",
            calculation_inputs_hash="inputs_hash_123",
            observation_hash="obs_hash_123",
        ),
        observation_status=ObservationStatus.VERIFIED.value,
        version=1,
    )
    save_observation(obs, store_dir)

    # Create dummy dataset and analytics
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
                    "included_observation_count": 1,
                    "status_counts": {"READY": 1},
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

    pres_cfg = PresentationConfig(
        store_root=store_dir,
        config_dir=Path("config"),
        dataset_path=dataset_file,
        analytics_path=analytics_file,
        proposal_path=Path("config/calibration-proposal.v1.6.0.json"),
    )
    service = PresentationService(pres_cfg)
    app = create_app(service)
    client = TestClient(app)

    return {
        "client": client,
        "service": service,
        "prelim": prelim,
        "final": final,
        "store": store,
        "store_dir": store_dir,
    }


# -----------------------------------------------------------------------------
# 1. Contract & Schema Validity
# -----------------------------------------------------------------------------


def test_openapi_contract_file_is_valid_and_complete():
    """Verify OpenAPI 3.1 YAML specification syntax and path declarations."""
    spec_path = Path("docs/openapi/presentation-api-v1.yaml")
    assert spec_path.is_file(), "docs/openapi/presentation-api-v1.yaml must exist"

    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    assert spec.get("openapi") == "3.1.0"
    paths = spec.get("paths") or {}

    expected_paths = [
        "/health",
        "/meta",
        "/ipos",
        "/ipos/{ipo_id}",
        "/ipos/{ipo_id}/history",
        "/evaluations",
        "/evaluations/{evaluation_id}",
        "/evaluations/{evaluation_id}/evidence",
        "/evidence/{evidence_id}",
        "/evaluations/{evaluation_id}/post-listing",
        "/evaluations/{evaluation_id}/performance",
        "/backtest/datasets",
        "/backtest/analytics",
        "/calibration/proposals",
        "/calibration/proposals/{proposal_id}",
        "/configuration/current",
    ]
    for ep in expected_paths:
        assert ep in paths, f"Path {ep} missing from OpenAPI specification"


# -----------------------------------------------------------------------------
# 2. Read-Only Enforcement
# -----------------------------------------------------------------------------


def test_mutation_methods_strictly_prohibited(populated_env):
    """Spec s2: Read-only enforcement blocks POST, PUT, PATCH, DELETE with 405."""
    client = populated_env["client"]

    for method in ["POST", "PUT", "PATCH", "DELETE"]:
        res = client.request(method, "/api/v1/evaluations")
        assert res.status_code == 405
        body = res.json()
        assert body["code"] == "READ_ONLY_METHOD_NOT_ALLOWED"


# -----------------------------------------------------------------------------
# 3. System Endpoints (Health & Meta)
# -----------------------------------------------------------------------------


def test_health_endpoint(populated_env):
    """GET /api/v1/health returns healthy and read_only: true."""
    client = populated_env["client"]
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["read_only"] is True


def test_meta_endpoint(populated_env):
    """GET /api/v1/meta returns versioning and golden result hash."""
    client = populated_env["client"]
    res = client.get("/api/v1/meta")
    assert res.status_code == 200
    data = res.json()
    assert data["api_version"] == "v1"
    assert data["engine_version"] == "1.5.0"
    assert data["active_config_version"] == "1.5.0"
    assert data["candidate_config_version"] == "1.6.0"
    assert data["candidate_config_status"] == "IMPLEMENTED_INACTIVE"
    assert data["golden_result_hash"] == "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"


# -----------------------------------------------------------------------------
# 4. IPO Discovery & Detail
# -----------------------------------------------------------------------------


def test_list_ipos(populated_env):
    """GET /api/v1/ipos lists evaluated IPO issuers."""
    client = populated_env["client"]
    res = client.get("/api/v1/ipos")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["ipo_id"] == "VISHAL-NIRMITI-LIMITED"
    assert item["company_name"] == "Vishal Nirmiti Limited"
    assert item["evaluation_count"] == 2
    assert item["latest_evaluation_mode"] == "FINAL"
    assert item["latest_score"] == 35.0
    assert item["latest_verdict"] == "INSUFFICIENT_DATA"


def test_get_ipo_detail(populated_env):
    """GET /api/v1/ipos/{ipo_id} returns authoritative issuer details."""
    client = populated_env["client"]
    res = client.get("/api/v1/ipos/VISHAL-NIRMITI-LIMITED")
    assert res.status_code == 200
    data = res.json()
    assert data["ipo_id"] == "VISHAL-NIRMITI-LIMITED"
    assert len(data["evaluations"]) == 2
    modes = [e["evaluation_mode"] for e in data["evaluations"]]
    assert modes == ["PRELIMINARY", "FINAL"]


def test_get_ipo_history_with_delta(populated_env):
    """GET /api/v1/ipos/{ipo_id}/history returns timeline and preliminary delta."""
    client = populated_env["client"]
    res = client.get("/api/v1/ipos/VISHAL-NIRMITI-LIMITED/history")
    assert res.status_code == 200
    data = res.json()
    assert data["ipo_id"] == "VISHAL-NIRMITI-LIMITED"
    assert len(data["history"]) == 2
    delta = data.get("delta")
    assert delta is not None
    assert delta["preliminary_score"] == 36.0
    assert delta["final_score"] == 35.0


def test_get_nonexistent_ipo(populated_env):
    """GET /api/v1/ipos/{unknown} returns 404 with structured ApiError."""
    client = populated_env["client"]
    res = client.get("/api/v1/ipos/NONEXISTENT-IPO")
    assert res.status_code == 404
    data = res.json()
    assert data["code"] == "IPO_NOT_FOUND"


# -----------------------------------------------------------------------------
# 5. Evaluation Discovery & Detail
# -----------------------------------------------------------------------------


def test_list_evaluations_filtering(populated_env):
    """GET /api/v1/evaluations filters by mode, verdict, etc."""
    client = populated_env["client"]

    # All evaluations
    res_all = client.get("/api/v1/evaluations")
    assert res_all.status_code == 200
    assert res_all.json()["total"] == 2

    # Filter by mode=FINAL
    res_final = client.get("/api/v1/evaluations?mode=FINAL")
    assert res_final.status_code == 200
    assert res_final.json()["total"] == 1
    assert res_final.json()["items"][0]["evaluation_mode"] == "FINAL"

    # Filter by verdict=INSUFFICIENT_DATA
    res_verd = client.get("/api/v1/evaluations?verdict=INSUFFICIENT_DATA")
    assert res_verd.status_code == 200
    assert res_verd.json()["total"] == 2


def test_get_evaluation_detail_preserves_golden_scorecard(populated_env):
    """GET /api/v1/evaluations/{id} preserves exact golden scorecard values."""
    client = populated_env["client"]
    final_id = populated_env["final"].record.evaluation_id

    res = client.get(f"/api/v1/evaluations/{final_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["evaluation_id"] == final_id
    assert data["result_hash"] == "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"

    score = data["score"]
    assert score["final_score"] == 35.0
    assert score["base_score"] == 38.0
    assert score["penalties_total"] == -3.0
    assert score["lower_bound"] == 25.0
    assert score["upper_bound"] == 62.0
    assert score["confidence"] == "Low"
    assert score["completeness_pct"] == 73.0

    # Knockouts
    knockouts = data["knockouts"]
    assert knockouts["status"] == "UNVERIFIED"
    k_states = {r["id"]: r["state"] for r in knockouts["rules"]}
    assert k_states["K1"] == "UNVERIFIED"
    assert k_states["K2"] == "CLEAR"

    # Module scores
    modules = {m["id"]: m["score"] for m in score["modules"]}
    assert len(modules) == 6
    assert sum(modules.values()) == 38.0


def test_get_nonexistent_evaluation(populated_env):
    """GET /api/v1/evaluations/{unknown} returns 404."""
    client = populated_env["client"]
    res = client.get("/api/v1/evaluations/eval_9999999999999999")
    assert res.status_code == 404
    assert res.json()["code"] == "EVALUATION_NOT_FOUND"


# -----------------------------------------------------------------------------
# 6. Evidence Registry Endpoints
# -----------------------------------------------------------------------------


def test_get_evaluation_evidence(populated_env):
    """GET /api/v1/evaluations/{id}/evidence returns citations and quotes."""
    client = populated_env["client"]
    final_id = populated_env["final"].record.evaluation_id

    res = client.get(f"/api/v1/evaluations/{final_id}/evidence")
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_count"] >= 15
    items = data["items"]
    assert len(items) >= 15
    first = items[0]
    assert first["field"] != ""
    assert first["page"] is not None
    assert first["quote"] is not None


def test_get_evidence_item_by_compound_id(populated_env):
    """GET /api/v1/evidence/{eval_id}:{ev_id} resolves specific item."""
    client = populated_env["client"]
    final_id = populated_env["final"].record.evaluation_id

    res = client.get(f"/api/v1/evidence/{final_id}:EV-cfo-fy26")
    assert res.status_code == 200
    item = res.json()
    assert item["evidence_id"] == "EV-cfo-fy26"
    assert item["page"] == 74
    assert item["quote"] == "2,715.47"


# -----------------------------------------------------------------------------
# 7. Post-Listing & Performance
# -----------------------------------------------------------------------------


def test_get_post_listing_observations(populated_env):
    """GET /api/v1/evaluations/{id}/post-listing returns child observations."""
    client = populated_env["client"]
    final_id = populated_env["final"].record.evaluation_id

    res = client.get(f"/api/v1/evaluations/{final_id}/post-listing")
    assert res.status_code == 200
    data = res.json()
    assert data["observation_count"] == 1
    obs = data["observations"][0]
    assert obs["horizon"] == "1W"
    assert obs["status"] == "VERIFIED"
    assert obs["returns"]["excess_return_pct"] == 14.5


def test_get_performance_summary(populated_env):
    """GET /api/v1/evaluations/{id}/performance returns multi-horizon tracker."""
    client = populated_env["client"]
    final_id = populated_env["final"].record.evaluation_id

    res = client.get(f"/api/v1/evaluations/{final_id}/performance")
    assert res.status_code == 200
    data = res.json()
    horizons = data["horizons"]
    assert horizons["one_week"]["status"] == "VERIFIED"
    assert horizons["one_week"]["excess_return_pct"] == "14.5"
    # Incomplete horizons have explicit null returns
    assert horizons["six_month"]["status"] == "INCOMPLETE"
    assert horizons["six_month"]["excess_return_pct"] is None


# -----------------------------------------------------------------------------
# 8. Backtest & Calibration
# -----------------------------------------------------------------------------


def test_get_backtest_datasets_and_analytics(populated_env):
    """GET /api/v1/backtest/datasets and /api/v1/backtest/analytics."""
    client = populated_env["client"]

    res_ds = client.get("/api/v1/backtest/datasets")
    assert res_ds.status_code == 200
    assert res_ds.json()["total"] == 1

    res_an = client.get("/api/v1/backtest/analytics")
    assert res_an.status_code == 200
    an_data = res_an.json()
    assert an_data["leakage_audit_passed"] is True
    assert an_data["rank_ic"]["spearman_ic"] == 0.164656


def test_get_calibration_proposals(populated_env):
    """GET /api/v1/calibration/proposals returns proposal artifact."""
    client = populated_env["client"]

    res_list = client.get("/api/v1/calibration/proposals")
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 1

    res_item = client.get("/api/v1/calibration/proposals/v1.6.0")
    assert res_item.status_code == 200
    prop = res_item.json()
    assert prop["candidate_config_version"] == "1.6.0"
    assert prop["approval_status"] == "APPROVED"
    assert prop["module_weight_adjustments"]["A"] == 30.0
    assert prop["module_weight_adjustments"]["B"] == 15.0


# -----------------------------------------------------------------------------
# 9. Configuration Status & Governance
# -----------------------------------------------------------------------------


def test_configuration_status_governance_invariants(populated_env):
    """GET /api/v1/configuration/current asserts v1.5 is ACTIVE, v1.6 is INACTIVE."""
    client = populated_env["client"]

    res = client.get("/api/v1/configuration/current")
    assert res.status_code == 200
    data = res.json()

    active_cfg = data["active_configuration"]
    assert active_cfg["version"] == "1.5.0"
    assert active_cfg["status"] == "ACTIVE"
    assert active_cfg["is_active"] is True

    candidate_cfg = data["candidate_configuration"]
    assert candidate_cfg["version"] == "1.6.0"
    assert candidate_cfg["status"] == "IMPLEMENTED_INACTIVE"
    assert candidate_cfg["is_active"] is False

    assert data["frozen_core_status"] == "VERIFIED"
    assert data["golden_result_status"] == "VERIFIED"


# -----------------------------------------------------------------------------
# 10. Edge Cases & Missing Data Handling
# -----------------------------------------------------------------------------


def test_empty_store_returns_empty_lists(tmp_path: Path):
    """Test behavior when EvaluationStore is empty."""
    empty_store = tmp_path / "empty_store"
    empty_store.mkdir()

    pres_cfg = PresentationConfig(
        store_root=empty_store,
        config_dir=Path("config"),
        dataset_path=None,
        analytics_path=None,
        proposal_path=Path("config/calibration-proposal.v1.6.0.json"),
    )
    service = PresentationService(pres_cfg)
    app = create_app(service)
    client = TestClient(app)

    res_ipos = client.get("/api/v1/ipos")
    assert res_ipos.status_code == 200
    assert res_ipos.json()["total"] == 0
    assert res_ipos.json()["items"] == []

    res_evals = client.get("/api/v1/evaluations")
    assert res_evals.status_code == 200
    assert res_evals.json()["total"] == 0
    assert res_evals.json()["items"] == []


def test_nonexistent_resources_return_404(populated_env):
    """Ensure missing resources return 404 with standard ApiError."""
    client = populated_env["client"]

    # Nonexistent post-listing
    res1 = client.get("/api/v1/evaluations/eval_fake_id/post-listing")
    assert res1.status_code == 404
    assert res1.json()["code"] == "EVALUATION_NOT_FOUND"

    # Nonexistent performance
    res2 = client.get("/api/v1/evaluations/eval_fake_id/performance")
    assert res2.status_code == 404
    assert res2.json()["code"] == "EVALUATION_NOT_FOUND"

    # Nonexistent evidence item
    res3 = client.get("/api/v1/evidence/EV-totally-fake")
    assert res3.status_code == 404
    assert res3.json()["code"] == "EVIDENCE_NOT_FOUND"

    # Nonexistent proposal
    res4 = client.get("/api/v1/calibration/proposals/v9.9.9")
    assert res4.status_code == 404
    assert res4.json()["code"] == "PROPOSAL_NOT_FOUND"


def test_pagination_beyond_available_data(populated_env):
    """Page 2 on 1-item universe returns empty items list."""
    client = populated_env["client"]

    res = client.get("/api/v1/ipos?page=2&page_size=20")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"] == []
