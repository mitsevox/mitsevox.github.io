import {pageScope} from './lifecycle.js';
let searchIndex;
function loadIndex(){
  if(!searchIndex)searchIndex=fetch('/assets/wiki-index.json').then(r=>{if(!r.ok)throw Error('Search unavailable');return r.json();}).catch(e=>{searchIndex=null;throw e;});
  return searchIndex;
}
function mountWikiArticle(main){
  const scope=pageScope();
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  if(!reduced.matches)scope.animate(main.querySelector('.wiki-reading'),[
    {opacity:0,transform:'translateY(7px)'},{opacity:1,transform:'translateY(0)'}
  ],{duration:240,easing:'cubic-bezier(.22,1,.36,1)'});
  const sectionLinks=[...main.querySelectorAll('.wiki-on-page nav a')];
  const headings=[...main.querySelectorAll('.wiki-article h2')];
  let positionFrame=null;
  function markSection(){
    positionFrame=null;
    const current=headings.filter(h=>h.getBoundingClientRect().top<=120).at(-1)||headings[0];
    for(const link of sectionLinks){
      if(link.hash==='#'+current?.id)link.setAttribute('aria-current','location');
      else link.removeAttribute('aria-current');
    }
  }
  scope.listen(window,'scroll',()=>{if(positionFrame===null)positionFrame=scope.frame(markSection);},{passive:true});
  markSection();
  for(const pre of main.querySelectorAll('pre')){
    const code=pre.querySelector('code');code.textContent=code.textContent.replace(/^\n+|\n+$/g,'');
    const block=document.createElement('div');block.className='wiki-code';
    const actions=document.createElement('div');actions.className='wiki-code-actions';
    const button=document.createElement('button');button.type='button';button.className='wiki-copy';button.textContent='Copy';button.setAttribute('aria-label','Copy code example');
    pre.before(block);block.append(pre,actions);actions.append(button);
    scope.listen(button,'click',async()=>{
      try{await navigator.clipboard.writeText(pre.querySelector('code').textContent);if(scope.signal.aborted)return;button.textContent='Copied';button.setAttribute('aria-label','Code copied');}
      catch{if(!scope.signal.aborted){button.textContent='Select to copy';button.setAttribute('aria-label','Clipboard unavailable; select the code to copy');}}
    });
  }
  return {destroy:scope.destroy};
}

export function mountWiki(main){
  const scope=pageScope(),sidebar=main.querySelector('.wiki-sidebar'),input=sidebar.querySelector('.wiki-search input'),results=sidebar.querySelector('.wiki-results'),status=sidebar.querySelector('.wiki-search-status'),chapters=sidebar.querySelector('.wiki-chapters');
  const nav=sidebar.querySelector('.wiki-nav'),links=[...nav.querySelectorAll('a')];
  const selector=document.createElement('span');selector.className='wiki-nav-selector';selector.setAttribute('aria-hidden','true');nav.prepend(selector);
  let queryVersion=0,article=mountWikiArticle(main),positionFrame=null;
  function positionSelector(){
    positionFrame=null;
    const current=links.find(link=>link.getAttribute('aria-current')==='page');
    if(!current||!nav.getClientRects().length)return;
    const item=current.getBoundingClientRect(),box=nav.getBoundingClientRect();
    selector.style.height=item.height+'px';
    selector.style.transform='translateY('+(item.top-box.top)+'px)';
    selector.style.opacity='1';
    if(!selector.classList.contains('is-ready'))scope.frame(()=>selector.classList.add('is-ready'));
  }
  function schedulePosition(){if(positionFrame===null)positionFrame=scope.frame(positionSelector);}
  const resize=new ResizeObserver(schedulePosition);resize.observe(nav);
  scope.listen(chapters,'toggle',schedulePosition);
  scope.listen(window,'resize',schedulePosition);
  function selectChapter(next){
    const selected=next.querySelector('.wiki-nav a[aria-current="page"]')?.getAttribute('href');
    for(const link of links){
      if(link.getAttribute('href')===selected)link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    }
    positionSelector();
  }
  const narrow=matchMedia('(max-width: 760px)');chapters.open=!narrow.matches;
  scope.listen(narrow,'change',()=>{chapters.open=!narrow.matches;});
  async function search(){
    const version=++queryVersion,query=input.value.trim().toLowerCase();
    results.replaceChildren();results.hidden=!query;chapters.hidden=!!query;status.textContent='';
    if(!query){scope.frame(positionSelector);return;}
    try{
      const index=await loadIndex();if(scope.signal.aborted||version!==queryVersion)return;
      const terms=query.split(/\s+/);
      const found=index.filter(page=>terms.every(term=>(page.title+' '+page.text).toLowerCase().includes(term))).sort((a,b)=>Number(b.title.toLowerCase().includes(query))-Number(a.title.toLowerCase().includes(query)));
      status.textContent=found.length+' matching chapter'+(found.length===1?'':'s');
      if(!found.length){const p=document.createElement('p');p.textContent='No chapters found. Try a different term.';results.append(p);}
      for(const page of found){
        const a=document.createElement('a'),strong=document.createElement('strong'),small=document.createElement('small');
        a.href=page.href;strong.textContent=page.title;
        const at=page.text.toLowerCase().indexOf(terms[0]),start=Math.max(0,at-35);
        small.textContent=(start?'…':'')+page.text.slice(start,start+115)+'…';
        a.append(strong,small);results.append(a);
      }
    }catch(error){if(scope.signal.aborted||version!==queryVersion)return;const p=document.createElement('p');p.textContent='Search is unavailable. Clear the field to browse chapters.';results.append(p);status.textContent=p.textContent;}
  }
  scope.listen(input,'input',search);scope.listen(input,'search',search);
  scope.listen(input,'keydown',event=>{if(event.key==='Escape'){input.value='';search();}});
  positionSelector();
  function update(next){
    article.destroy();
    main.querySelector('.wiki-reading').replaceWith(next.querySelector('.wiki-reading'));
    main.querySelector('.wiki-on-page').replaceWith(next.querySelector('.wiki-on-page'));
    main.dataset.chapter=next.dataset.chapter;
    selectChapter(next);
    article=mountWikiArticle(main);
  }
  return {main,sidebar,update,ready:Promise.resolve(),destroy(){article.destroy();resize.disconnect();scope.destroy();}};
}
