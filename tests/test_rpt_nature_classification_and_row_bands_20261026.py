"""Shared transaction natures and printed-row reconstruction (report s.34).

Two defects are covered here, plus the regression that proves the correction.

1. **A nature was classified by whichever reader happened to read it.**  The
   period-matrix reader and the scanned-note reader each carried their own
   phrase list, so the same printed nature could be a sale in one path and
   ``unclassified`` in the other, and a phrase added for readability could
   quietly make an expense eligible for the Module D numerator.  The vocabulary
   now lives in ``extraction/rpt_categories.py``, is shared by both readers and
   is the same set the builder counts.  The tests below prove the two
   directions that matter: the *positive* case (real revenue natures are
   classified and eligible) and the *negative* case (employee benefits,
   retainers, sitting fees, rents, purchases, loans -- and any nature whose
   wording does not state a direction -- are never eligible).

2. **An amount was bound to the printed row it was nearest to.**  These scans
   print a figure's baseline a few pixels below its own row's rule, so
   baseline/centre assignment puts a value in the *following* year's row.  The
   reader now rebuilds the table from its printed rules (``row_bands``),
   resolves vertically merged label cells from the rules that do not cross
   them (``_spans``) and places every value by the box overlap it has with its
   own printed row (``_band_table``).  Synthetic pages below make the drift
   explicit: the value's baseline lies inside the next printed row and it still
   binds to the row its own period label is printed in.

No issuer-specific rule is encoded anywhere: the geometry tests use a drawn
table, and the R.K. Fashion regression asserts the arithmetic the filing
itself prints.
"""

from __future__ import annotations

import numpy as np
import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction import rpt_categories
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.rpt_categories import classify_nature
from ipo_screening.extraction.rpt_image_note import (
    _band_confidence,
    _band_table,
    _band_text,
    _column_of,
    _overlap,
    _spans,
    column_roles,
    crosses,
    horizontal_rules,
    parse_page,
    read_related_party_note,
    row_bands,
)

RK_RHP = (
    REPO_ROOT / "handoff" / "reference" / "U18109WB2010PLC144256-R.K Fashion accessories.pdf"
)

pytestmark = pytest.mark.usefixtures("cached_pdf_text")


# ----------------------------------------------------------------------
# Shared nature vocabulary: the positive case
# ----------------------------------------------------------------------
def test_revenue_natures_are_classified_and_counted():
    """Revenue wording maps to the approved numerator set."""
    cases = {
        "Sale of goods": "sale_of_goods",
        "Sales of goods (net)": "sale_of_goods",
        "Sale of services": "sale_of_services",
        "Rendering of services": "sale_of_services",
        "Revenue from operations": "revenue_from_operations",
        "Revenue from sale of healthcare services": "sale_of_services",
        "Job work charges received": "job_work_charges_received",
    }
    for text, category in cases.items():
        assert classify_nature(text) == category, text
        assert rpt_categories.is_revenue_category(category) is True, text


def test_a_wrapped_nature_still_matches_after_line_breaks_are_collapsed():
    """OCR and PDF line breaks arrive as newlines inside one printed nature."""
    assert classify_nature("Post employment\ndefined benefits") == "employee_benefits"
    assert classify_nature("Sale of\n  goods") == "sale_of_goods"
    assert classify_nature("Interest on loan\npaid") == "interest_paid"


def test_the_builder_counts_exactly_the_shared_revenue_set():
    """The numerator and the readers cannot drift apart."""
    assert (
        CanonicalInputBuilder._RPT_SALES_SERVICES_CATEGORIES
        == rpt_categories.REVENUE_CATEGORIES
    )
    for category in list(rpt_categories.CATEGORY_CLASS) + ["sale_of_anything"]:
        assert CanonicalInputBuilder._rpt_is_sales_services(category) == (
            rpt_categories.is_revenue_category(category)
        ), category


