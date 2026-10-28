import {pageScope} from '../../lifecycle.js';
import {createAction} from './action.js';
import {componentScope} from './scope.js';

const checkmark='<svg class="dropdown-check" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg>';

// One controller for every popover: selection, focus, dismissal and interruptible motion.
export function createDropdownController(trigger,menu,{scope=pageScope(),isSelected=option=>option.getAttribute('aria-checked')==='true',onSelect}={}) {
  const {listen,frame,animate,signal}=scope;
  const holder=trigger.parentElement;
  const motion=matchMedia('(prefers-reduced-motion: reduce)');
  let phase='closed',animation=null,version=0;
  const options=()=>[...menu.querySelectorAll('a,button')];
  menu.classList.add('shared-dropdown');menu.setAttribute('role','menu');
  trigger.setAttribute('aria-haspopup','menu');
  function sync(){
    const items=options();let tabStop=false;
    for(const item of items){
      item.classList.add('dropdown-option');item.setAttribute('role','menuitemradio');
      const selected=!!isSelected(item);item.setAttribute('aria-checked',String(selected));
      item.tabIndex=selected?0:-1;tabStop ||= selected;
      if(!item.querySelector('.dropdown-check'))item.insertAdjacentHTML('beforeend',checkmark);
    }
    if(!tabStop&&items.length)items[0].tabIndex=0;
  }
  function position(){
    menu.style.translate='0px 0px';menu.style.maxHeight='';
    const rect=menu.getBoundingClientRect();
    const shift=Math.min(0,window.innerWidth-16-rect.right)+Math.max(0,16-rect.left);
    menu.style.translate=shift+'px 0px';
    // Keep the menu inside a short viewport; it scrolls internally instead.
    const room=window.innerHeight-16-rect.top;
    if(rect.height>room){menu.style.maxHeight=Math.max(120,room)+'px';menu.style.overflowY='auto';}
    else menu.style.overflowY='';
  }
  function cancel(){animation?.cancel();animation=null;}
  function close(restoreFocus=false){
    if(restoreFocus||menu.contains(document.activeElement))trigger.focus({preventScroll:true});
    if(phase==='closed'||phase==='closing')return;
    const state=getComputedStyle(menu),from={opacity:state.opacity,transform:state.transform};
    const token=++version;cancel();phase='closing';trigger.setAttribute('aria-expanded','false');
    menu.inert=true;menu.setAttribute('aria-hidden','true');
    const finish=()=>{if(token===version){menu.hidden=true;phase='closed';cancel();}};
    if(motion.matches||signal.aborted){finish();return;}
    animation=animate(menu,[from,{opacity:0,transform:'translateY(-4px) scale(.98)'}],{duration:120,easing:'cubic-bezier(.4,0,1,1)',fill:'forwards'});
    animation.finished.then(finish,()=>{});
  }
  function open(last=false){
    if(signal.aborted)return;
    const wasVisible=!menu.hidden;
    const state=wasVisible?getComputedStyle(menu):null;
    const from=state?{opacity:state.opacity,transform:state.transform}:{opacity:0,transform:'translateY(-5px) scale(.98)'};
    ++version;cancel();
    document.dispatchEvent(new CustomEvent('portfolio-menu-open',{detail:trigger}));
    phase='open';menu.hidden=false;menu.inert=false;menu.removeAttribute('aria-hidden');trigger.setAttribute('aria-expanded','true');
    sync();position();
    if(!motion.matches)animation=animate(menu,[from,{opacity:1,transform:'none'}],{duration:160,easing:'cubic-bezier(.2,.75,.25,1)'});
    const items=options();(last?items.at(-1):items.find(item=>item.getAttribute('aria-checked')==='true')||items[0])?.focus();
  }
  listen(trigger,'click',()=>phase==='open'?close(true):open());
  listen(trigger,'keydown',event=>{
    if(['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();open(event.key==='ArrowUp');}
  });
  listen(holder,'keydown',event=>{
    if(event.key==='Escape'&&phase==='open'){event.preventDefault();close(true);return;}
    if(event.key===' '&&phase==='open'&&menu.contains(event.target)){
      const item=options().find(option=>option.contains(event.target));
      if(item?.tagName==='A'){event.preventDefault();item.click();return;}
    }
    if(event.key==='Tab'){frame(()=>{if(!holder.contains(document.activeElement))close();});return;}
    if(phase!=='open'||!menu.contains(event.target)||!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
    event.preventDefault();const items=options(),index=items.indexOf(document.activeElement);
    const next=event.key==='Home'?0:event.key==='End'?items.length-1:(index+(event.key==='ArrowDown'?1:-1)+items.length)%items.length;
    items.forEach((item,i)=>item.tabIndex=i===next?0:-1);items[next]?.focus();
  });
  listen(menu,'click',event=>{
    if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
    const option=options().find(item=>item.contains(event.target));if(!option)return;
    onSelect?.(option);sync();close(true);
  });
  listen(document,'pointerdown',event=>{if(!holder.contains(event.target))close();});
  listen(document,'portfolio-menu-open',event=>{if(event.detail!==trigger)close();});
  listen(window,'resize',()=>{if(phase==='open')position();});
  listen(motion,'change',()=>{if(motion.matches){++version;cancel();if(phase==='closing'){menu.hidden=true;phase='closed';}}});
  signal.addEventListener('abort',()=>{++version;cancel();menu.hidden=true;phase='closed';},{once:true});
  sync();menu.hidden=true;trigger.setAttribute('aria-expanded','false');
  return {open,close,sync,get isOpen(){return phase==='open';}};
}

/**
 * @typedef {Object} DropdownOption
 * @property {string} value
 * @property {string} label
 * @property {string=} description
 * @property {string=} href Navigation options keep normal link behavior.
 * @property {string=} image Site-owned artwork URL.
 * @property {string=} console Console icon name, rendered by the UI icon registry.
 * @property {string=} region Region flag; accessible text belongs in ariaLabel.
 * @property {string=} ariaLabel
 *
 * @typedef {Object} DropdownProps
 * @property {string} id
 * @property {string} label Accessible name of the choice list.
 * @property {DropdownOption[]} options
 * @property {string|null} value
 * @property {string=} className Wrapper style variant.
 * @property {string=} triggerClass
 * @property {string=} labelClass
 * @property {string=} menuClass
 * @property {string=} triggerLabel Optional label independent of the current option.
 * @property {string=} ariaLabel
 * @property {'filter'|'sort'=} icon Icon-only trigger variant.
 * @property {boolean=} selectedLeading Show the selected option's icon in the trigger.
 * @property {string=} defaultValue Show an active-filter dot when value differs.
 * @property {(option:DropdownOption)=>void=} onSelect
 * @property {ReturnType<typeof pageScope>=} scope Parent page lifetime; destroy() also disposes this instance independently.
 */

import {consoleIcon} from '../../console-icon.js';
const chevron='<svg class="switch-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg>';
const triggerIcons={
  filter:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M7 12h10m-7 5h4"/></svg>',
  sort:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 4v16m-4-4 4 4 4-4m3-10h5m-5 5h4m-4 5h3"/></svg>'
};
const flags={USA:'🇺🇸',US:'🇺🇸',Japan:'🇯🇵',JPN:'🇯🇵',JP:'🇯🇵',Europe:'🇪🇺',EUR:'🇪🇺',EU:'🇪🇺',Australia:'🇦🇺',AUS:'🇦🇺',AU:'🇦🇺',Korea:'🇰🇷',KOR:'🇰🇷',KR:'🇰🇷'};
function leading(parent,option){
  if(option.image){const image=document.createElement('img');image.src=option.image;image.alt='';parent.append(image);}
  else if(option.console)parent.insertAdjacentHTML('beforeend',consoleIcon(option.console));
  else if(flags[option.region]){const flag=document.createElement('span');flag.className='region-flag';flag.setAttribute('aria-hidden','true');flag.textContent=flags[option.region];parent.append(flag);}
}

/** Build the complete primitive before attaching it to a page. @param {DropdownProps} props */
export function createDropdown(props){
  const scope=componentScope(props.scope);
  const node=document.createElement('div');node.className='ui-dropdown '+(props.className||'');
  const trigger=createAction({id:props.id,className:'dropdown-trigger '+(props.triggerClass||'')});
  const menu=document.createElement('div');menu.id=props.id+'-menu';menu.className='hub-popover '+(props.menuClass||'');menu.hidden=true;menu.setAttribute('aria-label',props.label);
  trigger.setAttribute('aria-controls',menu.id);
  let value=props.value,label=props.triggerLabel,ariaLabel=props.ariaLabel;
  const choices=new Map();
  for(const option of props.options){
    if(choices.has(option.value))throw Error('Duplicate dropdown value: '+option.value);
    choices.set(option.value,option);
    const item=createAction({href:option.href,className:'popover-option'});item.dataset.value=option.value;
    if(option.ariaLabel)item.setAttribute('aria-label',option.ariaLabel);
    leading(item,option);
    const text=document.createElement('span');text.className='dropdown-option-text';text.textContent=option.label;
    if(option.description){const description=document.createElement('small');description.textContent=option.description;text.append(description);}
    item.append(text);menu.append(item);
  }
  node.append(trigger,menu);
  const control=createDropdownController(trigger,menu,{scope,
    isSelected:item=>item.dataset.value===value,
    onSelect:item=>{const option=choices.get(item.dataset.value);if(!option.href)setValue(option.value);props.onSelect?.(option);}});
  function renderTrigger(){
    const option=choices.get(value);trigger.replaceChildren();
    trigger.setAttribute('aria-label',ariaLabel||props.label+': '+(label||option?.label||''));
    if(props.icon){trigger.insertAdjacentHTML('beforeend',triggerIcons[props.icon]);}
    else{
      if(props.selectedLeading&&option)leading(trigger,option);
      const text=document.createElement('span');text.className='dropdown-trigger-label '+(props.labelClass||'');text.textContent=label??option?.label??props.label;
      trigger.append(text);trigger.insertAdjacentHTML('beforeend',chevron);
    }
    if(props.defaultValue!==undefined){const dot=document.createElement('i');dot.className='control-dot';dot.setAttribute('aria-hidden','true');trigger.append(dot);trigger.classList.toggle('has-selection',value!==props.defaultValue);}
  }
  function setValue(next,{triggerLabel,ariaLabel:nextAria}={}){
    value=next;if(triggerLabel!==undefined)label=triggerLabel;if(nextAria!==undefined)ariaLabel=nextAria;
    control.sync();renderTrigger();
  }
  function destroy(){scope.destroy();node.remove();}
  renderTrigger();
  return {node,trigger,menu,setValue,destroy,open:control.open,close:control.close,get isOpen(){return control.isOpen;}};
}
