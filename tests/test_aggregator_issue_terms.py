"""Authored public-table fixtures and controlled API tests; not live source evidence."""
import copy
import hashlib
import pytest
from fastapi.testclient import TestClient
from ipo_screening.aggregator_issue_terms import (
    TAG, AggregatorIssueTermsResolver, parse_page, apply_override, build_from_env, eligible_url,
)
from ipo_screening.extraction import DocumentExtractor
from ipo_screening.issue_terms import IssueTermsResolver, ResolutionOutcome
from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService, IngestionAwaitingIssueTermsError

URI='https://www.chittorgarh.com/ipo/acme-forge-ipo/123/'
CTX={'open_date':'2026-10-21','close_date':'2026-10-23','price_band_low':100.,'price_band_high':120.,'lot_size':10,'ofs':0.,'fresh_issue':None}


def page(amount='240', unit='Cr',name='Acme Forge',period='21 to 23 Oct, 2026', extra=''):
    return (f'<html><h1>{name} IPO Details</h1><table>'
            f'<tr><td>IPO Date</td><td>{period}</td></tr>'
            f'<tr><td>Fresh Issue</td><td>200000 shares (agg. up to ₹{amount} {unit})</td></tr>'
            '<tr><td>Price Band</td><td>₹100 to ₹120</td></tr>'
            '<tr><td>Lot Size</td><td>10 Shares</td></tr>'+extra+'</table></html>').encode()


def resolver(raw=None, urls=None):
    return AggregatorIssueTermsResolver(fetcher=lambda uri:raw or page(),urls=urls or {'ACME-FORGE-LIMITED':URI},listings=())


def report(raw=None):
    return resolver(raw).resolve(company_name='Acme Forge Limited',ipo_id='ACME-FORGE-LIMITED',issue_context=CTX,missing_fields=['fresh_issue'])


def base():return {'issue':copy.deepcopy(CTX),'financials':{'reporting_unit':'INR_MILLIONS'}}


def test_explicit_policy_opt_in_and_invalid_configuration(monkeypatch):
    monkeypatch.delenv('IPO_ALLOW_AGGREGATOR_ISSUE_TERMS',raising=False)
    assert build_from_env() is None
    monkeypatch.setenv('IPO_ALLOW_AGGREGATOR_ISSUE_TERMS','1')
    assert isinstance(build_from_env(),AggregatorIssueTermsResolver)
    monkeypatch.setenv('IPO_ALLOW_AGGREGATOR_ISSUE_TERMS','yes')
    with pytest.raises(ValueError):build_from_env()


@pytest.mark.parametrize('uri',['http://www.chittorgarh.com/ipo/a/','https://localhost/ipo/a/',
    'https://www.chittorgarh.com.evil.test/ipo/a/','https://user@www.chittorgarh.com/ipo/a/',
    'https://www.chittorgarh.com:8080/ipo/a/','file:///private'])
def test_url_boundaries(uri):assert not eligible_url(uri)


def test_amount_scale_hash_raw_quote_and_nonofficial_provenance():
    r=report();out=apply_override(base(),r,['fresh_issue'])
    assert out['issue']['fresh_issue']==2400
    assert out['issue']['ofs']==0
    assert r['applied_fields']==['fresh_issue'] and r['verified'] is False
    spec=out['_evidence']['issue.fresh_issue']
    assert TAG in spec['note'] and 'NOT official' in spec['note']
    assert spec['extraction_method']=='TABLE_EXTRACTION'
    assert spec['quote']=='200000 shares (agg. up to ₹240 Cr)'
    assert out['_sources'][0]['content_hash']==hashlib.sha256(page()).hexdigest()
    assert out['_sources'][0]['source_type']=='MARKET_DATA'
    assert r['fields']['fresh_issue'][0]['verification']=='UNVERIFIED'


