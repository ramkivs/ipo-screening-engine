"""External data connectors package for IPO screening engine.

Phase 5H: Live / External Data Connectors.

Exports provider-neutral connector abstractions, adapters for official and secondary
sources, freshness evaluators, and the connector coordinator.
"""

from .adapters import (
    AnchorAllotmentAdapter,
    BaseConnectorAdapter,
    GmpSignalAdapter,
    MarketRegimeAdapter,
    OfficialSubscriptionAdapter,
    PeerMultipleAdapter,
)
from .coordinator import ConnectorCoordinator
from .interfaces import (
    ANCHOR_FRESHNESS_POLICY,
    MARKET_FRESHNESS_POLICY,
    PEER_FRESHNESS_POLICY,
    ConflictingSourceError,
    ConnectorAuthError,
    ConnectorError,
    ConnectorPayloadError,
    ConnectorTimeoutError,
    ExternalSnapshot,
    FreshnessPolicy,
    FreshnessStatus,
    SourceClass,
    StaleDataError,
    compute_payload_hash,
    sanitize_credentials,
)

__all__ = [
    "SourceClass",
    "FreshnessStatus",
    "ExternalSnapshot",
    "FreshnessPolicy",
    "MARKET_FRESHNESS_POLICY",
    "PEER_FRESHNESS_POLICY",
    "ANCHOR_FRESHNESS_POLICY",
    "sanitize_credentials",
    "compute_payload_hash",
    "ConnectorError",
    "ConnectorAuthError",
    "ConnectorTimeoutError",
    "ConnectorPayloadError",
    "StaleDataError",
    "ConflictingSourceError",
    "BaseConnectorAdapter",
    "OfficialSubscriptionAdapter",
    "GmpSignalAdapter",
    "MarketRegimeAdapter",
    "PeerMultipleAdapter",
    "AnchorAllotmentAdapter",
    "ConnectorCoordinator",
]
