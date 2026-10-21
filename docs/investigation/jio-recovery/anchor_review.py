"""Read-only original-page OCR review of the actually linked anchor report.
All text remains UNVERIFIED diagnostic evidence, never canonical issue terms.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import time
import traceback
import urllib.request
import zipfile
import zlib

from ipo_screening.issue_terms import _default_http_fetch
from ipo_screening.extraction.official_notice_ocr import _engine

out = Path(os.environ['JIO_RECOVERY_OUTPUT'])
out.mkdir(parents=True, exist_ok=True)
uri = 'https://nsearchives.nseindia.com/content/ipo/ANCHOR_JPL.zip'
result = {'uri': uri, 'scope': 'Read-only diagnostic, no terms promoted; original full pages, no numeric repair', 'pages': []}
try:
    raw = _default_http_fetch(uri, 30, referer='https://www.nseindia.com/api/ipo-detail?symbol=JPL')
    result['archive_sha256'] = hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = [e for e in archive.infolist() if not e.is_dir()]
        assert len(entries) == 1 and entries[0].file_size < 16 * 1024 * 1024
        result['member'] = entries[0].filename
        body = archive.read(entries[0])
    result['document_sha256'] = hashlib.sha256(body).hexdigest()
    assert result['document_sha256'] == 'f4122541c1898af248edb2eb50a8e3cd154a2749c551c130b58130ea30893ef4', 'source changed; review new document independently'
    (out / 'anchor-original.pdf').write_bytes(body)
    import pypdfium2 as pdfium
    import numpy as np
    engine = _engine()
    started = time.monotonic()
    with pdfium.PdfDocument(body) as doc:
        result['page_count'] = len(doc)
        assert len(doc) <= 24
        for index in range(len(doc)):
            if time.monotonic() - started > 540:
                raise TimeoutError('bounded diagnostic OCR budget exhausted; not absence')
            page = doc[index]
            bitmap = page.render(scale=min(3, 2800 / max(page.get_size())))
            image = bitmap.to_pil().convert('RGB')
            try:
                detected = engine(np.asarray(image))
                item = {'original_page': index+1, 'verification': 'UNVERIFIED',
                        'lines': [{'text': text, 'confidence': float(score)} for text, score in zip(
                            getattr(detected, 'txts', None) or (), getattr(detected, 'scores', None) or ())]}
                image_path = out / f'anchor-page-{index+1:02}.png'
                image.save(image_path)
                item['image_sha256'] = hashlib.sha256(image_path.read_bytes()).hexdigest()
                if index < 2:
                    item['original_page_png_base64'] = base64.b64encode(image_path.read_bytes()).decode()
                result['pages'].append(item)
                print('Reviewed original anchor page', index+1, 'lines', len(item['lines']), flush=True)
            finally:
                image.close()
                bitmap.close()
                page.close()
    result['elapsed_seconds'] = time.monotonic() - started
    result['complete_ocr_invocation'] = True
except Exception:
    result['traceback'] = traceback.format_exc()
    result['complete_ocr_invocation'] = False
(out / 'anchor-review.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
packed = base64.b64encode(zlib.compress(json.dumps(result).encode())).decode()
for index, offset in enumerate(range(0, len(packed), 55000)):
    payload = {'name': f'Anchor original-page review {index}', 'head_sha': os.environ['GITHUB_SHA'],
        'status': 'completed', 'conclusion': 'neutral', 'output': {'title': 'Actual anchor allocation report review',
        'summary': 'Original-page OCR is diagnostic only, not ingestion acceptance or verified financial terms.',
        'text': packed[offset:offset+55000]}}
    req = urllib.request.Request('https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + '/check-runs',
        data=json.dumps(payload).encode(), method='POST', headers={'Authorization': 'Bearer ' + os.environ['LIVE_CHECK_TOKEN'],
        'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        print('Evidence:', json.load(response)['html_url'], flush=True)
if result.get('traceback'):
    raise RuntimeError(result['traceback'])
