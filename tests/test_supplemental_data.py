from __future__ import annotations
import hashlib, json, subprocess, sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import pytest
from conftest import ENGINE_ROOT, GOLDEN_DIR, REPO_ROOT
CLI=ENGINE_ROOT/'tools'/'ipo_screen.py'
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.pipeline import evaluate, load_config, replay
from ipo_screening.supplemental_data import ELIGIBILITY_REGISTRY, initialize_template, finalize_payload, validate_payload, store_payload, baseline_binding

@pytest.fixture
def baseline(tmp_path):
    doc=json.loads((GOLDEN_DIR/'input.json').read_text())
    doc['market']['subscription'] = {}
    store=EvaluationStore(tmp_path/'evaluations')
    out=evaluate(doc,load_config(),mode='final',evaluation_datetime=datetime(2026,10,5,12,tzinfo=timezone.utc),store=store)
    return store,out.record.evaluation_id

def completed_payload(store,eid,tmp_path,value=2.5,target='market.subscription.qib_x'):
    evidence=tmp_path/'exchange.pdf'; evidence.write_bytes(b'official-test-artifact')
    t=initialize_template(store,eid)
    e=next(deepcopy(x) for x in t['entries'] if x['target']==target)
    e.update(value=value,observation_time='2026-10-05T11:00:00Z')
    e['source'].update(source_id='EX-1',title='Subscription notice',publisher='Exchange',publication_date='2026-10-05',official_url='https://example.invalid/notice',artifact_ref=evidence.name,artifact_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),locator='Table 1, QIB row')
    e['operator_attestation']={'operator_id':'owner','attested_at':'2026-10-05T12:05:00Z','statement':'I transcribed this value from the identified artifact.'}
    e['verification']={'status':'SOURCE_ARTIFACT_HASH_VERIFIED','procedure_note':'Artifact bytes matched the declared SHA-256; value authenticity is not established.'}
    t['entries']=[e]; t['created_at']='2026-10-05T12:05:00Z'
    return finalize_payload(t),evidence

def snapshot(store):
    return {str(p.relative_to(store.root)):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}

def test_template_is_bound_and_only_registry_gaps_are_fillable(baseline,tmp_path):
    store,eid=baseline; t=initialize_template(store,eid)
    rec=store.read_full(eid); manifest=store.read_artifact(eid,'manifest')
    assert t['baseline_binding']==baseline_binding(rec,manifest)
    # The golden baseline already explicitly supplies this guardrail; templates
    # expose only genuine gaps, not fields that merely happen to be eligible.
    assert {e['target'] for e in t['entries']}==set(ELIGIBILITY_REGISTRY)-{
        'governance.sebi_ed_action_active', 'business.industry_cagr_pct',
        'business.moat_rating', 'business.visibility_rating',
    }
    assert t['template_metadata']['excluded_gaps']
    assert t['template_metadata']['scoring_eligibility']=='NOT_GRANTED'

def test_valid_payload_and_operator_attestation_not_value_verification(baseline,tmp_path):
    store,eid=baseline; p,_=completed_payload(store,eid,tmp_path)
    result=validate_payload(p,store,payload_base=tmp_path)
    assert result.accepted and result.outcome=='SUPPLEMENTAL_STORAGE_ACCEPTABLE'
    assert p['entries'][0]['verification']['status']=='SOURCE_ARTIFACT_HASH_VERIFIED'

def test_missing_baseline_wrong_binding_and_identity_rejected(baseline,tmp_path):
    store,eid=baseline; p,_=completed_payload(store,eid,tmp_path)
    q=deepcopy(p); q['evaluation_id']='MISSING'; q=finalize_payload(q)
    assert not validate_payload(q,store,payload_base=tmp_path).accepted
    q=deepcopy(p); q['baseline_binding']='0'*64; q=finalize_payload(q)
    assert 'BASELINE_BINDING_MISMATCH' in validate_payload(q,store,payload_base=tmp_path).errors
    q=deepcopy(p); q['company_name']='Other'; q=finalize_payload(q)
    assert 'BASELINE_IDENTITY_MISMATCH' in validate_payload(q,store,payload_base=tmp_path).errors

