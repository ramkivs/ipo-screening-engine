"""Official Prospectus issue-term pathway (authorized 2026-10-17).

A final Prospectus filed on an allow-listed official host is a distinct
document class from a Price Band Notice. This pathway:

- classifies documents truthfully (Prospectus vs Notice vs RHP), with no
  cross-class mislabelling (``SRC-PROSPECTUS-…`` / ``OFFICIAL_PROSPECTUS``,
  never ``SRC-PBN-…`` notice provenance);
- extracts only terms the document explicitly establishes;
- fails closed on undisclosed (``[●]``), missing, ambiguous or
  wrong-issuer evidence, and on non-allow-listed hosts (the allowlist is
  unchanged -- ``nsearchives.nseindia.com`` remains outside it);
- preserves verified values against conflicting manual entries.

HTTP tests use mocked transport: they prove channel mechanics, NOT live
source acceptance. Live retrieval from SEBI could not be executed from
the sandbox (egress restricted); see
docs/investigation/OFFICIAL-PRICE-BAND-NOTICE-EVIDENCE-GAP-2026-10-17.md.
"""

from __future__ import annotations

import copy
import io

import pytest
from fastapi.testclient import TestClient

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.extraction.price_band_notice import PriceBandNoticeParser
from ipo_screening.extraction.prospectus_terms import (
    ProspectusClassificationError,
    ProspectusTermsParser,
)
from ipo_screening.issue_terms import HttpProspectusProvider, IssueTermsResolver
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService

SEBI_PROSPECTUS_URL = "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"
IPO_ID = "VISHAL-NIRMITI-LIMITED"
COMPANY = "Vishal Nirmiti Limited"
EXPLANATION = "Exchange price-band announcement read by the operator."

# Synthetic prospectus text mirroring the definition language of the real
# final Prospectus (floor/cap definitions, Bid Lot). Mechanics fixture
# only -- it is not the authentic document and proves nothing about it.
PROSPECTUS_TEXT = """Prospectus
Dated: October 05, 2026
100% Book Built Offer
VISHAL NIRMITI LIMITED
CORPORATE IDENTITY NUMBER: U01122MH1994PLC185445
"Price Band" Price band of a minimum price of ₹ 208 per Equity Share (i.e., the Floor Price) and the
maximum price of ₹ 220 per Equity Share (i.e., the Cap Price), including any revisions thereof.
The Price Band and the minimum Bid Lot for the Offer was decided by our Company in consultation
with the BRLM and was advertised in all editions of Financial Express.
"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.
"Offered Shares" 15,00,000 Equity Shares aggregating to ₹ 3,300.00 lakhs as part of the Offer for Sale.
"""

