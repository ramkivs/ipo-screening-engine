"""Reading defects found by scoring the Paras Healthcare RHP end to end (2026-10-26).

Every case below pins one *reading* rule that the shared extractor got wrong on
a real filing, using a synthetic page that reproduces the filing's typography
rather than the filing itself (the document is pinned separately in
``test_paras_evidence_regression.py``).  None of these corrections changes a
weight, a threshold, a penalty, a criterion definition or a knockout.

The theme is the same one behind A23 / D-5 / Step 4 Area B(i): a value the
filing does not state must stay **UNKNOWN**, and a value it does state must be
read from the filing's own words rather than from a caption the engine happens
to expect.  Two mirror-image defects are covered:

* a section that is present but unread (the objects schedule, the supplier
  table, the industry forecast, the peer table) -- the criterion went UNKNOWN
  or scored zero without evidence; and
* a field that was never read but *defaulted* to the favourable answer (the
  pledge, the lock-in, "no early unlock", the board's independence) -- the
  criterion was scored from nothing at all.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.extraction.interfaces import SourceDocument
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.extraction.toc import TOCRouter


def _section(pages: dict[int, str], page_count: int | None = None) -> SectionExtractor:
    extractor = SectionExtractor.__new__(SectionExtractor)
    extractor.page_count = page_count if page_count is not None else max(pages)
    extractor.doc = SimpleNamespace(source_id="RHP-TEST-0001")
    extractor._text_cache = {}
    extractor.extract_page_text = lambda p: pages.get(p, "")
    return extractor


def _fields(extractions) -> dict:
    out = {}
    for ex in extractions:
        out.setdefault(ex.field_path, ex)
    return out


# ---------------------------------------------------------------------------
# 1. Table of contents: a page number split by justification
# ---------------------------------------------------------------------------


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReader:
    def __init__(self, pages: list[str]) -> None:
        self.pages = [_FakePage(t) for t in pages]


def test_justified_toc_page_numbers_route_their_sections():
    """`OBJECTS OF THE OFFER ..... 12 4` is page 124, not an unparsed row.

    The three sections lost this way on Paras (objects of the offer, industry
    overview, basis for offer price) each fell back to a fixed page window that
    missed them, so every reader behind them read the wrong pages.
    """
    toc = "\n".join(
        [
            "TABLE OF CONTENTS",
            "SECTION I: GENERAL ................................ 1",
            "CAPITAL STRUCTURE ................................ 106",
            "OBJECTS OF THE OFFER ............................. 12 4",
            "BASIS FOR OFFER PRICE ............................ 14 5",
            "INDUSTRY OVERVIEW ................................ 1 84",
            "OUR BUSINESS ..................................... 258",
        ]
    )
    reader = _FakeReader([toc] + ["page"] * 300)
    router = TOCRouter.from_pdf(reader)

    assert router.entries["objects_of_the_offer"].printed_page == 124
    assert router.entries["basis_for_offer_price"].printed_page == 145
    assert router.entries["industry_overview"].printed_page == 184
    assert router.entries["capital_structure"].printed_page == 106


# ---------------------------------------------------------------------------
# 2. Objects of the offer: the schedule is a table, not a caption
# ---------------------------------------------------------------------------
#
# Paras prints the requirement of funds and the deployment schedule on the same
# page, each row captioned in ordinary ICDR wording that the keyword scan did
# not recognise, and follows the schedule with prose paragraphs.

PARAS_OBJECTS = {
    129: "\n".join(
        [
            "The Net Proceeds are proposed to be utilised in the following manner:",
            "1. Prepayment or scheduled re-payment, in full or part, of certain outstanding",
            "borrowings availed by our Company",
            "3,209.00",
            "2. Investment in our wholly owned Subsidiary, PMHPL (which also operates our",
            "hospital in Srinagar), for repayment/prepayment of borrowings",
            "541.00",
            "3. General corporate purposes*# [\u25cf]",
            "Requirement of funds",
            "(in \u20b9 million) Particulars Total estimated amount",
            "1. Prepayment or scheduled re-payment, in full or part, of certain outstanding",
            "borrowings availed by our Company",
            "3,209.00",
            "2. Investment in our wholly owned Subsidiary, PMHPL",
            "541.00",
            "3. General corporate purposes*# [\u25cf]",
            "Net Proceeds 3,750.00",
            "The requirement and deployment of funds indicated above are based on the current",
            "business plan and internal management estimates, and are not a forecast.",
        ]
    ),
}


def test_objects_rows_are_read_by_row_not_by_caption():
    fields = _fields(_section(PARAS_OBJECTS).extract_objects_of_offer({"objects_of_the_offer": (129, 145)}))
    schedule = fields["use_of_proceeds"].candidate_value
    assert schedule[0] == {"category": "debt_repayment", "amount": 3209.0}
    # An equity investment in a group company retires none of the issuer's own
    # debt: `other`, never `debt_repayment`.
    assert schedule[1]["category"] == "other" and schedule[1]["amount"] == 541.0
    assert schedule[2]["category"] == "gcp" and schedule[2]["amount"] is None
    assert schedule[2]["undisclosed_marker"] == "[\u25cf]"


def test_a_schedule_printed_twice_is_not_summed():
    """The requirement-of-funds and deployment tables state the same 3,209.00."""
    fields = _fields(_section(PARAS_OBJECTS).extract_objects_of_offer({"objects_of_the_offer": (129, 145)}))
    amounts = [u["amount"] for u in fields["use_of_proceeds"].candidate_value]
    assert amounts.count(3209.0) == 1
    assert sum(a for a in amounts if a) == 3750.0  # 3,209 + 541, never 6,418 + 1,082


def test_a_row_stops_at_its_amount_so_prose_is_not_absorbed():
    fields = _fields(_section(PARAS_OBJECTS).extract_objects_of_offer({"objects_of_the_offer": (129, 145)}))
    quote = fields["use_of_proceeds[0].amount"].quote
    assert "3,209.00" in quote
    assert "internal management estimates" not in quote


def test_objects_quote_is_the_filings_own_row():
    """The top-level evidence must be quoted from the filing, not summarised."""
    fields = _fields(_section(PARAS_OBJECTS).extract_objects_of_offer({"objects_of_the_offer": (129, 145)}))
    top = fields["use_of_proceeds"]
    assert top.quote_is_processing is False
    assert "Prepayment or scheduled re-payment" in top.quote


def test_direct_prepayment_of_a_subsidiarys_borrowings_is_still_debt_repayment():
    """Jio: "Prepayment ... of certain outstanding borrowings availed by the
    Material Subsidiary, RJIL" -- the object is retiring debt, and the
    borrowing's location does not change what the proceeds buy."""
    pages = {
        116: "\n".join(
            [
                "Proposed schedule of implementation and deployment of Net Proceeds",
                "1. Prepayment, in full or in part , of certain outstanding borrowings availed by the",
                "Material Subsidiary, RJIL 275,000 275,000",
                "2. General corporate purposes* [\u25cf] [\u25cf]",
                "The requirement and deployment of funds indicated above are based on the current",
                "business plan.",
            ]
        )
    }
    fields = _fields(_section(pages).extract_objects_of_offer({"objects_of_the_offer": (116, 125)}))
    schedule = {u["category"]: u for u in fields["use_of_proceeds"].candidate_value}
    assert schedule["debt_repayment"]["amount"] == 275000.0
    assert schedule["gcp"]["undisclosed_marker"] == "[\u25cf]"


