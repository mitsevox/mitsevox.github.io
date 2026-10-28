import {makeBoundaryGraph, packBoundaryGraph} from './map-geometry.js';
import {validateMap} from './report-map-validation.js';

self.onmessage = async ({data:{id, url, measures, layout}}) => {
  try {
    if (layout) {
      const graph=packBoundaryGraph(makeBoundaryGraph(layout));
      self.postMessage({id, graph},Object.values(graph).map(array=>array.buffer));return;
    }
    const response = await fetch(url, {cache:'force-cache'});
    if (!response.ok) throw Error('Report unavailable');
    const map = validateMap(await response.json(), measures);
    self.postMessage({id, map});
  } catch (error) {
    self.postMessage({id, error:error.message});
  }
};
