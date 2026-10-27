"""Owner-curated registrations. Reports cannot register repositories or code."""
import re
from pathlib import Path
from .validation import ROOT, decode, require, schema, SHA

SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


def site_config(root=ROOT):
    result = decode((Path(root)/'config/site.json').read_bytes())
    require(set(result) == {'repository','owner'} and
            re.fullmatch(r'[A-Za-z0-9-]+/[A-Za-z0-9_.-]+', result['repository']) and
            result['repository'].split('/')[0].lower() == result['owner'].lower(), 'Invalid personal site identity')
    return result


def registrations(root=ROOT):
    values = decode((Path(root)/'config/producers.json').read_bytes())
    require(isinstance(values,dict) and all(SLUG.fullmatch(k) for k in values), 'Invalid producer registry')
    return values


def load_policy(root,slug,item):
    root=Path(root)
    require(set(item)=={'format','policy'} and item['format'] in ('report-v1','report-v2','nfl-legacy-v1'),'Unknown producer format')
    require(re.fullmatch(r'[a-zA-Z0-9_-]+\.json',item['policy']),'Unsafe producer policy path')
    policy=decode((root/'config'/item['policy']).read_bytes())
    require(policy['repository'].split('/')[0].lower()==site_config(root)['owner'].lower(),'Producer must belong to the site owner')
    if item['format'] in ('report-v1','report-v2'):schema(policy,'producer-v'+str(2 if item['format']=='report-v2' else 1)+'.schema.json')
    else:require(all(SHA.fullmatch(x) for x in policy['workflowBlobs']),'Invalid workflow identities')
    return {**policy,'format':item['format'],'project':slug}


def registration(root,slug,target=None):
    from .targets import registered_catalog
    require(isinstance(slug,str) and SLUG.fullmatch(slug),'Invalid project slug')
    item=registrations(root).get(slug)
    require(item is not None,'Unregistered project: '+slug)
    document=registered_catalog(root,slug)
    if document:
        target=target or document['defaultTarget']
        require(target in item['targets'],'Target is archived or unregistered: '+str(target))
        return item['targets'][target],target
    require(target is None,'Single-target producer does not declare target selectors')
    return item,None


def producer(root,slug,target=None):
    from .targets import canonical_target
    item,target=registration(root,slug,target)
    require(set(item)<= {'format','policy','archives','pending','freeze'} and {'format','policy'}<=set(item),'Invalid producer registration')
    active=load_policy(root,slug,{k:item[k] for k in ('format','policy')})
    if target is not None:
        require(active['format']=='report-v2' and active['target']['id']==target
                and canonical_target(root,slug,active['target'])==active['target'],'Policy target differs from catalog')
        active['_target']=target
    if 'pending' in item:
        pending=load_policy(root,slug,item['pending'])
        require(pending['repository']==active['repository'] and pending['target']==active['target'],
                'Pending producer changes project identity')
    if 'freeze' in item:
        freeze=item['freeze']
        require(isinstance(freeze,dict) and set(freeze)=={'path','revision','manifestSha256'},'Invalid import freeze')
        snapshot_path(slug,freeze,target)
        active['freeze']=freeze
    return active


def producers(root):
    from .targets import registered_catalog
    for slug,item in registrations(root).items():
        document=registered_catalog(root,slug)
        if document:
            for target in item['targets']:yield slug,target,producer(root,slug,target)
        else:yield slug,None,producer(root,slug)


def package_policy(root,manifest,workflow_blob):
    from .targets import canonical_target, registered_catalog
    slug=manifest['project']
    target=canonical_target(root,slug,manifest['target'])['id'] if registered_catalog(root,slug) else None
    current=producer(root,slug,target);item,_=registration(root,slug,target)
    policies=[current]+[load_policy(root,slug,archive) for archive in item.get('archives',[])]
    formats={'execution-v1':'report-v1','execution-v2':'report-v2','nfl-execution-v1':'nfl-legacy-v1'}
    format_name=formats.get(manifest['validation']['receipt']['schema'])
    def tools_match(policy):
        expected=policy['tools'] if policy['format'] in ('report-v1','report-v2') else [
            {'name':'build-environment','identity':policy['environment']},
            {'name':'producer-workflow','identity':workflow_blob}]
        return manifest['tools']==expected
    matching=[p for p in policies if tools_match(p) and p['format']==format_name and p['repository']==manifest['repository']
              and p['repository']==current['repository'] and p['target']==manifest['target']
              and workflow_blob in p['workflowBlobs']]
    require(matching,'Package differs from registered producer policy')
    return matching[0]


def snapshot_path(slug, entry, target=None):
    require(SLUG.fullmatch(slug), 'Invalid snapshot project')
    from .targets import TARGET_ID
    require(target is None or TARGET_ID.fullmatch(target),'Unsafe target selector')
    prefix='data/'+slug+('/targets/'+target if target else '')+'/snapshots/'
    # A migrated v1 snapshot remains immutable at its original public path.
    if target and entry['path'].startswith('data/'+slug+'/snapshots/'):
        prefix='data/'+slug+'/snapshots/'
    path=entry['path']
    require(isinstance(path,str) and path.startswith(prefix) and
            re.fullmatch(r'[a-f0-9]{40}-v[12]-\d+-\d+(?:-g\d+-[a-f0-9]{12})?',path[len(prefix):]), 'Unsafe snapshot path')
    require(SHA.fullmatch(entry['revision']) and re.fullmatch(r'[a-f0-9]{64}',entry['manifestSha256']), 'Invalid report lock identity')
    return path


def snapshot_directory(root,slug,entry,target=None):
    root=Path(root).resolve()
    path=root/snapshot_path(slug,entry,target)
    expected=root/'data'/slug
    if '/targets/' in entry['path']:expected=expected/'targets'/str(target)/'snapshots'
    else:expected=expected/'snapshots'
    require(path.resolve().is_relative_to(expected) and not path.is_symlink(),'Snapshot path escapes its store')
    return path
