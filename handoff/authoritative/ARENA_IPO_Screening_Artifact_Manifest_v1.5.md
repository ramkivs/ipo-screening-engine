# Arena Share Package --- IPO Screening & Qualification Engine v1.5

## Purpose

This package is for Arena implementation/rebuild of the IPO Screening &
Qualification Engine.

The current Claude artifacts are **reference/prototype material**. The
new v1.5 specification is the target contract.

## Artifact precedence

1.  **`IPO_Screening_Engine_Specification_v1.5.md` --- AUTHORITATIVE
    TARGET SPEC**
2.  **`IPO_Screening_Engine_Technical_Design_v1.5.md` --- TARGET
    ARCHITECTURE**
3.  **`ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md` ---
    EXECUTION INSTRUCTIONS**
4.  Current Claude artifacts --- reference implementation, current
    policy/config/schema, and test/source material.

If a Claude artifact conflicts with v1.5, v1.5 wins.

------------------------------------------------------------------------

## Files to share with Arena

### A. New authoritative artifacts

  -----------------------------------------------------------------------------------------------
  File                                                    Role
  ------------------------------------------------------- ---------------------------------------
  `IPO_Screening_Engine_Specification_v1.5.md`            Corrected
                                                          functional/scoring/data/persistence
                                                          specification

  `IPO_Screening_Engine_Technical_Design_v1.5.md`         Layered architecture, evidence model,
                                                          persistence and Excel design

  `ARENA_IPO_Screening_Engine_v1.5_Execution_Prompt.md`   Detailed
                                                          implementation/review/test/acceptance
                                                          prompt
  -----------------------------------------------------------------------------------------------

### B. Existing Claude artifacts --- share as reference

  -------------------------------------------------------------------------------------
  File                                              Role
  ------------------------------------------------- -----------------------------------
  `IPO Screening Engine v 1.3 — Specification.md`   Existing specification/policy
                                                    baseline; it contains v1.4 content
                                                    despite filename

  `ipo-config.json`                                 Existing scoring configuration and
                                                    thresholds

  `ipo-input.schema.json`                           Existing input schema

  `ipo-scorer_4.html`                               Existing Claude
                                                    implementation/prototype to audit
                                                    and selectively reuse

  `VISHAL-NIRMITI-LIMITED.json`                     Existing test fixture

  `U01122MH1994PLC185445-vishal nirmiti.pdf`        RHP ground-truth source for the
                                                    test fixture
  -------------------------------------------------------------------------------------

## Total

**9 files** should be shared.

------------------------------------------------------------------------

## What should NOT be treated as authoritative

Do not treat:

-   the current HTML score;
-   current derived values;
-   current confidence percentage;
-   current Excel/HTML presentation;
-   Claude's current handling of missing data;
-   current regex extraction;
-   current browser API-key approach

as authoritative.

They are material to review, but Arena must correct them where they
conflict with v1.5.

------------------------------------------------------------------------

## Expected Arena outcome

Arena should return:

1.  architecture/design decision;
2.  revised schema;
3.  revised config;
4.  corrected implementation;
5.  validation engine;
6.  evidence/provenance model;
7.  tri-state knockout engine;
8.  sector overlays;
9.  deterministic scorer;
10. confidence/range engine;
11. immutable historical evaluation record;
12. Excel workbook generator;
13. Vishal Nirmiti golden regression;
14. full regression suite;
15. reproducibility test;
16. spec-to-code traceability matrix;
17. sample historical Excel workbook;
18. runbook/documentation.

## Historical preservation rule

Excel is the required user-facing historical output.

The implementation must additionally preserve immutable machine-readable
evaluation records from which Excel can be regenerated.

No historical evaluation may be overwritten.
