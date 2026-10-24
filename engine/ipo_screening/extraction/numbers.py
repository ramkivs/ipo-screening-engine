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
_UNDISCLOSED_RE = re.compile(
    r"\[[●•\*\.\s\-_]+\]|\[\s*â\s*\]|\[[^a-zA-Z0-9\s]{1,4}\]|^\[\s*\]$|^\s*[-—–]\s*$|^(?:NIL|N/?A\.?|N\.A\.|NOT\s+APPLICABLE)$",
    re.IGNORECASE,
)


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


# Header forms that declare the unit of the table that follows.  They are
# tried before the bare ``in <unit>`` forms because a *statement header* is
# evidence about every number on the page, whereas a stray "in millions" in
# body prose is only a statement about one figure.
#
# Paras RHP (2026-10-24): every restated statement is captioned
# "(All amounts are in INR million, unless otherwise stated)" and the KPI
# tables say "Amount (\u20b9 million)".  Neither was recognised -- the former
# because only "in millions"/"\u20b9 in millions" were accepted, the latter
# because the leading word boundary cannot match between "(" and "\u20b9",
# which is not a word character.  The whole restated financial information
# was therefore booked as INR_LAKHS and every monetary value was understated
# tenfold relative to the issue amounts, which are normalised separately.
_UNIT_WORDS = {
    "lakh": "INR_LAKHS",
    "crore": "INR_CRORES",
    "million": "INR_MILLIONS",
    "billion": "INR_BILLIONS",
    "thousand": "INR_THOUSANDS",
}
_UNIT_HEADER = re.compile(
    r"\b(?:amounts?|figures?|sums?)\s*(?:are\s*|is\s*)?(?:stated\s*|expressed\s*|presented\s*)?"
    r"in\s+(?:inr|rs\.?|\u20b9)?\s*(lakhs?|crores?|millions?|billions?|thousands?)\b",
    re.IGNORECASE,
)
_UNIT_PAREN = re.compile(
    r"\(\s*(?:in\s+)?(?:inr|rs\.?|\u20b9)\s*(?:in\s*)?(lakhs?|crores?|millions?|billions?|thousands?)\s*\)",
    re.IGNORECASE,
)

# Patterns for currency unit detection
_UNIT_PATTERNS = (
    (re.compile(r"\b(?:amount\s+in\s+lakhs?|in\s+lakhs?|₹\s*in\s*lakhs?|rs\.?\s*in\s*lakhs?)\b", re.IGNORECASE), "INR_LAKHS"),
    (re.compile(r"\b(?:amount\s+in\s+crores?|in\s+crores?|₹\s*in\s*crores?|rs\.?\s*in\s*crores?)\b", re.IGNORECASE), "INR_CRORES"),
    (re.compile(r"\b(?:amount\s+in\s+millions?|in\s+millions?|₹\s*in\s+millions?|in\s+₹\s+millions?|₹\s+millions?)\b", re.IGNORECASE), "INR_MILLIONS"),
    (re.compile(r"\b(?:amount\s+in\s+billions?|in\s+billions?|₹\s*in\s*billions?)\b", re.IGNORECASE), "INR_BILLIONS"),
    (re.compile(r"\b(?:amount\s+in\s+thousands?|in\s+thousands?|₹\s*in\s*thousands?)\b", re.IGNORECASE), "INR_THOUSANDS"),
)


def detect_currency_unit(header_text: Optional[str]) -> Optional[str]:
    """Detect the monetary reporting unit declared in a table header or section."""
    if not header_text:
        return None
    for pattern in (_UNIT_HEADER, _UNIT_PAREN):
        match = pattern.search(header_text)
        if match:
            word = match.group(1).lower().rstrip("s")
            unit = _UNIT_WORDS.get(word)
            if unit:
                return unit
    for pattern, unit in _UNIT_PATTERNS:
        if pattern.search(header_text):
            return unit
    return None
