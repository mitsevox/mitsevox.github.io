"""Event hints never replace the normal importer or widen producer trust."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from platform_fixtures import registered_root, POLICY, SLUG
from reporting.validation import ROOT, encoded
import refresh_reports as refresh
import notify_report
import build_notifier


def run(**updates):
    return dict({'id':42,'run_attempt':1,'head_sha':'a'*40,'head_branch':'main',
        'head_repository':{'full_name':POLICY['repository']},'event':'push','status':'completed',
        'conclusion':'success','path':POLICY['workflow']},**updates)


def lock_entry(number=42,attempt=1):
    return {'path':f'data/{SLUG}/snapshots/'+ 'a'*40+f'-v1-{number}-{attempt}',
        'revision':'a'*40,'manifestSha256':'b'*64}


class ReportRefreshTests(unittest.TestCase):
    def test_notifier_rejects_forks_failures_and_unrelated_workflows(self):
        event={'action':'completed','repository':{'full_name':POLICY['repository']},'workflow_run':run()}
        def notify(value):
            return notify_report.notification(value,SLUG,POLICY['repository'],'main',POLICY['workflow'],'mitsevox/portfolio')
        self.assertEqual(notify(event)['client_payload'],{'project':SLUG,'repository':POLICY['repository'],'runId':42})
        for update in ({'event':'pull_request'},{'head_branch':'topic'},{'conclusion':'failure'},
                       {'status':'in_progress'},{'path':'.github/workflows/other.yml'},
                       {'head_repository':{'full_name':'fork/test'}},{'id':True},{'id':-1}):
            with self.subTest(update=update),self.assertRaises(ValueError):notify({**event,'workflow_run':run(**update)})
        with self.assertRaises(ValueError):notify({**event,'repository':{'full_name':'fork/test'}})

    def test_receiver_reauthenticates_run_and_only_registered_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=registered_root(Path(temp)/'site')
            event={'client_payload':{'project':SLUG,'repository':POLICY['repository'],'runId':42}}
            class API:
                def get(self,path):
                    self.path=path
                    return run()
            api=API()
            self.assertEqual(refresh.validate_notification(root,event,lambda repo:api),SLUG)
            self.assertEqual(api.path,'actions/runs/42')
            for change in ({'repository':'fork/test'},{'runId':True},{'extra':'field'},{'project':'unknown'}):
                with self.assertRaises(ValueError):refresh.validate_notification(root,{'client_payload':{**event['client_payload'],**change}},lambda repo:api)
            with patch.object(api,'get',return_value=run(event='pull_request')):
                with self.assertRaises(ValueError):refresh.validate_notification(root,event,lambda repo:api)

    def test_repeated_notifications_skip_import_but_reruns_are_discovered(self):
        with tempfile.TemporaryDirectory() as temp:
            root=registered_root(Path(temp)/'site')
            class API:
                def get(self,path):return {'workflow_runs':[run(event='pull_request'),run()]}
            lock={'projects':{SLUG:lock_entry()}}
            with patch.object(refresh,'producers',return_value=[(SLUG,None,{**POLICY,'format':'report-v1'})]):
                self.assertEqual(refresh.changed_runs(root,lock,lambda repo:API()),({},[]))
                lock['projects'][SLUG]=lock_entry(attempt=2)
                self.assertEqual(refresh.changed_runs(root,lock,lambda repo:API()),({SLUG:42},[]))
            with self.assertRaises(ValueError):refresh.installed_run({**lock_entry(),'revision':'f'*40})

    def test_one_bad_producer_does_not_skip_other_changed_reports(self):
        calls=[]
        def importer(root,slug,number):
            calls.append(slug)
            if slug=='broken':raise ValueError('Producer workflow changed; review its policy')
        errors=[]
        refresh.refresh_changed(Path('/unused'),{'broken':1,'healthy':2},errors,importer)
        self.assertEqual(calls,['broken','healthy'])
        self.assertEqual(errors,[{'project':'broken','error':'Producer workflow changed; review its policy'}])

    def test_fast_lane_waits_for_successful_site_main(self):
        class API:
            def get(self,path):return {'workflow_runs':[run(path='.github/workflows/site.yml')]}
        api=API()
        self.assertTrue(refresh.successful_site_source(ROOT,'a'*40,api))
        for update in ({'event':'pull_request'},{'head_sha':'b'*40},{'conclusion':'failure'},
                       {'status':'in_progress'},{'path':'.github/workflows/other.yml'}):
            with patch.object(api,'get',return_value={'workflow_runs':[run(**{'path':'.github/workflows/site.yml',**update})]}):
                self.assertFalse(refresh.successful_site_source(ROOT,'a'*40,api))

    def test_batch_recovers_failed_publication_and_defers_untested_source(self):
        import os
        import sys
        with tempfile.TemporaryDirectory() as temp:
            root=registered_root(Path(temp)/'site')
            result_path=Path(temp)/'result.json'
            lock={'schemaVersion':1,'projects':{SLUG:lock_entry()}}
            environment={'GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_REPOSITORY':'mitsevox/mitsevox.github.io',
                'GITHUB_REF':'refs/heads/main'}
            with patch.object(refresh,'ROOT',root),patch.dict(os.environ,environment), \
                 patch.object(sys,'argv',['refresh_reports.py','--output',str(result_path)]), \
                 patch('report_store.git',return_value=('a'*40).encode()), \
                 patch('report_store.restore') as restore, \
                 patch.object(refresh,'successful_site_source',return_value=False) as verified, \
                 patch.object(refresh,'accepted_hint',return_value=lock), \
                 patch.object(refresh,'changed_runs',return_value=({},[])), \
                 patch.object(refresh,'live_lock',return_value=None), \
                 patch.object(refresh,'read_lock',return_value=lock):
                refresh.main()
                restore.assert_not_called()
                self.assertFalse(json.loads(result_path.read_text())['publish'])
                verified.return_value=True
                refresh.main()
                restore.assert_called_once_with(root)
                self.assertTrue(json.loads(result_path.read_text())['publish'])
                restore.reset_mock()
                with patch.object(refresh,'live_lock',return_value=lock):refresh.main()
                restore.assert_not_called()
                self.assertFalse(json.loads(result_path.read_text())['publish'])

    def test_notifier_is_reproducible_pinned_and_checks_before_minting_token(self):
        self.assertEqual((ROOT/'.github/workflows/notify-site.yml').read_text(),build_notifier.reusable())
        generated=build_notifier.caller(ROOT,'n100f','a'*40,'Validate')
        self.assertIn('notify-site.yml@'+'a'*40,generated)
        self.assertIn('workflow_run:',generated)
        self.assertNotIn('checkout@',build_notifier.reusable())
        self.assertLess(build_notifier.reusable().index('Validate completed main report event'),
                        build_notifier.reusable().index('Create site-scoped notification token'))
        with self.assertRaises(ValueError):build_notifier.caller(ROOT,'n100f','main','Validate')


if __name__=='__main__':unittest.main()
