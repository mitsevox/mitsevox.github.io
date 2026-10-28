import {createContributionLink} from './components/ui/contribution-link.js';
import {createDropdown} from './components/ui/dropdown.js';
import {projects} from './projects.js';
export const arrow = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>';
const github = '<svg class="icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .8a11.2 11.2 0 0 0-3.54 21.83c.56.1.77-.24.77-.54v-2.09c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.64-1.25-1.64-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 1.71 2.62 1.22 3.26.93.1-.73.39-1.22.71-1.5-2.5-.29-5.13-1.25-5.13-5.54 0-1.22.44-2.22 1.15-3-.12-.28-.5-1.42.11-2.96 0 0 .94-.3 3.08 1.15a10.72 10.72 0 0 1 5.6 0c2.14-1.45 3.08-1.15 3.08-1.15.61 1.54.23 2.68.11 2.96.71.78 1.15 1.78 1.15 3 0 4.3-2.64 5.25-5.15 5.53.4.35.76 1.03.76 2.08v3.09c0 .3.2.65.77.54A11.2 11.2 0 0 0 12 .8Z"/></svg>';
export function createHeader() {
  const node=document.createElement('header');
  const skip=document.createElement('a');skip.className='skip-link';skip.href='#page-content';skip.textContent='Skip to content';
  node.innerHTML=`<div class="header-location"><a class="wordmark" href="/" aria-label="mitsevox — all projects">mitsevox</a><span class="wordmark-slash" aria-hidden="true">/</span></div><nav class="main-nav" aria-label="Main navigation"><a class="wiki-link" href="/wiki/" aria-label="Wiki"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v15m0-15C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Z"/></svg><span>Wiki</span></a><a class="github-link">${github}<span>GitHub</span></a></nav>`;
  node.prepend(skip);
  const contribute=createContributionLink({hidden:true});node.querySelector('.main-nav').append(contribute);
  const dropdown=createDropdown({id:'project-picker',label:'Switch game',className:'project-switcher',triggerClass:'project-trigger',labelClass:'game-title',menuClass:'project-menu',value:null,triggerLabel:'Projects',
    options:projects.map(project=>({value:project.slug,label:project.title,description:project.console,image:project.cover,href:project.href}))});
  const switcher=dropdown.node,trigger=dropdown.trigger,menu=dropdown.menu;
  node.querySelector('.header-location').append(switcher);
  const wikiLabel=document.createElement('span');
  wikiLabel.className='wiki-location game-title';wikiLabel.textContent='Wiki';wikiLabel.hidden=true;
  switcher.after(wikiLabel);
  function update(project,{wiki=false}={}){
    if(!menu.hidden&&menu.contains(document.activeElement))trigger.focus();dropdown.close();
    switcher.hidden=wiki;wikiLabel.hidden=!wiki;
    dropdown.setValue(project?.slug||null,{triggerLabel:project?.shortTitle||'Projects',ariaLabel:'Switch game: '+(project?.title||'All projects')});
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
    buildLink.hidden=!project||project.available===false;
    if(project){buildLink.href=project.repo;buildLink.textContent='Loading progress…';buildLink.removeAttribute('title');}
    target.textContent=project?' · '+project.target:'Decompilation projects';
  }
  update(null);return {node,update,buildLink};
}
