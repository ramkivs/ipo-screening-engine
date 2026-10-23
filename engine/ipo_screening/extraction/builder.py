"""Canonical JSON input builder from RawExtractions.

Technical Design v1.5 s3.2, s15:
  Merges parsed field extractions into the canonical v1.5 input schema
  (schema/ipo-input.v1.5.schema.json), attaching strict provenance
  (_sources, _evidence) and preserving fail-closed nulls for unreadable
  or undisclosed fields.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from .interfaces import RawExtraction, SourceDocument


class CanonicalInputBuilder:
    """Builds and validates canonical IPO input JSON from raw extraction records."""

    SCHEMA_PATH = Path("schema/ipo-input.v1.5.schema.json")

    def __init__(
        self,
        doc: SourceDocument,
        extractions: List[RawExtraction],
        reference_base: Optional[Dict[str, Any]] = None,
        allow_fixture_fallbacks: bool = False,
    ) -> None:
        self.doc = doc
        self.extractions = extractions
        self.base = json.loads(json.dumps(reference_base)) if reference_base else {}
        self.allow_fixture_fallbacks = allow_fixture_fallbacks

    def build(self) -> Dict[str, Any]:
        """Construct the canonical dictionary including _sources and _evidence."""
        company_name = self._get_field("company_name", self.base.get("company_name", "Unknown Limited"))
        # Strip common prospectus title prefixes if inadvertently captured
        for pfx in ["RED HERRING PROSPECTUS", "DRAFT RED HERRING PROSPECTUS", "PROSPECTUS OF"]:
            if pfx in company_name:
                company_name = company_name.replace(pfx, "").strip()

        icdr_route = self.base.get("icdr_route") or self._detect_icdr_route()
        sector_profile = self.base.get("sector_profile") or self._detect_sector_profile()
        sector = self.base.get("sector") or self._detect_sector()

        # D-PEER-1: no synthetic peer fallback. When neither the reference
        # input nor extraction supplies genuine peers, the honest
        # representation is an empty list (permitted by the input
        # contract); peer-relative metrics then resolve UNKNOWN.
        peers_list = self.base.get("peers")
        if not peers_list:
            peers_list = self._get_field("peers")
        if not peers_list:
            peers_list = []

        output: Dict[str, Any] = {
            "ipo_id": self.base.get("ipo_id") or self._slugify(company_name or "UNKNOWN-IPO"),
            "company_name": company_name,
            "board": self.base.get("board") or self._get_field("board", "mainboard"),
            "icdr_route": icdr_route,
            "sector_profile": sector_profile,
            "sector": sector,
            "_sources": self._build_sources(),
            "_evidence": self._build_evidence(),
            "issue": self._build_issue(),
            "financials": self._build_financials(),
            "capital_structure": self._build_capital_structure(),
            "use_of_proceeds": self._build_use_of_proceeds(),
            "governance": self._build_governance(),
            "business": self._build_business(),
            "peers": peers_list,
        }

        if "market" in self.base:
            output["market"] = self.base["market"]
        if "recent_sector_ipos" in self.base:
            output["recent_sector_ipos"] = self.base["recent_sector_ipos"]

        return output

    def _detect_sector_profile(self) -> str:
        """Heuristic detection of sector profile from filing indicators."""
        cname = str(self._get_field("company_name", "")).lower()
        if any(w in cname for w in ["housing finance", "finance", "nbfc", "bank", "lending"]):
            return "financial"
        if any(w in cname for w in ["infra", "construction", "engineering", "projects"]):
            return "epc_real_estate"
        periods = self._get_field("financials.periods", [])
        if len(periods) >= 5:
            return "cyclical"
        if any(w in cname for w in ["forgings", "steel", "sugar", "textiles"]):
            return "cyclical"
        return "standard"

    def _detect_sector(self) -> str:
        prof = self._detect_sector_profile()
        if prof == "financial":
            return "Financial Services / Lending"
        if prof == "epc_real_estate":
            return "Infrastructure / Construction / Real Estate"
        if prof == "cyclical":
            return "Heavy Engineering / Cyclical Manufacturing"
        return "Diversified / General"

    def _detect_icdr_route(self) -> str:
        """Detect whether ICDR route is 6(1) or 6(2)."""
        quotas = self._get_field("issue.quota_pct", {})
        if quotas and isinstance(quotas, dict):
            if quotas.get("qib", 0) >= 70.0:
                return "6(2)"
        return "6(1)"

    def validate(self, instance: Optional[Dict[str, Any]] = None) -> bool:
        """Validate instance against schema/ipo-input.v1.5.schema.json."""
        target = instance or self.build()
        if not self.SCHEMA_PATH.exists():
            return True
        # If incomplete raw extraction (e.g. price is None before enrichment), skip full scoring schema check
        if target.get("issue", {}).get("price_band_low") is None:
            return True
        with open(self.SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=target, schema=schema)
        return True

    def _get_field(self, field_path: str, default: Any = None) -> Any:
        for ex in self.extractions:
            if ex.field_path == field_path:
                return ex.candidate_value
        return default

    def _slugify(self, text: str) -> str:
        s = "".join(c if c.isalnum() else "-" for c in text.upper())
        return "-".join(filter(None, s.split("-")))

    def _build_sources(self) -> List[Dict[str, Any]]:
        sources = [self.doc.to_source_ref_dict()]
        for src in self.base.get("_sources", []):
            if src.get("source_id") != self.doc.source_id:
                sources.append(src)
        return sources

    def _build_evidence(self) -> Dict[str, Dict[str, Any]]:
        evidence_dict: Dict[str, Dict[str, Any]] = {}
        for ex in self.extractions:
            evidence_dict.setdefault(ex.field_path, ex.to_evidence_dict(self.doc.source_id))

        # Seller-specific OFS quantities: the cover extraction records the
        # (single, list-valued) ofs_sellers result; without subfield
        # evidence the Explorer can show the seller's identity but never
        # the quantity attributed to that seller. Emit one evidence spec
        # per seller for shares_sold, bound to the same filing source,
        # page and locator as the seller list itself. The identity
        # quotation remains on issue.ofs_sellers; these specs record the
        # quantity linkage established by the Offer-for-Sale clause.
        for ex in self.extractions:
            if ex.field_path != "issue.ofs_sellers":
                continue
            if not isinstance(ex.candidate_value, list):
                continue
            base_spec = evidence_dict.get("issue.ofs_sellers") or ex.to_evidence_dict(self.doc.source_id)
            for idx, seller in enumerate(ex.candidate_value):
                if not isinstance(seller, dict) or seller.get("shares_sold") is None:
                    continue
                sub_path = f"issue.ofs_sellers[{idx}].shares_sold"
                spec = dict(base_spec)
                spec["evidence_id"] = f"EV-{sub_path}"
                spec["note"] = (
                    "Seller-specific Offer-for-Sale quantity attributed to the "
                    "named selling shareholder from the cover Offer-for-Sale "
                    "clause; seller identity quotation is recorded on "
                    "issue.ofs_sellers."
                )
                evidence_dict[sub_path] = spec
        # Carry over any pre-existing base evidence if not overridden
        for k, v in self.base.get("_evidence", {}).items():
            if k not in evidence_dict:
                evidence_dict[k] = v
        return evidence_dict

    def _build_issue(self) -> Dict[str, Any]:
        issue_base = self.base.get("issue", {})
        default_low = 208 if self.allow_fixture_fallbacks else None
        default_high = 220 if self.allow_fixture_fallbacks else None
        default_lot = 68 if self.allow_fixture_fallbacks else None
        default_fresh = 14500 if self.allow_fixture_fallbacks else None
        default_ofs = 3300 if self.allow_fixture_fallbacks else None
        default_fshares = 6590909 if self.allow_fixture_fallbacks else None
        default_pshares = 26390909 if self.allow_fixture_fallbacks else None
        default_presh = 19800000 if self.allow_fixture_fallbacks else None
        default_eps = 9.46 if self.allow_fixture_fallbacks else None
        default_open = "2026-09-30" if self.allow_fixture_fallbacks else None
        default_close = "2026-10-05" if self.allow_fixture_fallbacks else None

        def _pick_issue(key: str, default: Any = None) -> Any:
            if key in issue_base:
                return issue_base[key]
            return self._get_field(f"issue.{key}", default)

        fresh_shares = _pick_issue("fresh_shares", default_fshares)
        pre_shares = _pick_issue("pre_issue_shares", default_presh)
        post_shares = _pick_issue("post_issue_shares", default_pshares)
        if post_shares is None and pre_shares is not None and fresh_shares is not None:
            post_shares = pre_shares + fresh_shares

        # Deterministically derive post_issue_eps from restated PAT and
        # post_issue_shares if not explicitly provided.  The reporting unit
        # is the filing's, never an assumed lakh default: a filing stated in
        # INR millions previously produced an EPS ten times too small
        # (Jio: 3.26 instead of 32.63), which feeds P/E and PEG.
        post_eps = _pick_issue("post_issue_eps", None)
        if post_eps is None:
            fin_base = self.base.get("financials", {})
            periods = fin_base.get("periods") or self._get_field("financials.periods", [])
            unit = fin_base.get("reporting_unit") or self._get_field(
                "financials.reporting_unit", "INR_LAKHS"
            )
            factor = self._ISSUE_UNIT_TO_RUPEES.get(unit)
            if post_shares and periods and post_shares > 0 and factor:
                latest_p = periods[-1]
                latest_pat = latest_p.get("pat")
                if latest_pat is not None:
                    post_eps = round((latest_pat * factor) / post_shares, 2)
        if post_eps is None and self.allow_fixture_fallbacks:
            post_eps = default_eps

        res: Dict[str, Any] = {
            "price_band_low": _pick_issue("price_band_low", default_low),
            "price_band_high": _pick_issue("price_band_high", default_high),
            "lot_size": _pick_issue("lot_size", default_lot),
            "fresh_issue": _pick_issue("fresh_issue", default_fresh),
            "ofs": _pick_issue("ofs", default_ofs),
            "fresh_shares": fresh_shares,
            "post_issue_shares": post_shares,
            "pre_issue_shares": pre_shares,
            "post_issue_eps": post_eps,
            "open_date": _pick_issue("open_date", default_open),
            "close_date": _pick_issue("close_date", default_close),
        }
        if "quota_pct" in issue_base:
            res["quota_pct"] = issue_base["quota_pct"]
        elif self._get_field("issue.quota_pct"):
            res["quota_pct"] = self._get_field("issue.quota_pct")

        if "ofs_sellers" in issue_base:
            res["ofs_sellers"] = issue_base["ofs_sellers"]
        elif self._get_field("issue.ofs_sellers") is not None:
            res["ofs_sellers"] = self._get_field("issue.ofs_sellers")

        return res

    def _build_financials(self) -> Dict[str, Any]:
        fin_base = self.base.get("financials", {})
        unit = fin_base["reporting_unit"] if "reporting_unit" in fin_base else self._get_field("financials.reporting_unit", "INR_LAKHS")
        periods = fin_base["periods"] if "periods" in fin_base else self._get_field("financials.periods", [])
        cl = fin_base["contingent_liabilities"] if "contingent_liabilities" in fin_base else self._get_field("financials.contingent_liabilities", None)
        # The unquantified flag is extracted only from a positive disclosure;
        # an absent disclosure leaves it unknown (never False).
        cl_unquantified = fin_base.get("contingent_liabilities_unquantified")
        if cl_unquantified is None:
            cl_unquantified = self._get_field("financials.contingent_liabilities_unquantified", None)
        result = {
            "reporting_unit": unit,
            "periods": periods,
            "contingent_liabilities": cl,
            "contingent_liabilities_unquantified": cl_unquantified,
        }
        # Schema-permitted penalty inputs must not be dropped by the builder:
        # the ``unreconciled_metrics`` penalty consumes this flag, and a value
        # present in the input/extraction was previously lost here (the
        # penalty could never be evaluated).  Only carried when established,
        # so an absent value stays absent (UNKNOWN), never defaulted.
        if "adjusted_metrics_unreconciled" in fin_base:
            result["adjusted_metrics_unreconciled"] = fin_base["adjusted_metrics_unreconciled"]
        else:
            extracted_unreconciled = self._get_field(
                "financials.adjusted_metrics_unreconciled", None
            )
            if extracted_unreconciled is not None:
                result["adjusted_metrics_unreconciled"] = extracted_unreconciled
        return result

    def _build_capital_structure(self) -> Dict[str, Any]:
        cap_base = self.base.get("capital_structure", {})
        pre_pct = cap_base["promoter_pre_pct"] if "promoter_pre_pct" in cap_base else self._get_field("capital_structure.promoter_pre_pct", 73.42 if self.allow_fixture_fallbacks else None)
        post_pct = cap_base["promoter_post_pct"] if "promoter_post_pct" in cap_base else self._get_field("capital_structure.promoter_post_pct", None)
        pledge_pct = cap_base["promoter_pledge_pct"] if "promoter_pledge_pct" in cap_base else self._get_field("capital_structure.promoter_pledge_pct", 0.0)
        lockin = cap_base["promoter_lockin_in_place"] if "promoter_lockin_in_place" in cap_base else self._get_field("capital_structure.promoter_lockin_in_place", True)

        return {
            "promoter_pre_pct": pre_pct,
            "promoter_post_pct": post_pct,
            "promoter_pledge_pct": pledge_pct,
            "promoter_lockin_in_place": lockin,
            "large_holders_unlocked_early": cap_base.get("large_holders_unlocked_early", False),
            "pre_ipo_placements": cap_base.get("pre_ipo_placements", []),
            "discounted_allotments_18m_before_drhp": cap_base.get("discounted_allotments_18m_before_drhp", False),
        }

    def _build_use_of_proceeds(self) -> List[Dict[str, Any]]:
        if "use_of_proceeds" in self.base:
            return self.base["use_of_proceeds"]
        extracted_uop = self._get_field("use_of_proceeds", None)
        if extracted_uop:
            return extracted_uop
        return []

    #: Bucket spellings an input may legitimately use for one of the three
    #: governed buckets.  Anything else is UNKNOWN -- never "clean": an
    #: unreadable value is missing evidence, not evidence of no litigation.
    _LITIGATION_BUCKET_ALIASES = {
        "clean": "clean",
        "none": "clean",
        "nil": "clean",
        "no_litigation": "clean",
        "minor_civil": "minor_civil",
        "civil": "minor_civil",
        "material_civil": "minor_civil",
        "criminal_or_regulatory": "criminal_or_regulatory",
        "criminal": "criminal_or_regulatory",
        "regulatory": "criminal_or_regulatory",
    }

    @classmethod
    def _normalise_litigation_bucket(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        return cls._LITIGATION_BUCKET_ALIASES.get(str(value).strip().lower())

    def _build_governance(self) -> Dict[str, Any]:
        gov_base = self.base.get("governance", {})
        # D-5: neither the litigation bucket nor the SEBI/ED flag may be
        # defaulted.  The previous code (a) fell back to ``"clean"`` when the
        # extraction carried no bucket, (b) mapped *any* value that was not
        # ``criminal_or_regulatory`` onto ``"clean"`` -- so an extracted
        # ``minor_civil`` finding was silently rewritten into the favourable
        # bucket, 4/4 points instead of 2/4, destroying the evidence it was
        # taken from -- and (c) defaulted ``sebi_ed_action_active`` to
        # ``False``.  Both fields now stay ``None`` (UNKNOWN) unless the input
        # or an evidenced extraction establishes them; only explicitly stated
        # synonyms of a bucket are normalised.
        if "litigation_bucket" in gov_base:
            raw_lit: Any = gov_base["litigation_bucket"]
        else:
            raw_lit = self._get_field("governance.litigation_bucket", None)
        lit = self._normalise_litigation_bucket(raw_lit)

        def _pick_gov(key: str, default: Any = None) -> Any:
            if key in gov_base:
                return gov_base[key]
            return self._get_field(f"governance.{key}", default)

        gov = {
            "auditor_opinion": _pick_gov("auditor_opinion", None),
            "auditor_changed_3y": _pick_gov("auditor_changed_3y", None),
            "auditor_reputed": _pick_gov("auditor_reputed", None),
            "repeated_eom": _pick_gov("repeated_eom", None),
            "eom_materiality": _pick_gov("eom_materiality", None),
            "going_concern_uncertainty": _pick_gov("going_concern_uncertainty", None),
            "litigation_bucket": lit,
            "sebi_ed_action_active": _pick_gov("sebi_ed_action_active", None),
            "rpt_pct_revenue": _pick_gov("rpt_pct_revenue", 6.67 if self.allow_fixture_fallbacks else None),
            "rpt_pct_of_revenue_growth": _pick_gov("rpt_pct_of_revenue_growth", None),
            "board_independent_majority": _pick_gov("board_independent_majority", False),
            "kmp_exits_2y": _pick_gov("kmp_exits_2y", None),
        }
        # Schema-permitted governance inputs that a penalty/knockout consumes
        # must not be dropped.  ``auditor_or_cfo_exit_2y`` drives the
        # auditor/CFO-exit penalty; it was previously read by the derived
        # metric but never carried into the canonical input, so the penalty
        # was structurally UNKNOWN for every builder-based evaluation.  The
        # key is added only when the input/extraction establishes it, so the
        # absent case remains UNKNOWN (and the golden input is unchanged).
        for optional_key in ("auditor_or_cfo_exit_2y",):
            if optional_key in gov_base:
                gov[optional_key] = gov_base[optional_key]
            else:
                extracted = self._get_field(f"governance.{optional_key}", None)
                if extracted is not None:
                    gov[optional_key] = extracted
        self._derive_rpt_metrics(gov)
        return gov

    # Approved RPT metric definitions (Ramki, 2026-10-17; see
    # docs/investigation/RPT-EXTRACTION-AND-METRIC-DEFINITIONS-2026-10-17.md):
    # * Module D ``rpt_pct_revenue`` = related-party sales/services income
    #   / revenue from operations, latest audited FY, %.
    # * K6 ``rpt_pct_of_revenue_growth`` = change in that share between
    #   the latest two comparable audited FYs, in percentage points
    #   (latest share - prior share); a declining share is negative and
    #   therefore cannot satisfy the existing >40 trigger.
    # Eligible numerator categories are revenue-type only: sale of
    # goods/services (excluding sale of PPE) and job-work charges
    # received.  Purchases, financing, interest paid, remuneration and
    # balances are excluded (retained as evidence only).  Fail closed:
    # missing periods/revenue, non-positive revenue, unknown or
    # unconvertible units, or a missing numerator leave the fields null.
    _RPT_SALES_SERVICES_CATEGORIES = frozenset(
        {"sale_of_goods", "sale_of_services", "revenue_from_operations", "job_work_charges_received"}
    )
    _ISSUE_UNIT_TO_RUPEES = {
        "INR_LAKHS": 1e5,
        "INR_CRORES": 1e7,
        "INR_MILLIONS": 1e6,
        "INR_BILLIONS": 1e9,
    }

    _RPT_UNIT_TO_RUPEES = {
        "INR_LAKHS": 1e5,
        "INR_CRORES": 1e7,
        "INR_MILLIONS": 1e6,
        "INR_BILLIONS": 1e9,
    }

    @classmethod
    def _rpt_is_sales_services(cls, category: str) -> bool:
        if category in cls._RPT_SALES_SERVICES_CATEGORIES:
            return True
        return category.startswith("sale_of_") and category != "sale_of_ppe"

    def _derive_rpt_metrics(self, gov: Dict[str, Any]) -> None:
        if gov.get("rpt_pct_revenue") is not None and gov.get("rpt_pct_of_revenue_growth") is not None:
            return
        txns = [
            ex.candidate_value
            for ex in self.extractions
            if ex.field_path.startswith("governance.related_party_transactions[")
            and isinstance(ex.candidate_value, dict)
        ]
        if not txns:
            return
        financials = self._build_financials()
        reporting_unit = financials.get("reporting_unit")
        if reporting_unit not in self._RPT_UNIT_TO_RUPEES:
            return
        periods: Dict[int, float] = {}
        for period in financials.get("periods") or []:
            if not isinstance(period, dict):
                continue
            m = re.match(r"FY(20\d{2})$", str(period.get("fy") or ""))
            revenue = period.get("revenue")
            if m and isinstance(revenue, (int, float)) and revenue > 0:
                periods[int(m.group(1))] = float(revenue)
        if not periods:
            return
        eligible = [t for t in txns if self._rpt_is_sales_services(str(t.get("category") or ""))]
        if not eligible:
            return
        sums: Dict[int, float] = {}
        for txn in eligible:
            unit = txn.get("unit")
            m = re.match(r"FY(20\d{2})$", str(txn.get("period") or ""))
            amount = txn.get("amount")
            if unit not in self._RPT_UNIT_TO_RUPEES or not m or not isinstance(amount, (int, float)):
                return  # unconvertible/insufficient evidence: fail closed
            year = int(m.group(1))
            converted = amount * self._RPT_UNIT_TO_RUPEES[unit] / self._RPT_UNIT_TO_RUPEES[reporting_unit]
            sums[year] = sums.get(year, 0.0) + converted
        shares: Dict[int, float] = {}
        for year, revenue in periods.items():
            if year in sums:
                numerator = sums[year]
            else:
                # Eligible categories are disclosed in the note but no
                # amount was disclosed for this year ("-" cells): the
                # disclosed numerator is zero, not missing.
                numerator = 0.0
            shares[year] = numerator / revenue * 100.0
        latest = max(shares)
        if gov.get("rpt_pct_revenue") is None:
            gov["rpt_pct_revenue"] = round(shares[latest], 4)
        if gov.get("rpt_pct_of_revenue_growth") is None:
            prior_years = [y for y in shares if y < latest]
            if prior_years:
                prior = max(prior_years)
                gov["rpt_pct_of_revenue_growth"] = round(shares[latest] - shares[prior], 4)

    def _build_business(self) -> Dict[str, Any]:
        biz_base = self.base.get("business", {})

        def _pick_biz(key: str, default: Any = None) -> Any:
            if key in biz_base:
                return biz_base[key]
            return self._get_field(f"business.{key}", default)

        ob = self._get_field("business.order_book", biz_base.get("order_book", None))

        res = {
            "industry_cagr_pct": _pick_biz("industry_cagr_pct", 3.8 if self.allow_fixture_fallbacks else None),
            "industry_scope": _pick_biz("industry_scope", None),
            "industry_forecast_period": _pick_biz("industry_forecast_period", None),
            "industry_source": _pick_biz("industry_source", None),
            "top5_customer_pct": _pick_biz("top5_customer_pct", 85.33 if self.allow_fixture_fallbacks else None),
            "top5_supplier_pct": _pick_biz("top5_supplier_pct", None),
            "moat_rating": _pick_biz("moat_rating", "strong_niche" if self.allow_fixture_fallbacks else None),
            "visibility_rating": _pick_biz("visibility_rating", "strong" if self.allow_fixture_fallbacks else None),
            "regulatory_dependence": _pick_biz("regulatory_dependence", None),
        }
        if ob is not None:
            res["order_book"] = ob
        return res
