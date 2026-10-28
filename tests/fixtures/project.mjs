// A schema-1 target as the data layer hands it to the page (contract/README.md).
import fs from 'node:fs';

const read = name => JSON.parse(fs.readFileSync(new URL(name, import.meta.url)));
export const map = read('map.json');
export const latest = read('latest.json');
// The page keys each file's URL by the digest latest.json gives it.
export const version = '?v=' + latest.digests['map.json'];

export function project(reportBase = '/one/', report = latest) {
  return {target:'TEST', targetSha1:'a'.repeat(40), reportBase, report,
    modules:{map:true, timeline:true, contributors:true, functionCounts:false, fileCounts:false}};
}

export function withSummary(changes) {
  return {...latest, summary:{...latest.summary, ...changes}};
}
