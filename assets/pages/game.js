// A game page at one target: one section per feature. A feature whose data this target lacks is
// removed with its section; the rest load their code on demand. Adding a feature is a module in
// features/ (mount(root, ctx) -> {ready, destroy}), a section in game.html and one entry below.
import {createTooltip} from '../components/ui/tooltip.js';
import {createContributionLink} from '../components/ui/contribution-link.js';
import {pageScope} from '../lifecycle.js';

const FEATURES = [
  // The heading has no section of its own: it builds the identity block at the top of the page.
  {section:null, available:() => true, load:() => import('../features/identity.js')},
  {section:'.progress', available:project => project.available, load:() => import('../features/summary.js')},
  // The map is the heaviest payload on the page, so it loads only as it nears the viewport.
  {section:'#project-map', available:project => project.modules.map, load:() => import('../features/map.js'), deferred:true},
  {section:'.history-section', available:project => project.modules.timeline, load:() => import('../features/history.js')},
  {section:'.people-section', available:project => project.modules.contributors, load:() => import('../features/contributors.js')},
];
const COUNTS = {function:'functionCounts', file:'fileCounts'};

// Trim the template to what this target has, before it is shown.
export function prepare(main, project) {
  main.querySelector('h1').textContent = project.title + ' decompilation progress';
  main.querySelector('[data-ui="contribution-link"]').replaceWith(createContributionLink({href:project.contributeUrl, variant:'callout'}));
  if (!project.contributionsEnabled) main.querySelector('.lower').remove();
  for (const [kind, module] of Object.entries(COUNTS)) if (!project.modules[module]) main.querySelector(`[data-stats="${kind}"]`)?.remove();
  if (!main.querySelector('[data-stats]')) main.querySelector('.stats-grid')?.remove();
  for (const feature of FEATURES) if (feature.section && !feature.available(project)) main.querySelector(feature.section)?.remove();
}

// A controller that exists before its module has loaded, so the page can always destroy it.
function controller(feature, main, context, scope) {
  let mounted = null, destroyed = false;
  const start = () => feature.load().then(module => {
    if (destroyed) return;
    mounted = module.mount(main, context);
    return mounted.ready;
  });
  if (!feature.deferred) return {ready:start(), destroy() { destroyed = true; mounted?.destroy(); }};
  const section = main.querySelector(feature.section);
  const observer = new IntersectionObserver(entries => {
    if (!entries.some(entry => entry.isIntersecting)) return;
    observer.disconnect();
    start().catch(error => console.error(error));
  }, {rootMargin:'800px 0px'});
  observer.observe(section);
  scope.signal.addEventListener('abort', () => observer.disconnect(), {once:true});
  // A deferred section has a fixed height, so the page is ready without it.
  return {ready:Promise.resolve(), destroy() { destroyed = true; observer.disconnect(); mounted?.destroy(); }};
}

export function mount(main, {project, buildLink}) {
  const scope = pageScope();
  const tooltip = createTooltip({id:'map-tooltip', scope});
  const slot = main.querySelector('[data-ui="map-tooltip"]');
  if (slot) slot.replaceWith(tooltip.node); else main.append(tooltip.node);
  const context = {project, tooltip, buildLink};
  const controllers = FEATURES.filter(feature => !feature.section || main.querySelector(feature.section))
    .map(feature => controller(feature, main, context, scope));
  return {
    ready:Promise.allSettled(controllers.map(c => c.ready)),
    destroy() { controllers.forEach(c => c.destroy()); tooltip.destroy(); scope.destroy(); },
  };
}
