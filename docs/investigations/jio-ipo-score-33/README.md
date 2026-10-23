# Jio Platforms IPO — Score 33/100 Recovery Evidence

Purpose: preserve the recovered API responses and evaluation artifacts for read-only, artifact-assisted root-cause reconciliation of the Jio Platforms IPO evaluation.

## Target evaluations

- Latest: `JIO-PLATFORMS-LIMITED-20261023-051816Z-final-b79b5794`
- Previous: `JIO-PLATFORMS-LIMITED-20261022-101913Z-final-ad5e6872`

## Contents

- `artifacts/<evaluation-id>/`: recovered JSON artifacts, including `evaluation-record.v1.json`, `evaluation.json`, `result.json`, `input.json`, `evidence.json`, `lifecycle.json`, `market.json`, `peers.json`, and `manifest.json`.
- `api-get-responses/<evaluation-id>/`: recovered API detail and evidence responses.
- `api-inventory.json`, `artifact-inventory.json`, `recovery-summary.json`, and original `README.txt`: original inventory and recovery metadata.
- `SHA256SUMS.txt`: SHA-256 hashes of all original recovered bundle files, using paths relative to this directory.

## Integrity and interpretation

The original 26 recovered files are copied byte-for-byte from `IPO-Evaluation-Recovery-20261023-115835.zip`. `SHA256SUMS.txt` is generated from those copied bytes. The added repository README is explanatory and is not part of the original recovery bundle.

These files are recovered runtime/API artifacts. Their presence does not by itself establish which source-code revision produced them. Any source/runtime correspondence must be independently verified or explicitly marked UNVERIFIED.

This directory is evidence-only. Do not edit or regenerate the recovered artifacts in place. Any later investigation report should be stored separately and should cite the exact artifact paths and fields.
