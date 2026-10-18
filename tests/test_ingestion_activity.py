"""Ingestion Activity & Diagnostics (observability) tests.

The activity trace must originate from the actual backend execution:
these tests drive the real service/API paths (with deterministic
extractor/resolver doubles at the established seams) and assert that
stage events, per-term states, provider diagnostics, terminal status
and durable history all reflect what actually happened -- including
the Jio regression scenario, where a BSE listing URL returns the BSE
homepage with HTTP 200.  Fixture-driven; not live-source acceptance.
"""

from __future__ import annotations

import copy
import io
import time

import pytest
from fastapi.testclient import TestClient

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.issue_terms import IssueTermsResolver, OfficialDiscoveryProvider
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.ingestion_activity import (
    IngestionActivityStore,
    sanitize_details,
)
from ipo_screening.presentation.service import (
    IngestionAwaitingIssueTermsError,
    PresentationConfig,
    PresentationService,
)

BSE_HOMEPAGE = (
    "<html><head><title>LIVE Stock/Share Market | Indian Stock/Share Market LIVE | "
    "BSE SENSEX | BSE (formerly Bombay Stock Exchange)</title></head>"
    "<body><nav>Public Issues | Markets</nav>"
    '<a href="https://www.bseindia.com/sensex/code/16">BSE SENSEX</a></body></html>'
)


def _service(tmp_path, canonical_doc, providers):
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=providers),
    )
    service = PresentationService(cfg)
    DocumentExtractor.extract_from_pdf_orig = DocumentExtractor.extract_from_pdf
    return service


def _patch_extractor(monkeypatch, canonical_doc):
    monkeypatch.setattr(
        DocumentExtractor,
        "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (
            copy.deepcopy(canonical_doc),
            {},
        ),
    )


def _client(service):
    return TestClient(
        create_app(service),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )


def _jio_doc(golden_input):
    doc = copy.deepcopy(golden_input)
    doc["company_name"] = "Jio Platforms Limited"
    doc["ipo_id"] = "JIO-PLATFORMS-LIMITED"
    for field in ("price_band_low", "price_band_high", "lot_size", "ofs"):
        doc["issue"][field] = None
    return doc


def _homepage_provider():
    fetcher = lambda url: BSE_HOMEPAGE.encode()  # noqa: E731
    return OfficialDiscoveryProvider(fetcher=fetcher)


# ----------------------------------------------------------------------
# Event contract / store units
# ----------------------------------------------------------------------
def test_recorder_orders_events_and_persists_terminal(tmp_path):
    store = IngestionActivityStore(tmp_path / "activity")
    rec = store.new_recorder(filename="filing.pdf", mode="final")
    rec.emit("filing_extraction", "started", "RUNNING", "Extracting.")
    rec.emit("filing_extraction", "completed", "SUCCEEDED", "Done.")
    rec.finish("SUCCEEDED")
    saved = store.get(rec.ingestion_id)
    assert saved is not None and saved["status"] == "SUCCEEDED"
    seqs = [e["sequence"] for e in saved["events"]]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    assert all(e["ingestion_id"] == rec.ingestion_id for e in saved["events"])
    assert saved["events"][-1]["stage"] == "finalization"
    assert store.get("ing-does-not-exist") is None


def test_sanitize_details_redacts_and_bounds():
    cleaned = sanitize_details(
        {"Cookie": "BSESESSION=abc", "note": "x" * 5000, "nested": {"Authorization": "Bearer t"}}
    )
    assert cleaned["Cookie"] == "[redacted]"
    assert cleaned["nested"]["Authorization"] == "[redacted]"
    assert len(cleaned["note"]) <= 601


def test_store_retention_is_bounded(tmp_path):
    store = IngestionActivityStore(tmp_path / "activity", max_records=3)
    ids = []
    for i in range(5):
        rec = store.new_recorder(filename=f"f{i}.pdf", mode="final")
        rec.finish("FAILED", error_code="X")
        ids.append(rec.ingestion_id)
        time.sleep(0.01)
    remaining = store.list_recent(50)
    assert len(remaining) <= 3
    assert store.get(ids[-1]) is not None


# ----------------------------------------------------------------------
# Service-level: the Jio homepage regression scenario
# ----------------------------------------------------------------------
def test_jio_homepage_failure_leaves_durable_blocked_trace(tmp_path, monkeypatch, golden_input):
    service = _service(tmp_path, None, [_homepage_provider()])
    _patch_extractor(monkeypatch, _jio_doc(golden_input))
    with pytest.raises(IngestionAwaitingIssueTermsError) as excinfo:
        service.ingest_document(file_bytes=b"%PDF-1.4 test", filename="U72900GJ2019PLC110816_JIO.pdf", mode="final")
    ingestion_id = excinfo.value.ingestion_id
    record = service.get_ingestion_activity(ingestion_id)
    assert record is not None, "failed ingestion must have a durable trace"
    assert record["status"] == "BLOCKED"
    assert record["evaluation_run"] is False and record["persisted"] is False
    assert "issue.ofs" in record["missing_fields"]
    stages = [(e["stage"], e["status"]) for e in record["events"]]
    assert ("official_discovery", "RUNNING") in [(s, st) for s, st in stages]
    discovery_notes = " ".join(
        e["message"] for e in record["events"] if e["stage"] == "official_discovery"
    )
    assert "homepage" in discovery_notes  # precise reason, not a generic error
    assert ("evaluation", "SKIPPED") in stages
    assert ("persistence", "SKIPPED") in stages
    # no evaluation artifact was created for the blocked ingestion
    assert service.list_ingestion_activities(5)[0]["ingestion_id"] == ingestion_id
    assert not (tmp_path / "evaluations").exists() or not any(
        (tmp_path / "evaluations").iterdir()
    )


