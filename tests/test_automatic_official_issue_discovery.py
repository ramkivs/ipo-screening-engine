"""Authored protocol fixtures, never represented as actual exchange retrieval.

Live production-transport probes are retained separately under docs/investigation.
"""
import hashlib
import io
import json
import zipfile

import pytest

from ipo_screening.issue_terms import OfficialDiscoveryProvider, IssueTermsResolver
from ipo_screening.official_issue_sources import NSE_LISTING, official_document_members

NAME = 'Acme Forge Limited'
BSE = 'https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P'
DETAIL = 'https://www.bseindia.com/markets/publicIssues/DisplayIPO?id=17&type=IPO&idtype=1&status=L&IPONo=42&startdt=21/10/2026'
NSE_PAGE = 'https://www.nseindia.com/market-data/issue-information?symbol=ACME&series=EQ&type=Active'
NSE_API = 'https://www.nseindia.com/api/ipo-detail?symbol=ACME'
LISTING = f"<table><tr><td><a href='{DETAIL.replace('&', '&amp;')}'>{NAME}</a></td></tr></table>".encode()
# Same masthead as the real BSE issue page; no listing-style linked issue rows.
PAGE = f'''<html><head><title>LIVE Stock/Share Market | BSE SENSEX | BSE (formerly Bombay Stock Exchange)</title></head>
<table><tr><td>{NAME}</td></tr><tr><td>Issue Period</td><td>21 Oct 2026 to 23 Oct 2026</td></tr>
<tr><td>Price Band</td><td>100-120</td></tr><tr><td>Market Lot</td><td>50</td></tr></table></html>'''.encode()


def mapping_fetch(mapping, calls=None):
    def fetch(url):
        if calls is not None:
            calls.append(url)
        if url not in mapping:
            raise OSError('unavailable authored protocol fixture')
        return mapping[url]
    return fetch


def nse_listing(name=NAME):
    return json.dumps([{'companyName': name, 'symbol': 'ACME', 'series': 'EQ', 'status': 'Active'}]).encode()


def nse_detail(band='Rs. 100 to Rs. 120'):
    return json.dumps({'companyName': 'ACME', 'issueInfo': {'dataList': [
        {'title': NAME, 'value': ''}, {'title': 'Issue Period', 'value': '21-Oct-2026 to 23-Oct-2026'},
        {'title': 'Price Range', 'value': band}, {'title': 'Bid Lot', 'value': '50 Equity Shares'}]}}).encode()


def resolve(provider, fields=('price_band_low', 'price_band_high', 'lot_size')):
    return IssueTermsResolver([provider]).resolve(company_name=NAME, ipo_id='ACME-FORGE-LIMITED', missing_fields=list(fields))


def test_bse_detail_shared_masthead_is_not_rejected_as_homepage_and_full_query_survives():
    calls = []
    p = OfficialDiscoveryProvider(fetcher=mapping_fetch({BSE: LISTING, DETAIL: PAGE}, calls), listing_urls=[BSE])
    outcome = resolve(p)
    assert outcome.resolved_fields == ['price_band_low', 'price_band_high', 'lot_size']
    assert calls == [BSE, DETAIL]
    assert outcome.field_diagnostics['lot_size']['candidates'][0]['uri'] == DETAIL
    assert outcome.field_diagnostics['lot_size']['candidates'][0]['content_hash'] == hashlib.sha256(PAGE).hexdigest()


def test_nse_shell_falls_through_to_exact_issuer_feed_then_detail_api():
    calls = []
    html = OfficialDiscoveryProvider.LISTING_URLS[0]
    raw = nse_detail()
    p = OfficialDiscoveryProvider(fetcher=mapping_fetch({html: b'<app-root></app-root>', NSE_LISTING: nse_listing(),
        NSE_PAGE: b'<app-root></app-root>', NSE_API: raw}, calls), listing_urls=[html, NSE_LISTING])
    outcome = resolve(p)
    assert outcome.resolved_fields == ['price_band_low', 'price_band_high', 'lot_size']
    assert calls == [html, NSE_LISTING, NSE_PAGE, NSE_API]
    evidence = outcome.field_diagnostics['price_band_high']['candidates'][0]
    assert evidence['uri'] == NSE_API
    assert evidence['content_hash'] == hashlib.sha256(raw).hexdigest()
    assert outcome.enrichment_payload['sources'][0]['retrieval_timestamp']


