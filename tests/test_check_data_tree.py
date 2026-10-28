"""tools/check_data_tree.py: both readers accept a tree the publisher wrote; a tree the
publisher's checker refuses stops there, naming the file; a map only the page refuses, on any
target, still fails the tool."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/actions/publish'))
sys.path.insert(0, str(ROOT / 'tests'))
import publish  # noqa: E402
from test_publish import SITE, TARGETS, SECTIONS, REV, latest, report  # noqa: E402


def check(tree):
    return subprocess.run([sys.executable, str(ROOT / 'tools/check_data_tree.py'), str(tree)],
                          cwd=ROOT, capture_output=True, text=True)


def tree_from(*reports):
    """A tree with one active target per report: GAME01-rev0, then GAME01-rev1."""
    tree = Path(tempfile.mkdtemp())
    targets = copy.deepcopy(TARGETS['targets'])
    targets[1]['status'] = 'active'
    game = publish.game_document(SITE, targets, 'GAME01-rev0', 'owner/game')
    for r, target in zip(reports, targets):
        measurement = latest(REV[0], '2026-01-01T00:00:00Z', '2026-01-01T00:01:00Z', publish.summary(r, SECTIONS))
        measurement['target'] = target['id']
        publish.write_target(tree, game, measurement, publish.map_document(r, SECTIONS))
    return tree


def huge_report():
    # The page keeps every count a safe integer (below 2^53); the publisher's checker allows
    # 64-bit sizes. A unit that large passes the first reader and not the second.
    r = report()
    unit, auto = r['units']
    big = 2 ** 53 - 16  # the exact function becomes exactly 2^53 bytes; what follows moves up
    unit['sections'][0]['size'] = str(32 + big)
    unit['sections'][1]['metadata']['virtual_address'] = str(2147500000 + big)
    unit['functions'][0]['size'] = str(16 + big)
    unit['functions'][1]['metadata']['virtual_address'] = str(2147483664 + big)
    unit['measures'].update(total_code=str(32 + big), matched_code=str(16 + big))
    auto['sections'][0]['metadata']['virtual_address'] = str(2147483680 + big)
    auto['functions'][0]['metadata']['virtual_address'] = str(2147483680 + big)
    r['measures'].update(total_code=str(48 + big), matched_code=str(16 + big), complete_code=str(32 + big))
    return r


class CheckDataTreeTests(unittest.TestCase):
    def test_both_readers_accept_what_the_publisher_writes(self):
        tree = tree_from(report(), report())
        # A target archived after it was published keeps its measurement, and both readers still
        # check it: more than the page shows, exactly what every publish enforces.
        game_path = tree / 'data/game/game.json'
        game = json.loads(game_path.read_text())
        game['targets'][1]['status'] = 'archived'
        game_path.write_text(json.dumps(game))
        result = check(tree)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('publish.py check: 2 target(s) accepted', result.stdout)
        self.assertIn('page validator: 2 map(s) accepted', result.stdout)

    def test_a_tree_the_publisher_refuses_stops_before_the_page_and_names_the_file(self):
        tree = tree_from(report(), report())
        path = tree / 'data/game/GAME01-rev1/map.json'
        document = json.loads(path.read_text())
        document['files'][0]['children'][0]['linked'] = None  # a hand edit; the page needs integer counts
        path.write_text(json.dumps(document))
        result = check(tree)
        self.assertEqual(result.returncode, 1)
        self.assertIn("publish.py check refuses the tree: game/GAME01-rev1/map.json: map: 'Exact' lacks a count", result.stdout)
        self.assertNotIn('page validator', result.stdout)
        result = check(Path(tempfile.gettempdir()) / 'no-such-data-tree')
        self.assertEqual(result.returncode, 1)
        self.assertIn('refuses the tree', result.stdout)

    def test_a_map_only_the_page_refuses_fails_the_tool_on_any_target(self):
        tree = tree_from(report(), huge_report())
        self.assertEqual(publish.check_tree(tree), 2)
        result = check(tree)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('publish.py check: 2 target(s) accepted', result.stdout)
        self.assertIn('game/GAME01-rev1/map.json: the page refuses it', result.stdout)
        self.assertNotIn('GAME01-rev0/map.json: the page refuses', result.stdout)
        self.assertIn('page validator: 1 map(s) accepted', result.stdout)


if __name__ == '__main__':
    unittest.main()
