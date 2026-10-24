"""Peer row mapping and peer-value contract bounds (2026-10-19).

Observed Windows failure (audit trace ``ing-81fd285e5b8248c6``, HD Fire
Protect): the ingestion reached evaluation and failed ``PROCESSING_FAILED``
with ``SCHEMA_VIOLATION at peers/0/roe_pct: 26957.28 is greater than
maximum 10000`` (and peers/1 21700.34). Separately, the manual issue-term
interface recorded ``issue.ofs: entered 71231 vs existing 0`` (filing
extraction), which the operator confirmed.

Root-cause class (established by code trace and reproduction on the
repository's own reference filings -- NOT from magnitude alone):

- ``sections.extract_peers`` mapped peer cells by HARD-CODED POSITIONS of
  the R.K Fashion "Comparison of Accounting Ratios" layout
  (FV, CMP, EPS, Diluted EPS, P/E, RONW, NAV, PAT). Any other table
  layout silently puts the wrong financial field into ``pe``/``roe_pct``:
  replaying the Vishal Nirmiti listed-peers table (Closing price, FV,
  Revenue, EPS Basic, EPS Diluted, P/E, Net worth, RONW, NAV) produced
  ``roe_pct = 13.86`` -- a P/E cell -- and ``pb = 0.0``.
- The row tokenizer DROPPED non-numeric cells ([●], -, NA), so every
  later column shifted left and monetary/NAV cells land near ``roe_pct``:
  the exact signature of the reported 26957.28 / 21700.34 values.
- Out-of-bounds values then passed the entire ingestion (the full schema
  gate runs only at evaluation time) and detonated as an anonymous
  evaluation-time wall, after the operator had already entered terms.

Corrections (no schema relaxation, no clamping, no rewriting):

1. Peers are mapped only against a RECOGNISED header layout (anchored to
   the two reference documents above); placeholder cells keep their
   column; an unrecognised layout emits no peers (module B stays
   UNKNOWN); prose rows are not peers.
2. The peers array is validated against the SAME schema contract at
   ingestion time, with a diagnostic naming the peer and field.
"""

from __future__ import annotations

import copy
import io

import pytest
from fastapi.testclient import TestClient

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.issue_terms import IssueTermsResolver
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import (
    PresentationConfig,
    PresentationService,
)
from ipo_screening.schema_validation import validate_peer_records

PDF_BYTES = b"%PDF-1.4 peer-mapping-bounds"
EXPLANATION = "Broker IPO page values confirmed by the operator, 2026-10-19."

# Header + rows of the two established reference layouts.
RK_HEADER = (
    "Comparison of Accounting Ratios with Listed Industry Peers\n"
    "Face Value (Rs. Per share) CMP As on September 28, 2026 "
    "EPS# (Rs. Per share) Diluted EPS# (in Rs.) P/E Ratio# RONW# (%) "
    "NAV^ (Rs. Per share) PAT^ (Rs. in Lakhs)\n"
    "PEER GROUP\n"
)
RK_ROW = "2 Banaras Beads Limited\n10.00 119.20 2.69 2.69 44.31 3.08 87.38 177.46"

VISHAL_HEADER = (
    "6. Comparison of Accounting Ratios with listed industry peers\n"
    "The following is our peer group which has been determined on the basis of "
    "listed public companies comparable in the similar line of segments in which "
    "our Company operates and whose business segment in part or full may be "
    "comparable with that of our business, however, the same may not be exactly "
    "comparable in size or business portfolio on a whole with that of our business\n"
    "Set forth below is a comparison of our accounting ratios with our listed "
    "peer company as identified in accordance with the SEBI ICDR Regulations:\n"
    "Name of the company Closing price as on July 23, 2026 Face Value (in Rs.) "
    "Revenue from Operations as on Fiscal 2026 (Rs. in lakhs) EPS (in Rs.) "
    "P/E Ratio Net worth (Rs. lakhs) RONW (%) NAV (Per Equity Share) Basic Diluted\n"
)
VISHAL_ROWS = (
    # The issuer row sits inside the peer section with a prose paragraph
    # above it (as in the real filing) and [●] cells in its numeric line.
    "similar line of segments in which our Company operates and whose business "
    "segment in part or full may be comparable with that of our business however "
    "the same may not be exactly comparable in size or business portfolio on a "
    "whole with that of our business\n"
    "10.0 [●] 33867.73 12.61 12.61 [●] 8634.4 33.87 43.61\n"
    "Listed peers** GPT Infraprojects Limited\n"
    "114.24 10.0 128991.69 7.7 7.7 14.83 52775.35 18.25 41.77\n"
    "Indian Hume Pipe Company Limited\n"
    "371.4 2.0 130556.83 26.79 26.79 13.86 148435.98 9.51 281.76\n"
)


