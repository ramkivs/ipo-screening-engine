# CI remediation — peer staleness made two API tests wall-clock dependent

- **Date:** 2026-10-28
- **PR:** #13 (`arena/342ccacc-ipo-screening-engine`)
- **Head at diagnosis:** `ee287d0c` (A33/A34 approved decisions + implementation)
- **Failing CI run:** [40635332696](https://github.com/ramkivs/ipo-screening-engine/actions/runs/40635332696) — 2 failed / 2200
- **Change class:** test-only. **No engine, config, schema, scoring or policy file changed.**

## 1. The two failures

| Test | Expected | Observed |
|---|---|---|
| `test_peer_row_mapping_and_bounds.py::test_valid_peer_ingestion_reaches_a_scored_valuation` | `peer_snapshot.valid_count == 1` | `0` |
| `test_ui7_ingestion.py::test_ingest_rk_fashion_accessories_real_statutory_filing` | `final_score == 43.0` (base 46.0, completeness 66%) | `35.0` (base 38.0, completeness 54%) |

## 2. Independence from A33/A34

Both failures reproduce **identically on the previous PR head `89523bc`**, checked in a
clean detached worktree of that commit. `ee287d0c` changes only the Regulation 17(1)(c)
early-unlock reader and documentation, and touches neither `snapshots.py`,
`pipeline.py`, peer extraction, nor the peer threshold. The A33/A34 work is not the
cause and its semantics are untouched.

## 3. Root cause — one shared mechanism

`pipeline.evaluate` resolves the evaluation instant as:

```python
moment = evaluation_datetime or datetime.now(timezone.utc)   # pipeline.py:271
```

Peer freshness is `evaluation instant − peer.as_of` compared with
`thresholds.peer_staleness_days = 30` (`config/ipo-config.v1.5.0.json`).
Neither `PresentationService.ingest_document` nor the `/api/v1/ingest/*` endpoints
accept an `evaluation_datetime`, so every API-driven test inherits **today's date**.

Both failing tests carry peers dated `2026-09-28`:

- the peer test's `_peer(...)` fixture literal, and
- RK Fashion's real peer table — `Banaras Beads Limited`, `as_of: 2026-09-28`, parsed
  from the filing by `sections.py` and already asserted in
  `test_rk_fashion_reconciliation.py:122`.

`2026-09-28 + 30 days = 2026-10-28`. The boundary was crossed **on the day of the run**:

```
eval=2026-10-27T12:00:00Z  age_days=29.5000  status=VALID  valid_count=1
eval=2026-10-28T04:59:02Z  age_days=30.2077  status=STALE  valid_count=0
```

RK, same extraction, only the evaluation instant varied:

```
pinned 2026-10-05 -> final 43.0  base 46.0  complete 66.0   (matches the assertion)
pinned 2026-10-20 -> final 43.0  base 46.0  complete 66.0
now    2026-10-28 -> final 35.0  base 38.0  complete 54.0
                     pe_vs_peers + second_multiple flip to UNKNOWN
```

The green run at `89523bc` on 2026-10-27T17:09Z is the same arithmetic one day earlier.

## 4. Decision — pin the instant, do not move the policy

The engine behaviour is **correct**: a peer multiple more than 30 days old must not be
scored. The defect is in the tests, which asserted a verdict that depended on the
calendar rather than on the filing.

Rejected alternatives, and why:

- **Raise `peer_staleness_days` / relax the threshold** — weakens a live policy to make
  a test pass. Rejected.
- **Re-date the RK peer or the `_peer` fixture to "recent"** — the RK date is printed by
  the filing and asserted elsewhere; fabricating a fresher date would misrepresent the
  document and break `test_rk_fashion_reconciliation`.
- **Change expected scores from 43.0 to 35.0** — hard-codes today's accident as the
  expectation and would break again on the next boundary. Rejected.
- **Add a production time seam to the API** — production has no defect here; no
  production surface was added.

## 5. The correction

`tests/conftest.py` gains `FrozenEvaluationClock` (a `datetime` subclass whose
`now()`/`utcnow()` return the suite's canonical instant `EVAL_AT`) and the
`pinned_evaluation_clock` fixture, which `monkeypatch`es
`ipo_screening.pipeline.datetime`. This is the API-path equivalent of the
`evaluation_datetime=EVAL_AT` that the rest of the suite already passes explicitly —
the repository's existing determinism convention, extended to the one path that had no
argument for it.

Applied to the two failing tests only. New coverage,
`test_peer_freshness_follows_the_evaluation_instant`, asserts the same peer is
`VALID` at `EVAL_AT` and `STALE` 24 days later, so the policy is demonstrated to be
intact and any future attempt to green these tests by relaxing staleness fails.

## 6. Verification

- Both previously failing tests: **2 passed**.
- Affected modules (`test_peer_row_mapping_and_bounds`, `test_ui7_ingestion`,
  `test_rk_fashion_reconciliation`, `test_d_peer_1_no_synthetic_peers`): **56 passed**.
- A33/A34 and related focused modules: **101 passed**.
- Tier gate: **1 passed**. Integrity: schemas PASS, frozen core `True`, golden result
  `True`, v1.6 implementation `PASS`. `compileall` OK.
- **Full suite:** `2201 passed` — 2198 prior passes, plus the 2 repaired tests, plus the
  new regression test. 0 failed, 0 skipped.

## 7. Preserved

A33 Alternative A (provisional `kmp_exits_2y` counting rule) and A34 Alternative B
(carve-out alone is not an early unlock) are unchanged, as are their decision records,
the issuer reproduction evidence, and every scoring weight, threshold, penalty, knockout
and verdict rule.
