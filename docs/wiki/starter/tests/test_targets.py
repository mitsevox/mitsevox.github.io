"""Target identity and CI dependency scope. Run from the repository root:
python3 -m unittest discover -s tests -p 'test_*.py'"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from tools.targets import registry,select,build_targets
from tools.ci_targets import affected

ROOT=Path(__file__).resolve().parents[1]


class Targets(unittest.TestCase):
    def test_registry_is_valid_and_rejects_broken_entries(self):
        value=registry()
        self.assertIn(value['defaultTarget'],build_targets(value))
        for target in value['targets']:
            self.assertEqual(select(target['id'])['status'],target['status'])
        with self.assertRaises(ValueError):select('no-such-target')
        for change in ({'status':'live'},{'platform':'GameCube'},{'sha1':'A'*40},{'extra':1}):
            broken=copy.deepcopy(value);broken['targets'][0].update(change)
            with self.subTest(change=change),tempfile.NamedTemporaryFile('w',suffix='.json') as f:
                json.dump(broken,f);f.flush()
                with self.assertRaises(ValueError):registry(f.name)

    def test_changed_paths_select_their_targets(self):
        value=registry();deps=json.loads((ROOT/'config/ci-targets.json').read_text())
        active=build_targets(value)
        self.assertEqual(affected(['src/unit.cpp'],value,deps),active)
        self.assertEqual(affected(['docs/guide.md'],value,deps),[])
        self.assertEqual(affected(['unclassified/path'],value,deps),active)
        self.assertEqual(affected([],value,deps,force=True),active)
        for target in value['targets']:
            expected=[target['id']] if target['status']=='active' else []
            with self.subTest(target=target['id']):
                self.assertEqual(affected(['config/%s/splits.txt'%target['id']],value,deps),expected)
        with self.assertRaises(ValueError):affected(['../escape'],value,deps)


if __name__=='__main__':unittest.main()
