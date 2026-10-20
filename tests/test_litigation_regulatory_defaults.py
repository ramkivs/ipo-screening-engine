"""D-5: litigation and SEBI/ED findings require evidence, never a default.

Before D-5 the governance extractor initialised ``litigation_bucket`` to
``"clean"`` and ``sebi_ed_action_active`` to ``False`` before scanning and
emitted both unconditionally -- even when every page in the scanned range was
empty.  The builder repeated the defect (default ``"clean"``, then coerced an
explicit ``None`` back to ``"clean"``), and the SEBI record carried the
quotation "No active SEBI or ED regulatory proceedings", which appears in no
filing.  The two inputs are consumed by Module D ``litigation`` (4 points) and
by knockout K2, so the defaults handed out a clean bill of health from
silence.

These nine regressions pin the corrected contract:

1.  no evidence                       -> UNKNOWN / UNKNOWN, no quotation;
2.  documented clean                  -> ``clean`` with a real quotation;
3.  issuer-level proceeding           -> ``criminal_or_regulatory``;
4.  director-only proceeding          -> bucket set, SEBI/ED still UNKNOWN;
5.  criminal proceeding               -> never establishes a SEBI/ED action;
6.  explicit active SEBI/ED action    -> ``True`` and a regulatory bucket;
7.  incomplete / unreachable coverage -> UNKNOWN, never ``clean``;
8.  quotation provenance              -> every quote is real source text;
9.  scoring                          -> the 4/2/0 map and the golden score are
                                        unchanged.

The contract already permits both nulls (``schema/ipo-input.v1.5.schema.json``
``governance.litigation_bucket`` enum includes ``null`` and
``sebi_ed_action_active`` is ``["boolean", "null"]``), so no schema or config
change is involved.  Decision record: ``handoff/decisions/A23-...``.
"""

from __future__ import annotations

import json

import pytest

from conftest import GOLDEN_INPUT, GOLDEN_DIR, run
from ipo_screening.extraction import CanonicalInputBuilder, RawExtraction
from ipo_screening.extraction.sections import SectionExtractor

from test_promoter_holding_extraction import _StubDoc, _StubReader


def _governance(text: str, page: int = 257, page_count: int = 400):
    """Run ``extract_governance`` over a one-page litigation section."""
    ex = SectionExtractor(_StubDoc(), _StubReader(page_count), text_cache={page: text})
    raw = ex.extract_governance({"litigation": (page, page)})
    return {r.field_path: r for r in raw}


def _values(text: str, **kwargs):
    records = _governance(text, **kwargs)
    return {
        "litigation": records["governance.litigation_bucket"].candidate_value,
        "sebi": records["governance.sebi_ed_action_active"].candidate_value,
    }


# ---------------------------------------------------------------------------
# 1. No evidence
# ---------------------------------------------------------------------------


def test_absent_litigation_text_leaves_both_fields_unknown():
    records = _governance("")
    litigation = records["governance.litigation_bucket"]
    sebi = records["governance.sebi_ed_action_active"]

    # The UNKNOWN state is explicit and contract-supported: null candidate,
    # is_unknown set, no quotation, and an explanation of the limitation.
    assert litigation.candidate_value is None
    assert litigation.is_unknown is True
    assert litigation.quote is None
    assert "absence of a finding" in (litigation.notes or "")

    assert sebi.candidate_value is None
    assert sebi.is_unknown is True
    assert sebi.quote is None
    assert "not evidence that no action exists" in (sebi.notes or "")


def test_builder_never_coerces_an_unknown_back_to_clean():
    """Root cause 2: the builder default and the ``None -> clean`` coercion."""
    builder = CanonicalInputBuilder(
        doc=_StubDoc(), extractions=[], reference_base={"governance": {}}
    )
    gov = builder._build_governance()
    assert gov["litigation_bucket"] is None
    assert gov["sebi_ed_action_active"] is None

    # An explicit null extraction stays null; a missing key is not "clean".
    unknown = RawExtraction(
        field_path="governance.litigation_bucket",
        candidate_value=None,
        is_unknown=True,
    )
    builder = CanonicalInputBuilder(
        doc=_StubDoc(), extractions=[unknown], reference_base={"governance": {}}
    )
    assert builder._build_governance()["litigation_bucket"] is None

    # The legacy synonym is still mapped; that is an input normalisation, not
    # a default.
    builder = CanonicalInputBuilder(
        doc=_StubDoc(),
        extractions=[
            RawExtraction(
                field_path="governance.litigation_bucket", candidate_value="none"
            )
        ],
        reference_base={"governance": {}},
    )
    assert builder._build_governance()["litigation_bucket"] == "clean"


