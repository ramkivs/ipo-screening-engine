"""Real-document regression for the Paras Healthcare issue-term failure (2026-10-23).

Evidence artifact
-----------------
``evidence/non-authoritative/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf``

* recovered from the evidence branch ``evidence/jio-score-33-recovery-20261023``,
  commit ``1dd6e14e7fa50a677beefba9ca7d0d1a7b322c58``, path
  ``docs/investigations/paras-healthcare/U85110HR1987PLC035823 _ParasHealthcare.pdf``;
* 11,577,075 bytes, 651 pages, sha256
  ``e0a3187fe18d1c12f88f29170291972714cf15be7946e8a7f4a7d8c914570e74``
  (asserted below, so a substituted or truncated file fails loudly);
* investigation evidence only.  It is **not** registered as official
  evaluation evidence and no evaluation is produced from it.

The document is a real RHP whose cover states the Offer window, whose
abbreviations/definitions pages state the price band and bid lot as ``[●]``,
and whose Articles contain a defined term ``"Closing Date" shall mean 14 July
2017`` — the two things that produced the reported failure: a historical 2017
date competing with the current 2026 close date, and a document rejected
wholesale so that its disclosed Offer-for-Sale amount was never reached.

The module is skipped when the evidence file is absent, so the suite stays
runnable in a checkout that does not carry the artifact.  General behaviour is
covered issuer-independently in ``tests/test_official_rhp_terms_and_dates.py``;
this module pins the actual document.

Execution status: RUN 2026-10-24 -- parser cases and the new *upload-path* cases
pass with the artifact present at the published hash (the upload fixture extracts
the 651-page filing through ``DocumentExtractor``, which takes ~45 s).  Both guard
directions were verified: with the artifact absent the module reports every case
as *skipped* (never passed), and with a single byte changed at constant length
all of them error at the fixture hash assertion.

Two extraction paths are pinned here on the *same* evidence: the parser path
(``parse_official_rhp``) and the upload path (``DocumentExtractor`` →
``CanonicalInputBuilder``), which previously disagreed about this filing.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from ipo_screening.extraction.extractor import DocumentExtractor
from ipo_screening.extraction.official_offer_amounts import parse_official_rhp
from ipo_screening.extraction.price_band_notice import PriceBandNoticeParser

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    REPO_ROOT
    / "evidence"
    / "non-authoritative"
    / "paras-healthcare"
    / "U85110HR1987PLC035823 _ParasHealthcare.pdf"
)
EXPECTED_SHA256 = "E0A3187FE18D1C12F88F29170291972714CF15BE7946E8A7F4A7D8C914570E74"
URL = "https://www.sebi.gov.in/sebi_data/attachdocs/paras-rhp.pdf"

pytestmark = pytest.mark.skipif(
    not EVIDENCE.exists(), reason="retained Paras evidence PDF is not present in this checkout"
)


@pytest.fixture(scope="module")
def raw() -> bytes:
    data = EVIDENCE.read_bytes()
    assert hashlib.sha256(data).hexdigest().upper() == EXPECTED_SHA256
    return data


@pytest.fixture(scope="module")
def parsed(raw):
    return parse_official_rhp(raw, URL)


@pytest.fixture(scope="module")
def uploaded(raw):
    """The *upload* path: what ``PresentationService.ingest_document`` builds.

    Same bytes, different extractor.  Extraction is the expensive part (~45 s
    for 651 pages), so it runs once for the module.
    """
    canonical, _report = DocumentExtractor().extract_from_pdf(
        pdf_path=EVIDENCE, allow_fixture_fallbacks=False
    )
    return canonical


def test_evidence_bytes_match_the_published_hash(raw):
    assert len(raw) == 11577075
    assert hashlib.sha256(raw).hexdigest().upper() == EXPECTED_SHA256


def test_the_rhp_is_not_a_price_band_notice(parsed):
    assert parsed.document_class == "OFFICIAL_RHP_TERMS"
    assert parsed.is_classified_notice is False
    assert parsed.company_name == "PARAS HEALTHCARE LIMITED"
    assert parsed.cin == "U85110HR1987PLC035823"


def test_the_notice_parser_refuses_the_document_by_document_class(raw):
    """Classification is decided by the document's title pages, not by tokens."""
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(raw))
    pages = [(number, reader.pages[number - 1].extract_text() or "") for number in range(1, 6)]
    is_notice, reason = PriceBandNoticeParser()._classify_document(
        "\n".join(text for _, text in pages), pages
    )
    assert is_notice is False
    assert "prospectus" in reason.lower()


