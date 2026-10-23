"""Non-scoring audit checks of the unchanged governance contract.

No future CARO/K2 policy is encoded here; no evaluations or golden files are written.
"""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ipo_screening.canonical_input import build_canonical_input
from ipo_screening.config_validation import config_fingerprint
from ipo_screening.derived import DerivedMetrics, _eom_materiality
from ipo_screening.scoring import _evaluate_penalties

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "eom_count_3y": 2,
    "auditor_change_count_3y": 1,
    "caro_remarks": True,
    "regulatory_actions": [{"authority": "SEBI", "status": "review_required"}],
    "independent_director_count": 3,
}


@pytest.mark.parametrize("name,value", FIELDS.items())
def test_declared_governance_values_retained_in_direct_canonical_input(name, value):
    schema = json.loads((ROOT / "schema/ipo-input.v1.5.schema.json").read_text())
    assert name in schema["properties"]["governance"]["properties"]
    raw = json.loads((ROOT / "fixtures/vishal_nirmiti/input.json").read_text())
    raw["governance"][name] = value
    before = copy.deepcopy(raw)
    canonical = build_canonical_input(raw)
    assert canonical.governance()[name] == value
    assert raw == before


@pytest.mark.parametrize("value,points,reserve,state", [
    ("none", 0, 0, "SCORED"),
    (None, 0, 3, "UNKNOWN"),
    ("low", -1, 0, "SCORED"),
    ("medium", -2, 0, "SCORED"),
    ("high", -3, 0, "SCORED"),
])
def test_current_materiality_contract(value, points, reserve, state):
    raw = json.loads((ROOT / "fixtures/vishal_nirmiti/input.json").read_text())
    raw["governance"]["eom_materiality"] = value
    ctx = SimpleNamespace(canonical=build_canonical_input(raw))
    metric = _eom_materiality(ctx)
    config = json.loads((ROOT / "config/ipo-config.v1.5.0.json").read_text())
    penalty = next(p for p in config["penalties"]["items"] if p["id"] == "eom_caro")
    _, items, unresolved = _evaluate_penalties(
        {"penalties": {"items": [penalty]}}, DerivedMetrics({"eom_materiality": metric})
    )
    assert items[0]["points"] == points
    assert items[0]["state"] == state
    assert unresolved == reserve
    if value is None:
        del raw["governance"]["eom_materiality"]
        assert _eom_materiality(SimpleNamespace(canonical=build_canonical_input(raw))).is_unknown


def test_formula_wording_is_hash_material_without_mutating_config():
    config = json.loads((ROOT / "config/ipo-config.v1.5.0.json").read_text())
    before = copy.deepcopy(config)
    candidate = copy.deepcopy(config)
    candidate["derived_metrics"]["auditor_bucket"]["formula"] += " [audit-only example]"
    assert config_fingerprint(candidate) != config_fingerprint(config)
    assert config == before


@pytest.mark.parametrize("name,value", FIELDS.items())
def test_extraction_governance_allowlist_does_not_carry_declared_fields(name, value):
    from ipo_screening.extraction.builder import CanonicalInputBuilder

    # Exercise only the governance projection, which does not inspect SourceDocument.
    builder = CanonicalInputBuilder(
        doc=None, extractions=[], reference_base={"governance": {name: value}}
    )
    assert name not in builder._build_governance()


def test_supplied_caro_currently_does_not_change_clean_auditor_branch():
    from ipo_screening.derived import _auditor_bucket

    raw = json.loads((ROOT / "fixtures/vishal_nirmiti/input.json").read_text())
    raw["governance"].update(
        auditor_opinion="unqualified", auditor_reputed=True,
        auditor_changed_3y=False, repeated_eom=False,
    )
    before = _auditor_bucket(SimpleNamespace(canonical=build_canonical_input(raw)))
    raw["governance"]["caro_remarks"] = True
    after = _auditor_bucket(SimpleNamespace(canonical=build_canonical_input(raw)))
    assert before == after
    assert after.value == "clean_reputed"
    assert "governance.caro_remarks" not in after.inputs
