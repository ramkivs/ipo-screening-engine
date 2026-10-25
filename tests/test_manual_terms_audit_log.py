"""Audit-log recording for manual issue-term submissions (2026-10-19).

Defect (user-reported at ``a7f823d``): manual issue-term inputs are
submitted and processed, but the audit log records nothing.  The
authoritative ingestion audit log is the Ingestion Activity store
(``presentation/ingestion_activity.py``: one durable JSON trace per
ingestion attempt, event contract v1, retrieved through
``GET /api/v1/ingestions``, ``/ingestions/{id}`` and
``/ingestions/{id}/events`` and presented in the Ingestion Activity
panel).  Tracing proved the failing layers were: (1) the manual-terms
API error responses dropped the ``ingestion_id``/``activity_url``
correlation the established contract requires
(``test_api_error_correlates_to_recoverable_history``), so rejected
submissions left records the caller could never find; (2) the trace had
no submission-receipt event (what was submitted, before validation) and
no conflict event; (3) the accepted event omitted the values it
recorded; and (4) the UI never registered or displayed the manual
submission's trace at all.

These tests reproduce the original defect (correlation + content gaps)
and prove the correction, end to end: submission -> event creation ->
persistence -> retrieval through the audit-log API.
"""

from __future__ import annotations

import copy
import io

import pytest
from fastapi.testclient import TestClient

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.ingestion_activity import IngestionActivityStore
from ipo_screening.presentation.service import (
    PresentationConfig,
    PresentationService,
)

PDF_BYTES = b"%PDF-1.4 manual-terms-audit-log"
EXPLANATION = "Terms read from the broker platform IPO page on 2026-10-19."
FOUR = ("price_band_low", "price_band_high", "lot_size", "ofs")


def _service(tmp_path, monkeypatch, doc_factory):
    monkeypatch.setattr(
        DocumentExtractor,
        "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (doc_factory(), {}),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    client = TestClient(
        create_app(service),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )
    return client, service


def _missing_doc(golden_input, *, drop=FOUR):
    doc = copy.deepcopy(golden_input)
    for field in drop:
        doc["issue"][field] = None
    return doc


