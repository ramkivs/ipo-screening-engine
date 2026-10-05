"""Phase 6A: Trading calendar and observation window resolution.

Handles calendar horizon expansion (1W=7d, 1M=30d, 6M=180d) and deterministic
clamping to the latest preceding trading day.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Collection, Optional, Set, Tuple

from .models import Horizon

# Standard calendar day offsets defined by Phase 6A Decision D-3
HORIZON_CALENDAR_DAYS = {
    Horizon.W1.value: 7,
    Horizon.M1.value: 30,
    Horizon.M6.value: 180,
    "1W": 7,
    "1M": 30,
    "6M": 180,
}


def parse_iso_date(d: str | date) -> date:
    """Parse date from string or date object into datetime.date."""
    if isinstance(d, date):
        return d
    # Accept YYYY-MM-DD
    text = str(d).strip().split("T")[0]
    return datetime.strptime(text, "%Y-%m-%d").date()


def format_iso_date(d: date) -> str:
    """Format datetime.date into ISO YYYY-MM-DD string."""
    return d.strftime("%Y-%m-%d")


def compute_target_date(listing_date: str | date, horizon: str) -> str:
    """Compute the nominal calendar target date for a given horizon.

    1W = listing_date + 7 calendar days
    1M = listing_date + 30 calendar days
    6M = listing_date + 180 calendar days
    """
    base_date = parse_iso_date(listing_date)
    h_str = str(horizon).upper()
    if h_str not in HORIZON_CALENDAR_DAYS:
        raise ValueError(f"unsupported observation horizon: {horizon!r}")
    offset_days = HORIZON_CALENDAR_DAYS[h_str]
    target = base_date + timedelta(days=offset_days)
    return format_iso_date(target)


def is_trading_day(target_date: str | date, available_dates: Optional[Collection[str]] = None) -> bool:
    """Check if target_date is a valid trading day.

    If available_dates is supplied (from the price dataset), date must exist in it.
    Otherwise, defaults to weekday (Monday=0 to Friday=4).
    """
    d = parse_iso_date(target_date)
    d_str = format_iso_date(d)
    if available_dates is not None:
        return d_str in available_dates
    # Fallback to weekday check (0=Mon, 4=Fri)
    return d.weekday() < 5


def previous_trading_day(
    target_date: str | date,
    available_dates: Optional[Collection[str]] = None,
    max_lookback_days: int = 30,
) -> str:
    """Find the latest preceding valid trading day strictly before or on target_date.

    If target_date is a trading day, returns target_date.
    Otherwise rolls backward day by day until a trading day is found.
    """
    curr = parse_iso_date(target_date)
    for _ in range(max_lookback_days):
        if is_trading_day(curr, available_dates):
            return format_iso_date(curr)
        curr -= timedelta(days=1)
    raise ValueError(f"no valid trading day found within {max_lookback_days} days preceding {target_date}")


def resolve_observation_date(
    listing_date: str | date,
    horizon: str,
    available_dates: Optional[Collection[str]] = None,
) -> Tuple[str, str]:
    """Resolve nominal target date and actual clamped observation date.

    Returns:
        (target_observation_date, actual_observation_date)
    """
    target_str = compute_target_date(listing_date, horizon)
    actual_str = previous_trading_day(target_str, available_dates=available_dates)
    return target_str, actual_str
