# Spec-to-Code Traceability Matrix — IPO Screening Engine v1.5

**Repository:** `ramkivs/ipo-screening-engine`
**Branch:** `arena/01a10abc-ipo-screening-engine`
**Baseline:** `main @ 01ba66c`
**Engine version:** 1.5.0 · **Spec version:** 1.5 · **Config version:** 1.5.0
**Prepared:** 2026-10-05

---

## 0. How to read this matrix

Every normative requirement is listed once, with:

| Column | Meaning |
| --- | --- |
| **ID** | Spec section, or `P<n>` / `S<n>` for the Execution Prompt s19 matrix and Specification s26 list |
| **Requirement** | The requirement in one line |
| **Implementation** | File and symbol that satisfies it |
| **Test** | The named test that proves it |
| **Status** | `DONE`, `DONE (documented divergence)`, or `BLOCKED` |

Governing precedence applied throughout: **Specification v1.5 > Technical Design
v1.5 > Execution Prompt > Artifact Manifest**. Where the reference/prototype
artifacts disagree with v1.5, v1.5 wins; those decisions are recorded in
section 4 of this document.

Run the whole matrix with:

```bash
PYTHONPATH=engine python3 -m pytest tests/ -q
```

---

## 1. Non-negotiable design principles (Spec s3)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| 3.1 | Deterministic scoring: same inputs + snapshot + config + engine version → same result hash | `hashing.sha256_of`, `evaluation.compute_result_hash`, `build_record` builds an explicit `result_payload` with no timestamps or IDs | `test_p30_reproducibility_hash_is_a_pure_function_of_the_inputs`, `test_result_hash_is_stable_across_processes`, `test_same_inputs_produce_the_same_result_hash_twice` | DONE |
| 3.2 | Unknown is not zero; never `x \|\| 0` | `canonical.Value` (constructed-only) + `Value.UNKNOWN`; every derivation uses `_u(...)` for absence. `derived._use_of_proceeds_bucket` and `derived._margin_trend` return UNKNOWN rather than defaulting | `test_unknown_metric_does_not_become_zero`, `test_absent_boolean_flag_is_unknown_not_false`, `test_p14_partially_disclosed_category_is_unknown_not_understated`, `test_cfo_pat_is_unknown_when_a_year_is_missing` | DONE |
| 3.3 | Three-state knockout evaluation | `knockouts.Truth` (Kleene), `k_and/k_or/k_not`, `evaluate_expression`, `KnockoutSummary.status` | `test_kleene_and_matches_the_specification_table`, `test_kleene_or_matches_the_specification_table`, `test_kleene_not_is_involution`, `test_p13_s6_stale_peers_cannot_score_as_current` | DONE |
| 3.4 | Evidence before score | `canonical.Evidence`, `EvidenceRegistry`, `canonical_input._evidence` → path index, `semantic_validation._validate_provenance`, `Evidence` sheet, `provenance` in the record | `test_golden_evidence_is_grounded_in_the_rhp`, `test_evidence_sheet_lists_every_evidence_item`, `test_criteria_reference_their_metric_and_evidence` | DONE |
| 3.5 | Configuration is executable policy; invalid config blocks scoring | `config_validation.check_config/compile_config`, `ConfigValidationError`, `pipeline.evaluate` requires `_fingerprint` | `test_p17_s14_invalid_config_blocks_scoring`, `test_invalid_config_blocks_scoring`, `test_check_config_refuses_a_broken_configuration` | DONE |
| 3.6 | Excel is an output/preservation surface, never an implicit source of truth | `excel.py` is a pure projection of `EvaluationRecord`; `Run_Log`/`IPO_Master` are derived, never read back | `test_workbook_is_generated_from_stored_records_not_hand_edited`, `test_every_displayed_number_traces_to_the_record` | DONE |

## 2. Inputs and data model (Spec s4, s5)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| 4.1 | Offer: price band, fresh issue, OFS, dates, quotas, sellers, lock-in | `schema/ipo-input.v1.5.schema.json#/properties/issue`; `canonical_input.build_canonical_input`; derived `fresh_share_pct`, `ofs_share_pct`, `dilution_pct` | `test_p1_s1_vishal_nirmiti_mainboard_retail_heavy`, `test_p2_s2_pure_ofs_offer`, `test_p23_retail_heavy_structure_overlay` | DONE |
| 4.2 | Financials: 3 FY minimum, restated, unit-normalised | `canonical_input.FinancialPeriod`, `unit_factor`/`UNIT_TO_CRORE`, `derived.revenue_cagr_2y_from_3fy`, `cfo_pat_cumulative`, `roce_latest` | `test_fewer_than_three_full_fiscal_years_is_rejected`, `test_p10_s7_contingent_liabilities_above_50pct_of_net_worth`, `test_unknown_unit_raises` | DONE |
| 4.3 | Governance: auditor opinion, going concern, litigation, regulatory action, RPT, board/KMP | `derived.auditor_bucket`, `going_concern_uncertainty`, `litigation_bucket`, `sebi_ed_action_active`, `rpt_pct_revenue`, `board_kmp_bucket` (11 pass-through metrics) | `test_p3_s3_qualified_audit_opinion_triggers_k1`, `test_p4_going_concern_uncertainty_triggers_k1`, `test_p7_s12_active_sebi_action_triggers_k2` | DONE |
| 4.4 | Business: industry CAGR, moat, concentration, visibility, order book | `derived.industry_cagr_pct`, `moat_rating`, `top5_concentration_pct`, `visibility_rating`, `order_book` | `test_p19_s8_epc_overlay_with_negative_cfo_but_strong_order_book`, `test_p12_unknown_rpt_growth_is_unverified_not_clear` | DONE |
| 4.5 | Peers: VALID / STALE / UNUSABLE / MISSING; median over VALID only | `snapshots.classify_peers`, `PeerSnapshot.median`, `PEER_*` constants | `test_p13_s6_stale_peers_cannot_score_as_current`, `test_p13_fresh_peers_are_used`, `test_peers_are_classified_stale_with_the_reason` | DONE |
| 4.6 | Market snapshots: FRESH / STALE / MISSING per block; stale == missing | `snapshots.build_market_snapshot`, `MarketSnapshot.value` returns `None` for non-FRESH | `test_result_hash_changes_when_the_snapshot_materially_changes`, `test_p13_s6_stale_peers_cannot_score_as_current` | DONE |
| 5 | Data model: constructed-only `Value`, `State`, `Verification`, `ExtractionMethod` | `canonical.State`, `Verification`, `ExtractionMethod`, `SourceType`, `SourceRef`, `Evidence`, `Value` | `test_every_derived_metric_carries_formula_and_inputs`, `test_criteria_reference_their_metric_and_evidence` | DONE |

