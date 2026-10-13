"""Focused regression coverage for unresolved snapshot and FINAL-gate fixes.

Connector payloads used here are repository fixtures. No verified GMP fixture
is created: the market-signal fixture remains explicitly UNVERIFIED.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import EVAL_AT, metric, run
from ipo_screening.connectors import ConnectorCoordinator, SourceClass
from ipo_screening.enrichment_engine import EnrichmentEngine
from ipo_screening.errors import ValidationError
from ipo_screening.pipeline import evaluate

REPO_ROOT = Path(__file__).resolve().parents[1]
CONNECTOR_FIXTURES = REPO_ROOT / "fixtures" / "connectors"
GOLDEN_INPUT = REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _error_codes(exc: ValidationError) -> set[str]:
    return {finding.code for finding in exc.findings if finding.severity == "ERROR"}


@pytest.mark.parametrize(
    ("as_of", "gains", "reason_fragment"),
    [
        (
            "2026-10-04T19:26:01Z",
            [12.5, 24.0, -3.2, 45.0],
            "4 listing-gain slots",
        ),
        (
            "2026-10-04T19:26:01Z",
            [12.5, 24.0, None, 45.0, 8.1],
            "missing or invalid",
        ),
        (
            "2026-10-03T00:00:00Z",
            [12.5, 24.0, -3.2, 45.0, 8.1],
            "regime block is not fresh",
        ),
    ],
)
def test_market_regime_variant_stays_unknown_without_five_fresh_observations(
    config, make_input, as_of, gains, reason_fragment
):
    outcome = run(
        make_input(
            **{
                "market.regime.as_of": as_of,
                "market.regime.last_ipo_listing_gains_pct": gains,
            }
        ),
        config,
    )

    variant = metric(outcome, "market_regime_variant")
    assert variant.is_unknown
    assert reason_fragment in variant.reason


def test_market_regime_classifies_the_complete_fresh_lookback(config, make_input):
    # The five values are taken from the repository's market-regime connector fixture.
    outcome = run(
        make_input(
            **{
                "market.regime.as_of": "2026-10-04T19:26:01Z",
                "market.regime.last_ipo_listing_gains_pct": [12.5, 24.0, -3.2, 45.0, 8.1],
            }
        ),
        config,
    )

    variant = metric(outcome, "market_regime_variant")
    assert variant.is_value
    assert variant.value == "normal"


def test_preliminary_evaluation_does_not_apply_the_final_gmp_gate(config, make_input):
    # The canonical baseline carries an ordinary unverified GMP signal, but
    # preliminary scoring remains possible and does not claim verification.
    document = make_input()
    outcome = evaluate(document, config, mode="preliminary", evaluation_datetime=EVAL_AT)
    assert outcome.record.evaluation_mode == "PRELIMINARY"


def test_final_mode_fails_closed_when_the_gmp_snapshot_is_missing(config, make_input):
    document = make_input(**{"market.gmp": {}})

    with pytest.raises(ValidationError) as exc_info:
        evaluate(document, config, mode="final", evaluation_datetime=EVAL_AT)

    assert exc_info.value.gate == "final_gmp"
    assert _error_codes(exc_info.value) == {"GMP_SNAPSHOT_MISSING"}


def test_connector_gmp_remains_unverified_and_cannot_pass_the_final_gate(config):
    """The fixture's non-statutory tracker signal is retained, but is not verified."""
    base_input = _load_json(GOLDEN_INPUT)
    raw_gmp = _load_json(CONNECTOR_FIXTURES / "02_valid_gmp.json")
    coordinator = ConnectorCoordinator()
    gmp_snapshot = coordinator.ingest_snapshot(
        raw_gmp,
        SourceClass.SECONDARY_TRACKER,
        reference_time=EVAL_AT,
    )
    market_payload, _, _ = coordinator.reconcile_snapshots(
        [gmp_snapshot],
        reference_time=EVAL_AT,
    )
    enrichment_result = EnrichmentEngine.assemble(
        base_input=base_input,
        market_snapshot=market_payload,
        mode="preliminary",
    )

    gmp = enrichment_result.canonical_input["market"]["gmp"]
    assert gmp["verification"] == "UNVERIFIED"
    assert gmp["is_statutory"] is False
    assert gmp["raw_payload"]["snapshot_id"] == raw_gmp["snapshot_id"]

    with pytest.raises(ValidationError) as exc_info:
        evaluate(enrichment_result, config, mode="final", evaluation_datetime=EVAL_AT)

    assert exc_info.value.gate == "final_gmp"
    codes = _error_codes(exc_info.value)
    assert "GMP_SNAPSHOT_UNVERIFIED" in codes
    # A9 is scoped to GMP; ordinary subscription evidence is not subjected to
    # this gate and no subscription winner/aggregate is requested here.
    assert not any("SUBSCRIPTION" in code for code in codes)
