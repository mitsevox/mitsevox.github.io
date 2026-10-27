#!/usr/bin/env python3
"""Publish one target's objdiff report to the site's data repository (contract schema 1).

publish  objdiff report.json -> latest.json, map.json and one history row; clone the data
         repository, write, check, commit and push, retrying when another run wins
         (--dry-run writes into --output, or a temporary tree, and pushes nothing)
check    validate a whole data tree against the contract (contract/README.md)

The producer is the only writer and the only validator: everything written here is checked
before it is pushed, and the site only renders it. Standard library only.
"""
import argparse
import base64
import datetime
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = 1
TARGET_ID = re.compile(r'[A-Za-z0-9._-]+')
SLUG = re.compile(r'[a-z0-9][a-z0-9-]*')
SHA1 = re.compile(r'[0-9a-f]{40}')
SOURCE_PATH = re.compile(r'[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+)*')
# dtk names unnamed functions fn_<address>, splat names them func_<address>.
UNNAMED = r'(?:fn|func)_[0-9A-Fa-f]+'
TIME = '%Y-%m-%dT%H:%M:%SZ'


class ContractError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime(TIME)


def timestamp(value):
    # Writers emit TIME; readers accept any UTC ISO 8601 form, because imported history keeps its
    # original timestamps verbatim (some carry microseconds or +00:00).
    require(isinstance(value, str), 'Timestamp is not a string')
    try:
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError:
        raise ContractError('Timestamp is not ISO 8601: ' + value)
    require(parsed.utcoffset() == datetime.timedelta(0), 'Timestamp is not UTC: ' + value)
    return parsed


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise ContractError('%s: %s' % (path, error))


