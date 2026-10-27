"""Versioned game/target catalogs and target-scoped last-good selections."""
import re
from pathlib import Path
from .validation import decode, require, schema

TARGET_ID=re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}')


def catalog(root,slug,filename):
    require(isinstance(filename,str) and re.fullmatch(r'[A-Za-z0-9_-]+\.json',filename),'Unsafe target registry path')
    path=Path(root)/'config'/filename
    require(not path.is_symlink(),'Unsafe target registry')
    document=decode(path.read_bytes());schema(document,'targets-v1.schema.json')
    require(document['project']==slug,'Target registry belongs to another project')
    ids=set();identities=set();aliases=set()
    for item in document['targets']:
        target=item['target'];key=(target['platform'],target['gameId'],target['discRevision'])
        require(target['id'] not in ids and key not in identities,'Duplicate target identity')
        ids.add(target['id']);identities.add(key)
        if target['platform']=='gamecube':
            require(re.fullmatch(r'[A-Z0-9]{6}',target['gameId']) and target['id']==target['gameId']+'-rev'+str(target['discRevision']), 'Invalid GameCube target identity')
        require(not item['support']['reportFormats'] or item['support']['build'],'Report target has no verified build support')
        for old in item['legacyTargets']:
            alias=(old['id'],old['console'],old['sha1'])
            require(alias not in aliases and old['sha1']==target['sha1'],'Duplicate or cross-binary legacy target alias')
            aliases.add(alias)
    default=next((x for x in document['targets'] if x['target']['id']==document['defaultTarget']),None)
    require(default is not None and default['status']=='active' and default['support']['reportFormats'],'Default target is not report-supported')
    return document


def registered_catalog(root,slug):
    from .registry import registrations
    item=registrations(root)[slug]
    if 'targets' not in item:return None
    require(set(item)=={'format','catalog','targets'} and item['format']=='report-v2' and isinstance(item['targets'],dict),'Invalid multi-target registration')
    document=catalog(root,slug,item['catalog'])
    known={x['target']['id']:x for x in document['targets']}
    require(item['targets'] and all(key in known and 'report-v2' in known[key]['support']['reportFormats'] for key in item['targets']),'Unreportable target policy')
    require(document['defaultTarget'] in item['targets'],'Default target lacks a producer policy')
    from .registry import load_policy
    repositories={load_policy(root,slug,{key:policy[key] for key in ('format','policy')})['repository'] for policy in item['targets'].values()}
    require(len(repositories)==1,'One game must have one producer repository')
    return document


def canonical_target(root,slug,value):
    document=registered_catalog(root,slug)
    if document is None:return value
    matches=[item['target'] for item in document['targets'] if value==item['target'] or value in item['legacyTargets']]
    require(len(matches)==1,'Unregistered or ambiguous target identity')
    return matches[0]


def default_target(root,slug):
    document=registered_catalog(root,slug)
    return document['defaultTarget'] if document else None


def selected(lock,slug,target=None):
    entry=lock['projects'].get(slug)
    if target is None:return entry
    return entry.get('targets',{}).get(target) if entry else None


def select(lock,slug,target,entry):
    if target is None:lock['projects'][slug]=entry
    else:
        lock['schemaVersion']=2
        group=lock['projects'].setdefault(slug,{'targets':{}})
        require(set(group)=={'targets'},'Unmigrated target selection')
        group['targets'][target]=entry


def entries(lock):
    for slug,item in lock['projects'].items():
        if 'targets' in item:
            require(type(lock.get('schemaVersion')) is int and lock['schemaVersion']==2,'Target selections require lock version 2')
            require(set(item)=={'targets'} and isinstance(item['targets'],dict),'Invalid target selections')
            for target,entry in item['targets'].items():
                require(TARGET_ID.fullmatch(target),'Unsafe target selector')
                yield slug,target,entry
        else:yield slug,None,item


def normalize_lock(root,lock,read_manifest=None):
    """Only explicit owner-curated aliases can adopt an immutable v1 selection."""
    from .registry import registrations
    for slug,item in lock['projects'].items():
        registration=registrations(root).get(slug,{})
        if 'targets' not in registration:continue
        document=registered_catalog(root,slug)
        if 'targets' not in item:
            from .registry import snapshot_path
            from .validation import digest
            snapshot_path(slug,item)
            path=Path(root)/item['path']/'manifest.json'
            if read_manifest is None:
                require(path.is_file() and not path.is_symlink(),'Legacy selection manifest is unavailable for migration')
                raw=path.read_bytes()
            else:raw=read_manifest(item)
            require(digest(raw)==item['manifestSha256'],'Legacy manifest checksum differs')
            manifest=decode(raw)
            require(manifest['revision']==item['revision'],'Legacy revision differs')
            require(manifest['project']==slug and manifest['schemaVersion']==1,'Invalid legacy selection')
            target=canonical_target(root,slug,manifest['target'])['id']
            lock['projects'][slug]={'targets':{target:item}}
            lock['schemaVersion']=2
    return lock


def validate_selection(root,slug,target,entry,manifest):
    """A valid package is not sufficient: it must belong to this exact pointer."""
    require(manifest['project']==slug and manifest['revision']==entry['revision'],'Selection identity differs')
    identity=canonical_target(root,slug,manifest['target'])
    if target is not None:require(identity['id']==target,'Selection belongs to another target')
    else:require(registered_catalog(root,slug) is None,'Multi-target selection lacks target ID')
