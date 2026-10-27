"""Shared package integrity, registered format dispatch and validation utilities."""
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_JSON = 32 * 1024 * 1024
SHA = re.compile(r'[a-f0-9]{40}')
ADDRESS = re.compile(r'0x[A-F0-9]{8}')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def decode(data):
    require(len(data) <= MAX_JSON, 'JSON exceeds size limit')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Nonfinite JSON number: ' + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def schema(document, filename):
    from jsonschema import Draft202012Validator, FormatChecker
    spec = decode((ROOT / 'docs/reporting/schema' / filename).read_bytes())
    errors = sorted(Draft202012Validator(spec, format_checker=FormatChecker()).iter_errors(document),
                    key=lambda e: str(list(e.path)))
    require(not errors, str(errors[0])[:800] if errors else '')


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'Timestamp needs a timezone')
    return parsed.timestamp()


def integer(value):
    return type(value) is int and 0 <= value <= 2**53 - 1


def validate_package(directory, root=ROOT):
    from .registry import package_policy
    directory = Path(directory)
    require(not directory.is_symlink() and directory.is_dir(), 'Unsafe package directory')
    manifest = decode((directory/'manifest.json').read_bytes())
    version=manifest.get('schemaVersion')
    require(type(version) is int and version in (1,2),'Unsupported report version')
    schema(manifest, 'report-v'+str(version)+'.schema.json')
    ref=manifest['validation']['receipt']
    receipt_path=directory/'receipt.json'
    require(ref['path']=='receipt.json' and receipt_path.is_file() and not receipt_path.is_symlink(), 'Unsafe receipt reference')
    raw=receipt_path.read_bytes()
    require(digest(raw)==ref['sha256'],'Receipt checksum differs')
    policy=package_policy(root,manifest,decode(raw)['workflowBlob'])
    if policy['format'] == 'nfl-legacy-v1':
        from .archives.legacy_nfl import validate_package as validate_legacy
        return validate_legacy(directory, root, policy)
    from .standard import validate_package as validate_standard
    return validate_standard(directory, manifest, policy)


# Compatibility imports for callers of the original validator API.
def validate_progress(*args):
    from .archives.legacy_nfl import validate_progress as validate
    return validate(*args)


def validate_activity(*args):
    from .archives.legacy_nfl import validate_activity as validate
    return validate(*args)


def summary(*args):
    from .archives.legacy_nfl import summary as summarize
    return summarize(*args)


def merged_ranges(ranges):
    result=[]
    for start,end in sorted(ranges):
        require(not result or start>=result[-1][1], 'Overlapping map ranges')
        if result and start==result[-1][1]:result[-1]=(result[-1][0],end)
        else:result.append((start,end))
    return result
