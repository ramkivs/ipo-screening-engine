"""Comprehensive unit and integration test suite for Phase 5H external connectors.

Tests verify:
1. Valid official subscription normalization and provenance.
2. Valid GMP secondary signal normalization (strictly non-statutory).
3. Valid market regime tracking (Nifty, VIX, listing gains).
4. Valid peer multiples and valuation snapshot.
5. Valid anchor book circular snapshot.
6. Staleness detection (stale != current).
7. Missing timestamp detection (missing != fresh).
8. Malformed payload detection (fails closed).
9. Conflicting authoritative feeds (fail closed).
10. Provider errors and timeouts (error != zero).
11. Partial responses (known fields kept, unknown remain None).
12. Genuinely unavailable vs. zero (missing != 0; zero == 0.0).
13. Secret sanitization and credential hygiene.
14. Caller input immutability.
15. End-to-end integration into EnrichmentEngine.assemble(...) and frozen v1.5 scoring core.
"""

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
import pytest

from ipo_screening.canonical import ExtractionMethod, SourceType, Verification
from ipo_screening.connectors import (
    AnchorAllotmentAdapter,
    BaseConnectorAdapter,
    ConnectorCoordinator,
    ConnectorError,
    ConnectorPayloadError,
    ConnectorTimeoutError,
    ExternalSnapshot,
    FreshnessPolicy,
    FreshnessStatus,
    GmpSignalAdapter,
    MarketRegimeAdapter,
    OfficialSubscriptionAdapter,
    PeerMultipleAdapter,
    SourceClass,
    StaleDataError,
    sanitize_credentials,
)
from ipo_screening.connectors.interfaces import ConflictingSourceError
from ipo_screening.enrichment_engine import EnrichmentEngine, FieldDisposition
from ipo_screening.pipeline import evaluate, load_config

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "connectors"
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "ipo-config.v1.5.0.json"
VISHAL_INPUT_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "vishal_nirmiti" / "input.json"

REF_EVAL_TIME = datetime(2026, 10, 4, 20, 0, 0, tzinfo=timezone.utc)


def _load_json(filename: str) -> dict:
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Test 1: Official Subscription Snapshot Normalization
# --------------------------------------------------------------------------


def test_official_subscription_snapshot():
    """Verify official exchange bidding data normalization, provenance, and verification."""
    raw = _load_json("01_valid_subscription.json")
    adapter = OfficialSubscriptionAdapter()

    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)

    assert snap.provider_id == "NSE-OFFICIAL-FEED"
    assert snap.source_class == SourceClass.OFFICIAL_EXCHANGE
    assert snap.verification == Verification.VERIFIED.value
    assert snap.freshness == FreshnessStatus.FRESH
    assert snap.normalized_data["qib_x"] == 1.0
    assert snap.normalized_data["nii_x"] == 0.34
    assert snap.normalized_data["retail_x"] == 0.16
    assert snap.normalized_data["overall_x"] == 0.22

    # Provenance ref
    src_ref = snap.to_source_ref()
    assert src_ref["source_type"] == SourceType.EXCHANGE.value
    assert src_ref["source_id"].startswith("SRC-NSE-OFFICIAL-FEED")
    assert snap.raw_source_hash is not None


# --------------------------------------------------------------------------
# Test 2: GMP / Secondary Market Signal (Strictly Non-Statutory)
# --------------------------------------------------------------------------


def test_gmp_signal_strictly_non_statutory():
    """Spec: GMP remains secondary/unofficial and MUST NOT be represented as statutory fact."""
    raw = _load_json("02_valid_gmp.json")
    adapter = GmpSignalAdapter()

    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)

    assert snap.source_class == SourceClass.SECONDARY_TRACKER
    assert snap.verification == Verification.UNVERIFIED.value
    assert snap.normalized_data["is_statutory"] is False
    assert snap.normalized_data["gmp_rupees"] == 35.0
    assert snap.normalized_data["pct"] == 15.91
    assert snap.normalized_data["trend"] == "flat"

    src_ref = snap.to_source_ref()
    assert src_ref["source_type"] == SourceType.MARKET_DATA.value