## 3. Scoring modules (Spec s7–s13)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| 7 | Growth is `(FY_latest / FY_3back) ** (1/2) - 1`, labelled "2Y from 3 FY", never "3Y" | `derived._revenue_cagr_2y_from_3fy`; `revenue_cagr_3y_from_4fy` exists separately and needs 4 FY | `test_revenue_cagr_is_2y_from_3fy_not_a_3y_cagr`, `test_three_year_cagr_is_available_only_with_four_fy` | DONE |
| 8 | Financial Quality, 25 pts (CAGR 6 / profit trend 5 / ROCE 5 / CFO:PAT 5 / leverage 4) | `config.modules[A]`; `derived.roce_latest` (EBIT / (equity + borrowings)), `cfo_pat_cumulative` = ΣCFO/ΣPAT | `test_cfo_pat_is_cumulative_not_an_average_of_ratios`, `test_roce_uses_ebit_over_capital_employed`, `test_leverage_bands_follow_the_configuration` | DONE |
| 9 | Valuation, 20 pts (P/E vs peers 8, second multiple 4, PEG/loss 4, sector IPO valuation 4) | `config.modules[B]`; `derived.pe_premium_pct`, `second_multiple_premium_pct`, `peg` (with low-base-year cap), `sector_ipo_relative` | `test_p13_s6_stale_peers_cannot_score_as_current`, `test_disclosed_roce_overrides_the_computed_value` | DONE |
| 10 | Issue Structure & Proceeds, 15 pts; GCP `[●]` ⇒ UNKNOWN with the legal max held separately | `config.modules[C]`; `derived.gcp_amount`, `gcp_legal_max`, `use_of_proceeds_bucket`, `dilution_ok` | `test_p14_s4_missing_gcp_is_unknown_not_the_ceiling`, `test_p14_proceeds_bucket_classifies_each_disclosure_pattern`, `test_gcp_ceiling_recorded_as_an_amount_is_rejected` | DONE |
| 11 | Governance, 15 pts | `config.modules[D]`; `derived.auditor_bucket`, `rpt_pct_revenue`, `board_kmp_bucket`, `litigation_bucket`, `promoter_post_pct` | `test_p15_s5_missing_promoter_holding_is_unknown`, `test_p3_s3_qualified_audit_opinion_triggers_k1` | DONE |
| 12 | Business & Moat, 15 pts | `config.modules[E]`; `industry_cagr_pct`, `moat_rating`, `top5_concentration_pct`, `visibility_rating` | `test_p19_s8_epc_overlay_with_negative_cfo_but_strong_order_book` | DONE |
| 13 | Market & Demand, 10 pts | `config.modules[F]`; `anchor_bucket`, `qib_x`, `gmp_bucket`, `market_regime_bucket` | `test_p23_retail_heavy_structure_overlay`, `test_p23_normal_structure_keeps_anchor_criteria` | DONE |

