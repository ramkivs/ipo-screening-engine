"""Explicit monetary offer components from issuer-matched official attachments.

No total-issue substitution, reservation subtotal, shares-times-price inference,
or absent-OFS-to-zero default. Existing OFS NIL binding is reused unchanged.
RHP terms remain a distinct document class, never relabelled final Prospectus.
"""
from dataclasses import fields
import hashlib
import io
import math
import re

from ..canonical import SourceRef, SourceType
from .exchange_issue_page import ExchangeIssueTermsResult
from .interfaces import SourceDocument
from .price_band_notice import PriceBandField, PriceBandNoticeResult
from .prospectus_terms import ProspectusTermsParser
from .sections import _find_ofs_nil


def explicit_amounts(result, pages, table_columns=()):
    if not isinstance(result, ExchangeIssueTermsResult):
        result = ExchangeIssueTermsResult(**{f.name: getattr(result, f.name)
                                             for f in fields(PriceBandNoticeResult)})
        result.document_class = 'PRICE_BAND_NOTICE'
    diagnostics = result.metadata.setdefault('issue_term_diagnostics', [])
    table_pages = {column['page'] for column in table_columns}
    units = {'lakh': 'INR_LAKHS', 'million': 'INR_MILLIONS', 'crore': 'INR_CRORES'}
    for name, label in (('fresh_issue', r'fresh\s+(?:issue|offer)'),
                        ('ofs', r'offer\s+for\s+sale')):
        found = []
        inputs = [(page, text, None) for page, text in pages if page not in table_pages]
        for column in table_columns:
            if column['component'] == name:
                for cell in column['cells']:
                    # Reject category/face-value/subtotal runs, even in an
                    # apparently aligned cell. Never merge adjacent runs.
                    if re.search(r'reservation|employee|shareholder|anchor|face\s+value|total\s+(?:issue|offer)', cell['text'], re.I):
                        continue
                    label_text = 'Fresh Issue' if name == 'fresh_issue' else 'Offer for Sale'
                    inputs.append((column['page'], label_text + '\n' + cell['text'], cell))
        for page, text, cell in inputs:
            for m in re.finditer(label + r'\b', text, re.I):
                segment = text[m.end():m.end() + 300]
                amount = re.search(r'aggregating\s+(?:up\s+to\s+|to\s+)?(?:₹|Rs\.?|INR)\s*'
                                   r'(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|millions?|crores?)', segment, re.I)
                assertion = re.split(r'fresh\s+(?:issue|offer)|offer\s+for\s+sale|total\s+(?:issue|offer)|reservation|employee|shareholder|anchor', segment, maxsplit=1, flags=re.I)[0]
                if re.search(r'\[\s*[●•.\- ]+\s*\]|\bTBD\b', assertion, re.I):
                    diagnostics.append({'code': 'SOURCE_PLACEHOLDER', 'field': name,
                        'page': page, 'quote': cell['text'] if cell else text[m.start():m.end()+len(assertion)],
                        'method': 'NATIVE_TABLE' if cell else ('OCR' if result.metadata.get('ocr') else 'NATIVE_TEXT'),
                        'coordinates': {'x': cell['x'], 'y': cell['y']} if cell else None})
                if not amount:
                    continue
                before = segment[:amount.start()]
                if re.search(r'offer\s+for\s+sale|fresh\s+(?:issue|offer)|reservation|employee|shareholder|anchor|total\s+(?:issue|offer)|UNREADABLE_OCR_LINE|[●]|\bTBD\b|\[\s*\]', before, re.I):
                    continue  # another component, reservation, or a placeholder intervened
                from .exchange_issue_page import _number
                value = _number(amount.group(1))
                if not math.isfinite(value):
                    continue
                word = amount.group(2).lower()
                unit = next(u for k, u in units.items() if word.startswith(k))
                quote = text[m.start():m.end() + amount.end()]
                found.append((value, unit, page, cell['text'] if cell else quote, cell))
        unique = {(v, u) for v, u, _, _, _ in found}
        if len(unique) > 1:
            result.metadata.setdefault('issue_term_errors', {})[name] = 'Conflicting explicit monetary amounts in one document'
        if len(unique) == 1:
            value, unit, page, quote, cell = found[0]
            setattr(result, name + '_amount', PriceBandField(name=name + '_amount',
                value=value, raw_text=quote, quote=quote, page=page,
                locator=('Native offer-table column ' + name + '; original text run x=' + str(cell['x']) + ', y=' + str(cell['y']) if cell else 'Official offer document — explicit ' + name + ' aggregating amount')))
            setattr(result, name + '_amount_unit', unit)
    # Explicit no-OFS wording only, using the already-governed binding guard.
    nil_inputs = [(page, text, None) for page, text in pages if page not in table_pages]
    for column in table_columns:
        if column['component'] == 'ofs':
            nil_inputs.extend((column['page'], 'Offer for Sale\n' + cell['text'], cell) for cell in column['cells'])
    nil = next(((page, cell['text'] if cell else quote, cell) for page, text, cell in nil_inputs if (quote := _find_ofs_nil(text))), None)
    if nil and (result.ofs_amount is not None and result.ofs_amount.value > 0 or
                'ofs' in result.metadata.get('issue_term_errors', {})):
        result.ofs_amount = None
        result.ofs_amount_unit = None
        result.metadata.setdefault('issue_term_errors', {})['ofs'] = 'Explicit OFS NIL conflicts with monetary amounts'
    elif nil and result.ofs_amount is None:
        result.ofs_amount = PriceBandField(name='ofs_amount', value=0.0, page=nil[0],
            raw_text=nil[1], quote=nil[1], locator=('Native offer-table column ofs; original text run x=' + str(nil[2]['x']) + ', y=' + str(nil[2]['y']) if nil[2] else 'Official offer document — explicit OFS NIL'))
        result.ofs_amount_unit = 'INR_LAKHS'
    return result


