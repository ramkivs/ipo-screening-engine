# A9 Publisher-Level GMP Source-Policy Selection

**Record ID:** `A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15`
**Date:** 2026-10-15
**Branch:** `arena/573e69a4-ipo-screening-engine`
**Baseline reviewed:** remote branch tip `707405e9e81c80d791cedea9139d2ecfaf3ad02d`
**Status:** Model A selected as the source-policy direction. No individual publisher is selected, approved, or A9-qualified.

## 1. Selected policy and authority limits

**Selected policy direction: MODEL A — PUBLISHER-LEVEL GMP OBSERVATION.** The declared source will be one specific, named publisher's own reported GMP observation. The engine must describe it as that publisher's reported value, not as a verified or dealer-native quote.

This is a policy selection, not provider approval, source qualification, or implementation authorization. It does not select Niva Market Watch, IPOStation, InvestorGain, IPO Watch, or another publisher. No current candidate is A9-qualified. Model B/dealer-level provenance is not required by this selected policy, but any provenance claim must remain within the evidence actually available.

Multiple publishers that share the same upstream source are not automatically independent corroboration.

This is a follow-on to the [A9 GMP Source-Model Decision Record](A9-GMP-SOURCE-MODEL-DECISION-2026-10-15.md). It supersedes only that record's earlier statement that Model A had not yet been selected; the investigation findings and conclusion that no candidate was qualified remain in force.

## 2. Evidence carried forward

**Observed in the completed review:** Niva Market Watch and IPOStation displayed issue-specific GMP values. InvestorGain displayed dated history but no identifiable dealer-level quote. Values and timestamps differed across pages; some pages showed only a date or page-update time rather than distinct observation, publication, and retrieval times. No original response bytes or headers were retained and no evidence hash was computed. A currently displayed history is not proof that the same observation was available historically.

**Publisher claims:** Niva names InvestorGain as its GMP source. IPOStation names InvestorGain as its primary feed and IPO Watch as its cross-check. Those source and cross-check claims do not independently establish how the values were obtained or that the publishers are independent.

**Unresolved:** Timezone and evaluation-cutoff compatibility, freshness/staleness, historical reproducibility, source-artifact retention, missing-versus-zero semantics, conflict/correction behavior, and the exact integrity-hash subject remain insufficiently established. See the linked decision record for the reviewed page references and detailed findings; no new provider investigation is implied here.

## 3. Minimum source-specific qualification contract

All eight requirements below remain **UNRESOLVED for any named publisher**. The listed evidence describes what would resolve each gap; it does not prescribe unsupported source capabilities or numerical rules.

| # | Requirement | Evidence needed to resolve it |
|---|---|---|
| **1** | **Publisher identity and traceable issue-specific observation.** | Select one named publisher and retain evidence tying that publisher's own page or record to the particular IPO observation being evaluated. The trace must identify the source and the issue-specific record without implying a dealer source that is not exposed. |
| **2** | **IPO/issue identity and exact semantics of the published GMP value.** | Evidence must identify the IPO/issue and define what the publisher's displayed GMP field means, including the value's units and any other source-defined interpretation needed to reproduce it. A visible number alone is insufficient. |
| **3** | **Observation, publication, and retrieval-time semantics wherever available; timezone and evaluation-cutoff compatibility.** | Source-specific evidence must distinguish the meaning of each available timestamp and its timezone. The selected evaluation cutoff must be explicitly defined and shown compatible with the source's time fields; no cutoff is set by this record. |
| **4** | **Evidence-backed freshness and stale-value behavior.** | Establish the source's update/freshness behavior and what happens when an observation is delayed or stale, using source-specific documentation or retained observations. Any allowed-age rule remains for explicit policy selection; no threshold is invented here. |
| **5** | **Retained source artifact and reproducible integrity hash with a defined hash subject.** | Preserve the source artifact used for an evaluation with enough retrieval context to reproduce the capture. The source-specific contract must identify the exact hash subject and reproducible hashing procedure; neither is specified here. |
| **6** | **Missing versus genuine-zero representation.** | Source-specific evidence must distinguish a missing or unavailable observation from an actual zero GMP, including the publisher's displayed and retained representation. No sentinel or missing-value behavior is assumed. |
| **7** | **Conflict, correction, revision, and precedence behavior.** | Establish how the selected publisher handles conflicting inputs, corrections, revisions, and any source fallback or precedence. Evidence must distinguish a revised value from an overwritten value; no conflict rule or precedence is invented here. |
| **8** | **Sufficient retained history to reproduce the observation used by an evaluation.** | Retain enough issue-specific historical evidence to reproduce the exact publisher observation used, including relevant version or correction information and its evaluation-time availability. A mutable current page alone is insufficient. |

A hash can establish the integrity of the captured bytes; it does not independently establish the bytes' source authenticity or the truth of an underlying quote.

## 4. A9 and Final-mode consequences

A9 remains fail-closed until one named publisher satisfies the source-specific qualification contract. The selected policy direction does not change the gate or Final-mode behavior:

- Missing GMP remains nonterminal with reason `MISSING`.
- Present but unqualified GMP remains nonterminal with reason `SOURCE_UNQUALIFIED`.
- Neither withheld case sets `final_outcome`.
- A publisher's displayed value alone does not enable Final.

No scoring formulas, schemas, serialization, existing result hashes, or other verified behavior are changed or authorized to change by this record. No connector or source ingestion is authorized.

## 5. Next action

Assess **one named publisher** against the eight requirements above using concrete source evidence. Do not restart broad candidate discovery. Until that assessment establishes a qualifying source, preserve the existing A9 fail-closed behavior.
