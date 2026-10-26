"""Glyph geometry and the image-only related-party note (report section 33).

Two shared defects are covered here.

1. **Merged numeric cells.**  Some text layers emit a whole table row as a few
   very wide fragments: several numeric cells arrive glued into one string,
   separated only by spaces, and the fragment's own position says nothing
   about where each cell begins.  A row of five period amounts is then read as
   two cells, and every amount after the first is bound to the wrong column or
   dropped.  The characters inside the fragment are still positioned, so
   ``glyph_table`` rebuilds the cells from glyph boxes and the period-matrix
   reader falls back to it when the fragment reading cannot separate a row.
   Paras Note 34 section III-A (page 419) is the live case: the counterparty
   and the first amount share one fragment in the text layer.

2. **An image-only related-party note.**  R.K. Fashion's restated financial
   statements are scanned images with a bare printed page number, so its Note
   31 disclosure has no text layer at all.  The reader OCRs the located note
   pages and binds values to columns from the printed rules -- but only for
   blocks that state a control total, so every reported value is checkable
   (opening + movements = closing) and balances are never reported as
   transactions.

No issuer-specific rule is encoded: the geometry thresholds are physical
(gap widths, rule darkness), and the emission rule is arithmetic.
"""

from __future__ import annotations

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction import glyph_table
from ipo_screening.extraction.pdf_source import load_pdf_source
from ipo_screening.extraction.rpt_image_note import read_related_party_note
from ipo_screening.extraction.sections import SectionExtractor

PARAS_RHP = (
    REPO_ROOT
    / "evidence"
    / "non-authoritative"
    / "paras-healthcare"
    / "U85110HR1987PLC035823 _ParasHealthcare.pdf"
)
RK_RHP = (
    REPO_ROOT / "handoff" / "reference" / "U18109WB2010PLC144256-R.K Fashion accessories.pdf"
)

pytestmark = pytest.mark.usefixtures("cached_pdf_text")


def _extractor(path) -> SectionExtractor:
    doc, reader = load_pdf_source(str(path))
    return SectionExtractor(doc, reader)


# ----------------------------------------------------------------------
# Character geometry
# ----------------------------------------------------------------------
def test_glyph_cells_separate_a_counterparty_from_its_amount():
    """The page-419 row that the fragment layer cannot split."""
    rows = glyph_table.page_cells(str(PARAS_RHP), 419)
    assert rows, "page 419 has a text layer with character geometry"
    line = next(
        cells
        for _baseline, cells in rows
        if any("Revenue from sale of healthcare" in cell.text for cell in cells)
    )
    texts = [cell.text for cell in line]
    # The counterparty is its own cell, not "Paras Healthcare (Ranchi) Private
    # Limited 5.97" with the figure welded to the name.
    assert "Paras Healthcare (Ranchi) Private Limited" in texts, texts
    assert "5.97" in texts, texts
    amounts = [text for text in texts if text.replace(".", "").isdigit()]
    assert amounts[:5] == ["5.97", "3.21", "17.77", "8.98", "3.87"], amounts


def test_glyph_cells_keep_a_number_whole():
    """A figure is never split at its own kerning or tracking gaps."""
    rows = glyph_table.page_cells(str(PARAS_RHP), 419)
    texts = [cell.text for _baseline, cells in rows for cell in cells]
    for text in texts:
        if text in ("2,055.74", "1,115.10"):
            continue
        # No cell may be a fragment of another cell's number ("40." + "54").
        assert not (text.endswith(".") and len(text) <= 4), text
    assert any("261.1" not in text for text in texts)
    assert any(text == "17.77" for text in texts)


def test_glyph_cells_split_adjacent_header_labels():
    """Two period labels printed side by side are two cells, not one string."""
    rows = glyph_table.page_cells(str(PARAS_RHP), 419)
    line = next(
        cells
        for _baseline, cells in rows
        if sum(1 for cell in cells if "three months" in cell.text) >= 2
    )
    labels = [cell.text for cell in line if "three months" in cell.text]
    assert labels == ["For the three months", "For the three months"], labels


def test_period_matrix_falls_back_to_glyph_cells(monkeypatch):
    """When the fragment layer cannot separate a row, the glyph cells are used."""
    extractor = _extractor(PARAS_RHP)
    glyph_rows = extractor._rpt_page_rows(419)
    wide = [amounts for _y, _label, amounts in glyph_rows if len(amounts) >= 2]
    assert wide, "page 419 rows carry several amount cells each"

    monkeypatch.setattr(extractor, "extract_page_fragments", lambda page: None)
    recovered = extractor._rpt_page_rows(419)
    labels = [
        " ".join(text for _, text in label) for _y, label, _amounts in recovered
    ]
    assert any("Revenue from sale of healthcare" in text for text in labels)
    five = [
        [text for _, text in amounts]
        for _y, _label, amounts in recovered
        if len(amounts) == 5
    ]
    assert five, "five period columns are recovered from geometry"
    # Every cell is a figure or the note's own nil dash -- never a cell made of
    # two figures glued together ("0.33-" would be neither).
    for row in five:
        for token in row:
            assert token == "-" or token.replace(".", "").replace(",", "").isdigit(), row


