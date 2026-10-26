"""Jio EPS 3.26 vs 32.63: provenance, precedence and unit consistency.

Report section 27.  The defect was not that the engine computed 32.63; it was
that the number was anonymous.  Three facts had to be separated:

* the filing's **FY2026 basic/diluted EPS is 33.63/33.59** (basis-for-issue-price
  table, p. 129), computed on the *weighted-average* count of 30.55/30.51 crore
  shares -- it is not an EPS on the post-issue capital;
* the committed RHP prints **no post-issue earnings figure at all** (the P/E and
  post-issue NAV rows are "[●]");
* the engine's **32.63** is its own derivation, 300,527 (INR millions) /
  9,209,030,830 post-issue shares.

So a stored 3.26 is neither a unit slip of 32.63 nor a mis-scaling of 33.63: it
is an unattributed value that contradicts the arithmetic by ~90%.  These tests
pin the shared behaviour that makes that visible and that stops a derived figure
from masquerading as a disclosed one.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import RawExtraction
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.schema_validation import validate_schema
from conftest import EVAL_AT

JIO_PAT_INR_MILLIONS = 300527
JIO_POST_ISSUE_SHARES = 9209030830


def _doc():
    return SimpleNamespace(
        source_id="RHP-JIO-TEST",
        company_name="Jio Platforms Limited",
        to_source_ref_dict=lambda: {"source_id": "RHP-JIO-TEST", "source_type": "RHP"},
    )


def _builder(extractions=(), reference_base=None):
    return CanonicalInputBuilder(
        doc=_doc(),
        extractions=list(extractions),
        reference_base=reference_base,
        allow_fixture_fallbacks=False,
    )


def _millions_periods(pat=JIO_PAT_INR_MILLIONS, fy="FY2026"):
    """A restated-FY period in the *filing's* unit (INR millions)."""
    return [{"fy": fy, "revenue": 1000.0, "pat": float(pat)}]


# ---------------------------------------------------------------------------
# 1-3. Derivation carries its own provenance and basis
# ---------------------------------------------------------------------------


def test_derived_eps_is_labelled_and_recomputable_from_the_filing_unit():
    out = _builder(
        reference_base={
            "financials": {"reporting_unit": "INR_MILLIONS", "periods": _millions_periods()},
            "issue": {"post_issue_shares": JIO_POST_ISSUE_SHARES},
        }
    ).build()

    assert out["issue"]["post_issue_eps"] == 32.63
    assert out["issue"]["post_issue_eps_basis"] == "derived"

    spec = out["_evidence"]["issue.post_issue_eps"]
    assert spec["extraction_method"] == "DERIVED"
    assert spec["locator"].startswith("Derived by the engine")
    # The note names the inputs and the unit factor, so the number can be
    # recomputed without guessing which scale was used.
    assert "INR_MILLIONS" in spec["note"]
    assert "1,000,000" in spec["note"]
    assert str(JIO_POST_ISSUE_SHARES) in spec["note"].replace(",", "")


def test_derived_eps_matches_the_crore_basis_the_validator_uses(golden_input):
    """One unit convention: builder (filing unit) == validator (crore x 1e7)."""
    from ipo_screening.semantic_validation import _CRORE_TO_RUPEES

    out = _builder(
        reference_base={
            "financials": {"reporting_unit": "INR_MILLIONS", "periods": _millions_periods()},
            "issue": {"post_issue_shares": JIO_POST_ISSUE_SHARES},
        }
    ).build()
    derived = out["issue"]["post_issue_eps"]

    # The canonical stores the same figure normalised to INR crore; the
    # validator's implication must return the same EPS.
    crore_pat = JIO_PAT_INR_MILLIONS * 1e6 / _CRORE_TO_RUPEES
    implied = crore_pat * _CRORE_TO_RUPEES / JIO_POST_ISSUE_SHARES
    assert implied == pytest.approx(derived, abs=0.01)


