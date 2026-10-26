// Explicit reader support: an unknown map version must not silently lose evidence.
export function assertMapCompatibility(map, identifier) {
  if (identifier === 'nfl-progress-v1' && map?.schema === 1 && map.schemaVersion === undefined) return;
  const versions = {'map-v1': 1, 'map-v2': 2};
  if (!Object.hasOwn(versions, identifier) || map?.schemaVersion !== versions[identifier]) {
    throw new Error('Unsupported map schema or mismatched version');
  }
}

export function mapLabel(item) {
  const prefix = item.source && !item.name.includes(item.source) ? item.source + ' · ' : '';
  const partial = item.source === item.name && item.complete === false ? ' · partial file' : '';
  return prefix + item.name + partial;
}

export function showMapDetails(panel, item) {
  if (!panel) return;
  const rows = [];
  if (item) {
    for (const [field, label] of [['source', 'Source'], ['comparison_source', 'Comparison source'],
      ['boundary', 'Boundary'], ['scope', 'Scope']]) {
      if (item[field] !== undefined) rows.push([label, item[field]]);
    }
    if (item.complete !== undefined) rows.push(['File extent', item.complete ? 'Complete' : 'Partial']);
    if (item.auto_generated === true) rows.push(['Generated placeholder', 'Yes']);
  }
  panel.hidden = !rows.length;
  const list = panel.querySelector('dl');
  list.replaceChildren();
  panel.querySelector('h3').textContent = item ? mapLabel(item) : '';
  for (const [label, value] of rows) {
    const term = document.createElement('dt'), description = document.createElement('dd');
    term.textContent = label;
    description.textContent = value;
    list.append(term, description);
  }
}
