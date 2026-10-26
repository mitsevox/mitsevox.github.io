#!/usr/bin/env python3
"""Select the presentation lane; unknown files or comparison failures run full CI."""
import os
from pathlib import Path, PurePosixPath
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PRESENTATION = frozenset({
    'assets/style.css', 'assets/portfolio.css', 'assets/wiki.css',
    'assets/game.html', 'assets/hub.html',
    'assets/shell.js', 'assets/console-icon.js',
})
SHA = re.compile(r'[0-9a-f]{40}')
IMAGE_SUFFIXES = {'.webp', '.png', '.jpg', '.jpeg', '.svg', '.avif'}


def presentation_path(path):
    parts = PurePosixPath(path).parts
    if not parts or path != '/'.join(parts) or any(p in ('.', '..') for p in parts):
        return False
    return path in PRESENTATION or (
        len(parts) >= 3 and parts[:2] in (('assets', 'covers'), ('assets', 'banners'))
        and PurePosixPath(path).suffix.lower() in IMAGE_SUFFIXES
    )


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)


def select_lane(root, event, head, base='', before='', ref=''):
    if event not in ('push', 'pull_request') or not SHA.fullmatch(head):
        return 'full'
    try:
        if event == 'pull_request':
            start = base
        elif ref == 'refs/heads/main':
            start = before
        else:
            # Compare the whole work branch, not only its latest push: an earlier
            # data-reader change must not be hidden by a later stylesheet commit.
            start = git(root, 'merge-base', 'origin/main', head).decode().strip()
        if not SHA.fullmatch(start) or start == '0' * 40:
            return 'full'
        git(root, 'merge-base', '--is-ancestor', start, head)
        paths = [p.decode('utf-8') for p in git(
            root, 'diff', '--no-renames', '--name-only', '-z', start, head
        ).split(b'\0') if p]
        if not paths or not all(presentation_path(p) for p in paths):
            return 'full'
        # Symlinks/submodules can introduce content outside the named path.
        for revision in (start, head):
            for entry in git(root, 'ls-tree', '-z', revision, '--', *paths).split(b'\0'):
                if entry and entry.split(b' ', 1)[0] != b'100644':
                    return 'full'
        return 'ui'
    except (subprocess.CalledProcessError, UnicodeError, OSError):
        return 'full'


if __name__ == '__main__':
    lane = select_lane(ROOT, os.getenv('GITHUB_EVENT_NAME', ''), os.getenv('GITHUB_SHA', ''),
                       os.getenv('CI_BASE_SHA', ''), os.getenv('CI_BEFORE_SHA', ''),
                       os.getenv('GITHUB_REF', ''))
    print('Selected CI lane:', lane)
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f'lane={lane}\n')
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write(f'### CI lane: {lane}\n\n' + (
                'Presentation-only changes: validate stored reports, build, and deploy. '
                'No producer refresh or report-store publication.\n' if lane == 'ui' else
                'Full regression tests and normal report refresh/publication policy apply.\n'))
