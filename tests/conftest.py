"""Shared fixtures and synthetic-input builders for the v1.5 test suite.

The synthetic fixtures are expressed as deltas from the Vishal Nirmiti golden
input so that each test isolates one v1.5 behaviour. Every synthetic input is
still a complete, schema-valid document - the point is to vary one thing at a
time, not to bypass the gates.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = REPO_ROOT / "engine"
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from ipo_screening.evaluation import EvaluationStore  # noqa: E402
from ipo_screening.pipeline import evaluate, load_config  # noqa: E402

FIXTURES = REPO_ROOT / "fixtures"
GOLDEN_INPUT = FIXTURES / "vishal_nirmiti" / "input.json"
CONFIG_PATH = REPO_ROOT / "config" / "ipo-config.v1.5.0.json"
SCHEMA_PATH = REPO_ROOT / "schema" / "ipo-input.v1.5.schema.json"

#: Fixed evaluation instant used by every test so results are deterministic.
GOLDEN_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "vishal_nirmiti"

EVAL_AT = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="session")
def config() -> Dict[str, Any]:
    return load_config(CONFIG_PATH)


@pytest.fixture(scope="session")
def raw_config() -> Dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def schema() -> Dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def golden_input() -> Dict[str, Any]:
    with GOLDEN_INPUT.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def make_input(golden_input: Mapping[str, Any]) -> Callable[..., Dict[str, Any]]:
    """Return a factory producing a modified copy of the golden input."""

    def factory(**overrides: Any) -> Dict[str, Any]:
        """Apply dotted-path overrides, e.g. ``**{"issue.ofs": 0}``."""
        document = copy.deepcopy(golden_input)
        for path, value in overrides.items():
            _set(document, path, value)
        return document

    return factory


_INDEX_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def _tokenise(path: str):
    """Split ``financials.periods[2].pat`` into keys and integer indices."""
    tokens = []
    for match in _INDEX_RE.finditer(path):
        if match.group(1) is not None:
            tokens.append(match.group(1))
        else:
            tokens.append(int(match.group(2)))
    return tokens


def _set(document: Dict[str, Any], path: str, value: Any) -> None:
    tokens = _tokenise(path)
    if not tokens:
        raise ValueError(f"empty override path {path!r}")
    cursor: Any = document
    for token in tokens[:-1]:
        cursor = cursor[token]
    cursor[tokens[-1]] = value


def run(
    document: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    mode: str = "final",
    at: Optional[datetime] = None,
    store: Optional[EvaluationStore] = None,
    workbook_path: Optional[str] = None,
):
    """Evaluate a document with the fixed test instant."""
    return evaluate(
        document,
        config,
        mode=mode,
        evaluation_datetime=at or EVAL_AT,
        store=store,
        workbook_path=workbook_path,
    )


def criterion(outcome, criterion_id: str):
    for module in outcome.score.modules:
        for item in module.criteria:
            if item.criterion_id == criterion_id:
                return item
    raise AssertionError(f"criterion {criterion_id!r} not found in the result")


def knockout(outcome, rule_id: str):
    for result in outcome.knockouts.results:
        if result.rule_id == rule_id:
            return result
    raise AssertionError(f"knockout {rule_id!r} not found in the result")


def metric(outcome, metric_id: str):
    return outcome.derived.metrics[metric_id]


def minimal_input() -> Dict[str, Any]:
    """A small, schema-valid input with the least possible disclosure.

    Used by the UNKNOWN-semantics tests: almost everything material is null,
    so the engine has to report UNKNOWN rather than zero.
    """
    return {
        "ipo_id": "SYNTHETIC-MINIMAL",
        "company_name": "Synthetic Minimal Limited",
        "board": "mainboard",
        "icdr_route": "6(1)",
        "sector_profile": "standard",
        "issue": {
            "price_band_low": 100,
            "price_band_high": 110,
            "fresh_issue": 10000,
            "ofs": 0,
            "open_date": "2026-09-30",
            "close_date": "2026-10-05",
        },
        "financials": {
            "reporting_unit": "INR_LAKHS",
            "periods": [
                {"fy": "FY2024", "revenue": 20000, "pat": 500},
                {"fy": "FY2025", "revenue": 22000, "pat": 600},
                {"fy": "FY2026", "revenue": 24000, "pat": 700},
            ],
        },
        "capital_structure": {"promoter_pre_pct": 70, "promoter_post_pct": 55},
        "use_of_proceeds": [],
        "governance": {},
        "business": {},
        "peers": [{"name": "Some Peer Limited", "pe": 20, "as_of": "2026-07-01"}],
    }


__all__ = [
    "REPO_ROOT",
    "ENGINE_ROOT",
    "FIXTURES",
    "GOLDEN_INPUT",
    "CONFIG_PATH",
    "SCHEMA_PATH",
    "EVAL_AT",
    "run",
    "criterion",
    "knockout",
    "metric",
    "minimal_input",
]

def prepare(document: Mapping[str, Any], config: Mapping[str, Any], moment=None):
    """Canonicalise a document and build the snapshots the engine would.

    Mirrors ``pipeline.evaluate`` steps 2-4 so tests can exercise the derived
    layer and the overlay resolver in isolation without re-implementing the
    sequence. Validation gates are deliberately *not* enforced here: callers
    that want them should go through :func:`run`.
    """
    from ipo_screening.canonical_input import build_canonical_input
    from ipo_screening.snapshots import build_market_snapshot, classify_peers

    moment = moment or EVAL_AT
    canonical = build_canonical_input(document)
    thresholds = config.get("thresholds", {})
    peers = classify_peers(
        canonical.peers(),
        evaluation_datetime=moment,
        staleness_days=int(thresholds.get("peer_staleness_days", 90)),
        min_listed_years=float(thresholds.get("peer_min_listed_years", 3)),
    )
    market = build_market_snapshot(
        canonical.market(),
        evaluation_datetime=moment,
        staleness_hours=int(thresholds.get("market_staleness_hours", 24)),
    )
    return canonical, peers, market


def derive_for(document: Mapping[str, Any], config: Mapping[str, Any], moment=None):
    """Return the :class:`DerivedMetrics` for a document, as the engine would."""
    from ipo_screening.derived import derive

    moment = moment or EVAL_AT
    canonical, peers, market = prepare(document, config, moment)
    return derive(canonical, config, peers, market, evaluation_datetime=moment)


def plan_for(document: Mapping[str, Any], config: Mapping[str, Any], moment=None):
    """Return the :class:`EffectiveScoringPlan` for a document."""
    canonical, _, _ = prepare(document, config, moment)
    return resolve_overlay_plan(config, derive_for(document, config, moment), canonical)


def resolve_overlay_plan(config, derived, canonical):
    from ipo_screening.overlays import resolve_overlays

    return resolve_overlays(config, derived, canonical.sector_profile)
