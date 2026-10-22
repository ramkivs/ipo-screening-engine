"""A28.1 mechanical format/integrity tests, NEVER qualified positive fixtures.

Pins below deliberately refer to nonexistent test documents. Passing structural
and digest checks MUST NOT be interpreted as source authority or Final admission.
"""
import copy
import json

import pytest

from ipo_screening.gmp_binding import binding_digest, verify_binding_integrity, BindingIntegrityError
from ipo_screening.hashing import canonical_json


def pin(name):
    return {'ref': f'tests/format-only/{name}.md', 'sha256': 'a' * 64}


@pytest.fixture
def subject():
    quote = lambda text: {'locator': 'line 1', 'quote': text}
    return {
        'contract_version': 'A28.1', 'publisher_id': 'FORMAT-ONLY',
        'issuer_id': 'ISSUER-A', 'issue_id': 'OFFER-1',
        'publisher_issue_url': 'https://publisher.example/ipo/format-only',
        'qualification_decision': pin('NOT-AN-APPROVAL'),
        'qualification_scope': pin('NOT-A-SCOPE'),
        'qualification_evidence': [pin('NOT-QUALIFIED-EVIDENCE')],
        'observation': {'source_id': 'FORMAT-ONLY', 'pct': '71.4',
                        'as_of': '2026-10-15T10:32:00.000000Z', 'trend': None},
        'evidence': {'manifest': pin('manifest'), 'artifact_id': 'format-only',
                     'artifact': pin('artifact'),
                     'capture_start': '2026-10-15T13:15:00.000000Z',
                     'capture_end': '2026-10-15T13:18:00.000000Z',
                     'identity_quote': quote('Format Only'), 'pct_quote': quote('+71.4%'),
                     'as_of_quote': quote('Publisher stamp'), 'trend_quote': None},
        'selection': {'policy': 'explicit-only-a1', 'adjudications': []},
        'context': {'evaluation_at': '2026-10-15T14:00:00.000000Z', 'mode': 'FINAL',
                    'engine_version': '1.5.0', 'spec_version': '1.5',
                    'config_sha256': 'b' * 64, 'policy_refs': [pin('A28')]},
    }


def test_format_digest_is_deterministic_not_authorization(subject):
    digest = binding_digest(subject)
    shuffled = dict(reversed(list(subject.items())))
    assert binding_digest(shuffled) == digest
    assert binding_digest(json.loads(json.dumps(subject))) == digest
    assert verify_binding_integrity({'subject': subject, 'sha256': digest}) is None
    assert 'NOT-AN-APPROVAL' in subject['qualification_decision']['ref']
    assert 'evaluation_id' not in canonical_json(subject)


@pytest.mark.parametrize('path', [
    ('issuer_id',), ('issue_id',), ('publisher_id',),
    ('qualification_decision', 'sha256'), ('qualification_scope', 'sha256'),
    ('evidence', 'artifact', 'sha256'), ('evidence', 'manifest', 'sha256'),
    ('context', 'config_sha256'), ('context', 'evaluation_at'),
    ('observation', 'pct'),
])
def test_substitution_cannot_reuse_binding_digest(subject, path):
    digest = binding_digest(subject)
    changed = copy.deepcopy(subject)
    node = changed
    for key in path[:-1]:
        node = node[key]
    key = path[-1]
    node[key] = ('2026-10-15T15:00:00.000000Z' if key == 'evaluation_at' else
                 '72.4' if key == 'pct' else 'c' * 64 if key.endswith('sha256') else 'SUBSTITUTED')
    with pytest.raises(BindingIntegrityError, match='digest mismatch'):
        verify_binding_integrity({'subject': changed, 'sha256': digest})


@pytest.mark.parametrize('case', ['extra', 'eval-id', 'zero', 'negative-zero', 'plus', 'exponent',
    'trailing-zero', 'non-nfc', 'offsetless', 'invalid-date', 'future', 'late-capture',
    'stale', 'inverted', 'unsupported-trend', 'hidden-label', 'duplicate-ref',
    'unordered', 'contradictory-pin', 'traversal', 'non-https'])
