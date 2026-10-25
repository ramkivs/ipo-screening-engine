# A18 — GMP Evidence-Linkage Contract (L1–L4)

- **Decision ID:** A18
- **Decision status:** RAMKI-APPROVED CONTRACT; the bounded linkage implementation and regression correction were authorized by the direct task instruction.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-16 (Asia/Calcutta); no decision time is asserted.
- **Approval basis:** Ramki's direct 2026-10-16 instruction identifies L1–L4 as the approved contract and directs correction, regression coverage, and verification. This record does not derive approval from an assistant recommendation.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Authoritative baseline:** `805affe10ef387b649717facb31b0378f7b233d7`
- **Implementation source:** code commit `ca6c9862c5809d72a73d1493ef5f6fe31ec7f34f`; the eight implementation/test paths are unchanged at the verified session tip `bbe445a34196b93c98e9fa018888eb1536151f02`.
- **Scope:** Link one evaluation's GMP observation and issue identity to one retained rendered capture using existing v1.5 `_sources` and `_evidence` fields. No publisher is selected or qualified.
- **Publication snapshot:** At handoff verification, authoritative ref `arena/573e69a4-ipo-screening-engine` was `805affe10ef387b649717facb31b0378f7b233d7` and session ref `arena/ea6e5bc2-ipo-screening-engine` was `bbe445a34196b93c98e9fa018888eb1536151f02`. The session history is nine commits ahead and contains proposal history. No clean baseline-derived refs, authoritative integration, or PR had been created. Do not fast-forward or publish that session history as a substitute for clean refs.

## Approved contract

The approved choices are L1 as revised, L2-a, L3-a, and L4-a:

1. **L1 — Existing input fields only.** Attempt a link only through the existing GMP source reference, a single `_sources` manifest URI/content-hash pin, and manual `_evidence` entries for `company_name`, `market.gmp.pct`, and `market.gmp.as_of`. The capture title must identify the evaluated issue. Do not add fields or schema versions.
2. **L2-a — Local raw-byte digests.** On a verified link, recompute SHA-256 over the exact pinned manifest bytes and declared artifact bytes; represent both as `RAW_ARTIFACT_BYTES` / `LOCAL_COMPUTED`. If the manifest records only a bracketing capture window, preserve it as `UNKNOWN` `LOCAL_RETRIEVED_AT`; never invent an exact retrieval instant or put the window end in `retrieval_timestamp`.
3. **L3-a — Identity, quote, and time binding.** Bind the displayed identity to both the evaluated issuer and capture title. The percentage and publisher timestamp quotes must be on their declared locator lines and equal the input values. The percentage quote must be exactly one complete signed percentage token on that line; omitted signs, embedded substrings, multiple tokens, or ambiguous titles fail closed. The publisher timestamp must not exceed the capture-window end. Existing A17 cutoff, age, and publisher-label rules remain unchanged.
4. **L4-a — Nonterminal failures.** Link failures remain diagnostics and do not reject otherwise processable evaluations or change scoring. A9 remains fail-closed for Final. No input-schema, A15-schema, or version change is authorized.

Duplicate-key JSON parsing is scoped to evaluation-input and capture-manifest parsing for the link. It does not change configuration or stored-evaluation JSON readers.

## Preserved authority and qualification limits

- A `VERIFIED` link means only that this evaluation is tied to the specified retained local bytes and text. It does not authenticate a publisher or qualify a source.
- **MarketLiveIPOGMP remains NOT QUALIFIED; InvestorGain remains NOT QUALIFIED; PapsDigital remains a non-independent alternative.** R7 remains **UNRESOLVED**; R8 history remains open.
- The documented new-observation condition for an R7 capture was not met; no R7 capture was taken.
- A9 remains fail-closed: present GMP is `SOURCE_UNQUALIFIED`, missing GMP is `MISSING`, and no terminal `final_outcome` is created.
- The frozen core, scoring semantics, schemas, versions, and honest `UNKNOWN` capture-window handling are unchanged. Replay preserves the raw declarations needed to keep failed/contradictory links failed.

## Implementation and verification snapshot

The signed-percentage correction is in `gmp_evidence.py`; tests cover D1 duplicate-artifact-ID rejection, D2 capture-window-end cutoff semantics, issuer/title identity, cutoff, replay, integrity/tampering, strict duplicate keys, and signed-percentage matching/mismatching. The implementation-only patch is a path-filtered diff from the authoritative baseline to `ca6c986`; it contains exactly the eight paths listed in the handoff manifest.

Previously reported clean-tree verification applied that patch to a temporary archive of the baseline: focused group **128 passed**; full suite **885 passed** with two Starlette deprecation warnings; compileall passed; frozen core **6/6**, golden result, and v1.6 integrity checks passed. These are prior self-run results, not independent verification and not tests on a clean Git commit. The Windows runbook requires rerunning the checks on the final clean implementation commit before push.

## Publication reconciliation (2026-10-16)

The publication snapshot above is superseded. The eight-path implementation was integrated into `arena/573e69a4-ipo-screening-engine` by PR #4 (implementation commit `c0577d85f268164c6dcccc74fa42125d3f2ba48b`, merge `52536a1d9aae7aa298038b07893668af78e360fc`), and the tracker integration record by PR #5 (merge `9e8c260576b85fad66484c19eec04fe328e1575f`, the authoritative HEAD when this record was published). This decision record and source-policy §7 are published in the authoritative tree by the documentation commit accompanying this reconciliation; the earlier session branches (`arena/ea6e5bc2-ipo-screening-engine`, `arena/gmp-evidence-linkage-docs-clean`, `arena/5ccbfd5d-ipo-screening-engine`) are provenance only and must not be merged. At the authoritative HEAD, the full Python suite was run in a Linux environment: **885 passed** (focused GMP group **128 passed**), frozen core 6/6, golden result and v1.6 checks PASS, frontend **55 passed** — self-run verification, not independent review. Qualification limits above are unchanged.

## A28 explicit extension — 2026-10-22

RAMKI's current Q2 selection ratifies optional/UNKNOWN trend admission if all
other qualification requirements pass, and authorizes bounded asserted-label
linkage. A28's exact trend extension supersedes only this record's absent trend
link representation. Non-null trend now requires the fourth canonical evidence
`EV-market.gmp.trend`, exact label locator/quote on one `Trend: <label>` line,
the same source and existing A17 mapping. Unsupported/conflicting/hidden labels
fail linkage. Null trend preserves three-field linkage when no label is asserted.
Projection and replay preserve the fourth reference when present. No derived
label, input/A15 schema change, scoring change or source approval follows.
The A28.1 standalone binding schema is NOT an input/A15 extension and is NOT
consumed for A9 admission until actual qualification evidence exists.
