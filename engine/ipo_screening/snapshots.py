"""Immutable peer and market snapshots with explicit staleness status.

Spec v1.5 s9 (critical valuation rule) and s12:
  * peer status is VALID / STALE / UNUSABLE / MISSING;
  * a stale peer multiple is *not* automatically usable;
  * stale or unavailable peer data must not silently become valid scoring
    data, and (tech design s10) the engine "must not silently substitute
    stale data";
  * market inputs are only valid with a timestamp, a source and a defined
    applicability to the evaluation mode.

The reference prototype emitted a warning for stale peers and then scored
them as current. v1.5 forbids that. Here staleness is a first-class status
that the derived-metrics layer consumes: a valuation criterion backed only
by non-VALID peers resolves to UNKNOWN and widens the score range instead of
silently scoring full marks or zero.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .canonical import parse_date, parse_datetime

PEER_VALID = "VALID"
PEER_STALE = "STALE"
PEER_UNUSABLE = "UNUSABLE"
PEER_MISSING = "MISSING"

MARKET_FRESH = "FRESH"
MARKET_STALE = "STALE"
MARKET_MISSING = "MISSING"


@dataclass(frozen=True)
class PeerObservation:
    """One comparable company as observed in an immutable peer snapshot."""

    peer_id: str
    name: str
    status: str
    as_of: Optional[str]
    business_match: Optional[str]
    listed_years: Optional[float]
    pe: Optional[float]
    ev_ebitda: Optional[float]
    pb: Optional[float]
    ps: Optional[float]
    roe_pct: Optional[float]
    roa_pct: Optional[float]
    growth_pct: Optional[float]
    source_id: Optional[str] = None
    age_days: Optional[float] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "peer_id": self.peer_id,
            "name": self.name,
            "status": self.status,
        }
        for key in (
            "as_of",
            "business_match",
            "listed_years",
            "pe",
            "ev_ebitda",
            "pb",
            "ps",
            "roe_pct",
            "roa_pct",
            "growth_pct",
            "source_id",
            "age_days",
            "reason",
        ):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        return out


@dataclass(frozen=True)
class PeerSnapshot:
    """Frozen view of the peer set used by an evaluation (spec s21)."""

    snapshot_id: str
    as_of: Optional[str]
    observations: Sequence[PeerObservation]
    staleness_days: int
    min_listed_years: float
    included_peers: Sequence[str] = field(default_factory=tuple)
    #: When the snapshot was frozen. Audit detail only; excluded from the
    #: material hash so that the result hash does not move as the clock does.
    captured_at: Optional[str] = None

    @property
    def valid(self) -> Sequence[PeerObservation]:
        return [p for p in self.observations if p.status == PEER_VALID]

    @property
    def rejected(self) -> Sequence[PeerObservation]:
        return [p for p in self.observations if p.status != PEER_VALID]

    def has_valid(self) -> bool:
        return len(self.valid) > 0

    def median(self, field_name: str) -> Optional[float]:
        """Median of a multiple across VALID peers only.

        Returns ``None`` when no valid peer supplies the multiple, which
        propagates to UNKNOWN in the derived-metrics layer.
        """
        values = [
            getattr(p, field_name)
            for p in self.valid
            if getattr(p, field_name) is not None
        ]
        if not values:
            return None
        return float(statistics.median(values))

    def quartiles(self, field_name: str) -> Optional[Dict[str, float]]:
        values = sorted(
            getattr(p, field_name)
            for p in self.valid
            if getattr(p, field_name) is not None
        )
        if len(values) < 2:
            return None
        return {
            "min": values[0],
            "median": float(statistics.median(values)),
            "max": values[-1],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "as_of": self.as_of,
            "staleness_days": self.staleness_days,
            "min_listed_years": self.min_listed_years,
            "observations": [o.to_dict() for o in self.observations],
            "valid_count": len(self.valid),
            "rejected_count": len(self.rejected),
            "captured_at": self.captured_at,
            "content_hash": self.snapshot_hash(),
        }

    def hash_payload(self) -> Dict[str, Any]:
        """The material content of the snapshot, for hashing.

        Wall-clock ages (``age_days``) are deliberately excluded: they are an
        audit detail, not a decision input. Including them would make the
        result hash move because time passed, which would defeat the purpose
        of the hash as a reproducible fingerprint of the evaluation (spec s19).
        Everything that *can* change a decision is included: the classification
        status, the observation values, the thresholds, and the as-of dates.
        """
        return {
            "snapshot_id": self.snapshot_id,
            "as_of": self.as_of,
            "staleness_days": self.staleness_days,
            "min_listed_years": self.min_listed_years,
            "observations": [
                {k: v for k, v in o.to_dict().items() if k != "age_days"} for o in self.observations
            ],
        }

    def snapshot_hash(self) -> str:
        from .hashing import sha256_of

        return sha256_of(self.hash_payload())


def classify_peers(
    raw_peers: Sequence[Mapping[str, Any]],
    *,
    evaluation_datetime: datetime,
    staleness_days: int,
    min_listed_years: float,
    source_id: Optional[str] = None,
    snapshot_id: str = "PEERS-1",
) -> PeerSnapshot:
    """Classify each supplied peer as VALID / STALE / UNUSABLE / MISSING.

    A peer with no usable multiple at all is ``MISSING``; a peer lacking the
    required listing history or flagged as a mismatched business is
    ``UNUSABLE``; a peer whose ``as_of`` is older than ``staleness_days`` is
    ``STALE``. Only ``VALID`` peers contribute to peer medians.
    """
    observations: List[PeerObservation] = []
    for index, peer in enumerate(raw_peers or []):
        name = str(peer.get("name") or f"peer-{index}")
        peer_id = str(peer.get("peer_id") or f"PEER-{index + 1}")
        as_of = peer.get("as_of")
        listed_years = peer.get("listed_years")
        business_match = peer.get("business_match")

        multiples = {
            "pe": _num(peer.get("pe")),
            "ev_ebitda": _num(peer.get("ev_ebitda")),
            "pb": _num(peer.get("pb")),
            "ps": _num(peer.get("ps")),
        }
        age_days = _age_days(as_of, evaluation_datetime)

        status = PEER_VALID
        reason = None

        if all(v is None for v in multiples.values()):
            status = PEER_MISSING
            reason = "no peer multiple supplied"
        elif business_match is not None and str(business_match).lower() in {
            "mismatch",
            "unusable",
            "not_comparable",
        }:
            status = PEER_UNUSABLE
            reason = f"business comparability reported as {business_match!r}"
        elif listed_years is not None and float(listed_years) < min_listed_years:
            status = PEER_UNUSABLE
            reason = (
                f"listed {listed_years} years, below the {min_listed_years}-year "
                "minimum listing history"
            )
        elif as_of is None:
            status = PEER_STALE
            reason = "peer multiple has no as-of date, so its currency cannot be established"
        elif age_days is not None and age_days > staleness_days:
            status = PEER_STALE
            # The age itself is recorded in ``age_days``; it is deliberately
            # kept out of the reason text so that this reason (which is copied
            # into derived-metric explanations and hence into the result hash)
            # does not move as the wall clock does (spec s19).
            reason = (
                f"peer multiple dated {as_of} is beyond the {staleness_days}-day "
                "staleness limit"
            )

        observations.append(
            PeerObservation(
                peer_id=peer_id,
                name=name,
                status=status,
                as_of=as_of,
                business_match=business_match,
                listed_years=_num(listed_years),
                pe=multiples["pe"],
                ev_ebitda=multiples["ev_ebitda"],
                pb=multiples["pb"],
                ps=multiples["ps"],
                roe_pct=_num(peer.get("roe_pct")),
                roa_pct=_num(peer.get("roa_pct")),
                growth_pct=_num(peer.get("growth_pct")),
                source_id=peer.get("source_id") or source_id,
                age_days=age_days,
                reason=reason,
            )
        )

    return PeerSnapshot(
        snapshot_id=snapshot_id,
        as_of=_newest(
            [o.as_of for o in observations],
            fallback=evaluation_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        observations=tuple(observations),
        staleness_days=staleness_days,
        min_listed_years=min_listed_years,
        captured_at=evaluation_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _newest(stamps: Sequence[Optional[str]], fallback: str) -> str:
    """The newest parseable timestamp in ``stamps`` (lexicographic-safe ISO 8601).

    Used for the snapshot's material ``as_of``: it must be a *source* timestamp,
    not the instant the evaluation ran, or the snapshot hash would change
    whenever the clock moved (spec s19).
    """
    candidates = [str(s) for s in stamps if s]
    if not candidates:
        return fallback
    return max(candidates)


def _num(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _age_days(as_of: Any, evaluation_datetime: datetime) -> Optional[float]:
    if as_of is None:
        return None
    text = str(as_of)
    parsed: Optional[datetime] = None
    try:
        if "T" in text:
            parsed = parse_datetime(text)
        else:
            d = parse_date(text)
            if d is not None:
                parsed = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
    if parsed is None:
        return None
    return (evaluation_datetime - parsed).total_seconds() / 86400.0


# --------------------------------------------------------------------------
# Market snapshot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MarketBlock:
    """A timestamped market observation block (spec s12, s4.6)."""

    name: str
    status: str
    as_of: Optional[str]
    age_hours: Optional[float]
    values: Mapping[str, Any]
    source_id: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "block": self.name,
            "status": self.status,
            "as_of": self.as_of,
            "values": dict(self.values),
        }
        if self.age_hours is not None:
            out["age_hours"] = round(self.age_hours, 3)
        if self.source_id is not None:
            out["source_id"] = self.source_id
        if self.reason is not None:
            out["reason"] = self.reason
        return out


@dataclass(frozen=True)
class MarketSnapshot:
    snapshot_id: str
    as_of: Optional[str]
    blocks: Sequence[MarketBlock]
    staleness_hours: int
    #: When the snapshot was frozen. Audit detail only; excluded from the
    #: material hash so that the result hash does not move as the clock does.
    captured_at: Optional[str] = None

    def block(self, name: str) -> Optional[MarketBlock]:
        for b in self.blocks:
            if b.name == name:
                return b
        return None

    def value(self, block_name: str, key: str) -> Optional[Any]:
        """Value from a block, or ``None`` when the block is missing/stale.

        A stale block is treated exactly like an absent one: the dependent
        metric becomes UNKNOWN rather than scoring on old data.
        """
        block = self.block(block_name)
        if block is None or block.status != MARKET_FRESH:
            return None
        return block.values.get(key)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "as_of": self.as_of,
            "staleness_hours": self.staleness_hours,
            "blocks": [b.to_dict() for b in self.blocks],
            "captured_at": self.captured_at,
            "content_hash": self.snapshot_hash(),
        }

    def hash_payload(self) -> Dict[str, Any]:
        """The material content of the snapshot, for hashing.

        Volatile ages are excluded for the same reason as the peer snapshot:
        the hash must fingerprint the decision inputs, not the wall clock
        (spec s19). The freshness *classification* is included, because a
        stale block genuinely changes the result.
        """
        return {
            "snapshot_id": self.snapshot_id,
            "as_of": self.as_of,
            "staleness_hours": self.staleness_hours,
            "blocks": [
                {k: v for k, v in b.to_dict().items() if k != "age_hours"} for b in self.blocks
            ],
        }

    def snapshot_hash(self) -> str:
        from .hashing import sha256_of

        return sha256_of(self.hash_payload())


MARKET_BLOCK_NAMES = ("anchor", "subscription", "gmp", "regime")


def build_market_snapshot(
    raw_market: Mapping[str, Any],
    *,
    evaluation_datetime: datetime,
    staleness_hours: int,
    snapshot_id: str = "MARKET-1",
) -> MarketSnapshot:
    """Freeze the market blocks and mark each FRESH / STALE / MISSING."""
    blocks: List[MarketBlock] = []
    for name in MARKET_BLOCK_NAMES:
        raw_block = raw_market.get(name)
        if not isinstance(raw_block, Mapping) or not raw_block:
            blocks.append(
                MarketBlock(
                    name=name,
                    status=MARKET_MISSING,
                    as_of=None,
                    age_hours=None,
                    values={},
                    reason="block not supplied",
                )
            )
            continue

        as_of = raw_block.get("as_of")
        age_hours: Optional[float] = None
        status = MARKET_FRESH
        reason = None

        if as_of is None:
            status = MARKET_STALE
            reason = "block has no as-of timestamp, so its currency cannot be established"
        else:
            try:
                parsed = parse_datetime(as_of)
                assert parsed is not None
                age_hours = (evaluation_datetime - parsed).total_seconds() / 3600.0
                if age_hours > staleness_hours:
                    status = MARKET_STALE
                    # As above, the age is recorded in ``age_hours`` rather than
                    # in the reason, to keep the reason - and therefore the
                    # result hash - independent of the evaluation clock.
                    reason = (
                        f"block dated {as_of} is beyond the {staleness_hours}-hour "
                        "staleness limit"
                    )
                elif age_hours < -1.0:
                    status = MARKET_STALE
                    reason = f"block as-of {as_of} is in the future relative to the evaluation"
            except (ValueError, TypeError):
                status = MARKET_STALE
                reason = f"block as-of {as_of!r} is not a parseable timestamp"

        values = {k: v for k, v in raw_block.items() if k != "as_of"}
        blocks.append(
            MarketBlock(
                name=name,
                status=status,
                as_of=as_of,
                age_hours=age_hours,
                values=values,
                source_id=raw_block.get("source_id"),
                reason=reason,
            )
        )

    return MarketSnapshot(
        snapshot_id=snapshot_id,
        as_of=_newest(
            [b.as_of for b in blocks],
            fallback=evaluation_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        captured_at=evaluation_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        blocks=tuple(blocks),
        staleness_hours=staleness_hours,
    )


__all__ = [
    "PEER_VALID",
    "PEER_STALE",
    "PEER_UNUSABLE",
    "PEER_MISSING",
    "MARKET_FRESH",
    "MARKET_STALE",
    "MARKET_MISSING",
    "MARKET_BLOCK_NAMES",
    "PeerObservation",
    "PeerSnapshot",
    "MarketBlock",
    "MarketSnapshot",
    "classify_peers",
    "build_market_snapshot",
]
