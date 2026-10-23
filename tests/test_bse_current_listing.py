"""Published BSE SPA protocol fixtures; not captured/live financial evidence."""
import hashlib
import json
import urllib.error
from urllib.parse import parse_qs, urlparse
import pytest
from ipo_screening.official_issue_sources import BSE_LISTING, BSE_PUBLIC_LISTING, bse_issue_records
from ipo_screening.issue_terms import OfficialDiscoveryProvider, IssueTermsResolver

NAME = 'Acme Forge Limited'


def record(**changes):
    return dict(Scrip_Name=NAME, Scrip_cd='17', IPO_NO=42, IR_flag='IPO', Status='L',
                Price_Band='Rs. 100 to Rs. 120', Start_Dt='2026-10-21T00:00:00',
                End_Dt='2026-10-23T00:00:00', **changes)


def raw(*rows):
    return json.dumps({'Table': list(rows)}).encode()


def resolve(body, fields=('price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue')):
    calls = []
    def fetch(url):
        calls.append(url)
        return body if url == BSE_LISTING else b'<app-root></app-root>'
    outcome = IssueTermsResolver([OfficialDiscoveryProvider(fetcher=fetch, listing_urls=[BSE_LISTING])]).resolve(
        company_name=NAME, ipo_id='ACME-FORGE-LIMITED', missing_fields=list(fields))
    return outcome, calls


def test_current_records_keep_actual_json_hash_quotes_and_complete_detail_query():
    body = raw(record())
    page, terms = bse_issue_records(body, NAME)[0]
    assert parse_qs(urlparse(page).query) == {'id': ['17'], 'type': ['IPO'], 'idtype': ['1'],
        'status': ['L'], 'IPONo': ['42'], 'startdt': ['21/10/2026']}
    assert terms.company_name == NAME
    assert terms.source_ref.content_hash == hashlib.sha256(body).hexdigest()
    assert terms.price_band_low.value == 100 and terms.price_band_high.value == 120
    assert terms.price_band_high.quote == 'Rs. 100 to Rs. 120'
    assert terms.price_band_high.locator == 'BSE Table[0].Price_Band'
    assert terms.open_date.quote == '2026-10-21T00:00:00'
    assert terms.open_date.value == '2026-10-21'
    assert terms.lot_size is None and terms.fresh_issue_amount is None and terms.ofs_amount is None


def test_partial_record_does_not_default_lot_or_substitute_total_for_fresh():
    row = record()
    row['IssueSize'] = 'Rs. 240 million'
    result, calls = resolve(raw(row))
    assert result.status == 'PARTIAL'
    assert result.resolved_fields == ['price_band_low', 'price_band_high']
    assert result.unresolved_fields == ['lot_size', 'ofs', 'fresh_issue']
    assert calls[0] == BSE_LISTING and 'IPONo=42' in calls[1]
    assert result.field_diagnostics['price_band_high']['candidates'][0]['uri'] == BSE_LISTING


@pytest.mark.parametrize('change', [{'Scrip_Name': 'Other Acme Limited'}, {'IR_flag': 'OFS'}, {'Status': 'C'}])
def test_foreign_non_ipo_and_closed_records_never_supply_terms(change):
    row = record(); row.update(change)
    result, calls = resolve(raw(row))
    assert result.status == 'UNAVAILABLE' and not result.resolved_fields
    assert calls == [BSE_LISTING]


@pytest.mark.parametrize('body', [b'<app-root></app-root>', b'{}', b'[]', b'{"Table":[7]}'])
def test_shell_and_malformed_response_are_not_a_searched_listing(body):
    result, _ = resolve(body)
    assert result.status == 'UNAVAILABLE'
    assert not result.provider_reports[0].listing_searched
    assert not result.provider_reports[0].sources[0].searched


