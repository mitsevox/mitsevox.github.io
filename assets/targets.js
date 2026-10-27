import {pageScope} from './lifecycle.js';

export function selectTarget(project, url) {
  if (!project.targetCatalog) return project;
  const catalog=project.targetCatalog;
  const id=url.searchParams.get('target')||catalog.defaultTarget;
  const item=catalog.targets.find(item=>item.target.id===id);
  if(!item)return {...project,target:id,targetCatalog:null,available:false,unknownTarget:true,report:null,reportBase:null,latestCommit:null,
    modules:Object.fromEntries(Object.keys(project.modules).map(key=>[key,false])),contributionsEnabled:false};
  const report=project.targetReports[id];
  const available=!!report?.available;
  // Never inherit the default target's measurements into another selection.
  return {...project,target:id,selectedTarget:item,available,
    report:available?report.report:null,reportBase:available?report.reportBase:null,
    latestCommit:available?report.latestCommit:null,targetSha1:item.target.sha1,
    modules:available?report.modules:Object.fromEntries(Object.keys(project.modules).map(key=>[key,false])),
    contributionsEnabled:available&&project.contributionsEnabled};
}

export function mountTargetPicker(parent,project) {
  const scope=pageScope();
  if (!project.targetCatalog) return scope;
  const catalog=project.targetCatalog,current=project.selectedTarget.target;
  const wrapper=document.createElement('div');wrapper.className='target-pickers';
  const controls=[];
  const flags={USA:'🇺🇸',US:'🇺🇸',Japan:'🇯🇵',JPN:'🇯🇵',JP:'🇯🇵',Europe:'🇪🇺',EUR:'🇪🇺',EU:'🇪🇺',Australia:'🇦🇺',AUS:'🇦🇺',AU:'🇦🇺',Korea:'🇰🇷',KOR:'🇰🇷',KR:'🇰🇷'};
  function gameLabel(element,item){
    const flag=flags[item.target.region];
    if(flag){const icon=document.createElement('span');icon.className='region-flag';icon.setAttribute('aria-hidden','true');icon.textContent=flag;element.append(icon);}
    element.append(document.createTextNode(item.target.gameId));
  }
  const chevron='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg>';
  const ids=[...new Set(catalog.targets.map(item=>item.target.gameId))];
  const games=ids.map(id=>catalog.targets.find(item=>item.target.gameId===id&&item.target.id===catalog.defaultTarget)||catalog.targets.find(item=>item.target.gameId===id));
  const revisions=catalog.targets.filter(item=>item.target.gameId===current.gameId);
  function close(control,focus=false){control.menu.hidden=true;control.trigger.setAttribute('aria-expanded','false');if(focus)control.trigger.focus();}
  for (const [name,choices,label] of [['Game ID',games,item=>item.target.gameId],['Disc revision',revisions,item=>'Rev '+item.target.discRevision]]) {
    const holder=document.createElement('div');holder.className='target-picker';
    const trigger=document.createElement('button');trigger.type='button';trigger.className='target-trigger';
    const currentItem=name==='Game ID'?games.find(item=>item.target.gameId===current.gameId):project.selectedTarget;
    if(name==='Game ID')gameLabel(trigger,currentItem);else trigger.append(document.createTextNode(label(currentItem)));trigger.insertAdjacentHTML('beforeend',chevron);
    trigger.setAttribute('aria-label',name+': '+label(currentItem)+(name==='Game ID'?' · '+currentItem.target.region:''));trigger.setAttribute('aria-expanded','false');trigger.setAttribute('aria-haspopup','menu');
    const menu=document.createElement('div');menu.className='target-menu hub-popover';menu.hidden=true;menu.setAttribute('role','menu');menu.setAttribute('aria-label',name);
    menu.id='target-menu-'+(name==='Game ID'?'game':'revision');trigger.setAttribute('aria-controls',menu.id);
    const control={trigger,menu};controls.push(control);
    for(const item of choices){
      const link=document.createElement('a');link.className='popover-option';link.setAttribute('role','menuitemradio');
      const chosen=name==='Game ID'?item.target.gameId===current.gameId:item.target.id===current.id;
      link.setAttribute('aria-checked',String(chosen));link.tabIndex=chosen?0:-1;
      const url=new URL(project.href,location.origin);url.searchParams.set('target',item.target.id);link.href=url.pathname+url.search;
      const text=document.createElement('span');text.className='target-option-label';
      if(name==='Game ID'){gameLabel(text,item);link.setAttribute('aria-label',item.target.gameId+' · '+item.target.region);}else text.textContent=label(item);link.append(text);
      if(item.status==='archived'){const status=document.createElement('small');status.textContent='Archived';link.append(status);}
      menu.append(link);
    }
    function open(last=false){document.dispatchEvent(new CustomEvent('portfolio-menu-open',{detail:trigger}));menu.hidden=false;trigger.setAttribute('aria-expanded','true');const items=[...menu.children];(last?items.at(-1):items.find(item=>item.getAttribute('aria-checked')==='true')||items[0]).focus();}
    scope.listen(trigger,'click',()=>menu.hidden?open():close(control,true));
    scope.listen(trigger,'keydown',event=>{if(['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();open(event.key==='ArrowUp');}});
    scope.listen(menu,'keydown',event=>{
      if(event.key==='Escape'){event.preventDefault();close(control,true);return;}
      if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
        event.preventDefault();const items=[...menu.children],index=items.indexOf(document.activeElement);
        const next=event.key==='Home'?0:event.key==='End'?items.length-1:(index+(event.key==='ArrowDown'?1:-1)+items.length)%items.length;
        items.forEach((item,i)=>item.tabIndex=i===next?0:-1);items[next].focus();
      }
    });
    scope.listen(holder,'focusout',()=>scope.frame(()=>{if(!holder.contains(document.activeElement))close(control);}));
    holder.append(trigger,menu);wrapper.append(holder);
  }
  scope.listen(document,'pointerdown',event=>{for(const control of controls)if(!control.trigger.parentElement.contains(event.target))close(control);});
  scope.listen(document,'portfolio-menu-open',event=>{for(const control of controls)if(event.detail!==control.trigger)close(control);});
  parent.append(wrapper);return scope;
}
