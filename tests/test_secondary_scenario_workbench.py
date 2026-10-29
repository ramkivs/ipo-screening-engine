from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.supplemental_data import finalize_payload, initialize_template, store_payload
from ipo_screening.secondary_evaluation import build_secondary, store_secondary, verify_secondary, MODULE_CAPS
from ipo_screening.operator_scenario import scenario_template, finalize_scenario, evaluate_scenario, store_scenario

ROOT=Path(__file__).resolve().parents[1]
JIO=ROOT/'docs/investigation/jio-current-engine-probe-20261027/evaluations'
EID='JIO-PLATFORMS-LIMITED-20261027-145236Z-final-0fde1451'

def accepted_payload(tmp_path:Path):
 store=EvaluationStore(JIO); template=initialize_template(store,EID); artifact=tmp_path/'exchange.txt'; artifact.write_text('synthetic test only: QIB 12.34x\n'); digest=hashlib.sha256(artifact.read_bytes()).hexdigest(); entry=next(e for e in template['entries'] if e['target']=='market.subscription.qib_x'); template['entries']=[entry]; template['created_at']='2026-10-23T14:50:00Z'; entry.update(value=12.34,observation_time='2026-10-23T14:50:00Z',reporting_period='FINAL_DAY')
 entry['source'].update(source_id='TEST',title='Synthetic test artifact',publisher='SYNTHETIC NOT A PUBLISHER',publication_date='2026-10-23',artifact_ref='exchange.txt',artifact_sha256=digest,locator='line 1')
 entry['operator_attestation']={'operator_id':'test','attested_at':'2026-10-23T14:51:00Z','statement':'Test-only bytes; no authenticity claim.'};entry['verification']={'status':'SOURCE_ARTIFACT_HASH_VERIFIED','procedure_note':'Only local bytes matched.'};entry['limitations']=['Synthetic test only; not scoring evidence.']
 payload=finalize_payload(template); supp=tmp_path/'supp'; outcome,path,val=store_payload(payload,store,supp,payload_base=tmp_path); assert outcome=='SUPPLEMENTAL_STORAGE_ACCEPTED'; return payload,supp

def test_secondary_is_deterministic_capped_and_baseline_immutable(tmp_path):
 before={p.name:p.read_bytes() for p in (JIO/EID).iterdir() if p.is_file()}; payload,supp=accepted_payload(tmp_path); doc=build_secondary(EID,EvaluationStore(JIO),supp,payload['supplemental_payload_id']); assert doc['baseline']['score']==37.0; assert doc['secondary']['score']==39.0; assert doc['admitted_fields']==['market.subscription.qib_x']; assert all(m['secondary_points']<=MODULE_CAPS[m['module_id']] for m in doc['module_breakdown']); assert verify_secondary(doc)['valid']; outcome,path=store_secondary(doc,tmp_path/'secondary'); assert outcome=='SECONDARY_EVALUATION_STORED'; assert build_secondary(EID,EvaluationStore(JIO),supp,payload['supplemental_payload_id'])==doc; assert before=={p.name:p.read_bytes() for p in (JIO/EID).iterdir() if p.is_file()}

def test_secondary_rejects_non_whitelisted_stored_target(tmp_path):
 payload,supp=accepted_payload(tmp_path); directory=next((supp/EID).iterdir()); payload['entries'][0]['target']='business.moat_rating'; from ipo_screening.supplemental_data import payload_hash
 h=payload_hash(payload);payload['canonical_payload_hash']=h;payload['supplemental_payload_id']='SUPP-'+h[:16];(directory/'supplemental_payload.json').write_text(json.dumps(payload));m=json.loads((directory/'supplemental_manifest.json').read_text());m['payload_hash']=h;(directory/'supplemental_manifest.json').write_text(json.dumps(m))
 with pytest.raises(ValueError,match='whitelisted'):build_secondary(EID,EvaluationStore(JIO),supp,payload['supplemental_payload_id'])

