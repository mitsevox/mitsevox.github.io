import {componentScope} from './scope.js';
import {createAction} from './action.js';
import {icon} from './icons.js';

/**
 * @typedef {Object} CommitLineProps
 * @property {'page'|'compact'=} variant Page row is a link; compact row is inside the card link.
 * @property {string} repository Repository URL used as the loading/fallback destination.
 * @property {ReturnType<typeof import('../../lifecycle.js').pageScope>=} scope
 *
 * @typedef {{title?:string,date?:string,url?:string}} CommitInfo
 */
/** @param {CommitLineProps} props */
export function createCommitLine({variant='page',repository,scope:parent}) {
  const scope=componentScope(parent),compact=variant==='compact';
  const node=compact?document.createElement('div'):createAction({href:repository});node.className=compact?'entry-commit':'identity-commit';
  if(compact)node.setAttribute('aria-label','Latest commit');
  const title=document.createElement('span');title.className='commit-title';title.textContent='Loading latest commit…';
  const time=document.createElement('time');time.className='commit-time';time.hidden=!compact;
  const relativeText=document.createElement('span');time.append(icon('clock',{className:''}),relativeText);
  node.append(icon('commit',{className:'commit-icon'}),title,time);
  let date=null,timer=null;
  const relative=new Intl.RelativeTimeFormat('en',{numeric:'always'});
  function tick(){
    if(!date||scope.signal.aborted)return;
    const seconds=Math.max(0,(Date.now()-Date.parse(date))/1000);let text='just now';
    for(const [unit,size] of [['year',31536000],['month',2592000],['day',86400],['hour',3600],['minute',60]])if(seconds>=size){text=relative.format(-Math.floor(seconds/size),unit);break;}
    relativeText.textContent=text;
  }
  function resetTime(){clearInterval(timer);timer=null;date=null;time.removeAttribute('datetime');time.removeAttribute('aria-label');relativeText.textContent='';time.hidden=!compact;}
  /** @param {CommitInfo|null|undefined} commit */
  function update(commit){
    if(scope.signal.aborted)return;
    resetTime();title.textContent=commit?.title||'Latest commit unavailable';
    if(!compact){node.href=commit?.url?.startsWith(repository+'/commit/')?commit.url:repository;if(commit?.title)node.setAttribute('aria-label','Latest commit: '+commit.title);else node.removeAttribute('aria-label');}
    if(commit?.date&&Number.isFinite(Date.parse(commit.date))){date=commit.date;time.hidden=false;time.dateTime=date;time.setAttribute('aria-label',new Date(date).toLocaleString());tick();timer=setInterval(tick,60000);}
  }
  scope.signal.addEventListener('abort',resetTime,{once:true});
  return {node,update,get date(){return date;},destroy(){scope.destroy();node.remove();}};
}
