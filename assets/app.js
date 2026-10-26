import {projects} from './projects.js';
import {createHeader,createFooter} from './shell.js?v=3';
import {mountHub} from './hub.js';
import {mountProgress} from './progress.js';
import {mountActivity} from './activity.js';
import {mountIdentity} from './identity.js';
import {mountWiki} from './wiki.js?v=4';
import {wikiChapters} from './wiki-chapters.js';
import {createScrollState, pushRoute} from './scroll-state.js';

const shell=document.querySelector('.shell');
const header=createHeader(),footer=createFooter();
const content=document.createElement('div');content.id='page-content';
const navigationStatus=document.createElement('div');navigationStatus.className='route-progress';navigationStatus.hidden=true;navigationStatus.setAttribute('role','status');
const navigationLabel=document.createElement('span');navigationLabel.className='sr-only';navigationStatus.append(navigationLabel);
shell.replaceChildren(header.node,navigationStatus,content,footer.node);
const templates=new Map();
let controllers=[],generation=0,displayedURL=null,restoring=false,scrollIntent=0;
for(const event of ['wheel','touchstart'])document.addEventListener(event,()=>{scrollIntent++;},{passive:true});
document.addEventListener('keydown',event=>{if(['PageDown','PageUp','Home','End','ArrowDown','ArrowUp',' '].includes(event.key))scrollIntent++;});
function route(url){
  const path=url.pathname.replace(/\/+$/,'')||'/';
  if(path==='/')return {project:null};
  if(path==='/wiki')return {project:null,wiki:'start-here'};
  const wiki=path.match(/^\/wiki\/([a-z0-9-]+)$/);
  if(wiki&&wikiChapters.includes(wiki[1]))return {project:null,wiki:wiki[1]};
  const project=projects.find(p=>p.href.replace(/\/$/,'')===path);
  return project?{project}:null;
}
function template(name){
  // Keep chapter HTML in the same immutable release as its scripts and styles.
  const url=name.startsWith('/wiki/')?new URL('../'+name.slice(1),import.meta.url).href:name.startsWith('/')?name:'/assets/'+name+'.html';
  if(!templates.has(name))templates.set(name,fetch(url).then(response=>{
    if(!response.ok)throw Error('Layout unavailable');return response.text();
  }).catch(error=>{templates.delete(name);throw error;}));
  return templates.get(name);
}
const scrollState=createScrollState({history,location,readY:()=>window.scrollY,
  canSave:()=>!restoring&&displayedURL===location.href});