def _upload(client, path="/api/v1/ingest/manual-terms", **data):
    payload = {"mode": "final"}
    payload.update(data)
    return client.post(
        path,
        files={"file": ("filing.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
        data=payload,
    )


def _events(record):
    return [(e["stage"], e["event_type"], e["status"]) for e in record["events"]]


def _events_by_type(record, event_type):
    return [e for e in record["events"] if e["event_type"] == event_type]


# ---------------------------------------------------------------------------
# 1 + 2 + 3 + 5. Successful four-field submission: creation, persistence,
# retrieval through the audit-log API, IPO/evaluation association, and the
# distinction between evaluation success and audit-record existence.
# ---------------------------------------------------------------------------

def test_successful_manual_submission_creates_retrievable_audit_record(
    tmp_path, monkeypatch, golden_input
):
    client, service = _service(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))

    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    ingestion_id = body.get("ingestion_id")
    assert ingestion_id, "successful manual submission must return its audit id"
    assert body.get("correlation_id") == ingestion_id

    # The record survives the persistence boundary and is retrievable
    # through the supported audit-log API (record, events, list).
    hist = client.get(f"/api/v1/ingestions/{ingestion_id}")
    assert hist.status_code == 200
    record = hist.json()
    assert record["status"] == "SUCCEEDED"
    assert record["evaluation_run"] is True and record["persisted"] is True
    # Evaluation outcome is recorded and linked, not confused with the
    # mere existence of the audit record.
    assert record["result"]["evaluation_id"] == body["evaluation_id"]
    assert record["result"]["ipo_id"] == body["ipo_id"]

    events = client.get(f"/api/v1/ingestions/{ingestion_id}/events").json()
    assert events["evaluation_run"] is True and events["persisted"] is True
    stages = [(e["stage"], e["event_type"], e["status"]) for e in events["events"]]
    # Submission receipt, acceptance, evaluation and persistence are
    # distinct auditable steps.
    assert ("term_resolution", "manual_submission", "SUCCEEDED") in stages
    assert ("term_resolution", "manual_entry", "SUCCEEDED") in stages
    assert ("evaluation", "completed", "SUCCEEDED") in stages
    assert ("persistence", "completed", "SUCCEEDED") in stages
    assert ("finalization", "completed", "SUCCEEDED") in stages

    # The receipt records exactly what was submitted.
    receipt = _events_by_type(record, "manual_submission")[0]
    assert set(receipt["details"]["fields"]) == set(FOUR)
    assert receipt["details"]["values"]["ofs"] == 3300.0
    assert receipt["details"]["explanation_supplied"] is True

    # The accepted event carries the applied values and the operator
    # explanation (or a durable reference) plus provenance.
    accepted = _events_by_type(record, "manual_entry")[0]
    assert accepted["details"]["values"]["price_band_low"] == 208.0
    assert accepted["details"]["values"]["ofs"] == 3300.0
    assert accepted["details"]["explanation"] == EXPLANATION
    assert accepted["details"]["provenance"] == "MANUAL_ENTRY"
    assert accepted["details"]["verified"] is False
    assert accepted["details"]["conflicts_confirmed"] is False

    # Listing retrieval: the record is in the audit log listing too.
    listing = client.get("/api/v1/ingestions").json()["items"]
    assert any(item["ingestion_id"] == ingestion_id for item in listing)
    # Incremental event retrieval works (the established polling path).
    tail = client.get(
        f"/api/v1/ingestions/{ingestion_id}/events",
        params={"after_sequence": events["events"][-1]["sequence"]},
    ).json()
    assert tail["events"] == []


def test_audit_record_is_associated_with_the_correct_ipo_and_evaluation(
    tmp_path, monkeypatch, golden_input
):
    client, service = _service(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    record = service.get_ingestion_activity(body["ingestion_id"])

    assert record["result"]["ipo_id"] == golden_input["ipo_id"]
    assert record["result"]["evaluation_id"] == body["evaluation_id"]
    accepted = _events_by_type(record, "manual_entry")[0]
    assert accepted["details"]["ipo_id"] == golden_input["ipo_id"]
    # The evaluation itself is the durable evidence containing the
    # values; the audit trail links to it by id.
    assert service.eval_store.exists(body["evaluation_id"])


# ---------------------------------------------------------------------------
# 4. Provenance stays MANUAL_ENTRY/UNVERIFIED - never upgraded.
# ---------------------------------------------------------------------------

def test_manual_provenance_is_never_upgraded_in_the_recorded_evidence(
    tmp_path, monkeypatch, golden_input
):
    client, service = _service(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert res.status_code == 201
    body = res.json()
    record = service.get_ingestion_activity(body["ingestion_id"])
    accepted = _events_by_type(record, "manual_entry")[0]
    assert accepted["details"]["provenance"] == "MANUAL_ENTRY"
    assert accepted["details"]["verified"] is False

    evaluation = service.eval_store.read(body["evaluation_id"])
    manual_fields = set()
    for item in evaluation["evidence"]["evidence"]:
        if item.get("extraction_method") == "MANUAL_ENTRY":
            assert item["source_id"] == "SRC-MANUAL-ENTRY"
            assert EXPLANATION in (item.get("note") or "")
            manual_fields.add(item.get("evidence_id"))
    # All four values were applied and scored exactly as submitted.
    for field in FOUR:
        assert evaluation["input_snapshot"]["input"]["issue"][field] is not None
    assert {f"EV-issue.{f}" for f in FOUR} <= manual_fields
    # No official source id was claimed for any manually entered field.
    assert not any(
        s.get("source_id", "").startswith(("SRC-PBN-", "SRC-PROSPECTUS-"))
        for s in evaluation["evidence"]["sources"]
    )


# ---------------------------------------------------------------------------
# 6. Rejected submissions record the rejection, never a success.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "terms, needle",
    [
        (dict(price_band_low="208", price_band_high="220", lot_size="68", ofs="-5"), "issue.ofs"),
        (dict(price_band_low="230", price_band_high="220", lot_size="68", ofs="3300"), "price_band_low"),
        (dict(price_band_low="208", price_band_high="220", lot_size="68.5", ofs="3300"), "issue.lot_size"),
    ],
)
def test_rejected_submission_is_recorded_as_rejection_not_success(
    tmp_path, monkeypatch, golden_input, terms, needle
):
    client, service = _service(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(client, explanation=EXPLANATION, **terms)
    assert res.status_code == 400
    detail = res.json()
    assert detail["code"] == "VALIDATION_ERROR"
    # The defect: rejected submissions previously returned no correlation
    # id, so their audit records were unreachable from the flow.
    ingestion_id = detail.get("ingestion_id")
    assert ingestion_id, "rejected submission must correlate to its audit record"
    assert detail.get("activity_url") == f"/api/v1/ingestions/{ingestion_id}"

    record = service.get_ingestion_activity(ingestion_id)
    assert record["status"] == "FAILED"
    assert record["error_code"] == "VALIDATION_ERROR"
    assert record["evaluation_run"] is False and record["persisted"] is False
    stages = _events(record)
    # The submission itself is recorded (what was submitted) ...
    assert ("term_resolution", "manual_submission", "SUCCEEDED") in stages
    # ... and its rejection is recorded as a rejection.
    rejection = _events_by_type(record, "manual_validation")
    assert rejection and rejection[0]["status"] == "FAILED"
    assert needle in rejection[0]["message"]
    # No acceptance, no evaluation, no persistence, no success outcome.
    assert not _events_by_type(record, "manual_entry")
    assert ("evaluation", "started", "RUNNING") not in stages
    assert ("finalization", "completed", "SUCCEEDED") not in stages
    assert service.eval_store.list_evaluations() == []


def test_missing_explanation_is_recorded_as_rejection(tmp_path, monkeypatch, golden_input):
    client, service = _service(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))
    res = _upload(
        client, price_band_low="208", price_band_high="220", lot_size="68", ofs="3300"
    )
    assert res.status_code == 400
    ingestion_id = res.json()["ingestion_id"]
    record = service.get_ingestion_activity(ingestion_id)
    assert record["status"] == "FAILED"
    rejection = _events_by_type(record, "manual_validation")[0]
    assert "explanation" in rejection["message"].lower()
    assert rejection["details"]["values"]["ofs"] == 3300.0
    assert service.eval_store.list_evaluations() == []


# ---------------------------------------------------------------------------
# 7. Conflict handling and explicit confirmation preserve semantics, and
#    both outcomes are auditable.
# ---------------------------------------------------------------------------

def test_conflict_and_confirmation_are_audited_with_existing_semantics(
    tmp_path, monkeypatch, golden_input
):
    client, service = _service(tmp_path, monkeypatch, lambda: copy.deepcopy(golden_input))
    conflict = _upload(client, ofs="2500", explanation=EXPLANATION)
    assert conflict.status_code == 409
    detail = conflict.json()
    assert detail["code"] == "ISSUE_TERM_CONFLICT"
    ingestion_id = detail.get("ingestion_id")
    assert ingestion_id, "conflict response must correlate to its audit record"

    record = service.get_ingestion_activity(ingestion_id)
    assert record["status"] == "BLOCKED"
    assert record["error_code"] == "ISSUE_TERM_CONFLICT"
    conflict_events = _events_by_type(record, "conflict")
    assert conflict_events and conflict_events[0]["status"] == "BLOCKED"
    details = conflict_events[0]["details"]
    assert details["confirmation_required"] is True
    assert details["fields"] == ["issue.ofs"]
    observed = details["conflicts"][0]
    assert observed["manual_value"] == 2500.0
    assert observed["existing_value"] == 3300.0
    # Nothing was applied or evaluated by the blocked submission.
    assert not _events_by_type(record, "manual_entry")
    assert record["evaluation_run"] is False and record["persisted"] is False

    # Explicit confirmation keeps the existing semantics and is audited.
    resolved = _upload(
        client, ofs="2500", explanation=EXPLANATION, confirm_conflicts="true"
    )
    assert resolved.status_code == 201, resolved.text
    body = resolved.json()
    rec2 = service.get_ingestion_activity(body["ingestion_id"])
    assert rec2["status"] == "SUCCEEDED"
    accepted = _events_by_type(rec2, "manual_entry")[0]
    assert accepted["details"]["conflicts_confirmed"] is True
    assert accepted["details"]["values"]["ofs"] == 2500.0
    evaluation = service.eval_store.read(body["evaluation_id"])
    # Confirmation applied the manual value without upgrading provenance.
    assert evaluation["input_snapshot"]["input"]["issue"]["ofs"] == 2500.0
    assert service.eval_store.list_evaluations() != []


# ---------------------------------------------------------------------------
# 8. An evaluation/persistence failure never produces a false success.
# ---------------------------------------------------------------------------

def test_evaluation_failure_is_recorded_without_false_success(
    tmp_path, monkeypatch, golden_input
):
    import ipo_screening.presentation.service as service_module

    client, service = _service(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))

    def _boom(*args, **kwargs):
        raise RuntimeError("evaluation engine failure (test)")

    monkeypatch.setattr(service_module, "evaluate", _boom)
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert res.status_code == 422
    detail = res.json()
    assert detail["code"] == "PROCESSING_FAILED"
    ingestion_id = detail.get("ingestion_id")
    assert ingestion_id, "processing failure must correlate to its audit record"

    record = service.get_ingestion_activity(ingestion_id)
    assert record["status"] == "FAILED"
    assert record["error_code"] == "PROCESSING_FAILED"
    assert record["evaluation_run"] is False and record["persisted"] is False
    assert record["result"] is None
    stages = _events(record)
    assert ("finalization", "completed", "SUCCEEDED") not in stages
    assert ("finalization", "terminated", "FAILED") in stages
    assert service.eval_store.list_evaluations() == []


# ---------------------------------------------------------------------------
# 9. Audit-recording failure is loud, never a silent success.
# ---------------------------------------------------------------------------

def test_audit_store_failure_is_never_reported_as_success(
    tmp_path, monkeypatch, golden_input
):
    client, service = _service(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))

    def _broken_save(self, record):
        raise OSError("audit store unavailable (test)")

    monkeypatch.setattr(IngestionActivityStore, "save", _broken_save)
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    # The operation fails loudly: an unauditable run is never presented
    # as an auditable success (the existing contract has no separate
    # audit-health channel; failure propagates).
    assert res.status_code in (422, 500), res.text
    assert res.status_code != 201
    assert service.eval_store.list_evaluations() == []