## 4. Overlays and knockouts (Spec s14–s17)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| 14 | Sector overlays are mandatory and executable; an unimplemented overlay fails at config-validation time | `overlays.resolve_overlays` raises `OVERLAY_SELECTED_BUT_NOT_IMPLEMENTED`; `config_validation` checks every add/remove/override and reconciles to 100 | `test_overlay_that_does_not_reconcile_is_rejected`, `test_overlay_metric_not_implemented_is_rejected`, `test_every_sector_overlay_reconciles_to_100` | DONE |
| 14 (financial) | Financial overlay: NIM/cost-income, ROA/ROE vs peers, asset quality, CRAR, P/B–ROE | `config.sector_overlays.financial`; `derived.nim_cost_income_bucket`, `roa_roe_peer_quartile`, `asset_quality_bucket`, `crar_buffer_pts`, `pb_roe_adjusted_premium_pct` | plan: `test_p18_financial_institution_overlay`, `test_sector_overlay_replaces_criteria`; metrics: `test_financial_overlay_derives_all_five_metrics`, `test_nim_cost_income_bucket_reads_nim_up_with_cost_down`, `test_asset_quality_bucket_reads_falling_gnpa_with_rising_coverage`, `test_crar_buffer_is_measured_against_the_disclosed_minimum`, `test_roa_roe_peer_quartile_ranks_the_issuer_against_fresh_peers`, `test_pb_roe_adjusted_premium_scales_the_peer_multiple_to_the_issuer_roe` | DONE |
| 14 (EPC/real estate) | EPC / real-estate overlay: CFO-or-order-book, net debt / ICR | `config.sector_overlays.epc_real_estate`; `derived.net_debt_bucket` (reuses `cfo_pat_cumulative`) | plan: `test_p19_s8_epc_overlay_with_negative_cfo_but_strong_order_book`, `test_p20_real_estate_overlay`; metrics: `test_epc_net_debt_bucket_reads_the_balance_sheet_ratio`, `test_epc_reuses_the_standard_cumulative_cfo_ratio` | DONE (one combined overlay; see s5.2) |
| 14 (loss-making) | Loss-making overlay: contribution, cash runway, P/S–EV/Sales, loss narrowing | `config.sector_overlays.loss_making`, auto-selected by `profile_resolution.auto_rules`; `derived.contribution_bucket`, `cash_runway_months`, `ps_premium_pct`, `loss_narrowing_bucket` | plan: `test_p21_loss_making_overlay_is_auto_selected`, `test_p21_loss_making_profile_uses_loss_criteria`; metrics: `test_contribution_bucket_reads_two_years_of_expansion`, `test_cash_runway_is_cash_plus_the_fresh_issue_over_the_monthly_burn`, `test_runway_is_not_applicable_when_the_issuer_is_not_burning_cash`, `test_loss_making_ps_premium_uses_the_peer_median`, `test_loss_narrowing_bucket_reads_two_consecutive_years` | DONE |
| 14 (cyclical) | Cyclical overlay: 5-FY average margin trend; 5 FY required | `config.sector_overlays.cyclical`, `derived.margin_trend_5y_avg`, `semantic_validation` `PERIODS_CYCLICAL_INSUFFICIENT` | `test_p22_s10_cyclical_overlay_requires_five_fiscal_years`, `test_p22_s10_cyclical_overlay_with_five_years` | DONE |
| 15 | Structure overlay (retail-heavy, pure-OFS) | `config.structure_overlays.retail_heavy` (`qib_quota_pct <= 10` → replace anchor/QIB with overall/NII subscription); `derived.pure_ofs` | `test_p23_retail_heavy_structure_overlay`, `test_p23_normal_structure_keeps_anchor_criteria`, `test_p2_s2_pure_ofs_offer` | DONE |
| 16 | Knockouts K1–K6 tri-state; UNVERIFIED lists the missing evidence and is never CLEAR | `knockouts.evaluate_knockouts`, `KnockoutResult.missing`, `config.knockouts` | `test_golden_knockouts_are_a_mix_of_clear_and_unverified`, `test_unverified_knockout_lists_the_missing_evidence`, `test_nothing_is_clear_when_nothing_is_known`, `test_p9_k4_combined_promoter_sale_with_full_exit` | DONE |
| 17 | Penalties, capped at −15 total; an unverifiable penalty widens the range instead of being applied or ignored | `scoring.evaluate_criterion` penalty path, `penalty_items`, `unresolved_penalty_points` | `test_unknown_penalties_widen_the_lower_bound`, `test_penalty_ceiling_is_respected` | DONE |

## 5. Confidence, range, verdict, lifecycle (Spec s18–s19)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| 18 | Confidence = evaluable points / total points × 100 (High ≥ 95, Medium ≥ 80, Low < 80); separate critical / knockout / valuation / market completeness | `scoring.score`, `completeness_breakdown` (weighting `POINTS`) | `test_confidence_is_points_weighted_not_count_weighted`, `test_points_weighting_differs_from_count_weighting`, `test_completeness_breakdown_separates_critical_and_knockout_data` | DONE |
| 18 | Range = base ± unknown points ± unresolved penalties; band crossing ⇒ `VERDICT_UNCERTAIN`; missing critical safety info ⇒ `INSUFFICIENT_DATA` | `scoring.score` bound computation; `critical_data` block in config | `test_range_brackets_the_base_score`, `test_unknown_penalties_widen_the_lower_bound`, `test_high_overall_completeness_cannot_hide_a_missing_knockout_input` | DONE |
| 18 | A triggered knockout dominates the band | `scoring.score` applies `verdict = AVOID` when `knockouts.any_triggered` | `test_triggered_knockout_is_critical`, `test_p4_going_concern_uncertainty_triggers_k1` | DONE |
| 19 | Preliminary vs Final: separate, frozen, never overwritten; a delta record is stored | `pipeline.evaluate(mode=...)`, `evaluation.compute_preliminary_delta`, auto-wired from the latest stored Preliminary | `test_p24_preliminary_evaluation`, `test_p25_final_evaluation`, `test_p26_s16_preliminary_to_final_delta`, `test_p26_delta_refuses_to_overwrite_the_preliminary` | DONE |
| 19 | Same inputs ⇒ reproducible result hash | `replay` re-evaluates from the frozen artifacts at the *original* instant | `test_p27_s17_historical_rerun_reproduces_the_result`, `test_p27_historical_rerun_from_the_stored_golden_files`, `test_run_replays_to_the_same_hash` | DONE |

## 6. Validation, persistence, Excel, audit (Spec s20–s26)

