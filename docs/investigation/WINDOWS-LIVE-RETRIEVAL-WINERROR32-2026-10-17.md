# Live-path AWAITING_ISSUE_TERMS recurrence — root cause and fix, 2026-10-17

## Symptom (Windows, reported)

After checkout sync + restart, a fresh Vishal RHP upload in Final mode
returned `AWAITING_ISSUE_TERMS` with all four terms missing
(`price_band_low/high`, `lot_size`, `ofs`), "official sources could not
be retrieved or verified". All Linux-side tests passed throughout.

## Facts established

1. The configured official source **exists and is authentic**: the SEBI
   URL in `IPO_PROSPECTUS_URLS`
   (`sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf`) is
   Vishal Nirmiti's genuine final Prospectus dated October 05, 2026
   (independently fetched and read during this investigation: Fresh
   Offer 65,90,909 shares / ₹14,500.00 lakhs; OFS 15,00,000 /
   ₹3,300.00 lakhs; seller Vaman Prestressing Company Private Limited).
   Acceptance outcome B's precondition ("terms not published") is
   therefore **false** — the terms are published; the failure is in
   the application retrieval path, not in the world.
2. Configuration loading, issuer-key matching (slug-normalised),
   provider ordering, term parsing, OFS derivation and assembly are
   covered by passing tests and were re-verified.
3. Application-side live retrieval from the Arena sandbox is
   impossible (egress proxy closes TLS to sebi.gov.in:
   `URLError: TLS/SSL connection has been closed (EOF)`), so the
   Windows failure stage was established by code-path analysis plus
   mechanism-faithful automated reproduction, per the diagnostics
   design from `7588b42`.

## Root cause (Windows-only, demonstrated by mechanism test)

In `HttpNoticeProvider.find`, `HttpProspectusProvider.find` and
`NoticeSnapshotCache.get` (`engine/ipo_screening/issue_terms.py`), the
retrieved bytes were written to a `NamedTemporaryFile`, parsed via
pypdf — `pypdf.PdfReader(str(path))` keeps the file stream open and
nothing closes it — and the temp path was then unlinked in a
`finally` block. On Windows, unlinking a file that is still open
raises `PermissionError` [WinError 32]. An exception raised in
`finally` **replaces the successful result**, so a retrieved, genuine,
issuer-matched Prospectus was reported as REJECTED ("retrieved
document is not an established final Prospectus: [WinError 32]…") and
every term stayed missing. POSIX permits unlinking open files, which
is why the defect was invisible to the entire Linux test history.

Reproduction: `tests/test_issue_terms_windows_retrieval.py` makes
`Path.unlink` raise `PermissionError(32, …)` exactly as Windows does;
before the fix the prospectus parse is destroyed, after the fix the
candidate is FOUND. The same file proves the notice provider and the
snapshot cache survive the same condition.

Secondary retrieval weakness fixed in the same pass: the default
fetcher made a **single attempt** — any transient connection reset,
timeout or HTTP 429/5xx from the official document servers became a
permanent UNAVAILABLE. It now retries transient failures (3 attempts,
bounded backoff; permanent 4xx not retried), sends an
`Accept-Language` header alongside the browser-compatible set, and
HTML interstitial/anti-bot responses are classified distinctly
("official host returned an HTML page instead of a document") instead
of an opaque parse rejection. Retrieval mechanics are proven over a
genuine loopback HTTP socket (503, 503, 200 → FOUND) and genuine PDF
bytes (the real Vishal RHP flows through the provider's PDF pipeline
and is correctly rejected as a non-Prospectus).

## Fix

- `_best_effort_unlink()` for all three temp-file sites: cleanup can
  never fail an otherwise-successful parse (OS temp reclamation
  handles leftovers).
- `_default_http_fetch`: bounded transient retries + header completion.
- HTML-response classification in both HTTP providers.

## What remains external

Acceptance outcome A (live retrieval completing on the user's
machine) can only be demonstrated in the Windows environment: after
updating to the commit carrying this fix and restarting the server
with the same `IPO_PROSPECTUS_URLS`, one fresh Vishal upload should
complete. If it still returns `AWAITING_ISSUE_TERMS`, the 422 body's
`resolution.providers[].detail` now distinguishes the stage precisely
(configuration / retrieval / HTML interstitial / rejection), and that
detail — not another restart loop — is the next evidence required.
No terms were fabricated; provenance and verification rules are
unchanged; the allowlist was not broadened.
