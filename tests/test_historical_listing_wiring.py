"""Configuration → provider → ingestion wiring for closed-issue listings.

`tests/test_historical_issue_identity.py` proves the *rule*: a closed
exchange record may supply terms only when its identity is bound to the
offering.  This module proves the *wiring* — that the rule is reachable
from the application an operator actually runs:

    env configuration → build_resolver_from_env → OfficialDiscoveryProvider
      → PresentationService (constructed exactly as create_app does)
      → ingest_document → resolver receives the filing's own issue window

Two of the assertions are integration-level and deliberately so: they
construct the service the way ``create_app()`` does (no injected resolver)
and drive the real Paras RHP through ``ingest_document``.  Nothing here
creates an evaluation: the filing is unresolved in this environment, so
the ingestion must fail closed as ``AWAITING_ISSUE_TERMS`` and the
temporary store must stay empty.

The retrieval tests are **evidence-backed, not live**: the internet is
not reachable from this environment, so the fixture is built from the
retained BSE capture and is marked as such.
"""

from __future__ import annotations

import json
import os
import re

import pytest

from conftest import REPO_ROOT
from ipo_screening.issue_identity import IssueIdentity
from ipo_screening.issue_terms import (
    DISCOVERY_HOSTS,
    ConfigurationDiagnosticProvider,
    IssueTermsResolver,
    OfficialDiscoveryProvider,
    ResolutionOutcome,
    build_resolver_from_env,
)
from ipo_screening.official_issue_sources import (
    BSE_HISTORICAL_LISTING,
    BSE_LISTING,
    bse_historical_issue_records,
)

CAPTURE_DIR = REPO_ROOT / "evidence" / "non-authoritative" / "paras-healthcare-issue-terms-20261024"
LISTING_CAPTURE = CAPTURE_DIR / "source-captures" / "bse-historical-listing-chunk-0-prefix.md"
DETAIL_CAPTURE = CAPTURE_DIR / "source-captures" / "bse-displayipo-4895-chunk-0.md"
PARAS_RHP = (REPO_ROOT / "evidence" / "non-authoritative" / "paras-healthcare" /
             "U85110HR1987PLC035823 _ParasHealthcare.pdf")

ISSUER = "Paras Healthcare Limited"
HISTORICAL_URL = BSE_HISTORICAL_LISTING


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in ("IPO_OFFICIAL_HISTORICAL_LISTINGS", "IPO_PRICE_BAND_NOTICE_URLS",
                 "IPO_PROSPECTUS_URLS", "IPO_OFFICIAL_DISCOVERY", "IPO_ISSUE_TERMS_CACHE_DIR"):
        monkeypatch.delenv(name, raising=False)


def discovery_providers(resolver):
    return [p for p in resolver.providers if isinstance(p, OfficialDiscoveryProvider)]


# ----------------------------------------------------------------------
# 1. Configuration → provider construction
# ----------------------------------------------------------------------
def test_unset_variable_searches_no_closed_listing():
    resolver = build_resolver_from_env()
    assert discovery_providers(resolver)[0].historical_listing_urls == []


def test_configured_url_reaches_the_discovery_provider(monkeypatch):
    monkeypatch.setenv("IPO_OFFICIAL_HISTORICAL_LISTINGS", HISTORICAL_URL)
    provider = discovery_providers(build_resolver_from_env())[0]
    assert provider.historical_listing_urls == [HISTORICAL_URL]


def test_several_entries_and_blank_items_are_tolerated(monkeypatch):
    monkeypatch.setenv(
        "IPO_OFFICIAL_HISTORICAL_LISTINGS",
        f" {HISTORICAL_URL} ,, https://www.nseindia.com/market-data/all-upcoming-issues-ipo ")
    provider = discovery_providers(build_resolver_from_env())[0]
    assert provider.historical_listing_urls == [
        HISTORICAL_URL, "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"]


@pytest.mark.parametrize("value, reason", [
    ("http://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P", "not an HTTPS URL"),
    ("https://example.com/historical-issues", "not an allowed official source host"),
    ("https://127.0.0.1/archive", "not an allowed official source host"),
])
def test_an_unusable_entry_is_reported_as_configuration_not_as_absence(value, reason, monkeypatch):
    monkeypatch.setenv("IPO_OFFICIAL_HISTORICAL_LISTINGS", value)
    resolver = build_resolver_from_env()
    assert discovery_providers(resolver)[0].historical_listing_urls == []
    diagnostics = [p for p in resolver.providers if isinstance(p, ConfigurationDiagnosticProvider)]
    assert len(diagnostics) == 1
    assert reason in diagnostics[0].detail
    assert value not in diagnostics[0].detail  # the value is never echoed back
    # A broken archive entry must not disable discovery itself.
    assert discovery_providers(resolver)


def test_a_disabled_discovery_path_ignores_the_variable(monkeypatch):
    monkeypatch.setenv("IPO_OFFICIAL_DISCOVERY", "0")
    monkeypatch.setenv("IPO_OFFICIAL_HISTORICAL_LISTINGS", HISTORICAL_URL)
    assert discovery_providers(build_resolver_from_env()) == []


