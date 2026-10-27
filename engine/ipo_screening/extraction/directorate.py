"""Changes-in-directorate reader (report section 26).

The RHP carries a table of board / KMP changes in "Our Management", headed
variously:

* ``Changes in our Board of Directors during last three years``
* ``Changes in the Board of Directors``
* ``Changes in our Key Managerial Personnel``

Two real layouts occur, and the column *order* differs between them:

Paras Healthcare, p. 346 --::

    Name | Designation (at the time of ...) | Date of appointment / change
    in designation / cessation | Reason
    Ramesh Abhishek  Independent Director  July 12, 2024  Resignation due to ...

Vishal Nirmiti, p. 306 --::

    Name of Director | Appointment/Change/Cessation | Reason
    Rajgopal Shankarlal Gilada April 16, 2024 Cessation as Non-Executive
    Director for pre-occupation and personal reasons

So the reader does not assume a column count or order.  It anchors rows on
the **date**, which both layouts place between the person and the reason,
and then splits the text before the date into name + designation:

* the trailing designation phrase (``Independent Director``,
  ``Additional Director``, ``Chief Financial Officer`` ...) is peeled off the
  name, when the source supplies one;
* a wrapped cell (``... for pre-`` / ``occupation and personal reasons``) is
  re-joined by taking every line between two dated rows as the continuation
  of the earlier row's reason.

Every row that the reader cannot date is dropped from the event list rather
than guessed at, and its presence is reported so the caller can mark coverage
PARTIAL instead of pretending the table was fully read.

The 24-month window is applied in :func:`count_exits` against an explicit
anchor date supplied by the caller -- the engine never uses ``date.today()``
for this, so a saved canonical record re-derives the same count.
"""

from __future__ import annotations

import calendar
import re
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
_MONTH_ALT = "|".join(m.capitalize() for m in _MONTHS)

# "July 12, 2024" / "July 12 2024"
_MONTH_DAY_YEAR = re.compile(
    rf"\b(?P<month>{_MONTH_ALT})\.?\s+(?P<day>\d{{1,2}})\s*,?\s*(?P<year>20\d\d)\b",
    re.IGNORECASE,
)
# "12 July 2024"
_DAY_MONTH_YEAR = re.compile(
    rf"\b(?P<day>\d{{1,2}})\s+(?P<month>{_MONTH_ALT})\.?\s*,?\s*(?P<year>20\d\d)\b",
    re.IGNORECASE,
)
# "12/07/2024" and "12-07-2024"
_NUMERIC_DATE = re.compile(r"\b(?P<day>\d{1,2})[/-](?P<month>\d{1,2})[/-](?P<year>20\d\d)\b")


def find_date(text: str) -> Optional[Tuple[date, int, int]]:
    """First date in ``text`` as ``(value, start, end)``, or None.

    Ambiguous numeric forms (day and month both <= 12) are read day-first,
    which is the convention in every RHP table examined.
    """
    best: Optional[Tuple[date, int, int]] = None
    for pattern in (_MONTH_DAY_YEAR, _DAY_MONTH_YEAR):
        for match in pattern.finditer(text):
            month = _MONTHS.get(match.group("month").lower().rstrip("."))
            if not month:
                continue
            try:
                value = date(int(match.group("year")), month, int(match.group("day")))
            except ValueError:
                continue
            candidate = (value, match.start(), match.end())
            if best is None or candidate[1] < best[1]:
                best = candidate
            break
    for match in _NUMERIC_DATE.finditer(text):
        try:
            value = date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
        except ValueError:
            continue
        candidate = (value, match.start(), match.end())
        if best is None or candidate[1] < best[1]:
            best = candidate
        break
    return best


def find_all_dates(text: str) -> List[Tuple[date, int, int]]:
    """Every date in ``text`` as ``(value, start, end)``, left to right.

    The RHP's table cells are extracted line by line, so one physical line can
    carry several rows (Vishal Nirmiti p. 319 packs the whole KMP table into
    long lines).  Rows are therefore located on *all* dates in the block, not
    one per line.
    """
    found: List[Tuple[date, int, int]] = []
    spans: List[Tuple[int, int]] = []
    for pattern in (_MONTH_DAY_YEAR, _DAY_MONTH_YEAR, _NUMERIC_DATE):
        for match in pattern.finditer(text):
            if any(not (match.end() <= a or match.start() >= b) for a, b in spans):
                continue
            if pattern is _NUMERIC_DATE:
                month, day = int(match.group("month")), int(match.group("day"))
            else:
                month = _MONTHS.get(match.group("month").lower().rstrip("."))
                day = int(match.group("day"))
                if not month:
                    continue
            try:
                value = date(int(match.group("year")), month, day)
            except ValueError:
                continue
            found.append((value, match.start(), match.end()))
            spans.append((match.start(), match.end()))
    return sorted(found, key=lambda item: item[1])


