"""The report-v1 producer contract, independent of game identity and build system."""
import math
import re
from pathlib import Path
from .validation import decode, digest, encoded, integer, require, schema, timestamp

ASSETS = {'map':'map-v1','timeline':'timeline-v1','contributors':'contributors-v1'}
MAP_SCHEMAS = {1:'map-v1', 2:'map-v2'}
FIXED = {'manifest.json','summary.json','receipt.json'}


def asset_schema(key, document):
    if key != 'map':return ASSETS[key]
    version=document.get('schemaVersion') if isinstance(document,dict) else None
    require(type(version) in (int,float) and version in MAP_SCHEMAS,'Unsupported map schema version')
    return MAP_SCHEMAS[version]


def metrics(m):
    total=m['totalBytes']
    require(integer(total), 'Invalid measured denominator')
    require(all(integer(m[k]) and m[k] <= total for k in ('linkedBytes','matchedBytes')), 'Invalid byte coverage')
    fuzzy=m['fuzzyEquivalentBytes']
    require(fuzzy is None or (type(fuzzy) in (int,float) and math.isfinite(fuzzy)
            and m['matchedBytes'] <= fuzzy <= total), 'Invalid fuzzy coverage')


def view(manifest):
    p={'schema':1,'baseline':'verified','basis':'measured-bytes',
       'revision':manifest['revision'],'target':manifest['target']['id'],
       'target_sha1':manifest['target']['sha1'],'built_at':manifest['publishedAt'],
       'measures':{},'functions':manifest['summary']['functions'],'file_counts':manifest['summary']['files']}
    for kind in ('code','data'):
        m=manifest['summary'][kind];metrics(m)
        p['measures'][kind]={'total':m['totalBytes'],'linked':m['linkedBytes'],'matched':m['matchedBytes']}
        if m['fuzzyEquivalentBytes'] is not None:p['measures'][kind]['fuzzy']=m['fuzzyEquivalentBytes']
    return p


def check_map(document,p,identifier=None):
    expected=asset_schema('map',document)
    require(identifier is None or identifier==expected,'Map asset schema/version differs')
    schema(document,expected+'.schema.json')
    from .validation import merged_ranges
    # Generic address handling also permits wider targets; measured byte counts
    # stay within the integer range supported by the browser.
    def extents(item):
        if 'mapped_extents' in item:
            rs=[(int(x['start'],16),int(x['end'],16)) for x in item['mapped_extents']]
        else:
            require('address' in item,'Map leaf lacks address')
            rs=[(int(item['address'],16),int(item['address'],16)+item['size'])]
        require(all(0<=a<b<=2**64 for a,b in rs) and sum(b-a for a,b in rs)==item['size'],'Invalid map extents')
        return rs
    functions={};exact=set()
    def walk(item,kind,inventory=False):
        if document['schemaVersion']==2:
            for key in ('source','comparison_source'):
                if key in item:
                    path=item[key]
                    require(re.fullmatch(r'[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+)*',path)
                            and not any(part in ('.','..') for part in path.split('/')),'Invalid repository source path')
        require(item['kind']==kind,'Map kind differs')
        m={'totalBytes':item['size'],'linkedBytes':item['linked'],'matchedBytes':item['matched'],
           'fuzzyEquivalentBytes':item.get('fuzzy')};metrics(m)
        if item.get('children'):
            children=item['children']
            for key in ('size','linked','matched',*(['fuzzy'] if 'fuzzy' in item else [])):
                require(all(key in c for c in children) and math.isclose(math.fsum(c[key] for c in children),item[key],abs_tol=1e-6,rel_tol=1e-12),'Map child totals differ')
            rs=merged_ranges([r for c in children for r in walk(c,kind,inventory)])
            if 'address' in item or 'mapped_extents' in item:require(rs==merged_ranges(extents(item)),'Map parent extents differ')
            return rs
        rs=extents(item)
        if inventory and item.get('type')=='function':
            require(kind=='code' and 'function_address' in item and 'original_size' in item,'Incomplete function identity')
            start=int(item['function_address'],16);size=item['original_size'];identity=(start,size)
            require(all(start<=a<b<=start+size for a,b in rs),'Function fragment outside extent')
            functions.setdefault(identity,[]).extend(rs)
            if item['size']==size and item['matched']==size:
                require(identity not in exact,'Duplicate exact function');exact.add(identity)
        return rs
    for kind in ('code','data'):
        reference=None
        for field in ('sections','files'):
            items=[i for i in document[field] if i['kind']==kind];m=p['measures'][kind]
            for key in ('total','linked','matched',*(['fuzzy'] if 'fuzzy' in m else [])):
                k='size' if key=='total' else key
                require(all(k in x for x in items) and math.isclose(math.fsum(x[k] for x in items),m[key],abs_tol=1e-6,rel_tol=1e-12),'Map summary differs')
            actual=merged_ranges([r for i in items for r in walk(i,kind,field=='files')])
            if reference is not None:require(actual==reference,'Map coverage differs')
            reference=actual
    for (start,size),rs in functions.items():require(merged_ranges(rs)==[(start,start+size)],'Incomplete function extent')
    if functions and p['functions'] is not None:
        require(len(functions)==p['functions']['total'],'Function inventory differs')
        if p['functions']['exact'] is not None:require(len(exact)==p['functions']['exact'],'Exact inventory differs')
    return {f"{p['target']}:0x{start:08X}:{size}" for start,size in exact} if functions else None


