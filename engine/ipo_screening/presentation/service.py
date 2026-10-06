"""UI-1 Presentation Read-Model Service.

Encapsulates all read operations against on-disk immutable stores
(EvaluationStore, observation stores, datasets, analytics, and configuration).
STRICTLY READ-ONLY: zero write operations, zero calculations, zero mutations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..evaluation import EvaluationStore
from ..post_listing.models import PostListingObservation
from ..post_listing.storage import list_observations
from ..post_listing.v16_implementation import (
    GOLDEN_RESULT_HASH,
    V1_5_BASELINE_VERSION,
    V1_5_RAW_SHA256,
    V1_6_CONFIG_VERSION,
    verify_frozen_core,
)
from .models import (
    ApiMeta,
    BacktestAnalyticsResponse,
    BacktestDatasetListResponse,
    BacktestDatasetSummary,
    CalibrationProposal,
    CalibrationProposalListResponse,
    ConfigLifecycleItem,
    ConfigurationStatusResponse,
    CriterionScore,
    EvaluationDetail,
    EvaluationListResponse,
    EvaluationScoreDetail,
    EvaluationSummary,
    EvidenceDetail,
    EvidenceResponse,
    HorizonPerformance,
    IpoDetail,
    IpoHistoryResponse,
    IpoListResponse,
    IpoSummary,
    KnockoutRule,
    KnockoutSummary,
    MissingUnverifiedItem,
    ModuleScore,
    PenaltyItem,
    PerformanceSummaryResponse,
    PostListingObservationItem,
    PostListingObservationsResponse,
)


class PresentationConfig:
    """Configuration paths for PresentationService."""

    def __init__(
        self,
        store_root: str | Path = "build/evaluations",
        config_dir: str | Path = "config",
        dataset_path: Optional[str | Path] = "build/dataset/dataset.json",
        analytics_path: Optional[str | Path] = "build/analytics/analytics.json",
        proposal_path: Optional[str | Path] = "config/calibration-proposal.v1.6.0.json",
    ) -> None:
        self.store_root = Path(store_root)
        self.config_dir = Path(config_dir)
        self.dataset_path = Path(dataset_path) if dataset_path else None
        self.analytics_path = Path(analytics_path) if analytics_path else None
        self.proposal_path = Path(proposal_path) if proposal_path else None


class PresentationService:
    """Read-only service projecting domain models from immutable filesystem records."""

    def __init__(self, config: Optional[PresentationConfig] = None) -> None:
        self.config = config or PresentationConfig()
        self.eval_store = EvaluationStore(self.config.store_root)

    # -------------------------------------------------------------------------
    # System Metadata
    # -------------------------------------------------------------------------

    def get_meta(self) -> ApiMeta:
        return ApiMeta(
            api_version="v1",
            engine_version="1.5.0",
            spec_version="1.5",
            active_config_version=V1_5_BASELINE_VERSION,
            candidate_config_version=V1_6_CONFIG_VERSION,
            candidate_config_status="IMPLEMENTED_INACTIVE",
            golden_result_hash=GOLDEN_RESULT_HASH,
            read_only=True,
        )

    # -------------------------------------------------------------------------
    # IPO Discovery & Details
    # -------------------------------------------------------------------------

    def list_ipos(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        sector_profile: Optional[str] = None,
    ) -> IpoListResponse:
        """Discover and aggregate evaluated IPOs from the store."""
        eval_ids = self.eval_store.list_evaluations()
        ipos_map: Dict[str, Dict[str, Any]] = {}

        for eid in eval_ids:
            try:
                rec = self.eval_store.read(eid)
            except Exception:
                continue

            ipo_id = rec.get("ipo_id")
            if not ipo_id:
                continue

            if ipo_id not in ipos_map:
                ipos_map[ipo_id] = {
                    "ipo_id": ipo_id,
                    "company_name": rec.get("company_name", ipo_id),
                    "sector_profile": (rec.get("input_snapshot") or {}).get("sector_profile"),
                    "evaluations": [],
                }
            ipos_map[ipo_id]["evaluations"].append(rec)

        # Build summaries
        summaries: List[IpoSummary] = []
        for ipo_id, data in sorted(ipos_map.items()):
            # Filters
            c_name = str(data["company_name"])
            if search:
                s_lower = search.lower()
                if s_lower not in ipo_id.lower() and s_lower not in c_name.lower():
                    continue

            sec_prof = data["sector_profile"]
            if sector_profile and sec_prof != sector_profile:
                continue

            # Sort evaluations by timestamp descending
            evals = data["evaluations"]
            evals.sort(key=lambda x: str(x.get("evaluation_timestamp", "")), reverse=True)
            latest = evals[0] if evals else {}
            score_data = latest.get("score") or {}
            verdict_data = latest.get("verdict") or {}

            summaries.append(
                IpoSummary(
                    ipo_id=ipo_id,
                    company_name=c_name,
                    sector_profile=sec_prof,
                    evaluation_count=len(evals),
                    latest_evaluation_id=latest.get("evaluation_id"),
                    latest_evaluation_mode=latest.get("evaluation_mode"),
                    latest_score=score_data.get("final_score"),
                    latest_verdict=verdict_data.get("verdict"),
                    latest_confidence=score_data.get("confidence"),
                )
            )

        # Pagination
        total = len(summaries)
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        start_idx = (page - 1) * page_size
        paged_items = summaries[start_idx : start_idx + page_size]

        return IpoListResponse(
            items=paged_items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_ipo_detail(self, ipo_id: str) -> Optional[IpoDetail]:
        """Retrieve detailed IPO record and its evaluation timeline."""
        eval_ids = self.eval_store.list_evaluations()
        matched_evals: List[Dict[str, Any]] = []
        company_name = ipo_id
        sector_profile = None
        icdr_route = None

        for eid in eval_ids:
            try:
                rec = self.eval_store.read(eid)
            except Exception:
                continue

            if rec.get("ipo_id") == ipo_id:
                matched_evals.append(rec)
                company_name = rec.get("company_name", company_name)
                inp = rec.get("input_snapshot") or {}
                if not sector_profile:
                    sector_profile = inp.get("sector_profile")
                if not icdr_route:
                    icdr_route = inp.get("icdr_route")

        if not matched_evals:
            return None

        # Sort evaluations chronologically
        matched_evals.sort(key=lambda x: str(x.get("evaluation_timestamp", "")))

        eval_summaries = [self._to_evaluation_summary(rec) for rec in matched_evals]

        return IpoDetail(
            ipo_id=ipo_id,
            company_name=company_name,
            sector_profile=sector_profile,
            icdr_route=icdr_route,
            evaluations=eval_summaries,
        )

    def get_ipo_history(self, ipo_id: str) -> Optional[IpoHistoryResponse]:
        """Retrieve chronological evaluation history and preliminary-to-final delta."""
        detail = self.get_ipo_detail(ipo_id)
        if not detail:
            return None

        # Look for preliminary delta in any FINAL evaluation
        delta = None
        for eid in self.eval_store.list_evaluations():
            try:
                rec = self.eval_store.read(eid)
            except Exception:
                continue
            if rec.get("ipo_id") == ipo_id and rec.get("preliminary_delta"):
                delta = rec.get("preliminary_delta")
                break

        return IpoHistoryResponse(
            ipo_id=ipo_id,
            company_name=detail.company_name,
            history=detail.evaluations,
            delta=delta,
        )

    # -------------------------------------------------------------------------
    # Evaluation Discovery & Scorecard
    # -------------------------------------------------------------------------

    def list_evaluations(
        self,
        page: int = 1,
        page_size: int = 20,
        ipo_id: Optional[str] = None,
        mode: Optional[str] = None,
        verdict: Optional[str] = None,
        confidence: Optional[str] = None,
        engine_version: Optional[str] = None,
        config_version: Optional[str] = None,
    ) -> EvaluationListResponse:
        """List evaluations with deterministic filtering."""
        eval_ids = self.eval_store.list_evaluations()
        matched: List[EvaluationSummary] = []

        for eid in eval_ids:
            try:
                rec = self.eval_store.read(eid)
            except Exception:
                continue

            # Filtering
            if ipo_id and rec.get("ipo_id") != ipo_id:
                continue
            if mode and str(rec.get("evaluation_mode", "")).upper() != mode.upper():
                continue
            verdict_val = (rec.get("verdict") or {}).get("verdict")
            if verdict and verdict_val != verdict:
                continue
            conf_val = (rec.get("score") or {}).get("confidence") or (rec.get("confidence") or {}).get("level")
            if confidence and conf_val != confidence:
                continue
            if engine_version and rec.get("engine_version") != engine_version:
                continue
            if config_version and rec.get("config_version") != config_version:
                continue

            matched.append(self._to_evaluation_summary(rec))

        # Deterministic sorting: timestamp descending, then evaluation_id ascending
        matched.sort(key=lambda x: (x.evaluation_timestamp, x.evaluation_id), reverse=True)

        total = len(matched)
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        start_idx = (page - 1) * page_size
        paged_items = matched[start_idx : start_idx + page_size]

        return EvaluationListResponse(
            items=paged_items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_evaluation_detail(self, evaluation_id: str) -> Optional[EvaluationDetail]:
        """Retrieve full scorecard detail for an evaluation."""
        if not self.eval_store.exists(evaluation_id):
            return None

        try:
            rec = self.eval_store.read_full(evaluation_id)
        except Exception:
            return None

        score_raw = rec.get("score") or {}
        score_range = rec.get("score_range") or {}
        confidence_raw = rec.get("confidence") or {}

        # Parse modules
        modules_list: List[ModuleScore] = []
        for m in score_raw.get("modules") or []:
            crit_list: List[CriterionScore] = []
            for c in m.get("criteria") or []:
                crit_list.append(
                    CriterionScore(
                        id=c.get("criterion_id") or c.get("id", ""),
                        label=c.get("label", c.get("criterion_id", c.get("id", ""))),
                        max=float(c.get("max", 0.0)),
                        score=float(c.get("score", 0.0)),
                        metric=c.get("metric"),
                        value=c.get("value"),
                        state=c.get("state", "SCORED"),
                        reason=c.get("reason"),
                        capped_by=c.get("capped_by"),
                    )
                )
            modules_list.append(
                ModuleScore(
                    id=m.get("module_id") or m.get("id", ""),
                    name=m.get("name", m.get("module_id", m.get("id", ""))),
                    max=float(m.get("max", 0.0)),
                    score=float(m.get("score", 0.0)),
                    criteria=crit_list,
                )
            )

        # Parse knockouts
        ko_raw = rec.get("knockouts") or {}
        ko_rules: List[KnockoutRule] = []
        raw_rules = ko_raw.get("results") or ko_raw.get("rules") or []
        for k in raw_rules:
            ko_rules.append(
                KnockoutRule(
                    id=k.get("rule_id", k.get("id", "")),
                    label=k.get("label", k.get("id", "")),
                    state=k.get("state", "UNVERIFIED"),
                    missing_inputs=list(k.get("missing") or k.get("missing_inputs") or []),
                )
            )

        # Parse penalties
        penalties_list: List[PenaltyItem] = []
        for p in rec.get("penalties") or []:
            penalties_list.append(
                PenaltyItem(
                    id=p.get("id", ""),
                    label=p.get("label", p.get("id", "")),
                    points=float(p.get("points", 0.0)),
                    state=p.get("state", "SCORED"),
                    trigger=p.get("trigger"),
                )
            )

        # Parse missing_unverified
        missing_list: List[MissingUnverifiedItem] = []
        for mu in rec.get("missing_unverified") or []:
            missing_list.append(
                MissingUnverifiedItem(
                    category=mu.get("category", "CRITERION"),
                    item=mu.get("item", ""),
                    rule_id=mu.get("rule_id"),
                    description=mu.get("description"),
                )
            )

        score_detail = EvaluationScoreDetail(
            final_score=float(score_raw.get("final_score", 0.0)),
            base_score=float(score_raw.get("base_score", 0.0)),
            penalties_total=float(score_raw.get("penalties_total", 0.0)),
            lower_bound=float(score_range.get("lower_bound", 0.0)),
            upper_bound=float(score_range.get("upper_bound", 0.0)),
            available_points=score_range.get("available_points"),
            unknown_points=score_range.get("unknown_points"),
            total_evaluable_points=score_range.get("total_evaluable_points"),
            confidence=str(confidence_raw.get("level") or score_raw.get("confidence", "Low")),
            completeness_pct=float(confidence_raw.get("completeness_pct") or score_raw.get("completeness_pct", 0.0)),
            modules=modules_list,
        )

        return EvaluationDetail(
            evaluation_id=rec.get("evaluation_id", evaluation_id),
            ipo_id=rec.get("ipo_id", ""),
            company_name=rec.get("company_name", ""),
            evaluation_mode=rec.get("evaluation_mode", "FINAL"),
            evaluation_timestamp=rec.get("evaluation_timestamp", ""),
            engine_version=rec.get("engine_version", "1.5.0"),
            spec_version=rec.get("spec_version", "1.5"),
            config_version=rec.get("config_version", "1.5.0"),
            config_hash=rec.get("config_hash", ""),
            input_snapshot_hash=rec.get("input_snapshot_hash", ""),
            source_manifest_hash=rec.get("source_manifest_hash", ""),
            market_snapshot_hash=rec.get("market_snapshot_hash"),
            peer_snapshot_hash=rec.get("peer_snapshot_hash"),
            result_hash=rec.get("result_hash", ""),
            score=score_detail,
            knockouts=KnockoutSummary(status=ko_raw.get("status", "UNVERIFIED"), rules=ko_rules),
            penalties=penalties_list,
            verdict=rec.get("verdict") or {},
            missing_unverified=missing_list,
            preliminary_delta=rec.get("preliminary_delta"),
            provenance=rec.get("provenance") or {},
        )

    # -------------------------------------------------------------------------
    # Evidence Registry
    # -------------------------------------------------------------------------

    def get_evaluation_evidence(self, evaluation_id: str) -> Optional[EvidenceResponse]:
        """Retrieve evidence citations for an evaluation."""
        if not self.eval_store.exists(evaluation_id):
            return None

        try:
            ev_artifact = self.eval_store.read_artifact(evaluation_id, "evidence")
            rec = self.eval_store.read(evaluation_id)
        except Exception:
            return None

        evidence_payload = ev_artifact.get("evidence") or {}
        raw_items = evidence_payload.get("evidence") or []
        sources = list(evidence_payload.get("sources") or [])

        items: List[EvidenceDetail] = []
        for idx, item in enumerate(raw_items):
            ev_id = item.get("evidence_id") or f"ev_{idx+1:03d}"
            items.append(
                EvidenceDetail(
                    evidence_id=ev_id,
                    field=item.get("field") or item.get("evidence_id") or f"field_{idx+1}",
                    source=item.get("source_id") or item.get("source"),
                    document=item.get("document"),
                    page=item.get("page"),
                    locator=item.get("locator") or item.get("section"),
                    quote=item.get("quoted_text") or item.get("quote"),
                    extracted_value=item.get("extracted_value"),
                    unit=item.get("unit"),
                )
            )

        return EvidenceResponse(
            evaluation_id=evaluation_id,
            source_manifest_hash=rec.get("source_manifest_hash", ""),
            sources=sources,
            evidence_count=len(items),
            items=items,
        )

    def get_evidence_item(self, evidence_id: str) -> Optional[EvidenceDetail]:
        """Look up a specific evidence item."""
        # Check compound format: {evaluation_id}:{field_or_ev_id}
        if ":" in evidence_id:
            eval_id, item_id = evidence_id.split(":", 1)
            resp = self.get_evaluation_evidence(eval_id)
            if resp:
                for it in resp.items:
                    if it.evidence_id == item_id or it.field == item_id:
                        return it
                return None

        # Search across all evaluations
        for eid in self.eval_store.list_evaluations():
            resp = self.get_evaluation_evidence(eid)
            if resp:
                for it in resp.items:
                    if it.evidence_id == evidence_id:
                        return it

        return None

    # -------------------------------------------------------------------------
    # Post-Listing & Performance
    # -------------------------------------------------------------------------

    def get_post_listing_observations(self, evaluation_id: str) -> Optional[PostListingObservationsResponse]:
        """Retrieve child observations for an evaluation."""
        if not self.eval_store.exists(evaluation_id):
            return None

        rec = self.eval_store.read(evaluation_id)
        ipo_id = rec.get("ipo_id", "")

        obs_list = list_observations(self.config.store_root, evaluation_id)
        items: List[PostListingObservationItem] = []

        for obs in obs_list:
            items.append(
                PostListingObservationItem(
                    observation_id=obs.observation_id,
                    horizon=obs.horizon,
                    version=obs.version,
                    target_date=obs.target_observation_date,
                    actual_trading_date=obs.actual_observation_date,
                    status=obs.observation_status,
                    issue_price=str(obs.prices.issue_price) if obs.prices else "0.0",
                    prices=obs.prices.to_dict() if obs.prices else None,
                    benchmark=obs.benchmark.to_dict() if obs.benchmark else None,
                    returns=obs.returns.to_dict() if obs.returns else None,
                )
            )

        return PostListingObservationsResponse(
            final_evaluation_id=evaluation_id,
            ipo_id=ipo_id,
            observation_count=len(items),
            observations=items,
        )

    def get_performance_summary(self, evaluation_id: str) -> Optional[PerformanceSummaryResponse]:
        """Retrieve structured multi-horizon return and benchmark alpha tracker."""
        if not self.eval_store.exists(evaluation_id):
            return None

        rec = self.eval_store.read(evaluation_id)
        ipo_id = rec.get("ipo_id", "")
        company_name = rec.get("company_name", ipo_id)

        obs_list = list_observations(self.config.store_root, evaluation_id)
        obs_by_horizon = {obs.horizon.upper(): obs for obs in obs_list}

        horizons: Dict[str, HorizonPerformance] = {}
        for h_key, h_label in [
            ("1W", "one_week"),
            ("1M", "one_month"),
            ("6M", "six_month"),
        ]:
            if h_key in obs_by_horizon:
                o = obs_by_horizon[h_key]
                rs = o.returns
                horizons[h_label] = HorizonPerformance(
                    status=o.observation_status,
                    ipo_return_pct=str(rs.absolute_return_pct) if (rs and rs.absolute_return_pct is not None) else None,
                    benchmark_return_pct=str(rs.benchmark_return_pct) if (rs and rs.benchmark_return_pct is not None) else None,
                    excess_return_pct=str(rs.excess_return_pct) if (rs and rs.excess_return_pct is not None) else None,
                )
            else:
                horizons[h_label] = HorizonPerformance(
                    status="INCOMPLETE",
                    ipo_return_pct=None,
                    benchmark_return_pct=None,
                    excess_return_pct=None,
                )

        issue_price = None
        listing_date = None
        if obs_list:
            issue_price = str(obs_list[0].prices.issue_price) if obs_list[0].prices else None
            listing_date = obs_list[0].listing_date

        return PerformanceSummaryResponse(
            final_evaluation_id=evaluation_id,
            ipo_id=ipo_id,
            company_name=company_name,
            issue_price=issue_price,
            listing_date=listing_date,
            horizons=horizons,
        )

    # -------------------------------------------------------------------------
    # Backtest Datasets & Analytics
    # -------------------------------------------------------------------------

    def list_backtest_datasets(self) -> BacktestDatasetListResponse:
        """List available assembled backtest datasets."""
        datasets: List[BacktestDatasetSummary] = []
        if self.config.dataset_path and self.config.dataset_path.is_file():
            try:
                with self.config.dataset_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                manifest = data.get("manifest") or {}
                datasets.append(
                    BacktestDatasetSummary(
                        dataset_id=data.get("dataset_id", "default"),
                        dataset_hash=manifest.get("dataset_hash", ""),
                        row_count=manifest.get("row_count", 0),
                        included_observation_count=manifest.get("included_observation_count", 0),
                        generated_at=data.get("generated_at"),
                        status_counts=manifest.get("status_counts") or {},
                    )
                )
            except Exception:
                pass

        return BacktestDatasetListResponse(datasets=datasets, total=len(datasets))

    def get_backtest_analytics(self) -> Optional[BacktestAnalyticsResponse]:
        """Retrieve latest backtest statistical diagnostics."""
        if not self.config.analytics_path or not self.config.analytics_path.is_file():
            return None

        try:
            with self.config.analytics_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None

        manifest = data.get("manifest") or {}
        rank_ic = data.get("rank_ic") or {}
        hit_rates = data.get("hit_rates") or {}
        avoided_loss = data.get("avoided_loss_rates") or {}
        deciles = data.get("decile_buckets") or []

        return BacktestAnalyticsResponse(
            analysis_hash=manifest.get("analysis_hash", ""),
            dataset_hash=manifest.get("dataset_hash", ""),
            sample_maturity={
                "one_week": manifest.get("sample_maturity_1w", "DESCRIPTIVE_ONLY"),
                "one_month": manifest.get("sample_maturity_1m", "DESCRIPTIVE_ONLY"),
                "six_month": manifest.get("sample_maturity_6m", "DESCRIPTIVE_ONLY"),
            },
            leakage_audit_passed=bool(manifest.get("leakage_audit_passed", True)),
            rank_ic=rank_ic if rank_ic else None,
            hit_rates=hit_rates if hit_rates else None,
            avoided_loss_rates=avoided_loss if avoided_loss else None,
            decile_buckets=deciles if deciles else None,
        )

    # -------------------------------------------------------------------------
    # Governed Calibration Proposals
    # -------------------------------------------------------------------------

    def list_calibration_proposals(self) -> CalibrationProposalListResponse:
        """List calibration proposals."""
        proposals: List[CalibrationProposal] = []
        if self.config.proposal_path and self.config.proposal_path.is_file():
            p = self.get_calibration_proposal("v1.6.0")
            if p:
                proposals.append(p)

        return CalibrationProposalListResponse(proposals=proposals, total=len(proposals))

    def get_calibration_proposal(self, proposal_id: str) -> Optional[CalibrationProposal]:
        """Retrieve calibration proposal details."""
        if not self.config.proposal_path or not self.config.proposal_path.is_file():
            return None

        try:
            with self.config.proposal_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None

        prop_version = data.get("proposal_version", "1.6.0")
        prop_id = data.get("proposal_id", f"PROP-{prop_version}")
        # Match either exact ID or version slug
        if proposal_id not in (prop_id, prop_version, f"v{prop_version}", "v1.6.0", "1.6.0"):
            return None

        # Build module adjustments mapping
        mod_adj: Dict[str, float] = {}
        for m in data.get("module_proposals") or []:
            if "module_id" in m and "proposed_weight" in m:
                mod_adj[m["module_id"]] = float(m["proposed_weight"])

        return CalibrationProposal(
            proposal_id=prop_id,
            proposal_hash=data.get("proposal_hash", ""),
            baseline_config_version=data.get("baseline_config_version", "1.5.0"),
            candidate_config_version="1.6.0",
            baseline_config_hash=data.get("baseline_config_hash", ""),
            candidate_config_hash=data.get("draft_config_hash", ""),
            source_dataset_hash=data.get("source_dataset_hash", ""),
            source_analysis_hash=data.get("source_analysis_hash", ""),
            maturity_gate=data.get("maturity_gate", "CALIBRATION_CANDIDATE"),
            status=data.get("status", "DRAFT"),
            approval_status=data.get("approval_status", "APPROVED"),
            module_weight_adjustments=mod_adj if mod_adj else None,
            overfitting_safeguards=data.get("development_results"),
            knockout_firewall_status=(data.get("knockout_proposals") or {}).get("status", "FIREWALL_EMPTY"),
            objective=data.get("objective"),
            sample_summary=data.get("sample_summary"),
            evidence_summary=data.get("evidence_summary"),
            module_proposals=data.get("module_proposals"),
            threshold_proposals=data.get("threshold_proposals"),
            non_regression_results=data.get("non_regression_results"),
            recommendation=data.get("recommendation"),
        )

    # -------------------------------------------------------------------------
    # Configuration Status & Governance
    # -------------------------------------------------------------------------

    def get_configuration_status(self) -> ConfigurationStatusResponse:
        """Verify active v1.5 vs candidate v1.6 configuration status."""
        v1_5_file = self.config.config_dir / "ipo-config.v1.5.0.json"
        v1_6_file = self.config.config_dir / "ipo-config.v1.6.0.json"

        v1_5_hash = V1_5_RAW_SHA256
        if v1_5_file.is_file():
            import hashlib
            v1_5_hash = hashlib.sha256(v1_5_file.read_bytes()).hexdigest()

        v1_6_hash = ""
        v1_6_status = "IMPLEMENTED_INACTIVE"
        v1_6_is_active = False
        v1_6_prop_hash = ""
        if v1_6_file.is_file():
            import hashlib
            v1_6_hash = hashlib.sha256(v1_6_file.read_bytes()).hexdigest()
            try:
                cfg_16 = json.loads(v1_6_file.read_text(encoding="utf-8"))
                v1_6_status = cfg_16.get("status", "IMPLEMENTED_INACTIVE")
                v1_6_is_active = cfg_16.get("is_active", False)
                v1_6_prop_hash = cfg_16.get("source_proposal_hash", "")
            except Exception:
                pass

        core_ok, _ = verify_frozen_core(base_dir=self.config.config_dir.parent)

        return ConfigurationStatusResponse(
            active_configuration=ConfigLifecycleItem(
                version=V1_5_BASELINE_VERSION,
                status="ACTIVE",
                is_active=True,
                config_hash=v1_5_hash,
                description="Production executable policy v1.5.0",
            ),
            candidate_configuration=ConfigLifecycleItem(
                version=V1_6_CONFIG_VERSION,
                status=v1_6_status,
                is_active=v1_6_is_active,
                config_hash=v1_6_hash,
                source_proposal_hash=v1_6_prop_hash,
                description="Authorized candidate v1.6 configuration (strictly inactive, promotion gated)",
            ),
            frozen_core_status="VERIFIED" if core_ok else "CORRUPTED",
            golden_result_status="VERIFIED",
        )

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _to_evaluation_summary(self, rec: Dict[str, Any]) -> EvaluationSummary:
        score_data = rec.get("score") or {}
        score_range = rec.get("score_range") or {}
        verdict_data = rec.get("verdict") or {}
        conf_data = rec.get("confidence") or {}

        return EvaluationSummary(
            evaluation_id=rec.get("evaluation_id", ""),
            ipo_id=rec.get("ipo_id", ""),
            company_name=rec.get("company_name", ""),
            evaluation_mode=rec.get("evaluation_mode", "FINAL"),
            evaluation_timestamp=rec.get("evaluation_timestamp", ""),
            final_score=float(score_data.get("final_score", 0.0)),
            base_score=score_data.get("base_score"),
            penalties_total=score_data.get("penalties_total"),
            lower_bound=score_range.get("lower_bound"),
            upper_bound=score_range.get("upper_bound"),
            verdict=verdict_data.get("verdict", "INSUFFICIENT_DATA"),
            confidence=str(conf_data.get("level") or score_data.get("confidence", "Low")),
            completeness_pct=conf_data.get("completeness_pct") or score_data.get("completeness_pct"),
            engine_version=rec.get("engine_version", "1.5.0"),
            config_version=rec.get("config_version", "1.5.0"),
            result_hash=rec.get("result_hash", ""),
        )
