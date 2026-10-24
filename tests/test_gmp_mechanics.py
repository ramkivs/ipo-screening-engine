"""SYNTHETIC — NOT QUALIFICATION EVIDENCE: offline mechanics, NEVER admission."""
import copy
import json
from pathlib import Path

import pytest
from gmp_mechanics_harness import CASES, LABEL, materialize, mechanics
from ipo_screening.gmp_binding import BindingIntegrityError, binding_digest, verify_binding_files
from ipo_screening.evaluation_record import build_evaluation_record_v1
from ipo_screening.pipeline import evaluate
from datetime import datetime, timezone


@pytest.fixture(params=CASES, ids=lambda c: c['key'])
def example(request, tmp_path):
    case = request.param
    return case, materialize(tmp_path, case)


def rehash(e):
    e['sha256'] = binding_digest(e['subject'])


def test_multi_issue_positive_mechanics_are_never_qualification(example, tmp_path):
    case, e = example
    result = mechanics(tmp_path, e, case)
    assert result['label'] == LABEL and result['mechanics'] == 'PASS'
    assert result['production_admission'] is False
    assert result['publisher_qualification'] == 'NOT ESTABLISHED'
    assert result['trend'] == case['trend']
    assert 'SYNTHETIC' in (tmp_path / e['subject']['qualification_decision']['ref']).read_text()


@pytest.mark.parametrize('bad', [None, {}, {'sha256': '0'*64}, {'subject': {}}])
def test_missing_or_malformed_bindings(example, tmp_path, bad):
    with pytest.raises(BindingIntegrityError):
        mechanics(tmp_path, bad, example[0])


@pytest.mark.parametrize('cutoff,valid', [
    ('2026-10-22T12:00:00.000000Z', True),
    ('2026-10-23T12:00:00.000000Z', True),
    ('2026-10-23T12:00:00.000001Z', False),
    ('2026-10-22T11:59:59.999999Z', False),
])
def test_cutoff_boundaries_and_stale_future(example, tmp_path, cutoff, valid):
    case, e = example
    e['subject']['context']['evaluation_at'] = cutoff
    if valid:
        rehash(e)
        assert mechanics(tmp_path, e, case)['production_admission'] is False
    else:
        with pytest.raises(BindingIntegrityError): rehash(e)


@pytest.mark.parametrize('declaration', ['conflict', 'correction', 'withdrawal'])
def test_unresolved_declarations_never_pass_mechanics(example, tmp_path, declaration):
    case, e = example
    with pytest.raises(ValueError, match='unresolved'):
        mechanics(tmp_path, e, case, unresolved=[declaration])


@pytest.mark.parametrize('field', ['artifact', 'manifest'])
def test_mutated_external_bytes_fail_replay_without_changing_record(example, tmp_path, field):
    case, e = example
    saved = json.dumps(e)
    path = tmp_path / e['subject']['evidence'][field]['ref']
    original = path.read_bytes()
    path.write_bytes(original + b'\nmutation')
    with pytest.raises(BindingIntegrityError, match='file digest mismatch'):
        mechanics(tmp_path, json.loads(saved), case)
    assert json.dumps(e) == saved
    path.write_bytes(original)
    assert mechanics(tmp_path, json.loads(saved), case)['mechanics'] == 'PASS'


def test_cross_issuer_issue_and_evaluation_isolation(example, tmp_path):
    case, e = example
    other = next(c for c in CASES if c['key'] != case['key'])
    with pytest.raises(ValueError, match='cross-issuer/issue'):
        mechanics(tmp_path, e, other)
    # Reusing a saved digest with a different evaluation context is invalid.
    changed = copy.deepcopy(e)
    changed['subject']['context']['evaluation_at'] = '2026-10-22T13:00:00.000000Z'
    with pytest.raises(BindingIntegrityError, match='digest mismatch'):
        mechanics(tmp_path, changed, case)
    assert mechanics(tmp_path, e, case)['mechanics'] == 'PASS'


def test_serialization_and_offline_replay_are_deterministic(example, tmp_path):
    case, e = example
    text = json.dumps(e, ensure_ascii=False, sort_keys=True)
    saved = tmp_path / 'saved-test-envelope.json'
    saved.write_text(text)
    assert mechanics(tmp_path, e, case) == mechanics(tmp_path, json.loads(saved.read_text()), case)
    reordered = dict(reversed(list(e['subject'].items())))
    assert binding_digest(reordered) == e['sha256']


