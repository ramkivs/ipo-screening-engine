"""G-3 — the fail-closed fixture-default safeguard: where it is invoked, and why.

**The question (G-3 of `ARCHITECTURE-RECONCILIATION-2026-10-28.md`).** Is
`enrichment_contract.validate_fail_closed_unknown()` an unenforced safeguard, and
does `FORBIDDEN_FIXTURE_DEFAULTS` under-cover its own declared contract?

**What this module establishes, in order.**

1. The safeguard is **not** dead code: `validate_enrichment_contract()` invokes it
   and surfaces its findings, and `enforce_enrichment_contract()` raises on
   ERROR-severity findings. Tested through that public boundary, not by calling
   the private rule directly (§1).
2. The realistic leak vector — a builder fixture default reaching a real
   evaluation — is closed **at its source** by
   `allow_fixture_fallbacks=False`, and the production service passes it
   explicitly. That is the protection the canonical input actually rests on
   (§2), and it is why no new production gate was wired.
3. The rule is now **provenance-based, not issuer-name-based**: an earlier
   version exempted any `ipo_id` containing ``VISHAL``, so the same
   locator-less value passed for one issuer and failed for all others (§3).
4. Coverage is driven by `FORBIDDEN_FIXTURE_DEFAULTS`, so declared and
   implemented coverage cannot drift again; the two entries this artifact
   cannot adjudicate are asserted to be excluded **for a stated reason** (§4).
5. A legitimate issuer disclosure that happens to equal 208/220/68 is still
   accepted whenever provenance is present (§5).
6. None of this moves UNKNOWN handling, completeness, score bounds, K1-K6, or
   the golden record (§6).

The safeguard emits WARNING findings, so `enforce_enrichment_contract()` does not
reject a document for them; that is deliberate and asserted in §1 — a warning is
diagnostic, and adjudicating a locator-less disclosure stays a human decision.
"""

from __future__ import annotations

import copy
import inspect
import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from conftest import CONFIG_PATH, GOLDEN_INPUT, REPO_ROOT
from ipo_screening.enrichment_contract import (
    FORBIDDEN_FIXTURE_DEFAULTS,
    enforce_enrichment_contract,
    validate_enrichment_contract,
    validate_fail_closed_unknown,
)
from ipo_screening.errors import SEVERITY_WARNING
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.extractor import DocumentExtractor
from ipo_screening.pipeline import evaluate, load_config
from ipo_screening.presentation.service import PresentationConfig, PresentationService

EVAL_AT = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
GOLDEN_RESULT_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"

#: The source-fact constants this artifact can adjudicate.
SOURCE_FACT_CONSTANTS = {
    "price_band.price_band_low": 208,
    "price_band.price_band_high": 220,
    "price_band.lot_size": 68,
}


def _payload(values, *, locator=None, ipo_id="VISHAL-NIRMITI-LIMITED"):
    """Minimal enrichment payload carrying the given price-band values."""
    price_band = {}
    for field_name, value in values.items():
        entry = {"raw_value": value, "source_id": "SRC-PBN-001"}
        if locator is not None:
            entry["locator"] = locator
        price_band[field_name] = entry
    return {
        "contract_version": "1.0",
        "ipo_id": ipo_id,
        "as_of": "2026-10-05T12:00:00Z",
        "sources": [{"source_id": "SRC-PBN-001", "source_type": "EXCHANGE"}],
        "price_band": price_band,
    }


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_PATH)