def test_successful_ingestion_trace_matches_execution(tmp_path, monkeypatch, golden_input):
    service = _service(tmp_path, None, [])
    _patch_extractor(monkeypatch, copy.deepcopy(golden_input))
    result = service.ingest_document(file_bytes=b"%PDF-1.4 test", filename="vishal.pdf", mode="final")
    assert result.ingestion_id
    record = service.get_ingestion_activity(result.ingestion_id)
    assert record["status"] == "SUCCEEDED"
    assert record["evaluation_run"] is True and record["persisted"] is True
    assert record["result"]["evaluation_id"] == result.evaluation_id
    stages = [e["stage"] for e in record["events"]]
    for expected in ("upload", "document_validation", "filing_extraction", "evaluation", "persistence", "finalization"):
        assert expected in stages


# ----------------------------------------------------------------------
# API: correlation, history retrieval, async live trace
# ----------------------------------------------------------------------
def test_api_error_correlates_to_recoverable_history(tmp_path, monkeypatch, golden_input):
    service = _service(tmp_path, None, [_homepage_provider()])
    _patch_extractor(monkeypatch, _jio_doc(golden_input))
    client = _client(service)
    resp = client.post(
        "/api/v1/ingest/document",
        files={"file": ("U72900GJ2019PLC110816_JIO.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"mode": "final"},
    )
    assert resp.status_code == 422
    detail = resp.json()  # custom handler flattens the detail envelope
    assert detail["code"] == "AWAITING_ISSUE_TERMS"
    ingestion_id = detail["ingestion_id"]
    assert detail["activity_url"] == f"/api/v1/ingestions/{ingestion_id}"

    hist = client.get(f"/api/v1/ingestions/{ingestion_id}")
    assert hist.status_code == 200 and hist.json()["status"] == "BLOCKED"
    events = client.get(f"/api/v1/ingestions/{ingestion_id}/events").json()
    assert events["evaluation_run"] is False and events["persisted"] is False
    assert any("homepage" in e["message"] for e in events["events"])
    tail = client.get(
        f"/api/v1/ingestions/{ingestion_id}/events",
        params={"after_sequence": events["events"][-1]["sequence"]},
    ).json()
    assert tail["events"] == []

    missing = client.get("/api/v1/ingestions/ing-unknown")
    assert missing.status_code == 404
    assert missing.json()["code"] == "INGESTION_NOT_FOUND"


@pytest.mark.slow
def test_async_start_streams_live_trace_to_terminal(tmp_path, monkeypatch, golden_input):
    service = _service(tmp_path, None, [_homepage_provider()])
    _patch_extractor(monkeypatch, _jio_doc(golden_input))
    client = _client(service)
    start = client.post(
        "/api/v1/ingestions/start",
        files={"file": ("U72900GJ2019PLC110816_JIO.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"mode": "final"},
    )
    assert start.status_code == 202
    ingestion_id = start.json()["ingestion_id"]
    deadline = time.time() + 60
    record = None
    while time.time() < deadline:
        record = client.get(f"/api/v1/ingestions/{ingestion_id}").json()
        if record["status"] != "RUNNING":
            break
        time.sleep(0.2)
    assert record is not None and record["status"] == "BLOCKED"
    assert record["evaluation_run"] is False and record["persisted"] is False
    assert any("homepage" in e["message"] for e in record["events"])


# ----------------------------------------------------------------------
# Windows trace ing-eacd8815051f4222 consistency: BSE listings returned
# JavaScript shells (never searched) and SEBI failed, yet the outcome
# was reported UNPUBLISHED.  Shells must surface as UNAVAILABLE at every
# layer -- provider, resolver, activity events -- while the ingestion
# itself stays BLOCKED with no evaluation and no persistence.
# ----------------------------------------------------------------------
BSE_JS_SHELL = (
    "<html><head><title>Public Issues</title></head>"
    "<body><app-root></app-root><script src='main.js'></script></body></html>"
)


def test_shell_listings_surface_unavailable_in_activity_trace(tmp_path, monkeypatch, golden_input):
    fetcher = lambda url: BSE_JS_SHELL.encode()  # noqa: E731
    service = _service(tmp_path, None, [OfficialDiscoveryProvider(fetcher=fetcher)])
    _patch_extractor(monkeypatch, _jio_doc(golden_input))
    with pytest.raises(IngestionAwaitingIssueTermsError) as excinfo:
        service.ingest_document(
            file_bytes=b"%PDF-1.4 test",
            filename="U72900GJ2019PLC110816_JIO.pdf",
            mode="final",
        )
    # Resolver layer: UNAVAILABLE, not UNPUBLISHED.
    assert excinfo.value.resolution["status"] == "UNAVAILABLE"
    record = service.get_ingestion_activity(excinfo.value.ingestion_id)
    assert record is not None and record["status"] == "BLOCKED"
    assert record["evaluation_run"] is False and record["persisted"] is False
    messages = [e["message"] for e in record["events"]]
    assert any("Official discovery outcome: UNAVAILABLE" in m for m in messages)
    assert any("shell" in m for m in messages)
    assert not any("UNPUBLISHED" in m for m in messages)
    stages = [(e["stage"], e["status"]) for e in record["events"]]
    assert ("evaluation", "SKIPPED") in stages
    assert not (tmp_path / "evaluations").exists() or not any(
        (tmp_path / "evaluations").iterdir()
    )
