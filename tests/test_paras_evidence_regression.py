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

Execution status: RUN 2026-10-23 on commit 4b1c67f -- 9/9 passed with the artifact
present at the published hash.  Both guard directions were verified: with the
artifact absent the module reports 9 *skipped* (never passed), and with a single
byte changed at constant length all 9 error at the fixture hash assertion.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

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