def document_pages(raw, max_pages=5, diagnostics=None):
    if raw.startswith(b'%PDF-'):
        from pypdf import PdfReader
        with io.BytesIO(raw) as stream:
            reader = PdfReader(stream)
            pages = []
            limit = min(max_pages, len(reader.pages))
            if diagnostics is not None:
                diagnostics.update(total_pages=len(reader.pages), page_limit=max_pages,
                                   pages_examined=limit, complete_document=limit == len(reader.pages),
                                   page_read_errors=[])
            for i in range(limit):
                try:
                    pages.append((i + 1, reader.pages[i].extract_text() or ''))
                except Exception as exc:
                    if diagnostics is None:
                        raise
                    diagnostics['page_read_errors'].append({'page': i+1, 'error': str(exc)})
                    diagnostics['complete_document'] = False
            return pages
    return [(1, raw.decode('utf-8', errors='replace'))]


def parse_official_rhp(raw, url):
    read_scope = {}
    pages = document_pages(raw, max_pages=30, diagnostics=read_scope)
    cover = '\n'.join(t for page, t in pages if page <= 2)
    # A dated document title, not a mention of an RHP elsewhere in a notice.
    if re.search(r'\bDraft\s+Red\s+Herring\s+Prospectus\s*(?:Dated|Date)\s*:', cover, re.I):
        raise ValueError('Draft Red Herring Prospectus cannot be promoted to current RHP terms')
    dated = re.search(r'Red\s+Herring\s+Prospectus\s*\n?\s*(?:Dated|Date)\s*:', cover, re.I)
    # Some filed RHP covers have a graphical (non-text) dated title. Their
    # explicit issuer responsibility statement and complete offer-table header
    # establish the document role without inventing a publication date.
    cover_role = (re.search(r'this\s+Red\s+Herring\s+Prospectus\s+c\s*ontains\s+all\s+information', cover, re.I)
                  and re.search(r'FRESH\s+ISSUE\s+SIZE\s+OFFER\s+FOR\s+SALE\s+SIZE\s+TOTAL\s+ISSUE\s+SIZE', cover, re.I))
    if not (dated or cover_role) or re.search(r'GENERAL\s+INFORMATION\s+DOCUMENT', cover[:1500], re.I):
        raise ValueError('RHP title or issuer responsibility/offer-table role not established')
    cin = re.search(r'\b[LU]\d{5}[A-Z]{2}\d{4}PLC\d{6}\b', cover)
    name = ProspectusTermsParser._extract_company_name(cover)
    if not cin or not name:
        raise ValueError('RHP issuer name/CIN not established')
    digest = hashlib.sha256(raw).hexdigest()
    sid = 'SRC-OFFICIAL-RHP-' + digest[:8].upper()
    result = ExchangeIssueTermsResult(source=SourceDocument(source_id=sid,
        source_type=SourceType.RHP.value, uri=url, content_hash=digest),
        source_ref=SourceRef(source_id=sid, source_type=SourceType.RHP.value,
                             uri=url, content_hash=digest),
        company_name=name, is_classified_notice=False,
        metadata={'document_class': 'OFFICIAL_RHP_TERMS'})
    result.cin = cin.group()
    result.document_class = 'OFFICIAL_RHP_TERMS'
    columns = []
    if raw.startswith(b'%PDF-'):
        from pypdf import PdfReader
        from .offer_table import component_columns
        with io.BytesIO(raw) as stream:
            reader = PdfReader(stream)
            for number, _ in pages:
                try:
                    columns.extend(component_columns(reader.pages[number-1], number))
                except Exception as exc:
                    read_scope.setdefault('layout_read_errors', []).append({'page': number, 'error': str(exc)})
    result.metadata['native_read_scope'] = read_scope
    result.metadata['offer_table_columns'] = columns
    result.metadata['linear_text_excluded_table_pages'] = sorted({column['page'] for column in columns})
    return explicit_amounts(result, pages, columns)
