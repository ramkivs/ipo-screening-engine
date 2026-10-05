"""Vishal Nirmiti golden regression (execution prompt s5, s17; spec s26.1).

The golden result is determined from the v1.5 specification, not copied from
the reference prototype. Three reference behaviours are deliberately *not*
reproduced, and each is asserted below:

1. the reference scorer silently substituted 25% of the fresh issue for the
   undisclosed GCP amount (``[●]`` in the RHP, page 129). v1.5 s13 forbids
   that, so ``use_of_proceeds_bucket`` must be UNKNOWN;
2. the reference scored P/E and the second multiple as 0 against peer
   multiples dated 2026-07-23, which are 74 days old at the evaluation
   instant. v1.5 s9 forbids silently scoring stale data, so both criteria must
   be UNKNOWN;
3. the reference reported K1, K5 and K6 as CLEAR because an absent input
   evaluated to falsy. v1.5 s3.3 requires UNVERIFIED, and the reference worked
   example's distinctive numbers (29/58) must not reappear.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import EVAL_AT, FIXTURES, criterion, knockout, metric, run

GOLDEN = FIXTURES / "vishal_nirmiti"
REFERENCE_FIXTURE = FIXTURES.parent / "handoff" / "reference" / "VISHAL-NIRMITI-LIMITED.json"


@pytest.fixture(scope="module")
def outcome(golden_input, config):
    return run(golden_input, config)


def _load(name: str):
    with (GOLDEN / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


# --------------------------------------------------------------------------
# Golden expectations, generated from the engine and hand-verified
# --------------------------------------------------------------------------


def test_golden_verdict_matches_expected_file(outcome):
    expected = _load("expected_verdict.json")
    assert outcome.score.final_score == expected["score_range"]["final_score"]
    assert outcome.score.verdict == expected["verdict"]["verdict"]
    assert outcome.score.confidence == expected["confidence"]["level"]
    assert outcome.record.result_hash == expected["hashes"]["result_hash"]


def test_golden_result_hash_is_stable(outcome, golden_input, config):
    repeat = run(golden_input, config)
    assert repeat.record.result_hash == outcome.record.result_hash


def test_golden_score_is_the_documented_value(outcome):
    """Base 38.0, penalty -3.0, final 35.0, range 25.0-62.0."""
    assert outcome.score.final_score == pytest.approx(35.0)
    assert outcome.score.base_score == pytest.approx(38.0)
    assert outcome.score.penalties_total == pytest.approx(-3.0)
    assert outcome.score.lower_bound == pytest.approx(25.0)
    assert outcome.score.upper_bound == pytest.approx(62.0)


def test_golden_confidence_is_points_weighted(outcome):
    """73 of 100 evaluable points are available, so completeness is 73%."""
    assert outcome.score.total_evaluable_points == pytest.approx(100.0)
    assert outcome.score.available_points == pytest.approx(73.0)
    assert outcome.score.unknown_points == pytest.approx(27.0)
    assert outcome.score.completeness_pct == pytest.approx(73.0)
    assert outcome.score.confidence == "Low"
    assert outcome.score.completeness_breakdown["weighting"] == "POINTS"


def test_golden_verdict_is_insufficient_data(outcome):
    """A missing critical input yields INSUFFICIENT_DATA, not a bare AVOID."""
    assert outcome.score.verdict == "INSUFFICIENT_DATA"
    assert outcome.score.insufficient_data is True
    assert "going_concern_uncertainty" in outcome.score.completeness_breakdown["critical_data_missing"]


# --------------------------------------------------------------------------
# v1.5 corrections demonstrated on the golden case
# --------------------------------------------------------------------------


def test_gcp_is_unknown_not_the_legal_ceiling(outcome, golden_input):
    """v1.5 s13: the 25% ICDR ceiling must not become the GCP amount."""
    assert metric(outcome, "gcp_amount").is_unknown
    legal_max = metric(outcome, "gcp_legal_max")
    assert legal_max.is_value
    # 14,500 lakh x 25% = 3,625 lakh = 36.25 crore; recorded separately.
    assert legal_max.value == pytest.approx(36.25)
    use_of_proceeds = criterion(outcome, "use_of_proceeds")
    assert use_of_proceeds.state == "UNKNOWN"
    assert use_of_proceeds.score is None
    assert use_of_proceeds.max == 4.0


def test_gcp_ceiling_is_not_present_as_an_amount(golden_input):
    """The fixture must not carry the fabricated 3,625 lakh GCP amount."""
    gcp = [u for u in golden_input["use_of_proceeds"] if u["category"] == "gcp"]
    assert len(gcp) == 1
    assert gcp[0]["amount"] is None
    assert gcp[0]["undisclosed_marker"] == "[●]"


def test_stale_peers_are_not_scored_as_zero(outcome):
    """v1.5 s9: stale peer data neither scores full marks nor silently zero."""
    for criterion_id in ("pe_vs_peers", "second_multiple"):
        item = criterion(outcome, criterion_id)
        assert item.state == "UNKNOWN", criterion_id
        assert item.score is None
    # Only PEG and sector_ipo_relative are peer-independent; of the 20 valuation
    # points, the 16 that depend on peers or the sector set are UNKNOWN, and
    # PEG's 4 points are the sole available valuation points.
    assert outcome.score.completeness_breakdown["valuation_points_unknown"] == pytest.approx(16.0)
    assert outcome.score.completeness_breakdown["valuation_pct"] == pytest.approx(20.0)


def test_peers_are_classified_stale_with_the_reason(outcome):
    statuses = {p["name"]: p for p in outcome.record.peer_snapshot["observations"]}
    assert statuses["GPT Infraprojects Limited"]["status"] == "STALE"
    assert statuses["Indian Hume Pipe Company Limited"]["status"] == "STALE"
    # The reason cites the observation date and the limit; the precise age is
    # recorded in its own field so the reason stays clock-independent and the
    # result hash does not move merely because time passed (spec s19).
    reason = statuses["GPT Infraprojects Limited"]["reason"]
    assert "2026-07-23" in reason
    assert "30-day staleness limit" in reason
    assert 74.0 <= statuses["GPT Infraprojects Limited"]["age_days"] <= 75.0


def test_knockouts_are_tri_state_not_boolean(outcome):
    """v1.5 s3.3/s16: K1, K5 and K6 cannot resolve to CLEAR on missing input."""
    assert knockout(outcome, "K1").state == "UNVERIFIED"
    assert "going_concern_uncertainty" in knockout(outcome, "K1").missing
    assert knockout(outcome, "K5").state == "UNVERIFIED"
    assert "contingent_liab_unquantified" in knockout(outcome, "K5").missing
    assert knockout(outcome, "K6").state == "UNVERIFIED"
    assert "rpt_pct_of_revenue_growth" in knockout(outcome, "K6").missing

    assert knockout(outcome, "K2").state == "CLEAR"
    assert knockout(outcome, "K3").state == "CLEAR"
    assert knockout(outcome, "K4").state == "CLEAR"
    assert outcome.knockouts.status == "UNVERIFIED"


def test_k1_explanation_names_the_missing_input(outcome):
    """Matches the technical design's worked example wording."""
    k1 = knockout(outcome, "K1")
    assert "going_concern_uncertainty" in k1.explanation
    assert k1.required == (
        "auditor_opinion",
        "going_concern_uncertainty",
        "net_worth_latest",
    )


