"""Shared platform acceptance using a separately registered contract producer."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from platform_fixtures import POLICY,ROOT,SLUG,REVISION,registered_root,report,presentation
from reporting.validation import decode,encoded,digest,validate_package
from reporting.registry import producer
from reporting.state import install,read_lock,check_update
from build_site import build,project_bindings
from import_reports import authenticate,refresh,refresh_all


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=registered_root(self.base/'site',include_real=True)

    def install(self,**options):
        manifest,payloads=report(self.base/'producer',**options)
        destination=install(self.root,None,manifest,payloads,{'revision':REVISION,'title':'Contract fixture',
                    'description':'Isolated test data','date':'2026-10-25T10:00:00Z','url':'https://github.com/mitsevox/contract-test/commit/'+REVISION})
        return manifest,payloads,destination

    def test_second_project_summary_only_has_no_invented_optional_data(self):
        old=read_lock(self.root)['projects']['nflstreet2']
        manifest,_,directory=self.install(fuzzy=False)
        checked,p,a=validate_package(directory,self.root)
        self.assertEqual(manifest,checked)
        self.assertNotIn('files',p);self.assertNotIn('contributors',a);self.assertNotIn('snapshots',a)
        self.assertNotIn('fuzzy',p['measures']['code'])
        self.assertEqual(read_lock(self.root)['projects']['nflstreet2'],old)
        self.assertEqual(set(read_lock(self.root)['projects']),{'nflstreet2',SLUG})

    def test_timeline_without_credit_feed_and_rankings_without_timeline(self):
        _,_,directory=self.install(timeline=True)
        _,_,a=validate_package(directory,self.root)
        self.assertIn('snapshots',a);self.assertNotIn('contributors',a)
        manifest,payloads=report(self.base/'credits',contributors=True)
        with tempfile.TemporaryDirectory() as temp:
            for name,raw in payloads.items():(Path(temp)/name).write_bytes(raw)
            _,_,a=validate_package(temp,self.root)
        self.assertIn('contributors',a);self.assertNotIn('snapshots',a)

    def test_nested_map_extents_and_joint_credit_reconciliation(self):
        _,_,directory=self.install(map_data=True,contributors=True,joint=True)
        validate_package(directory,self.root)
        source=self.base/'producer/input'
        raw=decode((source/'map.json').read_bytes());raw['files'][1]['address']='0x80000020';raw['files'][1]['function_address']='0x80000020'
        (source/'map.json').write_bytes(encoded(raw))
        manifest=decode((directory/'manifest.json').read_bytes())
        receipt=decode((directory/'receipt.json').read_bytes())
        metadata={k:manifest[k] for k in ('project','repository','target','revision','tree','methodology','generation','tools','measuredAt','publishedAt')}
        metadata.update({k:receipt[k] for k in ('runId','attempt','workflowBlob')})
        from package_report import package
        with self.assertRaisesRegex(ValueError,'Overlapping'):
            package(source,metadata,POLICY,self.base/'invalid-package')

    def test_registered_owner_policy_and_checksum_cannot_be_bypassed(self):
        _,_,directory=self.install()
        data=decode((directory/'summary.json').read_bytes());data['code']['matchedBytes']=999
        (directory/'summary.json').write_bytes(encoded(data))
        with self.assertRaises(ValueError):validate_package(directory,self.root)
        policy=copy.deepcopy(POLICY);policy['repository']='someone/contract-test'
        (self.root/'config/contract-test-producer.json').write_bytes(encoded(policy))
        with self.assertRaisesRegex(ValueError,'site owner'):producer(self.root,SLUG)
        with self.assertRaisesRegex(ValueError,'Unregistered'):producer(self.root,'another-game')

    def test_linked_coverage_is_not_forced_equal_to_exact_or_fuzzy(self):
        _,_,directory=self.install(linked=80)
        _,p,_=validate_package(directory,self.root)
        self.assertEqual(p['measures']['code'],{'total':100,'linked':80,'matched':50,'fuzzy':70})

    def test_new_project_generates_route_and_shared_bindings_without_game_code(self):
        self.install(timeline=True);presentation(self.root,timeline=True)
        for folder in ('assets','wiki','docs'):shutil.copytree(ROOT/folder,self.root/folder)
        for filename in ('index.html','404.html'):shutil.copyfile(ROOT/filename,self.root/filename)
        output=self.base/'public';build(self.root,output)
        self.assertTrue((output/'games'/SLUG/'index.html').exists())
        manifest=decode((output/'site-manifest.json').read_bytes())
        self.assertEqual(set(manifest['projects']),{'nflstreet2',SLUG})
        release=manifest['release'];text=(output/'releases'/release/'assets/report-projects.js').read_text()
        self.assertIn('Contract test project',text);self.assertIn('"contributors":false',text)
        self.assertFalse((output/'fixtures').exists())

    def test_one_failed_refresh_does_not_skip_other_registered_sources(self):
        with patch('import_reports.registrations',return_value={'first':{},'second':{}}), \
             patch('import_reports.refresh',side_effect=[ValueError('bad report'),None]) as call:
            self.assertEqual(refresh_all(self.root),['first'])
            self.assertEqual([args.args[1] for args in call.call_args_list],['first','second'])

    def test_wrong_execution_and_missing_validation_are_rejected(self):
        run={'repository':{'full_name':POLICY['repository']},'head_repository':{'full_name':POLICY['repository']},
             'path':POLICY['workflow'],'head_branch':'main','event':'push','status':'completed','conclusion':'success',
             'head_sha':REVISION,'run_attempt':1}
        job={'name':'Measure','conclusion':'success','head_sha':REVISION,'run_attempt':1,
             'steps':[{'name':'Validate measurements','conclusion':'success'}]}
        self.assertEqual(authenticate(POLICY,run,[job],'c'*40),job)
        for change in ({'event':'pull_request'},{'head_branch':'other'},{'conclusion':'failure'},{'head_repository':{'full_name':'someone/fork'}}):
            with self.assertRaises(ValueError):authenticate(POLICY,{**run,**change},[job],'c'*40)
        with self.assertRaises(ValueError):authenticate(POLICY,run,[{**job,'steps':[]}],'c'*40)
        with self.assertRaises(ValueError):authenticate(POLICY,run,[job],'f'*40)


    def test_approved_historical_policy_survives_producer_format_cutover(self):
        registry=decode((self.root/'config/producers.json').read_bytes())
        old=copy.deepcopy(registry['nflstreet2'])
        next_policy=copy.deepcopy(POLICY)
        current_policy=decode((self.root/'config/nflstreet2-producer.json').read_bytes())
        next_policy.update(repository=current_policy['repository'],target=current_policy['target'])
        (self.root/'config/next-producer.json').write_bytes(encoded(next_policy))
        registry['nflstreet2']={'format':'report-v1','policy':'next-producer.json','archives':[old]}
        (self.root/'config/producers.json').write_bytes(encoded(registry))
        entry=read_lock(self.root)['projects']['nflstreet2']
        checked,_,_=validate_package(self.root/entry['path'],self.root)
        self.assertEqual(checked['project'],'nflstreet2')
        self.assertEqual(producer(self.root,'nflstreet2')['format'],'report-v1')
        registry['nflstreet2']['archives']=[]
        (self.root/'config/producers.json').write_bytes(encoded(registry))
        with self.assertRaisesRegex(ValueError,'registered producer policy'):
            validate_package(self.root/entry['path'],self.root)

    def test_history_conversion_retains_exact_original_record(self):
        old={'revision':'a'*40,'summary':{}}
        new={'revision':'d'*40,'summary':{}}
        row={'revision':'a'*40,'built_at':'2026-10-25T10:00:00Z','code':{'total':100,'linked':1},
             'data':{'total':10,'linked':0},'provenance':{'kind':'older-format','receipt':'source'}}
        retained={**row,'provenance':{'kind':'inherited','source':'prior accepted report','record':copy.deepcopy(row)}}
        check_update(old,new,{'snapshots':[row]},{'snapshots':[retained]},'ahead')
        retained['provenance']['record']['code']['linked']=2
        with self.assertRaisesRegex(ValueError,'history'):
            check_update(old,new,{'snapshots':[row]},{'snapshots':[retained]},'ahead')


    def test_install_does_not_follow_a_symlinked_data_store(self):
        root=registered_root(self.base/'unsafe-site')
        external=self.base/'private-data';external.mkdir()
        (root/'data').symlink_to(external,target_is_directory=True)
        manifest,payloads=report(self.base/'producer')
        with self.assertRaisesRegex(ValueError,'Unsafe report data'):
            install(root,None,manifest,payloads,{})
        self.assertEqual(list(external.iterdir()),[])


if __name__=='__main__':unittest.main()

class ImportExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=registered_root(self.base/'site',include_real=True)

    def archive(self,payloads):
        import io,zipfile
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w') as z:
            for name,raw in payloads.items():z.writestr(name,raw)
        return output.getvalue()

    def execution(self,revision=REVISION,run_id=42,mode='full'):
        start='2026-10-25T10:00:00Z' if run_id==42 else '2026-10-25T09:00:00Z'
        end='2026-10-25T10:02:00Z' if run_id==42 else '2026-10-25T09:02:00Z'
        run={'id':run_id,'repository':{'full_name':POLICY['repository']},'head_repository':{'full_name':POLICY['repository']},
             'path':POLICY['workflow'],'head_branch':'main' if run_id==42 else 'codex/candidate',
             'event':'push' if run_id==42 else 'pull_request','status':'completed','conclusion':'success',
             'head_sha':revision,'run_attempt':1,'run_started_at':start}
        steps=['Validate measurements',*POLICY['lanes'][mode]]
        job={'name':'Measure','conclusion':'success','head_sha':revision,'run_attempt':1,'completed_at':end,
             'steps':[{'name':s,'conclusion':'success'} for s in steps]}
        return run,job

    def artifact(self,raw,revision=REVISION,run_id=42,artifact_id=123):
        return {'id':artifact_id,'name':'public-report','digest':'sha256:'+digest(raw),'size_in_bytes':len(raw),
                'expired':False,'created_at':'2026-10-25T10:01:00Z' if run_id==42 else '2026-10-25T09:01:00Z',
                'workflow_run':{'id':run_id,'head_sha':revision}}

    def mocked_api(self,run,job,artifact,archive,source=None):
        from contextlib import ExitStack
        source=source or {}
        def get(api,path):
            if path=='actions/runs/42':return run
            if path.startswith('contents/'):return {'sha':'c'*40}
            if path.startswith('compare/'):return {'status':'identical'}
            if path.startswith('git/commits/'):return {'tree':{'sha':'e'*40}}
            if path=='commits/main':return {'sha':REVISION,'commit':{'message':'Contract fixture','committer':{'date':'2026-10-25T10:01:00Z'}}}
            if path in source:return source[path]
            raise AssertionError(path)
        def pages(api,path,field):
            if path=='actions/runs/42/attempts/1/jobs':return [job]
            if path=='actions/runs/42/artifacts':return [artifact]
            if path in source:return source[path]
            raise AssertionError(path)
        def raw(api,path):
            if path=='actions/artifacts/123/zip':return archive
            if path in source:return source[path]
            raise AssertionError(path)
        stack=ExitStack()
        stack.enter_context(patch('reporting.github.GitHub.get',get))
        stack.enter_context(patch('reporting.github.GitHub.pages',pages))
        stack.enter_context(patch('reporting.github.GitHub.raw',raw))
        return stack

    def test_full_standard_import_and_expired_artifact_cache_preserve_nfl(self):
        _,payloads=report(self.base/'producer',timeline=True)
        archive=self.archive(payloads);run,job=self.execution();artifact=self.artifact(archive)
        before=read_lock(self.root)['projects']['nflstreet2']
        with self.mocked_api(run,job,artifact,archive):refresh(self.root,SLUG,42)
        entry=read_lock(self.root)['projects'][SLUG]
        self.assertEqual(read_lock(self.root)['projects']['nflstreet2'],before)
        expired={**artifact,'expired':True}
        with self.mocked_api(run,job,expired,archive),patch('import_reports.accepted_package',return_value=True):
            refresh(self.root,SLUG,42)
        self.assertEqual(entry,read_lock(self.root)['projects'][SLUG])
        with self.mocked_api(run,job,expired,archive),patch('import_reports.accepted_package',return_value=False),self.assertRaisesRegex(ValueError,'artifact'):
            refresh(self.root,SLUG,42)

    def test_archived_tools_remain_readable_but_cannot_admit_new_reports(self):
        manifest,payloads=report(self.base/'producer')
        install(self.root,None,manifest,payloads,{'title':'Prior verified package'})
        registry=decode((self.root/'config/producers.json').read_bytes())
        old=copy.deepcopy(registry[SLUG]);changed=copy.deepcopy(POLICY)
        changed['tools']=[{'name':'new-toolchain','identity':'sha256:'+'f'*64}]
        (self.root/'config/next-tools.json').write_bytes(encoded(changed))
        registry[SLUG]={'format':'report-v1','policy':'next-tools.json','archives':[old]}
        (self.root/'config/producers.json').write_bytes(encoded(registry))
        entry=read_lock(self.root)['projects'][SLUG]
        validate_package(self.root/entry['path'],self.root)
        archive=self.archive(payloads);run,job=self.execution()
        before=read_lock(self.root)
        with self.mocked_api(run,job,self.artifact(archive),archive), \
             patch('import_reports.accepted_package',return_value=False),self.assertRaisesRegex(ValueError,'active producer'):
            refresh(self.root,SLUG,42)
        self.assertEqual(read_lock(self.root),before)

    def test_generic_reuse_checks_original_full_artifact_and_tree(self):
        original_revision='f'*40
        _,original_payloads=report(self.base/'original',revision=original_revision,metadata_updates={
            'runId':41,'measuredAt':'2026-10-25T09:00:00Z','publishedAt':'2026-10-25T09:01:00Z'})
        original_archive=self.archive(original_payloads)
        source_run,source_job=self.execution(original_revision,41)
        source_artifact=self.artifact(original_archive,original_revision,41,99)
        proof={'runId':41,'attempt':1,'artifactId':99,'artifactSha256':digest(original_archive),
               'revision':original_revision,'tree':'e'*40,'measuredAt':'2026-10-25T09:00:00Z'}
        _,payloads=report(self.base/'reused',metadata_updates={
            'mode':'reused','source':proof,'measuredAt':'2026-10-25T09:00:00Z'})
        archive=self.archive(payloads);run,job=self.execution(mode='reused');artifact=self.artifact(archive)
        source={'actions/runs/41/attempts/1':source_run,'actions/runs/41/attempts/1/jobs':[source_job],
                'actions/artifacts/99':source_artifact,'actions/artifacts/99/zip':original_archive}
        with self.mocked_api(run,job,artifact,archive,source):refresh(self.root,SLUG,42)
        before=read_lock(self.root)
        # A self-consistent new receipt cannot replace original measurements.
        changed=decode((self.base/'reused/input/summary.json').read_bytes())
        changed['code']['matchedBytes']=51
        (self.base/'reused/input/summary.json').write_bytes(encoded(changed))
        current=decode(payloads['manifest.json']);receipt=decode(payloads['receipt.json'])
        metadata={k:current[k] for k in ('project','repository','target','revision','tree','methodology','generation','tools','measuredAt','publishedAt')}
        metadata.update({k:receipt[k] for k in ('runId','attempt','workflowBlob','mode','source')})
        from package_report import package
        _,changed_payloads=package(self.base/'reused/input',metadata,POLICY,self.base/'changed-report')
        changed_archive=self.archive(changed_payloads)
        with self.mocked_api(run,job,self.artifact(changed_archive),changed_archive,source), \
             patch('import_reports.accepted_package',return_value=False),self.assertRaisesRegex(ValueError,'original'):
            refresh(self.root,SLUG,42)
        self.assertEqual(read_lock(self.root),before)
        source['actions/runs/41/attempts/1']={**source_run,'conclusion':'failure'}
        with self.mocked_api(run,job,artifact,archive,source),patch('import_reports.accepted_package',return_value=False),self.assertRaises(ValueError):
            refresh(self.root,SLUG,42)
        self.assertEqual(read_lock(self.root),before)