@pytest.mark.parametrize('raw', [b'<html>homepage</html>', b'{}', b'null', b'[7]'])
def test_malformed_feed_is_unavailable_not_unpublished(raw):
    outcome = resolve(OfficialDiscoveryProvider(fetcher=lambda url: raw, listing_urls=[NSE_LISTING]))
    assert outcome.status == 'UNAVAILABLE'
    assert not outcome.resolved_fields


def test_no_borrowed_symbol_or_partial_name_match():
    calls = []
    p = OfficialDiscoveryProvider(fetcher=mapping_fetch({NSE_LISTING: nse_listing('Other Acme Limited')}, calls), listing_urls=[NSE_LISTING])
    outcome = resolve(p)
    assert outcome.status == 'UNAVAILABLE' and calls == [NSE_LISTING]


def test_incomplete_official_detail_retains_pricing_but_blocks_missing_amounts():
    p = OfficialDiscoveryProvider(fetcher=mapping_fetch({BSE: LISTING, DETAIL: PAGE}), listing_urls=[BSE])
    outcome = resolve(p, ('price_band_low', 'lot_size', 'ofs', 'fresh_issue'))
    assert outcome.resolved_fields == ['price_band_low', 'lot_size']
    assert outcome.unresolved_fields == ['ofs', 'fresh_issue']
    assert outcome.status == 'PARTIAL'


def test_conflicting_official_exchange_values_are_not_arbitrarily_selected():
    p = OfficialDiscoveryProvider(fetcher=mapping_fetch({BSE: LISTING, DETAIL: PAGE,
        NSE_LISTING: nse_listing(), NSE_PAGE: b'<app-root/>', NSE_API: nse_detail('Rs. 105 to Rs. 125')}),
        listing_urls=[BSE, NSE_LISTING])
    outcome = resolve(p)
    assert outcome.status == 'CONFLICT'
    assert outcome.field_diagnostics['price_band_high']['state'] == 'CONFLICT'
    assert outcome.resolved_fields == ['lot_size']


def archive(member, name='notice.txt'):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as zipped:
        zipped.writestr(name, member)
    return stream.getvalue()


RHP = '''Red Herring Prospectus
Dated: October 15, 2026
ACME FORGE LIMITED
Corporate Identity Number: U12345MH2020PLC123456
Fresh Issue aggregating up to Rs. 240 million
Offer for Sale Size: Not Applicable
'''


def test_official_linked_archive_resolves_explicit_offer_components_with_member_provenance():
    url = 'https://listing.bseindia.com/Download/acme-rhp.zip'
    page = PAGE.replace(b'</html>', f"<a href='{url}'>Prospectus &amp; GID</a></html>".encode())
    p = OfficialDiscoveryProvider(fetcher=mapping_fetch({BSE: LISTING, DETAIL: page, url: archive(RHP)}), listing_urls=[BSE])
    outcome = resolve(p, ('price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue'))
    assert not outcome.unresolved_fields
    evidence = outcome.field_diagnostics['fresh_issue']['candidates'][0]
    assert evidence['value'] == 240 and evidence['unit'] == 'INR_MILLIONS'
    assert evidence['document_class'] == 'OFFICIAL_RHP_TERMS'
    assert evidence['uri'] == url + '#zip-member=notice.txt'
    assert evidence['content_hash'] == hashlib.sha256(RHP.encode()).hexdigest()
    assert outcome.enrichment_payload['ofs_amount']['value'] == 0


def test_foreign_attachment_and_reservation_subtotal_never_resolve_fresh_issue():
    from ipo_screening.extraction.official_offer_amounts import parse_official_rhp
    raw = RHP.replace('Fresh Issue aggregating up to Rs. 240 million',
        'Fresh Issue of 270,000,000 shares (Employee Reservation Portion aggregating up to Rs. 5,000 million)')
    result = parse_official_rhp(raw.encode(), 'https://www.bseindia.com/rhp.pdf')
    assert result.fresh_issue_amount is None
    assert result.ofs_amount.value == 0
    page = PAGE.replace(b'</html>', b'<a href="https://untrusted.example/a.zip">Prospectus</a></html>')
    calls = []
    resolve(OfficialDiscoveryProvider(fetcher=mapping_fetch({BSE: LISTING, DETAIL: page}, calls), listing_urls=[BSE]))
    assert calls == [BSE, DETAIL]


