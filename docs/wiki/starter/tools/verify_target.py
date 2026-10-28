#!/usr/bin/env python3
"""Verify the private original against config/targets.json before configuring a build."""
import argparse
import hashlib
from pathlib import Path
try:
    from tools.targets import select
except ModuleNotFoundError:
    from targets import select

# PARAMETER: the original's path inside orig/<target id>/. The build image provides the same file
# at /orig/<target id>/<this path>, and validate.yml copies it into the checkout before this check.
ORIGINAL='sys/main.dol'


def verify(target_id,root=Path('.')):
    item=select(target_id)
    if item['status']!='active':raise ValueError('Target is not active')
    original=root/'orig'/target_id/ORIGINAL
    if not original.is_file() or original.is_symlink():raise ValueError('Missing/unsafe target original')
    if hashlib.sha1(original.read_bytes()).hexdigest()!=item['sha1']:raise ValueError('Original executable SHA-1 differs')
    return item


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--target',required=True)
    print(verify(parser.parse_args().target)['id']+': original SHA-1 verified')
