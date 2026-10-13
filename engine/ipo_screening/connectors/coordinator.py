"""Connector coordinator and external data manager.

Phase 5H: Live / External Data Connectors.

Coordinates external provider adapters, enforces precedence rules between
competing feeds (Official Exchange > Secondary Tracker), validates freshness,
detects conflicts, and formats normalized payloads directly consumable by
Phase 5G EnrichmentEngine.assemble(...).
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from ..canonical import ExtractionMethod, SourceRef, SourceType, Verification
from ..errors import Finding, SEVERITY_ERROR, SEVERITY_WARNING
from .adapters import (
    AnchorAllotmentAdapter,
    BaseConnectorAdapter,
    GmpSignalAdapter,
    MarketRegimeAdapter,
    OfficialSubscriptionAdapter,
    PeerMultipleAdapter,
)
from .interfaces import (
    ConflictingSourceError,
    ConnectorError,
    ExternalSnapshot,
    FreshnessStatus,
    SourceClass,
    StaleDataError,
    compute_payload_hash,
    sanitize_credentials,
)


class ConnectorCoordinator:
    """Orchestrates external data connectors and produces governed enrichment payloads."""

    def __init__(
        self,
        adapters: Optional[Sequence[BaseConnectorAdapter]] = None,
        strict_freshness: bool = False,
    ) -> None:
        self.adapters: Dict[SourceClass, List[BaseConnectorAdapter]] = {}
        self.strict_freshness = strict_freshness

        # Register default adapters if none supplied
        if adapters is None:
            adapters = [
                OfficialSubscriptionAdapter(),
                GmpSignalAdapter(),
                MarketRegimeAdapter(),
                PeerMultipleAdapter(),
                AnchorAllotmentAdapter(),
            ]

        for adapter in adapters:
            self.register_adapter(adapter)

    def register_adapter(self, adapter: BaseConnectorAdapter) -> None:
        """Register a provider adapter for a specific source class."""
        self.adapters.setdefault(adapter.source_class, []).append(adapter)

    def ingest_snapshot(
        self,
        raw_payload: Mapping[str, Any],
        source_class: SourceClass,
        provider_id: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> ExternalSnapshot:
        """Normalize a raw external payload using a matching registered adapter."""
        candidates = self.adapters.get(source_class, [])
        adapter: Optional[BaseConnectorAdapter] = None

        if provider_id:
            for a in candidates:
                if a.provider_id == provider_id:
                    adapter = a
                    break
        if adapter is None and candidates:
            adapter = candidates[0]

        if adapter is None:
            raise ConnectorError(f"No adapter registered for source class: {source_class}")

        snapshot = adapter.normalize(raw_payload, reference_time=reference_time)

        if self.strict_freshness and snapshot.freshness in (
            FreshnessStatus.STALE,
            FreshnessStatus.FUTURE,
            FreshnessStatus.MISSING,
        ):
            raise StaleDataError(
                f"External snapshot '{snapshot.snapshot_id}' from provider '{snapshot.provider_id}' "
                f"failed strict freshness check: {snapshot.freshness.value}",
                provider_id=snapshot.provider_id,
            )

        return snapshot

    def reconcile_snapshots(
        self,
        snapshots: Sequence[ExternalSnapshot],
        reference_time: Optional[datetime] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
        """Reconcile multiple external snapshots into (market_snapshot, peer_snapshot, sources).

        Enforces codified source precedence:
        1. Official Exchange subscription > Secondary aggregator subscription.
        2. Authoritative market regime > Stale market regime.
        3. Conflicting feeds with equal authority -> ConflictingSourceError (fail closed).
        4. Immutability guaranteed.
        """
        sources: List[Dict[str, Any]] = []
        market_payload: Dict[str, Any] = {}
        peer_payload: Dict[str, Any] = {}

        # Group snapshots by source class
        by_class: Dict[SourceClass, List[ExternalSnapshot]] = {}
        for s in snapshots:
            by_class.setdefault(s.source_class, []).append(s)
            sources.append(s.to_source_ref())

        # ------------------------------------------------------------------
        # 1. Reconcile Subscription (Official > Secondary)
        # ------------------------------------------------------------------
        sub_snaps = by_class.get(SourceClass.OFFICIAL_EXCHANGE, [])
        sec_snaps = by_class.get(SourceClass.SECONDARY_TRACKER, [])

        chosen_sub: Optional[ExternalSnapshot] = None
        if len(sub_snaps) > 1:
            # Check for conflicting official feeds
            first = sub_snaps[0].normalized_data
            for other in sub_snaps[1:]:
                other_norm = other.normalized_data
                for k in ("qib_x", "nii_x", "retail_x", "overall_x"):
                    v1, v2 = first.get(k), other_norm.get(k)
                    if v1 is not None and v2 is not None and abs(v1 - v2) > 0.001:
                        raise ConflictingSourceError(
                            f"Conflicting official subscription feeds for '{k}': {v1} vs {v2}",
                            provider_id=other.provider_id,
                        )
            chosen_sub = sub_snaps[0]
        elif len(sub_snaps) == 1:
            chosen_sub = sub_snaps[0]

        # Subscription block
        if chosen_sub:
            data = chosen_sub.normalized_data
            market_payload["subscription"] = {
                "qib_x": data.get("qib_x"),
                "nii_x": data.get("nii_x"),
                "retail_x": data.get("retail_x"),
                "overall_x": data.get("overall_x"),
                "as_of": data.get("as_of"),
                "source_id": chosen_sub.to_source_ref()["source_id"],
            }
            # Also populate flat keys for legacy compatibility
            market_payload["qib_subscription"] = data.get("qib_x")
            market_payload["nii_subscription"] = data.get("nii_x")
            market_payload["retail_subscription"] = data.get("retail_x")
            market_payload["overall_subscription"] = data.get("overall_x")

        # ------------------------------------------------------------------
        # 2. Reconcile GMP (Secondary signal, never statutory)
        # ------------------------------------------------------------------
        if sec_snaps:
            gmp_snap = sec_snaps[0]
            data = gmp_snap.normalized_data
            market_payload["gmp"] = {
                "pct": data.get("pct"),
                "trend": data.get("trend"),
                "as_of": data.get("as_of"),
                "source_id": gmp_snap.to_source_ref()["source_id"],
            }
            market_payload["gmp_rupees"] = data.get("gmp_rupees")
            market_payload["gmp_trend"] = data.get("trend")

        # ------------------------------------------------------------------
        # 3. Reconcile Market Regime
        # ------------------------------------------------------------------
        regime_snaps = by_class.get(SourceClass.MARKET_REGIME, [])
        if regime_snaps:
            reg_snap = regime_snaps[0]
            data = reg_snap.normalized_data
            market_payload["regime"] = {
                "nifty_trend": data.get("nifty_trend"),
                "last_ipo_listing_gains_pct": data.get("last_ipo_listing_gains_pct", []),
                "as_of": data.get("as_of"),
                "source_id": reg_snap.to_source_ref()["source_id"],
            }
            market_payload["nifty_trend"] = data.get("nifty_trend")
            market_payload["listing_gains"] = data.get("last_ipo_listing_gains_pct", [])

        # ------------------------------------------------------------------
        # 4. Reconcile Anchor Book
        # ------------------------------------------------------------------
        anchor_snaps = by_class.get(SourceClass.ANCHOR_BOOK, [])
        if anchor_snaps:
            anc_snap = anchor_snaps[0]
            data = anc_snap.normalized_data
            market_payload["anchor"] = {
                "quality": data.get("quality"),
                "amount": data.get("amount"),
                "as_of": data.get("as_of"),
                "source_id": anc_snap.to_source_ref()["source_id"],
            }
            market_payload["anchor_names"] = data.get("anchor_names", [])
            market_payload["anchor_total_shares"] = data.get("anchor_total_shares")
            market_payload["anchor_total_amount"] = data.get("amount")
            market_payload["anchor_lockin_verified"] = data.get("anchor_lockin_verified")
            market_payload["anchor_quality"] = data.get("quality")

        # ------------------------------------------------------------------
        # 5. Reconcile Peer Valuations
        # ------------------------------------------------------------------
        peer_snaps = by_class.get(SourceClass.PEER_MULTIPLE, [])
        if peer_snaps:
            peer_snap = peer_snaps[0]
            data = peer_snap.normalized_data
            peer_payload["peers"] = data.get("peers", [])
            peer_payload["recent_sector_ipos"] = data.get("recent_sector_ipos", [])
            peer_payload["as_of"] = data.get("as_of")
            peer_payload["source_id"] = peer_snap.to_source_ref()["source_id"]

        return market_payload, peer_payload, sources


__all__ = [
    "ConnectorCoordinator",
    "OfficialSubscriptionAdapter",
    "GmpSignalAdapter",
    "MarketRegimeAdapter",
    "PeerMultipleAdapter",
    "AnchorAllotmentAdapter",
]