def write_json(path, document, rows=False, compact=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        # One row per line keeps history diffs readable in the data repository.
        text = '[\n' + ',\n'.join(json.dumps(r, sort_keys=True, separators=(',', ':')) for r in document) + '\n]\n'
    elif compact:
        text = json.dumps(document, sort_keys=True, separators=(',', ':')) + '\n'
    else:
        text = json.dumps(document, sort_keys=True, indent=1) + '\n'
    path.write_text(text)


# objdiff report.json -> contract measures. objdiff writes 64-bit counts as strings and leaves out
# any measure that is zero.

def num(value):
    return int(value) if value is not None else 0


def fuzzy_bytes(function):
    # Size-weighted similarity; the summary and the map use this same expression so they agree.
    return num(function.get('size')) * min(function.get('fuzzy_match_percent', 0), 100) / 100


def data_fuzzy_bytes(unit, code_sections):
    # objdiff reports a match percent per data section and rolls only 100% sections up into
    # matched_data; size-weighted, as for functions.
    return math.fsum(num(s.get('size')) * min(s.get('fuzzy_match_percent', 0), 100) / 100
                     for s in unit.get('sections', []) if s['name'] not in code_sections)


def summary(report, code_sections, unnamed=UNNAMED):
    m = report.get('measures', {})
    total_code, total_data = num(m.get('total_code')), num(m.get('total_data'))
    functions = [f for u in report.get('units', []) for f in u.get('functions', [])]
    require(len(functions) == num(m.get('total_functions')),
            'Report lists %d functions, its measures say %s' % (len(functions), m.get('total_functions')))
    exact = sum(1 for f in functions if f.get('fuzzy_match_percent', 0) >= 100)
    require(exact == num(m.get('matched_functions')),
            'Report has %d exact functions, its measures say %s' % (exact, m.get('matched_functions')))
    named = sum(1 for f in functions if not re.fullmatch(unnamed, f['name']))
    fuzzy = math.fsum(fuzzy_bytes(f) for f in functions)
    data_fuzzy = math.fsum(data_fuzzy_bytes(u, code_sections) for u in report.get('units', []))
    units = report.get('units', [])

    def auto(u):
        return u.get('metadata', {}).get('auto_generated', False)

    def complete(u):
        um = u.get('measures', {})
        return all(num(um.get('matched_' + k)) == num(um.get('total_' + k)) for k in ('code', 'data'))
    result = {
        'code': {'total': total_code, 'linked': num(m.get('complete_code')),
                 'matched': num(m.get('matched_code')), 'fuzzy': fuzzy},
        'data': {'total': total_data, 'linked': num(m.get('complete_data')),
                 'matched': num(m.get('matched_data')), 'fuzzy': data_fuzzy},
        'functions': {'total': len(functions), 'exact': exact, 'named': named},
        # A unit is a file; named = not a tool-generated address range, exact = named and fully matched.
        'files': {'total': len(units), 'exact': sum(1 for u in units if complete(u) and not auto(u)),
                  'named': sum(1 for u in units if not auto(u))},
    }
    check_summary(result)
    return result


def hexaddr(value):
    return '0x%08X' % value


def merged(ranges):
    result = []
    for start, end in sorted(ranges):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def extents(ranges):
    return [{'start': hexaddr(a), 'end': hexaddr(b)} for a, b in merged(ranges)]


def group(name, kind, children):
    # A group's measures are its children's sums; its extents are their merged ranges.
    node = {'name': name, 'kind': kind,
            'size': sum(c['size'] for c in children),
            'linked': sum(c['linked'] for c in children),
            'matched': sum(c['matched'] for c in children),
            'fuzzy': math.fsum(c['fuzzy'] for c in children)}
    node['_ranges'] = [tuple(r) for r in merged(r for c in children for r in c['_ranges'])]
    node['mapped_extents'] = extents(node['_ranges'])
    node['children'] = children
    return node


def map_document(report, code_sections, unit_prefix='main/'):
    """Every function as a tile, grouped by source unit (`files`, what the page draws) and by
    section (`sections`, a cross-check over the same bytes). A unit's data is one tile spanning
    its data sections, because objdiff rolls exact data matches up per unit."""
    code_by_section = {name: [] for name in code_sections}
    files, data_tiles = [], []
    for unit in report.get('units', []):
        m, md = unit.get('measures', {}), unit.get('metadata', {})
        name = unit['name'][len(unit_prefix):] if unit_prefix and unit['name'].startswith(unit_prefix) else unit['name']
        complete = bool(md.get('complete'))
        sections = [(s['name'], int(s['metadata']['virtual_address']), num(s.get('size')))
                    for s in unit.get('sections', []) if num(s.get('size'))]
        functions = []
        for f in unit.get('functions', []):
            start, size = int(f['metadata']['virtual_address']), num(f.get('size'))
            exact = f.get('fuzzy_match_percent', 0) >= 100
            leaf = {'name': f['name'], 'kind': 'code', 'type': 'function',
                    'address': hexaddr(start), 'size': size,
                    'linked': size if complete else 0, 'matched': size if exact else 0,
                    'fuzzy': fuzzy_bytes(f),
                    'function_address': hexaddr(start), 'original_size': size,
                    '_ranges': [(start, start + size)]}
            functions.append(leaf)
            section = next((s for s, a, n in sections if s in code_sections and a <= start < a + n), None)
            require(section is not None, '%s: %s lies outside the code sections %s'
                    % (name, f['name'], ', '.join(code_sections)))
            code_by_section[section].append(dict(leaf))
        if functions:
            files.append(group(name, 'code', functions))
        data = [(a, a + n) for s, a, n in sections if s not in code_sections]
        total_data = num(m.get('total_data'))
        if total_data:
            require(sum(b - a for a, b in data) == total_data, '%s: data sections do not add up to total_data' % name)
            tile = {'name': name, 'kind': 'data', 'size': total_data,
                    'linked': total_data if complete else 0, 'matched': num(m.get('matched_data')),
                    'fuzzy': data_fuzzy_bytes(unit, code_sections),
                    'mapped_extents': extents(data), '_ranges': data}
            files.append(tile)
            data_tiles.append(dict(tile))
    # The page draws tiles in list order: keep them in address order.
    files.sort(key=lambda f: min(f['_ranges']))
    sections = [group(s, 'code', sorted(fs, key=lambda f: f['_ranges'][0])) for s, fs in code_by_section.items() if fs]
    if data_tiles:
        sections.append(group('Data sections', 'data', sorted(data_tiles, key=lambda t: t['_ranges'][0])))

    def strip(node):
        node.pop('_ranges', None)
        for child in node.get('children', []):
            strip(child)
        return node
    return {'schema': SCHEMA, 'sections': [strip(s) for s in sections], 'files': [strip(f) for f in files]}


# Producer configuration -> game.json.

def load_targets(path):
    document = read_json(path)
    require(isinstance(document, dict) and isinstance(document.get('targets'), list) and document['targets'],
            'targets.json lists no targets')
    targets = []
    for entry in document['targets']:
        if 'target' in entry:
            # Transitional: the nested registry shape (gameId/discRevision) predating schema 1.
            t = entry['target']
            entry = {'id': t['id'], 'platform': t['platform'], 'label': t['gameId'], 'region': t.get('region'),
                     'revision': str(t['discRevision']), 'sha1': t['sha1'], 'status': entry['status']}
        targets.append({k: entry.get(k) for k in ('id', 'platform', 'label', 'region', 'revision', 'sha1', 'status')})
    default = document.get('defaultTarget', targets[0]['id'])
    check_targets(targets, default)
    return targets, default


def check_targets(targets, default):
    ids = [t['id'] for t in targets]
    require(len(set(ids)) == len(ids), 'Duplicate target id')
    require(default in ids, 'Default target is not listed')
    for t in targets:
        require(isinstance(t['id'], str) and TARGET_ID.fullmatch(t['id']), 'Invalid target id %r' % t['id'])
        require(isinstance(t['platform'], str) and t['platform'] and t['platform'] == t['platform'].lower(),
                '%s: platform must be a lower-case name' % t['id'])
        require(isinstance(t['sha1'], str) and SHA1.fullmatch(t['sha1']), '%s: sha1 must be 40 lower-case hex digits' % t['id'])
        require(t['status'] in ('active', 'planned', 'archived'), '%s: status must be active, planned or archived' % t['id'])
        for key in ('label', 'region', 'revision'):
            require(t[key] is None or isinstance(t[key], str), '%s: %s must be a string' % (t['id'], key))


def game_document(site, targets, default, repository):
    require(isinstance(site.get('slug'), str) and SLUG.fullmatch(site['slug']), 'site.json: invalid slug')
    for key in ('title', 'console'):
        require(isinstance(site.get(key), str) and site[key], 'site.json: %s is required' % key)
    game = {'schema': SCHEMA, 'slug': site['slug'], 'title': site['title'],
            'shortTitle': site.get('shortTitle', site['title']), 'console': site['console'],
            'year': site.get('year'), 'repository': repository,
            'contributions': site.get('contributions', {'accepting': False}),
            'defaultTarget': default, 'targets': targets}
    if 'artwork' in site:
        game['artwork'] = site['artwork']
    check_game(game)
    return game


# Validation: the contract, executable. Every document is checked before it is written or pushed.

def check_measure(m, label):
    require(isinstance(m, dict), label + ' is missing')
    total = m.get('total')
    require(isinstance(total, int) and not isinstance(total, bool) and total >= 0, label + ': invalid total')
    for key in ('linked', 'matched'):
        value = m.get(key)
        require(value is None or (isinstance(value, int) and 0 <= value <= total), label + ': invalid ' + key)
    fuzzy = m.get('fuzzy')
    require(fuzzy is None or (isinstance(fuzzy, (int, float)) and math.isfinite(fuzzy)
                              and (m.get('matched') or 0) - 1e-6 <= fuzzy <= total + 1e-6), label + ': invalid fuzzy')


def check_counts(c, label):
    if c is None:
        return
    require(isinstance(c.get('total'), int) and c['total'] >= 0, label + ': invalid total')
    for key in ('exact', 'named'):
        require(c.get(key) is None or (isinstance(c[key], int) and 0 <= c[key] <= c['total']), label + ': invalid ' + key)


def check_summary(s):
    for kind in ('code', 'data'):
        check_measure(s.get(kind), kind)
    check_counts(s.get('functions'), 'functions')
    check_counts(s.get('files'), 'files')


def check_game(game):
    require(game.get('schema') == SCHEMA, 'game.json: unsupported schema')
    require(SLUG.fullmatch(game.get('slug') or ''), 'game.json: invalid slug')
    require(isinstance(game.get('repository'), str) and game['repository'].count('/') == 1, 'game.json: invalid repository')
    check_targets(game['targets'], game['defaultTarget'])


def check_latest(latest, game, target):
    require(latest.get('schema') == SCHEMA, 'latest.json: unsupported schema')
    require(latest.get('game') == game and latest.get('target') == target, 'latest.json: identity differs from its path')
    source = latest.get('source', {})
    require(SHA1.fullmatch(source.get('revision') or ''), 'latest.json: invalid revision')
    timestamp(source.get('committedAt'))
    timestamp(latest.get('measuredAt'))
    check_summary(latest.get('summary', {}))


def check_history(rows):
    require(isinstance(rows, list), 'history.json is not a list')
    seen, last = set(), None
    for row in rows:
        require(SHA1.fullmatch(row.get('revision') or ''), 'history: invalid revision')
        require(row['revision'] not in seen, 'history: duplicate revision ' + row['revision'])
        seen.add(row['revision'])
        t = timestamp(row.get('measuredAt'))
        require(last is None or t >= last, 'history: rows out of order at ' + row['revision'])
        last = t
        for kind in ('code', 'data'):
            check_measure(row.get(kind), 'history %s %s' % (row['revision'][:7], kind))
        check_counts(row.get('functions'), 'history functions')


def merged_ranges(ranges):
    result = []
    for start, end in sorted(ranges):
        require(not result or start >= result[-1][1], 'map: overlapping ranges')
        if result and start == result[-1][1]:
            result[-1] = (result[-1][0], end)
        else:
            result.append((start, end))
    return result


def check_map(document, s):
    """Every byte the summary counts appears once in each view, and each parent is its children's sum."""
    require(document.get('schema') == SCHEMA, 'map.json: unsupported schema')

    def close(a, b):
        return math.isclose(a, b, abs_tol=1e-6, rel_tol=1e-12)

    def node_extents(item):
        if 'mapped_extents' in item:
            rs = [(int(x['start'], 16), int(x['end'], 16)) for x in item['mapped_extents']]
        else:
            require('address' in item, 'map: leaf %r lacks an address' % item.get('name'))
            rs = [(int(item['address'], 16), int(item['address'], 16) + item['size'])]
        require(all(0 <= a < b <= 2 ** 64 for a, b in rs) and sum(b - a for a, b in rs) == item['size'],
                'map: invalid extents for %r' % item.get('name'))
        return rs
    functions, exact = {}, set()

    def walk(item, kind, inventory):
        require(item.get('kind') == kind, 'map: kind differs at %r' % item.get('name'))
        for key in ('source', 'comparison_source'):
            if key in item:
                require(SOURCE_PATH.fullmatch(item[key]) and not any(p in ('.', '..') for p in item[key].split('/')),
                        'map: invalid repository path %r' % item[key])
        check_measure({'total': item['size'], 'linked': item['linked'], 'matched': item['matched'],
                       'fuzzy': item.get('fuzzy')}, 'map %r' % item.get('name'))
        if item.get('children'):
            children = item['children']
            for key in ('size', 'linked', 'matched', *(['fuzzy'] if 'fuzzy' in item else [])):
                require(all(key in c for c in children) and close(math.fsum(c[key] for c in children), item[key]),
                        'map: %r children do not add up (%s)' % (item.get('name'), key))
            rs = merged_ranges([r for c in children for r in walk(c, kind, inventory)])
            if 'address' in item or 'mapped_extents' in item:
                require(rs == merged_ranges(node_extents(item)), 'map: %r extents differ from its children' % item.get('name'))
            return rs
        rs = node_extents(item)
        if inventory and item.get('type') == 'function':
            require(kind == 'code' and 'function_address' in item and 'original_size' in item,
                    'map: incomplete function identity %r' % item.get('name'))
            start, size = int(item['function_address'], 16), item['original_size']
            require(all(start <= a < b <= start + size for a, b in rs), 'map: function fragment outside its extent')
            functions.setdefault((start, size), []).extend(rs)
            if item['size'] == size and item['matched'] == size:
                require((start, size) not in exact, 'map: duplicate exact function')
                exact.add((start, size))
        return rs
    for kind in ('code', 'data'):
        reference, m = None, s[kind]
        for field in ('sections', 'files'):
            items = [i for i in document[field] if i['kind'] == kind]
            for key, k in (('total', 'size'), ('linked', 'linked'), ('matched', 'matched'), ('fuzzy', 'fuzzy')):
                if m.get(key) is None:
                    continue
                require(all(k in x for x in items) and close(math.fsum(x[k] for x in items), m[key]),
                        'map: %s %s %s differs from the summary' % (field, kind, key))
            actual = merged_ranges([r for i in items for r in walk(i, kind, field == 'files')])
            require(reference is None or actual == reference, 'map: sections and files cover different %s bytes' % kind)
            reference = actual
    for (start, size), rs in functions.items():
        require(merged_ranges(rs) == [(start, start + size)], 'map: incomplete function at %s' % hexaddr(start))
    if functions and s.get('functions'):
        require(len(functions) == s['functions']['total'], 'map: function count differs from the summary')
        if s['functions'].get('exact') is not None:
            require(len(exact) == s['functions']['exact'], 'map: exact function count differs from the summary')


def check_contributors(document, s):
    """Each credited function is listed once, every author is a listed contributor, and the
    per-person totals and the credited count agree with the function list."""
    require(document.get('schema') == SCHEMA, 'contributors.json: unsupported schema')
    people = {p['id']: p for p in document['contributors']}
    require(len(people) == len(document['contributors']), 'contributors: duplicate person')
    totals = dict.fromkeys(people, 0)
    seen = set()
    for item in document['functions']:
        require(item['id'] not in seen, 'contributors: duplicate function credit')
        seen.add(item['id'])
        for author in item['authors']:
            require(author in totals, 'contributors: unknown author %r' % author)
            totals[author] += 1
    require(len(seen) == document['credited_functions'], 'contributors: credited count differs from the list')
    require(all(totals[i] == p['functions'] for i, p in people.items()), 'contributors: person totals differ from the list')
    if s.get('functions') and s['functions'].get('exact') is not None:
        require(document['credited_functions'] == s['functions']['exact'], 'contributors: credited count differs from exact functions')


def check_tree(tree):
    """Validate every game the data tree indexes. Returns the number of targets checked."""
    tree = Path(tree)
    index = read_json(tree / 'index.json')
    require(index.get('schema') == SCHEMA and isinstance(index.get('games'), list), 'index.json: invalid')
    checked = 0
    for slug in index['games']:
        root = tree / 'data' / slug
        game = read_json(root / 'game.json')
        check_game(game)
        require(game['slug'] == slug, 'game.json: slug differs from its path')
        for target in game['targets']:
            directory = root / target['id']
            if not (directory / 'latest.json').exists():
                continue
            latest = read_json(directory / 'latest.json')
            check_latest(latest, slug, target['id'])
            rows = read_json(directory / 'history.json')
            check_history(rows)
            row = next((r for r in rows if r['revision'] == latest['source']['revision']), None)
            require(row is not None, '%s/%s: history lacks the latest revision' % (slug, target['id']))
            for kind in ('code', 'data'):
                require(all(row[kind][k] == latest['summary'][kind][k] for k in ('total', 'linked')),
                        '%s/%s: history differs from latest' % (slug, target['id']))
            if latest.get('modules', {}).get('map'):
                check_map(read_json(directory / latest['modules']['map']), latest['summary'])
            if latest.get('modules', {}).get('contributors'):
                check_contributors(read_json(directory / latest['modules']['contributors']), latest['summary'])
            checked += 1
    return checked


# Writing one measurement into a data tree.

def history_row(latest):
    s = latest['summary']
    return {'revision': latest['source']['revision'], 'measuredAt': latest['measuredAt'],
            'code': s['code'], 'data': s['data'], 'functions': s['functions']}


def write_target(tree, game, latest, map_doc):
    """Add one measurement. The first measurement of a revision wins, so re-running CI changes
    nothing; latest and map only move forward, so a slow run of an older commit never replaces a
    newer one."""
    tree = Path(tree)
    slug, target = game['slug'], latest['target']
    require(any(t['id'] == target and t['status'] == 'active' for t in game['targets']),
            'Target %s is not an active target of %s' % (target, slug))
    check_latest(latest, slug, target)
    check_map(map_doc, latest['summary'])
    directory = tree / 'data' / slug / target
    history_path = directory / 'history.json'
    rows = read_json(history_path) if history_path.exists() else []
    check_history(rows)
    if not any(r['revision'] == latest['source']['revision'] for r in rows):
        rows.append(history_row(latest))
        rows.sort(key=lambda r: timestamp(r['measuredAt']))
    current_path = directory / 'latest.json'
    current = read_json(current_path) if current_path.exists() else None
    if current is None or (current['source']['revision'] != latest['source']['revision'] and
                           timestamp(current['source']['committedAt']) <= timestamp(latest['source']['committedAt'])):
        write_json(directory / 'map.json', map_doc, compact=True)
        write_json(current_path, latest)
    write_json(history_path, rows, rows=True)
    write_json(tree / 'data' / slug / 'game.json', game)
    index_path = tree / 'index.json'
    index = read_json(index_path) if index_path.exists() else {'schema': SCHEMA, 'games': []}
    index['games'] = sorted(set(index['games']) | {slug})
    write_json(index_path, index)


def git(*args, cwd=None, env=None):
    return subprocess.run(['git', '-c', 'safe.directory=*', *args], cwd=cwd, check=True,
                          capture_output=True, text=True, env=env).stdout.strip()


def token_env(token):
    # The token travels in the environment, never in arguments, so a failed command's message
    # cannot print it.
    header = 'AUTHORIZATION: basic ' + base64.b64encode(('x-access-token:' + token).encode()).decode()
    return {**os.environ, 'GIT_CONFIG_COUNT': '1', 'GIT_TERMINAL_PROMPT': '0',
            'GIT_CONFIG_KEY_0': 'http.https://github.com/.extraheader', 'GIT_CONFIG_VALUE_0': header}


def source_commit(directory):
    revision, committed, title = git('log', '-1', '--format=%H%n%cI%n%s', cwd=directory).split('\n', 2)
    committed = datetime.datetime.fromisoformat(committed).astimezone(datetime.timezone.utc).strftime(TIME)
    return revision, committed, title


def convert(args):
    """Build game.json, latest.json and map.json in memory from the producer's files."""
    code_sections = tuple(s.strip() for s in args.code_sections.split(',') if s.strip())
    report = read_json(args.report)
    targets, default = load_targets(args.targets)
    game = game_document(read_json(args.site), targets, default, args.repository)
    revision, committed, title = (args.revision, args.committed_at, args.title) if args.revision else source_commit(args.source)
    server = os.environ.get('GITHUB_SERVER_URL', 'https://github.com')
    run_id = os.environ.get('GITHUB_RUN_ID')
    tools = [dict(zip(('name', 'version'), line.split('=', 1))) for line in args.tools.splitlines() if '=' in line]
    latest = {'schema': SCHEMA, 'game': game['slug'], 'target': args.target,
              'source': {'revision': revision, 'committedAt': committed, 'title': title,
                         'url': '%s/%s/commit/%s' % (server, args.repository, revision),
                         'runUrl': '%s/%s/actions/runs/%s' % (server, args.repository, run_id) if run_id else None},
              'measuredAt': args.measured_at or now(),
              'tools': tools,
              'summary': summary(report, code_sections),
              'modules': {'map': 'map.json', 'contributors': None}}
    return game, latest, map_document(report, code_sections, args.unit_prefix)


def publish(args):
    game, latest, map_doc = convert(args)
    if args.dry_run:
        tree = Path(args.output or tempfile.mkdtemp(prefix='decomp-data-'))
        write_target(tree, game, latest, map_doc)
        print('checked %d target(s) in %s' % (check_tree(tree), tree))
        return
    token = os.environ.get('DATA_TOKEN')
    require(token, 'DATA_TOKEN is not set')
    work = Path(tempfile.mkdtemp(prefix='decomp-data-'))
    env = token_env(token)
    try:
        git('clone', '--quiet', '--depth', '1', 'https://github.com/%s.git' % args.data_repository, str(work), env=env)
        git('config', 'user.name', '%s publisher' % game['slug'], cwd=work)
        git('config', 'user.email', 'publisher@users.noreply.github.com', cwd=work)
        branch = git('rev-parse', '--abbrev-ref', 'HEAD', cwd=work)
        for attempt in range(1, 6):
            # Rebuild from the newest tip every attempt: the write is idempotent, so a lost race
            # simply re-applies this measurement on top of the winner's.
            git('fetch', '--quiet', '--depth', '1', 'origin', branch, cwd=work, env=env)
            git('reset', '--quiet', '--hard', 'origin/' + branch, cwd=work)
            write_target(work, game, latest, map_doc)
            check_tree(work)
            git('add', '-A', cwd=work)
            if not git('status', '--porcelain', cwd=work):
                print('%s/%s %s already published' % (game['slug'], latest['target'], latest['source']['revision'][:7]))
                return
            code = latest['summary']['code']
            git('commit', '--quiet', '-m', '%s %s: %s, %.2f%% code linked' % (
                game['slug'], latest['target'], latest['source']['revision'][:7],
                100 * code['linked'] / code['total'] if code['total'] else 0),
                '-m', latest['source']['runUrl'] or latest['source']['url'], cwd=work)
            try:
                git('push', '--quiet', 'origin', 'HEAD:' + branch, cwd=work, env=env)
                print('published %s/%s %s' % (game['slug'], latest['target'], latest['source']['revision'][:7]))
                return
            except subprocess.CalledProcessError as error:
                print('push failed (attempt %d), retrying: %s' % (attempt, error.stderr.strip()), file=sys.stderr)
        raise ContractError('push failed after 5 attempts')
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('publish')
    p.add_argument('--target', required=True)
    p.add_argument('--report', required=True, help="objdiff's report.json")
    p.add_argument('--targets', default='config/targets.json')
    p.add_argument('--site', default='config/site.json')
    p.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY'))
    p.add_argument('--source', default='.', help='checkout whose HEAD was measured')
    p.add_argument('--revision', help='measured commit (default: HEAD of --source)')
    p.add_argument('--committed-at')
    p.add_argument('--title', default='')
    p.add_argument('--measured-at', default='')
    p.add_argument('--tools', default='', help='name=version lines')
    p.add_argument('--code-sections', default='.init,.text')
    p.add_argument('--unit-prefix', default='main/')
    p.add_argument('--output', help='data tree to write into with --dry-run')
    p.add_argument('--data-repository', default='mitsevox/decomp-data')
    p.add_argument('--dry-run', action='store_true')
    check = commands.add_parser('check')
    check.add_argument('tree')
    args = parser.parse_args(argv)
    try:
        if args.command == 'check':
            print('checked %d target(s)' % check_tree(args.tree))
        else:
            require(args.repository, '--repository or GITHUB_REPOSITORY is required')
            publish(args)
    except ContractError as error:
        sys.exit('publish: ' + str(error))


if __name__ == '__main__':
    main()
