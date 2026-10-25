"""Real-filing regressions; never invent missing safety or market observations."""
import copy
from pathlib import Path
import pypdf
import pytest
from conftest import EVAL_AT, run
from ipo_screening.extraction.interfaces import SourceDocument, RawExtraction
from ipo_screening.extraction.sections import SectionExtractor
from ipo_screening.extraction.toc import TOCRouter
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.evaluation_record import build_evaluation_record_v1

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf'

@pytest.fixture(scope='module')
def document():
    reader = pypdf.PdfReader(PDF)
    return SourceDocument(source_id='SRC-JIO-TEST', content_hash='72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d'), reader

def section(document):
    doc,reader=document
    return SectionExtractor(doc, reader)

def test_issue_heading_routes_actual_objects(document):
    router=TOCRouter.from_pdf(document[1])
    assert router.get_page_range('objects_of_the_offer')[0]==116

def test_real_debt_and_unknown_gcp_with_amount_page(document):
    fields=section(document).extract_objects_of_offer({'objects_of_the_offer':(116,125)})
    schedule=next(x.candidate_value for x in fields if x.field_path=='use_of_proceeds')
    assert {'category':'debt_repayment','amount':275000.0} in schedule
    gcp=next(x for x in schedule if x['category']=='gcp')
    assert gcp['amount'] is None and gcp['undisclosed_marker']=='[●]'
    amount=next(x for x in fields if x.field_path=='use_of_proceeds[0].amount')
    assert amount.page==116 and '275,000' in amount.quote

def test_pre_holding_not_copied_into_post(document):
    fields={x.field_path:x for x in section(document).extract_capital_structure({'capital_structure':(99,126)})}
    assert fields['capital_structure.promoter_pre_pct'].candidate_value==66.43
    assert fields['capital_structure.promoter_pre_pct'].page==104
    assert 'capital_structure.promoter_post_pct' not in fields

def test_auditor_explicit_evidence_no_safety_inference(document):
    fields={x.field_path:x for x in section(document).extract_governance({'restated_financials':(320,432),'litigation':(463,474)})}
    assert fields['governance.auditor_changed_3y'].candidate_value is False
    assert fields['governance.auditor_changed_3y'].page==322
    assert fields['governance.auditor_reputed'].candidate_value is True
    assert fields['governance.repeated_eom'].candidate_value is False
    assert fields['governance.repeated_eom'].page==430
    assert 'governance.going_concern_uncertainty' not in fields

def test_builder_unknown_kmp_not_zero(document):
    doc,_=document
    builder=CanonicalInputBuilder(doc,[])
    assert builder._build_governance()['kmp_exits_2y'] is None

def test_builder_first_value_and_evidence_agree(document):
    doc,_=document
    builder=CanonicalInputBuilder(doc,[RawExtraction('company_name','first',quote='first'),RawExtraction('company_name','second',quote='second')])
    assert builder._get_field('company_name')=='first'
    assert builder._build_evidence()['company_name']['quote']=='first'

def test_explicit_map_survives_projection(golden_input,config):
    data=copy.deepcopy(golden_input)
    # A declared non-generated ID must survive, not be guessed by ID formatting.
    existing='governance.auditor_opinion'
    evidence=copy.deepcopy(next(iter(data['_evidence'].values())))
    data['_evidence'][existing]=evidence
    evidence['evidence_id']='EV-EXPLICIT-NONSTANDARD'
    outcome=run(data,config)
    assert outcome.record.evidence['field_map'][existing]=='EV-EXPLICIT-NONSTANDARD'
    projection=build_evaluation_record_v1(outcome.record)
    pointer='/input/'+existing.replace('.','/')
    rows=[x for x in projection['field_values'] if x['field_path']==pointer]
    assert rows
    assert 'EV-EXPLICIT-NONSTANDARD' in rows[0]['evidence_refs']
