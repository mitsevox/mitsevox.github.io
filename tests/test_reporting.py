"""Consumer regression tests: no original game files or compiler required."""
import copy
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from reporting.validation import ROOT, decode, encoded, validate_activity, validate_package, validate_progress
from reporting.github import FULL_STEPS, REUSE_STEP, authenticate_run, pages_reports, select_artifact, zip_members
from import_nfl import accepted_package, check_decomp, check_update, install
from build_site import build, locked_projects


def zipped(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as z:
        for name, raw in files.items():
            z.writestr(name, raw)
    return output.getvalue()


def tiny_reports():
    revision = 'a'*40
    def leaf(name, address, size, matched, fuzzy, kind='code', function=True):
        item = dict(name=name, address=f'0x{address:08X}', size=size, linked=0,
                    matched=matched, fuzzy=fuzzy, kind=kind)
        if function:
            item.update(type='function', function_address=item['address'], original_size=size)
        return item
    leaves = [leaf('exact unlinked', 0x80000000, 60, 60, 60),
              leaf('partial', 0x8000003C, 40, 0, 20)]
    code = dict(name='code', address='0x80000000', kind='code', size=100, linked=0,
                matched=60, fuzzy=80, children=leaves)
    data = leaf('data',0x80000100,10,0,2,kind='data',function=False)
    p = dict(schema=1, baseline='verified', basis='executable-sections', revision=revision,
             target='TEST', target_sha1='b'*40, built_at='2026-10-25T10:00:00Z',
             source={'report':'measured','units':0},
             measures={'code':dict(total=100,linked=0,matched=60,fuzzy=80),
                       'data':dict(total=10,linked=0,matched=0,fuzzy=2)},
             functions=dict(total=2,exact=1,named=1,basis='provisional-analysis'),
             file_counts=dict(total=1,exact=0,named=1,basis='mapped-file-inventory'),
             sections=[code,data],files=copy.deepcopy([code,data]))
    a = dict(schema=1, target='TEST', target_sha1='b'*40, revision=revision,
             contribution_basis='exact-functions', credited_functions=1,
             contributors=[dict(login='one',id=1,functions=1,pull_requests=[1]),
                           dict(login='two',id=2,functions=1,pull_requests=[1])],
             snapshots=[dict(revision=revision,built_at=p['built_at'],
                  code=dict(total=100,linked=0),data=dict(total=10,linked=0),
                  provenance=dict(kind='verified-source-build',report_sha256='c'*64))])
    return p,a


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.p,self.a = tiny_reports()

    def validate(self):
        return validate_progress(self.p, {'id':'TEST','sha1':'b'*40}, 'a'*40)

    def test_partial_exact_unlinked_and_joint_credit_survive(self):
        self.assertEqual(len(self.validate()),1)
        validate_activity(self.a,self.p)  # 2 personal credits, 1 unique function.

    def test_fuzzy_cannot_drop_below_exact_or_exceed_total(self):
        for value in (59,101,float('nan'),True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.p['measures']['code']['fuzzy']=value
                self.validate()

    def test_changed_denominator_fails_map_aggregation(self):
        self.p['measures']['code']['total']=101
        with self.assertRaisesRegex(ValueError,'aggregate'):self.validate()

    def test_overlapping_ranges_and_truncated_function_fail(self):
        self.p['files'][0]['children'][1]['address']='0x80000030'
        with self.assertRaises(ValueError):self.validate()
        self.p,self.a=tiny_reports()
        self.p['files'][0]['children'][1]['original_size']=41
        with self.assertRaisesRegex(ValueError,'extent'):self.validate()

    def test_empty_children_cannot_pass_import_then_fail_the_renderer(self):
        self.p['files'][0]['children'][0]['children']=[]
        with self.assertRaises(ValueError):self.validate()

    def test_partial_is_not_exact_function(self):
        self.p['functions']['exact']=2
        with self.assertRaisesRegex(ValueError,'Exact function count'):self.validate()

    def test_fixtures_unknown_fields_wrong_revision_rejected(self):
        self.p['baseline']='preview'
        with self.assertRaises(ValueError):self.validate()
        self.p,self.a=tiny_reports();self.p['raw_binary']='no'
        with self.assertRaises(ValueError):self.validate()
        self.p,self.a=tiny_reports();self.p['revision']='c'*40
        with self.assertRaises(ValueError):self.validate()

    def test_history_duplicates_count_gap_and_unknown_provenance_rejected(self):
        self.a['snapshots']*=2
        with self.assertRaisesRegex(ValueError,'Duplicate'):validate_activity(self.a,self.p)
        _,self.a=tiny_reports();self.a['credited_functions']=0
        with self.assertRaisesRegex(ValueError,'credited'):validate_activity(self.a,self.p)
        _,self.a=tiny_reports();self.a['snapshots'][0]['provenance']['kind']='guessed'
        with self.assertRaises(ValueError):validate_activity(self.a,self.p)

    def test_history_regression_or_rewrite_rejected(self):
        old={'revision':'a'*40,'summary':{}}
        new={'revision':'d'*40,'summary':{}}
        for relation in ('behind','diverged','identical'):
            with self.assertRaises(ValueError):check_update(old,new,self.a,self.a,relation)
        changed=copy.deepcopy(self.a);changed['snapshots'][0]['code']['linked']=1
        with self.assertRaises(ValueError):check_update(old,new,self.a,changed,'ahead')
        check_update(old,new,self.a,self.a,'ahead')

    def test_decomp_parity_rejects_fraction_boolean_and_fuzzy_mismatch(self):
        m=dict(total_code='100',matched_code='60',complete_code='0',total_data='10',
               matched_data='0',complete_data='0',fuzzy_match_percent=80)
        check_decomp(zipped({'report.json':encoded({'measures':m})}),self.p)
        for field,value in [('matched_code',60.5),('complete_code',False),('fuzzy_match_percent',79)]:
            bad={**m,field:value}
            with self.assertRaises(ValueError):check_decomp(zipped({'report.json':encoded({'measures':bad})}),self.p)


class ArchiveTests(unittest.TestCase):
    def test_duplicate_json_nonfinite_and_unsafe_zip_rejected(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}'):
            with self.assertRaises(ValueError):decode(raw)
        for name in ('../progress.json','dir/progress.json','dir\\progress.json'):
            with self.assertRaises(ValueError):zip_members(zipped({name:b'{}'}))

    def test_pages_parser_never_extracts_or_accepts_links(self):
        tar_data=io.BytesIO()
        with tarfile.open(fileobj=tar_data,mode='w') as archive:
            for name in ('progress.json','activity.json'):
                member=tarfile.TarInfo('./'+name);member.size=2
                archive.addfile(member,io.BytesIO(b'{}'))
        result=pages_reports(zipped({'artifact.tar':tar_data.getvalue()}))
        self.assertEqual(set(result),{'progress.json','activity.json'})
        tar_data=io.BytesIO()
        with tarfile.open(fileobj=tar_data,mode='w') as archive:
            member=tarfile.TarInfo('progress.json');member.type=tarfile.SYMTYPE;member.linkname='/etc/passwd'
            archive.addfile(member)
        with self.assertRaises(ValueError):pages_reports(zipped({'artifact.tar':tar_data.getvalue()}))


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lock=decode((ROOT/'data/reports.lock.json').read_bytes())
        cls.directory=ROOT/lock['projects']['nflstreet2']['path']
        cls.receipt=decode((cls.directory/'receipt.json').read_bytes())
        cls.policy=decode((ROOT/'config/nflstreet2-producer.json').read_bytes())

    def setUp(self):
        self.run=copy.deepcopy(self.receipt['run'])
        for key in ('repository','head_repository'):self.run[key]={'full_name':self.policy['repository']}
        self.jobs=[copy.deepcopy(self.receipt['job'])]

    def auth(self):return authenticate_run(self.policy,self.run,self.jobs,self.receipt['workflowBlob'])

    def test_real_reuse_receipt_and_simulated_full_lane(self):
        self.assertEqual(self.auth()[0],'reused')
        self.jobs[0]['steps']=[s for s in self.jobs[0]['steps'] if s['name'] not in FULL_STEPS and s['name']!=REUSE_STEP]
        self.jobs[0]['steps'] += [{'name':n,'conclusion':'success'} for n in FULL_STEPS]
        self.assertEqual(self.auth()[0],'full')
        self.jobs[0]['steps'].append({'name':REUSE_STEP,'conclusion':'success'})
        with self.assertRaises(ValueError):self.auth()

    def test_failed_fork_pr_wrong_attempt_and_changed_workflow_rejected(self):
        for key,value in [('conclusion','failure'),('event','pull_request'),('head_branch','codex/test')]:
            original=self.run[key];self.run[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.auth()
            self.run[key]=original
        self.run['head_repository']['full_name']='someone/fork'
        with self.assertRaises(ValueError):self.auth()
        self.setUp();self.jobs[0]['run_attempt']+=1
        with self.assertRaises(ValueError):self.auth()
        self.setUp()
        with self.assertRaises(ValueError):authenticate_run(self.policy,self.run,self.jobs,'f'*40)

    def test_explicit_main_audit_may_skip_selection_only_with_full_validation(self):
        selection = 'Select verified final-integration reports'
        self.jobs[0]['steps'] = [s for s in self.jobs[0]['steps']
                                if s['name'] not in FULL_STEPS and s['name'] not in (REUSE_STEP, selection)]
        self.jobs[0]['steps'] += [{'name':n,'conclusion':'success'} for n in FULL_STEPS]
        self.jobs[0]['steps'].append({'name':selection,'conclusion':'skipped'})
        self.run['event'] = 'workflow_dispatch'
        self.assertEqual(self.auth()[0], 'full')
        valid_steps = copy.deepcopy(self.jobs[0]['steps'])
        self.run['event'] = 'push'
        with self.assertRaises(ValueError): self.auth()
        self.run['event'] = 'workflow_dispatch'
        for outcome in ('failure', 'cancelled'):
            self.jobs[0]['steps'][-1]['conclusion'] = outcome
            with self.subTest(outcome=outcome), self.assertRaises(ValueError): self.auth()
        for bad in ([s for s in valid_steps if s['name'] != selection],
                    valid_steps + [valid_steps[-1]],
                    [s for s in valid_steps if s['name'] != FULL_STEPS[0]]):
            self.jobs[0]['steps'] = bad
            with self.assertRaises(ValueError): self.auth()

    def test_artifact_ambiguity_and_foreign_execution_rejected(self):
        a={**self.receipt['artifacts'][0],'expired':False,'workflow_run':{'id':self.run['id'],'head_sha':self.run['head_sha']}}
        self.assertEqual(select_artifact([a],a['name'],self.run,self.jobs[0]),a)
        with self.assertRaises(ValueError):select_artifact([a,a],a['name'],self.run,self.jobs[0])
        a['workflow_run']['id']+=1
        with self.assertRaises(ValueError):select_artifact([a],a['name'],self.run,self.jobs[0])

    def test_live_package_integrity_and_no_fake_projects_in_production(self):
        manifest,p,a=validate_package(self.directory)
        self.assertEqual(manifest['summary']['code']['fuzzyEquivalentBytes'],p['measures']['code']['fuzzy'])
        self.assertEqual(manifest['summary']['functions']['exact'],a['credited_functions'])
        projects=locked_projects(ROOT)
        self.assertEqual({c['slug'] for c,_,_ in projects},
                         {c['slug'] for c in decode((ROOT/'config/projects.json').read_bytes())})
        for config,_,report in projects:
            self.assertEqual(report['origin'],'measured')
            self.assertEqual(report['project'],config['slug'])
            self.assertEqual(report['repository'],config['repository'])

    def test_corrupt_package_cannot_replace_last_good(self):
        payloads={p.name:p.read_bytes() for p in self.directory.iterdir()}
        manifest=decode(payloads['manifest.json'])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            import shutil
            shutil.copytree(ROOT/'config',root/'config')
            install(root,None,manifest,payloads,{})
            before=(root/'data/reports.lock.json').read_bytes()
            payloads['progress.json']=b'{}'
            with self.assertRaises(ValueError):install(root,None,manifest,payloads,{})
            self.assertEqual((root/'data/reports.lock.json').read_bytes(),before)

    def test_cache_requires_accepted_main_digest_not_a_real_run_id(self):
        import base64
        entry=decode((ROOT/'data/reports.lock.json').read_bytes())['projects']['nflstreet2']
        response={'encoding':'base64','content':base64.b64encode(encoded({'schemaVersion':1,'projects':{'nflstreet2':entry}})).decode()}
        with patch('import_nfl.GitHub.get',return_value=response):
            self.assertTrue(accepted_package(entry))
            mutated={**entry,'manifestSha256':'0'*64}
            self.assertFalse(accepted_package(mutated))

    def test_extra_file_never_enters_public_package(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)/'package';shutil.copytree(self.directory,directory)
            (directory/'unrelated.bin').write_bytes(b'private research')
            with self.assertRaisesRegex(ValueError,'package files'):validate_package(directory)


if __name__ == '__main__':unittest.main()
