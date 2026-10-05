"""Provider-neutral external data connector interfaces, contracts, and data models.

Phase 5H: Live / External Data Connectors.

Defines the abstractions for acquiring, normalizing, validating, timestamping,
provenance-binding, and fail-closing external data feeds (Official Exchange Bidding,
Secondary GMP Signals, Market Regime Trackers, Peer Valuations, and Anchor Books)
WITHOUT embedding provider-specific logic inside the frozen evaluation core.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from ..canonical import (
    ExtractionMethod,
    SourceRef,
    SourceType,
    Verification,
    parse_datetime,
)
from ..errors import Finding, SEVERITY_ERROR, SEVERITY_WARNING


# --------------------------------------------------------------------------
# Enumerations
# --------------------------------------------------------------------------


class SourceClass(str, Enum):
    """Classification of external data source tier and regulatory standing."""

    OFFICIAL_EXCHANGE = "OFFICIAL_EXCHANGE"      # Tier 1/2: NSE/BSE official bidding or circular
    SECONDARY_TRACKER = "SECONDARY_TRACKER"      # Tier 3: Third-party tracker / Chittorgarh / GMP
    MARKET_REGIME = "MARKET_REGIME"              # Macroeconomic / Index tracking (Nifty, VIX)
    PEER_MULTIPLE = "PEER_MULTIPLE"              # Valuation multiple composites (Screener, BSE/NSE)
    ANCHOR_BOOK = "ANCHOR_BOOK"                  # Official anchor allotment circular (Exchange)


class FreshnessStatus(str, Enum):
    """Freshness classification relative to evaluation instant."""

    FRESH = "FRESH"                              # Age within staleness threshold
    STALE = "STALE"                              # Age exceeds staleness threshold
    FUTURE = "FUTURE"                            # Timestamp is in the future (> 1h ahead)
    MISSING = "MISSING"                          # Timestamp missing or unparseable


# --------------------------------------------------------------------------
# Secret Hygiene & Sanitization
# --------------------------------------------------------------------------

_SENSITIVE_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|auth|bearer|credential|password|secret|token|cookie|pwd|private[_-]?key)"
)

_BEARER_TOKEN_RE = re.compile(
    r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{8,}",
)


def sanitize_credentials(obj: Any) -> Any:
    """Recursively scrub secrets, tokens, and credentials from dictionaries and lists."""
    if isinstance(obj, Mapping):
        sanitized: Dict[str, Any] = {}
        for k, v in obj.items():
            if _SENSITIVE_KEY_RE.search(str(k)):
                sanitized[k] = "***REDACTED***"
            else:
                sanitized[k] = sanitize_credentials(v)
        return sanitized
    elif isinstance(obj, (list, tuple)):
        return [sanitize_credentials(item) for item in obj]
    elif isinstance(obj, str):
        return _BEARER_TOKEN_RE.sub("Bearer ***REDACTED***", obj)
    return obj


def compute_payload_hash(data: Any) -> str:
    """Compute deterministic SHA-256 hash of a payload (raw bytes or JSON-serializable)."""
    if isinstance(data, (bytes, bytearray)):
        return hashlib.sha256(data).hexdigest()
    if isinstance(data, str):
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
    clean_data = sanitize_credentials(data)
    canonical_json = json.dumps(clean_data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Connector Exceptions
# --------------------------------------------------------------------------


class ConnectorError(Exception):
    """Base class for all connector layer errors."""

    def __init__(self, message: str, provider_id: Optional[str] = None) -> None:
        safe_msg = sanitize_credentials(message)
        super().__init__(safe_msg)
        self.provider_id = provider_id


class ConnectorAuthError(ConnectorError):
    """Raised when authentication credentials fail or are rejected."""


class ConnectorTimeoutError(ConnectorError):
    """Raised when external provider communication times out."""


class ConnectorPayloadError(ConnectorError):
    """Raised when provider response is malformed, truncated, or unparseable."""


class StaleDataError(ConnectorError):
    """Raised when data fails freshness validation in strict / final mode."""


class ConflictingSourceError(ConnectorError):
    """Raised when two authoritative sources provide conflicting values without a tie-breaker."""


# --------------------------------------------------------------------------
# Provider-Neutral Snapshots & Data Containers
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ExternalSnapshot:
    """Immutable provider-neutral snapshot with audit provenance and freshness status."""

    snapshot_id: str
    provider_id: str
    source_class: SourceClass
    retrieval_timestamp: str
    as_of: Optional[str]
    raw_source_hash: str
    normalized_data: Mapping[str, Any]
    extraction_method: str = ExtractionMethod.MARKET_DATA.value
    verification: str = Verification.UNVERIFIED.value
    freshness: FreshnessStatus = FreshnessStatus.FRESH
    confidence: float = 1.0
    is_sanitized: bool = True
    notes: Optional[str] = None
    raw_payload: Optional[Mapping[str, Any]] = None

    def to_source_ref(self) -> Dict[str, Any]:
        """Convert snapshot metadata to canonical _sources reference dictionary."""
        st = SourceType.EXCHANGE.value if self.source_class in (
            SourceClass.OFFICIAL_EXCHANGE,
            SourceClass.ANCHOR_BOOK,
        ) else SourceType.MARKET_DATA.value

        if self.source_class == SourceClass.PEER_MULTIPLE:
            st = SourceType.PEER_DATA.value

        ref: Dict[str, Any] = {
            "source_id": f"SRC-{self.provider_id.upper()}-{self.snapshot_id}",
            "source_type": st,
            "uri": f"connector://{self.provider_id}/{self.snapshot_id}",
            "content_hash": self.raw_source_hash,
            "retrieval_timestamp": self.retrieval_timestamp,
        }
        if self.as_of:
            ref["source_timestamp"] = self.as_of
        if self.notes:
            ref["note"] = self.notes
        return ref

    def to_dict(self) -> Dict[str, Any]:
        """Serialize snapshot to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "provider_id": self.provider_id,
            "source_class": self.source_class.value,
            "retrieval_timestamp": self.retrieval_timestamp,
            "as_of": self.as_of,
            "raw_source_hash": self.raw_source_hash,
            "normalized_data": dict(self.normalized_data),
            "extraction_method": self.extraction_method,
            "verification": self.verification,
            "freshness": self.freshness.value,
            "confidence": self.confidence,
            "is_sanitized": self.is_sanitized,
            "notes": self.notes,
        }


