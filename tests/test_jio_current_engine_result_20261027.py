"""The published Jio 34.0 record is stale relative to the engine in ``main``.

``docs/investigation/JIO-CORRECTION-INTEGRATION-2026-10-23.md`` §7 asserts that
the published result ``JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601``
(34.0, 24-77, ``INSUFFICIENT_DATA``) *is* the current engine's result, because
the integrated tree's 66 engine files were byte-identical to the tree that
produced it.

That claim is false for ``main``.  The retained record's own ``runtime.json``
fingerprints 66 engine files, and **20 of them differ** from ``main`` (pinned
below).  The integrated tree is not reachable from any ref in this repository,
so the 34.0 result cannot be reproduced from ``main``.

Re-running the current engine on the same committed RHP (same five manual
terms, no official discovery provider) returns a *different* answer:

===========================  =============================  ============================
                            published 2026-10-23          current engine (this test)
===========================  =============================  ============================
``final_score``              34.0                          37.0
``verdict``                  INSUFFICIENT_DATA            AVOID
``lower`` / ``upper``        24 - 77                        25 - 74
``completeness_pct``         57.0                          63.0
K2                            UNVERIFIED                    TRIGGERED
Module C / D                  11 / 5                        10 / 9
===========================  =============================  ============================

The verdict change is not a scoring change.  A29 (K2-A) was ratified on the
prior line and is present in ``main``; applied to this filing it reads
``governance.sebi_ed_action_active = true`` (p. 468, "SEBI filed a revision
application before the Hon'ble High Court of Bombay and the same is currently
pending"), which makes K2 ``TRIGGERED`` and therefore ``AVOID`` under the
existing ``config.verdict.knockout_verdict``.  The published record predates
that correction.  This test pins both the divergence and the corrected result
so the stale figure cannot be asserted again.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.service import PresentationConfig, PresentationService

JIO_PDF = REPO_ROOT / "evidence" / "non-authoritative" / "jio" / "U72900GJ2019PLC110816_JIO.pdf"

RETAINED_RUNTIME = (
    REPO_ROOT
    / "docs"
    / "investigation"
    / "jio-fresh-20261023"
    / "final-retained"
    / "runtime.json"
)

PUBLISHED_EVALUATION_ID = "JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601"

# The engine files that differ between the published record's tree and ``main``.
# Pinned explicitly: a divergence list that drifts silently would let the
# "the published result IS this engine's result" claim survive.
DIVERGENT_ENGINE_FILES = frozenset(
    {
        "engine/ipo_screening/aggregator_issue_terms.py",
        "engine/ipo_screening/canonical_input.py",
        "engine/ipo_screening/derived.py",
        # 2026-10-28 (tracker Revision 33, G-3): the fail-closed fixture
        # safeguard became provenance-based and its coverage complete. The
        # change is confined to an enrichment-contract validator that no
        # production path invokes, so it does not move the Jio result; the file
        # diverges from the 2026-10-23 fingerprint all the same, and this pin is
        # the record of exactly which files diverge.
        "engine/ipo_screening/enrichment_contract.py",
        "engine/ipo_screening/excel.py",
        "engine/ipo_screening/extraction/builder.py",
        "engine/ipo_screening/extraction/extractor.py",
        "engine/ipo_screening/extraction/financial_tables.py",
        "engine/ipo_screening/extraction/numbers.py",
        "engine/ipo_screening/extraction/official_notice_ocr.py",
        "engine/ipo_screening/extraction/official_offer_amounts.py",
        "engine/ipo_screening/extraction/price_band_notice.py",
        "engine/ipo_screening/extraction/prospectus_terms.py",
        "engine/ipo_screening/extraction/sections.py",
        "engine/ipo_screening/extraction/toc.py",
        "engine/ipo_screening/issue_term_fields.py",
        "engine/ipo_screening/issue_terms.py",
        "engine/ipo_screening/official_issue_sources.py",
        "engine/ipo_screening/post_listing/v16_implementation.py",
        # Revision 50 embeds the isolated Layer 2C/Layer 3 workbench in the
        # presentation host; these UI read-path changes cannot affect Jio scoring.
        "engine/ipo_screening/presentation/api.py",
        "engine/ipo_screening/presentation/service.py",
        "engine/ipo_screening/semantic_validation.py",
        "engine/tools/ipo_screen.py",
    }
)

# The five manual terms the 2026-10-23 run also used (issue terms were taken
# from the PA-authorized third-party aggregator, which this sandbox cannot
# re-fetch; the manual terms are the same public figures).
MANUAL_TERMS = {
    "price_band_low": 1065.0,
    "price_band_high": 1119.0,
    "lot_size": 12,
    "ofs": 0.0,
    "fresh_issue": 302130.0,
}


def _service(tmp_path) -> PresentationService:
    return PresentationService(
        PresentationConfig(
            store_root=tmp_path / "evaluations",
            config_dir=REPO_ROOT / "config",
            issue_terms_resolver=IssueTermsResolver(providers=[]),
        )
    )


def test_published_record_engine_diverges_from_main():
    """The 34.0 record cannot be reproduced from ``main``; the divergence is pinned."""
    assert RETAINED_RUNTIME.is_file(), RETAINED_RUNTIME
    fingerprints = json.loads(RETAINED_RUNTIME.read_text())["source_fingerprints"]
    assert len(fingerprints) == 66

    divergent = set()
    for relative, expected in fingerprints.items():
        path = REPO_ROOT / relative
        if not path.is_file():
            divergent.add(relative)
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            divergent.add(relative)

    assert divergent == DIVERGENT_ENGINE_FILES
    assert len(divergent) == 23


def test_published_record_still_says_insufficient_data():
    """The retained record is the historical one and is not rewritten by this test."""
    record = (
        REPO_ROOT
        / "docs"
        / "investigation"
        / "jio-fresh-20261023"
        / "final-retained"
        / "evaluations"
        / PUBLISHED_EVALUATION_ID
    )
    result = json.loads((record / "result.json").read_text())
    assert result["evaluation_id"] == PUBLISHED_EVALUATION_ID
    assert result["score"]["final_score"] == 34.0
    assert result["verdict"]["verdict"] == "INSUFFICIENT_DATA"


@pytest.mark.slow
def test_current_engine_returns_avoid_with_k2_triggered(tmp_path):
    """The current engine's answer for the same filing is a K2 knockout, not a band."""
    service = _service(tmp_path)
    response = service.ingest_document(
        file_bytes=JIO_PDF.read_bytes(),
        filename=JIO_PDF.name,
        mode="final",
        manual_terms=MANUAL_TERMS,
        manual_explanation="Pin the current engine's Jio result (2026-10-27).",
        confirm_conflicts=True,
    )
    payload = response.model_dump() if hasattr(response, "model_dump") else vars(response)

    assert payload["final_score"] == 37.0
    assert payload["verdict"] == "AVOID"

    evaluation = payload["evaluation"]
    assert evaluation["knockouts"]["status"] == "TRIGGERED"
    knockouts = {
        rule["id"]: rule["state"] for rule in evaluation["knockouts"]["rules"]
    }
    assert knockouts["K2"] == "TRIGGERED"
    # The pledge limb stays UNKNOWN: the filing does not state a pledge and the
    # builder no longer supplies a favourable 0.0 default for real ingestion.
    canonical = json.loads(
        next((tmp_path / "evaluations").glob("*/input.json")).read_text()
    )
    assert canonical["snapshot"]["input"]["capital_structure"]["promoter_pledge_pct"] is None
