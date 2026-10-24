"""The operator's `issue-terms` diagnostic, and configured-URL normalisation.

Two small pieces of operator-facing surface, both about not misleading the
person running the engine:

* `ipo_screen.py issue-terms` runs the **real** resolver the ingestion path
  builds and reports what it saw — read-only, no evaluation, no writes.
  Its job is to make the difference between "the host was unreachable" and
  "the host was read and has no matching issue" visible in one command.
* `normalize_configured_url` removes paste artifacts (Markdown link
  syntax, angle brackets, quotes, `&amp;`) so an operator who copies a URL
  out of a document does not get a false "not an official host" verdict.

Transport is synthetic throughout: this module asserts reporting and
configuration behaviour, never live retrieval.
"""

from __future__ import annotations

import json

import pytest

from ipo_screening import issue_terms
from ipo_screening.issue_terms import (
    normalize_configured_url,
    _historical_listing_urls_from_env,
    _url_map_from_env,
)
from ipo_screening.official_issue_sources import BSE_HISTORICAL_LISTING, BSE_LISTING
from tools import ipo_screen  # noqa: E402  (engine/tools is on PYTHONPATH via conftest)

ISSUER = "Paras Healthcare Limited"
DETAIL_URL = ("https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4895&type=IPO"
              "&idtype=2&status=H&IPONo=8048&startdt=21/10/2026")

LISTING = f"""<html><body><table>
<tr><th>Security Name</th><th>Exchange Platform</th><th>Start Date</th><th>End Date</th>
<th>Offer Price</th><th>Face Value</th><th>Type of Issue</th></tr>
<tr><td><a href="{DETAIL_URL.replace('&', '&amp;')}">{ISSUER}</a></td><td>MainBoard</td>
<td>21-10-2026</td><td>23-10-2026</td><td>660.00 - 693.00</td><td>1.00</td>
<td>Book Building</td></tr>
</table></body></html>""".encode()

DETAIL = """<html><body><table><tr><td><b>Paras Healthcare Limited</b></td></tr>
<tr><td>Symbol</td><td>PARASHLTH</td></tr>
<tr><td>Issue Period</td><td>21 Oct 2026 to 23 Oct 2026</td></tr>
<tr><td>Price Band</td><td>660.00-693.00</td></tr>
<tr><td>Market Lot</td><td>21</td></tr></table></body></html>""".encode()


@pytest.fixture
def offline(monkeypatch):
    """Replace the real transport: every URL fails at the socket."""
    def fetch(url, *_args, **_kwargs):
        raise OSError("[Errno 101] Network is unreachable (offline test transport)")
    monkeypatch.setattr(issue_terms, "_default_http_fetch", fetch)
    monkeypatch.delenv("IPO_OFFICIAL_HISTORICAL_LISTINGS", raising=False)


@pytest.fixture
def served(monkeypatch):
    """Replace the real transport with the two official pages."""
    pages = {BSE_LISTING: b"<html><body><p>no issues</p></body></html>",
             BSE_HISTORICAL_LISTING: LISTING, DETAIL_URL: DETAIL}
    monkeypatch.setattr(issue_terms, "_default_http_fetch",
                        lambda url, *_a, **_k: pages[url])
    monkeypatch.setenv("IPO_OFFICIAL_HISTORICAL_LISTINGS", BSE_HISTORICAL_LISTING)


# ----------------------------------------------------------------------
# Paste artifacts
# ----------------------------------------------------------------------
@pytest.mark.parametrize("pasted, expected", [
    ("https://www.bseindia.com/x?a=1&b=2", "https://www.bseindia.com/x?a=1&b=2"),
    ("https://www.bseindia.com/x?a=1&amp;b=2", "https://www.bseindia.com/x?a=1&b=2"),
    ("[https://www.bseindia.com/x?a=1&amp;b=2](https://www.bseindia.com/x?a=1&b=2)",
     "https://www.bseindia.com/x?a=1&b=2"),
    ("  <https://www.bseindia.com/x>  ", "https://www.bseindia.com/x"),
    ('"https://www.bseindia.com/x"', "https://www.bseindia.com/x"),
    ("'https://www.bseindia.com/x'", "https://www.bseindia.com/x"),
])
def test_paste_artifacts_are_removed(pasted, expected):
    assert normalize_configured_url(pasted) == expected


def test_normalisation_never_invents_a_url():
    assert normalize_configured_url("") == ""
    assert normalize_configured_url("www.bseindia.com/x") == "www.bseindia.com/x"  # no scheme added
    assert normalize_configured_url("not a url") == "not a url"


def test_a_pasted_markdown_entry_is_usable_configuration(monkeypatch):
    pasted = f"[{BSE_HISTORICAL_LISTING.replace('&', '&amp;')}]({BSE_HISTORICAL_LISTING})"
    monkeypatch.setenv("IPO_OFFICIAL_HISTORICAL_LISTINGS", pasted)
    usable, problems = _historical_listing_urls_from_env()
    assert usable == [BSE_HISTORICAL_LISTING]
    assert problems == []


