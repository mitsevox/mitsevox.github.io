#!/usr/bin/env python3
"""Import reports for the owner's registered repositories; no game builds."""
import argparse
from pathlib import Path
import sys
import tempfile
from urllib.parse import quote

from reporting.validation import ROOT, decode, digest, require, validate_package, timestamp
from reporting.registry import producer, registrations, snapshot_path, snapshot_directory
from reporting.github import GitHub, artifact_bytes, select_artifact, zip_members
from reporting.state import read_lock, accepted_package, install, latest_commit


def authenticate(policy,run,jobs,blob,candidate=False):
    require(run['repository']['full_name']==policy['repository'] and run['head_repository']['full_name']==policy['repository']
            and run['path']==policy['workflow'] and (candidate or run['head_branch']==policy['branch'])
            and run['event'] in (('push','workflow_dispatch','pull_request') if candidate else ('push','workflow_dispatch')) and run['status']=='completed' and run['conclusion']=='success',
            'Run is not an eligible registered publication')
    require(blob in policy['workflowBlobs'],'Producer workflow changed; review its policy')
    selected=[j for j in jobs if j['name']==policy['job']]
    require(len(selected)==1,'Missing or ambiguous producer job');job=selected[0]
    require(job['conclusion']=='success' and job['run_attempt']==run['run_attempt'] and job['head_sha']==run['head_sha'],'Wrong producer job/attempt')
    for name in policy['requiredSteps']:
        require(sum(s['name']==name and s['conclusion']=='success' for s in job['steps'])==1,'Missing producer validation step: '+name)
    return job


def execution_mode(policy,job):
    def success(name):return sum(s['name']==name and s['conclusion']=='success' for s in job['steps'])==1
    modes=[mode for mode,steps in policy['lanes'].items() if all(success(name) for name in steps)]
    require(len(modes)==1,'Ambiguous or incomplete producer validation lane')
    return modes[0]


def verify_reuse(root,api,policy,manifest,receipt):
    proof=receipt['source']
    run=api.get(f"actions/runs/{proof['runId']}/attempts/{proof['attempt']}")
    require(run['run_attempt']==proof['attempt'] and run['head_sha']==proof['revision'],'Originating proof execution differs')
    jobs=api.pages(f"actions/runs/{proof['runId']}/attempts/{proof['attempt']}/jobs",'jobs')
    blob=api.get(f"contents/{policy['workflow']}?ref={proof['revision']}")['sha']
    job=authenticate(policy,run,jobs,blob,candidate=True)
    require(execution_mode(policy,job)=='full','Originating proof is not full validation')
    artifact=api.get(f"actions/artifacts/{proof['artifactId']}")
    require(artifact['workflow_run']['id']==proof['runId'] and artifact['workflow_run']['head_sha']==proof['revision']
            and artifact['digest']=='sha256:'+proof['artifactSha256'] and artifact['name']==policy['artifact'],
            'Originating proof artifact differs')
    select_artifact([artifact],policy['artifact'],run,job)
    payloads=zip_members(artifact_bytes(api,artifact))
    with tempfile.TemporaryDirectory() as temp:
        for name,raw in payloads.items():(Path(temp)/name).write_bytes(raw)
        original,_,_=validate_package(temp,root)
    require(original['validation']['mode']=='full' and original['validation']['runId']==proof['runId']
            and original['validation']['attempt']==proof['attempt'] and original['revision']==proof['revision'],
            'Original report differs from proof')
    for key in ('project','repository','target','tree','methodology','generation','tools','summary','measuredAt'):
        require(original[key]==manifest[key],'Reused measurements differ from original: '+key)
    for module in ('map','contributors'):
        require(original['modules'][module]==manifest['modules'][module],'Reused module differs from original: '+module)
    require(api.get('git/commits/'+proof['revision'])['tree']['sha']==manifest['tree'], 'Original tested tree differs')
    require(timestamp(run['run_started_at'])<=timestamp(original['measuredAt'])<=timestamp(original['publishedAt'])<=timestamp(job['completed_at'])+1,
            'Originating measurement time differs')


