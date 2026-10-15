"""GMP evidence-linkage verifier (A9 policy §7; L1, L2-a, L3-a, L4-a with R1-R8).

Fixtures are generated under ``tmp_path``. Nothing is written to ``evidence/``.
The retained ML-T manifest is read only, to prove it is ineligible (no marker).
A successful link proves value ties to retained bytes, not authenticity,
transcription accuracy, authenticated capture time, or qualification.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import CONFIG_PATH, REPO_ROOT, run
from ipo_screening.evaluation_record import build_evaluation_record_v1
from ipo_screening.gmp_linkage import (
    LINK_DIAGNOSTIC_CODE,
    RESULT_FAILED,
    RESULT_NOT_AVAILABLE_BY_CUTOFF,
    RESULT_VERIFIED,
    entries_from_input_evidence,
    entries_from_registry,
    normalise_evidence,
    render_publisher_stamp,
    verify_gmp_linkage,
)
from ipo_screening.pipeline import load_config
from ipo_screening.gmp_evidence import DisplayedGmpState

ML_DIR = REPO_ROOT / "evidence" / "gmp-observations" / "marketliveipogmp-tonbo-20261015"
ML_ARTIFACT = ML_DIR / "source-captures" / "marketliveipogmp-ipo-tonbo-imaging-india-chunk-0.md"
ML_MANIFEST = ML_DIR / "capture-manifest.json"
EVAL_OK = "2026-10-15T14:00:00Z"  # after the window end 13:17:58.770Z
STAMP = "4:02 pm IST on Thu, 15 Oct, 2026"
TITLE = "# Tonbo Imaging IndiaIPO GMP Today"
FIX_REL = "evidence/gmp-observations/fixture-linkage-001"
SRC = "SRC-FIX"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def repo(tmp_path):
    """A throwaway repository root holding one fixture manifest and artifact."""
    return tmp_path


def _write_fixture(root: Path, *, artifact_bytes: bytes | None = None, marker: bool = True,
                   window=None, extra_artifacts=(), manifest_mutator=None, duplicate_id=False):
    folder = root / FIX_REL
    (folder / "source-captures").mkdir(parents=True, exist_ok=True)
    data = artifact_bytes if artifact_bytes is not None else ML_ARTIFACT.read_bytes()
    (folder / "source-captures" / "capture.md").write_bytes(data)
    entry = {
        "id": "art-1",
        "url": "https://marketliveipogmp.com/ipo/tonbo-imaging-india",
        "toolResultStatus": "success",
        "file": "source-captures/capture.md",
        "bytes": len(data),
        "sha256": _sha(data).upper(),
        "retrievalWindowUtc": window or {
            "notBefore": "2026-10-15T13:15:14.096Z",
            "notAfter": "2026-10-15T13:17:58.770Z",
        },
    }
    artifacts = [entry, *extra_artifacts]
    if duplicate_id:
        artifacts.append(copy.deepcopy(entry))
    manifest = {
        "artifactType": "fixture-rendered-capture-manifest",
        "captureMethod": {"rawProviderResponseBytesCaptured": False, "exactReceiptTimeCaptured": False},
        "artifacts": artifacts,
    }
    if marker:
        manifest["writeOnce"] = True
    if manifest_mutator:
        manifest_mutator(manifest)
    raw = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    (folder / "capture-manifest.json").write_bytes(raw)
    return {"pin": "sha256:" + _sha(raw), "uri": f"{FIX_REL}/capture-manifest.json#art-1"}


def _source(pin_uri, **overrides):
    source = {
        "source_id": SRC,
        "source_type": "MARKET_DATA",
        "uri": pin_uri["uri"],
        "content_hash": pin_uri["pin"],
    }
    source.update(overrides)
    return source


def _gmp(**overrides):
    gmp = {"as_of": "2026-10-15T16:02:00+05:30", "pct": 71.4, "source_id": SRC}
    gmp.update(overrides)
    return gmp


def _pairs(*, name_quote=TITLE, name_loc="line 1", pct_quote="+71.4%", pct_loc="line 7",
           asof_quote=STAMP, asof_loc="line 84"):
    return [
        ("company_name", {"source_id": SRC, "locator": name_loc, "quote": name_quote,
                          "extraction_method": "MANUAL_ENTRY"}),
        ("market.gmp.pct", {"source_id": SRC, "locator": pct_loc, "quote": pct_quote,
                            "extraction_method": "MANUAL_ENTRY"}),
        ("market.gmp.as_of", {"source_id": SRC, "locator": asof_loc, "quote": asof_quote,
                              "extraction_method": "MANUAL_ENTRY"}),
    ]


def _verify(root, pin_uri, *, market=None, company="Tonbo Imaging India Limited", pairs=None,
            sources=None, evaluation=EVAL_OK):
    srcs = sources if sources is not None else [_source(pin_uri)]
    return verify_gmp_linkage(
        repo_root=root,
        market_gmp=market if market is not None else _gmp(),
        company_name=company,
        sources=srcs,
        evidence=normalise_evidence(entries_from_input_evidence(dict(pairs or _pairs()))),
        evaluation_timestamp=evaluation,
    )


def _artifact_with(line_index, new_line):
    lines = ML_ARTIFACT.read_text(encoding="utf-8").split("\n")
    lines[line_index - 1] = new_line
    return "\n".join(lines).encode("utf-8")


# ---------------------------------------------------------------- happy path

def test_matching_values_verify_and_stay_eligibility_only(repo):
    result = _verify(repo, _write_fixture(repo))
    assert result.result == RESULT_VERIFIED
    assert result.reasons == ()
    assert result.digests_verified is True
    assert result.displayed_state == DisplayedGmpState.AMOUNT.value
    assert result.window_source_text == "2026-10-15T13:15:14.096Z/2026-10-15T13:17:58.770Z"
    assert "not an exact receipt time" in result.message
    assert "A9 stays fail-closed" in result.message
    assert "not provider response bytes" in result.d1_label


def test_stamp_renders_in_publisher_format():
    assert render_publisher_stamp(datetime(2026, 10, 15, 10, 32, tzinfo=timezone.utc)) == STAMP


def test_zero_is_verified_but_classified_zero(repo):
    pin = _write_fixture(repo, artifact_bytes=_artifact_with(7, "₹0+0.0%"))
    result = _verify(repo, pin, market=_gmp(pct=0.0), pairs=_pairs(pct_quote="+0.0%"))
    assert result.result == RESULT_VERIFIED
    assert result.displayed_state == DisplayedGmpState.ZERO.value


# ---------------------------------------------------------------- absent / ineligible

def test_absent_when_no_evidence_uri_and_no_diagnostic(repo):
    plain = {"source_id": SRC, "source_type": "MARKET_DATA", "uri": "connector://market", "content_hash": "x"}
    assert _verify(repo, {"pin": "", "uri": ""}, sources=[plain]) is None
    assert verify_gmp_linkage(repo_root=repo, market_gmp={"pct": 1, "source_id": SRC}, company_name="X",
                              sources=[], evidence=[], evaluation_timestamp=EVAL_OK) is None


def test_real_ml_t_manifest_is_ineligible_without_marker():
    pin = {"pin": "sha256:" + _sha(ML_MANIFEST.read_bytes()),
           "uri": "evidence/gmp-observations/marketliveipogmp-tonbo-20261015/capture-manifest.json#ml-tonbo-chunk-0"}
    result = _verify(REPO_ROOT, pin)
    assert result.result == RESULT_FAILED
    assert "no write-once marker" in result.message


def test_retained_manifest_bytes_are_unchanged():
    # Guard: the repository's retained manifest is never edited by this work.
    assert _sha(ML_MANIFEST.read_bytes()) == "a4f83492455f4691159ba1f049547803cfa0db2aee248b7dbdfb4c990cfbb87d"


# ---------------------------------------------------------------- substitution / pin

def test_edited_manifest_fails_the_pin(repo):
    pin = _write_fixture(repo)
    manifest = repo / FIX_REL / "capture-manifest.json"
    manifest.write_bytes(manifest.read_bytes().replace(b"13:15:14", b"13:14:14"))
    result = _verify(repo, pin)
    assert result.result == RESULT_FAILED and "manifest bytes" in result.message


def test_swapped_artifact_bytes_fail_integrity(repo):
    pin = _write_fixture(repo)
    (repo / FIX_REL / "source-captures" / "capture.md").write_bytes(b"other text\n")
    result = _verify(repo, pin)
    assert result.result == RESULT_FAILED and "does not match its declared" in result.message


def test_another_artifact_id_in_the_same_manifest_fails(repo):
    pin = _write_fixture(repo)
    other = dict(pin, uri=pin["uri"].replace("#art-1", "#art-2"))
    result = _verify(repo, other)
    assert result.result == RESULT_FAILED and "not declared" in result.message


def test_duplicated_artifact_id_fails(repo):
    pin = _write_fixture(repo, duplicate_id=True)
    result = _verify(repo, pin)
    assert result.result == RESULT_FAILED and "declared more than once" in result.message


def test_another_issues_capture_with_equal_value_and_stamp_fails(repo):
    result = _verify(repo, _write_fixture(repo), company="Hero Motors Limited")
    assert result.result == RESULT_FAILED and "different issue" in result.message


# ---------------------------------------------------------------- duplicate keys (D1 defect)

def test_duplicate_window_key_in_manifest_is_refused(repo):
    pin = _write_fixture(repo)
    manifest = repo / FIX_REL / "capture-manifest.json"
    text = manifest.read_text(encoding="utf-8")
    needle = '"sha256"'
    assert text.count(needle) == 1
    dup = ('"retrievalWindowUtc": {"notBefore": "2026-10-15T10:40:00.000Z", '
           '"notAfter": "2026-10-15T10:41:00.000Z"}, ')
    manifest.write_text(text.replace(needle, dup + needle, 1), encoding="utf-8")
    # The pin is now stale too; re-pin so the duplicate itself is what is tested.
    pin = dict(pin, pin="sha256:" + _sha(manifest.read_bytes()))
    result = _verify(repo, pin)
    assert result.result == RESULT_FAILED and "not a strict JSON" in result.message
    assert "retrievalWindowUtc" in result.message


# ---------------------------------------------------------------- location and shape

@pytest.mark.parametrize("uri", [
    "/evidence/gmp-observations/x/capture-manifest.json#art-1",
    "evidence/gmp-observations/../gmp-observations/x/capture-manifest.json#art-1",
    "https://example.com/evidence/gmp-observations/x.json#art-1",
    "evidence/gmp-observations/x/capture-manifest.json",
    "evidence/other/capture-manifest.json#art-1",
])
def test_bad_uri_shapes_fail(repo, uri):
    pin = _write_fixture(repo)
    result = _verify(repo, pin | {"uri": uri}, sources=[_source(pin, uri=uri)])
    assert result.result == RESULT_FAILED


def test_missing_manifest_fails(repo):
    pin = {"pin": "sha256:" + "0" * 64, "uri": f"{FIX_REL}/capture-manifest.json#art-1"}
    assert _verify(repo, pin).result == RESULT_FAILED


def test_uppercase_pin_fails(repo):
    pin = _write_fixture(repo)
    bad = dict(pin, pin=pin["pin"].upper().replace("SHA256", "sha256"))
    assert _verify(repo, bad, sources=[_source(bad)]).result == RESULT_FAILED


def test_two_sources_with_the_same_id_fail(repo):
    pin = _write_fixture(repo)
    result = _verify(repo, pin, sources=[_source(pin), _source(pin)])
    assert result.result == RESULT_FAILED and "exactly one _sources entry" in result.message


def test_non_market_source_type_fails(repo):
    pin = _write_fixture(repo)
    assert _verify(repo, pin, sources=[_source(pin, source_type="PEER_DATA")]).result == RESULT_FAILED


def test_retrieval_timestamp_present_fails(repo):
    pin = _write_fixture(repo)
    result = _verify(repo, pin, sources=[_source(pin, retrieval_timestamp="2026-10-15T13:17:58Z")])
    assert result.result == RESULT_FAILED and "retrieval_timestamp" in result.message


# ---------------------------------------------------------------- value binding

def test_pct_on_another_line_fails(repo):
    result = _verify(repo, _write_fixture(repo), pairs=_pairs(pct_loc="line 11"))
    assert result.result == RESULT_FAILED


def test_pct_value_mismatch_fails(repo):
    result = _verify(repo, _write_fixture(repo), market=_gmp(pct=70.0))
    assert result.result == RESULT_FAILED and "does not equal" in result.message


def test_rupee_quote_for_pct_fails(repo):
    result = _verify(repo, _write_fixture(repo), pairs=_pairs(pct_quote="₹500"))
    assert result.result == RESULT_FAILED and "not a percentage" in result.message


def test_null_pct_is_failed_with_no_value_binding(repo):
    result = _verify(repo, _write_fixture(repo), market=_gmp(pct=None))
    assert result.result == RESULT_FAILED and "null" in result.message


def test_not_quoted_yet_cannot_link_a_value(repo):
    result = _verify(repo, _write_fixture(repo), pairs=_pairs(pct_quote="Not quoted yet"),
                     market=_gmp(pct=71.4))
    assert result.result == RESULT_FAILED


def test_pct_is_bound_as_a_token_not_a_substring(repo):
    # "71.4%" occurs inside "171.4%", so a substring match would wrongly pass.
    pin = _write_fixture(repo, artifact_bytes=_artifact_with(7, "₹500+171.4%"))
    result = _verify(repo, pin, pairs=_pairs(pct_quote="71.4%"))
    assert result.result == RESULT_FAILED and "exactly one token" in result.message


def test_non_null_trend_fails(repo):
    result = _verify(repo, _write_fixture(repo), market=_gmp(trend="up"))
    assert result.result == RESULT_FAILED and "trend" in result.message


def test_stamp_mismatch_fails(repo):
    result = _verify(repo, _write_fixture(repo), pairs=_pairs(asof_quote="4:03 pm IST on Thu, 15 Oct, 2026"))
    assert result.result == RESULT_FAILED


def test_stamp_must_be_the_exact_sentence_not_a_substring(repo):
    result = _verify(repo, _write_fixture(repo), pairs=_pairs(asof_quote="4:02 pm IST"))
    assert result.result == RESULT_FAILED


def test_as_of_later_than_window_end_fails(repo):
    late = "The grey market premium is ₹500 as of 7:00 pm IST on Thu, 15 Oct, 2026. That is +71.4%."
    pin = _write_fixture(repo, artifact_bytes=_artifact_with(84, late))
    result = _verify(repo, pin, market=_gmp(as_of="2026-10-15T19:00:00+05:30"),
                     pairs=_pairs(asof_quote="7:00 pm IST on Thu, 15 Oct, 2026"))
    assert result.result == RESULT_FAILED and "later than the window end" in result.message


def test_as_of_without_offset_fails(repo):
    result = _verify(repo, _write_fixture(repo), market=_gmp(as_of="2026-10-15T16:02:00"))
    assert result.result == RESULT_FAILED


def test_title_quote_must_be_line_one(repo):
    result = _verify(repo, _write_fixture(repo), pairs=_pairs(name_quote="Tonbo", name_loc="line 2"))
    assert result.result == RESULT_FAILED


# ---------------------------------------------------------------- evidence references

def test_explicit_evidence_id_must_equal_canonical(repo):
    pairs = _pairs()
    pairs[1][1]["evidence_id"] = "EV-pct-alt"
    result = _verify(repo, _write_fixture(repo), pairs=pairs)
    assert result.result == RESULT_FAILED and "canonical" in result.message


def test_contradictory_registry_entries_fail(repo):
    pin = _write_fixture(repo)
    items = [
        {"evidence_id": "EV-company_name", "source_id": SRC, "locator": "line 1", "quoted_text": TITLE},
        {"evidence_id": "EV-market.gmp.pct", "source_id": SRC, "locator": "line 7", "quoted_text": "+71.4%"},
        {"evidence_id": "EV-market.gmp.pct", "source_id": SRC, "locator": "line 7", "quoted_text": "+70.0%"},
        {"evidence_id": "EV-market.gmp.as_of", "source_id": SRC, "locator": "line 84", "quoted_text": STAMP},
    ]
    result = verify_gmp_linkage(
        repo_root=repo, market_gmp=_gmp(), company_name="Tonbo Imaging India Limited",
        sources=[_source(pin)], evidence=normalise_evidence(entries_from_registry(items)),
        evaluation_timestamp=EVAL_OK,
    )
    assert result.result == RESULT_FAILED and "contradictory" in result.message


def test_unexpected_entry_for_the_linked_source_fails(repo):
    pairs = _pairs() + [("market.gmp.trend", {"source_id": SRC, "locator": "line 7", "quote": "up"})]
    result = _verify(repo, _write_fixture(repo), pairs=pairs)
    assert result.result == RESULT_FAILED and "not a permitted" in result.message


def test_company_evidence_attributed_to_another_source_fails(repo):
    pairs = _pairs()
    pairs[0][1]["source_id"] = "SRC-OTHER"
    result = _verify(repo, _write_fixture(repo), pairs=pairs)
    assert result.result == RESULT_FAILED and "another source" in result.message


def test_missing_required_evidence_fails(repo):
    result = _verify(repo, _write_fixture(repo), pairs=_pairs()[:2])
    assert result.result == RESULT_FAILED and "missing evidence entry EV-market.gmp.as_of" in result.message


# ---------------------------------------------------------------- cutoff (D2, never retroactive)

def test_evaluation_before_window_end_is_not_available(repo):
    result = _verify(repo, _write_fixture(repo), evaluation="2026-10-15T13:17:00Z")
    assert result.result == RESULT_NOT_AVAILABLE_BY_CUTOFF


def test_evaluation_without_timezone_is_not_available(repo):
    result = _verify(repo, _write_fixture(repo), evaluation="2026-10-15T14:00:00")
    assert result.result == RESULT_NOT_AVAILABLE_BY_CUTOFF


def test_window_missing_offset_fails(repo):
    pin = _write_fixture(repo, window={"notBefore": "2026-10-15T13:15:14.096",
                                       "notAfter": "2026-10-15T13:17:58.770"})
    result = _verify(repo, pin)
    assert result.result == RESULT_FAILED and "window" in result.message


def test_inverted_window_fails(repo):
    pin = _write_fixture(repo, window={"notBefore": "2026-10-15T13:20:00Z",
                                       "notAfter": "2026-10-15T13:10:00Z"})
    assert _verify(repo, pin).result == RESULT_FAILED


# ---------------------------------------------------------------- A15 record mapping

def _record_with_link(*, pin_uri, pairs, market=None, evaluation=EVAL_OK):
    """A real evaluated record whose GMP block and registry carry the link."""
    document = json.loads((REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json").read_text(encoding="utf-8"))
    document["company_name"] = "Tonbo Imaging India Limited"
    document["market"]["gmp"] = market or _gmp()
    record = run(document, load_config(CONFIG_PATH)).record
    registry_sources = copy.deepcopy(record.evidence.get("sources", []))
    registry_sources = [s for s in registry_sources if s.get("source_id") != SRC]
    registry_sources.append(_source(pin_uri))
    registry_items = [item for item in record.evidence.get("evidence", []) if not str(item.get("evidence_id", "")).startswith("EV-market.gmp") and item.get("evidence_id") != "EV-company_name"]
    for key, entry in pairs:
        registry_items.append({"evidence_id": f"EV-{key}", "source_id": entry["source_id"], "locator": entry["locator"],
                               "quoted_text": entry["quote"], "extraction_method": "MANUAL_ENTRY"})
    evidence = dict(record.evidence, sources=registry_sources, evidence=registry_items)
    snapshot = copy.deepcopy(record.input_snapshot)
    snapshot["input"]["company_name"] = "Tonbo Imaging India Limited"
    snapshot["input"]["market"]["gmp"] = market or _gmp()
    linked = dataclasses.replace(record, evidence=evidence, input_snapshot=snapshot, evaluation_timestamp=evaluation)
    _UNLINKED[id(linked)] = record.evidence  # the same scored snapshot, without the link
    return linked


_UNLINKED: dict = {}


def _without_link(result):
    """Scoring and everything else. The A9 reason and A9 diagnostics are checked separately above."""
    copy_ = {k: v for k, v in result.items() if k != "outcome_resolution"}
    copy_["diagnostics"] = [d for d in result["diagnostics"] if not d["code"].startswith("A9_GMP")]
    return copy_


def _gmp_link_digests(payload):
    return [d for d in payload["integrity"]["digests"] if d["digest_id"].startswith("gmp-link-")]


def _link_diagnostics(payload):
    return [d for d in payload["result"]["diagnostics"] if d["code"] == LINK_DIAGNOSTIC_CODE]


def test_unlinked_record_is_unchanged_and_has_no_link_diagnostic():
    document = json.loads((REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json").read_text(encoding="utf-8"))
    record = run(document, load_config(CONFIG_PATH)).record
    payload = build_evaluation_record_v1(record)
    assert _link_diagnostics(payload) == []


def test_verified_link_is_mapped_to_digests_window_and_one_diagnostic(repo):
    pin = _write_fixture(repo)
    record = _record_with_link(pin_uri=pin, pairs=_pairs())
    payload = build_evaluation_record_v1(record, repo_root=repo)
    diagnostics = _link_diagnostics(payload)
    assert len(diagnostics) == 1 and "Result: VERIFIED." in diagnostics[0]["message"]
    digests = _gmp_link_digests(payload)
    assert len(digests) == 2
    assert {d["subject_kind"] for d in digests} == {"RAW_ARTIFACT_BYTES"}
    assert all(len(d["digest_value"]) == 64 and d["digest_value"] == d["digest_value"].lower() for d in digests)
    source = next(s for s in payload["sources"] if s["source_id"] == SRC)
    window = [t for t in source["timestamps"] if t["kind"] == "LOCAL_RETRIEVED_AT"]
    assert window and window[0]["state"] == "UNKNOWN"
    assert window[0]["source_text"] == "2026-10-15T13:15:14.096Z/2026-10-15T13:17:58.770Z"
    assert "normalized_utc" not in window[0]
    # The link never changes scoring or the A9 outcome: compare with the same record unlinked.
    unlinked = build_evaluation_record_v1(dataclasses.replace(record, evidence=_UNLINKED[id(record)]), repo_root=repo)
    linked_outcome = payload["result"]["outcome_resolution"]
    unlinked_outcome = unlinked["result"]["outcome_resolution"]
    assert linked_outcome["state"] == unlinked_outcome["state"]
    assert linked_outcome["reason"]["code"] == unlinked_outcome["reason"]["code"] == "SOURCE_UNQUALIFIED"
    assert "final_outcome" not in payload["result"]
    # The reason may now cite the linked GMP quotes, and nothing else changes.
    added = set(linked_outcome["reason"]["evidence_refs"]) - set(unlinked_outcome["reason"]["evidence_refs"])
    assert added <= {"EV-company_name", "EV-market.gmp.pct", "EV-market.gmp.as_of"}
    assert _without_link(payload["result"]) == _without_link(unlinked["result"])


def test_failed_link_is_a_nonterminal_diagnostic_and_keeps_verified_bytes(repo):
    # The pct mismatch fails after D1: the verified bytes are still recorded, and A9 is unchanged.
    pin = _write_fixture(repo)
    record = _record_with_link(pin_uri=pin, pairs=_pairs(), market=_gmp(pct=70.0))
    payload = build_evaluation_record_v1(record, repo_root=repo)
    diagnostics = _link_diagnostics(payload)
    assert len(diagnostics) == 1 and "Result: FAILED." in diagnostics[0]["message"]
    assert len(_gmp_link_digests(payload)) == 2


def test_value_changed_after_linkage_fails_closed_in_the_same_projection(repo):
    # Simulates an assembly step that alters the scored value after the quote was taken.
    pin = _write_fixture(repo)
    record = _record_with_link(pin_uri=pin, pairs=_pairs())
    snapshot = copy.deepcopy(record.input_snapshot)
    snapshot["input"]["market"]["gmp"]["pct"] = 99.0
    payload = build_evaluation_record_v1(dataclasses.replace(record, input_snapshot=snapshot), repo_root=repo)
    assert "Result: FAILED." in _link_diagnostics(payload)[0]["message"]


def test_link_after_cutoff_is_reported_not_retroactive(repo):
    pin = _write_fixture(repo)
    record = _record_with_link(pin_uri=pin, pairs=_pairs(), evaluation="2026-10-15T13:17:00Z")
    payload = build_evaluation_record_v1(record, repo_root=repo)
    assert "Result: NOT_AVAILABLE_BY_CUTOFF." in _link_diagnostics(payload)[0]["message"]
    assert len(_gmp_link_digests(payload)) == 2


def test_pinned_retained_manifest_is_never_modified():
    assert _sha(ML_MANIFEST.read_bytes()) == "a4f83492455f4691159ba1f049547803cfa0db2aee248b7dbdfb4c990cfbb87d"
