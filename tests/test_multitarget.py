"""Target isolation and explicit, immutable report-v1 adoption."""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from platform_fixtures import POLICY, SLUG, REVISION, registered_root, report
from reporting.validation import decode, encoded, validate_package
from reporting.registry import producer
from reporting.targets import catalog, selected, normalize_lock, validate_selection, entries
from reporting.state import install, read_lock, check_update
from import_reports import authenticate, publication_run
from package_report import package

TARGET={'id':'GIHE78-rev0','platform':'gamecube','gameId':'GIHE78','region':'USA','discRevision':0,'sha1':'b'*40}


def setup(root):
    registered_root(root)
    policy={**copy.deepcopy(POLICY),'schemaVersion':2,'target':TARGET,'requiredJobs':['Plan affected targets','Tool tests']}
    registry=decode((root/'config/producers.json').read_bytes())
    registry[SLUG]={'format':'report-v2','catalog':SLUG+'-targets.json','targets':{
        TARGET['id']:{'format':'report-v2','policy':SLUG+'-v2.json','archives':[{'format':'report-v1','policy':SLUG+'-producer.json'}]}}}
    (root/'config/producers.json').write_bytes(encoded(registry))
    (root/'config'/ (SLUG+'-v2.json')).write_bytes(encoded(policy))
    document={'schemaVersion':1,'project':SLUG,'defaultTarget':TARGET['id'],'targets':[
        {'target':TARGET,'status':'active','support':{'build':True,'reportFormats':['report-v2']},'legacyTargets':[POLICY['target']]},
        {'target':{**TARGET,'id':'GIHE78-rev1','discRevision':1,'sha1':'f'*40},'status':'archived','support':{'build':False,'reportFormats':[]},'legacyTargets':[]}]}
    (root/'config'/ (SLUG+'-targets.json')).write_bytes(encoded(document))
    return policy,document


