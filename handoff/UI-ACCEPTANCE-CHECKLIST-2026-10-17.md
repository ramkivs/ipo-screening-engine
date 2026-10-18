# UI Acceptance Checklist — Post-7 October Work (2026-10-17)

Additive handoff artifact for the tracker reconciliation (R-21). It is not a tracker. Every item's status starts **NOT VERIFIED** unless actual user-supplied UI evidence already exists (noted per item); Arena cannot access the Windows checkout, browser, or localhost server and has marked nothing passed on the user's behalf.

## 0. Windows checkout verification (do this first)

Repository: `https://github.com/ramkivs/ipo-screening-engine.git` · Branch: `arena/5dd3fe52-ipo-screening-engine` · **Target SHA: see the reconciliation commit on that branch (the commit adding this file's tracker register R-21); feature tip before it: `2087fd37ea1878b4659e6b8428cd47c6fb5581b8`.** Authoritative tracker: `handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md`. Published baseline branch (PR #6 base): `arena/573e69a4-ipo-screening-engine` at `6f54b3722532c2153e07d9a2cea59696fdd11def`.

```powershell
cd G:\ipo-screening-engine\ipo-screening-engine
git status --short --branch          # note any local modifications FIRST; preserve them
git fetch origin
git rev-parse --abbrev-ref HEAD      # expect arena/5dd3fe52-ipo-screening-engine
git rev-parse HEAD                   # compare with the target SHA above
git log --oneline -1                 # expect the reconciliation commit
git status --short                   # working tree state; do NOT reset/clean
```

If `HEAD` is behind the target and the tree is clean: `git pull origin arena/5dd3fe52-ipo-screening-engine`. If there are uncommitted changes, review them (`git diff`) and pull only after they are stashed/committed by your own decision — nothing in this handoff authorizes discarding them. If `HEAD` differs from both the target and its ancestors, stop and report the SHA — do not force anything.

**Server (fresh start so the new code and env are actually loaded):**

```powershell
$env:PYTHONPATH = "engine"
$env:IPO_PROSPECTUS_URLS = '{"VISHAL-NIRMITI-LIMITED":"https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"}'
python -m uvicorn ipo_screening.presentation.api:app --host 127.0.0.1 --port 8000
```

UI routes used below (same-origin, hash routing): `#ingest` (upload), `#evaluations/<evaluation_id>` (scorecard), `#evidence/<evaluation_id>` (Evidence & Provenance Explorer), `#ipos/<ipo_id>`, `#directory`, `#dashboard`. API prefix `/api/v1`.

---

## A. Ready for local UI verification (no external dependency beyond the configured Vishal prospectus URL)

### A1 — Vishal derived-evidence cards + stale-duplicate correction (R-18/R-19) — **NOT VERIFIED**
- **Prerequisites:** server above; filing `handoff/reference/U01122MH1994PLC185445-vishal nirmiti.pdf`.
- **Action:** `#ingest` → upload the Vishal RHP (final mode) → open the resulting evaluation → `#evidence/<evaluation_id>`.
- **Pass criteria:** a **new** evaluation ID is created (not the pre-fix duplicate); Explorer shows 27 citations including `EV-issue.fresh_shares` 6590909 (DERIVED), `EV-issue.ofs` 3300.0 (DERIVED, formula note, no quotation), `EV-issue.ofs_sellers[0].shares_sold` 1500000 (FILING), `EV-issue.post_issue_shares` 26390909 and `EV-issue.post_issue_eps` 9.46 (DERIVED); `EV-issue-fresh_issue` 14500 (FILING); price band/lot `OFFICIAL_VERIFIED` from `SRC-PROSPECTUS-…`. The older evaluation still exists unchanged in history.
- **Edge behaviour:** re-uploading again returns the same (new) evaluation as duplicate. If a 422 appears, read "Official-source resolution diagnostics" and report that line.
- **Support:** `tests/test_derived_evidence_registration.py`, `frontend/test/evidence-inspector.test.js`.

### A2 — Seller-list inspector provenance (R-17/R-18) — **user evidence exists; re-confirm on the A1 record**
- **Action:** in the A1 Explorer, open `EV-issue-ofs_sellers` inspector.
- **Pass criteria:** Provenance Classification reads `SOURCE EVIDENCE (Extracted from Filing)` (never `UNKNOWN / UNVERIFIED`), seller name in the value summary, recorded quote present, `verification` FILING. Genuinely empty evidence (none here) is the only UNKNOWN case.

### A3 — Duplicate/idempotency sanity (R-19)
- **Action:** upload the same Vishal RHP a second time.
- **Pass criteria:** returns the A1 evaluation as duplicate (same ID, `is_duplicate`), no new record; history unchanged.

### A4 — Manual issue-term entry (Step 5, R-12; four-field scope 2026-10-18) — **user-exercised; re-confirm boundaries**
- **Prerequisites:** server *without* the prospectus URL configured (separate run) to force the unresolved path, or use Jio (Section C).
- **Action:** upload a terms-placeholder RHP → in the AWAITING panel enter **all four terms** (price-band floor/cap, lot size, **OFS amount in the filing's reporting unit** — ₹ lakh for the Vishal RHP) + explanation → submit. Also try submitting only three terms first.
- **Pass criteria:** all four inputs are offered; a three-term submission still blocks on `missing: issue.ofs` (nothing defaulted); a complete four-field submission is evaluated and persisted with every value labelled `MANUAL_ENTRY` (never verified) and the exact values shown in the result panel; conflicts with existing/verified values block until confirmed and never displace verified official values; nothing persisted on any AWAITING outcome. Manual completion preserves the official-discovery outcome (stays UNAVAILABLE) — manual input is not official verification.

### A5 — Filing-disclosed terms without resolver (RK precedent)
- **Data:** `handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf`.
- **Action:** upload via `#ingest` with no issue-term env configured.
- **Pass criteria:** evaluation produced directly from the filing (terms FILING), `issue_terms` report absent/`null`; no external configuration needed.

## B. Automated evidence only — no browser acceptance yet

| Item | Capability | Where | Support |
|---|---|---|---|
| B1 | Cross-IPO provenance & canonical reconciliation (R-07), D-PEER-1 empty peers (R-08) | scorecard `#evaluations/<id>`, peers display UNKNOWN-not-negative | `tests/test_cross_ipo_issue_term_provenance.py`, RK suite |
| B2 | Workstream 2 value summaries / processing-vs-quote distinction (R-09) | `#evidence/<id>` cards + inspector | `tests/test_workstream2_evidence_presentation.py` |
| B3 | Market-data persisted block states — missing ≠ negative (R-10) | scorecard market section | frontend tests (`test/*.test.js`, 68) |
| B4 | Runtime diagnostics completeness (R-17): config-error / retrieval / REJECTED / PARTIAL / assembly states each named in `resolution.providers` | 422 body + AWAITING panel diagnostics list | `tests/test_issue_terms_runtime_path.py`, `frontend/test/ingest.test.js` |
| B5 | Evidence-content duplicate identity (R-19, beyond A3) | — | stale-artifact regression in `tests/test_derived_evidence_registration.py` |

## C. Requires external publication / genuine data

### C1 — Jio completion (R-20) — **BLOCKED (external)**
- **Waiting on:** genuine official Jio **final Prospectus** on SEBI/NSE/BSE (price band announcement expected around the Oct 21, 2026 opening; final Prospectus around/after the Oct 23 close). The SEBI-hosted **RHP** already supplied is the same placeholder document — do not configure it as a Prospectus.
- **Then:** `$env:IPO_PROSPECTUS_URLS = '{"JIO-PLATFORMS-LIMITED":"<official final-Prospectus URL>"}'`, restart, upload the Jio RHP.
- **Pass criteria:** evaluation produced; identity `JIO PLATFORMS LIMITED`; `issue.ofs` 0.0 (FILING), dates + 270,000,000 shares (FILING); price band/lot and fresh-issue amount `OFFICIAL_VERIFIED` from `SRC-PROSPECTUS-…`; no manual entry used.
- **Until then:** upload yields `AWAITING_ISSUE_TERMS` naming exactly the three pricing terms — that is the correct visible result, not a failure of this checklist.

### C2 — Live official retrieval generally (R-05/R-14)
- Any issuer using `IPO_PROSPECTUS_URLS` / `IPO_PRICE_BAND_NOTICE_URLS` performs a real Windows-side HTTPS retrieval; Arena cannot exercise SEBI/NSE/BSE egress. A1 exercises this for Vishal.

## D. Incomplete / blocked (unchanged registers)

- R7-E1 GMP re-capture (time-boxed to the 19 Oct 2026 Tonbo close), A8-G-QUAL, A8-M (NIFTY), A8-S/A10 (subscription/GraphLogic PDF), A8-P/A5 (peers calibration), A8-X (VIX/listing/anchor), PW-02 (v1.6 activation decision), PW-03 (GCP sign-off) — evidence/decision-blocked as registered in the tracker; no UI acceptance is meaningful until their evidence exists.
- Seller `pre_issue_shares` separation (R-16 limitation) — requires a schema decision; do not accept any UI representation that implies it is independently established.
- PR #6 merge and any `main`/release action — not authorized; UI acceptance above does not imply merge acceptance.
