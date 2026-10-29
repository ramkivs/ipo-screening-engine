"""Isolated Layer 3 operator-assumption scenarios."""
from __future__ import annotations
import copy, json, os, tempfile
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple
from jsonschema import Draft202012Validator, FormatChecker
from .evaluation import EvaluationStore
from .hashing import sha256_of
from .secondary_evaluation import MODULE_CAPS, verify_secondary

SCHEMA_PATH=Path(__file__).resolve().parents[2]/"schema"/"operator-scenario.v1.schema.json"
RESULT_SCHEMA_PATH=Path(__file__).resolve().parents[2]/"schema"/"operator-scenario-result.v1.schema.json"


def scenario_template(target_id:str)->Dict[str,Any]:
 return {"contract_name":"IPO_LAYER_3_OPERATOR_SCENARIO","contract_version":"1.0","target_id":target_id,"scenario_id":None,"created_at":"","operator_id":"","peer_assertions":[],"qualitative_assertions":[],"limitations":["[OPERATOR_ASSUMPTION] Scenario inputs are user assertions, not verified evidence."],"canonical_scenario_hash":None}

def _subject(d:Mapping[str,Any])->Dict[str,Any]:
 out=copy.deepcopy(dict(d)); out.pop("scenario_id",None); out.pop("canonical_scenario_hash",None); return out

def scenario_hash(d:Mapping[str,Any])->str:return sha256_of(_subject(d))

def finalize_scenario(d:Mapping[str,Any])->Dict[str,Any]:
 out=copy.deepcopy(dict(d)); h=scenario_hash(out); out["canonical_scenario_hash"]=h; out["scenario_id"]=f"SCN-{h[:16]}"; return out

def _load_target(target_id:str, store:EvaluationStore, sec_root:Path)->Tuple[str,Dict[str,Any],str]:
 if store.exists(target_id):
  check=store.verify_hashes(target_id)
  if not check["result_hash_matches"] or check["artifact_mismatches"]: raise ValueError("baseline integrity failed")
  r=store.read(target_id); return target_id,r,"LAYER_1_BASE"
 for p in sec_root.glob(f"*/{target_id}/secondary_evaluation.json"):
  d=json.loads(p.read_text()); v=verify_secondary(d)
  if not v["valid"]: raise ValueError("secondary target integrity failed")
  return str(d["baseline_evaluation_id"]),d,"ENRICHED_LAYER_2C"
 raise FileNotFoundError(f"target {target_id!r} not found")

def _target_view(target:Mapping[str,Any],kind:str)->Tuple[float,str,str,str,Dict[str,float]]:
 if kind=="LAYER_1_BASE":
  s=target["score"]; score=float(s["final_score"]); verdict=str(target["verdict"]["verdict"]); confidence=str(target["confidence"]["level"]); knockout_status=str(target["knockouts"]["status"]); modules={m["module_id"]:float(m["score"]) for m in s["modules"]}
 else:
  score=float(target["secondary"]["score"]); verdict=str(target["secondary"]["verdict"]); confidence=str(target["secondary"]["confidence"]); knockout_status=str(target["secondary"]["knockout_status"]); modules={m["module_id"]:float(m["secondary_points"]) for m in target["module_breakdown"]}
 return score,verdict,confidence,knockout_status,modules

