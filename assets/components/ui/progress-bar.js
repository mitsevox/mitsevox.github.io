import {componentScope} from './scope.js';
import {createValueMotion} from './motion.js';

/**
 * @typedef {Object} ProgressBarProps
 * @property {'code'|'data'} kind
 * @property {'page'|'compact'=} variant Compact bars intentionally have no legend/tab stop.
 * @property {string=} ariaLabel
 * @property {ReturnType<typeof import('./tooltip.js').createTooltip>} tooltip
 * @property {ReturnType<typeof import('../../lifecycle.js').pageScope>=} scope
 *
 * @typedef {{total:number,linked:number,matched:number,fuzzy?:number}} ProgressMeasure
 */
/** Owns bar markup, optional legend, values, hover lift and keyboard tooltip. @param {ProgressBarProps} props */
export function createProgressBar({kind,variant='page',ariaLabel,tooltip,scope:parent}) {
  const scope=componentScope(parent),motion=matchMedia('(prefers-reduced-motion: reduce)'),valuesMotion=createValueMotion(scope,motion);
  const compact=variant==='compact',label=kind==='code'?'Code':'Data';
  const node=document.createElement('div');node.className=(compact?'card-measure ':'')+'progress-element';node.dataset.progress=kind;
  const heading=document.createElement('div');heading.className=compact?'card-measure-label':'progress-heading';
  const title=document.createElement(compact?'span':'h2');title.textContent=label;
  const value=document.createElement(compact?'strong':'span');if(!compact)value.className='progress-value';value.textContent='—';heading.append(title,value);
  const track=document.createElement('div');track.className=compact?'card-track':'track';track.setAttribute('role','progressbar');track.setAttribute('aria-label',ariaLabel||label+' progress');track.setAttribute('aria-valuemin','0');track.setAttribute('aria-valuemax','100');track.setAttribute('aria-valuetext','Loading');if(!compact)track.tabIndex=0;
  const fills={};for(const field of ['fuzzy','matched','linked']){const fill=document.createElement('i');fill.className='progress-'+field;fills[field]=fill;track.append(fill);}
  node.append(heading,track);
  let fuzzyKey;
  if(!compact){
    const legend=document.createElement('div');legend.className='progress-key';legend.setAttribute('aria-hidden','true');
    for(const field of ['linked','matched','fuzzy']){const entry=document.createElement('span'),swatch=document.createElement('i');swatch.className=field+'-key';entry.append(swatch,document.createTextNode(field[0].toUpperCase()+field.slice(1)));legend.append(entry);if(field==='fuzzy')fuzzyKey=entry;}
    node.append(legend);
  }
  const lift=document.createElement('div');lift.className='progress-hover';lift.hidden=true;lift.setAttribute('aria-hidden','true');track.append(lift);
  let values={},available=false,lifted=null,animation=null;
  function clearLift(){animation?.cancel();animation=null;lifted=null;lift.hidden=true;}
  function dismiss(){if(tooltip.anchor===track)tooltip.hide();else clearLift();}
  function description(){return Object.entries(values).map(([field,n])=>field[0].toUpperCase()+field.slice(1)+' '+n.toFixed(2)+'%').join(' · ');}
  function hover(event){
    if(event.pointerType==='touch'||!available)return;
    const x=event.clientX-track.getBoundingClientRect().left;let start=0;
    for(const field of Object.keys(values)){
      const end=fills[field].getBoundingClientRect().width;
      if(x>=start&&x<end){
        tooltip.show({anchor:track,label:field[0].toUpperCase()+field.slice(1)+' '+values[field].toFixed(2)+'%',x:event.clientX,y:event.clientY,onHide:clearLift});
        if(lifted!==field||lift.style.width!==(end-start)+'px'){
          animation?.cancel();lifted=field;lift.hidden=false;lift.className='progress-hover progress-'+field;lift.style.left=start+'px';lift.style.width=(end-start)+'px';
          if(!motion.matches)animation=scope.animate(lift,[{transform:'translateY(-50%) scale(1)',opacity:.5},{transform:'translateY(-50%) scale(1.008,1.3)',opacity:1}],{duration:160,easing:'cubic-bezier(.22,1,.36,1)'});
        }
        return;
      }
      start=Math.max(start,end);
    }
    dismiss();
  }
  scope.listen(track,'pointerenter',hover);scope.listen(track,'pointermove',hover);scope.listen(track,'pointerleave',dismiss);
  scope.listen(motion,'change',()=>{if(motion.matches)animation?.cancel();});
  if(!compact){
    scope.listen(track,'focus',()=>{if(!track.matches(':focus-visible'))return;const rect=track.getBoundingClientRect();tooltip.show({anchor:track,label:available?label+' · '+description():label+' unavailable',x:rect.left,y:rect.bottom,onHide:clearLift});});
    scope.listen(track,'blur',dismiss);scope.listen(track,'click',hover);
  }
  scope.signal.addEventListener('abort',dismiss,{once:true});
  /** Values must come from the page's validated summary. @param {ProgressMeasure} measure */
  function update(measure){
    if(scope.signal.aborted)return;
    dismiss();available=measure.total>0;
    values={linked:available?measure.linked/measure.total*100:0,matched:available?measure.matched/measure.total*100:0,...(measure.fuzzy===undefined?{}:{fuzzy:available?measure.fuzzy/measure.total*100:0})};
    fills.fuzzy.hidden=measure.fuzzy===undefined;if(fuzzyKey)fuzzyKey.hidden=measure.fuzzy===undefined;
    valuesMotion.cancelNumber(value);
    if(available){if(compact)value.textContent=values.matched.toFixed(2)+'%';else valuesMotion.number(value,values.matched,2,'%');track.setAttribute('aria-valuenow',values.matched);}
    else{value.textContent='Unavailable';track.removeAttribute('aria-valuenow');}
    track.setAttribute('aria-valuetext',available?Object.entries(values).map(([key,n],i)=>`${!compact&&i===0?'Linked':key} ${n.toFixed(2)}%`).join(', '):'Unavailable');
    for(const field of Object.keys(values))valuesMotion.fill(fills[field],values[field]);
  }
  function unavailable(){if(scope.signal.aborted)return;dismiss();available=false;values={};valuesMotion.cancelNumber(value);value.textContent=compact?'Unavailable':'—';track.removeAttribute('aria-valuenow');track.setAttribute('aria-valuetext',compact?'Progress unavailable':'Unavailable');for(const fill of Object.values(fills))valuesMotion.fill(fill,0,true);}
  return {node,track,update,unavailable,get matched(){return available?values.matched:null;},destroy(){scope.destroy();node.remove();}};
}
