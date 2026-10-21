"""Conservative native-PDF offer-table geometry; no OCR or source authority.

Only isolated, aligned component headers establish columns. Text runs remain
separate and retain their original coordinates. Ambiguous/rotated layouts are
not reconstructed. This is a small table AST, not a general PDF table reader.
"""
from dataclasses import dataclass, asdict
import re


@dataclass(frozen=True)
class Cell:
    text: str
    x: float
    y: float


def component_columns(page, page_number):
    cells = []
    rectangles = []
    def visit(text, cm, tm, font, size):
        if not text.strip() or any(abs(v) > 1e-6 for v in (cm[1], cm[2], tm[1], tm[2])):
            return
        x, y = tm[4] * cm[0] + cm[4], tm[5] * cm[3] + cm[5]
        cells.append(Cell(text.strip(), float(x), float(y)))
    def operand(op, args, cm, tm):
        if op == b're' and len(args) == 4 and not (cm[1] or cm[2]):
            x, y, w, h = map(float, args)
            if w > 0 and h > 0 and cm[0] > 0 and cm[3] > 0:
                rectangles.append((x*cm[0]+cm[4], y*cm[3]+cm[5], w*cm[0], h*cm[3]))
    page.extract_text(visitor_text=visit, visitor_operand_before=operand)
    labels = {'fresh_issue': r'fresh\s+issue(?:\s+size)?',
              'ofs': r'offer\s+for\s+sale(?:\s+size)?',
              'total': r'total\s+(?:issue|offer)(?:\s+size)?'}
    headers = {}
    for field, pattern in labels.items():
        matches = [c for c in cells if re.fullmatch(pattern, c.text, re.I)]
        if len(matches) != 1:
            return []
        headers[field] = matches[0]
    ordered = sorted(headers.items(), key=lambda pair: pair[1].x)
    if ([f for f, _ in ordered] != ['fresh_issue', 'ofs', 'total'] or
            max(c.y for c in headers.values()) - min(c.y for c in headers.values()) > 12 or
            min(ordered[i+1][1].x - ordered[i][1].x for i in range(2)) < 60):
        return []
    # Explicit adjoining header/body rectangles are required. A fixed lookahead
    # distance is not a table boundary and could consume unrelated later prose.
    bounds = {}
    for field, header in ordered:
        boxes = [r for r in rectangles if r[0] <= header.x <= r[0]+8
                 and r[1] < header.y < r[1]+r[3] and r[2] >= 50]
        if len(boxes) != 1:
            return []
        box = boxes[0]
        bodies = [r for r in rectangles if abs(r[0]-box[0]) <= 1 and abs(r[2]-box[2]) <= 1
                  and abs(r[1]+r[3]-box[1]) <= 1]
        if len(bodies) != 1:
            return []
        bounds[field] = bodies[0]
    if max(r[1] for r in bounds.values())-min(r[1] for r in bounds.values()) > 1:
        return []
    columns = []
    for index, (field, header) in enumerate(ordered[:2]):
        x, bottom, width, height = bounds[field]
        right = min(x+width, ordered[index+1][1].x)
        members = [c for c in cells if header.x - 2 <= c.x < right - 2
                   and bottom < c.y < bottom+height]
        # Require row alignment to the header's left edge, not a text run
        # merely starting somewhere inside the column. No cell stitching into
        # a financial assertion: each run is parsed separately by the caller.
        members = [c for c in members if abs(c.x-header.x) <= 3]
        columns.append({'component': field, 'page': page_number,
                        'header': asdict(header), 'body_bounds': list(bounds[field]), 'cells': [asdict(c) for c in members]})
    return columns
