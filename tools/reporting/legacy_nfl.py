"""Compatibility validator for the original producer format; isolated from the shared contract."""
import math
from pathlib import Path
from .validation import ROOT, SHA, ADDRESS, decode, digest, require, schema, timestamp, integer

PACKAGE_FILES = {'manifest.json', 'progress.json', 'activity.json', 'receipt.json', 'summary.json'}

def measures(item, size='total'):
    total = item.get(size)
    require(integer(total), 'Invalid byte denominator')
    for field in ('linked', 'matched'):
        require(integer(item.get(field)) and item[field] <= total, 'Invalid ' + field + ' bytes')
    fuzzy = item.get('fuzzy')
    require(fuzzy is None or (type(fuzzy) in (int, float) and math.isfinite(fuzzy)
            and item['matched'] <= fuzzy <= total + 1e-6), 'Invalid fuzzy coverage')
    # NFL's promotion policy requires linked source to be byte exact. Other
    # adapters must establish their own policy; this is not a generic identity.
    require(item['linked'] <= item['matched'], 'NFL linked bytes exceed exact bytes')


def same_totals(items, parent, size='size'):
    for field in ('linked', 'matched', 'fuzzy', size):
        if field == 'fuzzy' and parent.get(field) is None:
            continue
        values = [i.get(field) for i in items]
        require(all(type(v) in (int, float) for v in values), 'Missing aggregate field ' + field)
        require(math.isclose(math.fsum(values), parent[field], abs_tol=1e-6, rel_tol=1e-12),
                'Map aggregate differs: ' + field)


def intervals(item):
    if 'mapped_extents' in item:
        ranges = [(int(e['start'], 16), int(e['end'], 16)) for e in item['mapped_extents']]
    else:
        require(ADDRESS.fullmatch(item.get('address', '')), 'Map leaf lacks address')
        ranges = [(int(item['address'], 16), int(item['address'], 16) + item['size'])]
    require(all(0 <= a < b <= 2**32 for a, b in ranges), 'Invalid map extent')
    require(sum(b-a for a, b in ranges) == item['size'], 'Map extent size differs')
    return ranges


def merged_ranges(ranges):
    result = []
    for a, b in sorted(ranges):
        require(not result or a >= result[-1][1], 'Overlapping map ranges')
        if result and a == result[-1][1]:
            result[-1] = (result[-1][0], b)
        else:
            result.append((a, b))
    return result


def validate_progress(p, target, revision):
    schema(p, 'nfl-progress-v1.schema.json')
    require(p['revision'] == revision and p['target'] == target['id']
            and p['target_sha1'] == target['sha1'], 'Progress identity differs')
    timestamp(p['built_at'])
    function_parts = {}
    exact = set()
    section_ranges = {k: [] for k in ('code', 'data')}
    for section in p['sections']:
        section_ranges[section['kind']].extend(intervals(section))
    for kind in section_ranges:
        section_ranges[kind] = merged_ranges(section_ranges[kind])
    def walk(item, kind, record_functions=False):
        require(item['kind'] == kind and item['size'] > 0, 'Invalid map kind/size')
        measures(item, 'size')
        children = item.get('children', [])
        if children:
            same_totals(children, item)
            ranges = [r for child in children for r in walk(child, kind, record_functions)]
            if 'mapped_extents' in item or 'address' in item:
                require(merged_ranges(ranges) == merged_ranges(intervals(item)), 'Parent extents differ from children')
            return ranges
        ranges = intervals(item)
        if record_functions and item.get('type') == 'function':
            start = int(item['function_address'], 16)
            extent = item['original_size']
            require(kind == 'code' and extent > 0 and all(start <= a < b <= start+extent for a,b in ranges),
                    'Function fragment outside original extent')
            identity = (item['function_address'], extent)
            function_parts.setdefault(identity, []).extend(ranges)
            if item['size'] == extent and item['matched'] == extent:
                require(identity not in exact, 'Duplicate exact function')
                exact.add(identity)
            # Names are producer policy. Counts are not re-inferred from spelling.
        return ranges
    for key in ('sections', 'files'):
        for kind in ('code', 'data'):
            m = p['measures'][kind]
            measures(m)
            items = [i for i in p[key] if i['kind'] == kind]
            same_totals(items, {**m, 'size': m['total']})
            actual = merged_ranges([r for i in items for r in walk(i, kind, key == 'files')])
            require(actual == section_ranges[kind], 'Map coverage differs from executable sections')
    for (address, size), ranges in function_parts.items():
        start = int(address, 16)
        require(merged_ranges(ranges) == [(start, start+size)], 'Incomplete function inventory extent')
    require(len(function_parts) == p['functions']['total'], 'Function inventory count differs')
    require(len(exact) == p['functions']['exact'], 'Exact function count differs from complete extents')
    for key in ('functions', 'file_counts'):
        c = p[key]
        require(all(integer(c[f]) and c[f] <= c['total'] for f in ('exact', 'named')), 'Invalid inventory count')
    return exact


