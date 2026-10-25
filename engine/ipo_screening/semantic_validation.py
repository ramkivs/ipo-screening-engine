"""Semantic, financial, cross-source and provenance validation.

Spec v1.5 s20 lists the required checks and tech design s4 splits them into
structural, semantic and financial/source layers. Validation is a hard gate:
errors stop scoring, warnings are recorded and carried into the evaluation
record so they remain visible.

Coverage:

  * share-count arithmetic (fresh + OFS against post-issue shares);
  * post-issue EPS reconciliation;
  * PBT / tax / PAT relationship;
  * balance-sheet sanity (net worth vs debt);
  * periods ordered and unique;
  * financial periods three or more, cyclical profile five or more;
  * percentages in range, share counts non-negative;
  * proceeds limits (GCP >25%, unidentified acquisition >25%, combined >35%);
  * OFS 6(2) selling limits;
  * peer listing age and staleness;
  * market block staleness;
  * evidence/provenance presence for material scored inputs;
  * GCP ``[●]`` semantics (the ceiling must not be recorded as the amount).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .canonical import EvidenceRegistry, parse_date
from .canonical_input import CanonicalInput, unprovenanced_paths
from .errors import Finding, SEVERITY_ERROR, SEVERITY_WARNING, SemanticValidationError
from .snapshots import MarketSnapshot, PeerSnapshot

MATERIAL_PREFIXES: Tuple[str, ...] = (
    "issue",
    "financials",
    "capital_structure",
    "governance",
    "business",
    "peers",
    "use_of_proceeds",
    "market",
)


@dataclass
class ValidationReport:
    findings: List[Finding] = field(default_factory=list)

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_ERROR]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": [f.to_dict() for f in self.errors],
            "warnings": [f.to_dict() for f in self.warnings],
        }

    def extend(self, findings: Sequence[Finding]) -> None:
        self.findings.extend(findings)


def _num(raw: Any) -> Optional[float]:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def _err(code: str, message: str, location: Optional[str] = None, **detail: Any) -> Finding:
    return Finding(code=code, message=message, severity=SEVERITY_ERROR, scope="semantic", location=location, detail=detail)


def _warn(code: str, message: str, location: Optional[str] = None, **detail: Any) -> Finding:
    return Finding(code=code, message=message, severity=SEVERITY_WARNING, scope="semantic", location=location, detail=detail)


def validate_semantics(
    canonical: CanonicalInput,
    config: Mapping[str, Any],
    peers: PeerSnapshot,
    market: MarketSnapshot,
) -> ValidationReport:
    """Run every semantic check and return the combined report."""
    report = ValidationReport()
    raw = canonical.raw
    issue = raw.get("issue") or {}
    financials = raw.get("financials") or {}

    # -- 1. periods ordered and unique -------------------------------------
    periods = financials.get("periods") or []
    labels = [str(p.get("fy", "")) for p in periods]
    if len(labels) != len(set(labels)):
        report.findings.append(
            _err(
                "PERIODS_DUPLICATE",
                f"financial periods contain duplicate labels: {labels}",
                "financials.periods",
            )
        )
    full_periods = [p for p in periods if not p.get("is_stub")]
    if len(full_periods) < 3:
        report.findings.append(
            _err(
                "PERIODS_INSUFFICIENT",
                f"at least three full FY observations are required; {len(full_periods)} supplied",
                "financials.periods",
            )
        )
    if canonical.sector_profile == "cyclical" and len(full_periods) < 5:
        report.findings.append(
            _err(
                "PERIODS_CYCLICAL_INSUFFICIENT",
                f"the cyclical profile requires five FY observations; {len(full_periods)} supplied",
                "financials.periods",
            )
        )
    for period in periods:
        fy = str(period.get("fy", ""))
        for field_name in ("revenue", "pat", "net_worth", "total_debt", "cfo"):
            value = _num(period.get(field_name))
            if value is None:
                continue
            if field_name == "revenue" and value < 0:
                report.findings.append(
                    _err("FINANCIAL_NEGATIVE_REVENUE", f"{fy}: revenue is negative ({value})", f"financials.periods.{fy}")
                )

    # -- 2. PBT / tax / PAT relationship -----------------------------------
    for period in periods:
        pbt, tax, pat = (_num(period.get(k)) for k in ("pbt", "tax", "pat"))
        if pbt is None or tax is None or pat is None:
            continue
        if abs((pbt - tax) - pat) > max(0.01, abs(pat) * 0.01):
            report.findings.append(
                _warn(
                    "FINANCIAL_PAT_RECONCILIATION",
                    f"{period.get('fy')}: PBT ({pbt}) - tax ({tax}) = {pbt - tax}, which does not "
                    f"reconcile to PAT ({pat}) within 1%",
                    f"financials.periods.{period.get('fy')}",
                )
            )

    # -- 3. EBITDA reproducibility -----------------------------------------
    for period in periods:
        ebitda, ebit, dep = (_num(period.get(k)) for k in ("ebitda", "ebit", "depreciation"))
        if ebitda is None or ebit is None or dep is None:
            continue
        if abs((ebit + dep) - ebitda) > max(0.05, abs(ebitda) * 0.02):
            report.findings.append(
                _warn(
                    "FINANCIAL_EBITDA_RECONCILIATION",
                    f"{period.get('fy')}: EBIT ({ebit}) + depreciation ({dep}) = {ebit + dep}, which "
                    f"does not reconcile to the disclosed EBITDA ({ebitda}) within 2%",
                    f"financials.periods.{period.get('fy')}",
                )
            )

    # -- 4. share-count arithmetic -----------------------------------------
    fresh_shares = _num(issue.get("fresh_shares"))
    post_shares = _num(issue.get("post_issue_shares"))
    pre_shares = _num(issue.get("pre_issue_shares"))
    seller_shares = sum(_num(s.get("shares_sold")) or 0.0 for s in issue.get("ofs_sellers") or [])
    if fresh_shares is not None and pre_shares is not None and post_shares is not None:
        expected = pre_shares + fresh_shares
        if abs(expected - post_shares) > max(1.0, abs(post_shares) * 0.005):
            report.findings.append(
                _warn(
                    "SHARE_COUNT_ARITHMETIC",
                    f"pre-issue shares ({pre_shares}) + fresh shares ({fresh_shares}) = {expected}, "
                    f"which does not reconcile to post-issue shares ({post_shares}) within 0.5%",
                    "issue.post_issue_shares",
                )
            )
    if seller_shares and fresh_shares is not None and post_shares is not None and pre_shares is not None:
        implied_post = pre_shares + fresh_shares
        if abs(implied_post - post_shares) > max(1.0, abs(post_shares) * 0.005):
            report.findings.append(
                _warn(
                    "OFS_SHARE_COUNT",
                    "the selling shareholders' offered shares were not used to reconcile the "
                    "post-issue count",
                    "issue.ofs_sellers",
                )
            )

    # -- 5. post-issue EPS sanity ------------------------------------------
    eps = _num(issue.get("post_issue_eps"))
    latest = canonical.latest
    if eps is not None and latest is not None:
        pat = latest.get("pat")
        if pat is not None and post_shares:
            implied = pat * 1e7 / post_shares
            if implied > 0 and abs(implied - eps) > max(0.05, eps * 0.10):
                report.findings.append(
                    _warn(
                        "POST_ISSUE_EPS_RECONCILIATION",
                        f"latest PAT over the post-issue share count implies an EPS of "
                        f"{implied:.4f}, which differs from the supplied post-issue EPS of {eps} by "
                        "more than 10%",
                        "issue.post_issue_eps",
                    )
                )

    # -- 6. seller shares cannot exceed the seller's holding ---------------
    for seller in issue.get("ofs_sellers") or []:
        pre, sold = _num(seller.get("pre_issue_shares")), _num(seller.get("shares_sold"))
        name = seller.get("name", "<unnamed>")
        if pre is not None and sold is not None and sold > pre:
            report.findings.append(
                _err(
                    "SELLER_OVERSELL",
                    f"seller {name!r} offers {sold} shares but held only {pre} pre-issue",
                    "issue.ofs_sellers",
                )
            )

    # -- 7. percentage ranges ----------------------------------------------
    for path, value in _percentage_fields(raw):
        if value is not None and not (-1000 <= value <= 10000):
            report.findings.append(
                _err("PERCENT_OUT_OF_RANGE", f"{path} is {value}, outside the permitted range", path)
            )

    # -- 8. proceeds limits -------------------------------------------------
    limits = (config.get("validation") or {}).get("proceeds_limits_pct_of_fresh", {})
    fresh_issue = canonical.money("issue", "fresh_issue")
    if fresh_issue and fresh_issue > 0:
        totals: Dict[str, float] = {}
        undisclosed: Dict[str, bool] = {}
        for entry in canonical.use_of_proceeds():
            category = str(entry.get("category"))
            amount = _num(entry.get("amount"))
            if amount is None:
                undisclosed[category] = True
                continue
            # Proceeds are stated in the reporting unit; normalise before
            # comparing them with the fresh issue, which is in INR crore.
            totals[category] = totals.get(category, 0.0) + amount * canonical.unit_factor
        gcp = totals.get("gcp", 0.0)
        unidentified = totals.get("acquisition_unidentified", 0.0)
        if "gcp" in undisclosed:
            report.findings.append(
                _warn(
                    "GCP_UNDISCLOSED",
                    "the general corporate purposes amount is undisclosed in the RHP; the 25% ICDR "
                    "ceiling is recorded separately as a limit and is not treated as the amount",
                    "use_of_proceeds.gcp",
                )
            )
        else:
            gcp_max = float(limits.get("gcp_max", 25))
            if gcp / fresh_issue * 100.0 > gcp_max:
                report.findings.append(
                    _err(
                        "PROCEEDS_GCP_LIMIT",
                        f"GCP of {gcp} is {gcp / fresh_issue * 100.0:.2f}% of the fresh issue, "
                        f"above the {gcp_max}% ICDR limit",
                        "use_of_proceeds.gcp",
                    )
                )
        una_max = float(limits.get("unidentified_acquisition_max", 25))
        if unidentified / fresh_issue * 100.0 > una_max:
            report.findings.append(
                _err(
                    "PROCEEDS_UNIDENTIFIED_LIMIT",
                    f"unidentified acquisitions of {unidentified} exceed {una_max}% of the fresh issue",
                    "use_of_proceeds",
                )
            )
        combined_max = float(limits.get("combined_max", 35))
        if (gcp + unidentified) / fresh_issue * 100.0 > combined_max:
            report.findings.append(
                _err(
                    "PROCEEDS_COMBINED_LIMIT",
                    f"GCP plus unidentified acquisitions exceed the {combined_max}% combined limit",
                    "use_of_proceeds",
                )
            )

    report.extend(_validate_ofs_route(canonical, config))

    # -- 9. cross-source tolerance -----------------------------------------
    tolerance = float((config.get("validation") or {}).get("source_cross_check_tolerance_pct", 5))
    report.extend(_cross_source_checks(canonical, tolerance))

    # -- 10. peers ----------------------------------------------------------
    for observation in peers.observations:
        if observation.status == "MISSING":
            report.findings.append(
                _warn(
                    "PEER_MULTIPLES_MISSING",
                    f"peer {observation.name!r} supplies no valuation multiple",
                    "peers",
                )
            )
        elif observation.status == "STALE":
            report.findings.append(
                _warn(
                    "PEER_MULTIPLES_STALE",
                    f"peer {observation.name!r}: {observation.reason}. The dependent valuation "
                    "criteria are treated as UNKNOWN rather than scored on stale data.",
                    "peers",
                )
            )
        elif observation.status == "UNUSABLE":
            report.findings.append(
                _warn(
                    "PEER_UNUSABLE",
                    f"peer {observation.name!r} is unusable: {observation.reason}",
                    "peers",
                )
            )
    if not peers.has_valid():
        report.findings.append(
            _warn(
                "PEER_SET_NO_VALID_ENTRIES",
                "no VALID peer remains, so every valuation criterion is UNKNOWN and the score "
                "range widens accordingly",
                "peers",
            )
        )

    # -- 11. market staleness ----------------------------------------------
    for block in market.blocks:
        if block.status != "FRESH":
            report.findings.append(
                _warn(
                    "MARKET_BLOCK_UNUSABLE",
                    f"market block {block.name!r} is {block.status}"
                    + (f": {block.reason}" if block.reason else ""),
                    f"market.{block.name}",
                )
            )

    # -- 12. GCP cannot be the ceiling -------------------------------------
    report.extend(_validate_gcp_semantics(canonical, config))

    # -- 13. evidence and provenance ---------------------------------------
    report.extend(_validate_provenance(canonical, config))

    return report


def _percentage_fields(raw: Mapping[str, Any]) -> List[Tuple[str, Optional[float]]]:
    out: List[Tuple[str, Optional[float]]] = []
    for key, value in (raw.get("capital_structure") or {}).items():
        if key.endswith("_pct"):
            out.append((f"capital_structure.{key}", _num(value)))
    for key, value in (raw.get("governance") or {}).items():
        if key.endswith("_pct"):
            out.append((f"governance.{key}", _num(value)))
    for key, value in (raw.get("business") or {}).items():
        if key.endswith("_pct"):
            out.append((f"business.{key}", _num(value)))
    return out


def _validate_ofs_route(canonical: CanonicalInput, config: Mapping[str, Any]) -> List[Finding]:
    """OFS 6(2) selling limits (spec s20 'OFS')."""
    findings: List[Finding] = []
    if canonical.icdr_route != "6(2)":
        return findings
    limits = (config.get("validation") or {}).get("ofs_6_2_limits_pct_of_holding", {})
    for seller in canonical.issue().get("ofs_sellers") or []:
        pre = _num(seller.get("pre_issue_shares"))
        sold = _num(seller.get("shares_sold"))
        holding_pct = _num(seller.get("holding_pct_pre_issue"))
        if pre is None or sold is None or pre <= 0:
            continue
        pct_sold = sold / pre * 100.0
        if holding_pct is None:
            findings.append(
                _warn(
                    "OFS_6_2_HOLDING_UNKNOWN",
                    f"seller {seller.get('name')!r} has no pre-issue holding percentage, so the "
                    "6(2) selling limit cannot be checked",
                    "issue.ofs_sellers",
                )
            )
            continue
        cap = (
            float(limits.get("holder_gt_20pct_max_sell", 50))
            if holding_pct > 20
            else float(limits.get("holder_lt_20pct_max_sell", 10))
        )
        if pct_sold > cap:
            findings.append(
                _err(
                    "OFS_6_2_BREACH",
                    f"seller {seller.get('name')!r} sold {pct_sold:.2f}% of its pre-issue holding, "
                    f"above the {cap}% limit for a holder of {holding_pct}% on the 6(2) route",
                    "issue.ofs_sellers",
                )
            )
    return findings


def _cross_source_checks(canonical: CanonicalInput, tolerance_pct: float) -> List[Finding]:
    """Compare restated values against any declared secondary source values."""
    findings: List[Finding] = []
    cross_checks = canonical.raw.get("_cross_checks") or []
    for index, check in enumerate(cross_checks):
        primary = _num(check.get("primary"))
        secondary = _num(check.get("secondary"))
        label = check.get("field", f"cross_check[{index}]")
        if primary is None or secondary is None:
            findings.append(
                _warn(
                    "CROSS_SOURCE_INCOMPLETE",
                    f"cross-source check for {label!r} is missing one of its values, so it cannot be "
                    "performed",
                    "_cross_checks",
                )
            )
            continue
        if primary == 0:
            continue
        delta_pct = abs(secondary - primary) / abs(primary) * 100.0
        if delta_pct > tolerance_pct:
            findings.append(
                _warn(
                    "CROSS_SOURCE_DIVERGENCE",
                    f"{label}: the RHP value {primary} differs from the secondary source value "
                    f"{secondary} by {delta_pct:.2f}%, beyond the {tolerance_pct}% tolerance. The "
                    "difference is reported, not silently resolved.",
                    "_cross_checks",
                    primary=primary,
                    secondary=secondary,
                    delta_pct=delta_pct,
                )
            )
    return findings


def _validate_gcp_semantics(canonical: CanonicalInput, config: Mapping[str, Any]) -> List[Finding]:
    """Spec s10/s13: the GCP ceiling must never be recorded as the amount."""
    findings: List[Finding] = []
    gcp_cfg = config.get("gcp") or {}
    legal_pct = float(gcp_cfg.get("legal_max_pct_of_fresh_offer", 25))
    fresh = canonical.money("issue", "fresh_issue")
    entries = [u for u in canonical.use_of_proceeds() if u.get("category") == "gcp"]
    if not entries or fresh is None or fresh <= 0:
        return findings
    ceiling = fresh * legal_pct / 100.0
    for entry in entries:
        raw_amount = _num(entry.get("amount"))
        if raw_amount is None:
            continue
        amount = raw_amount * canonical.unit_factor
        if abs(amount - ceiling) < 1e-6:
            findings.append(
                _err(
                    "GCP_CEILING_RECORDED_AS_AMOUNT",
                    f"the recorded GCP amount ({amount}) equals exactly {legal_pct}% of the fresh "
                    "issue, which is the ICDR legal ceiling. Spec s10/s13 requires an undisclosed "
                    "GCP to be recorded as UNKNOWN with the ceiling held separately; a ceiling that "
                    "has been written in as the amount must be corrected.",
                    "use_of_proceeds.gcp",
                    amount=amount,
                    ceiling=ceiling,
                )
            )
    return findings


def _validate_provenance(canonical: CanonicalInput, config: Mapping[str, Any]) -> List[Finding]:
    """Spec s3.4 / s24: material scored inputs must be traceable to evidence."""
    findings: List[Finding] = []
    if not canonical.registry.sources:
        findings.append(
            _warn(
                "PROVENANCE_NO_SOURCES",
                "no source documents are declared on the input, so scored values cannot be traced to "
                "a source. Evidence and provenance are required before scoring (spec s3.4).",
                "_sources",
            )
        )
    unprovenanced = [
        p for p in unprovenanced_paths(canonical) if p.split(".")[0].split("[")[0] in MATERIAL_PREFIXES
    ]
    if unprovenanced:
        findings.append(
            _warn(
                "PROVENANCE_MISSING_FOR_FIELDS",
                f"{len(unprovenanced)} material input field(s) carry no evidence reference, for "
                f"example {unprovenanced[:8]}. Each scored input should identify its source, "
                "as-of date, document/page and extraction method (spec s3.4).",
                "_evidence",
                count=len(unprovenanced),
                examples=unprovenanced[:20],
            )
        )
    for evidence in canonical.registry.evidence_items:
        if not evidence.locator:
            findings.append(
                _warn(
                    "EVIDENCE_NO_LOCATOR",
                    f"evidence {evidence.evidence_id!r} has no page, table or section locator, so the "
                    "engine cannot answer which page supplied the value (spec s24)",
                    "_evidence",
                )
            )
    return findings


def enforce_semantics(
    canonical: CanonicalInput,
    config: Mapping[str, Any],
    peers: PeerSnapshot,
    market: MarketSnapshot,
) -> ValidationReport:
    """Run semantic validation and raise on any error-level finding."""
    report = validate_semantics(canonical, config, peers, market)
    if not report.ok:
        raise SemanticValidationError(report.errors)
    return report


__all__ = ["ValidationReport", "validate_semantics", "enforce_semantics", "MATERIAL_PREFIXES"]
