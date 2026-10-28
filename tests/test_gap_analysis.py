"""Read-only Layer 2A gap-analysis regression coverage."""
from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import ENGINE_ROOT, GOLDEN_DIR, REPO_ROOT
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.gap_analysis import build_gap_report
from ipo_screening.pipeline import evaluate, load_config

CLI = ENGINE_ROOT / "tools" / "ipo_screen.py"


class FakeStore:
    def __init__(self, record, *, valid=True):
        self.root = Path("/read-only/fake-store")
        self.record = deepcopy(record)
        self.valid = valid

    def exists(self, evaluation_id):
        return evaluation_id == self.record.get("evaluation_id")

    def verify_hashes(self, evaluation_id):
        return {
            "result_hash_matches": self.valid,
            "artifact_mismatches": [] if self.valid else [{"artifact": "input.json"}],
        }

    def read_full(self, evaluation_id):
        return deepcopy(self.record)

    def read_artifact(self, evaluation_id, name):
        assert name == "manifest"
        return {"artifacts": {"input.json": "abc"}}


def minimal_record(gaps):
    return {
        "evaluation_id": "IPO-20261028-final-abcdef12",
        "ipo_id": "IPO",
        "company_name": "Issuer Limited",
        "evaluation_mode": "FINAL",
        "evaluation_timestamp": "2026-10-28T12:00:00Z",
        "engine_version": "1.5.0",
        "spec_version": "1.5",
        "config_hash": "c",
        "input_snapshot_hash": "i",
        "source_manifest_hash": "s",
        "market_snapshot_hash": "m",
        "peer_snapshot_hash": "p",
        "result_hash": "r",
        "missing_unverified": gaps,
        "score": {
            "modules": [{
                "module_id": "D", "name": "Valuation", "criteria": [{
                    "criterion_id": "peer_pe", "state": "UNKNOWN", "max": 5,
                    "reason": "no valid peer",
                }],
            }],
        },
        "evidence": {"sources": [{"source_id": "RHP-1", "source_type": "RHP"}]},
    }


def test_complete_baseline_has_deterministic_empty_report():
    store = FakeStore(minimal_record([]))
    first = build_gap_report(store, store.record["evaluation_id"])
    second = build_gap_report(store, store.record["evaluation_id"])
    assert first == second
    assert first["summary"] == {
        "gap_count": 0, "complete": True, "numeric_score_effect_gap_count": 0
    }


def test_unknown_criterion_uses_only_stored_reason_module_and_points():
    gap = {"category": "CRITERION", "item": "peer_pe", "state": "UNKNOWN",
           "detail": "no valid peer", "points_affected": 5}
    report = build_gap_report(FakeStore(minimal_record([gap])), "IPO-20261028-final-abcdef12")
    item = report["gaps"][0]
    assert item["reason"] == "no valid peer"
    assert item["module_id"] == "D"
    assert item["score_effect"]["connection"] == "ESTABLISHED_BY_BASELINE"
    assert item["score_effect"]["points_affected"] == 5


@pytest.mark.parametrize("state", ["STALE", "UNUSABLE", "UNVERIFIED", "UNSUPPORTED"])
def test_noncriterion_status_has_no_invented_score_effect(state):
    gap = {"category": "PEER", "item": "Peer Ltd", "state": state,
           "detail": None, "points_affected": None}
    report = build_gap_report(FakeStore(minimal_record([gap])), "IPO-20261028-final-abcdef12")
    item = report["gaps"][0]
    assert item["reason_availability"] == "UNDETERMINED"
    assert item["evidence_references"] == []
    assert item["score_effect"]["connection"] == "NOT_ESTABLISHED_BY_AVAILABLE_ARTIFACTS"


def test_invalid_identity_and_integrity_are_refused():
    store = FakeStore(minimal_record([]))
    with pytest.raises(FileNotFoundError):
        build_gap_report(store, "OTHER")
    store.valid = False
    with pytest.raises(ValueError, match="integrity verification"):
        build_gap_report(store, store.record["evaluation_id"])


def test_cli_writes_separate_report_without_mutating_store(tmp_path):
    document = json.loads((GOLDEN_DIR / "input.json").read_text(encoding="utf-8"))
    store_path = tmp_path / "evaluations"
    store = EvaluationStore(store_path)
    outcome = evaluate(
        document,
        load_config(),
        mode="final",
        evaluation_datetime=datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc),
        store=store,
    )
    evaluation_id = outcome.record.evaluation_id
    evaluation_dir = store.path_for(evaluation_id)
    before = {p.name: p.read_bytes() for p in evaluation_dir.iterdir() if p.is_file()}
    before_ids = store.list_evaluations()
    output = tmp_path / "reports" / "gap.json"

    completed = subprocess.run(
        [sys.executable, str(CLI), "gap-report", evaluation_id,
         "--store", str(store_path), "--output", str(output)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["baseline"]["evaluation_id"] == evaluation_id
    assert report["baseline"]["integrity_verified"] is True
    assert report["observational_only"] is True
    assert store.list_evaluations() == before_ids
    assert {p.name: p.read_bytes() for p in evaluation_dir.iterdir() if p.is_file()} == before


def test_cli_refuses_output_inside_baseline_and_existing_output(tmp_path):
    store = tmp_path / "evaluations"
    evaluation_id = "EVAL"
    (store / evaluation_id).mkdir(parents=True)
    inside = store / evaluation_id / "gap.json"
    first = subprocess.run(
        [sys.executable, str(CLI), "gap-report", evaluation_id,
         "--store", str(store), "--output", str(inside)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert first.returncode == 2
    assert "outside the immutable evaluation directory" in first.stderr

    existing = tmp_path / "existing.json"
    existing.write_text("{}", encoding="utf-8")
    second = subprocess.run(
        [sys.executable, str(CLI), "gap-report", evaluation_id,
         "--store", str(store), "--output", str(existing)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert second.returncode == 2
    assert existing.read_text(encoding="utf-8") == "{}"
