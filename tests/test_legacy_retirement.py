"""The standard activation preserves its frozen history and retires network selection."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from archives.import_nfl import refresh as retired_refresh
from build_site import copy_redirects
from reporting.github import GitHub
from reporting.registry import producer
from reporting.state import check_update
from reporting.validation import decode, validate_package


class LegacyRetirementTests(unittest.TestCase):
    def test_first_standard_report_preserves_every_frozen_row_and_legacy_stays_readable(self):
        checkpoint=decode((ROOT/'config/archives/nflstreet2-legacy-checkpoint.json').read_bytes())
        old,_,activity=validate_package(ROOT/checkpoint['entry']['path'])
        new,_,current=validate_package(ROOT/checkpoint['firstStandard']['path'])
        check_update(old,new,activity,current,'ahead')
        self.assertEqual(len(activity['snapshots']),checkpoint['historyRows'])
        for previous in activity['snapshots']:
            row=next(r for r in current['snapshots'] if r['revision']==previous['revision'])
            self.assertEqual(row['provenance']['record'],previous)
        self.assertEqual(new['modules']['map']['asset']['schema'],'map-v2')
        active=producer(ROOT,'nflstreet2')
        self.assertEqual(active['format'],'report-v1')
        self.assertEqual(active['artifact'],'report-v1')
        self.assertNotIn('freeze',active)

    def test_retired_refresh_cannot_read_upstream_for_active_standard_producer(self):
        with patch.object(GitHub,'get',side_effect=AssertionError('retired network path used')):
            with self.assertRaisesRegex(ValueError,'Archived legacy importer is disabled'):
                retired_refresh(ROOT)

    def test_retired_url_redirect_is_built_and_preserves_query_and_fragment(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=Path(temp);copy_redirects(ROOT,stage)
            page=(stage/'nflstreet2/index.html').read_text()
            self.assertIn('http-equiv="refresh"',page)
            self.assertIn("location.replace('/games/nflstreet2/' + location.search + location.hash)",page)
            self.assertIn('href="/games/nflstreet2/"',page)
            with self.assertRaisesRegex(ValueError,'conflicting redirect'):copy_redirects(ROOT,stage)


if __name__=='__main__':unittest.main()
