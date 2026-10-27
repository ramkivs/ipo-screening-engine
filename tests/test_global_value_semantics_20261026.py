"""Global missing-value and capital-structure semantics (2026-10-26).

Two shared defects in the derivation layer are pinned here.  Both are
issuer-neutral: neither mentions a filing, and both are expressed as deltas
from the golden Vishal Nirmiti input or from the synthetic minimal input.

1. **Silence used to score.**  An *empty* objects-of-the-offer schedule fell
   through every three-valued test in ``use_of_proceeds_bucket`` and landed on
   ``mixed_ok`` -- two of four points awarded from the absence of a reading --
   and ``gcp_amount`` reported ``0.0`` for the same empty list.  A fresh issue
   must state its objects, so an empty schedule is missing evidence, not a
   disclosed nil.  A *complete* schedule keeps its classification, a
   partially-disclosed one stays UNKNOWN (as before), a schedule that
   allocates more than the fresh issue it distributes is treated as misread,
   and a pure offer for sale with no proceeds is still NOT_APPLICABLE -- the
   genuine not-applicable case stays distinct from the missing one.

2. **Disclosed counts were never assembled.**  ``post_issue_shares`` and
   ``post_issue_eps`` were read as raw inputs only, so a filing that discloses
   the pre-issue count, the fresh-issue count and a year's PAT but not the
   post-issue count produced UNKNOWN valuation and dilution for no reason.
   The post-issue count is ``pre-issue + fresh-issue`` (an offer for sale
   transfers existing shares and therefore never moves the count), and the
   post-issue EPS follows conservatively as ``latest PAT / post-issue shares``.
   Disclosed values always win, and the prohibited ``fresh issue / price band``
   shortcut is never used.

Everything here is synthetic: no document is read, so the module is a fast
unit tier.
"""

from __future__ import annotations

import copy

import pytest

from conftest import criterion, metric, minimal_input, run


# ==========================================================================
# 1. Empty / partial / complete / malformed objects-of-the-offer schedules
# ==========================================================================


def test_empty_schedule_is_unknown_not_mixed_ok(config):
    """An unread schedule must not earn the ``mixed_ok`` midpoint."""
    document = minimal_input()  # use_of_proceeds is []
    outcome = run(document, config)
    bucket = metric(outcome, "use_of_proceeds_bucket")
    assert bucket.state == "UNKNOWN"
    assert "empty" in bucket.reason
    assert criterion(outcome, "use_of_proceeds").state == "UNKNOWN"
    assert criterion(outcome, "use_of_proceeds").score is None


def test_empty_schedule_does_not_report_a_zero_gcp(config):
    """No schedule is not the same as a schedule with no GCP line."""
    outcome = run(minimal_input(), config)
    gcp = metric(outcome, "gcp_amount")
    assert gcp.state == "UNKNOWN"
    assert gcp.value is None
    assert "no objects-of-the-offer schedule" in gcp.reason


def test_empty_schedule_with_no_fresh_issue_is_not_applicable(config):
    """A pure offer for sale has no proceeds to allocate: NOT_APPLICABLE."""
    document = minimal_input()
    document["issue"]["fresh_issue"] = 0
    document["issue"]["ofs"] = 10000
    outcome = run(document, config)
    bucket = metric(outcome, "use_of_proceeds_bucket")
    assert bucket.state == "NOT_APPLICABLE"
    assert "pure OFS" in bucket.reason