| ID | Requirement | Implementation | Test | Status |
| --- | --- | --- | --- | --- |
| 20 (schema) | JSON Schema gate is a hard gate | `schema_validation.enforce_schema` → `SchemaValidationError` | `test_schema_gate_stops_scoring`, `test_p16_invalid_schema_blocks_scoring`, 8 further schema cases | DONE |
| 20 (financial) | Period reconciliation: PBT−tax=PAT, EBITDA, share count/EPS, seller over-sell, % ranges | `semantic_validation.validate_semantics` | `test_seller_cannot_offer_more_than_it_held`, `test_percentage_out_of_range_is_rejected` | DONE |
| 20 (cross-source) | Cross-source divergence is reported, never silently reconciled | `semantic_validation._cross_source_checks` with `source_cross_check_tolerance_pct` | `test_cross_source_divergence_is_reported_not_resolved`, `test_cross_source_within_tolerance_is_quiet` | DONE |
| 20 (proceeds) | GCP ≤ 25% of fresh issue; combined ≤ 35%; unidentified ≤ 25% | `semantic_validation._validate_gcp_semantics` and the proceeds-limits block | `test_gcp_above_the_legal_ceiling_is_rejected`, `test_gcp_ceiling_check_is_unit_aware` | DONE |
| 20 (OFS) | 6(2) selling-shareholder cap breach | `semantic_validation._validate_ofs_route` | `test_ofs_6_2_selling_limit_breach_is_rejected`, `test_ofs_6_2_limit_is_not_applied_on_the_6_1_route`, `test_s13_ofs_6_2_breach_is_rejected` | DONE |
| 20 (peers) | Peer staleness / usability warnings | `semantic_validation` peer block | `test_peers_are_classified_stale_with_the_reason` | DONE |
| 20 (config) | Configuration gate | `config_validation.check_config` (15 assertion groups) | 20 config-gate cases in `tests/test_validation_gates.py` | DONE |
| 21 | Historical persistence: immutable, append-only, complete record | `evaluation.EvaluationStore.write` (exclusive create + `ImmutabilityError`), `LIFECYCLE`, `ARTIFACT_FILES` | `test_store_refuses_to_overwrite_an_evaluation`, `test_records_are_write_once_on_disk`, `test_every_artifact_required_by_spec_21_is_written` | DONE |
| 21 | Lifecycle PRELIMINARY → FINAL → POST_LISTING_1W/1M/6M | `config.modes` declares all five; `evaluation.LIFECYCLE` | `test_p29_post_listing_update_is_recorded`, `test_p29_all_lifecycle_stages_are_declared_in_the_config`, `test_p29_unknown_mode_is_refused` | DONE |
| 22 | Excel workbook, 14 sheets, append-only, historically preserved | `excel.SHEET_ORDER` / `SHEET_BUILDERS` / `project` | `test_sheet_order_is_the_specified_order`, `test_workbook_has_exactly_the_fourteen_required_sheets`, `test_p28_excel_is_append_only_across_the_lifecycle` | DONE |
| 22 | Excel must contain score, verdict, range, confidence, module scores, knockout states, penalties, missing inputs, evidence, timestamps, versions, post-listing | `excel._rows_*` for all 14 sheets | `test_workbook_carries_the_golden_numbers`, `test_module_scores_sheet_totals_100`, `test_criteria_detail_sheet_lists_every_criterion`, `test_knockouts_sheet_shows_the_tri_state`, `test_missing_unverified_sheet_lists_the_open_gaps`, `test_market_and_peer_sheets_are_populated_from_the_frozen_snapshots` | DONE |
| 22 | Excel is deterministic and rebuildable | `excel.workbook_bytes` (pinned 1980 timestamps, sorted rows) | `test_workbook_bytes_are_deterministic` | DONE |
| 23 | Immutable record layout `evaluation/{evaluation,input,evidence,market,peers,result,manifest}.json` | `EvaluationRecord.artifacts()`, `ARTIFACT_FILES` | `test_every_artifact_required_by_spec_21_is_written` | DONE |
| 24 | Auditability: hashes re-derived and verified | `EvaluationStore.verify_hashes` (manifest hash per artifact + recomputed result hash) | `test_recorded_hashes_verify_against_the_stored_artifacts`, `test_tampering_with_a_stored_artifact_is_detected`, `test_tampering_with_the_governing_record_is_detected` | DONE |
| 25 | Security / extraction: no API keys, extraction is out of the scoring path | No network calls anywhere in `engine/ipo_screening`; no extraction code ships, extraction is upstream of the canonical input | `test_workbook_bytes_are_deterministic` (offline run), `test_result_hash_is_stable_across_processes` | DONE |
| 26 | Golden regression suite, 17 named minimum cases | `tests/test_acceptance_matrix.py` (S-named tests) + `tests/test_vishal_golden.py` | 238 tests in the suite; every S1–S17 case present | DONE |
| 27 | Acceptance criteria list (14 items) | see section 7 below | 238 tests | DONE |

## 7. Acceptance criteria (Spec s27) — evidence per item

