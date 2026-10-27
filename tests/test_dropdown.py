"""Shared dropdown lifecycle regressions; no external JavaScript test dependency."""
from pathlib import Path
import subprocess
import unittest

class Dropdown(unittest.TestCase):
    def test_selection_keyboard_motion_and_interrupted_close(self):
        result=subprocess.run(['node','--test','tests/dropdown.mjs'],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
