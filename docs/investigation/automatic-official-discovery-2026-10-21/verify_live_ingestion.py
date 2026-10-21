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
import urllib.request

from ipo_screening.issue_terms import IssueTermsResolver, OfficialDiscoveryProvider
from ipo_screening.presentation.service import (
    IngestionAwaitingIssueTermsError, PresentationConfig, PresentationService,
)


records = []

def emit(kind, row):
    records.append({"kind": kind, **row})
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
        snapshot = record['input_snapshot']['input']
        emit('persisted_input', {'evaluation_id': response.evaluation_id,
            'issue': snapshot['issue'], 'sources': snapshot.get('_sources'),
            'issue_evidence': {k: v for k, v in snapshot.get('_evidence', {}).items() if k.startswith('issue.')}})
    except IngestionAwaitingIssueTermsError as exc:
        emit('remaining_terms', {'missing_fields': exc.missing_fields,
            'status': exc.resolution.get('status'),
            'ready': exc.resolution.get('ready'),
            'assembly_error': exc.resolution.get('assembly_error'),
            'conflicts': exc.resolution.get('conflicts'),
            'field_diagnostics': {f: {'state': d.get('state'), 'candidates': [{k: v for k, v in c.items() if k in ('value', 'unit', 'uri', 'quote', 'content_hash', 'verification')} for c in d.get('candidates', [])]} for f, d in exc.resolution.get('fields', {}).items()}})
    except Exception as exc:
        emit('other_gate_failure', {'type': type(exc).__name__, 'message': str(exc)})
    saved = svc.get_ingestion_activity(rec.ingestion_id)
    assert saved == rec.snapshot()
    emit('terminal', {k: saved[k] for k in ('ingestion_id', 'status', 'error_code',
        'finished_at', 'evaluation_run', 'evaluation_id', 'persisted')})
    for event in saved['events']:
        if event['stage'] == 'official_discovery' and event['event_type'] == 'source_attempt' and event['details'].get('notes'):
            emit('activity_event', event)
    if saved['status'] == 'SUCCEEDED':
        assert saved['evaluation_run'] and saved['persisted'] and saved['evaluation_id']
    else:
        assert not saved['persisted'] and saved['evaluation_id'] is None


# A green diagnostic workflow is not proof of ingestion success. Publish the
# exact terminal result through the Checks API as well as stdout/annotations;
# redirected Actions log storage is not reachable from the restricted sandbox.
# No credential value is printed or persisted. Only this read-only verification
# workflow receives checks:write; the application never receives that token.
if os.getenv('GITHUB_ACTIONS'):
    terminal = next(r for r in records if r['kind'] == 'terminal')
    accepted = terminal['status'] == 'SUCCEEDED' and terminal['evaluation_run'] and terminal['persisted']
    retained = [r for r in records if r['kind'] != 'activity_event']
    summary = 'Actual public HTTP and repository Jio PDF; temporary evaluation store only.\n\n'
    summary += '```json\n' + json.dumps(retained, indent=2, ensure_ascii=True) + '\n```'
    if len(summary.encode('utf-8')) > 60000:
        raise RuntimeError('live-result evidence exceeds check-summary bound; no truncated success published')
    body = {'name': 'Actual Jio ingestion result (official discovery)',
        'head_sha': os.environ['GITHUB_SHA'], 'status': 'completed',
        'conclusion': 'success' if accepted else 'neutral',
        'output': {'title': 'Jio automatic ingestion: ' + terminal['status'], 'summary': summary}}
    request = urllib.request.Request('https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + '/check-runs',
        data=json.dumps(body).encode('utf-8'), method='POST', headers={
            'Authorization': 'Bearer ' + os.environ['LIVE_CHECK_TOKEN'],
            'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json',
            'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=30) as response:
        published = json.load(response)
    print('Actual structured result check: ' + published['html_url'], flush=True)
