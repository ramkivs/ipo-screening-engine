# Two-layer gap-analysis validation receipt — 2026-10-29

- Base commit: `da52df318a7b965f009cd1eeb1759bc8c848f01f`
- Branch: `arena/6f3b5c5d-ipo-screening-engine`
- Environment: CPython 3.11.2, pytest 9.1.1, pinned `requirements.txt` in ignored `.venv`

Focused command:

```bash
PYTHONPATH=engine .venv/bin/python -m pytest tests/test_gap_analysis.py tests/test_cli.py -q
```

Result: **23 passed, 0 failed, 0 skipped**, exit 0, 7.70 s.

Full backend command:

```bash
PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q --durations=30
```

Result: **2,247 passed, 0 failed, 0 skipped**, exit 0, 25 existing Starlette deprecation warnings, 1,209.07 s (20m09s). PDF text cache: 15,161 hits and 1,615 decoded pages.

The nine new focused cases cover empty and populated reports, deterministic output, explicit UNKNOWN score linkage, non-numeric stale/unusable/unverified/unsupported states, unavailable reason/provenance, invalid identity, integrity refusal, baseline byte/hash preservation, no store write, and output separation/refusal. No evaluation was rescored and no supplemental value was admitted.
