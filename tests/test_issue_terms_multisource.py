"""Shared field resolution; all transport synthetic, no live evidence or persistence."""
import copy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from ipo_screening.issue_terms import (IssueTermsResolver, NoticeCandidate, ProviderReport,
    OfficialDiscoveryProvider, HttpNoticeProvider)
from ipo_screening.issue_platforms import PublicPlatformProvider, PLATFORM_LISTINGS
from ipo_screening.extraction.exchange_issue_page import ExchangeIssuePageParser
from ipo_screening.extraction.price_band_notice import PriceBandField
from ipo_screening.enrichment_engine import EnrichmentEngine

FIELDS = ['price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue', 'open_date', 'close_date']


def candidate(issuer='ACME FORGE LIMITED', text='', provider='test', verified=True):
    raw = ('<html><h1>' + issuer + '</h1>' + text + '</html>').encode()
    url = 'https://www.nseindia.com/' + provider
    result = ExchangeIssuePageParser().parse(raw, url=url)
    return NoticeCandidate(result, provider, url, '2026-10-21T00:00:00Z', verified=verified)


class Provider:
    def __init__(self, item=None, error=False):
        self.item, self.error, self.calls = item, error, 0
        self.name = 'mock'

    def find(self, company_name, ipo_id):
        self.calls += 1
        if self.error:
            raise TimeoutError('synthetic timeout')
        return self.item, ProviderReport(self.name, 'FOUND' if self.item else 'UNAVAILABLE')


def resolve(items, issuer='ACME FORGE LIMITED', context=None):
    return IssueTermsResolver([Provider(c) for c in items]).resolve(
        company_name=issuer, ipo_id=issuer.replace(' ', '-'), missing_fields=FIELDS,
        issue_context=context)


@pytest.mark.parametrize('issuer', ['ACME FORGE LIMITED', 'JIO PLATFORMS LIMITED', 'MERIDIAN TEXTILES LIMITED'])
def test_split_fields_have_independent_sources_and_assemble_without_persistence(issuer):
    a = candidate(issuer, '<p>Price Band 100 - 120</p>', 'price')
    b = candidate(issuer, '<p>Market Lot 50</p><p>Fresh Issue Rs 10 crore</p><p>Offer for Sale Rs 0 crore</p>'
                  '<p>Issue Period 21 October 2026 to 23 October 2026</p>', 'lot')
    before = copy.deepcopy(a.result)
    outcome = resolve([a, b], issuer)
    assert outcome.resolved_fields == FIELDS
    assert outcome.unresolved_fields == []
    payload = outcome.enrichment_payload
    assert len(payload['sources']) == 2
    assert payload['price_band']['lot_size']['source_id'] == b.result.source_ref.source_id
    assert payload['price_band']['price_band_low']['source_id'] == a.result.source_ref.source_id
    assert a.result == before
    assembled = EnrichmentEngine.assemble(base_input={'issue': {}, 'financials': {'reporting_unit': 'INR_LAKHS'}},
                                          price_band_notice=payload, mode='final')
    issue = assembled.canonical_input['issue']
    assert issue['lot_size'] == 50 and issue['fresh_issue'] == 1000 and issue['ofs'] == 0
    assert len([s for s in assembled.canonical_input['_sources'] if s['source_id'].startswith('SRC-EXCHANGE')]) == 2
    assert assembled.canonical_input['_evidence']['issue.lot_size']['source_id'] == b.result.source_ref.source_id


def test_third_candidate_conflict_detected_when_first_omits_field():
    a = candidate(text='<p>Price Band 100 - 120</p>', provider='a')
    b = candidate(text='<p>Market Lot 50</p>', provider='b')
    c = candidate(text='<p>Market Lot 60</p>', provider='c')
    outcome = resolve([a, b, c])
    assert outcome.field_diagnostics['lot_size']['state'] == 'CONFLICT'
    assert 'lot_size' not in outcome.enrichment_payload['price_band']
    assert outcome.enrichment_payload['price_band']['price_band_low']['normalized_value'] == 100


