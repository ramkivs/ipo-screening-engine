"""Runtime-path regression for the recurring Windows AWAITING_ISSUE_TERMS.

Investigation (2026-10-17, commit 40f0dd2): with the real Vishal RHP
and the documented env configuration, filing extraction yields
company ``VISHAL NIRMITI LIMITED`` / IPO ID ``VISHAL-NIRMITI-LIMITED``,
the env-built resolver registers ``official-prospectus`` and attempts
retrieval, and -- with controlled transport -- the whole path evaluates
(208/220/68, OFS 3300 derived, fresh shares correctly separated). The
runtime failure therefore sits at/below retrieval, but three defects
made it undiagnosable and fragile in production:

1. Malformed ``IPO_PROSPECTUS_URLS`` JSON was silently swallowed, so the
   provider was never registered and the resolution carried NO provider
   reports at all.
2. Configured-URL matching was exact-string only: keying the mapping by
   the spaced company name instead of the IPO-ID slug silently missed.
3. The frontend ``ingestDocument`` error path dropped FastAPI's
   ``detail.missing_fields``/``detail.resolution``, so the UI showed
   only the generic AWAITING message (covered in frontend tests), and
   the service collapsed "retrieved but rejected" into "could not be
   retrieved or verified".

All HTTP here uses controlled transport (injected fetchers): it proves
channel mechanics, NOT live SEBI retrieval.
"""

from __future__ import annotations

import copy
import io
import json

import pytest
from fastapi.testclient import TestClient

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.issue_terms import (
    HttpProspectusProvider,
    IssueTermsResolver,
    build_resolver_from_env,
)
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService

SEBI_URL = "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"
VISHAL_RHP_PDF = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"

PROSPECTUS_TEXT = """Prospectus
Dated: October 05, 2026
100% Book Built Offer
VISHAL NIRMITI LIMITED
CORPORATE IDENTITY NUMBER: U01122MH1994PLC185445
LISTING
The Equity Shares issued through the Red Herring Prospectus and this Prospectus are proposed to be
listed on the National Stock Exchange of India Limited and BSE Limited.
"Price Band" Price band of a minimum price of Rs 208 per Equity Share (i.e., the Floor Price) and the
maximum price of Rs 220 per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.
"""

RHP_TEXT = """Red Herring Prospectus
Dated: September 24, 2026
VISHAL NIRMITI LIMITED
CORPORATE IDENTITY NUMBER: U01122MH1994PLC185445
"Price Band" Price band of a minimum price of Rs [x] per Equity Share (i.e., the Floor Price).
"""


# ----------------------------------------------------------------------
# Configuration loading: failures are reported, never silent
# ----------------------------------------------------------------------


def test_malformed_prospectus_env_reports_configuration_problem(monkeypatch):
    monkeypatch.setenv("IPO_PROSPECTUS_URLS", "{not json")
    resolver = build_resolver_from_env()
    outcome = resolver.resolve(
        company_name="VISHAL NIRMITI LIMITED",
        ipo_id="VISHAL-NIRMITI-LIMITED",
        missing_fields=["price_band_low"],
    )
    assert outcome.status == "UNAVAILABLE"
    assert outcome.notice is None
    reports = [r for r in outcome.provider_reports if r.provider == "official-prospectus"]
    assert reports and "IPO_PROSPECTUS_URLS" in reports[0].detail
    # The configured (unparseable) value itself is never echoed back.
    assert "{not json" not in reports[0].detail


def test_non_object_prospectus_env_reports_configuration_problem(monkeypatch):
    monkeypatch.setenv("IPO_PROSPECTUS_URLS", '["https://www.sebi.gov.in/x.pdf"]')
    resolver = build_resolver_from_env()
    outcome = resolver.resolve(
        company_name="VISHAL NIRMITI LIMITED",
        ipo_id="VISHAL-NIRMITI-LIMITED",
        missing_fields=["price_band_low"],
    )
    assert any(
        "must be a JSON object" in r.detail for r in outcome.provider_reports
    )


def test_valid_prospectus_env_wires_provider(monkeypatch):
    monkeypatch.setenv(
        "IPO_PROSPECTUS_URLS", json.dumps({"VISHAL-NIRMITI-LIMITED": SEBI_URL})
    )
    resolver = build_resolver_from_env()
    providers = [p for p in resolver.providers if p.name == "official-prospectus"]
    assert len(providers) == 1
    assert providers[0].urls_by_ipo == {"VISHAL-NIRMITI-LIMITED": SEBI_URL}


# ----------------------------------------------------------------------
# Runtime IPO-ID / key matching (controlled transport)
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "key",
    ["VISHAL-NIRMITI-LIMITED", "Vishal Nirmiti Limited", "vishal nirmiti limited", "VISHAL_NIRMITI_LIMITED"],
)
def test_configured_url_matches_key_variants(key):
    provider = HttpProspectusProvider(
        {key: SEBI_URL}, fetcher=lambda u: PROSPECTUS_TEXT.encode()
    )
    candidate, report = provider.find("VISHAL NIRMITI LIMITED", "VISHAL-NIRMITI-LIMITED")
    assert candidate is not None and candidate.verified is True, report