def test_malformed_or_ineligible_subject_rejected(subject, case):
    if case == 'extra': subject['approval'] = True
    elif case == 'eval-id': subject['context']['evaluation_id'] = 'circular'
    elif case in ('zero', 'negative-zero', 'plus', 'exponent', 'trailing-zero'):
        subject['observation']['pct'] = {'zero':'0', 'negative-zero':'-0', 'plus':'+1', 'exponent':'1e2', 'trailing-zero':'1.00'}[case]
    elif case == 'non-nfc': subject['issuer_id'] = 'e\u0301'
    elif case == 'offsetless': subject['observation']['as_of'] = '2026-10-15T10:32:00'
    elif case == 'invalid-date': subject['observation']['as_of'] = '2026-02-30T10:32:00.000000Z'
    elif case == 'future': subject['observation']['as_of'] = '2026-10-15T15:00:00.000000Z'
    elif case == 'late-capture': subject['context']['evaluation_at'] = '2026-10-15T13:16:00.000000Z'
    elif case == 'stale': subject['observation']['as_of'] = '2026-10-14T13:59:59.999999Z'
    elif case == 'inverted': subject['evidence']['capture_start'] = '2026-10-15T13:19:00.000000Z'
    elif case == 'unsupported-trend': subject['observation']['trend'] = 'sideways'
    elif case == 'hidden-label': subject['evidence']['trend_quote'] = {'locator':'line 1','quote':'up'}
    elif case == 'duplicate-ref': subject['context']['policy_refs'] *= 2
    elif case == 'unordered': subject['context']['policy_refs'] = [pin('z'), pin('a')]
    elif case == 'contradictory-pin': subject['qualification_scope'] = dict(subject['qualification_decision'], sha256='b'*64)
    elif case == 'traversal': subject['qualification_decision']['ref'] = '../approval.md'
    elif case == 'non-https': subject['publisher_issue_url'] = 'http://publisher.example/ipo/x'
    with pytest.raises(BindingIntegrityError): binding_digest(subject)


def test_inclusive_time_boundary_and_optional_linked_trend(subject):
    subject['context']['evaluation_at'] = '2026-10-16T10:32:00.000000Z'
    digest = binding_digest(subject)
    subject['context']['evaluation_at'] = '2026-10-16T10:32:00.000001Z'
    with pytest.raises(BindingIntegrityError): binding_digest(subject)
    subject['context']['evaluation_at'] = '2026-10-16T10:32:00.000000Z'
    subject['observation']['trend'] = 'strong'
    subject['evidence']['trend_quote'] = {'locator':'line 5', 'quote':'rising'}
    assert binding_digest(subject) != digest
    subject['evidence']['trend_quote']['quote'] = 'down'
    with pytest.raises(BindingIntegrityError): binding_digest(subject)


@pytest.mark.parametrize('digest', ['0'*64, 'sha256:'+'a'*64, 'generic-market-digest', None])
def test_invalid_or_generic_digest_is_not_binding(subject, digest):
    with pytest.raises(BindingIntegrityError): verify_binding_integrity({'subject':subject, 'sha256':digest})


def test_fragments_cannot_assign_different_byte_hashes_to_the_same_file(subject):
    subject['qualification_scope'] = dict(subject['qualification_decision'], ref=subject['qualification_decision']['ref']+'#scope', sha256='b'*64)
    with pytest.raises(BindingIntegrityError, match='contradictory digest pins'):
        binding_digest(subject)


def test_strict_sidecar_parse_and_duplicate_rejection(subject):
    from ipo_screening.gmp_binding import parse_binding
    envelope = {'subject':subject, 'sha256':binding_digest(subject)}
    text = json.dumps(envelope)
    assert parse_binding(text) == envelope
    duplicate = text.replace('"publisher_id": "FORMAT-ONLY"', '"publisher_id": "FORMAT-ONLY", "publisher_id": "SUBSTITUTED"')
    with pytest.raises(BindingIntegrityError): parse_binding(duplicate)
    with pytest.raises(BindingIntegrityError): parse_binding('{not JSON}')