def test_every_named_host_is_one_the_discovery_path_may_already_read():
    """The variable cannot introduce a host the discovery path could not use."""
    assert "www.bseindia.com" in DISCOVERY_HOSTS
    assert "www.nseindia.com" in DISCOVERY_HOSTS
    assert "example.com" not in DISCOVERY_HOSTS


# ----------------------------------------------------------------------
# 2. Provider → service construction (the shape create_app uses)
# ----------------------------------------------------------------------
def test_the_application_service_builds_the_configured_resolver(monkeypatch, tmp_path):
    from ipo_screening.presentation.service import PresentationConfig, PresentationService

    monkeypatch.setenv("IPO_OFFICIAL_HISTORICAL_LISTINGS", HISTORICAL_URL)
    # No resolver injected: exactly what create_app() does.
    service = PresentationService(PresentationConfig(store_root=tmp_path / "evaluations",
                                                     config_dir=REPO_ROOT / "config"))
    resolver = service.config.issue_terms_resolver
    assert discovery_providers(resolver)[0].historical_listing_urls == [HISTORICAL_URL]


# ----------------------------------------------------------------------
# 3. Ingestion → resolver: the filing's own issue window is delivered
# ----------------------------------------------------------------------
class RecordingResolver(IssueTermsResolver):
    """Real resolver subject, recording the context the service passes it."""

    def __init__(self, providers=()):
        super().__init__(providers=list(providers))
        self.calls = []

    def resolve(self, *, company_name, ipo_id, missing_fields, issue_context=None):
        self.calls.append({"company_name": company_name, "ipo_id": ipo_id,
                           "missing_fields": list(missing_fields),
                           "issue_context": dict(issue_context or {})})
        return super().resolve(company_name=company_name, ipo_id=ipo_id,
                               missing_fields=missing_fields, issue_context=issue_context)


@pytest.mark.slow
def test_ingestion_delivers_the_filings_own_issue_window_to_the_resolver(tmp_path):
    """The identity rule is only usable if the window actually arrives.

    This runs the real retained RHP through the real ingestion path.  The
    transport is synthetic (a fetcher that refuses every URL), so the run
    is an integration check of wiring, not of retrieval.
    """
    from ipo_screening.presentation.service import PresentationConfig, PresentationService

    def offline(url, *_args, **_kwargs):
        raise OSError("[Errno 101] Network is unreachable (offline test transport)")

    resolver = RecordingResolver([OfficialDiscoveryProvider(
        fetcher=offline, historical_listing_urls=[HISTORICAL_URL])])
    service = PresentationService(PresentationConfig(
        store_root=tmp_path / "evaluations", config_dir=REPO_ROOT / "config",
        issue_terms_resolver=resolver))

    with pytest.raises(Exception) as excinfo:
        service.ingest_document(file_bytes=PARAS_RHP.read_bytes(),
                                filename=PARAS_RHP.name, mode="final")
    assert "AWAITING_ISSUE_TERMS" in str(excinfo.value)

    assert len(resolver.calls) == 1
    call = resolver.calls[0]
    assert call["company_name"] == "PARAS HEALTHCARE LIMITED"
    assert call["missing_fields"] == ["price_band_low", "price_band_high", "lot_size"]
    # These are the values the closed-record binding depends on; the filing
    # supplies them, so the archive row can be matched without a guess.
    assert call["issue_context"]["open_date"] == "2026-10-21"
    assert call["issue_context"]["close_date"] == "2026-10-23"
    assert IssueIdentity.from_issue_context(call["issue_context"]).binds_window is True

    # Fail-closed: the transport was unreachable, so nothing was resolved and
    # no evaluation (or evaluation store) was produced.
    assert not (tmp_path / "evaluations").exists() or not any(
        (tmp_path / "evaluations").rglob("*"))


# ----------------------------------------------------------------------
# 4. Evidence-backed retrieval (NOT live): the retained capture drives the path
# ----------------------------------------------------------------------
def detail_url_from_capture() -> str:
    """The issue-page link on the retained Paras row (never the site chrome)."""
    text = LISTING_CAPTURE.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines()
               if "Paras Healthcare Limited" in line and "DisplayIPO" in line)
    return re.search(r"\]\((https://[^)]+)\)", row).group(1)


def capture_rows_as_html() -> bytes:
    """The retained BSE historical-listing row, in the served HTML shape.

    Read from the committed capture, so the test cannot drift from the
    evidence: the issue link, issuer, window and offer price all come from
    the file, not from this module.
    """
    text = LISTING_CAPTURE.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines()
               if "Paras Healthcare Limited" in line and "DisplayIPO" in line)
    href = detail_url_from_capture()
    cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
    # cells: [name-link, platform, start, end, offer price, face value, type]
    assert len(cells) == 7, cells
    body = (f'<tr><td><a href="{href.replace("&", "&amp;")}">{ISSUER}</a></td>'
            + "".join(f"<td>{cell}</td>" for cell in cells[1:]) + "</tr>")
    return ("<html><body><table><tr><th>Security Name</th><th>Exchange Platform</th>"
            "<th>Start Date</th><th>End Date</th><th>Offer Price</th><th>Face Value</th>"
            f"<th>Type of Issue</th></tr>{body}</table></body></html>").encode()


