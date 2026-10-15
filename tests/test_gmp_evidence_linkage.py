"""§7 GMP evidence linkage through the evaluation and A15 persistence paths."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pytest

from ipo_screening import evaluation_record as evaluation_record_module
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.gmp_evidence import (
    GMP_LINK_DIAGNOSTIC_CODE,
    GMP_LINK_EVIDENCE_FIELDS,
    verify_gmp_evidence_link,
)
from ipo_screening.pipeline import evaluate, replay


LINK_SOURCE_ID = "SRC-SYNTHETIC-GMP"
MANIFEST_URI_PATH = "evidence/gmp-observations/synthetic-link/capture-manifest.json"
ARTIFACT_ID = "synthetic-page"
AS_OF = "2026-10-15T10:32:00Z"
WINDOW_START = "2026-10-15T13:15:14Z"
WINDOW_END = "2026-10-15T13:17:58Z"
EVALUATED_AT = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)
CAPTURE_TEXT = (
    "# Acme CorpIPO GMP Today\n"
    "Grey market premium\n"
    "+71.4%\n"
    "4:02 pm IST on Thu, 15 Oct, 2026"
)


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    return result.stdout


def _make_capture_repo(
    tmp_path: Path,
    *,
    manifest_mutator: Callable[[dict[str, Any]], None] | None = None,
    history_commits: int = 1,
    artifact_text: str = CAPTURE_TEXT,
    duplicate_manifest_json_key: bool = False,
) -> tuple[Path, str, dict[str, Any]]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "evidence-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "arena-tests@example.invalid")
    _git(repo, "config", "user.name", "Arena Tests")

    package = repo / "evidence" / "gmp-observations" / "synthetic-link"
    artifact_path = package / "source-captures" / "page.md"
    manifest_path = package / "capture-manifest.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_bytes = artifact_text.encode("utf-8")
    artifact_path.write_bytes(artifact_bytes)

    manifest: dict[str, Any] = {
        "artifactType": "synthetic-rendered-capture-manifest",
        "publisherIssuePage": {
            "url": "https://publisher.example/ipo/acme-corp",
            "displayedIssueName": "Acme Corp",
            "normalizedSourceTimeUtc": AS_OF,
        },
        "captureMethod": {
            "rawProviderResponseBytesCaptured": False,
            "exactReceiptTimeCaptured": False,
        },
        "artifacts": [
            {
                "id": ARTIFACT_ID,
                "url": "https://publisher.example/ipo/acme-corp",
                "toolResultStatus": "success",
                "file": "source-captures/page.md",
                "bytes": len(artifact_bytes),
                "sha256": hashlib.sha256(artifact_bytes).hexdigest().upper(),
                "retrievalWindowUtc": {
                    "notBefore": WINDOW_START,
                    "notAfter": WINDOW_END,
                },
            }
        ],
    }
    if manifest_mutator is not None:
        manifest_mutator(manifest)

    def manifest_bytes() -> bytes:
        encoded = json.dumps(manifest, indent=2, ensure_ascii=False)
        if duplicate_manifest_json_key:
            encoded = encoded.replace(
                '"exactReceiptTimeCaptured": false',
                '"exactReceiptTimeCaptured": false,\n    "exactReceiptTimeCaptured": true',
                1,
            )
        return (encoded + "\n").encode("utf-8")

    raw_manifest = manifest_bytes()
    manifest_path.write_bytes(raw_manifest)
    _git(repo, "add", "evidence")
    _git(repo, "commit", "-qm", "add synthetic retained capture")

    for commit_index in range(1, history_commits):
        manifest["history_note"] = f"follow-up amendment {commit_index}"
        raw_manifest = manifest_bytes()
        manifest_path.write_bytes(raw_manifest)
        _git(repo, "add", str(manifest_path.relative_to(repo)))
        _git(repo, "commit", "-qm", f"amend manifest {commit_index}")

    manifest_hash = hashlib.sha256(raw_manifest).hexdigest()
    source = {
        "source_id": LINK_SOURCE_ID,
        "source_type": "MARKET_DATA",
        "uri": f"{MANIFEST_URI_PATH}#{ARTIFACT_ID}",
        "content_hash": f"sha256:{manifest_hash}",
    }
    return repo, manifest_hash, source


def _linked_input(golden_input, source: dict[str, Any]) -> dict[str, Any]:
    document = copy.deepcopy(golden_input)
    document["company_name"] = "Acme Corp"
    document["market"]["gmp"] = {
        "as_of": AS_OF,
        "pct": 71.4,
        "trend": None,
        "source_id": LINK_SOURCE_ID,
    }
    document.setdefault("_sources", []).append(copy.deepcopy(source))
    evidence = document.setdefault("_evidence", {})
    quotes = {
        "company_name": ("line 1", "# Acme CorpIPO GMP Today"),
        "market.gmp.pct": ("line 3", "+71.4%"),
        "market.gmp.as_of": ("line 4", "4:02 pm IST on Thu, 15 Oct, 2026"),
    }
    for path, evidence_id in GMP_LINK_EVIDENCE_FIELDS:
        locator, quote = quotes[path]
        evidence[path] = {
            "evidence_id": evidence_id,
            "source_id": LINK_SOURCE_ID,
            "locator": locator,
            "quote": quote,
            "extraction_method": "MANUAL_ENTRY",
        }
    return document


def _use_test_repo(monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(
        evaluation_record_module,
        "verify_gmp_evidence_link",
        lambda context, record, *, evaluation_at: verify_gmp_evidence_link(
            context,
            record,
            evaluation_at=evaluation_at,
            repo_root=repo,
        ),
    )


def _a15_document(outcome) -> dict[str, Any]:
    return outcome.record.artifacts()["evaluation-record.v1.json"]


def _link_diagnostic(document: dict[str, Any]) -> dict[str, Any]:
    matches = [
        item
        for item in document["result"]["diagnostics"]
        if item["code"] == GMP_LINK_DIAGNOSTIC_CODE
    ]
    assert len(matches) == 1
    return matches[0]


def test_verified_link_maps_two_byte_digests_unknown_window_and_fixed_a15_diagnostic(
    tmp_path, monkeypatch, golden_input, config
):
    repo, manifest_hash, source = _make_capture_repo(tmp_path)
    _use_test_repo(monkeypatch, repo)
    document = _linked_input(golden_input, source)
    outcome = evaluate(
        document,
        config,
        mode="final",
        evaluation_datetime=EVALUATED_AT,
    )
    a15 = _a15_document(outcome)
    diag = _link_diagnostic(a15)

    assert "result=VERIFIED" in diag["message"]
    assert "Publisher-reported GMP observation: rendered-text capture of https://publisher.example/ipo/acme-corp" in diag["message"]
    assert "D3_state=AMOUNT" in diag["message"]
    assert f"manifest_sha256={manifest_hash}" in diag["message"]
    artifact_hash = hashlib.sha256(CAPTURE_TEXT.encode("utf-8")).hexdigest()
    assert f"artifact_sha256={artifact_hash}" in diag["message"]
    assert f"retrieval_window_utc={WINDOW_START}/{WINDOW_END}" in diag["message"]
    assert "exact_receipt_time=UNKNOWN" in diag["message"]

    linked_source = next(item for item in a15["sources"] if item["source_id"] == LINK_SOURCE_ID)
    assert len(linked_source["digest_refs"]) == 2
    timestamp = next(item for item in linked_source["timestamps"] if item["kind"] == "LOCAL_RETRIEVED_AT")
    assert timestamp == {
        "kind": "LOCAL_RETRIEVED_AT",
        "state": "UNKNOWN",
        "source_text": f"{WINDOW_START}/{WINDOW_END}",
        "evidence_refs": sorted(evidence_id for _path, evidence_id in GMP_LINK_EVIDENCE_FIELDS),
        "reason": {
            "code": "UNAVAILABLE",
            "message": "exact receipt time not captured; the manifest records only this bracketing window",
        },
    }
    assert "normalized_utc" not in timestamp

    digest_by_id = {item["digest_id"]: item for item in a15["integrity"]["digests"]}
    linked_digests = [digest_by_id[digest_id] for digest_id in linked_source["digest_refs"]]
    assert len(linked_digests) == 2
    assert all(item["algorithm"] == "SHA-256" for item in linked_digests)
    assert all(item["subject_kind"] == "RAW_ARTIFACT_BYTES" for item in linked_digests)
    assert all(item["origin"] == "LOCAL_COMPUTED" for item in linked_digests)
    assert all(item["evidence_refs"] == sorted(evidence_id for _path, evidence_id in GMP_LINK_EVIDENCE_FIELDS) for item in linked_digests)
    assert all(len(item["digest_value"]) == 64 and item["digest_value"] == item["digest_value"].lower() for item in linked_digests)
    # The manifest pin's previous opaque/legacy digest is replaced by the local
    # RAW_ARTIFACT_BYTES digest for a verified link.
    manifest_pin_id = next(item["digest_id"] for item in linked_digests if item["subject_ref"] == MANIFEST_URI_PATH)
    assert digest_by_id[manifest_pin_id]["digest_value"] == manifest_hash

    # The verifier is only a local-byte link: A9 still withholds FINAL and A17
    # / scoring remain the ordinary pipeline behavior.
    assert a15["result"]["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert a15["result"]["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"
    assert "final_outcome" not in a15["result"]
    assert any(item["code"] == "A9_GMP_FINAL_WITHHELD" for item in a15["result"]["diagnostics"])


def test_linkage_derives_only_the_canonical_default_evidence_ids(
    tmp_path, monkeypatch, golden_input, config
):
    repo, _manifest_hash, source = _make_capture_repo(tmp_path)
    _use_test_repo(monkeypatch, repo)
    document = _linked_input(golden_input, source)
    for path, _evidence_id in GMP_LINK_EVIDENCE_FIELDS:
        document["_evidence"][path].pop("evidence_id")
    outcome = evaluate(document, config, evaluation_datetime=EVALUATED_AT)
    assert "result=VERIFIED" in _link_diagnostic(_a15_document(outcome))["message"]


def test_d3_zero_and_missing_remain_linkable_without_qualifying_final(
    tmp_path, monkeypatch, golden_input, config
):
    repo, _manifest_hash, source = _make_capture_repo(
        tmp_path,
        artifact_text=CAPTURE_TEXT.replace("+71.4%", "0.0%"),
    )
    _use_test_repo(monkeypatch, repo)
    zero_document = _linked_input(golden_input, source)
    zero_document["market"]["gmp"]["pct"] = 0.0
    zero_document["_evidence"]["market.gmp.pct"]["quote"] = "0.0%"
    zero = _a15_document(evaluate(zero_document, config, evaluation_datetime=EVALUATED_AT))
    assert "result=VERIFIED" in _link_diagnostic(zero)["message"]
    assert "D3_state=ZERO" in _link_diagnostic(zero)["message"]
    assert zero["result"]["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"
    assert "final_outcome" not in zero["result"]

    missing_root = tmp_path / "missing"
    missing_repo, _hash, missing_source = _make_capture_repo(
        missing_root,
        artifact_text=CAPTURE_TEXT.replace("+71.4%", "Not quoted yet"),
    )
    _use_test_repo(monkeypatch, missing_repo)
    missing_document = _linked_input(golden_input, missing_source)
    missing_document["market"]["gmp"]["pct"] = None
    missing_document["_evidence"]["market.gmp.pct"]["quote"] = "Not quoted yet"
    missing = _a15_document(evaluate(missing_document, config, evaluation_datetime=EVALUATED_AT))
    assert "result=VERIFIED" in _link_diagnostic(missing)["message"]
    assert "D3_state=MISSING" in _link_diagnostic(missing)["message"]
    assert missing["result"]["outcome_resolution"]["reason"]["code"] == "MISSING"
    assert "final_outcome" not in missing["result"]


def test_linkage_does_not_change_scoring_or_a9_gate(tmp_path, monkeypatch, golden_input, config):
    repo, _manifest_hash, source = _make_capture_repo(tmp_path)
    _use_test_repo(monkeypatch, repo)
    linked = _linked_input(golden_input, source)
    plain = copy.deepcopy(linked)
    plain["market"]["gmp"]["source_id"] = "MARKET-TRACKER"
    plain["_sources"] = [item for item in plain["_sources"] if item["source_id"] != LINK_SOURCE_ID]
    for path, _evidence_id in GMP_LINK_EVIDENCE_FIELDS:
        if path != "company_name":
            plain["_evidence"].pop(path, None)
    plain["_evidence"]["company_name"] = copy.deepcopy(golden_input["_evidence"]["company_name"])

    linked_outcome = evaluate(linked, config, evaluation_datetime=EVALUATED_AT)
    plain_outcome = evaluate(plain, config, evaluation_datetime=EVALUATED_AT)
    assert linked_outcome.score.to_dict() == plain_outcome.score.to_dict()
    linked_a15 = _a15_document(linked_outcome)
    plain_a15 = _a15_document(plain_outcome)
    assert linked_a15["result"]["outcome_resolution"]["state"] == plain_a15["result"]["outcome_resolution"]["state"]
    assert linked_a15["result"]["outcome_resolution"]["reason"]["code"] == plain_a15["result"]["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"
    assert _link_diagnostic(linked_a15)["code"] == GMP_LINK_DIAGNOSTIC_CODE
    assert not any(item["code"] == GMP_LINK_DIAGNOSTIC_CODE for item in plain_a15["result"]["diagnostics"])


def test_cutoff_inside_window_is_nonterminal_and_preserves_only_unknown_window(
    tmp_path, monkeypatch, golden_input, config
):
    repo, _manifest_hash, source = _make_capture_repo(tmp_path)
    _use_test_repo(monkeypatch, repo)
    document = _linked_input(golden_input, source)
    evaluation_at = datetime(2026, 10, 15, 13, 16, tzinfo=timezone.utc)
    outcome = evaluate(document, config, evaluation_datetime=evaluation_at)
    a15 = _a15_document(outcome)
    diag = _link_diagnostic(a15)
    assert "result=NOT_AVAILABLE_BY_CUTOFF" in diag["message"]
    source_object = next(item for item in a15["sources"] if item["source_id"] == LINK_SOURCE_ID)
    assert len(source_object["digest_refs"]) == 1  # the legacy content_hash stays unresolved
    fact = next(item for item in source_object["timestamps"] if item["kind"] == "LOCAL_RETRIEVED_AT")
    assert fact["state"] == "UNKNOWN"
    assert fact["source_text"] == f"{WINDOW_START}/{WINDOW_END}"
    assert "normalized_utc" not in fact


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    [
        ("wrong-pct", "does not equal the displayed percentage"),
        ("wrong-as-of", "does not equal the publisher's exact displayed stamp"),
        ("weekday-mismatch", "not an explicit supported instant"),
        ("wrong-locator", "is outside the artifact"),
        ("publisher-host-mismatch", "publisher-host or issue-URL identity"),
        ("untied-trend", "trend has no linked evidence"),
    ],
)
def test_link_failures_are_diagnostics_not_input_rejections(
    tmp_path, monkeypatch, golden_input, config, case, expected_reason
):
    manifest_mutator = None
    if case == "publisher-host-mismatch":
        def manifest_mutator(manifest):
            manifest["artifacts"][0]["url"] = "https://other.example/ipo/acme-corp"

    artifact_text = CAPTURE_TEXT
    if case == "weekday-mismatch":
        artifact_text = artifact_text.replace("Thu, 15 Oct", "Fri, 15 Oct")
    repo, _manifest_hash, source = _make_capture_repo(
        tmp_path,
        manifest_mutator=manifest_mutator,
        artifact_text=artifact_text,
    )
    _use_test_repo(monkeypatch, repo)
    document = _linked_input(golden_input, source)
    if case == "wrong-pct":
        document["market"]["gmp"]["pct"] = 70.4
    elif case == "wrong-as-of":
        document["market"]["gmp"]["as_of"] = "2026-10-15T10:33:00Z"
    elif case == "weekday-mismatch":
        document["_evidence"]["market.gmp.as_of"]["quote"] = "4:02 pm IST on Fri, 15 Oct, 2026"
    elif case == "wrong-locator":
        document["_evidence"]["market.gmp.pct"]["locator"] = "line 99"
    elif case == "untied-trend":
        document["market"]["gmp"]["trend"] = "strong"

    outcome = evaluate(document, config, evaluation_datetime=EVALUATED_AT)
    a15 = _a15_document(outcome)
    message = _link_diagnostic(a15)["message"]
    assert "result=FAILED:" in message
    assert expected_reason in message
    assert a15["result"]["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"
    assert "final_outcome" not in a15["result"]


def test_duplicate_source_ids_and_contradictory_evidence_aliases_fail_nonterminally(
    tmp_path, monkeypatch, golden_input, config
):
    repo, _manifest_hash, source = _make_capture_repo(tmp_path)
    _use_test_repo(monkeypatch, repo)
    duplicate_source_input = _linked_input(golden_input, source)
    conflicting_source = copy.deepcopy(source)
    conflicting_source["uri"] = "evidence/gmp-observations/other/capture-manifest.json#other"
    duplicate_source_input["_sources"].append(conflicting_source)
    duplicate_result = _a15_document(
        evaluate(duplicate_source_input, config, evaluation_datetime=EVALUATED_AT)
    )
    assert "exactly one _sources entry" in _link_diagnostic(duplicate_result)["message"]
    assert duplicate_result["result"]["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"

    contradictory = _linked_input(golden_input, source)
    contradictory["_evidence"]["market.gmp.pct"]["quoted_text"] = "0.0%"
    contradictory_result = _a15_document(evaluate(contradictory, config, evaluation_datetime=EVALUATED_AT))
    assert "contradictory quote aliases" in _link_diagnostic(contradictory_result)["message"]
    assert contradictory_result["result"]["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"


def test_manifest_pin_artifact_bytes_duplicate_source_and_history_fail_closed(
    tmp_path, monkeypatch, golden_input, config
):
    # Two committed manifest versions are historically mutable even when the
    # input is pinned to the newest bytes.
    repo, _hash, source = _make_capture_repo(tmp_path, history_commits=2)
    _use_test_repo(monkeypatch, repo)
    document = _linked_input(golden_input, source)
    outcome = evaluate(document, config, evaluation_datetime=EVALUATED_AT)
    assert "manifest is not write-once" in _link_diagnostic(_a15_document(outcome))["message"]


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        ("manifest-pin", "manifest SHA-256 does not match"),
        ("artifact-bytes", "byte count or SHA-256 does not match"),
        ("offsetless-window", "retrieval window is missing, offset-less, or inverted"),
        ("inverted-window", "retrieval window is missing, offset-less, or inverted"),
        ("noncanonical-artifact-path", "non-canonical relative file path"),
    ],
)
def test_manifest_and_artifact_substitutions_and_bad_windows_fail_closed(
    tmp_path, monkeypatch, golden_input, config, mutation, expected_reason
):
    manifest_mutator = None
    if mutation == "offsetless-window":
        def manifest_mutator(manifest):
            manifest["artifacts"][0]["retrievalWindowUtc"]["notBefore"] = "2026-10-15T13:15:14"
    elif mutation == "inverted-window":
        def manifest_mutator(manifest):
            manifest["artifacts"][0]["retrievalWindowUtc"]["notBefore"] = "2026-10-15T13:18:00Z"
    elif mutation == "noncanonical-artifact-path":
        def manifest_mutator(manifest):
            manifest["artifacts"][0]["file"] = "source-captures//page.md"

    repo, _manifest_hash, source = _make_capture_repo(
        tmp_path,
        manifest_mutator=manifest_mutator,
    )
    if mutation == "manifest-pin":
        manifest_path = repo / MANIFEST_URI_PATH
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["publisherIssuePage"]["displayedIssueName"] = "Substituted Issue"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    elif mutation == "artifact-bytes":
        artifact_path = repo / "evidence/gmp-observations/synthetic-link/source-captures/page.md"
        artifact_path.write_text(CAPTURE_TEXT.replace("+71.4%", "+72.4%"), encoding="utf-8")

    _use_test_repo(monkeypatch, repo)
    outcome = evaluate(_linked_input(golden_input, source), config, evaluation_datetime=EVALUATED_AT)
    message = _link_diagnostic(_a15_document(outcome))["message"]
    assert "result=FAILED:" in message
    assert expected_reason in message
    assert outcome.record.score["final_score"] is not None


def test_manifest_duplicate_keys_and_present_retrieval_timestamp_fail_closed(
    tmp_path, monkeypatch, golden_input, config
):
    repo, _hash, source = _make_capture_repo(tmp_path, duplicate_manifest_json_key=True)
    _use_test_repo(monkeypatch, repo)
    document = _linked_input(golden_input, source)
    outcome = evaluate(document, config, evaluation_datetime=EVALUATED_AT)
    assert "duplicate JSON key" in _link_diagnostic(_a15_document(outcome))["message"]

    repo2, _hash2, source2 = _make_capture_repo(tmp_path / "with-retrieval", artifact_text=CAPTURE_TEXT)
    _use_test_repo(monkeypatch, repo2)
    source2["retrieval_timestamp"] = WINDOW_END
    document2 = _linked_input(golden_input, source2)
    outcome2 = evaluate(document2, config, evaluation_datetime=EVALUATED_AT)
    a15 = _a15_document(outcome2)
    assert "retrieval_timestamp must be absent" in _link_diagnostic(a15)["message"]
    source_object = next(item for item in a15["sources"] if item["source_id"] == LINK_SOURCE_ID)
    assert not any(item["kind"] == "LOCAL_RETRIEVED_AT" for item in source_object["timestamps"])


def test_replay_reconstructs_linked_evidence_paths_and_reverifies_a15(
    tmp_path, monkeypatch, golden_input, config
):
    repo, _hash, source = _make_capture_repo(tmp_path)
    _use_test_repo(monkeypatch, repo)
    store = EvaluationStore(tmp_path / "evaluations")
    outcome = evaluate(
        _linked_input(golden_input, source),
        config,
        evaluation_datetime=EVALUATED_AT,
        store=store,
    )
    stored_a15 = store.read_artifact(outcome.record.evaluation_id, "evaluation-record.v1")
    replayed = replay(store, outcome.record.evaluation_id, config)
    replayed_a15 = _a15_document(replayed)

    assert replayed.record.result_hash == outcome.record.result_hash
    assert replayed_a15["result"]["outcome_resolution"] == stored_a15["result"]["outcome_resolution"]
    assert _link_diagnostic(replayed_a15)["message"] == _link_diagnostic(stored_a15)["message"]
    verification = store.verify_hashes(outcome.record.evaluation_id)
    assert verification["result_hash_matches"] is True
    assert verification["artifact_mismatches"] == []


def test_replay_preserves_conflicting_link_declarations_and_failure_diagnostic(
    tmp_path, monkeypatch, golden_input, config
):
    repo, _hash, source = _make_capture_repo(tmp_path)
    _use_test_repo(monkeypatch, repo)
    document = _linked_input(golden_input, source)
    conflicting_source = copy.deepcopy(source)
    conflicting_source["uri"] = "evidence/gmp-observations/other/capture-manifest.json#other"
    document["_sources"].append(conflicting_source)
    store = EvaluationStore(tmp_path / "evaluations")

    original = evaluate(
        document,
        config,
        evaluation_datetime=EVALUATED_AT,
        store=store,
    )
    original_a15 = store.read_artifact(original.record.evaluation_id, "evaluation-record.v1")
    stored_record = store.read(original.record.evaluation_id)
    stored_linkage_context = stored_record["provenance"]["_gmp_linkage_context"]
    assert sum(item.get("source_id") == LINK_SOURCE_ID for item in stored_linkage_context["sources"]) == 2

    replayed = replay(store, original.record.evaluation_id, config)
    replayed_a15 = _a15_document(replayed)
    assert replayed.record.result_hash == original.record.result_hash
    assert _link_diagnostic(replayed_a15)["message"] == _link_diagnostic(original_a15)["message"]
    assert "exactly one _sources entry" in _link_diagnostic(replayed_a15)["message"]


def test_failed_or_unlinked_legacy_inputs_keep_the_existing_a15_mapping(
    golden_input, config
):
    # The known MARKET-TRACKER reference-fixture input remains unlinked and has
    # no new diagnostic or verified digest/timestamp mapping.
    outcome = evaluate(golden_input, config, evaluation_datetime=EVALUATED_AT)
    a15 = _a15_document(outcome)
    assert not any(item["code"] == GMP_LINK_DIAGNOSTIC_CODE for item in a15["result"]["diagnostics"])
    assert not any(item.get("subject_kind") == "RAW_ARTIFACT_BYTES" for item in a15["integrity"]["digests"])
