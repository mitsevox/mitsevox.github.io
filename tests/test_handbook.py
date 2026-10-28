"""Check that every wiki chapter is routable, that nothing written for the standard carries an em
dash, and that the starter kit works as a repository: its tools and tests run in a scratch
checkout built from the kit, and the scaffold check finds nothing to warn about there."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'docs/wiki/starter'
CHECK = ROOT / '.github/actions/scaffold-check/scaffold_check.py'
DIGEST = 'ghcr.io/owner/game-build@sha256:' + '0' * 64


def kit_checkout(folder):
    """A repository that followed the guide: the kit copied, the templates renamed, the parameters
    filled with the kit's placeholder values, one active target scaffolded and hashed."""
    root = Path(folder)
    for path in sorted(KIT.rglob('*')):
        if path.is_file() and 'build-image' not in path.parts and path.name != 'scaffold.json':
            dest = root / path.relative_to(KIT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, dest)
    (root / '.github/workflows/validate.yml.template').rename(root / '.github/workflows/validate.yml')
    (root / 'README.md.template').rename(root / 'README.md')
    (root / 'tools/project.py').write_text('"""dtk-template stand-in."""\n')
    (root / 'configure.py').write_text('from tools.targets import registry, build_targets\n'
                                       'config.dtk_tag = "v1.8.3"\nconfig.objdiff_tag = "v3.6.1"\n'
                                       'def MatchingFor(*versions):\n    return config.version in versions\n'
                                       'Object(MatchingFor("GAME01-rev0"), "unit.cpp")\n')
    (root / 'src').mkdir()
    (root / 'src/unit.cpp').write_text('#include "version.h"\n#if VERSION_GAME01_REV0\nint rev0;\n#else\nint later;\n#endif\n')
    (root / 'licenses').mkdir()
    targets = json.loads((root / 'config/targets.json').read_text())
    for target in targets['targets']:
        subprocess.run([sys.executable, 'tools/new_target.py', target['id']], cwd=root, check=True, capture_output=True)
        if target['status'] == 'active':
            folder = root / 'config' / target['id']
            (folder / 'build.sha1').write_text(target['sha1'] + '  build/%s/main.dol\n' % target['id'])
            (folder / 'splits.txt').write_text('')
            (folder / 'symbols.txt').write_text('')
    return root


def run(args, cwd, env=None):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, env={**os.environ, **(env or {})})


