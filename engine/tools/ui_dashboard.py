#!/usr/bin/env python3
"""Local single-user workbench for Layers 1, 2B/2C and operator scenarios."""
from __future__ import annotations
import copy, hashlib, html, json, logging, os, sys
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
 options='<option value="">-- Select an Evaluation --</option>'+"".join(f'<option value="{html.escape(r["id"])}">{html.escape(r["company"] or r["id"])}</option>' for r in _records())
 return rf'''<!doctype html><html><head><title>IPO Workbench</title><style>
*{{box-sizing:border-box}}body{{font:15px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:1200px;margin:auto;padding:2rem;color:#111827;background:#f8fafc}}section{{border:1px solid #e5e7eb;border-radius:10px;padding:1.25rem;margin:1.25rem 0;background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.04)}}h2{{display:flex;align-items:center;gap:.65rem;margin:0 0 1rem}}.badge{{display:inline-flex;align-items:center;border-radius:999px;padding:.25rem .6rem;background:#dcfce7;color:#166534;font:700 .72rem ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.02em}}.grid{{display:grid;gap:1rem}}.meta-grid,.multipliers-grid{{grid-template-columns:repeat(4,minmax(0,1fr))}}.three-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}.two-grid,.scenario-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.field-group{{display:flex;flex-direction:column;min-width:0}}.field-group label,.file-label{{font-weight:500;font-size:.85rem;color:#374151;margin:0 0 .25rem}}input,select,textarea{{width:100%;min-width:0;border:1px solid #d1d5db;border-radius:6px;background:#fff;color:#111827;font:inherit;padding:0 .7rem;transition:border-color .15s,box-shadow .15s}}input,select{{height:38px}}textarea{{min-height:92px;padding:.65rem .7rem;resize:vertical}}input:focus,select:focus,textarea:focus{{outline:none;border-color:#16a34a;box-shadow:0 0 0 3px rgba(22,163,74,.14)}}.card-block{{overflow:hidden;border:1px solid #e5e7eb;border-radius:8px;background:#fff;margin-top:1rem}}.card-block-header{{padding:.75rem 1.25rem;background:#fafafa;border-bottom:1px solid #e5e7eb;font-weight:650;color:#1f2937}}.card-block-body{{padding:1.25rem}}.action-bar{{display:flex;align-items:flex-end;justify-content:flex-end;flex-wrap:wrap;gap:1rem;margin-top:1rem;padding-top:1rem;border-top:1px solid #e5e7eb}}.action-bar .file-control{{flex:1 1 420px}}input[type=file]{{height:auto;padding:.45rem}}button{{height:38px;border:1px solid #15803d;border-radius:6px;background:#16a34a;color:#fff;font-weight:650;padding:0 1rem;cursor:pointer}}button:hover{{background:#15803d}}#dismiss-error{{display:none;margin-left:.5rem}}#dismiss-error.visible{{display:inline-block}}.source-pair{{display:grid;grid-template-columns:1fr 1fr;gap:.65rem}}.realities{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}}.card{{border:2px solid #174;padding:1rem;white-space:pre-wrap}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:.4rem}}#workbench-status{{padding:.8rem;margin:1rem 0;border-radius:.25rem}}#workbench-status:empty{{display:none}}#workbench-status.error{{display:block;background:#fff1f1;border:1px solid #b42318;color:#7a271a}}#workbench-status.success{{display:block;background:#ecfdf3;border:1px solid #067647;color:#05603a}}@media(max-width:900px){{.meta-grid,.multipliers-grid,.three-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.realities{{grid-template-columns:1fr}}}}@media(max-width:600px){{body{{padding:1rem}}.meta-grid,.multipliers-grid,.three-grid,.two-grid,.scenario-grid,.source-pair{{grid-template-columns:1fr}}.action-bar{{align-items:stretch}}.action-bar button{{width:100%}}}}
</style></head><body><h1>IPO Dual-Reality Workbench</h1><p>{html.escape(message)}</p>
<div id="workbench-status" role="alert" aria-live="polite"></div><button id="dismiss-error" type="button">Dismiss error</button>
<section><h2>Evaluation Explorer <span class="badge">[LAYER_1_BASE]</span></h2><select id="evaluation">{options}</select><button id="compare-button" type="button">Compare</button><div id="comparison" class="realities"></div></section>
<section><h2>Live Bidding <span class="badge">[ENRICHED_LAYER_2C]</span></h2>
<form id="inject-form" action="/actions/inject-rescore" method="post" enctype="multipart/form-data">
<div class="grid meta-grid">
<div class="field-group"><label for="baseline_id">Company</label><select id="baseline_id" name="baseline_id">{options}</select></div>
<div class="field-group"><label for="bidding_day">Bidding day</label><select id="bidding_day" name="bidding_day"><option value="">-- Select a Bidding Day --</option><option value="DAY_1">Day 1</option><option value="DAY_2">Day 2</option><option value="DAY_3">Day 3</option></select></div>
<div class="field-group"><label for="observation_time">Observation timestamp</label><input id="observation_time" name="observation_time" placeholder="2026-10-29T12:00:00Z" required></div>
<div class="source-pair"><div class="field-group"><label for="publisher">Publisher</label><input id="publisher" name="publisher" placeholder="Publisher" required></div><div class="field-group"><label for="source_id">Source ID</label><input id="source_id" name="source_id" placeholder="Source ID" required></div></div>
</div>
<div class="card-block"><div class="card-block-header">Bidding multipliers</div><div class="card-block-body grid multipliers-grid">
<div class="field-group"><label for="qib_x">QIB x</label><input id="qib_x" name="qib_x" type="number" step="any"></div><div class="field-group"><label for="nii_x">NII x</label><input id="nii_x" name="nii_x" type="number" step="any"></div><div class="field-group"><label for="retail_x">Retail x</label><input id="retail_x" name="retail_x" type="number" step="any"></div><div class="field-group"><label for="overall_x">Overall x</label><input id="overall_x" name="overall_x" type="number" step="any"></div>
</div></div>
<div class="card-block"><div class="card-block-header">Financial health and segment overrides</div><div class="card-block-body grid three-grid">
<div class="field-group"><label for="operating_cash_flow_3yr_cumulative">3Y cumulative operating cash flow</label><input id="operating_cash_flow_3yr_cumulative" name="operating_cash_flow_3yr_cumulative" type="number" step="any"></div><div class="field-group"><label for="net_income_3yr_cumulative">3Y cumulative net income</label><input id="net_income_3yr_cumulative" name="net_income_3yr_cumulative" type="number" step="any"></div><div class="field-group"><label for="trade_receivables_days">Trade receivables days</label><input id="trade_receivables_days" name="trade_receivables_days" type="number" step="any"></div><div class="field-group"><label for="net_working_capital_pct_revenue">Net working capital (% revenue)</label><input id="net_working_capital_pct_revenue" name="net_working_capital_pct_revenue" type="number" step="any"></div><div class="field-group"><label for="top_customer_revenue_pct">Largest customer revenue (%)</label><input id="top_customer_revenue_pct" name="top_customer_revenue_pct" type="number" min="0" max="100" step="any"></div><div class="field-group"><label for="loss_making_segments_present">Loss-making segments</label><select id="loss_making_segments_present" name="loss_making_segments_present"><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></div>
</div></div>
<div class="card-block"><div class="card-block-header">Legal and balance-sheet risk overrides</div><div class="card-block-body grid two-grid">
<div class="field-group"><label for="contingent_liabilities_pct_net_worth">Contingent liabilities (% net worth)</label><input id="contingent_liabilities_pct_net_worth" name="contingent_liabilities_pct_net_worth" type="number" min="0" step="any"></div><div class="field-group"><label for="material_regulatory_disputes_present">Material regulatory or tax disputes</label><select id="material_regulatory_disputes_present" name="material_regulatory_disputes_present"><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></div>
</div></div>
<div class="card-block"><div class="card-block-header">Governance overrides</div><div class="card-block-body grid two-grid">
<div class="field-group"><label for="promoter_pledged_shares_pct">Promoter pledged shares (%)</label><input id="promoter_pledged_shares_pct" name="promoter_pledged_shares_pct" type="number" min="0" max="100" step="any"></div><div class="field-group"><label for="pre_issue_promoter_holding_pct">Pre-issue promoter holding (%)</label><input id="pre_issue_promoter_holding_pct" name="pre_issue_promoter_holding_pct" type="number" min="0" max="100" step="any"></div>
</div></div>
<div class="action-bar"><div class="field-group file-control"><label class="file-label" for="evidence">Source evidence</label><input id="evidence" name="evidence" type="file" required><output id="evidenceHash"></output></div><button type="submit">Inject &amp; Rescore</button></div>
</form></section>
<section><h2>Scenario Builder <span class="badge">[OPERATOR_ASSUMPTION]</span></h2>
<form id="scenario-form" action="/actions/scenario" method="post">
<div class="card-block"><div class="card-block-header">Scenario context</div><div class="card-block-body grid scenario-grid">
<div class="field-group"><label for="target_id">Company</label><select id="target_id" name="target_id">{options}</select></div><div class="field-group"><label for="peer_name">Comparable peer</label><input id="peer_name" name="peer_name" placeholder="Peer name"></div><div class="field-group"><label for="peer_pe">Peer P/E</label><input id="peer_pe" name="peer_pe" type="number" step="any"></div><div class="field-group"><label for="peer_delta">Peer adjustment</label><input id="peer_delta" name="peer_delta" type="number" step="any"></div><div class="field-group"><label for="rating">Qualitative rating</label><select id="rating" name="rating"><option value="">-- Select a Rating --</option><option>LOW</option><option>MEDIUM</option><option>HIGH</option></select></div><div class="field-group"><label for="qualitative_delta">Qualitative adjustment</label><input id="qualitative_delta" name="qualitative_delta" type="number" step="any"></div>
</div></div>
<div class="card-block"><div class="card-block-header">Operator rationale</div><div class="card-block-body"><div class="field-group"><label for="justification">Justification</label><textarea id="justification" name="justification" required></textarea></div></div></div>
<div class="action-bar"><button type="submit">Apply Scenario</button></div>
</form></section>
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
const CONTROL_PATHS={{qib_x:'market.subscription.qib_x',nii_x:'market.subscription.nii_x',retail_x:'market.subscription.retail_x',overall_x:'market.subscription.overall_x',observation_time:'market.subscription.as_of',source_id:'market.subscription.source_id',operating_cash_flow_3yr_cumulative:'financials.operating_cash_flow_3yr_cumulative',net_income_3yr_cumulative:'financials.net_income_3yr_cumulative',trade_receivables_days:'financials.trade_receivables_days',net_working_capital_pct_revenue:'financials.net_working_capital_pct_revenue',top_customer_revenue_pct:'financials.top_customer_revenue_pct',loss_making_segments_present:'financials.loss_making_segments_present',promoter_pledged_shares_pct:'governance.promoter_pledged_shares_pct',pre_issue_promoter_holding_pct:'governance.pre_issue_promoter_holding_pct',contingent_liabilities_pct_net_worth:'risks.contingent_liabilities_pct_net_worth',material_regulatory_disputes_present:'risks.material_regulatory_disputes_present'}};
function valueAt(root,path){{return path.split('.').reduce((value,key)=>value&&typeof value==='object'?value[key]:undefined,root)}}
function resetFormState(){{document.querySelectorAll('#inject-form [name],#scenario-form [name]').forEach(control=>{{control.value=''}});document.getElementById('comparison').replaceChildren()}}
function hydrateFormState(input){{document.querySelectorAll('#inject-form [name],#scenario-form [name]').forEach(control=>{{if(['baseline_id','target_id','evidence'].includes(control.name))return;const path=CONTROL_PATHS[control.name]||control.name;const value=valueAt(input,path);if(value===undefined||value===null||Array.isArray(value)||typeof value==='object')return;control.value=typeof value==='boolean'?String(value):String(value)}});const defaults={{bidding_day:'DAY_1',rating:'LOW',peer_delta:'0',qualitative_delta:'0',justification:'Operator scenario only'}};Object.entries(defaults).forEach(([name,value])=>{{const control=document.querySelector(`[name="${{name}}"]`);if(control&&!control.value)control.value=value}})}}
async function loadEvaluation(identifier){{if(!identifier){{resetFormState();return}}clearError();const data=await parseResponse(await fetch('/api/v1/evaluations/'+encodeURIComponent(identifier)+'/input'));const input=data.input||(data.input_snapshot?.input)||data.input_snapshot||data;resetFormState();setActiveEvaluation(identifier);hydrateFormState(input);await explore(identifier);return data}}
async function refreshContext(){{try{{const response=await fetch('/api/v1/evaluations');const data=await parseResponse(response);const rows=Array.isArray(data)?data:(data.items||data.evaluations||[]);const ids=rows.map(x=>x.evaluation_id||x.id).filter(Boolean);if(!ids.length)showStatus('No evaluations are available in the active evaluation store.')}}catch(error){{showStatus(error.message)}}}}
async function explore(identifier){{clearError();try{{const id=typeof identifier==='string'?identifier:document.getElementById('evaluation').value;if(!id)return;setActiveEvaluation(id);const d=await parseResponse(await fetch('/api/v1/comparison/'+encodeURIComponent(id))),c=document.getElementById('comparison');c.innerHTML=`<div class="card"><b>[LAYER_1_BASE]</b><br>${{JSON.stringify(d.baseline,null,2)}}</div><div class="card"><b>[ENRICHED_LAYER_2C]</b><br>${{JSON.stringify(d.enriched,null,2)}}</div><div class="card"><b>[OPERATOR_ASSUMPTION]</b><br>${{JSON.stringify(d.scenarios,null,2)}}</div>`}}catch(error){{showStatus(error.message)}}}}
function bindWorkbench(){{document.getElementById('compare-button').addEventListener('click',explore);document.getElementById('evaluation').addEventListener('change',e=>loadEvaluation(e.target.value).catch(error=>showStatus(error.message)));document.querySelector('select[name="baseline_id"]').addEventListener('change',e=>loadEvaluation(e.target.value).catch(error=>showStatus(error.message)));
async function submitForm(event,successKind){{event.preventDefault();clearError();const form=event.currentTarget;const baseline=new FormData(form).get(successKind==='injection'?'baseline_id':'target_id');try{{const response=await fetch(form.action,{{method:'POST',body:new FormData(form),headers:{{'X-Workbench-Request':'fetch'}}}});const body=await parseResponse(response);setActiveEvaluation(baseline);saveSession({{evaluation_id:baseline,[successKind]:body}});showStatus(body.detail||`${{successKind}} succeeded.`,'success');if(successKind==='injection')await explore()}}catch(error){{showStatus(error.message)}}}}
document.getElementById('inject-form').addEventListener('submit',e=>submitForm(e,'injection'));
document.getElementById('scenario-form').addEventListener('submit',e=>submitForm(e,'scenario'));
document.getElementById('evidence').addEventListener('change',async e=>{{const f=e.target.files[0];if(!f)return;clearError();try{{const b=new FormData();b.append('evidence',f);const r=await parseResponse(await fetch('/api/v1/hash',{{method:'POST',body:b}}));document.getElementById('evidenceHash').textContent='SHA-256 '+r.sha256}}catch(error){{showStatus(error.message)}}}});document.body.dataset.workbenchReady='true';refreshContext().catch(error=>showStatus(error.message))}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bindWorkbench,{{once:true}});else bindWorkbench();
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
@app.get("/api/v1/evaluations")
def evaluations(): return _records()

@app.get("/api/evaluations/{evaluation_id}/input")
@app.get("/api/v1/evaluations/{evaluation_id}/input")
def evaluation_input(evaluation_id:str):
 try: evaluation_id=_resolve_evaluation_id(evaluation_id)
 except FileNotFoundError as exc: raise HTTPException(404,str(exc)) from exc
 record=EvaluationStore(L1).read_full(evaluation_id)
 snapshot=record.get("input_snapshot") or {}
 raw=copy.deepcopy(snapshot.get("input",snapshot) if isinstance(snapshot,dict) else {})
 for section in ("financials","governance","market","risks"): raw.setdefault(section,{})
 for block in (record.get("market_snapshot") or {}).get("blocks",[]):
  name=block.get("block");values=block.get("values")
  if name and isinstance(values,dict) and values:
   raw["market"].setdefault(name,{}).update(values)
   if block.get("as_of"): raw["market"][name]["as_of"]=block["as_of"]
 return {"evaluation_id":evaluation_id,"input":raw}

@app.get("/api/comparison/{baseline_id}")
@app.get("/api/v1/comparison/{baseline_id}")
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
@app.post("/api/v1/hash")
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