# --------------------------------------------------------------------------
# Freshness Policy
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FreshnessPolicy:
    """Rules for evaluating whether an external observation is current."""

    max_age_hours: float
    allow_missing_timestamp: bool = False
    allow_future_tolerance_seconds: float = 3600.0  # 1 hour clock skew tolerance

    def evaluate_freshness(
        self,
        as_of: Optional[str],
        reference_time: Optional[datetime] = None,
    ) -> FreshnessStatus:
        """Evaluate freshness status against the reference timestamp."""
        if not as_of:
            return FreshnessStatus.FRESH if self.allow_missing_timestamp else FreshnessStatus.MISSING

        ref = reference_time or datetime.now(timezone.utc)
        parsed = parse_datetime(as_of)
        if not parsed:
            return FreshnessStatus.MISSING

        # Ensure timezone awareness
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)

        age_seconds = (ref - parsed).total_seconds()
        age_hours = age_seconds / 3600.0

        if age_seconds < -self.allow_future_tolerance_seconds:
            return FreshnessStatus.FUTURE

        if age_hours > self.max_age_hours:
            return FreshnessStatus.STALE

        return FreshnessStatus.FRESH


# Default standard freshness policies aligned with v1.5 architecture
MARKET_FRESHNESS_POLICY = FreshnessPolicy(max_age_hours=24.0)
PEER_FRESHNESS_POLICY = FreshnessPolicy(max_age_hours=30.0 * 24.0)  # 30 days
ANCHOR_FRESHNESS_POLICY = FreshnessPolicy(max_age_hours=72.0)       # 3 days
