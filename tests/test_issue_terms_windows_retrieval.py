"""Live-path retrieval regressions (Windows failure, 2026-10-17).

Demonstrated failure stage: on Windows, the providers wrote the
retrieved document to a temp file, parsed it with pypdf (which keeps
the file open), then unlinked the temp path in a ``finally`` block.
Windows refuses to unlink an open file (WinError 32), so the cleanup
exception destroyed the successful parse and surfaced as a document
rejection -- every term stayed missing and the upload returned
AWAITING_ISSUE_TERMS.  POSIX unlink succeeds, so Linux CI never saw it.

These tests pin:
* temp-file cleanup can never destroy a successful parse (all three
  temp-file sites), simulated by making unlink raise PermissionError;
* the default fetcher retries transient failures over a genuine
  loopback HTTP socket (no mocked provider): 503-then-200 succeeds;
* HTML interstitial/anti-bot responses are classified distinctly;
* genuine PDF bytes (the real Vishal RHP) flow through the prospectus
  provider's PDF pipeline and are rejected as a non-Prospectus --
  proving the PDF-bytes path, not only the text path used historically.

Live SEBI retrieval is NOT exercised here (sandbox egress cannot reach
sebi.gov.in); the loopback tests prove retrieval mechanics only.
"""

from __future__ import annotations

import http.server
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from ipo_screening import issue_terms as issue_terms_module
from ipo_screening.issue_terms import (
    HttpNoticeProvider,
    HttpProspectusProvider,
    NoticeSnapshotCache,
    _default_http_fetch,
)

COMPANY = "Vishal Nirmiti Limited"
IPO_ID = "VISHAL-NIRMITI-LIMITED"
SEBI_URL = "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791286596126.pdf"
VISHAL_RHP = REPO_ROOT / "handoff" / "reference" / "U01122MH1994PLC185445-vishal nirmiti.pdf"

PROSPECTUS_TEXT = """Prospectus
Dated: October 05, 2026
100% Book Built Offer
VISHAL NIRMITI LIMITED
CORPORATE IDENTITY NUMBER: U01122MH1994PLC185445
"Price Band" Price band of a minimum price of Rs 208 per Equity Share (i.e., the Floor Price) and the
maximum price of Rs 220 per Equity Share (i.e., the Cap Price), including any revisions thereof.
"Bid Lot" 68 Equity Shares and in multiples of 68 Equity Shares thereafter.
"Offered Shares" 15,00,000 Equity Shares aggregating to Rs 3,300.00 lakhs as part of the Offer for Sale.
"""


def _windows_unlink(monkeypatch):
    """Simulate Windows: unlinking any file raises PermissionError."""
    original = Path.unlink

    def raising_unlink(self, missing_ok=False):
        raise PermissionError(32, "The process cannot access the file because it is being used by another process")

    monkeypatch.setattr(Path, "unlink", raising_unlink)
    return original


def test_prospectus_parse_survives_windows_unlink_failure(monkeypatch):
    _windows_unlink(monkeypatch)
    provider = HttpProspectusProvider({IPO_ID: SEBI_URL}, fetcher=lambda u: PROSPECTUS_TEXT.encode())
    candidate, report = provider.find(COMPANY, IPO_ID)
    assert report.outcome == "FOUND", report
    assert candidate is not None and candidate.verified is True