def test_exception_and_cache_never_skip_remaining_providers():
    good = Provider(candidate(text='<p>Market Lot 50</p>'))
    bad = Provider(error=True)
    cached = candidate(text='<p>Price Band 100 - 120</p>')
    cache = SimpleNamespace(get=lambda key: (cached, False))
    result = IssueTermsResolver([bad, good], cache=cache).resolve(
        company_name='ACME FORGE LIMITED', ipo_id='ACME', missing_fields=FIELDS)
    assert good.calls == bad.calls == 1
    assert 'lot_size' in result.resolved_fields and result.from_cache


@pytest.mark.parametrize('value', [0, -1, 2.5, float('nan'), float('inf'), True])
def test_invalid_lot_does_not_discard_valid_price(value):
    item = candidate(text='<p>Price Band 100 - 120</p>')
    item.result.lot_size = PriceBandField(name='lot_size', value=value)
    result = resolve([item])
    assert result.field_diagnostics['lot_size']['state'] == 'MALFORMED_OR_AMBIGUOUS'
    assert 'price_band_low' in result.resolved_fields


def test_wrong_issuer_and_wrong_issue_period_are_rejected():
    assert not resolve([candidate('ACME FORGE SERVICES LIMITED', '<p>Market Lot 50</p>')]).resolved_fields
    dated = candidate(text='<p>Market Lot 50</p><p>Issue Period 21 October 2025 to 23 October 2025</p>')
    result = resolve([dated], context={'open_date': '2026-10-21'})
    assert not result.resolved_fields
    assert any('STALE_OR_DIFFERENT_ISSUE' in r.detail for r in result.provider_reports)


def test_unverified_platform_values_cannot_resolve_or_override_official():
    third = candidate(text='<p>Market Lot 60</p>', provider='platform', verified=False)
    official = candidate(text='<p>Market Lot 50</p>', provider='official')
    assert resolve([third]).notice is None
    result = resolve([third, official])
    assert result.notice.lot_size.value == 50
    assert result.field_diagnostics['lot_size']['qualifications']


def test_partial_assembly_preserves_values_but_not_readiness():
    result = resolve([candidate(text='<p>Price Band 100 - 120</p>')])
    assembled = EnrichmentEngine.assemble(base_input={'issue': {}}, price_band_notice=result.enrichment_payload,
                                          mode='final', partial_issue_terms=True)
    assert assembled.canonical_input['issue']['price_band_low'] == 100
    assert 'lot_size' in result.unresolved_fields
    with pytest.raises(Exception, match='lot_size'):
        EnrichmentEngine.assemble(base_input=assembled.canonical_input, mode='final')


@pytest.mark.parametrize('name', list(PLATFORM_LISTINGS))
def test_each_public_platform_follows_exact_link_but_never_verifies(name):
    root = PLATFORM_LISTINGS[name]
    url = root.rstrip('/') + '/acme-ipo'
    listing = f'<a href="{url}">Acme Forge Limited IPO</a><a href="/other">Acme Forge Services IPO</a>'.encode()
    raw = b'<html><h1>Acme Forge IPO</h1><p>Price Band 100 - 120</p><p>Market Lot 50</p></html>'
    calls = []
    def fetch(target):
        calls.append(target)
        return listing if target == root else raw
    item, report = PublicPlatformProvider(name, fetcher=fetch).find('ACME FORGE LIMITED', 'ACME')
    assert calls == [root, url]
    assert item and not item.verified and item.result.lot_size.value == 50
    assert report.sources[-1].classification == 'CANDIDATE'


@pytest.mark.parametrize('response', [b'<html>Access denied CAPTCHA</html>', b'<html>Welcome home</html>'])
def test_blocked_or_homepage_never_claims_non_disclosure(response):
    item, report = PublicPlatformProvider('groww', fetcher=lambda _: response).find('ACME FORGE LIMITED', 'ACME')
    assert item is None and report.outcome == 'UNAVAILABLE'


