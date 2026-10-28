"""Target selection: a view only ever carries its own target's measurements."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TargetUI(unittest.TestCase):
    def test_selection_never_inherits_another_targets_report(self):
        script = r'''
import assert from 'node:assert/strict';
import {selectTarget, withTarget} from './assets/targets.js';
import {fetchSummary} from './assets/reports.js';
import {latest} from './tests/fixtures/project.mjs';
const targets=[{id:'ID-rev0',label:'ID',revision:'0',region:'USA',sha1:'a'.repeat(40),status:'active'},
  {id:'ID-rev1',label:'ID',revision:'1',region:'USA',sha1:'c'.repeat(40),status:'archived'}];
const game={slug:'game',base:'/decomp-data/data/game/',defaultTarget:'ID-rev0',targets,reports:{'ID-rev0':latest,'ID-rev1':null},
  contributions:{accepting:true}};
const active=selectTarget(game,new URL('https://example.test/games/game/'));
assert.equal(active.target,'ID-rev0');assert.equal(active.reportBase,'/decomp-data/data/game/ID-rev0/');
assert.equal(active.targetCatalog,targets);assert.equal(active.contributionsEnabled,true);
assert.deepEqual(active.modules,{map:true,timeline:true,contributors:true,functionCounts:false,fileCounts:false});
const summary=await fetchSummary(active);
assert.equal(summary.target,'ID-rev0');assert.equal(summary.target_sha1,'a'.repeat(40));assert.equal(summary.measures.code.linked,20);
for(const id of ['ID-rev1','invalid']){
  const selected=selectTarget(game,new URL('https://example.test/games/game/?target='+id));
  assert.equal(selected.available,false);assert.equal(selected.report,null);assert.equal(selected.reportBase,null);
  assert.equal(selected.contributionsEnabled,false);assert.ok(Object.values(selected.modules).every(v=>v===false));
  assert.equal(selected.unknownTarget,id==='invalid');assert.equal(selected.targetCatalog,id==='invalid'?null:targets);
}
const single=withTarget({...game,targets:[targets[0]]},'ID-rev0');assert.deepEqual(single.targetCatalog,[targets[0]]);
'''
        result = subprocess.run(['node', '--input-type=module'], input=script, text=True, cwd=ROOT, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