def evaluate_scenario(payload:Mapping[str,Any],store:EvaluationStore,sec_root:Path)->Dict[str,Any]:
 errors=[e.message for e in Draft202012Validator(json.loads(SCHEMA_PATH.read_text()),format_checker=FormatChecker()).iter_errors(payload)]
 if payload.get("canonical_scenario_hash")!=scenario_hash(payload) or payload.get("scenario_id")!=f"SCN-{scenario_hash(payload)[:16]}": errors.append("scenario identity mismatch")
 if errors: raise ValueError("; ".join(errors))
 baseline_id,target,kind=_load_target(str(payload["target_id"]),store,sec_root)
 score,verdict,confidence,knockout_status,modules=_target_view(target,kind); before=dict(modules); attribution=[]
 for a in payload.get("peer_assertions",[]):
  delta=float(a["points_delta"]); prior=modules.get("B",0); modules["B"]=max(0.0,min(MODULE_CAPS["B"],prior+delta)); attribution.append({"badge":"[OPERATOR_ASSUMPTION]","module_id":"B","label":a["peer_name"],"requested_delta":delta,"applied_delta":modules["B"]-prior})
 for a in payload.get("qualitative_assertions",[]):
  delta=float(a["points_delta"]); prior=modules.get("E",0); modules["E"]=max(0.0,min(MODULE_CAPS["E"],prior+delta)); attribution.append({"badge":"[OPERATOR_ASSUMPTION]","module_id":"E","label":a["criterion"],"requested_delta":delta,"applied_delta":modules["E"]-prior})
 for mid,value in modules.items():
  if value>MODULE_CAPS[mid]: raise ValueError(f"module {mid} cap exceeded")
 scenario_score=max(0.0,min(100.0,score+sum(modules.get(k,0)-before.get(k,0) for k in MODULE_CAPS)))
 scenario_verdict="AVOID" if knockout_status=="TRIGGERED" else next((v for minimum,v in ((75,"APPLY"),(60,"APPLY_SELECTIVELY"),(45,"NEUTRAL")) if scenario_score>=minimum),"AVOID")
 result={"contract_name":"IPO_LAYER_3_SCENARIO_RESULT","contract_version":"1.0","scenario_id":payload["scenario_id"],"target_id":payload["target_id"],"baseline_evaluation_id":baseline_id,"target_layer":kind,"input_scenario_hash":payload["canonical_scenario_hash"],"base":{"score":score,"verdict":verdict,"confidence":confidence,"knockout_status":knockout_status},"scenario":{"score":scenario_score,"verdict":scenario_verdict,"confidence":confidence,"knockout_status":knockout_status},"module_breakdown":[{"module_id":m,"base_points":before.get(m,0),"scenario_points":modules.get(m,0),"cap":MODULE_CAPS[m],"cap_applied":modules.get(m,0)>=MODULE_CAPS[m]} for m in MODULE_CAPS],"attribution":attribution,"badge":"[OPERATOR_ASSUMPTION]","canonical_result_hash":None}
 h=sha256_of({k:v for k,v in result.items() if k!="canonical_result_hash"}); result["canonical_result_hash"]=h
 result_errors=[e.message for e in Draft202012Validator(json.loads(RESULT_SCHEMA_PATH.read_text())).iter_errors(result)]
 if result_errors:raise ValueError("scenario result schema violation: "+"; ".join(result_errors))
 return result

def store_scenario(payload:Mapping[str,Any],result:Mapping[str,Any],root:Path,baseline_store:EvaluationStore|None=None)->Tuple[str,Path]:
 root=root.resolve();baseline_id=str(result["baseline_evaluation_id"])
 if Path(baseline_id).name!=baseline_id:raise ValueError("unsafe baseline evaluation identity")
 if baseline_store is not None:
  evaluation_dir=baseline_store.path_for(baseline_id).resolve()
  if root==evaluation_dir or evaluation_dir in root.parents:raise ValueError("operator store must be outside the immutable baseline directory")
 target=root/baseline_id/str(result["scenario_id"])
 if target.exists(): return "EXACT_DUPLICATE",target
 target.parent.mkdir(parents=True,exist_ok=True); temp=Path(tempfile.mkdtemp(prefix=".scenario.tmp-",dir=target.parent))
 try:
  (temp/"scenario_payload.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
  (temp/"scenario_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
  os.rename(temp,target)
 except Exception:
  for c in temp.glob("*"):c.unlink()
  temp.rmdir();raise
 return "SCENARIO_STORED",target
