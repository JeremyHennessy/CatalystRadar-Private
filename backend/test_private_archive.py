import unittest,tempfile,json,base64,hashlib
from pathlib import Path
from private_archive import archive
class ArchiveTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'snapshots'
  self.raw=json.dumps({'Meta Data':{'2. Symbol':'TEST','5. Time Zone':'US/Eastern','3. Last Refreshed':'2026-11-13'},'Time Series (Daily)':{'2026-11-13':{'1. open':'10','2. high':'11','3. low':'9','4. close':'10','5. volume':'100'}}}).encode()
  self.args={'ticker':'TEST','observed_utc':'2026-11-14T17:00:00Z','repo_metadata':{'private':True,'visibility':'private','full_name':'JeremyHennessy/PrivateFixture'},'expected_repository':'JeremyHennessy/PrivateFixture','forbidden_values':['SYNTHETIC_NOT_A_KEY']}
 def test_idempotent_private(self):
  self.assertTrue(archive(self.root,self.raw,**self.args)['saved']);self.assertTrue(archive(self.root,self.raw,**self.args)['already_present']);self.assertEqual(len(list(self.root.glob('*.json'))),1);saved=json.loads(next(self.root.glob('*.json')).read_text());self.assertEqual(base64.b64decode(saved['response_base64']),self.raw);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),saved['response_sha256'])
 def test_public_rejected(self):
  self.args['repo_metadata']['private']=False
  with self.assertRaises(ValueError):archive(self.root,self.raw,**self.args)
  self.assertFalse(self.root.exists())
 def test_secret_rejected(self):
  self.args['forbidden_values']=['TEST']
  with self.assertRaises(ValueError):archive(self.root,self.raw,**self.args)
  self.assertFalse(self.root.exists())
 def test_revision_preserved(self):
  archive(self.root,self.raw,**self.args);new=self.raw.replace(b'"100"',b'"200"');archive(self.root,new,**self.args);self.assertEqual(len(list(self.root.glob('*.json'))),2)
if __name__=='__main__':unittest.main()
