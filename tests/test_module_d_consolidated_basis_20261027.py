"""Module D's related-party revenue metric keeps its consolidated basis (s.35).

Owner decision, 2026-10-27: the metric is a **consolidated-basis** share, and

* a related-party figure that the disclosure itself says is *eliminated in
  consolidation* is never part of the numerator — consolidated revenue cannot
  contain it, so dividing it into consolidated revenue would mix two bases;
* where qualifying consolidated-basis revenue cannot be established the fields
  stay **null** (UNKNOWN) — no zero is substituted for missing evidence;
* a standalone-basis exposure measure, if it is ever wanted, is a separate
  metric with its own standalone revenue denominator (not implemented here).

These tests exercise the shared builder path, so the rule holds for every
issuer rather than for one filing.  Two of them read a real filing to show the
decision's effect on the issuer that raised the question.
"""

from __future__ import annotations

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import RawExtraction, SourceDocument
from ipo_screening.extraction.rpt_categories import (
    is_consolidation_eliminated,
    is_revenue_category,
)

PARAS_RHP = (
    REPO_ROOT
    / "evidence"
    / "non-authoritative"
    / "paras-healthcare"
    / "U85110HR1987PLC035823 _ParasHealthcare.pdf"
)


# ----------------------------------------------------------------------
# The disclosure wording, not a category name or an issuer
# ----------------------------------------------------------------------
def test_only_the_disclosure_wording_marks_a_figure_as_eliminated():
    for text in (
        "Transactions eliminated in consolidation",
        "Revenue from sale of healthcare services (eliminated on consolidation)",
        "Elimination of intra-group transactions",
        "Amounts eliminated",
    ):
        assert is_consolidation_eliminated(text) is True, text
    for text in (
        "Revenue from sale of healthcare services (excluding applicable taxes)",
        "Sale of goods",
        "Short term employee benefits",
        None,
        "",
    ):
        assert is_consolidation_eliminated(text) is False, text


# ----------------------------------------------------------------------
# Shared builder path (synthetic issuers)
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


def _builder_gov(periods, txns, reporting_unit="INR_CRORES"):
    doc = SourceDocument(source_id="RHP-TEST", uri="test", content_hash="abc")
    extractions = [
        RawExtraction(field_path="financials.periods", candidate_value=periods),
        RawExtraction(field_path="financials.reporting_unit", candidate_value=reporting_unit),
    ] + txns
    return CanonicalInputBuilder(doc, extractions, allow_fixture_fallbacks=False).build()["governance"]


PERIODS = [{"fy": "FY2025", "revenue": 1000.0}, {"fy": "FY2026", "revenue": 1000.0}]


def test_an_eliminated_row_never_enters_the_numerator():
    """A revenue-type row marked eliminated leaves the metric UNKNOWN."""
    gov = _builder_gov(
        PERIODS,
        [
            _txn(
                "sale_of_services",
                "Group Hospital A",
                "FY2026",
                100.0,
                "INR_CRORES",
                0,
                label="Revenue from sale of healthcare services (eliminated in consolidation)",
            )
        ],
    )
    assert gov["rpt_pct_revenue"] is None
    assert gov["rpt_pct_of_revenue_growth"] is None


def test_an_eliminated_row_does_not_hide_a_supported_row():
    """The exclusion is per row: supported consolidated revenue still counts."""
    gov = _builder_gov(
        PERIODS,
        [
            _txn(
                "sale_of_services",
                "Group Hospital A",
                "FY2026",
                100.0,
                "INR_CRORES",
                0,
                label="Revenue from sale of healthcare services (eliminated in consolidation)",
            ),
            _txn("sale_of_services", "Outside Customer", "FY2026", 40.0, "INR_CRORES", 1),
            _txn("sale_of_services", "Outside Customer", "FY2025", 10.0, "INR_CRORES", 2),
        ],
    )
    # 40 / 1000 = 4%; the eliminated 100 is not in the numerator.
    assert gov["rpt_pct_revenue"] == pytest.approx(4.0)
    # FY2026 share 4% - FY2025 share 1% = 3 pp.
    assert gov["rpt_pct_of_revenue_growth"] == pytest.approx(3.0)


def test_a_missing_amount_is_unknown_not_zero():
    """A year with no stated qualifying amount has no share, not a nil share."""
    gov = _builder_gov(
        [{"fy": "FY2025", "revenue": 1000.0}],
        [_txn("sale_of_goods", "Buyer", "FY2026", 50.0, "INR_CRORES", 0)],
    )
    assert gov["rpt_pct_revenue"] is None
    assert gov["rpt_pct_of_revenue_growth"] is None


def test_the_latest_year_must_be_established_before_a_share_is_reported():
    """The latest audited FY decides the metric; a prior year cannot stand in."""
    gov = _builder_gov(
        [
            {"fy": "FY2025", "revenue": 1000.0},
            {"fy": "FY2026", "revenue": 1200.0},
        ],
        [_txn("sale_of_goods", "Buyer", "FY2025", 50.0, "INR_CRORES", 0)],
    )
    assert gov["rpt_pct_revenue"] is None
    assert gov["rpt_pct_of_revenue_growth"] is None


def test_a_disclosed_amount_is_still_counted_in_full():
    """The fail-closed rules must not suppress a properly disclosed year."""
    gov = _builder_gov(
        PERIODS,
        [
            _txn("sale_of_goods", "Buyer", "FY2026", 120.0, "INR_CRORES", 0),
            _txn("sale_of_goods", "Buyer", "FY2025", 40.0, "INR_CRORES", 1),
        ],
    )
    assert gov["rpt_pct_revenue"] == pytest.approx(12.0)
    assert gov["rpt_pct_of_revenue_growth"] == pytest.approx(8.0)


# ----------------------------------------------------------------------
# The issuer that raised the question
# ----------------------------------------------------------------------
@pytest.mark.slow
def test_paras_keeps_the_metric_unknown_on_a_consolidated_basis():
    """Note 34's eliminated revenue is not counted against consolidated revenue.

    Counting it would give 0.1788% / 0.1116% / 0.0574% for FY2026 / FY2025 /
    FY2024 (report s.34.6) and clear K6 by mixing bases.  The metric stays null,
    and nothing is filled with zero.
    """
    from ipo_screening.extraction import DocumentExtractor

    canonical, _report = DocumentExtractor().extract_from_pdf(
        pdf_path=PARAS_RHP, allow_fixture_fallbacks=False
    )
    gov = canonical["governance"]
    assert gov["rpt_pct_revenue"] is None
    assert gov["rpt_pct_of_revenue_growth"] is None
    # The evidence is still registered, and none of it is a revenue-type row:
    # the summary the engine reads discloses no qualifying consolidated revenue.
    evidence = canonical["_evidence"]
    rpt = [p for p in evidence if p.startswith("governance.related_party_transactions[")]
    assert rpt, "the related-party rows are kept as evidence"
    for path in rpt:
        value = evidence[path].get("value") or {}
        category = str(value.get("category") or "")
        if category:
            assert is_revenue_category(category) is False, path