class _StubDoc:
    source_id = "SRC-TEST"


class _StubReader:
    def __init__(self, n: int) -> None:
        self.pages = [None] * n


def _extractor(page_text: str, page: int = 150) -> SectionExtractor:
    """SectionExtractor over a single cached page inside the peer scan range."""
    ex = SectionExtractor(_StubDoc(), _StubReader(200), text_cache={page: page_text})
    return ex


def _peers_from(page_text: str):
    ex = _extractor(page_text)
    raw = ex.extract_peers()
    return (raw[0].candidate_value if raw else [])


# ---------------------------------------------------------------------------
# A. Row mapping against recognised table layouts
# ---------------------------------------------------------------------------

def test_accounting_ratios_layout_maps_ronw_column():
    """The R.K Fashion layout pins (test_rk_fashion_reconciliation): the
    numeric row carries FV CMP EPS DilEPS P/E RONW NAV PAT."""
    peers = _peers_from(RK_HEADER + RK_ROW)
    assert len(peers) == 1
    p = peers[0]
    assert p["name"] == "Banaras Beads Limited"
    assert p["pe"] == 44.31
    assert p["roe_pct"] == 3.08
    assert p["pb"] == 1.36  # CMP/NAV = 119.20/87.38


def test_listed_peers_layout_maps_ronw_column():
    """The Vishal listed-peers layout maps to the golden peer values
    (fixtures/vishal_nirmiti/input.json: 14.83/2.73/18.25 and
    13.86/1.32/9.51). Positional mapping used to put P/E into roe_pct."""
    peers = _peers_from(VISHAL_HEADER + VISHAL_ROWS)
    assert len(peers) == 2
    gpt = next(p for p in peers if "GPT Infraprojects" in p["name"])
    ihp = next(p for p in peers if "Indian Hume Pipe" in p["name"])
    assert (gpt["pe"], gpt["roe_pct"], gpt["pb"]) == (14.83, 18.25, 2.73)
    assert (ihp["pe"], ihp["roe_pct"], ihp["pb"]) == (13.86, 9.51, 1.32)


def test_placeholder_cells_keep_their_columns():
    """[●]/NA placeholder cells occupy their column; later cells must not
    shift left (the demonstrated collapse defect). The RoNW column of a
    sparse accounting-ratios row stays the RoNW value."""
    row = "3 Acme Fire Systems Limited\n10.00 [●] 6.50 6.50 [●] 40.66 15.99 182.86"
    peers = _peers_from(RK_HEADER + row)
    assert len(peers) == 1
    p = peers[0]
    assert p["roe_pct"] == 40.66  # the RONW cell, not NAV 15.99 or PAT 182.86
    assert p["pe"] is None  # [●] P/E stays unknown, never a shifted cell


def test_unrecognised_layout_emits_no_peers():
    """A peer table whose declared columns this parser cannot map yields
    NO peers (module B stays UNKNOWN) instead of wrong-field values."""
    table = (
        "Comparison of Accounting Ratios with listed industry peers\n"
        "PEER GROUP\n"
        "Particulars Alpha Ltd Beta Ltd\n"
        "2 Some Company Limited 10.00 412.75 12.35 18.40 8.70 45.20 26957.28\n"
    )
    assert _peers_from(table) == []


