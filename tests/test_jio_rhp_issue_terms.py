"""Jio Platforms RHP: actual-disclosure extraction and completion path.

The committed PDF (``evidence/non-authoritative/jio/…``) is
NON-AUTHORITATIVE investigation evidence: it establishes what the
document states, never official provenance. Findings from inspecting
the real 591-page RHP and running the supported paths:

- company ``JIO PLATFORMS LIMITED`` (cover logo matter previously
  polluted the name, corrupting the runtime IPO ID);
- fresh-issue only: Offer for Sale ``Not applicable`` on the cover
  table -> ``issue.ofs = 0.0`` filing-established (the extractor only
  recognised the word ``NIL``);
- 270,000,000 fresh shares disclosed; bid/issue dates disclosed with
  weekday prefixes (previously unrecognised);
- price band and lot are genuine ``[●]`` / "will be decided"
  placeholders, and the fresh-issue amount is ``₹[●] million`` -- the
  filing cannot supply them, so an accepted official document remains
  necessary. The final Prospectus is the completing document class:
  it states the fresh-issue aggregating amount, which the verified
  pathway now carries (parser + assembly, unit-converted).

Transport below is controlled (injected fetcher): mechanics only,
NOT live official-source retrieval.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.extraction.prospectus_terms import ProspectusTermsParser
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.service import (
    IngestionAwaitingIssueTermsError,
    PresentationConfig,
    PresentationService,
)

JIO_PDF = REPO_ROOT / "evidence" / "non-authoritative" / "jio" / "U72900GJ2019PLC110816_JIO.pdf"

PROSPECTUS_TEXT = """Prospectus
Dated: October 24, 2026
100% Book Built Offer
JIO PLATFORMS LIMITED
CORPORATE IDENTITY NUMBER: U72900GJ2019PLC110816
THE ISSUE IS A FRESH ISSUE OF 270,000,000 EQUITY SHARES AGGREGATING UP TO Rs.148,500.00 MILLION BY OUR COMPANY.
"Price Band" Price band of a minimum price of Rs 500 per Equity Share (i.e., the Floor Price) and the
maximum price of Rs 550 per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" 25 Equity Shares and in multiples of 25 Equity Shares thereafter.
"""


@pytest.fixture(scope="module")
def jio_canonical():
    doc, _report = DocumentExtractor().extract_from_pdf(
        pdf_path=JIO_PDF, allow_fixture_fallbacks=False
    )
    return doc


def test_jio_filing_discloses_identity_ofs_dates_and_fresh_shares(jio_canonical):
    doc = jio_canonical
    assert doc["company_name"] == "JIO PLATFORMS LIMITED"
    assert doc["ipo_id"] == "JIO-PLATFORMS-LIMITED"
    issue = doc["issue"]
    # Fresh-issue only, as stated on the cover table ("Not applicable").
    assert issue["ofs"] == 0.0
    assert issue["ofs_sellers"] == []
    assert issue["fresh_shares"] == 270000000
    assert issue["open_date"] == "2026-10-21"
    assert issue["close_date"] == "2026-10-23"
    # Genuine placeholders: never extracted, never invented.
    assert issue["price_band_low"] is None
    assert issue["price_band_high"] is None
    assert issue["lot_size"] is None
    assert issue["fresh_issue"] is None


def _stub_extractor(cover: str):
    extractor = SectionExtractor.__new__(SectionExtractor)
    extractor.page_count = 4
    extractor.doc = SimpleNamespace(source_id="RHP-TEST-JIO")
    extractor.extract_page_text = lambda p: cover if p == 1 else ""
    return extractor


def test_cover_logo_lines_do_not_pollute_company_name():
    cover = "A\nMPLS\n\nJIO PLATFORMS LIMITED\nCORPORATE IDENTITY NUMBER: U72900GJ2019PLC110816\n"
    fields = {ex.field_path: ex for ex in _stub_extractor(cover).extract_cover_and_offer()}
    assert fields["company_name"].candidate_value == "JIO PLATFORMS LIMITED"


def test_ofs_not_applicable_means_no_offer_for_sale():
    cover = (
        "ACME LIMITED\nDETAILS OF THE ISSUE\nTYPE FRESH ISSUE SIZE OFFER FOR SALE SIZE\n"
        "Fresh Issue Up to 1,000 Equity Shares aggregating up to Rs.[x] million\nNot applicable\n"
    )
    fields = {ex.field_path: ex for ex in _stub_extractor(cover).extract_cover_and_offer()}
    assert fields["issue.ofs"].candidate_value == 0.0
    assert fields["issue.ofs_sellers"].candidate_value == []


def test_weekday_prefixed_issue_dates_are_recognised():
    cover = (
        "ACME LIMITED\nBID/ ISSUE OPENS\nON\nWEDNESDAY,\nOCTOBER 21, 2026\n"
        "BID/ ISSUE CLOSES\nON(1)\nFRIDAY,\nOCTOBER 23, 2026\n"
    )
    fields = {ex.field_path: ex for ex in _stub_extractor(cover).extract_cover_and_offer()}
    assert fields["issue.open_date"].candidate_value == "2026-10-21"
    assert fields["issue.close_date"].candidate_value == "2026-10-23"


def test_prospectus_carries_only_stated_fresh_amount():
    result = ProspectusTermsParser().parse_from_text(PROSPECTUS_TEXT)
    assert result.fresh_issue_amount.value == 148500.0
    assert result.fresh_issue_amount_unit == "INR_MILLIONS"
    undisclosed = PROSPECTUS_TEXT.replace("Rs.148,500.00 MILLION", "Rs.[x] MILLION")
    result = ProspectusTermsParser().parse_from_text(undisclosed)
    assert result.fresh_issue_amount is None  # placeholder never establishes an amount


def test_jio_without_official_source_fails_closed_on_all_missing_required_terms(tmp_path, jio_canonical, monkeypatch):
    monkeypatch.setattr(
        DocumentExtractor,
        "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (jio_canonical, {}),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    with pytest.raises(IngestionAwaitingIssueTermsError) as excinfo:
        service.ingest_document(file_bytes=b"%PDF-1.4 test", filename="jio.pdf", mode="final")
    # Explicit no-OFS is filing-established; monetary fresh amount is still
    # a placeholder and must enter the same required-term gate as pricing.
    assert excinfo.value.missing_fields == ["price_band_low", "price_band_high", "lot_size", "fresh_issue"]


def test_jio_completes_via_verified_prospectus_pathway(tmp_path):
    from ipo_screening.issue_terms import HttpProspectusProvider

    provider = HttpProspectusProvider(
        {"JIO-PLATFORMS-LIMITED": "https://www.sebi.gov.in/sebi_data/attachdocs/jio-prospectus.pdf"},
        fetcher=lambda u: PROSPECTUS_TEXT.encode(),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[provider]),
    )
    service = PresentationService(cfg)
    resp = service.ingest_document(
        file_bytes=JIO_PDF.read_bytes(), filename=JIO_PDF.name, mode="final"
    )
    assert resp.ipo_id == "JIO-PLATFORMS-LIMITED"
    record = service.eval_store.read(resp.evaluation_id)
    issue = record["input_snapshot"]["input"]["issue"]
    assert (issue["price_band_low"], issue["price_band_high"], issue["lot_size"]) == (500.0, 550.0, 25)
    assert issue["ofs"] == 0.0  # filing-established: no Offer for Sale
    # Stated Rs.148,500 million. The document's reporting unit is detected
    # as INR_MILLIONS (the statement headers say "in ₹ million"), so the
    # amount is recorded in its own unit without cross-unit conversion
    # (2026-10-19 unit-detection correction; previously misdetected as
    # INR_LAKHS and scaled to 1,485,000).
    assert issue["fresh_issue"] == 148500.0
    assert issue["fresh_shares"] == 270000000

    evidence = service.get_evaluation_evidence(resp.evaluation_id)
    items = {item.evidence_id: item for item in evidence.items}
    amount = items["EV-issue.fresh_issue"]
    assert amount.extracted_value == 148500.0
    assert amount.verification == "OFFICIAL_VERIFIED"  # stated in the verified Prospectus
    assert items["EV-issue-ofs"].verification == "FILING"  # never re-labelled official
