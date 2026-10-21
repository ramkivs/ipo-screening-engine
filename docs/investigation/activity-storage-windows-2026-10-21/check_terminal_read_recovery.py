"""Isolated check of worker reconciliation after a real read exception.

Run with PYTHONPATH=engine .venv/bin/python <this file>. No live ingestion,
evaluation, production data or network; synchronous dispatch makes the branch
check deterministic without changing the original lifecycle tests.
"""
import io
import json
import logging
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.service import PresentationConfig, PresentationService

root = Path(__file__).resolve().parents[3]
for fault in (PermissionError(13, "synthetic Windows read denial"),
              json.JSONDecodeError("synthetic corrupt terminal record", "", 0)):
    with tempfile.TemporaryDirectory() as temporary:
        svc = PresentationService(PresentationConfig(
            store_root=Path(temporary) / 'evaluations', config_dir=root / 'config',
            issue_terms_resolver=IssueTermsResolver([])))
        original_get, original_save = svc.activity_store.get, svc.activity_store.save
        faults, saves = [], []
        def get(ingestion_id):
            if not faults:
                faults.append(type(fault).__name__)
                raise fault
            return original_get(ingestion_id)
        def save(record):
            saves.append(record['status'])
            return original_save(record)
        def blocked(**kwargs):
            kwargs['recorder'].finish('BLOCKED', error_code='AWAITING_ISSUE_TERMS')
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        logger = logging.getLogger('ipo_screening.presentation.service')
        logger.addHandler(handler)
        try:
            with patch.object(svc.activity_store, 'get', get), \
                 patch.object(svc.activity_store, 'save', save), \
                 patch.object(svc, 'ingest_document', blocked), \
                 patch.object(threading.Thread, 'start', lambda worker: worker.run()):
                rec = svc.start_ingestion_async(b'%PDF-1.4 isolated boundary check')
        finally:
            logger.removeHandler(handler)
        saved = original_get(rec.ingestion_id)
        assert faults == [type(fault).__name__]
        assert saves.count('BLOCKED') == 2, saves  # finish, then exact snapshot recovery
        assert saved == rec.snapshot()
        assert saved['status'] == 'BLOCKED' and saved['finished_at']
        assert saved['error_code'] == 'AWAITING_ISSUE_TERMS'
        assert not saved['persisted'] and saved['evaluation_id'] is None
        assert sum(e['stage'] == 'finalization' for e in saved['events']) == 1
        assert 'terminal activity could not be read' in output.getvalue()
        print(type(fault).__name__, ': logged, exact terminal snapshot durably recovered; no false success')
print('2 isolated worker terminal-read recovery checks passed')
