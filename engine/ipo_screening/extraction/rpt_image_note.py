"""Related-party note reader for image-only (scanned) financial statements.

Proven defect (2026-10-26).  R.K. Fashion's restated financial statements are
image-only for PDF pp. 294-318, and its Note 31 "Related Party Disclosures"
lives at PDF pp. 308-309.  Each page carries one embedded image and roughly one
line of text (the printed page number), so every text-layer reader in the
package -- including the period-matrix reader of report section 30 -- returns
nothing there, and the disclosure was reported PARTIAL for that reason alone.

This module reads such a page the only way it can be read: bounded, offline OCR
of the page image, then a reconstruction of the table from *geometry*.  The
interesting part is not the OCR text but the cell boundaries: in these notes the
amounts are right-aligned inside columns that OCR's text boxes do not describe,
so binding a number to a column by the header word's position guesses (an
earlier attempt bound "Amount Borrowed" to a value that belongs to "Opening
Balance").  The reader therefore detects the table's **vertical rules** in the
rendered image -- the ruled columns of the printed table -- builds the column
bands from them, maps each header cell to the band that contains it, and binds
each amount to the band containing its own centre.  Every reconstructed row is
then checked against the block's own arithmetic (opening + additions -
reductions = closing) before its values are used.

Rules this reader keeps:

* a *balance* column (opening/closing balance) is never a transaction: a
  balance is a stock.  Only the transaction columns of a block (amount lent,
  amount borrowed, amount repaid, interest paid/received, purchases during the
  year, amount paid, the transaction column of a remuneration block, merger
  consideration paid) produce values;
* a value is emitted only from a cell whose OCR text has the shape of an amount
  (``12.34``, ``1,234.56``, ``(12.34)`` for a credit) at OCR confidence
  :data:`AMOUNT_CONFIDENCE` or better, whose box sits inside its column band,
  and whose row states its own period and party.  Anything else is counted as
  unread, never guessed, repaired, rescaled or rounded;
* a block is read only when it states a **control total** -- a balance column
  plus at least one movement column.  That is what makes each row checkable
  (opening + movements = closing, within :data:`ARITHMETIC_TOLERANCE`).  A
  block of purchases, payments, remuneration or merger consideration has no
  such control, so its cells are counted as unread rather than bound to a
  column on position alone; a block whose header names two quantities in one
  band (a missed dotted rule) is refused for the same reason;
* a period is a financial year from the block's own "Financial Year" column
  ("2025-26" -> ``FY2026``) or an interim cell the schedule prints as a date
  range ("April' 26 to June' 26" -> ``3M-2026-06-30``).  A row whose period
  cannot be established is unread;
* blocks are separated by their repeated header bands, so a page break or a
  second block cannot silently redefine a column;
* the reader reports what it established: ``DISCLOSED`` (every block mapped and
  every row reconciled), ``PARTIAL`` (the note was read, but some rows could not
  be bound to a column and a period, or did not reconcile) or ``UNREAD`` (no
  image-only related-party note was found).

The OCR models ship inside the pinned ``rapidocr`` wheel; nothing is downloaded,
and the scan is bounded by :data:`MAX_SCAN_PAGES` heading reads and
:data:`MAX_FULL_PAGES` full-page reads.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

# A value is only read when OCR is near-certain about the cell: a misread digit
# in an amount is indistinguishable from a correctly read one once bound to a
# column, so uncertain amounts are left unread (and counted) instead.
AMOUNT_CONFIDENCE = 0.94
# A cell below the read floor can still be admitted when the row's own control
# total proves it: an OCR figure that makes opening + movements = closing to the
# rupee is corroborated by the filing's arithmetic, not by proximity.
UNCERTAIN_CONFIDENCE = 0.80
MAX_SCAN_PAGES = 20
MAX_FULL_PAGES = 3
ROW_TOLERANCE = 9.0
RULE_DARK_FRACTION = 0.55
# A printed rule is one continuous stroke covering this share of the window;
# a line of text is a row of short strokes and never does (see ``_rule_rows``).
# The threshold is a share of the scan window rather than of the page, so a
# rule interrupted by a vertically merged label cell still qualifies while a
# densely set word inside one narrow column does not.
RULE_CONTINUITY = 0.55
ARITHMETIC_TOLERANCE = 0.15

# An amount cell always states two decimals in these notes.  A cell read as
# "480" where the filing prints "4.80" is not an amount: accepting it would
# turn an OCR slip into a value ten times too large, so it is left unread.
_NIL_CELL = re.compile(r"^[-\u2013\u2014.\u2022]+$")
_AMOUNT = re.compile(
    r"^\(?\d{1,3}(?:,\d{2,3})*\.\d{2}\)?$|^\(?\d+\.\d{2}\)?$"
)
_INTERIM = re.compile(r"apr[a-z]*[^0-9]{0,6}(\d{2})[^0-9]{0,12}jun[a-z]*[^0-9]{0,6}(\d{2})")
_UNIT = re.compile(r"in\s*(lakhs?|crores?|millions?|thousands?)", re.IGNORECASE)
_UNITS = {
    "lakhs": "INR_LAKHS", "lakh": "INR_LAKHS",
    "crores": "INR_CRORES", "crore": "INR_CRORES",
    "millions": "INR_MILLIONS", "million": "INR_MILLIONS",
    "thousands": "INR_THOUSANDS", "thousand": "INR_THOUSANDS",
}

_BALANCE_ROLES = frozenset({"opening_balance", "closing_balance"})
_ADDITION_ROLES = frozenset(
    {"loan_given", "loan_taken", "purchase_of_goods", "transaction_amount"}
)
_REDUCTION_ROLES = frozenset({"loan_repaid", "payment_made"})
_META_ROLES = frozenset({"party", "nature", "period", "meta"})
# Columns whose cells are amounts.  A balance column is a stock and is never a
# transaction; the movement columns are the only ones that can be.
_VALUE_ROLES = frozenset(
    {
        "opening_balance",
        "closing_balance",
        "loan_given",
        "loan_taken",
        "loan_repaid",
        "interest_paid",
        "interest_received",
        "purchase_of_goods",
        "payment_made",
        "transaction_amount",
        "merger_consideration",
        "rent_paid",
        "sale_of_goods",
        "sale_of_services",
    }
)

# Column role by the words a header cell carries, spaces and punctuation
# removed (OCR splits words freely).  Order matters: the first match wins.
_COLUMN_WORDS: Tuple[Tuple[str, str], ...] = (
    ("nameofthe", "party"),
    ("mergedcompany", "party"),
    ("nameof", "party"),
    ("relatedparty", "meta"),
    ("natureof", "nature"),
    ("particulars", "nature"),
    ("financialyear", "period"),
    ("yearofmerger", "period"),
    ("year", "period"),
    ("openingbalance", "opening_balance"),
    ("closingbalance", "closing_balance"),
    ("amountlend", "loan_given"),
    ("amountlent", "loan_given"),
    ("loanlend", "loan_given"),
    ("amountgiven", "loan_given"),
    ("amountborrowed", "loan_taken"),
    ("amounttaken", "loan_taken"),
    ("amountrepaid", "loan_repaid"),
    ("repayment", "loan_repaid"),
    ("interestpaid", "interest_paid"),
    ("interestreceived", "interest_received"),
    ("purchasesduringtheyear", "purchase_of_goods"),
    ("purchaseduringtheyear", "purchase_of_goods"),
    ("purchase", "purchase_of_goods"),
    ("amountpaid", "payment_made"),
    ("saleofproducts", "sale_of_goods"),
    ("saleofgoods", "sale_of_goods"),
    ("saleofservices", "sale_of_services"),
    ("salesduringtheyear", "sale_of_goods"),
    ("transactionduringtheyear", "transaction_amount"),
    ("transactionduringthe", "transaction_amount"),
    ("considerationpaid", "merger_consideration"),
    ("issueprice", "meta"),
    ("noofshares", "meta"),
)



# A cell that continues the party name printed above it: a corporate suffix
# ("Pvt.Ltd.*", "Limited)"), a footnote marker, or lower-case prose.
_PARTY_TAIL = re.compile(
    r"^(?:pvt|ltd|limited|llp|co\b|inc\b|&|and\b|\(|\.|-|\*)", re.IGNORECASE
)

_NATURE_SPLIT = re.compile(
    r"\b(loan\s+(?:taken|given|lend|repaid)|advance\s+given|advance|purchase|"
    r"sale\s+of\s+\w+|rendering\s+of\s+services?|remuneration|salary|"
    r"interest\s+(?:paid|received)|rent\s+paid)\b",
    re.IGNORECASE,
)


def split_party_nature(text: str) -> Tuple[str, str]:
    """Split a cell that carries both the party name and its nature.

    OCR returns a wide cell that straddles the party and nature columns as one
    item ("Valuable Vintrade Pvt.Ltd.*Loan Taken").  Keeping it whole would put
    the nature into the counterparty string for every later row, so the nature
    phrase is peeled off where it starts.
    """
    match = _NATURE_SPLIT.search(text or "")
    if not match or match.start() == 0:
        return (text or "").strip(), ""
    return text[: match.start()].strip(" *-"), text[match.start():].strip()


def _compact(text: str) -> str:
    return re.sub(r"[^0-9a-z]", "", (text or "").lower())


def _number(text: str) -> Optional[float]:
    compact = (text or "").replace(" ", "")
    if not compact or not _AMOUNT.match(compact):
        return None
    negative = compact.startswith("(") and compact.endswith(")")
    try:
        value = float(compact.strip("()").replace(",", ""))
    except ValueError:
        return None
    return -value if negative else value


def _period(text: str) -> Optional[str]:
    compact = re.sub(r"\s+", "", (text or "").lower()).replace("'", "")
    interim = _INTERIM.search(compact)
    if interim:
        return "3M-%04d-06-30" % (2000 + int(interim.group(1)))
    match = re.search(r"(20\d{2})\s*[-–]\s*(\d{2})", compact)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        year = start + 1 if end == (start + 1) % 100 else start
        return "FY%d" % year
    return None


def _category(nature: str) -> str:
    """Category of one transaction nature (shared vocabulary, report s.34)."""
    from .rpt_categories import classify_nature

    return classify_nature(nature) or "unclassified"


# The stems that name a *quantity* (a column whose cells are amounts or
# balances), derived from the column vocabulary instead of restated beside it:
# a stem added to ``_COLUMN_WORDS`` is visible to this check immediately, so the
# two can never disagree.
_VALUE_ROLE_STEMS: Tuple[Tuple[str, str], ...] = tuple(
    (stem, role)
    for stem, role in _COLUMN_WORDS
    if role != "party" and role not in _META_ROLES
)


def column_roles(header_words: Sequence[str]) -> List[str]:
    """Every value role the words seated above one column band name.

    A band whose header text names two different quantities is not one column:
    the rule that separated them was missed (a dotted or dashed rule is
    invisible to a dark-ink scan), so the band's amounts belong to two columns
    and cannot be bound to either.
    """
    joined = "".join(_compact(word) for word in header_words)
    if not joined:
        return []
    if any(stem in joined for stem in ("nameofthe", "mergedcompany", "nameof")):
        return ["party"]
    roles: List[str] = []
    for stem, role in _VALUE_ROLE_STEMS:
        if stem in joined and role not in roles:
            roles.append(role)
    return roles


def column_role(header_words: Sequence[str]) -> Optional[str]:
    """Role of one column band, from the header words printed above it.

    The longest matching stem wins: "Purchases during the year" is a purchase
    column, not a "year" column, and "Consideration paid during the Year" is
    merger consideration rather than a period.
    """
    joined = "".join(_compact(word) for word in header_words)
    if not joined:
        return None
    # The label columns name themselves first: "Name of the Related Party" is
    # the party column, not the generic "related party" wording.
    for stem in ("nameofthe", "mergedcompany", "nameof"):
        if stem in joined:
            return "party"
    for stem, role in (
        ("openingbalance", "opening_balance"),
        ("closingbalance", "closing_balance"),
    ):
        if stem in joined:
            return role
    matches = [(len(stem), role) for stem, role in _COLUMN_WORDS if stem in joined]
    if not matches:
        return None
    matches.sort(reverse=True)
    return matches[0][1]


def rows_of(items: Sequence[Dict[str, Any]], tolerance: float = ROW_TOLERANCE):
    """Group OCR items into visual rows, top to bottom, cells left to right."""
    rows: List[Dict[str, Any]] = []
    for item in sorted(items, key=lambda entry: (entry["y"], entry["x"])):
        if rows and abs(rows[-1]["y"] - item["y"]) <= tolerance:
            rows[-1]["cells"].append(item)
        else:
            rows.append({"y": item["y"], "cells": [item]})
    for row in rows:
        row["cells"].sort(key=lambda entry: entry["x"])
    return rows


def _dark(gray):
    import numpy as np

    return np.asarray(gray) < 160


def _merge_positions(positions: Sequence[float], gap: float = 2.0) -> List[float]:
    groups: List[List[float]] = []
    for position in positions:
        if groups and position - groups[-1][-1] <= gap:
            groups[-1].append(position)
        else:
            groups.append([position])
    return [sum(group) / len(group) for group in groups]


def _rule_rows(dark) -> List[int]:
    """Rows of a dark-pixel band that a printed *rule* occupies.

    A rule is one continuous stroke: it is dark across the whole window, with
    no gaps.  A line of densely set text (the word "Investment" centred in a
    narrow label column) is also mostly dark, so a plain dark-fraction test
    mistakes it for a cell boundary and splits a merged label cell in two --
    the merge is then lost and the label arrives truncated.  Requiring one
    long unbroken run separates the two physically: glyphs always leave white
    space between letters, a rule never does.
    """
    rows: List[int] = []
    if dark.size == 0:
        return rows
    width = dark.shape[1]
    need = max(4, int(round(width * RULE_CONTINUITY)))
    for index in range(dark.shape[0]):
        line = dark[index]
        if not line.any():
            continue
        # Longest run of consecutive dark pixels on this row.
        best = run = 0
        for value in line:
            run = run + 1 if value else 0
            if run > best:
                best = run
        if best >= need and line.mean() > RULE_DARK_FRACTION:
            rows.append(index)
    return rows


def horizontal_rules(gray, top: float, bottom: float, left: int, right: int) -> List[float]:
    """y positions of the table's horizontal rules across ``left..right``.

    These are the printed row boundaries.  A cell that is *merged* vertically
    (a party name printed once against four year rows) has no rule inside it,
    which is how a merged cell's real extent is recovered: from the rules that
    cross the label column, not from where OCR happened to put the text.
    """
    dark = _dark(gray)
    height, width = dark.shape
    top = max(0, min(int(top), height - 1))
    bottom = max(top + 1, min(int(bottom), height))
    left = max(0, min(int(left), width - 1))
    right = max(left + 1, min(int(right), width))
    band = dark[top:bottom, left:right]
    return _merge_positions([float(top + index) for index in _rule_rows(band)])


def crosses(gray, y: float, left: int, right: int, tolerance: int = 2) -> bool:
    """True when a printed rule sits at ``y`` across ``left..right``."""
    dark = _dark(gray)
    height, width = dark.shape
    top = int(max(0, y - tolerance))
    bottom = int(min(height, y + tolerance + 1))
    left = max(0, min(int(left), width - 1))
    right = max(left + 1, min(int(right), width))
    if bottom <= top:
        return False
    return bool(_rule_rows(dark[top:bottom, left:right]))


def _overlap(band: Dict[str, Any], item: Dict[str, Any]) -> float:
    """Vertical overlap between a printed row and an OCR item's box."""
    top = float(item.get("y", 0.0))
    bottom = float(item.get("y2", top) or top)
    if bottom <= top:
        return 1.0 if band["top"] <= top < band["bottom"] else 0.0
    return max(0.0, min(bottom, band["bottom"]) - max(top, band["top"]))


