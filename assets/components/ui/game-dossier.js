import {createAction} from './action.js';
import {icon} from './icons.js';
import {componentScope} from './scope.js';
import {createExpandableRegion} from './expandable-region.js';
import {createGameFacts} from './game-facts.js';

/**
 * Editorial content stays independent of reports. Code applicability is explicit.
 * @typedef {{id:string,title:string,description:string,rawIni:string,notes:string}} CodeEntry
 * @typedef {Object} DossierProps
 * @property {{title:string,console:string,cover:string,thumb?:string,coverWidth:number,coverHeight:number}} project
 * @property {{paragraphs:string[],facts:[string,string][],codes:CodeEntry[]}} editorial
 * @property {(text:string)=>Promise<void>=} writeText Clipboard adapter.
 * @property {HTMLElement} identity
 * @property {ReturnType<typeof import('../../lifecycle.js').pageScope>} scope
 */
const chevron='<svg class="dossier-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg>';
const copyGlyph='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/></svg>';
const copiedGlyph='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>';
const aboutGlyph='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><circle cx="12" cy="7.5" r=".8" fill="currentColor" stroke="none"/></svg>';
function text(tag,value,className){const node=document.createElement(tag);node.textContent=value;if(className)node.className=className;return node;}

/** @param {DossierProps} props */
export function createGameDossier({project,editorial,identity,scope:parent,writeText=value=>navigator.clipboard.writeText(value)}){
  const scope=componentScope(parent),motion=matchMedia('(prefers-reduced-motion: reduce)');
  const region=createExpandableRegion({id:'game-dossier',label:'Game notes and Gecko codes',scope});
  const panel=document.createElement('section');panel.className='dossier-panel';region.content.append(panel);
  const stage=document.createElement('div');stage.className='dossier-stage';panel.append(stage);
  const about=document.createElement('div');about.className='dossier-about';
  const prose=document.createElement('div');prose.className='dossier-prose';
  for(const paragraph of editorial.paragraphs){
    const node=document.createElement('p');
    // Support authored emphasis without treating editorial text as HTML.
    for(const part of paragraph.split(/(\*[^*\n]+\*)/g))node.append(part.startsWith('*')&&part.endsWith('*')?text('em',part.slice(1,-1)):document.createTextNode(part));
    prose.append(node);
  }
  const metadata=createGameFacts({facts:editorial.facts});
  if(editorial.paragraphs.length){about.append(prose);about.classList.add('has-bio');}
  about.append(metadata);
  const codes=document.createElement('div');codes.className='dossier-codes';codes.hidden=true;
  if(!editorial.codes.length)codes.append(text('p','No Gecko codes yet.','dossier-empty'));
  const codeRegions=[];
  for(const entry of editorial.codes){
    const row=document.createElement('div');row.className='dossier-code-entry';
    const heading=document.createElement('div');heading.className='dossier-code-heading';
    const toggle=createAction({className:'dossier-code-toggle',ariaLabel:'Show '+entry.title+' code'});toggle.append(icon('code',{className:'dossier-code-icon'}));
    const label=text('span',entry.title,'dossier-code-name');label.append(text('small',entry.description));
    toggle.append(label);toggle.insertAdjacentHTML('beforeend',chevron);toggle.setAttribute('aria-expanded','false');
    const detail=createExpandableRegion({id:'gecko-code-'+entry.id,label:entry.title+' code and description',duration:280,scope});codeRegions.push(detail);toggle.setAttribute('aria-controls',detail.node.id);
    const body=document.createElement('div');body.className='dossier-code-body';
    const visibleCode=entry.rawIni.split(/\r?\n/).filter(line=>/^[0-9A-Fa-fXx]{8}\s+[0-9A-Fa-fXx]{8}$/.test(line.trim())).join('\n');
    const code=text('pre',visibleCode);code.setAttribute('aria-label',entry.title+' Gecko code');
    const copy=createAction({ariaLabel:'Copy '+entry.title+' INI',className:'dossier-copy'});copy.innerHTML=copyGlyph;copy.title='Copy INI';heading.append(toggle,copy);
    body.append(code);if(entry.notes)body.append(text('p',entry.notes,'dossier-code-notes'));detail.content.append(body);
    let copyTimer=null;scope.signal.addEventListener('abort',()=>clearTimeout(copyTimer),{once:true});
    scope.listen(copy,'click',async()=>{
      clearTimeout(copyTimer);
      try{await writeText(entry.rawIni);if(scope.signal.aborted)return;copy.innerHTML=copiedGlyph;copy.classList.add('is-copied');copy.title='INI copied';copy.setAttribute('aria-label','INI copied');copyTimer=setTimeout(()=>{copy.innerHTML=copyGlyph;copy.classList.remove('is-copied');copy.title='Copy INI';copy.setAttribute('aria-label','Copy '+entry.title+' INI');},1600);}
      catch{if(!scope.signal.aborted){copy.title='Could not copy INI. Try again.';copy.setAttribute('aria-label','Could not copy '+entry.title+' INI. Try again.');}}
    });
    scope.listen(toggle,'click',()=>{const expanded=!detail.expanded;if(!expanded&&detail.node.contains(document.activeElement))toggle.focus();toggle.setAttribute('aria-expanded',String(expanded));detail.setExpanded(expanded);});
    row.append(heading,detail.node);codes.append(row);
  }
  stage.append(about,codes);
  const hero=document.createElement('div');hero.className='dossier-hero';
  const artwork=createAction({className:'dossier-artwork',ariaLabel:'About '+project.title});
  const cover=document.createElement('img');cover.src=project.thumb||project.cover;cover.alt=project.title+' cover';cover.width=project.coverWidth;cover.height=project.coverHeight;cover.decoding='async';artwork.append(cover);
  const body=document.createElement('div');body.className='dossier-hero-body';
  const heading=identity.querySelector('.game-heading-row');
  const actions=document.createElement('div');actions.className='dossier-actions';actions.setAttribute('role','group');actions.setAttribute('aria-label','Explore this game');
  const marker=document.createElement('span');marker.className='dossier-action-marker';marker.setAttribute('aria-hidden','true');
  const buttons=new Map();
  for(const [value,label] of [['about','About the game'],['codes','Gecko codes']]){
    const button=createAction({label,className:'dossier-action'});button.dataset.view=value;
    if(value==='about')button.insertAdjacentHTML('afterbegin',aboutGlyph);else button.prepend(icon('code'));
    if(value==='codes')button.append(text('span',String(editorial.codes.length),'dossier-count'));
    button.setAttribute('aria-controls',region.node.id);button.setAttribute('aria-expanded','false');button.setAttribute('aria-pressed','false');buttons.set(value,button);actions.append(button);
    scope.listen(button,'click',()=>{if(region.expanded&&selected===value)hide();else show(value);});
  }
  actions.append(marker);body.append(heading,actions);hero.append(...(project.cover?[artwork]:[]),body);if(!project.cover)hero.classList.add('without-artwork');identity.prepend(hero);identity.append(region.node);
  let selected='about',contentAnimation=null;
  function sync(){
    for(const [value,button] of buttons){const active=region.expanded&&selected===value;button.setAttribute('aria-expanded',String(active));button.setAttribute('aria-pressed',String(active));}
    artwork.setAttribute('aria-expanded',String(region.expanded&&selected==='about'));artwork.setAttribute('aria-controls',region.node.id);
    marker.style.opacity=region.expanded?'1':'0';
    if(region.expanded){const button=buttons.get(selected);marker.style.width=button.offsetWidth+'px';marker.style.transform='translateX('+button.offsetLeft+'px)';}
  }
  function show(value='about'){
    if(scope.signal.aborted||!buttons.has(value))return;
    contentAnimation?.cancel();
    const change=()=>{selected=value;about.hidden=value!=='about';codes.hidden=value!=='codes';};
    if(region.expanded)region.resize(change);else{change();region.setExpanded(true);}sync();
    if(!motion.matches)contentAnimation=scope.animate(value==='about'?about:codes,[{opacity:0,transform:'translateY(5px)'},{opacity:1,transform:'translateY(0)'}],{duration:260,easing:'cubic-bezier(.22,1,.36,1)'});
  }
  function hide(){if(scope.signal.aborted)return;contentAnimation?.cancel();if(region.node.contains(document.activeElement))buttons.get(selected).focus();region.setExpanded(false);sync();}
  scope.listen(motion,'change',()=>{if(motion.matches)contentAnimation?.cancel();});
  scope.listen(artwork,'click',()=>{if(region.expanded&&selected==='about')hide();else show('about');});
  scope.listen(region.node,'keydown',event=>{if(event.key==='Escape'){event.preventDefault();hide();}});
  const observer=new ResizeObserver(sync);observer.observe(actions);scope.signal.addEventListener('abort',()=>observer.disconnect(),{once:true});sync();
  return {show,hide,get expanded(){return region.expanded;},destroy(){contentAnimation?.cancel();codeRegions.forEach(item=>item.destroy());region.destroy();scope.destroy();hero.remove();}};
}
