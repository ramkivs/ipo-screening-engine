"""SYNTHETIC — NOT QUALIFICATION EVIDENCE. Test-only composition, not admission."""
import hashlib
import json
from pathlib import Path

from ipo_screening.gmp_binding import binding_digest, parse_binding, verify_binding_files
from ipo_screening.gmp_evidence import load_rendered_capture
from ipo_screening.connectors.coordinator import ConnectorCoordinator
from ipo_screening.connectors.adapters import GmpSignalAdapter
from datetime import datetime

LABEL = 'SYNTHETIC — NOT QUALIFICATION EVIDENCE'
CASES = json.loads((Path(__file__).resolve().parents[1] /
    'fixtures/non-authoritative/gmp-mechanics/cases.json').read_text())['cases']
AT = '2026-10-22T12:00:00.000000Z'


def materialize(root, case):
    if case.get('label') != LABEL:
        raise ValueError('synthetic fixture label required')
    prefix = f"synthetic/{case['key']}"
    def put(name, text):
        path = root / prefix / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return {'ref': f'{prefix}/{name}', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    text = f"{LABEL}\n{case['issuer_id']} / {case['issue_id']}\n+{case['pct']}%\n{AT}\n"
    trend_quote = None
    if case['trend'] is not None:
        text += 'Trend: rising\n'
        trend_quote = {'locator': 'line 5', 'quote': 'rising'}
    artifact = put('page.md', text)
    manifest = {
        'label': LABEL, 'captureMethod': {'rawProviderResponseBytesCaptured': False},
        'artifacts': [{'id': 'page', 'file': 'page.md', 'sha256': artifact['sha256'],
            'bytes': len(text.encode()), 'toolResultStatus': 'success',
            'retrievalWindowUtc': {'notBefore': AT, 'notAfter': AT}}],
    }
    manifest_pin = put('capture-manifest.json', json.dumps(manifest))
    quote = lambda line, text: {'locator': f'line {line}', 'quote': text}
    subject = {
        'contract_version': 'A28.1', 'publisher_id': LABEL,
        'issuer_id': case['issuer_id'], 'issue_id': case['issue_id'],
        'publisher_issue_url': f"https://publisher.example/ipo/{case['key']}",
        'qualification_decision': put('NOT-A-DECISION.md', LABEL),
        'qualification_scope': put('NOT-A-SCOPE.md', LABEL),
        'qualification_evidence': [put('NOT-R7-R8.md', LABEL)],
        'observation': {'source_id': 'SYNTHETIC-SOURCE', 'pct': case['pct'], 'as_of': AT, 'trend': case['trend']},
        'evidence': {'manifest': manifest_pin, 'artifact_id': 'page', 'artifact': artifact,
            'capture_start': AT, 'capture_end': AT,
            'identity_quote': quote(2, f"{case['issuer_id']} / {case['issue_id']}"),
            'pct_quote': quote(3, f"+{case['pct']}%"), 'as_of_quote': quote(4, AT),
            'trend_quote': trend_quote},
        'selection': {'policy': 'explicit-only-a1', 'adjudications': []},
        'context': {'evaluation_at': AT, 'mode': 'FINAL', 'engine_version': '1.5.0',
            'spec_version': '1.5', 'config_sha256': 'b'*64,
            'policy_refs': [put('NOT-POLICY-AUTHORITY.md', LABEL)]},
    }
    return {'subject': subject, 'sha256': binding_digest(subject)}


def mechanics(root, envelope, case, unresolved=()):
    """Test-only explicit scenario checks; NEVER an authorization verifier."""
    envelope = parse_binding(json.dumps(envelope))
    verify_binding_files(envelope, root)
    s = envelope['subject']
    if (s['issuer_id'], s['issue_id']) != (case['issuer_id'], case['issue_id']):
        raise ValueError('synthetic cross-issuer/issue mismatch')
    if unresolved:
        raise ValueError('synthetic unresolved declaration; no adjudication inferred')
    e = s['evidence']
    capture = load_rendered_capture(root / e['manifest']['ref'], e['artifact_id'])
    if (e['identity_quote']['quote'] != f"{s['issuer_id']} / {s['issue_id']}"
        or e['pct_quote']['quote'] != f"+{s['observation']['pct']}%"
        or e['as_of_quote']['quote'] != s['observation']['as_of']):
        raise ValueError('synthetic observation/quote mismatch')
    for field in ['identity_quote', 'pct_quote', 'as_of_quote', 'trend_quote']:
        q = e[field]
        if q is not None and capture.text.splitlines()[int(q['locator'].split()[1])-1] != ('Trend: ' + q['quote'] if field == 'trend_quote' else q['quote']):
            raise ValueError('synthetic quote mismatch')
    # A generic supplied-payload adapter preserves UNKNOWN; it grants no authority.
    snap = GmpSignalAdapter().normalize({'gmp_pct': s['observation']['pct'],
        'as_of': s['observation']['as_of'], 'trend': s['observation']['trend']},
        reference_time=datetime.fromisoformat(s['context']['evaluation_at'].replace('Z', '+00:00')))
    ConnectorCoordinator().reconcile_snapshots([snap])
    return {'label': LABEL, 'mechanics': 'PASS', 'production_admission': False,
            'publisher_qualification': 'NOT ESTABLISHED', 'trend': snap.normalized_data['trend']}
