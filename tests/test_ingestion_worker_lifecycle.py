"""Offline worker-boundary tests; no production ingestion records are modified."""
import threading
import time
from types import SimpleNamespace

import pytest
from conftest import REPO_ROOT
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.service import PresentationConfig, PresentationService


def service(tmp_path):
    return PresentationService(PresentationConfig(store_root=tmp_path / 'evaluations',
        config_dir=REPO_ROOT / 'config', issue_terms_resolver=IssueTermsResolver([])))


def terminal(svc, rec):
    until = time.monotonic() + 2
    while time.monotonic() < until:
        saved = svc.get_ingestion_activity(rec.ingestion_id)
        if saved['status'] != 'RUNNING':
            return saved
        time.sleep(.01)
    return svc.get_ingestion_activity(rec.ingestion_id)


@pytest.mark.parametrize('exc', [RuntimeError('synthetic boundary failure'), SystemExit('synthetic exit')])
def test_exception_outside_inner_terminal_handler_is_durable(tmp_path, monkeypatch, exc):
    svc = service(tmp_path)
    def fail(**kw):
        kw['recorder'].emit('upload', 'received', 'SUCCEEDED', 'Received')
        raise exc
    monkeypatch.setattr(svc, 'ingest_document', fail)
    rec = svc.start_ingestion_async(b'%PDF-1.4 test')
    saved = terminal(svc, rec)
    assert saved['status'] == 'FAILED'
    assert saved['finished_at'] and saved['error_code'] == 'INGESTION_WORKER_FAILED'
    assert saved['evaluation_id'] is None and not saved['persisted']
    assert saved['events'][-1]['status'] == 'FAILED'
    assert saved == rec.snapshot()


def test_thread_dispatch_failure_has_durable_terminal_state(tmp_path, monkeypatch):
    svc = service(tmp_path)
    monkeypatch.setattr(threading.Thread, 'start', lambda self: (_ for _ in ()).throw(RuntimeError('cannot start')))
    rec = svc.start_ingestion_async(b'%PDF-1.4 test')
    saved = svc.get_ingestion_activity(rec.ingestion_id)
    assert saved['status'] == 'FAILED' and saved['error_code'] == 'INGESTION_DISPATCH_FAILED'
    assert saved['finished_at'] and not saved['persisted']


def test_return_without_terminal_state_is_not_silently_running(tmp_path, monkeypatch):
    svc = service(tmp_path)
    monkeypatch.setattr(svc, 'ingest_document', lambda **kw: None)
    rec = svc.start_ingestion_async(b'%PDF-1.4 test')
    saved = terminal(svc, rec)
    assert saved['status'] == 'FAILED' and saved['error_code'] == 'INGESTION_WORKER_INCOMPLETE'


def test_real_validation_failure_preserves_specific_error(tmp_path):
    svc = service(tmp_path)
    rec = svc.start_ingestion_async(b'not a pdf')
    saved = terminal(svc, rec)
    assert saved['status'] == 'FAILED' and saved['error_code'] == 'VALIDATION_ERROR'
    assert len([e for e in saved['events'] if e['stage'] == 'finalization']) == 1


def test_success_requires_inner_persistence_and_keeps_result(tmp_path, monkeypatch):
    svc = service(tmp_path)
    def done(**kw):
        rec = kw['recorder']
        rec.record.update(evaluation_id='EV-SYNTHETIC', persisted=True, evaluation_run=True)
        rec.finish('SUCCEEDED')
    monkeypatch.setattr(svc, 'ingest_document', done)
    rec = svc.start_ingestion_async(b'%PDF-1.4 test')
    saved = terminal(svc, rec)
    assert saved['status'] == 'SUCCEEDED' and saved['evaluation_id'] == 'EV-SYNTHETIC'
    assert len([e for e in saved['events'] if e['stage'] == 'finalization']) == 1


def test_genuine_evaluation_success_and_api_history(tmp_path, monkeypatch, golden_input):
    import copy
    from ipo_screening.extraction import DocumentExtractor
    from ipo_screening.presentation.api import create_app
    from fastapi.testclient import TestClient
    svc = service(tmp_path)
    monkeypatch.setattr(DocumentExtractor, 'extract_from_pdf', lambda *a, **k: (copy.deepcopy(golden_input), {}))
    rec = svc.start_ingestion_async(b'%PDF-1.4 synthetic valid input')
    saved = terminal(svc, rec)
    assert saved['status'] == 'SUCCEEDED' and saved['persisted']
    assert svc.eval_store.read(saved['evaluation_id'])
    assert any(e['stage'] == 'document_validation' for e in saved['events'])
    assert any(e['stage'] == 'persistence' for e in saved['events'])
    client = TestClient(create_app(svc), base_url='http://127.0.0.1:8000')
    assert client.get('/api/v1/ingestions/' + rec.ingestion_id).json() == saved
    response = client.get('/api/v1/ingestions/' + rec.ingestion_id + '/events').json()
    assert response['events'] == saved['events']


