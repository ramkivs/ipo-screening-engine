"""Synthetic storage fault reproducer. Not a diagnosis of the Windows process.
Run with PYTHONPATH=engine .venv/bin/python this_file.py from repository root.
"""
import ast
import __future__
import json
import subprocess
import tempfile
import threading
import types
from pathlib import Path
import ipo_screening.presentation.service as module
from ipo_screening.issue_terms import IssueTermsResolver
root = Path(__file__).resolve().parents[3]
old = subprocess.check_output(['git', 'show', 'cb5c5e5:engine/ipo_screening/presentation/service.py'], cwd=root).decode()
cls = next(n for n in ast.parse(old).body if isinstance(n, ast.ClassDef) and n.name == 'PresentationService')
node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'start_ingestion_async')
scope = dict(vars(module))
exec(compile(ast.Module(body=[node], type_ignores=[]), 'baseline-cb5c5e5', 'exec', flags=__future__.annotations.compiler_flag), scope)
rows = []
for version in ('baseline', 'corrected'):
    with tempfile.TemporaryDirectory() as tmp:
        svc = module.PresentationService(module.PresentationConfig(store_root=Path(tmp) / 'evaluations',
            config_dir=root / 'config', issue_terms_resolver=IssueTermsResolver([])))
        if version == 'baseline':
            svc.start_ingestion_async = types.MethodType(scope['start_ingestion_async'], svc)
        original = svc.activity_store.save
        faults = []
        def save(record):
            if any(e['stage'] == 'document_validation' for e in record['events']) and len(faults) < 2:
                faults.append(True)
                raise OSError('injected activity write interruption')
            original(record)
        svc.activity_store.save = save
        rec = svc.start_ingestion_async(b'%PDF-1.4 synthetic')
        for worker in threading.enumerate():
            if worker.name == 'ingest-' + rec.ingestion_id:
                worker.join(2)
        saved = svc.get_ingestion_activity(rec.ingestion_id)
        row = {'version': version, 'injected_write_failures': len(faults), 'status': saved['status'],
               'finished_at': saved['finished_at'], 'error_code': saved['error_code'],
               'event_stages': [e['stage'] for e in saved['events']], 'evaluation_id': saved['evaluation_id']}
        rows.append(row)
        assert saved['status'] == ('RUNNING' if version == 'baseline' else 'FAILED'), row
        assert saved['evaluation_id'] is None
        if version == 'baseline':
            assert row['event_stages'] == ['upload', 'upload'] and saved['finished_at'] is None
Path(__file__).with_name('boundary-results.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows, indent=2))