def test_monetary_column_cells_never_land_in_roe_pct():
    """Retry of the observed failure class at the cause level: the reported
    magnitudes (26957.28 / 21700.34) as NET-WORTH (monetary) cells of the
    listed-peers layout must map into their own column; roe_pct takes the
    RONW column. This is the demonstrated mechanism: positional mapping of
    a mismatched layout put monetary cells into roe_pct."""
    rows = (
        # The issuer row resets name accumulation (as in the real table).
        "similar line of segments in which our Company operates and whose "
        "business segment in part or full may be comparable with that of our "
        "business\n"
        "10.0 [●] 33867.73 12.61 12.61 [●] 8634.4 33.87 43.61\n"
        "Alpha Fire Safety Limited\n"
        "412.75 10.0 26957.28 12.35 12.35 18.40 26957.28 12.40 45.20\n"
        "Beta Fire Safety Limited\n"
        "318.50 10.0 21700.34 9.85 9.85 16.20 21700.34 8.90 38.15\n"
    )
    peers = _peers_from(VISHAL_HEADER + rows)
    assert len(peers) == 2
    alpha = next(p for p in peers if "Alpha" in p["name"])
    beta = next(p for p in peers if "Beta" in p["name"])
    assert alpha["roe_pct"] == 12.40 and beta["roe_pct"] == 8.90
    # The monetary cells are simply not roe_pct; the rows are contract-valid.
    assert validate_peer_records(peers) == []


def test_prose_rows_are_not_peers():
    """Narrative text accumulated above a numeric line is not a company
    name (the real-filing garbage-peer defect: a 115-word sentence was
    emitted as a peer name)."""
    peers = _peers_from(
        VISHAL_HEADER
        + "similar line of segments in which our Company operates and whose "
        "business segment in part or full may be comparable with that of our "
        "business however the same may not be exactly comparable in size or "
        "business portfolio on a whole with that of our business as set forth "
        "below for the fiscal year indicated\n"
        + VISHAL_ROWS
    )
    assert all(len(p["name"].split()) <= 10 for p in peers)
    assert len(peers) == 2


# ---------------------------------------------------------------------------
# B. Peer-value contract bounds: reject early, name the peer and field
# ---------------------------------------------------------------------------

def _peer(name, **kw):
    base = {"name": name, "business_match": "partial", "listed_years": 15.0,
            "as_of": "2026-09-28"}
    base.update(kw)
    return base


def test_reported_out_of_contract_roe_values_are_named_and_rejected():
    """The two reported values (ing-81fd285e5b8248c6) fail the pct contract
    (-1000..10000) and the diagnostic names each peer and field."""
    peers = [
        _peer("Alpha Fire Safety Limited", roe_pct=26957.28),
        _peer("Beta Fire Safety Limited", roe_pct=21700.34),
    ]
    findings = validate_peer_records(peers)
    assert [f.location for f in findings] == ["peers/0/roe_pct", "peers/1/roe_pct"]
    assert all(f.code == "SCHEMA_VIOLATION" for f in findings)
    assert "26957.28" in findings[0].message and "maximum" in findings[0].message
    assert "10000" in findings[0].message
    assert "Alpha Fire Safety Limited" in findings[0].message
    assert "Beta Fire Safety Limited" in findings[1].message


def test_percent_bounds_boundary_values():
    """In-bound extremes are accepted untouched (no clamping); the exact
    schema bounds (-1000..10000) are the only authority."""
    ok = [
        _peer("A", roe_pct=9999.9),
        _peer("B", roe_pct=-999.0),
        _peer("C", roe_pct=10000.0),
        _peer("D", roe_pct=-1000.0),
        _peer("E", roe_pct=None),
    ]
    assert validate_peer_records(ok) == []
    bad = [
        _peer("F", roe_pct=10000.01),
        _peer("G", roe_pct=-1000.01),
        _peer("H", roe_pct="26957.28"),  # numeric string is not a number
    ]
    findings = validate_peer_records(bad)
    assert [f.location for f in findings] == [
        "peers/0/roe_pct", "peers/1/roe_pct", "peers/2/roe_pct",
    ]
    assert "F" in findings[0].message and "G" in findings[1].message