def test_blocked_terminal_state_not_overwritten_by_worker_guard(tmp_path, monkeypatch):
    svc = service(tmp_path)
    def blocked(**kw):
        kw['recorder'].finish('BLOCKED', error_code='AWAITING_ISSUE_TERMS')
        raise RuntimeError('already recorded')
    monkeypatch.setattr(svc, 'ingest_document', blocked)
    rec = svc.start_ingestion_async(b'%PDF-1.4 test')
    saved = terminal(svc, rec)
    assert saved['status'] == 'BLOCKED' and saved['error_code'] == 'AWAITING_ISSUE_TERMS'


def test_transient_terminal_write_retries_same_snapshot(tmp_path, monkeypatch):
    svc = service(tmp_path)
    original = svc.activity_store.save
    failures = []
    def save(record):
        if record['status'] == 'FAILED' and not failures:
            failures.append(True)
            raise OSError('synthetic transient sharing violation')
        original(record)
    monkeypatch.setattr(svc.activity_store, 'save', save)
    monkeypatch.setattr(svc, 'ingest_document', lambda **kw: (_ for _ in ()).throw(RuntimeError('boundary')))
    rec = svc.start_ingestion_async(b'%PDF-1.4 test')
    saved = terminal(svc, rec)
    assert saved['status'] == 'FAILED' and failures
    assert len([e for e in saved['events'] if e['stage'] == 'finalization']) == 1


def test_unavailable_storage_is_logged_not_silently_swallowed(tmp_path, monkeypatch, caplog):
    svc = service(tmp_path)
    original_thread = threading.Thread
    threads = []
    def thread(*args, **kwargs):
        worker = original_thread(*args, **kwargs)
        threads.append(worker)
        return worker
    monkeypatch.setattr(threading, 'Thread', thread)
    original = svc.activity_store.save
    exited = threading.Event()
    def save(record):
        if record['status'] == 'FAILED':
            exited.set()
            raise OSError('synthetic unavailable storage')
        original(record)
    monkeypatch.setattr(svc.activity_store, 'save', save)
    monkeypatch.setattr(svc, 'ingest_document', lambda **kw: (_ for _ in ()).throw(RuntimeError('boundary')))
    rec = svc.start_ingestion_async(b'%PDF-1.4 test')
    assert exited.wait(2)
    threads[0].join(2)
    assert not threads[0].is_alive()
    # An unwritable filesystem cannot honestly be reported as durable success.
    assert rec.snapshot()['status'] == 'FAILED'
    assert 'terminal activity write failed' in caplog.text


def test_async_api_ack_does_not_lie_about_dispatch_failure(tmp_path, monkeypatch):
    import io
    from fastapi.testclient import TestClient
    from ipo_screening.presentation.api import create_app
    svc = service(tmp_path)
    rec = svc.activity_store.new_recorder(filename='test.pdf', mode='final')
    rec.finish('FAILED', error_code='INGESTION_DISPATCH_FAILED')
    monkeypatch.setattr(svc, 'start_ingestion_async', lambda **kw: rec)
    client = TestClient(create_app(svc), base_url='http://127.0.0.1:8000', headers={'Origin': 'http://127.0.0.1:8000'})
    response = client.post('/api/v1/ingestions/start', files={'file': ('test.pdf', io.BytesIO(b'%PDF-1.4'), 'application/pdf')})
    assert response.status_code == 202 and response.json()['status'] == 'FAILED'
    assert client.get('/api/v1/ingestions/' + rec.ingestion_id).json()['error_code'] == 'INGESTION_DISPATCH_FAILED'


def test_inner_terminal_memory_does_not_hide_failed_disk_write(tmp_path, monkeypatch):
    svc = service(tmp_path)
    original = svc.activity_store.save
    failed = []
    def save(record):
        if record['status'] == 'FAILED' and not failed:
            failed.append(True)
            raise OSError('synthetic terminal write failure')
        original(record)
    monkeypatch.setattr(svc.activity_store, 'save', save)
    rec = svc.start_ingestion_async(b'invalid pdf')
    saved = terminal(svc, rec)
    assert failed and rec.snapshot()['status'] == 'FAILED'
    assert saved['status'] == 'FAILED' and saved['error_code'] == 'VALIDATION_ERROR'
    assert saved == rec.snapshot()


def test_early_activity_write_failure_cannot_disappear_at_worker_boundary(tmp_path, monkeypatch):
    svc = service(tmp_path)
    original = svc.activity_store.save
    failures = []
    def save(record):
        if any(e['stage'] == 'document_validation' for e in record['events']) and len(failures) < 2:
            failures.append(True)
            raise OSError('synthetic activity write interruption')
        original(record)
    monkeypatch.setattr(svc.activity_store, 'save', save)
    rec = svc.start_ingestion_async(b'%PDF-1.4 test')
    saved = terminal(svc, rec)
    assert len(failures) == 2
    assert saved['status'] == 'FAILED' and saved['error_code'] == 'INGESTION_WORKER_FAILED'
    assert saved['finished_at'] and saved['evaluation_id'] is None and not saved['persisted']
