# Jio RHP explicit OFS “Not applicable” — split-header extraction correction — 2026-10-22

**Status:** implemented, tested and published only after the focused and full validation
gates passed. **Not validated against the user's live Windows process**: the failed
ingestion was not retried, no Windows data was altered, and the original PDF was not
modified.

**Baseline:** `75df573e96a8499ad06865cf5cd29e4da244ade7` (parent and tested runtime
`ba7a0694db4714d0f6a53ef1aad48a28330675ca`).

## 1. Confirmed failure

The repository PDF is byte-identical to the PDF identified in the Windows evidence:

```
evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf
sha256 72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d
```

Extracting its **page 1 native text with pypdf 6.19.0** (Linux sandbox, Python 3.11.2; the supplied Windows evidence used Python 3.14.3) reproduces the supplied cover
layout, including:

```text
FRESH ISSUE 
SIZE 
OFFER FOR 
SALE SIZE 
TOTAL ISSUE 
SIZE ELIGIBILITY AND SHARE RESERVATION 
...
Fresh Issue Up to  
270,000,000 
...
aggregating up to 
₹[●] million 
Not applicable Up to 
270,000,000 
...
```

Running the release matcher on that text produced **zero regular-expression
candidates** and returned `None`. The root cause is therefore **not** the following
`Not applicable` line break, the 32-line lookahead, or a binding-guard rejection:
the label itself never matched.

`_OFS_NIL_PATTERN` required **literal spaces** between `offer`, `for` and `sale`.
The real extractor emits `OFFER FOR \nSALE SIZE`, so:

1. no `match` was created;
2. no `quote`/candidate reached the amount, bare-label or previous-line guards;
3. `_find_ofs_nil` returned `None` without an OFS extraction.

The previous positive Jio test authored the header on **one physical line**
(`TYPE FRESH ISSUE SIZE OFFER FOR SALE SIZE …`), so it did not reproduce the
two-line header produced by the real PDF reader. That test's pass was not evidence
that the real cover matched.

The same helper is imported by `official_offer_amounts.explicit_amounts`, which
passes reconstructed `"Offer for Sale\n" + cell text` input. The label correction
therefore also aligns that path, but no table-geometry rule, official-source
authority, OCR behaviour or verification state was changed.

## 2. Smallest correction

`engine/ipo_screening/extraction/sections.py` only:

- label identification now uses `offer\s+for\s+sale(?:\s+size)?`, allowing the
  reader's line wrap/multiple spaces while still requiring the complete label;
- the named `label` group marks where the label ends, so the existing
  monetary/quantity guard examines text **after the complete label** rather than
  only the quote's first physical line. Without this, `SALE SIZE Rs. 712.13 crore`
  could have hidden an amount on a wrapped label line;
