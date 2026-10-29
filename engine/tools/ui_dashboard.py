#!/usr/bin/env python3
"""Local single-user workbench for Layers 1, 2B/2C and operator scenarios."""
from __future__ import annotations
import hashlib, html, json, logging, os, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
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
logger=logging.getLogger("ipo_screening.workbench")


def _error(error:str,detail:str,status_code:int)->JSONResponse:
 return JSONResponse(status_code=status_code,content={"error":error,"detail":detail})


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_,exc:RequestValidationError):
 logger.warning("Workbench request validation failed: %s",exc)
 return _error("RequestValidationError",str(exc),400)


@app.exception_handler(HTTPException)
async def http_error_handler(_,exc:HTTPException):
 detail=exc.detail if isinstance(exc.detail,str) else json.dumps(exc.detail,sort_keys=True)
 return _error("WorkbenchRequestError",detail,exc.status_code)


@app.exception_handler(Exception)
async def unhandled_error_handler(_,exc:Exception):
 logger.exception("Unhandled workbench request failure")
 return _error(type(exc).__name__,str(exc) or "Unexpected workbench failure",500)


def _ensure_parent(target: str | Path) -> Path:
 """Create a target's complete parent tree before any Windows-safe write."""
 path=Path(target)
 os.makedirs(path.parent,exist_ok=True)
 return path


def _ensure_workbench_dirs() -> None:
 for directory in (ROOT,SUPP,SEC,OP,UPLOAD): os.makedirs(directory,exist_ok=True)


def configure_workbench(evaluation_store: str | Path, workbench_root: str | Path) -> None:
 """Point the workbench only at the evaluation store selected by its host API."""
 global L1, ROOT, SUPP, SEC, OP, UPLOAD
 L1=Path(evaluation_store).resolve();ROOT=Path(workbench_root).resolve()
 SUPP=ROOT/"supplemental";SEC=ROOT/"secondary";OP=ROOT/"operator";UPLOAD=ROOT/"uploads"
 _ensure_workbench_dirs()


def _resolve_evaluation_id(evaluation_id: str) -> str:
 """Reject stale IDs instead of searching historical or hardcoded stores."""
 requested=(evaluation_id or "").strip()
 if not requested or requested not in EvaluationStore(L1).list_evaluations():
  raise FileNotFoundError(f"Evaluation {requested or '<empty>'} is not in active store {L1}")
 return requested


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
 criterion:Literal["management_quality","moat","industry_growth","concentration","visibility"]
 rating:Literal["LOW","MEDIUM","HIGH"]
 points_delta:float=Field(ge=-15,le=15)
 justification:str=Field(min_length=1)


class ScenarioEvaluateRequest(BaseModel):
 model_config=ConfigDict(extra="forbid")
 target_id:str=Field(min_length=1)
 operator_id:str=Field(min_length=1)
 peer_assertions:list[PeerAssertionRequest]=Field(default_factory=list)
 qualitative_assertions:list[QualitativeAssertionRequest]=Field(default_factory=list)
 limitations:list[str]=Field(default_factory=lambda:["[OPERATOR_ASSUMPTION] User-asserted scenario; not verified evidence."])


async def _read_upload(upload:UploadFile,max_bytes:int=50*1024*1024)->tuple[str,bytes]:
 """Read either memory- or disk-spooled multipart uploads with a hard bound."""
 filename=Path(upload.filename or "evidence.bin").name
 if not filename or filename in {".",".."}: raise ValueError("Evidence filename is invalid")
 chunks=[];size=0
 while True:
  chunk=await upload.read(1024*1024)
  if not chunk: break
  size+=len(chunk)
  if size>max_bytes: raise ValueError(f"Evidence upload exceeds {max_bytes} bytes")
  chunks.append(chunk)
 if size==0: raise ValueError("Evidence upload is empty")
 return filename,b"".join(chunks)


def _records():
 store=EvaluationStore(L1); out=[]
 for eid in store.list_evaluations():
  r=store.read(eid); out.append({"id":eid,"company":r.get("company_name"),"score":r.get("score",{}).get("final_score"),"verdict":r.get("verdict",{}).get("verdict"),"confidence":r.get("confidence",{}).get("level"),"result_hash":r.get("result_hash")})
 return out

