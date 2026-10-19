"""Auditor opinion and going-concern evidence (K1 inputs), 2026-10-20.

The governed fields behind knockout K1 are `auditor_opinion`,
`going_concern_uncertainty` and `net_worth_latest`.

Two extraction defects were demonstrated on the committed Jio RHP
(SHA-256 ``72480c2e…1b6d``):

1. **The opinion scan was gated per page.**  It required the words
   "examination report" / "independent auditor" on the *same* page as the
   opinion language.  Jio states its conclusion ("we report that the
   Restated Consolidated Financial Information … there is no modification
   in the underlying audit reports") on PDF pp. 323-324, which do not repeat
   the heading, so the whole report yielded no opinion.
2. **`going_concern_uncertainty` was emitted as `False` unconditionally**
   (inside the `if auditor_name:` branch) with the quote "No material going
   concern uncertainty noted" — a sentence that appears nowhere in the
   source.  An absent disclosure was thereby converted into a favourable
   value, clearing a K1 input without evidence.

Corrections: the opinion is read from the contiguous examination-report
section (anchored on the heading, ending at the auditors' UDIN signature);
a component auditor's confirmation about one subsidiary's standalone
statements is not accepted as the issuer's opinion; a negative statement
("There are no Emphasis of matters") is never classified as an Emphasis of
Matter; and going-concern uncertainty is emitted only on positive
uncertainty language (this applies the already-approved Step 4 Area B(i)
principle — unknown rather than an unsupported favourable default).

K1 is NOT cleared for Jio: the going-concern input remains UNKNOWN, and
the absence of a going-concern paragraph is not evidence that no
uncertainty exists.
"""

from __future__ import annotations

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.extraction.sections import SectionExtractor

JIO_PDF = (
    REPO_ROOT / "evidence" / "non-authoritative" / "jio"
    / "U72900GJ2019PLC110816_JIO.pdf"
)

RANGES = {"restated_financials": (1, 8)}


def _extractor(pages):
    extractor = SectionExtractor.__new__(SectionExtractor)
    extractor.page_count = max(pages) if pages else 1
    extractor.extract_page_text = lambda p: pages.get(p, "")
    return extractor


def _field(extractions, path):
    for ex in extractions:
        if ex.field_path == path:
            return ex
    return None


HEADING = (
    "INDEPENDENT AUDITOR'S EXAMINATION REPORT ON RESTATED CONSOLIDATED "
    "FINANCIAL INFORMATION\nThe Board of Directors\n"
)


def test_opinion_is_read_from_the_conclusion_page_that_lacks_the_heading():
    """The conclusion paragraph spans pages; the second page carries neither
    'examination report' nor 'independent auditor'."""
    ex = _extractor({
        1: HEADING + "8. Based on our examination, we report that the "
                      "Restated Consolidated Financial Information:",
        2: "b. do not require any adjustment for modification as there is no "
           "modification in the underlying audit reports; and\n"
           "c. have been prepared in accordance with the Act.",
        3: "For Deloitte Haskins & Sells LLP\nUDIN: 26100459QBZXUZ8355",
    })
    extraction = _field(ex.extract_governance(RANGES), "governance.auditor_opinion")
    assert extraction is not None
    assert extraction.candidate_value == "unqualified"
    assert extraction.page == 2
    assert "no modification in the underlying audit reports" in extraction.quote


def test_component_auditor_confirmation_is_not_the_issuer_opinion():
    """Paragraph 7 of an examination report records another auditor's
    confirmation about one subsidiary's standalone statements.  It is not
    the joint auditors' opinion on the restated consolidated information."""
    ex = _extractor({
        1: HEADING + "The auditors of Reliance Jio Infocomm Limited have "
                      "examined the Standalone Financial Statements and have "
                      "confirmed that: (ii) do not require any adjustment for "
                      "modification as there is no modification in the "
                      "underlying audit reports.",
    })
    assert _field(ex.extract_governance(RANGES), "governance.auditor_opinion") is None