# ----------------------------------------------------------------------
# Shared nature vocabulary: the negative case
# ----------------------------------------------------------------------
NOT_REVENUE = {
    # employee benefits, KMP compensation
    "Short term employee benefits": "employee_benefits",
    "Post employment defined benefits": "employee_benefits",
    "Gratuity": "employee_benefits",
    "Leave encashment": "employee_benefits",
    "Contribution to provident fund": "employee_benefits",
    "Share based payment": "share_based_payment",
    "Managerial remuneration": "remuneration",
    "Remuneration": "remuneration",
    "Salary": "salary",
    "Salaries paid": "salary",
    # retainers and professional fees, sitting fees
    "Retainers and consultant s fee": "retainer_fees",
    "Retainers and Consultants fee": "retainer_fees",
    "Professional fees": "retainer_fees",
    "Directors sitting fees": "sitting_fees",
    "Sitting fees": "sitting_fees",
    # purchases and operating expenses
    "Purchase of goods": "purchase_of_goods",
    "Purchase of property, plant and equipment": "purchase_of_ppe",
    "Sale of property, plant and equipment": "sale_of_ppe",
    "Repair & maintenance and power & fuel": "repairs_and_power",
    "Reimbursement of expenses paid": "reimbursement_expenses_paid",
    "Job work charges paid": "job_work_charges_paid",
    "Hiring/transport charges paid": "hiring_transport_charges_paid",
    # interest and rent with a stated direction
    "Interest paid": "interest_paid",
    "Interest on loan taken": "interest_paid",
    "Rent paid": "rent_paid",
    "Lease rent paid": "rent_paid",
    "Rental income": "rent_received",
    "Rent received": "rent_received",
    "Interest received": "interest_received",
    # financing and capital
    "Loan taken": "loan_taken",
    "Amount borrowed": "loan_taken",
    "Loan repaid": "loan_repaid",
    "Loan to wholly owned subsidiaries": "loan_given",
    "Advances given": "advance_given",
    "Deemed capital contribution": "deemed_capital_contribution",
    "Investment in deemed equity of subsidiary and/or loan": "deemed_capital_contribution",
    "Share of profit paid": "share_of_profit_paid",
}


@pytest.mark.parametrize("text,category", sorted(NOT_REVENUE.items()))
def test_non_revenue_natures_are_classified_but_never_eligible(text, category):
    """The negative case that keeps the numerator honest."""
    assert classify_nature(text) == category, text
    assert rpt_categories.is_revenue_category(category) is False, text


def test_no_expense_or_balance_class_can_be_eligible():
    """Class and eligibility agree for every recognised category.

    A category added to the vocabulary with an expense/asset/liability/capital
    class therefore cannot be counted, and a "revenue" class that is not in the
    approved set cannot be counted either: both halves of the mapping are
    checked, so neither can be widened alone.
    """
    for category, nature_class in rpt_categories.CATEGORY_CLASS.items():
        eligible = rpt_categories.is_revenue_category(category)
        assert eligible == (nature_class == "revenue"), category
        in_set = category in rpt_categories.REVENUE_CATEGORIES
        assert eligible == in_set, category


def test_a_nature_without_a_stated_direction_is_not_classified():
    """"Rent and facility fees" does not say who paid: it stays unclassified."""
    for text in (
        "Rent and facility fees",
        "Loan to and from group companies",
        "Reimbursements",
        "Rent",
        "Unspecified services",
        "",
    ):
        assert classify_nature(text) is None, text


def test_rent_is_classified_by_direction_and_never_as_revenue():
    """"Rental income" and "Rent paid" are different economic events."""
    received = classify_nature("Rental income")
    paid = classify_nature("Rent paid by the Company")
    assert (received, paid) == ("rent_received", "rent_paid")
    assert rpt_categories.CATEGORY_CLASS[received] == "income_other"
    assert rpt_categories.CATEGORY_CLASS[paid] == "expense"
    assert not rpt_categories.is_revenue_category(received)
    assert not rpt_categories.is_revenue_category(paid)
    # The ambiguous form is not silently resolved to either.
    assert classify_nature("Rent and facility fees") is None


def test_shared_vocabulary_is_what_the_readers_call():
    """Both readers resolve a nature through the same function."""
    from ipo_screening.extraction import rpt_image_note

    assert rpt_image_note._category("Rental income") == rpt_categories.classify_nature(
        "Rental income"
    )
    assert rpt_image_note._category("Sitting fees") == "sitting_fees"
    assert rpt_image_note._category("Something not in the vocabulary") == "unclassified"


