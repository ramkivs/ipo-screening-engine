"""Vishal Nirmiti 7 October evaluation — historical reconciliation tests.

Established by investigation (2026-10-16):

* The historical scorecard (2026-10-07T03:48:18Z, final 38.0,
  INSUFFICIENT_DATA, result hash 0a89c0c3...) was produced by the UI-7
  upload path as it existed before commit df17d0a: extraction of the real
  RHP (SHA-256 644be76e..., 551 pages) with ``allow_fixture_fallbacks=True``.
  The four now-disputed issue fields were NOT extracted (the RHP prints
  [●] for them and the run's _evidence has no entries for them); they were
  populated from CanonicalInputBuilder's hardcoded fixture defaults.
* Extraction stamps a wall-clock retrieval_timestamp into the source
  record, which feeds the result hashes, so extracted-input evaluations
  are score-stable but not hash-reproducible run-to-run. The historical
  hash therefore cannot be regenerated and no durable copy exists in the
  repository; the golden record (e84f8bc0...) is a different, curated
  input and remains untouched.
* The legitimate way to supply the missing terms is the Price Band
  Notice enrichment path. The notice source record previously carried a
  non-schema ``note`` key that made assembled inputs fail the closed
  _sources schema; that defect is fixed and covered here.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import CONFIG_PATH, EVAL_AT, REPO_ROOT
from ipo_screening.enrichment_engine import EnrichmentEngine
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import SourceDocument
from ipo_screening.extraction.price_band_notice import PriceBandNoticeParser
from ipo_screening.pipeline import evaluate, load_config
from ipo_screening.schema_validation import validate_schema

GOLDEN_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
HISTORICAL_HASH = "0a89c0c3b44a37b69aef98612f0fbb72d6792ca1bb0c2bba2da439eae968b400"
ISSUE_FIELDS = ("price_band_low", "price_band_high", "lot_size", "ofs")


def _builder(allow_fixture_fallbacks: bool) -> dict:
    doc = SourceDocument(source_id="RHP-TEST", uri="test.pdf", content_hash="abc")
    return CanonicalInputBuilder(
        doc, [], allow_fixture_fallbacks=allow_fixture_fallbacks
    ).build()


def test_builder_without_fallbacks_keeps_undisclosed_terms_unknown():
    """The real PDF path must not acquire unsupported fixture values."""
    issue = _builder(allow_fixture_fallbacks=False)["issue"]
    for field in ISSUE_FIELDS:
        assert issue[field] is None, f"{field} must stay unknown (null), never a default or zero"


def test_builder_fixture_defaults_are_the_historical_mechanism():
    """Document the pre-df17d0a behaviour that produced the 7 Oct input:
    hardcoded Vishal fixture defaults, applied only when fallbacks were on."""
    issue = _builder(allow_fixture_fallbacks=True)["issue"]
    assert issue["price_band_low"] == 208
    assert issue["price_band_high"] == 220
    assert issue["lot_size"] == 68
    assert issue["ofs"] == 3300


def test_price_band_notice_enrichment_supplies_terms_legitimately(golden_input):
    """A Price Band Notice (the established source of truth for these
    terms) assembles a schema-valid, evaluable input with provenance."""
    base = copy.deepcopy(golden_input)
    for field in ISSUE_FIELDS:
        base["issue"][field] = None
        base.get("_evidence", {}).pop(f"issue.{field}", None)

    notice = PriceBandNoticeParser().parse_from_text(
        (REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt").read_text(encoding="utf-8")
    )
    result = EnrichmentEngine.assemble(base_input=base, price_band_notice=notice, mode="final")
    canonical = result.canonical_input

    # Notice-sourced terms, each carrying evidence provenance.
    assert canonical["issue"]["price_band_low"] == 208
    assert canonical["issue"]["price_band_high"] == 220
    assert canonical["issue"]["lot_size"] == 68
    for field in ("price_band_low", "price_band_high", "lot_size"):
        evidence = canonical["_evidence"][f"issue.{field}"]
        assert evidence["source_id"].startswith("SRC-PBN-")
        assert evidence.get("quote")

    # The assembled input passes the same closed schema the pipeline enforces.
    assert validate_schema(canonical) == []

    # It evaluates, and is distinguishable from both the golden record and
    # the (hash-irreproducible) historical extracted evaluation.
    config = load_config(CONFIG_PATH)
    record = evaluate(
        canonical,
        config,
        mode="final",
        evaluation_datetime=datetime(2026, 10, 7, 3, 48, 18, tzinfo=timezone.utc),
    ).record
    assert record.verdict["verdict"] == "INSUFFICIENT_DATA"
    assert record.result_hash not in (GOLDEN_HASH, HISTORICAL_HASH)
    assert record.evaluation_id.endswith(record.result_hash[:8])


def test_golden_record_remains_the_curated_baseline(golden_input, config):
    """The historical reconciliation does not touch the golden record."""
    record = evaluate(golden_input, config, mode="final", evaluation_datetime=EVAL_AT).record
    assert record.result_hash == GOLDEN_HASH
    assert record.score["final_score"] == 35.0
    # ...while the same curated input at the historical timestamp is a
    # different (staleness-dependent) result, proving the 7 Oct scorecard
    # was not simply this fixture replayed through the UI store.
    historical_ts = evaluate(
        golden_input,
        config,
        mode="final",
        evaluation_datetime=datetime(2026, 10, 7, 3, 48, 18, tzinfo=timezone.utc),
    ).record
    assert historical_ts.result_hash != HISTORICAL_HASH
    assert historical_ts.score["final_score"] != 38.0