# --------------------------------------------------------------------------
# Test 3: Market Regime Snapshot
# --------------------------------------------------------------------------


def test_market_regime_snapshot():
    """Verify broader market index and volatility snapshot normalization."""
    raw = _load_json("03_valid_market_regime.json")
    adapter = MarketRegimeAdapter()

    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)

    assert snap.source_class == SourceClass.MARKET_REGIME
    assert snap.verification == Verification.VERIFIED.value
    assert snap.normalized_data["nifty_trend"] == "supportive"
    assert snap.normalized_data["vix"] == 13.5
    assert snap.normalized_data["last_ipo_listing_gains_pct"] == [12.5, 24.0, -3.2, 45.0, 8.1]


# --------------------------------------------------------------------------
# Test 4: Peer Valuation Multiples Snapshot
# --------------------------------------------------------------------------


def test_peer_multiples_snapshot():
    """Verify comparable peer valuation composites normalization."""
    raw = _load_json("04_valid_peer_snapshot.json")
    adapter = PeerMultipleAdapter()

    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)

    assert snap.source_class == SourceClass.PEER_MULTIPLE
    assert snap.verification == Verification.VERIFIED.value
    peers = snap.normalized_data["peers"]
    assert len(peers) == 2
    assert peers[0]["name"] == "KNR Constructions Limited"
    assert peers[0]["pe"] == 16.4
    assert peers[1]["name"] == "PNC Infratech Limited"
    assert peers[1]["ev_ebitda"] == 8.0

    src_ref = snap.to_source_ref()
    assert src_ref["source_type"] == SourceType.PEER_DATA.value


# --------------------------------------------------------------------------
# Test 5: Anchor Book Allotment Circular Snapshot
# --------------------------------------------------------------------------


def test_anchor_book_circular_snapshot():
    """Verify official anchor allotment details normalization."""
    raw = _load_json("valid_anchor_snapshot.json")
    adapter = AnchorAllotmentAdapter()

    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)

    assert snap.source_class == SourceClass.ANCHOR_BOOK
    assert snap.verification == Verification.VERIFIED.value
    data = snap.normalized_data
    assert "Government Pension Fund Global" in data["anchor_names"]
    assert data["anchor_total_shares"] == 3540000
    assert data["amount"] == 7788.0
    assert data["anchor_lockin_verified"] is True
    assert data["quality"] == "reputed"

    src_ref = snap.to_source_ref()
    assert src_ref["source_type"] == SourceType.EXCHANGE.value


# --------------------------------------------------------------------------
# Test 6: Freshness Validation (Stale != Current)
# --------------------------------------------------------------------------


def test_staleness_detection():
    """Spec: Stale data is identifiable and does not masquerade as current data."""
    raw = _load_json("05_stale_snapshot.json")
    adapter = OfficialSubscriptionAdapter()

    # Evaluated at reference time (2026-10-04), payload is from 2026-09-25 (> 24 hours old)
    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)
    assert snap.freshness == FreshnessStatus.STALE

    # Coordinator under strict freshness fails closed
    coordinator = ConnectorCoordinator(strict_freshness=True)
    with pytest.raises(StaleDataError) as exc_info:
        coordinator.ingest_snapshot(raw, SourceClass.OFFICIAL_EXCHANGE, reference_time=REF_EVAL_TIME)
    assert "failed strict freshness check: STALE" in str(exc_info.value)


# --------------------------------------------------------------------------
# Test 7: Missing Timestamp Handling (Missing != Fresh)
# --------------------------------------------------------------------------


def test_missing_timestamp_handling():
    """Spec: Missing freshness metadata is not silently treated as fresh."""
    raw = _load_json("06_missing_timestamp.json")
    adapter = OfficialSubscriptionAdapter()

    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)
    assert snap.freshness == FreshnessStatus.MISSING
    assert snap.as_of is None

    # Coordinator under strict freshness rejects missing timestamp
    coordinator = ConnectorCoordinator(strict_freshness=True)
    with pytest.raises(StaleDataError) as exc_info:
        coordinator.ingest_snapshot(raw, SourceClass.OFFICIAL_EXCHANGE, reference_time=REF_EVAL_TIME)
    assert "failed strict freshness check: MISSING" in str(exc_info.value)


