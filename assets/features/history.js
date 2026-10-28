// Linked progress over time. The two lines are drawn once per load; scrubbing and hovering only
// move the cursor, dots and labels.
import {createRange} from '../components/ui/range.js';
import {createAction} from '../components/ui/action.js';
import {pageScope} from '../lifecycle.js';
import {fetchHistory} from '../reports.js';

const fields=['code','data'];
const shortDate=new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric'});
const fullDate=new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});

function validate(data,project){
  if(data.schema!==1||data.target!==project.target||data.target_sha1!==project.targetSha1||!Array.isArray(data.snapshots)||!data.snapshots.length)throw Error('Invalid progress history');
  const seen=new Set();let previous=-Infinity;
  for(const row of data.snapshots){
    const time=Date.parse(row.built_at);
    if(!/^[a-f0-9]{40}$/.test(row.revision)||seen.has(row.revision)||!Number.isFinite(time)||time<previous)throw Error('Invalid progress history');
    seen.add(row.revision);previous=time;
    for(const kind of fields){const m=row[kind];if(!m||!Number.isSafeInteger(m.total)||m.total<=0||!Number.isSafeInteger(m.linked)||m.linked<0||m.linked>m.total)throw Error('Invalid linked measurement');}
  }
}

export function mount(root,{project}){
  const scope=pageScope();
  const {signal,listen}=scope;
  const chart=root.querySelector('.history-chart');
  const scrub=createRange({id:'history-scrub',label:'Explore linked progress snapshots'});
  root.querySelector('[data-ui="history-scrub"]').replaceWith(scrub);
  const date=root.querySelector('#history-date'),cursor=root.querySelector('#history-cursor');
  let rows=[],times=[],values={},index=0,ceiling=10,first=0,last=1;
  const percent=(row,kind)=>row[kind].linked/row[kind].total*100;
  const x=i=>10+(rows.length===1?1:(times[i]-first)/(last-first))*980;
  const y=value=>200-value/ceiling*180;
  function draw(){
    for(const kind of fields){
      const dot=root.querySelector(`[data-dot="${kind}"]`);dot.setAttribute('cx',x(index));dot.setAttribute('cy',y(values[kind][index]));
      root.querySelector(`[data-history-value="${kind}"]`).textContent=values[kind][index].toFixed(2)+'%';
    }
    cursor.setAttribute('x1',x(index));cursor.setAttribute('x2',x(index));
    const when=rows[index].built_at;date.textContent=fullDate.format(new Date(when));date.dateTime=when;
    scrub.value=index;scrub.setAttribute('aria-valuetext',fullDate.format(new Date(when))+': code '+values.code[index].toFixed(2)+'% linked, data '+values.data[index].toFixed(2)+'% linked');
  }
  // Nearest snapshot to a time, by binary search over the sorted snapshot times.
  function nearest(time){
    let low=0,high=times.length-1;
    while(low<high){const mid=(low+high)>>1;if(times[mid]<time)low=mid+1;else high=mid;}
    return low>0&&time-times[low-1]<=times[low]-time?low-1:low;
  }
  function point(event){
    if(!rows.length)return;const rect=chart.getBoundingClientRect(),fraction=Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width));
    const next=nearest(first+fraction*(last-first));if(next!==index){index=next;draw();}
  }
  listen(scrub,'input',()=>{if(rows.length){index=Number(scrub.value);draw();}});
  listen(chart,'pointermove',point);
  listen(chart,'pointerdown',event=>{point(event);scrub.focus({preventScroll:true});});
  listen(chart,'pointerleave',()=>{if(rows.length&&index!==rows.length-1){index=rows.length-1;draw();}});
  function show(data){
    validate(data,project);
    const completed=data.snapshots.findIndex(row=>fields.every(kind=>row[kind].linked===row[kind].total));
    rows=completed<0?data.snapshots:data.snapshots.slice(0,completed+1);
    times=rows.map(row=>Date.parse(row.built_at));
    values=Object.fromEntries(fields.map(kind=>[kind,rows.map(row=>percent(row,kind))]));
    index=rows.length-1;first=times[0];last=times[index];if(last===first)last=first+1;
    ceiling=Math.min(100,Math.max(5,Math.ceil(Math.max(...values.code,...values.data)/5)*5));
    scrub.max=rows.length-1;scrub.disabled=false;root.querySelector('.history-ceiling').textContent=ceiling+'%';
    const ticks=[first,(first+last)/2,last],format=last-first<3*86400000?fullDate:shortDate;
    root.querySelectorAll('.history-axis span').forEach((tick,i)=>tick.textContent=format.format(new Date(ticks[i])));
    for(const kind of fields)root.querySelector(`[data-line="${kind}"]`).setAttribute('d',values[kind].map((v,i)=>(i?'L':'M')+x(i)+','+y(v)).join(' '));
    draw();
  }
  function load(){
    date.textContent='';
    return fetchHistory(project,signal).then(data=>{if(!signal.aborted)show(data);}).catch(()=>{
      if(signal.aborted)return;
      scrub.disabled=true;date.textContent='Progress history unavailable ';
      const retry=createAction({className:'inline-retry',label:'Retry'});
      listen(retry,'click',()=>{retry.remove();load();},{once:true});date.append(retry);
    });
  }
  return {ready:load(),destroy:scope.destroy};
}
