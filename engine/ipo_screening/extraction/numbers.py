"""Indian number formatting, accounting negative values and currency unit detection.

Indian mainboard prospectuses use the Indian numbering system (e.g. 1,23,456.78
or 15,00,000 shares) and standard accounting conventions where negative numbers
are enclosed in parentheses like (1,234.56). Undisclosed figures are marked with
bracketed bullet points like [●].
"""

from __future__ import annotations

import re
from typing import Optional, Tuple


# Regex for Indian numbers: digits with optional commas and optional decimal
_NUMBER_RE = re.compile(
    r"""
    ^
    \s*
    (?P<sign>[-+])?
    (?P<paren>\()?
    \s*
    (?:₹|Rs\.?|INR)?
    \s*
    (?P<integral>\d{1,3}(?:,\d{2,3})*|\d+)
    (?:\.(?P<fractional>\d+))?
    \s*
    (?P<close_paren>\))?
    \s*
    $
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Undisclosed / bracketed markers
_UNDISCLOSED_RE = re.compile(r"\[[●•\*\.\s\-_]+\]|^\[\s*\]$|^\s*[-—–]\s*$|^\b(?:NIL|N\.A\.|NOT\s+APPLICABLE)\b", re.IGNORECASE)


def is_undisclosed_marker(text: str) -> bool:
    """Return True if text represents an undisclosed or missing placeholder like [●]."""
    if not text:
        return True
    return bool(_UNDISCLOSED_RE.search(text.strip()))


def parse_indian_number(text: Optional[str]) -> Optional[float]:
    """Parse an Indian-formatted number into a Python float.

    Handles:
      * Indian grouped commas: "14,500.00", "15,00,000", "33,867.73"
      * Accounting negatives: "(1,234.56)", "(45.00)" -> -1234.56, -45.0
      * Explicit negative signs: "-123.45"
      * Embedded currency symbols: "₹ 14,500.00", "Rs. 10/-"
      * Undisclosed markers: "[●]", "[-]", "NIL" -> None
    """
    if text is None:
        return None
    cleaned = text.strip()
    if not cleaned or is_undisclosed_marker(cleaned):
        return None

    # Strip trailing '/-' common in Indian share face value like '₹10/-'
    cleaned = re.sub(r"/-\s*$", "", cleaned)
    # Remove currency prefixes
    cleaned = re.sub(r"^(?:₹|Rs\.?|INR)\s*", "", cleaned, flags=re.IGNORECASE)

    match = _NUMBER_RE.match(cleaned)
    if not match:
        return None

    groups = match.groupdict()
    integral_str = groups["integral"].replace(",", "")
    fractional_str = groups.get("fractional") or ""
    full_str = f"{integral_str}.{fractional_str}" if fractional_str else integral_str

    try:
        val = float(full_str)
    except ValueError:
        return None

    is_negative = (
        groups.get("sign") == "-"
        or (groups.get("paren") == "(" and groups.get("close_paren") == ")")
    )
    return -val if is_negative else val


# Patterns for currency unit detection
_UNIT_PATTERNS = (
    (re.compile(r"\b(?:amount\s+in\s+lakhs?|in\s+lakhs?|₹\s*in\s*lakhs?|rs\.?\s*in\s*lakhs?)\b", re.IGNORECASE), "INR_LAKHS"),
    (re.compile(r"\b(?:amount\s+in\s+crores?|in\s+crores?|₹\s*in\s*crores?|rs\.?\s*in\s*crores?)\b", re.IGNORECASE), "INR_CRORES"),
    (re.compile(r"\b(?:amount\s+in\s+millions?|in\s+millions?|₹\s*in\s*millions?)\b", re.IGNORECASE), "INR_MILLIONS"),
    (re.compile(r"\b(?:amount\s+in\s+billions?|in\s+billions?|₹\s*in\s*billions?)\b", re.IGNORECASE), "INR_BILLIONS"),
    (re.compile(r"\b(?:amount\s+in\s+thousands?|in\s+thousands?|₹\s*in\s*thousands?)\b", re.IGNORECASE), "INR_THOUSANDS"),
)


def detect_currency_unit(header_text: Optional[str]) -> Optional[str]:
    """Detect the monetary reporting unit declared in a table header or section."""
    if not header_text:
        return None
    for pattern, unit in _UNIT_PATTERNS:
        if pattern.search(header_text):
            return unit
    return None
