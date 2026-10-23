"""Bounded, offline OCR for image-only official offer notices.

Models ship in the pinned RapidOCR wheel. Explicit local model paths prevent
runtime model downloads. No CAPTCHA rendering, OCR-based access-control bypass,
number repair, currency guessing or issuer aliases. Low-confidence lines remain
unreadable markers, never silently spliced into a different assertion.
"""
from dataclasses import replace
import hashlib
import logging
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

# Fixed structural vocabulary only. OCR engines merge inter-word spaces inside
# these headings (the same image yields "INITIAL PUBLIC OFFERING OF" on one
# host and "INITIAL PUBLICOFFERINGOF" on another). Restoring a known phrase is
# not repair of issuer letters, digits or amounts.
_HEADING_VOCABULARY = ('PRICE BAND ADVERTISEMENT', 'INITIAL PUBLIC OFFERING OF',
                       'FLOOR PRICE', 'CAP PRICE', 'PRICE BAND', 'FRESH ISSUE',
                       # The one wording the offer parser requires to bind a
                       # fresh-issue amount; the runner merged it as
                       # "aggregatingup toRs 240million".
                       'AGGREGATING UP TO',
                       # Same merge class on the OFS row; both are fixed
                       # structural phrases, and restoring them keeps an
                       # explicit "Offer for Sale: Not applicable" readable.
                       'OFFER FOR SALE', 'NOT APPLICABLE')
# The legal suffix is another fixed token: OCR may emit "...ACMEFORGELIMITED"
# with no space before LIMITED. Splitting the suffix restores the ordinary
# spelling of the issuer's own heading; it never inserts, deletes, repairs or
# guesses an issuer letter, digit or name, and an all-caps word that merely
# ends in the suffix (UNLIMITED) is left untouched.
_FUSED_LEGAL_SUFFIX = re.compile(r'(?<![A-Za-z0-9])([A-Z][A-Z0-9&,.\-]{1,60}?)(LIMITED|LTD)(?![A-Za-z0-9])')
_NOT_A_NAME_STEM = {'UN', 'NON'}


def _restore_heading_spacing(text):
    """Normalize merged spaces in fixed headings on every OCR text form.

    Applied identically to the identity header and to the financial crops, so
    one engine's segmentation cannot make the issuer heading readable in one
    form and unreadable in the other.
    """
    for words in _HEADING_VOCABULARY:
        text = re.sub(r'(?i)\b' + r'\s*'.join(words.split()), words + ' ', text)

    def split_suffix(match):
        if match.group(1) in _NOT_A_NAME_STEM:
            return match.group(0)
        return match.group(1) + ' ' + match.group(2)

    return _FUSED_LEGAL_SUFFIX.sub(split_suffix, text)


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
                        identity_pages.append((1, _restore_heading_spacing('\n'.join(
                            t if score >= .95 else '[UNREADABLE_OCR_LINE]'
                            for t, score in zip(texts, scores)))))
                    finally:
                        header.close()
                for left in range(0, image.width, 1480):
                    for top in range(0, image.height, 1480):
                        crop = image.crop((left, top, min(left + 1600, image.width), min(top + 1600, image.height)))
                        try:
                            detected = engine(np.asarray(crop))
                            texts = getattr(detected, 'txts', None) or ()
                            scores = getattr(detected, 'scores', None) or ()
                            text = _restore_heading_spacing('\n'.join(
                                t if score >= .95 else '[UNREADABLE_OCR_LINE]'
                                for t, score in zip(texts, scores)))
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
    # The native 5-page TOI notice took 178.8s in a successful run and
    # exceeded the former fixed 180s in retained runs. Allow 45s per
    # sampled page plus one reserve (the native-text sampler stops at five,
    # the OCR worker rejects more than six). This remains <=270s, not an
    # unbounded ingestion-worker deadline or permission to use partial OCR.
    read_budget = max(180, 45 * (len(native) + 1))
    with _LOCK:
        try:
            proc = subprocess.run([sys.executable, '-m', __name__], input=raw,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=read_budget, check=False)
        except subprocess.TimeoutExpired as exc:
            logging.getLogger(__name__).error(
                'Official OCR timeout: budget=%s interpreter=%s module=%s document_sha256=%s; stderr=%s',
                read_budget, sys.executable, __name__, hashlib.sha256(raw).hexdigest(),
                (exc.stderr or b'').decode('utf-8', errors='replace'))
            raise ValueError(f'official image notice OCR exceeded bounded {read_budget}-second read budget') from exc
    if proc.returncode:
        # Preserve the actual complete child traceback in the server log;
        # the UI/provider note remains bounded and is never parsed as facts.
        logging.getLogger(__name__).error(
            'Official OCR child failed: exit=%s interpreter=%s module=%s document_sha256=%s; stderr=%s',
            proc.returncode, sys.executable, __name__, hashlib.sha256(raw).hexdigest(),
            proc.stderr.decode('utf-8', errors='replace'))
        raise ValueError('official image notice OCR failed: ' + proc.stderr.decode('utf-8', errors='replace')[-500:])
    decoded = json.loads(proc.stdout)
    # Idempotent: the child already normalises, and re-applying it keeps every
    # OCR output form (identity header, financial crops, any retained payload)
    # on one spelling rule without repairing issuer letters or digits.
    pages = [(page, _restore_heading_spacing(text)) for page, text in decoded['pages']]
    identity_pages = [(page, _restore_heading_spacing(text)) for page, text in decoded['identity_pages']]
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
        'read_budget_seconds': read_budget,
        'pages': sorted({number for number, _ in pages}), 'numeric_repair': False,
        'normalization': 'fixed structural vocabulary and legal-suffix separation only'}
    return result


if __name__ == '__main__':
    # Isolated read-only worker: no API/server/store imports and no model downloads.
    print(json.dumps(_ocr_pages(sys.stdin.buffer.read()), ensure_ascii=True))
