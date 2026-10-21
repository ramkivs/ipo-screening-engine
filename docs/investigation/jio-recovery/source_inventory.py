"""Inventory retained actual production responses; never supplies canonical facts.

Original public response bytes remain in the uploaded evidence artifact. Review
renders are explicitly not parser evidence or an upgrade of OCR confidence.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re


def inspect_sources(sources, review):
    from ipo_screening.official_issue_sources import official_document_members
    from pypdf import PdfReader
    review.mkdir(exist_ok=True)
    inventory = []
    seen = set()
    requests = [json.loads(line) for line in (sources / 'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    for request in requests:
        if 'sha256' not in request or request['sha256'] in seen:
            continue
        seen.add(request['sha256'])
        raw = (sources / (request['sha256'] + '.bin')).read_bytes()
        if not raw.startswith((b'%PDF-', b'PK\x03\x04')):
            continue
        for member, uri in official_document_members(raw, request['url']):
            if not member.startswith(b'%PDF-'):
                continue
            digest = hashlib.sha256(member).hexdigest()
            (sources / (digest + '.pdf')).write_bytes(member)
            row = {'uri': uri, 'sha256': digest, 'bytes': len(member),
                   'role': 'DIAGNOSTIC_ONLY; no new canonical assertions'}
            try:
                reader = PdfReader(io.BytesIO(member))
                row['page_count'] = len(reader.pages)
                row['fresh_contexts'] = []
                row['page_read_failures'] = []
                row['native_text_pages'] = 0
                for number, page in enumerate(reader.pages, 1):
                    try:
                        text = page.extract_text() or ''
                    except Exception as exc:
                        row['page_read_failures'].append({'page': number, 'error': repr(exc)})
                        continue
                    row['native_text_pages'] += bool(text.strip())
                    for match in re.finditer(r'fresh\s+(?:issue|offer)', text, re.I):
                        row['fresh_contexts'].append({'page': number,
                            'text': text[max(0, match.start()-80):match.end()+700]})
                if row['native_text_pages'] == 0 and len(reader.pages) <= 6:
                    import pypdfium2 as pdfium
                    with pdfium.PdfDocument(member) as doc:
                        row['review_images'] = []
                        for number in range(len(doc)):
                            page = doc[number]
                            bitmap = page.render(scale=min(3.0, 4500 / max(page.get_size())))
                            image = bitmap.to_pil().convert('RGB')
                            try:
                                header = image.crop((0, 0, image.width, min(1600, image.height)))
                                mono = header.convert('1')
                                target = review / f'{digest[:12]}-page-{number+1}-top.png'
                                mono.save(target)
                                row['review_images'].append({'page': number+1, 'width': mono.width,
                                    'height': mono.height, 'crop': 'top 1600 rendered pixels only; NOT whole-page examination',
                                    'render': 'bilevel diagnostic; original PDF retained unchanged',
                                    'name': target.name, 'png_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                                    **({'png_base64': base64.b64encode(target.read_bytes()).decode()}
                                       if os.getenv('JIO_RECOVERY_INLINE_REVIEW') == '1' else {})})
                                mono.close()
                                header.close()
                            finally:
                                image.close()
                                bitmap.close()
                                page.close()
            except Exception:
                import traceback
                row['diagnostic_traceback'] = traceback.format_exc()
            inventory.append(row)
    return inventory
