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
    pages = {
        10: "OUTSTANDING LITIGATION AND MATERIAL DEVELOPMENTS\n"
            "None of our Promoters, Directors, or Group Companies are involved in any "
            "material litigation or criminal cases.\n"
    }
    out = _govern(pages)
    record = out["governance.litigation_bucket"]
    assert record.candidate_value == "clean"
    assert "None of our Promoters" in record.quote
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


SEBI_SCOPED_TABLE = """| Category of individuals / entities | Criminal Proceedings | Tax Proceedings | Statutory or Regulatory Proceedings | Disciplinary actions by SEBI or stock exchanges against our Company, Promoters and Directors in the last five years, including outstanding action | Material civil litigation | Aggregate amount involved |
| --- | --- | --- | --- | --- | --- | --- |
| Against our Company | Nil | Nil | Nil | 2 | Nil | Nil |
| Against our Directors | Nil | Nil | Nil | Nil | Nil | Nil |
"""

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
