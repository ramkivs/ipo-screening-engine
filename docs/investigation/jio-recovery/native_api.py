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
    result = {'runtime_sha': os.getenv('GITHUB_SHA'), 'platform': sys.platform,
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
        proc = subprocess.Popen([sys.executable, __file__, 'serve', str(port)],
                                cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
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
                _, duplicate = upload(client)
                result['duplicate'] = duplicate
                assert duplicate['evaluation_id'] == terminal['evaluation_id']
                assert terminal['evaluation_run'] and terminal['persisted']
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
        publish(result)
    if 'diagnostic_traceback' in result:
        raise RuntimeError('Native API diagnostic failed; see retained full traceback')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        serve(sys.argv[2])
    else:
        main()
