#!/usr/bin/env python3
"""Propose reviewed producer-policy changes; never execute producer code or merge PRs."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote

from reporting.github import GitHub
from reporting.registry import producer, registration, registrations, site_config
from reporting.targets import selected, select
from reporting.state import read_lock
from reporting.validation import ROOT, SHA, decode, digest, encoded, require, schema

MAX_SOURCE = 256 * 1024


def command(args, cwd=None, env=None):
    return subprocess.check_output(args, cwd=cwd, text=True, env=env).strip()


def git(root, *args):
    return command(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(root), *args])


def source_path(value):
    require(isinstance(value, str) and len(value) <= 240 and
            re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', value) and
            all(p not in ('.', '..') for p in value.split('/')), 'Unsafe producer policy path')
    return value


def sources(root):
    config = decode((Path(root)/'config/policy-sync.json').read_bytes())
    require(set(config) == {'schemaVersion', 'projects'} and config['schemaVersion'] == 1
            and isinstance(config['projects'], dict), 'Invalid policy-sync configuration')
    registered = registrations(root)
    def check(item):
        if set(item)=={'disabled'}:
            require(isinstance(item['disabled'],str) and item['disabled'].strip(),'Missing disabled reason')
        else:
            require(set(item)=={'policyPath','mode'} and item['mode'] in ('policy','template'),'Invalid sync source')
            source_path(item['policyPath'])
    for slug,item in config['projects'].items():
        require(slug in registered,'Unregistered sync source')
        if 'targets' in registered[slug]:
            require(set(item)=={'targets'} and set(item['targets'])<=set(registered[slug]['targets']),'Unregistered target sync source')
            for value in item['targets'].values():check(value)
        else:
            require(registered[slug]['format']=='report-v1','Unregistered sync source');check(item)
    return config['projects']


def remote_file(api, path, revision):
    source_path(path)
    require(SHA.fullmatch(revision), 'Source must be pinned to a full Git revision')
    entry = api.get('contents/'+quote(path, safe='/')+'?ref='+revision)
    require(entry.get('type') == 'file' and entry.get('encoding') == 'base64'
            and type(entry.get('size')) is int and 0 < entry['size'] <= MAX_SOURCE, 'Missing, oversized or unsafe policy source')
    require(isinstance(entry.get('content'), str) and len(entry['content']) <= MAX_SOURCE * 2, 'Oversized source encoding')
    raw = base64.b64decode(entry['content'], validate=False)
    require(len(raw) == entry['size'], 'Source size differs')
    blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    require(blob == entry['sha'], 'Source Git blob differs')
    return raw, blob


def proposed_policy(raw, old_raw, blob, mode):
    require(mode in ('policy', 'template'), 'Unknown policy source mode')
    value, old = decode(raw), decode(old_raw)
    if mode == 'template':
        require('workflowBlobs' not in value, 'Template mode requires an explicit hash-free template')
        value['workflowBlobs'] = list(dict.fromkeys([*old['workflowBlobs'], blob]))
        raw = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    require(type(value.get('schemaVersion')) is int and value['schemaVersion'] in (1,2),'Unknown policy version')
    schema(value,'producer-v'+str(value['schemaVersion'])+'.schema.json')
    require(value['repository'] == old['repository'] and value['target'] == old['target'],
            'Repository/target changes require manual registration')
    require(blob in value['workflowBlobs'], 'Producer policy does not approve its current workflow blob')
    # A complete policy is copied verbatim. Templates have no formatting-sync requirement.
    if mode == 'template' and value == old:
        raw = old_raw
    return raw


def inspect_source(root, slug, item, api=None,target=None):
    current = producer(root,slug,target)
    registered,_ = registration(root,slug,target)
    require('freeze' not in registered and 'pending' not in registered, 'Producer migration/freeze needs manual review')
    api = api or GitHub(current['repository'])
    revision = api.get('commits/'+quote(current['branch'], safe=''))['sha']
    require(SHA.fullmatch(revision), 'Invalid producer main revision')
    raw, _ = remote_file(api, item['policyPath'], revision)
    value = decode(raw)
    # Validate the workflow path before using producer-controlled input in an API URL.
    require(isinstance(value, dict) and re.fullmatch(r'\.github/workflows/[A-Za-z0-9_-]+\.ya?ml', value.get('workflow', '')),
            'Invalid producer workflow path')
    _, blob = remote_file(api, value['workflow'], revision)
    old_path = Path(root)/'config'/registered['policy']
    old_raw = old_path.read_bytes()
    candidate = proposed_policy(raw, old_raw, blob, item['mode'])
    return {'raw':candidate, 'old':old_raw, 'revision':revision, 'workflowBlob':blob,
            'key':digest(old_raw+b'\0'+candidate)[:16]}


def apply_policy(root, slug, raw,target=None):
    root = Path(root)
    registry = registrations(root)
    item = registry[slug]['targets'][target] if target else registry[slug]
    active = root/'config'/item['policy']
    previous = active.read_bytes()
    if previous == raw:
        return []
    archive_name = f'{slug}'+('-'+target if target else '')+f'-producer-{digest(previous)[:16]}.json'
    archive = root/'config'/archive_name
    require(not archive.is_symlink() and (not archive.exists() or archive.read_bytes() == previous), 'Policy archive collision')
    archive.write_bytes(previous)
    reference = {'format':item['format'], 'policy':archive_name}
    if reference not in item.setdefault('archives', []):
        item['archives'].append(reference)
    active.write_bytes(raw)
    (root/'config/producers.json').write_text(json.dumps(registry, indent=2)+'\n')
    return [str(active.relative_to(root)), 'config/'+archive_name, 'config/producers.json',
            'data/reports.lock.json', 'data/'+slug+('/targets/'+target if target else '')]


def prepare_candidate(root, slug, item, info, candidate, output,target=None):
    from import_reports import refresh
    from report_store import restore
    from build_site import build
    site = site_config(root)['repository']
    command(['git', 'clone', '--no-hardlinks', '--quiet', str(root), str(candidate)])
    git(candidate, 'remote', 'set-url', 'origin', 'https://github.com/'+site+'.git')
    require(git(candidate, 'rev-parse', 'HEAD') == git(root, 'rev-parse', 'HEAD'), 'Candidate source differs')
    baseline = read_lock(candidate)
    restore(candidate)
    restored = read_lock(candidate)
    entry=selected(restored,slug,target)
    if entry:select(baseline,slug,target,entry)
    # Durable state for the selected producer is needed for proof reuse. Other
    # producers stay byte-for-byte at this PR's base, not incidental refreshes.
    (candidate/'data/reports.lock.json').write_bytes(encoded(baseline))
    paths = apply_policy(candidate,slug,info['raw'],target)
    destination = refresh(candidate,slug,target=target) if target else refresh(candidate,slug)
    manifest = decode((destination/'manifest.json').read_bytes())
    require(manifest['validation']['mode'] == 'full' or manifest['validation']['mode'] == 'reused', 'Unknown execution lane')
    measured_raw, _ = remote_file(GitHub(manifest['repository']), item['policyPath'], manifest['revision'])
    measured_blob = decode((destination/'receipt.json').read_bytes())['workflowBlob']
    measured = proposed_policy(measured_raw, info['old'], measured_blob, item['mode'])
    require(decode(measured) == decode(info['raw']), 'Successful package was produced under a different policy')
    build(candidate, candidate/'build/policy-sync-site')
    git(candidate, 'add', '--', *paths)
    staged = git(candidate, 'diff', '--cached', '--name-only').splitlines()
    require(staged and all(path in paths or path.startswith('data/'+slug+('/targets/'+target if target else '')+'/snapshots/') for path in staged),
            'Proposal contains changes outside the selected producer')
    after = read_lock(candidate)
    original = read_lock(root)
    require(all(after['projects'].get(name) == entry for name, entry in original['projects'].items() if name != slug),
            'Proposal changed another producer')
    if target:
        before=(original['projects'].get(slug) or {}).get('targets',{})
        after_targets=(after['projects'].get(slug) or {}).get('targets',{})
        require(all(after_targets.get(key)==entry for key,entry in before.items() if key!=target),'Proposal changed another target')
    output.mkdir(parents=True, exist_ok=True)
    patch = subprocess.check_output(['git', '-C', str(candidate), 'diff', '--cached', '--binary'])
    (output/'proposal.patch').write_bytes(patch)
    return manifest


def existing_proposal(site, branch):
    rows = json.loads(command(['gh','pr','list','--repo',site,'--head',branch,'--state','all',
                               '--json','url,state,baseRefName,headRepositoryOwner,isCrossRepository']))
    if not rows:
        # Never overwrite an occupied branch, including one edited by a person.
        remote = command(['git','ls-remote','--heads','https://github.com/'+site+'.git','refs/heads/'+branch])
        require(not remote, 'Proposal branch already exists without a matching PR; inspect manually')
        return None
    require(len(rows) == 1 and rows[0]['baseRefName'] == 'main' and not rows[0]['isCrossRepository'], 'Ambiguous policy proposal')
    return rows[0]


def sync_one(root, slug, item, output, propose=False,target=None):
    if 'disabled' in item:
        return {'project':slug, 'status':'disabled', 'reason':item['disabled']}
    info = inspect_source(root,slug,item,target=target) if target else inspect_source(root,slug,item)
    if info['raw'] == info['old']:
        return {'project':slug, 'status':'unchanged'}
    site = site_config(root)['repository']
    branch = 'codex/policy-sync/'+slug+('/'+target if target else '')+'/'+info['key']
    existing = existing_proposal(site, branch) if propose else None
    if existing:
        return {'project':slug, 'status':'existing-'+existing['state'].lower(), 'url':existing['url']}
    with tempfile.TemporaryDirectory(prefix='policy-sync-') as temp:
        candidate = Path(temp)/'candidate'
        location=output/slug/(target or 'single')/info['key']
        manifest=prepare_candidate(root,slug,item,info,candidate,location,target) if target else prepare_candidate(root,slug,item,info,candidate,location)
        body = ('Update the registered policy for `'+slug+'` from its tracked producer source.\n\n'
                '- Producer policy inspected at `'+info['revision']+'`.\n'
                '- Current workflow blob: `'+info['workflowBlob']+'`.\n'
                '- Authenticated report: `'+manifest['revision']+'`, run '+str(manifest['validation']['runId'])+'.\n'
                '- Standard import, history checks and static site build passed.\n'
                '- Previous policy is archived; other project pointers are unchanged.\n\n'
                'Review the policy diff and producing workflow before merging. This automation never approves or merges.\n')
        if os.getenv('GITHUB_RUN_ID'):
            body += '\n[Validation run](https://github.com/'+site+'/actions/runs/'+os.environ['GITHUB_RUN_ID']+')\n'
        body_file=location/'pr-body.md'
        body_file.write_text(body)
        if not propose:
            return {'project':slug, 'status':'validated-dry-run', 'patch':str(body_file.parent/'proposal.patch')}
        git(candidate, '-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
            'commit', '-qm', 'Propose '+slug+' producer policy '+info['key'])
        # Unique content-keyed branches are never reset or force-pushed. A rejected
        # proposal remains closed; changes to the policy get a new proposal key.
        write_env = {**os.environ, 'GH_TOKEN':os.getenv('POLICY_SYNC_WRITE_TOKEN') or os.environ.get('GH_TOKEN','')}
        command(['git','-c','core.hooksPath=/dev/null','-C',str(candidate),'push','origin','HEAD:refs/heads/'+branch], env=write_env)
        url = command(['gh','pr','create','--repo',site,'--base','main','--head',branch,
                       '--title','Sync '+slug+' producer policy','--body-file',str(body_file)], env=write_env)
        return {'project':slug, 'status':'proposed', 'url':url}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--all', action='store_true')
    choice.add_argument('--project')
    parser.add_argument('--propose', action='store_true', help='Create PRs after real import/build validation; default is dry-run')
    parser.add_argument('--output', type=Path, default=ROOT/'build/policy-sync')
    args = parser.parse_args()
    if args.propose:
        require(os.getenv('GITHUB_REPOSITORY') == site_config()['repository']
                and os.getenv('GITHUB_REF') == 'refs/heads/main'
                and os.getenv('GITHUB_EVENT_NAME') in ('schedule', 'workflow_dispatch', 'repository_dispatch'),
                'Automatic proposals run only from trusted site main')
    configured = sources(ROOT)
    require(args.project is None or args.project in configured, 'Unknown policy-sync project')
    selected = configured if args.all else {args.project:configured[args.project]}
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for slug,group in selected.items():
        targets=group['targets'].items() if 'targets' in group else [(None,group)]
        for target,item in targets:
            try:
                result=sync_one(ROOT,slug,item,args.output,args.propose,target) if target else sync_one(ROOT,slug,item,args.output,args.propose)
            except Exception as error:
                result={'project':slug,'status':'failed','reason':str(error)[:1500]}
            if target:result['target']=target
            results.append(result);print(json.dumps(result))
    (args.output/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write('## Producer policy sync\n\n```json\n'+json.dumps(results,indent=2)+'\n```\n')
    return int(any(result['status'] == 'failed' for result in results))


if __name__ == '__main__':
    raise SystemExit(main())
