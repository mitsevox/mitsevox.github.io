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
from .registry import snapshot_path, snapshot_directory, site_config
from .github import GitHub

LOCK='data/reports.lock.json'


def read_lock(root):
    root=Path(root).resolve()
    require((root/'data').resolve()==root/'data','Unsafe report data directory')
    path=root/LOCK
    lock=decode(path.read_bytes()) if path.exists() else {'schemaVersion':1,'projects':{}}
    require(set(lock)=={'schemaVersion','projects'} and lock['schemaVersion']==1 and isinstance(lock['projects'],dict),'Invalid report lock')
    for slug,entry in lock['projects'].items():
        snapshot_path(slug,entry)
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


def check_update(previous,manifest,old_activity,new_activity,relation):
    for key in ('project','repository','target'):
        if key in previous:require(previous[key]==manifest[key],'Report identity changed: '+key)
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
        lock=read_lock(root);slug=manifest['project'];parent=root/'data'/slug/'snapshots'
        require(parent.resolve()==parent,'Unsafe snapshot root')
        parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.incoming-',dir=parent) as temp:
            stage=Path(temp)
            for name,raw in payloads.items():
                require('/' not in name and '\\' not in name and name not in ('.','..'),'Unsafe package file')
                (stage/name).write_bytes(raw)
            checked,_,activity=validate_package(stage,root)
            require(checked==manifest,'Manifest argument differs from package')
            old=lock['projects'].get(slug)
            if old:
                directory=snapshot_directory(root,slug,old)
                require(digest((directory/'manifest.json').read_bytes())==old['manifestSha256'],'Previous manifest differs')
                previous,_,old_activity=validate_package(directory,root)
                relation='identical' if previous['revision']==manifest['revision'] else api.get(f"compare/{previous['revision']}...{manifest['revision']}")['status']
                check_update(previous,manifest,old_activity,activity,relation)
            identity=f"{manifest['revision']}-v1-{manifest['validation']['runId']}-{manifest['validation']['attempt']}"
            if manifest['validation']['receipt']['schema']=='execution-v1':
                identity+=f"-g{manifest['generation']}-"+digest(manifest['methodology'].encode())[:12]
            destination=parent/identity
            if destination.exists():
                require(not destination.is_symlink() and all(p.is_file() and not p.is_symlink() for p in destination.iterdir()),'Unsafe immutable snapshot')
                require({p.name:p.read_bytes() for p in destination.iterdir()}==payloads,'Immutable snapshot already exists with different content')
            else:shutil.copytree(stage,destination)
            lock['projects'][slug]={'path':destination.relative_to(root).as_posix(),
                'manifestSha256':digest(payloads['manifest.json']),'revision':manifest['revision'],'latestCommit':latest}
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
                lock['projects'][slug]['sourceProof']=source_proof
                key=source_proof['artifactSha256']
                require(key not in retained or retained[key]==source_proof,'Retained proof cache conflicts')
                retained[key]=source_proof
            if retained:lock['projects'][slug]['sourceProofs']=retained
            atomic_write(root/LOCK,encoded(lock))
        return destination


def accepted_package(root,slug,entry):
    api=GitHub(site_config(root)['repository'])
    for branch in ('main','report-data'):
        try:file=api.get('contents/data/reports.lock.json?ref='+branch)
        except subprocess.CalledProcessError:continue
        require(file.get('encoding')=='base64','Unexpected accepted lock encoding')
        lock=decode(base64.b64decode(file['content']))
        require(lock.get('schemaVersion')==1 and isinstance(lock.get('projects'),dict),'Invalid accepted report lock')
        trusted=lock['projects'].get(slug,{})
        if all(trusted.get(k)==entry.get(k) for k in ('path','manifestSha256','revision','sourceProof','sourceProofs')):return True
    return False


def latest_commit(api,branch='main'):
    commit=api.get('commits/'+quote(branch,safe=''));message=commit['commit']['message'].split('\n',1)
    return {'revision':commit['sha'],'title':message[0],'description':message[1].strip() if len(message)>1 else '',
            'date':commit['commit']['committer']['date'],'url':f'https://github.com/{api.repository}/commit/{commit["sha"]}'}
