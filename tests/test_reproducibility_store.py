"""Reproducibility, evaluation-record immutability and the Excel projection.

Spec v1.5 s19, s21, s22, s23; execution prompt s16, s18.11-s18.13. The claims
under test:

* same inputs + snapshot + config + engine version => same result hash, across
  processes and regardless of dictionary ordering or wall-clock time;
* a stored evaluation is immutable and append-only, and a re-run with the same
  identity is refused rather than overwritten;
* the workbook is a *projection* only - it is rebuilt from the record, and the
  record is never rebuilt from the workbook.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from conftest import EVAL_AT, ENGINE_ROOT, GOLDEN_DIR, REPO_ROOT, run
from ipo_screening.errors import ImmutabilityError
from ipo_screening.evaluation import EvaluationStore, compute_preliminary_delta
from ipo_screening.excel import SHEET_ORDER, build_workbook, project
from ipo_screening.pipeline import evaluate, load_config


# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------


def test_same_inputs_produce_the_same_result_hash_twice(golden_input, config):
    first = run(golden_input, config)
    second = run(copy.deepcopy(golden_input), config)
    assert first.record.result_hash == second.record.result_hash


def test_result_hash_ignores_the_clock_while_the_snapshot_is_unchanged(golden_input, config):
    """Spec s19: the hash fingerprints the decision inputs, not the run time.

    The market blocks in the fixture are 16.6 hours old against a 24-hour
    freshness limit, so an evaluation taken three hours later sees *identical*
    material content. Wall-clock ages are audit detail and are excluded from
    the snapshot hashes, so the result hash must not move.
    """
    first = run(golden_input, config, at=EVAL_AT)
    later = run(golden_input, config, at=EVAL_AT + timedelta(hours=5))
    assert first.record.market_snapshot_hash == later.record.market_snapshot_hash
    assert first.record.peer_snapshot_hash == later.record.peer_snapshot_hash
    assert first.record.result_hash == later.record.result_hash
    assert first.record.score["final_score"] == later.record.score["final_score"]

    # The identity of the record does change: the id carries the timestamp,
    # and the age of each block is recorded for audit.
    assert first.record.evaluation_id != later.record.evaluation_id
    assert first.record.evaluation_timestamp != later.record.evaluation_timestamp
    ages = [b["age_hours"] for b in later.record.market_snapshot["blocks"]]
    assert all(age is not None for age in ages)
    assert later.record.market_snapshot["captured_at"] == "2026-10-05T17:00:00Z"


def test_result_hash_changes_when_the_snapshot_materially_changes(golden_input, config):
    """When data genuinely goes stale the hash must change, and say why."""
    fresh = run(golden_input, config, at=EVAL_AT)
    stale = run(golden_input, config, at=EVAL_AT + timedelta(hours=24))

    assert stale.record.market_snapshot_hash != fresh.record.market_snapshot_hash
    assert stale.record.result_hash != fresh.record.result_hash
    # The market block went stale, so the subscription criteria lose their data.
    assert stale.record.score["final_score"] != fresh.record.score["final_score"]
    statuses = {b["block"]: b["status"] for b in stale.record.market_snapshot["blocks"]}
    assert statuses["subscription"] == "STALE"


def test_result_hash_is_independent_of_key_order(golden_input, config):
    shuffled = dict(reversed(list(golden_input.items())))
    shuffled["issue"] = dict(reversed(list(golden_input["issue"].items())))
    assert run(shuffled, config).record.result_hash == run(golden_input, config).record.result_hash


def test_result_hash_is_stable_across_processes(config):
    """Spec s27: identical inputs must hash identically in a fresh interpreter."""
    script = (
        "import json, sys;"
        "from datetime import datetime, timezone;"
        "from ipo_screening.pipeline import evaluate, load_config;"
        "doc = json.load(open(sys.argv[1]));"
        "out = evaluate(doc, load_config(), evaluation_datetime=datetime(2026,10,5,12,0,0,tzinfo=timezone.utc));"
        "print(out.record.result_hash)"
    )
    expected = run(
        json.loads(GOLDEN_DIR.joinpath("input.json").read_text(encoding="utf-8")), config
    ).record.result_hash

    hashes = set()
    for seed in ("0", "1", "12345"):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ENGINE_ROOT)
        env["PYTHONHASHSEED"] = seed
        completed = subprocess.run(
            [sys.executable, "-c", script, str(GOLDEN_DIR / "input.json")],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
            timeout=180,
        )
        assert completed.returncode == 0, completed.stderr
        hashes.add(completed.stdout.strip())

    assert hashes == {expected}, hashes


def test_an_input_change_changes_the_result_hash(golden_input, config):
    baseline = run(golden_input, config).record.result_hash
    changed = json.loads(json.dumps(golden_input))
    changed["business"]["industry_cagr_pct"] = 11.5
    assert run(changed, config).record.result_hash != baseline


def test_a_config_change_changes_the_result_hash(golden_input, raw_config):
    baseline = run(golden_input, config_from(raw_config)).record.result_hash
    weakened = copy.deepcopy(raw_config)
    for criterion in weakened["modules"][0]["criteria"]:
        if criterion["id"] == "revenue_cagr":
            criterion["rule"]["bands"][0][2] = 6.0
    assert run(golden_input, config_from(weakened)).record.result_hash != baseline


def config_from(raw):
    from ipo_screening.config_validation import compile_config

    return compile_config(copy.deepcopy(raw))


def test_recorded_hashes_verify_against_the_stored_artifacts(golden_input, config, tmp_path):
    outcome, store = run_and_store(golden_input, config, tmp_path)
    report = store.verify_hashes(outcome.record.evaluation_id)
    assert report["result_hash_matches"] is True
    assert report["artifact_mismatches"] == []
    assert report["artifacts_verified"] == 6


def test_tampering_with_a_stored_artifact_is_detected(golden_input, config, tmp_path):
    outcome, store = run_and_store(golden_input, config, tmp_path)
    result_path = store.path_for(outcome.record.evaluation_id) / "result.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["score"]["final_score"] = 99.0
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    report = store.verify_hashes(outcome.record.evaluation_id)
    # The manifest records a hash per artifact, so any edit is detectable.
    assert report["result_hash_matches"] is True  # evaluation.json is untouched
    assert "result.json" in {m["artifact"] for m in report["artifact_mismatches"]}


def test_tampering_with_the_governing_record_is_detected(golden_input, config, tmp_path):
    """Editing evaluation.json must break the recomputed result hash."""
    outcome, store = run_and_store(golden_input, config, tmp_path)
    evaluation_path = store.path_for(outcome.record.evaluation_id) / "evaluation.json"
    payload = json.loads(evaluation_path.read_text(encoding="utf-8"))
    payload["score"]["final_score"] = 99.0
    evaluation_path.write_text(json.dumps(payload), encoding="utf-8")

    report = store.verify_hashes(outcome.record.evaluation_id)
    assert report["result_hash_matches"] is False
    assert "evaluation.json" in {m["artifact"] for m in report["artifact_mismatches"]}


# --------------------------------------------------------------------------
# Store: append-only and immutable
# --------------------------------------------------------------------------


def run_and_store(document, config, tmp_path, mode="final", workbook=True):
    store = EvaluationStore(tmp_path / "evaluations")
    outcome = evaluate(
        copy.deepcopy(document),
        config,
        mode=mode,
        evaluation_datetime=EVAL_AT,
        store=store,
        workbook_path=(tmp_path / "IPO_Screening_History.xlsx") if workbook else None,
    )
    return outcome, store


def test_store_refuses_to_overwrite_an_evaluation(golden_input, config, tmp_path):
    outcome, store = run_and_store(golden_input, config, tmp_path)
    with pytest.raises(ImmutabilityError):
        store.write(outcome.record)


def test_store_keeps_every_evaluation_for_the_same_issuer(golden_input, config, tmp_path):
    """Two runs with different timestamps coexist; neither is replaced."""
    store = EvaluationStore(tmp_path / "evaluations")
    first = evaluate(golden_input, config, mode="preliminary", evaluation_datetime=EVAL_AT, store=store)
    second = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT + timedelta(hours=2),
        store=store,
    )
    assert first.record.evaluation_id != second.record.evaluation_id
    stored = store.read_all(full=False)
    assert len(stored) == 2
    assert {r["ipo_id"] for r in stored} == {"VISHAL-NIRMITI-LIMITED"}
    modes = {str(record.get("evaluation_mode", "")).lower() for record in stored}
    assert modes == {"preliminary", "final"}


def test_latest_for_returns_the_newest_preliminary(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evaluations")
    evaluate(golden_input, config, mode="preliminary", evaluation_datetime=EVAL_AT, store=store)
    evaluate(golden_input, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    latest = store.latest_for("VISHAL-NIRMITI-LIMITED", "preliminary")
    assert latest is not None
    assert str(latest["evaluation_mode"]).lower() == "preliminary"


def test_records_are_write_once_on_disk(golden_input, config, tmp_path):
    outcome, store = run_and_store(golden_input, config, tmp_path)
    directory = store.path_for(outcome.record.evaluation_id)
    before = {p.name: p.stat().st_mtime_ns for p in sorted(directory.iterdir())}
    # Re-running with the same identity is refused, so nothing on disk moves.
    with pytest.raises(ImmutabilityError):
        store.write(outcome.record)
    after = {p.name: p.stat().st_mtime_ns for p in sorted(directory.iterdir())}
    assert before == after


def test_every_artifact_required_by_spec_21_is_written(golden_input, config, tmp_path):
    outcome, store = run_and_store(golden_input, config, tmp_path)
    directory = store.path_for(outcome.record.evaluation_id)
    for name in (
        "evaluation.json",
        "input.json",
        "evidence.json",
        "market.json",
        "peers.json",
        "result.json",
        "manifest.json",
    ):
        assert (directory / name).exists(), name


def test_record_read_back_equals_record_written(golden_input, config, tmp_path):
    outcome, store = run_and_store(golden_input, config, tmp_path)
    reread = store.read(outcome.record.evaluation_id)
    assert reread["result_hash"] == outcome.record.result_hash
    assert reread["score"]["final_score"] == outcome.record.score["final_score"]
    assert reread["verdict"]["verdict"] == outcome.record.verdict["verdict"]


def test_preliminary_delta_is_recorded_on_the_final_run(golden_input, config, tmp_path):
    """Spec s19: the final record carries the delta from the frozen preliminary."""
    store = EvaluationStore(tmp_path / "evaluations")
    preliminary = evaluate(
        golden_input, config, mode="preliminary", evaluation_datetime=EVAL_AT, store=store
    )
    final = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT + timedelta(hours=1),
        store=store,
    )
    delta = final.record.preliminary_delta
    assert delta is not None
    assert delta["preliminary_result_hash"] == preliminary.record.result_hash
    assert delta["final_result_hash"] == final.record.result_hash
    # A Preliminary and a Final of the same inputs differ: the retail/NII
    # penalty only applies once the issue has closed (Final mode).
    assert delta["score_delta"] == pytest.approx(final.record.score["final_score"]
                                                 - preliminary.record.score["final_score"])
    assert delta["preliminary_score"] == preliminary.record.score["final_score"]
    assert delta["final_verdict"] == final.record.verdict["verdict"]
    # The Preliminary is never modified by the Final run.
    stored_preliminary = store.read(preliminary.record.evaluation_id)
    assert stored_preliminary["result_hash"] == preliminary.record.result_hash
    assert stored_preliminary["preliminary_delta"] is None


def test_delta_detects_a_material_change(golden_input, config, tmp_path):
    store = EvaluationStore(tmp_path / "evaluations")
    evaluate(golden_input, config, mode="preliminary", evaluation_datetime=EVAL_AT, store=store)

    revised = json.loads(json.dumps(golden_input))
    revised["governance"]["going_concern_uncertainty"] = True
    final = evaluate(
        revised, config, mode="final", evaluation_datetime=EVAL_AT + timedelta(hours=1), store=store
    )
    delta = final.record.preliminary_delta
    assert delta["verdict_changed"] is True
    assert delta["preliminary_verdict"] == "INSUFFICIENT_DATA"
    assert delta["final_verdict"] == "AVOID"
    assert delta["knockout_status_changed"] is True
    assert delta["final_knockout_status"] == "TRIGGERED"


def test_preliminary_delta_uses_the_frozen_preliminary_not_a_rerun(golden_input, config, tmp_path):
    """The preliminary hash in the delta must equal the stored preliminary."""
    store = EvaluationStore(tmp_path / "evaluations")
    preliminary = evaluate(
        golden_input, config, mode="preliminary", evaluation_datetime=EVAL_AT, store=store
    )
    final = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=EVAL_AT + timedelta(hours=3),
        store=store,
    )
    stored = store.latest_for("VISHAL-NIRMITI-LIMITED", "preliminary")
    assert final.record.preliminary_delta["preliminary_result_hash"] == stored["result_hash"]
    assert stored["result_hash"] == preliminary.record.result_hash


# --------------------------------------------------------------------------
# Excel projection
# --------------------------------------------------------------------------


def test_workbook_has_exactly_the_fourteen_required_sheets(golden_input, config, tmp_path):
    """Spec s22: the workbook carries exactly the fourteen recommended sheets."""
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    workbook = build_workbook(outcome.record.to_dict())
    assert list(workbook.sheetnames) == list(SHEET_ORDER)
    assert len(SHEET_ORDER) == 14


def test_sheet_order_is_the_specified_order():
    """The sheet names and order are fixed by specification s22."""
    assert list(SHEET_ORDER) == [
        "IPO_Master",
        "Evaluations",
        "Module_Scores",
        "Criteria_Detail",
        "Knockouts",
        "Penalties",
        "Missing_Unverified",
        "Evidence",
        "Market_Snapshots",
        "Peer_Snapshots",
        "Post_Listing",
        "Backtest",
        "Config_Versions",
        "Run_Log",
    ]


def test_workbook_carries_the_golden_numbers(golden_input, config, tmp_path):
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    workbook = build_workbook(outcome.record.to_dict())
    flat = _flat(workbook["Evaluations"])
    assert flat["score"] == pytest.approx(35.0)
    assert flat["base_score"] == pytest.approx(38.0)
    assert flat["penalties_total"] == pytest.approx(-3.0)
    assert flat["lower_bound"] == pytest.approx(25.0)
    assert flat["upper_bound"] == pytest.approx(62.0)
    assert flat["verdict"] == "INSUFFICIENT_DATA"
    assert flat["confidence"] == "Low"
    assert flat["result_hash"] == outcome.record.result_hash


def test_module_scores_sheet_totals_100(golden_input, config, tmp_path):
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    rows = _rows(build_workbook(outcome.record.to_dict())["Module_Scores"])
    body = [r for r in rows[1:] if r and r[0]]
    assert len(body) == 6
    assert sum(float(r[6]) for r in body) == pytest.approx(100.0)


def test_criteria_detail_sheet_lists_every_criterion(golden_input, config, tmp_path):
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    workbook = build_workbook(outcome.record.to_dict())
    body = [r for r in _rows(workbook["Criteria_Detail"])[1:] if r and r[0]]
    expected = sum(len(m["criteria"]) for m in outcome.record.score["modules"])
    assert len(body) == expected
    # Every row states its criterion state, so UNKNOWN cannot be missed.
    states = {str(r[8]) for r in body}
    assert states <= {"SCORED", "UNKNOWN", "NOT_APPLICABLE"}


def test_every_displayed_number_traces_to_the_record(golden_input, config, tmp_path):
    """Spec s22/s23: the workbook is a projection, never an independent source.

    Every figure on the evaluator-facing sheets must be re-derivable from the
    frozen record; a number that exists only in the spreadsheet would mean the
    sheet had become a second source of truth.
    """
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    record = outcome.record
    workbook = build_workbook(record.to_dict())

    evaluations = _flat(workbook["Evaluations"])
    assert evaluations["score"] == pytest.approx(record.score["final_score"])
    assert evaluations["base_score"] == pytest.approx(record.score["base_score"])
    assert evaluations["lower_bound"] == pytest.approx(record.score["lower_bound"])
    assert evaluations["upper_bound"] == pytest.approx(record.score["upper_bound"])
    assert evaluations["confidence"] == record.score["confidence"]
    assert evaluations["verdict"] == record.verdict["verdict"]
    assert evaluations["penalties_total"] == pytest.approx(record.score["penalties_total"])
    assert evaluations["result_hash"] == record.result_hash
    assert evaluations["config_hash"] == record.config_hash
    assert evaluations["input_hash"] == record.input_snapshot_hash

    module_rows = [r for r in _rows(workbook["Module_Scores"])[1:] if r and r[0]]
    assert sum(float(r[5]) for r in module_rows) == pytest.approx(record.score["base_score"])

    penalty_rows = {
        str(r[3]): float(r[5]) for r in _rows(workbook["Penalties"])[1:] if r and r[0]
    }
    for item in record.score["penalties"]:
        # The record stores the penalty points; the sheet shows the same value.
        assert penalty_rows[item["id"]] == pytest.approx(item["points"])
        assert item["state"] in {"SCORED", "UNKNOWN"}


def test_evidence_sheet_lists_every_evidence_item(golden_input, config, tmp_path):
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    workbook = build_workbook(outcome.record.to_dict())
    rows = _rows(workbook["Evidence"])
    header = [str(h) for h in rows[0]]
    assert "page" in header and "quote" in header
    body = [r for r in rows[1:] if r and r[0]]
    assert len(body) == len(outcome.record.evidence["evidence"])
    assert all(r[header.index("page")] for r in body)


def test_market_and_peer_sheets_are_populated_from_the_frozen_snapshots(
    golden_input, config, tmp_path
):
    """These sheets are empty if the projection loses the snapshot artifacts."""
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    workbook = build_workbook(outcome.record.to_dict())
    market = [r for r in _rows(workbook["Market_Snapshots"])[1:] if r and r[0]]
    peers = [r for r in _rows(workbook["Peer_Snapshots"])[1:] if r and r[0]]
    assert market, "Market_Snapshots must reflect the frozen market snapshot"
    assert len(peers) == 2
    statuses = {str(r[6]) for r in peers}
    assert statuses == {"STALE"}


def test_missing_unverified_sheet_lists_the_open_gaps(golden_input, config, tmp_path):
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    workbook = build_workbook(outcome.record.to_dict())
    rows = _rows(workbook["Missing_Unverified"])
    header = [str(h) for h in rows[0]]
    body = [r for r in rows[1:] if r and r[0]]
    assert body
    items = {str(r[header.index("item")]) for r in body}
    assert "going_concern_uncertainty" in items
    assert "pe_vs_peers" in items
    categories = {str(r[header.index("category")]) for r in body}
    assert {"CRITERION", "KNOCKOUT"}.issubset(categories)


def test_knockouts_sheet_shows_the_tri_state(golden_input, config, tmp_path):
    outcome, _ = run_and_store(golden_input, config, tmp_path)
    workbook = build_workbook(outcome.record.to_dict())
    rows = _rows(workbook["Knockouts"])
    header = [str(h) for h in rows[0]]
    body = [r for r in rows[1:] if r and r[0]]
    states = {str(r[header.index("rule_id")]): str(r[header.index("state")]) for r in body}
    assert states["K1"] == "UNVERIFIED"
    assert states["K2"] == "CLEAR"
    assert all(v in {"CLEAR", "TRIGGERED", "UNVERIFIED"} for v in states.values())
    # The missing input is named on the row, not only in the status.
    k1 = next(r for r in body if str(r[header.index("rule_id")]) == "K1")
    assert "going_concern_uncertainty" in str(k1[header.index("missing_inputs")])


def test_workbook_bytes_are_deterministic(golden_input, config, tmp_path):
    """Spec s22: the same record must project to byte-identical output."""
    from ipo_screening.excel import workbook_bytes

    outcome, _ = run_and_store(golden_input, config, tmp_path)
    first = workbook_bytes([outcome.record.to_dict()])
    second = workbook_bytes([outcome.record.to_dict()])
    assert first == second


def test_workbook_is_generated_from_stored_records_not_hand_edited(
    golden_input, config, tmp_path
):
    """Spec s23: Excel is generated from the persisted records."""
    outcome, store = run_and_store(golden_input, config, tmp_path)
    workbook_path = tmp_path / "IPO_Screening_History.xlsx"
    result = project(store, workbook_path)
    assert workbook_path.exists()

    import openpyxl

    book = openpyxl.load_workbook(workbook_path)
    flat = _flat(book["Evaluations"])
    assert flat["result_hash"] == outcome.record.result_hash
    assert flat["score"] == pytest.approx(35.0)
    assert result.sheet_counts["Evaluations"] == 1


def test_two_evaluations_appear_as_two_rows(golden_input, config, tmp_path):
    """Historical rows accumulate; nothing replaces an earlier evaluation."""
    store = EvaluationStore(tmp_path / "evaluations")
    evaluate(golden_input, config, mode="preliminary", evaluation_datetime=EVAL_AT, store=store)
    evaluate(
        golden_input, config, mode="final", evaluation_datetime=EVAL_AT + timedelta(hours=1),
        store=store,
    )
    workbook_path = tmp_path / "IPO_Screening_History.xlsx"
    project(store, workbook_path)

    import openpyxl

    book = openpyxl.load_workbook(workbook_path)
    rows = [r for r in _rows(book["Evaluations"])[1:] if r and r[0]]
    assert len(rows) == 2
    assert {str(r[3]) for r in rows} == {"PRELIMINARY", "FINAL"}
    # One issuer, so the master sheet still shows a single row with a count of 2.
    master = _flat(book["IPO_Master"])
    assert master["evaluation_count"] == 2
    assert master["latest_mode"] == "FINAL"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _rows(sheet):
    return [list(row) for row in sheet.iter_rows(values_only=True)]


def _flat(sheet):
    """The first data row of an evaluation sheet, keyed by column header."""
    rows = _rows(sheet)
    header = [str(h) for h in rows[0]]
    body = [r for r in rows[1:] if r and r[0]]
    assert body, "the sheet has no data rows"
    return dict(zip(header, body[0]))
