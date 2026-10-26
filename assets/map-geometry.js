export function makeBoundaryGraph(layout) {
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

// Circular graph objects can overflow WebKit's structured-clone stack on dense
// maps. Transfer flat typed buffers, then reconnect references iteratively.
export function packBoundaryGraph(nodes) {
  const indices=new Map(nodes.map((node,index)=>[node,index]));
  const points=new Float64Array(nodes.length*2), offsets=new Uint32Array(nodes.length+1);
  const edgeCount=nodes.reduce((sum,node)=>sum+node.edges.length,0);
  const neighbors=new Uint32Array(edgeCount), lengths=new Float64Array(edgeCount);
  let edge=0;
  nodes.forEach((node,index)=>{
    points[index*2]=node.x;points[index*2+1]=node.y;offsets[index]=edge;
    for(const link of node.edges){neighbors[edge]=indices.get(link.node);lengths[edge++]=link.length;}
  });
  offsets[nodes.length]=edge;
  return {points,offsets,neighbors,lengths};
}
export async function unpackBoundaryGraph({points,offsets,neighbors,lengths}) {
  const nodes=Array.from({length:points.length/2},(_,index)=>({x:points[index*2],y:points[index*2+1],edges:[]}));
  for(let index=0;index<nodes.length;index++){
    if(index&&index%2048===0)await new Promise(resolve=>setTimeout(resolve,0));
    for(let edge=offsets[index];edge<offsets[index+1];edge++)nodes[index].edges.push({node:nodes[neighbors[edge]],length:lengths[edge]});
  }
  return nodes;
}
