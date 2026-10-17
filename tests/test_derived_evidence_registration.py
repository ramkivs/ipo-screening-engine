"""Derived-evidence registration + seller-quantity evidence (2026-10-17).

Confirmed defect: enrichment registered derived evidence specifications
under ``SRC-DERIVED``, but that source was never declared in the
canonical ``_sources`` manifest, so ``canonical_input.build_registry``
skipped the specifications (``EVIDENCE_SOURCE_UNREGISTERED``) and the
persisted Evidence Explorer artifact had no cards for
``issue.fresh_shares``, ``issue.ofs``, ``issue.post_issue_shares`` or
``issue.post_issue_eps`` -- even though the values were present in the
input snapshot. Separately, the seller list showed the seller's identity
but never the seller-specific ``shares_sold`` quantity.

These tests exercise the actual persisted-artifact path used by the
Evidence Explorer (service -> store -> ``get_evaluation_evidence``),
using the real Vishal RHP and controlled transport (which proves
channel mechanics, not live SEBI retrieval).
"""

from __future__ import annotations

from pathlib import Path

from conftest import REPO_ROOT
from ipo_screening.issue_terms import HttpProspectusProvider, IssueTermsResolver
from ipo_screening.presentation.service import PresentationConfig, PresentationService

SEBI_URL = "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"
VISHAL_RHP_PDF = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"

PROSPECTUS_TEXT = """Prospectus
Dated: October 05, 2026
100% Book Built Offer
VISHAL NIRMITI LIMITED
CORPORATE IDENTITY NUMBER: U01122MH1994PLC185445
LISTING
The Equity Shares issued through the Red Herring Prospectus and this Prospectus are proposed to be
listed on the National Stock Exchange of India Limited and BSE Limited.
"Price Band" Price band of a minimum price of Rs 208 per Equity Share (i.e., the Floor Price) and the
maximum price of Rs 220 per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.
"""


def _ingest(tmp_path):
    provider = HttpProspectusProvider(
        {"Vishal Nirmiti Limited": SEBI_URL},
        fetcher=lambda u: PROSPECTUS_TEXT.encode(),
    )
    cfg = PresentationConfig(
        store_root=tmp_path / "evaluations",
        config_dir=REPO_ROOT / "config",
        issue_terms_resolver=IssueTermsResolver(providers=[provider]),
    )
    service = PresentationService(cfg)
    resp = service.ingest_document(
        file_bytes=VISHAL_RHP_PDF.read_bytes(), filename=VISHAL_RHP_PDF.name, mode="final"
    )
    return service, resp


def _items(service, evaluation_id):
    evidence = service.get_evaluation_evidence(evaluation_id)
    assert evidence is not None
    return {item.evidence_id: item for item in evidence.items}, evidence


def test_derived_evidence_is_registered_and_persisted(tmp_path):
    service, resp = _ingest(tmp_path)
    record = service.eval_store.read(resp.evaluation_id)

    # No valid SRC-DERIVED specification is skipped any more.
    warnings = record["validation"]["warnings"]
    assert not [
        w for w in warnings if w.get("code") == "EVIDENCE_SOURCE_UNREGISTERED"
    ], warnings

    # The derived source is declared in the persisted source manifest.
    source_ids = {s.get("source_id") for s in record["evidence"]["sources"]}
    assert "SRC-DERIVED" in source_ids
    derived_source = next(
        s for s in record["evidence"]["sources"] if s.get("source_id") == "SRC-DERIVED"
    )
    assert derived_source.get("source_type") == "DERIVED"

    items, _ = _items(service, resp.evaluation_id)
    issue = record["input_snapshot"]["input"]["issue"]

    expected = {
        "EV-issue.fresh_shares": (6590909, "equity shares", "fresh_issue"),
        "EV-issue.ofs": (3300.0, None, "seller_shares"),
        "EV-issue.post_issue_shares": (26390909, "equity shares", "pre_issue_shares"),
        "EV-issue.post_issue_eps": (9.46, None, "pat"),
    }
    for evidence_id, (value, unit, formula_fragment) in expected.items():
        assert issue[{"EV-issue.fresh_shares": "fresh_shares", "EV-issue.ofs": "ofs",
                      "EV-issue.post_issue_shares": "post_issue_shares",
                      "EV-issue.post_issue_eps": "post_issue_eps"}[evidence_id]] == value
        item = items[evidence_id]
        assert item.extracted_value == value, item
        assert item.verification == "DERIVED"  # never filing/official-quoted
        assert item.extraction_method == "DERIVED"
        assert item.source == "SRC-DERIVED"
        assert item.quote is None  # derived values are not dressed as quotations
        assert formula_fragment in (item.note or "")
        if unit:
            assert item.unit == unit


def test_seller_specific_ofs_quantity_evidence(tmp_path):
    service, resp = _ingest(tmp_path)
    items, _ = _items(service, resp.evaluation_id)

    # Seller identity from the filing (list-level evidence, summary only).
    seller_list = items["EV-issue-ofs_sellers"]
    assert seller_list.verification == "FILING"
    assert seller_list.extracted_value is None
    assert "VAMAN PRESTRESSING COMPANY PRIVATE LIMITED" in (seller_list.value_summary or "")

    # Seller-specific quantity is its own persisted evidence record,
    # filing-backed, distinct from the derived aggregate.
    quantity = items["EV-issue.ofs_sellers[0].shares_sold"]
    assert quantity.extracted_value == 1500000
    assert quantity.unit == "equity shares"
    assert quantity.verification == "FILING"
    assert quantity.source.startswith("RHP-FILING-")
    assert "shares_sold" in quantity.evidence_id

    aggregate = items["EV-issue.ofs"]
    assert aggregate.extracted_value == 3300.0
    assert aggregate.verification == "DERIVED"  # derived aggregate, not quoted
    assert aggregate.source == "SRC-DERIVED"
