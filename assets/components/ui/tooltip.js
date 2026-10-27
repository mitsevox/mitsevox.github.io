import {componentScope} from './scope.js';

/**
 * @typedef {Object} TooltipProps
 * @property {string} id
 * @property {'map'|'hub'=} variant Preserves each existing surface and placement.
 * @property {ReturnType<typeof import('../../lifecycle.js').pageScope>=} scope
 * @property {()=>void=} onHide Feature-specific visual cleanup, never report logic.
 *
 * @typedef {Object} TooltipContent
 * @property {HTMLElement} anchor
 * @property {string} label
 * @property {string=} value
 * @property {number} x
 * @property {number} y
 * @property {()=>void=} onHide Cleanup for the currently displayed interaction.
 */
/** @param {TooltipProps} props */
export function createTooltip({id,variant='map',scope:parent,onHide}) {
  const scope=componentScope(parent),node=document.createElement('div');
  node.id=id;node.className=variant==='map'?'map-tooltip':'hub-tooltip';node.setAttribute('role','tooltip');node.hidden=true;
  let anchor=null,cleanup=null,label=null,value=null,width=0,height=0;
  function describe(element,add){
    if(!element)return;
    const ids=new Set((element.getAttribute('aria-describedby')||'').split(/\s+/).filter(Boolean));
    if(add)ids.add(id);else ids.delete(id);
    if(ids.size)element.setAttribute('aria-describedby',[...ids].join(' '));else element.removeAttribute('aria-describedby');
  }
  function hide(){
    describe(anchor,false);anchor=null;node.hidden=true;
    const previous=cleanup;cleanup=null;previous?.();onHide?.();
  }
  /** @param {TooltipContent} content */
  function show(content){
    if(scope.signal.aborted)return;
    if(anchor!==content.anchor){hide();anchor=content.anchor;describe(anchor,true);}
    cleanup=content.onHide||null;
    const nextValue=content.value||'';
    if(node.hidden||label!==content.label||value!==nextValue){
      label=content.label;value=nextValue;
      if(variant==='hub')node.textContent=label;
      else{
        const name=document.createElement('span');name.className='tooltip-name';name.textContent=label+(value?' ':'');node.replaceChildren(name);
        if(value){const measure=document.createElement('span');measure.className='tooltip-value';measure.textContent=value;node.append(measure);}
      }
      node.hidden=false;width=node.offsetWidth;height=node.offsetHeight;
    }
    const gap=variant==='hub'?12:14,gutter=variant==='hub'?12:10;
    node.style.left=Math.max(gutter,Math.min(content.x+gap,innerWidth-width-gutter))+'px';
    node.style.top=(variant==='hub'?Math.max(gutter,content.y-height-gap):Math.max(gutter,Math.min(content.y+gap,innerHeight-height-gutter)))+'px';
  }
  scope.listen(document,'keydown',event=>{if(event.key==='Escape')hide();});
  scope.listen(window,'scroll',hide,{passive:true});scope.listen(window,'resize',hide);
  scope.signal.addEventListener('abort',hide,{once:true});
  return {node,show,hide,get anchor(){return anchor;},destroy(){scope.destroy();node.remove();}};
}
