"""The publisher: objdiff report -> contract files, history append rules and the tree check."""
import copy
import functools
import json
import math
import operator
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/actions/publish'))
import publish  # noqa: E402

SECTIONS = ('.init', '.text')
REV = ['%040x' % n for n in range(1, 5)]


def report():
    """A two-unit objdiff report: one linked unit with an exact and a fuzzy function plus data,
    one tool-generated unit with an unnamed function."""
    return {
        'measures': {'total_code': '48', 'matched_code': '16', 'complete_code': '32',
                     'total_data': '8', 'matched_data': '8', 'complete_data': '8',
                     'total_functions': 3, 'matched_functions': 1},
        'units': [
            {'name': 'main/game/unit', 'metadata': {'complete': True},
             'measures': {'total_code': '32', 'matched_code': '16', 'total_data': '8', 'matched_data': '8'},
             'sections': [{'name': '.text', 'size': '32', 'metadata': {'virtual_address': '2147483648'}},
                          {'name': '.data', 'size': '8', 'fuzzy_match_percent': 100,
                           'metadata': {'virtual_address': '2147500000'}}],
             'functions': [{'name': 'Exact', 'size': '16', 'fuzzy_match_percent': 100,
                            'metadata': {'virtual_address': '2147483648'}},
                           {'name': 'Fuzzy', 'size': '16', 'fuzzy_match_percent': 50,
                            'metadata': {'virtual_address': '2147483664'}}]},
            {'name': 'main/auto_80000020_text', 'metadata': {'auto_generated': True},
             'measures': {'total_code': '16'},
             'sections': [{'name': '.text', 'size': '16', 'metadata': {'virtual_address': '2147483680'}}],
             'functions': [{'name': 'fn_80000020', 'size': '16', 'metadata': {'virtual_address': '2147483680'}}]},
        ],
    }


SITE = {'schema': 1, 'slug': 'game', 'title': 'A Game', 'console': 'GameCube', 'year': '2002'}
TARGETS = {'schema': 1, 'defaultTarget': 'GAME01-rev0', 'targets': [
    {'id': 'GAME01-rev0', 'platform': 'gamecube', 'label': 'GAME01', 'region': 'USA', 'revision': '0',
     'sha1': 'a' * 40, 'status': 'active'},
    {'id': 'GAME01-rev1', 'platform': 'gamecube', 'label': 'GAME01', 'region': 'USA', 'revision': '1',
     'sha1': 'b' * 40, 'status': 'planned'}]}


def latest(revision, committed, measured, s=None):
    return {'schema': 1, 'game': 'game', 'target': 'GAME01-rev0',
            'source': {'revision': revision, 'committedAt': committed, 'title': 't', 'url': 'u', 'runUrl': None},
            'measuredAt': measured, 'tools': [], 'modules': {'map': 'map.json', 'contributors': None},
            'summary': s or publish.summary(report(), SECTIONS)}


