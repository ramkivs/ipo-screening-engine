"""Synthetic layer tests, not HD Fire evaluations or fabricated issuer data.

Pin an uncovered contract: only supplied full-FY receivable-days observations
enter the existing YoY metric; marked interim observations cannot trigger it.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ipo_screening.canonical_input import build_canonical_input
from ipo_screening.derived import DerivedMetrics, MetricValue, _receivable_days_yoy_pct
from ipo_screening.extraction.financial_tables import FinancialTableExtractor
from ipo_screening.scoring import _evaluate_penalties


def _metric(periods):
    canonical = build_canonical_input({"financials": {"periods": periods}})
    return _receivable_days_yoy_pct(SimpleNamespace(periods=canonical.full_periods))


def test_marked_interim_is_excluded_even_if_its_days_were_annualized():
    metric = _metric([
        {"fy": "FY2025", "receivable_days": 50},
        {"fy": "FY2026", "receivable_days": 60},
        {"fy": "Q1FY2027", "is_stub": True, "receivable_days": 240},
    ])
    assert metric.is_value
    assert metric.value == pytest.approx(20)


def test_one_full_fy_plus_interim_cannot_supply_yoy():
    metric = _metric([
        {"fy": "FY2026", "receivable_days": 60},
        {"fy": "Q1FY2027", "is_stub": True, "receivable_days": 240},
    ])
    assert metric.is_unknown


def test_missing_latest_full_fy_is_not_backfilled_from_interim_or_older_year():
    metric = _metric([
        {"fy": "FY2024", "receivable_days": 40},
        {"fy": "FY2025", "receivable_days": 50},
        {"fy": "FY2026"},
        {"fy": "Q1FY2027", "is_stub": True, "receivable_days": 80},
    ])
    assert metric.is_unknown


def test_two_full_fy_values_and_zero_prior_contract():
    assert _metric([{"fy": "FY2025", "receivable_days": 50},
                    {"fy": "FY2026", "receivable_days": 80}]).value == pytest.approx(60)
    assert _metric([{"fy": "FY2025", "receivable_days": 0},
                    {"fy": "FY2026", "receivable_days": 80}]).is_not_applicable


@pytest.mark.parametrize("value,points", [(29.99, 0), (30.0, 0), (30.01, -3)])
def test_configured_receivable_threshold_is_strictly_greater_than_30(value, points):
    config = json.loads((Path(__file__).parents[1] / "config/ipo-config.v1.5.0.json").read_text())
    rule = next(p for p in config["penalties"]["items"] if p["id"] == "receivable_days_up")
    derived = DerivedMetrics({"receivable_days_yoy_pct": MetricValue(
        "receivable_days_yoy_pct", "VALUE", value=value)})
    _, items, reserve = _evaluate_penalties({"penalties": {"items": [rule]}}, derived)
    assert items[0]["points"] == points
    assert reserve == 0


def test_receivables_and_revenue_select_same_full_fy_columns_not_interim():
    parser = FinancialTableExtractor(None, SimpleNamespace(pages=[]))
    # Deliberately extreme interim values distinguish leftmost from fiscal selection.
    rows = parser._parse_table_lines(
        "Revenue from operations 999 888 400 300 200\n"
        "Trade receivables 777 666 80 30 20\n",
        [("revenue", [r"revenue from operations"]),
         ("receivables", [r"trade receivables"])], 3)
    assert rows == {"revenue": [400, 300, 200], "receivables": [80, 30, 20]}
    days = [round(r / v * 365, 1) for r, v in zip(rows["receivables"], rows["revenue"])]
    assert days == [73, 36.5, 36.5]
    assert _metric([{"fy": "FY2025", "receivable_days": days[1]},
                    {"fy": "FY2026", "receivable_days": days[0]}]).value == pytest.approx(100)