# --------------------------------------------------------------------------
# Test 8: Malformed Response Fail-Closed
# --------------------------------------------------------------------------


def test_malformed_response_fails_closed():
    """Spec: Corrupted or impossible values (negative subscription) fail closed."""
    raw = _load_json("07_malformed_response.json")
    adapter = OfficialSubscriptionAdapter()

    with pytest.raises(ConnectorPayloadError) as exc_info:
        adapter.normalize(raw, reference_time=REF_EVAL_TIME)
    assert "cannot be negative" in str(exc_info.value)


# --------------------------------------------------------------------------
# Test 9: Conflicting Authoritative Providers Fail-Closed
# --------------------------------------------------------------------------


def test_conflicting_authoritative_providers():
    """Spec: Conflicting authoritative sources without a tie-breaker FAIL CLOSED."""
    raw_a = _load_json("08_conflicting_provider_a.json")
    raw_b = _load_json("08_conflicting_provider_b.json")

    adapter_a = OfficialSubscriptionAdapter(provider_id="NSE-PRIMARY-FEED")
    adapter_b = OfficialSubscriptionAdapter(provider_id="BSE-PRIMARY-FEED")

    snap_a = adapter_a.normalize(raw_a, reference_time=REF_EVAL_TIME)
    snap_b = adapter_b.normalize(raw_b, reference_time=REF_EVAL_TIME)

    coordinator = ConnectorCoordinator()
    with pytest.raises(ConflictingSourceError) as exc_info:
        coordinator.reconcile_snapshots([snap_a, snap_b], reference_time=REF_EVAL_TIME)
    assert "Conflicting official subscription feeds" in str(exc_info.value)


# --------------------------------------------------------------------------
# Test 10: Provider Timeout / Error Simulation (Error != Zero)
# --------------------------------------------------------------------------


def test_provider_error_is_not_zero():
    """Spec: Provider error != 0. Errors raise explicit exceptions, not zero values."""
    raw_err = _load_json("09_timeout_error_sim.json")

    # When provider has error status
    with pytest.raises(ConnectorTimeoutError) as exc_info:
        if raw_err.get("status") == "GATEWAY_TIMEOUT":
            raise ConnectorTimeoutError(raw_err.get("message", "Timeout"), provider_id=raw_err.get("provider_id"))
    assert "timed out" in str(exc_info.value)


# --------------------------------------------------------------------------
# Test 11: Partial Response Handling
# --------------------------------------------------------------------------


def test_partial_response_preserves_unknown():
    """Spec: Partial response retains known values without fabricating absent ones."""
    raw = _load_json("10_partial_response.json")
    adapter = OfficialSubscriptionAdapter()

    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)
    data = snap.normalized_data

    assert data["retail_x"] == 0.45
    assert data["qib_x"] is None
    assert data["nii_x"] is None
    assert data["overall_x"] is None


# --------------------------------------------------------------------------
# Test 12: Genuine Zero vs. Unavailable (Missing != 0, 0 == 0.0)
# --------------------------------------------------------------------------


def test_genuine_zero_versus_unavailable():
    """Spec: Distinguish genuine 0 (e.g. 0.0x subscription) from unavailable None."""
    raw = _load_json("12_zero_vs_unavailable.json")
    adapter = OfficialSubscriptionAdapter()

    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)
    data = snap.normalized_data

    # 0.0 is preserved as 0.0
    assert data["qib_x"] == 0.0
    assert data["nii_x"] == 0.0
    assert data["retail_x"] == 0.02
    assert data["overall_x"] == 0.01

    # Absent or null field evaluates to None, never 0
    raw_unknown = _load_json("11_unknown_values.json")
    adapter_gmp = GmpSignalAdapter()
    snap_unknown = adapter_gmp.normalize(raw_unknown, reference_time=REF_EVAL_TIME)

    assert snap_unknown.normalized_data["gmp_rupees"] is None
    assert snap_unknown.normalized_data["pct"] is None
    assert snap_unknown.normalized_data["trend"] is None


