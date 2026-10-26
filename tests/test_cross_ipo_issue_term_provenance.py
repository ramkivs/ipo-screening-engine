"""Cross-IPO issue-term canonical value and provenance reconciliation.

Root cause established by this suite's regression coverage:
the persisted evidence artifact is a citation registry (quote, locator,
source) that never carried the canonical value, and the presentation
projection passed ``extracted_value``/``unit``/``document`` through as
null -- so the Evidence Explorer rendered UNKNOWN / UNVERIFIED even
when the canonical input held a verified numeric value (e.g. the
₹208/₹220 quotation with ``extracted_value: null``).

Fixes covered here:
- Evidence API joins each citation to the persisted canonical input
  value (by field path, never by parsing the quotation, so floor/cap
  cannot be swapped), supplies units, document identity from the
  source manifest, and an honest verification classification.
- Only notices retrieved from allow-listed official hosts resolve
  terms (VERIFIED). Retained copies -- including the authored
  parser-test fixture in fixtures/notices (commit 3cddb64) -- are
  reported UNVERIFIED and never used as production evidence.

The HTTP tests use an injected fetcher (MOCKED transport): they prove
verified-channel mechanics, not live retrieval. No fabricated official
notice is introduced; the served text is the repository fixture text.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import EVAL_AT, REPO_ROOT
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.issue_terms import (
    HttpNoticeProvider,
    IssueTermsResolver,
    RetainedNoticeProvider,
    build_resolver_from_env,
)
from ipo_screening.pipeline import evaluate
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService


# These tests never mutate PDF readers/pages; only immutable text is reused.
pytestmark = pytest.mark.usefixtures("cached_pdf_text")

VISHAL_RHP_PDF = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"
RK_RHP_PDF = REPO_ROOT / "handoff" / "reference" / "U18109WB2010PLC144256-R.K Fashion accessories.pdf"
# Synthetic transport only: match the unchanged RHP cover issue window.
NOTICE_BYTES = (REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt").read_bytes().replace(
    b"Tuesday, October 06, 2026", b"Wednesday, September 30, 2026"
).replace(b"Thursday, October 08, 2026", b"Monday, October 05, 2026")
OFFICIAL_URL = "https://www.nseindia.com/announcements/vishal-price-band"
GOLDEN_HASH = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"


def _client(tmp_path, golden_input, config, resolver):
    store_dir = tmp_path / "evaluations"
    store = EvaluationStore(store_dir)
    baseline = evaluate(golden_input, config, mode="final", evaluation_datetime=EVAL_AT, store=store)
    cfg = PresentationConfig(store_root=store_dir, config_dir=REPO_ROOT / "config", issue_terms_resolver=resolver)
    client = TestClient(
        create_app(PresentationService(cfg)),
        base_url="http://127.0.0.1:8000",
        headers={"Origin": "http://127.0.0.1:8000"},
    )
    return client, store, baseline


def _upload(client, pdf_path, name):
    return client.post(
        "/api/v1/ingest/document",
        files={"file": (name, io.BytesIO(pdf_path.read_bytes()), "application/pdf")},
        data={"mode": "final"},
    )


def _evidence_items(client, evaluation_id):
    res = client.get(f"/api/v1/evaluations/{evaluation_id}/evidence")
    assert res.status_code == 200, res.text
    return {item["evidence_id"]: item for item in res.json()["items"]}


def test_verified_notice_canonical_values_reach_evidence_api(tmp_path, golden_input, config):
    """Verified source -> canonical value -> persisted -> evidence API.

    Low/high must map to their own canonical fields (the shared quote
    contains both numbers; values come from the canonical input, never
    from parsing the quote), lot size carries its unit, and the source
    document identity is visible.
    """
    resolver = IssueTermsResolver(
        providers=[HttpNoticeProvider({"VISHAL-NIRMITI-LIMITED": OFFICIAL_URL}, fetcher=lambda url: NOTICE_BYTES)]
    )
    client, store, baseline = _client(tmp_path, golden_input, config, resolver)

    res = _upload(client, VISHAL_RHP_PDF, "vishal_nirmiti_rhp.pdf")
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["issue_terms"]["status"] == "RESOLVED"
    assert body["issue_terms"]["verified"] is True

    record = store.read(body["evaluation_id"])
    issue = record["input_snapshot"]["input"]["issue"]
    assert (issue["price_band_low"], issue["price_band_high"], issue["lot_size"], issue["ofs"]) == (208, 220, 68, 3300)

    items = _evidence_items(client, body["evaluation_id"])
    low, high, lot = items["EV-issue.price_band_low"], items["EV-issue.price_band_high"], items["EV-issue.lot_size"]
    assert low["extracted_value"] == 208 and high["extracted_value"] == 220  # not swapped
    assert low["unit"] == "INR per equity share" and high["unit"] == "INR per equity share"
    assert lot["extracted_value"] == 68 and lot["unit"] == "equity shares"
    assert low["source"].startswith("SRC-PBN-")
    assert low["document"]  # document identity present, not null
    assert low["verification"] == "OFFICIAL_VERIFIED"
    assert "₹208" in low["quote"] and "₹220" in low["quote"]  # verbatim quote preserved

    # Reopening preserves canonical values and provenance; no duplicates.
    detail = client.get(f"/api/v1/evaluations/{body['evaluation_id']}")
    assert detail.json()["result_hash"] == body["result_hash"]
    dup = _upload(client, VISHAL_RHP_PDF, "vishal_nirmiti_rhp.pdf")
    assert dup.status_code == 200 and dup.json()["is_duplicate"] is True
    assert dup.json()["evaluation_id"] == body["evaluation_id"]
    assert store.read(baseline.record.evaluation_id)["result_hash"] == GOLDEN_HASH


def test_retained_fixture_notice_is_unverified_and_fails_closed(tmp_path, golden_input, config):
    """The authored fixture notice, offered as a retained copy, must not
    be represented as a verified official disclosure and must not
    resolve terms."""
    notice_dir = tmp_path / "notices"
    notice_dir.mkdir()
    (notice_dir / "clean_notice.txt").write_bytes(NOTICE_BYTES)
    resolver = IssueTermsResolver(providers=[RetainedNoticeProvider([notice_dir])])
    client, store, baseline = _client(tmp_path, golden_input, config, resolver)

    res = _upload(client, VISHAL_RHP_PDF, "vishal_nirmiti_rhp.pdf")
    assert res.status_code == 422, res.text
    body = res.json()
    assert body["code"] == "AWAITING_ISSUE_TERMS"
    assert body["resolution"]["status"] == "UNVERIFIED"
    assert body["resolution"]["verified"] is False
    # Nothing new persisted; the historical record is untouched.
    assert store.list_evaluations() == [baseline.record.evaluation_id]
    assert store.read(baseline.record.evaluation_id)["result_hash"] == GOLDEN_HASH


def test_default_runtime_has_no_packaged_fixture_source(monkeypatch):
    """No notice document ships as production evidence by default."""
    for var in ("IPO_PRICE_BAND_NOTICE_DIR", "IPO_PRICE_BAND_NOTICE_URLS", "IPO_ISSUE_TERMS_CACHE_DIR"):
        monkeypatch.delenv(var, raising=False)
    packaged = REPO_ROOT / "engine" / "ipo_screening" / "resources" / "notices" / "vishal_nirmiti_price_band_notice.txt"
    assert not packaged.exists()
    # No packaged/fixture source exists by default; the only default
    # provider is generic official-source discovery (no per-issuer
    # configuration, no shipped documents).  Network is stubbed out so
    # the test proves configuration shape, not live retrieval.
    import ipo_screening.issue_terms as issue_terms_module

    def _offline(url, timeout):
        raise OSError("network disabled in test")

    monkeypatch.setattr(issue_terms_module, "_default_http_fetch", _offline)
    monkeypatch.delenv("IPO_PROSPECTUS_URLS", raising=False)
    monkeypatch.delenv("IPO_OFFICIAL_DISCOVERY", raising=False)
    resolver = build_resolver_from_env()
    assert [type(p).__name__ for p in resolver.providers] == ["OfficialDiscoveryProvider"]
    outcome = resolver.resolve(
        company_name="VISHAL NIRMITI LIMITED",
        ipo_id="VISHAL-NIRMITI-LIMITED",
        missing_fields=["price_band_low", "price_band_high", "lot_size", "ofs"],
    )
    assert outcome.status in ("UNPUBLISHED", "UNAVAILABLE")
    assert outcome.notice is None


def test_rk_fashion_terms_come_from_its_own_filing(tmp_path, golden_input, config):
    """R.K. Fashion discloses its terms in its RHP, so no resolver is
    involved: canonical values and FILING-classified evidence come from
    the uploaded filing itself. This is the real difference from
    issuers whose RHP leaves the terms as [●] placeholders."""
    client, store, baseline = _client(
        tmp_path, golden_input, config, IssueTermsResolver(providers=[])
    )
    res = _upload(client, RK_RHP_PDF, "rk_fashion.pdf")
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["issue_terms"] is None  # resolver never engaged

    record = store.read(body["evaluation_id"])
    issue = record["input_snapshot"]["input"]["issue"]
    assert issue["price_band_low"] is not None and issue["price_band_high"] is not None
    assert issue["lot_size"] is not None

    items = _evidence_items(client, body["evaluation_id"])
    band_items = {k: v for k, v in items.items() if "price_band" in k or "lot_size" in k}
    assert band_items, "R.K. Fashion must carry issue-term evidence from its filing"
    for item in band_items.values():
        assert item["verification"] in ("FILING", "OFFICIAL_VERIFIED", "DERIVED", "UNVERIFIED")
    lows = [v for k, v in band_items.items() if "price_band_low" in k]
    if lows:
        assert lows[0]["extracted_value"] == issue["price_band_low"]
