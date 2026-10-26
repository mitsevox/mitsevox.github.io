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
const fs = await import('node:fs');
const map=JSON.parse(fs.readFileSync('docs/reporting/examples/map-evidence.json','utf8'));
assertMapCompatibility(map,'map-v2');
assertMapCompatibility({...map,schemaVersion:1},'map-v1');
for (const [version,identifier] of [[1,'map-v2'],[2,'map-v1'],[3,'map-v3'],['2','map-v2']]) {
  assert.throws(()=>assertMapCompatibility({...map,schemaVersion:version},identifier));
}
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
const summary=JSON.parse(fs.readFileSync('docs/reporting/examples/map-summary.json','utf8'));
const project={modules:{map:true},reportBase:'/report',report:{target:{id:'TEST',sha1:'a'.repeat(40)},summary,revision:'b'.repeat(40),publishedAt:'2000-01-02T00:00:00Z',modules:{map:{asset:{path:'map.json',schema:'map-v2'}}}}};
globalThis.fetch=async()=>({ok:true,json:async()=>map});
const result=await fetchProgress(project,new AbortController().signal);
assert.deepEqual(result.files,map.files);assert.deepEqual(result.sections,map.sections);
project.report.modules.map.asset.schema='map-v1';
await assert.rejects(fetchProgress(project,new AbortController().signal),/map schema/);
const legacy={schema:1,files:map.files,sections:map.sections};
globalThis.fetch=async()=>({ok:true,json:async()=>legacy});
assert.deepEqual(await fetchProgress({progressUrl:'/legacy.json'},new AbortController().signal),legacy);
project.report.modules.map.asset={path:'progress.json',schema:'nfl-progress-v1'};
assert.deepEqual((await fetchProgress(project,new AbortController().signal)).files,legacy.files);
assert.throws(()=>assertMapCompatibility({...legacy,schemaVersion:2},'nfl-progress-v1'));
console.log('Browser compatibility, source labels, partial files, detail text and v1/v2/legacy fetch checks passed.');
'''
        result=subprocess.run(['node','--input-type=module'],input=script,
                              text=True,cwd=ROOT,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
