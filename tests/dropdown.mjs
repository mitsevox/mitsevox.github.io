import assert from 'node:assert/strict';
import {test} from 'node:test';
import {createDropdownController as createDropdown} from '../assets/components/ui/dropdown.js';

class Node {
  constructor(tag='div'){this.tag=tag;this.attrs={};this.children=[];this.listeners={};this.style={};this.hidden=false;this.classList={add:()=>{}};}
  append(...items){for(const item of items){item.parentElement=this;this.children.push(item);}}
  setAttribute(key,value){this.attrs[key]=value;}
  getAttribute(key){return this.attrs[key]??null;}
  removeAttribute(key){delete this.attrs[key];}
  contains(node){return this===node||this.children.some(child=>child.contains(node));}
  querySelectorAll(){return this.children.flatMap(child=>['a','button'].includes(child.tag)?[child]:child.querySelectorAll());}
  querySelector(){return this.hasCheck?{}:null;}
  insertAdjacentHTML(){this.hasCheck=true;}
  getBoundingClientRect(){return {left:10,right:110};}
  focus(){document.activeElement=this;}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
  dispatchEvent(event){for(const fn of this.listeners[event.type]||[])fn(event);}
  emit(type,updates={}){this.dispatchEvent({type,target:this,button:0,preventDefault(){this.defaultPrevented=true;},...updates});}
}
function fixture(reduced=false){
  globalThis.document=new Node();globalThis.window=new Node();window.innerWidth=1000;
  globalThis.getComputedStyle=()=>({opacity:'1',transform:'none'});
  const motion=new Node();motion.matches=reduced;globalThis.matchMedia=()=>motion;
  const holder=new Node(),trigger=new Node('button'),menu=new Node(),a=new Node('a'),b=new Node('a');
  menu.hidden=true;a.setAttribute('aria-checked','true');menu.append(a,b);holder.append(trigger,menu);
  const animations=[];const controller=new AbortController();
  const scope={signal:controller.signal,listen:(node,type,fn)=>node.addEventListener(type,fn),frame:fn=>fn(),
    animate:()=>{let done;const animation={cancelled:false,finished:new Promise(resolve=>done=resolve),finish:()=>done(),cancel(){this.cancelled=true;}};animations.push(animation);return animation;}};
  const dropdown=createDropdown(trigger,menu,{scope});return {dropdown,trigger,menu,a,b,animations,controller,holder,motion};
}

test('every option gets the shared mark and selection/focus follows the current value',()=>{
  const f=fixture();assert.ok(f.a.hasCheck&&f.b.hasCheck);f.dropdown.open();
  assert.equal(f.trigger.getAttribute('aria-expanded'),'true');assert.equal(document.activeElement,f.a);
  f.holder.emit('keydown',{target:f.a,key:'ArrowDown'});assert.equal(document.activeElement,f.b);
  f.holder.emit('keydown',{target:f.b,key:'Escape'});assert.equal(document.activeElement,f.trigger);assert.equal(f.menu.inert,true);
});

test('close animates before hiding and releases its filled animation',async()=>{
  const f=fixture();f.dropdown.open();f.dropdown.close();const out=f.animations.at(-1);
  assert.equal(f.menu.hidden,false);assert.equal(f.trigger.getAttribute('aria-expanded'),'false');
  out.finish();await Promise.resolve();assert.equal(f.menu.hidden,true);assert.equal(out.cancelled,true);
  f.dropdown.open();assert.equal(f.menu.hidden,false);assert.equal(f.menu.inert,false);
});

test('a rapid reopen cannot be hidden by the previous close completion',async()=>{
  const f=fixture();f.dropdown.open();f.dropdown.close();const previous=f.animations.at(-1);
  f.dropdown.open();previous.finish();await Promise.resolve();assert.equal(f.menu.hidden,false);assert.equal(f.dropdown.isOpen,true);
});

test('reduced motion closes immediately and route cleanup cancels pending motion',async()=>{
  const f=fixture(true);f.dropdown.open();f.dropdown.close();assert.equal(f.menu.hidden,true);assert.equal(f.animations.length,0);
  const next=fixture();next.dropdown.open();next.dropdown.close();next.controller.abort();
  next.animations.at(-1).finish();await Promise.resolve();assert.equal(next.menu.hidden,true);
});
