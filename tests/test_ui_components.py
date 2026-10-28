"""Behavior and lifecycle regressions for reusable presentation components."""
from pathlib import Path
import subprocess
import unittest


class UIComponents(unittest.TestCase):
    def test_component_behavior_and_cleanup(self):
        result = subprocess.run(['node', '--test', 'tests/ui-components.mjs'],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
