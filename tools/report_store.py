#!/usr/bin/env python3
"""Restore and append verified data on the site's dedicated report-data branch."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

from reporting.validation import ROOT, decode, digest, encoded, require, validate_package
from reporting.github import GitHub
from reporting.registry import producer, registrations, site_config, snapshot_path, snapshot_directory
from reporting.state import LOCK, read_lock, check_update, install

BRANCH = 'report-data'
SHA = re.compile(r'[a-f0-9]{40}')


def git(root, *args, data=None, env=None):
    return subprocess.check_output(['git', *args], cwd=root, input=data, env=env)


def remote_head(root):
    rows = git(root, 'ls-remote', '--heads', 'origin', 'refs/heads/'+BRANCH).decode().splitlines()
    require(len(rows) <= 1, 'Ambiguous report store branch')
    if not rows:
        return None
    head = rows[0].split()[0]
    require(SHA.fullmatch(head), 'Invalid report store revision')
    git(root, 'fetch', '--no-tags', 'origin', head)
    return head


def stored_lock(root, head):
    lock=decode(git(root,'show',head+':'+LOCK))
    require(set(lock)=={'schemaVersion','projects'} and lock['schemaVersion']==1
            and isinstance(lock['projects'],dict), 'Invalid store contract')
    for slug,entry in lock['projects'].items():
        producer(root,slug)  # Older source cannot erase a newly registered project.
        snapshot_path(slug,entry)
    return lock


def stored_package(root, head, slug=None):
    lock=stored_lock(root,head)
    if slug is None:
        require(len(lock['projects'])==1,'Select a project in a multi-project store')
        slug=next(iter(lock['projects']))
    entry=lock['projects'][slug];path=snapshot_path(slug,entry)
    rows=git(root,'ls-tree','-r',head,'--',path).decode().splitlines()
    require(3<=len(rows)<=20,'Unexpected stored payload count')
    payloads={};total=0
    for row in rows:
        mode,kind,oid,name=row.split(maxsplit=3)
        require(mode=='100644' and kind=='blob' and name.rsplit('/',1)[0]==path
                and re.fullmatch(r'[A-Za-z0-9_-]+\.json',name.rsplit('/',1)[1]),'Unsafe stored entry')
        size=int(git(root,'cat-file','-s',oid));total+=size
        require(size<=32*1024*1024 and total<=80*1024*1024,'Stored payload too large')
        payloads[name.rsplit('/',1)[1]]=git(root,'cat-file','blob',oid)
    require(digest(payloads['manifest.json'])==entry['manifestSha256'],'Stored manifest checksum differs')
    with tempfile.TemporaryDirectory() as temp:
        for name,raw in payloads.items():(Path(temp)/name).write_bytes(raw)
        manifest,_,activity=validate_package(temp,root)
    require(manifest['project']==slug and manifest['revision']==entry['revision'],'Stored identity differs')
    return entry,manifest,activity,payloads


def restore(root):
    root=Path(root);head=remote_head(root)
    if head is None:
        print('No report store yet; using the reviewed bootstrap packages.')
        return
    stored=stored_lock(root,head)
    for slug in stored['projects']:
        entry,manifest,activity,payloads=stored_package(root,head,slug)
        api=GitHub(producer(root,slug)['repository'])
        local_entry=read_lock(root)['projects'].get(slug)
        if local_entry:
            directory=snapshot_directory(root,slug,local_entry)
            require(digest((directory/'manifest.json').read_bytes())==local_entry['manifestSha256'],'Local manifest differs')
            local,_,local_activity=validate_package(directory,root)
            require(local['revision']==local_entry['revision'],'Local revision differs')
            if local['revision']!=manifest['revision']:
                relation=api.get(f"compare/{manifest['revision']}...{local['revision']}")['status']
                if relation=='ahead':
                    check_update(manifest,local,activity,local_activity,relation)
                    print('Retaining newer reviewed local package:',slug)
                    continue
                require(relation=='behind','Local and stored reports diverge')
        install(root,api,manifest,payloads,entry['latestCommit'],source_proof=entry.get('sourceProof'),
                source_proofs=entry.get('sourceProofs'))
    print('Restored durable report store at',head)


def require_current_main(root):
    require(os.environ.get('GITHUB_REPOSITORY') == site_config(root)['repository']
            and os.environ.get('GITHUB_REF') == 'refs/heads/main'
            and os.environ.get('GITHUB_EVENT_NAME') in ('push','schedule','workflow_dispatch'),
            'Report publication is restricted to trusted main workflows')
    source_revision = os.environ.get('GITHUB_SHA','')
    require(SHA.fullmatch(source_revision), 'Missing publisher revision')
    rows = git(root, 'ls-remote', '--heads', 'origin', 'refs/heads/main').decode().splitlines()
    require(len(rows) == 1 and rows[0].split()[0] == source_revision, 'Publisher is no longer current site main')
    return source_revision


def publish(root, site):
    source_revision = require_current_main(root)
    lock=read_lock(site)
    require(lock['projects'],'No reports to publish')
    parent=remote_head(root)
    old_lock=stored_lock(root,parent) if parent else {'projects':{}}
    require(set(old_lock['projects'])<=set(lock['projects']),'Publication would erase a stored project')
    files={LOCK:encoded(lock)}
    for slug,entry in lock['projects'].items():
        policy=producer(root,slug);directory=snapshot_directory(site,slug,entry)
        manifest,_,activity=validate_package(directory,root)
        require(digest((directory/'manifest.json').read_bytes())==entry['manifestSha256']
                and manifest['project']==slug and manifest['revision']==entry['revision'],'Publication lock differs')
        if slug in old_lock['projects']:
            _,old,old_activity,_=stored_package(root,parent,slug)
            relation='identical' if old['revision']==manifest['revision'] else GitHub(policy['repository']).get(
                f"compare/{old['revision']}...{manifest['revision']}")['status']
            check_update(old,manifest,old_activity,activity,relation)
        files.update({entry['path']+'/'+p.name:p.read_bytes() for p in directory.iterdir()})
    with tempfile.TemporaryDirectory() as temp:
        env = {**os.environ, 'GIT_INDEX_FILE':str(Path(temp)/'index'),
               'GIT_AUTHOR_NAME':'github-actions[bot]', 'GIT_COMMITTER_NAME':'github-actions[bot]',
               'GIT_AUTHOR_EMAIL':'41898282+github-actions[bot]@users.noreply.github.com',
               'GIT_COMMITTER_EMAIL':'41898282+github-actions[bot]@users.noreply.github.com'}
        git(root, 'read-tree', parent if parent else '--empty', env=env)
        for name, raw in files.items():
            if parent and name != LOCK:
                existing = git(root,'ls-tree',parent,'--',name).decode().strip()
                if existing:
                    oid = existing.split()[2]
                    require(git(root,'cat-file','blob',oid) == raw, 'Immutable stored snapshot changed')
            oid = git(root, 'hash-object', '-w', '--stdin', data=raw).decode().strip()
            git(root, 'update-index', '--add', '--cacheinfo', '100644', oid, name, env=env)
        tree = git(root, 'write-tree', env=env).decode().strip()
        if parent and tree == git(root,'rev-parse',parent+'^{tree}').decode().strip():
            print('Report store already contains this publication.')
            return parent
        args = ['commit-tree', tree] + (['-p',parent] if parent else [])
        commit = git(root, *args, data=f'Preserve verified reports from site {source_revision}\n'.encode(), env=env).decode().strip()
        # Ordinary fast-forward push is the compare-and-swap. A concurrent
        # writer causes failure, never a forced overwrite or stale deployment.
        git(root, 'push', 'origin', commit+':refs/heads/'+BRANCH)
    print('Preserved reports at', commit)
    return commit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['restore','publish','check-current'])
    parser.add_argument('--site', type=Path, default=ROOT/'build/site')
    args = parser.parse_args()
    if args.action == 'restore':
        restore(ROOT)
    elif args.action == 'publish':
        publish(ROOT,args.site)
    else:
        require_current_main(ROOT)