def _page(message=""):
 options="".join(f'<option value="{html.escape(r["id"])}">{html.escape(r["company"] or r["id"])}</option>' for r in _records())
 return rf'''<!doctype html><html><head><title>IPO Workbench</title><style>body{{font:15px system-ui;max-width:1200px;margin:auto;padding:2rem}}section{{border:1px solid #ccc;padding:1rem;margin:1rem 0}}.badge{{font-weight:bold;color:#174}}.realities{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}}.card{{border:2px solid #174;padding:1rem;white-space:pre-wrap}}input,select,textarea{{margin:.3rem;padding:.4rem}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:.4rem}}#workbench-status{{padding:.8rem;margin:1rem 0;border-radius:.25rem}}#workbench-status:empty{{display:none}}#workbench-status.error{{display:block;background:#fff1f1;border:1px solid #b42318;color:#7a271a}}#workbench-status.success{{display:block;background:#ecfdf3;border:1px solid #067647;color:#05603a}}#dismiss-error{{display:none;margin-left:.5rem}}#dismiss-error.visible{{display:inline-block}}</style></head><body><h1>IPO Dual-Reality Workbench</h1><p>{html.escape(message)}</p>
<div id="workbench-status" role="alert" aria-live="polite"></div><button id="dismiss-error" type="button">Dismiss error</button>
<section><h2>Evaluation Explorer <span class="badge">[LAYER_1_BASE]</span></h2><select id="evaluation">{options}</select><button id="compare-button" type="button">Compare</button><div id="comparison" class="realities"></div></section>
<section><h2>Live Bidding <span class="badge">[ENRICHED_LAYER_2C]</span></h2><form id="inject-form" action="actions/inject-rescore" method="post" enctype="multipart/form-data"><select name="baseline_id">{options}</select><select name="bidding_day"><option value="DAY_1">Day 1</option><option value="DAY_2">Day 2</option><option value="DAY_3">Day 3</option></select><input name="qib_x" type="number" step="any" placeholder="QIB x"><input name="nii_x" type="number" step="any" placeholder="NII x"><input name="retail_x" type="number" step="any" placeholder="Retail x"><input name="overall_x" type="number" step="any" placeholder="Overall x"><input name="observation_time" placeholder="2026-10-29T12:00:00Z" required><input name="publisher" placeholder="Publisher" required><input name="source_id" placeholder="Source ID" required><fieldset><legend>Financial health overrides (reporting unit)</legend><input name="operating_cash_flow_3yr_cumulative" type="number" step="any" placeholder="3Y cumulative OCF"><input name="net_income_3yr_cumulative" type="number" step="any" placeholder="3Y cumulative net income"><input name="trade_receivables_days" type="number" step="any" placeholder="Trade receivables days"><input name="net_working_capital_pct_revenue" type="number" step="any" placeholder="NWC % revenue"><input name="top_customer_revenue_pct" type="number" min="0" max="100" step="any" placeholder="Largest customer revenue %"><select name="loss_making_segments_present"><option value="">Loss-making segments: unknown</option><option value="true">Loss-making segments: yes</option><option value="false">Loss-making segments: no</option></select></fieldset><fieldset><legend>Legal and balance-sheet risk overrides</legend><input name="contingent_liabilities_pct_net_worth" type="number" min="0" step="any" placeholder="Contingent liabilities % net worth"><select name="material_regulatory_disputes_present"><option value="">Material regulatory/tax disputes: unknown</option><option value="true">Material regulatory/tax disputes: yes</option><option value="false">Material regulatory/tax disputes: no</option></select></fieldset><fieldset><legend>Governance overrides</legend><input name="promoter_pledged_shares_pct" type="number" min="0" max="100" step="any" placeholder="Promoter pledged shares %"><input name="pre_issue_promoter_holding_pct" type="number" min="0" max="100" step="any" placeholder="Pre-issue promoter holding %"></fieldset><input id="evidence" name="evidence" type="file" required><output id="evidenceHash"></output><button>Inject &amp; Rescore</button></form></section>
<section><h2>Scenario Builder <span class="badge">[OPERATOR_ASSUMPTION]</span></h2><form id="scenario-form" action="actions/scenario" method="post"><select name="target_id">{options}</select><input name="peer_name" placeholder="Peer"><input name="peer_pe" type="number" step="any" placeholder="Peer P/E"><input name="peer_delta" type="number" step="any" value="0"><select name="rating"><option>LOW</option><option>MEDIUM</option><option>HIGH</option></select><input name="qualitative_delta" type="number" step="any" value="0"><textarea name="justification" required>Operator scenario only</textarea><button>Apply Scenario</button></form></section>
<footer>Lineage always displays exact baseline, supplemental, secondary, and scenario SHA-256 identities. Operator assertions never alter governed records.</footer>
<script>
const SESSION_KEY='ipo.workbench.session.v1';
const statusBox=document.getElementById('workbench-status'),dismiss=document.getElementById('dismiss-error');
function readSession(){{try{{return JSON.parse(sessionStorage.getItem(SESSION_KEY)||'{{}}')}}catch(_e){{return {{}}}}}}
function saveSession(patch){{const value={{...readSession(),...patch}};sessionStorage.setItem(SESSION_KEY,JSON.stringify(value));return value}}
function clearError(){{statusBox.textContent='';statusBox.className='';dismiss.classList.remove('visible')}}
function showStatus(detail,kind='error'){{statusBox.textContent=detail;statusBox.className=kind;dismiss.classList.toggle('visible',kind==='error')}}
dismiss.addEventListener('click',clearError);
function setActiveEvaluation(id){{if(!id)return;document.querySelectorAll('select[name="baseline_id"],select[name="target_id"],#evaluation').forEach(el=>{{if([...el.options].some(o=>o.value===id))el.value=id}});saveSession({{evaluation_id:id}})}}
async function parseResponse(response){{const type=response.headers.get('content-type')||'';let body;if(type.includes('json'))body=await response.json();else body={{detail:(await response.text()).replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim()}};if(!response.ok)throw new Error(body.detail||body.error||`Request failed (${{response.status}})`);return body}}
async function refreshContext(){{try{{const response=await fetch('api/evaluations');const rows=await parseResponse(response);const ids=rows.map(x=>x.id);const session=readSession(),cached=session.evaluation_id;const active=ids.includes(cached)?cached:ids[0];if(active){{setActiveEvaluation(active);if(session.injection?.evaluation_id===active)showStatus(session.injection.detail||'Previous injection restored.','success')}}else showStatus('No evaluations are available in the active evaluation store.')}}catch(error){{showStatus(error.message)}}}}
async function explore(){{clearError();try{{const id=document.getElementById('evaluation').value;setActiveEvaluation(id);const d=await parseResponse(await fetch('api/comparison/'+encodeURIComponent(id))),c=document.getElementById('comparison');c.innerHTML=`<div class="card"><b>[LAYER_1_BASE]</b><br>${{JSON.stringify(d.baseline,null,2)}}</div><div class="card"><b>[ENRICHED_LAYER_2C]</b><br>${{JSON.stringify(d.enriched,null,2)}}</div><div class="card"><b>[OPERATOR_ASSUMPTION]</b><br>${{JSON.stringify(d.scenarios,null,2)}}</div>`}}catch(error){{showStatus(error.message)}}}}
document.getElementById('compare-button').addEventListener('click',explore);
document.getElementById('evaluation').addEventListener('change',e=>setActiveEvaluation(e.target.value));
async function submitForm(event,successKind){{event.preventDefault();clearError();const form=event.currentTarget;const baseline=new FormData(form).get(successKind==='injection'?'baseline_id':'target_id');try{{const response=await fetch(form.action,{{method:'POST',body:new FormData(form),headers:{{'X-Workbench-Request':'fetch'}}}});const body=await parseResponse(response);setActiveEvaluation(baseline);saveSession({{evaluation_id:baseline,[successKind]:body}});showStatus(body.detail||`${{successKind}} succeeded.`,'success');if(successKind==='injection')await explore()}}catch(error){{showStatus(error.message)}}}}
document.getElementById('inject-form').addEventListener('submit',e=>submitForm(e,'injection'));
document.getElementById('scenario-form').addEventListener('submit',e=>submitForm(e,'scenario'));
document.getElementById('evidence').addEventListener('change',async e=>{{const f=e.target.files[0];if(!f)return;clearError();try{{const b=new FormData();b.append('evidence',f);const r=await parseResponse(await fetch('api/hash',{{method:'POST',body:b}}));document.getElementById('evidenceHash').textContent='SHA-256 '+r.sha256}}catch(error){{showStatus(error.message)}}}});
refreshContext();
</script></body></html>'''