def test_multiple_official_listings_exhausted_and_provenance_not_mutated():
    # Use current listing fixture shape via a deterministic custom matching listing.
    listings = ['https://www.nseindia.com/list-a', 'https://www.bseindia.com/list-b']
    page = b'<html>IPO Issues <a href="https://www.nseindia.com/issue-information/acme-forge">ACME FORGE LIMITED</a></html>'
    calls = []
    def fetch(url):
        calls.append(url)
        return page if url in listings else b'<html><h1>ACME FORGE LIMITED</h1><p>Market Lot 50</p></html>'
    _, report = OfficialDiscoveryProvider(fetcher=fetch, listing_urls=listings).find('ACME FORGE LIMITED', 'ACME')
    assert all(u in calls for u in listings)
    assert len(report.sources) == 2


def test_observed_nse_formats_generic_not_issuer_specific():
    c = candidate(text="<p>Price Range Rs. 1065 to Rs. 1119 per Equity Share</p>"
                  "<p>Bid Lot 12 Equity Shares and in multiples thereof</p>"
                  "<p>Issue Period 21-Oct-2026 to 23-Oct-2026</p>")
    out = resolve([c])
    assert c.result.price_band_low.value == 1065
    assert c.result.price_band_high.value == 1119
    assert c.result.lot_size.value == 12
    assert c.result.open_date.value == '2026-10-21'
    assert c.result.close_date.value == '2026-10-23'
    assert out.resolved_fields == ['price_band_low', 'price_band_high', 'lot_size', 'open_date', 'close_date']
    assert c.result.ofs_amount is None and c.result.fresh_issue_amount is None
    assert c.result.to_enrichment_dict()['as_of'] is None



@pytest.mark.parametrize('label', ['Market Lot -12', 'Lot Size 1,2', 'Fresh Issue Rs -5 crore', 'Offer for Sale Rs -1 lakh'])
def test_malformed_numeric_field_never_loses_other_valid_terms(label):
    out = resolve([candidate(text='<p>Price Band 100 - 120</p><p>' + label + '</p>')])
    assert out.enrichment_payload['price_band']['price_band_low']['normalized_value'] == 100
    field = 'lot_size' if 'Lot' in label else 'fresh_issue' if 'Fresh' in label else 'ofs'
    assert out.field_diagnostics[field]['state'] == 'MALFORMED_OR_AMBIGUOUS'
    assert field not in out.resolved_fields


def test_amount_equivalence_and_field_specific_official_conflict():
    a = candidate(text='<p>Fresh Issue Rs 10 crore</p><p>Offer for Sale Rs 2 crore</p>', provider='a')
    b = candidate(text='<p>Fresh Issue Rs 100 million</p><p>Offer for Sale Rs 3 crore</p>', provider='b')
    out = resolve([a, b])
    assert out.field_diagnostics['fresh_issue']['state'] == 'VERIFIED'
    assert len(out.field_diagnostics['fresh_issue']['candidates']) == 2
    assert out.field_diagnostics['ofs']['state'] == 'CONFLICT'
    assert 'fresh_issue_amount' in out.enrichment_payload and 'ofs_amount' not in out.enrichment_payload
    evidence = out.field_diagnostics['fresh_issue']['candidates'][0]
    assert evidence['canonical_field'] == 'issue.fresh_issue' and evidence['ipo_id']
    assert evidence['source_timestamp'] is None and evidence['content_hash']


def test_official_amount_only_detail_is_not_discarded():
    raw = b'<html><h1>ACME FORGE LIMITED</h1><p>Fresh Issue Rs 10 crore</p></html>'
    item, reason = OfficialDiscoveryProvider(fetcher=lambda _: raw)._from_issue_page(
        'https://www.nseindia.com/issue-information?symbol=ACME', 'ACME FORGE LIMITED')
    assert item is not None, reason
    assert resolve([item]).resolved_fields == ['fresh_issue']


