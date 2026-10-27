"""Common immutable installation and per-project last-good state."""
import base64
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import quote
from .validation import ROOT, decode, digest, encoded, require, schema, validate_package
from .registry import producer, snapshot_path, snapshot_directory, site_config
from .github import GitHub
from .targets import entries, normalize_lock, selected, select, registered_catalog, canonical_target, default_target

LOCK='data/reports.lock.json'


def read_lock(root,policy_root=None):
    root=Path(root).resolve()
    require((root/'data').resolve()==root/'data','Unsafe report data directory')
    path=root/LOCK
    lock=decode(path.read_bytes()) if path.exists() else {'schemaVersion':1,'projects':{}}
    require(set(lock)=={'schemaVersion','projects'} and type(lock['schemaVersion']) is int and lock['schemaVersion'] in (1,2) and isinstance(lock['projects'],dict),'Invalid report lock')
    policy_root=Path(policy_root or root)
    if (policy_root/'config/producers.json').exists():normalize_lock(policy_root,lock)
    for slug,target,entry in entries(lock):
        snapshot_path(slug,entry,target)
        if target is not None:producer(policy_root,slug,target)
        if 'sourceProof' in entry:
            proof=entry['sourceProof'];schema(proof,'source-proof-v1.schema.json')
            require(proof['parents']==[proof['base'],proof['head']],'Retained tested merge parents differ')
        if 'sourceProofs' in entry:
            require(isinstance(entry['sourceProofs'],dict),'Invalid retained proof cache')
            for key,proof in entry['sourceProofs'].items():
                schema(proof,'source-proof-v1.schema.json')
                require(key==proof['artifactSha256'] and proof['parents']==[proof['base'],proof['head']],
                        'Retained proof cache identity differs')
    return lock


def frozen_snapshot(root,slug,target=None):
    target=target or default_target(root,slug)
    freeze=producer(root,slug,target).get('freeze')
    if freeze is None:return None
    entry=selected(read_lock(root),slug,target)
    require(entry is not None and all(entry.get(k)==v for k,v in freeze.items()),'Frozen selection differs from checkpoint')
    directory=snapshot_directory(root,slug,entry,target)
    require(digest((directory/'manifest.json').read_bytes())==freeze['manifestSha256'],'Frozen manifest changed')
    manifest,_,_=validate_package(directory,root)
    require(manifest['revision']==freeze['revision'],'Frozen revision differs')
    print('Import frozen at verified checkpoint:',slug,freeze['revision'])
    return directory


def check_update(previous,manifest,old_activity,new_activity,relation,root=None):
    for key in ('project','repository','target'):
        if key in previous:
            old,new=previous[key],manifest[key]
            if key=='target' and root is not None:
                old=canonical_target(root,manifest['project'],old);new=canonical_target(root,manifest['project'],new)
            require(old==new,'Report identity changed: '+key)
    if previous['revision']==manifest['revision']:
        require(previous['summary']==manifest['summary'],'Same revision has conflicting measurements')
    else:require(relation=='ahead','Refresh would roll back or diverge from last good revision')
    rows={r['revision']:r for r in new_activity.get('snapshots',[])}
    for old in old_activity.get('snapshots',[]):
        candidate=rows.get(old['revision'])
        retained=candidate==old or (candidate is not None and candidate.get('provenance',{}).get('record')==old
                 and all(candidate.get(k)==old.get(k) for k in ('revision','built_at','code','data')))
        require(retained,'Refresh loses or changes recorded history')


