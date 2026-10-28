// Contributor rankings by credited, exactly matched functions.
import {createAction} from '../components/ui/action.js';
import {pageScope} from '../lifecycle.js';
import {fetchContributors} from '../reports.js';

function validate(people){
  if(!Array.isArray(people))throw Error('Invalid contributor credit');
  let count=Infinity;const users=new Set();
  for(const p of people){if(!/^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$/.test(p.login)||users.has(p.login)||!Number.isSafeInteger(p.id)||p.id<=0||!Number.isSafeInteger(p.functions)||p.functions<=0||p.functions>count)throw Error('Invalid contributor credit');users.add(p.login);count=p.functions;}
}

export function mount(root,{project}){
  const scope=pageScope();
  const {signal,listen}=scope;
  const list=root.querySelector('.contributor-rankings');
  function renderPeople(people){
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
  function load(){
    return fetchContributors(project,signal).then(people=>{if(signal.aborted)return;validate(people);renderPeople(people);}).catch(()=>{
      if(signal.aborted)return;
      list.textContent='Contributor credits unavailable ';
      const retry=createAction({className:'inline-retry',label:'Retry'});
      listen(retry,'click',()=>{retry.remove();list.textContent='';load();},{once:true});list.append(retry);
    });
  }
  return {ready:load(),destroy:scope.destroy};
}