def test_current_issue_window_is_read_from_the_cover(parsed):
    assert parsed.open_date is not None and parsed.open_date.value == "2026-10-21"
    assert parsed.close_date is not None and parsed.close_date.value == "2026-10-23"
    assert parsed.close_date.page == 3
    assert "OCTOBER 23, 2026" in parsed.close_date.quote.upper()
    assert parsed.close_date.extraction_method == "DETERMINISTIC_PDF"
    assert parsed.close_date.verification == "VERIFIED"


def test_the_historical_2017_defined_term_is_not_the_close_date(raw, parsed):
    """p590 defines ``"Closing Date"`` as 14 July 2017; it must not compete.

    On this document the date is rejected structurally -- the Articles'
    definitions page is not an issue-term page, so it is never read as an
    issue window -- which is exactly the "structural position, not proximity to
    an IPO word" rule.  The synthetic case in
    ``test_official_rhp_terms_and_dates.py`` pins the defined-term guard that
    applies if such a line ever *does* appear on a term page.
    """
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(raw))
    cover = [(3, reader.pages[2].extract_text() or "")]
    definitions = [(590, reader.pages[589].extract_text() or "")]
    assert "14 July 2017" in definitions[0][1]
    parser = PriceBandNoticeParser()
    open_field, close_field, findings = parser._extract_dates(cover + definitions)
    assert close_field is not None and close_field.value == "2026-10-23"
    assert open_field is not None and open_field.value == "2026-10-21"
    # Nothing on the definitions page becomes a close-date candidate, and no
    # conflict is reported: 2017 never enters the candidate set.
    assert all("2017" not in finding.message for finding in findings)
    assert close_field.value != "2017-07-14"
    # The exclusion is structural (p590 is not an issue-term page), so the
    # value is never even examined; if it ever is, the defined-term guard and
    # the document-date window are pinned by the synthetic cases.
    assert all(item["value"] != "2017-07-14" for item in parser._last_excluded_dates)
    assert parsed.close_date.value == "2026-10-23"


def test_offer_for_sale_amount_is_read_from_the_offer_summary(parsed):
    """The disclosed OFS amount (₹9,500.00 million) is resolved, not dropped."""
    assert parsed.ofs_amount is not None
    assert parsed.ofs_amount.value == 9500.0
    assert parsed.ofs_amount_unit == "INR_MILLIONS"
    assert parsed.ofs_amount.page == 3
    assert "9,500.00" in parsed.ofs_amount.quote
    assert parsed.ofs_amount.verification == "VERIFIED"


def test_fresh_issue_amount_is_read_from_the_offer_summary(parsed):
    assert parsed.fresh_issue_amount is not None
    assert parsed.fresh_issue_amount.value == 5000.0
    assert parsed.fresh_issue_amount_unit == "INR_MILLIONS"
    assert parsed.fresh_issue_amount.page == 3


def test_price_band_and_lot_are_placeholders_not_defaults(parsed):
    """The document states [●] for these; they stay unset and are diagnosed."""
    assert parsed.price_band_low is None
    assert parsed.price_band_high is None
    assert parsed.lot_size is None
    placeholder_fields = {
        item["field"]
        for item in (parsed.metadata.get("issue_term_diagnostics") or [])
        if item["code"] == "SOURCE_PLACEHOLDER"
    }
    assert {"price_band_low", "price_band_high", "lot_size"} <= placeholder_fields
    assert parsed.metadata.get("issue_term_errors") == {}


def test_no_field_is_defaulted_to_zero_or_guessed(parsed):
    for name in ("price_band_low", "price_band_high", "lot_size"):
        assert getattr(parsed, name) is None
    assert parsed.ofs_amount.value == 9500.0  # stated, not inferred
    assert parsed.fresh_issue_amount.value == 5000.0


# ---------------------------------------------------------------------------
# The upload path (DocumentExtractor -> CanonicalInputBuilder) on the same PDF
#
# These are the fields the 2026-10-24 controlled ingestion left unresolved
# while the parser path had already read them.  Both paths must now agree.
# ---------------------------------------------------------------------------

def test_upload_path_reads_the_current_issue_window(uploaded):
    issue = uploaded["issue"]
    assert issue["open_date"] == "2026-10-21"
    assert issue["close_date"] == "2026-10-23"
    # The Articles' "Closing Date" definition (p590, 14 July 2017) is not the
    # issue window on either path.
    assert issue["close_date"] != "2017-07-14"