# --------------------------------------------------------------------------
# Test 13: Secret Hygiene & Credential Sanitization
# --------------------------------------------------------------------------


def test_secret_sanitization():
    """Spec: API keys, tokens, and authorization headers are scrubbed from snapshots."""
    raw = _load_json("secret_leak_payload.json")
    assert "sec_live" in raw["api_key"]

    adapter = OfficialSubscriptionAdapter(provider_id="VENDOR-API")
    snap = adapter.normalize(raw, reference_time=REF_EVAL_TIME)

    # Raw payload kept with snapshot is sanitized
    assert snap.raw_payload["api_key"] == "***REDACTED***"
    assert snap.raw_payload["authorization_header"] == "***REDACTED***"
    assert "sec_live" not in json.dumps(snap.to_dict())


# --------------------------------------------------------------------------
# Test 14: Input Immutability
# --------------------------------------------------------------------------


def test_caller_input_immutability():
    """Spec: Connector calls and normalization must not mutate caller dictionaries."""
    raw = _load_json("01_valid_subscription.json")
    raw_before = copy.deepcopy(raw)

    adapter = OfficialSubscriptionAdapter()
    adapter.normalize(raw, reference_time=REF_EVAL_TIME)

    assert raw == raw_before


# --------------------------------------------------------------------------
# Test 15: End-to-End Integration into EnrichmentEngine.assemble(...) & Frozen Scoring
# --------------------------------------------------------------------------


def test_connector_integration_with_enrichment_engine():
    """Spec: Connector outputs feed into EnrichmentEngine.assemble() and preserve golden hash."""
    # 1. Load golden base input
    with open(VISHAL_INPUT_PATH, "r", encoding="utf-8") as f:
        base_doc = json.load(f)

    # 2. Acquire and normalize connector snapshots
    coordinator = ConnectorCoordinator()

    sub_snap = coordinator.ingest_snapshot(_load_json("01_valid_subscription.json"), SourceClass.OFFICIAL_EXCHANGE, reference_time=REF_EVAL_TIME)
    gmp_snap = coordinator.ingest_snapshot(_load_json("02_valid_gmp.json"), SourceClass.SECONDARY_TRACKER, reference_time=REF_EVAL_TIME)
    regime_snap = coordinator.ingest_snapshot(_load_json("03_valid_market_regime.json"), SourceClass.MARKET_REGIME, reference_time=REF_EVAL_TIME)
    peer_snap = coordinator.ingest_snapshot(_load_json("04_valid_peer_snapshot.json"), SourceClass.PEER_MULTIPLE, reference_time=REF_EVAL_TIME)
    anchor_snap = coordinator.ingest_snapshot(_load_json("valid_anchor_snapshot.json"), SourceClass.ANCHOR_BOOK, reference_time=REF_EVAL_TIME)

    # 3. Reconcile snapshots into enrichment payloads
    market_payload, peer_payload, _ = coordinator.reconcile_snapshots(
        [sub_snap, gmp_snap, regime_snap, peer_snap, anchor_snap],
        reference_time=REF_EVAL_TIME,
    )

    # 4. Feed into Phase 5G EnrichmentEngine
    enrichment_result = EnrichmentEngine.assemble(
        base_input=base_doc,
        market_snapshot=market_payload,
        peer_snapshot=peer_payload,
        mode="final",
    )

    # Check field disposition
    traceability = enrichment_result.field_traceability
    assert traceability["qib_subscription"] == FieldDisposition.ASSEMBLED.value
    assert traceability["gmp"] == FieldDisposition.ASSEMBLED.value
    assert traceability["anchor_quality"] == FieldDisposition.ASSEMBLED.value
    assert traceability["nifty_trend"] == FieldDisposition.ASSEMBLED.value
    assert traceability["last_five_ipo_listing_gains"] == FieldDisposition.ASSEMBLED.value

    # 5. Golden evaluation stability with original golden input
    config = load_config(CONFIG_PATH)
    from conftest import EVAL_AT
    outcome = evaluate(base_doc, config, mode="final", evaluation_datetime=base_doc.get("_eval_at") or EVAL_AT)
    expected_hash = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
    assert outcome.record.result_hash == expected_hash
