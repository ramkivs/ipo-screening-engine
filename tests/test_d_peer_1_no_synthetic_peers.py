"""D-PEER-1 regression suite: no synthetic peer fallback.

Approved correction (user decision D-PEER-1): when no genuine peer
data can be extracted, the canonical input carries ``peers: []``
(permitted by the amended v1.5 input contract) instead of the invented
entity "Generic Listed Peer Ltd". Peer-relative metrics keep their
existing UNKNOWN semantics; genuine peers and historical records are
unchanged.
"""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import pytest

from conftest import EVAL_AT, REPO_ROOT
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import RawExtraction
from ipo_screening.pipeline import evaluate, load_config
from ipo_screening.post_listing.v16_implementation import verify_frozen_core
from ipo_screening.schema_validation import validate_schema

GOLDEN_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
PLACEHOLDER = {"name": "Generic Listed Peer Ltd", "listed_years": 5, "business_match": "partial"}
GENUINE_PEER = {"name": "Banaras Beads Limited", "business_match": "match", "listed_years": 12, "pe": 44.31, "as_of": "2026-09-28"}


def _doc():
    return SimpleNamespace(
        source_id="RHP-TEST-000",
        company_name="Test Widgets Limited",
        to_source_ref_dict=lambda: {"source_id": "RHP-TEST-000", "source_type": "RHP", "uri": "test.pdf"},
    )


def _builder(extractions=(), reference_base=None):
    return CanonicalInputBuilder(
        doc=_doc(), extractions=list(extractions), reference_base=reference_base, allow_fixture_fallbacks=False
    )


def _peer_metrics(record_dict):
    metrics = record_dict["derived_metrics"]["metrics"]
    items = metrics.items() if isinstance(metrics, dict) else [(m.get("name"), m) for m in metrics]
    return {k: v for k, v in items if "premium" in str(k)}


# 1-2. Builder emits [] and the amended contract accepts it ---------------

def test_builder_emits_empty_peers_when_nothing_extracted():
    out = _builder().build()
    assert out["peers"] == []
    assert "Generic Listed Peer Ltd" not in json.dumps(out)


def test_empty_peers_pass_schema_validation(golden_input):
    doc = copy.deepcopy(golden_input)
    doc["peers"] = []
    findings = validate_schema(doc)
    assert not [f for f in findings if "peer" in str(f.location)], findings


# 3. Peer-object validation is not weakened -------------------------------

def test_invalid_peer_objects_still_rejected(golden_input):
    for bad in ([{}], [{"name": 123}], [{"name": "X", "pe": "not-a-number"}], [{"name": "X", "unexpected": 1}]):
        doc = copy.deepcopy(golden_input)
        doc["peers"] = bad
        findings = validate_schema(doc)
        assert [f for f in findings if "peer" in str(f.location)], f"invalid peer accepted: {bad}"


# 4-5. Genuine peers are retained -----------------------------------------

def test_genuine_extracted_peers_retained():
    extraction = RawExtraction(field_path="peers", candidate_value=[GENUINE_PEER])
    out = _builder(extractions=[extraction]).build()
    assert out["peers"] == [GENUINE_PEER]


def test_genuine_reference_peers_retained():
    out = _builder(reference_base={"peers": [GENUINE_PEER]}).build()
    assert out["peers"] == [GENUINE_PEER]


# 6-9. Empty peers: UNKNOWN metrics, no fabrication, evaluation proceeds --

def test_empty_peers_unknown_metrics_and_no_synthetic_entity(golden_input, config, tmp_path):
    doc = copy.deepcopy(golden_input)
    doc["peers"] = []
    out = evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT)
    record = out.record.to_dict()

    for name, metric in _peer_metrics(record).items():
        assert metric["state"] == "UNKNOWN", f"{name} not UNKNOWN with no peers: {metric}"
    assert record["peer_snapshot"]["valid_count"] == 0
    assert record["peer_snapshot"]["observations"] == []
    assert "Generic Listed Peer Ltd" not in json.dumps(record)

    # Persisting works and stores the honest empty peer set.
    store = EvaluationStore(tmp_path / "evals")
    store.write(out.record)
    persisted = store.read(out.record.evaluation_id)
    assert persisted["input_snapshot"]["input"]["peers"] == []
    assert "Generic Listed Peer Ltd" not in json.dumps(persisted)


def test_empty_peers_score_matches_placeholder_era_behaviour(golden_input, config):
    """Missing peers must not become zero or favourable: the empty-list
    outcome equals the old placeholder outcome (peer points unavailable)."""
    empty = copy.deepcopy(golden_input)
    empty["peers"] = []
    placeholder = copy.deepcopy(golden_input)
    placeholder["peers"] = [PLACEHOLDER]
    out_empty = evaluate(empty, config, mode="final", evaluation_datetime=EVAL_AT)
    out_placeholder = evaluate(placeholder, config, mode="final", evaluation_datetime=EVAL_AT)
    assert out_empty.score.final_score == out_placeholder.score.final_score
    assert out_empty.score.verdict == out_placeholder.score.verdict
    assert out_empty.score.confidence == out_placeholder.score.confidence


# 10-13. Genuine behaviour, golden hash, history, reproducibility ---------

def test_genuine_peer_golden_evaluation_unchanged(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evals")
    out = evaluate(golden_input, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    assert out.record.result_hash == GOLDEN_HASH
    before = store.read(out.record.evaluation_id)

    # A subsequent no-peer evaluation must not rewrite the historical one.
    doc = copy.deepcopy(golden_input)
    doc["peers"] = []
    doc["ipo_id"] = "OTHER-IPO"
    evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    assert store.read(out.record.evaluation_id) == before


def test_empty_peers_evaluation_is_reproducible(golden_input, config):
    doc = copy.deepcopy(golden_input)
    doc["peers"] = []
    first = evaluate(doc, config, mode="final", evaluation_datetime=EVAL_AT)
    second = evaluate(copy.deepcopy(doc), config, mode="final", evaluation_datetime=EVAL_AT)
    assert first.record.result_hash == second.record.result_hash


# 14-15. Fixture fallbacks stay off; frozen core untouched -----------------

def test_builder_fixture_fallback_protections_intact():
    out = _builder().build()
    assert out["issue"]["price_band_low"] is None
    assert out["issue"]["lot_size"] is None


def test_frozen_core_unchanged():
    ok, checks = verify_frozen_core(REPO_ROOT)
    assert ok, checks
