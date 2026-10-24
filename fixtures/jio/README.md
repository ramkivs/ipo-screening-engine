# Jio historical reproduction fixture

`jio_canonical_2026-10-19_pre_evidence_remediation.json` is the canonical
input produced by the **pre-remediation** extractor (repository commit
`86d4950`) on the committed, non-authoritative Jio RHP
(`evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf`,
SHA-256 `72480c2e…1b6d`).

It is preserved so that the published 2026-10-19 Jio result — 29/100 for the
filing-established fresh-issue structure and 21/100 for the inverted
structure — remains reproducible after the evidence-remediation changes
(net-worth derivation, unit-correct post-issue EPS, source-dated peers and
Note 36 related-party extraction). The fixture is a historical reproduction
artifact, not authoritative source evidence and not a scoring input.

`tests/test_jio_score_bridge.py` evaluates this frozen input; the live
extractor's new output is pinned separately in
`tests/test_jio_evidence_remediation.py`.
