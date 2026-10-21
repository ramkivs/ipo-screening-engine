"""Read public SPA assets to locate BSE's published data contract.

No endpoint guessing, form submission, access-control bypass or financial-term
inference. URLs are followed only from actual first-party HTML/JS references.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import traceback
from urllib.parse import urljoin, urlparse
import urllib.request
import zlib
from ipo_screening.issue_terms import _default_http_fetch
from ipo_screening.official_issue_sources import NSE_LISTING, nse_issue_links
from ipo_screening.extraction.official_offer_amounts import parse_official_rhp

out = Path(os.environ['JIO_RECOVERY_OUTPUT'])
out.mkdir(parents=True, exist_ok=True)
rows = []
queue = [('https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P', None)]
# Independently re-fetch actual raw NSE records/detail for byte/hash and
# quote verification against the API run; do not seed any financial values.
root = Path(__file__).resolve().parents[3]
issuer = parse_official_rhp((root / 'evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf').read_bytes(),
                            'repository-copy-identity-only').company_name
queue.append((NSE_LISTING, 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo'))
seen = set()
# Public service namespace independently exercised in the prior retained
# investigation. Only endpoint paths found in the actual current JS are used.
api_base = 'https://api.bseindia.com/BseIndiaAPI/api'
pattern = re.compile(r'public.?issue|\bipo\b|GetPublicIssue|Pubissues|GetMkt_ISSUE', re.I)
for _ in range(12):
    if not queue:
        break
    url, referrer = queue.pop(0)
    if url in seen:
        continue
    seen.add(url)
    row = {'url': url, 'referrer': referrer}
    try:
        raw = _default_http_fetch(url, 15, referer=referrer)
        digest = hashlib.sha256(raw).hexdigest()
        (out / (digest + '.txt')).write_bytes(raw)
        text = raw.decode('utf-8', errors='replace')
        row.update(sha256=digest, bytes=len(raw))
        if raw.lstrip().startswith((b'{', b'[')) and len(raw) <= 2000000:
            row['public_json'] = json.loads(raw)
            row['public_response_zlib_base64'] = base64.b64encode(zlib.compress(raw)).decode()
            if url == NSE_LISTING:
                for page, api in nse_issue_links(raw, issuer):
                    queue.append((api, page))
        matches = list(pattern.finditer(text))
        row['keyword_count'] = len(matches)
        row['contexts'] = [text[max(0, m.start()-350):m.end()+900] for m in matches[:60]]
        targets = []
        if '<app-root' in text or '<html' in text[:100].lower():
            base_match = re.search(r'<base\b[^>]*href=["\']([^"\']+)', text, re.I)
            document_base = urljoin(url, base_match.group(1)) if base_match else url
            for src in re.findall(r'<script\b[^>]*\bsrc=["\']([^"\']+)', text, re.I):
                if re.search(r'(?:^|/)env\.js$|(?:^|/)main-[^/]+\.js$', src):
                    targets.append(urljoin(document_base, src))
        else:
            # Lazy route asset names near an IPO/public-issue route. These
            # are the publisher's actual import literals, not guessed paths.
            imports = re.findall(r'import\s*\{[^}]+\}\s*from\s*["\'][^"\']+["\']', text)
            row['module_imports'] = imports[:40]
            for statement in imports:
                if re.search(r'\bas\s+I\b', statement):
                    match = re.search(r'from\s*["\']([^"\']+)["\']', statement)
                    if match:
                        targets.append(match.group(1))
            row['public_service_urls'] = list(dict.fromkeys(re.findall(
                r'https://[^"\'\s<>]*bseindia\.com[^"\'\s<>]*', text)))[:50]
            row['contract_contexts'] = []
            for term in ('IS_INTERNATIONAL', 'BseIndiaAPI', 'GetPublicIssue_par_updated', 'GetMkt_ISSUE', 'DisplayIPO',
                         'BSE_Domain_APIUrl', 'IPO_HomePageDetail'):
                row['contract_contexts'].extend(text[max(0, m.start()-450):m.end()+1600]
                    for m in list(re.finditer(re.escape(term), text, re.I))[:8])
            contexts = row['contexts'] + row['contract_contexts']
            for context in contexts:
                targets.extend(re.findall(r'(?:import\s*\(|from\s*)["\']([^"\']+\.js)["\']', context))
            row['api_literals'] = list(dict.fromkeys(re.findall(
                r'["\']([^"\'\s]{0,100}(?:PublicIssue|Pubissues|GetMkt_ISSUE|IPO_)[^"\'\s]{0,180})["\']', text, re.I)))[:80]
            if url.endswith('env.js'):
                row['public_environment_source'] = text[:15000]
                match = re.search(r'BSE_Domain_APIUrl.{0,12}[:=]\s*["\'](https://[^"\']+)', text)
                if match:
                    api_base = match.group(1)
            if api_base:
                for literal in row['api_literals']:
                    if literal == '/GetPublicIssue_par_updated/w?flag=1':
                        linked = api_base.rstrip('/') + literal
                        if urlparse(linked).hostname == 'api.bseindia.com':
                            queue.append((linked, 'https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P'))
        for target in dict.fromkeys(targets):
            linked = urljoin(url, target)
            if urlparse(linked).hostname == 'www.bseindia.com' and linked not in seen:
                queue.append((linked, url))
    except Exception:
        row['traceback'] = traceback.format_exc()
    rows.append(row)
    print(json.dumps(row), flush=True)
result = {'scope': 'Actual public BSE SPA contract research and independent raw NSE source audit; not ingestion acceptance', 'requests': rows}
(out / 'bse-source-contract.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
packed = base64.b64encode(zlib.compress(json.dumps(result).encode())).decode()
for index, offset in enumerate(range(0, len(packed), 55000)):
    body = {'name': f'BSE published SPA contract {index}', 'head_sha': os.environ['GITHUB_SHA'],
        'status': 'completed', 'conclusion': 'neutral', 'output': {'title': 'Public BSE source-contract research',
        'summary': f'Actual production transport, read-only first-party assets; compressed part {index}. Not ingestion acceptance.',
        'text': packed[offset:offset+55000]}}
    req = urllib.request.Request('https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + '/check-runs',
        data=json.dumps(body).encode(), method='POST', headers={
            'Authorization': 'Bearer ' + os.environ['LIVE_CHECK_TOKEN'],
            'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        print('Evidence: ' + json.load(response)['html_url'], flush=True)