def test_upload_path_reads_the_disclosed_monetary_components(uploaded):
    """₹5,000 m fresh issue and ₹9,500 m OFS, in the filing's reporting unit.

    The filing's restated statements are captioned "(All amounts are in INR
    million, unless otherwise stated)", so the reporting unit of the extracted
    input **is** millions and the offer components are stated in it directly.

    This assertion previously read ``INR_LAKHS`` with ``50,000/95,000``.  That
    was not an independent contract but the visible half of a defect: the unit
    header was not recognised, so the statements were booked as lakhs and every
    monetary value taken from them was ten times too small against an issue
    size normalised separately.  The unit is now read (2026-10-24), the offer
    components are converted with it, and the ratio between them — which never
    depended on the unit — is unchanged.
    """
    issue = uploaded["issue"]
    reporting_unit = uploaded["financials"]["reporting_unit"]
    assert reporting_unit == "INR_MILLIONS"
    assert issue["fresh_issue"] == 5000.0
    assert issue["ofs"] == 9500.0
    assert round(issue["fresh_issue"] / (issue["fresh_issue"] + issue["ofs"]) * 100, 2) == 34.48


def test_upload_path_and_parser_path_agree_once_units_are_normalized(uploaded, parsed):
    """Cross-path consistency: the same money, stated the same way."""
    issue = uploaded["issue"]
    assert parsed.ofs_amount_unit == "INR_MILLIONS"
    assert parsed.fresh_issue_amount_unit == "INR_MILLIONS"
    assert issue["ofs"] == parsed.ofs_amount.value
    assert issue["fresh_issue"] == parsed.fresh_issue_amount.value


def test_upload_path_keeps_the_placeholder_terms_unresolved(uploaded):
    issue = uploaded["issue"]
    assert issue["price_band_low"] is None
    assert issue["price_band_high"] is None
    assert issue["lot_size"] is None


def test_upload_path_records_provenance_for_every_resolved_term(uploaded):
    evidence = uploaded["_evidence"]
    for field_path in ("issue.open_date", "issue.close_date",
                       "issue.ofs", "issue.fresh_issue"):
        spec = evidence[field_path]
        assert spec["source_id"] == uploaded["_sources"][0]["source_id"]
        assert spec.get("locator")
        assert spec.get("quote")


# ---------------------------------------------------------------------------
# Reading gaps found by scoring this filing end to end (2026-10-24)
#
# The operator's run scored 8.0 with 71 points unknown.  Reproducing it showed
# that four of those unknowns were *reading* defects, not missing disclosures;
# the parsers are pinned synthetic-first in
# ``tests/test_paras_extraction_gaps_20261024.py`` and the filing's own numbers
# are pinned here, on the same single extraction.
# ---------------------------------------------------------------------------


def test_upload_path_now_reads_pat_for_every_fiscal_year(uploaded):
    """Restated P&L: "Profit/(loss) for the period/year (A)".

    FY2024 (153.31), FY2025 (579.83) and FY2026 438.34 — losses in the two
    earlier years, profit in the latest.  These are the filing's own figures
    and they are what makes the margin trend and the "profit declining" leaf
    answerable at all.
    """
    periods = {p["fy"]: p for p in uploaded["financials"]["periods"]}
    assert [periods[fy]["pat"] for fy in ("FY2024", "FY2025", "FY2026")] == [
        -153.31,
        -579.83,
        438.34,
    ]


def test_upload_path_now_reads_cash_flow_from_operations(uploaded):
    """Restated cash flow: "Net cash generated from operating activities (A)"."""
    periods = {p["fy"]: p for p in uploaded["financials"]["periods"]}
    assert [periods[fy]["cfo"] for fy in ("FY2024", "FY2025", "FY2026")] == [
        924.77,
        861.91,
        1635.12,
    ]


def test_upload_path_reads_the_contingent_liability_summary_total(uploaded):
    """The "Summary of Contingent Liabilities" Total row, FY2026 column.

    3,905.01 as at 31 March 2026 — the figure the RHP's own risk factor turns
    into 98.88% of the FY2026 net worth of 3,949.41.  The reader takes the
    issuer's Total, never a sum of the parts, and never the June-2026 interim
    column (which would be divided by a full-year net worth).
    """
    financials = uploaded["financials"]
    assert financials["contingent_liabilities"] == 3905.01
    assert financials["contingent_liabilities_unquantified"] is None
    net_worth = {p["fy"]: p["net_worth"] for p in financials["periods"]}["FY2026"]
    assert round(3905.01 / net_worth * 100, 2) == 98.88


