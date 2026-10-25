"""Retained-byte inventory regression, NOT source qualification or admission.

MarketLive's eight artifacts already have coverage in test_gmp_evidence_linkage.
These tests cover the other two packages, the parallel transcription and the
explicit retained-chunk concatenation; none supplies missing R7/R8 history.
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / 'evidence/gmp-observations'


@pytest.mark.parametrize('package', ['investorgain-tonbo-20261015', 'papsdigital-tonbo-20261015'])
def test_other_retained_packages_match_their_declared_bytes(package):
    root = PACKAGES / package
    manifest = json.loads((root / 'capture-manifest.json').read_text(encoding='utf-8'))
    assert len(manifest['artifacts']) == 6
    for artifact in manifest['artifacts']:
        data = (root / artifact['file']).read_bytes()
        assert len(data) == artifact['bytes'], artifact['id']
        assert hashlib.sha256(data).hexdigest().lower() == artifact['sha256'].lower(), artifact['id']


def test_parallel_investorgain_transcription_matches_its_own_checksum():
    sums = ROOT / 'evidence/market-observations/investorgain-tonbo-20261015/SHA256SUMS'
    digest, relative = sums.read_text(encoding='utf-8').strip().split(maxsplit=1)
    data = (ROOT / relative).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest.lower()
    # It remains a structured rendered transcription, not a second source.
    assert b'not a byte-for-byte export' in data


def test_investorgain_join_hashes_retained_redacted_chunks_not_provider_bytes():
    root = PACKAGES / 'investorgain-tonbo-20261015'
    manifest = json.loads((root / 'capture-manifest.json').read_text(encoding='utf-8'))
    artifacts = {item['id']: item for item in manifest['artifacts']}
    data = b''.join((root / artifacts[key]['file']).read_bytes() for key in [
        'ig-tonbo-2369-gmp-chunk-0', 'ig-tonbo-2369-gmp-chunk-1',
    ])
    declared = manifest['derivedChecks']['reassembledTonboPage']
    assert len(data) == declared['bytes'] == 10944
    assert hashlib.sha256(data).hexdigest().lower() == declared['sha256'].lower()
    assert 'not provider response bytes' in declared['hashScope']
