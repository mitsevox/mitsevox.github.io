import {makeBoundaryGraph, unpackBoundaryGraph} from './map-geometry.js';
import {validateMap} from './report-map-validation.js';

function summaryView(project){
  const report=project.report,s=report.summary;
  const measures=Object.fromEntries(['code','data'].map(kind=>{
    const m=s[kind];
    return [kind,{total:m.total,linked:m.linked,matched:m.matched,...(m.fuzzy===null?{}:{fuzzy:m.fuzzy})}];
  }));
  return {schema:1,baseline:'verified',basis:'measured-bytes',target:project.target,
    target_sha1:project.targetSha1,revision:report.source.revision,built_at:report.measuredAt,
    measures,functions:s.functions,file_counts:s.files};
}
// A target's files change with each measurement; keying them by revision makes each URL immutable.
function asset(project,path){return project.reportBase+path+'?v='+project.report.source.revision.slice(0,12);}
// Revisioned asset URLs are immutable; retain a bounded set of parsed payloads across routes.
const payloads = new Map(), maps = new Map();
function cached(cache, key, load, limit = 8) {
  if (cache.has(key)) {
    const value = cache.get(key);cache.delete(key);cache.set(key, value);return value;
  }
  const value = Promise.resolve().then(load);
  cache.set(key, value);
  while (cache.size > limit) cache.delete(cache.keys().next().value);
  value.catch(() => { if (cache.get(key) === value) cache.delete(key); });
  return value;
}
// A departing page cancels its subscription, not another page's shared request.
function subscribe(promise, signal) {
  if (!signal) return promise;
  if (signal.aborted) return Promise.reject(new DOMException('Aborted', 'AbortError'));
  return new Promise((resolve, reject) => {
    const abort = () => { cleanup();reject(new DOMException('Aborted', 'AbortError')); };
    const cleanup = () => signal.removeEventListener('abort', abort);
    signal.addEventListener('abort', abort, {once:true});
    promise.then(value => {cleanup();resolve(value);}, error => {cleanup();reject(error);});
  });
}
async function read(url, signal, immutable = false) {
  const load = async () => {
    const response = await fetch(url, immutable ? {cache:'force-cache'} : {signal, cache:'no-cache'});
    if (!response.ok) throw Error('Report unavailable');
    return response.json();
  };
  return immutable ? subscribe(cached(payloads, url, load), signal) : load();
}
let worker = null, requestID = 0, workerUnavailable = false;
const pending = new Map();
function mapWorker() {
  if (worker || workerUnavailable) return worker;
  if (typeof Worker === 'undefined') { workerUnavailable = true;return null; }
  try {
    worker = new Worker(new URL('./report-worker.js', import.meta.url), {type:'module'});
    worker.onmessage = ({data}) => {
      const request = pending.get(data.id);if (!request) return;
      pending.delete(data.id);
      if (data.error) request.reject(Error(data.error));else request.resolve(data.graph ?? data.map);
    };
    worker.onerror = () => {
      worker.terminate();worker = null;workerUnavailable = true;
      for (const request of pending.values()) request.fallback();
      pending.clear();
    };
  } catch { workerUnavailable = true; }
  return worker;
}
function workerRequest(message, fallback) {
  const service = mapWorker();
  if (!service) return fallback();
  return new Promise((resolve, reject) => {
    const id = ++requestID;
    pending.set(id, {resolve, reject, fallback:() => fallback().then(resolve, reject)});
    try { service.postMessage({id, ...message}); }
    catch (error) { pending.delete(id);reject(error); }
  });
}
function loadMap(url, measures) {
  const fallback = () => read(url, undefined, true).then(map => validateMap(map, measures));
  return workerRequest({url:new URL(url, import.meta.url).href, measures}, fallback);
}
export async function fetchBoundaryGraph(layout) {
  const result = await workerRequest({layout}, async () => {
    await new Promise(resolve => setTimeout(resolve, 0));
    return makeBoundaryGraph(layout);
  });
  return Array.isArray(result) ? result : unpackBoundaryGraph(result);
}
export async function fetchSummary(project){
  const source=project.report.source;
  return {...summaryView(project),latest_commit:{title:source.title,date:source.committedAt,url:source.url,revision:source.revision}};
}
export async function fetchProgress(project,signal){
  const p=summaryView(project);
  if(project.modules.map){
    const url=asset(project,project.report.modules.map);
    const key=JSON.stringify([url,p.measures]);
    const map=await subscribe(cached(maps,key,()=>loadMap(url,p.measures),3),signal);
    Object.assign(p,{basis:'executable-sections',sections:map.sections,files:map.files});
  }
  return p;
}
export async function fetchActivity(project,signal){
  const report=project.report;
  const a={schema:1,revision:report.source.revision,target:project.target,target_sha1:project.targetSha1};
  await Promise.all([
    project.modules.timeline&&read(asset(project,'history.json'),signal,true).then(rows=>{
      a.snapshots=rows.map(row=>({revision:row.revision,built_at:row.measuredAt,
        code:{total:row.code.total,linked:row.code.linked},data:{total:row.data.total,linked:row.data.linked}}));
    }),
    project.modules.contributors&&read(asset(project,report.modules.contributors),signal,true).then(document=>{a.contributors=document.contributors;}),
  ]);
  return a;
}
