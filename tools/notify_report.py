"""Embedded into the pinned notifier workflow; never check out producer code."""
import json
import os
from pathlib import Path
import re


def notification(event, project, repository, branch, workflow, site):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',project):
        raise ValueError('Invalid project slug')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',site):
        raise ValueError('Invalid site repository')
    run=event.get('workflow_run',{})
    if not (event.get('action')=='completed' and event.get('repository',{}).get('full_name')==repository
            and run.get('head_repository',{}).get('full_name')==repository
            and run.get('head_branch')==branch and run.get('path')==workflow
            and run.get('event') in ('push','workflow_dispatch')
            and run.get('status')=='completed' and run.get('conclusion')=='success'
            and type(run.get('id')) is int and 0<run['id']<2**63):
        raise ValueError('Only the registered successful same-repository main workflow may notify')
    return {'event_type':'producer-report-ready','client_payload':{
        'project':project,'repository':repository,'runId':run['id']}}


def main():
    payload=notification(json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()),
        os.environ['PROJECT'],os.environ['GITHUB_REPOSITORY'],os.environ['PRODUCER_BRANCH'],
        os.environ['PRODUCER_WORKFLOW'],os.environ['SITE_REPOSITORY'])
    path=Path(os.environ['RUNNER_TEMP'])/'report-notification.json'
    path.write_text(json.dumps(payload))
    with open(os.environ['GITHUB_OUTPUT'],'a') as output:
        owner,name=os.environ['SITE_REPOSITORY'].split('/')
        output.write('site_owner='+owner+'\nsite_name='+name+'\n')


if __name__=='__main__':main()