# ---------------------------------------------------------------------------
# Designations and events
# ---------------------------------------------------------------------------

# Longest first: "Joint Managing Director" must win over "Managing Director".
_DESIGNATIONS: Tuple[str, ...] = (
    "joint managing director",
    "managing director",
    "whole-time director",
    "whole time director",
    "executive director",
    "non-executive director",
    "non executive director",
    "independent director",
    "additional director",
    "nominee director",
    "alternate director",
    "chairman and managing director",
    "chairman",
    "director",
    "chief financial officer",
    "chief executive officer",
    "chief operating officer",
    "company secretary",
    "key managerial personnel",
    "general manager",
    "senior management",
)
_DESIGNATION_TAIL = re.compile(
    r"(?P<role>"
    r"(?:(?:joint\s+|whole[\s-]?time\s+|managing\s+|executive\s+|non[\s-]?executive\s+|"
    r"independent\s+|additional\s+|nominee\s+|alternate\s+|deputy\s+|senior\s+|assistant\s+|vice\s+)*"
    r"(?:managing\s+director|director|chairman(?:\s+and\s+managing\s+director)?|chairperson))"
    r"|(?:chief\s+[a-z]+\s+officer)"
    r"|(?:company\s+secretary(?:\s+and\s+compliance\s+officer)?)"
    r"|(?:compliance\s+officer)"
    r"|(?:(?:senior\s+|executive\s+|assistant\s+|deputy\s+|vice\s+)*president"
    r"(?:(?:\s*[-\u2013]\s*[^,;]{2,70})|(?:\s+of\s+[A-Za-z][A-Za-z&\s]{0,30})"
    r"|(?:,\s*[A-Za-z][A-Za-z&\s]{1,40}))?)"
    r"|(?:(?:deputy\s+|assistant\s+)?general\s+manager(?:\s*-\s*[^,;]{2,70})?)"
    r"|(?:head\s*[-\u2013]?\s*[^,;]{0,70})"
    r"|(?:key\s+managerial\s+personnel)"
    r")\s*$",
    re.IGNORECASE,
)

_EXIT_EVENTS = frozenset({"resignation", "cessation", "retirement", "term_expiry"})


def classify_event(reason: str) -> str:
    """Map the filed reason sentence onto an event type.

    The most specific statement wins: a resignation stays a resignation even
    when the sentence also mentions the cessation it causes.  A bare
    "cessation" is *not* promoted to "resignation" -- the source did not say
    the person resigned (Paras p. 346 records "Cessation as Non-Executive
    Director for pre-occupation and personal reasons").
    """
    low = (reason or "").lower()
    if "resign" in low:
        return "resignation"
    if "retire" in low or "superannuat" in low:
        return "retirement"
    if re.search(
        r"term\s+(?:of\s+(?:his|her|their)\s+office\s+)?(?:expired|expiry)|"
        r"expiry\s+of\s+(?:the\s+|his\s+|her\s+)?term|"
        r"completion\s+of\s+(?:his|her|their)\s+term|"
        r"termination\s+of\s+(?:the\s+|his\s+|her\s+)?term|"
        r"end\s+of\s+(?:the\s+|his\s+|her\s+)?term",
        low,
    ):
        return "term_expiry"
    if "cessation" in low or "ceased" in low:
        return "cessation"
    if re.search(r"appoint|regularis|regulariz|designat|induct|elevat", low):
        return "appointment"
    return "other"


def is_exit(event: Dict[str, Any]) -> bool:
    return str(event.get("event") or "") in _EXIT_EVENTS


def strip_footnote_marker(name: str) -> str:
    """Drop a ``(1)`` / ``(2)`` footnote marker from a name cell.

    The marker sits against the surname (``Usha Rajeev(1)``), followed by the
    designation column, so it is not always at the end of the cell.
    """
    return re.sub(r"\s*\(\d{1,2}\)", " ", (name or "")).strip()


