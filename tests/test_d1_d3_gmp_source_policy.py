"""Focused coverage for the approved GMP source-policy decisions D1-D3.

Decision record: ``docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md`` §6.

These tests pin the approved evidence-artifact, availability and missing-versus-
zero rules, and the unchanged fail-closed A9 boundary. They qualify no GMP
source. A rendered capture is publisher-reported evidence only. Its hash attests
the retained file, not the publisher's authenticity, and a capture says nothing
about availability before it was obtained.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import shutil
from datetime import datetime, timedelta, timezone

import pytest

from conftest import EVAL_AT, REPO_ROOT, criterion, run
from ipo_screening.connectors.adapters import GmpSignalAdapter
from ipo_screening.connectors.coordinator import ConnectorCoordinator
from ipo_screening.connectors.interfaces import (
    GMP_FRESHNESS_POLICY,
    ConnectorPayloadError,
    FreshnessStatus,
)
from ipo_screening.errors import SchemaValidationError
from ipo_screening.evaluation_record import build_evaluation_record_v1
from ipo_screening.gmp_evidence import (
    A9_MISSING,
    A9_SOURCE_UNQUALIFIED,
    NOT_QUOTED_YET,
    PUBLISHER_REPORTED_RENDERED_CAPTURE,
    DisplayedGmpState,
    GmpEvidenceError,
    a9_reason_for,
    assess_capture,
    capture_obtained_by,
    classify_displayed_gmp,
    load_rendered_capture,
)

ML_DIR = REPO_ROOT / "evidence" / "gmp-observations" / "marketliveipogmp-tonbo-20261015"
ML_MANIFEST = ML_DIR / "capture-manifest.json"
ML_TONBO = "ml-tonbo-chunk-0"
ML_TONBO_FILE = "source-captures/marketliveipogmp-ipo-tonbo-imaging-india-chunk-0.md"
ML_TONBO_SHA256 = "33516F86EBB2CC7E53AD0491FFAD05BAE1CA7115C6008ECFB7F41A9C6C79705D"

#: End of ML-T's retrieval window in the capture manifest: by then it had been obtained.
ML_T_CAPTURED_BY = datetime(2026, 10, 15, 13, 17, 58, 770000, tzinfo=timezone.utc)
#: The reading's displayed stamp, "15 Oct, 4:02 pm IST". Never a capture time.
ML_T_DISPLAYED_STAMP = datetime(2026, 10, 15, 10, 32, tzinfo=timezone.utc)
IST = timezone(timedelta(hours=5, minutes=30))

EVAL_AT_TEXT = EVAL_AT.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture(scope="module")
def ml_capture():
    return load_rendered_capture(ML_MANIFEST, ML_TONBO)


def _package_copy(tmp_path, mutate=None):
    """Copy the retained MarketLiveIPOGMP package; the original is never modified."""
    target = tmp_path / "package"
    shutil.copytree(ML_DIR, target)
    manifest_path = target / "capture-manifest.json"
    if mutate is not None:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        mutate(data)
        manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def _tonbo_entry(data):
    return next(item for item in data["artifacts"] if item["id"] == ML_TONBO)


def _safe(document):
    """Non-triggering knockout inputs, as in test_evaluation_record_v1, so A9 decides."""
    result = copy.deepcopy(document)
    result["governance"]["auditor_opinion"] = "unqualified"
    result["governance"]["going_concern_uncertainty"] = False
    result["governance"]["sebi_ed_action_active"] = False
    result["governance"]["rpt_pct_of_revenue_growth"] = 1.0
    result["financials"]["contingent_liabilities_unquantified"] = False
    return result


def _connector_evaluation(golden_input, config, payload):
    """Normalise a GMP payload, reconcile it, and evaluate it in Final mode."""
    adapter = GmpSignalAdapter()
    snapshot = adapter.normalize(payload, reference_time=EVAL_AT, snapshot_id="D3-GMP")
    market_payload, _peer, sources = ConnectorCoordinator(adapters=[adapter]).reconcile_snapshots(
        [snapshot], reference_time=EVAL_AT
    )
    document = _safe(golden_input)
    document["market"]["gmp"] = market_payload["gmp"]
    document["_sources"].extend({k: v for k, v in source.items() if k != "note"} for source in sources)
    outcome = run(document, config)
    return snapshot, market_payload["gmp"]["source_id"], build_evaluation_record_v1(outcome.record)


def _assert_final_withheld(result, code):
    assert result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert result["outcome_resolution"]["reason"]["code"] == code
    assert "final_outcome" not in result


# --------------------------------------------------------------------------
# D1 - a rendered capture plus its file hash, labelled publisher-reported
# --------------------------------------------------------------------------


def test_rendered_capture_is_labelled_publisher_reported_never_raw_or_authenticated(ml_capture):
    assert ml_capture.evidence_class == PUBLISHER_REPORTED_RENDERED_CAPTURE
    assert ml_capture.is_source_native is False
    assert ml_capture.authenticates_publisher is False
    assert ml_capture.verifies_dealer_quote is False
    assert ml_capture.label == (
        "Publisher-reported GMP observation: rendered-text capture of "
        "https://marketliveipogmp.com/ipo/tonbo-imaging-india, not provider response bytes. "
        "Its SHA-256 attests the integrity of the retained file only; it does not "
        "authenticate the publisher or verify a dealer quote."
    )
    # The class is not a constructor argument, so a capture cannot be relabelled.
    with pytest.raises(TypeError):
        dataclasses.replace(ml_capture, evidence_class="RAW_PROVIDER_BYTES")


@pytest.mark.parametrize("raw_flag", [True, None, "false"])
def test_only_a_declared_rendered_capture_is_a_d1_artifact(tmp_path, raw_flag):
    def mutate(data):
        if raw_flag is None:
            data["captureMethod"].pop("rawProviderResponseBytesCaptured")
        else:
            data["captureMethod"]["rawProviderResponseBytesCaptured"] = raw_flag

    with pytest.raises(GmpEvidenceError, match="rendered-text capture"):
        load_rendered_capture(_package_copy(tmp_path, mutate), ML_TONBO)


def test_hash_verification_applies_to_the_declared_retained_artifact(ml_capture):
    retained = (ML_DIR / ML_TONBO_FILE).read_bytes()
    assert ml_capture.artifact_file == ML_TONBO_FILE
    assert ml_capture.declared_bytes == len(retained) == 1693
    assert ml_capture.declared_sha256 == ML_TONBO_SHA256
    assert ml_capture.computed_sha256 == hashlib.sha256(retained).hexdigest().upper() == ML_TONBO_SHA256
    assert ml_capture.integrity_verified is True
    assert ml_capture.hash_subject == f"exact bytes of the retained file {ML_TONBO_FILE} declared in capture-manifest.json"


def test_an_altered_missing_or_misdeclared_artifact_fails_integrity(tmp_path):
    # Same length, one digit changed: the hash, not the size, catches it.
    altered = _package_copy(tmp_path / "altered")
    capture_file = altered.parent / ML_TONBO_FILE
    capture_file.write_bytes(capture_file.read_bytes().replace("₹500".encode(), "₹501".encode(), 1))
    tampered = load_rendered_capture(altered, ML_TONBO)
    assert tampered.computed_sha256 != ML_TONBO_SHA256
    assert tampered.integrity_verified is False
    assert not assess_capture(tampered, "₹501", evaluation_at=ML_T_CAPTURED_BY).eligible_for_cutoff_consideration

    missing = _package_copy(tmp_path / "missing")
    (missing.parent / ML_TONBO_FILE).unlink()
    absent = load_rendered_capture(missing, ML_TONBO)
    assert absent.computed_sha256 is None
    assert absent.integrity_verified is False

    misdeclared = _package_copy(tmp_path / "misdeclared", lambda d: _tonbo_entry(d).update(sha256="0" * 64))
    assert load_rendered_capture(misdeclared, ML_TONBO).integrity_verified is False


@pytest.mark.parametrize(
    "change",
    [
        {"file": "../outside.md"},
        {"sha256": "not-a-digest"},
        {"bytes": "1693"},
        {"file": ""},
    ],
)
def test_an_artifact_declaration_d1_cannot_use_is_rejected(tmp_path, change):
    manifest = _package_copy(tmp_path, lambda d: _tonbo_entry(d).update(change))
    with pytest.raises(GmpEvidenceError):
        load_rendered_capture(manifest, ML_TONBO)


def test_an_undeclared_artifact_is_rejected():
    with pytest.raises(GmpEvidenceError, match="not declared"):
        load_rendered_capture(ML_MANIFEST, "ml-tonbo-chunk-9")


# --------------------------------------------------------------------------
# D2 - the capture must have been obtained at or before the evaluation timestamp
# --------------------------------------------------------------------------


@pytest.mark.parametrize("evaluation_at", [ML_T_CAPTURED_BY, ML_T_CAPTURED_BY.astimezone(IST)])
def test_capture_obtained_at_the_evaluation_timestamp_is_eligible_for_cutoff_consideration_only(
    ml_capture, evaluation_at
):
    assert ml_capture.retrieved_not_after == ML_T_CAPTURED_BY
    assert capture_obtained_by(ml_capture, evaluation_at) is True

    assessment = assess_capture(ml_capture, "₹500", evaluation_at=evaluation_at)
    assert assessment.displayed_state is DisplayedGmpState.AMOUNT
    assert assessment.displayed_amount == 500.0
    assert assessment.displayed_in_capture is True
    assert assessment.eligible_for_cutoff_consideration is True
    # Eligible for cutoff consideration is not qualification: A9 stays nonterminal.
    assert assessment.a9_reason == A9_SOURCE_UNQUALIFIED


@pytest.mark.parametrize(
    "evaluation_at",
    [
        ML_T_DISPLAYED_STAMP,  # the displayed reading time itself
        ML_T_DISPLAYED_STAMP + timedelta(hours=1),
        datetime(2026, 10, 15, 13, 15, 14, 96000, tzinfo=timezone.utc),  # window start
        datetime(2026, 10, 15, 13, 16, tzinfo=timezone.utc),  # inside the window
        ML_T_CAPTURED_BY - timedelta(milliseconds=1),
    ],
)
def test_capture_obtained_after_the_evaluation_is_ineligible_despite_an_earlier_displayed_stamp(
    ml_capture, evaluation_at
):
    # Every one of these instants is after the reading's displayed 4:02 pm IST
    # stamp, but none is after the capture was certainly obtained.
    assert evaluation_at >= ML_T_DISPLAYED_STAMP
    assert capture_obtained_by(ml_capture, evaluation_at) is False
    assessment = assess_capture(ml_capture, "₹500", evaluation_at=evaluation_at)
    assert assessment.eligible_for_cutoff_consideration is False
    assert assessment.a9_reason == A9_SOURCE_UNQUALIFIED


def test_a_later_capture_does_not_retroactively_qualify_an_earlier_evaluation(tmp_path, ml_capture):
    def add_recapture(data):
        recapture = dict(_tonbo_entry(data), id="ml-tonbo-recapture")
        # The §13.1 R7 recapture window; its transcription was byte-identical.
        recapture["retrievalWindowUtc"] = {
            "notBefore": "2026-10-15T15:57:54.203Z",
            "notAfter": "2026-10-15T15:57:59.792Z",
        }
        data["artifacts"].append(recapture)

    later = load_rendered_capture(_package_copy(tmp_path, add_recapture), "ml-tonbo-recapture")
    assert later.integrity_verified is True
    assert later.computed_sha256 == ml_capture.computed_sha256  # same bytes, same reading

    before_both = datetime(2026, 10, 15, 13, 0, tzinfo=timezone.utc)
    between = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)
    after_both = datetime(2026, 10, 15, 16, 0, tzinfo=timezone.utc)

    assert not capture_obtained_by(ml_capture, before_both)
    assert not capture_obtained_by(later, before_both)
    assert capture_obtained_by(ml_capture, between)
    assert not capture_obtained_by(later, between)  # identical content, still too late
    assert capture_obtained_by(later, after_both)


def test_capture_time_needs_explicit_offsets_and_is_never_the_publisher_stamp(tmp_path, ml_capture):
    naive = ML_T_CAPTURED_BY.replace(tzinfo=None) + timedelta(hours=1)
    assert capture_obtained_by(ml_capture, naive) is False

    offset_less = _package_copy(
        tmp_path / "offset-less",
        lambda d: _tonbo_entry(d).update(
            retrievalWindowUtc={"notBefore": "2026-10-15T13:15:14.096", "notAfter": "2026-10-15T13:17:58.770"}
        ),
    )
    no_window = _package_copy(tmp_path / "no-window", lambda d: _tonbo_entry(d).pop("retrievalWindowUtc"))
    inverted = _package_copy(
        tmp_path / "inverted",
        lambda d: _tonbo_entry(d).update(
            retrievalWindowUtc={"notBefore": "2026-10-15T13:17:58.770Z", "notAfter": "2026-10-15T13:15:14.096Z"}
        ),
    )
    much_later = datetime(2026, 10, 16, tzinfo=timezone.utc)
    for manifest in (offset_less, no_window, inverted):
        capture = load_rendered_capture(manifest, ML_TONBO)
        # The manifest still records the publisher's normalised stamp, but it is
        # not a capture time and is never used as one.
        assert json.loads(manifest.read_text(encoding="utf-8"))["publisherIssuePage"]["normalizedSourceTimeUtc"]
        assert capture.integrity_verified is True
        assert capture.retrieved_not_after is None
        assert capture_obtained_by(capture, much_later) is False


# --------------------------------------------------------------------------
# D3 - "Not quoted yet" is MISSING; a displayed zero is SOURCE_UNQUALIFIED
# --------------------------------------------------------------------------


@pytest.mark.parametrize("display", [NOT_QUOTED_YET, f"  {NOT_QUOTED_YET} "])
def test_not_quoted_yet_maps_to_missing(display):
    # The exact state shown by the publisher (retained home-page capture).
    home = (ML_DIR / "source-captures" / "marketliveipogmp-home-chunk-0.md").read_text(encoding="utf-8")
    assert NOT_QUOTED_YET in home
    assert classify_displayed_gmp(display) == (DisplayedGmpState.MISSING, None)
    assert a9_reason_for(DisplayedGmpState.MISSING) == A9_MISSING


@pytest.mark.parametrize(
    "display, unit",
    [("₹0", "₹"), ("₹ 0", "₹"), ("₹0.00", "₹"), ("0", "₹"), (0, "₹"), (0.0, "₹"), ("-0", "₹"), ("0.0%", "%")],
)
def test_displayed_zero_maps_to_source_unqualified(display, unit):
    hero_motors = (ML_DIR / "source-captures" / "marketliveipogmp-ipo-hero-motors-chunk-0.md").read_text(
        encoding="utf-8"
    )
    assert "₹0" in hero_motors  # the publisher displays a ₹0 reading
    state, amount = classify_displayed_gmp(display, unit=unit)
    assert (state, amount) == (DisplayedGmpState.ZERO, 0.0)
    assert a9_reason_for(state) == A9_SOURCE_UNQUALIFIED


@pytest.mark.parametrize(
    "display, unit",
    [
        ("₹ --", "₹"),
        ("--", "₹"),
        ("—", "₹"),
        ("N/A", "₹"),
        ("", "₹"),
        ("not quoted yet", "₹"),  # not the exact observed state
        ("Not quoted", "₹"),
        ("₹", "₹"),
        ("₹abc", "₹"),
        ("-₹-2", "₹"),
        ("₹500+71.4%", "₹"),
        ("500%", "₹"),
        ("₹500", "%"),
        ("nan", "₹"),
        ("inf", "₹"),
        (True, "₹"),
        ([], "₹"),
        ({}, "₹"),
    ],
)
def test_ambiguous_or_malformed_displays_fail_closed(display, unit):
    state, amount = classify_displayed_gmp(display, unit=unit)
    assert (state, amount) == (DisplayedGmpState.MALFORMED, None)
    # Never coerced into a value, and never treated as the explicit MISSING state.
    assert a9_reason_for(state) == A9_SOURCE_UNQUALIFIED


@pytest.mark.parametrize(
    "display, unit, expected",
    [
        ("₹500", "₹", 500.0),
        ("₹-51", "₹", -51.0),
        ("-₹2", "₹", -2.0),
        ("₹14.5", "₹", 14.5),
        ("₹1,450", "₹", 1450.0),
        (35, "₹", 35.0),
        ("+71.4%", "%", 71.4),
    ],
)
def test_well_formed_non_zero_amounts_are_candidates_only(display, unit, expected):
    state, amount = classify_displayed_gmp(display, unit=unit)
    assert (state, amount) == (DisplayedGmpState.AMOUNT, expected)
    assert a9_reason_for(state) == A9_SOURCE_UNQUALIFIED


def test_assessed_value_must_occur_in_the_verified_capture(ml_capture):
    assessment = assess_capture(ml_capture, "₹600", evaluation_at=ML_T_CAPTURED_BY)
    assert assessment.displayed_state is DisplayedGmpState.AMOUNT
    assert assessment.displayed_in_capture is False
    assert assessment.eligible_for_cutoff_consideration is False

    not_quoted = assess_capture(ml_capture, NOT_QUOTED_YET, evaluation_at=ML_T_CAPTURED_BY)
    assert not_quoted.a9_reason == A9_MISSING
    assert not_quoted.eligible_for_cutoff_consideration is False


# --------------------------------------------------------------------------
# D3 and D2 on the connector path, through to the A9 Final gate
# --------------------------------------------------------------------------


def test_connector_maps_not_quoted_yet_to_missing_and_a9_withholds_final(golden_input, config):
    snapshot, _source_id, record = _connector_evaluation(
        golden_input,
        config,
        {"as_of": EVAL_AT_TEXT, "retrieval_timestamp": EVAL_AT_TEXT, "gmp_rupees": NOT_QUOTED_YET},
    )
    assert snapshot.normalized_data["gmp_rupees"] is None
    assert snapshot.normalized_data["pct"] is None
    _assert_final_withheld(record["result"], A9_MISSING)


@pytest.mark.parametrize(
    "values",
    [
        {"gmp_rupees": "₹0", "gmp_pct": "0.0%"},
        {"gmp_rupees": "₹0"},  # rupee-only: a zero premium is 0% of any price
        {"gmp_rupees": 0, "gmp_pct": 0},
    ],
)
def test_connector_keeps_a_displayed_zero_so_a9_reports_source_unqualified(golden_input, config, values):
    snapshot, _source_id, record = _connector_evaluation(
        golden_input, config, {"as_of": EVAL_AT_TEXT, "retrieval_timestamp": EVAL_AT_TEXT, **values}
    )
    assert snapshot.normalized_data["gmp_rupees"] == 0.0
    assert snapshot.normalized_data["pct"] == 0.0  # present, not dropped as missing
    _assert_final_withheld(record["result"], A9_SOURCE_UNQUALIFIED)


@pytest.mark.parametrize(
    "values",
    [
        {"gmp_rupees": "₹ --"},
        {"gmp_rupees": "N/A"},
        {"gmp": "abc"},
        {"gmp_pct": "n/a"},
        {"gmp_rupees": True},
        {"gmp_rupees": NOT_QUOTED_YET, "gmp_pct": 15.0},
        {"gmp_rupees": NOT_QUOTED_YET, "trend": "rising"},
        {"gmp_rupees": 0, "gmp_pct": 15.0},
        {"gmp_rupees": "₹500", "gmp_pct": "0.0%"},
    ],
)
def test_connector_rejects_malformed_or_contradictory_gmp_displays(values):
    with pytest.raises(ConnectorPayloadError, match=r"\(D3\)"):
        GmpSignalAdapter().normalize({"as_of": EVAL_AT_TEXT, **values}, reference_time=EVAL_AT)


@pytest.mark.parametrize(
    "values, rupees, pct, trend",
    [
        ({"gmp_rupees": 35.0, "gmp_pct": 15.91, "trend": "flat"}, 35.0, 15.91, "flat"),
        ({"gmp_rupees": "35"}, 35.0, None, None),
        ({"gmp_rupees": 25.0, "trend": "falling"}, 25.0, None, "falling"),
        ({"gmp_rupees": None, "gmp_pct": None}, None, None, None),
        ({"gmp_rupees": "UNKNOWN", "gmp_pct": "null"}, None, None, None),
        ({"gmp_rupees": ""}, None, None, None),
        ({"gmp_rupees": "₹500", "gmp_pct": "+71.4%"}, 500.0, 71.4, None),
    ],
)
def test_connector_keeps_existing_numeric_and_no_value_behaviour(values, rupees, pct, trend):
    data = GmpSignalAdapter().normalize({"as_of": EVAL_AT_TEXT, **values}, reference_time=EVAL_AT).normalized_data
    assert (data["gmp_rupees"], data["pct"], data["trend"]) == (rupees, pct, trend)


def test_connector_never_invents_a_capture_time(golden_input, config):
    snapshot, source_id, record = _connector_evaluation(
        golden_input, config, {"as_of": EVAL_AT_TEXT, "gmp_rupees": 35.0, "gmp_pct": 15.91}
    )
    assert snapshot.retrieval_timestamp is None
    assert snapshot.to_dict()["retrieval_timestamp"] is None
    assert "retrieval_timestamp" not in snapshot.to_source_ref()
    source = next(item for item in record["sources"] if item["source_id"] == source_id)
    assert all(fact["kind"] != "LOCAL_RETRIEVED_AT" for fact in source["timestamps"])
    _assert_final_withheld(record["result"], A9_SOURCE_UNQUALIFIED)

    recorded = "2026-10-05T11:59:00Z"
    snapshot, source_id, record = _connector_evaluation(
        golden_input,
        config,
        {"as_of": EVAL_AT_TEXT, "retrieval_timestamp": recorded, "gmp_rupees": 35.0, "gmp_pct": 15.91},
    )
    assert snapshot.retrieval_timestamp == recorded
    assert snapshot.to_source_ref()["retrieval_timestamp"] == recorded
    source = next(item for item in record["sources"] if item["source_id"] == source_id)
    retrieved = [fact for fact in source["timestamps"] if fact["kind"] == "LOCAL_RETRIEVED_AT"]
    assert [fact["source_text"] for fact in retrieved] == [recorded]
    # A recorded capture time does not qualify the observation either.
    _assert_final_withheld(record["result"], A9_SOURCE_UNQUALIFIED)


# --------------------------------------------------------------------------
# D3 on the evaluation-input path; A9 and A17 unchanged
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "gmp_values, code",
    [
        ({"pct": 0, "trend": None}, A9_SOURCE_UNQUALIFIED),  # a displayed zero
        ({"pct": 0.0}, A9_SOURCE_UNQUALIFIED),
        ({"pct": None, "trend": None}, A9_MISSING),  # "Not quoted yet": no value
    ],
)
def test_evaluation_input_zero_is_source_unqualified_and_no_value_is_missing(golden_input, config, gmp_values, code):
    document = _safe(golden_input)
    document["market"]["gmp"].update(as_of=EVAL_AT_TEXT, **gmp_values)
    result = build_evaluation_record_v1(run(document, config).record)["result"]
    _assert_final_withheld(result, code)


@pytest.mark.parametrize("display", ["₹0", NOT_QUOTED_YET, "N/A"])
def test_evaluation_input_rejects_a_display_string_before_scoring(golden_input, config, display):
    document = _safe(golden_input)
    document["market"]["gmp"]["pct"] = display
    with pytest.raises(SchemaValidationError):
        run(document, config)


def test_a17_age_limit_and_trend_label_policy_are_unchanged(golden_input, config):
    assert GMP_FRESHNESS_POLICY.max_age_hours == 24.0
    assert GMP_FRESHNESS_POLICY.allow_future_tolerance_seconds == 0.0
    assert GMP_FRESHNESS_POLICY.require_explicit_offset is True

    adapter = GmpSignalAdapter()

    def freshness(as_of):
        return adapter.normalize({"as_of": as_of, "gmp_rupees": "₹0"}, reference_time=EVAL_AT).freshness

    assert freshness("2026-10-04T12:00:00Z") == FreshnessStatus.FRESH  # exactly 24 h old
    assert freshness("2026-10-04T11:59:59Z") == FreshnessStatus.STALE
    assert freshness("2026-10-05T12:00:01Z") == FreshnessStatus.FUTURE

    def trend(**values):
        return adapter.normalize({"as_of": EVAL_AT_TEXT, **values}, reference_time=EVAL_AT).normalized_data["trend"]

    assert trend(gmp_rupees="₹500", trend="rising") == "strong"
    assert trend(gmp_rupees="₹500") is None  # never derived from the amount
    assert trend(gmp_rupees="₹0", trend="sideways") is None

    # Scoring still reads only the publisher-supplied label; a zero pct changes nothing.
    document = copy.deepcopy(golden_input)
    document["market"]["gmp"].update(as_of=EVAL_AT_TEXT, pct=0, trend="strong")
    scored = criterion(run(document, config), "gmp_trend")
    assert (scored.state, scored.score) == ("SCORED", 2.0)
    document["market"]["gmp"]["as_of"] = "2026-10-04T11:59:59Z"  # over 24 h old
    assert criterion(run(document, config), "gmp_trend").state == "UNKNOWN"