# ---------------------------------------------------------------------------
# 3. Supplier concentration: "Top five suppliers", latest fiscal column first
# ---------------------------------------------------------------------------

SUPPLIER_TABLE = {
    61: "\n".join(
        [
            "Our top five suppliers",
            "(in \u20b9 million) Particulars Fiscal 2026 Fiscal 2025 Fiscal 2024",
            "Top five suppliers 1,140.95 21.94 % 1,232.05 26.95% 670.30",
            "Top ten suppliers 1,631.00 31.37 % 1,700.00 37.20% 900.00",
            "Top five customers 1,000.00 11.11 % 900.00 12.00% 800.00",
            "Note: percentages are of revenue from operations",
        ]
    ),
    62: "Prose page with no table at all.",
}


def test_word_form_top_five_supplier_row_is_read():
    fields = _fields(_section(SUPPLIER_TABLE).extract_business({"our_business": (61, 62)}))
    assert fields["business.top5_supplier_pct"].candidate_value == 21.94
    assert fields["business.top5_supplier_pct"].page == 61
    assert fields["business.top5_supplier_pct"].quote_is_processing is False


def test_the_first_amount_percent_pair_is_the_latest_fiscal_year():
    """Columns run newest-first: 21.94% (FY2026), not 26.95% (FY2025)."""
    fields = _fields(_section(SUPPLIER_TABLE).extract_business({"our_business": (61, 62)}))
    assert fields["business.top5_supplier_pct"].candidate_value != 26.95


