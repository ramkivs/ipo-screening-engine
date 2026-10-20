"""Auditor tenure and repeated-EOM: no favourable default without evidence.

``SectionExtractor.extract_governance`` used to emit, whenever an auditor
NAME was found and an opinion was established:

    governance.auditor_changed_3y = False   ("Auditor <name> unchanged across audited fiscal years")
    governance.repeated_eom       = False   ("No repeated Emphasis of Matter noted")

Neither value was evidence.  ``aud_changed_3y`` was assigned ``False`` before
the tenure scan and ``False`` again in both branches, so no input could
produce any other value.  ``repeated_eom`` was appended unconditionally, with
a quote that appears nowhere in the filing and was not marked as processing.
Together with the hard-coded reputed-firm list they resolved
``_auditor_bucket`` to ``clean_reputed`` 2/2 on an unqualified opinion alone.

Corrected behaviour (existing contract: the schema allows ``boolean|null`` and
``_auditor_bucket`` returns UNKNOWN when ``auditor_changed_3y`` is null):

* ``auditor_changed_3y`` is emitted **only** when a sentence states that the
  same auditor audited the three fiscal years, and the quote is that
  sentence;
* ``repeated_eom`` is emitted **only** on an explicit negative statement in
  the auditors' report ("no Emphasis of Matter"), and the quote is that
  sentence;
* otherwise both fields stay unknown and Module D ``auditor`` is UNKNOWN.

A repeated Emphasis of Matter cannot be inferred from one report and no
extractor produces ``True``; that capability gap is documented, not invented.
"""

from __future__ import annotations

import copy

import pytest

from conftest import EVAL_AT, CONFIG_PATH, minimal_input
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.pipeline import evaluate, load_config


class _StubDoc:
    source_id = "SRC-TEST"


class _StubReader:
    def __init__(self, n: int) -> None:
        self.pages = [None] * n


HEADING = "INDEPENDENT AUDITOR'S EXAMINATION REPORT ON RESTATED CONSOLIDATED FINANCIAL INFORMATION\n"


def _extract(text: str):
    ex = SectionExtractor(_StubDoc(), _StubReader(200), text_cache={1: text})
    raw = ex.extract_governance({"restated_financials": (1, 3)})
    return {r.field_path: r for r in raw}


OPINION = HEADING + (
    "In our opinion the financial statements give an unqualified opinion.\n"
    "The financial statements were audited by Deloitte Haskins & Sells LLP.\n"
)

TENURE = (
    "The financial year ended March 31, 2026, March 31, 2025 and March 31, 2024 "
    "were audited by Deloitte Haskins & Sells LLP.\n"
)

NEGATIVE_EOM = "There are no Emphasis of matters in auditor's report for the period ended March 31, 2026.\n"

POSITIVE_EOM = "Emphasis of Matter: we draw attention to Note 4 regarding the scheme.\n"


def test_auditor_name_and_reputed_standing_are_extracted():
    """Positive control: the auditor is named and classified against the
    reputed-firm list (a curated governance input, not a filing fact)."""
    fields = _extract(OPINION)
    assert fields["governance.auditor_opinion"].candidate_value == "unqualified"
    assert fields["governance.auditor_reputed"].candidate_value is True


def test_auditor_tenure_is_not_asserted_without_tenure_language():
    """An unqualified opinion and a named auditor do not establish that the
    auditor did not change within three years."""
    fields = _extract(OPINION)
    assert "governance.auditor_changed_3y" not in fields
    assert fields["governance.auditor_reputed"].candidate_value is True


def test_repeated_eom_is_not_asserted_without_evidence():
    """The old constant ``False`` carried a quote found nowhere in the source."""
    fields = _extract(OPINION)
    assert "governance.repeated_eom" not in fields


def test_tenure_language_present_still_yields_no_change():
    """A sentence covering all three fiscal years establishes ``False`` and is
    quoted verbatim."""
    fields = _extract(OPINION + TENURE)
    field = fields["governance.auditor_changed_3y"]
    assert field.candidate_value is False
    assert "audited by Deloitte Haskins & Sells LLP" in field.quote
    assert field.quote in (OPINION + TENURE)


def test_explicit_negative_eom_is_recorded_verbatim():
    """An explicit 'no Emphasis of Matter' statement supports ``False`` and the
    quote is the filing's own sentence, not synthesised text."""
    fields = _extract(OPINION + NEGATIVE_EOM)
    field = fields["governance.repeated_eom"]
    assert field.candidate_value is False
    assert "no Emphasis of matters" in field.quote
    assert field.quote in (OPINION + NEGATIVE_EOM)


def test_positive_eom_does_not_assert_repeated_eom():
    """A single Emphasis of Matter is not a *repeated* one; the repeated flag
    stays unknown and the opinion carries the EOM."""
    fields = _extract(OPINION + POSITIVE_EOM + TENURE)
    assert fields["governance.auditor_opinion"].candidate_value == "emphasis_of_matter"
    assert "governance.repeated_eom" not in fields


def test_emitted_quotes_are_verbatim():
    """Every emitted quote for these fields must exist in the source text."""
    source = OPINION + TENURE + NEGATIVE_EOM
    fields = _extract(source)
    for path in ("governance.auditor_changed_3y", "governance.repeated_eom"):
        field = fields.get(path)
        if field is not None:
            assert field.quote in source


def _auditor_bucket(governance):
    cfg = load_config(CONFIG_PATH)
    doc = copy.deepcopy(minimal_input())
    doc["governance"] = governance
    outcome = evaluate(doc, cfg, mode="final", evaluation_datetime=EVAL_AT)
    return outcome.derived.metrics["auditor_bucket"], outcome


def test_unknown_tenure_leaves_auditor_bucket_unknown():
    metric_value, outcome = _auditor_bucket(
        {
            "auditor_opinion": "unqualified",
            "auditor_reputed": True,
            "auditor_changed_3y": None,
            "repeated_eom": None,
        }
    )
    assert metric_value.is_unknown
    criterion = next(
        c
        for module in outcome.score.modules
        for c in module.criteria
        if c.criterion_id == "auditor"
    )
    assert criterion.state == "UNKNOWN"


def test_known_tenure_still_reaches_clean_reputed():
    metric_value, _ = _auditor_bucket(
        {
            "auditor_opinion": "unqualified",
            "auditor_reputed": True,
            "auditor_changed_3y": False,
            "repeated_eom": False,
        }
    )
    assert metric_value.value == "clean_reputed"
