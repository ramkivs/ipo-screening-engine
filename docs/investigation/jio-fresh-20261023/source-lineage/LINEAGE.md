# Executed source lineage

The executed tree is reconstructible from remote refs plus the published patch. No engine file in this directory should be read as a change to the branch's own A9 lineage.

## Composition

1. `git archive 1dd6e14e7fa50a677beefba9ca7d0d1a7b322c58` (`origin/evidence/jio-score-33-recovery-20261023`)
2. Overlay these files from `d9012a2f570887ab1809e1f634dd7a78d67eecb7` (`origin/arena/07f3439f-ipo-screening-engine`), retaining the branch's A9 contract and pipeline integration:
   - `engine/ipo_screening/gmp_binding.py`, `gmp_evidence.py`, `gmp_policy.py`
   - `engine/ipo_screening/pipeline.py`, `evaluation_record.py`, `connectors/coordinator.py`
   - every `tests/test_gmp_*.py` and `schema/gmp-*.json` present there
3. Apply `corrections.patch` (`git diff 0d896040adc5e1484fd4835e362f459105ec07ad 36086944a2c321d2613af28972fd887af9f25f8c -- engine tests`).

`36086944` adds the corrected regression expectations to `514ca599`; the engine code is byte-identical, so the ingestion/evaluation was executed on the same engine revision that the tests now cover.

Resulting tree hashes: `executed-source-sha256.txt` (278 files). Verified: the reconstructed tree matches the executed tree for every engine and test file; the only difference was `tests/test_jio_rhp_issue_terms.py`, which was copied in for an evaluation attempt and **excluded** from the run (see report §9).

## Why the branch engine is not overwritten

`origin/arena/07f3439f-ipo-screening-engine` and the evidence line carry different, separately developed A9/engine variants (for example `gmp_binding.py` is present on the Arena line and absent on the evidence line). Writing the executed tree wholesale into the Arena branch would silently replace the branch's A9 implementation with a different one. Publishing the patch plus the exact reconstruction recipe keeps the execution auditable **and** the branch's A9 lineage intact.