def test_pasted_ampersand_entities_are_usable_in_the_notice_map(monkeypatch):
    monkeypatch.setenv("IPO_PRICE_BAND_NOTICE_URLS",
                       '{"P": "https://www.bseindia.com/n.pdf?a=1&amp;b=2"}')
    mapping, problem = _url_map_from_env("IPO_PRICE_BAND_NOTICE_URLS")
    assert problem is None
    assert mapping == {"P": "https://www.bseindia.com/n.pdf?a=1&b=2"}


def test_a_wrapped_url_on_a_foreign_host_is_still_rejected(monkeypatch):
    monkeypatch.setenv("IPO_OFFICIAL_HISTORICAL_LISTINGS", "[https://example.com/x](https://example.com/x)")
    usable, problems = _historical_listing_urls_from_env()
    assert usable == []
    assert problems and "not an allowed official source host" in problems[0]


# ----------------------------------------------------------------------
# The `issue-terms` command
# ----------------------------------------------------------------------
def _run(*argv):
    return ipo_screen.main(["issue-terms", *argv])


def test_unreachable_sources_are_reported_as_transport(offline, capsys):
    code = _run("--issuer", ISSUER, "--open", "2026-10-21", "--close", "2026-10-23")
    out = capsys.readouterr().out
    assert code == ipo_screen.EXIT_REFUSED
    assert "status             UNAVAILABLE" in out
    assert "[TRANSPORT]" in out
    assert "NOT_FOUND" not in out
    assert "UNPUBLISHED" not in out


def test_resolved_terms_are_printed_with_their_evidence(served, capsys):
    code = _run("--issuer", ISSUER, "--open", "2026-10-21", "--close", "2026-10-23")
    out = capsys.readouterr().out
    assert code == ipo_screen.EXIT_OK
    assert "status             RESOLVED" in out
    assert "value 660.0  VERIFIED" in out
    assert "value 693.0  VERIFIED" in out
    assert "value 21  VERIFIED" in out or "value 21.0  VERIFIED" in out
    assert "quote: 660.00 - 693.00" in out
    assert "searched" in out or "historical" in out


def test_without_a_window_the_closed_record_is_withheld(served, capsys):
    code = _run("--issuer", ISSUER)
    out = capsys.readouterr().out
    assert code == ipo_screen.EXIT_REFUSED
    assert "no window: a closed-issue record cannot be bound" in out
    assert "IDENTITY_UNBOUND" in out


