"""Read-only live exchange retrieval; never substitutes authored source content.

Run with PYTHONPATH=engine python <this file>. Public HTTP requests use the
production cookie/retry transport. No cookies or credentials are logged.
GitHub notices retain bounded compressed public response bytes for independent
parser replay, plus URL/hash/classification. No canonical fact is made from a
research-tool rendering. This first-stage probe does not evaluate or persist.
"""
import base64
import hashlib
import json
import os
import zlib
from datetime import datetime, timezone

from ipo_screening.issue_terms import OfficialDiscoveryProvider, _default_http_fetch

urls = list(OfficialDiscoveryProvider.LISTING_URLS) + [
    'https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4894&type=IPO&idtype=1&status=L&IPONo=8047&startdt=21/10/2026',
    'https://www.nseindia.com/api/all-upcoming-issues?category=ipo',
    'https://www.nseindia.com/api/ipo-detail?symbol=JPL',
]

def emit(row):
    text = json.dumps(row, separators=(',', ':'))
    print(text, flush=True)
    if os.getenv('GITHUB_ACTIONS'):
        escaped = text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print('::notice title=Live official retrieval::' + escaped, flush=True)

for url in urls:
    row = {'url': url, 'at': datetime.now(timezone.utc).isoformat(),
           'transport': 'production _default_http_fetch; actual public HTTP, no fixture'}
    try:
        raw = _default_http_fetch(url, 5)
        row.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                   classification=OfficialDiscoveryProvider._classify_listing(raw))
        packed = base64.b64encode(zlib.compress(raw)).decode()
        if len(packed) <= 45000:
            row['zlib_base64_public_response'] = packed
        else:
            row['response_not_in_annotation'] = 'compressed response exceeds bounded annotation size'
    except Exception as exc:
        row.update(error_type=type(exc).__name__, error=str(exc),
                   state='RETRIEVAL_FAILED_NOT_NONPUBLICATION')
    emit(row)
