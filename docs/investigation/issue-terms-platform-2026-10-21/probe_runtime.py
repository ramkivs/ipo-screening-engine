"""Read-only transport reproduction; no ingestion, evaluation, cache or persistence.
Run from repository root: PYTHONPATH=engine .venv/bin/python docs/investigation/issue-terms-platform-2026-10-21/probe_runtime.py
Public URLs below were observed through page links; this is not production configuration.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from ipo_screening.issue_terms import _default_http_fetch

URLS = [
    'https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P',
    'https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4894&type=IPO&idtype=1&status=L&IPONo=8047&startdt=21/10/2026',
    'https://listing.bseindia.com/Download/8888888/PreAnchor/JioPlatformsPBAdNewspaperClippings_20261015185329.zip',
    'https://www.bseindia.com/downloads/UploadDocs/Notices/20261019-46/20261019-46.pdf',
    'https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1792045029108.pdf',
    'https://www.nseindia.com/market-data/all-upcoming-issues-ipo',
    'https://www.nseindia.com/market-data/issue-information?symbol=JPL&series=EQ&type=Active',
    'https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=4894&type=IPO&status=F',
    'https://www.sebi.gov.in/filings/public-issues/oct-2026/jio-platforms-limited-rhp_105274.html',
    'https://dhan.co/ipo/',
    'https://dhan.co/ipo/jio-platforms-ipo/',
    'https://groww.in/ipo',
    'https://www.angelone.in/ipo/reliance-jio-ipo',
    'https://www.indmoney.com/ipo/reliance-jio-ipo',
    'https://myjiostatic.cdn.jio.com/cms/assets/iv3/Red%20Herring%20Prospectus.pdf',
]
results = []
for url in URLS:
    row = {'url': url, 'attempted_at': datetime.now(timezone.utc).isoformat(),
           'transport': 'production _default_http_fetch, 3 second per-request timeout, existing bounded retries'}
    try:
        raw = _default_http_fetch(url, 3)
        row.update(status='RETRIEVED_NOT_VERIFIED', bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    except Exception as exc:
        row.update(status='RETRIEVAL_FAILED_NOT_PUBLICATION_EVIDENCE', error_type=type(exc).__name__, error=str(exc))
    results.append(row)
    print(json.dumps(row), flush=True)
Path(__file__).with_name('runtime-transport.json').write_text(json.dumps(results, indent=2) + '\n')
