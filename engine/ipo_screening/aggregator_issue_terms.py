"""Opt-in PA-authorized, non-official issue-term fallback.

Official resolution runs first. Only absent fields may be filled; explicit
issuer/issue-window matching, currency/scale and conflict checks are mandatory.
No total-size substitution, implied OFS zero, shares-times-price or GMP data.
"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import math
import os
import re
import urllib.request
from urllib.parse import urljoin, urlparse, urldefrag

TAG = 'THIRD_PARTY_AGGREGATOR_OVERRIDE'
POLICY = 'pa-aggregator-issue-terms-v1'
HOSTS = frozenset({'www.chittorgarh.com', 'chittorgarh.com', 'www.investorgain.com', 'investorgain.com'})
LISTINGS = ('https://www.chittorgarh.com/ipo/ipo_dashboard.asp',
            'https://www.investorgain.com/report/live-ipo-gmp/331/')
FIELDS = ('fresh_issue', 'ofs', 'price_band_low', 'price_band_high', 'lot_size')
SCALES = {'INR_CRORES': 10_000_000, 'INR_MILLIONS': 1_000_000, 'INR_LAKHS': 100_000}
# Longest span a single offering's bid window can cover (a week plus the
# extension), used only to disambiguate a window that names its year once.
BID_WINDOW_MAX_DAYS = 31


def eligible_url(uri):
    p = urlparse(uri)
    return p.scheme == 'https' and p.hostname in HOSTS and not p.username and not p.password and p.port in (None,443)


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not eligible_url(newurl):
            raise ValueError('aggregator redirect outside allowed public HTTPS hosts')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_public(uri):
    if not eligible_url(uri): raise ValueError('ineligible aggregator URL')
    request = urllib.request.Request(uri,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html'})
    with urllib.request.build_opener(PublicRedirect()).open(request,timeout=15) as response:
        if not eligible_url(response.url): raise ValueError('ineligible final URL')
        raw = response.read(2_000_001)
    if len(raw)>2_000_000: raise ValueError('aggregator response exceeds bounded size')
    return raw


class Tables(HTMLParser):
    """Keep original rendered cell strings and row numbers; ignore scripts."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[]; self.headings=[]; self.links=[]
        self.row=None; self.cell=None; self.heading=None; self.anchor=None; self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.hidden+=1; return
        if self.hidden:return
        if tag=='h1':self.heading=''
        if tag=='tr':self.row=[]
        if tag in ('td','th') and self.row is not None:self.cell=''
        if tag=='a':self.anchor=[dict(attrs).get('href',''),'']
    def handle_data(self,text):
        if self.hidden:return
        if self.cell is not None:self.cell+=text
        if self.heading is not None:self.heading+=text
        if self.anchor is not None:self.anchor[1]+=text
    def handle_endtag(self,tag):
        if tag in ('script','style'):
            self.hidden=max(0,self.hidden-1);return
        if self.hidden:return
        if tag in ('td','th') and self.cell is not None and self.row is not None:
            self.row.append(' '.join(self.cell.split()));self.cell=None
        if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
        if tag=='h1' and self.heading is not None:self.headings.append(' '.join(self.heading.split()));self.heading=None
        if tag=='a' and self.anchor is not None:self.links.append(self.anchor);self.anchor=None


def issuer_key(name):
    name = re.sub(r'\b(?:Limited|Ltd\.?)\s*$', '', name.strip(), flags=re.I)
    return re.sub(r'[^A-Z0-9]','',name.upper())


def issuer_heading(text, company):
    # A dedicated IPO heading, not a company mention in menus or comments.
    name = re.split(r'\s+IPO\b',text,1,flags=re.I)[0]
    return bool(re.search(r'\s+IPO\b',text,re.I) and issuer_key(name)==issuer_key(company))


