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
    require(set(item)=={'format','policy'} and item['format'] in ('report-v1','nfl-legacy-v1'),'Unknown producer format')
    require(re.fullmatch(r'[a-zA-Z0-9_-]+\.json',item['policy']),'Unsafe producer policy path')
    policy=decode((root/'config'/item['policy']).read_bytes())
    require(policy['repository'].split('/')[0].lower()==site_config(root)['owner'].lower(),'Producer must belong to the site owner')
    if item['format']=='report-v1':schema(policy,'producer-v1.schema.json')
    else:require(all(SHA.fullmatch(x) for x in policy['workflowBlobs']),'Invalid workflow identities')
    return {**policy,'format':item['format'],'project':slug}


def producer(root,slug):
    require(isinstance(slug,str) and SLUG.fullmatch(slug),'Invalid project slug')
    item=registrations(root).get(slug)
    require(item is not None,'Unregistered project: '+slug)
    require(set(item)<= {'format','policy','archives'} and {'format','policy'}<=set(item),'Invalid producer registration')
    return load_policy(root,slug,{k:item[k] for k in ('format','policy')})


def package_policy(root,manifest,workflow_blob):
    slug=manifest['project'];current=producer(root,slug)
    registration=registrations(root)[slug]
    policies=[current]+[load_policy(root,slug,item) for item in registration.get('archives',[])]
    formats={'execution-v1':'report-v1','nfl-execution-v1':'nfl-legacy-v1'}
    format_name=formats.get(manifest['validation']['receipt']['schema'])
    def tools_match(policy):
        expected=policy['tools'] if policy['format']=='report-v1' else [
            {'name':'build-environment','identity':policy['environment']},
            {'name':'producer-workflow','identity':workflow_blob}]
        return manifest['tools']==expected
    matching=[p for p in policies if tools_match(p) and p['format']==format_name and p['repository']==manifest['repository']
              and p['repository']==current['repository'] and p['target']==manifest['target']
              and workflow_blob in p['workflowBlobs']]
    require(matching,'Package differs from registered producer policy')
    return matching[0]


def snapshot_path(slug, entry):
    require(SLUG.fullmatch(slug), 'Invalid snapshot project')
    prefix='data/'+slug+'/snapshots/'
    path=entry['path']
    require(isinstance(path,str) and path.startswith(prefix) and
            re.fullmatch(r'[a-f0-9]{40}-v1-\d+-\d+(?:-g\d+-[a-f0-9]{12})?',path[len(prefix):]), 'Unsafe snapshot path')
    require(SHA.fullmatch(entry['revision']) and re.fullmatch(r'[a-f0-9]{64}',entry['manifestSha256']), 'Invalid report lock identity')
    return path


def snapshot_directory(root,slug,entry):
    root=Path(root).resolve()
    path=root/snapshot_path(slug,entry)
    expected=root/'data'/slug/'snapshots'
    require(path.resolve().is_relative_to(expected) and not path.is_symlink(),'Snapshot path escapes its store')
    return path