def test_a_disclosed_post_issue_figure_wins_over_the_derivation():
    out = _builder(
        extractions=[
            RawExtraction(
                field_path="issue.post_issue_eps",
                candidate_value=41.2,
                page=129,
                section="Basis for Issue Price",
                locator="Post-issue earnings per share",
                quote="Earnings per share (post-issue) 41.2",
            ),
            RawExtraction(field_path="issue.post_issue_shares", candidate_value=JIO_POST_ISSUE_SHARES),
        ],
        reference_base={
            "financials": {"reporting_unit": "INR_MILLIONS", "periods": _millions_periods()},
        },
    ).build()
    assert out["issue"]["post_issue_eps"] == 41.2
    assert out["issue"]["post_issue_eps_basis"] == "disclosed"
    # A disclosed value is evidenced by the filing's row, never by a note the
    # engine wrote about its own arithmetic.
    assert "Derived by the engine" not in str(out["_evidence"].get("issue.post_issue_eps"))


def test_a_curated_value_keeps_no_basis_and_is_not_relabelled():
    """Backward compatibility: fixtures that predate the field are untouched."""
    out = _builder(reference_base={"issue": {"post_issue_eps": 3.26}}).build()
    assert out["issue"]["post_issue_eps"] == 3.26
    assert "post_issue_eps_basis" not in out["issue"]
    assert "issue.post_issue_eps" not in (out.get("_evidence") or {})


def test_the_reader_never_reads_a_weighted_average_row_as_post_issue_eps():
    reader = SectionExtractor
    # Jio p. 129 prints exactly this and no post-issue figure.
    assert not reader._POST_ISSUE_EPS.search("Earnings per share (Basic) 33.63 33.59")
    assert not reader._POST_ISSUE_EPS.search("Earnings per share (Diluted) (in ) 33.59")
    # An explicitly post-issue row is read.
    match = reader._POST_ISSUE_EPS.search("Post-issue earnings per share 41.20")
    assert match and match.group("value") == "41.20"


# ---------------------------------------------------------------------------
# 4-6. A conflicting stored value is reported, not silently accepted
# ---------------------------------------------------------------------------


def test_a_stored_3_26_is_flagged_as_unresolved_with_the_evidence_needed(golden_input):
    from ipo_screening.pipeline import evaluate, load_config

    doc = copy.deepcopy(golden_input)
    doc["issue"]["post_issue_eps"] = 3.26
    doc["issue"]["post_issue_shares"] = JIO_POST_ISSUE_SHARES
    doc["issue"].pop("post_issue_eps_basis", None)
    doc["_evidence"].pop("issue.post_issue_eps", None)

    out = evaluate(doc, load_config("config/ipo-config.v1.5.0.json"), mode="final", evaluation_datetime=EVAL_AT)
    findings = [
        f
        for f in out.record.validation.get("warnings", []) + out.record.validation.get("errors", [])
        if f.get("code") == "POST_ISSUE_EPS_RECONCILIATION"
    ]
    assert findings, out.record.validation
    message = findings[0]["message"]
    assert "3.26" in message
    assert "unresolved" in message
    assert "post-issue earnings figure" in message
    assert "weighted-average" in message
    # The captured value is preserved: this is a disclosure of a conflict, not
    # an overwrite of what the record says.
    assert out.record.to_dict()["input_snapshot"]["input"]["issue"]["post_issue_eps"] == 3.26


