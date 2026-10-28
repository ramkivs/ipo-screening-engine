"""Per-seller share counts are an all-or-nothing contract (2026-10-28).

**Why this file exists.** The derived layer forms two scoring inputs as
ratios over the offer-for-sale seller list::

    promoter_ofs_pct_of_holding   = sold / pre  x 100      (scoring band, 2 pts)
    pe_promoter_sold_pct_combined = sold / pre  x 100      (knockout K4, > 50)

Both summations are written defensively as ``sum(x.get(...) or 0.0 for x in
sellers)``. Read literally that looks like an absent per-seller number would be
silently treated as **zero**, which would understate a denominator (and so
*overstate* the percentage) or understate a numerator -- and could clear or
trigger a knockout on a number the filing never disclosed.

It cannot, and this file proves why: ``schema/ipo-input.v1.5.schema.json``
``$defs.seller`` lists ``pre_issue_shares`` and ``shares_sold`` as **required**,
typed ``number`` with ``minimum: 0``. A row can therefore never reach the
derivation with either value absent, ``null``, or a numeric string, so the
``or 0.0`` fallbacks are unreachable defence-in-depth rather than a defaulting
path. The structural gate -- not the arithmetic -- is what keeps "absent" from
becoming "zero here".

That property is load-bearing for the K1-K6 contract ("a missing input must not
become a favourable or an adverse finding"), so it is pinned here rather than
left as an observation. If a future schema revision relaxes either field to
optional or nullable, these tests fail and the derivation must return UNKNOWN
instead of summing a partial list.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone

import pytest

from conftest import CONFIG_PATH, GOLDEN_INPUT, SCHEMA_PATH
from ipo_screening.errors import SchemaValidationError
from ipo_screening.pipeline import evaluate, load_config
from ipo_screening.schema_validation import enforce_schema

EVAL_AT = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

COMPLETE_SELLERS = [
    {
        "name": "A Limited",
        "type": "promoter_group",
        "pre_issue_shares": 1500000,
        "shares_sold": 1500000,
    }
]


@pytest.fixture(scope="module")
def schema():
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_PATH)


@pytest.fixture(scope="module")
def golden():
    with GOLDEN_INPUT.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _document(golden, sellers):
    document = copy.deepcopy(golden)
    document["issue"]["ofs_sellers"] = sellers
    return document


def _violations(schema, document):
    with pytest.raises(SchemaValidationError) as excinfo:
        enforce_schema(document, schema)
    return " ".join(str(f) for f in excinfo.value.findings)


def test_complete_seller_rows_pass_the_gate(schema, golden):
    """Positive control: the reference shape is accepted untouched."""
    enforce_schema(_document(golden, COMPLETE_SELLERS), schema)


def test_a_row_without_pre_issue_shares_is_rejected_not_zeroed(schema, golden):
    """The denominator cannot silently lose a seller.

    Without this rejection the ratio would be ``sold / A`` instead of
    ``sold / (A + B)`` -- the percentage would be *overstated* on a count the
    filing never printed, and K4's ``> 50`` test could fire on it.
    """
    sellers = [
        COMPLETE_SELLERS[0],
        {"name": "B Limited", "type": "promoter_group", "shares_sold": 500000},
    ]
    findings = _violations(schema, _document(golden, sellers))
    assert "pre_issue_shares" in findings
    assert "required" in findings


def test_a_row_without_shares_sold_is_rejected_not_zeroed(schema, golden):
    """The numerator cannot silently lose a seller either."""
    sellers = [
        COMPLETE_SELLERS[0],
        {"name": "B Limited", "type": "promoter_group", "pre_issue_shares": 500000},
    ]
    findings = _violations(schema, _document(golden, sellers))
    assert "shares_sold" in findings
    assert "required" in findings


@pytest.mark.parametrize("field", ["pre_issue_shares", "shares_sold"])
def test_null_seller_numbers_are_rejected(schema, golden, field):
    """An explicit ``null`` is still "not a number", not a zero."""
    seller = dict(COMPLETE_SELLERS[0])
    seller[field] = None
    findings = _violations(schema, _document(golden, [seller]))
    assert field in findings


@pytest.mark.parametrize("field", ["pre_issue_shares", "shares_sold"])
def test_numeric_strings_are_rejected(schema, golden, field):
    """``"1500000"`` is a string; the schema requires a JSON number."""
    seller = dict(COMPLETE_SELLERS[0])
    seller[field] = "1500000"
    findings = _violations(schema, _document(golden, [seller]))
    assert field in findings


def test_complete_rows_form_the_ratio_exactly(config, golden):
    """With every row complete the ratio is exact -- no rounding, no fallback.

    ``1,500,000 / 1,500,000`` is 100 %, which K4's first leaf reports.
    """
    outcome = evaluate(
        _document(golden, COMPLETE_SELLERS),
        config,
        mode="final",
        evaluation_datetime=EVAL_AT,
    )
    k4 = next(r for r in outcome.record.knockouts["results"] if r["rule_id"] == "K4")
    leaf = next(
        item for item in k4["leaves"]
        if item.get("reference") == "pe_promoter_sold_pct_combined"
    )
    assert leaf["value"] == pytest.approx(100.0)
    assert leaf["truth"] == "TRUE"