def test_reference_worked_example_numbers_are_not_reproduced(outcome):
    """The reference's 29/58 range assumed stale peers score zero.

    v1.5 changes both the level and the reason, so the old pair must not
    reappear.
    """
    assert (outcome.score.lower_bound, outcome.score.upper_bound) != (29, 58)


# --------------------------------------------------------------------------
# Structural expectations
# --------------------------------------------------------------------------


def test_reference_fixture_type_defect_is_corrected(golden_input):
    """The reference fixture stored pre_issue_shares as the string "1500000".

    The v1.5 schema requires a number, so the corrected fixture uses a number.
    """
    seller = golden_input["issue"]["ofs_sellers"][0]
    assert isinstance(seller["pre_issue_shares"], int)
    if REFERENCE_FIXTURE.exists():
        with REFERENCE_FIXTURE.open("r", encoding="utf-8") as handle:
            reference = json.load(handle)
        assert isinstance(reference["issue"]["ofs_sellers"][0]["pre_issue_shares"], str)
        assert reference["use_of_proceeds"][2]["amount"] == 3625


def test_reference_fixture_would_fail_the_v1_5_schema(config, schema, raw_config):
    """The unmodified reference fixture is rejected by the v1.5 schema gate."""
    from ipo_screening.errors import SchemaValidationError
    from ipo_screening.pipeline import evaluate

    if not REFERENCE_FIXTURE.exists():
        pytest.skip("reference fixture not present")
    with REFERENCE_FIXTURE.open("r", encoding="utf-8") as handle:
        reference = json.load(handle)
    with pytest.raises(SchemaValidationError) as excinfo:
        evaluate(reference, config, evaluation_datetime=EVAL_AT)
    codes = {f.code for f in excinfo.value.findings}
    assert "SCHEMA_VIOLATION" in codes