def check_timeline(document,p):
    schema(document,'timeline-v1.schema.json');seen=set();last=-math.inf
    for row in document['snapshots']:
        t=timestamp(row['built_at'])
        require(row['revision'] not in seen and t>=last,'Duplicate/out-of-order history')
        seen.add(row['revision']);last=t
        if 'record' in row['provenance']:
            original=row['provenance']['record']
            require(row['provenance']['kind']=='inherited' and all(original.get(k)==row[k] for k in ('revision','built_at','code','data')),'Inherited history record differs')
        for kind in ('code','data'):
            m=row[kind];require(integer(m['total']) and 0<=m['linked']<=m['total'],'Invalid history bytes')
    current=next((r for r in document['snapshots'] if r['revision']==p['revision']),None)
    require(current is not None,'History lacks measured revision')
    for kind in ('code','data'):require(current[kind]=={k:p['measures'][kind][k] for k in ('total','linked')},'Current history differs')


def check_contributors(document,p,exact=None):
    schema(document,'contributors-v1.schema.json')
    counts=p['functions'];require(counts is not None and counts['exact']==document['credited_functions'],'Unique credit inventory differs')
    people=document['contributors'];ids=set();logins=set();last=math.inf;totals={}
    for person in people:
        require(integer(person['id']) and integer(person['functions']),'Invalid contributor integer')
        require(person['id'] not in ids and person['login'].lower() not in logins and person['functions']<=last,'Duplicate/unsorted contributor')
        ids.add(person['id']);logins.add(person['login'].lower());last=person['functions'];totals[person['id']]=0
    functions=set()
    for item in document['functions']:
        require(item['id'] not in functions and len(set(item['authors']))==len(item['authors']),'Duplicate function credit')
        functions.add(item['id'])
        for author in item['authors']:
            require(author in totals,'Unknown function author');totals[author]+=1
    require(len(functions)==document['credited_functions'] and all(totals[x['id']]==x['functions'] for x in people),'Contributor totals differ from ledger')
    if exact is not None:require(functions==exact,'Credited function identities differ from map exact inventory')


def validate_package(directory,manifest,policy):
    directory=Path(directory)
    require(manifest['origin']=='measured','Production rejects fixture packages')
    expected=set(FIXED)
    require(manifest['validation']['receipt']['path']=='receipt.json' and manifest['validation']['receipt']['schema']=='execution-v1','Invalid execution reference')
    for key,identifier in ASSETS.items():
        module=manifest['modules'][key]
        if module['status']=='supported':
            ref=module['asset']
            identifiers=tuple(MAP_SCHEMAS.values()) if key=='map' else (identifier,)
            require(ref['schema'] in identifiers and re.fullmatch(r'[A-Za-z0-9_-]+\.json',ref['path']) and ref['path'] not in expected,'Unknown/duplicate module asset')
            expected.add(ref['path'])
    require({x.name for x in directory.iterdir()}==expected and len(expected)<=20
            and all(x.is_file() and not x.is_symlink() for x in directory.iterdir())
            and sum(x.stat().st_size for x in directory.iterdir())<=80*1024*1024,'Unexpected or unsafe package files')
    raw={name:(directory/name).read_bytes() for name in expected}
    documents={name:decode(value) for name,value in raw.items()}
    require(documents['summary.json']==manifest['summary'],'Summary differs from manifest')
    p=view(manifest)
    for key in ('functions','files'):
        counts=manifest['summary'][key]
        if counts is not None:
            require(integer(counts['total']) and all(v is None or integer(v) and v<=counts['total'] for v in (counts['exact'],counts['named'])),'Invalid inventory count')
    a={k:p[k] for k in ('schema','target','target_sha1','revision')};exact=None
    for key in ASSETS:
        module=manifest['modules'][key]
        if module['status']!='supported':continue
        ref=module['asset'];require(digest(raw[ref['path']])==ref['sha256'],'Payload checksum differs: '+key)
        doc=documents[ref['path']]
        if key=='map':exact=check_map(doc,p,ref['schema']);p.update(sections=doc['sections'],files=doc['files'],basis='executable-sections')
        if key=='timeline':check_timeline(doc,p);a['snapshots']=doc['snapshots']
        if key=='contributors':check_contributors(doc,p,exact);a.update({k:doc[k] for k in ('contributors','credited_functions')})
    receipt=documents['receipt.json'];schema(receipt,'execution-v1.schema.json')
    require(digest(raw['receipt.json'])==manifest['validation']['receipt']['sha256'],'Receipt checksum differs')
    for key in ('repository','target','revision','tree','methodology','generation','measuredAt','publishedAt'):
        require(receipt[key]==manifest[key],'Receipt identity differs: '+key)
    require(receipt['mode']==manifest['validation']['mode'],'Receipt validation mode differs')
    if receipt['mode']=='reused':
        require('reused' in policy['lanes'] and receipt['source']['tree']==manifest['tree']
                and receipt['source']['measuredAt']==manifest['measuredAt'],'Reused proof identity differs')
    require(receipt['runId']==manifest['validation']['runId'] and receipt['attempt']==manifest['validation']['attempt']
            and manifest['validation']['workflowRevision']==manifest['revision'],'Receipt execution differs')
    require(receipt['workflowBlob'] in policy['workflowBlobs'] and manifest['tools']==policy['tools'],'Producer tools/workflow differ')
    require(timestamp(manifest['measuredAt'])<=timestamp(manifest['publishedAt']),'Invalid measurement time')
    require(receipt['files']=={name:digest(value) for name,value in raw.items() if name not in ('receipt.json','manifest.json')},'Receipt payload binding differs')
    return manifest,p,a