def test_archive_expansion_is_bounded():
    with pytest.raises(ValueError, match='encrypted or oversized'):
        list(official_document_members(_compressed_bomb(), 'https://www.bseindia.com/a.zip'))


def _compressed_bomb():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr('a.pdf', 'a' * 500000)
    return stream.getvalue()


def test_conflicting_labels_in_same_official_page_are_ambiguous():
    page = PAGE.replace(b'</table>', b'<tr><td>Price Band</td><td>110-130</td></tr></table>')
    outcome = resolve(OfficialDiscoveryProvider(fetcher=mapping_fetch({BSE: LISTING, DETAIL: page}), listing_urls=[BSE]))
    assert outcome.field_diagnostics['price_band_high']['state'] == 'MALFORMED_OR_AMBIGUOUS'
    assert outcome.resolved_fields == ['lot_size']


@pytest.mark.parametrize('complete', [True, False])
def test_validated_terms_reach_real_evaluation_and_persistence_only_when_complete(tmp_path, monkeypatch, golden_input, complete):
    import copy
    from conftest import REPO_ROOT
    from ipo_screening.extraction import DocumentExtractor
    from ipo_screening.presentation.service import PresentationConfig, PresentationService, IngestionAwaitingIssueTermsError
    canonical = copy.deepcopy(golden_input)
    issuer = canonical['company_name']
    issue = canonical['issue']
    # Source numbers are authored protocol fixtures, not a claimed live IPO.
    for field in ('price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue'):
        issue[field] = None
    issue['ofs_sellers'] = []
    issue['open_date'], issue['close_date'] = '2026-10-21', '2026-10-23'
    monkeypatch.setattr(DocumentExtractor, 'extract_from_pdf', lambda *a, **k: (copy.deepcopy(canonical), {}))
    url = 'https://www.bseindia.com/downloads/rhp.zip'
    page = PAGE.replace(NAME.encode(), issuer.encode())
    mapping = {BSE: LISTING.replace(NAME.encode(), issuer.encode()), DETAIL: page}
    if complete:
        mapping[DETAIL] = page.replace(b'</html>', f'<a href="{url}">Prospectus &amp; GID</a></html>'.encode())
        mapping[url] = archive(RHP.replace('ACME FORGE LIMITED', issuer.upper()))
    svc = PresentationService(PresentationConfig(store_root=tmp_path / 'evaluations', config_dir=REPO_ROOT / 'config',
        issue_terms_resolver=IssueTermsResolver([OfficialDiscoveryProvider(fetcher=mapping_fetch(mapping), listing_urls=[BSE])])))
    rec = svc.activity_store.new_recorder(filename='synthetic.pdf', mode='final')
    if complete:
        response = svc.ingest_document(b'%PDF-1.4 synthetic', 'synthetic.pdf', 'final', recorder=rec)
        record = svc.eval_store.read(response.evaluation_id)
        assert record is not None
        saved_issue = record['input_snapshot']['input']['issue']
        assert saved_issue['price_band_high'] == 120 and saved_issue['fresh_issue'] is not None
        assert saved_issue['ofs'] == 0
        assert rec.snapshot()['status'] == 'SUCCEEDED' and rec.snapshot()['persisted']
        assert any(e['stage'] == 'persistence' for e in rec.snapshot()['events'])
    else:
        with pytest.raises(IngestionAwaitingIssueTermsError) as raised:
            svc.ingest_document(b'%PDF-1.4 synthetic', 'synthetic.pdf', 'final', recorder=rec)
        assert set(raised.value.missing_fields) == {'ofs', 'fresh_issue'}
        assert not rec.snapshot()['persisted'] and rec.snapshot()['evaluation_id'] is None
        assert not rec.snapshot()['evaluation_run']
    assert svc.get_ingestion_activity(rec.ingestion_id) == rec.snapshot()


