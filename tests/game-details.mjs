import assert from 'node:assert/strict';
import {test} from 'node:test';
import {gameEditorial} from '../assets/game-editorial.js';
import {createGameDossier} from '../assets/components/ui/game-dossier.js';
import {createExpandableRegion} from '../assets/components/ui/expandable-region.js';
import {pageScope} from '../assets/lifecycle.js';
import {createHash} from 'node:crypto';

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

test('shipping content has exactly two bios, six facts per current game and target-scoped codes',()=>{
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

test('the four authored codes belong only to n100f GIHE78-rev0',()=>{
  const selectedTarget={id:'GIHE78-rev0',region:'USA'};
  const entries=gameEditorial({...project,selectedTarget}).codes;
  assert.deepEqual(entries.map(entry=>entry.title),['21:9 Ultrawide Fix','Infinite Health','Pickup Reach Fix','Restored Enemy Drops']);
  for(const slug of ['mvp2005','tw2004','nflstreet2'])assert.deepEqual(gameEditorial({...project,slug,selectedTarget}).codes,[]);
  for(const id of ['GIHE78-rev1','GIHP78-rev0','GIHE78'])assert.deepEqual(gameEditorial({...project,selectedTarget:{id,region:'USA'}}).codes,[]);
  assert.deepEqual(gameEditorial({...project,selectedTarget:null}).codes,[]);
});

test('real code views display every supplied line and copy the credited full INI',async()=>{
  const f=fixture(),selectedTarget={id:'GIHE78-rev0',region:'USA'};
  const editorial=gameEditorial({...project,selectedTarget}),copied=[];
  const dossier=createGameDossier({project,editorial,identity:f.identity,scope:f.scope,writeText:async text=>copied.push(text)});
  dossier.show('codes');
  assert.equal(f.identity.querySelector('.dossier-count').textContent,'4');
  assert.equal(f.identity.querySelector('.dossier-empty'),null);
  const views=f.identity.querySelectorAll('pre'),buttons=f.identity.querySelectorAll('.dossier-copy');
  assert.deepEqual(views.map(view=>view.textContent.split('\n').length),[7,1,4,58]);
  assert.deepEqual(views.map(view=>createHash('sha256').update(view.textContent+'\n').digest('hex')),[
    '3955ce68649bea5c4e3dd9b9ce825f36e48eea4c10b697552e51a5aff24133f0',
    '35b5171218f78f9dec4d4f871c35525f1f9d03a0255730ab4278e9ea63c99232',
    '1cf041dfa301ae01f188c1b7158b7a3b730b60ac7b22b19afbdc4329abbfc548',
    '7d59640d374abd328ca3b0babb21544d10900d5f6606a17779576f0268d119a1'
  ]);
  for(const [index,entry] of editorial.codes.entries()){
    assert.ok(entry.rawIni.startsWith('[Gecko]\n$'+entry.title+' [mits]\n'));
    assert.ok(entry.rawIni.endsWith('\n'));
    assert.ok(views[index].textContent.split('\n').every(line=>/^[0-9a-fA-F]{8} [0-9a-fA-F]{8}$/.test(line)));
    buttons[index].emit('click');await Promise.resolve();
    assert.equal(copied[index],entry.rawIni);
  }
  assert.match(editorial.codes[0].notes,/Turn off Dolphin's widescreen hack/);
  assert.match(editorial.codes[0].notes,/aspect ratio to Stretch/);
  assert.match(editorial.codes[1].notes,/falls still kill you/);
  dossier.destroy();f.scope.destroy();
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