def detail_page_from_capture() -> bytes:
    """The retained BSE issue page's labelled rows, in table shape."""
    text = DETAIL_CAPTURE.read_text(encoding="utf-8")
    pairs = re.findall(r"\|\s*\*\*([^|*]+?)\*\*\s*\|\s*([^|]+?)\s*\|", text)
    assert pairs, "capture carries no labelled rows"
    rows = "".join(f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in pairs)
    return f"<html><body><table><tr><td><b>{ISSUER}</b></td></tr>{rows}</table></body></html>".encode()


def test_the_retained_capture_still_states_the_terms_we_expect():
    listing = capture_rows_as_html().decode()
    assert "IPONo=8048" in listing and "660.00 - 693.00" in listing
    detail = detail_page_from_capture().decode()
    assert "660.00-693.00" in detail and "Market Lot" in detail


def test_the_retained_capture_binds_and_supplies_all_three_terms():
    """Evidence-backed: real captured content, synthetic transport."""
    detail_url = detail_url_from_capture()
    pages = {BSE_LISTING: b"<html><body><p>no issues</p></body></html>",
             HISTORICAL_URL: capture_rows_as_html(),
             detail_url: detail_page_from_capture()}

    def fetch(url, *_args, **_kwargs):
        if url not in pages:
            raise AssertionError(f"unexpected fetch: {url}")
        return pages[url]

    resolver = IssueTermsResolver([OfficialDiscoveryProvider(
        fetcher=fetch, listing_urls=[BSE_LISTING],
        historical_listing_urls=[HISTORICAL_URL])])
    outcome = resolver.resolve(
        company_name=ISSUER, ipo_id="PARAS-HEALTHCARE-LIMITED",
        missing_fields=["price_band_low", "price_band_high", "lot_size"],
        issue_context={"open_date": "2026-10-21", "close_date": "2026-10-23"})

    assert outcome.status == "RESOLVED"
    assert outcome.conflicts == []
    values = {f: outcome.field_diagnostics[f]["candidates"][0]["value"]
              for f in ("price_band_low", "price_band_high", "lot_size")}
    assert values == {"price_band_low": 660.0, "price_band_high": 693.0, "lot_size": 21.0}
    for field in ("price_band_low", "price_band_high", "lot_size"):
        evidence = outcome.field_diagnostics[field]["candidates"][0]
        assert evidence["issuer"] == ISSUER
        assert evidence["verification"] == "VERIFIED"
        assert evidence["content_hash"] and evidence["uri"]
        assert evidence["raw_text"] or evidence["quote"]
    # The band came from the listing row, the lot from the linked issue page.
    assert outcome.field_diagnostics["price_band_low"]["candidates"][0]["quote"] == "660.00 - 693.00"
    assert "Market Lot" in (outcome.field_diagnostics["lot_size"]["candidates"][0]["locator"] or "")


def test_the_same_capture_cannot_supply_another_issuer(monkeypatch):
    pages = {BSE_LISTING: b"<html><body><p>no issues</p></body></html>",
             HISTORICAL_URL: capture_rows_as_html()}

    def fetch(url, *_args, **_kwargs):
        return pages.get(url, b"<html><body><table></table></body></html>")

    resolver = IssueTermsResolver([OfficialDiscoveryProvider(
        fetcher=fetch, listing_urls=[BSE_LISTING],
        historical_listing_urls=[HISTORICAL_URL])])
    outcome = resolver.resolve(company_name="Another Hospitals Limited", ipo_id="OTHER",
                               missing_fields=["price_band_low", "price_band_high", "lot_size"],
                               issue_context={"open_date": "2026-10-21",
                                             "close_date": "2026-10-23"})
    assert outcome.resolved_fields == []


def test_a_prior_offering_in_the_same_archive_supplies_nothing():
    """The filing's window is the discriminator, so an earlier IPO of the
    same company cannot answer for this one."""
    prior = (capture_rows_as_html().decode()
             .replace("IPONo=8048", "IPONo=6900")
             .replace("startdt=21/10/2026", "startdt=01/08/2024")
             .replace("21-10-2026", "01-08-2024").replace("23-10-2026", "05-08-2024")
             .replace("660.00 - 693.00", "300.00 - 320.00"))
    records, rejections = bse_historical_issue_records(
        prior.encode(), ISSUER, IssueIdentity("2026-10-21", "2026-10-23"))
    assert records == []
    assert "STALE_OR_DIFFERENT_ISSUE" in rejections[0]
    assert "300.00 - 320.00" not in rejections[0]
