"""Focused acceptance coverage for the A15 canonical evaluation-record v1."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import unicodedata
from pathlib import Path

import pytest

from conftest import EVAL_AT, run
from ipo_screening.connectors.adapters import GmpSignalAdapter
from ipo_screening.connectors.coordinator import ConnectorCoordinator
from ipo_screening.errors import SchemaValidationError
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.evaluation_record import (
    CANONICALIZATION_ID,
    RECORD_ARTIFACT_NAME,
    EvaluationRecordV1Error,
    build_evaluation_record_v1,
    serialize_evaluation_record_v1,
    validate_evaluation_record_v1,
)
from ipo_screening.hashing import canonical_json, sha256_of


MODES = (
    "preliminary",
    "final",
    "post_listing_1w",
    "post_listing_1m",
    "post_listing_6m",
)


def _safe_ordinary_input(document):
    """Supply known non-triggering knockout inputs while preserving v1.5 policy."""
    result = copy.deepcopy(document)
    result["governance"]["auditor_opinion"] = "unqualified"
    result["governance"]["going_concern_uncertainty"] = False
    result["governance"]["sebi_ed_action_active"] = False
    result["governance"]["rpt_pct_of_revenue_growth"] = 1.0
    result["financials"]["contingent_liabilities_unquantified"] = False
    return result


def test_projected_record_uses_draft_2020_12_closed_a15_envelope(golden_input, config):
    outcome = run(golden_input, config)
    document = build_evaluation_record_v1(outcome.record)
    validate_evaluation_record_v1(document)

    schema_path = Path(__file__).resolve().parents[1] / "schema" / "ipo-evaluation-record.v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "urn:ipo-screening-engine:ipo-evaluation-record:1.1.0"
    assert document["record_schema_version"] == "1.1.0"
    assert set(document) == set(schema["required"])
    assert document["evaluation"]["mode"] == "FINAL"
    assert document["evaluation"]["validation"]["schema_status"] == "PASSED"
    assert document["snapshots"]["artifact_refs"] == {
        "input": "input.json",
        "evidence": "evidence.json",
        "market": "market.json",
        "peers": "peers.json",
        "result": "result.json",
        "manifest": "manifest.json",
    }
    assert document["adjudications"] == []

    rhp = next(item for item in document["sources"] if item["source_id"] == "RHP-VISHAL-NIRMITI")
    retrieval = next(item for item in rhp["timestamps"] if item["kind"] == "LOCAL_RETRIEVED_AT")
    assert retrieval["source_text"] == "2026-10-05T06:30:00Z"
    assert retrieval["normalized_utc"] == "2026-10-05T06:30:00Z"
    assert all(item.get("source_text") != "2026-09-24T00:00:00Z" for item in rhp["timestamps"])
    unresolved_source_time = next(
        item
        for item in document["evaluation"]["validation"]["findings"]
        if item["code"] == "LEGACY_SOURCE_TIMESTAMP_UNCLASSIFIED"
        and item.get("field_path", "").endswith("/source_timestamp")
    )
    assert unresolved_source_time["field_path"].startswith("evidence.json#/evidence/sources/")


def test_v1_1_schema_accepts_legacy_v1_0_terminal_records(golden_input, config):
    legacy_record = build_evaluation_record_v1(
        run(golden_input, config, mode="preliminary").record
    )
    legacy_record["record_schema_version"] = "1.0.0"
    validate_evaluation_record_v1(legacy_record)
    assert legacy_record["result"]["outcome_resolution"]["state"] == "TERMINAL"


def test_field_values_preserve_raw_unknown_and_unit_normalized_values(golden_input, config):
    outcome = run(golden_input, config)
    document = build_evaluation_record_v1(outcome.record)
    by_path = {item["field_path"]: item for item in document["field_values"]}

    revenue_path = "/input/financials/periods/2/revenue"
    revenue = by_path[revenue_path]
    assert revenue["value_state"] == "VALUE"
    assert revenue["raw_value"] == golden_input["financials"]["periods"][2]["revenue"]
    assert revenue["normalized_value"] == outcome.record.input_snapshot["periods"][2]["revenue"]
    assert revenue["raw_unit"] == "INR_LAKHS"
    assert revenue["normalized_unit"] == "INR_CRORES"
    assert revenue["normalization"]["kind"] == "NORMALIZED"
    assert revenue["normalization"]["formula_id"] == "UNIT_TO_CRORE"
    assert revenue["verification_status"] == "UNVERIFIED"
    assert revenue["qualification_status"] == "PENDING"
    assert revenue["source_observation_ids"]
    assert revenue["evidence_refs"]

    missing_path = "/input/governance/going_concern_uncertainty"
    missing = by_path[missing_path]
    assert missing["value_state"] == "UNKNOWN"
    assert "raw_value" not in missing and "normalized_value" not in missing
    assert missing["reason"]["code"] == "MISSING"
    assert missing["verification_status"] == "UNVERIFIED"
    assert missing["qualification_status"] == "PENDING"
    observation = next(
        item for item in document["observations"] if item["field_path"] == missing_path
    )
    assert observation["value_state"] == "UNKNOWN"
    assert "raw_value" not in observation
    assert missing["evidence_refs"] == observation["evidence_refs"]


def test_ordinary_outcome_copies_configured_v15_verdict_and_keeps_score_verdict_distinct(
    golden_input, config
):
    outcome = run(_safe_ordinary_input(golden_input), config, mode="preliminary")
    document = build_evaluation_record_v1(outcome.record)
    result = document["result"]

    assert all(item["state"] != "TRIGGERED" for item in result["knockouts"])
    assert all(item["state"] != "UNVERIFIED" for item in result["knockouts"])
    assert result["critical_safety"]["status"] == "COMPLETE"
    assert any(item["value_state"] == "UNKNOWN" for item in document["field_values"])
    assert result["outcome_resolution"] == {"state": "TERMINAL"}
    assert result["final_outcome"] == outcome.record.verdict["verdict"]
    assert result["score_verdict"]["value"] == outcome.record.score["verdict"]
    assert result["score_verdict"]["uncertain"] == outcome.record.score["verdict_uncertain"]
    if result["score_verdict"]["uncertain"]:
        assert any(item["code"] == "VERDICT_UNCERTAIN" for item in result["diagnostics"])
        assert result["final_outcome"] == outcome.record.verdict["verdict"]


def test_a9_missing_gmp_blocks_final_despite_generic_hash_and_persists_deterministically(
    golden_input, config, tmp_path
):
    document = _safe_ordinary_input(golden_input)
    document["market"].pop("gmp", None)

    first_root = tmp_path / "first-store"
    first_root.mkdir()
    first_store = EvaluationStore(first_root)
    first = run(copy.deepcopy(document), config, store=first_store)
    first_path = first_store.path_for(first.record.evaluation_id) / RECORD_ARTIFACT_NAME
    projected = first_store.read_artifact(
        first.record.evaluation_id, RECORD_ARTIFACT_NAME[:-5]
    )
    result = projected["result"]

    assert first.record.evaluation_mode == "FINAL"
    assert result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert result["outcome_resolution"]["reason"]["code"] == "MISSING"
    assert "final_outcome" not in result
    assert result["score_verdict"]["value"] == first.record.score["verdict"]
    assert any(
        item["status"] == "MISSING"
        for item in first.record.market_snapshot["blocks"]
        if item["block"] == "gmp"
    )

    market_digest = next(
        item
        for item in projected["integrity"]["digests"]
        if item["digest_id"] == "market-snapshot"
    )
    assert market_digest["origin"] == "LOCAL_COMPUTED"
    assert market_digest["subject_ref"] == "market.json#snapshot.hash_payload"
    assert market_digest["digest_value"] == first.record.market_snapshot_hash
    assert "market-snapshot" not in result["outcome_resolution"]["reason"]["evidence_refs"]

    reason_refs = set(result["outcome_resolution"]["reason"]["evidence_refs"])
    evidence_by_id = {item["evidence_id"]: item for item in projected["evidence"]}
    assert reason_refs
    assert reason_refs.issubset(evidence_by_id)
    assert any(
        evidence_by_id[ref]["artifact_ref"] == "market.json"
        and evidence_by_id[ref]["extraction_method"] == "DERIVED"
        for ref in reason_refs
    )
    assert any(
        item["code"] == "A9_GMP_FINAL_WITHHELD"
        and set(item["evidence_refs"]) == reason_refs
        for item in result["diagnostics"]
    )
    assert any(
        item["code"] == "A9_GMP_FINAL_WITHHELD"
        for item in projected["evaluation"]["validation"]["findings"]
    )
    verification = first_store.verify_hashes(first.record.evaluation_id)
    assert verification["result_hash_matches"] is True
    assert verification["artifact_mismatches"] == []

    second_root = tmp_path / "second-store"
    second_root.mkdir()
    second_store = EvaluationStore(second_root)
    second = run(copy.deepcopy(document), config, store=second_store)
    second_path = second_store.path_for(second.record.evaluation_id) / RECORD_ARTIFACT_NAME
    assert second.record.evaluation_id == first.record.evaluation_id
    assert second.record.result_hash == first.record.result_hash
    assert second_path.read_bytes() == first_path.read_bytes()


def test_a9_unqualified_connector_gmp_hash_stays_blocked_and_preliminary_is_unchanged(
    golden_input, config
):
    adapter = GmpSignalAdapter()
    snapshot = adapter.normalize(
        {
            "as_of": EVAL_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "retrieval_timestamp": EVAL_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "gmp_rupees": 42.0,
            "gmp_pct": 15.91,
            "trend": "flat",
        },
        reference_time=EVAL_AT,
        snapshot_id="A9-SYNTHETIC-GMP",
    )
    assert snapshot.verification == "UNVERIFIED"
    assert snapshot.raw_source_hash

    market_payload, _peer_payload, connector_sources = ConnectorCoordinator(
        adapters=[adapter]
    ).reconcile_snapshots([snapshot], reference_time=EVAL_AT)
    document = _safe_ordinary_input(golden_input)
    document["market"]["gmp"] = market_payload["gmp"]
    # The v1.5 SourceRef schema is closed; the connector's human note is not a
    # source-qualification field and is intentionally not promoted into it.
    document["_sources"].extend(
        {key: value for key, value in source.items() if key != "note"}
        for source in connector_sources
    )

    final = run(copy.deepcopy(document), config)
    projected = build_evaluation_record_v1(final.record)
    result = projected["result"]
    assert result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert result["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"
    assert "final_outcome" not in result
    assert result["score_verdict"]["value"] == final.record.score["verdict"]

    gmp_source_id = market_payload["gmp"]["source_id"]
    gmp_source = next(item for item in projected["sources"] if item["source_id"] == gmp_source_id)
    assert gmp_source["digest_refs"]
    raw_hash_digest = next(
        item
        for item in projected["integrity"]["digests"]
        if item["digest_id"] == gmp_source["digest_refs"][0]
    )
    assert raw_hash_digest["origin"] == "LEGACY_UNRESOLVED"
    assert raw_hash_digest["subject_kind"] == "LEGACY_UNSPECIFIED"

    market_digest = next(
        item
        for item in projected["integrity"]["digests"]
        if item["digest_id"] == "market-snapshot"
    )
    assert market_digest["origin"] == "LOCAL_COMPUTED"
    assert market_digest["digest_value"] == final.record.market_snapshot_hash

    # The gate is Final-only: the same unqualified observation does not change
    # Preliminary's existing A7/A15 terminal-outcome behavior.
    preliminary = run(copy.deepcopy(document), config, mode="preliminary")
    preliminary_record = build_evaluation_record_v1(preliminary.record)
    assert preliminary_record["result"]["outcome_resolution"] == {"state": "TERMINAL"}
    assert preliminary_record["result"]["final_outcome"] == preliminary.record.verdict["verdict"]
    assert all(
        item["code"] != "A9_GMP_FINAL_WITHHELD"
        for item in preliminary_record["result"]["diagnostics"]
    )


def test_a9_invalid_gmp_rejects_final_before_any_store_write(golden_input, config, tmp_path):
    document = _safe_ordinary_input(golden_input)
    document["market"]["gmp"]["trend"] = "unsupported-value"
    store = EvaluationStore(tmp_path / "invalid-gmp-store")

    with pytest.raises(SchemaValidationError):
        run(document, config, store=store)
    assert store.list_evaluations() == []


def test_a9_stale_generic_gmp_block_remains_nonterminal(golden_input, config):
    document = _safe_ordinary_input(golden_input)
    document["market"]["gmp"]["as_of"] = "2026-10-03T12:00:00Z"
    outcome = run(document, config)
    projected = build_evaluation_record_v1(outcome.record)
    result = projected["result"]
    gmp_block = next(
        item
        for item in outcome.record.market_snapshot["blocks"]
        if item["block"] == "gmp"
    )

    assert gmp_block["status"] == "STALE"
    assert result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert result["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"
    assert (
        "generic market classification is STALE"
        in result["outcome_resolution"]["reason"]["message"]
    )
    assert "final_outcome" not in result


def test_a9_final_gate_precedes_triggered_knockout_and_critical_safety(
    golden_input, config
):
    triggered = _safe_ordinary_input(golden_input)
    triggered["market"].pop("gmp", None)
    triggered["governance"]["going_concern_uncertainty"] = True
    triggered_result = build_evaluation_record_v1(run(triggered, config).record)["result"]
    assert any(item["state"] == "TRIGGERED" for item in triggered_result["knockouts"])
    assert triggered_result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert triggered_result["outcome_resolution"]["reason"]["code"] == "MISSING"
    assert "final_outcome" not in triggered_result

    incomplete = copy.deepcopy(golden_input)
    incomplete["market"].pop("gmp", None)
    incomplete_result = build_evaluation_record_v1(run(incomplete, config).record)["result"]
    assert incomplete_result["critical_safety"]["status"] == "INCOMPLETE"
    assert incomplete_result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert incomplete_result["outcome_resolution"]["reason"]["code"] == "MISSING"
    assert "final_outcome" not in incomplete_result


def test_a7_verified_trigger_and_critical_safety_precedence(golden_input, config):
    triggered_input = copy.deepcopy(golden_input)
    triggered_input["governance"]["going_concern_uncertainty"] = True
    outcome = run(triggered_input, config, mode="preliminary")
    result = build_evaluation_record_v1(outcome.record)["result"]
    assert any(item["state"] == "TRIGGERED" for item in result["knockouts"])
    assert result["outcome_resolution"]["state"] == "TERMINAL"
    assert result["final_outcome"] == "AVOID"
    assert result["critical_safety"]["status"] == "COMPLETE"

    missing_critical = run(golden_input, config, mode="preliminary")
    missing_result = build_evaluation_record_v1(missing_critical.record)["result"]
    assert missing_result["critical_safety"]["status"] == "INCOMPLETE"
    assert missing_result["final_outcome"] == "INSUFFICIENT_DATA"
    assert missing_result["outcome_resolution"]["state"] == "TERMINAL"


def test_a7_unverified_only_is_nonterminal_and_omits_final_outcome(golden_input, config):
    document = _safe_ordinary_input(golden_input)
    # K6 remains UNVERIFIED; the other known critical and knockout inputs are
    # sufficient to exercise A7's unverified-only representation.
    document["governance"]["rpt_pct_of_revenue_growth"] = None
    outcome = run(document, config, mode="preliminary")
    projected = build_evaluation_record_v1(outcome.record)
    result = projected["result"]

    assert result["critical_safety"]["status"] == "COMPLETE"
    assert any(item["state"] == "UNVERIFIED" for item in result["knockouts"])
    assert all(item["state"] != "TRIGGERED" for item in result["knockouts"])
    assert result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert result["outcome_resolution"]["reason"]["code"] == "UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT"
    assert "final_outcome" not in result
    evidence_ids = {item["evidence_id"] for item in projected["evidence"]}
    unresolved_refs = set(result["outcome_resolution"]["reason"]["evidence_refs"])
    assert unresolved_refs
    assert unresolved_refs.issubset(evidence_ids)
    assert unresolved_refs.issubset(
        {
            ref
            for item in result["knockouts"]
            if item["state"] == "UNVERIFIED"
            for ref in item["evidence_refs"]
        }
    )


def test_record_serialization_is_stable_utf8_lf_and_separate_from_hash_grammar(
    golden_input, config
):
    document = build_evaluation_record_v1(run(golden_input, config).record)
    document["record"]["company_name"] = "IPO e\u0301vidence"
    assert unicodedata.normalize("NFC", document["record"]["company_name"]) != document["record"]["company_name"]

    first = serialize_evaluation_record_v1(document)
    reordered = dict(reversed(list(document.items())))
    second = serialize_evaluation_record_v1(reordered)
    assert first == second
    assert first.endswith("\n")
    assert "\r" not in first
    assert "IPO e\u0301vidence" in first
    assert json.loads(first) == document
    assert first != canonical_json(document)

    invalid = copy.deepcopy(document)
    invalid["result"]["score"]["final_score"] = float("nan")
    with pytest.raises(EvaluationRecordV1Error, match="non-finite"):
        serialize_evaluation_record_v1(invalid)


def test_terminal_conditionals_fail_closed(golden_input, config):
    document = build_evaluation_record_v1(
        run(golden_input, config, mode="preliminary").record
    )
    missing_final = copy.deepcopy(document)
    missing_final["result"].pop("final_outcome", None)
    with pytest.raises(SchemaValidationError):
        validate_evaluation_record_v1(missing_final)

    nonterminal_with_final = copy.deepcopy(document)
    nonterminal_with_final["result"]["outcome_resolution"] = {
        "state": "NONTERMINAL_UNRESOLVED",
        "reason": {
            "code": "UNVERIFIED_KNOCKOUT_NO_SAFE_RESULT",
            "evidence_refs": [document["evidence"][0]["evidence_id"]],
        },
    }
    nonterminal_with_final["result"]["final_outcome"] = "AVOID"
    with pytest.raises(SchemaValidationError):
        validate_evaluation_record_v1(nonterminal_with_final)

    a9_reason_ref = document["evidence"][0]["evidence_id"]
    a9_nonfinal = copy.deepcopy(document)
    a9_nonfinal["result"]["outcome_resolution"] = {
        "state": "NONTERMINAL_UNRESOLVED",
        "reason": {
            "code": "MISSING",
            "message": "A9 test reason.",
            "evidence_refs": [a9_reason_ref],
        },
    }
    a9_nonfinal["result"].pop("final_outcome", None)
    a9_nonfinal["result"]["diagnostics"].append(
        {
            "code": "A9_GMP_FINAL_WITHHELD",
            "message": "A9 test reason.",
            "evidence_refs": [a9_reason_ref],
        }
    )
    with pytest.raises(EvaluationRecordV1Error, match="only valid for FINAL"):
        validate_evaluation_record_v1(a9_nonfinal)


def test_integrity_subjects_are_explicit_and_deterministic(golden_input, config):
    first = build_evaluation_record_v1(run(golden_input, config).record)
    second = build_evaluation_record_v1(run(copy.deepcopy(golden_input), config).record)
    assert first["integrity"] == second["integrity"]
    digests = {item["digest_id"]: item for item in first["integrity"]["digests"]}

    input_digest = digests["input-snapshot"]
    assert input_digest["algorithm"] == "SHA-256"
    assert input_digest["subject_kind"] == "CANONICAL_JSON_OBJECT"
    assert input_digest["subject_ref"] == "input.json#snapshot"
    assert input_digest["canonicalization_id"] == CANONICALIZATION_ID
    assert input_digest["origin"] == "LOCAL_COMPUTED"

    source_digest = digests["source-manifest"]
    assert source_digest["subject_kind"] == "CANONICAL_JSON_OBJECT"
    assert source_digest["subject_ref"] == "evidence.json#sources+evidence"
    assert source_digest["canonicalization_id"] == CANONICALIZATION_ID
    assert source_digest["origin"] == "LOCAL_COMPUTED"

    for name, subject_ref in (
        ("market-snapshot", "market.json#snapshot.hash_payload"),
        ("peer-snapshot", "peers.json#snapshot.hash_payload"),
    ):
        assert digests[name]["subject_kind"] == "CANONICAL_JSON_OBJECT"
        assert digests[name]["subject_ref"] == subject_ref
        assert digests[name]["canonicalization_id"] == CANONICALIZATION_ID
        assert digests[name]["origin"] == "LOCAL_COMPUTED"

    result_digest = digests["v1.5-result"]
    assert result_digest["subject_kind"] == "V1_5_RESULT_PAYLOAD"
    assert result_digest["subject_ref"] == "result_payload.v1.5"
    assert result_digest["canonicalization_id"] == CANONICALIZATION_ID
    assert result_digest["origin"] == "LOCAL_COMPUTED"

    content_hash_digests = [
        item for item in first["integrity"]["digests"]
        if item["digest_id"].startswith("source-content-hash-")
    ]
    assert content_hash_digests
    assert all(item["algorithm"] == "UNKNOWN" for item in content_hash_digests)
    assert all(item["subject_ref"] == "UNKNOWN" for item in content_hash_digests)
    assert all(item["origin"] == "LEGACY_UNRESOLVED" for item in content_hash_digests)
    assert not any("evaluation-record.v1.json" in item["subject_ref"] for item in digests.values())


def test_new_artifact_is_persisted_and_validated_for_all_five_lifecycle_stages(
    golden_input, config, tmp_path
):
    store = EvaluationStore(tmp_path / "evaluations")
    for mode in MODES:
        outcome = run(golden_input, config, mode=mode, at=EVAL_AT, store=store)
        artifact_path = store.path_for(outcome.record.evaluation_id) / RECORD_ARTIFACT_NAME
        raw = artifact_path.read_bytes()
        assert raw.endswith(b"\n")
        document = json.loads(raw.decode("utf-8"))
        validate_evaluation_record_v1(document)
        assert document["evaluation"]["mode"] == mode.upper()
        original_payloads = outcome.record.artifacts()
        for existing_name in (
            "evaluation.json",
            "input.json",
            "evidence.json",
            "market.json",
            "peers.json",
            "result.json",
        ):
            stored_existing = json.loads(
                (store.path_for(outcome.record.evaluation_id) / existing_name).read_text(encoding="utf-8")
            )
            assert stored_existing == original_payloads[existing_name]
        report = store.verify_hashes(outcome.record.evaluation_id)
        assert report["result_hash_matches"] is True
        assert report["artifact_mismatches"] == []
        assert report["artifacts_verified"] == 7

        manifest = json.loads(
            (store.path_for(outcome.record.evaluation_id) / "manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["artifact_hash_algorithm"] == "SHA-256"
        assert manifest["artifact_hash_profile"] == CANONICALIZATION_ID
        assert manifest["artifact_hash_subject"] == "parsed JSON object"
        assert manifest["artifacts"][RECORD_ARTIFACT_NAME] == sha256_of(document)


def test_old_directories_without_a15_artifact_remain_readable_and_verifiable(
    golden_input, config, tmp_path
):
    record = run(golden_input, config).record
    payloads = record.artifacts()
    payloads.pop(RECORD_ARTIFACT_NAME)
    manifest = payloads["manifest.json"]
    manifest.pop("artifact_hash_algorithm", None)
    manifest.pop("artifact_hash_profile", None)
    manifest.pop("artifact_hash_subject", None)
    manifest["artifacts"] = {
        name: sha256_of(payload)
        for name, payload in sorted(payloads.items())
        if name != "manifest.json"
    }

    root = tmp_path / "historical"
    directory = root / record.evaluation_id
    directory.mkdir(parents=True)
    for name, payload in payloads.items():
        (directory / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    store = EvaluationStore(root)
    assert not (directory / RECORD_ARTIFACT_NAME).exists()
    assert store.read(record.evaluation_id)["result_hash"] == record.result_hash
    assert store.read_full(record.evaluation_id)["input_snapshot"] == record.input_snapshot
    report = store.verify_hashes(record.evaluation_id)
    assert report["result_hash_matches"] is True
    assert report["artifact_mismatches"] == []
    assert report["artifacts_verified"] == 6
    assert not (directory / RECORD_ARTIFACT_NAME).exists()


def test_node_independently_matches_pinned_v15_canonical_object_hash():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed; cross-runtime hash vector is not executable")

    fixture = {
        "name": "e\u0301",
        "count": 7,
        "ratio": 1.25,
        "truth": True,
    }
    expected_text = '{"count":7,"name":"é","ratio":{"__float__":"1.25"},"truth":true}'
    expected_digest = "52d537c0d1a4843504a7bdd10f3957ad29f9b73ea8ae64e5c7cfddcf9c6daa4d"
    assert canonical_json(fixture) == expected_text
    assert sha256_of(fixture) == expected_digest

    script = r"""