def refresh(root,slug,run_id=None):
    root=Path(root);policy=producer(root,slug)
    require(run_id is None or type(run_id) is int and run_id>0,'Run ID must be a positive integer')
    if policy['format']=='nfl-legacy-v1':
        from import_nfl import refresh as legacy_refresh
        return legacy_refresh(root,run_id)
    api=GitHub(policy['repository'])
    if run_id is None:
        workflow=policy['workflow'].rsplit('/',1)[1]
        runs=api.get(f"actions/workflows/{workflow}/runs?branch={quote(policy['branch'],safe='')}&status=success&per_page=10")['workflow_runs']
        require(runs,'No successful producer publication');run_id=runs[0]['id']
    run=api.get(f'actions/runs/{run_id}')
    jobs=api.pages(f"actions/runs/{run_id}/attempts/{run['run_attempt']}/jobs",'jobs')
    blob=api.get(f"contents/{policy['workflow']}?ref={run['head_sha']}")['sha']
    job=authenticate(policy,run,jobs,blob)
    require(api.get(f"compare/{run['head_sha']}...{quote(policy['branch'],safe='')}")['status'] in ('ahead','identical'),'Measured revision is no longer eligible')
    entry=read_lock(root)['projects'].get(slug);payloads=None;cached=False
    if entry:
        directory=snapshot_directory(root,slug,entry)
        require(digest((directory/'manifest.json').read_bytes())==entry['manifestSha256'],'Cached manifest differs')
        manifest,_,_=validate_package(directory,root)
        if (manifest['validation']['runId']==run_id and manifest['validation']['attempt']==run['run_attempt']
                and manifest['revision']==run['head_sha'] and accepted_package(root,slug,entry)):
            payloads={p.name:p.read_bytes() for p in directory.iterdir()};cached=True
    if payloads is None:
        artifacts=api.pages(f'actions/runs/{run_id}/artifacts','artifacts')
        selected=select_artifact(artifacts,policy['artifact'],run,job)
        payloads=zip_members(artifact_bytes(api,selected))
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            for name,raw in payloads.items():(directory/name).write_bytes(raw)
            manifest,_,_=validate_package(directory,root)
    require(manifest['validation']['receipt']['schema']=='execution-v1','Report differs from active producer format')
    require(manifest['tools']==policy['tools'] and manifest['target']==policy['target']
            and manifest['repository']==policy['repository'],'Report differs from active producer identity/tools')
    require(manifest['revision']==run['head_sha'] and manifest['validation']['runId']==run_id
            and manifest['validation']['attempt']==run['run_attempt'],'Report belongs to another execution')
    receipt=decode(payloads['receipt.json'])
    require(receipt['workflowBlob']==blob and manifest['validation']['mode']==execution_mode(policy,job),'Receipt workflow/lane differs from GitHub')
    require(api.get('git/commits/'+run['head_sha'])['tree']['sha']==manifest['tree'],'Report tree differs from GitHub')
    require(timestamp(run['run_started_at'])<=timestamp(manifest['publishedAt'])<=timestamp(job['completed_at'])+1,'Report timestamps differ from producing execution')
    if manifest['validation']['mode']=='full':
        require(timestamp(run['run_started_at'])<=timestamp(manifest['measuredAt']),'Full measurement predates producing execution')
    elif not cached:verify_reuse(root,api,policy,manifest,receipt)
    destination=install(root,api,manifest,payloads,latest_commit(api,policy['branch']))
    print(f'Imported {slug} at {manifest["revision"]}: {destination}')
    return destination


def refresh_all(root):
    failures=[]
    for slug in registrations(root):
        try:refresh(root,slug)
        except Exception as error:
            failures.append(slug);print(f'{slug}: refresh failed: {error}',file=sys.stderr)
    return failures


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--project');choice.add_argument('--all',action='store_true')
    parser.add_argument('--run',type=int)
    args=parser.parse_args()
    if args.all:
        if args.run is not None:parser.error('--run requires --project')
        sys.exit(bool(refresh_all(ROOT)))
    refresh(ROOT,args.project,args.run)
