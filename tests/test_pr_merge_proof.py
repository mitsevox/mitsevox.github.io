"""Temporary PR merge commits are authenticated once, then retained by the consumer."""
import base64
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from platform_fixtures import POLICY, SLUG, registered_root, report
import test_platform as platform_tests
from import_reports import verify_reuse
from reporting.github import GitHub
from reporting.state import accepted_package, install, read_lock
from reporting.validation import decode, digest, encoded


class PRMergeProofTests(unittest.TestCase):
    archive=platform_tests.ImportExecutionTests.archive
    execution=platform_tests.ImportExecutionTests.execution
    artifact=platform_tests.ImportExecutionTests.artifact

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=registered_root(self.base/'site')
        self.merge='f'*40;self.head='4'*40;self.parent='3'*40
        _,original=report(self.base/'original',revision=self.merge,metadata_updates={
            'runId':41,'measuredAt':'2026-10-25T09:00:00Z','publishedAt':'2026-10-25T09:01:00Z'})
        self.raw=self.archive(original)
        self.run,self.job=self.execution(self.head,41)
        self.proof={'runId':41,'attempt':1,'artifactId':99,'artifactSha256':digest(self.raw),
                    'revision':self.merge,'tree':'e'*40,'measuredAt':'2026-10-25T09:00:00Z'}
        self.manifest,self.payloads=report(self.base/'reused',metadata_updates={
            'mode':'reused','source':self.proof,'measuredAt':self.proof['measuredAt']})
        self.receipt=decode(self.payloads['receipt.json'])
        self.responses={
            'actions/runs/41/attempts/1':self.run,
            f"contents/{POLICY['workflow']}?ref={self.head}":{'sha':'c'*40},
            'actions/artifacts/99':self.artifact(self.raw,self.head,41,99),
            'git/commits/'+self.head:{'sha':self.head,'tree':{'sha':'e'*40}},
            'git/commits/'+self.merge:{'sha':self.merge,'tree':{'sha':'e'*40},
                                      'parents':[{'sha':self.parent},{'sha':self.head}]}}
        self.pull={'head':{'sha':self.head,'repo':{'full_name':POLICY['repository']}},
                   'base':{'sha':self.parent,'ref':'main','repo':{'full_name':POLICY['repository']}},
                   'state':'closed','merged_at':'2026-10-25T10:00:00Z'}
        self.calls=[]

    def verify(self,retained=None):
        def get(api,path):
            self.calls.append(path)
            if path not in self.responses:raise AssertionError('Unexpected API lookup: '+path)
            return self.responses[path]
        def pages(api,path,field=None):
            self.calls.append(path)
            if path=='actions/runs/41/attempts/1/jobs':return [self.job]
            if path=='commits/'+self.head+'/pulls':return [self.pull]
            raise AssertionError(path)
        with patch.object(GitHub,'get',get),patch.object(GitHub,'pages',pages), \
             patch.object(GitHub,'raw',return_value=self.raw):
            return verify_reuse(self.root,GitHub(POLICY['repository']),POLICY,self.manifest,self.receipt,retained)

    def test_pr_merge_is_bound_to_run_head_parents_tree_and_original_artifact(self):
        retained=self.verify()
        self.assertEqual(retained['parents'],[self.parent,self.head])
        self.assertEqual(retained['revision'],self.merge)
        self.assertEqual(retained['head'],self.head)
        self.assertIn(f"contents/{POLICY['workflow']}?ref={self.head}",self.calls)
        self.assertNotIn(f"contents/{POLICY['workflow']}?ref={self.merge}",self.calls)

    def test_later_import_uses_retained_evidence_when_tested_merge_is_gone(self):
        retained=self.verify();self.calls=[]
        del self.responses['git/commits/'+self.merge]
        self.assertEqual(self.verify(retained),retained)
        self.assertNotIn('git/commits/'+self.merge,self.calls)
        self.assertNotIn('commits/'+self.head+'/pulls',self.calls)
        self.responses['git/commits/'+self.head]['tree']['sha']='0'*40
        with self.assertRaisesRegex(ValueError,'tree'):self.verify(retained)

    def test_wrong_merge_parents_tree_revision_and_foreign_pr_fail(self):
        original=copy.deepcopy(self.responses['git/commits/'+self.merge])
        for parents in ([self.head,self.parent],[self.parent,'5'*40],[self.head],[self.parent,self.head,'5'*40]):
            self.responses['git/commits/'+self.merge]={**original,'parents':[{'sha':p} for p in parents]}
            with self.subTest(parents=parents),self.assertRaisesRegex(ValueError,'parents'):self.verify()
        for key,value in [('sha','0'*40),('tree',{'sha':'0'*40})]:
            self.responses['git/commits/'+self.merge]={**original,key:value}
            with self.subTest(key=key),self.assertRaises(ValueError):self.verify()
        self.responses['git/commits/'+self.merge]=original
        self.pull['head']['repo']['full_name']='someone/fork'
        with self.assertRaisesRegex(ValueError,'source PR'):self.verify()

    def test_artifact_must_identify_run_head_not_tested_merge(self):
        self.responses['actions/artifacts/99']['workflow_run']['head_sha']=self.merge
        with self.assertRaisesRegex(ValueError,'artifact'):self.verify()

    def test_retained_metadata_must_match_the_proof_and_an_accepted_lock(self):
        retained=self.verify()
        install(self.root,None,self.manifest,self.payloads,{'title':'fixture'},source_proof=retained)
        entry=read_lock(self.root)['projects'][SLUG]
        self.assertEqual(entry['sourceProof'],retained)
        accepted={'encoding':'base64','content':base64.b64encode(encoded(read_lock(self.root))).decode()}
        with patch.object(GitHub,'get',return_value=accepted):
            self.assertTrue(accepted_package(self.root,SLUG,entry))
            changed=copy.deepcopy(entry);changed['sourceProof']['base']='0'*40
            self.assertFalse(accepted_package(self.root,SLUG,changed))
        changed=copy.deepcopy(retained);changed['artifactSha256']='0'*64
        with self.assertRaisesRegex(ValueError,'proof differs'):
            install(self.root,None,self.manifest,self.payloads,{'title':'fixture'},source_proof=changed)

    def test_staged_policy_cannot_activate_or_authorize_new_tools(self):
        from package_report import package
        from reporting.registry import producer
        from reporting.validation import validate_package
        registry=decode((self.root/'config/producers.json').read_bytes())
        pending=copy.deepcopy(POLICY);pending['tools']=[{'name':'next-tool','identity':'next-pin'}]
        (self.root/'config/pending-producer.json').write_bytes(encoded(pending))
        registry[SLUG]['pending']={'format':'report-v1','policy':'pending-producer.json'}
        (self.root/'config/producers.json').write_bytes(encoded(registry))
        self.assertEqual(producer(self.root,SLUG)['tools'],POLICY['tools'])
        validate_package(self.base/'reused/package',self.root)
        metadata={**decode((self.base/'original/package/receipt.json').read_bytes()),
                  'project':SLUG,'tools':pending['tools']}
        package(self.base/'original/input',metadata,pending,self.base/'pending-package')
        with self.assertRaisesRegex(ValueError,'registered producer policy'):
            validate_package(self.base/'pending-package',self.root)


