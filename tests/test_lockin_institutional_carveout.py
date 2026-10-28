"""A34 semantic boundary for ``capital_structure.large_holders_unlocked_early``.

Approved decision A34, alternative B: a category-specific institutional
lock-in carve-out alone does **not** establish an early unlock.  Regulation
17(1)(c) removes the six-months-from-Allotment lock-in for VCF / Category I or
II AIF / FVCI holders and replaces it with a *minimum* six months from the
date of purchase.  The filing prints no purchase dates, so a carve-out can
produce an earlier, equal or later release; it is not evidence of any holder
being released early.  With no other evidence the field must stay ``null`` and
C ``lockin`` must stay UNKNOWN.

The reader sets the flag only where a single sentence evidences an **actual
early release** of large / pre-IPO / institutional holders: a named holder
group, a release act, a lock-in context, and an explicit early / before-expiry
timing.  Pledge release, ordinary transferability, a release on normal expiry,
and hypothetical or negated language all stay UNKNOWN.

Real filings examined (five): Paras Healthcare p. 117, Jio p. 105 and
Moneyview p. 485 print the carve-out; Vishal Nirmiti and R.K. Fashion print
only a promoter lock-in.  **None of the five prints an evidenced early
release.**  Zero matches in this corpus is a corpus limitation, not evidence
that early releases never occur, so genuine positive cases are retained as
labelled synthetic fixtures below.  The real-filing carve-out quotes and pages
are asserted in the tests, so provenance is verified rather than assumed.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pypdf
import pytest

from conftest import REPO_ROOT, criterion, run
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import RawExtraction, SourceDocument
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.extraction.toc import TOCRouter

PARAS_PDF = (
    REPO_ROOT
    / "evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf"
)
JIO_PDF = REPO_ROOT / "evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf"
MONEYVIEW_PDF = (
    REPO_ROOT
    / "handoff/investigation/A8-M-MONEYVIEW-SOURCE-EVIDENCE/Moneyview_Final_Prospectus_Full.pdf"
)
VISHAL_PDF = REPO_ROOT / "handoff/reference/U01122MH1994PLC185445-vishal nirmiti.pdf"
RKFASHION_PDF = (
    REPO_ROOT / "handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf"
)

EARLY_PATH = "capital_structure.large_holders_unlocked_early"
CAPITAL_LOCKIN_PATH = "capital_structure.promoter_lockin_in_place"


def _fields(extractions) -> dict:
    return {ex.field_path: ex for ex in extractions}


def _synthetic_section(pages: dict[int, str]) -> SectionExtractor:
    """A SectionExtractor fed with literal page text (synthetic fixture)."""
    extractor = SectionExtractor.__new__(SectionExtractor)
    extractor.page_count = max(pages)
    extractor.doc = SimpleNamespace(source_id="RHP-SYNTHETIC")
    extractor._text_cache = {}
    extractor.extract_page_text = lambda p: pages.get(p, "")
    return extractor


def _routed_fields(pdf_path: Path) -> dict:
    """Run the reader over the TOC-routed capital-structure range of a real filing."""
    reader = pypdf.PdfReader(str(pdf_path))
    doc = SourceDocument(source_id=f"SRC-{pdf_path.stem[:12]}", content_hash="regression")
    router = TOCRouter.from_pdf(reader)
    page_range = router.get_page_range("capital_structure")
    extractor = SectionExtractor(doc, reader)
    return _fields(
        extractor.extract_capital_structure({"capital_structure": page_range})
    )


def _page_text(pdf_path: Path, printed_page: int) -> str:
    reader = pypdf.PdfReader(str(pdf_path))
    return " ".join((reader.pages[printed_page - 1].extract_text() or "").split())


@pytest.fixture(scope="module")
def paras_fields() -> dict:
    if not PARAS_PDF.is_file():
        pytest.skip("retained Paras evidence PDF is not present in this checkout")
    return _routed_fields(PARAS_PDF)


@pytest.fixture(scope="module")
def jio_fields() -> dict:
    if not JIO_PDF.is_file():
        pytest.skip("retained Jio evidence PDF is not present in this checkout")
    return _routed_fields(JIO_PDF)


@pytest.fixture(scope="module")
def vishal_fields() -> dict:
    if not VISHAL_PDF.is_file():
        pytest.skip("retained Vishal Nirmiti PDF is not present in this checkout")
    return _routed_fields(VISHAL_PDF)


@pytest.fixture(scope="module")
def rkfashion_fields() -> dict:
    if not RKFASHION_PDF.is_file():
        pytest.skip("retained R.K. Fashion PDF is not present in this checkout")
    return _routed_fields(RKFASHION_PDF)


# ---------------------------------------------------------------------------
# 1. Real filings: the carve-out is present, verbatim, and does NOT set the flag
# ---------------------------------------------------------------------------


def test_paras_rhp_carve_out_does_not_set_the_flag(paras_fields):
    text = _page_text(PARAS_PDF, 117)
    assert "at least six months from the date of purchase" in text
    assert "VCF" in text
    assert EARLY_PATH not in paras_fields, "a category carve-out is not an early release"
    assert paras_fields[CAPITAL_LOCKIN_PATH].candidate_value is True


def test_jio_rhp_carve_out_does_not_set_the_flag(jio_fields):
    text = _page_text(JIO_PDF, 105)
    assert "at least six months from the date of purchase" in text
    assert "Category I AIF" in text
    assert EARLY_PATH not in jio_fields, "a category carve-out is not an early release"
    assert jio_fields[CAPITAL_LOCKIN_PATH].candidate_value is True


def test_moneyview_carve_out_does_not_set_the_flag():
    """Rule level: Moneyview p. 485 sits outside the routed capital range."""
    if not MONEYVIEW_PDF.is_file():
        pytest.skip("retained Moneyview prospectus PDF is not present in this checkout")
    text = _page_text(MONEYVIEW_PDF, 485)
    assert "date of purchase" in text
    fields = _fields(
        _synthetic_section({485: text}).extract_capital_structure(
            {"capital_structure": (485, 485)}
        )
    )
    assert EARLY_PATH not in fields


def test_vishal_promoter_lock_in_without_carve_out_stays_unknown(vishal_fields):
    assert EARLY_PATH not in vishal_fields
    assert vishal_fields[CAPITAL_LOCKIN_PATH].candidate_value is True


def test_rk_fashion_promoter_lock_in_without_carve_out_stays_unknown(rkfashion_fields):
    assert EARLY_PATH not in rkfashion_fields
    assert rkfashion_fields[CAPITAL_LOCKIN_PATH].candidate_value is True


# ---------------------------------------------------------------------------
# 2. Carve-out wording variations (synthetic) all stay UNKNOWN
# ---------------------------------------------------------------------------

CARVE_OUT_VARIANTS = [
    # the category follows the lock-in clause (reverse order)
    "The Equity Shares shall be locked-in for a period of at least six months "
    "from the date of purchase, except for the Equity Shares held by a VCF or "
    "Category I AIF or Category II AIF or FVCI.",
    # categories spelled out, "from the date of their acquisition"
    "Shares held by a venture capital fund, an alternative investment fund or a "
    "foreign venture capital investor shall be locked in for at least 6 months "
    "from the date of their acquisition.",
    # hyphenation and spacing variants
    "Equity Shares held by a VCF will be locked -in for six months from the "
    "date of purchase.",
    # plural category names
    "Equity Shares held by VCFs or Category I AIFs shall be locked-in for a "
    "period of six months from the date of purchase.",
]


@pytest.mark.parametrize("sentence", CARVE_OUT_VARIANTS)
def test_carve_out_wording_variants_stay_unknown(sentence):
    fields = _fields(
        _synthetic_section({117: sentence}).extract_capital_structure(
            {"capital_structure": (117, 117)}
        )
    )
    assert EARLY_PATH not in fields


# ---------------------------------------------------------------------------
# 3. Ambiguous institutional disclosures stay unresolved
# ---------------------------------------------------------------------------

AMBIGUOUS_DISCLOSURES = [
    # category mentioned, but no purchase-anchored lock-in
    "Equity Shares held by a VCF or Category I AIF are subject to the lock-in "
    "requirements prescribed under Regulation 17 of the SEBI ICDR Regulations.",
    # the institutional category gets the general (Allotment-anchored) lock-in
    "Equity Shares held by a VCF shall be locked-in for a period of six months "
    "from the date of Allotment.",
    # a longer lock-in anchored to purchase is even further from an early release
    "Equity Shares held by a VCF shall be locked-in for a period of three years "
    "from the date of purchase.",
]


@pytest.mark.parametrize("sentence", AMBIGUOUS_DISCLOSURES)
def test_ambiguous_institutional_disclosures_stay_unknown(sentence):
    fields = _fields(
        _synthetic_section({117: sentence}).extract_capital_structure(
            {"capital_structure": (117, 117)}
        )
    )
    assert EARLY_PATH not in fields


# ---------------------------------------------------------------------------
# 4. Unrelated pledge / transferability language must not trigger the flag
# ---------------------------------------------------------------------------

UNRELATED_DISCLOSURES = [
    "The Equity Shares held by our Promoter are pledged and may be released "
    "upon repayment of the loan.",
    "Equity Shares held by a VCF are freely transferable and are not subject "
    "to any lock-in.",
    "The pledge over the promoters' Equity Shares was released on 12 March "
    "2026 after repayment of the loan.",
    "The Equity Shares are freely transferable and the lock-in will apply "
    "only to the promoter contribution.",
]


@pytest.mark.parametrize("sentence", UNRELATED_DISCLOSURES)
def test_pledge_and_transferability_language_stays_unknown(sentence):
    fields = _fields(
        _synthetic_section({117: sentence}).extract_capital_structure(
            {"capital_structure": (117, 117)}
        )
    )
    assert EARLY_PATH not in fields


# ---------------------------------------------------------------------------
# 5. Hypothetical, conditional or negated release language stays UNKNOWN
# ---------------------------------------------------------------------------

UNCERTAIN_RELEASES = [
    "The pre-IPO shareholders may seek an early release of the lock-in from SEBI.",
    "No early release of the lock-in was granted to the VCF shareholders.",
    "The VCF shareholders were not released from lock-in early.",
]


@pytest.mark.parametrize("sentence", UNCERTAIN_RELEASES)
def test_hypothetical_or_negated_release_stays_unknown(sentence):
    fields = _fields(
        _synthetic_section({117: sentence}).extract_capital_structure(
            {"capital_structure": (117, 117)}
        )
    )
    assert EARLY_PATH not in fields


# ---------------------------------------------------------------------------
# 6. Genuine positive cases remain detectable (synthetic: no real-filing case)
# ---------------------------------------------------------------------------

EVIDENCED_EARLY_RELEASES = [
    # dated release explicitly before the general lock-in expires
    "The 4,000,000 Equity Shares held by Meridian Ventures, a pre-IPO "
    "shareholder, were released from lock-in on 15 May 2026, three months "
    "before the expiry of the six-month lock-in period from the date of Allotment.",
    # an explicitly named early release of the lock-in
    "An early release of the lock-in was granted to the VCF and Category I AIF "
    "shareholders on 12 August 2026.",
    # a carve-out sentence plus a separate, evidenced release sentence
    "In terms of Regulation 17(1)(c), equity shares held by a VCF shall be "
    "locked-in for at least six months from the date of purchase. The Board "
    "approved the early release of the VCF's equity shares from lock-in on "
    "3 September 2026, before the expiry of the general lock-in period.",
]


@pytest.mark.parametrize("sentence", EVIDENCED_EARLY_RELEASES)
def test_evidenced_early_release_sets_the_flag(sentence):
    fields = _fields(
        _synthetic_section({117: sentence}).extract_capital_structure(
            {"capital_structure": (117, 117)}
        )
    )
    early = fields[EARLY_PATH]
    assert early.candidate_value is True
    assert early.page == 117
    assert early.quote_is_processing is False
    assert "releas" in early.quote.lower()
    # The quotation is the filing's own matched sentence, not a synthesised one.
    assert early.quote in " ".join(sentence.split())


# ---------------------------------------------------------------------------
# 7. Remaining fail-closed boundaries
# ---------------------------------------------------------------------------


def test_normal_expiry_release_stays_unknown():
    """A release *on* expiry is not an early release."""
    sentence = (
        "Upon expiry of the six-month lock-in from the date of Allotment, the "
        "Equity Shares held by pre-IPO shareholders were released from lock-in."
    )
    fields = _fields(
        _synthetic_section({117: sentence}).extract_capital_structure(
            {"capital_structure": (117, 117)}
        )
    )
    assert EARLY_PATH not in fields


def test_promoter_only_lock_in_does_not_set_the_flag():
    fields = _fields(
        _synthetic_section({116: "The Promoter's Contribution is locked in for a period of three years."}).extract_capital_structure(
            {"capital_structure": (116, 116)}
        )
    )
    assert EARLY_PATH not in fields
    assert fields[CAPITAL_LOCKIN_PATH].candidate_value is True


def test_absent_lock_in_disclosure_stays_unknown():
    fields = _fields(
        _synthetic_section({120: "The Company has no pending litigation."}).extract_capital_structure(
            {"capital_structure": (120, 120)}
        )
    )
    assert EARLY_PATH not in fields


# ---------------------------------------------------------------------------
# 8. The extraction reaches the canonical field and the governing criterion
# ---------------------------------------------------------------------------


def test_early_release_extraction_reaches_the_canonical_field():
    doc = SourceDocument(source_id="RHP-SYNTHETIC", content_hash="regression")
    quote = (
        "The 4,000,000 Equity Shares held by Meridian Ventures, a pre-IPO "
        "shareholder, were released from lock-in three months before the expiry "
        "of the six-month lock-in period."
    )
    extraction = RawExtraction(
        field_path=EARLY_PATH,
        candidate_value=True,
        raw_text=quote,
        page=117,
        section="Capital Structure",
        locator="Evidenced early release of large pre-IPO holders",
        quote=quote,
    )
    canonical = CanonicalInputBuilder(doc, [extraction], allow_fixture_fallbacks=False).build()
    assert canonical["capital_structure"]["large_holders_unlocked_early"] is True


def test_lockin_bucket_consumes_the_flag(make_input, config):
    """The governing criterion: True -> weak (0), False -> intact, None -> UNKNOWN."""
    intact = make_input()
    intact["capital_structure"]["promoter_lockin_in_place"] = True
    intact["capital_structure"]["large_holders_unlocked_early"] = False
    assert criterion(run(intact, config), "lockin").band == "intact"

    weak = make_input()
    weak["capital_structure"]["promoter_lockin_in_place"] = True
    weak["capital_structure"]["large_holders_unlocked_early"] = True
    crit = criterion(run(weak, config), "lockin")
    assert crit.band == "weak"
    assert crit.state == "SCORED"
    assert crit.score == 0.0

    unknown = make_input()
    unknown["capital_structure"]["promoter_lockin_in_place"] = True
    unknown["capital_structure"].pop("large_holders_unlocked_early", None)
    assert criterion(run(unknown, config), "lockin").state == "UNKNOWN"


def test_flag_does_not_change_unrelated_scoring(make_input, config):
    """Setting the flag changes only the lock-in criterion, not other modules."""
    base = make_input()
    base["capital_structure"]["promoter_lockin_in_place"] = True
    base["capital_structure"]["large_holders_unlocked_early"] = False
    weak = make_input()
    weak["capital_structure"]["promoter_lockin_in_place"] = True
    weak["capital_structure"]["large_holders_unlocked_early"] = True

    before = run(base, config)
    after = run(weak, config)

    def module_scores(outcome):
        return {m.module_id: m.score for m in outcome.score.modules}

    scores_before = module_scores(before)
    scores_after = module_scores(after)
    # Only module C can move (the lock-in criterion lives there); every other
    # module score is byte-identical.
    for module_id, score in scores_before.items():
        if module_id == "C":
            continue
        assert scores_after[module_id] == score, module_id