@app.get("/",response_class=HTMLResponse)
@app.get("/workbench",response_class=HTMLResponse)
def index(): return _page()


@app.post("/api/v1/secondary/evaluate")
def api_secondary_evaluate(request:SecondaryEvaluateRequest):
 try:
  baseline_id=_resolve_evaluation_id(request.baseline_id)
  _ensure_workbench_dirs()
  secondary=build_secondary(baseline_id,EvaluationStore(L1),SUPP,request.supplemental_id)
  outcome,path=store_secondary(secondary,SEC,EvaluationStore(L1))
 except FileNotFoundError as exc:
  raise HTTPException(404,str(exc)) from exc
 except ValueError as exc:
  logger.info("Secondary evaluation rejected: %s",exc)
  return _error("SecondaryEvaluationError",str(exc),400)
 except Exception as exc:
  logger.exception("Secondary evaluation failed")
  return _error(type(exc).__name__,str(exc),500)
 return {"outcome":outcome,"path":str(path),"secondary":secondary}


@app.post("/api/v1/scenario/evaluate")
def api_scenario_evaluate(request:ScenarioEvaluateRequest):
 try:
  target_id=_resolve_evaluation_id(request.target_id)
  _ensure_workbench_dirs()
  payload=scenario_template(target_id)
  payload.update({"created_at":datetime.now(timezone.utc).isoformat(),"operator_id":request.operator_id,"peer_assertions":[x.model_dump() for x in request.peer_assertions],"qualitative_assertions":[x.model_dump() for x in request.qualitative_assertions],"limitations":request.limitations})
  payload=finalize_scenario(payload)
  result=evaluate_scenario(payload,EvaluationStore(L1),SEC)
  outcome,path=store_scenario(payload,result,OP,EvaluationStore(L1))
 except FileNotFoundError as exc:
  raise HTTPException(404,str(exc)) from exc
 except ValueError as exc:
  logger.info("Scenario evaluation rejected: %s",exc)
  return _error("ScenarioEvaluationError",str(exc),400)
 except Exception as exc:
  logger.exception("Scenario evaluation failed")
  return _error(type(exc).__name__,str(exc),500)
 return {"outcome":outcome,"path":str(path),"scenario_payload":payload,"scenario":result}