def validate_activity(a, p):
    schema(a, 'nfl-activity-v1.schema.json')
    require(all(a[k] == p[k] for k in ('revision', 'target', 'target_sha1')), 'Activity identity differs')
    require(a['credited_functions'] == p['functions']['exact'], 'Unique credited count differs from exact inventory')
    seen = set()
    last = -math.inf
    for row in a['snapshots']:
        require(row['revision'] not in seen, 'Duplicate history revision')
        seen.add(row['revision'])
        time = timestamp(row['built_at'])
        require(time >= last, 'History out of order')
        last = time
        for kind in ('code', 'data'):
            m = row[kind]
            require(integer(m['total']) and 0 <= m['linked'] <= m['total'] and m['total'] > 0, 'Invalid history measurement')
    current = next((r for r in a['snapshots'] if r['revision'] == p['revision']), None)
    require(current is not None, 'History lacks measured revision')
    for kind in ('code', 'data'):
        require(current[kind] == {f:p['measures'][kind][f] for f in ('total', 'linked')}, 'Current history differs')
    users = set()
    previous = math.inf
    for person in a['contributors']:
        login = person['login'].lower()
        require(login not in users and person['functions'] <= previous
                and person['functions'] <= a['credited_functions'], 'Duplicate or invalid contributor count')
        users.add(login)
        previous = person['functions']
    # Personal counts can overlap for joint authorship. Never sum them as the
    # unique inventory; original attribution is verified in the producer CI.


def summary(p):
    return {**{kind:{'totalBytes':p['measures'][kind]['total'],
                    'linkedBytes':p['measures'][kind]['linked'],
                    'matchedBytes':p['measures'][kind]['matched'],
                    'fuzzyEquivalentBytes':p['measures'][kind].get('fuzzy')}
               for kind in ('code', 'data')},
            'functions':p['functions'], 'files':p['file_counts']}


def validate_package(directory, root=ROOT, policy=None):
    directory = Path(directory)
    require(not directory.is_symlink() and {p.name for p in directory.iterdir()} == PACKAGE_FILES
            and all(p.is_file() and not p.is_symlink() for p in directory.iterdir()),
            'Unexpected or unsafe package files')
    manifest = decode((directory/'manifest.json').read_bytes())
    schema(manifest, 'report-v1.schema.json')
    require(manifest['origin'] == 'measured', 'Production rejects fixture packages')
    expected_assets = {'map':('progress.json','nfl-progress-v1'),
                       'timeline':('activity.json','nfl-activity-v1'),
                       'contributors':('activity.json','nfl-activity-v1')}
    require(all(manifest['modules'][key]['status'] == 'supported'
                and (manifest['modules'][key]['asset']['path'],manifest['modules'][key]['asset']['schema']) == value
                for key,value in expected_assets.items()), 'Unsupported NFL payload contract')
    require(manifest['validation']['receipt']['path'] == 'receipt.json'
            and manifest['validation']['receipt']['schema'] == 'nfl-execution-v1', 'Invalid receipt reference')
    documents = {}
    references = [manifest['validation']['receipt']]
    references += [m['asset'] for m in manifest['modules'].values() if m['status'] == 'supported']
    for ref in references:
        path = directory / ref['path']
        require(path.resolve().is_relative_to(directory.resolve()) and not path.is_symlink(), 'Unsafe payload path')
        raw = path.read_bytes()
        require(digest(raw) == ref['sha256'], 'Payload checksum differs: '+ref['path'])
        documents[ref['path']] = decode(raw)
    require(manifest['methodology'] == 'nflstreet2-verified-export-v1', 'Unsupported adapter methodology')
    p, a = documents['progress.json'], documents['activity.json']
    validate_progress(p, manifest['target'], manifest['revision'])
    validate_activity(a, p)
    require(summary(p) == manifest['summary'], 'Manifest summary differs from payload')
    receipt = documents['receipt.json']
    schema(receipt, 'nfl-execution-v1.schema.json')
    require(receipt['revision'] == manifest['revision'] and receipt['tree'] == manifest['tree']
            and receipt['run']['id'] == manifest['validation']['runId']
            and receipt['run']['run_attempt'] == manifest['validation']['attempt'], 'Receipt identity differs')
    require(receipt['mode'] == manifest['validation']['mode'], 'Receipt lane differs')
    require(receipt['measuredAt'] == manifest['measuredAt'] and receipt['publishedAt'] == manifest['publishedAt']
            and receipt['publishedAt'] == p['built_at']
            and timestamp(receipt['measuredAt']) <= timestamp(receipt['publishedAt']), 'Measurement/publication time differs')
    policy = policy or decode((root/'config/nflstreet2-producer.json').read_bytes())
    require(manifest['project'] == 'nflstreet2' and manifest['repository'] == policy['repository'] and manifest['target'] == policy['target'],
            'Package does not match approved producer policy')
    require(manifest['tools'] == [{'name':'build-environment','identity':policy['environment']},
                                 {'name':'producer-workflow','identity':receipt['workflowBlob']}], 'Tool identities differ')
    from .github import authenticate_run
    recorded_run = {**receipt['run'], 'repository':{'full_name':receipt['repository']},
                    'head_repository':{'full_name':receipt['repository']}}
    mode, _ = authenticate_run(policy, recorded_run, [receipt['job']], receipt['workflowBlob'])
    require(mode == manifest['validation']['mode'] and manifest['validation']['workflowRevision'] == manifest['revision'],
            'Recorded validation differs from manifest')
    return manifest, p, a
