#!/usr/bin/env python3
"""Local single-user workbench for Layers 1, 2B/2C and operator scenarios."""
from __future__ import annotations
import hashlib, html, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

if __package__ in (None,""): sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ipo_screening.evaluation import EvaluationStore
from ipo_screening.supplemental_data import finalize_payload, initialize_template, store_payload
from ipo_screening.secondary_evaluation import build_secondary, store_secondary
from ipo_screening.operator_scenario import evaluate_scenario, finalize_scenario, scenario_template, store_scenario

ROOT=Path(os.environ.get("IPO_WORKBENCH_ROOT","build/workbench")).resolve()
L1=Path(os.environ.get("IPO_EVALUATION_STORE","build/evaluations")).resolve()
SUPP=ROOT/"supplemental"; SEC=ROOT/"secondary"; OP=ROOT/"operator"; UPLOAD=ROOT/"uploads"
app=FastAPI(title="IPO Dual-Reality Workbench",version="1.0",docs_url="/api/docs")


class SecondaryEvaluateRequest(BaseModel):
 model_config=ConfigDict(extra="forbid")
 baseline_id:str=Field(min_length=1)
 supplemental_id:str=Field(pattern=r"^SUPP-[0-9a-f]{16}$")


class PeerAssertionRequest(BaseModel):
 model_config=ConfigDict(extra="forbid")
 peer_name:str=Field(min_length=1)
 pe:float=Field(gt=0)
 as_of:str
 points_delta:float=Field(ge=-20,le=20)
 justification:str=Field(min_length=1)


class QualitativeAssertionRequest(BaseModel):
 model_config=ConfigDict(extra="forbid")
 criterion:str
 rating:str
 points_delta:float=Field(ge=-15,le=15)
 justification:str=Field(min_length=1)


class ScenarioEvaluateRequest(BaseModel):
 model_config=ConfigDict(extra="forbid")
 target_id:str=Field(min_length=1)
 operator_id:str=Field(min_length=1)
 peer_assertions:list[PeerAssertionRequest]=Field(default_factory=list)
 qualitative_assertions:list[QualitativeAssertionRequest]=Field(default_factory=list)
 limitations:list[str]=Field(default_factory=lambda:["[OPERATOR_ASSUMPTION] User-asserted scenario; not verified evidence."])


def _records():
 store=EvaluationStore(L1); out=[]
 for eid in store.list_evaluations():
  r=store.read(eid); out.append({"id":eid,"company":r.get("company_name"),"score":r.get("score",{}).get("final_score"),"verdict":r.get("verdict",{}).get("verdict"),"confidence":r.get("confidence",{}).get("level"),"result_hash":r.get("result_hash")})
 return out