_ROLE_FROM_REASON = re.compile(
    r"(?:as|to)\s+(?:an?\s+)?(?P<role>" + "|".join(re.escape(d) for d in _DESIGNATIONS) + r")",
    re.IGNORECASE,
)


def role_from_reason(reason: str) -> Optional[str]:
    """The designation named in the reason, when the source carries no column.

    Vishal Nirmiti p. 306 has no designation column: the role exists only
    inside the reason ("Cessation as Non-Executive Director for ...").
    """
    match = _ROLE_FROM_REASON.search(reason or "")
    return match.group("role").lower() if match else None


def _split_name_role(cell: str) -> Tuple[Optional[str], Optional[str]]:
    """Peel a trailing designation off the name cell."""
    cell = strip_footnote_marker(" ".join((cell or "").split()))
    cell = re.sub(r"[,;:\-\u2013]+$", "", cell).strip()
    if not cell:
        return None, None
    role: Optional[str] = None
    match = _DESIGNATION_TAIL.search(cell)
    if match:
        role = match.group("role").strip()
        cell = cell[: match.start()].strip(" ,;:-")
    role = role.lower() if role else None
    name = cell or None
    return name, role


# Tokens that show a "name" fragment is really a sentence continuation.
_NOT_A_NAME = frozenset(
    "the and of for due as on at held was were has have had his her their our "
    "with from by to in is are be been under section act reason reasons "
    "appointment cessation resignation regularisation appointment, upon effective".split()
)
_STOP_LINE = re.compile(
    r"^(?:(?:\d{1,3})|(?:shareholding\s+of\s+our\s+directors)|(?:other\s+confirmations)|"
    r"(?:corporate\s+governance)|(?:committees?\s+of\s+our\s+board)|(?:our\s+promoters)|"
    r"(?:interests?\s+of\s+our\s+directors)|(?:compensation\s+(?:of|payable))|"
    r"(?:payments?\s+(?:or|and)\s+benefits)|(?:equity\s+shareholding\s+of\s+our)|"
    r"(?:name\s+of\s+the\s+directors)|(?:details\s+of\s+the\s+directors))",
    re.IGNORECASE,
)
_FOOTNOTE_LINE = re.compile(r"^\(\d{1,2}\)\s")
_SECTION_END = re.compile(
    r"^(?:shareholding\s+of\s+our|shareholding\s+of\s+key|other\s+confirmations|"
    r"corporate\s+governance|interests?\s+of\s+our|interests?\s+of\s+key|"
    r"committees?\s+of\s+our\s+board|our\s+promoters|relationship)",
    re.IGNORECASE,
)
_HEADER_LINE = re.compile(
    r"^name\b[\s\S]{0,140}?(?:reason|date\s+of|appointment\s*/|designation)", re.IGNORECASE
)


def _looks_like_name(text: Optional[str]) -> bool:
    if not text:
        return False
    text = text.strip()
    if not (2 <= len(text) <= 70):
        return False
    if re.search(r"\d", text):
        return False
    text = re.sub(r"[*\u2020\u2021#]+\s*$", "", text).strip(" ,;.")
    tokens = text.split()
    if not tokens or len(tokens) > 7:
        return False
    if any(tok.lower().strip(".,;:()") in _NOT_A_NAME for tok in tokens):
        return False
    return bool(re.search(r"[A-Za-z]{2}", text))


# Tokens that end the backwards walk that recovers a person's name: role and
# reason vocabulary, plus the conjunctions and prepositions that appear inside
# a filed reason.  A hyphenated token also ends the walk ("Whole-Time").
_STOP_TOKENS = frozenset(
    """
    in to and as for of the under due with from by on at within upon
    change changes cessation resignation appointment appointments regularisation
    regularization retirement expiry removal death induction redesignation
    designation reason reasons particulars details effect
    director directors officer secretary chairman chairperson manager management
    president division head whole-time time managing executive independent
    additional nominee non-executive joint chief financial operating general vice
    business development contracts infrastructure accounts taxation compliance
    personnel section act companies company board limited private ltd india
    operations operation finance sales marketing technology projects project works
    plant commercial legal human resources quality safety logistics supply chain
    engineering production procurement materials information systems administration
    admin corporate strategy secretarial treasury risk audit internal controls
    """.split()
)