def test_cookie_and_parent_referer_sequence_over_real_http_socket(monkeypatch):
    import http.server
    import threading
    import http.cookiejar
    import urllib.request
    from ipo_screening import issue_terms
    # Isolate the real cookie opener so localhost cookies cannot leak to
    # unrelated socket regressions (cookies are scoped by host, not port).
    monkeypatch.setattr(issue_terms, '_SESSION_JAR', http.cookiejar.CookieJar())
    monkeypatch.setattr(issue_terms, '_SESSION_OPENER_READY', False)
    monkeypatch.setattr(urllib.request, '_opener', None)
    seen = []
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get('Cookie'), self.headers.get('Referer')))
            base = f'http://127.0.0.1:{self.server.server_port}'
            if self.path.startswith('/listing'):
                body = f'<table><tr><td><a href="{base}/DisplayIPO?id=17&amp;IPONo=42">{NAME}</a></td></tr></table>'.encode()
            elif 'EXCHANGE=valid' in (self.headers.get('Cookie') or '') and self.headers.get('Referer') == base + '/listing':
                body = PAGE
            else:
                body = b'<html>Exchange homepage</html>'
            self.send_response(200)
            self.send_header('Set-Cookie', 'EXCHANGE=valid; Path=/')
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        listing = f'http://127.0.0.1:{server.server_port}/listing'
        provider = OfficialDiscoveryProvider(allowed_hosts={'127.0.0.1'}, listing_urls=[listing])
        outcome = resolve(provider)
        assert outcome.resolved_fields == ['price_band_low', 'price_band_high', 'lot_size']
        assert seen[1][0] == '/DisplayIPO?id=17&IPONo=42'
        assert 'EXCHANGE=valid' in seen[1][1] and seen[1][2] == listing
    finally:
        server.shutdown()
        server.server_close()
        worker.join(2)


def test_general_information_examples_never_become_official_pricing():
    from ipo_screening.issue_terms import HttpNoticeProvider
    body = '''GENERAL INFORMATION DOCUMENT FOR INVESTING IN PUBLIC ISSUES
INITIAL PUBLIC OFFERING OF ACME FORGE LIMITED
An illustration: the floor price is Rs 20 and the cap price is Rs 24.
The price band of Rs 20 to Rs 24 illustrates book building for investors.
'''
    candidate, report = HttpNoticeProvider({'ACME': 'https://www.bseindia.com/gid.pdf'},
        fetcher=lambda url: body.encode()).find(NAME, 'ACME')
    assert candidate is None and report.outcome == 'REJECTED'
    assert 'General Information Document' in report.detail


def test_graphical_rhp_title_uses_cover_role_and_actual_issuer_cin_not_a_fabricated_date():
    from pathlib import Path
    from conftest import REPO_ROOT
    from ipo_screening.extraction.official_offer_amounts import parse_official_rhp
    raw = (REPO_ROOT / 'evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf').read_bytes()
    result = parse_official_rhp(raw, 'https://www.nseindia.com/discovered-archive.zip#member=rhp.pdf')
    assert result.company_name == 'JIO PLATFORMS LIMITED'
    assert result.cin == 'U72900GJ2019PLC110816'
    assert result.ofs_amount.value == 0
    assert result.fresh_issue_amount is None  # monetary placeholder, not shares * cap
    assert result.source_ref.source_timestamp is None