def test_changed_or_missing_artifact_fails_closed(baseline,tmp_path):
    store,eid=baseline; p,_=completed_payload(store,eid,tmp_path)
    path=store.path_for(eid)/'input.json'
    altered=json.loads(path.read_text()); altered['snapshot']['company_name']='Tampered'; path.write_text(json.dumps(altered))
    result=validate_payload(p,store,payload_base=tmp_path)
    assert not result.accepted and any('failed artifact' in e for e in result.errors)

def test_eligibility_type_range_metadata_and_provenance_rejections(baseline,tmp_path):
    store,eid=baseline; p,evidence=completed_payload(store,eid,tmp_path)
    variants=[]
    q=deepcopy(p); q['entries'][0]['target']='unknown.target'; variants.append(q)
    q=deepcopy(p); q['entries'][0]['value']=-1; variants.append(q)
    q=deepcopy(p); q['entries'][0]['value']='2.5'; variants.append(q)
    q=deepcopy(p); q['entries'][0]['unit']=None; variants.append(q)
    q=deepcopy(p); q['entries'][0]['observation_time']=None; variants.append(q)
    q=deepcopy(p); q['entries'][0]['source']['artifact_ref']='missing.pdf'; variants.append(q)
    q=deepcopy(p); q['entries'][0]['source']['artifact_sha256']='0'*64; variants.append(q)
    q=deepcopy(p); q['entries'][0]['source']['source_type']='OFFICIAL_FILING'; variants.append(q)
    for q in variants:
        q=finalize_payload(q)
        assert not validate_payload(q,store,payload_base=tmp_path).accepted

def test_additional_properties_rejected(baseline,tmp_path):
    store,eid=baseline; p,_=completed_payload(store,eid,tmp_path)
    q=deepcopy(p); q['extra']='no'; q=finalize_payload(q)
    assert any('additional' in e.lower() for e in validate_payload(q,store,payload_base=tmp_path).errors)


def test_established_stale_layer1_value_cannot_be_overwritten(tmp_path):
    doc=json.loads((GOLDEN_DIR/'input.json').read_text())
    store=EvaluationStore(tmp_path/'stale-evaluations')
    out=evaluate(doc,load_config(),mode='final',evaluation_datetime=datetime(2026,12,5,12,tzinfo=timezone.utc),store=store)
    stale_id=out.record.evaluation_id
    assert 'market.subscription.qib_x' not in {e['target'] for e in initialize_template(store,stale_id)['entries']}
    clean=deepcopy(doc);clean['market']['subscription']={}
    clean_out=evaluate(clean,load_config(),mode='final',evaluation_datetime=datetime(2026,12,6,12,tzinfo=timezone.utc),store=store)
    p,_=completed_payload(store,clean_out.record.evaluation_id,tmp_path)
    stale_record=store.read_full(stale_id);stale_manifest=store.read_artifact(stale_id,'manifest')
    p['evaluation_id']=stale_id;p['baseline_binding']=baseline_binding(stale_record,stale_manifest);p=finalize_payload(p)
    result=validate_payload(p,store,payload_base=tmp_path)
    assert not result.accepted
    assert any('TARGET_ALREADY_ESTABLISHED_IN_LAYER1' in e for e in result.errors)

def test_store_isolated_immutable_duplicate_and_conflict(baseline,tmp_path):
    store,eid=baseline; p,_=completed_payload(store,eid,tmp_path)
    before=snapshot(store); supp=tmp_path/'supp'
    outcome,target,result=store_payload(p,store,supp,payload_base=tmp_path)
    assert outcome=='SUPPLEMENTAL_STORAGE_ACCEPTED' and result.accepted
    assert (target/'supplemental_payload.json').is_file() and (target/'supplemental_manifest.json').is_file()
    saved=(target/'supplemental_payload.json').read_bytes()
    assert store_payload(p,store,supp,payload_base=tmp_path)[0]=='EXACT_DUPLICATE'
    assert (target/'supplemental_payload.json').read_bytes()==saved
    p2,_=completed_payload(store,eid,tmp_path,value=3.0); assert store_payload(p2,store,supp,payload_base=tmp_path)[0]=='CONFLICT_REJECTED'
    assert snapshot(store)==before