def test_without_a_fiscal_column_header_no_concentration_is_read():
    """A row of numbers with no stated years cannot be assigned to a period."""
    pages = {
        61: "\n".join(
            [
                "Top five suppliers 1,140.95 21.94 % 1,232.05 26.95%",
                "Top five customers 1,000.00 11.11 % 900.00 12.00%",
            ]
        )
    }
    fields = _fields(_section(pages).extract_business({"our_business": (61, 61)}))
    assert "business.top5_supplier_pct" not in fields
    assert "business.top5_customer_pct" not in fields


# ---------------------------------------------------------------------------
# 4. Industry forecast: a disclosed range, its period, and its source
# ---------------------------------------------------------------------------

FORECAST_PAGE = (
    "The India healthcare delivery market is expected to grow at a CAGR of 10 to 12% "
    "between fiscals 2025 and 2030, driven by rising private participation."
)
REPORT_DEF_PAGE = (
    "We have commissioned and paid for the \u201cCRISIL Report\u201d, an Industry Report titled "
    "\u201cAssessment of Healthcare delivery sector in India\u201d, dated September, 2026, "
    "exclusively for the purposes of this Red Herring Prospectus."
)


def test_disclosed_forecast_range_records_its_lower_bound_with_period_and_source():
    pages = {6: REPORT_DEF_PAGE, 204: FORECAST_PAGE}
    fields = _fields(_section(pages).extract_business({"industry_overview": (204, 204)}))
    assert fields["business.industry_cagr_pct"].candidate_value == 10.0
    assert "10 to 12" in fields["business.industry_cagr_pct"].quote
    assert fields["business.industry_forecast_period"].candidate_value == "FY2025-FY2030"
    # `industry_scope` is a schema enum; the market name belongs in the locator.
    assert fields["business.industry_scope"].candidate_value == "india"
    assert "healthcare delivery" in fields["business.industry_scope"].locator
    assert fields["business.industry_source"].candidate_value.startswith("CRISIL Report")


def test_a_forecast_without_a_defined_report_is_not_used():
    """The metric needs value, scope, period and source together; a range whose
    publisher is never named cannot supply the fourth."""
    pages = {204: FORECAST_PAGE}
    fields = _fields(_section({**pages}).extract_business({"industry_overview": (204, 204)}))
    cagr = fields.get("business.industry_cagr_pct")
    assert cagr is None or cagr.candidate_value != 10.0


# ---------------------------------------------------------------------------
# 5. Capital structure: promises stated with different grammar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        "none of the Equity Shares held by our Promoter are pledged.",
        "None of the Equity Shares held by our Promoters is pledged.",
        "As on the date of this Red Herring Prospectus, none of the Equity Shares held by our Promoter are pledged.",
    ],
)
def test_a_no_pledge_statement_is_read_in_singular_or_plural(sentence):
    pages = {114: sentence}
    fields = _fields(_section(pages).extract_capital_structure({"capital_structure": (114, 114)}))
    pledge = fields["capital_structure.promoter_pledge_pct"]
    assert pledge.candidate_value == 0.0
    assert pledge.page == 114
    assert pledge.quote_is_processing is False
    assert "pledged" in pledge.quote


