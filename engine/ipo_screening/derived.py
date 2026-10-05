"""Deterministic derived-metrics engine.

Tech design s5: derived metrics are pure functions
``derive(input_snapshot, config) -> derived_metrics`` with no source access,
no mutation and **no default-to-zero**. Each metric returns a value, a
status, a formula and the inputs it consumed.

Spec v1.5 s3.2 and s8 in particular:
  * UNKNOWN must stay UNKNOWN - it is never converted to ``0`` so that a
    formula can evaluate;
  * the CFO/PAT metric is the cumulative ratio ``sum(CFO) / sum(PAT)`` and is
    *not* the arithmetic average of yearly ratios;
  * revenue growth is ``revenue_cagr_2y_from_3fy`` - three FY observations
    give a two-year CAGR, and the engine must not label it a 3-year CAGR;
  * ROCE is EBIT / (total equity + total borrowings), per the RHP's own
    "Basis for Offer Price" definition, overridden by a disclosed ROCE.

Every value carries the formula and input list that produced it so the
engine can answer "what formula produced this metric?" (spec s24).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .canonical import State, parse_date
from .canonical_input import CanonicalInput, FinancialPeriod
from .snapshots import MARKET_FRESH, PEER_VALID, MarketSnapshot, PeerSnapshot

UNKNOWN = State.UNKNOWN.value
NOT_APPLICABLE = State.NOT_APPLICABLE.value
VALUE = State.VALUE.value


@dataclass(frozen=True)
class MetricValue:
    """A derived metric with its state, formula, inputs and explanation."""

    metric_id: str
    state: str
    value: Any = None
    kind: str = "numeric"  # numeric | categorical | boolean
    formula: str = ""
    inputs: Tuple[str, ...] = ()
    reason: str = ""
    evidence_refs: Tuple[str, ...] = ()

    @property
    def is_value(self) -> bool:
        return self.state == VALUE

    @property
    def is_unknown(self) -> bool:
        return self.state == UNKNOWN

    @property
    def is_not_applicable(self) -> bool:
        return self.state == NOT_APPLICABLE

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "metric_id": self.metric_id,
            "state": self.state,
            "kind": self.kind,
            "formula": self.formula,
        }
        if self.value is not None:
            out["value"] = self.value
        if self.inputs:
            out["inputs"] = list(self.inputs)
        if self.reason:
            out["reason"] = self.reason
        if self.evidence_refs:
            out["evidence_refs"] = list(self.evidence_refs)
        return out


def _v(
    metric_id: str,
    value: Any,
    *,
    kind: str = "numeric",
    formula: str = "",
    inputs: Sequence[str] = (),
    reason: str = "",
    evidence_refs: Sequence[str] = (),
) -> MetricValue:
    return MetricValue(
        metric_id=metric_id,
        state=VALUE,
        value=value,
        kind=kind,
        formula=formula,
        inputs=tuple(inputs),
        reason=reason,
        evidence_refs=tuple(evidence_refs),
    )


def _u(
    metric_id: str,
    reason: str,
    *,
    kind: str = "numeric",
    formula: str = "",
    inputs: Sequence[str] = (),
) -> MetricValue:
    return MetricValue(
        metric_id=metric_id, state=UNKNOWN, kind=kind, formula=formula, inputs=tuple(inputs), reason=reason
    )


def _na(
    metric_id: str,
    reason: str,
    *,
    kind: str = "numeric",
    formula: str = "",
    inputs: Sequence[str] = (),
) -> MetricValue:
    return MetricValue(
        metric_id=metric_id,
        state=NOT_APPLICABLE,
        kind=kind,
        formula=formula,
        inputs=tuple(inputs),
        reason=reason,
    )


# --------------------------------------------------------------------------
# Derivation context
# --------------------------------------------------------------------------


@dataclass
class DerivationContext:
    canonical: CanonicalInput
    config: Mapping[str, Any]
    peers: PeerSnapshot
    market: MarketSnapshot
    evaluation_datetime: datetime

    # -- shorthands --------------------------------------------------------

    @property
    def thresholds(self) -> Mapping[str, Any]:
        return self.config.get("thresholds", {})

    @property
    def periods(self) -> Tuple[FinancialPeriod, ...]:
        return self.canonical.full_periods

    def p(self, key: str) -> Optional[float]:
        """Latest full-FY value for *key*, or ``None`` when absent."""
        latest = self.canonical.latest
        return latest.get(key) if latest else None

    @staticmethod
    def all_present(values: Sequence[Optional[float]]) -> bool:
        return all(v is not None for v in values)


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

REGISTRY: Dict[str, Callable[[DerivationContext], MetricValue]] = {}


def metric(metric_id: str) -> Callable[
    [Callable[[DerivationContext], MetricValue]], Callable[[DerivationContext], MetricValue]
]:
    def decorate(fn: Callable[[DerivationContext], MetricValue]) -> Callable[[DerivationContext], MetricValue]:
        if metric_id in REGISTRY:
            raise ValueError(f"metric {metric_id!r} registered twice")
        REGISTRY[metric_id] = fn
        return fn

    return decorate


# --------------------------------------------------------------------------
# Financials
# --------------------------------------------------------------------------


@metric("pat_latest")
def _pat_latest(ctx: DerivationContext) -> MetricValue:
    value = ctx.p("pat")
    if value is None:
        return _u("pat_latest", "latest full-FY PAT is not disclosed", inputs=["financials.periods"])
    return _v(
        "pat_latest",
        value,
        formula="PAT of latest restated full FY (INR_CRORES)",
        inputs=["financials.periods"],
    )


@metric("net_worth_latest")
def _net_worth_latest(ctx: DerivationContext) -> MetricValue:
    value = ctx.p("net_worth")
    if value is None:
        return _u(
            "net_worth_latest",
            "latest full-FY net worth is not disclosed",
            inputs=["financials.periods"],
        )
    return _v(
        "net_worth_latest",
        value,
        formula="net worth of latest restated full FY (INR_CRORES)",
        inputs=["financials.periods"],
    )


def _cagr(ctx: DerivationContext, metric_id: str, field_name: str, years: int) -> MetricValue:
    periods = ctx.periods
    required = years + 1
    formula = (
        f"(({field_name}[latest] / {field_name}[latest-{years}]) ^ (1/{years}) - 1) * 100"
    )
    inputs = ["financials.periods"]
    if len(periods) < required:
        return _u(
            metric_id,
            f"{required} full FY observations are required for a {years}-year CAGR; "
            f"{len(periods)} supplied",
            formula=formula,
            inputs=inputs,
        )
    end = periods[-1].get(field_name)
    start = periods[-1 - years].get(field_name)
    if end is None or start is None:
        return _u(
            metric_id,
            f"{field_name} is not disclosed for one of the observations required by the "
            f"{years}-year CAGR",
            formula=formula,
            inputs=inputs,
        )
    if start <= 0 or end <= 0:
        return _na(
            metric_id,
            f"{field_name} must be positive at both ends of the window for a CAGR to be "
            "meaningful",
            formula=formula,
            inputs=inputs,
        )
    return _v(metric_id, (math.pow(end / start, 1.0 / years) - 1.0) * 100.0, formula=formula, inputs=inputs)


@metric("revenue_cagr_2y_from_3fy")
def _revenue_cagr_2y_from_3fy(ctx: DerivationContext) -> MetricValue:
    return _cagr(ctx, "revenue_cagr_2y_from_3fy", "revenue", 2)


@metric("revenue_cagr_3y_from_4fy")
def _revenue_cagr_3y_from_4fy(ctx: DerivationContext) -> MetricValue:
    return _cagr(ctx, "revenue_cagr_3y_from_4fy", "revenue", 3)


@metric("pat_cagr_2y_from_3fy")
def _pat_cagr_2y_from_3fy(ctx: DerivationContext) -> MetricValue:
    return _cagr(ctx, "pat_cagr_2y_from_3fy", "pat", 2)


def _margins(ctx: DerivationContext, numerator: str) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for period in ctx.periods:
        revenue = period.get("revenue")
        top = period.get(numerator)
        if revenue is None or top is None or revenue == 0:
            out.append(None)
        else:
            out.append(top / revenue * 100.0)
    return out


def _margin_trend_from(
    ebitda_margins: Sequence[Optional[float]],
    pat_margins: Sequence[Optional[float]],
    metric_id: str,
    latest_pat: Optional[float],
) -> MetricValue:
    formula = (
        "expanding: EBITDA and PAT margin both up each year; declining_or_loss: latest PAT<=0 "
        "or both margins down; volatile: direction flips with range >300 bps; else stable"
    )
    inputs = ["financials.periods"]
    if any(m is None for m in list(ebitda_margins) + list(pat_margins)):
        return _u(
            metric_id,
            "one or more EBITDA or PAT margins are not derivable, so the trend cannot be "
            "established",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if len(ebitda_margins) < 2:
        return _u(
            metric_id,
            "at least two full FY observations are required to establish a margin trend",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    de = [ebitda_margins[i + 1] - ebitda_margins[i] for i in range(len(ebitda_margins) - 1)]
    dp = [pat_margins[i + 1] - pat_margins[i] for i in range(len(pat_margins) - 1)]
    if (latest_pat is not None and latest_pat <= 0) or (
        all(x < 0 for x in de) and all(x < 0 for x in dp)
    ):
        bucket = "declining_or_loss"
    elif all(x > 0 for x in de) and all(x > 0 for x in dp):
        bucket = "expanding"
    elif (
        any(x > 0 for x in de)
        and any(x < 0 for x in de)
        and (max(ebitda_margins) - min(ebitda_margins)) > 3
    ):
        bucket = "volatile"
    else:
        bucket = "stable"
    return _v(metric_id, bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("margin_trend")
def _margin_trend(ctx: DerivationContext) -> MetricValue:
    return _margin_trend_from(
        _margins(ctx, "ebitda"), _margins(ctx, "pat"), "margin_trend", ctx.p("pat")
    )


@metric("margin_trend_5y_avg")
def _margin_trend_5y_avg(ctx: DerivationContext) -> MetricValue:
    periods = ctx.periods[-5:]
    formula = "cyclical override: margin_trend computed on 5-FY average margins"
    if len(periods) < 5:
        return _u(
            "margin_trend_5y_avg",
            f"the cyclical profile requires 5 FY observations; {len(periods)} supplied",
            kind="categorical",
            formula=formula,
            inputs=["financials.periods"],
        )
    ebitda, pat = [], []
    for period in periods:
        revenue = period.get("revenue")
        if revenue is None or revenue == 0:
            return _u(
                "margin_trend_5y_avg",
                "revenue is missing for one of the five observations",
                kind="categorical",
                formula=formula,
                inputs=["financials.periods"],
            )
        if period.get("ebitda") is None or period.get("pat") is None:
            return _u(
                "margin_trend_5y_avg",
                "EBITDA or PAT is missing for one of the five observations",
                kind="categorical",
                formula=formula,
                inputs=["financials.periods"],
            )
        ebitda.append(period.get("ebitda") / revenue * 100.0)
        pat.append(period.get("pat") / revenue * 100.0)
    return _margin_trend_from(ebitda, pat, "margin_trend_5y_avg", ctx.p("pat"))


@metric("roce_latest")
def _roce_latest(ctx: DerivationContext) -> MetricValue:
    formula = (
        "ROCE = EBIT / Capital Employed, where Capital Employed = total equity + total "
        "borrowings (RHP 'Basis for Offer Price' definitions); a disclosed ROCE overrides"
    )
    inputs = ["financials.periods"]
    latest = ctx.canonical.latest
    if latest is None:
        return _u("roce_latest", "no full FY observation supplied", formula=formula, inputs=inputs)

    disclosed = latest.get("disclosed_roce_pct")
    if disclosed is not None:
        return _v(
            "roce_latest",
            disclosed,
            formula=formula,
            inputs=inputs,
            reason="disclosed ROCE in the restated financials takes precedence over the computed value",
        )

    ebit = latest.get("ebit")
    equity = latest.get("net_worth")
    debt = latest.get("total_debt")
    missing = [
        name
        for name, value in (("EBIT", ebit), ("net worth", equity), ("total debt", debt))
        if value is None
    ]
    if missing:
        return _u(
            "roce_latest",
            "cannot compute ROCE because {} is not disclosed".format(", ".join(missing)),
            formula=formula,
            inputs=inputs,
        )
    capital_employed = equity + debt
    if capital_employed <= 0:
        return _na(
            "roce_latest",
            "capital employed is non-positive, so ROCE is not meaningful",
            formula=formula,
            inputs=inputs,
        )
    return _v("roce_latest", ebit / capital_employed * 100.0, formula=formula, inputs=inputs)


@metric("cfo_pat_cumulative")
def _cfo_pat_cumulative(ctx: DerivationContext) -> MetricValue:
    formula = (
        "sum(CFO over the full FY observations) / sum(PAT over the same observations); "
        "a cumulative ratio, not the arithmetic mean of annual CFO/PAT ratios"
    )
    inputs = ["financials.periods"]
    periods = ctx.periods
    if not periods:
        return _u("cfo_pat_cumulative", "no full FY observation supplied", formula=formula, inputs=inputs)
    cfo_values = [p.get("cfo") for p in periods]
    pat_values = [p.get("pat") for p in periods]
    if any(v is None for v in cfo_values) or any(v is None for v in pat_values):
        return _u(
            "cfo_pat_cumulative",
            "CFO or PAT is not disclosed for every observation in the window, so the "
            "cumulative ratio cannot be formed",
            formula=formula,
            inputs=inputs,
        )
    total_cfo = sum(cfo_values)
    total_pat = sum(pat_values)
    if total_pat <= 0:
        return _na(
            "cfo_pat_cumulative",
            "cumulative PAT is non-positive, so the ratio is not meaningful (it is not "
            "forced to zero)",
            formula=formula,
            inputs=inputs,
        )
    return _v("cfo_pat_cumulative", total_cfo / total_pat, formula=formula, inputs=inputs)


@metric("leverage_bucket")
def _leverage_bucket(ctx: DerivationContext) -> MetricValue:
    formula = (
        "strong: D/E<0.5 and ICR>5; ok: D/E<1; stretched: 1<=D/E<=2; weak: D/E>2"
    )
    inputs = ["financials.periods"]
    latest = ctx.canonical.latest
    if latest is None:
        return _u("leverage_bucket", "no full FY observation supplied", kind="categorical", formula=formula, inputs=inputs)
    equity = latest.get("net_worth")
    debt = latest.get("total_debt")
    if equity is None or debt is None:
        return _u(
            "leverage_bucket",
            "net worth or total debt is not disclosed, so D/E cannot be established",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if equity <= 0:
        return _u(
            "leverage_bucket",
            "net worth is non-positive, so D/E is not a meaningful leverage measure here",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    de = debt / equity

    interest = latest.get("interest_expense")
    if de < 0.5:
        # The "strong" band additionally requires interest cover > 5x.
        if interest is None:
            return _u(
                "leverage_bucket",
                "D/E is below 0.5 but interest expense is not disclosed, so interest cover "
                "cannot be established and the strong band cannot be confirmed",
                kind="categorical",
                formula=formula,
                inputs=inputs,
            )
        if interest == 0:
            if debt == 0:
                return _v(
                    "leverage_bucket",
                    "strong",
                    kind="categorical",
                    formula=formula + "; ICR is NOT_APPLICABLE for a debt-free balance sheet",
                    inputs=inputs,
                    reason="no borrowings and no finance cost: there is no debt service to cover",
                )
            return _u(
                "leverage_bucket",
                "finance cost is zero while borrowings are outstanding, which is not "
                "internally consistent; interest cover cannot be established",
                kind="categorical",
                formula=formula,
                inputs=inputs,
            )
        icr = (latest.get("ebit") if latest.get("ebit") is not None else latest.get("ebitda"))
        if icr is None:
            return _u(
                "leverage_bucket",
                "interest cover cannot be computed because neither EBIT nor EBITDA is disclosed",
                kind="categorical",
                formula=formula,
                inputs=inputs,
            )
        icr = icr / interest
        return _v("leverage_bucket", "strong" if icr > 5 else "ok", kind="categorical", formula=formula, inputs=inputs)

    if de < 1:
        bucket = "ok"
    elif de <= 2:
        bucket = "stretched"
    else:
        bucket = "weak"
    return _v("leverage_bucket", bucket, kind="categorical", formula=formula, inputs=inputs)


# --------------------------------------------------------------------------
# Valuation
# --------------------------------------------------------------------------


def _issue_price(canonical: CanonicalInput) -> Optional[float]:
    return _as_float(canonical.issue().get("price_band_high"))


def _as_float(raw: Any) -> Optional[float]:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def _market_cap(ctx: DerivationContext) -> Optional[float]:
    price = _issue_price(ctx.canonical)
    shares = _as_float(ctx.canonical.issue().get("post_issue_shares"))
    if price is None or shares is None:
        return None
    # Shares are in absolute units; price is INR per share. Result in INR crore.
    return price * shares / 1e7


def _issuer_pe(ctx: DerivationContext) -> Optional[float]:
    price = _issue_price(ctx.canonical)
    eps = _as_float(ctx.canonical.issue().get("post_issue_eps"))
    if price is None or eps is None or eps <= 0:
        return None
    return price / eps


def _issuer_ev_ebitda(ctx: DerivationContext) -> Optional[float]:
    mcap = _market_cap(ctx)
    latest = ctx.canonical.latest
    if mcap is None or latest is None:
        return None
    debt, cash, ebitda = latest.get("total_debt"), latest.get("cash_and_equivalents"), latest.get("ebitda")
    if debt is None or cash is None or ebitda is None or ebitda <= 0:
        return None
    return (mcap + debt - cash) / ebitda


def _issuer_pb(ctx: DerivationContext) -> Optional[float]:
    mcap = _market_cap(ctx)
    latest = ctx.canonical.latest
    if mcap is None or latest is None:
        return None
    equity = latest.get("net_worth")
    fresh = ctx.canonical.money("issue", "fresh_issue") or 0.0
    if equity is None or (equity + fresh) <= 0:
        return None
    return mcap / (equity + fresh)


def _issuer_ps(ctx: DerivationContext) -> Optional[float]:
    mcap = _market_cap(ctx)
    latest = ctx.canonical.latest
    if mcap is None or latest is None:
        return None
    revenue = latest.get("revenue")
    if revenue is None or revenue <= 0:
        return None
    return mcap / revenue


def _premium_pct(value: Optional[float], peer_median: Optional[float]) -> Optional[float]:
    if value is None or peer_median in (None, 0):
        return None
    return (value / peer_median - 1.0) * 100.0


def _peer_blocked_reason(ctx: DerivationContext) -> str:
    rejected = ctx.peers.rejected
    details = "; ".join(f"{p.name}: {p.status} ({p.reason})" for p in rejected)
    return (
        "no VALID peer multiple is available; valuation cannot be scored as current. "
        f"Rejected peers: {details or 'none supplied'}"
    )


@metric("pe_premium_pct")
def _pe_premium_pct(ctx: DerivationContext) -> MetricValue:
    formula = "(issue price / post-issue EPS) / (median VALID peer P/E) - 1, x100"
    inputs = ["issue.price_band_high", "issue.post_issue_eps", "peers"]
    issuer_pe = _issuer_pe(ctx)
    if issuer_pe is None:
        return _u(
            "pe_premium_pct",
            "issue P/E cannot be computed because the price band or the post-issue EPS is not "
            "disclosed",
            formula=formula,
            inputs=inputs,
        )
    median = ctx.peers.median("pe")
    if median is None:
        return _u("pe_premium_pct", _peer_blocked_reason(ctx), formula=formula, inputs=inputs)
    return _v("pe_premium_pct", _premium_pct(issuer_pe, median), formula=formula, inputs=inputs)


@metric("second_multiple_premium_pct")
def _second_multiple_premium_pct(ctx: DerivationContext) -> MetricValue:
    formula = "issuer EV/EBITDA vs the median VALID peer EV/EBITDA; P/B if EBITDA is not meaningful"
    inputs = ["peers", "financials.periods"]
    peer_ev = ctx.peers.median("ev_ebitda")
    issuer_ev = _issuer_ev_ebitda(ctx)
    if peer_ev is not None and issuer_ev is not None:
        return _v("second_multiple_premium_pct", _premium_pct(issuer_ev, peer_ev), formula=formula, inputs=inputs)
    peer_pb = ctx.peers.median("pb")
    issuer_pb = _issuer_pb(ctx)
    if peer_pb is not None and issuer_pb is not None:
        return _v(
            "second_multiple_premium_pct",
            _premium_pct(issuer_pb, peer_pb),
            formula=formula + "; fell back to P/B because EV/EBITDA was not meaningful",
            inputs=inputs,
        )
    return _u("second_multiple_premium_pct", _peer_blocked_reason(ctx), formula=formula, inputs=inputs)


@metric("pb_roe_adjusted_premium_pct")
def _pb_roe_adjusted_premium_pct(ctx: DerivationContext) -> MetricValue:
    formula = "issuer P/B divided by the ROE-adjusted median VALID peer P/B - 1, x100"
    inputs = ["peers", "financials.periods"]
    issuer_pb = _issuer_pb(ctx)
    peer_pb = ctx.peers.median("pb")
    peer_roe = ctx.peers.median("roe_pct")
    latest = ctx.canonical.latest
    issuer_roe = latest.get("roe_pct") if latest else None
    if issuer_roe is None and latest is not None:
        equity, pat = latest.get("net_worth"), latest.get("pat")
        if equity and equity > 0 and pat is not None:
            issuer_roe = pat / equity * 100.0
    if issuer_pb is None or peer_pb is None or peer_roe in (None, 0) or issuer_roe is None:
        return _u(
            "pb_roe_adjusted_premium_pct",
            "the ROE-adjusted P/B comparison needs issuer P/B, issuer ROE and peer P/B and ROE; "
            + _peer_blocked_reason(ctx),
            formula=formula,
            inputs=inputs,
        )
    # Scale the peer multiple to the issuer's ROE so like is compared with like.
    adjusted_peer_pb = peer_pb * (issuer_roe / peer_roe)
    return _v(
        "pb_roe_adjusted_premium_pct",
        _premium_pct(issuer_pb, adjusted_peer_pb),
        formula=formula,
        inputs=inputs,
    )


@metric("peg")
def _peg(ctx: DerivationContext) -> MetricValue:
    formula = "post-issue P/E / PAT CAGR (2Y from 3 FY), %"
    inputs = ["issue.price_band_high", "issue.post_issue_eps", "financials.periods"]
    issuer_pe = _issuer_pe(ctx)
    growth = REGISTRY["pat_cagr_2y_from_3fy"](ctx)
    if issuer_pe is None:
        return _u("peg", "post-issue P/E cannot be computed", formula=formula, inputs=inputs)
    if not growth.is_value:
        return _u(
            "peg",
            f"PAT CAGR is unavailable ({growth.state}: {growth.reason}), so PEG cannot be formed",
            formula=formula,
            inputs=inputs,
        )
    if growth.value <= 0:
        return _na(
            "peg",
            "PAT CAGR is non-positive, so PEG is not meaningful",
            formula=formula,
            inputs=inputs,
        )
    return _v("peg", issuer_pe / growth.value, formula=formula, inputs=inputs)


@metric("low_base_year")
def _low_base_year(ctx: DerivationContext) -> MetricValue:
    formula = "earliest-year PAT margin < low_base_margin_ratio x latest-year PAT margin"
    inputs = ["financials.periods"]
    margins = _margins(ctx, "pat")
    if any(m is None for m in margins) or len(margins) < 2:
        return _u(
            "low_base_year",
            "PAT margins are not derivable for every FY observation",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    ratio = float(ctx.thresholds.get("low_base_margin_ratio", 0.5))
    return _v(
        "low_base_year",
        bool(margins[0] < ratio * margins[-1]),
        kind="boolean",
        formula=formula,
        inputs=inputs,
    )


@metric("sector_ipo_relative")
def _sector_ipo_relative(ctx: DerivationContext) -> MetricValue:
    formula = (
        "post-issue P/E vs the median of the last 4 same-sector IPOs: cheaper below -band, "
        "richer above +band, else in_line"
    )
    inputs = ["recent_sector_ipos"]
    issuer_pe = _issuer_pe(ctx)
    raw = ctx.canonical.raw.get("recent_sector_ipos") or []
    pes = [_as_float(item.get("pe_at_issue")) for item in raw]
    pes = [x for x in pes if x is not None]
    if issuer_pe is None:
        return _u(
            "sector_ipo_relative",
            "post-issue P/E cannot be computed",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if not pes:
        return _u(
            "sector_ipo_relative",
            "no recent same-sector IPO valuations were supplied, so the relative test cannot "
            "be evaluated",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    band = float(ctx.thresholds.get("sector_ipo_band_pct", 10))
    median = float(statistics.median(pes))
    if issuer_pe < median * (1 - band / 100.0):
        bucket = "cheaper"
    elif issuer_pe > median * (1 + band / 100.0):
        bucket = "richer"
    else:
        bucket = "in_line"
    return _v("sector_ipo_relative", bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("pe_premium_mid_cycle_pct")
def _pe_premium_mid_cycle_pct(ctx: DerivationContext) -> MetricValue:
    formula = "pe_premium_pct recomputed against mid-cycle (5-FY average) earnings"
    inputs = ["peers", "financials.periods"]
    periods = ctx.periods[-5:]
    if len(periods) < 5:
        return _u(
            "pe_premium_mid_cycle_pct",
            "the cyclical profile needs 5 FY observations to form a mid-cycle multiple",
            formula=formula,
            inputs=inputs,
        )
    pats = [p.get("pat") for p in periods]
    shares = _as_float(ctx.canonical.issue().get("post_issue_shares"))
    price = _issue_price(ctx.canonical)
    if any(p is None for p in pats) or shares is None or price is None:
        return _u(
            "pe_premium_mid_cycle_pct",
            "mid-cycle EPS cannot be formed because a 5-FY PAT series, the share count or the "
            "price band is unavailable",
            formula=formula,
            inputs=inputs,
        )
    avg_pat = sum(pats) / len(pats)
    eps = avg_pat * 1e7 / shares
    if eps <= 0:
        return _na(
            "pe_premium_mid_cycle_pct",
            "mid-cycle EPS is non-positive",
            formula=formula,
            inputs=inputs,
        )
    median = ctx.peers.median("pe")
    if median is None:
        return _u("pe_premium_mid_cycle_pct", _peer_blocked_reason(ctx), formula=formula, inputs=inputs)
    return _v("pe_premium_mid_cycle_pct", _premium_pct(price / eps, median), formula=formula, inputs=inputs)


@metric("ev_ebitda_mid_cycle_premium_pct")
def _ev_ebitda_mid_cycle_premium_pct(ctx: DerivationContext) -> MetricValue:
    formula = "second_multiple_premium_pct recomputed against mid-cycle (5-FY average) EBITDA"
    inputs = ["peers", "financials.periods"]
    periods = ctx.periods[-5:]
    mcap = _market_cap(ctx)
    latest = ctx.canonical.latest
    if len(periods) < 5 or mcap is None or latest is None:
        return _u(
            "ev_ebitda_mid_cycle_premium_pct",
            "a mid-cycle EV/EBITDA needs 5 FY observations, a market cap and a balance sheet",
            formula=formula,
            inputs=inputs,
        )
    ebitdas = [p.get("ebitda") for p in periods]
    debt, cash = latest.get("total_debt"), latest.get("cash_and_equivalents")
    if any(e is None for e in ebitdas) or debt is None or cash is None:
        return _u(
            "ev_ebitda_mid_cycle_premium_pct",
            "EBITDA, total debt or cash is not disclosed for the mid-cycle window",
            formula=formula,
            inputs=inputs,
        )
    avg_ebitda = sum(ebitdas) / len(ebitdas)
    if avg_ebitda <= 0:
        return _na(
            "ev_ebitda_mid_cycle_premium_pct",
            "mid-cycle EBITDA is non-positive",
            formula=formula,
            inputs=inputs,
        )
    median = ctx.peers.median("ev_ebitda")
    if median is None:
        return _u("ev_ebitda_mid_cycle_premium_pct", _peer_blocked_reason(ctx), formula=formula, inputs=inputs)
    return _v(
        "ev_ebitda_mid_cycle_premium_pct",
        _premium_pct((mcap + debt - cash) / avg_ebitda, median),
        formula=formula,
        inputs=inputs,
    )


@metric("ps_premium_pct")
def _ps_premium_pct(ctx: DerivationContext) -> MetricValue:
    formula = "(market cap / revenue) vs the median VALID peer P/S - 1, x100"
    inputs = ["peers", "financials.periods"]
    issuer_ps = _issuer_ps(ctx)
    median = ctx.peers.median("ps")
    if issuer_ps is None:
        return _u("ps_premium_pct", "issuer P/S cannot be computed", formula=formula, inputs=inputs)
    if median is None:
        return _u("ps_premium_pct", _peer_blocked_reason(ctx), formula=formula, inputs=inputs)
    return _v("ps_premium_pct", _premium_pct(issuer_ps, median), formula=formula, inputs=inputs)


# --------------------------------------------------------------------------
# Issue structure and proceeds
# --------------------------------------------------------------------------


@metric("fresh_share_pct")
def _fresh_share_pct(ctx: DerivationContext) -> MetricValue:
    formula = "fresh / (fresh + ofs) x 100"
    inputs = ["issue.fresh_issue", "issue.ofs"]
    fresh = ctx.canonical.money("issue", "fresh_issue")
    ofs = ctx.canonical.money("issue", "ofs")
    if fresh is None or ofs is None:
        return _u(
            "fresh_share_pct",
            "the fresh issue or the OFS amount is not disclosed",
            formula=formula,
            inputs=inputs,
        )
    if fresh + ofs <= 0:
        return _na("fresh_share_pct", "the offer size is zero", formula=formula, inputs=inputs)
    return _v("fresh_share_pct", fresh / (fresh + ofs) * 100.0, formula=formula, inputs=inputs)


@metric("ofs_share_pct")
def _ofs_share_pct(ctx: DerivationContext) -> MetricValue:
    formula = "100 - fresh_share_pct"
    inputs = ["issue.fresh_issue", "issue.ofs"]
    fresh_share = REGISTRY["fresh_share_pct"](ctx)
    if not fresh_share.is_value:
        return _u("ofs_share_pct", fresh_share.reason, formula=formula, inputs=inputs)
    return _v("ofs_share_pct", 100.0 - fresh_share.value, formula=formula, inputs=inputs)


@metric("pure_ofs")
def _pure_ofs(ctx: DerivationContext) -> MetricValue:
    formula = "fresh == 0"
    inputs = ["issue.fresh_issue"]
    fresh = ctx.canonical.money("issue", "fresh_issue")
    if fresh is None:
        return _u("pure_ofs", "the fresh issue amount is not disclosed", kind="boolean", formula=formula, inputs=inputs)
    return _v("pure_ofs", bool(fresh == 0), kind="boolean", formula=formula, inputs=inputs)


def _sellers(ctx: DerivationContext) -> Sequence[Mapping[str, Any]]:
    return ctx.canonical.issue().get("ofs_sellers") or []


def _sellers_available(ctx: DerivationContext) -> bool:
    """Is the OFS composition actually established?

    An empty seller list is only meaningful when the offer has no OFS at all.
    If an OFS is present but no sellers were supplied, the composition is
    UNKNOWN rather than "no promoter sold".
    """
    if _sellers(ctx):
        return True
    ofs = ctx.canonical.money("issue", "ofs")
    if ofs is None:
        return False
    return ofs == 0


@metric("ofs_seller_bucket")
def _ofs_seller_bucket(ctx: DerivationContext) -> MetricValue:
    formula = (
        "promoter_selling if any promoter/promoter-group seller sold >0; else pe_vc_exit if any "
        "PE/VC sells >=25% of its holding; else none_or_small"
    )
    inputs = ["issue.ofs_sellers"]
    if not _sellers_available(ctx):
        return _u(
            "ofs_seller_bucket",
            "an offer for sale is present but the selling shareholders were not supplied, so "
            "the seller composition cannot be established",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    promoter_sold = sum(
        _as_float(s.get("shares_sold")) or 0.0
        for s in _sellers(ctx)
        if s.get("type") in ("promoter", "promoter_group")
    )
    if promoter_sold > 0:
        return _v("ofs_seller_bucket", "promoter_selling", kind="categorical", formula=formula, inputs=inputs)
    for seller in _sellers(ctx):
        if seller.get("type") != "pe_vc":
            continue
        pre, sold = _as_float(seller.get("pre_issue_shares")), _as_float(seller.get("shares_sold"))
        if pre and pre > 0 and sold is not None and sold / pre >= 0.25:
            return _v("ofs_seller_bucket", "pe_vc_exit", kind="categorical", formula=formula, inputs=inputs)
    return _v("ofs_seller_bucket", "none_or_small", kind="categorical", formula=formula, inputs=inputs)


@metric("promoter_ofs_pct_of_holding")
def _promoter_ofs_pct_of_holding(ctx: DerivationContext) -> MetricValue:
    formula = "promoter shares sold / sum(pre-issue shares of promoter and promoter-group sellers) x 100"
    inputs = ["issue.ofs_sellers"]
    if not _sellers_available(ctx):
        return _u(
            "promoter_ofs_pct_of_holding",
            "the selling-shareholder list was not supplied, so the promoter stake sold cannot "
            "be established",
            formula=formula,
            inputs=inputs,
        )
    promoter_sellers = [
        s for s in _sellers(ctx) if s.get("type") in ("promoter", "promoter_group")
    ]
    sold = sum(_as_float(s.get("shares_sold")) or 0.0 for s in promoter_sellers)
    pre = sum(_as_float(s.get("pre_issue_shares")) or 0.0 for s in promoter_sellers)
    if not promoter_sellers:
        return _v(
            "promoter_ofs_pct_of_holding",
            0.0,
            formula=formula,
            inputs=inputs,
            reason="the offer for sale lists no promoter or promoter-group seller",
        )
    if pre <= 0:
        return _u(
            "promoter_ofs_pct_of_holding",
            "a promoter seller is listed without a pre-issue share count, so the percentage "
            "sold cannot be formed",
            formula=formula,
            inputs=inputs,
        )
    return _v("promoter_ofs_pct_of_holding", sold / pre * 100.0, formula=formula, inputs=inputs)


@metric("pe_promoter_sold_pct_combined")
def _pe_promoter_sold_pct_combined(ctx: DerivationContext) -> MetricValue:
    formula = "(promoter + PE/VC shares sold) / (their listed pre-issue shares) x 100"
    inputs = ["issue.ofs_sellers"]
    if not _sellers_available(ctx):
        return _u(
            "pe_promoter_sold_pct_combined",
            "the selling-shareholder list was not supplied, so combined promoter/PE-VC selling "
            "cannot be established",
            formula=formula,
            inputs=inputs,
        )
    relevant = [s for s in _sellers(ctx) if s.get("type") in ("promoter", "promoter_group", "pe_vc")]
    if not relevant:
        return _v(
            "pe_promoter_sold_pct_combined",
            0.0,
            formula=formula,
            inputs=inputs,
            reason="no promoter, promoter-group or PE/VC seller is listed",
        )
    sold = sum(_as_float(s.get("shares_sold")) or 0.0 for s in relevant)
    pre = sum(_as_float(s.get("pre_issue_shares")) or 0.0 for s in relevant)
    if pre <= 0:
        return _u(
            "pe_promoter_sold_pct_combined",
            "a listed seller has no pre-issue share count, so the percentage sold cannot be formed",
            formula=formula,
            inputs=inputs,
        )
    return _v("pe_promoter_sold_pct_combined", sold / pre * 100.0, formula=formula, inputs=inputs)


@metric("promoter_full_exit")
def _promoter_full_exit(ctx: DerivationContext) -> MetricValue:
    formula = "promoter post-issue holding == 0"
    inputs = ["capital_structure.promoter_post_pct"]
    post = ctx.canonical.number("capital_structure", "promoter_post_pct")
    if post is None:
        return _u(
            "promoter_full_exit",
            "post-issue promoter holding is not disclosed",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    return _v("promoter_full_exit", bool(post == 0), kind="boolean", formula=formula, inputs=inputs)


@metric("promoter_post_pct")
def _promoter_post_pct(ctx: DerivationContext) -> MetricValue:
    formula = "promoter and promoter-group holding post-issue, %"
    inputs = ["capital_structure.promoter_post_pct"]
    post = ctx.canonical.number("capital_structure", "promoter_post_pct")
    if post is None:
        return _u("promoter_post_pct", "post-issue promoter holding is not disclosed", formula=formula, inputs=inputs)
    return _v("promoter_post_pct", post, formula=formula, inputs=inputs)


@metric("dilution_pct")
def _dilution_pct(ctx: DerivationContext) -> MetricValue:
    formula = "fresh shares / post-issue shares x 100"
    inputs = ["issue.fresh_shares", "issue.post_issue_shares"]
    fresh = _as_float(ctx.canonical.issue().get("fresh_shares"))
    post = _as_float(ctx.canonical.issue().get("post_issue_shares"))
    if fresh is None or post is None:
        return _u(
            "dilution_pct",
            "the fresh share count or the post-issue share count is not disclosed",
            formula=formula,
            inputs=inputs,
        )
    if post <= 0:
        return _na("dilution_pct", "post-issue share count is zero", formula=formula, inputs=inputs)
    return _v("dilution_pct", fresh / post * 100.0, formula=formula, inputs=inputs)


@metric("dilution_ok")
def _dilution_ok(ctx: DerivationContext) -> MetricValue:
    formula = "dilution_pct < 25 or use_of_proceeds_bucket == growth"
    inputs = ["issue.fresh_shares", "issue.post_issue_shares", "use_of_proceeds_bucket"]
    dilution = REGISTRY["dilution_pct"](ctx)
    bucket = REGISTRY["use_of_proceeds_bucket"](ctx)
    if dilution.is_value and dilution.value < 25:
        return _v("dilution_ok", True, kind="boolean", formula=formula, inputs=inputs)
    if bucket.is_value and bucket.value == "growth":
        return _v(
            "dilution_ok",
            True,
            kind="boolean",
            formula=formula,
            inputs=inputs,
            reason="dilution is 25% or more but the proceeds are growth-directed",
        )
    if not dilution.is_value and not bucket.is_value:
        return _u(
            "dilution_ok",
            "neither the dilution percentage nor the use-of-proceeds bucket could be established",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    if not dilution.is_value and bucket.is_value and bucket.value != "growth":
        return _u(
            "dilution_ok",
            f"dilution is unknown and the use-of-proceeds bucket is {bucket.value!r}, which does "
            "not confer the growth exemption",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    return _v("dilution_ok", False, kind="boolean", formula=formula, inputs=inputs)


@metric("gcp_amount")
def _gcp_amount(ctx: DerivationContext) -> MetricValue:
    formula = "the disclosed general corporate purposes amount; UNKNOWN when the RHP shows [●]"
    inputs = ["use_of_proceeds"]
    entries = [u for u in ctx.canonical.use_of_proceeds() if u.get("category") == "gcp"]
    if not entries:
        return _v(
            "gcp_amount",
            0.0,
            formula=formula + "; no general corporate purposes category is present",
            inputs=inputs,
            reason="no GCP line item in the objects of the offer",
        )
    amounts = [_as_float(u.get("amount")) for u in entries]
    mentioned = [
        str(u.get("undisclosed_marker") or "[●]") for u in entries if _as_float(u.get("amount")) is None
    ]
    if any(a is None for a in amounts):
        return _u(
            "gcp_amount",
            "the general corporate purposes amount is shown as {} in the RHP and is therefore "
            "undisclosed; the legal maximum is recorded separately and is NOT substituted for "
            "the actual amount".format(", ".join(sorted(set(mentioned)))),
            formula=formula,
            inputs=inputs,
        )
    return _v("gcp_amount", sum(amounts) * ctx.canonical.unit_factor, formula=formula, inputs=inputs)


@metric("gcp_legal_max")
def _gcp_legal_max(ctx: DerivationContext) -> MetricValue:
    formula = "legal_max_pct_of_fresh_offer x fresh issue (SEBI ICDR Reg. 7(2))"
    inputs = ["issue.fresh_issue"]
    gcp_cfg = ctx.config.get("gcp", {})
    pct = float(gcp_cfg.get("legal_max_pct_of_fresh_offer", 25))
    fresh = ctx.canonical.money("issue", "fresh_issue")
    if fresh is None:
        return _u(
            "gcp_legal_max",
            "the fresh issue amount is not disclosed, so the legal ceiling cannot be computed",
            formula=formula,
            inputs=inputs,
        )
    return _v(
        "gcp_legal_max",
        fresh * pct / 100.0,
        formula=f"{pct}% x fresh issue (INR_CRORES)",
        inputs=inputs,
        reason="recorded separately from the disclosed GCP amount, per spec s10/s13",
    )


@metric("use_of_proceeds_bucket")
def _use_of_proceeds_bucket(ctx: DerivationContext) -> MetricValue:
    formula = (
        "blind_heavy: (gcp + unidentified acquisition)/fresh > 20%; else debt_heavy: debt "
        "repayment/fresh > 50%; else growth: (capex + R&D)/fresh >= growth_share_min_pct; else "
        "mixed_ok"
    )
    inputs = ["use_of_proceeds", "issue.fresh_issue"]
    fresh = ctx.canonical.money("issue", "fresh_issue")
    if fresh is None:
        return _u(
            "use_of_proceeds_bucket",
            "the fresh issue amount is not disclosed, so proceeds cannot be expressed as a "
            "share of it",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if fresh == 0:
        return _na(
            "use_of_proceeds_bucket",
            "a pure OFS has no proceeds to allocate",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    # Proceeds are stated in the reporting unit, so normalise each amount to
    # the engine currency before expressing it as a share of the fresh issue
    # (which is already normalised). A category that has *any* undisclosed
    # entry is treated as unknown for the whole category: a partial total
    # would understate the share and could silently clear the blind_heavy
    # test (spec s3.2 - absence is never treated as zero).
    totals: Dict[str, Optional[float]] = {}
    undisclosed: set = set()
    for entry in ctx.canonical.use_of_proceeds():
        category = str(entry.get("category"))
        amount = _as_float(entry.get("amount"))
        if amount is None:
            undisclosed.add(category)
            continue
        totals[category] = (totals.get(category) or 0.0) + amount * ctx.canonical.unit_factor

    def share(category: str) -> Optional[float]:
        """Share of the fresh issue allocated to a category.

        ``None`` means UNKNOWN - the category appears on the schedule but its
        amount is not disclosed. A category that does not appear on the
        schedule at all means no allocation (0%), which is a genuine value:
        the object-of-the-offer schedule is exhaustive by construction, so an
        absent line is a disclosed nil rather than a missing disclosure.
        """
        if category in undisclosed:
            return None
        return (totals.get(category) or 0.0) / fresh * 100.0

    gcp_share = share("gcp")
    unidentified_share = share("acquisition_unidentified")
    debt_share = share("debt_repayment")
    growth_share_parts = [share("growth_capex"), share("rnd")]
    growth_min = float(ctx.thresholds.get("growth_share_min_pct", 75))

    # The three tests are evaluated in order and in three-valued logic. An
    # UNKNOWN test cannot be skipped: "the GCP amount is undisclosed" means the
    # bucket could be blind_heavy, so it is not the same as "not blind_heavy".
    # A leg is UNKNOWN when its inputs are UNKNOWN; a test is TRUE/FALSE only
    # when every leg it needs is known (spec s3.2, s16).
    blind: Optional[bool] = None
    if gcp_share is not None and unidentified_share is not None:
        blind = (gcp_share + unidentified_share) > 20.0

    if blind is True:
        bucket = "blind_heavy"
    elif blind is None:
        return _u(
            "use_of_proceeds_bucket",
            "the blind_heavy test ((GCP + unidentified acquisition)/fresh > 20%) cannot be "
            "evaluated because a GCP or unidentified-acquisition amount is undisclosed. The "
            "legal maximum is not substituted, and an undisclosed amount is not read as zero, "
            "because either would let a blind-heavy offer pass the test",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    elif debt_share is None:
        return _u(
            "use_of_proceeds_bucket",
            "the offer is not blind-heavy, but the debt_repayment amount is undisclosed, so "
            "the debt_heavy test cannot be evaluated",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    elif debt_share > 50.0:
        bucket = "debt_heavy"
    elif any(part is None for part in growth_share_parts):
        return _u(
            "use_of_proceeds_bucket",
            "the offer is neither blind-heavy nor debt-heavy, but a growth_capex or rnd amount "
            "is undisclosed, so the growth test cannot be evaluated",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    elif sum(part for part in growth_share_parts if part is not None) >= growth_min:
        bucket = "growth"
    else:
        bucket = "mixed_ok"
    return _v("use_of_proceeds_bucket", bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("pre_ipo_placement_bucket")
def _pre_ipo_placement_bucket(ctx: DerivationContext) -> MetricValue:
    formula = (
        "deep_discount_12m: any placement in the 12 months before the issue open at more than "
        "25% below the issue price; none_or_near_ipo: none, or all within near_ipo_price_pct; "
        "else in_between"
    )
    inputs = ["capital_structure.pre_ipo_placements", "issue.price_band_high", "issue.open_date"]
    placements = ctx.canonical.capital_structure().get("pre_ipo_placements") or []
    if not placements:
        return _v(
            "pre_ipo_placement_bucket",
            "none_or_near_ipo",
            kind="categorical",
            formula=formula,
            inputs=inputs,
            reason="no pre-IPO placements are disclosed",
        )
    price = _issue_price(ctx.canonical)
    open_date = parse_date(ctx.canonical.issue().get("open_date"))
    if price is None or open_date is None:
        return _u(
            "pre_ipo_placement_bucket",
            "the issue price or the open date is not disclosed, so placements cannot be dated or "
            "compared",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    recent = []
    for placement in placements:
        placed = parse_date(placement.get("date"))
        if placed is None:
            continue
        age = (open_date - placed).days
        if 0 <= age <= 365:
            recent.append(placement)
    if not recent:
        return _v(
            "pre_ipo_placement_bucket",
            "none_or_near_ipo",
            kind="categorical",
            formula=formula,
            inputs=inputs,
            reason="no placements fall within the 12 months before the issue opened",
        )
    near = 1 - float(ctx.thresholds.get("near_ipo_price_pct", 10)) / 100.0
    prices = [_as_float(p.get("price")) for p in recent]
    if any(p is None for p in prices):
        return _u(
            "pre_ipo_placement_bucket",
            "a recent placement has no price, so its discount cannot be established",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if any(p < 0.75 * price for p in prices):
        bucket = "deep_discount_12m"
    elif all(p >= near * price for p in prices):
        bucket = "none_or_near_ipo"
    else:
        bucket = "in_between"
    return _v("pre_ipo_placement_bucket", bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("lockin_bucket")
def _lockin_bucket(ctx: DerivationContext) -> MetricValue:
    formula = "intact: promoter lock-in in place and no early unlock of large pre-IPO holders; else weak"
    inputs = ["capital_structure.promoter_lockin_in_place", "capital_structure.large_holders_unlocked_early"]
    lockin = ctx.canonical.flag("capital_structure", "promoter_lockin_in_place")
    early = ctx.canonical.flag("capital_structure", "large_holders_unlocked_early")
    if lockin is None:
        return _u(
            "lockin_bucket",
            "it is not established whether the promoter lock-in is in place",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if early is None:
        return _u(
            "lockin_bucket",
            "it is not established whether large pre-IPO holders were unlocked early",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    return _v(
        "lockin_bucket",
        "intact" if (lockin and not early) else "weak",
        kind="categorical",
        formula=formula,
        inputs=inputs,
    )


# --------------------------------------------------------------------------
# Governance
# --------------------------------------------------------------------------


@metric("litigation_bucket")
def _litigation_bucket(ctx: DerivationContext) -> MetricValue:
    formula = "clean / minor_civil / criminal_or_regulatory across promoters, directors and the company"
    inputs = ["governance.litigation_bucket"]
    value = ctx.canonical.governance().get("litigation_bucket")
    if value is None:
        return _u(
            "litigation_bucket",
            "the litigation status of the promoters, directors and company is not established",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    return _v("litigation_bucket", str(value), kind="categorical", formula=formula, inputs=inputs)


@metric("rpt_pct_revenue")
def _rpt_pct_revenue(ctx: DerivationContext) -> MetricValue:
    formula = "related-party transactions / revenue, latest FY, %"
    inputs = ["governance.rpt_pct_revenue"]
    value = ctx.canonical.number("governance", "rpt_pct_revenue")
    if value is None:
        return _u(
            "rpt_pct_revenue",
            "related-party transactions as a share of revenue are not disclosed",
            formula=formula,
            inputs=inputs,
        )
    return _v("rpt_pct_revenue", value, formula=formula, inputs=inputs)


@metric("rpt_pct_of_revenue_growth")
def _rpt_pct_of_revenue_growth(ctx: DerivationContext) -> MetricValue:
    formula = "share of revenue growth attributable to related parties, %"
    inputs = ["governance.rpt_pct_of_revenue_growth"]
    value = ctx.canonical.number("governance", "rpt_pct_of_revenue_growth")
    if value is None:
        return _u(
            "rpt_pct_of_revenue_growth",
            "the related-party contribution to revenue growth is not disclosed",
            formula=formula,
            inputs=inputs,
        )
    return _v("rpt_pct_of_revenue_growth", value, formula=formula, inputs=inputs)


@metric("auditor_bucket")
def _auditor_bucket(ctx: DerivationContext) -> MetricValue:
    formula = (
        "clean_reputed: unqualified, no auditor change, no EOM; eom_only: EOM/CARO only and no "
        "change; unstable_or_repeated_eom: auditor change within 3 years or repeated EOM. A "
        "qualified/adverse/disclaimer opinion is a knockout rather than a score."
    )
    inputs = [
        "governance.auditor_opinion",
        "governance.auditor_reputed",
        "governance.auditor_changed_3y",
        "governance.repeated_eom",
    ]
    governance = ctx.canonical.governance()
    opinion = governance.get("auditor_opinion")
    if opinion is None:
        return _u(
            "auditor_bucket",
            "the audit opinion is not disclosed, so auditor status cannot be established",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if opinion in ("qualified", "adverse", "disclaimer"):
        return _na(
            "auditor_bucket",
            f"a {opinion} opinion is handled by knockout K1, not by the auditor score",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    changed = ctx.canonical.flag("governance", "auditor_changed_3y")
    reputed = ctx.canonical.flag("governance", "auditor_reputed")
    repeated = ctx.canonical.flag("governance", "repeated_eom")
    if changed is None:
        return _u(
            "auditor_bucket",
            "it is not established whether the auditor changed within the last three years",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if changed or repeated is True:
        return _v(
            "auditor_bucket",
            "unstable_or_repeated_eom",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if opinion == "unqualified" and reputed is True:
        return _v("auditor_bucket", "clean_reputed", kind="categorical", formula=formula, inputs=inputs)
    if opinion in ("emphasis_of_matter", "unqualified"):
        if opinion == "unqualified" and reputed is None:
            return _u(
                "auditor_bucket",
                "the opinion is unqualified but it is not established whether the auditor is a "
                "reputed firm, which decides between clean_reputed and eom_only",
                kind="categorical",
                formula=formula,
                inputs=inputs,
            )
        return _v("auditor_bucket", "eom_only", kind="categorical", formula=formula, inputs=inputs)
    return _u(
        "auditor_bucket",
        f"audit opinion {opinion!r} does not map to a defined auditor bucket",
        kind="categorical",
        formula=formula,
        inputs=inputs,
    )


@metric("eom_materiality")
def _eom_materiality(ctx: DerivationContext) -> MetricValue:
    formula = "low / medium / high by the size of the matter relative to net worth"
    inputs = ["governance.eom_materiality"]
    value = ctx.canonical.governance().get("eom_materiality")
    if value is None:
        return _u(
            "eom_materiality",
            "the materiality of the emphasis-of-matter items is not established",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    return _v("eom_materiality", str(value), kind="categorical", formula=formula, inputs=inputs)


@metric("board_kmp_bucket")
def _board_kmp_bucket(ctx: DerivationContext) -> MetricValue:
    formula = (
        "independent_stable: independent-majority board and no KMP exit in 2 years; high_churn: "
        ">=2 KMP exits; else other"
    )
    inputs = ["governance.board_independent_majority", "governance.kmp_exits_2y"]
    exits = ctx.canonical.governance().get("kmp_exits_2y")
    independent = ctx.canonical.flag("governance", "board_independent_majority")
    if exits is None:
        return _u(
            "board_kmp_bucket",
            "the number of KMP exits in the last two years is not disclosed",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if int(exits) >= 2:
        return _v("board_kmp_bucket", "high_churn", kind="categorical", formula=formula, inputs=inputs)
    if independent is None:
        return _u(
            "board_kmp_bucket",
            "board independence is not established, which decides between independent_stable and other",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if int(exits) == 0 and independent:
        return _v("board_kmp_bucket", "independent_stable", kind="categorical", formula=formula, inputs=inputs)
    return _v("board_kmp_bucket", "other", kind="categorical", formula=formula, inputs=inputs)


# --------------------------------------------------------------------------
# Business
# --------------------------------------------------------------------------


@metric("industry_cagr_pct")
def _industry_cagr_pct(ctx: DerivationContext) -> MetricValue:
    formula = "forward industry CAGR from the independent industry report in the RHP, %"
    inputs = [
        "business.industry_cagr_pct",
        "business.industry_scope",
        "business.industry_forecast_period",
        "business.industry_source",
    ]
    business = ctx.canonical.business()
    value = _as_float(business.get("industry_cagr_pct"))
    if value is None:
        return _u(
            "industry_cagr_pct",
            "the forward industry CAGR is not disclosed",
            formula=formula,
            inputs=inputs,
        )
    missing = [
        label
        for label, key in (
            ("scope", "industry_scope"),
            ("forecast period", "industry_forecast_period"),
            ("source", "industry_source"),
        )
        if business.get(key) in (None, "")
    ]
    if missing:
        return _u(
            "industry_cagr_pct",
            "the industry CAGR is not scorable because its {} is not recorded; spec s12 requires "
            "value, scope, forecast period and source together".format(", ".join(missing)),
            formula=formula,
            inputs=inputs,
        )
    return _v("industry_cagr_pct", value, formula=formula, inputs=inputs)


@metric("top5_concentration_pct")
def _top5_concentration_pct(ctx: DerivationContext) -> MetricValue:
    formula = "the higher of the top-5 customer and top-5 supplier concentration"
    inputs = ["business.top5_customer_pct", "business.top5_supplier_pct"]
    business = ctx.canonical.business()
    values = [
        v
        for v in (
            _as_float(business.get("top5_customer_pct")),
            _as_float(business.get("top5_supplier_pct")),
        )
        if v is not None
    ]
    if not values:
        return _u(
            "top5_concentration_pct",
            "neither top-5 customer nor top-5 supplier concentration is disclosed",
            formula=formula,
            inputs=inputs,
        )
    return _v("top5_concentration_pct", max(values), formula=formula, inputs=inputs)


# --------------------------------------------------------------------------
# Market and demand
# --------------------------------------------------------------------------


@metric("market_regime_variant")
def _market_regime_variant(ctx: DerivationContext) -> MetricValue:
    formula = "hot when at least min_count of the last lookback_ipos listed above listing_gain_pct"
    inputs = ["market.regime.last_ipo_listing_gains_pct"]
    hot = ctx.thresholds.get("hot_market", {})
    gains = ctx.market.value("regime", "last_ipo_listing_gains_pct") or []
    gains = [g for g in gains if isinstance(g, (int, float))]
    lookback = int(hot.get("lookback_ipos", 5))
    min_count = int(hot.get("min_count", 3))
    threshold = float(hot.get("listing_gain_pct", 20))
    recent = gains[-lookback:]
    variant = "hot" if sum(1 for g in recent if g > threshold) >= min_count else "normal"
    return _v(
        "market_regime_variant",
        variant,
        kind="categorical",
        formula=formula,
        inputs=inputs,
        reason=(
            f"{len(recent)} recent listing gain observations available; the variant selects the "
            "subscription band table"
        ),
    )


@metric("retail_or_nii_below_1x")
def _retail_or_nii_below_1x(ctx: DerivationContext) -> MetricValue:
    formula = "retail or NII subscription below 1.0x at close"
    inputs = ["market.subscription.retail_x", "market.subscription.nii_x"]
    retail = ctx.market.value("subscription", "retail_x")
    nii = ctx.market.value("subscription", "nii_x")
    if retail is None or nii is None:
        return _u(
            "retail_or_nii_below_1x",
            "the retail or NII subscription multiple is unavailable or stale",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    return _v("retail_or_nii_below_1x", bool(retail < 1 or nii < 1), kind="boolean", formula=formula, inputs=inputs)


def _market_metric(ctx: DerivationContext, metric_id: str, block: str, key: str, kind: str, formula: str) -> MetricValue:
    inputs = [f"market.{block}.{key}"]
    block_obj = ctx.market.block(block)
    if block_obj is None or block_obj.status != MARKET_FRESH:
        reason = (
            block_obj.reason
            if block_obj is not None and block_obj.reason
            else f"the {block} block is unavailable"
        )
        return _u(metric_id, f"{block} market data is not usable: {reason}", kind=kind, formula=formula, inputs=inputs)
    value = block_obj.values.get(key)
    if value is None:
        return _u(metric_id, f"{block}.{key} was not supplied", kind=kind, formula=formula, inputs=inputs)
    return _v(metric_id, value, kind=kind, formula=formula, inputs=inputs)


@metric("qib_quota_pct")
def _qib_quota_pct(ctx: DerivationContext) -> MetricValue:
    formula = "QIB share of the offer, %"
    inputs = ["issue.quota_pct.qib"]
    quota = ctx.canonical.issue().get("quota_pct") or {}
    value = _as_float(quota.get("qib"))
    if value is None:
        return _u(
            "qib_quota_pct",
            "the QIB quota share is not disclosed, so the structure overlay cannot be resolved",
            formula=formula,
            inputs=inputs,
        )
    return _v("qib_quota_pct", value, formula=formula, inputs=inputs)


@metric("anchor_bucket")
def _anchor_bucket(ctx: DerivationContext) -> MetricValue:
    return _market_metric(
        ctx, "anchor_bucket", "anchor", "quality", "categorical", "market.anchor.quality"
    )


@metric("qib_x")
def _qib_x(ctx: DerivationContext) -> MetricValue:
    return _market_metric(
        ctx, "qib_x", "subscription", "qib_x", "numeric", "market.subscription.qib_x"
    )


@metric("nii_x")
def _nii_x(ctx: DerivationContext) -> MetricValue:
    return _market_metric(
        ctx, "nii_x", "subscription", "nii_x", "numeric", "market.subscription.nii_x"
    )


@metric("overall_x")
def _overall_x(ctx: DerivationContext) -> MetricValue:
    return _market_metric(
        ctx, "overall_x", "subscription", "overall_x", "numeric", "market.subscription.overall_x"
    )


@metric("gmp_bucket")
def _gmp_bucket(ctx: DerivationContext) -> MetricValue:
    return _market_metric(ctx, "gmp_bucket", "gmp", "trend", "categorical", "market.gmp.trend")


@metric("market_regime_bucket")
def _market_regime_bucket(ctx: DerivationContext) -> MetricValue:
    return _market_metric(
        ctx, "market_regime_bucket", "regime", "nifty_trend", "categorical", "market.regime.nifty_trend"
    )


# --------------------------------------------------------------------------
# Penalty / knockout inputs
# --------------------------------------------------------------------------


@metric("profit_declining")
def _profit_declining(ctx: DerivationContext) -> MetricValue:
    formula = "PAT below the prior FY, or PAT CAGR below zero"
    inputs = ["financials.periods"]
    periods = ctx.periods
    if len(periods) < 2:
        return _u(
            "profit_declining",
            "at least two full FY observations are required",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    latest, prior = periods[-1].get("pat"), periods[-2].get("pat")
    if latest is None or prior is None:
        return _u(
            "profit_declining",
            "PAT is not disclosed for the latest or the prior full FY",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    growth = REGISTRY["pat_cagr_2y_from_3fy"](ctx)
    declining = latest < prior or (growth.is_value and growth.value < 0)
    return _v("profit_declining", bool(declining), kind="boolean", formula=formula, inputs=inputs)


@metric("margin_spike_pre_ipo")
def _margin_spike_pre_ipo(ctx: DerivationContext) -> MetricValue:
    formula = "EBITDA margin rose by more than margin_spike_bps in either of the last two FYs"
    inputs = ["financials.periods"]
    margins = _margins(ctx, "ebitda")
    if any(m is None for m in margins) or len(margins) < 3:
        return _u(
            "margin_spike_pre_ipo",
            "EBITDA margins are not derivable across three FY observations",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    bps = float(ctx.thresholds.get("margin_spike_bps", 500))
    deltas = [margins[i + 1] - margins[i] for i in range(len(margins) - 1)][-2:]
    return _v(
        "margin_spike_pre_ipo",
        bool(any(d * 100.0 > bps for d in deltas)),
        kind="boolean",
        formula=formula,
        inputs=inputs,
    )


@metric("receivable_days_yoy_pct")
def _receivable_days_yoy_pct(ctx: DerivationContext) -> MetricValue:
    formula = "(receivable days latest / prior - 1) x 100"
    inputs = ["financials.periods"]
    periods = ctx.periods
    if len(periods) < 2:
        return _u(
            "receivable_days_yoy_pct",
            "at least two full FY observations are required",
            formula=formula,
            inputs=inputs,
        )
    latest, prior = periods[-1].get("receivable_days"), periods[-2].get("receivable_days")
    if latest is None or prior is None:
        return _u(
            "receivable_days_yoy_pct",
            "receivable days are not disclosed for the latest or the prior full FY",
            formula=formula,
            inputs=inputs,
        )
    if prior == 0:
        return _na(
            "receivable_days_yoy_pct",
            "prior-year receivable days are zero, so a percentage change is not meaningful",
            formula=formula,
            inputs=inputs,
        )
    return _v("receivable_days_yoy_pct", (latest / prior - 1.0) * 100.0, formula=formula, inputs=inputs)


@metric("cfo_exempt")
def _cfo_exempt(ctx: DerivationContext) -> MetricValue:
    formula = (
        "cfo_pat_cumulative < 0 and (order book >= 2x revenue, or collections >= pre-sales) and "
        "receivable days up less than 15% YoY"
    )
    inputs = ["financials.periods"]
    cumulative = REGISTRY["cfo_pat_cumulative"](ctx)
    if not cumulative.is_value:
        return _u(
            "cfo_exempt",
            f"cumulative CFO/PAT is unavailable ({cumulative.reason})",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    if cumulative.value >= 0:
        return _v("cfo_exempt", False, kind="boolean", formula=formula, inputs=inputs)
    latest = ctx.canonical.latest
    if latest is None:
        return _u("cfo_exempt", "no full FY observation supplied", kind="boolean", formula=formula, inputs=inputs)
    order_book, revenue = latest.get("order_book"), latest.get("revenue")
    pre_sales, collections = latest.get("pre_sales"), latest.get("collections")
    order_book_ok = order_book is not None and revenue is not None and revenue > 0 and order_book >= 2 * revenue
    collections_ok = pre_sales is not None and collections is not None and collections >= pre_sales
    receivable = REGISTRY["receivable_days_yoy_pct"](ctx)
    if not receivable.is_value:
        return _u(
            "cfo_exempt",
            "receivable days cannot be compared year on year, so the exemption condition cannot "
            "be confirmed",
            kind="boolean",
            formula=formula,
            inputs=inputs,
        )
    exempt = bool((order_book_ok or collections_ok) and receivable.value < 15)
    return _v("cfo_exempt", exempt, kind="boolean", formula=formula, inputs=inputs)


@metric("contingent_liab_pct_networth")
def _contingent_liab_pct_networth(ctx: DerivationContext) -> MetricValue:
    formula = "contingent liabilities / net worth x 100"
    inputs = ["financials.contingent_liabilities", "financials.periods"]
    contingent = ctx.canonical.money("financials", "contingent_liabilities")
    if contingent is None:
        return _u(
            "contingent_liab_pct_networth",
            "contingent liabilities are not disclosed; an absent disclosure is not treated as zero",
            formula=formula,
            inputs=inputs,
        )
    equity = ctx.p("net_worth")
    if equity is None:
        return _u(
            "contingent_liab_pct_networth",
            "net worth is not disclosed, so the ratio cannot be formed",
            formula=formula,
            inputs=inputs,
        )
    if equity <= 0:
        return _na(
            "contingent_liab_pct_networth",
            "net worth is non-positive, so a percentage of it is not meaningful",
            formula=formula,
            inputs=inputs,
        )
    return _v("contingent_liab_pct_networth", contingent / equity * 100.0, formula=formula, inputs=inputs)


# --------------------------------------------------------------------------
# Sector overlay metrics
# --------------------------------------------------------------------------


@metric("nim_cost_income_bucket")
def _nim_cost_income_bucket(ctx: DerivationContext) -> MetricValue:
    formula = "trend of NIM and cost-to-income across the FY observations"
    inputs = ["financials.periods"]
    periods = ctx.periods
    if len(periods) < 2:
        return _u(
            "nim_cost_income_bucket",
            "at least two FY observations are required for a trend",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    nims = [p.get("nim_pct") for p in periods]
    costs = [p.get("cost_to_income_pct") for p in periods]
    if any(v is None for v in nims) or any(v is None for v in costs):
        return _u(
            "nim_cost_income_bucket",
            "NIM or cost-to-income is not disclosed for every FY observation",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    nim_up = nims[-1] > nims[-2]
    nim_down = nims[-1] < nims[-2]
    cost_down = costs[-1] < costs[-2]
    cost_up = costs[-1] > costs[-2]
    if nim_up and cost_down:
        bucket = "improving"
    elif nim_down and cost_up:
        bucket = "deteriorating"
    elif (nim_up and cost_up) or (nim_down and cost_down) or (nims[-1] == nims[-2] and costs[-1] == costs[-2]):
        bucket = "stable"
    else:
        bucket = "mixed"
    return _v("nim_cost_income_bucket", bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("roa_roe_peer_quartile")
def _roa_roe_peer_quartile(ctx: DerivationContext) -> MetricValue:
    formula = "issuer ROA/ROE versus the VALID peer quartiles"
    inputs = ["financials.periods", "peers"]
    latest = ctx.canonical.latest
    if latest is None:
        return _u("roa_roe_peer_quartile", "no full FY observation supplied", kind="categorical", formula=formula, inputs=inputs)
    issuer_roe = latest.get("roe_pct")
    if issuer_roe is None:
        equity, pat = latest.get("net_worth"), latest.get("pat")
        if equity and equity > 0 and pat is not None:
            issuer_roe = pat / equity * 100.0
    quartiles = ctx.peers.quartiles("roe_pct")
    if issuer_roe is None or quartiles is None:
        return _u(
            "roa_roe_peer_quartile",
            "the peer-quartile comparison needs the issuer ROE and at least two VALID peer ROE "
            "observations; " + _peer_blocked_reason(ctx),
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    if issuer_roe >= quartiles["median"]:
        bucket = "top_quartile" if issuer_roe >= quartiles["max"] - (quartiles["max"] - quartiles["median"]) / 2 else "median"
    else:
        bucket = "median" if issuer_roe >= quartiles["min"] else "bottom_half"
    return _v("roa_roe_peer_quartile", bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("asset_quality_bucket")
def _asset_quality_bucket(ctx: DerivationContext) -> MetricValue:
    formula = "GNPA/NNPA trend with provision coverage"
    inputs = ["financials.periods"]
    periods = ctx.periods
    if len(periods) < 2:
        return _u(
            "asset_quality_bucket",
            "at least two FY observations are required for an asset-quality trend",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    gnpa = [p.get("gnpa_pct") for p in periods]
    if any(v is None for v in gnpa):
        return _u(
            "asset_quality_bucket",
            "GNPA is not disclosed for every FY observation",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    coverage = [p.get("provision_coverage_pct") for p in periods]
    latest_gnpa, prior_gnpa = gnpa[-1], gnpa[-2]
    if latest_gnpa > prior_gnpa * 1.1:
        bucket = "stressed" if latest_gnpa > 5 else "deteriorating"
    elif latest_gnpa < prior_gnpa:
        bucket = "improving_strong" if (coverage[-1] or 0) >= (coverage[-2] or 0) else "stable"
    else:
        bucket = "stable"
    return _v("asset_quality_bucket", bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("crar_buffer_pts")
def _crar_buffer_pts(ctx: DerivationContext) -> MetricValue:
    formula = "CRAR (or Tier 1) minus the regulatory minimum, in percentage points"
    inputs = ["financials.periods"]
    latest = ctx.canonical.latest
    if latest is None:
        return _u("crar_buffer_pts", "no full FY observation supplied", formula=formula, inputs=inputs)
    crar = latest.get("crar_pct")
    tier1 = latest.get("tier1_pct")
    if crar is None and tier1 is None:
        return _u(
            "crar_buffer_pts",
            "neither CRAR nor Tier 1 is disclosed",
            formula=formula,
            inputs=inputs,
        )
    minimum = ctx.canonical.number("financials", "regulatory_crar_min_pct")
    if minimum is None:
        minimum = float(ctx.thresholds.get("regulatory_crar_min_pct", 15.0))
    return _v("crar_buffer_pts", (crar if crar is not None else tier1) - minimum, formula=formula, inputs=inputs)


@metric("cash_runway_months")
def _cash_runway_months(ctx: DerivationContext) -> MetricValue:
    formula = "post-issue cash and equivalents / average monthly operating cash burn"
    inputs = ["financials.periods", "issue.fresh_issue"]
    latest = ctx.canonical.latest
    if latest is None:
        return _u("cash_runway_months", "no full FY observation supplied", formula=formula, inputs=inputs)
    cash = latest.get("cash_and_equivalents")
    cfo = latest.get("cfo")
    if cash is None or cfo is None:
        return _u(
            "cash_runway_months",
            "cash and equivalents or operating cash flow is not disclosed",
            formula=formula,
            inputs=inputs,
        )
    if cfo >= 0:
        return _na(
            "cash_runway_months",
            "the latest FY was not cash-consumptive, so runway is not a binding constraint",
            formula=formula,
            inputs=inputs,
        )
    burn = -cfo / 12.0
    fresh = ctx.canonical.money("issue", "fresh_issue") or 0.0
    return _v("cash_runway_months", (cash + fresh) / burn, formula=formula, inputs=inputs)


@metric("net_debt_bucket")
def _net_debt_bucket(ctx: DerivationContext) -> MetricValue:
    formula = "net debt/equity trend and project-debt interest cover"
    inputs = ["financials.periods"]
    periods = ctx.periods
    if len(periods) < 2:
        return _u(
            "net_debt_bucket",
            "at least two FY observations are required for a trend",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    latest, prior = periods[-1], periods[-2]
    values = [latest.get("total_debt"), latest.get("cash_and_equivalents"), latest.get("net_worth")]
    if any(v is None for v in values):
        return _u(
            "net_debt_bucket",
            "total debt, cash or net worth is not disclosed for the latest FY",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    debt, cash, equity = values
    if equity <= 0:
        return _u(
            "net_debt_bucket",
            "net worth is non-positive",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    ratio = (debt - cash) / equity
    prior_values = [prior.get("total_debt"), prior.get("cash_and_equivalents"), prior.get("net_worth")]
    improving = None
    if all(v is not None for v in prior_values) and prior_values[2] > 0:
        prior_ratio = (prior_values[0] - prior_values[1]) / prior_values[2]
        improving = ratio < prior_ratio
    if ratio < 0.5:
        bucket = "strong"
    elif ratio < 1:
        bucket = "ok"
    elif ratio <= 2:
        bucket = "stretched"
    else:
        bucket = "weak"
    if improving and bucket in ("stretched", "weak"):
        bucket = "ok"
    return _v("net_debt_bucket", bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("contribution_bucket")
def _contribution_bucket(ctx: DerivationContext) -> MetricValue:
    formula = (
        "expanding_2y_gt300bps: positive and up more than 300 bps two years running; "
        "positive_improving; positive_flat_or_falling; negative"
    )
    inputs = ["financials.periods"]
    values = [p.get("contribution_margin_pct") for p in ctx.periods]
    if len(values) < 3 or any(v is None for v in values[-3:]):
        return _u(
            "contribution_bucket",
            "three FY observations of contribution margin are required",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    a, b, c = values[-3], values[-2], values[-1]
    if c <= 0:
        bucket = "negative"
    elif (c - b) > 3 and (b - a) > 3:
        bucket = "expanding_2y_gt300bps"
    elif c > b:
        bucket = "positive_improving"
    else:
        bucket = "positive_flat_or_falling"
    return _v("contribution_bucket", bucket, kind="categorical", formula=formula, inputs=inputs)


@metric("loss_narrowing_bucket")
def _loss_narrowing_bucket(ctx: DerivationContext) -> MetricValue:
    formula = (
        "two_years: operating loss as a share of revenue narrowed two consecutive years; "
        "one_year: the latest year only; widening: otherwise"
    )
    inputs = ["financials.periods"]
    values = [p.get("operating_loss_pct_revenue") for p in ctx.periods]
    if len(values) < 3 or any(v is None for v in values[-3:]):
        return _u(
            "loss_narrowing_bucket",
            "three FY observations of operating loss as a share of revenue are required",
            kind="categorical",
            formula=formula,
            inputs=inputs,
        )
    a, b, c = values[-3], values[-2], values[-1]
    if c < b and b < a:
        bucket = "two_years"
    elif c < b:
        bucket = "one_year"
    else:
        bucket = "widening"
    return _v("loss_narrowing_bucket", bucket, kind="categorical", formula=formula, inputs=inputs)


# --------------------------------------------------------------------------
# Direct pass-through inputs
# --------------------------------------------------------------------------
#
# Knockout expressions and some criteria consume canonical inputs directly.
# They are registered as metrics so that (a) the configuration validator can
# prove every referenced input exists, and (b) an absent input is reported as
# UNKNOWN rather than silently evaluating to False - which is precisely the
# defect v1.5 s3.3 and s16 forbid ("A missing knockout input must never be
# treated as CLEAR").


def _passthrough(
    ctx: DerivationContext,
    metric_id: str,
    section: str,
    key: str,
    kind: str,
    formula: str,
    missing_reason: str,
) -> MetricValue:
    inputs = [f"{section}.{key}"]
    container = ctx.canonical.raw.get(section) or {}
    if key not in container or container.get(key) is None:
        return _u(metric_id, missing_reason, kind=kind, formula=formula, inputs=inputs)
    raw = container.get(key)
    if kind == "boolean":
        if not isinstance(raw, bool):
            return _u(
                metric_id,
                f"{section}.{key} is not a boolean, so the condition cannot be evaluated",
                kind=kind,
                formula=formula,
                inputs=inputs,
            )
        return _v(metric_id, raw, kind=kind, formula=formula, inputs=inputs)
    if kind == "numeric":
        value = _as_float(raw)
        if value is None:
            return _u(
                metric_id,
                f"{section}.{key} is not numeric, so the condition cannot be evaluated",
                kind=kind,
                formula=formula,
                inputs=inputs,
            )
        return _v(metric_id, value, kind=kind, formula=formula, inputs=inputs)
    return _v(metric_id, str(raw), kind=kind, formula=formula, inputs=inputs)


@metric("auditor_opinion")
def _auditor_opinion(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "auditor_opinion",
        "governance",
        "auditor_opinion",
        "categorical",
        "governance.auditor_opinion",
        "the audit opinion is not disclosed, so it cannot be established whether the opinion is "
        "qualified, adverse or a disclaimer",
    )


@metric("going_concern_uncertainty")
def _going_concern_uncertainty(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "going_concern_uncertainty",
        "governance",
        "going_concern_uncertainty",
        "boolean",
        "governance.going_concern_uncertainty",
        "the supplied input does not establish whether going-concern uncertainty exists",
    )


@metric("sebi_ed_action_active")
def _sebi_ed_action_active(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "sebi_ed_action_active",
        "governance",
        "sebi_ed_action_active",
        "boolean",
        "governance.sebi_ed_action_active",
        "the supplied input does not establish whether an active SEBI/ED action exists",
    )


@metric("promoter_pledge_pct")
def _promoter_pledge_pct(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "promoter_pledge_pct",
        "capital_structure",
        "promoter_pledge_pct",
        "numeric",
        "capital_structure.promoter_pledge_pct",
        "promoter pledge as a percentage of holding is not disclosed",
    )


@metric("contingent_liab_unquantified")
def _contingent_liab_unquantified(ctx: DerivationContext) -> MetricValue:
    container = ctx.canonical.raw.get("financials") or {}
    if "contingent_liabilities_unquantified" not in container or container.get("contingent_liabilities_unquantified") is None:
        return _u(
            "contingent_liab_unquantified",
            "the supplied input does not establish whether any material contingent liability is "
            "unquantified",
            kind="boolean",
            formula="financials.contingent_liabilities_unquantified",
            inputs=["financials.contingent_liabilities_unquantified"],
        )
    return _v(
        "contingent_liab_unquantified",
        bool(container["contingent_liabilities_unquantified"]),
        kind="boolean",
        formula="financials.contingent_liabilities_unquantified",
        inputs=["financials.contingent_liabilities_unquantified"],
    )


@metric("adjusted_metrics_unreconciled")
def _adjusted_metrics_unreconciled(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "adjusted_metrics_unreconciled",
        "financials",
        "adjusted_metrics_unreconciled",
        "boolean",
        "financials.adjusted_metrics_unreconciled",
        "the supplied input does not establish whether adjusted metrics are reconciled to Ind AS",
    )


@metric("heavy_discounted_allotments_18m")
def _heavy_discounted_allotments_18m(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "heavy_discounted_allotments_18m",
        "capital_structure",
        "discounted_allotments_18m_before_drhp",
        "boolean",
        "capital_structure.discounted_allotments_18m_before_drhp",
        "the supplied input does not establish whether there were discounted allotments within the "
        "18 months before DRHP filing",
    )


@metric("auditor_or_cfo_exit_2y")
def _auditor_or_cfo_exit_2y(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "auditor_or_cfo_exit_2y",
        "governance",
        "auditor_or_cfo_exit_2y",
        "boolean",
        "governance.auditor_or_cfo_exit_2y",
        "the supplied input does not establish whether the auditor or CFO resigned in the last "
        "two years",
    )


@metric("regulatory_dependence")
def _regulatory_dependence(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "regulatory_dependence",
        "business",
        "regulatory_dependence",
        "boolean",
        "business.regulatory_dependence",
        "the supplied input does not establish whether the business depends on a single licence or "
        "a controlled price",
    )


@metric("moat_rating")
def _moat_rating(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "moat_rating",
        "business",
        "moat_rating",
        "categorical",
        "business.moat_rating",
        "the market-position and moat assessment is not recorded",
    )


@metric("visibility_rating")
def _visibility_rating(ctx: DerivationContext) -> MetricValue:
    return _passthrough(
        ctx,
        "visibility_rating",
        "business",
        "visibility_rating",
        "categorical",
        "business.visibility_rating",
        "the capacity and order-book visibility assessment is not recorded",
    )


# --------------------------------------------------------------------------
# Aggregate
# --------------------------------------------------------------------------


@dataclass
class DerivedMetrics:
    """All derived metrics for one evaluation, plus access helpers."""

    metrics: Dict[str, MetricValue]
    overrides: Tuple[str, ...] = ()

    def get(self, metric_id: str) -> MetricValue:
        if metric_id not in self.metrics:
            raise KeyError(metric_id)
        return self.metrics[metric_id]

    def __contains__(self, metric_id: str) -> bool:
        return metric_id in self.metrics

    def value_of(self, metric_id: str) -> Any:
        item = self.metrics.get(metric_id)
        return item.value if item is not None and item.is_value else None

    def state_of(self, metric_id: str) -> Optional[str]:
        item = self.metrics.get(metric_id)
        return item.state if item is not None else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": {k: self.metrics[k].to_dict() for k in sorted(self.metrics)},
            "overrides_applied": list(self.overrides),
        }

    def hash(self) -> str:
        from .hashing import sha256_of

        return sha256_of(self.to_dict())


def derive(
    canonical: CanonicalInput,
    config: Mapping[str, Any],
    peers: PeerSnapshot,
    market: MarketSnapshot,
    evaluation_datetime: Optional[datetime] = None,
) -> DerivedMetrics:
    """Compute every registered metric for the supplied snapshot.

    Pure with respect to its arguments: nothing is mutated and no source is
    read (tech design s5).
    """
    # A snapshot that was never supplied behaves exactly like a snapshot that
    # is entirely missing: every market/peer metric resolves to UNKNOWN rather
    # than crashing the run (spec s3.2 - absence is UNKNOWN, never a value).
    if market is None:
        market = MarketSnapshot(snapshot_id="", as_of=None, blocks=(), staleness_hours=0)
    if peers is None:
        peers = PeerSnapshot(
            snapshot_id="",
            as_of=None,
            observations=(),
            staleness_days=0,
            min_listed_years=0.0,
        )

    ctx = DerivationContext(
        canonical=canonical,
        config=config,
        peers=peers,
        market=market,
        evaluation_datetime=evaluation_datetime or datetime.now(timezone.utc),
    )
    metrics: Dict[str, MetricValue] = {}
    for metric_id in sorted(REGISTRY):
        metrics[metric_id] = REGISTRY[metric_id](ctx)

    # Manual overrides declared on the input win over computed values, but
    # they are recorded so the audit trail shows they were applied.
    overrides = canonical.raw.get("metric_overrides") or {}
    applied: List[str] = []
    for metric_id, raw in sorted(overrides.items()):
        if metric_id not in metrics:
            continue
        existing = metrics[metric_id]
        metrics[metric_id] = MetricValue(
            metric_id=metric_id,
            state=VALUE,
            value=raw,
            kind=existing.kind,
            formula=existing.formula,
            inputs=existing.inputs,
            reason="manual metric override supplied on the input document",
            evidence_refs=existing.evidence_refs,
        )
        applied.append(metric_id)

    return DerivedMetrics(metrics=metrics, overrides=tuple(applied))


__all__ = [
    "MetricValue",
    "DerivedMetrics",
    "DerivationContext",
    "REGISTRY",
    "derive",
    "metric",
]
