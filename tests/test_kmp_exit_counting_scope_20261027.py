"""The ``kmp_exits_2y`` counting rule, pinned as the regression baseline for A33.

Governance record ``handoff/decisions/A33-kmp-exit-counting-scope.md`` asks one
question and **no code change is made pending it**: does "KMP exit" mean *only*
Key Managerial Personnel (CEO/MD/WTD/CFO/Company Secretary/Manager), or every
dated exit read from the changes-in-directorate table -- a table that carries
board rows and KMP rows under a single caption ("Changes in our Board" on one
page, "Changes in the Key Managerial Personnel" on another)?

The rule implemented and merged in PR #12, and documented with cross-issuer
validation in ``handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md``
Revision 25, is the second: ``directorate.count_exits`` counts every row whose
``event`` is an exit type among the rows the reader established, **regardless of
the designation**, inside the 24 calendar months ending at the offer open date.

These tests therefore pin the *current* rule issuer-neutrally, so that the
pending decision has a regression baseline and its measured impact is visible
rather than argued:

* a verified KMP exit counts, and so does a non-KMP board exit -- the exact row
  the proposed KMP-only reading would exclude;
* a mixed table counts every exit, not one per category;
* duplicate rows are counted literally, and a role outside the designation
  vocabulary does not suppress an exit;
* the window is anchored on the offer open date and inclusive at both ends;
* appointments are not exits, an exit outside the window is not counted, and a
  missing anchor is UNKNOWN rather than a zero.

No weight, boundary, threshold, penalty, knockout or criterion definition is
touched.  Nothing here asserts that the KMP-only reading is wrong; it records
what the engine does today so the decision can be measured against it.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from ipo_screening.canonical_input import build_canonical_input
from ipo_screening.derived import derive
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.directorate import count_exits, parse_changes_table
from ipo_screening.extraction.interfaces import RawExtraction
from ipo_screening.pipeline import load_config

ANCHOR = date(2026, 10, 21)

# A table that carries both categories under one caption, as the real filings do.
MIXED_TABLE = """Changes in our Board and Key Managerial Personnel
Name Designation Date of change Reason
Anika Rao Independent Director June 25, 2026 Resignation due to personal commitments
Vikram Bhatt Chief Financial Officer June 25, 2026 Resignation under Section 168 of the Companies Act
Mira Patel Company Secretary June 29, 2026 Cessation as Company Secretary
Rohan Mehta Non-Executive Director June 30, 2026 Retirement on attaining the age of superannuation
Sanjay Kumar Chief Operating Officer July 01, 2026 Appointment as Chief Operating Officer
"""


def _event(name, role, event, when, reason=""):
    return {
        "name": name,
        "role": role,
        "event": event,
        "date": when.isoformat(),
        "reason": reason,
    }


def _events(block):
    return parse_changes_table(block)["events"]


# ---------------------------------------------------------------------------
# 1-2. The two readings the decision turns on, kept visibly apart
# ---------------------------------------------------------------------------


def test_a_verified_kmp_exit_inside_the_window_counts():
    events = [_event("Vikram Bhatt", "chief financial officer", "resignation", date(2026, 6, 25))]
    assert count_exits(events, ANCHOR) == 1


def test_a_non_kmp_board_exit_inside_the_window_counts_under_the_current_rule():
    """The row the proposed KMP-only reading would exclude.

    ``count_exits`` does not consult ``role`` at all, so an independent-director
    resignation counts exactly like a CFO resignation.  That is the behaviour
    A33 is asked to decide on; this test is the baseline, not a verdict.
    """
    events = [_event("Anika Rao", "independent director", "resignation", date(2026, 6, 25))]
    assert count_exits(events, ANCHOR) == 1


# ---------------------------------------------------------------------------
# 3-5. Mixed tables, duplicates and unrecognised designations
# ---------------------------------------------------------------------------


def test_a_real_table_is_read_and_every_exit_inside_the_window_counts():
    events = _events(MIXED_TABLE)
    assert [e["event"] for e in events] == [
        "resignation",
        "resignation",
        "cessation",
        "retirement",
        "appointment",
    ]
    assert [e["role"] for e in events] == [
        "independent director",
        "chief financial officer",
        "company secretary",
        "non-executive director",
        "chief operating officer",
    ]
    # Four exits (two board, two KMP); the appointment is not one.
    assert count_exits(events, ANCHOR) == 4


def test_duplicate_rows_are_counted_literally_not_deduped():
    row = _event("Mira Patel", "company secretary", "resignation", date(2026, 6, 29))
    assert count_exits([row, dict(row)], ANCHOR) == 2


def test_an_unrecognised_designation_does_not_suppress_an_exit():
    """Fail-closed is for the *count*, never for a role the reader did not map.

    A row whose designation is outside the title vocabulary is still an exit
    event with a date; the count must not become UNKNOWN because a role string
    was not recognised.
    """
    events = [
        _event("Nomineee of the Promoter", "nominee of the promoter", "resignation", date(2026, 6, 25)),
        _event("Anika Rao", "independent director", "resignation", date(2026, 6, 25)),
    ]
    assert count_exits(events, ANCHOR) == 2


# ---------------------------------------------------------------------------
# 6-8. The window
# ---------------------------------------------------------------------------


def test_the_window_is_anchored_on_the_offer_open_date_and_inclusive_at_both_ends():
    inside = _event("A One", "independent director", "resignation", date(2024, 10, 21))
    just_outside = _event("A Two", "independent director", "resignation", date(2024, 10, 20))
    assert count_exits([inside], ANCHOR) == 1
    assert count_exits([just_outside], ANCHOR) == 0
    assert count_exits([inside, just_outside], ANCHOR) == 1


def test_an_exit_outside_the_window_is_not_counted():
    events = [
        _event("Old Exit", "chief financial officer", "resignation", date(2023, 1, 10)),
        _event("New Exit", "chief financial officer", "resignation", date(2026, 2, 10)),
    ]
    assert count_exits(events, ANCHOR) == 1


def test_appointments_inside_the_window_are_not_counted():
    events = [
        _event("New Hire", "chief financial officer", "appointment", date(2026, 2, 10)),
        _event("Re-designated", "whole-time director", "other", date(2026, 3, 10)),
    ]
    assert count_exits(events, ANCHOR) == 0


def test_a_missing_anchor_is_unknown_not_zero():
    row = _event("Vikram Bhatt", "chief financial officer", "resignation", date(2026, 6, 25))
    assert count_exits([row], None) is None


# ---------------------------------------------------------------------------
# 9-11. The builder carries the events and derives the count
# ---------------------------------------------------------------------------


def _doc():
    return SimpleNamespace(
        source_id="RHP-TEST-KMP",
        company_name="Counting Test Limited",
        to_source_ref_dict=lambda: {
            "source_id": "RHP-TEST-KMP",
            "source_type": "RHP",
            "uri": "counting-test.json",
        },
    )


def _builder(extractions=(), reference_base=None):
    return CanonicalInputBuilder(
        doc=_doc(),
        extractions=list(extractions),
        reference_base=reference_base,
        allow_fixture_fallbacks=False,
    )


def test_builder_derives_the_count_from_the_events_and_supersedes_a_curated_value():
    events = _events(MIXED_TABLE)
    out = _builder(
        reference_base={"governance": {"kmp_exits_2y": 0}},
        extractions=[
            RawExtraction(field_path="governance.board_changes", candidate_value=events),
            RawExtraction(field_path="coverage.governance.board_changes", candidate_value="DISCLOSED"),
            RawExtraction(field_path="issue.open_date", candidate_value="2026-10-21"),
        ],
    ).build()
    # An evidenced count beats the unevidenced curated zero.
    assert out["governance"]["kmp_exits_2y"] == 4
    assert out["coverage"]["governance.kmp_exits_2y"] == "DISCLOSED"


def test_builder_leaves_the_count_unknown_when_the_table_was_not_read():
    out = _builder(
        extractions=[RawExtraction(field_path="coverage.governance.board_changes", candidate_value="UNREAD")],
    ).build()
    assert out["governance"]["kmp_exits_2y"] is None
    assert out["coverage"]["governance.kmp_exits_2y"] == "UNREAD"


def test_builder_reports_partial_when_no_offer_date_anchors_the_window():
    events = _events(MIXED_TABLE)
    out = _builder(
        extractions=[
            RawExtraction(field_path="governance.board_changes", candidate_value=events),
            RawExtraction(field_path="coverage.governance.board_changes", candidate_value="DISCLOSED"),
        ],
    ).build()
    assert out["governance"]["kmp_exits_2y"] is None
    assert out["coverage"]["governance.kmp_exits_2y"] == "PARTIAL"


# ---------------------------------------------------------------------------
# 12. The criterion consumes the count
# ---------------------------------------------------------------------------


def _canonical(exits, independent=False):
    raw = {
        "ipo_id": "KMP-TEST",
        "company_name": "Counting Test Limited",
        "issue": {"price_band_high": 100.0, "open_date": "2026-10-21"},
        "capital_structure": {},
        "governance": {"kmp_exits_2y": exits, "board_independent_majority": independent},
        "financials": {"periods": []},
    }
    return build_canonical_input(raw)


def _bucket(exits, independent=False):
    config = load_config("config/ipo-config.v1.5.0.json")
    metrics = derive(_canonical(exits, independent), config, peers=None, market=None).metrics
    return metrics["board_kmp_bucket"].value


def test_criterion_bucket_is_high_churn_at_two_exits_and_other_at_one():
    assert _bucket(2) == "high_churn"
    assert _bucket(6) == "high_churn"
    assert _bucket(1) == "other"


def test_criterion_bucket_stays_unknown_when_the_count_is_not_established():
    config = load_config("config/ipo-config.v1.5.0.json")
    metrics = derive(_canonical(None), config, peers=None, market=None).metrics
    bucket = metrics["board_kmp_bucket"]
    assert bucket.value is None
    assert "not disclosed" in (bucket.reason or "")