@pytest.mark.parametrize(
    "sentence",
    [
        "The Equity Shares held by our Promoter and locked in for a period of three years.",
        "The Promoter's Contribution is locked in for a period of 18 months.",
        "The Equity Shares held by our Promoter are locked-in for 3 years.",
    ],
)
def test_a_lock_in_statement_is_read_in_each_standard_form(sentence):
    pages = {116: sentence}
    fields = _fields(_section(pages).extract_capital_structure({"capital_structure": (116, 116)}))
    lockin = fields["capital_structure.promoter_lockin_in_place"]
    assert lockin.candidate_value is True
    assert lockin.page == 116
    assert lockin.quote_is_processing is False


def test_promoter_pre_holding_is_read_from_the_prose_percentage():
    pages = {
        111: (
            "Our Promoter, Dr. Dharminder Kumar Nagar, holds 73,519,238 Equity Shares, "
            "equivalent to 72.80% of the issued, subscribed and paid-up Equity Share capital."
        )
    }
    fields = _fields(_section(pages).extract_capital_structure({"capital_structure": (111, 111)}))
    pre = fields["capital_structure.promoter_pre_pct"]
    assert pre.candidate_value == 72.8
    assert "72.80%" in pre.quote


# ---------------------------------------------------------------------------
# 6. Governance: the auditor's letter, and a board counted in words
# ---------------------------------------------------------------------------


def test_auditor_continuity_is_read_from_the_auditors_own_letter():
    pages = {
        99: (
            "There has been no change in our statutory auditors in the last three years "
            "preceding the date of this Red Herring Prospectus."
        )
    }
    fields = _fields(_section(pages).extract_governance({"restated_financials": (99, 99)}))
    changed = fields["governance.auditor_changed_3y"]
    assert changed.candidate_value is False
    assert changed.page == 99
    assert "no change in our statutory auditors" in changed.quote


def test_board_composition_counts_are_read_in_words():
    pages = {
        337: (
            "As on the date of this Red Herring Prospectus, we have seven Directors on our "
            "Board, of whom, two are Executive Directors, five are Non-Executive Directors, "
            "of which three are Independent Directors (including one woman Independent Director)."
        )
    }
    fields = _fields(_section(pages).extract_governance({"our_management": (337, 337)}))
    majority = fields["governance.board_independent_majority"]
    assert majority.candidate_value is False  # 3 of 7
    assert majority.page == 337
    assert majority.quote_is_processing is False
    assert "seven Directors" in majority.quote


def test_an_unread_board_is_not_reported_as_independent_or_not():
    """Neither answer may be emitted without the composition sentence: the
    previous code emitted False with a quote of its own making, which cost the
    issuer a scored point for a section nobody read."""
    fields = _fields(_section({1: "Our Management is described elsewhere."}).extract_governance({}))
    assert "governance.board_independent_majority" not in fields


# ---------------------------------------------------------------------------
# 7. Peers: a twelve-column table whose rows wrap mid-number
# ---------------------------------------------------------------------------

PEER_TABLE = {
    150: "\n".join(
        [
            "F. Comparison of accounting ratios with Listed Industry Peers",
            "Company",
            "Face value per equity share (\u20b9)",
            "Enterprise Value as on October 5, 2026(\u20b9 million)",
            "Closing Price as on October 5, 2026 per equity share (\u20b9)",
            "Revenue from Operations for Fiscal 2026 (\u20b9 Million)",
            "EBITDA for Fiscal 2026 (\u20b9 Million)",
            "EPS (Basic) (\u20b9)",
            "EPS (Diluted) (\u20b9)",
            "P/E EV/EBITDA Net Worth",
            "Return on Net Worth (%)",
            "Net Asset Value per Equity Share (\u20b9)",
            "Paras Healthcare Limited(1) 1 [\u25cf] [\u25cf] 16,059.52 3,355.77 4.34 4.34 [\u25cf]* [\u25cf]* 3,949.41 12.98% 39.11",
            "Listed Peers",
            "Aster DM Quality",
            "Care Limited^",
            "10 366,964.63 691.00 46,432.20 9,010.00 7.53 7.52 91.89 40.73 45,758.60 9.70% 88.32",
            "Apollo Hospitals",
            "Enterprise",
            "Limited (\u201cAHEL\u201d)",
            "5 1,228,529.3",
            "9",
            "8,010.00 2,52,285.00 37,693.00 135.04 134.94 59.36 32.59 94,801.00 21.95% 657.58",
            "Note: All financial information is on a consolidated basis.",
        ]
    )
}


