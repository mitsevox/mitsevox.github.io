function summaryView(project){
  const report=project.report;
  const measures=Object.fromEntries(['code','data'].map(kind=>{
    const m=report.summary[kind];
    return [kind,{total:m.totalBytes,linked:m.linkedBytes,matched:m.matchedBytes,
      ...(m.fuzzyEquivalentBytes===null?{}:{fuzzy:m.fuzzyEquivalentBytes})}];
  }));
  return {schema:1,baseline:'verified',basis:'measured-bytes',target:report.target.id,
    target_sha1:report.target.sha1,revision:report.revision,built_at:report.publishedAt,
    measures,functions:report.summary.functions,file_counts:report.summary.files};
}
async function read(url,signal){
  const response=await fetch(url,{signal,cache:'no-cache'});
  if(!response.ok)throw Error('Report unavailable');
  return response.json();
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
    const map=await read(project.reportBase+'/'+asset.path,signal);
    Object.assign(p,{basis:'executable-sections',sections:map.sections,files:map.files});
  }
  return p;
}
export async function fetchActivity(project,signal){
  if(!project.report)return read(project.activityUrl,signal);
  const report=project.report,files=new Map();
  const a={schema:1,revision:report.revision,target:report.target.id,target_sha1:report.target.sha1};
  for(const [module,field] of [['timeline','snapshots'],['contributors','contributors']]){
    if(project.modules?.[module]===false)continue;
    const asset=report.modules[module].asset;
    if(!asset)throw Error('Unsupported activity module');
    const url=project.reportBase+'/'+asset.path;
    if(!files.has(url))files.set(url,read(url,signal));
    a[field]=(await files.get(url))[field];
  }
  return a;
}
