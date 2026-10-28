import assert from 'node:assert/strict';
import {test} from 'node:test';
import {pageScope} from '../assets/lifecycle.js';
import {createProgressBar} from '../assets/components/ui/progress-bar.js';
import {createTooltip} from '../assets/components/ui/tooltip.js';
import {mountCodeBlock} from '../assets/components/ui/code-block.js';
import {createCommitLine} from '../assets/components/ui/commit-line.js';
import {createSegmentedControl} from '../assets/components/ui/segmented-control.js';
import {createCountSummary} from '../assets/components/ui/count-summary.js';

// Small DOM adapter: tests exercise state, ownership and cancellation; browser checks
// cover actual layout, native focus/keyboard behavior and the unchanged SVG artwork.
class Element extends EventTarget {
  constructor(tag='div'){super();this.tagName=tag.toUpperCase();this.children=[];this.attrs={};this.style={};this.dataset={};this.hidden=false;this._text='';}
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(n=>n.textContent).join('');}
  set innerHTML(value){assert.equal(this.tagName,'TEMPLATE');this.content={firstElementChild:new Element('svg')};}
  setAttribute(name,value){this.attrs[name]=String(value);}
  getAttribute(name){return this.attrs[name]??null;}
  removeAttribute(name){delete this.attrs[name];}
  append(...nodes){for(const node of nodes){node.parentElement=this;this.children.push(node);}}
  replaceChildren(...nodes){this.children=[];this._text='';this.append(...nodes);}
  before(node){const parent=this.parentElement;parent.children.splice(parent.children.indexOf(this),0,node);node.parentElement=parent;}
  remove(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(n=>n!==this);}
  matches(selector){return selector===':focus-visible'?true:selector.split('.').every((part,i)=>i===0?(part?this.tagName.toLowerCase()===part:true):this.className?.split(' ').includes(part));}
  querySelectorAll(selector){return this.children.flatMap(n=>[...(n.matches(selector)?[n]:[]),...n.querySelectorAll(selector)]);}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  getBoundingClientRect(){const width=this.tagName==='I'?parseFloat(this.style.width)||0:100;return {left:0,top:0,bottom:22,width,height:22};}
  get offsetWidth(){return 120;}
  get offsetHeight(){return 24;}
  emit(type,fields={}){const event=new Event(type);for(const [key,value] of Object.entries(fields))Object.defineProperty(event,key,{value});this.dispatchEvent(event);}
}
function fixture(reduced=true){
  globalThis.document=new Element();document.createElement=tag=>new Element(tag);document.createTextNode=text=>{const node=new Element('#text');node.textContent=text;return node;};
  globalThis.window=new Element();globalThis.innerWidth=1000;globalThis.innerHeight=800;
  const frames=new Map();let frameId=0;
  window.requestAnimationFrame=callback=>{frames.set(++frameId,callback);return frameId;};window.cancelAnimationFrame=id=>frames.delete(id);
  const media=new Element();media.matches=reduced;globalThis.matchMedia=()=>media;
  const animations=[];Element.prototype.animate=function(){const animation={cancelled:false,finished:Promise.resolve(),cancel(){this.cancelled=true;}};animations.push(animation);return animation;};
  const scope=pageScope(),tooltip=createTooltip({id:'tip',scope});
  const flush=()=>{for(let i=0;frames.size&&i<8;i++){const pending=[...frames];frames.clear();for(const [,callback] of pending)callback(performance.now()+1000);}};
  return {scope,tooltip,frames,flush,animations};
}
const measure={total:100,linked:20,matched:40,fuzzy:60};

test('page and compact bars share values while preserving legend and keyboard variants',()=>{
  const f=fixture();
  const page=createProgressBar({kind:'code',scope:f.scope,tooltip:f.tooltip});
  const card=createProgressBar({kind:'data',variant:'compact',scope:f.scope,tooltip:f.tooltip});
  page.update(measure);card.update(measure);
  assert.equal(page.matched,card.matched);assert.equal(page.track.getAttribute('aria-valuenow'),'40');assert.equal(page.track.tabIndex,0);assert.equal(card.track.tabIndex,undefined);
  assert.ok(page.node.querySelector('.progress-key'));assert.equal(card.node.querySelector('.progress-key'),null);
  page.update({total:100,linked:0,matched:0});assert.equal(page.track.querySelector('.progress-fuzzy').hidden,true);assert.equal(page.node.querySelector('.fuzzy-key').parentElement.hidden,true);
  page.update({...measure,total:0});assert.equal(page.track.getAttribute('aria-valuenow'),null);assert.equal(page.track.getAttribute('aria-valuetext'),'Unavailable');
  f.scope.destroy();
});

test('unavailable state invalidates queued fills and counts rather than restoring stale progress',()=>{
  const f=fixture(false),bar=createProgressBar({kind:'code',scope:f.scope,tooltip:f.tooltip});
  bar.update(measure);bar.unavailable();f.flush();
  assert.equal(bar.track.querySelector('.progress-linked').style.width,'0%');assert.equal(bar.node.querySelector('.progress-value').textContent,'—');
  bar.update(measure);f.scope.destroy();const departed=bar.node.querySelector('.progress-value').textContent;bar.update({...measure,matched:90});bar.unavailable();assert.equal(bar.node.querySelector('.progress-value').textContent,departed);assert.equal(f.frames.size,0);f.flush();assert.equal(bar.track.querySelector('.progress-linked').style.width,'0%');
});

