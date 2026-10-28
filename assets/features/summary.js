// Build progress: the code/data bars, the function and file counts, and the footer build link.
import {createProgressBar} from '../components/ui/progress-bar.js';
import {createCountSummary} from '../components/ui/count-summary.js';
import {pageScope} from '../lifecycle.js';
import {fetchSummary} from '../reports.js';
import {validMeasure} from '../report-map-validation.js';

export function mount(root, {project, tooltip, buildLink}) {
const scope = pageScope();
const {signal} = scope;
const progressBars=Object.fromEntries(['code','data'].map(kind=>{const bar=createProgressBar({kind,scope,tooltip});root.querySelector('.progress').append(bar.node);return [kind,bar];}));
const countPanels={};
for(const placeholder of root.querySelectorAll('[data-stats]')){
  const panel=createCountSummary({kind:placeholder.dataset.stats,scope});
  countPanels[placeholder.dataset.stats]=panel;placeholder.replaceWith(panel.node);
}
function renderCounts(functions, type, basis) {
  if (!root.querySelector('[data-stats="' + type + '"]')) return;
  const available = functions && functions.total > 0;
  if (functions && (!Number.isSafeInteger(functions.total) || functions.total < 0 ||
      !['exact', 'named'].every(field => Number.isSafeInteger(functions[field]) && functions[field] >= 0 && functions[field] <= functions.total))) {
    throw new Error('Invalid function progress');
  }
  countPanels[type].update(available ? functions : null);
}

function renderSummary(data) {
if(data.schema!==1||data.target!==project.target||data.target_sha1!==project.targetSha1||data.baseline!=='verified'||!(/^[a-f0-9]{40}$/).test(data.revision)||!validMeasure(data.measures?.code)||!validMeasure(data.measures?.data))throw new Error('Invalid progress');
renderCounts(data.functions, 'function', 'provisional-analysis');renderCounts(data.file_counts, 'file', 'mapped-file-inventory');
for(const kind of ['code','data'])progressBars[kind].update(data.measures[kind]);
const link=buildLink;link.href=project.preview?project.repo:project.repo+'/commit/'+data.revision;link.textContent=project.preview?'View repository':'Verified report · '+data.revision.slice(0,7);link.title=project.preview?'View project on GitHub':'Measured '+(project.report?.measuredAt||data.built_at)+'; published '+data.built_at;
}
async function load() {
  try {
    const summary = await fetchSummary(project, signal);
    if (signal.aborted) return;
    renderSummary(summary);
  } catch {
    if (signal.aborted) return;
    renderCounts(null, 'function', 'provisional-analysis');renderCounts(null, 'file', 'mapped-file-inventory');
    buildLink.textContent='Progress unavailable';
    for(const bar of Object.values(progressBars))bar.unavailable();
  }
}
return {ready: load(), destroy: scope.destroy};
}
