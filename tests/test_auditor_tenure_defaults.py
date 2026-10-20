"""Auditor tenure / repeated-EOM: favourable defaults with synthesised quotes.

``SectionExtractor.extract_governance`` emits, whenever an auditor NAME is found
and an opinion is established:

    governance.auditor_changed_3y = False   ("Auditor <name> unchanged across audited fiscal years")
    governance.auditor_reputed    = True|False   (hard-coded reputed-firm list)
    governance.repeated_eom       = False   ("No repeated Emphasis of Matter noted")

Two of those three are not evidence:

- ``aud_changed_3y = False`` is assigned **before** the tenure scan and both
  branches of the scan assign ``False`` again (``sections.py:1420-1450``), so the
  value is a constant, not a finding.  The emitted quote is a synthesised
  sentence that does not appear in the filing.
- ``repeated_eom = False`` is appended unconditionally with the
  verbatim-looking quote "No repeated Emphasis of Matter noted"
  (``sections.py:1464-1475``), again not a filing sentence.

Together with ``auditor_reputed`` these decide ``_auditor_bucket``
(``derived.py:1428-1486``): ``unqualified`` + ``reputed`` + ``changed_3y = False``
→ ``clean_reputed`` 2/2.  That is a favourable 2 points produced by two
defaults, in the same class as the other unverified builder defaults recorded in
the tracker.

These tests are ``xfail(strict=True)`` until the defaults are corrected; the
correction changes a scored canonical input and is therefore a missing-value
decision, not a mechanical fix.
"""

from __future__ import annotations

import pytest

from ipo_screening.extraction.sections import SectionExtractor


class _StubDoc:
    source_id = "SRC-TEST"


class _StubReader:
    def __init__(self, n: int) -> None:
        self.pages = [None] * n


def _governance(text: str):
    ex = SectionExtractor(_StubDoc(), _StubReader(200), text_cache={1: text})
    raw = ex.extract_governance({"restated_financials": (1, 3)})
    return {r.field_path: r.candidate_value for r in raw}


OPINION = (
    "Independent Auditor's Examination Report\n"
    "In our opinion the financial statements give an unqualified opinion.\n"
    "The financial statements were audited by Deloitte Haskins & Sells LLP.\n"
)

TENURE = (
    "The financial year ended March 31, 2026, March 31, 2025 and March 31, 2024 "
    "were audited by Deloitte Haskins & Sells LLP.\n"
)


def test_auditor_name_and_reputed_standing_are_extracted():
    """Positive control: the auditor is named and classified against the
    reputed-firm list.  (The list is a governance input, not a filing fact.)"""
    gov = _governance(OPINION)
    assert gov["governance.auditor_opinion"] == "unqualified"
    assert gov["governance.auditor_reputed"] is True


@pytest.mark.xfail(
    strict=True,
    reason=(
        "auditor_changed_3y is assigned False before and inside the tenure scan, "
        "so 'no auditor change in 3 years' is asserted without tenure evidence"
    ),
)
def test_auditor_tenure_is_not_asserted_without_tenure_language():
    gov = _governance(OPINION)  # no sentence about which years the auditor audited
    assert gov.get("governance.auditor_changed_3y") is None


@pytest.mark.xfail(
    strict=True,
    reason=(
        "repeated_eom = False is emitted whenever an auditor name is found, with a "
        "synthesised quote"
    ),
)
def test_repeated_eom_is_not_asserted_without_evidence():
    gov = _governance(OPINION)  # no emphasis-of-matter discussion at all
    assert gov.get("governance.repeated_eom") is None


def test_tenure_language_present_still_yields_no_change():
    """Documents current behaviour where the evidence does exist: the filing
    covers the three fiscal years under one auditor, so False is defensible.
    This test passes today and must keep passing after any correction."""
    gov = _governance(OPINION + TENURE)
    assert gov["governance.auditor_changed_3y"] is False