def test_configured_url_never_borrowed_for_other_issuer():
    provider = HttpProspectusProvider(
        {"OTHER-ISSUER-LIMITED": SEBI_URL}, fetcher=lambda u: PROSPECTUS_TEXT.encode()
    )
    candidate, report = provider.find("VISHAL NIRMITI LIMITED", "VISHAL-NIRMITI-LIMITED")
    assert candidate is None and report.outcome == "UNAVAILABLE"


# ----------------------------------------------------------------------
# API-level diagnostic propagation (mocked extraction, controlled HTTP)
# ----------------------------------------------------------------------


def _client(tmp_path, monkeypatch, golden_input, providers):
    doc = copy.deepcopy(golden_input)
    for field_name in ("price_band_low", "price_band_high", "lot_size", "ofs"):
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
    return TestClient(
        create_app(service),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )


def _upload(client):
    return client.post(
        "/api/v1/ingest/document",
        files={"file": ("filing.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"mode": "final"},
    )


def test_retrieval_failure_propagates_provider_diagnostics(tmp_path, monkeypatch, golden_input):
    def boom(url):
        raise ConnectionError("simulated TLS failure")

    provider = HttpProspectusProvider({"VISHAL-NIRMITI-LIMITED": SEBI_URL}, fetcher=boom)
    res = _upload(_client(tmp_path, monkeypatch, golden_input, [provider]))
    assert res.status_code == 422, res.text
    body = res.json()
    assert body["code"] == "AWAITING_ISSUE_TERMS"
    assert set(body["missing_fields"]) == {"price_band_low", "price_band_high", "lot_size", "ofs"}
    reports = body["resolution"]["providers"]
    assert reports and reports[0]["provider"] == "official-prospectus"
    assert reports[0]["outcome"] == "UNAVAILABLE"
    assert "retrieval failed" in reports[0]["detail"]
    assert "simulated TLS failure" in reports[0]["detail"]


def test_rejected_document_is_distinguished_from_retrieval_failure(
    tmp_path, monkeypatch, golden_input
):
    provider = HttpProspectusProvider(
        {"VISHAL-NIRMITI-LIMITED": SEBI_URL}, fetcher=lambda u: RHP_TEXT.encode()
    )
    res = _upload(_client(tmp_path, monkeypatch, golden_input, [provider]))
    assert res.status_code == 422, res.text
    body = res.json()
    reports = body["resolution"]["providers"]
    assert reports and reports[0]["outcome"] == "REJECTED"
    # The operator-facing message must not claim retrieval failed.
    assert "retrieved but rejected" in body["message"]


def test_partial_prospectus_fails_closed_on_missing_term_only(
    tmp_path, monkeypatch, golden_input
):
    no_lot = PROSPECTUS_TEXT.replace(
        '"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.\n', ""
    )
    provider = HttpProspectusProvider(
        {"VISHAL-NIRMITI-LIMITED": SEBI_URL}, fetcher=lambda u: no_lot.encode()
    )
    res = _upload(_client(tmp_path, monkeypatch, golden_input, [provider]))
    assert res.status_code == 422, res.text
    body = res.json()
    # Fail-closed: nothing evaluated. The diagnostics layer distinguishes
    # what the official document verified from what it did not establish:
    # only lot_size is unverified; assembly requires it in final mode and
    # reports that explicitly instead of silently discarding the terms.
    assert body["resolution"]["status"] == "PARTIAL"
    assert body["resolution"]["resolved_fields"] == ["price_band_low", "price_band_high"]
    assert body["resolution"]["unresolved_fields"] == ["lot_size"]
    assert "lot_size" in body["resolution"]["assembly_error"]


# ----------------------------------------------------------------------
# The actual failing execution path: real filing PDF, unmocked
# extraction, runtime IPO-ID matching, controlled official transport.
# ----------------------------------------------------------------------


def test_real_filing_end_to_end_with_configured_prospectus(tmp_path):
    provider = HttpProspectusProvider(
        # Keyed by spaced company name -- the variant that previously
        # silently missed the runtime IPO-ID slug.
        {"Vishal Nirmiti Limited": SEBI_URL},
        fetcher=lambda u: PROSPECTUS_TEXT.encode(),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[provider]),
    )
    service = PresentationService(cfg)
    resp = service.ingest_document(
        file_bytes=VISHAL_RHP_PDF.read_bytes(), filename=VISHAL_RHP_PDF.name, mode="final"
    )
    assert resp.ipo_id == "VISHAL-NIRMITI-LIMITED"
    record = service.eval_store.read(resp.evaluation_id)
    issue = record["input_snapshot"]["input"]["issue"]
    assert (issue["price_band_low"], issue["price_band_high"], issue["lot_size"]) == (208.0, 220.0, 68)
    assert issue["ofs"] == 3300.0  # derived: 15,00,000 seller shares x Rs 220 cap
    assert issue["fresh_shares"] == 6590909  # fresh quantity, never the OFS quantity
    assert issue["fresh_shares"] != 1500000
    assert resp.issue_terms["status"] == "RESOLVED"
    assert resp.issue_terms["document_class"] == "OFFICIAL_PROSPECTUS"
