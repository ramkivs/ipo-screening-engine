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

_LOCK = threading.RLock()
_ENGINE = None


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
                       'EngineConfig.onnxruntime.intra_op_num_threads': 1,
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
    with _LOCK, pdfium.PdfDocument(raw) as doc:
        if len(doc) > 6:
            raise ValueError('image-only official notice exceeds six-page OCR limit')
        engine = _engine()
        for index in range(len(doc)):
            page = doc[index]
            scale = min(3.0, 6000 / max(page.get_size()))
            bitmap = page.render(scale=scale)
            image = bitmap.to_pil().convert('RGB')
            try:
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
    return output


def reject_general_information(pages):
    # GIDs teach hypothetical prices; bundling with an issuer's RHP does not
    # make those examples issuer-specific disclosures. Guard outside the frozen
    # notice parser, preserving its hashes and original contracts.
    text = '\n'.join(text for _, text in pages)[:2000]
    if re.search(r'^\s*GENERAL\s+INFORMATION\s+DOCUMENT(?:\s+FOR\s+INVESTING\s+IN\s+PUBLIC\s+ISSUES)?\s*$|^\s*This\s+General\s+Information\s+Document\s+highlights', text, re.I | re.M):
        raise ValueError('General Information Document examples are not issuer issue terms')


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
    pages = _ocr_pages(raw)
    reject_general_information(pages)
    from .interfaces import SourceDocument
    from .price_band_notice import PriceBandNoticeParser
    digest = hashlib.sha256(raw).hexdigest()
    source = SourceDocument(source_id='SRC-PBN-' + digest[:8].upper(), source_type='EXCHANGE',
                            uri=url, content_hash=digest, file_size_bytes=len(raw))
    result = PriceBandNoticeParser().parse_document(source, pages)
    result = explicit_amounts(result, pages)
    for name in ('price_band_low', 'price_band_high', 'lot_size', 'open_date', 'close_date',
                 'fresh_issue_amount', 'ofs_amount'):
        obj = getattr(result, name, None)
        if obj is not None:
            if '[UNREADABLE_OCR_LINE]' in (obj.quote or ''):
                setattr(result, name, None)
            else:
                setattr(result, name, replace(obj, extraction_method='OCR', confidence=.95,
                    locator='Offline OCR; original PDF page ' + str(obj.page) + '; ' + (obj.locator or 'notice')))
    result.metadata['ocr'] = {'engine': 'rapidocr-3.10.0 bundled PP-OCRv6 ONNX',
        'minimum_line_confidence': .95, 'segments': len(pages),
        'pages': sorted({number for number, _ in pages}), 'numeric_repair': False, 'normalization': 'fixed structural heading whitespace only'}
    return result