def test_the_json_report_is_the_resolver_report(served, capsys):
    code = _run("--issuer", ISSUER, "--open", "2026-10-21", "--close", "2026-10-23", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert code == ipo_screen.EXIT_OK
    assert payload["status"] == "RESOLVED"
    assert payload["resolved_fields"] == ["price_band_low", "price_band_high", "lot_size"]
    assert payload["fields"]["lot_size"]["candidates"][0]["value"] == 21


def test_an_unknown_term_is_a_usage_error(offline, capsys):
    code = _run("--issuer", ISSUER, "--fields", "price_band_low", "not_a_term")
    captured = capsys.readouterr()
    assert code == ipo_screen.EXIT_USAGE
    assert "unknown issue term" in captured.err


def test_the_command_writes_nothing(served, tmp_path, monkeypatch):
    """Read-only: no evaluation, no store, no file touched."""
    monkeypatch.chdir(tmp_path)
    before = sorted(p.name for p in tmp_path.iterdir())
    _run("--issuer", ISSUER, "--open", "2026-10-21", "--close", "2026-10-23")
    assert sorted(p.name for p in tmp_path.iterdir()) == before


# ----------------------------------------------------------------------
# A retrieved page is not a read listing
# ----------------------------------------------------------------------
def test_a_page_with_no_issue_rows_says_so(monkeypatch):
    from ipo_screening.issue_terms import OfficialDiscoveryProvider
    provider = OfficialDiscoveryProvider(
        fetcher=lambda *_a, **_k: b"<html><body><div id='app'></div></body></html>",
        listing_urls=[], historical_listing_urls=[BSE_HISTORICAL_LISTING])
    _, matched, notes = provider._search_historical_listing(
        BSE_HISTORICAL_LISTING, ISSUER, "P",
        {"open_date": "2026-10-21", "close_date": "2026-10-23"})
    assert matched == 0
    assert any("carried no issue-information links at all" in n for n in notes)
    assert any("not a usable closed-issue listing" in n for n in notes)


def test_a_page_with_rows_but_not_this_issuer_says_so(monkeypatch):
    from ipo_screening.issue_terms import OfficialDiscoveryProvider
    other = (b'<table><tr><td><a href="https://www.bseindia.com/markets/publicIssues/'
             b'DisplayIPO?id=1&type=IPO&IPONo=1&startdt=01/01/2026">Other Ltd</a></td>'
             b'<td>01-01-2026</td><td>02-01-2026</td></tr></table>')
    provider = OfficialDiscoveryProvider(
        fetcher=lambda *_a, **_k: other,
        listing_urls=[], historical_listing_urls=[BSE_HISTORICAL_LISTING])
    _, matched, notes = provider._search_historical_listing(
        BSE_HISTORICAL_LISTING, ISSUER, "P",
        {"open_date": "2026-10-21", "close_date": "2026-10-23"})
    assert matched == 0
    assert any("carried 1 issue row(s) but none for this issuer" in n for n in notes)


def test_row_diagnostics_count_what_the_page_carried():
    from ipo_screening.issue_identity import IssueIdentity
    from ipo_screening.official_issue_sources import bse_historical_issue_records
    diagnostics = {}
    records, _ = bse_historical_issue_records(
        LISTING, ISSUER, IssueIdentity("2026-10-21", "2026-10-23"), diagnostics=diagnostics)
    assert len(records) == 1
    assert diagnostics == {"issue_rows": 1, "issuer_rows": 1, "bound_rows": 1, "rejections": 0}


# ----------------------------------------------------------------------
# One-shot official documents for a single issuer
#
# Setting an environment variable and restarting the server is the wrong
# unit of work for "why is this one issuer unresolved".  These flags add the
# same providers the environment would add, under the same allow-list.
# ----------------------------------------------------------------------
NOTICE = b"""PRICE BAND ADVERTISEMENT
INITIAL PUBLIC OFFERING OF PARAS HEALTHCARE LIMITED
NOTICE TO INVESTORS

THE FLOOR PRICE AND THE CAP PRICE
The Floor Price is Rs.660 per Equity Share of face value of Rs.1 each and the Cap Price is Rs.693 per Equity Share of face value of Rs.1 each.
The Price Band is Rs.660 to Rs.693 per Equity Share.
Bids can be made for a minimum of 21 Equity Shares and in multiples of 21 Equity Shares thereafter.

BID/OFFER PERIOD:
BID/OFFER OPENS ON: Wednesday, October 21, 2026
BID/OFFER CLOSES ON: Friday, October 23, 2026
"""


def test_a_one_shot_notice_url_is_used_without_any_environment_configuration(
        monkeypatch, capsys):
    monkeypatch.delenv("IPO_PRICE_BAND_NOTICE_URLS", raising=False)
    monkeypatch.setenv("IPO_OFFICIAL_DISCOVERY", "0")
    fetched = []
    monkeypatch.setattr(issue_terms, "_default_http_fetch",
                        lambda url, *_a, **_k: fetched.append(url) or NOTICE)
    url = "https://www.bseindia.com/downloads/notices/paras-pba.pdf"
    code = ipo_screen.main([
        "issue-terms", "--issuer", "Paras Healthcare Limited",
        "--open", "2026-10-21", "--close", "2026-10-23",
        "--notice-url", url,
    ])
    out = capsys.readouterr().out
    assert fetched == [url]
    assert "price_band_low" in out and "660" in out
    assert code == ipo_screen.EXIT_OK


@pytest.mark.parametrize("bad", [
    "http://www.bseindia.com/downloads/notices/x.pdf",          # not HTTPS
    "https://www.chittorgarh.com/ipo/paras/1/",                  # not official
    "https://listing.bseindia.com/Download/1/PBA.pdf",           # discovery-only host
])
def test_a_one_shot_url_outside_the_official_allow_list_is_refused(
        monkeypatch, capsys, bad):
    monkeypatch.setattr(issue_terms, "_default_http_fetch",
                        lambda *_a, **_k: pytest.fail("no retrieval may be attempted"))
    code = ipo_screen.main(["issue-terms", "--issuer", "Paras Healthcare Limited",
                            "--notice-url", bad])
    err = capsys.readouterr().err
    assert code == ipo_screen.EXIT_USAGE
    assert "official source host" in err


def test_a_one_shot_prospectus_url_uses_the_prospectus_document_class(
        monkeypatch, capsys):
    monkeypatch.delenv("IPO_PROSPECTUS_URLS", raising=False)
    monkeypatch.setenv("IPO_OFFICIAL_DISCOVERY", "0")
    monkeypatch.setattr(issue_terms, "_default_http_fetch", lambda *_a, **_k: NOTICE)
    url = "https://www.sebi.gov.in/sebi_data/attachdocs/paras-p.pdf"
    ipo_screen.main(["issue-terms", "--issuer", "Paras Healthcare Limited",
                     "--open", "2026-10-21", "--close", "2026-10-23",
                     "--prospectus-url", url, "--json"])
    payload = json.loads(capsys.readouterr().out)
    providers = {report.get("provider") for report in payload.get("providers", [])}
    assert "official-prospectus" in providers
    assert "official-url" not in providers