def test_reference_fixture_gcp_would_be_rejected_as_a_ceiling(config):
    """If the fabricated amount is fed in, the semantic gate names the defect."""
    from ipo_screening.errors import SemanticValidationError
    from ipo_screening.pipeline import evaluate

    if not REFERENCE_FIXTURE.exists():
        pytest.skip("reference fixture not present")
    with REFERENCE_FIXTURE.open("r", encoding="utf-8") as handle:
        reference = json.load(handle)
    reference["issue"]["ofs_sellers"][0]["pre_issue_shares"] = 1500000
    with pytest.raises((SemanticValidationError, Exception)) as excinfo:
        evaluate(reference, config, evaluation_datetime=EVAL_AT)
    message = str(excinfo.value)
    assert "GCP_CEILING_RECORDED_AS_AMOUNT" in message or "SCHEMA_VIOLATION" in message


def test_golden_evidence_is_grounded_in_the_rhp(outcome):
    """Every evidence item resolves, and the GCP evidence records [●]."""
    evidence = outcome.record.evidence
    assert evidence["sources"], "the golden fixture must declare its sources"
    identifiers = {e["evidence_id"] for e in evidence["evidence"]}
    gcp = next(e for e in evidence["evidence"] if e["evidence_id"] == "EV-gcp-undisclosed")
    assert gcp["page"] == 129
    assert "[●]" in gcp["quoted_text"]
    assert "legal maximum" in gcp["page_note"].lower()
    assert "EV-roce" in identifiers


def test_golden_preserves_the_distinction_between_fact_classes(outcome, golden_input):
    """Source facts, extracted values, derived values and decisions stay apart.

    * source fact       - the RHP page 129 text, held in the evidence registry;
    * extracted value   - the canonical input (GCP null, revenue 33867.73);
    * derived value     - revenue_cagr_2y_from_3fy, computed and tagged DERIVED;
    * scoring decision  - the criterion result, referencing the derived metric.
    """
    assert metric(outcome, "revenue_cagr_2y_from_3fy").is_value
    derived = metric(outcome, "revenue_cagr_2y_from_3fy")
    assert "revenue[latest]" in derived.formula
    assert derived.inputs == ("financials.periods",)

    item = criterion(outcome, "revenue_cagr")
    assert item.state == "SCORED"
    assert item.value == pytest.approx(derived.value)
    assert item.metric == "revenue_cagr_2y_from_3fy"
    assert item.formula == derived.formula

    snapshot = outcome.record.input_snapshot
    assert snapshot["input"]["use_of_proceeds"][2]["amount"] is None


def test_golden_module_scores_sum_to_the_base_score(outcome):
    total = sum(m.score for m in outcome.score.modules)
    assert total == pytest.approx(outcome.score.base_score)


def test_golden_criteria_count_is_stable(outcome):
    """Six modules; the retail-heavy overlay swaps two criteria for two."""
    assert len(outcome.score.modules) == 6
    assert len(outcome.score.criteria) == 30
