"""Exercise the actual browser modules without external DOM dependencies."""
import json
from pathlib import Path
import subprocess
import unittest


ROOT=Path(__file__).resolve().parents[1]


class MapEvidenceUITests(unittest.TestCase):
    def test_browser_version_gate_tooltip_details_and_report_fetch(self):
        script=r'''
import assert from 'node:assert/strict';
import {assertMapCompatibility, mapLabel, showMapDetails} from './assets/map-evidence.js';
import {fetchProgress} from './assets/reports.js';
import {map,project as target} from './tests/fixtures/project.mjs';
assertMapCompatibility(map);
for (const schema of [2,'1',undefined]) assert.throws(()=>assertMapCompatibility({...map,schema}));
assert.equal(mapLabel({name:'Update',source:'src/math.c'}),'src/math.c · Update');
assert.equal(mapLabel({name:'src/math.c · Update',source:'src/math.c'}),'src/math.c · Update');
assert.equal(mapLabel({name:'src/math.c',source:'src/math.c',complete:false}),'src/math.c · partial file');
assert.equal(mapLabel({name:'src/math.c',source:'src/math.c',complete:true}),'src/math.c');
assert.equal(mapLabel({name:'src/math.c',source:'src/math.c'}),'src/math.c');
const element=tag=>({tag,textContent:'',children:[],append(...items){this.children.push(...items);},replaceChildren(...items){this.children=[...items];}});
globalThis.document={createElement:element};
const heading=element('h3'),list=element('dl');
const panel={hidden:true,querySelector:selector=>selector==='h3'?heading:list};
const item={name:'Update',source:'src/unit.c',comparison_source:'compare/unit.c',boundary:'provisional',scope:'candidate-ranges',complete:false,auto_generated:true};
showMapDetails(panel,item);
assert.equal(panel.hidden,false);
assert.equal(heading.textContent,'src/unit.c · Update');
assert.deepEqual(list.children.map(x=>x.textContent),['Source','src/unit.c','Comparison source','compare/unit.c','Boundary','provisional','Scope','candidate-ranges','File extent','Partial','Generated placeholder','Yes']);
assert.ok(list.children.every(x=>x.innerHTML===undefined));
showMapDetails(panel,{name:'Plain'});assert.equal(panel.hidden,true);assert.equal(list.children.length,0);
showMapDetails(panel,null);assert.equal(panel.hidden,true);assert.equal(heading.textContent,'');
showMapDetails(null,item);
const project=target('/report/');
globalThis.fetch=async()=>({ok:true,json:async()=>map});
const result=await fetchProgress(project,new AbortController().signal);
assert.deepEqual(result.files,map.files);assert.deepEqual(result.sections,map.sections);
globalThis.fetch=async()=>({ok:true,json:async()=>({...map,schema:2})});
await assert.rejects(fetchProgress(target('/other/'),new AbortController().signal),/map schema/);
console.log('Map schema gate, source labels, partial files, detail text and fetch checks passed.');
'''
        result=subprocess.run(['node','--input-type=module'],input=script,
                              text=True,cwd=ROOT,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
