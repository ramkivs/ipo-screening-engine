"""Boundary negatives/identity invariants, NOT qualified-source positives."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ipo_screening.connectors.adapters import GmpSignalAdapter
from ipo_screening.connectors.coordinator import ConnectorCoordinator
from ipo_screening.connectors.interfaces import ConflictingSourceError
from ipo_screening.gmp_evidence import GmpEvidenceError, load_rendered_capture

AT = datetime(2026, 10, 22, 18, tzinfo=timezone.utc)
BASE = {'gmp_pct': 63.57, 'as_of': '2026-10-22T16:07:00Z'}


def snap(payload):
    return GmpSignalAdapter().normalize(payload, reference_time=AT)


@pytest.mark.parametrize('change', [
    {},  # duplicate observations are not independent confirmation
    {'gmp_pct': 64},  # conflicting value at same stamp
    {'as_of': '2026-10-22T16:08:00Z'},  # revised timestamp
    {'gmp_pct': 64, 'as_of': '2026-10-22T16:08:00Z'},
    {'snapshot_id': 'ROW-2'},  # display ordinal is not selection authority
])
@pytest.mark.parametrize('reverse', [False, True])
def test_no_list_order_or_content_based_selection(change, reverse):
    first, second = snap(BASE), snap(dict(BASE, **change))
    values = [first, second]
    if reverse:
        values.reverse()
    with pytest.raises(ConflictingSourceError, match='explicitly selected'):
        ConnectorCoordinator().reconcile_snapshots(values, reference_time=AT)


def test_explicit_single_snapshot_reconstruction_is_deterministic_not_qualification():
    first = snap(BASE)
    # Dict key order is not a new observation hash/identity contract.
    second = snap(json.loads(json.dumps(dict(reversed(list(BASE.items()))))))
    assert first.raw_source_hash == second.raw_source_hash
    assert first.normalized_data == second.normalized_data
    result = ConnectorCoordinator().reconcile_snapshots([first], reference_time=AT)
    assert result == ConnectorCoordinator().reconcile_snapshots([second], reference_time=AT)
    assert first.verification == 'UNVERIFIED'
    assert first.snapshot_id == 'GMP-001'  # label, NOT stable publisher observation ID


def test_content_change_does_not_reuse_payload_integrity_digest():
    first = snap(BASE)
    for change in [{'gmp_pct': 64}, {'as_of': '2026-10-22T16:08:00Z'}]:
        changed = snap(dict(BASE, **change))
        assert changed.raw_source_hash != first.raw_source_hash
        # The shared default label MUST NOT be mistaken for content identity.
        assert changed.snapshot_id == first.snapshot_id


@pytest.mark.parametrize('status', [200, 404, 429, 500, 503])
@pytest.mark.parametrize('body', [
    '# Temporarily unavailable\nPlease try again',
    '<html><body>Error 503</body></html>',  # no required DOM/value fields
    '<html><div class="gmp"></div></html>',
    '',
])
def test_response_envelopes_are_not_gmp_payloads(status, body):
    # There is no HTTP/DOM GMP parser here. Transport envelopes cannot be
    # interpreted as a numeric reading by the supplied-payload normalizer.
    value = snap({'status_code': status, 'body': body})
    assert value.normalized_data['pct'] is None
    assert value.normalized_data['gmp_rupees'] is None
    assert value.normalized_data['as_of'] is None
    assert value.freshness.value == 'MISSING'


def manifest(tmp_path, text, status='success'):
    data = text.encode()
    (tmp_path / 'page.md').write_bytes(data)
    value = {'captureMethod': {'rawProviderResponseBytesCaptured': False}, 'artifacts': [{
        'id': 'page', 'file': 'page.md', 'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(), 'toolResultStatus': status,
    }]}
    path = tmp_path / 'capture-manifest.json'
    path.write_text(json.dumps(value))
    return path


@pytest.mark.parametrize('status', ['error', 'failed', 'timeout', 404, 500])
def test_recorded_retrieval_failure_is_distinct_from_a_missing_or_zero_reading(tmp_path, status):
    path = manifest(tmp_path, '# Error\n503\n₹0', status)
    with pytest.raises(GmpEvidenceError, match='capture failed: retrieval'):
        load_rendered_capture(path, 'page')


def test_tool_success_with_actual_pd_error_body_is_capture_failure(tmp_path):
    root = Path(__file__).resolve().parents[1]
    text = (root / 'evidence/gmp-observations/targeted-followup-20261022/source-captures/pd-unavailable.md').read_text()
    path = manifest(tmp_path, text)
    with pytest.raises(GmpEvidenceError, match='capture failed: temporary'):
        load_rendered_capture(path, 'page')
    with pytest.raises(GmpEvidenceError, match='capture failed: temporary'):
        load_rendered_capture(
            root / 'evidence/gmp-observations/targeted-followup-20261022/capture-manifest.json',
            'PD-T22',
        )


def test_withdrawal_notice_retains_evidence_and_is_not_numeric_zero(tmp_path):
    # Hypothetical explicit notice, NOT an actual publisher record/decision.
    text = '# Withdrawal notice\nObservation example withdrawn effective 2026-10-22T16:00Z'
    capture = load_rendered_capture(manifest(tmp_path, text), 'page')
    assert capture.integrity_verified and capture.text == text
    # No general notice parser or implicit withdrawal-to-zero conversion exists.
    value = snap({'body': text})
    assert value.normalized_data['pct'] is None
    assert value.normalized_data['gmp_rupees'] is None


@pytest.mark.parametrize('note', ['correction asserted without a supporting record',
                                 'withdrawal applicability unresolved',
                                 'conflict awaiting A1 adjudication'])
def test_prepended_revision_or_notice_cannot_select_a_reading(note):
    original = snap(BASE)
    revised = snap(dict(BASE, gmp_pct=64, notes=note))
    for values in ([revised, original, original], [original, revised, original]):
        with pytest.raises(ConflictingSourceError, match='explicitly selected'):
            ConnectorCoordinator().reconcile_snapshots(values, reference_time=AT)
    assert revised.raw_payload['notes'] == note  # preserve, do not adjudicate


@pytest.mark.parametrize('rows', [
    [{'row': 1, 'value': 445}, {'row': 2, 'value': 443}],
    [{'row': 2, 'value': 443}, {'row': 1, 'value': 445}],
    [{'row': 1, 'value': 450}, {'row': 2, 'value': 445}, {'row': 3, 'value': 443}],
])
def test_raw_history_rows_cannot_select_or_supply_a_gmp_observation(rows):
    # No IG history/DOM parser exists: history stays raw evidence, not implicit
    # observation selection. Reorder/prepend cannot replace the explicit value.
    selected = snap(dict(BASE, history=rows))
    assert selected.normalized_data == snap(BASE).normalized_data
    assert selected.raw_payload['history'] == rows
    unselected = snap({'history': rows})
    assert unselected.normalized_data['pct'] is None
