// Production assembly replaces these bindings with validated immutable reports.
export const production = false;
const read = async path => {
  const response=await fetch(path,{cache:'no-cache'});
  if(!response.ok)throw Error('Verified report configuration unavailable');
  return response.json();
};
const [lock,configurations]=await Promise.all([read('/data/reports.lock.json'),read('/config/projects.json')]);
export const reportProjects=Object.fromEntries(await Promise.all(configurations.map(async config=>{
  const catalog=config.schemaVersion===2?await read('/config/'+config.targetRegistry):null;
  const group=lock.projects[config.slug];
  const bind=async entry=>{
    if(!entry)return {available:false};
    const base='/'+entry.path,manifest=await read(base+'/manifest.json');
    const modules={...config.modules};
    if(catalog)for(const key of Object.keys(modules)){
      const counts=manifest.summary[key==='functionCounts'?'functions':'files'];
      const supported=['functionCounts','fileCounts'].includes(key)?counts&&counts.exact!==null&&counts.named!==null:manifest.modules[key]?.status==='supported';
      modules[key]=!!(modules[key]&&supported);
    }
    return {available:true,target:manifest.target.id,targetSha1:manifest.target.sha1,reportBase:base,report:manifest,latestCommit:entry.latestCommit,modules};
  };
  let primary,variants;
  if(catalog){
    // Local development may still hold the immutable v1 bootstrap selection.
    const legacy=group.targets?null:await read('/'+group.path+'/manifest.json');
    variants=Object.fromEntries(await Promise.all(catalog.targets.map(async item=>{
      const entry=group.targets?.[item.target.id]||(!group.targets&&item.legacyTargets.some(old=>['id','console','sha1'].every(key=>old[key]===legacy.target[key]))?group:null);
      return [item.target.id,await bind(entry)];
    })));
    primary={...variants[catalog.defaultTarget]};
    const commits=Object.values(variants).filter(item=>item.available&&item.latestCommit?.date).map(item=>item.latestCommit);
    if(commits.length)primary.latestCommit=commits.sort((a,b)=>b.date.localeCompare(a.date))[0];
  }else primary=await bind(group);
  return [config.slug,{...config,...primary,preview:false,
    ...(catalog?{targetCatalog:catalog,targetReports:variants,target:catalog.defaultTarget}:{}),
    contributionsEnabled:config.contributions.accepting,contributeUrl:config.contributions.guideUrl}];
})));