def test_a_derived_value_is_never_reported_as_a_conflict(golden_input):
    """A figure the engine derived from PAT/shares reconciles by construction."""
    from ipo_screening.pipeline import evaluate, load_config

    from ipo_screening.canonical_input import build_canonical_input

    doc = copy.deepcopy(golden_input)
    shares = doc["issue"]["post_issue_shares"]
    # The canonical normalises the filing's unit to INR crore; the EPS the
    # engine derives uses that same rupee basis.
    implied = round(build_canonical_input(doc).latest.get("pat") * 1e7 / shares, 2)
    doc["issue"]["post_issue_eps"] = implied
    doc["issue"]["post_issue_eps_basis"] = "derived"
    doc["_evidence"]["issue.post_issue_eps"] = {
        "evidence_id": "EV-issue-post_issue_eps",
        "source_id": doc["_sources"][0]["source_id"],
        "locator": "Derived by the engine (not printed in the filing)",
        "extraction_method": "DERIVED",
        "extraction_confidence": 0.9,
        "note": "derived: latest full-year PAT / post-issue shares",
    }

    out = evaluate(doc, load_config("config/ipo-config.v1.5.0.json"), mode="final", evaluation_datetime=EVAL_AT)
    codes = [f.get("code") for f in out.record.validation.get("warnings", [])]
    assert "POST_ISSUE_EPS_RECONCILIATION" not in codes, out.record.validation


def test_basis_field_validates_and_rejects_an_invented_basis(golden_input):
    good = copy.deepcopy(golden_input)
    good["issue"]["post_issue_eps_basis"] = "derived"
    assert not [f for f in validate_schema(good) if "post_issue_eps_basis" in str(f.location)]

    bad = copy.deepcopy(golden_input)
    bad["issue"]["post_issue_eps_basis"] = "guessed"
    assert [f for f in validate_schema(bad) if "post_issue_eps_basis" in str(f.location)]


# ---------------------------------------------------------------------------
# 7-8. The recorded defect itself: the historical Jio record
# ---------------------------------------------------------------------------


def test_the_historical_jio_record_is_the_lakh_assumption_of_the_same_derivation():
    """Pins *why* 3.26 exists, so the defect cannot return unnoticed.

    300,527 (INR millions) / 9,209,030,830 shares:
      x 1e5 (a lakh assumption)   -> 3.26   <- the stored historical value
      x 1e6 (the filing's unit)   -> 32.63  <- what the engine derives now
    The stored value is preserved; nothing here rewrites the record.
    """
    import json

    fixture = json.load(open("fixtures/jio/jio_canonical_2026-10-19_pre_evidence_remediation.json", encoding="utf-8"))
    assert fixture["financials"]["reporting_unit"] == "INR_MILLIONS"
    pat = next(p["pat"] for p in fixture["financials"]["periods"] if p["fy"] == "FY2026")
    shares = fixture["issue"]["post_issue_shares"]

    assert fixture["issue"]["post_issue_eps"] == 3.26
    assert round(pat * 1e5 / shares, 2) == 3.26
    assert round(pat * 1e6 / shares, 2) == 32.63


def test_the_historical_jio_record_is_flagged_as_unresolved_by_the_validator():
    import json

    from ipo_screening.canonical_input import build_canonical_input
    from ipo_screening.pipeline import load_config
    from ipo_screening.semantic_validation import validate_semantics
    from ipo_screening.snapshots import MarketSnapshot, PeerSnapshot

    fixture = json.load(open("fixtures/jio/jio_canonical_2026-10-19_pre_evidence_remediation.json", encoding="utf-8"))
    report = validate_semantics(
        build_canonical_input(fixture),
        load_config("config/ipo-config.v1.5.0.json"),
        peers=PeerSnapshot(
            snapshot_id="", as_of=None, observations=(), staleness_days=0, min_listed_years=0.0
        ),
        market=MarketSnapshot(snapshot_id="", as_of=None, blocks=(), staleness_hours=0),
    )
    hits = [f for f in report.findings if f.code == "POST_ISSUE_EPS_RECONCILIATION"]
    assert len(hits) == 1, [f.code for f in report.findings]
    message = hits[0].message
    assert "32.6" in message and "3.26" in message
    assert "unresolved" in message
    # The historical value itself is untouched in the fixture.
    assert fixture["issue"]["post_issue_eps"] == 3.26
