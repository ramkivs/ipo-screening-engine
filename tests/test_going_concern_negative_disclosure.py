"""Going-concern uncertainty: a negative statement is not a positive one.

``SectionExtractor._GOING_CONCERN_UNCERTAINTY`` matched the standard phrase
"material uncertainty ... going concern" without checking polarity.  The
standard *negative* confirmation used in audit reports —

    "There is no material uncertainty related to going concern"
    "We did not identify any material uncertainty ..."
    "No material uncertainty exists ..."

— therefore emitted ``going_concern_uncertainty = True`` and triggered
knockout K1 on the opposite of the disclosed fact.  The engine already
applies the same polarity rule to Emphasis of Matter
(``_has_positive_emphasis_of_matter``); this is the equivalent correction for
the K1 input.

The correction is deliberately narrow:

* a negated phrase is **not** emitted as True;
* nothing is emitted as False.  "No material uncertainty exists" is evidence
  *in the document* that no uncertainty was reported, but turning that into
  ``False`` (and so clearing K1) is the negative-confirmation rule that
  decision D-1 has not authorised.  The field therefore stays unknown.
"""

from __future__ import annotations

import pytest

from ipo_screening.extraction.sections import SectionExtractor


class _StubDoc:
    source_id = "SRC-TEST"


class _StubReader:
    def __init__(self, n: int) -> None:
        self.pages = [None] * n


HEADING = "INDEPENDENT AUDITOR'S EXAMINATION REPORT ON RESTATED CONSOLIDATED FINANCIAL INFORMATION\n"


def _extract(text: str):
    ex = SectionExtractor(_StubDoc(), _StubReader(200), text_cache={1: HEADING + text})
    raw = ex.extract_governance({"restated_financials": (1, 3)})
    return {r.field_path: r for r in raw}


POSITIVE = "There is a material uncertainty related to going concern that may cast significant doubt.\n"

NEGATIVES = [
    "There is no material uncertainty related to going concern.\n",
    "We did not identify any material uncertainty related to going concern.\n",
    "No material uncertainty exists that may cast significant doubt on the Company's ability to "
    "continue as a going concern.\n",
    "The auditors have not reported any material uncertainty related to going concern.\n",
    "There is no substantial doubt about the entity's ability to continue as a going concern.\n",
]


def test_positive_uncertainty_is_still_detected():
    field = _extract(POSITIVE).get("governance.going_concern_uncertainty")
    assert field is not None and field.candidate_value is True
    assert "material uncertainty related to going concern" in field.quote


@pytest.mark.parametrize("text", NEGATIVES)
def test_negative_uncertainty_statement_is_not_a_trigger(text):
    """The phrase appears, but the sentence asserts its absence."""
    assert _extract(text).get("governance.going_concern_uncertainty") is None


def test_measurement_basis_is_not_uncertainty():
    """A transfer 'on a going concern basis' is an accounting convention."""
    text = "Assets were transferred at carrying values on a going concern basis.\n"
    assert _extract(text).get("governance.going_concern_uncertainty") is None


def test_unrelated_no_does_not_suppress_a_real_disclosure():
    """A bare 'no' earlier in the sentence must not hide a genuine statement."""
    text = "No doubt, there is a material uncertainty related to going concern.\n"
    field = _extract(text).get("governance.going_concern_uncertainty")
    assert field is not None and field.candidate_value is True