def test_complete_schedule_keeps_its_classification(make_input, config):
    """A fully disclosed schedule still classifies normally."""
    document = make_input(
        **{
            "use_of_proceeds": [
                {"category": "debt_repayment", "amount": 12000.0},
                {"category": "gcp", "amount": 2000.0},
            ]
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "use_of_proceeds_bucket").value == "debt_heavy"
    assert criterion(outcome, "use_of_proceeds").state == "SCORED"


def test_complete_schedule_without_a_gcp_row_reports_a_nil_gcp(make_input, config):
    """A read schedule with no GCP line *is* evidence that GCP is nil."""
    document = make_input(
        **{
            "use_of_proceeds": [
                {"category": "growth_capex", "amount": 12000.0},
                {"category": "debt_repayment", "amount": 2000.0},
            ]
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "gcp_amount").value == pytest.approx(0.0)
    assert metric(outcome, "use_of_proceeds_bucket").value == "growth"


def test_partial_schedule_stays_unknown(make_input, config):
    """An undisclosed leg still blocks the test that needs it."""
    document = make_input(
        **{
            "use_of_proceeds": [
                {"category": "debt_repayment", "amount": 12000.0},
                {"category": "gcp", "amount": None, "undisclosed_marker": "[●]"},
            ]
        }
    )
    outcome = run(document, config)
    assert metric(outcome, "use_of_proceeds_bucket").state == "UNKNOWN"
    assert criterion(outcome, "use_of_proceeds").state == "UNKNOWN"


def test_schedule_larger_than_the_fresh_issue_is_not_scored(make_input, config):
    """A schedule cannot allocate more than the gross proceeds it distributes.

    The objects schedule is commonly printed twice (requirement of funds, then
    deployment); a reader that reads both double-counts.  Every share would be
    overstated, so no bucket may be taken from it.
    """
    document = make_input(
        **{
            "use_of_proceeds": [
                {"category": "debt_repayment", "amount": 20000.0},
                {"category": "gcp", "amount": 2000.0},
            ]
        }
    )
    outcome = run(document, config)
    bucket = metric(outcome, "use_of_proceeds_bucket")
    assert bucket.state == "UNKNOWN"
    assert "exceeds" in bucket.reason
    assert criterion(outcome, "use_of_proceeds").state == "UNKNOWN"


def test_negative_amount_is_rejected_by_the_contract(make_input, config):
    """A malformed (negative) allocation cannot reach scoring at all."""
    from ipo_screening.schema_validation import validate_schema

    document = make_input(
        **{"use_of_proceeds": [{"category": "gcp", "amount": -5.0}]}
    )
    findings = validate_schema(document)
    assert any("use_of_proceeds" in f.location for f in findings)


# ==========================================================================
# 2. Post-issue capital structure and valuation
# ==========================================================================


def test_disclosed_post_issue_count_wins(make_input, config):
    """The disclosed count is used unchanged; the derivation is not applied."""
    outcome = run(make_input(), config)
    # Vishal: 19,800,000 + 6,590,909 fresh = 26,390,909, disclosed as such.
    assert metric(outcome, "dilution_pct").value == pytest.approx(
        6590909 / 26390909 * 100.0
    )


def test_post_issue_count_is_derived_when_only_the_components_are_disclosed(
    make_input, config
):
    """pre-issue + fresh-issue reproduces the disclosed count exactly."""
    disclosed = run(make_input(), config)
    derived = run(make_input(**{"issue.post_issue_shares": None}), config)
    assert derived.record.score["final_score"] is not None
    assert metric(derived, "dilution_pct").value == pytest.approx(
        metric(disclosed, "dilution_pct").value
    )
    assert "derived" in metric(derived, "dilution_pct").reason
    assert "does not change the count" in metric(derived, "dilution_pct").reason


def test_offer_for_sale_does_not_change_the_share_count(make_input, config):
    """OFS transfers existing shares; only the fresh issue enlarges the count."""
    # same fresh count, OFS doubled
    document = make_input(**{"issue.ofs": 6600.0, "issue.post_issue_shares": None})
    outcome = run(document, config)
    assert metric(outcome, "dilution_pct").value == pytest.approx(
        6590909 / 26390909 * 100.0
    )


def test_post_issue_eps_is_derived_from_pat_and_post_issue_shares(make_input, config):
    """The conservative EPS reproduces the disclosed figure on this filing."""
    fresh_peers = {"peers[0].as_of": "2026-10-02", "peers[1].as_of": "2026-10-02"}
    disclosed = run(make_input(**fresh_peers), config)
    derived = run(make_input(**{**fresh_peers, "issue.post_issue_eps": None}), config)
    base_pe = metric(disclosed, "pe_premium_pct")
    derived_pe = metric(derived, "pe_premium_pct")
    assert base_pe.state == "VALUE" and derived_pe.state == "VALUE"
    # PAT 2,497.5 lakh = 24.975 crore over 26,390,909 shares = 9.4635/share
    # against the filing's 9.46: the derived P/E is within a rounding step.
    assert derived_pe.value == pytest.approx(base_pe.value, rel=0.002)


def test_promoter_post_percentage_is_derived_and_reproduces_the_disclosure(
    make_input, config
):
    """pre % x pre shares - shares sold, over post shares, equals the disclosure."""
    derived = run(make_input(**{"capital_structure.promoter_post_pct": None}), config)
    pct = metric(derived, "promoter_post_pct")
    assert pct.state == "VALUE"
    assert pct.value == pytest.approx(49.4, abs=0.02)
    assert "derived" in pct.reason


def test_a_seller_cannot_offer_more_than_it_held(make_input, config):
    """The seller list is validated before any derived holding is formed."""
    from ipo_screening.errors import SemanticValidationError

    document = make_input(**{"capital_structure.promoter_post_pct": None})
    document["issue"]["ofs_sellers"][0]["shares_sold"] = 2_000_000  # more than held
    with pytest.raises(SemanticValidationError):
        run(document, config)


def test_promoter_derivation_refuses_a_group_sale_larger_than_the_group(
    make_input, config
):
    """A sale exceeding the group's disclosed pre-issue holding is refused."""
    document = make_input(
        **{
            "capital_structure.promoter_post_pct": None,
            "capital_structure.promoter_pre_pct": 5.0,  # 990,000 shares implied
        }
    )
    outcome = run(document, config)
    pct = metric(outcome, "promoter_post_pct")
    assert pct.state == "UNKNOWN"
    assert "exceed the promoter group" in pct.reason


def test_post_issue_count_is_unknown_when_only_the_amount_and_band_exist(
    make_input, config
):
    """The prohibited shortcut stays prohibited, and the reason says so."""
    outcome = run(
        make_input(
            **{
                "issue.post_issue_shares": None,
                "issue.pre_issue_shares": None,
                "issue.fresh_shares": None,
                "capital_structure.promoter_post_pct": None,
            }
        ),
        config,
    )
    dilution = metric(outcome, "dilution_pct")
    assert dilution.state == "UNKNOWN"
    # The amount and the band are present; the count still is not invented
    # from them, and the message says exactly that.
    assert "price band" in dilution.reason
    derived = metric(outcome, "promoter_post_pct")
    assert derived.state == "UNKNOWN"
    assert "pre-issue share count is not disclosed" in derived.reason


def test_contradictory_share_counts_are_unknown_not_used(make_input, config):
    """A post-issue count below the pre-issue count cannot come from an issue."""
    outcome = run(make_input(**{"issue.post_issue_shares": 1000}), config)
    assert metric(outcome, "dilution_pct").state == "UNKNOWN"
    assert "smaller than the" in metric(outcome, "dilution_pct").reason


def test_derived_values_are_identical_to_the_disclosed_ones_on_the_golden_input(
    golden_input, config
):
    """The derivation is a reconstruction, not an estimate: it is exact here."""
    stripped = copy.deepcopy(golden_input)
    stripped["issue"]["post_issue_shares"] = None
    stripped["issue"]["post_issue_eps"] = None
    stripped["capital_structure"]["promoter_post_pct"] = None
    derived = run(stripped, config)
    assert metric(derived, "dilution_pct").value == pytest.approx(
        6590909 / 26390909 * 100.0
    )
    assert metric(derived, "promoter_post_pct").value == pytest.approx(49.4, abs=0.02)
