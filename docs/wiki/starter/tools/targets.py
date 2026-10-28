"""Explicit target inventory (the site's schema-1 targets.json); no inferred revision aliases or
filesystem discovery. An active target is built, verified and measured; planned and archived
targets are listed only."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
FIELDS={'id','platform','label','region','revision','sha1','status'}


def registry(path=None):
    value=json.loads(Path(path or ROOT/'config/targets.json').read_text())
    if set(value)!={'schema','defaultTarget','targets'} or value['schema']!=1:raise ValueError('Invalid target registry')
    ids=set()
    for target in value['targets']:
        if set(target)!=FIELDS:raise ValueError('Unknown target fields')
        if not (re.fullmatch(r'[A-Za-z0-9._-]+',target['id']) and re.fullmatch(r'[a-z0-9]+',target['platform'])
                and all(isinstance(target[k],str) and target[k].strip() for k in ('label','region','revision'))
                and re.fullmatch(r'[a-f0-9]{40}',target['sha1'])):raise ValueError('Invalid target identity')
        if target['status'] not in ('active','planned','archived'):raise ValueError('Invalid target status')
        if target['id'] in ids:raise ValueError('Duplicate target')
        ids.add(target['id'])
    if value['defaultTarget'] not in build_targets(value):raise ValueError('Default target is not active')
    return value


def build_targets(value=None):
    value=value or registry()
    return [target['id'] for target in value['targets'] if target['status']=='active']


def select(target_id,value=None):
    value=value or registry()
    matches=[target for target in value['targets'] if target['id']==target_id]
    if len(matches)!=1:raise ValueError('Unknown explicit target: '+target_id)
    return matches[0]
