"""Read-only discovery of actual public aggregator issue links; no term values supplied."""
import base64, hashlib, json, os, re, time, traceback, urllib.request, zlib
from http.cookiejar import CookieJar
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.rows=[]; self.current=None
    def handle_starttag(self,tag,attrs):
        if tag=='a': self.current=[dict(attrs).get('href',''),'']
    def handle_data(self,text):
        if self.current is not None:self.current[1]+=text
    def handle_endtag(self,tag):
        if tag=='a' and self.current is not None:self.rows.append(self.current);self.current=None

out=Path(os.environ['JIO_RECOVERY_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
queue=[('https://www.chittorgarh.com/ipo/ipo_dashboard.asp',False),
       ('https://www.chittorgarh.com/report/ipo-in-india-list-main-board-sme/82/',False),
       ('https://www.investorgain.com/report/live-ipo-gmp/331/',False)]
allowed={'www.chittorgarh.com','chittorgarh.com','www.investorgain.com','investorgain.com'}
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
rows=[];seen=set()
for _ in range(10):
    if not queue:break
    uri,detail=queue.pop(0)
    if uri in seen:continue
    seen.add(uri);row={'uri':uri,'detail':detail}
    try:
        request=urllib.request.Request(uri,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html,application/json'})
        with opener.open(request,timeout=20) as response:
            assert urlparse(response.url).hostname in allowed
            raw=response.read(2_000_001)
            assert len(raw)<=2_000_000, 'bounded response limit'
            row['final_uri']=response.url
        row.update(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        (out/(row['sha256']+'.html')).write_bytes(raw)
        text=raw.decode('utf-8',errors='replace');parser=Links();parser.feed(text)
        row['matched_links']=[]
        for href,label in parser.rows:
            if re.search(r'jio[\s-]+platforms',href+' '+label,re.I):
                target=urljoin(row['final_uri'],href)
                row['matched_links'].append({'uri':target,'label':label})
                if urlparse(target).hostname in allowed:queue.append((target,True))
        if detail:row['raw_zlib_base64']=base64.b64encode(zlib.compress(raw)).decode()
        else:
            row['script_srcs']=re.findall(r'<script[^>]+src=["\']([^"\']+)',text,re.I)[:30]
            row['issuer_contexts']=[text[max(0,m.start()-200):m.end()+800] for m in list(re.finditer('jio',text,re.I))[:15]]
    except Exception:row['traceback']=traceback.format_exc()
    rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='raw_zlib_base64'}),flush=True);time.sleep(1)
result={'scope':'Actual third-party public source research only, not ingestion acceptance','requests':rows}
(out/'source-probe.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
packed=base64.b64encode(zlib.compress(json.dumps(result).encode())).decode()
for i,start in enumerate(range(0,len(packed),55000)):
    payload={'name':f'Aggregator source research {i}','head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral',
      'output':{'title':'Actual aggregator source research','summary':'Read-only publisher bytes/links; no invented financial terms.','text':packed[start:start+55000]}}
    req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(payload).encode(),method='POST',headers={'Authorization':'Bearer '+os.environ['LIVE_CHECK_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:print(json.load(response)['html_url'],flush=True)