NOTICE_TEXT = (REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt").read_text(encoding="utf-8")

RHP_TEXT = """Red Herring Prospectus
Dated: September 24, 2026
100% Book Built Offer
VISHAL NIRMITI LIMITED
CORPORATE IDENTITY NUMBER: U01122MH1994PLC185445
"Price Band" Price band of a minimum price of ₹ [●] per Equity Share (i.e., the Floor Price) and the
maximum price of ₹ [●] per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" [●] Equity Shares and in multiples thereof.
"""


# ---------------------------------------------------------------------------
# Classification: truthful, no cross-class mislabelling
# ---------------------------------------------------------------------------


def test_prospectus_classification_and_terms():
    result = ProspectusTermsParser().parse_from_text(PROSPECTUS_TEXT)
    assert result.is_classified_prospectus is True
    assert result.document_class == "OFFICIAL_PROSPECTUS"
    assert result.company_name == "VISHAL NIRMITI LIMITED"
    assert result.cin == "U01122MH1994PLC185445"
    assert result.price_band_low.value == 208
    assert result.price_band_high.value == 220
    assert result.lot_size.value == 68
    assert result.source_ref.source_id.startswith("SRC-PROSPECTUS-")
    assert "Final Prospectus" in result.price_band_low.locator
    payload = result.to_enrichment_dict()
    assert payload["sources"][0]["note"] == "OFFICIAL_PROSPECTUS"
    assert payload["sources"][0]["source_id"].startswith("SRC-PROSPECTUS-")


def test_notice_is_not_a_prospectus_and_prospectus_is_not_mislabelled():
    # The Price Band Notice classifies under its own parser...
    notice_result = PriceBandNoticeParser().parse_from_text(NOTICE_TEXT)
    assert notice_result.is_classified_notice is True
    assert notice_result.source_ref.source_id.startswith("SRC-PBN-")
    # ...and is rejected by the Prospectus parser (no prospectus identity).
    with pytest.raises(ProspectusClassificationError):
        ProspectusTermsParser().parse_from_text(NOTICE_TEXT)


def test_rhp_with_undisclosed_terms_is_rejected():
    with pytest.raises(ProspectusClassificationError):
        ProspectusTermsParser().parse_from_text(RHP_TEXT)


def test_prospectus_without_lot_extracts_only_supported_terms():
    text = PROSPECTUS_TEXT.replace(
        '"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.\n', ""
    )
    result = ProspectusTermsParser().parse_from_text(text)
    assert result.price_band_low.value == 208
    assert result.price_band_high.value == 220
    assert result.lot_size is None  # not inferred, not defaulted


# ---------------------------------------------------------------------------
# Provider / resolver mechanics (mocked transport)
# ---------------------------------------------------------------------------


def _provider(url=SEBI_PROSPECTUS_URL, payload=PROSPECTUS_TEXT):
    return HttpProspectusProvider({IPO_ID: url}, fetcher=lambda u: payload.encode("utf-8"))


def test_provider_verifies_only_allowlisted_official_hosts():
    candidate, report = _provider().find(COMPANY, IPO_ID)
    assert candidate is not None and candidate.verified is True
    assert candidate.provider == "official-prospectus"

    nse_archives = _provider(url="https://nsearchives.nseindia.com/corporate/FP_INE1O5L01025_06OCT2026.pdf")
    candidate, report = nse_archives.find(COMPANY, IPO_ID)
    assert candidate is None and report.outcome == "REJECTED"  # allowlist not broadened

    third_party = _provider(url="https://example.com/prospectus.pdf")
    candidate, report = third_party.find(COMPANY, IPO_ID)
    assert candidate is None and report.outcome == "REJECTED"


def test_provider_rejects_wrong_issuer_and_non_prospectus():
    wrong = PROSPECTUS_TEXT.replace("VISHAL NIRMITI LIMITED", "OTHER ISSUER LIMITED")
    candidate, report = _provider(payload=wrong).find(COMPANY, IPO_ID)
    assert candidate is None and report.outcome == "REJECTED"

    candidate, report = _provider(payload=NOTICE_TEXT).find(COMPANY, IPO_ID)
    assert candidate is None and report.outcome == "REJECTED"


def test_resolver_reports_document_class_and_partial_resolution():
    resolver = IssueTermsResolver(providers=[_provider()])
    outcome = resolver.resolve(
        company_name=COMPANY, ipo_id=IPO_ID, missing_fields=["price_band_low", "price_band_high", "lot_size"]
    )
    assert outcome.status == "RESOLVED"
    assert outcome.verified is True
    assert outcome.document_class == "OFFICIAL_PROSPECTUS"
    assert outcome.to_dict()["document_class"] == "OFFICIAL_PROSPECTUS"

    no_lot = PROSPECTUS_TEXT.replace(
        '"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.\n', ""
    )
    resolver = IssueTermsResolver(providers=[_provider(payload=no_lot)])
    outcome = resolver.resolve(
        company_name=COMPANY, ipo_id=IPO_ID, missing_fields=["price_band_low", "price_band_high", "lot_size"]
    )
    assert outcome.status == "PARTIAL"
    assert outcome.unresolved_fields == ["lot_size"]


def test_resolver_fails_closed_when_prospectus_unavailable():
    def boom(url):
        raise ConnectionError("egress blocked")

    provider = HttpProspectusProvider({IPO_ID: SEBI_PROSPECTUS_URL}, fetcher=boom)
    outcome = IssueTermsResolver(providers=[provider]).resolve(
        company_name=COMPANY, ipo_id=IPO_ID, missing_fields=["price_band_low"]
    )
    assert outcome.verified is False
    assert outcome.notice is None
    assert outcome.status in ("UNAVAILABLE", "UNPUBLISHED")


# ---------------------------------------------------------------------------
# End-to-end ingestion: OFFICIAL_VERIFIED via Prospectus, manual protected
# ---------------------------------------------------------------------------


def _client(tmp_path, monkeypatch, golden_input, providers):
    doc = copy.deepcopy(golden_input)
    for field_name in ("price_band_low", "price_band_high", "lot_size"):
        doc["issue"][field_name] = None
    monkeypatch.setattr(
        DocumentExtractor,
        "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (copy.deepcopy(doc), {}),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=providers),
    )
    service = PresentationService(cfg)
    client = TestClient(
        create_app(service),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )
    return client, service


def _upload(client, path, **data):
    payload = {"mode": "final"}
    payload.update(data)
    return client.post(
        path,
        files={"file": ("filing.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data=payload,
    )


def test_ingest_resolves_via_prospectus_as_official_verified(tmp_path, monkeypatch, golden_input):
    client, service = _client(tmp_path, monkeypatch, golden_input, [_provider()])
    res = _upload(client, "/api/v1/ingest/document")
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["issue_terms"]["status"] == "RESOLVED"
    assert body["issue_terms"]["verified"] is True
    assert body["issue_terms"]["document_class"] == "OFFICIAL_PROSPECTUS"
    assert body["issue_terms"]["provider"] == "official-prospectus"

    record = service.eval_store.read(body["evaluation_id"])
    issue = record["input_snapshot"]["input"]["issue"]
    assert (issue["price_band_low"], issue["price_band_high"], issue["lot_size"]) == (208.0, 220.0, 68)

    evidence = client.get(f"/api/v1/evaluations/{body['evaluation_id']}/evidence").json()
    items = {item["field"]: item for item in evidence["items"]}
    low = items["EV-issue.price_band_low"]
    assert low["extracted_value"] == 208.0
    assert low["verification"] == "OFFICIAL_VERIFIED"
    assert low["source"].startswith("SRC-PROSPECTUS-")
    assert "Final Prospectus" in (low["locator"] or "")


def test_manual_conflict_against_prospectus_values_verified_wins(
    tmp_path, monkeypatch, golden_input
):
    client, service = _client(tmp_path, monkeypatch, golden_input, [_provider()])
    conflict = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="200",
        explanation=EXPLANATION,
    )
    assert conflict.status_code == 409
    entry = conflict.json()["conflicts"][0]
    assert entry["existing_origin"] == "OFFICIAL_VERIFIED"
    assert entry["existing_value"] == 208.0
    assert service.eval_store.list_evaluations() == []

    resolved = _upload(
        client,
        "/api/v1/ingest/manual-terms",
        price_band_low="200",
        explanation=EXPLANATION,
        confirm_conflicts="true",
    )
    assert resolved.status_code == 201, resolved.text
    assert resolved.json()["issue_terms"]["document_class"] == "OFFICIAL_PROSPECTUS"
    record = service.eval_store.read(resolved.json()["evaluation_id"])
    assert record["input_snapshot"]["input"]["issue"]["price_band_low"] == 208.0
    assert not any(
        item.get("extraction_method") == "MANUAL_ENTRY"
        for item in record["evidence"]["evidence"]
        if "price_band_low" in (item.get("evidence_id") or "")
    )


def test_env_configuration_wires_prospectus_provider(monkeypatch):
    from ipo_screening.issue_terms import build_resolver_from_env

    monkeypatch.setenv(
        "IPO_PROSPECTUS_URLS", '{"VISHAL-NIRMITI-LIMITED": "' + SEBI_PROSPECTUS_URL + '"}'
    )
    resolver = build_resolver_from_env()
    assert any(p.name == "official-prospectus" for p in resolver.providers)


# ---------------------------------------------------------------------------
# Regression: live-failure root cause (2026-10-17)
#
# The real final Prospectus references the "Red Herring Prospectus" in its
# opening LISTING section. The original classification rejected any
# document whose first pages mentioned "red herring", so the genuine
# SEBI-filed Prospectus was REJECTED, the resolver reported UNAVAILABLE,
# and ingestion returned AWAITING_ISSUE_TERMS for all four terms.
# Classification now turns on the dated document title.
# ---------------------------------------------------------------------------

REALISTIC_FINAL_PROSPECTUS = """Prospectus
Dated: October 05, 2026
100% Book Built Offer
VISHAL NIRMITI LIMITED
CORPORATE IDENTITY NUMBER: U01122MH1994PLC185445
LISTING
The Equity Shares issued through the Red Herring Prospectus and this Prospectus are proposed to be
listed on the National Stock Exchange of India Limited and BSE Limited.
"Price Band" Price band of a minimum price of ₹ 208 per Equity Share (i.e., the Floor Price) and the
maximum price of ₹ 220 per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.
"""


def test_final_prospectus_referencing_rhp_in_body_is_accepted():
    result = ProspectusTermsParser().parse_from_text(REALISTIC_FINAL_PROSPECTUS)
    assert result.is_classified_prospectus is True
    assert (result.price_band_low.value, result.price_band_high.value, result.lot_size.value) == (208, 220, 68)


def test_red_herring_titles_are_rejected_by_title():
    rhp = REALISTIC_FINAL_PROSPECTUS.replace("Prospectus\nDated:", "Red Herring Prospectus\nDated:")
    with pytest.raises(ProspectusClassificationError):
        ProspectusTermsParser().parse_from_text(rhp)
    drhp = REALISTIC_FINAL_PROSPECTUS.replace("Prospectus\nDated:", "Draft Red Herring Prospectus\nDated:")
    with pytest.raises(ProspectusClassificationError):
        ProspectusTermsParser().parse_from_text(drhp)


def test_default_fetcher_uses_browser_compatible_headers(monkeypatch):
    import urllib.request

    from ipo_screening import issue_terms as issue_terms_module

    captured = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return PROSPECTUS_TEXT.encode("utf-8")

    def fake_urlopen(request, timeout=None):
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    provider = HttpProspectusProvider({IPO_ID: SEBI_PROSPECTUS_URL})  # no injected fetcher
    candidate, report = provider.find(COMPANY, IPO_ID)
    assert candidate is not None and candidate.verified is True
    assert "Mozilla/5.0" in captured["headers"].get("User-agent", "")


def test_prospectus_ingest_derives_ofs_from_seller_shares(tmp_path, monkeypatch, golden_input):
    """OFS is not independently blocked: once the Prospectus establishes
    the cap, the established assembly derivation (seller shares x cap)
    supplies OFS, exactly as on the notice pathway."""
    doc = copy.deepcopy(golden_input)
    for field_name in ("price_band_low", "price_band_high", "lot_size", "ofs"):
        doc["issue"][field_name] = None
    assert doc["issue"]["ofs_sellers"]  # RHP-established seller shares
    monkeypatch.setattr(
        DocumentExtractor,
        "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (copy.deepcopy(doc), {}),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[_provider()]),
    )
    service = PresentationService(cfg)
    client = TestClient(
        create_app(service),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )
    res = _upload(client, "/api/v1/ingest/document")
    assert res.status_code == 201, res.text
    record = service.eval_store.read(res.json()["evaluation_id"])
    assert record["input_snapshot"]["input"]["issue"]["ofs"] == 3300.0
