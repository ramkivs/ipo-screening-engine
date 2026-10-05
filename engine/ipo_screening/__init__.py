"""IPO Screening & Qualification Engine v1.5.

A deterministic, auditable screening engine for Indian mainboard IPOs.

The layered architecture (spec v1.5 s6.1, technical design s2):

    Sources -> Extraction -> Canonical Input + Evidence -> Validation
      -> Derived Metrics -> Overlay Resolver -> Knockout Engine
      -> Deterministic Scorer -> Confidence / Range / Verdict
      -> Immutable Evaluation Record -> Excel Projection

Guiding rules enforced throughout:

  * UNKNOWN is not zero (spec s3.2);
  * knockouts are tri-state and a missing input never yields CLEAR (s3.3);
  * evidence and provenance exist before scoring (s3.4);
  * configuration is executable policy and an invalid configuration blocks
    scoring (s3.5);
  * Excel is a projection of the immutable evaluation record, not the
    authoritative store (s3.6).

Quick start::

    from ipo_screening import evaluate_file, EvaluationStore

    outcome = evaluate_file("fixtures/vishal_nirmiti/input.json")
    print(outcome.score.final_score, outcome.score.verdict)
"""

from __future__ import annotations

from .canonical import Evidence, SourceRef, State, Value, Verification
from .canonical_input import CanonicalInput, build_canonical_input
from .config_validation import check_config, compile_config, config_fingerprint
from .derived import DerivedMetrics, MetricValue, derive
from .errors import (
    ConfigValidationError,
    Finding,
    ImmutabilityError,
    SchemaValidationError,
    SemanticValidationError,
    ValidationError,
)
from .evaluation import EvaluationRecord, EvaluationStore, compute_result_hash
from .knockouts import KnockoutResult, KnockoutSummary, evaluate_knockouts
from .overlays import EffectiveScoringPlan, resolve_overlays
from .pipeline import EvaluationOutcome, evaluate, evaluate_file, load_config, replay
from .scoring import CriterionResult, ModuleResult, ScoreResult, score
from .snapshots import classify_peers, build_market_snapshot
from .version import ENGINE_VERSION, SPEC_VERSION

__all__ = [
    "ENGINE_VERSION",
    "SPEC_VERSION",
    "State",
    "Verification",
    "Value",
    "SourceRef",
    "Evidence",
    "CanonicalInput",
    "build_canonical_input",
    "DerivedMetrics",
    "MetricValue",
    "derive",
    "EffectiveScoringPlan",
    "resolve_overlays",
    "KnockoutResult",
    "KnockoutSummary",
    "evaluate_knockouts",
    "CriterionResult",
    "ModuleResult",
    "ScoreResult",
    "score",
    "EvaluationRecord",
    "EvaluationStore",
    "compute_result_hash",
    "EvaluationOutcome",
    "evaluate",
    "evaluate_file",
    "replay",
    "load_config",
    "compile_config",
    "check_config",
    "config_fingerprint",
    "classify_peers",
    "build_market_snapshot",
    "Finding",
    "ValidationError",
    "SchemaValidationError",
    "SemanticValidationError",
    "ConfigValidationError",
    "ImmutabilityError",
]

__version__ = ENGINE_VERSION
