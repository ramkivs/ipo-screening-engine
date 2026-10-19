"""Jio evidence remediation — live-extraction pins (2026-10-19 -> 2026-10-20).

Four evidence gaps were investigated against the committed non-authoritative
RHP (SHA-256 ``72480c2e…a59a1b6d``):

1. **Net worth / K1.**  The restated balance sheet prints Equity Share
   Capital and Other Equity, then a separate Non-Controlling Interest line;
   it prints no Total Equity subtotal.  Note 38 ("Capital Management")
   states "Total Equity (As per Restated Consolidated Statement of Assets
   and Liabilities)" as 3,359,769 / 3,050,474 / 2,782,864 — the owner
   components, excluding NCI.  Net worth is therefore derived from the two
   owner components and reconciled to Total Assets - Total Liabilities with
   NCI added back.  The issuer's own net-worth definition (p. 130 note 1)
   further excludes other comprehensive income, which would give 3,340,134
   for FY2026 (0.59% lower); that definition is not derivable from the
   balance-sheet components alone, so the canonical value is disclosed total
   equity and the difference is reported, not silently applied.  K1 still
   cannot be cleared: the auditor opinion and going-concern fields are not
   established by the governed (positive opinion language) parser, so K1
   stays UNVERIFIED.
2. **Leverage.**  Gross debt is Note 38 borrowings (707,810 at FY2026), not
   trade payables, lease liabilities or deferred payment liabilities and
   never total liabilities.  D/E = 0.21 and interest cover = 5.33 with the
   existing thresholds unchanged.
3. **RPT / K6.**  Note 36 (pp. 376-378) discloses revenue from operations
   with related parties: FY2026 63,299, FY2025 56,717, FY2024 52,878
   (INR millions).  The approved metric is the change in that share
   (4.3094% -> prior 4.4235% = -0.1141 pp), not related-party transactions
   divided by revenue and not a contribution inferred from totals.
4. **Valuation.**  The source peer table (p. 130) lists exactly two peers
   with vendor P/E and Return on Average Net Worth as of 2026-10-13.  No
   CMP is disclosed, so no P/B is invented; the second multiple and
   sector-IPO relative criteria remain UNKNOWN.

K1 and K5 remain UNVERIFIED by design.  K5's amount (Note 37: claims
15,021 at FY2026, 0.45% of net worth) is far below the 50% threshold, but
the canonical ``contingent_liabilities_unquantified`` flag is not
established by any governed extractor, and absence of a disclosure is not
evidence that it is false.
"""

from __future__ import annotations

import pytest

from conftest import REPO_ROOT
from ipo_screening.extraction import DocumentExtractor

JIO_PDF = (
    REPO_ROOT / "evidence" / "non-authoritative" / "jio"
    / "U72900GJ2019PLC110816_JIO.pdf"
)


@pytest.mark.slow
def test_live_extraction_pins_remediated_evidence():
    doc, _ = DocumentExtractor().extract_from_pdf(
        pdf_path=JIO_PDF, allow_fixture_fallbacks=False
    )
    financials = doc["financials"]
    periods = financials["periods"]
    assert [p["fy"] for p in periods] == ["FY2024", "FY2025", "FY2026"]
    assert financials["reporting_unit"] == "INR_MILLIONS"

    # 1. Net worth = Equity Share Capital + Other Equity (Note 38 total
    # equity).  NCI (10,993 / 11,338 / 11,353) reconciles the balance sheet
    # but is not part of net worth.
    assert [p["net_worth"] for p in periods] == [
        2782864.0, 3050474.0, 3359769.0
    ]
    assert [p["total_debt"] for p in periods] == [
        543489.0, 730603.0, 707810.0
    ]

    # 2. Leverage inputs: D/E and interest cover under existing bands.
    latest = periods[-1]
    assert latest["total_debt"] == 707810.0
    assert latest["net_worth"] == 3359769.0
    assert latest["ebit"] == 461327.0
    assert latest["interest_expense"] == 86534.0
    assert latest["total_debt"] / latest["net_worth"] == pytest.approx(0.2107, abs=1e-4)
    assert latest["ebit"] / latest["interest_expense"] == pytest.approx(5.3312, abs=1e-4)

    # 3. Post-issue EPS is unit-correct: PAT in INR millions divided by
    # post-issue shares (not the old lakhs factor that produced 3.26).
    issue = doc["issue"]
    assert issue["fresh_shares"] == 270000000
    assert issue["ofs"] == 0.0
    assert issue["post_issue_shares"] == 9209030830
    assert issue["pre_issue_shares"] == 8939030830
    assert issue["post_issue_eps"] == pytest.approx(32.63, abs=0.01)

    # 4. Peers: exactly the two companies the source table names, each with
    # its own disclosed multiple and the filing's valuation date.  No CMP
    # column exists, so P/B and listing history stay unknown.
    peers = {p["name"]: p for p in doc["peers"]}
    assert set(peers) == {"Bharti Airtel Limited", "Vodafone Idea Limited"}
    assert peers["Bharti Airtel Limited"]["pe"] == 40.71
    assert peers["Bharti Airtel Limited"]["roe_pct"] == 20.32
    assert peers["Vodafone Idea Limited"]["pe"] == 3.99
    assert peers["Vodafone Idea Limited"]["roe_pct"] is None  # disclosed "NM"
    for peer in peers.values():
        assert peer["as_of"] == "2026-10-13"
        assert peer["pb"] is None
        assert peer["listed_years"] is None

    # 5. RPT / K6: share of revenue and change in share, from Note 36.
    governance = doc["governance"]
    assert governance["rpt_pct_revenue"] == pytest.approx(4.3094, abs=0.0005)
    assert governance["rpt_pct_of_revenue_growth"] == pytest.approx(-0.1141, abs=0.0005)

    # 6. K1 and K5 evidence boundary: no inference from an absent disclosure.
    assert governance["auditor_opinion"] is None
    assert governance["going_concern_uncertainty"] is None
    assert governance["eom_materiality"] is None
    assert financials["contingent_liabilities"] is None
    assert financials["contingent_liabilities_unquantified"] is None