@pytest.mark.parametrize('code,expected', [(401, 'ACCESS_DENIED'), (403, 'ACCESS_DENIED'), (429, 'RATE_LIMITED'), (404, 'HTTP_ERROR')])
def test_platform_http_failure_preserves_transport_classification(code, expected):
    from urllib.error import HTTPError
    def fetch(url):
        raise HTTPError(url, code, 'synthetic', {}, None)
    item, report = PublicPlatformProvider('dhan', fetcher=fetch).find('ACME FORGE LIMITED', 'ACME')
    assert item is None and report.sources[0].classification == expected
    assert report.outcome == 'UNAVAILABLE'


def test_platform_timeout_is_not_non_disclosure():
    from urllib.error import URLError
    def fetch(url):
        raise URLError(TimeoutError('synthetic timeout'))
    _, report = PublicPlatformProvider('groww', fetcher=fetch).find('ACME FORGE LIMITED', 'ACME')
    assert report.sources[0].classification == 'TIMEOUT'


def test_platform_detail_malformed_labels_not_falsely_undisclosed():
    root = PLATFORM_LISTINGS['indmoney']
    detail = root + '/acme'
    def fetch(url):
        if url == root:
            return ('<a href="' + detail + '">Acme Forge IPO</a>').encode()
        return b'<html><h1>Acme Forge IPO</h1><p>Price Band [pending]</p></html>'
    item, report = PublicPlatformProvider('indmoney', fetcher=fetch).find('ACME FORGE LIMITED', 'ACME')
    assert item is None and report.sources[-1].classification == 'PARSE_FAILURE_OR_MALFORMED_TERMS'


def test_platform_source_and_fields_never_mislabelled_exchange_verified():
    root = PLATFORM_LISTINGS['dhan']
    def fetch(url):
        return (b'<a href="/ipo/acme">Acme Forge IPO</a>' if url == root else
                b'<html><h1>Acme Forge IPO</h1><p>Market Lot 12</p></html>')
    item, _ = PublicPlatformProvider('dhan', fetcher=fetch).find('ACME FORGE LIMITED', 'ACME')
    payload = item.result.to_enrichment_dict()
    assert payload['sources'][0]['source_type'] == 'MARKET_DATA'
    assert payload['sources'][0]['source_id'].startswith('SRC-PLATFORM-')
    assert payload['sources'][0]['note'] == 'INVESTMENT_PLATFORM_PAGE'
    assert payload['price_band']['lot_size']['verification'] == 'UNVERIFIED'
    assert payload['price_band']['lot_size']['extraction_method'] == 'MARKET_DATA'


@pytest.mark.parametrize('value', [float('nan'), float('inf'), float('-inf')])
def test_rejected_nonfinite_diagnostics_are_strict_json_api_safe(value):
    import json
    from starlette.responses import JSONResponse
    item = candidate(text='<p>Price Band 100 - 120</p>')
    item.result.lot_size = PriceBandField(name='lot_size', value=value)
    out = resolve([item])
    response = JSONResponse(out.to_dict())
    fields = json.loads(response.body)['fields']
    assert fields['lot_size']['state'] == 'MALFORMED_OR_AMBIGUOUS'
    assert isinstance(fields['lot_size']['candidates'][0]['value'], str)
    assert fields['price_band_low']['candidates'][0]['value'] == 100
    assert 'lot_size' not in out.resolved_fields


@pytest.mark.parametrize('name', list(PLATFORM_LISTINGS))
def test_date_only_platform_page_retained_as_unverified_candidate(name):
    root = PLATFORM_LISTINGS[name]
    def fetch(url):
        return (b'<a href="/ipo/acme">Acme Forge IPO</a>' if url == root else
                b'<html><h1>Acme Forge IPO</h1><p>Issue Period 21 October 2026 to 23 October 2026</p></html>')
    item, report = PublicPlatformProvider(name, fetcher=fetch).find('ACME FORGE LIMITED', 'ACME')
    assert item is not None and not item.verified, report
    assert item.result.open_date.value == '2026-10-21'
    assert item.result.close_date.value == '2026-10-23'
    out = resolve([item])
    assert out.field_diagnostics['open_date']['state'] == 'CANDIDATE_AWAITING_VERIFICATION'
    assert out.resolved_fields == [] and out.notice is None
