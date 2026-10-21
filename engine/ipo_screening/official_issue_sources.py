"""Bounded public exchange discovery adapters; no issuer-specific IDs/defaults.

NSE's public JSON listing is the data behind its client-rendered IPO page.
Only an exact legal-name match supplies the symbol/series/status used to reach
that issuer's detail page/API. JSON is parsed as labelled source data, never
trusted as HTML and never attributed to a synthesized HTML document.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlparse

NSE_LISTING = 'https://www.nseindia.com/api/all-upcoming-issues?category=ipo'


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.href = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self.href = dict(attrs).get('href')
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self.href is not None:
            self.links.append((self.href, ' '.join(self.text)))
            self.href = None


def links(raw, base):
    if urlparse(base).path == '/api/ipo-detail':
        data = json.loads(raw)
        return [(r['value'], str(r.get('title') or ''))
                for r in data.get('issueInfo', {}).get('dataList', [])
                if isinstance(r, dict) and isinstance(r.get('value'), str)
                and urlparse(r['value']).scheme == 'https']
    parser = Links()
    parser.feed(raw.decode('utf-8', errors='replace'))
    return [(urljoin(base, href), text) for href, text in parser.links]


def nse_issue_links(raw, company_name):
    from .issue_terms import _norm_name
    rows = json.loads(raw)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError('NSE listing is not an issue-record array')
    # An empty array alone is not authoritative non-publication evidence.
    matched = []
    for row in rows:
        if _norm_name(row.get('companyName')) != _norm_name(company_name):
            continue
        symbol, series, status = (row.get(k) for k in ('symbol', 'series', 'status'))
        if not all(isinstance(v, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,40}', v)
                   for v in (symbol, series, status)):
            raise ValueError('matched NSE record lacks valid symbol/series/status')
        if series != 'EQ' or status.lower() not in ('active', 'upcoming', 'forthcoming'):
            continue  # not the current equity IPO
        matched.append((
            'https://www.nseindia.com/market-data/issue-information?' +
            urlencode({'symbol': symbol, 'series': series, 'type': status}),
            'https://www.nseindia.com/api/ipo-detail?' + urlencode({'symbol': symbol}),
        ))
    return matched


def parse_nse_detail(raw, url):
    from .extraction.exchange_issue_page import ExchangeIssuePageParser
    data = json.loads(raw)
    rows = data.get('issueInfo', {}).get('dataList') if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
        raise ValueError('NSE detail lacks issueInfo.dataList')
    from urllib.parse import parse_qs
    expected_symbol = parse_qs(urlparse(url).query).get('symbol', [None])[0]
    stated_symbol = data.get('issueInfo', {}).get('symbol')
    if stated_symbol and stated_symbol != expected_symbol:
        raise ValueError('NSE detail symbol differs from requested issue')
    # Escape all API strings: embedded tags cannot add facts or issuer names.
    html = '<html><table>' + ''.join('<tr><td>' + escape(str(r.get('title') or '')) +
        '</td><td>' + escape(str(r.get('value') or '')) + '</td></tr>' for r in rows) + '</table></html>'
    result = ExchangeIssuePageParser().parse(html.encode(), url=url)
    # The retained source is the actual API bytes, not the presentation adapter.
    digest = hashlib.sha256(raw).hexdigest()
    sid = 'SRC-EXCHANGE-' + digest[:8].upper()
    from dataclasses import replace
    result.source = replace(result.source, source_id=sid, content_hash=digest)
    result.source_ref = replace(result.source_ref, source_id=sid, content_hash=digest)
    result.company_name = rows[0].get('title') if not rows[0].get('value') else None
    # Quotes are actual decoded API field values, not synthesized HTML. Duplicate
    # conflicting labelled values are ambiguous and must not become first-wins.
    for names, labels in (
        (('price_band_low', 'price_band_high'), ('price range', 'price band')),
        (('lot_size',), ('bid lot', 'market lot', 'lot size')),
        (('open_date', 'close_date'), ('issue period',)),
    ):
        matches = [(i, r.get('value')) for i, r in enumerate(rows)
                   if str(r.get('title') or '').lower().strip() in labels]
        for name in names:
            obj = getattr(result, name)
            if len({str(value) for _, value in matches}) > 1:
                setattr(result, name, None)
            elif obj is not None and matches:
                index, value = matches[0]
                setattr(result, name, replace(obj, quote=str(value),
                    locator=f'NSE issueInfo.dataList[{index}] — {rows[index]["title"]}'))
    result.metadata['page_kind'] = 'nse_issue_detail_json'
    return result


def official_document_members(raw, url):
    """Yield in-memory public PDF/text documents, with exact member identity.

    Never extract archive paths to disk. Reject encrypted/oversized archives and
    suspicious expansion ratios; unsupported contents remain diagnostics, not
    missing terms or a license to invent amounts.
    """
    if not raw.startswith(b'PK\x03\x04'):
        yield raw, url
        return
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > 32 or sum(e.file_size for e in entries) > 64 * 1024 * 1024:
            raise ValueError('official archive exceeds bounded member/size limits')
        for entry in entries:
            if entry.is_dir() or not entry.filename.lower().endswith(('.pdf', '.txt')):
                continue
            if (entry.flag_bits & 1 or entry.file_size > 32 * 1024 * 1024 or
                    entry.file_size > max(1, entry.compress_size) * 200):
                raise ValueError('encrypted or oversized official document member')
            from urllib.parse import quote
            yield archive.read(entry), url + '#zip-member=' + quote(entry.filename, safe='')
