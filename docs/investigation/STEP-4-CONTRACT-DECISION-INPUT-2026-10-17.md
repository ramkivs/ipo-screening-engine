# Step 4 — Contract Decision Input: Financial Periods, Audit/Restatement Status, Manual Issue-Term Entry, GMP Qualification

- **Date:** 2026-10-17 · **Repository:** `ramkivs/ipo-screening-engine` · **Baseline:** session branch `arena/5dd3fe52-ipo-screening-engine` at `485167c8b73892b2f890d56bbff898d1599ed91a` (market-data presentation), incorporating D-PEER-1 (`73ec730`), Workstream 2 evidence presentation (`636dde4`) · PR #6 OPEN, unmerged · **Nature:** decision-input record only. It approves nothing, changes no behaviour, and introduces no schema properties, enums, or scoring changes.
- **Controlling authorities:** v1.5 input contract (`schema/ipo-input.v1.5.schema.json`), A15 (semantic distinctions; property approval reserved), A16 (personal-use scope), A1 (field-conflict authority: Ramki), A8-M/A9/A10, D-PEER-1 (approved 2026-10-16), fail-closed fixture-fallback policy.

Classification key: **SUPPORTED** (permitted by existing contracts) · **CONDITIONALLY SUPPORTED** (only within stated limits) · **DECISION REQUIRED** (explicit user decision first) · **UNSUPPORTED** (insufficient evidence/authority).

---

## Decision Area A — Financial period semantics

| Field | Finding |
|---|---|
| Current behaviour | `financials.periods` is an array of 3–6 items (`minItems: 3, maxItems: 6`). Each period requires only `fy` (a label such as `FY2025`, or `9M-FY2026` for a stub) and permits `is_stub` plus monetary fields. There are **no period start/end date properties** anywhere in the contract. Canonical `FinancialPeriod` (`canonical_input.py:44ff`) carries `fy`, `is_stub`, values; `full_periods` excludes stubs; derived metrics require stated full-period counts and resolve UNKNOWN otherwise. |
| Existing authority | v1.5 schema `$defs/period` and its description ("three full FYs plus an optional stub; the cyclical profile needs five FYs"); spec §4.2 stub semantics. |
| Evidence | `schema/ipo-input.v1.5.schema.json` (`financials.periods`, `$defs/period`); `canonical_input.py:116-127, 322-332`; `derived.py` period guards; extraction builds labels as `FY{year}` (`extraction/financial_tables.py:243ff`). |
| Gap | (1) Period *dates* do not exist and cannot be presented or validated. (2) Extraction never sets `is_stub` (no extraction code writes it); stub flags exist only in authored inputs, so a stub extracted from a filing is indistinguishable from a full year except by its label text. (3) Non-standard period lengths are carried only in the free-text `fy` label. |
| Existing-authority action | **SUPPORTED:** present periods exactly as recorded (label + stub flag) — already done by Workstream 2's summary. **CONDITIONALLY SUPPORTED:** treat a label like `9M-FY2026` as a stub *hint* in presentation wording only, without changing canonical semantics. |
| Decision required | **DECISION REQUIRED:** whether the contract should gain exact period start/end dates and mandatory stub identification. That is a schema-property addition reserved by A15 for explicit approval. **UNSUPPORTED:** inferring dates from fiscal-year labels (Indian FY convention would be an assumption, not evidence). |
| Consequence until resolved | Period-level presentation remains label-based; period-date validation, stub-aware extraction, and cross-issuer period-alignment checks remain unavailable. Scoring is not blocked: full-period counting and UNKNOWN propagation already behave correctly. |

## Decision Area B — Audit and restatement status

