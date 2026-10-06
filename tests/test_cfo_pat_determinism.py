"""Focused regression suite for CFO/PAT cross-platform determinism repair.

Verifies:
1. Deterministic calculation for the identified Vishal Nirmiti golden case.
2. Normative mathematical semantics: sum(CFO) / sum(PAT) cumulative ratio,
   NOT the arithmetic mean of annual CFO/PAT ratios.
3. Order-invariance and deterministic representation across period permutations.
4. Fail-closed and NA behavior on zero, negative, and missing denominators.
5. UNKNOWN propagation when any period observation is missing or periods are empty.
6. Bit-for-bit consistency with golden evaluation hash.
"""

from __future__ import annotations

import copy
import itertools
from decimal import Decimal
from typing import Any, Dict, List

import pytest

from conftest import criterion, metric, run


GOLDEN_EXPECTED_VALUE: float = 1.7881897553619628
GOLDEN_HEX_REPRESENTATION: str = "0x1.c9c6cdc652662p+0"
WINDOWS_DEFECT_VALUE: float = 1.7881897553619623
GOLDEN_RESULT_HASH: str = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"


# -----------------------------------------------------------------------------
# 1. Deterministic calculation on the golden fixture
# -----------------------------------------------------------------------------


def test_cfo_pat_deterministic_calculation_golden_case(golden_input, config):
    """Asserts deterministic calculation for the identified case and golden hash match."""
    outcome = run(golden_input, config)
    item = metric(outcome, "cfo_pat_cumulative")

    assert item.is_value
    assert item.value == GOLDEN_EXPECTED_VALUE
    assert item.value.hex() == GOLDEN_HEX_REPRESENTATION
    # Must not match the Windows defect value
    assert item.value != WINDOWS_DEFECT_VALUE
    # Golden result hash must remain permanently bit-for-bit identical
    assert outcome.record.result_hash == GOLDEN_RESULT_HASH


# -----------------------------------------------------------------------------
# 2. Semantic formula: sum(CFO) / sum(PAT), not average(CFO / PAT)
# -----------------------------------------------------------------------------


def test_cfo_pat_semantic_formula_cumulative_vs_average(golden_input, config):
    """Asserts the exact formula sum(CFO)/sum(PAT) and proves divergence from mean(CFO/PAT)."""
    outcome = run(golden_input, config)
    item = metric(outcome, "cfo_pat_cumulative")

    # Inputs: FY24 (2773.05, 344.56), FY25 (3820.17, 2363.59), FY26 (2715.47, 2497.5)
    total_cfo = 2773.05 + 3820.17 + 2715.47  # 9308.69
    total_pat = 344.56 + 2363.59 + 2497.5    # 5205.65
    cumulative_ratio = total_cfo / total_pat

    naive_average = (
        (2773.05 / 344.56) +
        (3820.17 / 2363.59) +
        (2715.47 / 2497.5)
    ) / 3.0

    assert item.value == pytest.approx(cumulative_ratio, rel=1e-9)
    # The two mathematical formulations diverge massively (> 1.7)
    assert abs(cumulative_ratio - naive_average) > 1.7
    assert abs(item.value - naive_average) > 1.7
    # Provenance metadata confirms the formula semantics
    assert "sum(CFO" in item.formula
    assert "sum(PAT" in item.formula
    assert "cumulative ratio" in item.formula
    assert "not the arithmetic mean" in item.formula
    assert item.inputs == ("financials.periods",)


# -----------------------------------------------------------------------------
# 3. Order invariance across period sequences
# -----------------------------------------------------------------------------


