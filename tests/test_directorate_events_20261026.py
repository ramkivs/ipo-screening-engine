"""Changes-in-directorate reader: layouts, event types and the 24-month window.

Report section 26.  The tables below are the *literal* cell text of two real
filings (Paras Healthcare p. 346/p. 357, Vishal Nirmiti p. 306/p. 319), as the
page decoder returns it -- including the column order, the wrapped cells and
the version where one physical line carries several rows.  Nothing here decodes
a document, so the module stays in the fast synthetic tier.
"""

from __future__ import annotations

from datetime import date

import pytest

from ipo_screening.extraction.directorate import (
    classify_event,
    count_exits,
    find_all_dates,
    minus_months,
    parse_changes_table,
)

# Paras p. 346: Name | Designation | Date | Reason, with a numbered footnote.
PARAS_BOARD = """Name Designation (at the time of appointment / change in designation / cessation) Date of appointment / change in designation / cessation Reason
Ramesh Abhishek Independent Director July 12, 2024  Resignation due to personal commitments
Usha Rajeev(1) Additional Director June 12, 2024 Appointment
Upendra Prasad Singh(2) Additional Director June 12, 2024 Appointment
Nakul Anand(3) Additional Director February 1, 2024 Appointment
Saurabh Sood(4) Additional Director  February 1, 2024 Appointment
Saurabh Sood Independent Director January 31, 2024 Resignation under Section 168 of the Companies Act, 2013 due to restructuring of the Board
Veer Singh Mehta  Non-Executive Director January 31, 2024 Resignation under Section 168 of the Companies Act, 2013 due to professional commitments
(1) The appointment of Usha Rajeev was regularized and was appointed as an Independent Director pursuant to a resolution passed at the AGM held on June 20, 2024.
(2) The appointment of Upendra Prasad Singh was regularized pursuant to a resolution passed at the AGM held on June 20, 2024."""

# Vishal p. 306: Name | Appointment/Change/Cessation | Reason -- the reason wraps
# onto the following line, and there is no designation column.
VISHAL_BOARD = """Name of Director Appointment/Change/ Cessation Reason
Brij B Tapadiya September 16, 2025 Change in designation to Chairman and Whole-Time Director
Dillip Kumar Nanda September 16, 2025 Appointment as Independent Director
Rajgopal Shankarlal Gilada April 16, 2024 Cessation as Non-Executive Director for pre-
occupation and personal reasons
Rajgopal Shankarlal Gilada September 30, 2023 Regularisation as Non-Executive Director"""

# Vishal p. 319: Name | Designation | Date | Reason, wrapped cells.
VISHAL_KMP = """Name Designation Date of
Appointment/Change/
Cessation
Particulars/ Reason
Suhas Ganpat Naik Company Secretary  and
Compliance Officer
September 25, 2025 Appointment as Company
Secretary and Compliance
Officer
Abhijeet Kumudchandra
Shah
Chief Financial Officer September 17, 2025 Appointment as Chief Financial
Officer
Deepak Sagarmal Bandi Vice President -Business
Development (Sleeper
Division)
July 01, 2025 Appointment as Vice President-
Business Development (Sleeper
Division)
Kanagaraj Kamu Reddy Executive Vice President of
Operations
July 01, 2025 Appointment as Executive Vice
President of Operations"""

# Paras p. 357: Name | Date of change | Reason, plus a numbered-notes block that
# carries its own dates.
PARAS_KMP = """Name Date of change Reason
Dr. Amrita Singh  April 1, 2026 Change in reporting structure*
Balkishan Sharma February 10, 2026 Appointment as the Chief Human Resources and Business Transformation Officer
Mangesh Shirodkar  May 22, 2025 Resignation as the Chief Financial Officer - Operations due to personal commitments
Dr. Shashank Teotia February 28, 2026 Resignation as the Group Head Human Resources due to personal commitments
Dr. Santy N Sajan January 31, 2025 Resignation as the Group Chief Operating Officer due to personal commitments
Pradeep Mishra February 21, 2025 Resignation as the Vice President, Supply Chain Management due to personal commitments
Mangesh Shirodkar October 3, 2024 Appointment as the Chief Financial Officer - Operations
Notes: This does not include changes pursuant to re-designation of Key Managerial Personnel and Senior Management."""


def _events(block):
    return parse_changes_table(block)["events"]


# ---------------------------------------------------------------------------
# 1-3. Real layouts are read with names, roles, events and dates
# ---------------------------------------------------------------------------


def test_paras_board_layout_is_read_with_designation_column():
    events = _events(PARAS_BOARD)
    by_name = {(e["name"], e["date"]): e for e in events}

    ramesh = by_name[("Ramesh Abhishek", "2024-07-12")]
    assert ramesh["event"] == "resignation"
    assert ramesh["role"] == "independent director"
    assert ramesh["reason"].startswith("Resignation due to personal commitments")

    # A footnote marker glued to the surname is not part of the name.
    assert ("Usha Rajeev", "2024-06-12") in by_name
    assert by_name[("Usha Rajeev", "2024-06-12")]["event"] == "appointment"
    assert not [e for e in events if "(1)" in (e["name"] or "")]

    # AGM dates inside the footnotes are not directorate rows.
    assert not [e for e in events if e["date"] == "2024-06-20"]
    assert len(events) == 7


