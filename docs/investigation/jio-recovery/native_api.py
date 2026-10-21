"""Native HTTP baseline: actual PDF, default discovery, durable isolated store.

No supplied terms, substituted transport, parser mocks, or weakened gates.
Writes only under JIO_RECOVERY_OUTPUT, outside the tracked repository.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import traceback
import urllib.request
import zlib

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.environ['JIO_RECOVERY_OUTPUT'])
OUT.mkdir(parents=True, exist_ok=True)


def serve(port):
    # Read-only observation: original production transport still performs every
    # request with its original timeout, session, retries and return bytes.
    import ipo_screening.issue_terms as terms
    original_fetch = terms._default_http_fetch
    sources = OUT / 'sources'
    sources.mkdir(exist_ok=True)

    def observed_fetch(url, timeout_seconds, **kwargs):
        row = {'url': url, 'timeout_seconds': timeout_seconds}
        try:
            raw = original_fetch(url, timeout_seconds, **kwargs)
            digest = hashlib.sha256(raw).hexdigest()
            (sources / (digest + '.bin')).write_bytes(raw)
            row.update(sha256=digest, bytes=len(raw))
            return raw
        except Exception:
            row['traceback'] = traceback.format_exc()
            raise
        finally:
            with (sources / 'requests.jsonl').open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(row) + '\n')
    terms._default_http_fetch = observed_fetch
    # Observe actual third-party requests without substituting any bytes.
    from ipo_screening import aggregator_issue_terms as aggregator
    original_aggregator_fetch = aggregator.fetch_public
    def observed_aggregator_fetch(url):
        row = {'url': url, 'authority': aggregator.TAG}
        try:
            raw = original_aggregator_fetch(url)
            digest = hashlib.sha256(raw).hexdigest()
            (sources / (digest + '.bin')).write_bytes(raw)
            row.update(sha256=digest, bytes=len(raw))
            return raw
        except Exception:
            row['traceback'] = traceback.format_exc()
            raise
        finally:
            with (sources / 'requests.jsonl').open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(row) + '\n')
    aggregator.fetch_public = observed_aggregator_fetch
    from ipo_screening.extraction import official_notice_ocr as ocr
    original_ocr = ocr.parse_if_scanned

    def observed_ocr(raw, uri):
        row = {'uri': uri, 'document_sha256': hashlib.sha256(raw).hexdigest()}
        started = time.monotonic()
        try:
            result = original_ocr(raw, uri)
            row['ocr_performed'] = result is not None
            if result is not None:
                row['metadata'] = result.metadata
                row['fields'] = {}
                for name in ('price_band_low', 'price_band_high', 'lot_size', 'open_date',
                             'close_date', 'fresh_issue_amount', 'ofs_amount'):
                    obj = getattr(result, name, None)
                    row['fields'][name] = ({key: getattr(obj, key) for key in
                        ('value', 'quote', 'page', 'locator', 'extraction_method', 'confidence', 'verification')}
                        if obj is not None else None)
            return result
        except Exception:
            row['traceback'] = traceback.format_exc()
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic() - started
            with (sources / 'ocr.jsonl').open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(row, default=str) + '\n')
    ocr.parse_if_scanned = observed_ocr
    from ipo_screening.presentation.api import create_app
    from ipo_screening.presentation.service import PresentationConfig, PresentationService
    import uvicorn
    service = PresentationService(PresentationConfig(
        store_root=OUT / 'evaluations', config_dir=ROOT / 'config'))
    uvicorn.run(create_app(service), host='0.0.0.0', port=int(port))


def publish(result):
    (OUT / 'api-result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    if not os.getenv('GITHUB_ACTIONS'):
        return
    packed = base64.b64encode(zlib.compress(json.dumps(result).encode())).decode()
    for index, offset in enumerate(range(0, len(packed), 55000)):
        body = {'name': f'Jio native API evidence {index}',
                'head_sha': os.environ['GITHUB_SHA'], 'status': 'completed',
                'conclusion': 'success' if result.get('accepted') else 'neutral',
                'output': {'title': result.get('terminal', {}).get('status', 'DIAGNOSTIC_FAILED'),
                           'summary': 'Actual Windows HTTP API upload; default production discovery. '
                                      'Neutral is NOT restoration success. Compressed evidence part '
                                      f'{index + 1}/{(len(packed) + 54999) // 55000}.',
                           'text': packed[offset:offset + 55000]}}
        req = urllib.request.Request(
            'https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + '/check-runs',
            data=json.dumps(body).encode(), method='POST', headers={
                'Authorization': 'Bearer ' + os.environ['LIVE_CHECK_TOKEN'],
                'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            print('Evidence check: ' + json.load(response)['html_url'], flush=True)


def main():
    import httpx
    from importlib.metadata import version
    result = {'runtime_dependencies': {name: version(name) for name in
              ('rapidocr', 'onnxruntime', 'pypdfium2', 'pypdf')},
              'runtime_sha': os.getenv('GITHUB_SHA'), 'platform': sys.platform,
              'python': sys.version, 'accepted': False}
    pdf = ROOT / 'evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf'
    raw = pdf.read_bytes()
    result['pdf_sha256'] = hashlib.sha256(raw).hexdigest()
    result['identity_scope'] = 'Repository Jio PDF; user upload identity not established'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    log = (OUT / 'server.log').open('wb')
    process = None

    def start():
        child_env = dict(os.environ)
        child_env.pop('LIVE_CHECK_TOKEN', None)
        proc = subprocess.Popen([sys.executable, __file__, 'serve', str(port)],
                                cwd=ROOT, env=child_env, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(f'API exited during startup: {proc.returncode}')
            try:
                if httpx.get(base + '/api/v1/health', timeout=2).status_code == 200:
                    return proc
            except httpx.TransportError:
                pass
            time.sleep(1)
        proc.terminate()
        proc.wait(timeout=30)
        raise TimeoutError('API health did not become ready within 90s')

    def upload(client):
        response = client.post('/api/v1/ingestions/start', headers={'Origin': base},
                               files={'file': (pdf.name, raw, 'application/pdf')}, data={'mode': 'final'})
        response.raise_for_status()
        activity_url = response.json()['activity_url']
        print('Actual API upload: ' + response.text, flush=True)
        deadline = time.monotonic() + 2100
        sequence = -1
        while time.monotonic() < deadline:
            response = client.get(activity_url)
            response.raise_for_status()
            terminal = response.json()
            events = terminal.get('events', [])
            if len(events) != sequence:
                sequence = len(events)
                print(json.dumps({'status': terminal['status'], 'events': sequence,
                                  'last_event': events[-1] if events else None}), flush=True)
                (OUT / 'latest-activity.json').write_text(json.dumps(terminal, indent=2), encoding='utf-8')
            if terminal.get('finished_at'):
                return activity_url, terminal
            if process.poll() is not None:
                raise RuntimeError(f'API exited during ingestion: {process.returncode}')
            time.sleep(2)
        raise TimeoutError('API did not produce terminal activity in 2100s; not classified as evidence absence')

    try:
        process = start()
        with httpx.Client(base_url=base, timeout=120) as client:
            activity_url, terminal = upload(client)
            result['terminal'] = terminal
            result['evaluations_before_restart'] = client.get('/api/v1/evaluations').json()
            if terminal.get('evaluation_id'):
                eid = terminal['evaluation_id']
                for suffix in ('', '/evidence', '/trace'):
                    response = client.get('/api/v1/evaluations/' + eid + suffix)
                    result['GET_evaluation' + suffix] = {'status': response.status_code, 'body': response.json()}
        # Stop only after terminal activity. Restart reads the SAME durable store.
        process.terminate()
        process.wait(timeout=30)
        process = start()
        with httpx.Client(base_url=base, timeout=120) as client:
            response = client.get(activity_url)
            response.raise_for_status()
            result['terminal_after_restart'] = response.json()
            assert result['terminal_after_restart'] == terminal
            result['evaluations_after_restart'] = client.get('/api/v1/evaluations').json()
            if terminal.get('status') == 'SUCCEEDED':
                assert terminal['evaluation_run'] and terminal['persisted']
                from ipo_screening.evaluation import EvaluationStore
                store = EvaluationStore(OUT / 'evaluations')
                result['independent_hash_verification'] = store.verify_hashes(terminal['evaluation_id'])
                assert result['independent_hash_verification']['result_hash_matches']
                assert not result['independent_hash_verification']['artifact_mismatches']
                stored = store.read_full(terminal['evaluation_id'])
                canonical = stored['input_snapshot']['input']
                result['persisted_issue'] = canonical['issue']
                result['persisted_sources'] = stored.get('provenance', {}).get('sources', [])
                result['persisted_issue_evidence'] = {
                    item['evidence_id']: item for item in stored.get('evidence', {}).get('evidence', [])
                    if item.get('evidence_id', '').startswith('EV-issue')}
                for field in ('price_band_low', 'price_band_high', 'lot_size',
                              'fresh_issue', 'ofs', 'open_date', 'close_date'):
                    assert canonical['issue'].get(field) is not None
                    assert any(item.get('evidence_id') in ('EV-issue.' + field, 'EV-issue-' + field) for item in stored.get('evidence', {}).get('evidence', [])), field
                response = client.get('/api/v1/evaluations/' + terminal['evaluation_id'])
                response.raise_for_status()
                result['GET_evaluation_after_restart'] = response.json()
                assert response.json()['result_hash'] == stored['result_hash']
                assert len(stored['score']['modules']) == 6
                if os.getenv('IPO_ALLOW_AGGREGATOR_ISSUE_TERMS') == '1':
                    assert response.json()['authority_warnings']
                    assert any(src['source_id'].startswith('SRC-AGG-') for src in result['persisted_sources'])
                    assert any('THIRD_PARTY_AGGREGATOR_OVERRIDE' in item.get('note', '') for item in result['persisted_issue_evidence'].values())
                    assert result['GET_evaluation/evidence']['status'] == 200
                    assert any(item.get('verification') == 'THIRD_PARTY_AGGREGATOR_OVERRIDE' for item in result['GET_evaluation/evidence']['body']['items'])
                _, duplicate = upload(client)
                result['duplicate'] = duplicate
                assert duplicate['evaluation_id'] == terminal['evaluation_id']
                assert duplicate['is_duplicate']
                result['accepted'] = True
            else:
                assert not terminal['persisted'] and terminal['evaluation_id'] is None
                result['duplicate'] = 'NOT_RUN: blocked before evaluation; success idempotency unproven'
    except Exception:
        result['diagnostic_traceback'] = traceback.format_exc()
        print(result['diagnostic_traceback'], flush=True)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=30)
        log.close()
        result['server_log'] = (OUT / 'server.log').read_text(encoding='utf-8', errors='replace')
        requests = OUT / 'sources' / 'requests.jsonl'
        if requests.exists():
            result['actual_source_requests'] = [json.loads(line) for line in requests.read_text(encoding='utf-8').splitlines()]
            result['aggregator_source_bytes'] = [
                dict(url=row['url'], sha256=row['sha256'], raw_zlib_base64=base64.b64encode(zlib.compress((OUT / 'sources' / (row['sha256'] + '.bin')).read_bytes(), 9)).decode())
                for row in result['actual_source_requests'] if row.get('authority') == 'THIRD_PARTY_AGGREGATOR_OVERRIDE' and row.get('sha256')]
            from source_inventory import inspect_sources
            result['source_inventory'] = inspect_sources(OUT / 'sources', OUT / 'review')
            ocr_log = OUT / 'sources' / 'ocr.jsonl'
            if ocr_log.exists():
                result['actual_ocr_invocations'] = [json.loads(line) for line in ocr_log.read_text(encoding='utf-8').splitlines()]
        publish(result)
    if 'diagnostic_traceback' in result:
        raise RuntimeError('Native API diagnostic failed; see retained full traceback')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        serve(sys.argv[2])
    else:
        main()