def test_invalid_no_partial_store_and_baseline_destination_refused(baseline,tmp_path):
    store,eid=baseline; p,_=completed_payload(store,eid,tmp_path); p['baseline_binding']='0'*64; p=finalize_payload(p)
    supp=tmp_path/'supp'; assert store_payload(p,store,supp,payload_base=tmp_path)[0]=='CONTRACT_REJECTED'; assert not supp.exists()
    p,_=completed_payload(store,eid,tmp_path)
    outcome,_,_=store_payload(p,store,store.path_for(eid)/'supp',payload_base=tmp_path)
    assert outcome=='CONTRACT_REJECTED'

def test_symlink_into_baseline_refused(baseline,tmp_path):
    store,eid=baseline; p,_=completed_payload(store,eid,tmp_path)
    link=tmp_path/'link'; link.symlink_to(store.path_for(eid),target_is_directory=True)
    assert store_payload(p,store,link/'supp',payload_base=tmp_path)[0]=='CONTRACT_REJECTED'

def test_layer1_verify_and_replay_unchanged_after_storage(baseline,tmp_path):
    store,eid=baseline; p,_=completed_payload(store,eid,tmp_path); before=snapshot(store); original=store.read(eid)
    assert store_payload(p,store,tmp_path/'supp',payload_base=tmp_path)[0]=='SUPPLEMENTAL_STORAGE_ACCEPTED'
    check=store.verify_hashes(eid); assert check['result_hash_matches'] and not check['artifact_mismatches']
    replayed=replay(store,eid,load_config()); assert replayed.record.result_hash==original['result_hash']
    assert snapshot(store)==before


def test_cli_init_validate_and_inject_are_separate(baseline,tmp_path):
    store,eid=baseline; template_path=tmp_path/'template.json'
    init=subprocess.run([sys.executable,str(CLI),'supplemental-init',eid,'--store',str(store.root),'--output',str(template_path)],cwd=REPO_ROOT,capture_output=True,text=True)
    assert init.returncode==0 and template_path.is_file() and 'scoring           NOT_GRANTED' in init.stdout
    template=json.loads(template_path.read_text()); evidence=tmp_path/'exchange.pdf'; evidence.write_bytes(b'official-test-artifact')
    entry=next(e for e in template['entries'] if e['target']=='market.subscription.qib_x'); entry.update(value=1.5,observation_time='2026-10-05T11:00:00Z')
    entry['source'].update(source_id='EX-1',title='Notice',publisher='Exchange',publication_date='2026-10-05',official_url='https://example.invalid/n',artifact_ref=evidence.name,artifact_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),locator='Table 1')
    entry['operator_attestation']={'operator_id':'owner','attested_at':'2026-10-05T12:00:00Z','statement':'Transcribed from identified artifact.'}
    entry['verification']={'status':'SOURCE_ARTIFACT_HASH_VERIFIED','procedure_note':'Artifact hash only; value authenticity not established.'}
    template['entries']=[entry]; template['created_at']='2026-10-05T12:00:00Z'; payload=finalize_payload(template)
    payload_path=tmp_path/'payload.json'; payload_path.write_text(json.dumps(payload))
    before=snapshot(store)
    valid=subprocess.run([sys.executable,str(CLI),'supplemental-validate',str(payload_path),'--store',str(store.root)],cwd=REPO_ROOT,capture_output=True,text=True)
    assert valid.returncode==0 and 'SUPPLEMENTAL_STORAGE_ACCEPTABLE' in valid.stdout and not (tmp_path/'supp').exists()
    inject=subprocess.run([sys.executable,str(CLI),'supplemental-inject',str(payload_path),'--store',str(store.root),'--supp-store',str(tmp_path/'supp')],cwd=REPO_ROOT,capture_output=True,text=True)
    assert inject.returncode==0 and 'SUPPLEMENTAL_STORAGE_ACCEPTED' in inject.stdout
    assert snapshot(store)==before
