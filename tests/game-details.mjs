import assert from 'node:assert/strict';
import {test} from 'node:test';
import {gameEditorial} from '../assets/game-editorial.js';
import {createGameDossier} from '../assets/components/ui/game-dossier.js';
import {createExpandableRegion} from '../assets/components/ui/expandable-region.js';
import {pageScope} from '../assets/lifecycle.js';

// State/lifetime adapter; actual geometry, glyphs and responsive layout are checked in browser.
class Element extends EventTarget {
  constructor(tag='div') {super();this.tagName=tag.toUpperCase();this.children=[];this.attrs={};this.style={};this.dataset={};this._text='';this.hidden=false;this.offsetWidth=100;this.offsetLeft=0;this.className='';this.classList={add:value=>this.className+=' '+value,remove:value=>this.className=this.className.split(' ').filter(c=>c!==value).join(' ')};}
  set textContent(value){this.children=[];this._text=String(value);}
  get textContent(){return this._text+this.children.map(n=>n.textContent).join('');}
  set innerHTML(value){this.html=value;if(this.tagName==='TEMPLATE')this.content={firstElementChild:new Element('svg')};}
  setAttribute(name,value){this.attrs[name]=String(value);}
  getAttribute(name){return this.attrs[name]??null;}
  append(...nodes){for(const node of nodes){node.remove();node.parentElement=this;this.children.push(node);}}
  prepend(...nodes){for(const node of nodes.reverse()){node.remove();node.parentElement=this;this.children.unshift(node);}}
  insertAdjacentHTML(position,html){const svg=new Element('svg');svg.html=html;position==='afterbegin'?this.prepend(svg):this.append(svg);}
  remove(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(n=>n!==this);this.parentElement=null;}
  querySelectorAll(selector){return this.children.flatMap(n=>[...(selector[0]==='.'?n.className.split(' ').includes(selector.slice(1)):n.tagName.toLowerCase()===selector)?[n]:[],...n.querySelectorAll(selector)]);}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  contains(node){return node===this||this.children.some(child=>child.contains(node));}
  getBoundingClientRect(){return {height:this.hidden?0:100};}
  focus(){document.activeElement=this;}
  emit(type,fields={}){const event=new Event(type);Object.assign(event,fields);this.dispatchEvent(event);}
}
function fixture(reduced=true) {
  globalThis.document={createElement:tag=>new Element(tag),createTextNode:value=>{const node=new Element('#text');node.textContent=value;return node;},activeElement:null};
  const media=new EventTarget();media.matches=reduced;globalThis.matchMedia=()=>media;
  let disconnected=false;
  globalThis.ResizeObserver=class{observe(){}disconnect(){disconnected=true;}};
  const animations=[];
  Element.prototype.animate=function(){let resolve,reject;const finished=new Promise((yes,no)=>{resolve=yes;reject=no;});const animation={finished,resolve,cancel(){reject(Error('cancelled'));}};animations.push(animation);return animation;};
  const scope=pageScope(),identity=new Element(),heading=new Element();heading.className='game-heading-row';identity.append(heading);
  return {scope,identity,animations,media,get disconnected(){return disconnected;}};
}
const project={slug:'n100f',title:'Game',console:'GameCube',year:'2002',cover:'/cover.webp',coverWidth:640,coverHeight:908,selectedTarget:{id:'ID-rev0',region:'USA'}};

test('shipping content has exactly two bios, six facts per current game and no Gecko codes',()=>{
  for(const slug of ['n100f','tw2004','mvp2005','nflstreet2']){
    const content=gameEditorial({...project,slug});
    assert.equal(content.paragraphs.length,['n100f','tw2004'].includes(slug)?4:0);
    assert.equal(content.facts.length,6);assert.deepEqual(content.codes,[]);
    assert.deepEqual(content.facts.at(-1),['Region','USA']);
    assert.deepEqual(gameEditorial({...project,slug,selectedTarget:{id:'ID-rev1',region:'Europe'}}).facts.at(-1),['Region','Europe']);
  }
  const unknown=gameEditorial({...project,slug:'new-game',selectedTarget:null});
  assert.deepEqual(unknown.paragraphs,[]);assert.deepEqual(unknown.codes,[]);
});

