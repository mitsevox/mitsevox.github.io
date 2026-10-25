import {projects} from './projects.js';
import {createHeader,createFooter} from './shell.js?v=3';
import {mountHub} from './hub.js';
import {mountProgress} from './progress.js';
import {mountActivity} from './activity.js';
import {mountIdentity} from './identity.js';
import {mountWiki} from './wiki.js?v=4';

const shell=document.querySelector('.shell');
const header=createHeader(),footer=createFooter();
const content=document.createElement('div');content.id='page-content';
shell.replaceChildren(header.node,content,footer.node);
const templates=new Map();
let controllers=[],generation=0,displayedURL=null,restoring=false;
function route(url){
  const path=url.pathname.replace(/\/+$/,'')||'/';
  if(path==='/')return {project:null};
  if(path==='/wiki')return {project:null,wiki:'start-here'};
  const wiki=path.match(/^\/wiki\/([a-z0-9-]+)$/);
  if(wiki&&['repository-setup','layout-and-naming','evidence-and-reconstruction','build-and-validation','review-and-approval','ci-and-publication','credits-and-history','website-integration','operations','starter-kit'].includes(wiki[1]))return {project:null,wiki:wiki[1]};
  const project=projects.find(p=>p.href.replace(/\/$/,'')===path);
  return project?{project}:null;
}
function template(name){
  if(!templates.has(name))templates.set(name,fetch(name.startsWith('/')?name:'/assets/'+name+'.html').then(response=>{
    if(!response.ok)throw Error('Layout unavailable');return response.text();
  }).catch(error=>{templates.delete(name);throw error;}));
  return templates.get(name);
}
function saveScroll(){
  if(!restoring&&displayedURL===location.href)history.replaceState({...history.state,scrollY:window.scrollY},'',location.href);
}
function restorePosition(url,scrollY,{smooth=false}={}){
  const behavior=smooth&&!matchMedia('(prefers-reduced-motion: reduce)').matches?'smooth':'instant';
  if(url.hash){const target=document.getElementById(decodeURIComponent(url.hash.slice(1)));if(target){target.scrollIntoView({behavior});return;}}
  window.scrollTo({top:scrollY,behavior});
}
async function navigate(url,{push=false,scrollY=0,focus=false}={}){
  const match=route(url);if(!match)return;
  const version=++generation;
  try{
    const html=await template(match.wiki?(match.wiki==='start-here'?'/wiki/content.html':'/wiki/'+match.wiki+'/content.html'):match.project?'game':'hub');
    if(version!==generation)return;
    saveScroll();restoring=true;
    const wikiController=match.wiki&&controllers.find(controller=>controller.update&&controller.main?.classList.contains('wiki-layout'));
    const focusedInContent=content.contains(document.activeElement)&&!wikiController?.sidebar.contains(document.activeElement);
    if(!wikiController){controllers.forEach(controller=>controller.destroy());controllers=[];}
    if(push)history.pushState({scrollY:0},'',url);
    displayedURL=location.href;
    const fragment=document.createElement('template');fragment.innerHTML=html;
    let main=fragment.content.querySelector('main');main.tabIndex=-1;
    const project=match.project;
    if(project){
      document.body.dataset.project=project.slug;
      main.querySelector('h1').textContent=project.title+' decompilation progress';
      main.querySelector('.lower h3').textContent=project.slug==='nflstreet2'?'Want to join the blitz?':'Contribute to '+project.shortTitle;
      main.querySelector('.lower a').href=project.contributeUrl;
      if(!project.contributionsEnabled)main.querySelector('.lower').remove();

    }else delete document.body.dataset.project;
    if(wikiController){wikiController.update(main);main=wikiController.main;content.querySelector('.route-error')?.remove();}
    else content.replaceChildren(main);
    header.update(project,{wiki:!!match.wiki});footer.update(project);
    document.title=match.wiki?main.querySelector('h1').textContent+' · Wiki · mitsevox':project?project.title+' · mitsevox':'mitsevox · Decompilations';
    if(project)controllers=[mountIdentity(main,project),mountProgress(main,project,footer.buildLink),mountActivity(main,project)];
    else controllers=[wikiController||(match.wiki?mountWiki(main):mountHub(main))];
    if(focus&&focusedInContent)main.focus({preventScroll:true});
    window.scrollTo({top:0,behavior:'instant'});
    // Restore after report-driven content has its final height.
    await Promise.allSettled(controllers.map(controller=>controller.ready));
    if(version!==generation)return;
    restorePosition(url,scrollY);restoring=false;saveScroll();
  }catch(error){
    if(version!==generation)return;
    restoring=false;
    const message=document.createElement('p');message.className='route-error';
    message.textContent='This page could not load. ';
    const retry=document.createElement('a');retry.href=url.href;retry.textContent='Try again';message.append(retry);
    content.querySelector('.route-error')?.remove();content.append(message);
    console.error(error);
  }
}
history.scrollRestoration='manual';
history.replaceState({scrollY:window.scrollY,...history.state},'',location.href);
let scrollFrame=null;
window.addEventListener('scroll',()=>{if(scrollFrame===null)scrollFrame=requestAnimationFrame(()=>{scrollFrame=null;saveScroll();});},{passive:true});
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
      if(location.href!==url.href)history.pushState({scrollY:window.scrollY},'',url);
      displayedURL=url.href;restorePosition(url,0,{smooth:true});
    }
    return;
  }
  event.preventDefault();
  if(url.href===displayedURL&&!content.querySelector('.route-error')){header.update(route(url).project,{wiki:!!route(url).wiki});window.scrollTo({top:0,behavior:'smooth'});return;}
  navigate(url,{push:true,focus:true});
});
window.addEventListener('popstate',event=>{
  const url=new URL(location.href);
  if(displayedURL&&new URL(displayedURL).pathname===url.pathname){++generation;displayedURL=url.href;restoring=false;restorePosition(url,event.state?.scrollY||0,{smooth:!!route(url)?.wiki});return;}
  navigate(url,{scrollY:event.state?.scrollY||0,focus:true});
});
navigate(new URL(location.href),{scrollY:history.state?.scrollY||0});
