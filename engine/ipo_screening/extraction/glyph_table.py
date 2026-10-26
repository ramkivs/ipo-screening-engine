"""Character-geometry table recovery for text layers with merged cells.

Some filings' text layers emit a whole table row as a handful of very wide
fragments: several numeric cells arrive glued into one string separated only
by runs of spaces, and the fragment's own start position says nothing about
where the individual cells begin.  Splitting such a fragment on whitespace
cannot tell a cell boundary from an inter-word space, so a row of five period
amounts is read as two cells and every amount after the first is bound to the
wrong period (or dropped).

PDF text is positioned per glyph, and those positions survive however the
extractor chose to chunk the string.  This module reads the glyph boxes of one
page and rebuilds cells from geometry alone:

* characters are grouped into visual lines by vertical centre;
* inside a line, characters are grouped into runs, splitting only where the
  horizontal gap is clearly wider than the line's own letter/word spacing and
  never between two digits of the same number;
* each cell keeps its own box, so a caller can associate a value with a
  column by geometry instead of by position in a string.

The result is a list of ``(baseline, cells)`` rows with the same shape the
text-layer readers already consume, i.e. a drop-in replacement for
``SectionExtractor.extract_page_fragments`` output.  Nothing is inferred
about table semantics here: no period labels, no totals, no categories.

The recovery is deliberately conservative.  A page whose glyph geometry is
unavailable returns ``None`` (no layer) so the caller can distinguish "read
and empty" from "could not read"; and the split rule is biased towards
leaving characters joined rather than inventing a cell boundary, because a
missing cell boundary leaves a value unread while a spurious one binds a
value to the wrong period.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

# A gap wider than this many points separates two cells.  Body text in these
# filings is set at 7-9 pt; within a word the glyphs are all but touching, and
# a column boundary is at least an em wide.  The floor only has to sit above
# intra-word spacing: a spurious split inside a word is repaired by joining the
# label fragments back up, while a missed split binds a value to the wrong
# period.
MIN_GAP = 2.6

# A gap wider than this multiple of the line's own typical gap separates two
# cells when the line is set loose (justified text, tracked-out figures).
GAP_FACTOR = 2.4

# Digits, thousands separators and decimal points on both sides of a gap mean
# the gap sits inside one number, whatever its width (a justified or
# tracked-out figure still reads as one figure).
NUMERIC_JOIN_CHARS = set("0123456789,.")
NUMERIC_JOIN_LIMIT = 12.0


@dataclass(frozen=True)
class GlyphCell:
    """One reconstructed cell: its box and its text."""

    x0: float
    x1: float
    y0: float
    y1: float
    text: str

    @property
    def centre(self) -> float:
        return (self.x0 + self.x1) / 2.0


Char = Tuple[float, float, float, str]  # (x0, x1, y_centre, char)


def _char_boxes(pdf_path: str, page_1_indexed: int) -> Optional[List[Char]]:
    """Character boxes ``(x0, x1, y_centre, char)`` for one page, or ``None``.

    ``None`` means the page has no character geometry (a scanned image, a page
    beyond the end of the document, or a decoder that could not open it).
    """
    try:
        import pypdfium2 as pdfium
    except Exception:  # pragma: no cover - optional dependency
        return None
    try:
        document = pdfium.PdfDocument(pdf_path)
    except Exception:
        return None
    try:
        if not 1 <= page_1_indexed <= len(document):
            return None
        page = document[page_1_indexed - 1]
        try:
            textpage = page.get_textpage()
            try:
                count = int(textpage.count_chars())
                boxes: List[Char] = []
                for index in range(count):
                    char = textpage.get_text_range(index, 1)
                    if not char or char in ("\r", "\n"):
                        continue
                    left, bottom, right, top = textpage.get_charbox(index)
                    if char.isspace():
                        # Whitespace carries no ink but its advance is the
                        # gap it needs: keep it as a zero-width marker at its
                        # own position so word spacing is measured, not
                        # guessed.
                        boxes.append(
                            (
                                float(left),
                                max(float(right), float(left)),
                                (float(bottom) + float(top)) / 2.0,
                                " ",
                            )
                        )
                        continue
                    boxes.append(
                        (
                            float(left),
                            max(float(right), float(left)),
                            (float(bottom) + float(top)) / 2.0,
                            char,
                        )
                    )
                return boxes
            finally:
                textpage.close()
        finally:
            page.close()
    except Exception:
        return None
    finally:
        document.close()


def _group_lines(boxes: Sequence[Char]) -> List[List[Char]]:
    """Group character boxes into visual lines, top of page first."""
    lines: List[List[Char]] = []
    for box in sorted(boxes, key=lambda item: (-item[2], item[0])):
        if lines and abs(lines[-1][0][2] - box[2]) <= 2.2:
            lines[-1].append(box)
        else:
            lines.append([box])
    for line in lines:
        line.sort(key=lambda item: item[0])
    return lines


def _line_gap_threshold(line: Sequence[Char]) -> float:
    """Gap width above which two characters belong to different cells."""
    gaps: List[float] = []
    previous_x1: Optional[float] = None
    for x0, x1, _y, char in line:
        if char == " ":
            continue
        if previous_x1 is not None:
            gap = x0 - previous_x1
            if gap > 0.05:
                gaps.append(gap)
        previous_x1 = x1
    if not gaps:
        return MIN_GAP
    gaps.sort()
    median = gaps[len(gaps) // 2]
    return max(MIN_GAP, GAP_FACTOR * median)


def _split_runs(line: Sequence[Char]) -> List[GlyphCell]:
    """Rebuild the cells of one visual line from its character geometry.

    A run of glyphs becomes one cell.  Adjacent runs are separated where the
    horizontal gap is wider than the line's own spacing, and the intervening
    space glyphs become a single space in the text of a run that is not
    broken.  Two digits separated by a wide gap are never split: a figure
    stays one cell however it is tracked out.
    """
    threshold = _line_gap_threshold(line)
    cells: List[GlyphCell] = []
    buffer: List[Char] = []
    pending_space = False

    def flush() -> None:
        nonlocal pending_space
        if not buffer:
            pending_space = False
            return
        text = " ".join("".join(box[3] for box in buffer).split())
        if text:
            cells.append(
                GlyphCell(
                    x0=min(box[0] for box in buffer),
                    x1=max(box[1] for box in buffer),
                    y0=min(box[2] for box in buffer),
                    y1=max(box[2] for box in buffer),
                    text=text,
                )
            )
        buffer.clear()
        pending_space = False

    previous_end: Optional[float] = None
    previous_char = ""
    for x0, x1, y, char in line:
        if char == " ":
            if buffer:
                pending_space = True
            continue
        if buffer and previous_end is not None:
            gap = x0 - previous_end
            joined = (
                previous_char in NUMERIC_JOIN_CHARS
                and char in NUMERIC_JOIN_CHARS
                and gap <= NUMERIC_JOIN_LIMIT
            )
            if gap > threshold and not joined:
                flush()
            elif pending_space:
                buffer.append((previous_end, previous_end, y, " "))
        buffer.append((x0, x1, y, char))
        previous_end = x1
        previous_char = char
        pending_space = False
    flush()
    return cells


def page_cells(
    pdf_path: str, page_1_indexed: int
) -> Optional[List[Tuple[float, List[GlyphCell]]]]:
    """Reconstructed cells per visual line for one page, or ``None``."""
    boxes = _char_boxes(pdf_path, page_1_indexed)
    if boxes is None:
        return None
    rows: List[Tuple[float, List[GlyphCell]]] = []
    for line in _group_lines(boxes):
        cells = _split_runs(line)
        if not cells:
            continue
        baseline = sum(cell.y0 for cell in cells) / len(cells)
        rows.append((baseline, cells))
    if not rows:
        return None
    return rows


def as_fragments(
    rows: Sequence[Tuple[float, List[GlyphCell]]]
) -> List[Tuple[float, float, str]]:
    """Flatten reconstructed cells into ``(y, x, text)`` fragments."""
    fragments: List[Tuple[float, float, str]] = []
    for baseline, cells in rows:
        for cell in cells:
            fragments.append((baseline, cell.x0, cell.text))
    return fragments


def numeric_columns(
    rows: Sequence[Tuple[float, List[GlyphCell]]],
    matcher,
    tolerance: float = 8.0,
) -> List[Tuple[float, float]]:
    """Cluster numeric cells of a page into column bands, left to right.

    ``matcher`` decides which cell texts count as a value.  Bands are built
    from the positions of the cells themselves, so they describe where the
    amounts actually sit rather than where a header says they should.
    """
    starts = sorted(
        cell.x0
        for _baseline, cells in rows
        for cell in cells
        if matcher(cell.text)
    )
    bands: List[List[float]] = []
    for start in starts:
        if bands and start - bands[-1][-1] <= tolerance:
            bands[-1].append(start)
        else:
            bands.append([start])
    return [(band[0], band[-1]) for band in bands]


def column_index(bands: Sequence[Tuple[float, float]], x: float) -> Optional[int]:
    """Index of the band a cell starting at ``x`` belongs to, if any."""
    for index, (start, end) in enumerate(bands):
        if start - 2.0 <= x <= end + 2.0:
            return index
    return None
