"""Provider adapters for external data feeds.

Phase 5H: Live / External Data Connectors.

Adapters normalize raw payloads from specific providers (Official Exchanges,
Secondary Grey Market Trackers, Market Regime Trackers, Peer Multiples, and Anchor Books)
into immutable, provider-neutral ExternalSnapshot structures with explicit provenance,
freshness evaluation, and strict secret hygiene.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Mapping, Optional, Sequence

from ..canonical import ExtractionMethod, Verification
from .interfaces import (
    ANCHOR_FRESHNESS_POLICY,
    MARKET_FRESHNESS_POLICY,
    PEER_FRESHNESS_POLICY,
    ConnectorPayloadError,
    ExternalSnapshot,
    FreshnessPolicy,
    FreshnessStatus,
    SourceClass,
    compute_payload_hash,
    sanitize_credentials,
)


def _safe_float(val: Any) -> Optional[float]:
    """Parse numeric value safely to float, returning None for missing or unparseable."""
    if val is None or val == "" or val == "UNKNOWN" or val == "null" or val == "[●]":
        return None
    try:
        f = float(val)
        return None if f != f else f  # Filter out NaN
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    """Parse numeric value safely to int, returning None for missing or unparseable."""
    if val is None or val == "" or val == "UNKNOWN" or val == "null" or val == "[●]":
        return None
    try:
        return int(round(float(val)))
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------
# Base Provider Adapter
# --------------------------------------------------------------------------


class BaseConnectorAdapter:
    """Base provider adapter defining ingestion, normalization, and provenance."""

    def __init__(
        self,
        provider_id: str,
        source_class: SourceClass,
        freshness_policy: FreshnessPolicy,
        verification: str = Verification.UNVERIFIED.value,
        extraction_method: str = ExtractionMethod.MARKET_DATA.value,
    ) -> None:
        self.provider_id = provider_id
        self.source_class = source_class
        self.freshness_policy = freshness_policy
        self.verification = verification
        self.extraction_method = extraction_method

    def normalize(
        self,
        raw_payload: Mapping[str, Any],
        reference_time: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> ExternalSnapshot:
        """Transform raw provider response into a validated ExternalSnapshot."""
        raise NotImplementedError


# --------------------------------------------------------------------------
# 1. Official Subscription Adapter (NSE / BSE)
# --------------------------------------------------------------------------


class OfficialSubscriptionAdapter(BaseConnectorAdapter):
    """Adapter for official exchange bidding data (NSE / BSE)."""

    def __init__(
        self,
        provider_id: str = "NSE-EXCHANGE-FEED",
        freshness_policy: Optional[FreshnessPolicy] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            source_class=SourceClass.OFFICIAL_EXCHANGE,
            freshness_policy=freshness_policy or MARKET_FRESHNESS_POLICY,
            verification=Verification.VERIFIED.value,
            extraction_method=ExtractionMethod.EXCHANGE_DATA.value,
        )

    def normalize(
        self,
        raw_payload: Mapping[str, Any],
        reference_time: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> ExternalSnapshot:
        clean_raw = sanitize_credentials(dict(raw_payload))
        raw_hash = compute_payload_hash(clean_raw)
        provider_id = clean_raw.get("provider_id") or self.provider_id

        # Extract timestamps
        retrieval_ts = clean_raw.get("retrieval_timestamp") or datetime.now(timezone.utc).isoformat()
        as_of = clean_raw.get("as_of")

        freshness = self.freshness_policy.evaluate_freshness(as_of, reference_time)

        # Subscription multiples
        qib = _safe_float(clean_raw.get("qib_x", clean_raw.get("qib_subscription")))
        nii = _safe_float(clean_raw.get("nii_x", clean_raw.get("nii_subscription")))
        retail = _safe_float(clean_raw.get("retail_x", clean_raw.get("retail_subscription")))
        overall = _safe_float(clean_raw.get("overall_x", clean_raw.get("overall_subscription")))

        # Check for negative subscription (impossible in official bidding feed)
        for name, val in [("qib", qib), ("nii", nii), ("retail", retail), ("overall", overall)]:
            if val is not None and val < 0:
                raise ConnectorPayloadError(
                    f"Official subscription multiple '{name}' cannot be negative: {val}",
                    provider_id=provider_id,
                )

        normalized = {
            "qib_x": qib,
            "nii_x": nii,
            "retail_x": retail,
            "overall_x": overall,
            "as_of": as_of,
            "source_id": f"SRC-{provider_id.upper()}",
        }

        snap_id = snapshot_id or clean_raw.get("snapshot_id") or "SUB-001"
        return ExternalSnapshot(
            snapshot_id=snap_id,
            provider_id=provider_id,
            source_class=self.source_class,
            retrieval_timestamp=retrieval_ts,
            as_of=as_of,
            raw_source_hash=raw_hash,
            normalized_data=normalized,
            extraction_method=self.extraction_method,
            verification=self.verification,
            freshness=freshness,
            confidence=1.0 if freshness == FreshnessStatus.FRESH else 0.5,
            notes=f"Official exchange bidding feed ({provider_id})",
            raw_payload=clean_raw,
        )


# --------------------------------------------------------------------------
# 2. GMP / Secondary Market Signal Adapter
# --------------------------------------------------------------------------


class GmpSignalAdapter(BaseConnectorAdapter):
    """Adapter for grey market premium (GMP) and secondary sentiment signals."""

    def __init__(
        self,
        provider_id: str = "CHITTORGARH-TRACKER",
        freshness_policy: Optional[FreshnessPolicy] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            source_class=SourceClass.SECONDARY_TRACKER,
            freshness_policy=freshness_policy or MARKET_FRESHNESS_POLICY,
            verification=Verification.UNVERIFIED.value,  # GMP is always unverified secondary signal
            extraction_method=ExtractionMethod.MARKET_DATA.value,
        )

    def normalize(
        self,
        raw_payload: Mapping[str, Any],
        reference_time: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> ExternalSnapshot:
        clean_raw = sanitize_credentials(dict(raw_payload))
        raw_hash = compute_payload_hash(clean_raw)

        retrieval_ts = clean_raw.get("retrieval_timestamp") or datetime.now(timezone.utc).isoformat()
        as_of = clean_raw.get("as_of")

        freshness = self.freshness_policy.evaluate_freshness(as_of, reference_time)

        gmp_val = _safe_float(clean_raw.get("gmp_rupees", clean_raw.get("gmp")))
        gmp_pct = _safe_float(clean_raw.get("gmp_pct", clean_raw.get("pct")))

        # Standardize trend enum
        raw_trend = clean_raw.get("trend", clean_raw.get("gmp_trend"))
        trend = None
        if raw_trend is not None:
            t_str = str(raw_trend).strip().lower()
            if t_str in ("strong", "rising", "bullish", "up"):
                trend = "strong"
            elif t_str in ("flat", "steady", "neutral"):
                trend = "flat"
            elif t_str in ("falling", "declining", "bearish", "down"):
                trend = "falling"
            elif t_str in ("null", "unknown", "none"):
                trend = None
            else:
                trend = t_str

        normalized = {
            "gmp_rupees": gmp_val,
            "pct": gmp_pct,
            "trend": trend,
            "as_of": as_of,
            "source_id": f"SRC-{self.provider_id.upper()}",
            "is_statutory": False,  # Explicit contract: GMP is NEVER statutory fact
        }

        snap_id = snapshot_id or clean_raw.get("snapshot_id") or "GMP-001"
        return ExternalSnapshot(
            snapshot_id=snap_id,
            provider_id=self.provider_id,
            source_class=self.source_class,
            retrieval_timestamp=retrieval_ts,
            as_of=as_of,
            raw_source_hash=raw_hash,
            normalized_data=normalized,
            extraction_method=self.extraction_method,
            verification=self.verification,
            freshness=freshness,
            confidence=0.7 if freshness == FreshnessStatus.FRESH else 0.3,
            notes="Secondary market grey-market estimate (unofficial signal, non-statutory)",
            raw_payload=clean_raw,
        )


# --------------------------------------------------------------------------
# 3. Market Regime Adapter (Nifty 50, VIX, Recent Listings)
# --------------------------------------------------------------------------


class MarketRegimeAdapter(BaseConnectorAdapter):
    """Adapter for broader market regime (NSE Nifty 50, VIX, recent listing gains)."""

    def __init__(
        self,
        provider_id: str = "NSE-MARKET-REGIME",
        freshness_policy: Optional[FreshnessPolicy] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            source_class=SourceClass.MARKET_REGIME,
            freshness_policy=freshness_policy or MARKET_FRESHNESS_POLICY,
            verification=Verification.VERIFIED.value,
            extraction_method=ExtractionMethod.MARKET_DATA.value,
        )

    def normalize(
        self,
        raw_payload: Mapping[str, Any],
        reference_time: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> ExternalSnapshot:
        clean_raw = sanitize_credentials(dict(raw_payload))
        raw_hash = compute_payload_hash(clean_raw)

        retrieval_ts = clean_raw.get("retrieval_timestamp") or datetime.now(timezone.utc).isoformat()
        as_of = clean_raw.get("as_of")

        freshness = self.freshness_policy.evaluate_freshness(as_of, reference_time)

        # Standardize nifty trend enum
        raw_nifty = clean_raw.get("nifty_trend")
        nifty_trend = None
        if raw_nifty is not None:
            n_str = str(raw_nifty).strip().lower()
            if n_str in ("supportive", "bullish", "strong", "positive"):
                nifty_trend = "supportive"
            elif n_str in ("neutral", "flat", "sideways", "steady"):
                nifty_trend = "neutral"
            elif n_str in ("weak", "bearish", "negative"):
                nifty_trend = "weak"
            elif n_str in ("null", "none", "unknown"):
                nifty_trend = None
            else:
                nifty_trend = n_str

        # Listing gains array
        raw_gains = clean_raw.get("last_ipo_listing_gains_pct", clean_raw.get("listing_gains", []))
        listing_gains: List[float] = []
        if isinstance(raw_gains, (list, tuple)):
            for g in raw_gains:
                gf = _safe_float(g)
                if gf is not None:
                    listing_gains.append(gf)
        elif _safe_float(raw_gains) is not None:
            listing_gains.append(_safe_float(raw_gains))  # type: ignore

        vix = _safe_float(clean_raw.get("vix"))

        normalized = {
            "nifty_trend": nifty_trend,
            "last_ipo_listing_gains_pct": listing_gains[:5],  # Capped at 5 per schema
            "vix": vix,
            "as_of": as_of,
            "source_id": f"SRC-{self.provider_id.upper()}",
        }

        snap_id = snapshot_id or clean_raw.get("snapshot_id") or "REGIME-001"
        return ExternalSnapshot(
            snapshot_id=snap_id,
            provider_id=self.provider_id,
            source_class=self.source_class,
            retrieval_timestamp=retrieval_ts,
            as_of=as_of,
            raw_source_hash=raw_hash,
            normalized_data=normalized,
            extraction_method=self.extraction_method,
            verification=self.verification,
            freshness=freshness,
            confidence=1.0 if freshness == FreshnessStatus.FRESH else 0.5,
            notes=f"Market regime and index momentum tracker ({self.provider_id})",
            raw_payload=clean_raw,
        )


# --------------------------------------------------------------------------
# 4. Peer Valuation Multiple Adapter
# --------------------------------------------------------------------------


class PeerMultipleAdapter(BaseConnectorAdapter):
    """Adapter for listed peer valuation multiples (Screener / Exchange composites)."""

    def __init__(
        self,
        provider_id: str = "PEER-SCREENER",
        freshness_policy: Optional[FreshnessPolicy] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            source_class=SourceClass.PEER_MULTIPLE,
            freshness_policy=freshness_policy or PEER_FRESHNESS_POLICY,
            verification=Verification.VERIFIED.value,
            extraction_method=ExtractionMethod.MARKET_DATA.value,
        )

    def normalize(
        self,
        raw_payload: Mapping[str, Any],
        reference_time: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> ExternalSnapshot:
        clean_raw = sanitize_credentials(dict(raw_payload))
        raw_hash = compute_payload_hash(clean_raw)

        retrieval_ts = clean_raw.get("retrieval_timestamp") or datetime.now(timezone.utc).isoformat()
        as_of = clean_raw.get("as_of")

        freshness = self.freshness_policy.evaluate_freshness(as_of, reference_time)

        # Normalize peers list
        raw_peers = clean_raw.get("peers", [])
        normalized_peers: List[Dict[str, Any]] = []

        if not isinstance(raw_peers, (list, tuple)):
            raise ConnectorPayloadError(
                "Peer multiples payload must contain a 'peers' list",
                provider_id=self.provider_id,
            )

        for p in raw_peers:
            if not isinstance(p, Mapping):
                continue
            name = str(p.get("name", "")).strip()
            if not name:
                continue

            peer_as_of = p.get("as_of") or as_of
            peer_dict: Dict[str, Any] = {
                "name": name,
                "pe": _safe_float(p.get("pe")),
                "ev_ebitda": _safe_float(p.get("ev_ebitda")),
                "pb": _safe_float(p.get("pb")),
                "ps": _safe_float(p.get("ps")),
                "roe_pct": _safe_float(p.get("roe_pct")),
                "roa_pct": _safe_float(p.get("roa_pct")),
                "source_id": p.get("source_id") or f"SRC-{self.provider_id.upper()}",
            }
            if peer_as_of:
                peer_dict["as_of"] = peer_as_of
            normalized_peers.append(peer_dict)

        # Recent sector IPOs
        recent_ipos = clean_raw.get("recent_sector_ipos", [])
        clean_recent: List[Dict[str, Any]] = []
        if isinstance(recent_ipos, (list, tuple)):
            for item in recent_ipos:
                if isinstance(item, Mapping):
                    clean_recent.append(dict(item))

        normalized = {
            "peers": normalized_peers,
            "recent_sector_ipos": clean_recent,
            "as_of": as_of,
            "source_id": f"SRC-{self.provider_id.upper()}",
        }

        snap_id = snapshot_id or clean_raw.get("snapshot_id") or "PEER-001"
        return ExternalSnapshot(
            snapshot_id=snap_id,
            provider_id=self.provider_id,
            source_class=self.source_class,
            retrieval_timestamp=retrieval_ts,
            as_of=as_of,
            raw_source_hash=raw_hash,
            normalized_data=normalized,
            extraction_method=self.extraction_method,
            verification=self.verification,
            freshness=freshness,
            confidence=1.0 if freshness == FreshnessStatus.FRESH else 0.5,
            notes=f"Listed peer valuation multiple composites ({self.provider_id})",
            raw_payload=clean_raw,
        )


# --------------------------------------------------------------------------
# 5. Anchor Allotment Adapter
# --------------------------------------------------------------------------


class AnchorAllotmentAdapter(BaseConnectorAdapter):
    """Adapter for official exchange anchor allotment notifications."""

    def __init__(
        self,
        provider_id: str = "EXCHANGE-ANCHOR-CIRCULAR",
        freshness_policy: Optional[FreshnessPolicy] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            source_class=SourceClass.ANCHOR_BOOK,
            freshness_policy=freshness_policy or ANCHOR_FRESHNESS_POLICY,
            verification=Verification.VERIFIED.value,
            extraction_method=ExtractionMethod.EXCHANGE_DATA.value,
        )

    def normalize(
        self,
        raw_payload: Mapping[str, Any],
        reference_time: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> ExternalSnapshot:
        clean_raw = sanitize_credentials(dict(raw_payload))
        raw_hash = compute_payload_hash(clean_raw)

        retrieval_ts = clean_raw.get("retrieval_timestamp") or datetime.now(timezone.utc).isoformat()
        as_of = clean_raw.get("as_of")

        freshness = self.freshness_policy.evaluate_freshness(as_of, reference_time)

        # Investor names
        raw_names = clean_raw.get("anchor_names", clean_raw.get("investors", []))
        anchor_names: List[str] = []
        if isinstance(raw_names, (list, tuple)):
            for n in raw_names:
                if isinstance(n, str) and n.strip():
                    anchor_names.append(n.strip())
                elif isinstance(n, Mapping) and "name" in n:
                    anchor_names.append(str(n["name"]).strip())

        total_shares = _safe_int(clean_raw.get("anchor_total_shares", clean_raw.get("total_shares")))
        total_amount = _safe_float(clean_raw.get("anchor_total_amount", clean_raw.get("amount")))
        lockin_verified = clean_raw.get("anchor_lockin_verified", clean_raw.get("lockin_verified"))
        if lockin_verified is not None:
            lockin_verified = bool(lockin_verified)

        # Quality enum: reputed, mixed, unknown
        raw_quality = clean_raw.get("anchor_quality", clean_raw.get("quality"))
        quality = None
        if raw_quality is not None:
            q_str = str(raw_quality).strip().lower()
            if q_str in ("reputed", "strong", "high", "top_tier"):
                quality = "reputed"
            elif q_str in ("mixed", "average", "moderate"):
                quality = "mixed"
            elif q_str in ("unknown", "poor", "unverified"):
                quality = "unknown"
            elif q_str in ("null", "none"):
                quality = None
            else:
                quality = q_str

        normalized = {
            "anchor_names": anchor_names,
            "anchor_total_shares": total_shares,
            "amount": total_amount,
            "anchor_lockin_verified": lockin_verified,
            "quality": quality,
            "as_of": as_of,
            "source_id": f"SRC-{self.provider_id.upper()}",
        }

        snap_id = snapshot_id or clean_raw.get("snapshot_id") or "ANCHOR-001"
        return ExternalSnapshot(
            snapshot_id=snap_id,
            provider_id=self.provider_id,
            source_class=self.source_class,
            retrieval_timestamp=retrieval_ts,
            as_of=as_of,
            raw_source_hash=raw_hash,
            normalized_data=normalized,
            extraction_method=self.extraction_method,
            verification=self.verification,
            freshness=freshness,
            confidence=1.0 if freshness == FreshnessStatus.FRESH else 0.5,
            notes=f"Official anchor book allotment circular ({self.provider_id})",
            raw_payload=clean_raw,
        )
