# A25 — Evidence and Source Coverage Required to Declare SEBI/ED Action Absent

- **Decision ID:** A25
- **Title:** When may `governance.sebi_ed_action_active` be `false`, and what must be true of the sources that were searched?
- **Record type:** **PROPOSAL — decision request, with an attached dependency request to A8.** Under `handoff/decisions/CONVENTION.md` rule 4 this record is neither an approval nor implementation authority.
- **Decision status:** **PROPOSED / UNRESOLVED — RAMKI APPROVAL REQUIRED.** Nothing here is implemented; the corrected-in-A23 narrow defect is the only change in force.
- **Date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Repository / baseline:** branch `arena/95234306-ipo-screening-engine` at remotely verified `38f51571d2a043c91fed054d90ea01141ca41de9`; `main` `01ba66c…`; PR #6 `OPEN`/`UNMERGED` at `e05c0ef…`.
- **Completes:** A23 §6.2 / §6A.2. **Depends on:** A8 (source/provider/event/cutoff contracts) — see §6 and the companion proposal `handoff/decisions/A8-R-REGULATOR-SOURCE-COVERAGE-DEPENDENCY-REQUEST-2026-10-20.md`.
- **Out of scope and unchanged:** K2's definition, `required` list and three-state semantics; `schema/`; `config/` (v1.5.0 and v1.6.0); retrieval implementation; scoring; `fixtures/`; historical evaluations.
- **Implementation authority:** NOT GRANTED by this record.

## 1. Problem statement

`sebi_ed_action_active` is a pass-through boolean that does two jobs at once: it is K2's regulatory limb (`config…K2 … {"flag": "sebi_ed_action_active"}`) and one of `config.critical_data`'s five items, so its absence turns a verdict into `INSUFFICIENT_DATA`. A `false` therefore *clears a knockout and completes a critical input*. The open question is what evidence may produce that `false`, and in particular whether "we searched and found nothing" may ever be reported as "verified absence".

## 2. What the current contract actually says

| Authority | Text | Consequence |
|---|---|---|
| `config/ipo-config.v1.5.0.json` K2 | "Promoter pledge >25% **or active SEBI/ED action**", `required: [promoter_pledge_pct, sebi_ed_action_active]` | the flag's question is about the **present**; both fields must exist for K2 to resolve |
| `config…critical_data` | includes `sebi_ed_action_active` | absence ⇒ `INSUFFICIENT_DATA`, not a favourable default |
| v1.5 §3.2 / §3.3 | `VALUE / UNKNOWN / NOT_APPLICABLE`; no `x \|\| 0` fallbacks; knockouts resolve to `TRIGGERED / CLEAR / UNKNOWN` | absence must stay a distinct state |
| `derived.py:2225-2235` | pass-through; UNKNOWN reason "the supplied input does not establish whether an active SEBI/ED action exists" | the derived layer never infers absence |
| `extraction/sections.py` `…_sebi_ed_*` routes | `True` from a count in the table's "Disciplinary Actions by SEBI or Stock Exchanges" column, a regulator-named labelled count, or a sentence with agency + finite act + party; `False` only from a denial naming **both** SEBI and the Enforcement Directorate that is not scoped to a closed period (A23 §6A.2) | the asymmetry in force today |
| `extraction/builder.py` | neither field is defaulted; `None` ⇒ absent | no favourable substitution |

Measured behaviour of that rule on this commit (synthetic pages through the published extractor; probe run in this pass):

| Evidence state | Today's outcome |
|---|---|
| unqualified denial naming both regulators | `False` (+ verbatim quote, parties noted) |
| denial naming SEBI only | field **absent** |
| denial naming ED only | field **absent** |
| denial limited to a closed period ("during FY 2023-24", "as on 31 March 2022") | field **absent** (A23 §6A.2 correction) |
| denial with an as-of date at/after the disclosure date ("as on the date of this RHP") | `False` |
| rolling window covering today ("in the last five years") | `False` |
| count in the table's SEBI/Stock-Exchange column, `Against our …` row | `True` |
| `Nil` in that column (a scope the ICDR heads to promoters only) | field **absent** — a subset's nil clears nothing |
| adverse SEBI/ED action in prose | `True` |
| stock-exchange-only adverse action ("the BSE has issued a disciplinary notice") | field **absent** (not a SEBI/ED act), while the *table's merged column* would read it as one — recorded limitation |
| boilerplate ("has not been approved or recommended by SEBI") | ignored |
| page empty / unreadable / nothing found | field **absent** |

## 3. A8, investigated rather than assumed

