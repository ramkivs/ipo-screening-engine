"""Cross-issuer regression for the Regulation 17 institutional lock-in carve-out.

``capital_structure.large_holders_unlocked_early`` is set only when a filing
discloses the Regulation 17 pre-Offer lock-in carve-out for an institutional /
venture holder category: those shares are locked for six months from the date
of *purchase* instead of the general six months from Allotment, so a holder
that purchased before the Offer is free at Allotment.  The rule must be
issuer-neutral -- it may not depend on any issuer's names, pages, dates,
transaction values or passages.

Positive cases come from real filings in the repository:

* Paras Healthcare RHP p. 117
  (``evidence/non-authoritative/paras-healthcare/``);
* Jio RHP p. 105 (``evidence/non-authoritative/jio/``);
* Moneyview prospectus p. 485
  (``handoff/investigation/A8-M-MONEYVIEW-SOURCE-EVIDENCE/``).  Its provision
  sits in the bidder-category section, outside the capital-structure page
  range the TOC router routes for that filing, so it is exercised at the rule
  level from the real page text rather than through the routed range.

Negative cases are real filings whose promoter lock-in is disclosed without any
institutional carve-out (Vishal Nirmiti, R.K. Fashion).  Ambiguous, absent and
wording-variation cases are synthetic page texts and are labelled as such.
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
# 1. Positive: the carve-out is read from real filings
# ---------------------------------------------------------------------------


def test_paras_rhp_institutional_carve_out_sets_the_flag(paras_fields):
    early = paras_fields[EARLY_PATH]
    assert early.candidate_value is True
    assert early.page == 117
    assert early.quote_is_processing is False
    assert "date of purchase" in early.quote
    assert "VCF" in early.quote


def test_jio_rhp_institutional_carve_out_sets_the_flag(jio_fields):
    early = jio_fields[EARLY_PATH]
    assert early.candidate_value is True
    assert early.page == 105
    assert early.quote_is_processing is False
    assert "date of purchase" in early.quote


def test_moneyview_carve_out_wording_sets_the_flag():
    """A different wording (plural categories, spelled out) is still read.

    The provision sits outside the capital-structure page range the TOC router
    routes for this filing, so it is exercised from the real page text at the
    rule level.  This documents that the rule keys on the disclosed semantics,
    not on the section the filing happens to print it in.
    """
    if not MONEYVIEW_PDF.is_file():
        pytest.skip("retained Moneyview prospectus PDF is not present in this checkout")
    reader = pypdf.PdfReader(str(MONEYVIEW_PDF))
    text = reader.pages[484].extract_text() or ""
    extractor = _synthetic_section({485: text})
    fields = _fields(extractor.extract_capital_structure({"capital_structure": (485, 485)}))
    early = fields[EARLY_PATH]
    assert early.candidate_value is True
    assert early.page == 485
    assert early.quote_is_processing is False
    assert "date of purchase" in early.quote


# ---------------------------------------------------------------------------
# 2. Negative: a promoter lock-in without an institutional carve-out
# ---------------------------------------------------------------------------


def test_vishal_promoter_lock_in_without_carve_out_stays_unknown(vishal_fields):
    assert EARLY_PATH not in vishal_fields
    assert vishal_fields["capital_structure.promoter_lockin_in_place"].candidate_value is True


def test_rk_fashion_promoter_lock_in_without_carve_out_stays_unknown(rkfashion_fields):
    assert EARLY_PATH not in rkfashion_fields
    assert rkfashion_fields["capital_structure.promoter_lockin_in_place"].candidate_value is True


# ---------------------------------------------------------------------------
# 3. Wording variations (synthetic fixtures -- not represented in the corpus)
# ---------------------------------------------------------------------------

SYNTHETIC_POSITIVE = [
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


@pytest.mark.parametrize("sentence", SYNTHETIC_POSITIVE)
def test_synthetic_wording_variants_set_the_flag(sentence):
    fields = _fields(
        _synthetic_section({117: sentence}).extract_capital_structure(
            {"capital_structure": (117, 117)}
        )
    )
    early = fields[EARLY_PATH]
    assert early.candidate_value is True
    assert early.page == 117
    assert early.quote_is_processing is False
    assert "purchase" in early.quote or "acquisition" in early.quote


# ---------------------------------------------------------------------------
# 4. Ambiguous: a category mention is not enough
# ---------------------------------------------------------------------------

SYNTHETIC_AMBIGUOUS = [
    # category mentioned, but no purchase-anchored lock-in
    "Equity Shares held by a VCF or Category I AIF are subject to the lock-in "
    "requirements prescribed under Regulation 17 of the SEBI ICDR Regulations.",
    # the institutional category gets the *general* (Allotment-anchored) lock-in
    "Equity Shares held by a VCF shall be locked-in for a period of six months "
    "from the date of Allotment.",
    # a longer lock-in anchored to purchase is not an early unlock
    "Equity Shares held by a VCF shall be locked-in for a period of three years "
    "from the date of purchase.",
]


@pytest.mark.parametrize("sentence", SYNTHETIC_AMBIGUOUS)
def test_synthetic_ambiguous_disclosures_stay_unknown(sentence):
    fields = _fields(
        _synthetic_section({117: sentence}).extract_capital_structure(
            {"capital_structure": (117, 117)}
        )
    )
    assert EARLY_PATH not in fields


# ---------------------------------------------------------------------------
# 5. Absent disclosure
# ---------------------------------------------------------------------------


def test_absent_lock_in_disclosure_stays_unknown():
    fields = _fields(
        _synthetic_section({120: "The Company has no pending litigation."}).extract_capital_structure(
            {"capital_structure": (120, 120)}
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
    assert fields["capital_structure.promoter_lockin_in_place"].candidate_value is True


# ---------------------------------------------------------------------------
# 6. The extraction reaches the canonical field and the evaluator
# ---------------------------------------------------------------------------


def test_carve_out_extraction_reaches_the_canonical_field():
    doc = SourceDocument(source_id="RHP-SYNTHETIC", content_hash="regression")
    extraction = RawExtraction(
        field_path=EARLY_PATH,
        candidate_value=True,
        raw_text="locked-in for a period of at least six months from the date of purchase",
        page=117,
        section="Capital Structure",
        locator="Institutional lock-in carve-out",
        quote="locked-in for a period of at least six months from the date of purchase",
    )
    canonical = CanonicalInputBuilder(doc, [extraction], allow_fixture_fallbacks=False).build()
    assert canonical["capital_structure"]["large_holders_unlocked_early"] is True


def test_lockin_bucket_consumes_the_flag(make_input, config):
    """The evaluator reads the flag: True -> weak, False -> intact, None -> UNKNOWN."""
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
