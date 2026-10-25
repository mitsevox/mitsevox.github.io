import copy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import report_store
from reporting.validation import ROOT, decode, encoded


class ReportStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.remote=self.base/'remote.git'
        subprocess.run(['git','init','--bare','--initial-branch=main',str(self.remote)],check=True,capture_output=True)
        self.repo=self.base/'site';self.repo.mkdir()
        self.git('init','--initial-branch=main')
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','Site source')
        self.git('remote','add','origin',str(self.remote))
        self.git('push','origin','main')
        self.sha=self.git('rev-parse','HEAD').decode().strip()
        self.env=patch.dict(os.environ,{'GITHUB_REPOSITORY':'mitsevox/mitsevox.github.io',
            'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'push','GITHUB_SHA':self.sha})
        self.env.start();self.addCleanup(self.env.stop)
        self.site=self.base/'built';self.site.mkdir()
        self.lock=decode((ROOT/'data/reports.lock.json').read_bytes())
        entry=self.lock['projects']['nflstreet2']
        shutil.copytree(ROOT/entry['path'],self.site/entry['path'])
        (self.site/report_store.LOCK).write_bytes(encoded(self.lock))

    def git(self,*args):return subprocess.check_output(['git',*args],cwd=self.repo,stderr=subprocess.DEVNULL)

    def test_bootstrap_rerun_restore_and_data_only_contents(self):
        first=report_store.publish(self.repo,self.site)
        self.assertEqual(first,report_store.publish(self.repo,self.site))
        names=self.git('ls-tree','-r','--name-only',first).decode().splitlines()
        self.assertEqual(len(names),6)
        self.assertTrue(all(n.startswith('data/') for n in names))
        report_store.restore(self.repo)
        self.assertEqual(decode((self.repo/report_store.LOCK).read_bytes()),self.lock)
        self.assertEqual(self.git('rev-parse','HEAD').decode().strip(),self.sha)

    def test_new_commit_metadata_preserves_prior_store_revision(self):
        first=report_store.publish(self.repo,self.site)
        changed=copy.deepcopy(self.lock)
        changed['projects']['nflstreet2']['latestCommit']['title']='New repository activity'
        (self.site/report_store.LOCK).write_bytes(encoded(changed))
        second=report_store.publish(self.repo,self.site)
        self.assertNotEqual(first,second)
        self.assertEqual(self.git('rev-parse',second+'^').decode().strip(),first)
        self.assertEqual(decode(self.git('show',first+':'+report_store.LOCK)),self.lock)

    def test_branch_and_pr_cannot_publish(self):
        for key,value in [('GITHUB_REF','refs/heads/codex/test'),('GITHUB_EVENT_NAME','pull_request'),
                          ('GITHUB_REPOSITORY','someone/fork')]:
            with patch.dict(os.environ,{key:value}), self.assertRaises(ValueError):
                report_store.publish(self.repo,self.site)
        self.assertIsNone(report_store.remote_head(self.repo))

    def test_corrupt_candidate_leaves_store_unchanged(self):
        first=report_store.publish(self.repo,self.site)
        entry=self.lock['projects']['nflstreet2']
        (self.site/entry['path']/'progress.json').write_text('{}')
        with self.assertRaises(ValueError):report_store.publish(self.repo,self.site)
        self.assertEqual(report_store.remote_head(self.repo),first)

    def test_stale_site_revision_cannot_publish_even_identical_reports(self):
        first=report_store.publish(self.repo,self.site)
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','New source')
        self.git('push','origin','main')
        with self.assertRaisesRegex(ValueError,'no longer current'):
            report_store.publish(self.repo,self.site)
        self.assertEqual(report_store.remote_head(self.repo),first)

    def test_newer_local_report_is_retained_only_with_history_continuity(self):
        report_store.publish(self.repo,self.site)
        report_store.restore(self.repo)
        entry, stored, activity, payloads=report_store.stored_package(self.repo,report_store.remote_head(self.repo))
        newer=copy.deepcopy(stored);newer['revision']='a'*40
        local_lock=copy.deepcopy(self.lock)
        local_lock['projects']['nflstreet2']['revision']=newer['revision']
        (self.repo/report_store.LOCK).write_bytes(encoded(local_lock))
        # Keep real Git/storage and test the ancestry-selection boundary with
        # independently validated package results supplied at that boundary.
        with patch.object(report_store,'stored_package',return_value=(entry,stored,activity,payloads)), \
             patch.object(report_store,'validate_package',return_value=(newer,{},activity)), \
             patch.object(report_store.GitHub,'get',return_value={'status':'ahead'}):
            report_store.restore(self.repo)
            self.assertEqual(decode((self.repo/report_store.LOCK).read_bytes()),local_lock)
            missing=copy.deepcopy(activity);missing['snapshots']=[]
            with patch.object(report_store,'validate_package',return_value=(newer,{},missing)), self.assertRaisesRegex(ValueError,'history'):
                report_store.restore(self.repo)


if __name__=='__main__':unittest.main()
