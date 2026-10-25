"""Durable visibility across activity readers/writers; no user data or live I/O.

The sharing denial injection models Windows CRT PermissionError(errno=13,
winerror=None), observed on the native Windows baseline CI runner.
"""
import json
import threading
from pathlib import Path

import pytest

from ipo_screening.presentation.ingestion_activity import IngestionActivityStore


def test_unreadable_existing_record_is_not_reported_missing(tmp_path, monkeypatch):
    store = IngestionActivityStore(tmp_path)
    rec = store.new_recorder(filename='test.pdf', mode='final')
    original = Path.read_text
    def denied(path, *args, **kw):
        if path == store._path(rec.ingestion_id):
            raise PermissionError(13, 'synthetic Windows CRT sharing denial')
        return original(path, *args, **kw)
    monkeypatch.setattr(Path, 'read_text', denied)
    with pytest.raises(PermissionError):
        store.get(rec.ingestion_id)


def test_corrupt_existing_record_is_not_reported_missing(tmp_path):
    store = IngestionActivityStore(tmp_path)
    rec = store.new_recorder(filename='test.pdf', mode='final')
    store._path(rec.ingestion_id).write_text('{not valid JSON', encoding='utf-8')
    with pytest.raises(json.JSONDecodeError):
        store.get(rec.ingestion_id)
    assert store.get('ing-truly-absent') is None


@pytest.mark.parametrize('reader', ['get', 'list_recent'])
def test_reader_cannot_open_destination_during_publication(tmp_path, monkeypatch, reader):
    store = IngestionActivityStore(tmp_path)
    rec = store.new_recorder(filename='test.pdf', mode='final')
    path = store._path(rec.ingestion_id)
    writing = threading.Event()
    publish = threading.Event()
    entered = threading.Event()
    done = threading.Event()
    failures = []
    result = []
    original_replace = Path.replace
    original_read = Path.read_text
    def replace(src, target):
        if Path(target) == path:
            writing.set()
            if not publish.wait(3):
                raise AssertionError('test publication barrier timed out')
        return original_replace(src, target)
    def read(src, *args, **kw):
        if src == path and writing.is_set() and not publish.is_set():
            raise PermissionError(13, 'modeled Windows destination handle denial')
        return original_read(src, *args, **kw)
    monkeypatch.setattr(Path, 'replace', replace)
    monkeypatch.setattr(Path, 'read_text', read)
    def writer():
        try:
            rec.finish('FAILED', error_code='SYNTHETIC_PROCESSING_FAILURE')
        except BaseException as exc:
            failures.append(exc)
    def poller():
        entered.set()
        try:
            result.append(store.get(rec.ingestion_id) if reader == 'get' else store.list_recent()[0])
        except BaseException as exc:
            failures.append(exc)
        finally:
            done.set()
    worker = threading.Thread(target=writer)
    polling = threading.Thread(target=poller)
    worker.start()
    try:
        assert writing.wait(2)
        polling.start()
        assert entered.wait(2)
        # The writer owns publication; a reader must wait, not return None,
        # omit history, expose an OS error, or consume an old terminal state.
        assert not done.wait(.05)
    finally:
        publish.set()
        worker.join(3)
        if polling.ident is not None:
            polling.join(3)
    assert not worker.is_alive() and not polling.is_alive()
    assert not failures
    assert result[0]['status'] == 'FAILED'
    assert result[0]['finished_at']
    assert store.get(rec.ingestion_id) == rec.snapshot()