# ----------------------------------------------------------------------
# Printed-row geometry on a drawn table
# ----------------------------------------------------------------------
PARTY, NATURE, PERIOD, OPENING, TAKEN, CLOSING = range(6)
_EDGES = (40, 140, 240, 340, 440, 560, 700)
# Printed rows of the drawn table (y positions of the horizontal rules).
_RULES = (60, 80, 100, 120, 140, 160)


def _drawn_table():
    """A ruled table whose party/nature cells are merged across three years.

    The party and nature columns carry rules only at their outer edges, which
    is how a vertically merged label cell looks on paper: no rule crosses it.
    """
    gray = np.full((400, 760), 250, dtype=np.uint8)
    for x in _EDGES:
        gray[_RULES[0] : _RULES[-1] + 2, x - 1 : x + 1] = 0
    for y in _RULES:
        gray[y - 1 : y + 1, _EDGES[0] : _EDGES[-1] + 1] = 0
    # Erase the rules that would split the merged party and nature cells:
    # between y=100 and y=160 only their outer edges are ruled.
    for y in (100, 120, 140):
        for column in (PARTY, NATURE):
            left, right = _EDGES[column] + 2, _EDGES[column + 1] - 2
            gray[y - 1 : y + 1, left:right] = 250
    return gray


def _item(text, column, y, height=14.0, confidence=0.98, x_inset=10.0):
    left, right = _EDGES[column] + x_inset, _EDGES[column + 1] - x_inset
    return {
        "text": text,
        "x": left,
        "x2": right,
        "y": float(y),
        "y2": float(y + height),
        "confidence": confidence,
    }


def _drawn_page():
    """The drawn table plus the OCR items a reader would see for it.

    ``taken 5.00`` and ``taken 12.00`` are deliberately tall boxes: their
    baselines fall *inside the next printed year*, which is exactly what these
    scans print.  Only their overlap with their own printed row says where the
    figure belongs.
    """
    items = [
        _item("Amounts in Lakhs", PARTY, 30, height=12),
        _item("Name of the Related Party", PARTY, 64),
        _item("Nature of Transaction", NATURE, 64),
        _item("Financial Year", PERIOD, 64),
        _item("Opening Balance", OPENING, 64),
        _item("Amount Taken", TAKEN, 64),
        _item("Closing Balance", CLOSING, 64),
        # The merged label cells, printed once against all three year rows.
        _item("Alpha Traders", PARTY, 117, height=18),
        _item("Loan Taken", NATURE, 117, height=18),
        # FY 2023-24
        _item("2023-24", PERIOD, 104),
        _item("0.00", OPENING, 104),
        _item("10.00", TAKEN, 104),
        _item("10.00", CLOSING, 104),
        # FY 2024-25: the figure's baseline reaches into the row below.
        _item("2024-25", PERIOD, 123),
        _item("10.00", OPENING, 123),
        _item("5.00", TAKEN, 124, height=23),
        _item("15.00", CLOSING, 124, height=18),
        # FY 2025-26
        _item("2025-26", PERIOD, 143),
        _item("15.00", OPENING, 143),
        _item("12.00", TAKEN, 144, height=23),
        _item("27.00", CLOSING, 144, height=16),
    ]
    return items, _drawn_table()


def test_horizontal_rules_are_the_printed_row_boundaries():
    gray = _drawn_table()
    rules = horizontal_rules(gray, 95, 175, _EDGES[0] + 5, _EDGES[-1] - 5)
    # Only the outer edges cross the merged label columns, so the rules are read
    # across the value columns, where every printed row boundary is ruled.
    assert [round(rule) for rule in rules] == [100, 120, 140, 160], rules
    assert crosses(gray, 120, _EDGES[1] + 5, _EDGES[-1] - 5) is True
    assert crosses(gray, 110, _EDGES[1] + 5, _EDGES[-1] - 5) is False


