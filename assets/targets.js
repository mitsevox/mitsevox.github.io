import {createDropdown} from './components/ui/dropdown.js';
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
  const ids=[...new Set(catalog.targets.map(item=>item.target.gameId))];
  const games=ids.map(id=>catalog.targets.find(item=>item.target.gameId===id&&item.target.id===catalog.defaultTarget)||catalog.targets.find(item=>item.target.gameId===id));
  const revisions=catalog.targets.filter(item=>item.target.gameId===current.gameId);
  for(const [name,choices] of [['Game ID',games],['Disc revision',revisions]]){
    const gamePicker=name==='Game ID';
    const options=choices.map(item=>{
      const url=new URL(project.href,location.origin);url.searchParams.set('target',item.target.id);
      return {value:gamePicker?item.target.gameId:item.target.id,label:gamePicker?item.target.gameId:'Rev '+item.target.discRevision,
        ...(gamePicker?{region:item.target.region,ariaLabel:item.target.gameId+' · '+item.target.region}:{}),href:url.pathname+url.search};
    });
    const picker=createDropdown({id:'target-'+(gamePicker?'game':'revision'),label:name,className:'target-picker',triggerClass:'target-trigger',menuClass:'target-menu',
      value:gamePicker?current.gameId:current.id,options,scope,selectedLeading:gamePicker,
      ariaLabel:gamePicker?'Game ID: '+current.gameId+' · '+current.region:'Disc revision: Rev '+current.discRevision});
    wrapper.append(picker.node);
  }
  parent.append(wrapper);return scope;
}