class HandbookTests(unittest.TestCase):
    def test_every_registered_chapter_is_routable(self):
        module = (ROOT / 'assets/wiki-chapters.js').read_text()
        slugs = json.loads(module.split('Object.freeze(', 1)[1].split(');', 1)[0])
        chapters = json.loads((ROOT / 'docs/wiki/chapters.json').read_text())
        self.assertEqual(slugs, [chapter['slug'] for chapter in chapters])
        for slug in slugs:
            route = ROOT / 'wiki' if slug == 'start-here' else ROOT / 'wiki' / slug
            self.assertTrue((route / 'index.html').is_file())
            self.assertTrue((route / 'content.html').is_file())
        for stale in (ROOT / 'wiki').iterdir():
            if stale.is_dir() and stale.name != 'downloads':
                self.assertIn(stale.name, slugs, 'wiki/%s has no chapter' % stale.name)

    def test_no_em_dash_in_the_standard(self):
        folders = [ROOT / 'docs/wiki', ROOT / 'wiki', ROOT / 'tools', ROOT / 'config', ROOT / '.github', ROOT / 'tests']
        offenders = []
        for folder in folders:
            for path in folder.rglob('*'):
                if path.is_file() and path.suffix in ('.md', '.py', '.json', '.yml', '.template', '.h', '.html', '.js', '.txt', '.gitignore', '.gitattributes', ''):
                    try:
                        text = path.read_text()
                    except (UnicodeDecodeError, OSError):
                        continue
                    if chr(0x2014) in text:
                        offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_kit_checkout_passes_its_tools_tests_and_the_scaffold_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = kit_checkout(tmp)
            tests = run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'], root)
            self.assertEqual(tests.returncode, 0, tests.stderr)
            for tool in (['tools/targets.py', 'check'], ['tools/versions.py', 'check'], ['tools/evidence.py', 'check']):
                result = run([sys.executable] + tool, root)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            view = run([sys.executable, 'tools/versions.py', 'view', '--target', 'GAME01-rev0', 'src/unit.cpp'], root)
            self.assertEqual(view.stdout.split('\n')[:2], ['#include "version.h"', 'int rev0;'])
            diff = run([sys.executable, 'tools/versions.py', 'diff', '--target', 'GAME01-rev0', '--target', 'GAME01-rev1', 'src/unit.cpp'], root)
            self.assertIn('-int rev0;', diff.stdout)
            self.assertIn('+int later;', diff.stdout)
            tools = run([sys.executable, 'tools/measuring_tools.py'], root, {'BUILD_IMAGE': DIGEST})
            self.assertEqual(tools.stdout.split('\n')[0], 'build-environment=' + DIGEST)
            check = run([sys.executable, str(CHECK), '--repo', str(root), '--strict'], ROOT)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertIn('0 findings', check.stdout)

    def test_planner_reads_push_and_dispatch_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = kit_checkout(tmp)
            git = ['git', '-c', 'user.email=t@example.com', '-c', 'user.name=t']
            run(['git', 'init', '-q'], root)
            run(git + ['add', '-A'], root)
            run(git + ['commit', '-qm', 'base'], root)
            base = run(['git', 'rev-parse', 'HEAD'], root).stdout.strip()
            (root / 'config/GAME01-rev1/README.md').write_text('# planned\n')
            run(git + ['commit', '-qam', 'planned only'], root)
            head = run(['git', 'rev-parse', 'HEAD'], root).stdout.strip()
            event = root / 'event.json'
            event.write_text(json.dumps({'before': base}))
            env = {'GITHUB_EVENT_PATH': str(event), 'GITHUB_EVENT_NAME': 'push', 'GITHUB_SHA': head}
            push = run([sys.executable, 'tools/ci_targets.py'], root, env)
            self.assertEqual(json.loads(push.stdout)['targets'], [], push.stdout + push.stderr)
            env['GITHUB_EVENT_NAME'] = 'workflow_dispatch'
            dispatch = run([sys.executable, 'tools/ci_targets.py'], root, env)
            self.assertEqual(json.loads(dispatch.stdout), {'targets': ['GAME01-rev0'], 'changedPaths': [], 'forced': True})

    def test_planner_and_tier_diff_a_pull_request_from_its_merge_commit(self):
        # The event's base.sha lags the branch tip the test merge commit was built on: the
        # base's newer commit (an inferred evidence row, tier A) is not the pull request's.
        with tempfile.TemporaryDirectory() as tmp:
            root = kit_checkout(tmp)
            git = lambda *a: run(['git', '-c', 'user.email=t@example.com', '-c', 'user.name=t', *a], root).stdout.strip()
            git('init', '-q', '-b', 'main')
            git('add', '-A')
            git('commit', '-qm', 'base')
            stale = git('rev-parse', 'HEAD')
            git('switch', '-q', '-c', 'pr')
            (root / 'docs').mkdir(exist_ok=True)
            (root / 'docs/note.md').write_text('note\n')
            git('add', '-A')
            git('commit', '-qm', 'docs')
            tip = git('rev-parse', 'HEAD')
            git('switch', '-q', 'main')
            with open(root / 'config/GAME01-rev0/evidence.tsv', 'a') as rows:
                rows.write('function\t0x80001000\t0x80001010\tfoo\tinferred\texact\texact\tloads\n')
            git('commit', '-qam', 'another pull request')
            git('switch', '-q', '--detach', 'main')
            git('merge', '-q', '--no-ff', '-m', 'test merge', 'pr')
            merge = git('rev-parse', 'HEAD')
            event = root / 'event.json'
            event.write_text(json.dumps({'pull_request': {'base': {'sha': stale}, 'head': {'sha': tip}, 'body': '## Scope\n\nTier C, docs'}}))
            env = {'GITHUB_EVENT_PATH': str(event), 'GITHUB_EVENT_NAME': 'pull_request', 'GITHUB_SHA': merge}
            plan = run([sys.executable, 'tools/ci_targets.py'], root, env)
            self.assertEqual(json.loads(plan.stdout)['changedPaths'], ['docs/note.md'], plan.stdout + plan.stderr)
            tier = run([sys.executable, 'tools/tier.py'], root, env)
            self.assertEqual(tier.returncode, 0, tier.stdout + tier.stderr)
            self.assertIn('declared Tier C', tier.stdout)


if __name__ == '__main__':
    unittest.main()
