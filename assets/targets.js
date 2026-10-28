import {createDropdown} from './components/ui/dropdown.js';
import {pageScope} from './lifecycle.js';

// A project viewed at one target. Only that target's measurements are ever shown under it.
export function withTarget(project, id) {
  const target = project.targets.find(item => item.id === id) || null;
  const report = target ? project.reports[id] : null;
  const s = report?.summary;
  const counted = c => !!(c && c.exact !== null && c.named !== null);
  return {
    ...project, target:id, selectedTarget:target, unknownTarget:!target, available:!!report, report,
    targetSha1:target?.sha1, reportBase:report ? `${project.base}${id}/` : null,
    // Every game is a list of targets, so every game shows the picker, even with one entry.
    targetCatalog:target ? project.targets : null,
    modules:{map:!!report?.modules.map, timeline:!!report, contributors:!!report?.modules.contributors,
      functionCounts:counted(s?.functions), fileCounts:counted(s?.files)},
    contributionsEnabled:!!report && !!project.contributions?.accepting,
  };
}

export function selectTarget(project, url) {
  return withTarget(project, url.searchParams.get('target') || project.defaultTarget);
}

export function mountTargetPicker(parent,project) {
  const scope=pageScope();
  if (!project.targetCatalog) return scope;
  const catalog=project.targetCatalog,current=project.selectedTarget;
  const wrapper=document.createElement('div');wrapper.className='target-pickers';
  // Targets group by label (the game id on disc), then by revision.
  const labels=[...new Set(catalog.map(item=>item.label))];
  const games=labels.map(label=>catalog.find(item=>item.label===label&&item.id===project.defaultTarget)||catalog.find(item=>item.label===label));
  const revisions=catalog.filter(item=>item.label===current.label);
  for(const [name,choices] of [['Game ID',games],['Disc revision',revisions]]){
    const gamePicker=name==='Game ID';
    const options=choices.map(item=>{
      const url=new URL(project.href,location.origin);url.searchParams.set('target',item.id);
      return {value:gamePicker?item.label:item.id,label:gamePicker?item.label:'Rev '+item.revision,
        ...(gamePicker?{region:item.region,ariaLabel:item.label+' · '+item.region}:{}),href:url.pathname+url.search};
    });
    const picker=createDropdown({id:'target-'+(gamePicker?'game':'revision'),label:name,className:'target-picker',triggerClass:'target-trigger',menuClass:'target-menu',
      value:gamePicker?current.label:current.id,options,scope,selectedLeading:gamePicker,
      ariaLabel:gamePicker?'Game ID: '+current.label+' · '+current.region:'Disc revision: Rev '+current.revision});
    wrapper.append(picker.node);
  }
  parent.append(wrapper);return scope;
}