# ---------------------------------------------------------------------------
# 2. Documented clean
# ---------------------------------------------------------------------------


def test_explicit_clean_statement_covering_the_parties_is_scored_clean():
    text = (
        "Except as stated below, there are no outstanding criminal proceedings "
        "or material civil litigation involving our Company, Directors or Promoters."
    )
    records = _governance(text)
    litigation = records["governance.litigation_bucket"]

    assert litigation.candidate_value == "clean"
    assert litigation.is_unknown is False
    # The quotation is the filing's own sentence, not a processing summary.
    assert litigation.quote == text
    assert litigation.quote_is_processing is False


def test_a_group_company_negative_does_not_establish_the_issuer_status():
    """``Group Companies`` are not the issuer (fixtures/filings/class_b)."""
    text = (
        "None of our Promoters, Directors, or Group Companies are involved in "
        "any material litigation or criminal cases."
    )
    assert _values(text) == {"litigation": None, "sebi": None}


# ---------------------------------------------------------------------------
# 3. Issuer-level proceeding
# ---------------------------------------------------------------------------


def test_issuer_level_criminal_proceeding_sets_the_bucket():
    text = (
        "A criminal complaint is pending against our Company before the "
        "Judicial Magistrate."
    )
    records = _governance(text)
    litigation = records["governance.litigation_bucket"]

    assert litigation.candidate_value == "criminal_or_regulatory"
    assert litigation.quote == text
    # A criminal case is not a SEBI/ED action.
    assert records["governance.sebi_ed_action_active"].candidate_value is None


# ---------------------------------------------------------------------------
# 4. Director-only proceeding
# ---------------------------------------------------------------------------


def test_director_only_proceeding_sets_the_bucket_but_not_sebi():
    text = (
        "A criminal complaint is pending against our Directors in relation to "
        "a contractual dispute."
    )
    records = _governance(text)

    assert records["governance.litigation_bucket"].candidate_value == (
        "criminal_or_regulatory"
    )
    sebi = records["governance.sebi_ed_action_active"]
    assert sebi.candidate_value is None
    assert sebi.is_unknown is True


def test_director_only_negative_does_not_establish_the_issuer_status():
    text = "There are no outstanding criminal proceedings against our Directors."
    assert _values(text) == {"litigation": None, "sebi": None}


# ---------------------------------------------------------------------------
# 5. Criminal proceeding is not a SEBI/ED action
# ---------------------------------------------------------------------------


def test_criminal_proceeding_never_establishes_a_sebi_or_ed_action():
    text = (
        "A criminal case is pending against our Company. "
        "SEBI has been informed of the dispute."
    )
    values = _values(text)
    assert values["litigation"] == "criminal_or_regulatory"
    assert values["sebi"] is None

    # A bare reference to the SEBI (ICDR) Regulations is not an action either.
    text = (
        "A criminal complaint is pending against our Promoters. "
        "The Offer is made in compliance with the SEBI (ICDR) Regulations."
    )
    values = _values(text)
    assert values["litigation"] == "criminal_or_regulatory"
    assert values["sebi"] is None


# ---------------------------------------------------------------------------
# 6. Explicit active SEBI/ED action
# ---------------------------------------------------------------------------


def test_explicit_active_sebi_action_sets_the_flag_and_a_regulatory_bucket():
    text = (
        "SEBI has initiated proceedings against our Company for alleged "
        "disclosure violations."
    )
    records = _governance(text)

    sebi = records["governance.sebi_ed_action_active"]
    assert sebi.candidate_value is True
    assert sebi.quote == text
    # An active regulatory proceeding is itself a regulatory exposure.
    assert records["governance.litigation_bucket"].candidate_value == (
        "criminal_or_regulatory"
    )