| Field | Finding |
|---|---|
| Current behaviour | `governance` carries optional `auditor_name`, `auditor_opinion`, `auditor_changed_3y`, `auditor_change_count_3y`, `auditor_reputed`, `auditor_or_cfo_exit_2y` (schema, no required set). **Restatement status has no explicit field**: it is implicit in the extraction routing ("Restated Financial Statements" sections) and in locator text. Extraction heuristics scan for opinion language (`extraction/sections.py:705ff`). |
| Existing authority | v1.5 schema `governance.*`; knockout rule k1 consumes `auditor_opinion` (qualified/adverse/disclaimer, going concern, negative net worth). |
| Evidence | `schema/ipo-input.v1.5.schema.json` (`governance` properties); `extraction/sections.py:712` — **`auditor_opinion` is initialised to `"unqualified"` and only changed if adverse/emphasis language is found** in the scanned pages. |
| Gap | **Unknown vs verified-negative conflation (confirmed):** when the scan finds nothing, extraction reports `auditor_opinion: "unqualified"` — a clean-opinion claim — without positive evidence. Absence of adverse language in a heuristic page window is not proof of an unqualified opinion. Restatement status similarly cannot be asserted or denied from current data. |
| Existing-authority action | **SUPPORTED:** presentation may state that audit/restatement status is *as recorded* and surface the underlying evidence (section/locator) without upgrading it. **CONDITIONALLY SUPPORTED:** an extraction-behaviour correction that emits `null` (unknown) instead of the `"unqualified"` default when no opinion language is found — contract-permitted (field is nullable/optional), but it changes extraction outputs for filings currently receiving the default and can move knockout/criteria states, so it is scoring-visible. |
| Decision required | **DECISION REQUIRED:** (i) approve replacing the `"unqualified"` default with explicit unknown (recommended; restores unknown-vs-negative distinction per A15 §2); (ii) whether explicit restatement/audit-status fields are wanted at contract level (schema addition — separate approval). Do not implement either under this record. |
| Consequence until resolved | For filings where opinion language is not located by the heuristic scan, the application may present an unqualified audit opinion that the evidence does not establish. Financial values are unaffected numerically, but their qualification context can be overstated (knockout k1 input). |

## Decision Area C — Manual IPO issue-term entry

| Field | Finding |
|---|---|
| Current behaviour | Terms resolve as: filing extraction → verified official-notice retrieval (`issue_terms.py`; only allow-listed NSE/BSE/SEBI retrievals verify) → otherwise fail-closed `AWAITING_ISSUE_TERMS`, nothing persisted. The presentation API accepts only `file` + `mode` and rejects value-carrying parameters (`presentation/api.py:299ff`, `SECURITY_VIOLATION_UNAUTHORIZED_PARAMETER`). A manual channel substrate exists outside the UI: the supplemental enrichment contract (`enrichment_contract.py`, analyst `MANUAL_ENTRY` method) consumed by the CLI (`tools/ipo_screen.py --supplemental`), with precedence PBN > supplemental > RHP in `EnrichmentEngine._resolve_pricing_field`. |
| Existing authority | A15 (manual-entry is a *method* label in the evidence contract, not an authorization); v1.5 §5 raw/normalized value provenance; A1 (conflicts are Ramki-adjudicated, observations preserved). **No decision authorizes user-entered price-band/lot values in the application workflow.** |
| Evidence | `presentation/api.py:299-306`; `presentation/service.py` awaiting gate; `enrichment_contract.py:58, 90`; `enrichment_engine.py` pricing precedence; `issue_terms.py` verified/retained classes. |
| Gap | No authorized, provenance-distinguishable path for a user to supply floor/cap/lot when official retrieval is unavailable; no defined conflict workflow between entered, extracted, and official values in the UI. |
| Existing-authority action | **SUPPORTED:** keep fail-closed awaiting; CLI supplemental enrichment remains available to the operator as an analyst channel with `MANUAL_ENTRY` provenance (existing behaviour, unchanged). |
| Decision required | **DECISION REQUIRED (minimum decision):** authorize (or decline) application-level manual entry with these parameters: (1) entered values are recorded with `MANUAL_ENTRY` provenance and `UNVERIFIED`-class presentation, visibly distinct from `OFFICIAL_VERIFIED`; (2) entry requires an accompanying explanation/document reference; (3) any conflict with filing-extracted or official-notice values blocks evaluation pending explicit user confirmation, preserving all observations (A1); (4) entered terms never upgrade evidence verification status; (5) scope limited to `price_band_low`, `price_band_high`, `lot_size` (OFS remains derived only). |
| Consequence until resolved | Filings whose terms exist only outside the configured official sources remain in `AWAITING_ISSUE_TERMS` in the application, even if the operator personally knows the terms. That is the intended fail-closed posture, not a defect. |