def test_a_wrapping_twelve_column_peer_table_is_read():
    fields = _fields(_section(PEER_TABLE).extract_peers({"basis_for_offer_price": (145, 189)}))
    peers = fields["peers"].candidate_value
    assert [p["name"] for p in peers] == [
        "Aster DM Quality Care Limited",
        "Apollo Hospitals Enterprise Limited (\u201cAHEL\u201d)",
    ]
    assert fields["peers"].page == 150


def test_the_issuers_own_row_is_not_a_peer():
    """"Paras Healthcare Limited" sits above the "Listed Peers" label and its
    own multiples are undisclosed: it must never enter the peer set."""
    fields = _fields(_section(PEER_TABLE).extract_peers({"basis_for_offer_price": (145, 189)}))
    names = [p["name"] for p in fields["peers"].candidate_value]
    assert not any("Paras" in n for n in names)


def test_a_value_split_across_two_lines_is_rejoined():
    fields = _fields(_section(PEER_TABLE).extract_peers({"basis_for_offer_price": (145, 189)}))
    ahel = next(p for p in fields["peers"].candidate_value if "AHEL" in p["name"])
    # 1,228,529.3 + "9" -> 1,228,529.39 is the EV column; the P/E is 59.36 and
    # the P/B is struck on the closing price, so no column shifted left.
    assert ahel["pe"] == 59.36
    assert ahel["pb"] == 12.18


def test_peer_valuation_date_is_the_tables_own_and_listing_history_is_unknown():
    fields = _fields(_section(PEER_TABLE).extract_peers({"basis_for_offer_price": (145, 189)}))
    for peer in fields["peers"].candidate_value:
        assert peer["as_of"] == "2026-10-05"
        # The table never states a listing history: it stays unknown rather
        # than being invented as a 15-year assumption.
        assert peer["listed_years"] is None
    assert fields["peers"].quote_is_processing is False
    assert "Enterprise Value" in fields["peers"].quote


def test_a_peer_table_without_the_listed_peers_label_yields_nothing():
    pages = {150: PEER_TABLE[150].replace("Listed Peers", "Other companies")}
    fields = _fields(_section(pages).extract_peers({"basis_for_offer_price": (145, 189)}))
    assert "peers" not in fields  # fail-closed: no label, no peer set


# ---------------------------------------------------------------------------
# 8. The builder supplies no favourable default when nothing was read
# ---------------------------------------------------------------------------


def _build(extractions, *, fixtures: bool):
    doc = SourceDocument(source_id="RHP-TEST-0001", source_type="RHP")
    builder = CanonicalInputBuilder(doc, extractions, allow_fixture_fallbacks=fixtures)
    return builder.build()


def test_capital_and_governance_absent_evidence_stays_absent():
    canonical = _build([], fixtures=False)
    cap = canonical["capital_structure"]
    for key in (
        "promoter_pledge_pct",
        "promoter_lockin_in_place",
        "large_holders_unlocked_early",
        "discounted_allotments_18m_before_drhp",
    ):
        assert cap.get(key) is None, key
    assert canonical["governance"].get("board_independent_majority") is None


def test_fixture_fallbacks_are_still_available_to_the_template_path():
    """The synthetic template chain keeps its reference values; only the
    strict (real-filing) path must fail closed."""
    canonical = _build([], fixtures=True)
    cap = canonical["capital_structure"]
    assert cap["promoter_pledge_pct"] == 0.0
    assert cap["promoter_lockin_in_place"] is True
    assert cap["large_holders_unlocked_early"] is False
    assert cap["discounted_allotments_18m_before_drhp"] is False
    assert canonical["governance"]["board_independent_majority"] is False