def date_token(text):
    text = re.sub(r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s*','',text.strip(),flags=re.I).replace(',','')
    for fmt in ('%b %d %Y','%B %d %Y','%d %b %Y','%d %B %Y','%Y-%m-%d','%d-%m-%Y'):
        try:return datetime.strptime(text,fmt).date().isoformat()
        except ValueError:pass
    return None


def issue_dates(value):
    match=re.fullmatch(r'(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})',value,re.I)
    if match:
        a,b,month,year=match.groups()
        return date_token(f'{a} {month} {year}'),date_token(f'{b} {month} {year}')
    parts=re.split(r'\s+to\s+|\s+-\s+',value,flags=re.I)
    if len(parts)!=2:return (None,None)
    opened,closed=map(date_token,parts)
    if opened or not closed:
        return opened,closed
    # A window may name the year once ("30 Sep - 5 Oct 2026").  The missing
    # year is *not* guessed: the closing date's year and the year before it are
    # both tried, and the window is accepted only when exactly one candidate is
    # non-inverted **and** no longer than a bid window can be (BID_WINDOW_MAX_DAYS).
    # Anything else stays unreadable, because an unbounded interpretation of a
    # one-year date is exactly the error that binds a page to the wrong issue.
    tail=re.search(r',?\s*(\d{4})\s*$',parts[1])
    if not tail:return (None,None)
    year=int(tail.group(1))
    candidates=[]
    for candidate_year in (year,year-1):
        attempt=date_token(re.sub(r',?\s*\d{4}\s*$','',parts[0]).strip()+f' {candidate_year}')
        if attempt:
            candidates.append((attempt,closed))
    valid=[pair for pair in candidates
           if pair[0]<=pair[1]
           and (datetime.strptime(pair[1],'%Y-%m-%d')-datetime.strptime(pair[0],'%Y-%m-%d')).days<=BID_WINDOW_MAX_DAYS]
    return valid[0] if len(valid)==1 else (None,None)


def parse_page(raw, uri, company, context):
    if not eligible_url(uri) or not urlparse(uri).path.startswith('/ipo/'):
        raise ValueError('not an allowed aggregator issue-detail page')
    doc=Tables();doc.feed(raw.decode('utf-8',errors='strict'))
    if len(doc.headings)!=1 or not issuer_heading(doc.headings[0],company):
        raise ValueError('exact issuer IPO heading not established')
    pairs={}
    for index,row in enumerate(doc.rows,1):
        if len(row)==2:pairs.setdefault(row[0].strip().lower(),[]).append((row[1],index,row[0]))
    periods={issue_dates(v) for v,_,_ in pairs.get('ipo date',[])}
    if len(periods)!=1:raise ValueError('unique explicit IPO date range not established')
    opened,closed=next(iter(periods))
    # Four different things used to be reported as one message
    # ("aggregator period differs or official/filing window absent"), which is
    # useless to an operator: an unreadable page, a missing filing window and a
    # genuinely different issue all looked identical.  They are separated here,
    # and where there are two windows both are stated.
    filing_open=str(context.get('open_date') or '')
    filing_close=str(context.get('close_date') or '')
    if not opened or not closed or opened>closed:
        raise ValueError(
            'IDENTITY_WINDOW_UNREADABLE: this page\'s IPO Date row does not state a readable, '
            'non-inverted bid window, so the page cannot be bound to any issue; nothing on it '
            'was read and nothing may be concluded from its silence')
    if not filing_open or not filing_close:
        raise ValueError(
            'IDENTITY_UNBOUND: the filing established no bid window '
            f'(open={filing_open or "absent"}, close={filing_close or "absent"}), so a third-party '
            'page cannot be bound to this issue; no value was taken')
    if opened!=filing_open or closed!=filing_close:
        raise ValueError(
            f'STALE_OR_DIFFERENT_ISSUE: the page\'s window {opened}..{closed} differs from the '
            f'filing\'s {filing_open}..{filing_close}; the page describes another offering and no '
            'value was taken')
    digest=hashlib.sha256(raw).hexdigest(); sid='SRC-AGG-'+digest[:16].upper()
    source={'source_id':sid,'source_type':'MARKET_DATA','uri':uri,'content_hash':digest,
            'retrieval_timestamp':datetime.now(timezone.utc).isoformat().replace('+00:00','Z')}
    candidates={}
    def add(field,value,unit,row,label,quote):
        if not math.isfinite(value) or value<0 or (field not in ('fresh_issue','ofs') and value<=0):return
        if field=='lot_size' and not value.is_integer():return
        item={'value':value,'unit':unit,'source_id':sid,'quote':quote,'locator':f'HTML table row {row}, {label}',
              'extraction_method':'TABLE_EXTRACTION','verification':'UNVERIFIED','authority':TAG,
              'issuer':company,'uri':uri,'content_hash':digest,'retrieved_at':source['retrieval_timestamp'],
              'open_date':opened,'close_date':closed}
        candidates.setdefault(field,[]).append(item)
    money=re.compile(r'(?:₹|\bRs\.?|\bINR)\s*(\d[\d,]*(?:\.\d+)?)\s*(crores?|cr\.?|millions?|mn|lakhs?)\b',re.I)
    from .extraction.exchange_issue_page import _number
    for field,labels in (('fresh_issue',('fresh issue','fresh issue size')),('ofs',('offer for sale','offer for sale size','ofs'))):
        for label in labels:
            for value,row,original in pairs.get(label,[]):
                if re.search(r'\[|\bTBD\b|employee|reservation|anchor|shareholder',value,re.I):continue
                amounts=list(money.finditer(value))
                if len(amounts)==1:
                    m=amounts[0]
                    if ',,' in m[1] or m[1].endswith(','):continue
                    word=m[2].lower();unit='INR_CRORES' if word.startswith('cr') else 'INR_LAKHS' if word.startswith('lakh') else 'INR_MILLIONS'
                    add(field,_number(m[1]),unit,row,original,value)
                elif field=='ofs' and re.fullmatch(r'nil|not applicable',value.strip(),re.I):add(field,0.,'INR_CRORES',row,original,value)
    for value,row,label in pairs.get('price band',[]):
        m=re.fullmatch(r'(?:₹|Rs\.?|INR)\s*(\d[\d,]*(?:\.\d+)?)\s*(?:to|-)\s*(?:₹|Rs\.?|INR)\s*(\d[\d,]*(?:\.\d+)?)(?:\s+per\s+share)?',value,re.I)
        if m:
            add('price_band_low',_number(m[1]),'INR',row,label,value);add('price_band_high',_number(m[2]),'INR',row,label,value)
    for value,row,label in pairs.get('lot size',[]):
        if re.fullmatch(r'[\d,]+\s+Shares?',value,re.I):add('lot_size',_number(value.split()[0]),'SHARES',row,label,value)
    from .issue_terms import _values_valid
    for field,items in candidates.items():
        normalized={item['value']*SCALES[item['unit']] if field in ('fresh_issue','ofs') else item['value'] for item in items}
        if len(normalized)>1:raise ValueError('contradictory repeated '+field+' rows')
    if _values_valid({field:items[0]['value'] for field,items in candidates.items() if field in ('price_band_low','price_band_high','lot_size')}):
        raise ValueError('invalid third-party pricing invariants')
    # Identity is the qualified assertion, not volatile React/ad payloads.
    # Full raw response hashes remain in provenance; duplicate evaluation keeps
    # its ORIGINAL immutable manifest. A changed value/unit/quote/row label,
    # issuer/window or publisher URL still changes identity.
    assertion={'issuer':issuer_key(company),'open_date':opened,'close_date':closed,'uri':uri,
        'fields':{field:[{key:item[key] for key in ('value','unit','quote')} | {'label':item['locator'].split(', ',1)[1]}
                         for item in items] for field,items in candidates.items()}}
    fingerprint=hashlib.sha256(json.dumps(assertion,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    source['source_id']='SRC-AGG-'+fingerprint[:16].upper()
    for items in candidates.values():
        for item in items:item['source_id']=source['source_id']
    return source,candidates


class AggregatorIssueTermsResolver:
    def __init__(self, fetcher=None, urls=None, listings=LISTINGS):
        self.fetcher=fetcher or fetch_public;self.urls=dict(urls or {});self.listings=tuple(listings)
    def resolve(self,*,company_name,ipo_id,issue_context,missing_fields):
        report={'policy':POLICY,'authority':TAG,'verified':False,'attempts':[],'fields':{},'conflicts':[]}
        uris=[]
        if ipo_id in self.urls:uris.append(self.urls[ipo_id])
        else:
            for uri in self.listings:
                try:
                    if not eligible_url(uri):raise ValueError('ineligible listing URL')
                    raw=self.fetcher(uri);doc=Tables();doc.feed(raw.decode('utf-8',errors='strict'))
                    for href,label in doc.links:
                        target=urldefrag(urljoin(uri,href))[0]
                        name=re.sub(r'\s+IPO\s*$','',label.strip(),flags=re.I)
                        if issuer_key(name)==issuer_key(company_name) and eligible_url(target) and urlparse(target).path.startswith('/ipo/'):
                            uris.append(target)
                    report['attempts'].append({'uri':uri,'outcome':'LISTING_READ','content_hash':hashlib.sha256(raw).hexdigest()})
                except Exception as exc:report['attempts'].append({'uri':uri,'outcome':'UNAVAILABLE','detail':f'{type(exc).__name__}: {exc}'})
        for uri in list(dict.fromkeys(uris))[:4]:
            try:
                if not eligible_url(uri):raise ValueError('ineligible detail URL')
                source,fields=parse_page(self.fetcher(uri),uri,company_name,issue_context)
                report['attempts'].append({'uri':uri,'outcome':'ISSUER_AND_PERIOD_MATCHED','content_hash':source['content_hash']})
                for field,items in fields.items():
                    for item in items:
                        item['source']=source
                        report['fields'].setdefault(field,[]).append(item)
            except Exception as exc:report['attempts'].append({'uri':uri,'outcome':'REJECTED','detail':f'{type(exc).__name__}: {exc}'})
        return report


def apply_override(base, report, missing_fields):
    """Validate the entire selection before mutation; retain official values."""
    from .issue_terms import _values_valid
    result=copy.deepcopy(base);issue=result.setdefault('issue',{});unit=(result.get('financials') or {}).get('reporting_unit')
    selected={};report['applied_fields']=[]
    report['remaining_fields']=[field for field in missing_fields if issue.get(field) is None]
    rejected=set()
    for field,items in report['fields'].items():
        if issue.get(field) is None:continue
        for item in items:
            if field in ('fresh_issue','ofs'):
                if unit not in SCALES:continue
                normalized=item['value']*SCALES[item['unit']]/SCALES[unit]
            else:normalized=item['value']
            if abs(float(issue[field])-normalized)>1e-6:rejected.add(item['source_id'])
    report['rejected_sources']=sorted(rejected)

    for field,items in report['fields'].items():
        if field not in FIELDS:continue
        items=[item for item in items if item['source_id'] not in rejected]
        if not items:continue
        values={item['value']*SCALES[item['unit']] if field in ('fresh_issue','ofs') else item['value'] for item in items}
        if len(values)>1:
            report['conflicts'].append('issue.'+field);continue
        if field not in missing_fields or issue.get(field) is not None:continue
        if field in ('fresh_issue','ofs') and unit not in SCALES:continue
        selected[field]=dict(items[0],normalized_value=next(iter(values))/SCALES[unit] if field in ('fresh_issue','ofs') else next(iter(values)))
    # An aggregator conflict never arbitrarily picks a publisher or supplies
    # another missing field while the disagreement is unresolved.
    if report['conflicts']:return result
    combined={k:issue.get(k) for k in ('price_band_low','price_band_high','lot_size')}
    combined.update({k:v['normalized_value'] for k,v in selected.items() if k in combined})
    if _values_valid({k:v for k,v in combined.items() if v is not None}):
        report['conflicts'].append('invalid combined pricing');return result
    for field,item in selected.items():
        issue[field]=int(item['normalized_value']) if field=='lot_size' else item['normalized_value']
        sources=result.setdefault('_sources',[])
        if not any(s.get('source_id')==item['source_id'] for s in sources):sources.append(item['source'])
        result.setdefault('_evidence',{})['issue.'+field]={
            'source_id':item['source_id'],'extraction_method':'TABLE_EXTRACTION','quote':item['quote'],'locator':item['locator'],
            'note':f'{TAG}; PA policy {POLICY}; UNVERIFIED third-party assertion, NOT official disclosure. '
                   f"Raw amount/value {item['value']} {item['unit']}; normalized to {unit if field in ('fresh_issue','ofs') else item['unit']}",
        }
        report['applied_fields'].append(field)
    report['remaining_fields']=[field for field in missing_fields if issue.get(field) is None]
    return result


def build_from_env():
    value=os.getenv('IPO_ALLOW_AGGREGATOR_ISSUE_TERMS','0')
    if value not in ('0','1'):raise ValueError('IPO_ALLOW_AGGREGATOR_ISSUE_TERMS must be 0 or 1')
    if value=='0':return None
    urls=json.loads(os.getenv('IPO_AGGREGATOR_ISSUE_URLS','{}'))
    if not isinstance(urls,dict) or any(not isinstance(k,str) or not isinstance(v,str) or not eligible_url(v) for k,v in urls.items()):
        raise ValueError('IPO_AGGREGATOR_ISSUE_URLS must map IPO IDs to allowed public HTTPS detail URLs')
    return AggregatorIssueTermsResolver(urls=urls)


def authority_warnings(record):
    snapshot=record.get('input_snapshot') or {}
    canonical=snapshot.get('input') if isinstance(snapshot.get('input'),dict) else snapshot
    fields={field for field,spec in (canonical.get('_evidence') or {}).items()
            if isinstance(spec,dict) and str(spec.get('source_id','')).startswith('SRC-AGG-')}
    for spec in (record.get('evidence') or {}).get('evidence',[]):
        if str(spec.get('source_id','')).startswith('SRC-AGG-'):
            fields.add(spec.get('field') or spec.get('evidence_id','').removeprefix('EV-'))
    return [f'{TAG}: {field} used PA-authorized third-party data, NOT official disclosure.' for field in sorted(fields)]
