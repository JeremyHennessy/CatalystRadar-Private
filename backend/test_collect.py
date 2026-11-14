import unittest,json,os,tempfile
from unittest.mock import patch,MagicMock
from datetime import datetime,timezone
from pathlib import Path
import collect
class CollectorTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,11,14,19,tzinfo=timezone.utc);self.repo={'private':True,'visibility':'private','full_name':collect.REPO}
 def environment(self):return patch.dict(os.environ,{'GITHUB_REPOSITORY':collect.REPO,'GITHUB_ACTIONS':'true','GITHUB_RUN_ATTEMPT':'1','GITHUB_RUN_ID':'3','GITHUB_TOKEN':'TOKEN_FIXTURE_ONLY','ALPHA_VANTAGE_API_KEY':'KEY_FIXTURE_ONLY'},clear=True)
 def test_private_zero_collaborators(self):
  with patch('collect.api',side_effect=[self.repo,[]]):self.assertEqual(collect.privacy(),self.repo)
 def test_public_repo_rejected(self):
  with patch('collect.api',return_value={**self.repo,'private':False}):
   with self.assertRaises(ValueError):collect.privacy()
 def test_collaborator_rejected(self):
  with patch('collect.api',side_effect=[self.repo,[{'login':'someone'}]]):
   with self.assertRaises(ValueError):collect.privacy()
 def test_retired_workflow_required(self):
  with self.environment(),patch('collect.privacy',return_value=self.repo),patch('collect.api',return_value={'sha':'wrong'}):
   with self.assertRaises(ValueError):collect.gate(self.now)
 def test_public_outstanding_blocks(self):
  with self.environment(),patch('collect.privacy',return_value=self.repo),patch('collect.api',side_effect=[{'sha':collect.PUBLIC_RETIRED_WORKFLOW_SHA},{'workflow_runs':[{'status':'in_progress'}]}]):
   with self.assertRaises(ValueError):collect.gate(self.now)
 def test_empty_history_gate(self):
  with self.environment(),patch('collect.privacy',return_value=self.repo),patch('collect.api',side_effect=[{'sha':collect.PUBLIC_RETIRED_WORKFLOW_SHA},{'workflow_runs':[]},{'workflow_runs':[]}]):self.assertEqual(collect.gate(self.now),self.repo)
 def test_success_private_retention(self):
  class Clock(datetime):
   @classmethod
   def now(cls,tz=None):return datetime(2026,11,14,19,tzinfo=timezone.utc)
  responses=[]
  for symbol in collect.SYMBOLS:
   raw=json.dumps({'Meta Data':{'2. Symbol':symbol,'5. Time Zone':'US/Eastern','3. Last Refreshed':'2026-11-13'},'Time Series (Daily)':{'2026-11-13':{'1. open':'10','2. high':'11','3. low':'9','4. close':'10','5. volume':'100'}}}).encode();response=MagicMock();response.__enter__.return_value.status=200;response.__enter__.return_value.read.return_value=raw;responses.append(response)
  with tempfile.TemporaryDirectory()as d,self.environment(),patch('collect.ROOT',Path(d)),patch('collect.datetime',Clock),patch('collect.gate',return_value=self.repo),patch('collect.privacy',return_value=self.repo),patch('collect.time.sleep'),patch('collect.HTTP.open',side_effect=responses)as fetch:
   r=collect.collect();self.assertEqual(r['saved_snapshots'],11);self.assertEqual(fetch.call_count,11);self.assertEqual(len(list((Path(d)/'data/prices').glob('*.json'))),11);self.assertNotIn('close',json.dumps(r));self.assertNotIn('KEY_FIXTURE_ONLY',json.dumps(r))
if __name__=='__main__':unittest.main()
