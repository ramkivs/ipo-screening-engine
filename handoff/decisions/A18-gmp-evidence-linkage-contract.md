# A18 — GMP Evidence-Linkage Contract (L1–L4)

- **Decision ID:** A18
- **Title:** GMP evidence-linkage contract using existing v1.5 input fields
- **Decision status:** RAMKI-APPROVED CONTRACT; narrow implementation authorized for the correction and verification described below.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-16 (Asia/Calcutta). No decision time is supplied or asserted.
- **Authorization basis:** Ramki's direct Arena task instruction dated 2026-10-16 refers to L1–L4 as the approved contract and directs correction, regression coverage, and verification. This record is based on that instruction, not on an Arena report or a prior assistant recommendation.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Authoritative baseline:** `805affe10ef387b649717facb31b0378f7b233d7`
- **Implementation baseline:** `3f8a1766e24a4926b6cd0478ae73ad81865d62c0`; signed-token correction `e473f0090916cf6a125447be077316ea694b2675`.
- **Scope:** Link one evaluation's GMP observation and issue identity to one retained rendered capture using existing v1.5 `_sources` and `_evidence` fields. No publisher is selected or qualified by this decision.
- **Publication status:** This decision and the implementation remain on the working implementation branch. This record does not authorize a push, merge, PR, or other publication to the authoritative branch.

## Approved contract

The approved implementation-facing choices are L1 as revised, L2-a, L3-a, and L4-a from §7.10 of `docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md`. They are bounded as follows:

1. **L1 — Existing input fields.** A link is attempted only through the existing GMP source reference and a single `_sources` manifest URI/content-hash pin. The reference has no `retrieval_timestamp` when the capture manifest records only a window. The three canonical manual evidence entries bind `company_name`, `market.gmp.pct`, and `market.gmp.as_of` to exact displayed text and locators. The title line must identify the evaluated issue.
2. **L2-a — Local raw-byte digests.** For a verified link, recompute SHA-256 over the exact manifest bytes and exact declared-artifact bytes. Record both as `RAW_ARTIFACT_BYTES` / `LOCAL_COMPUTED`. Preserve the manifest's bracketing retrieval window as `UNKNOWN` `LOCAL_RETRIEVED_AT`; never invent an exact receipt time or treat a window endpoint as one.
3. **L3-a — Identity, value, and stamp binding.** The displayed issue identity must match both the evaluated company and the exact capture title. The percentage and publisher timestamp quotes must bind to the displayed content and equal the input values. The timestamp must be no later than the capture-window end. A percentage quote must equal the complete signed percentage token on its locator line; embedded substrings and multiple/ambiguous percentage tokens fail closed. Existing A17 cutoff, age, and trend-label rules remain unchanged.
4. **L4-a — Nonterminal failures.** Link failures remain diagnostics; they do not reject otherwise processable evaluations or change scoring. A9 remains fail-closed for Final. No input-schema, A15-schema, or version change is authorized.

Strict duplicate-key parsing is scoped to the evaluation-input and manifest boundaries that consume the link. It does not change the permissive JSON behavior of configuration or stored-record readers.

## Preserved authority and qualification limits

- D1–D3 remain the approved capture-integrity, cutoff-availability, and missing-versus-zero rules; a `VERIFIED` link means only that this evaluation is tied to the specified retained local bytes and text.
- **MarketLiveIPOGMP remains NOT QUALIFIED.** R7 remains **UNRESOLVED**. No R7 capture was taken, and none is authorized or implied here.
- Publisher authenticity, source-native bytes, cached-content status, source revision history, R7, and R8 are not established by a link, local Git write-once checks, or local hashes.
- The frozen evaluation core, scoring semantics, A9 behavior, existing schemas/versions, and honest `UNKNOWN` capture-window handling are unchanged.
- Replay preserves raw link declarations so failed/contradictory links remain failed on replay.

## Implementation and verification record

The correction is commit `e473f0090916cf6a125447be077316ea694b2675` on `arena/ea6e5bc2-ipo-screening-engine`. It changes only `engine/ipo_screening/gmp_evidence.py` and `tests/test_gmp_evidence_linkage.py` relative to its implementation parent. The code binds the quote to one complete signed percentage token, rejects embedded or multiple tokens, parses the sign before comparing the numeric value, and rejects an ambiguous repeated `IPO GMP` title marker. Focused tests also cover wrong-issuer and empty-issuer identity, final A15 field tampering, negative-value binding, and replay/failure boundaries.

Verification against the implementation commit:

- Before correction, the new regression using source line `-71.4%`, quote `71.4%`, and input `71.4` failed because the verifier reported `result=VERIFIED` instead of `FAILED`.
- `.venv/bin/python -m pytest tests/test_gmp_evidence_linkage.py tests/test_strict_evaluation_json.py tests/test_d1_d3_gmp_source_policy.py -q` — **128 passed**.
- `.venv/bin/python -m pytest tests/ -q` — **885 passed**, two Starlette deprecation warnings, 316.45 seconds.
- `.venv/bin/python -m compileall -q engine tests` — passed.
- `verify_frozen_core()` — passed, all six pinned files.
- `git show --check --oneline HEAD` — passed.

The focused and full test runs were performed on implementation commit `e473f0090916cf6a125447be077316ea694b2675`, before this documentation record was added. They are not represented as tests run on a later documentation-only commit.

## Dependencies and next steps

1. Keep this decision record separate from the implementation commit for review.
2. The repository tracker was not edited under the task's explicit scope restriction; its historical GMP/linkage status must be reconciled through the authorized tracker process before treating it as current status.
3. Prepare any authoritative integration as a new, implementation-only commit based on the authoritative baseline above; do not merge the implementation branch wholesale or import the old proposal history unchanged.
