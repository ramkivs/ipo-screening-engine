# Backend test tiers and safe page-text reuse

## Commands

Run from the repository root with the dependencies in `requirements.txt`
installed (activate your virtual environment first):

```bash
# Fast PR/change checks: all fast tests, including the entire Pass-9 suite
PYTHONPATH=engine python -m pytest tests/ -q -m fast --strict-markers
npm --prefix frontend test

# Integration: real filings, API/service ingestion, provenance, persistence,
# idempotency, and mixed modules containing those workflows
PYTHONPATH=engine python -m pytest tests/ -q -m integration --durations=30

# Full/nightly/release: no exclusions; fast + integration
PYTHONPATH=engine python -m pytest tests/ -q --durations=30

# Explicit Pass-9 acceptance (no skips or deselections)
PYTHONPATH=engine python -m pytest -q \
  tests/test_aggregator_issue_terms.py \
  tests/test_issue_terms_cli.py \
  tests/test_paras_extraction_gaps_20261024.py

# Uncached control: same full coverage, without the opt-in optimization
PYTEST_PDF_TEXT_CACHE=0 PYTHONPATH=engine python -m pytest tests/ -q --durations=30
```

No marker filtering is applied by default. `slow` is now an alias for the
integration tier, **not** a claim that every individual case is expensive.
`tests/tier_inventory.py` explicitly lists conservative module-level integration
membership. Mixed modules stay together, including their inexpensive synthetic
cases: a fast command must not silently contain an expensive filing case.
The inventory guard flags new modules mentioning PDF or ingestion for review;
synthetic Pass-9 exceptions are explicit. Existing individual `slow` markers also
imply integration. Every collected case belongs to exactly one tier.

Fast is not a replacement for full release validation. The existing workflow's
mandatory/default `full` path and explicit `workflow_dispatch` full choice are
unchanged; its pre-existing focused linkage choice does not prove full-suite
acceptance. No CI failure handling, existing assertions, skips or production code changed.

## Optimization boundary

Eight audited modules opt into `cached_pdf_text`:

- `test_extraction.py`
- `test_step5_auditor_and_manual_terms.py`
- `test_ui7_ingestion.py`
- `test_official_discovery.py`
- `test_cross_ipo_issue_term_provenance.py`
- `test_rpt_extraction.py`
- `test_rk_fashion_reconciliation.py`
- `test_derived_evidence_registration.py`

Only `pypdf.PageObject.extract_text()`'s **default-call string result** is reused.
The process-local session cache keys by SHA-256 of the reader's complete actual
PDF bytes plus page object number/generation. The digest is computed once per
fresh reader. Upload filenames, paths, mtimes, and source IDs are not cache
identities. Non-default arguments, layout modes, and visitors bypass reuse;
exceptions are never cached. The function-scoped monkeypatch is undone between
tests. The cache can be disabled using the command above.

Every real `extract_from_pdf()` invocation still loads a fresh PDF reader and
performs source validation and hashing, TOC/section/financial extraction rules,
canonical construction and schema validation. The cache does not bypass API
issue-term resolution, evaluation, evidence registration or persistence: those
steps still execute whenever the original workflow gates permit them. Rejected
or awaiting-term requests retain their original no-evaluation/no-persistence
behavior. The cache shares no canonical dictionaries, reports, services,
resolvers, evaluation state or stores. Mutable
identical canonical construction was deliberately **not** memoized. No test or
assertion was deleted or consolidated; six isolation/inventory tests were added.

These opt-in modules do not mutate PDF pages/readers/streams or exercise pypdf
internals. Do **not** add such tests to them without disabling this fixture for
that test or moving it to an uncached module. A reader's bytes/pages must remain
immutable for its lifetime. Parser mutation, fallback isolation, notice-cache
invalidation and Windows retrieval suites remain outside this optimization.
The evidence-registration re-upload test changes registry behavior downstream of
page decoding; registry/evaluation/persistence always execute again. Its explicit
`monkeypatch.undo()` also removes the text wrapper before the subsequent uploads.

## Real-file safeguards

Uncached issuer/workflow coverage remains, including Vishal historical and
phase-5B extraction, R.K. fixture-fallback isolation, Jio evidence remediation,
and Paras upload/parser evidence regression. Within opted-in suites, cache misses
also perform real pypdf decoding, and all extraction rules rerun on each call.
Existing Vishal manual-term completion, R.K. API ingestion and Jio discovered
prospectus completion retain the genuine PDF → canonical → issue terms →
evaluation → persistence path. Paras's existing evidence suite deliberately does
not produce an official evaluation; its unchanged hash-checked parser/upload
boundary remains intact. No new issuer evaluation is represented as qualified
or official evidence. Full-suite coverage is retained, not replaced by synthetic
inputs. No Windows-local validation is performed.

## Integrity checks (also required for PR/release validation)

```bash
PYTHONPATH=engine python - <<'PY'
import json
from pathlib import Path
from jsonschema.validators import validator_for
from ipo_screening.post_listing.v16_implementation import (
    verify_frozen_core, verify_golden_result, verify_v1_6_implementation,
)
for path in Path('schema').glob('*.json'):
    schema = json.loads(path.read_text())
    validator_for(schema).check_schema(schema)
assert verify_frozen_core()[0]
assert verify_golden_result()[0]
report = verify_v1_6_implementation()
assert report['status'] == 'PASS', report
print('Schemas, frozen core, golden result and inactive v1.6: PASS')
PY
python -m compileall -q engine
git diff --check
```

Measured results and remaining limitations are recorded in
[TEST_PERFORMANCE_RESULTS.md](TEST_PERFORMANCE_RESULTS.md).
