"""Market-data absence and presentation integrity regression suite.

The persisted market snapshot already distinguishes FRESH / STALE /
MISSING blocks with reasons (frozen snapshots.py), and market criteria
resolve UNKNOWN with those reasons. The defect corrected here is
presentational: the presentation API exposed only the snapshot hash,
so the application could not show *why* market criteria were UNKNOWN,
and missing data could be misread as an observed negative signal.

This suite pins: block states reach the API unchanged; missing/stale
data stays UNKNOWN (never zero or negative); no qualification is
claimed for any source (A8-M/A9/A10 boundaries intact); historical
records and prior workstreams are untouched.
"""

from __future__ import annotations

import copy
import json

from fastapi.testclient import TestClient

from conftest import EVAL_AT, REPO_ROOT
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.pipeline import evaluate
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService
from ipo_screening.schema_validation import validate_schema

GOLDEN_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"


def _run(tmp_path, doc, config):
    store = EvaluationStore(tmp_path / "evals")
    out = evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    service = PresentationService(PresentationConfig(store_root=tmp_path / "evals", config_dir=REPO_ROOT / "config"))
    detail = service.get_evaluation_detail(out.record.evaluation_id)
    return out, store, service, detail


def _blocks(detail):
    return {b.block: b for b in detail.market_blocks}


def _module_f(detail):
    return {c.id: c for m in detail.score.modules if m.id == "F" for c in m.criteria}


def test_supplied_market_blocks_presented_as_fresh_with_source(golden_input, config, tmp_path):
    out, store, service, detail = _run(tmp_path, golden_input, config)
    blocks = _blocks(detail)
    assert set(blocks) == {"anchor", "subscription", "gmp", "regime"}
    for block in blocks.values():
        assert block.status == "FRESH"
        assert block.as_of is not None
        assert block.source_id == "MARKET-TRACKER"
    # Freshness is presented as recorded currency, never as a
    # qualification claim: the API carries no qualification field.
    blocks_json = json.dumps([b.model_dump() for b in detail.market_blocks]).lower()
    assert "qualified" not in blocks_json


def test_missing_market_blocks_presented_as_not_supplied(golden_input, config, tmp_path):
    doc = copy.deepcopy(golden_input)
    doc.pop("market", None)
    out, store, service, detail = _run(tmp_path, doc, config)
    blocks = _blocks(detail)
    assert all(b.status == "MISSING" for b in blocks.values())
    assert all(b.reason == "block not supplied" for b in blocks.values())

    criteria = _module_f(detail)
    for cid in ("gmp_trend", "market_regime", "overall_subscription", "nii_subscription"):
        assert criteria[cid].state == "UNKNOWN"
        assert criteria[cid].value is None  # never an implicit zero/negative signal
        assert "not usable" in (criteria[cid].reason or "")


def test_stale_market_blocks_presented_as_stale_not_negative(golden_input, config, tmp_path):
    doc = copy.deepcopy(golden_input)
    for block in doc["market"].values():
        if isinstance(block, dict):
            block["as_of"] = "2026-09-01T00:00:00Z"
    out, store, service, detail = _run(tmp_path, doc, config)
    blocks = _blocks(detail)
    assert all(b.status == "STALE" for b in blocks.values())
    assert all("staleness limit" in (b.reason or "") for b in blocks.values())
    criteria = _module_f(detail)
    assert criteria["gmp_trend"].state == "UNKNOWN"
    assert criteria["gmp_trend"].value is None


def test_market_blocks_reach_http_api(golden_input, config, tmp_path):
    out, store, service, detail = _run(tmp_path, golden_input, config)
    client = TestClient(create_app(service), base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"})
    res = client.get(f"/api/v1/evaluations/{out.record.evaluation_id}")
    assert res.status_code == 200
    blocks = {b["block"]: b for b in res.json()["market_blocks"]}
    assert blocks["gmp"]["status"] == "FRESH"
    assert blocks["gmp"]["source_id"] == "MARKET-TRACKER"


def test_historical_record_not_rewritten_by_projection(golden_input, config, tmp_path):
    out, store, service, detail = _run(tmp_path, golden_input, config)
    assert out.record.result_hash == GOLDEN_HASH
    before = json.dumps(store.read(out.record.evaluation_id), sort_keys=True)
    service.get_evaluation_detail(out.record.evaluation_id)
    assert json.dumps(store.read(out.record.evaluation_id), sort_keys=True) == before


def test_prior_workstreams_intact(golden_input):
    # D-PEER-1: empty peers valid, no synthetic entity.
    doc = copy.deepcopy(golden_input)
    doc["peers"] = []
    assert not [f for f in validate_schema(doc) if "peer" in str(f.location)]
    # Workstream 2: evidence projection still distinguishes processing
    # claims (covered fully in test_workstream2_evidence_presentation).
    from ipo_screening.extraction.interfaces import RawExtraction

    ev = RawExtraction(field_path="financials.periods", quote="Parsed 3 financial periods", quote_is_processing=True).to_evidence_dict("RHP-X")
    assert "quote" not in ev and ev["note"].startswith("PROCESSING_SUMMARY:")