def test_a_densely_set_word_is_not_a_printed_rule():
    """A label column's dense text must not be read as a cell boundary."""
    from ipo_screening.extraction import rpt_image_note as note

    width = 64
    text_like = np.full((20, width), 250, dtype=np.uint8)
    # Glyph-like bars with the white gaps real letters always leave.
    for start in range(0, width - 6, 8):
        text_like[5:9, start : start + 6] = 0
    rule_like = np.full((20, width), 250, dtype=np.uint8)
    rule_like[10, :] = 0
    assert text_like[5:9].mean() < 150  # as dark as a rule by average only
    assert note.horizontal_rules(text_like, 0, 20, 0, width) == []
    assert [round(rule) for rule in note.horizontal_rules(rule_like, 0, 20, 0, width)] == [10]


def test_row_bands_gives_up_when_a_page_prints_no_rules():
    """No rules means no printed rows: the caller keeps its unread count."""
    blank = np.full((200, 400), 250, dtype=np.uint8)
    assert row_bands(blank, 10, 190, 10, 390) is None


def test_row_bands_returns_the_intervals_between_the_rules():
    gray = _drawn_table()
    bands = row_bands(gray, 100, 160, _EDGES[0] + 5, _EDGES[-1] - 5)
    assert [round(band["top"]) for band in bands] == [100, 120, 140]
    assert [round(band["bottom"]) for band in bands] == [120, 140, 159]


def test_spans_give_a_merged_label_cell_its_whole_extent():
    """The party column has no rule inside the merged cell, so one span covers it."""
    gray = _drawn_table()
    spans = _spans(gray, 72, 168, _EDGES[PARTY] + 3, _EDGES[PARTY + 1] - 3)
    rounded = [(round(lower), round(upper)) for lower, upper in spans]
    assert (160, 167) in rounded or rounded[-1][0] >= 159, spans
    assert any(lower <= 100 and upper >= 160 for lower, upper in rounded), spans
    assert not any(100 < lower < 160 for lower, upper in rounded), spans


def test_overlap_prefers_a_box_whose_baseline_has_drifted():
    band = {"top": 120.0, "bottom": 140.0}
    drifted = {"y": 124.0, "y2": 147.0}
    assert _overlap(band, drifted) == 16.0
    assert _overlap({"top": 140.0, "bottom": 160.0}, drifted) == 7.0
    # A zero-height box (OCR gave only a baseline) is accepted by containment.
    assert _overlap(band, {"y": 125.0}) == 1.0
    assert _overlap(band, {"y": 145.0}) == 0.0


def test_column_of_places_a_centre_in_its_own_band():
    bands = [(0.0, 10.0), (10.0, 20.0)]
    assert _column_of(4.0, bands) == 0
    assert _column_of(10.0, bands) == 1
    assert _column_of(25.0, bands) is None


def _year_rows(rows):
    """Printed rows that state a financial year (not the heading row)."""
    selected = []
    for row in rows:
        text = _band_text(row["texts"].get(PERIOD, []))
        if len(text) == 7 and text[4] == "-" and text[:4].isdigit() and text[5:].isdigit():
            selected.append(row)
    return selected


def test_band_table_repeats_a_merged_label_into_every_printed_row():
    """A party name printed once against three years governs all three rows."""
    items, gray = _drawn_page()
    bands = [(float(left), float(right)) for left, right in zip(_EDGES, _EDGES[1:])]
    rows = _band_table(gray, items, 72.0, 168.0, bands, [PARTY, NATURE])
    assert rows is not None
    year_rows = _year_rows(rows)
    assert len(year_rows) == 3, [row["top"] for row in rows]
    for row in year_rows:
        assert _band_text(row["texts"][PARTY]) == "Alpha Traders"
        assert _band_text(row["texts"][NATURE]) == "Loan Taken"


def test_band_table_binds_a_value_to_its_own_period_not_its_neighbour():
    """The drifted boxes stay with the year their own period label is printed in."""
    items, gray = _drawn_page()
    bands = [(float(left), float(right)) for left, right in zip(_EDGES, _EDGES[1:])]
    rows = _band_table(gray, items, 72.0, 168.0, bands, [PARTY, NATURE])
    by_period = {
        _band_text(row["texts"][PERIOD]): _band_text(row["texts"][TAKEN])
        for row in _year_rows(rows)
    }
    assert by_period == {"2023-24": "10.00", "2024-25": "5.00", "2025-26": "12.00"}
    assert _band_confidence(rows[0]["texts"][TAKEN]) == pytest.approx(0.98)