def test_the_reading_gaps_are_what_kept_knockout_k5_blind(uploaded):
    """With the disclosed contingent liabilities read, K5 is TRIGGERED.

    This is the point of the whole correction: the score of 8.0 was not the
    engine judging a weak issuer, it was the engine unable to see a disclosed
    knockout.  Contingent liabilities of 3,905.01 against a net worth of
    3,949.41 is 98.88% — far above K5's 50% threshold — and the RHP states the
    ratio itself in a risk factor ("contingent liabilities ... constituted
    89.55% of our net worth" as at 30 June 2026).

    Exercised through the engine's own derivation and knockout modules, not a
    re-implementation.  ``pipeline.evaluate`` is not used here because the
    schema correctly refuses an input whose price band and lot are undisclosed
    — the required-term gate — and no third-party value is substituted to get
    past it.  K5 does not depend on those terms.
    """
    from ipo_screening.canonical_input import build_canonical_input
    from ipo_screening.derived import derive
    from ipo_screening.knockouts import evaluate_knockouts
    from ipo_screening.pipeline import load_config

    config = load_config()
    derived = derive(build_canonical_input(uploaded), config, None, None)
    assert round(derived.value_of("contingent_liab_pct_networth"), 2) == 98.88
    results = {rule.rule_id: rule for rule in evaluate_knockouts(config, derived)}
    assert results["K5"].state == "TRIGGERED"
    # The two earlier-year losses are now visible too, so "profit declining"
    # is answerable and answers False (the trend is improving).
    assert derived.value_of("profit_declining") is False
    # The terms the filing states as [●] stay unresolved: this correction
    # reads disclosed facts, it does not fill placeholders.
    assert uploaded["issue"]["price_band_low"] is None


# ---------------------------------------------------------------------------
# A34 (approved alternative B): the p. 117 carve-out is not an early release
# ---------------------------------------------------------------------------


def test_a34_carve_out_leaves_the_early_unlock_field_unknown(uploaded):
    """Paras prints the Regulation 17(1)(c) carve-out on p. 117, not a release.

    Before A34 the institutional carve-out reader emitted
    ``large_holders_unlocked_early = True`` with a p. 117 quotation.  A34
    removes that inference: the carve-out states a purchase-anchored minimum
    and prints no purchase dates.  No other sentence in this filing evidences
    an early release, so the field stays ``null`` and no evidence row is
    emitted for it.  The promoter lock-in is still read on its own evidence.
    """
    capital = uploaded["capital_structure"]
    assert capital["promoter_lockin_in_place"] is True
    assert capital["large_holders_unlocked_early"] is None
    evidence = uploaded.get("_evidence", {})
    assert "capital_structure.large_holders_unlocked_early" not in evidence
    assert evidence["capital_structure.promoter_lockin_in_place"]["page"] == 115
    # The carve-out is genuinely in the filing; the reader must ignore it for
    # this field, not fail to find it.
    import pypdf

    reader = pypdf.PdfReader(str(EVIDENCE))
    page_117 = " ".join((reader.pages[116].extract_text() or "").split())
    assert "at least six months from the date of purchase" in page_117


def test_a34_paras_end_to_end_result(uploaded):
    """A34's measured Paras effect: only completeness / bounds move.

    Rebuilt on the same canonical input with the identity-bound issue terms
    the pinned record uses (band 660/693, lot 21).  The flag that PR #13 set
    from the carve-out is absent, so C ``lockin`` is UNKNOWN again: final score
    13.0, AVOID and K5 TRIGGERED are unchanged, completeness returns from
    44.21% to 43.16%, and the upper bound returns from 66.0 to 67.0.
    """
    import copy
    from datetime import datetime, timezone

    from ipo_screening.pipeline import evaluate, load_config

    document = copy.deepcopy(uploaded)
    document["issue"].update(
        price_band_low=660.0, price_band_high=693.0, lot_size=21
    )
    outcome = evaluate(
        document,
        load_config(),
        mode="final",
        evaluation_datetime=datetime(2026, 10, 5, 12, tzinfo=timezone.utc),
    )
    record = outcome.record.to_dict()
    score = record["score"]
    assert score["final_score"] == 13.0
    assert score["base_score"] == 16.0
    assert score["penalties_total"] == -3.0
    assert round(score["completeness_pct"], 2) == 43.16
    assert score["lower_bound"] == 1.0
    assert score["upper_bound"] == 67.0
    assert record["verdict"]["verdict"] == "AVOID"
    knockouts = {rule["rule_id"]: rule["state"] for rule in record["knockouts"]["results"]}
    assert knockouts["K5"] == "TRIGGERED"
    assert knockouts["K1"] == "UNVERIFIED"
    assert knockouts["K2"] == "UNVERIFIED"
    criteria = {
        c["criterion_id"]: c
        for module in score["modules"]
        for c in module["criteria"]
    }
    assert criteria["lockin"]["state"] == "UNKNOWN"
    assert criteria["lockin"].get("score") is None
    assert criteria["board_kmp"]["band"] == "high_churn"
    assert criteria["board_kmp"]["score"] == 0.0
    assert uploaded["governance"]["kmp_exits_2y"] == 4
