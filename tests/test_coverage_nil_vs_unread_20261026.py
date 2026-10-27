"""Verified-nil vs unread: the coverage contract and its three consumers.

Report section 25.  ``capital_structure.pre_ipo_placements: []`` used to be
ambiguous -- it meant both "read the share-history schedule, nothing qualifies"
and "never read it" -- and the criterion awarded the favourable 2/2 in both
cases.  The contract added here is a per-field ``coverage`` map whose states are
DISCLOSED / VERIFIED_NIL / PARTIAL / UNREAD.  These tests pin:

* the schema accepts the map and the board-change events, and rejects invented
  states (so a typo cannot silently become UNKNOWN);
* a record *without* a coverage map keeps the v1.5 behaviour, so published
  results stay reproducible;
* only DISCLOSED and VERIFIED_NIL produce a placement bucket, and only
  VERIFIED_NIL is allowed to be a scored zero;
* the builder derives ``kmp_exits_2y`` from the dated events instead of taking
  a number on trust, and never turns "unread" into zero.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from conftest import EVAL_AT
from ipo_screening.canonical_input import build_canonical_input
from ipo_screening.derived import derive
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import RawExtraction
from ipo_screening.pipeline import load_config
from ipo_screening.post_listing.v16_implementation import verify_frozen_core, verify_golden_result
from ipo_screening.schema_validation import validate_schema

COVERAGE_STATES = {"DISCLOSED", "VERIFIED_NIL", "PARTIAL", "UNREAD"}


def _doc():
    return SimpleNamespace(
        source_id="RHP-TEST-COV",
        company_name="Coverage Test Limited",
        to_source_ref_dict=lambda: {
            "source_id": "RHP-TEST-COV",
            "source_type": "RHP",
            "uri": "coverage-test.json",
        },
    )


def _builder(extractions=(), reference_base=None):
    return CanonicalInputBuilder(
        doc=_doc(),
        extractions=list(extractions),
        reference_base=reference_base,
        allow_fixture_fallbacks=False,
    )


def _canonical(placements=(), coverage=None):
    raw = {
        "ipo_id": "COV-TEST",
        "company_name": "Coverage Test Limited",
        "issue": {"price_band_high": 100.0, "open_date": "2026-10-21"},
        "capital_structure": {"pre_ipo_placements": list(placements)},
        "governance": {},
        "financials": {"periods": []},
    }
    if coverage is not None:
        raw["coverage"] = coverage
    return build_canonical_input(raw)


def _bucket(canonical):
    config = load_config("config/ipo-config.v1.5.0.json")
    metrics = derive(canonical, config, peers=None, market=None).metrics
    return metrics["pre_ipo_placement_bucket"]


# ---------------------------------------------------------------------------
# 1-3. The schema contract
# ---------------------------------------------------------------------------


def test_schema_accepts_the_coverage_map(golden_input):
    doc = copy.deepcopy(golden_input)
    doc["coverage"] = {"capital_structure.pre_ipo_placements": "VERIFIED_NIL"}
    findings = validate_schema(doc)
    assert not [f for f in findings if "coverage" in str(f.location)], findings


@pytest.mark.parametrize("state", sorted(COVERAGE_STATES))
def test_schema_accepts_each_state(golden_input, state):
    doc = copy.deepcopy(golden_input)
    doc["coverage"] = {"capital_structure.pre_ipo_placements": state}
    assert not [f for f in validate_schema(doc) if "coverage" in str(f.location)]


def test_schema_rejects_an_invented_state(golden_input):
    doc = copy.deepcopy(golden_input)
    doc["coverage"] = {"capital_structure.pre_ipo_placements": "PROBABLY_NONE"}
    findings = [f for f in validate_schema(doc) if "coverage" in str(f.location)]
    assert findings, "an invented coverage state must not validate"


def test_schema_accepts_board_change_events(golden_input):
    doc = copy.deepcopy(golden_input)
    doc["governance"]["board_changes"] = [
        {
            "name": "Ramesh Abhishek",
            "role": "independent director",
            "event": "resignation",
            "date": "2024-07-12",
            "reason": "Resignation due to personal commitments",
        }
    ]
    assert not [f for f in validate_schema(doc) if "board_changes" in str(f.location)]


def test_schema_rejects_an_event_without_a_type_or_date(golden_input):
    for bad in (
        [{"date": "2024-07-12"}],
        [{"event": "resignation"}],
        [{"event": "sacked", "date": "2024-07-12"}],
        [{"event": "resignation", "date": "12/07/2024"}],
    ):
        doc = copy.deepcopy(golden_input)
        doc["governance"]["board_changes"] = bad
        assert [f for f in validate_schema(doc) if "board_changes" in str(f.location)], bad


# ---------------------------------------------------------------------------
# 4-7. The placement bucket: nil must be verified before it scores
# ---------------------------------------------------------------------------


def test_legacy_record_without_coverage_keeps_v15_behaviour():
    """Backward compatibility: no map at all == the old answer, unchanged."""
    metric = _bucket(_canonical(placements=[], coverage=None))
    assert metric.is_value
    assert metric.value == "none_or_near_ipo"


def test_unread_section_is_unknown_not_none_or_near_ipo():
    metric = _bucket(_canonical(placements=[], coverage={"capital_structure.pre_ipo_placements": "UNREAD"}))
    assert not metric.is_value, metric
    assert "never verified" in (metric.reason or "")


def test_partially_examined_section_is_unknown():
    metric = _bucket(_canonical(placements=[], coverage={"capital_structure.pre_ipo_placements": "PARTIAL"}))
    assert not metric.is_value
    assert "share-capital history schedule was located" in (metric.reason or "")


def test_verified_nil_scores_the_favourable_bucket():
    metric = _bucket(
        _canonical(placements=[], coverage={"capital_structure.pre_ipo_placements": "VERIFIED_NIL"})
    )
    assert metric.is_value
    assert metric.value == "none_or_near_ipo"
    assert "no equity shares were issued below the offer price" in (metric.reason or "")


def test_disclosed_schedule_with_no_qualifying_rows_is_a_read_nil(golden_input):
    """DISCLOSED means the schedule was read, so an empty list is a real nil."""
    doc = copy.deepcopy(golden_input)
    doc["capital_structure"]["pre_ipo_placements"] = []
    doc["coverage"] = {"capital_structure.pre_ipo_placements": "DISCLOSED"}
    metric = _bucket(build_canonical_input(doc))
    assert metric.is_value
    assert metric.value == "none_or_near_ipo"


def test_disclosed_placements_are_unchanged(golden_input):
    doc = copy.deepcopy(golden_input)
    doc["capital_structure"]["pre_ipo_placements"] = [{"date": "2026-09-01", "price": 208.0}]
    doc["coverage"] = {"capital_structure.pre_ipo_placements": "DISCLOSED"}
    metric = _bucket(build_canonical_input(doc))
    assert metric.is_value
    assert metric.value == "none_or_near_ipo"  # placed at the issue price: near_ipo


def test_a_deep_discount_placement_still_scores_zero():
    metric = _bucket(
        _canonical(
            placements=[{"date": "2026-08-01", "price": 30.0}],
            coverage={"capital_structure.pre_ipo_placements": "DISCLOSED"},
        )
    )
    assert metric.value == "deep_discount_12m"


# ---------------------------------------------------------------------------
# 8-11. The builder: coverage is emitted, counted and never defaulted
# ---------------------------------------------------------------------------


def test_builder_emits_coverage_map_from_reader_states():
    out = _builder(
        extractions=[
            RawExtraction(
                field_path="coverage.capital_structure.pre_ipo_placements",
                candidate_value="VERIFIED_NIL",
            ),
            RawExtraction(field_path="capital_structure.pre_ipo_placements", candidate_value=[]),
        ]
    ).build()
    assert out["coverage"]["capital_structure.pre_ipo_placements"] == "VERIFIED_NIL"


def test_builder_does_not_emit_coverage_when_the_reader_said_nothing():
    out = _builder().build()
    assert "coverage" not in out


def test_builder_derives_kmp_exits_from_dated_events():
    events = [
        {"name": "A Person", "role": "independent director", "event": "resignation", "date": "2024-11-01"},
        {"name": "B Person", "role": "independent director", "event": "resignation", "date": "2024-01-01"},
        {"name": "C Person", "role": "independent director", "event": "appointment", "date": "2025-05-01"},
    ]
    out = _builder(
        extractions=[
            RawExtraction(field_path="governance.board_changes", candidate_value=events),
            RawExtraction(field_path="coverage.governance.board_changes", candidate_value="DISCLOSED"),
            RawExtraction(field_path="issue.open_date", candidate_value="2026-10-21"),
        ]
    ).build()
    # Only the 2024-11-01 resignation is inside the 24 months before the offer.
    assert out["governance"]["kmp_exits_2y"] == 1
    assert out["governance"]["board_changes"] == events
    assert out["coverage"]["governance.kmp_exits_2y"] == "DISCLOSED"


def test_builder_keeps_kmp_exits_unknown_when_the_section_was_not_read():
    out = _builder(
        extractions=[
            RawExtraction(field_path="coverage.governance.board_changes", candidate_value="UNREAD"),
        ]
    ).build()
    assert out["governance"]["kmp_exits_2y"] is None
    assert out["coverage"]["governance.kmp_exits_2y"] == "UNREAD"


def test_builder_keeps_kmp_exits_unknown_when_no_offer_date_anchors_the_window():
    events = [
        {"name": "A Person", "role": "independent director", "event": "resignation", "date": "2024-11-01"}
    ]
    out = _builder(
        extractions=[
            RawExtraction(field_path="governance.board_changes", candidate_value=events),
            RawExtraction(field_path="coverage.governance.board_changes", candidate_value="DISCLOSED"),
        ]
    ).build()
    assert out["governance"]["kmp_exits_2y"] is None
    assert out["coverage"]["governance.kmp_exits_2y"] == "PARTIAL"


def test_builder_zero_from_a_verified_nil_table_is_a_verified_zero():
    out = _builder(
        extractions=[
            RawExtraction(field_path="coverage.governance.board_changes", candidate_value="VERIFIED_NIL"),
            RawExtraction(field_path="issue.open_date", candidate_value="2026-10-21"),
        ]
    ).build()
    assert out["governance"]["kmp_exits_2y"] == 0
    assert out["coverage"]["governance.kmp_exits_2y"] == "VERIFIED_NIL"


def test_builder_does_not_overwrite_a_curated_value_when_nothing_was_read():
    out = _builder(
        reference_base={"governance": {"kmp_exits_2y": 2}},
        extractions=[
            RawExtraction(field_path="coverage.governance.board_changes", candidate_value="UNREAD"),
        ],
    ).build()
    assert out["governance"]["kmp_exits_2y"] == 2
    assert "governance.kmp_exits_2y" not in out.get("coverage", {})


# ---------------------------------------------------------------------------
# 12-13. The criterion and the evaluation surface
# ---------------------------------------------------------------------------


def test_criterion_awards_no_points_for_an_unread_section(golden_input):
    from ipo_screening.pipeline import evaluate

    legacy = copy.deepcopy(golden_input)
    legacy["capital_structure"]["pre_ipo_placements"] = []
    legacy.pop("coverage", None)
    legacy_out = evaluate(legacy, load_config("config/ipo-config.v1.5.0.json"), mode="final", evaluation_datetime=EVAL_AT)

    unread = copy.deepcopy(legacy)
    unread["coverage"] = {"capital_structure.pre_ipo_placements": "UNREAD"}
    unread_out = evaluate(unread, load_config("config/ipo-config.v1.5.0.json"), mode="final", evaluation_datetime=EVAL_AT)

    def criterion(outcome):
        for module in outcome.record.to_dict()["score"]["modules"]:
            for item in module.get("criteria", []):
                if item.get("criterion_id") == "pre_ipo_placement":
                    return item
        raise AssertionError("pre_ipo_placement criterion missing")

    legacy_item, unread_item = criterion(legacy_out), criterion(unread_out)
    assert legacy_item["state"] == "SCORED"
    assert legacy_item.get("score", legacy_item.get("points")) == 2.0
    assert unread_item["state"] != "SCORED"
    assert not unread_item.get("score", unread_item.get("points"))
    assert unread_out.record.score["final_score"] == legacy_out.record.score["final_score"] - 2.0


def test_verified_nil_still_scores_and_frozen_core_is_intact():
    out = _builder(
        extractions=[
            RawExtraction(
                field_path="coverage.capital_structure.pre_ipo_placements",
                candidate_value="VERIFIED_NIL",
            ),
            RawExtraction(field_path="capital_structure.pre_ipo_placements", candidate_value=[]),
        ]
    ).build()
    assert out["coverage"]["capital_structure.pre_ipo_placements"] == "VERIFIED_NIL"
    assert verify_frozen_core()[0] is True
    assert verify_golden_result()[0] is True


def test_migration_note_is_recorded_in_the_schema():
    schema = json.load(open("schema/ipo-input.v1.5.schema.json", encoding="utf-8"))
    description = schema["properties"]["coverage"]["description"]
    assert "legacy" in description.lower()
    assert "UNREAD" in description
