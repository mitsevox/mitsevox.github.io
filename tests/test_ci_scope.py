import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from ci_scope import presentation_path, select_lane


class ScopeTests(unittest.TestCase):
    def test_allowlist_excludes_report_readers_and_unknown_files(self):
        for path in ('assets/style.css', 'assets/game.html', 'assets/shell.js',
                     'assets/covers/game.webp'):
            self.assertTrue(presentation_path(path), path)
        for path in ('assets/reports.js', 'assets/hub.js', 'assets/identity.js',
                     'assets/progress.js', 'assets/activity.js', 'assets/projects.js',
                     'assets/report-projects.js', 'assets/app.js', 'tools/build_site.py',
                     'config/projects.json', 'data/reports.lock.json',
                     'docs/reporting/schema/map-v2.schema.json', '.github/workflows/site.yml',
                     'assets/new.js', 'assets/../tools/x.svg', '/assets/style.css',
                     'assets//style.css', 'assets/covers/x.json'):
            self.assertFalse(presentation_path(path), path)

    def test_commit_ranges_and_failure_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def run(*args):
                return subprocess.check_output(['git', '-C', directory, *args], stderr=subprocess.PIPE).decode().strip()

            def commit(path, value):
                file = root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(value)
                run('add', '.')
                run('commit', '-qm', 'fixture')
                return run('rev-parse', 'HEAD')

            run('init', '-q', '-b', 'main')
            run('config', 'user.email', 'test@example.test')
            run('config', 'user.name', 'Test')
            initial = commit('assets/style.css', 'old')
            run('update-ref', 'refs/remotes/origin/main', initial)
            ui = commit('assets/style.css', 'new')
            for event, kwargs in (
                ('pull_request', {'base': initial}),
                ('push', {'before': initial, 'ref': 'refs/heads/main'}),
                ('push', {'ref': 'refs/heads/codex/presentation'}),
            ):
                self.assertEqual(select_lane(root, event, ui, **kwargs), 'ui')
            reader = commit('assets/reports.js', 'changed reader')
            later = commit('assets/style.css', 'another style')
            # Full-branch and multi-commit main comparisons retain reader changes.
            self.assertEqual(select_lane(root, 'push', later, ref='refs/heads/codex/work'), 'full')
            self.assertEqual(select_lane(root, 'push', later, before=initial, ref='refs/heads/main'), 'full')
            self.assertEqual(select_lane(root, 'pull_request', later, base=ui), 'full')
            self.assertEqual(select_lane(root, 'schedule', ui), 'full')
            self.assertEqual(select_lane(root, 'workflow_dispatch', ui), 'full')
            self.assertEqual(select_lane(root, 'push', ui, before='0' * 40, ref='refs/heads/main'), 'full')
            self.assertEqual(select_lane(root, 'pull_request', ui, base='f' * 40), 'full')
            self.assertEqual(select_lane(root, 'pull_request', initial, base=initial), 'full')
            # A rename from data-reading code into an allowed name is still full.
            run('mv', 'assets/reports.js', 'assets/shell.js')
            run('commit', '-qam', 'rename')
            renamed = run('rev-parse', 'HEAD')
            self.assertEqual(select_lane(root, 'pull_request', renamed, base=later), 'full')
            run('rm', 'assets/style.css')
            (root / 'assets/style.css').symlink_to('../tools/reader.py')
            run('add', '.')
            run('commit', '-qm', 'symlink')
            self.assertEqual(select_lane(root, 'pull_request', run('rev-parse', 'HEAD'), base=renamed), 'full')


if __name__ == '__main__':
    unittest.main()
