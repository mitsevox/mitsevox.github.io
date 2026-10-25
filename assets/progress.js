import {pageScope} from './lifecycle.js';
export function mountProgress(root, project, buildLink) {
const scope = pageScope();
const {signal, listen, frame, cancelFrame, animate} = scope;
const mapEnabled = project.modules?.map !== false;
const mapListen = mapEnabled ? listen : () => {};
let sections=[];
const canvas=root.querySelector('#canvas');
const projectMap = root.querySelector('#project-map');
const mapLift = document.createElement('div');
mapLift.className = 'map-lift';
mapLift.setAttribute('aria-hidden', 'true');
mapLift.hidden = true;
if (mapEnabled) canvas.parentElement.append(mapLift);
const similarity = item => (item.fuzzy ?? item.matched) / item.size;
const partialColorStrength = .65;
function color(item) {
  if (item.matched === item.size) return 'var(--map-color)';
  const blend = Math.min(similarity(item) / .99, 1) * partialColorStrength * 100;
  return `color-mix(in srgb, var(--empty), var(--map-color) ${blend}%)`;
}
// Preserve report order so neighboring files and functions stay together.
// Balanced area partitioning keeps byte proportions exact across viewport sizes.
function partition(items,x,y,w,h,out){if(!items.length)return;if(items.length===1){out.push({...items[0],x,y,w,h});return;}let total=items.reduce((s,a)=>s+a.size,0),sum=0,split=1;for(let i=0;i<items.length-1;i++){sum+=items[i].size;split=i+1;if(sum>=total/2)break;}const ratio=sum/total;if(w>=h){partition(items.slice(0,split),x,y,w*ratio,h,out);partition(items.slice(split),x+w*ratio,y,w*(1-ratio),h,out);}else{partition(items.slice(0,split),x,y,w,h*ratio,out);partition(items.slice(split),x,y+h*ratio,w,h*(1-ratio),out);}}
const tooltip = root.querySelector('#map-tooltip');
const back = root.querySelector('#map-back');
const search = root.querySelector('#map-search');
const kindPicker = root.querySelector('#map-kind');
if (!mapEnabled) { root.append(tooltip); projectMap.remove(); }
const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
const countAnimations = new WeakMap();
let mapFrame = null;
let activePulses = [];
let rippleSurface = null;
let boundaryGraph = [];
let mapLayout = [];
let hoverTarget = null;
let hoverItem = null;
function countUp(element, value, decimals = 0, suffix = '') {
  const previous = countAnimations.get(element);
  if (previous) cancelFrame(previous);
  const format = number => decimals ? number.toFixed(decimals) + suffix : Math.round(number).toLocaleString() + suffix;
  if (motionPreference.matches) {
    element.textContent = format(value);
    return;
  }
  const start = performance.now();
  const step = now => {
    const t = motionPreference.matches ? 1 : Math.min((now - start) / 780, 1);
    element.textContent = format(value * (1 - Math.pow(1 - t, 3)));
    if (t < 1) countAnimations.set(element, frame(step));
    else countAnimations.delete(element);
  };
  element.textContent = format(0);
  countAnimations.set(element, frame(step));
}
function fillTo(element, percent) {
  if (motionPreference.matches) element.style.width = percent + '%';
  else frame(() => frame(() => { element.style.width = percent + '%'; }));
}
function clearMapMotion() {
  if (mapFrame !== null) cancelFrame(mapFrame);
  mapFrame = null;
  activePulses = [];
  canvas.dataset.activePulses = '0';
  if (rippleSurface) {
    const context = rippleSurface.getContext('2d');
    context.clearRect(0, 0, rippleSurface.width, rippleSurface.height);
  }
}
mapListen(motionPreference, 'change', () => {
  if (motionPreference.matches) { clearMapMotion(); liftAnimation?.cancel(); }
});
function clickOrigin(event, block) {
  const map = canvas.getBoundingClientRect();
  const target = block.getBoundingClientRect();
  const x = event?.detail ? event.clientX : target.left + target.width / 2;
  const y = event?.detail ? event.clientY : target.top + target.height / 2;
  return {x: Math.max(0, Math.min(map.width, x - map.left)),
    y: Math.max(0, Math.min(map.height, y - map.top))};
}
function makeBoundaryGraph(layout) {
  const nodes = [], byPoint = new Map(), rows = new Map(), columns = new Map();
  function group(groups, coordinate) {
    if (!groups.has(coordinate)) groups.set(coordinate, {nodes: [], spans: []});
    return groups.get(coordinate);
  }
  function point(x, y) {
    x = Math.round(x * 10) / 10;
    y = Math.round(y * 10) / 10;
    const key = x + ':' + y;
    if (!byPoint.has(key)) {
      const node = {x, y, edges: []};
      byPoint.set(key, nodes.length);
      nodes.push(node);
      group(rows, y).nodes.push(node);
      group(columns, x).nodes.push(node);
    }
    return nodes[byPoint.get(key)];
  }
  for (const item of layout) {
    const a = point(item.x, item.y), b = point(item.x + item.w, item.y);
    const c = point(item.x, item.y + item.h), d = point(item.x + item.w, item.y + item.h);
    group(rows, a.y).spans.push([a.x, b.x]);
    group(rows, c.y).spans.push([c.x, d.x]);
    group(columns, a.x).spans.push([a.y, c.y]);
    group(columns, b.x).spans.push([b.y, d.y]);
  }
  function connect(groups, axis) {
    for (const entry of groups.values()) {
      entry.nodes.sort((a, b) => a[axis] - b[axis]);
      entry.spans.sort((a, b) => a[0] - b[0]);
      let span = 0, end = -Infinity;
      for (let i = 0; i < entry.nodes.length - 1; i++) {
        const a = entry.nodes[i], b = entry.nodes[i + 1];
        while (span < entry.spans.length && entry.spans[span][0] <= a[axis] + 0.1) {
          end = Math.max(end, entry.spans[span++][1]);
        }
        const length = b[axis] - a[axis];
        if (length > 0 && end >= b[axis] - 0.1) {
          a.edges.push({node: b, length});
          b.edges.push({node: a, length});
        }
      }
    }
  }
  connect(rows, 'x');
  connect(columns, 'y');
  return nodes;
}
function drawPulses(now) {
  mapFrame = null;
  if (!rippleSurface) return;
  const context = rippleSurface.getContext('2d');
  const width = canvas.clientWidth, height = canvas.clientHeight;
  const ratio = rippleSurface.width / width;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.globalCompositeOperation = 'source-over';
  context.clearRect(0, 0, width, height);
  activePulses = activePulses.filter(pulse => now - pulse.start < pulse.duration);
  canvas.dataset.activePulses = activePulses.length;
  if (!activePulses.length) return;
  context.fillStyle = getComputedStyle(canvas).getPropertyValue('--bg').trim();
  context.fillRect(0, 0, width, height);
  context.globalCompositeOperation = 'lighten';
  context.lineWidth = 1.5;
  context.lineCap = 'butt';
  for (const pulse of activePulses) pulse.paint(context, now - pulse.start);
  context.globalCompositeOperation = 'source-over';
  mapFrame = frame(drawPulses);
}
function ripple(origin, start = performance.now()) {
  if (!origin || motionPreference.matches || !rippleSurface || !boundaryGraph.length) return;
  const width = canvas.clientWidth, height = canvas.clientHeight;
  let seed = boundaryGraph[0], nearest = Infinity;
  for (const node of boundaryGraph) {
    const distance = Math.hypot(node.x - origin.x, node.y - origin.y);
    if (distance < nearest) { seed = node; nearest = distance; }
  }
  // Walk connected seams; branch arrivals depend on their route, rather than a circular front.
  const frontier = [], costs = new Map([[seed, 0]]), parents = new Map(), visited = new Set();
  function push(entry) {
    frontier.push(entry);
    let index = frontier.length - 1;
    while (index) {
      const parent = (index - 1) >> 1;
      if (frontier[parent].cost <= entry.cost) break;
      frontier[index] = frontier[parent];
      index = parent;
    }
    frontier[index] = entry;
  }
  function pop() {
    const first = frontier[0], last = frontier.pop();
    if (!frontier.length) return first;
    let index = 0;
    while (index * 2 + 1 < frontier.length) {
      let child = index * 2 + 1;
      if (child + 1 < frontier.length && frontier[child + 1].cost < frontier[child].cost) child++;
      if (frontier[child].cost >= last.cost) break;
      frontier[index] = frontier[child];
      index = child;
    }
    frontier[index] = last;
    return first;
  }
  const routeCount = 16;
  const reach = 1500;
  const easingDistance = 520;
  const pace = 1.8, initialPace = 0.22;
  const arrivalAt = cost => pace * (initialPace * cost + (1 - initialPace) * cost * cost / (2 * easingDistance));
  const distanceAt = time => {
    const clock = Math.max(0, time) / pace;
    return 2 * clock / (initialPace + Math.sqrt(initialPace * initialPace + 2 * (1 - initialPace) * clock / easingDistance));
  };
  const endpoints = Array(routeCount).fill(null);
  push({node: seed, cost: 0});
  while (frontier.length && visited.size < 18000) {
    const current = pop();
    if (visited.has(current.node)) continue;
    visited.add(current.node);
    const dx = current.node.x - seed.x, dy = current.node.y - seed.y;
    const distance = Math.hypot(dx, dy);
    const sector = Math.floor((Math.atan2(dy, dx) + Math.PI) / (Math.PI * 2) * routeCount) % routeCount;
    if (distance > (endpoints[sector]?.distance ?? 0)) endpoints[sector] = {...current, distance};
    for (const edge of current.node.edges) {
      const cost = current.cost + edge.length + 5;
      if (cost > reach || visited.has(edge.node) || cost >= (costs.get(edge.node) ?? Infinity)) continue;
      costs.set(edge.node, cost);
      parents.set(edge.node, {a: current.node, b: edge.node, from: current.cost, to: cost,
        arrival: arrivalAt(current.cost), travel: arrivalAt(cost) - arrivalAt(current.cost)});
      push({node: edge.node, cost});
    }
  }
  // Illuminate a few connected routes, rather than flooding every reachable seam.
  const selected = new Map();
  for (const endpoint of endpoints) {
    let node = endpoint?.node;
    while (node && node !== seed) {
      const edge = parents.get(node);
      if (!edge) break;
      selected.set(node, edge);
      node = edge.a;
    }
  }
  const traces = [...selected.values()].sort((a, b) => a.from - b.from);
  const outgoing = new Map();
  for (const trace of traces) {
    if (!outgoing.has(trace.a)) outgoing.set(trace.a, []);
    outgoing.get(trace.a).push(trace);
  }
  for (const branches of outgoing.values()) {
    branches.sort((a, b) => Math.atan2(a.b.y - a.a.y, a.b.x - a.a.x) - Math.atan2(b.b.y - b.a.y, b.b.x - b.a.x));
  }
  const clocks = new Map([[seed, {arrival: 0, pace: 1, lifetime: 950}]]);
  const branchPaces = [0.65, 1.35, 0.9, 1.7];
  const branchLifetimes = [520, 1150, 720, 1450];
  for (const trace of traces) {
    const parent = clocks.get(trace.a);
    const siblings = outgoing.get(trace.a);
    const rank = siblings.indexOf(trace);
    trace.pace = siblings.length > 1 ? parent.pace * 0.25 + branchPaces[rank % 4] * 0.75 : parent.pace;
    trace.lifetime = siblings.length > 1 ? parent.lifetime * 0.25 + branchLifetimes[rank % 4] * 0.75 : parent.lifetime;
    trace.arrival = parent.arrival;
    trace.travel = (arrivalAt(trace.to) - arrivalAt(trace.from)) * trace.pace;
    clocks.set(trace.b, {arrival: trace.arrival + trace.travel, pace: trace.pace, lifetime: trace.lifetime});
  }
  const attackTime = 45;
  const duration = Math.max(0, ...traces.map(trace => trace.arrival + trace.travel + trace.lifetime));
  const styles = getComputedStyle(canvas);
  const background = styles.getPropertyValue('--bg').trim();
  const rgb = hex => [1, 3, 5].map(index => parseInt(hex.slice(index, index + 2), 16));
  const dark = rgb(background), light = rgb(styles.getPropertyValue('--map-color').trim());
  function paint(context, elapsed) {
    for (const trace of traces) {
      const age = elapsed - trace.arrival;
      if (age <= 0 || age >= trace.travel + trace.lifetime) continue;
      const distance = distanceAt(arrivalAt(trace.from) + age / trace.pace);
      const progress = Math.max(0, Math.min((distance - trace.from) / (trace.to - trace.from), 1));
      const gradient = context.createLinearGradient(trace.a.x, trace.a.y, trace.b.x, trace.b.y);
      // Each point fades from its own arrival; routes continue beyond the visible glow.
      for (let step = 0; step <= 8; step++) {
        const position = step / 8;
        const cost = trace.from + (trace.to - trace.from) * position;
        const pointAge = age - (arrivalAt(cost) - arrivalAt(trace.from)) * trace.pace;
        const fade = Math.pow(Math.max(0, 1 - Math.max(0, pointAge - attackTime) / (trace.lifetime - attackTime)), 1.3);
        const brightness = Math.max(0, Math.min(pointAge / attackTime, 1)) * fade * Math.exp(-cost / 340);
        gradient.addColorStop(position, `rgb(${dark.map((value, index) => Math.round(value + (light[index] - value) * brightness)).join(',')})`);
      }
      context.strokeStyle = gradient;
      context.beginPath();
      context.moveTo(trace.a.x, trace.a.y);
      context.lineTo(trace.a.x + (trace.b.x - trace.a.x) * progress, trace.a.y + (trace.b.y - trace.a.y) * progress);
      context.stroke();
    }
  }
  activePulses.push({origin, start, duration, width, height, paint});
  canvas.dataset.activePulses = activePulses.length;
  if (mapFrame === null) mapFrame = frame(drawPulses);
}
const path = [];
let mapKind = 'code';
function leaves(items) {
  return items.flatMap(item => item.children?.length ? leaves(item.children) : [item]);
}
function mapItems() {
  const roots = sections.filter(section => section.kind === mapKind);
  const query = search.value.trim().toLocaleLowerCase();
  if (query) return roots.flatMap(item => item.name.toLocaleLowerCase().includes(query)
    ? [item] : leaves([item]).filter(leaf => leaf.name.toLocaleLowerCase().includes(query)));
  return path.at(-1)?.children || roots;
}
mapListen(search, 'input', () => {
  path.length = 0;
  render('search');
});
kindPicker.querySelectorAll('button').forEach(button => {
  mapListen(button, 'click', event => {
    mapKind = button.dataset.kind;
    kindPicker.dataset.selected = mapKind;
    projectMap.dataset.kind = mapKind;
    kindPicker.querySelectorAll('button').forEach(option => option.setAttribute('aria-pressed', option === button));
    path.length = 0;
    render('switch', clickOrigin(event, button));
  });
});
let activeTile = null;
let liftedItem = null;
let liftAnimation = null;
let hoverFrame = null;
let hoverPoint = null;
let tooltipWidth = 0, tooltipHeight = 0;
function clearMapLift() {
  liftedItem = null;
  liftAnimation?.cancel();
  liftAnimation = null;
  mapLift.hidden = true;
}
function cancelMapHover() {
  if (hoverFrame !== null) cancelFrame(hoverFrame);
  hoverFrame = null;
  hoverPoint = null;
}
const percent = item => (similarity(item) * 100).toFixed(2) +
  (item.matched === item.size ? '% matched' : '% similarity');
function hideTooltip() {
  cancelMapHover();
  clearMapLift();
  tooltip.hidden = true;
  activeTile?.removeAttribute('aria-describedby');
  activeTile = null;
}
function showTooltip(block, item, x, y) {
  const name = (item.source && !item.name.includes(item.source) ? item.source + ' · ' : '') + item.name;
  showTooltipText(block, name, x, y, percent(item));
  liftMapBlock(item);
}
function showTooltipText(block, text, x, y, value = '') {
  if (!value) clearMapLift();
  const changed = tooltip.hidden || tooltip.dataset.label !== text || tooltip.dataset.value !== value;
  if (activeTile !== block) {
    activeTile?.removeAttribute('aria-describedby');
    activeTile = block;
    block.setAttribute('aria-describedby', 'map-tooltip');
  }
  if (changed) {
    tooltip.dataset.label = text;
    tooltip.dataset.value = value;
    const name = document.createElement('span');
    name.className = 'tooltip-name';
    name.textContent = text + (value ? ' ' : '');
    tooltip.replaceChildren(name);
    if (value) {
      const measure = document.createElement('span');
      measure.className = 'tooltip-value';
      measure.textContent = value;
      tooltip.append(measure);
    }
    tooltip.hidden = false;
    tooltipWidth = tooltip.offsetWidth;
    tooltipHeight = tooltip.offsetHeight;
  }
  const gap = 14;
  tooltip.style.left = Math.max(10, Math.min(x + gap, window.innerWidth - tooltipWidth - 10)) + 'px';
  tooltip.style.top = Math.max(10, Math.min(y + gap, window.innerHeight - tooltipHeight - 10)) + 'px';
}
let palette = null;
function colorValue(item) {
  if (item.matched === item.size) return palette.done;
  const blend = Math.min(similarity(item) / .99, 1) * partialColorStrength;
  return `rgb(${palette.emptyRGB.map((value, index) => Math.round(value + (palette.doneRGB[index] - value) * blend)).join(',')})`;
}
function drawCompletedFinish(context, x, y, width, height) {
  const edge = Math.min(1, width * .18, height * .18);
  // Keep tiny cells crisp; larger completed blocks get a softly raised face.
  if (width >= 5 && height >= 5) {
    const sheen = context.createLinearGradient(x, y, x, y + height);
    sheen.addColorStop(0, 'rgba(255,255,255,.045)');
    sheen.addColorStop(.45, 'rgba(255,255,255,0)');
    sheen.addColorStop(1, 'rgba(0,0,0,.045)');
    context.fillStyle = sheen;
    context.fillRect(x, y, width, height);
    context.fillStyle = 'rgba(255,255,255,.035)';
    context.fillRect(x + edge, y + edge, width - edge * 2, edge * 2);
    context.fillRect(x + edge, y + edge * 3, edge * 2, height - edge * 4);
  }
  context.fillStyle = 'rgba(255,255,255,.28)';
  context.fillRect(x, y, width, edge);
  context.fillRect(x, y + edge, edge, height - edge);
  context.fillStyle = 'rgba(0,0,0,.14)';
  context.fillRect(x + edge, y + height - edge, width - edge, edge);
  context.fillRect(x + width - edge, y + edge, edge, height - edge * 2);
}
function liftMapBlock(item) {
  if (liftedItem === item || !palette || !(item.w > 0 && item.h > 0)) return;
  liftedItem = item;
  liftAnimation?.cancel();
  mapLift.hidden = false;
  mapLift.classList.toggle('is-complete', item.matched === item.size);
  const growX = Math.min(3, Math.max(.6, item.w * .025));
  const growY = Math.min(3, Math.max(.6, item.h * .025));
  const transform = `scale(${1 + growX * 2 / item.w},${1 + growY * 2 / item.h})`;
  Object.assign(mapLift.style, {
    left: item.x + 'px', top: item.y + 'px', width: item.w + 'px', height: item.h + 'px',
    backgroundColor: colorValue(item),
    opacity: '1', transform
  });
  // Restart only on a new cell: its geometry never inherits the previous cell's scale.
  if (!motionPreference.matches) {
    liftAnimation = animate(mapLift, [
      {transform: 'scale(1)', opacity: .55}, {transform, opacity: 1}
    ], {duration: 150, easing: 'cubic-bezier(.22,1,.36,1)'});
  }
}
function drawMap(layout) {
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const scene = document.createElement('canvas');
  scene.className = 'map-pixels';
  scene.setAttribute('aria-hidden', 'true');
  scene.width = Math.round(canvas.clientWidth * ratio);
  scene.height = Math.round(canvas.clientHeight * ratio);
  rippleSurface = document.createElement('canvas');
  rippleSurface.className = 'map-ripple';
  rippleSurface.setAttribute('aria-hidden', 'true');
  rippleSurface.width = scene.width;
  rippleSurface.height = scene.height;
  const styles = getComputedStyle(canvas);
  const rgb = hex => [1, 3, 5].map(index => parseInt(hex.slice(index, index + 2), 16));
  palette = {empty: styles.getPropertyValue('--empty').trim(), done: styles.getPropertyValue('--map-color').trim()};
  palette.emptyRGB = rgb(palette.empty);
  palette.doneRGB = rgb(palette.done);
  const context = scene.getContext('2d');
  context.scale(ratio, ratio);
  // Transparent seams expose the ripple underneath; the opaque blocks are drawn only once.
  for (const item of layout) {
    context.fillStyle = colorValue(item);
    const inset = Math.min(0.6, item.w * 0.2, item.h * 0.2);
    const x = item.x + inset, y = item.y + inset;
    const width = item.w - inset * 2, height = item.h - inset * 2;
    context.fillRect(x, y, width, height);
    if (item.matched === item.size) drawCompletedFinish(context, x, y, width, height);
  }
  boundaryGraph = makeBoundaryGraph(layout);
  canvas.append(rippleSurface, scene);
}
function selectItem(item, block, event) {
  const origin = clickOrigin(event, block);
  hideTooltip();
  if (item.children?.length) {
    search.value = '';
    path.push(item);
    render('enter', origin);
    back.focus();
  } else {
    const rect = block.getBoundingClientRect();
    showTooltip(block, item, event?.detail ? event.clientX : rect.left, event?.detail ? event.clientY : rect.top);
    ripple(origin);
  }
}
function hitItem(event) {
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left, y = event.clientY - rect.top;
  return mapLayout.find(item => x >= item.x && x < item.x + item.w && y >= item.y && y < item.y + item.h);
}
function targetItem(item) {
  if (item.target) return item.target;
  if (hoverItem === item && hoverTarget) return hoverTarget;
  hoverItem = item;
  if (!hoverTarget) {
    hoverTarget = document.createElement('button');
    hoverTarget.type = 'button';
    hoverTarget.className = 'tile map-hit';
    mapListen(hoverTarget, 'blur', () => { if (activeTile === hoverTarget) hideTooltip(); });
    mapListen(hoverTarget, 'focus', () => {
      if (!hoverTarget.matches(':focus-visible')) return;
      const rect = hoverTarget.getBoundingClientRect();
      showTooltip(hoverTarget, hoverItem, rect.left, rect.top);
    });
    canvas.append(hoverTarget);
  }
  hoverTarget.dataset.name = item.name;
  hoverTarget.dataset.mapIndex = mapLayout.indexOf(item);
  hoverTarget.setAttribute('aria-label', item.name + ' · ' + percent(item));
  Object.assign(hoverTarget.style, {left: item.x + 'px', top: item.y + 'px', width: item.w + 'px', height: item.h + 'px'});
  return hoverTarget;
}
mapListen(canvas, 'pointermove', event => {
  if (event.pointerType === 'touch') return;
  hoverPoint = {clientX: event.clientX, clientY: event.clientY};
  if (hoverFrame !== null) return;
  hoverFrame = frame(() => {
    hoverFrame = null;
    const point = hoverPoint;
    const item = point && hitItem(point);
    if (item) showTooltip(targetItem(item), item, point.clientX, point.clientY);
    else hideTooltip();
  });
});
mapListen(canvas, 'keydown', event => {
  if (!['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
  event.preventDefault();
  const index = Number(event.target.dataset.mapIndex);
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? mapLayout.length - 1 :
    Math.max(0, Math.min(mapLayout.length - 1, index + (['ArrowRight', 'ArrowDown'].includes(event.key) ? 1 : -1)));
  if (mapLayout[next]) {
    const target = targetItem(mapLayout[next]);
    target.focus();
    const rect = target.getBoundingClientRect();
    showTooltip(target, mapLayout[next], rect.left, rect.top);
  }
});
mapListen(canvas, 'click', event => {
  const item = event.detail ? hitItem(event) : mapLayout[Number(event.target.dataset.mapIndex)];
  if (item) selectItem(item, targetItem(item), event);
});
mapListen(canvas, 'pointerleave', () => {
  hideTooltip();
  if (hoverTarget !== document.activeElement) {
    hoverTarget?.remove();
    hoverTarget = null;
  }
});
function render(direction = null, origin = null) {
  if (!mapEnabled) return;
  if (!sections.length) return;
  const continuing = activePulses.filter(pulse => performance.now() - pulse.start < pulse.duration)
    .map(pulse => ({origin: {x: pulse.origin.x / pulse.width * canvas.clientWidth,
      y: pulse.origin.y / pulse.height * canvas.clientHeight}, start: pulse.start}));
  clearMapMotion();
  const focusedIndex = !direction && canvas.contains(document.activeElement) ? Number(document.activeElement.dataset.mapIndex) : null;
  hideTooltip();
  const current = path.at(-1);
  const items = mapItems();
  back.hidden = !current;
  canvas.setAttribute('aria-description', 'Use arrow keys to move between blocks, Home or End to reach the first or last block, and Enter to select.');
  canvas.setAttribute('aria-label', current ? current.name + ' contents' : (mapKind === 'code' ? 'Code' : 'Data') + ' file map');
  const layout = [];
  partition(items, 0, 0, canvas.clientWidth, canvas.clientHeight, layout);
  canvas.replaceChildren();
  hoverTarget = null;
  hoverItem = null;
  rippleSurface = null;
  mapLayout = layout;
  if (!items.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-search';
    empty.textContent = 'No matches';
    canvas.append(empty);
    return;
  }
  drawMap(layout);
  // Pixel drawing keeps dense maps fast; larger cells and search results retain native keyboard targets.
  const targets = search.value.trim() ? layout.slice(0, 128) : layout.slice(0, 64);
  for (const [index, item] of targets.entries()) {
    const block = document.createElement('button');
    block.type = 'button';
    block.className = 'tile';
    block.dataset.name = item.name;
    block.dataset.mapIndex = index;
    Object.assign(block.style, {left: item.x + 'px', top: item.y + 'px', width: item.w + 'px', height: item.h + 'px'});
    block.setAttribute('aria-label', item.name + ' · ' + percent(item));
    item.target = block;
    mapListen(block, 'blur', () => { if (activeTile === block) hideTooltip(); });
    mapListen(block, 'focus', () => {
      if (!block.matches(':focus-visible')) return;
      const rect = block.getBoundingClientRect();
      showTooltip(block, item, rect.left, rect.top);
    });
    canvas.append(block);
    if (index === focusedIndex) block.focus();
  }
  if (focusedIndex !== null && focusedIndex >= targets.length && layout[focusedIndex]) targetItem(layout[focusedIndex]).focus();
  for (const pulse of continuing) ripple(pulse.origin, pulse.start);
  if (direction !== 'search') ripple(origin);
}
mapListen(back, 'click', event => {
  const origin = clickOrigin(event, back);
  const previous = path.pop();
  render('back', origin);
  const tile = [...canvas.children].find(block => block.dataset.name === previous?.name);
  tile?.focus();
});
listen(document, 'keydown', event => {
  if (event.key === 'Escape') hideTooltip();
});
mapListen(window, 'scroll', () => {
  hideTooltip();
  const focused = document.activeElement;
  if (!canvas.contains(focused) || !focused.matches(':focus-visible')) return;
  frame(() => {
    if (!canvas.contains(focused) || document.activeElement !== focused) return;
    const item = mapLayout[Number(focused.dataset.mapIndex)];
    const rect = focused.getBoundingClientRect();
    if (item && rect.bottom > 0 && rect.top < window.innerHeight) showTooltip(focused, item, rect.left, rect.top);
  });
}, {passive: true});
function validMap(items, kind = null) {
  return Array.isArray(items) && items.length > 0 && items.every(item => {
    if (!['code', 'data'].includes(item.kind) || (kind && item.kind !== kind) ||
        typeof item.name !== 'string' || !validMeasure({total: item.size, linked: item.linked, matched: item.matched, fuzzy: item.fuzzy})) return false;
    if (item.children) {
      if (!validMap(item.children, item.kind)) return false;
      for (const field of ['size', 'linked', 'matched', ...(item.fuzzy === undefined ? [] : ['fuzzy'])]) {
        if (Math.abs(item.children.reduce((sum, child) => sum + child[field], 0) - item[field]) > 1e-6) return false;
      }
    }
    return true;
  });
}
function renderCounts(functions, type, basis) {
  if (!root.querySelector('[data-stats="' + type + '"]')) return;
  const available = functions && functions.basis !== 'unavailable' && functions.total > 0;
  if (functions && functions.basis !== 'unavailable' && (functions.basis !== basis || !Number.isSafeInteger(functions.total) || functions.total < 0 || (type === 'function' && functions.total === 0) ||
      !['exact', 'named'].every(field => Number.isSafeInteger(functions[field]) && functions[field] >= 0 && functions[field] <= functions.total))) {
    throw new Error('Invalid function progress');
  }
  root.querySelector('[data-stats="' + type + '"] .stats-total span').textContent = available ? functions.total.toLocaleString() : '—';
  for (const field of ['exact', 'named']) {
    const stat = root.querySelector('[data-' + type + '="' + field + '"]');
    const value = available ? functions[field] / functions.total * 100 : 0;
    if (available) countUp(stat.querySelector('strong'), functions[field]);
    else stat.querySelector('strong').textContent = '—';
    const track = stat.querySelector('.function-track');
    fillTo(track.firstElementChild, value);
    if (available) {
      track.setAttribute('aria-valuenow', value);
      track.setAttribute('aria-valuetext', `${functions[field].toLocaleString()} of ${functions.total.toLocaleString()}`);
    } else {
      track.removeAttribute('aria-valuenow');
      track.setAttribute('aria-valuetext', 'Unavailable');
    }
  }
}

function validMeasure(m){return m&&Number.isSafeInteger(m.total)&&m.total>0&&Number.isSafeInteger(m.linked)&&m.linked>=0&&m.linked<=m.total&&Number.isSafeInteger(m.matched)&&m.matched>=0&&m.linked<=m.matched&&m.matched<=m.total&&(m.fuzzy===undefined||(Number.isFinite(m.fuzzy)&&m.matched<=m.fuzzy&&m.fuzzy<=m.total));}
async function loadProgress(){try{const response=await fetch(project.progressUrl,{cache:'no-cache',signal});if(!response.ok)throw new Error('Progress unavailable');const data=await response.json();if(signal.aborted)return;if(data.schema!==1||data.target!==project.target||data.basis!=='executable-sections'||data.baseline!==(project.preview?'preview':'verified')||!(/^[a-f0-9]{40}$/).test(data.revision)||!validMeasure(data.measures?.code)||!validMeasure(data.measures?.data)||!Array.isArray(data.sections)||!data.sections.length)throw new Error('Invalid progress');for(const item of data.sections){if(!['code','data'].includes(item.kind)||typeof item.name!=='string'||!/^0x[0-9A-F]{8}$/.test(item.address)||!validMeasure({total:item.size,linked:item.linked,matched:item.matched,fuzzy:item.fuzzy}))throw new Error('Invalid section');}for(const kind of ['code','data']){for(const field of ['total','linked','matched',...(data.measures[kind].fuzzy===undefined?[]:['fuzzy'])]){const sum=data.sections.filter(s=>s.kind===kind).reduce((n,s)=>n+s[field==='total'?'size':field],0);if(Math.abs(sum-data.measures[kind][field])>1e-6)throw new Error('Inconsistent progress');}}
const files=data.files || data.sections;
if(!validMap(data.sections)||!validMap(files))throw new Error('Invalid map');
for(const kind of ['code','data']){for(const field of ['total','linked','matched',...(data.measures[kind].fuzzy===undefined?[]:['fuzzy'])]){
  if(Math.abs(files.filter(item=>item.kind===kind).reduce((sum,item)=>sum+item[field==='total'?'size':field],0)-data.measures[kind][field])>1e-6)throw new Error('Inconsistent file map');
}}
renderCounts(data.functions, 'function', 'provisional-analysis');renderCounts(data.file_counts, 'file', 'mapped-file-inventory');sections=files;root.querySelectorAll('.progress-element').forEach(element => {
  const kind = element.dataset.progress;
  const measures = data.measures[kind];
  const linked = measures.linked / measures.total * 100;
  const matched = measures.matched / measures.total * 100;
  const fuzzy = (measures.fuzzy ?? measures.matched) / measures.total * 100;
  const track = element.querySelector('.track');
  const description = `${kind === 'code' ? 'Code' : 'Data'} · Linked ${linked.toFixed(2)}% · Matched ${matched.toFixed(2)}% · Fuzzy ${fuzzy.toFixed(2)}%`;
  countUp(element.querySelector('.progress-value'), matched, 2, '%');
  track.setAttribute('aria-valuenow', matched);
  track.setAttribute('aria-valuetext', `Linked ${linked.toFixed(2)}%, matched ${matched.toFixed(2)}%, fuzzy ${fuzzy.toFixed(2)}%`);
  fillTo(track.querySelector('.progress-linked'), linked);
  fillTo(track.querySelector('.progress-matched'), matched);
  fillTo(track.querySelector('.progress-fuzzy'), fuzzy);
  const strips = [
    {field: 'linked', label: 'Linked', value: linked},
    {field: 'matched', label: 'Matched', value: matched},
    {field: 'fuzzy', label: 'Fuzzy', value: fuzzy}
  ];
  const lift = document.createElement('div');
  lift.className = 'progress-hover';
  lift.setAttribute('aria-hidden', 'true');
  lift.hidden = true;
  track.append(lift);
  let liftedStrip = null, stripAnimation = null;
  function clearHover() {
    stripAnimation?.cancel();
    liftedStrip = null;
    lift.hidden = true;
    hideTooltip();
  }
  function hoverStrip(event) {
    const rect = track.getBoundingClientRect();
    const x = event.clientX - rect.left;
    let start = 0;
    for (const strip of strips) {
      const end = track.querySelector('i.progress-' + strip.field).getBoundingClientRect().width;
      if (x >= start && x < end) {
        if (liftedStrip !== strip.field || lift.style.width !== (end - start) + 'px') {
          stripAnimation?.cancel();
          liftedStrip = strip.field;
          lift.hidden = false;
          lift.className = 'progress-hover progress-' + strip.field;
          lift.style.left = start + 'px';
          lift.style.width = (end - start) + 'px';
          if (!motionPreference.matches) stripAnimation = animate(lift, [
            {transform: 'translateY(-50%) scale(1)', opacity: .5},
            {transform: 'translateY(-50%) scale(1.008,1.3)', opacity: 1}
          ], {duration: 160, easing: 'cubic-bezier(.22,1,.36,1)'});
        }
        showTooltipText(track, `${strip.label} ${strip.value.toFixed(2)}%`, event.clientX, event.clientY);
        return;
      }
      start = end;
    }
    clearHover();
  }
  listen(track, 'pointerenter', event => {
    if (event.pointerType !== 'touch') hoverStrip(event);
  });
  listen(track, 'pointermove', event => {
    if (event.pointerType !== 'touch') hoverStrip(event);
  });
  listen(track, 'pointerleave', clearHover);
  listen(window, 'resize', clearHover);
  listen(motionPreference, 'change', () => { if (motionPreference.matches) stripAnimation?.cancel(); });
  listen(window, 'scroll', clearHover, {passive: true});
  listen(track, 'focus', () => {
    if (!track.matches(':focus-visible')) return;
    const rect = track.getBoundingClientRect();
    showTooltipText(track, description, rect.left, rect.bottom);
  });
  listen(track, 'blur', clearHover);
  listen(track, 'click', hoverStrip);
});const link=buildLink;link.href=project.preview?project.repo:project.repo+'/commit/'+data.revision;link.textContent=project.preview?'View repository':'Baseline verified · '+data.revision.slice(0,7);link.title=project.preview?'View project on GitHub':'Built '+data.built_at;render();}catch(error){if(signal.aborted)return;renderCounts(null, 'function', 'provisional-analysis');renderCounts(null, 'file', 'mapped-file-inventory');buildLink.textContent='Progress unavailable';canvas.textContent='Progress unavailable';root.querySelectorAll('.track').forEach(track=>track.setAttribute('aria-valuetext','Unavailable'));}}
const observer = mapEnabled ? new ResizeObserver(() => { if (!signal.aborted) render(); }) : null;
observer?.observe(canvas);
const ready = loadProgress();
return {ready, destroy() { observer?.disconnect(); clearMapMotion(); scope.destroy(); }};

}
