# Layer 2B supplemental data validation — 2026-10-29

Base: `f954a3f36f602bf806ae3151d9ec314db10710b6`, branch `arena/4e2cc795-ipo-screening-engine`, CPython 3.11.2 / pytest 9.1.1.

Focused: `PYTHONPATH=engine .venv/bin/python -m pytest tests/test_supplemental_data.py tests/test_gap_analysis.py tests/test_cli.py tests/test_suite_tiers.py -q` → **36 passed**, exit 0, 13.60 s.

First full run found only a test-tier inventory omission: **2,258 passed / 1 failed**. `test_supplemental_data.py` uses tiny synthetic bytes named `exchange.pdf`; it was correctly added to `SYNTHETIC_EXCEPTIONS` (no parser or real filing). No product assertion was weakened.

Final full: `PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q --durations=30` → **2,259 passed, 0 failed, 0 skipped**, exit 0, 25 existing Starlette deprecation warnings, 1,351.45 s. Layer 1 verification/replay and byte-preservation are included in focused coverage.