@pytest.mark.slow
def test_image_only_official_notice_uses_real_offline_ocr_and_preserves_original_pdf_hash():
    import textwrap
    from PIL import Image, ImageDraw, ImageFont
    from ipo_screening.issue_terms import HttpNoticeProvider
    text = '''PRICE BAND ADVERTISEMENT
INITIAL PUBLIC OFFERING OF ACME FORGE LIMITED
NOTICE TO INVESTORS
The Floor Price is Rs 100 per Equity Share and the Cap Price is Rs 120 per Equity Share.
The Price Band is Rs 100 to Rs 120 per Equity Share.
Bids can be made for a minimum of 50 Equity Shares and in multiples of 50 Equity Shares thereafter.
Fresh Issue aggregating up to Rs 240 million
Offer for Sale Size: Not Applicable
'''
    # Narrow single-column advertisement, sized so every text line fits inside
    # one OCR tile at the pipeline's render scale (1040 px at 160 dpi renders to
    # 1458 px, under the 1600 px tile). The previous 1800 px / 90-character
    # layout produced lines wider than a tile, so each line was cut at a crop
    # boundary and its OCR confidence depended on the host CPU: the CI runner
    # returned an [UNREADABLE_OCR_LINE] there and lost both prices, while this
    # sandbox recovered them. The notice content, the image-only rendering, the
    # real OCR engine and the original-hash assertion are unchanged.
    image = Image.new('RGB', (1040, 800), 'white')
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 28)
    except OSError:
        font = ImageFont.truetype('arial.ttf', 28)
    ImageDraw.Draw(image).multiline_text((40, 40), '\n'.join(textwrap.fill(line, width=54) for line in text.splitlines()),
        fill='black', font=font, spacing=15)
    buffer = io.BytesIO()
    image.save(buffer, format='PDF', resolution=160)
    image.close()
    raw = buffer.getvalue()
    candidate, report = HttpNoticeProvider({'ACME': 'https://www.bseindia.com/notice.pdf'},
        fetcher=lambda url: raw).find(NAME, 'ACME')
    assert candidate is not None, report.detail
    assert candidate.values['price_band_low'] == 100, candidate.values
    assert candidate.values['price_band_high'] == 120 and candidate.values['lot_size'] == 50, candidate.values
    assert candidate.result.fresh_issue_amount.value == 240
    assert candidate.result.price_band_high.extraction_method == 'OCR'
    assert candidate.result.fresh_issue_amount.extraction_method == 'OCR'
    assert candidate.result.source_ref.content_hash == hashlib.sha256(raw).hexdigest()
    assert candidate.result.metadata['ocr']['numeric_repair'] is False


def test_read_only_ocr_deadline_discards_partial_output_and_never_enters_parser(monkeypatch):
    import subprocess
    from ipo_screening.extraction import official_notice_ocr as module
    from ipo_screening.extraction import official_offer_amounts as amounts
    monkeypatch.setattr(amounts, 'document_pages', lambda raw: [(1, '')])
    calls = []
    def expired(command, **kwargs):
        calls.append((command, kwargs))
        raise subprocess.TimeoutExpired(command, kwargs['timeout'], output=b'partial pricing')
    monkeypatch.setattr(module.subprocess, 'run', expired)
    with pytest.raises(ValueError, match='bounded 180-second read budget'):
        module.parse_if_scanned(b'%PDF-image', 'https://www.bseindia.com/ad.pdf')
    assert len(calls) == 1
    assert calls[0][1]['input'] == b'%PDF-image'
    assert calls[0][1]['timeout'] == 180
    assert calls[0][0][1:] == ['-m', module.__name__]


def test_read_only_ocr_failure_does_not_consume_partial_success_payload(monkeypatch):
    import subprocess
    from ipo_screening.extraction import official_notice_ocr as module
    from ipo_screening.extraction import official_offer_amounts as amounts
    monkeypatch.setattr(amounts, 'document_pages', lambda raw: [(1, '')])
    monkeypatch.setattr(module.subprocess, 'run', lambda *args, **kwargs:
        subprocess.CompletedProcess(args, 1, b'[[1,"Fresh Issue Rs 240 million"]]', b'model failure'))
    with pytest.raises(ValueError, match='OCR failed: model failure'):
        module.parse_if_scanned(b'%PDF-image', 'https://www.bseindia.com/ad.pdf')


def test_ocr_primary_issuer_header_excludes_newspaper_masthead_without_letter_repair():
    from ipo_screening.extraction.official_notice_ocr import _primary_issuer_header
    assert _primary_issuer_header([(1, 'DAILY NEWSPAPER\nACME FORGE LIMITED\nCIN: U12345MH2020PLC123456\nRegistered Office: Mumbai')]) == ('ACME FORGE LIMITED', 'ACME FORGE LIMITED')
    assert _primary_issuer_header([(1, 'DAILY NEWSPAPER\nACMEFORGELIMITED\nREGISTEREDOFFICE: Mumbai')]) == ('ACMEFORGE LIMITED', 'ACMEFORGELIMITED')
    assert _primary_issuer_header([(1, 'ACMEFORGELIMITED\n(TO BE LISTED ON THE STOCK EXCHANGES)')]) == ('ACMEFORGE LIMITED', 'ACMEFORGELIMITED')
    assert _primary_issuer_header([(1, 'Other company Limited\nBook running lead manager')]) is None
    assert _primary_issuer_header([(2, 'Other company Limited\nRegistered Office: Mumbai')]) is None
    assert _primary_issuer_header([(1, '[UNREADABLE_OCR_LINE]\nRegistered Office: Mumbai')]) is None
    with pytest.raises(ValueError, match='conflicting standalone primary issuer'):
        _primary_issuer_header([(1, 'ACME FORGE LIMITED\nCIN: x\nOTHER COMPANY LIMITED\nCIN: y')])