## Decision Area D — GMP qualification

| Field | Finding |
|---|---|
| Current behaviour | GMP enters evaluations only as canonical input data (`market.gmp.pct/trend`, timestamped blocks; freshness FRESH/STALE/MISSING in the frozen snapshot layer). Connector adapters exist (`connectors/adapters.py`: `GmpSignalAdapter`, coordinator) with A17 cutoff handling (`gmp_policy.py:54`), and A9 investigation records evaluate candidate publishers. **No GMP source is qualified**; present-but-unqualified GMP remains nonterminal with `SOURCE_UNQUALIFIED` in the A9 gate model, and the canonical-input path scores recorded fixture-era data exactly as the v1.5 baseline defines. |
| Existing authority | A9 (fail-closed; absent/invalid required qualifying GMP snapshot withholds Final *in its approved scope*); A9 source-policy selection (Model A direction; **no publisher selected or qualified**); A17 (cutoff/freshness); A15 (digests do not qualify sources). |
| Evidence | `docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md` ("No current candidate is A9-qualified", "A9 gate… has no qualified path"); `A9-GMP-ALTERNATIVE-PUBLISHER-QUALIFICATION-2026-10-15.md`; `connectors/adapters.py:220`; `snapshots.py` market blocks; tracker GMP qualification boundaries (MarketLiveIPOGMP / InvestorGain NOT QUALIFIED). |
| Gap | Qualification requires, per source: established source identity, observation value + timing evidence, and historical availability — none is satisfied by any current candidate. Availability of a value, an HTTP 200, or a populated field does not satisfy any of these. |
| Existing-authority action | **SUPPORTED:** presentation/diagnostics that show GMP state exactly as recorded (done: market-state panel, freshness ≠ qualification). **CONDITIONALLY SUPPORTED:** further *investigation* of a named candidate against the A9 evidence requirements, producing evidence records only. |
| Decision required | **DECISION REQUIRED:** qualify a named GMP source (requires the per-source evidence above plus your explicit qualification decision), and separately decide the qualifying snapshot/hash subject. **UNSUPPORTED:** promoting any observed GMP value, treating connector capture hashes as qualification, or relaxing historical-availability requirements. |
| Consequence until resolved | GMP remains fail-closed/unqualified for qualification-dependent purposes; recorded GMP in canonical inputs continues to behave exactly as the v1.5 baseline specifies, and the UI must not describe it as qualified. |

---

## Consolidated dispositions

| Area | Disposition |
|---|---|
| A. Financial periods | Semantics are label + optional stub; adequate for current scoring. Exact dates/stub-detection: **DECISION REQUIRED** (schema). No action needed now. |
| B. Audit/restatement | One confirmed conflation (`auditor_opinion` default). Fix is contract-permitted but scoring-visible: **DECISION REQUIRED** (approve unknown-instead-of-default). Explicit status fields: separate schema decision. |
| C. Manual issue-term entry | **Not authorized** for the application. Minimum decision specified above (5 parameters). CLI analyst channel already exists and is unchanged. |
| D. GMP qualification | **Fail-closed, unqualified — no path currently satisfiable.** Qualification of a named source with per-source evidence: **DECISION REQUIRED**. Presentation already honest. |

**Actions that can proceed under existing authority (no new decision):** none of the four areas requires implementation to remain correct today; the supported items (label-faithful period presentation, as-recorded audit presentation, market/GMP state presentation, CLI supplemental channel) are already the implemented behaviour at the baseline commit. The next item in the existing execution order is the user's disposition of Areas B(i) and C above (the two decision-ready, bounded items), with A and D held until their evidence or qualification prerequisites exist.
