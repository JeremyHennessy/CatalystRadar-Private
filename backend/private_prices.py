"""Ephemeral private API validation: prints metadata only, never quotes or secrets.
No public artifacts/cache/commit, no brokerage, no retries. No persistent history.
"""
import os,json,time,urllib.request,urllib.parse
from datetime import datetime,timezone,timedelta,date
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None
HTTP=urllib.request.build_opener(NoRedirect())

def budget(runs,now,current_run):
 if len(runs)>=100:raise ValueError('budget history truncated')
 recent=[]
 for row in runs:
  if str(row['id'])==str(current_run):continue
  status=row['status']
  if status not in ('completed','queued','in_progress','waiting','pending','requested'):raise ValueError('unknown run state')
  stamps=[]
  for field in ('created_at','run_started_at','updated_at'):
   value=datetime.fromisoformat(row[field].replace('Z','+00:00'))
   if value.tzinfo is None:raise ValueError('run timestamp lacks timezone')
   stamps.append(value)
  if status!='completed' or max(stamps)>=now-timedelta(hours=24):recent.append(row)
 # Completed update time conservatively upper-bounds when requests could occur.
 # Unresolved runs count regardless of age. Current run reserves another11calls.
 if len(recent)>1:raise ValueError('rolling request reservation exhausted')
 return True

def metadata(raw,ticker,observed):
 j=json.loads(raw)
 if any(k in j for k in ('Information','Note','Error Message')):raise ValueError('provider refused or quota unavailable')
 m=j['Meta Data'];series=j['Time Series (Daily)']
 if m['2. Symbol']!=ticker or m['5. Time Zone']!='US/Eastern':raise ValueError('source identity/timezone mismatch')
 dates=sorted(series)
 et=observed.astimezone(ZoneInfo('America/New_York'));latest=et.date()
 if et.hour<16:latest-=timedelta(days=1)
 while latest.weekday()>4:latest-=timedelta(days=1)
 # Fixed Nov14..21 trial has no exchange holidays; not a general calendar.
 if dates and dates[-1]!=latest.isoformat():raise ValueError('stale or unexpected latest session')
 if not dates or len(dates)>100 or m['3. Last Refreshed']!=dates[-1]:raise ValueError('unexpected compact coverage')
 for day in dates:
  parsed=date.fromisoformat(day)
  if day!=parsed.isoformat()or parsed>observed.date()or parsed.weekday()>4:raise ValueError('invalid date')
  row=series[day]
  if set(row)!={'1. open','2. high','3. low','4. close','5. volume'}:raise ValueError('not raw daily schema')
  o,h,l,c,v=[Decimal(str(row[k]))for k in ('1. open','2. high','3. low','4. close','5. volume')]
  if not all(x.is_finite()for x in(o,h,l,c,v))or min(o,h,l,c)<=0 or l>min(o,c)or h<max(o,c)or v<0 or v!=v.to_integral_value():raise ValueError('invalid OHLCV')
 return {'symbol':ticker,'returned_rows':len(dates),'first_session':dates[0],'last_session':dates[-1],'validation':'RAW_DAILY_SCHEMA_ONLY','calendar_complete':False,'corporate_actions_verified':False,'auction_verified':False,'eligible':False}

def run(mode):
 # Only this bounded repository workflow; no local fallback silently weakens quota guard.
 if os.environ.get('GITHUB_REPOSITORY')!='JeremyHennessy/CatalystRadar' or os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('workflow context required')
 now=datetime.now(timezone.utc)
 if os.environ.get('GITHUB_RUN_ATTEMPT')!='1':raise ValueError('retries disallowed to preserve quota reservation')
 if not datetime(2026,11,14,tzinfo=timezone.utc)<=now<datetime(2026,11,22,tzinfo=timezone.utc):raise ValueError('trial date gate')
 key=os.environ.get('ALPHA_VANTAGE_API_KEY','')
 if not key:raise ValueError('private secret unavailable')
 url='https://api.github.com/repos/JeremyHennessy/CatalystRadar/actions/workflows/private-prices.yml/runs?per_page=100'
 request=urllib.request.Request(url,headers={'User-Agent':'CatalystRadar-private-diagnostic','Authorization':'Bearer '+os.environ['GITHUB_TOKEN']})
 with HTTP.open(request,timeout=30)as response:history=json.load(response)
 budget(history['workflow_runs'],now,os.environ['GITHUB_RUN_ID'])
 symbols=['IBM'] if mode=='diagnostic' else [x['ticker'] for x in json.loads((Path(__file__).resolve().parent.parent/'data/watchlist.json').read_text())]+['SPY']
 if len(symbols)>11 or len(set(symbols))!=len(symbols)or any(not x.isalpha()or len(x)>5 for x in symbols):raise ValueError('invalid bounded symbols')
 result=[]
 for index,symbol in enumerate(symbols):
  if index:time.sleep(13)
  query=urllib.parse.urlencode({'function':'TIME_SERIES_DAILY','symbol':symbol,'apikey':key})
  with HTTP.open('https://www.alphavantage.co/query?'+query,timeout=30)as response:
   if response.status!=200:raise ValueError('provider response unavailable')
   raw=response.read(2000000)
  result.append(metadata(raw,symbol,datetime.now(timezone.utc)))
  del raw
 return {'observed_utc':datetime.now(timezone.utc).isoformat(),'scope':'EPHEMERAL_PRIVATE_VALIDATION_NOT_PERSISTED_HISTORY','budget_scope':'THIS_WORKFLOW_ONLY_EXTERNAL_KEY_USAGE_UNKNOWN','mode':mode,'symbols':result,'orders':0,'forecasts':[]}
def safe_report(mode):
 try:return {'ok':True,'report':run(mode)}
 except Exception:
  # No exception/body/url interpolation: any may contain a private key.
  return {'ok':False,'status':'STOPPED_SAFELY_SOURCE_QUOTA_SCHEMA_OR_AUTHORIZATION','orders':0}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['diagnostic','daily'],required=True);a=p.parse_args()
 r=safe_report(a.mode);print(json.dumps(r,indent=2));raise SystemExit(0 if r['ok'] else 1)
