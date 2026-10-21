"""Read-only remote source/artifact readback for the extraction enhancement."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[3]
BASE = '4ce17356e3a68d45f80b71f73f8bbc53beb62155'
RUNTIME = 'e416b1f808d09bf96b8446430ea86c93d3071557'
PREFIX = 'docs/investigation/offer-extraction-improvements-2026-10-21/'


def cmd(*args):
    return subprocess.check_output(args, cwd=ROOT)


def api(path):
    return json.loads(cmd('gh', 'api', 'repos/ramkivs/ipo-screening-engine/' + path))


def main():
    head = cmd('git', 'rev-parse', 'HEAD').decode().strip()
    assert cmd('git', 'branch', '--show-current').decode().strip() == 'arena/95234306-ipo-screening-engine'
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], cwd=ROOT, check=True)
    assert cmd('git', 'ls-remote', 'origin', 'refs/heads/arena/95234306-ipo-screening-engine').decode().split()[0] == head
    commit = api('commits/' + head)
    assert commit['sha'] == head
    tree = api('git/trees/' + commit['commit']['tree']['sha'] + '?recursive=1')
    assert not tree['truncated']
    remote = {row['path']:row['sha'] for row in tree['tree'] if row['type']=='blob'}
    local = {}
    for row in cmd('git', 'ls-tree', '-rz', head).split(b'\0'):
        if row:
            meta, path = row.split(b'\t',1)
            local[path.decode()] = meta.decode().split()[2]
    assert remote == local
    blobs = []
    for path in cmd('git', 'diff', '--name-only', BASE, head).decode().splitlines():
        if path not in local:
            continue
        data = base64.b64decode(api('git/blobs/' + local[path])['content'])
        assert data == cmd('git', 'show', head + ':' + path)
        blobs.append({'path':path, 'blob':local[path], 'sha256':hashlib.sha256(data).hexdigest()})
    protected = ['config','schema','fixtures','handoff/decisions',
                 'engine/ipo_screening/extraction/price_band_notice.py',
                 'engine/ipo_screening/extraction/prospectus_terms.py']
    assert not cmd('git','diff','--name-only',BASE,head,'--',*protected).strip()
    checks = api('commits/' + RUNTIME + '/check-runs?per_page=100')['check_runs']
    parts = sorted([r for r in checks if r['name'].startswith('Jio native API evidence ')],key=lambda r:int(r['name'].rsplit(' ',1)[1]))
    assert parts and [int(r['name'].rsplit(' ',1)[1]) for r in parts] == list(range(len(parts)))
    assert all(r['status']=='completed' and r['head_sha']==RUNTIME for r in parts)
    raw = zlib.decompress(base64.b64decode(''.join(r['output']['text'] for r in parts)))
    live = json.loads(raw)
    assert live == json.loads((ROOT/PREFIX/'native-api-result.json').read_text())
    assert live['runtime_sha']==RUNTIME and live['platform']=='win32'
    assert not live['accepted'] and not live.get('diagnostic_traceback')
    terminal = live['terminal']
    assert terminal == live['terminal_after_restart']
    assert terminal['status']=='BLOCKED' and terminal['missing_fields']==['issue.fresh_issue']
    assert terminal['evaluation_id'] is None and not terminal['evaluation_run'] and not terminal['persisted']
    assert live['evaluations_before_restart']['total']==live['evaluations_after_restart']['total']==0
    ofs = [e['details'] for e in terminal['events'] if e['event_type']=='field_evidence' and e['details']['field']=='issue.ofs']
    assert any(e['origin']=='official_discovery' and e['verification']=='VERIFIED' and e['value']==0 and e['confidence']==1 and e['content_hash']==live['pdf_sha256'] for e in ofs)
    paper_ocr = [row for row in live['actual_ocr_invocations'] if 'RATIOS_JPL.zip' in row['uri']]
    assert len(paper_ocr)==3 and all(not row.get('traceback') and row['metadata']['ocr']['read_budget_seconds']==270 for row in paper_ocr)
    job = next(r for r in checks if r['name']=='actual-api')
    assert job['conclusion']=='success'
    main_sha = cmd('git','ls-remote','origin','refs/heads/main').decode().split()[0]
    assert main_sha=='01ba66c12ca1195fd7acbd287c3e39a019808094'
    pr = api('pulls/6')
    assert pr['state']=='open' and not pr['merged']
    assert pr['head']['sha']=='e05c0efbca1ecb3024e52da73a22e180ea171118'
    assert pr['head']['ref']=='arena/5dd3fe52-ipo-screening-engine'
    assert pr['base']['ref']=='arena/573e69a4-ipo-screening-engine'
    receipt = {'verified_at':datetime.now(timezone.utc).isoformat(),'published_sha':head,
        'implementation_runtime':RUNTIME,'remote_tree_matches':len(local),'changed_blobs_fetched':blobs,
        'native_check_ids':[r['id'] for r in parts], 'decoded_native_sha256':hashlib.sha256(raw).hexdigest(),
        'native_job_conclusion':job['conclusion'],'native_artifact_matches':True,
        'terminal_id':terminal['ingestion_id'],'terminal_status':terminal['status'],
        'missing_fields':terminal['missing_fields'],'durable_restart_equal':True,
        'no_evaluation_or_persistence':True,'success_idempotency':'NOT_RUN: fresh cash unresolved',
        'protected_paths_unchanged':protected,'main':main_sha,
        'pr6':{'state':pr['state'],'merged':pr['merged'],'head':pr['head']['sha'],'base':pr['base']['ref']}}
    Path(sys.argv[1]).write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'head':head,'paths':len(local),'blobs_fetched':len(blobs),'terminal':terminal['ingestion_id'],'verified':True}))


if __name__=='__main__':
    main()
