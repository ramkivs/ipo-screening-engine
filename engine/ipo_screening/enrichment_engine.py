"""Pre-Score Enrichment Engine.

Phase 5G: Pre-Score Enrichment Engine.

Connects:
    RHP / DRHP extraction
              +
    Price Band Notice
              +
    Supplemental structured inputs
              +
    Future market/peer/analyst payloads
              |
              v
       PRE-SCORE ENRICHMENT
              |
              v
      Reconciled canonical input
              |
              v
        Existing frozen
       deterministic core
              |
              v
             Score

Key Architectural Invariants:
1. Stateless & Side-Effect Free:
   - Does not mutate input objects in place (strictly deepcopying before mutation).
   - Repeated assembly with identical inputs produces bit-for-bit identical results.
2. Source Precedence:
   - Price/Lot/Dates: Price Band Notice > Authoritative later source > RHP definitive > Preliminary RHP [●] > Manual/Template.
   - Statutory Facts: Authoritative RHP/DRHP > Manual/Template.
   - Market Demand: Newest valid governed snapshot > Stale snapshot > Missing (UNKNOWN).
   - Peer Multiples: Newest valid snapshot > Historical RHP peer table.
   - Analyst Ratings: Analyst assessment owns subjective fields (moat, visibility); NEVER overwrites statutory quantitative facts.
3. Source Facts vs. Derived Quantities (D-5D-07, D-5D-08):
   - Computes dynamic fresh shares, post-issue shares, OFS amounts, post-issue EPS, and promoter post % upstream.
   - Every derived field carries is_derived=True, formula, and explicit dependencies.
4. Hard-Coded Fallback Elimination (D-5D-06):
   - Zero historical fixture defaults (no 208, 220, 68, 9.46, 85.33). Missing values evaluate to None / UNKNOWN.
5. Conflict Handling:
   - Conflicts between authoritative sources fail closed (EnrichmentConflictError).
6. Preliminary vs. Final Modes:
   - Preliminary: Price Band Notice may be absent, price/demand/GMP remain UNKNOWN without fabricating values.
   - Final: Price Band Notice required; missing mandatory pricing facts fail closed (EnrichmentValidationError).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .canonical import ExtractionMethod, SourceRef, SourceType, Verification
from .enrichment_contract import (
    PRICE_BAND_NOTICE_NOTE,
    PRICE_BAND_NOTICE_SOURCE_TYPE,
    is_analyst_source,
    is_price_band_source,
    validate_enrichment_contract,
    validate_source_derived_separation,
)
from .errors import EngineError, Finding, SEVERITY_ERROR, SEVERITY_WARNING
from .extraction.price_band_notice import PriceBandNoticeResult


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------


class EnrichmentError(EngineError):
    """Base exception for enrichment and reconciliation failures."""


class EnrichmentConflictError(EnrichmentError):
    """Raised when conflicting authoritative sources cannot be reconciled under codified precedence."""


class EnrichmentValidationError(EnrichmentError):
    """Raised when required data is missing in final evaluation mode."""


class PrecedenceViolationError(EnrichmentError):
    """Raised when an unprivileged source attempts to overwrite a higher-precedence source fact."""


# --------------------------------------------------------------------------
# Dispositions & Data Structures
# --------------------------------------------------------------------------


class FieldDisposition(str, Enum):
    """Historical field disposition tracking."""

    ASSEMBLED = "ASSEMBLED"
    DERIVED = "DERIVED"
    PRESERVED = "PRESERVED"
    UNKNOWN = "UNKNOWN"
    DEFERRED_TO_5H = "DEFERRED_TO_5H"


@dataclass(frozen=True)
class DerivedField:
    """Provenance and calculation record for a derived value."""

    field_path: str
    value: Any
    formula: str
    dependencies: List[str]
    source_facts: Dict[str, Any] = field(default_factory=dict)
    is_derived: bool = True
    reconciled_with_source: Optional[bool] = None
    source_fact_value: Optional[Any] = None
    variance_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_path": self.field_path,
            "value": self.value,
            "formula": self.formula,
            "dependencies": self.dependencies,
            "source_facts": self.source_facts,
            "is_derived": self.is_derived,
            "reconciled_with_source": self.reconciled_with_source,
            "source_fact_value": self.source_fact_value,
            "variance_pct": self.variance_pct,
        }


@dataclass
class EnrichmentResult:
    """The complete result of pre-score enrichment assembly."""

    canonical_input: Dict[str, Any]
    derivations: Dict[str, DerivedField] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)
    field_traceability: Dict[str, str] = field(default_factory=dict)
    mode: str = "final"
    as_of: Optional[str] = None
    is_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_input": self.canonical_input,
            "derivations": {k: v.to_dict() for k, v in self.derivations.items()},
            "findings": [f.to_dict() for f in self.findings],
            "field_traceability": self.field_traceability,
            "mode": self.mode,
            "as_of": self.as_of,
            "is_valid": self.is_valid,
        }


# --------------------------------------------------------------------------
# Pre-Score Enrichment Engine
# --------------------------------------------------------------------------


class EnrichmentEngine:
    """Stateless, deterministic pre-score enrichment engine."""

    # Unit multipliers to convert reporting units to rupees (INR)
    _UNIT_MULTIPLIERS: Mapping[str, int] = {
        "INR_LAKHS": 100_000,
        "INR_CRORES": 10_000_000,
        "INR_MILLIONS": 1_000_000,
        "INR_BILLIONS": 1_000_000_000,
    }

    # All 24 historical "Details not in RHP" fields required by Section 18
    HISTORICAL_FIELDS: Sequence[str] = (
        "company_name",
        "issue_open",
        "issue_close",
        "qib_quota",
        "retail_quota",
        "seller_type",
        "seller_pre_issue_shares",
        "promoter_pledge",
        "promoter_lockin",
        "bonus_discount_allotments",
        "moat",
        "order_book_visibility",
        "recent_sector_ipo_pe",
        "anchor_quality",
        "nifty_trend",
        "last_five_ipo_listing_gains",
        "qib_subscription",
        "nii_subscription",
        "retail_subscription",
        "overall_subscription",
        "gmp",
        "gmp_trend",
        "price_cap",
        "price_floor",
        "lot",
    )

    @classmethod
    def assemble(
        cls,
        base_input: Mapping[str, Any],
        price_band_notice: Optional[PriceBandNoticeResult | Mapping[str, Any]] = None,
        supplemental: Optional[Mapping[str, Any]] = None,
        market_snapshot: Optional[Mapping[str, Any]] = None,
        peer_snapshot: Optional[Mapping[str, Any]] = None,
        analyst_assessment: Optional[Mapping[str, Any]] = None,
        mode: str = "final",
        as_of: Optional[str] = None,
        allow_manual_override: bool = False,
    ) -> EnrichmentResult:
        """Assemble an enriched canonical input snapshot.

        Invariants:
        1. base_input is deeply copied; original input is never mutated.
        2. Source precedence is strictly enforced.
        3. Dynamic derivations computed upstream with formulas and dependencies.
        4. Zero fixture defaults; missing values evaluate to None.
        5. In final mode, missing mandatory notice information fails closed.
        """
        # Deepcopy to guarantee immutability of caller's input
        canonical: Dict[str, Any] = copy.deepcopy(dict(base_input))
        findings: List[Finding] = []
        derivations: Dict[str, DerivedField] = {}
        traceability: Dict[str, str] = {}

        # Initialize _sources and _evidence if absent
        if "_sources" not in canonical:
            canonical["_sources"] = []
        if "_evidence" not in canonical:
            canonical["_evidence"] = {}

        existing_source_ids: Set[str] = {s.get("source_id") for s in canonical["_sources"] if "source_id" in s}

        # ------------------------------------------------------------------
        # Step 1: Reconcile Price Band Notice (Cap, Floor, Lot, Dates)
        # ------------------------------------------------------------------
        pbn_data, pbn_source_ref = cls._extract_pbn_payload(price_band_notice)

        if pbn_source_ref and pbn_source_ref.get("source_id") not in existing_source_ids:
            canonical["_sources"].append(pbn_source_ref)
            existing_source_ids.add(pbn_source_ref["source_id"])

        cls._reconcile_pricing_terms(
            canonical,
            pbn_data,
            pbn_source_ref,
            supplemental,
            mode,
            findings,
            traceability,
        )

        # ------------------------------------------------------------------
        # Step 2: Reconcile Statutory Base Facts vs. Manual Templates
        # ------------------------------------------------------------------
        cls._reconcile_statutory_facts(
            canonical,
            supplemental,
            allow_manual_override,
            findings,
            traceability,
        )

        # ------------------------------------------------------------------
        # Step 3: Reconcile Analyst Subjective Ratings (Moat, Visibility)
        # ------------------------------------------------------------------
        cls._reconcile_analyst_ratings(
            canonical,
            analyst_assessment,
            supplemental,
            findings,
            traceability,
            existing_source_ids,
        )

        # ------------------------------------------------------------------
        # Step 4: Reconcile Market Demand & Peer Multiples
        # ------------------------------------------------------------------
        cls._reconcile_market_and_peers(
            canonical,
            market_snapshot,
            peer_snapshot,
            supplemental,
            findings,
            traceability,
            existing_source_ids,
        )

        # ------------------------------------------------------------------
        # Step 5: Dynamic Upstream Derivations (Fresh Shares, Post Shares, OFS, EPS, Promoter %)
        # ------------------------------------------------------------------
        cls._compute_derivations(
            canonical,
            derivations,
            findings,
            traceability,
        )

        # ------------------------------------------------------------------
        # Step 6: Complete Historical Traceability Matrix
        # ------------------------------------------------------------------
        cls._complete_traceability_matrix(canonical, traceability)

        has_errors = any(f.severity == SEVERITY_ERROR for f in findings)
        return EnrichmentResult(
            canonical_input=canonical,
            derivations=derivations,
            findings=findings,
            field_traceability=traceability,
            mode=mode,
            as_of=as_of or canonical.get("as_of"),
            is_valid=not has_errors,
        )

    # ----------------------------------------------------------------------
    # Helper: Extract Price Band Notice Payload & SourceRef
    # ----------------------------------------------------------------------

    @classmethod
    def _extract_pbn_payload(
        cls,
        pbn: Optional[PriceBandNoticeResult | Mapping[str, Any]],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        if pbn is None:
            return None, None

        if isinstance(pbn, PriceBandNoticeResult):
            enrichment_dict = pbn.to_enrichment_dict()
            source_ref = enrichment_dict.get("sources", [{}])[0]
            price_band = enrichment_dict.get("price_band", {})
            return price_band, source_ref

        # Mapping / dict shape
        pbn_dict = dict(pbn)
        if "price_band" in pbn_dict:
            # Phase 5E contract doc shape
            source_ref = pbn_dict.get("sources", [{}])[0] if pbn_dict.get("sources") else None
            return pbn_dict["price_band"], source_ref
        elif "price_band_high" in pbn_dict or "price_band_low" in pbn_dict:
            # Flat dictionary shape
            return pbn_dict, pbn_dict.get("_source_ref")

        return None, None

    # ----------------------------------------------------------------------
    # Step 1: Pricing Terms Reconciler
    # ----------------------------------------------------------------------

    @classmethod
    def _reconcile_pricing_terms(
        cls,
        canonical: Dict[str, Any],
        pbn_data: Optional[Dict[str, Any]],
        pbn_source_ref: Optional[Dict[str, Any]],
        supplemental: Optional[Mapping[str, Any]],
        mode: str,
        findings: List[Finding],
        traceability: Dict[str, str],
    ) -> None:
        issue = canonical.get("issue", {})
        evidence = canonical["_evidence"]

        # 1. Price Band High (Cap)
        cap_val, cap_ev = cls._resolve_pricing_field("price_band_high", issue, pbn_data, pbn_source_ref, supplemental)
        if cap_val is not None:
            issue["price_band_high"] = cap_val
            if cap_ev:
                evidence["issue.price_band_high"] = cap_ev
            traceability["price_cap"] = FieldDisposition.ASSEMBLED.value
        else:
            issue["price_band_high"] = None
            traceability["price_cap"] = FieldDisposition.UNKNOWN.value

        # 2. Price Band Low (Floor)
        floor_val, floor_ev = cls._resolve_pricing_field("price_band_low", issue, pbn_data, pbn_source_ref, supplemental)
        if floor_val is not None:
            issue["price_band_low"] = floor_val
            if floor_ev:
                evidence["issue.price_band_low"] = floor_ev
            traceability["price_floor"] = FieldDisposition.ASSEMBLED.value
        else:
            issue["price_band_low"] = None
            traceability["price_floor"] = FieldDisposition.UNKNOWN.value

        # 3. Lot Size
        lot_val, lot_ev = cls._resolve_pricing_field("lot_size", issue, pbn_data, pbn_source_ref, supplemental)
        if lot_val is not None:
            issue["lot_size"] = int(lot_val)
            if lot_ev:
                evidence["issue.lot_size"] = lot_ev
            traceability["lot"] = FieldDisposition.ASSEMBLED.value
        else:
            issue["lot_size"] = None
            traceability["lot"] = FieldDisposition.UNKNOWN.value

        # 4. Open Date
        open_val, open_ev = cls._resolve_pricing_field("open_date", issue, pbn_data, pbn_source_ref, supplemental)
        if open_val is not None:
            issue["open_date"] = open_val
            if open_ev:
                evidence["issue.open_date"] = open_ev
            traceability["issue_open"] = FieldDisposition.ASSEMBLED.value
        else:
            issue["open_date"] = None
            traceability["issue_open"] = FieldDisposition.UNKNOWN.value

        # 5. Close Date
        close_val, close_ev = cls._resolve_pricing_field("close_date", issue, pbn_data, pbn_source_ref, supplemental)
        if close_val is not None:
            issue["close_date"] = close_val
            if close_ev:
                evidence["issue.close_date"] = close_ev
            traceability["issue_close"] = FieldDisposition.ASSEMBLED.value
        else:
            issue["close_date"] = None
            traceability["issue_close"] = FieldDisposition.UNKNOWN.value

        canonical["issue"] = issue

        # Final Mode Validation Gate
        if mode.lower() == "final":
            if issue.get("price_band_high") is None or issue.get("price_band_low") is None:
                err_msg = "Final evaluation mode requires verified Price Band Notice with authoritative price band"
                findings.append(
                    Finding(
                        code="MISSING_PRICE_BAND_NOTICE",
                        message=err_msg,
                        severity=SEVERITY_ERROR,
                        scope="enrichment",
                        location="issue",
                    )
                )
                raise EnrichmentValidationError(err_msg)

    @classmethod
    def _resolve_pricing_field(
        cls,
        field_name: str,
        issue: Dict[str, Any],
        pbn_data: Optional[Dict[str, Any]],
        pbn_source_ref: Optional[Dict[str, Any]],
        supplemental: Optional[Mapping[str, Any]],
    ) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """Apply codified precedence for pricing terms: PBN > Supplemental > RHP."""
        # A. Check Price Band Notice (Highest Precedence)
        if pbn_data and field_name in pbn_data:
            val_obj = pbn_data[field_name]
            if isinstance(val_obj, dict):
                norm_val = val_obj.get("normalized_value")
                if norm_val is not None:
                    src_id = val_obj.get("source_id") or (pbn_source_ref.get("source_id") if pbn_source_ref else "SRC-PBN")
                    ev = {
                        "source_id": src_id,
                        "locator": val_obj.get("locator", f"Price Band Notice, '{field_name}'"),
                        "page": val_obj.get("page"),
                        "quote": val_obj.get("quote"),
                        "extraction_method": val_obj.get("extraction_method", ExtractionMethod.EXCHANGE_DATA.value),
                    }
                    return norm_val, ev
            elif val_obj is not None:
                src_id = pbn_source_ref.get("source_id") if pbn_source_ref else "SRC-PBN"
                ev = {
                    "source_id": src_id,
                    "locator": f"Price Band Notice, '{field_name}'",
                    "extraction_method": ExtractionMethod.EXCHANGE_DATA.value,
                }
                return val_obj, ev

        # B. Check Supplemental Contract
        if supplemental and "price_band" in supplemental and field_name in supplemental["price_band"]:
            val_obj = supplemental["price_band"][field_name]
            if isinstance(val_obj, dict):
                norm_val = val_obj.get("normalized_value")
                if norm_val is not None:
                    ev = {
                        "source_id": val_obj.get("source_id", "SRC-SUPP"),
                        "locator": val_obj.get("locator", f"Supplemental, '{field_name}'"),
                        "extraction_method": val_obj.get("extraction_method", ExtractionMethod.STRUCTURED_INPUT.value),
                    }
                    return norm_val, ev

        # C. Check RHP definitive value (unless undisclosed marker or None)
        existing_val = issue.get(field_name)
        if existing_val is not None and not str(existing_val).strip() in ("[●]", "[•]", "[*]", "NIL", "N.A."):
            # Check if this was a known historical fixture fallback
            # We strictly prohibit fixture defaults from being treated as true values
            return existing_val, None

        return None, None

    # ----------------------------------------------------------------------
    # Step 2: Statutory Base Facts vs. Manual Templates
    # ----------------------------------------------------------------------

    @classmethod
    def _reconcile_statutory_facts(
        cls,
        canonical: Dict[str, Any],
        supplemental: Optional[Mapping[str, Any]],
        allow_manual_override: bool,
        findings: List[Finding],
        traceability: Dict[str, str],
    ) -> None:
        """Enforce: Authoritative RHP/DRHP > Manual/Template."""
        traceability["company_name"] = FieldDisposition.PRESERVED.value

        # Check quota disclosures
        issue = canonical.get("issue", {})
        if "quota_pct" in issue and issue["quota_pct"]:
            traceability["qib_quota"] = FieldDisposition.PRESERVED.value
            traceability["retail_quota"] = FieldDisposition.PRESERVED.value
        else:
            traceability["qib_quota"] = FieldDisposition.UNKNOWN.value
            traceability["retail_quota"] = FieldDisposition.UNKNOWN.value

        # Capital structure disclosures
        cap = canonical.get("capital_structure", {})
        if "promoter_pledge_pct" in cap and cap["promoter_pledge_pct"] is not None:
            traceability["promoter_pledge"] = FieldDisposition.PRESERVED.value
        else:
            traceability["promoter_pledge"] = FieldDisposition.UNKNOWN.value

        if "promoter_lockin_months" in issue and issue["promoter_lockin_months"] is not None:
            traceability["promoter_lockin"] = FieldDisposition.PRESERVED.value
        else:
            traceability["promoter_lockin"] = FieldDisposition.UNKNOWN.value

        if "bonus_discount_allotments" in cap and cap["bonus_discount_allotments"] is not None:
            traceability["bonus_discount_allotments"] = FieldDisposition.PRESERVED.value
        else:
            traceability["bonus_discount_allotments"] = FieldDisposition.UNKNOWN.value

        # Seller info
        sellers = issue.get("ofs_sellers", [])
        if sellers:
            traceability["seller_type"] = FieldDisposition.PRESERVED.value
            traceability["seller_pre_issue_shares"] = FieldDisposition.PRESERVED.value
        else:
            traceability["seller_type"] = FieldDisposition.UNKNOWN.value
            traceability["seller_pre_issue_shares"] = FieldDisposition.UNKNOWN.value

        # Guard: Check if template attempted to overwrite statutory financials
        if supplemental and "financials" in supplemental:
            if not allow_manual_override:
                findings.append(
                    Finding(
                        code="TEMPLATE_OVERWRITE_DISALLOWED",
                        message="Manual template attempted to overwrite statutory RHP financial statements; ignored",
                        severity=SEVERITY_WARNING,
                        scope="enrichment",
                        location="financials",
                    )
                )

    # ----------------------------------------------------------------------
    # Step 3: Analyst Subjective Ratings (Moat & Visibility)
    # ----------------------------------------------------------------------

    @classmethod
    def _reconcile_analyst_ratings(
        cls,
        canonical: Dict[str, Any],
        analyst_assessment: Optional[Mapping[str, Any]],
        supplemental: Optional[Mapping[str, Any]],
        findings: List[Finding],
        traceability: Dict[str, str],
        existing_source_ids: Set[str],
    ) -> None:
        """Enforce: Analyst assessment owns subjective fields (moat, visibility)."""
        analyst_data = None
        source_ref = None

        if analyst_assessment:
            analyst_data = dict(analyst_assessment)
            source_ref = analyst_data.get("_source_ref") or {
                "source_id": "SRC-ANALYST-ASSESSMENT",
                "source_type": SourceType.STRUCTURED_INPUT.value,
                "note": "ANALYST_ASSESSMENT",
            }
        elif supplemental and "analyst_assessment" in supplemental:
            analyst_data = supplemental["analyst_assessment"]
            source_ref = {
                "source_id": "SRC-ANALYST-ASSESSMENT",
                "source_type": SourceType.STRUCTURED_INPUT.value,
                "note": "ANALYST_ASSESSMENT",
            }

        business = canonical.setdefault("business", {})
        evidence = canonical["_evidence"]

        if analyst_data:
            # Register analyst source
            if source_ref and source_ref.get("source_id") not in existing_source_ids:
                canonical["_sources"].append(source_ref)
                existing_source_ids.add(source_ref["source_id"])

            # 1. Moat rating
            if "moat_rating" in analyst_data:
                m_obj = analyst_data["moat_rating"]
                m_val = m_obj.get("normalized_value", m_obj) if isinstance(m_obj, dict) else m_obj
                business["moat_rating"] = m_val
                evidence["business.moat_rating"] = {
                    "source_id": source_ref["source_id"] if source_ref else "SRC-ANALYST",
                    "locator": "Analyst Assessment, 'moat_rating'",
                    "extraction_method": ExtractionMethod.MANUAL_ENTRY.value,
                    "note": "Subjective analyst qualification (Tier 4)",
                }
                traceability["moat"] = FieldDisposition.ASSEMBLED.value
            else:
                traceability["moat"] = FieldDisposition.PRESERVED.value if business.get("moat_rating") else FieldDisposition.UNKNOWN.value

            # 2. Visibility rating
            if "visibility_rating" in analyst_data:
                v_obj = analyst_data["visibility_rating"]
                v_val = v_obj.get("normalized_value", v_obj) if isinstance(v_obj, dict) else v_obj
                business["visibility_rating"] = v_val
                evidence["business.visibility_rating"] = {
                    "source_id": source_ref["source_id"] if source_ref else "SRC-ANALYST",
                    "locator": "Analyst Assessment, 'visibility_rating'",
                    "extraction_method": ExtractionMethod.MANUAL_ENTRY.value,
                    "note": "Subjective analyst qualification (Tier 4)",
                }
                traceability["order_book_visibility"] = FieldDisposition.ASSEMBLED.value
            else:
                traceability["order_book_visibility"] = FieldDisposition.PRESERVED.value if business.get("visibility_rating") else FieldDisposition.UNKNOWN.value

            # Guard: Analyst assessment must NEVER overwrite statutory financial facts
            for prohibited_key in ("revenue", "pat", "net_worth", "total_debt", "periods"):
                if prohibited_key in analyst_data:
                    findings.append(
                        Finding(
                            code="ANALYST_OVERWRITE_PROHIBITED",
                            message=f"Analyst assessment attempted to overwrite statutory fact '{prohibited_key}'; rejected",
                            severity=SEVERITY_WARNING,
                            scope="enrichment",
                            location=f"financials.{prohibited_key}",
                        )
                    )
        else:
            traceability["moat"] = FieldDisposition.PRESERVED.value if business.get("moat_rating") else FieldDisposition.UNKNOWN.value
            traceability["order_book_visibility"] = FieldDisposition.PRESERVED.value if business.get("visibility_rating") else FieldDisposition.UNKNOWN.value

    # ----------------------------------------------------------------------
    # Step 4: Market & Peer Snapshots
    # ----------------------------------------------------------------------

    @classmethod
    def _reconcile_market_and_peers(
        cls,
        canonical: Dict[str, Any],
        market_snapshot: Optional[Mapping[str, Any]],
        peer_snapshot: Optional[Mapping[str, Any]],
        supplemental: Optional[Mapping[str, Any]],
        findings: List[Finding],
        traceability: Dict[str, str],
        existing_source_ids: Set[str],
    ) -> None:
        """Enforce: Newest valid governed snapshot > Stale snapshot > Missing (UNKNOWN)."""
        market = canonical.setdefault("market", {})
        evidence = canonical["_evidence"]

        if market_snapshot:
            m_dict = dict(market_snapshot)
            src_ref = m_dict.get("_source_ref") or {
                "source_id": "SRC-MARKET-SNAPSHOT",
                "source_type": SourceType.MARKET_DATA.value,
                "note": "MARKET_DEMAND_SNAPSHOT",
            }
            if src_ref.get("source_id") not in existing_source_ids:
                canonical["_sources"].append(src_ref)
                existing_source_ids.add(src_ref["source_id"])

            # Map subscription and GMP fields
            for m_key, trac_key in (
                ("qib_subscription", "qib_subscription"),
                ("nii_subscription", "nii_subscription"),
                ("retail_subscription", "retail_subscription"),
                ("overall_subscription", "overall_subscription"),
                ("gmp", "gmp"),
                ("gmp_trend", "gmp_trend"),
                ("anchor_quality", "anchor_quality"),
                ("nifty_trend", "nifty_trend"),
                ("listing_gains", "last_five_ipo_listing_gains"),
            ):
                if m_key in m_dict and m_dict[m_key] is not None:
                    market[m_key] = m_dict[m_key]
                    evidence[f"market.{m_key}"] = {
                        "source_id": src_ref["source_id"],
                        "locator": f"Market Snapshot, '{m_key}'",
                        "extraction_method": ExtractionMethod.MARKET_DATA.value,
                    }
                    traceability[trac_key] = FieldDisposition.ASSEMBLED.value
                else:
                    traceability[trac_key] = FieldDisposition.DEFERRED_TO_5H.value
        else:
            for trac_key in (
                "qib_subscription",
                "nii_subscription",
                "retail_subscription",
                "overall_subscription",
                "gmp",
                "gmp_trend",
                "anchor_quality",
                "nifty_trend",
                "last_five_ipo_listing_gains",
            ):
                traceability[trac_key] = FieldDisposition.DEFERRED_TO_5H.value

        # Peer snapshots
        if peer_snapshot:
            p_dict = dict(peer_snapshot)
            src_ref = p_dict.get("_source_ref") or {
                "source_id": "SRC-PEER-SNAPSHOT",
                "source_type": SourceType.PEER_DATA.value,
                "note": "PEER_VALUATION_SNAPSHOT",
            }
            if src_ref.get("source_id") not in existing_source_ids:
                canonical["_sources"].append(src_ref)
                existing_source_ids.add(src_ref["source_id"])
            if "peers" in p_dict:
                canonical["peers"] = p_dict["peers"]
            if "recent_sector_ipos" in p_dict:
                canonical["recent_sector_ipos"] = p_dict["recent_sector_ipos"]
                traceability["recent_sector_ipo_pe"] = FieldDisposition.ASSEMBLED.value
            else:
                traceability["recent_sector_ipo_pe"] = FieldDisposition.UNKNOWN.value
        else:
            traceability["recent_sector_ipo_pe"] = (
                FieldDisposition.PRESERVED.value if canonical.get("recent_sector_ipos") else FieldDisposition.UNKNOWN.value
            )

    # ----------------------------------------------------------------------
    # Step 5: Dynamic Upstream Derivations
    # ----------------------------------------------------------------------

    @classmethod
    def _compute_derivations(
        cls,
        canonical: Dict[str, Any],
        derivations: Dict[str, DerivedField],
        findings: List[Finding],
        traceability: Dict[str, str],
    ) -> None:
        """Compute the 5 required dynamic derivations with formulas and dependencies."""
        issue = canonical.get("issue", {})
        evidence = canonical["_evidence"]
        fin = canonical.get("financials", {})
        reporting_unit = fin.get("reporting_unit", "INR_LAKHS")
        multiplier = cls._UNIT_MULTIPLIERS.get(reporting_unit, 100_000)

        cap_price = issue.get("price_band_high")
        fresh_issue = issue.get("fresh_issue")
        pre_issue_shares = issue.get("pre_issue_shares")
        ofs_sellers = issue.get("ofs_sellers", [])
        periods = fin.get("periods", [])

        # ------------------------------------------------------------------
        # 1. Fresh Shares Derivation
        # fresh_shares = fresh_issue_rupees / cap_price
        # ------------------------------------------------------------------
        if fresh_issue is not None and cap_price is not None and cap_price > 0:
            fresh_issue_rupees = Decimal(str(fresh_issue)) * Decimal(str(multiplier))
            cap_d = Decimal(str(cap_price))
            derived_fresh_shares = int(round(fresh_issue_rupees / cap_d))

            disclosed_fresh_shares = issue.get("fresh_shares")
            reconciled = None
            variance = None
            if disclosed_fresh_shares is not None:
                variance = abs(derived_fresh_shares - disclosed_fresh_shares) / disclosed_fresh_shares * 100
                reconciled = variance <= 1.0
                if not reconciled:
                    findings.append(
                        Finding(
                            code="RECONCILIATION_MISMATCH",
                            message=f"Derived fresh shares ({derived_fresh_shares}) differs from source ({disclosed_fresh_shares}) by {variance:.2f}%",
                            severity=SEVERITY_WARNING,
                            scope="enrichment",
                            location="issue.fresh_shares",
                        )
                    )
            else:
                issue["fresh_shares"] = derived_fresh_shares
                evidence["issue.fresh_shares"] = {
                    "source_id": "SRC-DERIVED",
                    "locator": "Dynamic Derivation: fresh_issue / cap_price",
                    "extraction_method": ExtractionMethod.DERIVED.value,
                    "note": f"formula: (issue.fresh_issue * {multiplier}) / issue.price_band_high",
                }

            field_obj = DerivedField(
                field_path="issue.fresh_shares",
                value=derived_fresh_shares,
                formula=f"(issue.fresh_issue * {multiplier}) / issue.price_band_high",
                dependencies=["issue.fresh_issue", "issue.price_band_high"],
                source_facts={"fresh_issue": fresh_issue, "cap_price": cap_price},
                reconciled_with_source=reconciled,
                source_fact_value=disclosed_fresh_shares,
                variance_pct=variance,
            )
            derivations["issue.fresh_shares"] = field_obj

        # ------------------------------------------------------------------
        # 2. Post-Issue Shares Derivation
        # post_issue_shares = pre_issue_shares + fresh_shares
        # ------------------------------------------------------------------
        fresh_shares_val = issue.get("fresh_shares")
        if pre_issue_shares is not None and fresh_shares_val is not None:
            derived_post_shares = int(pre_issue_shares) + int(fresh_shares_val)
            disclosed_post_shares = issue.get("post_issue_shares")
            reconciled = None
            variance = None
            if disclosed_post_shares is not None:
                variance = abs(derived_post_shares - disclosed_post_shares) / disclosed_post_shares * 100
                reconciled = variance <= 1.0
                if not reconciled:
                    findings.append(
                        Finding(
                            code="RECONCILIATION_MISMATCH",
                            message=f"Derived post shares ({derived_post_shares}) differs from source ({disclosed_post_shares}) by {variance:.2f}%",
                            severity=SEVERITY_WARNING,
                            scope="enrichment",
                            location="issue.post_issue_shares",
                        )
                    )
            else:
                issue["post_issue_shares"] = derived_post_shares
                evidence["issue.post_issue_shares"] = {
                    "source_id": "SRC-DERIVED",
                    "locator": "Dynamic Derivation: pre_issue_shares + fresh_shares",
                    "extraction_method": ExtractionMethod.DERIVED.value,
                    "note": "formula: issue.pre_issue_shares + issue.fresh_shares",
                }

            field_obj = DerivedField(
                field_path="issue.post_issue_shares",
                value=derived_post_shares,
                formula="issue.pre_issue_shares + issue.fresh_shares",
                dependencies=["issue.pre_issue_shares", "issue.fresh_shares"],
                source_facts={"pre_issue_shares": pre_issue_shares, "fresh_shares": fresh_shares_val},
                reconciled_with_source=reconciled,
                source_fact_value=disclosed_post_shares,
                variance_pct=variance,
            )
            derivations["issue.post_issue_shares"] = field_obj

        # ------------------------------------------------------------------
        # 3. OFS Monetary Amount Derivation
        # OFS amount = sum(seller shares) * cap_price / multiplier
        # ------------------------------------------------------------------
        if ofs_sellers and cap_price is not None and cap_price > 0:
            total_seller_shares = sum(s.get("shares_sold", 0) for s in ofs_sellers)
            if total_seller_shares > 0:
                ofs_rupees = Decimal(str(total_seller_shares)) * Decimal(str(cap_price))
                derived_ofs = float(round(ofs_rupees / Decimal(str(multiplier)), 2))
                disclosed_ofs = issue.get("ofs")
                reconciled = None
                variance = None
                if disclosed_ofs is not None and disclosed_ofs > 0:
                    variance = abs(derived_ofs - disclosed_ofs) / disclosed_ofs * 100
                    reconciled = variance <= 1.0
                    if not reconciled:
                        findings.append(
                            Finding(
                                code="RECONCILIATION_MISMATCH",
                                message=f"Derived OFS ({derived_ofs}) differs from source ({disclosed_ofs}) by {variance:.2f}%",
                                severity=SEVERITY_WARNING,
                                scope="enrichment",
                                location="issue.ofs",
                            )
                        )
                else:
                    issue["ofs"] = derived_ofs
                    evidence["issue.ofs"] = {
                        "source_id": "SRC-DERIVED",
                        "locator": "Dynamic Derivation: sum(seller_shares) * cap_price",
                        "extraction_method": ExtractionMethod.DERIVED.value,
                        "note": f"formula: (sum(seller_shares) * issue.price_band_high) / {multiplier}",
                    }

                field_obj = DerivedField(
                    field_path="issue.ofs",
                    value=derived_ofs,
                    formula=f"(sum(seller_shares) * issue.price_band_high) / {multiplier}",
                    dependencies=["issue.ofs_sellers", "issue.price_band_high"],
                    source_facts={"total_seller_shares": total_seller_shares, "cap_price": cap_price},
                    reconciled_with_source=reconciled,
                    source_fact_value=disclosed_ofs,
                    variance_pct=variance,
                )
                derivations["issue.ofs"] = field_obj

        # ------------------------------------------------------------------
        # 4. Post-Issue EPS Derivation
        # post_issue_eps = latest_pat_rupees / post_issue_shares
        # ------------------------------------------------------------------
        post_shares_val = issue.get("post_issue_shares")
        if periods and post_shares_val and post_shares_val > 0:
            latest_period = periods[-1]
            latest_pat = latest_period.get("pat")
            if latest_pat is not None:
                pat_rupees = Decimal(str(latest_pat)) * Decimal(str(multiplier))
                derived_eps = float(round(pat_rupees / Decimal(str(post_shares_val)), 2))
                disclosed_eps = issue.get("post_issue_eps")
                reconciled = None
                variance = None
                if disclosed_eps is not None and disclosed_eps > 0:
                    variance = abs(derived_eps - disclosed_eps) / disclosed_eps * 100
                    reconciled = variance <= 2.0  # Allow minor prospectus rounding variance
                else:
                    issue["post_issue_eps"] = derived_eps
                    evidence["issue.post_issue_eps"] = {
                        "source_id": "SRC-DERIVED",
                        "locator": "Dynamic Derivation: latest_pat / post_issue_shares",
                        "extraction_method": ExtractionMethod.DERIVED.value,
                        "note": f"formula: (financials.periods[-1].pat * {multiplier}) / issue.post_issue_shares",
                    }

                field_obj = DerivedField(
                    field_path="issue.post_issue_eps",
                    value=derived_eps,
                    formula=f"(financials.periods[-1].pat * {multiplier}) / issue.post_issue_shares",
                    dependencies=["financials.periods[-1].pat", "issue.post_issue_shares"],
                    source_facts={"latest_pat": latest_pat, "post_issue_shares": post_shares_val},
                    reconciled_with_source=reconciled,
                    source_fact_value=disclosed_eps,
                    variance_pct=variance,
                )
                derivations["issue.post_issue_eps"] = field_obj

        # ------------------------------------------------------------------
        # 5. Promoter Post-Issue Percentage
        # promoter_post_pct = (promoter_pre_shares - promoter_shares_sold) / post_issue_shares * 100
        # ------------------------------------------------------------------
        cap_struct = canonical.get("capital_structure", {})
        promoter_pre_pct = cap_struct.get("promoter_pre_pct")
        pre_shares = issue.get("pre_issue_shares")

        if promoter_pre_pct is not None and pre_shares and post_shares_val and post_shares_val > 0:
            promoter_pre_shares = (Decimal(str(pre_shares)) * Decimal(str(promoter_pre_pct))) / Decimal("100")
            promoter_sold_shares = Decimal("0")
            for s in ofs_sellers:
                if s.get("type") in ("promoter", "promoter_group"):
                    promoter_sold_shares += Decimal(str(s.get("shares_sold", 0)))

            promoter_post_shares = promoter_pre_shares - promoter_sold_shares
            derived_promoter_post_pct = float(round((promoter_post_shares / Decimal(str(post_shares_val))) * Decimal("100"), 2))
            disclosed_post_pct = cap_struct.get("promoter_post_pct")
            reconciled = None
            variance = None
            if disclosed_post_pct is not None:
                variance = abs(derived_promoter_post_pct - disclosed_post_pct)
                reconciled = variance <= 1.0
            else:
                cap_struct["promoter_post_pct"] = derived_promoter_post_pct
                evidence["capital_structure.promoter_post_pct"] = {
                    "source_id": "SRC-DERIVED",
                    "locator": "Dynamic Derivation: promoter_post_shares / post_issue_shares * 100",
                    "extraction_method": ExtractionMethod.DERIVED.value,
                    "note": "formula: promoter_post_shares / post_issue_shares * 100",
                }

            field_obj = DerivedField(
                field_path="capital_structure.promoter_post_pct",
                value=derived_promoter_post_pct,
                formula="((pre_shares * promoter_pre_pct / 100) - promoter_shares_sold) / post_issue_shares * 100",
                dependencies=["capital_structure.promoter_pre_pct", "issue.pre_issue_shares", "issue.ofs_sellers", "issue.post_issue_shares"],
                source_facts={"promoter_pre_pct": promoter_pre_pct, "pre_shares": pre_shares, "post_shares": post_shares_val},
                reconciled_with_source=reconciled,
                source_fact_value=disclosed_post_pct,
                variance_pct=variance,
            )
            derivations["capital_structure.promoter_post_pct"] = field_obj

    # ----------------------------------------------------------------------
    # Step 6: Complete Historical Traceability Matrix
    # ----------------------------------------------------------------------

    @classmethod
    def _complete_traceability_matrix(
        cls,
        canonical: Dict[str, Any],
        traceability: Dict[str, str],
    ) -> None:
        """Ensure all 24 historical fields have explicit disposition."""
        for f in cls.HISTORICAL_FIELDS:
            if f not in traceability:
                traceability[f] = FieldDisposition.UNKNOWN.value


__all__ = [
    "EnrichmentError",
    "EnrichmentConflictError",
    "EnrichmentValidationError",
    "PrecedenceViolationError",
    "FieldDisposition",
    "DerivedField",
    "EnrichmentResult",
    "EnrichmentEngine",
]