@pytest.mark.parametrize('raw',[page(name='Other Forge'),page(period='21 to 23 Oct, 2025'),
    '<h1>Acme Forge IPO Details</h1><table><tr><td>Fresh Issue</td><td>₹240 Cr</td></tr></table>'.encode(),
    b'<h1>Other IPO</h1><p>Acme Forge Limited</p>', b'<app-root></app-root>'])
def test_identity_period_and_shell_rejected(raw):
    r=report(raw);assert not r['fields']
    assert apply_override(base(),r,['fresh_issue'])['issue']['fresh_issue'] is None


@pytest.mark.parametrize('raw',[page(amount='[●]'),page(unit='shares'),page(unit=''),
    page(extra='<tr><td>Employee Reservation</td><td>₹999 Cr</td></tr>').replace(b'Fresh Issue',b'Total Issue Size')])
def test_placeholder_shares_missing_unit_and_total_cannot_supply_fresh(raw):
    assert apply_override(base(),report(raw),['fresh_issue'])['issue']['fresh_issue'] is None


def test_explicit_nil_ofs_but_absence_not_zero():
    r=report();assert 'ofs' not in r['fields']
    r=report(page(extra='<tr><td>Offer for Sale</td><td>Not applicable</td></tr>'))
    b=base();b['issue']['ofs']=None
    assert apply_override(b,r,['ofs'])['issue']['ofs']==0


def test_official_value_wins_and_disagreeing_source_cannot_supply_other_fields():
    r=report(page().replace(b'120',b'125'))
    assert apply_override(base(),r,['fresh_issue'])['issue']['fresh_issue'] is None
    assert r['rejected_sources']
    b=base();b['issue']['fresh_issue']=999
    assert apply_override(b,report(),['fresh_issue'])['issue']['fresh_issue']==999


def test_aggregator_disagreement_is_not_first_wins():
    r=report();other=report(page(amount='241'))
    r['fields']['fresh_issue']+=other['fields']['fresh_issue']
    out=apply_override(base(),r,['fresh_issue'])
    assert out['issue']['fresh_issue'] is None and r['conflicts']==['issue.fresh_issue']


def test_automatic_listing_exact_issuer_to_actual_detail_link():
    listing=b'<a href="/ipo/acme-forge-ipo/123/">Acme Forge IPO</a><a href="/ipo/foreign/">Other Forge IPO</a>'
    calls=[]
    def fetch(uri):calls.append(uri);return listing if uri.endswith('dashboard.asp') else page()
    res=AggregatorIssueTermsResolver(fetcher=fetch,listings=['https://www.chittorgarh.com/ipo/ipo_dashboard.asp'])
    r=res.resolve(company_name='Acme Forge Limited',ipo_id='ACME-FORGE-LIMITED',issue_context=CTX,missing_fields=['fresh_issue'])
    assert len(calls)==2 and calls[-1]==URI
    assert r['fields']['fresh_issue'][0]['value']==240


def service(tmp_path,monkeypatch,golden_input, fallback, official=None):
    from conftest import REPO_ROOT
    doc=copy.deepcopy(golden_input);doc.update(company_name='Acme Forge Limited',ipo_id='ACME-FORGE-LIMITED')
    doc['issue'].update(CTX)
    doc.get('_evidence',{}).pop('issue.fresh_issue',None)
    monkeypatch.setattr(DocumentExtractor,'extract_from_pdf',lambda *a,**k:(copy.deepcopy(doc),{}))
    return PresentationService(PresentationConfig(store_root=tmp_path/'evaluations',config_dir=REPO_ROOT/'config',
        issue_terms_resolver=official or IssueTermsResolver([]),aggregator_issue_terms_resolver=fallback))


