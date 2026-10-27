"""Target view-model migration without modifying original package identity."""
from pathlib import Path
import json
import subprocess
import unittest
from reporting.validation import ROOT


class TargetUI(unittest.TestCase):
    def test_explicit_selection_clears_default_state_and_v1_alias_keeps_original_manifest(self):
        source='''
import assert from 'node:assert/strict';
import {selectTarget} from MODULE;
import {fetchSummary} from REPORTS;
const old={schemaVersion:1,target:{id:'OLD',sha1:'b'.repeat(40)},revision:'a'.repeat(40),publishedAt:'2026-10-25T00:00:00Z',summary:{code:{totalBytes:100,linkedBytes:20,matchedBytes:30,fuzzyEquivalentBytes:40},data:{totalBytes:10,linkedBytes:0,matchedBytes:0,fuzzyEquivalentBytes:null},functions:null,files:null}};
const p={target:'ID-rev0',targetCatalog:{defaultTarget:'ID-rev0',targets:[{target:{id:'ID-rev0'}},{target:{id:'ID-rev1'},status:'archived'}]},targetReports:{'ID-rev0':{available:true,report:old,modules:{map:false},reportBase:'/immutable',latestCommit:{title:'new'}}},modules:{map:true,timeline:true},contributionsEnabled:true};
const active=selectTarget(p,new URL('https://example.test/games/game/?target=ID-rev0'));
assert.equal((await fetchSummary(active)).target,'ID-rev0');assert.equal(old.target.id,'OLD');
assert.equal((await fetchSummary(active)).measures.code.linked,20);
for(const id of ['ID-rev1','invalid']){
 const selected=selectTarget(p,new URL('https://example.test/games/game/?target='+id));
 assert.equal(selected.available,false);assert.equal(selected.report,null);assert.equal(selected.reportBase,null);assert.equal(selected.latestCommit,null);assert.equal(selected.contributionsEnabled,false);assert.ok(Object.values(selected.modules).every(v=>v===false));
}
const single={target:'OLD'};assert.equal(selectTarget(single,new URL('https://example.test/')),single);
'''.replace('MODULE',json.dumps((ROOT/'assets/targets.js').as_uri())).replace('REPORTS',json.dumps((ROOT/'assets/reports.js').as_uri()))
        subprocess.run(['node','--input-type=module','-e',source],check=True,capture_output=True,text=True)
