/** Shared number/fill motion; all frames belong to the supplied component scope. */
export function createValueMotion(scope,motion=matchMedia('(prefers-reduced-motion: reduce)')) {
  const counts=new WeakMap(),fills=new WeakMap();
  function cancelNumber(node){const previous=counts.get(node);if(previous!==undefined)scope.cancelFrame(previous);counts.delete(node);}
  function number(node,value,decimals=0,suffix='') {
    cancelNumber(node);
    const format=n=>decimals?n.toFixed(decimals)+suffix:Math.round(n).toLocaleString()+suffix;
    if(motion.matches){node.textContent=format(value);return;}
    const start=performance.now();
    function step(now){
      const t=motion.matches?1:Math.max(0,Math.min((now-start)/780,1));
      node.textContent=format(value*(1-Math.pow(1-t,3)));
      if(t<1)counts.set(node,scope.frame(step));else counts.delete(node);
    }
    node.textContent=format(0);counts.set(node,scope.frame(step));
  }
  function fill(node,value,immediate=false){
    const version=(fills.get(node)||0)+1;fills.set(node,version);
    const apply=()=>{if(fills.get(node)===version)node.style.width=value+'%';};
    if(motion.matches||immediate)apply();else scope.frame(()=>scope.frame(apply));
  }
  return {number,fill,cancelNumber};
}
