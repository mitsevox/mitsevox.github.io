#!/usr/bin/env python3
"""Print the tools that measure each report, one name=identity per line, for the site's provenance:
the digest-pinned build image from the BUILD_IMAGE environment variable (validate.yml exports the
image it runs in) and the tool versions the repository pins: the tags in configure.py, or, for a
build without configure.py, the `version` fields of the JSON pin files named in PINS. validate.yml
passes this output to the publish action's `tools` input."""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGURE = ROOT / 'configure.py'
IMAGE = re.compile(r'ghcr\.io/[^@\s]+@sha256:[0-9a-f]{64}')
# PARAMETER: the `config.<name> = "<version>"` lines of configure.py to report, as name=version.
TAGS = {'dtk': 'dtk_tag', 'objdiff': 'objdiff_tag'}
# PARAMETER: for a build without configure.py, the JSON files that pin its tools, each
# {"<name>": {"version": "<version>", ...}, ...}; every entry is reported. Empty for dtk-template.
PINS = []


def tools(image=None, configure=None, pins=None):
    image = image if image is not None else os.environ.get('BUILD_IMAGE', '')
    if not IMAGE.fullmatch(image):
        raise SystemExit('measuring_tools: BUILD_IMAGE is not a digest-pinned image reference')
    result = [('build-environment', image)]
    pins = pins if pins is not None else [json.loads((ROOT / path).read_text()) for path in PINS]
    if pins:
        for document in pins:
            for name, pin in document.items():
                if not isinstance(pin, dict) or not isinstance(pin.get('version'), str) or not pin['version']:
                    raise SystemExit('measuring_tools: %s has no version' % name)
                result.append((name, pin['version']))
        return result
    configure = configure if configure is not None else CONFIGURE.read_text()
    for name, tag in TAGS.items():
        m = re.search(r'^config\.%s = "([^"]+)"$' % tag, configure, re.M)
        if not m:
            raise SystemExit('measuring_tools: configure.py has no %s' % tag)
        result.append((name, m.group(1)))
    return result


if __name__ == '__main__':
    print('\n'.join('%s=%s' % pair for pair in tools()))