def test_vishal_board_layout_rejoins_a_wrapped_reason_and_infers_the_role():
    events = _events(VISHAL_BOARD)
    assert len(events) == 4

    gilada = [e for e in events if e["date"] == "2024-04-16"][0]
    assert gilada["name"] == "Rajgopal Shankarlal Gilada"
    assert gilada["event"] == "cessation"
    # The cell wrapped; the whole reason is recovered, not just its first line.
    assert "pre- occupation and personal reasons" in gilada["reason"]
    # There is no designation column, so the role is taken from the reason.
    assert gilada["role"] == "non-executive director"

    brij = [e for e in events if e["name"] == "Brij B Tapadiya"][0]
    assert brij["event"] == "appointment"
    assert brij["reason"] == "Change in designation to Chairman and Whole-Time Director"


def test_vishal_kmp_layout_handles_wrapped_names_and_titles():
    events = _events(VISHAL_KMP)
    assert [e["name"] for e in events] == [
        "Suhas Ganpat Naik",
        "Abhijeet Kumudchandra Shah",
        "Deepak Sagarmal Bandi",
        "Kanagaraj Kamu Reddy",
    ]
    assert events[0]["role"] == "company secretary and compliance officer"
    assert events[2]["role"].startswith("vice president")
    assert events[3]["role"] == "executive vice president of operations"
    assert all(e["event"] == "appointment" for e in events)


def test_paras_kmp_layout_types_every_row():
    events = _events(PARAS_KMP)
    assert [(e["name"], e["date"], e["event"]) for e in events] == [
        ("Dr. Amrita Singh", "2026-04-01", "other"),
        ("Balkishan Sharma", "2026-02-10", "appointment"),
        ("Mangesh Shirodkar", "2025-05-22", "resignation"),
        ("Dr. Shashank Teotia", "2026-02-28", "resignation"),
        ("Dr. Santy N Sajan", "2025-01-31", "resignation"),
        ("Pradeep Mishra", "2025-02-21", "resignation"),
        ("Mangesh Shirodkar", "2024-10-03", "appointment"),
    ]
    # The "Notes:" block has its own prose and no rows.
    assert not [e for e in events if e["name"] and "Notes" in e["name"]]


# ---------------------------------------------------------------------------
# 4. Event typing distinguishes what the source actually says
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reason, expected",
    [
        ("Resignation under Section 168 of the Companies Act, 2013", "resignation"),
        ("Cessation as Non-Executive Director for pre-occupation", "cessation"),
        ("Retirement on attaining the age of superannuation", "retirement"),
        ("Expiry of his term as an Independent Director", "term_expiry"),
        ("Termination of the term of office of the director", "term_expiry"),
        ("Appointment as Independent Director", "appointment"),
        ("Change in designation to Chairman and Whole-Time Director", "appointment"),
        ("Regularisation as Non-Executive Director", "appointment"),
        ("Change in reporting structure*", "other"),
    ],
)
def test_classify_event(reason, expected):
    assert classify_event(reason) == expected


def test_a_bare_cessation_is_not_promoted_to_resignation():
    """The source said the directorship ceased; it did not say he resigned."""
    events = _events(VISHAL_BOARD)
    gilada = [e for e in events if e["date"] == "2024-04-16"][0]
    assert gilada["event"] == "cessation"


# ---------------------------------------------------------------------------
# 5-7. The 24-month window
# ---------------------------------------------------------------------------


def test_window_boundary_is_inclusive_and_calendar_aware():
    anchor = date(2026, 10, 21)
    events = [
        {"event": "resignation", "date": "2024-10-21"},  # exactly 24 months before
        {"event": "resignation", "date": "2024-10-20"},  # one day outside
        {"event": "resignation", "date": "2026-10-21"},  # the anchor itself
        {"event": "resignation", "date": "2026-10-22"},  # after the anchor
    ]
    assert count_exits(events, anchor) == 2
    assert minus_months(date(2024, 2, 29), 24) == date(2022, 2, 28)


def test_non_exit_events_are_not_counted():
    events = _events(PARAS_BOARD) + _events(PARAS_KMP)
    # Board resignations (Jan/Jul 2024) are older than 24 months from the
    # Paras offer open date; four KMP resignations fall inside it.
    assert count_exits(events, date(2026, 10, 21)) == 4
    assert count_exits(events, date(2024, 12, 31)) == 3


def test_missing_anchor_is_unknown_not_zero():
    assert count_exits(_events(PARAS_KMP), None) is None


def test_undated_exit_row_is_reported_not_silently_dropped():
    block = """Name Designation Date of change Reason
Ramesh Abhishek Independent Director July 12, 2024 Resignation due to personal commitments
Usha Rajeev Independent Director Resignation due to personal commitments"""
    parsed = parse_changes_table(block)
    assert len(parsed["events"]) == 1
    assert parsed["undated_exit_rows"] == 1


# ---------------------------------------------------------------------------
# 8-9. Empty, malformed and non-table text
# ---------------------------------------------------------------------------


def test_empty_table_is_not_an_event_list():
    parsed = parse_changes_table("Name Designation Date Reason")
    assert parsed["events"] == []
    assert parsed["header_seen"] is True


def test_prose_with_dates_is_not_a_directorate_row():
    """A circular date and an AGM date are not directorate events."""
    block = (
        "none of our Directors are declared as Fraudulent Borrowers in terms of RBI master "
        "circular dated July 01, 2016 and the resolution passed at the AGM held on June 20, 2024."
    )
    assert parse_changes_table(block)["events"] == []


def test_malformed_dates_are_ignored():
    block = """Name Date of change Reason
Ramesh Abhishek February 31, 2024 Resignation due to personal commitments"""
    parsed = parse_changes_table(block)
    assert parsed["events"] == []


def test_all_dates_are_found_in_a_multi_row_line():
    text = "A September 16, 2025 x B April 16, 2024 y C 12/07/2024 z"
    assert [d[0].isoformat() for d in find_all_dates(text)] == [
        "2025-09-16",
        "2024-04-16",
        "2024-07-12",
    ]
