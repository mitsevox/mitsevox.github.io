// Production assembly replaces these bindings with validated immutable reports.
export const production = false;
const read = async path => {
  const response=await fetch(path,{cache:'no-cache'});
  if(!response.ok)throw Error('Verified report configuration unavailable');
  return response.json();
};
const [lock,configurations]=await Promise.all([read('/data/reports.lock.json'),read('/config/projects.json')]);
export const reportProjects=Object.fromEntries(await Promise.all(configurations.map(async config=>{
  const entry=lock.projects[config.slug],base='/'+entry.path;
  const manifest=await read(base+'/manifest.json');
  return [config.slug,{...config,preview:false,targetSha1:manifest.target.sha1,reportBase:base,
    report:manifest,latestCommit:entry.latestCommit,contributionsEnabled:config.contributions.accepting,
    contributeUrl:config.contributions.guideUrl}];
})));
