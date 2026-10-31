import {componentScope} from './scope.js';

/**
 * @typedef {Object} ExpandableRegionProps
 * @property {string} id
 * @property {string} label
 * @property {number=} duration
 * @property {ReturnType<typeof import('../../lifecycle.js').pageScope>=} scope
 */
/** Layout motion in both directions; content retains natural height after settling.
 * @param {ExpandableRegionProps} props */
export function createExpandableRegion({id,label,duration=320,scope:parent}){
  const scope=componentScope(parent),motion=matchMedia('(prefers-reduced-motion: reduce)');
  const node=document.createElement('div');node.id=id;node.className='expandable-region';node.hidden=true;node.inert=true;node.setAttribute('role','region');node.setAttribute('aria-label',label);
  const content=document.createElement('div');content.className='expandable-content';node.append(content);
  let expanded=false,animation=null,version=0;
  function settle(){node.hidden=!expanded;node.inert=!expanded;node.style.height=expanded?'auto':'0px';node.style.opacity=expanded?'1':'0';}
  function transition(from,to){
    const current=++version;animation?.cancel();animation=null;node.style.height=to+'px';
    if(motion.matches||from===to){settle();return;}
    animation=scope.animate(node,[{height:from+'px',opacity:from===0?0:1},{height:to+'px',opacity:to===0?0:1}],{duration:expanded?duration:240,easing:'cubic-bezier(.22,1,.36,1)'});
    animation.finished.then(()=>{if(current===version&&!scope.signal.aborted){animation=null;settle();}},()=>{});
  }
  function setExpanded(value){
    if(scope.signal.aborted||value===expanded)return;
    const from=node.hidden?0:node.getBoundingClientRect().height;expanded=value;node.hidden=false;node.inert=!value;
    transition(from,value?content.getBoundingClientRect().height:0);
  }
  function resize(update){
    if(scope.signal.aborted)return;
    const from=node.hidden?0:node.getBoundingClientRect().height;update();
    if(expanded)transition(from,content.getBoundingClientRect().height);
  }
  scope.listen(motion,'change',()=>{if(motion.matches){++version;animation?.cancel();animation=null;settle();}});
  return {node,content,setExpanded,resize,get expanded(){return expanded;},destroy(){++version;animation?.cancel();scope.destroy();node.remove();}};
}
