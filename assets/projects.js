// Every game the data repository lists, with each active target's newest measurement
// (contract/README.md). Producers publish there directly; this page only reads.
import {withTarget} from './targets.js';

export const DATA = '/decomp-data/';

async function read(path) {
  const response = await fetch(DATA + path, {cache:'no-cache'});
  if (!response.ok) throw Error('Report data unavailable');
  return response.json();
}

async function load(slug) {
  const game = await read(`data/${slug}/game.json`);
  const base = `${DATA}data/${slug}/`;
  const reports = Object.fromEntries(await Promise.all(game.targets.map(async target => {
    if (target.status !== 'active') return [target.id, null];
    // One unreadable target leaves the rest of the game available.
    return [target.id, await read(`data/${slug}/${target.id}/latest.json`).catch(() => null)];
  })));
  return {
    ...game, base, reports, preview:false,
    href:`/games/${slug}/`, repo:`https://github.com/${game.repository}`,
    cover:game.artwork ? base + game.artwork.cover : null,
    coverWidth:game.artwork?.width, coverHeight:game.artwork?.height,
    contributeUrl:game.contributions?.guideUrl,
  };
}

const index = await read('index.json');
export const projects = (await Promise.all(index.games.map(slug => load(slug).catch(error => {
  console.error(slug, error);
  return null;
})))).filter(Boolean).map(project => withTarget(project, project.defaultTarget));
