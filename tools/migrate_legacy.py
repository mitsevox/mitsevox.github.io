#!/usr/bin/env python3
"""One-shot: copy a game's accepted report from the report-data branch into a schema-1 data tree.

Reads the lock and the selected snapshot (manifest, timeline, map) at --ref, the presentation from
config/projects.json, and writes data/<slug>/{game.json,cover.webp,<target>/{latest,history,map}.json}
plus index.json. Every history row keeps its revision, time and code/data total and linked bytes
exactly, with the old provenance under `legacy`; the script re-reads what it wrote and refuses to
finish unless every row equals its source and the tree passes publish.py check.

Deleted with the old pipeline once every game publishes schema 1 itself.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/actions/publish'))
import publish  # noqa: E402
from publish import ContractError, require, write_json  # noqa: E402


def show(ref, path):
    return subprocess.run(['git', '-C', str(ROOT), 'show', '%s:%s' % (ref, path)],
                          check=True, capture_output=True).stdout


def load(ref, path):
    return json.loads(show(ref, path))


def targets_for(project, manifest):
    if 'targetRegistry' in project:
        return publish.load_targets(ROOT / 'config' / project['targetRegistry'])
    # Single-target report-v1 games: the manifest's identity is the only target.
    t = manifest['target']
    return [{'id': t['id'], 'platform': t['console'].lower(), 'label': t['id'], 'region': None,
             'revision': None, 'sha1': t['sha1'], 'status': 'active'}], t['id']


def measures(m):
    return {'total': m['totalBytes'], 'linked': m['linkedBytes'], 'matched': m['matchedBytes'],
            'fuzzy': m['fuzzyEquivalentBytes']}


def counts(c):
    return None if c is None else {k: c.get(k) for k in ('total', 'exact', 'named')}


def latest_document(slug, target, manifest, entry):
    commit = entry['latestCommit']
    run = manifest['validation']['runId']
    return {'schema': 1, 'game': slug, 'target': target,
            'source': {'revision': manifest['revision'],
                       'committedAt': publish.datetime.datetime.fromisoformat(commit['date'].replace('Z', '+00:00'))
                       .astimezone(publish.datetime.timezone.utc).strftime(publish.TIME),
                       'title': commit['title'], 'url': commit['url'],
                       'runUrl': 'https://github.com/%s/actions/runs/%s' % (manifest['repository'], run)},
            'measuredAt': manifest['measuredAt'],
            'tools': [{'name': t['name'], 'version': t['identity']} for t in manifest['tools']],
            'summary': {'code': measures(manifest['summary']['code']), 'data': measures(manifest['summary']['data']),
                        'functions': counts(manifest['summary']['functions']),
                        'files': counts(manifest['summary']['files'])},
            'modules': {'map': 'map.json', 'contributors': None}}


def history_rows(timeline):
    return [{'revision': r['revision'], 'measuredAt': r['built_at'],
             'code': {'total': r['code']['total'], 'linked': r['code']['linked'], 'matched': None, 'fuzzy': None},
             'data': {'total': r['data']['total'], 'linked': r['data']['linked'], 'matched': None, 'fuzzy': None},
             'functions': None, 'legacy': {'provenance': r['provenance']}}
            for r in timeline['snapshots']]


def verify(tree, slug, target, timeline):
    """Row-for-row equality with the source timeline, read back from disk."""
    rows = json.loads((tree / 'data' / slug / target / 'history.json').read_text())
    source = timeline['snapshots']
    require(len(rows) == len(source), '%s/%s: %d rows written, %d in the source' % (slug, target, len(rows), len(source)))
    for row, old in zip(rows, source):
        require(row['revision'] == old['revision'] and row['measuredAt'] == old['built_at']
                and row['legacy']['provenance'] == old['provenance']
                and all(row[k][f] == old[k][f] for k in ('code', 'data') for f in ('total', 'linked')),
                '%s/%s: row %s differs from its source' % (slug, target, old['revision']))
    return len(rows)


def migrate(slug, tree, ref):
    tree = Path(tree)
    lock = load(ref, 'data/reports.lock.json')['projects']
    require(slug in lock, '%s is not in the lock at %s' % (slug, ref))
    project = next(p for p in json.loads((ROOT / 'config/projects.json').read_text()) if p['slug'] == slug)
    entries = lock[slug]['targets'] if 'targets' in lock[slug] else None
    first = next(iter(entries.values())) if entries else lock[slug]
    targets, default = targets_for(project, load(ref, first['path'] + '/manifest.json'))
    entries = entries or {default: lock[slug]}

    site = {k: project[k] for k in ('slug', 'title', 'shortTitle', 'console', 'year', 'contributions') if k in project}
    artwork = project.get('artwork')
    if artwork:
        cover = tree / 'data' / slug / 'cover.webp'
        cover.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / artwork['cover'].lstrip('/'), cover)
        site['artwork'] = {'cover': 'cover.webp', 'width': artwork['width'], 'height': artwork['height']}
    game = publish.game_document(site, targets, default, project['repository'])
    write_json(tree / 'data' / slug / 'game.json', game)

    report = []
    for target, entry in entries.items():
        manifest = load(ref, entry['path'] + '/manifest.json')
        timeline = load(ref, entry['path'] + '/timeline.json')
        map_doc = load(ref, entry['path'] + '/map.json')
        map_doc['schema'] = 1
        map_doc.pop('schemaVersion', None)
        directory = tree / 'data' / slug / target
        write_json(directory / 'history.json', history_rows(timeline), rows=True)
        write_json(directory / 'map.json', map_doc, compact=True)
        latest = latest_document(slug, target, manifest, entry)
        if manifest['modules'].get('contributors', {}).get('status') == 'supported':
            contributors = load(ref, entry['path'] + '/contributors.json')
            contributors['schema'] = contributors.pop('schemaVersion')
            write_json(directory / 'contributors.json', contributors, compact=True)
            latest['modules']['contributors'] = 'contributors.json'
        write_json(directory / 'latest.json', latest)
        report.append((target, verify(tree, slug, target, timeline)))

    index_path = tree / 'index.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {'schema': 1, 'games': []}
    index['games'] = sorted(set(index['games']) | {slug})
    write_json(index_path, index)
    publish.check_tree(tree)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('slug')
    parser.add_argument('--output', required=True, help='data repository checkout to write into')
    parser.add_argument('--ref', default='origin/report-data')
    args = parser.parse_args()
    try:
        for target, rows in migrate(args.slug, args.output, args.ref):
            print('%s/%s: %d history rows, identical to the source timeline' % (args.slug, target, rows))
    except (ContractError, subprocess.CalledProcessError, KeyError, StopIteration) as error:
        sys.exit('migrate_legacy: %s' % error)


if __name__ == '__main__':
    main()
