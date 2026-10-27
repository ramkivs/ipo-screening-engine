"""Transaction-nature vocabulary for related-party disclosures.

A related-party note names each transaction in the filing's own words ("Rental
income", "Short term employee benefits and Other long term benefits",
"Retainers and consultant s fee", "Loan to wholly owned subsidiaries").  The
metric layer needs to know what each of those *is* -- revenue earned by the
issuer, an expense it incurred, a financing or capital movement, or something
whose direction the disclosure does not establish -- because only revenue-type
related-party income can enter the approved Module D numerator (see
``docs/investigation/RPT-EXTRACTION-AND-METRIC-DEFINITIONS-2026-10-17.md``).

Two rules govern this vocabulary:

* a nature is classified only when its wording establishes the economic
  meaning *and the direction*.  "Rent and facility fees" does not say whether
  the issuer paid or received it, so it stays unclassified; "Rental income" and
  "Rent paid by the Company" do;
* classification never changes eligibility.  ``REVENUE_CATEGORIES`` is the
  approved numerator set and is deliberately the *same* set the builder has
  always counted: sale of goods, sale of services, revenue from operations and
  job-work charges received.  Everything else this module recognises -- rents,
  employee benefits, sitting fees, retainers, repairs, purchases, loans,
  advances, deemed capital contributions, merger consideration -- is recorded as
  evidence and excluded from the numerator.

The classifier is shared: the period-matrix reader, the image-note reader and
any future reader call it, so a given nature is classified the same way
wherever it is printed.  A nature that no phrase matches stays ``unclassified``
with its verbatim text preserved by the caller.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# The approved numerator categories (Ramki, 2026-10-17).  Kept deliberately
# equal to ``CanonicalInputBuilder._RPT_SALES_SERVICES_CATEGORIES`` plus the
# ``sale_of_*`` prefix rule the builder already applies (except sale of PPE).
REVENUE_CATEGORIES = frozenset(
    {
        "sale_of_goods",
        "sale_of_services",
        "revenue_from_operations",
        "job_work_charges_received",
    }
)

# What each recognised category is, for the investigation record and for tests
# that must prove a class never leaks into the numerator.
CATEGORY_CLASS = {
    # revenue earned by the issuer
    "sale_of_goods": "revenue",
    "sale_of_services": "revenue",
    "revenue_from_operations": "revenue",
    "job_work_charges_received": "revenue",
    # assets / liabilities (financing)
    "loan_taken": "liability",
    "loan_given": "asset",
    "loan_repaid": "settlement",
    "advance_given": "asset",
    "interest_paid": "expense",
    "interest_received": "income_other",
    # purchases and operating expenses
    "purchase_of_goods": "expense",
    "purchase_of_ppe": "expense",
    "sale_of_ppe": "disposal",
    "payment_made": "settlement",
    "repairs_and_power": "expense",
    "hire_charges_paid": "expense",
    "reimbursement_expenses_paid": "expense",
    "reimbursement_expenses_received": "income_other",
    "hiring_transport_charges_paid": "expense",
    "transport_charges_paid": "expense",
    "job_work_charges_paid": "expense",
    # employee benefits and KMP compensation
    "remuneration": "expense",
    "salary": "expense",
    "employee_benefits": "expense",
    "share_based_payment": "expense",
    "sitting_fees": "expense",
    "retainer_fees": "expense",
    # property income / expense, only when the direction is stated
    "rent_received": "income_other",
    "rent_paid": "expense",
    # capital transactions
    "deemed_capital_contribution": "capital",
    "merger_consideration": "capital",
    "share_of_profit_paid": "expense",
}

# Ordered longest-phrase-first within a family; matching is on a
# whitespace-collapsed lower-case string, so a nature the filing wraps across
# two printed lines ("Post employment\ndefined benefits") still matches."
NATURE_CATEGORIES: Tuple[Tuple[str, str], ...] = (
    # revenue earned by the issuer
    ("sale of goods", "sale_of_goods"),
    ("sales of goods", "sale_of_goods"),
    ("sale of products", "sale_of_goods"),
    ("sale of services", "sale_of_services"),
    ("sales of services", "sale_of_services"),
    ("rendering of services", "sale_of_services"),
    ("rendering of service", "sale_of_services"),
    ("revenue from operations", "revenue_from_operations"),
    ("revenue from sale of healthcare services", "sale_of_services"),
    ("job work charges received", "job_work_charges_received"),
    ("sale of property, plant and equipment", "sale_of_ppe"),
    ("sale of property plant and equipment", "sale_of_ppe"),
    # purchases and operating expenses
    ("purchase of property, plant and equipment", "purchase_of_ppe"),
    ("purchase of property plant and equipment", "purchase_of_ppe"),
    ("purchases during the year", "purchase_of_goods"),
    ("purchase during the year", "purchase_of_goods"),
    ("purchase of goods", "purchase_of_goods"),
    ("purchases of goods", "purchase_of_goods"),
    ("repair & maintenance", "repairs_and_power"),
    ("repair and maintenance", "repairs_and_power"),
    ("repairs and maintenance", "repairs_and_power"),
    ("power & fuel", "repairs_and_power"),
    ("hire charges paid", "hire_charges_paid"),
    ("hiring/transport charges paid", "hiring_transport_charges_paid"),
    ("transport charges paid", "transport_charges_paid"),
    ("job work charges paid", "job_work_charges_paid"),
    ("reimbursement of expenses paid", "reimbursement_expenses_paid"),
    ("reimbursement of expenses received", "reimbursement_expenses_received"),
    # employee benefits and KMP compensation
    ("short term employee benefits", "employee_benefits"),
    ("post employment defined benefits", "employee_benefits"),
    ("post employment benefits", "employee_benefits"),
    ("post retirement benefits", "employee_benefits"),
    ("gratuity", "employee_benefits"),
    ("leave encashment", "employee_benefits"),
    ("contribution to provident fund", "employee_benefits"),
    ("share based payment", "share_based_payment"),
    ("share-based payment", "share_based_payment"),
    ("employee stock option", "share_based_payment"),
    ("directors sitting fees", "sitting_fees"),
    ("sitting fees", "sitting_fees"),
    ("retainers and consultant s fee", "retainer_fees"),
    ("retainers and consultants fee", "retainer_fees"),
    ("retainers and consultation fee", "retainer_fees"),
    ("retainer and consultant fee", "retainer_fees"),
    ("professional fees", "retainer_fees"),
    ("managerial remuneration", "remuneration"),
    ("remuneration", "remuneration"),
    ("salary", "salary"),
    ("salaries", "salary"),
    # interest, with its direction stated
    ("interest on loan taken", "interest_paid"),
    ("interest on loan paid", "interest_paid"),
    ("interest paid", "interest_paid"),
    ("interest on loan to", "interest_received"),
    ("interest on loan given", "interest_received"),
    ("interest received", "interest_received"),
    # property income / expense, only when the direction is stated
    ("rental income", "rent_received"),
    ("rent income", "rent_received"),
    ("rent received", "rent_received"),
    ("rent paid", "rent_paid"),
    ("lease rent paid", "rent_paid"),
    # financing and capital
    ("loan to wholly owned subsidiaries", "loan_given"),
    ("loan to subsidiary", "loan_given"),
    ("loan to associate", "loan_given"),
    ("amount lent", "loan_given"),
    ("amount given", "loan_given"),
    ("advance to key managerial person", "advance_given"),
    ("advances given", "advance_given"),
    ("advance given", "advance_given"),
    ("loan from holding company", "loan_taken"),
    ("loan from subsidiary", "loan_taken"),
    ("loan taken", "loan_taken"),
    ("amount borrowed", "loan_taken"),
    ("loan repaid", "loan_repaid"),
    ("loans repaid", "loan_repaid"),
    ("share of profit paid", "share_of_profit_paid"),
    ("deemed capital contribution", "deemed_capital_contribution"),
    ("investment in deemed equity", "deemed_capital_contribution"),
)


def normalise(text: str) -> str:
    """Lower-case, collapse whitespace, drop the noise OCR leaves in a word."""
    collapsed = re.sub(r"\s+", " ", (text or "").strip().lower())
    return collapsed.strip(" .:-")


def classify_nature(text: str) -> Optional[str]:
    """Category for a transaction nature, or ``None`` when it is not established.

    Matching is anchored at the start of the nature text, and the longest
    phrase wins within a family (``repair & maintenance and power & fuel`` is
    one expense, not a ``power`` keyword match).  A nature the vocabulary does
    not cover is left unclassified: a convenient default is how an expense
    becomes revenue.
    """
    normalised = normalise(text)
    if not normalised:
        return None
    best: Optional[Tuple[int, str]] = None
    for phrase, category in NATURE_CATEGORIES:
        if normalised.startswith(phrase) or normalised == phrase:
            if best is None or len(phrase) > best[0]:
                best = (len(phrase), category)
    return best[1] if best else None


# A disclosure can say, in its own words, that a figure is eliminated in
# consolidation.  Such a figure is not revenue of the consolidated entity and
# cannot be a numerator against consolidated revenue (owner decision
# 2026-10-27, report s.35).  The test is deliberately narrow -- the word
# "eliminated"/"elimination" next to nothing else -- so ordinary natures never
# match it.
_ELIMINATED = re.compile(r"\beliminat(?:ed|ion|ions|ing)\b", re.IGNORECASE)


def is_consolidation_eliminated(*texts: Optional[str]) -> bool:
    """True when the disclosure itself marks the figure as eliminated.

    Checked against whatever verbatim text the reader kept for the row (its
    nature, its printed label, a captured heading).  A row is excluded from the
    numerator when any of them says the amount is eliminated in consolidation;
    nothing is inferred from a category name or from the filing's structure.
    """
    for text in texts:
        if text and _ELIMINATED.search(str(text)):
            return True
    return False


def is_revenue_category(category: str) -> bool:
    """True only for the categories the approved numerator may count."""
    if category in REVENUE_CATEGORIES:
        return True
    return category.startswith("sale_of_") and category != "sale_of_ppe"
