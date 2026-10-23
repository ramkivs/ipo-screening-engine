"""Auditable diagnostic observer; real service ingestion, no fabricated input/market values."""
import sys,os,json,hashlib,dataclasses,platform,traceback,base64,zlib,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'engine'))
from ipo_screening.presentation.service import PresentationService,PresentationConfig
from ipo_screening.extraction.extractor import DocumentExtractor
from ipo_screening.extraction.builder import CanonicalInputBuilder
from ipo_screening.issue_terms import IssueTermsResolver,OfficialDiscoveryProvider
from ipo_screening.aggregator_issue_terms import AggregatorIssueTermsResolver
# Observer files are separate from engine-owned immutable stores.
MODE=sys.argv[1];out=ROOT/'docs/investigation/jio-fresh-20261023'/sys.argv[2];out.mkdir(exist_ok=True,parents=True)
def save(name,data):
 (out/(name+'.json')).write_text(json.dumps(data,indent=2,default=str,ensure_ascii=False)+'\n')
def now():return datetime.now(timezone.utc).isoformat()
pdf=(ROOT/'evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf').read_bytes();assert hashlib.sha256(pdf).hexdigest()=='72480c2e249eb8da19a23283ecc6dec74627ed3caa2f8c370684acf9a59a1b6d'
old_build=CanonicalInputBuilder.build
builds=[]
def build(self,*a,**kw):
 before={'source':dataclasses.asdict(self.doc),'ordered_candidates':[dataclasses.asdict(x) for x in self.extractions],'reference_base':self.base}
 result=old_build(self,*a,**kw);builds.append({'before':before,'after':result});save('builder-stages',builds);return result
CanonicalInputBuilder.build=build
old_extract=DocumentExtractor.extract_from_pdf
def extract(self,*a,**kw):
 result,report=old_extract(self,*a,**kw);save('extraction-report',dataclasses.asdict(report));save('extracted-canonical-with-map',result)
 import pypdf
 reader=pypdf.PdfReader(kw['pdf_path']);save('source-page-contexts',{str(i):reader.pages[i-1].extract_text() for i in [5,44,45,93,94,104,109,116,117,122,312,322,324,405,430,451,487]})
 return result,report
DocumentExtractor.extract_from_pdf=extract
fetches=[]
def live(url):
 row={'url':url,'started_at':now(),'transport':'LIVE_HTTP_ATTEMPT'};fetches.append(row)
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=3) as r:b=r.read(2000001)
  row.update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b));return b
 except Exception as e:row['error']=repr(e);raise
 finally:row['finished_at']=now();save('source-transport',fetches)
if MODE=='live':
 official=IssueTermsResolver(providers=[OfficialDiscoveryProvider(fetcher=live)])
 agg=AggregatorIssueTermsResolver(fetcher=live)
else:
 # Existing public publisher bytes, re-parsed, not old evaluation input/results.
 # Explicit PA opt-in remains non-official and UNVERIFIED. No GMP is consumed.
 native=json.loads((ROOT/'docs/investigation/aggregator-fallback-2026-10-22/native-accepted.json').read_text())
 src=next(x for x in native['persisted_sources'] if 'chittorgarh' in x.get('uri',''))
 row=next(x for x in native['aggregator_source_bytes'] if x['sha256']==src['content_hash'])
 raw=zlib.decompress(base64.b64decode(row['raw_zlib_base64']));assert hashlib.sha256(raw).hexdigest()==src['content_hash']
 save('retained-source-receipt',{'scope':'RETAINED_PUBLISHER_BYTES_NOT_LIVE_FETCH','reference_commit':'ebb8a6c6b0d12e54228ec6b523bda025e927fb0b','container':'docs/investigation/aggregator-fallback-2026-10-22/native-accepted.json','source':src,'raw_sha256':hashlib.sha256(raw).hexdigest(),'consumed_at':now(),'qualification':'UNVERIFIED / PA opt-in issue terms only; not GMP qualification'})
 (out/'retained-publisher.html').write_bytes(raw)
 def cached(url):
  assert url==src['uri'];fetches.append({'url':url,'transport':'RETAINED_BYTES','accessed_at':now(),'original_retrieval_timestamp':src['retrieval_timestamp'],'sha256':src['content_hash']});save('source-transport',fetches);return raw
 class Retained(AggregatorIssueTermsResolver):
  def resolve(self,**kw):
   r=super().resolve(**kw)
   for candidates in r['fields'].values():
    for c in candidates:c['source']['retrieval_timestamp']=src['retrieval_timestamp']
   save('aggregator-resolution',r);return r
 official=IssueTermsResolver(providers=[])
 agg=Retained(fetcher=cached,urls={'JIO-PLATFORMS-LIMITED':src['uri']})
config=PresentationConfig(store_root=out/'evaluations',config_dir=ROOT/'config',dataset_path=None,analytics_path=None,issue_terms_resolver=official,aggregator_issue_terms_resolver=agg)
service=PresentationService(config)
# Capture actual assembled dictionary at evaluation boundary without modifying it.
import ipo_screening.presentation.service as mod
old_eval=mod.evaluate
def evaluate(*a,**kw):
 save('evaluation-call',{'args':a,'kwargs':kw});return old_eval(*a,**kw)
mod.evaluate=evaluate
runtime={'source_commit':os.environ.get('JIO_SOURCE_COMMIT'),'python':sys.version,'platform':platform.platform(),'pid':os.getpid(),'started_at':now(),'pdf_sha256':hashlib.sha256(pdf).hexdigest(),'mode':MODE,'manual_terms':False,'source_fingerprints':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'engine').rglob('*.py')}};save('runtime',runtime)
try:
 result=service.ingest_document(file_bytes=pdf,filename='U72900GJ2019PLC110816_JIO.pdf',mode='final');save('response',result.model_dump() if hasattr(result,'model_dump') else vars(result));print('SUCCESS',result,flush=True)
except BaseException as e:
 save('failure',{'type':type(e).__name__,'message':str(e),'ingestion_id':getattr(e,'ingestion_id',None),'traceback':traceback.format_exc()});print('FAILURE',repr(e),flush=True)
finally:
 save('activity-list',service.list_ingestion_activities(limit=100));runtime['finished_at']=now();save('runtime',runtime)
