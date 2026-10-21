"""Bounded, offline OCR for image-only official offer notices.

Models ship in the pinned RapidOCR wheel. Explicit local model paths prevent
runtime model downloads. No CAPTCHA rendering, OCR-based access-control bypass,
number repair, currency guessing or issuer aliases. Low-confidence lines remain
unreadable markers, never silently spliced into a different assertion.
"""
from dataclasses import replace
import hashlib
import re
from pathlib import Path
import threading
import json
import os
import subprocess
import sys

_LOCK = threading.RLock()
_ENGINE = None
_INFERENCE_THREADS = min(4, os.cpu_count() or 1)


def _engine():
    global _ENGINE
    if _ENGINE is None:
        import rapidocr
        from rapidocr import RapidOCR
        models = Path(rapidocr.__file__).parent / 'models'
        paths = {'Det': models / 'PP-OCRv6_det_small.onnx',
                 'Rec': models / 'PP-OCRv6_rec_small.onnx',
                 'Cls': models / 'ch_ppocr_mobile_v2.0_cls_mobile.onnx'}
        if not all(p.is_file() for p in paths.values()):
            raise ValueError('bundled official-notice OCR models unavailable; no download attempted')
        params = {name + '.model_path': str(path) for name, path in paths.items()}
        params.update({'Global.log_level': 'error', 'Global.max_side_len': 2000,
                       'Det.limit_side_len': 1600, 'Det.limit_type': 'max',
                       'EngineConfig.onnxruntime.intra_op_num_threads': _INFERENCE_THREADS,
                       'EngineConfig.onnxruntime.inter_op_num_threads': 1})
        _ENGINE = RapidOCR(params=params)
    return _ENGINE


def _ocr_pages(raw):
    import pypdfium2 as pdfium
    import numpy as np
    # One rendered page at a time, bounded pages/pixels/tiles; no huge archive
    # can trigger unlimited rendering. Tiles are separate parsing segments so
    # adjoining columns/crops cannot fabricate one combined monetary assertion.
    output = []
    identity_pages = []
    with _LOCK, pdfium.PdfDocument(raw) as doc:
        if len(doc) > 6:
            raise ValueError('image-only official notice exceeds six-page OCR limit')
        engine = _engine()
        for index in range(len(doc)):
            page = doc[index]
            scale = min(3.0, 4500 / max(page.get_size()))
            bitmap = page.render(scale=scale)
            image = bitmap.to_pil().convert('RGB')
            try:
                if index == 0:
                    # Read the actual complete heading image, never stitch
                    # issuer fragments from different crops. This result is
                    # identity-only: its financial text is never parsed.
                    header = image.crop((0, 0, image.width, min(1600, image.height)))
                    try:
                        detected = engine(np.asarray(header))
                        texts = getattr(detected, 'txts', None) or ()
                        scores = getattr(detected, 'scores', None) or ()
                        identity_pages.append((1, '\n'.join(t if score >= .95 else '[UNREADABLE_OCR_LINE]'
                            for t, score in zip(texts, scores))))
                    finally:
                        header.close()
                for left in range(0, image.width, 1480):
                    for top in range(0, image.height, 1480):
                        crop = image.crop((left, top, min(left + 1600, image.width), min(top + 1600, image.height)))
                        try:
                            detected = engine(np.asarray(crop))
                            texts = getattr(detected, 'txts', None) or ()
                            scores = getattr(detected, 'scores', None) or ()
                            text = '\n'.join(t if score >= .95 else '[UNREADABLE_OCR_LINE]'
                                             for t, score in zip(texts, scores))
                            # OCR may fuse spaces in headings; restore only
                            # fixed vocabulary, never issuer letters/digits.
                            for words in ('PRICE BAND ADVERTISEMENT', 'INITIAL PUBLIC OFFERING OF',
                                          'FLOOR PRICE', 'CAP PRICE', 'PRICE BAND', 'FRESH ISSUE'):
                                text = re.sub(r'(?i)\b' + r'\s*'.join(words.split()), words + ' ', text)
                            output.append((index + 1, text))
                        finally:
                            crop.close()
            finally:
                image.close()
                bitmap.close()
                page.close()
    return {'pages': output, 'identity_pages': identity_pages}


def reject_general_information(pages):
    # GIDs teach hypothetical prices; bundling with an issuer's RHP does not
    # make those examples issuer-specific disclosures. Guard outside the frozen
    # notice parser, preserving its hashes and original contracts.
    text = '\n'.join(text for _, text in pages)[:2000]
    if re.search(r'^\s*GENERAL\s+INFORMATION\s+DOCUMENT(?:\s+FOR\s+INVESTING\s+IN\s+PUBLIC\s+ISSUES)?\s*$|^\s*This\s+General\s+Information\s+Document\s+highlights', text, re.I | re.M):
        raise ValueError('General Information Document examples are not issuer issue terms')