| # | Criterion | Evidence |
| --- | --- | --- |
| 1 | Schema validation is enforced | `test_schema_gate_stops_scoring`, `test_p16_invalid_schema_blocks_scoring` |
| 2 | Unknown values cannot become favourable values | `test_unknown_metric_does_not_become_zero`, `test_absent_boolean_flag_is_unknown_not_false`, `test_interest_cover_is_never_a_favourable_sentinel`, `test_p14_partially_disclosed_category_is_unknown_not_understated` |
| 3 | All sector overlays implemented or explicitly rejected at config-validation time | `test_overlay_metric_not_implemented_is_rejected`, `test_overlay_that_does_not_reconcile_is_rejected`, `test_every_profile_and_structure_combination_reconciles` |
| 4 | Knockout state is tri-state | `test_golden_knockouts_are_a_mix_of_clear_and_unverified`, `test_nothing_is_clear_when_nothing_is_known` |
| 5 | Stale valuation data cannot silently score as current | `test_p13_s6_stale_peers_cannot_score_as_current`, `test_p13_fresh_peers_are_used` |
| 6 | GCP `[●]` is not converted into an assumed actual amount | `test_p14_s4_missing_gcp_is_unknown_not_the_ceiling`, `test_gcp_ceiling_recorded_as_an_amount_is_rejected` |
| 7 | Weighted completeness and score ranges work | `test_confidence_is_points_weighted_not_count_weighted`, `test_points_weighting_differs_from_count_weighting`, `test_range_brackets_the_base_score` |
| 8 | Config invalidity blocks scoring | `test_p17_s14_invalid_config_blocks_scoring`, `test_invalid_config_blocks_scoring` |
| 9 | Every score has evidence/provenance | `test_golden_evidence_is_grounded_in_the_rhp`, `test_criteria_reference_their_metric_and_evidence`, `test_missing_evidence_is_reported_as_a_warning` |
| 10 | Preliminary and Final are immutable historical records | `test_store_keeps_every_evaluation_for_the_same_issuer`, `test_p26_delta_refuses_to_overwrite_the_preliminary` |
| 11 | Excel output is append-only and historically preserved | `test_p28_excel_is_append_only_across_the_lifecycle`, `test_two_evaluations_appear_as_two_rows` |
| 12 | Exact prior results are reproducible | `test_p27_s17_historical_rerun_reproduces_the_result`, `test_result_hash_is_stable_across_processes`, `test_run_replays_to_the_same_hash` (CLI replay) |
| 13 | Golden regression suite passes | 238 passed |
| 14 | Vishal Nirmiti test demonstrates expected unknown/stale behaviour | `test_p1_s1_vishal_nirmiti_mainboard_retail_heavy` and the other 18 tests in `tests/test_vishal_golden.py` |

## 8. Execution Prompt s19 — required test matrix (30 items)

| # | Item | Test | Status |
| --- | --- | --- | --- |
| 1 | Normal profitable IPO | `test_p1_s1_vishal_nirmiti_mainboard_retail_heavy` | DONE |
| 2 | Pure OFS | `test_p2_s2_pure_ofs_offer`, `test_p2_pure_ofs_cap_is_enforced_on_the_6_2_route` | DONE |
| 3 | Qualified audit | `test_p3_s3_qualified_audit_opinion_triggers_k1` | DONE |
| 4 | Going-concern uncertainty | `test_p4_going_concern_uncertainty_triggers_k1` | DONE |
| 5 | Negative net worth | `test_p5_negative_net_worth_triggers_k1` | DONE |
| 6 | Promoter pledge > 25% | `test_p6_promoter_pledge_above_25pct_triggers_k2`, `test_p6_promoter_pledge_at_25pct_does_not_trigger` | DONE |
| 7 | Active SEBI/ED action | `test_p7_s12_active_sebi_action_triggers_k2`, `test_p7_inactive_sebi_action_clears_k2` | DONE |
| 8 | OFS > 80% + declining profits | `test_p8_ofs_above_80pct_with_declining_profit_triggers_k3`, `test_p8_ofs_above_80pct_alone_is_not_enough` | DONE |
| 9 | K4 combined-sale condition | `test_p9_k4_combined_promoter_sale_with_full_exit`, `test_p9_k4_requires_the_combined_sale_leg` | DONE |
| 10 | Contingent liabilities | `test_p10_s7_contingent_liabilities_above_50pct_of_net_worth`, `test_p10_s7_contingent_liabilities_below_the_threshold_clear` | DONE |
| 11 | Unquantified contingent liabilities | `test_p11_s12_unquantified_contingent_liabilities_trigger_k5`, `test_p11_unquantified_when_absent_leaves_k5_unverified`, `test_p11_unknown_unquantified_flag_leaves_k5_unverified` | DONE |
| 12 | RPT growth | `test_p12_rpt_growth_above_40pct_triggers_k6`, `test_p12_rpt_growth_below_the_threshold_clears_k6`, `test_p12_unknown_rpt_growth_is_unverified_not_clear` | DONE |
| 13 | Stale peers | `test_p13_s6_stale_peers_cannot_score_as_current`, `test_p13_fresh_peers_are_used` | DONE |
| 14 | Missing GCP | `test_p14_s4_missing_gcp_is_unknown_not_the_ceiling`, `test_p14_gcp_disclosed_actually_scores`, `test_p14_proceeds_bucket_classifies_each_disclosure_pattern`, `test_p14_partially_disclosed_category_is_unknown_not_understated` | DONE |
| 15 | Missing promoter holding | `test_p15_s5_missing_promoter_holding_is_unknown` | DONE |
| 16 | Invalid schema | `test_p16_invalid_schema_blocks_scoring` | DONE |
| 17 | Invalid config | `test_p17_s14_invalid_config_blocks_scoring` | DONE |
| 18 | Financial institution overlay | `test_p18_financial_institution_overlay` | DONE |
| 19 | EPC overlay | `test_p19_s8_epc_overlay_with_negative_cfo_but_strong_order_book` | DONE |
| 20 | Real-estate overlay | `test_p20_real_estate_overlay` | DONE |
| 21 | Loss-making overlay | `test_p21_loss_making_overlay_is_auto_selected`, `test_p21_loss_making_profile_uses_loss_criteria` | DONE |
| 22 | Cyclical overlay | `test_p22_s10_cyclical_overlay_requires_five_fiscal_years`, `test_p22_s10_cyclical_overlay_with_five_years` | DONE |
| 23 | Retail-heavy structure overlay | `test_p23_retail_heavy_structure_overlay`, `test_p23_normal_structure_keeps_anchor_criteria` | DONE |
| 24 | Preliminary evaluation | `test_p24_preliminary_evaluation` | DONE |
| 25 | Final evaluation | `test_p25_final_evaluation` | DONE |
| 26 | Preliminary-to-Final delta | `test_p26_s16_preliminary_to_final_delta`, `test_p26_delta_refuses_to_overwrite_the_preliminary` | DONE |
| 27 | Historical rerun | `test_p27_s17_historical_rerun_reproduces_the_result`, `test_p27_historical_rerun_from_the_stored_golden_files`, `test_p27_rerun_after_an_input_correction_creates_a_new_record` | DONE |
| 28 | Excel append-only behaviour | `test_p28_excel_is_append_only_across_the_lifecycle`, `test_p28_workbook_has_the_fourteen_sheets` | DONE |
| 29 | Post-listing updates | `test_p29_post_listing_update_is_recorded`, `test_p29_all_lifecycle_stages_are_declared_in_the_config`, `test_p29_unknown_mode_is_refused` | DONE |
| 30 | Reproducibility hash | `test_p30_reproducibility_hash_is_a_pure_function_of_the_inputs`, `test_p30_hash_covers_every_material_input` | DONE |

