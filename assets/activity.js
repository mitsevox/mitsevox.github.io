import {pageScope} from './lifecycle.js';
import {fetchActivity} from './reports.js';
export function mountActivity(root, project) {
  const scope=pageScope();
  const {signal,listen}=scope;

  const chart=root.querySelector('.history-chart'),scrub=root.querySelector('#history-scrub');
  const list=root.querySelector('.contributor-rankings');
  const timeline = !!chart, contributors = !!list;
  if (!timeline && !contributors) return {ready:Promise.resolve(), destroy:scope.destroy};
  const fields=['code','data'];
  const shortDate=new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric'});
  const fullDate=new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
  let rows=[],index=0,ceiling=10;
  const percent=(row,kind)=>row[kind].linked/row[kind].total*100;
  let first=0,last=1;
  const x=i=>10+(rows.length===1?1:(Date.parse(rows[i].built_at)-first)/(last-first))*980;
  const y=value=>200-value/ceiling*180;
  function draw(){
    if (!timeline) return;
    for(const kind of fields){
      const values=rows.map(row=>percent(row,kind));
      root.querySelector(`[data-line="${kind}"]`).setAttribute('d',values.map((v,i)=>(i?'L':'M')+x(i)+','+y(v)).join(' '));
      const dot=root.querySelector(`[data-dot="${kind}"]`);dot.setAttribute('cx',x(index));dot.setAttribute('cy',y(values[index]));
      root.querySelector(`[data-history-value="${kind}"]`).textContent=values[index].toFixed(2)+'%';
    }
    const cursor=root.querySelector('#history-cursor');cursor.setAttribute('x1',x(index));cursor.setAttribute('x2',x(index));
    const time=root.querySelector('#history-date');time.textContent=fullDate.format(new Date(rows[index].built_at));time.dateTime=rows[index].built_at;
    scrub.value=index;scrub.setAttribute('aria-valuetext',fullDate.format(new Date(rows[index].built_at))+': code '+percent(rows[index],'code').toFixed(2)+'% linked, data '+percent(rows[index],'data').toFixed(2)+'% linked');
  }
  function renderPeople(people){
    if (!contributors) return;
    list.replaceChildren();
    people.forEach((person,i)=>{
      const row=document.createElement('li'),place=document.createElement('span');place.className='contributor-place';place.textContent=String(i+1).padStart(2,'0');
      if(i<3){
        const ns='http://www.w3.org/2000/svg',medal=document.createElementNS(ns,'svg');
        medal.classList.add('rank-medal');medal.setAttribute('viewBox','0 0 32 36');medal.setAttribute('aria-hidden','true');
        const faceId=`rank-medal-face-${i+1}`,rimId=`rank-medal-rim-${i+1}`;
        medal.innerHTML=`
          <defs>
            <linearGradient id="${faceId}" x1="7" y1="13" x2="25" y2="33" gradientUnits="userSpaceOnUse">
              <stop stop-color="var(--medal-light)"/>
              <stop offset=".48" stop-color="var(--medal-mid)"/>
              <stop offset="1" stop-color="var(--medal-dark)"/>
            </linearGradient>
            <linearGradient id="${rimId}" x1="6" y1="12" x2="26" y2="34" gradientUnits="userSpaceOnUse">
              <stop stop-color="var(--medal-light)"/>
              <stop offset=".45" stop-color="var(--medal-dark)"/>
              <stop offset="1" stop-color="var(--medal-mid)"/>
            </linearGradient>
          </defs>
          <path d="M5 2h8l8 15-7 4Z" fill="#344966"/>
          <path d="M19 2h8l-9 19-7-4Z" fill="#607da5"/>
          <path d="m21 2-7 15" fill="none" stroke="#9cb4d2" stroke-opacity=".45" stroke-width="1.5"/>
          <circle cx="16" cy="23" r="10.5" fill="url(#${rimId})" stroke="var(--medal-dark)" stroke-width=".6"/>
          <circle cx="16" cy="23" r="8.5" fill="url(#${faceId})" stroke="var(--medal-light)" stroke-opacity=".65" stroke-width=".7"/>
          <path d="m16 17.8 1.6 3.3 3.6.5-2.6 2.5.6 3.6-3.2-1.7-3.2 1.7.6-3.6-2.6-2.5 3.6-.5Z" fill="var(--medal-dark)" stroke="var(--medal-light)" stroke-opacity=".65" stroke-width=".5" stroke-linejoin="round"/>
        `;
        place.append(medal);
      }
      const avatar=document.createElement('span');avatar.className='person-avatar avatar-'+['one','two','three','four'][i%4];avatar.setAttribute('aria-hidden','true');avatar.textContent=person.login.slice(0,2).toUpperCase();
      const image=document.createElement('img');if(!project.preview)image.src='https://avatars.githubusercontent.com/u/'+person.id+'?s=80';image.alt='';image.width=40;image.height=40;image.loading='lazy';image.referrerPolicy='no-referrer';listen(image, 'error',()=>image.remove());if(!project.preview)avatar.append(image);else avatar.textContent=String(i+1).padStart(2,'0');
      const name=document.createElement(project.preview?'span':'a');if(!project.preview)name.href='https://github.com/'+person.login;name.className='contributor-name';name.textContent=project.preview?'Contributor '+(i+1):person.login;
      const count=document.createElement('span');count.className='contributor-functions';const value=document.createElement('b');value.textContent=person.functions.toLocaleString();count.append(value,document.createTextNode(person.functions===1?' function':' functions'));
      row.append(place,avatar,name,count);list.append(row);
    });
  }
  function validate(data){
    if(data.schema!==1||data.target!==project.target||data.target_sha1!==project.targetSha1||(timeline&&(!Array.isArray(data.snapshots)||!data.snapshots.length))||(contributors&&!Array.isArray(data.contributors)))throw Error('Invalid project activity');
    const seen=new Set();let previous=-Infinity;
    for(const row of timeline?data.snapshots:[]){
      const time=Date.parse(row.built_at);
      if(!/^[a-f0-9]{40}$/.test(row.revision)||seen.has(row.revision)||!Number.isFinite(time)||time<previous)throw Error('Invalid progress history');
      seen.add(row.revision);previous=time;
      for(const kind of fields){const m=row[kind];if(!m||!Number.isSafeInteger(m.total)||m.total<=0||!Number.isSafeInteger(m.linked)||m.linked<0||m.linked>m.total)throw Error('Invalid linked measurement');}
    }
    let count=Infinity;const users=new Set();
    for(const p of contributors?data.contributors:[]){if(!/^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$/.test(p.login)||users.has(p.login)||!Number.isSafeInteger(p.id)||p.id<=0||!Number.isSafeInteger(p.functions)||p.functions<=0||p.functions>count)throw Error('Invalid contributor credit');users.add(p.login);count=p.functions;}
  }
  if (timeline) listen(scrub, 'input',()=>{if(rows.length){index=Number(scrub.value);draw();}});
  function point(event){
    if(!rows.length)return;const rect=chart.getBoundingClientRect(),fraction=Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width));
    const time=first+fraction*(last-first);index=rows.reduce((best,row,i)=>Math.abs(Date.parse(row.built_at)-time)<Math.abs(Date.parse(rows[best].built_at)-time)?i:best,0);draw();
  }
  if (timeline) listen(chart, 'pointermove',point);
  if (timeline) listen(chart, 'pointerdown',event=>{point(event);scrub.focus({preventScroll:true});});
  if (timeline) listen(chart, 'pointerleave',()=>{if(rows.length){index=rows.length-1;draw();}});
  const ready = fetchActivity(project,signal).then(data=>{
    if(signal.aborted)return;
    validate(data);if(timeline){rows=data.snapshots;index=rows.length-1;first=Date.parse(rows[0].built_at);last=Date.parse(rows[index].built_at);if(last===first)last=first+1;
    ceiling=Math.min(100,Math.max(5,Math.ceil(Math.max(...rows.flatMap(row=>fields.map(kind=>percent(row,kind))))/5)*5));
    if (timeline) { scrub.max=rows.length-1;root.querySelector('.history-ceiling').textContent=ceiling+'%';
    const ticks=[first,(first+last)/2,last],format=last-first<3*86400000?fullDate:shortDate;
    root.querySelectorAll('.history-axis span').forEach((tick,i)=>tick.textContent=format.format(new Date(ticks[i])));
    }
    }
    renderPeople(data.contributors);draw();
  }).catch(()=>{if(signal.aborted)return;if(timeline){root.querySelector('#history-date').textContent='Progress history unavailable';scrub.disabled=true;}if(contributors)list.textContent='Contributor credits unavailable';});

  return {ready, destroy:scope.destroy};
}
