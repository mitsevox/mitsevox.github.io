"""Exercise shared requests, cancellation, retries and the real worker modules."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReportLoadingTests(unittest.TestCase):
    def run_js(self, script):
        result = subprocess.run(['node', '--input-type=module'], input=script,
                                text=True, cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_shared_immutable_payloads_do_not_block_summaries_or_other_subscribers(self):
        self.run_js(r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {fetchSummary,fetchProgress,fetchActivity} from './assets/reports.js';
const map=JSON.parse(fs.readFileSync('docs/reporting/examples/map-evidence.json'));
const summary=JSON.parse(fs.readFileSync('docs/reporting/examples/map-summary.json'));
const project={modules:{map:true,timeline:true,contributors:true},reportBase:'/one',report:{target:{id:'TEST',sha1:'a'.repeat(40)},summary,revision:'b'.repeat(40),publishedAt:'2000-01-02T00:00:00Z',modules:{map:{asset:{path:'map.json',schema:'map-v2'}},timeline:{asset:{path:'timeline.json'}},contributors:{asset:{path:'contributors.json'}}}}};
let release, calls=[];
const delayed=new Promise(resolve=>release=resolve);
globalThis.fetch=async(url,options)=>{
  calls.push({url,options});
  if(url==='/one/map.json'){await delayed;return {ok:true,json:async()=>map};}
  if(url.endsWith('timeline.json'))return {ok:true,json:async()=>({snapshots:[{revision:'timeline'}]})};
  if(url.endsWith('contributors.json'))return {ok:true,json:async()=>({contributors:[{login:'credit'}]})};
  return {ok:true,json:async()=>map};
};
const a=new AbortController(),b=new AbortController();
const cancelled=fetchProgress(project,a.signal);
const survivor=fetchProgress(project,b.signal);
assert.equal((await fetchSummary(project)).measures.code.total,summary.code.totalBytes);
a.abort();await assert.rejects(cancelled,{name:'AbortError'});
release();const data=await survivor;
assert.deepEqual(data.files,map.files);
await fetchProgress(project);
assert.equal(calls.filter(c=>c.url==='/one/map.json').length,1);
assert.equal(calls[0].options.cache,'force-cache');
assert.equal(calls[0].options.signal,undefined);
const result=await fetchActivity(project);
assert.equal(result.snapshots[0].revision,'timeline');assert.equal(result.contributors[0].login,'credit');
await fetchActivity(project);assert.equal(calls.length,3);
// The cache cannot hide a schema/measurement disagreement or a failed response.
await assert.rejects(fetchProgress({...project,report:{...project.report,summary:{...summary,code:{...summary.code,totalBytes:summary.code.totalBytes+1}}}}),/Inconsistent map/);
let attempts=0;
globalThis.fetch=async()=>({ok:++attempts>1,json:async()=>map});
const retry={...project,reportBase:'/retry'};
await assert.rejects(fetchProgress(retry),/unavailable/);
await fetchProgress(retry);assert.equal(attempts,2);
// Different snapshots never reuse a previous revision's payload.
await fetchProgress({...project,reportBase:'/two'});assert.equal(attempts,3);
// Both activity requests start even while one remains unresolved.
let finishHistory;const history=new Promise(resolve=>finishHistory=resolve), started=[];
globalThis.fetch=async(url)=>{started.push(url);if(url.endsWith('timeline.json'))await history;return {ok:true,json:async()=>url.endsWith('timeline.json')?{snapshots:[]}:{contributors:[]}};};
const activity=fetchActivity({...project,reportBase:'/parallel'});
await new Promise(resolve=>setTimeout(resolve,0));assert.equal(started.length,2);
finishHistory();await activity;
''')

    def test_worker_parses_validates_and_builds_the_same_boundary_graph(self):
        self.run_js(r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Worker as NodeWorker} from 'node:worker_threads';
import {makeBoundaryGraph} from './assets/map-geometry.js';
const map=JSON.parse(fs.readFileSync('docs/reporting/examples/map-evidence.json'));
const summary=JSON.parse(fs.readFileSync('docs/reporting/examples/map-summary.json'));
const entry=new URL('./assets/report-worker.js',import.meta.url).href;
let workerFetches=0,instance;
globalThis.fetch=()=>{throw Error('Map parsing must run in worker');};
globalThis.Worker=class {
  constructor(){
    instance=this;
    const bootstrap=`import {parentPort,workerData} from 'node:worker_threads';
      globalThis.self={postMessage:data=>parentPort.postMessage(data)};
      globalThis.fetch=async()=>{parentPort.postMessage({fetched:true});return {ok:true,json:async()=>workerData.map};};
      await import(workerData.entry);
      parentPort.on('message',data=>self.onmessage({data}));`;
    this.worker=new NodeWorker(new URL('data:text/javascript,'+encodeURIComponent(bootstrap)),{workerData:{map,entry}});
    this.worker.on('message',data=>{if(data.fetched)workerFetches++;else this.onmessage({data});});
    this.worker.on('error',error=>this.onerror(error));
  }
  postMessage(data){this.worker.postMessage(data);}
  terminate(){this.worker.terminate();}
};
const {fetchProgress,fetchBoundaryGraph}=await import('./assets/reports.js?worker-test');
const project={modules:{map:true},reportBase:'https://test.invalid/one',report:{target:{id:'TEST',sha1:'a'.repeat(40)},summary,revision:'b'.repeat(40),publishedAt:'2000-01-02T00:00:00Z',modules:{map:{asset:{path:'map.json',schema:'map-v2'}}}}};
try {
  assert.deepEqual((await fetchProgress(project)).files,map.files);
  await fetchProgress(project);assert.equal(workerFetches,1);
  await assert.rejects(fetchProgress({...project,report:{...project.report,modules:{map:{asset:{path:'map.json',schema:'map-v1'}}}}}),/map schema/);
  const layout=[{x:0,y:0,w:10,h:10},{x:10,y:0,w:20,h:10}];
  const describe=nodes=>nodes.map(n=>({x:n.x,y:n.y,edges:n.edges.map(e=>({x:e.node.x,y:e.node.y,length:e.length}))}));
  assert.deepEqual(describe(await fetchBoundaryGraph(layout)),describe(makeBoundaryGraph(layout)));
  const columns=100,rows=120,dense=Array.from({length:columns*rows},(_,i)=>({x:i%columns,y:Math.floor(i/columns),w:1,h:1}));
  const graph=await fetchBoundaryGraph(dense);
  assert.equal(graph.length,(columns+1)*(rows+1));
  assert.equal(graph.reduce((sum,node)=>sum+node.edges.length,0),2*(columns*(rows+1)+rows*(columns+1)));
  assert.ok(graph.every(node=>node.edges.every(edge=>edge.length===1)));
} finally {instance?.terminate();}
''')

    def test_worker_startup_failure_keeps_validation_and_retry_available(self):
        self.run_js(r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
const map=JSON.parse(fs.readFileSync('docs/reporting/examples/map-evidence.json'));
const summary=JSON.parse(fs.readFileSync('docs/reporting/examples/map-summary.json'));
let calls=0;
globalThis.Worker=class {postMessage(){queueMicrotask(()=>this.onerror());}terminate(){}};
globalThis.fetch=async()=>{calls++;return {ok:true,json:async()=>map};};
const {fetchProgress}=await import('./assets/reports.js?failed-worker');
const project={modules:{map:true},reportBase:'https://test.invalid/fallback',report:{target:{id:'TEST',sha1:'a'.repeat(40)},summary,revision:'b'.repeat(40),publishedAt:'2000-01-02T00:00:00Z',modules:{map:{asset:{path:'map.json',schema:'map-v2'}}}}};
assert.deepEqual((await fetchProgress(project)).files,map.files);assert.equal(calls,1);
await assert.rejects(fetchProgress({...project,report:{...project.report,summary:{...summary,code:{...summary.code,totalBytes:summary.code.totalBytes+1}}}}),/Inconsistent map/);
''')


if __name__ == '__main__':
    unittest.main()
