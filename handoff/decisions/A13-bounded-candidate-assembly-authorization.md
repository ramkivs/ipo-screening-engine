# A13 — Bounded Non-Canonical Review-Candidate Assembly

- **Record ID:** A13
- **Title:** Bounded product/governance candidate assembly on the fixed session branch
- **Status:** RAMKI-APPROVED — LIMITED CANDIDATE-ASSEMBLY AUTHORITY
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-13 (Asia/Calcutta)
- **Approval provenance:** Ramki's explicit, bounded candidate-assembly instruction in the Arena conversation received 2026-10-13 (Asia/Calcutta). No decision time is supplied or asserted.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** Fixed target branch `arena/573e69a4-ipo-screening-engine`, at `de8d5f82442eff3ef77437c1fe96fa73c7a62c2c` before the A11–A13 disposition records; product source `arena/01a10b42-ipo-screening-engine` at `4b19faf848a721265597a678926988d484d30e59`; governance source `arena/4e1080b7-ipo-screening-engine` at `adbd93c5b4450fb113561368d7d101eb4686c842`; common baseline `main` at `01ba66c12ca1195fd7acbd287c3e39a019808094`.
- **Scope:** Assemble an exact, non-canonical review candidate on the existing session branch and preserve/pin the controlling governance evidence.
- **Implementation authority:** NOT GRANTED. Phase 1 and `P1-CANON-01` remain unauthorized.

## Approved bounded assembly

1. **Target:** only `arena/573e69a4-ipo-screening-engine`. Begin from the session-branch HEAD containing this A13 authorization record. Record the resulting merge/candidate commit and its parents after assembly.
2. **Product source:** incorporate the 01a product tree at `4b19faf848a721265597a678926988d484d30e59` as-is with a non-fast-forward merge into the fixed session branch. This creates a review candidate only; it is not a canonical product selection or merge to `main`.
3. **Governance source:** use 4e at the pinned commit `adbd93c5b4450fb113561368d7d101eb4686c842` as the controlling source for the current governance records. Do **not** merge the 4e branch history or its application/configuration/fixture/test changes.
4. **Decision-record content:**
   - Keep the 01a copies of `handoff/decisions/CONVENTION.md`, `A1-evidence-adjudication-authority.md`, and `A7-knockout-verdict-precedence.md`; their blobs are identical on 01a and 4e (`92005f1685dc8246a4d54f8abeb7ca0891058792`, `11eebb4e214bbb9acff6a2f235937f1214653b94`, and `3e70b562c2dfc463675cc9a4043542803481b21c`, respectively).
   - Use the **4e** version of `handoff/decisions/A8-final-snapshot-event-cutoffs-investigation.md`. The 01a blob `b83a5828c8f0fd64ce5a83314e9b90b4fbc1b3e0` is older; the controlling 4e blob is `9a96f29befdb3f059e9fce917e41cc86d58ce520`. Do not manually combine them.
   - Add byte-for-byte copies from 4e of `handoff/decisions/A8-M-ARENA-HANDOFF-2026-10-13.md`, `A8-M-NIFTY-TREND-DECISION-APPROVAL-2026-10-13.md`, `A8-M-OBSERVATION-CONTRACT-AND-UNKNOWN-DECISION-APPROVAL-2026-10-13.md`, `A9-missing-gmp-final-fail-closed.md`, and `A10-interim-subscription-handling.md`.
   - The shared `evidence/market-observations/official-index-history-20261013/A8-M-EVIDENCE-FINDINGS.md` is byte-identical on 01a and 4e (blob `da97d38e2118cc38641c6b4b6fa001bfb3637ec3`) and is carried from 01a. Pin the 4e-only `evidence/market-observations/official-index-history-20261013/A8-M-SMA-EVIDENCE-20261013.md` (blob `4c5462abd25206f8cc3c7f390aaf9c6fb5c282df`) and the supporting `handoff/investigation/A8-M-DECISION-INPUT-RECONCILIATION-2026-10-13.md` and `handoff/investigation/A8-M-SOURCE-QUALIFICATION-AND-AVAILABILITY-INVESTIGATION-DRAFT-2026-10-13.md` to the exact 4e commit rather than merging the 4e evidence/data tree.
5. **Tracker protection:** preserve the session-branch `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md` as a review candidate. Do not overwrite it with the 4e source tracker; leave the source tracker on 4e unchanged. Update the session candidate only to report this assembly and retain its explicit non-canonical/pending-review status.
6. **Other session material:** preserve the published audit, tracker-delta proposal, Program Authority package, and unrelated untracked authorization-request note. Do not publish the unrelated note.
7. **Scope boundary:** 01a's existing product tree is incorporated unchanged as the selected review base; this does not approve its policies, configurations or fixtures or authorize edits to them. Do not import any 4e `engine/`, `config/`, `fixtures/`, `schema/` or `tests/` changes, including 4e's partial A9 gate in `pipeline.py`. Do not add/modify scoring, schema, configuration, fixture, test, provider, A9 or NIFTY behavior.
8. Preserve Phase 0 OPEN and Phase 1 NOT AUTHORIZED. The candidate is not accepted, canonical, release-ready or production-authorized. No P1 implementation grant is made.

## Conflict and divergence handling

The inspected refs share `main` as their merge base. Session-vs-01a changed paths had no same-path overlap at the stated tips; session-vs-4e overlap was the tracker path; 01a-vs-4e had 72 same-path changes, including core code, configuration, fixtures and evidence. Therefore this authorization permits the 01a product merge plus the explicit decision-record handling above, **not** a wholesale 4e merge. Preserve the session tracker candidate and current 4e source tracker separately. If any conflict arises outside the explicit A8-record selection above, stop that change and request amended authority.

