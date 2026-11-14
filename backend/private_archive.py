"""Append-only private price snapshots, not connected to the public workflow.
Requires a caller-supplied, freshly fetched GitHub repository metadata response.
Caller must use authenticated official GitHub API and verify its provenance.
"""
from pathlib import Path
import os,json,hashlib,re,fcntl,base64
from datetime import datetime
from private_prices import metadata

def archive(root,raw,*,ticker,observed_utc,repo_metadata,expected_repository,forbidden_values):
 if repo_metadata.get('private')is not True or repo_metadata.get('visibility')!='private' or repo_metadata.get('full_name')!=expected_repository:raise ValueError('verified private repository required')
 if not expected_repository.startswith('JeremyHennessy/')or expected_repository=='JeremyHennessy/CatalystRadar':raise ValueError('wrong archive repository')
 if not re.fullmatch('[A-Z]{1,5}',ticker):raise ValueError('invalid symbol')
 if not forbidden_values or any(not isinstance(x,str)or not x for x in forbidden_values):raise ValueError('secret exclusion checks required')
 if any(x.encode()in raw for x in forbidden_values):raise ValueError('response contains forbidden secret material')
 observed=datetime.fromisoformat(observed_utc.replace('Z','+00:00'))
 if observed.tzinfo is None:raise ValueError('timezone required')
 quality=metadata(raw,ticker,observed)
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 if root.is_symlink():raise ValueError('symlink archive root')
 digest=hashlib.sha256(raw).hexdigest();identity=observed.strftime('%Y%m%dT%H%M%S%f%z')+'-'+ticker+'-'+digest
 # Immutable separate response and observation records; don't overwrite revisions.
 with (root/'.archive.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  target=root/(identity+'.json')
  envelope={'symbol':ticker,'observed_utc':observed_utc,'response_sha256':digest,'price_basis':'RAW_UNADJUSTED_DAILY_AGGREGATE_NOT_AUCTION','source_endpoint':'https://www.alphavantage.co/query','source_function':'TIME_SERIES_DAILY','source_outputsize':'compact','scope':'PRIVATE_PERSONAL_RESEARCH_ONLY','quality':quality,'response_base64':base64.b64encode(raw).decode('ascii')}
  payload=json.dumps(envelope,sort_keys=True,separators=(',',':')).encode()
  if target.exists():
   if target.is_symlink()or target.read_bytes()!=payload:raise ValueError('immutable archive conflict')
   return {'saved':False,'already_present':True,'symbol':ticker,'rows':quality['returned_rows']}
  fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb')as out:out.write(payload);out.flush();os.fsync(out.fileno())
 return {'saved':True,'already_present':False,'symbol':ticker,'rows':quality['returned_rows']}
