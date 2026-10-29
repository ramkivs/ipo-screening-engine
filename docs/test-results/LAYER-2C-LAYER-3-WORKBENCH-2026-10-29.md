# Layer 2C, Layer 3, and local workbench validation receipt — 2026-10-29

## Implemented boundary

Layer 2C admits only accepted, exact-baseline-bound Layer 2B subscription entries for QIB, NII, retail, and overall demand. Entries must carry `SOURCE_ARTIFACT_HASH_VERIFIED`, fall inside the baseline bidding window, and pass exact payload/manifest identity checks. The unchanged core engine performs the secondary evaluation and enforces module caps. Secondary artifacts are isolated, immutable, independently hashed, verifiable, and replayable.

Layer 3 stores peer and qualitative assertions separately, labels every point attribution `[OPERATOR_ASSUMPTION]`, limits changes to Modules B and E, enforces module and total caps, and preserves knockout status. It cannot mutate Layer 1 or Layer 2C.

The FastAPI local workbench lists Layer 1 evaluations; hashes uploaded evidence; drives Layer 2B injection and Layer 2C evaluation; accepts day 1/2/3 demand observations; builds isolated operator scenarios; and displays baseline, enriched, and scenario realities with explicit badges and hash lineage. It is a local single-user tool, not an authenticated production service.

## Focused and full validation

- Focused command: `PYTHONPATH=engine .venv/bin/python -m pytest tests/test_secondary_scenario_workbench.py tests/test_supplemental_data.py tests/test_cli.py tests/test_suite_tiers.py -q`
- Focused result: **35 passed, 1 non-fatal deprecation warning in 15.91s**.
- Final full command: `PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q --durations=30`
- Final full result: **2,267 passed, 0 failed, 0 skipped, 25 warnings in 1625.84s**.
- Frontend command: `npm test --prefix frontend`
- Frontend result: **93 passed, 0 failed**.
- All repository JSON schemas passed `jsonschema.validator_for(...).check_schema(...)`.
- Frozen core, golden result, and inactive v1.6 verification passed.
- `PYTHONPATH=engine .venv/bin/python -m compileall -q engine` passed.
- `git diff --check` passed before publication.

## Operational acceptance

The retained Jio evaluation `JIO-PLATFORMS-LIMITED-20261027-145236Z-final-0fde1451` was used without modification. A conspicuously synthetic QIB artifact (`12.34x`, observed inside the 2026-10-21 through 2026-10-23 bidding window) exercised Layer 2B/2C; it makes no publisher-authenticity or value-truth claim.

- Baseline result hash: `0fde1451c1ea3ee61e6178d48908e8bffe12a943ba21f42f993429d11af9fb44`
- Baseline score/verdict/confidence: `37.0 / AVOID / Low`
- Supplemental ID: `SUPP-c69b3dc490f9bb2e`
- Supplemental canonical hash: `c69b3dc490f9bb2edc8dbd35257e17d80fe6c1f0bdd9a2fa2b71537ef4c5c14a`
- Synthetic artifact SHA-256: `e613af4f5b2b4066121de498d89d06541877a1434df02ca626207b377a5bd353`
- Secondary ID: `SEC-f9e78db70f7e91d3`
- Secondary canonical hash: `f9e78db70f7e91d3f9564d1d18f94afb1e7eadd29bc49532311b2ca64b5f5bcf`
- Secondary score/verdict/confidence: `39.0 / AVOID / Low`; Module F changed `0.0 → 2.0`; every other module was unchanged.
- `secondary-verify`: exit `0`, valid.
- `secondary-replay`: exit `0`, canonical hash matched.
- Scenario ID: `SCN-222b153c68a914fc`
- Scenario input hash: `222b153c68a914fc35308f74be7077bd5411515b58c077fac6adb3881030e14e`
- Scenario score/verdict/confidence: `48.0 / AVOID / Low`; the triggered knockout remains controlling despite the score-band scenario.
- Baseline before/after inventory SHA-256: `ec4e2634c7644bfc06a0f219d8d93bbe720cfea78e152476d963d12c07acedf7` for both inventories; byte comparison exited `0`.
- Post-operation Layer 1 `verify`: exit `0`, seven artifacts and zero mismatches.
- Post-operation Layer 1 `replay`: exit `0`, stored and recomputed result hashes matched.

The operational artifacts are intentionally under ignored `build/layer2c-acceptance/`; hashes above retain their identities without promoting synthetic bytes into repository evidence.