function saveScroll(){scrollState.save(true);}
function restorePosition(url,scrollY,{smooth=false}={}){
  const behavior=smooth&&!matchMedia('(prefers-reduced-motion: reduce)').matches?'smooth':'instant';
  if(url.hash){const target=document.getElementById(decodeURIComponent(url.hash.slice(1)));if(target){target.scrollIntoView({behavior});return;}}
  window.scrollTo({top:scrollY,behavior});
}
function templateFor(match){return match.wiki?(match.wiki==='start-here'?'/wiki/content.html':'/wiki/'+match.wiki+'/content.html'):match.project?'game':'hub';}
async function navigate(url,{push=false,scrollY=0,focus=false}={}){
  const match=route(url);if(!match)return;
  const version=++generation;
  navigationLabel.textContent='Loading '+(match.wiki?'wiki':match.project?.title||'projects');navigationStatus.hidden=false;content.setAttribute('aria-busy','true');
  try{
    const html=await template(templateFor(match));
    if(version!==generation)return;
    saveScroll();restoring=true;
    const wikiController=match.wiki&&controllers.find(controller=>controller.update&&controller.main?.classList.contains('wiki-layout'));
    const focusedInContent=content.contains(document.activeElement)&&!wikiController?.sidebar.contains(document.activeElement);
    if(!wikiController){controllers.forEach(controller=>controller.destroy());controllers=[];}
    if(push&&!pushRoute({scrollY:0},url))return;
    displayedURL=location.href;
    const fragment=document.createElement('template');fragment.innerHTML=html;
    let main=fragment.content.querySelector('main');main.tabIndex=-1;
    const project=match.project;
    if(project){
      document.body.dataset.project=project.slug;
      main.querySelector('h1').textContent=project.title+' decompilation progress';
      main.querySelector('.lower h3').textContent=project.contributionHeading||'Want to join the effort?';
      main.querySelector('.lower a').href=project.contributeUrl;
      if(!project.contributionsEnabled)main.querySelector('.lower').remove();
      const optional = {functionCounts:'[data-stats="function"]',fileCounts:'[data-stats="file"]',timeline:'.history-section',contributors:'.people-section'};
      for(const [key,selector] of Object.entries(optional))if(project.modules?.[key]===false)main.querySelector(selector)?.remove();
      if(!main.querySelector('.function-stats'))main.querySelector('.stats-grid').remove();

    }else delete document.body.dataset.project;
    if(wikiController){wikiController.update(main);main=wikiController.main;content.querySelector('.route-error')?.remove();}
    else content.replaceChildren(main);
    header.update(project,{wiki:!!match.wiki});footer.update(project);
    document.title=match.wiki?main.querySelector('h1').textContent+' · Wiki · mitsevox':project?project.title+' · mitsevox':'mitsevox · Decompilations';
    if(project)controllers=[mountIdentity(main,project),mountProgress(main,project,footer.buildLink),mountActivity(main,project)];
    else controllers=[wikiController||(match.wiki?mountWiki(main):mountHub(main))];
    navigationStatus.hidden=true;content.removeAttribute('aria-busy');
    if(focus&&focusedInContent)main.focus({preventScroll:true});
    window.scrollTo({top:0,behavior:'instant'});
    // A late map response must never snap a visitor back after they start scrolling.
    const intent=scrollIntent;
    // Restore after report-driven content has its final height.
    await Promise.allSettled(controllers.map(controller=>controller.ready));
    if(version!==generation)return;
    if(intent===scrollIntent)restorePosition(url,scrollY);restoring=false;saveScroll();
  }catch(error){
    if(version!==generation)return;
    restoring=false;navigationStatus.hidden=true;content.removeAttribute('aria-busy');
    const message=document.createElement('p');message.className='route-error';
    message.textContent='This page could not load. ';
    const retry=document.createElement('a');retry.href=url.href;retry.textContent='Try again';message.append(retry);
    content.querySelector('.route-error')?.remove();content.append(message);
    console.error(error);
  }
}
// Warm only the small route template when a visitor indicates navigation intent.
function warmTemplate(event){
  const link=event.target.closest('a[href]');if(!link)return;
  const url=new URL(link.href);if(url.origin!==location.origin)return;
  const match=route(url);if(match)template(templateFor(match)).catch(()=>{});
}
document.addEventListener('pointerover',warmTemplate,{passive:true});
document.addEventListener('focusin',warmTemplate);
history.scrollRestoration='manual';
window.addEventListener('scroll',()=>scrollState.save(),{passive:true});
window.addEventListener('pagehide',saveScroll);
document.addEventListener('click',event=>{
  if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  const link=event.target.closest('a[href]');
  if(!link||link.hasAttribute('download')||(link.target&&link.target!=='_self'))return;
  const url=new URL(link.href);
  if(url.origin!==location.origin||!route(url))return;
  if(url.pathname===location.pathname&&url.hash){
    if(route(url).wiki){
      let id;try{id=decodeURIComponent(url.hash.slice(1));}catch{return;}
      if(!document.getElementById(id))return;
      event.preventDefault();saveScroll();
      if(location.href!==url.href&&!pushRoute({scrollY:window.scrollY},url))return;
      displayedURL=url.href;restorePosition(url,0,{smooth:true});
    }
    return;
  }
  event.preventDefault();
  if(url.href===displayedURL&&!content.querySelector('.route-error')){++generation;restoring=false;navigationStatus.hidden=true;content.removeAttribute('aria-busy');header.update(route(url).project,{wiki:!!route(url).wiki});window.scrollTo({top:0,behavior:'smooth'});return;}
  navigate(url,{push:true,focus:true});
});
window.addEventListener('popstate',event=>{
  const url=new URL(location.href);
  if(displayedURL&&new URL(displayedURL).pathname===url.pathname){++generation;navigationStatus.hidden=true;content.removeAttribute('aria-busy');displayedURL=url.href;restoring=false;restorePosition(url,event.state?.scrollY||0,{smooth:!!route(url)?.wiki});return;}
  navigate(url,{scrollY:event.state?.scrollY||0,focus:true});
});
navigate(new URL(location.href),{scrollY:history.state?.scrollY||0});