def row_bands(gray, top: float, bottom: float, left: int, right: int) -> Optional[List[Dict[str, Any]]]:
    """Printed rows of one block, rebuilt from its horizontal rules.

    Returns ``None`` when the page prints no usable horizontal rules (a table
    whose rules are dotted, or a text block), so the caller can keep its
    OCR-row reading instead of guessing at row boundaries.
    """
    rules = horizontal_rules(gray, top, bottom, left, right)
    inside = [rule for rule in rules if top - 1 <= rule <= bottom]
    if len(inside) < 3:
        return None
    edges = list(inside)
    if edges[0] - top > 3.0:
        edges = [float(top)] + edges
    if bottom - edges[-1] > 3.0:
        edges = edges + [float(bottom)]
    bands: List[Dict[str, Any]] = []
    for lower, upper in zip(edges, edges[1:]):
        if upper - lower >= 4.0:
            bands.append({"top": lower, "bottom": upper})
    return bands or None


def vertical_rules(gray, top: int, bottom: int) -> List[float]:
    """x positions of the table's vertical rules between two y bounds.

    A rule is a column of the rendered image that is dark for most of the
    table's height.  Neighbouring dark columns are merged, so one printed rule
    yields one boundary even where anti-aliasing spreads it over a few pixels.
    """
    import numpy as np

    if bottom - top < 20:
        return []
    band = (np.asarray(gray) < 160)[top:bottom, :]
    fraction = band.mean(axis=0)
    dark_columns = [int(x) for x in np.flatnonzero(fraction > RULE_DARK_FRACTION)]
    rules: List[List[int]] = []
    for x in dark_columns:
        if rules and x - rules[-1][-1] <= 2:
            rules[-1].append(x)
        else:
            rules.append([x])
    return [float(sum(group)) / len(group) for group in rules]


