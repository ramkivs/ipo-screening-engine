"""Independent read-only GitHub source, live Checks and protection readback.
Run after publication: python .../verify_publication.py --output RECEIPT.json
Receipt refers to the already-published commit; publishing that receipt is a
separate append-only commit, not a circular claim about its own contents.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[3]
REPO = 'repos/ramkivs/ipo-screening-engine'
BASELINE = '0d1d48ba2c04f9a7b306e53c330dd3701559820e'


def command(*args):
    return subprocess.check_output(args, cwd=ROOT)


def api(path):
    return json.loads(command('gh', 'api', REPO + '/' + path))


def check_result(sha, prefix, filename):
    checks = api('commits/' + sha + '/check-runs?per_page=100')['check_runs']
    parts = sorted([c for c in checks if c['name'].startswith(prefix)],
                   key=lambda c: int(c['name'][len(prefix):]))
    assert parts and [int(c['name'][len(prefix):]) for c in parts] == list(range(len(parts)))
    assert all(c['head_sha'] == sha and c['status'] == 'completed' for c in parts)
    packed = ''.join(c['output']['text'] for c in parts)
    raw = zlib.decompress(base64.b64decode(packed))
    parsed = json.loads(raw)
    assert parsed == json.loads((ROOT / filename).read_text(encoding='utf-8')), filename
    return parsed, {'head_sha': sha, 'check_ids': [c['id'] for c in parts],
                    'decoded_sha256': hashlib.sha256(raw).hexdigest(), 'local_json_matches': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--anchor-sha', required=True)
    args = parser.parse_args()
    head = command('git', 'rev-parse', 'HEAD').decode().strip()
    assert command('git', 'branch', '--show-current').decode().strip() == 'arena/95234306-ipo-screening-engine'
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASELINE, head], cwd=ROOT, check=True)
    remote = api('commits/' + head)
    assert remote['sha'] == head
    assert command('git', 'ls-remote', 'origin', 'refs/heads/arena/95234306-ipo-screening-engine').decode().split()[0] == head
    tree = {r['path']: r for r in api('git/trees/' + remote['commit']['tree']['sha'] + '?recursive=1')['tree']}
    local = {}
    for record in command('git', 'ls-tree', '-r', '-z', head).split(b'\0'):
        if record:
            meta, name = record.split(b'\t', 1)
            mode, kind, sha = meta.decode().split()
            local[name.decode('utf-8')] = sha
    assert all(tree[name]['sha'] == sha for name, sha in local.items())
    readback = []
    changed = command('git', 'diff', '--name-only', '-z', BASELINE, head).split(b'\0')
    for name in changed:
        if not name:
            continue
        name = name.decode('utf-8')
        if name not in local:
            continue
        blob = api('git/blobs/' + local[name])
        raw = base64.b64decode(blob['content'])
        expected = command('git', 'show', head + ':' + name)
        assert raw == expected, name
        readback.append({'path': name, 'blob': local[name], 'sha256': hashlib.sha256(raw).hexdigest()})
    main_sha = command('git', 'ls-remote', 'origin', 'refs/heads/main').decode().split()[0]
    assert main_sha == '01ba66c12ca1195fd7acbd287c3e39a019808094'
    pr = api('pulls/6')
    assert pr['state'] == 'open' and not pr['merged'] and pr['merged_at'] is None
    assert pr['head']['sha'] == 'e05c0efbca1ecb3024e52da73a22e180ea171118'
    assert pr['head']['ref'] == 'arena/5dd3fe52-ipo-screening-engine'
    assert pr['base']['ref'] == 'arena/573e69a4-ipo-screening-engine'
    protected = ['config', 'schema', 'fixtures', 'handoff/decisions',
        'engine/ipo_screening/extraction/price_band_notice.py',
        'engine/ipo_screening/extraction/prospectus_terms.py']
    assert not command('git', 'diff', '--name-only', BASELINE, head, '--', *protected).strip()
    pfx = 'docs/investigation/jio-recovery/'
    live, live_receipt = check_result('62bad2c33464f7e8c7cc3c35368d97cff1295486', 'Jio native API evidence ', pfx + 'latest-api-result.json')
    source, source_receipt = check_result('0f5e226e830433f9f083129c047443b5ef79c100', 'BSE published SPA contract ', pfx + 'independent-source-audit.json')
    extra, extra_receipt = check_result('3d53cb0801762a7805442bdaa6c5084ddb04334f', 'BSE published SPA contract ', pfx + 'additional-official-documents.json')
    anchor, anchor_receipt = check_result(args.anchor_sha, 'Anchor original-page review ', pfx + 'anchor-review.json')
    terminal = live['terminal']
    assert live['accepted'] is False and not live.get('diagnostic_traceback')
    assert terminal == live['terminal_after_restart']
    assert terminal['status'] == 'BLOCKED' and terminal['missing_fields'] == ['issue.fresh_issue']
    assert not terminal['evaluation_run'] and not terminal['persisted'] and terminal['evaluation_id'] is None
    assert live['evaluations_before_restart']['total'] == live['evaluations_after_restart']['total'] == 0
    source_rows = [r for r in source['requests'] if 'public_response_zlib_base64' in r]
    for row in source_rows:
        raw = zlib.decompress(base64.b64decode(row['public_response_zlib_base64']))
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        assert json.loads(raw) == row['public_json']
        assert any(r.get('sha256') == row['sha256'] and r['url'] == row['url'] for r in live['actual_source_requests'])
    ocr = [r for r in live['actual_ocr_invocations'] if 'RATIOS_JPL.zip' in r['uri']]
    assert len(ocr) == 3 and all(not r.get('traceback') and r['metadata']['ocr']['read_budget_seconds'] == 270 for r in ocr)
    for page in anchor['pages']:
        if page.get('original_page_png_base64'):
            assert hashlib.sha256(base64.b64decode(page['original_page_png_base64'])).hexdigest() == page['image_sha256']
    assert anchor['complete_ocr_invocation'] and len(anchor['pages']) == anchor['page_count']
    job = api('actions/jobs/119347179710')
    assert job['conclusion'] == 'success'
    receipt = {'verified_at': datetime.now(timezone.utc).isoformat(), 'published_sha': head,
        'required_baseline': BASELINE, 'baseline_is_ancestor': True, 'main_sha': main_sha,
        'pr6': {'state': pr['state'], 'merged': pr['merged'], 'head': pr['head']['sha'], 'base': pr['base']['ref']},
        'all_remote_tree_blob_ids_match': len(local), 'changed_blobs_individually_fetched': readback,
        'protected_paths_unchanged': protected, 'actual_api': live_receipt,
        'independent_sources': source_receipt, 'additional_documents': extra_receipt, 'anchor_review': anchor_receipt,
        'native_job': {'id': job['id'], 'conclusion': job['conclusion'], 'steps': job['steps']},
        'terminal_id': terminal['ingestion_id'], 'terminal_after_restart_identical': True,
        'no_evaluation_before_or_after_restart': True, 'success_idempotency': 'NOT_RUN: authoritative fresh cash unresolved',
        'acceptance': 'B: restoration incomplete; source/evidence boundary, no fabricated evaluation'}
    Path(args.output).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sha': head, 'tree_paths': len(local), 'blobs_read': len(readback), 'terminal': terminal['ingestion_id'], 'result': 'PASS: incomplete restoration accurately verified'}))


if __name__ == '__main__':
    main()
