"""Policy proposals must preserve trust boundaries and historical validation."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from platform_fixtures import registered_root, report, POLICY, SLUG
from reporting.validation import encoded, decode, validate_package
import sync_policies as sync


def file_entry(raw, **updates):
    entry={'type':'file','encoding':'base64','size':len(raw),'content':base64.b64encode(raw).decode(),
           'sha':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}
    entry.update(updates)
    return entry


class PolicySyncTests(unittest.TestCase):
    def test_paths_git_identity_size_and_json_schema_are_strict(self):
        for path in ('../policy.json','/policy.json','config/../policy.json','config//policy.json',
                     'https://example.test/policy.json','a\\b.json','a%2fb.json','a b.json'):
            with self.assertRaises(ValueError):sync.source_path(path)
        raw=b'{"example":true}\n'
        class API:
            def get(self,path):return file_entry(raw)
        self.assertEqual(sync.remote_file(API(),'config/policy.json','a'*40)[0],raw)
        for updates in ({'type':'symlink'},{'sha':'f'*40},{'size':sync.MAX_SOURCE+1},{'size':1},{'encoding':'none'}):
            with patch.object(API,'get',return_value=file_entry(raw,**updates)):
                with self.assertRaises(ValueError):sync.remote_file(API(),'config/policy.json','a'*40)
        candidate=copy.deepcopy(POLICY);candidate['workflowBlobs'].append('f'*40)
        value=encoded(candidate)
        self.assertEqual(sync.proposed_policy(value,encoded(POLICY),'f'*40,'policy'),value)
        for change in ({'repository':'someone/else'},{'target':{**POLICY['target'],'id':'OTHER'}},
                       {'unknown':'property'},{'workflowBlobs':['c'*40]}):
            broken={**candidate,**change}
            with self.assertRaises(ValueError):sync.proposed_policy(encoded(broken),encoded(POLICY),'f'*40,'policy')
        with self.assertRaises(ValueError):sync.proposed_policy(b'{"schemaVersion":1,"schemaVersion":1}',encoded(POLICY),'f'*40,'policy')

    def test_template_mode_only_adds_inspected_blob_and_deduplicates(self):
        template={k:v for k,v in POLICY.items() if k!='workflowBlobs'}
        self.assertEqual(sync.proposed_policy(encoded(template),encoded(POLICY),'c'*40,'template'),encoded(POLICY))
        new=decode(sync.proposed_policy(encoded(template),encoded(POLICY),'f'*40,'template'))
        self.assertEqual(new['workflowBlobs'],['c'*40,'f'*40])
        with self.assertRaises(ValueError):sync.proposed_policy(encoded(POLICY),encoded(POLICY),'c'*40,'template')

    def test_upstream_source_is_pinned_and_active_migrations_are_not_touched(self):
        with tempfile.TemporaryDirectory() as temp:
            root=registered_root(Path(temp)/'site')
            workflow=b'name: Fixture\n'
            blob=file_entry(workflow)['sha']
            new={**POLICY,'workflowBlobs':['c'*40,blob]}
            calls=[]
            class API:
                def get(self,path):
                    calls.append(path)
                    if path.startswith('commits/'):return {'sha':'a'*40}
                    if path.startswith('contents/config/'):return file_entry(encoded(new))
                    return file_entry(workflow)
            info=sync.inspect_source(root,SLUG,{'policyPath':'config/policy.json','mode':'policy'},API())
            self.assertEqual(info['workflowBlob'],blob)
            self.assertTrue(all('?ref='+'a'*40 in path for path in calls if path.startswith('contents/')))
            registry=decode((root/'config/producers.json').read_bytes());registry[SLUG]['pending']={'format':'report-v1','policy':SLUG+'-producer.json'}
            (root/'config/producers.json').write_bytes(encoded(registry))
            with self.assertRaisesRegex(ValueError,'migration/freeze'):
                sync.inspect_source(root,SLUG,{'policyPath':'config/policy.json','mode':'policy'},API())

    def test_archive_validates_old_and_new_tools_without_changing_other_registrations(self):
        with tempfile.TemporaryDirectory() as temp:
            root=registered_root(Path(temp)/'site')
            before=decode((root/'config/producers.json').read_bytes())
            report(Path(temp)/'old',map_data=True)
            previous=Path(temp)/'old/package'
            validate_package(previous,root)
            new=copy.deepcopy(POLICY);new['workflowBlobs'].append('f'*40)
            new['tools']=[{'name':'test-toolchain','identity':'sha256:'+'e'*64}]
            old_raw=(root/'config'/before[SLUG]['policy']).read_bytes()
            sync.apply_policy(root,SLUG,encoded(new))
            after=decode((root/'config/producers.json').read_bytes())
            self.assertTrue(all(value==after[name] for name,value in before.items() if name!=SLUG))
            archived=after[SLUG]['archives'][0]['policy']
            self.assertEqual((root/'config'/archived).read_bytes(),old_raw)
            validate_package(previous,root)
            with patch.dict(POLICY,new,clear=True):
                report(Path(temp)/'new',map_data=True,metadata_updates={'workflowBlob':'f'*40})
                current=Path(temp)/'new/package'
            validate_package(current,root)
            # Reapplying cannot overwrite or duplicate the prior archive.
            initial=(root/'config'/archived).read_bytes()
            sync.apply_policy(root,SLUG,encoded(new))
            self.assertEqual((root/'config'/archived).read_bytes(),initial)
            self.assertEqual(len(decode((root/'config/producers.json').read_bytes())[SLUG]['archives']),1)

    def test_unchanged_disabled_and_existing_proposals_do_not_publish_or_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root=registered_root(Path(temp)/'site')
            old=(root/'config'/f'{SLUG}-producer.json').read_bytes()
            info={'raw':old,'old':old,'key':'f'*16}
            with patch.object(sync,'inspect_source',return_value=info),patch.object(sync,'prepare_candidate') as prepare:
                self.assertEqual(sync.sync_one(root,SLUG,{'mode':'policy'},Path(temp),True)['status'],'unchanged')
                prepare.assert_not_called()
            info['raw']=old+b'\n'
            with patch.object(sync,'inspect_source',return_value=info),patch.object(sync,'existing_proposal',return_value={'state':'CLOSED','url':'https://example.test/pr'}),patch.object(sync,'prepare_candidate') as prepare:
                self.assertEqual(sync.sync_one(root,SLUG,{'mode':'policy'},Path(temp),True)['status'],'existing-closed')
                prepare.assert_not_called()
            with patch.object(sync,'inspect_source') as inspect:
                self.assertEqual(sync.sync_one(root,SLUG,{'disabled':'Await a tracked policy'},Path(temp),True)['status'],'disabled')
                inspect.assert_not_called()

    def test_configuration_is_explicit_and_only_registered_sources_are_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=registered_root(Path(temp)/'site')
            path=root/'config/policy-sync.json'
            path.write_bytes(encoded({'schemaVersion':1,'projects':{SLUG:{'policyPath':'config/policy.json','mode':'policy'}}}))
            self.assertIn(SLUG,sync.sources(root))
            for values in ({'schemaVersion':2,'projects':{}}, {'schemaVersion':1,'projects':{'unregistered':{'disabled':'none'}}},
                           {'schemaVersion':1,'projects':{SLUG:{'policyPath':'../bad','mode':'policy'}}}):
                path.write_bytes(encoded(values))
                with self.assertRaises(ValueError):sync.sources(root)


if __name__=='__main__':unittest.main()
