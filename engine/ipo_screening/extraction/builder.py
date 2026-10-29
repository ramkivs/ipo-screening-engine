"""Canonical JSON input builder from RawExtractions.

Technical Design v1.5 s3.2, s15:
  Merges parsed field extractions into the canonical v1.5 input schema
  (schema/ipo-input.v1.5.schema.json), attaching strict provenance
  (_sources, _evidence) and preserving fail-closed nulls for unreadable
  or undisclosed fields.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from .directorate import count_exits
from .interfaces import RawExtraction, SourceDocument
from .rpt_categories import (
    REVENUE_CATEGORIES,
    is_consolidation_eliminated,
    is_revenue_category,
)


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

        coverage = self._build_coverage()
        if coverage:
            output["coverage"] = coverage

        self._attach_derived_eps_evidence(output)

        if "market" in self.base:
            output["market"] = self.base["market"]
        if "recent_sector_ipos" in self.base:
            output["recent_sector_ipos"] = self.base["recent_sector_ipos"]

        return output

    def _attach_derived_eps_evidence(self, output: Dict[str, Any]) -> None:
        """Record how a derived post-issue EPS was formed.

        A number the engine computed must never look like a number the filing
        printed.  The derivation is written to ``_evidence`` with the inputs it
        used, so the Explorer (and the semantic validator) can tell a disclosed
        figure from a derived one and can recompute it.
        """
        if output.get("issue", {}).get("post_issue_eps_basis") != "derived":
            return
        note = getattr(self, "_derived_eps_note", None)
        evidence = output.get("_evidence") or {}
        if "issue.post_issue_eps" in evidence:
            return
        evidence["issue.post_issue_eps"] = {
            "evidence_id": "EV-issue-post_issue_eps",
            "source_id": self.doc.source_id,
            "locator": "Derived by the engine (not printed in the filing)",
            "extraction_method": "DERIVED",
            "extraction_confidence": 0.9,
            "note": note
            or (
                "derived: latest full-year PAT / post-issue shares; no post-issue earnings figure "
                "was found in the sections read"
            ),
        }
        output["_evidence"] = evidence

    def _build_coverage(self) -> Dict[str, str]:
        """Collect `coverage.<...>` extraction results into the inputs map.

        Each reader that can distinguish "read it, nothing there" from
        "never read it" emits a string-valued RawExtraction on a
        `coverage.` path.  Those are stripped out of the ordinary field
        tree here so they never collide with real input fields.
        """
        coverage: Dict[str, str] = {}
        for ex in self.extractions:
            path = ex.field_path or ""
            if not path.startswith("coverage."):
                continue
            value = str(ex.candidate_value or "").strip().upper()
            if value in {"DISCLOSED", "VERIFIED_NIL", "PARTIAL", "UNREAD"}:
                coverage[path[len("coverage."):]] = value
        derived = getattr(self, "_kmp_exits_coverage", None)
        if derived and "governance.kmp_exits_2y" not in coverage:
            coverage["governance.kmp_exits_2y"] = derived
        return coverage

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

    @classmethod
    def _canonical_unit(cls, unit: Optional[str]) -> Optional[str]:
        """Normalise a unit label ("millions", "INR_LAKHS", "Rs") to its code."""
        if not unit:
            return None
        text = str(unit).strip()
        if not text:
            return None
        upper = text.upper().replace(".", "")
        if upper in cls._AMOUNT_UNIT_TO_RUPEES:
            return upper
        return cls._AMOUNT_UNIT_WORDS.get(upper, upper)

    @classmethod
    def _normalize_issue_amount(
        cls,
        value: Any,
        raw_unit: Optional[str],
        reporting_unit: Optional[str],
    ) -> Any:
        """Express an extracted issue amount in the filing's reporting unit.

        One conversion, at one boundary.  A candidate with no unit, or whose
        unit already is the reporting unit, is returned unchanged; an amount
        whose unit cannot be converted is withheld rather than guessed at,
        because a wrong magnitude is worse than an unknown value.
        """
        if value is None:
            return None
        source = cls._canonical_unit(raw_unit)
        if source is None:
            return value  # no stated unit: already canonical, never scaled
        target = cls._canonical_unit(reporting_unit)
        if source not in cls._AMOUNT_UNIT_TO_RUPEES or target not in cls._AMOUNT_UNIT_TO_RUPEES:
            return None
        if source == target:
            return value
        return round(
            float(value) * cls._AMOUNT_UNIT_TO_RUPEES[source] / cls._AMOUNT_UNIT_TO_RUPEES[target],
            2,
        )

    def _reporting_unit(self) -> Optional[str]:
        """The filing's monetary reporting unit (as the financials are built)."""
        fin_base = self.base.get("financials", {})
        if "reporting_unit" in fin_base:
            return fin_base["reporting_unit"]
        return self._get_field("financials.reporting_unit", "INR_LAKHS")

    def _pick_issue_amount(self, key: str, default: Any = None) -> Any:
        """An issue monetary amount, expressed in the reporting unit."""
        issue_base = self.base.get("issue", {})
        if key in issue_base:
            # A reference/manual input is already in the canonical unit.
            return issue_base[key]
        extraction = next(
            (ex for ex in self.extractions if ex.field_path == f"issue.{key}"),
            None,
        )
        if extraction is None:
            return default
        return self._normalize_issue_amount(
            extraction.candidate_value, extraction.raw_unit, self._reporting_unit()
        )

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
        # Basis of the figure, so the number is never anonymous.  A value the
        # reader took from the filing's own post-issue disclosure is
        # ``disclosed``; a value the engine formed is ``derived`` and carries a
        # derivation note in _evidence.  A value supplied by a curated input
        # that predates this field keeps no basis (reconciled by the validator).
        eps_basis: Optional[str] = None
        if post_eps is not None:
            if self._get_field("issue.post_issue_eps") is not None:
                eps_basis = "disclosed"
        else:
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
                    eps_basis = "derived"
                    self._derived_eps_note = (
                        f"derived: latest full-year PAT {latest_pat} {unit} x "
                        f"{factor:,.0f} / post-issue shares {post_shares:,} = {post_eps} "
                        f"({latest_p.get('fy') or 'latest period'}); no post-issue earnings figure "
                        "was found in the sections read, and a historical basic/diluted EPS on the "
                        "weighted-average count is not the same quantity"
                    )
        if post_eps is None and self.allow_fixture_fallbacks:
            post_eps = default_eps
            eps_basis = None

        res: Dict[str, Any] = {
            "price_band_low": _pick_issue("price_band_low", default_low),
            "price_band_high": _pick_issue("price_band_high", default_high),
            "lot_size": _pick_issue("lot_size", default_lot),
            "fresh_issue": self._pick_issue_amount("fresh_issue", default_fresh),
            "ofs": self._pick_issue_amount("ofs", default_ofs),
            "fresh_shares": fresh_shares,
            "post_issue_shares": post_shares,
            "pre_issue_shares": pre_shares,
            "post_issue_eps": post_eps,
            "open_date": _pick_issue("open_date", default_open),
            "close_date": _pick_issue("close_date", default_close),
        }
        if eps_basis is not None and post_eps is not None:
            res["post_issue_eps_basis"] = eps_basis

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
        for name in (
            "operating_cash_flow_3yr_cumulative", "net_income_3yr_cumulative",
            "trade_receivables_days", "net_working_capital_pct_revenue",
            "top_customer_revenue_pct", "loss_making_segments_present",
        ):
            value = fin_base.get(name) if name in fin_base else self._get_field(f"financials.{name}", None)
            if value is not None:
                result[name] = value
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
        # Evidence or UNKNOWN -- never a favourable constant.
        #
        # A pledge of 0.0%, a lock-in "in place", "no early unlock" and "no
        # discounted allotments" were all *defaults*: when the filing was not
        # read, the builder supplied the answer that scores best (K2's pledge
        # limb, the C `lockin` criterion and the discounted-allotment penalty
        # were all cleared without evidence).  The extracted value is used when
        # it exists; otherwise the field stays absent and the dependent metric
        # is UNKNOWN.  Where the filing does disclose the fact, the readers in
        # ``sections.py`` now emit it with a verbatim quotation.
        def _cap_value(key: str, fallback: Any = None) -> Any:
            if key in cap_base:
                return cap_base[key]
            return self._get_field(f"capital_structure.{key}", fallback)

        fixture = self.allow_fixture_fallbacks
        pledge_pct = _cap_value("promoter_pledge_pct", 0.0 if fixture else None)
        lockin = _cap_value("promoter_lockin_in_place", True if fixture else None)

        return {
            "promoter_pre_pct": pre_pct,
            "promoter_post_pct": post_pct,
            "promoter_pledge_pct": pledge_pct,
            "promoter_lockin_in_place": lockin,
            "large_holders_unlocked_early": _cap_value(
                "large_holders_unlocked_early", False if fixture else None
            ),
            "pre_ipo_placements": _cap_value("pre_ipo_placements", []),
            "discounted_allotments_18m_before_drhp": _cap_value(
                "discounted_allotments_18m_before_drhp", False if fixture else None
            ),
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
            # Evidence or UNKNOWN: a board composition that was never read is
            # not a non-independent board.
            "board_independent_majority": _pick_gov(
                "board_independent_majority", False if self.allow_fixture_fallbacks else None
            ),
            "kmp_exits_2y": _pick_gov("kmp_exits_2y", None),
        }
        # Schema-permitted governance inputs that a penalty/knockout consumes
        # must not be dropped.  ``auditor_or_cfo_exit_2y`` drives the
        # auditor/CFO-exit penalty; it was previously read by the derived
        # metric but never carried into the canonical input, so the penalty
        # was structurally UNKNOWN for every builder-based evaluation.  The
        # key is added only when the input/extraction establishes it, so the
        # absent case remains UNKNOWN (and the golden input is unchanged).
        for optional_key in (
            "auditor_or_cfo_exit_2y",
            "promoter_pledged_shares_pct",
            "pre_issue_promoter_holding_pct",
            "professionally_managed_without_identifiable_promoters",
        ):
            if optional_key in gov_base:
                gov[optional_key] = gov_base[optional_key]
            else:
                extracted = self._get_field(f"governance.{optional_key}", None)
                if extracted is not None:
                    gov[optional_key] = extracted
        self._derive_rpt_metrics(gov)
        self._derive_board_changes(gov)
        return gov

    def _derive_board_changes(self, gov: Dict[str, Any]) -> None:
        """Carry the directorate events through, and count exits in window.

        ``kmp_exits_2y`` is no longer taken on trust from whatever the reader
        happened to leave behind.  When the changes-in-directorate table was
        read, the events are persisted on ``governance.board_changes`` and the
        count is derived here against the offer open date, so the same
        canonical record always re-derives the same count.  When the table was
        *not* read, the count stays ``None`` (UNKNOWN) and the coverage state
        records why -- an unread section is never a zero.

        Only the two states that establish the count keep a number:

        * ``DISCLOSED``  -- rows read; the window decides the count;
        * ``VERIFIED_NIL`` -- the filing positively states there were no
          changes, so zero exits is a verified zero.
        """
        events = self._get_field("governance.board_changes")
        if events is None:
            events = gov.get("board_changes")
        if isinstance(events, list) and events:
            gov["board_changes"] = events
        elif "board_changes" not in gov:
            gov.pop("board_changes", None)

        state = self._get_field("coverage.governance.board_changes")
        base_has_value = "kmp_exits_2y" in self.base.get("governance", {})

        if state not in ("DISCLOSED", "VERIFIED_NIL"):
            # The reader established nothing about the directorate section.
            # A curated input value is then left exactly as supplied, with no
            # coverage claim either way (legacy/v1.5 behaviour); otherwise the
            # field stays UNKNOWN -- never zero.
            if base_has_value:
                return
            gov["kmp_exits_2y"] = None
            if state is not None:
                self._kmp_exits_coverage = state
            return

        if state == "VERIFIED_NIL" and isinstance(events, list) and not events:
            gov["kmp_exits_2y"] = 0
            self._kmp_exits_coverage = "VERIFIED_NIL"
            return

        # The 24-month window is anchored on the date the offer opens -- never
        # on the ingestion date, the retrieval date or "today".  When the filing
        # has not disclosed the open date, the next date on the same offer
        # timeline is used, and the count is reported as PARTIAL rather than
        # DISCLOSED: a later anchor starts the window later, so it can only
        # narrow the window the rule defines.
        anchor_raw = None
        anchor_is_open_date = False
        for field in ("open_date", "close_date", "listing_date"):
            candidate = self._get_field("issue.%s" % field) or self.base.get(
                "issue", {}
            ).get(field)
            if not candidate:
                continue
            try:
                anchor = datetime.date.fromisoformat(str(candidate)[:10])
            except ValueError:
                continue
            anchor_raw = candidate
            anchor_is_open_date = field == "open_date"
            break
        else:
            anchor = None
        count = count_exits(events or [], anchor)
        if count is None:
            # No offer date to anchor the window: the count is not established.
            gov["kmp_exits_2y"] = None
            self._kmp_exits_coverage = "PARTIAL"
        elif not anchor_is_open_date:
            gov["kmp_exits_2y"] = count
            self._kmp_exits_coverage = "PARTIAL"
        else:
            gov["kmp_exits_2y"] = count
            self._kmp_exits_coverage = "DISCLOSED" if count else "VERIFIED_NIL"

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
    #
    # Numerator basis — owner decision, 2026-10-27 (report s.35): the
    # metric is a *consolidated-basis* share.  A related-party figure the
    # disclosure states is eliminated in consolidation is therefore never
    # part of the numerator, because consolidated revenue cannot contain
    # it; a year whose qualifying amount the note does not state has no
    # share (no zero substitution); and where the latest year's qualifying
    # consolidated-basis revenue cannot be established the fields stay null
    # (UNKNOWN).  A standalone-basis exposure measure is a separate metric
    # with its own standalone revenue denominator and is not implemented
    # here.
    # Imported from the shared nature vocabulary (extraction/rpt_categories.py)
    # rather than restated here, so a reader that recognises a new revenue
    # nature cannot silently disagree with the numerator about what may be
    # counted.  The contents are unchanged: the four categories the approved
    # definition names.
    _RPT_SALES_SERVICES_CATEGORIES = REVENUE_CATEGORIES
    _ISSUE_UNIT_TO_RUPEES = {
        "INR_LAKHS": 1e5,
        "INR_CRORES": 1e7,
        "INR_MILLIONS": 1e6,
        "INR_BILLIONS": 1e9,
    }

    # ------------------------------------------------------------------
    # Issue monetary units
    # ------------------------------------------------------------------
    # The canonical input contract states that ``issue.fresh_issue`` and
    # ``issue.ofs`` are "in reporting_unit" (schema/ipo-input.v1.5.schema.json),
    # and every downstream consumer multiplies by the reporting unit's rupee
    # factor (``enrichment_engine`` derives fresh shares as
    # ``fresh_issue * multiplier / cap_price``).  The *document*, however,
    # states the money in its own unit -- a filed RHP commonly prints
    # "AGGREGATING UP TO ₹ 5,000.00 MILLION" while its financial statements are
    # in lakhs.  Writing the document's number straight into a lakh-denominated
    # field made ₹5,000 million (50,000 lakh) read as ₹5,000 lakh: a tenfold
    # magnitude error that was invisible because the label said lakhs.
    #
    # Conversion therefore happens exactly once, here, when the canonical input
    # is assembled -- the earliest point at which the filing's reporting unit
    # is known.  Extraction keeps the document's own wording in ``raw_unit``,
    # so no component can convert twice: a candidate whose unit already equals
    # the reporting unit, or that states no unit at all, is left untouched.
    _AMOUNT_UNIT_WORDS = {
        "LAKH": "INR_LAKHS",
        "LAKHS": "INR_LAKHS",
        "CRORE": "INR_CRORES",
        "CRORES": "INR_CRORES",
        "MILLION": "INR_MILLIONS",
        "MILLIONS": "INR_MILLIONS",
        "BILLION": "INR_BILLIONS",
        "BILLIONS": "INR_BILLIONS",
        "THOUSAND": "INR_THOUSANDS",
        "THOUSANDS": "INR_THOUSANDS",
        "RUPEE": "INR",
        "RUPEES": "INR",
        "RS": "INR",
        "INR": "INR",
    }
    _AMOUNT_UNIT_TO_RUPEES = {
        **_ISSUE_UNIT_TO_RUPEES,
        "INR_THOUSANDS": 1e3,
        "INR": 1.0,
    }

    _RPT_UNIT_TO_RUPEES = {
        "INR_LAKHS": 1e5,
        "INR_CRORES": 1e7,
        "INR_MILLIONS": 1e6,
        "INR_BILLIONS": 1e9,
    }

    # The verbatim text a related-party row may carry, in the order the
    # readers set them.  Used only to recognise a disclosure that says the
    # figure is eliminated in consolidation.
    _RPT_EVIDENCE_TEXT_KEYS = (
        "category_label",
        "nature",
        "description",
        "heading",
        "block_label",
    )

    @classmethod
    def _rpt_is_sales_services(cls, category: str) -> bool:
        return is_revenue_category(category)

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
        # A revenue-type row is still not eligible when the disclosure says the
        # figure is eliminated in consolidation: this metric is divided by
        # *consolidated* revenue, which by construction cannot contain
        # eliminated intra-group revenue (owner decision 2026-10-27, report
        # s.35).  The exclusion reads the row's own verbatim text, never a
        # category name, and an issuer name appears nowhere.
        eligible = [
            t
            for t in txns
            if self._rpt_is_sales_services(str(t.get("category") or ""))
            and not is_consolidation_eliminated(
                *(t.get(key) for key in self._RPT_EVIDENCE_TEXT_KEYS)
            )
        ]
        if not eligible:
            return
        sums: Dict[int, float] = {}
        for txn in eligible:
            unit = txn.get("unit")
            amount = txn.get("amount")
            if unit not in self._RPT_UNIT_TO_RUPEES or not isinstance(amount, (int, float)):
                return  # unconvertible/insufficient evidence: fail closed
            m = re.match(r"FY(20\d{2})$", str(txn.get("period") or ""))
            if m is None:
                # A column that is not a financial year -- the interim "three
                # months ended 30 June 2026" column of a period-matrix
                # disclosure (report section 30) -- is a known period that
                # carries no annual share.  It is skipped, not treated as an
                # unknown period, so an interim column cannot suppress the
                # annual share the note does disclose.
                continue
            year = int(m.group(1))
            converted = amount * self._RPT_UNIT_TO_RUPEES[unit] / self._RPT_UNIT_TO_RUPEES[reporting_unit]
            sums[year] = sums.get(year, 0.0) + converted
        # Only years for which the note discloses an eligible amount have a
        # numerator.  Absence of a disclosed amount is *missing evidence*, not a
        # disclosed nil, so no year is filled in with zero (owner decision
        # 2026-10-27, report s.35): a share is computed only where the note
        # states the amount, and the metric is left null where the latest year's
        # qualifying revenue cannot be established.
        shares: Dict[int, float] = {}
        for year, revenue in periods.items():
            if year in sums:
                shares[year] = sums[year] / revenue * 100.0
        latest = max(periods)
        if latest not in shares:
            return
        prior_years = [y for y in periods if y < latest]
        prior = max(prior_years) if prior_years else None
        if gov.get("rpt_pct_revenue") is None:
            gov["rpt_pct_revenue"] = round(shares[latest], 4)
        if gov.get("rpt_pct_of_revenue_growth") is None and prior is not None and prior in shares:
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