def _page(message=""):
 options="".join(f'<option value="{html.escape(r["id"])}">{html.escape(r["company"] or r["id"])}</option>' for r in _records())
 return f'''<!doctype html><html><head><title>IPO Workbench</title><style>body{{font:15px system-ui;max-width:1200px;margin:auto;padding:2rem}}section{{border:1px solid #ccc;padding:1rem;margin:1rem 0}}.badge{{font-weight:bold;color:#174}}.realities{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}}.card{{border:2px solid #174;padding:1rem;white-space:pre-wrap}}input,select,textarea{{margin:.3rem;padding:.4rem}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:.4rem}}</style></head><body><h1>IPO Dual-Reality Workbench</h1><p>{html.escape(message)}</p>
<section><h2>Evaluation Explorer <span class="badge">[LAYER_1_BASE]</span></h2><select id="evaluation">{options}</select><button onclick="explore()">Compare</button><div id="comparison" class="realities"></div></section>
<section><h2>Live Bidding <span class="badge">[ENRICHED_LAYER_2C]</span></h2><form action="/actions/inject-rescore" method="post" enctype="multipart/form-data"><select name="baseline_id">{options}</select><select name="bidding_day"><option value="DAY_1">Day 1</option><option value="DAY_2">Day 2</option><option value="DAY_3">Day 3</option></select><input name="qib_x" type="number" step="any" placeholder="QIB x"><input name="nii_x" type="number" step="any" placeholder="NII x"><input name="retail_x" type="number" step="any" placeholder="Retail x"><input name="overall_x" type="number" step="any" placeholder="Overall x"><input name="observation_time" placeholder="2026-10-29T12:00:00Z" required><input name="publisher" placeholder="Publisher" required><input name="source_id" placeholder="Source ID" required><input id="evidence" name="evidence" type="file" required><output id="evidenceHash"></output><button>Inject &amp; Rescore</button></form></section>
<section><h2>Scenario Builder <span class="badge">[OPERATOR_ASSUMPTION]</span></h2><form action="/actions/scenario" method="post"><select name="target_id">{options}</select><input name="peer_name" placeholder="Peer"><input name="peer_pe" type="number" step="any" placeholder="Peer P/E"><input name="peer_delta" type="number" step="any" value="0"><select name="rating"><option>LOW</option><option>MEDIUM</option><option>HIGH</option></select><input name="qualitative_delta" type="number" step="any" value="0"><textarea name="justification" required>Operator scenario only</textarea><button>Apply Scenario</button></form></section>
<footer>Lineage always displays exact baseline, supplemental, secondary, and scenario SHA-256 identities. Operator assertions never alter governed records.</footer><script>async function explore(){{let id=document.getElementById('evaluation').value,d=await(await fetch('/api/comparison/'+encodeURIComponent(id))).json(),c=document.getElementById('comparison');c.innerHTML=`<div class="card"><b>[LAYER_1_BASE]</b><br>${{JSON.stringify(d.baseline,null,2)}}</div><div class="card"><b>[ENRICHED_LAYER_2C]</b><br>${{JSON.stringify(d.enriched,null,2)}}</div><div class="card"><b>[OPERATOR_ASSUMPTION]</b><br>${{JSON.stringify(d.scenarios,null,2)}}</div>`}}document.getElementById('evidence').addEventListener('change',async(e)=>{{let f=e.target.files[0];if(!f)return;let b=new FormData();b.append('evidence',f);let r=await(await fetch('/api/hash',{{method:'POST',body:b}})).json();document.getElementById('evidenceHash').textContent='SHA-256 '+r.sha256}})</script></body></html>'''

@app.get("/",response_class=HTMLResponse)
@app.get("/workbench",response_class=HTMLResponse)
def index(): return _page()


@app.post("/api/v1/secondary/evaluate")
def api_secondary_evaluate(request:SecondaryEvaluateRequest):
 try:
  secondary=build_secondary(request.baseline_id,EvaluationStore(L1),SUPP,request.supplemental_id)
  outcome,path=store_secondary(secondary,SEC,EvaluationStore(L1))
 except FileNotFoundError as exc:
  raise HTTPException(404,str(exc)) from exc
 except ValueError as exc:
  raise HTTPException(400,str(exc)) from exc
 return {"outcome":outcome,"path":str(path),"secondary":secondary}


@app.post("/api/v1/scenario/evaluate")
def api_scenario_evaluate(request:ScenarioEvaluateRequest):
 payload=scenario_template(request.target_id)
 payload.update({"created_at":datetime.now(timezone.utc).isoformat(),"operator_id":request.operator_id,"peer_assertions":[x.model_dump() for x in request.peer_assertions],"qualitative_assertions":[x.model_dump() for x in request.qualitative_assertions],"limitations":request.limitations})
 payload=finalize_scenario(payload)
 try:
  result=evaluate_scenario(payload,EvaluationStore(L1),SEC)
  outcome,path=store_scenario(payload,result,OP,EvaluationStore(L1))
 except FileNotFoundError as exc:
  raise HTTPException(404,str(exc)) from exc
 except ValueError as exc:
  raise HTTPException(400,str(exc)) from exc
 return {"outcome":outcome,"path":str(path),"scenario_payload":payload,"scenario":result}


@app.get("/api/evaluations")
def evaluations(): return _records()

@app.get("/api/comparison/{baseline_id}")
def comparison(baseline_id:str):
 base=next((x for x in _records() if x["id"]==baseline_id),None)
 if not base: raise HTTPException(404,"baseline not found")
 enriched=[]
 for p in SEC.glob(f"{baseline_id}/*/secondary_evaluation.json"): enriched.append(json.loads(p.read_text()))
 scenarios=[]
 for p in OP.glob(f"{baseline_id}/*/scenario_result.json"): scenarios.append(json.loads(p.read_text()))
 return {"baseline":{"badge":"[LAYER_1_BASE]",**base},"enriched":[{"badge":"[ENRICHED_LAYER_2C]",**x} for x in enriched],"scenarios":[{"badge":"[OPERATOR_ASSUMPTION]",**x} for x in scenarios]}