@app.get("/api/evaluations")
def evaluations(): return _records()

@app.get("/api/comparison/{baseline_id}")
def comparison(baseline_id:str):
 try: baseline_id=_resolve_evaluation_id(baseline_id)
 except FileNotFoundError as exc: raise HTTPException(404,str(exc)) from exc
 base=next((x for x in _records() if x["id"]==baseline_id),None)
 enriched=[]
 for p in SEC.glob(f"{baseline_id}/*/secondary_evaluation.json"): enriched.append(json.loads(p.read_text()))
 scenarios=[]
 for p in OP.glob(f"{baseline_id}/*/scenario_result.json"): scenarios.append(json.loads(p.read_text()))
 return {"baseline":{"badge":"[LAYER_1_BASE]",**base},"enriched":[{"badge":"[ENRICHED_LAYER_2C]",**x} for x in enriched],"scenarios":[{"badge":"[OPERATOR_ASSUMPTION]",**x} for x in scenarios]}

@app.post("/api/hash")
async def hash_file(evidence:UploadFile=File(...)):
 try:
  filename,data=await _read_upload(evidence)
  return {"filename":filename,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
 except ValueError as exc:
  return _error("EvidenceUploadError",str(exc),400)
 except Exception as exc:
  logger.exception("Evidence hashing failed")
  return _error(type(exc).__name__,str(exc),500)

@app.post("/actions/inject-rescore",response_class=HTMLResponse)
async def inject_rescore(
 request:Request,baseline_id:str=Form(...),bidding_day:str=Form(...),observation_time:str=Form(...),
 publisher:str|None=Form(None),source_id:str|None=Form(None),evidence:UploadFile=File(...),
 qib_x:float|None=Form(None),nii_x:float|None=Form(None),
 retail_x:float|None=Form(None),overall_x:float|None=Form(None),
 operating_cash_flow_3yr_cumulative:float|None=Form(None),net_income_3yr_cumulative:float|None=Form(None),
 trade_receivables_days:float|None=Form(None),net_working_capital_pct_revenue:float|None=Form(None),
 top_customer_revenue_pct:float|None=Form(None),loss_making_segments_present:str|None=Form(None),
 contingent_liabilities_pct_net_worth:float|None=Form(None),material_regulatory_disputes_present:str|None=Form(None),
 promoter_pledged_shares_pct:float|None=Form(None),pre_issue_promoter_holding_pct:float|None=Form(None),
):
 try:
  baseline_id=_resolve_evaluation_id(baseline_id)
  _ensure_workbench_dirs()
  publisher=(publisher or "").strip();source_id=(source_id or "").strip()
  if not publisher or not source_id: raise ValueError("publisher and source_id are required")
  observed=datetime.fromisoformat(observation_time.replace("Z","+00:00"))
  if observed.tzinfo is None: raise ValueError("observation_time must include a timezone")
  filename,data=await _read_upload(evidence)
  segment_flag=(loss_making_segments_present or "").strip().lower()
  if segment_flag not in {"","true","false"}: raise ValueError("loss_making_segments_present must be true or false")
  segment_value=None if not segment_flag else segment_flag=="true"
  dispute_flag=(material_regulatory_disputes_present or "").strip().lower()
  if dispute_flag not in {"","true","false"}: raise ValueError("material_regulatory_disputes_present must be true or false")
  dispute_value=None if not dispute_flag else dispute_flag=="true"
  values={"qib_x":qib_x,"nii_x":nii_x,"retail_x":retail_x,"overall_x":overall_x,"operating_cash_flow_3yr_cumulative":operating_cash_flow_3yr_cumulative,"net_income_3yr_cumulative":net_income_3yr_cumulative,"trade_receivables_days":trade_receivables_days,"net_working_capital_pct_revenue":net_working_capital_pct_revenue,"top_customer_revenue_pct":top_customer_revenue_pct,"loss_making_segments_present":segment_value,"contingent_liabilities_pct_net_worth":contingent_liabilities_pct_net_worth,"material_regulatory_disputes_present":dispute_value,"promoter_pledged_shares_pct":promoter_pledged_shares_pct,"pre_issue_promoter_holding_pct":pre_issue_promoter_holding_pct}
  if all(value is None for value in values.values()): raise ValueError("at least one subscription, financial-health, segment-risk, regulatory-risk, or governance value is required")
  digest=hashlib.sha256(data).hexdigest()
  artifact=_ensure_parent(UPLOAD/baseline_id/f"{digest}-{filename}")
  if not artifact.exists(): artifact.write_bytes(data)
  template=initialize_template(EvaluationStore(L1),baseline_id);entries=[]
  for entry in template["entries"]:
   key=entry["target"].rsplit(".",1)[1]
   if values[key] is None: continue
   entry["value"]=values[key];entry["observation_time"]=observation_time;entry["reporting_period"]=bidding_day
   entry["source"].update({"source_id":source_id,"title":filename,"publisher":publisher,"publication_date":observed.date().isoformat(),"official_url":None,"artifact_ref":os.path.relpath(artifact,ROOT),"artifact_sha256":digest,"locator":"Operator-selected uploaded artifact"})
   entry["operator_attestation"]={"operator_id":"local-workbench","attested_at":datetime.now(timezone.utc).isoformat(),"statement":"I selected this local artifact; attestation is accountability metadata, not authentication."}
   entry["verification"]={"status":"SOURCE_ARTIFACT_HASH_VERIFIED","procedure_note":"Workbench verified only the uploaded local bytes."}
   entry["limitations"]=["Storage is not publisher authenticity, value truth, or scoring eligibility."];entries.append(entry)
  template["entries"]=entries;template["created_at"]=datetime.now(timezone.utc).isoformat();payload=finalize_payload(template)
  payload_path=_ensure_parent(ROOT/"payloads"/baseline_id/f"{payload['supplemental_payload_id']}.json")
  if not payload_path.exists(): payload_path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
  outcome,_,validation=store_payload(payload,EvaluationStore(L1),SUPP,payload_base=ROOT)
  if not validation.accepted: return _error("SupplementalInjectionError","; ".join(validation.errors),400)
  secondary=build_secondary(baseline_id,EvaluationStore(L1),SUPP,payload["supplemental_payload_id"])
  sec_out,_=store_secondary(secondary,SEC,EvaluationStore(L1))
  detail=f"{outcome}; {sec_out}; {secondary['secondary_evaluation_id']} hash {secondary['canonical_secondary_hash']}"
  if request.headers.get("x-workbench-request")=="fetch":
   return JSONResponse({"detail":detail,"evaluation_id":baseline_id,"supplemental_id":payload["supplemental_payload_id"],"secondary_id":secondary["secondary_evaluation_id"]})
  return _page(detail)
 except (ValueError,FileNotFoundError) as exc:
  logger.info("Supplemental injection rejected: %s",exc)
  return _error("SupplementalInjectionError",str(exc),400)
 except Exception as exc:
  logger.exception("Supplemental injection failed")
  return _error(type(exc).__name__,str(exc),500)

@app.post("/actions/scenario",response_class=HTMLResponse)
def apply_scenario(request:Request,target_id:str=Form(...),peer_name:str=Form(""),peer_pe:float|None=Form(None),peer_delta:float=Form(0),rating:str=Form("LOW"),qualitative_delta:float=Form(0),justification:str=Form(...)):
 try:
  target_id=_resolve_evaluation_id(target_id)
  _ensure_workbench_dirs()
  peer_name=peer_name.strip();justification=justification.strip()
  if not justification: raise ValueError("scenario justification is required")
  if bool(peer_name)!=(peer_pe is not None): raise ValueError("peer_name and peer_pe must be supplied together")
  payload=scenario_template(target_id);payload.update({"created_at":datetime.now(timezone.utc).isoformat(),"operator_id":"local-workbench"})
  if peer_name: payload["peer_assertions"]=[{"peer_name":peer_name,"pe":peer_pe,"as_of":datetime.now(timezone.utc).date().isoformat(),"points_delta":peer_delta,"justification":justification}]
  payload["qualitative_assertions"]=[{"criterion":"moat","rating":rating,"points_delta":qualitative_delta,"justification":justification}]
  payload=finalize_scenario(payload);result=evaluate_scenario(payload,EvaluationStore(L1),SEC)
  outcome,_=store_scenario(payload,result,OP,EvaluationStore(L1))
  detail=f"{outcome}; {result['scenario_id']} hash {result['canonical_result_hash']}"
  if request.headers.get("x-workbench-request")=="fetch":
   return JSONResponse({"detail":detail,"evaluation_id":target_id,"scenario_id":result["scenario_id"]})
  return _page(detail)
 except (ValueError,FileNotFoundError) as exc:
  logger.info("Scenario form rejected: %s",exc)
  return _error("ScenarioEvaluationError",str(exc),400)
 except Exception as exc:
  logger.exception("Scenario form failed")
  return _error(type(exc).__name__,str(exc),500)

if __name__=="__main__":
 import uvicorn
 uvicorn.run(app,host="0.0.0.0",port=int(os.environ.get("PORT","8000")))
