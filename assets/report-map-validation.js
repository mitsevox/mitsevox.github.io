import {assertMapCompatibility} from './map-evidence.js';

export function validMeasure(m) {
  return m && Number.isSafeInteger(m.total) && m.total >= 0 &&
    Number.isSafeInteger(m.linked) && m.linked >= 0 && m.linked <= m.total &&
    Number.isSafeInteger(m.matched) && m.matched >= 0 && m.matched <= m.total &&
    (m.fuzzy === undefined || (Number.isFinite(m.fuzzy) && m.matched <= m.fuzzy && m.fuzzy <= m.total));
}
function validMap(items, kind = null) {
  return Array.isArray(items) && items.length > 0 && items.every(item => {
    if (!(item.size > 0) || !['code', 'data'].includes(item.kind) || (kind && item.kind !== kind) ||
        typeof item.name !== 'string' || !validMeasure({total:item.size, linked:item.linked, matched:item.matched, fuzzy:item.fuzzy})) return false;
    if (item.children) {
      if (!validMap(item.children, item.kind)) return false;
      for (const field of ['size', 'linked', 'matched', ...(item.fuzzy === undefined ? [] : ['fuzzy'])]) {
        if (Math.abs(item.children.reduce((sum, child) => sum + child[field], 0) - item[field]) > 1e-6) return false;
      }
    }
    return true;
  });
}
export function validateMap(map, measures) {
  assertMapCompatibility(map);
  const files = map.files || map.sections;
  if (!validMap(map.sections) || !validMap(files)) throw Error('Invalid map');
  for (const items of [map.sections, files]) for (const kind of ['code', 'data']) {
    if (!validMeasure(measures[kind])) throw Error('Invalid progress');
    const roots = items.filter(item => item.kind === kind);
    for (const field of ['total', 'linked', 'matched', ...(measures[kind].fuzzy === undefined ? [] : ['fuzzy'])]) {
      if (Math.abs(roots.reduce((sum, item) => sum + item[field === 'total' ? 'size' : field], 0) - measures[kind][field]) > 1e-6) {
        throw Error('Inconsistent map');
      }
    }
  }
  return {sections:map.sections, files};
}
