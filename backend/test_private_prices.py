import unittest,json,os
from unittest.mock import patch,MagicMock
import private_prices
from contextlib import ExitStack
from datetime import datetime,timezone
from private_prices import metadata,budget
class PrivateTests(unittest.TestCase):
 def setUp(self):self.now=datetime(2026,11,14,17,tzinfo=timezone.utc);self.raw={'Meta Data':{'2. Symbol':'TEST','5. Time Zone':'US/Eastern','3. Last Refreshed':'2026-11-13'},'Time Series (Daily)':{'2026-11-13':{'1. open':'10','2. high':'11','3. low':'9','4. close':'10','5. volume':'100'}}}
 def test_error_text_never_exposed(self):
  with patch('private_prices.run',side_effect=ValueError('key=FAKE_SECRET_VALUE')):
   self.assertNotIn('FAKE_SECRET_VALUE',json.dumps(private_prices.safe_report('diagnostic')))
 def context(self):
  stack=ExitStack();fixed=self.now
  class FixedDatetime(datetime):
   @classmethod
   def now(cls,tz=None):return fixed
  stack.enter_context(patch('private_prices.datetime',FixedDatetime))
  stack.enter_context(patch.dict(os.environ,{'GITHUB_REPOSITORY':'JeremyHennessy/CatalystRadar','GITHUB_ACTIONS':'true','GITHUB_RUN_ATTEMPT':'1','GITHUB_RUN_ID':'123','GITHUB_TOKEN':'SYNTHETIC_TOKEN','ALPHA_VANTAGE_API_KEY':'SYNTHETIC_KEY'},clear=True))
  return stack

 def test_missing_key_zero_requests(self):
  with self.context(),patch('private_prices.HTTP.open')as request:
   os.environ.pop('ALPHA_VANTAGE_API_KEY');self.assertFalse(private_prices.safe_report('diagnostic')['ok']);request.assert_not_called()
 def test_retry_attempt_zero_requests(self):
  with self.context(),patch('private_prices.HTTP.open')as request:
   os.environ['GITHUB_RUN_ATTEMPT']='2';self.assertFalse(private_prices.safe_report('diagnostic')['ok']);request.assert_not_called()
 def test_provider_timeout_not_retried(self):
  with self.context(),patch('private_prices.HTTP.open')as request:
   history=MagicMock();history.__enter__.return_value.read.return_value=b'{"workflow_runs":[]}'
   request.side_effect=[history,TimeoutError('SYNTHETIC_KEY')]
   report=private_prices.safe_report('diagnostic');self.assertFalse(report['ok']);self.assertEqual(request.call_count,2);self.assertNotIn('SYNTHETIC_KEY',json.dumps(report))
 def test_redirects_disabled(self):self.assertIsNone(private_prices.NoRedirect().redirect_request(None,None,302,'',{},'https://evil.invalid'))
 def test_stale(self):
  self.raw['Meta Data']['3. Last Refreshed']='2026-11-12';self.raw['Time Series (Daily)']['2026-11-12']=self.raw['Time Series (Daily)'].pop('2026-11-13')
  with self.assertRaises(ValueError):metadata(json.dumps(self.raw).encode(),'TEST',self.now)
 def test_no_quotes_output(self):
  r=metadata(json.dumps(self.raw).encode(),'TEST',self.now);self.assertNotIn('close',r);self.assertEqual(r['returned_rows'],1);self.assertFalse(r['eligible'])
 def test_nan(self):
  self.raw['Time Series (Daily)']['2026-11-13']['4. close']='NaN'
  with self.assertRaises(ValueError):metadata(json.dumps(self.raw).encode(),'TEST',self.now)
 def test_wrong_symbol(self):
  with self.assertRaises(ValueError):metadata(json.dumps(self.raw).encode(),'BAD',self.now)
 def test_quota_message(self):
  with self.assertRaises(ValueError):metadata(b'{"Information":"secret-bearing provider text"}','TEST',self.now)
 def test_budget(self):
  rows=[{'id':1,'created_at':self.now.isoformat(),'run_started_at':self.now.isoformat(),'updated_at':self.now.isoformat(),'status':'completed'}];self.assertTrue(budget(rows,self.now,1));self.assertTrue(budget(rows,self.now,2))
  with self.assertRaises(ValueError):budget(rows+[{**rows[0],'id':2}],self.now,3)
 def test_delayed_runs_count_recent_activity(self):
  r={'id':1,'created_at':'2026-11-01T00:00:00Z','run_started_at':self.now.isoformat(),'updated_at':self.now.isoformat(),'status':'completed'}
  with self.assertRaises(ValueError):budget([r,{**r,'id':2}],self.now,3)
 def test_unresolved_old_runs_count(self):
  r={'id':1,'created_at':'2026-11-01T00:00:00Z','run_started_at':'2026-11-01T00:00:00Z','updated_at':'2026-11-01T00:00:00Z','status':'queued'}
  with self.assertRaises(ValueError):budget([r,{**r,'id':2}],self.now,3)
 def test_missing_run_timestamp_fails_closed(self):
  with self.assertRaises(KeyError):budget([{'id':1,'created_at':self.now.isoformat(),'status':'completed'}],self.now,3)
 def test_truncated_history(self):
  with self.assertRaises(ValueError):budget([{}]*100,self.now,1)
if __name__=='__main__':unittest.main()