def test_valid_peers_pass_the_ingestion_gate(tmp_path, monkeypatch, golden_input):
    """The early gate must not disturb governed valid flows."""

    def factory():
        doc = copy.deepcopy(golden_input)
        doc["peers"] = [_peer("Peer Limited", pe=12.5, pb=1.4, roe_pct=9.5)]
        return doc

    monkeypatch.setattr(
        DocumentExtractor, "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (factory(), {}),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations", config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    client = TestClient(create_app(service), base_url="http://127.0.0.1:8000",
                        headers={"Origin": "http://127.0.0.1:8000"})
    res = client.post(
        "/api/v1/ingest/manual-terms",
        files={"file": ("filing.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
        data={"mode": "final"},
    )
    assert res.status_code == 201, res.text


def test_ingest_rejects_out_of_contract_peers_early_with_actionable_diagnostic(
    tmp_path, monkeypatch, golden_input
):
    """The observed failure class is now rejected at ingestion time, naming
    the peer and field, before any evaluation-time schema wall."""

    def factory():
        doc = copy.deepcopy(golden_input)
        doc["peers"] = [
            _peer("Alpha Fire Safety Limited", roe_pct=26957.28),
            _peer("Beta Fire Safety Limited", roe_pct=21700.34),
        ]
        return doc

    monkeypatch.setattr(
        DocumentExtractor, "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (factory(), {}),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations", config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    client = TestClient(create_app(service), base_url="http://127.0.0.1:8000",
                        headers={"Origin": "http://127.0.0.1:8000"})
    res = client.post(
        "/api/v1/ingest/manual-terms",
        files={"file": ("filing.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
        data={"mode": "final"},
    )
    assert res.status_code == 400, res.text
    body = res.json()
    message = body.get("message") or body.get("detail") or ""
    assert "peers/0/roe_pct" in message
    assert "peers/1/roe_pct" in message
    assert "Alpha Fire Safety Limited" in message
    assert "Beta Fire Safety Limited" in message
    assert "never clamped or substituted" in message
    # Nothing was evaluated or persisted under a false successful state.
    assert "evaluation_id" not in body
    assert service.eval_store.list_evaluations() == []


# ---------------------------------------------------------------------------
# C. Phase 4 -- issue-term governance: the confirmed OFS override
# ---------------------------------------------------------------------------

def test_confirmed_ofs_override_stays_manual_entry_and_unverified(
    tmp_path, monkeypatch, golden_input
):
    """ing-81fd285e5b8248c6 Phase 4: the filing extracted issue.ofs = 0
    (NIL-OFS) and the operator entered 71231. The confirmed manual value
    replaces the extracted one, keeps MANUAL_ENTRY provenance, is never
    official-verified, and the conflict + confirmation are recorded."""

    def factory():
        doc = copy.deepcopy(golden_input)
        for field in ("price_band_low", "price_band_high", "lot_size", "fresh_issue"):
            doc["issue"][field] = None
        doc["issue"]["ofs"] = 0.0  # filing-established NIL-OFS
        return doc

    monkeypatch.setattr(
        DocumentExtractor, "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (factory(), {}),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations", config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    client = TestClient(create_app(service), base_url="http://127.0.0.1:8000",
                        headers={"Origin": "http://127.0.0.1:8000"})

    def post(confirm):
        data = {
            "mode": "final",
            "price_band_low": "208", "price_band_high": "220",
            "lot_size": "68", "ofs": "71231", "fresh_issue": "14500",
            "explanation": EXPLANATION,
        }
        if confirm:
            data["confirm_conflicts"] = "true"
        return client.post(
            "/api/v1/ingest/manual-terms",
            files={"file": ("filing.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
            data=data,
        )

    # 1. The conflict is surfaced, not silently resolved.
    res = post(confirm=False)
    assert res.status_code == 409, res.text
    detail = res.json()
    assert detail["code"] == "ISSUE_TERM_CONFLICT"
    ofs_conflict = next(c for c in detail["conflicts"] if c["field"] == "issue.ofs")
    assert ofs_conflict["existing_value"] == 0.0
    assert ofs_conflict["existing_origin"] == "FILING_EXTRACTION"
    assert ofs_conflict["manual_value"] == 71231.0

    # 2. Explicit confirmation applies the manual value.
    res = post(confirm=True)
    assert res.status_code == 201, res.text
    body = res.json()
    record = service.eval_store.read(body["evaluation_id"])
    issue = record["input_snapshot"]["input"]["issue"]
    assert issue["ofs"] == 71231.0

    # 3. Provenance: MANUAL_ENTRY and unverified on every term; the
    #    confirmed field is never labelled official-verified.
    for field in ("price_band_low", "price_band_high", "lot_size", "ofs", "fresh_issue"):
        item = _spec_for(record, field)
        assert item["extraction_method"] == "MANUAL_ENTRY"
        assert item["source_id"] == "SRC-MANUAL-ENTRY"
        assert not item.get("verified")
        assert EXPLANATION in (item.get("note") or "")

    manual = body["issue_terms"]["manual_entry"]
    assert manual["overridden_by_verified"] == []
    assert body["issue_terms"].get("verified") is False

    # 4. The audit trace records the submission, the conflict
    #    confirmation, the accepted manual entry, and the completed
    #    evaluation and persistence.
    hist = client.get(f"/api/v1/ingestions/{body['ingestion_id']}")
    assert hist.status_code == 200
    events = [(e["stage"], e["event_type"], e["status"]) for e in hist.json()["events"]]
    assert ("term_resolution", "manual_submission", "SUCCEEDED") in events
    assert ("term_resolution", "manual_entry", "SUCCEEDED") in events
    assert ("evaluation", "completed", "SUCCEEDED") in events
    assert ("persistence", "completed", "SUCCEEDED") in events
    accepted = [e for e in hist.json()["events"] if e["event_type"] == "manual_entry"][0]
    assert accepted["details"]["values"]["ofs"] == 71231.0


def _spec_for(record, field):
    items = (record.get("evidence") or {}).get("evidence") or []
    if isinstance(items, dict):
        evidence = items
    else:
        evidence = {item.get("evidence_id"): item for item in items}
    hyphen = field.replace("_", "-")
    for candidate in (f"EV-issue.{field}", f"EV-issue-{hyphen}", f"EV-{hyphen}"):
        if candidate in evidence:
            return evidence[candidate]
    raise KeyError(field)


def _peers_from_pages(pages):
    ex = SectionExtractor(
        _StubDoc(), _StubReader(200), text_cache={p: t for p, t in pages.items()}
    )
    raw = ex.extract_peers()
    return (raw[0].candidate_value if raw else [])


JIO_PEER_TABLE = (
    "Particulars Face \nvalu\ne \n(₹) \nRevenue \nfrom \noperations \nfor Fiscal \n"
    "2026 \n(in ₹ million) \nEPS \n(Basic) \n(₹) \nEPS \n(Diluted) \n(₹) \n"
    "P/E Return on \nAverage \nNet Worth \n(%) \nNAV per \nEquity \nShare (₹) \n"
    "The Company* 10 1,468,853 33.63 33.59 [●]# 9.42%^ 373.66^ \n"
    "Peer Companies \n"
    "Bharti Airtel Limited 5 2,109,728(1) 45.96(3) 44.37(3) 40.71 (4) 20.32%(5) 244.60(6) \n"
    "Vodafone Idea Limited 10 448,730(2) 3.21(3) 3.21(3) 3.99 (4) NM$ (3.30)(7) \n"
)
JIO_PEER_NOTE = (
    "(4) P/E ratio of peer companies has been computed based on the closing "
    "market price of the equity shares of respective peer companies on NSE "
    "as on October 13, 2026, divided by diluted EPS for fiscal ended "
    "March 31, 2026."
)


def test_jio_peer_companies_layout_maps_pe_and_ronw_only():
    """The Jio RHP layout (Face value, Revenue, EPS Basic, EPS Diluted, P/E,
    Return on Average Net Worth, NAV) maps each column to its own field.
    There is no CMP column, so no P/B is invented."""
    peers = _peers_from_pages({150: JIO_PEER_TABLE, 151: JIO_PEER_NOTE})
    assert [p["name"] for p in peers] == ["Bharti Airtel Limited", "Vodafone Idea Limited"]
    bharti, vi = peers
    assert (bharti["pe"], bharti["roe_pct"]) == (40.71, 20.32)
    assert (vi["pe"], vi["roe_pct"]) == (3.99, None)  # NM is not a number
    assert bharti["pb"] is None and vi["pb"] is None
    # The valuation date is the filing's, never a 2026-09-28 default.
    assert bharti["as_of"] == vi["as_of"] == "2026-10-13"
    # Listing history is not disclosed, so it is not asserted as 15 years.
    assert bharti["listed_years"] is None


def test_short_data_row_never_leaks_into_the_next_peer_name():
    """A row with too few numeric cells is an unmappable data row.  Its
    numbers must not become the next peer's name (the demonstrated defect:
    '.75 10.0 26957.28 12.35 Beta Fire Safety Limited')."""
    rows = (
        "412.75 10.0 26957.28 12.35\n"
        "Beta Fire Safety Limited\n"
        "318.50 10.0 21700.34 9.85 9.85 16.20 21700.34 8.90 38.15\n"
    )
    peers = _peers_from(VISHAL_HEADER + rows)
    assert len(peers) == 1
    assert peers[0]["name"] == "Beta Fire Safety Limited"
    assert peers[0]["pe"] == 16.2  # the row's own P/E, not a shifted cell


def test_missing_numeric_cell_row_emits_no_peer():
    """A blank cell that vanishes in text extraction shortens the row; the
    row is rejected rather than shifting a later value into ROE."""
    rows = "Alpha Fire Safety Limited\n412.75 10.0 26957.28 12.35 12.35 18.40 26957.28 12.40\n"
    assert _peers_from(VISHAL_HEADER + rows) == []


def test_absent_valuation_date_is_not_defaulted():
    """With no disclosed valuation date the peer's currency is unknown; a
    fixed 2026-09-28 default must never be substituted."""
    table = VISHAL_HEADER.replace(
        "Closing price as on July 23, 2026", "Closing price"
    ) + VISHAL_ROWS
    peers = _peers_from(table)
    assert [p["name"].split()[0] for p in peers] == ["GPT", "Indian"]
    assert {p["as_of"] for p in peers} == {None}


def test_blank_and_non_numeric_cells_keep_their_columns():
    """An empty/``NA`` revenue cell and an ``NM`` RONW cell occupy their own
    columns.  Neither shortens the row nor shifts a later value into RONW
    (the demonstrated placeholder-collapse defect, in its ``NA``/``NM``
    spelling)."""
    rows = (
        "Alpha Fire Safety Limited\n"
        "114.24 10.0 NA 7.7 7.7 14.83 52775.35 18.25 41.77\n"
        "Beta Fire Safety Limited\n"
        "371.4 2.0 130556.83 26.79 26.79 13.86 148435.98 NM 281.76\n"
    )
    peers = _peers_from(VISHAL_HEADER + rows)
    assert [p["name"].split()[0] for p in peers] == ["Alpha", "Beta"]
    alpha, beta = peers
    assert (alpha["pe"], alpha["roe_pct"]) == (14.83, 18.25)
    assert alpha["pb"] == pytest.approx(114.24 / 41.77, abs=0.01)
    assert beta["pe"] == 13.86
    assert beta["pb"] == pytest.approx(371.4 / 281.76, abs=0.01)
    assert beta["roe_pct"] is None  # NM stays in the RONW column


def test_valid_peer_ingestion_reaches_a_scored_valuation(
    tmp_path, monkeypatch, golden_input
):
    """A contract-valid peer set survives ingestion, is snapshotted as VALID,
    and reaches evaluation: ``pe_vs_peers`` is SCORED (a real zero), not
    UNKNOWN.  This is the positive control for the rejection tests above."""

    def factory():
        doc = copy.deepcopy(golden_input)
        doc["peers"] = [_peer("Peer Limited", pe=12.5, pb=1.4, roe_pct=9.5)]
        return doc

    monkeypatch.setattr(
        DocumentExtractor, "extract_from_pdf",
        lambda self, pdf_path=None, allow_fixture_fallbacks=False: (factory(), {}),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations", config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[]),
    )
    service = PresentationService(cfg)
    client = TestClient(create_app(service), base_url="http://127.0.0.1:8000",
                        headers={"Origin": "http://127.0.0.1:8000"})
    res = client.post(
        "/api/v1/ingest/manual-terms",
        files={"file": ("filing.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
        data={"mode": "final", "price_band_low": "208", "price_band_high": "220",
              "lot_size": "68", "ofs": "3300", "fresh_issue": "14500",
              "explanation": EXPLANATION, "confirm_conflicts": "true"},
    )
    assert res.status_code == 201, res.text
    record = service.eval_store.read(res.json()["evaluation_id"])
    assert record["peer_snapshot"]["valid_count"] == 1
    assert record["peer_snapshot"]["observations"][0]["status"] == "VALID"
    module_b = next(m for m in record["score"]["modules"] if m["module_id"] == "B")
    pe = next(c for c in module_b["criteria"] if c["criterion_id"] == "pe_vs_peers")
    # 220 / 9.46 = 23.26 issuer P/E vs a 12.5 peer P/E -> +86 %, the
    # "richer than peers" band: a scored zero, not an unknown.
    assert pe["state"] == "SCORED"
    assert pe["score"] == 0.0