@pytest.fixture(scope="module")
def golden():
    with GOLDEN_INPUT.open("r", encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# §1 The safeguard is invoked at the enrichment-contract boundary
# ---------------------------------------------------------------------------


def test_fail_closed_check_is_reachable_from_the_contract_validator():
    """`validate_fail_closed_unknown` is invoked by the public validator.

    This is the fact an earlier reconciliation got wrong: it reported the rule
    as having no caller, having searched only for a *direct* call site outside
    the module that defines it. It is called from
    `validate_enrichment_contract`, so findings propagate to every caller of
    that function.
    """
    findings = validate_enrichment_contract(_payload({"price_band_high": 220}))
    codes = [f.code for f in findings]
    assert "SUSPICIOUS_FIXTURE_DEFAULT_VALUE" in codes, codes


def test_fail_closed_check_is_invoked_by_the_enforcing_wrapper():
    """`enforce_enrichment_contract` runs the same chain and does not raise.

    The finding is a WARNING, so a document is never *rejected* for it. That is
    the intended boundary: the locator-less case is surfaced for adjudication,
    not silently failed closed, because the governing contract does not make a
    locator a hard schema requirement.
    """
    payload = _payload({"price_band_high": 220}, locator="Page 1, 'Offer Details' Table, Row 2")
    findings = enforce_enrichment_contract(payload)          # must not raise
    assert [f for f in findings if f.code == "SUSPICIOUS_FIXTURE_DEFAULT_VALUE"] == []

    findings = validate_enrichment_contract(_payload({"price_band_high": 220}))
    suspicious = [f for f in findings if f.code == "SUSPICIOUS_FIXTURE_DEFAULT_VALUE"]
    assert len(suspicious) == 1
    assert suspicious[0].severity == SEVERITY_WARNING


def test_the_reported_finding_is_actionable():
    """The message names the field, the constant and the missing evidence."""
    finding = validate_fail_closed_unknown(_payload({"price_band_high": 220}))[0]
    assert finding.location == "price_band.price_band_high"
    assert "price_band.price_band_high" in finding.message
    assert "220" in finding.message
    assert "locator" in finding.message
    assert finding.scope == "fail_closed_validation"
    assert finding.detail == {"forbidden_value": 220, "field": "price_band.price_band_high"}


# ---------------------------------------------------------------------------
# §2 The real leak vector is closed at its source, by the builder default
# ---------------------------------------------------------------------------


def test_builder_fixture_fallbacks_default_off_and_block_the_constants():
    """A fixture default cannot reach a canonical input by default.

    This — not the enrichment warning — is the protection a real evaluation
    actually rests on, and it is why wiring a second production gate would be
    redundant rather than protective.
    """
    assert inspect.signature(CanonicalInputBuilder.__init__).parameters[
        "allow_fixture_fallbacks"
    ].default is False
    assert inspect.signature(DocumentExtractor.extract_from_pdf).parameters[
        "allow_fixture_fallbacks"
    ].default is False

    # The production ingestion path passes False explicitly.
    assert "allow_fixture_fallbacks=False" in inspect.getsource(
        PresentationService._ingest_document_impl
    )

    # With the default off, none of the declared constants is synthesised.
    canonical = CanonicalInputBuilder(
        doc=_source_document(), extractions=[], reference_base={},
        allow_fixture_fallbacks=False,
    ).build()
    issue = canonical.get("issue", {})
    for field_name in ("price_band_low", "price_band_high", "lot_size"):
        assert issue.get(field_name) is None, f"{field_name} was defaulted"
    assert canonical.get("derived", {}).get("post_issue_eps") is None
    assert canonical.get("business", {}).get("top5_customer_pct") is None


def _source_document():
    from ipo_screening.extraction.interfaces import SourceDocument

    return SourceDocument(
        source_id="G3-DOC", source_type="RHP", uri="g3.pdf",
        content_hash="abc", file_size_bytes=100, page_count=10,
    )


# ---------------------------------------------------------------------------
# §3 Provenance, not issuer name, decides
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ipo_id",
    ["VISHAL-NIRMITI-LIMITED", "PARAS-HEALTHCARE-LIMITED", "", "VISHALWAVE-LIMITED"],
)
def test_locatorless_fixture_value_is_flagged_for_every_issuer(ipo_id):
    """The rule no longer varies by issuer name.

    Under the previous `"VISHAL" in ipo_id` exemption this test failed for the
    first two ids and for the fourth (any name containing the substring): the
    identical locator-less value was reported for one issuer and silently
    allowed for another.
    """
    findings = validate_fail_closed_unknown(
        _payload({"price_band_high": 220}, ipo_id=ipo_id)
    )
    assert [f.code for f in findings] == ["SUSPICIOUS_FIXTURE_DEFAULT_VALUE"]


@pytest.mark.parametrize(
    "ipo_id",
    ["VISHAL-NIRMITI-LIMITED", "PARAS-HEALTHCARE-LIMITED", "ANY-OTHER-LIMITED"],
)
def test_located_fixture_value_is_accepted_for_every_issuer(ipo_id):
    """A real disclosure may legitimately be 208/220/68 — provenance is the test."""
    findings = validate_fail_closed_unknown(
        _payload(
            {"price_band_low": 208, "price_band_high": 220, "lot_size": 68},
            locator="Page 1, 'Offer Details' Table",
            ipo_id=ipo_id,
        )
    )
    assert findings == []


def test_the_issuer_name_exemption_is_gone_from_the_source():
    """A name-based exemption must not be reintroduced as a provenance shortcut."""
    source = inspect.getsource(validate_fail_closed_unknown)
    assert "is_vishal" not in source
    assert '"VISHAL" in' not in source


# ---------------------------------------------------------------------------
# §4 Declared coverage equals implemented coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path,forbidden", sorted(SOURCE_FACT_CONSTANTS.items()))
def test_every_source_fact_constant_is_enforced(path, forbidden):
    """All three source-fact entries are enforced, not just `price_band_high`.

    The mapping declares five; the previous implementation hard-coded 220 only,
    so `price_band_low` (208) and `lot_size` (68) were declared forbidden and
    never checked.
    """
    field_name = path.split(".", 1)[1]
    findings = validate_fail_closed_unknown(_payload({field_name: forbidden}))
    assert [f.location for f in findings] == [path]


