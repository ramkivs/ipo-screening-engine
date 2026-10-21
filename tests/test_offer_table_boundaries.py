"""Synthetic source/layout tests; never live financial evidence."""
import io
import pytest
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from ipo_screening.extraction.official_offer_amounts import explicit_amounts, document_pages, parse_official_rhp
from ipo_screening.extraction.offer_table import component_columns
from ipo_screening.extraction.exchange_issue_page import ExchangeIssueTermsResult


def extract(text):
    return explicit_amounts(ExchangeIssueTermsResult(source=None, source_ref=None, is_classified_notice=False), [(1, text)])


@pytest.mark.parametrize('token', ['[●]', '[ ]', 'TBD'])
def test_placeholder_is_null_diagnostic_not_zero(token):
    r = extract(f'Fresh Issue aggregating up to Rs. {token} million')
    assert r.fresh_issue_amount is None
    assert r.metadata['issue_term_diagnostics'][0]['code'] == 'SOURCE_PLACEHOLDER'
    assert r.metadata['issue_term_diagnostics'][0]['page'] == 1


def test_explicit_nil_is_not_placeholder():
    r = extract('Offer for Sale: Not applicable')
    assert r.ofs_amount.value == 0
    assert not r.metadata['issue_term_diagnostics']


@pytest.mark.parametrize('component', ['Employee Reservation', 'Anchor Investor Portion', 'Shareholder Reservation'])
def test_subtotal_does_not_supply_fresh_cash(component):
    r = extract(f'Fresh Issue 270000000 equity shares. {component} aggregating up to Rs. 5000 million')
    assert r.fresh_issue_amount is None


def test_share_count_and_placeholder_do_not_cross_into_later_amount():
    r = extract('Fresh Issue 270000000 equity shares aggregating up to Rs. TBD million. Later aggregating up to Rs. 600 million')
    assert r.fresh_issue_amount is None


def test_later_applicable_assertion_resolves_without_erasing_placeholder_history():
    r = explicit_amounts(ExchangeIssueTermsResult(source=None, source_ref=None, is_classified_notice=False), [(1, 'Fresh Issue aggregating up to Rs. TBD million'),
            (2, 'Fresh Issue aggregating up to Rs. 240 million')])
    assert r.fresh_issue_amount.value == 240
    assert r.fresh_issue_amount.page == 2
    assert r.metadata['issue_term_diagnostics'][0]['code'] == 'SOURCE_PLACEHOLDER'


def test_distinct_explicit_amounts_remain_conflicting():
    r = extract('Fresh Issue aggregating up to Rs. 240 million. Fresh Issue aggregating up to Rs. 300 million')
    assert r.fresh_issue_amount is None
    assert 'fresh_issue' in r.metadata['issue_term_errors']


def pdf(pages):
    w = PdfWriter()
    for content in pages:
        p = w.add_blank_page(width=600, height=800)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        p[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): w._add_object(font)})})
        stream = DecodedStreamObject(); stream.set_data(content.encode('ascii'))
        p[NameObject('/Contents')] = w._add_object(stream)
    out = io.BytesIO(); w.write(out); return out.getvalue()


def run(text, x, y):
    return f'BT /F1 9 Tf 1 0 0 1 {x} {y} Tm ({text}) Tj ET\n'


def table(grid=True):
    s = ''
    for x, title in [(25, 'Fresh Issue Size'), (205, 'Offer for Sale Size'), (385, 'Total Issue Size')]:
        if grid:
            s += f'{x-5} 690 180 30 re S\n{x-5} 550 180 140 re S\n'
        s += run(title, x, 700)
    return s


def test_pdf_table_cells_keep_cash_shares_and_total_separate():
    raw = pdf([table()+run('270000000 Equity Shares',25,670)+run('aggregating up to Rs. 240 million',25,650)+run('Not applicable',205,670)+run('aggregating up to Rs. 999 million',385,650)+run('aggregating up to Rs. 777 million',25,500)])
    columns = component_columns(PdfReader(io.BytesIO(raw)).pages[0], 1)
    assert len(columns) == 2
    r = explicit_amounts(ExchangeIssueTermsResult(source=None, source_ref=None, is_classified_notice=False), document_pages(raw), columns)
    assert r.fresh_issue_amount.value == 240
    assert r.ofs_amount.value == 0
    assert r.fresh_issue_amount.quote == 'aggregating up to Rs. 240 million'
    assert 'x=25.0' in r.fresh_issue_amount.locator
    assert columns[0]['body_bounds'] == [20.,550.,180.,140.]


def test_unbounded_columns_are_not_guessed_as_table():
    raw = pdf([table(False)])
    assert component_columns(PdfReader(io.BytesIO(raw)).pages[0],1) == []