const crypto = require('node:crypto');
function normalise(value) {
  if (value === null || typeof value === 'boolean') return value;
  if (typeof value === 'string') return value.normalize('NFC');
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('non-finite number');
    if (Number.isInteger(value)) return value;
    return {__float__: value.toString()};
  }
  if (Array.isArray(value)) return value.map(normalise);
  if (typeof value === 'object') {
    const out = {};
    for (const key of Object.keys(value).sort()) out[key] = normalise(value[key]);
    return out;
  }
  throw new Error('unsupported value');
}
const input = JSON.parse(process.env.A15_CANONICAL_FIXTURE);
const text = JSON.stringify(normalise(input));
const digest = crypto.createHash('sha256').update(text, 'utf8').digest('hex');
let rejectedNonFinite = false;
try { normalise(Number.NaN); } catch (_) { rejectedNonFinite = true; }
if (!rejectedNonFinite) throw new Error('non-finite number was accepted');
process.stdout.write(JSON.stringify({text, digest}));
"""
    env = dict(os.environ)
    env["A15_CANONICAL_FIXTURE"] = json.dumps(fixture, ensure_ascii=False)
    completed = subprocess.run(
        [node, "-e", script],
        capture_output=True,
        text=True,
        env=env,
        check=True,
        timeout=30,
    )
    assert json.loads(completed.stdout) == {"text": expected_text, "digest": expected_digest}