test('no bio means no prose or separator; zero codes retains its tab and empty state',()=>{
  const f=fixture(),dossier=createGameDossier({project,editorial:gameEditorial({...project,slug:'mvp2005'}),identity:f.identity,scope:f.scope});
  assert.equal(f.identity.querySelector('.dossier-prose'),null);
  assert.equal(f.identity.querySelector('.dossier-about').className,'dossier-about');
  assert.equal(f.identity.querySelectorAll('.dossier-action').length,2);
  const codes=f.identity.querySelectorAll('.dossier-action')[1];assert.equal(codes.textContent,'Gecko codes0');
  codes.emit('click');assert.equal(f.identity.querySelector('.dossier-codes').hidden,false);
  assert.equal(f.identity.querySelectorAll('.dossier-code-entry').length,0);
  assert.equal(f.identity.querySelector('.dossier-empty').textContent,'No Gecko codes yet.');
  const action=f.identity.querySelector('.dossier-action');action.emit('click');
  assert.equal(dossier.expanded,true);assert.equal(action.getAttribute('aria-expanded'),'true');
  action.emit('click');assert.equal(dossier.expanded,false);
  dossier.destroy();assert.equal(f.disconnected,true);f.scope.destroy();
});

test('bios render emphasis as text nodes and escape closes the region with focus restored',()=>{
  const f=fixture(),dossier=createGameDossier({project,editorial:{paragraphs:['An *italic* <script>literal</script>'],facts:[],codes:[]},identity:f.identity,scope:f.scope});
  const prose=f.identity.querySelector('.dossier-prose');
  assert.equal(prose.querySelector('em').textContent,'italic');assert.match(prose.textContent,/<script>literal/);
  assert.match(f.identity.querySelector('.dossier-about').className,/has-bio/);
  dossier.show();prose.focus();f.identity.querySelector('.expandable-region').emit('keydown',{key:'Escape'});
  assert.equal(dossier.expanded,false);assert.equal(document.activeElement,f.identity.querySelector('.dossier-action'));dossier.destroy();f.scope.destroy();
});

test('INI copy writes the full raw value but late completion cannot update a departed header',async()=>{
  const f=fixture();let copied,resolve;
  const rawIni='[Gecko]\n$Example\n04000000 12345678\n';
  const dossier=createGameDossier({project,editorial:{paragraphs:[],facts:[],codes:[{id:'example',title:'Example',description:'Details',notes:'Notes',rawIni}]},identity:f.identity,scope:f.scope,writeText:value=>{copied=value;return new Promise(done=>resolve=done);}});
  assert.equal(f.identity.querySelector('pre').textContent,'04000000 12345678');
  const button=f.identity.querySelector('.dossier-copy');button.emit('click');assert.equal(copied,rawIni);
  f.scope.destroy();resolve();await Promise.resolve();assert.equal(button.getAttribute('aria-label'),'Copy Example INI');assert.equal(f.disconnected,true);dossier.destroy();
});

test('interrupted expansion and page exit cancel animations without restoring stale state',async()=>{
  const f=fixture(false),region=createExpandableRegion({id:'test',label:'Details',scope:f.scope});
  region.setExpanded(true);region.setExpanded(false);region.setExpanded(true);
  f.animations.at(-1).resolve();await Promise.resolve();
  assert.equal(region.node.hidden,false);assert.equal(region.node.inert,false);assert.equal(region.node.style.height,'auto');
  region.setExpanded(false);f.scope.destroy();await Promise.resolve();region.destroy();
  assert.equal(f.scope.signal.aborted,true);
});
