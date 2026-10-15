"""A17 GMP observation-eligibility rules applied on top of the frozen market snapshot.

Decision record: ``handoff/decisions/A17-gmp-cutoff-freshness-and-trend-labels.md``.

* **A17-1 - cutoff.** The evaluation timestamp is the GMP eligibility cutoff.
  A GMP block whose source timestamp is later than the evaluation timestamp is
  ineligible. The generic one-hour future-timestamp allowance applied by
  ``build_market_snapshot`` does not apply to GMP. A source timestamp without
  an explicit UTC offset is never given an assumed zone: its position relative
  to the cutoff cannot be established, so the block fails closed.
* **A17-2 - maximum age.** The configured ``market_staleness_hours`` (24 h) is
  retained and is already enforced by ``build_market_snapshot`` relative to the
  same evaluation timestamp. It is deliberately not re-implemented here, so
  there is one threshold.

``snapshots.py`` belongs to the hash-pinned frozen core and is not modified.
This module only demotes a GMP block that the builder classified ``FRESH`` to
``STALE``. It never promotes a block, never alters another block, and never
touches source qualification: the A9 gate still withholds ``FINAL`` for every
GMP observation until a source qualifies.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Optional

from .snapshots import MARKET_FRESH, MARKET_STALE, MarketSnapshot

GMP_BLOCK_NAME = "gmp"


def explicit_offset_instant(value: Any) -> Optional[datetime]:
    """Parse an ISO 8601 timestamp only when it carries an explicit UTC offset.

    Returns ``None`` for missing, unparseable or offset-less values. Unlike
    ``canonical.parse_datetime``, it never assumes UTC for an offset-less value.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def apply_gmp_cutoff(market: MarketSnapshot, *, evaluation_datetime: datetime) -> MarketSnapshot:
    """Return ``market`` with the A17-1 GMP cutoff applied to its GMP block.

    A block the builder already classified as missing or stale (absent, no or
    unparseable as-of, beyond the configured age, or more than one hour ahead)
    keeps the builder's classification and reason. A ``FRESH`` GMP block is
    demoted to ``STALE`` when its timestamp is later than the evaluation
    timestamp, or when eligibility cannot be established. Like the builder's
    reasons, the reason text is independent of the evaluation clock, so it
    does not make the result hash depend on the wall clock.
    """
    block = market.block(GMP_BLOCK_NAME)
    if block is None or block.status != MARKET_FRESH:
        return market

    observed = explicit_offset_instant(block.as_of)
    if observed is None:
        reason = (
            f"block as-of {block.as_of!r} has no explicit UTC offset, so its time "
            "relative to the evaluation cannot be established"
        )
    elif evaluation_datetime.tzinfo is None or evaluation_datetime.utcoffset() is None:
        reason = "the evaluation timestamp has no timezone, so the GMP cutoff cannot be applied"
    elif observed > evaluation_datetime:
        # Same wording the builder uses for blocks more than one hour ahead:
        # for GMP there is no future allowance at all.
        reason = f"block as-of {block.as_of} is in the future relative to the evaluation"
    else:
        return market

    demoted = replace(block, status=MARKET_STALE, reason=reason)
    return replace(market, blocks=tuple(demoted if b is block else b for b in market.blocks))


__all__ = ["GMP_BLOCK_NAME", "apply_gmp_cutoff", "explicit_offset_instant"]