def test_parse_page_reads_one_value_per_period_and_never_shifts_a_year():
    """End to end: three years, three movements, no balance reported."""
    items, gray = _drawn_page()
    parsed = parse_page(1, items, gray, scale=2.0)
    assert parsed["blocks"] == 1
    readings = [
        (transaction["period"], round(transaction["amount"], 2), transaction["column"])
        for transaction in parsed["transactions"]
    ]
    assert readings == [
        ("FY2024", 10.0, "loan_taken"),
        ("FY2025", 5.0, "loan_taken"),
        ("FY2026", 12.0, "loan_taken"),
    ], readings
    assert {transaction["counterparty"] for transaction in parsed["transactions"]} == {
        "Alpha Traders"
    }
    assert {transaction["unit"] for transaction in parsed["transactions"]} == {"INR_LAKHS"}
    assert {transaction["reading"] for transaction in parsed["transactions"]} == {
        "ocr_geometry"
    }
    assert parsed["unread"] == 0, parsed["reasons"]


def test_parse_page_keeps_a_nature_that_does_not_close_unread():
    """Broken arithmetic is never repaired by moving a figure to a neighbour."""
    items, gray = _drawn_page()
    # FY 2024-25 closing is printed as 15.00; make that one printed figure
    # 16.00 so opening 10.00 + taken 5.00 no longer closes against it.  (The
    # FY 2025-26 opening is also 15.00 and is deliberately left alone.)
    for item in items:
        left, right = _EDGES[CLOSING], _EDGES[CLOSING + 1]
        if item["text"] == "15.00" and left <= (item["x"] + item["x2"]) / 2 < right:
            item["text"] = "16.00"
    parsed = parse_page(1, items, gray, scale=2.0)
    periods = [transaction["period"] for transaction in parsed["transactions"]]
    assert "FY2025" not in periods, periods
    assert parsed["reasons"].get("row_does_not_close_against_its_balances") == 3


def test_a_band_naming_two_quantities_is_refused():
    """A missed column rule must not bind two columns' amounts to one role."""
    assert column_roles(["Opening Balance"]) == ["opening_balance"]
    assert column_roles(["Name of the Related Party"]) == ["party"]
    assert set(column_roles(["Purchases during the Year", "Amount Paid"])) == {
        "purchase_of_goods",
        "payment_made",
    }
    assert column_roles(["Financial Year", "Amount"]) == []


# ----------------------------------------------------------------------
# R.K. Fashion Note 31: the live regression (OCR)
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def rk_note():
    return read_related_party_note(str(RK_RHP), [308, 309, 310])


def test_rk_note_reads_the_table_pages_and_not_the_statements_after_them(rk_note):
    """Continuation is decided by the repeated header band, not by adjacency."""
    assert rk_note["found"] is True
    assert rk_note["pages"] == [308, 309], rk_note["note"]
    assert rk_note["state"] == "PARTIAL", rk_note["note"]


def test_rk_note_reports_the_twenty_three_reconstructable_values(rk_note):
    """Row count is evidence only because every row closes against its balances."""
    transactions = rk_note["transactions"]
    assert len(transactions) == 23, [
        (transaction["counterparty"], transaction["period"], transaction["amount"])
        for transaction in transactions
    ]
    assert {transaction["reading"] for transaction in transactions} == {"ocr_geometry"}
    assert {transaction["unit"] for transaction in transactions} == {"INR_LAKHS"}
    assert all(transaction["page"] in (308, 309) for transaction in transactions)


