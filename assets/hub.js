import {createDropdown} from './components/ui/dropdown.js';
import {fetchSummary} from './reports.js';
import {projects} from './projects.js';
import {consoleIcon} from './console-icon.js';
import {pageScope} from './lifecycle.js';
export function mountHub(root) {
const scope=pageScope();
const {signal,listen,frame,animate}=scope;
const motionPreference=matchMedia('(prefers-reduced-motion: reduce)');
const pending=[];
const grid=root.querySelector('.project-grid');
const tooltip=root.querySelector('#card-tooltip');
const search=root.querySelector('#project-search');
const entries=[];
const relativeTime=new Intl.RelativeTimeFormat('en',{numeric:'always'});
function updateCommitTimes(){
  for(const entry of entries){
    if(!entry.commitDate)continue;
    const seconds=Math.max(0,(Date.now()-Date.parse(entry.commitDate))/1000);
    let text='just now';
    for(const [unit,size] of [['year',31536000],['month',2592000],['day',86400],['hour',3600],['minute',60]])if(seconds>=size){text=relativeTime.format(-Math.floor(seconds/size),unit);break;}
    entry.card.querySelector('.commit-time span').textContent=text;
  }
}
const timeRefresh=setInterval(updateCommitTimes,60000);
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
listen(root.querySelector('#project-reset'),'click',()=>{search.value='';filterValue='all';syncControls();updateEntries();search.focus();});
const kindLabel=kind=>kind==='code'?'Code':'Data';
let clearLift=null;
function hideTooltip(){tooltip.hidden=true;clearLift?.();clearLift=null;}
for(const project of projects){
  const card=document.createElement('a');card.className='project-card';card.href=project.href;card.setAttribute('aria-label','Explore '+project.title);
  const cover=`<img class="project-cover" src="${project.cover}" alt="" width="${project.coverWidth}" height="${project.coverHeight}" ${entries.length===0?'fetchpriority="high"':'loading="lazy"'}>`;
  card.innerHTML=`${cover}<div class="entry-details"><h2 class="entry-title">${consoleIcon(project.console)}<span>${project.title}</span></h2><div class="card-progress">${['code','data'].map(kind=>`<div class="card-measure progress-element" data-progress="${kind}"><div class="card-measure-label"><span>${kindLabel(kind)}</span><strong>—</strong></div><div class="card-track" role="progressbar" aria-label="${project.title} ${kind} matched progress" aria-valuemin="0" aria-valuemax="100"><i class="progress-fuzzy"></i><i class="progress-matched"></i><i class="progress-linked"></i></div></div>`).join('')}</div></div><div class="entry-commit" aria-label="Latest commit"><svg class="commit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M3 12h5m8 0h5"/><circle cx="12" cy="12" r="4"/></svg><span class="commit-title">Loading latest commit…</span><time class="commit-time"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3 2"/></svg><span></span></time></div>`;
  grid.append(card);
  const entry={project,card,index:entries.length,progress:{}};entries.push(entry);
  pending.push(fetchSummary(project, signal).then(data=>{
    if(signal.aborted)return;
    const commit=data.latest_commit;
    card.querySelector('.commit-title').textContent=commit?.title||'Latest commit unavailable';
    if(commit?.date&&Number.isFinite(Date.parse(commit.date))){
      entry.commitDate=commit.date;
      const time=card.querySelector('.commit-time');time.dateTime=commit.date;
      time.setAttribute('aria-label',new Date(commit.date).toLocaleString());
      updateCommitTimes();
    }
    for(const kind of ['code','data']){
      const measure=data.measures[kind],element=card.querySelector(`[data-progress="${kind}"]`),track=element.querySelector('.card-track');
      const available=measure.total>0;
      const values={linked:available?measure.linked/measure.total*100:0,matched:available?measure.matched/measure.total*100:0,
        ...(measure.fuzzy===undefined?{}:{fuzzy:available?measure.fuzzy/measure.total*100:0})};
      track.querySelector('.progress-fuzzy').hidden=measure.fuzzy===undefined;
      entry.progress[kind]=available?values.matched:null;
      element.querySelector('strong').textContent=available?values.matched.toFixed(2)+'%':'Unavailable';
      if(available)track.setAttribute('aria-valuenow',values.matched);else track.removeAttribute('aria-valuenow');
      track.setAttribute('aria-valuetext',available?Object.entries(values).map(([key,value])=>`${key} ${value.toFixed(2)}%`).join(', '):'Unavailable');
      frame(()=>frame(()=>{for(const field of Object.keys(values))track.querySelector('.progress-'+field).style.width=values[field]+'%';}));
      const lift=document.createElement('div');lift.className='progress-hover';lift.hidden=true;lift.setAttribute('aria-hidden','true');track.append(lift);
      let liftedStrip=null,stripAnimation=null;
      function clearHover(){stripAnimation?.cancel();liftedStrip=null;lift.hidden=true;}
      function hoverStrip(event){
        if(event.pointerType==='touch')return;
        const rect=track.getBoundingClientRect(),x=event.clientX-rect.left;
        let start=0;
        for(const field of ['linked','matched',...(values.fuzzy===undefined?[]:['fuzzy'])]){
          const end=track.querySelector('i.progress-'+field).getBoundingClientRect().width;
          if(x>=start&&x<end){
            if(clearLift&&clearLift!==clearHover)hideTooltip();
            clearLift=clearHover;
            if(liftedStrip!==field||lift.style.width!==(end-start)+'px'){
              stripAnimation?.cancel();liftedStrip=field;lift.hidden=false;
              lift.className='progress-hover progress-'+field;lift.style.left=start+'px';lift.style.width=(end-start)+'px';
              if(!motionPreference.matches)stripAnimation=animate(lift,[
                {transform:'translateY(-50%) scale(1)',opacity:.5},
                {transform:'translateY(-50%) scale(1.008,1.3)',opacity:1}
              ],{duration:160,easing:'cubic-bezier(.22,1,.36,1)'});
            }
            tooltip.textContent=field[0].toUpperCase()+field.slice(1)+' '+values[field].toFixed(2)+'%';tooltip.hidden=false;
            tooltip.style.left=Math.max(12,Math.min(event.clientX+12,innerWidth-tooltip.offsetWidth-12))+'px';
            tooltip.style.top=Math.max(12,event.clientY-tooltip.offsetHeight-12)+'px';
            return;
          }
          start=Math.max(start,end);
        }
        hideTooltip();
      }
      listen(track, 'pointerenter',hoverStrip);
      listen(track, 'pointermove',hoverStrip);
      listen(track, 'pointerleave',hideTooltip);
    }
    if(['latest','code','data'].includes(sortValue))updateEntries();
  }).catch(()=>{if(!signal.aborted)card.querySelector('.commit-title').textContent='Latest commit unavailable';if(!signal.aborted)for(const measure of card.querySelectorAll('.card-measure')){measure.querySelector('strong').textContent='Unavailable';measure.querySelector('.card-track').setAttribute('aria-valuetext','Progress unavailable');}}));
}
updateEntries();
listen(window, 'scroll',hideTooltip,{passive:true});
listen(window, 'resize',hideTooltip);
listen(motionPreference,'change',hideTooltip);

return {ready:Promise.allSettled(pending),destroy(){clearInterval(timeRefresh);scope.destroy();}};
}