def test_sebi_action_against_an_unrelated_party_is_not_our_exposure():
    text = (
        "SEBI has initiated proceedings against an unrelated listed company "
        "in a different matter."
    )
    assert _values(text) == {"litigation": None, "sebi": None}


# ---------------------------------------------------------------------------
# 7. Missing / inaccessible / incomplete / ambiguous coverage
# ---------------------------------------------------------------------------


def test_unreachable_page_range_stays_unknown_instead_of_clean():
    ex = SectionExtractor(_StubDoc(), _StubReader(400), text_cache={})
    raw = {
        r.field_path: r for r in ex.extract_governance({"litigation": (500, 520)})
    }
    assert raw["governance.litigation_bucket"].candidate_value is None
    assert raw["governance.sebi_ed_action_active"].candidate_value is None


def test_truncated_or_unattributed_negative_stays_unknown():
    # A cross-reference is not a finding: no party and no status.
    assert _values(
        "Except as stated in the section above, there are no outstanding proceedings."
    ) == {"litigation": None, "sebi": None}


def test_ambiguous_negation_without_an_action_word_establishes_nothing():
    assert _values(
        "Our Company has no material developments to report in this section."
    ) == {"litigation": None, "sebi": None}


# ---------------------------------------------------------------------------
# 8. No synthesised quotation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Except as stated below, there are no outstanding criminal proceedings "
        "or material civil litigation involving our Company, Directors or Promoters.",
        "A criminal complaint is pending against our Directors.",
        "SEBI has initiated proceedings against our Company.",
    ],
)
def test_every_quotation_is_real_source_text(text):
    records = _governance(text)
    flat = " ".join(text.split())
    for field in ("governance.litigation_bucket", "governance.sebi_ed_action_active"):
        record = records[field]
        if record.quote is not None:
            assert record.quote in flat, f"{field} quote is not source text"
            assert record.quote_is_processing is False
        else:
            assert record.candidate_value is None


# ---------------------------------------------------------------------------
# 9. No accidental scoring change
# ---------------------------------------------------------------------------


def test_governance_categorical_map_is_unchanged(golden_input, config, make_input):
    expected = {"clean": 4.0, "minor_civil": 2.0, "criminal_or_regulatory": 0.0}
    for value, points in expected.items():
        document = make_input(**{"governance.litigation_bucket": value})
        outcome = run(document, config)
        module_d = next(
            m for m in outcome.record.score["modules"] if m["module_id"] == "D"
        )
        criterion = next(
            c for c in module_d["criteria"] if c["criterion_id"] == "litigation"
        )
        assert criterion["max"] == 4.0
        assert criterion["state"] == "SCORED"
        assert criterion["score"] == points

    # UNKNOWN earns nothing but also loses nothing beyond its own 4 points.
    document = make_input(**{"governance.litigation_bucket": None})
    outcome = run(document, config)
    module_d = next(m for m in outcome.record.score["modules"] if m["module_id"] == "D")
    criterion = next(c for c in module_d["criteria"] if c["criterion_id"] == "litigation")
    assert criterion["state"] == "UNKNOWN"
    assert criterion["max"] == 4.0
    assert criterion.get("score") is None
    assert criterion["reason"] == (
        "the litigation status of the promoters, directors and company is not established"
    )


def test_golden_score_is_unchanged(golden_input, config):
    """The stored Vishal Nirmiti expectation still reproduces exactly."""
    expected = json.loads((GOLDEN_DIR / "expected_score.json").read_text())
    outcome = run(golden_input, config)
    assert outcome.record.score["final_score"] == expected["final_score"]
    assert outcome.record.score["modules"] == expected["modules"]


def test_golden_input_governance_fields_are_untouched():
    golden = json.loads(GOLDEN_INPUT.read_text())
    assert golden["governance"]["litigation_bucket"] == "criminal_or_regulatory"
    assert golden["governance"]["sebi_ed_action_active"] is False
