#!/usr/bin/env python3
"""Restore and append verified data on the site's dedicated report-data branch."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

from reporting.validation import ROOT, PACKAGE_FILES, decode, digest, encoded, require, validate_package
from reporting.github import GitHub
from import_nfl import check_update, install

BRANCH = 'report-data'
LOCK = 'data/reports.lock.json'
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


def stored_package(root, head):
    lock = decode(git(root, 'show', head+':'+LOCK))
    require(lock.get('schemaVersion') == 1 and set(lock['projects']) == {'nflstreet2'}, 'Unknown store contract')
    entry = lock['projects']['nflstreet2']
    path = entry['path']
    require(re.fullmatch(r'data/nflstreet2/snapshots/[a-f0-9]{40}-v1-\d+-\d+', path), 'Unsafe stored path')
    # Read a bounded, exact set of blobs. Never check out or execute branch contents.
    rows = git(root, 'ls-tree', '-r', head, '--', path).decode().splitlines()
    require(len(rows) == len(PACKAGE_FILES), 'Unexpected stored payloads')
    payloads = {}
    for row in rows:
        mode, kind, oid, name = row.split(maxsplit=3)
        require(mode == '100644' and kind == 'blob' and name.rsplit('/',1)[0] == path
                and name.rsplit('/',1)[1] in PACKAGE_FILES, 'Unsafe stored entry')
        require(int(git(root, 'cat-file', '-s', oid)) <= 32*1024*1024, 'Stored payload too large')
        payloads[name.rsplit('/',1)[1]] = git(root, 'cat-file', 'blob', oid)
    require(digest(payloads['manifest.json']) == entry['manifestSha256'], 'Stored manifest checksum differs')
    with tempfile.TemporaryDirectory() as temp:
        for name, raw in payloads.items():
            (Path(temp)/name).write_bytes(raw)
        manifest, _, activity = validate_package(temp)
    require(manifest['revision'] == entry['revision'], 'Stored revision differs')
    return entry, manifest, activity, payloads


def restore(root):
    head = remote_head(root)
    if head is None:
        print('No report store yet; using the reviewed bootstrap package.')
        return
    entry, manifest, activity, payloads = stored_package(root, head)
    api = GitHub('mitsevox/nflstreet2')
    local_lock = root/LOCK
    if local_lock.exists():
        local_entry = decode(local_lock.read_bytes())['projects']['nflstreet2']
        directory = root/local_entry['path']
        require(directory.resolve().is_relative_to((root/'data/nflstreet2/snapshots').resolve()), 'Unsafe local path')
        require(digest((directory/'manifest.json').read_bytes()) == local_entry['manifestSha256'], 'Local manifest differs')
        local, _, local_activity = validate_package(directory)
        require(local['revision'] == local_entry['revision'], 'Local revision differs')
        if local['revision'] != manifest['revision']:
            relation = api.get(f"compare/{manifest['revision']}...{local['revision']}")['status']
            if relation == 'ahead':
                check_update(manifest, local, activity, local_activity, relation)
                print('Retaining newer reviewed local package.')
                return
            require(relation == 'behind', 'Local and stored reports diverge')
    install(root, api, manifest, payloads, entry['latestCommit'])
    print('Restored durable report store at', head)


def require_current_main(root):
    require(os.environ.get('GITHUB_REPOSITORY') == 'mitsevox/mitsevox.github.io'
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
    lock = decode((site/LOCK).read_bytes())
    require(lock.get('schemaVersion') == 1 and set(lock['projects']) == {'nflstreet2'}, 'Unknown publication contract')
    entry = lock['projects']['nflstreet2']
    require(re.fullmatch(r'data/nflstreet2/snapshots/[a-f0-9]{40}-v1-\d+-\d+', entry['path']), 'Unsafe publication path')
    directory = site/entry['path']
    manifest, _, activity = validate_package(directory)
    require(digest((directory/'manifest.json').read_bytes()) == entry['manifestSha256']
            and manifest['revision'] == entry['revision'], 'Publication lock differs')
    parent = remote_head(root)
    if parent:
        old_entry, old, old_activity, _ = stored_package(root, parent)
        relation = 'identical' if old['revision'] == manifest['revision'] else GitHub('mitsevox/nflstreet2').get(
            f"compare/{old['revision']}...{manifest['revision']}")['status']
        check_update(old, manifest, old_activity, activity, relation)
    files = {entry['path']+'/'+name:(directory/name).read_bytes() for name in PACKAGE_FILES}
    files[LOCK] = encoded(lock)
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