def test_no_opinion_language_emits_no_clean_opinion():
    ex = _extractor({
        1: HEADING + "Basis of preparation and restatement adjustments.",
        2: "The Restated Consolidated Financial Information has been compiled.",
        3: "UDIN: 26100459QBZXUZ8355",
    })
    extractions = ex.extract_governance(RANGES)
    assert _field(extractions, "governance.auditor_opinion") is None


def test_negative_emphasis_statement_is_not_an_emphasis_of_matter():
    """'There are no Emphasis of matters in auditor's report' is a negative
    disclosure; classifying it as an EOM would invert its meaning."""
    text = (
        "There are no Emphasis of matters in auditor's report for the period "
        "/ year ended 31st March, 2026."
    )
    assert SectionExtractor._has_positive_emphasis_of_matter(text) is False
    ex = _extractor({1: HEADING + text, 2: "UDIN: 26100459QBZXUZ8355"})
    assert _field(ex.extract_governance(RANGES), "governance.auditor_opinion") is None


def test_positive_emphasis_of_matter_is_classified():
    text = "Emphasis of Matter: we draw attention to Note 4 regarding the scheme."
    assert SectionExtractor._has_positive_emphasis_of_matter(text) is True
    ex = _extractor({1: HEADING + text, 2: "UDIN: 26100459QBZXUZ8355"})
    extraction = _field(ex.extract_governance(RANGES), "governance.auditor_opinion")
    assert extraction.candidate_value == "emphasis_of_matter"


def test_qualified_opinion_dominates_a_later_no_modification_sentence():
    ex = _extractor({
        1: HEADING + "Basis for qualified opinion: inventory was not verified.",
        2: "8. we report that the Restated Consolidated Financial Information "
           "… there is no modification in the underlying audit reports.",
        3: "UDIN: 26100459QBZXUZ8355",
    })
    assert _field(ex.extract_governance(RANGES), "governance.auditor_opinion").candidate_value == "qualified"


def test_going_concern_uncertainty_requires_positive_language():
    positive = _extractor({
        1: HEADING + "Material uncertainty related to going concern: the Group "
                     "has net current liabilities.",
        2: "UDIN: 26100459QBZXUZ8355",
    })
    extraction = _field(
        positive.extract_governance(RANGES), "governance.going_concern_uncertainty"
    )
    assert extraction is not None and extraction.candidate_value is True

    # A measurement convention ("transferred on a going concern basis") is
    # not an uncertainty.
    convention = _extractor({
        1: HEADING + "Assets were transferred at carrying values on a going "
                     "concern basis with effect from March 31, 2019.",
        2: "UDIN: 26100459QBZXUZ8355",
    })
    assert _field(
        convention.extract_governance(RANGES), "governance.going_concern_uncertainty"
    ) is None


def test_absent_going_concern_disclosure_is_never_emitted_as_false():
    """The previous implementation emitted False (with a quote that appears
    nowhere in the source) whenever an auditor name was found."""
    ex = _extractor({
        1: HEADING + "The financial statements have been audited by Example & "
                     "Associates LLP. Our opinion is not modified.",
        2: "UDIN: 26100459QBZXUZ8355",
    })
    extractions = ex.extract_governance(RANGES)
    assert _field(extractions, "governance.going_concern_uncertainty") is None


@pytest.mark.slow
def test_jio_real_filing_opinion_and_going_concern():
    """Live pin on the committed RHP (pp. 321-324, 430)."""
    doc, _ = DocumentExtractor().extract_from_pdf(
        pdf_path=JIO_PDF, allow_fixture_fallbacks=False
    )
    governance = doc["governance"]
    assert governance["auditor_opinion"] == "unqualified"
    # The only "going concern" string in the 591-page filing is the 2019
    # scheme's measurement convention (p. 253); it is not an uncertainty.
    assert governance["going_concern_uncertainty"] is None
    assert governance["eom_materiality"] is None
