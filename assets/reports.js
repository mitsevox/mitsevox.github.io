import {makeBoundaryGraph, unpackBoundaryGraph} from './map-geometry.js';
import {validateMap} from './report-map-validation.js';

function summaryView(project){
  const report=project.report;
  const measures=Object.fromEntries(['code','data'].map(kind=>{
    const m=report.summary[kind];
    return [kind,{total:m.totalBytes,linked:m.linkedBytes,matched:m.matchedBytes,
      ...(m.fuzzyEquivalentBytes===null?{}:{fuzzy:m.fuzzyEquivalentBytes})}];
  }));
  return {schema:1,baseline:'verified',basis:'measured-bytes',target:project.target,
    target_sha1:report.target.sha1,revision:report.revision,built_at:report.publishedAt,
    measures,functions:report.summary.functions,file_counts:report.summary.files};
}
// Snapshot URLs are immutable; retain a bounded set of parsed payloads across routes.
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
function loadMap(url, schema, measures) {
  const fallback = () => read(url, undefined, true).then(map => validateMap(map, schema, measures));
  return workerRequest({url:new URL(url, import.meta.url).href, schema, measures}, fallback);
}
export async function fetchBoundaryGraph(layout) {
  const result = await workerRequest({layout}, async () => {
    await new Promise(resolve => setTimeout(resolve, 0));
    return makeBoundaryGraph(layout);
  });
  return Array.isArray(result) ? result : unpackBoundaryGraph(result);
}
export async function fetchSummary(project,signal){
  const summary=project.report?summaryView(project):await read(project.summaryUrl,signal);
  return project.latestCommit?{...summary,latest_commit:project.latestCommit}:summary;
}
export async function fetchProgress(project,signal){
  if(!project.report)return read(project.progressUrl,signal);
  const p=summaryView(project);
  if(project.modules?.map!==false){
    const asset=project.report.modules.map.asset;
    if(!asset)throw Error('Map unsupported');
    const url=project.reportBase+'/'+asset.path;
    const key=JSON.stringify([url,asset.schema,p.measures]);
    const map=await subscribe(cached(maps,key,()=>loadMap(url,asset.schema,p.measures),3),signal);
    Object.assign(p,{basis:'executable-sections',sections:map.sections,files:map.files});
  }
  return p;
}
export async function fetchActivity(project,signal){
  if(!project.report)return read(project.activityUrl,signal);
  const report=project.report,files=new Map();
  const a={schema:1,revision:report.revision,target:project.target,target_sha1:report.target.sha1};
  await Promise.all([['timeline','snapshots'],['contributors','contributors']].map(async ([module,field])=>{
    if(project.modules?.[module]===false)return;
    const asset=report.modules[module].asset;
    if(!asset)throw Error('Unsupported activity module');
    const url=project.reportBase+'/'+asset.path;
    if(!files.has(url))files.set(url,read(url,signal,true));
    a[field]=(await files.get(url))[field];
  }));
  return a;
}
