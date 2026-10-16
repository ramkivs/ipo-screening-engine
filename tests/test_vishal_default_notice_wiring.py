"""Regression: Vishal Nirmiti runtime resolution under DEFAULT config.

Defect (Windows application, commit 72e64c3): the automated end-to-end
test injected a RetainedNoticeProvider pointing at a temporary notice
directory, while the normal application built its resolver from
``build_resolver_from_env()`` -- which registered ZERO providers unless
``IPO_PRICE_BAND_NOTICE_DIR``/``IPO_PRICE_BAND_NOTICE_URLS`` were set.
An operator launching the app with only PYTHONPATH therefore got
``AWAITING_ISSUE_TERMS`` for every Vishal upload despite the retained
Price Band Notice being present in the repository.

These tests exercise the normal initialisation path: no resolver is
injected and no notice environment variables are set.
"""

from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import REPO_ROOT
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.issue_terms import build_resolver_from_env, default_retained_notice_dirs
from ipo_screening.pipeline import evaluate
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService

VISHAL_RHP_PDF = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"
RETAINED_FIXTURE = REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt"
GOLDEN_TS = datetime(2026, 10, 4, 19, 26, 1, tzinfo=timezone.utc)
NOTICE_ENV_VARS = (
    "IPO_PRICE_BAND_NOTICE_DIR",
    "IPO_PRICE_BAND_NOTICE_URLS",
    "IPO_ISSUE_TERMS_CACHE_DIR",
    "IPO_ISSUE_TERMS_CACHE_TTL_HOURS",
)


@pytest.fixture
def default_env(monkeypatch):
    """Ensure no notice configuration leaks in from the test process env."""
    for var in NOTICE_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


def test_packaged_retained_notice_is_the_retained_document():
    dirs = default_retained_notice_dirs()
    assert dirs, "packaged retained-notice directory must exist by default"
    packaged = dirs[0] / "vishal_nirmiti_price_band_notice.txt"
    assert packaged.is_file()
    assert (
        hashlib.sha256(packaged.read_bytes()).hexdigest()
        == hashlib.sha256(RETAINED_FIXTURE.read_bytes()).hexdigest()
    ), "packaged runtime notice must be the retained repository document, unaltered"


def test_default_resolver_discovers_vishal_notice_from_any_cwd(default_env, tmp_path):
    default_env.chdir(tmp_path)  # discovery must not depend on working directory
    resolver = build_resolver_from_env()
    outcome = resolver.resolve(
        company_name="VISHAL NIRMITI LIMITED",
        ipo_id="VISHAL-NIRMITI-LIMITED",
        missing_fields=["price_band_low", "price_band_high", "lot_size", "ofs"],
    )
    assert outcome.status == "RESOLVED"
    assert sorted(outcome.resolved_fields) == ["lot_size", "price_band_high", "price_band_low"]
    assert outcome.source_uri.endswith("vishal_nirmiti_price_band_notice.txt")
    values = {
        f: getattr(outcome.notice, f).value
        for f in ("price_band_low", "price_band_high", "lot_size")
    }
    assert values == {"price_band_low": 208.0, "price_band_high": 220.0, "lot_size": 68}


def test_default_resolver_does_not_resolve_unknown_issuer(default_env):
    resolver = build_resolver_from_env()
    outcome = resolver.resolve(
        company_name="UNLISTED UNKNOWN INDUSTRIES LIMITED",
        ipo_id="UNLISTED-UNKNOWN",
        missing_fields=["price_band_low", "price_band_high", "lot_size", "ofs"],
    )
    assert outcome.status != "RESOLVED"
    assert outcome.notice is None


def test_ingest_vishal_rhp_with_default_runtime_configuration(default_env, tmp_path, golden_input, config):
    """Full application path: PresentationService built WITHOUT an injected
    resolver must auto-resolve Vishal's terms from the retained notice."""
    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)
    baseline = evaluate(golden_input, config, mode="final", evaluation_datetime=GOLDEN_TS, store=store)
    historical_id = baseline.record.evaluation_id
    historical_hash = baseline.record.result_hash

    cfg = PresentationConfig(store_root=store_dir, config_dir=REPO_ROOT / "config")
    assert cfg.issue_terms_resolver is None  # normal default wiring, as in production
    client = TestClient(
        create_app(PresentationService(cfg)),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )

    payload = {"file": ("vishal_nirmiti_rhp.pdf", io.BytesIO(VISHAL_RHP_PDF.read_bytes()), "application/pdf")}
    res = client.post("/api/v1/ingest/document", files=payload, data={"mode": "final"})
    assert res.status_code == 201, f"default-configuration ingestion failed: {res.text}"
    body = res.json()
    assert body["issue_terms"]["status"] == "RESOLVED"

    record = store.read(body["evaluation_id"])
    issue = record["input_snapshot"]["input"]["issue"]
    assert (issue["price_band_low"], issue["price_band_high"], issue["lot_size"]) == (208, 220, 68)
    assert issue["ofs"] == 3300  # derived: OFS seller shares x cap price
    source_ids = {i.get("source_id", "") for i in record["evidence"]["evidence"]}
    assert any(s.startswith("SRC-PBN-") for s in source_ids)
    import json as _json

    assert "SRC-DERIVED" in _json.dumps(record)  # OFS formula provenance, not a source claim

    detail = client.get(f"/api/v1/evaluations/{body['evaluation_id']}")
    assert detail.status_code == 200
    assert detail.json()["result_hash"] == body["result_hash"]

    dup = client.post(
        "/api/v1/ingest/document",
        files={"file": ("vishal_nirmiti_rhp.pdf", io.BytesIO(VISHAL_RHP_PDF.read_bytes()), "application/pdf")},
        data={"mode": "final"},
    )
    assert dup.status_code == 200
    assert dup.json()["is_duplicate"] is True
    assert dup.json()["evaluation_id"] == body["evaluation_id"]

    # Historical evaluation is never rewritten by resolution or refresh.
    assert store.read(historical_id)["result_hash"] == historical_hash