# The same rendered notice is segmented differently by host OCR engines: one
# keeps the heading spacing, the other merges it. The text below is the merged
# form the CI runner actually produced for the image-only test above.
SEPARATED_OCR_TEXT = (
    'PRICE BAND ADVERTISEMENT\n'
    'INITIAL PUBLIC OFFERING OF ACME FORGE LIMITED\n'
    'NOTICE TO INVESTORS\n'
    'The Floor Price is Rs 100 per Equity Share and the Cap Price is Rs 120 per Equity Share.\n'
    'The Price Band is Rs 100 to Rs 120 per Equity Share.\n'
    'Bids can be made for a minimum of 50 Equity Shares and in multiples of 50 Equity Shares thereafter.\n'
    'Fresh Issue aggregating up to Rs 240 million\n'
    'Offer for Sale Size: Not Applicable')
CONCATENATED_OCR_TEXT = (
    'PRICEBANDADVERTISEMENT\n'
    'INITIAL PUBLICOFFERINGOFACMEFORGELIMITED\n'
    'NOTICE TO INVESTORS\n'
    'The Floor Price is Rs 100 per Equity Share and the Cap Price is Rs 120 per Equity Share.\n'
    'The Price Band is Rs100 to Rs 120 per EquityShare.\n'
    'Bids can be made for a minimum of 50 Equity Shares and in multiples of 50 Equity Shares\n'
    'thereafter.\n'
    'Fresh Issue aggregatingup toRs 240million\n'
    'Offer forSale Size:NotApplicable')


def parse_ocr_payload(monkeypatch, text, url='https://www.bseindia.com/notice.pdf'):
    import subprocess
    from ipo_screening.extraction import official_notice_ocr as module, official_offer_amounts as amounts
    payload = json.dumps({'pages': [[1, text]], 'identity_pages': [[1, text]]}).encode()
    monkeypatch.setattr(amounts, 'document_pages', lambda raw: [(1, '')])
    monkeypatch.setattr(module.subprocess, 'run',
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, payload, b''))
    return module.parse_if_scanned(b'%PDF-image', url)


def test_merged_heading_spacing_is_restored_without_repairing_issuer_letters_or_digits():
    from ipo_screening.extraction.official_notice_ocr import _restore_heading_spacing
    assert _restore_heading_spacing('INITIAL PUBLICOFFERINGOFACMEFORGELIMITED') == \
        'INITIAL PUBLIC OFFERING OF ACMEFORGE LIMITED'
    assert _restore_heading_spacing('PRICEBANDADVERTISEMENT') == 'PRICE BAND  ADVERTISEMENT '
    assert _restore_heading_spacing('ACME FORGE LIMITED') == 'ACME FORGE LIMITED'
    # Structural only: a word that merely ends in the legal suffix, an
    # identifier with a glued digit, and every amount survive untouched.
    assert _restore_heading_spacing('UNLIMITED') == 'UNLIMITED'
    assert _restore_heading_spacing('ACME CORP LIMITED1') == 'ACME CORP LIMITED1'
    assert _restore_heading_spacing('ACME FORGELTD 100-120 Rs 240 million') == \
        'ACME FORGE LTD 100-120 Rs 240 million'