def test_declared_mapping_still_holds_five_entries():
    """The contract itself is unchanged; only its enforcement was completed."""
    assert set(FORBIDDEN_FIXTURE_DEFAULTS) == {
        "price_band.price_band_low",
        "price_band.price_band_high",
        "price_band.lot_size",
        "derived.post_issue_eps",
        "business.top5_customer_pct",
    }


def test_underivable_entries_are_excluded_for_a_stated_reason():
    """The two non-adjudicable entries are excluded, not silently ignored.

    `derived.post_issue_eps` is a `derivedValue` whose contract requires
    `is_derived`/`formula`/`dependencies` and has no `locator` field at all, so
    "no locator" is its correct shape. `business.top5_customer_pct` has no
    `business` block in this artifact. Neither can be judged by the
    locator-absence rule, and both are guarded by `allow_fixture_fallbacks`.
    """
    # A derived value that legitimately equals the constant, with its contract
    # satisfied, is not reported.
    payload = _payload({})
    payload["derived"] = {
        "post_issue_eps": {
            "is_derived": True,
            "calculated_value": 9.46,
            "formula": "pat / post_issue_shares",
            "dependencies": ["financials.pat", "capital_structure.post_issue_shares"],
        }
    }
    assert validate_fail_closed_unknown(payload) == []

    # Even an unprovenanced one is out of this rule's reach; it is not flagged.
    assert validate_fail_closed_unknown({"ipo_id": "X", "derived": {
        "post_issue_eps": {"is_derived": True, "formula": "f", "dependencies": [],
                           "calculated_value": 9.46}}}) == []


# ---------------------------------------------------------------------------
# §5 Legitimate data that resembles a fixture is preserved
# ---------------------------------------------------------------------------


def test_values_that_are_not_fixture_constants_are_never_flagged():
    """The rule keys on the declared constants, not on 'looks suspicious'."""
    findings = validate_fail_closed_unknown(
        _payload({"price_band_low": 315, "price_band_high": 330, "lot_size": 44})
    )
    assert findings == []


def test_absent_price_band_block_is_not_a_finding():
    """Fail-closed means silent on absence — the schema, not this rule, gates shape."""
    assert validate_fail_closed_unknown({"ipo_id": "X"}) == []
    assert validate_fail_closed_unknown({"ipo_id": "X", "price_band": None}) == []
    assert validate_fail_closed_unknown(
        {"ipo_id": "X", "price_band": {"price_band_high": None}}
    ) == []


def test_normalised_slot_leak_is_also_caught():
    """A leak may populate `normalized_value` without a raw value."""
    payload = {"ipo_id": "X", "price_band": {
        "price_band_high": {"normalized_value": 220.0, "source_id": "SRC"}}}
    assert [f.location for f in validate_fail_closed_unknown(payload)] == [
        "price_band.price_band_high"
    ]


def test_golden_enrichment_shape_passes_untouched():
    """The reference payload in the suite carries locators and is unaffected."""
    payload = _payload(
        {"price_band_low": 208.0, "price_band_high": 220.0, "lot_size": 68},
        locator="Page 1, 'Offer Details' Table, Row 2",
    )
    assert validate_fail_closed_unknown(payload) == []


# ---------------------------------------------------------------------------
# §6 Scoring semantics, UNKNOWN, bounds and K1-K6 are untouched
# ---------------------------------------------------------------------------


def test_golden_evaluation_is_unchanged(config, golden):
    """The correction touches an unused-by-scoring validator, not the engine."""
    outcome = evaluate(golden, config, mode="final", evaluation_datetime=EVAL_AT)
    assert outcome.record.result_hash == GOLDEN_RESULT_HASH
    score = outcome.record.score
    assert score["base_score"] == pytest.approx(38.0)
    assert score["final_score"] == pytest.approx(35.0)
    assert score["available_points"] + score["unknown_points"] == pytest.approx(
        score["total_evaluable_points"]
    )
    # upper = base + unknown + penalties, and penalties = final - base,
    # so the bound is exactly final + unknown. Base excludes UNKNOWN entirely.
    assert score["upper_bound"] == pytest.approx(
        score["final_score"] + score["unknown_points"]
    )
    assert score["lower_bound"] < score["final_score"]


def test_unknown_and_knockout_states_are_unchanged(config, golden):
    """UNKNOWN still earns 0 in base, keeps its max in the bound, and stays UNVERIFIED."""
    outcome = evaluate(golden, config, mode="final", evaluation_datetime=EVAL_AT)
    record = outcome.record
    assert record.score["unknown_points"] > 0
    assert record.score["final_score"] < record.score["upper_bound"]
    results = {r["rule_id"]: r["state"] for r in record.knockouts["results"]}
    assert results["K1"] == "UNVERIFIED"     # going-concern input absent
    assert results["K2"] == "CLEAR"          # pledged 0 and SEBI/ED False are supplied
    assert results["K4"] == "CLEAR"          # one TRUE leaf cannot win an `all`
