# G-3 — the fail-closed fixture-default safeguard: disposition and correction (2026-10-28)

- **Repository:** `ramkivs/ipo-screening-engine`
- **Starting `main`:** `4cc81a9f3f84656527fd2989d0d5965fbd3beede`
- **Raised by:** G-3 of `ARCHITECTURE-RECONCILIATION-2026-10-28.md`
- **Question:** *Should `validate_fail_closed_unknown()` be wired into a gate, and if so is its
  fixture-leak rule provenance-based (locator absence) rather than issuer-name-based?*

## Answer in one line

**Half refuted, half confirmed.** The rule is **not** dead code — it is invoked by
`validate_enrichment_contract()` — and the real leak vector is already closed at the builder,
so **no new production gate was justified**. But the `"VISHAL" in ipo_id` exemption was **live
logic** that decided a provenance question by issuer name, and `FORBIDDEN_FIXTURE_DEFAULTS`
declared five forbidden constants while only one was enforced. Both are now corrected.

---

## 1. Correcting the premise

The reconciliation recorded the validator as having "no caller". That was **wrong**, and the
error is worth naming: the search was `grep … engine/ --include=*.py | grep -v
enrichment_contract.py`, which excluded the very file containing the call site.

The actual chain is:

```
validate_fail_closed_unknown          enrichment_contract.py:414
  └── called by validate_enrichment_contract      :296
        └── called by enforce_enrichment_contract :306
              └── callers: tests only
enrichment_engine.py:64 imports validate_enrichment_contract — and never calls it.
```

So the rule **is** wired, at the enrichment-contract boundary. What is true is narrower and
more important: **that boundary is exercised only by tests.** No production ingest path
validates a supplemental enrichment document, and `EnrichmentEngine.assemble()` — the function
`PresentationService` actually calls — never invokes the contract validator.

## 2. Reachability: can a test-only default reach a real evaluation?

**No — and this is the fact that settles the "wire it in" part of G-3.**

| Vector | Status | Evidence |
|---|---|---|
| Builder synthesising 208/220/68/9.46/85.33 | **closed** | `CanonicalInputBuilder.__init__(allow_fixture_fallbacks: bool = False)`; every constant is `X if self.allow_fixture_fallbacks else None` |
| Extractor enabling it by default | **closed** | `DocumentExtractor.extract_from_pdf(..., allow_fixture_fallbacks: bool = False)` |
| Production ingest enabling it | **closed** | `PresentationService._ingest_document_impl` contains the literal `allow_fixture_fallbacks=False` |
| `supplemental=` passed in production | **never** | both `assemble()` calls in `service.py` pass only `base_input`, `price_band_notice`, `mode`, `partial_issue_terms` |
| A locator-less notice value reaching canonical evidence | **labelled, not silently trusted** | `_resolve_pricing_field` synthesises a locator (`"Price Band Notice, '<field>'"`), so the value is never presented as provenance-free |

`allow_fixture_fallbacks=True` appears in **tests only** (`test_extraction_phase5b.py`,
`test_vishal_historical_reconciliation.py`, and Test C of `test_fixture_fallback_isolation.py`,
which pins the flag as backward-compatibility behaviour).

**Equivalent protection therefore exists**, and a dedicated module already pins it:
`tests/test_fixture_fallback_isolation.py` Tests A–H. Per the standing rule — *if equivalent
protection already exists, document and test that fact instead of adding redundant validation* —
**no production gate was wired.** Doing so would have been a behaviour change on the ingest
path with no defect to justify it, and would risk rejecting legitimate enrichment documents.

## 3. What was genuinely wrong (confirmed)

### 3.1 The issuer-name exemption was live, not dead

The rule was `val == 220 and not loc`, guarded by `not is_vishal`. Executed against otherwise
identical payloads:

```
A. 220 WITH locator,    ipo_id=VISHAL  → []                                (correct)
B. 220 WITHOUT locator, ipo_id=VISHAL  → []            ← EXEMPTION SUPPRESSED IT
C. 220 WITHOUT locator, ipo_id=PARAS   → SUSPICIOUS_FIXTURE_DEFAULT_PRICE
D. 220 WITHOUT locator, no ipo_id      → SUSPICIOUS_FIXTURE_DEFAULT_PRICE
```

B versus C/D is the defect: the **same** locator-less value was silently allowed for one issuer
and reported for every other. A provenance question was being answered by a name. It was the
only issuer-specific branch in `engine/` outside fixture definitions, and it contradicts the
standing constraint that an issuer-naming exemption must not substitute for provenance.

The exemption was also **pointless for its apparent purpose**: the suite's reference payload
carries `locator: "Page 1, 'Offer Details' Table, Row 2"`, so condition A already passes
without it.

### 3.2 Declared coverage exceeded implemented coverage

`FORBIDDEN_FIXTURE_DEFAULTS` declares five entries; the implementation consulted none of them
and hard-coded `220`. `price_band_low` (208) and `lot_size` (68) were declared forbidden and
never checked.

Of the five, only three are adjudicable by a locator rule:

| Entry | Adjudicable here? | Why |
|---|---|---|
| `price_band.price_band_low` = 208 | **yes** | source fact (`$defs.provenanceValue`, carries `locator`) |
| `price_band.price_band_high` = 220 | **yes** | same |
| `price_band.lot_size` = 68 | **yes** | same |
| `derived.post_issue_eps` = 9.46 | **no** | `$defs.derivedValue` requires `is_derived`/`formula`/`dependencies` and has **no** `locator` field; "no locator" is its correct shape, so flagging it would mark every honest derivation suspicious |
| `business.top5_customer_pct` = 85.33 | **no** | the enrichment artifact has no `business` block; the path cannot occur |