def test_secondary_rejects_out_of_window_observation(tmp_path):
 payload,supp=accepted_payload(tmp_path);directory=next((supp/EID).iterdir());payload['entries'][0]['observation_time']='2026-10-27T14:50:00Z';from ipo_screening.supplemental_data import payload_hash
 h=payload_hash(payload);payload['canonical_payload_hash']=h;payload['supplemental_payload_id']='SUPP-'+h[:16];(directory/'supplemental_payload.json').write_text(json.dumps(payload));m=json.loads((directory/'supplemental_manifest.json').read_text());m['payload_hash']=h;(directory/'supplemental_manifest.json').write_text(json.dumps(m))
 with pytest.raises(ValueError,match='outside'):build_secondary(EID,EvaluationStore(JIO),supp,payload['supplemental_payload_id'])

def test_secondary_store_cannot_enter_baseline(tmp_path):
 payload,supp=accepted_payload(tmp_path);doc=build_secondary(EID,EvaluationStore(JIO),supp,payload['supplemental_payload_id'])
 with pytest.raises(ValueError,match='outside'):store_secondary(doc,JIO/EID/'secondary',EvaluationStore(JIO))

def test_secondary_hash_tamper_detected(tmp_path):
 payload,supp=accepted_payload(tmp_path);doc=build_secondary(EID,EvaluationStore(JIO),supp,payload['supplemental_payload_id']);doc['secondary']['score']+=1;assert not verify_secondary(doc)['valid']

def test_operator_scenario_is_badged_isolated_and_capped(tmp_path):
 p=scenario_template(EID);p.update(created_at='2026-10-29T12:00:00Z',operator_id='tester');p['peer_assertions']=[{'peer_name':'Asserted Peer','pe':20,'as_of':'2026-10-29','points_delta':20,'justification':'scenario only'}];p['qualitative_assertions']=[{'criterion':'moat','rating':'HIGH','points_delta':15,'justification':'scenario only'}];p=finalize_scenario(p);r=evaluate_scenario(p,EvaluationStore(JIO),tmp_path/'secondary');assert r['badge']=='[OPERATOR_ASSUMPTION]'; assert all(x['badge']=='[OPERATOR_ASSUMPTION]' for x in r['attribution']);assert all(m['scenario_points']<=m['cap'] for m in r['module_breakdown']);assert r['scenario']['knockout_status']=='TRIGGERED' and r['scenario']['verdict']=='AVOID';out,path=store_scenario(p,r,tmp_path/'operator');assert out=='SCENARIO_STORED';assert not (JIO/EID/'scenario_result.json').exists()

def test_scenario_target_must_exist(tmp_path):
 p=scenario_template('missing');p.update(created_at='2026-10-29T12:00:00Z',operator_id='tester');p=finalize_scenario(p)
 with pytest.raises(FileNotFoundError):evaluate_scenario(p,EvaluationStore(JIO),tmp_path/'secondary')

def test_workbench_explorer_and_badges(monkeypatch,tmp_path):
 import importlib,engine.tools.ui_dashboard as dashboard
 monkeypatch.setattr(dashboard,'L1',JIO);monkeypatch.setattr(dashboard,'ROOT',tmp_path);monkeypatch.setattr(dashboard,'SUPP',tmp_path/'supp');monkeypatch.setattr(dashboard,'SEC',tmp_path/'sec');monkeypatch.setattr(dashboard,'OP',tmp_path/'op');client=TestClient(dashboard.app);page=client.get('/');assert page.status_code==200;assert '[LAYER_1_BASE]' in page.text and '[ENRICHED_LAYER_2C]' in page.text and '[OPERATOR_ASSUMPTION]' in page.text;data=client.get('/api/evaluations').json();assert any(x['id']==EID for x in data);hashed=client.post('/api/hash',files={'evidence':('x.txt',b'abc')}).json();assert hashed['sha256']==hashlib.sha256(b'abc').hexdigest()