### Specification s26 minimum list

| # | Item | Test | Status |
| --- | --- | --- | --- |
| S1 | Vishal Nirmiti — normal/mainboard/retail-heavy | `test_p1_s1_vishal_nirmiti_mainboard_retail_heavy` | DONE |
| S2 | Pure OFS IPO | `test_p2_s2_pure_ofs_offer` | DONE |
| S3 | Qualified audit opinion | `test_p3_s3_qualified_audit_opinion_triggers_k1` | DONE |
| S4 | Missing GCP | `test_p14_s4_missing_gcp_is_unknown_not_the_ceiling` | DONE |
| S5 | Missing promoter holding | `test_p15_s5_missing_promoter_holding_is_unknown` | DONE |
| S6 | Stale peers | `test_p13_s6_stale_peers_cannot_score_as_current` | DONE |
| S7 | Financial institution | `test_p18_financial_institution_overlay` | DONE |
| S8 | EPC with negative CFO but strong order book | `test_p19_s8_epc_overlay_with_negative_cfo_but_strong_order_book` | DONE |
| S9 | Loss-making / new-age | `test_p21_loss_making_overlay_is_auto_selected`, `test_p21_loss_making_profile_uses_loss_criteria` | DONE |
| S10 | Cyclical company | `test_p22_s10_cyclical_overlay_requires_five_fiscal_years`, `test_p22_s10_cyclical_overlay_with_five_years` | DONE |
| S11 | Unquantified contingent liabilities | `test_p11_s12_unquantified_contingent_liabilities_trigger_k5`, `test_p11_unknown_unquantified_flag_leaves_k5_unverified` | DONE |
| S12 | Active SEBI/ED action | `test_p7_s12_active_sebi_action_triggers_k2` | DONE |
| S13 | 6(2) OFS breach | `test_s13_ofs_6_2_breach_is_rejected` | DONE |
| S14 | Invalid schema/type | `test_p16_invalid_schema_blocks_scoring`, `test_p17_s14_invalid_config_blocks_scoring` | DONE |
| S15 | Invalid config | `test_p17_s14_invalid_config_blocks_scoring` | DONE |
| S16 | Preliminary → Final delta | `test_p26_s16_preliminary_to_final_delta` | DONE |
| S17 | Historical rerun reproducibility | `test_p27_s17_historical_rerun_reproduces_the_result` | DONE |

---

## 9. Deliberate divergences from the Claude reference prototype

The six reference artifacts are prototype material only. v1.5 governs. Three
behaviours were deliberately **not** reproduced; each is asserted in the test
suite so that a future change cannot quietly reinstate the old behaviour.

### D1. Stale peer multiples do not score zero

* **Reference behaviour:** with no fresh peer multiple, the prototype scored the
  P/E-vs-peers and second-multiple criteria **0**, which reads as "expensive"
  and *lowers* the score.
* **v1.5 behaviour:** the peers are classified `STALE`, the valuation criteria
  become `UNKNOWN`, and their points move from the base score into the *upper*
  bound of the range. Valuation completeness is reported separately.
* **Why:** Spec s3.2 ("unknown is not zero") and s4.5. A punitive zero converts
  an absence of information into a negative judgement, which is precisely the
  failure mode v1.5 exists to remove.
* **Test:** `test_p13_s6_stale_peers_cannot_score_as_current`,
  `test_stale_peers_are_not_scored_as_zero` (golden suite).
* **Effect on the golden case:** 16 of 20 valuation points are unavailable;
  `completeness_breakdown["valuation_pct"] == 20.0`.

### D2. An undisclosed GCP is not replaced by the 25% legal ceiling

* **Reference behaviour:** the reference fixture `VISHAL-NIRMITI-LIMITED.json`
  records `use_of_proceeds[2].amount == 3625` — exactly 25% of the ₹14,500 lakh
  fresh offer, i.e. the ICDR ceiling written in as if it were the amount. The
  prototype then graded the proceeds as `blind_heavy` and scored **0**.
* **v1.5 behaviour:** the amount is `UNKNOWN`, `gcp_legal_max` is recorded
  separately (`36.25` crore) and labelled a limit, the proceeds criterion is
  `UNKNOWN`, and the input validator *rejects* a recorded amount that equals the
  ceiling (`GCP_CEILING_RECORDED_AS_AMOUNT`).
