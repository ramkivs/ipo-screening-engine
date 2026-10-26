> **Integration closure, revision21 (2026-10-26):** PR #10 merged as`70c5b0facc20f718500bcddc1efaae778ebd78c5`,
> accepted source head9333b1c. Windows gate accepted by user decision: focused
> exit0; initial full1941passed/1CLI subprocess timeout; same test isolated pass
>98.51s. NOT a clean Windows full pass, and no rerun required. Historical OPEN
> statements below are superseded by tracker revision21 and the
> [verified remote closure receipt](https://github.com/ramkivs/ipo-screening-engine/pull/10#issuecomment-6409140261). Closure updates are docs-only;
> existing timing/validation receipts are preserved, not rewritten.

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
acceptance. Finalization adds a `pull_request` trigger targeting `main` because
this integration cannot dispatch workflows (HTTP 403) and the prior push trigger
names an older Arena branch. Pull requests execute the unchanged **full** job,
including frontend and integrity checks. No CI failure handling, existing
assertions, skips or production code changed.

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


## Publication and remote evidence

Published from `arena/cf756dd1-ipo-screening-engine` to
[PR #10](https://github.com/ramkivs/ipo-screening-engine/pull/10), based on
`dedb4b876cdc68bdf3023d9740dc13f6888b45b3`. The initial implementation and tracker
commit is `96cd9bd548b24b86caa1f89e2c0ab0a6cf509cd8`; its follow-up changes only
publication documentation/tracker and the two-line PR-trigger addition above.
The PR's **Checks** tab and final verification comment are the authoritative
remote CI/branch-state receipts; local benchmark timings are not GitHub runner
timings. Publication does not authorize or claim a merge, release or deployment.


The code/CI head `3ba28f6f67998cb6c9b6b1abf5f4fcf5b75ee502` passed
[full remote run 40194048213](https://github.com/ramkivs/ipo-screening-engine/actions/runs/40194048213):
1,914 tests, zero failures/errors/skips, 1,048.850s JUnit suite time. Frontend,
integrity, compileall and clean-tree steps passed. The results report records
runner notices and the unavailable bulk-log/pytest-warning-count limitation.
A documentation-only receipt follows that tested code head; its final SHA and
full-CI result are verified separately in the PR's final comment.

## Windows portability follow-up (2026-10-25; correctness, not a speed claim)

The user's Windows run at `dfa34b2` reported **1,907 passed, 7 failed, 57 warnings
in 26m42s**. The original `dedb4b8` comparison reran only those seven cases
(**7 failed**, 103.81s), not the full baseline. These are user-supplied Windows
results and are not interchangeable with Arena/Linux timings above. Windows
acceptance remains open until the unresolved R.K. extraction difference is
explained and a corrected Windows run is supplied.

### Environment and byte preservation

- Install the **complete** `requirements.txt` with the same interpreter that
  executes `python -m pytest`. Pillow is required by the OCR render-to-image
  runtime and imported directly by the image-only regression. It was already
  a transitive RapidOCR dependency; it is now pinned directly as
  `Pillow==13.0.0`. Missing `PIL` means that interpreter's installation is
  incomplete/mismatched, not a reason to skip OCR. No optional dependency group
  is declared in this repository.
- `.gitattributes` now protects only the InvestorGain retained transcription and
  the Paras issue-terms package's four Markdown captures with `-text`. Their
  original bytes and declared digests are **unchanged**. Actual Git checkout
  tests cover `core.autocrlf=true` and `input` using a private index/work tree;
  an unprotected control demonstrates that CRLF conversion is really active.
- Updating attributes does **not** repair a previously transformed working copy.
  Do not change manifests, regenerate expected hashes, run blanket renormalizing
  commands, or discard the user's `tests/gmp_mechanics_harness.py` edit. After
  capturing diagnostics, validate in a **separate fresh clone/directory** with
  the corrected attributes. That leaves the existing Windows checkout and its
  local harness edit untouched.
- The reproducibility test's child now opens the golden JSON explicitly as
  UTF-8; a second parameter forces CP1252 defaults inside the child while retaining
  all three hash seeds and the original equality assertions. The pre-correction
  child fails on byte `0x8f` at position 1843 under that emulation. This proves
  a portability defect, not the content of the still-missing original Windows
  traceback.

### Single read-only diagnostic needed from the failing Windows interpreter

After obtaining the correction without discarding local edits, run this **before
repairing the failing environment/capture bytes**, with the SAME Python used by
pytest (PowerShell):

```powershell
python tests/diagnose_windows_portability.py --full-extraction --output "$env:TEMP\ipo-windows-before-repair-18.json"
```

Choose a new filename if it already exists. Return that one JSON artifact. The
script reports interpreter/dependency versions and actual Pillow import, native
child encoding failure/stdout/stderr for the exact published original script,
actual versus declared capture hashes and CRLF fingerprints, R.K. PDF hash,
routing, extraction statuses, raw pages 125/126 and canonical capital fields.
It never installs dependencies, changes checkout files, patches parser/cache
state or writes an evaluation/store. Optional `--output` exclusively creates a
UTF-8 receipt **outside** the repository and refuses to overwrite an existing
file. The harness is only queried for Git status, never read or rewritten.

This artifact supplies the currently unavailable Windows facts: Paras's actual
checkout digest; the original reproducibility child exception under that native
interpreter; and the R.K. dependency/PDF/page-text differences. No parser or score
change is justified by the truncated failures alone.

After diagnostics, the required environment action in either a preserved
checkout or a separate fresh validation clone is:

```powershell
python -m pip install -r requirements.txt
python -m pip check
python -c "import sys, PIL, pypdf; print(sys.executable, PIL.__version__, pypdf.__version__)"
```

For clean byte-preservation validation, use a **new** destination, not a reset or
clean of the existing checkout:

```powershell
git -c core.autocrlf=true clone --single-branch --branch arena/cf756dd1-ipo-screening-engine https://github.com/ramkivs/ipo-screening-engine.git C:\path\to\NEW-ipo-portability-check
```

Create/install a separate virtual environment there using the existing README
instructions, then run the focused cases and documented full command. A fresh
clone does not contain the user's local harness edit: record that difference in
any full-suite comparison rather than discarding or silently copying the edit.
Do not copy the transformed captures into that clone. None of these Windows commands
has been executed or claimed as executed by Arena.