def test_audit_store_failure_at_finalization_still_reports_failure(
    tmp_path, monkeypatch, golden_input
):
    """If the audit store fails only when the terminal success event is
    written (after evaluation persistence), the API still does not
    present the operation as an auditable success.  The immutable
    evaluation artifact may exist -- atomicity between evaluation
    persistence and audit persistence is NOT part of the established
    contract -- but the response is a failure, never a silent success."""
    client, service = _service(tmp_path, monkeypatch, lambda: _missing_doc(golden_input))

    original_save = IngestionActivityStore.save

    def _fail_on_success(self, record):
        if record.get("status") == "SUCCEEDED":
            raise OSError("audit store unavailable at finalization (test)")
        return original_save(self, record)

    monkeypatch.setattr(IngestionActivityStore, "save", _fail_on_success)
    res = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert res.status_code != 201, res.text
    assert res.status_code in (422, 500)


# ---------------------------------------------------------------------------
# 10. Unrelated IPOs and existing audit events remain unaffected.
# ---------------------------------------------------------------------------

def test_manual_submission_leaves_other_ipo_records_unaffected(
    tmp_path, monkeypatch, golden_input
):
    other = copy.deepcopy(golden_input)
    other["ipo_id"] = "OTHER-ISSUER-LIMITED"
    other["company_name"] = "Other Issuer Limited"
    queue = [_missing_doc(golden_input), _missing_doc(other)]

    client, service = _service(tmp_path, monkeypatch, lambda: queue.pop(0))

    done = _upload(
        client,
        price_band_low="208",
        price_band_high="220",
        lot_size="68",
        ofs="3300",
        explanation=EXPLANATION,
    )
    assert done.status_code == 201
    id_a = done.json()["ingestion_id"]

    awaiting = _upload(client, "/api/v1/ingest/document")
    assert awaiting.status_code == 422
    id_b = awaiting.json()["ingestion_id"]
    assert id_a != id_b

    rec_a = service.get_ingestion_activity(id_a)
    rec_b = service.get_ingestion_activity(id_b)
    # Each record belongs to its own IPO; no cross-contamination.
    assert rec_a["result"]["ipo_id"] == "VISHAL-NIRMITI-LIMITED"
    assert rec_b["status"] == "BLOCKED" and rec_b["result"] is None
    # The second IPO's trace carries no manual-entry content at all.
    assert not _events_by_type(rec_b, "manual_submission")
    assert not _events_by_type(rec_b, "manual_entry")
    assert not _events_by_type(rec_b, "conflict")
    a_events = _events_by_type(rec_a, "manual_submission")
    assert a_events and a_events[0]["details"]["values"]["ofs"] == 3300.0
    # Both are retrievable independently from the audit log.
    listing = {item["ingestion_id"] for item in client.get("/api/v1/ingestions").json()["items"]}
    assert {id_a, id_b} <= listing
