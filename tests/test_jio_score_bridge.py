"""The Jio 29 -> 21 bridge: an issue-structure inversion, not extraction.

The 2026-10-19 Windows Jio scorecard reported 21/100 with the *corrected*
financials (revenue CAGR +15.79%, ROCE 10.76, CFO/PAT 2.62) and the same
available/unknown points (46/54) as Arena's 29/100 reproduction.  This test
pins the complete numerical bridge:

* the filing-established fresh-only structure (OFS 0, fresh > 0) => 29;
* the inverted structure (fresh 0, OFS > 0) => 21;
* the only difference is Module C: fresh_share 3->0, ofs_seller_type 2->0,
  promoter_ofs_pct 2->0, dilution 1->0; use_of_proceeds moves from UNKNOWN
  to a scored zero, keeping available/unknown exactly invariant.

Both runs use the real committed RHP and the same five manual terms, so
the financial extraction and every other module are identical.  No
scoring rule is changed by the test.
"""

from __future__ import annotations

import copy

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.service import PresentationConfig, PresentationService

JIO_PDF = REPO_ROOT / "evidence" / "non-authoritative" / "jio" / "U72900GJ2019PLC110816_JIO.pdf"
EXPLANATION = "Reproduction of the 2026-10-19 Windows evaluation issue structure."


def _service(tmp_path):
    return PresentationService(
        PresentationConfig(
            store_root=tmp_path / "evaluations",
            config_dir=REPO_ROOT / "config",
            issue_terms_resolver=IssueTermsResolver(providers=[]),
        )
    )


def _ingest(service, fresh, ofs):
    return service.ingest_document(
        file_bytes=JIO_PDF.read_bytes(),
        filename=JIO_PDF.name,
        mode="final",
        manual_terms={
            "price_band_low": 1065.0,
            "price_band_high": 1119.0,
            "lot_size": 12,
            "ofs": float(ofs),
            "fresh_issue": float(fresh),
        },
        manual_explanation=EXPLANATION,
        confirm_conflicts=True,
    )


def _module(record, module_id):
    return next(m for m in record["score"]["modules"] if m["module_id"] == module_id)


def _criterion(module, criterion_id):
    return next(c for c in module["criteria"] if c["criterion_id"] == criterion_id)


@pytest.mark.slow
def test_jio_correct_structure_is_29_and_inverted_is_21(tmp_path, monkeypatch):
    # One real extraction, reused for both evaluations (the issue terms are
    # the only difference and are applied after extraction).
    doc, _report = DocumentExtractor().extract_from_pdf(
        pdf_path=JIO_PDF, allow_fixture_fallbacks=False
    )
    monkeypatch.setattr(
        DocumentExtractor,
        "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (
            copy.deepcopy(doc),
            {},
        ),
    )
    service = _service(tmp_path)

    correct = service.eval_store.read(
        _ingest(service, fresh=3021300, ofs=0).evaluation_id
    )
    inverted = service.eval_store.read(
        _ingest(service, fresh=0, ofs=3021300).evaluation_id
    )

    # -- headline numbers ---------------------------------------------------
    assert correct["score"]["final_score"] == 29.0
    assert inverted["score"]["final_score"] == 21.0
    for record in (correct, inverted):
        assert record["score_range"]["available_points"] == 46.0
        assert record["score_range"]["unknown_points"] == 54.0
        assert record["confidence"]["level"] == "Low"
        assert record["verdict"]["verdict"] == "INSUFFICIENT_DATA"
        assert record["score"]["penalties_total"] == 0.0

    # -- the only difference is Module C ------------------------------------
    assert _module(correct, "A")["score"] == 13.0
    assert _module(inverted, "A")["score"] == 13.0
    assert _module(correct, "B")["score"] == 0.0
    assert _module(inverted, "B")["score"] == 0.0
    assert _module(correct, "C")["score"] == 11.0
    assert _module(inverted, "C")["score"] == 3.0
    assert _module(correct, "D")["score"] == 5.0
    assert _module(inverted, "D")["score"] == 5.0

    # -- the four-criterion, eight-point delta ------------------------------
    c_correct, c_inverted = _module(correct, "C"), _module(inverted, "C")
    assert _criterion(c_correct, "fresh_share")["score"] == 3.0
    assert _criterion(c_inverted, "fresh_share")["score"] == 0.0
    assert _criterion(c_correct, "ofs_seller_type")["score"] == 2.0
    assert _criterion(c_inverted, "ofs_seller_type")["state"] == "UNKNOWN"
    assert _criterion(c_correct, "promoter_ofs_pct")["score"] == 2.0
    assert _criterion(c_inverted, "promoter_ofs_pct")["state"] == "UNKNOWN"
    assert _criterion(c_correct, "dilution")["score"] == 1.0
    assert _criterion(c_inverted, "dilution")["score"] == 0.0
    assert _criterion(c_inverted, "dilution")["zeroed_by"] == "pure_ofs"
    assert _criterion(c_correct, "use_of_proceeds")["state"] == "UNKNOWN"
    assert _criterion(c_inverted, "use_of_proceeds")["score"] == 0.0
    assert _criterion(c_inverted, "use_of_proceeds")["zeroed_by"] == "pure_ofs"

    # -- the structure and the cap ------------------------------------------
    assert correct["input_snapshot"]["input"]["issue"]["fresh_issue"] == 3021300.0
    assert correct["input_snapshot"]["input"]["issue"]["ofs"] == 0.0
    assert inverted["input_snapshot"]["input"]["issue"]["fresh_issue"] == 0.0
    assert inverted["input_snapshot"]["input"]["issue"]["ofs"] == 3021300.0
    assert inverted["score"]["caps_applied"] == [{"id": "pure_ofs", "max_score": 60}]
    assert correct["score"]["caps_applied"] == []
