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
from reporting.validation import ROOT, decode, digest, encoded


def compact_legacy_package():
    """Exercise the real compatibility validator without copying game-sized maps.

    Only the retained manifest/receipt metadata is borrowed. Measurements and
    history are isolated test data; real packages are covered in test_reporting.
    """
    from test_reporting import tiny_reports
    from reporting.legacy_nfl import summary
    entry=copy.deepcopy(decode((ROOT/'data/reports.lock.json').read_bytes())['projects']['nflstreet2'])
    directory=ROOT/entry['path']
    manifest=decode((directory/'manifest.json').read_bytes())
    progress,activity=tiny_reports()
    for document in (progress,activity):
        document.update(revision=manifest['revision'],target=manifest['target']['id'],
                        target_sha1=manifest['target']['sha1'])
    progress['built_at']=manifest['publishedAt']
    activity['snapshots'][0].update(revision=manifest['revision'],built_at=manifest['publishedAt'])
    manifest['summary']=summary(progress)
    payloads={'progress.json':encoded(progress),'activity.json':encoded(activity),
              'summary.json':encoded(manifest['summary']),'receipt.json':(directory/'receipt.json').read_bytes()}
    for module in manifest['modules'].values():
        asset=module['asset'];asset['sha256']=digest(payloads[asset['path']])
    payloads['manifest.json']=encoded(manifest)
    entry['manifestSha256']=digest(payloads['manifest.json'])
    return entry,payloads


class ReportStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.remote=self.base/'remote.git'
        subprocess.run(['git','init','--bare','--initial-branch=main',str(self.remote)],check=True,capture_output=True)
        self.repo=self.base/'site';self.repo.mkdir()
        shutil.copytree(ROOT/'config',self.repo/'config')
        from platform_fixtures import clear_import_freezes
        clear_import_freezes(self.repo)
        self.git('init','--initial-branch=main')
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','Site source')
        self.git('remote','add','origin',str(self.remote))
        self.git('push','origin','main')
        self.sha=self.git('rev-parse','HEAD').decode().strip()
        self.env=patch.dict(os.environ,{'GITHUB_REPOSITORY':'mitsevox/mitsevox.github.io',
            'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'push','GITHUB_SHA':self.sha})
        self.env.start();self.addCleanup(self.env.stop)
        self.site=self.base/'built';self.site.mkdir()
        entry,payloads=compact_legacy_package()
        self.lock={'schemaVersion':1,'projects':{'nflstreet2':entry}}
        directory=self.site/entry['path'];directory.mkdir(parents=True)
        for name,raw in payloads.items():(directory/name).write_bytes(raw)
        (self.site/report_store.LOCK).write_bytes(encoded(self.lock))

    def git(self,*args):return subprocess.check_output(['git',*args],cwd=self.repo,stderr=subprocess.DEVNULL)

    def test_bootstrap_rerun_restore_and_data_only_contents(self):
        first=report_store.publish(self.repo,self.site)
        self.assertEqual(first,report_store.publish(self.repo,self.site))
        names=self.git('ls-tree','-r','--name-only',first).decode().splitlines()
        expected={report_store.LOCK}
        for entry in self.lock['projects'].values():
            expected.update(p.relative_to(self.site).as_posix() for p in (self.site/entry['path']).iterdir())
        self.assertEqual(set(names),expected)
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
        # This mocked history boundary targets the compatibility timeline only.
        self.lock['projects']={'nflstreet2':self.lock['projects']['nflstreet2']}
        (self.site/report_store.LOCK).write_bytes(encoded(self.lock))
        report_store.publish(self.repo,self.site)
        report_store.restore(self.repo)
        entry, stored, activity, payloads=report_store.stored_package(self.repo,report_store.remote_head(self.repo),'nflstreet2')
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


class MultiProjectStoreTests(unittest.TestCase):
    setUp=ReportStoreTests.setUp
    git=ReportStoreTests.git
    # Exercise both formats through the real bare-remote writer and validators,
    # using small compatibility and standard reports in every failure scenario.
    def add_contract(self):
        from platform_fixtures import registered_root,report,SLUG
        from reporting.state import install
        registered_root(self.repo);registered_root(self.site)
        manifest,payloads=report(self.base/'contract',timeline=True)
        install(self.site,None,manifest,payloads,{'title':'Contract fixture'})
        return SLUG

    def test_all_projects_restore_and_rerun_without_erasing_any(self):
        slug=self.add_contract()
        first=report_store.publish(self.repo,self.site)
        report_store.restore(self.repo)
        selected=decode((self.repo/report_store.LOCK).read_bytes())
        self.assertEqual(set(selected['projects']),set(self.lock['projects'])|{slug})
        self.assertEqual(selected,decode((self.site/report_store.LOCK).read_bytes()))
        self.assertEqual(report_store.publish(self.repo,self.site),first)
        for key in selected['projects']:report_store.stored_package(self.repo,first,key)

    def test_old_candidate_cannot_remove_a_stored_project(self):
        self.add_contract();first=report_store.publish(self.repo,self.site)
        (self.site/report_store.LOCK).write_bytes(encoded(self.lock))
        with self.assertRaisesRegex(ValueError,'erase a stored project'):
            report_store.publish(self.repo,self.site)
        self.assertEqual(report_store.remote_head(self.repo),first)

    def test_old_registration_cannot_overwrite_or_restore_unknown_project(self):
        self.add_contract();first=report_store.publish(self.repo,self.site)
        registry=decode((self.repo/'config/producers.json').read_bytes())
        registry.pop('contract-test')
        (self.repo/'config/producers.json').write_bytes(encoded(registry))
        with self.assertRaisesRegex(ValueError,'Unregistered project'):
            report_store.restore(self.repo)
        self.assertEqual(report_store.remote_head(self.repo),first)


    def test_concurrent_writer_is_never_force_overwritten(self):
        self.add_contract();first=report_store.publish(self.repo,self.site)
        changed=decode((self.site/report_store.LOCK).read_bytes())
        changed['projects']['contract-test']['latestCommit']['title']='New metadata'
        (self.site/report_store.LOCK).write_bytes(encoded(changed))
        original=report_store.git;competing=[]
        def race(root,*args,**kwargs):
            if args[:2]==('push','origin') and not competing:
                tree=original(root,'rev-parse',first+'^{tree}').decode().strip()
                other=original(root,'-c','user.name=Other','-c','user.email=other@example.invalid',
                               'commit-tree',tree,'-p',first,data=b'Concurrent accepted publication\n').decode().strip()
                original(root,'push','origin',other+':refs/heads/report-data')
                competing.append(other)
            return original(root,*args,**kwargs)
        with patch.object(report_store,'git',side_effect=race),self.assertRaises(subprocess.CalledProcessError):
            report_store.publish(self.repo,self.site)
        self.assertEqual(report_store.remote_head(self.repo),competing[0])


if __name__=='__main__':unittest.main()
