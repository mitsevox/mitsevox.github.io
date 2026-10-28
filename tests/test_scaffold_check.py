"""The scaffold check: each drift check fires on a broken checkout and stays quiet on a clean one,
and the settings read compares what the default token can see without any network."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_handbook import kit_checkout  # noqa: E402

spec = importlib.util.spec_from_file_location('scaffold_check', ROOT / '.github/actions/scaffold-check/scaffold_check.py')
scaffold_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scaffold_check)


def findings(root):
    return [(path, message) for path, message in scaffold_check.Check(root).run()]


def messages(root, path):
    return [message for p, message in findings(root) if p == path]


class ScaffoldCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.clean = kit_checkout(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def broken(self):
        folder = tempfile.mkdtemp()
        shutil.rmtree(folder)
        shutil.copytree(self.clean, folder)
        self.addCleanup(shutil.rmtree, folder)
        return Path(folder)

    def test_clean_checkout_has_no_findings(self):
        self.assertEqual(findings(self.clean), [])

    def test_required_paths_and_root_allowlist(self):
        root = self.broken()
        (root / 'include/version.h').unlink()
        (root / 'notes.txt').write_text('')
        (root / 'Makefile').unlink(missing_ok=True)
        self.assertIn('required file is missing', messages(root, 'include/version.h'))
        self.assertTrue(messages(root, 'notes.txt'))

    def test_per_target_files_and_hashes(self):
        root = self.broken()
        (root / 'config/GAME01-rev0/build.sha1').write_text('f' * 40 + '  build/main.dol\n')
        (root / 'orig/GAME01-rev1/.gitkeep').unlink()
        self.assertTrue(any('differs' in m for m in messages(root, 'config/GAME01-rev0/build.sha1')))
        self.assertTrue(messages(root, 'orig/GAME01-rev1/.gitkeep'))

    def test_versions_evidence_and_ci_targets(self):
        root = self.broken()
        (root / 'src/unit.cpp').write_text('#if VERSION_NOPE\n#endif\n')
        (root / 'config/GAME01-rev0/evidence.tsv').write_text('kind\tstart\n')
        deps = json.loads((root / 'config/ci-targets.json').read_text())
        deps['targets'] = {}
        (root / 'config/ci-targets.json').write_text(json.dumps(deps))
        self.assertTrue(any('VERSION_NOPE' in m for m in messages(root, 'src')))
        self.assertTrue(any('header row' in m for m in messages(root, 'config')))
        self.assertTrue(any("'targets' key" in m for m in messages(root, 'config/ci-targets.json')))

    def test_byte_identical_and_outline_files(self):
        root = self.broken()
        (root / 'tools/evidence.py').write_text('# changed\n')
        (root / 'README.md').write_text('# Game\n\n## Building\n\n## Targets\n')
        (root / 'AGENTS.md').write_text('# My rules\n\n## Project\n')
        (root / 'CONTRIBUTING.md').write_text('# Contributing\n\n## Rules\n')
        (root / '.github/pull_request_template.md').write_text('## Scope\n')
        self.assertTrue(messages(root, 'tools/evidence.py'))
        self.assertTrue(any('headings must be' in m for m in messages(root, 'README.md')))
        self.assertTrue(any('kit header' in m for m in messages(root, 'AGENTS.md')))
        self.assertTrue(any('section headings' in m for m in messages(root, 'CONTRIBUTING.md')))
        self.assertTrue(any('## Targets' in m for m in messages(root, '.github/pull_request_template.md')))

    def test_workflow_skeleton(self):
        root = self.broken()
        workflow = root / '.github/workflows/validate.yml'
        text = workflow.read_text().replace('- name: Configure target', '- name: Set up')
        text = text.replace('BUILD_IMAGE: ghcr.io/owner/game-build@sha256:' + '0' * 64, 'BUILD_IMAGE: ghcr.io/owner/game-build:main')
        text = text.replace('uses: mitsevox/mitsevox.github.io/.github/actions/scaffold-check@main', 'uses: nobody/else@v1')
        text = text.replace('uses: mitsevox/mitsevox.github.io/.github/actions/check-report@main', 'uses: nobody/check@v1')
        workflow.write_text(text)
        (root / '.github/workflows/review.yml').write_text('name: Review\n')
        found = messages(root, '.github/workflows/validate.yml')
        self.assertTrue(any("'Configure target' is missing" in m for m in found))
        self.assertTrue(any("'Set up' is not in the skeleton" in m for m in found))
        self.assertTrue(any('digest-pinned' in m for m in found))
        self.assertTrue(any('scaffold-check@main' in m for m in found))
        self.assertTrue(any('check-report@main' in m for m in found))
        self.assertTrue(messages(root, '.github/workflows/review.yml'))
        workflow.write_text(workflow.read_text().replace('      - name: List measuring tools', '      - name: Project checks\n        run: true\n      - name: List measuring tools'))
        self.assertFalse(any("'Project checks' is not" in m for m in messages(root, '.github/workflows/validate.yml')))
        # The environment's name line is not a step, and the publish environment must stay main-only.
        self.assertFalse(any('publish' in m for m in messages(root, '.github/workflows/validate.yml')))
        environment = "name: ${{ github.ref == 'refs/heads/main' && (github.event_name == 'push' || github.event_name == 'workflow_dispatch') && 'publish' || 'validate' }}"
        self.assertIn(environment, workflow.read_text())
        workflow.write_text(workflow.read_text().replace(environment, 'name: publish'))
        self.assertTrue(any('publish environment' in m for m in messages(root, '.github/workflows/validate.yml')))

    def test_forbidden_paths_references_and_gitignore(self):
        root = self.broken()
        (root / 'docs/dtk').mkdir(parents=True)
        (root / 'config/GAME01-rev0/config.example.yml').write_text('')
        (root / 'references').mkdir()
        (root / 'references/big.txt').write_bytes(b'0' * (4 * 1024 * 1024 + 1))
        (root / '.gitignore').write_text('/build/\n')
        self.assertTrue(messages(root, 'docs/dtk'))
        self.assertTrue(messages(root, 'config/GAME01-rev0/config.example.yml'))
        self.assertTrue(messages(root, 'references/big.txt'))
        self.assertEqual(sorted(m.split()[-1] for m in messages(root, '.gitignore')), ['*.dol', '*.elf', 'orig/*/*'])

    def test_settings_read_compares_the_readable_half(self):
        check = scaffold_check.Check(self.clean)
        # /rules/branches/main is the union of every ruleset: `update` comes from the merges ruleset.
        rules = [{'type': 'update'}, {'type': 'deletion'}, {'type': 'non_fast_forward'},
                 {'type': 'pull_request', 'parameters': {'dismiss_stale_reviews_on_push': True, 'allowed_merge_methods': ['squash']}},
                 {'type': 'required_status_checks', 'parameters': {'strict_required_status_checks_policy': False,
                  'required_status_checks': [{'context': 'Validate targets'}]}}]
        repo = {'default_branch': 'main', 'description': 'Scooby-Doo! Night of 100 Frights (GameCube, 2002) decompilation',
                'homepage': 'https://mitsevox.github.io/games/n100f/', 'topics': ['decompilation', 'gamecube', 'n100f'],
                'has_issues': True, 'has_wiki': False, 'has_projects': False, 'has_discussions': False,
                'allow_squash_merge': True, 'allow_merge_commit': False, 'allow_rebase_merge': False,
                'allow_auto_merge': False, 'delete_branch_on_merge': True}
        responses = {'/repos/mitsevox/n100f': (200, repo), '/repos/mitsevox/n100f/rules/branches/main': (200, rules)}
        check.settings('mitsevox/n100f', 'token', fetch=lambda path: responses[path])
        self.assertEqual(check.findings, [])
        repo['has_wiki'] = True
        rules.pop()
        check.settings('mitsevox/n100f', 'token', fetch=lambda path: responses[path])
        self.assertEqual(sorted(m.split(':')[0] for _, m in check.findings), ['repository.has_wiki', 'ruleset.required_status_checks'])
        # Without the merges ruleset a writer could merge: its update rule is expected on main.
        check = scaffold_check.Check(self.clean)
        rules.pop(0)
        check.settings('mitsevox/n100f', 'token', fetch=lambda path: responses[path])
        self.assertIn('ruleset.rule.update', [m.split(':')[0] for _, m in check.findings])
        unlisted = scaffold_check.Check(self.clean)
        responses['/repos/x/y'] = (200, dict(repo, description='anything', topics=[]))
        responses['/repos/x/y/rules/branches/main'] = (403, None)
        unlisted.settings('x/y', 'token', fetch=lambda path: responses[path])
        self.assertFalse(any('description' in m or 'topics' in m for _, m in unlisted.findings))
        self.assertTrue(any('ruleset.rule.deletion' in m for _, m in unlisted.findings))


if __name__ == '__main__':
    unittest.main()