def test_native_read_expands_but_reports_bound():
    raw = pdf([run(f'Page {i}',25,700) for i in range(35)])
    scope = {}
    pages = document_pages(raw, max_pages=30, diagnostics=scope)
    assert len(pages) == 30 and pages[-1][0] == 30
    assert scope['total_pages'] == 35 and scope['complete_document'] is False
    assert scope['page_read_errors'] == []


def test_qualified_rhp_extracts_page_twelve_with_original_hash_and_page():
    import hashlib
    cover = 'Red Herring Prospectus Dated: October 21, 2026\nACME FORGE LIMITED\nU12345MH2020PLC123456'
    raw = pdf([run(cover.replace('\n', ' '),25,700)] + [run('Other material',25,700)]*10 + [run('THE ISSUE',25,730)+run('Fresh Issue aggregating up to Rs. 240 million',25,700)])
    r = parse_official_rhp(raw, 'https://www.nseindia.com/rhp.pdf')
    assert r.fresh_issue_amount.value == 240 and r.fresh_issue_amount.page == 12
    assert r.source_ref.content_hash == hashlib.sha256(raw).hexdigest()


def test_face_value_clause_does_not_hide_valid_fresh_aggregate():
    r = extract('Fresh Issue of 2400000 Equity Shares of face value of Rs. 10 each aggregating up to Rs. 240 million')
    assert r.fresh_issue_amount.value == 240


def test_unreadable_is_not_a_placeholder_or_cash():
    r = extract('Fresh Issue [UNREADABLE_OCR_LINE] aggregating up to Rs. 240 million')
    assert r.fresh_issue_amount is None
    assert not r.metadata['issue_term_diagnostics']


def test_table_nil_quote_is_original_cell_not_synthetic_heading():
    raw = pdf([table()+run('Not applicable',205,670)])
    columns = component_columns(PdfReader(io.BytesIO(raw)).pages[0],1)
    r = explicit_amounts(ExchangeIssueTermsResult(source=None,source_ref=None,is_classified_notice=False), document_pages(raw), columns)
    assert r.ofs_amount.quote == 'Not applicable'
    assert 'x=205.0' in r.ofs_amount.locator


def test_placeholder_diagnostic_does_not_cross_component_header():
    r = extract('Offer for Sale Size Total Issue Size Fresh Issue aggregating up to Rs. TBD million')
    assert {d['field'] for d in r.metadata['issue_term_diagnostics']} == {'fresh_issue'}


def test_total_does_not_supply_ofs():
    r = extract('Offer for Sale Size Total Issue Size aggregating up to Rs. 240 million')
    assert r.ofs_amount is None


def test_page_read_failure_is_incomplete_not_placeholder(monkeypatch):
    import pypdf
    class Bad:
        def extract_text(self): raise ValueError('unreadable stream')
    class Reader:
        pages = [Bad()]
    monkeypatch.setattr(pypdf, 'PdfReader', lambda stream: Reader())
    scope = {}
    assert document_pages(b'%PDF-controlled', max_pages=30, diagnostics=scope) == []
    assert scope['complete_document'] is False
    assert scope['page_read_errors'] == [{'page': 1, 'error': 'unreadable stream'}]


def test_unrelated_later_page_is_not_an_offer_summary():
    cover = 'Red Herring Prospectus Dated: October 21, 2026 ACME FORGE LIMITED U12345MH2020PLC123456'
    raw = pdf([run(cover,25,700)] + [run('Other material',25,700)]*10 + [run('Fresh Issue aggregating up to Rs. 999 million',25,700)])
    r = parse_official_rhp(raw, 'https://www.nseindia.com/rhp.pdf')
    assert r.fresh_issue_amount is None
    assert 12 not in r.metadata['native_read_scope']['amount_pages_considered']


def test_multiline_visitor_chunk_is_not_reconstructed_into_cells():
    # pypdf callbacks can group multiple text operators. Do not split a
    # grouped chunk and pretend each line's geometry has been established.
    class Page:
        def extract_text(self, visitor_text, visitor_operand_before):
            cm=[1,0,0,1,0,0]
            for x,title in [(25,'Fresh Issue Size'),(205,'Offer for Sale Size'),(385,'Total Issue Size')]:
                visitor_operand_before(b're',[x-5,690,180,30],cm,cm)
                visitor_operand_before(b're',[x-5,550,180,140],cm,cm)
                visitor_text(title,cm,[1,0,0,1,x,700],None,9)
            visitor_text('aggregating up to Rs. 240 million\nNot applicable',cm,[1,0,0,1,25,650],None,9)
    columns=component_columns(Page(),1)
    assert not columns[0]['cells']
    assert columns[0]['ambiguous_text_runs']