**3.1 What A8 actually specifies.** `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md` is titled "Final Snapshot Policy Directions and Event/Cutoff Contract" and its scope is the **Final-snapshot inputs**: A8-S subscription, A8-M market, A8-G GMP, A8-P peers, plus common timestamp/provenance safeguards. Its status line: "RAMKI-APPROVED POLICY DIRECTIONS RECORDED; **SOURCE/PROVIDER/EVENT/CUTOFF CONTRACTS OPEN**"; implementation authority "Not granted". Its own *Unresolved dependencies* list still contains "A source-specific canonical evidence contract for event occurrence, original timezone/offset and UTC timestamps, publication/retrieval times, cutoffs/evaluation time and required hashes."

**3.2 What the A8-M approval covers, verbatim.** `A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`: "**Scope:** … for a required `market.regime.nifty_trend` input **only**", and §6: "This decision applies **only** to required NIFTY trend. It does not decide UNKNOWN/Final consequences for India VIX, recent IPO listing gains, subscription, GMP, **or any other metric**". §1–§2 establish the evidence standard (authoritative source-published value for a named completed session; source identity, event timestamp + offset, publication/availability time, retrieval time, cutoff; **retrieval time is not event time**; a local rendered capture is descriptive and unqualified; a local hash identifies only local bytes); §4 requires UNKNOWN with a preserved reason for missing/invalid/stale/unqualified/conflicting evidence; §7 records that even the retained NIFTY captures are *unqualified* and §8 leaves source-native qualification **OPEN**.

**3.3 Therefore, on the question this record asks:** **A8 specifies nothing about source discovery, retrieval, issuer matching, authority, completeness, temporal scope, failed requests or unavailable sources for regulator enforcement or litigation status.** There is no SEBI/ED watch-list, no Enforcement Directorate source, and no "authority" for a negative finding about them anywhere in the approved A8 material. Any claim that A8 authorises an externally-corroborated regulatory absence would be fabricated.

**3.4 What the retrieval machinery in this repository actually does today.** Specified **and** implemented, but for a different subject:

| Capability | Where | Relevance to SEBI/ED absence |
|---|---|---|
| Allow-listed official hosts, `sebi.gov.in` included | `engine/ipo_screening/issue_terms.py:53-60` (`OFFICIAL_HOSTS`) | the *hosts* are known; **no enforcement listing is queried** — `LISTING_URLS` are the exchanges' upcoming-issue pages and SEBI's *IPO* listing |
| Provider outcome taxonomy `FOUND \| NOT_FOUND \| UNAVAILABLE \| REJECTED` | `issue_terms.py:282` | the distinction "searched and found nothing" vs "could not search" exists **as a contract**, but only for issue-term notices |
| `listing_searched` + `searched_listings`: "a bare flag is not enough, the report has to name a listing that really was read"; a search of a retained local corpus "is not evidence of non-publication" | `issue_terms.py:283-306` | **this is the ready-made evidentiary form for a verified absence**, and the repo's own repair history shows why: a marker-substring recognition bug produced a false `NOT_FOUND` → false `UNPUBLISHED` (Windows trace `ing-5aa6dd92cd7640a8`, fixed at `3fea259`) |
| Response identity by content structure (issue rows), never by a marker; JS-shell/homepage responses are `UNAVAILABLE`, never evidence of absence | `issue_terms.py:575-600` | transferable rule for any register search |
| Retries so a transient failure does not become a permanent `AWAITING_ISSUE_TERMS` | `issue_terms.py:140-150` | failure-vs-absence hygiene already solved |
| `ResolutionOutcome.status`: `RESOLVED \| PARTIAL \| UNPUBLISHED \| UNAVAILABLE \| CONFLICT \| UNVERIFIED`, conflict detection instead of arbitrary choice | `issue_terms.py:309-320` | the state vocabulary a SEBI/ED source check would extend, not replace |
| Connector framework: `SourceClass` (`OFFICIAL_EXCHANGE / SECONDARY_TRACKER / MARKET_REGIME / PEER_MULTIPLE / ANCHOR_BOOK`), `FreshnessStatus` (`FRESH / STALE / FUTURE / MISSING`), strict freshness gate, snapshot reconciliation, credential sanitisation | `engine/ipo_screening/connectors/interfaces.py`, `coordinator.py` | **no source class for a regulator register**, and the coordinator *ingests supplied snapshots*; it does not fetch |
| Document-level evidence linkage approved for GMP: L1 existing `_sources`/`_evidence` fields only, L2 raw-byte digests labelled `LOCAL_COMPUTED`, L3 identity+quote+time binding with fail-closed ambiguity, L4 failures stay diagnostics | `handoff/decisions/A18-gmp-evidence-linkage-contract.md` | the approved *shape* of "an evidenced claim about an external capture"; an A8-R contract for regulatory absence would follow L1–L4 rather than invent a new form |

