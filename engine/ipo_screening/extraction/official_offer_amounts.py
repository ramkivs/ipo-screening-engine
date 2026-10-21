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


def explicit_amounts(result, pages):
    if not isinstance(result, ExchangeIssueTermsResult):
        result = ExchangeIssueTermsResult(**{f.name: getattr(result, f.name)
                                             for f in fields(PriceBandNoticeResult)})
        result.document_class = 'PRICE_BAND_NOTICE'
    units = {'lakh': 'INR_LAKHS', 'million': 'INR_MILLIONS', 'crore': 'INR_CRORES'}
    for name, label in (('fresh_issue', r'fresh\s+(?:issue|offer)'),
                        ('ofs', r'offer\s+for\s+sale')):
        found = []
        for page, text in pages:
            for m in re.finditer(label + r'\b', text, re.I):
                segment = text[m.end():m.end() + 300]
                amount = re.search(r'aggregating\s+(?:up\s+to\s+|to\s+)?(?:₹|Rs\.?|INR)\s*'
                                   r'(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|millions?|crores?)', segment, re.I)
                if not amount:
                    continue
                before = segment[:amount.start()]
                if re.search(r'offer\s+for\s+sale|fresh\s+(?:issue|offer)|reservation|employee|shareholder|UNREADABLE_OCR_LINE|[●]', before, re.I):
                    continue  # another component, reservation, or a placeholder intervened
                from .exchange_issue_page import _number
                value = _number(amount.group(1))
                if not math.isfinite(value):
                    continue
                word = amount.group(2).lower()
                unit = next(u for k, u in units.items() if word.startswith(k))
                quote = text[m.start():m.end() + amount.end()]
                found.append((value, unit, page, quote))
        unique = {(v, u) for v, u, _, _ in found}
        if len(unique) > 1:
            result.metadata.setdefault('issue_term_errors', {})[name] = 'Conflicting explicit monetary amounts in one document'
        if len(unique) == 1:
            value, unit, page, quote = found[0]
            setattr(result, name + '_amount', PriceBandField(name=name + '_amount',
                value=value, raw_text=quote, quote=quote, page=page,
                locator='Official offer document — explicit ' + name + ' aggregating amount'))
            setattr(result, name + '_amount_unit', unit)
    # Explicit no-OFS wording only, using the already-governed binding guard.
    nil = next(((page, quote) for page, text in pages if (quote := _find_ofs_nil(text))), None)
    if nil and (result.ofs_amount is not None and result.ofs_amount.value > 0 or
                'ofs' in result.metadata.get('issue_term_errors', {})):
        result.ofs_amount = None
        result.ofs_amount_unit = None
        result.metadata.setdefault('issue_term_errors', {})['ofs'] = 'Explicit OFS NIL conflicts with monetary amounts'
    elif nil and result.ofs_amount is None:
        result.ofs_amount = PriceBandField(name='ofs_amount', value=0.0, page=nil[0],
            raw_text=nil[1], quote=nil[1], locator='Official offer document — explicit OFS NIL')
        result.ofs_amount_unit = 'INR_LAKHS'
    return result


def document_pages(raw):
    if raw.startswith(b'%PDF-'):
        from pypdf import PdfReader
        with io.BytesIO(raw) as stream:
            reader = PdfReader(stream)
            return [(i + 1, reader.pages[i].extract_text() or '')
                    for i in range(min(5, len(reader.pages)))]
    return [(1, raw.decode('utf-8', errors='replace'))]


def parse_official_rhp(raw, url):
    pages = document_pages(raw)
    cover = '\n'.join(t for _, t in pages[:2])
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
    return explicit_amounts(result, pages)