_HONORIFICS = frozenset(
    {"mr", "mrs", "ms", "dr", "shri", "smt", "prof", "professor", "capt", "lt", "sri"}
)
_TABLE_HEADER = re.compile(
    r"\bname(?:\s+of\s+(?:the\s+)?(?:director|directors?|kmp|key\s+managerial\s+personnel))?"
    r"[\s\S]{0,80}?\b(?:designation|date\s+of|appointment|reason|particulars)\b",
    re.IGNORECASE,
)


def _take_name_tail(prefix: str) -> Tuple[Optional[str], int]:
    """Recover a person's name from the tail of ``prefix``.

    Returns ``(name, start_index_in_prefix)``.  The walk goes backwards over
    capitalised, non-vocabulary tokens so it can stop exactly where the name
    begins, which lets the caller re-attach the preceding fragment to the
    previous row's reason (a wrapped cell) and take the row's reason as
    everything up to the *next* name.
    """
    tokens = [(m.start(), m.group(0)) for m in re.finditer(r"\S+", prefix)]
    taken: List[Tuple[int, str]] = []
    for pos, token in tokens[::-1]:
        core = re.sub(r"\(\d{1,2}\)", "", token)
        core = core.strip(".,;:()[]\u2019\u201c\u201d*\u2020\u2021#")
        if not core or "-" in core or "/" in core:
            break
        if core.lower() in _STOP_TOKENS:
            break
        if not re.fullmatch(r"[A-Z][A-Za-z.\u2019]*", core):
            break
        taken.append((pos, token))
        if len(taken) == 4:
            break
    if not taken:
        return None, len(prefix)
    taken.reverse()
    # An honorific opens the name: anything before it is the previous cell
    # ("... President, Network Solutions Mr. Daniel Bailey").
    for pos, (_, token) in enumerate(taken):
        if token.rstrip(".").lower() in _HONORIFICS and pos > 0:
            taken = taken[pos:]
            break
    name = " ".join(tok for _, tok in taken).strip(" ,;.")
    name = re.sub(r"\s*\(\d{1,2}\)", " ", name)
    name = name.strip(" ,;.*\u2020\u2021#")
    name = re.sub(r"\*+\s*$", "", name).strip()
    if not _looks_like_name(name):
        return None, len(prefix)
    return name, taken[0][0]


_TITLE_WORDS = _STOP_TOKENS | frozenset(
    """
    sleeper sleepers infra supply chain human resources business management
    transformation information technology operations group compliance
    key managerial personnel vice president executive senior general manager
    head assistant deputy joint managing whole time director independent
    non executive additional nominee alternate chairman chairperson
    """.split()
)


def _role_before(prefix: str) -> Tuple[Optional[str], int]:
    """Designation at the tail of ``prefix`` and the index where it starts.

    Only *title vocabulary* is accepted, and only when it forms the tail of
    the prefix: a title is a suffix made entirely of title words
    ("Company Secretary and Compliance Officer", "Executive Vice President of
    Operations").  A looser pattern (any characters up to the end) matched
    reason prose as if it were a designation -- Paras p. 357's
    "... Resignation as the Group Head Human Resources due to personal
    commitments Dr. Santy N Sajan" was read as the role
    "Head Human Resources due to personal commitments Dr. Santy N Sajan".
    """
    tokens = [(m.start(), m.group(0)) for m in re.finditer(r"\S+", prefix)]
    taken: List[Tuple[int, str]] = []
    for pos, token in tokens[::-1]:
        core = re.sub(r"\(\d{1,2}\)", "", token)
        core = core.strip(".,;:()[]\u2019\u201c\u201d-")
        if not core or core.lower() not in _TITLE_WORDS:
            break
        taken.append((pos, token))
        if len(taken) == 10:
            break
    if not taken:
        return None, len(prefix)
    taken.reverse()
    role = " ".join(tok for _, tok in taken).strip(" ,;:.")
    role = re.sub(r"\s+", " ", role)
    if not role or not re.search(r"[A-Za-z]{3}", role):
        return None, len(prefix)
    return role.lower(), taken[0][0]