**3.5 Gaps that block a verified absence today, even inside the issuer's own document.**
* `SectionExtractor.extract_page_text` (`sections.py:112-123`) swallows extraction exceptions and returns `""`, so a **failed page is indistinguishable from a blank page**, and `ExtractionReport.findings` is empty on the normal path (`extractor.py:100-110`).
* When the filing's table of contents yields no litigation entry, `extract_governance` scans a **hardcoded guessed range** `430 … min(500, page_count)` (`sections.py:2566-2570`); `TOCRouter.get_page_range` has its own `1 … min(page_count, 50)` fallback for a key that is absent (`toc.py:121-126`), which the extractor never reaches because it iterates only located keys and the outcome carries no indication that the range was a guess; for documents shorter than ~430 pages that range covers nothing at all, so "absent" is produced by an unset search rather than by a search that failed.
* A23 §6A.2's recommended precondition — "each page actually extracted successfully" — is **not expressible with today's primitives**; that clause is withdrawn here and replaced by the prerequisites in §5 C1–C2. (Correcting my own earlier recommendation is part of this record's purpose.)

## 4. Options for what may clear K2's regulatory limb

* **Option 1 (status quo).** `False` only from a present-scope, both-regulator denial in the filing's own text. No external claim is made.
* **Option 2 (bounded strengthening of Option 1).** As Option 1, plus explicit preconditions on the *document-side* coverage (§5's C1–C5), and explicit record language that a `False` is "no action disclosed by the issuer", never "no action exists".
* **Option 3 (externally corroborated absence).** `False` additionally requires a searched regulator source, with the `issue_terms` NOT_FOUND evidentiary discipline. Not implementable and not authorised today: it needs an A8-R source contract (§6), a `SourceClass`, and a K2 evidence rule.
* **Option 4 (never clear from issuer text).** `False` is not admissible; the field is only ever `True` or absent, and K2 for regulatory action can never be `CLEAR`. Maximally strict; would make K2's regulatory limb permanently UNVERIFIED for every PDF-only ingestion, contradicting the D-5 decision to keep the evidenced-negative path. Rejected for that reason, not for convenience.

## 5. Recommended standard (Option 2), stated testably

A `false` may be emitted **only** when all of the following hold, each of them checkable in code and each producing a distinct reason when unmet:

* **C1 — the section was actually located.** The search that produced the denial ran over a page range derived from the filing's own table of contents (`TOCRouter` litigation entry). A guessed span (`430…500`) may support `True` (finding adverse text is evidence) but **not** `False`. *Prerequisite: expose located-vs-guessed on the page range.*
* **C2 — the searched pages were read.** A page whose text extraction failed must be distinguishable from an empty page, and any failure in the searched range marks the absence **unverified** rather than `false`. *Prerequisite: per-page extraction status; today `""` conflates them.*
* **C3 — both regulators named, present scope.** The denial names SEBI **and** the Enforcement Directorate (or the ED by its statutory name), and is not limited to a closed period (already enforced), a single financial year, or a subset of parties.
* **C4 — population coverage.** The denial reaches the Company, the Promoters and the Directors, using the A24 R1/R3 enumeration and its "Group Companies" precision; a nil scoped to a subset covers only that subset.
* **C5 — truthful labelling.** The record's `notes`/`quote` state that this is the issuer's own declaration, and no surface may call it a verified external absence. `True` and `False` keep their current single-boolean type: **no new state, no schema change** — "we could not look" remains *absent*, which K2 already renders as `UNVERIFIED` and `critical_data` as `INSUFFICIENT_DATA`.

**Can an issuer-authored denial alone ever satisfy "verified absence"?** Under this recommendation, **yes for "no adverse action disclosed", and never for "no adverse action exists".** The distinction is preserved by C5 and by keeping the external option (Option 3) unexercised until A8-R exists. If RAMKI wants `false` to mean the stronger claim, that is Option 3 and it is blocked on A8-R — it cannot be reached by re-labelling issuer text.

## 6. Exact A8 dependencies and unresolved gaps

The precise provisions that must be approved before Option 3 is available (expanded in the companion request):

1. **Named authority set** for regulatory action (which SEBI pages/registers, whether ED/EBE/MHA sources are in scope, and which of them are authoritative for *absence* as opposed to *presence*).
2. **Issuer-matching rule** for enforcement records (entity-name normalisation, aliases, promoter identification — a name match that is not identity-verified cannot support absence).
3. **Completeness obligation**: under what evidence a search may be said to *cover* the population and period, so that `NOT_FOUND` is admissible at all.
4. **Event/observation semantics**: "active as of" which instant (evaluation cutoff, issue date, or last update), with event time distinct from retrieval time per A8-M §2.
5. **Failure and unavailability handling** (transport, JS-shell, paywall, truncated PDF): mapped to *unverified*, never to absence — the `issue_terms` `UNAVAILABLE` precedent.
6. **Retention and provenance**: capture bytes, hashes labelled `LOCAL_COMPUTED` per A18 L2, per A18 L1 no new fields or schema versions.
7. **Currency window / staleness** for a negative, which A8-M deliberately left as an OPEN prerequisite for NIFTY rather than invent a number; the same discipline applies here.
8. **Conflict rule**: issuer denial vs a found order (which wins, and that unresolved conflict ⇒ UNKNOWN, mirroring `ResolutionOutcome.status = CONFLICT`).
9. **K2 evidence policy**: whether a `false` that is externally corroborated may clear K2 while an issuer-only `false` clears it *provisionally* — a scoring/knockout decision, therefore Ramki's, not the implementation's.

**Status:** unresolved; A8 does not currently answer 1–9, and nothing in this record pretends otherwise.

## 7. Required acceptance criteria and regression tests (if §5 is approved)

1. C1: denial found on a TOC-located litigation page ⇒ `False`; same text inside the guessed default range ⇒ absent, with the reason recorded.
2. C2: a page in the searched range flagged as extraction-failed ⇒ absent (not `False`), and the failure is visible in `ExtractionReport.findings`.
3. C3/C4: existing pins keep passing (SEBI-only, ED-only, closed-period, subset-scoped nils ⇒ absent; both-regulator present-scope party-covering nil ⇒ `False`), plus new cases for a Directors-omitting denial.
4. C5: the emitted record's `notes` contains the issuer-authored qualifier; a grep-able assertion that no presentation surface turns the flag into an external-verification claim (extends the frontend test added in A23 §6A.3).
5. K2 stays three-state: `CLEAR` only with `False`, `TRIGGERED` only with `True`, `UNVERIFIED` when absent — asserted, not assumed, for each combination; verdicts `INSUFFICIENT_DATA` where `critical_data` is unmet.
6. No schema/config change; `python3 engine/tools/ipo_screen.py check-config` still `valid True`; vishal golden hash unchanged; 0 `xfail`; no historical evaluation re-run.

## 8. Affected components and downstream consumers

`extraction/sections.py` (SEBI/ED routes, page-range provenance), `extraction/toc.py` (located-vs-guessed flag), `extraction/pdf_source.py` / `SectionExtractor.extract_page_text` (per-page status), `extraction/interfaces.py` (report metadata/findings), `extraction/builder.py` (no default, unchanged), `connectors/interfaces.py` (only under Option 3: a source class), `knockouts.py`/`config` (**not** changed under §5; only Option 3/9 would touch K2's evidence policy), `presentation/service.py` + `frontend/app.js` (labels only), `tests/test_litigation_regulatory_defaults.py`, `docs/TRACEABILITY_MATRIX.md`, `docs/RUNBOOK.md`. Historical records and `build/evaluations/` are untouched.

## 9. Compatibility and migration

§5 changes only *when* an extraction may assert `False`; stored records are not re-evaluated, so approved-by-default `CLEAR` outcomes recorded before A23 remain in history and are re-derived only if someone deliberately re-runs an evaluation. Because the rule can only *narrow* the `False` path, the direction of any change is fail-closed (a cleared K2 becomes UNVERIFIED, never the reverse), which is the same migration posture D-5 took.

## 10. Questions for RAMKI

1. Do you approve C1–C5 (Option 2) as the standard for emitting `false`, including that a denial found only in a guessed page range may not clear K2?
2. Do you confirm that `false` means "no SEBI/ED action disclosed by the issuer" and never "verified absence", until and unless A8-R is approved?
3. Do you authorise the two small observability prerequisites (located-vs-guessed range; per-page extraction status) as an implementation pass, given they gate only the *favourable* path and add no state?
4. Do you want the A8-R request taken up as its own A8 sub-decision (source/matching/completeness/event/cutoff/failure/provenance/staleness/conflict provisions listed in §6), and should K2's evidence policy for an externally corroborated absence (item 9) be decided inside it?

## 11. Interim behaviour while unapproved

A23 §6A.2's rule stands, unmodified by this record: `True` from disclosed adverse action; `False` from a both-regulator, present-scope denial anywhere in the searched litigation pages, including a guessed range; everything else absent. The gap this record identifies is the *unverified* strength of that `False`, which today is stated in `notes` but not gated by C1–C2.