def test_controlled_api_evaluation_persistence_flags_hash_restart_and_duplicate(tmp_path,monkeypatch,golden_input):
    transport=resolver()
    bodies=iter([page()+b'<script>request_id=1</script>',page()+b'<script>request_id=2</script>'])
    transport.fetcher=lambda uri:next(bodies)
    s=service(tmp_path,monkeypatch,golden_input,transport)
    result=s.ingest_document(b'%PDF-1.4 controlled','controlled.pdf')
    assert result.issue_terms['aggregator_override']['applied_fields']==['fresh_issue']
    assert result.evaluation.authority_warnings and TAG in result.message
    stored=s.eval_store.read_full(result.evaluation_id)
    assert any(e['evidence_id']=='EV-issue.fresh_issue' and e['source_id'].startswith('SRC-AGG-') and TAG in e['note'] for e in stored['evidence']['evidence'])
    assert len(stored['score']['modules'])==6
    assert s.eval_store.verify_hashes(result.evaluation_id)['result_hash_matches']
    restarted=PresentationService(s.config)
    client=TestClient(create_app(restarted),base_url='http://127.0.0.1:8000')
    detail=client.get('/api/v1/evaluations/'+result.evaluation_id).json()
    assert detail['authority_warnings'] and detail['result_hash']==result.result_hash
    evidence=client.get('/api/v1/evaluations/'+result.evaluation_id+'/evidence').json()
    assert any(item['verification']==TAG and item['quote']=='200000 shares (agg. up to ₹240 Cr)' for item in evidence['items'])
    assert client.get('/api/v1/evaluations').json()['items'][0]['authority_warnings']
    duplicate=restarted.ingest_document(b'%PDF-1.4 controlled','controlled.pdf')
    assert duplicate.is_duplicate and duplicate.evaluation_id==result.evaluation_id
    assert restarted.eval_store.read_full(result.evaluation_id)==stored
    assert len(restarted.eval_store.list_evaluations())==1


def test_disabled_fallback_keeps_old_gate(tmp_path,monkeypatch,golden_input):
    monkeypatch.delenv('IPO_ALLOW_AGGREGATOR_ISSUE_TERMS',raising=False)
    s=service(tmp_path,monkeypatch,golden_input,None)
    with pytest.raises(IngestionAwaitingIssueTermsError):s.ingest_document(b'%PDF-1.4 controlled','controlled.pdf')
    assert s.eval_store.list_evaluations()==[]


def test_official_conflict_never_calls_fallback(tmp_path,monkeypatch,golden_input):
    class Official:
        def resolve(self,**kw):return ResolutionOutcome(status='CONFLICT',conflicts=['issue.fresh_issue: two official amounts'],unresolved_fields=['fresh_issue'])
    calls=[]
    class Forbidden:
        def resolve(self,**kw):
            calls.append(kw)
            raise AssertionError('fallback must not run for official conflict')
    s=service(tmp_path,monkeypatch,golden_input,Forbidden(),Official())
    with pytest.raises(IngestionAwaitingIssueTermsError) as exc:s.ingest_document(b'%PDF-1.4 controlled','controlled.pdf')
    assert exc.value.resolution['status']=='CONFLICT' and not s.eval_store.list_evaluations()
    assert calls==[]


def test_unusable_fallback_preserves_exact_placeholder_evidence():
    b=base();b['_evidence']={'issue.fresh_issue':{'source_id':'RHP','note':'SOURCE_PLACEHOLDER: ₹[●] million'}}
    r=report(page(amount='[●]'))
    assert apply_override(b,r,['fresh_issue'])==b
    assert r['remaining_fields']==['fresh_issue']


@pytest.mark.parametrize('text',['shareholders 240 crore shares','₹240 cricket shares','₹2,,40 Cr', '₹240 Cr or ₹241 Cr'])
def test_malformed_or_ambiguous_money_does_not_gain_authority(text):
    raw=page().replace('200000 shares (agg. up to ₹240 Cr)'.encode(),text.encode())
    assert apply_override(base(),report(raw),['fresh_issue'])['issue']['fresh_issue'] is None