def test_distinct_official_rows_conflict_instead_of_first_wins():
    other = record(); other['Price_Band'] = 'Rs. 105 to Rs. 125'
    result, _ = resolve(raw(record(), other))
    assert result.status == 'CONFLICT'
    assert result.field_diagnostics['price_band_high']['state'] == 'CONFLICT'
    assert {c['value'] for c in result.field_diagnostics['price_band_high']['candidates']} == {120, 125}


def test_bse_api_headers_use_public_site_session_json_origin_and_referrer(monkeypatch):
    from ipo_screening import issue_terms as module
    warmups, requests = [], []
    monkeypatch.setattr(module, '_ensure_session_opener', lambda: None)
    monkeypatch.setattr(module, '_warm_up_session', lambda url, timeout: warmups.append(url))
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def geturl(self): return BSE_LISTING
        def read(self): return raw(record())
    def open_(request, **kwargs):
        requests.append(request)
        return Response()
    monkeypatch.setattr(module.urllib.request, 'urlopen', open_)
    body = module._default_http_fetch(BSE_LISTING, 5, referer=BSE_PUBLIC_LISTING,
                                     eligible_redirect_hosts=module.DISCOVERY_HOSTS)
    assert json.loads(body)['Table'][0]['Scrip_Name'] == NAME
    assert warmups == ['https://www.bseindia.com/']
    assert requests[0].get_header('Accept') == 'application/json,text/plain,*/*'
    assert requests[0].get_header('Origin') == 'https://www.bseindia.com'
    assert requests[0].get_header('Referer') == BSE_PUBLIC_LISTING
    assert 'api.bseindia.com' not in module.OFFICIAL_HOSTS  # direct notice authority unchanged


def test_current_feed_403_names_external_failure_without_claiming_absence():
    def forbidden(url):
        raise urllib.error.HTTPError(url, 403, 'Forbidden', {}, None)
    outcome = IssueTermsResolver([OfficialDiscoveryProvider(fetcher=forbidden, listing_urls=[BSE_LISTING])]).resolve(
        company_name=NAME, ipo_id='ACME-FORGE-LIMITED', missing_fields=['fresh_issue'])
    assert outcome.status == 'UNAVAILABLE'
    report = outcome.provider_reports[0]
    assert '403' in report.notes[0]
    assert not report.sources[0].searched


def test_large_scanned_notice_has_measured_bounded_budget_and_discards_partial_output(monkeypatch):
    import subprocess
    from ipo_screening.extraction import official_notice_ocr as ocr, official_offer_amounts as amounts
    monkeypatch.setattr(amounts, 'document_pages', lambda raw: [(page, '') for page in range(1, 6)])
    calls = []
    def expired(command, **kwargs):
        calls.append((command, kwargs))
        raise subprocess.TimeoutExpired(command, kwargs['timeout'], output=b'partial terms')
    monkeypatch.setattr(ocr.subprocess, 'run', expired)
    with pytest.raises(ValueError, match='bounded 270-second read budget'):
        ocr.parse_if_scanned(b'%PDF-controlled', 'https://www.nseindia.com/ad.pdf')
    assert calls[0][1]['timeout'] == 270
    assert calls[0][1]['input'] == b'%PDF-controlled'


def test_failed_ocr_keeps_complete_child_traceback_in_log_without_consuming_stdout(monkeypatch, caplog):
    import subprocess
    from ipo_screening.extraction import official_notice_ocr as ocr, official_offer_amounts as amounts
    monkeypatch.setattr(amounts, 'document_pages', lambda raw: [(1, '')])
    stderr = b'Traceback root context\n' + b'stack frame\n' * 100 + b'original child error'
    monkeypatch.setattr(ocr.subprocess, 'run', lambda *args, **kwargs:
        subprocess.CompletedProcess(args, 1, b'{"pages": [[1,"invented partial terms"]]}', stderr))
    with pytest.raises(ValueError, match='original child error'):
        ocr.parse_if_scanned(b'%PDF-controlled', 'https://www.nseindia.com/ad.pdf')
    assert stderr.decode() in caplog.text
    assert 'interpreter=' in caplog.text and 'document_sha256=' in caplog.text
