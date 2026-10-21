"""Actual Jio PDF -> actual official HTTP -> real validation/evaluation gates.

All writes are isolated in TemporaryDirectory. No extraction/evaluation mock,
manual terms, configured issuer URL, fixture fallback or production-store writes.
BLOCKED is reported as BLOCKED, never treated as end-to-end acceptance success.
Network/official-disclosure limitations are evidence, not publication absence.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

from ipo_screening.issue_terms import IssueTermsResolver, OfficialDiscoveryProvider
from ipo_screening.presentation.service import (
    IngestionAwaitingIssueTermsError, PresentationConfig, PresentationService,
)


def emit(kind, row):
    text = json.dumps({'kind': kind, **row}, separators=(',', ':'), default=str)
    print(text, flush=True)
    if os.getenv('GITHUB_ACTIONS'):
        # GitHub annotations truncate at 4096 characters. Split only large
        # diagnostics, retaining an explicit part index (not invalid JSON).
        for index in range(0, len(text), 2800):
            piece = json.dumps({'kind': 'json_part', 'record': kind, 'index': index // 2800,
                                'text': text[index:index + 2800]}, separators=(',', ':'))
            print('::notice title=Live ingestion verification::' + piece.replace('%', '%25').replace('\n', '%0A'), flush=True)


root = Path(__file__).resolve().parents[3]
pdf = root / 'evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf'
emit('input', {'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
               'scope': 'repository PDF, not proof of byte identity with user upload; temporary stores only'})
with tempfile.TemporaryDirectory(prefix='actual-jio-discovery-') as temp:
    svc = PresentationService(PresentationConfig(store_root=Path(temp) / 'evaluations',
        config_dir=root / 'config', issue_terms_resolver=IssueTermsResolver([
            OfficialDiscoveryProvider(timeout_seconds=5)])))
    rec = svc.activity_store.new_recorder(filename=pdf.name, mode='final')
    try:
        response = svc.ingest_document(pdf.read_bytes(), pdf.name, 'final', recorder=rec)
        record = svc.eval_store.read(response.evaluation_id)
        assert record is not None, 'success without durable evaluation is forbidden'
        emit('persisted_input', {'evaluation_id': response.evaluation_id,
                                'issue': record['input_snapshot']['input']['issue']})
    except IngestionAwaitingIssueTermsError as exc:
        emit('remaining_terms', {'missing_fields': exc.missing_fields,
            'status': exc.resolution.get('status'),
            'ready': exc.resolution.get('ready'),
            'assembly_error': exc.resolution.get('assembly_error'),
            'field_diagnostics': exc.resolution.get('field_diagnostics')})
    except Exception as exc:
        emit('other_gate_failure', {'type': type(exc).__name__, 'message': str(exc)})
    saved = svc.get_ingestion_activity(rec.ingestion_id)
    assert saved == rec.snapshot()
    for event in saved['events']:
        if event['stage'] in ('official_discovery', 'term_resolution', 'evaluation', 'persistence'):
            emit('activity_event', event)
    emit('terminal', {k: saved[k] for k in ('ingestion_id', 'status', 'error_code',
        'finished_at', 'evaluation_run', 'evaluation_id', 'persisted')})
    if saved['status'] == 'SUCCEEDED':
        assert saved['evaluation_run'] and saved['persisted'] and saved['evaluation_id']
    else:
        assert not saved['persisted'] and saved['evaluation_id'] is None
