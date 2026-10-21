"""Read-only source PDF test in temporary stores; no network, no evaluation permitted.
Run: PYTHONPATH=engine .venv/bin/python -u docs/investigation/ingestion-worker-stall-2026-10-21/reproduce_available_jio.py
This is the repository PDF, not a claim of byte identity with the Windows upload.
"""
import ast
import __future__
import hashlib
import json
import subprocess
import tempfile
import time
import types
from pathlib import Path
import ipo_screening.presentation.service as module
from ipo_screening.issue_terms import IssueTermsResolver

root = Path(__file__).resolve().parents[3]
source = root / 'evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf'
raw = source.read_bytes()
old = subprocess.check_output(['git', 'show', 'cb5c5e595557ed79f5f78bbc3150ac42b5cd7f88:engine/ipo_screening/presentation/service.py'], cwd=root).decode()
cls = next(n for n in ast.parse(old).body if isinstance(n, ast.ClassDef) and n.name == 'PresentationService')
node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'start_ingestion_async')
method = ast.Module(body=[node], type_ignores=[])
scope = dict(vars(module))
exec(compile(method, 'baseline-cb5c5e5', 'exec', flags=__future__.annotations.compiler_flag), scope)

def forbidden(*a, **k):
    raise AssertionError('Evaluation prohibited in this diagnostic reproduction')
module.evaluate = forbidden
rows = []
for label in ('baseline_cb5c5e5_dispatch', 'corrected_dispatch'):
    with tempfile.TemporaryDirectory(prefix='jio-worker-test-') as temp:
        svc = module.PresentationService(module.PresentationConfig(
            store_root=Path(temp) / 'evaluations', config_dir=root / 'config',
            issue_terms_resolver=IssueTermsResolver([])))
        if label.startswith('baseline'):
            svc.start_ingestion_async = types.MethodType(scope['start_ingestion_async'], svc)
        began = time.monotonic()
        rec = svc.start_ingestion_async(raw, source.name, 'final')
        while time.monotonic() - began < 180:
            saved = svc.get_ingestion_activity(rec.ingestion_id)
            if saved['status'] != 'RUNNING':
                break
            time.sleep(.05)
        saved = svc.get_ingestion_activity(rec.ingestion_id)
        row = {'path': label, 'pdf_sha256': hashlib.sha256(raw).hexdigest(),
               'seconds': round(time.monotonic() - began, 2), 'status': saved['status'],
               'error_code': saved['error_code'], 'finished_at': saved['finished_at'],
               'event_count': len(saved['events']),
               'events': [{'stage': e['stage'], 'status': e['status']} for e in saved['events']],
               'evaluation_id': saved['evaluation_id'], 'persisted': saved['persisted']}
        rows.append(row)
        print(json.dumps(row), flush=True)
        assert saved['status'] == 'BLOCKED', row
        assert saved['error_code'] == 'AWAITING_ISSUE_TERMS'
        assert saved['evaluation_id'] is None and not saved['persisted']
Path(__file__).with_name('available-jio-results.json').write_text(json.dumps(rows, indent=2) + '\n')