def test_notice_parse_survives_windows_unlink_failure(monkeypatch):
    _windows_unlink(monkeypatch)
    notice = (REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt").read_bytes()
    provider = HttpNoticeProvider({IPO_ID: SEBI_URL}, fetcher=lambda u: notice)
    candidate, report = provider.find(COMPANY, IPO_ID)
    # Issuer may or may not match the fixture notice; the parse must not
    # be destroyed by cleanup -- outcome is FOUND or issuer REJECTED,
    # never a WinError-flavoured parse rejection.
    assert "WinError" not in report.detail and "cannot access the file" not in report.detail
    assert report.outcome == "FOUND"


def test_cache_read_survives_windows_unlink_failure(tmp_path, monkeypatch):
    provider = HttpProspectusProvider({IPO_ID: SEBI_URL}, fetcher=lambda u: PROSPECTUS_TEXT.encode())
    candidate, _report = provider.find(COMPANY, IPO_ID)
    cache = NoticeSnapshotCache(tmp_path / "cache")
    cache.put(IPO_ID, candidate)
    _windows_unlink(monkeypatch)
    cached, stale = cache.get(IPO_ID)
    assert cached is not None and stale is False


def test_html_interstitial_is_classified_not_parsed():
    provider = HttpProspectusProvider(
        {IPO_ID: SEBI_URL}, fetcher=lambda u: b"<html><body>Please verify you are human</body></html>"
    )
    candidate, report = provider.find(COMPANY, IPO_ID)
    assert candidate is None
    assert report.outcome == "REJECTED" and "HTML page" in report.detail


class _FlakyHandler(http.server.BaseHTTPRequestHandler):
    attempts = 0
    body = PROSPECTUS_TEXT.encode()

    def do_GET(self):  # noqa: N802
        type(self).attempts += 1
        if type(self).attempts < 3:
            self.send_response(503)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(type(self).body)))
        self.end_headers()
        self.wfile.write(type(self).body)

    def log_message(self, *args):  # silence
        pass


def test_default_fetcher_retries_transient_503_over_real_socket(monkeypatch):
    monkeypatch.setattr(issue_terms_module.time, "sleep", lambda s: None)
    _FlakyHandler.attempts = 0
    server = http.server.HTTPServer(("127.0.0.1", 0), _FlakyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/prospectus.txt"
        provider = HttpProspectusProvider({IPO_ID: url}, allowed_hosts={"127.0.0.1"})
        candidate, report = provider.find(COMPANY, IPO_ID)
        assert report.outcome == "FOUND", report
        assert candidate is not None
        assert _FlakyHandler.attempts == 3
    finally:
        server.shutdown()


def test_default_fetcher_does_not_retry_permanent_404(monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(urllib.error.HTTPError):
        _default_http_fetch(SEBI_URL, 5.0)
    assert calls["n"] == 1


@pytest.mark.slow
def test_genuine_pdf_bytes_rejected_as_non_prospectus():
    """The real Vishal RHP (genuine PDF bytes) must flow through the
    provider's PDF pipeline and be classified -- not crash, not pass."""
    raw = VISHAL_RHP.read_bytes()
    assert raw.startswith(b"%PDF-")
    provider = HttpProspectusProvider({IPO_ID: SEBI_URL}, fetcher=lambda u: raw)
    candidate, report = provider.find(COMPANY, IPO_ID)
    assert candidate is None
    assert report.outcome == "REJECTED"


class _CookieHandler(http.server.BaseHTTPRequestHandler):
    seen_cookies: list = []

    def do_GET(self):  # noqa: N802
        type(self).seen_cookies.append(self.headers.get("Cookie"))
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Set-Cookie", "BSESESSION=abc123; Path=/")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence
        pass


def test_default_fetcher_keeps_session_cookies():
    """BSE serves its homepage (HTTP 200) to cookie-less requests for
    listing/issue URLs (observed on the user's Windows runtime,
    2026-10-18); the default fetcher must therefore carry session
    cookies across requests like a browser session does.  Loopback
    proves the cookie mechanism only -- not live BSE access."""
    _CookieHandler.seen_cookies = []
    server = http.server.HTTPServer(("127.0.0.1", 0), _CookieHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/markets/PublicIssues/IPOIssues?id=1&Type=P"
        assert _default_http_fetch(url, 5.0) == b"ok"
        assert _default_http_fetch(url, 5.0) == b"ok"
    finally:
        server.shutdown()
    assert _CookieHandler.seen_cookies[0] is None  # first request: no cookie yet
    assert "BSESESSION=abc123" in (_CookieHandler.seen_cookies[1] or "")