_HEADER_STEMS = (
    "nameof", "natureof", "particulars", "financialyear", "yearofmerger",
    "openingbalance", "closingbalance", "amount", "interest", "purchase",
    "sale", "transaction", "consideration", "issueprice", "noofshares",
    "mergedcompany", "repaid",
)


def header_like(row: Dict[str, Any], min_stems: int = 2) -> bool:
    """True for a row of column headings.

    A heading row carries the table's column words and no amount.  A data row
    can carry one of those words too (a "Purchase" nature cell), so a row that
    states a financial year or an amount is never a heading: headings name the
    year column, they do not fill it.
    """
    if not row["cells"]:
        return False
    if any(_number(cell["text"]) is not None for cell in row["cells"]):
        return False
    if any(_period(cell["text"]) for cell in row["cells"]):
        return False
    joined = "".join(_compact(cell["text"]) for cell in row["cells"])
    if len(joined) > 220:
        return False
    stems = {stem for stem in _HEADER_STEMS if stem in joined}
    return len(stems) >= min_stems


def _blocks(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Header bands and the row ranges they govern."""
    blocks: List[Dict[str, Any]] = []
    index = 0
    while index < len(rows):
        row = rows[index]
        if not header_like(row):
            index += 1
            continue
        # A header can print on two lines; absorb the heading rows directly
        # beneath it, which is where a second header line's column words sit.
        header_rows = [row]
        probe = index + 1
        while probe < len(rows) and len(header_rows) < 3:
            later = rows[probe]
            if header_like(later, min_stems=1) and later["y"] - header_rows[-1]["y"] <= 30:
                header_rows.append(later)
                probe += 1
            else:
                break
        blocks.append(
            {
                "header_rows": header_rows,
                "header_y": header_rows[0]["y"],
                "top": header_rows[-1]["y"] + 6.0,
                "bottom": None,
                "cells": [cell for entry in header_rows for cell in entry["cells"]],
            }
        )
        index = probe
    for current, following in zip(blocks, blocks[1:]):
        current["bottom"] = following["header_y"] - 4.0
    if blocks:
        # The last block ends with its last row, not with the page: a footnote
        # or a page number far below the table must not dilute the
        # vertical-rule scan.  Walk down while the rows stay in one run.
        last = blocks[-1]
        bottom = last["top"]
        previous = last["header_y"]
        for row in rows:
            if row["y"] <= last["header_y"]:
                continue
            if row["y"] - previous > 60.0:
                break
            previous = row["y"]
            bottom = row["y"]
        last["bottom"] = bottom + 24.0
    return blocks


def _column_of(centre: float, bands: Sequence[Tuple[float, float]]) -> Optional[int]:
    for position, (left, right) in enumerate(bands):
        if left <= centre < right:
            return position
    return None


def _spans(gray, top: float, bottom: float, left: int, right: int) -> List[Tuple[float, float]]:
    """Intervals between the rules that cross one column.

    A merged cell has no rule inside it, so the interval between its own
    crossing rules *is* the cell's extent.
    """
    edges = [rule for rule in horizontal_rules(gray, top, bottom, left, right) if top - 1 <= rule <= bottom]
    if len(edges) < 2:
        return [(float(top), float(bottom))]
    if edges[0] - top > 3.0:
        edges = [float(top)] + edges
    if bottom - edges[-1] > 3.0:
        edges = edges + [float(bottom)]
    return [(lower, upper) for lower, upper in zip(edges, edges[1:]) if upper - lower > 1.0]


def _band_table(
    gray,
    items: Sequence[Dict[str, Any]],
    top: float,
    bottom: float,
    columns: Sequence[Tuple[float, float]],
    label_positions: Sequence[int],
) -> Optional[List[Dict[str, Any]]]:
    """Printed rows of one block, with merged label cells resolved.

    Each returned row is ``{top, bottom, texts: {column: [(text, confidence)]}}``
    for one *printed* row.  Two different placements are used, because the two
    kinds of cell behave differently:

    * a value cell belongs to the printed row its printed box overlaps most --
      these boxes are taller than a row, so a box's baseline cannot say which
      row a figure belongs to (that is exactly how a value drifts into the
      neighbouring year);
    * a label cell (party, nature) is placed in the *merged cell* it sits in,
      i.e. the interval between the rules that cross its own column, and its
      text is repeated into every printed row that interval covers.  That is
      what lets a party name printed once against four year rows govern all
      four without moving any value.
    """
    if not columns:
        return None
    print_rows = row_bands(
        gray, top, bottom, int(columns[0][0]) + 3, int(columns[-1][1]) - 3
    )
    if not print_rows:
        return None
    placed: List[Dict[int, List[Tuple[float, float, str, float]]]] = [
        {} for _ in print_rows
    ]
    label_text: Dict[
        int, List[Tuple[Tuple[float, float], List[Tuple[float, float, str, float]]]]
    ] = {position: [] for position in label_positions}
    for item in items:
        centre = (item["x"] + item.get("x2", item["x"])) / 2.0
        position = _column_of(centre, columns)
        if position is None:
            continue
        if position in label_text:
            left, right = columns[position]
            spans = _spans(gray, top, bottom, int(left) + 3, int(right) - 3)
            span = max(spans, key=lambda pair: _overlap({"top": pair[0], "bottom": pair[1]}, item))
            if _overlap({"top": span[0], "bottom": span[1]}, item) <= 0.0:
                continue
            entry = (
                float(item.get("y", 0.0)),
                float(item.get("x", 0.0)),
                item["text"],
                item.get("confidence", 1.0),
            )
            for existing, cells in label_text[position]:
                if existing == span:
                    cells.append(entry)
                    break
            else:
                label_text[position].append((span, [entry]))
            continue
        best = max(range(len(print_rows)), key=lambda i: _overlap(print_rows[i], item))
        if _overlap(print_rows[best], item) <= 0.0:
            continue
        placed[best].setdefault(position, []).append(
            (
                float(item.get("y", 0.0)),
                float(item.get("x", 0.0)),
                item["text"],
                item.get("confidence", 1.0),
            )
        )
    for position, spans in label_text.items():
        for row_index, print_row in enumerate(print_rows):
            for (lower, upper), cells in spans:
                if min(upper, print_row["bottom"]) - max(lower, print_row["top"]) > 0.0:
                    placed[row_index].setdefault(position, []).extend(cells)
    for row_index in range(len(print_rows)):
        for position, cells in placed[row_index].items():
            # Reading order inside a cell: down its printed lines, then across.
            cells.sort(key=lambda entry: (entry[0], entry[1]))
    return [
        {"top": band["top"], "bottom": band["bottom"], "texts": text}
        for band, text in zip(print_rows, placed)
    ]


def _band_text(cells: Sequence[Tuple[float, float, str, float]]) -> str:
    return " ".join(" ".join(entry[2] for entry in cells).split())


def _band_confidence(cells: Sequence[Tuple[float, float, str, float]]) -> float:
    return min((entry[3] for entry in cells), default=1.0)


def parse_page(
    page_number: int,
    items: Sequence[Dict[str, Any]],
    gray,
    scale: float = 2.0,
) -> Dict[str, Any]:
    """Transactions of one OCR'd note page.

    The page is reconstructed from the printed table itself: column bands from
    its vertical rules, printed rows from its horizontal rules, and merged
    label cells from the rules that *do not* cross them.  An amount is read
    only from the printed row that states its own period, so a value can never
    be carried into a neighbouring year because it happens to sit near it.
    """
    import numpy as np

    gray = np.asarray(gray)
    rows = rows_of(items)
    blocks = _blocks(rows)
    height = float(gray.shape[0]) if gray.ndim == 2 else 0.0
    transactions: List[Dict[str, Any]] = []
    unread = 0
    # Why cells were left unread, so coverage can say what is missing instead
    # of only how much.
    reasons: Dict[str, int] = {}
    mapped_blocks = 0
    unit = _page_unit(items)

    def leave(count: int, reason: str) -> None:
        nonlocal unread
        unread += count
        if count:
            reasons[reason] = reasons.get(reason, 0) + count

    def values_in(block, bottom) -> int:
        return sum(
            1
            for row in rows
            if block["header_y"] < row["y"] < bottom
            for cell in row["cells"]
            if _number(cell["text"]) is not None
        )

    for block in blocks:
        if block["bottom"] is not None:
            bottom = block["bottom"]
        else:
            # The last block has no following header to end it: a page number or
            # a footnote far below the table would otherwise stretch its band
            # until no vertical rule is dark for long enough to be found.
            last_row = max(
                (row["y"] for row in rows if row["y"] > block["header_y"]),
                default=block["top"],
            )
            bottom = min(height - 4.0, last_row + 24.0)
        rules = vertical_rules(gray, int(block["top"]), int(min(bottom, height)))
        bands = [(left, right) for left, right in zip(rules, rules[1:])]
        if len(bands) < 3:
            leave(1, "block_without_column_rules")
            continue
        roles: Dict[int, Optional[str]] = {}
        ambiguous = False
        for position, (left, right) in enumerate(bands):
            words = [
                cell["text"]
                for cell in block["cells"]
                if left <= (cell["x"] + cell["x2"]) / 2.0 < right
            ]
            roles[position] = column_role(words)
            if len(column_roles(words)) > 1:
                ambiguous = True
        if ambiguous:
            leave(values_in(block, bottom), "column_header_names_two_quantities")
            continue
        if "party" not in roles.values() or not any(
            role not in _META_ROLES for role in roles.values() if role
        ):
            leave(1, "block_without_party_or_value_column")
            continue
        # A block is read only when every row is checkable against the block's
        # own control total: both an opening and a closing balance column, so
        # that opening + movements = closing holds row by row.  A block that
        # prints only a closing balance (a remuneration table) has no such
        # control, so its figures are counted unread rather than bound to a
        # column on position alone.
        block_roles = {role for role in roles.values() if role}
        if not _BALANCE_ROLES <= block_roles:
            leave(values_in(block, bottom), "block_without_opening_and_closing_control")
            continue
        label_positions = [
            position for position, role in roles.items() if role in ("party", "nature")
        ]
        table_rows = _band_table(gray, items, block["top"], bottom, bands, label_positions)
        if table_rows is None:
            # The page prints no horizontal rules, so its printed rows cannot be
            # separated: every figure is unread rather than attached to a
            # neighbouring row.
            leave(values_in(block, bottom), "printed_rows_not_separable")
            continue
        mapped_blocks += 1
        party_position = next(
            (position for position, role in roles.items() if role == "party"), None
        )
        nature_position = next(
            (position for position, role in roles.items() if role == "nature"), None
        )
        period_positions = [
            position for position, role in roles.items() if role == "period"
        ]
        party_carried = ""
        nature_carried = ""
        for table_row in table_rows:
            texts = table_row["texts"]
            party = _band_text(texts.get(party_position, [])) if party_position is not None else ""
            nature = (
                _band_text(texts.get(nature_position, [])) if nature_position is not None else ""
            )
            period: Optional[str] = None
            for position in period_positions:
                text = _band_text(texts.get(position, []))
                if text:
                    period = _period(text) or period
            amounts: List[Tuple[float, str, str]] = []
            uncertain: List[Tuple[float, str, str]] = []
            nil_balances: List[str] = []
            for position, cells in sorted(texts.items()):
                role = roles.get(position)
                if role not in _VALUE_ROLES:
                    continue
                text = _band_text(cells)
                value = _number(text)
                if value is None:
                    if role in _BALANCE_ROLES:
                        if _period(text):
                            period = period or _period(text)
                        elif text and _NIL_CELL.match(text):
                            # A printed dash is a disclosed nil balance, which
                            # is what makes the row checkable.
                            nil_balances.append(role)
                    continue
                confidence = _band_confidence(cells)
                if confidence < AMOUNT_CONFIDENCE:
                    if confidence >= UNCERTAIN_CONFIDENCE:
                        uncertain.append((value, role, text))
                    else:
                        leave(1, "low_confidence_amount")
                    continue
                amounts.append((value, role, text))
            if party:
                name, peeled = split_party_nature(party)
                party = name
                if peeled:
                    nature = (nature + " " + peeled).strip()
            if nature:
                nature_carried = nature
            if party:
                party_carried = party
            if not amounts:
                continue
            if not period:
                leave(len(amounts), "row_without_period")
                continue
            if not party_carried:
                leave(len(amounts), "row_without_party")
                continue
            if not _reconciles(amounts, roles, nil_balances):
                # An uncertain cell can still be admitted when the row's own
                # control total proves it: the filing's arithmetic, not the
                # cell's neighbours, is the corroboration.
                rescued = list(amounts) + list(uncertain)
                if uncertain and _reconciles(rescued, roles, nil_balances):
                    amounts = rescued
                else:
                    leave(len(amounts) + len(uncertain), "row_does_not_close_against_its_balances")
                    continue
            for value, role, text in amounts:
                if role in _BALANCE_ROLES or role == "meta":
                    continue
                transactions.append(
                    {
                        "category": _category(nature_carried)
                        if role == "transaction_amount"
                        else role,
                        "category_label": nature_carried or role,
                        "counterparty": party_carried,
                        "period": period,
                        "amount": value,
                        "unit": unit,
                        "page": page_number,
                        "column": role,
                        "reading": "ocr_geometry",
                        "ocr_text": text,
                    }
                )
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for transaction in transactions:
        key = (
            transaction["counterparty"],
            transaction["category"],
            transaction["period"],
            transaction["column"],
            transaction["amount"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(transaction)
    if len(deduped) < len(transactions):
        leave(len(transactions) - len(deduped), "duplicate_row")
    return {
        "transactions": deduped,
        "blocks": mapped_blocks,
        "unread": unread,
        "reasons": reasons,
        "unit": unit,
    }


def _page_unit(items: Sequence[Dict[str, Any]]) -> Optional[str]:
    for item in items:
        match = _UNIT.search(item["text"])
        if match:
            return _UNITS.get(match.group(1).lower())
    return None


def _reconciles(
    amounts: Sequence[Tuple[float, str, str]],
    roles: Dict[int, Optional[str]],
    nil_balances: Sequence[str] = (),
) -> bool:
    """True when a row's opening/closing and movements add up.

    ``nil_balances`` names the balance roles whose cell the filing prints as a
    dash -- an explicitly disclosed nil, never a missing cell.  A row that
    states the movements and one balance is checkable, and closing out at zero
    is a real reconciliation (Mohammed Imran: 24.00 + 18.50 - 42.50 = 0.00 with
    no closing figure printed).
    """
    values: Dict[str, float] = {}
    for value, role, _text in amounts:
        values[role] = values.get(role, 0.0) + value
    for role in nil_balances:
        values.setdefault(role, 0.0)
    if not ({"opening_balance", "closing_balance"} & set(values)):
        return False
    values.setdefault("opening_balance", 0.0)
    values.setdefault("closing_balance", 0.0)
    if not any(role in _ADDITION_ROLES or role in _REDUCTION_ROLES for role in values):
        return False
    additions = sum(value for role, value in values.items() if role in _ADDITION_ROLES)
    reductions = sum(value for role, value in values.items() if role in _REDUCTION_ROLES)
    expected = values["opening_balance"] + additions - reductions
    return abs(expected - values["closing_balance"]) <= ARITHMETIC_TOLERANCE


# ---------------------------------------------------------------------------
# Page location and full read
# ---------------------------------------------------------------------------


def _engine():
    from .official_notice_ocr import _engine as notice_engine

    return notice_engine()


def _render(pdf_path: str, page_1_indexed: int, scale: float):
    import pypdfium2 as pdfium

    with pdfium.PdfDocument(pdf_path) as document:
        page = document[page_1_indexed - 1]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil().convert("RGB")
        page.close()
        bitmap.close()
    return image


def _ocr_items(image) -> List[Dict[str, Any]]:
    import numpy as np

    engine = _engine()
    result = engine(np.asarray(image))
    boxes = getattr(result, "boxes", None)
    texts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    boxes = list(boxes) if boxes is not None else []
    texts = list(texts) if texts is not None else []
    scores = list(scores) if scores is not None else []
    items = []
    for box, text, score in zip(boxes, texts, scores):
        items.append(
            {
                "x": float(min(point[0] for point in box)),
                "y": float(min(point[1] for point in box)),
                "x2": float(max(point[0] for point in box)),
                "y2": float(max(point[1] for point in box)),
                "text": str(text),
                "confidence": float(score),
            }
        )
    return items


def find_note_pages(pdf_path: str, candidates: Sequence[int]) -> List[int]:
    """Image-only pages whose heading names the related-party disclosure.

    Only the top of each candidate page is rendered, so the scan is bounded and
    cheap.  The accepted page and up to :data:`MAX_FULL_PAGES` - 1 following
    candidates are returned, because the disclosure continues onto the next
    page.
    """
    import numpy as np

    engine = _engine()
    strict: Optional[int] = None
    loose: Optional[int] = None
    for page_number in list(candidates)[:MAX_SCAN_PAGES]:
        # 1.6x keeps a 7pt heading large enough for the detector; a lower
        # scale reads nothing at all on these scans (verified on R.K. Fashion).
        image = _render(pdf_path, page_number, 1.6)
        try:
            strip = image.crop((0, 0, image.width, max(150, int(image.height * 0.22))))
            try:
                result = engine(np.asarray(strip))
            finally:
                strip.close()
            combined = " ".join(str(text) for text in (getattr(result, "txts", None) or ()))
        finally:
            image.close()
        compact = _compact(combined)
        if "relatedpartydisclosure" in compact or "detailsofrelatedparty" in compact:
            strict = page_number
            break
        if loose is None and "relatedparty" in compact and (
            "disclosure" in compact or "transaction" in compact
        ):
            # A policy paragraph ("transactions with related parties are ...")
            # also names the subject without being the note heading; it is
            # kept only as a fallback for a note that heads itself
            # differently.
            loose = page_number
    found = strict if strict is not None else loose
    if found is None:
        return []
    # The continuation pages are decided by the reader, not by adjacency: a page
    # is part of the table only when it prints the table's own repeated header
    # band (see ``read_related_party_note``).  Guessing "the next candidate
    # pages" pulled in a profit-and-loss statement and a cash-flow statement.
    return [found]


def _reason_text(reasons: Dict[str, int]) -> str:
    """Human-readable count per reason a cell was left unread."""
    if not reasons:
        return ""
    parts = ", ".join(
        "%s: %d" % (reason.replace("_", " "), count)
        for reason, count in sorted(reasons.items(), key=lambda pair: -pair[1])
    )
    return " (unread by reason -- %s)" % parts


def read_related_party_note(
    pdf_path: str, candidates: Sequence[int], scale: float = 2.0
) -> Dict[str, Any]:
    """Locate and read an image-only related-party note.

    ``candidates`` are the image-only page numbers in document order; the caller
    establishes that they carry no usable text layer.  Nothing is claimed when
    no such note is found.
    """
    located = find_note_pages(pdf_path, candidates)
    if not located:
        return {"found": False, "transactions": [], "state": "UNREAD", "note": "", "pages": []}
    first = located[0]
    transactions: List[Dict[str, Any]] = []
    blocks = 0
    unread = 0
    reasons: Dict[str, int] = {}
    unit: Optional[str] = None
    pages: List[int] = []
    order = [first] + [page for page in candidates if page > first]
    for page_number in order[:MAX_FULL_PAGES]:
        image = _render(pdf_path, page_number, scale)
        try:
            items = _ocr_items(image)
            gray = image.convert("L")
            parsed = parse_page(page_number, items, gray, scale)
        finally:
            image.close()
        if not parsed["blocks"]:
            if page_number == first:
                # A page that only mentions the subject in prose is not the
                # note: no claim is made about the disclosure from it.
                return {
                    "found": False,
                    "transactions": [],
                    "state": "UNREAD",
                    "note": "",
                    "pages": [],
                }
            # The table ends where its repeated header band stops appearing.
            break
        pages.append(page_number)
        blocks += parsed["blocks"]
        unread += parsed["unread"]
        for reason, count in (parsed.get("reasons") or {}).items():
            reasons[reason] = reasons.get(reason, 0) + count
        unit = unit or parsed["unit"]
        transactions.extend(parsed["transactions"])
    if not transactions:
        return {
            "found": True,
            "transactions": [],
            "state": "PARTIAL",
            "note": "an image-only related-party note was located but no transaction value "
            "could be read from it (%d value(s) unread%s)"
            % (unread, _reason_text(reasons)),
            "pages": pages,
            "reasons": reasons,
        }
    page_unit = unit or _page_unit(
        [item for item in _ocr_items(_render(pdf_path, pages[0], scale))]
    )
    for transaction in transactions:
        if transaction.get("unit") is None:
            transaction["unit"] = page_unit
    state = "DISCLOSED" if not unread else "PARTIAL"
    note = (
        "%d related-party transaction block(s) read by OCR of image-only note page(s) "
        "%s: %d value(s) reported, %d unread cell(s)%s"
        % (
            blocks,
            ", ".join(str(page) for page in pages),
            len(transactions),
            unread,
            _reason_text(reasons),
        )
    )
    return {
        "found": True,
        "transactions": transactions,
        "state": state,
        "note": note,
        "pages": pages,
        "reasons": reasons,
    }
