"""A17 focused coverage: GMP cutoff (A17-1), maximum age (A17-2), trend labels (A17-3).

Decision record: ``handoff/decisions/A17-gmp-cutoff-freshness-and-trend-labels.md``.
These tests pin the approved policy and the fail-closed A9 boundary. They do not
qualify any GMP source: A9 still withholds Final for every GMP observation.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone

import pytest
from jsonschema import FormatChecker

from conftest import EVAL_AT, criterion, metric, run
from ipo_screening.connectors.adapters import (
    GmpSignalAdapter,
    MarketRegimeAdapter,
    OfficialSubscriptionAdapter,
)
from ipo_screening.connectors.coordinator import ConnectorCoordinator
from ipo_screening.connectors.interfaces import (
    GMP_FRESHNESS_POLICY,
    MARKET_FRESHNESS_POLICY,
    FreshnessStatus,
    SourceClass,
    StaleDataError,
)
from ipo_screening.errors import SchemaValidationError
from ipo_screening.evaluation_record import build_evaluation_record_v1
from ipo_screening.gmp_policy import apply_gmp_cutoff
from ipo_screening.post_listing.v16_implementation import GOLDEN_RESULT_HASH
from ipo_screening.snapshots import build_market_snapshot

# jsonschema checks "date-time" only when its optional RFC 3339 dependency is
# installed. The pinned environment does not install it, so malformed and
# offset-less strings reach the market snapshot. Either way they must fail closed.
DATE_TIME_FORMAT_ENFORCED = "date-time" in FormatChecker().checkers

#: Connector reference (evaluation) time used by the existing connector tests.
REF = datetime(2026, 10, 4, 20, 0, 0, tzinfo=timezone.utc)

FUTURE_REASON = "block as-of {} is in the future relative to the evaluation"


def _gmp_block(outcome):
    return next(b for b in outcome.record.market_snapshot["blocks"] if b["block"] == "gmp")


def _with_gmp(document, **fields):
    result = copy.deepcopy(document)
    result["market"]["gmp"].update(fields)
    return result


def _safe(document):
    """Non-triggering knockout inputs, as in test_evaluation_record_v1, so A9 decides."""
    result = copy.deepcopy(document)
    result["governance"]["auditor_opinion"] = "unqualified"
    result["governance"]["going_concern_uncertainty"] = False
    result["governance"]["sebi_ed_action_active"] = False
    result["governance"]["rpt_pct_of_revenue_growth"] = 1.0
    result["financials"]["contingent_liabilities_unquantified"] = False
    return result


def _gmp_snapshot(as_of, **extra):
    return GmpSignalAdapter().normalize({"as_of": as_of, "gmp_rupees": 35.0, **extra}, reference_time=REF)


# --------------------------------------------------------------------------
# A17-1 - the evaluation timestamp is the GMP eligibility cutoff
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "as_of",
    [
        "2026-10-05T12:00:00Z",  # exactly the evaluation timestamp
        "2026-10-05T17:30:00+05:30",  # the same instant written in IST
    ],
)
def test_gmp_observation_exactly_at_the_cutoff_is_eligible(golden_input, config, as_of):
    outcome = run(_with_gmp(golden_input, as_of=as_of), config)

    assert _gmp_block(outcome)["status"] == "FRESH"
    assert metric(outcome, "gmp_bucket").value == "flat"
    assert criterion(outcome, "gmp_trend").state == "SCORED"


@pytest.mark.parametrize(
    "as_of",
    [
        "2026-10-05T12:00:01Z",  # one second after the cutoff
        "2026-10-05T12:30:00Z",  # inside the former one-hour allowance
        "2026-10-05T12:59:59Z",
        "2026-10-05T17:30:01+05:30",  # IST offset, one second after the cutoff
    ],
)
def test_gmp_observation_after_the_cutoff_is_ineligible_despite_the_former_allowance(
    golden_input, config, as_of
):
    outcome = run(_with_gmp(golden_input, as_of=as_of), config)
    block = _gmp_block(outcome)

    assert block["status"] == "STALE"
    assert block["reason"] == FUTURE_REASON.format(as_of)
    assert metric(outcome, "gmp_bucket").state == "UNKNOWN"
    assert criterion(outcome, "gmp_trend").state == "UNKNOWN"
    assert criterion(outcome, "gmp_trend").score is None


def test_gmp_more_than_one_hour_after_the_cutoff_keeps_the_existing_reason(golden_input, config):
    as_of = "2026-10-05T13:30:00Z"
    block = _gmp_block(run(_with_gmp(golden_input, as_of=as_of), config))

    assert block["status"] == "STALE"
    assert block["reason"] == FUTURE_REASON.format(as_of)


@pytest.mark.parametrize(
    "as_of, reason_fragment",
    [
        ("not-a-date", "is not a parseable timestamp"),
        # Offset-less: it would look one hour old only if UTC were assumed.
        ("2026-10-05T11:00:00", "has no explicit UTC offset"),
    ],
)
def test_malformed_or_offset_less_gmp_timestamp_fails_closed(golden_input, config, as_of, reason_fragment):
    document = _with_gmp(golden_input, as_of=as_of)
    if DATE_TIME_FORMAT_ENFORCED:
        with pytest.raises(SchemaValidationError):
            run(document, config)
        return

    outcome = run(document, config)
    block = _gmp_block(outcome)
    assert block["status"] == "STALE"
    assert reason_fragment in block["reason"]
    assert criterion(outcome, "gmp_trend").state == "UNKNOWN"


def test_missing_gmp_timestamp_fails_closed(golden_input, config):
    outcome = run(_with_gmp(golden_input, as_of=None), config)
    block = _gmp_block(outcome)

    assert block["status"] == "STALE"
    assert block["reason"] == "block has no as-of timestamp, so its currency cannot be established"
    assert criterion(outcome, "gmp_trend").state == "UNKNOWN"


def test_cutoff_is_not_applied_against_an_evaluation_time_without_a_timezone(golden_input):
    market = build_market_snapshot(golden_input["market"], evaluation_datetime=EVAL_AT, staleness_hours=24)
    assert market.block("gmp").status == "FRESH"

    demoted = apply_gmp_cutoff(market, evaluation_datetime=EVAL_AT.replace(tzinfo=None))

    assert demoted.block("gmp").status == "STALE"
    assert "cannot be applied" in demoted.block("gmp").reason


def test_cutoff_never_promotes_a_block_or_changes_an_eligible_one(golden_input):
    stale_raw = copy.deepcopy(golden_input["market"])
    stale_raw["gmp"]["as_of"] = "2026-10-03T12:00:00Z"
    stale = build_market_snapshot(stale_raw, evaluation_datetime=EVAL_AT, staleness_hours=24)
    eligible = build_market_snapshot(golden_input["market"], evaluation_datetime=EVAL_AT, staleness_hours=24)

    assert apply_gmp_cutoff(stale, evaluation_datetime=EVAL_AT) is stale
    assert apply_gmp_cutoff(eligible, evaluation_datetime=EVAL_AT) is eligible


def test_only_the_gmp_block_loses_the_generic_future_allowance(golden_input, config):
    document = copy.deepcopy(golden_input)
    for name in ("anchor", "subscription", "gmp", "regime"):
        document["market"][name]["as_of"] = "2026-10-05T12:30:00Z"

    statuses = {b["block"]: b["status"] for b in run(document, config).record.market_snapshot["blocks"]}

    assert statuses == {"anchor": "FRESH", "subscription": "FRESH", "gmp": "STALE", "regime": "FRESH"}


# --------------------------------------------------------------------------
# A17-2 - the existing 24-hour maximum age, relative to the evaluation timestamp
# --------------------------------------------------------------------------


def test_maximum_age_is_the_existing_24_hours_from_the_evaluation_timestamp(golden_input, config, raw_config):
    assert raw_config["thresholds"]["market_staleness_hours"] == 24

    at_limit = _with_gmp(golden_input, as_of="2026-10-04T12:00:00Z")
    over_limit = _with_gmp(golden_input, as_of="2026-10-04T11:59:59Z")

    assert _gmp_block(run(at_limit, config))["status"] == "FRESH"
    over = _gmp_block(run(over_limit, config))
    assert over["status"] == "STALE"
    assert over["reason"] == "block dated 2026-10-04T11:59:59Z is beyond the 24-hour staleness limit"
    # Same observation, evaluated one second later: the age is measured from the evaluation timestamp.
    later = run(at_limit, config, at=EVAL_AT + timedelta(seconds=1))
    assert _gmp_block(later)["status"] == "STALE"


def test_golden_result_hash_is_unchanged(golden_input, config):
    assert run(golden_input, config).record.result_hash == GOLDEN_RESULT_HASH


# --------------------------------------------------------------------------
# Connector freshness - consistent with A17-1 and A17-2
# --------------------------------------------------------------------------


def test_gmp_connector_uses_the_a17_policy_while_other_connectors_keep_theirs():
    assert GmpSignalAdapter().freshness_policy is GMP_FRESHNESS_POLICY
    assert GMP_FRESHNESS_POLICY.max_age_hours == MARKET_FRESHNESS_POLICY.max_age_hours == 24.0
    assert GMP_FRESHNESS_POLICY.allow_future_tolerance_seconds == 0.0
    assert OfficialSubscriptionAdapter().freshness_policy is MARKET_FRESHNESS_POLICY
    assert MarketRegimeAdapter().freshness_policy is MARKET_FRESHNESS_POLICY
    # The generic market policy keeps its existing behaviour.
    assert MARKET_FRESHNESS_POLICY.evaluate_freshness("2026-10-04T20:30:00Z", REF) == FreshnessStatus.FRESH
    assert MARKET_FRESHNESS_POLICY.evaluate_freshness("2026-10-04T19:00:00", REF) == FreshnessStatus.FRESH


@pytest.mark.parametrize(
    "as_of, expected",
    [
        ("2026-10-04T20:00:00Z", FreshnessStatus.FRESH),  # exactly at the reference time
        ("2026-10-05T01:30:00+05:30", FreshnessStatus.FRESH),  # the same instant in IST
        ("2026-10-04T20:00:01Z", FreshnessStatus.FUTURE),
        ("2026-10-04T20:30:00Z", FreshnessStatus.FUTURE),  # FRESH under the former allowance
        ("2026-10-03T20:00:00Z", FreshnessStatus.FRESH),  # exactly 24 h old
        ("2026-10-03T19:59:59Z", FreshnessStatus.STALE),
        ("2026-10-04T19:00:00", FreshnessStatus.MISSING),  # no offset: never assumed UTC
        (None, FreshnessStatus.MISSING),
    ],
)
def test_gmp_connector_freshness(as_of, expected):
    assert _gmp_snapshot(as_of).freshness == expected


def test_gmp_connector_freshness_needs_a_timezone_aware_reference_time():
    naive_ref = REF.replace(tzinfo=None)
    assert GMP_FRESHNESS_POLICY.evaluate_freshness("2026-10-04T20:00:00Z", naive_ref) == FreshnessStatus.MISSING


def test_gmp_connector_keeps_its_existing_error_for_a_malformed_timestamp():
    with pytest.raises(ValueError):
        _gmp_snapshot("not-a-date")


def test_strict_coordinator_rejects_a_gmp_observation_after_the_reference_time():
    coordinator = ConnectorCoordinator(strict_freshness=True)
    with pytest.raises(StaleDataError):
        coordinator.ingest_snapshot(
            {"as_of": "2026-10-04T20:30:00Z", "gmp_rupees": 35.0, "trend": "flat"},
            SourceClass.SECONDARY_TRACKER,
            reference_time=REF,
        )


# --------------------------------------------------------------------------
# A17-3 - publisher-supplied trend labels only
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label, expected",
    [
        ("strong", "strong"),
        ("flat", "flat"),
        ("falling", "falling"),
        ("Rising", "strong"),  # existing exact-match synonyms are unchanged
        (" STEADY ", "flat"),
        ("bearish", "falling"),
    ],
)
def test_supplied_trend_label_maps_to_an_accepted_label(label, expected):
    assert _gmp_snapshot("2026-10-04T20:00:00Z", trend=label).normalized_data["trend"] == expected


@pytest.mark.parametrize(
    "labels",
    [
        {},  # no label supplied
        {"trend": None},
        {"trend": "unknown"},
        {"trend": "sideways"},  # unsupported (previously passed through raw)
        {"trend": "Strong Upward"},  # not an exact accepted label or synonym
        {"trend": "stable/rising"},  # superseded v1.3 phrase: not implemented
        {"trend": "strong", "gmp_trend": "falling"},  # conflicting labels: ambiguous
        {"trend": "flat", "gmp_trend": "sideways"},  # one unmappable label: ambiguous
    ],
)
def test_missing_unsupported_or_ambiguous_trend_label_stays_unknown(labels):
    assert _gmp_snapshot("2026-10-04T20:00:00Z", **labels).normalized_data["trend"] is None


def test_agreeing_trend_labels_are_not_ambiguous():
    snapshot = _gmp_snapshot("2026-10-04T20:00:00Z", trend="up", gmp_trend="strong")
    assert snapshot.normalized_data["trend"] == "strong"


def test_trend_is_never_derived_from_gmp_values_movement_history_or_issue_price():
    snapshot = _gmp_snapshot(
        "2026-10-04T20:00:00Z",
        gmp=500,
        pct=71.4,
        issue_price=700,
        change_since_last=32,
        history=[
            {"as_of": "2026-10-03T20:00:00Z", "gmp": 270},
            {"as_of": "2026-10-04T20:00:00Z", "gmp": 500},
        ],
    )
    assert snapshot.normalized_data["trend"] is None


def test_unmapped_publisher_label_reaches_the_evaluation_as_unknown_trend(golden_input, config):
    coordinator = ConnectorCoordinator()
    snapshot = coordinator.ingest_snapshot(
        {"as_of": golden_input["market"]["gmp"]["as_of"], "pct": 15.91, "trend": "sideways"},
        SourceClass.SECONDARY_TRACKER,
        reference_time=EVAL_AT,
    )
    market_payload, _, _ = coordinator.reconcile_snapshots([snapshot])
    document = copy.deepcopy(golden_input)
    for key in ("as_of", "pct", "trend"):
        document["market"]["gmp"][key] = market_payload["gmp"][key]

    outcome = run(document, config)  # schema-valid: no raw label reaches the enum field

    assert document["market"]["gmp"]["trend"] is None
    assert _gmp_block(outcome)["status"] == "FRESH"
    assert metric(outcome, "gmp_bucket").state == "UNKNOWN"
    assert criterion(outcome, "gmp_trend").state == "UNKNOWN"


# --------------------------------------------------------------------------
# A9 - still fail-closed; A17 eligibility is not source qualification
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "as_of, block_status",
    [
        ("2026-10-05T12:00:00Z", "FRESH"),  # eligible under A17, still not a qualified source
        ("2026-10-05T12:30:00Z", "STALE"),  # after the cutoff
    ],
)
def test_a9_still_withholds_final_for_any_present_gmp(golden_input, config, as_of, block_status):
    outcome = run(_safe(_with_gmp(golden_input, as_of=as_of)), config)
    result = build_evaluation_record_v1(outcome.record)["result"]

    assert outcome.record.evaluation_mode == "FINAL"
    assert _gmp_block(outcome)["status"] == block_status
    assert result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert result["outcome_resolution"]["reason"]["code"] == "SOURCE_UNQUALIFIED"
    assert f"generic market classification is {block_status}" in result["outcome_resolution"]["reason"]["message"]
    assert "final_outcome" not in result


def test_a9_missing_gmp_still_withholds_final(golden_input, config):
    document = _safe(golden_input)
    document["market"].pop("gmp", None)

    result = build_evaluation_record_v1(run(document, config).record)["result"]

    assert result["outcome_resolution"]["state"] == "NONTERMINAL_UNRESOLVED"
    assert result["outcome_resolution"]["reason"]["code"] == "MISSING"
    assert "final_outcome" not in result