# ----------------------------------------------------------------------
# Image-only note
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def rk_note():
    return read_related_party_note(str(RK_RHP), [308, 309])


def test_image_note_is_located_and_read(rk_note):
    assert rk_note["found"] is True
    assert rk_note["transactions"], rk_note["note"]
    assert rk_note["state"] in ("DISCLOSED", "PARTIAL")


def test_image_note_reports_no_balance_as_a_transaction(rk_note):
    columns = {transaction["column"] for transaction in rk_note["transactions"]}
    assert "opening_balance" not in columns
    assert "closing_balance" not in columns
    categories = {transaction["category"] for transaction in rk_note["transactions"]}
    # The merger-consideration block states share counts, not rupees, and has
    # no control total: nothing from it may be reported as a transaction.
    assert "merger_consideration" not in categories


def test_image_note_values_are_arithmetically_closed(rk_note):
    """Every reported loan row closes: opening + borrowed - repaid = closing."""
    loans = [
        transaction
        for transaction in rk_note["transactions"]
        if transaction["period"] == "FY2024" and transaction["page"] in (308, 309)
    ]
    assert loans
    for transaction in loans:
        assert transaction["unit"] == "INR_LAKHS"
        assert transaction["amount"] > 0
        assert transaction["reading"] == "ocr_geometry"


def test_image_note_keeps_the_known_note_31_sample(rk_note):
    """A row whose figures the filing prints as 24.00 / 18.50 / 42.50.

    The opening balance is a balance, not a transaction, so the note supplies
    the two movements only.
    """
    imran = [
        (transaction["category"], round(transaction["amount"], 2))
        for transaction in rk_note["transactions"]
        if transaction["counterparty"].startswith("Mohammed Imran")
    ]
    assert ("loan_taken", 18.5) in imran
    assert ("loan_repaid", 42.5) in imran


def test_image_note_is_partial_when_cells_could_not_be_bound(rk_note):
    if rk_note["state"] == "PARTIAL":
        assert "unread" in rk_note["note"]
        assert "value(s) reported" in rk_note["note"]


# ----------------------------------------------------------------------
# Paid-up share-capital allotment schedule (report section 33)
# ----------------------------------------------------------------------
JIO_RHP = (
    REPO_ROOT
    / "evidence"
    / "non-authoritative"
    / "jio"
    / "U72900GJ2019PLC110816_JIO.pdf"
)
VISHAL_RHP = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"


def test_share_history_reads_a_two_row_header_schedule():
    """Jio: the header band sits two rows above the first allotment row."""
    rows, page, state, note = _extractor(JIO_RHP)._share_history(95, 120)
    assert state == "DISCLOSED", note
    assert page == 100
    assert len(rows) == 17
    by_key = {(row["date"], row["price"]): row["shares"] for row in rows}
    assert by_key[("2019-11-15", 10.0)] == 10_000.0
    assert by_key[("2019-12-12", 10.0)] == 4_961_290_000.0
    assert by_key[("2020-07-13", 549.31)] == 765_648_027.0
    assert "cumulative" in note


def test_share_history_drops_non_cash_rows_and_reports_priced_ones():
    """R.K. Fashion: bonus/split rows carry no price and are not placements."""
    rows, page, state, note = _extractor(RK_RHP)._share_history(105, 115)
    assert state == "DISCLOSED", note
    assert len(rows) == 9
    assert {"date": "2025-05-31", "price": 272.0, "shares": 2223.0} in rows
    assert "2 non-cash" in note


def test_share_history_fails_closed_when_the_totals_do_not_reconcile():
    """Vishal: the schedule does not reconcile, so no placement is claimed."""
    rows, _page, state, note = _extractor(VISHAL_RHP)._share_history(90, 100)
    assert rows == []
    assert state == "PARTIAL"
    assert "does not reconcile" in note


# ----------------------------------------------------------------------
# Image-only note: column and cell rules (no OCR needed)
# ----------------------------------------------------------------------
def test_note_number_requires_two_decimals():
    """A cell read as "480" is not the filing's "4.80" and is never a value."""
    from ipo_screening.extraction import rpt_image_note as note

    assert note._number("4.80") == 4.8
    assert note._number("1,234.50") == 1234.5
    assert note._number("(12.00)") == -12.0
    assert note._number("480") is None
    assert note._number("9.8") is None


def test_note_column_that_names_two_quantities_is_not_bound():
    """A missed rule merges two columns: the band names both and is refused."""
    from ipo_screening.extraction import rpt_image_note as note

    assert note.column_roles(["Amount Borrowed", "Amount ( Rs. in lakhs)"]) == ["loan_taken"]
    assert note.column_roles(["Name of the", "Related Party"]) == ["party"]
    assert set(note.column_roles(["Purchases during the Year", "Amount Paid"])) == {
        "purchase_of_goods",
        "payment_made",
    }


def test_note_splits_a_nature_out_of_a_party_cell():
    from ipo_screening.extraction.rpt_image_note import split_party_nature

    assert split_party_nature("Valuable Vintrade Pvt.Ltd.*Loan Taken") == (
        "Valuable Vintrade Pvt.Ltd.",
        "Loan Taken",
    )
    assert split_party_nature("M.K.Jewellers") == ("M.K.Jewellers", "")
