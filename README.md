# IPO Screening Engine

A single-user, personal-use IPO research application for Ramki. The Python engine performs deterministic, fail-closed screening and stores immutable evaluation records. A local FastAPI server exposes the browser UI and presentation API from the same origin; the UI displays engine results and does not calculate scores in the browser.

## Quick start (Python 3.11+)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export PYTHONPATH="$PWD/engine"

# Validate the active v1.5 configuration.
python engine/tools/ipo_screen.py check-config

# Run the deterministic worked example into the ignored local build/ store.
python engine/tools/ipo_screen.py run fixtures/vishal_nirmiti/input.json \
  --at 2026-10-05T12:00:00Z \
  --store build/evaluations

# Start the personal-use web app. Keep it bound to this computer.
uvicorn ipo_screening.presentation.api:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/ui/>. The API is at `/api/v1`; interactive API docs are at `/docs`.

The UI reads `IPO_STORE_ROOT` (default `build/evaluations`). To use another local store, set that environment variable before starting Uvicorn. The normal API includes GET read-model routes and limited POST operations for filing ingestion and evaluation lifecycle actions. It does not provide scoring/configuration mutation endpoints. Every request must use a literal `localhost` or loopback-IP `Host` authority (arbitrary hostnames are rejected), and workflow POSTs require a same-origin `Origin` header. The personal server has **no authentication**; keep it on loopback and do not expose it to a network you do not control.

## Verify a stored evaluation

```bash
python engine/tools/ipo_screen.py verify --store build/evaluations
python engine/tools/ipo_screen.py replay \
  VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0 \
  --store build/evaluations
```

New evaluations include `evaluation-record.v1.json` alongside the existing artifacts. Stores and generated reports under `build/` are local and ignored by Git.

## Tests

```bash
python -m pytest tests/ -q
npm --prefix frontend test
```

The browser UI is static JavaScript and needs no npm install. Python test/API dependencies are listed in `requirements.txt`.

## Operating limits

- Use evidence-backed input and preserve `UNKNOWN`; never substitute zero or infer source qualification.
- Official source/event/freshness contracts remain incomplete for some market, subscription, GMP, and peer metrics. Missing required evidence remains visibly unresolved; the app does not invent data or policy.
- Exchange connectors are not live streaming feeds. On-demand official IPO discovery attempts issuer-matched NSE/BSE issue sources and linked documents; generic page shells, retrieval failures and unreadable documents are not evidence of non-publication. Required unresolved terms remain fail-closed, without invented values or a manual-entry workaround for discovery defects.
- v1.5 remains the active scoring configuration. v1.6 is inactive; this README does not authorize its activation or any scoring change.
- This repository intentionally does not add authentication/RBAC, multi-user support, PostgreSQL, enterprise architecture, or production deployment requirements.

See [`docs/RUNBOOK.md`](docs/RUNBOOK.md) for CLI, persistence, replay, and analytical workflows. The current personal-use operating boundary is recorded in [`handoff/decisions/A16-personal-use-operating-scope-and-gate-disposition.md`](handoff/decisions/A16-personal-use-operating-scope-and-gate-disposition.md).
