import {fetchSummary} from './reports.js';
import {consoleIcon} from './console-icon.js';
import {pageScope} from './lifecycle.js';
export function mountIdentity(root,project){
  const scope=pageScope();
  const identity=document.createElement('div');identity.className='game-identity';
  const heading=root.querySelector('h1');heading.className='game-identity-title';heading.textContent=project.title;
  heading.insertAdjacentHTML('afterbegin',consoleIcon(project.console));
  root.prepend(identity);identity.append(heading);
  const commit=document.createElement('a');commit.className='identity-commit';commit.href=project.repo;
  commit.innerHTML='<svg class="commit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M3 12h5m8 0h5"/><circle cx="12" cy="12" r="4"/></svg><span class="commit-title">Loading latest commit…</span><time class="commit-time" hidden><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3 2"/></svg><span></span></time>';
  identity.append(commit);
  let date=null;
  const relative=new Intl.RelativeTimeFormat('en',{numeric:'always'});
  function updateTime(){
    if(!date)return;
    const seconds=Math.max(0,(Date.now()-Date.parse(date))/1000);
    let text='just now';
    for(const [unit,size] of [['year',31536000],['month',2592000],['day',86400],['hour',3600],['minute',60]])if(seconds>=size){text=relative.format(-Math.floor(seconds/size),unit);break;}
    commit.querySelector('.commit-time span').textContent=text;
  }
  const refresh=setInterval(updateTime,60000);
  const ready=fetchSummary(project, scope.signal).then(data=>{
    if(scope.signal.aborted)return;
    const latest=data.latest_commit;if(!latest?.title)throw Error();
    commit.querySelector('.commit-title').textContent=latest.title;
    commit.setAttribute('aria-label','Latest commit: '+latest.title);
    if(latest.url?.startsWith(project.repo+'/commit/'))commit.href=latest.url;
    if(latest.date&&Number.isFinite(Date.parse(latest.date))){
      date=latest.date;const time=commit.querySelector('time');time.hidden=false;time.dateTime=date;time.setAttribute('aria-label',new Date(date).toLocaleString());updateTime();
    }
  }).catch(()=>{if(!scope.signal.aborted)commit.querySelector('.commit-title').textContent='Latest commit unavailable';});
  return {ready,destroy(){clearInterval(refresh);scope.destroy();}};
}