class MultiTargetTests(unittest.TestCase):
    def test_strict_identity_archived_metadata_and_explicit_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);policy,doc=setup(root)
            self.assertEqual(producer(root,SLUG)['target'],TARGET)
            self.assertEqual(catalog(root,SLUG,SLUG+'-targets.json'),doc)
            with self.assertRaises(ValueError):producer(root,SLUG,'GIHE78-rev1')
            for change in ({'discRevision':True},{'id':'../rev0'},{'gameId':'GIHE79'},{'sha1':'invalid'}):
                value=copy.deepcopy(doc);value['targets'][0]['target'].update(change)
                (root/'config'/ (SLUG+'-targets.json')).write_bytes(encoded(value))
                with self.subTest(change=change),self.assertRaises(ValueError):catalog(root,SLUG,SLUG+'-targets.json')

    def test_v1_adoption_preserves_package_bytes_history_and_pointer(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=registered_root(base/'site')
            report(base/'old',timeline=True);source=base/'old/package'
            manifest=decode((source/'manifest.json').read_bytes())
            class API:pass
            payloads={p.name:p.read_bytes() for p in source.iterdir()}
            install(root,API(),manifest,payloads,{'title':'old'})
            old=copy.deepcopy(read_lock(root)['projects'][SLUG]);setup(root)
            migrated=read_lock(root)
            self.assertEqual(migrated['schemaVersion'],2)
            self.assertEqual(selected(migrated,SLUG,TARGET['id']),old)
            self.assertEqual({p.name:p.read_bytes() for p in (root/old['path']).iterdir()},payloads)
            validate_package(root/old['path'],root)
            restored=install(root,API(),manifest,payloads,{'title':'old'})
            self.assertEqual(restored.relative_to(root.resolve()).as_posix(),old['path'])
            self.assertEqual(selected(read_lock(root),SLUG,TARGET['id']),old)
            new={**manifest,'target':TARGET}
            check_update(manifest,new,{'snapshots':[]},{'snapshots':[]},'identical',root)
            with self.assertRaises(ValueError):check_update(manifest,{**new,'target':{**TARGET,'sha1':'f'*40}},{},{},'identical',root)

    def test_packager_and_store_support_v2_without_changing_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'site';policy,_=setup(root)
            report(base/'old',timeline=True);original=base/'old/package'
            metadata={'project':SLUG,'repository':policy['repository'],'target':TARGET,'revision':REVISION,'tree':'e'*40,
                'methodology':'contract-report-v1','generation':1,'tools':policy['tools'],'measuredAt':'2026-10-25T10:00:00Z',
                'publishedAt':'2026-10-25T10:01:00Z','runId':42,'attempt':1,'workflowBlob':'c'*40}
            package(base/'old/input',metadata,policy,base/'new');result=base/'new'
            manifest,_,_=validate_package(result,root)
            self.assertEqual(manifest['schemaVersion'],2)
            self.assertEqual(manifest['summary'],decode((original/'manifest.json').read_bytes())['summary'])
            class API:pass
            payloads={p.name:p.read_bytes() for p in result.iterdir()}
            install(root,API(),manifest,payloads,{'title':'new'})
            entry=selected(read_lock(root),SLUG,TARGET['id'])
            self.assertIn('/targets/GIHE78-rev0/snapshots/',entry['path'])
            self.assertIsNone(selected(read_lock(root),SLUG,'GIHE78-rev1'))

    def test_failed_sibling_does_not_block_successful_target_but_shared_checks_do(self):
        policy={**POLICY,'schemaVersion':2,'requiredJobs':['Plan affected targets','Tool tests']}
        run={'repository':{'full_name':POLICY['repository']},'head_repository':{'full_name':POLICY['repository']},
             'path':POLICY['workflow'],'head_branch':'main','event':'push','status':'completed','conclusion':'failure',
             'head_sha':REVISION,'run_attempt':1}
        def job(name,conclusion='success'):
            return {'name':name,'head_sha':REVISION,'run_attempt':1,'conclusion':conclusion,
                    'steps':[{'name':'Validate measurements','conclusion':'success'}]}
        jobs=[job('Measure'),job('Plan affected targets'),job('Tool tests'),job('Other target','failure')]
        authenticate(policy,run,jobs,'c'*40)
        jobs[2]['conclusion']='failure'
        with self.assertRaises(ValueError):authenticate(policy,run,jobs,'c'*40)
        with self.assertRaises(ValueError):authenticate(POLICY,run,[job('Measure')],'c'*40)

    def test_discovery_skips_runs_that_did_not_build_this_target(self):
        policy={**POLICY,'schemaVersion':2}
        class API:
            def iter_pages(self,path,field):return iter(self.pages(path,field))
            def pages(self,path,field):
                if 'workflows/' in path:return [{'id':n,'event':'push','conclusion':result,'run_attempt':1} for n,result in [(4,'success'),(3,'failure'),(2,'failure')]]
                if 'artifacts' in path:return [] if '/4/' in path else [{'name':policy['artifact'],'expired':False}]
                return [{'name':policy['job'],'conclusion':'failure' if '/3/' in path else 'success'}]
        self.assertEqual(publication_run(API(),policy)['id'],2)

    def test_scoped_selection_rejects_valid_package_from_another_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);setup(root)
            entry={'revision':REVISION}
            manifest={'project':SLUG,'revision':REVISION,'target':POLICY['target']}
            validate_selection(root,SLUG,'GIHE78-rev0',entry,manifest)
            with self.assertRaises(ValueError):validate_selection(root,SLUG,'GIHE78-rev1',entry,manifest)
        with self.assertRaises(ValueError):list(entries({'schemaVersion':1,'projects':{SLUG:{'targets':{'GIHE78-rev0':{}}}}}))

    def test_lazy_discovery_stops_at_latest_match_even_with_thousands_of_runs(self):
        from reporting.github import GitHub
        policy={**POLICY,'schemaVersion':2}
        class API(GitHub):
            def get(self,path):
                if 'workflows/' in path:
                    self.assert_first_page(path)
                    return {'workflow_runs':[{'id':n,'event':'push','conclusion':'success','run_attempt':1} for n in range(2000,1900,-1)]}
                if 'artifacts' in path:return {'artifacts':[{'name':policy['artifact'],'expired':False}]}
                return {'jobs':[{'name':policy['job'],'conclusion':'success'}]}
            def assert_first_page(self,path):
                if not path.endswith('page=1'):raise AssertionError('Discovery eagerly fetched older pages')
        self.assertEqual(publication_run(API('owner/repo'),policy)['id'],2000)

    def test_two_active_targets_same_commit_store_and_policy_updates_are_isolated(self):
        import subprocess
        import report_store
        import sync_policies
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'site';policy,doc=setup(root)
            other=doc['targets'][1];other['status']='active';other['support']={'build':True,'reportFormats':['report-v2']}
            (root/'config'/ (SLUG+'-targets.json')).write_bytes(encoded(doc))
            second={**copy.deepcopy(policy),'target':other['target'],'artifact':'other-report','job':'Other measure'}
            (root/'config/second-policy.json').write_bytes(encoded(second))
            registration=decode((root/'config/producers.json').read_bytes())
            registration[SLUG]['targets'][other['target']['id']]={'format':'report-v2','policy':'second-policy.json'}
            (root/'config/producers.json').write_bytes(encoded(registration))
            class API:pass
            for i,current in enumerate((policy,second)):
                folder=base/str(i);report(folder,linked=20+i*10)
                metadata={'project':SLUG,'repository':current['repository'],'target':current['target'],'revision':REVISION,'tree':'e'*40,
                    'methodology':'contract-report-v1','generation':1,'tools':current['tools'],'measuredAt':'2026-10-25T10:00:00Z',
                    'publishedAt':'2026-10-25T10:01:00Z','runId':42+i,'attempt':1,'workflowBlob':'c'*40}
                output=folder/'v2';package(folder/'input',metadata,current,output)
                manifest=decode((output/'manifest.json').read_bytes())
                install(root,API(),manifest,{p.name:p.read_bytes() for p in output.iterdir()},
                        {'title':str(i),'date':'2026-10-2'+str(5+i)+'T10:00:00Z'})
            before=copy.deepcopy(read_lock(root))
            self.assertNotEqual(selected(before,SLUG,TARGET['id'])['path'],selected(before,SLUG,other['target']['id'])['path'])
            from build_site import project_bindings
            from reporting.validation import ROOT
            config={'schemaVersion':2,'slug':SLUG,'title':'Target fixture','repository':POLICY['repository'],
                'targetRegistry':SLUG+'-targets.json','console':'GameCube','artwork':{'cover':'/assets/covers/test.webp','width':1,'height':1},
                'modules':{key:False for key in ('map','functionCounts','fileCounts','timeline','contributors')},'contributions':{'accepting':False}}
            (root/'config/projects.json').write_bytes(encoded([config]))
            cover=root/'assets/covers/test.webp';cover.parent.mkdir(parents=True)
            shutil.copyfile(ROOT/'assets/covers/n100f.webp',cover)
            bindings=project_bindings(root,root/'bindings.js')[SLUG]
            self.assertEqual(bindings['report']['summary']['code']['linkedBytes'],20)
            self.assertEqual(bindings['targetReports'][other['target']['id']]['report']['summary']['code']['linkedBytes'],30)
            self.assertEqual(bindings['latestCommit']['title'],'1')
            # A docs-only repository commit needs no target build/new snapshot.
            from reporting.state import update_latest_commits
            metadata={'revision':'9'*40,'title':'Document setup','description':'','date':'2026-10-27T00:00:00Z','url':'https://github.com/'+POLICY['repository']+'/commit/'+'9'*40}
            update_latest_commits(root,{SLUG:metadata},before)
            after_metadata=read_lock(root)
            for target in (TARGET['id'],other['target']['id']):
                original=selected(before,SLUG,target);current=selected(after_metadata,SLUG,target)
                self.assertEqual({k:v for k,v in current.items() if k!='latestCommit'},{k:v for k,v in original.items() if k!='latestCommit'})
                self.assertEqual(current['latestCommit'],metadata)
            # A stale observation cannot overwrite metadata installed later.
            stale={**metadata,'title':'Older observation'}
            self.assertEqual(update_latest_commits(root,{SLUG:stale},before),set())
            self.assertEqual(read_lock(root),after_metadata)
            before=copy.deepcopy(after_metadata)

            # A policy update stages only its target, never newer sibling files.
            updated={**policy,'workflowBlobs':['c'*40,'d'*40]}
            paths=sync_policies.apply_policy(root,SLUG,encoded(updated),TARGET['id'])
            self.assertNotIn('data/'+SLUG,paths)
            self.assertIn('data/'+SLUG+'/targets/'+TARGET['id'],paths)
            self.assertEqual(read_lock(root),before)
            self.assertEqual(producer(root,SLUG,other['target']['id'])['workflowBlobs'],['c'*40])
            # Append/restore through the real Git report store, with no GitHub mutations.
            report_store.git(root,'init','-q')
            bare=base/'remote.git';subprocess.check_call(['git','init','--bare','-q',str(bare)])
            report_store.git(root,'remote','add','origin',str(bare))
            with patch.object(report_store,'require_current_main',return_value='a'*40):head=report_store.publish(root,root)
            stored=report_store.stored_lock(root,head)
            self.assertEqual(stored,before)
            for target in (TARGET['id'],other['target']['id']):
                entry,manifest,_,_=report_store.stored_package(root,head,SLUG,target)
                self.assertEqual(manifest['target']['id'],target)
                self.assertEqual(entry,selected(before,SLUG,target))

    def test_metadata_refresh_rejects_symlinked_store_before_opening_guard(self):
        from reporting.state import update_latest_commits
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'site';root.mkdir();outside=base/'outside';outside.mkdir()
            (root/'data').symlink_to(outside,target_is_directory=True)
            with self.assertRaises(ValueError):update_latest_commits(root,{}, {'projects':{}})
            self.assertFalse((outside/'.report-refresh.lock').exists())


if __name__=='__main__':unittest.main()