@pytest.mark.parametrize('trend', ['sideways', 'volatile'])
def test_unsupported_trend_cannot_become_an_absent_unknown(example, tmp_path, trend):
    case, e = example
    e['subject']['observation']['trend'] = trend
    with pytest.raises(BindingIntegrityError): rehash(e)


@pytest.mark.parametrize('kind', ['failed-tool', 'malformed-content'])
def test_rehashed_bad_capture_still_fails_semantics(example, tmp_path, kind):
    case, e = example
    evidence = e['subject']['evidence']
    path = tmp_path / evidence['manifest']['ref']
    manifest = json.loads(path.read_text())
    if kind == 'failed-tool':
        manifest['artifacts'][0]['toolResultStatus'] = 'error'
    else:
        # Keep valid UTF8 and a matching hash; missing/malformed identity content
        # must not turn a successful integrity check into valid observation data.
        import hashlib
        artifact = tmp_path / evidence['artifact']['ref']
        artifact.write_text('not a GMP observation\n' * 6)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        evidence['artifact']['sha256'] = digest
        manifest['artifacts'][0].update(sha256=digest, bytes=artifact.stat().st_size)
    path.write_text(json.dumps(manifest))
    import hashlib
    evidence['manifest']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    rehash(e)
    with pytest.raises(ValueError): mechanics(tmp_path, e, case)


@pytest.mark.parametrize('pin', ['qualification_decision', 'qualification_scope'])
def test_missing_declared_files_fail_not_authority(example, tmp_path, pin):
    case, e = example
    (tmp_path / e['subject'][pin]['ref']).unlink()
    with pytest.raises(BindingIntegrityError, match='missing or unreadable'):
        verify_binding_files(e, tmp_path)


def test_symlink_escape_and_file_fragment_scope(example, tmp_path):
    case, e = example
    ref = e['subject']['qualification_decision']['ref']
    path = tmp_path / ref
    outside = tmp_path.parent / (case['key'] + '-outside.md')
    outside.write_bytes(path.read_bytes())
    path.unlink(); path.symlink_to(outside)
    with pytest.raises(BindingIntegrityError, match='escapes repository'):
        verify_binding_files(e, tmp_path)
    path.unlink(); path.write_bytes(outside.read_bytes())
    e['subject']['qualification_decision']['ref'] += '#section'
    rehash(e)
    verify_binding_files(e, tmp_path)  # whole-file digest, never fragment bytes


def test_mechanics_positive_cannot_unlock_real_final(example, tmp_path, golden_input, config):
    case, e = example
    assert mechanics(tmp_path, e, case)['production_admission'] is False
    document = copy.deepcopy(golden_input)
    document['governance'].update(auditor_opinion='unqualified', going_concern_uncertainty=False,
                                 sebi_ed_action_active=False, rpt_pct_of_revenue_growth=1.0)
    document['financials']['contingent_liabilities_unquantified'] = False
    document['market']['gmp'].update(pct=float(case['pct']), as_of='2026-10-22T12:00:00Z',
                                    trend=case['trend'])
    outcome = evaluate(document, config, mode='final',
                       evaluation_datetime=datetime(2026,10,22,12,tzinfo=timezone.utc))
    result = build_evaluation_record_v1(outcome.record)['result']
    assert result['outcome_resolution']['state'] == 'NONTERMINAL_UNRESOLVED'
    assert result['outcome_resolution']['reason']['code'] == 'SOURCE_UNQUALIFIED'
    assert 'final_outcome' not in result


def test_file_pin_verification_reads_resolved_bytes_once_per_invocation(example, tmp_path, monkeypatch):
    case, e = example
    original = tmp_path / e['subject']['qualification_decision']['ref']
    scope = tmp_path / e['subject']['qualification_scope']['ref']
    scope.unlink(); scope.symlink_to(original)
    e['subject']['qualification_decision']['ref'] += '#scope'
    rehash(e)
    reads = []
    read_bytes = Path.read_bytes
    def track(path):
        reads.append(path)
        return read_bytes(path)
    monkeypatch.setattr(Path, 'read_bytes', track)
    verify_binding_files(e, tmp_path)
    assert reads and len(reads) == len(set(reads))
    reads.clear()
    verify_binding_files(e, tmp_path)
    assert reads and len(reads) == len(set(reads))  # no cross-call cache


def test_unlabelled_case_cannot_produce_a_mechanics_positive(tmp_path):
    case = dict(CASES[0])
    case.pop('label')
    with pytest.raises(ValueError, match='fixture label required'):
        materialize(tmp_path, case)
