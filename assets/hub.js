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
const search=root.querySelector('#project-search'),filter=root.querySelector('#project-filter'),sort=root.querySelector('#project-sort');
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

const check='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg>';
const controls=[
  {trigger:filter,menu:root.querySelector('#filter-menu'),getValue:()=>filterValue,setValue:value=>filterValue=value,choices:[['all','All consoles'],...[...new Set(projects.map(p=>p.console))].map(name=>[name,name])]},
  {trigger:sort,menu:root.querySelector('#sort-menu'),getValue:()=>sortValue,setValue:value=>sortValue=value,choices:[['latest','Latest commit'],['name','Name A–Z'],['code','Code progress'],['data','Data progress']]}
];
function closeMenu(control,restoreFocus=false){
  control.menu.hidden=true;control.trigger.setAttribute('aria-expanded','false');
  if(restoreFocus)control.trigger.focus();
}
function syncControls(){
  for(const control of controls){
    control.trigger.classList.toggle('has-selection',!['all','latest'].includes(control.getValue()));
    for(const option of control.menu.querySelectorAll('[role="menuitemradio"]')){
      const selected=option.dataset.value===control.getValue();
      option.setAttribute('aria-checked',String(selected));option.tabIndex=selected?0:-1;
    }
  }
}
function openMenu(control,focusLast=false){
  document.dispatchEvent(new CustomEvent('portfolio-menu-open',{detail:control.trigger}));
  for(const other of controls)if(other!==control)closeMenu(other);
  control.menu.hidden=false;control.trigger.setAttribute('aria-expanded','true');
  const options=[...control.menu.querySelectorAll('[role="menuitemradio"]')];
  (focusLast?options.at(-1):options.find(option=>option.getAttribute('aria-checked')==='true')||options[0]).focus();
}
for(const control of controls){
  for(const [value,label] of control.choices){
    const option=document.createElement('button');option.type='button';option.className='popover-option';option.dataset.value=value;option.setAttribute('role','menuitemradio');
    const text=document.createElement('span');text.className='popover-option-label';
    if(control.trigger===filter&&value!=='all')text.insertAdjacentHTML('beforeend',consoleIcon(value));
    text.append(document.createTextNode(label));option.append(text);option.insertAdjacentHTML('beforeend',check);
    control.menu.querySelector('.popover-options').append(option);
    listen(option,'click',()=>{control.setValue(value);syncControls();updateEntries();closeMenu(control,true);});
  }
  listen(control.trigger,'click',()=>control.menu.hidden?openMenu(control):closeMenu(control,true));
  listen(control.trigger,'keydown',event=>{if(['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();openMenu(control,event.key==='ArrowUp');}});
  listen(control.menu,'keydown',event=>{
    if(event.key==='Escape'){event.preventDefault();closeMenu(control,true);return;}
    const options=[...control.menu.querySelectorAll('[role="menuitemradio"]')],index=options.indexOf(document.activeElement);
    if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
      event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?options.length-1:(index+(event.key==='ArrowDown'?1:-1)+options.length)%options.length;
      options.forEach((option,i)=>option.tabIndex=i===next?0:-1);options[next].focus();
    }
  });
  listen(control.trigger.parentElement,'focusout',()=>frame(()=>{if(!control.trigger.parentElement.contains(document.activeElement))closeMenu(control);}));
}
listen(document,'pointerdown',event=>{for(const control of controls)if(!control.trigger.parentElement.contains(event.target))closeMenu(control);});
listen(document,'portfolio-menu-open',event=>{for(const control of controls)if(event.detail!==control.trigger)closeMenu(control);});
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
  card.innerHTML=`${cover}<div class="entry-details"><h2 class="entry-title">${consoleIcon(project.console)}<span>${project.title}</span></h2><div class="card-progress">${['code','data'].map(kind=>`<div class="card-measure progress-element" data-progress="${kind}"><div class="card-measure-label"><span>${kindLabel(kind)}</span><strong>—</strong></div><div class="card-track" role="progressbar" aria-label="${project.title} ${kind} matched progress" aria-valuemin="0" aria-valuemax="100"><i class="progress-fuzzy"></i><i class="progress-matched"></i><i class="progress-linked"></i></div><div class="progress-key" aria-hidden="true"><span><i class="linked-key"></i>Linked</span><span><i class="matched-key"></i>Matched</span><span><i class="fuzzy-key"></i>Fuzzy</span></div></div>`).join('')}</div></div><div class="entry-commit" aria-label="Latest commit"><svg class="commit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M3 12h5m8 0h5"/><circle cx="12" cy="12" r="4"/></svg><span class="commit-title">Loading latest commit…</span><time class="commit-time"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3 2"/></svg><span></span></time></div>`;
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
