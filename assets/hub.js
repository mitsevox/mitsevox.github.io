import {createAction} from './components/ui/action.js';
import {createProgressBar} from './components/ui/progress-bar.js';
import {createSearchField} from './components/ui/search-field.js';
import {createTooltip} from './components/ui/tooltip.js';
import {createCommitLine} from './components/ui/commit-line.js';
import {createDropdown} from './components/ui/dropdown.js';
import {fetchSummary} from './reports.js';
import {projects} from './projects.js';
import {consoleIcon} from './console-icon.js';
import {pageScope} from './lifecycle.js';
export function mountHub(root) {
const scope=pageScope();
const {signal,listen}=scope;
const motionPreference=matchMedia('(prefers-reduced-motion: reduce)');
const pending=[];
const grid=root.querySelector('.project-grid');
const tooltip=createTooltip({id:'card-tooltip',variant:'hub',scope});root.append(tooltip.node);
const searchField=createSearchField({id:'project-search',label:'Search games',placeholder:'Search games',variant:'hub'});
root.querySelector('[data-ui="project-search"]').replaceWith(searchField.node);
const search=searchField.input;
const entries=[];
let filterValue='all',sortValue='latest';

const controls=[
  {id:'project-filter',label:'Filter by console',icon:'filter',defaultValue:'all',getValue:()=>filterValue,setValue:value=>filterValue=value,
   options:[{value:'all',label:'All consoles'},...[...new Set(projects.map(p=>p.console))].map(console=>({value:console,label:console,console}))]},
  {id:'project-sort',label:'Sort games',icon:'sort',defaultValue:'latest',getValue:()=>sortValue,setValue:value=>sortValue=value,
   options:[['latest','Latest commit'],['name','Name A–Z'],['code','Code progress'],['data','Data progress']].map(([value,label])=>({value,label}))}
];
function syncControls(){for(const control of controls)control.dropdown.setValue(control.getValue());}
const optionArea=root.querySelector('.hub-options');
for(const control of controls){
  control.dropdown=createDropdown({...control,className:'hub-control',triggerClass:'hub-icon-button',value:control.getValue(),ariaLabel:control.label,scope,
    onSelect:option=>{control.setValue(option.value);syncControls();updateEntries();}});
  optionArea.append(control.dropdown.node);
}
syncControls();
function updateEntries(){
  hideTooltip();
  const query=search.value.trim().toLocaleLowerCase();
  const ordered=[...entries].sort((a,b)=>{
    if(sortValue==='latest')return (Date.parse(b.commitDate)||0)-(Date.parse(a.commitDate)||0);
    if(sortValue==='name')return a.project.title.localeCompare(b.project.title);
    if(sortValue==='code'||sortValue==='data')return (b.progress[sortValue]??-1)-(a.progress[sortValue]??-1);
    return a.index-b.index;
  });
  let visible=0;
  for(const entry of ordered){
    const searchable=[entry.project.title,entry.project.slug,entry.project.year,entry.project.console].join(' ').toLocaleLowerCase();
    entry.card.hidden=!(searchable.includes(query)&&(filterValue==='all'||entry.project.console===filterValue));
    if(!entry.card.hidden)visible++;
    grid.append(entry.card);
  }
  root.querySelector('.hub-empty').hidden=visible!==0;
  root.querySelector('#project-results').textContent=visible+' '+(visible===1?'game':'games');
}
listen(search,'input',updateEntries);
const reset=createAction({id:'project-reset',label:'Clear filters'});root.querySelector('[data-ui="project-reset"]').replaceWith(reset);
listen(reset,'click',()=>{search.value='';filterValue='all';syncControls();updateEntries();search.focus();});
function hideTooltip(){tooltip.hide();}
for(const project of projects){
  const card=createAction({href:project.href,className:'project-card',ariaLabel:'Explore '+project.title});
  const cover=document.createElement('img');cover.className='project-cover';cover.src=project.thumb;cover.addEventListener('error',()=>{cover.src=project.cover;},{once:true});cover.alt='';cover.width=project.coverWidth;cover.height=project.coverHeight;
  if(entries.length===0)cover.setAttribute('fetchpriority','high');else cover.loading='lazy';
  const details=document.createElement('div');details.className='entry-details';
  const title=document.createElement('h2');title.className='entry-title';title.insertAdjacentHTML('afterbegin',consoleIcon(project.console));const name=document.createElement('span');name.textContent=project.title;title.append(name);
  const measures=document.createElement('div');measures.className='card-progress';
  const bars=Object.fromEntries(['code','data'].map(kind=>{const bar=createProgressBar({kind,variant:'compact',ariaLabel:project.title+' '+kind+' matched progress',tooltip,scope});measures.append(bar.node);return [kind,bar];}));
  details.append(title,measures);
  const commit=createCommitLine({variant:'compact',repository:project.repo,scope});
  card.append(cover,details,commit.node);grid.append(card);
  const entry={project,card,bars,commit,index:entries.length,progress:{}};entries.push(entry);
  pending.push(fetchSummary(project, signal).then(data=>{
    if(signal.aborted)return;
    entry.commit.update(data.latest_commit);entry.commitDate=entry.commit.date;
    for(const kind of ['code','data']){entry.bars[kind].update(data.measures[kind]);entry.progress[kind]=entry.bars[kind].matched;}
    if(['latest','code','data'].includes(sortValue))updateEntries();
  }).catch(()=>{if(signal.aborted)return;entry.commit.update(null);for(const bar of Object.values(entry.bars))bar.unavailable();}));
}
updateEntries();
listen(window, 'scroll',hideTooltip,{passive:true});
listen(window, 'resize',hideTooltip);
listen(motionPreference,'change',hideTooltip);

return {ready:Promise.allSettled(pending),destroy(){scope.destroy();}};
}