def test_contradictory_rows_and_invalid_price_band_fail_closed():
    r=report(page(extra='<tr><td>Fresh Issue Size</td><td>₹241 Cr</td></tr>'))
    assert not r['fields']
    r=report(page().replace(b'100 to',b'121 to'))
    assert not r['fields']


def test_assertion_identity_ignores_only_nonconsumed_html_not_changed_evidence():
    one,facts=parse_page(page()+b'<script>request=one</script>',URI,'Acme Forge Limited',CTX)
    two,_=parse_page(page()+b'<script>request=two</script>',URI,'Acme Forge Limited',CTX)
    assert one['content_hash']!=two['content_hash'] and one['source_id']==two['source_id']
    changed,_=parse_page(page(amount='241'),URI,'Acme Forge Limited',CTX)
    assert changed['source_id']!=one['source_id']
    changed_quote,_=parse_page(page(amount='240.0'),URI,'Acme Forge Limited',CTX)
    assert changed_quote['source_id']!=one['source_id']


# ---------------------------------------------------------------------------
# Diagnosing *why* a third-party page was refused (2026-10-24)
#
# One message used to cover four different situations -- an unreadable page, a
# filing with no window, a genuinely different issue and a parse failure -- so
# an operator could not tell "my configuration is wrong" from "this page is
# about another offering".  Each now states its own cause, and where two
# windows exist both are shown.
# ---------------------------------------------------------------------------

def _rejection(raw, context=None):
    r = AggregatorIssueTermsResolver(
        fetcher=lambda uri: raw, urls={'ACME-FORGE-LIMITED': URI}, listings=()
    ).resolve(company_name='Acme Forge Limited', ipo_id='ACME-FORGE-LIMITED',
              issue_context=CTX if context is None else context,
              missing_fields=['fresh_issue'])
    detail = next(a['detail'] for a in r['attempts'] if a['outcome'] == 'REJECTED')
    assert not r['fields']
    return detail


def test_an_unreadable_page_window_is_not_reported_as_a_different_issue():
    detail = _rejection(page(period='dates to be announced'))
    assert 'IDENTITY_WINDOW_UNREADABLE' in detail
    assert 'STALE_OR_DIFFERENT_ISSUE' not in detail


def test_a_filing_without_a_window_cannot_bind_a_page():
    detail = _rejection(page(), context={})
    assert 'IDENTITY_UNBOUND' in detail
    assert 'open=absent' in detail


def test_a_genuine_window_mismatch_states_both_windows():
    detail = _rejection(page(period='21 to 23 Oct, 2025'))
    assert 'STALE_OR_DIFFERENT_ISSUE' in detail
    assert '2025-10-21..2025-10-23' in detail   # what the page says
    assert '2026-10-21..2026-10-23' in detail   # what the filing says


@pytest.mark.parametrize('stated,expected', [
    ('30 Sep - 5 Oct 2026', ('2026-09-30', '2026-10-05')),
    ('28 Dec - 2 Jan 2027', ('2026-12-28', '2027-01-02')),
    ('24 Sep 2025 to 26 Sep 2025', ('2025-09-24', '2025-09-26')),
])
def test_a_window_that_names_its_year_once_is_read(stated, expected):
    from ipo_screening.aggregator_issue_terms import issue_dates

    assert issue_dates(stated) == expected


@pytest.mark.parametrize('stated', ['30 Sep - 5 Oct', '1 to 5', 'dates to be announced'])
def test_an_underdetermined_window_is_not_guessed(stated):
    from ipo_screening.aggregator_issue_terms import issue_dates

    assert issue_dates(stated) == (None, None)


def test_a_year_is_never_inherited_across_more_than_a_bid_window():
    """``28 Dec - 2 Jan`` resolved to 2026->2027, never to a 370-day window."""
    from ipo_screening.aggregator_issue_terms import issue_dates

    assert issue_dates('28 Dec - 2 Jan 2027') == ('2026-12-28', '2027-01-02')
