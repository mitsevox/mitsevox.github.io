import {createCommitLine} from '../components/ui/commit-line.js';
import {mountTargetPicker} from '../targets.js';
import {fetchSummary} from '../reports.js';
import {consoleIcon} from '../console-icon.js';
import {pageScope} from '../lifecycle.js';
import {createGameDossier} from '../components/ui/game-dossier.js';
import {gameEditorial} from '../game-editorial.js';
// The game heading: title, platform, target picker and latest commit.
export function mount(root,{project}){
  const scope=pageScope();
  const identity=document.createElement('div');identity.className='game-identity';
  const heading=root.querySelector('h1');heading.className='game-identity-title';heading.textContent='';
  const title=document.createElement('span');title.className='game-name';title.textContent=project.title;
  const target=document.createElement('span');target.className='game-target';target.textContent=project.target;target.setAttribute('aria-label','Game ID: '+project.target);
  heading.append(title);
  if(!project.targetCatalog)heading.append(target);
  heading.insertAdjacentHTML('afterbegin',consoleIcon(project.console));
  const headingRow=document.createElement('div');headingRow.className='game-heading-row';
  root.prepend(identity);identity.append(headingRow);headingRow.append(heading);
  const commitLine=createCommitLine({repository:project.repo,scope}),commit=commitLine.node;
  const picker=mountTargetPicker(headingRow,project);
  identity.append(commit);
  if(project.available===false){commit.remove();const message=document.createElement('p');message.className='target-unavailable';message.textContent=project.selectedTarget?.status==='archived'?'Archived revision · No validated report available.':'No validated report available.';if(project.unknownTarget){message.textContent='Unknown target. ';const recovery=document.createElement('a');recovery.href=project.href;recovery.textContent='Open the default target';message.append(recovery);}identity.append(message);}
  const dossier=createGameDossier({project,editorial:gameEditorial(project),identity,scope});
  const ready=project.available===false?Promise.resolve():fetchSummary(project, scope.signal).then(data=>{
    if(scope.signal.aborted)return;
    const latest=data.latest_commit;if(!latest?.title)throw Error();
    commitLine.update(latest);
  }).catch(()=>{if(!scope.signal.aborted)commitLine.update(null);});
  return {ready,destroy(){dossier.destroy();picker.destroy();scope.destroy();}};
}