def parse_changes_table(block: str) -> Dict[str, Any]:
    """Parse one changes-in-directorate block.

    Returns ``{"events": [...], "rows": n, "undated_exit_rows": n,
    "header_seen": bool}``.  Events are ordered as the filing presents them;
    each is ``{name, role, event, date (ISO), reason}``.

    Rows are anchored on the date tokens.  For each row the reader walks back
    from the date to recover the person's name and designation, and takes the
    reason as everything after that date up to the start of the *next* name --
    so a reason that wraps onto the next line (Vishal p. 306) and a table that
    is extracted as long multi-row lines (Vishal p. 319) are both read without
    any column arithmetic or fixed column count.
    """
    lines: List[str] = []
    rows_started = False
    for line in (block or "").splitlines():
        flat = " ".join(line.split())
        if not flat:
            continue
        if rows_started and (
            _FOOTNOTE_LINE.match(flat)
            or re.match(r"^notes?\s*[:.]", flat, re.IGNORECASE)
            or _SECTION_END.match(flat)
        ):
            # Numbering footnotes and "Notes:" lines sit under the table and
            # carry dates of their own (AGM dates, board-resolution dates);
            # they are not rows.  The same goes for the next section heading.
            break
        if find_date(flat) is not None:
            rows_started = True
        lines.append(line)
    text = re.sub(r"\s+", " ", "\n".join(lines)).strip()
    header_seen = bool(_TABLE_HEADER.search(text))
    dates = find_all_dates(text)

    rows: List[Dict[str, Any]] = []
    for idx, (value, start, end) in enumerate(dates):
        prefix_start = dates[idx - 1][2] if idx else 0
        prefix = text[prefix_start:start]
        role, role_start = _role_before(prefix)
        name, name_start_rel = _take_name_tail(prefix[:role_start])
        name_start = prefix_start + name_start_rel if name else end
        if name is None and role is None:
            # Nothing identifies a person or a designation: this is prose that
            # merely carries a date (a circular's issue date, an AGM date in a
            # footnote), not a directorate row.
            continue
        rows.append(
            {"value": value, "end": end, "name": name, "role": role, "name_start": name_start}
        )

    events: List[Dict[str, Any]] = []
    for pos, row in enumerate(rows):
        reason_end = rows[pos + 1]["name_start"] if pos + 1 < len(rows) else len(text)
        reason = text[row["end"]:reason_end].strip(" ,;.")
        reason = re.sub(r"\s+", " ", reason).strip()
        if len(reason) > 300:
            reason = reason[:300].rsplit(" ", 1)[0]
        event = classify_event(reason)
        events.append(
            {
                "name": row["name"],
                "role": row["role"] or role_from_reason(reason),
                "event": event,
                "date": row["value"].isoformat(),
                "reason": reason or None,
            }
        )

    undated_exit_rows = 0
    for line in lines:
        flat = " ".join(line.split())
        if not flat or find_date(flat) is not None:
            continue
        if classify_event(flat) not in _EXIT_EVENTS:
            continue
        prefix = re.split(
            r"\bresign|\bcessation|\bceased|\bretire|\bterm\s+of",
            flat,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        if _looks_like_name(prefix) and len(flat.split()) <= 16:
            undated_exit_rows += 1

    return {
        "events": events,
        "rows": len(dates),
        "undated_exit_rows": undated_exit_rows,
        "header_seen": header_seen,
    }


# ---------------------------------------------------------------------------
# The 24-month window
# ---------------------------------------------------------------------------


def minus_months(anchor: date, months: int) -> date:
    """``anchor`` shifted back by whole calendar months (clamped day)."""
    total = anchor.month - 1 - months
    year = anchor.year + total // 12
    month = total % 12 + 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def count_exits(
    events: Sequence[Dict[str, Any]], anchor: Optional[date], months: int = 24
) -> Optional[int]:
    """Exit events in the ``months`` window ending at ``anchor``, inclusive.

    ``None`` when the anchor is unknown: a missing evaluation date is not a
    zero and must not be scored as one.
    """
    if anchor is None:
        return None
    start = minus_months(anchor, months)
    count = 0
    for event in events or ():
        if not is_exit(event):
            continue
        raw = event.get("date")
        try:
            when = date.fromisoformat(str(raw))
        except (TypeError, ValueError):
            continue
        if start <= when <= anchor:
            count += 1
    return count
