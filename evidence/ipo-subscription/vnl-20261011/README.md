# VNL IPO Subscription Source Evidence

Status: NON-AUTHORITATIVE INVESTIGATION EVIDENCE

Issue:
- Company: Vishal Nirmiti Limited
- Symbol: VNL
- ISIN: INE1O5L01025
- Issue period: 30 September–5 October 2026
- Price band: INR 208–220
- Recorded offered/reserved quantity: 8,471,153 shares

## Captured observations

### NSE bid details
Source endpoint: /api/ipo-bid-details?symbol=VNL&series=EQ
Update time: 5 October 2026, 19:00:04
Total bids: 10,020,004
Cut-off bids: 5,970,264
Recorded SHA-256:
C61F4BCB90C13B4B99F1DEBDDEE60D5E3AC029B678C7B04FEEAE2EF02E091A64

### Consolidated active categories
Source endpoint: /api/ipo-active-category?symbol=VNL
Update time: 5 October 2026, 19:00:00
Total bids: 14,446,804
Cut-off bids: 8,955,260
Recorded SHA-256:
3F58B12EC21241D1CB63806686419EAFBC90EFBE6709F55EA360AE499ED86ACC

Do not double-count parent categories and their subcategories.

### All Exchange demand graph
Source endpoint: /api/ipo-detail?symbol=VNL
Response field: demandGraphALL
Update time: 5 October 2026, 19:00:00
Total bids: 14,471,488
Cut-off bids: 8,963,828

The NSE demand graph matches the separate NSE bid-details totals.

## Known limitation

The consolidated active-category figures and All Exchange demand graph differ by:
- 24,684 total bids
- 8,568 cut-off bids

The discrepancy is CLOSED WITH LIMITATION. Its cause and the exact scope of the All Exchange figures remain unverified.

Preserve each endpoint as a distinct observation. Do not average or combine the conflicting totals. Do not treat this discrepancy as a blocker for broader IPO subscription-source assessment.

The two captured chart-demand endpoints returned valid empty JSON arrays. Empty responses do not establish zero demand.

## Interpretation and authority

These files preserve public-source observations. This directory is not an authoritative data contract, source approval, implementation authorization, or production certification.

Subscription data must remain distinct from GMP.

The accompanying SHA256-MANIFEST.json records the hashes of the files published here. Its generated time is the manifest-generation time, not the original source-retrieval time.