### 3.3 The rule had no test at all

`SUSPICIOUS_FIXTURE_DEFAULT_PRICE` was referenced by **zero** tests, so the safeguard's only
observable behaviour was unverified.

## 4. The correction

`engine/ipo_screening/enrichment_contract.py::validate_fail_closed_unknown`:

1. **Issuer-name exemption removed.** The rule is now purely provenance-based:
   flag only when the value equals a declared constant **and** no `locator` is present.
2. **Coverage driven by `FORBIDDEN_FIXTURE_DEFAULTS`**, restricted to the source-fact
   `price_band.*` entries (`_FIXTURE_CHECKED_PREFIX`), so declared and implemented coverage
   cannot drift apart again. The two non-adjudicable entries are excluded **with the reason in
   the source**.
3. **Both value slots checked** (`raw_value` and `normalized_value`), since a leak may populate
   either.
4. Finding code generalised to `SUSPICIOUS_FIXTURE_DEFAULT_VALUE`; no consumer referenced the
   old code. Severity stays **WARNING**, so no document is rejected by this rule and the
   enrichment schema's own ERROR gate is untouched.

**No scoring, threshold, weight, penalty, knockout, config, schema, canonical-field or
`derived.py` behaviour changed.** The corrected function is on no production path, and the
golden result hash is unmoved.

### Authority

Within existing authority: this is the smallest correction to a demonstrated defect in a
provenance check, in an artifact whose declared contract (`FORBIDDEN_FIXTURE_DEFAULTS`) already
specified the intended coverage. It redefines no field, decides no policy question, and changes
no evaluation outcome. **Remaining governance item: see §7.**

## 5. Verification

| Check | Result |
|---|---|
| New module `test_fail_closed_fixture_safeguard_20261028.py` | **23 passed** |
| `test_enrichment_contract` (13) + `test_price_band_notice` (20) + `test_enrichment_engine` (15) | **48 passed** |
| `test_fixture_fallback_isolation` (Tests A–H) | **8 passed** |
| Combined focused run incl. tier gate | **80 passed** |
| Scoring / UNKNOWN / knockout / A33-A34 / golden battery | **199 passed** |
| **Full suite** (`pytest tests/ -q`) | **2232 passed, 0 failed, 0 skipped** (1505.7 s) |
| Integrity | 4 schemas valid; `verify_frozen_core()` True; `verify_golden_result()` True; `verify_v1_6_implementation()` PASS; `compileall` (engine, tests) clean |

Proven in the new module: the check is reachable through `validate_enrichment_contract` and
`enforce_enrichment_contract` (not merely callable directly); the builder default is `False` and
synthesises nothing; the locator-less value is flagged for **four** different `ipo_id` values
including `""` and `VISHALWAVE-…`; located values pass for **every** issuer; all three
source-fact constants are enforced; the two exclusions are asserted with their reason; non-fixture
values and absent blocks are silent; the golden result hash, base/final/unknown, bound
arithmetic and K1/K2/K4 states are unchanged.

### 5.1 One pin moved, and it moved honestly

Editing `enrichment_contract.py` makes it diverge from the 2026-10-23 published
fingerprint, so `test_jio_current_engine_result_20261027.py::test_published_record_engine_diverges_from_main`
failed: its expected divergence set no longer matched. That pin exists to record
**exactly which engine files differ** from the tree that produced the stale 34.0
record, so the correct response is to add the file, not to weaken the assertion.

Updated: the set gains `engine/ipo_screening/enrichment_contract.py` and the count
goes 20 → 21, with the reason in a comment. The assertion is unchanged in
strictness (`divergent == DIVERGENT_ENGINE_FILES`); only the recorded fact moved.
The Jio result itself is unaffected — the changed function is on no production
path.

## 6. What was deliberately not done

- **No production gate was wired.** §2 shows the leak vector is closed at the builder and the
  enrichment contract is not on the ingest path; wiring it would be an unjustified behaviour
  change.
- **`derived.post_issue_eps` was not forced into a locator rule.** Its contract has no locator;
  doing so would misrepresent derived values.
- **`business.top5_customer_pct` was not invented into the artifact.** The block does not exist.
- **The enrichment schema was not tightened** to require `locator`. That would fail closed on
  legitimate documents and is a schema/semantic change needing its own authority.

## 7. Remaining governance question

**G-3a — the only part of G-3 that is not resolved by evidence:**

> Should the supplemental-enrichment contract be *enforced* on a production ingest path at all —
> that is, should `EnrichmentEngine.assemble()` validate its `supplemental`/`price_band_notice`
> input against the contract before use?

- **Current status:** not enforced; the contract is a test-suite validator only.
- **Why not decided here:** enforcement would change ingest behaviour and could reject documents
  that are currently accepted. It is not required by any demonstrated defect — §2 shows no
  fixture default can reach an evaluation — so it is a policy choice, not a bug fix.
- **Dependency / what would resolve it:** a decision from the contract owner; evidence would be a
  production enrichment document that the contract rejects while the engine would otherwise
  accept it. **No such specimen exists in the retained corpus.**
- **Independent work completed meanwhile:** the rule itself is now provenance-based, fully
  covered, and free of the issuer-name exemption — so it is correct and safe whenever it is
  eventually enforced.