def atomic_write(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:f.write(raw);name=f.name
    os.replace(name,path)


def install(root,api,manifest,payloads,latest,source_proof=None,source_proofs=None):
    root=Path(root).resolve()
    require((root/'data').resolve()==root/'data','Unsafe report data directory')
    (root/'data').mkdir(parents=True,exist_ok=True)
    require(not (root/'data/.report-refresh.lock').is_symlink(),'Unsafe report lock')
    with (root/'data/.report-refresh.lock').open('a') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        lock=read_lock(root);slug=manifest['project']
        target=canonical_target(root,slug,manifest['target'])['id'] if registered_catalog(root,slug) else None
        parent=root/'data'/slug
        # Historical v1 packages keep their original immutable public path.
        # Only new v2 packages enter the target-scoped snapshot namespace.
        if target and manifest['schemaVersion']==2:parent=parent/'targets'/target
        parent=parent/'snapshots'
        freeze=producer(root,slug,target).get('freeze')
        if freeze is not None:
            old=selected(lock,slug,target)
            require(old is not None and all(old.get(k)==v for k,v in freeze.items())
                    and manifest['revision']==freeze['revision']
                    and digest(payloads['manifest.json'])==freeze['manifestSha256'],'Producer import is frozen')
        require(parent.resolve()==parent,'Unsafe snapshot root')
        parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.incoming-',dir=parent) as temp:
            stage=Path(temp)
            for name,raw in payloads.items():
                require('/' not in name and '\\' not in name and name not in ('.','..'),'Unsafe package file')
                (stage/name).write_bytes(raw)
            checked,_,activity=validate_package(stage,root)
            require(checked==manifest,'Manifest argument differs from package')
            old=selected(lock,slug,target)
            if old:
                directory=snapshot_directory(root,slug,old,target)
                require(digest((directory/'manifest.json').read_bytes())==old['manifestSha256'],'Previous manifest differs')
                previous,_,old_activity=validate_package(directory,root)
                relation='identical' if previous['revision']==manifest['revision'] else api.get(f"compare/{previous['revision']}...{manifest['revision']}")['status']
                check_update(previous,manifest,old_activity,activity,relation,root)
            identity=f"{manifest['revision']}-v{manifest['schemaVersion']}-{manifest['validation']['runId']}-{manifest['validation']['attempt']}"
            if manifest['validation']['receipt']['schema'] in ('execution-v1','execution-v2'):
                identity+=f"-g{manifest['generation']}-"+digest(manifest['methodology'].encode())[:12]
            destination=parent/identity
            if destination.exists():
                require(not destination.is_symlink() and all(p.is_file() and not p.is_symlink() for p in destination.iterdir()),'Unsafe immutable snapshot')
                require({p.name:p.read_bytes() for p in destination.iterdir()}==payloads,'Immutable snapshot already exists with different content')
            else:shutil.copytree(stage,destination)
            new_entry={'path':destination.relative_to(root).as_posix(),
                'manifestSha256':digest(payloads['manifest.json']),'revision':manifest['revision'],'latestCommit':latest}
            select(lock,slug,target,new_entry)
            retained=dict(old.get('sourceProofs',{})) if old else {}
            for key,proof in (source_proofs or {}).items():
                schema(proof,'source-proof-v1.schema.json')
                require(key==proof['artifactSha256'] and proof['parents']==[proof['base'],proof['head']]
                        and (key not in retained or retained[key]==proof),'Retained proof cache conflicts')
                retained[key]=proof
            if source_proof is not None:
                schema(source_proof,'source-proof-v1.schema.json')
                original=decode(payloads['receipt.json']).get('source')
                require(manifest['validation']['mode']=='reused' and isinstance(original,dict)
                        and all(source_proof.get(k)==v for k,v in original.items())
                        and source_proof['repository']==manifest['repository']
                        and source_proof['parents']==[source_proof['base'],source_proof['head']],
                        'Consumer proof differs from report source')
                new_entry['sourceProof']=source_proof
                key=source_proof['artifactSha256']
                require(key not in retained or retained[key]==source_proof,'Retained proof cache conflicts')
                retained[key]=source_proof
            if retained:new_entry['sourceProofs']=retained
            atomic_write(root/LOCK,encoded(lock))
        return destination


def accepted_package(root,slug,entry,target=None):
    api=GitHub(site_config(root)['repository'])
    for branch in ('main','report-data'):
        try:file=api.get('contents/data/reports.lock.json?ref='+branch)
        except subprocess.CalledProcessError:continue
        require(file.get('encoding')=='base64','Unexpected accepted lock encoding')
        lock=decode(base64.b64decode(file['content']))
        require(lock.get('schemaVersion') in (1,2) and isinstance(lock.get('projects'),dict),'Invalid accepted report lock')
        normalize_lock(root,lock,lambda item:base64.b64decode(api.get('contents/'+item['path']+'/manifest.json?ref='+branch)['content']))
        trusted=selected(lock,slug,target) or {}
        if all(trusted.get(k)==entry.get(k) for k in ('path','manifestSha256','revision','sourceProof','sourceProofs')):return True
    return False


def latest_commit(api,branch='main'):
    commit=api.get('commits/'+quote(branch,safe=''));message=commit['commit']['message'].split('\n',1)
    return {'revision':commit['sha'],'title':message[0],'description':message[1].strip() if len(message)>1 else '',
            'date':commit['commit']['committer']['date'],'url':f'https://github.com/{api.repository}/commit/{commit["sha"]}'}


def update_latest_commits(root,updates,expected):
    """Repository activity is metadata, never a new target measurement/history row."""
    root=Path(root).resolve()
    require((root/'data').resolve()==root/'data' and not (root/'data/.report-refresh.lock').is_symlink(),'Unsafe commit metadata store')
    with (root/'data/.report-refresh.lock').open('a') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        lock=read_lock(root);changed=set()
        for slug,target,entry in entries(lock):
            # A concurrent import wins over an earlier metadata observation.
            if entry!=selected(expected,slug,target):continue
            if slug in updates and entry.get('latestCommit')!=updates[slug]:
                entry['latestCommit']=updates[slug];changed.add(slug)
        if changed:atomic_write(root/LOCK,encoded(lock))
    return changed