# Storage runs the actual validators and Git writer, with compact packages.
import test_report_store as store_tests

class SourceProofStoreTests(unittest.TestCase):
    setUp=store_tests.ReportStoreTests.setUp
    git=store_tests.ReportStoreTests.git

    def test_proof_cache_survives_publish_restore_and_an_intervening_full_build(self):
        import report_store
        registered_root(self.repo);registered_root(self.site)
        source={'runId':41,'attempt':1,'artifactId':99,'artifactSha256':'b'*64,
                'revision':'f'*40,'tree':'e'*40,'measuredAt':'2026-10-25T09:00:00Z'}
        captured={**source,'schemaVersion':1,'repository':POLICY['repository'],'event':'pull_request',
                  'head':'4'*40,'base':'3'*40,'parents':['3'*40,'4'*40],'workflowBlob':'c'*40}
        manifest,payloads=report(self.base/'proof-report',timeline=True,metadata_updates={
            'mode':'reused','source':source,'measuredAt':source['measuredAt']})
        install(self.site,None,manifest,payloads,{'title':'fixture'},source_proof=captured)
        first=report_store.publish(self.repo,self.site);report_store.restore(self.repo)
        expected=read_lock(self.site)['projects'][SLUG]
        self.assertEqual(read_lock(self.repo)['projects'][SLUG],expected)
        self.assertEqual(report_store.stored_lock(self.repo,first)['projects'][SLUG],expected)
        full,payloads=report(self.base/'full-report',timeline=True,metadata_updates={'runId':43})
        install(self.repo,None,full,payloads,{'title':'full build'})
        after=read_lock(self.repo)['projects'][SLUG]
        self.assertNotIn('sourceProof',after)
        self.assertEqual(after['sourceProofs'],{source['artifactSha256']:captured})


if __name__=='__main__':unittest.main()