* **Why:** Spec s10/s13. Substituting the ceiling manufactures a favourable
  reason to distrust the issue out of a missing disclosure.
* **Test:** `test_p14_s4_missing_gcp_is_unknown_not_the_ceiling`,
  `test_gcp_ceiling_recorded_as_an_amount_is_rejected`,
  `test_gcp_ceiling_check_is_unit_aware`.
* **Open item for Ramki:** the reference fixture itself violates the v1.5 rule
  (see section 10, blocker B2).

### D3. The knockouts are tri-state, not the prototype's 29/58 pair

* **Reference behaviour:** the v1.3 §14 worked example resolved K1, K5 and K6
  to `CLEAR` on inputs that never established going-concern status, whether any
  contingent liability was unquantified, or the RPT growth rate, and published a
  29-floor / 58-ceiling range with a `CLEAR` knockout line.
* **v1.5 behaviour:** K1, K5 and K6 are `UNVERIFIED` and each lists the missing
  fact (`going_concern_uncertainty`, `contingent_liab_unquantified`,
  `rpt_pct_of_revenue_growth`). `verdict = INSUFFICIENT_DATA` because a declared
  critical input is unknown. The 29/58 pair is not reproduced.
* **Why:** Spec s3.3 and s16. "We could not check" must never render as "we
  checked and it was fine".
* **Test:** `test_golden_knockouts_are_a_mix_of_clear_and_unverified`,
  `test_knockouts_are_tri_state_not_boolean`,
  `test_nothing_is_clear_when_nothing_is_known`.

### Additional, non-behavioural divergences

| # | Reference | v1.5 engine | Reason |
| --- | --- | --- | --- |
| N1 | `"1500000"` as a string for `pre_issue_shares` | Schema requires a number | Spec s20 schema gate; asserted in `test_reference_fixture_gcp_would_be_rejected_as_a_ceiling` and `test_p16_invalid_schema_blocks_scoring` |
| N2 | Reference config version `1.4.0` | `config/ipo-config.v1.5.0.json`, validated by 15 assertion groups | Spec s3.5 |
| N3 | Confidence computed by counting criteria | Points-weighted completeness | Spec s11/s18; `test_confidence_is_points_weighted_not_count_weighted` |
| N4 | Latest/oldest over three FY observations labelled "3Y CAGR" | `revenue_cagr_2y_from_3fy`; a genuine 3Y value needs four FYs | Spec s7; `test_revenue_cagr_is_2y_from_3fy_not_a_3y_cagr` |
| N5 | ICR sentinel of 99 when interest expense was absent | `UNKNOWN` unless the balance sheet is debt-free | Spec s3.2; `test_interest_cover_is_never_a_favourable_sentinel` |

## 10. Ambiguities, decisions and blockers

### R1. GCP: specification rule vs reference fixture — RESOLVED, NEEDS SIGN-OFF

* **Conflict:** Spec s10/s13 requires an undisclosed `[●]` GCP to be `UNKNOWN`
  with the ceiling held separately. The reference fixture records the ceiling
  (3625 lakh = 25%) as the amount.
* **Decision taken:** the engine implements the **specification** rule. A
  recorded amount equal to the ceiling is a validation error, and the golden
  fixture records `amount: null` with `undisclosed_marker: "[●]"` and a
  `page_note` stating that 25% is a limit, not the amount.
* **Consequence:** the unmodified reference fixture is rejected by the schema
  gate on two counts (string share count, ceiling recorded as amount). This is
  intentional and asserted.
* **Action required:** confirmation from R. Kapoor / Ramki that the reference
  fixture is superseded, per Spec s21's ambiguity rule. Until then the engine
  follows the specification and the fixture is treated as prototype material.

### R2. EPC and real estate share one overlay

Spec s14 lists "EPC / real estate" as a single subsection, so v1.5 ships one
`epc_real_estate` overlay. Acceptance items P19 (EPC) and P20 (real estate) are
therefore both satisfied by that overlay, with P20 additionally asserting the
removals. If the intent was two separate profiles, the configuration needs a
second overlay; that is a policy question, not a code change, and is raised as a
residual item rather than guessed.

### R3. Absent proceeds category means nil, undisclosed means UNKNOWN

The object-of-the-offer schedule is exhaustive, so a category that does not
appear on it is treated as a disclosed nil (0%), while a category that appears
with a null amount is `UNKNOWN`. This distinction is what allows a
fully-disclosed offer to receive a determinate `use_of_proceeds_bucket` while
`[●]` still blocks it. Documented in `derived._use_of_proceeds_bucket` and
tested by `test_p14_proceeds_bucket_classifies_each_disclosure_pattern` and
`test_p14_partially_disclosed_category_is_unknown_not_understated`.

### R4. Snapshot hashing excludes wall-clock ages

The peer and market snapshot hashes cover the *material* content (classification
status, observation values, thresholds, source `as_of` dates) and exclude the
derived `age_days` / `age_hours`, which are recorded in their own fields for
audit. Without this, two evaluations a minute apart produced different result
hashes even though nothing material had changed, which would have made the hash
useless as a change detector for the Preliminary→Final delta. When data
genuinely crosses the staleness limit the classification changes, the snapshot
and result hashes change, and the score legitimately moves — asserted by
`test_result_hash_ignores_the_clock_while_the_snapshot_is_unchanged` and
`test_result_hash_changes_when_the_snapshot_materially_changes`.

