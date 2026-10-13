"""Connector coordinator and external data manager.

Phase 5H: Live / External Data Connectors.

Coordinates external provider adapters, validates freshness, preserves each
source observation when no governed source-selection rule is available, and
formats normalized payloads directly consumable by
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
            FreshnessStatus.UNRESOLVED,
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
        """Reconcile snapshots without inventing unsupported source winners.

        Single snapshots retain compatibility aliases. Distinct subscription,
        GMP, regime, anchor or peer universes remain separate observations until
        an applicable source-selection rule exists. Inputs are never mutated.
        """
        sources: List[Dict[str, Any]] = []
        market_payload: Dict[str, Any] = {}
        peer_payload: Dict[str, Any] = {}

        # Group snapshots by source class, retaining the received order. No
        # exchange/provider precedence is inferred from registration order.
        by_class: Dict[SourceClass, List[ExternalSnapshot]] = {}
        for snapshot in snapshots:
            by_class.setdefault(snapshot.source_class, []).append(snapshot)
            sources.append(snapshot.to_source_ref())

        def snapshot_record(snapshot: ExternalSnapshot) -> Dict[str, Any]:
            """Carry a source observation without erasing source-native fields."""
            source_ref = snapshot.to_source_ref()
            return {
                "snapshot_id": snapshot.snapshot_id,
                "provider_id": snapshot.provider_id,
                "source_class": snapshot.source_class.value,
                "source_id": source_ref["source_id"],
                "source_timestamp": snapshot.as_of,
                "as_of": snapshot.as_of,
                "retrieval_timestamp": snapshot.retrieval_timestamp,
                "content_hash": snapshot.raw_source_hash,
                "freshness": snapshot.freshness.value,
                "verification": snapshot.verification,
                "extraction_method": snapshot.extraction_method,
                "normalized_data": copy.deepcopy(dict(snapshot.normalized_data)),
                "raw_payload": copy.deepcopy(dict(snapshot.raw_payload or {})),
            }

        def block_from_single(snapshot: ExternalSnapshot, value_keys: Sequence[str]) -> Dict[str, Any]:
            source_ref = snapshot.to_source_ref()
            data = snapshot.normalized_data
            block = {key: copy.deepcopy(data.get(key)) for key in value_keys}
            block.update(
                {
                    "as_of": snapshot.as_of,
                    "source_timestamp": snapshot.as_of,
                    "retrieval_timestamp": snapshot.retrieval_timestamp,
                    "source_id": source_ref["source_id"],
                    "snapshot_id": snapshot.snapshot_id,
                    "provider_id": snapshot.provider_id,
                    "content_hash": snapshot.raw_source_hash,
                    "freshness": snapshot.freshness.value,
                    "verification": snapshot.verification,
                    "extraction_method": snapshot.extraction_method,
                    "raw_payload": copy.deepcopy(dict(snapshot.raw_payload or {})),
                    "observations": [snapshot_record(snapshot)],
                }
            )
            return block

        market_sources: List[Dict[str, Any]] = []
        for source_class in (
            SourceClass.OFFICIAL_EXCHANGE,
            SourceClass.SECONDARY_TRACKER,
            SourceClass.MARKET_REGIME,
            SourceClass.ANCHOR_BOOK,
        ):
            market_sources.extend(
                snapshot.to_source_ref() for snapshot in by_class.get(source_class, [])
            )
        if market_sources:
            market_payload["_sources"] = market_sources

        # ------------------------------------------------------------------
        # 1. Subscription: preserve each NSE/BSE/other exchange observation.
        # ------------------------------------------------------------------
        subscription_snaps = by_class.get(SourceClass.OFFICIAL_EXCHANGE, [])
        if subscription_snaps:
            observations = [snapshot_record(snapshot) for snapshot in subscription_snaps]
            if len(subscription_snaps) == 1:
                chosen = subscription_snaps[0]
                data = chosen.normalized_data
                subscription = block_from_single(
                    chosen, ("qib_x", "nii_x", "retail_x", "overall_x")
                )
                market_payload["subscription"] = subscription
                # Legacy aliases remain only for a single observation; multiple
                # exchange observations have no approved aggregate/preference.
                market_payload["qib_subscription"] = data.get("qib_x")
                market_payload["nii_subscription"] = data.get("nii_x")
                market_payload["retail_subscription"] = data.get("retail_x")
                market_payload["overall_subscription"] = data.get("overall_x")
            else:
                market_payload["subscription"] = {"observations": observations}

        # ------------------------------------------------------------------
        # 2. GMP: retain the raw hash and the observation metadata needed by
        #    the FINAL-only integrity gate. Multiple snapshots are not merged.
        # ------------------------------------------------------------------
        gmp_snaps = by_class.get(SourceClass.SECONDARY_TRACKER, [])
        if gmp_snaps:
            if len(gmp_snaps) == 1:
                chosen = gmp_snaps[0]
                data = chosen.normalized_data
                market_payload["gmp"] = block_from_single(
                    chosen, ("gmp_rupees", "pct", "trend", "is_statutory")
                )
                market_payload["gmp_rupees"] = data.get("gmp_rupees")
                market_payload["gmp_trend"] = data.get("trend")
            else:
                market_payload["gmp"] = {
                    "observations": [snapshot_record(snapshot) for snapshot in gmp_snaps]
                }

        # ------------------------------------------------------------------
        # 3. Market regime. Preserve all observations; do not infer a winner
        #    where the configured source/session/cutoff is not established.
        # ------------------------------------------------------------------
        regime_snaps = by_class.get(SourceClass.MARKET_REGIME, [])
        if regime_snaps:
            if len(regime_snaps) == 1:
                chosen = regime_snaps[0]
                data = chosen.normalized_data
                market_payload["regime"] = block_from_single(
                    chosen, ("nifty_trend", "last_ipo_listing_gains_pct", "vix")
                )
                market_payload["nifty_trend"] = data.get("nifty_trend")
                market_payload["listing_gains"] = copy.deepcopy(
                    data.get("last_ipo_listing_gains_pct", [])
                )
            else:
                market_payload["regime"] = {
                    "observations": [snapshot_record(snapshot) for snapshot in regime_snaps]
                }

        # ------------------------------------------------------------------
        # 4. Anchor book. Preserve distinct source observations rather than
        #    selecting by adapter registration order.
        # ------------------------------------------------------------------
        anchor_snaps = by_class.get(SourceClass.ANCHOR_BOOK, [])
        if anchor_snaps:
            if len(anchor_snaps) == 1:
                chosen = anchor_snaps[0]
                data = chosen.normalized_data
                market_payload["anchor"] = block_from_single(
                    chosen,
                    ("quality", "amount", "anchor_names", "anchor_total_shares", "anchor_lockin_verified"),
                )
                market_payload["anchor_names"] = copy.deepcopy(data.get("anchor_names", []))
                market_payload["anchor_total_shares"] = data.get("anchor_total_shares")
                market_payload["anchor_total_amount"] = data.get("amount")
                market_payload["anchor_lockin_verified"] = data.get("anchor_lockin_verified")
                market_payload["anchor_quality"] = data.get("quality")
            else:
                market_payload["anchor"] = {
                    "observations": [snapshot_record(snapshot) for snapshot in anchor_snaps]
                }

        # ------------------------------------------------------------------
        # 5. Peer valuations. A single snapshot keeps its peer-level evidence;
        #    multiple universe snapshots are not collapsed into a synthetic set.
        # ------------------------------------------------------------------
        peer_snaps = by_class.get(SourceClass.PEER_MULTIPLE, [])
        if peer_snaps:
            peer_payload["_sources"] = [snapshot.to_source_ref() for snapshot in peer_snaps]
            if len(peer_snaps) == 1:
                chosen = peer_snaps[0]
                data = chosen.normalized_data
                peer_payload["peers"] = copy.deepcopy(data.get("peers", []))
                peer_payload["recent_sector_ipos"] = copy.deepcopy(
                    data.get("recent_sector_ipos", [])
                )
                peer_payload["as_of"] = data.get("as_of")
                peer_payload["source_id"] = chosen.to_source_ref()["source_id"]
                peer_payload["snapshot"] = snapshot_record(chosen)
            else:
                peer_payload["snapshots"] = [snapshot_record(snapshot) for snapshot in peer_snaps]

        return market_payload, peer_payload, sources


__all__ = [
    "ConnectorCoordinator",
    "OfficialSubscriptionAdapter",
    "GmpSignalAdapter",
    "MarketRegimeAdapter",
    "PeerMultipleAdapter",
    "AnchorAllotmentAdapter",
]