- the existing bare-label guard (the NIL is that label's value) and previous-line
  guard are retained unchanged;
- one additional check rejects the **wrapped equivalents** of the same competing
  structural labels (`Fresh\nIssue`, `Promoter\nGroup`, `Total Issue\nSize`,
  `Eligible\nRIL\nShareholder\nReservation`, etc.) when they are the lines
  immediately before the NIL. Up to four preceding lines are joined for this check;
  unrelated intervening text still prevents binding.

No fresh-issue-only inference, amount repair, tolerance for a missing NIL token,
schema/scoring/golden/config change, or weaker evidence state was introduced.

Original source blob: `375ea084291fdb133a39693e82b3c391fcab131e`.
Corrected source SHA-256: `0a59b200fa13bedb59cd350126354c4eeea008eacdcc6318549371fd86f81e27`.

## 3. Regression evidence

`tests/fixtures/jio/cover-page-pypdf-6.19.0.txt` (5,595 bytes, SHA-256
`45cc8790a6e6e7cf992352232279b96238285001fa690baa2b3d8cd4069cc503`) is the
**actual first-page native text captured from the unchanged repository PDF with
pypdf 6.19.0**. It is committed so the observed reader output is reproducible
without a PDF-parser version dependency. The PDF itself is unmodified.

`tests/test_ofs_nil_binding.py` now covers:

- the captured real layout: candidate found, quotation ends `Not applicable`,
  `issue.ofs` is `0.0`, sellers remain `[]`;
- a captured text with the explicit declaration removed: `None`, and **no**
  `issue.ofs` extraction (fresh issue alone never establishes zero);
- split-label same-line monetary/quantity cases remain non-NIL;
- split OFS label followed by Fresh Issue / Pre-IPO / Promoter / reservation /
  total-issue NILs (inline and on the previous line), including wrapped competing
  labels, remains rejected;
- the existing 32-newline bound is not extended.

`tests/test_jio_rhp_issue_terms.py` adds an integration regression that:

1. verifies the source PDF SHA-256;
2. runs the real `DocumentExtractor` on that PDF with only page 1 replaced by the
   captured 6.19.0 text (a controlled replay, not a live ingestion);
3. asserts `RawExtraction` value `0.0` and the explicit quotation;
4. asserts the canonical evidence carries the same quotation and empty sellers;
5. asserts the required-term gate reports missing `fresh_issue` (and other genuine
   placeholders) but **not** `ofs`, with no evaluation artifact;
6. completes through the existing controlled Prospectus provider seam and asserts
   persisted canonical `ofs == 0.0`, `EV-issue-ofs` = `0.0`/`FILING` with the same
   quote, a filing-origin activity event `value = 0.0`, and stored hash verification;
7. uses no public-source request, aggregator OFS inference or manual OFS entry.

## 4. Validation results

Executed in the Linux sandbox with Python 3.11.2 and repository `requirements.txt`
(pypdf 6.20.1); the 6.19.0 reproduction used a separate read-only `--target`
installation. The captured fixture, not the live parser version, is what the
regression asserts.

| Gate | Result |
|---|---|
| Focused: OFS binding, Jio RHP, offer-table boundaries, ingestion activity/lifecycle, issue-term multisource, aggregator | **151 passed, 0 failed, 3 warnings, 82.22 s** |
| OFS binding module after final additions | **14 passed** |
| Full backend suite (`python -m pytest tests/ -q`) | **1481 passed, 0 failed, 0 skipped, 0 xfailed, 25 warnings, 1489.13 s, exit 0** |
| `check-config` | `valid True`, 10 profiles resolved, each 100 points |
| Frontend Node tests | 93 passed, 0 failed |
| `git diff --check` | clean |

The full suite includes the frozen-core hash checks and golden evaluation result;
neither was re-baselined. No test was skipped, xfailed or weakened.

## 5. Explicit-OFS zero preservation — confirmed through code and regression

- `SectionExtractor.extract_cover_and_offer` emits `issue.ofs = 0.0` only from the
  matched explicit NIL quotation; the quote is retained.
- `CanonicalInputBuilder` returns candidate zero directly (`_get_field`/`_pick_issue`);
  the upload path supplies no reference-base field that could override it.
- Required-term readiness uses `is None`, and the canonical schema allows
  numeric zero with minimum 0.
- `EV-issue-ofs` records value `0.0`, `FILING` verification, the explicit quote and
  the filing source hash.
- The activity record emits a filing-origin field event with value `0.0`.
- The persisted input snapshot and evaluation hash verification were asserted in
  the new integration test.

No zero is derived from the fresh issue, total issue, seller list or a placeholder.

## 6. Official-discovery OCR — investigated separately, no change

Repository facts, kept distinct from the confirmed uploaded-PDF matcher defect:

- OCR is used only by `official_notice_ocr.parse_if_scanned` for an official notice
  with **no sampled native page of at least 50 characters**; a native-text RHP
  (including this Jio RHP) correctly bypasses OCR.
- The child uses `sys.executable -m ipo_screening.extraction.official_notice_ocr`
  with a bounded budget (180–270 s), at most six pages, bundled model paths, no
  network download; timeout/child failure raises and no partial payload is parsed.
- Retained historical evidence records three successful newspaper OCR runs in the
  final runtime; it does not establish an OCR failure in the failed ingestion.

No OCR code was changed. The failed ingestion's server log lines beginning
`Official OCR timeout` or `Official OCR child failed` (including the document
SHA-256, interpreter and child traceback) are the discriminating evidence. The
repository alone cannot establish that an OCR failure occurred, and this correction
does not claim one.

## 7. Authority and limits

- Routine personal-use implementation/test/publish is authorised by A16; scoring,
  thresholds, knockouts, taxonomy, canonical schema, configuration and golden
  history are unchanged.
- The actual PDF was neither modified nor re-uploaded. The user's live ingestion
  was not retried and no local Windows data was changed.
- The fix is proven against the **same PDF bytes** and the **reproduced 6.19.0 cover
  text**. It is not proof that the user's live process reloads the corrected module;
  that requires a normal restart/retry by the operator.
- Official-source authority remains unchanged: the explicit NIL establishes OFS
  zero; the monetary fresh-issue placeholder remains unresolved unless a qualifying
  official document states it.