### B1. Branch name

The session branch is `arena/01a10abc-ipo-screening-engine`, not the
prompt-mandated `arena/ipo-screening-engine-v1.5-implementation`. The session is
pinned to its own branch and cannot create another; this is an infrastructure
constraint, not a design decision. No merge to `main` was performed.

### B2. Remote operations unavailable

GitHub remote access for this session was revoked
("This coding session has ended because its pull request was merged or closed"),
so the implementation could not be pushed and no pull request was opened. All
work is committed locally on `arena/01a10abc-ipo-screening-engine`. Continuing
requires a new coding session.

---

## 11. Defects found and fixed during verification

Every one of these became a regression test. They are listed because "the tests
pass" is only meaningful alongside what they caught.

| # | Defect | Impact if shipped | Fix |
| --- | --- | --- | --- |
| 1 | `use_of_proceeds_bucket` dropped the **first** amount seen for each category (`elif totals.get(category) is not None`) | Every fully-disclosed offer fell through to `mixed_ok`; `debt_heavy`, `growth` and `blind_heavy` could never be detected, so the largest single scoring signal in Module C was inert | Rewritten to accumulate every amount and to track undisclosed categories explicitly; branch tests are now three-valued (`derived._use_of_proceeds_bucket`) |
| 2 | `use_of_proceeds_bucket` used `share(...) or 0.0`, masking UNKNOWN as zero on the unidentified-acquisition and growth legs | An undisclosed leg silently cleared `blind_heavy` — the exact "unknown becomes favourable" failure v1.5 forbids | Each test is now evaluated in three-valued logic; an unknown leg yields UNKNOWN for the bucket |
| 3 | GCP ceiling compared in **lakhs** against a fresh issue in **crore** | Reported 2500% instead of 25%; the ceiling check appeared to fire but reported a nonsense figure and would mis-fire at other unit combinations | Unit-normalised before comparison (`semantic_validation`, `derived`) |
| 4 | Peer/market snapshot hashes embedded the evaluation instant and the derived age | Two runs a minute apart produced different result hashes with identical material content; reproducibility and delta detection were both undermined | Snapshot `as_of` is now the newest **source** timestamp; the capture instant moved to `captured_at`; ages excluded from `hash_payload()` |
| 5 | Staleness reason text embedded the age in days/hours | The age flowed into derived-metric reasons and thus into the result hash, so the clock leaked into the hash even after fix 4 | Reasons cite the observation date and the limit; the precise age stays in `age_days` / `age_hours` |
| 6 | `EvaluationRecord.to_dict()` omitted `input_snapshot`, `evidence`, `market_snapshot`, `peer_snapshot`, `derived_metrics` | Any projection built from a record silently produced empty Evidence / Market_Snapshots / Peer_Snapshots sheets | The record is now self-sufficient; asserted by `test_market_and_peer_sheets_are_populated_from_the_frozen_snapshots` |
| 7 | `build_workbook` accepted a bare mapping and iterated its keys | A single record would render fourteen empty sheets with no error | A mapping is normalised to a one-element list |
| 8 | `verify_hashes` relied on `evaluation.json` for the result payload and never checked `result.json`'s hash | A tampered `result.json` was invisible to the audit command | Manifest artifact hashes are re-derived for every file; `test_tampering_with_a_stored_artifact_is_detected` |
| 9 | `replay` read `record["input_snapshot"]["snapshot"]`, which never existed on the summary, and defaulted to the wall clock | Historical rerun either crashed or legitimately re-classified the snapshot, failing its own reproducibility check | Replay reads the frozen artifacts and defaults to the stored `evaluation_timestamp` |
| 10 | `_evidence` accepted `quote` on input but the registry emits `quoted_text` | A frozen input snapshot failed schema validation on re-load, breaking replay | `quoted_text` accepted as an alias, in schema and loader |
| 11 | `check_expression` accepted any `{"flag": ...}` without checking the metric exists | A misspelled flag left the rule permanently UNVERIFIED with no error — an easy way to make a knockout silently vanish | `CONFIG_FLAG_UNIMPLEMENTED`; also added `not`-node support for parity with the evaluator |
| 12 | `EvaluationRecord.preliminary_delta` stored the raw preliminary record, and `compute_preliminary_delta` was never called | Spec s19's delta record did not exist | The delta is computed in `build_record` and auto-wired from the latest stored Preliminary |
| 13 | `margin_trend_5y_avg` returned UNKNOWN with an empty `formula` | Broke the "every metric states its formula" invariant | Formula attached to every early return |
| 14 | `derive(canonical, config, None, None)` raised `AttributeError` | A caller without snapshots got a crash instead of a record full of UNKNOWNs | Absent snapshots are normalised to empty ones |

## 12. Coverage summary

| Metric | Value |
| --- | --- |
| Modules | 17 (`engine/ipo_screening`) + 1 CLI (`engine/tools`) |
| Derived metrics implemented | 75 |
| Scoring criteria (standard profile) | 30 + 7 penalties |
| Sector overlays | 4 (financial, epc_real_estate, loss_making, cyclical) — every overlay metric derivable and exercised in `tests/test_sector_overlays.py` |
| Structure overlays | 1 (retail_heavy) |
| Resolved profile × structure plans validated | 10 |
| Excel sheets | 14 (per Spec s22) |
| Tests | 238 passing (7 functional modules + 1 overlay-metric module) |
| Prompt matrix items covered | 30 / 30 |
| Spec s26 items covered | 17 / 17 |
| Spec s27 acceptance criteria covered | 14 / 14 |
