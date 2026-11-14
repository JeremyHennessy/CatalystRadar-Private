"""Single private collector. Raw prices never leave this private repository."""
import os,json,time,urllib.request,urllib.parse,base64
from pathlib import Path
from datetime import datetime,timezone
from private_prices import HTTP,budget
from private_archive import archive
REPO='JeremyHennessy/CatalystRadar-Private'
PUBLIC_RETIRED_WORKFLOW_SHA='8b1312de5fe67781cabd4a58553ca7181c2ab690'
SYMBOLS=('COHR','HRB','CINF','TXMD','RVTY','EMR','GT','KEY','WOR','XRX','SPY')
ROOT=Path(__file__).resolve().parent.parent

def api(path):
 req=urllib.request.Request('https://api.github.com/'+path,headers={'User-Agent':'CatalystRadar-private-research','Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json'})
 with HTTP.open(req,timeout=30)as r:return json.load(r)

def privacy():
 repo=api('repos/'+REPO)
 if repo.get('private')is not True or repo.get('visibility')!='private' or repo.get('full_name')!=REPO:raise ValueError('private repository required')
 collaborators=api('repos/'+REPO+'/collaborators?per_page=100')
 if not isinstance(collaborators,list)or len(collaborators)>=100 or not {x['login'] for x in collaborators}.issubset({'JeremyHennessy'}):raise ValueError('owner-only access required')
 return repo

def gate(now):
 if os.environ.get('GITHUB_REPOSITORY')!=REPO or os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_RUN_ATTEMPT')!='1':raise ValueError('wrong workflow context/retry')
 if not datetime(2026,11,14,tzinfo=timezone.utc)<=now<datetime(2026,11,22,tzinfo=timezone.utc):raise ValueError('trial date gate')
 repo=privacy()
 retired=api('repos/JeremyHennessy/CatalystRadar/contents/.github/workflows/private-prices.yml?ref=main')
 if retired.get('sha')!=PUBLIC_RETIRED_WORKFLOW_SHA:raise ValueError('public workflow retirement changed/unverified')
 history=[]
 for repository,workflow in [('JeremyHennessy/CatalystRadar','private-prices.yml'),(REPO,'collect.yml')]:
  runs=api('repos/'+repository+'/actions/workflows/'+workflow+'/runs?per_page=100')['workflow_runs']
  if len(runs)>=100:raise ValueError('history truncated')
  if repository!=REPO and any(x['status']!='completed' for x in runs):raise ValueError('public consumer unresolved')
  history.extend(runs)
 budget(history,now,os.environ['GITHUB_RUN_ID'])
 return repo

def collect():
 key=os.environ.get('ALPHA_VANTAGE_API_KEY','');token=os.environ.get('GITHUB_TOKEN','')
 if not key or not token:raise ValueError('missing private credentials')
 repo=gate(datetime.now(timezone.utc));results=[]
 for index,symbol in enumerate(SYMBOLS):
  if index:time.sleep(13)
  query=urllib.parse.urlencode({'function':'TIME_SERIES_DAILY','symbol':symbol,'apikey':key})
  with HTTP.open('https://www.alphavantage.co/query?'+query,timeout=30)as response:
   if response.status!=200:raise ValueError('provider failure')
   raw=response.read(2000000)
  observed=datetime.now(timezone.utc).isoformat()
  result=archive(ROOT/'data/prices',raw,ticker=symbol,observed_utc=observed,repo_metadata=repo,expected_repository=REPO,forbidden_values=[key,token])
  results.append(result);del raw
 privacy() # reverify before allowing workflow commit/push
 report={'observed_utc':datetime.now(timezone.utc).isoformat(),'saved_snapshots':sum(x['saved']for x in results),'symbols':results,'orders':0,'forecasts':[],'price_basis':'RAW_DAILY_NOT_AUCTION_OR_TOTAL_RETURN','scope':'PRIVATE_PERSONAL_RESEARCH'}
 (ROOT/'data/latest-collection.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 import sys
 try:
  if '--verify-privacy' in sys.argv:privacy();print('Verified private owner-only repository')
  else:print(json.dumps(collect(),indent=2))
 except Exception:
  print('Private collection stopped safely. No retry, no secret/error/body disclosure, no orders.');raise SystemExit(1)