class ConversionTests(unittest.TestCase):
    def test_summary_measures(self):
        s = publish.summary(report(), SECTIONS)
        self.assertEqual(s['code'], {'total': 48, 'linked': 32, 'matched': 16, 'fuzzy': 24.0})
        self.assertEqual(s['data'], {'total': 8, 'linked': 8, 'matched': 8, 'fuzzy': 8.0})
        self.assertEqual(s['functions'], {'total': 3, 'exact': 1, 'named': 2})
        self.assertEqual(s['files'], {'total': 2, 'exact': 0, 'named': 1})

    def test_summary_rejects_inconsistent_report(self):
        r = report()
        r['measures']['matched_functions'] = 2
        with self.assertRaises(publish.ContractError):
            publish.summary(r, SECTIONS)

    def test_map_agrees_with_summary(self):
        s = publish.summary(report(), SECTIONS)
        m = publish.map_document(report(), SECTIONS)
        publish.check_map(m, s)
        self.assertEqual([f['name'] for f in m['files']], ['game/unit', 'auto_80000020_text', 'game/unit'])

    def test_code_outside_functions_gets_its_own_tile(self):
        # A producer whose functions do not cover a code section (padding, unsplit code) counts the
        # rest in matched_code; the map shows it as one non-function tile per section piece.
        r = report()
        unit = r['units'][0]
        unit['functions'][1]['size'] = '8'  # Fuzzy now ends at 0x80000018; 8 bytes follow it
        unit['measures']['matched_code'] = '20'
        r['measures']['matched_code'] = '20'
        s = publish.summary(r, SECTIONS)
        self.assertEqual((s['code']['total'], s['code']['matched']), (48, 20))
        self.assertEqual(s['code']['fuzzy'], 16 + 4 + 4)  # exact, half of fuzzy, then 4 other bytes
        m = publish.map_document(r, SECTIONS)
        publish.check_map(m, s)
        other = [c for c in m['files'][0]['children'] if c['name'].endswith('(other code)')]
        self.assertEqual([(c['address'], c['size'], c['matched']) for c in other], [('0x80000018', 8, 4)])
        self.assertNotIn('type', other[0])
        self.assertEqual(s['functions']['total'], 3)
        unit['measures']['matched_code'] = '40'
        with self.assertRaisesRegex(publish.ContractError, 'does not fit'):
            publish.summary(r, SECTIONS)

    def test_function_outside_code_sections_is_named(self):
        with self.assertRaisesRegex(publish.ContractError, 'outside the code sections'):
            publish.map_document(report(), ('.init',))

    def rounding_report(self):
        # nflstreet2's dvd.c: 408 of 632 data bytes exact, sent as one percent on each of its six
        # data extents. Back in bytes they sum to 407.99999999999994, a rounding step below
        # matched_data.
        r = report()
        unit = r['units'][0]
        address = 2147500000
        unit['sections'][1:] = []
        for size in (384, 152, 24, 60, 8, 4):
            unit['sections'].append({'name': '.data', 'size': str(size), 'fuzzy_match_percent': 100 * 408 / 632,
                                     'metadata': {'virtual_address': str(address)}})
            address += size
        unit['measures'].update(total_data='632', matched_data='408')
        r['measures'].update(total_data='632', matched_data='408', complete_data='632')
        return r

    def test_data_fuzzy_stays_within_matched_and_total(self):
        r = self.rounding_report()
        s = publish.summary(r, SECTIONS)
        m = publish.map_document(r, SECTIONS)
        publish.check_map(m, s)
        tile = next(f for f in m['files'] if f['kind'] == 'data')
        self.assertEqual((tile['matched'], tile['fuzzy']), (408, 408))

    def test_the_page_accepts_the_map(self):
        # The page validates every map again before drawing it; run its own check on ours.
        for r in (report(), self.rounding_report()):
            s = publish.summary(r, SECTIONS)
            measures = {kind: {k: s[kind][k] for k in ('total', 'linked', 'matched', 'fuzzy')}
                        for kind in ('code', 'data')}
            script = ("import {validateMap} from './assets/report-map-validation.js';\n"
                      "const [map, measures] = JSON.parse(process.argv[1]);\n"
                      "validateMap(map, measures);\n")
            payload = json.dumps([publish.map_document(r, SECTIONS), measures])
            result = subprocess.run(['node', '--input-type=module', '-e', script, payload],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_map_check_catches_drift(self):
        s = publish.summary(report(), SECTIONS)
        m = publish.map_document(report(), SECTIONS)
        m['files'][0]['children'][0]['matched'] = 0
        with self.assertRaises(publish.ContractError):
            publish.check_map(m, s)

    def test_group_fuzzy_is_added_as_the_page_adds_it(self):
        # The page re-adds a group's children left to right and compares with the group. One
        # 2^40-byte exact function and a hundred 1-byte functions at 10 percent put the exact sum
        # about 0.01 away from that. The publisher writes the page's sum, at the group and in the
        # summary, so its own output passes both readers; a copy holding the exact sum fails both.
        r = report()
        unit, auto = r['units']
        big, base = 2 ** 40, 2147483648
        unit['sections'][0]['size'] = str(big + 100)
        unit['sections'][1]['metadata']['virtual_address'] = str(2147500000 + big)
        unit['functions'] = [{'name': 'Exact', 'size': str(big), 'fuzzy_match_percent': 100, 'metadata': {'virtual_address': str(base)}}]
        unit['functions'] += [{'name': 'f%d' % i, 'size': '1', 'fuzzy_match_percent': 10,
                               'metadata': {'virtual_address': str(base + big + i)}} for i in range(100)]
        unit['measures'].update(total_code=str(big + 100), matched_code=str(big))
        auto['sections'][0]['metadata']['virtual_address'] = str(base + big + 100)
        auto['functions'][0]['metadata']['virtual_address'] = str(base + big + 100)
        r['measures'].update(total_code=str(big + 116), matched_code=str(big), complete_code=str(big + 100), total_functions=102)
        s = publish.summary(r, SECTIONS)
        m = publish.map_document(r, SECTIONS)
        group = m['files'][0]
        exact = math.fsum(c['fuzzy'] for c in group['children'])
        self.assertEqual(exact, big + 10)
        self.assertEqual(group['fuzzy'], functools.reduce(operator.add, (c['fuzzy'] for c in group['children']), 0))
        self.assertGreater(abs(group['fuzzy'] - exact), 1e-6)
        self.assertEqual(s['code']['fuzzy'], group['fuzzy'])  # the other code group adds nothing
        publish.check_map(m, s)
        self.assertFalse(self.page_rejects(m, s))
        m['files'][0]['fuzzy'] = exact
        self.assertTrue(self.page_rejects(m, s))
        with self.assertRaisesRegex(publish.ContractError, 'do not add up'):
            publish.check_map(m, s)

    def page_rejects(self, map_doc, s):
        measures = {kind: {k: s[kind][k] for k in ('total', 'linked', 'matched', 'fuzzy')} for kind in ('code', 'data')}
        script = ("import {validateMap} from './assets/report-map-validation.js';\n"
                  "const [map, measures] = JSON.parse(process.argv[1]);\n"
                  "validateMap(map, measures);\n")
        result = subprocess.run(['node', '--input-type=module', '-e', script, json.dumps([map_doc, measures])],
                                cwd=ROOT, capture_output=True, text=True)
        return result.returncode != 0

    def test_map_check_is_exactly_as_strict_as_the_page(self):
        # The page sums children with an absolute tolerance of 1e-6 and no relative one. A big
        # unit whose group fuzzy is 1.5e-6 off its children is refused by the page; a relative
        # tolerance would have let the publisher accept it.
        r = report()
        unit, auto = r['units']
        big = 4000000  # the exact function grows by this; everything after it moves up by this
        unit['sections'][0]['size'] = str(32 + big)
        unit['sections'][1]['metadata']['virtual_address'] = str(2147500000 + big)
        unit['functions'][0]['size'] = str(16 + big)
        unit['functions'][1]['metadata']['virtual_address'] = str(2147483664 + big)
        unit['measures'].update(total_code=str(32 + big), matched_code=str(16 + big))
        auto['sections'][0]['metadata']['virtual_address'] = str(2147483680 + big)
        auto['functions'][0]['metadata']['virtual_address'] = str(2147483680 + big)
        r['measures'].update(total_code=str(48 + big), matched_code=str(16 + big), complete_code=str(32 + big))
        s = publish.summary(r, SECTIONS)
        self.assertEqual(s['code']['fuzzy'], 16 + big + 8)
        m = publish.map_document(r, SECTIONS)
        publish.check_map(m, s)
        self.assertFalse(self.page_rejects(m, s))  # the page accepts the map as written
        m['files'][0]['fuzzy'] += 1.5e-6
        self.assertTrue(self.page_rejects(m, s))
        with self.assertRaisesRegex(publish.ContractError, 'fuzzy'):  # off the summary and off its children
            publish.check_map(m, s)
        # Four more shapes the page refuses: a node without a name, an empty view, a top-level
        # node of another kind, and a node whose children list is empty.
        for change, message in (
                (lambda d: d['files'][0]['children'][0].pop('name'), 'no name'),
                (lambda d: d.__setitem__('files', []), 'is empty'),
                (lambda d: d['sections'].append({'name': 'bss', 'kind': 'bss', 'size': 4, 'linked': 0, 'matched': 0,
                                                 'address': '0x90000000'}), 'has kind'),
                (lambda d: d['files'][0]['children'][0].__setitem__('children', []), 'no children')):
            m = publish.map_document(r, SECTIONS)
            change(m)
            with self.subTest(message=message):
                self.assertTrue(self.page_rejects(m, s))
                with self.assertRaisesRegex(publish.ContractError, message):
                    publish.check_map(m, s)


class TimestampTests(unittest.TestCase):
    def test_accepts_any_utc_iso_form(self):
        for value in ('2026-10-26T20:57:37Z', '2026-10-26T20:57:37.624145+00:00'):
            publish.timestamp(value)

    def test_rejects_offsets_and_garbage(self):
        for value in ('2026-10-26T20:57:37+02:00', '2026-10-26T20:57:37', 'yesterday', None):
            with self.assertRaises(publish.ContractError, msg=value):
                publish.timestamp(value)


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'targets.json'

    def load(self, document):
        self.path.write_text(json.dumps(document))
        return publish.load_targets(self.path)

    def test_flat_targets(self):
        targets, default = self.load(TARGETS)
        self.assertEqual(default, 'GAME01-rev0')
        self.assertEqual(targets, TARGETS['targets'])

    def test_rejects_bad_identity(self):
        for change in ({'platform': 'GameCube'}, {'sha1': 'A' * 40}, {'status': 'live'}, {'id': 'a/b'}):
            document = copy.deepcopy(TARGETS)
            document['targets'][0].update(change)
            with self.assertRaises(publish.ContractError, msg=change):
                self.load(document)


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.tree = Path(self.temp.name)
        self.game = publish.game_document(SITE, TARGETS['targets'], 'GAME01-rev0', 'owner/game')
        self.map = publish.map_document(report(), SECTIONS)

    def rows(self):
        return json.loads((self.tree / 'data/game/GAME01-rev0/history.json').read_text())

    def current(self):
        return json.loads((self.tree / 'data/game/GAME01-rev0/latest.json').read_text())

    def test_appends_one_row_per_revision(self):
        publish.write_target(self.tree, self.game, latest(REV[0], '2026-01-01T00:00:00Z', '2026-01-01T00:01:00Z'), self.map)
        publish.write_target(self.tree, self.game, latest(REV[1], '2026-01-02T00:00:00Z', '2026-01-02T00:01:00Z'), self.map)
        publish.write_target(self.tree, self.game, latest(REV[1], '2026-01-02T00:00:00Z', '2026-01-02T00:09:00Z'), self.map)
        self.assertEqual([r['revision'] for r in self.rows()], REV[:2])
        self.assertEqual(self.current()['measuredAt'], '2026-01-02T00:01:00Z')
        self.assertEqual(publish.check_tree(self.tree), 1)
        index = json.loads((self.tree / 'index.json').read_text())
        self.assertEqual(index, {'schema': 1, 'games': ['game']})

    def test_older_commit_never_replaces_latest(self):
        publish.write_target(self.tree, self.game, latest(REV[1], '2026-01-02T00:00:00Z', '2026-01-02T00:01:00Z'), self.map)
        publish.write_target(self.tree, self.game, latest(REV[0], '2026-01-01T00:00:00Z', '2026-01-02T00:05:00Z'), self.map)
        self.assertEqual(self.current()['source']['revision'], REV[1])
        self.assertEqual([r['revision'] for r in self.rows()], [REV[1], REV[0]])
        publish.check_tree(self.tree)

    def test_rows_stay_ordered_by_measurement(self):
        publish.write_target(self.tree, self.game, latest(REV[1], '2026-01-02T00:00:00Z', '2026-01-02T00:01:00Z'), self.map)
        publish.write_target(self.tree, self.game, latest(REV[0], '2026-01-01T00:00:00Z', '2026-01-01T00:01:00Z'), self.map)
        self.assertEqual([r['revision'] for r in self.rows()], [REV[0], REV[1]])

    def test_inactive_target_is_refused(self):
        bad = latest(REV[0], '2026-01-01T00:00:00Z', '2026-01-01T00:01:00Z')
        bad['target'] = 'GAME01-rev1'
        with self.assertRaisesRegex(publish.ContractError, 'not an active target'):
            publish.write_target(self.tree, self.game, bad, self.map)

    def test_corrupt_history_is_never_overwritten(self):
        path = self.tree / 'data/game/GAME01-rev0/history.json'
        path.parent.mkdir(parents=True)
        path.write_text('[{"revision": ')
        with self.assertRaises(publish.ContractError):
            publish.write_target(self.tree, self.game, latest(REV[0], '2026-01-01T00:00:00Z', '2026-01-01T00:01:00Z'), self.map)
        self.assertEqual(path.read_text(), '[{"revision": ')

    def test_tree_check_catches_history_mismatch(self):
        publish.write_target(self.tree, self.game, latest(REV[0], '2026-01-01T00:00:00Z', '2026-01-01T00:01:00Z'), self.map)
        rows = self.rows()
        rows[0]['code']['linked'] = 0
        publish.write_json(self.tree / 'data/game/GAME01-rev0/history.json', rows, rows=True)
        with self.assertRaisesRegex(publish.ContractError, 'history differs from latest'):
            publish.check_tree(self.tree)


class CreditTests(unittest.TestCase):
    """Credits follow the earliest measured build in which a function was exact."""
    OWNER, ALICE, BOB = (1, 'owner'), (2, 'alice'), (3, 'bob')
    T0, T1, T2, T3 = ('2026-01-0%dT00:00:00Z' % n for n in range(1, 5))

    def ids(self, *addresses):
        return {'GAME01-rev0:%s:16' % a: a for a in addresses}

    def authors(self, document):
        return {f['id'].split(':')[1]: f['authors'] for f in document['functions']}

    def step(self, previous, exact, when, authors, overrides=None, newer=True):
        document = publish.credit(previous, exact, when, authors, overrides or {}, newer)
        publish.check_contributors(document, {'functions': {'exact': len(document['functions']) if newer else None}})
        return document

    def test_switching_on_credits_the_owner_then_merges_credit_their_authors(self):
        first = self.step(None, self.ids('0x80000000', '0x80000010'), self.T0, [self.OWNER])
        self.assertEqual(self.authors(first), {'0x80000000': [1], '0x80000010': [1]})
        second = self.step(first, self.ids('0x80000000', '0x80000010', '0x80000020'), self.T1, [self.ALICE, self.BOB])
        self.assertEqual(self.authors(second)['0x80000020'], [2, 3])
        self.assertEqual(self.authors(second)['0x80000000'], [1])
        self.assertEqual([(p['login'], p['functions']) for p in second['contributors']],
                         [('owner', 2), ('alice', 1), ('bob', 1)])

    def test_a_function_that_regresses_and_returns_keeps_its_first_credit(self):
        first = self.step(None, self.ids('0x80000000'), self.T0, [self.OWNER])
        second = self.step(first, self.ids('0x80000000', '0x80000010'), self.T1, [self.ALICE])
        lost = self.step(second, self.ids('0x80000000'), self.T2, [self.BOB])
        self.assertEqual([f['id'] for f in lost['retired']], ['GAME01-rev0:0x80000010:16'])
        self.assertEqual([p['login'] for p in lost['contributors']], ['owner'])
        back = self.step(lost, self.ids('0x80000000', '0x80000010'), self.T3, [self.BOB])
        self.assertEqual(self.authors(back)['0x80000010'], [2])
        self.assertEqual(back['retired'], [])

    def test_an_older_build_finishing_late_moves_a_credit_earlier_and_nothing_else(self):
        first = self.step(None, self.ids('0x80000000'), self.T0, [self.OWNER])
        # T2 (bob) published before T1 (alice), although alice's merge made 0x80000010 exact first.
        bob = self.step(first, self.ids('0x80000000', '0x80000010'), self.T2, [self.BOB])
        alice = self.step(bob, self.ids('0x80000000', '0x80000010', '0x80000020'), self.T1, [self.ALICE], newer=False)
        self.assertEqual(self.authors(alice), {'0x80000000': [1], '0x80000010': [2]})
        self.assertEqual(alice['credited_functions'], 2)

    def test_imported_credits_without_since_are_kept(self):
        legacy = {'schema': 1, 'credited_functions': 1, 'contributors': [{'id': 2, 'login': 'alice', 'functions': 1}],
                  'functions': [{'id': 'GAME01-rev0:0x80000000:16', 'authors': [2]}]}
        document = self.step(legacy, self.ids('0x80000000', '0x80000010'), self.T1, [self.BOB])
        self.assertEqual(self.authors(document), {'0x80000000': [2], '0x80000010': [3]})
        older = self.step(document, self.ids('0x80000000', '0x80000010'), self.T0, [self.OWNER], newer=False)
        self.assertEqual(self.authors(older), {'0x80000000': [2], '0x80000010': [1]})

    def test_overrides_win(self):
        first = self.step(None, self.ids('0x80000000', '0x80000010'), self.T0, [self.OWNER],
                          overrides={'0x80000010': [self.ALICE, self.BOB]})
        self.assertEqual(self.authors(first)['0x80000010'], [2, 3])

    def test_check_rejects_a_ranking_that_disagrees(self):
        document = self.step(None, self.ids('0x80000000'), self.T0, [self.OWNER])
        document['contributors'][0]['functions'] = 2
        with self.assertRaisesRegex(publish.ContractError, 'totals'):
            publish.check_contributors(document, {})
        document = self.step(None, self.ids('0x80000000'), self.T0, [self.OWNER])
        document['retired'] = [dict(document['functions'][0])]
        with self.assertRaisesRegex(publish.ContractError, 'both current and retired'):
            publish.check_contributors(document, {})

    def test_credits_line_and_overrides_file(self):
        self.assertEqual(publish.credits_line('## Scope\n\nCredits: @alice, bob\n'), ['alice', 'bob'])
        self.assertIsNone(publish.credits_line('no line here'))
        for bad in ('Credits: ', 'Credits: @alice, @alice', 'Credits: not a login!'):
            with self.subTest(bad=bad), self.assertRaises(publish.ContractError):
                publish.credits_line(bad)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'credits.tsv'
            path.write_text('# address\tlogins\treason\n0x80000010\talice,bob\timported from #12\n')
            self.assertEqual(publish.credits_tsv(path), {'0x80000010': ['alice', 'bob']})
            for bad in ('0x8000001a\talice\tr\n', '0x80000010\talice\t\n', '0x80000010\talice\n'):
                path.write_text(bad)
                with self.subTest(bad=bad), self.assertRaises(publish.ContractError):
                    publish.credits_tsv(path)

    def test_write_target_publishes_and_checks_credits(self):
        with tempfile.TemporaryDirectory() as temp:
            tree = Path(temp)
            game = publish.game_document(SITE, TARGETS['targets'], 'GAME01-rev0', 'owner/game')
            credits = {'authors': [self.ALICE], 'owner': self.OWNER, 'overrides': {}}
            publish.write_target(tree, game, latest(REV[0], self.T0, self.T0), publish.map_document(report(), SECTIONS), credits)
            current = json.loads((tree / 'data/game/GAME01-rev0/latest.json').read_text())
            self.assertEqual(current['modules']['contributors'], 'contributors.json')
            document = json.loads((tree / 'data/game/GAME01-rev0/contributors.json').read_text())
            self.assertEqual([p['login'] for p in document['contributors']], ['owner'])
            self.assertEqual(publish.check_tree(tree), 1)
            # Re-running the same revision changes nothing.
            publish.write_target(tree, game, latest(REV[0], self.T0, self.T1), publish.map_document(report(), SECTIONS), credits)
            self.assertEqual(json.loads((tree / 'data/game/GAME01-rev0/contributors.json').read_text()), document)


class CommandTests(unittest.TestCase):
    def test_dry_run_from_a_git_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            source = temp / 'producer'
            (source / 'config').mkdir(parents=True)
            (source / 'config/site.json').write_text(json.dumps(SITE))
            (source / 'config/targets.json').write_text(json.dumps(TARGETS))
            (source / 'report.json').write_text(json.dumps(report()))
            for args in (['init', '-q'], ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q',
                                          '--allow-empty', '-m', 'Measured commit']):
                subprocess.run(['git', *args], cwd=source, check=True)
            out = temp / 'tree'
            subprocess.run([sys.executable, str(ROOT / '.github/actions/publish/publish.py'), 'publish',
                            '--dry-run', '--target', 'GAME01-rev0', '--report', 'report.json',
                            '--repository', 'owner/game', '--output', str(out), '--tools', 'objdiff=v3.6.1'],
                           cwd=source, check=True, capture_output=True)
            current = json.loads((out / 'data/game/GAME01-rev0/latest.json').read_text())
            self.assertEqual(current['source']['title'], 'Measured commit')
            self.assertEqual(current['tools'], [{'name': 'objdiff', 'version': 'v3.6.1'}])
            self.assertEqual(publish.check_tree(out), 1)
            # The report check of a pull request: credits on, but the merged pull request does
            # not exist yet, so --no-credits converts without reading GitHub.
            (source / 'config/site.json').write_text(json.dumps(dict(SITE, contributors=True)))
            command = [sys.executable, str(ROOT / '.github/actions/publish/publish.py'), 'publish', '--dry-run',
                       '--target', 'GAME01-rev0', '--report', 'report.json', '--repository', 'owner/game',
                       '--output', str(temp / 'check')]
            refused = subprocess.run(command, cwd=source, capture_output=True, text=True, env={**os.environ, 'GITHUB_TOKEN': ''})
            self.assertIn('GITHUB_TOKEN is required', refused.stderr)
            checked = subprocess.run(command + ['--no-credits'], cwd=source, capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertIn('checked 1 target(s)', checked.stdout)
            self.assertIsNone(json.loads((temp / 'check/data/game/GAME01-rev0/latest.json').read_text())['modules']['contributors'])


if __name__ == '__main__':
    unittest.main()