def test_cfo_pat_order_invariance_across_permutations(golden_input, config):
    """Asserts order-invariance across all period permutations when the period set is logically identical."""
    periods = golden_input["financials"]["periods"]
    assert len(periods) == 3

    distinct_values = set()
    distinct_hexes = set()

    for perm in itertools.permutations(periods):
        doc = copy.deepcopy(golden_input)
        doc["financials"]["periods"] = list(perm)
        outcome = run(doc, config)
        item = metric(outcome, "cfo_pat_cumulative")
        assert item.is_value
        distinct_values.add(item.value)
        distinct_hexes.add(item.value.hex())

    # Every permutation must evaluate to the exact identical numeric value and IEEE-754 bit pattern
    assert len(distinct_values) == 1
    assert len(distinct_hexes) == 1
    assert distinct_values.pop() == GOLDEN_EXPECTED_VALUE
    assert distinct_hexes.pop() == GOLDEN_HEX_REPRESENTATION


# -----------------------------------------------------------------------------
# 4. Denominator validation: zero, negative, and missing
# -----------------------------------------------------------------------------


def test_cfo_pat_zero_denominator_yields_not_applicable(make_input, config):
    """Asserts that cumulative PAT summing to exactly zero returns NOT_APPLICABLE (not forced to zero)."""
    doc = make_input(
        **{
            "financials.periods[0].pat": 100.0,
            "financials.periods[1].pat": -50.0,
            "financials.periods[2].pat": -50.0,
        }
    )
    outcome = run(doc, config)
    item = metric(outcome, "cfo_pat_cumulative")
    assert item.is_not_applicable
    assert item.value is None
    assert "cumulative PAT is non-positive" in item.reason
    assert "not forced to zero" in item.reason


def test_cfo_pat_negative_denominator_yields_not_applicable(make_input, config):
    """Asserts that cumulative PAT summing to negative returns NOT_APPLICABLE (not forced to zero)."""
    doc = make_input(
        **{
            "financials.periods[0].pat": -500.0,
            "financials.periods[1].pat": -100.0,
            "financials.periods[2].pat": -200.0,
        }
    )
    outcome = run(doc, config)
    item = metric(outcome, "cfo_pat_cumulative")
    assert item.is_not_applicable
    assert item.value is None
    assert "cumulative PAT is non-positive" in item.reason


def test_cfo_pat_single_negative_year_with_positive_cumulative_sum(make_input, config):
    """Asserts that a negative year with positive cumulative PAT evaluates successfully."""
    doc = make_input(
        **{
            "financials.periods[0].pat": -100.0,
            "financials.periods[1].pat": 600.0,
            "financials.periods[2].pat": 500.0,
        }
    )
    outcome = run(doc, config)
    item = metric(outcome, "cfo_pat_cumulative")
    assert item.is_value
    assert item.value is not None
    # CFO = 9308.69, PAT = 1000.0 -> ratio = 9.30869
    expected = (2773.05 + 3820.17 + 2715.47) / 1000.0
    assert item.value == pytest.approx(expected, rel=1e-9)


# -----------------------------------------------------------------------------
# 5. UNKNOWN propagation on missing observations
# -----------------------------------------------------------------------------


def test_cfo_pat_missing_cfo_propagates_unknown(make_input, config):
    """Asserts that missing CFO in any year produces UNKNOWN and value None."""
    doc = make_input(**{"financials.periods[1].cfo": None})
    outcome = run(doc, config)
    item = metric(outcome, "cfo_pat_cumulative")
    assert item.is_unknown
    assert item.value is None
    assert "CFO or PAT is not disclosed for every observation" in item.reason


def test_cfo_pat_missing_pat_propagates_unknown(make_input, config):
    """Asserts that missing PAT in any year produces UNKNOWN and value None."""
    doc = make_input(**{"financials.periods[0].pat": None})
    outcome = run(doc, config)
    item = metric(outcome, "cfo_pat_cumulative")
    assert item.is_unknown
    assert item.value is None
    assert "CFO or PAT is not disclosed for every observation" in item.reason


def test_cfo_pat_empty_periods_propagates_unknown(golden_input, config):
    """Asserts that missing all periods produces UNKNOWN and value None."""
    from conftest import derive_for

    doc = copy.deepcopy(golden_input)
    doc["financials"]["periods"] = []
    der = derive_for(doc, config)
    item = der.metrics["cfo_pat_cumulative"]
    assert item.is_unknown
    assert item.value is None
    assert "no full FY observation supplied" in item.reason