def test_rk_note_binds_the_recovered_rows_to_the_year_their_balances_close_in(rk_note):
    """The two rows the previous reader lost, with the arithmetic that proves them.

    Mohammed Usman: 47.21 + 216.00 - 213.31 = 49.90 (the printed closing).
    M.K. Jewellers:  36.88 + 9.13 - 16.02 = 29.99, printed 29.98.
    """
    rows = {
        (transaction["counterparty"], transaction["category"], transaction["period"]): round(
            transaction["amount"], 2
        )
        for transaction in rk_note["transactions"]
    }
    assert rows[("Mohammed Usman", "loan_taken", "FY2024")] == 216.00
    assert rows[("Mohammed Usman", "loan_repaid", "FY2024")] == 213.31
    assert rows[("M.K.Jewellers", "purchase_of_goods", "3M-2026-06-30")] == 9.13
    assert rows[("M.K.Jewellers", "payment_made", "3M-2026-06-30")] == 16.02


def test_rk_note_keeps_every_earlier_reading(rk_note):
    """The correction adds rows; it does not trade one reading for another."""
    rows = {
        (transaction["counterparty"], transaction["category"], transaction["period"]): round(
            transaction["amount"], 2
        )
        for transaction in rk_note["transactions"]
    }
    earlier = {
        ("Mohammed Imran", "loan_repaid", "FY2024"): 42.50,
        ("Shaistah Usman", "loan_taken", "FY2024"): 11.00,
        ("Shaistah Usman", "loan_repaid", "FY2024"): 15.00,
        ("MK.Jewellers", "loan_repaid", "FY2024"): 118.53,
        ("Valuable Vintrade Pvt.Ltd.", "loan_repaid", "FY2024"): 47.54,
        ("Variety Fashion Accessories Pvt.Ltd.*", "loan_repaid", "FY2024"): 39.00,
        ("Variety Fashion Accessories Pvt.Ltd.*", "payment_made", "FY2024"): 32.58,
        ("M.K.Jewellers", "purchase_of_goods", "FY2026"): 72.06,
        ("M.K.Jewellers", "payment_made", "FY2026"): 85.64,
        ("M.K.Jewellers", "purchase_of_goods", "FY2025"): 68.46,
        ("M.K.Jewellers", "payment_made", "FY2025"): 18.02,
    }
    for key, amount in earlier.items():
        assert rows.get(key) == amount, (key, rows.get(key))


def test_rk_note_reads_a_merged_label_cell_whole(rk_note):
    """A nature printed over three lines is one phrase, not its first line.

    Mohammed Usman's row states "Advances against Investment" in a merged
    nature cell.  The cell's third line is set densely enough to look like a
    printed rule to a dark-fraction test, which split the cell and truncated
    the description to "Advances against".  A rule is a continuous stroke, so
    the label is recovered whole and printed with the row it belongs to.
    """
    rows = {
        (transaction["counterparty"], transaction["period"]): transaction
        for transaction in rk_note["transactions"]
    }
    advances = rows[("Mohammed Usman", "FY2026")]
    assert advances["category_label"] == "Advances against Investment"
    assert advances["category"] == "loan_repaid"
    assert round(advances["amount"], 2) == 38.44
    # The interim column states the same balance twice and no movement, so it
    # is not a transaction and is not reported as one.
    assert ("Mohammed Usman", "3M-2026-06-30") not in rows


def test_rk_note_reports_no_balance_and_no_negative_balance_as_a_movement(rk_note):
    """A printed negative balance is a stock, never a repayment."""
    for transaction in rk_note["transactions"]:
        assert transaction["column"] not in ("opening_balance", "closing_balance")
        assert transaction["amount"] > 0, transaction
        # The remuneration block has only a closing balance and no control
        # total, so nothing from it may be reported.
        assert transaction["category"] not in ("remuneration", "merger_consideration")


def test_rk_note_reasons_are_counted_not_hidden(rk_note):
    reasons = rk_note["reasons"]
    assert reasons.get("block_without_opening_and_closing_control") == 30, reasons
    assert reasons.get("row_does_not_close_against_its_balances") == 10, reasons
    assert reasons.get("row_without_period") == 7, reasons


def test_rk_categories_are_all_non_revenue(rk_note):
    """So the Module D numerator stays unknown; nothing is promoted to revenue."""
    categories = {transaction["category"] for transaction in rk_note["transactions"]}
    assert categories == {"loan_taken", "loan_repaid", "purchase_of_goods", "payment_made"}
    for category in categories:
        assert rpt_categories.is_revenue_category(category) is False, category
