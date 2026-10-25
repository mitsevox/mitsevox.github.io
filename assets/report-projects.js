// Local preview reads one atomic report lock. Production builds replace this
// module with validated, release-specific bindings; visitors make no API calls.
export const production = false;
const read = async path => {
  const response = await fetch(path, {cache:'no-cache'});
  if (!response.ok) throw Error('Verified report configuration unavailable');
  return response.json();
};
const [lock, configurations] = await Promise.all([read('/data/reports.lock.json'), read('/config/projects.json')]);
export const reportProjects = Object.fromEntries(configurations.map(config => {
  const entry = lock.projects[config.slug], base = '/'+entry.path;
  return [config.slug, {preview:false, progressUrl:base+'/progress.json', activityUrl:base+'/activity.json',
    summaryUrl:base+'/summary.json', latestCommit:entry.latestCommit, modules:config.modules,
    contributionsEnabled:config.contributions.accepting, contributeUrl:config.contributions.guideUrl}];
}));
