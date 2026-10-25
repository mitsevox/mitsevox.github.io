import {projects} from './projects.js';
export const arrow = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>';
const github = '<svg class="icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .8a11.2 11.2 0 0 0-3.54 21.83c.56.1.77-.24.77-.54v-2.09c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.64-1.25-1.64-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 1.71 2.62 1.22 3.26.93.1-.73.39-1.22.71-1.5-2.5-.29-5.13-1.25-5.13-5.54 0-1.22.44-2.22 1.15-3-.12-.28-.5-1.42.11-2.96 0 0 .94-.3 3.08 1.15a10.72 10.72 0 0 1 5.6 0c2.14-1.45 3.08-1.15 3.08-1.15.61 1.54.23 2.68.11 2.96.71.78 1.15 1.78 1.15 3 0 4.3-2.64 5.25-5.15 5.53.4.35.76 1.03.76 2.08v3.09c0 .3.2.65.77.54A11.2 11.2 0 0 0 12 .8Z"/></svg>';
const contributionIcon = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 4v10a4 4 0 0 0 4 4h4M16 4v4a4 4 0 0 1-4 4H8"/><circle cx="8" cy="4" r="2"/><circle cx="16" cy="4" r="2"/><circle cx="18" cy="18" r="2"/></svg>';
const chevron = '<svg class="switch-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg>';
export function createHeader() {
  const node=document.createElement('header');
  node.innerHTML=`<div class="header-location"><a class="wordmark" href="/" aria-label="mitsevox — all projects">mitsevox</a><span class="wordmark-slash" aria-hidden="true">/</span><div class="project-switcher"><button type="button" class="project-trigger" aria-expanded="false" aria-haspopup="true" aria-controls="project-menu"><span class="game-title"></span>${chevron}</button><nav id="project-menu" class="project-menu hub-popover" aria-label="Switch game" hidden>${projects.map(p=>`<a data-project="${p.slug}" href="${p.href}"><img src="${p.cover}" alt=""><span>${p.title}<small>${p.console}</small></span><span class="current-mark" aria-hidden="true" hidden>✓</span></a>`).join('')}</nav></div></div><nav class="main-nav" aria-label="Main navigation"><a class="wiki-link" href="/wiki/"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v15m0-15C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Z"/></svg><span>Wiki</span></a><a class="github-link">${github}<span>GitHub</span></a><a class="contribute-link" aria-label="Contribute" hidden>${contributionIcon}<span>Contribute</span></a></nav>`;
  const switcher=node.querySelector('.project-switcher'),trigger=node.querySelector('.project-trigger'),menu=node.querySelector('#project-menu'),contribute=node.querySelector('.contribute-link');
  const wikiLabel=document.createElement('span');
  wikiLabel.className='wiki-location game-title';wikiLabel.textContent='Wiki';wikiLabel.hidden=true;
  switcher.after(wikiLabel);
  const links=[...menu.querySelectorAll('a')];
  function close(restore=false){menu.hidden=true;trigger.setAttribute('aria-expanded','false');if(restore)trigger.focus();}
  function open(focusLast=false){
    document.dispatchEvent(new CustomEvent('portfolio-menu-open',{detail:trigger}));
    menu.hidden=false;trigger.setAttribute('aria-expanded','true');
    (focusLast?links.at(-1):links.find(link=>link.hasAttribute('aria-current'))||links[0]).focus();
  }
  trigger.addEventListener('click',()=>menu.hidden?open():close(true));
  trigger.addEventListener('keydown',event=>{if(['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();open(event.key==='ArrowUp');}});
  switcher.addEventListener('keydown',event=>{
    if(event.key==='Escape'){event.preventDefault();close(true);}
    if(menu.hidden||!menu.contains(event.target))return;
    if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
      event.preventDefault();const index=links.indexOf(document.activeElement);
      const next=event.key==='Home'?0:event.key==='End'?links.length-1:(index+(event.key==='ArrowDown'?1:-1)+links.length)%links.length;links[next].focus();
    }
  });
  document.addEventListener('pointerdown',event=>{if(!switcher.contains(event.target))close();});
  document.addEventListener('portfolio-menu-open',event=>{if(event.detail!==trigger)close();});
  // Pointer focus can leave an anchor before its click fires (notably in WebKit).
  // Outside pointerdown already dismisses the menu; defer focus dismissal only for Tab.
  switcher.addEventListener('keydown',event=>{
    if(event.key==='Tab')requestAnimationFrame(()=>{if(!switcher.contains(document.activeElement))close();});
  });
  function update(project,{wiki=false}={}){
    if(!menu.hidden&&menu.contains(document.activeElement))trigger.focus();close();
    switcher.hidden=wiki;wikiLabel.hidden=!wiki;
    trigger.querySelector('.game-title').textContent=project?.shortTitle||'Projects';
    trigger.setAttribute('aria-label','Switch game: '+(project?.title||'All projects'));
    for(const link of links){const selected=link.dataset.project===project?.slug;if(selected)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');link.querySelector('.current-mark').hidden=!selected;}
    const wikiLink=node.querySelector('.wiki-link');if(wiki)wikiLink.setAttribute('aria-current','page');else wikiLink.removeAttribute('aria-current');
    const githubLink=node.querySelector('.github-link');githubLink.href=project?.repo||'https://github.com/mitsevox';githubLink.setAttribute('aria-label',project?project.title+' on GitHub':'GitHub');
    contribute.hidden=!project?.contributionsEnabled;
    if(project?.contributionsEnabled)contribute.href=project.contributeUrl;else contribute.removeAttribute('href');
  }
  update(null);return {node,update};
}
export function createFooter(){
  const node=document.createElement('footer');
  node.innerHTML='<span>made by <a href="https://github.com/mitsevox">@mitsevox</a></span><span><a id="build-link"></a><span class="build-target"></span></span>';
  const buildLink=node.querySelector('#build-link'),target=node.querySelector('.build-target');
  function update(project){
    buildLink.hidden=!project;
    if(project){buildLink.href=project.repo;buildLink.textContent='Loading progress…';buildLink.removeAttribute('title');}
    target.textContent=project?' · '+project.target:'GameCube decompilations';
  }
  update(null);return {node,update,buildLink};
}