def _primary_issuer_header(pages):
    """Standalone issuer heading immediately followed by its identity/office block.

    Newspaper mastheads must not be swallowed into a legal name by the frozen
    parser's broad fallback. No requested issuer, alias or repaired letters are
    used: the source heading itself must still pass the caller's exact match.
    """
    found = {}
    for page, text in pages:
        if page != 1:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines[:25]):
            match = re.fullmatch(r'([A-Z][A-Z0-9 &,.\-]{2,80}?)(?:\s*LIMITED)', line.strip(), re.I)
            if not match:
                continue
            context = '\n'.join(lines[i + 1:i + 6])
            if not re.search(r'CORPORATE\s*IDENTITY\s*NUMBER|\bCIN\b|REGISTERED\s*OFFICE|TO\s*BE\s*LISTED\s*ON', context, re.I):
                continue
            name = match.group(1).strip() + ' LIMITED'
            found[re.sub(r'[^A-Z0-9]', '', name.upper())] = (name, line.strip())
    if len(found) > 1:
        raise ValueError('conflicting standalone primary issuer headings in OCR notice')
    return next(iter(found.values()), None)


def _has_explicit_price_currency(obj):
    # A face-value multiple or a currency-free OCR chart number is not an INR
    # price. Require the captured assertion to contain its own matching money
    # token. Never compare against another provider or repair OCR digits.
    from .exchange_issue_page import _number
    return any(_number(m.group(1)) == obj.value for m in re.finditer(
        r'(?:₹|\bRs\.?|\bINR)\s*(\d[\d,]*(?:\.\d+)?)', obj.quote or '', re.I))


def parse_if_scanned(raw, url):
    """None means native text exists; errors mean OCR/parse failure, not absence."""
    if not raw.startswith(b'%PDF-'):
        reject_general_information([(1, raw.decode('utf-8', errors='replace'))])
        return None
    from .official_offer_amounts import document_pages, explicit_amounts
    native = document_pages(raw)
    reject_general_information(native)
    if any(len(text.strip()) >= 50 for _, text in native):
        return None
    # The child performs read-only OCR, never evaluation or persistence. It can
    # be stopped safely without the live-worker timeout hazard. No partial OCR
    # output is consumed after a deadline or child failure.
    env = dict(os.environ)
    engine_root = str(Path(__file__).resolve().parents[2])
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [engine_root, env.get('PYTHONPATH')]))
    with _LOCK:
        try:
            proc = subprocess.run([sys.executable, '-m', __name__], input=raw,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=180, check=False)
        except subprocess.TimeoutExpired as exc:
            raise ValueError('official image notice OCR exceeded bounded 180-second read budget') from exc
    if proc.returncode:
        raise ValueError('official image notice OCR failed: ' + proc.stderr.decode('utf-8', errors='replace')[-500:])
    decoded = json.loads(proc.stdout)
    pages = decoded['pages']
    identity_pages = decoded['identity_pages']
    if sum(len(text) for _, text in pages) > 120000:
        raise ValueError('OCR text exceeds bounded official notice size')
    reject_general_information(pages)
    from .interfaces import SourceDocument
    from .price_band_notice import PriceBandNoticeParser
    digest = hashlib.sha256(raw).hexdigest()
    source = SourceDocument(source_id='SRC-PBN-' + digest[:8].upper(), source_type='EXCHANGE',
                            uri=url, content_hash=digest, file_size_bytes=len(raw))
    result = PriceBandNoticeParser().parse_document(source, pages)
    header = _primary_issuer_header(identity_pages) or _primary_issuer_header(pages)
    if header:
        result.company_name = header[0]
        result.metadata['ocr_primary_issuer_quote'] = header[1]
    result.metadata['ocr_header_excerpt'] = (identity_pages[0][1] if identity_pages else pages[0][1] if pages else '')[:650]
    result = explicit_amounts(result, pages)
    for name in ('price_band_low', 'price_band_high', 'lot_size', 'open_date', 'close_date',
                 'fresh_issue_amount', 'ofs_amount'):
        obj = getattr(result, name, None)
        if obj is not None:
            if '[UNREADABLE_OCR_LINE]' in (obj.quote or ''):
                setattr(result, name, None)
            else:
                verified = obj.verification
                if name in ('price_band_low', 'price_band_high') and not _has_explicit_price_currency(obj):
                    verified = 'UNVERIFIED'
                    result.metadata.setdefault('ocr_price_validation', {})[name] = (
                        'Captured OCR assertion lacks an explicit matching INR/Rs/rupee token; '
                        'face-value multiples and currency-free chart numbers are not verified prices')
                setattr(result, name, replace(obj, extraction_method='OCR', confidence=.95,
                    verification=verified, locator='Offline OCR; original PDF page ' + str(obj.page) + '; ' + (obj.locator or 'notice')))
    result.metadata['ocr'] = {'engine': 'rapidocr-3.10.0 bundled PP-OCRv6 ONNX',
        'identity_strategy': 'full-width first-page header; financial fields from original crops only',
        'minimum_line_confidence': .95, 'inference_threads': _INFERENCE_THREADS, 'segments': len(pages),
        'pages': sorted({number for number, _ in pages}), 'numeric_repair': False, 'normalization': 'fixed structural heading whitespace only'}
    return result


if __name__ == '__main__':
    # Isolated read-only worker: no API/server/store imports and no model downloads.
    print(json.dumps(_ocr_pages(sys.stdin.buffer.read()), ensure_ascii=True))
