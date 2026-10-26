#!/usr/bin/env python3
"""Refresh changed approved reports using already validated site code."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

from reporting.github import GitHub
from reporting.registry import producer, registrations, site_config, snapshot_path
from reporting.state import read_lock
from reporting.validation import ROOT, SHA, decode, require


def successful_site_source(root, revision, api=None):
    require(SHA.fullmatch(revision), 'Invalid site source revision')
    api = api or GitHub(site_config(root)['repository'])
    rows = api.get('actions/workflows/site.yml/runs?branch=main&status=success&head_sha='+revision+'&per_page=10')['workflow_runs']
    return any(run['head_sha'] == revision and run['head_branch'] == 'main'
               and run['event'] in ('push','schedule','workflow_dispatch') and run['status'] == 'completed'
               and run['path'] == '.github/workflows/site.yml' and run['conclusion'] == 'success' for run in rows)


def validate_notification(root, event, api_factory=GitHub):
    require(set(event.get('client_payload', {})) == {'project','repository','runId'}, 'Unknown notification fields')
    payload = event['client_payload']
    slug = payload['project']
    require(isinstance(slug, str) and slug in registrations(root), 'Unknown notification project')
    policy = producer(root, slug)
    require(policy['format'] == 'report-v1' and 'freeze' not in policy, 'Producer is not accepting report events')
    require(payload['repository'] == policy['repository'] and type(payload['runId']) is int
            and 0 < payload['runId'] < 2**63, 'Invalid notification identity')
    run = api_factory(policy['repository']).get('actions/runs/'+str(payload['runId']))
    require(run['id'] == payload['runId'] and run['status'] == 'completed' and run['conclusion'] == 'success'
            and run['head_branch'] == policy['branch'] and run['event'] in ('push','workflow_dispatch')
            and run['path'] == policy['workflow'] and run['head_repository']['full_name'] == policy['repository']
            and SHA.fullmatch(run['head_sha']), 'Notification is not a successful registered main workflow')
    return slug


def accepted_hint(root, api=None):
    api = api or GitHub(site_config(root)['repository'])
    entry = api.get('contents/data/reports.lock.json?ref=report-data')
    require(entry.get('encoding') == 'base64', 'Unexpected durable lock encoding')
    lock = decode(base64.b64decode(entry['content']))
    require(set(lock) == {'schemaVersion','projects'} and lock['schemaVersion'] == 1
            and isinstance(lock['projects'], dict), 'Invalid durable report lock')
    for slug, item in lock['projects'].items():
        producer(root, slug)
        snapshot_path(slug, item)
    return lock


def installed_run(entry):
    match = re.fullmatch(r'data/([a-z0-9]+(?:-[a-z0-9]+)*)/snapshots/([a-f0-9]{40})-v1-(\d+)-(\d+)(?:-g\d+-[a-f0-9]{12})?',entry['path'])
    require(match and match[2] == entry['revision'], 'Durable snapshot identity differs')
    snapshot_path(match[1],entry)
    return int(match[3]), int(match[4])


def changed_runs(root, lock, api_factory=GitHub):
    changed, failures = {}, []
    for slug in registrations(root):
        policy = producer(root, slug)
        if policy.get('freeze') or policy['format'] != 'report-v1':
            continue
        try:
            api = api_factory(policy['repository'])
            rows = api.get('actions/workflows/'+quote(policy['workflow'].rsplit('/',1)[-1],safe='')+
                           '/runs?branch='+quote(policy['branch'],safe='')+'&status=success&per_page=10')['workflow_runs']
            # Ignore PR runs even if their branch happened to be named main.
            run = next((r for r in rows if r['event'] in ('push','workflow_dispatch') and
                        r['head_branch'] == policy['branch'] and r['conclusion'] == 'success'), None)
            require(run is not None, 'No successful producer publication')
            previous = lock['projects'].get(slug)
            if previous is None or installed_run(previous) != (run['id'], run['run_attempt']):
                changed[slug] = run['id']
        except Exception as error:
            failures.append({'project':slug,'error':str(error)[:1000]})
    return changed, failures


def refresh_changed(root, runs, failures, refresh=None):
    from import_reports import refresh as standard_refresh
    refresh = refresh or standard_refresh
    for slug, run_id in runs.items():
        try:
            refresh(root, slug, run_id)
        except Exception as error:
            failures.append({'project':slug,'error':str(error)[:1000]})
    return failures


def live_lock(root):
    settings = decode((Path(root)/'config/report-refresh.json').read_bytes())
    require(set(settings) == {'schemaVersion','siteUrl'} and settings['schemaVersion'] == 1, 'Invalid refresh config')
    url = settings['siteUrl']
    # The URL is site-owned configuration, never selected by a notification.
    require(isinstance(url, str) and re.fullmatch(r'https://[A-Za-z0-9.-]+(?:/[A-Za-z0-9_-]+)*/',url), 'Invalid public site URL')
    with urlopen(Request(url+'data/reports.lock.json',headers={'Cache-Control':'no-cache'}),timeout=20) as response:
        raw = response.read(1024*1024+1)
    require(len(raw) <= 1024*1024, 'Public report lock too large')
    return decode(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/report-refresh.json')
    args = parser.parse_args()
    event_name = os.environ.get('GITHUB_EVENT_NAME')
    require(os.environ.get('GITHUB_REPOSITORY') == site_config()['repository']
            and os.environ.get('GITHUB_REF') == 'refs/heads/main'
            and event_name in ('repository_dispatch','workflow_dispatch','schedule'), 'Report refresh runs only on trusted site main')
    from report_store import git, restore
    revision = git(ROOT,'rev-parse','HEAD').decode().strip()
    if event_name == 'repository_dispatch':
        event = decode(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes())
        require(event.get('action') == 'producer-report-ready', 'Unknown report event')
        validate_notification(ROOT,event)
    result = {'siteRevision':revision,'publish':False,'failures':[],'changed':{}}
    if not successful_site_source(ROOT,revision):
        result['deferred'] = 'Current site main has not completed its normal validation/deployment; retry after it succeeds.'
    else:
        hint = accepted_hint(ROOT)
        runs, failures = changed_runs(ROOT,hint)
        try:
            public = live_lock(ROOT)
        except Exception:
            public = None
        if runs or public != hint:
            # Authentication, ancestry, history and schema validation remain in
            # the shared importer/store. A failure retains that producer's pointer.
            restore(ROOT)
            refresh_changed(ROOT,runs,failures)
            selected = read_lock(ROOT)
            result['publish'] = selected != public
        result.update(changed=runs,failures=failures)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as output:
            output.write('publish='+str(result['publish']).lower()+'\n')
            output.write('site_revision='+revision+'\n')
            output.write('policy_projects='+json.dumps(sorted({x['project'] for x in result['failures']}))+'\n')
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as summary:
            summary.write('## Changed report refresh\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n')
    print(json.dumps(result))


if __name__ == '__main__':main()
