"""A format-handoff freeze binds one exact snapshot and cannot advance its history."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from platform_fixtures import POLICY, SLUG, registered_root, report
from import_reports import refresh
from package_report import package
from reporting.github import GitHub
from reporting.state import frozen_snapshot, install, read_lock
from reporting.validation import decode, encoded


class ImportFreezeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=registered_root(self.base/'site')
        self.manifest,self.payloads=report(self.base/'original',timeline=True)
        self.path=install(self.root,None,self.manifest,self.payloads,{'title':'fixture'})
        self.freeze(SLUG)

    def freeze(self,slug):
        registry=decode((self.root/'config/producers.json').read_bytes())
        entry=read_lock(self.root)['projects'][slug]
        registry[slug]['freeze']={k:entry[k] for k in ('path','revision','manifestSha256')}
        (self.root/'config/producers.json').write_bytes(encoded(registry))

    def test_automatic_refresh_validates_checkpoint_without_reading_upstream(self):
        with patch.object(GitHub,'get',side_effect=AssertionError('upstream must not be read')):
            self.assertEqual(refresh(self.root,SLUG),self.path)
        self.assertEqual(frozen_snapshot(self.root,SLUG),self.path)
        with self.assertRaisesRegex(ValueError,'frozen'):refresh(self.root,SLUG,43)

    def test_install_rejects_a_new_revision_or_new_rows_even_with_the_same_revision(self):
        before=read_lock(self.root)
        newer,payloads=report(self.base/'new-revision',timeline=True,revision='b'*40)
        with self.assertRaisesRegex(ValueError,'frozen'):install(self.root,None,newer,payloads,{})
        source=self.base/'original/input'
        rows=decode((source/'timeline.json').read_bytes())
        added=copy.deepcopy(rows['snapshots'][0]);added['revision']='b'*40;rows['snapshots'].append(added)
        (source/'timeline.json').write_bytes(encoded(rows))
        metadata={**decode(self.payloads['receipt.json']),'project':SLUG,'tools':POLICY['tools'],'runId':43}
        changed,payloads=package(source,metadata,POLICY,self.base/'added-history')
        with self.assertRaisesRegex(ValueError,'frozen'):install(self.root,None,changed,payloads,{})
        self.assertEqual(read_lock(self.root),before)
        install(self.root,None,self.manifest,self.payloads,{'title':'same snapshot'})
        self.assertEqual(read_lock(self.root)['projects'][SLUG]['revision'],before['projects'][SLUG]['revision'])

    def test_changed_lock_or_manifest_fails_closed(self):
        lock=read_lock(self.root);lock['projects'][SLUG]['revision']='b'*40
        (self.root/'data/reports.lock.json').write_bytes(encoded(lock))
        with self.assertRaisesRegex(ValueError,'checkpoint'):refresh(self.root,SLUG)
        lock['projects'][SLUG]['revision']=self.manifest['revision']
        (self.root/'data/reports.lock.json').write_bytes(encoded(lock))
        (self.path/'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'manifest changed'):refresh(self.root,SLUG)

    def test_other_registered_producers_can_still_install(self):
        policy=copy.deepcopy(POLICY);policy['repository']='mitsevox/another-project'
        registry=decode((self.root/'config/producers.json').read_bytes())
        registry['another-project']={'format':'report-v1','policy':'another-producer.json'}
        (self.root/'config/another-producer.json').write_bytes(encoded(policy))
        (self.root/'config/producers.json').write_bytes(encoded(registry))
        metadata={**decode(self.payloads['receipt.json']),'project':'another-project',
                  'repository':policy['repository'],'tools':policy['tools']}
        manifest,payloads=package(self.base/'original/input',metadata,policy,self.base/'other-report')
        install(self.root,None,manifest,payloads,{'title':'other project'})
        self.assertEqual(frozen_snapshot(self.root,SLUG),self.path)
        self.assertIn('another-project',read_lock(self.root)['projects'])

    def test_direct_legacy_entry_point_obeys_the_same_freeze(self):
        from import_nfl import refresh as legacy_refresh
        from test_report_store import compact_legacy_package
        entry,payloads=compact_legacy_package();manifest=decode(payloads['manifest.json'])
        install(self.root,None,manifest,payloads,{'title':'legacy fixture'});self.freeze('nflstreet2')
        with patch.object(GitHub,'get',side_effect=AssertionError('upstream must not be read')):
            self.assertEqual(legacy_refresh(self.root),(self.root/entry['path']).resolve())
        with self.assertRaisesRegex(ValueError,'frozen'):legacy_refresh(self.root,43)


import test_report_store as store_tests

class FrozenStoreTests(unittest.TestCase):
    setUp=store_tests.ReportStoreTests.setUp
    git=store_tests.ReportStoreTests.git
    add_contract=store_tests.MultiProjectStoreTests.add_contract

    def test_frozen_store_round_trip_works_and_publication_cannot_bypass_freeze(self):
        import report_store
        from types import SimpleNamespace
        self.add_contract();first=report_store.publish(self.repo,self.site);report_store.restore(self.repo)
        entry=read_lock(self.repo)['projects'][SLUG]
        registry=decode((self.repo/'config/producers.json').read_bytes())
        registry[SLUG]['freeze']={k:entry[k] for k in ('path','revision','manifestSha256')}
        (self.repo/'config/producers.json').write_bytes(encoded(registry))
        report_store.restore(self.repo)
        self.assertEqual(report_store.publish(self.repo,self.site),first)
        _,payloads=report(self.base/'newer',timeline=True,revision='b'*40,metadata_updates={'runId':43})
        source=self.base/'newer/input';timeline=decode((source/'timeline.json').read_bytes())
        old=decode((self.site/entry['path']/'timeline.json').read_bytes())['snapshots']
        timeline['snapshots']=old+timeline['snapshots'];(source/'timeline.json').write_bytes(encoded(timeline))
        metadata={**decode(payloads['receipt.json']),'project':SLUG,'tools':POLICY['tools']}
        manifest,payloads=package(source,metadata,POLICY,self.base/'newer-package')
        install(self.site,SimpleNamespace(get=lambda path:{'status':'ahead'}),manifest,payloads,{})
        with self.assertRaisesRegex(ValueError,'frozen'):report_store.publish(self.repo,self.site)
        self.assertEqual(report_store.remote_head(self.repo),first)


if __name__=='__main__':unittest.main()