## Acceptance and review boundary

Technical assembly verification may proceed without an appointed reviewer. It must verify the exact source parents, selected 4e decision-record contents, retained session documents/tracker, and exclusion of 4e code/configuration/fixtures. This is not independent acceptance. Ramki must separately appoint an independent reviewer for the exact assembled candidate; no reviewer is appointed by A13.

## Rationale

The verified source refs have no changed-path overlap between the session and 01a, while the 01a and 4e product histories have broad conflicting same-path changes. Selecting 01a as the product-code review base and copying only the named 4e governance records gives reviewers a traceable candidate without silently combining incompatible application histories or replacing the session tracker with the source tracker. The older 01a A8-final record is explicitly superseded in the candidate by the exact current 4e record; no manual synthesis is authorized.

## Supporting evidence and v1.5 references

- Source identities and path/blob comparison recorded in the published reconciliation audit and Program Authority package at the session baseline above.
- `handoff/decisions/CONVENTION.md` (GOV-001), `A1-evidence-adjudication-authority.md`, `A7-knockout-verdict-precedence.md`, A8 final-snapshot, A8-M, A9 and A10 at the exact source commits named above. The selected 4e evidence/investigation paths are pinned in §4 above.
- `handoff/authoritative/ARENA_IPO_Screening_Artifact_Manifest_v1.5.md`, `IPO_Screening_Engine_Specification_v1.5.md` §§5, 19–20, 23, and `ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md` §§1–2, 5, 12–15, 23. These remain authoritative; A13 authorizes only candidate assembly and does not amend requirements or authorize implementation.

## Unresolved dependencies

Independent reviewer appointment and acceptance; formal Phase 0 closure; canonical evidence/output contract approval; separate Phase 1 implementation authority; and all release/production gates remain open. No candidate status in A13 satisfies any of these.

## Explicitly not authorized

- `P1-CANON-01` or any other Phase 1/application implementation.
- Source qualification, provider access, hash computation/certification, scoring, schema/configuration/fixture/test changes, or A9/NIFTY gate work.
- Merge to `main`, PR mutation, release, production activation, or treating the candidate as canonical.
- Changes to the source product branch 01a or governance branch 4e.

## Execution and verification addendum

**Recorded after execution on 2026-10-13 (Asia/Calcutta).** This addendum records the authorized assembly result; it does not expand or change A13's authority.

- **Candidate merge commit:** `9bad659927616ad7fd3aad2864b6637f095872c5`; tree `5adc30818c8bff61d8ca4b4a5529d2389df91bc5`.
- **Parents:** first parent is the A11–A13 authorization commit `7e25d1e2f97d162d97ff837c7dd40fb3d070aea1`; second parent is the exact 01a product source `4b19faf848a721265597a678926988d484d30e59`. The 4e commit is not an ancestor; no 4e history was merged.
- **Product-tree integrity:** `engine/`, `config/`, `fixtures/`, `schema/`, `tests/`, `frontend/`, `docs/`, and `evidence/` at the candidate match the 01a source tree exactly. The selected 4e governance files below are the deliberate documentation-only differences. The 01a pipeline contains no A9 gate implementation; no application, scoring, schema, configuration, fixture or test behavior was authored or modified in this assembly.
- **Selected 4e blobs in the candidate:** A8 final-snapshot `9a96f29befdb3f059e9fce917e41cc86d58ce520`; A8-M Arena handoff `4784e6681ada91e37e2e7a44cadae4d8f833c5c1`; A8-M NIFTY decision `617d04bc5d4135f876ecfac9ee2e9a1200f0dee1`; A8-M observation/UNKNOWN decision `3e5fc1a0112758107308d0be6cccd23649fc472a`; A9 `60372381bec60fe2d8b590ce63166f02ce35b6e3`; and A10 `0500933b3578530cd30d1e548c97807e6b9dfbf9`. Each candidate blob was checked against 4e at `adbd93c`.
- **Shared/pinned evidence:** A1, A7 and `CONVENTION.md` match the byte-identical source blobs recorded above. The candidate's A8-M evidence-findings file is the shared 01a/4e blob `da97d38e2118cc38641c6b4b6fa001bfb3637ec3`; the 4e-only SMA evidence blob `4c5462abd25206f8cc3c7f390aaf9c6fb5c282df` and the named 4e investigations remain pinned, not copied.
- **Tracker separation:** The 4e source tracker remains blob `f661f1b73df04dbacba8d15254a25c2b573d3d88` at the pinned source. The session tracker is its separate candidate-only derivative and is updated in the documentation-only follow-up to point at this exact candidate. The unrelated untracked authorization-request draft was preserved and not published.
- **Scoped tests on this exact candidate:** `tests/test_enrichment_contract.py`, `tests/test_validation_gates.py`, and `tests/test_reproducibility_store.py` — **85 passed**. This is not a full-suite or Windows-validation claim. The temporary test environment was outside the repository.
- **Whitespace check:** the full candidate diff check reports inherited trailing-whitespace/blank-line findings in unmodified 01a documents and fixture artifacts. The directly edited tracker and selected governance files passed their scoped whitespace check; no unrelated source files were normalized.
- **Remote durability:** after pushing, a fresh fetch and `git ls-remote` both reported the session branch at `9bad659927616ad7fd3aad2864b6637f095872c5`; remote tree, parents and selected governance blobs matched the local candidate.

The candidate remains non-canonical and pending independent review. Phase 0 remains OPEN, Phase 1 and `P1-CANON-01` remain UNAUTHORIZED, and no release or production authority is implied.

---
