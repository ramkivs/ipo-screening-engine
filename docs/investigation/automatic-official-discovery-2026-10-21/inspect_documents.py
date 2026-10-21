"""Actual discovered archive diagnostics, not canonical input or evaluation."""
import hashlib
import json
import os
import re
from ipo_screening.issue_terms import _default_http_fetch, HttpNoticeProvider, _norm_name
from ipo_screening.official_issue_sources import NSE_LISTING, nse_issue_links, links, official_document_members
from ipo_screening.extraction.official_offer_amounts import parse_official_rhp, document_pages


def emit(row):
    text = json.dumps(row, separators=(',', ':'), default=str)
    print(text, flush=True)
    if os.getenv('GITHUB_ACTIONS'):
        print('::notice title=Actual official document parser::' + text.replace('%', '%25').replace('\n', '%0A'), flush=True)


listing = _default_http_fetch(NSE_LISTING, 5)
for page, api in nse_issue_links(listing, 'Jio Platforms Limited'):
    raw = _default_http_fetch(api, 5, referer=page)
    for uri, title in links(raw, api):
        if not re.search('ratios|prospectus|rhp', title, re.I) or not uri.endswith('.zip'):
            continue
        try:
            archive = _default_http_fetch(uri, 5, referer=page)
            for member, member_uri in official_document_members(archive, uri):
                pages = document_pages(member)
                candidate, report = HttpNoticeProvider({'JIO': member_uri}, fetcher=lambda url: member).find('Jio Platforms Limited', 'JIO')
                row = {'uri': member_uri, 'bytes': len(member), 'sha256': hashlib.sha256(member).hexdigest(),
                       'notice_values': candidate.values if candidate else None,
                       'notice_report': report.detail[:700], 'first_page_prefix': pages[0][1][:450]}
                if candidate:
                    row['quotes'] = {name: getattr(candidate.result, name).quote for name in ('price_band_low', 'price_band_high', 'lot_size') if getattr(candidate.result, name, None)}
                try:
                    rhp = parse_official_rhp(member, member_uri)
                    row['rhp'] = {'company': rhp.company_name, 'ofs': rhp.ofs_amount.value if rhp.ofs_amount else None, 'fresh': rhp.fresh_issue_amount.value if rhp.fresh_issue_amount else None}
                except Exception as exc:
                    row['rhp_error'] = type(exc).__name__ + ': ' + str(exc)
                text = '\n'.join(t for _, t in pages[:2])
                row['offer_excerpts'] = [m.group(0)[:500] for m in list(re.finditer(r'.{0,20}(?:fresh\s+issue|offer\s+for\s+sale|red\s+herring|aggregating).{0,160}', text, re.I))[:4]]
                emit(row)
        except Exception as exc:
            emit({'uri': uri, 'error': type(exc).__name__ + ': ' + str(exc)})