@app.post("/api/hash")
async def hash_file(evidence:UploadFile=File(...)):
 data=await evidence.read(); return {"filename":evidence.filename,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}

@app.post("/actions/inject-rescore",response_class=HTMLResponse)
async def inject_rescore(baseline_id:str=Form(...),bidding_day:str=Form(...),observation_time:str=Form(...),publisher:str=Form(...),source_id:str=Form(...),evidence:UploadFile=File(...),qib_x:float|None=Form(None),nii_x:float|None=Form(None),retail_x:float|None=Form(None),overall_x:float|None=Form(None)):
 data=await evidence.read(); UPLOAD.mkdir(parents=True,exist_ok=True); digest=hashlib.sha256(data).hexdigest(); artifact=UPLOAD/f"{digest}-{Path(evidence.filename or 'evidence').name}"; artifact.write_bytes(data)
 template=initialize_template(EvaluationStore(L1),baseline_id); values={"qib_x":qib_x,"nii_x":nii_x,"retail_x":retail_x,"overall_x":overall_x}; entries=[]
 for entry in template["entries"]:
  key=entry["target"].rsplit(".",1)[1]
  if values[key] is None: continue
  entry["value"]=values[key]; entry["observation_time"]=observation_time; entry["reporting_period"]=bidding_day
  entry["source"].update({"source_id":source_id,"title":evidence.filename or "Uploaded demand evidence","publisher":publisher,"publication_date":observation_time[:10],"official_url":None,"artifact_ref":os.path.relpath(artifact,ROOT),"artifact_sha256":digest,"locator":"Operator-selected uploaded artifact"})
  entry["operator_attestation"]={"operator_id":"local-workbench","attested_at":datetime.now(timezone.utc).isoformat(),"statement":"I selected this local artifact; attestation is accountability metadata, not authentication."}; entry["verification"]={"status":"SOURCE_ARTIFACT_HASH_VERIFIED","procedure_note":"Workbench verified only the uploaded local bytes."}; entry["limitations"]=["Storage is not publisher authenticity, value truth, or scoring eligibility."]; entries.append(entry)
 template["entries"]=entries; template["created_at"]=datetime.now(timezone.utc).isoformat(); payload=finalize_payload(template); ROOT.mkdir(parents=True,exist_ok=True); payload_path=ROOT/f"{payload['supplemental_payload_id']}.json"; payload_path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 outcome,_,validation=store_payload(payload,EvaluationStore(L1),SUPP,payload_base=ROOT)
 if not validation.accepted: raise HTTPException(400,"; ".join(validation.errors))
 secondary=build_secondary(baseline_id,EvaluationStore(L1),SUPP,payload["supplemental_payload_id"]); sec_out,path=store_secondary(secondary,SEC,EvaluationStore(L1))
 return _page(f"{outcome}; {sec_out}; {secondary['secondary_evaluation_id']} hash {secondary['canonical_secondary_hash']}")

@app.post("/actions/scenario",response_class=HTMLResponse)
def apply_scenario(target_id:str=Form(...),peer_name:str=Form(""),peer_pe:float|None=Form(None),peer_delta:float=Form(0),rating:str=Form("LOW"),qualitative_delta:float=Form(0),justification:str=Form(...)):
 p=scenario_template(target_id); p.update({"created_at":datetime.now(timezone.utc).isoformat(),"operator_id":"local-workbench"})
 if peer_name and peer_pe is not None:p["peer_assertions"]=[{"peer_name":peer_name,"pe":peer_pe,"as_of":datetime.now(timezone.utc).date().isoformat(),"points_delta":peer_delta,"justification":justification}]
 p["qualitative_assertions"]=[{"criterion":"moat","rating":rating,"points_delta":qualitative_delta,"justification":justification}]; p=finalize_scenario(p); result=evaluate_scenario(p,EvaluationStore(L1),SEC); outcome,path=store_scenario(p,result,OP,EvaluationStore(L1)); return _page(f"{outcome}; {result['scenario_id']} hash {result['canonical_result_hash']}")

if __name__=="__main__":
 import uvicorn
 uvicorn.run(app,host="0.0.0.0",port=int(os.environ.get("PORT","8000")))
