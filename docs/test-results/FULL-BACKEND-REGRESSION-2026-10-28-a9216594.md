# Full backend regression receipt — 2026-10-28

## Tested integration candidate

- Repository: `ramkivs/ipo-screening-engine`
- Branch: `arena/a9216594-ipo-screening-engine`
- Base/production-code commit: `0a77bf95a3fa74101bd40d1137c4dd33badb5e87`
- `origin/main` before the run: `0a77bf95a3fa74101bd40d1137c4dd33badb5e87`
- Working-tree delta during the run: documentation, governance/evidence records, and `.gitattributes` only; no production code, test, schema, config, fixture, or scoring file differed from the base commit.

## Environment

- CPython 3.11.2
- pytest 9.1.1
- Dependencies installed from the repository's pinned `requirements.txt` into the ignored local `.venv` because no supported provisioned environment was available.

## Command and result

```bash
PYTHONPATH=engine .venv/bin/python -m pytest tests/ -q --durations=30
```

- Collected: 2,238
- Passed: 2,238
- Failed: 0
- Skipped: 0
- Warnings: 25 Starlette deprecation warnings (one TestClient/httpx warning and 24 `HTTP_422_UNPROCESSABLE_ENTITY` warnings)
- pytest result: exit 0
- pytest duration: 1,493.58 seconds (24m53s)
- Progress plugin duration: 1,489.6 seconds
- PDF text cache: 15,161 hits; 1,615 decoded pages

No assertion was weakened, no test was removed or skipped, and no failure correction was required.

## Scope statement

This receipt validates the exact production/test tree at the stated base commit plus the pending documentation/governance integration candidate. It does not claim that a real new IPO was evaluated. No evaluation store, provider route, exchange adapter, peer injection route, cache behavior, scoring behavior, or source authority was changed by this validation.
