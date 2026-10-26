"""Related-party disclosure reader: period-matrix layout (report section 30).

Proven defect (2026-10-26).  ``extract_related_party_transactions`` returned
zero extractions on the Paras Healthcare RHP even though the filing discloses
related-party transactions in full: its disclosure is not a
transaction-category table over three annual columns (the layout the original
reader assumed) but a *matrix* -- "SUMMARY OF RELATED PARTY TRANSACTIONS" over
five period columns (three months ended 30 June 2026, three months ended
30 June 2025, FY2026, FY2025, FY2024), each paired with a "% revenue from
operations" column, one row per (counterparty, nature of transaction).  No
anchor was found, so the section was indistinguishable from one that was never
read and Module D ``rpt`` / knockout K6 stayed unverified.

What this suite proves:

* the real Paras disclosure is read row by row: counterparty, nature of
  transaction, each disclosed period, amount, the disclosed revenue share and
  a verbatim source line, in the unit the note declares;
* the period columns are mapped from the table header, and an interim column
  is labelled as an interim period (``3M-2026-06-30``) rather than as a
  financial year;
* a "-" cell is undisclosed, never zero, and emits nothing;
* the reader stops at the outstanding-balances disclosure that follows (a
  balance is not a transaction) and never reads a header row as an amount row;
* numbers the text layer splits at a kerning point ("0." + "12") are one cell;
* coverage distinguishes "read and disclosed" from "located but unreadable"
  (aggregate-only summaries, like R.K. Fashion's) and from "never seen";
* the metric path consumes annual columns only, so an interim column cannot
  suppress the annual related-party share, and a disclosure with no
  revenue-type category leaves the share unknown rather than zero.

Nothing here is issuer-specific: the layout rules are geometric (column
position, numeric cell shape, header words), and no threshold or scoring rule
is added or changed.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import RawExtraction
from ipo_screening.extraction.sections import SectionExtractor

PARAS_RHP = (
    REPO_ROOT
    / "evidence"
    / "non-authoritative"
    / "paras-healthcare"
    / "U85110HR1987PLC035823 _ParasHealthcare.pdf"
)
RK_RHP = REPO_ROOT / "handoff" / "reference" / "U18109WB2010PLC144256-R.K Fashion accessories.pdf"

pytestmark = pytest.mark.usefixtures("cached_pdf_text")


# ----------------------------------------------------------------------
# Layout primitives: no PDF needed
# ----------------------------------------------------------------------
def test_period_labels_distinguish_interim_from_annual():
    label = SectionExtractor._rpt_period_label
    pattern = SectionExtractor._RPT_PERIOD_LABEL
    cases = {
        "For the three months ended 30 June, 2026": "3M-2026-06-30",
        "For the three months period ended 30 June 2025": "3M-2025-06-30",
        "For the Fiscal 2026": "FY2026",
        "For the year ended 31 March 2025": "FY2025",
        "For Financial Year ended March 31, 2024": "FY2024",
        "For stub period ended June 30, 2026": "INTERIM-2026-06-30",
    }
    for text, expected in cases.items():
        found = [label(m) for m in pattern.finditer(text)]
        assert found == [expected], (text, found)
    # A bare year list in a preamble is not a period column.
    assert [m for m in pattern.finditer("with Fiscals 2026, 2025 and 2024")] == []


def test_kerning_split_number_is_one_cell():
    cells = [
        (113.66, "Post"),
        (173.42, "0."),
        (180.29, "12"),
        (208.49, "0.00%"),
        (252.89, "0."),
        (259.73, "1"),
        (264.17, "3"),
        (291.29, "0.00%"),
    ]
    label, amounts = SectionExtractor._rpt_split_row(cells)
    assert [text for _, text in label] == ["Post"]
    assert [text for _, text in amounts] == ["0.12", "0.00%", "0.13", "0.00%"]


def test_bare_percent_fragment_belongs_to_its_share():
    cells = [(113.66, "Directors"), (452.14, "0.0"), (463.42, "2"), (467.98, "%")]
    _, amounts = SectionExtractor._rpt_split_row(cells)
    assert [text for _, text in amounts] == ["0.02%"]


def test_header_line_is_not_an_amount_row():
    is_amount = SectionExtractor._rpt_is_amount_row
    assert is_amount(["21.97", "0.47%", "-"]) is True
    assert is_amount(["2026", "2025", "2026"]) is False
    assert is_amount(["%", "%"]) is False


def test_aggregate_control_totals_are_not_transactions():
    pattern = SectionExtractor._RPT_AGGREGATE_LABEL
    for text in (
        "Sum of all related party transactions",
        "Revenue from Operations",
        "Sum of all related party transaction as a % of revenue from operations",
        "Total",
    ):
        assert pattern.match(text), text
    for text in ("Short term employee benefits", "Rental income", "Advance to key managerial person"):
        assert not pattern.match(text), text


# ----------------------------------------------------------------------
# Builder metric path: annual columns only, never a fabricated zero
# ----------------------------------------------------------------------
def _txn(category, counterparty, period, amount, unit, idx, label=None):
    return RawExtraction(
        field_path=f"governance.related_party_transactions[{idx}]",
        candidate_value={
            "category": category,
            "category_label": label or category.replace("_", " "),
            "counterparty": counterparty,
            "period": period,
            "amount": amount,
            "unit": unit,
            "page": 10,
        },
        quote=f"{counterparty} {amount}",
        page=10,
    )


def _gov(periods, txns, reporting_unit="INR_CRORES"):
    doc = SimpleNamespace(
        source_id="RHP-MATRIX-TEST",
        company_name="Matrix Test Limited",
        to_source_ref_dict=lambda: {"source_id": "RHP-MATRIX-TEST"},
    )
    extractions = [
        RawExtraction(field_path="financials.periods", candidate_value=periods),
        RawExtraction(field_path="financials.reporting_unit", candidate_value=reporting_unit),
    ] + txns
    return CanonicalInputBuilder(doc, extractions, allow_fixture_fallbacks=False).build()


def test_interim_column_does_not_suppress_the_annual_share():
    periods = [
        {"fy": "FY2025", "revenue": 1000.0},
        {"fy": "FY2026", "revenue": 1200.0},
    ]
    txns = [
        _txn("sale_of_services", "Meridian Advisors LLP", "FY2026", 120.0, "INR_CRORES", 0),
        _txn("sale_of_services", "Meridian Advisors LLP", "FY2025", 60.0, "INR_CRORES", 1),
        # An interim column of the same matrix disclosure: no annual share.
        _txn("sale_of_services", "Meridian Advisors LLP", "3M-2026-06-30", 40.0, "INR_CRORES", 2),
    ]
    gov = _gov(periods, txns)["governance"]
    assert gov["rpt_pct_revenue"] == pytest.approx(10.0)  # 120 / 1200
    assert gov["rpt_pct_of_revenue_growth"] == pytest.approx(4.0)  # 10.0 - 6.0


def test_disclosure_without_a_revenue_category_leaves_the_share_unknown():
    periods = [{"fy": "FY2026", "revenue": 1000.0}, {"fy": "FY2025", "revenue": 900.0}]
    txns = [
        _txn("unclassified", "Dr. Example", "FY2026", 53.77, "INR_MILLIONS", 0,
             label="Short term employee benefits"),
        _txn("unclassified", "Example Society", "FY2026", 0.02, "INR_MILLIONS", 1,
             label="Rental income"),
    ]
    gov = _gov(periods, txns)["governance"]
    # The approved numerator has no category for these rows; that is not a
    # measured zero and must not become one.
    assert gov["rpt_pct_revenue"] is None
    assert gov["rpt_pct_of_revenue_growth"] is None
    # The rows themselves survive as evidence.
    rows = [
        ex.candidate_value
        for ex in CanonicalInputBuilder(
            SimpleNamespace(
                source_id="RHP-MATRIX-TEST",
                company_name="Matrix Test Limited",
                to_source_ref_dict=lambda: {"source_id": "RHP-MATRIX-TEST"},
            ),
            [RawExtraction("financials.periods", periods)]
            + [RawExtraction("financials.reporting_unit", "INR_MILLIONS")]
            + txns,
            allow_fixture_fallbacks=False,
        ).extractions
        if ex.field_path.startswith("governance.related_party_transactions[")
    ]
    assert len(rows) == 2


# ----------------------------------------------------------------------
# Real filing: Paras Healthcare RHP pp. 92-93 (slow)
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def paras_extractions():
    if not PARAS_RHP.exists():  # pragma: no cover - fixture absent
        pytest.skip("Paras Healthcare RHP is not present in this checkout")
    import pypdf

    from ipo_screening.extraction.interfaces import SourceDocument

    doc = SourceDocument(source_id="PARAS-RHP", uri=str(PARAS_RHP), content_hash="paras")
    extractor = SectionExtractor(doc, pypdf.PdfReader(str(PARAS_RHP)))
    return extractor, extractor.extract_related_party_transactions()


def _rows(extractions):
    return [ex.candidate_value for ex in extractions if isinstance(ex.candidate_value, dict)]


def _coverage(extractions):
    records = [ex for ex in extractions if ex.field_path.startswith("coverage.")]
    assert len(records) == 1
    return records[0]


@pytest.mark.slow
def test_paras_disclosure_is_read_and_reported_disclosed(paras_extractions):
    _, extractions = paras_extractions
    rows = _rows(extractions)
    assert len(rows) >= 60
    coverage = _coverage(extractions)
    assert coverage.field_path == "coverage.governance.rpt_pct_revenue"
    assert coverage.candidate_value == "DISCLOSED"
    assert "period-matrix" in coverage.raw_text
    assert {row["unit"] for row in rows} == {"INR_MILLIONS"}
    assert {row["page"] for row in rows} == {92, 93}


@pytest.mark.slow
def test_paras_amounts_periods_and_disclosed_share(paras_extractions):
    _, extractions = paras_extractions
    rows = _rows(extractions)
    dharminder = {
        row["period"]: row
        for row in rows
        if row["category_label"] == "Short term employee benefits and Other long term benefits"
        # The source renders the name across lines ("Dharminde" / "r Kumar");
        # the wrap is preserved as a space, so match on the fragment.
        and "Dharminde" in row["counterparty"]
    }
    assert set(dharminder) == {
        "3M-2026-06-30",
        "3M-2025-06-30",
        "FY2026",
        "FY2025",
        "FY2024",
    }
    assert dharminder["FY2026"]["amount"] == pytest.approx(53.77)
    assert dharminder["FY2024"]["amount"] == pytest.approx(53.77)
    assert dharminder["3M-2026-06-30"]["amount"] == pytest.approx(21.97)
    assert dharminder["3M-2025-06-30"]["amount"] == pytest.approx(13.44)
    # The disclosure prints the revenue share next to each amount; it is kept,
    # not recomputed, and never treated as the amount.
    assert dharminder["FY2026"]["pct_revenue"] == pytest.approx(0.33)
    assert dharminder["FY2024"]["pct_revenue"] == pytest.approx(0.48)
    # No approved revenue-type category is disclosed for these rows.
    assert dharminder["FY2026"]["category"] == "unclassified"


@pytest.mark.slow
def test_paras_counterparty_and_nature_are_separate_columns(paras_extractions):
    _, extractions = paras_extractions
    rows = _rows(extractions)
    facilities = [
        row
        for row in rows
        if row["counterparty"].startswith("Paras RE Facilities")
        and row["period"] == "FY2026"
    ]
    assert len(facilities) == 1
    row = facilities[0]
    # The source wraps the cell text mid-word; the wrap is preserved as a
    # space and never silently "repaired".
    assert row["counterparty"] == "Paras RE Facilities Manageme nt Private Limited"
    assert row["category_label"] == (
        "Repair & maintenan ce and power & fuel (inc. applicable taxes)"
    )
    assert row["amount"] == pytest.approx(8.93)
    society = next(
        row
        for row in rows
        if row["counterparty"] == "Ch. Ved Ram Nagar Medical Education & Research Society"
        and row["period"] == "FY2026"
    )
    assert society["category_label"] == "Rental income"
    assert society["amount"] == pytest.approx(0.02)


@pytest.mark.slow
def test_paras_undisclosed_cells_are_absent_not_zero(paras_extractions):
    _, extractions = paras_extractions
    rows = _rows(extractions)
    advance = [
        row for row in rows if row["category_label"] == "Advance to key managerial person"
    ]
    # One amount in FY2026 only; the other four columns print "-".
    assert [row["period"] for row in advance] == ["FY2026"]
    assert advance[0]["amount"] == pytest.approx(1.20)
    share_based = [row for row in rows if row["category_label"] == "Share based payment expenses"]
    assert sorted(row["period"] for row in share_based) == [
        "3M-2026-06-30",
        "FY2026",
    ]


@pytest.mark.slow
def test_paras_quotes_are_verbatim_source_lines(paras_extractions):
    extractor, extractions = paras_extractions
    for ex in extractions:
        if not isinstance(ex.candidate_value, dict):
            continue
        assert ex.quote, ex.locator
        assert ex.quote in extractor.extract_page_text(ex.candidate_value["page"]), ex.locator


@pytest.mark.slow
def test_paras_balances_table_is_not_read_as_transactions(paras_extractions):
    _, extractions = paras_extractions
    for row in _rows(extractions):
        # PDF p. 94 is the outstanding-balances disclosure.
        assert row["page"] in (92, 93)
        assert "balance" not in row["category_label"].lower()


@pytest.mark.slow
def test_aggregate_only_summary_is_partial_coverage_not_values():
    if not RK_RHP.exists():  # pragma: no cover - fixture absent
        pytest.skip("R.K. Fashion RHP is not present in this checkout")
    import pypdf

    from ipo_screening.extraction.interfaces import SourceDocument

    doc = SourceDocument(source_id="RK-RHP", uri=str(RK_RHP), content_hash="rk")
    extractor = SectionExtractor(doc, pypdf.PdfReader(str(RK_RHP)))
    extractions = extractor.extract_related_party_transactions()
    # The summary prints "Sum of all related party transactions", revenue and
    # the share -- control totals, not per-counterparty rows.
    assert _rows(extractions) == []
    coverage = _coverage(extractions)
    assert coverage.candidate_value == "PARTIAL"
    assert "aggregate" in coverage.raw_text
