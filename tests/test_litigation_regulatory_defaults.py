"""D-5: litigation and regulatory-action evidence defaults.

Two unsupported negative defaults let a filing score as litigation-free on the
strength of *not being read*:

``engine/ipo_screening/extraction/sections.py`` (``extract_governance``)
    ``lit_bucket = "clean"`` and ``sebi_active = False`` were assigned **before**
    the litigation scan and both fields were appended **unconditionally**
    afterwards, whatever the scan found -- including when the page range was
    empty.  ``clean`` is the favourable end of the scored ``litigation``
    criterion, so an unread section earned 4/4 points, and K2 was cleared by a
    flag no source had set.

``engine/ipo_screening/extraction/builder.py`` (``_build_governance``)
    any bucket that was not ``criminal_or_regulatory`` was *rewritten* to
    ``"clean"`` -- so the ``minor_civil`` finding the extractor had actually made
    on ``fixtures/filings/class_a_financial_lender.pdf`` p. 11 was silently
    converted into the favourable bucket, and its evidence destroyed.  The same
    block defaulted ``sebi_ed_action_active`` to ``False``.

The synthesised quotation
    ``governance.sebi_ed_action_active`` carried ``quote="No active SEBI or ED
    regulatory proceedings"`` -- text present in no filing, and not marked
    ``quote_is_processing``, so the evidence record presented it as a source
    quotation (the defect D-4 removed from the auditor fields).

Corrected behaviour, entirely inside the existing contract:
    * ``governance.litigation_bucket`` and ``governance.sebi_ed_action_active``
      are emitted **only** from text on the page cited, and are **absent**
      otherwise.  The schema already allows ``null`` for both, ``derived`` already
      maps ``null`` to UNKNOWN, the ``litigation`` criterion already scores
      UNKNOWN rather than zero, K2 already lists the flag as required, and
      ``config.critical_data`` already makes its absence yield INSUFFICIENT_DATA.
      No bucket, weight, threshold, formula, cap, penalty or knockout semantic
      is changed by this module or by the fix.
    * Polarity is respected: "there are **no** outstanding criminal proceedings
      or material civil litigation" is a statement of absence and no longer
      classifies as ``minor_civil``.
    * The statutory disclosure forms are now *read*: the ICDR summary table (one
      row per party group and direction, one column per proceeding type) and the
      labelled "category line / value line" list.  That is what lets a criminal
      proceeding against Directors -- in scope, because the criterion's own
      formula reads "across promoters, directors and the company" -- reach the
      bucket instead of being invisible.
    * Every emitted quotation is a verbatim slice of the page it cites.

The two questions that genuinely need a governed decision stay open and are
recorded, not silently answered: a *party-coverage* standard for ``clean``
(whether "the Company and its Promoters" also clears the Directors), and a
*source-coverage* standard under which a SEBI-only negative could clear a flag
whose governed name covers SEBI **and** the Enforcement Directorate.  Until the
second is defined, only a negative naming both regulators yields ``False``.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import CONFIG_PATH, EVAL_AT, criterion, knockout, metric, minimal_input, run
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import RawExtraction, SourceDocument
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.pipeline import load_config

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE = REPO_ROOT / "engine" / "ipo_screening" / "extraction"
GOLDEN_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


class _StubDoc:
    source_id = "SRC-D5"


class _StubReader:
    def __init__(self, n: int) -> None:
        self.pages = [None] * n


def _govern(pages, page_range=None):
    """Run the governance scan over ``pages`` as the litigation section."""
    pages = dict(pages)
    lo, hi = page_range or (min(pages), min(pages))
    ex = SectionExtractor(_StubDoc(), _StubReader(max(pages) + 4), text_cache=pages)
    return {r.field_path: r for r in ex.extract_governance({"litigation": (lo, hi)})}


def _norm(text: str) -> str:
    return " ".join(text.split())


D5_FIELDS = ("governance.litigation_bucket", "governance.sebi_ed_action_active")


def _assert_verbatim(pages, records):
    """No D-5 quotation may be invented: it must be on the page it cites.

    Scoped to the two fields this pass governs; other governance fields have
    their own evidence rules (``board_independent_majority`` legitimately emits
    a marked processing summary and is outside D-5's scope).
    """
    source = _norm("\n".join(pages.values()))
    for field_path in D5_FIELDS:
        record = records.get(field_path)
        if record is None or record.quote is None:
            continue
        assert record.quote_is_processing is False, (
            f"{field_path}: a verbatim quotation was marked as processing"
        )
        assert _norm(record.quote) in source, f"{field_path}: quote is not in the source"


#: The exact shape SEBI ICDR prescribes, as published in the HD Fire Protect
#: Abridged Prospectus section 12 ("Summary table of outstanding litigations").
#: Retrieved 2026-10-20 from the SEBI-hosted PDF
#: ``HD Fire Protect Limited-Abridged Prospectus_p.pdf``; the cell values are the
#: published ones and the line breaks follow the rendered table.
HD_FIRE_LITIGATION_TABLE = """12. Summary table of outstanding litigations

A summary of outstanding litigation proceedings involving our Company, Subsidiary, Directors, Promoters, Key Managerial Personnel and Senior Management as on the date of the Red Herring Prospectus, in accordance with the SEBI ICDR Regulations and the Materiality Policy, is provided below:

| Category of individuals / entities | Criminal Proceedings | Tax Proceedings | Statutory or Regulatory Proceedings | Disciplinary actions by SEBI or stock exchanges against our Promoters in the last five years, including outstanding action | Material civil litigation# | Aggregate amount involved* (Rs in million) |
| --- | --- | --- | --- | --- | --- | --- |
| Company |  |  |  |  |  |  |
| Against our Company | Nil | Nil | Nil | NA | Nil | Nil |
| By our Company | Nil | 3 | Nil | NA | Nil | 0.40 |
| Directors (excluding Promoters) |  |  |  |  |  |  |
| Against our Directors | 2 | Nil | Nil | NA | Nil | Nil |
| By our Directors | Nil | Nil | Nil | NA | Nil | Nil |
| Against our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |
| By our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |

#In accordance with the Materiality Policy.
* To the extent quantifiable.
"""


# ---------------------------------------------------------------------------
# 1. No litigation evidence available
# ---------------------------------------------------------------------------


def test_unrelated_section_text_emits_no_bucket_and_no_flag():
    pages = {430: "The Company was incorporated on 12 March 1998 and is engaged in trading."}
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out
    assert "governance.sebi_ed_action_active" not in out
    # The previous behaviour was the defect: a bucket was asserted anyway.
    assert out.get("governance.litigation_bucket") is None


def test_empty_page_range_emits_nothing():
    """A range that resolves to no pages is "not searched", not "no litigation".

    ``page_ranges`` defaults to pp. 430-500; a short or unindexed document scans
    nothing at all, which used to yield ``clean`` -- the case that made R.K.
    Fashion and both complete-sample fixtures score 4/4 on an empty scan.
    """
    pages = {2: "Table of contents only."}
    out = _govern(pages, page_range=(430, 500))
    assert "governance.litigation_bucket" not in out
    assert "governance.sebi_ed_action_active" not in out


def test_unreadable_prose_is_unknown_and_not_zero_points():
    """UNKNOWN is a distinct state: the 4 points are unavailable, not awarded."""
    cfg = load_config(CONFIG_PATH)
    doc = copy.deepcopy(minimal_input())
    doc["governance"] = {"litigation_bucket": None, "sebi_ed_action_active": None}
    outcome = run(doc, cfg)
    item = criterion(outcome, "litigation")
    assert item.state == "UNKNOWN"
    assert item.score is None
    assert item.max == 4.0
    assert metric(outcome, "litigation_bucket").is_unknown
    assert "not established" in item.reason
    module_d = next(m for m in outcome.score.modules if m.module_id == "D")
    # the unavailable points are counted as unavailable, not silently awarded
    assert module_d.unknown_points >= 4.0


# ---------------------------------------------------------------------------
# 2. Explicitly documented clean status (the contract supports it)
# ---------------------------------------------------------------------------


def test_explicit_absence_statement_is_clean_and_quoted():
    """A denial covering the whole party population is ``clean``, and is quoted.

    Re-pinned for A24-D1 (approved 2026-10-20).  This test used to accept the
    wording taken from ``class_b_cyclical_manufacturing.pdf`` -- "None of our
    Promoters, Directors, or Group Companies ..." -- as ``clean``.  Under the
    approved coverage standard that sentence no longer qualifies: it denies
    anything for the Company itself, and "Group Companies" are separate legal
    persons that do not stand in for the issuer (A24 R3).  The party population
    of the criterion is Company + Promoters + Directors, so the test now uses a
    denial that names all three; the class_b wording is pinned as UNKNOWN by
    ``test_group_companies_are_not_the_issuer`` below.
    """
    pages = {
        10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n"
            "None of our Company, our Promoters or our Directors are involved in any "
            "material litigation or criminal cases.\n"
    }
    out = _govern(pages)
    record = out["governance.litigation_bucket"]
    assert record.candidate_value == "clean"
    assert "None of our Company" in record.quote
    _assert_verbatim(pages, out)
    # the parties the statement actually names are recorded, not assumed
    assert "Promoters" in record.notes and "Directors" in record.notes


def test_negated_civil_wording_is_not_misread_as_a_civil_finding():
    """The sentence that used to produce ``minor_civil`` now produces ``clean``.

    ``class_a_financial_lender.pdf`` p. 11 states "there are no outstanding
    criminal proceedings or material civil litigation"; the polarity-blind scan
    classified that as material civil litigation and the builder then rewrote
    it to ``clean`` -- two defects cancelling into an accidentally right answer
    with an unsupported quotation underneath it.
    """
    pages = {
        11: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n"
            "Except as stated below, there are no outstanding criminal proceedings or "
            "material civil litigation involving our Company, Directors or Promoters.\n"
    }
    out = _govern(pages)
    record = out["governance.litigation_bucket"]
    assert record.candidate_value == "clean"
    assert "there are no outstanding criminal proceedings" in record.quote
    _assert_verbatim(pages, out)


def test_all_nil_summary_table_is_clean():
    pages = {
        12: "Summary table of outstanding litigation\n"
            "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
            "| Statutory or Regulatory Proceedings | Disciplinary actions by SEBI or stock "
            "exchanges against our Promoters in the last five years, including outstanding "
            "action | Material civil litigation | Aggregate amount involved |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "| Against our Company | Nil | Nil | Nil | NA | Nil | Nil |\n"
            "| Against our Directors | Nil | Nil | Nil | NA | Nil | Nil |\n"
            "| Against our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |\n"
    }
    out = _govern(pages)
    assert out["governance.litigation_bucket"].candidate_value == "clean"
    _assert_verbatim(pages, out)


# ---------------------------------------------------------------------------
# 3. Issuer-level proceeding
# ---------------------------------------------------------------------------


def test_issuer_level_criminal_proceeding_is_criminal_or_regulatory():
    pages = {
        14: "Criminal proceedings against our promoters and the Company are pending "
            "before the Court of the Sessions Judge.\n"
    }
    out = _govern(pages)
    record = out["governance.litigation_bucket"]
    assert record.candidate_value == "criminal_or_regulatory"
    assert "Criminal proceedings against our promoters" in record.quote
    _assert_verbatim(pages, out)


def test_summary_table_row_against_the_company_is_an_issuer_finding():
    pages = {
        12: "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
            "| Statutory or Regulatory Proceedings | Material civil litigation | Aggregate amount involved |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| Against our Company | 1 | Nil | Nil | Nil | 12.40 |\n"
            "| Against our Directors | Nil | Nil | Nil | Nil | Nil |\n"
    }
    out = _govern(pages)
    assert out["governance.litigation_bucket"].candidate_value == "criminal_or_regulatory"
    assert "Against our Company" in out["governance.litigation_bucket"].quote
    _assert_verbatim(pages, out)


# ---------------------------------------------------------------------------
# 4. Director-only proceeding (in scope for the bucket, out of scope for the issuer)
# ---------------------------------------------------------------------------


def test_director_only_criminal_proceeding_reaches_the_bucket():
    """HD Fire Protect's disclosed facts, verbatim from the Abridged Prospectus.

    Two criminal proceedings against Directors (excluding Promoters), three tax
    proceedings *by* the Company, nothing else.  The criterion's formula is
    "across promoters, directors and the company", so the Director row is in
    scope and the bucket is ``criminal_or_regulatory`` -- the value the previous
    code reported as ``clean``.
    """
    pages = {12: HD_FIRE_LITIGATION_TABLE}
    out = _govern(pages)
    record = out["governance.litigation_bucket"]
    assert record.candidate_value == "criminal_or_regulatory"
    assert "Against our Directors" in record.quote
    assert "summary-table" in record.notes
    _assert_verbatim(pages, out)


def test_proceedings_brought_by_the_issuer_are_not_adverse():
    """The "By our Company" row (3 tax proceedings) changes nothing on its own."""
    pages = {
        12: "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
            "| Statutory or Regulatory Proceedings | Material civil litigation | Aggregate amount involved |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| By our Company | Nil | 3 | Nil | Nil | 0.40 |\n"
            "| By our Directors | Nil | Nil | Nil | Nil | Nil |\n"
    }
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out


def test_unmapped_adverse_type_blocks_clean_without_inventing_a_bucket():
    """Tax proceedings *against* the Company map to no governed bucket.

    They must not be ignored into ``clean``: litigation exists, its type simply
    is not one of the three scored buckets.  UNKNOWN is the contract's answer.
    """
    pages = {
        12: "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
            "| Statutory or Regulatory Proceedings | Disciplinary actions by SEBI or stock "
            "exchanges against our Promoters in the last five years | Material civil litigation "
            "| Aggregate amount involved |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "| Against our Company | Nil | 3 | Nil | NA | Nil | 12.40 |\n"
            "| Against our Directors | Nil | Nil | Nil | NA | Nil | Nil |\n"
    }
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out


def test_partially_unreadable_table_never_becomes_clean():
    """A truncated row is ambiguous coverage: no bucket, and no "clean"."""
    pages = {
        12: "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
            "| Statutory or Regulatory Proceedings | Material civil litigation |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| Against our Company | Nil\n"
            "| Against our Directors | Nil | Nil | Nil | Nil |\n"
    }
    out = _govern(pages)
    # the readable row says nothing adverse, the unreadable one is unknown; the
    # engine must not average that into "clean".
    assert out.get("governance.litigation_bucket") is None or (
        out["governance.litigation_bucket"].candidate_value != "clean"
    )


# ---------------------------------------------------------------------------
# 5. A criminal proceeding is not a SEBI/ED action
# ---------------------------------------------------------------------------


def test_criminal_proceeding_alone_does_not_set_the_regulatory_flag():
    pages = {
        30: "Criminal complaint No. 221 of 2025 is pending against our Director before "
            "the Magistrate Court.\n"
    }
    out = _govern(pages)
    assert out["governance.litigation_bucket"].candidate_value == "criminal_or_regulatory"
    assert "governance.sebi_ed_action_active" not in out
    _assert_verbatim(pages, out)


def test_tax_or_civil_proceedings_are_not_regulatory_actions():
    pages = {12: HD_FIRE_LITIGATION_TABLE}
    out = _govern(pages)
    # 2 criminal proceedings against Directors and 3 tax proceedings by the
    # Company are disclosed; no SEBI or ED action is.
    assert out["governance.litigation_bucket"].candidate_value == "criminal_or_regulatory"
    assert "governance.sebi_ed_action_active" not in out


# ---------------------------------------------------------------------------
# 6. Explicit active SEBI/ED action
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        "The Enforcement Directorate (ED) has initiated proceedings against the Company under the PMLA.",
        "SEBI has issued a show cause notice to our Directors in the matter of the preferential allotment.",
        "An order imposing a penalty has been passed by SEBI against our Promoters.",
        "Proceedings initiated by SEBI against the Company are pending before the Special Court.",
    ],
)
def test_explicit_regulatory_action_is_emitted_true(sentence):
    pages = {22: "OUTSTANDING LITIGATION\n" + sentence + "\n"}
    out = _govern(pages)
    record = out["governance.sebi_ed_action_active"]
    assert record.candidate_value is True
    assert _norm(sentence) in _norm(record.quote)
    _assert_verbatim(pages, out)


def test_verified_active_action_triggers_k2():
    cfg = load_config(CONFIG_PATH)
    doc = copy.deepcopy(minimal_input())
    doc["governance"] = {"sebi_ed_action_active": True}
    doc["capital_structure"]["promoter_pledge_pct"] = 0.0
    outcome = run(doc, cfg)
    assert knockout(outcome, "K2").state == "TRIGGERED"
    assert outcome.record.verdict["verdict"] == "AVOID"


# ---------------------------------------------------------------------------
# 7. Missing, inaccessible, incomplete or ambiguous regulatory coverage
# ---------------------------------------------------------------------------


def test_no_search_result_is_not_a_negative_finding():
    pages = {22: "This section sets out the offer structure and the terms of the issue."}
    out = _govern(pages)
    assert "governance.sebi_ed_action_active" not in out


def test_sebi_only_negative_does_not_clear_a_sebi_and_ed_flag():
    """A SEBI/RBI/Exchange negative says nothing about the Enforcement Directorate.

    This is the wording real filings use (``class_a_financial_lender.pdf`` p. 11,
    and the SEBI column of every ICDR summary table).  Treating it as
    ``sebi_ed_action_active = False`` would clear K2 on partial coverage, so the
    field stays unknown until a source-coverage standard is defined for it.
    """
    pages = {
        22: "As on the date of this Red Herring Prospectus, there are no outstanding "
            "disciplinary actions or penalties imposed by SEBI or the RBI or Stock Exchanges "
            "against our Company, Directors or Promoters.\n"
    }
    out = _govern(pages)
    assert "governance.sebi_ed_action_active" not in out


def test_promoter_scoped_nil_column_does_not_clear_the_flag():
    """HD Fire's SEBI column is scoped "against our Promoters", in the last five years.

    A promoter-scoped nil cannot speak for the issuer, and does not mention the
    Enforcement Directorate, so the disclosure supports neither True nor a
    verified absence -- the flag is UNKNOWN for HD Fire, from its own filing.
    """
    pages = {12: HD_FIRE_LITIGATION_TABLE}
    out = _govern(pages)
    assert "governance.sebi_ed_action_active" not in out


def test_heading_that_names_sebi_is_not_an_action():
    """A section label ("Disciplinary actions by SEBI ... involving our Company")
    names proceeding types, not a finding; the value line decides."""
    pages = {
        24: "(d) Disciplinary actions by SEBI and / or the Stock Exchanges involving our Company\n"
            "Nil\n"
    }
    out = _govern(pages)
    assert "governance.sebi_ed_action_active" not in out
    assert "governance.litigation_bucket" not in out


def test_boilerplate_sebi_references_are_not_actions():
    pages = {
        1: "The Issue is being made in terms of the SEBI ICDR Regulations, 2018. The Equity "
           "Shares have not been recommended or approved by SEBI, nor does SEBI guarantee the "
           "accuracy of this document.\n"
    }
    out = _govern(pages)
    assert "governance.sebi_ed_action_active" not in out


def test_both_regulators_named_absent_is_a_verified_negative():
    pages = {
        22: "There are no proceedings initiated by SEBI or the Enforcement Directorate "
            "against our Company or our Promoters.\n"
    }
    out = _govern(pages)
    record = out["governance.sebi_ed_action_active"]
    assert record.candidate_value is False
    _assert_verbatim(pages, out)


def test_missing_regulatory_input_leaves_k2_unverified_and_verdict_insufficient():
    """K2 is never CLEAR on an absent input, and the verdict says so."""
    cfg = load_config(CONFIG_PATH)
    doc = copy.deepcopy(minimal_input())
    doc["governance"] = {"litigation_bucket": "clean"}
    doc["capital_structure"]["promoter_pledge_pct"] = 0.0
    outcome = run(doc, cfg)
    k2 = knockout(outcome, "K2")
    assert k2.state == "UNVERIFIED"
    assert "sebi_ed_action_active" in k2.missing
    assert "the supplied input does not establish" in k2.explanation
    assert outcome.record.verdict["verdict"] == "INSUFFICIENT_DATA"


def test_inaccessible_pages_are_reported_as_unknown_not_clean_end_to_end():
    """The complete-sample fixture has no litigation section at all.

    It used to score ``clean`` 4/4; the honest state is UNKNOWN, and the
    criterion is unavailable rather than earned.
    """
    from ipo_screening.extraction.extractor import DocumentExtractor

    pdf = REPO_ROOT / "fixtures" / "filings" / "complete_sample_rhp.pdf"
    if not pdf.exists():
        pytest.skip("synthetic filing not present")
    canonical, _report = DocumentExtractor().extract_from_pdf(pdf, allow_fixture_fallbacks=False)
    assert canonical["governance"]["litigation_bucket"] is None
    assert canonical["governance"]["sebi_ed_action_active"] is None
    assert "governance.litigation_bucket" not in canonical["_evidence"]
    assert "governance.sebi_ed_action_active" not in canonical["_evidence"]


# ---------------------------------------------------------------------------
# 8. No synthesised quotation without a real source passage
# ---------------------------------------------------------------------------


BATTERY = {
    "silence": {430: "Nothing about proceedings appears on this page."},
    "absence": {
        10: "None of our Promoters, Directors, or Group Companies are involved in any "
            "material litigation or criminal cases.\n"
    },
    "adverse": {11: "Criminal proceedings against our promoters are pending.\n"},
    "table": {12: HD_FIRE_LITIGATION_TABLE},
    "labelled": {
        20: "a) Criminal proceedings against the Company\n2\n"
            "b) Material civil litigation against the Company\nNil\n"
    },
    "regulator": {
        22: "The Enforcement Directorate (ED) has initiated proceedings against the Company.\n"
    },
}


@pytest.mark.parametrize("name", sorted(BATTERY))
def test_every_emitted_quotation_is_a_source_passage(name):
    pages = BATTERY[name]
    out = _govern(pages)
    _assert_verbatim(pages, out)
    for record in out.values():
        quote = (record.quote or "") + (record.notes or "")
        assert "No active SEBI or ED regulatory proceedings" not in quote
        assert "Litigation bucket classified as" not in quote


def test_the_fabricated_sentences_are_gone_from_the_extractor():
    """Pin the removal at source: neither synthesised string may come back.

    They survive only in the comments that explain the defect, so the check is
    on code lines: no quote (or any other emitted value) may assert them again.
    """
    for module in ("sections.py", "builder.py"):
        text = (ENGINE / module).read_text(encoding="utf-8")
        code = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )
        assert "No active SEBI or ED regulatory proceedings" not in code
        assert "Litigation bucket classified as" not in code


# ---------------------------------------------------------------------------
# A23-A: `clean` needs the denial to cover what the bucket is defined over
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        "There are no outstanding criminal proceedings involving our Company or our Promoters.",
        "No material civil litigation is pending against our Directors.",
        "Our Company has no pending regulatory proceedings.",
        "No tax proceedings are pending against our Company.",
    ],
)
def test_a_dimension_scoped_nil_is_not_clean(sentence):
    """`clean` means no material litigation at all, not "none of one kind".

    The criterion's three values are `clean`, `minor_civil` and
    `criminal_or_regulatory`, so a denial that reaches only one dimension leaves
    the other undisclosed -- UNKNOWN, exactly as the summary-table route already
    requires its criminal/civil/regulatory columns to be present before it may
    answer `clean`.  Before this correction the prose route accepted a
    one-dimension nil, and three of the repository's synthetic filings were
    earning 4/4 on it.
    """
    pages = {10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n" + sentence + "\n"}
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out


@pytest.mark.parametrize(
    "sentence",
    [
        # both dimensions and all three parties named (the class_a disclosure, verbatim)
        "Except as stated below, there are no outstanding criminal proceedings or "
        "material civil litigation involving our Company, Directors or Promoters.",
        # the same, in the other order, with the Company as "the issuer"
        "There are no proceedings, criminal or civil, pending against the Company, "
        "its Promoters or its Directors.",
    ],
)
def test_a_comprehensive_nil_is_clean_and_quoted(sentence):
    """Comprehensive means both *dimensions* and the whole *party population*.

    "No litigation is pending against our Company." used to be enough for
    ``clean``; A24-D1 (approved 2026-10-20) says it is not, because it leaves
    the Promoters and Directors undisclosed -- it is pinned as UNKNOWN by
    ``test_partial_party_coverage_is_unknown_not_clean`` below.  "No litigation
    against our Promoters, Directors or Group Companies" likewise leaves the
    issuer itself undisclosed.
    """
    pages = {11: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n" + sentence + "\n"}
    out = _govern(pages)
    record = out["governance.litigation_bucket"]
    assert record.candidate_value == "clean"
    _assert_verbatim(pages, out)


def test_a_denial_in_unrecognised_wording_stays_unknown():
    """A recorded capability limit, in the safe direction.

    "Our Company and its Promoters are **not a party to** any proceedings" is a
    genuine nil, but the engine's absence forms are the ones prospectuses use
    ("no litigation", "none of … involved in any …", "no proceedings are
    pending").  A denial it does not recognise leaves the bucket UNKNOWN rather
    than guessing at the favourable value; widening the *favourable* vocabulary
    is a coverage decision (A23 §6.1), so it is not taken here.
    """
    pages = {11: "OUTSTANDING LITIGATION\nOur Company and its Promoters are not a party to any proceedings.\n"}
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out


# ---------------------------------------------------------------------------
# A23-B: a denial limited to a closed period cannot clear the regulatory flag
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        "No proceedings were initiated by SEBI or the Enforcement Directorate against "
        "our Company during the financial year 2023-24.",
        "No penalty was imposed by SEBI or the Enforcement Directorate on our Promoters "
        "as on 31 March 2022.",
        "SEBI and the Enforcement Directorate initiated no action against our Company "
        "for the period ended 31 March 2021.",
    ],
)
def test_b_closed_period_denial_does_not_clear_the_flag(sentence):
    """"Nothing happened in FY2023-24" is not "nothing is active now".

    The governed flag is `sebi_ed_action_**active**`; a denial whose stated scope
    closed before the disclosure date leaves the present state unestablished, so
    the field stays absent and K2 stays UNVERIFIED.
    """
    pages = {22: "OUTSTANDING LITIGATION\n" + sentence + "\n"}
    out = _govern(pages)
    assert "governance.sebi_ed_action_active" not in out


@pytest.mark.parametrize(
    "sentence",
    [
        "There are no proceedings initiated by SEBI or the Enforcement Directorate "
        "against our Company or our Promoters.",
        "As on the date of this Red Herring Prospectus, no proceedings have been "
        "initiated by SEBI or the Enforcement Directorate against our Company.",
        "No action has been initiated by SEBI or the Enforcement Directorate against "
        "our Company in the last five years.",
    ],
)
def test_b_present_or_rolling_denial_still_clears_the_flag(sentence):
    """The guard must not swallow the statements that do speak for the present.

    An unqualified denial, an as-of-the-prospectus denial and a rolling window
    that includes today all reach the flag's own question, so each yields False
    with its sentence quoted -- and the "last five years" form is the ICDR
    disclosure window, so it is the wording real filings use.
    """
    pages = {22: "OUTSTANDING LITIGATION\n" + sentence + "\n"}
    out = _govern(pages)
    record = out["governance.sebi_ed_action_active"]
    assert record.candidate_value is False
    _assert_verbatim(pages, out)


SEBI_SCOPED_TABLE = """| Category of individuals / entities | Criminal Proceedings | Tax Proceedings | Statutory or Regulatory Proceedings | Disciplinary actions by SEBI or stock exchanges against our Company, Promoters and Directors in the last five years, including outstanding action | Material civil litigation | Aggregate amount involved |
| --- | --- | --- | --- | --- | --- | --- |
| Against our Company | Nil | Nil | Nil | 2 | Nil | Nil |
| Against our Directors | Nil | Nil | Nil | Nil | Nil | Nil |
"""

# A *statutory or regulatory* adverse count is already inside the governed
# taxonomy: the bucket is named `criminal_or_regulatory`, and the ICDR table
# column of the same name is its disclosure form.  Tax is the residual type with
# no bucket of its own (see the tax-only table below and A23 6.4).
REGULATORY_ONLY_TABLE = """| Category of individuals / entities | Criminal Proceedings | Tax Proceedings | Statutory or Regulatory Proceedings | Material civil litigation | Aggregate amount involved |
| --- | --- | --- | --- | --- | --- |
| Against our Company | Nil | Nil | 1 | Nil | 3.20 |
| Against our Directors | Nil | Nil | Nil | Nil | Nil |
"""


def test_d_statutory_or_regulatory_count_uses_the_existing_bucket():
    """No new category: "regulatory" is in the bucket's own name.

    A single adverse statutory/regulatory proceeding scores 0/4 for the same
    reason a criminal one does, and a *tax*-only nil or count never reaches
    `clean` (below), so nothing is quietly forgiven.
    """
    pages = {12: REGULATORY_ONLY_TABLE}
    out = _govern(pages)
    assert out["governance.litigation_bucket"].candidate_value == "criminal_or_regulatory"
    _assert_verbatim(pages, out)


TAX_ONLY_TABLE = """| Category of individuals / entities | Tax Proceedings | Statutory or Regulatory Proceedings | Aggregate amount involved |
| --- | --- | --- | --- |
| Against our Company | 4 | Nil | 3.20 |
| Against our Directors | Nil | Nil | Nil |
"""


def test_summary_table_regulatory_column_can_set_the_flag():
    """The ICDR table is where an outstanding SEBI action is disclosed.

    A count in that column on an adverse row is a positive finding; the row
    itself is the quotation, so the flag can be traced to the cell that
    established it.
    """
    pages = {12: SEBI_SCOPED_TABLE}
    out = _govern(pages)
    record = out["governance.sebi_ed_action_active"]
    assert record.candidate_value is True
    assert record.page == 12
    assert "Against our Company" in record.quote
    assert out["governance.litigation_bucket"].candidate_value == "criminal_or_regulatory"
    _assert_verbatim(pages, out)


def test_labelled_count_naming_the_regulator_sets_the_flag():
    pages = {
        24: "(d) Disciplinary actions by SEBI and / or the Stock Exchanges involving our Company\n"
            "2\n"
    }
    out = _govern(pages)
    assert out["governance.sebi_ed_action_active"].candidate_value is True
    assert out["governance.litigation_bucket"].candidate_value == "criminal_or_regulatory"
    _assert_verbatim(pages, out)


def test_enforcement_directorate_only_negative_does_not_clear_the_sebi_side():
    """The mirror image of the SEBI-only negative: neither half implies both."""
    pages = {
        22: "No proceedings have been initiated by the Enforcement Directorate against "
            "our Company or our Promoters.\n"
    }
    out = _govern(pages)
    assert "governance.sebi_ed_action_active" not in out


def test_negation_between_the_regulator_and_the_act_is_read():
    """"SEBI has **not** imposed any penalty" must not trigger K2.

    The negation sits *after* the agency token, so a prefix-only polarity test
    would have missed it and emitted ``sebi_ed_action_active = True`` -- a
    knockout and an AVOID verdict -- out of a sentence that denies the action.
    """
    pages = {22: "SEBI has not imposed any penalty on our Promoters.\n"}
    out = _govern(pages)
    assert "governance.sebi_ed_action_active" not in out


def test_explicit_both_regulator_absence_needs_no_act_verb():
    pages = {
        22: "As on the date of the Red Herring Prospectus, there are no active SEBI or ED "
            "regulatory proceedings against our Company.\n"
    }
    out = _govern(pages)
    record = out["governance.sebi_ed_action_active"]
    assert record.candidate_value is False
    assert "no active SEBI or ED regulatory proceedings" in record.quote
    _assert_verbatim(pages, out)


def test_unreadable_row_does_not_cancel_a_disclosed_count():
    """"Truncated" costs the *favourable* conclusions, not an adverse one.

    The Directors row discloses a criminal proceeding; the Company row could
    not be parsed.  Reporting the disclosed matter is what the evidence supports
    -- the missing row can add a proceeding, never remove one.  What the
    unreadable row does cost is ``clean``.
    """
    pages = {
        12: "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
            "| Statutory or Regulatory Proceedings | Material civil litigation |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| Against our Company | Nil\n"
            "| Against our Directors | 1 | Nil | Nil | Nil |\n"
    }
    out = _govern(pages)
    assert out["governance.litigation_bucket"].candidate_value == "criminal_or_regulatory"
    _assert_verbatim(pages, out)


def test_table_without_the_bucket_columns_cannot_show_clean():
    """A summary table carrying only tax / statutory columns proves no absence."""
    pages = {12: TAX_ONLY_TABLE}
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out


# ---------------------------------------------------------------------------
# 9. No accidental change to existing scoring semantics
# ---------------------------------------------------------------------------


def test_bucket_points_and_schema_are_unchanged():
    """The governed map is still clean 4 / minor_civil 2 / criminal 0, and the
    input contract still permits ``null`` for both fields."""
    import json

    raw = json.loads((REPO_ROOT / "config" / "ipo-config.v1.5.0.json").read_text(encoding="utf-8"))
    criterion_def = next(
        c
        for module in raw["modules"]
        for c in module["criteria"]
        if c["id"] == "litigation"
    )
    assert criterion_def["max"] == 4
    assert criterion_def["metric"] == "litigation_bucket"
    assert criterion_def["rule"] == {
        "type": "categorical",
        "map": {"clean": 4, "minor_civil": 2, "criminal_or_regulatory": 0},
    }
    schema = json.loads(
        (REPO_ROOT / "schema" / "ipo-input.v1.5.schema.json").read_text(encoding="utf-8")
    )
    governance = schema["properties"]["governance"]["properties"]
    assert governance["litigation_bucket"]["enum"] == [
        "clean",
        "minor_civil",
        "criminal_or_regulatory",
        None,
    ]
    assert governance["sebi_ed_action_active"]["type"] == ["boolean", "null"]
    assert "sebi_ed_action_active" in raw["critical_data"]["items"]


@pytest.mark.parametrize(
    "bucket,points",
    [("clean", 4.0), ("minor_civil", 2.0), ("criminal_or_regulatory", 0.0)],
)
def test_scored_buckets_still_score_as_before(bucket, points):
    cfg = load_config(CONFIG_PATH)
    doc = copy.deepcopy(minimal_input())
    doc["governance"] = {"litigation_bucket": bucket, "sebi_ed_action_active": False}
    item = criterion(run(doc, cfg), "litigation")
    assert item.state == "SCORED"
    assert item.score == points


def test_golden_evaluation_hash_is_bit_for_bit_unchanged():
    """The vishal golden input states its own bucket: the fix must not move it."""
    import json

    cfg = load_config(CONFIG_PATH)
    canonical = json.loads((REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json").read_text())
    assert canonical["governance"]["litigation_bucket"] == "criminal_or_regulatory"
    outcome = evaluate_final(cfg, canonical)
    assert outcome.record.result_hash == GOLDEN_HASH
    assert outcome.record.score["final_score"] == 35.0


def evaluate_final(cfg, canonical):
    from ipo_screening.pipeline import evaluate

    return evaluate(
        copy.deepcopy(canonical), cfg, mode="final", evaluation_datetime=EVAL_AT
    )


# ---------------------------------------------------------------------------
# Builder layer: the coercion that destroyed extracted evidence
# ---------------------------------------------------------------------------


def _build(extractions, base=None, allow_fixture_fallbacks=False):
    doc = SourceDocument(
        source_id="TEST-D5",
        source_type="RHP",
        uri="test.pdf",
        content_hash="abc",
        file_size_bytes=100,
        page_count=10,
    )
    return CanonicalInputBuilder(
        doc=doc,
        extractions=extractions,
        reference_base=base or {},
        allow_fixture_fallbacks=allow_fixture_fallbacks,
    ).build()


def _lit_extraction(value):
    return RawExtraction(
        field_path="governance.litigation_bucket",
        candidate_value=value,
        raw_text=str(value),
        page=11,
        quote=str(value),
    )


def test_extracted_minor_civil_is_no_longer_rewritten_to_clean():
    canonical = _build([_lit_extraction("minor_civil")])
    assert canonical["governance"]["litigation_bucket"] == "minor_civil"


def test_absent_extraction_leaves_the_bucket_unknown_not_clean():
    canonical = _build([])
    assert canonical["governance"]["litigation_bucket"] is None
    assert canonical["governance"]["sebi_ed_action_active"] is None


def test_unrecognised_value_is_unknown_not_a_favourable_bucket():
    canonical = _build([_lit_extraction("some_other_thing")])
    assert canonical["governance"]["litigation_bucket"] is None


def test_stated_synonyms_still_normalise():
    for spelling, expected in (
        ("none", "clean"),
        ("material_civil", "minor_civil"),
        ("criminal", "criminal_or_regulatory"),
        ("CLEAN", "clean"),
    ):
        assert _build([_lit_extraction(spelling)])["governance"]["litigation_bucket"] == expected


def test_input_governance_still_overrides_the_extraction():
    base = {"governance": {"litigation_bucket": "criminal_or_regulatory", "sebi_ed_action_active": True}}
    canonical = _build([_lit_extraction("clean")], base=base)
    assert canonical["governance"]["litigation_bucket"] == "criminal_or_regulatory"
    assert canonical["governance"]["sebi_ed_action_active"] is True


# ---------------------------------------------------------------------------
# A24-D1: the party population a ``clean`` conclusion is defined over
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        # the issuer alone; its Promoters and Directors are undisclosed
        "No litigation is pending against our Company.",
        # two of the three parties
        "There are no outstanding criminal proceedings or material civil litigation "
        "involving our Company or our Promoters.",
        "No proceedings are pending against our Directors or our Promoters.",
        # the company that is not the issuer
        "None of our Promoters, Directors, or Group Companies are involved in any "
        "material litigation or criminal cases.",
        "There are no proceedings against our Subsidiary, our Promoters or our Directors.",
        # a population the criterion does not use, however wide
        "No proceeding of any kind is pending against our Key Managerial Personnel or "
        "our Senior Management Personnel.",
    ],
)
def test_partial_party_coverage_is_unknown_not_clean(sentence):
    """``clean`` asserts absence for Company **and** Promoters **and** Directors.

    A24-D1, approved 2026-10-20: the bucket is defined over the party population
    the governed metric formula itself names -- "across promoters, directors and
    the company" (``engine/ipo_screening/derived.py``), the same three parties
    the upstream reference config enumerates for this bucket.  Before this
    correction a single party token was enough, so a nil naming only the issuer
    awarded 4/4 and left the Directors undisclosed.

    A denial about Group Companies or about KMP / Senior Management is *not*
    coverage: the first names separate legal persons, and the second is a
    population the criterion does not include (widening it is a separate governed
    decision, so it is neither required here nor sufficient).
    """
    pages = {10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n" + sentence + "\n"}
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out


@pytest.mark.parametrize(
    "sentence",
    [
        "No litigation is pending against our Company, our Promoters or our Directors.",
        "There are no criminal proceedings, and no material civil litigation, involving "
        "the Company, the Promoters and the Board of Directors.",
        # a wider population still covers the required three
        "No proceeding is pending against our Company, our Promoters, our Directors or "
        "our Key Managerial Personnel.",
    ],
)
def test_full_party_coverage_nil_is_clean(sentence):
    """The rule is a floor, not a ceiling: naming more is still enough."""
    pages = {10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n" + sentence + "\n"}
    out = _govern(pages)
    record = out["governance.litigation_bucket"]
    assert record.candidate_value == "clean"
    _assert_verbatim(pages, out)


def test_an_adverse_finding_needs_no_party_coverage():
    """The asymmetry is deliberate: a finding is true on its own evidence.

    Only the *favourable* conclusion has to establish that the whole population
    was silent.  A criminal proceeding against one Director condemns, whatever
    the other rows say, so widening the coverage requirement must not be allowed
    to suppress adverse evidence.
    """
    pages = {
        10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n"
            "Criminal Complaint No. 812 of 2024 is pending against one of our Directors "
            "before the Court of Judicial Magistrate.\n"
    }
    out = _govern(pages)
    assert out["governance.litigation_bucket"].candidate_value == "criminal_or_regulatory"


def test_prose_and_table_routes_apply_the_same_coverage_rule():
    """One standard, two disclosure forms (A24-D3's "both routes" condition).

    The identical coverage -- Company and Promoters silent, Directors simply not
    shown -- must classify the same way whichever statutory form carries it.
    Before the correction the prose route accepted any party and the table route
    required no party row at all, so two filings with the same disclosure could
    be scored differently for being formatted differently.
    """
    partial_prose = {
        10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n"
            "There are no outstanding criminal proceedings or material civil litigation "
            "involving our Company or our Promoters.\n"
    }
    partial_table = {
        11: "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
            "| Statutory or Regulatory Proceedings | Material civil litigation |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| Against our Company | Nil | Nil | Nil | Nil |\n"
            "| Against our Promoters | Nil | Nil | Nil | Nil |\n"
    }
    full_table = {
        11: "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
            "| Statutory or Regulatory Proceedings | Material civil litigation |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| Against our Company | Nil | Nil | Nil | Nil |\n"
            "| Against our Promoters | Nil | Nil | Nil | Nil |\n"
            "| Against our Directors | Nil | Nil | Nil | Nil |\n"
    }
    assert "governance.litigation_bucket" not in _govern(partial_prose)
    assert "governance.litigation_bucket" not in _govern(partial_table)
    # ...and the table route does reach `clean` once the population is covered,
    # so the rule is not a permanent block on the disclosure form.
    assert _govern(full_table)["governance.litigation_bucket"].candidate_value == "clean"


def test_reviewer_assertion_is_outside_the_coverage_rule():
    """A24-D2: a reviewer's bucket assertion is never treated as source evidence.

    ``governance.litigation_bucket`` supplied by the reviewer is honoured as an
    assertion (it was, and stays, outside the automated coverage rule) but it
    does not become an extraction record -- so it cannot acquire a quotation, a
    page, or the appearance of having been read off the filing.  Conversely, a
    coverage rule can never *relabel* that assertion: the rule constrains what
    the engine may conclude from text, not what a reviewer may state.
    """
    base = {"governance": {"litigation_bucket": "clean"}}
    canonical = _build([], base=base)
    assert canonical["governance"]["litigation_bucket"] == "clean"
    assert not any(
        r.field_path == "governance.litigation_bucket" for r in []
    )  # the extraction that would have carried evidence does not exist

    # an extraction whose own coverage fails yields nothing at all, so the
    # reviewer's value cannot be quietly re-branded as source-derived
    partial = {
        10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n"
            "No litigation is pending against our Company.\n"
    }
    assert "governance.litigation_bucket" not in _govern(partial)


# ---------------------------------------------------------------------------
# A24-D3: the ``Directors (excluding Promoters)`` row-parsing defect
# ---------------------------------------------------------------------------

#: The ICDR Schedule VI row label as real filings print it, qualifier included.
HD_FIRE_STYLE_TABLE = (
    "| Category of individuals / entities | Criminal Proceedings | Tax Proceedings "
    "| Statutory or Regulatory Proceedings | Disciplinary actions by SEBI or stock "
    "exchanges against our Promoters in the last five years | Material civil litigation "
    "| Aggregate amount involved (Rs in million) |\n"
    "| --- | --- | --- | --- | --- | --- | --- |\n"
    "| Company |  |  |  |  |  |  |\n"
    "{rows}"
)


def _hd_table(*rows: str) -> dict:
    return {12: "12. Summary table of outstanding litigations\n\n" + HD_FIRE_STYLE_TABLE.format(
        rows="".join(row + "\n" for row in rows)
    )}


def test_parenthetical_party_label_does_not_shift_the_row():
    """``Against our Directors (excluding Promoters)`` is a readable row.

    The row pattern ends the party name at the first pipe, so the qualifier was
    left at the head of the row body and became a spurious first cell: every
    value slid one column right, ``len(parts) != len(keys)`` failed, and the row
    was discarded as unreadable -- an adverse criminal count going unreported
    (and, on a nil row, the whole table being treated as ambiguous).  A24-D3,
    approved 2026-10-20, authorises exactly this repair.
    """
    pages = _hd_table(
        "| Against our Company | Nil | Nil | Nil | NA | Nil | Nil |",
        "| Against our Directors (excluding Promoters) | 2 | Nil | Nil | NA | Nil | Nil |",
        "| Against our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |",
    )
    out = _govern(pages)
    record = out["governance.litigation_bucket"]
    assert record.candidate_value == "criminal_or_regulatory"
    # the quotation is the untouched source line: the qualifier is still there,
    # so the reader can see what the row actually scoped
    assert "Directors (excluding Promoters)" in record.quote
    _assert_verbatim(pages, out)


def test_qualifier_never_becomes_coverage_of_the_excluded_group():
    """Directors excluding Promoters is a *Directors* row, not a Promoters row."""
    pages = _hd_table(
        "| Against our Company | Nil | Nil | Nil | NA | Nil | Nil |",
        "| Against our Directors (excluding Promoters) | Nil | Nil | Nil | NA | Nil | Nil |",
    )
    # Promoters are then undisclosed, so `clean` is withheld even though every
    # readable cell is nil.
    assert "governance.litigation_bucket" not in _govern(pages)


def test_nil_in_a_parenthetical_row_is_not_read_as_an_adverse_count():
    """The repair must not create findings: a nil row stays a nil row."""
    pages = _hd_table(
        "| Against our Company | Nil | Nil | Nil | NA | Nil | Nil |",
        "| Against our Directors (excluding Promoters) | Nil | Nil | Nil | NA | Nil | Nil |",
        "| Against our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |",
    )
    out = _govern(pages)
    assert out["governance.litigation_bucket"].candidate_value == "clean"


def test_unreadable_cell_after_the_qualifier_is_not_inferred_as_nil():
    """A cell that is neither Nil nor a count leaves the row unreadable.

    The row body ``Refer Note 32(b)`` is not evidence of a nil.  It blocks
    ``clean`` for the whole table and is reported as UNKNOWN; the quotation and
    the party label are untouched.
    """
    pages = _hd_table(
        "| Against our Company | Nil | Nil | Nil | NA | Nil | Nil |",
        "| Against our Directors (excluding Promoters) | Refer Note 32(b) | Nil | Nil | NA | Nil | Nil |",
        "| Against our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |",
    )
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out
    assert out.get("governance.sebi_ed_action_active") is None or (
        out["governance.sebi_ed_action_active"].candidate_value is not False
    )


def test_stacked_qualifiers_stay_unparseable_rather_than_guessed():
    """The documented limit of the repair (A24-D3's "cannot be parsed" clause).

    One bracketed qualifier is what the ICDR row label carries.  A second is not
    guessed at: the row stays unreadable, which blocks a favourable conclusion
    and never produces a NIL out of ambiguity.
    """
    pages = _hd_table(
        "| Against our Company | Nil | Nil | Nil | NA | Nil | Nil |",
        "| Against our Directors (excluding Promoters) (as on the date of the RHP) "
        "| 2 | Nil | Nil | NA | Nil | Nil |",
        "| Against our Promoters | Nil | Nil | Nil | Nil | Nil | Nil |",
    )
    out = _govern(pages)
    assert out.get("governance.litigation_bucket") is None or (
        out["governance.litigation_bucket"].candidate_value != "clean"
    )


# ---------------------------------------------------------------------------
# A25-D1 / A25-D2: what an absence may be read from, and what is observable
# ---------------------------------------------------------------------------


class _TextPage:
    """A PDF page whose text extraction either returns text or fails."""

    def __init__(self, text: str, fails: bool = False) -> None:
        self._text = text
        self._fails = fails

    def extract_text(self) -> str:
        if self._fails:
            raise RuntimeError("page could not be extracted")
        return self._text


class _TextReader:
    def __init__(self, page_count: int, texts=None, failing=()) -> None:
        texts = texts or {}
        failing = set(failing)
        self.pages = [
            _TextPage(texts.get(p, ""), fails=p in failing) for p in range(1, page_count + 1)
        ]


def _govern_window(page_count, texts, page_range=None, failing=()):
    """Run the scan over a document whose pages were (or were not) read.

    Unlike ``_govern`` this drives real extraction through the reader, so the
    A25-D2 states -- located vs fallback window, read vs failed page -- are the
    ones the extractor actually sees instead of being pre-supplied.
    """
    ex = SectionExtractor(_StubDoc(), _TextReader(page_count, texts, failing))
    return ex, {r.field_path: r for r in ex.extract_governance(page_range)}


_SEBI_DENIAL = (
    "Except as disclosed, there has been no action initiated against our Company or "
    "our Promoters by SEBI or by the Enforcement Directorate."
)
_SEBI_ACTION = (
    "The Enforcement Directorate has initiated proceedings against our Company under "
    "the Foreign Exchange Management Act, 1999."
)


def test_per_page_extraction_status_is_observable():
    """A25-D2: a page that failed to extract is distinguishable from a blank one."""
    ex, _ = _govern_window(4, {1: "cover", 2: "text"}, page_range={"litigation": (1, 4)})
    assert ex.page_status[1] == "READ"  # read, and it had text
    assert ex.page_status[2] == "READ"
    assert ex.page_status[3] == "BLANK"  # read, and it had none -- still a read
    assert ex.pages_read(1, 4) is True
    assert ex.pages_read(1, 9) is True  # clamped: the document has no page 5+
    assert ex.pages_read(9, 12) is False  # a window with no page at all is not searched
    ex_failed, _ = _govern_window(
        4, {2: "text"}, page_range={"litigation": (1, 4)}, failing=(3,)
    )
    assert ex_failed.page_status[3] == "FAILED"
    assert ex_failed.pages_read(1, 4) is False


def test_a_fallback_window_may_find_action_but_may_not_declare_absence():
    """Absence requires a window we know was the right one (A25-D1).

    When the filing's own table of contents does not locate the litigation
    section, the extractor scans a hardcoded range.  A hit there is still a
    finding -- seeing something does not depend on how the page was looked for --
    but a *non*-hit cannot mean nothing exists: the section may simply be
    elsewhere.  Before A25 the two were indistinguishable in the record.
    """
    _, guessed = _govern_window(500, {450: "OUTSTANDING LITIGATION\n" + _SEBI_DENIAL})
    assert "governance.sebi_ed_action_active" not in guessed
    _, located = _govern_window(
        500,
        {450: "OUTSTANDING LITIGATION\n" + _SEBI_DENIAL},
        page_range={"litigation": (450, 452)},
    )
    assert located["governance.sebi_ed_action_active"].candidate_value is False
    _, adverse_on_guess = _govern_window(500, {450: "OUTSTANDING LITIGATION\n" + _SEBI_ACTION})
    assert adverse_on_guess["governance.sebi_ed_action_active"].candidate_value is True


def test_an_unreadable_page_blocks_absence_not_a_finding():
    """Same asymmetry, caused by a page that could not be extracted."""
    pages = {450: "OUTSTANDING LITIGATION\n" + _SEBI_DENIAL, 451: _SEBI_ACTION}
    _, broken = _govern_window(
        500, {450: "OUTSTANDING LITIGATION\n" + _SEBI_DENIAL},
        page_range={"litigation": (450, 452)}, failing=(451,),
    )
    assert "governance.sebi_ed_action_active" not in broken
    _, broken_with_action = _govern_window(
        500, pages, page_range={"litigation": (450, 452)}, failing=(452,)
    )
    assert broken_with_action["governance.sebi_ed_action_active"].candidate_value is True


def test_a_negative_record_says_absence_of_disclosure_not_verified_absence():
    """A25-D1 / C5: the wording is part of the contract, not decoration.

    ``governance.sebi_ed_action_active = false`` means "the filing denies any
    SEBI or ED action on the pages searched".  It is never an independently
    verified absence -- no regulator source is consulted -- so the record says so
    and names the search basis.  ``true`` remains a disclosed adverse action.
    """
    _, located = _govern_window(
        500,
        {450: "OUTSTANDING LITIGATION\n" + _SEBI_DENIAL},
        page_range={"litigation": (450, 451)},
    )
    record = located["governance.sebi_ed_action_active"]
    assert record.candidate_value is False
    assert "absence of disclosure" in record.notes
    assert "not verified absence" in record.notes
    assert "table of contents" in record.notes
    assert "verified that no action exists" not in record.notes
    _assert_verbatim({450: "OUTSTANDING LITIGATION\n" + _SEBI_DENIAL}, located)


def test_a_fallback_window_is_named_as_such_in_the_record():
    """A guessed range is still usable evidence, but must say it was guessed."""
    pages = {450: "OUTSTANDING LITIGATION\n" + _SEBI_ACTION}
    _, out = _govern_window(500, pages)
    record = out["governance.sebi_ed_action_active"]
    assert record.candidate_value is True
    assert "hardcoded fallback" in record.notes
    assert "litigation section located via" not in record.notes


def test_bucket_record_carries_its_coverage_basis():
    """The litigation bucket reports what was searched, for every route."""
    pages = {
        10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n"
            "No litigation is pending against our Company, our Promoters or our Directors.\n"
    }
    record = _govern(pages)["governance.litigation_bucket"]
    assert "search basis:" in record.notes or "coverage basis:" in record.notes


def test_the_labelled_list_route_cannot_award_clean_on_partial_coverage():
    """All three statutory forms are held to the same standard.

    The labelled "category line / value line" disclosure can report an adverse
    finding, but it never concludes absence: a list of nils says nothing about
    the categories it does not print, let alone about the parties it does not
    name.  That is the A24-D1 coverage rule already in force on that route,
    pinned here so a later widening has to pass through this test.
    """
    pages = {
        14: "OUTSTANDING LITIGATION\n"
            "Criminal proceedings involving our Company: Nil\n"
            "Material civil litigation involving our Company: Nil\n"
            "Tax proceedings involving our Company: Nil\n"
    }
    out = _govern(pages)
    assert "governance.litigation_bucket" not in out