test('shared tooltip transfers ownership, dismisses old lifts and preserves unrelated descriptions',()=>{
  const f=fixture(),one=createProgressBar({kind:'code',scope:f.scope,tooltip:f.tooltip}),two=createProgressBar({kind:'data',scope:f.scope,tooltip:f.tooltip});
  one.update(measure);two.update(measure);one.track.setAttribute('aria-describedby','existing');
  one.track.emit('pointermove',{clientX:10,clientY:10,pointerType:'mouse'});
  assert.equal(one.node.querySelector('.progress-hover').hidden,false);assert.equal(one.track.getAttribute('aria-describedby'),'existing tip');
  two.track.emit('pointermove',{clientX:30,clientY:10,pointerType:'mouse'});
  assert.equal(one.node.querySelector('.progress-hover').hidden,true);assert.equal(one.track.getAttribute('aria-describedby'),'existing');assert.equal(f.tooltip.node.textContent,'Matched 40.00%');
  document.emit('keydown',{key:'Escape'});assert.equal(f.tooltip.node.hidden,true);assert.equal(two.track.getAttribute('aria-describedby'),null);
  two.track.emit('pointermove',{clientX:10,clientY:10,pointerType:'touch'});assert.equal(f.tooltip.node.hidden,true);
  f.scope.destroy();
});

test('copy completion cannot update a code block after its page has been destroyed',async()=>{
  const f=fixture(),holder=new Element(),pre=new Element('pre'),code=new Element('code');code.textContent='\nexample\n';pre.append(code);holder.append(pre);let resolve,copied;
  const block=mountCodeBlock({pre,scope:f.scope,writeText:text=>{copied=text;return new Promise(done=>resolve=done);}});
  block.button.emit('click');assert.equal(copied,'example');f.scope.destroy();resolve();await Promise.resolve();
  assert.equal(block.button.textContent,'Copy');
});

test('copy failure retains an accessible manual-copy fallback',async()=>{
  const f=fixture(),holder=new Element(),pre=new Element('pre'),code=new Element('code');code.textContent='example';pre.append(code);holder.append(pre);
  const block=mountCodeBlock({pre,scope:f.scope,writeText:async()=>{throw Error('denied');}});
  block.button.emit('click');await Promise.resolve();assert.equal(block.button.textContent,'Select to copy');assert.match(block.button.getAttribute('aria-label'),/Clipboard unavailable/);f.scope.destroy();
});

test('both commit variants share time formatting; invalid dates and route cleanup stop timers',()=>{
  const f=fixture(),oldSet=globalThis.setInterval,oldClear=globalThis.clearInterval,timers=new Set();let id=0;
  globalThis.setInterval=()=>{timers.add(++id);return id;};globalThis.clearInterval=id=>timers.delete(id);
  try{
    const page=createCommitLine({repository:'https://github.com/owner/game',scope:f.scope}),card=createCommitLine({repository:'https://github.com/owner/game',variant:'compact',scope:f.scope});
    const commit={title:'Change',date:new Date(Date.now()-3600000).toISOString(),url:'https://github.com/owner/game/commit/abc'};page.update(commit);card.update(commit);
    assert.equal(page.node.querySelector('time').textContent,card.node.querySelector('time').textContent);assert.equal(timers.size,2);
    page.update({title:'Bad date',date:'invalid',url:'https://foreign.test/commit/abc'});assert.equal(page.date,null);assert.equal(page.node.href,'https://github.com/owner/game');assert.equal(timers.size,1);
    f.scope.destroy();assert.equal(timers.size,0);
  }finally{globalThis.setInterval=oldSet;globalThis.clearInterval=oldClear;}
});

test('segmented selection is synchronized without invoking view callbacks on programmatic updates',()=>{
  const f=fixture(),calls=[],control=createSegmentedControl({id:'kind',label:'Map type',value:'code',options:[{value:'code',label:'Code'},{value:'data',label:'Data'}],scope:f.scope,onChange:value=>calls.push(value)});
  control.setValue('data');assert.equal(control.node.children[1].getAttribute('aria-pressed'),'true');assert.deepEqual(calls,[]);
  control.node.children[0].emit('click');assert.deepEqual(calls,['code']);assert.equal(control.node.dataset.selected,'code');f.scope.destroy();control.node.children[1].emit('click');assert.deepEqual(calls,['code']);
});

test('count inventories expose unavailable instead of a misleading zero and cancel on cleanup',()=>{
  const f=fixture(),counts=createCountSummary({kind:'file',scope:f.scope});counts.update({total:10,exact:2,named:3});
  assert.equal(counts.node.querySelector('strong').textContent,'2');assert.equal(counts.node.querySelector('.function-track').getAttribute('aria-valuetext'),'2 of 10');
  counts.update(null);assert.equal(counts.node.querySelector('strong').textContent,'—');assert.equal(counts.node.querySelector('.function-track').getAttribute('aria-valuenow'),null);f.scope.destroy();counts.update({total:10,exact:10,named:10});assert.equal(counts.node.querySelector('strong').textContent,'—');
});
