# A20 — K5 Contingent-Liability Numerator: Defined Section Total, Commitments Excluded

- **Decision ID:** A20 (decision **D-2** of the HD Fire / Jio decision set)
- **Title:** K5 numerator is the disclosed total of the contingent-liability section
- **Decision status:** RAMKI-APPROVED POLICY, with the narrow implementation authorized.
- **Decision authority:** RAMKI
- **Decision date:** 2026-10-20 (Asia/Calcutta); no decision time is asserted.
- **Authorization basis:** Ramki's direct 2026-10-20 instruction approving the D-2 recommendation: *"The intended numerator is the disclosed total for the defined contingent-liability section, excluding capital commitments unless the existing authoritative criterion contract explicitly includes them. Do not include capital commitments merely because they appear adjacent to contingent liabilities."* The same instruction authorizes the narrowest correction consistent with this definition and lists the required regression cases.
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline identity:** branch `arena/ae4d04e8-ipo-screening-engine` at remotely verified commit `7754f9b397696e72ab025eca964325aa074f2796`.
- **Scope:** `financials.contingent_liabilities` extraction and the K5 percentage leaf.
- **Implementation authority:** GRANTED for `_extract_contingent_liabilities` only. No threshold, criterion, schema or scoring change.
- **Publication status:** recorded in the authoritative tracker; the implementation commit is identified there.

## Decision

`financials.contingent_liabilities` is the **disclosed total of the defined contingent-liability
section** of the issuer's note, **excluding capital commitments**.

Operational rules:

1. **Section boundary.** The section is the body of the note whose heading matches
   `Contingent Liabilities (and Commitments)`, read to (a) an `(II) Commitments` subsection
   heading or (b) the next numbered note heading on the same page.
2. **Rows.** A row is a line that ends with amount cells; its label is the text accumulated
   above it and on the same line. Period headers, "As at" labels and subsection headings are
   never row labels.
3. **Column.** The latest fiscal-year column (`31 March`), never an interim (`30 June`) column;
   a row whose width does not match the header fails closed.
4. **Aggregate over constituents.** If the section carries exactly one `Total` row, that total
   is the numerator and the constituent rows are **not** added to it. More than one `Total` is
   ambiguous and fails closed.
5. **Sum.** Without a disclosed total, the section's rows are summed.
6. **Commitments excluded.** A commitment-labelled row (`commitments`, `capital account`,
   `contracts remaining`) and everything under a commitments subsection is excluded. A total
   row that itself says "commitments" is not a contingent-liability total.
7. **Completeness.** An unparseable/width-mismatched row, or an unquantified exposure with no
   disclosed total, leaves the amount **UNKNOWN**. A sum of the quantified rows is not treated
   as the section total.
8. **Unquantified flag.** Set `True` only on a positive unquantified statement in the same
   section; negated language leaves it `None`; it is never coerced to `False`.
9. **Threshold and structure unchanged.** K5 still fires when
   `contingent liabilities / net worth × 100 > 50` **or** the unquantified flag is true.

## Rationale

- The K5 label ("Contingent liabilities >50 % of net worth") and the field name refer to
  contingent liabilities, not to a single claims line. The previous extractor read only
  `claims / disputed liabilities`; a note that itemised guarantees, EPCG obligations or
  statutory demands returned either one narrow line or no amount at all.
- The schema entry is `$ref: num` with no description, so the definition existed only in code.
  This record makes it explicit without changing the schema.
- Commitments are contractual obligations disclosed alongside contingent liabilities under
  Schedule III / Ind AS 37; they are not contingent liabilities. Including them because they
  are adjacent would change the meaning of the ratio.
- Using a disclosed total when present avoids double counting an aggregate and its components.
- Measured effect of the definition on a controlled fixture with net worth 10,000: a note
  disclosing claims 1,000 and guarantees 5,850 gave K5 **CLEAR** under claims-only (10 %) and
  **TRIGGERED** under the section total (68.5 %). This is the materiality the definition can
  change; the threshold itself is untouched.

## Scope

- `engine/ipo_screening/extraction/financial_tables.py::_extract_contingent_liabilities`.
- Consumed by `builder.py` → canonical `financials.contingent_liabilities` →
  `derived.py::_contingent_liab_pct_networth` → K5.

## Explicit exclusions

- No change to the 50 % threshold, the `when.any` structure, the unquantified leg, or scoring.
- No schema change (the schema remains `$ref: num`; a description would be a protected-artifact
  change and is deferred).
- No treatment of collateral as an offset, and no netting of insured/secured exposures.
- No inference that a quantified section means every exposure is quantified.
- No hard-coded issuer values; no threshold relaxation or tightening.

## Implementation implications

The extractor now parses the whole section instead of one labelled row, classifies total /
constituent / commitment rows, right-aligns amount cells to the period columns, and returns
`None` on ambiguity. The unquantified flag is read from the same section with the existing
polarity guard. The function signature and the canonical field are unchanged.

The returned `quote` is the joined **row-label** text of the rows actually used (for Jio,
`Total contingent liabilities`) — the filer's own line wording, not a verbatim sentence and
not a page-level quotation. No new quotation, figure, note number or page is asserted by the
extraction.

## Verification evidence

| Check | Result |
|---|---|
| `tests/test_contingent_liabilities_extraction.py` | **17 passed** (29.50 s), including the live Jio pin |
| Cases covered | claims-only; guarantees/EPCG without a claims row; multiple categories; aggregate + constituents (no double count); commitments excluded; two totals; unquantified with and without a total; negated unquantified language; width mismatch; missing headers; next-note boundary; adjacent note with the same header |
| Live Jio (Note 37, p. 405) | **15,021** (claims), commitments 26,198 excluded, flag `None` ⇒ 0.45 % of net worth; K5 UNVERIFIED on the flag only |
| Controlled K5 runs | net worth 10,000: 1,000 ⇒ CLEAR (10 %); 6,850 ⇒ TRIGGERED (68.5 %); 5,000 (50.0 %) ⇒ CLEAR (`> 50` is strict); `None` + unquantified ⇒ TRIGGERED |
| Focused regression battery (11 files) | **153 passed** (344.58 s) |
| Full backend suite (`pytest tests -q`, final tree) | **1192 passed, 0 failed, 0 xfailed**, 38 warnings, 1566.58 s (baseline `7754f9b`: 1179 passed, 1 xfailed, 1542.57 s) |

## Deferred work

1. **Schema description** for `financials.contingent_liabilities` (protected artifact; requires
   a separate schema change).
2. **Notes longer than one following page:** the reader currently reads the heading page and
   the next page. A longer note may need more pages and an explicit continuation rule.
3. **Integer-only percentage/amount cells:** the row parser reads grouped (comma) or decimal
   amounts; a bare small integer is treated as unparseable rather than guessed.
4. **Collateral / overlapping exposures:** the decision deliberately does not net a guarantee
   against the security behind it. If a future rule nets exposures, it needs its own record.
5. **HD Fire's BG/EPCG:** whether they sit in the contingent-liability section or the
   commitments section cannot be established without the RHP.

## Limitations and unresolved blockers

- HD Fire's RHP and historical evaluation remain unavailable. The BG ₹58.50 cr and EPCG
  ₹31.43 cr are **unverified secondary values**; the 22.49 % arithmetic is not a verified K5
  input and is not used to clear or trigger anything.
- Jio's note carries one contingent-liability row, so the aggregate-versus-constituents rule
  does not change its value (15,021). The rule is exercised by synthetic notes and by the
  general row/section parser.
