"""A28.1 representation/integrity tooling, NOT a qualification authority or gate.

No engine pipeline consumes this optional sidecar yet. A structurally valid,
correctly hashed binding can still reference fabricated or unauthorized evidence.
Only a future evidence-backed qualification verifier may establish admission.
"""
from __future__ import annotations

import json
import unicodedata
from datetime import datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .hashing import sha256_of


class BindingIntegrityError(ValueError):
    """Invalid representation or digest; never an approval disposition."""


@lru_cache(maxsize=1)
def _schema() -> dict:
    path = Path(__file__).resolve().parents[2] / 'schema/gmp-qualification-binding.v1.schema.json'
    schema = json.loads(path.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    return schema


def _nfc(value: Any) -> None:
    if isinstance(value, str) and value != unicodedata.normalize('NFC', value):
        raise BindingIntegrityError('subject strings must already be NFC')
    if isinstance(value, dict):
        for key, item in value.items():
            _nfc(key)
            _nfc(item)
    if isinstance(value, list):
        for item in value:
            _nfc(item)


def _pins(rows: list) -> None:
    names = [item['ref'] for item in rows]
    if names != sorted(set(names)):
        raise BindingIntegrityError('pin arrays must be sorted and unique by ref')


def _instant(value: str) -> datetime:
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError as exc:
        raise BindingIntegrityError('invalid canonical UTC instant') from exc


def binding_digest(subject: Mapping[str, Any]) -> str:
    """Digest a well-formed A28.1 subject; DOES NOT verify authority/source bytes.

    Temporal relationships and declared trend consistency are checked, but none
    of these declarations is evidence that the referenced source was qualified.
    """
    envelope = {'subject': subject, 'sha256': '0' * 64}
    errors = list(Draft202012Validator(_schema()).iter_errors(envelope))
    if errors:
        raise BindingIntegrityError(errors[0].message)
    _nfc(subject)
    _pins(subject['qualification_evidence'])
    _pins(subject['selection']['adjudications'])
    _pins(subject['context']['policy_refs'])
    # One ref must always pin the same bytes throughout the whole subject.
    pins: dict[str, str] = {}
    def collect(value: Any) -> None:
        if isinstance(value, dict):
            if set(value) == {'ref', 'sha256'}:
                file_ref = value['ref'].split('#', 1)[0]
                previous = pins.setdefault(file_ref, value['sha256'])
                if previous != value['sha256']:
                    raise BindingIntegrityError('contradictory digest pins for one ref')
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
    collect(subject)
    observation, evidence = subject['observation'], subject['evidence']
    pct = Decimal(observation['pct'])
    if pct == 0 or not Decimal('-1000') <= pct <= Decimal('10000'):
        raise BindingIntegrityError('zero or out-of-schema percentage')
    as_of = _instant(observation['as_of'])
    start, end = _instant(evidence['capture_start']), _instant(evidence['capture_end'])
    cutoff = _instant(subject['context']['evaluation_at'])
    if not (start <= end <= cutoff and as_of <= end and timedelta(0) <= cutoff-as_of <= timedelta(hours=24)):
        raise BindingIntegrityError('ineligible capture window or publisher timestamp')
    trend_quote = evidence['trend_quote']
    if observation['trend'] is None:
        if trend_quote is not None:
            raise BindingIntegrityError('absent trend cannot hide an asserted label')
    else:
        from .connectors.adapters import _map_gmp_trend_label
        if trend_quote is None or _map_gmp_trend_label(trend_quote['quote']) != observation['trend']:
            raise BindingIntegrityError('asserted trend is not an accepted matching publisher label')
    return sha256_of(subject)


def verify_binding_integrity(envelope: Mapping[str, Any]) -> None:
    """Verify representation/digest ONLY; returns no qualification/Final signal."""
    errors = list(Draft202012Validator(_schema()).iter_errors(envelope))
    if errors:
        raise BindingIntegrityError(errors[0].message)
    if binding_digest(envelope['subject']) != envelope['sha256']:
        raise BindingIntegrityError('qualification binding digest mismatch')


def parse_binding(text: str) -> dict:
    """Strict sidecar JSON parsing + integrity only, never source authorization."""
    from .json_strict import loads_strict_json
    try:
        envelope = loads_strict_json(text)
    except ValueError as exc:
        raise BindingIntegrityError(str(exc)) from exc
    verify_binding_integrity(envelope)
    return envelope