@pytest.mark.parametrize('text', [SEPARATED_OCR_TEXT, CONCATENATED_OCR_TEXT], ids=['separated', 'concatenated'])
def test_ocr_heading_segmentation_variants_identify_the_configured_issuer(monkeypatch, text):
    from ipo_screening.issue_terms import _norm_name, HttpNoticeProvider
    result = parse_ocr_payload(monkeypatch, text)
    assert _norm_name(result.company_name) == _norm_name(NAME)
    assert result.price_band_low.value == 100 and result.price_band_high.value == 120
    assert result.lot_size.value == 50
    assert result.fresh_issue_amount.value == 240
    assert result.ofs_amount.value == 0
    assert result.metadata['ocr']['numeric_repair'] is False
    candidate, report = HttpNoticeProvider({'ACME': 'https://www.bseindia.com/notice.pdf'},
        fetcher=lambda url: b'%PDF-image').find(NAME, 'ACME')
    assert candidate is not None, report.detail
    assert _norm_name(candidate.result.company_name) == _norm_name(NAME)


def test_merged_and_separated_ocr_extract_identical_issue_terms(monkeypatch):
    merged = parse_ocr_payload(monkeypatch, CONCATENATED_OCR_TEXT)
    separated = parse_ocr_payload(monkeypatch, SEPARATED_OCR_TEXT)
    for name in ('price_band_low', 'price_band_high', 'lot_size', 'fresh_issue_amount', 'ofs_amount'):
        assert getattr(merged, name).value == getattr(separated, name).value, name


@pytest.mark.parametrize('text', [
    CONCATENATED_OCR_TEXT.replace('ACMEFORGELIMITED', 'OTHERCOMPANYLIMITED'),
    SEPARATED_OCR_TEXT.replace('ACME FORGE LIMITED', 'OTHER COMPANY LIMITED'),
], ids=['concatenated', 'separated'])
def test_merged_heading_does_not_match_a_different_issuer(monkeypatch, text):
    from ipo_screening.issue_terms import _norm_name, HttpNoticeProvider
    result = parse_ocr_payload(monkeypatch, text)
    assert _norm_name(result.company_name) != _norm_name(NAME)
    candidate, report = HttpNoticeProvider({'ACME': 'https://www.bseindia.com/notice.pdf'},
        fetcher=lambda url: b'%PDF-image').find(NAME, 'ACME')
    assert candidate is None
    assert 'different issuer' in report.detail


def test_archive_hosts_are_scoped_to_issuer_matched_discovery_not_direct_prospectus_urls():
    from ipo_screening.issue_terms import HttpNoticeProvider, HttpProspectusProvider, OfficialDiscoveryProvider
    archive = 'https://nsearchives.nseindia.com/content/ipo/issuer.pdf'
    assert 'nsearchives.nseindia.com' in OfficialDiscoveryProvider().allowed_hosts
    assert 'listing.bseindia.com' in OfficialDiscoveryProvider().allowed_hosts
    def forbidden_fetch(url):
        raise AssertionError('direct provider must reject before any fetch')
    for cls in (HttpNoticeProvider, HttpProspectusProvider):
        candidate, report = cls({'ACME': archive}, fetcher=forbidden_fetch).find(NAME, 'ACME')
        assert candidate is None and report.outcome == 'REJECTED'


def test_draft_offer_document_is_never_promoted_to_current_rhp_authority():
    from ipo_screening.extraction.official_offer_amounts import parse_official_rhp
    with pytest.raises(ValueError, match='Draft Red Herring Prospectus cannot be promoted'):
        parse_official_rhp(('Draft ' + RHP).encode(), 'https://www.nseindia.com/draft.pdf')


def test_ocr_prices_require_own_currency_token_not_face_value_multiples_or_other_provider_values():
    from ipo_screening.extraction.official_notice_ocr import _has_explicit_price_currency
    from ipo_screening.extraction.price_band_notice import PriceBandField
    def check(value, quote):
        return _has_explicit_price_currency(PriceBandField('price_band_low', value, quote=quote))
    assert not check(10.5, 'FLOOR PRICE IS 10.50 TIMES FACE VALUE Rs 10')
    assert not check(1055, 'lower end 1,055: at upper end 1,119')
    assert not check(100, 'Cap Price Rs 120')
    assert check(100, 'Floor Price Rs 100 per Equity Share')
    assert check(101, 'Floor Price INR 101 per Equity Share')  # no comparison/override against API 100
    assert check(1065, 'Price Band ₹1,065 to ₹1,119 per Equity Share')
